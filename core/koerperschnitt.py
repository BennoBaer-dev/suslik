"""Der Cutter: schneidet aus dem Video eines Ereignisses wenige Koerperbilder (Koerperweg neu, Stufe KW3).

HERKUNFT: Bauplan analysen/bauplan_koerperweg_neu.md (Fassung 6, vom Eigentuemer abgenommen 20.11.2026 17:25:28), Stufe
KW3 Punkte 1 bis 4; Konzept analysen/konzept_koerperbilder_extralauf.md Abschnitt 4. Der Eigentuemer 20.11.2026: „Da soll
moeglichst viel uebernommen werden" (16:57:35), die Arbeit laeuft im eigenen Koerper-Prozess (Entscheid B, 16:42:49),
Dekodieren auf der GPU und Pose und Fingerabdruck auf der CPU (Entscheid P, 16:54:51), und Frigates Schnappschuss ist nur
der Uhr-Anker, nie selbst ein Koerperbild (15:21:05).

UEBERNOMMEN (Rechnung Zeile fuer Zeile, geaendert nur, wo der Plan es verlangt oder hier genannt ist; die Originale
liegen seit Stufe KW6 im Archiv des Projekts unter archiv/koerperweg_alt/, gleiche Pfade darunter):
  prototyp/pfad_snapshots.py   anker_finden, snapshot_holen, Koerper (Abnehmer mit RAM-Gate), bestbilder
  prototyp/frame_vergleich.py  bewegungs_box, schaerfe
  prototyp/ernte_lauf.py       person_zuschnitt, blick_bestimmen (die Pose-Schwelle kommt von der Wache, nicht aus dem
                               Prototyp: `wache.schwelle`, derselbe Wert)
  core/personmodell.py         _providers, _bindung_pruefen, session_bauen, _modell_pfad, BACKBONES["omz0277"], MEAN,
                               STD als Fingerabdruck ohne Training; _person_backend als Lesestelle des Werts
GEAENDERT: bestbilder liefert alle Kandidaten statt der drei groessten und kennt die Zeitregel (KW3 Punkt 2); jeder
Kandidat traegt seine Bildzeit, und sein Ausschnitt ist eine Kopie (das Frame darf mit dem Puffer gehen); die Gruende
sind englische Kurztexte (GRUENDE) statt deutscher Prosa; Koerper meldet ueber core.logbuch statt print und bekommt die
Frigate-Adresse als Argument; ein Ereignis ohne end_time faellt im Vorbereiten aus (ohne Ende keine Spanne);
_person_backend liest den Wert aus dem Auftrag (Lesart 5).

ABLAUF EINES AUFTRAGS (schnitt_job, Typ koerperschnitt im Koerper-Prozess worker.py; art cutter oder abfrage):
  1. nur cutter: das person.png des Bestbild-Satzes derselben Person im selben Ereignis; fehlt es, Ausfall
  2. Frigate ueber core.frigate_auth: Ereignis (box, path_data, snapshot_frame_time, start_time, end_time) und der
     Schnappschuss als Uhr-Anker
  3. der Clip nur aus dem Cache (der Dienst holt ihn vorher)
  4. EIN Frame-Lauf ueber core.frames.lauf am decode.FrameIter mit RAM-Gate; Zeitwache EVENT_ZEITWACHE_S; reisst sie
     oder wird der Abnehmer abgeworfen, faellt das Video aus, Teilmaterial wird nicht ausgewertet
  5. bestbilder: Uhr-Anker, Median-Hintergrund, Pfad-Fenster, alle Kandidaten, Zeitregel; nur abfrage: dazu jedes
     Abtastbild in der Spanne am zeitlich eingeschobenen Wegpunkt, zwischen erstem und letztem Wegpunkt, je ein
     Abtastschritt Rand (Sammelplan analysen/bauplan_klein.md, Stufen K1 und K2)
  6. sieben: Pose-Wache streng (core.livewache.pose_wache, keine zweite Ladestelle), Zuschnitt aufs Skelett, Groesse des
     Fingerabdrucks, Fingerabdruck
  7. nur cutter: Anker gegen den Fingerabdruck des person.png, Grenze koerper_anker_min; darunter fallen alle Bilder weg
  8. Auswahl zeitlich gleichmaessig, hoechstens n; abfrage setzt n auf die Zahl der Kandidaten (kein Pose-Deckel in
     Schritt 6, keine Auswahl): alle bestandenen Bilder gehen zurueck
Die Bilder gehen als PNG (base64) mit Feldern zurueck; abgelegt werden sie vom Dienst (Service.cutter_starten ueber
core.refquelle.body_add). auftrag, antwort_lesen und schublade_felder sind die Dienst-Seite desselben Protokolls.

LESARTEN (wo der Plan offen ist, die engste):
  1. Mindesthoehe: die Grenze 60 aus bestbilder (Prototyp Zeile 360) als MIN_HOEHE_PX; keine zweite Pruefung danach.
  2. Pose-Pruefungen: in der Reihenfolge der Rechnung (Groesse mal Schaerfe), je Bildnummer nur der beste Kandidat (zwei
     Spurpunkte koennen auf dasselbe Bild fallen), hoechstens POSE_JE_BILD mal n Pruefungen je Video.
  3. Ankerwert eines Bilds: sein Kosinus zum Fingerabdruck des person.png; der Anker gilt, wenn das beste Bild die Grenze
     erreicht. Art abfrage hat keinen Anker (Wert None).
  4. Auswahl: nach Bildzeit geordnet, bei mehr als n Bildern die Plaetze round(j * (L - 1) / (n - 1)); bei n = 1 das
     mittlere Bild.
  5. person_backend: personmodell._person_backend liest <data_dir>/config.json, der Config-Store liegt aber unter
     <data_dir>/config/config.json (verifyd._config_store_pfad); der Wert kaeme dort nie an. Der Dienst gibt ihn deshalb
     im Auftrag mit (der Worker greift nie selbst in die Config), Werk cpu.
  6. Zeitregel: der Abstand zwischen Bildzeit und Spurpunkt ist hoechstens 1 / fps_sample Sekunden; die Spanne gilt fuer
     die Bildzeit auf Frigates Uhr (start_time + i / fps - pre), Grenzen eingeschlossen.

EHRLICHE GRENZEN:
  - Ein zweiter Mensch, dessen Gesicht nie zu sehen war, kann im Bild stehen (Bauplan, „Was zugesagt wird und was nicht").
  - Speicher und Dauer des Schnitts sind fuer diesen Weg nicht gemessen (Bauplan KW3, Last).
  - Die Pose-Wache sieht nur die Hauptperson im Ausschnitt (Kopf prototyp/pose_wache.py).
"""
import base64
import io
import json
import math
import os

import cv2
import numpy as np
from PIL import Image

from core import frames as _frames
from core import frigate_auth as _fauth
from core import harvest_set as _harvest_set
from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

FPS_SAMPLE = 3
MIN_BILDER = 4              # darunter: "clip zu kurz" (unveraendert aus dem Prototyp)
# Dichte-Boden der RAM-Gate-Degradation, gemessen am Vorfalls-Event 10.08. (Herleitung im Kopf von
# prototyp/pfad_snapshots.py, MIN_DICHTE_ANTEIL): 48 % Dichte trug, 17 % nicht; 1/3 liegt in der Luecke.
MIN_DICHTE_ANTEIL = 1 / 3
# Aufschlag der Auswertung auf den Frame-Puffer in Frame-Groessen, aus dem Code von bestbilder abgeleitet (np.stack 12,
# Median-Kopie 12, float64 8, astype 1, Crops < 1 = rund 34; Herleitung im Prototyp, AUSWERTUNG_FRAMES).
AUSWERTUNG_FRAMES = 34
MIN_HOEHE_PX = 60           # Mindesthoehe der Bewegungsbox (Prototyp Zeile 360, Lesart 1)
# Frist eines Videos im Frame-Lauf (aus core/personlauf.py, Bauplan KW3 Punkt 3); der Dienst gibt dem Auftrag 60 s dazu.
EVENT_ZEITWACHE_S = 120
POSE_JE_BILD = 3            # technische Grenze: hoechstens 3 x n Pose-Pruefungen je Video (kein Schwellwert)
ARTEN = ("cutter", "abfrage")
NAME = "koerper"            # Name des Abnehmers im Frame-Lauf

# Die Gruende eines Ausfalls, je ein englischer Kurztext (Stand des Laufs, Ausfaelle nach Grund, Log).
GRUND_ART = "unknown job kind"
GRUND_PERSONBILD = "no person image of the recognised face"
GRUND_FRIGATE = "Frigate event not readable"
GRUND_SPUR = "no path data or box"
GRUND_UHR = "no snapshot time or start time"
GRUND_ENDE = "no end time"
GRUND_BUDGET = "memory budget too small"
GRUND_CLIP = "clip not in the cache"
GRUND_ZEITWACHE = "frame run deadline passed"
GRUND_LAUF = "frame run failed"
GRUND_KURZ = "clip too short"
GRUND_UHRANKER = "clock anchor not found"
GRUND_KEINE_BOX = "no box at the path"
GRUND_POSE = "pose model missing"
GRUND_UNVOLLSTAENDIG = "no complete person"
GRUND_ANKER = "anchor below koerper_anker_min"
# Gruende der Dienst-Seite (Service.cutter_starten)
GRUND_CLIP_HOLEN = "clip not fetched"
GRUND_KEINE_ANTWORT = "no answer from the body process"
GRUND_JOB = "body job failed"
GRUND_ABLAGE = "image not stored"

# Zuschnitt auf die Skelett-Box (prototyp/ernte_lauf.py, Raender heuristisch v0, relativ zur Skelett-Hoehe)
ZUSCHNITT_SC = 0.5
ZUSCHNITT_PAD_X = 0.10
ZUSCHNITT_PAD_OBEN = 0.10
ZUSCHNITT_PAD_UNTEN = 0.04
NASE, AUGE_L, AUGE_R = 0, 1, 2          # Halpe-26
SCHULTER_L, SCHULTER_R = 5, 6
BLICK_SEITLICH_REL = 0.08               # |Schulterbreite|/Crop-Hoehe darunter = seitlich (v0.2, ungeeicht)

# Fingerabdruck (core/personmodell.py): Intel OMZ person-reidentification-retail-0277 (Datei 0265), ImageNet-RGB und
# BILINEAR, feste Batchgroesse 1.
FINGERABDRUCK = "omz0277"
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
BACKBONES = {
    "omz0277": {"datei": "person-reidentification-retail-0265.onnx",
                "eingang": "data", "groesse": (128, 256), "dim": 256,
                "batch": 1, "filter": "bilinear", "whitening": (0, 128),
                "env": "SUSLIK_PERSON_REID"},
}
WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALLBACK = {"fallback": False, "backend": None}
_SITZUNGEN = {}              # je Backend EINE Sitzung je Prozessleben (warm wie die Pose-Wache)


class KeinKoerper(Exception):
    """Dieses Ereignis traegt keine Koerper-Auswertung; grund ist einer der GRUND_-Texte, detail sagt mehr."""

    def __init__(self, grund, detail=""):
        super().__init__(f"{grund}: {detail}" if detail else grund)
        self.grund, self.detail = grund, detail


def _frigate_json(basis, pfad):
    with _fauth.oeffnen(basis + pfad, timeout=20) as r:
        return json.loads(r.read())


def snapshot_holen(basis, eid):
    """snapshot-clean.webp als RGB-Array, nur der Uhr-Anker der Kette (nie ein Koerperbild).
    -> numpy uint8 (H, W, 3)"""
    with _fauth.oeffnen(f"{basis}/api/events/{eid}/snapshot-clean.webp", timeout=20) as r:
        return np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"))


def anker_finden(frames, ev, snap_rgb):
    """Clip-Uhr eichen: Frame suchen, dessen Box-Ausschnitt dem snapshot-clean
    am aehnlichsten ist. Rueckgabe: (frame_liste_index, geschaetzte pre_capture, Guete)."""
    box = ev["data"]["box"]
    st, sft = ev["start_time"], ev["data"]["snapshot_frame_time"]
    fps = frames["fps"]
    H, W = frames["bilder"][0][1].shape[:2]
    x, y, w, h = box
    sx0, sy0 = int(x * W), int(y * H)
    sx1, sy1 = int((x + w) * W), int((y + h) * H)
    soll = cv2.resize(cv2.cvtColor(snap_rgb, cv2.COLOR_RGB2GRAY)[sy0:sy1, sx0:sx1] if snap_rgb.shape[:2] == (H, W)
                      else cv2.cvtColor(snap_rgb, cv2.COLOR_RGB2GRAY), (64, 128))
    best, best_i = -2.0, None
    for li, (i, f) in enumerate(frames["bilder"]):
        t_clip = i / fps
        # Kandidaten nur im plausiblen Fenster: Anker liegt bei (sft-st)+pre, pre in 0..20 s
        if not (sft - st) - 1 <= t_clip <= (sft - st) + 21:
            continue
        crop = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[sy0:sy1, sx0:sx1]
        if crop.size == 0:
            continue
        crop = cv2.resize(crop, (64, 128))
        r = cv2.matchTemplate(crop, soll, cv2.TM_CCOEFF_NORMED)[0][0]
        if r > best:
            best, best_i = r, li
    if best_i is None:
        return None, None, None
    i_anker = frames["bilder"][best_i][0]
    pre = i_anker / fps - (sft - st)
    return best_i, pre, best


class Koerper:
    """Die Bestbild-Wahl als Abnehmer am Frame-Lauf (Vertrag core.frames.Abnehmer): bedarf puffer, zeitbezug wanduhr,
    hart False, fps_sample FPS_SAMPLE. RAM-Gate: passt die Sample-Zahl nicht ins Budget, wird gleichmaessig ausgeduennt;
    unter dem Dichte-Boden (MIN_DICHTE_ANTEIL, mindestens MIN_BILDER) faellt das Ereignis laut aus. Ohne Budget kein
    Lauf (seit .202 verboten, konzept_speicher I-1)."""

    def __init__(self, eid, frigate_url, fps_sample=FPS_SAMPLE, ram_budget_mb=None, alle=False):
        self.eid, self.alle = eid, alle
        self.basis = str(frigate_url or "").rstrip("/")
        self.fps_sample = fps_sample
        self.ram_budget_mb = ram_budget_mb
        self.ev = self.snap = self.fps = None
        self.bilder = []
        self.puffer_mb = 0.0
        self.behalte = None
        self._sample_j = 0
        self.gehalten = 0

    def vorbereiten(self):
        """Ereignis und Schnappschuss bei Frigate holen, vor dem ersten Frame (idempotent).
        -> None; KeinKoerper, wenn Spur, Box, Uhr oder Ende fehlen"""
        if self.ev is not None:
            return
        ev = _frigate_json(self.basis, f"/api/events/{self.eid}")
        data = ev.get("data") or {}
        if not (data.get("path_data") or []) or not data.get("box"):
            raise KeinKoerper(GRUND_SPUR)
        # Issue #27 (Frigate 0.17.2): ohne snapshot_frame_time ist die Uhr nicht eichbar; ein start_time-Ersatz
        # verschoebe die Pfad-Uhr unbemerkt — ehrlicher Verzicht statt stiller Naeherung.
        if not data.get("snapshot_frame_time") or not ev.get("start_time"):
            raise KeinKoerper(GRUND_UHR)
        if ev.get("end_time") is None:
            raise KeinKoerper(GRUND_ENDE, "the event has no end yet, so there is no span")
        self.snap = snapshot_holen(self.basis, self.eid)
        self.ev = ev

    def _start(self, info):
        self.vorbereiten()
        self.fps = info.fps
        n = info.soll_samples or 0
        frame_mb = info.breite * info.hoehe * 3 / 1048576.0
        self.puffer_mb = n * frame_mb
        if self.ram_budget_mb is None:
            raise KeinKoerper(GRUND_BUDGET, "no memory budget set (the body process sets it)")
        if not n:
            raise KeinKoerper(GRUND_LAUF, "the frame source names no sample count")
        spitze = self.puffer_mb + AUSWERTUNG_FRAMES * frame_mb
        if spitze > self.ram_budget_mb:
            passt = int(self.ram_budget_mb / frame_mb) - AUSWERTUNG_FRAMES
            boden = max(MIN_BILDER, math.ceil(n * MIN_DICHTE_ANTEIL))
            if passt < boden:
                raise KeinKoerper(GRUND_BUDGET, f"budget {self.ram_budget_mb:.0f} MB carries only {max(passt, 0)} "
                                                f"of {n} samples, below the density floor {boden}")
            self.behalte = {round(j * (n - 1) / (passt - 1)) for j in range(passt)}
            self.puffer_mb = len(self.behalte) * frame_mb
            _log.info(f"body cutter: memory gate {spitze:.0f} MB > budget {self.ram_budget_mb:.0f} MB — "
                      f"thinned to {len(self.behalte)} samples spread over the event")

    def _frame(self, i, f):
        j = self._sample_j
        self._sample_j += 1
        if self.behalte is not None and j not in self.behalte:
            return
        self.bilder.append((i, f))
        self.gehalten += 1

    def abnehmer(self, zeitwache_s=None):
        """Der Abnehmer dieses Ereignisses fuer core.frames.lauf.
        -> core.frames.Abnehmer"""
        return _frames.Abnehmer(
            name=NAME, fps_sample=self.fps_sample, zeitbezug="wanduhr",
            bedarf="puffer", hart=False, wache_politik="nachrechnen",
            zeitwache_s=zeitwache_s, start=self._start, frame=self._frame)

    def auswerten(self):
        """Alle Kandidaten aus den gehaltenen Samples; der Puffer wird immer losgelassen.
        -> wie bestbilder"""
        try:
            return bestbilder(self.bilder, self.fps, self.ev, self.snap, self.fps_sample, alle=self.alle)
        finally:
            self.bilder = []


def bewegungs_box(frame_bgr, hintergrund):
    """Groesste Bewegungsflaeche gegen den Median-Hintergrund (geglaettet, Otsu mit Grenzen, Flaechen-Deckel).
    -> (x, y, w, h) in Pixeln oder None"""
    d = cv2.absdiff(cv2.GaussianBlur(frame_bgr, (5, 5), 0),
                    cv2.GaussianBlur(hintergrund, (5, 5), 0))
    g = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)
    otsu, _ = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, m = cv2.threshold(g, max(14, min(otsu, 40)), 255, cv2.THRESH_BINARY)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    kont, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not kont:
        return None
    c = max(kont, key=cv2.contourArea)
    fl = cv2.contourArea(c)
    if fl < 400 or fl > 0.45 * frame_bgr.shape[0] * frame_bgr.shape[1]:
        return None
    return cv2.boundingRect(c)


def schaerfe(bgr):
    """Laplace-Varianz eines Ausschnitts.
    -> float"""
    return cv2.Laplacian(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()


def _box_am_pfad(f, hintergrund, cx, cy, bw, bh):
    """Die Bewegungsbox im Fenster um einen Spurpunkt mit den Plausibilitaeten des Prototyps (Zeilen 352-375).
    -> (Ausschnitt als Kopie, Boxhoehe) oder None"""
    H, W = f.shape[:2]
    fw, fh = max(int(3 * bw), 220), max(int(3 * bh), 220)
    x0 = max(0, int(cx * W - fw / 2)); y0 = max(0, int(cy * H - fh / 2))
    x1 = min(W, x0 + fw); y1 = min(H, y0 + fh)
    box = bewegungs_box(f[y0:y1, x0:x1], hintergrund[y0:y1, x0:x1])
    if box is None:
        return None
    bx, by, bwx, bhy = box
    if bhy < MIN_HOEHE_PX or bhy < bwx * 0.8:
        return None
    # Box muss AUF dem Pfad-Punkt sitzen und hoch statt breit sein, nicht unter knapp der halben Frigate-Box
    mx, my = x0 + bx + bwx / 2, y0 + by + bhy / 2
    if abs(mx - cx * W) > max(bw, 80) or abs(my - cy * H) > max(bh * 0.9, 120):
        return None
    if bwx > 0.9 * bhy or bhy < 0.45 * bh:
        return None
    r = 0.08
    cx0 = max(0, int(x0 + bx - r * bwx)); cy0 = max(0, int(y0 + by - r * bhy))
    cx1 = min(W, int(x0 + bx + bwx * (1 + r))); cy1 = min(H, int(y0 + by + bhy * (1 + r)))
    return f[cy0:cy1, cx0:cx1].copy(), bhy


def bestbilder(bilder, fps, ev, snap, fps_sample=FPS_SAMPLE, alle=False):
    """Uhr-Anker, Median-Hintergrund, Pfad-Fenster und Zeitregel (KW3 Punkt 2) ueber die gehaltenen Samples; mit alle
    dazu jedes Abtastbild ohne Kandidaten in der Spanne am zeitlich eingeschobenen Wegpunkt, zwischen erstem und letztem
    Wegpunkt, je ein Abtastschritt Rand (Sammelplan, Stufen K1 und K2).
    -> (Kandidaten oder None, Grund oder None, Detail); Kandidat = (Wert, Bildnummer, Ausschnitt, Hoehe, Bildzeit),
       alle, nach Wert absteigend"""
    if len(bilder) < MIN_BILDER:
        return None, GRUND_KURZ, f"{len(bilder)} samples"
    frames = {"bilder": bilder, "fps": fps}
    _, pre, guete = anker_finden(frames, ev, snap)
    if pre is None:
        return None, GRUND_UHRANKER, ""
    st, ende = ev["start_time"], ev["end_time"]
    pd = (ev.get("data") or {}).get("path_data") or []
    H, W = bilder[0][1].shape[:2]
    stapel = np.stack([f for _, f in bilder[:: max(1, len(bilder) // 12)]][:12])
    hintergrund = np.median(stapel, axis=0).astype(np.uint8)
    bw, bh = ev["data"]["box"][2] * W, ev["data"]["box"][3] * H
    schritt_s = 1.0 / fps_sample
    kandidaten = []
    for (cx, cy), ts in pd:
        t_clip = (ts - st) + pre
        ziel_i = int(round(t_clip * fps))
        li = min(range(len(bilder)), key=lambda k: abs(bilder[k][0] - ziel_i))
        i, f = bilder[li]
        bildzeit = st + i / fps - pre
        # Zeitregel: hoechstens ein Abtastschritt vom Spurpunkt und innerhalb der Spanne des Ereignisses
        if abs(i / fps - t_clip) > schritt_s or not st <= bildzeit <= ende:
            continue
        treffer = _box_am_pfad(f, hintergrund, cx, cy, bw, bh)
        if treffer is None:
            continue
        crop, bhy = treffer
        kandidaten.append((bhy * np.log1p(schaerfe(crop)), i, crop, bhy, bildzeit))
    # die Stelle zeitlich eingeschoben, nur zwischen erstem und letztem Wegpunkt, je ein Abtastschritt Rand
    if alle:
        reihe, belegt = sorted(pd, key=lambda p: p[1]), {k[1] for k in kandidaten}
        zeiten, xs, ys = [p[1] for p in reihe], [p[0][0] for p in reihe], [p[0][1] for p in reihe]
        for i, f in bilder:
            bildzeit = st + i / fps - pre
            if (i in belegt or not st <= bildzeit <= ende
                    or not zeiten[0] - schritt_s <= bildzeit <= zeiten[-1] + schritt_s):
                continue
            treffer = _box_am_pfad(f, hintergrund, float(np.interp(bildzeit, zeiten, xs)),
                                   float(np.interp(bildzeit, zeiten, ys)), bw, bh)
            if treffer is not None:
                kandidaten.append((treffer[1] * np.log1p(schaerfe(treffer[0])), i, treffer[0], treffer[1], bildzeit))
    if not kandidaten:
        return None, GRUND_KEINE_BOX, f"anchor quality {guete:.2f}"
    kandidaten.sort(key=lambda t: -t[0])
    return kandidaten, None, f"anchor quality {guete:.2f}, pre={pre:.1f}s, {len(kandidaten)} candidates"


def rahmen_lesen(koerper, clip, zeitwache_s=EVENT_ZEITWACHE_S):
    """EIN Frame-Lauf mit Zeitwache ueber core.frames.lauf; reisst die Wache oder faellt der Abnehmer aus, wird das
    Teilmaterial verworfen und nicht ausgewertet. -> wie bestbilder"""
    w = _frames.lauf(clip, [koerper.abnehmer(zeitwache_s)])[NAME]
    if w.budget_gerissen or w.lauf_wache_gerissen:
        koerper.bilder = []
        return None, GRUND_ZEITWACHE, f"deadline {zeitwache_s}s, {w.samples} samples seen"
    if w.abgeworfen:
        koerper.bilder = []
        grund = GRUND_LAUF
        for g in (GRUND_SPUR, GRUND_UHR, GRUND_ENDE, GRUND_BUDGET):
            if g in str(w.ausfall):
                grund = g
        return None, grund, str(w.ausfall)[:200]
    return koerper.auswerten()


def person_zuschnitt(bild, punkte, scores):
    """Ausschnitt auf die Skelett-Box mit Rand (Kinderwagen-Befund 04.08.: die Bewegungsbox nimmt mit, was sich mitbewegt).
    -> (Ausschnitt, Anteil der Skelett-Box, Box); ohne verlaessliche Box das Bild unveraendert und (None, None)"""
    H, W = bild.shape[:2]
    pts = [(float(x), float(y)) for (x, y), s in zip(punkte, scores)
           if float(s) >= ZUSCHNITT_SC]
    if len(pts) < 6:
        return bild, None, None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1 = max(0.0, min(xs)), min(float(W), max(xs))
    y0, y1 = max(0.0, min(ys)), min(float(H), max(ys))
    hs = y1 - y0
    if hs < 40 or x1 - x0 < 10:
        return bild, None, None
    cx0 = max(0, int(x0 - ZUSCHNITT_PAD_X * hs))
    cx1 = min(W, int(x1 + ZUSCHNITT_PAD_X * hs))
    cy0 = max(0, int(y0 - ZUSCHNITT_PAD_OBEN * hs))
    cy1 = min(H, int(y1 + ZUSCHNITT_PAD_UNTEN * hs))
    anteil = round(((x1 - x0) * hs) / (W * H), 3)
    return bild[cy0:cy1, cx0:cx1], anteil, [cx0, cy0, cx1, cy1]


def blick_bestimmen(det, crop_hoehe, schwelle):
    """Ansicht aus den Pose-Punkten (Heuristik v0.2, ungeeicht): seitlich bei schmaler Schulterlinie, sonst vorn oder
    hinten ueber die Reihenfolge der Schultern; unklar, wenn eine Schulter unter der Schwelle der Wache liegt.
    -> (vorn | hinten | seitlich | unklar, Messwerte)"""
    sc, pts = det["scores"], det["punkte"]
    gesicht = max(sc[NASE], sc[AUGE_L], sc[AUGE_R])
    lr = (pts[SCHULTER_L][0] - pts[SCHULTER_R][0]) / max(1, crop_hoehe)
    schulter_rel = abs(lr)
    if min(sc[SCHULTER_L], sc[SCHULTER_R]) < schwelle:
        richtung = "unklar"
    elif schulter_rel < BLICK_SEITLICH_REL:
        richtung = "seitlich"
    elif lr > 0:
        richtung = "vorn"
    else:
        richtung = "hinten"
    return richtung, {"gesicht": round(float(gesicht), 2),
                      "schulter_rel": round(float(schulter_rel), 3),
                      "lr": round(float(lr), 3)}


def _person_backend(wert):
    """Rechen-Placement des Fingerabdrucks: der Wert von person_backend aus dem Auftrag (Lesart 5), Werk cpu. GPU/NPU
    ist kein Automatismus: am 11.08. toetete ein zusaetzlicher OpenVINO-Kontext auf der iGPU die Live-Waechter."""
    return str(wert) if wert else "cpu"


def _providers(backend):
    """onnxruntime-Provider-Liste zum Backend-Schalter — VOLLE kind-Menge
    der Registry (cpu / openvino / cuda / migraphx, Deckungs-Vertrag SK1):
    "cpu" | "openvino:GPU" | "openvino:NPU" | "cuda" | "migraphx". Jeder
    Wert setzt das passende Image voraus (openvino nur in gpu/gpu-legacy,
    cuda nur im cuda-Image, migraphx nur in rocm); CPU haengt immer als
    Fallback dran, session_bauen faellt LAUT zurueck."""
    if isinstance(backend, str) and backend.startswith("openvino:"):
        return [("OpenVINOExecutionProvider",
                 {"device_type": backend.split(":", 1)[1]}),
                "CPUExecutionProvider"]
    if backend == "cuda":
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if backend == "migraphx":
        return ["MIGraphXExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


def _bindung_pruefen(sess, backend):
    """Nach dem Bau: bindet die Sitzung den eingestellten Provider? Sonst rechnet onnxruntime still auf der CPU — eine
    ERROR-Zeile je Sitzung und das Merkmal FALLBACK, kein Neuaufbau. -> dieselbe Sitzung"""
    gewollt = _providers(backend)[0]
    name = gewollt[0] if isinstance(gewollt, tuple) else gewollt
    gefallen = name != "CPUExecutionProvider" and name not in sess.get_providers()
    FALLBACK.update(fallback=gefallen, backend=backend)
    if gefallen:
        _log.error(f"person_backend {backend} not bound — computing on CPU")
    return sess


def _modell_pfad(backbone):
    bb = BACKBONES[backbone]
    for k in (os.environ.get(bb["env"]) or "",
              "/app/modelle/" + bb["datei"],
              os.path.join(WURZEL, "modelle", bb["datei"])):
        if k and os.path.exists(k):
            return k
    raise RuntimeError(f"backbone ONNX missing: {bb['datei']} (modelle/)")


def session_bauen(backbone, wert=None):
    """Die ORT-Sitzung des Fingerabdrucks; scheitert das eingestellte Backend, faellt sie LAUT auf CPU zurueck.
    -> onnxruntime.InferenceSession"""
    import onnxruntime as ort
    from face_audit import _ort_thread_opts
    backend = _person_backend(wert)
    try:
        return _bindung_pruefen(ort.InferenceSession(_modell_pfad(backbone),
                                                     providers=_providers(backend),
                                                     sess_options=_ort_thread_opts()),
                                backend)
    except Exception:
        if backend == "cpu":
            raise
        _log.error(f"person_backend={backend} not available — LOUD fallback to CPU")
        FALLBACK.update(fallback=True, backend=backend)
        return ort.InferenceSession(_modell_pfad(backbone),
                                    providers=["CPUExecutionProvider"],
                                    sess_options=_ort_thread_opts())


def bild_vorbereiten(bgr):
    """Einen Ausschnitt auf die Eingangsgroesse des Fingerabdrucks bringen (RGB, BILINEAR).
    -> (PNG-Bytes, RGB-Array in Eingangsgroesse)"""
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).resize(
        BACKBONES[FINGERABDRUCK]["groesse"], Image.BILINEAR)
    puffer = io.BytesIO()
    im.save(puffer, format="PNG")
    return puffer.getvalue(), np.asarray(im)


def abdruck_rechnen(sess, rgb):
    """Der L2-normierte Fingerabdruck eines RGB-Bilds in Eingangsgroesse.
    -> numpy float32 (dim,)"""
    bb = BACKBONES[FINGERABDRUCK]
    x = ((rgb.astype(np.float32) / 255.0 - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    e = sess.run(None, {bb["eingang"]: x})[0][0].astype(np.float32)
    return e / max(float(np.linalg.norm(e)), 1e-12)


def sieben(kandidaten, wache, n, abdruck):
    """Je Bildnummer der beste Kandidat, hoechstens POSE_JE_BILD * n Pose-Pruefungen (streng: vollstaendige Person),
    Zuschnitt aufs Skelett, Eingangsgroesse, Fingerabdruck (Lesart 2). -> (Bilder als dict, Zaehler)"""
    je_bild = {}
    for k in kandidaten:
        je_bild.setdefault(k[1], k)
    deckel = POSE_JE_BILD * int(n)
    z = {"kandidaten": len(kandidaten), "bildnummern": len(je_bild), "pose_geprueft": 0, "pose_ok": 0}
    bilder = []
    for _wert, i, crop, _hoehe, zeit in je_bild.values():
        if z["pose_geprueft"] >= deckel:
            break
        z["pose_geprueft"] += 1
        komplett, det = wache.pruefen(crop)
        if not komplett:
            continue
        z["pose_ok"] += 1
        zuschnitt, _anteil, _box = person_zuschnitt(crop, det["punkte"], det["scores"])
        ansicht, _mess = blick_bestimmen(det, crop.shape[0], wache.schwelle)
        png, rgb = bild_vorbereiten(zuschnitt)
        bilder.append({"bildnummer": int(i), "zeit": float(zeit), "ansicht": ansicht, "png": png,
                       "fingerabdruck": abdruck(rgb), "anker": None})
    return bilder, z


def auswahl(bilder, n):
    """Hoechstens n Bilder, zeitlich gleichmaessig ueber die verbliebenen verteilt (Lesart 4).
    -> Liste, nach Bildzeit geordnet"""
    reihe = sorted(bilder, key=lambda b: b["zeit"])
    n = int(n)
    if len(reihe) <= n:
        return reihe
    if n == 1:
        return [reihe[len(reihe) // 2]]
    return [reihe[j] for j in sorted({round(k * (len(reihe) - 1) / (n - 1)) for k in range(n)})]


def abschliessen(bilder, art, fp_person, anker_min, n):
    """Anker (nur cutter, Lesart 3) und Auswahl: erreicht kein Bild anker_min zum person.png, fallen alle weg.
    -> (Grund oder None, Detail, ausgewaehlte Bilder)"""
    if art == "cutter":
        ref = np.asarray(fp_person, dtype=np.float32)
        for b in bilder:
            b["anker"] = round(float(np.dot(np.asarray(b["fingerabdruck"], dtype=np.float32), ref)), 4)
        bester = max((b["anker"] for b in bilder), default=None)
        if bester is None or bester < float(anker_min):
            return GRUND_ANKER, f"best {bester} < {anker_min}", []
    return None, "", auswahl(bilder, n)


def person_bild(data_dir, eid, person):
    """Das person.png des Bestbild-Satzes dieser Person in diesem Ereignis (kandidaten.jsonl, Lese-Stufe d).
    -> (PNG-Bytes oder None, Detail)"""
    from core import refquelle as _rq
    zeile = _harvest_set.event_rows(os.path.join(data_dir, "events", str(eid).replace("/", "_")))[1].get(person)
    if not (zeile or {}).get("ref_id"):
        return None, "no best-face set of the person in this event"
    r = _rq.read_image({"data_dir": data_dir}, zeile["ref_id"], "person")
    if r is None:
        return None, "best-face set not visible"
    if r.get("daten") is None:
        return None, f"set without person image ({r.get('fehlt') or r.get('fehler') or 'missing'})"
    return r["daten"], ""


def _pose():
    """Die Pose-Wache des Prozesses ueber core.livewache (keine zweite Ladestelle). -> Wache oder None"""
    from core import livewache as _lw
    if not _lw.pose_verfuegbar():
        return None
    return _lw.pose_wache()


def _sitzung(wert):
    backend = _person_backend(wert)
    if backend not in _SITZUNGEN:
        _SITZUNGEN[backend] = session_bauen(FINGERABDRUCK, backend)
    return _SITZUNGEN[backend]


def _ausfall(grund, detail="", zaehler=None):
    return {"grund": grund, "detail": str(detail)[:200], "zaehler": zaehler or {}, "bilder": []}


def _ausgabe(b):
    return {"bildnummer": b["bildnummer"], "zeit": b["zeit"], "ansicht": b["ansicht"], "anker": b["anker"],
            "fingerabdruck": [float(x) for x in b["fingerabdruck"]],
            "png_b64": base64.b64encode(b["png"]).decode("ascii")}


def schnitt_job(job, ram_budget_mb):
    """Einen Auftrag koerperschnitt im Koerper-Prozess ausfuehren (Ablauf im Kopf dieser Datei).
    -> dict grund (None, wenn Bilder kommen), detail, zaehler, bilder"""
    art, eid, dd = job.get("art"), job.get("eid"), job.get("data_dir")
    if art not in ARTEN:
        return _ausfall(GRUND_ART, f"art {art!r}")
    roh = None
    if art == "cutter":
        roh, detail = person_bild(dd, eid, job.get("person"))
        if roh is None:
            return _ausfall(GRUND_PERSONBILD, detail)
    k = Koerper(eid, job.get("frigate_url"), ram_budget_mb=ram_budget_mb, alle=art == "abfrage")
    try:
        k.vorbereiten()
    except KeinKoerper as e:
        return _ausfall(e.grund, e.detail)
    except Exception as e:                                   # noqa: BLE001  Netz, Antwort, Bild: der Grund geht mit
        return _ausfall(GRUND_FRIGATE, f"{type(e).__name__}: {e}")
    try:
        clip = _frames.clip_holen(eid, data_dir=dd, cache_only=True)
    except _frames.ClipCacheMissing as e:
        return _ausfall(GRUND_CLIP, e)
    try:
        kandidaten, grund, detail = rahmen_lesen(k, clip)
    finally:
        _frames.frei(eid, dd)
    if kandidaten is None:
        return _ausfall(grund, detail)
    wache = _pose()
    if wache is None:
        _log.warning("body cutter: the pose model is missing — no body image can be cut")
        return _ausfall(GRUND_POSE)
    sess = _sitzung(job.get("person_backend"))
    n = len(kandidaten) if art == "abfrage" else job["n"]     # abfrage: kein Pose-Deckel, keine Auswahl (Stufe K1)
    bilder, zaehler = sieben(kandidaten, wache, n, lambda rgb: abdruck_rechnen(sess, rgb))
    if not bilder:
        return _ausfall(GRUND_UNVOLLSTAENDIG, detail, zaehler)
    fp_person = None
    if art == "cutter":
        fp_person = abdruck_rechnen(sess, np.asarray(Image.open(io.BytesIO(roh)).convert("RGB").resize(
            BACKBONES[FINGERABDRUCK]["groesse"], Image.BILINEAR)))
    grund, detail2, gewaehlt = abschliessen(bilder, art, fp_person, job.get("anker_min"), n)
    zaehler["anker_bester"] = max((b["anker"] for b in bilder if b["anker"] is not None), default=None)
    if grund:
        return _ausfall(grund, detail2, zaehler)
    return {"grund": None, "detail": detail, "zaehler": zaehler, "bilder": [_ausgabe(b) for b in gewaehlt]}


# ------------------------------------------------------------------ Dienst-Seite desselben Protokolls
def auftrag(cfg, eid, person, art):
    """Der Auftrag koerperschnitt fuer den Koerper-Prozess, Werte aus der Config des Dienstes.
    -> dict (Felder des Protokolls in worker.py)"""
    dd = cfg["data_dir"]
    ordner = os.path.join(dd, "events", str(eid).replace("/", "_"))
    os.makedirs(ordner, exist_ok=True)
    return {"typ": "koerperschnitt", "art": art, "eid": eid, "person": person, "data_dir": dd,
            "frigate_url": cfg.get("frigate_url") or "", "n": int(cfg["koerper_bilder_je_video"]),
            "anker_min": float(cfg["koerper_anker_min"]), "person_backend": cfg.get("person_backend") or "cpu",
            "log": os.path.join(ordner, "koerperschnitt.log")}


def antwort_lesen(antwort):
    """Die Antwort des Koerper-Prozesses auf einen Auftrag koerperschnitt lesen.
    -> (Grund oder None, Detail, Bilder mit PNG-Bytes unter png)"""
    if antwort is None:
        return GRUND_KEINE_ANTWORT, "deadline passed or the process died", []
    if not antwort.get("ok") or not isinstance(antwort.get("schnitt"), dict):
        return GRUND_JOB, str(antwort.get("fehler") or "no result")[:200], []
    s = antwort["schnitt"]
    bilder = [dict(b, png=base64.b64decode(b["png_b64"])) for b in s.get("bilder") or []]
    return s.get("grund"), str(s.get("detail") or ""), bilder


def schublade_felder(person, eid, bild, zustand):
    """Die Felder eines geschnittenen Bilds fuer core.refquelle.body_add.
    -> dict"""
    return {"person": person, "ereignis": eid, "zeit": bild["zeit"], "bildnummer": bild["bildnummer"],
            "ansicht": bild["ansicht"], "anker": bild["anker"], "fingerabdruck": bild["fingerabdruck"],
            "zustand": zustand}
