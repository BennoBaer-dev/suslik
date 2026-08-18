/* verifyd Web UI — central JS (AP3): GT labeling, previously duplicated per page. */
/* Config sheet (AP5): collect whitelist values, confirm, save, restart */

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
        if (r.ok && warUnten) { txt('Service is back, loading …'); location.href = ziel; return; }
        txt(warUnten ? 'Service coming back …' : 'Saved. Restarting service, please wait …');
        setTimeout(tick, 1500);
      })
      .catch(function () { warUnten = true; txt('Restarting service, please wait …'); setTimeout(tick, 1500); });
  }
  tick();
}

function konfigSpeichern() {
  var felder = document.querySelectorAll('[id^="cfg-"]'),
      d = {}, s = document.getElementById('cfg-status');
  for (var i = 0; i < felder.length; i++) {
    d[felder[i].id.slice(4)] = felder[i].value;
  }
  if (!confirm('Save configuration and restart the service?')) return;
  s.textContent = 'saving …';
  fetch('/konfig', {method: 'POST', body: JSON.stringify(d)})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      s.textContent = r.msg;
      if (r.ok) _neustartDann(location.href, s);
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
  out.textContent = '≈ total ~' + (s >= 60 ? Math.round(s / 60) + ' min' : s + ' s') +
                    ' at ' + fps + '/s';
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
      document.getElementById('ll-status').textContent = d.msg || (d.ok ? 'ok' : 'error');
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
    document.getElementById('lf-pop-status').textContent = 'pick a day first';
    return;
  }
  btn.disabled = true;
  var body = {fps: fps, person: person, weiter: !!(w && w.checked)};
  if (tag) body.tag = tag; else body.events = n;
  fetch('/lernlauf_start', {method: 'POST', body: JSON.stringify(body)})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      document.getElementById('lf-pop-status').textContent = d.msg || (d.ok ? 'ok' : 'error');
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
      else { alert(d.msg || 'error'); btn.disabled = false; }
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
      else { alert(d.msg || 'error'); btn.disabled = false; }
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
      else { alert(d.msg || 'error'); btn.disabled = false; }
    })
    .catch(function () { btn.disabled = false; });
}

function lernlaufAbbruch(btn) {
  if (!confirm('Abort this learning run?')) return;
  btn.disabled = true;
  fetch('/lernlauf_abbruch', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function () { location.href = '/lernlauf'; })
    .catch(function () { btn.disabled = false; });
}

function notifSpeichern() {
  var s = document.getElementById('notif-status');
  if (!confirm('Save notification settings and restart the service?')) return;
  s.textContent = 'saving …';
  fetch('/benachrichtigung_speichern', {method: 'POST', body: JSON.stringify(_notifFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) { s.textContent = r.msg; if (r.ok) _neustartDann('/benachrichtigungen', s); })
    .catch(function () { _neustartDann('/benachrichtigungen', s); });
}

function testKanal(kanal, btn) {
  var st = document.getElementById('test-' + kanal);
  btn.disabled = true; st.textContent = 'sending …';
  fetch('/test_' + kanal, {method: 'POST', body: JSON.stringify(_notifFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) { st.textContent = r.msg; btn.disabled = false; })
    .catch(function (e) { st.textContent = 'error'; btn.disabled = false; });
}

function frigateWrite(readonly) {
  var txt = readonly ? 'Switch to READ-ONLY? suslik will stop writing to Frigate.'
                     : 'Enable WRITING to Frigate (sub_labels + reference sync)?';
  if (!confirm(txt)) return;
  var st = document.getElementById('fw-status');
  st.textContent = 'saving …';
  fetch('/konfig', {method: 'POST', body: JSON.stringify({frigate_read_only: readonly})})
    .then(function (r) { return r.json(); })
    .then(function (d) { st.textContent = d.msg || (d.ok ? 'saved' : 'error'); if (d.ok) setTimeout(function () { location.reload(); }, 800); })
    .catch(function () {});
}

function configRestore(input) {
  var f = input.files && input.files[0];
  if (!f) return;
  if (!confirm('Restore configuration from "' + f.name + '"? This overwrites the current settings and restarts the service.')) { input.value = ''; return; }
  var st = document.getElementById('restore-status');
  st.textContent = 'restoring …';
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
  if (!confirm('Restore the FULL backup "' + f.name + '"? This replaces settings, references and all learned material, then restarts the service.')) { input.value = ''; return; }
  var st = document.getElementById('vollrestore-status');
  st.textContent = 'uploading + restoring … (large files take a while)';
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
        alert('Error: ' + d.msg);
      }
    });
}
function enrollFremd(id, el) {
  var sel = document.getElementById('sel-' + id),
      neu = document.getElementById('neu-' + id),
      person = (neu && neu.value.trim()) || (sel && sel.value) || '';
  if (!person) { alert('Choose a person or enter a new one.'); return; }
  enroll(id, 'aufnehmen', person, el);
}
function uploadRef() {
  var neu = document.getElementById('up-neu'),
      p = (neu && neu.value.trim()) || document.getElementById('up-person').value,
      f = document.getElementById('up-datei').files[0],
      s = document.getElementById('up-status');
  if (!p || !f) { alert('Choose a person (dropdown or new) and a file.'); return; }
  s.textContent = 'uploading …';
  var senden = function (personWert) {
    fetch('/upload?person=' + encodeURIComponent(personWert), {method: 'POST', body: f})
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok && d.msg && d.msg.indexOf('GATE') === 0 &&
            confirm(d.msg + '\n\nAdd anyway?')) {
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
  if (!confirm('Add group as "' + person + '" (best images become references)?')) return;
  btn.disabled = true; btn.textContent = 'learning …';
  fetch('/anlernen_benennen', {method: 'POST', body: JSON.stringify({ids: ids, person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      var c = btn.closest('.card');
      if (d.ok && c) { c.style.opacity = 0.45; } else { btn.disabled = false; }
    })
    .catch(function () { btn.textContent = 'Error'; btn.disabled = false; });
}
function anlernNeu(ids, btn) {
  var person = (window.prompt('Name of the new person:') || '').trim();
  if (person) anlernSenden(ids, person, btn);
}
function anlernZu(ids, selId, btn) {
  var person = document.getElementById(selId).value;
  if (!person) { alert('Please choose an existing person.'); return; }
  anlernSenden(ids, person, btn);
}
/* reverse path: add ticked matching faces to an existing person */
function aehnlicheHinzu(person, btn) {
  var cbs = document.querySelectorAll('.ae-cb:checked'), ids = [];
  for (var i = 0; i < cbs.length; i++) ids.push(cbs[i].value);
  if (!ids.length) { alert('Please tick at least one face.'); return; }
  anlernSenden(ids.join(','), person, btn);
}
/* Library search: take ticked suggestions from recognized events / search again */
function vorschlaegeAlleEmpfohlen(person, btn) {   // Auto-Uebernehmen: alle empfohlenen auf einmal (User 22.07.)
  var cbs = document.querySelectorAll('.vs-cb-rec'), items = [];
  for (var i = 0; i < cbs.length; i++) {
    var v = cbs[i].value.split('|');
    items.push({eid: v[0], datei: v.slice(1).join('|')});
  }
  if (!items.length) { alert('No recommended faces.'); return; }
  if (!confirm('Add all ' + items.length + ' recommended face(s) to ' + person +
               '? They become references immediately.')) return;
  btn.disabled = true; btn.textContent = 'adding …';
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
  if (!items.length) { alert('Please tick at least one face.'); return; }
  if (!confirm('Add ' + items.length + ' face(s) to ' + person + '?')) return;
  btn.disabled = true; btn.textContent = 'adding …';
  fetch('/vorschlag_aufnehmen', {method: 'POST', body: JSON.stringify({person: person, items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}
function vorschlagNeu(person, btn) {
  btn.disabled = true; btn.textContent = 'searching …';
  fetch('/vorschlaege_neu', {method: 'POST', body: JSON.stringify({person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      setTimeout(function () { location.reload(); }, 4000);
    });
}
/* Maintenance (collect + check) manually */
function anlernWartungJetzt(btn) {
  btn.disabled = true; btn.textContent = 'running …';
  fetch('/anlern_wartung_jetzt', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) { btn.textContent = d.msg; });
}
/* Reference sync Master <-> Frigate (System page) */
function syncAktion(modus, btn) {
  var txt = modus === 'export' ? 'Master → Frigate' : 'Frigate → Master';
  if (!confirm('Synchronize: ' + txt + '?')) return;
  btn.disabled = true; btn.textContent = 'starting …';
  fetch('/sync_' + modus, {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { btn.textContent = d.msg; return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (s.phase === 'loading') {
            btn.textContent = 'loading model …';
          } else if (s.phase === 'import' || s.phase === 'export') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            btn.textContent = s.done + '/' + s.total + ' faces (' + (s.current || '') + ') ' + pct + '%';
          } else if (s.phase === 'done') {
            clearInterval(poll);
            btn.textContent = 'done: ' + (s.ok || 0) + ' ok, ' + (s.gate || 0) + ' skipped — reloading …';
            setTimeout(function () { location.reload(); }, 2000);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            /* .131: Ursache/Hinweis zeigen, nicht nur 'rc=1' (carlsmith-Fall:
               Frigate-Erkennung aus -> Schalt-Hinweis direkt am Knopf). */
            btn.textContent = 'sync failed: ' + (s.hinweis || s.detail || s.msg || 'see service log');
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
    b.textContent = n ? 'Transfer ' + n + ' selected to Frigate' : 'Nothing selected';
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
  var zurueck = btn.dataset.label || (weg ? 'skip' : 'restore');
  btn.disabled = true; btn.textContent = weg ? 'skipping …' : 'restoring …';
  fetch('/sync_abwahl', {method: 'POST', body: JSON.stringify(d)})
    .then(function (r) { return r.json(); })
    .then(function (dd) {
      /* .134: ok:false auswerten — eine fehlgeschlagene Abwahl sah vorher wie
         eine erfolgreiche aus (Seite lud einfach neu). */
      if (dd && dd.ok) { location.reload(); return; }
      alert((dd && dd.msg) || 'error');
      btn.disabled = false; btn.textContent = zurueck;
    })
    .catch(function () { btn.disabled = false; btn.textContent = zurueck; });
}
/* .137 'offer again': ein in Frigate geloeschtes oder frueher exportiertes Bild
   wieder zum normalen Kandidaten machen (POST /sync_wieder_anbieten). */
function syncWiederAnbieten(btn) {
  var zurueck = btn.dataset.label || 'offer again';
  btn.disabled = true; btn.textContent = 'putting it back …';
  fetch('/sync_wieder_anbieten', {method: 'POST',
        body: JSON.stringify({bilder: [[btn.dataset.person, btn.dataset.datei]]})})
    .then(function (r) { return r.json(); })
    .then(function (dd) {
      if (dd && dd.ok) { location.reload(); return; }
      alert((dd && dd.msg) || 'error');
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
  if (!sel.length) { if (st) st.textContent = 'nothing selected'; return; }
  if (!confirm('Send ' + sel.length + ' reference image(s) to Frigate?')) return;
  /* .137: Fehlertexte gehoeren NICHT in den gruenen Startknopf (Operator-Fund
     06.08.: ein gruener Knopf mit Fehlermeldung darin liest sich wie Erfolg).
     Der Knopf wird neutral-rot beschriftet, der Text steht daneben — mit dem
     Diagnose-Anker, Muster gesImport. */
  function scheitern(txt) {
    btn.className = 'gtb sa-crit'; btn.textContent = 'transfer failed';
    btn.disabled = false;
    if (!st) return;
    st.className = 'sa-crit'; st.textContent = txt + ' ';
    var dg = document.createElement('a');
    dg.href = '/sync_diagnose'; dg.target = '_blank'; dg.textContent = 'diagnosis';
    st.appendChild(dg);
  }
  btn.disabled = true; btn.textContent = 'starting …';
  fetch('/sync_auswahl_start', {method: 'POST', body: JSON.stringify({auswahl: sel})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { scheitern(d.msg || 'error'); return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (s.phase === 'export') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            btn.textContent = s.done + '/' + s.total + ' (' + (s.current || '') + ') ' + pct + '%';
          } else if (s.phase === 'done') {
            clearInterval(poll);
            btn.textContent = 'done: ' + (s.ok || 0) + ' uploaded, ' + (s.gate || 0)
              + ' not accepted — reloading …';
            setTimeout(function () { location.reload(); }, 1500);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            /* Ursache/Hinweis zeigen, nicht 'rc=1' (carlsmith-Fall .131) */
            scheitern('transfer failed: ' + (s.hinweis || s.detail || s.msg || 'see service log'));
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
          el.textContent = 'pre-check appears stuck — reload the page to retry';
          return;
        }
        el.textContent = 'checking images … ' + (s.fertig || 0) + '/' + (s.gesamt || 0);
      } else {
        clearInterval(poll);
        if (s.fehler) { el.textContent = 'pre-check failed: ' + s.fehler; return; }
        el.textContent = 'pre-check done — reloading …';
        setTimeout(function () { location.reload(); }, 800);
      }
    }).catch(function () {});
  }, 1500);
}

/* Setup wizard step 4: import faces from Frigate with live progress */
function wizImport(btn) {
  var url = (document.getElementById('setup-url') || {}).value || '';
  var st = document.getElementById('wiz-import-status');
  btn.disabled = true; btn.textContent = 'starting …';
  fetch('/sync_import', {method: 'POST', body: JSON.stringify({url: url})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { if (st) st.textContent = d.msg || 'error'; btn.disabled = false; return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (!st) return;
          if (s.phase === 'import') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            st.textContent = 'downloading ' + s.done + '/' + s.total + ' (' + (s.current || '') + ') ' + pct + '%';
          } else if (s.phase === 'done') {
            clearInterval(poll);
            st.textContent = '✓ imported ' + (s.ok || 0) + ' — computing features on the accelerator …';
            btn.textContent = 'Imported ✓';
          } else if (s.phase === 'error') {
            /* Der Server meldet Fehler sauber (phase:'error'), aber diese Schleife wertete nur
               import/done aus — bei einem Fehler pollte sie endlos, der Text fror ein und der
               Knopf blieb tot (Plan-QS P.9). Die Zwillingsfunktion oben macht es laengst so. */
            clearInterval(poll);
            st.textContent = 'import failed: ' + (s.hinweis || s.detail || s.msg || 'see service log') + ' ';
            var dg1 = document.createElement('a');
            dg1.href = '/sync_diagnose'; dg1.target = '_blank'; dg1.textContent = 'diagnosis';
            st.appendChild(dg1);
            btn.disabled = false; btn.textContent = 'Import faces';
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
  btn.disabled = true; btn.textContent = 'starting …';
  fetch('/sync_import', {method: 'POST', body: JSON.stringify({})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { if (st) st.textContent = d.msg || 'error'; btn.disabled = false; btn.textContent = 'Import faces from Frigate'; return; }
      var poll = setInterval(function () {
        fetch('/sync_status').then(function (r) { return r.json(); }).then(function (s) {
          if (!st) return;
          if (s.phase === 'import') {
            var pct = s.total ? Math.round(100 * s.done / s.total) : 0;
            st.textContent = 'downloading ' + s.done + '/' + s.total + ' (' + (s.current || '') + ') ' + pct + '%';
          } else if (s.phase === 'done') {
            clearInterval(poll);
            st.textContent = '✓ imported ' + (s.ok || 0) + ' — computing features, page reloads …';
            setTimeout(function () { location.reload(); }, 2500);
          } else if (s.phase === 'error') {
            clearInterval(poll);
            st.textContent = 'import failed: ' + (s.hinweis || s.detail || s.msg || 'see service log') + ' ';
            var dg2 = document.createElement('a');
            dg2.href = '/sync_diagnose'; dg2.target = '_blank'; dg2.textContent = 'diagnosis';
            st.appendChild(dg2);
            btn.disabled = false; btn.textContent = 'Import faces from Frigate';
          }
        }).catch(function () {});
      }, 1000);
    });
}

/* Check (19.07.): remove a single reference image / recompute reference QC */
function refEntfernen(person, datei, btn) {
  if (!confirm('Remove reference image of ' + person + '?')) return;
  btn.disabled = true; btn.textContent = 'removing …';
  fetch('/ref_entfernen', {method: 'POST', body: JSON.stringify({person: person, datei: datei})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      var c = btn.closest('.card');
      if (d.ok && c) { c.style.opacity = 0.4; }
    });
}
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
      if (!d.ok) { if (s) s.textContent = d.msg || 'error'; btn.disabled = false; return; }
      location.href = '/qualitaet' + (d.person ? '?person=' + encodeURIComponent(d.person) : '');
    })
    .catch(function () {
      /* .282: NIE still scheitern — Klicks waehrend eines Dienst-Neustarts
         (Deploy) liefen sonst ins Leere und der Knopf wirkte tot. */
      var s = document.getElementById('qs-status');
      if (s) s.textContent = 'cannot reach the service — try again in a moment.';
      btn.disabled = false;
    });
}

function qsPerson(name, btn) {
  /* .273c: Kontext-Start von der Personen-Seite — Lauf ist immer global,
     die Ergebnis-Sicht springt gefiltert auf die Person. */
  btn.disabled = true; btn.textContent = 'checking …';
  fetch('/qualitaet/start', {method: 'POST',
                             body: JSON.stringify({person: name})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) { btn.textContent = d.msg || 'error'; btn.disabled = false; return; }
      location.href = '/qualitaet?person=' + encodeURIComponent(name);
    })
    .catch(function () { btn.disabled = false; });
}

function refPruefNeu(btn) {
  btn.disabled = true; btn.textContent = 'checking …';
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
  if (!items.length) { alert('Please select at least one image.'); return; }
  if (!confirm('Delete ' + items.length + ' image(s)?')) return;
  btn.disabled = true; btn.textContent = 'deleting …';
  fetch('/ref_entfernen_batch', {method: 'POST', body: JSON.stringify({items: items})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 900);
    });
}

function gt(eid, label, el) {
  fetch('/gt', {method: 'POST', body: JSON.stringify({eid: eid, label: label})})
    .then(function (r) {
      if (!r.ok) return;
      var p = el.parentElement,
          bs = p.querySelectorAll('.gtb'),
          ss = p.querySelectorAll('select');
      /* Auswahl ueber Klassen, NICHT ueber Inline-Farben (Fund 25.07.). Vorher setzte diese
         Funktion nach jedem Klick '#333' auf alle Selects und '#2a6' auf das gewaehlte — ohne die
         Textfarbe mitzusetzen, die vorher als 'color:#eee' daneben stand und beim Zentralisieren
         der Formularelemente entfiel. Ergebnis im jetzt voreingestellten Hellmodus: dunkler Grund
         unter dunklem Text, gemessen 1,31:1 statt 10,89. Das Zentralisieren hatte nur verifyd.py
         erfasst; das JavaScript schrieb die Festfarben stillschweigend wieder hin. */
      for (var i = 0; i < bs.length; i++) bs[i].className = 'gtb';
      for (var i = 0; i < ss.length; i++) ss[i].classList.remove('gewaehlt');
      if (el.tagName === 'SELECT') { el.classList.add('gewaehlt'); }
      else { el.className = 'gtb on'; }
      var card = el.closest('.card');
      if (card && card.dataset.fadeOnLabel) { card.style.opacity = 0.35; }
    });
}

/* Unknown tab (20.07.): assign to person / ignore / merge / re-run */
function unbReconcile(btn) {
  /* Verlaufs-Timer (requirement: progress must stay visible while a long job runs)
     — Sekunden + Phase aus /reconcile_status, bis der POST zurueck ist. */
  btn.disabled = true;
  var start = Date.now();
  var tick = setInterval(function () {
    var s = Math.round((Date.now() - start) / 1000);
    fetch('/reconcile_status').then(function (r) { return r.json(); }).then(function (d) {
      btn.textContent = (d.phase && d.phase !== '-' ? d.phase : 'running') + ' … ' + s + ' s';
    }).catch(function () { btn.textContent = 'running … ' + s + ' s'; });
  }, 1000);
  btn.textContent = 'running … 0 s';
  fetch('/unbekannt_reconcile', {method: 'POST', body: '{}'})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      clearInterval(tick);
      btn.textContent = d.msg;
      setTimeout(function () { location.reload(); }, 1200);
    })
    .catch(function () { clearInterval(tick); btn.textContent = 'error'; btn.disabled = false; });
}
function unbBesucher(uid, an, btn) {
  if (an && !confirm('Ignore as a known stranger? It will no longer trigger alerts. (Re-activate any time under "known visitors" below.)')) return;
  fetch('/unbekannt_besucher', {method: 'POST', body: JSON.stringify({uid: uid, an: an})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 700);
    });
}
function unbMerge(uid, btn) {
  var sel = document.getElementById('mg-' + uid), b = sel && sel.value;
  if (!b) { alert('Choose a target identity.'); return; }
  unbMergePaar(uid, b, btn);
}
function unbMergePaar(a, b, btn) {
  if (!confirm('Merge?')) return;
  btn.disabled = true;
  fetch('/unbekannt_merge', {method: 'POST', body: JSON.stringify({a: a, b: b})})
    .then(function (r) { return r.json(); })
    .then(function (d) { btn.textContent = d.msg; if (d.ok) setTimeout(function () { location.reload(); }, 800); });
}
function unbVerwerfen(a, b, btn) {
  // 'Different' persistent (25.07.): vorher nur display:none — nach Reload/Reconcile
  // stand dieselbe Frage wieder da. Der Server merkt sich das Paar dauerhaft.
  var m = btn.closest('.merge'); if (m) m.style.display = 'none';
  fetch('/unbekannt_verwerfen', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({a: a, b: b})}).catch(function () {});
}
function unbBenennen(uid, btn) {
  var nm = document.getElementById('nm-' + uid), p = nm && nm.value.trim();
  if (!p) { alert('Enter a name (new or existing person).'); return; }
  if (!confirm('Assign to "' + p + '"? The best images become references.')) return;
  btn.disabled = true; btn.textContent = 'learning …';
  fetch('/unbekannt_benennen', {method: 'POST', body: JSON.stringify({uid: uid, person: p})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      var c = document.getElementById('uk-' + uid);
      if (d.ok && c) { c.style.opacity = 0.4; setTimeout(function () { location.reload(); }, 1200); }
      else { btn.disabled = false; }
    });
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
  btn.disabled = true; if (s) s.textContent = 'saving …';
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
  btn.disabled = true; if (s) s.textContent = 'saving …';
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
  var tipp = prompt('Delete ALL references and the name "' + person + '"?\n' +
                    'The images move to the trash folder (recoverable).\n\n' +
                    'Type the name to confirm:');
  if (tipp === null) return;
  if (tipp.trim() !== person) { alert('Name did not match — nothing deleted.'); return; }
  btn.disabled = true; btn.textContent = 'removing …';
  fetch('/person_loeschen', {method: 'POST', body: JSON.stringify({person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      btn.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.href = '/gesichter'; }, 1500);
      else btn.disabled = false;
    })
    .catch(function () { btn.textContent = 'error'; btn.disabled = false; });
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
    for (var i = 0; i < spans.length; i++) spans[i].textContent = '(' + s + ' s)';
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
  if (s) s.textContent = 'saving …';
  fetch('/areas_speichern', {method: 'POST',
    body: JSON.stringify({areas: _areasPaareObjekt(paare)})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (s) s.textContent = d.msg;
      if (d.ok) location.reload();
      else if (btn) btn.disabled = false;
    })
    .catch(function () {
      if (s) s.textContent = 'save failed — is the service reachable?';
      if (btn) btn.disabled = false;
    });
}
function areaAnlegen(btn) {
  var f = document.getElementById('ar-neu'), n = (f && f.value || '').trim();
  if (!n) { alert('Enter an area name first.'); return; }
  var paare = _areasSammeln(), i;
  for (i = 0; i < paare.length; i++) {
    if (paare[i][0].toLowerCase() === n.toLowerCase()) { alert('This area already exists.'); return; }
  }
  paare.push([n, []]);
  areasSpeichern(btn, paare);
}
function areaEntfernen(btn) {
  var p = btn.closest('.ar-pill'), n = p && p.dataset.area;
  if (!n) return;
  if (!confirm('Remove area "' + n + '"? Its cameras return to Default — nothing else changes.')) return;
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
    if (st) st.textContent = 'error: ' + (d.msg || r.status);
  } catch (e) {
    if (st) st.textContent = 'error: ' + e;
  }
  btn.disabled = false;
}

// PE1: laufenden Person-Learn-Lauf abbrechen (Geerntetes bleibt).
async function personlaufAbbruch(btn) {
  if (!confirm('Abort this person-learn run? Harvested images are kept.')) return;
  btn.disabled = true;
  try {
    var r = await fetch('/personlauf_abbruch', { method: 'POST' });
    if (r.ok) { location.reload(); return; }
  } catch (e) { /* Reload zeigt den echten Zustand */ }
  btn.disabled = false;
}

// PE2b: kompletten Lauf verwerfen (schlechtes Ergebnis), Wizard wird frei.
async function personlaufVerwerfen(lid) {
  if (!confirm('Discard run ' + lid + ' completely? All its images are deleted; a new run can re-harvest any time.')) return;
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
  s.textContent = 'saving …';
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
    .catch(function () { return {ok: false, msg: 'could not reach the service — nothing was saved'}; })
    .then(function (r) {
      if (!r.ok) { s.textContent = r.msg; return; }
      VIS_DIRTY.block = false;
      _visionDirtyZeigen();
      if (!zahlenDirty) {
        s.textContent = 'saved — recognition uses this connection from now on';
        _visionDirtySetzen(null);
        if (danach) danach();
        return;
      }
      return fetch('/konfig', {method: 'POST', body: JSON.stringify(zahlen)})
        .then(function (r2) { return r2.json(); })
        .then(function (r2) {
          s.textContent = r2.ok ? 'saved — the service restarts in a moment' : r2.msg;
          if (r2.ok) { _visionDirtySetzen(null); VIS_NAV_OK = true; _neustartDann('/vision', s); }
        })
        .catch(function () {
          s.textContent = 'saved — the service is restarting, this page reloads in a moment';
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
  if (s.dauer_s != null) w.push(s.dauer_s + ' s');
  if (s.treffer != null) w.push(s.treffer + '/2 right');
  if (s.ist != null) w.push(s.ist + ' tokens vs ' + s.soll);
  return (s.text || '') + (w.length ? ' · ' + w.join(' · ') : '');
}

function visionTest(btn) {
  if (VIS_DIRTY.block || VIS_DIRTY.zahlen) {
    /* Der Irrtum, den der User beschrieben hat: nach einem gruenen Test hielt
       er die Sache fuer erledigt — dabei hatte er nie gespeichert. */
    _visionFrage(
      'You have not saved this connection',
      'The test would use the values you just typed. Recognition keeps using ' +
      'the SAVED connection until you press Save — a green test alone changes ' +
      'nothing about the verdicts.',
      [['Save first, then test', function () { visionSpeichern(function () { _visionTestLauf(btn); }); }],
       ['Test without saving', function () { _visionTestLauf(btn); }],
       ['Cancel', function () { btn.disabled = false; }]]);
    return;
  }
  _visionTestLauf(btn);
}

function _visionTestLauf(btn) {
  var st = document.getElementById('vision-test-status');
  var namen = ['reachability and model', 'forced-choice shape grids', 'token count'];
  btn.disabled = true;
  var felder = _visionFelder();
  function stufe(nr) {
    st.textContent = 'step ' + nr + '/3 — ' + namen[nr - 1] +
      ' … (a local model on CPU can take minutes)';
    var z = document.getElementById('vs-log-' + nr);
    if (z) z.textContent = 'running …';
    felder.stufe = nr;
    return fetch('/vision/test', {method: 'POST', body: JSON.stringify(felder)})
      .then(function (r) { return r.json(); })
      .then(function (r) {
        var s = r.msg && r.msg.stufe;
        if (!s) { st.textContent = (r.msg && r.msg.msg) || r.msg || 'the test could not be run'; btn.disabled = false; return; }
        if (z) z.textContent = _visionStufeText(s);
        if (!r.msg.weiter) {
          st.textContent = 'stopped at step ' + nr + ' — see the log below';
          location.reload();
          return;
        }
        if (nr < 3) return stufe(nr + 1);
        st.textContent = 'done — ' + r.msg.ampel.toUpperCase();
        location.reload();
      })
      .catch(function () {
        st.textContent = 'step ' + nr + ' could not be run';
        btn.disabled = false;
      });
  }
  stufe(1);
}

function visionSchalter(an) {
  var st = document.getElementById('vision-schalter-status');
  st.textContent = 'saving …';
  fetch('/vision/schalter', {method: 'POST', body: JSON.stringify({aktiv: an})})
    .then(function (r) { return r.json(); })
    .then(function (r) { st.textContent = r.msg || ''; if (r.ok) location.reload(); })
    .catch(function () {
      /* Der Schalter selbst startet den Dienst nicht neu — aber ein
         gleichzeitiger Neustart (z.B. vom Speichern nebenan) kappt trotzdem
         die Verbindung. Auch hier: warten und neu laden statt "error". */
      st.textContent = 'the service is not answering right now — this page reloads in a moment';
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
  if (!confirm('Reset the question to the default wording?')) return;
  t.value = (typeof VIS_PROMPT_STD === 'string') ? VIS_PROMPT_STD : '';
  document.getElementById('vision-status').textContent =
    'default wording restored — press Save to store it';
}

/* --- Recognition test (konzept_vision.md v2 §4, Zug V4) ----------------------
   Der Lauf faehrt den ECHTEN Urteilspfad und dauert je nach Backend Sekunden
   bis Minuten; die Seite laedt sich waehrenddessen selbst nach (refresh). */
function rtVision(btn) {
  var st = document.getElementById('rt-vision-status');
  btn.disabled = true;
  st.textContent = 'starting the vision run …';
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
    .catch(function () { st.textContent = 'the run could not be started'; btn.disabled = false; });
}

/* .161: den Durchgang noch einmal analysieren, wenn der Sammel-Modus AN ist und
   trotzdem kein Material da ist. Der Knopf steht nur in genau diesem Fall auf
   der Seite; hier wird er nur ausgeloest. */
function rtNachanalyse(btn) {
  var st = document.getElementById('rt-nach-status');
  btn.disabled = true;
  st.textContent = 'starting …';
  fetch('/vision/nachanalyse', {method: 'POST', body: JSON.stringify({pass_key: RT_PASS})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) setTimeout(function () { location.reload(); }, 3000);
      else btn.disabled = false;
    })
    .catch(function () { st.textContent = 'it could not be started'; btn.disabled = false; });
}

/* --- Vision detect V2: Kacheln, Key-Sofortpruefung, Modellwahl ---------------
   Die Kachel wird NICHT beim Klick gespeichert, sondern nur angezeigt
   (?kachel=). Sonst muesste man eine externe Verbindung speichern, um
   ueberhaupt die Cloud-Bestaetigung zu sehen, die das Speichern verlangt — ein
   Ring. Gespeichert wird erst mit "Save", geprueft mit "Check the key". */
function visionKachel(name) {
  if ((VIS_DIRTY.block || VIS_DIRTY.zahlen)
      && !confirm('You have unsaved changes. Switching provider discards them. Continue?')) return;
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
    leer.textContent = '— pick one —';
    s.appendChild(leer);
  }
  for (var i = 0; i < modelle.length; i++) {
    var m = modelle[i], o = document.createElement('option');
    o.value = m.id;
    /* Die Anmerkung kommt vom SERVER (Messwerte-Registry) — hier steht keine
       Zahl und kein Modellname fest im Code. */
    o.textContent = m.id + ' — ' + ((m.badge && m.badge.text) || 'untested here');
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
  if (i) i.textContent = 'the connection changed — check it again to see which models it has';
}

function visionSchluessel(btn) {
  var st = document.getElementById('vision-key-status');
  btn.disabled = true;
  st.textContent = 'asking the provider which models you can use …';
  fetch('/vision/schluessel', {method: 'POST', body: JSON.stringify(_visionFelder())})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      btn.disabled = false;
      var d = r.msg || {};
      st.textContent = d.text || d || '';
      var info = document.getElementById('vision-modell-info');
      if (!r.ok) { if (info) info.textContent = d.text || 'the check failed'; _visionModellListe([], ''); return; }
      VIS_ENTDECKT = {endpunkt: d.endpunkt, kachel: d.kachel};
      if (info) info.textContent = d.text || '';
      var sel = document.getElementById('vision-modell');
      _visionModellListe(d.modelle, sel ? sel.value : '');
    })
    .catch(function () { st.textContent = 'the check could not be run'; btn.disabled = false; });
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
  st.textContent = 'saving …';
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
    .catch(function () { st.textContent = 'error'; sel.disabled = false; });
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
      k.querySelector('.vw-m').innerHTML = zeile.innerHTML
        + (neu.geliehen_aus ? '<div class="vw-warn">from the ' + neu.geliehen_aus + ' row</div>' : '');
    })
    .catch(function () { k.style.opacity = '1'; });
}

function vwVergessen() {
  if (!confirm('Forget the images you rejected for this gallery? They can be proposed again.')) return;
  fetch('/vision/galerie/vergessen', {method: 'POST', body: JSON.stringify({person: VW_PERSON})})
    .then(function () { location.reload(); });
}

function vwAbnehmen(btn) {
  var st = document.getElementById('vw-status');
  var auswahl = VW_ZELLEN.map(function (z) { return z && z.schluessel ? z.schluessel : null; });
  var leer = auswahl.filter(function (s) { return !s; }).length;
  if (leer && !confirm(leer + ' cell(s) could not be filled. Approve the gallery anyway?')) return;
  btn.disabled = true;
  st.textContent = 'copying the pictures into the gallery …';
  fetch('/vision/galerie/abnahme', {method: 'POST', body: JSON.stringify(
    {person: VW_PERSON, groesse: VW_GROESSE, auswahl: auswahl})})
    .then(function (r) { return r.json(); })
    .then(function (r) {
      st.textContent = r.msg || '';
      if (r.ok) location.href = '/vision/galerie?person=' + encodeURIComponent(VW_PERSON);
      else btn.disabled = false;
    })
    .catch(function () { st.textContent = 'error'; btn.disabled = false; });
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
          hoehe: (document.querySelector('input[name="lv-hoehe"]:checked') || {}).value || null};
}

function liveSpeichern(btn) {
  var s = document.getElementById('lv-status');
  btn.disabled = true; if (s) s.textContent = 'saving …';
  fetch('/live_speichern', {method: 'POST', body: JSON.stringify(_liveFelder())})
    .then(function (r) { return r.json(); })
    .then(function (d) { if (s) s.textContent = d.msg; btn.disabled = false; })
    .catch(function () { if (s) s.textContent = 'error'; btn.disabled = false; });
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
          var ph = {verbinden: 'Connecting', messen: 'Measuring',
                    auswerten: 'Evaluating', abbruch: 'Aborting'}[a.phase] || a.phase;
          var rest = (a.rest_s !== null && a.rest_s !== undefined)
            ? ' — ' + Math.ceil(a.rest_s) + ' s left' : '';
          /* UI-KANN 11: 'watchers paused' nur, wenn wirklich welche pausieren
             (Quelltests pausieren nicht; ohne Waechter pausiert niemand). */
          el.textContent = (a.art === 'messung' ? 'Load measurement' : 'Source test')
            + ' on ' + a.kamera + ': ' + ph + rest
            + (a.pausiert && a.pausiert.length
               ? ' — watchers paused for measurement (' + a.pausiert.join(', ') + ')'
               : '');
        } else { el.textContent = ''; }
      }
      Object.keys(d.jobs || {}).forEach(function (kam) {
        var j = d.jobs[kam];
        var jel = document.getElementById('lv-job-' + kam);
        if (!jel) return;
        if (!j.fertig)
          jel.textContent = 'source test running (helper process, up to ~2 minutes) …';
        else if (j.text !== undefined)
          /* UI-M3: das Helfer-ERGEBNIS anzeigen, nicht nur das Laufen. */
          jel.textContent = (j.ok ? 'source test done: ' : 'source test FAILED: ')
            + (j.text || '');
      });
      /* UI-M3: Fehl-Auftraege der Engine sichtbar machen (frisch-gegated). */
      Object.keys(d.auftraege || {}).forEach(function (kam) {
        var e = d.auftraege[kam];
        ['test', 'messung'].forEach(function (art) {
          var b = e[art];
          if (b && b.ok === false && b.fehler) {
            var jel = document.getElementById('lv-job-' + kam);
            if (jel) jel.textContent = (art === 'messung'
              ? 'load measurement failed: ' : 'source test failed: ') + b.fehler;
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
