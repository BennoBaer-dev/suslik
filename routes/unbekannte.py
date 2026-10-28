"""routes/unbekannte — die Seite „Unbekannte“ zum Benennen unter /unbekannte (Bauplan analysen/bauplan_benennen.md,
Fassung 3, Stufe BN3 Punkte 1 bis 4; Konzept analysen/konzept_benennen.md Entscheid 7).

Die Seite zeigt die offenen Unbekannt-Einheiten der letzten Tage in drei Reitern, „Ähnelt einer bekannten Person“ (mit
Vorschlag), „Unbekannt“ und seit Stufe NL1 (Bauplan analysen/bauplan_reiter_nicht_lernbar.md) „Nicht gut genug zum
Lernen“, je Seite so viele Karten, wie die Config sagt, die zuletzt gesehene zuerst, mit Blättern. Die
Daten kommen aus dem Leser von Stufe BN2 (core.unbekanntpool.benennen_seite; einzelne Einheiten für die Antworten der
Handlungen über offene_einheiten und bildwahl), nicht aus der Akte. Die Vergleichsreihe „So kennt suslik X“ liest die
jüngsten Bindungen der Person über core.refquelle.persons_view (die eine Quelle der Referenzen).

Die Karte hat das Design von Heute und Auftritte: Rahmen, Reihen, Kacheln, Haken und Lupe kommen aus auftritte.py
(karte_html, reihe_html, kachel_html, wahl_html, held_html, thumb_html, BRUECKE_JS); hier steht nur, was die Karte einer
Unbekannt-Einheit zeigt. Gezeigt werden nur Bilder über der Latte (Bauplan analysen/bauplan_fix_unbekannte.md, Stufe
FU1, Entscheid E3: core.unbekanntpool.benennbar für Seite, Sprung und Antworten); eine Gruppe ohne solches Bild steht
im dritten Reiter, einer reinen Infoseite (Stufe NL1, Entscheid 2): dieselbe Karte mit den Bildern, je Bild der Grund
mit Wert und Latte, ohne Haken und ohne jeden Knopf, darüber eine Hinweiszeile. Vorauswahl: an einer einzelnen
Identität sind alle Bilder angehakt, am Sammelbecken keines. Am Becken gibt es nur Handlungen mit Auswahl; die
Handlungen an der ganzen Identität (nicht X, ignorieren, kein Gesicht) fragen vorher nach (data-frage).

Ehrlichkeit (ED008): „Alles benannt“ erscheint nur, wenn in keinem der drei Reiter eine Gruppe steht; stehen Gruppen nur
im dritten, zeigen die beiden anderen einen Satz mit ihrer Zahl (Nachbesserung FU1, Stufe NL1). Der Leerzustand
erscheint nur, wenn der Leser vollständig gelesen hat; sonst zeigt die Seite bei
jeder Ansicht einen roten Hinweis mit dem übersetzten Satz (Entscheid E4) und schreibt die Gründe als ERROR-Zeile über
core/logbuch.py, einmal je Prozess und Grund (Stufe FU1 Punkt 3). Namensliste und Vergleichsbilder kommen aus einem
abgesicherten Lesen über core.refquelle.persons_view (_sicht, Nachzug BN3 Punkt 1); scheitert es, gilt das als
Teilmenge, die Karten bleiben stehen. Ist der letzte Aufräum-Schritt für „vermutlich P“ gescheitert
(core.aehnlich.SPEICHER.rot), zeigt die Seite den roten Hinweis wie Heute (Nachzug BN3 Punkt 2).

Sprung auf eine Karte: Heute und Auftritte verlinken /unbekannte?uk=<uid>#uk-<uid>; die Seite sucht Reiter und Seite der
Einheit und zeigt sie dort (ziel), auch im dritten Reiter. Vom alten Inhalt der Seite bleibt nur die Bildregel bild
(genutzt von Heute, /auftritte und /aehnliche).

Ehrliche Grenzen: eine Einheit für die Antworten wird mit einem eigenen Lesen gesucht (der Leser kennt keine Abfrage
einer einzelnen Einheit); der Sprung über uk liest die Einheiten einmal mehr als ein gewöhnlicher Aufruf. Ein Grund gilt
als derselbe, wenn sein Text gleich ist: ändert sich eine Zahl darin, steht eine neue ERROR-Zeile; die gemeldeten Texte
bleiben bis zum Neustart im Speicher."""
import datetime
import html
import json
import threading
import urllib.parse

import auftritte
import webui
from core import logbuch as _logbuch
from core import unbekanntpool as _ubp
from core.lernlauf import bild_url
from core.sprache import t, t_n

_log = _logbuch.logger(__name__)
# Stufe FU1 Punkt 3: die Gründe, für die dieser Prozess schon eine ERROR-Zeile geschrieben hat, und ihr Schloss.
_GEMELDET, _GEMELDET_SCHLOSS = set(), threading.Lock()


def bild(ref_id, mid):
    """Die Bild-Adresse eines Pool-Gesichts (E3a-2): mit ref_id das Profilbild seines Satzes
    (core.lernlauf.bild_url, Lese-Stufe d), ohne (Zeile vor dieser Version, J8) der Ausschnitt unter
    /anlern/crops/. -> URL-Pfad"""
    return bild_url(ref_id, None) if ref_id else f"/anlern/crops/{urllib.parse.quote(str(mid))}.jpg"


def _e(text):
    """Text für HTML maskieren (auch für Attribute). -> Text"""
    return html.escape(str(text), quote=True)


def _zeit(ts):
    """Uhrzeit, mit Datum, wenn nicht von heute. -> Text"""
    d = datetime.datetime.fromtimestamp(ts)
    # Stufe-2-Grenze (B19): Datumsformat je Sprache ist ein eigener Zug.
    return d.strftime("%H:%M") if d.date() == datetime.date.today() else d.strftime("%d.%m. %H:%M")


def _melden(gruende, wo):
    """Eine ERROR-Zeile, wenn der Leser nur eine Teilmenge lesen konnte (ED008: unvollständig ist rot), mit den Gründen,
    die dieser Prozess noch nicht gemeldet hat (einmal je Prozess und Grund, Stufe FU1 Punkt 3).
    -> None"""
    with _GEMELDET_SCHLOSS:
        neu = [g for g in dict.fromkeys(gruende) if g not in _GEMELDET]
        _GEMELDET.update(neu)
    if neu:
        _log.error(f"unknown page ({wo}): only a subset could be read — {'; '.join(neu)}")


def _sicht(cfg):
    """Das eine abgesicherte Lesen der Referenzen über core.refquelle.persons_view (Namensliste und Vergleichsbilder).
    -> ({Person: [ref_id], jüngste Bindung zuerst}, [Grund englisch, falls nicht lesbar])"""
    from core import refquelle as _rq                      # noqa: PLC0415  Referenzen nur über core.refquelle
    try:
        return _rq.persons_view(cfg), []
    except Exception as ex:                                # noqa: BLE001  laut gemeldet: Hinweis und ERROR
        return {}, [f"references not readable, no names and comparison pictures ({type(ex).__name__}: {ex})"]


def _vergleich(sicht, personen, n):
    """Die Vergleichsbilder je vorgeschlagener Person: ihre jüngsten n Bindungen aus der Sicht von _sicht.
    -> {Person: [ref_id]}"""
    return {p: list(sicht.get(p, ()))[:n] for p in sorted({p for p in personen if p})} if n > 0 else {}


def _person(e):
    """Die vorgeschlagene Person einer Einheit: der Vorschlag, beim Sammelbecken seine Person. -> Name oder None"""
    return e["vorschlag"] or e["person"]


def _titel(e):
    """Der Titel der Karte: „ähnlich P“ am Becken, „vermutlich P“ mit Vorschlag, sonst „Unbekannt N“. -> Text"""
    if e["art"] == _ubp.ART_BECKEN:
        return t("heute.aehnlich.sammel", person=e["person"])
    if e["vorschlag"]:
        return t("heute.aehnlich.zu", person=e["vorschlag"])
    return t("unbekannte.name", nummer=e["uid"][1:])


def _info(e):
    """Die Datenzeilen rechts in der Karte: Vorschlag, Zahlen nur für Expert, Hinweise. -> HTML"""
    p = _person(e)
    if e["art"] == _ubp.ART_BECKEN:
        zeile = t("heute.aehnlich.sammel_hinweis", person=p)
    else:
        zeile = t("benennen.vorschlag", person=p) if p else t("benennen.kein_vorschlag")
    aus = f'<div class="pass-folge">{_e(zeile)}</div>'
    m = e.get("merkmal")
    if m:
        zahlen = t("heute.aehnlich.ident", uid=e["uid"], median=f"{m['median']:.2f}", abstand=f"{m['abstand']:.2f}")
        aus += f'<div class="dim nur-expert">{_e(zahlen)}</div>'
    if any(b["rang"] == _ubp.RANG_ZEIT for b in e["bilder"]):
        aus += f'<div class="dim nur-expert">{_e(t("benennen.nach_zeit"))}</div>'
    return aus


def _knoepfe(e):
    """Die Knöpfe der Karte. Am Becken nur Handlungen mit Auswahl; die Handlungen an der ganzen Identität tragen ihre
    Rückfrage in data-frage. -> HTML"""
    p = _person(e)
    aus = f'<button class="gtb" data-aktion="alle" onclick="bnAlle(this)">{_e(t("benennen.knopf.alle"))}</button>'
    if p:
        aus += (f'<button class="gtb on" data-aktion="sind" data-person="{_e(p)}" onclick="bnBenennen(this)">'
                f'{_e(t("benennen.knopf.sind", person=p))}</button>')
    aus += (f'<input class="bn-name" list="bn-personen" placeholder="{_e(t("benennen.attr_name"))}">'
            f'<button class="gtb" data-aktion="name" onclick="bnBenennen(this)">{_e(t("benennen.knopf.name"))}</button>')
    if e["art"] == _ubp.ART_BECKEN:
        return aus + (f'<button class="gtb" data-aktion="nicht_auswahl" data-person="{_e(p)}" '
                      f'onclick="bnNichtAuswahl(this)">{_e(t("benennen.knopf.nicht_auswahl", person=p))}</button>')
    gruppe = []
    if p:
        gruppe.append(("nicht", t("benennen.knopf.nicht", person=p), t("benennen.frage.nicht", person=p), p))
    gruppe += [("besucher", t("benennen.knopf.ignorieren"), t("benennen.frage.ignorieren"), ""),
               ("objekt", t("benennen.knopf.objekt"), t("benennen.frage.objekt"), "")]
    return aus + "".join(f'<button class="gtb" data-aktion="{a}" data-frage="{_e(frage)}" data-person="{_e(person)}" '
                         f'onclick="bnGruppe(this)">{_e(text)}</button>' for a, text, frage, person in gruppe)


def _kachel(e, b):
    """Eine Kachel der Bildreihe: Bild mit Haken (Vorauswahl nur an der einzelnen Identität; die Bildwahl kennt nur Bilder
    über der Latte, Stufe FU1), Uhrzeit und Kamera, für Expert Norm und Latte, die Lupe mit der Person. -> HTML"""
    wahl = auftritte.wahl_html(b["ref_id"], bild(b["ref_id"], b["ref_id"]), an=e["art"] != _ubp.ART_BECKEN)
    norm = t("benennen.bild.norm", norm=f"{b['norm']:.1f}", latte=f"{b['latte']:.1f}")
    unter = (f'<small>{_e(_zeit(b["zeit"]))} {_e(b["kamera"] or "")}</small>'
             f'<small class="nur-expert">{_e(norm)}</small>')
    return auftritte.kachel_html(wahl + unter, _person(e), b["eid"])


def _kachel_info(b):
    """Eine Kachel im dritten Reiter (Stufe NL1, reine Infoseite): das Bild ohne Haken und ohne Lupe, verlinkt auf das
    Ereignis, darunter Uhrzeit und Kamera und sichtbar der Grund mit Wert und Latte. -> HTML"""
    if b["grund"] == _ubp.GRUND_OHNE_NORM:
        grund = t("benennen.nicht_lernbar.ohne_wert")
    else:
        grund = t("benennen.nicht_lernbar.grund", wert=f"{b['norm']:.1f}", latte=f"{b['latte']:.1f}")
    return (f'<div class="pass-kachel"><a class="ubw" href="/event/{_e(urllib.parse.quote(str(b["eid"])))}">'
            f'<img src="{_e(bild(b["ref_id"], b["ref_id"]))}" loading="lazy" alt=""></a>'
            f'<small>{_e(_zeit(b["zeit"]))} {_e(b["kamera"] or "")}</small><small>{_e(grund)}</small></div>')


def karte(e, vergleich):
    """Die Karte einer Einheit (mit ihrer Bildwahl, Feld bilder) im Design von Heute und Auftritte, in ihrem Rahmen
    mit Anker uk-<uid> und der verdeckten Vorlage der Zeile „benannt: X“; im dritten Reiter (Stufe NL1) ohne Knöpfe, ohne
    Haken und ohne Vorlage, je Bild mit seinem Grund. -> HTML"""
    uid, bilder, n = e["uid"], e["bilder"], len(e["mitglieder"])
    info_seite = e["reiter"] == _ubp.REITER_NICHT_LERNBAR
    letzte = e["mitglieder"][0]
    kopf = (f'<b>{_e(_titel(e))}</b> · {_e(t_n("benennen.kopf.bilder", n))} · '
            f'{_e(t("benennen.kopf.zuletzt", zeit=_zeit(letzte["ts"]), kamera=letzte["kamera"] or "?"))}')
    best = max(bilder, key=lambda b: (b["mass"] is not None, b["mass"] or 0.0, b["zeit"]), default=None)
    held = (auftritte.held_html(best["eid"], bild(best["ref_id"], best["ref_id"])) if best
            else f'<span class="pass-bild-leer">{_e(t("auftritte.karte.kein_bild"))}</span>')
    if info_seite:
        info, kacheln = _info(e), "".join(_kachel_info(b) for b in bilder)
    else:
        info = _info(e) + f'<div class="pass-links">{_knoepfe(e)}<span class="dim bn-msg"></span></div>'
        kacheln = "".join(_kachel(e, b) for b in bilder)
    if n > len(bilder):
        kacheln += f'<span class="pass-thumbs-rest">{_e(t("benennen.mehr_bilder", n=n - len(bilder)))}</span>'
    unten = auftritte.reihe_html(_e(t("benennen.reihe.gruppe")), kacheln)
    p = _person(e)
    if p and vergleich.get(p):
        unten += auftritte.reihe_html(_e(t("benennen.reihe.vergleich", person=p)), "".join(
            auftritte.thumb_html(bild_url(r, None), bild_url(r, None), "") for r in vergleich[p]))
    vorlage = ("" if info_seite else
               auftritte.reihe_html("", "", attrs=f' data-rolle="benannt" hidden data-txt="{_e(t("benennen.benannt"))}"'))
    return (f'<div class="bn-einheit" id="uk-{_e(uid)}" data-uid="{_e(uid)}" data-art="{_e(e["art"])}" '
            f'data-reiter="{_e(e["reiter"])}">'
            + auftritte.karte_html(kopf, held, info, unten) + vorlage + '</div>')


def ziel(cfg, uid, jetzt=None):
    """Reiter und Seite, auf der die Einheit uid steht (Sprung von Heute und Auftritte), auch im dritten Reiter (Stufe
    NL1); eine Einheit, die in keinem Reiter steht, hat kein Ziel. -> (Reiter, Seite) oder None"""
    leser = _ubp.benennbar(cfg, jetzt)
    e = next((x for x in leser["einheiten"] if x["uid"] == uid), None)
    if e is None:
        return None
    liste = [x for x in leser["einheiten"] if x["reiter"] == e["reiter"]]
    return e["reiter"], liste.index(e) // max(1, int(leser["werte"]["benennen_karten_je_seite"])) + 1


def stand(cfg, uids, jetzt=None):
    """Der neue Stand der Einheiten uids für die Antworten der Handlungen: Karte und Reiter je Einheit eines der drei
    Reiter (core.unbekanntpool.benennbar), die übrigen als weg, dazu die Zahl je Reiter.
    -> {"karte", "reiter", "weg", "zahl", "vollstaendig"}"""
    leser = _ubp.benennbar(cfg, jetzt)
    w = leser["werte"]
    nach = {e["uid"]: e for e in leser["einheiten"]}
    gezeigt = [dict(nach[u], bilder=_ubp.bildwahl(cfg, nach[u], w["benennen_ereignisse_je_karte"],
                                                  w["benennen_bilder_je_karte"]))
               for u in dict.fromkeys(str(x) for x in uids) if u in nach]
    personen = [_person(e) for e in gezeigt]
    sicht, vf = _sicht(cfg) if any(personen) and w["benennen_vergleichsbilder"] > 0 else ({}, [])
    vergleich = _vergleich(sicht, personen, w["benennen_vergleichsbilder"])
    gruende = leser["gruende"] + vf
    _melden(gruende, "answer")
    return {"karte": {e["uid"]: karte(e, vergleich) for e in gezeigt},
            "reiter": {e["uid"]: e["reiter"] for e in gezeigt},
            "weg": [u for u in dict.fromkeys(str(x) for x in uids) if u not in nach],
            "zahl": {r: sum(1 for e in leser["einheiten"] if e["reiter"] == r) for r in _ubp.REITER},
            "vollstaendig": not gruende}


def _zahl(qs, name):
    """Eine ganze Zahl aus der Query, ohne gültigen Wert 1. -> int"""
    try:
        return max(1, int((qs.get(name) or ["1"])[0]))
    except (TypeError, ValueError):
        return 1


def _reiter_html(daten):
    """Die drei Reiter mit ihrer Zahl, der gezeigte hervorgehoben; data-txt traegt den Rahmen mit {n} fuer das Skript.
    -> HTML"""
    # Statische Schluessel je Reiter (Sprachregel: nie dynamische t()-Schluessel); der assert haelt sie deckungsgleich.
    schluessel = {_ubp.REITER[0]: "benennen.reiter.aehnlich", _ubp.REITER[1]: "benennen.reiter.unbekannt",
                  _ubp.REITER_NICHT_LERNBAR: "benennen.reiter.nicht_lernbar"}
    assert set(schluessel) == set(_ubp.REITER)
    return '<p class="bn-reiter">' + " ".join(
        f'<a class="gtb{" on" if r == daten["reiter"] else ""}" id="bn-reiter-{r}" data-reiter="{r}" '
        f'data-txt="{_e(t(schluessel[r]))}" href="/unbekannte?reiter={r}">{_e(t(schluessel[r], n=daten["zahl"][r]))}</a>'
        for r in _ubp.REITER) + '</p>'


def _blaettern_html(daten):
    """Blättern zwischen den Seiten des Reiters, nur bei mehr als einer Seite. -> HTML"""
    if daten["seiten"] < 2:
        return ""
    nr, r = daten["nr"], daten["reiter"]
    teile = ([f'<a class="gtb" href="/unbekannte?reiter={r}&amp;seite={nr - 1}">{_e(t("benennen.blaettern.neuer"))}</a>']
             if nr > 1 else [])
    teile.append(_e(t("benennen.blaettern.stand", nr=nr, seiten=daten["seiten"])))
    if nr < daten["seiten"]:
        teile.append(f'<a class="gtb" href="/unbekannte?reiter={r}&amp;seite={nr + 1}">'
                     f'{_e(t("benennen.blaettern.aelter"))}</a>')
    return f'<p class="pnote">{" · ".join(teile)}</p>'


def _leer_html(daten, gruende):
    """Der Leerzustand, nur bei vollständigem Status; sonst nichts (der rote Hinweis steht schon oben). Stehen in einem
    Reiter zum Benennen Karten, der Hinweis darauf; stehen Gruppen nur im dritten Reiter (Stufe NL1), der Satz mit ihrer
    Zahl; „Alles benannt“ nur, wenn in keinem Reiter eine Gruppe steht (Nachbesserung FU1 Punkt 1). -> HTML"""
    if daten["karten"] or gruende:
        return ""
    nicht_lernbar = daten["zahl"][_ubp.REITER_NICHT_LERNBAR]
    if any(n for r, n in daten["zahl"].items() if r != _ubp.REITER_NICHT_LERNBAR):
        return webui.leer(t("benennen.leer_reiter"), t("benennen.leer_reiter_hinweis"))
    if nicht_lernbar:
        return webui.leer(t_n("benennen.leer_ausgeblendet", nicht_lernbar))
    return webui.leer(t("benennen.leer", tage=daten["werte"]["benennen_tage"]), t("benennen.leer_hinweis"))


def seite(cfg, qs, jetzt=None):
    """GET /unbekannte: Reiter (Query reiter), Seite (Query seite) oder Sprung auf die Karte einer Einheit (Query uk),
    Karten, Blättern, Hinweis bei Teilmenge, Leerzustand und das Skript; Namensliste und Vergleichsbilder aus dem einen
    abgesicherten Lesen _sicht, roter Hinweis bei gescheitertem Aufräum-Schritt (core.aehnlich.SPEICHER.rot).
    -> Seiten-INHALT (Layout beim Handler)"""
    from core import aehnlich as _aeh                      # noqa: PLC0415  Zustand des letzten Aufräum-Schritts
    reiter = (qs.get("reiter") or [_ubp.REITER[0]])[0]
    reiter = reiter if reiter in _ubp.REITER else _ubp.REITER[0]
    nr, uk, hinweis, z = _zahl(qs, "seite"), (qs.get("uk") or [""])[0], "", None
    if uk:
        z = ziel(cfg, uk, jetzt)
        if z:
            reiter, nr = z
    daten = _ubp.benennen_seite(cfg, reiter, nr, jetzt)
    w = daten["werte"]
    if uk and not z:
        hinweis = f'<p class="dim">{_e(t("benennen.ziel_weg", tage=w["benennen_tage"]))}</p>'
    sicht, vf = _sicht(cfg)
    vergleich = _vergleich(sicht, [_person(e) for e in daten["karten"]], w["benennen_vergleichsbilder"])
    personen = sorted(sicht)
    gruende = daten["gruende"] + vf
    _melden(gruende, "page")
    if gruende:                    # Entscheid E4: nur der übersetzte Satz, die Gründe stehen im Log
        hinweis += f'<p class="hk-aeh-fehler">{_e(t("benennen.teilmenge"))}</p>'
    if _aeh.SPEICHER.rot():        # ED008: wie Heute; die Merkmale sind dann die des letzten gelungenen Laufs
        hinweis += f'<p class="hk-aeh-fehler">{_e(t("heute.aehnlich.fehler"))}</p>'
    kopf = (f'<h2>{_e(t("benennen.titel"))}</h2>'
            f'<p class="sub">{_e(t("benennen.satz", tage=w["benennen_tage"]))}</p>'
            f'<p class="sub nur-expert">{_e(t("benennen.satz_expert", ereignisse=w["benennen_ereignisse_je_karte"]))}</p>'
            + hinweis + _reiter_html(daten)
            + (f'<p class="sub">{_e(t("benennen.nicht_lernbar.hinweis"))}</p>'
               if daten["reiter"] == _ubp.REITER_NICHT_LERNBAR else "")
            + '<p class="dim" id="bn-meldung"></p>'
            + '<datalist id="bn-personen">' + "".join(f'<option value="{_e(p)}">' for p in personen) + '</datalist>')
    karten = "".join(karte(e, vergleich) for e in daten["karten"])
    return (kopf + f'<div id="bn-liste">{karten}</div>' + _leer_html(daten, gruende)
            + _blaettern_html(daten)
            + _js(daten["reiter"]) + auftritte.BRUECKE_JS)


def _js(reiter):
    """Das Skript der Seite: Haken, Benennen über /benennen_zuweisen mit Zeile „benannt: X“, Handlungen am Becken und
    an der ganzen Identität (mit Rückfrage), neuer Stand der Karte aus der Antwort. -> HTML <script>"""
    txt = {k: json.dumps(t(s), ensure_ascii=False) for k, s in (("keine", "benennen.js.keine"), ("name", "benennen.js.name"),
                                                              ("laeuft", "benennen.js.laeuft"),
                                                              ("fehler", "benennen.js.fehler"))}
    return ('<script>'
            f'var BN_REITER={json.dumps(reiter)};'
            'function bnKarte(b){return b.closest(".bn-einheit");}'
            'function bnMsg(k,s){var m=(k&&document.body.contains(k)&&k.querySelector(".bn-msg"))'
            '||document.getElementById("bn-meldung");if(m)m.textContent=s||"";}'
            'function bnGewaehlt(k){var c=k.querySelector(".pass-card");if(!c)return[];'
            'return Array.prototype.map.call(c.querySelectorAll("input[name=ub-sel]:checked:not(:disabled)"),'
            'function(x){return x.value;});}'
            'function bnAlle(b){bnKarte(b).querySelectorAll(".pass-card input[name=ub-sel]")'
            '.forEach(function(c){if(!c.disabled)c.checked=true;});}'
            'function bnPost(p,d){return fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify(d)}).then(function(r){return r.json();});}'
            'function bnWeg(w){var c=w.querySelector(".pass-card");if(c)c.remove();'
            'if(!w.querySelector("[data-rolle=benannt]:not([hidden])"))w.remove();}'
            'function bnStand(d){var tmp=document.createElement("div");'
            'Object.keys(d.karte||{}).forEach(function(u){tmp.innerHTML=d.karte[u];'
            'var neu=tmp.firstElementChild,alt=document.getElementById("uk-"+u);'
            'if((d.reiter||{})[u]!==BN_REITER){if(alt)bnWeg(alt);return;}'
            'if(!alt){var l=document.getElementById("bn-liste");if(l)l.insertBefore(neu,l.firstChild);return;}'
            'var ac=alt.querySelector(".pass-card"),nc=neu.querySelector(".pass-card");'
            'if(ac)alt.replaceChild(nc,ac);else alt.insertBefore(nc,alt.firstChild);});'
            '(d.weg||[]).forEach(function(u){var a=document.getElementById("uk-"+u);if(a)bnWeg(a);});'
            'Object.keys(d.zahl||{}).forEach(function(r){var a=document.getElementById("bn-reiter-"+r);'
            'if(a)a.textContent=a.dataset.txt.split("{n}").join(d.zahl[r]);});}'
            'function bnBenannt(k,p,ids){var v=k.querySelector("[data-rolle=benannt][hidden]");if(!v)return;'
            'var r=v.cloneNode(true);r.hidden=false;'
            'r.querySelector(".pass-reihe-kopf").textContent=v.dataset.txt.split("{person}").join(p);'
            'var z=r.querySelector(".pass-thumbs");'
            'k.querySelectorAll(".pass-card input[name=ub-sel]").forEach(function(c){'
            'if(ids.indexOf(c.value)<0)return;var ka=c.closest(".pass-kachel");if(!ka)return;'
            'c.checked=false;c.disabled=true;var b=ka.querySelector(".pass-knopf");'
            'if(b){b.dataset.person=p;b.hidden=false;}z.appendChild(ka);});k.appendChild(r);}'
            'function bnBenennen(b){var k=bnKarte(b),ids=bnGewaehlt(k),f=k.querySelector(".bn-name");'
            'var p=(b.dataset.person||(f&&f.value)||"").trim();'
            f'if(!ids.length){{bnMsg(k,{txt["keine"]});return;}}if(!p){{bnMsg(k,{txt["name"]});return;}}'
            f'b.disabled=true;bnMsg(k,{txt["laeuft"]});'
            'bnPost("/benennen_zuweisen",{uid:k.dataset.uid,person:p,ids:ids}).then(function(d){'
            'b.disabled=false;bnMsg(k,d.msg);if(!d.ok)return;bnBenannt(k,p,d.uebernommen||[]);'
            'return bnPost("/unbekannt_seite",{uids:[k.dataset.uid]}).then(function(s){bnStand(s);bnMsg(k,d.msg);});'
            f'}}).catch(function(){{b.disabled=false;bnMsg(k,{txt["fehler"]});}});}}'
            'function bnNichtAuswahl(b){var k=bnKarte(b),ids=bnGewaehlt(k);'
            f'if(!ids.length){{bnMsg(k,{txt["keine"]});return;}}b.disabled=true;bnMsg(k,{txt["laeuft"]});'
            'bnPost("/unbekannt_nicht_p_auswahl",{uid:k.dataset.uid,ids:ids}).then(function(d){'
            'b.disabled=false;bnStand(d);bnMsg(k,d.msg);})'
            f'.catch(function(){{b.disabled=false;bnMsg(k,{txt["fehler"]});}});}}'
            'function bnGruppe(b){var k=bnKarte(b);if(!confirm(b.dataset.frage))return;'
            'var a=b.dataset.aktion,pfad={besucher:"/unbekannt_besucher",objekt:"/unbekannt_objekt",'
            'nicht:"/unbekannt_nicht_p"}[a],d={uid:k.dataset.uid,an:true};if(a==="nicht")d.person=b.dataset.person;'
            f'b.disabled=true;bnMsg(k,{txt["laeuft"]});'
            'bnPost(pfad,d).then(function(x){b.disabled=false;bnStand(x);bnMsg(k,x.msg);})'
            f'.catch(function(){{b.disabled=false;bnMsg(k,{txt["fehler"]});}});}}'
            '</script>')
