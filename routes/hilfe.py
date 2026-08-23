"""routes/hilfe — In-App-Anleitungen je Erkennungs-Kachel (.208, User 16.08.).

Je Weg EINE Seite mit zwei Tiefen: der Basis-Text ist fuer JEDEN Leser da,
der Zusatz-Block erscheint nur im Expert-Modus — Expert ist bewusst
"Easy plus" (mehr Tiefe, gleiche Sprache), kein Techniker-Text: keine
Modellnamen, keine Schwellen-Zahlen, kein Fachjargon (User-Auflage 16.08.,
alle Texte durch den Humanizer-Lauf). Anleitungen leben IN suslik, nicht
auf GitHub.

Sprach-Stufe 3: die Basis-Texte liegen als hilfe.*-Schluessel in
core/texte/<code>.py — Titel via t(), je <p>-Absatz EIN t_html-Schluessel
(B9-Granularitaet; das <p> liegt im Wert, HTML_SCHLUESSEL-Vertrag in
core/sprache.py). Der Rueck-Link ist je Ziel ein GANZER Schluessel
("Back to {ziel}" ist das B9-Anti-Beispiel aus konzept_sprache.md §4.0).

Injektion pur: reines Rendern, kein Zustand, importiert verifyd nie."""
import html

from core.sprache import t, t_html


def _seiten():
    """weg -> (Titel, Absatz-Liste, Rueckweg oder None=/erkennung).
    Funktion statt Konstante (§8.12: t() nie auf Modulebene). Reihenfolge
    == Schluessel-Reihenfolge im hilfe-Abschnitt von core/texte/en.py."""
    return {
        "live": (t("hilfe.live.titel"),
                 [t_html("hilfe.live.satz1"), t_html("hilfe.live.satz2"),
                  t_html("hilfe.live.satz3"), t_html("hilfe.live.satz4"),
                  t_html("hilfe.live.satz5")], None),
        "gesicht": (t("hilfe.gesicht.titel"),
                    [t_html("hilfe.gesicht.satz1"),
                     t_html("hilfe.gesicht.satz2"),
                     t_html("hilfe.gesicht.satz3"),
                     t_html("hilfe.gesicht.satz4"),
                     t_html("hilfe.gesicht.satz5"),
                     t_html("hilfe.gesicht.satz6")], None),
        "koerper": (t("hilfe.koerper.titel"),
                    [t_html("hilfe.koerper.satz1"),
                     t_html("hilfe.koerper.satz2"),
                     t_html("hilfe.koerper.satz3"),
                     t_html("hilfe.koerper.satz4")], None),
        "vision": (t("hilfe.vision.titel"),
                   [t_html("hilfe.vision.satz1"),
                    t_html("hilfe.vision.satz2"),
                    t_html("hilfe.vision.satz3"),
                    t_html("hilfe.vision.satz4")], None),
        # .221: die vier Faces-Anleitungen (User-Abnahme 16.08. abends, "ok"
        # auf die deutschen Entwuerfe). zurueck=/faces statt /erkennung.
        "faces_bekannt": (t("hilfe.faces_bekannt.titel"),
                          [t_html("hilfe.faces_bekannt.satz1"),
                           t_html("hilfe.faces_bekannt.satz2"),
                           t_html("hilfe.faces_bekannt.satz3")], "/faces"),
        "faces_lernen": (t("hilfe.faces_lernen.titel"),
                         [t_html("hilfe.faces_lernen.satz1"),
                          t_html("hilfe.faces_lernen.satz2"),
                          t_html("hilfe.faces_lernen.satz3")], "/faces"),
        "faces_unbekannt": (t("hilfe.faces_unbekannt.titel"),
                            [t_html("hilfe.faces_unbekannt.satz1"),
                             t_html("hilfe.faces_unbekannt.satz2")],
                            "/faces"),
        "faces_qualitaet": (t("hilfe.faces_qualitaet.titel"),
                            [t_html("hilfe.faces_qualitaet.satz1"),
                             t_html("hilfe.faces_qualitaet.satz2")],
                            "/faces"),
        # .244: Lernlauf-Anleitung (vier Saetze vom User 17.08. pauschal
        # gebilligt, "passt") — verlinkt von /lernlauf, Rueckweg dorthin.
        "faces_lernlauf": (t("hilfe.faces_lernlauf.titel"),
                           [t_html("hilfe.faces_lernlauf.satz1"),
                            t_html("hilfe.faces_lernlauf.satz2"),
                            t_html("hilfe.faces_lernlauf.satz3"),
                            t_html("hilfe.faces_lernlauf.satz4")],
                           "/lernlauf"),
    }


# Easy-plus-Bloecke ("mehr", Expert-Tiefe): abgestimmter Bestand vom 16.08.,
# per User-Entscheid (16.08. spaeter Vormittag) bewusst NICHT gerendert —
# ERSTMAL NUR die Easy-Fassung; nichts hiervon erscheint heute im UI.
# Deshalb Stufe-3-Grenze: NICHT auf der Sprachschicht (ungenutzte Schluessel
# waeren im Deckungs-Gate tot) — der Einzug als hilfe.<weg>.mehrN-Schluessel
# erfolgt im selben Zug wie der Easy-plus-Bau, der sie rendert.
MEHR = {
    "live": """
<p>How the name forms: the watcher checks every usable face it sees during a
pass and counts how often the same person wins. Two hits in a row for the same
name trigger the preliminary alert. One odd frame is never enough, but two
are, which is why a name can flicker in rare cases. The alert always says
preliminary.</p>
<p>If a camera delivers more pictures than your machine can process, the
watcher skips frames instead of falling behind, and its status says so. Fewer
frames means fewer chances to catch a good face, but nothing crashes and
nothing piles up.</p>
<p>Each watcher has its own processing resolution. A higher setting finds
faces earlier at a distance and costs more computing power. The measure
button on the Live tab shows what your machine can afford.</p>
<p>Live watch and the normal way share the same face library. Teaching the
system a new face improves both at once.</p>""",
    "gesicht": """
<p>Behind the scenes each person has a small library of reference pictures. A
new pass is compared against these references, and the system only claims a
name when the similarity clears a bar it has set for itself. It sets that bar
by testing itself against people who do not live here, so a stranger walking
through should not clear it.</p>
<p>You can review the library any time. Weak or wrong pictures can be
removed, and a deletion retrains the system on its own.</p>
<p>If you also use Frigate's own face recognition, the sync page can copy
faces in both directions, so you never teach the same person twice.</p>
<p>Face recognition has no off switch because the other ways build on its
verdict: body recognition steps in when faces come up empty, and the picture
referee is only asked when faces leave doubt.</p>""",
    "koerper": """
<p>The verdict is calibrated against strangers: the system measured how
confident it gets about people who do not belong to the household and put its
bar above that. This is what the "calibrated against strangers" line on the
card means. A verdict below the bar counts as unknown rather than being
guessed.</p>
<p>Body recognition is the most expensive local step, because it reads the
full recording of a pass. It runs in its own supervised worker with a memory
budget: a huge pass gets thinned out instead of exhausting the machine.</p>
<p>On the recognition test page you can replay a pass and see what each way
concluded.</p>
<p>The same approved pictures also feed the vision galleries, so a person
learned here is halfway into the picture referee too.</p>""",
    "vision": """
<p>Vision compares picture sets, not single frames. For every known person it
keeps a small gallery built from the approved body pictures, and the pass in
question is laid out the same way. The model compares set against set, both
ways round, and the answers are counted like votes. One odd picture cannot
decide a pass.</p>
<p><b>Register vision</b> leads to the galleries. A person needs approved
body material before a gallery can be built, and the page tells you honestly
who is ready and who is not.</p>
<p>There are request limits per hour and per day, so a busy day cannot run up
costs unnoticed. When a limit is reached, vision pauses and says so instead
of failing quietly.</p>
<p>A referee verdict is marked as such on the pass, so you can always tell
which way decided.</p>""",
}


def render(weg):
    """-> Seiten-INHALT /hilfe/<weg> oder None (unbekannter Weg)."""
    s = _seiten().get(weg)
    if not s:
        return None
    titel, saetze, zurueck = s
    # User-Entscheid 16.08. spaeter Vormittag: ERSTMAL NUR die Easy-Fassung —
    # die MEHR-Bloecke (Easy plus, im Expert-Modus) bleiben oben als
    # abgestimmter Bestand liegen und werden SPAETER gerendert, wenn der
    # Easy-plus-Schritt drankommt (dann auch als Schluessel einziehen).
    zurueck = zurueck or "/erkennung"
    ziel = {"/faces": t("hilfe.zurueck.faces"),
            "/lernlauf": t("hilfe.zurueck.lernlauf")}.get(
                zurueck, t("hilfe.zurueck.erkennung"))
    return (
        f"<h2>{html.escape(titel)}</h2>"
        '<div class="hilfe">' + "\n" + "\n".join(saetze)
        + f'<p><a class="gtb" href="{zurueck}">{html.escape(ziel)}</a></p>'
        + "</div>")
