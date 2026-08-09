# Person recognition (preview) — recognizing residents without a face

Sometimes an event shows up as "unknown" although it clearly is a known
person — just seen from behind, or too far away for a face. Person
recognition is suslik's second, independent recognition path for exactly
these cases: it learns what a resident looks like as a **whole** (build,
hair, posture) from your own recordings.

Everything runs locally. Images are turned into a numerical fingerprint
(DINOv2 embeddings), and a small model trained on your own, hand-approved
pictures decides which resident a fingerprint belongs to — with a decision
threshold that strangers stay below.

**Preview status:** the path works end to end. Since 0.1.0.118 the
decision threshold is measured on your own approved material after every
training, and since 0.1.0.139 it can be measured against real strangers
(see below). Keep an eye on alerts and disarm any time. You can override
the threshold and the fire rule under **Person → Model status**.

## The threshold, and what it is measured against

After every training the threshold is re-measured by cross-validation:
the model is trained on part of the material and has to judge the rest,
which it has never seen.

Without stranger material that measurement can only compare your learned
people against each other — the threshold ends up just above the
strongest confidence a *wrong resident* ever got, and a real stranger is
an untested case.

Put confirmed stranger crops into `personlern/fremd/` (flat; `.jpg`,
`.jpeg` or `.png` in any casing; at least five) and two things change.
The strangers become a class of their own, so a body the model reads as
a stranger is dropped before it can become a hit — no alert, nothing on
Today. And the threshold becomes the strongest confidence any real
stranger reached *for one of your people* across three fixed
cross-validation splits, plus a small margin, so no stranger in the
measurement would have passed it. Model status names the price too: how
many of your own images still pass, and how many of them would reach
that threshold for the wrong person. With fewer than five stranger
images they stay out of the model entirely — training and threshold
always describe the same model — and the status says why. An unreadable
file in the folder (a broken copy, a non-image) is skipped and counted,
never a reason for the training to stop; if a training run does fail,
the model page says so in red instead of presenting the previous model
as current.

## How to use it, step by step

1. **Learn → Person learn.** Pick who to learn (one person, or all known
   people — people come from your face collection) and how many events to
   scan. Start small (50). The run harvests full-body images from your
   recordings; an image is tied to a person only when a face-confirmed
   walk-through proves it. Identical frames are never stored twice (the
   harvest has a duplicate guard; material harvested before 0.1.0.119 can
   still contain such pairs). A run can legitimately finish with **zero
   images** — the wizard then explains why: either that person had no
   face-confirmed walk-throughs in the window (the card shows when the
   event record starts and whether they were seen *below* the
   confirmation threshold), or everything bindable is already in your
   learning material.
   *Note on speed: harvesting currently runs on the CPU — expect roughly
   15–30 s per event. GPU/NPU support for this path is planned.*
2. **Review every image.** After the run, click **Review the images now**
   and mark everything that is wrong (not this person, or unusable). A bad
   run can be discarded entirely. Nothing is learned without your
   approval.
3. **Finish the review.** Approved images become learning material; the
   model retrains automatically (seconds).
4. **Person → Body images** shows everything that has been learned, per
   person and per run. Delete single images or whole runs there — the
   model retrains after deletions, and a new run can always re-harvest.
5. **Person → Model status** shows the trained model (images per person,
   training time, how many stranger negatives went in and what the
   threshold was calibrated against) and holds the **live switch**.
   Arming is only possible
   after at least one person has been learned *and* reviewed. Until then
   the path stays off and never sends anything.

## Alerts

When armed, the body path judges live person events on its own — fully
separate from face recognition (own threshold, own fire rule, own
cool-down). It alerts only after **several** supporting events of the same
walk-through, never on a single image.

- **Pushover**: message plus the best body crop of the walk-through so far
  as image (the largest crop among the supporting events wins).
- **Telegram**: message plus the event clip as video (same transcode and
  quality settings as face alerts; `telegram_inhalt`/`telegram_hoehe`
  apply to both paths).
- **MQTT**: every hit above the threshold is published on
  `verifyd/person_erkennung` as JSON (`person`, `score`, `stuetzen`,
  `feuer`, `quelle`) — handy for Home Assistant automations.

## How it shows up on Today

Since 0.1.0.118 the two paths cooperate on **Today** (and on the
Appearances day view): a pass with no usable face is **attributed** to the
person the body path recognized — it needs at least as many supporting
events as your fire rule requires, the person's card counts the pass, and
it no longer appears as an unknown visitor. The pass row is clearly marked
*via person recognition, no face*; passes recognized by face show *via
face* or *via face + person*. Face judgments always take precedence. The
pass chip and the person card show the best body crop of that walk-through
(the judged crops are kept under `personlern/treffer/` for 30 days).

Every alert from this path is marked as coming from **person recognition,
not face recognition**, so the two paths never get mixed up. Because both
paths are independent, you may receive two notifications for the same
walk-through — merging them into one smart alert is planned for a later
version.
