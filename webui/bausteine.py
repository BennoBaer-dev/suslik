"""Quer genutzte HTML-Bausteine (M0, Modul-Konzept: "Helfer ohne Heimat") — hierher
ziehen Helfer, die MEHRERE Seiten brauchen, BEVOR die Seiten selbst umziehen (loest
die Import-Zyklen). Kontrakt wie auftritte.py: Funktionen bekommen Daten als
Parameter, importieren nie den Dienst zurueck. verifyd.py re-exportiert die Namen
(Kompatibilitaet fuer qs/Seiten), bis die Konsumenten in M1 umgezogen sind."""
import html
import re


def gt_leiste(eid, schnell, andere, cur=""):
    """Ground-Truth-Buttonleiste: dynamische Schnell-Personen + Kombi (bei >=2) + Stranger + ? +
    'other…'-Dropdown. cur='' (Default) = ungelabelt (Review-Liste), sonst Highlight des Labels."""
    knoepfe = [(p, p) for p in schnell]
    if len(schnell) >= 2:
        knoepfe.append(("+".join(schnell[:2]), "+".join(p[:1] for p in schnell[:2])))
    from szenarien import GT_KEIN_MENSCH, GT_OFFEN_LABELS   # EINE Quelle fuer die
    knoepfe += [(GT_OFFEN_LABELS[0], "Stranger"),   # Speicherwerte (Review .54: Anzeige-
                (GT_OFFEN_LABELS[1], "?"),          # Text und Speicherwert waren
                (GT_KEIN_MENSCH, "No person")]      # verwechselt; Issue #16: Fehlausloeser
                                                    # per Klick beurteilen und schliessen
    b = "".join(f'<button class="gtb{" on" if cur == lb else ""}" '
                f"onclick=\"gt('{eid}','{html.escape(lb, quote=True)}',this)\">{html.escape(txt)}</button>"
                for lb, txt in knoepfe)
    if andere:
        opts = "".join(f'<option{" selected" if cur == p else ""}>{html.escape(p)}</option>'
                       for p in andere)
        # Das Gruen war ein ZUSTANDSSIGNAL ("aus dieser Liste wurde etwas gewaehlt"), nicht Deko —
        # es bleibt erhalten, nur ueber dieselbe Klassen-Konvention wie die Knoepfe daneben
        # (.gtb / .gtb.on) statt ueber eine feste Farbe. Vorher trug es zusaetzlich ein hartes
        # #333 fuer den Normalfall und war damit im Hellmodus unlesbar.
        b += (f'<select class="gtb{" on" if cur in andere else ""}" '
              f"onchange=\"if(this.value)gt('{eid}',this.value,this)\">"
              f'<option value="">other…</option>{opts}</select>')
    return b


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
# Kategorie-Slugs -> englische ANZEIGE-Labels (nur UI). Die Slugs selbst bleiben deutsch,
# weil sie Datenwerte sind (deckung.jsonl, MQTT-Payload, Log, Filter-value). v2 = aktive
# Achse (Events-Badge); v1 = Frigate-Vergleich, degeneriert, nur bei Altdaten noch im Filter.
KAT_LABELS = {
    "erkannt": "Recognized", "fremd_verdacht": "Stranger?",
    "unbekannt_schwach": "Unknown (weak)", "fehler": "Error",
    "no_person": "No person found (likely false trigger)",
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
    "fehler": "#a3a",              # 5,58  lila: Dienstfehler, keine Aussage ueber Personen
}
