"""Die Tuer: nach einem guten Gesicht eines noch nicht erkannten Namens jedes Bild pruefen (K3 aus L16).

HERKUNFT: Bauplan analysen/bauplan_k3_produkt.md, Stufe KP2. Die Regel kommt aus dem Werkzeug des Labors
L16 (backups/release3_bau/labor_k3_norm/werkzeug/l5_regel.py:152-257, `TuerQuelle`, `_sprung`, `_ss`); der
Massstab fuer „richtig uebernommen" ist der Anker samples/labor_archiv/versionen/k3_l16_anker_2026-10-03/
(Rohdaten je Bild: Bildnummer, Herkunft, Erkennungswert). Ablauf je Bild wie im Labor: erst das Urteil
(der Stapel, core.stapel), dann die Tuer, dann das Ende.

FRUEHES ENDE (Stufe KP3, l5_regel.py:236-244): Hat der Stapel so viele verschiedene Namen erkannt wie die
Personenzahl des Ereignisses (core.personenzahl, Frigate oder Metadaten der Einspielung) und ist die Tuer
zu, endet das Ereignis an diesem Bild (Grund ALLE_ERKANNT); sonst laeuft es bis zum Clip-Ende. Die
Personenzahl geht wie im Labor auch als Obergrenze in den Stapel. Ohne gueltige Zahl gibt es weder
Obergrenze noch fruehes Ende, die Tuer bleibt. Ein Fehler der eigenen Logik schaltet das fruehe Ende fuer
das Ereignis ab (l5_regel.py:172-174), eine ERROR-Zeile, das Ereignis rechnet zu Ende. Was der Worker
daraus meldet (geplantes Ende fuer die Wache, Zaehler der INFO-Zeile), liefert `bilanz`.

ZWECK: Die Engine liefert ein Ereignis in der Grundrate (jedes `schritt`-te Bild, decode.sample_schritt).
Zeigt ein Gesicht mit Erkennungswert ab TUER_SCHWELLE auf einen Namen, den der Stapel nach diesem Bild
noch nicht erkannt hat, geht die Tuer auf: die laufende Decoder-Kette wird beendet und am naechsten Bild
mit Schritt 1 neu angesetzt, bis zum Bild + `tuer_fenster`; ein neuer Ausloeser im Fenster verlaengert
es. Danach geht es auf dem Raster der Grundrate weiter, gezaehlt ab Clip-Anfang. Neu angesetzt wird ueber
dieselbe Engine-Kette (`engine.frames(..., sprung=...)`), also derselbe Pixelweg und derselbe Rueckfall.

SPRUNGSTELLEN OHNE VORLAUF (Bauplan KP2 Punkt 2): Das Labor baute die Zeitstempel-Karte vorab per
ffprobe ueber alle DEKODIERTEN Bilder (prep.py). Hier kommt sie aus der Paketliste des Containers, ohne
zu dekodieren, und erst dann, wenn die Tuer im Ereignis zum ersten Mal aufgeht: Ereignisse ohne Ausloeser
bezahlen nichts. Die Zeiten der Pakete, nach Zeit geordnet, sind die Bilder in Ausgabe-Reihenfolge, also
die Folge, die das select der Kette mit n zaehlt. Belegt ist das nur durch die kleine Probe aus Punkt 2
(backups/release3_bau/kp2/belege/), an der Software-Kette und an drei Clips.

EHRLICHE GRENZEN:
  - Ein Paket, das der Decoder nicht als Bild ausgibt, verschiebt die Zaehlung hinter ihm. Die Probe an
    einem Clip mit Transport-Stoerung im HEVC-Strom deckt einen solchen Fall ab, nicht jeden.
  - Faellt die Karte aus (ffprobe scheitert, ein Paket ohne Zeit), bleibt die Tuer fuer dieses Ereignis
    zu: eine ERROR-Zeile, das Ereignis rechnet auf dem Raster zu Ende wie ohne Tuer (seit KP3 auch ohne
    fruehes Ende, es ist ein Fehler der eigenen Logik).
  - Das fruehe Ende sieht nur die bis dahin geprueften Bilder: was danach im Clip noch kaeme (ein
    Doppelgaenger-Hoechstwert, gute Bilder fuer den Vorrat), fehlt dem Ereignis (Tuer-Konzept Abschnitt 7).
  - Wird eine Kette mitten im Fenster neu angesetzt, startet ffmpeg neu (gemessen im Labor L3: 0,61 bis
    1,91 s Wartezeit je Neustart); das kostet Zeit, keine Bilder.
  - Der Tuer-Deckel zaehlt die Bilder der Tuer-Kette, auch die, die zugleich auf dem Raster liegen. Ist
    er erreicht, schliesst die Tuer fuer den Rest des Ereignisses.
"""
import collections
import json
import subprocess

from core import logbuch as _logbuch
from core import stapel as _stapel

_log = _logbuch.logger(__name__)

# Die Tuer-Schwelle: ab diesem Erkennungswert oeffnet ein Gesicht die Tuer fuer einen noch nicht
# erkannten Namen. Gemessen im Labor L16 (Anker: schwelle 0,375 in allen Laeufen); ein Profilwert,
# bewusst unabhaengig von `win_thresh` und `win_min` (Bauplan K3, Entscheid 6).
TUER_SCHWELLE = 0.375
# Zwei Bilder, deren Zeiten naeher als diese Spanne liegen, trennt ein Sprung per -ss nicht; dann setzt
# die Kette am ersten trennbaren Bild davor an und zaehlt die fehlenden Bilder per select ab
# (l5_regel.py:36, Vorgabe des Labors, und `_sprung` :187-193).
SPRUNG_MIN_S = 0.0001
# Die Herkunft eines Bildes: aus der Kette der Grundrate oder aus der Kette der offenen Tuer (Werte wie in
# den Rohdaten des Ankers).
GRUNDRATE, TUER = "grundrate", "tuer"
# Der Grund, aus dem ein Ereignis endet (Werte wie `ende_grund` in den Rohdaten des Labors L16): alle
# gemeldeten Personen erkannt und die Tuer zu, oder das Ende des Clips.
ALLE_ERKANNT, CLIP_ENDE = "alle_erkannt", "clip_ende"

# Ein Ansatzpunkt der Kette: `ab` ist die Original-Bildnummer des ersten gelieferten Bildes, `ss` die
# Sprungzeit vor dem Eingang (None = ab Dateianfang), `off` die Zahl der Bilder, die select nach dem
# Sprung noch abzaehlt.
Sprung = collections.namedtuple("Sprung", "ab ss off")


def eingang(sprung):
    """Die Eingangs-Optionen der ffmpeg-Kette fuer einen Ansatzpunkt, vor `-i` zu setzen.
    -> Liste (leer am Clip-Anfang)"""
    if sprung is None or sprung.ss is None:
        return []
    return ["-ss", "%.6f" % sprung.ss]


def auswahl(schritt, sprung=None):
    """Der select-Ausdruck der Kette: jedes `schritt`-te Bild, nach einem Sprung erst ab dem `off`-ten.
    -> Text fuer -vf (ohne Komma am Ende)"""
    off = sprung.off if sprung is not None else 0
    if off:
        return "select='gte(n\\,%d)*not(mod(n-%d\\,%d))'" % (off, off, schritt)
    return f"select='not(mod(n\\,{schritt}))'"


def start(sprung):
    """Die Original-Bildnummer, ab der eine Kette zaehlt.
    -> int"""
    return 0 if sprung is None else int(sprung.ab)


def sprungkarte(clip):
    """Die Zeit jedes Bildes relativ zum Dateistart, aus der Paketliste (ohne Dekodieren), in
    Ausgabe-Reihenfolge. -> Liste der Sekunden (Index = Original-Bildnummer); ValueError bei Paketen
    ohne Zeit"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "packet=pts_time:format=start_time", "-of", "json", clip],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60, check=True)
    d = json.loads(r.stdout or "{}")
    pakete = d.get("packets") or []
    zeiten = [p.get("pts_time") for p in pakete]
    if not zeiten or any(z in (None, "N/A") for z in zeiten):
        raise ValueError(f"packet list without timestamps ({len(zeiten)} packets)")
    st = float((d.get("format") or {}).get("start_time") or 0)
    # ffmpeg rechnet ein Eingangs-ss relativ zum Dateistart (l5_regel/prep.py), deshalb minus start_time
    return sorted(float(z) - st for z in zeiten)


def sprung_berechnen(karte, ab):
    """Der Ansatzpunkt fuer Bild `ab`: Sprung in die Mitte vor dem ersten zeitlich trennbaren Bild, der
    Rest per select (l5_regel.py:187-193). -> Sprung"""
    if ab == 0:
        return Sprung(0, None, 0)
    j = ab
    while j > 0 and karte[j] - karte[j - 1] <= SPRUNG_MIN_S:
        j -= 1
    return Sprung(ab, None if j == 0 else (karte[j - 1] + karte[j]) / 2.0, ab - j)


def bilanz(quelle=None):
    """Was der Worker vom Ende eines Ereignisses meldet (KP3): Grund, geplantes Ende (letztes Bild bei einem
    fruehen Ende, sonst None), Tuer-Oeffnungen, Zusatz-Bilder ausserhalb des Rasters, Logik-Fehler; ohne
    Tuer-Quelle (Fenster 0) das Clip-Ende ohne Tuer. -> dict"""
    q = quelle
    return {"grund": q.ende if q else CLIP_ENDE,
            "geplant": q.letztes if q and q.ende == ALLE_ERKANNT else None,
            "oeffnungen": q.oeffnungen if q else 0, "zusatz": q.zusatz if q else 0,
            "logik_fehler": bool(q and q.logik_fehler)}


class TuerQuelle:
    """Die Bild-Quelle eines Ereignisses mit Tuer (l5_regel.TuerQuelle ohne Zeitnahme).

    `strom(schritt, sprung)` liefert die Bilder einer Engine-Kette als (i, y, uv) mit Original-Bildnummer
    i; `sprung` None heisst Clip-Anfang. Der Kern ruft nach jedem Bild mit Gesichtern `melden`; danach
    entscheidet die Quelle, ob die Kette weiterlaeuft, die Tuer aufgeht, es zurueck aufs Raster geht oder
    das Ereignis frueh endet. `personenzahl` ist eine gueltige Zahl oder None, geprueft vom Aufrufer
    (core.personenzahl.gueltig); None heisst: kein fruehes Ende, keine Obergrenze im Stapel.
    """

    def __init__(self, strom, clip, schritt, lat, personenzahl=None):
        self.strom, self.clip, self.S = strom, clip, int(schritt)
        self.fenster = int(lat["tuer_fenster"])
        self.deckel = int(lat.get("tuer_deckel") or 0)             # 0 = ohne Deckel (Haus-Konvention)
        self.lat, self.x = lat, int(lat.get("stapel_stimmen") or 0)
        self.karte, self.zu = None, False                            # zu: Deckel erreicht oder Karte fehlt
        self.tuer_bis, self.erkannt, self.meldung = -1, set(), None
        self.herkunft, self.tuer_bilder = GRUNDRATE, 0
        self.gen, self.art, self._fehler_gemeldet = None, None, False
        # KP3: Personenzahl, Grund und Bild des Endes, Zaehler der INFO-Zeile, Fehler der eigenen Logik
        self.pz, self.ende, self.letztes = personenzahl, CLIP_ENDE, None
        self.oeffnungen, self.zusatz, self.logik_fehler = 0, 0, False

    def melden(self, i, faces, zeilen):
        """Nach einem Bild mit Gesichtern: erst das Urteil (Stapel ueber alle Zeilen bis hier), dann die
        Ausloeser dieses Bildes. -> None (das Ergebnis wartet in `meldung` auf den naechsten Schritt)"""
        try:
            self.erkannt = (set(_stapel.entscheiden(zeilen, self.lat, self.x, self.pz)["namen"])
                            if self.x > 0 else set())
        except Exception as e:                                       # noqa: BLE001
            # Fehler der eigenen Logik: die Tuer arbeitet mit den bisher erkannten Namen weiter, das
            # fruehe Ende ist fuer dieses Ereignis aus (l5_regel.py:172-174); laut, einmal je Ereignis
            # (Tuer-Konzept Abschnitt 5).
            self._logik_aus(f"door logic: verdict failed ({type(e).__name__}: {e}) — "
                            f"keeping the names recognised so far")
        ausl = []
        for f in faces:
            d = f["sc"]
            if not d:
                continue
            p, w = max(d.items(), key=lambda x: x[1])
            if w >= TUER_SCHWELLE and p not in self.erkannt:
                ausl.append(p)
        self.meldung = (int(i), ausl)

    def _fehler(self, text):
        if not self._fehler_gemeldet:
            self._fehler_gemeldet = True
            _log.error(f"{text} ({self.clip})")

    def _logik_aus(self, text):
        """Fehler der eigenen Logik: das fruehe Ende ist fuer dieses Ereignis aus, eine ERROR-Zeile
        (l5_regel.py:172-174). -> None"""
        if self.pz is not None:
            self.logik_fehler = True
            text += " — early end off for this event, it is computed to the end of the clip"
        self.pz = None
        self._fehler(text)

    def _alle_erkannt(self, i):
        """Das fruehe Ende nach Bild i (l5_regel.py:241-244): Personenzahl erreicht und Tuer zu. Ein
        Fehler hier schaltet das fruehe Ende ab (l5_regel.py:172-174). -> bool"""
        try:
            return self.pz is not None and len(self.erkannt) >= self.pz and self.tuer_bis <= i
        except Exception as e:                                       # noqa: BLE001
            self._logik_aus(f"door logic: early-end check failed ({type(e).__name__}: {e})")
            return False

    def _starten(self, art, ab, schritt):
        sprung = None if ab == 0 else sprung_berechnen(self.karte, ab)
        self.gen = self.strom(schritt, sprung)
        self.art = art
        self.oeffnungen += art == TUER

    def _karte_da(self):
        """Die Sprungkarte, beim ersten Gebrauch gebaut. -> bool (False: Tuer bleibt zu, laut)"""
        if self.karte is None and not self.zu:
            try:
                self.karte = sprungkarte(self.clip)
            except Exception as e:                                   # noqa: BLE001
                self.zu = True
                self._logik_aus(f"door logic: no jump map ({type(e).__name__}: {str(e)[:200]}) — "
                             f"door stays shut, the event is judged on the base rate")
        return self.karte is not None

    def __iter__(self):
        """Die Bilder des Ereignisses, Grundrate und Tuer, in aufsteigender Bildnummer.
        -> Iterator (i, y, uv)"""
        self._starten(GRUNDRATE, 0, self.S)
        try:
            while True:
                try:
                    i, y, uv = next(self.gen)
                except StopIteration:
                    return
                self.herkunft = TUER if self.art == TUER else GRUNDRATE
                self.tuer_bilder += self.art == TUER
                self.zusatz += i % self.S != 0                       # nur Bilder zwischen den Raster-Punkten
                self.letztes = i
                self.meldung = None
                yield i, y, uv
                if self._weiter(i) is False:
                    return
        finally:
            self.gen.close()                 # bricht der Verbraucher ab, endet auch die laufende Kette

    def _weiter(self, i):
        """Nach Bild i: Fenster verlaengern, Deckel pruefen, fruehes Ende, Kette wechseln
        (l5_regel.py:236-257). -> False am Ende des Clips oder beim fruehen Ende, sonst None"""
        m = self.meldung if (self.meldung and self.meldung[0] == i) else None
        if m and m[1] and not self.zu:
            self.tuer_bis = max(self.tuer_bis, i + self.fenster)
        if self.art == TUER and self.deckel > 0 and self.tuer_bilder >= self.deckel:
            self.zu = True                                           # Deckel: Tuer schliesst jetzt
            self.tuer_bis = i
            _log.debug(f"door cap reached: {self.tuer_bilder} door frames ({self.clip})")
        if self._alle_erkannt(i):                                    # KP3: erst Urteil, dann Tuer, dann Ende
            self.ende = ALLE_ERKANNT
            _log.debug(f"early end at frame {i}: {len(self.erkannt)} of {self.pz} persons recognised, "
                       f"door shut ({self.clip})")
            return False
        if self.art != TUER and self.tuer_bis > i:
            if not self._karte_da():
                self.tuer_bis = -1
                return None
            self.gen.close()
            if i + 1 >= len(self.karte):
                return False
            self._starten(TUER, i + 1, 1)
        elif self.art == TUER and i >= self.tuer_bis:
            self.gen.close()
            r = (i // self.S + 1) * self.S
            if r >= len(self.karte):
                return False
            self._starten(GRUNDRATE, r, self.S)
        return None
