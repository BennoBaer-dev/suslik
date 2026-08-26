"""Quer genutzte HTML-Bausteine (M0, Modul-Konzept: "Helfer ohne Heimat") — hierher
ziehen Helfer, die MEHRERE Seiten brauchen, BEVOR die Seiten selbst umziehen (loest
die Import-Zyklen). Kontrakt wie auftritte.py: Funktionen bekommen Daten als
Parameter, importieren nie den Dienst zurueck. verifyd.py re-exportiert die Namen
(Kompatibilitaet fuer qs/Seiten), bis die Konsumenten in M1 umgezogen sind.
Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t() — BYTE-TREU (Harnisch tools/harnisch_sprache.py). Tranche D:
die Kategorie-/Wortstufen-/Reihen-ANZEIGE laeuft ueber die Kennung->t()-Maps
unten (kat_wort/kat_map, stufe_wort, reihen_wort); KAT_LABELS bleibt die
englische Quelle (Fallback + EN-Deckungsvertrag), KAT_FARBE ist keine
Sprache, "?" ist sprachneutrale Interpunktion (§8.6). Stufe 4 (20.08.):
die Meldetexte lesen jetzt ebenfalls hier (kat_wort) bzw. ueber
core/vertrauen.label_sprachig (stufe_wort ist nur noch der UI-Name)."""
import html
import re

from core.sprache import t


def gt_leiste(eid, schnell, andere, cur="", vorschlag=None):
    """Ground-Truth-Leiste als MENGE (.313, Tester-Fund 'C+R'): die Personen-Knoepfe sind
    SCHALTER (an = gruen, nochmal tippen = aus), kein Kombi-Knopf aus Initialen mehr.
    Aufbau: optionaler Uebernehmen-Knopf mit den VOLLEN Namen des suslik-Vorschlags
    (`vorschlag` = bestaetigte Personen der Zeile; ein Klick, auch bei drei Namen) ·
    ein Schalter je Schnell-Person (haeufigste Namen) plus je Person, die in DIESER
    Zeile schon gewaehlt ist · 'Stranger' als Mitglied · '?' und 'No person' exklusiv
    (leeren die Menge) · 'add person…' ergaenzt aus dem Dropdown statt zu ersetzen.
    cur: Liste der gewaehlten Werte (neu) oder ein Alt-Label-String (wird gespalten
    wie szenarien.gt_personen_aus_label ohne Master: '+'-Strings bleiben opak).
    Die Leiste traegt ihren Zustand in data-personen (JSON); app.js gtT() schaltet,
    POSTet die Menge und malt die Klassen nach der Antwort des Dienstes."""
    import json as _json
    from szenarien import GT_KEIN_MENSCH, GT_OFFEN_LABELS, gt_personen_aus_label
    if isinstance(cur, (list, tuple, set)):
        gew = sorted(str(x) for x in cur if str(x))
    else:
        gew = gt_personen_aus_label(cur, set(schnell) | set(andere))
    gew_set = set(gew)
    reserviert = set(GT_OFFEN_LABELS) | {GT_KEIN_MENSCH}
    bekannt = set(schnell) | set(andere)
    # Werte, die der Dienst (gt_pruefen) nicht annimmt — opake Alt-Kombis, inzwischen
    # geloeschte Personen — werden NICHT als Schalter angeboten (ein toter Klick saehe aus
    # wie ein Erfolg), sondern als stiller Hinweis; Umschalten auf '?' oder einen Namen
    # ersetzt sie. (Widerleger .313)
    opak = [p for p in gew if p not in bekannt and p not in reserviert]
    sichtbar = list(schnell) + [p for p in gew if p not in schnell and p in bekannt]
    e_eid = html.escape(eid, quote=True)

    def knopf(wert, text, titel="", an=False):
        # eid kommt aus data-eid der Leiste (nie in den JS-Quelltext interpoliert)
        return (f'<button class="gtb{" on" if an else ""}" data-gt="{html.escape(wert, quote=True)}" '
                + (f'title="{html.escape(titel, quote=True)}" ' if titel else "")
                + f'onclick="gtT(this)">{html.escape(text)}</button>')
    b = ""
    vs = [str(p) for p in (vorschlag or []) if str(p) and str(p) in bekannt]
    if vs and not gew_set:
        b += (f'<button class="gtb gt-ok" data-gt-alle="{html.escape(_json.dumps(vs), quote=True)}" '
              f'title="{html.escape(t("baustein.gt.uebernehmen"), quote=True)}" '
              f'onclick="gtAlle(this)">&#10003; {html.escape(', '.join(vs))}</button>')
    for p in opak:
        b += f'<span class="gtb gt-opak" title="{html.escape(t("baustein.gt.opak_titel"), quote=True)}">{html.escape(p)}</span>'
    for p in sichtbar:
        b += knopf(p, p, "", p in gew_set)
    b += knopf(GT_OFFEN_LABELS[0], t("baustein.gt.fremd"), t("baustein.gt.fremd_titel"),
               GT_OFFEN_LABELS[0] in gew_set)
    b += knopf(GT_OFFEN_LABELS[1], "?", t("baustein.gt.unklar_titel"), GT_OFFEN_LABELS[1] in gew_set)
    b += knopf(GT_KEIN_MENSCH, t("baustein.gt.kein_mensch"), t("baustein.gt.kein_mensch_titel"),
               GT_KEIN_MENSCH in gew_set)
    rest = [p for p in andere if p not in gew_set]
    if rest:
        opts = "".join(f"<option>{html.escape(p)}</option>" for p in rest)
        b += (f'<select class="gtb" onchange="if(this.value){{gtT(this,this.value);}}">'
              f'<option value="">{t("baustein.gt.add")}</option>{opts}</select>')
    return (f'<span class="gtl" data-eid="{e_eid}" '
            f'data-personen="{html.escape(_json.dumps(gew), quote=True)}">{b}'
            f'<span class="gt-msg dim" style="font-size:11px"></span></span>')


def bild_nn(name):
    """Match-Score aus einem analyze-Bildnamen ('<label>_best_<Person>_NN0.52_t7s.jpg',
    '<label>_show_<Person>_NN0.52.jpg'). Enrollment-Crops ('_enroll_') tragen keinen -> None."""
    m = re.search(r"_NN(-?\d+(?:\.\d+)?)", name)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def fehler_grund(log_pfad, n=220):
    """Ursache eines Fehler-Events aus seinem analyze.log — die EINE Quelle fuer die
    Event-Seite UND die Pass-Seite (Widerleger 11.08.: vorher beantworteten drei
    Stellen dieselbe Frage verschieden, und beide UI-Stellen zeigten an den echten
    Fehler-Events Nachspann statt Ursache — die letzte Log-Zeile ist systematisch
    Telemetrie/Zusammenfassung, nie der Fehler; Trefferquote 0/3).
    Rangfolge: letzte FEHLER-Zeile (analyze.py schreibt die Ursache so) -> letzte
    verifyd-Zeile OHNE das Telemetrie-Muster 'cpu_s=' (worker-Fehlerpfad) -> letzte
    nicht-leere Zeile als Rueckfall. Kappung VORN behalten ([:n]) — der Fehlertyp
    steht am Anfang (fehler_kern-Lehre aus Issue #18). Nicht druckbare Zeichen
    werden ersetzt (Binaermuell landet sonst in der Seite). Leerer String, wenn es
    nichts Lesbares gibt — der Aufrufer zeigt seinen ehrlichen Fallback. Wirft nie
    (Grund-Zeile ist Komfort, nie ein Seitenkiller)."""
    try:
        with open(log_pfad, encoding="utf-8", errors="replace") as f:
            zeilen = [z.strip() for z in f if z.strip()]
    except Exception:
        return ""
    kand = ""
    for z in zeilen:
        if z.startswith("FEHLER"):
            kand = z
    if not kand:
        for z in zeilen:
            if z.startswith("verifyd") and "cpu_s=" not in z:
                kand = z
    if not kand:
        # Rueckfall: letzte nicht-leere Zeile, die KEINE Telemetrie ist — sonst
        # reproduziert der Rueckfall exakt das Blocker-Muster (Nachspann als Grund).
        # Nur-Telemetrie-Logs liefern "" -> der Aufrufer zeigt seinen ehrlichen Text.
        for z in zeilen:
            if "cpu_s=" not in z:
                kand = z
    kand = "".join(ch if ch.isprintable() or ch == " " else " " for ch in kand)
    if kand.startswith("verifyd: "):
        kand = kand[len("verifyd: "):]     # Praefix-Doppelung auf der Pass-Seite vermeiden
    return kand[:n]


# --- Kategorie-ANZEIGE-Tabellen (Modulumbau R1: aus verifyd.py hierher, die
# Helfer-Heimat-Regel von oben; verifyd re-exportiert wie gt_leiste) ---------
# Stufe 2 Tranche D (§8.13, Muster live.GRUPPEN): die UI-ANZEIGE laeuft jetzt
# ueber kat_wort()/kat_map() (Kennung->t()-Map unten, Funktion statt Konstante
# wegen §8.12). KAT_LABELS selbst BLEIBT die englische zentrale Quelle: sie
# ist der Fallback von kat_wort() und der EN-Deckungs-Vertrag der
# baustein.kat.*-Schluessel (en.py-Werte wortgleich, Beweis Tranche D).
# Sprach-Stufe 4 (20.08.): auch der Push-TITEL liest jetzt ueber kat_wort()
# (Schluessel meldung.titel.kategorie) — kein direkter KAT_LABELS-Leser mehr.
# Kategorie-Slugs -> englische ANZEIGE-Labels (nur UI). Die Slugs selbst bleiben deutsch,
# weil sie Datenwerte sind (deckung.jsonl, MQTT-Payload, Log, Filter-value). v2 = aktive
# Achse (Events-Badge); v1 = Frigate-Vergleich, degeneriert, nur bei Altdaten noch im Filter.
KAT_LABELS = {
    "erkannt": "Recognized", "fremd_verdacht": "Stranger?",
    "unbekannt_schwach": "Unknown (weak)", "fehler": "Error",
    "no_person": "No person found (likely false trigger)",
    "uebersprungen": "Skipped at startup",
    "deckung": "Match", "widerspruch": "Conflict", "frigate_nur": "Frigate only",
    "wir_nur": "suslik only", "beide_unknown": "Both unknown",
}

# Plakettenfarben je Kategorie — EINE Tabelle. Sie stand bisher wortgleich an zwei Stellen
# (Event-Detail + Ereignisliste); genau so laufen solche Werte auseinander.
# Drei Werte sind am 25.07. nachgerechnet und abgedunkelt worden: die Plaketten tragen weissen
# Text (.k in style.css), und bei 12 px verlangt WCAG AA 4,5:1. Gemessen waren "Recognized"
# 3,00:1 (die HAEUFIGSTE Plakette im ganzen UI), "Frigate only" 2,94:1 und "suslik only" 3,79:1.
# Der Farbton bleibt erkennbar derselbe, nur dunkler: #2a6->#1b8650 (4,59), #c83->#a16b28 (4,52),
# #38c->#2e7ab8 (4,57). Die uebrigen lagen bereits darueber (#c33 5,14 · #666 5,74 · #a3a 5,58).
# Das gilt in BEIDEN Modi gleich — es war nie ein Hellmodus-Problem, sondern immer zu schwach.
#
# ROT HAT GENAU EINE BEDEUTUNG (User-Entscheid 25.07.): "jemand muss jetzt hinsehen".
# Das ist ausschliesslich `fremd_verdacht`. Vorher trug Rot auch `widerspruch` — und
# Widersprueche sind haeufig: von 144 fremd_verdacht-Faellen lagen 118 in einem Durchgang, in
# dem dieselbe Person anderswo bestaetigt war. Wer Rot so oft sieht, lernt es als Rauschen und
# uebersieht den einen echten Fall.
# Fuenf Farben, sechs Bedeutungen — die Unterscheidung innerhalb einer Klasse traegt der TEXT,
# nicht ein weiterer Farbton ("Frigate only" gegen "suslik only" sind beide informativ):
#   gruen    Einigkeit / erkannt          rot     Fremder — hinsehen
#   bernstein pruefenswert (Widerspruch)  lila    Dienstfehler
#   blau     informativer Unterschied     grau    nichts bekannt
# Alle Werte tragen weisse Schrift (.k) und liegen ueber WCAG AA 4,5:1, nachgerechnet.
KAT_FARBE = {
    "deckung": "#1b8650",          # 4,59  Einigkeit
    "erkannt": "#1b8650",          # 4,59  erkannt
    "fremd_verdacht": "#c33",      # 5,14  ROT — der einzige Fall, der Aufmerksamkeit will
    "widerspruch": "#a16b28",      # 4,52  bernstein: pruefen, aber kein Vorfall
    "frigate_nur": "#2e7ab8",      # 4,57  blau: informativer Unterschied
    "wir_nur": "#2e7ab8",          # 4,57  blau: derselbe Fall spiegelverkehrt, Text unterscheidet
    "beide_unknown": "#666",       # 5,74  grau
    "unbekannt_schwach": "#666",   # 5,74  grau
    "no_person": "#666",           # 5,74  grau: bewusst KEIN Rot — "hier war wohl niemand"
    "uebersprungen": "#666",       # 5,74  grau: keine Aussage ueber Personen (nie analysiert)
    "fehler": "#a3a",              # 5,58  lila: Dienstfehler, keine Aussage ueber Personen
}


# --- Kennung->Anzeige-Maps (Stufe 2 Tranche D, §8.13 Muster live.GRUPPEN) ---
# Funktionen statt Konstanten (§8.12: t() nie auf Modulebene). Die Kennungen
# bleiben Daten-/Speicherwerte; NUR die UI-Darstellung wird sprachfaehig.
# KAT_FARBE bleibt unberuehrt (Farben sind keine Sprache).

def kat_map():
    """Kategorie-Kennung -> uebersetztes Anzeige-Label, als dict fuer
    Konsumenten mit Tabellen-Vertrag (routes/benachrichtigungen.render).
    Deckungs-Vertrag: Schluesselmenge == KAT_LABELS (englische Quelle +
    Meldetext-Tabelle der Stufe 4, unveraendert)."""
    return {"erkannt": t("baustein.kat.erkannt"),
            "fremd_verdacht": t("baustein.kat.fremd_verdacht"),
            "unbekannt_schwach": t("baustein.kat.unbekannt_schwach"),
            "fehler": t("baustein.kat.fehler"),
            "no_person": t("baustein.kat.no_person"),
            "uebersprungen": t("baustein.kat.uebersprungen"),
            "deckung": t("baustein.kat.deckung"),
            "widerspruch": t("baustein.kat.widerspruch"),
            "frigate_nur": t("baustein.kat.frigate_nur"),
            "wir_nur": t("baustein.kat.wir_nur"),
            "beide_unknown": t("baustein.kat.beide_unknown")}


def kat_wort(kat):
    """Anzeige-Label EINER Kategorie-Kennung; unbekannte Kennung zeigt sich
    selbst (ehrlich statt leer, §8.19)."""
    return kat_map().get(kat, KAT_LABELS.get(kat, kat))


def stufe_wort(st):
    """UI-Wort einer Vertrauens-Stufe (core/vertrauen.STUFEN).
    Sprach-Stufe 4: die Aufloesung ist nach core/vertrauen.label_sprachig()
    gewandert — der MELDEWEG (core/livewache, verifyd-Push) braucht sie
    ebenfalls und darf webui/* nicht importieren; zwei Listen derselben
    vier Schluessel waeren ein verstreutes Literal (K3-Regel). Diese
    Funktion bleibt der UI-Name derselben EINEN Quelle.
    LOGS nutzen weiter core/vertrauen.label() — englisch (B20)."""
    from core import vertrauen as _vt
    return _vt.label_sprachig(st)


def reihen_wort(kennung):
    """Anzeige-Wort einer Galerie-Reihen-Kennung (vorn/seitlich/hinten/
    unklar aus core/visiongalerie). Kennung bleibt Store-/JSON-Wert;
    Fallback ist die englische zentrale Quelle REIHEN_ANZEIGE bzw. die
    Kennung selbst (§8.19)."""
    m = {"vorn": t("visiongalerie.reihe.vorn"),
         "seitlich": t("visiongalerie.reihe.seitlich"),
         "hinten": t("visiongalerie.reihe.hinten"),
         "unklar": t("visiongalerie.reihe.unklar")}
    w = m.get(kennung)
    if w is not None:
        return w
    from core.visiongalerie import REIHEN_ANZEIGE   # import-frei, kein Zyklus
    return REIHEN_ANZEIGE.get(kennung, kennung)


def bruecke_grund(dg):
    """D1 (.30x, User-Fund 20.08.): der DOMINANTE Ausschlussgrund einer
    Pass-Pruefung als Satzteil MIT ZAHLEN — Kennung->Anzeige wie kat_wort/
    reihen_wort, hier fuer die Kennungen aus anlernen.diagnose_dominant.
    Kennungen, Zaehler UND Schwellen kommen fertig aus der Diagnose
    (anlernen.vorschlaege_person, Latte = core/benennung.REF_LATTE): hier
    wird nichts nachgerechnet und keine Schwelle wiederholt (K3-Regel).
    -> Satz|None; None heisst 'nichts zu erklaeren' — dann bleibt der
    Aufrufer bei seinem Pauschal-Satz (§8.19: nie ein erfundenes Wort)."""
    if not dg:
        return None

    def _z(x):
        return "?" if x is None else str(int(x))

    kennung = str(dg.get("dominant") or "")
    n = int((dg.get("klassen") or {}).get(kennung, 0))
    person = str(dg.get("person") or "")
    if kennung == "zu_klein":
        return t("antwort.bruecke_grund_zu_klein", n=n,
                 kante=_z(dg.get("kante_max")), min_kante=_z(dg.get("min_kante")))
    if kennung == "zu_unscharf":
        return t("antwort.bruecke_grund_zu_unscharf", n=n,
                 sharp=_z(dg.get("sharp_max")),
                 unscharf_max=_z(dg.get("unscharf_max")))
    if kennung == "kein_gesicht":
        return t("antwort.bruecke_grund_kein_gesicht", n=n)
    if kennung == "gedeckt":
        return t("antwort.bruecke_grund_gedeckt", n=n, person=person)
    if kennung == "fremd_naeher":
        return t("antwort.bruecke_grund_fremd_naeher", n=n, person=person)
    if kennung == "id_unsicher":
        return t("antwort.bruecke_grund_id_unsicher", n=n, person=person)
    if kennung == "beides_schwach":
        return t("antwort.bruecke_grund_beides_schwach", n=n)
    if kennung == "kein_crop":
        return t("antwort.bruecke_grund_kein_crop",
                 n=int(dg.get("events") or 0))
    if kennung == "keine_events":
        return t("antwort.bruecke_grund_keine_events", person=person)
    if kennung == "keine_referenzen":
        return t("antwort.bruecke_grund_keine_referenzen", person=person)
    return None


def lauffluss_stil():
    """Das Lauf-Design (.246/.259/.271, Mockup-Abnahmen 17.-18.08.) als EINE
    Quelle — Vier-Kachel-Fluss, Fortschritts-Saeule, gruener Suchknopf mit
    Einstellungs-Popup, Zuweisungs-Flaeche, Verwerfen-Knopf.

    Es gab dieses Blatt bis 20.08. nur inline in routes/lernwizard.py. Als der
    Koerper-Lernlauf (/personlauf) auf dasselbe Design gehoben wurde, waere die
    Alternative ein zweites, wortgleiches CSS-Blatt gewesen — genau das
    verstreute Zweit-Literal, das die K3-Regel verbietet (eine Feinjustage am
    einen Blatt liesse das andere still zuruecklaufen). Deshalb wohnt es hier:
    beide Lauf-Seiten rendern DIESELBEN Klassen aus DERSELBEN Quelle.
    Byte-Vertrag: der Rueckgabestring ist Zeichen fuer Zeichen der alte
    lernwizard-`stil` (Beweis tools/harnisch_sprache.py, Fall lernwizard).
    Enthaelt keine Sprache — nur Klassen und Masse (nichts einzuziehen).

    Geometrie (S9-Klasse): alle Breiten relativ bzw. mit Umbruch —
    .lf-fluss faellt 4 -> 2 -> 1 Spalte, .lf-pop ist min(440px,92vw),
    Kachel-Inhalte flexen; nichts erzwingt eine Mindestbreite."""
    return ('<style>.phok{color:seagreen;font-weight:bold}'
            '.phz{margin:2px 0}.phdet{margin:0 0 4px 1.4em;font-size:.9em}'
            # .246: Vier-Kachel-Fluss + Saeule + Zuweisungs-Flaeche (Mockup
            # b_lernfluss, User-Abnahme 17.08.)
            '.lf-fluss{display:grid;grid-template-columns:repeat(4,1fr);'
            'gap:14px;margin:14px 0}'
            '@media(max-width:1000px){.lf-fluss{grid-template-columns:1fr 1fr}}'
            '@media(max-width:560px){.lf-fluss{grid-template-columns:1fr}}'
            '.lf-k{position:relative;background:var(--surface);'
            'border:1px solid var(--border);border-radius:12px;'
            'padding:14px 14px 12px;min-height:220px;display:flex;'
            'flex-direction:column;gap:7px}'
            '.lf-k.dran{border-color:var(--accent);'
            'box-shadow:0 0 0 1px var(--accent)}'
            '.lf-k.folgt{opacity:.45}'
            '.lf-k.fertig{border-color:seagreen}'
            '.lf-k h3{margin:0;font-size:15px;display:flex;align-items:center;gap:8px}'
            '.lf-k .nr{width:23px;height:23px;border-radius:50%;'
            'background:var(--border);display:grid;place-items:center;'
            'font-size:12px;font-weight:bold;flex:0 0 23px}'
            '.lf-k.dran .nr{background:var(--accent);color:#fff}'
            '.lf-k.fertig .nr{background:seagreen;color:#fff}'
            '.lf-satz{font-size:13.5px;color:var(--dim);margin:0}'
            '.lf-rest{margin-top:auto}'
            '.lf-saeule-w{display:flex;gap:12px;align-items:stretch;flex:1}'
            '.lf-saeule{width:32px;height:150px;border:1px solid var(--border);'
            'border-radius:8px;position:relative;overflow:hidden;'
            'background:var(--bg);flex:0 0 32px;align-self:flex-end}'
            '.lf-saeule .fuell{position:absolute;bottom:0;left:0;right:0;'
            'background:linear-gradient(180deg,var(--accent),seagreen)}'
            '.lf-saeule .marke{position:absolute;left:0;right:0;'
            'border-top:1px dashed var(--border)}'
            '.lf-phasen{display:flex;flex-direction:column-reverse;'
            'justify-content:space-between;font-size:12.5px;height:150px;'
            'align-self:flex-end;padding:2px 0}'
            '.lf-phasen div{display:flex;gap:6px;align-items:center;color:var(--dim)}'
            '.lf-phasen .an{color:var(--text);font-weight:bold}'
            '.lf-phasen .ok{color:seagreen}'
            '.lf-puls{display:inline-block;width:8px;height:8px;'
            'border-radius:50%;background:var(--accent);'
            'animation:lfpu 1.2s infinite}'
            '@keyframes lfpu{50%{opacity:.25}}'
            '.lf-q{display:flex;flex-wrap:wrap;gap:6px;margin:2px 0}'
            '.lf-q a{position:relative;display:block;width:44px;height:44px}'
            '.lf-q img{width:44px;height:44px;object-fit:cover;border-radius:8px;'
            'border:1px solid var(--border)}'
            '.lf-q .jetzt img{outline:2px solid var(--accent);outline-offset:2px}'
            '.lf-q .done::after{content:"\\2713";position:absolute;inset:0;'
            'display:grid;place-items:center;background:#1f7a5fd9;color:#fff;'
            'border-radius:8px;font-size:18px}'
            '.lf-q .skip::after{content:"\\2013";position:absolute;inset:0;'
            'display:grid;place-items:center;background:#555c66d9;color:#fff;'
            'border-radius:8px;font-size:18px}'
            '.lf-zw{background:var(--surface);border:1px solid var(--accent);'
            'border-radius:12px;box-shadow:0 0 0 1px var(--accent);'
            'padding:14px 16px;margin:0 0 16px}'
            '.lf-zw h3{margin:0 0 2px;font-size:16px}'
            '.lf-zwg{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px}'
            '.lf-zwg label{position:relative;display:block;cursor:pointer}'
            '.lf-zwg input{position:absolute;top:4px;left:4px;z-index:2}'
            '.lf-zwg img{width:84px;height:84px;object-fit:cover;border-radius:8px}'
            '.lf-zwg input:not(:checked)+img{opacity:.4}'
            '.lf-zwg input:checked+img{outline:2px solid var(--accent);'
            'outline-offset:2px}'
            # .258: Pfeil INS Bild gelegt (top statt bottom) — seit die
            # Grund-Zeile unter dem Bild haengt, ueberlappte er sie.
            '.lf-zwclip{position:absolute;right:4px;top:62px;font-size:11px;'
            'background:var(--surface);border-radius:4px;padding:0 4px;'
            'text-decoration:none}'
            # .257: Pruef-Rahmen — gut=seagreen (angehakt), Grenzfall=goldenrod
            # (abgehakt, wieder anhakbar wie im Bruecken-Overlay), raus
            # gedimmt mit Grund.
            '.lf-zwg .lf-neu input:checked+img{outline-color:seagreen}'
            '.lf-zwg .lf-grenz input:checked+img{outline-color:goldenrod}'
            '.lf-zwg .lf-grenz .lf-zwgrund{color:goldenrod}'
            '.lf-zwg .lf-dup img{opacity:.3}'
            '.lf-zwgrund{display:block;max-width:84px;font-size:10px;'
            'color:var(--dim);line-height:1.2;padding-top:2px}'
            '.lf-knoepfe{display:flex;gap:8px;flex-wrap:wrap;align-items:center}'
            # .258: gesperrter Take-Knopf (0 Haken) sieht auch gesperrt aus.
            '.lf-knoepfe button.gtb:disabled{opacity:.45;cursor:default;'
            'filter:grayscale(.6)}'
            # .259 (Mockup b_suchknopf, Variante A): grosser gruener
            # Suchknopf, Einstellungs-Popup, Delete rechtsbuendig rot umrandet.
            '.lf-such{display:block;width:100%;margin-top:auto;'
            'padding:13px 14px;font-size:15.5px;font-weight:600;'
            'border-radius:9px;cursor:pointer;text-align:center;'
            'background:var(--ok);border:1px solid var(--ok);'
            'color:var(--on-ink)}'
            '.lf-such small{display:block;font-weight:400;font-size:12px;'
            'opacity:.85;margin-top:2px}'
            '.lf-such:hover{filter:brightness(1.08)}'
            '.lf-deck{position:fixed;inset:0;background:#000a;display:none;'
            'place-items:center;z-index:9}'
            '.lf-pop{background:var(--surface);'
            'border:1px solid var(--border-strong,var(--border));'
            'border-radius:12px;padding:18px 20px;width:min(440px,92vw);'
            'box-shadow:0 12px 40px #000a;text-align:left;font-weight:400}'
            '.lf-pop h3{margin:0 0 4px}'
            '.lf-popz{margin:12px 0;font-size:14px;display:flex;'
            'align-items:center;gap:8px;flex-wrap:wrap}'
            '.lf-hint{color:var(--dim);font-size:12px;flex-basis:100%}'
            '.lf-popf{display:flex;gap:8px;margin-top:16px;'
            'align-items:center}'
            '.lf-spacer{flex:1}'
            # .271/.271b: Blickwinkel-Kaesten mit Rahmen + Legende
            '.lf-blickbox{border:1px solid var(--border-strong,var(--border));'
            'border-radius:10px;padding:6px 10px 10px;margin:10px 0}'
            '.lf-blickbox legend{font-weight:600;font-size:13px;'
            'padding:0 6px}'
            '.lf-blickbox.lf-leer{opacity:.6}'
            '.lf-del{background:transparent;border:1px solid var(--crit);'
            'color:var(--crit);border-radius:6px;padding:6px 12px;'
            'cursor:pointer}'
            '.lf-del:hover{background:var(--crit);color:#fff}'
            '</style>')


def js_literal(wert):
    """Uebersetzten Text als EINFACH-quotiertes JS-String-Literal einbetten
    (Tranche D, §8.4): fuer Inline-JS-Kontexte, in denen json.dumps mit
    seinen Doppel-Quotes die Byte-Treue braeche (onclick-Attribute,
    einfach-quotierte Scripts). ASCII-Text laeuft byte-identisch durch;
    Backslash/Quote werden escapet, '"', <>&, Steuer- und Nicht-ASCII-
    Zeichen als \\uXXXX (attribut- und script-sicher, §8.21-nbsp inkl.)."""
    aus = []
    for ch in str(wert):
        o = ord(ch)
        if ch == "\\":
            aus.append("\\\\")
        elif ch == "'":
            aus.append("\\'")
        elif ch in '"<>&' or o < 32 or o > 126:
            aus.append("\\u%04x" % o)
        else:
            aus.append(ch)
    return "'" + "".join(aus) + "'"
