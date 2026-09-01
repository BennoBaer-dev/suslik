/* verifyd Web UI — central JS (AP3): GT labeling, previously duplicated per page. */
/* Config sheet (AP5): collect whitelist values, confirm, save, restart */

/* ── Sprach-Stufe 1 (konzept_sprache.md B3/B4): window.T traegt die
   js.*-Schluessel der aktiven Sprache (das Seitenskelett injiziert sie als
   json.dumps). TT() liest mit ENGLISCHEM Literal-Fallback — fehlt die
   Tabelle oder der Schluessel, bleibt die Seite exakt englisch. Platzhalter
   sind {name}-Felder wie in core/texte (split/join statt Regex: kein
   Escaping-Risiko). VERTRAG: app.js nutzt Texte NUR ueber TT() mit
   js.*-Schluesseln; beide Richtungen prueft die Gate-Stufe Sprach-Deckung. */
function TT(key, fb, kw) {
  var s = (window.T && window.T[key]) || fb;
  if (kw) { Object.keys(kw).forEach(function (k) {
    s = s.split('{' + k + '}').join(String(kw[k]));
  }); }
  return s;
}

/* Sprachwahl (Kopfleisten-Menue + Wizard-Schritt 0): POST an
   /sprache_speichern (Areas-Muster, kein Neustart), dann Reload. Ein
   delegierter Listener deckt beide Einbauorte (.sp-knopf[data-s]). */
document.addEventListener('click', function (ev) {
  var b = ev.target && ev.target.closest ? ev.target.closest('.sp-knopf[data-s]') : null;
  if (!b) {
    /* Klick neben das offene Kopfleisten-Menue schliesst es */
    var w = document.getElementById('sprache-wahl');
    if (w && w.open && !w.contains(ev.target)) w.open = false;
    return;
  }
  b.disabled = true;
  fetch('/sprache_speichern', {method: 'POST',
                               body: JSON.stringify({sprache: b.getAttribute('data-s')})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) { location.reload(); }
      else { alert(d.msg || TT('js.status.fehler', 'error')); b.disabled = false; }
    })
    .catch(function () { b.disabled = false; });
});

/* Shared: nach einem Selbst-Neustart (re-exec) warten bis der Dienst wieder antwortet, dann weiter.
   Erkennt die Restart-Grenze robust als "erst unten, dann wieder oben" — kein fixer Timer, der den
   ~20s Reinit/Modell-Load ueberholt und in ein "Seite kann nicht laden" rennt. */
function _neustartDann(ziel, s) {
  var start = Date.now(), MAX = 120000, warUnten = false;
  function txt(m) { if (s) s.textContent = m; }
  function tick() {
    if (Date.now() - start > MAX) { location.href = ziel; return; }   /* Deckel: trotzdem weiter */
    fetch('/health', {cache: 'no-store'})
      .then(function (r) {
        if (r.ok && warUnten) { txt(TT('js.neustart.zurueck', 'Service is back, loading …')); location.href = ziel; return; }
        txt(warUnten ? TT('js.neustart.kommt', 'Service coming back …')
                     : TT('js.neustart.gespeichert', 'Saved. Restarting service, please wait …'));
        setTimeout(tick, 1500);
      })
      .catch(function () { warUnten = true; txt(TT('js.neustart.warten', 'Restarting service, please wait …')); setTimeout(tick, 1500); });
  }
  tick();
}

function konfigSpeichern() {
  var felder = document.querySelectorAll('[id^="cfg-"]'),
      d = {}, s = document.getElementById('cfg-status');
  for (var i = 0; i < felder.length; i++) {
    d[felder[i].id.slice(4)] = felder[i].value;
  }
  if (!confirm(TT('js.konfig.frage', 'Save configuration and restart the service?'))) return;
  s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/konfig', {method: 'POST', body: JSON.stringify(d)})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      s.textContent = r.msg;
      /* B6: eine reine debug-Aenderung wirkt live, der Dienst geht dabei nicht
         unten durch — dann NICHT auf die Neustart-Grenze warten (die Schleife
         liefe sonst bis in ihren 120-s-Deckel), sondern sofort neu laden. */
      if (r.ok) { if (r.neustart === false) { location.reload(); } else { _neustartDann(location.href, s); } }
    })
    .catch(function () { _neustartDann(location.href, s); });
}

/* Notifications sheet: collect channel fields (ids "n-*") + checked categories, save, restart;
   per-channel live "Test" sends a real message with the current form values (a blank secret field keeps the stored value). */
function _notifFelder() {
  var d = {}, felder = document.querySelectorAll('[id^="n-"]');
  for (var i = 0; i < felder.length; i++) d[felder[i].id.slice(2)] = felder[i].value;
  var cats = [], cb = document.querySelectorAll('.n-cat');
  for (var j = 0; j < cb.length; j++) if (cb[j].checked) cats.push(cb[j].value);
  d.alert_kategorien = cats;
  return d;
}

function llFpsUpdate(el) {
  var out = document.getElementById('ll-fps-est');
  if (!out) return;
  var a = parseFloat(el.getAttribute('data-analyse')) || 0;
  var r = parseFloat(el.getAttribute('data-rest')) || 0;
  var fps = parseFloat(el.value) || 3;
  if (!a) { out.textContent = ''; return; }
  var s = Math.round(a * (fps / 3) + r);
  var dauer = s >= 60 ? TT('js.einheit.min', '{n} min', {n: Math.round(s / 60)})
                      : TT('js.einheit.s', '{n} s', {n: s});
  out.textContent = TT('js.lernlauf.fps_zeile', '≈ total ~{dauer} at {fps}/s',
                       {dauer: dauer, fps: fps});
}

function lernlaufStart(n, btn) {
  var frage = btn.getAttribute('data-frage');
  if (frage && !confirm(frage)) return;
  btn.disabled = true;
  var fpsEl = document.getElementById('ll-fps');
  var fps = fpsEl ? parseFloat(fpsEl.value) : 0;
  fetch('/lernlauf_start', {method: 'POST',
                            body: JSON.stringify({events: n, fps: fps || 0})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      document.getElementById('ll-status').textContent =
        d.msg || (d.ok ? TT('js.status.ok', 'ok') : TT('js.status.fehler', 'error'));
      if (d.ok) setTimeout(function () { location.href = '/lernlauf'; }, 500);
      else btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

function lernlaufPopupStart(btn) {
  /* .259 Such-Popup (Mockup-Abnahme): Events + Bilder/s + Zielperson lesen;
     person leer = alle Gesichter. Eigene Feld-IDs (lf-pop-*), damit der
     Expert-Planer (ll-fps/ll-status) nicht kollidiert. */
  var n = parseInt(document.getElementById('lf-pop-n').value) || 0;
  var fps = parseFloat(document.getElementById('lf-pop-fps').value) || 0;
  var z = document.getElementById('lf-ziel');
  var person = (z && !z.disabled) ? z.value : '';
  var w = document.getElementById('lf-weiter');
  /* .263 Wechselschalter: Tages-Modus schickt tag statt events. */
  var tEl = document.getElementById('lf-pop-tag');
  var tag = (tEl && !tEl.disabled) ? tEl.value : '';
  if (tEl && !tEl.disabled && !tag) {
    document.getElementById('lf-pop-status').textContent = TT('js.lernlauf.tag_fehlt', 'pick a day first');
    return;
  }
  btn.disabled = true;
  var body = {fps: fps, person: person, weiter: !!(w && w.checked)};
  /* .358 Ernte-Vorfilter: gewaehlte Kameras mitschicken. Leer = alle, dann
     faellt das Feld ganz weg und der Lauf verhaelt sich wie bisher. */
  var kEl = document.getElementById('lf-pop-kams');
  if (kEl) {
    var kams = Array.prototype.filter.call(kEl.options, function (o) { return o.selected; })
                    .map(function (o) { return o.value; });
    if (kams.length) body.kameras = kams;
  }
  if (tag) body.tag = tag; else body.events = n;
  fetch('/lernlauf_start', {method: 'POST', body: JSON.stringify(body)})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      document.getElementById('lf-pop-status').textContent =
        d.msg || (d.ok ? TT('js.status.ok', 'ok') : TT('js.status.fehler', 'error'));
      if (d.ok) setTimeout(function () { location.href = '/lernlauf'; }, 500);
      else btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

function ankerVerwerfen(aid, btn) {
  /* Dismiss mit Gedaechtnis: Zeile+Zentroid bleiben (Wiederernten erben
     still), Crops werden geloescht — Bestaetigung via data-frage. */
  var frage = btn.getAttribute('data-frage');
  if (frage && !confirm(frage)) return;
  btn.disabled = true;
  fetch('/lernlauf/verwerfen', {method: 'POST',
                                body: JSON.stringify({anker_id: aid})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) location.reload();
      else { alert(d.msg || TT('js.status.fehler', 'error')); btn.disabled = false; }
    })
    .catch(function () { btn.disabled = false; });
}

function laufLoeschen(lid, btn) {
  /* Lauf KOMPLETT loeschen (kein Papierkorb): alle Cluster des Laufs + Ordner
     endgueltig weg; bereits uebernommene Referenzen bleiben (Kopien in faces/). */
  var frage = btn.getAttribute('data-frage');
  if (frage && !confirm(frage)) return;
  btn.disabled = true;
  fetch('/lernlauf/lauf_loeschen', {method: 'POST',
                                    body: JSON.stringify({lauf_id: lid})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) location.reload();
      else { alert(d.msg || TT('js.status.fehler', 'error')); btn.disabled = false; }
    })
    .catch(function () { btn.disabled = false; });
}

function alteLaeufeLoeschen(btn) {
  /* Sammel-Loeschung: ALLE alten Laeufe mit EINEM OK, der neueste bleibt.
     Auswahl rechnet der Server (nie eine Client-Liste loeschen). */
  var frage = btn.getAttribute('data-frage');
  if (frage && !confirm(frage)) return;
  btn.disabled = true;
  fetch('/lernlauf/alte_loeschen', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) location.reload();
      else { alert(d.msg || TT('js.status.fehler', 'error')); btn.disabled = false; }
    })
    .catch(function () { btn.disabled = false; });
}

function lernlaufAbbruch(btn) {
  if (!confirm(TT('js.lernlauf.abbruch_frage', 'Abort this learning run?'))) return;
  btn.disabled = true;
  fetch('/lernlauf_abbruch', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function () { location.href = '/lernlauf'; })
    .catch(function () { btn.disabled = false; });
}

function notifSpeichern() {
  var s = document.getElementById('notif-status');
  if (!confirm(TT('js.notif.frage', 'Save notification settings and restart the service?'))) return;
  s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/benachrichtigung_speichern', {method: 'POST', body: JSON.stringify(_notifFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) { s.textContent = r.msg; if (r.ok) _neustartDann('/benachrichtigungen', s); })
    .catch(function () { _neustartDann('/benachrichtigungen', s); });
}

function testKanal(kanal, btn) {
  var st = document.getElementById('test-' + kanal);
  btn.disabled = true; st.textContent = TT('js.status.senden', 'sending …');
  fetch('/test_' + kanal, {method: 'POST', body: JSON.stringify(_notifFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) { st.textContent = r.msg; btn.disabled = false; })
    .catch(function (e) { st.textContent = TT('js.status.fehler', 'error'); btn.disabled = false; });
}

function frigateWrite(readonly) {
  var txt = readonly ? TT('js.frigate.ro_frage', 'Switch to READ-ONLY? suslik will stop writing to Frigate.')
                     : TT('js.frigate.rw_frage', 'Enable WRITING to Frigate (sub_labels + reference sync)?');
  if (!confirm(txt)) return;
  var st = document.getElementById('fw-status');
  st.textContent = TT('js.status.speichern', 'saving …');
  fetch('/konfig', {method: 'POST', body: JSON.stringify({frigate_read_only: readonly})})
    .then(function (r) { return r.json(); })
    .then(function (d) { st.textContent = d.msg || (d.ok ? TT('js.status.gespeichert', 'saved') : TT('js.status.fehler', 'error')); if (d.ok) setTimeout(function () { location.reload(); }, 800); })
    .catch(function () {});
}

/* .340: Angebot aus dem Nachhol-Banner — EIN Schalter ueber den bestehenden
   /konfig-Weg (Muster frigateWrite). config_schreiben startet den Dienst dabei
   neu, deshalb dieselbe Warteschleife wie beim Konfigblatt; der laufende
   Nachhol-Lauf bricht damit ab, was hier genau der Zweck ist. */
function startNachholAus() {
  if (!confirm(TT('js.catchup.frage', 'Skip catching up on missed events at startup from now on? The service restarts to apply this.'))) return;
  fetch('/konfig', {method: 'POST', body: JSON.stringify({start_catchup: 'off'})})
    .then(function (r) { return r.json(); })
    .then(function (d) { if (d.ok) { _neustartDann('/heute', null); } else { alert(d.msg || TT('js.status.fehler', 'error')); } })
    .catch(function () { _neustartDann('/heute', null); });
}

function configRestore(input) {
  var f = input.files && input.files[0];
  if (!f) return;
  if (!confirm(TT('js.restore.frage', 'Restore configuration from "{name}"? This overwrites the current settings and restarts the service.', {name: f.name}))) { input.value = ''; return; }
  var st = document.getElementById('restore-status');
  st.textContent = TT('js.status.wiederherstellen', 'restoring …');
  var rd = new FileReader();
  rd.onload = function () {
    fetch('/config_wiederherstellen', {method: 'POST', body: rd.result})
      .then(function (r) { return r.json(); })
      .then(function (d) { st.textContent = d.msg; if (d.ok) _neustartDann('/system', st); })
      .catch(function () { _neustartDann('/system', st); });
  };
  rd.readAsText(f);
  input.value = '';
}

/* PE6 Full-Restore: Archiv als roher Body (kein multipart — der Server liest
   stueckweise nach Content-Length), Datei kann einige 100 MB gross sein. */
function vollRestore(input) {
  var f = input.files && input.files[0];
  if (!f) return;
  if (!confirm(TT('js.vollrestore.frage', 'Restore the FULL backup "{name}"? This replaces settings, references and all learned material, then restarts the service.', {name: f.name}))) { input.value = ''; return; }
  var st = document.getElementById('vollrestore-status');
  st.textContent = TT('js.vollrestore.laeuft', 'uploading + restoring … (large files take a while)');
  fetch('/backup_voll_wiederherstellen', {method: 'POST', body: f})
    .then(function (r) { return r.json(); })
    .then(function (d) { st.textContent = d.msg; if (d.ok) _neustartDann('/system', st); })
    .catch(function () { _neustartDann('/system', st); });
  input.value = '';
}

/* Enrollment (AP4): decide on a suggestion / add a stranger as a person / upload */
function enroll(id, aktion, person, el) {
  fetch('/enroll', {method: 'POST',
                    body: JSON.stringify({id: id, aktion: aktion, person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) {
        var card = el.closest('.card');
        if (card) card.style.opacity = 0.35;
      } else {
        alert(TT('js.enroll.fehler', 'Error: {msg}', {msg: d.msg}));
      }
    });
}
function enrollFremd(id, el) {
  var sel = document.getElementById('sel-' + id),
      neu = document.getElementById('neu-' + id),
      person = (neu && neu.value.trim()) || (sel && sel.value) || '';
  if (!person) { alert(TT('js.enroll.person_fehlt', 'Choose a person or enter a new one.')); return; }
  enroll(id, 'aufnehmen', person, el);
}
function uploadRef() {
  var neu = document.getElementById('up-neu'),
      p = (neu && neu.value.trim()) || document.getElementById('up-person').value,
      f = document.getElementById('up-datei').files[0],
      s = document.getElementById('up-status');
  if (!p || !f) { alert(TT('js.upload.fehlt', 'Choose a person (dropdown or new) and a file.')); return; }
  s.textContent = TT('js.status.hochladen', 'uploading …');
  var senden = function (personWert) {
    fetch('/upload?person=' + encodeURIComponent(personWert), {method: 'POST', body: f})
      .then(function (r) { return r.json(); })
      .then(function (d) {
        /* ACHTUNG Anzeige==Kennung (§8-Nachtrag): das 'GATE'-Praefix ist ein
           SERVER-Protokollwort im msg-Text — bleibt englisch, bis die
           JSON-msg-Felder (Stufe 2) Kennung und Anzeige trennen. */
        if (!d.ok && d.msg && d.msg.indexOf('GATE') === 0 &&
            confirm(TT('js.upload.trotzdem', '{msg}\n\nAdd anyway?', {msg: d.msg}))) {
          senden(personWert + '!');
          return;
        }
        s.textContent = d.msg;
      });
  };
  senden(p);
}

/* Cluster (19.07.): group as new person (name via prompt) or existing (dropdown) */
function anlernSenden(ids, person, btn) {
  if (!confirm(TT('js.anlernen.frage', 'Add group as "{person}" (best images become references)?', {person: person}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.lernen', 'learning …');
  fetch('/anlernen_benennen', {method: 'POST', body: JSON.stringify({ids: ids, person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      var c = btn.closest('.card');
      if (d.ok && c) { c.style.opacity = 0.45; } else { btn.disabled = false; }
    })
    .catch(function () { btn.textContent = TT('js.status.fehler_gross', 'Error'); btn.disabled = false; });
}
function anlernNeu(ids, btn) {
  var person = (window.prompt(TT('js.anlernen.name_frage', 'Name of the new person:')) || '').trim();
  if (person) anlernSenden(ids, person, btn);
}
function anlernZu(ids, selId, btn) {
  var person = document.getElementById(selId).value;
  if (!person) { alert(TT('js.anlernen.person_fehlt', 'Please choose an existing person.')); return; }
  anlernSenden(ids, person, btn);
}
/* reverse path: add ticked matching faces to an existing person */
function aehnlicheHinzu(person, btn) {
  var cbs = document.querySelectorAll('.ae-cb:checked'), ids = [];
  for (var i = 0; i < cbs.length; i++) ids.push(cbs[i].value);
  if (!ids.length) { alert(TT('js.auswahl.gesicht_fehlt', 'Please tick at least one face.')); return; }
  anlernSenden(ids.join(','), person, btn);
}
/* Library search: take ticked suggestions from recognized events / search again */
function vorschlaegeAlleEmpfohlen(person, btn) {   // Auto-Uebernehmen: alle empfohlenen auf einmal (User 22.07.)
  var cbs = document.querySelectorAll('.vs-cb-rec'), items = [];
  for (var i = 0; i < cbs.length; i++) {
    var v = cbs[i].value.split('|');
    items.push({eid: v[0], datei: v.slice(1).join('|')});
  }
  if (!items.length) { alert(TT('js.vorschlag.keine', 'No recommended faces.')); return; }
  if (!confirm(TT('js.vorschlag.alle_frage',
                  'Add all {n} recommended face(s) to {person}? They become references immediately.',
                  {n: items.length, person: person}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.hinzufuegen', 'adding …');
  fetch('/vorschlag_aufnehmen', {method: 'POST', body: JSON.stringify({person: person, items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}

function vorschlagAufnehmen(person, btn) {
  var cbs = document.querySelectorAll('.vs-cb:checked'), items = [];
  for (var i = 0; i < cbs.length; i++) {
    var v = cbs[i].value.split('|');
    items.push({eid: v[0], datei: v.slice(1).join('|')});
  }
  if (!items.length) { alert(TT('js.auswahl.gesicht_fehlt', 'Please tick at least one face.')); return; }
  if (!confirm(TT('js.vorschlag.frage', 'Add {n} face(s) to {person}?',
                  {n: items.length, person: person}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.hinzufuegen', 'adding …');
  fetch('/vorschlag_aufnehmen', {method: 'POST', body: JSON.stringify({person: person, items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}
function vorratAufnehmen(person, btn) {   // Vorrats-Angebote (bauplan_vorrat B4): eigener
  // Draht mit data-Attributen — der eid|datei-Wert des Bestands-Wegs kann den
  // Lauf-Pfad nicht transportieren (Konzept-QS W1.13).
  var cbs = document.querySelectorAll('.vo-cb:checked'), items = [];
  for (var i = 0; i < cbs.length; i++) {
    items.push({lauf_id: cbs[i].dataset.lauf, datei: cbs[i].dataset.datei,
                eid: cbs[i].dataset.eid});
  }
  if (!items.length) { alert(TT('js.auswahl.gesicht_fehlt', 'Please tick at least one face.')); return; }
  if (!confirm(TT('js.vorrat.frage', 'Add {n} stock face(s) to {person}? They become references immediately (kept local, not exported).',
                  {n: items.length, person: person}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.hinzufuegen', 'adding …');
  fetch('/vorrat_aufnehmen', {method: 'POST', body: JSON.stringify({person: person, items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}
function vorschlagNeu(person, btn) {
  btn.disabled = true; btn.textContent = TT('js.status.suchen', 'searching …');
  fetch('/vorschlaege_neu', {method: 'POST', body: JSON.stringify({person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      setTimeout(function () { location.reload(); }, 4000);
    });
}
/* Maintenance (collect + check) manually */
function anlernWartungJetzt(btn) {
  btn.disabled = true; btn.textContent = TT('js.status.laeuft', 'running …');
  fetch('/anlern_wartung_jetzt', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) { btn.textContent = d.msg; });
}
/* Reference sync Master <-> Frigate (System page) */
function syncAktion(modus, btn) {
  /* 'Master → Frigate': beides Eigennamen (Produktnamen-Regel §8.6) —
     die Richtungsangabe bleibt in jeder Sprache identisch. */
  var txt = modus === 'export' ? 'Master → Frigate' : 'Frigate → Master';
  if (!confirm(TT('js.sync.frage', 'Synchronize: {richtung}?', {richtung: txt}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.starten', 'starting …');
  fetch('/sync_' + modus, {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { btn.textContent = d.msg; return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (s.phase === 'loading') {
            btn.textContent = TT('js.sync.modell_laedt', 'loading model …');
          } else if (s.phase === 'import' || s.phase === 'export') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            btn.textContent = TT('js.sync.fortschritt', '{done}/{total} faces ({current}) {pct}%',
                                 {done: s.done, total: s.total, current: s.current || '', pct: pct});
          } else if (s.phase === 'done') {
            clearInterval(poll);
            btn.textContent = TT('js.sync.fertig', 'done: {ok} ok, {gate} skipped — reloading …',
                                 {ok: s.ok || 0, gate: s.gate || 0});
            setTimeout(function () { location.reload(); }, 2000);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            /* .131: Ursache/Hinweis zeigen, nicht nur 'rc=1' (carlsmith-Fall:
               Frigate-Erkennung aus -> Schalt-Hinweis direkt am Knopf). */
            btn.textContent = TT('js.sync.fehler', 'sync failed: {grund}',
                                 {grund: s.hinweis || s.detail || s.msg || TT('js.status.siehe_log', 'see service log')});
          }
        }).catch(function () {});
      }, 1500);
    });
}

/* .133 "Review & sync" (/sync_auswahl): selective export — tick what goes to Frigate,
   remember what should never go, then transfer and show Frigate's verdict per image.
   Person/file never travel through a JS string: they sit in data-attributes. */
function syncAuswahlZaehlen() {
  var cbs = document.querySelectorAll('.sa-cb'), n = 0, i;
  for (i = 0; i < cbs.length; i++) { if (cbs[i].checked) n++; }
  var z = document.getElementById('sa-gewaehlt');
  if (z) z.textContent = n;
  var b = document.getElementById('sa-start');
  if (b && !b.disabled) {
    b.textContent = n ? TT('js.syncauswahl.knopf', 'Transfer {n} selected to Frigate', {n: n})
                      : TT('js.syncauswahl.nichts', 'Nothing selected');
    /* .138: ein frueherer Fehlschlag hat den Knopf rot gefaerbt (scheitern());
       wer die Auswahl aendert, bekommt wieder einen normalen Start-Knopf —
       vorher stand ein Start-Text im Fehler-Rot (Panel-Hinweis: die Umkehrung
       des gerade behobenen 'Fehler im gruenen Knopf'-Problems). */
    b.className = 'gtb on';
  }
  return n;
}
function syncAuswahlAlle(an) {
  var cbs = document.querySelectorAll('.sa-cb'), i;
  for (i = 0; i < cbs.length; i++) { cbs[i].checked = !!an; }
  syncAuswahlZaehlen();
}
/* weg=1: deselect and remember · weg=0: put it back on the candidate list */
function syncAbwahl(btn, weg) {
  var d = {}, paar = [[btn.dataset.person, btn.dataset.datei]];
  d[weg ? 'abwahl' : 'zurueck'] = paar;
  /* .137: der Ruecksetz-Text kommt aus data-label — derselbe Knopf heisst auf der
     Entscheidungs-Kachel 'respect the deletion', nicht 'skip'. */
  var zurueck = btn.dataset.label || (weg ? TT('js.syncauswahl.skip', 'skip')
                                          : TT('js.syncauswahl.restore', 'restore'));
  btn.disabled = true; btn.textContent = weg ? TT('js.status.ueberspringen', 'skipping …')
                                             : TT('js.status.wiederherstellen', 'restoring …');
  fetch('/sync_abwahl', {method: 'POST', body: JSON.stringify(d)})
    .then(function (r) { return r.json(); })
    .then(function (dd) {
      /* .134: ok:false auswerten — eine fehlgeschlagene Abwahl sah vorher wie
         eine erfolgreiche aus (Seite lud einfach neu). */
      if (dd && dd.ok) { location.reload(); return; }
      alert((dd && dd.msg) || TT('js.status.fehler', 'error'));
      btn.disabled = false; btn.textContent = zurueck;
    })
    .catch(function () { btn.disabled = false; btn.textContent = zurueck; });
}
/* .137 'offer again': ein in Frigate geloeschtes oder frueher exportiertes Bild
   wieder zum normalen Kandidaten machen (POST /sync_wieder_anbieten). */
function syncWiederAnbieten(btn) {
  var zurueck = btn.dataset.label || TT('js.syncauswahl.wieder', 'offer again');
  btn.disabled = true; btn.textContent = TT('js.syncauswahl.zurueck_laeuft', 'putting it back …');
  fetch('/sync_wieder_anbieten', {method: 'POST',
        body: JSON.stringify({bilder: [[btn.dataset.person, btn.dataset.datei]]})})
    .then(function (r) { return r.json(); })
    .then(function (dd) {
      if (dd && dd.ok) { location.reload(); return; }
      alert((dd && dd.msg) || TT('js.status.fehler', 'error'));
      btn.disabled = false; btn.textContent = zurueck;
    })
    .catch(function () { btn.disabled = false; btn.textContent = zurueck; });
}
function syncAuswahlStart(btn) {
  var cbs = document.querySelectorAll('.sa-cb'), sel = [], i;
  for (i = 0; i < cbs.length; i++) {
    if (cbs[i].checked) sel.push([cbs[i].dataset.person, cbs[i].dataset.datei]);
  }
  var st = document.getElementById('sa-status');
  if (!sel.length) { if (st) st.textContent = TT('js.syncauswahl.nichts_klein', 'nothing selected'); return; }
  if (!confirm(TT('js.syncauswahl.frage', 'Send {n} reference image(s) to Frigate?', {n: sel.length}))) return;
  /* .137: Fehlertexte gehoeren NICHT in den gruenen Startknopf (Operator-Fund
     06.08.: ein gruener Knopf mit Fehlermeldung darin liest sich wie Erfolg).
     Der Knopf wird neutral-rot beschriftet, der Text steht daneben — mit dem
     Diagnose-Anker, Muster gesImport. */
  function scheitern(txt) {
    btn.className = 'gtb sa-crit'; btn.textContent = TT('js.syncauswahl.fehl_knopf', 'transfer failed');
    btn.disabled = false;
    if (!st) return;
    st.className = 'sa-crit'; st.textContent = txt + ' ';
    var dg = document.createElement('a');
    dg.href = '/sync_diagnose'; dg.target = '_blank'; dg.textContent = TT('js.status.diagnose', 'diagnosis');
    st.appendChild(dg);
  }
  btn.disabled = true; btn.textContent = TT('js.status.starten', 'starting …');
  fetch('/sync_auswahl_start', {method: 'POST', body: JSON.stringify({auswahl: sel})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { scheitern(d.msg || 'error'); return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (s.phase === 'export') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            btn.textContent = TT('js.syncauswahl.fortschritt', '{done}/{total} ({current}) {pct}%',
                                 {done: s.done, total: s.total, current: s.current || '', pct: pct});
          } else if (s.phase === 'done') {
            clearInterval(poll);
            btn.textContent = TT('js.syncauswahl.fertig', 'done: {ok} uploaded, {gate} not accepted — reloading …',
                                 {ok: s.ok || 0, gate: s.gate || 0});
            setTimeout(function () { location.reload(); }, 1500);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            /* Ursache/Hinweis zeigen, nicht 'rc=1' (carlsmith-Fall .131) */
            scheitern(TT('js.syncauswahl.fehler', 'transfer failed: {grund}',
                         {grund: s.hinweis || s.detail || s.msg || TT('js.status.siehe_log', 'see service log')}));
          }
        }).catch(function () {});
      }, 1200);
    });
}
/* Pre-check runs in the background (own subprocess): poll, then reload once */
function syncVorpruefungPoll() {
  var el = document.getElementById('sa-pruef');
  if (!el) return;
  var stillstand = 0, letzterStand = -1;
  var poll = setInterval(function () {
    fetch('/sync_vorpruefung_status').then(function (r) { return r.json(); }).then(function (s) {
      if (s.laeuft) {
        /* .134: haengt der Lauf (Prozess hart gestorben, Status bleibt auf
           laeuft), nicht ewig 'checking' zeigen — nach ~6 min ohne Fortschritt
           ehrlich aufgeben statt endlos zu pollen. */
        if ((s.fertig || 0) === letzterStand) { stillstand++; } else { stillstand = 0; letzterStand = s.fertig || 0; }
        if (stillstand > 240) {
          clearInterval(poll);
          el.textContent = TT('js.vorpruef.haengt', 'pre-check appears stuck — reload the page to retry');
          return;
        }
        el.textContent = TT('js.vorpruef.laeuft', 'checking images … {fertig}/{gesamt}',
                            {fertig: s.fertig || 0, gesamt: s.gesamt || 0});
      } else {
        clearInterval(poll);
        if (s.fehler) { el.textContent = TT('js.vorpruef.fehler', 'pre-check failed: {grund}', {grund: s.fehler}); return; }
        el.textContent = TT('js.vorpruef.fertig', 'pre-check done — reloading …');
        setTimeout(function () { location.reload(); }, 800);
      }
    }).catch(function () {});
  }, 1500);
}

/* Setup wizard step 4: import faces from Frigate with live progress */
function wizImport(btn) {
  var url = (document.getElementById('setup-url') || {}).value || '';
  var st = document.getElementById('wiz-import-status');
  btn.disabled = true; btn.textContent = TT('js.status.starten', 'starting …');
  fetch('/sync_import', {method: 'POST', body: JSON.stringify({url: url})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { if (st) st.textContent = d.msg || TT('js.status.fehler', 'error'); btn.disabled = false; return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (!st) return;
          if (s.phase === 'import') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            st.textContent = TT('js.import.fortschritt', 'downloading {done}/{total} ({current}) {pct}%',
                                {done: s.done, total: s.total, current: s.current || '', pct: pct});
          } else if (s.phase === 'done') {
            clearInterval(poll);
            st.textContent = TT('js.import.fertig_wiz', '✓ imported {n} — computing features on the accelerator …', {n: s.ok || 0});
            btn.textContent = TT('js.import.knopf_fertig', 'Imported ✓');
          } else if (s.phase === 'error') {
            /* Der Server meldet Fehler sauber (phase:'error'), aber diese Schleife wertete nur
               import/done aus — bei einem Fehler pollte sie endlos, der Text fror ein und der
               Knopf blieb tot (Plan-QS P.9). Die Zwillingsfunktion oben macht es laengst so. */
            clearInterval(poll);
            st.textContent = TT('js.import.fehler', 'import failed: {grund}',
                                {grund: s.hinweis || s.detail || s.msg || TT('js.status.siehe_log', 'see service log')}) + ' ';
            var dg1 = document.createElement('a');
            dg1.href = '/sync_diagnose'; dg1.target = '_blank'; dg1.textContent = TT('js.status.diagnose', 'diagnosis');
            st.appendChild(dg1);
            btn.disabled = false; btn.textContent = TT('js.import.knopf', 'Import faces');
          }
        }).catch(function () {});
      }, 1000);
    });
}

/* Known page: import faces from Frigate outside the wizard (Task #22 — after a config
   restore the wizard is skipped and the import was unreachable). Same route as wizImport;
   empty url => server falls back to the configured frigate_url. */
function gesImport(btn) {
  var st = document.getElementById('ges-import-status');
  btn.disabled = true; btn.textContent = TT('js.status.starten', 'starting …');
  fetch('/sync_import', {method: 'POST', body: JSON.stringify({})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { if (st) st.textContent = d.msg || TT('js.status.fehler', 'error'); btn.disabled = false; btn.textContent = TT('js.import.knopf_ges', 'Import faces from Frigate'); return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (!st) return;
          if (s.phase === 'import') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            st.textContent = TT('js.import.fortschritt', 'downloading {done}/{total} ({current}) {pct}%',
                                {done: s.done, total: s.total, current: s.current || '', pct: pct});
          } else if (s.phase === 'done') {
            clearInterval(poll);
            st.textContent = TT('js.import.fertig_ges', '✓ imported {n} — computing features, page reloads …', {n: s.ok || 0});
            setTimeout(function () { location.reload(); }, 2500);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            st.textContent = TT('js.import.fehler', 'import failed: {grund}',
                                {grund: s.hinweis || s.detail || s.msg || TT('js.status.siehe_log', 'see service log')}) + ' ';
            var dg2 = document.createElement('a');
            dg2.href = '/sync_diagnose'; dg2.target = '_blank'; dg2.textContent = TT('js.status.diagnose', 'diagnosis');
            st.appendChild(dg2);
            btn.disabled = false; btn.textContent = TT('js.import.knopf_ges', 'Import faces from Frigate');
          }
        }).catch(function () {});
      }, 1000);
    });
}

/* Check (19.07.): remove a single reference image / recompute reference QC */
function refEntfernen(person, datei, btn) {
  if (!confirm(TT('js.ref.frage', 'Remove reference image of {person}?', {person: person}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.entfernen', 'removing …');
  fetch('/ref_entfernen', {method: 'POST', body: JSON.stringify({person: person, datei: datei})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      var c = btn.closest('.card');
      if (d.ok && c) { c.style.opacity = 0.4; }
    });
}
function ladeBalken(el, i, n, z) {
  /* .311 (User 21.08., Lernlauf-Karte 'Gruppe 2 von 3': 'hier koennte man auch
     so einen kleinen Balken bauen'): schmaler Fortschrittsbalken + Zaehler
     hinter einem Warte-Text — fuer Antworten mit laden + i/n/zustand
     (refcache-Neuaufbau, Pass-Ernte). Haengt sich an das Element an; der
     Aufrufer setzt vorher den Text (textContent loescht alte Balken mit).
     Das Auftritte-Blatt malt seit .345 stattdessen den grossen
     Fortschritts-Block (lbBlock, inline und eigenstaendig); hier bleibt der
     schmale Balken, gleiche Form wie der Bestands-QS-Balken (#qs-lauf-balken). */
  if (!el) return;
  var w = document.createElement('span');
  w.style.cssText = 'display:inline-block;vertical-align:middle;width:110px;height:6px;' +
    'margin-left:8px;border-radius:3px;background:var(--surface-2);' +
    'border:1px solid var(--border);overflow:hidden';
  var f = document.createElement('span');
  var pz = n ? Math.round(100 * i / n) : 0;
  f.style.cssText = 'display:block;height:100%;width:' + pz + '%;' +
    'background:' + (z === 'wartet' ? 'var(--warn)' : 'seagreen') + ';transition:width .6s';
  w.appendChild(f); el.appendChild(w);
  if (n) {
    var c = document.createElement('span');
    c.className = 'dim'; c.style.marginLeft = '6px';
    c.textContent = i + '/' + n;
    el.appendChild(c);
  }
}
function qsFortschritt() {
  /* .310 Bestands-QS-Fortschritt ohne Seiten-Reload (Lernlauf-Muster):
     pollt /qualitaet/status alle 3 s, fuehrt Balken + Zaehler nach und laedt
     GENAU EINMAL neu, wenn der Lauf fertig ist — nur auf der Uebersicht
     (data-reload=1); die Galerie mit Haken bekommt stattdessen den Hinweis. */
  var box = document.getElementById('qs-lauf');
  if (!box) return;
  fetch('/qualitaet/status').then(function (r) { return r.json(); }).then(function (d) {
    var b = document.getElementById('qs-lauf-balken'), tx = document.getElementById('qs-lauf-text');
    if (d.laeuft) {
      var pz = d.n ? Math.round(100 * d.i / d.n) : 0;
      if (b) b.style.width = pz + '%';
      if (tx) tx.textContent = '\u23F3 ' + (d.n ? TT('js.qs.fortschritt', 'checking picture {i} of {n} …', {i: d.i, n: d.n})
                                                 : TT('js.status.starten', 'starting …'));
      setTimeout(qsFortschritt, 3000);
    } else {
      if (b) b.style.width = '100%';
      if (box.getAttribute('data-reload') === '1') { location.reload(); return; }
      /* Galerie mit Haken/Reitern: NIE selbst neu laden (.282) — nur sagen, dass es fertig ist */
      if (tx) tx.textContent = '\u2705 ' + (box.getAttribute('data-fertig') || '');
    }
  }).catch(function () { setTimeout(qsFortschritt, 5000); });
}
document.addEventListener('DOMContentLoaded', function () { if (document.getElementById('qs-lauf')) qsFortschritt(); });

function qsStart(btn) {
  /* .273 Bestands-QS-Popup (Faces-Karte): Start mit Personen-Wahl; laeuft
     ueber denselben Hintergrund-Runner wie der automatische Re-Check. */
  btn.disabled = true;
  var z = document.getElementById('qs-ziel');
  var person = (z && !z.disabled) ? z.value : '';
  fetch('/qualitaet/start', {method: 'POST',
                             body: JSON.stringify({person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var s = document.getElementById('qs-status');
      if (!d.ok) { if (s) s.textContent = d.msg || TT('js.status.fehler', 'error'); btn.disabled = false; return; }
      location.href = '/qualitaet' + (d.person ? '?person=' + encodeURIComponent(d.person) : '');
    })
    .catch(function () {
      /* .282: NIE still scheitern — Klicks waehrend eines Dienst-Neustarts
         (Deploy) liefen sonst ins Leere und der Knopf wirkte tot. */
      var s = document.getElementById('qs-status');
      if (s) s.textContent = TT('js.dienst.nicht_erreichbar', 'cannot reach the service — try again in a moment.');
      btn.disabled = false;
    });
}

function cacheAufraeumen(btn) {
  /* .313 (Issue #25): Aufraeum-Knopf der System-Seite — raeumt Clip-Cache nach Alter,
     Deckel und Mindestfrei und zeigt, was frei wurde. */
  btn.disabled = true;
  var m = document.getElementById('disk-msg'); if (m) m.textContent = TT('js.status.pruefen', 'checking …');
  fetch('/cache_aufraeumen', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (m) m.textContent = d.msg || TT('js.status.fehler', 'error');
      btn.disabled = false;
      if (d.ok) setTimeout(function () { location.reload(); }, 2500);
    })
    .catch(function () {
      if (m) m.textContent = TT('js.dienst.nicht_erreichbar', 'cannot reach the service — try again in a moment.');
      btn.disabled = false;
    });
}
function qsPerson(name, btn) {
  /* .273c: Kontext-Start von der Personen-Seite — Lauf ist immer global,
     die Ergebnis-Sicht springt gefiltert auf die Person. */
  btn.disabled = true; btn.textContent = TT('js.status.pruefen', 'checking …');
  fetch('/qualitaet/start', {method: 'POST',
                             body: JSON.stringify({person: name})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { btn.textContent = d.msg || TT('js.status.fehler', 'error'); btn.disabled = false; return; }
      location.href = '/qualitaet?person=' + encodeURIComponent(name);
    })
    .catch(function () { btn.disabled = false; });
}

function refPruefNeu(btn) {
  btn.disabled = true; btn.textContent = TT('js.status.pruefen', 'checking …');
  fetch('/ref_pruef_neu', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) { btn.textContent = d.msg; });
}
/* Quality/suitability: tick all checkboxes of a reason group */
function usAlle(cls) {
  var cbs = document.querySelectorAll('.' + cls);
  for (var i = 0; i < cbs.length; i++) cbs[i].checked = true;
}
/* Quality/suitability: delete ticked images in a batch */
function refBatchLoeschen(btn) {
  var cbs = document.querySelectorAll('.us-cb:checked'), items = [];
  for (var i = 0; i < cbs.length; i++) {
    var v = cbs[i].value.split('|');
    items.push({person: v[0], datei: v.slice(1).join('|')});
  }
  if (!items.length) { alert(TT('js.auswahl.bild_fehlt', 'Please select at least one image.')); return; }
  if (!confirm(TT('js.ref.batch_frage', 'Delete {n} image(s)?', {n: items.length}))) return;
  btn.disabled = true; btn.textContent = TT('js.status.loeschen', 'deleting …');
  fetch('/ref_entfernen_batch', {method: 'POST', body: JSON.stringify({items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}

function gtSenden(leiste, personen, fertig) {
  /* .313 GT als MENGE: POST {eid, personen:[...]}; der Dienst prueft, speichert
     (label wird dort abgeleitet) und antwortet mit der gueltigen Menge. Die Menge
     wird SOFORT im Datensatz fortgeschrieben (zwei schnelle Klicks rechnen sonst
     auf demselben alten Stand), gemalt wird nur die JUENGSTE Antwort (Folgezaehler);
     eine Ablehnung des Dienstes wird an der Leiste gezeigt, nie verschluckt. */
  var folge = (parseInt(leiste.dataset.folge || '0', 10) + 1);
  leiste.dataset.folge = folge;
  var vorher = leiste.dataset.personen;
  leiste.dataset.personen = JSON.stringify(personen);
  var msg = leiste.querySelector('.gt-msg');
  if (msg) msg.textContent = '';
  fetch('/gt', {method: 'POST', body: JSON.stringify({eid: leiste.dataset.eid, personen: personen})})
    .then(function (r) { return r.json().catch(function () { return {ok: false, msg: 'HTTP ' + r.status}; }); })
    .then(function (d) {
      if (parseInt(leiste.dataset.folge || '0', 10) !== folge) return;   /* aelter als der letzte Klick */
      if (!d || !d.ok) {
        leiste.dataset.personen = vorher;
        if (msg) msg.textContent = (d && d.msg) ? d.msg : TT('js.status.fehler', 'error');
        gtMalen(leiste, JSON.parse(vorher || '[]'));
        return;
      }
      gtMalen(leiste, d.personen || []);
      var card = leiste.closest('.card');
      if (card && card.dataset.fadeOnLabel) { card.style.opacity = 0.35; }
      if (fertig) fertig(d);
    })
    .catch(function () {
      if (parseInt(leiste.dataset.folge || '0', 10) !== folge) return;
      leiste.dataset.personen = vorher;
      if (msg) msg.textContent = TT('js.dienst.nicht_erreichbar', 'cannot reach the service — try again in a moment.');
      gtMalen(leiste, JSON.parse(vorher || '[]'));
    });
}
function gtMalen(leiste, personen) {
  leiste.dataset.personen = JSON.stringify(personen);
  var bs = leiste.querySelectorAll('button[data-gt]');
  for (var i = 0; i < bs.length; i++) {
    bs[i].className = personen.indexOf(bs[i].dataset.gt) >= 0 ? 'gtb on' : 'gtb';
  }
  /* Uebernehmen-Knopf nur, solange nichts gewaehlt ist */
  var alle = leiste.querySelector('button[data-gt-alle]');
  if (alle) alle.style.display = personen.length ? 'none' : '';
  /* gewaehlte Person aus dem Dropdown bekommt ihren eigenen Schalter in dieser Zeile */
  for (var j = 0; j < personen.length; j++) {
    if (!leiste.querySelector('button[data-gt="' + CSS.escape(personen[j]) + '"]')) {
      var b = document.createElement('button');
      b.className = 'gtb on'; b.dataset.gt = personen[j]; b.textContent = personen[j];
      b.onclick = function () { gtT(this); };
      var anker = leiste.querySelector('button[data-gt="Fremd"]');
      leiste.insertBefore(b, anker || null);
    }
  }
  var sel = leiste.querySelector('select');
  if (sel) {
    sel.value = '';
    for (var k = 0; k < sel.options.length; k++) {
      var weg = sel.options[k].value && personen.indexOf(sel.options[k].value) >= 0;
      sel.options[k].hidden = weg; sel.options[k].disabled = weg;
    }
  }
}
function gtT(el, wert) {
  /* Schalter: an/aus. '?' und 'No person' sind exklusiv (leeren die Menge);
     sie wieder auszuschalten entfernt das Urteil (= '?' im Dienst).
     el = Knopf (Wert aus data-gt) oder Select (Wert als 2. Argument). */
  var leiste = el.closest('.gtl'); if (!leiste) return;
  wert = (wert === undefined) ? el.dataset.gt : wert;
  if (!wert) return;
  var cur = []; try { cur = JSON.parse(leiste.dataset.personen || '[]'); } catch (e) {}
  var exklusiv = (wert === 'unklar' || wert === 'kein_mensch');
  var neu;
  if (cur.indexOf(wert) >= 0) { neu = cur.filter(function (x) { return x !== wert; }); }
  else if (exklusiv) { neu = [wert]; }
  else { neu = cur.filter(function (x) { return x !== 'unklar' && x !== 'kein_mensch'; }); neu.push(wert); }
  gtSenden(leiste, neu);
}
function gtAlle(el) {
  var leiste = el.closest('.gtl'); if (!leiste) return;
  var alle = []; try { alle = JSON.parse(el.dataset.gtAlle || '[]'); } catch (e) {}
  gtSenden(leiste, alle);
}
function gt(eid, label, el) {
  /* Altaufrufer (ein Wert = Menge mit einem Element) */
  gtT(el, label);
}

/* Unknown tab (20.07.): assign to person / ignore / merge / re-run */
function unbReconcile(btn) {
  /* Verlaufs-Timer (requirement: progress must stay visible while a long job runs)
     — Sekunden + Phase aus /reconcile_status, bis der POST zurueck ist. */
  btn.disabled = true;
  var start = Date.now();
  var tick = setInterval(function () {
    var s = Math.round((Date.now() - start) / 1000);
    /* Uhr-Stub-Muster (§8-Nachtrag): der Zaehler-Rahmen ist ein Schluessel,
       die Phase kommt (noch englisch) vom Server. */
    fetch('/reconcile_status').then(function (r) { return r.json(); }).then(function (d) {
      btn.textContent = TT('js.unb.tick', '{phase} … {s} s',
                           {phase: (d.phase && d.phase !== '-' ? d.phase : TT('js.status.laeuft_wort', 'running')), s: s});
    }).catch(function () { btn.textContent = TT('js.unb.tick', '{phase} … {s} s', {phase: TT('js.status.laeuft_wort', 'running'), s: s}); });
  }, 1000);
  btn.textContent = TT('js.unb.tick', '{phase} … {s} s', {phase: TT('js.status.laeuft_wort', 'running'), s: 0});
  fetch('/unbekannt_reconcile', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      clearInterval(tick);
      btn.textContent = d.msg;
      setTimeout(function () { location.reload(); }, 1200);
    })
    .catch(function () { clearInterval(tick); btn.textContent = TT('js.status.fehler', 'error'); btn.disabled = false; });
}
/* .380 Unknown-Seite ohne Reload: die Aktions-Antworten tragen die betroffene
   Kachel fertig gerendert mit (kachel: {uid: html}) bzw. sagen, dass sie aus der
   Sicht faellt (weg: [uid]) — dazu den Stand des Fortschrittsankers. Frueher lud
   JEDE Aktion die ganze Seite neu; bei 95 Gruppen hiess das nach jeder Zuweisung
   alle Gruppen und alle Crops noch einmal. Die Texte mit Zahl kommen als Rahmen
   mit {…}-Platzhalter aus data-txt (Server-Schluessel), hier wird nur die Zahl
   eingesetzt. */
function unbTxt(el, kw) {
  var r = el && el.getAttribute('data-txt'); if (!r) return '';
  Object.keys(kw).forEach(function (k) { r = r.split('{' + k + '}').join(String(kw[k])); });
  return r;
}
function unbListe() { return document.getElementById('ukliste'); }
function unbZustand() {
  var l = unbListe();
  return {sort: (l && l.dataset.sort) || '', f: (l && l.dataset.filter) || ''};
}
function unbAnwenden(d) {
  if (d.kachel) {
    Object.keys(d.kachel).forEach(function (u) {
      var alt = document.getElementById('uk-' + u);
      if (alt) { alt.outerHTML = d.kachel[u]; }
    });
  }
  (d.weg || []).forEach(function (u) {
    var alt = document.getElementById('uk-' + u);
    if (alt) alt.parentNode.removeChild(alt);
  });
  var a = document.getElementById('uk-anker');
  if (a && typeof d.offen === 'number') {
    a.textContent = unbTxt(a, {offen: d.offen, gesamt: d.gesamt});
  }
  unbSel();
}
function unbSenden(pfad, daten, btn, dann) {
  var z = unbZustand();
  daten.sort = z.sort; daten.f = z.f;
  if (btn) btn.disabled = true;
  return fetch(pfad, {method: 'POST', headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify(daten)})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (dann) dann(d);
      unbAnwenden(d);
      return d;
    })
    .catch(function () {
      if (btn) { btn.disabled = false; btn.textContent = TT('js.status.fehler', 'error'); }
    });
}
function unbMeldung(uid, text) {
  var c = document.getElementById('uk-' + uid), m = c && c.querySelector('.uk-msg');
  if (m) m.textContent = text || '';
}
function unbBesucher(uid, an, btn) {
  if (an && !confirm(TT('js.unb.besucher_frage', 'Ignore as a known stranger? It will no longer trigger alerts. (Re-activate any time under "known visitors" below.)'))) return;
  unbSenden('/unbekannt_besucher', {uid: uid, an: an}, btn, function (d) {
    if (!d.ok && btn) { btn.disabled = false; btn.textContent = d.msg; }
    else unbMeldung(uid, d.msg);
  });
}
function unbObjekt(uid, an, btn) {
  if (an && !confirm(TT('js.unb.objekt_frage', 'Mark as "no person" (a bush, a reflection, a parked car)? It stops showing up as a visitor; you can undo this under "not people".'))) return;
  unbSenden('/unbekannt_objekt', {uid: uid, an: an}, btn, function (d) {
    if (!d.ok && btn) { btn.disabled = false; btn.textContent = d.msg; }
    else unbMeldung(uid, d.msg);
  });
}
/* Gruppen-Auswahl fuer das n:1-Zusammenlegen (ersetzt die Merge-Auswahllisten
   je Kachel: die trugen bei 95 Gruppen 9056 <option>-Elemente). */
function unbGewaehlt() {
  return Array.prototype.map.call(
    document.querySelectorAll('.uk-sel:checked'), function (c) { return c.value; });
}
function unbSel() {
  var b = document.getElementById('uk-bulk'); if (!b) return;
  var n = unbGewaehlt().length;
  b.hidden = n < 2;
  b.disabled = false;
  b.textContent = unbTxt(b, {n: n});
}
function unbBulkMerge(btn) {
  var uids = unbGewaehlt();
  if (uids.length < 2) return;
  if (!confirm(TT('js.unb.merge_frage', 'Merge?'))) return;
  unbSenden('/unbekannt_merge_viele', {uids: uids}, btn, function (d) {
    var m = document.getElementById('uk-bulk-msg');
    if (m) m.textContent = d.msg;
  });
}
/* Teil-Zuweisung (B4): Haken am Crop-Streifen. Ohne Haken bleibt es beim
   Zuweisen der ganzen Gruppe; mit Haken gehen NUR die angetickten Bilder an die
   Person, alle anderen bleiben im Pool (eine Gruppe ist nicht immer eine
   Person). */
function unbHaken(uid) {
  var c = document.getElementById('uk-' + uid);
  return c ? Array.prototype.map.call(c.querySelectorAll('.uk-m:checked'),
                                      function (x) { return x.value; }) : [];
}
function unbTick(el) {
  var c = el.closest('.uk'); if (!c) return;
  var uid = c.dataset.uid, b = document.getElementById('teil-' + uid);
  if (!b) return;
  var n = unbHaken(uid).length;
  b.hidden = n < 1;
  b.textContent = unbTxt(b, {n: n});
}
function unbBenennenSenden(uid, btn, ids) {
  var nm = document.getElementById('nm-' + uid), p = nm && nm.value.trim();
  if (!p) { alert(TT('js.unb.name_fehlt', 'Enter a name (new or existing person).')); return; }
  var frage = ids
    ? TT('js.unb.teil_frage', 'Assign the {n} ticked pictures to "{person}"? The rest of the group stays under Unknown.', {n: ids.length, person: p})
    : TT('js.unb.benennen_frage', 'Assign to "{person}"? The best images become references.', {person: p});
  if (!confirm(frage)) return;
  btn.textContent = TT('js.status.lernen', 'learning …');
  var daten = {uid: uid, person: p};
  if (ids) daten.ids = ids;
  unbSenden('/unbekannt_benennen', daten, btn, function (d) {
    if (d.ok) unbMeldung(uid, d.msg);
    else { btn.disabled = false; btn.textContent = d.msg; }
  });
}
function unbBenennen(uid, btn) { unbBenennenSenden(uid, btn, null); }
function unbTeil(uid, btn) {
  var ids = unbHaken(uid);
  if (!ids.length) return;
  unbBenennenSenden(uid, btn, ids);
}
/* Nachladen (B1): der Server liefert die naechsten Kacheln als HTML-Stueck; die
   Seite haengt sie an, statt beim Aufbau alles auf einmal zu bauen. */
function unbMehr(btn) {
  var l = unbListe(); if (!l) return;
  var z = unbZustand();
  btn.disabled = true;
  btn.textContent = TT('js.status.laeuft_wort', 'running');
  fetch('/unbekannt_seite', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({sort: z.sort, f: z.f, offset: parseInt(btn.dataset.offset, 10) || 0})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      l.insertAdjacentHTML('beforeend', d.html || '');
      btn.dataset.offset = d.offset;
      if (d.rest > 0) {
        btn.textContent = unbTxt(btn, {n: d.n_naechste});
        btn.disabled = false;
      } else {
        btn.parentNode.removeChild(btn);
      }
    })
    .catch(function () { btn.disabled = false; btn.textContent = TT('js.status.fehler', 'error'); });
}

/* Cameras sheet (Phase 2b, 21.07.): collect per-camera use + zones, save, restart */
function kamerasSpeichern(btn) {
  var kameras = {}, i,
      vs = document.querySelectorAll('.kam-verw'),
      zs = document.querySelectorAll('.kam-zone:checked');
  for (i = 0; i < vs.length; i++) {
    kameras[vs[i].dataset.cam] = {verwenden: vs[i].checked, zonen: []};
  }
  for (i = 0; i < zs.length; i++) {
    if (kameras[zs[i].dataset.cam]) kameras[zs[i].dataset.cam].zonen.push(zs[i].value);
  }
  var s = document.getElementById('kam-status');
  btn.disabled = true; if (s) s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/kameras_speichern', {method: 'POST', body: JSON.stringify({kameras: kameras})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (s) s.textContent = d.msg;
      if (d.ok) _neustartDann(location.href, s);
      else btn.disabled = false;
    })
    .catch(function () { _neustartDann(location.href, s); });
}

function setupTest() {                                  // Setup-Wizard: Frigate mit eingegebener URL testen (Reload)
  var u = (document.getElementById('setup-url') || {}).value || '';
  location.href = '/setup?url=' + encodeURIComponent(u.trim());
}

function setupSpeichern(btn) {                          // Setup-Wizard committen (URL + Backend + Kameras/Zonen)
  var kameras = {}, i,
      vs = document.querySelectorAll('.kam-verw'),
      zs = document.querySelectorAll('.kam-zone:checked');
  for (i = 0; i < vs.length; i++) {
    kameras[vs[i].dataset.cam] = {verwenden: vs[i].checked, zonen: []};
  }
  for (i = 0; i < zs.length; i++) {
    if (kameras[zs[i].dataset.cam]) kameras[zs[i].dataset.cam].zonen.push(zs[i].value);
  }
  var url = ((document.getElementById('setup-url') || {}).value || '').trim(),
      bk = document.querySelector('input[name="setup-backend"]:checked'),
      body = {frigate_url: url, backend: bk ? bk.value : ''};
  var wr = document.querySelector('input[name="setup-write"]:checked');
  if (wr) body.frigate_read_only = (wr.value === 'ro');
  if (Object.keys(kameras).length) body.kameras = kameras;
  var s = document.getElementById('setup-status');
  btn.disabled = true; if (s) s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/setup_speichern', {method: 'POST', body: JSON.stringify(body)})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (s) s.textContent = d.msg;
      if (d.ok) { _neustartDann('/heute', s); }
      else btn.disabled = false;
    })
    .catch(function () { _neustartDann('/heute', s); });
}

/* Theme toggle (20.07.): light/dark, choice in localStorage (default dark) */
(function () {
  var b = document.getElementById('theme-toggle');
  if (!b) return;
  b.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('vd-theme', next); } catch (e) {}
  });
})();

/* ── Zuweisen direkt an der Today-Karte (User-Entscheid 25.07. abends) ─────────────────
   Klappe zeigt die Gesichter der Unbekannt-Identitaet; der Nutzer WAEHLT einzeln, was
   wirklich zur Person gehoert (Schutz gegen das Greedy-Seed-Clustering, #57: Identitaeten
   koennen gemischt sein oder Nicht-Gesichter enthalten). Uebernahme laeuft ueber den
   BESTEHENDEN Weg /anlernen_benennen — gleiche Mechanik wie die Vorschlags-Seite. */
/* .234: ukKlappe/ukZuweisen entfernt — die Today-Klappe wich dem
   konsistenten Karten-Link aufs Besucher-Profil (/unbekannte#uk-...). */

/* ── Ganze Person loeschen (requirement: deleting a person removes the NAME, not just one image) ──────
   Serverseitig reversibel (wandert nach <data>/trash/). Doppelte Bestaetigung mit
   getipptem Namen: das ist die einzige Aktion, die eine komplette Referenzbibliothek
   einer Person auf einmal entfernt — ein Fehlklick darf dafuer nicht reichen. */
function personLoeschen(person, btn) {
  var tipp = prompt(TT('js.person.loesch_frage',
                       'Delete ALL references and the name "{person}"?\n' +
                       'The images move to the trash folder (recoverable).\n\n' +
                       'Type the name to confirm:', {person: person}));
  if (tipp === null) return;
  if (tipp.trim() !== person) { alert(TT('js.person.name_falsch', 'Name did not match — nothing deleted.')); return; }
  btn.disabled = true; btn.textContent = TT('js.status.entfernen', 'removing …');
  fetch('/person_loeschen', {method: 'POST', body: JSON.stringify({person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.href = '/gesichter'; }, 1500);
      else btn.disabled = false;
    })
    .catch(function () { btn.textContent = TT('js.status.fehler', 'error'); btn.disabled = false; });
}

/* ── Hochzaehlen bei laufender Suche (requirement: show elapsed time while searching) ────────
   Der Zaehler ueberlebt die Auto-Refreshes der Seite (Startzeit je Person in
   sessionStorage) und pollt alle 3 s, ob das Ergebnis da ist — dann laedt die Seite
   sofort neu statt aufs naechste 15/20-s-Fenster zu warten. Ehrlich: gezaehlt wird die
   VERGANGENE Zeit; eine Restzeit-Prognose waere geraten. */
(function () {
  var spans = document.querySelectorAll('.such-zaehler');
  if (!spans.length) {                       /* Suche fertig -> Startzeit vergessen */
    try { Object.keys(sessionStorage).forEach(function (k) {
      if (k.indexOf('such-start-') === 0) sessionStorage.removeItem(k);
    }); } catch (e) {}
    return;
  }
  var person = spans[0].getAttribute('data-person') || '';
  var key = 'such-start-' + person;
  var start = parseInt(sessionStorage.getItem(key) || '0', 10);
  if (!start) { start = Date.now(); sessionStorage.setItem(key, String(start)); }
  function tick() {
    var s = Math.round((Date.now() - start) / 1000);
    for (var i = 0; i < spans.length; i++) spans[i].textContent = TT('js.einheit.klammer_s', '({n} s)', {n: s});
  }
  tick();
  setInterval(tick, 1000);
  setInterval(function () {
    fetch('/aehnliche_status?person=' + encodeURIComponent(person))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.fertig) { sessionStorage.removeItem(key); location.reload(); }
      }).catch(function () {});
  }, 3000);
})();

/* ── Areas Stufe 1 v2 (Partitions-Modell): eine Kamera = eine Area, per Dropdown, Speichern OHNE
   Dienst-Neustart (kein _neustartDann — /areas_speichern aktualisiert die laufende
   Instanz direkt, ein laufender Lernlauf bleibt unangetastet). Gesammelt wird als
   PAAR-LISTE + Object.fromEntries: ein rohes Objekt-Literal wuerde bei Namen wie
   '__proto__' keine eigene Eigenschaft anlegen (Widerleger .91, stiller Verlust). */
function _areasSammeln() {
  var paare = [], i, pills = document.querySelectorAll('.ar-pill'),
      wahlen = document.querySelectorAll('.ar-wahl');
  for (i = 0; i < pills.length; i++) paare.push([pills[i].dataset.area, []]);
  function eintrag(n) {
    for (var j = 0; j < paare.length; j++) if (paare[j][0] === n) return paare[j];
    return null;
  }
  for (i = 0; i < wahlen.length; i++) {
    var n = wahlen[i].value, e = n && eintrag(n);
    if (e) e[1].push(wahlen[i].dataset.cam);           /* leer = Default (nicht gespeichert) */
  }
  return paare;
}
function _areasPaareObjekt(paare) {
  return Object.fromEntries(paare.map(function (p) { return [p[0], {cameras: p[1]}]; }));
}
function areasSpeichern(btn, paare) {
  paare = paare || _areasSammeln();
  var s = document.getElementById('ar-status');
  if (btn) btn.disabled = true;
  if (s) s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/areas_speichern', {method: 'POST',
    body: JSON.stringify({areas: _areasPaareObjekt(paare)})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (s) s.textContent = d.msg;
      if (d.ok) location.reload();
      else if (btn) btn.disabled = false;
    })
    .catch(function () {
      if (s) s.textContent = TT('js.areas.fehl', 'save failed — is the service reachable?');
      if (btn) btn.disabled = false;
    });
}
function areaAnlegen(btn) {
  var f = document.getElementById('ar-neu'), n = (f && f.value || '').trim();
  if (!n) { alert(TT('js.areas.name_fehlt', 'Enter an area name first.')); return; }
  var paare = _areasSammeln(), i;
  for (i = 0; i < paare.length; i++) {
    if (paare[i][0].toLowerCase() === n.toLowerCase()) { alert(TT('js.areas.existiert', 'This area already exists.')); return; }
  }
  paare.push([n, []]);
  areasSpeichern(btn, paare);
}
function areaEntfernen(btn) {
  var p = btn.closest('.ar-pill'), n = p && p.dataset.area;
  if (!n) return;
  /* "Default" ist zugleich Kennung der Standard-Area (Anzeige==Kennung,
     §8.2) — im Satz bleibt das Wort deshalb in jeder Sprache "Default". */
  if (!confirm(TT('js.areas.entfernen_frage', 'Remove area "{name}"? Its cameras return to Default — nothing else changes.', {name: n}))) return;
  areasSpeichern(btn, _areasSammeln().filter(function (q) { return q[0] !== n; }));
}

// PE1 B4 (stufe2.md): Person-Learn-Lauf starten (Wizard /personlauf).
async function personlaufStart(n, btn) {
  var sel = document.getElementById('pl-person');
  var person = sel ? sel.value : '';
  btn.disabled = true;
  var st = document.getElementById('pl-status');
  try {
    var r = await fetch('/personlauf_start', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: n, person: person })
    });
    var d = await r.json();
    if (r.ok && d.ok) { location.href = '/personlauf'; return; }
    if (st) st.textContent = TT('js.status.fehler_detail', 'error: {msg}', {msg: d.msg || r.status});
  } catch (e) {
    if (st) st.textContent = TT('js.status.fehler_detail', 'error: {msg}', {msg: e});
  }
  btn.disabled = false;
}

// PE1: laufenden Person-Learn-Lauf abbrechen (Geerntetes bleibt).
async function personlaufAbbruch(btn) {
  if (!confirm(TT('js.personlauf.abbruch_frage', 'Abort this person-learn run? Harvested images are kept.'))) return;
  btn.disabled = true;
  try {
    var r = await fetch('/personlauf_abbruch', { method: 'POST' });
    if (r.ok) { location.reload(); return; }
  } catch (e) { /* Reload zeigt den echten Zustand */ }
  btn.disabled = false;
}

// PE2b: kompletten Lauf verwerfen (schlechtes Ergebnis), Wizard wird frei.
async function personlaufVerwerfen(lid) {
  if (!confirm(TT('js.personlauf.verwerfen_frage', 'Discard run {lid} completely? All its images are deleted; a new run can re-harvest any time.', {lid: lid}))) return;
  var r = await fetch('/personlauf/loeschen', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lauf_id: lid })
  });
  if (r.ok) location.reload();
}

/* .133: die Review-&-sync-Seite braucht beim Laden zwei Dinge — den Zaehler auf den
   echten Haken-Stand und, falls die Vorpruefung noch rechnet, den Fortschritts-Poll.
   app.js laeuft mit defer, das DOM steht hier also schon. */
if (document.querySelector('.sa-cb')) syncAuswahlZaehlen();
if (document.getElementById('sa-pruef')) syncVorpruefungPoll();

/* --- Vision detect (konzept_vision.md v2 §4, Zug V1) -------------------------
   Drei Knoepfe, dieselben Muster wie die Notifications-Seite: Felder mit der
   Vorsilbe "vis-" sind der Vision-Block (Secret leer lassen = behalten), Felder
   mit "cfgv-" sind die zwei Whitelist-Zahlen und gehen ueber /konfig. Der
   Test-Knopf kann Minuten dauern (lokale CPU-Inferenz) — deshalb ohne Timeout
   im Browser und mit sichtbarem Laufzustand statt eines stillen Spinners. */
function _visionFelder() {
  var d = {}, felder = document.querySelectorAll('[id^="vis-"]');
  for (var i = 0; i < felder.length; i++) {
    var f = felder[i];
    d[f.id.slice(4)] = (f.type === 'checkbox') ? (f.checked ? 'true' : 'false') : f.value;
  }
  return d;
}

/* --- Ungespeicherte Aenderungen (User-Fund 08.08. abend) --------------------
   Woertlich: "Save wird leider vergessen, zu klein, zu unscheinbar." Real
   passiert: mehrfach konfiguriert, getestet, nie gespeichert — die Erkennung
   lief die ganze Zeit gegen die ALTE Verbindung, weil der Test die getippten
   Werte benutzt und das Speichern die gespeicherten. Genau diese Verwechslung
   spricht der Dialog unten an.
   EIN Zustand, ZWEI Anzeigen (oben an der Ueberschrift, unten an der klebenden
   Leiste) — hier wird beides aus derselben Stelle geschaltet. */
var VIS_DIRTY = {block: false, zahlen: false};
var VIS_NAV_OK = false;

function _visionDirtyZeigen() {
  var an = VIS_DIRTY.block || VIS_DIRTY.zahlen;
  var bar = document.getElementById('vision-savebar');
  var u = document.getElementById('vision-dirty');
  var o = document.getElementById('vision-dirty-oben');
  if (bar) bar.classList.toggle('dirty', an);
  if (u) u.hidden = !an;
  if (o) o.hidden = !an;
}

function _visionDirtySetzen(was) {
  if (was) {
    VIS_DIRTY[was] = true;
    /* Beim Dirty-Werden den alten Statustext raeumen (#22-Nebenbefund): sonst
       steht "saved — …" vom letzten Speichern direkt neben "unsaved changes"
       und die Leiste widerspricht sich selbst. */
    var s = document.getElementById('vision-status');
    if (s) s.textContent = '';
  } else {
    VIS_DIRTY = {block: false, zahlen: false};
  }
  _visionDirtyZeigen();
}

function _visionDirtyVerdrahten() {
  if (!document.getElementById('vision-savebar')) return;
  var f = document.querySelectorAll('[id^="vis-"], [id^="cfgv-"]');
  for (var i = 0; i < f.length; i++) {
    (function (el) {
      var was = el.id.indexOf('cfgv-') === 0 ? 'zahlen' : 'block';
      /* input deckt Tippen ab, change die Checkboxen und die Auswahlfelder.
         Ein LEER gelassenes Key-Feld loest nichts aus — leer heisst weiterhin
         "behalte den gespeicherten Wert", das ist keine Aenderung. */
      el.addEventListener('input', function () { _visionDirtySetzen(was); });
      el.addEventListener('change', function () { _visionDirtySetzen(was); });
    })(f[i]);
  }
  window.addEventListener('beforeunload', function (e) {
    if (!(VIS_DIRTY.block || VIS_DIRTY.zahlen) || VIS_NAV_OK) return;
    e.preventDefault();
    e.returnValue = '';
    return '';
  });
}

/* Drei-Wege-Frage. confirm() kann nur ja/nein, hier braucht es drei Wege —
   also ein winziger eigener Dialog im bestehenden Farbsystem. */
function _visionFrage(titel, text, wahlen) {
  var h = document.createElement('div');
  h.className = 'vs-modal';
  var box = document.createElement('div');
  box.className = 'vs-box';
  var t = document.createElement('h4');
  t.textContent = titel;
  var p = document.createElement('p');
  p.textContent = text;
  var w = document.createElement('div');
  w.className = 'vs-w';
  box.appendChild(t); box.appendChild(p); box.appendChild(w);
  h.appendChild(box);
  wahlen.forEach(function (wahl, i) {
    var b = document.createElement('button');
    b.className = 'gtb' + (i === 0 ? ' on' : '');
    b.textContent = wahl[0];
    b.onclick = function () { h.remove(); wahl[1](); };
    w.appendChild(b);
  });
  document.body.appendChild(h);
}

/* Der zweite Save (/konfig) loest den geplanten Dienst-Neustart aus. Reisst der
   die Verbindung ab, BEVOR die Antwort ankommt, landete man frueher im .catch
   und der User las "error" — obwohl alles gespeichert war (real passiert
   08.08.: 19:01:58 gespeichert, 19:02:10 Neustart, Store korrekt, Anzeige
   "error"). Deshalb: nach erfolgreichem /vision/konfig ist ein Abbruch der
   WAHRSCHEINLICHE Neustart, nicht ein Fehler — wir steigen in dasselbe
   Warte-und-neu-laden ein wie beim normalen Speichern. Nur wenn schon der
   ERSTE Aufruf scheitert, ist wirklich nichts gespeichert. */
function visionSpeichern(danach) {
  var s = document.getElementById('vision-status');
  s.textContent = TT('js.status.speichern', 'saving …');
  var zahlen = {}, zf = document.querySelectorAll('[id^="cfgv-"]');
  /* Checkboxen (die zwei optionalen Meldungen) tragen ihren Zustand in
     .checked, nicht in .value — .value waere immer "on". */
  for (var i = 0; i < zf.length; i++) {
    zahlen[zf[i].id.slice(5)] = (zf[i].type === 'checkbox')
      ? (zf[i].checked ? 'true' : 'false') : zf[i].value;
  }
  /* REIHENFOLGE (Beweis v4b): erst /vision/konfig — die Verbindung selbst —,
     danach erst alles Weitere. Der Zahlen-Save laeuft nur, wenn wirklich eine
     Zahl angefasst wurde: er startet den Dienst neu, und ein Neustart macht
     jeden angehaengten Test unmoeglich. */
  var zahlenDirty = VIS_DIRTY.zahlen;
  fetch('/vision/konfig', {method: 'POST', body: JSON.stringify(_visionFelder())})
    .then(function (r) { return r.json(); })
    .catch(function () { return {ok: false, msg: TT('js.vision.nicht_erreichbar', 'could not reach the service — nothing was saved')}; })
    .then(function (r) {
      if (!r.ok) { s.textContent = r.msg; return; }
      VIS_DIRTY.block = false;
      _visionDirtyZeigen();
      if (!zahlenDirty) {
        s.textContent = TT('js.vision.gespeichert', 'saved — recognition uses this connection from now on');
        _visionDirtySetzen(null);
        if (danach) danach();
        return;
      }
      return fetch('/konfig', {method: 'POST', body: JSON.stringify(zahlen)})
        .then(function (r2) { return r2.json(); })
        .then(function (r2) {
          s.textContent = r2.ok ? TT('js.vision.gespeichert_neustart', 'saved — the service restarts in a moment') : r2.msg;
          if (r2.ok) { _visionDirtySetzen(null); VIS_NAV_OK = true; _neustartDann('/vision', s); }
        })
        .catch(function () {
          s.textContent = TT('js.vision.gespeichert_reload', 'saved — the service is restarting, this page reloads in a moment');
          _visionDirtySetzen(null);
          VIS_NAV_OK = true;
          _neustartDann('/vision', s);
        });
    });
}

/* Der Test laeuft seit .158 STUFE FUER STUFE (User: "ich will sehen, welche
   Stufe laeuft, und am Ende ein Testlog"). Der Browser ruft 1, dann 2, dann 3;
   jede Antwort traegt das strukturierte Stufen-Ergebnis, das sofort in die
   Log-Zeile geschrieben wird. Bricht eine Stufe rot ab, bleiben die folgenden
   als "not run" stehen. Kein Polling, kein Server-Zustand. */
function _visionStufeText(s) {
  var w = [];
  if (s.dauer_s != null) w.push(TT('js.einheit.s', '{n} s', {n: s.dauer_s}));
  if (s.treffer != null) w.push(TT('js.vision.treffer', '{n}/2 right', {n: s.treffer}));
  if (s.ist != null) w.push(TT('js.vision.tokens', '{ist} tokens vs {soll}', {ist: s.ist, soll: s.soll}));
  return (s.text || '') + (w.length ? ' · ' + w.join(' · ') : '');
}

function visionTest(btn) {
  if (VIS_DIRTY.block || VIS_DIRTY.zahlen) {
    /* Der Irrtum, den der User beschrieben hat: nach einem gruenen Test hielt
       er die Sache fuer erledigt — dabei hatte er nie gespeichert. */
    _visionFrage(
      TT('js.vision.dirty_titel', 'You have not saved this connection'),
      TT('js.vision.dirty_text',
         'The test would use the values you just typed. Recognition keeps using ' +
         'the SAVED connection until you press "Save connection" — a green test ' +
         'alone changes nothing about the verdicts.'),
      [[TT('js.vision.dirty_save', 'Save first, then test'), function () { visionSpeichern(function () { _visionTestLauf(btn); }); }],
       [TT('js.vision.dirty_test', 'Test without saving'), function () { _visionTestLauf(btn); }],
       [TT('js.allg.abbrechen', 'Cancel'), function () { btn.disabled = false; }]]);
    return;
  }
  _visionTestLauf(btn);
}

function _visionTestLauf(btn) {
  var st = document.getElementById('vision-test-status');
  var namen = [TT('js.vision.stufe1', 'reachability and model'),
               TT('js.vision.stufe2', 'forced-choice shape grids'),
               TT('js.vision.stufe3', 'token count')];
  btn.disabled = true;
  var felder = _visionFelder();
  function stufe(nr) {
    st.textContent = TT('js.vision.stufe_laeuft', 'step {nr}/3 — {name} … (a local model on CPU can take minutes)',
                        {nr: nr, name: namen[nr - 1]});
    var z = document.getElementById('vs-log-' + nr);
    if (z) z.textContent = TT('js.status.laeuft', 'running …');
    felder.stufe = nr;
    return fetch('/vision/test', {method: 'POST', body: JSON.stringify(felder)})
      .then(function (r) { return r.json(); })
      .then(function (r) {
        var s = r.msg && r.msg.stufe;
        if (!s) { st.textContent = (r.msg && r.msg.msg) || r.msg || TT('js.vision.test_fehl', 'the test could not be run'); btn.disabled = false; return; }
        if (z) z.textContent = _visionStufeText(s);
        if (!r.msg.weiter) {
          st.textContent = TT('js.vision.stufe_stop', 'stopped at step {nr} — see the log below', {nr: nr});
          location.reload();
          return;
        }
        if (nr < 3) return stufe(nr + 1);
        st.textContent = TT('js.vision.fertig', 'done — {ampel}', {ampel: r.msg.ampel.toUpperCase()});
        location.reload();
      })
      .catch(function () {
        st.textContent = TT('js.vision.stufe_fehl', 'step {nr} could not be run', {nr: nr});
        btn.disabled = false;
      });
  }
  stufe(1);
}

function visionSchalter(an) {
  var st = document.getElementById('vision-schalter-status');
  st.textContent = TT('js.status.speichern', 'saving …');
  fetch('/vision/schalter', {method: 'POST', body: JSON.stringify({aktiv: an})})
    .then(function (r) { return r.json(); })
    .then(function (r) { st.textContent = r.msg || ''; if (r.ok) location.reload(); })
    .catch(function () {
      /* Der Schalter selbst startet den Dienst nicht neu — aber ein
         gleichzeitiger Neustart (z.B. vom Speichern nebenan) kappt trotzdem
         die Verbindung. Auch hier: warten und neu laden statt "error". */
      st.textContent = TT('js.vision.neustart_warte', 'the service is not answering right now — this page reloads in a moment');
      _neustartDann('/vision', st);
    });
}

/* Zuruecksetzen schreibt den DEFAULT-WORTLAUT ins Feld (nicht leer): das Feld
   zeigt immer, was das System wirklich fragt. Gespeichert wird erst mit Save —
   und dort rechnet der Server den Default wieder auf "kein eigener Prompt"
   zurueck, damit die Marke "custom prompt" ehrlich bleibt. */
function visionPromptZurueck() {
  var t = document.getElementById('vis-prompt');
  if (!t) return;
  if (!confirm(TT('js.vision.prompt_frage', 'Reset the question to the default wording?'))) return;
  t.value = (typeof VIS_PROMPT_STD === 'string') ? VIS_PROMPT_STD : '';
  document.getElementById('vision-status').textContent =
    TT('js.vision.prompt_zurueck', 'default wording restored — press "Save connection" to store it');
}

/* --- Recognition test (konzept_vision.md v2 §4, Zug V4) ----------------------
   Der Lauf faehrt den ECHTEN Urteilspfad und dauert je nach Backend Sekunden
   bis Minuten; die Seite laedt sich waehrenddessen selbst nach (refresh). */
function rtVision(btn) {
  var st = document.getElementById('rt-vision-status');
  btn.disabled = true;
  st.textContent = TT('js.rt.start', 'starting the vision run …');
  /* .164: die zwei Felder gelten NUR fuer diesen Lauf — sie fahren mit der
     Anfrage mit und werden nirgends gespeichert. Fehlen sie (Seite ohne
     Felder), entscheidet der Server mit den Config-Werten. */
  var zf = document.getElementById('rt-zellen');
  var vf = document.getElementById('rt-voten');
  var df = document.getElementById('rt-doppel');
  fetch('/vision/urteil', {method: 'POST', body: JSON.stringify(
    {pass_key: RT_PASS,
     zellen: zf ? zf.value : null,
     voten: vf ? vf.value : null,
     /* Checkbox: .checked, nicht .value — .value waere immer "on". */
     doppellauf: df ? (df.checked ? 'true' : 'false') : null})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) setTimeout(function () { location.reload(); }, 4000);
      else btn.disabled = false;
    })
    .catch(function () { st.textContent = TT('js.rt.fehl', 'the run could not be started'); btn.disabled = false; });
}

/* .161: den Durchgang noch einmal analysieren, wenn der Sammel-Modus AN ist und
   trotzdem kein Material da ist. Der Knopf steht nur in genau diesem Fall auf
   der Seite; hier wird er nur ausgeloest. */
function rtNachanalyse(btn) {
  var st = document.getElementById('rt-nach-status');
  btn.disabled = true;
  st.textContent = TT('js.status.starten', 'starting …');
  fetch('/vision/nachanalyse', {method: 'POST', body: JSON.stringify({pass_key: RT_PASS})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) setTimeout(function () { location.reload(); }, 3000);
      else btn.disabled = false;
    })
    .catch(function () { st.textContent = TT('js.rt.nach_fehl', 'it could not be started'); btn.disabled = false; });
}

/* --- Vision detect V2: Kacheln, Key-Sofortpruefung, Modellwahl ---------------
   Die Kachel wird NICHT beim Klick gespeichert, sondern nur angezeigt
   (?kachel=). Sonst muesste man eine externe Verbindung speichern, um
   ueberhaupt die Cloud-Bestaetigung zu sehen, die das Speichern verlangt — ein
   Ring. Gespeichert wird erst mit "Save", geprueft mit "Check the key". */
function visionKachel(name) {
  if ((VIS_DIRTY.block || VIS_DIRTY.zahlen)
      && !confirm(TT('js.vision.kachel_frage', 'You have unsaved changes. Switching provider discards them. Continue?'))) return;
  VIS_NAV_OK = true;          /* bewusster Wechsel: kein zweiter Dialog */
  location.href = '/vision?kachel=' + encodeURIComponent(name);
}

/* Nach dem Check wurde frueher stumpf neu geladen — und genau daran ist am
   08.08. ein Nutzer haengengeblieben: eine noch NICHT gespeicherte Verbindung
   (URL + Key eingetippt, sofort geprueft) war nach dem Reload wieder die
   GESPEICHERTE, die Liste passte nicht mehr dazu und wurde verworfen. Fuer den
   Nutzer sah es aus, als haette er nichts eingegeben.
   Jetzt: die Antwort TRAEGT die gefundenen Modelle, der Browser rendert sie,
   und die eingetippten Felder bleiben stehen. Die harte Entdecken-Regel bleibt
   dabei unverletzt — die Liste gehoert per Konstruktion zu genau der
   Verbindung, die im Formular steht; aendert man daran etwas, wird sie
   verworfen (siehe _visionEntdeckungVerwerfen). */
var VIS_ENTDECKT = null;

function _visionModellListe(modelle, gewaehlt) {
  var w = document.getElementById('vision-modell-wahl');
  if (!w) return;
  if (!modelle || !modelle.length) { w.innerHTML = ''; return; }
  var s = document.createElement('select');
  s.id = 'vision-modell';
  s.className = 'vs-sel';
  s.onchange = function () { visionModell(s); };
  if (!gewaehlt) {
    var leer = document.createElement('option');
    leer.value = '';
    leer.textContent = TT('js.vision.pick', '— pick one —');
    s.appendChild(leer);
  }
  for (var i = 0; i < modelle.length; i++) {
    var m = modelle[i], o = document.createElement('option');
    o.value = m.id;
    /* Die Anmerkung kommt vom SERVER (Messwerte-Registry) — hier steht keine
       Zahl und kein Modellname fest im Code. */
    o.textContent = m.id + ' — ' + ((m.badge && m.badge.text) || TT('js.vision.untested', 'untested here'));
    if (m.id === gewaehlt) o.selected = true;
    s.appendChild(o);
  }
  w.innerHTML = '';
  w.appendChild(s);
}

function _visionEntdeckungVerwerfen() {
  /* Kachel- oder Endpunkt-Wechsel nach dem Check: die eben gezeigte Liste
     gehoert dann zu einer anderen Verbindung und ist damit hinfaellig. */
  if (!VIS_ENTDECKT) return;
  VIS_ENTDECKT = null;
  _visionModellListe([], '');
  var i = document.getElementById('vision-modell-info');
  if (i) i.textContent = TT('js.vision.neu_pruefen', 'the connection changed — check it again to see which models it has');
}

function visionSchluessel(btn) {
  var st = document.getElementById('vision-key-status');
  btn.disabled = true;
  st.textContent = TT('js.vision.key_laeuft', 'asking the provider which models you can use …');
  fetch('/vision/schluessel', {method: 'POST', body: JSON.stringify(_visionFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      btn.disabled = false;
      var d = r.msg || {};
      st.textContent = d.text || d || '';
      var info = document.getElementById('vision-modell-info');
      if (!r.ok) { if (info) info.textContent = d.text || TT('js.vision.key_fehl', 'the check failed'); _visionModellListe([], ''); return; }
      VIS_ENTDECKT = {endpunkt: d.endpunkt, kachel: d.kachel};
      if (info) info.textContent = d.text || '';
      var sel = document.getElementById('vision-modell');
      _visionModellListe(d.modelle, sel ? sel.value : '');
    })
    .catch(function () { st.textContent = TT('js.vision.key_fehl2', 'the check could not be run'); btn.disabled = false; });
}

/* Eingaben, die die Verbindung veraendern, entwerten eine gezeigte Liste. */
['vis-endpunkt', 'vis-host', 'vis-port', 'vis-api_key'].forEach(function (id) {
  var f = document.getElementById(id);
  if (f) f.addEventListener('input', _visionEntdeckungVerwerfen);
});
_visionDirtyVerdrahten();

/* Modell-Dropdown: die Wahl aus der ENTDECKTEN Liste wird sofort in den
   vision-Block des Config-Stores geschrieben (Entscheid 08.08.), damit sie einen
   Neustart ueberlebt und beim naechsten Aufruf vorausgewaehlt ist. Danach
   Reload, weil die Detailzeile unter der Auswahl serverseitig aus der
   Messwerte-Registry kommt — kein zweiter Badge-Bau im Browser. */
function visionModell(sel) {
  var st = document.getElementById('vision-modell-status');
  if (!sel.value) { st.textContent = ''; return; }
  st.textContent = TT('js.status.speichern', 'saving …');
  sel.disabled = true;
  var d = _visionFelder();
  d.modell = sel.value;
  fetch('/vision/konfig', {method: 'POST', body: JSON.stringify(d)})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) { VIS_DIRTY.block = false; VIS_NAV_OK = true; location.reload(); }
      else sel.disabled = false;
    })
    .catch(function () { st.textContent = TT('js.status.fehler', 'error'); sel.disabled = false; });
}

/* --- Galerie-Wizard (konzept_vision.md v2 §6) --------------------------------
   VW_ZELLEN traegt die Lesereihenfolge (Reihe 1 links->rechts, dann Reihe 2 …);
   eine abgelehnte Zelle wird serverseitig ins Gedaechtnis geschrieben und durch
   den naechstbesten Kandidaten DERSELBEN Ansicht ersetzt. */
function vwWeg(i) {
  var z = VW_ZELLEN[i], k = document.getElementById('vwz_' + i);
  if (!z || !z.schluessel) return;
  var belegt = VW_ZELLEN.filter(function (x) { return x && x.schluessel; })
    .map(function (x) { return x.schluessel; });
  // Die Zellen DIESER Reihe fahren mit: der Kurator (.161) haelt seine
  // Vielfalts-Deckel je Reihe, und der Nachruecker soll den Tag nicht doppeln,
  // den der Nutzer gerade behalten hat.
  var reiheBelegt = VW_ZELLEN.filter(function (x) {
    return x && x.schluessel && x.reihe === z.reihe;
  }).map(function (x) { return x.schluessel; });
  k.style.opacity = '.4';
  fetch('/vision/galerie/weg', {method: 'POST', body: JSON.stringify(
    {person: VW_PERSON, schluessel: z.schluessel, reihe: z.reihe, belegt: belegt,
     reihe_belegt: reiheBelegt})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      if (!r.ok) { k.style.opacity = '1'; return; }
      var neu = r.msg && r.msg.zelle;
      if (!neu) { location.reload(); return; }
      VW_ZELLEN[i].schluessel = r.msg.schluessel;
      k.style.opacity = '1';
      k.className = 'vw-z' + (neu.geliehen_aus ? ' geliehen' : '');
      k.querySelector('img').src = '/personlauf/bild/'
        + encodeURIComponent(neu.lauf_id) + '/' + encodeURIComponent(neu.datei);
      // Die Begruendungszeile kommt FERTIG vom Server (core/visiongalerie) —
      // der Browser baut keinen zweiten Satz, sonst driften zwei Fassungen.
      var zeile = document.createElement('div');
      zeile.textContent = neu.begruendung
        || [neu.tag || '?', neu.camera || '?', (neu.hoehe || '?') + ' px'].join(' · ');
      /* Tranche D (Kennung/Anzeige-Trennung 3b): geliehen_text kommt fertig
         uebersetzt vom Server (bausteine.reihen_wort); geliehen_aus bleibt
         die interne Kennung (Logik oben) und der ehrliche Fallback. */
      k.querySelector('.vw-m').innerHTML = zeile.innerHTML
        + (neu.geliehen_aus
           ? '<div class="vw-warn">' + TT('js.vw.geliehen', 'from the {reihe} row', {reihe: neu.geliehen_text || neu.geliehen_aus}) + '</div>'
           : '');
    })
    .catch(function () { k.style.opacity = '1'; });
}

function vwVergessen() {
  if (!confirm(TT('js.vw.vergessen_frage', 'Forget the images you rejected for this gallery? They can be proposed again.'))) return;
  fetch('/vision/galerie/vergessen', {method: 'POST', body: JSON.stringify({person: VW_PERSON})})
    .then(function () { location.reload(); });
}

function vwAbnehmen(btn) {
  var st = document.getElementById('vw-status');
  var auswahl = VW_ZELLEN.map(function (z) { return z && z.schluessel ? z.schluessel : null; });
  var leer = auswahl.filter(function (s) { return !s; }).length;
  if (leer && !confirm(TT('js.vw.leer_frage', '{n} cell(s) could not be filled. Approve the gallery anyway?', {n: leer}))) return;
  btn.disabled = true;
  st.textContent = TT('js.vw.kopiert', 'copying the pictures into the gallery …');
  fetch('/vision/galerie/abnahme', {method: 'POST', body: JSON.stringify(
    {person: VW_PERSON, groesse: VW_GROESSE, auswahl: auswahl})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) location.href = '/vision/galerie?person=' + encodeURIComponent(VW_PERSON);
      else btn.disabled = false;
    })
    .catch(function () { st.textContent = TT('js.status.fehler', 'error'); btn.disabled = false; });
}

/* ---- Live watchers (Phase 2): Save / Toggle / Source test / Load measurement.
   K1-Poll: die Seite zeigt Zustaende NUR aus der Engine-Quittung (/live_status
   liest live_status.json); der Poll aktualisiert Countdown + Phase des
   laufenden Auftrags ("watchers paused for measurement") und laedt die Seite
   neu, sobald sich ein Kachel-ZUSTAND aendert (nicht bei blossen Detail-
   Texten wie "last frame Xs ago" — sonst wuerde die Seite dauer-reloaden). */
function _liveFelder() {
  var q = (document.querySelector('input[name="lv-quelle"]:checked') || {}).value || 'proxy';
  var kan = [];
  document.querySelectorAll('.lv-kanal:checked').forEach(function (c) { kan.push(c.value); });
  return {kamera: (document.getElementById('lv-kamera') || {}).value || '',
          quelle: q,
          url: (document.getElementById('lv-url') || {}).value || '',
          ende_ohne_gesicht_s: (document.getElementById('lv-ende') || {}).value,
          wieder_scharf_s: (document.getElementById('lv-scharf') || {}).value,
          kanaele: kan,
          hoehe: (document.querySelector('input[name="lv-hoehe"]:checked') || {}).value || null,
          /* Live-Umbau 31.08. — die je-Kamera-Werte der neuen Kacheln. Fehlt
             ein Feld im DOM (gesperrter Build), bleibt der Wert `undefined`,
             JSON.stringify laesst ihn weg und der Server BEHAELT den
             gespeicherten Wert (live_speichern._wert). Genau deshalb stehen
             hier keine Ersatz-Defaults: ein `|| 2` wuerde eine 3 des Nutzers
             still auf 2 zuruecksetzen, sobald das Feld einmal fehlt. */
          erkannt_n: (document.getElementById('lv-erkannt-n') || {}).value,
          erkannt_t_s: (document.getElementById('lv-erkannt-t') || {}).value,
          erkannt_fenster_s: (document.getElementById('lv-erkannt-fenster') || {}).value,
          frigate_events: (document.getElementById('lv-frigate') || {}).checked,
          frigate_abstand_s: (document.getElementById('lv-frigate-abstand') || {}).value,
          /* Live-Performance Welle 1, Etappe A: bewegungsgesteuertes Abtasten.
             Dieselbe Halte-Regel wie oben — fehlt das Feld im DOM, geht es
             nicht mit und der Server behaelt den gespeicherten Wert. */
          bewegung_gate: (document.getElementById('lv-bewegung') || {}).checked,
          ruhe_takt_s: (document.getElementById('lv-ruhe-takt') || {}).value,
          bewegung_schwelle: (document.getElementById('lv-bewegung-schwelle') || {}).value,
          bewegung_flaeche: (document.getElementById('lv-bewegung-flaeche') || {}).value};
}

/* Kalibrier-Vorrat EINER Kamera wegwerfen (User-Auftrag 31.08.: nachkalibrieren
   mit frischem Material). Mit Rueckfrage, weil der Ring danach von vorn
   anfaengt — die Bilder sind nicht wiederherstellbar. */
function liveVorratLeeren(kamera, btn) {
  /* Der Fallback ist BYTE-GLEICH zum en.py-Wert (Gate-Vertrag js.*): ein
     abweichender Fallback wuerde ohne geladene Sprachtabelle etwas anderes
     versprechen als die uebersetzte Fassung. */
  if (!confirm(TT('js.live.vorrat_leeren_frage',
                  'Delete the calibration samples of this camera? They cannot '
                  + 'be brought back; the watcher starts collecting again from '
                  + 'now on.'))) return;
  btn.disabled = true;
  fetch('/live_kalib_leeren', {method: 'POST',
                               body: JSON.stringify({kamera: kamera})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var s = document.getElementById('lk-msg') || document.getElementById('lv-status');
      if (s) s.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 800);
      else btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

/* ── Materialsuche der Kalibrier-Seite (Etappe 4 des Zentral-Umbaus 31.08.):
   Knopf startet den Mini-Ernte-Lauf ueber die letzten Person-Events DIESER
   Kamera, danach pollt die Seite den Stand. Der Knopf bleibt gesperrt, solange
   der Lauf laeuft — ein zweiter Start waere nur eine Absage (der Server laesst
   ohnehin nur einen Lauf zu). Die Bilanz bleibt am Ende STEHEN, auch wenn sie
   mager ist: "aus N Ereignissen kamen M Bilder" ist die Diagnose der Kamera.
   Die Fallbacks sind BYTE-GLEICH zu en.py (Gate-Vertrag js.*). */
function kalibFuellen(kamera, btn) {
  var z = document.getElementById('kf-' + kamera);
  btn.disabled = true;
  if (z) z.textContent = TT('js.kalib.start', 'looking for material …');
  fetch('/kalibrierung_fuellen', {method: 'POST',
                                  body: JSON.stringify({kamera: kamera})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) {
        if (z) z.textContent = d.msg || TT('js.kalib.fehler',
                                           'could not look for material');
        btn.disabled = false;
        return;
      }
      kalibFuellstand(kamera, btn);
    })
    .catch(function () {
      if (z) z.textContent = TT('js.kalib.fehler', 'could not look for material');
      btn.disabled = false;
    });
}

function kalibFuellstand(kamera, btn) {
  var z = document.getElementById('kf-' + kamera);
  fetch('/kalibrierung_fuellstand?k=' + encodeURIComponent(kamera))
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d || d.kamera === undefined) { btn.disabled = false; return; }
      if (d.laeuft) {
        if (z) z.textContent = TT('js.kalib.lauf',
                                  '{i} of {n} events · {bilder} picture(s)',
                                  {i: d.i, n: d.n, bilder: d.bilder});
        setTimeout(function () { kalibFuellstand(kamera, btn); }, 2000);
        return;
      }
      if (z) z.textContent = TT('js.kalib.fertig',
                                '{bilder} picture(s) from {events} event(s)',
                                {bilder: d.bilder, events: d.i})
                             + (d.fehler ? ' — ' + d.fehler : '');
      btn.disabled = false;
      /* Neue Bilder aendern Vorrats-Stand und Galerie — die Seite holt sie
         sich, sobald wirklich etwas dazugekommen ist. Bei leerer Ausbeute
         bleibt sie stehen, sonst waere die Bilanz nach dem Reload weg. */
      if (d.bilder > 0) setTimeout(function () { location.reload(); }, 2500);
    })
    .catch(function () { btn.disabled = false; });
}

function liveSpeichern(btn) {
  var s = document.getElementById('lv-status');
  btn.disabled = true; if (s) s.textContent = TT('js.status.speichern', 'saving …');
  fetch('/live_speichern', {method: 'POST', body: JSON.stringify(_liveFelder())})
    .then(function (r) { return r.json(); })
    .then(function (d) { if (s) s.textContent = d.msg; btn.disabled = false; })
    .catch(function () { if (s) s.textContent = TT('js.status.fehler', 'error'); btn.disabled = false; });
}

function liveSchalter(kamera, an, btn) {
  btn.disabled = true;
  fetch('/live_schalter', {method: 'POST',
                           body: JSON.stringify({kamera: kamera, enabled: an})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var s = document.getElementById('lv-status') || document.getElementById('lv-job-' + kamera);
      if (s) s.textContent = d.msg;
      btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

function liveTest(kamera, btn) {
  btn.disabled = true;
  fetch('/live_test', {method: 'POST', body: JSON.stringify({kamera: kamera})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var s = document.getElementById('lv-job-' + kamera);
      if (s) s.textContent = d.msg;
      btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

function liveMessung(kamera, btn) {
  btn.disabled = true;
  fetch('/live_messung', {method: 'POST', body: JSON.stringify({kamera: kamera})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var s = document.getElementById('lv-job-' + kamera);
      if (s) s.textContent = d.msg;
      btn.disabled = false;
    })
    .catch(function () { btn.disabled = false; });
}

function _livePoll() {
  fetch('/live_status')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      /* UI-B2: der Server liefert auftrag/auftraege NUR bei frischem
         Engine-Herzschlag (status_fuer_ui) — ein toter Auftrag kann Countdown
         und Reload-Tor hier also nicht mehr einfrieren. */
      var a = d.auftrag;
      var el = document.getElementById('lv-auftrag');
      if (el) {
        if (a) {
          /* Status-replace-Mapping (§8-Nachtrag): a.phase ist eine KENNUNG,
             das Anzeige-Wort kommt je Kennung aus einem eigenen Schluessel —
             unbekannte Kennungen zeigen sich selbst (ehrlich statt leer). */
          var ph = {verbinden: TT('js.live.phase_verbinden', 'Connecting'),
                    messen: TT('js.live.phase_messen', 'Measuring'),
                    auswerten: TT('js.live.phase_auswerten', 'Evaluating'),
                    abbruch: TT('js.live.phase_abbruch', 'Aborting')}[a.phase] || a.phase;
          var rest = (a.rest_s !== null && a.rest_s !== undefined)
            ? TT('js.live.rest', ' — {n} s left', {n: Math.ceil(a.rest_s)}) : '';
          /* UI-KANN 11: 'watchers paused' nur, wenn wirklich welche pausieren
             (Quelltests pausieren nicht; ohne Waechter pausiert niemand). */
          el.textContent = TT('js.live.auftrag_zeile', '{art} on {kamera}: {phase}{rest}{pausiert}',
            {art: (a.art === 'messung' ? TT('js.live.messung', 'Load measurement') : TT('js.live.quelltest', 'Source test')),
             kamera: a.kamera, phase: ph, rest: rest,
             pausiert: (a.pausiert && a.pausiert.length
               ? TT('js.live.pausiert', ' — watchers paused for measurement ({liste})', {liste: a.pausiert.join(', ')})
               : '')});
        } else { el.textContent = ''; }
      }
      Object.keys(d.jobs || {}).forEach(function (kam) {
        var j = d.jobs[kam];
        var jel = document.getElementById('lv-job-' + kam);
        if (!jel) return;
        if (!j.fertig)
          jel.textContent = TT('js.live.job_laeuft', 'source test running (helper process, up to ~2 minutes) …');
        else if (j.text !== undefined)
          /* UI-M3: das Helfer-ERGEBNIS anzeigen, nicht nur das Laufen. */
          jel.textContent = (j.ok ? TT('js.live.job_ok', 'source test done: {text}', {text: j.text || ''})
                                  : TT('js.live.job_fehl', 'source test FAILED: {text}', {text: j.text || ''}));
      });
      /* UI-M3: Fehl-Auftraege der Engine sichtbar machen (frisch-gegated). */
      Object.keys(d.auftraege || {}).forEach(function (kam) {
        var e = d.auftraege[kam];
        ['test', 'messung'].forEach(function (art) {
          var b = e[art];
          if (b && b.ok === false && b.fehler) {
            var jel = document.getElementById('lv-job-' + kam);
            if (jel) jel.textContent = (art === 'messung'
              ? TT('js.live.messung_fehl', 'load measurement failed: {grund}', {grund: b.fehler})
              : TT('js.live.test_fehl', 'source test failed: {grund}', {grund: b.fehler}));
          }
        });
      });
      /* Reload NUR bei echter Zustands-/Ergebnis-Aenderung (s. Kopfkommentar);
         waehrend eines laufenden Auftrags aufgeschoben (der Countdown soll
         stehen bleiben) — nachgeholt, sobald der Auftrag endet, weil _liveSnap
         den alten Stand behaelt. */
      var kern = [];
      Object.keys(d.zustaende || {}).sort().forEach(function (k) {
        kern.push(k + ':' + d.zustaende[k].z);
      });
      Object.keys(d.auftraege || {}).sort().forEach(function (k) {
        var e = d.auftraege[k];
        ['test', 'messung'].forEach(function (art) {
          if (e[art]) kern.push(k + ':' + art + ':' + e[art].ts);
        });
      });
      Object.keys(d.jobs || {}).sort().forEach(function (k) {
        kern.push(k + ':job:' + !!d.jobs[k].fertig);
      });
      kern.push('engine:' + !!(d.engine || {}).frisch);
      var schnapp = kern.join('|');
      if (window._liveSnap === undefined) { window._liveSnap = schnapp; return; }
      if (schnapp !== window._liveSnap && !a) location.reload();
    })
    .catch(function () {});
}

if (window._livePage) setInterval(_livePoll, 1000);

/* Kachel-Vorschau (User 13.08.): alle 2 s ein frisches JPEG aus dem AGENTEN
   (/live_bild liefert den verarbeiteten Waechter-Frame; ?t= als Cache-Buster).
   onerror/onload an der Kachel blenden bei 404 (Engine aus/Frische-Frist)
   ehrlich aus und bei Rueckkehr wieder ein. */
if (window._livePage) setInterval(function () {
  document.querySelectorAll('img.lv-vorschau').forEach(function (im) {
    im.src = '/live_bild/' + encodeURIComponent(im.getAttribute('data-kamera'))
      + '?t=' + Date.now();
  });
}, 2000);

/* Hide/Show je Kachel (.186, User 13.08.): reine Anzeige-Praeferenz im Store,
   danach Reload (die Kachel wandert in die Hidden-Gruppe bzw. zurueck). */
function liveVerstecken(kamera, an, btn) {
  btn.disabled = true;
  fetch('/live_verstecken', {method: 'POST',
                             body: JSON.stringify({kamera: kamera, versteckt: an})})
    .then(function (r) { return r.json(); })
    .then(function () { location.reload(); })
    .catch(function () { btn.disabled = false; });
}

/* Area-Gruppier-Schalter (.186): Wahl in localStorage, beim Seitenaufruf ohne
   Parameter einmalig angewandt (replace, keine History-Muellzeile). */
function liveAreaMerken(an) {
  try { localStorage.setItem('vd-live-area', an ? '1' : '0'); } catch (e) {}
}
if (window._livePage) (function () {
  try {
    var will = localStorage.getItem('vd-live-area') === '1';
    var hat = location.search.indexOf('gruppe=area') !== -1;
    if (will && !hat) location.replace('/live?gruppe=area');
  } catch (e) {}
})();

/* Easy/Expert-Schalter (.204): NUR der Schalter — Modus in localStorage (analog Theme),
   body-Klasse "easy" als Anker; die Seiten ziehen ihre Easy-Ansichten schrittweise nach. */
(function () {
  var w = document.getElementById('ui-modus');
  if (!w) return;
  function setzen(m) {
    document.body.classList.toggle('easy', m === 'easy');
    var bs = w.querySelectorAll('button');
    for (var i = 0; i < bs.length; i++) {
      bs[i].classList.toggle('an', bs[i].getAttribute('data-m') === m);
    }
    try { localStorage.setItem('vd-modus', m); } catch (e) {}
  }
  w.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('button') : null;
    if (b) setzen(b.getAttribute('data-m'));
  });
  var m = null;
  try { m = localStorage.getItem('vd-modus'); } catch (e) {}
  setzen(m === 'easy' ? 'easy' : 'expert');
})();

/* --------------------------------------------------------------- .371 Nachholen auf Knopfdruck
   User 29.08.: "Wenn unser System startet, passiert nichts. Wenn unverarbeitete Events da sind,
   dann bieten wir den Knopf an, die Events zu holen. Beim Druecken des Knopfes koennte eine Frage
   sein, wie weit sollen wir zurueckgehen, wie viele Events sollen wir maximal holen."
   Der Knopf steht im Markup jeder Seite und ist versteckt, bis /health etwas Wartendes meldet.
   Spanne und Vorgaben kommen AUS /health (Whitelist ist die einzige Quelle), nicht von hier. */
var _cuStand = null;

function _cuAnzeigen(d) {
  var k = document.getElementById('catchup-knopf');
  if (!k) return;
  var c = (d && d.start_catchup) || {}, n = c.wartet || 0;
  _cuStand = c;
  /* Waehrend ein Nachhol-Lauf laeuft, zeigt der Banner auf /heute den Fortschritt —
     dann waere ein zweiter Startknopf danebengestellt eine Einladung zum Doppelstart. */
  if (n > 0 && !c.aktiv) {
    document.getElementById('catchup-zahl').textContent = n;
    /* User-Vorgabe 29.08.: ist noch niemand angelernt, kann der Lauf nichts
       ausrichten (der Sweep steigt vor der Analyse aus). Dann steht der Knopf da,
       zeigt die wartende Zahl, ist aber ausgegraut und sagt im Tooltip, was fehlt —
       statt den Nutzer ins Leere klicken zu lassen. */
    var bereit = c.bereit !== false;
    k.disabled = !bereit;
    /* Der normale Tooltip steht serverseitig im Markup und ist dort schon
       uebersetzt — TT() gilt vertraglich nur fuer js.*-Schluessel. Also einmal
       merken und zurueckgeben, statt ihn hier ein zweites Mal zu uebersetzen. */
    if (k.dataset.titel === undefined) k.dataset.titel = k.title;
    k.title = bereit ? k.dataset.titel
                     : TT('js.catchup.nicht_bereit',
                          'Enroll a person first, then these can be checked.');
    k.hidden = false;
  } else {
    k.hidden = true;
  }
}

function catchupPruefen() {
  if (!document.getElementById('catchup-knopf')) return;
  fetch('/health', {cache: 'no-store'})
    .then(function (r) { return r.json(); })
    .then(_cuAnzeigen)
    .catch(function () { /* Dienst gerade weg: der Knopf bleibt, wie er ist */ });
}

function catchupStarten() {
  var dlg = document.getElementById('catchup-dlg'), c = _cuStand || {};
  if (!dlg) return;
  var g = c.grenzen || {}, v = c.vorgabe || {},
      gh = g.stunden, gn = g.limit,
      h = document.getElementById('cu-h'), n = document.getElementById('cu-n');
  /* Spannen und Vorgaben kommen AUSSCHLIESSLICH aus /health, das sie aus der
     CONFIG_WHITELIST liest. Eigene Zahlen hier waeren ein zweites Literal neben
     der einen Quelle — fehlen sie, wird nicht geraten, sondern nachgeladen. */
  if (!gh || !gn) { catchupPruefen(); return; }
  h.min = gh[0]; h.max = gh[1]; h.value = v.stunden || gh[0];
  n.min = gn[0]; n.max = gn[1]; n.value = v.limit || gn[0];
  document.getElementById('cu-h-hint').textContent =
    TT('js.catchup.spanne', '{von} to {bis}', {von: gh[0], bis: gh[1]});
  document.getElementById('cu-n-hint').textContent =
    TT('js.catchup.spanne', '{von} to {bis}', {von: gn[0], bis: gn[1]});
  document.getElementById('catchup-satz').textContent =
    TT('js.catchup.warten', 'Unprocessed events waiting: {n}', {n: c.wartet || 0});
  if (dlg.showModal) { dlg.showModal(); } else { dlg.setAttribute('open', ''); }
}

function catchupSchliessen() {
  var dlg = document.getElementById('catchup-dlg');
  if (!dlg) return;
  if (dlg.close) { dlg.close(); } else { dlg.removeAttribute('open'); }
}

function catchupLos() {
  var hf = document.getElementById('cu-h'), nf = document.getElementById('cu-n'),
      /* Leeres Feld: parseInt liefert NaN, die Rueckfrage zeigte "NaN" und der Lauf
         nahm danach stillschweigend die Config-Werte. Ein leeres Feld heisst hier
         "das Vorgeschlagene", also faellt es auf die Vorgabe zurueck. */
      h = parseInt(hf.value, 10), n = parseInt(nf.value, 10),
      knopf = document.getElementById('catchup-knopf'),
      hk = isNaN(h) ? +hf.min : Math.max(+hf.min, Math.min(+hf.max, h)),
      nk = isNaN(n) ? +nf.min : Math.max(+nf.min, Math.min(+nf.max, n));
  if (isNaN(h)) h = hk;
  if (isNaN(n)) n = nk;
  /* Der Server klemmt an die Whitelist-Spanne. Vorher fragen statt hinterher
     stillschweigend etwas anderes tun, als eingegeben wurde. */
  if ((hk !== h || nk !== n) &&
      !confirm(TT('js.catchup.geklemmt',
                  'Only {h} h and {n} events are possible. Run it with those?',
                  {h: hk, n: nk}))) { return; }
  h = hk; n = nk;
  catchupSchliessen();
  if (knopf) knopf.hidden = true;          /* sofort weg, damit niemand zweimal drueckt */
  fetch('/catchup_start', {method: 'POST', body: JSON.stringify({stunden: h, limit: n})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { alert(d.msg || TT('js.status.fehler', 'error')); catchupPruefen(); return; }
      /* Auf /heute zeigt der Banner den Fortschritt — dorthin, sonst sieht der
         Nutzer von seinem Klick nichts als einen verschwundenen Knopf. */
      if (location.pathname === '/heute' || location.pathname === '/') { location.reload(); }
      else { location.href = '/heute'; }
    })
    .catch(function () { catchupPruefen(); });
}

if (document.getElementById('catchup-knopf')) {
  catchupPruefen();
  /* Nur fragen, wenn jemand hinsieht: ein Hintergrund-Tab braucht keinen
     Minutentakt gegen den Dienst (Widerleger-Fund 29.08.). */
  setInterval(function () { if (!document.hidden) catchupPruefen(); }, 60000);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) catchupPruefen();
  });
}
