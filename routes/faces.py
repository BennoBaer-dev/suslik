"""routes/faces — die Faces-Startseite (.220, User 16.08., Mockup-Abnahme
"ok"): der Gesichts-Bereich "eingedampft" auf eine Kachel-Startseite im
/erkennung-Muster. Easy sieht Known people (mit Avatar-Leiste: je Person ein
echtes Gesichts-Icon, Klick -> alle Referenzen), Learning (der gefuehrte
Pflege-Fluss) und Unknown; Quality ist Expert (Klasse nur-expert — der Reiter
darf sich verstecken, ein Problem nicht: der Warnhinweis auf der Known-Kachel
folgt, sobald ein guenstiges Quality-Signal vorliegt).

Jeder erste Kachel-Satz beantwortet die Wann-brauche-ich-das-Frage
(User-Fund am Mockup: drei Knoepfe, die alle irgendwie "lernen" heissen,
erklaeren sich sonst nicht). Die How-it-works-Links je Kachel kommen mit den
abgenommenen Texten (Satz-fuer-Satz-Abnahme wie bei den vier Erkennungs-
Anleitungen), nicht vorher.

Injektion pur: alles kommt als Parameter, dieses Modul importiert verifyd nie."""
import html
import urllib.parse


def _q(s):
    return urllib.parse.quote(str(s), safe="")


def render(personen, n_bilder, n_unbekannt, lern_offen):
    """-> Seiten-INHALT /faces.
    personen    = [(name, avatar_datei), ...] (Avatar = juengstes aktives
                  Referenzbild laut refs_meta, Fallback erste Datei)
    n_bilder    = Gesamtzahl Referenzbilder
    n_unbekannt = Zahl persistenter Unbekannt-Identitaeten
    lern_offen  = Zahl offener Lern-Vorschlaege (0 = nichts zu tun)"""
    avatare = "".join(
        f'<a class="fc-avatar" href="/gesichter#{_q(p)}" title="{html.escape(p)}">'
        f'<img src="/refs/{_q(p)}/{_q(d)}" alt="" loading="lazy">'
        f'<span>{html.escape(p)}</span></a>'
        for p, d in personen)

    bekannt = (
        '<div class="ek-card" id="fc-bekannt">'
        '<h3>&#128578; Known people</h3>'
        '<p class="ek-satz">Everyone the system already knows — tap a face '
        'to see every reference picture behind it. <b>Someone new in the '
        'household?</b> Use &bdquo;Register face&ldquo;: their face is '
        'collected from normal camera footage, no photo upload needed.</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_bekannt">'
        'How it works &#8230;</a></div>'
        + (f'<div class="fc-avatare">{avatare}</div>' if avatare else
           '<div class="ek-beweis">no people learned yet — register the '
           'first face below</div>')
        + (f'<div class="ek-beweis"><b>{len(personen)} people</b> &middot; '
           f'{n_bilder} reference images</div>' if avatare else "")
        + '<div class="ek-fuss"><a class="ek-knopf" href="/gesichter">'
          'Manage people &#8230;</a>'
          '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
          'Register face &#8230;</a></div></div>')

    lern_beweis = (f'<b>{lern_offen}</b> suggestion(s) waiting for review'
                   if lern_offen else
                   "nothing waiting — the system keeps collecting on its own")
    lernen = (
        '<div class="ek-card" id="fc-lernen">'
        '<h3>&#127891; Learning</h3>'
        '<p class="ek-satz"><b>The regular care routine:</b> while the '
        'cameras run, the system keeps collecting new pictures of the '
        'people it knows — here you review what it gathered, every few '
        'days or whenever you like.</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_lernen">'
        'How it works &#8230;</a></div>'
        '<div class="fc-schritt"><b>1</b><span>Run a learning pass over '
        'the recent recordings</span></div>'
        '<div class="fc-schritt"><b>2</b><span>Review the suggestions — '
        'confirm, correct or dismiss</span></div>'
        '<div class="fc-schritt"><b>3</b><span>Name new faces the system '
        'found on its own</span></div>'
        + f'<div class="ek-beweis">{lern_beweis}</div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/lernlauf">'
          'Start learning &#8230;</a>'
          '<a class="ek-knopf" style="margin-top:6px" href="/lernen">'
          'Review suggestions &#8230;</a></div></div>')

    unb_beweis = (f'<b>{n_unbekannt}</b> recurring unknown visitor(s)'
                  if n_unbekannt else "no recurring unknown visitors")
    unbekannt = (
        '<div class="ek-card" id="fc-unbekannt">'
        '<h3>&#10067; Unknown</h3>'
        '<p class="ek-satz"><b>The system asks YOU here:</b> it noticed '
        'people coming back that it cannot name yet — decide who they are '
        '(the postman? a neighbour?) or leave them unknown on purpose.</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_unbekannt">'
        'How it works &#8230;</a></div>'
        + f'<div class="ek-beweis">{unb_beweis}</div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/unbekannte">'
          'Review unknown &#8230;</a></div></div>')

    qualitaet = (
        '<div class="ek-card nur-expert" id="fc-qualitaet">'
        '<h3>&#129658; Quality</h3>'
        '<p class="ek-satz"><b>For a health check now and then:</b> finds '
        'weak or mixed-up reference pictures before they cost you a '
        'recognition.</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_qualitaet">'
        'How it works &#8230;</a></div>'
        '<div class="ek-fuss"><a class="ek-knopf" href="/qualitaet">'
        'Open quality check &#8230;</a></div></div>')

    return ('<h2 style="margin:2px 0 10px">Faces</h2>'
            '<p class="dim" style="margin:0 0 14px">Everything about the '
            'faces your system knows, in one place — recognition itself is '
            'configured on the <a href="/erkennung">Recognition</a> page.</p>'
            '<div class="ek-grid">'
            + bekannt + lernen + unbekannt + qualitaet + "</div>")
