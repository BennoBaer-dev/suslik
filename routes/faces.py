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

Injektion pur: alles kommt als Parameter, dieses Modul importiert verifyd nie.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py (der dim-Einleitungssatz mit
<a>-Link im Satz bleibt literal; Datumsformat bleibt in der Route)."""
import html
import urllib.parse

from core.sprache import t


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
        f'<h3>&#128578; {t("faces.bekannt.titel")}</h3>'
        '<div><a class="ek-knopf" href="/gesichter">'
        + t("faces.bekannt.knopf_verwalten") + '</a>'
        '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
        + t("faces.bekannt.knopf_register") + '</a></div>'
        + (f'<div class="fc-avatare">{avatare}</div>' if avatare else
           f'<div class="ek-beweis">{t("faces.bekannt.leer")}</div>')
        # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
        + ('<div class="ek-beweis"><b>'
           + t("faces.bekannt.beweis_personen", n=len(personen))
           + '</b> &middot; '
           + t("faces.bekannt.beweis_bilder", n=n_bilder)
           + '</div>' if avatare else "")
        + '<div class="ek-hilfe"><a href="/hilfe/faces_bekannt">'
        + t("faces.link_how") + '</a></div></div>')

    lern_beweis = ('<b>' + str(lern_offen) + '</b> '
                   + t("faces.lernen.beweis_offen")
                   if lern_offen else t("faces.lernen.beweis_leer"))
    lernen = (
        '<div class="ek-card" id="fc-lernen">'
        f'<h3>&#127891; {t("faces.lernen.titel")}</h3>'
        '<div><a class="ek-knopf" href="/lernlauf">'
        + t("faces.lernen.knopf_start") + '</a>'
        '<a class="ek-knopf" style="margin-top:6px" href="/lernen">'
        + t("faces.lernen.knopf_review") + '</a></div>'
        + f'<div class="ek-beweis">{lern_beweis}</div>'
        + f'<p class="ek-satz">{t("faces.lernen.satz")}</p>'
          '<div class="ek-hilfe"><a href="/hilfe/faces_lernen">'
        + t("faces.link_how") + '</a></div></div>')

    unb_beweis = ('<b>' + str(n_unbekannt) + '</b> '
                  + t("faces.unbekannt.beweis_offen")
                  if n_unbekannt else t("faces.unbekannt.beweis_leer"))
    unbekannt = (
        '<div class="ek-card" id="fc-unbekannt">'
        f'<h3>&#10067; {t("faces.unbekannt.titel")}</h3>'
        '<div><a class="ek-knopf" href="/unbekannte">'
        + t("faces.unbekannt.knopf") + '</a></div>'
        + f'<div class="ek-beweis">{unb_beweis}</div>'
        + f'<p class="ek-satz">{t("faces.unbekannt.satz")}</p>'
          '<div class="ek-hilfe"><a href="/hilfe/faces_unbekannt">'
        + t("faces.link_how") + '</a></div></div>')

    # .273 (User 18.08.: 'Qualitaetssichere alle meine Bilder'): die Karte
    # ist EASY, traegt den Stand der letzten Pruefung und startet den Lauf
    # ueber ein Popup (alle Personen ODER eine; Muster Such-Popup .259).
    import html as _html
    stand_zeile = ""
    if qs_stand and qs_stand.get("ts"):
        import datetime as _dt
        # §8.9: Datumsformat bleibt in der Route (B19-Stufe); {wann}/{n}
        # kommen vorformatiert (§8.8).
        stand_zeile = ('<p class="ek-satz dim">'
                       + t("faces.qualitaet.stand",
                           wann=_dt.datetime.fromtimestamp(qs_stand["ts"])
                           .strftime("%d.%m. %H:%M"),
                           n=int(qs_stand.get("funde", 0)))
                       + '</p>')
    opts = "".join(f'<option>{_html.escape(p)}</option>' for p, _d in personen)
    wen = ""
    if opts:
        wen = ('<div class="qsz"><label><input type="radio" name="qs-wen" '
               'checked onchange="document.getElementById(\'qs-ziel\')'
               '.disabled=true"> ' + t("faces.qualitaet.label_alle")
               + '</label> '
               '<label><input type="radio" name="qs-wen" '
               'onchange="document.getElementById(\'qs-ziel\')'
               '.disabled=false"> ' + t("faces.qualitaet.label_eine")
               + '</label> '
               f'<select id="qs-ziel" disabled>{opts}</select></div>')
    popup = (
        '<div id="qs-deck" onclick="if(event.target===this)'
        'this.style.display=\'none\'" style="position:fixed;inset:0;'
        'background:#000a;display:none;place-items:center;z-index:9">'
        '<div style="background:var(--surface);border:1px solid '
        'var(--border-strong,var(--border));border-radius:12px;'
        'padding:18px 20px;width:min(420px,92vw)">'
        '<h3 style="margin:0 0 4px">' + t("faces.qualitaet.knopf_check")
        + '</h3>'
        f'<p class="ek-satz">{t("faces.qualitaet.popup_satz")}</p>'
        + wen +
        '<div style="display:flex;gap:8px;margin-top:14px;align-items:center">'
        '<button class="gtb on" onclick="qsStart(this)">'
        + t("faces.qualitaet.knopf_start") + '</button>'
        '<button class="gtb" onclick="document.getElementById(\'qs-deck\')'
        '.style.display=\'none\'">' + t("faces.qualitaet.knopf_abbrechen")
        + '</button>'
        '<span id="qs-status" class="dim"></span></div></div></div>'
        '<style>.qsz{display:flex;gap:8px;align-items:center;flex-wrap:wrap;'
        'font-size:14px}.qsz select{background:var(--surface-2);'
        'color:var(--text);border:1px solid '
        'var(--border-strong,var(--border));border-radius:6px;'
        'padding:4px 6px}</style>')
    qualitaet = (
        '<div class="ek-card" id="fc-qualitaet">'
        f'<h3>&#129658; {t("faces.qualitaet.titel")}</h3>'
        # .276 (User: 'finde den Button nirgends' — Suchknopf-Lektion):
        # grosser gruener Knopf; seit .280 OBEN direkt unter dem Titel.
        '<div><button style="display:block;width:100%;padding:12px 14px;'
        'font-size:15px;font-weight:600;border-radius:9px;cursor:pointer;'
        'background:var(--ok);border:1px solid var(--ok);'
        'color:var(--on-ink);text-align:center;margin-bottom:6px" '
        'onclick="document.getElementById(\'qs-deck\')'
        '.style.display=\'grid\'">&#129658;&nbsp; '
        + t("faces.qualitaet.knopf_check") + '</button>'
        '<a class="ek-knopf" href="/qualitaet">'
        + t("faces.qualitaet.knopf_ergebnisse") + '</a>'
        '</div>' + stand_zeile +
        f'<p class="ek-satz">{t("faces.qualitaet.satz")}</p>'
        '<div class="ek-hilfe"><a href="/hilfe/faces_qualitaet">'
        + t("faces.link_how") + '</a></div>'
        '</div>' + popup)

    return (f'<h2 style="margin:2px 0 10px">{t("faces.titel")}</h2>'
            # Stufe-0-Grenze: <a>-Link mitten im Satz — bleibt literal.
            '<p class="dim" style="margin:0 0 14px">Everything about the '
            'faces your system knows, in one place — recognition itself is '
            'configured on the <a href="/erkennung">Recognition</a> page.</p>'
            '<div class="ek-grid">'
            + bekannt + lernen + unbekannt + qualitaet + "</div>")
