"""W1: Worker-Rechnung fuer Live-Bilder, mit Stapelfenster und Tuer am Feed."""

import argparse
import importlib
import os
import threading
from collections import Counter
from dataclasses import dataclass
from types import SimpleNamespace

import decode
from core import gpubudget, logbuch, refquelle, stapel, tuer

_log = logbuch.logger(__name__)
# Eigentuemer 29.10.2026, 11:27:41: „Also zum Beispiel 30 Sekunden Hardcap oder 60,
# irgend sowas.“ W1, Soll 4, uebernimmt den Startwert 60 aus Entscheid Nr. 1.
WINDOW_SECONDS = 60


def split_frame(index, buffer):
    """Zerlegt den gelieferten NV12-Puffer in dieselben Sichten wie der Worker.
    -> (Bildnummer, Y [1,H,W,1], UV [1,H/2,W/2,2]), ohne Kopie.
    """
    height, width = buffer.shape[0] * 2 // 3, buffer.shape[1]
    return (index, buffer[:height].reshape(1, height, width, 1),
            buffer[height:].reshape(1, height // 2, width // 2, 2))


def display_frame(buffer):
    """Wandelt NV12 ausschliesslich fuer Vorschau, Vorrat oder Meldebild um.
    -> BGR-Bild ueber den CPU-Anzeigeweg des Workers.
    """
    import worker_kern as wk
    _, y, uv = split_frame(0, buffer)
    return wk.nv12_bgr((y, uv), y.shape[2], y.shape[1])


def sample_step(cfg, fps):
    """Liest das Worker-Grundraster fuer einen Feed ohne bekannte Paketanzahl.
    -> Schrittweite aus decode.sample_schritt.
    """
    return decode.sample_schritt(fps, cfg["fps_sample"])[0]


def decoder_command(module, location, hardware):
    """Ergaenzt die Live-Eingangsoptionen am nativen NV12-Rezept der Worker-Engine.
    -> ffmpeg-Argumentliste; jedes Bild, ohne Skalierung oder Rueckspulen.
    """
    from core.livewache import auth_argumente, quelle_ist_datei
    recipe = module.em if module.Engine.name == "cpu" else module
    command = recipe._ffmpeg_nv12(location, 1, bool(hardware))
    options = ["-re", "-stream_loop", "-1"] if quelle_ist_datei(location) else []
    if location.startswith("rtsp://"):
        options += ["-rtsp_transport", "tcp"]
    options += auth_argumente(location)
    index = command.index("-i")
    return command[:index] + options + command[index:]


@dataclass(frozen=True)
class ReferenceSnapshot:
    """Ein ganzer Referenzabzug mit seiner Generation."""

    generation: int
    all_names: tuple
    reference_names: tuple
    recognition: dict


class ReferenceStore:
    """Referenzleser aus dem Prototyp; der Aufrufer haelt das Rechenschloss."""

    def __init__(self, data_dir, identity, source=refquelle, log=_log):
        self.cfg, self.identity = {"data_dir": str(data_dir)}, identity
        self.source, self.log = source, log
        self.snapshot, self.generation, self.error = None, 0, "References have not been read"

    def refresh(self):
        """Liest nach einem Katalogwechsel einen ganzen, nach Modell gesiebten Abzug.
        -> ReferenceSnapshot oder None; ein Fehler entwertet alte Generationen.
        """
        import worker_kern as wk
        try:
            state = self.source.state_id(self.cfg)
            if self.snapshot is not None and state == self.snapshot.recognition["stand"]:
                return self.snapshot
            if self.snapshot is None:
                self.source.heads_clear(self.cfg)
            self.source.catalog_ref_ids(self.cfg)
            reading = self.source.read_matrix(self.cfg, None)
            watch = self.source.matrix_watch(self.cfg, reading["stand"], len(reading["ausgelassen"]))
            if reading["ausgelassen"] or (watch is not None and watch["fehlte"]):
                raise ValueError("Incomplete reference read")
            all_names, reference_names, recognition = wk.referenzen_laden(reading, self.identity)
            if self.source.state_id(self.cfg) != recognition["stand"]:
                raise ValueError("Reference state changed during read")
            for key in ("refs", "refs_t"):
                recognition[key].flags.writeable = False
            snapshot = ReferenceSnapshot(self.generation + 1, tuple(all_names),
                                         tuple(reference_names), recognition)
        except Exception as error:  # jede misslungene Lesung sperrt Namen
            reason = "Reference read failed (" + type(error).__name__ + ")"
            if self.snapshot is not None or self.error != reason:
                self.generation += 1
                self.log.error(reason + "; name notifications blocked")
            self.snapshot, self.error = None, reason
            return None
        self.snapshot, self.generation, self.error = snapshot, snapshot.generation, None
        self.log.info("Complete reference generation installed")
        if not snapshot.reference_names:
            self.log.warning("No usable references; name notifications blocked")
        return snapshot

    def allows_names(self, generation):
        """Vergleicht eine Ergebnisgeneration mit dem bereits gelesenen Stand.
        -> bool; bei leeren, kaputten oder ausgetauschten Referenzen False.
        """
        return (self.snapshot is not None and bool(self.snapshot.reference_names)
                and generation == self.generation)


@dataclass(frozen=True)
class FrameResult:
    """Fundzeilen und Latten gehoeren zu derselben Referenzgeneration."""

    generation: int
    rows: list
    limits: dict


class _FrameEngine:
    def __init__(self, frame):
        self.frame = frame

    def frames(self, _clip, _width, _height, _step):
        """Speist genau ein bereits geliefertes Bild in den Worker.
        -> Iterator (Bildnummer, Y, UV).
        """
        yield self.frame


class EngineContext:
    """Ein Worker-Kontext; alle Rechnungen laufen unter Engine._det_lock."""

    def __init__(self, cfg, log=_log, *, engine_module=None, reference_source=refquelle,
                 identity_factory=None):
        import worker_dienst as wd
        self.cfg, self.log = cfg, log
        self.module = engine_module or importlib.import_module("engine_" + wd.engine_waehlen())
        self.source, self.identity_factory = reference_source, identity_factory
        self.engine, self.references = None, None
        self.geometries, self.camera_fields = {}, {}
        self.local = threading.local()
        self.binding = {}
        self.frames = 0  # bestehender Kern-Zaehler einzel

    def limits(self, camera):
        """Loest die Kamera-Latten auf exakt dem Job-Weg des Workers auf.
        -> (eingelesene Job-Felder, wirksame Latten), mit lauten Modell-Abschaltungen.
        """
        import worker_dienst as wd
        from verifyd import job_latten
        fields = wd.felder_lesen({"latten": job_latten(self.cfg, camera)})["argv_fest"]
        old = self.camera_fields.get(camera)
        if old is None or old[0] != fields:
            sink = SimpleNamespace(zeile=lambda text, stufe=logbuch.INFO: self.log.log(stufe, text))
            limits, quality_off, pose_off = wd.latten_bauen(fields, sink)
            self.camera_fields[camera] = fields, limits, quality_off, pose_off
        return self.camera_fields[camera][:2]

    def _start(self):
        import worker_dienst as wd
        if self.engine is not None:
            return
        parser = argparse.ArgumentParser(add_help=False)
        self.module.Engine.argumente(parser)
        args = parser.parse_args([])
        if self.module.Engine.name == "cuda":
            args.vram_deckel_mb = gpubudget.WATCHER_CUDA_ARENA_MB
        args.out = os.path.join(os.environ.get("SCRATCH_DIR") or
                                os.path.join(self.cfg["data_dir"], "clips"), "live")
        args.inferenz_frist_s = self.cfg.get("inferenz_frist_s")
        self.engine = self.module.Engine(args)
        self.binding = {"engine": self.module.Engine.name, "gebunden": True,
                        "geraet": getattr(self.module, "GERAET", None) or getattr(self.module, "EP", None)}
        if hasattr(self.engine, "bindung_ergaenzen"):
            self.engine.bindung_ergaenzen(self.binding)
        identity = (self.identity_factory() if self.identity_factory else
                    wd.bild_kern.model_identity(wd.face_audit.aktuelles_modell()))
        self.references = ReferenceStore(self.cfg["data_dir"], identity, self.source, self.log)

    def calculate(self, camera, frame, fps):
        """Rechnet ein NV12-Bild mit thread-eigenem Satz und unveraenderter Worker-Kaskade.
        -> FrameResult oder None bei unlesbaren Referenzen; Engine-Fehler gehen nach oben.
        """
        import worker_kern as wk
        self._start()
        fields, limits = self.limits(camera)
        snapshot = self.references.refresh()
        if snapshot is None:
            return None
        _, y, _uv = frame
        shape = y.shape[2], y.shape[1]
        if shape not in self.geometries:
            self.geometries[shape] = self.engine.geometrie_bauen({camera: (*shape, fps)})[shape]
        geometry = self.geometries[shape]
        if not hasattr(self.local, "warm"):
            self.local.warm = set()
        if shape not in self.local.warm:
            geometry.satz().warm()
            self.local.warm.add(shape)
        self.frames += 1
        rows, _frames = wk.event_rechnen(
            _FrameEngine(frame), geometry, camera, 1, fields["det_thresh"], fps,
            snapshot.all_names, snapshot.reference_names, snapshot.recognition,
            {**limits, "tuer_fenster": 0}, Counter(), Counter(), vorrat=None, personenzahl=None)
        return FrameResult(snapshot.generation, rows, limits)

    def allows_names(self, generation):
        """Prueft den Referenzstand unmittelbar vor einer Namensmeldung erneut.
        -> bool; ein Wechsel sperrt Ergebnisse der alten Generation.
        """
        if self.references is None:
            return False
        self.references.refresh()
        return self.references.allows_names(generation)

    def problem(self, camera):
        """Meldet Referenz- und Modell-Rueckfaelle an die bestehende Kachel-Stoerung.
        -> Fehlertext oder leer bei vollstaendiger Rechnung.
        """
        if self.references is not None and self.references.error:
            return self.references.error
        if self.binding.get("gebunden") is False:
            return self.binding.get("grund") or "requested compute device not bound"
        fields = self.camera_fields.get(camera)
        return "measurement model unavailable; recognition bars disabled" if fields and any(fields[2:]) else ""

    def status(self):
        """Liefert die bestehenden Kern-Felder; die Worker-Rechnung hat keinen Sammelbatch.
        -> dict fuer die vorhandene Statusdatei, ohne neue Zaehler.
        """
        return {"sessions": int(self.engine is not None), "rec_geraet": self.binding.get("geraet") or "?",
                "sammelbatch": False, "parallel": 1, "sammel_ms": 0.0,
                "batches": 0, "batch_bilder": 0, "batch_crops": 0, "einzel": self.frames}


class FeedDoor:
    """Die Worker-Tuer ohne Sprung; Deckel und Fenster gehoeren zum Kamera-Stapel."""

    def __init__(self):
        self.until, self.frames, self.closed = -1, 0, False

    def active(self, index):
        """Prueft, ob dieses Bild innerhalb der noch offenen Tuer liegt.
        -> bool.
        """
        return not self.closed and index <= self.until

    def report(self, index, rows, decision, limits, door_frame):
        """Zaehlt ein gerechnetes Tuerbild und verlaengert bei einem Worker-Ausloeser.
        -> None; vergangene Bilder werden nie nachgefordert.
        """
        self.frames += bool(door_frame)
        cap = limits["tuer_deckel"]
        if cap > 0 and self.frames >= cap:
            self.closed, self.until = True, index
        if not self.closed and limits["tuer_fenster"] > 0 and tuer.ausloeser(rows, decision["namen"]):
            self.until = max(self.until, index + limits["tuer_fenster"])


class CameraStack:
    """Fundzeilen und beste gueltige Stimmen eines begrenzten Kamera-Fensters."""

    def __init__(self):
        self.generation, self.limits = None, None
        self.reset()

    def reset(self, started=None):
        """Leert Stapel, Beweisbilder und Tuer; die Meldesperre liegt weiterhin im Auftritt.
        -> None.
        """
        self.rows, self.best, self.started = [], {}, started
        self.door = FeedDoor()

    def tick(self, mono):
        """Setzt ein abgelaufenes Fenster auch ohne neue Gesichter zurueck.
        -> None; der Deckel beendet keinen Auftritt.
        """
        if self.started is not None and mono >= self.started + WINDOW_SECONDS:
            count = int((mono - self.started) // WINDOW_SECONDS)
            self.reset(self.started + count * WINDOW_SECONDS)

    def add(self, result, buffer, mono):
        """Fuegt die ungerundeten Worker-Zeilen hinzu und pflegt das Bild der besten Stimme.
        -> Worker-Stapelurteil ohne Personenzahl-Grenze.
        """
        self.tick(mono)
        # Ein Fenster rechnet wie ein Worker-Ereignis mit EINEM Latten-Satz: wechseln Referenzen oder
        # Kamera-Latten, beginnt ein neues Fenster, sonst traegt `best` eine nicht mehr gueltige Stimme.
        if self.generation != result.generation or self.limits != result.limits:
            self.reset()
            self.generation, self.limits = result.generation, result.limits
        if self.started is None and any(row.get("fd") is False for row in result.rows):
            self.started = mono
        if self.started is not None:
            self.rows.extend(result.rows)
        for row in result.rows:
            if not stapel.gueltig(row, result.limits):
                continue
            name, _tie = stapel.stimme(row["sc"])
            if name is not None:
                score = row["sc"][name]
                if name not in self.best or score > self.best[name][0]:
                    self.best[name] = score, row["bb"], buffer
        return stapel.entscheiden(self.rows, result.limits, result.limits["stapel_stimmen"], None)
