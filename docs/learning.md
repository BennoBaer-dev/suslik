# Learning people from your own recordings

suslik does not want photo uploads. It learns the people around your property from the
footage your cameras already recorded, and it asks you to name a person **once** instead
of labeling image after image.

There are two ways in, and they complement each other:

- The **learning run** described here works through your event history in one go. Use it
  when you set suslik up, or whenever you want to catch up on people it has been unsure
  about. This is the guided path.
- The **day-to-day path** picks up the same work automatically after every walk-through:
  suggestions for people it already knows, and clusters for faces it doesn't. That one is
  described in [usage.md](usage.md#enrollment-teaching-suslik-a-person).

## What a learning run does

Open **Known people → Learn people**. The wizard walks through five phases, and the page
keeps updating while it works — you can close the browser, a run survives restarts and
resumes where it stopped.

**1. Preparation.** suslik measures the analysis speed of *this* machine and estimates how
long the run will take and how much video it needs to pull from Frigate. The estimate is
measured, not guessed; before the first measurement it says so.

**2. Harvest.** It walks the person events you selected and collects the usable faces from
each one — sharp enough, large enough, facing the camera enough. Detections that are not
really faces (foliage, a wheel arch, a light pattern) are filtered out here.

Start small. The wizard has a field for how many events to work through, and roughly **50
events** is a good first run: it finishes quickly and shows you whether the result looks
sensible. Widen it afterwards.

**3. Grouping.** The harvested faces are clustered into **anchors** — one anchor is one
recurring person, gathered across cameras and days. This is the step that turns "hundreds
of face crops" into "seven people who keep showing up".

**4. Naming.** Your step, and the only one that needs you. Open an anchor cluster: suslik
sorts its faces by perspective (facing the camera, looking left, looking right) and marks
the ones it recommends as references. Two buttons — **Select all recommended** and
**Deselect all** — do the bulk work; you can still add or remove single images. Then give
the cluster a name, either a new one or an existing person.

The recommendation is not arbitrary. Near-identical crops of the same moment are dropped,
because ten copies of one pose teach nothing, and a limited number per perspective is kept
so that a person is represented from several angles rather than fifty times from the front.

**5. Adoption.** With **Adopt into recognition** the selected faces become reference images
for that person. suslik checks them against the references it already has, so the same face
does not land twice, and the adoption is all-or-nothing: either the whole set lands or
nothing changes. Afterwards the cluster is marked as adopted and becomes read-only.

## What you should expect

A learning run does not make suslik perfect at recognizing everyone. It gives it a solid,
varied set of reference faces per person, which is the single biggest lever on recognition
quality. Faces recorded at night under infrared illumination are the known weak spot — the
recognition models are trained on colour images, so a purely infrared reference is worth
less than a daylight one.

Two phases are listed in the wizard but not active yet: side views and a full-body stock.
They are being built.

## Settings worth knowing

These live under **System → Advanced settings**. The defaults are deliberate starting
values; if a run does not feel right, this is where you tune it, one value at a time.

| Key | What it does |
|---|---|
| `benennung_k_je_bin` | how many recommended images are kept per perspective |
| `benennung_yaw_grenze` | beyond this angle a face counts as looking left or right |
| `benennung_dup_sim` | similarity at or above which two crops count as near-identical |
| `benennung_vorschlag_schwelle` | when suslik offers "looks like *X*" during naming |
| `anker_k_min` | minimum number of faces before a cluster becomes an anchor |

If a run produced anchors that mix two people, or split one person into three clusters,
that is a threshold question rather than a bug — the anchor page shows the margin for each
cluster, and clusters with a weak margin are flagged for review.

## Where the data lives

Everything a run produces stays in your data volume: the harvested crops, the anchors, and
a protocol of what was adopted when. Nothing is uploaded anywhere, and Frigate is only ever
read from — unless you deliberately switch on the reference export, which writes your
reference images back into Frigate's own face library over its HTTP API.
