#!/usr/bin/env python3
"""Referenz-Sync Master <-> Frigate (Plan v1.0 AP1).

Master = verify_data/refs/<Person>/*.jpg + refs_meta.jsonl (Herkunft, aktiv-Flag,
Tombstones). Frigate-Ablage = /opt/frigate/media/clips/faces/<Person>/.

  sync_refs.py status              # Diff beider Seiten + offene Entscheidungen
  sync_refs.py import [--dry-run]  # NEUE Frigate-Bilder -> Master (mit Gesichts-Gate;
                                   #   Tombstones werden NIE re-importiert)
  sync_refs.py export [--dry-run]  # aktive Master-Bilder, die Frigate fehlen -> POST
                                   #   /api/faces/{name} (HTTP-API; der SSH/scp-Altweg ist
                                   #   seit 0.1.0.107 abgeloest — Invariante + Shell-Injektion)

Konfliktregel (Plan §AP1): in Frigate GELOESCHTE, im Master aktive Bilder werden NICHT
still re-exportiert — status meldet sie als offene Entscheidung (User loescht im Master
oder exportiert bewusst per --auch-extern-geloeschte)."""
import os, re, sys, json, time, urllib.parse, urllib.request, uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("VERIFY_DATA_DIR") or os.path.join(HERE, "verify_data")   # Container: /data
MASTER = os.path.join(DATA, "faces")
META = os.path.join(MASTER, "refs_meta.jsonl")
# SSH-Reste (LXC-Credentials, Remote-Faces-Pfad) mit 0.1.0.107 entfallen — der Export
# laeuft ueber die HTTP-API, s. api_upload(). Nichts hier braucht mehr Host-Zugang.


def _frigate():
    """Frigate-Basis-URL zur AUFRUF-Zeit aus der ENV (#18 carlsmith360): der
    Dienst exportiert die im UI gespeicherte URL erst beim Config-Laden nach
    os.environ — ein beim Import eingefrorener Leer-Wert machte jede
    Sync-Funktion dauerhaft blind ('unknown url type: /api/faces'). Fuer den
    CLI-Weg (source .env) aendert sich nichts."""
    return os.environ.get("FRIGATE_URL", "")
PROGRESS = os.path.join(DATA, "state", "sync_progress.json")   # Fortschritt fuer die UI (X von Y)


def _progress(**d):
    """Fortschritt atomar in eine Statusdatei schreiben; die UI pollt sie (/sync_status)."""
    try:
        os.makedirs(os.path.dirname(PROGRESS), exist_ok=True)
        tmp = PROGRESS + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"ts": round(time.time(), 1), **d}, f)
        os.replace(tmp, PROGRESS)
    except Exception:
        pass


ERLAUBTE_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")
# Permissiv und UNICODE-bewusst: echte Namen wie "Müller" oder "Anna-Lena" muessen durch,
# sonst faellt ein legitimer Import STILL aus (Fehlerklasse C). Verboten sind nur die Zeichen,
# die Pfade aufbrechen. Die eigentliche Sicherheit macht das realpath-Containment darunter.
# Bis 03.08. stand hier nur "alles ausser / \\ NUL" — permissiver als JEDE Konsumenten-
# Pruefung. Folge (Sweep-Befund): ein Frigate-Gesicht "Anna.B"/"Tim+Bo" wurde importiert,
# war auf der Known-Seite sichtbar, aber unbedienbar (Thumbnails 404, Loeschen
# "ungueltiger Pfad"). Jetzt gilt derselbe Vertrag wie fuer die Verbraucher; was nicht
# passt, wird LAUT uebersprungen (Zeile im Import-Log) statt still unbrauchbar angelegt.
from core.registry import PERSON_RE as _PERSON_RE
_NAME_OK = re.compile(rf"^{_PERSON_RE}$", re.UNICODE)


def sicheres_ziel(person, datei):
    """Schreibziel fuer ein Referenzbild bauen — oder (None, Grund), wenn es unsicher ist.

    Die Namen kommen aus /api/faces der GEGENSTELLE und sind damit Fremdeingabe: die
    Frigate-URL ist ueber POST /sync_import frei setzbar. Ohne Pruefung landet person='../../app'
    per os.path.join ausserhalb von MASTER — im Container als root, mit /app/verifyd.py als
    Ziel (Codeausfuehrung beim naechsten Neustart). Zwei Schichten, absichtlich redundant:
    1. Namens-/Endungs-Whitelist (faengt das Offensichtliche und haelt den Master sauber),
    2. realpath-Containment (die eigentliche Garantie — greift auch bei Symlinks und bei
       allem, woran die Regex nicht gedacht hat)."""
    if not person or not datei:
        return None, "leerer Name"
    if person in (".", "..") or datei in (".", ".."):
        return None, "Punkt-Eintrag"
    if not _NAME_OK.match(person) or not _NAME_OK.match(datei):
        return None, "unerlaubte Zeichen im Namen"
    if not datei.lower().endswith(ERLAUBTE_ENDUNGEN):
        return None, "unerlaubte Dateiendung"
    ziel = os.path.join(MASTER, person, datei)
    basis = os.path.realpath(MASTER)
    echt = os.path.realpath(ziel)
    if echt != basis and not echt.startswith(basis + os.sep):
        return None, "Pfad zeigt aus dem Master heraus"
    return ziel, ""


def lade_meta():
    aktiv, tomb = {}, set()
    if os.path.exists(META):
        for l in open(META):
            try:
                d = json.loads(l)
            except Exception:
                continue
            key = (d["person"], d["datei"])
            if d.get("aktiv", True):
                aktiv[key] = d
                tomb.discard(key)
            else:
                tomb.add(key)
                aktiv.pop(key, None)
    return aktiv, tomb


def meta_append(**d):
    with open(META, "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), **d}, ensure_ascii=False) + "\n")
        f.flush()


def master_stand():
    out = {}
    for p in sorted(os.listdir(MASTER)):
        d = os.path.join(MASTER, p)
        if os.path.isdir(d):
            out[p] = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    return out


def frigate_stand():
    with urllib.request.urlopen(f"{_frigate()}/api/faces", timeout=20) as r:
        d = json.load(r)
    return {k: sorted(v) for k, v in d.items() if k != "train"}


def diff():
    """-> (nur_frigate, nur_master, extern_geloescht). EXPORT-DEDUP LAEUFT UEBERS
    PROTOKOLL, nicht ueber Frigate-Dateinamen (Live-Befund 05.08. am echten
    0.18.0: /register benennt JEDES Bild in <Name>_<timestamp>.webp um und
    verarbeitet asynchron — ein Namens-Abgleich saehe Exportiertes ewig als
    'fehlend' und wuerde es bei jedem Lauf erneut hochpumpen; mit dem alten
    SSH-Weg blieben die Namen erhalten, daher trug der Abgleich frueher).
    Ein Master-Bild mit aktivem export-Protokolleintrag ist deshalb NIE wieder
    Export-Kandidat. Bekannte Grenze (Design-Entscheid offen): die von Frigate
    umbenannten Exporte erscheinen in nur_frigate als Import-Kandidaten —
    cmd_import ist manuell, nichts laeuft von allein."""
    m, f = master_stand(), frigate_stand()
    aktiv, tomb = lade_meta()
    nur_frigate, nur_master, extern_geloescht = [], [], []
    for p in sorted(set(m) | set(f)):
        ms, fs = set(m.get(p, [])), set(f.get(p, []))
        for datei in sorted(fs - ms):
            if (p, datei) not in tomb:
                nur_frigate.append((p, datei))
        for datei in sorted(ms - fs):
            # Master-Bild fehlt in Frigate: nie exportiert (enrollment/upload) ->
            # Kandidat · schon exportiert -> Frigate fuehrt es unter eigenem
            # Namen, NIE erneut senden · Herkunft frigate-import -> dort geloescht.
            herkunft = (aktiv.get((p, datei)) or {}).get("herkunft", "?")
            if herkunft.startswith("frigate-import"):
                extern_geloescht.append((p, datei))
            elif herkunft != "export":
                nur_master.append((p, datei))
    return nur_frigate, nur_master, extern_geloescht


def cmd_status():
    nf, nm, eg = diff()
    print(f"Neu in Frigate (Import-Kandidaten): {len(nf)}")
    for p, d in nf[:10]:
        print(f"  + {p}/{d}")
    print(f"Nur im Master, nie exportiert (Export-Kandidaten): {len(nm)}")
    for p, d in nm[:10]:
        print(f"  > {p}/{d}")
    print(f"EXTERN GELOESCHT (in Frigate weg, im Master aktiv) — Entscheidung offen: {len(eg)}")
    for p, d in eg[:10]:
        print(f"  ! {p}/{d}  (Master loeschen ODER bewusst re-exportieren)")
    # Ehrliche Zusatzzeile (nie stilles Verschwinden): schon Exportiertes fuehrt
    # Frigate 0.18 unter EIGENEM Namen (<Name>_<ts>.webp) — es fehlt im
    # Namens-Abgleich, ist aber KEIN Kandidat und KEIN Verlust.
    aktiv, _t = lade_meta()
    m, f = master_stand(), frigate_stand()
    n_exp = sum(1 for (p, d), e in aktiv.items()
                if e.get("herkunft") == "export"
                and d in set(m.get(p, [])) and d not in set(f.get(p, [])))
    if n_exp:
        print(f"Bereits exportiert, von Frigate unter eigenem Namen gefuehrt: {n_exp}")
    if not (nf or nm or eg):
        print("=> synchron.")


def cmd_import(dry):
    # Frigate-Referenzbilder sind bereits fertige Gesichts-Crops -> KEIN CPU-Face-Gate hier. Das war
    # redundant: nach dem Import rechnet der Dienst alle Embeddings ohnehin neu, und ZWAR auf der GPU
    # (refcache-Neuaufbau). Hier nur schnell herunterladen; die Rechenarbeit macht die GPU.
    nf, _, _ = diff()
    if not nf:
        _progress(phase="done", total=0, done=0, ok=0, gate=0)
        print("nichts zu importieren.")
        return
    total = len(nf)
    n_ok = n_dl = n_bad = 0
    for i, (p, datei) in enumerate(nf):
        _progress(phase="import", total=total, done=i, current=p, ok=n_ok, gate=n_dl)
        ziel, grund = sicheres_ziel(p, datei)      # Fremdeingabe: NIE ungeprueft in einen Pfad
        if ziel is None:
            n_bad += 1
            print(f"  ABGELEHNT: {p!r}/{datei!r} ({grund}) -> uebersprungen")
            continue
        if dry:
            n_ok += 1
            print(f"  [dry] importiere {p}/{datei}")
            continue
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        try:
            with urllib.request.urlopen(f"{_frigate()}/clips/faces/{urllib.parse.quote(p)}/{urllib.parse.quote(datei)}",
                                        timeout=20) as r:
                data = r.read()
            with open(ziel, "wb") as f:
                f.write(data)
        except Exception as e:
            # KEIN Tombstone: ein Timeout/500 ist transient, ein Tombstone waere permanent und
            # sperrte das Bild fuer alle kuenftigen Importe aus (lade_meta -> tomb). Nur zaehlen,
            # der naechste Lauf versucht es erneut.
            n_dl += 1
            print(f"  DOWNLOAD-FEHLER: {p}/{datei} ({str(e)[:40]}) -> uebersprungen (kein Tombstone, Retry beim naechsten Lauf)")
            continue
        n_ok += 1
        meta_append(person=p, datei=datei, herkunft="frigate-import", aktiv=True)
        print(f"  importiert: {p}/{datei}")
    _progress(phase="done", total=total, done=total, ok=n_ok, gate=n_dl, abgelehnt=n_bad)
    msg = f"=> {n_ok} importiert{' (dry)' if dry else ''}, {n_dl} Download-Fehler"
    if n_bad:
        msg += f", {n_bad} ABGELEHNT (unsichere Namen)"     # laut, nicht still
    print(msg)


def api_upload(person, datei, quelle, person_existiert=None):
    """Referenzbild ueber die Frigate-HTTP-API hochladen (Frigate 0.18.0, Endpunkte
    aus der OpenAPI der LAUFENDEN Instanz verifiziert, 05.08. — der fruehere
    POST /api/faces/{name} existiert dort NICHT, 404):
      1. unbekannter Name -> POST /api/faces/{name}/create (legt den Namen an),
      2. Bild             -> POST /api/faces/{name}/register (multipart, Feld `file`).
    person_existiert: vom Aufrufer gereichter Ist-Stand (spart je Datei einen
    /api/faces-Abruf); None = selbst nachschauen.

    WICHTIG: Frigate verweigert JEDE Faces-Mutation mit 400 'Face recognition is
    not enabled.', solange die hauseigene Gesichtserkennung aus ist — das wird
    hier als klarer Fehlertext gemeldet, nie als nackter HTTP-Fehler.

    Loest den SSH/scp-Altweg ab (CLAUDE.md-Invariante 'Frigate NUR ueber die
    HTTP-API'; Sicherheits-Fix Sweep 03.08.: der alte Weg interpolierte den
    Personen-Namen in eine Remote-Shell-Zeile — ueber die API ist der Name ein
    URL-Segment (quote) und ein Formularfeld, keine Shell im Spiel)."""
    if not _frigate():
        raise RuntimeError("FRIGATE_URL fehlt — Export ueber die API nicht moeglich")
    basis = _frigate().rstrip("/")
    pq = urllib.parse.quote(person, safe="")

    def _lesen(r):
        if r.status not in (200, 201):
            raise RuntimeError(f"Frigate-API antwortete HTTP {r.status}")
        return r.read()

    def _mutation(req):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return _lesen(r)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read()).get("message", "")
            except Exception:
                pass
            if "not enabled" in detail.lower():
                raise RuntimeError(
                    "Frigate refuses face changes: its own face recognition is "
                    "disabled (face_recognition.enabled: false). Enable it in "
                    "Frigate to use the sync, or leave the sync off.") from e
            raise RuntimeError(f"Frigate-API HTTP {e.code}: {detail or e.reason}") from e

    if person_existiert is None:
        person_existiert = person in frigate_stand()
    if not person_existiert:
        _mutation(urllib.request.Request(f"{basis}/api/faces/{pq}/create",
                                         data=b"", method="POST"))
    grenze = uuid.uuid4().hex
    inhalt = open(quelle, "rb").read()
    typ = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
           "webp": "image/webp"}.get(datei.rsplit(".", 1)[-1].lower(), "application/octet-stream")
    body = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{os.path.basename(datei)}\"\r\nContent-Type: {typ}\r\n\r\n").encode() \
        + inhalt + f"\r\n--{grenze}--\r\n".encode()
    _mutation(urllib.request.Request(
        f"{basis}/api/faces/{pq}/register",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={grenze}"}))


def cmd_export(dry, auch_extern=False):
    nf, nm, eg = diff()
    kandidaten = nm + (eg if auch_extern else [])
    if not kandidaten:
        _progress(phase="done", total=0, done=0, ok=0, gate=0)
        print("nichts zu exportieren." + (f" ({len(eg)} extern geloeschte nur mit --auch-extern-geloeschte)" if eg else ""))
        return
    total = len(kandidaten)
    vorhanden = set(frigate_stand())     # einmal geholt: wer braucht /create?
    for i, (p, datei) in enumerate(kandidaten):
        _progress(phase="export", total=total, done=i, current=p)
        quelle = os.path.join(MASTER, p, datei)
        ziel = f"api:/api/faces/{p}"     # Protokoll-Vermerk: WOHIN exportiert wurde
        if dry:
            print(f"  [dry] exportiere {p}/{datei}")
            continue
        api_upload(p, datei, quelle, person_existiert=p in vorhanden)
        vorhanden.add(p)
        meta_append(person=p, datei=datei, herkunft="export", aktiv=True, ziel=ziel)
        print(f"  exportiert: {p}/{datei}")
    _progress(phase="done", total=len(kandidaten), done=len(kandidaten), ok=len(kandidaten), gate=0)
    print(f"=> {len(kandidaten)} exportiert{' (dry)' if dry else ''}")


if __name__ == "__main__":
    import urllib.parse
    modus = sys.argv[1] if len(sys.argv) > 1 else "status"
    dry = "--dry-run" in sys.argv
    if modus == "status":
        cmd_status()
    elif modus == "import":
        cmd_import(dry)
    elif modus == "export":
        cmd_export(dry, auch_extern="--auch-extern-geloeschte" in sys.argv)
    else:
        print(__doc__)
