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
training (cross-validation between your learned people) — but real
strangers are not part of that material yet, so keep an eye on alerts
and disarm any time. You can override the threshold and the fire rule
under **Person → Model status**.

## How to use it, step by step

1. **Learn → Person learn.** Pick who to learn (one person, or all known
   people — people come from your face collection) and how many events to
   scan. Start small (50). The run harvests full-body images from your
   recordings; an image is tied to a person only when a face-confirmed
   walk-through proves it.
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
   training time) and holds the **live switch**. Arming is only possible
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

Every alert from this path is marked as coming from **person recognition,
not face recognition**, so the two paths never get mixed up. Because both
paths are independent, you may receive two notifications for the same
walk-through — merging them into one smart alert is planned for a later
version.
