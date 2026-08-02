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
FRIGATE = os.environ.get("FRIGATE_URL", "")
# SSH-Reste (LXC-Credentials, Remote-Faces-Pfad) mit 0.1.0.107 entfallen — der Export
# laeuft ueber die HTTP-API, s. api_upload(). Nichts hier braucht mehr Host-Zugang.
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
    with urllib.request.urlopen(f"{FRIGATE}/api/faces", timeout=20) as r:
        d = json.load(r)
    return {k: sorted(v) for k, v in d.items() if k != "train"}


def diff():
    m, f = master_stand(), frigate_stand()
    _, tomb = lade_meta()
    nur_frigate, nur_master, extern_geloescht = [], [], []
    for p in sorted(set(m) | set(f)):
        ms, fs = set(m.get(p, [])), set(f.get(p, []))
        for datei in sorted(fs - ms):
            (nur_frigate if (p, datei) not in tomb else []).append((p, datei))
        for datei in sorted(ms - fs):
            # Master-Bild fehlt in Frigate: entweder nie exportiert (Herkunft enrollment/
            # upload) oder EXTERN GELOESCHT (Herkunft frigate-import)
            aktiv, _ = lade_meta()
            herkunft = (aktiv.get((p, datei)) or {}).get("herkunft", "?")
            (extern_geloescht if herkunft.startswith("frigate-import") else nur_master).append((p, datei))
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
            with urllib.request.urlopen(f"{FRIGATE}/clips/faces/{urllib.parse.quote(p)}/{urllib.parse.quote(datei)}",
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


def api_upload(person, datei, quelle):
    """Referenzbild ueber die Frigate-HTTP-API hochladen: POST /api/faces/{name}, Feld `file`
    (Endpunkte aus dem Frigate-Quellcode verifiziert).

    Loest den SSH/scp-Altweg ab (CLAUDE.md-Invariante 'Frigate NUR ueber die HTTP-API':
    fremde Nutzer haben keinen Root-SSH auf ihr Frigate, der Weg lief hier nur zufaellig).
    Zugleich Sicherheits-Fix (Sweep 03.08., Schwere hoch): der alte Weg interpolierte den
    PERSONEN-Namen in eine Remote-Shell-Zeile (`mkdir -p '<pfad>/<person>'`). _NAME_OK
    erlaubt bewusst alles ausser / \\ NUL — also auch Apostroph und $(...). Ein per
    /api/faces gelieferter Name wie "Anna';id;#" fuehrte damit Kommandos auf dem
    Frigate-Host aus (end-to-end nachgestellt), und schon ein legitimes "O'Brien" liess
    den ganzen Export mit Syntaxfehler abbrechen. Ueber die API ist der Name ein
    URL-Segment (quote) und ein Formularfeld — keine Shell im Spiel.
    """
    if not FRIGATE:
        raise RuntimeError("FRIGATE_URL fehlt — Export ueber die API nicht moeglich")
    grenze = uuid.uuid4().hex
    inhalt = open(quelle, "rb").read()
    typ = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
           "webp": "image/webp"}.get(datei.rsplit(".", 1)[-1].lower(), "application/octet-stream")
    body = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{os.path.basename(datei)}\"\r\nContent-Type: {typ}\r\n\r\n").encode() \
        + inhalt + f"\r\n--{grenze}--\r\n".encode()
    req = urllib.request.Request(
        f"{FRIGATE.rstrip('/')}/api/faces/{urllib.parse.quote(person, safe='')}",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={grenze}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status not in (200, 201):
            raise RuntimeError(f"Frigate-API antwortete HTTP {r.status}")


def cmd_export(dry, auch_extern=False):
    nf, nm, eg = diff()
    kandidaten = nm + (eg if auch_extern else [])
    if not kandidaten:
        _progress(phase="done", total=0, done=0, ok=0, gate=0)
        print("nichts zu exportieren." + (f" ({len(eg)} extern geloeschte nur mit --auch-extern-geloeschte)" if eg else ""))
        return
    total = len(kandidaten)
    for i, (p, datei) in enumerate(kandidaten):
        _progress(phase="export", total=total, done=i, current=p)
        quelle = os.path.join(MASTER, p, datei)
        ziel = f"api:/api/faces/{p}"     # Protokoll-Vermerk: WOHIN exportiert wurde
        if dry:
            print(f"  [dry] exportiere {p}/{datei}")
            continue
        api_upload(p, datei, quelle)
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
