"""core/frames — Zug 1 + 2 + 4 + 5 des Frame-Verteilers (konzept_frames.md v2).

TEIL A (Z1/Z2, §3.1) — EINE Clip-Beschaffung fuer alle Abnehmer:
cache_pfad() loest das Ablage-Verzeichnis in fester Rangfolge,
clip_holen() laedt atomar (.part) und setzt den PIN im selben Zug (kein
ungeschuetztes Fenster zwischen Download und Abnehmer-Start —
Widerleger-MUSS 4), pin()/frei() fuehren einen REFCOUNT je Halter
(<eid>.<pid>.<tid>.pin): zwei unabhaengige Halter (Worker-Analyse +
Dienst-Thread) koennen sich nie gegenseitig die Datei unter dem Size-Cap
wegraeumen lassen. gepinnt() ist die Auskunft fuer cleanup_cache.

TEIL B (Z4, §3.2) — DER VERTEILER: lauf(vid, abnehmer) faehrt EINEN
FrameIter und bedient jeden registrierten Abnehmer nach dessen
deklariertem Vertrag (Abnehmer, sechs Pflichtfelder). Bei EINEM Abnehmer
ist die Frame-Index-Menge dieselbe wie beim frueheren Einzellauf —
Neutralitaet per Konstruktion, nicht per Messung: der Verteiler baut den
Iterator mit dem fps_sample DES Abnehmers und waehlt selbst nie aus.

Z5 (§4/Z5) macht den ZWEITEN Abnehmer moeglich — den Koerper-Strang, der
seine Samples HAELT (bedarf='puffer') und seine Zeitachse gegen den
Frigate-Snapshot eicht (zeitbezug='wanduhr'). Damit faellt der
Doppel-Decode. Dazu drei Dinge, die Z4 offen liess: die Lauf-Wache
(Zeitwache Stufe b, killt die ffmpeg-Pipe), die Puffer-Wache (ein
haltender Abnehmer darf nie einen wiederverwendeten Puffer bekommen) und
LaufInfo.soll_samples (Vorab-Groesse fuer das RAM-Gate des Halters).

Dieses Modul liefert Dateien und Frames, nie Urteile."""
import os
import shutil
import tempfile
import threading
import time
import urllib.request


def cache_dir(data_dir=None):
    """Rangfolge (v2 §3.1, Widerleger-MUSS 5 — SCRATCH_DIR ist im
    DIENST-Prozess nicht gesetzt): explizites data_dir -> VERIFY_DATA_DIR
    -> SCRATCH_DIR (Worker-Umfeld) -> tempdir-Fallback.

    Der Ordnername ist <data_dir>/clips und NICHT frei waehlbar (v2 §3.1
    woertlich): genau dorthin zeigt SCRATCH_DIR der Kinder
    (verifyd.py:571/:621/:2629), dort liest make_browser_copy den Clip
    (verifyd.py:3768) und nur diesen Ordner raeumen cleanup_cache/
    clip_cache_bytes (:3823/:3838). Ein zweiter Ordner waere ein Cache,
    den niemand raeumt und aus dem niemand sonst liest."""
    for d in (os.path.join(data_dir, "clips") if data_dir else None,
              os.environ.get("VERIFY_DATA_DIR") and os.path.join(
                  os.environ["VERIFY_DATA_DIR"], "clips"),
              os.environ.get("SCRATCH_DIR")):
        if d:
            os.makedirs(d, exist_ok=True)
            return d
    d = os.path.join(tempfile.gettempdir(), "suslik-scratch")
    os.makedirs(d, exist_ok=True)
    return d


def cache_pfad(eid, data_dir=None):
    return os.path.join(cache_dir(data_dir),
                        str(eid).replace("/", "_") + ".mp4")


def _pin_pfad(pfad):
    return f"{pfad}.{os.getpid()}.{threading.get_native_id()}.pin"


def pin(eid, data_dir=None):
    """Refcount-Marke DIESES Halters setzen (idempotent je Halter)."""
    p = _pin_pfad(cache_pfad(eid, data_dir))
    open(p, "a").close()
    return p


def frei(eid, data_dir=None):
    """Marke DIESES Halters loesen; fremde Marken bleiben unberuehrt."""
    try:
        os.remove(_pin_pfad(cache_pfad(eid, data_dir)))
    except FileNotFoundError:
        pass


PIN_ABGESTANDEN_S = 1800     # v2 §3.1: aelter = Waise (aufgegebener Thread/
#                              Prozess) — zaehlt nicht mehr und wird geraeumt


def gepinnt(pfad):
    """Auskunft fuer cleanup_cache: haelt IRGENDWER diese Clip-Datei?
    (Glob ueber <pfad>.*.pin.) Abgestandene Pins (> PIN_ABGESTANDEN_S)
    zaehlen nicht und werden im selben Zug geraeumt — eine Waise darf
    den Size-Cap nie dauerhaft blocken (Widerleger-Rest aus Z2)."""
    import glob
    import time
    lebt = False
    for p in glob.glob(f"{pfad}.*.pin"):
        try:
            if time.time() - os.path.getmtime(p) > PIN_ABGESTANDEN_S:
                os.remove(p)
            else:
                lebt = True
        except OSError:
            lebt = True          # im Zweifel schuetzen, nie wegraeumen
    return lebt


def clip_holen(eid, data_dir=None, frigate_url=None, timeout=30):
    """Clip beschaffen: Cache-Treffer ODER atomarer Download (.part wie
    analyze.py — ein abgerissener Download darf nie als halbes Video
    durchgehen). Der PIN dieses Halters wird IM SELBEN ZUG gesetzt
    (Download UND Cache-Treffer). Rueckgabe: Pfad. Aufrufer ruft frei().
    Fehler raeumen .part-Waisen und den eigenen Pin.
    .262 Hebel 1 (gemessen am 300er-Lauf 17.08.: DREI Events liefen je in
    den prozessweiten 120-s-Socket-Default und frassen 6 der ersten 15 min;
    gesunde LAN-Downloads liefern in <1 s erste Bytes, gemessen 0.4-0.6 s
    je Clip): timeout wirkt je Socket-Operation — ein STALL (timeout s ohne
    Bytes) bricht ab, ein langsamer, aber FLIESSENDER Download nie. Der
    .part-Name traegt PID+TID (endet auf .part — cleanup_cache raeumt
    Waisen weiter): zwei parallele Beschaffer desselben Clips (Vorlader +
    Worker, Hebel 2) schrieben sonst in DIESELBE Teil-Datei."""
    pfad = cache_pfad(eid, data_dir)
    pin(eid, data_dir)
    teil = f"{pfad}.{os.getpid()}.{threading.get_native_id()}.part"
    try:
        if not os.path.exists(pfad):
            basis = (frigate_url
                     or os.environ.get("FRIGATE_URL", "")).rstrip("/")
            with urllib.request.urlopen(f"{basis}/api/events/{eid}/clip.mp4",
                                        timeout=timeout) as r, \
                 open(teil, "wb") as f:
                shutil.copyfileobj(r, f)
            os.replace(teil, pfad)
        return pfad
    except Exception:
        try:
            os.unlink(teil)
        except FileNotFoundError:
            pass
        frei(eid, data_dir)
        raise


# ======================================================= B: Verteiler ======
# Zug 4 (konzept_frames.md v2 §3.2 "Verteiler", §4/Z4, §9-Entscheide 2/3/6,
# §10-Leitplanke). Der Verteiler aendert nur, WOHER Frames kommen — nie, WIE
# gerechnet wird: er waehlt keine Frames aus (das tut die Frame-Quelle mit dem
# fps_sample des Abnehmers), er urteilt nicht, er setzt keine Modell-Parameter.
#
# Der Vertrag hat zwei Tabellen, und das ist Absicht: VERTRAG = was ein
# Abnehmer deklarieren DARF, GEBAUT = was der Verteiler heute wirklich kann.
# Ein Abnehmer, der etwas Deklariertes-aber-noch-nicht-Gebautes verlangt, wird
# LAUT abgewiesen statt still halb bedient (stiller Verlust ist die
# Fehlerklasse, die qs.md fuehrt).

ZEITBEZUG = ("clip", "wanduhr")
BEDARF = ("stream", "puffer")
WACHE_POLITIK = ("nachrechnen",)
# Z5: 'wanduhr' und 'puffer' sind jetzt GEBAUT (vorher laut abgewiesen).
# Die Abweisung bleibt als Mechanismus stehen — sie ist die Zusage, dass ein
# kuenftiger Vertragswert nie still halb bedient wird (qs.md: stiller Verlust).
GEBAUT = {"zeitbezug": ("clip", "wanduhr"), "bedarf": ("stream", "puffer"),
          "wache_politik": ("nachrechnen",)}
_NOCH_NICHT = {}

# §3.2 fps_sample: gemeinsam gedekodiert wird NUR bei step-Gleichheit
# (§9-Entscheid 3 "Rueckfall"). Zaehler + letzter Grund, damit der Rueckfall
# spaeter in /health ausweisbar ist, ohne dass hier ein Dienst-Zustand wohnt.
RUECKFAELLE = {"n": 0, "zuletzt": None}

# Testschalter (Z6-Vorgriff): None = decode.FrameIter. Die S2-Einheitstests
# patchen heute decode.FrameIter (tools/qs.sh) — ueber diese eine Stelle
# greift ein solcher Patch auch dann noch, wenn ein Abnehmer seine Frames
# nur noch ueber den Verteiler bezieht.
FRAME_QUELLE = None


def _frame_quelle():
    """DIE Frame-Quelle des Verteilers — lazy aufgeloest.

    Lazy, weil core.frames auch im DIENST-Prozess importiert wird
    (cleanup_cache, verifyd.py:3858) und `decode` cv2+numpy mitbraechte;
    injizierbar ueber FRAME_QUELLE (s.o.)."""
    if FRAME_QUELLE is not None:
        return FRAME_QUELLE
    from decode import FrameIter
    return FrameIter


def _formel(klasse, name):
    """Die drei Wache-Formeln werden NICHT nachgebaut, sondern von der
    Frame-Quelle uebernommen (decode.FrameIter._soll_samples / verlust_pct /
    unvollstaendig sind properties). EINE Quelle, keine driftende
    Zweitformel — dieselbe Regel wie bei den Aufzaehlungen (qs_ebenen.md).
    Fehlt eine Formel, ist das ein Befund und kein Sonderfall."""
    p = getattr(klasse, name, None)
    if not isinstance(p, property):
        raise TypeError(
            f"Frame-Quelle {klasse.__name__} traegt die Wache-Formel "
            f"'{name}' nicht. Der Verteiler rechnet die Wache je Abnehmer "
            f"nach (§3.2 wache_politik) und uebernimmt die Formel dafuer von "
            f"der Quelle — eine zweite, eigene Formel ist nicht vorgesehen.")
    return p.fget


class LaufInfo:
    """Was ein Abnehmer VOR dem ersten Frame wissen muss (Clip-Metadaten).

    Bewusst nur Metadaten: was der Abnehmer daraus macht (det_size, Zeitachse,
    Fenstergroessen), bleibt beim Abnehmer — der Verteiler kennt keine
    Modell-Parameter und keine Reihenfolge-Regeln der Erkennung."""

    def __init__(self, vid, it):
        self.vid = vid
        self.fps = it.fps
        self.breite, self.hoehe = it.breite, it.hoehe
        self.step = getattr(it, "step", 1)
        self.soll = getattr(it, "soll", None)
        # Z5: erwartete Sample-ZAHL, bevor das erste Frame faellt. Ein
        # haltender Abnehmer (bedarf='puffer') kann daraus VOR dem Puffern
        # rechnen, wie gross der Puffer wuerde, und absagen statt den Prozess
        # in den OOM zu fahren (§5 'RAM'). Die Formel wird NICHT nachgebaut,
        # sondern von der Frame-Quelle uebernommen (s. _formel) — dieselbe
        # Regel wie bei der Wache. None = die Quelle kennt kein Soll.
        try:
            self.soll_samples = _formel(type(it), "_soll_samples")(it)
        except TypeError:
            self.soll_samples = None


class Abnehmer:
    """Der EINE Andock-Punkt (§3.2 + §7): wer Frames braucht, deklariert
    seinen Bedarf und bekommt sie geliefert — nie ein eigener Decode.

    Alle SECHS Vertragsfelder sind Pflicht, keins hat einen Default: ein
    weggelassenes Feld waere wieder eine Annahme IM VERTEILER statt einer
    Aussage des Abnehmers, und genau das soll der Vertrag beenden.

      fps_sample     Sampling-Wunsch. Gemeinsam gedekodiert wird nur, wenn
                     ALLE Abnehmer denselben step ergeben (§9-Entscheid 3);
                     sonst faehrt jeder seinen eigenen Lauf (ein Download
                     bleibt). Grund: die Wache haengt am step des LAUFS
                     (decode.py:240-247) — ein gemeinsamer, anderer step
                     verschoebe still `frames_fehlen`.
      zeitbezug      'clip' (t = i/fps) | 'wanduhr' (der Abnehmer eicht
                     seine Zeitachse selbst gegen snapshot-clean). Der
                     Verteiler rechnet KEINEN Anker — er kennt Frigate
                     nicht und urteilt nie; seine Zusage an einen
                     wanduhr-Abnehmer ist der ORIGINAL-Index i und die
                     unveraenderte fps in LaufInfo, aus denen der Abnehmer
                     eicht. Weil der Anker je Event genau EINMAL faellt
                     (§3.2), laesst der Verteiler nur EINEN wanduhr-
                     Abnehmer je Lauf zu — ein zweiter braeuchte einen
                     geteilten Anker und wird laut abgewiesen.
      bedarf         'stream' (haelt nichts) | 'puffer' (haelt alle
                     Samples). Bei einem Puffer-Abnehmer sichert der
                     Verteiler zu, dass zwei aufeinander folgende Frames
                     nie DENSELBEN Speicher benutzen (Puffer-Wache in
                     _fahren) — eine recycelnde Frame-Quelle wuerde einem
                     Halter sonst still alle Bilder gleich machen.
                     RAM ist SEINE Sache: LaufInfo.soll_samples + breite/
                     hoehe sagen ihm in start() vorab, wie gross sein
                     Puffer wuerde (§5 'RAM', 4K: 23,7 MiB je Sample).
      hart           True: ein Ausfall beendet den ganzen Lauf (die
                     Ausnahme geht unveraendert an den Aufrufer).
                     False: der Ausfall wird in der Wache vermerkt, der
                     Abnehmer abgeworfen, die uebrigen laufen zu Ende.
      wache_politik  'nachrechnen': der Verteiler rechnet Verlust und
                     Vollstaendigkeit aus der EIGENEN Sample-Zahl dieses
                     Abnehmers nach (ein abgeworfener hat weniger gesehen
                     als der Lauf) und reicht decoder_fehler/hwdec/
                     hwdec_fallback unveraendert durch. Er urteilt nie.
      zeitwache_s    Zeitbudget DIESES Abnehmers ueber alle Callbacks
                     zusammen. None = kein eigenes Budget; dann gilt
                     weiter der Deckel des Aufrufers. Ein weicher Abnehmer
                     ueber Budget wird abgeworfen, ein harter laeuft zu
                     Ende (der Riss steht in der Wache).
                     ZWEISTUFIG seit Z5 (§3.2): Stufe (a) ist diese
                     Abnehmer-Wache. Stufe (b) ist die LAUF-Wache — ein
                     Waechter-Thread, der die ffmpeg-Pipe beendet
                     (decode.FrameIter.abbrechen), weil zwischen zwei
                     Frames sonst gar keine Wache greift: ein blockierender
                     Pipe-Read haengt bis zum Job-Deckel des Aufrufers.
                     Sie laeuft NUR, wenn JEDER Abnehmer des Laufs ein
                     Budget nennt, und dann mit dem GROESSTEN davon. Denn
                     die Pipe gehoert allen: haette ein Abnehmer kein
                     Budget (der Gesichts-Pfad hat bewusst keins), wuerde
                     ihm ein fremdes Zeitmass den Clip mitten im Urteil
                     abschneiden. Ohne dieses Feld erbte der Koerper-Strang
                     umgekehrt den 1800-s-Deckel des Jobs (§5).

    frame(i, frame_bgr)   Pflicht-Callback je Sample-Frame.
    start(LaufInfo)       optional, EINMAL vor dem ersten Frame.

    FRAME-EIGENTUM: das gelieferte Bild ist LESEND. Wer ueber den Callback
    hinaus etwas behaelt, KOPIERT — ein numpy-View haelt sonst den ganzen
    dekodierten Frame am Leben (die .copy()-Lehre aus analyze.py:261-265,
    die dort einen OOM-Kill beendet hat)."""

    def __init__(self, name, fps_sample, zeitbezug, bedarf, hart,
                 wache_politik, zeitwache_s, frame, start=None):
        for feld, wert, erlaubt in (("zeitbezug", zeitbezug, ZEITBEZUG),
                                    ("bedarf", bedarf, BEDARF),
                                    ("wache_politik", wache_politik,
                                     WACHE_POLITIK)):
            if wert not in erlaubt:
                raise ValueError(
                    f"Abnehmer '{name}': {feld}={wert!r} steht nicht im "
                    f"Vertrag {erlaubt}")
            if wert not in GEBAUT[feld]:
                raise NotImplementedError(
                    f"Abnehmer '{name}': {feld}={wert!r} ist deklariert, "
                    f"aber im Verteiler NOCH NICHT GEBAUT — "
                    f"{_NOCH_NICHT.get(wert, 'kein Bauzug zugeordnet')}. "
                    f"Lieber laut abweisen als still anders bedienen.")
        if not callable(frame):
            raise TypeError(f"Abnehmer '{name}': frame-Callback fehlt")
        if start is not None and not callable(start):
            raise TypeError(f"Abnehmer '{name}': start ist nicht aufrufbar")
        if float(fps_sample) <= 0:
            raise ValueError(f"Abnehmer '{name}': fps_sample muss > 0 sein")
        self.name = name
        self.fps_sample = fps_sample
        self.zeitbezug = zeitbezug
        self.bedarf = bedarf
        self.hart = bool(hart)
        self.wache_politik = wache_politik
        self.zeitwache_s = zeitwache_s
        self.frame = frame
        self.start = start


class Wache:
    """Wache-Werte JE ABNEHMER (§3.2 'wache_politik').

    Traegt bewusst dieselben Namen wie decode.FrameIter (gelesen/soll/
    samples/verlust_pct/unvollstaendig/decoder_fehler/hwdec/hwdec_fallback):
    ein Abnehmer, der frueher direkt am FrameIter haing, liest danach
    unveraendert weiter. `samples`/`gelesen` sind die des ABNEHMERS (ein
    abgeworfener hat weniger gesehen als der Lauf), die drei Stream-
    Eigenschaften kommen unveraendert vom Lauf."""

    def __init__(self, name, it):
        self.name = name
        self._quelle = type(it)
        self.fps = it.fps
        self.breite, self.hoehe = it.breite, it.hoehe
        self.step = getattr(it, "step", 1)
        self.soll = getattr(it, "soll", None)
        self.samples = 0
        self.gelesen = 0
        self.decoder_fehler = 0
        self.hwdec = False
        self.hwdec_fallback = False
        self.cb_s = 0.0            # in den Callbacks verbrachte Zeit
        self.abgeworfen = False    # weicher Abnehmer: Ausfall/Budget
        self.budget_gerissen = False
        self.ausfall = None        # repr der Ausnahme bzw. Budget-Grund
        self.lauf_wache_gerissen = False   # Z5: Stufe (b) hat die Pipe beendet

    def _durchreichen(self, it):
        """decoder_fehler/hwdec/hwdec_fallback sind Eigenschaften des
        STREAMS, nicht des Abnehmers — unveraendert durchgereicht (§3.2)."""
        self.decoder_fehler = getattr(it, "decoder_fehler", 0)
        self.hwdec = getattr(it, "hwdec", False)
        self.hwdec_fallback = getattr(it, "hwdec_fallback", False)

    # Formeln der Frame-Quelle, nicht nachgebaut (s. _formel).
    @property
    def _soll_samples(self):
        return _formel(self._quelle, "_soll_samples")(self)

    @property
    def verlust_pct(self):
        return _formel(self._quelle, "verlust_pct")(self)

    @property
    def unvollstaendig(self):
        return _formel(self._quelle, "unvollstaendig")(self)


def lauf(vid, abnehmer, log=print):
    """EIN Decode fuer alle registrierten Abnehmer. Rueckgabe: {name: Wache}.

    NEUTRALITAET PER KONSTRUKTION: bei EINEM Abnehmer entsteht genau EIN
    Iterator mit dessen fps_sample — dieselbe Frame-Index-Menge wie beim
    frueheren Einzellauf. Der Verteiler filtert nie selbst."""
    if not abnehmer:
        raise ValueError("lauf() ohne Abnehmer — es gibt nichts zu liefern")
    namen = [a.name for a in abnehmer]
    if len(set(namen)) != len(namen):
        raise ValueError(f"Abnehmer-Namen nicht eindeutig: {namen}")
    uhren = [a.name for a in abnehmer if a.zeitbezug == "wanduhr"]
    if len(uhren) > 1:
        raise NotImplementedError(
            f"zwei wanduhr-Abnehmer in einem Lauf ({uhren}): der Anker faellt "
            f"je Event genau EINMAL (§3.2 zeitbezug). Einen geteilten Anker "
            f"gibt es noch nicht — lieber laut abweisen als zweimal eichen.")
    Q = _frame_quelle()
    # Je Abnehmer EIN Iterator (nur ffprobe, KEIN Decode): so kommt jeder
    # step aus der einen Formel der Frame-Quelle (decode.py:140) statt aus
    # einer zweiten Rechnung hier. Bei step-Gleichheit faehrt der erste und
    # die uebrigen werden verworfen (bei einem Abnehmer: kein Zusatzaufwand).
    iters = [Q(vid, a.fps_sample) for a in abnehmer]
    steps = {getattr(it, "step", 1) for it in iters}
    if len(steps) == 1:
        return _fahren(vid, abnehmer, iters[0])
    RUECKFAELLE["n"] += 1
    RUECKFAELLE["zuletzt"] = {
        "vid": os.path.basename(str(vid)),
        "steps": {a.name: getattr(it, "step", 1)
                  for a, it in zip(abnehmer, iters)}}
    log("WARN: frame distributor falls back to separate decodes — consumers "
        f"ask for different steps {RUECKFAELLE['zuletzt']['steps']}. One "
        "download stays, but a shared step would silently move the "
        "completeness watch (it is computed against the step of the run, "
        "decode.py:240-247) and with it frames_fehlen.")
    ergebnis = {}
    for a, it in zip(abnehmer, iters):
        ergebnis.update(_fahren(vid, [a], it))
    return ergebnis


def _zeiger(frame):
    """Speicher-Adresse eines Frames (fuer die Puffer-Wache). None = das
    Objekt sagt nichts darueber (fremde Test-Quelle) -> keine Aussage."""
    try:
        return frame.__array_interface__["data"][0]
    except Exception:                                # noqa: BLE001
        return None


def _fahren(vid, abnehmer, it):
    """EIN Iterator, Bedienung in Registrierungs-Reihenfolge, harte zuerst."""
    reihenfolge = ([a for a in abnehmer if a.hart]
                   + [a for a in abnehmer if not a.hart])
    wachen = {a.name: Wache(a.name, it) for a in abnehmer}
    aktiv = []
    for a in reihenfolge:
        if a.start is None:
            aktiv.append(a)
            continue
        try:
            a.start(LaufInfo(vid, it))
        except Exception as ex:                      # noqa: BLE001
            if a.hart:
                raise
            w = wachen[a.name]
            w.ausfall, w.abgeworfen = repr(ex), True
            continue
        aktiv.append(a)
    if not aktiv:
        # Alle weichen Abnehmer haben schon in start() abgesagt (z.B. der
        # Koerper-Abnehmer am RAM-Gate). Dann gar nicht erst dekodieren:
        # ffmpeg zu starten, um beim ersten Frame abzubrechen, waere genau
        # die verschwendete Arbeit, die dieser Zug einsparen soll.
        for w in wachen.values():
            w._durchreichen(it)
        return wachen
    # Zeitwache Stufe (b), die LAUF-Wache (§3.2): nur wenn JEDER Abnehmer ein
    # Budget nennt — die Pipe gehoert allen, und ein Abnehmer ohne eigenes
    # Zeitmass (der Gesichts-Pfad) darf nie durch das eines anderen
    # abgeschnitten werden. Dann gilt das GROESSTE Budget.
    budgets = [a.zeitwache_s for a in abnehmer]
    lauf_budget = (max(budgets) if budgets and None not in budgets else None)
    fertig, waechter = threading.Event(), None
    if lauf_budget is not None and hasattr(it, "abbrechen"):
        def _lauf_wache():
            if fertig.wait(lauf_budget):
                return                     # Lauf war rechtzeitig durch
            if it.abbrechen():             # ffmpeg beenden -> read() bekommt EOF
                for w in wachen.values():
                    w.lauf_wache_gerissen = True
        waechter = threading.Thread(target=_lauf_wache, daemon=True,
                                    name="frames-laufwache")
        waechter.start()
    # Puffer-Wache (§3.2 bedarf): haelt ein Abnehmer die Frames, darf die
    # Quelle keinen Speicher wiederverwenden. Geprueft wird gegen das
    # VORHERIGE Frame, das dafuer eine Runde lang festgehalten wird — nur so
    # ist Adressgleichheit beweisend (freigegebener Speicher darf dieselbe
    # Adresse wiederbekommen, festgehaltener nicht).
    haelt = any(a.bedarf == "puffer" for a in abnehmer)
    letztes, vor_zeiger = [None], None      # [0] haelt das vorherige Frame fest
    gen = iter(it)
    try:
        for i, frame in gen:
            if not aktiv:
                break            # niemand mehr da, den der Decode bedient
            if haelt:
                z = _zeiger(frame)
                if z is not None and z == vor_zeiger:
                    raise RuntimeError(
                        "Frame-Quelle liefert wiederverwendeten Speicher, ein "
                        "Abnehmer haelt aber die Samples (bedarf='puffer'): "
                        "alle gehaltenen Bilder waeren dasselbe. Die Quelle "
                        "muss je Sample ein eigenes Bild liefern.")
                letztes[0], vor_zeiger = frame, z
            for a in list(aktiv):
                w = wachen[a.name]
                t0 = time.monotonic()
                try:
                    a.frame(i, frame)
                except Exception as ex:              # noqa: BLE001
                    if a.hart:
                        raise                        # Ausfall beendet den Lauf
                    w.ausfall, w.abgeworfen = repr(ex), True
                    aktiv.remove(a)
                    continue
                finally:
                    w.cb_s += time.monotonic() - t0
                w.samples += 1
                w.gelesen = i + 1
                if a.zeitwache_s is not None and w.cb_s > a.zeitwache_s:
                    w.budget_gerissen = True
                    if not a.hart:
                        w.ausfall = (f"Zeitwache {a.zeitwache_s}s gerissen "
                                     f"({w.cb_s:.1f}s in {w.samples} Frames)")
                        w.abgeworfen = True
                        aktiv.remove(a)
    finally:
        fertig.set()                 # Lauf-Wache abbestellen (Z5, Stufe b)
        if waechter is not None:
            waechter.join(timeout=5)
        letztes[0] = None            # letzte Puffer-Wache-Referenz loslassen
        # Deterministisch schliessen: das finally IN der Frame-Quelle
        # (ffmpeg-Pipe zu, rc lesen, stderr auswerten) muss auch dann laufen,
        # wenn wir vorzeitig aussteigen — sonst faehrt die Wache ohne
        # decoder_fehler heim. decode.FrameIter.__iter__ ist ein Generator und
        # hat close(); eine einfache Testquelle liefert evtl. nur einen
        # gewoehnlichen Iterator — dort gibt es nichts zu schliessen.
        if hasattr(gen, "close"):
            gen.close()
        for w in wachen.values():
            w._durchreichen(it)
    return wachen
