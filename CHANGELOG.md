# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.111 (2026-11-23)

Test release. Person recognition stays a preview.

- New page **Person → Named persons**: the people who got a body name in the last three days (at least `koerper_stimmen` votes on one pass), plus body names suslik wrote to Frigate. One row per person, newest picture on the left, at most twelve. Each picture is the one the comparison used and opens its event; date and time below it, camera, score, threshold and votes on hover.
- Every event whose body comparison names a person now keeps the compared picture in its event folder (`koerper_treffer.png`), removed with the folder after `aufbewahrung_tage` days. Names from before this version have no picture; the page only counts them.
- A wrong name is fixed with the small ✕ below its picture: choose the correct person, "stranger" or "don't know", then **Save**. The event loses its body name for good, on every page, and the log notes the correction without names. If suslik wrote the name to Frigate, it removes it there or puts in the person you chose; a chosen person is saved as your verdict for the event.
- A correction can't be undone on the page. Notifications already sent and presence marks stay, and the event never gets a body name again, not even the right one.
- **Recognition** page: the switch **Accept new images automatically** is now on the body card below **Start learning run**. Both are set only there (and on **Advanced**). The **Body images** page has no settings and no save button any more; its footer shows the current setting with a link to **Recognition**.
- Live watchers: fields that earlier versions left in saved watchers are removed once at the first start, with one line in the log. The warning "… was removed in an earlier version" then no longer shows up.

## 0.1.1.110 (2026-11-22)

Test release. 0.1.1.104 to 0.1.1.109 were never published; their changes are part of this version.

- Person recognition (preview) is rebuilt and optional. It learns body images per person from videos in which the face path recognized exactly that person. An event without a recognized face and with exactly one person then counts as a vote when its body picture is close enough to one of them; by default a name counts when one pass gives the same person three votes (`koerper_stimmen`). Details: `docs/person-recognition.md` and the chapter Person recognition in Read me first.
- Only videos analyzed with this version can give body images; older videos don't count. The path does nothing until there is at least one valid body image.
- New page **Person → Body images**: start the learning run, choose how many videos per person to check, accept or discard new images (by default only images you accept count) and see the stock per person. `koerper_lauf` sets when the run starts: `hand` (by the button, the default), `taeglich` (once a day with the maintenance at 06:00) or `sofort` (right after each suitable video).
- A body name is shown on **Today**, **Passes** and **Appearances**. Five switches, all off by default, let it go further: `koerper_meldet_frigate` (sub label, needs `sub_label_schreiben`), `koerper_meldet_pushover`, `koerper_meldet_telegram`, `koerper_meldet_ha` (MQTT topic `koerper_erkannt`) and `koerper_meldet_anwesenheit` (marks on the **Presence** page and in the hour bar on **Today**, nothing sent outside). Pushover, Telegram and Home Assistant send at most once per pass and person, and stay silent when the face path confirmed the same person within `anwesenheit_cooldown`.
- **Recognition** page: the body card shows these switches and the choice **Start learning run** directly. The save button is now a bar at the bottom of the page, grey with "All saved" until you change something, then highlighted with "Not saved, saving restarts the service".
- New settings, all on the **Advanced** page: `koerper_auswahl_stimmen` (6), `koerper_bilder_je_video` (3), `koerper_anker_min` (0.5), `koerper_sichtpruefung` (on), `koerper_lauf` (`hand`), `koerper_max_tage` (10), `koerper_max_je_person` (50), `koerper_schwelle` (0.65), `koerper_marge` (0.02), `koerper_stimmen` (3) and the five switches above (off). None of the defaults is measured on more than one system; see `docs/configuration.md`.
- The old person-learn run is removed: its pages, its model and training pictures, the alerts with the note "person recognition, not face" and the MQTT message `person_erkennung`. The learned faces stay. If you used it, person recognition has to learn again. The maintenance step "data cleanup" moves the folder `personlern/` into the trash, which is emptied 7 days later.
- Vision detect is parked: it is switched off and cannot be switched on in this version, a saved "on" is set to off once at the first start, and the Vision pages say why.
- Telegram: with `telegram_modus` set to `aus` (off, the default), nothing is sent over Telegram any more, including fault messages and the messages and videos of the live watchers. The channel test on the page still works.
- Body images live in `refquelle/koerperbilder/` in the data folder and are part of the full backup and of `/support/faces`; the support area `/support/personlern` is gone. The images no longer carry the DINOv2 model file.

## 0.1.1.103 (2026-11-18)

- Accelerator images (cuda, gpu, gpu-legacy, rocm) no longer report OK when their GPU or NPU is not working at startup: the startup log shows FAIL, `/health` reports `ok: false`, every page shows a red line in the header, and the System page gives cause and fix under the Backend tile.
- cuda: the startup log now names the exact case and lists what arrives in the container.
- Docs: the Compose example for NVIDIA now names only `capabilities: [gpu]`. With `video` added, `nvidia-smi` was missing in the container; if you copied the old example, remove `video`.
- System page: the Analysis tile turns red when the last analysis has failed.

## 0.1.1.102 (2026-11-16)

- Event clips: suslik now waits until Frigate has stored the recording up to the end of an event before it fetches the clip, so the end is no longer cut off by fetching too early. Thanks for the report in #40.
- The setting `clip_delay` was removed.
- New setting `clip_aufnahme_deckel_s` (factory value 20 s, 5 to 120 s): the longest time suslik waits for the recording.

## 0.1.1.101 (2026-11-11)

Test release. 0.1.1.058 was never published; its changes are part of this version.

- Today: the page now shows only cards, in three bands (Recognized, Probably recognized, Unknown), each card with its action. The list of passes and the numbers of the day moved to the new tab Passes. Card pictures are sent scaled down.
- Unknown people seen by a live watcher on Today: an appearance that a live watcher judges as an unknown person gets a card in the Unknown band, whatever channel the watcher reports on. The card opens the live alert. It has no identity and cannot be named there.
- Live watchers page: one page with slots replaces the tile overview and the separate settings page. A camera is assigned to a slot; below the slot bar are the settings of the selected slot: Push messages (a table with all nine push switches), Home Assistant (MQTT), Visit, Frigate (optional), and the folded sections Advanced and Diagnostics. "End after no face" is now "Visit ends after" and "Re-armed after" is now "Push pause"; the saved values are unchanged. The counter in the head reads "reported" instead of "alerts".
- Second look: a face that resembles nobody known must be found a second time by the detector before it counts as an unknown person. This keeps leaves, bushes and similar things out of the alerts and the unknown pool. Checked on Intel GPU and CPU, untested on AMD.
- The calibration samples of a live watcher keep all filter values.
- New setting `vorlauf_timeout_s` (factory value 60 s, 10 to 300 s): how long the service waits for the connection when it fetches a clip.
- Live watcher MQTT: every message has the field event, faces_recognized and appearance_ended are new. MQTT no longer waits for image, video or push, and "Push pause" no longer holds it back. Old fields are unchanged. Details in Read me first.
- Live watcher on Pushover and Telegram: the first face is no longer reported there. Known people come right away with name and a small picture, unknown people once the appearance is over, and Telegram gets one video per reported appearance. Each message type has its own switch per watcher, and "Push pause" now starts at the first face of a reported appearance.
- NVIDIA under Windows with Docker Desktop (WSL 2): the cuda image now detects the card without the device nodes /dev/nvidia*, so recognition, decoding and display videos run on the GPU there. Not yet verified on our own hardware. Thanks for the report in #37.
- Live alerts: the video of an appearance now also plays in Safari.
