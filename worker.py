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
  {"typ":"rechenprobe","zeitbudget_s":60,"backend_geraet_je_task":{...},"log":"..."}
     (Lieferung C: rechnet jedes Modell auf seinem BETRIEBS-Geraet gegen die CPU —
      Antwortfeld "rechenprobe" = eine Zeile je Modell; gedruckt wird beim Dienst)
  {"typ":"ping"}
  Jeder Job (ausser ping) darf zusaetzlich "rss_max_mb" tragen: die Politik-Grenze
  der In-Job-RSS-Wache (= worker_rss_max_mb des Dienstes; s. _JobRssWache und
  _job_rss_grenze — ohne den Wert wacht nur die cgroup-Regel).
Antwort: {"ok":bool,"cpu_s":float,"wall_s":float,"rss_mb":int,"vmhwm_mb":int,
          "rss_spitze_mb":int,("fehler":str)}
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
import threading
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
_werk = {}                       # P1: warme Werkzeuge des personwork-Betriebs (PoseWache)
_normmass = None                 # die eine warme NormMass je Worker-Leben (Vorrat B2)
_strukturmass = None             # die eine warme StrukturMass je Worker-Leben (.32x)


def _normmass_holen():
    """Warme NormMass wie der _emb-Cache: EIN Bau je Worker-Leben, Neubau nur
    bei Modellwechsel. GEBRAUCHT wird sie ausschliesslich vom Ernte-Job, und
    nur von dort wird sie geholt — ueber _normmass_fuer_ernte, das Budget und
    Anmeldung bei der RSS-Wache davorsetzt. Faellt der Bau aus (fremdes
    Modell, Graph-Fehler), traegt die Instanz ok=False und die Ernte laeuft
    DEKLARIERT ohne v weiter."""
    global _normmass
    import face_audit
    modell = face_audit.aktuelles_modell()
    if _normmass is None or _normmass.modell != modell:
        _normmass = face_audit.NormMass(modell=modell)
    return _normmass


# Bauspitze des NormMass-ERSTBAUS, gemessen 24.08.2026 auf der Projektmaschine
# (LXC, Intel Core Ultra 9 285H mit NPU; frischer Prozess, VmHWM aus
# /proc/self/status, Sockel 58 MB nach den Importen):
#   ERSTBAU mit Kompilat-Cache (der Weg im Dienst)   2675-2690 MB, 9-10 s
#   Erstbau ohne Cache (nackter CLI-Lauf)            2025-2251 MB
#   Folgebau aus warmem Cache                        1997 MB, 4,2 s
#   reiner CPU-Weg (SUSLIK_NORM_DEVICE=CPU)          1069 MB
# Die Spitze traegt die Geraete-Session, die CPU-Session der Kreuzprobe und beim
# Erstbau zusaetzlich das zu schreibende Kompilat (2x ~126 MB). Genommen wird
# der groesste gemessene Wert: beide Verbraucher unten (Budget-Untergrenze,
# Wachstums-Zugestaendnis) werden falsch, wenn die Zahl zu klein ist.
_NORMMASS_BAUSPITZE_MB = 2700
_NORMMASS_MARGE_MB = 256          # dieselbe Marge wie der Budget-Boden in _koerper_budget


def _laut(text):
    """Eine Zeile ungepuffert auf fd 2. WAEHREND eines Jobs liegt fd 2 per dup2
    auf der Job-Logdatei (_fd_umleitung) — os.write landet dort sofort, ein
    Kill mitten im Bau laesst die Zeile also stehen. sys.stderr waere derselbe
    fd, aber mit Python-Puffer davor."""
    try:
        os.write(2, (text + "\n").encode())
    except Exception:
        pass


def _normmass_fuer_ernte(wache=None):
    """NormMass fuer EINEN Ernte-Job. None = dieser Lauf faehrt ohne Vorrat.

    Zwei Vorbedingungen haengen am ERSTBAU, nicht am Gebrauch (warm ist er
    gratis, deshalb der fruehe Rueckweg):

    1. BUDGET: die Spitze oben faellt in einem Prozess an, den die cgroup des
       Containers toetet, wenn sie nicht hineinpasst. Ist die Grenze lesbar
       und zu knapp, faellt der Vorrat DIESES Laufs laut aus — nachholbar,
       waehrend ein Kernel-OOM den ganzen Job und den Worker mitnaehme.
    2. RSS-WACHE: Regel 2 der _JobRssWache misst das WACHSTUM dieses Jobs
       gegen die Politik-Grenze (worker_rss_max_mb). Der Bau ist Wachstum,
       das nicht dem Ernte-Job gehoert; ohne Anmeldung riebe er einen
       unschuldigen Job an der Grenze auf. Angemeldet wird nur bei echtem
       Erstbau und nur an DIESER Wache, also fuer diesen einen Job.

    Ein Modellwechsel im laufenden Worker laesst _normmass_holen ebenfalls neu
    bauen (Neubau-Zweig dort); im Ernte-Lauf steht das Modell fest, deshalb
    zaehlt hier der Erstbau."""
    if _normmass is not None:
        return _normmass_holen()
    frei = _cgroup_frei_mb()
    noetig = _NORMMASS_BAUSPITZE_MB + _NORMMASS_MARGE_MB
    if 0 <= frei < noetig:
        _laut(f"worker: learning stock skipped this run — free memory {frei} MB "
              f"< build peak {_NORMMASS_BAUSPITZE_MB} MB + {_NORMMASS_MARGE_MB} MB "
              f"margin (harvest continues without the feature norm)")
        return None
    if wache is not None and wache.grenze:   # 0 = Politik unbekannt: dort wacht nur
        wache.grenze += _NORMMASS_BAUSPITZE_MB   # Regel 3, und die darf nichts erben
    _laut("worker phase: building feature-norm session")
    nm = _normmass_holen()
    if getattr(nm, "ok", False):
        _laut(f"worker phase: feature-norm ready on {nm.device}")
    return nm


# Bauspitze der RECHENPROBE (Lieferung C, analysen/15 §4), gemessen 24.08.2026 auf der
# Projektmaschine (LXC, Intel Core Ultra 9 285H mit iGPU + NPU, Backend openvino:MIXED,
# Norm auf NPU; frischer Prozess je Lauf, VmHWM aus /proc/self/status, voller Lauf ueber
# alle sechs geprueften Modelle des Vertrags):
#   OV-Blob-Cache UND Treiber-Cache leer      2434 MB, 42,7 s
#   OV-Blob-Cache leer, Treiber-Cache warm    2387 MB, 23,6 s
#   beide warm (Lauf 2 / Lauf 3)              1986 / 1985 MB, 16,9 / 13,2 s
# Die Spitze traegt IMMER nur EINE Session (die Probe ist strikt seriell — die
# CPU-Ausgaenge ueberleben als Zahlen, die CPU-Session nicht); den Ausschlag gibt das
# groesste Modell des Vertrags, der 260-MB-adaface-Kopf samt seiner Graph-Variante.
# Genommen wird der groesste gemessene Wert, aufgerundet: eine zu kleine Zahl macht die
# Budget-Pruefung unten wertlos, und genau dieser Fall (unbudgetierte Bauspitze in einem
# Prozess, den die cgroup toetet) ist die Feld-Regression, die Lieferung A behoben hat.
_RECHENPROBE_SPITZE_MB = 2500
_RECHENPROBE_MARGE_MB = 256       # dieselbe Marge wie _NORMMASS_MARGE_MB / _koerper_budget


def _rechenprobe_bauer(quelle, geraet, precision=None):
    """Der ECHTE Session-Bauer der Rechenprobe — die einzige Stelle, an der sie
    Aussenwelt beruehrt (core/rechenprobe.messen kennt kein onnxruntime).

    quelle    Modell-Pfad ODER Graph-Bytes (ort.InferenceSession nimmt beides; die
              Feature-Norm ist eine Graph-Variante desselben adaface-Files).
    geraet    (kind, geraet) — ("cpu", None) fuer die Referenz, sonst das Betriebsgeraet.
    precision OpenVINO-Rechenpraezision ("FP32") oder None = Voreinstellung (fp16).

    KEIN STILLER CPU-RUECKFALL, und das ist der Kern: face_audit._ort_session taugt fuer
    eine Diagnose NICHT — es faellt bei Nichtbindung auf CPU zurueck und liefert trotzdem
    eine Session. Die Probe verglich dann CPU gegen CPU und meldete "maxdiff 0.0 = alles
    gut" (Begruendung wortgleich in tester/gputest_kommandos_tokn59.md §1). Hier wird
    deshalb nach JEDEM Bau geprueft, ob der EP wirklich in get_providers() steht, und
    sonst geworfen — die Messfunktion kann diese Klasse konstruktiv nicht selbst fangen.

    Der Aufbau ist der von face_audit.NormMass._feature_norm_session: Geraeteknoten VOR
    dem Versuch pruefen (sonst nur Treiber-Spam), Kompilat-Cache aus SCRATCH_DIR (ohne
    ihn kompiliert OpenVINO bei JEDEM Bau neu), Pseudo-Geraete (GPU_FP32) aus
    face_audit.NORM_PSEUDO_GERAETE aufloesen statt aus einem zweiten Literal."""
    import glob as _glob
    import face_audit
    import onnxruntime as ort
    kind, dev = (geraet if isinstance(geraet, (tuple, list)) else ("cpu", None))
    dev = str(dev or "").upper()
    if kind == "cpu" or not dev:
        return ort.InferenceSession(quelle, providers=["CPUExecutionProvider"],
                                    sess_options=face_audit._ort_thread_opts())
    from core.registry import ep_von
    soll = ep_von(kind)
    if soll not in ort.get_available_providers():
        raise ValueError(f"{kind}:{dev}: {soll} not available in this image")
    knoten = face_audit.geraete_knoten_muster(dev if kind == "openvino" else
                                              ("NVIDIA" if kind == "cuda" else "KFD"))
    if knoten and not _glob.glob(knoten):
        raise ValueError(f"{kind}:{dev}: no device node ({knoten})")
    if kind == "openvino":
        pseudo = face_audit.NORM_PSEUDO_GERAETE.get(dev)
        opts = {"device_type": pseudo["ov_device"] if pseudo else dev}
        if precision or pseudo:
            opts["precision"] = precision or pseudo["precision"]
        _scratch = (os.environ.get("SCRATCH_DIR") or "").strip()
        if _scratch:
            cache = os.path.join(_scratch, "ov_cache")
            try:
                os.makedirs(cache, exist_ok=True)
                opts["cache_dir"] = cache
            except OSError:      # read-only Volume: dann ohne Cache bauen — der Ausfall
                pass             # des Caches ist kein Grund, das Geraet zu verlieren
        s = ort.InferenceSession(quelle, providers=["OpenVINOExecutionProvider"],
                                 provider_options=[opts],
                                 sess_options=face_audit._ort_thread_opts())
    else:                        # cuda/migraphx: keine Praezisions-Achse (die Option
        try:                     # existiert dort nicht), Geraetenummer wie _ort_session
            _did = int(dev)
        except (TypeError, ValueError):
            _did = 0
        # Provider-Liste wortgleich face_audit._ort_session (Beschleuniger PLUS
        # CPU-Rueckfall): ohne den Rueckfall bricht der Session-Bau, sobald EIN Knoten
        # des Graphen auf dem EP nicht laeuft. Still wird das trotzdem nicht — die
        # Bind-Pruefung unten sieht, ob der Beschleuniger ueberhaupt registriert ist,
        # und genau daran erkennt auch _ort_session den stillen CPU-Rueckfall.
        s = ort.InferenceSession(quelle, providers=[(soll, {"device_id": _did}),
                                                    "CPUExecutionProvider"],
                                 sess_options=face_audit._ort_thread_opts())
    if soll not in s.get_providers():
        raise ValueError(f"{kind}:{dev}: provider did not bind")
    return s


def _rechenprobe_fuer_job(job):
    """Die Rechenprobe EINES Jobs. -> dict fuer die Job-Antwort.

    Budget VOR dem Bauen, exakt das Muster von _normmass_fuer_ernte: die Spitze faellt in
    einem Prozess an, den die cgroup des Containers toetet, wenn sie nicht hineinpasst.
    Reicht sie nicht, wird NICHT gemessen und das laut gesagt — ein Kernel-OOM naehme den
    Boot-Selbstcheck mit."""
    from core import rechenprobe as _rp
    frei = _cgroup_frei_mb()
    noetig = _RECHENPROBE_SPITZE_MB + _RECHENPROBE_MARGE_MB
    if 0 <= frei < noetig:
        grund = (f"compute probe skipped — free memory {frei} MB < probe peak "
                 f"{_RECHENPROBE_SPITZE_MB} MB + {_RECHENPROBE_MARGE_MB} MB margin")
        _laut("worker: " + grund)
        return {"rechenprobe": [], "rechenprobe_grund": grund}
    _laut("worker phase: compute probe")
    from core.registry import MODELL_VERTRAG
    zeilen = _rp.messen(MODELL_VERTRAG, _rechenprobe_bauer,
                        zeitbudget_s=float(job.get("zeitbudget_s") or 60.0),
                        backend_geraet_je_task=job.get("backend_geraet_je_task") or {})
    _laut("worker phase: compute probe done")
    return {"rechenprobe": zeilen}


def _strukturmass_holen():
    """Warme StrukturMass — HIER GILT DAS GEGENTEIL DER NormMass-REGEL.

    Der NormMass-Bau braucht Budget-Pruefung und Anmeldung bei der RSS-Wache,
    weil seine Spitze in GB rechnet (_normmass_fuer_ernte). StrukturMass ist
    umgekehrt: ihr 5-MB-Modell kostet NEBEN einer schon warmen Session gemessen
    0 MB RSS und 0,2 s — in einem NACKTEN Prozess dagegen +464 MB (nicht das
    Modell, sondern das Plugin, das dort erst aufgebaut wuerde). Deshalb LAZY
    beim ersten Ernte-Job, wenn Embedder und NormMass ohnehin stehen. Faellt
    der Bau aus, traegt die Instanz ok=False und die Ernte laeuft DEKLARIERT
    ohne Struktur-Test weiter (z["struktur_aus"])."""
    global _strukturmass
    import face_audit
    if _strukturmass is None:
        _strukturmass = face_audit.StrukturMass()
    return _strukturmass


def _koerper_budget(job):
    """RAM-Budget eines Koerper-Jobs (P1, exakt das analyze.py-Muster):
    Politik = rss_max_mb des Jobs minus eigener VmRSS, Physik = cgroup-Rest
    (falls lesbar; -1 = keine Grenze -> Politik allein, geraten wird nichts).
    Boden 256 MB: ein Budget unter dem Dichte-Boden lehnt Koerper._start
    ohnehin laut ab — aber ein NEGATIVES Budget waere ein Rechenfehler,
    kein Urteil."""
    rss = _rss_mb()
    grenze = float(job.get("rss_max_mb") or 3072)
    budget = (grenze - rss) if rss > 0 else 256.0
    cg = _cgroup_frei_mb()
    if cg >= 0:
        budget = min(budget, float(cg))
    return max(budget, 256.0)


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


def _proc_mb(feld):
    """Ein Feld aus /proc/self/status in MB (-1 = nicht lesbar)."""
    try:
        with open("/proc/self/status") as f:
            for z in f:
                if z.startswith(feld + ":"):
                    return int(z.split()[1]) // 1024
    except Exception:
        pass
    return -1


def _rss_mb():
    """Aktuell belegt (VmRSS) — daran haengt der Neustart-Deckel
    worker_rss_max_mb (verifyd.py:695-698)."""
    return _proc_mb("VmRSS")


def _vmhwm_mb():
    """SPITZE seit Prozessstart (VmHWM). Der Deckel oben greift erst NACH
    einem Job und sieht nur den Stand DANACH — die Spitze INNERHALB des Jobs
    kann er konstruktionsbedingt nie sehen (konzept_frames.md v2 §5 'RAM').
    VmHWM ist der einzige Wert, der sie belegt: er faellt nie."""
    return _proc_mb("VmHWM")


def _cgroup_frei_mb(wurzel="/sys/fs/cgroup"):
    """Freier Speicher bis zur CGROUP-Grenze dieses Containers in MB,
    MemAvailable-artig (Limit minus unverzichtbarem Verbrauch), -1 = keine
    Grenze lesbar/gesetzt. `wurzel` ist nur fuer den Testharnisch.

    Bewusst NIE /proc/meminfo: im Container zeigt das den WIRT (auf der
    Prod-LXC gemessen 10.08.: meminfo sagt 64 GB Wirt, docker info 24 GiB
    LXC-Limit — die dokumentierte Falle aus CLAUDE.md 'Maschine'). Nur die
    eigene cgroup traegt die Wahrheit, die diesen Prozess wirklich toetet.

    MemAvailable-ARTIG, nicht Limit minus current (Nachbesserung F4):
    memory.current enthaelt den REKLAMIERBAREN Seiten-Cache, und der
    besteht in diesem Dienst gerade aus den CLIPS, die die Analyse liest.
    Am Prod-Container gemessen (10.08.): current 5534 MB, davon file
    4395 MB (79 %), inactive_file allein 3201 MB. Ein naives Limit-current
    haette bei einem 6-GiB-Docker-Limit nur 610 MB "frei" gemeldet, das
    min() im Budget (analyze.py koerper_abnehmer) haette 2725 auf 610 MB
    gedrueckt und damit genau den KeinKoerper-Totalausfall erzeugt, den
    der Fix beseitigt — ausgerechnet auf den speicherbegrenzten
    Installationen, fuer die der Deckel gebaut ist. Der Kernel wirft
    inactive_file unter Druck zurueck, BEVOR er toetet; als Verbrauch
    zaehlt deshalb current - inactive_file (memory.stat), MemAvailable-
    artig = 3811 MB im selben Beispiel, das Budget bleibt unberuehrt.
    Prod selbst: memory.max='max' (Docker ohne --memory; das LXC-Limit
    liegt auf einem von hier unsichtbaren Eltern-cgroup) -> ehrlich -1
    statt einer geratenen Zahl. Der v1-Zweig (total_inactive_file) deckt
    Alt-Systeme ab."""
    def _stat(pfad, feld):
        try:
            with open(pfad) as f:
                for z in f:
                    if z.startswith(feld + " "):
                        return int(z.split()[1])
        except Exception:
            pass
        return 0
    try:                                          # cgroup v2 (unified)
        with open(os.path.join(wurzel, "memory.max")) as f:
            mx = f.read().strip()
        if mx.isdigit():
            with open(os.path.join(wurzel, "memory.current")) as f:
                belegt = int(f.read())
            belegt -= _stat(os.path.join(wurzel, "memory.stat"), "inactive_file")
            return max(0, (int(mx) - max(0, belegt)) // 1048576)
    except Exception:
        pass
    try:                                          # cgroup v1 (legacy)
        with open(os.path.join(wurzel, "memory", "memory.limit_in_bytes")) as f:
            mx = int(f.read())
        if mx < 1 << 60:                          # ~2^63 = "unbegrenzt"
            with open(os.path.join(wurzel, "memory", "memory.usage_in_bytes")) as f:
                belegt = int(f.read())
            belegt -= _stat(os.path.join(wurzel, "memory", "memory.stat"),
                            "total_inactive_file")
            return max(0, (mx - max(0, belegt)) // 1048576)
    except Exception:
        pass
    return -1


WACHE_INTERVALL_S = 1.0   # Abtast-Takt der In-Job-RSS-Wache. Reine Mess-Kadenz, kein
#                           Budget: die Abbruch-Regeln skalieren ihre Marge mit dem
#                           Wachstum JE INTERVALL (s. _JobRssWache Regel 3), der Takt
#                           aendert also nur die Telemetrie-Aufloesung, nicht den Schutz.


def _job_rss_grenze(job):
    """Politik-Grenze der In-Job-Wache in MB (0 = unbekannt -> nur Regel 3).
    Rangfolge — DECKUNGS-VERTRAG statt zweiter Zahlenquelle (beide Wege speist
    verifyd aus DERSELBEN Config worker_rss_max_mb):
      1. Job-Feld "rss_max_mb" (Protokoll oben): setzt der Dienst seit .172
         per setdefault in WorkerProzess.job auf jeden Nicht-ping-Job — aus
         derselben Config worker_rss_max_mb wie seine Neustart-Schwelle.
      2. analyze-Jobs: der --koerper-rss-max-mb-Wert aus argv. verifyd
         (run_analyze) setzt ihn aus worker_rss_max_mb, allerdings nur bei
         scharfem Koerperpfad — derselbe Wert auf dem aelteren Transport."""
    try:
        g = job.get("rss_max_mb")
        if g:
            return max(0, int(float(g)))
        argv = job.get("argv") or []
        if job.get("typ") == "analyze" and "--koerper-rss-max-mb" in argv:
            return max(0, int(float(argv[argv.index("--koerper-rss-max-mb") + 1])))
    except Exception:
        pass
    return 0


class _JobRssWache:
    """In-Job-RSS-Wache — Issue #20, Bitte 1 des Melders: "Monitor or enforce
    the worker RSS limit WHILE a job is running" (Nachbesserung 10.08.).

    Der Dienst prueft rss_mb erst NACH dem Job (verifyd WorkerProzess.job):
    die Spitze IM Job sah bis .172 niemand, und ein Ausreisser-Job konnte
    unbegrenzt wachsen (Issue #20: 34-38 GB auf einem 46-GiB-Wirt ohne
    Container-Limit -> Host-OOM, fremde Dienste starben mit). Diese Wache
    laeuft als Thread NEBEN dem Job und tastet VmRSS im WACHE_INTERVALL_S-
    Takt ab. Drei Regeln, KEIN neues Budget — beide Grenzen existieren schon:

    1. LAUT (einmal je Job): VmRSS ueberschreitet die Politik-Grenze
       (worker_rss_max_mb, Transport s. _job_rss_grenze) -> WARN-Zeile ins
       Job-Log (fd 2 liegt waehrend des Jobs per dup2 dort).
    2. ABBRUCH Politik: DIESER Job allein ist um mehr als die Grenze
       gewachsen (rss - rss_start > grenze). Bewusst das Job-WACHSTUM, nicht
       der Absolutwert: im Kriech-Fall (Worker beginnt den Job schon nahe der
       Grenze, Soak-Befund 27.07.) wuerde der Absolutwert einen unschuldigen
       Job killen — den faengt weiter der geordnete Neustart nach dem Job.
       Ein Ausreisser wie #20 endet dagegen bei rss_start+grenze (Default:
       nach ~4 GB Wachstum statt bei 34-38 GB).
    3. ABBRUCH Physik: die cgroup-Grenze des Containers waere im NAECHSTEN
       Intervall erreicht (frei <= eigenes Wachstum des letzten Intervalls;
       frei MemAvailable-artig aus _cgroup_frei_mb, derselben Quelle wie das
       RAM-Gate des Koerperpfads). Extrapolation statt fester Schwelle: die
       Marge skaliert mit der Wachstumsgeschwindigkeit. Die Bedingung haengt
       am EIGENEN Wachstum — frisst ein ANDERER Prozess der cgroup den
       Speicher, bricht sie nicht ab.

    ABBRUCH heisst: ok:false-Antwort auf die Antwort-Pipe (der Dienst
    behandelt das wie jeden Analysefehler — bewusst KEIN Sofort-Retry, ein
    deterministischer Ausreisser soll nicht schleifen; die Nachhol-Runde
    versucht es spaeter auf einem frischen Worker), WARN ins Job-Log, dann
    os._exit: nur ein Prozess-Ende gibt ORT-Arenas wirklich frei
    (Soak-Befund 27.07.), und der naechste Job startet ohnehin frisch.

    EHRLICHE GRENZEN: die Wache sieht nur DIESEN Prozess (ffmpeg-Kinder
    zaehlen nie als Ausloeser), nur im Takt (eine einzelne Allokation
    schneller als ein Intervall faengt erst der Kernel), und sie senkt den
    Speicherbedarf keines Pfades — sie macht den Schaden endlich und laut.
    Der reale 34-38-GB-Traeger von #20 (anker->clustere, n^2 im DIENST-
    Prozess, nicht im Worker) ist hiermit NICHT gedeckelt; eigener Bauschritt."""

    def __init__(self, grenze_mb, antwort_out, intervall_s=WACHE_INTERVALL_S):
        self.grenze = int(grenze_mb or 0)   # 0 = Politik unbekannt -> nur Regel 3
        self.out = antwort_out              # None (--roundtrip): Abbruch ohne Antwort-Zeile
        self.intervall = float(intervall_s)
        self.spitze = -1                    # groesster abgetasteter VmRSS im Job (MB)
        self._stop = threading.Event()
        self._t = None

    def __enter__(self):
        self._t = threading.Thread(target=self._lauf, daemon=True, name="job-rss-wache")
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._t is not None:
            self._t.join(timeout=self.intervall + 2)
        return False

    def _laut(self, text):
        try:
            os.write(2, (text + "\n").encode())   # fd 2 = Job-Log (_fd_umleitung)
        except Exception:
            pass

    def _abbruch(self, grund, rss):
        self._laut(f"WARN: {grund} — aborting this job; the worker exits and "
                   f"the service starts a fresh one for the next job")
        antwort = {"ok": False, "fehler": grund, "rss_mb": rss,
                   "vmhwm_mb": _vmhwm_mb(), "rss_spitze_mb": max(self.spitze, rss)}
        try:
            if self.out is not None:
                self.out.write(json.dumps(antwort, ensure_ascii=False) + "\n")
                self.out.flush()
        except Exception:
            pass
        os._exit(1)

    def _lauf(self):
        rss_start = rss_vor = _rss_mb()
        gemeldet = False
        while not self._stop.wait(self.intervall):
            rss = _rss_mb()
            if rss < 0:
                continue                    # /proc nicht lesbar: Wache kann nur schweigen
            if rss_start < 0:
                rss_start = rss             # erster lesbarer Wert als Job-Basis
            self.spitze = max(self.spitze, rss)
            if self.grenze and not gemeldet and rss > self.grenze:
                gemeldet = True             # Regel 1: LAUT, einmal je Job
                self._laut(f"WARN: worker rss {rss} MB exceeds worker_rss_max_mb "
                           f"{self.grenze} MB while the job is still running "
                           f"(job started at {rss_start} MB; the service only "
                           f"checks after the job)")
            if self.grenze and rss - rss_start > self.grenze:
                self._abbruch(              # Regel 2: Politik
                    f"in-job rss guard: this job alone grew by {rss - rss_start} MB "
                    f"(more than worker_rss_max_mb {self.grenze} MB), rss now "
                    f"{rss} MB", rss)
            frei = _cgroup_frei_mb()
            wachstum = rss - rss_vor if rss_vor >= 0 else 0
            if frei >= 0 and 0 < wachstum >= frei:
                self._abbruch(              # Regel 3: Physik
                    f"in-job rss guard: container memory almost exhausted "
                    f"({frei} MB free, worker grew {wachstum} MB in the last "
                    f"{self.intervall:.0f}s — the kernel OOM killer would strike "
                    f"next), rss {rss} MB", rss)
            rss_vor = rss


def _koerper_zusatz(argv):
    """Z5 zusatz-Rueckweg: was der Koerper-Abnehmer im Analyse-Lauf geliefert
    hat, in die Job-Antwort heben (konzept_frames.md v2 §3.2 'Wo der Lauf
    wohnt'). Der Dienst sieht damit im Log, ob der zweite Abnehmer wirklich
    lieferte, ohne die Uebergabe selbst zu oeffnen. Fehlt sie, ist das kein
    Fehler: dann faehrt der Dienst wie immer seinen eigenen Weg."""
    try:
        d = argv[argv.index("--dir") + 1]
        with open(os.path.join(d, "koerper.json")) as f:
            k = json.load(f)
    except Exception:
        return None
    return {"koerper_crops": len(k.get("top") or []),
            "koerper_puffer_mb": k.get("puffer_mb"),
            "koerper_samples": k.get("samples"),
            **({"koerper_degradiert": str(k.get("degradiert"))[:40]}
               if k.get("degradiert") else {}),
            **({"koerper_ausfall": str(k.get("ausfall"))[:120]}
               if k.get("ausfall") else {})}


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


def _job_ausfuehren(job, antwort_out=None):
    """Einen Job im Prozess ausfuehren; stdout/stderr in die Job-Logdatei.
    SystemExit (z.B. analyze 'Referenz-Master leer') toetet den Worker NICHT.
    antwort_out: Antwort-Pipe fuer den ABBRUCH-Fall der In-Job-RSS-Wache
    (None im --roundtrip: dort endet ein Abbruch als lauter Exit 1)."""
    typ = job.get("typ")
    if typ == "ping":
        return {"ok": True, "rss_mb": _rss_mb()}
    logpfad = job.get("log") or os.devnull
    # .287 Clip-Debug (User-Auftrag 18.08., Frigate-Haenger-Klasse Task #11):
    # der Dienst reicht seinen cfg['debug']-Schalter als Job-Feld 'clip_dbg'
    # durch (WorkerProzess.job, setdefault wie rss_max_mb — EINE Quelle).
    # Armiert wird JE Job: die [clipdbg]-Zeilen der Clip-Beschaffung
    # (core.frames.clip_holen) landen via print im Log DIESES Jobs
    # (analyze.log/ernte.log, fd-Umleitung unten); Quelle + Event-Alter
    # kommen als Job-Felder mit. Ein Job at a time -> Modul-Zustand ist safe.
    from core import frames as _clipdbg_fr
    _clipdbg_fr.CLIP_DBG = ((lambda z: print(z, flush=True))
                            if job.get("clip_dbg") else None)
    _clipdbg_fr.CLIP_QUELLE = job.get("clip_quelle")
    _clipdbg_fr.CLIP_ALTER_MIN = job.get("clip_alter_min")
    # .290 (Task #11): Erzeugungs-Modus-Defaults je Job armieren — der
    # Analyze-Weg (runpy analyze.py) ruft clip_holen ohne eigene Parameter;
    # ohne diese Armierung zoege ein Nachhol-Lauf auf einem ALTEN Event den
    # Clip mit hartem 30-s-Abbruch und fuetterte genau den Serie-E-Leak.
    # VERHALTEN, nicht Telemetrie; explizite clip_holen-Argumente (Ernte-
    # Branch unten) gewinnen.
    _clipdbg_fr.CLIP_ERZEUGUNG = bool(job.get("clip_erzeugung"))
    _clipdbg_fr.CLIP_ERZEUGUNG_DECKEL_S = job.get("clip_erzeugung_deckel_s")
    # .292: VOD-Weg-Schalter je Job (Default AN — nur explizites False der
    # Dienst-Config schaltet ab); wirkt nur im Erzeugungs-Fall (Alt-Events).
    _clipdbg_fr.CLIP_VOD = job.get("clip_vod") is not False
    wache = _JobRssWache(_job_rss_grenze(job), antwort_out)
    t0 = os.times()
    t0w = time.monotonic()   # E1/V0.4: WANDUHR je Job — cpu_s allein hatte die v1-Hochrechnung
    #                          in die Irre gefuehrt (CPU-Sekunden sind KEINE Dauer)
    zusatz = None            # E2: ernte-Jobs liefern ihre Zaehler in der Antwort mit
    try:
        with _fd_umleitung(logpfad), wache:
            if typ == "analyze":
                sys.argv = ["analyze.py"] + list(job.get("argv") or [])
                # analyze haelt Zustand auf Modulebene -> run_path gibt jedem Lauf ein
                # frisches Modul-Umfeld; nur der Embedder ueberlebt (Factory oben).
                runpy.run_path(os.path.join(HERE, "analyze.py"), run_name="__main__")
                zusatz = _koerper_zusatz(job.get("argv") or [])
            elif typ == "sammle":
                import anlernen
                anlernen.sammle(float(job.get("tage", 0.1)),
                                mit_migriere=bool(job.get("mit_migriere", False)),
                                kalib_deckel=job.get("kalib_deckel"))
            elif typ == "ernte":
                # E2 Frontal-Ernte, EIN Event je Job (Leitprinzip 5). Z2
                # (konzept_frames v2): Clip ueber core.frames statt eigener
                # SCRATCH-Kopie — EINE Beschaffung je Event fuer alle Wege
                # (Cache-Rangfolge, .part-Atomik samt Waisen-Raeumung, Pin im
                # selben Zug). Der Fallback '/tmp' entfaellt damit ebenfalls:
                # er lag ausserhalb <data_dir>/clips und wurde nie geraeumt.
                from core import ernte as _ernte
                from core import frames as clipcache
                import face_audit
                eid = job["eid"]
                # .288 (Task #11): Alt-Event-Weiche des Dienstes — bei
                # clip_erzeugung wartet clip_holen auf Frigates Clip-
                # ERZEUGUNG (Probe-Schleife statt hartem 30-s-Abbruch, der
                # drueben je Zug 1 Thread + 1 ffmpeg liegen liess, Serie E).
                # Der Deckel kommt aus der Dienst-Config via Job-Feld.
                vid = clipcache.clip_holen(
                    eid, erzeugung=bool(job.get("clip_erzeugung")),
                    erzeugung_deckel_s=job.get("clip_erzeugung_deckel_s"))
                try:
                    # Vorrats-Gate nur, wenn das eingefrorene Job-Regime die
                    # vorrat-Keys traegt (alte Manifeste: None -> Alt-Verhalten).
                    # Der Bau selbst liegt hinter Budget und Wachen-Anmeldung
                    # (_normmass_fuer_ernte) — er ist der einzige Grund, aus dem
                    # dieser Prozess ueberhaupt eine NormMass haelt.
                    nm = (_normmass_fuer_ernte(wache)
                          if _ernte.vorrat_schwellen_da(job["schwellen"]) else None)
                    zusatz = _ernte.ernte_event(
                        vid, eid, job.get("kamera"), float(job.get("ts") or 0),
                        float(job.get("fps_sample") or 3), job["schwellen"],
                        job["lauf_dir"], emb=face_audit.Embedder(), norm_mass=nm,
                        struktur_mass=(_strukturmass_holen()
                                       if job["schwellen"].get("struktur_min")
                                       else None),
                        # .33x DATEIQUELLE: Herkunft aus dem Job in die
                        # Kandidaten-Zeile (Bauplan analysen/12). Alt-Jobs ohne
                        # das Feld liefern None = Frigate, wie bisher.
                        quelle=job.get("quelle"),
                        # Kalibrier-Vorrat je Kamera (Zentral-Umbau 31.08.):
                        # {"data_dir","deckel"} kommt aus dem JOB, nicht aus
                        # dem eingefrorenen Manifest — der Ring-Deckel ist eine
                        # laufende Config-Entscheidung. Alt-Jobs ohne das Feld
                        # ernten unveraendert ohne Vorrats-Speisung.
                        kalib=job.get("kalib"))
                finally:
                    clipcache.frei(eid)   # nie eine Pin-Waise (Size-Cap)
            elif typ == "rechenprobe":
                # Lieferung C (analysen/15 §4): laeuft im BOOT-EXKLUSIVFENSTER als
                # eigener WorkerProzess (verifyd.startup_selfcheck, Schritt 8) — dort
                # ist die GPU frei. Der Prozess LIEFERT nur Daten; gedruckt wird vom
                # Hauptprozess, sonst stuende das Ergebnis nicht im Docker-Log.
                zusatz = _rechenprobe_fuer_job(job)
            elif typ == "koerper":
                # P1 (.202, konzept_speicher.md): das Koerper-URTEIL laeuft im
                # personwork-Prozess statt als ungedeckelter Thread im Main —
                # der 15.08. hat den Main fuenfmal daran sterben lassen. Das
                # RAM-Budget entsteht HIER (eigener VmRSS ist der wahre Stand,
                # exakt das analyze.py-Muster), damit das 10.08.-Gate samt
                # Degradation auf diesem Pfad ZUM ERSTEN MAL wirklich greift
                # (I-1). Melde-/Kontroll-Folgen zieht der Dienst aus der
                # Antwort — dieser Prozess urteilt nur.
                from core import personlive as _plv
                zusatz = {"u": _plv.urteilen(
                    job["data_dir"], os.environ.get("FRIGATE_URL", ""),
                    job["eid"], kontrolle=job.get("kontrolle"),
                    still=bool(job.get("still")),
                    ram_budget_mb=_koerper_budget(job))}
            elif typ == "personlauf_ernte":
                # P1: die ZWEITE Tuer (Personlauf-Ernte lief inline im Main,
                # Widerleger-Fund W-F1) — EIN Event je Job, PoseWache bleibt
                # warm (_werk, Muster des Embedder-Factory oben). Die alte
                # Thread-Zeitwache des Mains entfaellt: haengt ein Event, killt
                # der Dienst diesen Prozess ueber den Job-Timeout — sauberer
                # als ein zurueckbleibender Daemon-Thread samt Puffer.
                from core.personlauf import _proto
                _proto()
                import pfad_snapshots
                from core import personernte as _pe
                if _werk.get("wache") is None:
                    from pose_wache import PoseWache
                    _werk["wache"] = PoseWache()
                budget = _koerper_budget(job)

                def _extraktor(eid):
                    return pfad_snapshots.event_verarbeiten(
                        {"eid": eid}, ram_budget_mb=budget)

                zusatz = {"r": _pe.ernte_event(
                    job["data_dir"], job["lauf_id"], job["job"],
                    _werk["wache"], _extraktor)}
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
               "rss_mb": _rss_mb(), "vmhwm_mb": _vmhwm_mb()}
    # In-Job-Spitze (abgetastet, Wache oben): vmhwm_mb ist die Spitze der PROZESS-
    # Lebenszeit, rss_spitze_mb ordnet sie dem einzelnen Job zu. Additiv (.get()).
    antwort["rss_spitze_mb"] = max(wache.spitze, antwort["rss_mb"])
    # Z8 Mitnahme A (konzept_frames.md §3.2): der Verteiler-Rueckfall auf
    # GETRENNTE Laeufe faellt HIER an, nicht im Dienst — dessen eigenes
    # core.frames saehe fuer immer 0 und /health loege durch Auslassung.
    # Kumulativ ueber die Lebenszeit dieses Worker-Prozesses; der Dienst
    # bildet daraus seine Summe (WorkerProzess.job). Nur melden, wenn der
    # Verteiler ueberhaupt geladen ist — kein Import um des Zaehlers willen.
    if "core.frames" in sys.modules:
        antwort["frame_rueckfaelle"] = int(
            sys.modules["core.frames"].RUECKFAELLE.get("n") or 0)
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
        out.write(json.dumps(_job_ausfuehren(job, antwort_out=out),
                             ensure_ascii=False) + "\n")


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
