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
Filterwert "merge suggested"."""
import datetime
import html
import urllib.parse

import webui
from core.sprache import t

# EINE Quelle der Listen-Zustaende (QS-Ebenen-Regel: fachliche Aufzaehlungen nie
# verstreut) — der Handler validiert Query/POST gegen genau diese Tupel, die
# Leiste zeichnet sich daraus, und die Gate-Stufe prueft die Deckung.
SORT = ("bilder", "neu")
FILTER = ("offen", "wieder", "heute", "vorschlag", "besucher", "objekt")
SEITE_N = 20            # Gruppen je Ladeschritt
STREIFEN_N = 12         # Crops je Kachel (Deckel; das Beste zuerst)


def _tagesbeginn(jetzt=None):
    d = datetime.datetime.fromtimestamp(jetzt) if jetzt else datetime.datetime.now()
    return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def infos(idents_roh, gesichter):
    """Die Anzeige-Sicht je Identitaet: Mitglieder mit lebendem Gesicht, Zeitspanne,
    bestes Bild. Kaputte Pool-Zeilen duerfen die Seite nie toeten (kc_phase34 R-2):
    nur Dicts mit Listen-members kommen durch, Identitaeten ohne lebende Stuetze
    fallen raus."""
    faces = {g["id"]: g for g in gesichter}
    aus = []
    for u in idents_roh:
        if not (isinstance(u, dict) and isinstance(u.get("members"), list)):
            continue
        mids = [m for m in u.get("members", []) if m in faces]
        if not mids:
            continue
        tss = [faces[m]["ts"] for m in mids]
        mids.sort(key=lambda m: -faces[m].get("guete", 0))
        aus.append({"u": u, "id": str(u.get("id", "")), "mids": mids,
                    "von": min(tss), "bis": max(tss), "rep": mids[0],
                    "n": len(mids),
                    "objekt": bool(u.get("objekt")),
                    "status": u.get("status", "aktiv")})
    return aus


def auswahl(alle, vors, sortierung="bilder", filter_="offen", jetzt=None):
    """Serverseitiges Sortieren/Filtern (der Browser bekommt nur, was er zeigt).
    vors = Vorschlagspaare (fuer den Filterwert "merge suggested"). Unbekannte
    Werte fallen auf den Standard zurueck — eine getippte URL darf keine leere
    Seite ergeben."""
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
        aus = [i for i in alle if i["status"] == "aktiv" and not i["objekt"]]
        if filter_ == "wieder":
            aus = [i for i in aus if i["n"] >= 2]
        elif filter_ == "heute":
            grenze = _tagesbeginn(jetzt)
            aus = [i for i in aus if i["von"] >= grenze]
        elif filter_ == "vorschlag":
            aus = [i for i in aus if i["id"] in mit_vorschlag]
    if sortierung == "neu":
        aus.sort(key=lambda i: (-i["bis"], -i["n"]))
    else:
        aus.sort(key=lambda i: (-i["n"], -i["bis"]))
    return aus


def zaehler(alle):
    """(offen, gesamt) fuer den Fortschrittsanker: offen = die aktiven
    Nicht-Objekt-Gruppen, die noch eine Entscheidung brauchen; gesamt = alle
    Gruppen mit lebender Stuetze. Beides aus DERSELBEN Liste wie die Kacheln."""
    return (sum(1 for i in alle if i["status"] == "aktiv" and not i["objekt"]),
            len(alle))


def _tag(t0, t1):
    # Datums-Hardcodes (%d.%m., B19): bleiben Code, bis die
    # Format-Schluessel-Stufe (format.datum_*) gebaut ist.
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
    uid = html.escape(i["id"], quote=True)
    name = html.escape(_unb_name(i["id"]))
    haken = "".join(
        f'<label class="uk-mg"><input type="checkbox" class="uk-m" value="{html.escape(m, quote=True)}" '
        f'onchange="unbTick(this)">'
        f'<img loading="lazy" src="/anlern/crops/{urllib.parse.quote(m)}.jpg" alt=""></label>'
        for m in i["mids"][:STREIFEN_N])
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
               f'<button class="gtb" onclick="unbObjekt(\'{uid}\',true,this)">{t("unbekannte.knopf_objekt")}</button>')
        wahl = (f'<label class="uk-wahl" title="{html.escape(t("unbekannte.attr_wahl"), quote=True)}">'
                f'<input type="checkbox" class="uk-sel" value="{uid}" onchange="unbSel()"></label>')
    return (
        f'<div class="uk" id="uk-{uid}" data-uid="{uid}">'
        f'<div class="uk-kopf">'
        f'<img class="uk-face" loading="lazy" src="/anlern/crops/{urllib.parse.quote(i["rep"])}.jpg" alt="">'
        f'<div style="min-width:0"><div class="uk-titel">{name}</div>'
        f'<div class="uk-meta"><span class="num">{i["n"]}</span>'
        f'{t("unbekannte.meta_zeit", zeit=_tag(i["von"], i["bis"]))}</div></div>'
        f'{wahl}</div>'
        f'<div class="uk-str">{haken}</div>{mehr_bilder}'
        f'<div class="uk-akt">{akt}</div><div class="uk-msg"></div></div>')


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
           filter_="offen", jetzt=None):
    """-> Seiten-INHALT (Layout/Banner bleiben beim Handler).
    idents_roh = anlernen.lade_unbekannte() (roh, der Kaputt-Zeilen-Filter
    wohnt in infos()) · gesichter = anlernen.lade_gesichter() · vors =
    anlernen.lade_unbekannt_vorschlaege() · personen = master_persons(cfg)."""
    alle = infos(idents_roh, gesichter)
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
    inhalt = kopf + _leiste(sortierung, filter_, mengen) + sammel
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
