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
             wie /kette: auditiert + sauberer Neustart). Darunter seit Stufe
             KW12 (Bauplan analysen/bauplan_koerperweg_neu.md) die Zeile
             "Meldet an:" mit den gewaehlten Wegen und das Gitter mit den
             Melde-Schaltern (Frigate, Pushover, Telegram, Home Assistant;
             Namen aus core.koerperweg.MELDE_SCHALTER), seit Stufe EK1
             (Bauplan analysen/bauplan_erkennung_karte.md) offen sichtbar;
             je Schalter ein verstecktes cfg-Feld, gespeichert wie der Modus.
             Ein Kanal ohne Einrichtung (core.melden.konfigurierte_kanaele,
             Frigate: sub_label_schreiben) traegt "nicht eingerichtet" mit
             Link. Darunter seit EK1 die Wahl "Lernlauf starten"
             (cfg-koerper_lauf, Stellungen aus routes.koerperbilder._LAUF),
             seit FN2 (Bauplan analysen/bauplan_feldnachzug_0110.md) darunter
             der Kipp "Neue Bilder automatisch uebernehmen" mit dem
             versteckten Feld cfg-koerper_sichtpruefung (umgekehrt); die
             Seite Koerperbilder traegt beide nicht mehr.
  Speichern -> seit EK1 die Leiste ek-savebar, die unten am Bildschirmrand
             klebt: ohne Aenderung ruhig mit aria-disabled, nach jeder
             Aenderung (ekMarkieren) hervorgehoben; der Klick speichert ueber
             konfigSpeichern (webui/app.js).
  Vision  -> vision_pfad  (dito).
  Gesicht -> hat heute KEINEN Aus-Schalter (Rueckgrat der Kette, person/vision
             haengen an seinem Pass-Urteil) — der Kipp ist sichtbar VERRIEGELT
             und sagt das ehrlich, statt einen toten Schalter zu spielen.

Injektion pur (Muster routes/konfiguration.py): alles kommt als Parameter,
dieses Modul importiert verifyd nie.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py — u. a. bleiben die Saetze mit
Inline-Markup und die JS-Statustexte literal; der _unter-Schleifenname `t`
wurde zu `txt` umbenannt, damit er t() nicht verschattet. Die Unteroptions-
Labels kommen seit Stufe KW12 aus erkennung.unter.*, die Knoepfe tragen
ihren Wert in data-wert (ekUnterWert, der den Button-TEXT verglich, ist
entfallen)."""
import html

from core.koerperweg import MELDE_SCHALTER
from core.melden import konfigurierte_kanaele
from core.sprache import t
from routes.koerperbilder import _LAUF   # Stufe EK1: die Stellungen von koerper_lauf, gelesen, nicht kopiert


def _kipp(an, verriegelt=False, onclick="", titel=None, label=None):
    # Bauplan analysen/bauplan_koerperweg_neu.md, Stufe KW9 Punkt 2: titel ersetzt den Text der gesperrten Karte
    # Gesicht (geparktes Vision traegt den Parksatz); maskiert ins Attribut. Stufe KW12: label ersetzt
    # erkennung.kipp.label (Zellen der Melde-Schalter).
    k = ('<span class="ek-kipp%s%s" role="switch" aria-checked="%s"%s%s></span>'
         % (" an" if an else "", " fest" if verriegelt else "",
            "true" if an else "false",
            f' title="{html.escape(titel, quote=True)}"' if titel else
            f' title="{t("erkennung.kipp.attr_verriegelt")}"'
            if verriegelt else "",
            f' onclick="{onclick}"' if onclick else ""))
    return ('<div class="ek-kippzeile"><span class="ek-zl">'
            + (label or t("erkennung.kipp.label")) + '</span>' + k + "</div>")


def _unter(feld_id, wert, opts, onclick_js):
    """Modus-Unteroption (nur sichtbar, wenn der Weg an ist)."""
    kn = "".join(
        f'<button type="button"{" class=an" if wert == o else ""} data-wert="{o}" '
        f'onclick="{onclick_js}(this,\'{o}\')">{html.escape(txt)}</button>'
        for o, txt in opts)
    return f'<div class="ek-unter" data-feld="{feld_id}">{kn}</div>'


_MELDE_NAMEN = ("Frigate", "Pushover", "Telegram", "Home Assistant")   # Eigennamen, Reihenfolge wie MELDE_SCHALTER
_ANWESENHEIT = "koerper_meldet_anwesenheit"   # Stufe KW14: der fuenfte Schalter, eigene Zeile unter dem Gitter


def _melden(cfg):
    """Die Zeile „Meldet an“ der Karte Koerper mit dem Gitter der Melde-Schalter (Stufe KW12, Abschnitt Oberflaeche; seit
    Stufe EK1 offen) und darunter der Zeile „Seite Anwesenheit“ (Stufe KW14 Punkt 8, ohne Kanal).
    -> (HTML des Blocks, HTML der versteckten cfg-Felder)"""
    kanaele = konfigurierte_kanaele(cfg)
    bereit = (bool(cfg.get("sub_label_schreiben")), "pushover" in kanaele, "telegram" in kanaele, "mqtt" in kanaele)
    namen = dict(zip(MELDE_SCHALTER, _MELDE_NAMEN + (t("erkennung.koerper.melden.anwesenheit"),)))
    gewaehlt = [namen[k] for k in MELDE_SCHALTER if cfg.get(k)]
    zellen = "".join(
        f'<div class="ek-melden-zelle" data-name="{n}">'
        + _kipp(bool(cfg.get(k)), onclick=f"ekMelden(this,'{k}')", label=n)
        + ("" if ok else f'<a class="ek-melden-fehlt" href="/benachrichtigungen">'
           f'{t("erkennung.koerper.melden.nicht_eingerichtet")}</a>')
        + "</div>" for k, n, ok in zip(MELDE_SCHALTER, _MELDE_NAMEN, bereit))   # zip endet nach den vier Meldewegen
    n = html.escape(namen[_ANWESENHEIT], quote=True)
    zellen += (f'<div class="ek-melden-zelle ek-melden-anw" data-name="{n}">'
               + _kipp(bool(cfg.get(_ANWESENHEIT)), onclick=f"ekMelden(this,'{_ANWESENHEIT}')", label=n) + "</div>")
    block = ('<div class="ek-melden-block"><div class="ek-melden">'
             f'<span>{t("erkennung.koerper.melden.titel")} <span id="kw-melden-wege" '
             f'data-leer="{html.escape(t("erkennung.koerper.melden.nur_anzeige"), quote=True)}">'
             + (f'<b>{html.escape(", ".join(gewaehlt))}</b>' if gewaehlt
                else t("erkennung.koerper.melden.nur_anzeige"))
             + '</span></span></div>'
             f'<div id="kw-melden-gitter" class="ek-melden-gitter" role="group" '
             f'aria-label="{html.escape(t("erkennung.koerper.melden.aria"), quote=True)}">{zellen}'
             f'<p class="ek-melden-leer"{" hidden" if gewaehlt else ""}>{t("erkennung.koerper.melden.leer")}</p>'
             '</div></div>')
    felder = "".join(f'<input type="hidden" id="cfg-{k}" value="{"true" if cfg.get(k) else "false"}">'
                     for k in MELDE_SCHALTER)
    return block, felder


def render(cfg, whitelist, lage, waechter, gesicht, n_areas=None):
    """-> Seiten-INHALT /erkennung.
    waechter = {"an": n_laufend, "eingerichtet": n_eingerichtet}
    gesicht  = {"personen": n, "bilder": n}
    n_areas  = Zahl der Areas (None = Zeile weglassen, Alt-Aufrufer).
    (Der Parameter modell — Status des alten Personenmodells — ist mit Stufe KW6 des Bauplans
    analysen/bauplan_koerperweg_neu.md entfallen; die Karte Koerper liest ihren Stand aus lage.)"""
    lg_p = (lage or {}).get("person") or {}
    lg_v = (lage or {}).get("vision") or {}
    p_stufe = cfg.get("person_pfad") or "immer"
    v_stufe = cfg.get("vision_pfad") or "immer"
    v_aktiv = bool((cfg.get("vision") or {}).get("aktiv"))
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
    melden_block, melden_felder = _melden(cfg)
    # Bauplan analysen/bauplan_erkennung_karte.md, Stufe EK1 Punkte 2 und 3: Wahl des Lernlaufs in der Karte, gespeichert
    # wie jedes Feld cfg-* der Seite; die Statuszeile nur noch, wenn der Weg nicht wirksam ist, mit dem Grund aus lage()
    # (Stufe KW5 Punkt 9 des Bauplans analysen/bauplan_koerperweg_neu.md: kein gueltiges Bild, Pose-Modell fehlt, hier aus).
    lauf_wahl = cfg.get("koerper_lauf")
    # Klasse ek-lauf (Punkt 7): die Zeile bricht bei 360 px um, statt die Karte zu verbreitern
    lauf = ('<div class="ek-kippzeile ek-lauf"><label class="ek-zl" for="cfg-koerper_lauf">'
            + html.escape(t("koerperbilder.auto.lauf")) + '</label>'
            '<select id="cfg-koerper_lauf" onchange="ekMarkieren()">'
            + "".join(f'<option value="{w}"{" selected" if w == lauf_wahl else ""}>{html.escape(t(k))}</option>'
                      for w, k in _LAUF)
            + '</select></div>')
    # Bauplan analysen/bauplan_feldnachzug_0110.md, Stufe FN2 Punkt 2: „Neue Bilder automatisch uebernehmen“ unter dem
    # Lernlauf; an heisst koerper_sichtpruefung aus, das versteckte Feld traegt den Wert der Config (Muster _melden)
    pruef = bool(cfg.get("koerper_sichtpruefung"))
    lauf += (_kipp(not pruef, onclick="ekUebernehmen(this)", label=html.escape(t("koerperbilder.auto.uebernehmen")))
             + f'<input type="hidden" id="cfg-koerper_sichtpruefung" value="{"true" if pruef else "false"}">')
    p_status = ("" if lg_p.get("wirksam") else
                '<div class="ek-beweis nur-expert">'
                + html.escape(t("erkennung.status.kein_vorrat") if not lg_p.get("vorrat") else
                              t("erkennung.status.pose_fehlt") if lg_p.get("grund") else
                              t("erkennung.status.hier_aus")) + '</div>')
    koerper = (
        '<div class="ek-card' + ("" if p_stufe != "aus" else " aus")
        + '" id="ek-koerper">'
        f'<h3>&#128694; {t("erkennung.koerper.titel")}</h3>'
        + _kipp(p_stufe != "aus", onclick="ekKipp(this,'person_pfad')")
        # Stufe KW12: Labels aus erkennung.unter.*, der Wert steht in data-wert.
        + _unter("cfg-person_pfad", p_stufe,
                 [("immer", t("erkennung.unter.immer")),
                  ("nur_wenn_gesicht_leer", t("erkennung.unter.nur_ohne_gesicht"))], "ekUnter")
        + f'<p class="ek-satz">{t("erkennung.koerper.satz")}</p>'
        + melden_block + lauf + p_status
        # KW6: der Knopf fuehrt auf die Seite der Koerperbilder (die alten Seiten /personlauf sind ausgebaut)
        + '<div class="ek-fuss"><a class="ek-knopf" href="/koerperbilder">'
        + t("erkennung.koerper.knopf_register") + '</a></div></div>')

    # --- Vision
    vis_beweis = (t("erkennung.vision.beweis_an") if v_aktiv
                  else t("erkennung.vision.beweis_aus"))
    # Bauplan analysen/bauplan_koerperweg_neu.md, Stufe KW9 Punkte 1 und 2: geparkt (lage traegt den Grund) ist die
    # Karte aus, der Kipp fest mit dem Parksatz; ohne Unterwahl, Anleitung, Statuszeile, Knoepfe und ohne cfg-Feld.
    v_geparkt = bool(lg_v.get("grund"))
    park = t("vision.geparkt_satz")
    if v_geparkt:
        vision = (
            '<div class="ek-card aus" id="ek-vision">'
            f'<h3>&#128302; {t("erkennung.vision.titel")} '
            f'<span class="ek-beta">{t("erkennung.vision.beta")}</span></h3>'
            + _kipp(False, verriegelt=True, titel=park)
            + f'<p class="ek-satz">{t("erkennung.vision.satz")}</p>'
            + f'<div class="ek-beweis">{html.escape(park)}</div></div>')
    else:
        vision = (
            '<div class="ek-card' + ("" if v_stufe != "aus" and v_aktiv
                                     else " aus") + '" id="ek-vision">'
            # .219 (User 16.08.): der Vision-Bereich traegt sichtbar "Beta" — der
            # Nutzer soll wissen, dass dieser Weg noch reift (Misch-Gitter-Frage,
            # Kalibrier-Test offen), bevor er sich auf ihn verlaesst.
            f'<h3>&#128302; {t("erkennung.vision.titel")} '
            f'<span class="ek-beta">{t("erkennung.vision.beta")}</span></h3>'
            + _kipp(v_stufe != "aus", onclick="ekKipp(this,'vision_pfad')")
            # Stufe KW12: Labels aus erkennung.unter.* (s. Koerper).
            + _unter("cfg-vision_pfad", v_stufe,
                     [("immer", t("erkennung.unter.immer")),
                      ("nur_wenn_gesicht_leer", t("erkennung.unter.wenn_noetig"))], "ekUnter")
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
/* Stufe EK1 (Bauplan analysen/bauplan_erkennung_karte.md): jede Aenderung hebt die Speicherleiste hervor. */
function ekMarkieren(){ekDirty = true;
  ekFeld('ek-savebar').classList.add('offen');
  var k = ekFeld('ek-speichern');
  k.classList.add('on'); k.setAttribute('aria-disabled', 'false');
  var z = ekFeld('ek-save-zustand');
  z.textContent = z.getAttribute('data-offen');}
/* Ohne Aenderung tut der Klick nichts. konfigSpeichern schreibt cfg-status erst nach dem Ja der Rueckfrage: bleibt die
   Zeile leer, hat der Nutzer abgebrochen, und die Seite bleibt "nicht gespeichert" samt Abfrage beim Verlassen. */
function ekSpeichern(k){
  if (k.getAttribute('aria-disabled') === 'true') return;
  var s = ekFeld('cfg-status');
  s.textContent = '';
  konfigSpeichern();
  ekDirty = !s.textContent;
}
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
    sel.value = u ? u.getAttribute('data-wert') : 'immer';
  } else { sel.value = 'aus'; }
  ekMarkieren();
}
/* Stufe KW12: Melde-Schalter der Koerper-Erkennung. Ein Klick setzt nur das versteckte Feld und die Zeile
   "Meldet an"; gespeichert wird mit dem Knopf wie der Modus. */
function ekMelden(k, key){
  var an = !k.classList.contains('an');
  k.classList.toggle('an', an);
  k.setAttribute('aria-checked', an ? 'true' : 'false');
  ekFeld('cfg-' + key).value = an ? 'true' : 'false';
  var namen = [];
  document.querySelectorAll('.ek-melden-zelle').forEach(function(z){
    if (z.querySelector('.ek-kipp.an')) namen.push(z.getAttribute('data-name'));});
  var w = ekFeld('kw-melden-wege');
  w.textContent = '';
  if (namen.length) { var b = document.createElement('b'); b.textContent = namen.join(', '); w.appendChild(b); }
  else { w.textContent = w.getAttribute('data-leer'); }
  document.querySelector('.ek-melden-leer').hidden = namen.length > 0;
  ekMarkieren();
}
/* Stufe FN2: Kipp "Neue Bilder automatisch uebernehmen"; an heisst Sichtpruefung aus, das Feld traegt den umgekehrten
   Wert, gespeichert wird mit der Leiste. */
function ekUebernehmen(k){
  var an = !k.classList.contains('an');
  k.classList.toggle('an', an);
  k.setAttribute('aria-checked', an ? 'true' : 'false');
  ekFeld('cfg-koerper_sichtpruefung').value = an ? 'false' : 'true';
  ekMarkieren();
}
function ekUnter(b, wert){
  var u = b.closest('.ek-unter');
  u.querySelectorAll('button').forEach(function(x){
    x.classList.toggle('an', x===b);});
  var sel = ekFeld(u.getAttribute('data-feld'));
  if (sel && !b.closest('.ek-card').classList.contains('aus')) {
    sel.value = wert; ekMarkieren();
  }
}
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
        # KW9 Punkt 2: geparkt kein Feld vision_pfad, sonst lehnte config_schreiben jedes Speichern der Seite ab
        + _sel("person_pfad", p_stufe) + ("" if v_geparkt else _sel("vision_pfad", v_stufe)) + melden_felder
        # Stufe-0-Grenze: zwei <a>-Links mitten im Satz — bleibt literal.
        + '<p class="sub nur-expert">Every switch here writes the same '
          'audited settings as <a href="/kette">Recognition chain</a> and '
          'the <a href="/live">Live tab</a> — one value, shown in one more '
          "place.</p>"
        # Stufe EK1 Punkt 4: die Speicherleiste klebt unten; aria-disabled statt disabled, damit der Knopf fokussierbar
        # bleibt (W3C); den Text "nicht gespeichert" setzt ekMarkieren aus data-offen.
        + '<div class="ek-savebar" id="ek-savebar">'
          '<button type="button" class="gtb" id="ek-speichern" aria-disabled="true" onclick="ekSpeichern(this)">'
        + t("erkennung.knopf_speichern") + '</button>'
          '<span class="ek-save-zustand" id="ek-save-zustand" '
        + f'data-offen="{html.escape(t("erkennung.save.offen"), quote=True)}">'
        + html.escape(t("erkennung.save.sauber")) + '</span>'
          '<span id="cfg-status" style="color:var(--dim)"></span></div>'
        + script)
