#!/usr/bin/env python3
# INVARIANTE: GEPINNTER_PIXELPFAD   (Marke: CLAUDE.md "Gepinnter Pixelpfad")
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
HW-Decode ist damit NICHT opt-in, sondern per Default AN: env SUSLIK_HWDEC
ist ungesetzt gleichbedeutend mit 'auto' — h264/hevc gehen dann ueber die
HW-Pipe, Intel (VAAPI) zuerst, sonst NVIDIA (NVDEC). Werte: 'auto' (Default)
· 'vaapi'/'nvdec' = erzwingen · 'aus'/'off'/'0'/'nein' = nie. In JEDEM Modus
greifen dieselben harten Gates (s. _hwdec): nur 8-bit yuv420p/yuvj420p und
nur mit validierter Quelle (VA-Treiber + SUSLIK_HWDEC_DEVICE, Default
/dev/dri/renderD128, bzw. /dev/nvidiactl); faellt ein Gate, laeuft es
lautlos in Software. Scheitert die angeforderte HW-Pipe erst beim Decode,
faellt der Iterator LAUT (Flag .hwdec_fallback) auf Software zurueck —
gleiche Bytes, nur langsamer. Preis der Migration: einmalige Soll-Neueinfrierung (E3);
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
# INVARIANTE-ENDE: GEPINNTER_PIXELPFAD
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
        # .536 B1a: stdin=DEVNULL. ffprobe kennt kein `-nostdin` — hier ist die
        # abgeklemmte Quelle des fd 0 der einzige Riegel. Er zaehlt, weil dieser
        # Probe-Lauf im Worker vor JEDEM FrameIter steht.
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-count_packets", "-show_entries",
                            "stream=codec_name,pix_fmt,width,height,"
                            "avg_frame_rate,nb_read_packets",
                            "-of", "json", vid],
                           stdin=subprocess.DEVNULL,
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
    # Verfuegbarkeits-Praedikate ausgelagert (va_da/nv_da, Dateiende): auch
    # der Live-Leser (core/livewache.hw_wahl) waehlt an DENSELBEN Kriterien
    # (eine Quelle, kein zweites Rezept — K3-Regel).
    va, nv = va_da(), nv_da()
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


# ------------------------------------------------------------------ Sample-Budget
# .540 K-DECKEL (Inhaber-Entscheid 17.09.2026, Anlass Discussion #30).
#
# DAS PROBLEM, gemessen: die Abtastung war bis hier allein ein ZEITRASTER
# (jedes step-te Frame, step = fps/fps_sample) — also waechst die Rechenarbeit
# eines Ereignisses linear mit seiner Laenge, ohne jede Obergrenze. Am echten
# Bestand (Auswertung 17.09., 9659 Prod-Ereignisse GEMESSEN + 50068 Feld-
# Ereignisse abgeleitet) traegt das TEUERSTE PROZENT der Ereignisse 12-16 % der
# gesamten Rechenarbeit, das teuerste Zehntel 43,5 %; der Spitzenfall auf Prod
# waren 4464 Sample-Frames = 1320 s Analyse fuer EIN Ereignis. Genau solche
# Ereignisse blockieren beim Feldtester einen Rechenstrang, waehrend die
# Schlange waechst.
#
# DIE REGEL: hoechstens `deckel` Sample-Frames je Clip, und zwar GLEICHMAESSIG
# ueber die ganze Cliplaenge verteilt — kein Frueh-Stopp. Ein Frueh-Stopp waere
# die naheliegende, aber falsche Loesung: er wuerde die letzte Minute eines
# langen Auftritts gar nicht mehr ansehen, und der beste Gesichtswinkel liegt
# genauso oft hinten wie vorn (Szenario-Prinzip). Deshalb wird nicht abgebrochen,
# sondern die SCHRITTWEITE vergroessert: `select='not(mod(n,step))'` laeuft
# unveraendert bis zum Clip-Ende, nur weiter auseinander. Die erste und die
# letzte Clip-Region sind danach exakt gleich dicht abgetastet.
#
# WERKSWERT 240 (~80 s Clip bei fps_sample 3): er liegt sauber ueber dem P95
# BEIDER Bestaende (201 bzw. 211 Sample-Frames) und beschneidet 3,8 % / 3,9 %
# der Ereignisse; gespart werden 16,5 % / 12,5 % der Sample-Frames. Die Zahl ist
# ein Quantil, kein Mittelwert — ein Mittelwert (72,8 / 65,0) haette das normale
# Material beschnitten.
#
# EHRLICHE GRENZEN, beide bewusst getragen:
#  - Bestaetigte Ereignisse sind LAENGER als der Schnitt (P90 267 gegen 135 im
#    Feld), ein Deckel trifft sie also 2- bis 3-fach haeufiger als den
#    Durchschnitt. Die Risiko-Naeherung der Auswertung sagt fuer 240 zwar 0,00 %,
#    aber sie rechnet linear und kennt die zeitliche Verteilung der Treffer
#    nicht. Wer es belastbar will, muss die betroffenen Ereignisse nachrechnen.
#  - Der Deckel aendert die FRAME-AUSWAHL, nicht nur ihre Anzahl. Fixpunkt- und
#    Ankerlaeufe, die auf der heutigen Index-Menge beruhen, verschieben sich,
#    sobald er greift. Deshalb ist 0 = aus die Haus-Konvention und der Wert ein
#    Job-Feld: ein Messlauf faehrt ohne Deckel und vergleicht dann Gleiches.
#
# DIESE FUNKTION IST DIE EINE QUELLE der Schrittweite. Vor .540 stand die Formel
# dreimal da (hier, worker_kern.auftrag_rechnen, worker_dienst.JobLauf) — zweimal
# davon mit dem Kommentar „wie decode.py:148", also schon damals als Abschrift
# gekennzeichnet. Eine zweite, driftende Formel gibt es jetzt nicht mehr.


def samples_bei(pakete, schritt):
    """Wie viele Sample-Frames ein Clip mit dieser Schrittweite liefert.
    Indexbasis wie `FrameIter._pipe`: geliefert werden 0, schritt, 2*schritt …
    bis < pakete. None/0 Pakete = unbekannt -> 0."""
    n = int(pakete or 0)
    s = max(1, int(schritt))
    return ((n - 1) // s) + 1 if n > 0 else 0


def sample_schritt(fps, fps_sample, pakete=None, deckel=0):
    """DIE Schrittweite eines Clips — Zeitraster, gedeckelt auf `deckel` Samples.

    -> (schritt, moeglich, verwendet)
       schritt    jedes schritt-te ORIGINAL-Frame wird abgetastet
       moeglich   Sample-Frames ohne Deckel (None = Paketzahl unbekannt)
       verwendet  Sample-Frames mit Deckel   (None = dito)

    `deckel <= 0` heisst AUS (Haus-Konvention) und liefert exakt das Verhalten
    vor .540. Ohne Paketzahl (`pakete` None/0 — ffprobe hat nichts geliefert)
    kann nicht gedeckelt werden: dann gilt das Zeitraster, und der Aufrufer
    bekommt `(schritt, None, None)`. Fail-open ist hier richtig — ein Ereignis
    ungedeckelt zu rechnen ist teuer, es gar nicht zu rechnen waere ein Verlust."""
    zeit = max(1, int(round(float(fps) / float(fps_sample))))
    n = int(pakete or 0)
    if n <= 0:
        return zeit, None, None
    moeglich = samples_bei(n, zeit)
    k = int(deckel or 0)
    if k <= 0 or moeglich <= k:
        return zeit, moeglich, moeglich
    # Kleinste Schrittweite, die hoechstens k Samples liefert: geliefert werden
    # die Indizes 0, s, 2s … also samples = (n-1)//s + 1 <= k  <=>  s >= (n-1)/(k-1).
    # Aufgerundet ist das die exakte Untergrenze (k = 1 ist der Sonderfall „ein
    # einziges Frame" — dann reicht jede Schrittweite ab n).
    gross = n if k <= 1 else -(-(n - 1) // (k - 1))
    schritt = max(zeit, gross)
    return schritt, moeglich, samples_bei(n, schritt)


class FrameIter:
    """Iterierbar: liefert (i, frame_bgr) fuer jedes step-te Frame (i = Original-Index).
    Nach dem Durchlauf tragen .gelesen/.soll/.verlust_pct das Wache-Ergebnis;
    .unvollstaendig sagt, ob der Verlust ueber der Toleranz liegt.
    .hwdec sagt, ob die HW-Pipe lief; .hwdec_fallback, ob sie angefordert war
    und auf Software zurueckgefallen ist (gleiche Bytes, nur langsamer)."""

    def __init__(self, vid, fps_sample, deckel=0):
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
        self.soll = self.meta.get("pakete")
        # .540 K-Deckel: die Schrittweite kommt aus der EINEN Formel oben.
        # `deckel=0` (Vorgabe) liefert exakt das Zeitraster von vor .540 —
        # alle Wege, die keinen Deckel durchreichen (Ernte, Sammeln, der
        # Frame-Verteiler core/frames), verhalten sich also unveraendert.
        self.deckel = int(deckel or 0)
        self.step, self.samples_moeglich, _verw = sample_schritt(
            self.fps, fps_sample, self.soll, self.deckel)
        self.gekappt = bool(self.samples_moeglich is not None
                            and _verw is not None and _verw < self.samples_moeglich)
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
        # .536 B1a: `-nostdin` — ffmpeg darf den fd 0 seines Elternprozesses
        # nicht pollen. Im Worker ist das die Job-Pipe (Byte-Beweis im Kopf von
        # worker_kern.nv12_strom). Kein Eingriff in den Pixelpfad: der Schalter
        # betrifft allein den Tastatur-Poll, nicht Decoder, Filter oder Format.
        basis = ["ffmpeg", "-nostdin", "-v", "warning"]   # warning: Concealment-Zeilen sichtbar (Wache-Quelle)
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
            # .536 B1a: stdin=DEVNULL, der zweite Riegel neben `-nostdin`
            # (s. _kommando). Diese Pipe laeuft im Worker auf dem Sammel- und
            # Ernte-Weg (anlernen.py:164/437, core/ernte.py).
            p = subprocess.Popen(self._kommando(hw), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,
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
                    # INVARIANTE: GEPINNTER_PIXELPFAD   (Marke: CLAUDE.md "Gepinnter Pixelpfad")
                    # HIER steht der gepinnte Pfad, nicht nur im Docstring oben:
                    # rawvideo yuv420p aus der ffmpeg-Pipe -> DIE eine YUV->BGR-
                    # Konvertierung. Nicht durch swscale (-pix_fmt bgr24 im
                    # Kommando) oder cv2.VideoCapture ersetzen — die weichen um
                    # mittl. ~1,5 Graustufen ab (Kanten 40+) und kippen Urteile.
                    yield i, cv2.cvtColor(y, cv2.COLOR_YUV2BGR_I420)
                    # INVARIANTE-ENDE: GEPINNTER_PIXELPFAD
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


# ---------------------------------------------------------------------------
# Verfuegbarkeits-Praedikate der HW-Decode-Wahl — EINE Quelle fuer _hwdec
# (oben) UND den Live-Leser (core/livewache.hw_wahl, Runde cuda-nvdec):
# wer ein Kriterium aendert, aendert beide Nutzer mit. Bewusst am Dateiende,
# damit die dokumentierten Zeilen-Anker (decode.py:1-30, :243) stabil bleiben.

def va_da():
    """Intel-VAAPI verfuegbar: Render-Node (SUSLIK_HWDEC_DEVICE, Default
    /dev/dri/renderD128) UND validierter VA-Treiber (_va_treiber, iHD/i965).
    Blosse Knoten-Existenz genuegt NICHT (Panel-Fund, s. _va_treiber)."""
    return (os.path.exists(os.environ.get("SUSLIK_HWDEC_DEVICE",
                                          "/dev/dri/renderD128"))
            and _va_treiber())


def nv_da():
    """NVIDIA-Runtime im Container: /dev/nvidiactl (Kriterium unveraendert
    aus der _hwdec-Historie; NVDEC-Byte-Beweis am NB 05.08.)."""
    return os.path.exists("/dev/nvidiactl")


# ---------------------------------------------------------------------------
# DIE BYTE-PROBE (E6, 17.09.2026) — das Nachmess-Werkzeug zum gepinnten Pfad.
#
# WOZU. Der Beweis vom 04.08.2026, auf dem der gepinnte Pixelpfad steht (HW-Decode
# liefert BIT-IDENTISCHE Rohpixel wie Software, md5 ueber rawvideo, h264-4K /
# hevc-4K / hevc-1080p), ist auf INTEL gefuehrt worden. Auf AMD/mesa ist er
# UNGEMESSEN, auf jeder fremden Anlage ebenso. Diese Funktion ist genau dieser
# Vergleich, verpackt so, dass ihn ein Nutzer auf SEINER Maschine fahren kann:
# `docker exec <container> python verifyd.py --benchmark` druckt den Abschnitt
# „decode byte probe" und die Zeilen sind direkt postbar.
#
# KEINE ZWEITE IMPLEMENTIERUNG: gemessen wird die PRODUKTIONS-Kette, geholt ueber
# `FrameIter._kommando` — dieselben ffmpeg-Argumente, derselbe select-vor-Transfer,
# dasselbe rawvideo-Format. Verglichen werden die Bytes, die der Iterator in
# `cv2.cvtColor` gibt, nicht irgendein Ersatzstrom.
#
# KEIN AUTOMATISCHER SELBSTTEST (Inhaber-Entscheid 17.09.2026): der Vergleich laeuft
# AUSSCHLIESSLICH manuell von aussen. „Es macht keinen Sinn, jedes Mal einen
# Bit-Vergleich zu machen" — im Dienstbetrieb ruft diese Funktion niemand.
#
# WARUM DIE PROBE NICHT `_hwdec` FRAGT: `_hwdec` laesst ueber `_va_treiber` nur die
# validierten Intel-Treiber (iHD/i965) durch und sperrt radeonsi ausdruecklich aus.
# Das ist fuer den BETRIEB eine bewusste Sperre — aber eine Messung, die genau
# diesen ungetesteten Decoder pruefen soll, darf nicht an ihr scheitern. Die Probe
# waehlt deshalb am GERAET (Render-Node bzw. NVIDIA-Knoten) und sagt dazu, welchen
# VA-Treiber sie gefunden hat.
_PROBE_BLOCK = 1 << 20


def _md5_strom(cmd, deckel_s):
    """Ein ffmpeg-Lauf, md5 ueber ALLES, was er auf stdout schreibt.
    -> (md5|None, bytes, sekunden, rc, fehlertext)"""
    import hashlib
    import tempfile
    import time as _t
    h, n, t0 = hashlib.md5(), 0, _t.monotonic()
    with tempfile.TemporaryFile() as err:
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=err)
        abbruch = None
        try:
            while True:
                b = p.stdout.read(_PROBE_BLOCK)
                if not b:
                    break
                h.update(b)
                n += len(b)
                if deckel_s and (_t.monotonic() - t0) > deckel_s:
                    abbruch = f"aborted after {deckel_s:.0f}s"
                    p.kill()
                    break
        finally:
            p.stdout.close()
            rc = p.wait()
        text = ""
        try:
            err.seek(0)
            text = err.read(8000).decode("utf-8", "replace").strip()
        except OSError:
            pass
    if abbruch:
        return None, n, _t.monotonic() - t0, rc, abbruch
    if rc != 0:
        # Die AUSSAGEKRAEFTIGE Zeile, nicht die letzte: ffmpeg haengt an sein
        # stderr gern noch „Last message repeated N times" und Task-Abschluss-
        # Zeilen an, und genau die stuenden sonst als Diagnose im Feld-Log.
        zeilen = [z.strip() for z in text.splitlines() if z.strip()]
        zeilen = [z for z in zeilen
                  if "Last message repeated" not in z
                  and "Terminating thread" not in z
                  and "Task finished with error code" not in z]
        return None, n, _t.monotonic() - t0, rc, " | ".join(zeilen[:2])[:300]
    if n == 0:
        return None, 0, _t.monotonic() - t0, rc, "delivered 0 bytes"
    return h.hexdigest(), n, _t.monotonic() - t0, rc, ""


def hw_geraet():
    """Welche HW-Decode-Quelle diese Maschine ueberhaupt anbieten koennte, und
    womit. -> (art|None, beschreibung)

    Am GERAET entschieden, nicht an der Betriebs-Politik (s. Block oben)."""
    import glob as _g
    node = os.environ.get("SUSLIK_HWDEC_DEVICE", "/dev/dri/renderD128")
    if os.path.exists(node):
        treiber = sorted(os.path.basename(p) for p in
                         _g.glob("/usr/lib/*/dri/*_drv_video.so"))
        return "vaapi", (f"{node}, VA drivers: "
                         + (", ".join(treiber) if treiber else "none found"))
    if nv_da():
        return "nvdec", "/dev/nvidiactl (NVIDIA runtime)"
    return None, (f"no usable hardware decode device "
                  f"(neither {node} nor /dev/nvidiactl)")


def byte_probe(vid, fps_sample=2.0, deckel_s=180.0):
    """EIN Clip durch BEIDE Decode-Ketten, md5 ueber das rawvideo. -> dict

    Die Felder sind so gewaehlt, dass der Aufrufer daraus eine EINZEILIGE Aussage
    machen kann: `verdikt` ist 'bitgleich' / 'abweichend' / 'kein-hw' / 'fehler',
    `grund` traegt den Klartext, wenn es nicht 'bitgleich' ist.

    EHRLICH BENANNT: ein 'bitgleich' bezieht sich auf GENAU diesen Clip mit GENAU
    diesem Codec und dieser Aufloesung auf DIESER Maschine. Es ist keine Aussage
    ueber andere Clips und keine ueber den naechsten Treiber."""
    it = FrameIter(vid, fps_sample)
    art, beschreibung = hw_geraet()
    aus = {"clip": os.path.basename(vid), "codec": it.meta.get("codec"),
           "pix_fmt": it.meta.get("pix_fmt"), "breite": it.breite,
           "hoehe": it.hoehe, "step": it.step, "hw": art, "geraet": beschreibung,
           "md5_hw": None, "md5_sw": None, "bytes": 0,
           "s_hw": None, "s_sw": None, "verdikt": "fehler", "grund": ""}
    if not (it.breite and it.hoehe):
        aus["grund"] = "no video geometry (ffprobe and cv2 both silent)"
        return aus
    if art is None:
        aus["verdikt"] = "kein-hw"
        aus["grund"] = beschreibung
        return aus
    if it.meta.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        # Dasselbe harte Gate wie im Betrieb (_hwdec): p010 durch format=nv12 ergibt
        # ein FALSCHES Bild. Ein Vergleich waere hier nicht „abweichend", sondern
        # sinnlos — also wird er gar nicht erst gefahren.
        aus["verdikt"] = "kein-hw"
        aus["grund"] = (f"pixel format {it.meta.get('pix_fmt')!r} is not 8-bit "
                        f"yuv420p — hardware decode is off for this clip by design")
        return aus
    md5_hw, n_hw, s_hw, _rc, f_hw = _md5_strom(it._kommando(art), deckel_s)
    aus["s_hw"] = round(s_hw, 1)
    if md5_hw is None:
        aus["grund"] = f"hardware chain ({art}) failed: {f_hw}"
        return aus
    md5_sw, n_sw, s_sw, _rc2, f_sw = _md5_strom(it._kommando(None), deckel_s)
    aus["s_sw"] = round(s_sw, 1)
    if md5_sw is None:
        aus["grund"] = f"software chain failed: {f_sw}"
        return aus
    aus.update({"md5_hw": md5_hw, "md5_sw": md5_sw, "bytes": n_hw})
    if n_hw != n_sw:
        aus["verdikt"] = "abweichend"
        aus["grund"] = (f"different amount of data: hardware {n_hw} bytes, "
                        f"software {n_sw} bytes")
        return aus
    aus["verdikt"] = "bitgleich" if md5_hw == md5_sw else "abweichend"
    if aus["verdikt"] == "abweichend":
        aus["grund"] = "same size, different bytes"
    return aus
