"""routes/frigate — die Frigate-Kachel-Startseite (.216, User 16.08.:
"den Punkt Frigate sync wuerde ich einfach in Frigate aendern und darunter
dann analog unserer schoenen Config-Seite Kacheln ... eine Kachel fuer die
Config mit Frigate, eine Kachel fuer den Sync etc").

Vier Kacheln im /erkennung-Muster (gleiche ek-*-Klassen, kein neues CSS):
Connection · Cameras · Sync · Frigate's own face recognition. Die Seite ZEIGT
Zustand und fuehrt zu den bestehenden Seiten — geschaltet wird nichts, alle
Bedienung bleibt dort, wo sie heute liegt (kein zweites halbes Sync-UI, dieselbe
Begruendung wie die .137-Statuszeile der System-Karte).

Injektion pur (Muster routes/konfiguration.py): alles kommt als Parameter,
dieses Modul importiert verifyd nie.
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe siehe
Abschnitts-Kommentar in core/texte/en.py (Markup-Beweiszeilen, Expert-Zeilen,
JS-Texte mit \\u-Escapes bleiben literal)."""
import html

from core.sprache import t


def _karte(kid, titel, satz, beweis, expert="", fuss="", klasse=""):
    return ('<div class="ek-card%s" id="ek-%s"><h3>%s</h3>'
            '<p class="ek-satz">%s</p>'
            '<div class="ek-beweis">%s</div>%s%s</div>'
            % (f" {klasse}" if klasse else "", kid, titel, satz, beweis,
               f'<div class="ek-beweis nur-expert">{expert}</div>' if expert
               else "",
               f'<div class="ek-fuss">{fuss}</div>' if fuss else ""))


def render(url, verbindung, kameras, sync_html, fr):
    """-> Seiten-INHALT /frigate.
    url        = konfigurierte Frigate-URL ("" wenn keine)
    verbindung = (ok: bool|None, detail: str) — Live-Probe /api/version,
                 detail traegt bei ok die Version, sonst den Grund
    kameras    = {"verwendet": n, "gesamt": n}  (aus dem Kamera-Store)
    sync_html  = fertige Bilanz-Zeile (bilanz_zeile, EINE Quelle mit
                 System-Karte und Sync-Seite) ODER Klartext-Fehlersatz
    fr         = (True|False|None, detail) aus sync_refs.frigate_fr_status"""
    v_ok, v_detail = verbindung

    if not url:
        verb_beweis = ("no Frigate URL configured yet — set it under "
                       '<a href="/konfiguration">Advanced</a>')
    elif v_ok:
        verb_beweis = (f"connected · Frigate <b>{html.escape(v_detail)}</b> "
                       f"at {html.escape(url)}")
    else:
        verb_beweis = (f"<b>not reachable</b> — {html.escape(v_detail)}"
                       f"<br>{html.escape(url)}")
    verbindung_k = _karte(
        "frigate-verbindung", f'&#128268; {t("frigate.verbindung.titel")}',
        t("frigate.verbindung.satz"),
        verb_beweis,
        expert='credentials and everything else live under '
               '<a href="/konfiguration">Advanced</a>',
        # .240 (User: "ich wollte doch nur die URL zu Frigate aendern" — der
        # .221-Knopf leitete auf die ganze Advanced-Tabelle um): Inline-Form
        # DIREKT auf der Kachel; Speichern laeuft ueber /setup_speichern
        # (validiert gegen die echte Frigate, auditiert, Neustart).
        fuss=('<button class="ek-knopf" type="button" '
              f'onclick="fgForm(true)">{t("frigate.verbindung.knopf_aendern")} &#8230;</button>'
              '<div id="fg-form" hidden style="margin-top:8px">'
              f'<input id="fg-url" size="26" value="{html.escape(url)}" '
              'placeholder="http://frigate:5000">'
              '<div style="margin-top:6px">'
              '<button class="ek-knopf" type="button" onclick="fgSave(this)">'
              f'{t("frigate.verbindung.knopf_speichern")}</button> '
              '<button class="ek-knopf" type="button" onclick="fgForm(false)">'
              f'{t("frigate.verbindung.knopf_abbrechen")}</button></div>'
              '<div class="dim" id="fg-status" style="margin-top:4px">'
              f'{t("frigate.verbindung.hinweis_speichern")}</div></div>'))

    if kameras["gesamt"]:
        kam_beweis = (f'<b>{kameras["verwendet"]} of {kameras["gesamt"]}</b> '
                      "Frigate cameras in use")
    else:
        kam_beweis = t("frigate.kameras.beweis_keine_auswahl")
    kameras_k = _karte(
        "frigate-kameras", f'&#128247; {t("frigate.kameras.titel")}',
        t("frigate.kameras.satz"),
        kam_beweis,
        fuss=f'<a class="ek-knopf" href="/kameras">{t("frigate.kameras.knopf")} &#8230;</a>')

    sync_k = _karte(
        "frigate-sync", f'&#128260; {t("frigate.sync.titel")}',
        t("frigate.sync.satz"),
        sync_html,
        fuss='<a class="ek-knopf" href="/sync_auswahl">'
             f'{t("frigate.sync.knopf")} &#8230;</a>')

    fr_ok, fr_detail = fr
    if fr_ok is True:
        fr_beweis = ("<b>enabled</b> in Frigate — faces sent by the sync "
                     "are used by Frigate&rsquo;s own recognition")
    elif fr_ok is False:
        fr_beweis = ("<b>disabled</b> in Frigate — Frigate refuses face "
                     "uploads while it is off (reading still works); "
                     "recognition here is not affected")
    else:
        fr_beweis = t("frigate.fr.beweis_unbekannt",
                      detail=html.escape(fr_detail or ''))
    # .221 (User 16.08.: "beim normalen View haette ich die definitiv
    # rausgenommen, was bringt sie uns"): reine Zustands-Kachel ohne
    # Handlung -> nur Expert; der Sync-Kenner braucht sie, sonst niemand.
    fr_k = _karte(
        "frigate-fr", f'&#128100; {t("frigate.fr.titel")}',
        t("frigate.fr.satz"),
        fr_beweis,
        expert="checked live via <code>GET /api/config</code> "
               "(face_recognition.enabled), never from a stored status",
        klasse="nur-expert")

    js = ('<script>'
          'function fgForm(an){document.getElementById("fg-form").hidden=!an;}'
          'function fgSave(b){var u=(document.getElementById("fg-url").value||"").trim();'
          'var st=document.getElementById("fg-status");'
          'if(!u){st.textContent="' + t("frigate.js.url_fehlt") + '";return;}'
          'b.disabled=true;st.textContent="checking the connection\\u2026";'
          'fetch("/setup_speichern",{method:"POST",'
          'headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({frigate_url:u})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'if(!d.ok){st.textContent=d.msg;b.disabled=false;return;}'
          'st.textContent="saved \\u2014 restarting, this page reloads\\u2026";'
          'setTimeout(function(){location.reload()},6000);})'
          '.catch(function(e){st.textContent="' + t("frigate.js.fehler") + ' "+e;b.disabled=false;});}'
          '</script>')
    return ('<h2 style="margin:2px 0 10px">Frigate</h2>'
            '<p class="dim" style="margin:0 0 14px">Everything about the '
            'connected Frigate in one place &mdash; the recognition itself '
            'runs on the <a href="/erkennung">Recognition</a> page.</p>'
            '<div class="ek-grid">'
            + verbindung_k + kameras_k + sync_k + fr_k + "</div>" + js)
