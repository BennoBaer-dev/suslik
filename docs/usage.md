# Usage

Once suslik is running and the wizard is done, everything happens through the web UI at
`http://<host>:8199/` and, in the background, automatically as Frigate produces person events.

## The web UI

The UI is organized into **four sections** (top bar) with a second row of tabs underneath:
**Activity**, **People**, **Settings** and **System**. All routes are stable — bookmarks keep
working. The UI follows your operating system's light/dark preference; the **Theme** button
(top right) overrides it permanently. On *Today* you can page back through past days.

**Activity**

- **Today** — the scenario view. Each entry is one *walk* (a person moving across your property),
  grouped from the individual events across cameras and time. Recognized people lead the page;
  passes where nobody was recognized appear as "Unknown N" cards once the unknown pool has
  grouped them (with how often that identity was seen before). A scenario still in progress is
  shown live and finalizes once the walk ends.
- **Events** — the flat event list with filters and paging, category badges, ground-truth
  buttons, and video links. Useful for drilling into a single event.
- **To label** — the work list of unconfirmed events (route `/offen`, 50 per page): events that
  have a usable face but aren't ground-truth confirmed yet, so you can label them one by one.

**People**

- **Known** — your reference library (the "master"): the people suslik knows and their reference
  images. Also where you can upload photos to bootstrap a person.
- **Unknown** — persistent unknown identities: recurring faces that aren't in your library yet,
  grouped over time so you can promote one to a known person.
- **Suggestions** — enrollment suggestions. suslik proposes reference faces to add for known
  people after each walk; **"Apply all recommended"** accepts all suggested faces at once.
  Applying stays a manual click (a safeguard against poisoning the library with bad crops).
- **Quality** — reference-library quality reports (finding no-face, mislabeled, or confusable
  references so you can clean the master up).

**Settings**

- **Cameras** — the cameras from Frigate, with the zone condition as a checkbox per camera.
- **Notifications** — configure the alert channels (Pushover, Telegram, MQTT) and pick which
  judgment categories raise an alert. For Telegram you can choose the attachment: a short
  **video** clip (falls back to an image and says so) or **image only** (no transcoding —
  lighter on weak hardware). Each channel has a **Test** button; stored secrets are shown masked.
- **Advanced** — the remaining configuration values and a clean restart.

**System**

- **System** — the status "traffic light", the reference-sync status, a QC report, the
  **configuration backup/restore** card, the **Frigate write-back** control (read-only is the
  safe default), **Re-run setup wizard**, and a link to this documentation.

## Enrollment (teaching suslik a person)

suslik learns from your own camera footage — you don't upload photos. The flow is
person-centric:

1. Let the person appear on camera normally. After each walk, suslik collects the best faces
   (up to three per event), generates enrollment suggestions (**Enroll** tab) for people it
   already knows, and clusters faces it doesn't recognize into the **Unknown** tab.
2. To add a **new** person, the shortest path is the **Today page**: an *Unknown* card shows a
   sample face and is clickable — the panel that opens lets you pick exactly the faces you want
   (walkthrough faces first) and assign them to a new or existing name. Alternatively, promote a
   whole unknown cluster to a name on the **Unknown** tab.
3. Review the suggested faces and apply the good ones. Only clear, unambiguous faces make good
   references — suslik's suggestions are filtered, but the final accept is yours.

On the **Unknown** tab, *"same person?"* rows show faces of both identities so you can answer
**Merge** or **Different** at a glance; *Different* is remembered permanently. Clusters that turn
out to be static objects (a wheel arch, a light pattern the face detector keeps firing on) are
quarantined automatically into their own collapsed bucket. A person can also be **deleted
entirely** (name + references) from their detail page; the data moves to a recoverable trash
folder.

A recurring background job keeps the unknown pool tidy and re-checks it against your current
references. On an **event page**, images are grouped per person, and groups whose best match is
below the "unknown" threshold sit under a visible divider — *weak matches, the name is a guess*.

## How a judgment is reached

For each person event, suslik pulls the recorded clip, searches across frames for the best face,
and matches it against your references over time. It reports one of:

- **recognized** — a known person confirmed by enough consistent frames.
- **unknown** — a face was seen but didn't match any reference confidently.
- **disagreement** — suslik confirms a *different* person than Frigate's label (the case suslik
  exists to catch).
- (plus bookkeeping categories for "Frigate labeled but no usable face", "both unknown", etc.)

Alerts fire only for the categories you enable (disagreement by default), with a global cooldown
so continuous presence doesn't spam you.

## Reading the startup self-check

If something looks wrong, the container log is the fastest diagnosis:

```bash
docker logs -f suslik
```

The service prints a 7-step self-check on start: config, hardware (which accelerator was found
and whether it engaged), backend bind, recognition model, Frigate connection, references, and a
per-backend benchmark — ending in `========== ready ==========`. It contains no secrets, so it's
safe to share when asking for help.

Next: [architecture.md](architecture.md) · [hardware-acceleration.md](hardware-acceleration.md)
