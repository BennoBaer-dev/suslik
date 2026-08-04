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
            btn.textContent = 'sync failed: ' + (s.msg || 'see service log');
          }
        }).catch(function () {});
      }, 1500);
    });
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
            st.textContent = 'import failed: ' + (s.msg || 'see service log');
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
            st.textContent = 'import failed: ' + (s.msg || 'see service log');
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
function ukKlappe(uid) {
  var p = document.getElementById('ukp-' + uid);
  if (p) p.hidden = !p.hidden;
}
function ukZuweisen(uid, btn) {
  var cbs = document.querySelectorAll('.ukcb-' + uid + ':checked'), ids = [];
  for (var i = 0; i < cbs.length; i++) ids.push(cbs[i].value);
  var inp = document.getElementById('ukperson-' + uid);
  var person = (inp && inp.value || '').trim();
  var st = document.getElementById('ukst-' + uid);
  if (!ids.length) { if (st) st.textContent = 'tick at least one face'; return; }
  if (!person) { if (st) st.textContent = 'enter a person name'; return; }
  if (!confirm('Add ' + ids.length + ' selected face(s) as "' + person + '"?')) return;
  btn.disabled = true; if (st) st.textContent = 'learning …';
  fetch('/anlernen_benennen', {method: 'POST', body: JSON.stringify({ids: ids.join(','), person: person})})
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (st) st.textContent = d.msg;
      if (d.ok) setTimeout(function () { location.reload(); }, 1400);
      else btn.disabled = false;
    })
    .catch(function () { if (st) st.textContent = 'error'; btn.disabled = false; });
}

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
