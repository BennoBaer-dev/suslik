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


def render(personen, n_bilder, n_unbekannt, lern_offen, qs_stand=None):
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

    # .280 (User 18.08.: 'Button nach oben, damit nichts unten wegrutscht —
    # oben gleichmaessig vom Look and Feel; Texte weg oder deutlich kuerzer,
    # alles steht ja im How it works'): jede Kachel ist gleich gebaut —
    # Titel, KNOEPFE direkt darunter, Stand-Zeile, Mini-Zeile + Hilfe-Link.
    # Bewusst OHNE ek-fuss (dessen margin-top:auto drueckte die Knoepfe an
    # den Kachelboden); die Regel selbst bleibt fuer andere Seiten.
    bekannt = (
        '<div class="ek-card" id="fc-bekannt">'
        '<h3>&#128578; Known people</h3>'
        '<div><a class="ek-knopf" href="/gesichter">'
        'Manage people &#8230;</a>'
        '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
        'Register face &#8230;</a></div>'
        + (f'<div class="fc-avatare">{avatare}</div>' if avatare else
           '<div class="ek-beweis">no people learned yet — register the '
           'first face above</div>')
        + (f'<div class="ek-beweis"><b>{len(personen)} people</b> &middot; '
           f'{n_bilder} reference images</div>' if avatare else "")
        + '<div class="ek-hilfe"><a href="/hilfe/faces_bekannt">'
          'How it works &#8230;</a></div></div>')

    lern_beweis = (f'<b>{lern_offen}</b> suggestion(s) waiting for review'
                   if lern_offen else
                   "nothing waiting — the system keeps collecting on its own")
    lernen = (
        '<div class="ek-card" id="fc-lernen">'
        '<h3>&#127891; Learning</h3>'
        '<div><a class="ek-knopf" href="/lernlauf">'
        'Start learning &#8230;</a>'
        '<a class="ek-knopf" style="margin-top:6px" href="/lernen">'
        'Review suggestions &#8230;</a></div>'
        + f'<div class="ek-beweis">{lern_beweis}</div>'
        + '<p class="ek-satz">Review what the cameras collected.</p>'
          '<div class="ek-hilfe"><a href="/hilfe/faces_lernen">'
          'How it works &#8230;</a></div></div>')

    unb_beweis = (f'<b>{n_unbekannt}</b> recurring unknown visitor(s)'
                  if n_unbekannt else "no recurring unknown visitors")
    unbekannt = (
        '<div class="ek-card" id="fc-unbekannt">'
        '<h3>&#10067; Unknown</h3>'
        '<div><a class="ek-knopf" href="/unbekannte">'
        'Review unknown &#8230;</a></div>'
        + f'<div class="ek-beweis">{unb_beweis}</div>'
        + '<p class="ek-satz">Visitors without a name yet.</p>'
          '<div class="ek-hilfe"><a href="/hilfe/faces_unbekannt">'
          'How it works &#8230;</a></div></div>')

    # .273 (User 18.08.: 'Qualitaetssichere alle meine Bilder'): die Karte
    # ist EASY, traegt den Stand der letzten Pruefung und startet den Lauf
    # ueber ein Popup (alle Personen ODER eine; Muster Such-Popup .259).
    import html as _html
    stand_zeile = ""
    if qs_stand and qs_stand.get("ts"):
        import datetime as _dt
        stand_zeile = ('<p class="ek-satz dim">last checked '
                       + _dt.datetime.fromtimestamp(qs_stand["ts"])
                       .strftime("%d.%m. %H:%M")
                       + f' &middot; {int(qs_stand.get("funde", 0))} '
                         'finding(s)</p>')
    opts = "".join(f'<option>{_html.escape(p)}</option>' for p, _d in personen)
    wen = ""
    if opts:
        wen = ('<div class="qsz"><label><input type="radio" name="qs-wen" '
               'checked onchange="document.getElementById(\'qs-ziel\')'
               '.disabled=true"> All people</label> '
               '<label><input type="radio" name="qs-wen" '
               'onchange="document.getElementById(\'qs-ziel\')'
               '.disabled=false"> One person:</label> '
               f'<select id="qs-ziel" disabled>{opts}</select></div>')
    popup = (
        '<div id="qs-deck" onclick="if(event.target===this)'
        'this.style.display=\'none\'" style="position:fixed;inset:0;'
        'background:#000a;display:none;place-items:center;z-index:9">'
        '<div style="background:var(--surface);border:1px solid '
        'var(--border-strong,var(--border));border-radius:12px;'
        'padding:18px 20px;width:min(420px,92vw)">'
        '<h3 style="margin:0 0 4px">Quality-check my pictures</h3>'
        '<p class="ek-satz">Re-measures every reference picture and looks '
        'for weak ones, near-duplicates and mixed-up faces. Takes about a '
        'minute and runs in the background.</p>'
        + wen +
        '<div style="display:flex;gap:8px;margin-top:14px;align-items:center">'
        '<button class="gtb on" onclick="qsStart(this)">Start check</button>'
        '<button class="gtb" onclick="document.getElementById(\'qs-deck\')'
        '.style.display=\'none\'">Cancel</button>'
        '<span id="qs-status" class="dim"></span></div></div></div>'
        '<style>.qsz{display:flex;gap:8px;align-items:center;flex-wrap:wrap;'
        'font-size:14px}.qsz select{background:var(--surface-2);'
        'color:var(--text);border:1px solid '
        'var(--border-strong,var(--border));border-radius:6px;'
        'padding:4px 6px}</style>')
    qualitaet = (
        '<div class="ek-card" id="fc-qualitaet">'
        '<h3>&#129658; Picture quality</h3>'
        # .276 (User: 'finde den Button nirgends' — Suchknopf-Lektion):
        # grosser gruener Knopf; seit .280 OBEN direkt unter dem Titel.
        '<div><button style="display:block;width:100%;padding:12px 14px;'
        'font-size:15px;font-weight:600;border-radius:9px;cursor:pointer;'
        'background:var(--ok);border:1px solid var(--ok);'
        'color:var(--on-ink);text-align:center;margin-bottom:6px" '
        'onclick="document.getElementById(\'qs-deck\')'
        '.style.display=\'grid\'">&#129658;&nbsp; Quality-check my '
        'pictures</button>'
        '<a class="ek-knopf" href="/qualitaet">Last results &#8230;</a>'
        '</div>' + stand_zeile +
        '<p class="ek-satz">Finds weak or mixed-up pictures.</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_qualitaet">'
        'How it works &#8230;</a></div>'
        '</div>' + popup)

    return ('<h2 style="margin:2px 0 10px">Faces</h2>'
            '<p class="dim" style="margin:0 0 14px">Everything about the '
            'faces your system knows, in one place — recognition itself is '
            'configured on the <a href="/erkennung">Recognition</a> page.</p>'
            '<div class="ek-grid">'
            + bekannt + lernen + unbekannt + qualitaet + "</div>")
