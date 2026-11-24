"""routes/koerperbilder — die Seite „Body images“ unter /koerperbilder, die erste Seite im Menuebereich Person (daneben
seit Stufe FN3 „Named persons“, routes/koerpernamen).

HERKUNFT: Bauplan analysen/bauplan_koerperweg_neu.md, Stufe KW4 Punkte 1 bis 4 (die Wege der Seite) und Stufe KW8
(Seite neu geordnet, Auftrag des Eigentuemers 21.11.2026 10:26:23 gegen den „Bandwurm“ aus Zeilen ohne Daten; Konzept
analysen/konzept_koerperbilder_seite.md Abschnitte 4 bis 6) und Stufe KW10 (Nachzug nach der Pruefung des Gebauten:
Tageszahl in Kalendertagen, Meldung beim Start, Platz von „Personen waehlen“, Zustand der Marken) und Stufe KW11 (das
Feld heisst „Wie viele Videos je Person untersuchen“, ein Balken zeigt den Fortschritt des Laufs). Gebaut mit den
Bausteinen der Oberflaeche: Abschnitt-Karten der Live-Seite (card lvs-abschnitt), Marken (badge), Knoepfe (gtb),
Bildreihen ueber auftritte.reihe_html, Kacheln pass-kachel; was nur diese Seite braucht, steht im Stilblock _STIL
(Praefix kb-).

DIE SEITE, eine kurze Seite ohne Register, nur mit dem, was Daten hat: Titel und ein Satz. Karte Personen-Lernlauf
(_lauf): Knopf mit der Zahl der verfuegbaren Videos (POST /koerperbilder/cutter aus Stufe KW3), darunter links das Feld
mit der Zahl der Videos je Person und gleich rechts daneben eingeklappt die Auswahl der Personen mit wartenden Videos (Marken mit
aria-pressed), darunter der Stand des Laufs (Service._cutter_stand; die Meldung beim Start weicht dem ersten
Fortschritt); ein Lauf, der nicht durchlief, steht rot mit Grund. Gesperrt ist der Knopf, solange ein Lauf laeuft, das
Pose-Modell fehlt (core.livewache.pose_verfuegbar, Dateipruefung ohne Laden) oder kein Video wartet. Unter dem Stand
der Balken kb-balken (role progressbar, Geruest fs-bar und fs-fill aus webui/style.css), nur waehrend eines Laufs
sichtbar; den Anteil rechnet allein lauf_anteil (gepruefte Videos durch die Gesamtzahl videos_offen), GET
/koerperbilder/cutter liefert ihn als anteil, und das Skript setzt ihn alle 3 s ohne Neuladen und ohne eigene Rechnung. Ein
automatischer oder taeglicher Lauf nennt seinen Ausloeser in der Zeile des Stands, die ihn als data-von traegt; meldet der
Abruf einen anderen Ausloeser, laedt das Skript die Seite neu (Nachzug B2). Die Einstellungen des Lernlaufs (koerper_lauf,
koerper_sichtpruefung) stehen seit Stufe FN2 (Bauplan analysen/bauplan_feldnachzug_0110.md) nur in der Karte
Koerpererkennung der Seite Erkennung; diese Seite hat keinen eigenen Speicherknopf. Karte
Neue Bilder (_neu) nur mit offenen Bildern: je Person die offenen Bilder mit Annehmen und Verwerfen, auch bei
Sichtpruefung aus (dann mit der Zeile Pruefung aus darueber), sonst eine Zeile. Karte Bestand (_bestand) nur mit Personen, die gueltige Bilder haben: je Person eine Zeile (Zahl, an wie vielen
der letzten koerper_max_tage Kalendertage der Ortszeit, heute mitgezaehlt, also nie mehr als koerper_max_tage, neuestes
Bild) als Aufklapper ueber ihre Bilder, jedes einzeln entfernbar (ins Archiv, core.refquelle.body_remove); die uebrigen
bekannten Personen nur als Zahl. Fuss (_fuss): der Zustand (Koerperweg nach
person_pfad, Sichtpruefung koerper_sichtpruefung, Lernlauf koerper_lauf) und der Verweis auf /erkennung, wo die Schalter
stehen. Aufklapper sind Knoepfe mit
aria-expanded und aria-controls (Muster der WAI-ARIA Authoring Practices, Konzept Abschnitt 3), beim Laden alle zu.

WOHER DIE ZAHLEN KOMMEN: die Bilder aus core.refquelle.body_read, die bearbeiteten Ereignisse aus body_events, die Personen
aus core.refquelle.persons_view und der Schublade; die wartenden Videos aus der Akte, begrenzt ueber
core.akte.sicht(...).heute(von, bis) mit dem Fenster core.koerperweg.cutter_fenster(jetzt, koerper_max_tage), gezaehlt mit
derselben Auswahl wie der Cutter (core.koerperweg.cutter_auswahl, ohne Personenliste, ohne Deckel je Person). Die Seite
fragt nichts bei Frigate ab.

AUSGESCHALTETE PERSONEN (Bauplan analysen/bauplan_koerper_schwelle.md, Stufe KF2; Eigentuemer 24.11.2026 08:27:51 „Der
User muss ja erkennen, dass für diese Person keine Personenerkennung da ist"): _bestand ruft
core.koerperweg.abschaltung einmal mit den gueltigen Bildern aus daten und cfg; Wert, Nachbar und aus kommen nur von
dort. Die Zeile einer Person, die aus ist, traegt data-aus="1" und die Klasse kb-aus (roter Ring um die Initiale), unter
dem Namen steht rot der Text koerperbilder.vorrat.aus mit der aehnlichen Person, dem Wert auf zwei Stellen abgerundet und
der Schwelle koerper_schwelle (_aus_satz). Personen, die an sind, bekommen nichts Neues.

EHRLICHKEIT (ED008): laesst sich ein Teil nicht lesen, zeigt die Seite einen roten Hinweis und schreibt den Grund als
ERROR-Zeile, einmal je Prozess und Grund (Muster routes/unbekannte._melden); die wartenden Videos fehlen dann (der Knopf
heisst dann ohne Zahl), und Zeilen, deren Aussage die fehlenden Daten braucht (keine neuen Bilder, keine Bilder im
Bestand, weitere Personen, „noch ohne Bilder“ im Fuss), stehen nicht da.

DIE GRUENDE IM STAND: die Ausfaelle und der Grund eines Laufs, der nicht startete oder abbrach, erscheinen in einfacher
Sprache (Schluessel koerperbilder.grund.*, Tabelle _GRUND_SCHLUESSEL ueber die Konstanten GRUND_* aus core.koerperschnitt;
Gruende, die fuer den Nutzer dasselbe bedeuten, teilen sich einen Schluessel, ihre Zahlen werden zusammengezaehlt). Ein
Grund ohne Zuordnung erscheint im Rohtext. Log und Stand des Dienstes behalten die Kurztexte. Die Zahlen der Zeile stehen
fett wie im Bild.

EHRLICHE GRENZEN: die Schublade wird je Aufruf zweimal gelesen (body_read und body_events oeffnen je die eine Datei); die
Abschaltung rechnet je Aufruf eine Matrix der gueltigen Bilder (Bauplan KF2, Last). Das
Datumsformat ist fuer alle Sprachen gleich (Stufe-2-Grenze B19 wie routes/unbekannte._zeit). Die Farbe der Initiale
folgt der Regel von verifyd (_av_farbe in do_GET: Bytesumme des Namens) ueber die sechs Farb-Tokens --av-1 bis --av-6 aus
webui/style.css. Nach einer Auswahl setzt das Skript die Zahl des Knopfs neu und waehlt die Form nach n gleich 1 (die
Zahl 0 kommt dabei nicht vor, waehlbar sind nur Personen mit wartenden Videos); nach dem Entfernen eines Bilds laedt es
die Seite neu und klappt dieselbe Zeile wieder auf (Merker im sessionStorage, nur fuer diesen einen Neuaufruf), damit
Zahl, Tage und Datum der Zeile vom Dienst kommen."""
import collections
import datetime
import html
import json
import math
import threading
import time

import auftritte
import webui
from core import akte as _akte
from core import kette as _kette
from core import koerperschnitt as _ks
from core import koerperweg as _kw
from core import livewache as _lw
from core import logbuch as _logbuch
from core import refquelle as _rq
from core.sprache import t, t_n

_log = _logbuch.logger(__name__)
OFFEN, GUELTIG, VERWORFEN = _rq.basis.BODY_STATES
BILD_PFAD = "/koerperbilder/bild/"
GRUND_ANNEHMEN = "accepted on the Body images page"
GRUND_VERWERFEN = "discarded on the Body images page"
GRUND_ENTFERNEN = "removed on the Body images page"
AV_TOKENS = 6                   # die Farb-Tokens --av-1 bis --av-6 in webui/style.css
# Die Gruende, fuer die dieser Prozess schon eine ERROR-Zeile geschrieben hat, und ihr Schloss (Muster routes/unbekannte).
_GEMELDET, _GEMELDET_SCHLOSS = set(), threading.Lock()
# Die Gruende des Cutters in einfacher Sprache (Kopf, DIE GRUENDE IM STAND); statische Schluessel, kein t() auf Modulebene.
_GRUND_SCHLUESSEL = {
    _ks.GRUND_ANKER: "koerperbilder.grund.anker",
    _ks.GRUND_PERSONBILD: "koerperbilder.grund.personbild",
    _ks.GRUND_CLIP: "koerperbilder.grund.clip", _ks.GRUND_CLIP_HOLEN: "koerperbilder.grund.clip",
    _ks.GRUND_KURZ: "koerperbilder.grund.kurz",
    _ks.GRUND_UNVOLLSTAENDIG: "koerperbilder.grund.person", _ks.GRUND_KEINE_BOX: "koerperbilder.grund.person",
    _ks.GRUND_FRIGATE: "koerperbilder.grund.daten", _ks.GRUND_SPUR: "koerperbilder.grund.daten",
    _ks.GRUND_UHR: "koerperbilder.grund.daten", _ks.GRUND_ENDE: "koerperbilder.grund.daten",
    _ks.GRUND_UHRANKER: "koerperbilder.grund.daten",
    _ks.GRUND_POSE: "koerperbilder.grund.pose",
    _ks.GRUND_BUDGET: "koerperbilder.grund.speicher",
    _ks.GRUND_ZEITWACHE: "koerperbilder.grund.technik", _ks.GRUND_LAUF: "koerperbilder.grund.technik",
    _ks.GRUND_KEINE_ANTWORT: "koerperbilder.grund.technik", _ks.GRUND_JOB: "koerperbilder.grund.technik",
    _ks.GRUND_ART: "koerperbilder.grund.technik",
    _ks.GRUND_ABLAGE: "koerperbilder.grund.ablage",
}
# Die Stellungen von koerper_lauf mit ihrem Text (Stufe KW13 Punkt 3); dieselben Werte stehen in verifyd
# Service.CONFIG_WHITELIST, die Probe e3_138 haelt beide deckungsgleich.
_LAUF = (("hand", "koerperbilder.auto.hand"), ("taeglich", "koerperbilder.auto.taeglich"),
         ("sofort", "koerperbilder.auto.sofort"))

# Elemente mit dem Attribut hidden (die Ziele der Aufklapper) tragen hier keine eigene display-Regel; leere Meldungs- und
# Stand-Elemente blendet :empty aus, damit ein Text des Skripts sie von selbst zeigt.
_STIL = ('<style>'
         '.kb-seite .avs{flex:none}'
         '.gtb.kb-haupt{display:block;width:100%;margin:10px 0 0;padding:10px 14px;font-size:14px;font-weight:600}'
         '.gtb.kb-haupt:disabled{background:var(--surface-2);border-color:var(--border);color:var(--dim);opacity:1}'
         '.kb-keine{display:block;font-size:15px;margin:6px 0 2px}'
         '.kb-hinweis{font-size:13px;color:var(--dim);margin:0 0 6px}'
         '.kb-opt{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-start;gap:8px 24px;'
         'padding:10px 0 2px}'
         '.kb-videos{display:inline-flex;align-items:center;gap:8px;font-size:13px}.kb-videos .lvs-num{width:64px}'
         '.kb-auf{font-size:13px;font-weight:600}'
         '.kb-pfeil{display:inline-block;color:var(--dim);transition:transform .15s}'
         '[aria-expanded="true"] .kb-pfeil{transform:rotate(90deg)}'
         '.kb-personen{padding:6px 0 2px}.kb-personen .lvs-zweck{margin:0 0 8px}'
         '.kb-picks{display:flex;flex-wrap:wrap;gap:8px}'
         '.kb-pick{display:inline-flex;flex-direction:column;align-items:flex-start;border-radius:10px;padding:4px 12px;'
         'font:inherit;font-size:13px;cursor:pointer}'
         '.kb-pick small{font-size:11px;font-weight:400;color:var(--dim)}'
         '.kb-msg{font-size:13px;color:var(--dim);margin:6px 0 0}.kb-msg:empty{display:none}'
         '.kb-stand{font-size:13px;color:var(--dim);margin:10px 0 4px;padding-top:8px;border-top:1px solid var(--border)}'
         '.kb-stand:empty{display:none}.kb-stand.hk-aeh-fehler{color:var(--crit)}'
         '.fs-bar.kb-balken{margin:0 0 6px}'
         '.kb-person{display:flex;align-items:center;gap:12px;width:100%;margin:0;padding:10px 2px;border:0;'
         'border-top:1px solid var(--border);background:none;color:inherit;font:inherit;text-align:left;cursor:pointer}'
         '.lvs-zweck+.kb-person{border-top:0}.kb-person:hover .lvs-name{color:var(--accent)}'
         '.kb-person .avs{width:36px;height:36px;font-size:14px}.kb-person .lvs-lbl{flex:1 1 auto}'
         '.kb-zahl{font-size:14px;font-weight:600;white-space:nowrap}'
         '.kb-offen{padding:2px 0 12px 48px}.kb-offen .pass-reihe-kopf:empty{display:none}'
         '.kb-kb{display:block;width:44px;height:88px;border-radius:6px;background:var(--surface-2);'
         'border:1px solid var(--border);object-fit:contain}'
         '#kb-neu .kb-kb{width:56px;height:112px}'
         '.kb-rahmen{position:relative}'
         '.kb-x{position:absolute;top:-6px;right:-8px;margin:0;padding:0 5px;line-height:16px;font-size:12px;'
         'border-radius:999px;background:var(--surface);color:var(--dim)}'
         '.kb-x:hover{color:var(--crit);border-color:var(--crit)}'
         '.kb-wahl{display:flex;gap:2px}.kb-wahl .gtb{margin:0;padding:1px 8px;font-size:12px}'
         '.kb-gruppe{padding:10px 0 12px;border-top:1px solid var(--border)}.lvs-zweck+.kb-gruppe{border-top:0}'
         '.kb-gruppe .pass-reihe-kopf:empty{display:none}'
         '.kb-gruppe-kopf{display:flex;align-items:center;gap:10px;flex-wrap:wrap}'
         '.kb-gruppe-kopf .gtb{margin-left:auto;padding:4px 12px}'
         '.kb-rest{font-size:13px;color:var(--dim);margin:0;padding:10px 0 4px;border-top:1px solid var(--border)}'
         '.kb-zeile{font-size:13px;color:var(--dim);margin:0 4px 12px}'
         '.kb-fuss{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;font-size:13px;color:var(--dim);'
         'margin:4px 4px 16px}'
         '.kb-rot{color:var(--crit)}'
         '.kb-aus .avs{box-shadow:0 0 0 2px var(--surface),0 0 0 4px var(--crit)}'
         '.kb-aus-satz{display:block;font-size:13px;color:var(--crit);margin:2px 0 0}'
         '@media (max-width:560px){.kb-gruppe-kopf .gtb{margin-left:0}.kb-offen{padding-left:0}}'
         '</style>')


def _e(text):
    """Text fuer HTML maskieren (auch fuer Attribute). -> Text"""
    return html.escape(str(text), quote=True)


def _zeit(ts):
    """Datum und Uhrzeit eines Bilds oder Laufs. -> Text"""
    return datetime.datetime.fromtimestamp(ts).strftime("%d.%m. %H:%M")


def _datum(ts):
    """Nur das Datum. -> Text"""
    return datetime.datetime.fromtimestamp(ts).strftime("%d.%m.")


def _avatar(person):
    """Die Initiale der Person im Farbkreis (Klasse avs, Farbe nach der Bytesumme des Namens). -> HTML"""
    nr = sum(bytearray(person.encode("utf-8"))) % AV_TOKENS + 1
    return f'<span class="avs" style="background:var(--av-{nr})">{_e(person[:1].upper())}</span>'


def _melden(gruende):
    """Eine ERROR-Zeile fuer Gruende, die dieser Prozess noch nicht gemeldet hat (ED008). -> None"""
    with _GEMELDET_SCHLOSS:
        neu = [g for g in dict.fromkeys(gruende) if g not in _GEMELDET]
        _GEMELDET.update(neu)
    if neu:
        _log.error(f"body images page: only a part could be read — {'; '.join(neu)}")


def _versuch(gruende, was, aufruf, leer):
    """Einen Leser abgesichert rufen; scheitert er, kommt der Grund in gruende. -> Ergebnis oder leer"""
    try:
        return aufruf()
    except Exception as ex:                                # noqa: BLE001  laut gemeldet: roter Hinweis und ERROR
        gruende.append(f"{was} not readable ({type(ex).__name__}: {ex})")
        return leer


def daten(cfg, log_path, jetzt):
    """Die Daten der Seite: Bilder der Schublade, Personen, wartende geeignete Videos je Person (Kopf, WOHER DIE ZAHLEN
    KOMMEN). -> {"bilder", "personen", "wartend" (Counter oder None), "gruende"}"""
    gruende = []
    bilder = _versuch(gruende, "body images", lambda: _rq.body_read(cfg), [])
    bearbeitet = _versuch(gruende, "processed events", lambda: _rq.body_events(cfg), None)
    gesichter = _versuch(gruende, "references", lambda: _rq.persons_view(cfg), {})
    wartend = None
    if bearbeitet is not None:
        def _zaehlen():
            von, bis = _kw.cutter_fenster(jetzt, cfg["koerper_max_tage"])
            zeilen = _akte.sicht(log_path).heute(von, bis)[0]
            wahl = _kw.cutter_auswahl(zeilen, bearbeitet, cfg, None, max(1, len(zeilen)), von)
            return collections.Counter(p for p, _eid in wahl)
        wartend = _versuch(gruende, "event record", _zaehlen, None)
    personen = sorted(set(gesichter) | {b["person"] for b in bilder} | set(wartend or ()))
    return {"bilder": bilder, "personen": personen, "wartend": wartend, "gruende": gruende}


def _kopf():
    """Ueberschrift und Satz der Seite. -> HTML"""
    return f'<h2>{_e(t("nav.person"))}</h2><p class="sub">{_e(t("koerperbilder.satz"))}</p>'


def _fuss(cfg, d, pose_ok):
    """Fuss der Seite: Zustand des Koerperwegs (Warnfarbe, wenn er ohne Pose-Modell oder ohne gueltiges Bild nicht
    wirkt) und der Sichtpruefung, dazu der Verweis auf die Seite Erkennung mit den Schaltern. -> HTML"""
    # Statische Schluessel je Stufe von person_pfad (Sprachregel: nie dynamische t()-Schluessel); der assert haelt sie
    # deckungsgleich mit core.kette.KETTE_STUFEN.
    stufen = {"immer": ("koerperbilder.zustand.an", "ok"),
              "nur_wenn_gesicht_leer": ("koerperbilder.zustand.nur_ohne_gesicht", "ok"),
              "aus": ("koerperbilder.zustand.aus", "warn")}
    assert set(stufen) == set(_kette.KETTE_STUFEN)
    weg, weg_kl = stufen.get(cfg.get("person_pfad"), ("koerperbilder.zustand.unbekannt", "warn"))
    weg = t(weg)
    if cfg.get("person_pfad") != "aus":
        if not pose_ok:                                    # der Weg wirkt dann nicht (core/kette.lage)
            weg, weg_kl = f'{weg}, {t("koerperbilder.grund.pose")}', "warn"
        elif not d["gruende"] and not any(b["zustand"] == GUELTIG for b in d["bilder"]):
            weg, weg_kl = f'{weg}, {t("koerperbilder.zustand.ohne_bilder")}', "warn"
    pruef, pruef_kl = (("koerperbilder.zustand.an", "ok") if cfg.get("koerper_sichtpruefung")
                       else ("koerperbilder.zustand.aus", "warn"))
    lauf = dict(_LAUF).get(cfg.get("koerper_lauf"), "koerperbilder.zustand.unbekannt")     # Stufe KW13 Punkt 3
    return (f'<p id="kb-fuss" class="kb-fuss"><span>{_e(t("koerperbilder.zustand.erkennen"))} '
            f'<span class="badge {weg_kl}">{_e(weg)}</span></span>'
            f'<span>{_e(t("koerperbilder.zustand.pruefung"))} <span class="badge {pruef_kl}">{_e(t(pruef))}</span></span>'
            f'<span>{_e(t("koerperbilder.auto.fuss"))} <span class="badge ok">{_e(t(lauf))}</span></span>'
            f'<span>{_e(t("koerperbilder.fuss.einstellungen"))} <a href="/erkennung">{_e(t("nav.erkennung"))}</a>'
            '</span></p>')


def _bild_kachel(b, wahl):
    """Eine Kachel eines Koerperbilds: Bild, Zeit und darunter (Neue Bilder) Annehmen und Verwerfen, sonst der Knopf
    zum Entfernen am Bild. -> HTML"""
    bild = f'<img class="kb-kb" src="{_e(BILD_PFAD + b["bild_id"])}.png" loading="lazy" alt="">'
    if wahl:
        unten = (f'<span class="kb-wahl"><button class="gtb" title="{_e(t("koerperbilder.neu.annehmen"))}" '
                 f'aria-label="{_e(t("koerperbilder.neu.annehmen"))}" onclick="kbWahl(this,\'bestaetigen\',0)">'
                 f'&#10003;</button><button class="gtb" title="{_e(t("koerperbilder.neu.verwerfen"))}" '
                 f'aria-label="{_e(t("koerperbilder.neu.verwerfen"))}" onclick="kbWahl(this,\'verwerfen\',0)">'
                 f'&#10005;</button></span>')
        return (f'<div class="pass-kachel kb-bild" data-bild="{_e(b["bild_id"])}">{bild}'
                f'<small>{_e(_zeit(b["zeit"]))}</small>{unten}</div>')
    x = (f'<button class="gtb kb-x" title="{_e(t("koerperbilder.vorrat.entfernen"))}" '
         f'aria-label="{_e(t("koerperbilder.vorrat.entfernen"))}" onclick="kbEntfernen(this)">&times;</button>')
    return (f'<div class="pass-kachel kb-bild" data-bild="{_e(b["bild_id"])}"><div class="kb-rahmen">{bild}{x}</div>'
            f'<small>{_e(_zeit(b["zeit"]))}</small></div>')


def _aus_satz(a, cfg):
    """Die rote Zeile einer Person, die fuer das Erkennen aus ist (Kopf, AUSGESCHALTETE PERSONEN): wem sie zu aehnlich
    ist, Wert und Schwelle. -> HTML; fuer eine Person, die an ist, leer"""
    if not a["aus"]:
        return ""
    wert = math.floor(a["wert"] * 100) / 100           # abgerundet: eine gezeigte Zahl unter der Schwelle heisst nie aus
    text = t("koerperbilder.vorrat.aus", person=a["nachbar"], wert=f"{wert:.2f}",
             schwelle=f'{float(cfg["koerper_schwelle"]):g}')
    return f'<span class="kb-aus-satz">{_e(text)}</span>'


def _bestand(d, cfg, jetzt):
    """Karte Bestand: je Person mit gueltigen Bildern eine Zeile als Aufklapper ueber ihre Bilder (meiste Bilder zuerst,
    alle zu), eine ausgeschaltete Person rot markiert, die uebrigen Personen als Zahl; ohne gueltiges Bild nur eine
    Zeile, ohne Person der Leerzustand. -> HTML"""
    tage = int(cfg["koerper_max_tage"])
    je = {}
    for b in d["bilder"]:
        if b["zustand"] == GUELTIG:
            je.setdefault(b["person"], []).append(b)
    if not d["personen"]:
        return webui.leer(t("koerperbilder.vorrat.leer"), t("koerperbilder.vorrat.leer_hinweis"))
    if not je:
        return "" if d["gruende"] else f'<p class="kb-zeile">{_e(t("koerperbilder.vorrat.keine_bilder"))}</p>'
    heute = datetime.date.fromtimestamp(jetzt)          # Kalendertage der Ortszeit, heute und die tage - 1 davor
    erster = heute - datetime.timedelta(days=tage - 1)
    # Stufe KF2 Punkt 1: Wert, Nachbar und aus nur aus core.koerperweg.abschaltung, die Seite vergleicht selbst nichts
    abschaltung = _kw.abschaltung([b for b in d["bilder"] if b["zustand"] == GUELTIG], cfg)
    zeilen = []
    for nr, p in enumerate(sorted(je, key=lambda p: (-len(je[p]), p)), start=1):
        gl = sorted(je[p], key=lambda b: -b["zeit"])
        abgedeckt = len({k for k in (datetime.date.fromtimestamp(b["zeit"]) for b in gl) if erster <= k <= heute})
        hn = " · ".join((t("koerperbilder.vorrat.tage", tage=abgedeckt, max_tage=tage),
                         t("koerperbilder.vorrat.neuest", datum=_datum(gl[0]["zeit"]))))
        kl, merk = (" kb-aus", ' data-aus="1"') if abschaltung[p]["aus"] else ("", "")    # Stufe KF2 Punkt 2
        zeilen.append(f'<button type="button" class="kb-person{kl}" aria-expanded="false" aria-controls="kb-p-{nr}" '
                      f'data-person="{_e(p)}"{merk} onclick="kbAuf(this)">{_avatar(p)}<span class="lvs-lbl">'
                      f'<span class="lvs-name">{_e(p)}</span><span class="lvs-hn">{_e(hn)}</span>'
                      f'{_aus_satz(abschaltung[p], cfg)}</span>'
                      f'<span class="kb-zahl">{_e(t_n("koerperbilder.vorrat.bilder", len(gl)))}</span>'
                      '<span class="kb-pfeil" aria-hidden="true">&#8250;</span></button>'
                      f'<div id="kb-p-{nr}" class="kb-offen" hidden>'
                      + auftritte.reihe_html("", "".join(_bild_kachel(b, False) for b in gl)) + '</div>')
    rest = len([p for p in d["personen"] if p not in je])
    weitere = (f'<p class="kb-rest">{_e(t_n("koerperbilder.vorrat.weitere", rest))}</p>'
               if rest and not d["gruende"] else "")
    return (f'<div id="kb-bestand" class="card lvs-abschnitt"><h3>{_e(t("koerperbilder.vorrat.titel"))}</h3>'
            f'<p class="lvs-zweck">{_e(t("koerperbilder.vorrat.zweck"))}</p>{"".join(zeilen)}{weitere}'
            '<p class="kb-msg" id="kb-bestand-msg"></p></div>')


def _grund_text(grund):
    """Ein Grund des Cutters in einfacher Sprache (Schluessel koerperbilder.grund.*); ohne Zuordnung der Rohtext.
    -> Text (noch nicht maskiert)"""
    schluessel = _GRUND_SCHLUESSEL.get(grund)
    return t(schluessel) if schluessel else str(grund)


def _fett(text, n):
    """Text maskieren und das erste Vorkommen der Zahl n fett setzen (die Zahlen der Zeile zum letzten Lauf, wie im Bild).
    -> HTML"""
    s, z = _e(text), str(n)
    i = s.find(z)
    return s if i < 0 else f"{s[:i]}<b>{z}</b>{s[i + len(z):]}"


def _stand(stand):
    """Die Zeile zum Stand des Laufs: ohne Lauf seit dem Start leer (der Stilblock blendet sie aus, das Skript fuellt sie
    beim ersten Lauf), laeuft (data-laeuft 1, Vorlage fuer das Skript), letzter Lauf, oder rot mit Grund, wenn ein Lauf
    nicht durchlief. -> HTML"""
    # Stufe KW13 Punkt 2: der Ausloeser eines automatischen oder taeglichen Laufs steht in der Zeile (statische Schluessel)
    von = {"auto": "koerperbilder.auto.von_auto", "taeglich": "koerperbilder.auto.von_taeglich"}.get(
        (stand or {}).get("ausloeser"))
    von = t(von) if von else ""
    vorlage = _e(" · ".join(x for x in (von, t("koerperbilder.cutter.laeuft", videos="{videos}", offen="{offen}",
                                                 bilder="{bilder}")) if x))
    # Nachzug B2: data-von ist der Ausloeser, fuer den die Vorlage gilt (ohne Stand der von Hand); meldet der Abruf einen
    # anderen, laedt kbWarten die Seite neu
    attrs = f'data-txt="{vorlage}" data-von="{_e((stand or {}).get("ausloeser") or "hand")}"'
    if not stand:
        return f'<p id="kb-stand" class="kb-stand" data-laeuft="0" {attrs}></p>'
    if stand.get("laeuft"):
        text = " · ".join(x for x in (von, t("koerperbilder.cutter.laeuft", videos=stand.get("videos", 0),
                                              offen=stand.get("videos_offen", 0), bilder=stand.get("bilder", 0))) if x)
        return f'<p id="kb-stand" class="kb-stand" data-laeuft="1" {attrs}>{_e(text)}</p>'
    teile = [_e(" · ".join(x for x in (t("koerperbilder.cutter.letzter", zeit=_zeit(stand.get("start") or 0)), von)
                           if x)),
             _fett(t_n("koerperbilder.cutter.geprueft", stand.get("videos", 0)), stand.get("videos", 0)),
             _fett(t_n("koerperbilder.cutter.behalten", stand.get("bilder", 0)), stand.get("bilder", 0))]
    je_text = collections.Counter()
    for g, n in (stand.get("ausfaelle") or {}).items():
        je_text[_grund_text(g)] += n
    if je_text:
        gruende = ", ".join(f"{n} {g}" for g, n in sorted(je_text.items(), key=lambda x: (-x[1], x[0])))
        n = sum(je_text.values())
        zeile = _fett(t_n("koerperbilder.cutter.ausgefallen", n, gruende="\x00"), n)
        teile.append(zeile.replace("\x00", _e(gruende)))  # die Gruende erst nach dem Fettsetzen (ihre Zahlen bleiben normal)
    kl = "kb-stand"
    if stand.get("grund"):
        teile.append(_e(t("koerperbilder.cutter.fehler", grund=_grund_text(stand["grund"]))))
        kl += " hk-aeh-fehler"
    return f'<p id="kb-stand" class="{kl}" data-laeuft="0" {attrs}>{" · ".join(teile)}</p>'


def lauf_anteil(stand):
    """Der Anteil eines Laufs: gepruefte Videos (videos) durch die Gesamtzahl des Laufs (videos_offen), abgerundet.
    -> ganze Zahl 0 bis 100; ohne Stand, bei Gesamtzahl 0 oder unbrauchbaren Werten 0"""
    try:
        fertig, alle = int(stand["videos"]), int(stand["videos_offen"])
    except (TypeError, KeyError, ValueError):
        return 0
    if fertig < 0 or alle <= 0:
        return 0
    return min(100, fertig * 100 // alle)


def _balken(stand):
    """Der Balken des Laufs unter der Zeile des Stands (Geruest fs-bar und fs-fill aus webui/style.css, Anteil aus
    lauf_anteil); laeuft kein Lauf, traegt er hidden. -> HTML"""
    a = lauf_anteil(stand)
    zu = "" if (stand or {}).get("laeuft") else " hidden"
    return (f'<div id="kb-balken" class="fs-bar kb-balken" role="progressbar" aria-valuemin="0" aria-valuemax="100" '
            f'aria-valuenow="{a}" aria-label="{_e(t("koerperbilder.cutter.balken"))}"{zu}>'
            f'<span class="fs-fill" style="width:{a}%"></span></div>')


def _auswahl(d):
    """Das Feld Videos je Person und, wenn fuer mindestens zwei Personen Videos warten, der Aufklapper „Personen waehlen“
    mit einer Marke je Person mit wartenden Videos (keine Auswahl heisst alle). -> HTML"""
    w = d["wartend"]
    feld = (f'<label class="kb-videos">{_e(t("koerperbilder.cutter.videos"))}'
            '<input class="lvs-num" id="kb-videos" type="number" min="1" step="1" value="1"></label>')
    mit = [p for p in d["personen"] if w is not None and w.get(p, 0) > 0]
    if len(mit) < 2:
        return f'<div class="kb-opt">{feld}</div>'
    picks = "".join(f'<button type="button" class="uk-f kb-pick" aria-pressed="false" data-person="{_e(p)}" '
                    f'data-wartend="{w[p]}" onclick="kbPick(this)">{_e(p)}'
                    f'<small>{_e(t_n("koerperbilder.cutter.wartend", w[p]))}</small></button>' for p in mit)
    return (f'<div class="kb-opt">{feld}<button type="button" class="lvs-link kb-auf" aria-expanded="false" '
            f'aria-controls="kb-personen" onclick="kbAuf(this)">{_e(t("koerperbilder.cutter.personen_waehlen"))} '
            '<span class="kb-pfeil" aria-hidden="true">&#8250;</span></button></div>'
            f'<div id="kb-personen" class="kb-personen" hidden><p class="lvs-zweck">'
            f'{_e(t("koerperbilder.cutter.personen_hilfe"))}</p><div class="kb-picks">{picks}</div></div>')


def _lauf(d, stand, cfg, pose_ok):
    """Karte Personen-Lernlauf: Satz oder Leerzustand, Hinweise (Weg aus, Pose-Modell fehlt), Knopf mit der Zahl der
    verfuegbaren Videos, Feld und Auswahl (_auswahl), Stand und Balken des Laufs. -> HTML"""
    w = d["wartend"]
    n = None if w is None else sum(w.values())
    if n == 0:
        satz = (f'<b class="kb-keine">{_e(t("koerperbilder.cutter.keine_titel"))}</b><p class="lvs-zweck">'
                f'{_e(t("koerperbilder.cutter.keine_satz", tage=int(cfg["koerper_max_tage"])))}</p>')
    else:
        satz = f'<p class="lvs-zweck">{_e(t("koerperbilder.cutter.zweck"))}</p>'
    if cfg.get("person_pfad") == "aus":
        satz += (f'<p class="kb-hinweis">{_e(t("koerperbilder.cutter.weg_aus"))} '
                 f'<a href="/erkennung">{_e(t("nav.erkennung"))}</a></p>')
    if not pose_ok:
        satz += f'<p class="kb-hinweis kb-rot">{_e(t("koerperbilder.grund.pose"))}</p>'
    gesperrt = bool((stand or {}).get("laeuft")) or not pose_ok or n == 0
    text = t("koerperbilder.cutter.start_ohne_zahl") if n is None else t_n("koerperbilder.cutter.start", n)
    knopf = (f'<button type="button" class="gtb on kb-haupt" id="kb-start" data-n="{"" if n is None else n}" '
             f'data-eins="{_e(t("koerperbilder.cutter.start.eins", n="{n}"))}" '
             f'data-viele="{_e(t("koerperbilder.cutter.start.viele", n="{n}"))}" onclick="kbStart(this)"'
             f'{" disabled" if gesperrt else ""}>{_e(text)}</button>')
    return (f'<div id="kb-lauf" class="card lvs-abschnitt"><h3>{_e(t("koerperbilder.cutter.titel"))}</h3>{satz}{knopf}'
            + ("" if n == 0 else _auswahl(d)) + '<p class="kb-msg" id="kb-msg"></p>' + _stand(stand) + _balken(stand)
            + '</div>')


def _neu(d, cfg):
    """Neue Bilder: mit offenen Bildern die Karte (Zahl im Titel, je Person die offenen Bilder, neueste zuerst, mit
    Annehmen und Verwerfen), auch bei Pruefung aus (Stufe KW13 Punkt 1, nichts wird still gueltig; dann steht die Zeile
    Pruefung aus darueber); ohne offene Bilder eine Zeile (keine offenen Bilder, Pruefung aus). -> HTML"""
    aus = "" if cfg.get("koerper_sichtpruefung") else f'<p class="kb-zeile">{_e(t("koerperbilder.neu.pruefung_aus"))}</p>'
    gruppen, zahl = [], 0
    for p in d["personen"]:
        of = sorted((b for b in d["bilder"] if b["person"] == p and b["zustand"] == OFFEN), key=lambda b: -b["zeit"])
        if not of:
            continue
        zahl += len(of)
        kopf = (f'<div class="kb-gruppe-kopf">{_avatar(p)}<b>{_e(p)}</b>'
                f'<button class="gtb on" onclick="kbWahl(this,\'bestaetigen\',1)">{_e(t("koerperbilder.neu.alle"))}'
                '</button></div>')
        gruppen.append(f'<div class="kb-gruppe" data-person="{_e(p)}">{kopf}'
                       + auftritte.reihe_html("", "".join(_bild_kachel(b, True) for b in of)) + '</div>')
    if not gruppen:
        return aus or ("" if d["gruende"] else f'<p class="kb-zeile">{_e(t("koerperbilder.neu.leer"))}</p>')
    return (aus + f'<div id="kb-neu" class="card lvs-abschnitt"><h3>{_e(t("koerperbilder.neu.titel"))} '
            f'<span id="kb-neu-zahl">({zahl})</span></h3>'
            f'<p class="lvs-zweck">{_e(t("koerperbilder.neu.zweck"))}</p>{"".join(gruppen)}'
            '<p class="kb-msg" id="kb-neu-msg"></p></div>')


def seite(cfg, log_path, stand, jetzt=None):
    """GET /koerperbilder: Kopf, roter Hinweis bei Teilmenge, Personen-Lernlauf, Neue Bilder, Bestand, Fuss und das
    Skript. -> Seiten-INHALT (Layout beim Handler)"""
    jetzt = time.time() if jetzt is None else jetzt
    d = daten(cfg, log_path, jetzt)
    _melden(d["gruende"])
    pose_ok = _lw.pose_verfuegbar()
    hinweis = f'<p class="hk-aeh-fehler">{_e(t("koerperbilder.teilmenge"))}</p>' if d["gruende"] else ""
    return (_STIL + '<div class="kb-seite">' + _kopf() + hinweis + _lauf(d, stand, cfg, pose_ok) + _neu(d, cfg)
            + _bestand(d, cfg, jetzt) + _fuss(cfg, d, pose_ok) + '</div>' + _js())


def _ids(werte):
    """Die Kennungen einer Anfrage, nur gueltige sha256-Kennungen, ohne Doppel. -> Liste oder None"""
    if not (isinstance(werte, list) and werte
            and all(isinstance(i, str) and _rq.basis.REF_ID_RE.fullmatch(i) for i in werte)):
        return None
    return list(dict.fromkeys(werte))


def zustand_setzen(cfg, anfrage, annehmen):
    """POST /koerperbilder/bestaetigen (annehmen) und /koerperbilder/verwerfen: offene Bilder auf gueltig oder verworfen;
    nur wenn alle genannten Bilder offen in der Schublade liegen, sonst nichts. -> (HTTP-Status, Antwort als dict)"""
    ids = _ids(anfrage.get("ids"))
    if ids is None:
        return 400, {"ok": False, "msg": "ids must be a non-empty list of body image ids"}
    offen = {b["bild_id"] for b in _rq.body_read(cfg, states=(OFFEN,))}
    fremd = [i for i in ids if i not in offen]
    if fremd:
        return 400, {"ok": False, "msg": f"{len(fremd)} image(s) are not new images in the drawer — nothing changed"}
    ziel, grund = (GUELTIG, GRUND_ANNEHMEN) if annehmen else (VERWORFEN, GRUND_VERWERFEN)
    try:
        for i in ids:
            _rq.body_state(cfg, i, ziel, grund)
    except _rq.RefquelleError as ex:
        return 409, {"ok": False, "msg": str(ex)}
    _log.info(f"body images page: {len(ids)} new image(s) set to {ziel}")
    return 200, {"ok": True, "zustand": ziel, "n": len(ids)}


def entfernen(cfg, anfrage):
    """POST /koerperbilder/entfernen: ein Bild der Schublade ins Archiv (core.refquelle.body_remove).
    -> (HTTP-Status, Antwort als dict)"""
    ids = _ids([anfrage.get("id")])
    if ids is None:
        return 400, {"ok": False, "msg": "id must be a body image id"}
    if ids[0] not in {b["bild_id"] for b in _rq.body_read(cfg)}:
        return 400, {"ok": False, "msg": "the image is not in the drawer — nothing removed"}
    try:
        _rq.body_remove(cfg, ids[0], GRUND_ENTFERNEN)
    except _rq.RefquelleError as ex:
        return 409, {"ok": False, "msg": str(ex)}
    return 200, {"ok": True}


def _js():
    """Das Skript der Seite: Aufklapper (kbAuf), Bild entfernen (danach neu laden und die Zeile wieder aufklappen),
    annehmen, verwerfen (Zahl im Titel nachfuehren, ohne offenes Bild neu laden), Personen waehlen (Zahl des Knopfs), Lauf
    starten und seinen Stand nachlesen, bis er endet (Zeile des Stands und Balken aus dem Feld anteil, dann neu laden).
    -> HTML <script>"""
    txt = {k: json.dumps(t(s), ensure_ascii=False) for k, s in (("fertig", "koerperbilder.js.fertig"),
                                                              ("nicht", "koerperbilder.js.nicht"),
                                                              ("fehler", "koerperbilder.js.fehler"),
                                                              ("zahl", "koerperbilder.js.zahl"),
                                                              ("laeuft", "koerperbilder.js.laeuft"))}
    return ('<script>'
            'function kbMsg(id,s,rot){var m=document.getElementById(id);if(m){m.textContent=s||"";'
            'm.classList.toggle("kb-rot",!!rot);}}'
            f'function kbNicht(id,d){{kbMsg(id,{txt["nicht"]}.split("{{grund}}").join((d&&d.msg)||""),true);}}'
            'function kbPost(p,d){return fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify(d)}).then(function(r){return r.json();});}'
            'function kbAuf(b){var z=document.getElementById(b.getAttribute("aria-controls"));if(!z)return;'
            'var auf=b.getAttribute("aria-expanded")!=="true";b.setAttribute("aria-expanded",auf?"true":"false");'
            'z.hidden=!auf;}'
            'function kbEntfernen(b){var k=b.closest(".kb-bild"),z=b.closest(".kb-offen"),'
            'p=z&&document.querySelector(\'[aria-controls="\'+z.id+\'"]\');b.disabled=true;'
            'kbPost("/koerperbilder/entfernen",{id:k.dataset.bild}).then(function(d){'
            'if(d.ok){try{if(p)sessionStorage.setItem("kbAuf",p.dataset.person);}catch(e){}location.reload();}'
            'else{b.disabled=false;kbNicht("kb-bestand-msg",d);}})'
            f'.catch(function(){{b.disabled=false;kbMsg("kb-bestand-msg",{txt["fehler"]},true);}});}}'
            'function kbWahl(b,was,alle){var g=b.closest(".kb-gruppe"),ids=alle?'
            'Array.prototype.map.call(g.querySelectorAll(".kb-bild"),function(x){return x.dataset.bild;})'
            ':[b.closest(".kb-bild").dataset.bild];b.disabled=true;'
            'kbPost("/koerperbilder/"+was,{ids:ids}).then(function(d){if(!d.ok){b.disabled=false;'
            'kbNicht("kb-neu-msg",d);return;}Array.prototype.forEach.call(g.querySelectorAll(".kb-bild"),function(k){'
            'if(ids.indexOf(k.dataset.bild)>=0)k.remove();});if(!g.querySelector(".kb-bild"))g.remove();'
            'var r=document.querySelectorAll("#kb-neu .kb-bild").length;if(!r){location.reload();return;}'
            'var z=document.getElementById("kb-neu-zahl");if(z)z.textContent="("+r+")";'
            f'kbMsg("kb-neu-msg",{txt["fertig"]});}})'
            f'.catch(function(){{b.disabled=false;kbMsg("kb-neu-msg",{txt["fehler"]},true);}});}}'
            'function kbPick(b){b.setAttribute("aria-pressed",b.classList.toggle("an")?"true":"false");'
            'var k=document.getElementById("kb-start");if(!k)return;'
            'var a=document.querySelectorAll(".kb-pick.an");if(!a.length)a=document.querySelectorAll(".kb-pick");'
            'var n=0;a.forEach(function(x){n+=parseInt(x.dataset.wartend,10)||0;});k.dataset.n=n;'
            'k.textContent=(n===1?k.dataset.eins:k.dataset.viele).split("{n}").join(n);}'
            'function kbWarten(){fetch("/koerperbilder/cutter").then(function(r){return r.json();}).then(function(s){'
            'var e=document.getElementById("kb-stand");'
            'if(!s.laeuft||(e&&s.ausloeser!==e.dataset.von)){location.reload();return;}'
            'if(e&&e.dataset.txt)e.textContent=e.dataset.txt.split("{videos}").join(s.videos)'
            '.split("{offen}").join(s.videos_offen).split("{bilder}").join(s.bilder);kbMsg("kb-msg","");'
            'var g=document.getElementById("kb-balken"),f=g&&g.querySelector(".fs-fill");'
            'if(g){g.hidden=false;g.setAttribute("aria-valuenow",s.anteil);if(f)f.style.width=s.anteil+"%";}'
            'setTimeout(kbWarten,3000);})'
            f'.catch(function(){{kbMsg("kb-msg",{txt["fehler"]},true);}});}}'
            'function kbStart(b){var p=[];document.querySelectorAll(".kb-pick.an").forEach(function(x){'
            'p.push(x.dataset.person);});'
            'var n=parseInt(document.getElementById("kb-videos").value,10);'
            f'if(!(n>=1)){{kbMsg("kb-msg",{txt["zahl"]},true);return;}}b.disabled=true;kbMsg("kb-msg",{txt["laeuft"]});'
            'kbPost("/koerperbilder/cutter",{personen:p,videos:n}).then(function(d){'
            'if(d.ok){kbWarten();}else{b.disabled=false;kbNicht("kb-msg",d);}})'
            f'.catch(function(){{b.disabled=false;kbMsg("kb-msg",{txt["fehler"]},true);}});}}'
            'var kbS=document.getElementById("kb-stand");if(kbS&&kbS.dataset.laeuft==="1")setTimeout(kbWarten,3000);'
            '(function(){var p=null;try{p=sessionStorage.getItem("kbAuf");sessionStorage.removeItem("kbAuf");}'
            'catch(e){}if(!p)return;document.querySelectorAll(".kb-person").forEach(function(x){'
            'if(x.dataset.person===p&&x.getAttribute("aria-expanded")!=="true")kbAuf(x);});})();'
            '</script>')
