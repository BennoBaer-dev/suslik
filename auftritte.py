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
    try:
        with open(os.path.join(cfg["data_dir"], "learn", "unbekannte.jsonl")) as f:
            for l in f:
                try:
                    d = json.loads(l)
                except Exception:
                    continue
                if d.get("objekt") or d.get("status", "aktiv") != "aktiv":
                    continue          # Review .55: archivierte stehen auf /unbekannte nicht
                u = d.get("uid") or d.get("id")
                for g in d.get("members") or []:
                    m.setdefault(g, u)
                    m.setdefault(str(g).split("~")[0], u)
    except OSError:
        pass
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
            tt = f'{html.escape(e["cam"])} {_hhmm(e["t"])}' + (" — not confirmed here" if schwach else "")
            thumbs.append(f'<a class="{kl}" title="{tt}" '
                          f'href="/event/{urllib.parse.quote(str(e.get("eid") or ""))}">'
                          f'<img src="{tu}" alt=""><small>{_hhmm(e["t"])}</small></a>')
        if ohne_gesicht:
            thumbs.append(f'<span class="pass-thumbs-rest">+{ohne_gesicht} '
                          f'{"event" if ohne_gesicht == 1 else "events"} without a face</span>')
        # best match: Kamera/Zeit des BEST-Events (d["eid"]), nicht der letzten
        # Bestaetigung (Review .50 — das waren zwei verschiedene Events).
        be = next((e for e in evs if e.get("eid") and e.get("eid") == d.get("eid")), None)
        best_ort = f' ({html.escape(be["cam"])}, {_hhmm(be["t"])})' if be else ''
        bestz = (f'confirmed at {_hhmm(d["erst_t"])}' if _hhmm(d["erst_t"]) == _hhmm(d["letzt_t"]) else
                 f'confirmed {_hhmm(d["erst_t"])} &ndash; {_hhmm(d["letzt_t"])}')
        live = (' <span class="badge live"><span class="ldot"></span>in progress</span>'
                if s.get("laeuft") else '')
        video = (f' <a class="gtb" href="/video/{urllib.parse.quote(str(d["eid"]))}">&#9654; video</a>'
                 if d.get("eid") else '')
        bloecke.append(
            f'<div class="card pass-card"><div class="pass-kopf"><b>Pass {i}</b>'
            f' · {_hhmm(s["start"])} &ndash; {_hhmm(s["ende"])}'
            f' · {s["n"]} {"event" if s["n"] == 1 else "events"}'
            f' · {len(s["kams"])} {"camera" if len(s["kams"]) == 1 else "cameras"}{live}</div>'
            f'<div class="pass-body">{bild}<div class="pass-info">'
            f'<div class="pass-folge">{" &rarr; ".join(folge)}</div>'
            f'<div class="dim">{bestz} · best match {d["best"]:.2f}{best_ort}</div>'
            + (f'<div class="dim">also in this pass: {dabei}</div>' if dabei else '')
            + (f'<div class="dim">{_unbek_zeile(s, e2u)}</div>'
               if s.get("unbek") else '')
            + f'<div class="pass-links">{video}</div></div></div>'
            f'<div class="pass-thumbs">{"".join(thumbs)}</div></div>')

    return f"{person} — Appearances", kopf + "".join(bloecke)


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
        pzeilen.append(
            f'<div class="evrow"><span class="lab">'
            f'<a href="/auftritte?person={urllib.parse.quote(p)}&amp;tag={tag_str}">{html.escape(p)}</a></span>'
            f'<span>confirmed {spanne} · best match {d["best"]:.2f}{ort}</span></div>')
    if s.get("unbek"):
        pzeilen.append(f'<div class="evrow"><span class="lab">Unmatched</span>'
                       f'<span>{_unbek_zeile(s, e2u)}</span></div>')
    if s.get("gt_fremd"):
        pzeilen.append('<div class="evrow"><span class="lab">Label</span>'
                       '<span class="badge-gtfremd">confirmed stranger</span></div>')

    # Task #9 (Tokn59 Issue #9, 31.07.): Fehler-Events erklaeren sich auf der Pass-Seite
    # selbst. Der Grund stand seit jeher NUR im analyze.log des Events (verifyd:-Zeilen,
    # z.B. "analyze failed in worker: ..." / "analyze timeout ..."); hier die LETZTE
    # solche Zeile je Fehler-Event zeigen statt eines nackten "error" ohne Detail.
    for e in evs:
        r = by_h.get(e.get("eid") or "")
        if not r or r.get("kategorie") != "fehler":
            continue
        grund = ""
        lp = os.path.join(cfg["data_dir"], "events",
                          str(e.get("eid") or "").replace("/", "_"), "analyze.log")
        try:
            with open(lp, encoding="utf-8", errors="replace") as f:
                for l in f:
                    if l.startswith("verifyd"):
                        grund = l.split(":", 1)[-1].strip() if ":" in l else l.strip()
        except OSError:
            pass
        pzeilen.append(
            f'<div class="evrow"><span class="lab">Error</span>'
            f'<span>{html.escape(e["cam"])} {_hhmm(e["t"])}: '
            f'{html.escape(grund or "no analyze.log kept for this event — see the service log")}'
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
