#!/usr/bin/env python3
"""worker — persistenter Analyse-Worker (W2 der GPU-Welle, 0.1.0.38).

WARUM: ~85 % der CPU je Event war PROZESS-STARTUP von analyze.py (Modelle laden; gemessen
26.07.: 55 CPU-s je Event, davon die Analyse selbst nur ~6). Dieser Worker haelt die Modelle
EINMAL und fuehrt die bestehenden Skripte MEHRFACH IM SELBEN PROZESS aus — der Recon hat
genau das gemessen (mehrere eids in einem Prozess: 5,5-6,4 CPU-s Marginalkosten je Clip).

WIE (bewusst OHNE analyze.py-Refactor — die kalibrierte Pipeline bleibt wortgleich):
- analyze-Jobs laufen via runpy.run_path(analyze.py, run_name="__main__") mit gesetztem
  sys.argv. Ergebnis-Kontrakt (results.jsonl, stdout-Marken) ist damit identisch zum
  Subprozess-Weg; stdout/stderr werden je Job in die analyze.log-Datei des Events geleitet.
- face_audit.Embedder wird beim Worker-Start durch eine Cache-Factory ersetzt: EIN warmer
  Embedder je Worker-Leben (Frische: Modellwechsel erzwingt Neubau; det_size setzt jedes
  Skript selbst — nach P1 attributsbillig; Reset auf 320 je Job wahrt den Referenzpfad).
- sammle-Jobs rufen anlernen.sammle() direkt (importierbare Funktion, nutzt die Factory mit).

PROTOKOLL: Jobs als JSON-Zeilen auf stdin; Antworten als JSON-Zeilen auf den fd aus
WORKER_ANTWORT_FD (eigene Pipe — stdout gehoert den Skripten!). Ein Job at a time; verifyd
serialisiert (self.lock) und haelt Timeout/killpg. stdin-EOF (execv-Waise/Ende) -> Exit.
  {"typ":"analyze","argv":[...],"log":"/pfad/analyze.log"}
  {"typ":"sammle","tage":0.1,"mit_migriere":false,"log":"..."}
  {"typ":"ernte","eid":"...","kamera":"...","ts":0,"fps_sample":3,
   "schwellen":{...},"lauf_dir":"...","log":"..."}   (E2: 1 Event je Job, Live-Vorrang)
  {"typ":"ping"}
Antwort: {"ok":bool,"cpu_s":float,"wall_s":float,"rss_mb":int,("fehler":str)}
         (ernte zusaetzlich: die Zaehler aus core.ernte.ernte_event)

Idle-EXIT nach WORKER_IDLE_S (Default 900 s): der Worker beendet sich selbst, verifyd
startet ihn beim naechsten Job neu. Urspruenglich war hier eine Embedder-Entladung im
laufenden Prozess — der Prod-Soak 27.07. hat sie widerlegt: ORT gibt Arena-Speicher nicht
an das OS zurueck, jeder Entlade-/Neuaufbau-Zyklus ADDIERTE ~200 MB RSS (1850->2057,
worker_rss_max_mb nach 54 min gerissen). Nur ein Prozess-Ende gibt den Speicher wirklich
frei; die Kalt-Kosten (~70 CPU-s) sind identisch zum Neuaufbau. Die Kontext-Kollision
loest ohnehin die Buendelung aller Jobs in DIESEM Prozess (E2-Doku), nicht das Idle-Verhalten.
--roundtrip <argv...>: Selbsttest fuers QS-Gate — zwei analyze-Jobs (kalt+warm) ueber die
echte Job-Mechanik, Antwort nach stdout, Exit 0/1. Kein verifyd, keine Nebenwirkungen.
"""
import contextlib
import json
import os
import runpy
import select
import socket
import sys
import time

from core.pfade import WURZEL as HERE   # M0-Anker (Falle 0): eine Pfad-Quelle

# urlretrieve kennt kein timeout= — ohne Default haengt ein TCP-Stall ewig und
# haelt den Job-Lock bis zum harten Deckel (Widerleger .75: analyze.py setzt das
# fuer sich selbst, aber der ERSTE Job eines frischen Workers kann ein ernte-Job
# sein und lief dann ungeschuetzt). Prozessweit wie in analyze.py:25.
socket.setdefaulttimeout(120)
sys.path.insert(0, HERE)

_emb = None                      # der eine warme Embedder je Worker-Leben
_EchterEmbedder = None


def _factory(*a, **kw):
    """Ersatz fuer face_audit.Embedder: liefert den warmen Embedder wieder aus.
    Neubau nur bei Modellwechsel (aktuelles_modell aendert sich via Config/UI).
    det 320 je Ausgabe = exakt der frische Zustand, den die Skripte erwarten
    (Referenzbilder werden IMMER bei 320 eingebettet — die heilige Reihenfolge)."""
    global _emb
    import face_audit
    modell = (kw.get("modell") or face_audit.aktuelles_modell())
    modell = str(modell).lower()
    if _emb is None or _emb.modell != modell:
        _emb = _EchterEmbedder(*a, **kw)
    else:
        _emb.set_det_size((320, 320))
    return _emb


def _rss_mb():
    try:
        with open("/proc/self/status") as f:
            for z in f:
                if z.startswith("VmRSS:"):
                    return int(z.split()[1]) // 1024
    except Exception:
        pass
    return -1


@contextlib.contextmanager
def _fd_umleitung(logpfad):
    """stdout+stderr auf FD-EBENE (dup2) in die Job-Logdatei umleiten.
    redirect_stdout allein reicht NICHT: ORT/OpenCV schreiben am Python-Objekt vorbei
    direkt auf fd 1/2 (der pthread-Spam, den qs.sh an analyze.log zaehlt, und die
    PROVIDER-GUARD-Marker, die verifyd aus analyze.log hebt, muessen dort landen —
    der Log-Kontrakt des alten Subprozess-Wegs bleibt so unveraendert)."""
    lf = open(logpfad, "a")
    sys.stdout.flush(); sys.stderr.flush()
    alt1, alt2 = os.dup(1), os.dup(2)
    try:
        os.dup2(lf.fileno(), 1); os.dup2(lf.fileno(), 2)
        yield
    finally:
        sys.stdout.flush(); sys.stderr.flush()
        os.dup2(alt1, 1); os.dup2(alt2, 2)
        os.close(alt1); os.close(alt2); lf.close()


def _job_ausfuehren(job):
    """Einen Job im Prozess ausfuehren; stdout/stderr in die Job-Logdatei.
    SystemExit (z.B. analyze 'Referenz-Master leer') toetet den Worker NICHT."""
    typ = job.get("typ")
    if typ == "ping":
        return {"ok": True, "rss_mb": _rss_mb()}
    logpfad = job.get("log") or os.devnull
    t0 = os.times()
    t0w = time.monotonic()   # E1/V0.4: WANDUHR je Job — cpu_s allein hatte die v1-Hochrechnung
    #                          in die Irre gefuehrt (CPU-Sekunden sind KEINE Dauer)
    zusatz = None            # E2: ernte-Jobs liefern ihre Zaehler in der Antwort mit
    try:
        with _fd_umleitung(logpfad):
            if typ == "analyze":
                sys.argv = ["analyze.py"] + list(job.get("argv") or [])
                # analyze haelt Zustand auf Modulebene -> run_path gibt jedem Lauf ein
                # frisches Modul-Umfeld; nur der Embedder ueberlebt (Factory oben).
                runpy.run_path(os.path.join(HERE, "analyze.py"), run_name="__main__")
            elif typ == "sammle":
                import anlernen
                anlernen.sammle(float(job.get("tage", 0.1)),
                                mit_migriere=bool(job.get("mit_migriere", False)))
            elif typ == "ernte":
                # E2 Frontal-Ernte, EIN Event je Job (Leitprinzip 5). Clip-Beschaffung
                # exakt das analyze-Muster (SCRATCH-Cache, atomar via .part).
                from urllib.request import urlretrieve
                from core import ernte as _ernte
                import face_audit
                eid = job["eid"]
                scratch = os.environ.get("SCRATCH_DIR", "/tmp")
                vid = os.path.join(scratch, str(eid).replace("/", "_") + ".mp4")
                if not os.path.exists(vid):
                    frigate = os.environ["FRIGATE_URL"].rstrip("/")
                    try:
                        urlretrieve(f"{frigate}/api/events/{eid}/clip.mp4", vid + ".part")
                        os.replace(vid + ".part", vid)
                    except Exception:
                        try:                       # keine .part-Waisen im Cache
                            os.unlink(vid + ".part")
                        except FileNotFoundError:
                            pass
                        raise
                zusatz = _ernte.ernte_event(
                    vid, eid, job.get("kamera"), float(job.get("ts") or 0),
                    float(job.get("fps_sample") or 3), job["schwellen"],
                    job["lauf_dir"], emb=face_audit.Embedder())
            else:
                return {"ok": False, "fehler": f"unbekannter typ '{typ}'"}
        ok, fehler = True, None
    except SystemExit as e:                      # analyze bricht kontrolliert ab
        ok, fehler = (e.code in (0, None)), f"exit {e.code}"
    except Exception as e:
        ok, fehler = False, f"{type(e).__name__}: {e}"
    t1 = os.times()
    antwort = {"ok": ok,
               "cpu_s": round(t1.user - t0.user + t1.system - t0.system, 1),
               "wall_s": round(time.monotonic() - t0w, 1),   # additiv; Leser nutzen .get()
               "rss_mb": _rss_mb()}
    if zusatz:
        antwort.update(zusatz)
    if fehler:
        antwort["fehler"] = fehler
    return antwort


def _patch_embedder():
    global _EchterEmbedder
    import face_audit
    if _EchterEmbedder is None:
        _EchterEmbedder = face_audit.Embedder
        face_audit.Embedder = _factory


def main():
    _patch_embedder()
    idle_s = int(os.environ.get("WORKER_IDLE_S", "900"))
    fd = int(os.environ["WORKER_ANTWORT_FD"])
    out = os.fdopen(fd, "w", buffering=1)
    while True:
        r, _, _ = select.select([sys.stdin], [], [], idle_s)
        if not r:
            return                                # Idle-EXIT: nur Prozess-Ende gibt ORT-Arenas
                                                  # frei (Soak-Befund 27.07.); verifyd startet neu
        zeile = sys.stdin.readline()
        if not zeile:                             # EOF: verifyd weg/execv -> geordnet enden
            return
        try:
            job = json.loads(zeile)
        except Exception:
            out.write(json.dumps({"ok": False, "fehler": "job unlesbar"}) + "\n")
            continue
        out.write(json.dumps(_job_ausfuehren(job), ensure_ascii=False) + "\n")


def roundtrip(argv):
    """QS-Selbsttest: zwei analyze-Jobs (kalt+warm) ueber die echte Job-Mechanik."""
    _patch_embedder()
    log = os.path.join(os.environ.get("SCRATCH_DIR", "/tmp"), "worker_roundtrip.log")
    a = _job_ausfuehren({"typ": "analyze", "argv": argv, "log": log})
    # analyze resumed sonst via done_labels (results.jsonl) und Lauf 2 liefe LEER —
    # genau die Falle, die qs.sh S5 am 23.07. bei sich selbst fand. Clip-Cache (SCRATCH)
    # bleibt bewusst stehen: Lauf 2 soll die warme ANALYSE messen, nicht den Download.
    if "--dir" in argv:
        rj = os.path.join(argv[argv.index("--dir") + 1], "results.jsonl")
        if os.path.exists(rj):
            os.unlink(rj)
    b = _job_ausfuehren({"typ": "analyze", "argv": argv, "log": log})
    print(json.dumps({"lauf1": a, "lauf2": b}, ensure_ascii=False))
    sys.exit(0 if (a.get("ok") and b.get("ok")) else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--roundtrip":
        roundtrip(sys.argv[2:])
    else:
        main()
