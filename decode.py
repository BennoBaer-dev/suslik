#!/usr/bin/env python3
"""decode — die EINE Frame-Quelle fuer analyze/anlernen/abnahme (W1 der GPU-Welle, Plan v3).

MIGRATION 04.08.2026 (User-Go, messgefuehrt — 'gepinnter Pixelpfad'):
Byte-Beweis am 04.08.: HW-Decode (VAAPI) liefert BIT-IDENTISCHE YUV-Rohpixel
wie der Software-Decode (md5 ueber rawvideo, h264-4K/hevc-4K/hevc-1080p).
Das alte W6-Verdikt (0,02-NN-Shift) war fehl-attribuiert: nicht der Decoder
wich ab, sondern die YUV->BGR-KONVERTIERUNG (cv2.VideoCapture intern vs
swscale-Varianten: mittl. ~1,5 Graustufen, Kanten bis 40+). Deshalb gilt ab
jetzt EIN gepinnter Pfad fuer alle Urteils-Frames:

    ffmpeg-Decode (SW oder HW, beweisbar bitgleich) -> rawvideo yuv420p
    -> cv2.cvtColor(COLOR_YUV2BGR_I420)   [DIE eine Konvertierung]

Damit ist die Frame-Quelle auf jeder Hardware identisch BY CONSTRUCTION —
die alte Invariante 'Analyse-Decode bleibt CPU' wird ersetzt durch
'Analyse-KONVERTIERUNG bleibt cvtColor-I420, Decode-Quelle frei'.
HW-Decode ist opt-in via env SUSLIK_HWDEC=vaapi (+SUSLIK_HWDEC_DEVICE,
Default /dev/dri/renderD128); scheitert die HW-Pipe, faellt der Iterator
LAUT (Flag .hwdec_fallback) auf Software zurueck — gleiche Bytes, nur
langsamer. Preis der Migration: einmalige Soll-Neueinfrierung (E3);
Referenz-JPEGs (cv2.imread-Weg) sind NICHT betroffen.

Vertrag (unveraendert zur cv2-Aera, Kalibrierung haengt daran):
- Frame-Auswahl: jedes step-te Frame, step = round(fps / fps_sample),
  gezaehlt ueber den ORIGINAL-Frame-Index i; Zeitachse t = i / fps.
- fps aus cv2.CAP_PROP_FPS (= avg_frame_rate). NIE r_frame_rate (HEVC-
  Kameras liefern dort 90000/1 — Totalausfall bei gruenem Anschein).
- Die WACHE zaehlt gelesene Frames gegen die Container-Paketzahl
  (ffprobe -count_packets); Toleranz max(1, 2 %). Reaktion ist Sache des
  Aufrufers (analyze urteilt weiter + Flag; verifyd wertet <50 % als Fehler).
"""
import os
import subprocess

import cv2
import numpy as np


def toleranz(soll):
    """max(1, 2 % aufgerundet) — eine Formel fuer Wache, Flag und Gate."""
    return max(1, (int(soll) * 2 + 99) // 100)


def _probe(vid):
    """EIN ffprobe fuer alle Metadaten (Panel-Fund: 3 Parser = 217 ms je Clip,
    einer = 93 ms). Rueckgabe dict oder {} — Aufrufer faellt auf cv2 zurueck."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-count_packets", "-show_entries",
                            "stream=codec_name,pix_fmt,width,height,"
                            "avg_frame_rate,nb_read_packets",
                            "-of", "json", vid],
                           capture_output=True, text=True, timeout=30)
        import json as _json
        s = (_json.loads(r.stdout or "{}").get("streams") or [{}])[0]
        z, n = (s.get("avg_frame_rate") or "0/1").split("/")
        fps = (float(z) / float(n)) if float(n or 0) else 0.0
        return {"codec": s.get("codec_name"), "pix_fmt": s.get("pix_fmt"),
                "breite": int(s.get("width") or 0),
                "hoehe": int(s.get("height") or 0), "fps": fps,
                "pakete": int(s.get("nb_read_packets") or 0) or None}
    except Exception:
        return {}


def frames_soll(vid):
    """Paketzahl des Videostreams (Soll fuer die Wache). None = neutral."""
    return _probe(vid).get("pakete")


_VA_OK = None                     # einmal je Prozess: validierter VA-Treiber da?


def _va_treiber():
    """Nur die VALIDIERTEN Intel-Treiber zaehlen (iHD/i965) — Panel-Fund:
    cpu/cuda-Images haben gar keinen VA-Treiber (Knoten-Existenz genuegt
    nicht), und rocm traegt radeonsi (AMD-VAAPI = UNGETESTETER Decoder,
    darf nie stillschweigend per auto aktiv werden)."""
    global _VA_OK
    if _VA_OK is None:
        import glob as _g
        treiber = {os.path.basename(p) for p in
                   _g.glob("/usr/lib/*/dri/*_drv_video.so")}
        _VA_OK = bool(treiber & {"iHD_drv_video.so", "i965_drv_video.so"})
    return _VA_OK


def _hwdec(meta=None):
    """HW-Decode-Politik ('vaapi'/'nvdec'/None). Nur die QUELLE der Bytes —
    die Konvertierung danach ist immer dieselbe (gepinnter Pfad, s. Kopf).
    SUSLIK_HWDEC: 'auto' (Default) = h264+hevc, Intel zuerst, sonst NVIDIA
    (Select-Messung 04.08.: hevc −65 %, h264 −58 % CPU-s) · 'vaapi'/'nvdec'
    = erzwingen · 'aus' = nie. HARTE GATES in jedem Modus: nur 8-bit
    yuv420p (Panel-Fund: p010 durch format=nv12 = FALSCHES Bild) und nur
    mit validierter Quelle (Intel-VA-Treiber+Geraet bzw. NVIDIA-Runtime;
    NVDEC-Byte-Beweis auf dem NB 05.08.)."""
    m = (os.environ.get("SUSLIK_HWDEC") or "auto").strip().lower()
    if m in ("aus", "off", "0", "nein"):
        return None
    meta = meta or {}
    if meta.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        return None
    va = (os.path.exists(os.environ.get("SUSLIK_HWDEC_DEVICE",
                                        "/dev/dri/renderD128"))
          and _va_treiber())
    nv = os.path.exists("/dev/nvidiactl")     # NVIDIA-Runtime im Container
    if m == "vaapi":
        return "vaapi" if va else None
    if m == "nvdec":
        return "nvdec" if nv else None
    if m == "auto" and meta.get("codec") in ("h264", "hevc"):
        if va:
            return "vaapi"
        if nv:
            return "nvdec"
    return None


class FrameIter:
    """Iterierbar: liefert (i, frame_bgr) fuer jedes step-te Frame (i = Original-Index).
    Nach dem Durchlauf tragen .gelesen/.soll/.verlust_pct das Wache-Ergebnis;
    .unvollstaendig sagt, ob der Verlust ueber der Toleranz liegt.
    .hwdec sagt, ob die HW-Pipe lief; .hwdec_fallback, ob sie angefordert war
    und auf Software zurueckgefallen ist (gleiche Bytes, nur langsamer)."""

    def __init__(self, vid, fps_sample):
        self.vid = vid
        self.meta = _probe(vid)              # EIN Parser fuer alle Metadaten
        if not self.meta.get("breite"):      # Fallback: cv2-Metadaten (kein Decode)
            cap = cv2.VideoCapture(vid)
            self.meta = {"codec": None, "pix_fmt": None,
                         "fps": cap.get(cv2.CAP_PROP_FPS) or 0,
                         "breite": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
                         "hoehe": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
                         "pakete": None}
            cap.release()
        self.fps = self.meta["fps"] or 25
        self.breite, self.hoehe = self.meta["breite"], self.meta["hoehe"]
        self.step = max(1, int(round(self.fps / float(fps_sample))))
        self.soll = self.meta.get("pakete")
        self.gelesen = 0
        self.samples = 0
        self.hwdec = False
        self.hwdec_fallback = False
        self.rc = None                       # ffmpeg-Exitcode des letzten Laufs
        self.decoder_fehler = 0              # Fehlerzeilen aus ffmpeg-stderr
        self._proc = None                    # laufende ffmpeg-Pipe (s. abbrechen)
        self.abgebrochen = False

    def _kommando(self, hw):
        # SELECT VOR TRANSFER (User-Idee 04.08., gemessen -45..-59 %): die
        # Auswahl "jedes step-te Frame" laeuft als ffmpeg-select DIREKT nach
        # dem Decode — bei HW noch VOR dem GPU->RAM-Download. Es verlassen
        # nur die gebrauchten Frames den Decoder; die gelieferten Bilder
        # sind BYTE-IDENTISCH zur frueheren Python-seitigen Auswahl
        # (Gate-A-Beweis), nur der Ballast der Zwischenframes entfaellt.
        basis = ["ffmpeg", "-v", "warning"]   # warning: Concealment-Zeilen sichtbar (Wache-Quelle)
        if hw == "vaapi":
            dev = os.environ.get("SUSLIK_HWDEC_DEVICE", "/dev/dri/renderD128")
            basis += ["-hwaccel", "vaapi", "-hwaccel_device", dev,
                      "-hwaccel_output_format", "vaapi"]
        elif hw == "nvdec":                    # NVIDIA: gleiche Kette, andere Byte-Quelle
            basis += ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        basis += ["-i", self.vid, "-map", "0:v:0"]
        sel = f"select='not(mod(n\\,{self.step}))'"
        rest = "hwdownload,format=nv12,format=yuv420p" if hw else "format=yuv420p"
        return basis + ["-vf", f"{sel},{rest}", "-fps_mode", "passthrough",
                        "-f", "rawvideo", "-"]

    def _pipe(self, hw):
        """Sample-Frames der Pipe als (i, frame_bgr); i = ORIGINAL-Index
        (k-tes geliefertes Frame ist Original-Frame k*step — exakt die
        fruehere i%step==0-Auswahl, nur ffmpeg-seitig)."""
        fsz = self.breite * self.hoehe * 3 // 2
        if fsz <= 0:
            return
        import tempfile
        # stderr in Datei statt DEVNULL (Panel-Fund: ffmpeg CONCEALED kaputte
        # Pakete und liefert rc=0 bei vollem Frame-Zaehler — cv2 brach frueher
        # ab und die Wache sah den Verlust. Die Fehlerzeilen sind jetzt die
        # einzige ehrliche Quelle fuer 'Bild-Inhalt beschaedigt'.)
        with tempfile.TemporaryFile() as err:
            p = subprocess.Popen(self._kommando(hw), stdout=subprocess.PIPE,
                                 stderr=err, bufsize=fsz * 2)
            self._proc = p                    # Griff fuer abbrechen() (Z5)
            try:
                k = 0
                while True:
                    b = p.stdout.read(fsz)
                    if len(b) < fsz:
                        break
                    i = k * self.step
                    self.samples = k + 1
                    self.gelesen = i + 1      # Fortschritt in Original-Indizes
                    y = np.frombuffer(b, dtype=np.uint8) \
                        .reshape(self.hoehe * 3 // 2, self.breite)
                    yield i, cv2.cvtColor(y, cv2.COLOR_YUV2BGR_I420)
                    k += 1
            finally:
                self._proc = None
                p.stdout.close()
                self.rc = p.wait()
                try:
                    err.seek(0)
                    text = err.read(65536).decode("utf-8", "replace")
                    # Bei -v warning ist JEDE Decoder-Kontext-Zeile eine
                    # Auffaelligkeit (gesunde Clips: exakt 0; Glitch-Clip:
                    # cu_qp_delta/undecodable-NALU-Serien) — Schlagwort-
                    # Listen waeren ein Streu-Literal je Codec/Version.
                    self.decoder_fehler = sum(
                        1 for z in text.splitlines() if " @ 0x" in z)
                except OSError:
                    pass

    def __iter__(self):
        hw = _hwdec(self.meta)
        if hw:
            self.gelesen = 0
            geliefert = False
            for i, f in self._pipe(hw):
                geliefert = True
                self.hwdec = True
                yield i, f
            if not geliefert:
                # HW-Pipe hat NICHTS geliefert (Treiber/Geraet) -> Software-
                # Neustart; die Bytes sind beweisbar dieselben.
                self.hwdec_fallback = True
            elif self.rc not in (0, None) or self.unvollstaendig:
                # Panel-Fund: VAAPI kann MITTEN im Clip sterben (real rc=251
                # nach Teillieferung). Bereits gelieferte Frames sind beim
                # Konsumenten — nicht rueckholbar. Ehrliche Reaktion wie die
                # cv2-Aera bei Teilverlust: Wache/Flags melden (der Aufrufer
                # urteilt den lesbaren Teil + Flag), Fallback-Flag zeigt an,
                # dass der SW-Pfad den Clip evtl. weiter lesen koennte.
                self.hwdec_fallback = True
                return
            else:
                return
        self.gelesen = 0
        yield from self._pipe(None)

    def abbrechen(self):
        """Die laufende ffmpeg-Pipe von AUSSEN beenden — Zeitwache Stufe (b)
        des Frame-Verteilers (konzept_frames.md v2 §3.2 zeitwache_s). Zwischen
        zwei Frames greift sonst keine Wache: haengt der Pipe-Read, haengt der
        ganze Lauf bis zum Job-Deckel des Aufrufers.

        KEIN killpg (bewusst, W1-Lehre): die Pipe laeuft absichtlich in der
        Prozessgruppe des Aufrufers, damit verifyds killpg auf den Worker auch
        ffmpeg-ENKEL mitnimmt (verifyd.py:659). Ein eigenes start_new_session
        haette genau diesen Schutz zerschnitten und den 480-MB-ffmpeg-Zombie
        zurueckgebracht. ffmpeg hat selbst keine Kinder — .kill() genuegt: der
        blockierende read() bekommt EOF, die Schleife bricht ab und das
        bestehende finally raeumt (rc lesen, stderr auswerten) unveraendert.

        Threadsicher genug per Konstruktion: gelesen wird EIN Attribut, das
        nur der Lese-Thread setzt und loescht; ist es None, war die Pipe schon
        zu. Rueckgabe: True = Signal ging raus."""
        self.abgebrochen = True
        p = self._proc
        if p is None:
            return False
        try:
            p.kill()
        except Exception:
            return False
        return True

    @property
    def _soll_samples(self):
        """Erwartete Sample-Zahl bei vollstaendigem Clip (Wache-Basis seit
        Select-vor-Transfer: die Pipe liefert nur noch die Samples, also
        prueft die Wache Samples gegen Soll-Samples statt Frames gegen
        Pakete — gleiche Toleranz-Formel, gleiche Fehlerklasse)."""
        if not self.soll:
            return None
        return (int(self.soll) + self.step - 1) // self.step

    @property
    def verlust_pct(self):
        s = self._soll_samples
        if not s:
            return 0.0
        return max(0.0, 100.0 * (s - self.samples) / s)

    @property
    def unvollstaendig(self):
        s = self._soll_samples
        if s and (s - self.samples) > toleranz(s):
            return True
        # Concealment-Ehrlichkeit (Panel-Fund): ffmpeg dekodiert kaputte
        # Clips mit rc=0 und vollem Zaehler DURCH und verfaelscht still die
        # Bilder (gemessen: 61 % der Samples, median 33 Graustufen). Die
        # cv2-Aera brach ab und die Wache schlug an — dieselbe Fehlerklasse
        # meldet jetzt der stderr-Zaehler.
        basis = s or self.samples or 1
        return self.decoder_fehler > toleranz(basis)
