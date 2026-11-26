# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.116 (2026-11-26)

Test release. Person recognition stays a preview.

- **Stranger alert** (`fremd_verdacht`): suslik now raises it only when a face at least 100 pixels wide also passes the recognition checks (head pose, image quality, second look). Until now any detection not marked as a false detection was enough, so grass, leaves or the back of a head could trigger the alert. A stranger whose face is only seen turned away or blurred no longer triggers it.

## 0.1.1.115 (2026-11-26)

Test release. Person recognition stays a preview.

- **Important, retention:** suslik now keeps its own event data for 14 days by default instead of 60 (`aufbewahrung_tage`). At the first start of this version, every installation without its own value deletes event folders without ground truth that are older than 14 days for good; the monthly archive of the event record, the pieces of the unknown queue and the log of names written to Frigate go to the trash after 14 days. You now set the value on the **Advanced** page (whole days from 1); folders deleted at the first start do not come back.
- **Person recognition:** the body check now compares every frame along a person's track (three per second, between the first and the last point Frigate has for them) instead of at most three images, so it names the person more often.
- **Settings:** every settings page has the same save bar; it shows whether something is unsaved and warns before you leave the page with unsaved changes. You can now set the body threshold right in the **Body recognition** card on the **Recognition** page. On **Body images**, images that are too similar to another person have a red frame, and a link leads to the threshold.
- **Small fixes from reported issues** (pull request #46): when Pushover rejects a message, the log, the pause notice and the channel test now show Pushover's own reason (for example "application token is invalid") instead of only "HTTP Error 400". When the hardware decoder of a live watcher delivers no frame, suslik falls back to decoding on the CPU and says so, instead of failing the source test.

## 0.1.1.113 (2026-11-24)

Test release. Person recognition stays a preview.

- **Cameras** and the setup wizard: **use this camera** is now saved the way you set it, also for a camera that is off in Frigate. Until now such a camera was always saved as used, and the page still said "saved". A camera without a saved choice starts ticked.
- A camera you untick is now off completely: suslik fetches and checks nothing from it, not even events that Frigate gave a name (until now those were checked, with notifications and presence). So a wrong name from Frigate on such a camera is no longer checked. The **Cameras** page says this in its intro, and the tick box sits at the same place on every card.
- Person recognition: the body threshold is now fixed at `koerper_schwelle` (default 0.65), the same for everyone. Until now suslik raised it on its own above the most similar pair of two people, so a single pair made it stricter for all. `koerper_marge` is gone; the help texts of `koerper_schwelle` and `koerper_stimmen` are new.
- A person whose images reach the threshold against another person's images is switched off: they get no body name, and neither does an event with an image that matches them above the threshold. Their images are still learned.
- **Body images**: a switched-off person has a red ring and a red line naming the similar person, the value and the threshold. A threshold above that value switches them back on, but stricter for everyone.

## 0.1.1.112 (2026-11-23)

Test release. Person recognition stays a preview.

- Person recognition now starts whenever the tracked person of an event got no face name, no matter how many people the video shows. Until now it needed a video with exactly one person.
- A body name now also counts next to a face name on the same walk-through once the person has `koerper_stimmen` votes (default 3). The walk-through then shows both names, and the body name goes to presence, notifications and Frigate like any other. Until now it did not count next to a face that names someone else.
- A body name that a face in the same video already confirmed is not used.
- With `person_pfad` on `nur_wenn_gesicht_leer`, an event is always checked when the video shows several people and the tracked person got no face name.

## 0.1.1.111 (2026-11-23)

Test release. Person recognition stays a preview.

- New page **Person → Named persons**: the people who got a body name in the last three days (at least `koerper_stimmen` votes on one pass), plus body names suslik wrote to Frigate. One row per person, newest picture on the left, at most twelve. Each picture is the one the comparison used and opens its event; date and time below it, camera, score, threshold and votes on hover.
- Every event whose body comparison names a person now keeps the compared picture in its event folder (`koerper_treffer.png`), removed with the folder after `aufbewahrung_tage` days. Names from before this version have no picture; the page only counts them.
- A wrong name is fixed with the small ✕ below its picture: choose the correct person, "stranger" or "don't know", then **Save**. The event loses its body name for good, on every page, and the log notes the correction without names. If suslik wrote the name to Frigate, it removes it there or puts in the person you chose; a chosen person is saved as your verdict for the event.
- A correction can't be undone on the page. Notifications already sent and presence marks stay, and the event never gets a body name again, not even the right one.
- **Recognition** page: the switch **Accept new images automatically** is now on the body card below **Start learning run**. Both are set only there (and on **Advanced**). The **Body images** page has no settings and no save button any more; its footer shows the current setting with a link to **Recognition**.
- Live watchers: fields that earlier versions left in saved watchers are removed once at the first start, with one line in the log. The warning "… was removed in an earlier version" then no longer shows up.
