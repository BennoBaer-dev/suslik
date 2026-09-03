"""Today-Bausteine (.412 T1, analysen/today_umbau_konzept.md Fassung 2 §3).

Reine Funktionen fuer den /heute-Handler in verifyd.py: sie bekommen die schon
gelesenen Daten (Szenarien, Anwesenheits-Tag, Live-Auftritte) und liefern
Entscheidungen oder kleine HTML-Stuecke. Kein Netz, kein Store, kein
Dateizugriff — deshalb im Gate ohne laufenden Dienst pruefbar (PYHEUTE412).

Warum diese Deckel (gemessen am Tester-Abzug 02.09., §1 des Konzepts): Today
trug 441 Bilder in 188 KB, 79 % davon im Durchgangs-Block — je Kamerazeile eine
ungedeckelte Chip-Wand, 317 Bilder in 140 Zeilen; das Personenband 28 Kacheln plus
6 Gruppenkacheln. Die Zahlen unten sind User- Entscheide vom 02.09. (§9): zwoelf
Personenkarten sichtbar (9.7), Durchgangs-Block gedeckelt behalten (9.2),
Stunden-Balken nur mit Anwesenheits-Datei (9.4), kein Live-Zaehler (9.5 Nachtrag).

Die Anwesenheits-Miniatur nutzt DIESELBE Zustandsregel wie /anwesenheit
(routes.anwesenheit.zustand + nacht_zustand — Deckungsvertrag, K2), aber eine
EIGENE Darstellung: 24 Stundenzellen als <span> in einer flex-Reihe, kein Pitch
der grossen Leiste (--anw-pitch bleibt in style.css bei der Leiste).
"""
import html

from core import sprache as _sp
from routes import anwesenheit as _r_anw

# User-Entscheide 02.09. (§9.7 / §3 Durchgangs-Block).
PERSONEN_SICHTBAR = 12        # Personenkarten vor dem Aufklapper "alle N Personen"
PASS_OFFEN_MAX = 3            # hoechstens so viele Durchgangszeilen starten offen
CHIPS_JE_ZEILE = 3            # Personen-Chips je Kamerazeile im Karten-Body
KAMERAZEILEN_SICHTBAR = 8     # Kamerazeilen je Body vor "alle N Kameras"
STUNDEN_JE_TAG = 24
VIERTEL_JE_STUNDE = 4         # core.anwesenheit.SLOT_S = 900 s -> 4 Zellen je Stunde
STUNDE_H = 1.0 / VIERTEL_JE_STUNDE


def deckel(liste, n):
    """-> (sichtbar, rest): die ersten n Elemente und der Rest."""
    liste = list(liste)
    return liste[:n], liste[n:]


def anw_stunden(person_eintrag, zellen):
    """24 Stunden-Zustaende 'da'/'weg'/'leer' aus den Viertelstunden einer
    Person (tag_lesen()['personen'][p]) und den Tages-Zellen (tag_lesen()
    ['zellen']). Je Stunde gilt die Nacht-Regel der grossen Leiste: rot, sobald
    eine Viertelstunde rot ist; gruen nur, wenn alle vier gruen sind."""
    person_eintrag = person_eintrag or {}
    zellen = zellen or {}
    aus = []
    for h in range(STUNDEN_JE_TAG):
        viertel = [_r_anw.zustand(zellen.get(c), person_eintrag.get(c))
                   for c in range(h * VIERTEL_JE_STUNDE, (h + 1) * VIERTEL_JE_STUNDE)]
        aus.append(_r_anw.nacht_zustand(viertel))
    return aus


def anw_dauer_h(person_eintrag):
    """'anwesend rund N h' (§3, M11): rote Viertelstunden x 0,25."""
    return len(person_eintrag or {}) * STUNDE_H


def dauer_text(h):
    """9.75 -> '9¾', 8.0 -> '8', 0.25 -> '¼' (Viertel-Bruchteile wie im Mockup)."""
    ganz = int(h)
    rest = round((h - ganz) * VIERTEL_JE_STUNDE)
    bruch = {0: "", 1: "¼", 2: "½", 3: "¾"}.get(rest, "")
    if rest == VIERTEL_JE_STUNDE:
        ganz, bruch = ganz + 1, ""
    if ganz == 0 and bruch:
        return bruch
    return f"{ganz}{bruch}"


def anw_balken_html(person_eintrag, zellen, fenster, gesamt=False):
    """Die Miniatur einer Personenkarte: 24 <span>-Zellen (Stundenaufloesung)
    plus die Dauerzeile. Zellen ausserhalb des Tagesfensters tragen hk-anw-n
    (Nacht, gedimmt). Kein Link in den Zellen — die Karte ist der eine Klick
    (K7). gesamt=True (Area-Sicht) sagt im Tooltip, dass die Miniatur
    ungefiltert ueber alle Kameras rechnet (K8)."""
    if not person_eintrag:
        return ""
    von = int((fenster or {}).get("von", 0) or 0)
    bis = int((fenster or {}).get("bis", STUNDEN_JE_TAG) or STUNDEN_JE_TAG)
    # Zwei getrennte t()-Aufrufe (kein Bedingungsausdruck IN der Klammer): der
    # Sprach-Deckungs-Scan des Gates liest Schluessel-Literale nur in der Form
    # t("…") — sonst gilt der zweite Schluessel als tot (Lauf-1-Befund .412).
    titel = _sp.t("heute.anw.title_gesamt") if gesamt else _sp.t("heute.anw.title")
    zellen_html = "".join(
        f'<span class="hk-anw-z hk-anw-{z}{" hk-anw-n" if (h < von or h >= bis) else ""}"'
        f' title="{h:02d}:00"></span>'
        for h, z in enumerate(anw_stunden(person_eintrag, zellen)))
    dauer = _sp.t("heute.anw.dauer", h=dauer_text(anw_dauer_h(person_eintrag)))
    return (f'<div class="hk-anw" title="{html.escape(titel, quote=True)}">{zellen_html}</div>'
            f'<div class="hk-anw-t">{html.escape(dauer)}</div>')


def live_personen(auftritte):
    """Live-benannte Personen des Tages aus den Auftritten.

    VERTRAG (.413): hier kommen NUR Stufe-2-Namensmeldungen herein —
    core.livewache.namens_auftritte, nicht auftritts_gruppen. Wer die rohe
    Auftrittsliste hineingibt, bekommt die Namen der Stufe-1-Schnellurteile
    mit (genau der Fehler vom 02.09.: ein Passant stand als anwesende Person
    auf Today). Die Regel selbst steht in livewache.ist_namensmeldung —
    dieses Modul kennt sie nicht und soll sie nicht kennen.

    -> {person: {"erst", "letzt", "kam", "bild", "n", "anker"}}
    (erst/letzt = Spanne aller Auftritte, kam/bild/anker vom juengsten;
    anker = dessen Beginn, die Sprungmarke nach /live_alerts)."""
    aus = {}
    for a in auftritte or []:
        p = a.get("person")
        if not p:
            continue
        ts, ts2 = float(a.get("ts") or 0), float(a.get("ts_letzte") or a.get("ts") or 0)
        e = aus.get(p)
        if e is None:
            aus[p] = {"erst": ts, "letzt": ts2, "kam": a.get("kamera") or "",
                      "bild": a.get("bild") or "", "n": 1, "anker": ts}
            continue
        e["n"] += 1
        e["erst"] = min(e["erst"], ts)
        if ts2 >= e["letzt"]:
            e["letzt"], e["kam"], e["anker"] = ts2, a.get("kamera") or e["kam"], ts
            if a.get("bild"):
                e["bild"] = a["bild"]
    return aus


def anker_ts(alle_auftritte, kamera, ts):
    """Sprungmarke fuer den Link einer nur-live-Karte -> int.

    /live_alerts zeigt die UNGEFILTERTE Tagesliste und gibt jeder Karte
    id="a<int(ts des Auftritts)>". Die Namens-Auftritte von Today sind
    gefiltert und beginnen deshalb oft SPAETER als die Karte, in der sie
    dort stecken (02.09. real: 2 von 4). Diese Funktion sucht den
    ungefilterten Auftritt derselben Kamera, der den Zeitpunkt enthaelt, und
    liefert dessen Beginn; ohne Fund den Zeitpunkt selbst (dann landet der
    Nutzer am Seitenanfang statt auf der Karte, nie auf einer falschen)."""
    for a in alle_auftritte or []:
        if a.get("kamera") != kamera:
            continue
        if float(a.get("ts") or 0) <= ts <= float(a.get("ts_letzte") or a.get("ts") or 0):
            return int(float(a.get("ts") or 0))
    return int(ts)


def live_im_pass(auftritte, start, ende):
    """Hat ein Live-Waechter WAEHREND dieses Durchgangs einen NAMEN gemeldet?
    (Zeitueberdeckung Auftritt/Durchgang, kameraunabhaengig — die Plakette
    'live' an der Durchgangszeile, §3.5.) Derselbe Vertrag wie
    live_personen: nur Stufe-2-Auftritte hineingeben."""
    for a in auftritte or []:
        if not a.get("person"):
            continue
        a0 = float(a.get("ts") or 0)
        a1 = float(a.get("ts_letzte") or a0)
        if a0 <= ende and a1 >= start:
            return True
    return False


def pass_offen(s, alarm):
    """Oeffnungsregel (§3, M3): nur Durchgaenge OHNE jede Bestaetigung mit
    ernstzunehmendem Gesicht (unbek_echt-Kriterium) oder mit ausgeloestem
    Alarm starten aufgeklappt. 'Erste Sichtung' und die Unmatched-Fussnote
    sind KEINE Kriterien (beim Tester traefen sie jede Zeile)."""
    if alarm:
        return True
    return bool(not s.get("pers") and s.get("unbek") and s.get("unbek_stark", 1) > 0)


def personen_reihenfolge(pers):
    """Personen eines Durchgangs fuer die Zeile: nach bestem Treffer, dann
    nach Stuetzenzahl (§3: 'Reihenfolge nach bestem Treffer')."""
    return sorted(pers.items(),
                  key=lambda x: (-(x[1].get("best") or 0), -(x[1].get("count") or 0), x[0]))


def plus_html(namen):
    """'+N' hinter gedeckelten Avataren/Chips; die Namen stehen im Tooltip."""
    if not namen:
        return ""
    return (f'<span class="hk-plus" title="{html.escape(", ".join(namen), quote=True)}">'
            f'+{len(namen)}</span>')
