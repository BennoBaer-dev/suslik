"""routes/erkennung — die Vier-Saeulen-Erkennungsseite (.205, User 15.08.:
"vier Bereiche/Kacheln, fuer jede Erkennungsoption", "auf jeder Kachel ein
enable/disable", "sowohl Expert als auch Easy, bei Expert mehr Moeglichkeiten").

EINE Seite fuer beide Modi: Easy zeigt je Weg den Kippschalter, einen
Klartext-Satz, die Zustands-Zeile und EINEN Einrichtungs-Knopf; Expert blendet
zusaetzlich Status-Details und Tief-Links ein (Klasse "nur-expert", die
body.easy per CSS versteckt — nichts wird geloescht, Easy blendet nur aus).

ECHTE Schalter, nichts Vorgetaeuschtes:
  Live    -> /live_schalter je EINGERICHTETEM Waechter (der Server-Riegel je
             Kamera entscheidet; aus = alle laufenden aus, ein = alle
             eingerichteten an), wirkt sofort, kein Neustart.
  Koerper -> person_pfad  (verstecktes cfg-Feld, derselbe konfigSpeichern-Weg
             wie /kette: auditiert + sauberer Neustart).
  Vision  -> vision_pfad  (dito).
  Gesicht -> hat heute KEINEN Aus-Schalter (Rueckgrat der Kette, person/vision
             haengen an seinem Pass-Urteil) — der Kipp ist sichtbar VERRIEGELT
             und sagt das ehrlich, statt einen toten Schalter zu spielen.

Injektion pur (Muster routes/konfiguration.py): alles kommt als Parameter,
dieses Modul importiert verifyd nie.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py — u. a. bleiben die Unteroptions-
Labels "Always"/"Only if no face"/"If needed" literal (Anzeige==Kennung:
ekUnterWert vergleicht den Button-TEXT), ebenso die Saetze mit Inline-Markup
und die JS-Statustexte; der _unter-Schleifenname `t` wurde zu `txt`
umbenannt, damit er t() nicht verschattet."""
import html

from core.sprache import t


def _kipp(an, verriegelt=False, onclick=""):
    k = ('<span class="ek-kipp%s%s" role="switch" aria-checked="%s"%s%s></span>'
         % (" an" if an else "", " fest" if verriegelt else "",
            "true" if an else "false",
            f' title="{t("erkennung.kipp.attr_verriegelt")}"'
            if verriegelt else "",
            f' onclick="{onclick}"' if onclick else ""))
    return ('<div class="ek-kippzeile"><span class="ek-zl">'
            + t("erkennung.kipp.label") + '</span>' + k + "</div>")


def _unter(feld_id, wert, opts, onclick_js):
    """Modus-Unteroption (nur sichtbar, wenn der Weg an ist)."""
    kn = "".join(
        f'<button type="button"{" class=an" if wert == o else ""} '
        f'onclick="{onclick_js}(this,\'{o}\')">{html.escape(txt)}</button>'
        for o, txt in opts)
    return f'<div class="ek-unter" data-feld="{feld_id}">{kn}</div>'


def render(cfg, whitelist, lage, waechter, gesicht, modell, n_areas=None):
    """-> Seiten-INHALT /erkennung.
    waechter = {"an": n_laufend, "eingerichtet": n_eingerichtet}
    gesicht  = {"personen": n, "bilder": n}
    modell   = personmodell.status_lesen(...) oder None.
    n_areas  = Zahl der Areas (None = Zeile weglassen, Alt-Aufrufer)."""
    lg_p = (lage or {}).get("person") or {}
    lg_v = (lage or {}).get("vision") or {}
    p_stufe = cfg.get("person_pfad") or "immer"
    v_stufe = cfg.get("vision_pfad") or "immer"
    v_aktiv = bool((cfg.get("vision") or {}).get("aktiv"))
    p_erkl = (whitelist.get("person_pfad") or (0, 0, 0, ""))[3]
    v_erkl = (whitelist.get("vision_pfad") or (0, 0, 0, ""))[3]

    # --- Live
    live_an = waechter["an"] > 0
    # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
    live_beweis = (t("erkennung.live.beweis_prefix") + ' <b>'
                   + t("erkennung.live.beweis_zaehler", an=waechter["an"],
                       ges=waechter["eingerichtet"])
                   + '</b> ' + t("erkennung.live.beweis_suffix")
                   if live_an else
                   (f'<b>{waechter["eingerichtet"]}</b> '
                    + t("erkennung.live.beweis_keine_laufend")
                    if waechter["eingerichtet"]
                    else t("erkennung.live.beweis_keiner")))
    live = (
        '<div class="ek-card' + ("" if live_an else " aus") + '" id="ek-live">'
        f'<h3>&#128680; {t("erkennung.live.titel")}</h3>'
        + _kipp(live_an, onclick="ekLive(this)")
        # Stufe-0-Grenze: <b>moment</b> mitten im Satz — bleibt literal.
        + '<p class="ek-satz">Alerts the <b>moment</b> someone steps onto '
          'the property — seconds after the camera sees them, with a '
          'preliminary name.</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/live">'
        + t("erkennung.link_how") + '</a></div>'
        + f'<div class="ek-beweis">{live_beweis}</div>'
        + '<div class="ek-beweis nur-expert">'
        + t("erkennung.live.expert_schalter") + ' · '
          '<a href="/live">' + t("erkennung.live.link_prokamera")
        + '</a></div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/live">'
        + t("erkennung.live.knopf_kameras") + '</a>'
          # User 16.08.: die Live-Namensstufe urteilt mit DENSELBEN
          # Gesichts-Referenzen wie der Face-Weg — gleicher Knopf,
          # gleiches Ziel auf beiden Kacheln.
          '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
        + t("erkennung.knopf_register_face") + '</a></div></div>')

    # --- Gesicht
    ges = (
        '<div class="ek-card" id="ek-gesicht">'
        f'<h3>&#128578; {t("erkennung.gesicht.titel")}</h3>'
        + _kipp(True, verriegelt=True)
        + f'<p class="ek-satz">{t("erkennung.gesicht.satz")}</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/gesicht">'
        + t("erkennung.link_how") + '</a></div>'
        # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
        + ('<div class="ek-beweis"><b>'
           + t("erkennung.gesicht.beweis_personen", n=gesicht["personen"])
           + '</b> · '
           + t("erkennung.gesicht.beweis_bilder", n=gesicht["bilder"])
           + '</div>')
        # Stufe-0-Grenze: zwei <a>-Links mitten im Satz — bleibt literal.
        + '<div class="ek-beweis nur-expert">model and thresholds live under '
          '<a href="/konfiguration">Advanced</a> · chain order on '
          '<a href="/kette">Recognition chain</a></div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/gesichter">'
        + t("erkennung.gesicht.knopf_verwalten") + '</a>'
          # .208 (User-Entscheid 16.08.: JEDE Kachel hat ihren eigenen
          # Register-Knopf mit dem Namen ihres Wegs; Leitsatz: Registrieren
          # richtet sich nach dem, was eingeschaltet ist): Face registriert
          # ueber den Gesichts-Lernlauf (aus dem Betrieb, kein Upload).
          '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
        + t("erkennung.knopf_register_face") + '</a></div></div>')

    # --- Koerper
    m = modell or {}
    if m.get("bilder"):
        ei = m.get("eichung") or {}
        # Stufe-0-Grenze: drei <b>-Inseln + konditionale Anhaenge in EINEM
        # Zaehler (§8.10-Grenzfall) — bleibt literal.
        k_beweis = (f'model trained (<b>{m.get("bilder")}</b> images'
                    + (f', calibrated against <b>{ei.get("n_fremd")}</b> '
                       f'strangers' if ei.get("n_fremd") else "")
                    + (")" if m.get("scharf") else ") · <b>not armed</b>"))
    else:
        k_beweis = t("erkennung.koerper.beweis_kein_modell")
    koerper = (
        '<div class="ek-card' + ("" if p_stufe != "aus" else " aus")
        + '" id="ek-koerper">'
        f'<h3>&#128694; {t("erkennung.koerper.titel")}</h3>'
        + _kipp(p_stufe != "aus", onclick="ekKipp(this,'person_pfad')")
        # Stufe-0-Grenze: "Always"/"Only if no face" sind Anzeige==Kennung
        # (ekUnterWert vergleicht den Button-Text) — bleiben literal.
        + _unter("cfg-person_pfad", p_stufe,
                 [("immer", "Always"),
                  ("nur_wenn_gesicht_leer", "Only if no face")], "ekUnter")
        + f'<p class="ek-satz">{t("erkennung.koerper.satz")}</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/koerper">'
        + t("erkennung.link_how") + '</a></div>'
        + f'<div class="ek-beweis">{k_beweis}</div>'
        # Stufe-0-Grenze: 'status: <b>armed</b> — runs by itself' bleibt
        # literal (Muster konfiguration); die Not-running-Zweige sind
        # Schluessel.
        + '<div class="ek-beweis nur-expert">status: '
        + ("<b>armed</b> — runs by itself" if lg_p.get("wirksam") else
           html.escape(t("erkennung.status.kein_modell")
                       if not lg_p.get("modell_scharf") else
                       t("erkennung.status.hier_aus")))
        + ' · <a href="/personlauf">' + t("erkennung.koerper.link_modell")
        + '</a><br>'
          # §8.14 Slice-vor-Format: p_erkl ist Whitelist-DATEN mit [:180].
          f'{html.escape(p_erkl[:180])}&#8230;</div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/personlauf">'
        + t("erkennung.koerper.knopf_status") + '</a>'
          '<a class="ek-knopf" style="margin-top:6px" href="/personlauf">'
        + t("erkennung.koerper.knopf_register") + '</a></div></div>')

    # --- Vision
    vis_beweis = (t("erkennung.vision.beweis_an") if v_aktiv
                  else t("erkennung.vision.beweis_aus"))
    vision = (
        '<div class="ek-card' + ("" if v_stufe != "aus" and v_aktiv
                                 else " aus") + '" id="ek-vision">'
        # .219 (User 16.08.): der Vision-Bereich traegt sichtbar "Beta" — der
        # Nutzer soll wissen, dass dieser Weg noch reift (Misch-Gitter-Frage,
        # Kalibrier-Test offen), bevor er sich auf ihn verlaesst.
        f'<h3>&#128302; {t("erkennung.vision.titel")} '
        f'<span class="ek-beta">{t("erkennung.vision.beta")}</span></h3>'
        + _kipp(v_stufe != "aus", onclick="ekKipp(this,'vision_pfad')")
        # Stufe-0-Grenze: Anzeige==Kennung (s. Koerper) — bleibt literal.
        + _unter("cfg-vision_pfad", v_stufe,
                 [("immer", "Always"),
                  ("nur_wenn_gesicht_leer", "If needed")], "ekUnter")
        + f'<p class="ek-satz">{t("erkennung.vision.satz")}</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/vision">'
        + t("erkennung.link_how") + '</a></div>'
        + f'<div class="ek-beweis">{vis_beweis}</div>'
        # Stufe-0-Grenze: '<b>armed</b>'-Zweig bleibt literal (s. Koerper).
        + '<div class="ek-beweis nur-expert">status: '
        + ("<b>armed</b> — runs by itself" if lg_v.get("wirksam") else
           html.escape(t("erkennung.status.vision_aus")
                       if not v_aktiv else t("erkennung.status.hier_aus")))
        # §8.14 Slice-vor-Format: v_erkl ist Whitelist-DATEN mit [:180].
        + f'<br>{html.escape(v_erkl[:180])}&#8230;</div>'
        + '<div class="ek-fuss">'
          '<a class="ek-knopf" href="/vision">'
        + t("erkennung.vision.knopf_connect") + '</a>'
          # Register vision (User-Entscheid 16.08.) fuehrt zum Galerien-
          # Bereich der Vision-Seite: dort wohnt "Build a gallery", und die
          # Karten erklaeren ehrlich die Vorbedingung (abgenommenes
          # Koerper-Material aus dem Person-learn-Weg).
          '<a class="ek-knopf" style="margin-top:6px" href="/vision#galerien">'
        + t("erkennung.vision.knopf_register") + '</a></div></div>')

    # Versteckte cfg-Felder: konfigSpeichern() sammelt [id^=cfg-] der Seite ein
    # — exakt der /kette-Save-Weg (auditiert, sauberer Neustart).
    def _sel(key, wert):
        opts = "".join(f'<option{" selected" if wert == o else ""}>{o}</option>'
                       for o in (whitelist.get(key) or (None, [],))[1])
        return f'<select id="cfg-{key}" style="display:none">{opts}</select>'

    script = """
<script>
var ekDirty = false;
function ekFeld(id){return document.getElementById(id);}
function ekMarkieren(){ekDirty = true;
  var s=document.getElementById('cfg-status');
  if(s) s.textContent='changed — Save + restart applies it';}
/* .210 (User 16.08.): wer mit ungesicherten Body/Vision-Aenderungen die Seite
   verlaesst (Zuruecktaste, Link), bekommt den Browser-Warn-Dialog. Der
   Live-Kipp zaehlt nicht als ungesichert — er wirkt sofort. */
window.addEventListener('beforeunload', function(e){
  if (ekDirty) { e.preventDefault(); e.returnValue = ''; }
});
function ekKipp(k, key){
  if(k.classList.contains('fest')) return;
  var an = !k.classList.contains('an');
  k.classList.toggle('an', an);
  k.setAttribute('aria-checked', an ? 'true' : 'false');
  var karte = k.closest('.ek-card');
  karte.classList.toggle('aus', !an);
  var sel = ekFeld('cfg-' + key);
  if (an) {
    var u = karte.querySelector('.ek-unter button.an');
    sel.value = u ? u.getAttribute('data-wert') || ekUnterWert(u) : 'immer';
  } else { sel.value = 'aus'; }
  ekMarkieren();
}
function ekUnterWert(b){var t=b.textContent;
  return t==='Always' ? 'immer' : 'nur_wenn_gesicht_leer';}
function ekUnter(b, wert){
  var u = b.closest('.ek-unter');
  u.querySelectorAll('button').forEach(function(x){
    x.classList.toggle('an', x===b);});
  var sel = ekFeld(u.getAttribute('data-feld'));
  if (sel && !b.closest('.ek-card').classList.contains('aus')) {
    sel.value = wert; ekMarkieren();
  }
}
document.addEventListener('DOMContentLoaded', function(){
  var sb = document.querySelector('button.gtb.on');
  if (sb) sb.addEventListener('click', function(){ ekDirty = false; });
});
function ekLive(k){
  var an = !k.classList.contains('an');
  k.style.pointerEvents='none';
  fetch('/erkennung_live', {method:'POST',
        body: JSON.stringify({an: an})})
    .then(function(r){return r.json();})
    .then(function(d){
      var s=document.getElementById('cfg-status');
      if(s) s.textContent=d.msg;
      setTimeout(function(){location.reload();}, 900);
    })
    .catch(function(){location.reload();});
}
</script>"""

    return (
        f'<h2>{t("erkennung.titel")}</h2>'
        f'<p class="sub">{t("erkennung.kopf.satz")}</p>'
        '<div class="ek-grid">' + live + ges + koerper + vision + "</div>"
        # .222 (User 16.08.: Areas gehoert zu Configuration, nicht in die
        # Hauptnavigation): zweite, kleinere Kachel-Reihe "Property set-up"
        # unter den vier Erkennungswegen — natuerlicher Platz fuer weitere
        # Einrichtungs-Themen.
        + (f'<h3 class="ek-abschnitt">{t("erkennung.abschnitt_property")}</h3>'
           '<div class="ek-grid"><div class="ek-card" id="ek-areas">'
           f'<h3>&#128506; {t("erkennung.areas.titel")}</h3>'
           f'<p class="ek-satz">{t("erkennung.areas.satz")}</p>'
           '<div class="ek-beweis">'
           # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
           + (f'<b>{n_areas}</b> ' + t("erkennung.areas.beweis_zahl")
              if n_areas else t("erkennung.areas.beweis_keine"))
           + '</div><div class="ek-fuss"><a class="ek-knopf" href="/areas">'
           + t("erkennung.areas.knopf") + '</a></div></div></div>'
           if n_areas is not None else "")
        + _sel("person_pfad", p_stufe) + _sel("vision_pfad", v_stufe)
        + '<p><button class="gtb on" onclick="konfigSpeichern()">'
        + t("erkennung.knopf_speichern") + '</button> '
          '<span id="cfg-status" style="color:var(--dim)"></span></p>'
        # Stufe-0-Grenze: zwei <a>-Links mitten im Satz — bleibt literal.
        + '<p class="sub nur-expert">Every switch here writes the same '
          'audited settings as <a href="/kette">Recognition chain</a> and '
          'the <a href="/live">Live tab</a> — one value, shown in one more '
          "place.</p>"
        + script)
