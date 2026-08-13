"""core/livewached — der STARTWEG des Live-Waechters (Live-Phase 1).

EIN eigenstaendiger Prozess fuer N Kameras (Architektur B, Bauplan §11
Entscheid 1) — analog zum Prototyp-Start, aber als Produktweg:

    python -m core.livewached run              # Engine starten (Default)
    python -m core.livewached test <kamera>    # Quell-Test (§5) -> test-Block in den Store
    python -m core.livewached status           # Status-Datei lesbar ausgeben

CONFIG-QUELLE (Bauplan §3; Phase 1 = "Config aus dem Store, von Hand
editiert"): verifyd.yaml-Basis (ENV VERIFYD_CONFIG, sonst <wurzel>/
verifyd.yaml) + Config-Store `<data_dir>/config/config.json`, Top-Level-Block
`live` — geladen ueber verifyd.load_config(), das den Store einmischt.
BEWUSST KEINE LIVE_*-ENV: die gehoert dem Prototyp (§3/§9, zwei Wahrheiten
ueber `enabled` waeren die Darstellungs-Fehlklasse).

verifyd wird NUR HIER importiert (Entry-Prozess, dasselbe Muster wie der
Prototyp mit verifyd.load_config) — `core/livewache` selbst bleibt
injektionsrein (Muster core/melden: importiert verifyd NIE). Kein
Import-Zyklus: verifyd importiert dieses Modul nicht; die spaetere
Supervisor-Anbindung (Phase 4, worker.py-Muster mit CLOEXEC-Pipe) startet
den PROZESS, nicht das Modul.

CONFIG-AENDERUNG IM BETRIEB: Phase 1 liest die Config beim Start; eine
Aenderung braucht einen Prozess-Neustart (SIGTERM endet sauber, s. unten).
Der selektive Je-Waechter-Reload (§8 "nur der betroffene Waechter startet
neu") kommt mit der UI-Phase — dokumentierter offener Punkt, kein Versehen.

CPU-ONLY-SPERRE (§11 Entscheid 3): auf einem cpu-Backend startet die Engine
NICHT (klarer Text statt stillem 1090-%-CPU-Betrieb); der sichtbare
UI-Hinweis dazu kommt mit dem Live-Reiter (Phase 2).
"""
import json
import os
import signal
import sys
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WURZEL not in sys.path:
    sys.path.insert(0, WURZEL)

from core import livewache as lw                          # noqa: E402
from core.liveaufsicht import RC_NICHTS_ZU_TUN            # noqa: E402
# ^ Exit-Vertrag Kind -> Supervisor (EINE Quelle, Deckungs-Regel): "kein
#   enabled-Guard" endet mit RC_NICHTS_ZU_TUN statt 0 — der Supervisor
#   unterscheidet das geordnete Nichts-zu-tun damit vom Absturz (rc 0 nach
#   5 s zaehlte sonst als Fehlstart, 3x davon = falsche Stoerungsmeldung).

CONFIG_PFAD = os.environ.get("VERIFYD_CONFIG", os.path.join(WURZEL, "verifyd.yaml"))


def _log(zeile):
    print(f"{time.strftime('%d.%m %H:%M:%S')} {zeile}", flush=True)


def _cfg_laden():
    """yaml-Basis + Store via verifyd.load_config — die EINE Config-Wahrheit
    (kein Nachbau des Ladewegs, K3)."""
    import verifyd
    return verifyd.load_config(CONFIG_PFAD), verifyd


class Detektor:
    """Der EINE geteilte Detektor-Kontext der Engine (Architektur B).

    Baut face_audit.Embedder MIT lauter Backend-Kontrolle (K1-Lehre 09.08.:
    ohne Kontrolle faellt onnxruntime still auf CPU, Faktor ~150) und stellt
    das Detektor-Netz je Kachel-Geometrie um: set_det_size() setzt nur
    Attribute (P1-Beweis in face_audit) — bei gemischten Seitenverhaeltnissen
    wechselt das Netz je Frame; OpenVINO kompiliert je Shape genau EINMAL
    (P4/W0-Cache). Die realen Wechselkosten misst der Ein-Waechter-Realtest
    bzw. der 2-Kamera-Schritt (Phase 3) — offener Messpunkt, dokumentiert."""

    def __init__(self, log=_log):
        from face_audit import Embedder
        self.log = log
        self.app = Embedder()
        self._netz = None
        prov = self.provider()
        if prov.startswith("CPU"):
            log("!! Detektion laeuft auf CPU — auf einer GPU-Variante ist das "
                "der stille Rueckfall (K1); Live erwartet einen GPU-Provider")
        else:
            log(f"Detektion: {prov}")

    def provider(self):
        try:
            return self.app.app.models["detection"].session.get_providers()[0] \
                .replace("ExecutionProvider", "")
        except Exception:
            return "unbekannt"

    def erkennen(self, frame_bgr, netz):
        if netz and netz != self._netz:
            self.app.set_det_size(tuple(netz))
            self._netz = tuple(netz)
        return self.app.app.get(frame_bgr) or []


def _cpu_sperre(log=_log):
    """§11 Entscheid 3: Live ist fuer CPU-only GESPERRT (Messbasis: CPU-Sub-
    Test 11.08. — funktional, aber erst nach Anpassungen tragfaehig; bis
    dahin fail-closed). -> True, wenn gesperrt.

    Der Hinweistext nennt die GANZE Hardware-Welt (Lens-B B2: der alte Text
    kannte nur Intel/NVIDIA — ein ROCm-Nutzer las, dass sein Geraet nicht
    vorkommt). Deckungs-Vertrag tools/deckung_pruefen.py, Mengen-Quelle
    core.registry: kinds cpu, openvino, cuda, migraphx · Image-Varianten
    gpu, cpu, cuda, gpu-legacy, rocm."""
    from face_audit import resolve_backend
    kind, _dev = resolve_backend()
    if kind == "cpu":
        log("Live watchers require a GPU build — integrated Intel graphics "
            "(gpu / gpu-legacy images, OpenVINO), an NVIDIA card (cuda image) "
            "or an AMD card (rocm image, MIGraphX) all qualify. They are not "
            "available on the cpu image (CPU-only). "
            "(Bauplan §11 Entscheid 3; engine refuses to start)")
        return True
    return False


def _mqtt_client(cfg, log=_log):
    """Eigener paho-Client der Engine (Bauplan §6/melden.mqtt_pub-Vertrag:
    `pub` kommt vom Aufrufer). BEWUSST OHNE Heartbeat — verifyd/heartbeat
    gehoert dem Dienst, eine zweite Quelle waere eine Luege im Topic."""
    braucht = any("mqtt" in (g.get("kanaele") or [])
                  for g in (cfg.get("live", {}).get("guards") or {}).values()
                  if g.get("enabled"))
    if not braucht:
        return None
    m = cfg.get("mqtt") or {}
    if not m.get("host"):
        log("live: mqtt channel configured but no broker in config — "
            "mqtt alerts will report as failed")
        return None
    try:
        import paho.mqtt.client as mqtt
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if m.get("user"):
            c.username_pw_set(m["user"], m.get("password", ""))
        c.reconnect_delay_set(min_delay=1, max_delay=60)
        c.connect_async(m["host"], int(m.get("port", 1883)), 60)
        c.loop_start()
        log(f"live: mqtt publisher connecting to {m['host']}:{m.get('port', 1883)}")
        return c
    except Exception as e:
        log(f"live: mqtt publisher not available: {e}")
        return None


def referenzen_noetig(guards):
    """Sollen die Referenzen fuers Namens-Voting geladen werden? Seit .197
    JA, sobald irgendein Waechter enabled ist (der Quick-verdict-Haken ist
    abgeschafft). ALS FUNKTION herausgeloest (.198): der .197-Start-Absturz
    (KeyError schnell_urteil, Engine 3x tot, 15-min-Pause) sass in genau
    diesem Praedikat als Inline-Genexpr — die QS-Stufe S10 ruft die Funktion
    jetzt mit guards_lesen-normalisierten Guards durch, Feld-Drift zwischen
    guards_lesen und diesem Modul crasht damit im GATE, nicht auf Prod."""
    return any(g["enabled"] for g in guards.values())


def cmd_run():
    cfg, verifyd = _cfg_laden()
    if _cpu_sperre():
        return 2
    defaults, guards = lw.guards_lesen(cfg, _log)
    if not any(g["enabled"] for g in guards.values()):
        _log("live: no enabled guard in config store (live.guards.<camera>."
             "enabled) — nothing to do. Run 'test <camera>' first, then enable.")
        return RC_NICHTS_ZU_TUN
    # Detektor + Referenzen: die det-320-FALLE gilt (referenzen_laden-Docstring)
    # — Referenzen ZUERST, solange der Embedder auf 320 steht; das grosse Netz
    # stellt erst der Betrieb je Kachel.
    det = Detektor(_log)
    refs, ref_quelle, schwelle = {}, "aus", None
    if referenzen_noetig(guards):
        try:
            refs, ref_quelle = lw.referenzen_laden(det.app)
            schwelle = float(cfg["win_thresh"])
            _log(f"live: Schnell-Urteil {sum(len(M) for M in refs.values())} "
                 f"Referenzen / {len(refs)} Personen aus {ref_quelle}, Schwelle "
                 f"{schwelle:.2f} (win_thresh) — VORLAEUFIG, nur fuer die Meldung")
        except Exception as e:
            refs, schwelle = {}, None
            _log(f"live: Schnell-Urteil aus ({type(e).__name__}: {e})")
    kameras, kam_fehler = verifyd.frigate_cameras(cfg)
    if kam_fehler:
        _log(f"live: Frigate camera list unavailable ({kam_fehler}) — "
             f"feed inventory limited to configured guards")
    pub = _mqtt_client(cfg, _log)
    melder = lw.Melder(cfg, _log, pub=pub)
    engine = lw.Engine(cfg, _log, detektor=det,
                       detektor_fabrik=lambda: Detektor(_log),
                       melder=melder, kameras=kameras or None,
                       refs=refs, win_thresh=schwelle,
                       # Phase 2: Store-Reload je Waechter (Mtime-Wache) und
                       # Auftrags-Strecke (Quelltest/Last-Messung per
                       # Kommando-Datei des Dienstes) — Config-Quelle bleibt
                       # die EINE load_config-Wahrheit (kein Nachbau, K3).
                       config_quelle=lambda: verifyd.load_config(CONFIG_PFAD),
                       store_pfad=verifyd._config_store_pfad(cfg))

    def _ende(signum, _rahmen):
        engine.stop(f"signal {signum}")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _ende)
    if not engine.start():
        return 3
    engine.warten()
    # stop() IMMER — auch wenn der Todespfad stop_ev selbst gesetzt hat
    # (Lens-A B3/M11: sonst blieben Threads ungejoint, angestossene Meldungen
    # gingen verloren und die Statusdatei behielt engine:'ok').
    engine.stop("ende")
    if pub is not None:
        try:
            pub.loop_stop()
            pub.disconnect()
        except Exception:
            pass
    if engine.engine_fehler:
        _log(f"live: engine ended with error: {engine.engine_fehler}")
        return 1
    return 0


def cmd_test(kamera, als_json=False):
    """Quell-Test (§5) fahren und den test-Block in den Store schreiben —
    damit ist der Enable-Riegel (test.ok + Fingerprint) SERVERSEITIG bedienbar,
    bevor es die UI gibt (Phase 1: Store von Hand + dieser Befehl).

    EHRLICHE GRENZE (CLI-Weg): der Store-Schreib laeuft prozess-uebergreifend
    ohne gemeinsames Lock mit einem laufenden verifyd (dessen _cfg_lock ist
    prozess-intern); letzter Schreiber gewinnt.

    --json (Phase 2, UI-Weg OHNE laufende Engine): Ergebnis als EINE
    JSON-Zeile auf stdout, KEIN Store-Schreib — der DIENST uebernimmt den
    test-Block dann selbst unter seinem _cfg_lock (Schreibweg hinter der UI,
    Bauplan §3; die Race-Grenze des CLI-Wegs entfaellt dort). Ein Guard muss
    dafuer noch nicht existieren (die UI testet auch unkonfigurierte
    Kameras mit dem proxy-Default)."""
    cfg, verifyd = _cfg_laden()
    if _cpu_sperre():
        return 2
    _defaults, guards = lw.guards_lesen(cfg, _log)
    guard = guards.get(kamera)
    if guard is None:
        if not als_json:
            _log(f"live test: no live.guards entry for {kamera!r} in the config "
                 f"store — add one first (Bauplan §3 schema)")
            return 1
        guard = {"quelle": "proxy", "url": ""}
    det = Detektor(_log)
    ok, text, block = lw.quelle_testen(cfg, kamera, guard, det, log=_log,
                                       det_basis=_defaults["det_basis"],
                                       hoehe=_defaults["hoehe"])
    _log(f"live test {kamera}: {'GRUEN' if ok else 'ROT'} — {text}")
    if als_json:
        print(json.dumps({"ok": ok, "text": text, "block": block},
                         ensure_ascii=False), flush=True)
        return 0 if ok else 1
    if ok and block:
        store = verifyd._lade_config_store(cfg)
        g = store.setdefault("live", {}).setdefault("guards", {}).setdefault(kamera, {})
        g["test"] = block
        verifyd._store_schreiben(verifyd._config_store_pfad(cfg), store)
        _log(f"live test {kamera}: test-Block gespeichert (quelle_fp "
             f"{block['quelle_fp']}) — enable prueft genau diesen Fingerprint")
    return 0 if ok else 1


def cmd_status():
    cfg, _verifyd = _cfg_laden()
    pfad = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", "live_status.json")
    # Frische-Urteil aus der EINEN Quelle (lw.status_lesen — dieselbe, die
    # auch UI-Kacheln und /health speist; K3).
    d, frisch = lw.status_lesen(cfg)
    if d is None:
        print(f"kein Status lesbar ({pfad})")
        return 1
    alter = time.time() - float(d.get("ts") or 0)
    print(f"live_status.json ({pfad})")
    print(f"  Herzschlag: vor {alter:.1f} s "
          f"({'FRISCH' if frisch else 'ALT — Engine laeuft nicht?'}), "
          f"engine={d.get('engine')}, pid={d.get('pid')}")
    print(f"  Scheduler: {d.get('scheduler')}")
    print(f"  Slots: {d.get('slots')}")
    for name, grund in (d.get("verweigert") or {}).items():
        print(f"  VERWEIGERT {name}: {grund}")
    for name, k in sorted((d.get("kacheln") or {}).items()):
        print(f"  {name}: {k.get('zustand')}"
              + (f" ({k.get('grund')})" if k.get("grund") else "")
              + f" — Bild vor {k.get('letztes_bild_alter_s')} s, "
                f"{k.get('trigger')} Trigger / {k.get('gemeldet')} gemeldet, "
                f"{k.get('auftritte')} Auftritte, watchdog {k.get('watchdog_kills')}, "
                f"abrisse {k.get('abrisse')}")
    return 0 if frisch else 1


def main(argv):
    # umask 022 auch fuer den HANDSTART (der Aufsicht-Spawn erbt sie vom
    # Dienst, verifyd.main setzt sie dort — hier dieselbe Regel fuer den
    # Standalone-Weg; Realfall 13.08.: 600er-root-Dateien im /data-Mount
    # waren vom Host nicht lesbar/sicherbar).
    os.umask(0o022)
    was = argv[1] if len(argv) > 1 else "run"
    if was == "run":
        return cmd_run()
    if was == "test":
        rest = [a for a in argv[2:] if a != "--json"]
        if not rest:
            print("usage: python -m core.livewached test <kamera> [--json]")
            return 1
        return cmd_test(rest[0], als_json="--json" in argv[2:])
    if was == "status":
        return cmd_status()
    print(f"unbekanntes Kommando: {was} (run | test <kamera> | status)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
