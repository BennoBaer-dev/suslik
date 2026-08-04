"""Zentrale Quelle der Release-Highlights fuer die What's-new-Box im UI (Task #16).

INHALTS-REGEL (User-Vorgabe 01.08.): NUR Key-Features, und der Inhalt wird vor
JEDEM Release MIT dem User abgestimmt — nie selbststaendig fuellen
(Memory whatsnew-inhalt-abstimmen; Runbook-Stufe-0-Halt). K3-Regel: die Box
liest AUSSCHLIESSLICH diese Liste. Das Gate prueft, dass der neueste Eintrag
der VERSION entspricht. Import-frei wie core/registry.py.

Stand .101 (User-Entscheid 01.08.): GENAU zwei Punkte — Learn-Modul und Areas."""

# STAND = bis zu welcher VERSION der Box-Inhalt MIT dem User abgestimmt ist (das Gate
# prueft STAND == VERSION). NICHT jede Version bekommt einen Eintrag (User 02.08.:
# .104/.105 nur ins CHANGELOG) — ein Release ohne Box-Aenderung zieht NUR STAND hoch,
# die Box erscheint dann nicht neu. Eintraege bleiben Key-Features-only.
STAND = "0.1.0.113"

# Neueste zuerst: (version, (eintraege ...)).
HIGHLIGHTS = (
    ("0.1.0.113", (
        "Person learn (preview): a second recognition path that learns "
        "residents by their whole appearance — start under Learn → Person "
        "learn, harvest full-body images and review every picture. Body "
        "recognition stays off until at least one person is learned and "
        "reviewed, and you arm it yourself under Person → Model status.",
        "A note on speed: this new path still runs on the CPU, so learning "
        "runs take a while (roughly 15–30 s per event) — please bear with "
        "it. Moving it to the GPU/NPU is planned for a later version.",
    )),
    ("0.1.0.103-alpha", (
        "Learning module: run guided learning over your past events — harvest faces, group recurring people, name them and adopt them into recognition.",
        "Camera areas: group cameras into parts of your property and use them as views on Today, Appearances and Events.",
    )),
)
