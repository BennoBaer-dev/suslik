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
STAND = "0.1.0.170"

# HERVORHEBUNG (0.1.0.168): ein Eintrag kann optisch herausstechen — genau EIN
# Fall ist dafuer vorgesehen, der Vorab-Hinweis am Anfang eines Releases. Die
# Markierung ist ein PRAEFIX am Text, kein neues Schema: die Eintraege bleiben
# Strings, damit Gate, Beweis und jeder Leser unveraendert weiterlaufen. Der
# Renderer nimmt das Praefix ab und setzt den Eintrag fett und in Warnfarbe;
# wer die Liste roh liest, sieht die Marke und weiss, was gemeint ist.
BETONT = "!! "
# .139/.140 (Erkennungs-Review Baustein 1, Fremd-Klasse + Schwellen-Eichung)
# bekommen BEWUSST keinen Box-Eintrag: interne Prod-Schritte, kein Release. Der
# Box-Inhalt der naechsten Veroeffentlichung wird wie immer vorher mit dem User
# abgestimmt — hier wird nur STAND nachgezogen, die Box bleibt unveraendert.

# Neueste zuerst: (version, (eintraege ...)).
HIGHLIGHTS = (
    # .170 — Release-Eintrag, mit dem User abgestimmt (10.08.): die
    # KI-/Vision-Geschichte bleibt der Kern der Box (.168), .170 traegt NUR den
    # kurzen Fix-Hinweis zur Galerie; der fruehere .169-Block ging darin auf.
    ("0.1.0.170", (
        "Fixes for the gallery comparison: the candidate grid now uses up to "
        "12 cells (matching your reference galleries), the exact grid shown "
        "to the model is saved and visible on the walk-through's page, and "
        "the recognition test shows the face pictures alongside person and "
        "vision.",
    )),
    # .168 — mit dem User abgestimmt (09.08.); der fruehere Betont-Punkt
    # "early working version" wurde am 10.08. auf User-Anweisung ENTFERNT
    # (kein Arbeitsversions-Hinweis mehr in der Box).
    ("0.1.0.168", (
        "Vision detect: a third, independent recognition path — each "
        "walk-through is judged as one candidate grid against your approved "
        "galleries (local llama.cpp or your own API endpoint).",
        "Gallery wizard with automatic curation: proposals are scored on face "
        "visibility, lighting and completeness, with a reason line per cell.",
        "Recognition test: face, person and vision side by side for any past "
        "walk-through, with a live narrative log.",
    )),
    # .138 mit User abgestimmt 06.08. ("go" auf den Zwei-Punkte-Vorschlag).
    ("0.1.0.138", (
        "New \"Frigate sync\" page: a full reconciliation of your reference "
        "library with Frigate — see what is on both sides and what is "
        "missing where, pick exactly which images to send, and get a "
        "per-image result, including Frigate's own reason when it refuses "
        "one. Images you deleted in Frigate become explicit decisions "
        "instead of silent re-uploads.",
        "Sync problems now explain themselves: the export never stops on a "
        "single bad image, a live status line shows whether Frigate's face "
        "recognition is on, and a one-click diagnosis bundles the suslik "
        "report together with Frigate's log — ready to attach to a bug "
        "report.",
    )),
    ("0.1.0.129", (
        "Clean up your learning area: runs can now be deleted completely "
        "— per run or all old ones with a single click. Dismissed "
        "clusters are remembered, so re-harvests of the same events stay "
        "quiet.",
        "\"Looks like\" suggestions now also recognize people already in "
        "your system — resident clusters no longer show up unlabeled.",
        "Events without any person in them can be marked as false triggers "
        "— they get their own silent class and stop cluttering the "
        "label flow.",
    )),
    ("0.1.0.118", (
        "Recognition got a lot faster: video decoding now runs on the GPU "
        "(Intel via VAAPI, NVIDIA via NVDEC) and only the frames that matter "
        "leave the decoder. On the author's machine a learning run dropped "
        "from 6.6 to 2.9 seconds per event.",
        "Face and person recognition now work together on Today: a pass with "
        "no usable face is attributed to the person the body path recognized "
        "\u2014 clearly marked 'via person recognition, no face'.",
        "Full backup: one portable archive with everything you taught your "
        "installation (settings, face references, learned person material, "
        "models) and a restore that brings it all back \u2014 made for moving "
        "to another machine.",
        "The person path's decision threshold is now measured from your own "
        "material after every training, and the fire rule (window, supporting "
        "events, cool-down) is configurable under Person \u2192 Model status.",
    )),
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
