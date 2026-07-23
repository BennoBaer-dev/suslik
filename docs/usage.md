# Usage

Once suslik is running and the wizard is done, everything happens through the web UI at
`http://<host>:8199/` and, in the background, automatically as Frigate produces person events.

## The web UI

- **Today** — the scenario view. Each entry is one *walk* (a person moving across your property),
  grouped from the individual events across cameras and time. You see who was recognized, or
  "unknown", per scenario. A scenario still in progress is shown live and finalizes once the walk
  ends. Click a person chip (or "unknown") to open the event detail page with all face crops, the
  judgment, and the clip.
- **Events** — the flat event list with filters and paging, category badges, ground-truth
  buttons, and video links. Useful for drilling into a single event.
- **Faces** — your reference library (the "master"): the people suslik knows and their reference
  images.
- **Unknown** — persistent unknown identities: recurring faces that aren't in your library yet,
  grouped over time so you can promote one to a known person.
- **Enroll** — enrollment suggestions. suslik proposes reference faces to add for known people
  after each walk; **"Apply all recommended"** accepts all suggested faces at once. Applying stays
  a manual click (a safeguard against poisoning the library with bad crops).
- **Quality / Review** — library-quality reports and review galleries.
- **Cameras** — the cameras from Frigate, with the zone condition as a checkbox per camera.
- **Settings** — configuration and a clean restart; also **Re-run setup**.
- **System** — the status "traffic light", the reference-sync status, a QC report, and a link to
  this documentation.

## Enrollment (teaching suslik a person)

suslik learns from your own camera footage — you don't upload photos. The flow is
person-centric:

1. Let the person appear on camera normally. After each walk, suslik generates enrollment
   suggestions (**Enroll** tab) for people it already knows, and clusters faces it doesn't
   recognize into the **Unknown** tab.
2. To add a **new** person, promote an unknown cluster to a name, then let suslik gather more
   reference faces of them from subsequent appearances.
3. Review the suggested faces and apply the good ones. Only clear, unambiguous faces make good
   references — suslik's suggestions are filtered, but the final accept is yours.

A recurring background job keeps the unknown pool tidy and re-checks it against your current
references.

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
