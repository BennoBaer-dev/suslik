"""routes/hilfe — In-App-Anleitungen je Erkennungs-Kachel (.208, User 16.08.).

Je Weg EINE Seite mit zwei Tiefen: der Basis-Text ist fuer JEDEN Leser da,
der Zusatz-Block erscheint nur im Expert-Modus — Expert ist bewusst
"Easy plus" (mehr Tiefe, gleiche Sprache), kein Techniker-Text: keine
Modellnamen, keine Schwellen-Zahlen, kein Fachjargon (User-Auflage 16.08.,
alle Texte durch den Humanizer-Lauf). Anleitungen leben IN suslik, nicht
auf GitHub. Beide Fassungen stehen im HTML; der Easy/Expert-Schalter der
Kopfzeile blendet um (Klassen nur-easy/nur-expert), nichts laedt nach.

Injektion pur: reines Rendern, kein Zustand, importiert verifyd nie."""
import html

TEXTE = {
    "live": {
        "titel": "Live watch, explained",
        "basis": """
<p>Live watch looks at your cameras the moment something moves. When a person
steps onto the property, you get an alert within seconds, and if the system
already knows the face, the alert carries a name.</p>
<p>The name at this stage is a first guess. The thorough check runs right
after, on the recording, and has the final word.</p>
<p>Live watch does not depend on Frigate: it is not triggered by Frigate
events and runs completely on its own. It watches the video stream directly,
either Frigate's proxy stream or the camera's own stream; you choose that
per camera.</p>
<p>Use <b>Choose cameras</b> to pick which cameras get a watcher. Every watched
camera costs computing power around the clock, so start where people actually
arrive: driveway, front door, gate. You can add more later.</p>
<p>Switching a camera off here changes nothing about recording. Frigate keeps
recording as before; the switch only decides whether suslik looks at the
picture immediately or waits for the recording.</p>""",
        "mehr": """
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
    },
    "gesicht": {
        "titel": "Face recognition, explained",
        "basis": """
<p>This is the base way suslik recognizes and learns faces. Every recorded
pass is checked against the faces you have taught the system.</p>
<p>Teaching works from your own cameras: suslik collects faces it sees, you
look at the pictures and tell it who is who. The more different situations
and poses it has seen of a person, the better it gets: daylight, evening,
hat on, hat off, from the side.</p>
<p>If Frigate already knows faces, you can import them on the Frigate sync
page. The recommendation is still to learn faces here: suslik's own learning
collects many different poses and situations per person, and those
references give better results in suslik than faces taken over from
Frigate. What you teach here can be handed back to Frigate on the sync page
if you want.</p>
<p>Everything stays on your machine. Nothing is uploaded anywhere, and there
is no cloud service behind it.</p>
<p>When a face is recognized, or an unknown one shows up, suslik can alert you
directly: Pushover, Telegram, or MQTT for your home automation. You choose on
the Notifications page what gets sent where. These alerts are suslik's own
and work completely independent of Frigate; Frigate needs no notification
setup at all.</p>
<p><b>Manage people</b> shows everyone the system knows and lets you clean
up. <b>Register face</b> starts a learning run for someone new.</p>""",
        "mehr": """
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
    },
    "koerper": {
        "titel": "Body recognition, explained",
        "basis": """
<p>Some passes never show a usable face: the person looks away, wears a hood,
or is too far off. Body recognition covers these cases. It recognizes
household members by build and posture, using pictures of the whole
person.</p>
<p>It is built for exactly this case: no usable face, you still want to know
who it was, and you do not want to hand the pictures to an AI vision model
for it.</p>
<p>It learns from material you approve. <b>Register body</b> starts a short
learning run for one person: the system collects pictures of them from your
cameras, you review the result once, and from then on it keeps learning by
itself.</p>
<p>With the switch above you choose whether and when it runs. <b>Only if no
face</b> means it stays quiet unless the face check came up empty.
<b>Always</b> means it checks every pass. Off means it never runs.</p>""",
        "mehr": """
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
    },
    "vision": {
        "titel": "AI vision, explained",
        "basis": """
<p>AI vision is a recognition way of its own. It shows the pictures of a
pass to an image model and asks which registered person they resemble. You
can use it as a backup for the hard cases, or let it carry recognition
alone: set to <b>Always</b>, it judges every pass by itself, even if no
faces are taught at all. It judges at the end of a pass, not live.</p>
<p>What it needs to work: registered people with approved body pictures
(their galleries), and a connected model. The model can run locally on your
own hardware or in the cloud. With a cloud model, remember that the
pictures leave your house: what is fine with a local model is not
automatically allowed with a cloud one. And do not pick the smallest
models; a mid-sized model does the job fine.</p>
<p>What we run ourselves: Qwen 3.5 in the 9B size, and it does the job well,
locally as well as in the cloud. We also tested models from Anthropic
(Claude), Google (Gemini) and OpenAI (GPT). Take this as tested, not as a
recommendation; the model list on the Vision page marks the ones we
measured, right where you choose.</p>
<p>And it does not stop at one comparison: to rule out mix-ups, the pass is
checked against the galleries of the other people too, both ways round.
Each compared pair costs two requests, so a single pass can add up. <b>If
needed</b> keeps that bill small: the model only gets asked when faces
leave doubt. Without a connected model, vision simply stays out of the
game, and the card says so.</p>""",
        "mehr": """
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
    },
    # .221: die vier Faces-Anleitungen (User-Abnahme 16.08. abends, "ok" auf
    # die deutschen Entwuerfe — hier die englische Produkt-Fassung, gleicher
    # Inhalt Satz fuer Satz). zurueck=/faces statt /erkennung.
    "faces_bekannt": {
        "titel": "Known people & registering, explained",
        "zurueck": "/faces",
        "basis": """
<p>Here you see every person your system knows &mdash; tap a face and you see
every picture stored behind it.</p>
<p>You do not teach a new person with a photo upload: they are learned from
normal camera footage. Over the day the system collects pictures from
different angles, you confirm who it is, and only after that check a picture
is kept.</p>
<p>That way every person gets a small collection of real everyday pictures
&mdash; exactly what makes recognition strong, even when someone looks away
or wears a cap.</p>""",
        "mehr": "",
    },
    "faces_lernen": {
        "titel": "Learning, explained",
        "zurueck": "/faces",
        "basis": """
<p>While the cameras run, the system keeps collecting new pictures of the
people it already knows. Here you look through what has come together
&mdash; every few days is plenty.</p>
<p>You confirm, correct or dismiss with one click; nothing is kept without
you.</p>
<p>The more good pictures a person has, the more reliably they are
recognized &mdash; so learning never fully stops, it just becomes rarer.</p>""",
        "mehr": "",
    },
    "faces_unbekannt": {
        "titel": "Unknown visitors, explained",
        "zurueck": "/faces",
        "basis": """
<p>Some people keep showing up without the system having a name for them
&mdash; the postman, a neighbour, the gardener. Here the system collects
these recurring unknowns and asks you: who is this?</p>
<p>Give them a name and from then on they are recognized like everyone
else. Or leave them unknown on purpose &mdash; that is a decision too, and
the system will not keep asking.</p>""",
        "mehr": "",
    },
    "faces_qualitaet": {
        "titel": "Quality check, explained",
        "zurueck": "/faces",
        "basis": """
<p>Over time many pictures pile up, and not every one helps recognition
&mdash; some are blurry, some barely show the person, and in the worst case
pictures of two different people look so alike that mix-ups loom.</p>
<p>This check finds such weak spots before they cost you a recognition. You
get concrete pointers which pictures to look at &mdash; nothing is deleted
unless you decide it yourself.</p>""",
        "mehr": "",
    },
}


def render(weg):
    """-> Seiten-INHALT /hilfe/<weg> oder None (unbekannter Weg)."""
    t = TEXTE.get(weg)
    if not t:
        return None
    # User-Entscheid 16.08. spaeter Vormittag: ERSTMAL NUR die Easy-Fassung —
    # die "mehr"-Bloecke (Easy plus, im Expert-Modus) bleiben hier als
    # abgestimmter Bestand liegen und werden SPAETER gerendert, wenn der
    # Easy-plus-Schritt drankommt. Nichts davon erscheint heute im UI.
    # .221: Faces-Anleitungen fuehren zurueck nach /faces, die Erkennungs-
    # Anleitungen wie bisher nach /erkennung (Feld "zurueck", Default alt).
    zurueck = t.get("zurueck") or "/erkennung"
    ziel = "Faces" if zurueck == "/faces" else "Recognition"
    return (
        f"<h2>{html.escape(t['titel'])}</h2>"
        '<div class="hilfe">' + t["basis"]
        + f'<p><a class="gtb" href="{zurueck}">Back to {ziel}</a></p>'
        + "</div>")
