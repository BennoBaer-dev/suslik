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
dieses Modul importiert verifyd nie."""
import html


def _kipp(an, verriegelt=False, onclick=""):
    k = ('<span class="ek-kipp%s%s" role="switch" aria-checked="%s"%s%s></span>'
         % (" an" if an else "", " fest" if verriegelt else "",
            "true" if an else "false",
            ' title="always on — every other method builds on the face '
            'verdict"' if verriegelt else "",
            f' onclick="{onclick}"' if onclick else ""))
    return ('<div class="ek-kippzeile"><span class="ek-zl">Enabled</span>'
            + k + "</div>")


def _unter(feld_id, wert, opts, onclick_js):
    """Modus-Unteroption (nur sichtbar, wenn der Weg an ist)."""
    kn = "".join(
        f'<button type="button"{" class=an" if wert == o else ""} '
        f'onclick="{onclick_js}(this,\'{o}\')">{html.escape(t)}</button>'
        for o, t in opts)
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
    live_beweis = (f'watching <b>{waechter["an"]} of '
                   f'{waechter["eingerichtet"]}</b> set-up cameras'
                   if live_an else
                   (f'<b>{waechter["eingerichtet"]}</b> camera(s) set up, '
                    'none running' if waechter["eingerichtet"]
                    else "no watcher set up yet"))
    live = (
        '<div class="ek-card' + ("" if live_an else " aus") + '" id="ek-live">'
        '<h3>&#128680; Live watch</h3>'
        + _kipp(live_an, onclick="ekLive(this)")
        + '<p class="ek-satz">Alerts the <b>moment</b> someone steps onto '
          'the property — seconds after the camera sees them, with a '
          'preliminary name.</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/live">'
          'How it works &#8230;</a></div>'
        + f'<div class="ek-beweis">{live_beweis}</div>'
        + '<div class="ek-beweis nur-expert">switching off stops every '
          'running watcher; switching on starts all set-up watchers (the '
          'per-camera gate still applies) · '
          '<a href="/live">per-camera control</a></div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/live">'
          'Choose cameras …</a>'
          # User 16.08.: die Live-Namensstufe urteilt mit DENSELBEN
          # Gesichts-Referenzen wie der Face-Weg — gleicher Knopf,
          # gleiches Ziel auf beiden Kacheln.
          '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
          'Register face …</a></div></div>')

    # --- Gesicht
    ges = (
        '<div class="ek-card" id="ek-gesicht">'
        '<h3>&#128578; Face recognition</h3>'
        + _kipp(True, verriegelt=True)
        + '<p class="ek-satz">The most precise way: every pass is checked '
          'against the faces of the people you taught the system. It is the '
          'backbone — body and vision hang off its walk-through verdict, so '
          'it has no off switch today.</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/gesicht">'
          'How it works &#8230;</a></div>'
        + (f'<div class="ek-beweis"><b>{gesicht["personen"]} people</b> · '
           f'{gesicht["bilder"]} reference images</div>')
        + '<div class="ek-beweis nur-expert">model and thresholds live under '
          '<a href="/konfiguration">Advanced</a> · chain order on '
          '<a href="/kette">Recognition chain</a></div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/gesichter">'
          'Manage people …</a>'
          # .208 (User-Entscheid 16.08.: JEDE Kachel hat ihren eigenen
          # Register-Knopf mit dem Namen ihres Wegs; Leitsatz: Registrieren
          # richtet sich nach dem, was eingeschaltet ist): Face registriert
          # ueber den Gesichts-Lernlauf (aus dem Betrieb, kein Upload).
          '<a class="ek-knopf" style="margin-top:6px" href="/lernlauf">'
          'Register face …</a></div></div>')

    # --- Koerper
    m = modell or {}
    if m.get("bilder"):
        ei = m.get("eichung") or {}
        k_beweis = (f'model trained (<b>{m.get("bilder")}</b> images'
                    + (f', calibrated against <b>{ei.get("n_fremd")}</b> '
                       f'strangers' if ei.get("n_fremd") else "")
                    + (")" if m.get("scharf") else ") · <b>not armed</b>"))
    else:
        k_beweis = "no person model yet — learn and review first"
    koerper = (
        '<div class="ek-card' + ("" if p_stufe != "aus" else " aus")
        + '" id="ek-koerper">'
        '<h3>&#128694; Body recognition</h3>'
        + _kipp(p_stufe != "aus", onclick="ekKipp(this,'person_pfad')")
        + _unter("cfg-person_pfad", p_stufe,
                 [("immer", "Always"),
                  ("nur_wenn_gesicht_leer", "Only if no face")], "ekUnter")
        + '<p class="ek-satz">Recognizes household members even when no face '
          'is visible, by build and posture — it learns from the reviewed '
          'pictures by itself.</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/koerper">'
          'How it works &#8230;</a></div>'
        + f'<div class="ek-beweis">{k_beweis}</div>'
        + '<div class="ek-beweis nur-expert">status: '
        + ("<b>armed</b> — runs by itself" if lg_p.get("wirksam") else
           html.escape("not running (no trained person model armed yet)"
                       if not lg_p.get("modell_scharf") else
                       "not running (switched off here)"))
        + f' · <a href="/personlauf">model status</a><br>'
          f'{html.escape(p_erkl[:180])}&#8230;</div>'
        + '<div class="ek-fuss"><a class="ek-knopf" href="/personlauf">'
          'Model status …</a>'
          '<a class="ek-knopf" style="margin-top:6px" href="/personlauf">'
          'Register body …</a></div></div>')

    # --- Vision
    vis_beweis = ("endpoint connected" if v_aktiv
                  else "no endpoint connected")
    vision = (
        '<div class="ek-card' + ("" if v_stufe != "aus" and v_aktiv
                                 else " aus") + '" id="ek-vision">'
        # .219 (User 16.08.): der Vision-Bereich traegt sichtbar "Beta" — der
        # Nutzer soll wissen, dass dieser Weg noch reift (Misch-Gitter-Frage,
        # Kalibrier-Test offen), bevor er sich auf ihn verlaesst.
        '<h3>&#128302; AI vision <span class="ek-beta">Beta</span></h3>'
        + _kipp(v_stufe != "aus", onclick="ekKipp(this,'vision_pfad')")
        + _unter("cfg-vision_pfad", v_stufe,
                 [("immer", "Always"),
                  ("nur_wenn_gesicht_leer", "If needed")], "ekUnter")
        + '<p class="ek-satz">A picture-AI as referee for the hard cases. '
          'Needs a model endpoint (local or paid) — every check costs '
          'requests.</p>'
        + '<div class="ek-hilfe"><a href="/hilfe/vision">'
          'How it works &#8230;</a></div>'
        + f'<div class="ek-beweis">{vis_beweis}</div>'
        + '<div class="ek-beweis nur-expert">status: '
        + ("<b>armed</b> — runs by itself" if lg_v.get("wirksam") else
           html.escape("not running (vision detect is switched off)"
                       if not v_aktiv else "not running (switched off here)"))
        + f'<br>{html.escape(v_erkl[:180])}&#8230;</div>'
        + '<div class="ek-fuss">'
          '<a class="ek-knopf" href="/vision">Connect a model …</a>'
          # Register vision (User-Entscheid 16.08.) fuehrt zum Galerien-
          # Bereich der Vision-Seite: dort wohnt "Build a gallery", und die
          # Karten erklaeren ehrlich die Vorbedingung (abgenommenes
          # Koerper-Material aus dem Person-learn-Weg).
          '<a class="ek-knopf" style="margin-top:6px" href="/vision#galerien">'
          'Register vision …</a></div></div>')

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
        "<h2>Recognition</h2>"
        '<p class="sub">The four ways your system can recognize someone — '
        "each one is its own card: switch it, see that it works, set it up. "
        'The Live switch acts immediately; body and vision changes apply '
        "with Save + restart.</p>"
        '<div class="ek-grid">' + live + ges + koerper + vision + "</div>"
        # .222 (User 16.08.: Areas gehoert zu Configuration, nicht in die
        # Hauptnavigation): zweite, kleinere Kachel-Reihe "Property set-up"
        # unter den vier Erkennungswegen — natuerlicher Platz fuer weitere
        # Einrichtungs-Themen.
        + ('<h3 class="ek-abschnitt">Property set-up</h3>'
           '<div class="ek-grid"><div class="ek-card" id="ek-areas">'
           '<h3>&#128506; Areas</h3>'
           '<p class="ek-satz">Where on the property counts: draw areas so '
           'alerts only fire where you care — the driveway matters, the '
           'street behind the fence does not.</p>'
           '<div class="ek-beweis">'
           + (f"<b>{n_areas}</b> area(s) defined" if n_areas else
              "no areas yet — everything counts")
           + '</div><div class="ek-fuss"><a class="ek-knopf" href="/areas">'
             'Manage areas &#8230;</a></div></div></div>'
           if n_areas is not None else "")
        + _sel("person_pfad", p_stufe) + _sel("vision_pfad", v_stufe)
        + '<p><button class="gtb on" onclick="konfigSpeichern()">'
          'Save + restart</button> '
          '<span id="cfg-status" style="color:var(--dim)"></span></p>'
        + '<p class="sub nur-expert">Every switch here writes the same '
          'audited settings as <a href="/kette">Recognition chain</a> and '
          'the <a href="/live">Live tab</a> — one value, shown in one more '
          "place.</p>"
        + script)
