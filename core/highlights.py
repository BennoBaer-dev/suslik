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
STAND = "0.1.0.199"   # .199 = RELEASE (Buendel .184-.198), Box-Eintraege vom
# User diktiert + abgestimmt (13.08. ~18:20 "das passt").
# Davor .198 = Fix des .197-Start-Absturzes (livewached las den
# abgeschafften Haken; referenzen_noetig + S10-Drift-Wache), kein Box-Eintrag.
# Davor .197 = interner Prod-Schritt (Quick-verdict-Haken weg:
# jeder enabled-Waechter erkennt Namen; live_speichern Felder-Fix: fehlende
# Felder behalten Gespeichertes), kein Box-Eintrag.
# Davor .196 = interner Prod-Schritt (Vereinfachungs-Schnitt:
# Slot-Vergabe ohne Lastmodell — enabled = laeuft, Notbremsen nur harter
# Deckel + RAM-Boden; Ueberlast regelt die Drossel; Quelltest misst echte
# Lieferrate), kein Box-Eintrag.
# Davor .195 = interner Prod-Schritt (Auftritts-Sicht der Live-
# Alerts: Tagesansicht + Today-Karten zeigen je Auftritt ALLE Gesichts-Crops
# + Rueckblick-Videos, analog der Pass-Ansicht; Slot-Riegel rechnet mit der
# gemessenen Lieferrate statt Test-Durchsatz), kein Box-Eintrag.
# Davor .194 = interner Prod-Schritt (Verarbeitungshoehe je Kachel
# 360-2160, Default 1080; Beweisbild-Klick an Live-Karten), kein Box-Eintrag.
# Davor .193 = interner Prod-Schritt (kontinuierliches Namens-Voting:
# Stufe-2-Namens-Meldung nach NAME_STIMMEN konsistenten Treffern je Auftritt),
# kein Box-Eintrag.
# Davor .192 = interner Prod-Schritt (/live_alerts Tagesuebersicht
# aller Trigger als Klickziel der Sidebar-Zeile), kein Box-Eintrag.
# Davor .191 = interner Prod-Schritt (Recognized live zeigt NUR
# erkannte Trigger — unknown erschlaegt die Reihe nicht mehr), kein Box-Eintrag.
# Davor .190 = interner Prod-Schritt (Recognized-live-Kartenreihe
# auf Today mit Beweisbild + Schnell-Urteils-Name), KEIN Box-Eintrag.
# Davor .189 = interner Prod-Schritt (Recognition chain als vierter
# Settings-Menuepunkt, eigenes Blatt /kette), KEIN Box-Eintrag.
# Davor .188 = interner Prod-Schritt (Today zeigt Live-Alerts als
# separate Liste mit Meldetext), KEIN Box-Eintrag.
# Davor .187 = interner Prod-Schritt (Recognition-chain-Sektion in
# Settings, ersetzt die zwei generischen Dropdowns), KEIN Box-Eintrag.
# Davor .186 = interner Prod-Schritt (Zustands-Gruppen + Hide +
# Stream-Steckbrief-Probe + Area-Schalter im Live-Reiter), KEIN Box-Eintrag.
# Davor .185 = interner Prod-Schritt (Kachel-Vorschau + echte
# Kopf-Aufloesung im Live-Reiter), KEIN Box-Eintrag ohne Abstimmung.
# Davor .184 = interner Prod-Schritt (umask-022-Fix, Backup-
# Klasse root:600), KEIN Box-Eintrag — Box bleibt auf dem .183-Stand.
# BOX-DIKTAT fuers NAECHSTE Release (User 13.08. ~11:45, ERWEITERT ~14:15;
# vor dem Release nochmal bestaetigen lassen). Kern und WICHTIGSTER Punkt:
# der Appell um Rueckmeldung. Sinngemaess: Entwickeln macht Spass, aber es
# kommt viel zu wenig Rueckmeldung — ohne sie weiss der Autor nicht, ob das
# Gebaute wirklich Bedarf trifft und gewuenscht ist; die Downloads sieht er,
# Rueckmeldung fehlt. Positiv WIE negativ erwuenscht. Speziell: zu rocm und
# gpu-legacy kam bisher GAR NICHTS — dabei kann er diese Hardware nicht
# selbst testen und weiss deshalb nicht einmal, ob es funktioniert (gerne
# mit Log melden). Erreichbar auf ZWEI Wegen: suslik_dev@posteo.de und
# GitHub. Dazu: Version 1.0 ist geplant, wenn das so funktioniert.
# Davor: .183 = Live-Release (Respin von .182: Kameranamen-Leck
# in Code-Kommentaren gefixt, Audit-Stufe 8b ergaenzt; Box-Text unveraendert).
# Box-Inhalt vom User DIKTIERT und abgestimmt (12.08. ~22:50 im Chat):
# (1) BETONTER Hinweis ungetestete Zwischenversion/ganzer Live-Part neu,
# (2) die Live-Story mit den gemessenen 199-801 ms. Weitere Kandidaten
# (Unknown-Sichtbarkeit, Topic-Praefix .176) blieben BEWUSST draussen —
# nicht ohne neue Abstimmung ergaenzen.

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
# .171 (Vision-Favorit aus Zellen-Stimmen, Analyse-Watchdog + RAM-Gate)
# bekommt BEWUSST keinen Box-Eintrag: interner Prod-Schritt, Box-Inhalt der
# naechsten Veroeffentlichung wird vorher mit dem User abgestimmt — hier wird
# nur STAND nachgezogen, die Box bleibt unveraendert.
# .172 (Tester-Paket: CPU-Thread-Kappung, Analyse-nice, Wanduhr-Serialisierung,
# Ketten-Schalter, In-Job-RSS-Wache, Vision-Stimme, Vision-Seiten-CSS) bekommt
# BEWUSST keinen Box-Eintrag: interner Prod-Schritt, Box-Inhalt der naechsten
# Veroeffentlichung wird vorher mit dem User abgestimmt — nur STAND nachgezogen.

# Neueste zuerst: (version, (eintraege ...)).
HIGHLIGHTS = (
    # .199 — User-DIKTAT (13.08. ~11:45, erweitert ~14:15, deutscher Entwurf
    # abgestimmt "das passt" ~18:20): TOP = Feedback-Appell (rocm/gpu-legacy
    # ungetestet, zwei Kontaktwege, 1.0-Plan), dann die fuenf Feature-Kerne
    # des .184-.198-Buendels.
    ("0.1.0.199", (
        BETONT + "A personal note from the author: I can see the downloads, "
        "but I get almost no feedback. Building this is fun — yet without "
        "feedback I don't know whether it actually meets a need. Positive "
        "and negative reports are equally welcome. Especially the rocm and "
        "gpu-legacy variants: not a single report so far, and I cannot test "
        "that hardware myself — I don't even know whether they work (a short "
        "note with a log would be great). If this works out, version 1.0 is "
        "the next step. You can reach me at suslik_dev@posteo.de or on "
        "GitHub.",
        "Recognized live, with a name: watchers now send a preliminary name "
        "verdict seconds after the trigger, with a proof picture — several "
        "people in the same pass are reported individually.",
        "Appearance view: the live day view bundles each pass into one card "
        "with all face pictures and recap videos; Today links straight to "
        "it.",
        "Per-camera processing resolution (360p-2160p, default 1080p) — "
        "measurably faster name recognition than before.",
        "Simpler and predictable: enabled means running — no load model "
        "refuses a watcher anymore, overload is handled by the runtime "
        "throttle; the source test now shows the camera's real delivery "
        "rate.",
        "A tidier Live tab: preview through the agent's eyes, real stream "
        "resolution, grouping by state and area; recognition chain as its "
        "own settings page.",
    )),
    # .183 — User-DIKTAT (12.08. ~22:50, Text im Chat abgestimmt; HALT-Gate
    # dafuer abgegolten): betonter Zwischenversions-Hinweis + Live-Story.
    # (.182 wurde nie als Release beworben — Respin wegen Kameranamen-Leck,
    # der Eintrag wandert mit auf die ausgelieferte Version.)
    ("0.1.0.183", (
        BETONT + "Untested in-between release: the entire live-watcher part "
        "is brand new in this version and has not seen wider testing yet — "
        "expect rough edges and please report what breaks.",
        "Live watchers: pick cameras to watch directly on the live stream — "
        "first face to verified signal in under one second (measured "
        "199-801 ms), e.g. to trigger Home Assistant via MQTT.",
    )),
    # .173 — mit dem User abgestimmt (11.08., Auswahl-Frage + Diktat-Ergaenzung):
    # der BETONTE Test-Release-Hinweis fuer cpu/gpu-legacy plus der Auto-Default;
    # #19/#9/#10 bleiben bewusst nur im CHANGELOG.
    ("0.1.0.173", (
        BETONT + "This build doubles as a test release for small machines: it "
        "ships as version tags for the cpu and gpu-legacy variants, so "
        "low-power boxes and older Intel iGPUs (5th–10th gen Core) can try "
        "it. The recent load cuts — thread caps on every model session, "
        "per-path recognition switches, conservative defaults on weak "
        "hardware — are aimed exactly at that hardware. Feedback welcome.",
        "Weak machines now default themselves: on the first start of this "
        "version every install measures its usable physical cores, and below "
        "the floor the recognition chain and the CPU thread cap are pre-set "
        "conservatively — loud in the start log, explained next to the "
        "settings, and never touching values you set yourself.",
    )),
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
