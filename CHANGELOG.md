# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.045 (2026-10-30)

Live watcher: the watcher now recognises faces with the same computation as the event analysis (the same models, quality, head-pose and feature-norm checks and the same vote stack) at full camera resolution, on every hardware variant.

## 0.1.1.043 (2026-10-28)

Today page: the side column now shows how many of the day's events had at least one face, instead of the 'not matched inside passes' count.

Housekeeping: face candidates nobody picked and unknown groups not seen for seven days are now cleared out automatically, together with old internal logs. Everything removed waits one week in a trash folder before it is deleted.

CUDA: the first card size query at startup now waits up to 30 seconds instead of 2. On machines where the graphics card answers slowly right after startup, the start then no longer logs two misleading errors about the card.

## 0.1.1.041 (2026-10-27)

Learning run: the feature-norm step now always gets a full hour, so large runs no longer stop the worker halfway through. Its success messages are no longer logged as errors; real problems get their own warning.

## 0.1.1.040 (2026-10-26)

This release bundles 0.1.1.038 and 0.1.1.039, which were built but never pushed.

The Unknown page is new. It shows the unknown faces of the last seven days as cards in three tabs, "Looks like a known
person", "Unknown" and "Not good enough to learn", five cards per page. Tick the good pictures on a card and give them a
name; they become references for that person. Only pictures of good enough quality can be ticked. When suslik suggests a
person, the card also shows the pictures it already knows of that person. The third tab lists groups whose pictures are
all too weak to learn from, each picture with its quality and the value it needs, without buttons. Links from Today and
Appearances open the right card. The page is in the menu under Activity next to Events and under Faces, and in the Easy
view as well. If it cannot read everything, it says so in red instead of showing an empty page. Five new settings on the
Advanced page set the days, cards per page, pictures per card, comparison pictures and events per card.

The "To label" page is gone. It took far too long on installations with many events; old bookmarks open the Unknown page.

With several people in one pass, each Frigate event now gets the name of the person Frigate tracked in it, worked out
from where the faces are in the clip and from Frigate's path of each event. If that is not possible, suslik writes the
strongest name of the clip as before and logs a warning. Later events of the same pass correct names suslik wrote
earlier; names set by someone else are never overwritten.

The check buttons on Appearances now say when a clip could not be fetched instead of "nothing to take", and fetch it again on
the next click. Their progress updates no longer read the whole detection record each time.

The dispatcher can now fetch up to 4 clips from Frigate at the same time instead of 3 (setting vorlauf_parallel on the
Advanced page; the default stays 2).

The Unknown page now only offers pictures that suslik stored in its current format, with every quality value measured;
older pictures from earlier versions are no longer offered for naming. Pictures below the quality bar cannot be ticked. If
no group can be named, the page says so instead of "Everything named". If the page can read only part of its data, the red
note shows one translated sentence, and the log gets one error line per reason instead of one per visit. The name field
shows its whole placeholder.

## 0.1.1.037 (2026-10-24)

This release bundles 0.1.1.036, which was built but never pushed.

Faster with a large face catalog. When references are added, suslik now updates its catalog in place instead of reading and
checking all of it again. Pages that list people only check what changed since their last look.

The System page no longer compares the face library with Frigate on every visit. It shows a link to Frigate sync instead, where
the comparison still runs.

After a restart, suslik reads the detection record and the list of people in the background right after the start check. The
first visit to Presence, Today or System then no longer waits for this, as long as the background read has finished. If the
background read fails, the start counts as failed and the status stays red until the next start.

suslik now keeps a local record of how face candidates become references (offered, selected, taken over, used). It stays on your
machine, holds no names, and prepares better storage rules in a coming version.
