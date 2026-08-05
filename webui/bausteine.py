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
