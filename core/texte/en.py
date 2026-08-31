"""Englische Referenz-Texte (Stufe 0: waechst je eingezogener Tranche;
Schluessel-Konvention <modul>.<block>.<rolle>, konzept_sprache.md v2)."""
T = {
    # ------------------------------------------------ routes/gesichter ---
    "gesichter.titel": "Known people",
    "gesichter.kopf.knopf_lernen": "Learn people",
    "gesichter.kopf.hinweis_lernen":
        "guided learning run over your own recordings (foundation stage)",
    "gesichter.kopf.satz":
        "All learned persons and their reference images. You can remove "
        "individual images, assign more from the unknown faces via the "
        "button per person, or upload a photo below, also for an entirely "
        "new person.",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "images"; der
    # Plural-Feinschliff (eins/viele via t_n) ist eine BEWUSSTE spaetere
    # Verhaltensaenderung, nie Teil des Einzugs.
    "gesichter.galerie.bildzahl": "{n} images",
    "gesichter.galerie.knopf_entfernen": "remove",
    "gesichter.galerie.knopf_aehnliche": "find matching faces",
    "gesichter.galerie.knopf_qs": "Quality-check",
    "gesichter.galerie.knopf_loeschen": "Delete person\u2026",
    "gesichter.galerie.hinweis_leer": "no images yet",
    "gesichter.upload.titel": "Upload photo",
    "gesichter.upload.attr_person": "existing person\u2026",
    "gesichter.upload.attr_neu": "or new person",
    "gesichter.upload.knopf": "Upload",
    "gesichter.upload.hinweis":
        "New person: type the name into the free-text field. Gate: "
        "buffalo_l must find a face (otherwise an override prompt appears).",
    "gesichter.import.titel": "Import / resync from Frigate",
    "gesichter.import.knopf": "Sync faces from Frigate",
    "gesichter.import.hinweis":
        "Fetches reference images Frigate has that this library doesn't "
        "yet \u2014 incremental, safe to run any time (nothing local is "
        "deleted). Same import as in the setup wizard, now reachable "
        "without re-running it (e.g. after restoring a configuration).",
    # ------------------------------------------------- routes/kameras ---
    "kameras.steckbrief.knopf": "Re-check stream details",
    "kameras.steckbrief.hinweis":
        "Stream resolution is read once per camera and then remembered. Use this if you changed a camera's stream, or if one is listed as unreachable.",
    "kameras.steckbrief.stand": "{n} of {ges} camera(s) checked, {fehler} unreachable",
    "kameras.steckbrief.laeuft": "checking \u2026",
    "kameras.steckbrief.fertig": "will be re-checked on the next restart",
    "readme.einleitung": 'I wrote this because these questions kept coming up.',
    "readme.kontakt": 'I am glad to hear from you:',
    "readme.titel": 'Read me first',
        "readme.knopf": 'Read me first',
        "readme.schliessen": 'Close',
    "readme.zurueck": 'Back',
        "readme.fuss": 'This text appears once after every restart.',
        "readme.inhalt": 'Contents',
        "readme.generell.titel": 'General',
    "readme.generell.text": "My scenario detection hangs on Frigate's person detection. As soon as Frigate reports a person, I fetch the whole person event. Such an event is sometimes a few seconds long, sometimes several minutes. I go through all of it to find every person in it.\n\nWhether Frigate's own face recognition is switched on makes no difference. It is only needed if you want faces synced with Frigate.\n\nThe check never runs on the detect stream. It runs on the recording, that is the best stream the camera hands to Frigate.\n\nA check starts in one of two ways. Either from a person event in Frigate, which is the scenario path. Or from the live watcher: it pulls the running stream, straight from the camera or through Frigate's proxy, looks for faces and starts from there.\n\nA person is recognised in three ways. By the face. By the person as a whole, from the picture alone, without a face. By a vision model, and that one is still beta.\n\nI run 4K cameras here, with the frame rate as high as it goes, at least 15 frames per second. Same for the bitrate. A low bitrate leaves moving faces blurred.",
    "readme.aktuell.titel": 'What I am working on',
    "readme.aktuell.text": 'A calibration button. Camera feeds differ a lot, and with them the sharpness and what gets recognised. Calibration is meant to even that out.\n\nVision recognition through a language model: identifying a person when no face is visible. It runs in beta and needs to get better.\n\nPresence tracking: recording whether a known person is there or not. Other systems can hook into that, an alarm system for instance, or time tracking.',
    "readme.lernen.titel": 'How do I teach it new faces?',
    "readme.lernen.text": "This is how I do it on my system:\n\nFace learning run. The first thing on a new system. Depending on the hardware the last 500 events, 1000 if there is room to spare. The program fetches the events with a person, groups them and puts the pictures together. Known ones it assigns on its own. Unknown ones it collects as a group, and I give the group a name. That gives the starting set. Only works on faces that were recognised cleanly.\n\nToday. Once the starting set is there, anything new comes in from here: click an event or a person, adopt the face.\n\nKnown. Pick a person, have it find matching faces.\n\nPerson learning run. There is one next to it, for people whose face is not readable. More on that later.\n\nQuality. I use that tab regularly. It shows how good a person's pictures really are, which ones are too weak and which ones overlap with another person. Anything too similar I take out.\n\nThe Unknown tab is left over from an earlier version. I do not use it.",
    "readme.persoenlich.titel": 'Personal',
    "readme.persoenlich.text": 'This is purely a hobby. As a senior IT architect, I enjoy building something with AI. It is built entirely with Claude Code, mostly on Fable 5, with Opus 5 for the agents.\n\nWhat I would like is feedback, and it makes me happy when someone puts the system to use. That is my reward.',
    "kameras.titel": "Cameras",
    "kameras.banner.config_fehler":
        "Could not read the Frigate config: {fehler}",
    "kameras.karte.verwenden": "use this camera",
    "kameras.karte.zonen_hinweis": "none ticked = all events",
    "kameras.karte.zonen_keine":
        "no zones defined in Frigate \u2014 all events",
    "kameras.karte.rec_an": "rec \u2713",
    "kameras.karte.rec_aus": "no rec",
    "kameras.karte.pill_aus": "off in Frigate",
    # Byte-Treue: das HTML-Entity &mdash; stammt aus dem Original-Attribut
    # (title=...) und bleibt Stufe 0 exakt erhalten; huebscher machen ist
    # eine spaetere bewusste Aenderung, nie Teil des Einzugs.
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate runs no person detection on this stream &mdash; no events "
        "can arrive here",
    "kameras.karte.pill_keine_detektion": "no detection in Frigate",
    "kameras.leer.titel": "No cameras found in Frigate.",
    "kameras.leer.hinweis": "Check that suslik can reach the Frigate API.",
    "kameras.fuss.knopf_speichern": "Save cameras",
    # -------------------------------------------------- routes/lernen ---
    "lernen.titel": "Suggestions — people to enroll",
    "lernen.kopf.titel_offen": "Suggestions ({n})",
    "lernen.leer.titel": "No open enrollment suggestions.",
    "lernen.leer.hinweis":
        "Good new faces (large, sharp, frontal, confidently recognized or "
        "clearly a stranger) appear here automatically after the analysis.",
    "lernen.karte.unbekannt": "Unknown/Stranger",
    # {sharp} kommt vorformatiert (:.0f) aus der Route — Formatspezifika
    # gehoeren nicht in Textwerte (Gate-Formatprobe kennt nur {name}).
    "lernen.karte.metrik_voll":
        "score {score} · novelty {novelty} · {bw}×{bh}px · front {front} · "
        "sharp {sharp}",
    "lernen.karte.metrik_kurz": "score {score}",
    "lernen.karte.link_video": "Video",
    "lernen.karte.knopf_add_person": "Add as {person}",
    "lernen.karte.attr_person": "as person…",
    "lernen.karte.attr_neu": "or new person",
    "lernen.karte.knopf_add": "Add",
    "lernen.karte.knopf_ablehnen": "Reject",
    "lernen.galerie.titel": "Reference stock (Master)",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "references" —
    # Plural-Feinschliff (t_n) ist eine BEWUSSTE spaetere Aenderung.
    "lernen.galerie.bildzahl": "{n} references",
    "lernen.upload.titel_abschnitt": "Upload",
    "lernen.upload.titel": "Upload your own photo into the Master",
    "lernen.upload.attr_person": "existing person…",
    "lernen.upload.attr_neu": "or new person",
    "lernen.upload.knopf": "Upload",
    "lernen.upload.hinweis":
        "New person (e.g. Alex): type the name into the free-text field. "
        "Gate: buffalo_l must find a face (otherwise an override prompt "
        "appears). PNG is converted to JPEG. Upload several photos from "
        "different angles one after another.",
    # --------------------------------------------------- routes/areas ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Chip-Texte "All"/
    # "Default" sind zugleich Sicht-KENNUNGEN (Vergleich gegen aktiv +
    # URL-Wert aus core/areas.sicht_aufloesen) — Anzeige==Kennung ist erst
    # mit einer Entkopplung uebersetzbar; dazu zwei Absaetze mit Inline-
    # Markup mitten im Satz (<b>Default</b>, <b>view</b> + konditionalem
    # Satzteil), die auf den t_html-Weg spaeterer Stufen warten.
    "areas.titel": "Areas",
    "areas.kopf.sprung": "Jump into a view:",
    "areas.verwaltung.titel": "Manage areas",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "areas.verwaltung.camzahl.eins": "{n} cam",
    "areas.verwaltung.camzahl.viele": "{n} cams",
    "areas.verwaltung.attr_entfernen":
        "remove this area — its cameras return to Default",
    "areas.verwaltung.attr_neu": "new area name",
    "areas.verwaltung.knopf_anlegen": "Add area",
    "areas.verwaltung.titel_zuweisen": "Assign cameras",
    "areas.verwaltung.satz_zuweisen":
        "One camera belongs to exactly one area; everything not assigned "
        "stays in Default. Saving needs no service restart.",
    "areas.verwaltung.pill_nicht_gesehen": "not seen",
    "areas.verwaltung.attr_nicht_gesehen":
        "assigned earlier, not in Frigate right now",
    "areas.verwaltung.hinweis_keine_kameras":
        "No cameras known yet — connect Frigate first (Settings).",
    "areas.verwaltung.knopf_speichern": "Save areas",
    # -------------------------------------- routes/benachrichtigungen ---
    # NICHT eingezogen (bewusst): der Einleitungs-Absatz (<b>/data</b>,
    # <b>Test</b>) und der Topic-Praefix-Hinweis (<b>verifyd</b>) tragen
    # Inline-Markup mitten im Satz (t_html-Weg spaeterer Stufen); die
    # Karten-Titel Pushover/Telegram/MQTT sind reine Produktnamen; die
    # Option-WERTE aus/ha/direkt/beide und video/bild sind Config-Werte
    # (technische Bezeichner), nur ihre Erklaerzeile ist Text.
    "benachrichtigungen.titel": "Notifications",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• stored — blank keeps it",
    "benachrichtigungen.felder.secret_leer": "not set",
    "benachrichtigungen.felder.option_an": "on",
    "benachrichtigungen.felder.option_aus": "off",
    "benachrichtigungen.alerts.titel": "Alerts",
    "benachrichtigungen.alerts.hinweis":
        "Which judgment categories raise an alert — on every channel "
        "(Pushover, Telegram, MQTT scene topics). The recognized-person "
        "push itself is governed by the Presence toggle below; the MQTT "
        "data topics (erkennung, heartbeat) always publish while MQTT "
        "publishing is on.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik confirms a different person than Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate labeled someone, suslik saw no usable face",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik recognized someone, Frigate did not",
    "benachrichtigungen.kategorien.beide_unknown":
        "neither side identified a face",
    "benachrichtigungen.kategorien.erkannt":
        "a known person was recognized",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "a usable face, but nobody confirmed (possible stranger)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "a face too weak or small to identify",
    "benachrichtigungen.alerts.stil_label": "Alert text style:",
    "benachrichtigungen.alerts.stil_worte": "plain words",
    "benachrichtigungen.alerts.stil_worte_zahlen": "words + raw scores",
    "benachrichtigungen.alerts.stil_hinweis":
        "how alerts describe a match (plain words is the default; raw "
        "cosine/score numbers only if you want them back)",
    "benachrichtigungen.alerts.label_anwesenheit_push": "Presence push:",
    "benachrichtigungen.alerts.label_alert_cooldown": "Alert cooldown (s):",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Presence cooldown (s):",
    "benachrichtigungen.alerts.label_szene_karenz": "Scene grace (s):",
    "benachrichtigungen.pushover.label_token": "Token:",
    "benachrichtigungen.pushover.label_user": "User key:",
    "benachrichtigungen.pushover.knopf_test": "Test Pushover",
    "benachrichtigungen.telegram.label_modus": "Mode:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=off · ha=via Home Assistant · direkt=direct bot · beide=both",
    "benachrichtigungen.telegram.label_inhalt": "Attachment:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=short clip, image if unavailable · bild=image only "
        "(no transcoding — lighter on weak hardware)",
    "benachrichtigungen.telegram.label_bot_token": "Bot token:",
    "benachrichtigungen.telegram.label_chat_id": "Chat ID:",
    "benachrichtigungen.telegram.label_cooldown": "Unknown cooldown (s):",
    "benachrichtigungen.telegram.knopf_test": "Test Telegram",
    "benachrichtigungen.mqtt.label_publish": "Publish recognition topics:",
    "benachrichtigungen.mqtt.label_host": "Host:",
    "benachrichtigungen.mqtt.label_port": "Port:",
    "benachrichtigungen.mqtt.label_user": "User:",
    "benachrichtigungen.mqtt.label_password": "Password:",
    "benachrichtigungen.mqtt.label_topic_praefix": "Topic prefix:",
    "benachrichtigungen.mqtt.knopf_test": "Test MQTT",
    "benachrichtigungen.fuss.knopf_speichern": "Save + restart",
    # ----------------------------------------------- routes/aehnliche ---
    # {sim} kommt vorformatiert (:.2f) aus der Route (wie lernen.{sharp}).
    "aehnliche.kopf.titel": "Matching faces for {person}",
    "aehnliche.kopf.satz":
        "Two sources: unknown faces that resemble {person}, and new "
        "faces from events in which {person} was already confidently "
        "recognized. Tick and apply.",
    "aehnliche.kopf.link_zurueck": "back",
    "aehnliche.unbekannt.titel": "From unknown faces",
    "aehnliche.unbekannt.suche_titel":
        "Search running — references are being re-read.",
    "aehnliche.unbekannt.suche_hinweis": "The page refreshes by itself.",
    "aehnliche.unbekannt.hinweis_leer":
        "No similar unknown faces in stock.",
    "aehnliche.unbekannt.aehnlichkeit": "similarity {sim}",
    "aehnliche.unbekannt.knopf_hinzu": "Add selected to {person}",
    "aehnliche.vorschlaege.titel":
        "New faces from recognized events (7 days)",
    "aehnliche.vorschlaege.suche_titel":
        "Search running — recognized events are being scanned.",
    "aehnliche.vorschlaege.suche_hinweis":
        "The page refreshes by itself; result in one or two minutes.",
    "aehnliche.vorschlaege.kachel_zeile": "{wann} · {kamera} · sim {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Recommended",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutral — check the image before applying",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Clearly this person, but either the match is below the confidence "
        "threshold or the crop is smaller / less sharp — a look decides.",
    "aehnliche.vorschlaege.knopf_alle": "Apply all recommended ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt": "Apply selected to {person}",
    "aehnliche.vorschlaege.knopf_neu": "search again",
    "aehnliche.vorschlaege.fuss":
        "as of {stand} · recommended = confidently {person} + reference "
        "quality",
    "aehnliche.vorschlaege.hinweis_leer":
        "Nothing matching found in the recognized events.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Criteria: unambiguously this person, novel compared to "
        "the stock, sufficiently large and sharp.",
    "aehnliche.vorrat.titel": "New from the learning stock",
    "aehnliche.vorrat.hinweis":
        "High-quality faces the learning run collected, judged by the "
        "reference-free quality measure and the scenario consensus. They "
        "stay local and are never exported to Frigate.",
    "aehnliche.vorrat.kachel_zeile": "{wann} · {kamera} · match {sim} · quality {norm}",
    "aehnliche.vorrat.auch_anker": "also in a face group",
    "aehnliche.vorrat.knopf_gewaehlt": "Apply selected to {person}",
    # ------------------------------------------------- routes/frigate ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Beweis-Zeilen der
    # Verbindungs-, Kamera- und FR-Kachel (bis auf "state unknown") tragen
    # <b>/<br>/<a>/<code> mitten im Satz — t_html-Weg spaeterer Stufen;
    # ebenso der Seiten-Einleitungssatz (Link im Satz) und die Expert-
    # Zeilen. Der h2 "Frigate" ist reiner Produktname. Zwei JS-Statustexte
    # tragen \\u-Escape-Folgen im JS-Quelltext und warten auf den
    # window.T-Weg (Stufe 1). HTML-Entities (&mdash; &rsquo; &amp;) in
    # Werten sind Byte-Treue zum Original.
    "frigate.verbindung.titel": "Connection",
    "frigate.verbindung.satz":
        "My program reads events and snapshots from your Frigate over its "
        "HTTP API — nothing is installed on the Frigate side.",
    "frigate.verbindung.knopf_aendern": "Change connection",
    "frigate.verbindung.knopf_speichern": "Save &amp; restart",
    "frigate.verbindung.knopf_abbrechen": "Cancel",
    "frigate.verbindung.hinweis_speichern":
        "saving restarts the service briefly; this tile then shows "
        "live whether the new address answers",
    "frigate.kameras.titel": "Cameras",
    "frigate.kameras.satz":
        "Which of Frigate&rsquo;s cameras this program watches, and which "
        "zones count. Everything else is ignored.",
    "frigate.kameras.beweis_keine_auswahl":
        "no camera selection saved yet — every camera Frigate "
        "offers is used",
    "frigate.kameras.knopf": "Manage cameras",
    "frigate.sync.titel": "Sync",
    "frigate.sync.satz":
        "Keeps the two face libraries in step: send reviewed faces to "
        "Frigate, import what only Frigate has &mdash; always your call, "
        "never automatic.",
    "frigate.sync.knopf": "Review &amp; sync",
    "frigate.fr.titel": "Frigate&rsquo;s own face recognition",
    "frigate.fr.satz":
        "Frigate can recognize faces too. This program works with or "
        "without it &mdash; the switch lives in Frigate&rsquo;s config, "
        "read here live so you know what a sync can do right now.",
    "frigate.fr.beweis_unbekannt": "state unknown — {detail}",
    "frigate.js.url_fehlt": "enter the Frigate URL",
    "frigate.js.fehler": "error:",
    # ------------------------------------------- routes/ereignisliste ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Tabellen-Kopfzellen
    # "Frigate" und "suslik" sind reine Produktnamen; die Kategorie-Labels
    # kommen aus webui.bausteine.KAT_LABELS (zentrale Quelle, eigene
    # Tranche); das Datumsformat %d.%m bleibt in der Route (B19-Stufe).
    "ereignisliste.offen.titel": "Open cases to label ({n})",
    "ereignisliste.offen.satz":
        "Filled automatically: all events with faces that nobody confirmed "
        "and that you haven't labeled yet. Ones with nobody recognized "
        "nearby come first — those are the ones worth looking at. After "
        "labeling, the card fades and disappears on the next load.",
    # {score} kommt vorformatiert (:.2f) aus der Route (Format-Regel §8.8).
    "ereignisliste.offen.frigate_mit": "Frigate: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate: —",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "faces".
    "ereignisliste.offen.zeile_faces": "{n} faces · best: {beste}",
    "ereignisliste.offen.link_video": "Video",
    "ereignisliste.offen.kontext_erkannt":
        "recognized in the same time window: {wer}",
    "ereignisliste.offen.kontext_fehlt": "no confirmed recognition nearby",
    "ereignisliste.blaettern.neuer": "← newer",
    "ereignisliste.blaettern.aelter": "older →",
    "ereignisliste.offen.blaettern_stand": "Page {seite}/{max} ({n} open)",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} weak-face event hidden — likely no usable face (nothing "
        "confirmed nearby either).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} weak-face events hidden — likely no usable face (nothing "
        "confirmed nearby either).",
    "ereignisliste.offen.schwach_zeigen": "show them",
    "ereignisliste.offen.schwach_alle":
        "showing weak-face events too —",
    "ereignisliste.offen.schwach_zurueck": "back to the worthwhile ones",
    "ereignisliste.offen.leer_titel": "Nothing open — everything labeled.",
    "ereignisliste.offen.leer_hinweis":
        "New unconfirmed events with faces appear here automatically.",
    "ereignisliste.titel": "Events",
    "ereignisliste.filter.alle_areas": "all areas",
    "ereignisliste.filter.alle_kameras": "all cameras",
    "ereignisliste.filter.alle_personen": "all persons",
    "ereignisliste.filter.alle_kategorien": "all categories",
    "ereignisliste.filter.knopf": "Filter",
    "ereignisliste.filter.reset": "reset",
    "ereignisliste.tabelle.blaettern_stand":
        "Page {seite}/{max} ({n} events)",
    "ereignisliste.tabelle.kopf_zeit": "Time",
    "ereignisliste.tabelle.kopf_kamera": "Camera",
    "ereignisliste.tabelle.kopf_kategorie": "Category",
    "ereignisliste.tabelle.kopf_crop": "Crop",
    "ereignisliste.tabelle.kopf_gt": "Confirm or correct (GT)",
    # {score} vorformatiert; {cos} bleibt roh (Original druckt auch None).
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "log",
    "ereignisliste.tabelle.link_video": "video",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "clip incomplete — judged from the readable part",
    "ereignisliste.tabelle.attr_kein_crop":
        "no usable face was kept for this event",
    # ------------------------------------------- routes/konfiguration ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Status-Zeile
    # 'status: <b>armed</b> — runs by itself' und die drei Absaetze mit
    # <a>-Links mitten im Satz (Kopf-Absatz, Kette-Blatt-Rest, Fussnote
    # Cameras-Seite) tragen Inline-Markup (t_html-Weg spaeterer Stufen);
    # die Whitelist-Erklaertexte und auto_hinweis-Saetze kommen als
    # Parameter vom Dienst (eigene Tranche); Parametergrenzen ({lo}–{hi})
    # und Read-only-Werte sind Daten. Das Config-Token
    # "nur_wenn_gesicht_leer" im Ketten-Satz bleibt in jeder Sprache
    # wortgleich (§8.7).
    "konfiguration.kette.gesicht_titel": "Face",
    "konfiguration.kette.gesicht_kosten":
        "base analysis on the recorded clip — always on",
    "konfiguration.kette.gesicht_zeitpunkt": "per event",
    "konfiguration.kette.person_titel": "Person (body)",
    "konfiguration.kette.person_kosten":
        "the most expensive local step (body embedding on your hardware)",
    "konfiguration.kette.person_zeitpunkt":
        "per event, decided on the walk-through verdict",
    "konfiguration.kette.vision_titel": "Vision",
    "konfiguration.kette.vision_kosten":
        "one request per walk-through to your configured vision endpoint",
    "konfiguration.kette.vision_zeitpunkt": "at the end of the walk-through",
    "konfiguration.kette.immer_an": "always",
    "konfiguration.kette.immer_hinweis": "(not switchable today)",
    "konfiguration.kette.gesicht_erkl":
        "the face path is the backbone of every analysis — person and "
        "vision hang off its walk-through verdict",
    "konfiguration.kette.grund_person": "no trained person model armed yet",
    "konfiguration.kette.grund_vision": "vision detect is switched off",
    "konfiguration.kette.grund_aus": "switched off here",
    "konfiguration.kette.status_aus": "status: not running ({grund})",
    "konfiguration.kette.zeile_kosten": "cost: {kosten}",
    "konfiguration.kette.titel": "Recognition chain",
    "konfiguration.kette.satz":
        "Which recognizers run, and in which order. The condition "
        "\"nur_wenn_gesicht_leer\" means: the step only runs when the face "
        "path could NOT confirm everyone on the walk-through — decided on "
        "the whole pass, never on a single event. Changing the order "
        "itself is a later stage; today the chain always starts with the "
        "face path.",
    "konfiguration.knopf_speichern": "Save + restart",
    "konfiguration.kette_blatt.hinweis":
        "Changes are audited (config_audit.jsonl); after saving, the "
        "service restarts cleanly.",
    "antwort.support_token_neu": "new support token created — the old one is invalid; copy it now, it is shown only this once",
    "konfiguration.support.titel": "Remote support access",
    "konfiguration.support.satz": "Read-only download of named areas (logs, masked config, faces, learning runs, body material, state files) for whoever holds the support token. The on/off switch support_zugriff sits in the table below, default off. Every request is written to the service log. The face and body areas contain pictures of real people — hand the token out with care. Without TLS in front of this service the token travels in plain text.",
    "konfiguration.support.token_gesetzt": "A support token is set.",
    "konfiguration.support.token_fehlt": "No support token yet.",
    "konfiguration.support.knopf_token": "Create new token",
    "konfiguration.support.einmal_hinweis": "The token appears here exactly once after creation — store it; afterwards only ••• is shown.",
    "konfiguration.titel": "Advanced settings",
    "konfiguration.kopf.satz1":
        "Changes are audited (config_audit.jsonl); after saving, the "
        "service restarts cleanly (it waits for a running analysis to "
        "finish).",
    "konfiguration.feld.option_an": "on",
    "konfiguration.feld.option_aus": "off",
    "konfiguration.frigate_auth.titel": "Frigate login (optional)",
    "konfiguration.frigate_auth.satz":
        "Only needed if your Frigate asks for a login \u2014 that is the case on its "
        "authenticated port (8971), not on the internal one (5000). Leave both fields "
        "empty and nothing changes: suslik talks to Frigate exactly as it does today.",
    "konfiguration.frigate_auth.erkl_user":
        "user name of a Frigate account. Empty = no login at all; emptying it also "
        "clears the stored password",
    "konfiguration.frigate_auth.erkl_password":
        "password for that account. It is stored with your other settings under "
        "/data and never shown again \u2014 leave the field blank to keep it",
    "konfiguration.frigate_auth.erkl_tls":
        "check Frigate's TLS certificate. Frigate's authenticated port ships with a "
        "self-signed certificate, so turn this off if you connect to it by https and "
        "have not replaced that certificate",
    "konfiguration.frigate_auth.pw_gesetzt": "stored \u2014 leave blank to keep it",
    "konfiguration.frigate_auth.pw_leer": "no password stored",
    "konfiguration.abschnitt_alle": "All parameters",
    "konfiguration.tabelle.kopf_parameter": "Parameter",
    "konfiguration.tabelle.kopf_wert": "Value",
    "konfiguration.tabelle.kopf_bedeutung": "Meaning",
    "konfiguration.knopf_setup": "Re-run setup wizard",
    "konfiguration.abschnitt_readonly": "Read-only (console/yaml)",
    # ----------------------------------------------- routes/lernanker ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Pills mit <b> mitten
    # im Satz (adopted as <b>X</b> …, named <b>X</b> …, looks like <b>X</b>
    # …) und die Kaputt-Warnzeile (<b>-Satzteil) tragen Inline-Markup
    # (t_html-Weg spaeterer Stufen; die _bek-Halbsaetze darin sind schon
    # Schluessel); die JS-Texte mit \u-/\n-Escape-Folgen warten auf
    # window.T (Stufe 1) — nur die drei escape-freien JS-Kurztexte sind
    # nach dem frigate.js-Muster eingezogen. Eimer-/Bin-Tokens bleiben
    # unberuehrt, nur ihre Anzeige-Map ist Schluessel (Funktion statt
    # Modul-Konstante, t() zur Render-Zeit). "(s)"-Klammer-Plurale sind
    # Byte-Treue zum Original, kein t_n.
    "lernanker.eimer.ok": "clean",
    "lernanker.eimer.unbestaetigt": "unconfirmed",
    "lernanker.eimer.zu_duenn": "thin",
    "lernanker.eimer.hart": "mixed",
    "lernanker.bin.frontal": "Frontal",
    "lernanker.bin.links": "Looking left",
    "lernanker.bin.rechts": "Looking right",
    # {kamera} kommt je Kontext vorbehandelt aus der Route (attr_clip:
    # einzeln escaped; attr_kurz: Gesamtwert wird danach escaped).
    "lernanker.kachel.attr_clip": "{kamera} · det {det} · click opens the clip",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "open the clip",
    "lernanker.kachel.grund_fehlt": "not rated",
    "lernanker.detail.gruppe": "Group {pos} of {gesamt}",
    "lernanker.detail.frage": "Who is this?",
    "lernanker.badge.stuetz": "{n} faces ({phys} physical)",
    "lernanker.badge.faces": "{n} faces",
    "lernanker.badge.durchgaenge": "{n} passes",
    "lernanker.badge.tage": "{n} day(s): {spanne}",
    "lernanker.badge.marge": "margin {marge}",
    "lernanker.link_zurueck": "back to all clusters",
    "lernanker.detail.hinweis_klick": "click a face to open its clip",
    "lernanker.detail.hinweis_auswahl":
        "click an image to select or deselect it",
    "lernanker.detail.hinweis_pfeil": "the little &#9654; opens the clip",
    "lernanker.detail.weiter": "Next group &#8230;",
    "lernanker.detail.pflege_hinweis":
        "reference upkeep lives on the Quality page",
    "lernanker.detail.verworfen":
        "deleted by you — the pictures are gone; the group stays listed here as a record only",
    "lernanker.detail.dublette_hinweis":
        "duplicate check unavailable (anchor predates embedding "
        "persistence) — physical duplicates are still filtered",
    "lernanker.bekannt.system": "already in your system",
    "lernanker.bekannt.anker": "named on another cluster",
    "lernanker.detail.empfohlen": "Recommended — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Not recommended ({n}) — kept visible, reason on each image",
    # .373: die uebernommene Gruppe beschriftet, was sie aufteilt — die
    # DAMALIGE Auswahl. Kein Empfehlungs-Wort (die frische Rechnung kennt das
    # Urteil der Gruppen-Flaeche nicht) und kein Grund-Versprechen (der Grund
    # von damals ist nirgends festgehalten).
    "lernanker.detail.gewaehlt": "Selected — {bin} ({n})",
    "lernanker.detail.nicht_gewaehlt": "Not selected ({n}) — kept visible",
    # .373: die Rueckstufungs-Gruende der Empfehlung. Kennungen kommen aus
    # core.benennung.GRUND_WERTE (die eine Quelle), eingesetzt werden sie in
    # routes/lernanker._grund_text — vorher standen diese Saetze als englische
    # Literale in der Rechnung und erschienen in JEDER Oberflaechen-Sprache.
    "lernanker.grund.bildpruefung": "did not pass the picture check",
    "lernanker.grund.zu_dunkel": "too dark (brightness {luma} — needs {min}+)",
    "lernanker.grund.ueberbelichtet":
        "overexposed (brightness {luma} — needs {max} or less)",
    "lernanker.grund.dublette_phys":
        "duplicate detection (same camera and box)",
    "lernanker.grund.fast_gleich": "near-identical to {datei}",
    "lernanker.grund.bin_limit": "bin limit reached ({k} kept)",
    "lernanker.detail.skip_weiter": "Skip this group",
    "lernanker.detail.skip_zurueck": "Skip — back to the groups",
    "lernanker.detail.knopf_ja": "Yes, it&rsquo;s {name}",
    "lernanker.detail.knopf_andere": "Someone else &#8230;",
    "lernanker.detail.knopf_benennen_easy": "Name this group &#8230;",
    "lernanker.detail.knopf_alle": "Select all recommended",
    "lernanker.detail.knopf_keine": "Deselect all",
    "lernanker.detail.attr_name": "person name (new or existing)",
    "lernanker.detail.knopf_benennen": "Name this cluster",
    "lernanker.detail.knopf_adopt": "Adopt into recognition",
    "lernanker.js.fehler": "error:",
    "lernanker.js.nicht_uebernommen": "not adopted",
    "lernanker.js.nicht_gespeichert": "not saved",
    "lernanker.liste.frage_lauf":
        "Delete run {lid} and all its data? This permanently removes its "
        "{n} cluster(s) — including named and dismissed ones — and all "
        "harvested images. References already adopted into recognition "
        "stay. This cannot be undone.",
    "lernanker.liste.frage_alle":
        "Delete ALL {alt} old run(s) with their {n} cluster(s) and all "
        "harvested images? Only the newest run {neuester} is kept. "
        "References already adopted into recognition stay. This cannot "
        "be undone.",
    "lernanker.liste.knopf_alte": "Delete all old runs (keep {neuester})",
    "lernanker.liste.lauf_zeile":
        "Delete a run — permanently removes all its clusters and "
        "harvested images (references you already adopted stay):",
    "lernanker.liste.verworfen":
        "{n} group(s) deleted by you (pictures gone, kept as a record only)",
    "lernanker.titel": "Anchor clusters",
    "lernanker.liste.leer":
        "No anchors yet — a learning run builds them (Preparation → "
        "Harvest → Grouping).",
    "lernanker.liste.leer_link": "Open the learning run page",
    "lernanker.liste.kopf":
        "{n} clusters from {ges} anchor-ready faces — {ok} clean, {rest} "
        "for review (dimmed, with the reason on the badge). Open a "
        "cluster to review and name it — named clusters are adopted into "
        "recognition right there (Adopt button).",
    "lernanker.liste.kopf_link": "Back to the learning run",
    "lernanker.liste.mehr": "+{n} more faces",
    "lernanker.liste.dublette":
        "same cluster as {anker} — harvested again by a newer run; "
        "name it there",
    "lernanker.liste.knopf_review": "Review naming",
    "lernanker.liste.knopf_view": "View cluster",
    "lernanker.liste.knopf_benennen": "Name these {n} faces",
    "lernanker.liste.frage_verwerfen":
        "Delete this group? Its pictures are removed. This cannot be undone.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Delete this group? Its pictures are removed and the pending naming is discarded. This cannot be undone.",
    "lernanker.liste.knopf_verwerfen": "Delete",
    # ---------------------------------------------- routes/syncauswahl ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): FR_AUS_HINWEIS kommt aus
    # sync_refs (zentrale Quelle, eigene Tranche); die Satzreste mit
    # <a>-Link mitten im Satz (Read-only-Karte, "… more (full list in the
    # diagnosis)") bleiben literal; die Zaehler-Hauptzeile beginnt nach
    # der <b>-Zahl (Split an der Markup-Grenze — neue Gattung §8).
    "syncauswahl.titel": "Review &amp; sync — references to Frigate",
    "syncauswahl.kopf.satz":
        "Frigate runs every uploaded reference through its own face "
        "detector and refuses images it finds no face in. This page checks "
        "the same thing first, shows you every candidate, and sends only "
        "what you tick.",
    "syncauswahl.fehler.titel": "Candidates not available",
    "syncauswahl.fehler.satz":
        "The candidate list needs a reachable Frigate — its face library "
        "is one half of the comparison.",
    "syncauswahl.link_diagnose_auf": "open the diagnosis",
    "syncauswahl.link_diagnose": "diagnosis",
    "syncauswahl.link_system": "back to System",
    "syncauswahl.kachel.frigate_abgelehnt": "Frigate rejected: {fehler}",
    "syncauswahl.kachel.pruefe": "checking …",
    "syncauswahl.kachel.vorpruefung_ok": "pre-check ok",
    "syncauswahl.kachel.wohl_abgelehnt":
        "would likely be rejected: {grund}",
    "syncauswahl.kachel.kein_gesicht": "no face detectable",
    "syncauswahl.kachel.kein_grund": "no reason given",
    "syncauswahl.kachel.senden": "send",
    "syncauswahl.kachel.knopf_skip": "skip",
    "syncauswahl.kachel.attr_skip":
        "Never send this image — remembered, the automatic sync skips "
        "it too",
    "syncauswahl.kachel.knopf_restore": "restore",
    "syncauswahl.kachel.attr_restore":
        "Put this image back on the candidate list",
    "syncauswahl.geloescht.satz_import":
        "came from Frigate and is gone there now",
    "syncauswahl.geloescht.satz_export":
        "was sent under this exact name and is gone there now",
    "syncauswahl.geloescht.badge": "deleted in Frigate",
    "syncauswahl.knopf_anbieten": "offer again",
    "syncauswahl.geloescht.attr_anbieten":
        "Put it back on the candidate list — the next sync (manual or "
        "automatic) sends it again",
    "syncauswahl.geloescht.knopf_respekt": "respect the deletion",
    "syncauswahl.geloescht.attr_respekt":
        "Remember that this image should stay out of Frigate",
    "syncauswahl.api.badge": "{person} — sent earlier",
    "syncauswahl.api.attr_anbieten":
        "Put it back on the candidate list (sends a second copy if "
        "Frigate still has the first one)",
    "syncauswahl.fr.titel_unbekannt": "Frigate face recognition: unknown",
    "syncauswahl.fr.satz_unbekannt":
        "suslik could not read it from Frigate just now — {detail}. "
        "Sending may still work; Frigate has the last word either way.",
    "syncauswahl.fr.titel_an": "Frigate face recognition: on",
    "syncauswahl.fr.satz_an":
        "(read from Frigate as this page loaded) — it accepts reference "
        "uploads.",
    "syncauswahl.fr.titel_aus": "Frigate face recognition: off",
    "syncauswahl.bilanz.titel": "Balance",
    "syncauswahl.bilanz.hauptzeile":
        "reference images · {beide} already in Frigate · {bereit} ready "
        "to transfer",
    "syncauswahl.bilanz.abgelehnt": "{n} rejected by Frigate",
    "syncauswahl.bilanz.geloescht": "{n} deleted in Frigate",
    "syncauswahl.bilanz.exportiert":
        "{n} sent earlier (Frigate renamed them)",
    "syncauswahl.bilanz.abgewaehlt": "{n} deselected",
    "syncauswahl.bilanz.vorrat": "{n} stock reference(s) local only (embedding-based, not transferable)",
    "syncauswahl.bilanz.nur_frigate": "{n} only in Frigate",
    "syncauswahl.bilanz.je_person": "In Frigate, per person:",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "syncauswahl.bilanz.kandidaten.eins": "{n} candidate",
    "syncauswahl.bilanz.kandidaten.viele": "{n} candidates",
    "syncauswahl.bilanz.vorpruefung": "{n} pass the pre-check",
    "syncauswahl.bilanz.gewaehlt_wort": "selected",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "{n} would likely be rejected by Frigate (unticked, but you can "
        "still send them).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "{n} were rejected by Frigate before (unticked; ticking one "
        "tries it again).",
    "syncauswahl.pruef.fehler":
        "pre-check could not run: {fehler} — images without a verdict "
        "stay selected.",
    "syncauswahl.pruef.laeuft.eins":
        "checking {n} image … {fertig}/{gesamt} (this page reloads when "
        "it is done)",
    "syncauswahl.pruef.laeuft.viele":
        "checking {n} images … {fertig}/{gesamt} (this page reloads when "
        "it is done)",
    "syncauswahl.sperre.titel": "Read-only mode is on",
    "syncauswahl.sperre.satz":
        "suslik does not write to Frigate right now.",
    "syncauswahl.knopf_alle": "Select all",
    "syncauswahl.knopf_keine": "Deselect all",
    "syncauswahl.knopf_transfer": "Transfer {n} selected to Frigate",
    "syncauswahl.leer.titel": "Nothing to send",
    "syncauswahl.leer.satz":
        "Every reference either already reached Frigate or is deselected.",
    "syncauswahl.leer.zusatz":
        "The sections below list what cannot simply be transferred.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} likely rejected",
    "syncauswahl.gruppe.prueft": "{n} still checking",
    "syncauswahl.geloescht.zusatz": "— your decision",
    "syncauswahl.geloescht.satz":
        "These are still in your library, but Frigate no longer has them "
        "under the name they were stored with. suslik never re-sends them "
        "without your decision: deleting a face in Frigate can be "
        "deliberate. Offer it again to make it a normal candidate — from "
        "then on the next sync, including the automatic one, uploads it. "
        "Respect the deletion to keep it out for good.",
    "syncauswahl.aufklapp": "— show",
    "syncauswahl.api.titel":
        "{n} exported earlier — Frigate keeps these under its own names",
    "syncauswahl.api.satz":
        "These went up through Frigate's API, and Frigate renames every "
        "reference it accepts. suslik therefore cannot tell by name "
        "whether they are still there — no count on this page can prove "
        "it either way. Nothing is re-sent automatically; if you know one "
        "is missing, offer it again (that sends a second copy if the "
        "first one is still there).",
    "syncauswahl.api.vergleich":
        "{person}: {n} sent this way · Frigate currently holds {bestand} "
        "images",
    "syncauswahl.import.zeile.eins": "{n} image:",
    "syncauswahl.import.zeile.viele": "{n} images:",
    "syncauswahl.import.mehr": "… and {n} more",
    "syncauswahl.import.satz":
        "Frigate has these reference images, suslik does not. Importing "
        "copies them into your library; nothing in Frigate changes.",
    "syncauswahl.import.warnung":
        "This list may include your own uploads: Frigate renames every "
        "reference it accepts, so suslik cannot tell them apart from "
        "faces you added in Frigate directly. Importing those back would "
        "duplicate content.",
    "syncauswahl.import.knopf": "Import them into suslik",
    "syncauswahl.raus.satz":
        "Remembered on purpose: these stay in your library but are never "
        "sent to Frigate, not even by the automatic sync. Restore puts "
        "one back on the candidate list.",
    "syncauswahl.alter.unbekannt": "age unknown",
    "syncauswahl.alter.sekunden": "{s} s ago",
    "syncauswahl.alter.minuten": "{m} min ago",
    "syncauswahl.alter.stunden": "{h} h {m} min ago",
    "syncauswahl.ergebnis.titel": "Last transfer",
    "syncauswahl.ergebnis.stopp": "stopped:",
    "syncauswahl.ergebnis.wand":
        "same error three times in a row: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "uploaded — {bild}",
    "syncauswahl.ergebnis.zaehler": "{hoch} uploaded · {weg} not accepted",
    "syncauswahl.ergebnis.auswahl": "of {n} selected",
    "syncauswahl.ergebnis.uebersprungen": "{n} deselected (skipped)",
    "syncauswahl.ergebnis.dauer": "took {n} s",
    # ---------------------------------------------------- routes/live ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): drei Saetze mit
    # <b>Measure load</b> bzw. <a>-Link mitten im Satz (Messung-fehlt-
    # Zeile, CPU-Sperrkarten-Rest, Aufloesungs-Absatz, Credentials-Zeile,
    # Erklaer-Satz 2) bleiben literal; die Kanal-Haekchen pushover/
    # telegram/mqtt und "(detect)" sind Anzeige==Kennung (Vergleichs-/
    # Ersetzungs-Token) und bleiben literal; LIVE_ZUSTAENDE-Labels kommen
    # aus core/registry (zentrale Quelle, eigene Tranche); GRUPPEN behaelt
    # seine EN-Literale als Kennungs-Kontrakt (harnisch_live1), die
    # Anzeige laeuft ueber die live.gruppe.*-Schluessel; die unbenutzte
    # Modul-Konstante _PHASEN bleibt unberuehrt. Zahlen wie 199–801 ms
    # und {tage}/{mb}/{kerne} kommen vorformatiert aus der Route (§8.8).
    "live.hinweis_gpu":
        "Works with a GPU only for now — we are working on a CPU option "
        "but can't promise it.",
    "live.hinweis_cpu":
        "CPU mode: watchers are expensive here — the quick check "
        "typically takes 1–2 s (a GPU build reacts in under a second), "
        "and additional watchers slow each other down. How many you run "
        "is your call; we recommend starting with one.",
    "live.zeile.alter": "({tage} day(s) old)",
    "live.test.zeile":
        "source test {wann}: {aufloesung} → {skala}, {bilder_s} frames/s",
    "live.test.durchsatz":
        "(throughput, not delivery rate — rerun the source test)",
    "live.test.provider": "provider {provider}",
    "live.test.sw": "(software decode)",
    "live.test.entwertet": "— INVALIDATED: source changed since this test",
    "live.test.veraltet_bitte":
        "This check is {tage} days old — run the source test again so the "
        "numbers describe what the camera delivers today.",
    "live.test.fehlgeschlagen":
        "last source test FAILED ({wann}): {fehler}",
    "live.messung.zeile": "load measured on {wann}: {text}",
    "live.messung.veraltet":
        "— STALE: source changed since this measurement, measure again",
    "live.messung.fehlgeschlagen":
        "last load measurement FAILED ({wann}): {fehler}",
    "live.zaehler.auftritte": "{n} appearances",
    "live.zaehler.trigger": "{n} triggers",
    "live.zaehler.alerts": "{n} alerts",
    "live.zaehler.letzter": "last trigger {zeit}",
    "live.zaehler.kopf": "since engine start:",
    "live.engine.titel_aus": "Live engine: not running",
    "live.engine.satz_aus":
        "No heartbeat from the engine process. Tiles show the saved "
        "configuration; enabling, testing against a running watcher and "
        "load measurements need the engine — the service starts it "
        "automatically once at least one watcher is enabled.",
    "live.engine.cpu_mit_limit":
        "suslik CPU right now: {kerne} of {limit} allowed cores (whole "
        "container: watchers, analysis, service)",
    "live.engine.cpu_ohne_limit":
        "suslik CPU right now: {kerne} cores (whole container: watchers, "
        "analysis, service)",
    "live.engine.rss": "engine RSS {rss} MB",
    "live.engine.grundkosten": "base cost {mb} MB",
    "live.engine.je_stream": "{mb} MB per stream ({quelle})",
    "live.engine.je_stream_fehlt":
        "per-stream RAM not yet measured on this machine",
    "live.engine.ram_frei": "{mb} MB RAM free ({quelle})",
    "live.engine.ram_unlesbar": "RAM: no container limit readable",
    "live.engine.detektor": "detector {ms} ms/frame ({quelle})",
    "live.engine.drossel":
        "throttle level {stufe}, utilization {auslastung}",
    "live.engine.rest":
        "after one more stream: ~{mb} MB RAM would remain",
    "live.engine.rest_warnung":
        "— BELOW the safety floor, no further slot",
    "live.engine.kapazitaet":
        "capacity: up to {n} watcher(s) (hard cap {hart}) — limited by: "
        "{grund}",
    "live.engine.hart": "hard cap {hart} watchers",
    "live.engine.titel_standalone":
        "Live engine: running (standalone engine detected)",
    "live.engine.titel_an": "Live engine: running",
    "live.gruppe.laufend": "Running",
    "live.gruppe.bereit": "Ready",
    "live.gruppe.rest": "Not set up",
    "live.gruppe.versteckt": "Hidden",
    "live.gruppe.ohne_area": "No area",
    "live.kachel.attr_fremd":
        "configured here, but this camera is not in Frigate right now",
    "live.kachel.pill_fremd": "not in Frigate",
    "live.kachel.attr_detect":
        "Frigate detect stream — the real stream resolution appears "
        "after the service probes the stream or a source test runs",
    "live.knopf_konfigurieren": "Configure",
    "live.knopf_test": "Run source test",
    "live.knopf_messung": "Measure load",
    "live.knopf_enable": "Enable",
    "live.knopf_disable": "Disable",
    "live.knopf_zeigen": "Show",
    "live.knopf_verstecken": "Hide",
    "live.banner.kameraliste":
        "Could not read the Frigate camera list: {fehler}",
    "live.schalter.ungruppiert": "ungrouped view",
    "live.schalter.area": "group by area",
    "live.sperre.cpu_titel": "CPU mode",
    "live.sperre.titel": "Not available on this build",
    "live.sperre.satz":
        "Live watchers require a GPU build — integrated Intel graphics "
        "(gpu / gpu-legacy images), an NVIDIA card (cuda image) or an "
        "AMD card (rocm image) all qualify.",
    "live.sperre.cpu_only":
        "They are not available on the CPU-only image.",
    "live.erklaer.titel":
        "Live watchers — instant reaction at the camera stream",
    "live.erklaer.satz1":
        "A live watcher connects straight to one camera stream and "
        "reacts while the person is still in the picture: the first face "
        "starts a check, and after the configured number of consistent "
        "detections a verified signal goes out — the goal is under one "
        "second (measured 199–801 ms on the reference setup). Use it to "
        "trigger home automations, e.g. via MQTT.",
    "live.erklaer.link": "Read more: how live watchers work",
    "live.titel": "Live watchers",
    "live.leer.titel": "No cameras found.",
    "live.leer.hinweis":
        "Configure the Frigate connection first — tiles appear per "
        "camera.",
    "live.knopf_speichern": "Save",
    "live.detail.titel": "Live watcher — {name}",
    "live.abschnitt.quelle": "Source",
    "live.quelle.proxy": "go2rtc restream via Frigate (default, recommended)",
    "live.quelle.direct": "camera producer URL discovered via go2rtc",
    "live.quelle.url": "a stream URL you enter yourself",
    "live.detail.url_label": "Stream URL (source 'url' only):",
    "live.detail.url_hinweis":
        "credentials in the URL are masked everywhere they are shown — "
        "leave the field as shown to keep the saved URL, or paste a "
        "new one",
    "live.detail.quelle_hinweis":
        "Changing the source invalidates the source test — run it again "
        "before enabling.",
    "live.abschnitt.aufloesung": "Processing resolution",
    "live.hoehe.default": "default (1080p)",
    "live.hoehe.h360": "360p — weak-GPU fallback, latest name fire (measured)",
    "live.hoehe.h720": "720p — lighter decode, name fires later",
    "live.hoehe.h1080":
        "1080p — sweet spot (measured: name ~2.4 s earlier than 720p)",
    "live.hoehe.alt_hinweis":
        "Saved: {alt}p. That step was dropped (measured: no gain over "
        "{jetzt}p) — this watcher runs at {jetzt}p. The saved value and the "
        "source test stay valid; pick a new step to change it.",
    "live.abschnitt.alarm": "Alarm chain",
    "live.detail.ende_label": "End after no face (s):",
    "live.detail.ende_hinweis":
        "an appearance ends after this many seconds without a face "
        "(3–120)",
    "live.detail.scharf_label": "Re-armed after (s):",
    "live.detail.scharf_hinweis":
        "minimum seconds between alerts — with someone present it alerts "
        "again after this time; 0 = every trigger alerts (0–3600)",
    "live.abschnitt.kanaele": "Notification channels",
    "live.detail.namensschaetzung":
        "Alerts include a preliminary name guess (\"probably X\") when "
        "the face matches a known person — never stored, never used for "
        "learning.",
    "live.abschnitt.test": "Test &amp; measure",
    "live.detail.gesperrt_hinweis":
        "testing and measuring are unavailable while live watching is "
        "locked on this machine — the note at the top of this page "
        "explains why.",
    "live.knopf_messung_lang": "Measure load (15–30 s)",
    "live.detail.messung_hinweis":
        "the load measurement pauses the other watchers while it runs",
    "live.detail.link_zurueck": "back to overview",
    "live.detail.kein_bild": "No live picture — this watcher is not running.",
    "live.detail.kein_bild_test":
        "Last source test saw {aufloesung}, processed as {skala}.",
    "live.detail.kein_bild_ohne_test":
        "No source test has run yet, so nothing is known about this feed.",
    # --- Live-Umbau 31.08.: die Konfigseite eines Waechters traegt jetzt
    # Kacheln statt einer Kartenspalte, und alles Neue ist JE KAMERA
    # einstellbar (die Guete-Skalen sind kameraabhaengig — gemessen).
    "live.abschnitt.erkennung": "Recognition",
    "live.abschnitt.melden": "Alerting",
    "live.abschnitt.frigate": "Frigate events",
    "live.abschnitt.erweitert": "Advanced settings",
    "live.abschnitt.abtastung": "Sampling",
    "live.abtastung.schalter": "Only look closely when something moves",
    "live.abtastung.erklaerung":
        "Face detection is what costs — a cheap motion check on the "
        "brightness plane decides whether a frame is worth it. While a "
        "person is being tracked the watcher always runs at full rate; only "
        "a quiet scene is sampled less often.",
    "live.abtastung.ruhe_label": "Look anyway every",
    "live.abtastung.ruhe_einheit": "s",
    "live.abtastung.ruhe_hinweis":
        "Leave empty to use this camera's appearance-end time — someone "
        "standing perfectly still creates no motion, so the watcher takes a "
        "look now and then anyway (1–600 s).",
    "live.abtastung.schwelle_label": "Sensitivity (grey-level change):",
    "live.abtastung.flaeche_label": "smallest area:",
    "live.abtastung.eich_hinweis":
        "Leave both empty for Frigate's shipping values. Lower sensitivity or "
        "a smaller area makes the watcher look more often; higher values keep "
        "it quiet on a windy hedge. Every site is different — these belong to "
        "this camera, not to the whole system.",
    "live.abschnitt.guete": "Picture quality thresholds",
    "live.abschnitt.last": "Load measurement",
    "live.erkennung.det_zeile":
        "A find counts as a face from a detection score of {wert} up{marke}.",
    "live.erkennung.det_vorgabe": " (default)",
    "live.erkennung.regel_vor": "Recognized after",
    "live.erkennung.regel_mitte": "confirmations within",
    "live.erkennung.regel_nach": "seconds",
    "live.erkennung.regel_hinweis":
        "0 seconds means the whole appearance counts, which is how it worked "
        "before. A time window helps on cameras where someone stands around "
        "for minutes and two lucky hits far apart should not count as one "
        "recognition.",
    "live.erkennung.vorrat_zeile":
        "Calibration samples: {n} of {deckel} kept — one picture per "
        "appearance, the oldest drop out.",
    "live.erkennung.vorrat_aus":
        "Sample collection is off, so the calibration page has nothing to "
        "show (System page, \"live_kalib_max\").",
    "live.erkennung.latte_e": "picture impression from {wert}",
    "live.erkennung.latte_t": "recognisability from {wert}",
    "live.erkennung.latte_aus": "not set",
    "live.erkennung.latte_hinweis":
        "These two never decide WHO is recognized — that would cost "
        "confirmations. They decide which picture goes into the alert and "
        "which faces are kept as calibration samples. Set them on the "
        "calibration page, where you can see the pictures.",
    "live.knopf_kalibrieren": "Calibrate",
    "live.knopf_vorrat_leeren": "Clear samples",
    "live.frigate.schalter": "Create a Frigate event when someone is recognized",
    "live.frigate.erklaerung":
        "Off by default. When on, this watcher writes its own event into "
        "Frigate with the name in the sub label \u2014 your own recording, "
        "independent of Frigate\u2019s detection. Writing runs in the "
        "background: the watcher never waits for Frigate. Nothing is written "
        "while read-only mode is on.",
    "live.frigate.abstand_label": "At most one event per person every (s):",
    "live.frigate.abstand_hinweis":
        "Empty means: the same distance you set above for alerts. The limit "
        "counts per person, so two different people can be written at the "
        "same time.",
    "livekalib.titel": "Camera calibration — {name}",
    "livekalib.erklaerung":
        "These are real faces this camera collected \u2014 one picture per "
        "appearance. Drag the sliders until the selection looks right to you, "
        "then apply. The values are saved for THIS camera only, because the "
        "quality scales differ from camera to camera.",
    "livekalib.regler_det": "Detection score",
    "livekalib.regler_det_prosa":
        "From here on a find counts as a face at all. This one really does "
        "steer the recognition: everything below never reaches the name "
        "check. Lower keeps more material (measured: a high bar threw away "
        "half of the usable material); higher keeps hedges and light patches "
        "out.",
    "livekalib.regler_e": "Picture impression",
    "livekalib.regler_e_prosa":
        "How clean and bright the picture looks to the eye. This does NOT "
        "decide who is recognized \u2014 it decides which picture goes into "
        "the alert and which faces are kept here as samples.",
    "livekalib.regler_t": "Recognisability",
    "livekalib.regler_t_prosa":
        "How well the person can be made out, half-covered faces included. "
        "Like the one above: it picks the picture and fills this page, it "
        "never sorts anybody out of the recognition.",
    "livekalib.ohne_guete":
        "The two quality models are missing in this build, so these samples "
        "carry no quality figures and the two lower sliders have no effect "
        "here. The detection score works.",
    "livekalib.standard": "Defaults",
    "livekalib.tab_erkennen": "Recognition",
    "livekalib.tab_lernen": "Face catalog",
    "livekalib.uebernehmen": "Apply",
    "livekalib.leer": "No samples yet. They arrive on their own — from a running watcher and from every event analysis of this camera, one face each. If you do not want to wait, use \"Look for fresh material\" below.",
    "livekalib.zurueck": "back to the watcher",
    "livekalib.js.genutzt": "{n} of {gesamt} samples pass",
    "livekalib.js.gespeichert": "saved",
    "livekalib.js.fehler": "error",
    # --- Kalibrier-Zentralumbau 31.08.: Abschnitte, Katalog-Latte, Material
    "livekalib.zur_uebersicht": "back to all cameras",
    "livekalib.abschnitt.anzeige": "Alerts, display and samples",
    "livekalib.abschnitt.anzeige_prosa": "These three decide which picture of this camera goes into an alert, and which faces are kept here as samples. They do not decide who is recognised.",
    "livekalib.abschnitt.katalog": "Catalogue bar",
    "livekalib.abschnitt.material": "Material",
    "livekalib.katalog.prosa": "A separate, stricter bar: how good a face of this camera has to look before it may become a stored reference. It applies wherever a picture enters the catalogue — naming an unknown group, adopting from a learning run, taking a suggestion.",
    "livekalib.katalog.grenze": "What it does not do: it never removes references you already have, and it never changes who is recognised. Pictures without quality scores (older material, or a build without the quality models) pass untouched — a bar without a measurement would discard blindly.",
    "livekalib.katalog.quelle_kamera": "In use: this camera's own values.",
    "livekalib.katalog.quelle_global": "In use: the global fallback — this camera has no own values yet.",
    "livekalib.katalog.quelle_aus": "No catalogue bar set: every picture may become a reference.",
    "livekalib.katalog.regler_e": "Catalogue: picture impression",
    "livekalib.katalog.regler_e_prosa": "Minimum picture impression for a reference of this camera. Keep it above the slider further up: what is good enough to show is not automatically good enough to learn from.",
    "livekalib.katalog.regler_t": "Catalogue: recognisability",
    "livekalib.katalog.regler_t_prosa": "Minimum recognisability for a reference of this camera. This is the one that keeps half-covered faces out of the catalogue.",
    "livekalib.material.aus": "Sample collection is switched off (Advanced, calibration samples). Without samples this page has nothing to show.",
    "livekalib.material.stand": "{n} of at most {deckel} samples stored",
    "livekalib.material.wann": "latest {wann}",
    "livekalib.material.fuellen_prosa": "Looking for fresh material works through the most recent person events of this camera and keeps the best face of each. It stops at {ziel} pictures or after {events} events, whichever comes first.",
    "livekalib.material.lauf": "Plus {n} picture(s) of this camera from the latest learning run — shown below and marked as such.",
    "livekalib.js.katalog": "{n} of {gesamt} would be allowed into the catalogue",
    "livekalib.js.lauf": "run",
    # ----------------------------------------------- routes/erkennung ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die ek-satz-Zeile der
    # Live-Kachel (<b>moment</b> mitten im Satz), der Expert-Status
    # "status: <b>armed</b> — runs by itself" (Muster konfiguration), die
    # Expert-Zeile der Gesichts-Kachel (zwei <a>-Links mitten im Satz),
    # der k_beweis-Trained-Zweig (drei <b>-Inseln + konditionale Anhaenge,
    # §8.10-Grenzfall), der Schluss-Absatz (zwei <a>-Links im Satz) und
    # der Fuss-Satz mit <b>back</b>. Die Unteroptions-Labels "Always"/
    # "Only if no face"/"If needed" sind Anzeige==Kennung (§8.2: das JS
    # ekUnterWert vergleicht den Button-TEXT gegen 'Always', um den
    # Config-Wert abzuleiten) und bleiben literal; die JS-Statustexte
    # ('changed — Save + restart applies it' u. a.) warten auf window.T
    # (Stufe 1). p_erkl/v_erkl sind Whitelist-DATEN mit [:180]-Slice —
    # Slice-vor-Format-Stelle (§8.14), nur markiert.
    "erkennung.titel": "Recognition",
    "erkennung.kopf.satz":
        "The four ways your system can recognize someone — each one is "
        "its own card: switch it, see that it works, set it up. The Live "
        "switch acts immediately; body and vision changes apply with "
        "Save + restart.",
    "erkennung.kipp.label": "Enabled",
    "erkennung.kipp.attr_verriegelt":
        "always on — every other method builds on the face verdict",
    "erkennung.link_how": "How it works &#8230;",
    "erkennung.live.titel": "Live watch",
    # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze, Fragmente
    # duerfen klein beginnen.
    "erkennung.live.beweis_prefix": "watching",
    "erkennung.live.beweis_zaehler": "{an} of {ges}",
    "erkennung.live.beweis_suffix": "set-up cameras",
    "erkennung.live.beweis_keine_laufend": "camera(s) set up, none running",
    "erkennung.live.beweis_keiner": "no watcher set up yet",
    "erkennung.live.expert_schalter":
        "switching off stops every running watcher; switching on starts "
        "all set-up watchers (the per-camera gate still applies)",
    "erkennung.live.link_prokamera": "per-camera control",
    "erkennung.live.knopf_kameras": "Choose cameras …",
    "erkennung.knopf_register_face": "Register face …",
    "erkennung.gesicht.titel": "Face recognition",
    "erkennung.gesicht.satz":
        "The most precise way: every pass is checked against the faces "
        "of the people you taught the system. It is the backbone — body "
        "and vision hang off its walk-through verdict, so it has no off "
        "switch today.",
    "erkennung.gesicht.beweis_personen": "{n} people",
    "erkennung.gesicht.beweis_bilder": "{n} reference images",
    "erkennung.gesicht.knopf_verwalten": "Manage people …",
    "erkennung.koerper.titel": "Body recognition",
    "erkennung.koerper.satz":
        "Recognizes household members even when no face is visible, by "
        "build and posture — it learns from the reviewed pictures by "
        "itself.",
    "erkennung.koerper.beweis_kein_modell":
        "no person model yet — learn and review first",
    "erkennung.status.kein_modell":
        "not running (no trained person model armed yet)",
    "erkennung.status.hier_aus": "not running (switched off here)",
    "erkennung.status.vision_aus":
        "not running (vision detect is switched off)",
    "erkennung.koerper.link_modell": "model status",
    "erkennung.koerper.knopf_status": "Model status …",
    "erkennung.koerper.knopf_register": "Register body …",
    "erkennung.vision.titel": "AI vision",
    "erkennung.vision.beta": "Beta",
    "erkennung.vision.satz":
        "A picture-AI as referee for the hard cases. Needs a model "
        "endpoint (local or paid) — every check costs requests.",
    "erkennung.vision.beweis_an": "endpoint connected",
    "erkennung.vision.beweis_aus": "no endpoint connected",
    "erkennung.vision.knopf_connect": "Connect a model …",
    "erkennung.vision.knopf_register": "Register vision …",
    "erkennung.abschnitt_property": "Property set-up",
    "erkennung.areas.titel": "Areas",
    "erkennung.areas.satz":
        "Where on the property counts: draw areas so alerts only fire "
        "where you care — the driveway matters, the street behind the "
        "fence does not.",
    "erkennung.areas.beweis_zahl": "area(s) defined",
    "erkennung.areas.beweis_keine": "no areas yet — everything counts",
    "erkennung.areas.knopf": "Manage areas &#8230;",
    "erkennung.knopf_speichern": "Save + restart",
    # --------------------------------------------------- routes/faces ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): der dim-Einleitungs-
    # Satz traegt einen <a>-Link mitten im Satz (t_html-Weg spaeterer
    # Stufen). Das Datumsformat %d.%m. %H:%M der Stand-Zeile bleibt in
    # der Route (B19/§8.9); {wann}/{n} kommen vorformatiert (§8.8).
    "faces.titel": "Faces",
    "faces.link_how": "How it works &#8230;",
    "faces.bekannt.titel": "Known people",
    "faces.bekannt.knopf_verwalten": "Manage people &#8230;",
    "faces.bekannt.knopf_register": "Register face &#8230;",
    "faces.bekannt.leer":
        "no people learned yet — register the first face above",
    # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
    "faces.bekannt.beweis_personen": "{n} people",
    "faces.bekannt.beweis_bilder": "{n} reference images",
    "faces.lernen.titel": "Learning",
    "faces.lernen.knopf_start": "Start learning &#8230;",
    "faces.lernen.knopf_review": "Review suggestions &#8230;",
    "faces.lernen.beweis_offen": "suggestion(s) waiting for review",
    "faces.lernen.beweis_leer":
        "nothing waiting — the system keeps collecting on its own",
    "faces.lernen.satz": "Review what the cameras collected.",
    "faces.unbekannt.titel": "Unknown",
    "faces.unbekannt.knopf": "Review unknown &#8230;",
    "faces.unbekannt.beweis_offen": "recurring unknown visitor(s)",
    "faces.unbekannt.beweis_leer": "no recurring unknown visitors",
    "faces.unbekannt.satz": "Visitors without a name yet.",
    "faces.qualitaet.titel": "Picture quality",
    "faces.qualitaet.stand": "last checked {wann} &middot; {n} finding(s)",
    # EIN Schluessel fuer Popup-Titel UND grossen Knopf (wortgleich im
    # Original — bewusste Wiederverwendung, kein Duplikat).
    "faces.qualitaet.knopf_check": "Quality-check my pictures",
    "faces.qualitaet.popup_satz":
        "Re-measures every reference picture (incl. its face quality) and "
        "looks for weak ones, near-duplicates and mixed-up faces. Takes a few "
        "minutes depending on the number of pictures and runs in the background.",
    "faces.qualitaet.label_alle": "All people",
    "faces.qualitaet.label_eine": "One person:",
    "faces.qualitaet.knopf_start": "Start check",
    "faces.qualitaet.knopf_abbrechen": "Cancel",
    "faces.qualitaet.knopf_ergebnisse": "Last results &#8230;",
    "faces.qualitaet.satz": "Finds weak or mixed-up pictures.",
    # ----------------------------------------------- routes/qualitaet ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): der Luecken-Block
    # ("no X and no Y yet …" — Satzteil-Splicing ueber " and no ".join,
    # §8.3), die filt-Zeile (showing only <b>X</b> + <a>-Link im Satz,
    # §8.1), der Ergebnis-Satz des Funde-Zweigs (", "/" and "-Join der
    # <b>-Zaehler-Fragmente, §8.3) und der JS-Text '" selected"' in
    # qgZaehl (window.T, Stufe 1). Datumsformate %d.%m. %H:%M bleiben in
    # der Route (B19/§8.9); {fehler} kommt escaped+gesliced aus der Route
    # (Slice-vor-Format-Stelle [:180], §8.14 — nur markiert).
    "qualitaet.kopf.titel": "Quality — reference library",
    "qualitaet.kopf.hinweis":
        "tap a person below to see all their pictures with the weak "
        "ones marked.",
    "qualitaet.kopf.stand": "As of: {stand} · {n} references",
    "qualitaet.kopf.knopf_neu": "Re-check now",
    "qualitaet.lauf.fehler":
        "last check FAILED: {fehler} &mdash; start it again.",
    "qualitaet.lauf.checking": "checking picture {i} of {n} &hellip;",
    "qualitaet.lauf.reload_person":
        "reload this page afterwards for the fresh result.",
    "qualitaet.lauf.abgebrochen":
        "the last check did not finish (service restart or it was "
        "stopped) &mdash; start it again.",
    "qualitaet.tabelle.kopf_person": "person",
    "qualitaet.tabelle.kopf_bilder": "pictures",
    "qualitaet.tabelle.kopf_gut": "good",
    "qualitaet.tabelle.kopf_mittel": "fair",
    "qualitaet.tabelle.kopf_unter": "below bar",
    "qualitaet.tabelle.kopf_links": "&larr; left",
    "qualitaet.tabelle.kopf_front": "front",
    "qualitaet.tabelle.kopf_rechts": "right &rarr;",
    "qualitaet.tabelle.kopf_doppel": "duplicates",
    "qualitaet.tabelle.kopf_verwechslung": "confusion",
    "qualitaet.person.funde": "{n} picture(s) worth a look",
    "qualitaet.person.verwechselt": "maybe mixed-up",
    "qualitaet.person.alles_gut": "all good",
    # Ergebnis-Satz "alles gut": die <b>-Grenze trennt zwei VOLLSTAENDIGE
    # Saetze — B9-sicherer Split (der Funde-Zweig dagegen bleibt literal,
    # s. Abschnittskommentar).
    "qualitaet.ergebnis.alles_gut": "All good.",
    "qualitaet.ergebnis.alles_gut_satz":
        "Checked {n} pictures of {np} people &mdash; nothing needs your "
        "attention.",
    "qualitaet.wort.defekt": "broken file",
    "qualitaet.wort.kein_gesicht": "no face found",
    "qualitaet.wort.zu_klein": "too small",
    "qualitaet.wort.unscharf": "blurry",
    "qualitaet.wort.schwach": "weak picture",
    # {name} kommt escaped aus der Route (Muster lernanker {kamera}).
    "qualitaet.galerie.looks_like": "looks like {name}",
    "qualitaet.galerie.doppel": "duplicate — the kept one covers it",
    "qualitaet.galerie.gut": "good",
    "qualitaet.galerie.gut_behalten": "good — kept of its duplicates",
    "qualitaet.galerie.vorrat": "from stock",
    "qualitaet.galerie.norm": "quality {norm}",
    "qualitaet.galerie.okay": "okay",
    "qualitaet.galerie.satz_gut": "All {n} pictures look fine.",
    "qualitaet.galerie.satz_funde":
        "{funde} of {n} pictures are worth a look — the two right-hand "
        "tabs hold them. Tick what you want to remove — nothing happens "
        "without your click.",
    "qualitaet.reiter.gut": "Good ({n})",
    "qualitaet.reiter.check": "Check these ({n})",
    "qualitaet.reiter.weg": "Suggest removing ({n})",
    "qualitaet.galerie.knopf_alle": "Select all",
    "qualitaet.galerie.knopf_keine": "Deselect all",
    "qualitaet.galerie.knopf_entfernen": "Remove selected",
    "qualitaet.galerie.leer_gruppe": "nothing in this group.",
    "qualitaet.galerie.titel": "{name} — picture quality",
    "qualitaet.galerie.link_zurueck": "&larr; back to the overview",
    "qualitaet.galerie.leer_person": "no pictures for this person.",
    "qualitaet.leer.titel": "No check computed yet.",
    "qualitaet.leer.hinweis": "Click Re-check now above.",
    # ---------------------------------------------- routes/lernwizard ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen; die JS-Bloecke
    # _zw_js()/_sicht_js() und der Mehr-Knopf sind seit Tranche D
    # eingezogen — Abschnitt Tranche D unten, _WIDGET_JS traegt keine
    # Sprache): die sicht_zeile samt
    # pruef_wort "reference check"/"picture check" (Satzteil-Splicing
    # §8.3, zugleich qs.sh-.257-Anker) und "nothing here passes the
    # {pruef_wort} …"; der fps-Erklaertext (<b>3</b>/s-Inseln mitten im
    # Satz, §8.1); der k1-Leer-Satz (<b>back</b> im Satz); die
    # Zielpersonen-Zeile und die beiden hin-Zeilen looks like <b>X</b> /
    # named <b>X</b> (Markup um Daten mitten im Satz — Muster lernanker,
    # die _bek-Halbsaetze sind Schluessel); die Statustext-Ersetzung
    # st.replace("naming ships …") mappt GESPEICHERTE Statuswerte
    # (Anzeige==Kennung, §8.2); die Fortschritts-Zaehlernamen aus
    # _PHASEN_KEYS sind fortschritt-Dict-KEYS (Kennungen); Datumsformat
    # "%a %d.%m. %H:%M" bleibt in der Route (B19/§8.9). PHASEN_TEXT
    # wurde zu _phasen_text() (§8.12: t() nie auf Modulebene).
    "lernwizard.titel": "Learning run",
    "lernwizard.link_how": "How it works &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Preparation",
    "lernwizard.phase.ernte": "Harvest (collect faces)",
    "lernwizard.phase.anker": "Grouping (anchors)",
    "lernwizard.phase.benennung": "Naming (your step)",
    "lernwizard.phase.neben_ansichten": "Side views",
    "lernwizard.phase.ganzkoerper": "Full-body stock",
    "lernwizard.phase.uebernahme": "Adoption into the master",
    "lernwizard.phase.fertig": "Done",
    "lernwizard.phase.aktuell": "(current)",
    "lernwizard.phase.link_benennen": "open the clusters and name them",
    "lernwizard.wizard.titel": "Learn people — guided run",
    "lernwizard.wizard.satz":
        "Plans a learning run over your own recordings. Preparation, "
        "harvest, grouping, naming and adoption into recognition all "
        "run for real.",
    "lernwizard.wizard.lage_b":
        "B — existing references/unknowns will be extended",
    "lernwizard.wizard.lage_a": "A — cold start, no faces yet",
    "lernwizard.badge.unbekannt": "unknown visitors",
    # echter Plural schon im Original (is/are) — t_n loest .eins/.viele.
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} unknown visitor is waiting under",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} unknown visitors are waiting under",
    "lernwizard.link_unbekannte": "People &rarr; Unknown",
    "lernwizard.wizard.unbekannt_hinweis":
        "Faces collected today that match no known person — you can "
        "name, merge or mute them there right away; no learning run "
        "needed for that.",
    "lernwizard.wizard.start_titel": "Starting point",
    "lernwizard.wizard.start_hinweis":
        "Clean-up switch for auto-collected unknowns: arrives with the "
        "naming stage.",
    "lernwizard.wizard.knopf_letzte": "last {n}",
    "lernwizard.wizard.knopf_alle": "ALL reachable",
    "lernwizard.wizard.attr_eigen": "own N",
    "lernwizard.wizard.knopf_go": "go",
    "lernwizard.wizard.scope_titel": "Scope (events, not days)",
    "lernwizard.wizard.scope_hinweis":
        "ALL walks the whole reachable history (bounded by Frigate's "
        "retention — the balance below shows how far).",
    "lernwizard.wizard.auswahl_titel": "Your selection",
    # {wann}/{clips} kommen vorformatiert aus der Route (§8.8/§8.9).
    "lernwizard.wizard.auswahl_zeile":
        "last {n} person events = back to {wann} · {clips} with an "
        "available clip",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} older ones without a clip will be skipped",
    "lernwizard.wizard.auswahl_hinweis":
        "The cut is exact at N — completing selections to full passes "
        "arrives with the grouping stage.",
    "lernwizard.wizard.auswahl_durchsucht": "{k} of these {n} are already searched — with \"skip searched events\" the run takes older events instead (the card shows where it ends up).",
    "lernwizard.wizard.q_teilgemessen":
        "analysis speed measured on THIS machine; download estimate "
        "uses defaults",
    "lernwizard.wizard.q_gemessen": "measured on THIS machine",
    # Konditionale Annotations-Anhaenge (§8.11): eigene Schluessel, Werte
    # duerfen mit ", " beginnen.
    "lernwizard.wizard.q_skip":
        ", measurement skipped on this machine ({grund})",
    "lernwizard.wizard.q_wartet":
        ", measurement waiting for a free analysis slot …",
    "lernwizard.wizard.q_laeuft": ", measuring now …",
    "lernwizard.wizard.q_rueckfall":
        "fallback values — not yet measured here",
    "lernwizard.wizard.dauer_titel": "Estimated duration",
    "lernwizard.wizard.dauer_zeile":
        "analysis ~{analyse} · clip downloads ~{download} · one-time "
        "warm-up {kalt}",
    "lernwizard.wizard.dauer_gesamt": "total ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Thresholds (adjustable in Advanced)",
    "lernwizard.wizard.frage":
        "Learn from all {n} events? Estimated duration ~{gesamt} "
        "(analysis {analyse} + downloads {download}). The run can be "
        "aborted at any time.",
    "lernwizard.wizard.fps_titel": "Analysis frames per second",
    "lernwizard.wizard.knopf_start": "Create this run",
    "lernwizard.seg.vorbereiten": "Prepare",
    "lernwizard.seg.sammeln": "Collect faces",
    "lernwizard.seg.sortieren": "Sort into groups",
    "lernwizard.status.laeuft_seit": "running for {dauer}",
    "lernwizard.status.rest": "{rest} remaining",
    "lernwizard.status.fertig_in": "finished in {dauer}",
    # .345 Fortschritts-Block (Kachel 2): drei Unterbalken + Zustands-Woerter.
    "lernwizard.balken.suchen": "Searching faces",
    "lernwizard.balken.pose": "Head pose",
    "lernwizard.balken.erkennen": "Recognizing faces",
    "lernwizard.balken.z_frames": "frame {f} of {s}",
    "lernwizard.balken.z_posen.eins": "{n} pose",
    "lernwizard.balken.z_posen.viele": "{n} poses",
    "lernwizard.balken.z_erkannt.eins": "{n} recognized",
    "lernwizard.balken.z_erkannt.viele": "{n} recognized",
    "lernwizard.balken.wartet": "waiting",
    "lernwizard.balken.clip": "fetching the clip …",
    "lernwizard.balken.fertig": "done",
    "lernwizard.status.aufnahmen": "recordings: {n}",
    "lernwizard.status.bilder": "{n} pictures collected so far",
    "lernwizard.puls.working": "working — updated {s}s ago",
    "lernwizard.puls.stumm":
        "no update for {s}s — a long clip can take minutes; if this "
        "keeps growing, check /log",
    "lernwizard.zeile.kaputt": "{n} unreadable lines counted",
    "lernwizard.zeile.anker_link": "view the {n} anchor clusters",
    # DREI Plurale in EINEM Satz: je Plural ein t_n-Fragment, Trenner
    # bleiben literal in der Route (Zaehler, keine Prosa — §8.10).
    "lernwizard.ergebnis.bilder.eins": "collected {n} picture",
    "lernwizard.ergebnis.bilder.viele": "collected {n} pictures",
    "lernwizard.ergebnis.aufnahmen.eins": "from {n} recording",
    "lernwizard.ergebnis.aufnahmen.viele": "from {n} recordings",
    "lernwizard.ergebnis.gruppen.eins": "sorted into {n} group",
    "lernwizard.ergebnis.gruppen.viele": "sorted into {n} groups",
    "lernwizard.ergebnis.beiseite": "({n} set aside)",
    "lernwizard.kachel.lauf": "Learning run",
    "lernwizard.kachel.sammeln": "Collect &amp; sort",
    "kalib.titel": "Camera calibration",
    "kalib.erklaerung": "These two thresholds decide which faces future learning runs keep. Slide until the border feels right — everything greyed out would be dropped. Below are the pictures of the latest run, best picture impression first. Yellow frame = picture picked for adoption.",
    "kalib.leer": "Nothing to calibrate yet: the latest run carries no quality scores. Start a learning run with this version first.",
    "kalib.regler_e": "Picture impression",
    "kalib.regler_e_prosa": "How clean and bright the picture looks to the eye. Lower keeps more, but darker and rougher pictures.",
    "kalib.regler_t": "Recognisability",
    "kalib.regler_t_prosa": "How well the person can be identified on the picture. Also sorts out half-covered faces.",
    "kalib.standard": "Reset to defaults",
    "kalib.uebernehmen": "Apply thresholds",
    "kalib.js.genutzt": "Kept: {n} of {gesamt}",
    "kalib.js.gespeichert": "Saved — the run is re-graded with the new thresholds, taking you back to the learning run …",
    "kalib.js.fehler": "Saving failed",
    # --- zentrale Kamera-Uebersicht + globaler Rueckfall (31.08.)
    "kalib.knopf": "Calibration",
    "kalib.knopf_tip": "Camera calibration: the bars for alerts, samples and the reference catalogue",
    "kalib.uebersicht.erklaerung": "One camera, one set of values. The quality scales differ from camera to camera — measured on a single setup, the median recognisability of one camera was more than twice that of another. Pick a camera to set its bars.",
    "kalib.uebersicht.leer": "No cameras yet",
    "kalib.uebersicht.leer_hinweis": "As soon as Frigate reports cameras, they show up here.",
    "kalib.grenze.titel": "What calibration does — and what it does not",
    "kalib.grenze.satz": "It decides which picture is shown or sent, which faces are kept as samples, and which of them may become a stored reference. It never decides who is recognised: the name check sees every face, unfiltered. That is measured, not assumed — filtering before the vote cost confirmations.",
    "kalib.kachel.eigene": "own values",
    "kalib.kachel.vorgabe": "default values",
    "kalib.kachel.fremd": "not in Frigate",
    "kalib.kachel.fremd_tip": "This camera has calibration values but Frigate no longer reports it. The values stay, nothing is deleted.",
    "kalib.kachel.vorrat": "{n} of {deckel} samples",
    "kalib.kachel.vorrat_aus": "Sample collection is off (Advanced, calibration samples).",
    "kalib.kachel.stand": "latest {wann}",
    "kalib.kachel.leer": "No samples yet",
    "kalib.kachel.leer_hinweis": "Samples come from a running watcher and from event analyses — or fetch some now.",
    "kalib.kachel.werte": "detection {det} · impression {e} · recognisability {tw}",
    "kalib.kachel.katalog": "catalogue bar {e} / {tw}",
    "kalib.quelle.kamera": "own",
    "kalib.quelle.global": "global fallback",
    "kalib.quelle.aus": "off",
    "kalib.knopf_kalibrieren": "Calibrate",
    "kalib.knopf_fuellen": "Look for fresh material",
    "kalib.knopf_leeren": "Delete samples",
    "kalib.global.titel": "Global fallback",
    "kalib.global.satz": "These apply to cameras without their own values, and they are the bar a learning run uses when it decides which faces to keep.",
    "kalib.global.werte": "impression {e} · recognisability {tw}",
    "kalib.global.katalog": "catalogue bar {e} / {tw}",
    "kalib.global.knopf": "Set on the latest learning run",
    "kalib.global.kein_lauf": "No learning run with quality scores yet — these can be set once a run has finished.",
    "kalib.lauf.titel": "Global bars — latest learning run",
    "kalib.zurueck": "back to all cameras",
    "js.kalib.start": "looking for material …",
    "js.kalib.lauf": "{i} of {n} events · {bilder} picture(s)",
    "js.kalib.fertig": "{bilder} picture(s) from {events} event(s)",
    "js.kalib.fehler": "could not look for material",
    "lernwizard.kachel.benennen": "Smart naming",
    "lernwizard.kachel.fertig": "Done &mdash; they count",
    "lernwizard.such.titel": "Search events for faces",
    "lernwizard.such.klein": "looks back through your recordings",
    "lernwizard.pop.satz":
        "Looks back through your recordings and collects faces. Day to "
        "day the system keeps learning on its own.",
    "lernwizard.pop.label_letzte": "Look back through the last",
    "lernwizard.pop.wort_events": "events",
    "lernwizard.pop.hint_n":
        "how many recent recordings to check (up to {max})",
    "lernwizard.pop.label_tag": "One whole day:",
    "lernwizard.pop.hint_tag":
        "every recording of that day, however many there are",
    "lernwizard.pop.label_kameras": "only these cameras",
    "lernwizard.pop.hint_kameras": "nothing selected = all cameras; pick several with Ctrl/Cmd",
    "lernwizard.pop.wort_fps": "pictures per second",
    "lernwizard.pop.hint_fps":
        "more pictures find more angles, but the search takes longer",
    "lernwizard.pop.label_skip": "Skip events already searched",
    "lernwizard.pop.hint_skip":
        "each search continues further into the past &mdash; untick to "
        "search the newest events again",
    "lernwizard.pop.alle_gesichter": "All faces",
    "lernwizard.pop.eine_person": "Only one person:",
    "lernwizard.pop.hint_person":
        "with one person chosen, matching groups are listed first "
        "&mdash; nothing is hidden",
    "lernwizard.pop.knopf_start": "Start search",
    "lernwizard.knopf_abbrechen": "Cancel",
    "lernwizard.k1.unbekannt.eins": "{n} unknown visitor from today:",
    "lernwizard.k1.unbekannt.viele": "{n} unknown visitors from today:",
    "lernwizard.k1.gestartet": "Run started {wann}",
    "lernwizard.k1.scope": "scope {n} events",
    "lernwizard.k1.kameras": "cameras only: {kameras}",
    "lernwizard.k1.tag": "day {tag}",
    "lernwizard.k2.satz":
        "Runs on its own &mdash; you can close this page and come back.",
    "lernwizard.k2.knopf_abort": "Abort run",
    "lernwizard.k3.satz_warten":
        "Whoever the system recognises for sure gets named by itself. Everything else comes to you &mdash; say who it is, or skip it.",
    "lernwizard.k3.keine_gesichter":
        "No new faces this time &mdash; nothing to name. That is fine: "
        "it just means the recordings held nobody new.",
    "lernwizard.knopf_neuer_lauf": "Start a new run",
    "lernwizard.k3.gruppe_offen":
        "The current group is open below, full width.",
    "lernwizard.k3.alle_erledigt": "All groups are handled.",
    "lernwizard.k3.altes_verfahren":
        "These groups come from the older method, before the quality check. Naming them would sort pictures the run no longer accepts. Start a new run.",
    "lernwizard.chip.bilder": "{n} pictures",
    # .295-Sammelzeile — Anker der qs.sh-PYAD-Stufe (Text wohnt jetzt
    # hier, die Route referenziert den Schluessel).
    "lernwizard.k3.verworfen.eins":
        "{n} group deleted by you &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} groups deleted by you &middot;",
    "lernwizard.k3.link_einsehen": "view",
    # B9: je Zweig ein GANZER Satz-Schluessel (statt Punkt-Anhaengsel).
    "lernwizard.k3.done_weiter":
        "{erledigt} of {gesamt} done &mdash; the next one is ready.",
    "lernwizard.k3.done_punkt": "{erledigt} of {gesamt} done.",
    "lernwizard.k3.wartend.eins": "{n} group is waiting for you.",
    "lernwizard.k3.wartend.viele": "{n} groups are waiting for you.",
    "lernwizard.k3.auto.eins": "{n} was recognised automatically &mdash; check it if you like.",
    "lernwizard.k3.auto.viele": "{n} were recognised automatically &mdash; check them if you like.",
    # ZWEI Plurale in einem <b>-Zaehler: zwei t_n-Fragmente (§8.10).
    "lernwizard.k4.adopt_bilder.eins": "{n} picture adopted for",
    "lernwizard.k4.adopt_bilder.viele": "{n} pictures adopted for",
    "lernwizard.k4.adopt_personen.eins": "{n} person",
    "lernwizard.k4.adopt_personen.viele": "{n} people",
    "lernwizard.k4.zaehlen_sofort":
        "they count for recognition right away.",
    "lernwizard.k4.link_qs": "quality-check the library &#8230;",
    "lernwizard.k4.nichts":
        "no new pictures were adopted this time (groups skipped or "
        "already covered).",
    "lernwizard.k4.wiederholen":
        "Repeat every few days, or let the day view top up known people "
        "in between.",
    "lernwizard.k4.knopf_faces": "Back to Faces",
    "lernwizard.k4.hinweis":
        "Named pictures become references and count for recognition "
        "right away.",
    "lernwizard.zw.grund_maessig": "picture quality only fair",
    "lernwizard.zw.attr_clip": "open the clip",
    "lernwizard.blick.links": "Looking left",
    "lernwizard.blick.frontal": "Frontal",
    "lernwizard.blick.rechts": "Looking right",
    "lernwizard.blick.leer":
        "no usable pictures of this angle in the group",
    "lernwizard.blick.legende":
        "({gut} good, {grenz} borderline of {n} checked)",
    "lernwizard.zw.titel": "Group {pos} of {gesamt} &mdash; who is this?",
    "lernwizard.zw.titel_auto": "Group {pos} of {gesamt} &mdash; is this {name}?",
    "lernwizard.zw.satz":
        "One group should be one person. Tap a picture to leave it out "
        "&mdash; then say who it is, or skip the group.",
    "lernwizard.bekannt.system": "already in your system",
    "lernwizard.bekannt.anker": "named on another cluster",
    # {name} kommt escaped aus der Route.
    "lernwizard.zw.knopf_adopt": "Adopt as {name}",
    "lernwizard.zw.knopf_ja": "Yes, it&rsquo;s {name}",
    "lernwizard.zw.fehler":
        "the picture check could not run (see /log) &mdash; reload to "
        "retry; Skip and Delete still work.",
    "lernwizard.zw.warte":
        "checking this group&rsquo;s pictures against the reference bar "
        "&mdash; a few seconds &hellip;",
    "lernwizard.zw.knopf_andere": "Someone else &#8230;",
    "lernwizard.zw.attr_name": "person name (new or existing)",
    "lernwizard.zw.knopf_save": "Save name",
    "lernwizard.zw.knopf_skip": "Skip this group",
    "lernwizard.zw.frage_delete":
        "Delete this group? Its pictures are removed and a pending naming is discarded. This cannot be undone.",
    "lernwizard.zw.knopf_delete": "Delete this group",
    "lernwizard.zw.link_detail": "full detail view",
    "lernwizard.zw.detail_zusatz":
        "(all pictures with reasons, expert selection)",
    "lernwizard.erfolg.titel": "Grouping done",
    "lernwizard.erfolg.cluster.eins": "{n} face cluster ready:",
    "lernwizard.erfolg.cluster.viele": "{n} face clusters ready:",
    "lernwizard.erfolg.knopf_anker": "View the anchor clusters",
    "lernwizard.erfolg.hinweis": "open a cluster to name it",
    "lernwizard.expert.phasen_titel": "Phases",
    "lernwizard.expert.phasen_hinweis":
        "Preparation, Harvest, Grouping, Naming and adoption into the "
        "master run for real in this build — side views and the "
        "full-body stock activate with the coming updates.",
    "lernwizard.expert.progress_titel": "Progress",
    "lernwizard.expert.anker_bisher": "anchors so far: {n}",
    "lernwizard.expert.progress_rest":
        "created {wann} · scope {n} events · survives restarts (resume "
        "built in)",
    "lernwizard.expert.lauf_bleibt":
        "this run stays — its anchors remain available",
    # --------------------------------- Stufe 1: Einhang/Skelett (webui) ---
    "nav.bereich.activity": "Activity",
    "nav.bereich.faces": "Faces",
    "nav.bereich.learn": "Learn",
    "nav.bereich.person": "Person",
    "nav.bereich.vision": "Vision",
    "nav.bereich.live": "Live",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Configuration",
    "nav.bereich.erkennungstest": "Recognition test",
    "nav.bereich.system": "System",
    "nav.heute": "Today",
    "nav.ereignisse": "Events",
    "nav.offen": "To label",
    "nav.faces": "Faces",
    "nav.gesichter": "Known",
    "nav.unbekannte": "Unknown",
    "nav.qualitaet": "Quality",
    "nav.lernlauf": "Face learning run",
    "nav.anker": "Anchors",
    "nav.lernen": "Suggestions",
    "nav.person": "Body images",
    "nav.person_kontrolle": "Judged images",
    "nav.person_modell": "Model status",
    "nav.personlauf": "Person learning run",
    "nav.vision": "Vision detect",
    "nav.live": "Live watchers",
    "nav.live_alerts": "Live alerts",
    "nav.erkennung": "Recognition",
    "nav.kameras": "Cameras",
    "nav.benachrichtigungen": "Notifications",
    "nav.areas": "Areas",
    "nav.kette": "Recognition chain",
    "nav.konfiguration": "Advanced",
    "nav.erkennungstest": "Recognition test",
    "nav.system": "System",
    "nav.systemstat": "System stats",
    "nav.sync_auswahl": "Frigate sync",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Service log",
    "ui.fuss.docs": "Docs",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip": "Easy shows the core pages — Expert shows everything. Nothing is deleted, Easy only hides.",
    "ui.live.chip": "Live",
    "ui.theme.knopf": "Theme",
    "ui.last.knopf": "System stats",
    "ui.last.tooltip": "System load: CPU, RAM, disk, GPU and the recognition",
    "ui.theme.tooltip": "Switch between light and dark",
    "ui.theme.aria": "Switch colour theme",
    "ui.sprache.tooltip": "Language of this installation — applies to all pages and notifications",
    "ui.upd.link": "update {tag}",
    "ui.upd.tooltip": "A newer suslik version is available on GitHub",
    "ui.upd.titel": "Update available",
    # ui.upd.satz ist der erste deklarierte t_html-Schluessel (HTML_SCHLUESSEL,
    # core/sprache.py) — Tag-Folge muss in jeder Sprache identisch sein.
    "ui.upd.satz": "A newer suslik image (<b>{tag}</b>) is on GitHub — <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">release notes</a>. Pull the new image and restart to update; your data and settings are kept.",
    "ui.wn.titel": "What’s new",
    "ui.wn.x_tooltip": "Hide until the next version",
    "ui.wn.x_aria": "Dismiss",
    "ui.wn.mehr": "Show all ({n})",
    "ui.wn.weniger": "Show fewer",
    # --------------------------------- Stufe 1: Seitentitel (verifyd) ---
    "titel.setup": "Setup",
    "titel.anker_detail": "Anchor",
    "titel.aehnliche": "Matching faces",
    "titel.live_kamera": "Live — {kamera}",
    "titel.video": "Video",
    "titel.event": "Event",
    "titel.vision_galerie": "Build a gallery",
    "titel.hilfe": "How it works",
    # --------------------------------- Stufe 1: Setup-Wizard Schritt 0 ---
    "setup.sprache.titel": "Language",
    "setup.sprache.satz": "Pick the language for this installation — it applies immediately and also covers notifications. You can change it any time with the switch in the header.",
    # --------------------------------- Stufe 1: js.* (window.T, app.js) ---
    # VERTRAG: app.js liest NUR js.*-Schluessel (TT() mit EN-Fallback ==
    # diesem Wert); jede Richtung prueft die Gate-Stufe Sprach-Deckung.
    "js.status.fehler": "error",
    "js.status.fehler_gross": "Error",
    "js.status.fehler_detail": "error: {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "saving …",
    "js.status.gespeichert": "saved",
    "js.status.senden": "sending …",
    "js.status.starten": "starting …",
    "js.status.laeuft": "running …",
    "js.status.laeuft_wort": "running",
    "js.status.pruefen": "checking …",
    "js.status.suchen": "searching …",
    "js.status.lernen": "learning …",
    "js.status.hinzufuegen": "adding …",
    "js.status.entfernen": "removing …",
    "js.status.loeschen": "deleting …",
    "js.status.hochladen": "uploading …",
    "js.status.wiederherstellen": "restoring …",
    "js.status.ueberspringen": "skipping …",
    "js.status.siehe_log": "see service log",
    "js.status.diagnose": "diagnosis",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Cancel",
    "js.neustart.zurueck": "Service is back, loading …",
    "js.neustart.kommt": "Service coming back …",
    "js.neustart.gespeichert": "Saved. Restarting service, please wait …",
    "js.neustart.warten": "Restarting service, please wait …",
    "js.konfig.frage": "Save configuration and restart the service?",
    "js.lernlauf.fps_zeile": "≈ total ~{dauer} at {fps}/s",
    "js.lernlauf.tag_fehlt": "pick a day first",
    "js.lernlauf.abbruch_frage": "Abort this learning run?",
    "js.notif.frage": "Save notification settings and restart the service?",
    "js.frigate.ro_frage": "Switch to READ-ONLY? suslik will stop writing to Frigate.",
    "js.frigate.rw_frage": "Enable WRITING to Frigate (sub_labels + reference sync)?",
    "js.catchup.frage": "Skip catching up on missed events at startup from now on? The service restarts to apply this.",
    "catchup.knopf": 'Catch up',
    "catchup.knopf.tooltip": 'Unprocessed events are waiting',
    "catchup.dlg.titel": 'Fetch unprocessed events',
    "catchup.dlg.label_stunden": 'Go back',
    "catchup.dlg.wort_stunden": 'hours',
    "catchup.dlg.label_limit": 'At most',
    "catchup.dlg.wort_events": 'events',
    "catchup.dlg.fuss": 'Only events that were never analysed are fetched. Your settings stay as they are.',
    "catchup.dlg.abbrechen": 'Cancel',
    "catchup.dlg.los": 'Fetch',
    "js.catchup.spanne": '{von} to {bis}',
    "js.catchup.geklemmt": 'Only {h} h and {n} events are possible. Run it with those?',
    "js.catchup.nicht_bereit": 'Enroll a person first, then these can be checked.',
    # .374 (Widerleger-Fund 30.08.): stand als Satz da ("{n} unprocessed events
    # are waiting.") und las mit n=1 falsch — n ist die Zahl der nie analysierten
    # Ereignisse im Rueckschau-Fenster, 1 ist ein voellig normaler Wert. Die
    # Klammerform der uebrigen gezaehlten js.*-Schluessel ("{n} image(s)") traegt
    # hier nur en und fr; de braeuchte "1 unverarbeitetes Ereignis wartet"
    # (Adjektiv UND Verb kongruieren), it "1 evento non elaborato è in attesa".
    # Eine Plural-Mechanik fuer js.*-Schluessel gibt es nicht (t_n in
    # core/sprache.py loest .eins/.viele nur serverseitig auf). Deshalb die
    # Zaehl-Beschriftung: in allen fuenf Sprachen fuer JEDES n richtig.
    "js.catchup.warten": 'Unprocessed events waiting: {n}',
    "antwort.catchup_gestartet": 'Fetching the last {stunden} h, at most {n} events.',
    "antwort.catchup_laeuft": 'A catch-up run is already going.',
    "js.restore.frage": "Restore configuration from \"{name}\"? This overwrites the current settings and restarts the service.",
    "js.vollrestore.frage": "Restore the FULL backup \"{name}\"? This replaces settings, references and all learned material, then restarts the service.",
    "js.vollrestore.laeuft": "uploading + restoring … (large files take a while)",
    "js.enroll.fehler": "Error: {msg}",
    "js.enroll.person_fehlt": "Choose a person or enter a new one.",
    "js.upload.fehlt": "Choose a person (dropdown or new) and a file.",
    "js.upload.trotzdem": "{msg}\n\nAdd anyway?",
    "js.anlernen.frage": "Add group as \"{person}\" (best images become references)?",
    "js.anlernen.name_frage": "Name of the new person:",
    "js.anlernen.person_fehlt": "Please choose an existing person.",
    "js.auswahl.gesicht_fehlt": "Please tick at least one face.",
    "js.auswahl.bild_fehlt": "Please select at least one image.",
    "js.vorschlag.keine": "No recommended faces.",
    "js.vorschlag.alle_frage": "Add all {n} recommended face(s) to {person}? They become references immediately.",
    "js.vorschlag.frage": "Add {n} face(s) to {person}?",
    "js.vorrat.frage": "Add {n} stock face(s) to {person}? They become references immediately (kept local, not exported).",
    "js.qs.fortschritt": "checking picture {i} of {n} …",
    "js.sync.frage": "Synchronize: {richtung}?",
    "js.sync.modell_laedt": "loading model …",
    "js.sync.fortschritt": "{done}/{total} faces ({current}) {pct}%",
    "js.sync.fertig": "done: {ok} ok, {gate} skipped — reloading …",
    "js.sync.fehler": "sync failed: {grund}",
    "js.syncauswahl.knopf": "Transfer {n} selected to Frigate",
    "js.syncauswahl.nichts": "Nothing selected",
    "js.syncauswahl.nichts_klein": "nothing selected",
    "js.syncauswahl.skip": "skip",
    "js.syncauswahl.restore": "restore",
    "js.syncauswahl.wieder": "offer again",
    "js.syncauswahl.zurueck_laeuft": "putting it back …",
    "js.syncauswahl.frage": "Send {n} reference image(s) to Frigate?",
    "js.syncauswahl.fehl_knopf": "transfer failed",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct}%",
    "js.syncauswahl.fertig": "done: {ok} uploaded, {gate} not accepted — reloading …",
    "js.syncauswahl.fehler": "transfer failed: {grund}",
    "js.vorpruef.haengt": "pre-check appears stuck — reload the page to retry",
    "js.vorpruef.laeuft": "checking images … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "pre-check failed: {grund}",
    "js.vorpruef.fertig": "pre-check done — reloading …",
    "js.import.fortschritt": "downloading {done}/{total} ({current}) {pct}%",
    "js.import.fertig_wiz": "✓ imported {n} — computing features on the accelerator …",
    "js.import.knopf_fertig": "Imported ✓",
    "js.import.fehler": "import failed: {grund}",
    "js.import.knopf": "Import faces",
    "js.import.knopf_ges": "Import faces from Frigate",
    "js.import.fertig_ges": "✓ imported {n} — computing features, page reloads …",
    "js.ref.frage": "Remove reference image of {person}?",
    "js.ref.batch_frage": "Delete {n} image(s)?",
    "js.dienst.nicht_erreichbar": "cannot reach the service — try again in a moment.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage": "Ignore as a known stranger? It will no longer trigger alerts. (Re-activate any time under \"known visitors\" below.)",
    "js.unb.merge_frage": "Merge?",
    "js.unb.name_fehlt": "Enter a name (new or existing person).",
    "js.unb.benennen_frage": "Assign to \"{person}\"? The best images become references.",
    "js.unb.teil_frage": "Assign the {n} ticked pictures to \"{person}\"? The rest of the group stays under Unknown.",
    "js.unb.objekt_frage": "Mark as \"no person\" (a bush, a reflection, a parked car)? It stops showing up as a visitor; you can undo this under \"not people\".",
    "js.person.loesch_frage": "Delete ALL references and the name \"{person}\"?\nThe images move to the trash folder (recoverable).\n\nType the name to confirm:",
    "js.person.name_falsch": "Name did not match — nothing deleted.",
    "js.areas.fehl": "save failed — is the service reachable?",
    "js.areas.name_fehlt": "Enter an area name first.",
    "js.areas.existiert": "This area already exists.",
    # js.areas.entfernen_frage: "Default" ist zugleich Kennung der
    # Standard-Area (Anzeige==Kennung §8.2) — bleibt in jeder Sprache.
    "js.areas.entfernen_frage": "Remove area \"{name}\"? Its cameras return to Default — nothing else changes.",
    "js.personlauf.abbruch_frage": "Abort this person-learn run? Harvested images are kept.",
    "js.personlauf.verwerfen_frage": "Discard run {lid} completely? All its images are deleted; a new run can re-harvest any time.",
    "js.vision.nicht_erreichbar": "could not reach the service — nothing was saved",
    "js.vision.gespeichert": "saved — recognition uses this connection from now on",
    "js.vision.gespeichert_neustart": "saved — the service restarts in a moment",
    "js.vision.gespeichert_reload": "saved — the service is restarting, this page reloads in a moment",
    "js.vision.treffer": "{n}/2 right",
    "js.vision.tokens": "{ist} tokens vs {soll}",
    "js.vision.dirty_titel": "You have not saved this connection",
    # js.vision.dirty_text: zitiert den Vision-Knopf vision.save.knopf
    # ("Save connection") woertlich — Zitat-Kopplung, bei Knopf-Aenderung
    # nachziehen (gleiche Kopplung in js.vision.prompt_zurueck).
    "js.vision.dirty_text": "The test would use the values you just typed. Recognition keeps using the SAVED connection until you press \"Save connection\" — a green test alone changes nothing about the verdicts.",
    "js.vision.dirty_save": "Save first, then test",
    "js.vision.dirty_test": "Test without saving",
    "js.vision.stufe1": "reachability and model",
    "js.vision.stufe2": "forced-choice shape grids",
    "js.vision.stufe3": "token count",
    "js.vision.stufe_laeuft": "step {nr}/3 — {name} … (a local model on CPU can take minutes)",
    "js.vision.test_fehl": "the test could not be run",
    "js.vision.stufe_stop": "stopped at step {nr} — see the log below",
    "js.vision.fertig": "done — {ampel}",
    "js.vision.stufe_fehl": "step {nr} could not be run",
    "js.vision.neustart_warte": "the service is not answering right now — this page reloads in a moment",
    "js.vision.prompt_frage": "Reset the question to the default wording?",
    "js.vision.prompt_zurueck": "default wording restored — press \"Save connection\" to store it",
    "js.vision.kachel_frage": "You have unsaved changes. Switching provider discards them. Continue?",
    "js.vision.pick": "— pick one —",
    "js.vision.untested": "untested here",
    "js.vision.neu_pruefen": "the connection changed — check it again to see which models it has",
    "js.vision.key_laeuft": "asking the provider which models you can use …",
    "js.vision.key_fehl": "the check failed",
    "js.vision.key_fehl2": "the check could not be run",
    "js.rt.start": "starting the vision run …",
    "js.rt.fehl": "the run could not be started",
    "js.rt.nach_fehl": "it could not be started",
    "js.vw.geliehen": "from the {reihe} row",
    "js.vw.vergessen_frage": "Forget the images you rejected for this gallery? They can be proposed again.",
    "js.vw.leer_frage": "{n} cell(s) could not be filled. Approve the gallery anyway?",
    "js.vw.kopiert": "copying the pictures into the gallery …",
    # js.live.phase_*: Anzeige-Woerter zu den Status-KENNUNGEN des
    # Live-Polls (Status-replace-Mapping, §8-Nachtrag).
    "js.live.phase_verbinden": "Connecting",
    "js.live.phase_messen": "Measuring",
    "js.live.phase_auswerten": "Evaluating",
    "js.live.phase_abbruch": "Aborting",
    "js.live.rest": " — {n} s left",
    "js.live.auftrag_zeile": "{art} on {kamera}: {phase}{rest}{pausiert}",
    "js.live.messung": "Load measurement",
    "js.live.quelltest": "Source test",
    "js.live.pausiert": " — watchers paused for measurement ({liste})",
    "js.live.job_laeuft": "source test running (helper process, up to ~2 minutes) …",
    "js.live.vorrat_leeren_frage":
        "Delete the calibration samples of this camera? They cannot be brought back; the watcher starts collecting again from now on.",
    "js.live.job_ok": "source test done: {text}",
    "js.live.job_fehl": "source test FAILED: {text}",
    "js.live.messung_fehl": "load measurement failed: {grund}",
    "js.live.test_fehl": "source test failed: {grund}",
    # ---- auftritte (Stufe 2, Tranche A) ----
    # Projektroot-Route /heute-Personensicht + /pass/<eid> (auftritte.py).
    # Stufe-2-Grenzen dort: §8.1 (leer_link-Hinweis + full-profile-Halbsatz
    # mit <a> im Satz), §8.4/§8.17 (Lern-Bruecken-JS samt Toggle-Knopf,
    # \u-Escapes), B19 (%A/%B- und %d.%m.-Datumsformate).
    "auftritte.unbek.zaehlung": "+{n} not matched (usually the same people)",
    "auftritte.unbek.name": "Unknown {nummer}",
    "auftritte.unbek.ohne_treffer.eins": "{n} event with an unmatched face",
    "auftritte.unbek.ohne_treffer.viele": "{n} events with an unmatched face",
    "auftritte.nav.zurueck_heute": "&#8592; Today",
    "auftritte.unbek.titel": "Unknown",
    "auftritte.unbek.leer_link": "This link is missing its walk-through.",
    "auftritte.unbek.leer_weg": "This walk-through is no longer in the day view.",
    "auftritte.unbek.leer_weg_hinweis":
        "The day may have been re-grouped — open it again from Today.",
    "auftritte.unbek.leer_pool": "No collected faces for this walk-through.",
    "auftritte.unbek.leer_pool_hinweis":
        "The pool may have been cleaned up in the meantime.",
    "auftritte.knopf.video": "video",
    "auftritte.karte.faces.eins": "{n} face",
    "auftritte.karte.faces.viele": "{n} faces",
    "auftritte.karte.kameras.eins": "{n} camera",
    "auftritte.karte.kameras.viele": "{n} cameras",
    "auftritte.unbek.mehr_im_lauf": "+{n} more in this walk",
    "auftritte.unbek.ein_lauf": "one walk-through",
    "auftritte.zuweisen.titel": "Who is this?",
    "auftritte.zuweisen.satz":
        "These are the faces from THIS walk-through. Tick the ones that "
        "really belong to the person &mdash; junk stays behind. Give them a "
        "name (new or existing) and they are learned; doing nothing keeps "
        "them unknown.",
    "auftritte.zuweisen.knopf_alle": "Select all",
    "auftritte.zuweisen.knopf_keine": "None",
    "auftritte.zuweisen.attr_person": "person (new or existing)",
    "auftritte.zuweisen.knopf_zuweisen": "Add selected faces",
    "auftritte.zuweisen.js_keine": "tick at least one face",
    "auftritte.zuweisen.js_name": "enter a person name",
    "auftritte.zuweisen.js_lernt": "learning…",
    "auftritte.zuweisen.js_fehler": "error",
    "auftritte.unbek.titel_lauf": "Unknown {nummer} — walk-through",
    "auftritte.leer_person": "Unknown person.",
    "auftritte.leer_person_hinweis": "Pick a person on the Today page.",
    "auftritte.titel": "Appearances",
    "auftritte.nav.attr_tag": "back to the day",
    "auftritte.nav.attr_vortag": "previous day",
    "auftritte.kopf.passzahl.eins": "{n} pass",
    "auftritte.kopf.passzahl.viele": "{n} passes",
    "auftritte.nav.attr_kein_morgen": "no future days",
    "auftritte.nav.attr_folgetag": "next day",
    "auftritte.titel_person": "{person} — Appearances",
    "auftritte.leer_passe": "No confirmed passes of {person} on this day.",
    "auftritte.leer_passe_hinweis": "Use the day arrows to look around.",
    "auftritte.karte.kein_bild": "no image",
    "auftritte.thumb.zusatz_unbestaetigt": " — not confirmed here",
    "auftritte.thumb.zusatz_referenz": " — in the references",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} event without a face",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} events without a face",
    "auftritte.thumb.hinweis_referenz":
        "green border = already in the references",
    "auftritte.karte.best_punkt": "confirmed at {zeit}",
    "auftritte.karte.best_spanne": "confirmed {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "in progress",
    "auftritte.karte.pass_nr": "Pass {n}",
    "auftritte.karte.events.eins": "{n} event",
    "auftritte.karte.events.viele": "{n} events",
    "auftritte.karte.best_match": "best match {wert}",
    "auftritte.karte.auch_dabei": "also in this pass: {namen}",
    "auftritte.pass.titel": "Pass",
    "auftritte.pass.leer_event": "Event not found.",
    "auftritte.pass.leer_event_hinweis": "It may have aged out of the log.",
    "auftritte.pass.leer_gruppe": "This event is not part of a grouped pass.",
    "auftritte.pass.leer_gruppe_hinweis": "Grouping needs the day view context.",
    "auftritte.nav.zurueck_tag": "&#8592; Day",
    "auftritte.pass.attr_vor": "previous pass of the day",
    "auftritte.pass.attr_nach": "next pass of the day",
    "auftritte.pass.kopf": "Pass {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Unmatched",
    "auftritte.pass.label_gt": "Label",
    "auftritte.pass.badge_fremd": "confirmed stranger",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log holds no reason line — open the event for the full log",
    "auftritte.pass.grund_ohne_log":
        "no analyze.log kept for this event — see the service log",
    "auftritte.pass.label_fehler": "Error",
    "auftritte.pass.wer": "Who",
    "auftritte.pass.titel_zeit": "Pass {zeit} — {tag}",
    # ---- verifyd-Innenseiten (Stufe 2, Tranche B) ----
    # Inline-Handler in verifyd.py (kein routes/-Modul): _banner, Setup-
    # Wizard, Today-Leerzustaende, /unbekannte, /live_alerts, /video,
    # /event/<id>. Stufe-2-Grenzen dort: §8.1 (<b>System…</b>-Saetze im
    # Wizard-Schritt 3 und im Fertig-Block), §8.6 (Frigate/suslik-Zeilen-
    # labels der Event-Seite), B19 (%d.%m.-Datumsformate in _tag() und der
    # Event-Kopfzeit). Wiederverwendet statt dupliziert: kameras.karte.*
    # (Wizard-Schritt 2 = identische Karten-UI wie routes/kameras) und
    # auftritte.pass.leer_event* (gleicher Event-404-Text).
    "banner.schoner":
        "Frigate is not answering — backing off and probing every few "
        "seconds until it recovers; the UI keeps serving local data.",
    "banner.fehler":
        "Frigate unreachable (last error {zeit}): {fehler} — the UI keeps "
        "serving local data.",
    "banner.nachholen.eins":
        "Catching up on missed events from the last hour: {fertig} of {gesamt}",
    "banner.nachholen.viele":
        "Catching up on missed events from the last {n} hours: "
        "{fertig} of {gesamt}",
    "banner.nachholen_aus": "Don't catch up at startup in the future",
    "hinweis.frigate_fr_an": "Frigate\u2019s own face recognition is switched on. suslik does not need it \u2014 it recognises faces itself and works either way. You can turn it off in Frigate if you do not use it otherwise.",
    "ui.hinweis.x_tooltip": "Do not show this notice again",
    "ui.hinweis.x_aria": "Dismiss this notice for good",
    "setupwiz.frigate.status_ok": "✓ Connected — {n} camera(s) found",
    "setupwiz.frigate.status_fehl": "✗ Could not reach Frigate: {fehler}",
    "setupwiz.frigate.status_fehl_keine": "no cameras",
    "setupwiz.frigate.status_fehl_hinweis":
        "Fix the URL (or set FRIGATE_URL in your .env / docker-compose) "
        "and test again.",
    "setupwiz.frigate.status_leer":
        "Enter your Frigate URL and test the connection.",
    "setupwiz.frigate.titel": "Connect to Frigate",
    "setupwiz.frigate.satz":
        "suslik reads your cameras straight from Frigate's API "
        "(usually port 5000). No cameras are hard-coded.",
    "setupwiz.frigate.knopf_test": "Test connection",
    "setupwiz.kameras.titel": "Pick cameras &amp; conditions",
    "setupwiz.kameras.satz":
        "Tick which cameras to watch; tick one or more zones to only "
        "analyze events that entered them (e.g. person in the garden). "
        "None ticked = all events.",
    "setupwiz.kameras.satz_ohne":
        "Connect to Frigate first — your cameras appear here.",
    "setupwiz.backend.titel": "Acceleration",
    "setupwiz.backend.verfuegbar": "Available on this machine:",
    "setupwiz.backend.satz_wahl": "Pick one — CPU always works.",
    "setupwiz.import.titel": "Import faces from Frigate",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/mitte/nach rahmen die
    # hervorgehobenen Zahlen, Rand-Leerzeichen gehoeren zum Wert.
    "setupwiz.import.zahl_vor": "Frigate already has ",
    "setupwiz.import.zahl_mitte": " reference image(s) of ",
    "setupwiz.import.zahl_nach": " person(s).",
    "setupwiz.import.satz":
        "Import them so suslik recognizes everyone from the start. The "
        "images are downloaded quickly, then suslik computes its own face "
        "features on your accelerator (GPU/NPU).",
    "setupwiz.import.knopf": "Import {n} faces from Frigate",
    "setupwiz.import.satz_leer":
        "No faces in Frigate yet. Note: suslik needs at least one "
        "reference face before it can recognize anyone — import from "
        "Frigate here, or upload photos later on the Known page.",
    "setupwiz.import.satz_ohne":
        "Connect to Frigate first — then you can import its known faces "
        "here.",
    "setupwiz.fertig.knopf": "Save &amp; start suslik",
    "setupwiz.fertig.satz":
        "Saves your choices and restarts the service once.",
    "setupwiz.restore.titel": "Already have a configuration?",
    "setupwiz.restore.satz":
        "If you exported a suslik configuration before (System → "
        "Configuration backup), load it here to restore all settings and "
        "skip the wizard.",
    "setupwiz.restore.knopf": "Load configuration file…",
    "setupwiz.write.titel": "Write back to Frigate?",
    "setupwiz.write.satz":
        "suslik can write its verdicts back to Frigate (sub_labels) and "
        "mirror references, for running both in parallel. Read-only is "
        "the safe default.",
    "setupwiz.write.opt_ro":
        "Read-only (recommended) — suslik never writes to Frigate",
    "setupwiz.write.opt_rw": "Write back to Frigate (parallel operation)",
    "setupwiz.willkommen.titel": "Welcome to suslik",
    "setupwiz.willkommen.satz":
        "A quick guided setup — or load an existing configuration to skip "
        "it. Everything here is editable later on the normal pages.",
    # leer.*: Today-Leerzustaende + verstreute webui.leer()-Stellen.
    # passe_area/band: B9-Ganz-Satz-Umbau (frueher Halbsatz-Splicing
    # "yet today."/"on this day." — jetzt je Zweig ein voller Satz).
    "leer.passe_area_heute": "No passes touched {area} yet today.",
    "leer.passe_area_tag": "No passes touched {area} on this day.",
    "leer.passe_area_hinweis": "The All chip above shows the whole property.",
    "leer.passe_heute": "No passes with a face yet today.",
    "leer.passe_heute_hinweis":
        "As soon as someone walks across the property, the pass appears "
        "here.",
    "leer.tag": "Nothing with a face on this day.",
    "leer.tag_hinweis":
        "Use the arrows to look at another day, or open Events for the "
        "full list.",
    "leer.frigate": "No Frigate connected yet.",
    "leer.frigate_hinweis":
        "Set your Frigate URL in the setup wizard (System page) — then "
        "passes appear here automatically.",
    "leer.refs":
        "Connected — but no reference faces yet, so nobody can be "
        "recognized.",
    "leer.refs_hinweis":
        "Import faces from Frigate or upload photos — both on the Known "
        "page. suslik then keeps learning from the cameras on its own.",
    "leer.band_heute": "Nothing with a face yet today.",
    "leer.band_tag": "Nothing with a face on this day.",
    "leer.band_hinweis": "People appear here as soon as a pass is analysed.",
    "leer.person_unbekannt": "Person unknown.",
    "leer.kamera_unbekannt": "Unknown camera.",
    "leer.kamera_unbekannt_hinweis":
        "Tiles come from Frigate's camera list and saved watchers only.",
    "unbekannte.name": "Unknown {nummer}",
    "unbekannte.meta_zeit": " appearances · {zeit}",
    "unbekannte.mehr_bilder": "+{n} more pictures in this group",
    "unbekannte.knopf_reaktivieren": "reactivate",
    "unbekannte.attr_name": "Name (new or existing)",
    "unbekannte.attr_wahl": "Pick this group for merging",
    "unbekannte.knopf_zuweisen": "Assign person",
    "unbekannte.knopf_teil": "Assign the {n} ticked",
    "unbekannte.knopf_ignorieren": "Ignore",
    "unbekannte.knopf_objekt": "No person",
    "unbekannte.knopf_person": "Is a person",
    "unbekannte.knopf_bulkmerge": "Merge the {n} picked groups",
    "unbekannte.knopf_mehr": "Show {n} more groups",
    "unbekannte.titel": "Unknown",
    "unbekannte.anker": "{offen} of {gesamt} groups still waiting for you",
    "unbekannte.sort_label": "Sort",
    "unbekannte.sort_bilder": "most pictures",
    "unbekannte.sort_neu": "newest",
    "unbekannte.filter_label": "Show",
    "unbekannte.f_offen": "open",
    "unbekannte.f_wieder": "recurring",
    "unbekannte.f_heute": "new today",
    "unbekannte.f_vorschlag": "merge suggested",
    "unbekannte.f_besucher": "muted",
    "unbekannte.f_objekt": "not people",
    "unbekannte.kopf_satz":
        "Faces with no known match, grouped into recurring identities.",
    # Kopf-Erklaerung an den <b>-Grenzen gesplittet; die Fett-Teile sind
    # die knopf_*-Schluessel selbst (eine Quelle, kein Drift).
    "unbekannte.kopf_satz_zuweisen":
        " links a tile to a person (new or existing, type the name),",
    "unbekannte.kopf_satz_ignorieren": " mutes a known stranger (no alert).",
    "unbekannte.kopf_satz_auto":
        "New faces are collected automatically after each pass.",
    "unbekannte.knopf_reorg": "Reorganize now",
    "unbekannte.hinweis_reorg":
        "re-check the pool and rebuild the clusters — collection itself "
        "runs automatically (1-2 min)",
    "unbekannte.satz_objekte":
        "Groups whose images are near-identical to each other and unlike "
        "any person — typically a wheel arch, pavement or light pattern "
        "the detector keeps mistaking for a face. They are frozen: new "
        "finds are never added here (they form fresh, visible clusters "
        "and get re-checked by the same rule) — the groups stay listed so "
        "nothing is hidden. Marked by hand or found automatically; "
        '"Is a person" puts one back.',
    "unbekannte.leer": "No unknown faces collected yet.",
    "unbekannte.leer_hinweis":
        "Identities appear here after the next unknown visitor.",
    "unbekannte.leer_filter": "Nothing in this view.",
    "unbekannte.leer_filter_hinweis":
        "Other groups are waiting under a different filter above.",
    "livealerts.link_video": "&#9654; video {n}",
    "livealerts.person_unbekannt": "unknown",
    "livealerts.trigger.eins": "{n} trigger",
    "livealerts.trigger.viele": "{n} triggers",
    "livealerts.kanal_keiner": "not sent (no channel)",
    "livealerts.keine_bilder": "no stored pictures",
    "livealerts.titel": "Live watcher alerts",
    "livealerts.kopf.auftritte.eins": "{n} appearance",
    "livealerts.kopf.auftritte.viele": "{n} appearances",
    "livealerts.kopf.satz":
        " on {tag} — quick check, preliminary; the confirmed verdict "
        "comes from the normal analysis.",
    "livealerts.kopf.satz_alt":
        "Entries from before 0.1.0.190 have no picture or name recorded.",
    "livealerts.leer": "No live alerts that day.",
    "video.fehl": "&#9888; Transcode failed — see the service log (/log).",
    "video.fehl_hinweis":
        "Reload this page to retry, or open the original clip:",
    "video.warte": "Preparing browser video (H.264)&nbsp;…",
    "video.warte_satz":
        "This page refreshes automatically. The copy is built once and "
        "then cached.",
    "event.ours_zeile.eins": "{person} — {stufe} (seen in {n} window)",
    "event.ours_zeile.viele": "{person} — {stufe} (seen in {n} windows)",
    "event.ours_keiner": "no match for anyone",
    "event.ours_rest.eins": " · {n} other: no match",
    "event.ours_rest.viele": " · {n} others: no match",
    "event.grenze":
        "below this line: weak matches (best score &lt; {wert}) — the "
        "name is a guess, this could be a different person",
    "event.gruppe_ohne": "Unattributed",
    "event.badge_unsicher": "unsure",
    "event.leer_crops": "No face crops stored for this event.",
    "event.knopf_video": "&#9654; Video",
    "event.knopf_log": "Analysis log",
    "event.attr_unvollstaendig":
        "clip incomplete — read {gelesen}/{soll} frames; judged from the "
        "readable part",
    "event.badge_unvollstaendig": "⚠ incomplete clip",
    "event.pass_zurueck": "&#8592; prev",
    "event.pass_weiter": "next &#8594;",
    "event.pass_teil": "Part of a pass",
    "event.pass_events.eins": "{n} event",
    "event.pass_events.viele": "{n} events",
    "event.pass_knopf": "view pass",
    "event.label_grund": "Error reason",
    "event.grund_ohne_zeile":
        "analyze.log holds no reason line — use the log button below",
    "event.grund_ohne_log":
        "no analyze.log kept for this event — see the service log "
        "(System page)",
    "event.zurueck": "← Today",
    "event.label_korrektur": "Correct if wrong",
    "event.label_wer": "Who was it?",
    "event.h_bilder": "Images",
    # ---- Routen-Seiten (Stufe 2, Tranche C) ----
    # routes/system.py, routes/vision.py, routes/visiontest.py,
    # routes/visionwizard.py, routes/personwizard.py, webui/bausteine.py.
    # Grenzen dieser Tranche stehen als Kommentar an den Fundstellen:
    # §8.1 (Inline-<a>/<b>/<code> mitten in Prosa, t_html-Stufe), §8.4
    # (Inline-JS + JSON-msg, Tranche D), B19 (Datumsformate), §8.6
    # (Produkt-/Protokollnamen, Endpunkt-Namen), §8.12/§8.13
    # (KAT_LABELS-Konstante in webui/bausteine.py, eigener Umbau-Zug).
    # Wiederverwendet statt dupliziert: ereignisliste.tabelle.kopf_kamera +
    # ereignisliste.titel (QC-Tabellenkopf), ui.fuss.log ("Service log"),
    # konfiguration.knopf_setup ("Re-run setup wizard").
    # ZITAT-FOLGE (Uebersetzungsrunde): system.titel + system.backup.titel
    # ("System"/"Configuration backup") werden von setupwiz.restore.satz
    # woertlich zitiert, konfiguration.knopf_setup vom Wizard-Fertig-Block
    # (verifyd.py — seit Stufe 3 der Schluessel setupwiz.fertig.wieder_satz),
    # vision.save.knopf ("Save connection")
    # sinngemaess von js.vision.dirty_text ("press Save").
    # --- routes/system.py ---
    "system.ampel.service": "Service",
    "system.ampel.service_info": "processed (total): {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — self-check OK",
    "system.ampel.backend_fail":
        "{backend} — {n} self-check FAIL(s), see service log",
    "system.ampel.analyse": "Analysis",
    "system.ampel.analyse_dauer": "last duration {s} s",
    "system.ampel.analyse_nie": "no analysis yet",
    "system.ampel.retry": "Retry queue",
    "system.ampel.retry_info":
        "{offen} open / {aufgegeben} given up (window {tage} d)",
    "system.ampel.frigate_unkonfiguriert":
        "not configured yet — set the URL in the setup wizard",
    "system.ampel.frigate_ok": "reachable",
    # {zeit} kommt vorformatiert (%H:%M) aus der Route (B19-Stufe).
    "system.ampel.frigate_fehler": "last error {zeit}",
    # {s} vorformatiert (:.0f) — Formatspezifika nie in Werte (§8.8).
    "system.ampel.mqtt_hb": "heartbeat {s} s ago",
    "system.ampel.mqtt_kein_hb": "no heartbeat yet",
    "system.ampel.mqtt_pub_aus": "configured, publishing off",
    "system.ampel.mqtt_pub_kaputt":
        "configured, publisher not started — see service log",
    "system.ampel.mqtt_unkonfiguriert": "not configured",
    "system.ampel.disk": "Disk",
    "system.ampel.disk_info2": "{gb} GB free · clip cache {cache} GB of {max} GB",
    "system.disk.titel": "Disk space",
    "system.disk.satz": "Clips are a cache: kept {tage} days, capped at {max} GB, and trimmed whenever less than {min} GB is free (checked after every event and by a daily disk watch that tightens to every 10 minutes while space is low).",
    "system.disk.knopf": "Clean up now",
    "system.disk.warnung": "Only {gb} GB free and the clip cache is already empty — free space on the data volume; otherwise new events cannot be saved.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "CHECK",
    "system.drift.banner":
        "DRIFT GUARD RED after the last reference add:",
    "system.sync.titel": "Sync with Frigate",
    "system.sync.knopf": "Open Frigate sync",
    "system.sync.satz":
        "The sync page compares both libraries class by class, pre-checks "
        "every candidate the way Frigate does, sends only what you tick, "
        "and imports what only Frigate has.",
    "system.sync.fehlt":
        "not available yet — needs a reachable Frigate and at least one "
        "reference face",
    "system.qc.titel": "QC report",
    "system.qc.stand": "(as of {stand}, {tage} days)",
    "system.qc.kopf_gesicht": "with face",
    "system.qc.kopf_bestaetigt": "confirmed",
    "system.qc.kopf_quote": "window rate",
    # WIRD ZITIERT: setupwiz.restore.satz aller Sprachen nennt diesen Titel
    # woertlich englisch — in der Uebersetzungsrunde nachziehen.
    "system.backup.titel": "Configuration backup",
    "system.backup.satz":
        "Download the settings stored in /data/config as one JSON file, or "
        "restore them from such a file. Honest scope: today that is the "
        "CAMERA SHEET (incl. its stored values); thresholds/channels set "
        "only in verifyd.yaml or via environment are NOT in this file. "
        "Learned people/references: use the full backup below.",
    "system.backup.knopf_download": "Download configuration",
    "system.backup.knopf_restore": "Restore from file…",
    "system.backup.careful": "Careful:",
    # {hinweis} = core.registry.VISION_EXPORT_HINWEIS (zentrale Quelle).
    "system.backup.careful_config":
        "this file {hinweis} (notification channels and vision detect), so "
        "that a restore on another machine really works.",
    "system.backup.restore_satz":
        "Restore overwrites the current settings (the previous ones are "
        "kept as a .bak) and restarts the service.",
    "system.voll.titel": "Full backup",
    "system.voll.satz":
        "One portable archive with everything you taught this "
        "installation: settings, the face reference library, learning-run "
        "results, the whole person-recognition material (images, your "
        "review verdicts, trained models) and the event record. Made for "
        "moving to another machine. Honest scope: the video clip cache and "
        "per-event analysis artifacts are NOT included — they are rebuilt "
        "over time.",
    "system.voll.knopf_download": "Download full backup",
    "system.voll.knopf_restore": "Restore full backup…",
    "system.voll.careful": "this archive {hinweis}.",
    "system.voll.restore_satz":
        "Restore replaces those parts (each previous one is kept once as "
        "*.pre-restore-*) and restarts the service. Uploading a few "
        "hundred MB can take a while — leave the page open.",
    "system.live.titel": "Live watchers",
    "system.live.alerts": "Alerts sent today: {kanaele}",
    "system.live.stoerungen": "Disturbance notices today: {n}",
    "system.live.knopf": "Open Live watchers",
    "system.live.quelle":
        "Counted from the engine's own message log — only messages that "
        "were really accepted by a channel. Live watcher alerts are "
        "separate from the event-analysis alert counters on the Today "
        "page.",
    "system.write.titel": "Frigate write-back",
    "system.write.satz":
        "Does suslik write back to Frigate, or only read? Read-only is the "
        "safe default; enable writing only for parallel operation "
        "(Frigate-Face + suslik).",
    "system.write.aktuell": "Current:",
    "system.write.zustand_ro": "READ-ONLY — suslik does not write to Frigate",
    "system.write.zustand_rw": "WRITING to Frigate — sub_labels",
    "system.write.zustand_rw_sync": " + reference sync",
    "system.write.knopf_rw": "Enable writing",
    "system.write.knopf_ro": "Read-only",
    # WIRD ZITIERT: setupwiz.restore.satz ("System → Configuration backup")
    # und der Wizard-Fertig-Block nennen die Seite woertlich englisch.
    "system.titel": "System",
    "system.tools.titel": "Tools",
    "system.docs.titel": "Docs",
    "system.docs.link": "Documentation on GitHub",
    # --- routes/vision.py ---
    "vision.zeit.nie": "never",
    "vision.titel": "Vision detect",
    "vision.kopf.dirty": "not saved",
    "vision.hinweis.titel": "What you need for this",
    "vision.schalter.knopf_aus": "Turn off",
    "vision.schalter.knopf_an": "Turn on",
    "vision.schalter.fehlt": "Still missing:",
    "vision.schalter.fehlt_galerien": "{n} of {soll} approved galleries — build one under 'Build a gallery'",
    "vision.schalter.fehlt_test": "a green connection test",
    "vision.schalter.fehlt_kandidaten": "judged images to pick a candidate from — they appear while a pass is running; turn on 'diagnostic collection' under Person if you want them to stay",
    "vision.schalter.titel_an": "Vision detect is on",
    "vision.schalter.titel_aus": "Vision detect is off",
    "vision.schalter.aus_satz":
        "While it is off nothing is sent anywhere and no image leaves this "
        "machine.",
    "vision.frage.titel": "How a comparison is asked",
    "vision.frage.doppel_titel":
        "Ask each pair twice, with the galleries swapped",
    "vision.frage.doppel_satz":
        "This is the position check. A in the first run and B in the "
        "swapped run mean the SAME gallery, so a contradiction exposes a "
        "model that simply prefers whatever comes first. Measured here: "
        "every wrong answer across all our test series was an "
        "&bdquo;A&ldquo;, never a &bdquo;B&ldquo;. Turning it off halves "
        "the requests &mdash; and a comparison then rests on a single "
        "answer, with nothing to check it against.",
    "vision.meld.titel": "Extra messages",
    "vision.meld.satz":
        "Both are off unless you turn them on, and neither changes the "
        "existing alarms: vision cannot raise one, cancel one, or overrule "
        "the face and body paths.",
    "vision.meld.judged_titel":
        "Tell me when a walk-through has been judged",
    "vision.meld.judged_satz":
        "A short note through your usual channels once the verdict is in "
        "&mdash; with the real vote count. It arrives after the pass is "
        "over, on a local model that can be minutes later. Information, "
        "not an alarm.",
    "vision.meld.alarm_titel":
        "Alert me when vision contradicts the body recognition",
    "vision.meld.alarm_satz":
        "Fires only when a run really happened, the model answered, and it "
        "still confirmed nobody. It stays quiet when there was simply not "
        "enough material &mdash; that would be noise. Recognising people "
        "you taught it is the strong side of this path, so a "
        "non-confirmation means something; turning strangers away is the "
        "weak side, so vision never votes in that direction.",
    "vision.kachel.was_key": "you enter an API key",
    "vision.kachel.was_host": "you enter host and port",
    "vision.kachel.was_url": "you enter a URL and an optional key",
    "vision.kachel.titel": "Where the model runs",
    "vision.kachel.satz":
        "Pick a provider. For the three named ones the official API "
        "address is already built in &mdash; you only enter your key. "
        "Nothing is sent anywhere until you press a button yourself.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; stored &mdash; leave blank to keep it",
    "vision.verb.key_pflicht_ph": "paste your key here",
    "vision.verb.key_frei_ph": "only if your server asks for one",
    "vision.verb.host": "Host",
    "vision.verb.host_ph": "the name or address of that machine",
    "vision.verb.port": "Port",
    "vision.verb.host_satz":
        "Just the machine &mdash; suslik adds the rest of the address "
        "itself. The example port is the one llama.cpp uses by default; "
        "use whatever yours listens on.",
    "vision.verb.endpunkt": "Endpoint URL",
    "vision.verb.endpunkt_satz":
        "That is an example of an OpenAI-compatible endpoint &mdash; "
        "replace it with yours if you use another provider.",
    "vision.verb.betriebsart": "This endpoint is",
    "vision.verb.betriebsart_extern": "on the internet",
    "vision.verb.betriebsart_lokal": "in my own network",
    "vision.verb.adresse": "API address",
    "vision.verb.adresse_satz":
        "Built in &mdash; there is nothing to type wrong here.",
    "vision.verb.key": "API key",
    "vision.verb.key_frei_satz":
        "Optional here &mdash; most local servers do not ask for one. "
        "Press the button anyway: it also fetches the list of models your "
        "server has.",
    "vision.verb.titel": "Connection",
    "vision.modell.titel": "Model",
    "vision.modell.verweigert": "the endpoint refused the connection",
    # {zeit} vorformatiert aus _zeit() — das Format bleibt in der Route (B19).
    "vision.modell.geprueft": "Checked {zeit} against",
    "vision.modell.opt_wahl": "&mdash; pick one &mdash;",
    "vision.modell.ungetestet": "untested here",
    "vision.modell.opt_verschollen":
        " — saved earlier, the endpoint does not list it now",
    "vision.modell.wahl_satz":
        "Pick one from the list &mdash; the note next to each name is "
        "ours, the names are the endpoint&rsquo;s.",
    "vision.modell.verschollen_satz":
        "This model is saved and still in use, but the endpoint did not "
        "list it this time. Check the name, or pick one from the list.",
    "vision.modell.fremde_plattform": "measured on another platform",
    "vision.modell.kein_rohergebnis": "no raw result archived for this one",
    "vision.modell.gemessen": "measured {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "Not measured here &mdash; that is not a verdict, just honesty. "
        "Run the connection test below before you rely on it.",
    "vision.modell.manuell": "Model id by hand",
    "vision.modell.manuell_ph": "exact model id",
    "vision.modell.manuell_knopf": "Check this id",
    "vision.modell.manuell_satz":
        "For endpoints that do not list everything: the id is checked with "
        "a tiny text request first; nothing unchecked can be saved.",
    "vision.prompt.standard_satz":
        "This is the measured default wording. As long as you leave it "
        "exactly like this, verdicts are not marked as custom.",
    "vision.prompt.titel": "The question suslik asks",
    "vision.prompt.satz":
        "You can change the wording. The last paragraph is fixed: it is "
        "the one-word instruction the answer parser depends on, and it is "
        "what was measured.",
    "vision.prompt.knopf_zurueck": "Reset to default",
    "vision.zahlen.think": "Turn the model&rsquo;s thinking off",
    "vision.zahlen.think_satz":
        "On since 0.1.0.211 by default: on hard comparison grids a "
        "thinking model can talk itself past the token budget and the run "
        "ends without a verdict. Strict endpoints reject the switch; "
        "suslik then repeats the request once without it and says so.",
    "vision.zahlen.titel": "Limits",
    "vision.zahlen.max_tokens": "Max tokens per answer",
    "vision.zahlen.timeout": "Timeout per request (s)",
    "vision.zahlen.satz":
        "3000 tokens was measured to be not enough on one run &mdash; the "
        "answer was cut off and counted as no verdict, and the same "
        "question was right with 12000. A local model on a CPU machine "
        "needs minutes per request, an online one seconds.",
    "vision.cloud.ziel_fallback": "the endpoint you configure above",
    "vision.cloud.titel": "Sending pictures to an outside service",
    "vision.cloud.satz":
        "Those pictures are not only of the people who live here: the "
        "uncertain cases are mostly strangers &mdash; visitors, delivery "
        "drivers, neighbours, passers-by. You are the one responsible for "
        "that, not the operator of the service. Your confirmation is "
        "written to the audit log with a timestamp; switching back to a "
        "local model withdraws it.",
    "vision.cloud.bestaetigung": "I understand and confirm this",
    "vision.cloud.bestaetigt": "(confirmed {zeit})",
    "vision.test.treffer": "{n}/2 right",
    "vision.test.tokens": "{ist} tokens vs {soll}",
    "vision.test.falsch": " (wrong)",
    # ZITAT-FOLGE: js.vision.dirty_text UND js.vision.prompt_zurueck
    # zitieren diesen Knopf woertlich ("Save connection") — beim
    # Uebersetzen/Aendern beide nachziehen.
    "vision.save.knopf": "Save connection",
    "vision.save.dirty":
        "unsaved changes &mdash; recognition still uses the saved "
        "connection",
    "vision.test.titel": "Test this connection",
    "vision.test.knopf": "Run the test",
    "vision.test.nicht_gelaufen": "not run",
    "vision.test.stufe1": "reachability",
    "vision.test.stufe2": "forced choice",
    "vision.test.stufe3": "token audit",
    "vision.test.ungetestet": "Not tested yet.",
    "vision.test.letzter": "Last run {zeit} against",
    "vision.galerien.stand_gut": "approved {zeit} &middot; {zellen} cells",
    "vision.galerien.pruefen": "needs a look",
    "vision.galerien.keine": "no gallery yet",
    "vision.galerien.zu_wenig":
        "not enough approved body images yet ({n} usable)",
    "vision.galerien.knopf_auffrischen": "Refresh it",
    "vision.galerien.knopf_bauen": "Build a gallery",
    "vision.galerien.zahl": "{n} usable images &middot; {reihen}",
    "vision.galerien.titel": "Galleries",
    "vision.galerien.stand":
        "{n} galleries ready ({min} required) &mdash; vision needs at "
        "least two, because it always compares one person against another.",
    "vision.galerien.satz":
        "Only people with a learned body model can get a gallery; the "
        "images come from the body material you already approved. Vision "
        "only ever judges people who have one, and it says so on the "
        "verdict.",
    # --- routes/visiontest.py ---
    "visiontest.titel": "Recognition test",
    "visiontest.kopf.satz":
        "Face and person are read from what was recorded at the time "
        "&mdash; nothing is recomputed. Vision runs now, through exactly "
        "the same path it uses in normal operation.",
    # Frueher Modulkonstante KOSTEN — §8.12: t() nie auf Modulebene.
    "visiontest.kosten":
        "A test run costs real requests, exactly like normal operation: "
        "the whole walk-through goes in as one candidate grid, and each "
        "compared pair of galleries costs two requests, because every "
        "question is asked again with the galleries swapped. It counts as "
        "a manual click, so it does not eat your daily limit &mdash; but "
        "on a paid endpoint it is money, and on a local CPU model it "
        "takes minutes.",
    "visiontest.wer.niemand": "nobody recognized",
    # EN-Klammerformen ("camera(s)", "pass(es)") bleiben EINE Form je
    # Schluessel (§8.18) — echter Plural waere eine bewusste Textaenderung.
    "visiontest.wahl.kachel_zahlen":
        "{events} events &middot; {kameras} camera(s)",
    "visiontest.wahl.vision_fertig": " &middot; vision done",
    "visiontest.wahl.titel": "1 &middot; Which walk-through",
    "visiontest.wahl.leer":
        "No passes recorded yet. As soon as somebody walks across the "
        "property, they appear here.",
    "visiontest.wahl.kopf_zahlen":
        "{events} event(s) &middot; {kameras} camera(s)",
    "visiontest.wahl.anderer": "choose another walk-through",
    "visiontest.wahl.titel_offen": "1 &middot; Choose a walk-through",
    "visiontest.wahl.anzahl": "{n} recent pass(es)",
    "visiontest.wahl.satz":
        "The most recent passes, grouped exactly like on the Today page.",
    "visiontest.gesicht.kein_match": "not matched",
    "visiontest.gesicht.gezeigt": "showing {gezeigt} of {gesamt} picture(s)",
    "visiontest.gesicht.ohne_bild":
        "{fehlt} of the {unbek} unmatched event(s) kept no picture",
    "visiontest.gesicht.kein_bild":
        "no face picture was kept for this pass",
    "visiontest.gesicht.keines": "no known face",
    "visiontest.gesicht.zeile": "{person} &middot; {events} event(s)",
    # {best} vorformatiert (:.2f) aus der Route (§8.8).
    "visiontest.gesicht.best": " &middot; best {best}",
    "visiontest.gesicht.unbekannt":
        "{n} event(s) with a face that was not matched",
    "visiontest.gesicht.titel": "Face",
    "visiontest.gesicht.quelle":
        "embedding comparison against your reference faces &mdash; from "
        "the record of this pass",
    "visiontest.koerper.kandidaten":
        "candidates, none above the rule: {liste}",
    "visiontest.koerper.nichts": "nothing judged",
    "visiontest.koerper.zeile":
        "{klasse} &middot; score {score} of {schwelle} &middot; {quelle}",
    "visiontest.koerper.bild_weg": "image expired",
    "visiontest.koerper.titel": "Person",
    "visiontest.koerper.quelle":
        "DINOv2 embedding + classifier on the judged images of this pass",
    "visiontest.log.warte":
        "waiting for the model &mdash; this page refreshes itself",
    "visiontest.log.titel": "What happened",
    "visiontest.gitter.alt": "the candidate grid of this run",
    "visiontest.gitter.bildunterschrift":
        "the picture the model was actually shown",
    "visiontest.gitter.zeile":
        "candidate grid: {n} cell(s) from this walk-through, asked as ONE "
        "picture",
    "visiontest.gitter.luecken": " ({n} cell(s) left empty)",
    "visiontest.runden.kein_votum": "no vote &mdash; {grund}",
    "visiontest.runden.paar": "{a} vs {b}",
    "visiontest.nach.laeuft": "Re-analysing this walk-through",
    "visiontest.nach.stand":
        "{fertig} of {gesamt} events done &mdash; the judged images are "
        "collected along the way, this takes a few minutes. It is quiet: "
        "no alerts, no notifications. This page refreshes itself.",
    "visiontest.nach.titel": "Nothing was kept for this walk-through",
    "visiontest.nach.satz":
        "Analysing it again brings the judged images back &mdash; and that "
        "fills all three paths, not just vision. It runs the ordinary "
        "analysis over the events of this pass once more: quiet, without "
        "alerts, and it waits for live recognition instead of pushing it "
        "aside.",
    "visiontest.nach.knopf": "Analyse this walk-through again",
    "visiontest.felder.zellen": "grid cells for this run",
    "visiontest.felder.voten": "confirmations needed for this run",
    "visiontest.felder.doppel": "ask each pair twice (swap check)",
    "visiontest.felder.satz":
        "All three apply to THIS run only &mdash; nothing is saved and "
        "normal operation keeps its own settings. This walk-through has "
        "{material} usable picture(s) &mdash; asking for more cells than "
        "that is fine, the grid just gets smaller. {galerien} approved "
        "galleries allow at most {voten_max} comparison(s). With the swap "
        "check on, a comparison costs two requests; without it, one "
        "&mdash; and it then rests on a single answer.",
    "visiontest.laeufe.abgebrochen": "aborted (service restarted)",
    "visiontest.laeufe.kein_urteil": "no verdict",
    "visiontest.laeufe.von": "of {n}",
    "visiontest.laeufe.ohne_tausch": "no swap",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} open",
    "visiontest.laeufe.titel": "Runs on this walk-through",
    "visiontest.laeufe.kopf_wann": "when",
    "visiontest.laeufe.kopf_zellen": "cells",
    "visiontest.laeufe.kopf_noetig": "needed",
    "visiontest.laeufe.kopf_backend": "backend",
    "visiontest.laeufe.kopf_urteil": "verdict",
    "visiontest.laeufe.kopf_voten": "votes",
    "visiontest.laeufe.kopf_anfragen": "req",
    "visiontest.laeufe.kopf_zeit": "time",
    "visiontest.laeufe.satz":
        "Newest first. Only what was really run &mdash; the list comes "
        "from this walk-through's own log and disappears with it.",
    "visiontest.vision.titel": "Vision",
    "visiontest.vision.quelle_kurz":
        "a vision model comparing this pass against your galleries",
    "visiontest.vision.unkonfiguriert": "not configured",
    "visiontest.vision.attr_nichts": "there is nothing to compare yet",
    "visiontest.vision.knopf": "Run vision on this pass",
    "visiontest.vision.nichts_satz":
        "nothing to compare yet &mdash; analyse this walk-through again "
        "first (button above)",
    "visiontest.vision.laeuft_satz":
        "a run is going right now &mdash; the log below grows as it works",
    "visiontest.vision.startet": "starting &mdash; nothing reported yet",
    "visiontest.vision.quelle":
        "forced choice against your galleries: the whole walk-through "
        "goes in as ONE candidate grid, and every pair is asked twice "
        "with the galleries swapped",
    "visiontest.vision.nicht_gelaufen": "not run for this pass",
    "visiontest.vision.verglichen":
        "compared {a} against {b} &mdash; it says nothing about anyone "
        "else",
    "visiontest.vision.abgebrochen":
        "run aborted &mdash; the service restarted",
    "visiontest.vision.kein_urteil": "no verdict &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten} of {bilder} comparison(s) gave an answer &middot; "
        "{anfragen} requests &middot; {dauer} s &middot; run {zeit}",
    "visiontest.vision.reihenfolge": " &middot; order: {quelle}",
    "visiontest.vision.custom_prompt": " &middot; custom prompt",
    "visiontest.drei.titel": "2 &middot; What the three paths say",
    "visiontest.drei.satz":
        "Same pass, three independent judgements. They are allowed to "
        "disagree &mdash; that is the point of looking at them together.",
    # --- routes/visionwizard.py ---
    "visionwizard.schritt.person": "pick a person",
    "visionwizard.schritt.groesse": "pick a size",
    "visionwizard.schritt.vorschlag": "check the proposal",
    "visionwizard.schritt.abnahme": "approve",
    "visionwizard.titel": "Build a gallery",
    "visionwizard.kopf.satz":
        "A gallery is a small grid of pictures of one person &mdash; that "
        "is what the vision model compares a new picture against. It is "
        "built from body images you already approved; nothing new is "
        "recorded and no video is opened.",
    "visionwizard.person.stand_gut": "gallery approved {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} usable images &mdash; not enough for a gallery yet. Run "
        "Person learn on more walk-throughs.",
    "visionwizard.person.max_gitter":
        "largest grid this material supports: {n}",
    "visionwizard.person.titel": "1 &middot; Which person",
    "visionwizard.person.satz":
        "Only people with a learned body model appear here, and the counts "
        "are the images that pass the size filter (at least 350 pixels "
        "tall) &mdash; not everything that was ever harvested.",
    "visionwizard.groesse.zellen": "{n} cells",
    "visionwizard.groesse.titel": "2 &middot; How many pictures",
    "visionwizard.zelle.leer":
        "no more images for this row &mdash; and nothing left to borrow "
        "either",
    "visionwizard.zelle.geliehen": "from the {reihe} row",
    "visionwizard.zelle.knopf_weg": "does not fit",
    "visionwizard.reihe.geliehen":
        "{n} filled from another view &mdash; there were not enough clean "
        "{reihe} images",
    "visionwizard.reihe.luecken": "{n} cell(s) could not be filled at all",
    "visionwizard.reihe.spreizung": "{tage} day(s), {kameras} camera(s)",
    "visionwizard.reihe.kopf": "{reihe} view",
    "visionwizard.reihe.eigene": "{eigene} of {gesamt} from this view",
    "visionwizard.vorschlag.abgelehnt":
        "{n} image(s) you rejected earlier are remembered and will not "
        "come back.",
    "visionwizard.vorschlag.titel": "3 &middot; Does this fit?",
    "visionwizard.vorschlag.grenze":
        "Honest limit: those are measurements of the picture, not of the "
        "moment. A picture where someone is tying their hair or bending "
        "down looks fine to every one of them &mdash; that is what your "
        "eyes are for.",
    "visionwizard.vorschlag.knopf": "Approve this gallery",
    "visionwizard.vorschlag.kopie_satz":
        "Approving copies these pictures into the gallery folder. From "
        "then on the gallery is fixed: deleting an original later cannot "
        "punch holes into it &mdash; suslik only asks you to approve it "
        "again.",
    "visionwizard.fertig.geliehen": " &middot; borrowed",
    "visionwizard.fertig.titel": "Approved gallery",
    "visionwizard.fertig.stand": "{zellen} cells, approved {zeit}.",
    "visionwizard.fertig.satz":
        "These are copies inside the gallery folder, with the origin of "
        "every picture (run, file, checksum) written next to them. They "
        "travel with your backup.",
    "visionwizard.fertig.knopf_neu": "Build it again from current material",
    "visionwizard.fertig.knopf_zurueck": "Back to Vision detect",
    "visionwizard.neu.titel": "New material available",
    "visionwizard.neu.satz":
        "Nothing changes on its own &mdash; the gallery you approved "
        "stays exactly as it is until you build and approve a new one.",
    # --- routes/personwizard.py ---
    "personwizard.wer.alle": "all known people",
    "personwizard.wer.fremde": "strangers",
    "personwizard.titel": "Learn people — body recognition",
    "personwizard.kopf.satz":
        "A second, independent recognition path: it learns what a person "
        "looks like as a WHOLE (build, hair, posture) so it can recognize "
        "residents even when no face is visible.",
    "personwizard.kopf.wie_titel": "How this works — you stay in control",
    "personwizard.kopf.schritt1":
        "1 · You choose how many events to scan and WHO to learn (one "
        "person, or all known people).",
    "personwizard.kopf.schritt2":
        "2 · The run harvests full-body images from your own recordings. "
        "A picture is tied to a person only when a face-confirmed "
        "walk-through proves it — deliberately conservative.",
    "personwizard.kopf.schritt3":
        "3 · YOU review every harvested image; one click rejects a wrong "
        "one. Nothing is learned without your approval.",
    "personwizard.kopf.schritt4":
        "4 · Training then runs locally in seconds, and a decision "
        "threshold is measured so strangers stay below it.",
    "personwizard.kopf.tempo":
        "A note on speed: harvesting currently runs on the CPU, so please "
        "bear with a run taking a little while (roughly 15&ndash;30 s per "
        "event). Moving this to the GPU/NPU is planned for a later "
        "version.",
    "personwizard.kopf.warum":
        "Why at least one person first: this path can only tell people "
        "apart after it has learned — and you have reviewed — what at "
        "least one resident looks like. Until then body recognition stays "
        "OFF and never sends an alert. When it does alert later "
        "(Pushover/Telegram), the message is marked as coming from person "
        "recognition, not from face recognition.",
    "personwizard.vorb.titel": "Preparing the run &hellip;",
    "personwizard.vorb.zeile":
        "tying the last {n} events to {wer} via confirmed walk-throughs",
    "personwizard.vorb.satz":
        "This takes a minute or two — the page refreshes on its own, "
        "harvesting starts right after.",
    "personwizard.ernte.stand":
        "{events}/{von} events · {bilder} images harvested",
    "personwizard.ernte.startet": "starting …",
    "personwizard.ernte.titel": "A person-learn run is active",
    "personwizard.ernte.zeile": "learning {wer} · {stand}",
    "personwizard.ernte.satz":
        "This page refreshes on its own. A new run can be started once it "
        "finishes.",
    "personwizard.ernte.knopf_abbruch": "Abort run",
    "personwizard.ernte.abbruch_hinweis": "harvested images are kept",
    "personwizard.unterbrochen.titel": "Last run was interrupted",
    "personwizard.unterbrochen.satz":
        "Probably a service restart. Start the same run again below — "
        "already-harvested events are skipped automatically (resume), "
        "nothing is lost.",
    "personwizard.abnahme.titel": "Last run finished — your review is next",
    "personwizard.abnahme.zeile":
        "{n} images harvested for {wer} (run {lauf}).",
    "personwizard.abnahme.knopf": "Review the images now",
    "personwizard.abnahme.hinweis":
        "finish the review to unlock the next run",
    "personwizard.abnahme.knopf_verwerfen": "Discard this run",
    "personwizard.abnahme.verwerfen_hinweis":
        "bad result? throw it all away",
    "personwizard.leer.verwaist":
        "Skipped on purpose: {liste} — these names were deleted from your "
        "people; their old confirmed events stay as history but are not "
        "harvested.",
    "personwizard.leer.titel":
        "Run finished without images — here is why",
    "personwizard.leer.satz":
        "Nothing was changed; you can start another run below any time.",
    "personwizard.fertig.verwaist":
        "Skipped on purpose: {liste} — deleted people; their old confirmed "
        "events are not harvested.",
    "personwizard.fertig.fremd":
        "{n} confirmed stranger images moved into the stranger pool — the "
        "next training uses them right away.",
    "personwizard.fertig.titel": "Review finished — material adopted",
    "personwizard.fertig.zeile":
        "{abgenommen} images approved as learning material, {verworfen} "
        "rejected (run {lauf}).",
    "personwizard.fertig.knopf": "View the learned material",
    "personwizard.fehler.titel": "Last run failed",
    "personwizard.auswahl.opt_alle": "All known people",
    "personwizard.auswahl.opt_fremde":
        "Strangers — collect stranger images",
    "personwizard.auswahl.titel": "Who to learn",
    "personwizard.auswahl.satz":
        "Pick one person to review in small, focused batches — or all at "
        "once. People come from your face collection; learning one at a "
        "time keeps the review short.",
    "personwizard.auswahl.fremde_satz":
        "Strangers: harvests walk-throughs where nobody was recognized "
        "(street-only passes, unconfirmed visitors). You confirm in the "
        "review which really are strangers — they go into the stranger "
        "pool and sharpen the decision threshold.",
    "personwizard.umfang.knopf_letzte": "last {n}",
    "personwizard.umfang.attr_eigen": "own N",
    "personwizard.umfang.knopf_go": "go",
    "personwizard.umfang.titel": "Scope (events, not days)",
    "personwizard.umfang.satz":
        "Start small (50) — you will review every harvested image by "
        "hand.",
    "personwizard.bilanz.ohne":
        "last {n} person events for {wer} — the binding balance is "
        "computed when the run is created",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/nach rahmen die
    # hervorgehobene Zahl, Rand-Leerzeichen gehoeren zum Wert.
    "personwizard.bilanz.zahl_vor": "last {n} person events · ",
    "personwizard.bilanz.zahl_nach":
        " can be tied to {wer} via confirmed walk-throughs",
    "personwizard.bilanz.fremd": " · {n} stranger candidates",
    "personwizard.bilanz.erkl_fremd":
        "Candidates are walk-throughs where nobody was recognized — "
        "street-only passes and unconfirmed visitors. Everything is a "
        "SUSPICION until your review; mark anyone who is NOT a stranger "
        "there.",
    "personwizard.bilanz.erkl":
        "Tying is conservative: only walk-throughs with exactly one "
        "face-confirmed person count. Everything you see afterwards can "
        "be rejected with one click.",
    "personwizard.bilanz.titel": "Your selection",
    "personwizard.bilanz.knopf": "Create this run",
    "personwizard.review.stempel": "WRONG",
    "personwizard.review.h_fremde": "Strangers",
    "personwizard.review.frage_fremd":
        "click every image that is NOT a stranger (a resident, a known "
        "visitor) or unusable. A second click takes it back. Everything "
        "is saved instantly; unmarked images are adopted as confirmed "
        "strangers and sharpen the decision threshold.",
    "personwizard.review.frage":
        "click every image that is WRONG (not this person, or unusable). "
        "A second click takes it back. Everything is saved instantly; "
        "unmarked images count as approved.",
    "personwizard.review.titel": "Review the harvest",
    "personwizard.review.kopf": "Run {lauf} — {frage}",
    # Der Zeilenumbruch ist Teil des Originals (Template-Literal) und
    # bleibt fuer die Byte-Treue im Wert.
    "personwizard.review.zurueck": "&larr; back to the\nwizard",
    "personwizard.review.knopf_fertig":
        "Finish review — adopt approved images",
    "personwizard.kontrolle.sammeln_titel": "Collect mode is ON",
    "personwizard.kontrolle.sammeln_rest":
        " — every judged image is kept for 30 days so you can check the "
        "decisions later. Expect roughly 20&ndash;40 MB a day.",
    "personwizard.kontrolle.schlank_titel": "Lean mode (default)",
    "personwizard.kontrolle.schlank_rest":
        " — judged images only live while a pass is running; afterwards "
        "only the winning image and the verdict log below remain. This is "
        "the privacy-friendly default for a fresh installation.",
    "personwizard.kontrolle.titel": "Judged images",
    "personwizard.kontrolle.satz":
        "What body recognition actually looked at, one block per "
        "walk-through: the image it judged, the class it came out with, "
        "the score, and where the picture came from. Useful when a person "
        "was missed, or someone was recognized who should not have been.",
    "personwizard.kontrolle.leer_titel": "Nothing recorded yet",
    "personwizard.kontrolle.tag_fremd": "stranger",
    "personwizard.kontrolle.tag_drueber": "above threshold",
    "personwizard.kontrolle.tag_drunter": "below threshold",
    "personwizard.kontrolle.schwelle": " &middot; thr {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} judged, {n} image kept",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} judged, {n} images kept",
    "personwizard.tabelle.fremd_zeile": "Strangers (extra class)",
    "personwizard.tabelle.kein_fremd":
        "No stranger class yet — recognition works much better with one: "
        "confirmed stranger images teach the model what does NOT belong "
        "and calibrate the decision threshold.",
    "personwizard.tabelle.q_eichung": "measured",
    "personwizard.tabelle.q_user": "set by you",
    "personwizard.tabelle.q_standard": "built-in default",
    "personwizard.tabelle.f_modell": "Active model",
    "personwizard.tabelle.f_schwelle": "Threshold",
    "personwizard.tabelle.f_scharf": "Armed",
    "personwizard.tabelle.scharf_ja": "YES",
    "personwizard.tabelle.scharf_ja_rest": " — judging live",
    "personwizard.tabelle.scharf_nein": "no — not armed",
    "personwizard.tabelle.konf_vor":
        "Largest cross-group confusion in the calibration: ",
    "personwizard.tabelle.konf_nach":
        " — the strongest score any image reached for the WRONG group; "
        "the closer to 1, the closer two groups are.",
    "personwizard.tabelle.titel": "Learned groups",
    "personwizard.karte.scharf": "Armed",
    "personwizard.karte.unscharf": "Not armed yet",
    "personwizard.karte.fehler":
        "Last training attempt FAILED: {fehler} — this card shows the "
        "previous model.",
    "personwizard.karte.titel": "Model status",
    "personwizard.karte.zeile":
        "trained {wann} in {dauer} s — {bilder} images: {je} · {modell} · ",
    "personwizard.karte.link": "details",
    "personwizard.bestand.titel":
        "Person material — what has been learned",
    "personwizard.bestand.satz":
        "Approved full-body images per person. Pick a group below to see "
        "its images; delete a single image (&times; on the tile) — a new "
        "run can always re-harvest afterwards. Deletions take effect on "
        "the next training.",
    "personwizard.bestand.leer_titel": "No approved material yet",
    "personwizard.bestand.stark_titel": "What makes this model strong",
    "personwizard.bestand.chip_fremde": "Strangers ({n})",
    "personwizard.bestand.zeigen_titel": "Show images of",
    "personwizard.bestand.zeigen_satz":
        "Pick a group — its images open below, newest first.",
    "personwizard.bestand.marker_tage.eins":
        "only {n} day — recognition improves most with images from more "
        "days, outfits and light",
    "personwizard.bestand.marker_tage.viele":
        "only {n} days — recognition improves most with images from more "
        "days, outfits and light",
    "personwizard.bestand.attr_loeschen": "delete this image",
    "personwizard.bestand.z_bilder": "{n} images",
    "personwizard.bestand.z_tage.eins": "{n} day",
    "personwizard.bestand.z_tage.viele": "{n} days",
    "personwizard.bestand.z_kameras.eins": "{n} camera",
    "personwizard.bestand.z_kameras.viele": "{n} cameras",
    "personwizard.modell.titel": "Person model — status",
    "personwizard.modell.satz":
        "The body-recognition model, trained from your approved images. "
        "It retrains automatically after every finished review and after "
        "deletions.",
    "personwizard.modell.leer_titel": "No model yet",
    "personwizard.modell.fremd_keine":
        "none yet — threshold measured between your people only",
    "personwizard.modell.fremd_gesammelt":
        "{n} collected — {min} needed before they are trained and "
        "calibrate the threshold",
    "personwizard.modell.fremd_geeicht":
        "{n} in training · threshold calibrated against real strangers",
    "personwizard.modell.fremd_ungeeicht":
        "{n} in training — the threshold calibration did not run (see the "
        "note below)",
    "personwizard.modell.f_trainiert": "Trained",
    "personwizard.modell.f_dauer": "Training time",
    "personwizard.modell.f_modell": "Model",
    "personwizard.modell.f_bilder": "Images total",
    "personwizard.modell.f_personen": "Persons",
    "personwizard.modell.f_fremd": "Stranger negatives",
    "personwizard.modell.scharf_ja": "YES — live judging active",
    "personwizard.modell.scharf_nein": "no — not armed yet",
    "personwizard.modell.fehler":
        "Last training attempt FAILED ({zeit}): {fehler} — the model "
        "shown here is the previous one and does not include your latest "
        "changes.",
    "personwizard.modell.aktuell_titel": "Current model",
    "personwizard.modell.material_titel": "Learning material per person",
    "personwizard.modell.kopf_person": "person",
    "personwizard.modell.kopf_bilder": "approved images",
    "personwizard.modell.kopf_anteil": "share",
    "personwizard.modell.summe": "total",
    "personwizard.modell.q_eichung": "measured on your material",
    # {pct} vorformatiert (round) aus der Route (§8.8).
    "personwizard.modell.eich_fremd":
        "Measured by {folds}-fold cross-validation over {n} held-out "
        "images of your people plus {n_fremd} confirmed strangers: the "
        "strongest resident confidence any real stranger reached was "
        "{max} &rarr; threshold {schwelle}; {pct}% of the genuine images "
        "pass. The other side of the coin: {ueber} of your own images "
        "would reach that threshold for the WRONG person (strongest "
        "{vmax}).",
    "personwizard.modell.eich_intern":
        "Measured by {folds}-fold cross-validation over {n} held-out "
        "images: strongest confidence for a WRONG person {max} &rarr; "
        "threshold {schwelle}; {pct}% of the genuine images pass. Honest "
        "limit: this calibrates BETWEEN your learned people — real "
        "strangers are not in the material yet.",
    "personwizard.modell.regeln_titel": "Judgment settings",
    "personwizard.modell.schwelle_vor": "Decision threshold: ",
    "personwizard.modell.r_fenster": "Fire window",
    "personwizard.modell.r_feuer": "Supporting events to fire",
    "personwizard.modell.r_karenz": "Cool-down after an alert",
    "personwizard.modell.regeln_satz":
        "Leave the threshold empty to follow the measured value "
        "automatically (it re-measures with every training). The fire "
        "rule: alert only after this many supporting events inside the "
        "window, then stay quiet for the cool-down.",
    "personwizard.modell.knopf_speichern": "Save settings",
    "personwizard.modell.satz_user":
        "The decision threshold is set by you ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — the calibration against {n} confirmed strangers would be "
        "{alt}",
    "personwizard.modell.satz_geeicht":
        "The decision threshold is calibrated against {n} confirmed "
        "stranger images.",
    "personwizard.modell.satz_ungeeicht":
        "The decision threshold is not yet calibrated against stranger "
        "material — treat alerts as a preview and keep an eye on them.",
    "personwizard.modell.satz_fremd_drop":
        " A body the model reads as a stranger is dropped before it can "
        "become a hit.",
    "personwizard.modell.live_titel": "Live switch",
    "personwizard.modell.live_an":
        "ARMED — the body path judges live events and may alert.",
    "personwizard.modell.live_aus":
        "Not armed — the body path stays silent.",
    "personwizard.modell.live_hinweis":
        "Alerts carry the note &quot;person recognition, not face&quot;.",
    "personwizard.modell.knopf_disarm": "Disarm",
    "personwizard.modell.knopf_arm": "Arm body recognition",
    # --- webui/bausteine.py ---
    # Nur die gt_leiste-ANZEIGE-Texte; die Speicherwerte (GT_OFFEN_LABELS,
    # GT_KEIN_MENSCH) und KAT_LABELS/KAT_FARBE bleiben literal (Kommentar
    # im Modul: §8.12/§8.13, Meldetext-Mitnutzung).
    "baustein.gt.fremd": "Stranger",
    "baustein.gt.kein_mensch": "No person",
    "baustein.gt.add": "add person…",
    "baustein.gt.uebernehmen": "confirm this suggestion (everyone listed was there)",
    "baustein.gt.fremd_titel": "a stranger was there (can stand next to names)",
    "baustein.gt.unklar_titel": "not sure — leave it open",
    "baustein.gt.kein_mensch_titel": "no person in this event (false trigger)",
    "baustein.gt.opak_titel": "an old judgement that no longer matches a known person — pick ? or a name to replace it",
    # ---- Route-JS + Meldungen (Stufe 2, Tranche D) ----
    # Drei Text-Gattungen: (1) Inline-<script>-Texte der Routen (§8.4) —
    # server-seitig via json.dumps(t(...)) bzw. bausteine.js_literal()
    # BYTE-TREU injiziert (json.dumps ensure_ascii=True reproduziert die
    # \uXXXX-Escapes des Originals; js_literal fuer einfach-quotierte
    # Kontexte). (2) JSON-msg-Felder der POST-Handler in verifyd.py
    # (Praefix antwort.*, server-seitiges t() — die Sprache ist je Request
    # als contextvar aktiv) inkl. der beiden text/plain-Clip-Antworten.
    # (3) Konstante->Schluessel-Umzuege (Kennung/Anzeige-Trennung):
    # registry.VISION_EXPORT_HINWEIS, visiongalerie.REIHEN_ANZEIGE,
    # bausteine.KAT_LABELS, vertrauen.LABELS — NUR die UI-Anzeige wird
    # sprachfaehig, Speicher-/Log-/Meldewerte bleiben englische Kennungen.
    # Grenzen dieser Tranche stehen als Stufe-2-Grenze-Marker im Code:
    # JS-Zaehler mit Laufzeit-Plural (§8.18), Name+Zaehler-Konkatenationen
    # ohne byte-treue Splitstelle, deutsche Alt-msg (de->en = bewusste
    # Textaenderung), Fachschicht-msg (anlernen/svc/core-Helfer),
    # GATE-Protokollwort (§8.16), Log-geteilte msg-Bausteine.
    # Deklarierte Splits: Zaehler-/Fragment-Splits an Konkatenationsgrenzen
    # (§8.10-Muster setupwiz.import.zahl_*) — js_zaehl_*, js_gespeichert_*,
    # koll_*, review.js_frage_*; Rand-Leerzeichen gehoeren zum Wert.
    # --- routes/lernwizard.py (Zuweisungs-Flaeche + Sichtung) ---
    "lernwizard.zw.js_zaehl_mitte": " of ",
    "lernwizard.zw.js_zaehl_nach": " pictures selected",
    # Wiederverwendet aus lernanker.js.*: fehler, nicht_uebernommen,
    # nicht_gespeichert (byte-identische Texte beider Routen).
    "lernanker.js.uebernimmt": "adopting…",
    "lernanker.js.tag_frage_vor": "Settings changed since naming:\n",
    "lernanker.js.tag_frage_nach": "\nAdopt anyway with the named selection?",
    "lernanker.js.weiter": "saved — next group…",
    "lernanker.js.speichert": "saving…",
    "lernanker.js.koll_vor": "’",
    "lernanker.js.koll_mitte": "’ matches existing ’",
    "lernanker.js.koll_nach": "’ — add to that person instead?",
    "lernwizard.zw.js_gespeichert_vor": "saved as ",
    "lernwizard.zw.js_gespeichert_nach": " — checking the pictures …",
    "lernwizard.sicht.js_fehl": "check failed — reload to retry",
    "lernwizard.zw.js_verbergen": "Hide the other {n} checked pictures",
    "lernwizard.zw.js_zeigen": "Show all {n} checked pictures",
    # --- routes/qualitaet.py ---
    "qualitaet.galerie.js_gewaehlt": " selected",
    # --- routes/lernanker.py (nur dort) ---
    "lernanker.js.alle_fertig":
        "All groups done — the named pictures now count for recognition.",
    # --- routes/vision.py (Hand-ID-Script) ---
    "vision.modell.js_id_fehlt": "enter an id first",
    "vision.modell.js_prueft": "checking …",
    "vision.modell.js_fehler": "error",
    # --- routes/personwizard.py (Review-Script + Schalter) ---
    "personwizard.review.js_zaehl": " of {n} marked wrong",
    "personwizard.review.js_frage_vor": "Finish the review? ",
    "personwizard.review.js_frage_mitte":
        " images will be adopted as learning material, ",
    "personwizard.review.js_frage_nach": " rejected.",
    "personwizard.modell.js_fehler": "error ",
    # --- verifyd.py POST-Antworten (antwort.*, Nutzungs-Reihenfolge) ---
    "antwort.person_entfernt":
        "{person} removed ({n} reference images moved to trash — "
        "recoverable)",
    "antwort.person_name_ungueltig": "invalid name",
    "antwort.person_unbekannt": "unknown person",
    "antwort.pruefung_gestartet": "check started",
    "antwort.reorg_los":
        "Reorganizing (pool re-check + re-cluster, 1-2 min, then reload "
        "the pages)",
    "antwort.reorg_laeuft": "Reorganizing already running — please wait",
    "antwort.paar_notiert": "noted — won't suggest this pair again",
    "antwort.unbek_objekt": "marked as not a person",
    "antwort.unbek_person": "back among the visitors",
    "antwort.unbek_gemergt": "{n} groups merged into one",
    # §8.11-Anhang an eine Fachschicht-msg (die Basis bleibt Grenze).
    "antwort.nachpruefung_anhang":
        " — re-checking this pass's events in the background",
    "antwort.sync_wieder": "{n} back on the candidate list",
    "antwort.sync_auswahl": "{ab} deselected, {zu} restored",
    "antwort.sync_laeuft": "a sync is already running — wait for it to finish",
    "antwort.sync_readonly":
        "read-only mode: writing references to Frigate is disabled (see "
        "the System page switch)",
    "antwort.sync_nichts": "nothing selected — tick at least one image",
    "antwort.frigate_url": "Frigate URL: {fehler}",
    "antwort.sync_transfer": "transfer running ({n} selected)",
    "antwort.bruecke_hinzu": "{n} picture(s) added",
    "antwort.modell_laedt":
        "loading the recognition model — a few seconds …",
    "antwort.refcache_baut":
        "rebuilding the reference library — with a large library this can "
        "take a minute …",
    "antwort.refcache_fehler":
        "rebuilding the reference library failed twice in a row — see the "
        "service log (/log); the next attempt runs in a few minutes",
    "antwort.cache_aufgeraeumt": "{n} clip(s) removed, {mb} MB freed — cache {cache} GB, {frei} GB free",
    "antwort.bruecke_nimmt": "the check picks {n} picture(s)",
    "antwort.bruecke_grenz_zusatz": " · {n} borderline shown unticked",
    "antwort.bruecke_nur_grenz":
        "nothing clearly helpful — {n} borderline picture(s) kept back "
        "(identity sure, picture quality only fair); you can still take "
        "them",
    "antwort.bruecke_nichts":
        "nothing to take — no helpful new picture in this pass (that is "
        "fine)",
    "antwort.bruecke_undo": "{n} picture(s) removed again",
    "antwort.personlauf_kein_review": "no run awaiting review",
    "antwort.personlauf_kein_lauf": "no active run",
    "antwort.events_bereich": "events must be 1..{max}",
    "antwort.personlauf_aktiv": "a person-learn run is already active",
    "antwort.lernlauf_tag_ungueltig": "invalid day (YYYY-MM-DD)",
    # {phase} ist die interne Phasen-Kennung (sprachneutral, §8.19).
    "antwort.lernlauf_phase":
        "a run is already in phase '{phase}' — abort it first",
    "antwort.lernlauf_beschaeftigt":
        "the previous run is still finishing its current event — try "
        "again in a moment",
    "antwort.lernlauf_schreibfehler": "could not write run state: {fehler}",
    "antwort.lernlauf_angelegt": "run created",
    "antwort.lernlauf_abgebrochen":
        "aborted — a running event may still finish in the background",
    "antwort.live_nichts": "nothing to change",
    "antwort.live_nachtests": "{n} source check(s) run one after another automatically; each watcher starts once its check passes",
    "antwort.live_an": "started {ok}/{alle} watcher(s)",
    "antwort.live_aus": "stopped {ok}/{alle} watcher(s)",
    "antwort.vision_modell_ok":
        "model answered — added to the list as manually checked; pick it "
        "there and save",
    "antwort.restore_upload_fehlt": "missing or oversized upload",
    "antwort.restore_upload_kaputt": "upload truncated",
    "antwort.backend_unbekannt": "unknown backend '{backend}'",
    "antwort.kameras_fehlen": "Frigate cameras not available: {fehler}",
    "antwort.setup_gespeichert": "Setup saved — restarting",
    "antwort.kameras_gespeichert": "{n} cameras saved — restarting",
    "antwort.name_ungueltig":
        "invalid person name (2-40 letters, digits, space, -)",
    "antwort.anker_unbekannt": "unknown anchor",
    "antwort.anker_benannt":
        "named '{name}' — {n} images selected, adopt it with the Adopt "
        "button",
    "antwort.anker_nur_unadoptiert":
        "only groups without adopted pictures can be dismissed",
    "antwort.anker_verworfen":
        "deleted — {n} pictures removed",
    "antwort.lauf_id_ungueltig": "invalid run id",
    "antwort.lauf_aktiv": "this run is still active — abort it first",
    "antwort.lauf_nichts": "nothing found for run {lauf} — already deleted?",
    "antwort.lauf_nur_einer": "nothing to delete — only one run in the store",
    "antwort.gruppe_unbekannt": "unknown or closed group",
    "antwort.sichtung_laeuft": "checking pictures — a few seconds …",
    "antwort.anker_unbenannt": "anchor is not named (or unknown)",
    "antwort.benennen_mismatch":
        "your selection did not match any image of this cluster — reload "
        "the page and tick the images again",
    "antwort.adopt_nichts":
        "nothing selected — tick at least one image to adopt",
    "antwort.adopt_phantom":
        "dedup matched only references that no longer exist on disk — "
        "please retry the adoption; if this persists, report it",
    "antwort.adopt_gedeckt":
        "already covered — all {n} selected image(s) are near-identical "
        "to {person}'s existing references; cluster marked as adopted, "
        "nothing copied",
    # §8.10-Plural-Split: frueher {'s' if n != 1} im f-String, jetzt t_n.
    "antwort.adopt_fertig.eins": "adopted {n} reference for '{person}'",
    "antwort.adopt_fertig.viele": "adopted {n} references for '{person}'",
    "antwort.adopt_skip": ", {n} skipped as near-identical",
    "antwort.adopt_watchdog": " — drift watchdog running (System page)",
    "antwort.areas_gespeichert.eins": "{n} area saved",
    "antwort.areas_gespeichert.viele": "{n} areas saved",
    # text/plain-Antwort der /video- und /clip-Routen (Tranche-B-Rest).
    "antwort.clip_weg": "Clip no longer in cache — retention {tage} days",
    # --- Konstante->Schluessel (Kennung/Anzeige-Trennung, Paket 3) ---
    # 3a: EN-Referenz bleibt core/registry.VISION_EXPORT_HINWEIS (Gate
    # prueft Wortgleichheit en.T == Konstante; Anzeige laeuft ueber t()).
    "system.backup.hinweis":
        "contains your API keys — treat this file like a password",
    # 3b: Anzeige-Woerter der Galerie-Reihen; Kennungen (vorn/seitlich/
    # hinten/unklar) bleiben Store-/JSON-Werte. EN == REIHEN_ANZEIGE.
    "visiongalerie.reihe.vorn": "front",
    "visiongalerie.reihe.seitlich": "side",
    "visiongalerie.reihe.hinten": "back",
    "visiongalerie.reihe.unklar": "unclear",
    # 3c: Kategorie-ANZEIGE (bausteine.kat_wort). EN == KAT_LABELS; seit
    # Stufe 4 liest auch der Push-Titel hier (meldung.titel.kategorie).
    "baustein.kat.erkannt": "Recognized",
    "baustein.kat.fremd_verdacht": "Stranger?",
    "baustein.kat.unbekannt_schwach": "Unknown (weak)",
    "baustein.kat.fehler": "Error",
    "baustein.kat.no_person": "No person found (likely false trigger)",
    "baustein.kat.uebersprungen": "Skipped at startup",
    "baustein.kat.deckung": "Match",
    "baustein.kat.widerspruch": "Conflict",
    "baustein.kat.frigate_nur": "Frigate only",
    "baustein.kat.wir_nur": "suslik only",
    "baustein.kat.beide_unknown": "Both unknown",
    # 3d: Wortstufen-ANZEIGE (bausteine.stufe_wort) — Meldetexte/Logs
    # lesen weiter core/vertrauen.label() englisch. EN == vertrauen.LABELS.
    "baustein.stufe.clear": "clear match",
    "baustein.stufe.narrow": "just above the bar",
    "baustein.stufe.below": "below the bar",
    "baustein.stufe.none": "no match",
    # ---- Anleitungen /hilfe (Stufe 3) ----
    # routes/hilfe.py: je Anleitungs-Seite ein Titel (t) + die Absaetze als
    # t_html-Schluessel (ein <p>-Absatz = ein Schluessel, B9-Granularitaet;
    # das <p> liegt IM Wert, die Werte tragen die Original-Zeilenumbrueche —
    # Byte-Treue). Die "mehr"-Bloecke (Easy plus) sind bewusst NICHT
    # eingezogen: seit .208 nicht gerendert (User-Entscheid 16.08.), als
    # Schluessel waeren sie im Deckungs-Gate tot — Einzug mit dem
    # Easy-plus-Bau (routes/hilfe.py MEHR).
    # ZITAT-KOPPLUNGEN (Uebersetzungsrunde: wortgleich je Sprache setzen):
    #  - hilfe.live.satz4 zitiert <b>Choose cameras</b>
    #    == erkennung.live.knopf_kameras (ohne das " …").
    #  - hilfe.gesicht.satz5 zitiert die Seite "Notifications"
    #    == benachrichtigungen.titel / nav.benachrichtigungen.
    #  - hilfe.gesicht.satz3 nennt die "Frigate sync page"
    #    == nav.sync_auswahl ("Frigate sync").
    #  - hilfe.gesicht.satz6 zitiert <b>Manage people</b> + <b>Register
    #    face</b> == erkennung.gesicht.knopf_verwalten /
    #    erkennung.knopf_register_face (bzw. faces.bekannt.*, wortgleich).
    #  - hilfe.koerper.satz3 zitiert <b>Register body</b>
    #    == erkennung.koerper.knopf_register.
    #  - hilfe.koerper.satz4 + hilfe.vision.satz1/satz4 zitieren die
    #    Unteroptions-Labels <b>Only if no face</b>/<b>Always</b>/<b>If
    #    needed</b> — die sind Anzeige==Kennung (§8.2) und noch LITERAL in
    #    routes/erkennung.py: erst entkoppeln, dann beides wortgleich.
    #  - hilfe.vision.satz3 nennt die "Vision page" == nav.vision
    #    ("Vision detect"); "Register vision" auf der Vision-Kachel
    #    == erkennung.vision.knopf_register (hilfe.vision "mehr"-Block,
    #    erst mit Easy plus relevant).
    "hilfe.live.titel": "Live watch, explained",
    "hilfe.live.satz1": """<p>Live watch looks at your cameras the moment something moves. When a person
steps onto the property, you get an alert within seconds, and if the system
already knows the face, the alert carries a name.</p>""",
    "hilfe.live.satz2": """<p>The name at this stage is a first guess. The thorough check runs right
after, on the recording, and has the final word.</p>""",
    "hilfe.live.satz3": """<p>Live watch does not depend on Frigate: it is not triggered by Frigate
events and runs completely on its own. It watches the video stream directly,
either Frigate's proxy stream or the camera's own stream; you choose that
per camera.</p>""",
    "hilfe.live.satz4": """<p>Use <b>Choose cameras</b> to pick which cameras get a watcher. Every watched
camera costs computing power around the clock, so start where people actually
arrive: driveway, front door, gate. You can add more later.</p>""",
    "hilfe.live.satz5": """<p>Switching a camera off here changes nothing about recording. Frigate keeps
recording as before; the switch only decides whether suslik looks at the
picture immediately or waits for the recording.</p>""",
    "hilfe.gesicht.titel": "Face recognition, explained",
    "hilfe.gesicht.satz1": """<p>This is the base way suslik recognizes and learns faces. Every recorded
pass is checked against the faces you have taught the system.</p>""",
    "hilfe.gesicht.satz2": """<p>Teaching works from your own cameras: suslik collects faces it sees, you
look at the pictures and tell it who is who. The more different situations
and poses it has seen of a person, the better it gets: daylight, evening,
hat on, hat off, from the side.</p>""",
    "hilfe.gesicht.satz3": """<p>If Frigate already knows faces, you can import them on the Frigate sync
page. The recommendation is still to learn faces here: suslik's own learning
collects many different poses and situations per person, and those
references give better results in suslik than faces taken over from
Frigate. What you teach here can be handed back to Frigate on the sync page
if you want.</p>""",
    "hilfe.gesicht.satz4": """<p>Everything stays on your machine. Nothing is uploaded anywhere, and there
is no cloud service behind it.</p>""",
    "hilfe.gesicht.satz5": """<p>When a face is recognized, or an unknown one shows up, suslik can alert you
directly: Pushover, Telegram, or MQTT for your home automation. You choose on
the Notifications page what gets sent where. These alerts are suslik's own
and work completely independent of Frigate; Frigate needs no notification
setup at all.</p>""",
    "hilfe.gesicht.satz6": """<p><b>Manage people</b> shows everyone the system knows and lets you clean
up. <b>Register face</b> starts a learning run for someone new.</p>""",
    "hilfe.koerper.titel": "Body recognition, explained",
    "hilfe.koerper.satz1": """<p>Some passes never show a usable face: the person looks away, wears a hood,
or is too far off. Body recognition covers these cases. It recognizes
household members by build and posture, using pictures of the whole
person.</p>""",
    "hilfe.koerper.satz2": """<p>It is built for exactly this case: no usable face, you still want to know
who it was, and you do not want to hand the pictures to an AI vision model
for it.</p>""",
    "hilfe.koerper.satz3": """<p>It learns from material you approve. <b>Register body</b> starts a short
learning run for one person: the system collects pictures of them from your
cameras, you review the result once, and from then on it keeps learning by
itself.</p>""",
    "hilfe.koerper.satz4": """<p>With the switch above you choose whether and when it runs. <b>Only if no
face</b> means it stays quiet unless the face check came up empty.
<b>Always</b> means it checks every pass. Off means it never runs.</p>""",
    "hilfe.vision.titel": "AI vision, explained",
    "hilfe.vision.satz1": """<p>AI vision is a recognition way of its own. It shows the pictures of a
pass to an image model and asks which registered person they resemble. You
can use it as a backup for the hard cases, or let it carry recognition
alone: set to <b>Always</b>, it judges every pass by itself, even if no
faces are taught at all. It judges at the end of a pass, not live.</p>""",
    "hilfe.vision.satz2": """<p>What it needs to work: registered people with approved body pictures
(their galleries), and a connected model. The model can run locally on your
own hardware or in the cloud. With a cloud model, remember that the
pictures leave your house: what is fine with a local model is not
automatically allowed with a cloud one. And do not pick the smallest
models; a mid-sized model does the job fine.</p>""",
    "hilfe.vision.satz3": """<p>What we run ourselves: Qwen 3.5 in the 9B size, and it does the job well,
locally as well as in the cloud. We also tested models from Anthropic
(Claude), Google (Gemini) and OpenAI (GPT). Take this as tested, not as a
recommendation; the model list on the Vision page marks the ones we
measured, right where you choose.</p>""",
    "hilfe.vision.satz4": """<p>And it does not stop at one comparison: to rule out mix-ups, the pass is
checked against the galleries of the other people too, both ways round.
Each compared pair costs two requests, so a single pass can add up. <b>If
needed</b> keeps that bill small: the model only gets asked when faces
leave doubt. Without a connected model, vision simply stays out of the
game, and the card says so.</p>""",
    "hilfe.faces_bekannt.titel": "Known people & registering, explained",
    "hilfe.faces_bekannt.satz1": """<p>Here you see every person your system knows &mdash; tap a face and you see
every picture stored behind it.</p>""",
    "hilfe.faces_bekannt.satz2": """<p>You do not teach a new person with a photo upload: they are learned from
normal camera footage. Over the day the system collects pictures from
different angles, you confirm who it is, and only after that check a picture
is kept.</p>""",
    "hilfe.faces_bekannt.satz3": """<p>That way every person gets a small collection of real everyday pictures
&mdash; exactly what makes recognition strong, even when someone looks away
or wears a cap.</p>""",
    "hilfe.faces_lernen.titel": "Learning, explained",
    "hilfe.faces_lernen.satz1": """<p>While the cameras run, the system keeps collecting new pictures of the
people it already knows. Here you look through what has come together
&mdash; every few days is plenty.</p>""",
    "hilfe.faces_lernen.satz2": """<p>You confirm, correct or dismiss with one click; nothing is kept without
you.</p>""",
    "hilfe.faces_lernen.satz3": """<p>The more good pictures a person has, the more reliably they are
recognized &mdash; so learning never fully stops, it just becomes rarer.</p>""",
    "hilfe.faces_unbekannt.titel": "Unknown visitors, explained",
    "hilfe.faces_unbekannt.satz1": """<p>Some people keep showing up without the system having a name for them
&mdash; the postman, a neighbour, the gardener. Here the system collects
these recurring unknowns and asks you: who is this?</p>""",
    "hilfe.faces_unbekannt.satz2": """<p>Give them a name and from then on they are recognized like everyone
else. Or leave them unknown on purpose &mdash; that is a decision too, and
the system will not keep asking.</p>""",
    "hilfe.faces_qualitaet.titel": "Quality check, explained",
    "hilfe.faces_qualitaet.satz1": """<p>Over time many pictures pile up, and not every one helps recognition
&mdash; some are blurry, some barely show the person, and in the worst case
pictures of two different people look so alike that mix-ups loom.</p>""",
    "hilfe.faces_qualitaet.satz2": """<p>This check finds such weak spots before they cost you a recognition. You
get concrete pointers which pictures to look at &mdash; nothing is deleted
unless you decide it yourself.</p>""",
    "hilfe.faces_lernlauf.titel": "The learning run, explained",
    "hilfe.faces_lernlauf.satz1": """<p>You start a run; the system re-reads your recent recordings and collects
faces on its own.</p>""",
    "hilfe.faces_lernlauf.satz2":
        "<p>It sorts them into groups. One group should be one person.</p>",
    "hilfe.faces_lernlauf.satz3": """<p>You name each group, or skip it. That is the only step that needs
you.</p>""",
    "hilfe.faces_lernlauf.satz4": """<p>Named pictures become references and count for recognition right away.
Repeat every few days, or let the day view top up known people in
between.</p>""",
    # B9: der Rueck-Link ist je Ziel ein GANZER Satz-Schluessel — "Back to
    # {ziel}" ist DAS Anti-Beispiel aus konzept_sprache.md §4.0 (Genus/
    # Praeposition). Kopplung: "Faces" == nav.faces/faces.titel,
    # "Recognition" == nav.erkennung/erkennung.titel, "the learning run"
    # nennt die Lauf-Seite (nav.lernlauf "Learning run") im Satz.
    "hilfe.zurueck.erkennung": "Back to Recognition",
    "hilfe.zurueck.faces": "Back to Faces",
    "hilfe.zurueck.lernlauf": "Back to the learning run",
    # ---- §8.1-Nachzuegler (Stufe 3): Inline-Markup-Prosa der Tranchen ----
    # Die bei den Stufe-2-Tranchen als "Stufe-2-Grenze (§8.1)" markierten
    # Prosa-Bloecke mit <b>/<a>/<code>/<br> mitten im Satz — jetzt als
    # t_html-Schluessel (HTML_SCHLUESSEL in core/sprache.py). Statische
    # hrefs bleiben IM Wert (die identische Tag-Folge je Uebersetzung pinnt
    # sie, tools/texte_pruefen.py); dynamische Einsetzungen laufen als
    # kwargs durch t_html (escapt selbst, quote=True).
    # verifyd.py Wizard-Schritt 3: zitiert die Seite <b>System</b>
    # == system.titel / nav.system / nav.bereich.system.
    "setupwiz.backend.system_satz":
        "Whether the accelerator really engages is confirmed live on the "
        "<b>System</b> page after start (suslik never silently falls back "
        "to CPU without saying so).",
    # verifyd.py Wizard-Fertig-Block: zitiert <b>System → Re-run setup
    # wizard</b> — WORTGLEICH zu system.titel + konfiguration.knopf_setup
    # je Sprache setzen (der Pfeil verbindet die beiden Zitate).
    "setupwiz.fertig.wieder_satz":
        "You can re-run this wizard any time from <b>System → Re-run "
        "setup wizard</b>.",
    # routes/system.py Sync-Karte (Happy-Path + Fallback-Karte).
    "system.sync.diagnose_satz":
        'If a sync reports a problem, <a href="/sync_diagnose" '
        'target="_blank">open the diagnosis</a> — it bundles the suslik '
        "report and the Frigate log, ready to copy into an issue.",
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">open the diagnosis</a> '
        "— bundles the suslik report and the Frigate log.",
    # routes/vision.py Einleitungs-Absatz.
    "vision.kopf.einleitung":
        "A third recognition path next to face and body: a vision language "
        "model looks at one picture from a walk-through and says which of "
        "your learned people it shows &mdash; by comparing it against a "
        "small gallery of that person. It is an <b>extra voice</b>, never "
        "the doorkeeper: the forced choice answers &bdquo;A or B&ldquo;, so "
        "it can confirm a resident but it cannot turn a stranger away. That "
        "stays the job of the existing recognition.",
    # Produktnamen (llama.cpp, Qwen3.5, docker stats) bleiben in jeder
    # Sprache wortgleich (§8.7).
    "vision.hinweis.modell_satz":
        "A vision model that can look at several pictures at once. You can "
        "use one of the online providers below, or run one yourself &mdash; "
        "the combination measured here is <b>llama.cpp</b> with a "
        "<b>Qwen3.5</b> vision model (the 4B is as good as the 9B on this "
        "task and needs about half the memory). It does <b>not</b> have to "
        "run on this machine.",
    "vision.hinweis.host_satz":
        "<b>This host is usually too small for a local model.</b> The 9B "
        "needs roughly 12 GB of working set, the 4B about 6.6 GB, and "
        "suslik plus the analysis worker already live here &mdash; the "
        "worker is the first thing the kernel kills when memory runs out. "
        "A second machine, or an online provider, is the sane setup.",
    "vision.hinweis.mess_satz":
        "A warning about measuring that memory: <code>docker stats</code> "
        "shows about 2.7 GiB for the model container because the weights "
        "are mapped, not copied. The real working set is ~11.6 GiB. If you "
        "size <code>--memory</code> by what <code>docker stats</code> says, "
        "the model reloads its weights continuously and everything crawls.",
    "vision.hinweis.kosten_satz":
        "Speed and cost, measured, so nothing surprises you later: the "
        "whole walk-through goes in as <b>one candidate grid</b>, and each "
        "<b>compared pair of galleries is two requests</b> (the same "
        "question is asked again with the two galleries swapped, to catch "
        "a position bias). Usually one pair settles it. On a CPU-class "
        "machine that is about 7 minutes per pair; on the online endpoints "
        "measured here, seconds.",
    # Schluessel-Ort-Warnung der Verbindungskarte.
    "vision.verb.key_ort":
        "<b>Put the key in the key field, not in the URL</b>: an endpoint "
        "that carries credentials in its address &mdash; in front of the "
        "host name, or as a query parameter &mdash; holds the same secret, "
        "and it shows up in far more places (status, log, backup).",
    # Leerzustand der Modellkarte: B9-konform JE pruef_wort ein GANZER
    # Block (Woerter aus core/vision.pruef_wort: "key"/"connection" —
    # Deckungs-Vertrag mit dieser Zwei-Wert-Funktion). ZITAT: <b>Check the
    # key/connection</b> zitiert den Pruef-Knopf, der selbst noch ein
    # B9-Literal in routes/vision.py:_verbindung ist — sein Schluessel-
    # Umbau muss VOR/mit der Uebersetzungsrunde landen, sonst laufen
    # Zitat und Knopf auseinander.
    "vision.modell.leer_key":
        "Nothing to choose yet. Enter your key above and press <b>Check "
        "the key</b>: suslik connects to the endpoint, asks what is there, "
        "and shows you what it found. You pick from that list.",
    "vision.modell.leer_verbindung":
        "Nothing to choose yet. Fill in the fields above and press "
        "<b>Check the connection</b>: suslik connects to the endpoint, "
        "asks what is there, and shows you what it found. You pick from "
        "that list.",
    # {zeit} = vorformatierte Zeit (_zeit, B19 bleibt Route), {stand} =
    # Messwerte-Stand — beide escapt t_html selbst.
    "vision.modell.antwort_satz":
        "This is what the endpoint answered when suslik asked it, {zeit} "
        "&mdash; nothing here is a suggestion from us. Where we have "
        "measured a model, the note sits on that model. Two abilities are "
        "shown separately, because they fall apart: <b>residents</b> is "
        "picking the right one of two known people, <b>strangers</b> is "
        "answering &bdquo;neither&ldquo; for somebody you never taught it. "
        "A tick means every judgement of that kind in our measurement was "
        "right; the fraction next to it is the whole story. Models without "
        "a measurement here say <b>untested here</b> &mdash; that is not a "
        "verdict, just honesty (measurements from {stand}).",
    # ZITAT: <b>custom prompt</b> == die Urteils-Marke
    # visiontest.vision.custom_prompt (" &middot; custom prompt").
    "vision.prompt.eigen_satz":
        "This is your own wording &mdash; verdicts made with it are marked "
        "<b>custom prompt</b>. Reset it to go back to the measured default.",
    # {ziel} = Endpunkt-Anzeige (escapt t_html); das class-Attribut ist
    # Teil der gepinnten Tag-Folge.
    "vision.cloud.sendet_satz":
        "This sends pictures of people from your cameras to "
        '<b class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Three steps, because a plain reachability ping is not enough: one "
        "backend was reachable, had the model and answered quickly &mdash; "
        "and still got 5 of 12 comparison questions wrong, because it "
        "shrank the pictures before looking at them.<br><b>1</b> "
        "reachability, model and response time, using a test image "
        "generated on the spot.<br><b>2</b> a forced-choice run on "
        "generated shape grids where the right answer is known &mdash; "
        "this checks the answer format, the parser and the thinking "
        "switch.<br><b>3</b> a token count against a measured reference, "
        "which is how image shrinking shows up.<br><b>No picture of a "
        "person is used for this</b>, and there is no option to do so.",
    # routes/visiontest.py.
    "visiontest.kopf.wege_satz":
        "Pick one real walk-through and see what all three recognition "
        "paths make of it, side by side: <b>face</b>, <b>person</b> and "
        "<b>vision</b>.",
    # ZITAT: "Vision detect" == nav.vision.
    "visiontest.vision.einrichten_satz":
        'Set it up under <a href="/vision">Vision detect</a>: a model, a '
        "green connection test and at least two approved galleries. The "
        "other two columns work without it.",
    # routes/visionwizard.py. {empfehlung} escapt t_html selbst.
    "visionwizard.groesse.satz":
        "Measured, honestly: the size was <b>not</b> the lever in any of "
        "the cases we ran &mdash; a bigger grid did not make the answers "
        "better, and it did not make them worse either. Take the larger "
        "one if your material carries it (here: {empfehlung}), the smaller "
        "one if it does not. Both cost about the same, because the canvas "
        "is what costs tokens, not the number of cells.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Forget them</a> '
        "if you want to start over.",
    # ZITAT: <b>does not fit</b> == visionwizard.zelle.knopf_weg.
    "visionwizard.vorschlag.satz":
        "One row per view: front, side, back. Pictures are picked by size "
        "and sharpness, how clearly the eyes and nose are there, how much "
        "light is blown out, how much of the crop is actually the person "
        "&mdash; and spread over different days, events and cameras. The "
        "line under each picture says what was measured on it. Click "
        "<b>does not fit</b> on anything unusable &mdash; the next best "
        "picture of the SAME view moves up. This does not touch your "
        "learning material; it only says &bdquo;not as a gallery "
        "cell&ldquo;.",
    # routes/personwizard.py.
    "personwizard.kopf.stark_satz":
        "<b>What makes the model strong:</b> variety beats volume. Images "
        "from <b>many different days</b> (outfits, light, cameras) help "
        "far more than many images from one walk — run the harvest "
        "again on new days rather than harvesting one day deeper. "
        "Confirmed stranger images sharpen the decision threshold the "
        "same way.",
    # ZITAT: "Model status" == nav.person_modell (+ erkennung.koerper.
    # knopf_status "Model status …").
    "personwizard.fertig.training_satz":
        "Training on the approved material starts automatically after the "
        'review — see <a href="/person/modell">Model status</a>. You '
        "can start another run below any time.",
    # ZITAT-KOPPLUNG: "Configuration" == nav.bereich.configuration,
    # "Advanced" == nav.konfiguration. Der alte Wortlaut "Settings" war
    # GEDRIFTET (Bereich seit .210 "Configuration") — toter Wegweiser,
    # gleiche faktische Klasse wie der "(Settings)"-Fix vom 20.08.,
    # deshalb an der Quelle korrigiert (kein Stil-Eingriff).
    "personwizard.kontrolle.schalter_satz":
        'Switch it under <a href="/konfiguration">Configuration &rarr; '
        "Advanced</a>, key <code>diagnostic_collection</code>. Images and "
        "log expire together with the hit log after 30 days &mdash; "
        "nothing here is kept longer than the recognition record itself.",
    # ZITAT: "Model status" == nav.person_modell.
    "personwizard.kontrolle.leer_satz":
        "Entries appear once body recognition is armed on "
        '<a href="/person/modell">Model status</a> and a person walks '
        "through.",
    # ZITAT: "Person learn" == nav.personlauf.
    "personwizard.bestand.leer_satz":
        'Run <a href="/personlauf">Person learn</a> and finish the review '
        "— approved images appear here.",
    "personwizard.bestand.stark_satz":
        "Variety beats volume: images from <b>many different days</b> "
        "(outfits, light) help far more than many images from one walk. "
        "Aim for several days per person and let the harvest cover all "
        "your cameras.",
    # {n} = Fremd-Bilderzahl (Route liefert die rohe Zahl).
    "personwizard.bestand.fremd_satz":
        "<b>Strangers:</b> {n} confirmed stranger images calibrate the "
        "decision threshold — the more strangers the model has seen, "
        "the more reliable that line is. (Collected in "
        "<code>personlern/fremd/</code>; a page for growing this set from "
        "your own street traffic is planned.)",
    "personwizard.bestand.fremd_erklaerung":
        "Confirmed stranger images — they train the extra class and "
        "calibrate the decision threshold. Deleting one retrains the model "
        "right away (files live in <code>personlern/fremd/</code>).",
    # ZITAT: "Person learn" == nav.personlauf.
    "personwizard.modell.leer_satz":
        'Run <a href="/personlauf">Person learn</a> and finish a review '
        "— training starts automatically afterwards.",
    # ZITAT: "Body images" == nav.person.
    "personwizard.modell.material_satz":
        "Manage the images under "
        '<a href="/person">Body images</a> — deletions retrain the '
        "model automatically.",
    # ---- Meldetexte (Stufe 4) --------------------------------------------
    # Pushover-/Telegram-TEXTE (konzept_sprache.md §4.4 + §6.4). Sie
    # entstehen OHNE Request: die Sprache kommt am Meldeweg aus dem
    # Config-Store (core/melden.sprache_aktivieren, Eintrittspunkte b/c).
    # NUTZUNGS-REIHENFOLGE unten = Reihenfolge im Meldefluss:
    # Titel -> Event-Alert -> Personen-Erkennung -> Vision -> Live-Waechter
    # -> geteilte Bausteine (Video-Rueckfall, Kanal-Test).
    #
    # NICHT eingezogen (bewusst, Stufe-4-Grenzen — Sammelmarker in
    # verifyd.py bei den Kategorie-Tabellen, core/melden.telegram_melden,
    # core/melden.stoerung_melden und core/livewache.TEXT_URTEIL_*):
    # (a) DEUTSCHE Alt-Meldetexte (Szenen-Telegram-Captions "… erkannt um
    #     …"/"Unbekannte Person um …", Anwesenheits-Satz, alle
    #     "suslik-Stoerung"-Pushes der Wartungsjobs) — de->en waere eine
    #     bewusste TEXTAENDERUNG, nie Teil des Einzugs.
    # (b) Stoerungs-DIAGNOSEN, die wortgleich ins Log gehen (Log bleibt
    #     englisch/maschinenlesbar, B20).
    # (c) Das Schnell-Urteil des Waechters (TEXT_URTEIL_*): derselbe String
    #     ist zugleich MQTT-Payload-Wert (Additiv-Invariante: kein
    #     bestehendes Feld aendert seine Bytes) und Log-Zeile.
    # (d) MQTT-Felder/Topics/Werte insgesamt — dort steht die Wortstufe als
    #     KENNUNG (clear|narrow|below|none), nie als Anzeigewort.
    # Produktnamen (suslik/Frigate/Pushover/Telegram) bleiben in JEDER
    # Sprache wortgleich (§8.6).
    #
    # Push-Titel der Kategorie-Alerts: {wort} kommt aus der Kategorie-
    # Anzeige (webui.bausteine.kat_wort, Tranche-D-Quelle).
    "meldung.titel.kategorie": "suslik: {wort}",
    # Event-Alert (verifyd._maybe_alert): je Urteils-Zweig ein GANZER Satz
    # (B9); {wort} = Wortstufe aus core/vertrauen (uebersetzt, §6.4).
    "meldung.alert.bestaetigt":
        "{name} confirmed ({wort}, seen in {n} window(s))",
    "meldung.alert.keiner_naechster":
        "no one confirmed — closest is {name} ({wort})",
    "meldung.alert.keiner_ohne_gesicht": "no one confirmed — no usable faces",
    # {kamera} kommt zusammengesetzt aus der Route (Kamera · Area(s)),
    # {urteil} ist einer der drei Zweige oben, {gesichter} der Plural.
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate saw: {label}. {gesichter}",
    # echter Plural schon im Original (face/faces) — t_n loest .eins/.viele.
    "meldung.alert.gesichter.eins": "{n} face in this event.",
    "meldung.alert.gesichter.viele": "{n} faces in this event.",
    # Rohzahlen-Anhang, nur im Stil alert_stil=worte_zahlen. {score}/{cos}
    # kommen vorformatiert aus dem Dienst (§8.8).
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    # Personen-Erkennung ueber den Koerper (verifyd, personlive-Weg).
    "meldung.person.titel": "suslik person recognition",
    "meldung.person.satz":
        "{name} recognized by body (person recognition, not face) — "
        "{wort}, {n} supporting events",
    # Ersatzwort, wenn die geeichte Latte nicht lesbar war (Original:
    # "{_vt_wort or 'match'}").
    "meldung.person.wort_ersatz": "match",
    "meldung.person.zahl": "[score {score}]",
    # Vision-Meldungen (verifyd._vision_melden). "picture(s)"/
    # "comparison(s)" bleiben EINE Form (§8.18), der Gedankenstrich-Zusatz
    # ist ein eigener Schluessel (§8.11).
    "meldung.vision.titel": "suslik vision",
    "meldung.vision.unbestaetigt":
        "vision could not confirm anyone on this pass",
    "meldung.vision.koerper_zusatz": "— the body ranking said {namen}",
    "meldung.vision.bilder_zusatz": "({n} picture(s) in the grid)",
    "meldung.vision.einig":
        "vision: {name} — unanimous, {voten} of {bilder} comparison(s)",
    "meldung.vision.kein_urteil": "vision: no verdict — {grund}",
    # Live-Waechter (core/livewache). {wache} ist die KENNUNG des Waechters
    # (core.livewache.WATCHER_TITEL, EIN Literal, Invariante §6) — sie
    # bleibt in jeder Sprache wortgleich, uebersetzt wird der Rest.
    "meldung.wache.titel_person": "{wache} {kamera}: person detected",
    "meldung.wache.titel_stoerung": "{wache} {kamera}: disturbance",
    "meldung.wache.caption": "{wache} {kamera}: {text}",
    "meldung.wache.name_satz":
        "recognized (live, preliminary): {name} ({wort}, {n} "
        "consistent looks)",
    "meldung.wache.name_zahl": "[cosine {cos}]",
    # echter Plural schon im Original (face/faces) — t_n; {sek}/{score}/{ms}
    # kommen vorformatiert aus der Engine (§8.8).
    "meldung.wache.funde.eins": "{n} face in {sek} s",
    "meldung.wache.funde.viele": "{n} faces in {sek} s",
    "meldung.wache.funde_zahl": "(score {score}, {ms} ms)",
    # Geteilte Bausteine beider Straenge (core/melden + verifyd).
    "meldung.video_ersatz.satz": "(video unavailable — sending image)",
    "meldung.test.satz": "Test notification from suslik ✓",
    # ---- D1: ehrliche Begruendung der Pass-Pruefung ----------------------
    # Anlass (User 20.08.): der Knopf "Check this pass for good pictures"
    # meldete "nothing to take … (that is fine)", obwohl alle 149 Gesichter
    # des Durchgangs unter der Groessen-Latte lagen — der Code kannte die
    # Zahl und verschwieg sie. Die Saetze unten sind SATZTEILE (kleines
    # Anfangswort): sie haengen entweder hinter "nothing to take — " oder
    # hinter dem Grenzfall-Satz. Die Kennung->Satz-Wahl trifft
    # webui.bausteine.bruecke_grund, die Zahlen liefert
    # anlernen.vorschlaege_person (Schwellen aus core/benennung.REF_LATTE —
    # hier steht KEINE Schwelle als Literal, nur ihr Platzhalter).
    # "face(s)"/"event(s)" bleiben EINE Form (§8.18, wie antwort.adopt_skip).
    "antwort.bruecke_nichts_grund": "nothing to take — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    "antwort.bruecke_grund_zu_klein":
        "all {n} face(s) measured in this pass are below the minimum face "
        "size — largest {kante} px, needs {min_kante} px",
    "antwort.bruecke_grund_zu_unscharf":
        "{n} face(s) in this pass are too blurry for a reference — best "
        "sharpness {sharp}, needs {unscharf_max}",
    "antwort.bruecke_grund_kein_gesicht":
        "no measurable face in the {n} picture(s) checked in this pass",
    "antwort.bruecke_grund_gedeckt":
        "{n} of the checked face(s) are near-identical to references "
        "{person} already has",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} of the checked face(s) look more like someone else than like "
        "{person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} of the checked face(s) were not clearly {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} of the checked face(s) were weak on both counts — picture "
        "quality and identity",
    "antwort.bruecke_grund_kein_crop":
        "none of the {n} event(s) in this pass has a face crop to check",
    "antwort.bruecke_grund_keine_events":
        "no event of this pass has {person} confirmed or as its best match",
    "antwort.bruecke_grund_keine_referenzen":
        "{person} has no reference pictures yet to compare against",
    # ---- personlauf-Design (Nachzug) ----
    # 20.08.: /personlauf traegt jetzt dasselbe Lauf-Design wie der
    # Gesichts-Lernlauf (Vier-Kachel-Fluss, Saeule, Suchknopf mit Popup).
    # Alle bisherigen personwizard.*-Texte bleiben unveraendert in Gebrauch —
    # neu sind nur die Beschriftungen, die es im alten Karten-Layout gar
    # nicht gab (Kachel-Titel und je ein Klartext-Satz je Kachel-Leerzustand).
    # Was wortgleich schon existiert, wird wiederverwendet statt verdoppelt:
    # Kachel 1/4 heissen wie drueben (lernwizard.kachel.lauf/.fertig), die
    # erste Saeulen-Marke ist lernwizard.seg.vorbereiten, dazu
    # lernwizard.k1.gestartet/.k1.scope, .such.klein, .knopf_abbrechen,
    # .knopf_neuer_lauf und erkennung.link_how.
    # ACHTUNG Uebersetzungsrunde: diese sieben Schluessel fehlen noch in
    # de/es/it/fr — das ist die bewusst deklarierte Fehlmenge.
    "personwizard.kachel.sammeln": "Collect images",
    "personwizard.kachel.pruefen": "Review the pictures",
    "personwizard.k1.satz":
        "Choose who to learn and how far back to look &mdash; the run then "
        "collects the pictures from your own recordings.",
    "personwizard.k2.satz":
        "Harvests full-body pictures from your recordings, and only from "
        "walk-throughs a face already confirmed.",
    "personwizard.k3.satz":
        "The step that needs you: every harvested picture gets your yes or "
        "no before anything is learned.",
    "personwizard.k4.satz":
        "Approved pictures train the body model right away &mdash; it can "
        "then recognize people with no face in sight.",
    "personwizard.such.titel": "Set up a person-learn run",
    # --------------------------------------------- routes/systemstat ---
    "systemstat.titel": "System load",
    "systemstat.sub":
        "Total load of this machine. A new sample every {takt} seconds, kept "
        "for {stunden} hours. There is no split per process here: Frigate "
        "runs in its own container, so its share cannot be named from this "
        "side. Anything this hardware cannot measure says so instead of "
        "showing a zero.",
    "systemstat.leer.titel": "No samples yet.",
    "systemstat.leer.hinweis":
        "The first line is written about {takt} seconds after the service "
        "starts. Values that need two measurements (CPU, NPU, GPU) follow "
        "one round later.",
    "systemstat.block.hardware": "Hardware",
    "systemstat.block.erkennung": "Recognition",
    "systemstat.block.live": "Live",
    "systemstat.nicht_verfuegbar": "not available",
    "systemstat.kein_prozent": "no percentage",
    "systemstat.ja": "yes",
    "systemstat.nein": "no",
    "systemstat.verlauf.leer": "no history yet",
    "systemstat.verlauf.aria": "the last hour",
    "systemstat.cpu.anzahl": "Cores",
    "systemstat.cpu.kerne": "per core, right now",
    "systemstat.kachel.platte": "Disk",
    "systemstat.ram.genutzt": "In use",
    "systemstat.ram.grafik": "Graphics (shared RAM)",
    "systemstat.ram.prozesse": "Processes",
    "systemstat.ram.limit": "Limit",
    "systemstat.ram.cache": "Reclaimable cache",
    "systemstat.platte.frei": "Free",
    "systemstat.platte.gesamt": "Total",
    "systemstat.platte.cache": "Clip cache / cap",
    "systemstat.platte.frei_min": "Keep free",
    "systemstat.gpu.engine": "Busiest engine",
    "systemstat.gpu.speicher": "Memory",
    "systemstat.gpu.temperatur": "Temperature",
    "systemstat.gpu_eigen.titel": "GPU (suslik's share)",
    "systemstat.gpu.gesamt": "Whole card",
    "systemstat.gpu_eigen.zeile": "suslik's share",
    "systemstat.kachel.worker": "Analysis worker",
    "systemstat.worker.laeuft": "running",
    "systemstat.worker.ruht": "idle, starts on demand",
    "systemstat.worker.tode": "restarts in 24 h",
    "systemstat.worker.zuletzt": "Last death",
    "systemstat.worker.ursache": "Last cause",
    "systemstat.kachel.durchsatz": "Throughput",
    "systemstat.durchsatz.tag": "Last 24 h",
    "systemstat.durchsatz.dauer": "Average duration",
    "systemstat.kachel.rueckstau": "Backlog",
    "systemstat.rueckstau.laeuft": "Catching up",
    "systemstat.rueckstau.fenster": "Look-back window",
    "systemstat.kachel.live": "Live engine",
    "systemstat.live.waechter": "Watchers active",
    "systemstat.live.supervisor": "Supervisor",
    "systemstat.stand": "Measured at {zeit}. The page refreshes itself.",
    "systemstat.grund.erster_lauf":
        "waiting for the second measurement \u2014 this number is the "
        "difference between two samples",
    "systemstat.grund.kein_geraet": "no such device on this machine",
    "systemstat.grund.kein_zaehler":
        "the device is here, but its driver publishes no utilization counter",
    "systemstat.grund.gesperrt":
        "the counter exists, but this container may not read it (kernel "
        "performance events need extra privileges)",
    "systemstat.grund.werkzeug_fehlt":
        "the query tool for this device is not part of this image",
    "systemstat.grund.nicht_lesbar": "this source could not be read",
    "systemstat.grund.kein_limit":
        "no memory limit is set for this container, so there is no "
        "percentage to show",
    "systemstat.grund.kein_dienst":
        "only the running service knows this number",
}
