"""routes/unbekannte — persistente Unbekannt-Identitaeten /unbekannte (User
20.07.), ME1 aus verifyd extrahiert. Daten als Parameter: die Pool-Staende laedt
der Handler ueber anlernen.lade_* und reicht sie herein — kein Pool-/Store-
Zugriff im Renderer (Muster kameras/benachrichtigungen). Sprachschicht:
unbekannte.*-Schluessel (Tranche B).

.380 Umbau "Unknown-Seite skaliert" (User-Auftrag 31.08., nach der Sicht aus
Nutzeraugen auf einem Bestand mit 95 Gruppen):
  - Die Seite baute JEDE Gruppe in EINEM Rutsch, mit sechs Crops je Kachel und
    einer Merge-Auswahlliste je Kachel, die ALLE anderen Gruppen als <option>
    trug (gemessen: 9056 options bei 95 Gruppen). Jetzt: serverseitig
    sortiert/gefiltert, SEITE_N Gruppen je Schritt, Rest ueber "mehr laden";
    jedes Bild loading="lazy".
  - Die Eimer-Struktur (Recurring / single / muted / objects) ist eine
    Filterleiste geworden — dieselben Mengen, aber eine Liste statt vier, und
    die Auswahl entscheidet der Server (FILTER/SORT unten sind die EINE Quelle
    dieser Werte, kein Streu-Literal im Handler).
  - Die Kacheln folgen dem juengeren Kachel-Bild der Lern-/Kalibrier-Seiten
    (lf-zwg-Haekchen im Bild, kal-k-Rahmen) statt des alten Looks.
  - Der Crop-Streifen traegt Haekchen: eine Gruppe ist nicht immer EINE Person,
    darum kann eine Teilmenge zugewiesen werden (der Rest bleibt im Pool —
    anlernen._unbekannt_benennen_intern mit ids).
Bewusst NICHT wieder eingebaut: das Kohaerenz-Badge je Kachel (es kostete eine
N x N-Matrix ueber alle Mitglieder in JEDEM Seitenaufruf), der Kamera-Chip in
der Liste und der paarweise Vorschlagsblock — dessen Nutzen traegt jetzt der
Filterwert "merge suggested".

GRUPPE „VERMUTLICH P“ (Bauplan analysen/bauplan_aehnlich.md Fassung 6, Stufe AE5 Punkt 1, Entscheide 19 und 20; W5 V4 bis
V6): eine Identitaet, deren Merkmal „ähnlich zu P“ zaehlt (core.aehnlich.vermutlich: Merkmal und Urteil „nicht P“
zusammen), aktiv und kein Objekt, steht nicht in der Liste, sondern ueber ihr in der Gruppe ihrer Person P, ohne
Seitenteilung, mit derselben Kachel (alle Handlungen) plus Median und Abstand und dem Knopf „nicht P“. Filter, Sortierung,
Seitenteilung, Leiste und Fortschrittsanker gelten nur fuer die Liste; die Gruppe steht auch bei leerer Liste. Eine Kachel
mit Urteil „nicht P“ traegt das Urteil mit der Ruecknahme. Ohne Merkmal und Urteil ist jede Ausgabe wie vorher.

SAMMELBECKEN „ÄHNLICH P“ (Bauplan analysen/bauplan_aehnlich.md Fassung 8, Stufe AE6 Punkt 5, Entscheide 26 und 27): steht
als erste Kachel seiner Person in der Gruppe, heisst „ähnlich P“ statt „Unbekannt N“, zeigt alle Bilder mit Haken und hat nur
zwei Handlungen, beide mit Auswahl: Zuweisen an P und „nicht P“ (_becken_kachel)."""
import datetime
import html
import urllib.parse

import webui
from core import aehnlich as _aeh
from core.lernlauf import bild_url
from core.sprache import t

# EINE Quelle der Listen-Zustaende (QS-Ebenen-Regel: fachliche Aufzaehlungen nie
# verstreut) — der Handler validiert Query/POST gegen genau diese Tupel, die
# Leiste zeichnet sich daraus, und die Gate-Stufe prueft die Deckung.
SORT = ("bilder", "neu")
FILTER = ("offen", "wieder", "heute", "vorschlag", "besucher", "objekt")
SEITE_N = 20            # Gruppen je Ladeschritt
STREIFEN_N = 12         # Crops je Kachel (Deckel; das Beste zuerst)


def bild(ref_id, mid):
    """Die Bild-Adresse eines Pool-Gesichts (E3a-2): mit ref_id das Profilbild seines Satzes
    (core.lernlauf.bild_url, Lese-Stufe d), ohne (Zeile vor dieser Version, J8) der Ausschnitt unter
    /anlern/crops/. -> URL-Pfad"""
    return bild_url(ref_id, None) if ref_id else f"/anlern/crops/{urllib.parse.quote(str(mid))}.jpg"


def _tagesbeginn(jetzt=None):
    d = datetime.datetime.fromtimestamp(jetzt) if jetzt else datetime.datetime.now()
    return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def infos(idents_roh, gesichter, mitglieder=None):
    """Die Anzeige-Sicht je Identitaet: Mitglieder mit lebendem Gesicht, Zeitspanne, bestes Bild. Kaputte Pool-Zeilen
    duerfen die Seite nie toeten (kc_phase34 R-2): nur Dicts kommen durch, Identitaeten ohne lebendes Mitglied fallen raus.
    Stufe V1c (Bauplan analysen/bauplan_verbraucher_unbekannt.md Punkt 2): mitglieder = core.unbekanntpool.mitglieder
    (vom Handler); daraus die gebundenen Saetze mit Zeit aus dem Satz, juengste zuerst vor dem Altbestand (Liste members,
    Zeit und Guete aus der Pool-Zeile). Bauplan analysen/bauplan_unbekannt_zeit.md, Stufe UZ1: ohne Zeit bleiben von und
    bis None (kein Ersatz-Null). -> Liste der Anzeige-Eintraege"""
    faces = {g["id"]: g for g in gesichter}
    aus = []
    for u in idents_roh:
        if not isinstance(u, dict):
            continue
        uid = str(u.get("uid") or u.get("id") or "")
        saetze = [m for m in (mitglieder or {}).get(uid, []) if m["satz"]]
        saetze.sort(key=lambda m: -(m["ts"] if isinstance(m["ts"], (int, float)) else 0))
        alt = [m for m in u.get("members", []) if m in faces] if isinstance(u.get("members"), list) else []
        if not (saetze or alt):
            continue
        alt.sort(key=lambda m: -faces[m].get("guete", 0))
        mids = [m["id"] for m in saetze] + alt
        tss = ([m["ts"] for m in saetze if isinstance(m["ts"], (int, float))]
               + [faces[m]["ts"] for m in alt])
        refs = {m["id"]: m["ref_id"] for m in saetze}
        refs.update({m: faces[m].get("ref_id") for m in alt})
        aus.append({"u": u, "id": str(u.get("id", "")), "mids": mids,
                    "refs": refs,
                    "von": min(tss, default=None), "bis": max(tss, default=None), "rep": mids[0],
                    "n": len(mids),
                    "objekt": bool(u.get("objekt")),
                    "status": u.get("status", "aktiv"),
                    "aehnlich": _aeh.vermutlich(u),
                    "nein": sorted(_aeh.verneint(u)),
                    "sammel": _aeh.sammel_von(u)})
    return aus


def in_gruppe(i):
    """Steht die Identitaet in der Gruppe „Vermutlich P“ statt in der Liste (Entscheid 19): Merkmal mit Urteil gelesen,
    aktiv, kein Objekt. -> bool"""
    return bool(i.get("aehnlich")) and i["status"] == "aktiv" and not i["objekt"]


def gruppen(alle):
    """Die Gruppen „Vermutlich P“ (Entscheid 19): je Person P ihre Identitaeten, das Sammelbecken „ähnlich P“ zuerst
    (Entscheid 27), dann juengste Sichtung zuerst (ohne Zeit als aelteste, UZ1), Personen nach Namen.
    -> Liste (Person, [Anzeige-Eintraege])"""
    out = {}
    for i in alle:
        if in_gruppe(i):
            out.setdefault(i["aehnlich"]["person"], []).append(i)
    return [(p, sorted(out[p], key=lambda i: (not i.get("sammel"), i["bis"] is None, -(i["bis"] or 0), -i["n"])))
            for p in sorted(out)]


def auswahl(alle, vors, sortierung="bilder", filter_="offen", jetzt=None):
    """Serverseitiges Sortieren/Filtern (der Browser bekommt nur, was er zeigt).
    vors = Vorschlagspaare (fuer den Filterwert "merge suggested"). Unbekannte
    Werte fallen auf den Standard zurueck — eine getippte URL darf keine leere
    Seite ergeben. UZ1: eine Gruppe ohne Zeit gilt in jeder Sortierung als aelteste, „new today“ nimmt sie nicht."""
    if sortierung not in SORT:
        sortierung = SORT[0]
    if filter_ not in FILTER:
        filter_ = FILTER[0]
    mit_vorschlag = {str(x) for paar in (vors or []) for x in paar}
    if filter_ == "besucher":
        aus = [i for i in alle if i["status"] == "besucher" and not i["objekt"]]
    elif filter_ == "objekt":
        aus = [i for i in alle if i["objekt"]]
    else:
        aus = [i for i in alle if i["status"] == "aktiv" and not i["objekt"] and not in_gruppe(i)]
        if filter_ == "wieder":
            aus = [i for i in aus if i["n"] >= 2]
        elif filter_ == "heute":
            grenze = _tagesbeginn(jetzt)
            aus = [i for i in aus if i["von"] is not None and i["von"] >= grenze]
        elif filter_ == "vorschlag":
            aus = [i for i in aus if i["id"] in mit_vorschlag]
    if sortierung == "neu":
        aus.sort(key=lambda i: (i["bis"] is None, -(i["bis"] or 0), -i["n"]))
    else:
        aus.sort(key=lambda i: (-i["n"], i["bis"] is None, -(i["bis"] or 0)))
    return aus


def zaehler(alle):
    """(offen, gesamt) fuer den Fortschrittsanker: offen = die aktiven
    Nicht-Objekt-Gruppen, die noch eine Entscheidung brauchen; gesamt = alle
    Gruppen mit lebender Stuetze. Beides aus DERSELBEN Liste wie die Kacheln; die Gruppe „Vermutlich P“ zaehlt nicht
    (Entscheid 19)."""
    liste = [i for i in alle if not in_gruppe(i)]
    return (sum(1 for i in liste if i["status"] == "aktiv" and not i["objekt"]),
            len(liste))


def _tag(t0, t1):
    # Datums-Hardcodes (%d.%m., B19): bleiben Code, bis die
    # Format-Schluessel-Stufe (format.datum_*) gebaut ist.
    # Bauplan analysen/bauplan_unbekannt_zeit.md, Stufe UZ1: ohne Zeit der Text, nie ein Datum.
    if t0 is None or t1 is None:
        return t("unbekannte.zeit_unbekannt")
    d0 = datetime.datetime.fromtimestamp(t0)
    d1 = datetime.datetime.fromtimestamp(t1)
    if d0.date() == d1.date():
        s = d0.strftime("%d.%m. %H:%M")
        return s if t1 - t0 < 60 else f"{s}–{d1.strftime('%H:%M')}"
    return f"{d0.strftime('%d.%m.')}–{d1.strftime('%d.%m.')}"


def _unb_name(uid_):
    # Anzeige != Kennung (§8.2): die ID ("U3", anlernen vergibt
    # U+Ziffern) bleibt intern, die Anzeige kommt als Schluessel
    # mit {nummer} — wie auftritte.unbek.name (Tranche A).
    return t("unbekannte.name", nummer=uid_[1:])


def kachel(i):
    """EINE Gruppen-Kachel. Dieselbe Funktion baut die Seite, die Nachlade-Seiten
    UND die Antwort eines Aktions-POSTs — nur so kann die Seite eine Kachel
    ersetzen statt sich neu zu laden (der alte location.reload() lud bei 95
    Gruppen alles noch einmal, inklusive aller Crops)."""
    if i.get("sammel"):
        return _becken_kachel(i)
    uid = html.escape(i["id"], quote=True)
    name = html.escape(_unb_name(i["id"]))
    haken = _haken(i, i["mids"][:STREIFEN_N])
    mehr_bilder = (f'<span class="uk-rest">{t("unbekannte.mehr_bilder", n=i["n"] - STREIFEN_N)}</span>'
                   if i["n"] > STREIFEN_N else "")
    if i["objekt"]:
        akt = (f'<button class="gtb" onclick="unbObjekt(\'{uid}\',false,this)">'
               f'{t("unbekannte.knopf_person")}</button>')
        wahl = ""
    elif i["status"] == "besucher":
        akt = (f'<button class="gtb" onclick="unbBesucher(\'{uid}\',false,this)">'
               f'{t("unbekannte.knopf_reaktivieren")}</button>')
        wahl = ""
    else:
        akt = (f'<input id="nm-{uid}" placeholder="{t("unbekannte.attr_name")}" list="pers-list">'
               f'<button class="gtb on" onclick="unbBenennen(\'{uid}\',this)">{t("unbekannte.knopf_zuweisen")}</button>'
               # Knopftexte mit ZAHL (Teil-Knopf, Bulk-Knopf, Anker, Nachlade-
               # Knopf): der Rahmen kommt aus DEMSELBEN t()-Schluessel wie
               # alles andere und steht mit seinem {…}-Platzhalter in data-txt;
               # app.js setzt nur die Zahl ein. So gibt es keine zweite
               # Textquelle im JavaScript (§8-Regel: Anzeige und Erklaerung
               # koennen nicht auseinanderlaufen).
               f'<button class="gtb uk-teil" id="teil-{uid}" hidden '
               f'data-txt="{html.escape(t("unbekannte.knopf_teil"), quote=True)}" '
               f'onclick="unbTeil(\'{uid}\',this)"></button>'
               f'<button class="gtb" onclick="unbBesucher(\'{uid}\',true,this)">{t("unbekannte.knopf_ignorieren")}</button>'
               f'<button class="gtb" onclick="unbObjekt(\'{uid}\',true,this)">{t("unbekannte.knopf_objekt")}</button>'
               + (_nein_knopf(i["id"], i["aehnlich"]["person"], True) if in_gruppe(i) else ""))
        wahl = (f'<label class="uk-wahl" title="{html.escape(t("unbekannte.attr_wahl"), quote=True)}">'
                f'<input type="checkbox" class="uk-sel" value="{uid}" onchange="unbSel()"></label>')
    return (
        f'<div class="uk" id="uk-{uid}" data-uid="{uid}">'
        f'<div class="uk-kopf">'
        f'<img class="uk-face" loading="lazy" src="{bild((i.get("refs") or {}).get(i["rep"]), i["rep"])}" alt="">'
        f'<div style="min-width:0"><div class="uk-titel">{name}</div>'
        f'<div class="uk-meta"><span class="num">{i["n"]}</span>'
        f'{t("unbekannte.meta_zeit", zeit=_tag(i["von"], i["bis"]))}</div>{_aeh_zeilen(i)}</div>'
        f'{wahl}</div>'
        f'<div class="uk-str">{haken}</div>{mehr_bilder}'
        f'<div class="uk-akt">{akt}</div><div class="uk-msg"></div></div>')


def _haken(i, mids):
    """Der Bildstreifen einer Kachel: je Bild ein Haken fuer die Teil-Auswahl. -> HTML"""
    return "".join(
        f'<label class="uk-mg"><input type="checkbox" class="uk-m" value="{html.escape(m, quote=True)}" '
        f'onchange="unbTick(this)">'
        f'<img loading="lazy" src="{bild((i.get("refs") or {}).get(m), m)}" alt=""></label>'
        for m in mids)


def _becken_kachel(i):
    """Die Kachel des Sammelbeckens „ähnlich P“ (Bauplan analysen/bauplan_aehnlich.md Entscheide 26 und 27): Titel „ähnlich
    P“, alle Bilder mit Haken und nur die zwei Handlungen mit Auswahl, Zuweisen an P und „nicht P“; kein Benennen der ganzen
    Gruppe, kein Zusammenlegen, Besucher, Objekt (der Server lehnt sie ab). -> HTML"""
    uid = html.escape(i["id"], quote=True)
    p = html.escape(i["sammel"], quote=True)
    akt = (f'<input type="hidden" id="nm-{uid}" value="{p}">'
           f'<button class="gtb on uk-teil" id="teil-{uid}" hidden '
           f'data-txt="{html.escape(t("unbekannte.knopf_teil"), quote=True)}" '
           f'onclick="unbTeil(\'{uid}\',this)"></button>'
           f'<button class="gtb uk-nein-teil" id="nein-{uid}" hidden data-person="{p}" '
           f'data-txt="{html.escape(t("heute.aehnlich.sammel_nein_teil"), quote=True)}" '
           f'onclick="unbNichtPTeil(\'{uid}\',this)"></button>')
    return (
        f'<div class="uk uk-becken" id="uk-{uid}" data-uid="{uid}">'
        f'<div class="uk-kopf">'
        f'<img class="uk-face" loading="lazy" src="{bild((i.get("refs") or {}).get(i["rep"]), i["rep"])}" alt="">'
        f'<div style="min-width:0"><div class="uk-titel">{html.escape(t("heute.aehnlich.sammel", person=i["sammel"]))}'
        f'</div><div class="uk-meta"><span class="num">{i["n"]}</span>'
        f'{t("unbekannte.meta_zeit", zeit=_tag(i["von"], i["bis"]))}</div>'
        f'<div class="uk-meta">{html.escape(t("heute.aehnlich.sammel_hinweis", person=i["sammel"]))}</div></div></div>'
        f'<div class="uk-str">{_haken(i, i["mids"])}</div>'
        f'<div class="uk-akt">{akt}</div><div class="uk-msg"></div></div>')


def _nein_knopf(uid, person, an):
    """Der Knopf „nicht P“ (an) oder die Ruecknahme des Urteils (Entscheid 20); Kennung und Person als data-Attribute, nie
    im JS-Text. -> HTML"""
    text = t("heute.aehnlich.nein", person=person) if an else t("heute.aehnlich.nein_zurueck")
    return (f'<button class="gtb" data-uid="{html.escape(uid, quote=True)}" '
            f'data-person="{html.escape(person, quote=True)}" '
            f'onclick="unbNichtP(this,{"true" if an else "false"})">{html.escape(text)}</button>')


def _aeh_zeilen(i):
    """Die Zusatzzeilen einer Kachel (Entscheide 19, 20): in der Gruppe Median und Abstand, je Urteil „nicht P“ das Urteil
    mit der Ruecknahme; ohne beides leer. -> HTML"""
    aus = ""
    if in_gruppe(i):
        m = i["aehnlich"]
        zeile = t("heute.aehnlich.ident", uid=i["id"], median=f'{m["median"]:.2f}', abstand=f'{m["abstand"]:.2f}')
        aus += f'<div class="uk-meta uk-aeh-zeile">{html.escape(zeile)}</div>'
    for p in i.get("nein") or []:
        aus += (f'<div class="uk-meta uk-nein">{html.escape(t("heute.aehnlich.nein", person=p))} '
                f'{_nein_knopf(i["id"], p, False)}</div>')
    return aus


def gruppe_html(person, karten=""):
    """Eine Gruppe „Vermutlich P“ (Entscheid 19): Kopf „probably P“ und die Kacheln; leer der Rahmen, in den die Seite eine
    Kachel nach einer Handlung einsetzt. -> HTML"""
    return (f'<div class="uk-aeh-p" data-person="{html.escape(person, quote=True)}">'
            f'<h4>{html.escape(t("heute.aehnlich.zu", person=person))}</h4>'
            f'<div class="ukliste uk-aeh-liste">{karten}</div></div>')


def _gruppen_block(alle, aeh_fehler):
    """Der Block „Probably recognized“ ueber der Liste (Entscheid 19), mit dem roten Hinweis, wenn der letzte
    Aufraeum-Schritt scheiterte (ED008); ohne Gruppe und ohne Fehler leer. -> HTML"""
    gr = gruppen(alle)
    if not gr and not aeh_fehler:
        return ""
    fehler = f'<p class="hk-aeh-fehler">{html.escape(t("heute.aehnlich.fehler"))}</p>' if aeh_fehler else ""
    return (f'<div class="uk-aeh" id="uk-gruppen"><h3>{html.escape(t("heute.aehnlich.titel"))}</h3>{fehler}'
            + "".join(gruppe_html(p, kacheln(ii)) for p, ii in gr) + '</div>')


def kacheln(liste):
    """Nur die Kacheln (Nachlade-Antwort des "mehr laden"-Knopfes)."""
    return "".join(kachel(i) for i in liste)


def _leiste(sortierung, filter_, mengen):
    """Eine Zeile: Sortierung + Filter, beides als Link (der Server entscheidet,
    die Seite kommt fertig gefiltert). Die Zahl je Filterwert steht dabei, damit
    niemand blind in einen leeren Eimer klickt."""
    def link(art, wert, text, aktiv):
        z = {"sort": sortierung, "f": filter_}
        z[art] = wert
        q = urllib.parse.urlencode(z)
        return (f'<a class="uk-f{" an" if aktiv else ""}" href="/unbekannte?{q}">'
                f'{html.escape(text)}</a>')
    # Statische Schluessel-Mappings (Sprachregel: nie dynamische t()-Schluessel
    # bauen — der Deckungs-Scanner kann f-strings nicht sehen, die Schluessel
    # galten als tot). Der assert haelt Mapping und Wertelisten deckungsgleich.
    sort_texte = {"bilder": t("unbekannte.sort_bilder"),
                  "neu": t("unbekannte.sort_neu")}
    filter_texte = {"offen": t("unbekannte.f_offen"),
                    "wieder": t("unbekannte.f_wieder"),
                    "heute": t("unbekannte.f_heute"),
                    "vorschlag": t("unbekannte.f_vorschlag"),
                    "besucher": t("unbekannte.f_besucher"),
                    "objekt": t("unbekannte.f_objekt")}
    assert set(sort_texte) == set(SORT) and set(filter_texte) == set(FILTER)
    s = "".join(link("sort", w, sort_texte[w], w == sortierung) for w in SORT)
    f = "".join(link("f", w, f"{filter_texte[w]} {mengen.get(w, 0)}", w == filter_)
                for w in FILTER)
    return (f'<div class="uk-leiste">'
            f'<span class="uk-lab">{t("unbekannte.sort_label")}</span>{s}'
            f'<span class="uk-lab">{t("unbekannte.filter_label")}</span>{f}</div>')


def render(idents_roh, gesichter, vors, personen, sortierung="bilder",
           filter_="offen", jetzt=None, mitglieder=None, aeh_fehler=False):
    """-> Seiten-INHALT (Layout/Banner bleiben beim Handler).
    idents_roh = anlernen.lade_unbekannte() (roh, der Kaputt-Zeilen-Filter
    wohnt in infos()) · gesichter = anlernen.lade_gesichter() · vors =
    anlernen.lade_unbekannt_vorschlaege() · personen = master_persons(cfg) ·
    mitglieder = core.unbekanntpool.mitglieder (Stufe V1c, gebundene Saetze) · aeh_fehler = der letzte
    Aufraeum-Schritt der Gruppe „ähnlich“ scheiterte (core.aehnlich.SPEICHER.rot)."""
    alle = infos(idents_roh, gesichter, mitglieder)
    liste = auswahl(alle, vors, sortierung, filter_, jetzt=jetzt)
    offen, gesamt = zaehler(alle)
    mengen = {w: len(auswahl(alle, vors, sortierung, w, jetzt=jetzt)) for w in FILTER}
    opts = "".join(f"<option>{html.escape(p)}</option>" for p in personen)
    kopf = (f'<h2>{t("unbekannte.titel")}</h2>'
            f'<p class="sub">{t("unbekannte.kopf_satz")} '
            f'<b>{t("unbekannte.knopf_zuweisen")}</b>{t("unbekannte.kopf_satz_zuweisen")} '
            f'<b>{t("unbekannte.knopf_ignorieren")}</b>{t("unbekannte.kopf_satz_ignorieren")} '
            f'{t("unbekannte.kopf_satz_auto")}</p>'
            # Fortschrittsanker (B7): eine Seite mit 95 Gruppen braucht eine
            # Zahl, die beim Abarbeiten runterzaehlt — sonst sieht der Nutzer
            # nach zehn Zuweisungen dieselbe endlose Liste.
            f'<p class="uk-anker" id="uk-anker" '
            f'data-txt="{html.escape(t("unbekannte.anker"), quote=True)}">'
            f'{t("unbekannte.anker", offen=offen, gesamt=gesamt)}</p>'
            f'<p><button class="gtb on" onclick="anlernWartungJetzt(this)">{t("unbekannte.knopf_reorg")}</button> '
            f'<span style="color:var(--dim);font-size:13px">{t("unbekannte.hinweis_reorg")}</span></p>'
            f'<datalist id="pers-list">{opts}</datalist>')
    # Bulk-Merge (B5): EIN Knopf fuer alle angetickten Gruppen. Er ersetzt die
    # quadratischen Auswahllisten je Kachel und steht still (hidden), solange
    # weniger als zwei Gruppen angetickt sind.
    sammel = (f'<div class="uk-sammel"><button class="gtb on" id="uk-bulk" hidden '
              f'data-txt="{html.escape(t("unbekannte.knopf_bulkmerge"), quote=True)}" '
              f'onclick="unbBulkMerge(this)"></button>'
              f'<span id="uk-bulk-msg"></span></div>')
    inhalt = kopf + _gruppen_block(alle, aeh_fehler) + _leiste(sortierung, filter_, mengen) + sammel
    if filter_ == "objekt":
        inhalt += f'<p class="dim">{t("unbekannte.satz_objekte")}</p>'
    if not liste:
        if gesamt:
            inhalt += webui.leer(t("unbekannte.leer_filter"),
                                 t("unbekannte.leer_filter_hinweis"))
        else:
            inhalt += webui.leer(t("unbekannte.leer"), t("unbekannte.leer_hinweis"))
        return inhalt
    inhalt += (f'<div class="ukliste" id="ukliste" data-sort="{html.escape(sortierung, quote=True)}" '
               f'data-filter="{html.escape(filter_, quote=True)}">'
               + kacheln(liste[:SEITE_N]) + '</div>')
    # Nachladen (B1): der Knopf traegt den naechsten Versatz; app.js holt die
    # naechsten SEITE_N Kacheln und haengt sie an. Ohne JS bleibt die Seite
    # vollstaendig bedienbar — sie zeigt dann eben die erste Seite.
    rest = len(liste) - SEITE_N
    if rest > 0:
        inhalt += (f'<div class="uk-mehr"><button class="gtb" id="uk-mehr" '
                   f'data-offset="{SEITE_N}" '
                   f'data-txt="{html.escape(t("unbekannte.knopf_mehr"), quote=True)}" '
                   f'onclick="unbMehr(this)">'
                   f'{t("unbekannte.knopf_mehr", n=min(SEITE_N, rest))}</button></div>')
    return inhalt
