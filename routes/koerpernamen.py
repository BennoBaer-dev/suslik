"""routes/koerpernamen — die Seite „Named persons“ (Benannte Personen) unter /koerpernamen, die zweite Seite im
Menuebereich Person neben „Body images“ (routes/koerperbilder).

HERKUNFT: Bauplan analysen/bauplan_feldnachzug_0110.md, Stufe FN3. Der Eigentuemer 23.11.2026 08:59:30: die Personen
sehen, die ueber die Personenerkennung einen Namen bekommen haben, „und zwar nur die“, mit dem Bild aus dem Lauf;
09:28:11: das Neueste zuerst, „nur 10 oder 20 Treffer … in einer Zeile“.

DIE SEITE: Titel und ein Satz, dann eine Karte mit einem Block je Person (Initiale wie auf der Seite Koerperbilder,
Name), darunter eine Bildreihe (auftritte.reihe_html und thumb_html) mit den neuesten Bildern, hoechstens
core.registry.BENANNT_JE_PERSON, das neueste links. Jede Kachel verweist auf /event/<eid> und zeigt das Bild, das der
Vergleich nahm (core.koerperweg.TREFFER_BILD im Ereignisordner, ausgeliefert ueber /events/), darunter Datum und Uhrzeit;
der title nennt Kamera, Wert, Schwelle und Stimmen; die Marke Frigate steht an Ereignissen, deren Name an Frigate ging.
Die Personen stehen nach ihrem neuesten Bild. Die Reihe bricht nicht um, sie schiebt sich seitlich (Stilblock _STIL,
Praefix bn-). Leere Zustaende je eine graue Zeile: Koerperweg aus oder kein gueltiges Koerperbild
(core.kette.koerper_scharf), kein Name im Zeitraum, Namen ohne Bild.

DIE KORREKTUR (Stufe FN4; Eigentuemer 23.11.2026 11:14:02 „Wenn ein falsches Bild drauf ist, dann sollte der User das
anklicken können“, 11:25:31 die richtige Person „freiwillig“): unter jeder Kachel ein kleines x (neben dem Verweis, nicht
darin); es oeffnet unter der Reihe der Person die versteckte Zeile „Richtig waere“ (Auswahl: weiss nicht, die bekannten
Personen ohne die des Blocks, fremde Person) mit Speichern und Abbrechen. Speichern geht an POST /koerpernamen/falsch
(verifyd Service.koerper_korrektur) und laedt bei Erfolg die Seite neu; eine Ablehnung steht rot im Meldefeld. Ein
Formular gibt es nicht, das Skript (_js) hat drei kleine Funktionen.

WOHER DIE NAMEN KOMMEN (daten): dieselbe Regel wie der Auswerter (verifyd Service._koerper_gang) ueber die letzten
core.registry.BENANNT_TAGE Kalendertage, heute mitgezaehlt: karte = core.koerperweg.treffer_karte, ab = koerper_stimmen;
je Tag der Vorfilter moegliche_personen; die Akte wird nur gelesen, wenn ein Tag ihn besteht oder eine an Frigate
geschriebene Kennung (geschrieben, eine Kopie von Service.own_writes_koerper) in karte mit einer Zeile im Zeitraum
steht; dann einmal core.akte.sicht(...).heute(...), je Tag szenarien.szenarien_des_tages und koerper_namen je
Durchgang. Dazu die geschriebenen Kennungen, deren Akte-Zeile gelesen ist und die karte traegt. Die Person kommt immer
aus karte (nach einem Umbenennen der neue Name).

LESARTEN: der Deckel zaehlt Kacheln, also Bilder; ein Name ohne Bild bekommt keine Kachel und zaehlt nur in der Zeile
„ohne Bild“, eine Person ganz ohne Bild steht deshalb nicht als Block da. Die leeren Zustaende stehen nur, wenn kein
Block da ist, nichts unlesbar war und kein Name ohne Bild gezaehlt ist (dann steht nur die Zeile „ohne Bild“).

EHRLICHKEIT (ED008): scheitert das Lesen der Akte oder das Rechnen der Durchgaenge mit einer Ausnahme, zeigt die Seite
einen roten Hinweis und schreibt den Grund als ERROR-Zeile, einmal je Prozess und Grund (Muster routes/koerperbilder,
dessen _versuch hier mitbenutzt wird).

EHRLICHE GRENZEN: Durchgaenge ueber Mitternacht teilt die Seite wie Heute und der Auswerter; die Seite folgt der Regel des
Auswerters (ohne Wahrheits-Karte, ohne Kamera-Filter), nicht der Anzeige von Heute. Ist die Treffer-Datei nicht lesbar,
liefert treffer_karte eine leere Karte mit WARNING, die Seite zeigt dann „kein Name“ ohne roten Hinweis. Treffer vor
dieser Version haben kein Bild. Das Lesen der Akte haelt das Schloss der Akten-Sicht (core/akte.py)."""
import datetime
import html
import json
import os
import threading
import time
import urllib.parse

import auftritte
import szenarien as _sz
from core import akte as _akte
from core import kette as _kette
from core import koerperweg as _kw
from core import logbuch as _logbuch
from core import registry as _reg
from core.sprache import t, t_n
from routes.koerperbilder import _avatar, _versuch, _zeit   # gelesen, nicht kopiert (Muster routes/erkennung _LAUF)

_log = _logbuch.logger(__name__)
# Die Gruende, fuer die dieser Prozess schon eine ERROR-Zeile geschrieben hat, und ihr Schloss (Muster routes/koerperbilder).
_GEMELDET, _GEMELDET_SCHLOSS = set(), threading.Lock()
# Reihe ohne Umbruch, seitlich schiebbar (.pass-thumbs bricht sonst um); Bild 56 x 112 wie #kb-neu .kb-kb.
_STIL = ('<style>'
         '.bn-person{padding:10px 0 12px;border-top:1px solid var(--border)}.bn-person:first-child{border-top:0}'
         '.bn-kopf{display:flex;align-items:center;gap:10px}.bn-kopf .avs{flex:none}'
         '.bn-person .pass-reihe{margin-top:6px}.bn-person .pass-reihe-kopf:empty{display:none}'
         '.bn-person .pass-thumbs{flex-wrap:nowrap;overflow-x:auto;align-items:flex-start;padding-bottom:4px}'
         '.pass-thumb.bn-k{flex:none;position:relative}'
         '.pass-thumb.bn-k img{width:56px;height:112px;object-fit:contain;background:var(--surface-2);'
         'border:1px solid var(--border)}'
         '.pass-thumb.bn-k .bn-f{position:absolute;top:3px;left:50%;transform:translateX(-50%);display:block;'
         'width:auto;height:auto;padding:0 5px;border-radius:999px;font-size:9px;line-height:14px;white-space:nowrap;'
         'background:var(--accent);color:#fff}'
         '.bn-zeile{font-size:13px;color:var(--dim);margin:0 4px 12px}'
         # Stufe FN4: das kleine x unter der Kachel, die markierte Kachel, die Zeile „Richtig waere“ mit Meldefeld
         '.bn-kachel{flex:none;display:flex;flex-direction:column;align-items:center;gap:2px}'
         '.bn-x{margin:0;padding:0 6px;line-height:16px;font-size:12px;border-radius:999px;background:var(--surface);'
         'color:var(--dim)}.bn-x:hover{color:var(--crit);border-color:var(--crit)}'
         '.bn-wahl img{outline:2px solid var(--crit);outline-offset:1px}'
         '.bn-korr{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;margin-top:8px;font-size:13px}'
         '.bn-korr[hidden]{display:none}.bn-korr label{display:flex;flex-wrap:wrap;align-items:center;gap:6px;'
         'max-width:100%}.bn-korr select{max-width:100%}.bn-korr .gtb{margin:0;padding:4px 12px}'
         '.bn-msg{color:var(--crit)}'
         '</style>')


def _e(text):
    """Text fuer HTML maskieren (auch fuer Attribute). -> Text"""
    return html.escape(str(text), quote=True)


def _beginn(tag):
    """Beginn eines Kalendertags der Ortszeit. -> Sekunden seit 1970"""
    return datetime.datetime.combine(tag, datetime.time()).timestamp()


def _melden(gruende):
    """Eine ERROR-Zeile fuer Gruende, die dieser Prozess noch nicht gemeldet hat (ED008). -> None"""
    with _GEMELDET_SCHLOSS:
        neu = [g for g in dict.fromkeys(gruende) if g not in _GEMELDET]
        _GEMELDET.update(neu)
    if neu:
        _log.error(f"named persons page: only a part could be read — {'; '.join(neu)}")


def _namen_des_tages(zeilen, tag, cfg, karte, ab):
    """Die Kennungen mit geltendem Koerper-Namen in den Durchgaengen eines Tags, wie der Auswerter. -> Menge"""
    liste = _sz.szenarien_des_tages(zeilen, _beginn(tag), _beginn(tag + datetime.timedelta(days=1)), cfg, {},
                                    koerper_map=karte, koerper_ab=ab)
    return {e for d in liste for eids in _kw.koerper_namen(d, karte, ab).values() for e in eids}


def _ordnen(benannt, zeilen, karte, geschrieben, data_dir):
    """Die Kacheln je Person, das neueste zuerst, hoechstens BENANNT_JE_PERSON; Personen nach ihrem neuesten Bild.
    -> (Liste (Person, [Kachel]), Zahl der Namen ohne Bild)"""
    je, ohne = {}, 0
    for e in benannt:
        if not os.path.isfile(os.path.join(data_dir, "events", e, _kw.TREFFER_BILD)):
            ohne += 1
            continue
        z, k = zeilen[e], karte[e]
        je.setdefault(k["person"], []).append(
            {"eid": e, "beginn": z.get("start") or z.get("ts") or 0, "kamera": z.get("camera"), "score": k.get("score"),
             "schwelle": k.get("schwelle"), "stimmen": _kw.stimmen_zaehlen((k,)), "frigate": e in geschrieben})
    deckel = int(_reg.BENANNT_JE_PERSON)
    reihen = [(p, sorted(ks, key=lambda x: (-x["beginn"], x["eid"]))[:deckel]) for p, ks in je.items()]
    return sorted(reihen, key=lambda r: (-r[1][0]["beginn"], r[0])), ohne


def daten(cfg, log_path, geschrieben, jetzt):
    """Die benannten Personen der letzten BENANNT_TAGE Kalendertage nach der Regel des Auswerters (Kopf, WOHER DIE
    NAMEN KOMMEN). -> {"personen": [(Person, [Kachel])], "ohne_bild": Zahl, "gruende": [Text]}"""
    gruende = []
    out = {"personen": [], "ohne_bild": 0, "gruende": gruende}
    karte, ab = _kw.treffer_karte(cfg["data_dir"]), int(cfg["koerper_stimmen"])
    heute = datetime.date.fromtimestamp(jetzt)
    tage = [heute - datetime.timedelta(days=k) for k in range(int(_reg.BENANNT_TAGE))]
    von, bis = _beginn(tage[-1]), _beginn(heute + datetime.timedelta(days=1))
    rechnen = [tag for tag in tage if _kw.moegliche_personen(karte, _beginn(tag), ab)]
    im_zeitraum = [e for e in geschrieben if e in karte and von <= (karte[e].get("ts") or 0) < bis]
    if not rechnen and not im_zeitraum:
        return out
    zeilen = _versuch(gruende, "event record", lambda: _akte.sicht(log_path).heute(von, bis)[0], None)
    if zeilen is None:
        return out
    benannt = {e for e in geschrieben if e in zeilen and e in karte}
    for tag in rechnen:
        benannt |= _versuch(gruende, "passes", lambda tag=tag: _namen_des_tages(zeilen, tag, cfg, karte, ab), set())
    out["personen"], out["ohne_bild"] = _ordnen(benannt, zeilen, karte, set(geschrieben), cfg["data_dir"])
    return out


def _zahl(wert):
    """Ein Wert der Treffer-Zeile mit zwei Stellen, ohne Wert ein Strich. -> Text"""
    return f"{wert:.2f}" if isinstance(wert, (int, float)) else "–"


def _kachel(k):
    """Eine Kachel: Verweis auf das Ereignis, das Treffer-Bild, darunter Datum und Uhrzeit, die Marke Frigate; daneben,
    nicht im Verweis, das x der Korrektur (Stufe FN4, Muster routes/koerperbilder._bild_kachel). -> HTML"""
    q = urllib.parse.quote(k["eid"])
    titel = t("koerpernamen.titel", kamera=k["kamera"] or "?", wert=_zahl(k["score"]), schwelle=_zahl(k["schwelle"]),
              stimmen=k["stimmen"])
    marke = f'<span class="bn-f">{_e(t("koerpernamen.frigate"))}</span>' if k["frigate"] else ""
    verweis = auftritte.thumb_html(f"/event/{q}", f"/events/{q}/{_kw.TREFFER_BILD}", _e(_zeit(k["beginn"])) + marke,
                                   kl="pass-thumb bn-k", titel=_e(titel))
    falsch = _e(t("koerpernamen.falsch"))
    return (f'<div class="bn-kachel" data-eid="{_e(k["eid"])}">{verweis}<button class="gtb bn-x" title="{falsch}" '
            f'aria-label="{falsch}" onclick="bnFalsch(this)">&times;</button></div>')


def _korr(person, personen):
    """Die versteckte Zeile „Richtig waere“ eines Personen-Blocks: Auswahl (weiss nicht zuerst, die Personen ohne die des
    Blocks, fremde Person), Speichern, Abbrechen, Meldefeld (Stufe FN4 Punkt 7). -> HTML"""
    wahl = ([("", t("koerpernamen.weiss_nicht"))] + [(p, p) for p in personen if p != person]
            + [(_sz.GT_OFFEN_LABELS[0], t("koerpernamen.fremd"))])
    optionen = "".join(f'<option value="{_e(w)}">{_e(text)}</option>' for w, text in wahl)
    return (f'<div class="bn-korr" hidden><label>{_e(t("koerpernamen.richtig"))}<select>{optionen}</select></label>'
            f'<button class="gtb" onclick="bnSpeichern(this)">{_e(t("koerpernamen.speichern"))}</button>'
            f'<button class="gtb" onclick="bnAbbrechen()">{_e(t("js.allg.abbrechen"))}</button>'
            '<span class="bn-msg" role="status"></span></div>')


def _js():
    """Das Skript der Korrektur (Stufe FN4 Punkt 7, Muster routes/koerperbilder kbPost): bnFalsch oeffnet die Zeile des
    Blocks und merkt die Kachel, bnSpeichern sendet und laedt bei ok neu, sonst Meldung in rot, bnAbbrechen schliesst.
    -> HTML <script>"""
    nicht, fehler = (json.dumps(t(s), ensure_ascii=False) for s in ("koerpernamen.js.nicht", "koerpernamen.js.fehler"))
    return ('<script>'
            'function bnAbbrechen(){document.querySelectorAll(".bn-korr").forEach(function(z){z.hidden=true;});'
            'document.querySelectorAll(".bn-wahl").forEach(function(k){k.classList.remove("bn-wahl");});}'
            'function bnFalsch(b){var k=b.closest(".bn-kachel"),z=b.closest(".bn-person").querySelector(".bn-korr");'
            'bnAbbrechen();k.classList.add("bn-wahl");z.dataset.eid=k.dataset.eid;z.querySelector("select").value="";'
            'z.querySelector(".bn-msg").textContent="";z.hidden=false;}'
            'function bnSpeichern(b){var z=b.closest(".bn-korr"),m=z.querySelector(".bn-msg");b.disabled=true;'
            'fetch("/koerpernamen/falsch",{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({eid:z.dataset.eid,richtig:z.querySelector("select").value})})'
            '.then(function(r){return r.json();}).then(function(d){if(d.ok){location.reload();return;}'
            f'b.disabled=false;m.textContent={nicht}.split("{{grund}}").join(d.msg||"");}})'
            f'.catch(function(){{b.disabled=false;m.textContent={fehler};}});}}'
            '</script>')


def seite(cfg, log_path, geschrieben, jetzt=None, personen=()):
    """GET /koerpernamen: Kopf, roter Hinweis bei Teilmenge, je Person ein Block mit der Bildreihe und der versteckten
    Zeile der Korrektur (personen: die bekannten Personen fuer die Auswahl), die Zeilen der leeren Zustaende.
    -> Seiten-INHALT (Layout beim Handler)"""
    jetzt = time.time() if jetzt is None else jetzt
    d = daten(cfg, log_path, geschrieben, jetzt)
    _melden(d["gruende"])
    teile = [_STIL, f'<h2>{_e(t("nav.koerpernamen"))}</h2><p class="sub">{_e(t("koerpernamen.satz"))}</p>']
    if d["gruende"]:
        teile.append(f'<p class="hk-aeh-fehler">{_e(t("koerperbilder.teilmenge"))}</p>')
    if d["personen"]:
        bloecke = "".join(f'<div class="bn-person" data-person="{_e(p)}"><div class="bn-kopf">{_avatar(p)}<b>{_e(p)}</b>'
                          '</div>' + auftritte.reihe_html("", "".join(_kachel(k) for k in ks)) + _korr(p, personen)
                          + '</div>' for p, ks in d["personen"])
        teile.append(f'<div id="bn-liste" class="card lvs-abschnitt">{bloecke}</div>{_js()}')
    elif not d["gruende"] and not d["ohne_bild"]:      # Nachzug B1: Namen ohne Bild sind kein leerer Zeitraum
        if cfg.get("person_pfad") == "aus" or not _kette.koerper_scharf(cfg["data_dir"]):
            leer = t("koerpernamen.leer_aus")
        else:
            leer = t("koerpernamen.leer_keine", tage=int(_reg.BENANNT_TAGE))
        teile.append(f'<p class="bn-zeile">{_e(leer)}</p>')
    if d["ohne_bild"]:
        teile.append(f'<p class="bn-zeile">{_e(t_n("koerpernamen.ohne_bild", d["ohne_bild"]))}</p>')
    return "".join(teile)
