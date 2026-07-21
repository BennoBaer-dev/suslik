# suslik

*A suslik is a ground squirrel that stands sentinel, watches the surroundings, and warns its colony
of danger.*

A small companion service for [Frigate](https://github.com/blakeblackshear/frigate) that treats a
person's walk across your property as **one scenario across multiple cameras**, and only calls a
face "recognized" after **several consistent hits**, not a single lucky frame.

> **Status: it works, it just isn't packaged for anyone else yet.** The recognition runs on my own
> cameras every day and does its job well. What's missing before you can run it is the packaging (a
> Docker image you bring your own reference photos to) and testing on hardware that isn't mine. Code
> and a Docker image aren't here yet; this page is where that's being prepared. See [Roadmap](#roadmap).
> (Built for a German homelab; the web UI is in English.)

## Why this exists

Frigate's built-in face recognition decides per camera and per event, often from a single frame.
On my own setup that got things wrong often enough to be annoying: the wrong name on a delivery
driver, a family member flagged as unknown, a stranger quietly matched to someone in my reference
library.

Rather than replace Frigate's recognition, `suslik` runs *next to* it and double-checks.
It doesn't change anything inside Frigate. It reads Frigate's events and recordings over the API and
MQTT, looks at them with a stronger model and a stricter rule, and forms its own opinion. Where the
two disagree, that disagreement is the interesting signal.

## The idea

- **The pass, not the frame.** When someone walks from the driveway to the front door, that's
  several events to Frigate but **one scenario** here. The service groups the events of a single pass
  by time so you see the whole pass together, across all the cameras it touched, instead of judging
  any one camera in isolation.
- **No single-frame trust.** Recognition needs more than one lucky frame (see [How it works](#how-it-works)).
- **Measured, not guessed.** The recognition model (AdaFace) was chosen by measuring it against two
  common alternatives (InsightFace's buffalo_l / ArcFace pack and LVFace) on hand-labeled events,
  not by gut feeling. Thresholds were calibrated the same way.
- **Local.** Everything runs on the same box as Frigate, on an Intel iGPU or NPU. No cloud, no
  dedicated GPU.

## What works today

This is what actually runs today, not a wish list:

- **Scenario view across cameras.** The events of one pass are grouped by time and shown as a single
  scenario you can open per camera, so the day reads as a handful of passes instead of a flood of
  separate events. Within a scenario, the best face for each person is picked across all the cameras
  of that pass.
- **Multi-hit confirmation.** Someone counts as recognized only after several consistent frames,
  calibrated on labeled recordings (the exact rule is under [How it works](#how-it-works)).
- **A "who is this?" review flow.** Events with a face that nobody has confirmed yet surface
  automatically, so labeling them is a short evening task instead of digging through history.
- **Reference-library hygiene.** The UI spots reference images that are unusable (no detectable
  face, too small, too blurry) or that are confusably similar to a *different* person, and helps you
  remove them. It also proposes good new reference images from appearances where the person was
  already confidently recognized.
- **Persistent unknown clustering.** Repeated unknown faces are grouped by similarity and kept
  across days, so a recurring visitor becomes one identity you can name once, instead of "unknown"
  over and over. A nightly job keeps this list tidy.
- **Cameras and zones from Frigate's config.** Camera names, zones and resolutions are read from
  Frigate rather than hard-coded, and a per-camera sheet in the UI lets you enable or disable a
  camera and set a zone condition for it.
- **Editable settings, no file surgery.** The main recognition parameters are edited on a Settings
  page in the UI; changes are validated, saved to an internal config store, and applied on the next
  restart, so you never hand-edit the base YAML.
- **Local recognition pipeline.** Face detection, alignment, embedding and matching all run locally;
  nothing leaves the machine.
- **MQTT and alerts.** Results are published on the service's own MQTT topics, and unknown-visitor
  and recognition alerts can be sent via Pushover or Telegram.

## How it works

For each pass, the service pulls the relevant recording from Frigate and samples it at a few frames
per second. In each sampled frame it detects faces (SCRFD), aligns each face to a canonical crop,
and computes an embedding with AdaFace. Each embedding is compared by cosine similarity against your
reference images for every known person, taking the best match per person.

A single frame over the threshold is not enough. Only when **at least two frames within a
three-second window** agree on the same person does the service treat that person as recognized for
the scenario. That one rule is most of what makes it steadier than a per-frame decision.

The recognition path runs entirely on the same machine as Frigate, on an Intel iGPU or NPU through
OpenVINO. On my own box that measured at about 24 ms per face on the iGPU and about 10 ms on the
NPU. There is no cloud dependency.

## Honest limits

In my own tests, with the multi-hit criterion, I haven't had a false match. But that's a handful of
people on my own recordings, not a guarantee: more people in your reference library, or very
different cameras, could change the picture. The timing figures above are measurements from one
setup, not a spec for every Intel iGPU or NPU.

## Requirements

- A running Frigate instance. `suslik` only *reads* Frigate (its API and MQTT) and never
  writes back to it; its own results go out on separate MQTT topics.
- An Intel iGPU or NPU for acceleration (via OpenVINO). Other accelerators such as Nvidia are not
  supported yet.

## Roadmap

- [ ] Docker image (bring your own reference data)
- [ ] Support for other accelerators (Nvidia CUDA, plain CPU) behind a pluggable backend
- [ ] Optional, local-first LLM second stage for scenarios where the face isn't recognized cleanly —
      advisory only, never overriding a confident face match
- [ ] A pluggable notification layer (beyond the built-in Pushover / Telegram / MQTT output)

## How this is built

I've spent a long time as a systems architect: whole operating systems written in assembler, large
programs in C and C++. Now retired, I do this outside my regular hours for the pleasure of putting
that architect's hat back on and pairing it with AI. The scenario concept, the model measurements,
and the design decisions are mine; the code is written largely with Claude (mostly Fable 5,
occasionally Opus 4.8). I'd rather be open about that.

## Feedback

The code and a Docker image aren't here yet; this repository is being prepared, and the README will
grow as the pieces become shareable. If you run Frigate and this sounds useful, I'd like to hear from
you: star the repo, start a thread in the **Discussions** tab about your setup or what you'd want, or
open an **issue** for a concrete bug or feature request. Telling me your setup (cameras, hardware,
how many people) genuinely helps shape it.
