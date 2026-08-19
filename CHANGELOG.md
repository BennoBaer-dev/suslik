# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). History older than 0.1.0.180 has been trimmed from
this file — the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git
history.

## 0.1.0.298 — 2026-08-19

Interim release. Bundles the internal steps 0.1.0.287–0.1.0.297.

- **Crash fix for large learning runs**: found and fixed a bug that could
  cause a crash of Frigate during very large, long learning runs with many
  events. Clip fetching for past events now takes a sturdier path and
  reports failures instead of piling up stalled downloads.
- **suslik now speaks five languages** — English, German, Spanish, Italian
  and French. Pick yours with the new switch in the header (or in step 0 of
  the setup wizard); the choice applies to the whole installation and
  survives backups. Translation is rolling out page by page: the menu, all
  dialogs, the main pages and the Today view are done, pages not yet
  translated say so honestly and follow with the next releases.
- **Learning runs tidy up after themselves**: groups without usable faces
  are set aside automatically at the end of a run (with a review link,
  nothing is deleted), so naming only shows real groups and the counters
  stay accurate.
- **Today as a tile grid**: the recognized-live row and person cards align
  in a steady grid instead of ragged rows.

## 0.1.0.286 — 2026-08-18

Interim release (entry added retroactively — it was missing from this file;
the GitHub release existed all along). Bundles the internal steps
0.1.0.244–0.1.0.285; 0.1.0.284/.285 were respun as 0.1.0.286 after the
privacy and layout gates flagged two issues (an operator name in old
comments, a table overflow on phone widths).

- Focused work on face learning: guided learning runs and easier assigning
  of faces to people.
- Picture quality: a one-click check finds weak, duplicate and mixed-up
  reference pictures for you.
- Clearer camera setup and configuration.

## 0.1.0.243 — 2026-08-17

Intermediate release — focus on simplification and clarity. We are mid-way
through the Easy/Expert rebuild; this release bundles the internal steps
0.1.0.203–0.1.0.242 (each documented below; 0.1.0.241/.242 were respun as
0.1.0.243 after the privacy gates flagged private names in old code
comments — comments neutralized, the name check itself hardened, nothing
else changed). The visible core:

- **Configuration start page, Faces area, guided learning flow**: tile-based
  start pages with plain-language "How it works" texts, a step-by-step
  learning run, and a naming card that walks you through the found groups.
- **Learn directly from the day view**: a person's pass cards offer a
  check/adopt bridge — review the suggested faces (borderline ones shown
  unticked), adopt them as references in one click, undo if needed. Already
  adopted references carry a green outline.
- **Unknown visitors, consistently**: clicking an unknown card on Today opens
  exactly that walk-through with its faces, ready to assign to a new or
  existing person.
- **Change connection inline**: the Frigate Connection tile edits the URL
  right there instead of routing you to the Advanced table.
- Honest feedback on whether this direction feels right is very welcome —
  suslik_dev@posteo.de.

## 0.1.0.240 — 2026-08-17

- "Change connection" on the Frigate page no longer dumps you into the whole
  Advanced table: the Connection tile opens a small form right there —
  current URL prefilled, Save & restart, Cancel. After the restart the tile
  itself shows live whether the new address answers.

## 0.1.0.239 — 2026-08-17

- Third and final shape of the unknown-visitor click, exactly as our user
  meant it: the Today card IS one walk-through, so clicking it opens exactly
  that walk — its camera chain, video and ONLY the faces collected on this
  walk (whatever internal group they landed in). Tick them, name them (new
  or existing person), done; doing nothing keeps them unknown. The full
  cross-day profile stays on the Unknown page.

## 0.1.0.238 — 2026-08-17

- The unknown visitor's page now really matches the person view: it merges
  the linked face groups of the same walks (the good pictures often sit in a
  neighbour group — 16 faces instead of 4 on the real test case), and every
  appearance card carries the big preview image on the left like a person's
  pass card.

## 0.1.0.237 — 2026-08-17

- Clicking an unknown visitor now opens the same kind of view as for known
  people: their appearances as pass cards (camera chain, face thumbnails,
  video), with one addition on top — "Who is this?": tick the faces that
  really belong to them, name them (new or existing person) and they are
  learned like everyone else.

## 0.1.0.236 — 2026-08-17

- Fix: after taking pictures, the NEXT check was slow again without saying
  why — adopting used to throw the whole reference cache away, and the next
  check rebuilt all ~300 reference embeddings inline. Taking pictures now
  slots the new embeddings into the cache directly; where a full rebuild is
  still needed (undo, deletions) the check honestly says "updating the
  reference library …", rebuilds in the background and re-runs by itself.

## 0.1.0.235 — 2026-08-17

- The pass check is fast for every pass now: it accidentally ran on a second,
  CPU-only model instance (~2 s per picture — passes with many faces took
  half a minute, passes with none answered instantly, which looked
  inconsistent). It now shares the service's accelerated instance; the
  warm-up on opening Today prepares exactly that one.

## 0.1.0.234 — 2026-08-17

- One click rule for all Today cards: clicking an unknown visitor now opens
  their profile on the Unknown page (all faces, naming, merging) — exactly
  like clicking a known person opens their day. The old inline
  assign-panel on Today is gone; assigning lives on the Unknown page.

## 0.1.0.233 — 2026-08-17

- The pass buttons got a cleaner look: consistent height and rounded corners,
  a small icon each (play for video, magnifier for the picture check, a check
  mark once pictures were taken) and a calm hover.

## 0.1.0.232 — 2026-08-17

- Smart model warm-up, designed by our user: opening Today (or a person's
  day) quietly prepares the face model in the background, so the pass check
  answers instantly; after 15 minutes without use the model is released from
  memory again (measured 379 MB — small boxes get it back). If you click a
  check while the model is still cold, the button says honestly "loading the
  recognition model — a few seconds …" and runs the check by itself once
  ready.

## 0.1.0.231 — 2026-08-17

- The pass check no longer hides borderline pictures: faces whose identity is
  sure but whose picture quality is only fair now appear in the dialog too —
  unticked, clearly labeled, tick to take anyway. The status line says
  honestly how many were kept back instead of a bare "nothing to take".

## 0.1.0.230 — 2026-08-17

- The pass check (and the automatic after-pass suggestion search) is much
  faster: the face-embedding models were rebuilt from scratch on every call
  (measured 11-13 s each time); they are now built once per service run and
  reused — a click costs the actual picture measurement only.

## 0.1.0.229 — 2026-08-17

- Rows with green-outlined pictures now say what the outline means, right
  next to the pictures: "green border = already in the references" — no
  hovering needed.

## 0.1.0.228 — 2026-08-17

- Fix: the green reference outlines from .227 did not appear — the periodic
  reference re-check rewrites metadata lines without the event link, and the
  newest line silently erased it. The event link now survives those
  rewrites (verified on the real library: 11 marked events instead of 1).

## 0.1.0.227 — 2026-08-17

- You can now SEE which pictures made it into the references: on a person's
  day view, every thumbnail whose event contributed an active reference is
  outlined green (tooltip "in the references") — immediately after taking
  pictures, permanently on every later visit, and Undo removes exactly those
  outlines again.

## 0.1.0.226 — 2026-08-17

- The pass-learning button is now two honest steps: "Check this pass for
  good pictures" runs the sieve and opens an in-page dialog showing exactly
  the pictures it would take — untick any you do not trust, then "Take N
  pictures" or Cancel. Nothing is adopted before you confirmed what you saw
  (no browser popup involved — the dialog is part of the page, so popup
  blockers cannot break it). Undo still works afterwards.

## 0.1.0.225 — 2026-08-16

- Learning where you already are: every confirmed pass on a person's day view
  got one button — "Add <name>'s faces from this pass". One click, the
  built-in check picks only clearly helpful new pictures (same identity,
  quality and novelty sieves as the reference search — a stranger's face can
  not be adopted by construction), the answer appears right there ("3
  pictures added · 2 kept back by the check"), and Undo takes them out again
  without a dialog.

## 0.1.0.224 — 2026-08-16

- Naming is now a guided card, not a document: the easy view shows "Group 2
  of 7" and one question — "Who is this?" — with the answer prepared when
  the system has a suggestion ("Yes, it's &lt;name&gt;"). One click names
  the group, adopts it into recognition and jumps to the next group; skip
  works the
  same way, and the last group says so. The full selection view (all images,
  checkboxes, per-image reasons) is the expert view, unchanged.
- Internal cluster-state words no longer leak into the interface in German
  ("unbestaetigt" → "unconfirmed").

## 0.1.0.223 — 2026-08-16

- The learning-run page is now a guided flow: a four-step bar (Collect →
  Group → Name → Adopt), one plain sentence saying where the run stands, and
  one button for the single next action — no anchor/cluster/harvest jargon
  in the easy view. The full phase chain with all counters is still there,
  one switch away in the expert view.

## 0.1.0.222 — 2026-08-16

- Areas left the main menu: the Recognition start page got a second, smaller
  tile row "Property set-up" with the Areas card (count + Manage areas), and
  the Areas sheet itself lives on as an expert tab under Configuration —
  same pattern as everywhere else, one menu entry less.

## 0.1.0.221 — 2026-08-16

- The four Faces tiles each got their "How it works" guide (same plain
  language as the recognition guides), leading back to Faces.
- Frigate page: the Connection tile has a "Change connection" button for
  both views, and the read-only "Frigate's own face recognition" tile moved
  to the expert view.
- Internal: a resident name in a code comment slipped past me again in .220
  and the privacy gate caught it; reworded. (.220 briefly ran on the in-house
  test instance despite the red gate — process slip on my side, the name
  never left the house.)

## 0.1.0.220 — 2026-08-16

- The face area is consolidated into one "Faces" start page (same tile
  pattern as Recognition and Frigate): Known people with an avatar row —
  one real face icon per person, tap it to see every reference picture —
  plus Learning as a guided three-step routine and Unknown for recurring
  visitors you have not named yet. Every tile's first sentence says WHEN
  you need it. The former People and Learn menus merge behind it: easy view
  shows the start page, expert view keeps all detail tabs; Person learn
  moved to the Person section. "How it works" guides per tile follow in a
  later step.

## 0.1.0.219 — 2026-08-16

- The AI vision card on the Recognition page now carries a visible "Beta"
  mark: this path still matures (mixed-grid handling and the per-endpoint
  calibration test are open) and users should know before they rely on it.

## 0.1.0.218 — 2026-08-16

- Internal: two code comments from .217 carried resident names; the privacy
  gate caught them before anything shipped. Reworded, no functional change.

## 0.1.0.217 — 2026-08-16

- Vision diagnosis package (V1-V3 from the lever analysis): the counters now
  see every round outcome (cut-off answers, errors and timeouts per round were
  invisible before — the store said 0 while the logs held 28 of them); a mixed
  round (one run "neither", the other picking a person) is counted as half an
  abstention instead of a positional contradiction; every run records the
  settings it actually ran with (model, thinking switch, token budget, prompt
  mark) plus each arm's visible answer text; and the candidate grid image is
  booked against the orphan cleanup the moment it is written — before, long
  runs lost exactly the evidence pictures of their hardest cases. New optional
  switch `vision_gitter_behalten` keeps no-verdict grids even in lean mode
  (default off, normal 30-day expiry still applies).

## 0.1.0.216 — 2026-08-16

- The "Frigate sync" section is now called "Frigate" and opens with a tile
  start page like Recognition: Connection (live reachability + Frigate
  version), Cameras (which ones are in use), Sync (same balance line as the
  sync page), and the live state of Frigate's own face recognition. The sync
  page itself is unchanged, one tab further (expert view).

## 0.1.0.215 — 2026-08-16

- Fix: the manual model-id check now really works. The probe request used to
  carry the standard verdict instruction ("answer A or B or NEITHER") next to
  its own "Say OK" — two contradicting orders; the model silently ruminated
  into the token cap and the check rejected working models. The probe now
  sends its question without the verdict instruction (verified against the
  live endpoint: real id passes in seconds, fake id gets a clear refusal).

## 0.1.0.214 — 2026-08-16

- Fix: the manual model-id check rejected working models. The tiny "Say OK"
  probe capped the answer at 64 tokens, but some models spend ~140 invisible
  template tokens before the first visible word (measured on Qwen3.5-9B) —
  the probe now allows 512.

## 0.1.0.213 — 2026-08-16

- Vision: you can now add a model id by hand on the Vision page — for
  endpoints that do not list every model they serve. The id is verified with
  a tiny real request first; only a model that actually answers is added to
  the list (marked "manually checked"), nothing unchecked can be saved.

## 0.1.0.212 — 2026-08-16

- The "How it works" guide links on the Recognition cards are now clearly
  visible: semibold, underlined, slightly larger — for a new user they are
  the first thing to click, and they looked like a footnote.

## 0.1.0.211 — 2026-08-16

- Vision: "thinking off" is now the default on endpoints that support the
  switch (local and custom). Reason, measured in production: on a hard
  comparison grid a thinking model talked itself past the token budget
  (47k tokens, requests over five minutes) and the pass ended without a
  verdict; with thinking off the same endpoint answers the same question
  correctly in seconds. A deliberately saved "off" stays respected, and
  the checkbox on the Vision page now shows the value that is actually
  sent.

## 0.1.0.210 — 2026-08-16

- The top navigation section is now called **Configuration** instead of
  Settings (all addresses unchanged).
- The Recognition page warns before you leave it with unsaved body or
  vision changes (browser dialog); the Live switch is exempt because it
  applies immediately.

## 0.1.0.209 — 2026-08-16

- Guide polish after the first read-through: the "Is it for you?" closers
  are gone, and the Face guide now says clearly that suslik alerts on its
  own channels (Pushover, Telegram, MQTT) when a face is recognized or an
  unknown one shows up — completely independent of Frigate, which needs no
  notification setup at all.

## 0.1.0.208 — 2026-08-16

- **Every Recognition card now carries a built-in guide** ("How it works …"):
  plain-language pages inside suslik, no GitHub needed. Each guide has two
  depths and follows the Easy/Expert switch: Easy readers get what the way
  does, what it costs and whether it is for them; Expert adds how the
  verdict forms, written for an interested user, not an engineer.
- **Register buttons per card**: Live and Face carry "Register face" (both
  use the same face library), Body "Register body", AI vision "Register
  vision" (jumps straight to the galleries). Each button leads into the
  existing flow of its own method — registering never drags you through
  methods you switched off. No photo upload, by design: the system learns
  from your cameras; Frigate import remains the supplementary source.
- Today's "Recognized" row now says honestly when a pass is still in
  progress ("events are analyzed as they finish and show up here") instead
  of looking empty for the minute or two the normal path needs after the
  live alert. The page already refreshes itself while a pass is running.

## 0.1.0.207 — 2026-08-16

- **The Recognition page is now the front door of Settings**: clicking
  "Settings" in the top navigation lands directly on the four pillars. In
  Easy mode it is the whole configuration view — the sub-tabs (Cameras,
  Notifications, Recognition chain, Advanced) appear in Expert mode; they
  are only hidden, never locked, and stay reachable by URL.
- Fixes the Face card claiming "0 people · 0 reference images": the counter
  looked in the wrong folder; it now counts the real reference library.

## 0.1.0.206 — 2026-08-15

- Fixes the new Recognition page crashing on load (0.1.0.205 was on the
  production box for minutes and never published): the watcher summary read
  the guard store with the wrong shape. The QA gate gained a new stage that
  starts the built image data-free and fetches EVERY navigation page over
  HTTP — the class "page renders in review but crashes in the image" cannot
  pass silently again.

## 0.1.0.205 — 2026-08-15

- **New "Recognition" settings page: four pillars, one per recognition
  method** (Live watch, Face, Body, AI vision). Each card leads with an
  enable/disable toggle so you decide per method what runs, followed by a
  plain-language sentence, the honest current state and one setup button.
  The Live toggle acts immediately (it starts/stops the set-up watchers
  through the same per-camera gate as the Live tab); body and vision
  changes apply with Save + restart — the same audited settings as the
  Recognition-chain page, one value shown in one more place. Face has no
  off switch today (it is the backbone the other methods hang off) and
  the card says so instead of faking one.
- The page is the first to use the Easy/Expert switch: both modes see the
  four cards, Expert additionally shows status details and deep links.

## 0.1.0.204 — 2026-08-15

- **New Easy/Expert switch in the header** (left of the Live indicator, styled
  like the Theme button): a two-segment pill showing both modes with the
  active one highlighted. For now it is just the switch — the choice is
  remembered per browser (like the theme choice) and pages will adopt their
  simplified Easy views step by step in the coming versions. Nothing is ever
  deleted; Easy only hides.

## 0.1.0.203 — 2026-08-15

Body recognition gets a new, measurably better and properly licensed model:

- **The person path now runs on Intel's OMZ person-reidentification-retail-0277**
  (Apache-2.0 including the model file) instead of DINOv2. Measured on the
  frozen benchmark: 32/30/30 of 37 scenarios across three seed sets vs
  18/16/16 before, max confusion probability 0.20 vs 0.89, and it passes
  the real hard-case walk the old candidate failed. An A/B on fresh
  out-of-sample walks fired 6/12 scenarios vs 3/12.
- **Existing installations migrate themselves**: on the first start after
  the update the service re-trains the person model once in the background
  from the stored, reviewed images (seconds to a few minutes on small
  CPUs); until then the old model keeps judging. A failure is shown on the
  model card, never silent.
- New setting `person_backend` (default `cpu`): compute placement of the
  embedding model. Measured on the reference box: 18.8 ms/image on CPU,
  3.2 ms on the iGPU, 3.6 ms on the NPU — the path is dominated by video
  decode, so CPU stays the default; move it only after measuring, an extra
  GPU context can starve the live watchers.
- The whitening step (PCA, fitted per training fold) ships inside the
  stored model; threshold calibration is unchanged in method and now lands
  at ~0.74 on the reference data.

## 0.1.0.202 — 2026-08-15

Memory fix — the important one. On 2026-08-15 our own production box went
down five times; the measured root cause applies to every installation:

- **Body recognition now runs in its own supervised process** ("personwork")
  instead of unbounded threads inside the main service. A burst of events
  used to spawn one heavy 4K-decode thread each (a 41-event re-analysis
  ate +1.2 GB in 30 s and froze the whole container); now they queue and
  run one at a time, live verdicts take priority over batch work.
- **The RAM budget guard from 0.1.0.172 finally applies to the body path.**
  It existed, but the body path silently skipped it; that skip is now a
  loud error, and a QA-gate check keeps it from ever coming back. Large
  events degrade their sampling instead of exhausting memory (median
  events are unaffected).
- The person-learn harvest goes through the same supervised process
  (it was the second unbounded door).
- A vision-request thread could outlive its deadline holding the full
  request body; it now discards late responses immediately.
- Image sharpness/height are computed once when a judged image is stored,
  instead of re-decoding every image of a pass on every vision run and
  page view.
- New setting `personwork_rss_max_mb` (default 3072) caps the body process.

Next up: a simpler Easy mode (with an Expert mode keeping every control).
Feedback is very welcome: suslik_dev@posteo.de.

## 0.1.0.201 — 2026-08-14

- Removes the "UI address" field and the push-message link again that
  0.1.0.200 had introduced (that version was never published): no real user
  ever asked for it, and suslik is deliberately not reachable from the
  internet, so the link would only ever work on the home network.

## 0.1.0.200 — 2026-08-14

Fix round from a full user's-eye review of all 31 pages:

- **Advanced settings page was unsaveable on a fresh installation**: four
  whitelist keys had no code default, two of them rendered the literal
  string "None" and any save of the whole page failed with HTTP 400. All
  four now carry their code default; this also removes a silent trap where
  the daily update check showed "off" on fresh installs while actually
  running.
- **Alert categories now govern every channel** as the Notifications page
  always claimed: Telegram scene messages and the MQTT scene topics
  (szene_erkannt/szene_unbekannt) respect the category checkboxes; the
  factory default has the matching categories ticked, so unchanged
  installations behave exactly as before. The MQTT data topics (erkennung,
  heartbeat) keep publishing unfiltered.
- **New live watchers no longer default to Pushover blindly**: the channel
  preselection comes from the channels you actually configured; a watcher
  whose channel list ends up empty says so loudly in the log.
- **Push messages can carry a link back into suslik**: set the new "UI
  address" field on the Notifications page and Pushover alerts get an
  "Open in suslik" link to the event, live-alerts or System page. Blank
  keeps the old behavior.
- **Stale texts corrected**: the learning-run, anchors and person-learn
  pages claimed naming/adoption/training would "ship in the next updates"
  although all of it works in this build; the System page now really has
  the "Re-run setup wizard" link and a Backend lamp confirming the
  accelerator self-check, as the setup wizard always promised.
- **Live alerts** is now in the navigation (Live section) instead of being
  reachable only through the Today sidebar.

## 0.1.0.199 — 2026-08-13

Release bundling the internal steps 0.1.0.184–0.1.0.198 (they were never
pushed to GHCR; see the individual entries below for details). Highlights:

- Live watchers now include a preliminary **name stage** on every enabled
  watcher: continuous per-frame voting fires "recognized (live,
  preliminary): NAME" seconds after the trigger, with a proof picture;
  several people in the same pass are reported individually.
- **Appearance view**: the live-alerts day view bundles each pass into one
  card with all stored face pictures and recap videos; Today's "Recognized
  live" cards link straight to it.
- **Per-camera processing resolution** (360p–2160p, default 1080p).
- **Simpler capacity model**: enabled means running — the predictive GPU
  budget that could refuse watchers is gone; overload is handled by the
  runtime sampling throttle. The source test measures the camera's real
  delivery rate.
- Live tab: agent-eye preview, real stream resolution, state/area grouping,
  per-tile hide; recognition chain as its own settings page.

## 0.1.0.198 — 2026-08-13

- Fixes a 0.1.0.197 startup crash of the live engine (a leftover reader of
  the removed quick-verdict field; the engine died three times and paused).
  References for the name stage now load whenever any watcher is enabled,
  and the QA gate got a new drift check that runs the engine-start
  predicates against normalized watcher configs.

## 0.1.0.197 — 2026-08-13

- The per-camera "quick verdict" toggle is gone: every enabled watcher now
  includes the preliminary name stage (it costs microseconds since the
  continuous voting — the toggle only caused confusion; a real pass was
  missed because the switch had silently flipped off).
- Watcher save API: fields missing from a save request now keep their
  stored values instead of silently resetting to defaults — exactly the
  bug that flipped the toggle above.

## 0.1.0.196 — 2026-08-13

- Watcher slots simplified: an enabled watcher now always runs. The
  GPU-budget prediction that could refuse a slot based on estimated
  numbers (and judged the same setup differently depending on start order
  and restart state) is gone — overload is handled at runtime by the
  existing sampling throttle, visible in the status. The only remaining
  guards are the hard cap (5 watchers) and the measured RAM floor.
- The source test now measures the camera's real delivery rate (frames
  after the initial buffer burst) instead of decode throughput — the old
  number could read several times the true frame rate; old test results
  are marked "throughput, not delivery rate" until rerun.

## 0.1.0.195 — 2026-08-13

- Live alerts day view now shows **appearances** instead of single triggers:
  triggers of the same camera within 30 s form one card carrying ALL stored
  face crops (including karenz triggers that never sent an alert) plus the
  recap videos — consistent with the pass view under Recognized. The
  "Recognized live" cards on Today link straight to their appearance card.
- Capacity check fix: a watcher slot candidate is now budgeted with the
  **measured delivery rate** (from "Measure load", anchored to the exact
  source) instead of the source-test throughput, which read several times
  the real frame rate and could refuse a slot that actually fits.

## 0.1.0.194 — 2026-08-13

- Live watchers: per-camera processing resolution (360p / 720p / 1080p /
  1440p / 2160p) on the watcher's configure page. Default is now 1080p —
  measured on a reference walk it fires the preliminary name ~2.4 s earlier
  than 720p; the detection net stays the same size, so the extra cost is
  decode/scaling (use Measure load for your hardware's real numbers).
  Changing the resolution invalidates the source test, honestly.
- Today / Live alerts: clicking a recognized-live card's picture opens the
  full-size proof image.

## 0.1.0.193 — 2026-08-13

- Live watchers: continuous name voting. Every processed face is now matched
  against the reference library across the WHOLE appearance (the embedding is
  already computed by the detector, so this costs a microseconds-range
  nearest-neighbour lookup, not a second model run). After 2 consistent
  hits above the recognition threshold for the same person, a second,
  clearly preliminary "recognized: <name>" message fires — once per
  appearance and person, independent of the instant presence alert. Fixes
  the structural miss where the name was only judged on the 4 trigger-moment
  frames (typically the farthest/worst faces of a walk).

## 0.1.0.192 — 2026-08-13

- New "Live alerts" day view: clicking the live-alert counter on Today opens
  all of that day's triggers with proof picture, name or "unknown", exact
  time, camera and channels — the unknown faces the Recognized-live row
  deliberately hides.

## 0.1.0.191 — 2026-08-13

- Today: the "Recognized live" row now shows only triggers where the quick
  check actually recognized someone — unknown triggers no longer flood the
  row (they stay in the live-alert counter and on the Live tab). The label
  says honestly how many of the day's triggers were recognized.

## 0.1.0.190 — 2026-08-13

- Today: live triggers now show as a "Recognized live" card row right under
  Recognized — proof picture, the quick-check name (or "unknown"), time and
  camera, honestly labeled "quick check, preliminary" (a live trigger is not
  the confirmed verdict). Replaces the plain text list from 0.1.0.188. The
  alert log now records the person and the proof-picture path; older entries
  render without a picture. The MQTT payload's quick-verdict block also
  carries the person as its own field now.

## 0.1.0.189 — 2026-08-13

- Settings: "Recognition chain" is now its own menu item (Cameras ·
  Notifications · Recognition chain · Advanced) with its own save button,
  instead of a section inside Advanced.

## 0.1.0.188 — 2026-08-13

- Today: live-watcher alerts now show as their own list next to the day
  counters — one row per trigger (time, camera, the alert text such as
  "probably …", and the channels it went out on). The engine's alert log
  now records the alert text, so rows from before this version show
  time and camera only.

## 0.1.0.187 — 2026-08-13

- Settings: new "Recognition chain" section — the chain Face → Person →
  Vision rendered in its real order, with per-step condition (always / only
  when the face path could not confirm everyone / off), an honest status line
  (configured vs. actually armed, same source as /health), and a cost hint
  per step. Replaces the two bare dropdown rows in the parameter table;
  changing the order itself is a later stage.

## 0.1.0.186 — 2026-08-13

- Live tab: tiles are grouped by state — Running (including disturbed ones,
  those never hide), Ready, and a collapsed "Not set up" section — instead of
  one wall of equal tiles. Cameras that will never be watchers can be hidden
  per tile; hidden ones live in a collapsed "Hidden" section at the bottom.
- Live tab: the service now probes every camera's real stream once at startup
  (background, cached), so tile headers show the true stream resolution
  without running a source test first.
- Live tab: optional "group by area" view using your camera areas.

## 0.1.0.185 — 2026-08-13

- Live tab: active watcher tiles now show a preview image straight from the
  watcher itself — the processed frame the engine actually analyzes (720p
  watcher scale), refreshed every ~2 seconds. You see what the watcher sees,
  not Frigate's picture.
- Live tab: the tile header now shows the camera's real stream resolution
  (from the source test) instead of Frigate's small detect-substream size,
  which made 4K cameras look like 800×600 webcams. Without a source test the
  detect size is still shown, honestly labeled "(detect)".

## 0.1.0.184 — 2026-08-13

- The service now forces umask 022 for itself and every child process, so
  all files written to the data volume are readable from the host (running
  as root in the container, learning-run references and state files were
  written as 600 and silently missing from host-side backups).

## 0.1.0.183 — 2026-08-13

- Privacy respin of 0.1.0.182 (which was public for under an hour and is
  withdrawn): the author's camera names appeared in code comments inside the
  shipped images. Comments anonymized, and the image privacy audit gained a
  dedicated stage that scans every image for camera names before publishing.
  No functional changes.

## 0.1.0.182 — 2026-08-13

- Live watcher sources: a custom stream URL (source "url") no longer fails for
  non-RTSP inputs — the RTSP transport flag was passed to ffmpeg
  unconditionally, so file/http sources were refused outright ("Option not
  found"), including the software fallback. Found during the CUDA real test.
- NVDEC live decoding confirmed on real NVIDIA hardware: watcher start line
  shows "HW-Decode (nvdec)" on an RTX 2060 (driver 550) against a live
  go2rtc restream, detector at 43 ms/frame.

## 0.1.0.181 — 2026-08-13

- Live watchers pick their video decoder by hardware: VAAPI on Intel/AMD
  (unchanged), NVDEC on NVIDIA cards (previously the live reader was
  VAAPI-only and fell back to software decoding on NVIDIA). The chosen mode
  is logged in the watcher's start line; if the hardware pipe fails, the
  loud software fallback remains.

## 0.1.0.180 — 2026-08-12

- Live watchers now start themselves: the service launches and supervises the
  watcher engine as its own process — restart with backoff on failure, a loud
  alert instead of a crash loop, clean shutdown with the service. A manually
  started engine is detected and never doubled.
- Live watcher alerts are counted on Today and System (per channel, with the
  channels you actually use), backed by a restart-proof log.
- The pose-gate model now ships inside every image variant (no manual staging
  step), and a new QA stage guards the live path on built images.
- Robustness: a corrupted unknown-pool line can no longer break the Today,
  Unknown or Appearances pages — one tolerant reader everywhere.
