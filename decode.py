#!/usr/bin/env python3
"""decode — die EINE Frame-Quelle fuer analyze/anlernen/abnahme (W1 der GPU-Welle, Plan v3).

Bis 0.1.0.34 trug jedes der drei Werkzeuge seine eigene Kopie derselben cv2-Schleife — und
alle drei hatten denselben stillen Fehler: `while cap.grab()` endet beim ERSTEN harten
Decode-Fehler kommentarlos, das Urteil entsteht dann aus dem lesbaren Anfang (am Glitch-
Archivstueck gemessen: cv2 liest 209 von 345 Paketen, 39 % still verloren — Fehlerklasse C).

Vertrag (bewusst BIT-EXAKT zum Bestand, Plan-QS R2/Lens1-5 — Kalibrierung haengt daran):
- Frame-Auswahl: jedes step-te Frame, step = round(fps / fps_sample), gezaehlt ueber den
  ORIGINAL-Frame-Index i. Die Zeitachse rechnet der Aufrufer wie bisher: t = i / fps.
- fps kommt aus cv2.CAP_PROP_FPS (= avg_frame_rate). NIE r_frame_rate nehmen — die HEVC-
  Kameras liefern dort 90000/1, step waere ~30000: Totalausfall bei gruenem Anschein.
- Die WACHE zaehlt gelesene Frames gegen die Container-Paketzahl (ffprobe -count_packets,
  ~0,14 s, KEIN Decode). Toleranz max(1, 2 %): CAP_PROP_FRAME_COUNT weicht regulaer um +-1
  ab, der Glitch-Fall liegt bei ~39 % — sauber trennbar. Reaktion ist Sache des Aufrufers
  (E1: analyze urteilt weiter + Flag; unter 50 % lesbar wertet verifyd als 'fehler').

Hinweis Historie: der 18.07.-VAAPI-Verwurf ("verlor bei HEVC-Glitches still Frames") lebte
frueher als Kommentar in analyze.frame_iter — der HW-Decode-Anlauf (W6) findet seine
Auflagen der GPU-Messreihe (W6); DIESE Datei bleibt der CPU-Referenzpfad.
"""
import subprocess

import cv2


def toleranz(soll):
    """max(1, 2 % aufgerundet) — eine Formel fuer Wache, Flag und Gate."""
    return max(1, (int(soll) * 2 + 99) // 100)


def frames_soll(vid):
    """Paketzahl des Videostreams (Soll fuer die Wache). None = nicht ermittelbar
    (ffprobe fehlt / Datei unlesbar) — die Wache bleibt dann neutral statt falsch zu warnen."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-count_packets", "-show_entries", "stream=nb_read_packets",
                            "-of", "csv=p=0", vid],
                           capture_output=True, text=True, timeout=30)
        n = int((r.stdout or "").strip())
        return n if n > 0 else None
    except Exception:
        return None


class FrameIter:
    """Iterierbar: liefert (i, frame_bgr) fuer jedes step-te Frame (i = Original-Index).
    Nach dem Durchlauf tragen .gelesen/.soll/.verlust_pct das Wache-Ergebnis;
    .unvollstaendig sagt, ob der Verlust ueber der Toleranz liegt."""

    def __init__(self, vid, fps_sample):
        self.vid = vid
        self._cap = cv2.VideoCapture(vid)
        self.fps = self._cap.get(cv2.CAP_PROP_FPS) or 25
        self.step = max(1, int(round(self.fps / float(fps_sample))))
        # H4: Clip-Geometrie fuer die AR-abhaengige det_size (face_audit.ar_det_size)
        self.breite = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        self.hoehe = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        self.soll = frames_soll(vid)
        self.gelesen = 0

    def __iter__(self):
        i = 0
        while self._cap.grab():
            self.gelesen = i + 1
            if i % self.step == 0:
                ok, frame = self._cap.retrieve()
                if ok:
                    yield i, frame
            i += 1
        self._cap.release()

    @property
    def verlust_pct(self):
        if not self.soll:
            return 0.0
        return max(0.0, 100.0 * (self.soll - self.gelesen) / self.soll)

    @property
    def unvollstaendig(self):
        if not self.soll:
            return False
        return (self.soll - self.gelesen) > toleranz(self.soll)
