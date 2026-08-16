"""auftritte — die Personen-Tagessicht (Paket B / 0.1.0.50, Spec 02_today §4.3/S3).

Klick auf eine Person landet hier statt auf einem Einzel-Event: je DURCHGANG ein Block
(Zeitspanne, Kamerafolge, bestes Bild des ganzen Durchgangs, Gesichts-Thumbnails,
wer sonst noch da war). Das ist das Szenario-Prinzip als Klickpfad — die Einzel-Events
bleiben als Beleg erreichbar, sind aber kein Einstieg mehr.
Neues Modul nach der E6c-Regel; nutzt dieselbe szenarien_des_tages()-Gruppierung wie /heute.
Review-Fassung (Opus-Diff-Review + User-Feedback 27.07.): Thumbnail-Streifen zeigt NUR
Events mit Gesichts-Crop der Person (Entwicklung des Gesichts ueber den Durchgang statt
grauer Uhrzeit-Kacheln; Rest als "+N events without a face"); unbestaetigte Crops gedimmt;
Kopfzeile = Durchgangs-Spanne, Bestaetigungs-Spanne separat; best-match-Kamera aus dem
BEST-Event (nicht der letzten Bestaetigung); Unbekannt-Angabe zaehlt ehrlich EVENTS.
v1-Abweichung von der Spec (dokumentiert): U-Nummern-Anreicherung folgt mit dem
Label-Schritt (naechste Etappe)."""
import datetime
import html
import json
import os
import urllib.parse

from core import unbekanntpool

import szenarien as _szen
from core import areas as _areas_mod        # Areas Stufe 1: Sicht-Aufloesung (30.07.)
from routes import areas as _r_areas        # Chip-Leiste (reine Links)



def _koerper(cfg):
    """Koerper-Treffer-Karte + Stuetzen-Regel fuer die Zuschreibung —
    dieselbe Quelle wie /heute (Fusion Schritt 1; .119: auch hier, damit
    Personen-Tagessicht und Today dieselben Passe zaehlen)."""
    try:
        from core import personlive as _plv
        from core import personmodell as _pm
        kmap = _plv.treffer_karte(cfg["data_dir"])
        kab = int((_pm.status_lesen(cfg["data_dir"]) or {})
                  .get("feuer_ab") or _plv.FEUER_AB)
        return kmap, kab
    except Exception:
        return {}, 2

def _hhmm(t):
    return datetime.datetime.fromtimestamp(t).strftime("%H:%M")


def _ref_eids(cfg, person):
    """Events, aus denen AKTIVE Referenzen dieser Person stammen (.227,
    User-Fund: nach der Uebernahme sah man den Bildern nicht an, dass sie
    jetzt Referenzen sind). Letzte refs_meta-Zeile je Datei gilt (Tombstones
    setzen aktiv:false)."""
    stand = {}
    try:
        for zeile in open(os.path.join(cfg["data_dir"], "faces",
                                       "refs_meta.jsonl")):
            try:
                e = json.loads(zeile)
            except ValueError:
                continue
            if e.get("person") == person and e.get("datei"):
                # .228 (Live-Fund): die Referenz-Pruefung schreibt je Datei
                # NEUE Zeilen OHNE eid-Feld — das eid frueherer Zeilen bleibt
                # deshalb erhalten, nur der aktiv-Status folgt der letzten
                # Zeile (Tombstones wirken weiter).
                alt_eid = stand.get(e["datei"], (None, False))[0]
                stand[e["datei"]] = (e.get("eid") or alt_eid,
                                     bool(e.get("aktiv")))
    except OSError:
        return set()
    return {eid for eid, aktiv in stand.values() if aktiv and eid}


def _crop_url(cfg, eid, person):
    ed = str(eid or "").replace("/", "_")
    edir = os.path.join(cfg["data_dir"], "events", ed)
    if ed and os.path.isdir(edir):
        js = (sorted(c for c in os.listdir(edir) if f"_show_{person}_" in c) or
              sorted(c for c in os.listdir(edir) if f"_best_{person}_" in c))
        if js:      # sorted + [-1]: hoechster Score gewinnt (Namen tragen den Score, zero-padded)
            return f"/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(js[-1])}"
    return None


def _lade_rows(log_pfad):
    rows = []
    if os.path.exists(log_pfad):
        with open(log_pfad) as f:
            for l in f:
                try:
                    rows.append(json.loads(l))
                except Exception:
                    pass
    return rows


def _lade_gtmap(cfg):
    gtmap = {}                       # eid -> letztes Label (F2)
    gtp = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
    if os.path.exists(gtp):
        with open(gtp) as f:
            for l in f:
                try:
                    d0 = json.loads(l); gtmap[d0["eid"]] = d0["label"]
                except Exception:
                    pass
    return gtmap


def _eid2uid(cfg):
    """eid -> U-Nummer aus dem Unbekannt-Pool (Haeppchen 2): dieselbe Zuordnung wie die
    /heute-Karten (face_id IST die Event-ID; ~2/~3-Suffixe der Top-3-Sammlung matchen
    ueber die Basis-ID; objekt-Identitaeten ausgenommen). Faellt still auf {} zurueck."""
    m = {}
    for d in unbekanntpool._cluster_lesen(cfg["data_dir"]):
        if d.get("objekt") or d.get("status", "aktiv") != "aktiv":
            continue          # Review .55: archivierte stehen auf /unbekannte nicht
        u = d.get("uid") or d.get("id")
        mem = d.get("members")
        for g in (mem if isinstance(mem, list) else []):
            m.setdefault(g, u)
            m.setdefault(str(g).split("~")[0], u)
    return m


def _unbek_zeile(s, eid2uid):
    """Unbekannt-Angabe eines Durchgangs (Review .55): In Durchgaengen MIT bestaetigter
    Person bewusst NUR die stumme Zaehlung (User-Entscheid 25.07.: das sind meist
    dieselben Leute, schlecht getroffen — eine U-Nummer behauptete dort eine zweite
    Identitaet). U-Nummern nur fuer Durchgaenge OHNE Bestaetigung, verlinkt mit Anker
    auf die Kachel; archivierte Identitaeten liefert _eid2uid nicht mehr."""
    if not s.get("unbek"):
        return ""
    if s.get("pers"):
        n = s["unbek"]
        return f'+{n} not matched (usually the same people)'
    uids, ohne = [], 0
    for e in s.get("unbek_eids") or []:
        u = eid2uid.get(str(e or "").replace("/", "_")) or eid2uid.get(str(e or ""))
        if u:
            if u not in uids:
                uids.append(u)
        else:
            ohne += 1
    teile = [f'<a href="/unbekannte#uk-{urllib.parse.quote(str(u))}">'
             f'Unknown {html.escape(str(u).lstrip("U"))}</a>' for u in uids]
    if ohne or not teile:
        n = ohne if teile else s["unbek"]
        teile.append(f'{n} {"event" if n == 1 else "events"} with an unmatched face')
    return " · ".join(teile)


def render_unbekannt(cfg, log_pfad, personen_bekannt, params):
    """.239 (User-Zielbild, dritte und richtige Fassung: 'ich dachte, ich sehe
    die Bilder vom Lauf 12:19 und kann diese dann zuweisen'): die Today-Karte
    eines Unbekannten IST ein Lauf — diese Seite zeigt GENAU diesen einen
    Durchgang (Personen-Karten-Layout: grosses Bild, Kamerafolge, Video) und
    darueber die Zuweisung NUR mit den Gesichtern dieses Laufs, egal in
    welchem internen Gruppchen sie gelandet sind. Kein Identitaets-Dossier
    (das lebt auf /unbekannte), keine Cluster-Zusammenfuehrung ueber Tage —
    die hatte am Echtbestand verschiedene Personen gemischt."""
    import webui
    uid = (params.get("u", [""])[0] or "").strip()
    tag_par = (params.get("tag", [""])[0] or "").strip()
    try:
        p_start = float(params.get("p", [""])[0])
    except (TypeError, ValueError):
        p_start = None
    try:
        tag_dt = datetime.datetime.strptime(tag_par, "%Y-%m-%d")
    except ValueError:
        tag_dt = None
    zurueck_url = f"/heute?tag={tag_par}" if tag_par else "/heute"
    zurueck = (f'<div class="tagnav"><a class="gtb" href="{zurueck_url}">'
               '&#8592; Today</a></div>')
    if tag_dt is None or p_start is None:
        return "Unknown", zurueck + webui.leer(
            "This link is missing its walk-through.",
            'Open the visitor from a day card on Today, or see '
            '<a href="/unbekannte">Unknown</a> for the full profiles.')
    # Den EINEN Durchgang des Tages finden (Toleranz: die Karte gibt den
    # exakten Start mit; 120 s fangen Rundungs-/Neurechnungs-Drift).
    rows = _lade_rows(log_pfad)
    by_h = {r["eid"]: r for r in rows if r.get("eid")}
    gtmap = _lade_gtmap(cfg)
    _km, _ka = _koerper(cfg)
    t0 = tag_dt.timestamp()
    szen = _szen.szenarien_des_tages(by_h, t0, t0 + 86400, cfg, gtmap,
                                     koerper_map=_km, koerper_ab=_ka)
    s = min((x for x in szen), key=lambda x: abs(x["start"] - p_start),
            default=None)
    if s is None or abs(s["start"] - p_start) > 120:
        return "Unknown", zurueck + webui.leer(
            "This walk-through is no longer in the day view.",
            "The day may have been re-grouped — open it again from Today.")
    evs = s.get("evs") or []
    pass_eids = {str(e.get("eid")) for e in evs if e.get("eid")}
    # ALLE unbekannten Gesichter DIESES Laufs, quer ueber die Gruppchen.
    member, uids = [], []
    for d in unbekanntpool._cluster_lesen(cfg["data_dir"]):
        if d.get("status", "aktiv") != "aktiv" or d.get("objekt"):
            continue
        traf = False
        for m in (d.get("members") or []):
            if str(m).split("~")[0] in pass_eids and str(m) not in member:
                member.append(str(m))
                traf = True
        if traf:
            uids.append(str(d.get("uid") or d.get("id")))
    nummer = html.escape(uid.lstrip("U"))
    weitere = max(0, len(uids) - 1)
    if not member:
        return f"Unknown {nummer}", zurueck + webui.leer(
            "No collected faces for this walk-through.",
            "The pool may have been cleaned up in the meantime.")
    # Lauf-Karte im Personen-Layout.
    folge, gesehen = [], set()
    for e in evs:
        if e["cam"] not in gesehen:
            gesehen.add(e["cam"])
            folge.append(f'{html.escape(e["cam"])} {_hhmm(e["t"])}')
    _best = sorted(member)[0]
    held = (f'<a class="pass-bild" href="/event/'
            f'{urllib.parse.quote(_best.split("~")[0])}">'
            f'<img src="/anlern/crops/{urllib.parse.quote(_best)}.jpg" '
            f'alt=""></a>')
    video = (f' <a class="gtb pass-knopf" href="/video/'
             f'{urllib.parse.quote(str(evs[0].get("eid")))}">'
             f'<span class="pk-icon">&#9654;</span>video</a>'
             if evs and evs[0].get("eid") else "")
    thumbs = "".join(
        f'<a class="pass-thumb" href="/event/'
        f'{urllib.parse.quote(str(m.split("~")[0]))}">'
        f'<img src="/anlern/crops/{urllib.parse.quote(m)}.jpg" alt="">'
        f'<small>{_hhmm(float(m.split(".")[0]))}</small></a>'
        for m in sorted(member))
    lauf_karte = (
        f'<div class="card pass-card"><div class="pass-kopf">'
        f'<b>{tag_dt.strftime("%A, %d %B %Y")}</b>'
        f' · {_hhmm(s["start"])} &ndash; {_hhmm(s["ende"])}'
        f' · {len(member)} face{"s" if len(member) != 1 else ""}'
        f' · {len(s["kams"])} camera{"s" if len(s["kams"]) != 1 else ""}</div>'
        f'<div class="pass-body">{held}<div class="pass-info">'
        f'<div class="pass-folge">{" &rarr; ".join(folge)}</div>'
        f'<div class="pass-links">{video}</div></div></div>'
        f'<div class="pass-thumbs">{thumbs}</div></div>')
    opts = "".join(f'<option value="{html.escape(p)}">' for p in personen_bekannt)
    wahl = "".join(
        f'<label class="ubw"><input type="checkbox" name="ub-sel" '
        f'value="{html.escape(m)}">'
        f'<img src="/anlern/crops/{urllib.parse.quote(m)}.jpg" alt=""></label>'
        for m in sorted(member))
    kopf = (
        zurueck
        + f'<h2>Unknown {nummer}'
        + (f' <span class="dim" style="font-size:15px">+{weitere} more in '
           'this walk</span>' if weitere else "") + "</h2>"
        f'<div class="dim" style="margin:0 0 10px">one walk-through · '
        f'{tag_dt.strftime("%d.%m.")} {_hhmm(s["start"])} · full profile on '
        f'<a href="/unbekannte#uk-{urllib.parse.quote(uid)}">Unknown</a></div>'
        '<div class="card"><b>Who is this?</b>'
        '<div class="dim" style="margin:4px 0 8px">These are the faces from '
        'THIS walk-through. Tick the ones that really belong to the person '
        '&mdash; junk stays behind. Give them a name (new or existing) and '
        'they are learned; doing nothing keeps them unknown.</div>'
        f'<div class="ub-wahl">{wahl}</div>'
        '<div class="bn-leiste">'
        '<button type="button" class="gtb" onclick="ubAlle(true)">Select all</button>'
        '<button type="button" class="gtb" onclick="ubAlle(false)">None</button>'
        '<input list="ub-personen" id="ub-name" '
        'placeholder="person (new or existing)">'
        f'<datalist id="ub-personen">{opts}</datalist>'
        '<button type="button" class="gtb on" onclick="ubZuweisen(this)">'
        'Add selected faces</button>'
        '<span class="dim" id="ub-status"></span></div></div>')
    js = ('<script>'
          'function ubAlle(an){document.querySelectorAll("input[name=ub-sel]")'
          '.forEach(function(c){c.checked=an;});}'
          'function ubZuweisen(b){var ids=[];'
          'document.querySelectorAll("input[name=ub-sel]:checked")'
          '.forEach(function(c){ids.push(c.value);});'
          'var person=(document.getElementById("ub-name").value||"").trim();'
          'var st=document.getElementById("ub-status");'
          'if(!ids.length){st.textContent="tick at least one face";return;}'
          'if(!person){st.textContent="enter a person name";return;}'
          'b.disabled=true;st.textContent="learning\u2026";'
          'fetch("/anlernen_benennen",{method:"POST",'
          'body:JSON.stringify({ids:ids.join(","),person:person})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'st.textContent=d.msg;'
          f'if(d.ok)setTimeout(function(){{location="{zurueck_url}"}},1400);'
          'else b.disabled=false;})'
          '.catch(function(){st.textContent="error";b.disabled=false;});}'
          '</script>')
    return (f"Unknown {nummer} — walk-through",
            kopf + lauf_karte + js)


def render(cfg, log_pfad, personen_bekannt, params):
    """-> (titel, inhalt_html). params = parsed query dict (Listen je Key, wie qs im Handler)."""
    import webui
    person = (params.get("person", [""])[0] or "").strip()
    heute_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tag_par = params.get("tag", [""])[0]
    tag_dt = heute_dt
    if tag_par:
        try:                                   # dasselbe robuste Muster wie /heute (9999-12-31-Falle)
            t = datetime.datetime.strptime(tag_par, "%Y-%m-%d")
            heute0, tag_ende = t.timestamp(), (t + datetime.timedelta(days=1)).timestamp()
            tag_dt = t
        except (ValueError, OverflowError, OSError):
            tag_par = ""
    if not tag_par:
        heute0 = tag_dt.timestamp()
        tag_ende = (tag_dt + datetime.timedelta(days=1)).timestamp()
    ist_heute = tag_dt.date() == heute_dt.date()
    tag_str = tag_dt.strftime("%Y-%m-%d")

    rows = _lade_rows(log_pfad) if person else []
    # Person gilt, wenn sie im Master steht ODER im Log je bestaetigt wurde — sonst
    # laufen /heute-Karten alter Tage nach einer Personen-Loeschung in eine Sackgasse
    # (Review .50): die Karten kommen aus dem Log, nicht aus dem Master.
    bekannt = person and (person in personen_bekannt or
                          any(person in (r.get("bestaetigt") or []) for r in rows))
    if not bekannt:
        inhalt = webui.leer("Unknown person.", "Pick a person on the Today page.")
        return "Appearances", f'<div class="tagnav"><a class="gtb" href="/heute">&#8592; Today</a></div>' + inhalt

    by_h = {}
    for r in rows:
        if r.get("eid"):
            by_h[r["eid"]] = r
    gtmap = _lade_gtmap(cfg)         # F2 (.54): eid -> letztes Label (wie /heute)
    # Areas Stufe 1 v2: die Sicht WAEHLT Paesse aus (beruehrt die Area), Urteil und
    # Zahlen bleiben property-weit; Chip-Leiste unterm Kopf rendert nur mit Areas.
    areas_cfg = _areas_mod.normalisieren(cfg.get("areas"))
    ar_aktiv, nur = _areas_mod.sicht_aufloesen(
        areas_cfg, params.get("area", [""])[0],
        {str(r.get("camera", "?")) for r in by_h.values()})
    aq = f'&amp;area={urllib.parse.quote(ar_aktiv)}' if nur is not None else ''
    _km, _ka = _koerper(cfg)
    szen = _szen.szenarien_des_tages(by_h, heute0, tag_ende, cfg, gtmap, nur_kameras=nur,
                                 koerper_map=_km, koerper_ab=_ka)
    paesse = [s for s in szen if person in s["pers"]]
    paesse.sort(key=lambda s: s["start"])                     # Pass 1 = fruehester

    heute_link = ("/heute" if ist_heute else f"/heute?tag={tag_str}") \
        + (aq.replace("&amp;", "?", 1) if (nur is not None and ist_heute) else aq)
    vortag = (tag_dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    folgetag = (tag_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    pq = urllib.parse.quote(person)
    fest = {"person": person} if ist_heute else {"person": person, "tag": tag_str}
    kopf = (f'<div class="tagnav">'
            f'<a class="gtb" href="{heute_link}" title="back to the day">&#8592; Today</a>'
            f'<a class="gtb" href="/auftritte?person={pq}&amp;tag={vortag}{aq}" title="previous day">&#8592;</a>'
            f'<div class="tagnav-mitte"><div class="tagnav-t">{html.escape(person)} — '
            f'{tag_dt.strftime("%A, %d %B %Y")}</div>'
            f'<div class="tagnav-u">{len(paesse)} {"pass" if len(paesse) == 1 else "passes"}</div></div>'
            + (f'<span class="gtb" aria-disabled="true" title="no future days">&#8594;</span>' if ist_heute else
               f'<a class="gtb" href="/auftritte?person={pq}&amp;tag={folgetag}{aq}" title="next day">&#8594;</a>')
            + '</div>' + _r_areas.chips(areas_cfg, ar_aktiv, "/auftritte", fest))

    if not paesse:
        return (f"{person} — Appearances",
                kopf + webui.leer(f"No confirmed passes of {person} on this day.",
                                  "Use the day arrows to look around."))

    e2u = _eid2uid(cfg)              # Haeppchen 2: U-Nummern in der Unbekannt-Angabe
    ref_eids = _ref_eids(cfg, person)   # .227: Referenz-Marker je Thumb
    bloecke = []
    for i, s in enumerate(paesse, 1):
        d = s["pers"][person]
        evs = s.get("evs") or []
        # Kamerafolge: je Kamera die ERSTE Eventzeit, Reihenfolge = Zeitreihenfolge des
        # DURCHGANGS; Kameras mit Bestaetigung DIESER Person fett (Review .50: sonst las
        # sich die Folge als Personenweg ueber Kameras, auf denen sie nie bestaetigt war).
        bestaetigt_kams = {e["cam"] for e in evs if person in (e.get("conf") or [])}
        folge, gesehen = [], set()
        for e in evs:
            if e["cam"] not in gesehen:
                gesehen.add(e["cam"])
                teil = f'{html.escape(e["cam"])} {_hhmm(e["t"])}'
                folge.append(f'<b>{teil}</b>' if e["cam"] in bestaetigt_kams else teil)
        andere = [p for p in s["pers"] if p != person]
        dabei = ", ".join(html.escape(p) for p in andere)
        best_url = _crop_url(cfg, d.get("eid"), person)
        bild = (f'<a class="pass-bild" href="/event/{urllib.parse.quote(str(d["eid"]))}">'
                f'<img src="{best_url}" alt=""></a>' if best_url and d.get("eid") else
                '<div class="pass-bild pass-bild-leer">no image</div>')
        # Thumbnails = NUR Events mit Gesichts-Crop der Person (User 27.07.: Entwicklung
        # des Gesichts ueber den Durchgang zeigen; Uhrzeit-Kacheln ohne Gesicht raus).
        # Unbestaetigte Treffer (Crop da, Event nicht bestaetigt) gedimmt + benannt.
        thumbs, ohne_gesicht = [], 0
        for e in evs:
            tu = _crop_url(cfg, e.get("eid"), person)
            if not tu:
                ohne_gesicht += 1
                continue
            schwach = person not in (e.get("conf") or [])
            kl = "pass-thumb pass-thumb-schwach" if schwach else "pass-thumb"
            # .227: Referenz-Marker direkt am Bild — gruen umrandet heisst
            # "dieses Event hat eine aktive Referenz geliefert".
            ist_ref = e.get("eid") in ref_eids
            if ist_ref:
                kl += " pass-thumb-ref"
            tt = f'{html.escape(e["cam"])} {_hhmm(e["t"])}' + (" — not confirmed here" if schwach else "") \
                + (" — in the references" if ist_ref else "")
            thumbs.append(f'<a class="{kl}" title="{tt}" '
                          f'href="/event/{urllib.parse.quote(str(e.get("eid") or ""))}">'
                          f'<img src="{tu}" alt=""><small>{_hhmm(e["t"])}</small></a>')
        if ohne_gesicht:
            thumbs.append(f'<span class="pass-thumbs-rest">+{ohne_gesicht} '
                          f'{"event" if ohne_gesicht == 1 else "events"} without a face</span>')
        # .229 (User: "so dass der User weiss, die sind schon uebernommen"):
        # die Bedeutung des gruenen Rands steht AN der Reihe, nicht nur im
        # Tooltip — aber nur, wenn die Reihe markierte Bilder traegt.
        if any(e.get("eid") in ref_eids for e in evs):
            thumbs.append('<span class="pass-thumbs-rest">green border = '
                          'already in the references</span>')
        # best match: Kamera/Zeit des BEST-Events (d["eid"]), nicht der letzten
        # Bestaetigung (Review .50 — das waren zwei verschiedene Events).
        be = next((e for e in evs if e.get("eid") and e.get("eid") == d.get("eid")), None)
        best_ort = f' ({html.escape(be["cam"])}, {_hhmm(be["t"])})' if be else ''
        # "—" statt "0.00": eine per Anlern-Korrektur bestaetigte Person hat bewusst
        # KEINEN ours-Score (Widerleger 11.08.) — 0.00 saehe nach schlechtester
        # Messung aus, dabei gab es schlicht keine Live-Messung.
        bm = f'{d["best"]:.2f}' if d["best"] else "—"
        bestz = (f'confirmed at {_hhmm(d["erst_t"])}' if _hhmm(d["erst_t"]) == _hhmm(d["letzt_t"]) else
                 f'confirmed {_hhmm(d["erst_t"])} &ndash; {_hhmm(d["letzt_t"])}')
        live = (' <span class="badge live"><span class="ldot"></span>in progress</span>'
                if s.get("laeuft") else '')
        # .233 (User: "bekommst du die Buttons schicker hin? auch mit kleinem
        # Icon?"): einheitliche pass-knopf-Optik + Emoji-Ikonografie wie auf
        # den Kachel-Seiten (Video behaelt sein Play, der Check bekommt die
        # Lupe; das Haekchen nach der Uebernahme setzt das JS).
        video = (f' <a class="gtb pass-knopf" href="/video/{urllib.parse.quote(str(d["eid"]))}">'
                 f'<span class="pk-icon">&#9654;</span>video</a>'
                 if d.get("eid") else '')
        # .225 Lern-Bruecke (User-Ablauf abgenommen): EIN Knopf je Pass — das
        # System siebt selbst (anlernen.lernbruecke, nur 'empfohlen'), die
        # Antwort kommt inline, Undo statt Dialog. Gesendet werden ALLE
        # Pass-Events: das Identitaets-Sieb prueft jedes Bild einzeln gegen
        # die Referenzen, eine fremde Person kann konstruktionsbedingt nicht
        # uebernommen werden.
        _eids = html.escape(json.dumps(
            [str(e.get("eid")) for e in evs if e.get("eid")]), quote=True)
        lern = (f' <button class="gtb pass-knopf" data-person="{html.escape(person, quote=True)}" '
                f'data-eids="{_eids}" onclick="lernBruecke(this)">'
                f'<span class="pk-icon">&#128269;</span>'
                f'Check this pass for good pictures &#8230;</button>'
                '<span class="dim lb-status" style="margin-left:8px"></span>')
        bloecke.append(
            f'<div class="card pass-card"><div class="pass-kopf"><b>Pass {i}</b>'
            f' · {_hhmm(s["start"])} &ndash; {_hhmm(s["ende"])}'
            f' · {s["n"]} {"event" if s["n"] == 1 else "events"}'
            f' · {len(s["kams"])} {"camera" if len(s["kams"]) == 1 else "cameras"}{live}</div>'
            f'<div class="pass-body">{bild}<div class="pass-info">'
            f'<div class="pass-folge">{" &rarr; ".join(folge)}</div>'
            f'<div class="dim">{bestz} · best match {bm}{best_ort}</div>'
            + (f'<div class="dim">also in this pass: {dabei}</div>' if dabei else '')
            + (f'<div class="dim">{_unbek_zeile(s, e2u)}</div>'
               if s.get("unbek") else '')
            + f'<div class="pass-links">{video}{lern}</div></div></div>'
            f'<div class="pass-thumbs">{"".join(thumbs)}</div></div>')

    # .226 (User-Feedback am .225-Knopf, dritte Fassung): Pruefen oeffnet ein
    # In-Page-OVERLAY mit genau den Bildern, die uebernommen wuerden — jedes
    # abwaehlbar, dann OK oder Cancel (KEIN window.open: Browser-Popup-Blocker
    # koennen eigenes Seiten-HTML nicht blocken, User-Fallen-Sorge). Nach
    # der Uebernahme bleibt Undo.
    js = ('<script>'
          'function lbStart(b){b.disabled=false;'
          'b.innerHTML="<span class=\\"pk-icon\\">\\uD83D\\uDD0D</span>'
          'Check this pass for good pictures \\u2026";}'
          'function lbUebernehmen(b,st,items){'
          'st.textContent="adopting\\u2026";b.disabled=true;'
          'fetch("/auftritt_lernen",{method:"POST",'
          'headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({person:b.dataset.person,uebernehmen:items})})'
          '.then(function(r){return r.json()}).then(function(d2){'
          'if(!d2.ok){st.textContent="error: "+d2.msg;lbStart(b);return;}'
          'st.textContent=d2.msg;'
          'b.innerHTML="<span class=\\"pk-icon\\">\\u2713</span>"+d2.n+" added";'
          # .227: die uebernommenen Bilder SOFORT gruen markieren (ohne Reload)
          'var kk=b.closest(".pass-card");'
          'if(kk)items.forEach(function(it){'
          'var t=kk.querySelector(".pass-thumb[href*=\\""+it.eid+"\\"]");'
          'if(t)t.classList.add("pass-thumb-ref");});'
          'var u=document.createElement("a");u.textContent="Undo";u.href="#";'
          'u.style.marginLeft="8px";'
          'u.onclick=function(ev){ev.preventDefault();st.textContent="removing\\u2026";'
          'fetch("/auftritt_lernen_undo",{method:"POST",'
          'headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({person:b.dataset.person,dateien:d2.dateien})})'
          '.then(function(r){return r.json()}).then(function(d3){'
          'st.textContent=d3.msg;u.remove();'
          # Nur die EBEN uebernommenen Marker zuruecknehmen — aeltere
          # Referenzen desselben Passes behalten ihre Umrandung.
          'var ku=b.closest(".pass-card");'
          'if(ku)items.forEach(function(it){'
          'var t=ku.querySelector(".pass-thumb[href*=\\""+it.eid+"\\"]");'
          'if(t)t.classList.remove("pass-thumb-ref");});'
          'lbStart(b);});};'
          'b.parentNode.insertBefore(u,st);})'
          '.catch(function(e){st.textContent="error: "+e;lbStart(b);});}'
          'function lbOverlay(b,st,d){'
          'var ov=document.createElement("div");ov.className="lb-overlay";'
          'var dg=document.createElement("div");dg.className="lb-dialog";'
          'var np=d.nehmen.length,ng=(d.grenz||[]).length;'
          'dg.innerHTML="<h3 style=\\"margin:0 0 4px\\">Take these pictures for "'
          '+b.dataset.person+"?</h3><div class=\\"dim\\">"+'
          '(np?"The check picked "+np+" picture(s) \\u2014 untick any you do '
          'not trust.":"The check found no clearly helpful picture.")+"</div>";'
          'function reihe(items,checked){var w=document.createElement("div");'
          'w.className="lb-wahl";items.forEach(function(it){'
          'var l=document.createElement("label"),c=document.createElement("input");'
          'c.type="checkbox";c.checked=checked;c._it=it;'
          'var im=document.createElement("img");im.src=it.url;im.loading="lazy";'
          'l.appendChild(c);l.appendChild(im);w.appendChild(l);});return w;}'
          'var wahl=reihe(d.nehmen,true);dg.appendChild(wahl);'
          # .231: Grenzfaelle sichtbar, aber OHNE Haken — bewusste Zuwahl.
          'var wahl2=null;'
          'if(ng){var gh=document.createElement("div");gh.className="dim";'
          'gh.style.marginTop="6px";'
          'gh.textContent=ng+" borderline picture(s) \\u2014 identity sure, '
          'picture quality only fair; tick to take anyway:";'
          'dg.appendChild(gh);wahl2=reihe(d.grenz,false);dg.appendChild(wahl2);}'
          'var ok=document.createElement("button");ok.className="gtb on";'
          'var ab=document.createElement("button");ab.className="gtb";'
          'ab.textContent="Cancel";ab.style.marginLeft="8px";'
          'function boxenAlle(){var a=Array.from(wahl.querySelectorAll("input"));'
          'if(wahl2)a=a.concat(Array.from(wahl2.querySelectorAll("input")));return a;}'
          'function zaehl(){var n=boxenAlle().filter(function(c){return c.checked}).length;'
          'ok.textContent="Take "+n+" picture(s)";ok.disabled=!n;return n;}'
          'wahl.addEventListener("change",zaehl);'
          'if(wahl2)wahl2.addEventListener("change",zaehl);zaehl();'
          'ok.onclick=function(){var items=[];'
          'boxenAlle().forEach(function(c){if(c.checked)'
          'items.push({eid:c._it.eid,datei:c._it.datei});});'
          'ov.remove();lbUebernehmen(b,st,items);};'
          'ab.onclick=function(){ov.remove();st.textContent="nothing taken";'
          'lbStart(b);};'
          'dg.appendChild(ok);dg.appendChild(ab);ov.appendChild(dg);'
          'ov.onclick=function(ev){if(ev.target===ov)ab.onclick(ev);};'
          'document.body.appendChild(ov);}'
          'function lernBruecke(b){'
          'var st=b.parentNode.querySelector(".lb-status");'
          'b.disabled=true;st.textContent="checking the pictures\\u2026";'
          'fetch("/auftritt_lernen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({person:b.dataset.person,eids:JSON.parse(b.dataset.eids)})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'if(!d.ok){st.textContent="error: "+d.msg;b.disabled=false;return;}'
          # .232 (User-Idee): kaltes Modell -> ehrliche Lade-Anzeige und
          # automatisch nachfragen, sobald es steht (max ~1 min).
          'if(d.laden){st.textContent=d.msg;'
          'b._ladeversuche=(b._ladeversuche||0)+1;'
          'if(b._ladeversuche>24){st.textContent="model did not load — try again";'
          'b.disabled=false;b._ladeversuche=0;return;}'
          'setTimeout(function(){lernBruecke(b)},2500);return;}'
          'b._ladeversuche=0;'
          'st.textContent=d.msg;b.disabled=false;'
          # .231: Overlay auch, wenn NUR Grenzfaelle da sind.
          'if((d.nehmen&&d.nehmen.length)||(d.grenz&&d.grenz.length))'
          'lbOverlay(b,st,d);})'
          '.catch(function(e){st.textContent="error: "+e;b.disabled=false;});}'
          '</script>')
    return f"{person} — Appearances", kopf + "".join(bloecke) + js


def render_pass(cfg, log_pfad, personen_bekannt, eid):
    """/pass/<eid> (Haeppchen 2): die Durchgangs-Seite — erreichbar ueber JEDE Mitglieds-
    Event-ID, Regruppierung beim Aufruf (Szenario-Prinzip als eigene Adresse: der
    Durchgang hat keine persistente ID, seine Events schon). -> (titel, inhalt_html)."""
    import webui
    eid = (eid or "").strip()
    rows = _lade_rows(log_pfad)
    zeile = None
    for r in rows:
        if r.get("eid") == eid:
            zeile = r                                     # letzte Zeile gewinnt
    if not zeile:
        return "Pass", ('<div class="tagnav"><a class="gtb" href="/heute">&#8592; Today</a></div>'
                        + webui.leer("Event not found.", "It may have aged out of the log."))
    t0 = zeile.get("start") or zeile.get("ts") or 0
    tag_dt = datetime.datetime.fromtimestamp(t0).replace(hour=0, minute=0, second=0, microsecond=0)
    heute0 = tag_dt.timestamp()
    tag_ende = (tag_dt + datetime.timedelta(days=1)).timestamp()
    ist_heute = tag_dt.date() == datetime.date.today()
    tag_str = tag_dt.strftime("%Y-%m-%d")
    by_h = {}
    for r in rows:
        if r.get("eid"):
            by_h[r["eid"]] = r
    _km, _ka = _koerper(cfg)
    szen = _szen.szenarien_des_tages(by_h, heute0, tag_ende, cfg, _lade_gtmap(cfg),
                                 koerper_map=_km, koerper_ab=_ka)
    szen.sort(key=lambda s: s["start"])
    idx = next((i for i, s in enumerate(szen)
                if any(e.get("eid") == eid for e in s.get("evs") or [])), None)
    if idx is None:
        return "Pass", ('<div class="tagnav"><a class="gtb" href="/heute">&#8592; Today</a></div>'
                        + webui.leer("This event is not part of a grouped pass.",
                                     "Grouping needs the day view context."))
    s = szen[idx]
    evs = s.get("evs") or []
    e2u = _eid2uid(cfg)

    def _pass_link(s2, txt, titel):
        ziel = next((e.get("eid") for e in s2.get("evs") or [] if e.get("eid")), None)
        if not ziel:
            return f'<span class="gtb" aria-disabled="true">{txt}</span>'
        return f'<a class="gtb" href="/pass/{urllib.parse.quote(str(ziel))}" title="{titel}">{txt}</a>'

    heute_link = "/heute" if ist_heute else f"/heute?tag={tag_str}"
    kopf = (f'<div class="tagnav">'
            f'<a class="gtb" href="{heute_link}" title="back to the day">&#8592; Day</a>'
            + (_pass_link(szen[idx - 1], "&#8592;", "previous pass of the day") if idx > 0
               else '<span class="gtb" aria-disabled="true">&#8592;</span>')
            + f'<div class="tagnav-mitte"><div class="tagnav-t">Pass {_hhmm(s["start"])}'
              f' &ndash; {_hhmm(s["ende"])} — {tag_dt.strftime("%A, %d %B %Y")}</div>'
              f'<div class="tagnav-u">{s["n"]} {"event" if s["n"] == 1 else "events"} · '
              f'{len(s["kams"])} {"camera" if len(s["kams"]) == 1 else "cameras"}</div></div>'
            + (_pass_link(szen[idx + 1], "&#8594;", "next pass of the day") if idx + 1 < len(szen)
               else '<span class="gtb" aria-disabled="true">&#8594;</span>')
            + '</div>')

    # Personen-Zeilen: je bestaetigter Person Spanne, best match (Ort aus dem Best-Event)
    # und der Link in ihre Tagessicht.
    pzeilen = []
    for p, d in sorted(s["pers"].items(), key=lambda x: x[1]["erst_t"]):
        be = next((e for e in evs if e.get("eid") and e.get("eid") == d.get("eid")), None)
        ort = f' ({html.escape(be["cam"])}, {_hhmm(be["t"])})' if be else ''
        spanne = (f'at {_hhmm(d["erst_t"])}' if _hhmm(d["erst_t"]) == _hhmm(d["letzt_t"])
                  else f'{_hhmm(d["erst_t"])} &ndash; {_hhmm(d["letzt_t"])}')
        bm = f'{d["best"]:.2f}' if d["best"] else "—"   # s. Pass-Karte: Korrektur-Personen ohne Live-Score
        pzeilen.append(
            f'<div class="evrow"><span class="lab">'
            f'<a href="/auftritte?person={urllib.parse.quote(p)}&amp;tag={tag_str}">{html.escape(p)}</a></span>'
            f'<span>confirmed {spanne} · best match {bm}{ort}</span></div>')
    if s.get("unbek"):
        pzeilen.append(f'<div class="evrow"><span class="lab">Unmatched</span>'
                       f'<span>{_unbek_zeile(s, e2u)}</span></div>')
    if s.get("gt_fremd"):
        pzeilen.append('<div class="evrow"><span class="lab">Label</span>'
                       '<span class="badge-gtfremd">confirmed stranger</span></div>')

    # Task #9 (Tokn59 Issue #9, 31.07.): Fehler-Events erklaeren sich auf der Pass-Seite
    # selbst. Seit .173 liest die Zeile die EINE Quelle webui.bausteine.fehler_grund
    # (Widerleger 11.08.: die alte lokale verifyd:-Zeilensuche traf an 0 von 3 echten
    # Fehler-Events die Ursache — die letzte verifyd-Zeile ist die Telemetrie).
    from webui.bausteine import fehler_grund as _fg
    for e in evs:
        r = by_h.get(e.get("eid") or "")
        if not r or r.get("kategorie") != "fehler":
            continue
        lp = os.path.join(cfg["data_dir"], "events",
                          str(e.get("eid") or "").replace("/", "_"), "analyze.log")
        grund = _fg(lp)
        if not grund:                        # ehrlich unterscheiden (Widerleger-Recheck):
            grund = ("analyze.log holds no reason line — open the event for the full log"
                     if os.path.isfile(lp) else
                     "no analyze.log kept for this event — see the service log")
        pzeilen.append(
            f'<div class="evrow"><span class="lab">Error</span>'
            f'<span>{html.escape(e["cam"])} {_hhmm(e["t"])}: '
            f'{html.escape(grund)}'
            f'</span></div>')

    # Kamerafolge (fett = irgendeine Bestaetigung auf der Kamera)
    conf_kams = {e["cam"] for e in evs if e.get("conf")}
    folge, gesehen = [], set()
    for e in evs:
        if e["cam"] not in gesehen:
            gesehen.add(e["cam"])
            teil = f'{html.escape(e["cam"])} {_hhmm(e["t"])}'
            folge.append(f'<b>{teil}</b>' if e["cam"] in conf_kams else teil)

    # Beleg-Streifen: ALLE Events des Durchgangs (das hier ist die Beweis-Sicht, anders
    # als die Personen-Sicht) — Bild wenn eine der Durchgangs-Personen dort einen Crop
    # hat, sonst Kamera+Zeit-Kachel; alles verlinkt aufs Event.
    thumbs = []
    for e in evs:
        tu = None
        for p in list(e.get("conf") or []) + list(s["pers"].keys()):
            tu = _crop_url(cfg, e.get("eid"), p)
            if tu:
                break
        inner = (f'<img src="{tu}" alt="">' if tu
                 else f'<span>{html.escape(e["cam"][:6])}</span>')
        thumbs.append(f'<a class="pass-thumb" title="{html.escape(e["cam"])} {_hhmm(e["t"])}" '
                      f'href="/event/{urllib.parse.quote(str(e.get("eid") or ""))}">{inner}'
                      f'<small>{_hhmm(e["t"])}</small></a>')

    live = (' <span class="badge live"><span class="ldot"></span>in progress</span>'
            if s.get("laeuft") else '')
    inhalt = (kopf
              + f'<div class="card pass-card"><div class="pass-kopf"><b>Who</b>{live}</div>'
              + "".join(pzeilen)
              + f'<div class="pass-folge" style="margin-top:8px">{" &rarr; ".join(folge)}</div>'
              + f'<div class="pass-thumbs">{"".join(thumbs)}</div></div>')
    return f"Pass {_hhmm(s['start'])} — {tag_str}", inhalt
