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
    "konfiguration.titel": "Advanced settings",
    "konfiguration.kopf.satz1":
        "Changes are audited (config_audit.jsonl); after saving, the "
        "service restarts cleanly (it waits for a running analysis to "
        "finish).",
    "konfiguration.feld.option_an": "on",
    "konfiguration.feld.option_aus": "off",
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
        "dismissed — images removed; the cluster is remembered so "
        "re-harvests of the same events stay quiet",
    "lernanker.detail.dublette_hinweis":
        "duplicate check unavailable (anchor predates embedding "
        "persistence) — physical duplicates are still filtered",
    "lernanker.bekannt.system": "already in your system",
    "lernanker.bekannt.anker": "named on another cluster",
    "lernanker.detail.empfohlen": "Recommended — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Not recommended ({n}) — kept visible, reason on each image",
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
        "{n} dismissed cluster(s) remembered — re-harvests of the same "
        "events stay quiet",
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
        "Dismiss this cluster? Its images are removed; the cluster is "
        "remembered so re-harvests of the same events stay quiet.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Dismiss this cluster? Its images are removed and the pending "
        "naming is discarded; the cluster is remembered so re-harvests "
        "of the same events stay quiet.",
    "lernanker.liste.knopf_verwerfen": "Dismiss",
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
    "live.hoehe.h1440": "1440p — no measured gain over 1080p",
    "live.hoehe.h2160": "2160p — native 4K, marginal gain, highest decode cost",
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
        "Re-measures every reference picture and looks for weak ones, "
        "near-duplicates and mixed-up faces. Takes about a minute and "
        "runs in the background.",
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
    "qualitaet.lauf.reload_auto": "the page refreshes on its own.",
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
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die drei JS-Bloecke
    # _ZW_JS/_SICHT_JS/_WIDGET_JS (\\u-Escapes, warten auf window.T,
    # Stufe 1) samt dem JS-gekoppelten Mehr-Knopf (Show all/Hide the
    # other — das JS setzt textContent zur Laufzeit, HTML-Label und
    # JS-Literal muessen wortgleich bleiben); die sicht_zeile samt
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
    "lernwizard.kachel.benennen": "Name the groups",
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
    "lernwizard.k1.tag": "day {tag}",
    "lernwizard.k2.satz":
        "Runs on its own &mdash; you can close this page and come back.",
    "lernwizard.k2.knopf_abort": "Abort run",
    "lernwizard.k3.satz_warten":
        "The only step that needs you: one group should be one person "
        "&mdash; say who it is, or skip it.",
    "lernwizard.k3.keine_gesichter":
        "No new faces this time &mdash; nothing to name. That is fine: "
        "it just means the recordings held nobody new.",
    "lernwizard.knopf_neuer_lauf": "Start a new run",
    "lernwizard.k3.gruppe_offen":
        "The current group is open below, full width.",
    "lernwizard.k3.alle_erledigt": "All groups are handled.",
    "lernwizard.chip.bilder": "{n} pictures",
    # .295-Sammelzeile — Anker der qs.sh-PYAD-Stufe (Text wohnt jetzt
    # hier, die Route referenziert den Schluessel).
    "lernwizard.k3.verworfen.eins":
        "{n} group dismissed (no usable faces or by you) &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} groups dismissed (no usable faces or by you) &middot;",
    "lernwizard.k3.link_einsehen": "view",
    # B9: je Zweig ein GANZER Satz-Schluessel (statt Punkt-Anhaengsel).
    "lernwizard.k3.done_weiter":
        "{erledigt} of {gesamt} done &mdash; the next one is ready.",
    "lernwizard.k3.done_punkt": "{erledigt} of {gesamt} done.",
    "lernwizard.k3.wartend.eins": "{n} group is waiting for you.",
    "lernwizard.k3.wartend.viele": "{n} groups are waiting for you.",
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
        "Delete this group? Its pictures are removed and a pending "
        "naming is discarded; the group is remembered so re-harvests of "
        "the same events stay quiet.",
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
    "nav.lernlauf": "Learning run",
    "nav.anker": "Anchors",
    "nav.lernen": "Suggestions",
    "nav.person": "Body images",
    "nav.person_kontrolle": "Judged images",
    "nav.person_modell": "Model status",
    "nav.personlauf": "Person learn",
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
    "ui.hinweis.englisch": "This page is not translated yet — its content is still shown in English.",
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
    "js.unb.ziel_fehlt": "Choose a target identity.",
    "js.unb.merge_frage": "Merge?",
    "js.unb.name_fehlt": "Enter a name (new or existing person).",
    "js.unb.benennen_frage": "Assign to \"{person}\"? The best images become references.",
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
    # js.vision.dirty_text: "Save" ist der (noch englische) Knopf der
    # Vision-Seite — bleibt woertlich, bis die Seite selbst einzieht.
    "js.vision.dirty_text": "The test would use the values you just typed. Recognition keeps using the SAVED connection until you press Save — a green test alone changes nothing about the verdicts.",
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
    "js.vision.prompt_zurueck": "default wording restored — press Save to store it",
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
}
