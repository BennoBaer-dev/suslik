# Muttersprachler-QS durchlaufen 19.08.2026 (Opus-Pruefagent je Sprache, Bericht im
# Session-Transkript); aktiv erst mit Registrierung in core/sprache.py (Stufe 1).
"""Deutsche Texte (Uebersetzung von en.py, gleiche Schluessel in gleicher
Reihenfolge; verbindliche Vorlage: begriffe_tabellen.md, DE-Abschnitt)."""
T = {
    # ------------------------------------------------ routes/gesichter ---
    "gesichter.titel": "Bekannte Personen",
    "gesichter.kopf.knopf_lernen": "Personen anlernen",
    "gesichter.kopf.hinweis_lernen":
        "geführter Lernlauf über deine eigenen Aufnahmen "
        "(Fundament-Stufe)",
    "gesichter.kopf.satz":
        "Alle angelernten Personen und ihre Referenzbilder. Du kannst "
        "einzelne Bilder entfernen, über den Knopf je Person weitere "
        "Bilder aus den unbekannten Gesichtern zuordnen oder unten ein "
        "Foto hochladen, auch für eine ganz neue Person.",
    "gesichter.galerie.bildzahl": "{n} Bilder",
    "gesichter.galerie.knopf_entfernen": "entfernen",
    "gesichter.galerie.knopf_aehnliche": "passende Gesichter suchen",
    "gesichter.galerie.knopf_qs": "Qualitätscheck",
    "gesichter.galerie.knopf_loeschen": "Person löschen…",
    "gesichter.galerie.hinweis_leer": "noch keine Bilder",
    "gesichter.upload.titel": "Foto hochladen",
    "gesichter.upload.attr_person": "bestehende Person…",
    "gesichter.upload.attr_neu": "oder neue Person",
    "gesichter.upload.knopf": "Hochladen",
    "gesichter.upload.hinweis":
        "Neue Person: den Namen ins Freitextfeld tippen. Gate: buffalo_l "
        "muss ein Gesicht finden (sonst erscheint eine Rückfrage zum "
        "Erzwingen).",
    "gesichter.import.titel": "Import / Neuabgleich aus Frigate",
    "gesichter.import.knopf": "Gesichter aus Frigate abgleichen",
    "gesichter.import.hinweis":
        "Holt Referenzbilder, die Frigate hat und die hier in den "
        "Referenzen noch fehlen — inkrementell, jederzeit gefahrlos "
        "ausführbar (lokal wird nichts gelöscht). Derselbe "
        "Import wie im Einrichtungsassistenten, jetzt erreichbar, ohne "
        "ihn neu zu durchlaufen (z. B. nach dem Wiederherstellen deiner "
        "Einstellungen).",
    # ------------------------------------------------- routes/kameras ---
    "kameras.titel": "Kameras",
    "kameras.banner.config_fehler":
        "Die Frigate-Config ließ sich nicht lesen: {fehler}",
    "kameras.karte.verwenden": "diese Kamera verwenden",
    "kameras.karte.zonen_hinweis": "nichts angehakt = alle Events",
    "kameras.karte.zonen_keine":
        "keine Zonen in Frigate definiert — alle Events",
    "kameras.karte.rec_an": "Aufnahme ✓",
    "kameras.karte.rec_aus": "keine Aufnahme",
    "kameras.karte.pill_aus": "in Frigate aus",
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate führt auf diesem Stream keine Objekterkennung "
        "für Personen aus &mdash; hier können keine Events "
        "ankommen",
    "kameras.karte.pill_keine_detektion": "keine Objekterkennung in Frigate",
    "kameras.leer.titel": "Keine Kameras in Frigate gefunden.",
    "kameras.leer.hinweis": "Prüfe, ob suslik die Frigate-API erreicht.",
    "kameras.fuss.knopf_speichern": "Kameras speichern",
    # -------------------------------------------------- routes/lernen ---
    "lernen.titel": "Vorschläge — Personen zum Anlernen",
    "lernen.kopf.titel_offen": "Vorschläge ({n})",
    "lernen.leer.titel": "Keine offenen Anlern-Vorschläge.",
    "lernen.leer.hinweis":
        "Gute neue Gesichter (groß, scharf, frontal, sicher erkannt "
        "oder klar fremd) erscheinen hier automatisch nach der Analyse.",
    "lernen.karte.unbekannt": "Unbekannt/Fremd",
    "lernen.karte.metrik_voll":
        "Score {score} · Neuheit {novelty} · {bw}×{bh}px · frontal "
        "{front} · scharf {sharp}",
    "lernen.karte.metrik_kurz": "Score {score}",
    "lernen.karte.link_video": "Video",
    "lernen.karte.knopf_add_person": "Als {person} hinzufügen",
    "lernen.karte.attr_person": "als Person…",
    "lernen.karte.attr_neu": "oder neue Person",
    "lernen.karte.knopf_add": "Hinzufügen",
    "lernen.karte.knopf_ablehnen": "Aussortieren",
    "lernen.galerie.titel": "Referenzen (Master)",
    "lernen.galerie.bildzahl": "{n} Referenzen",
    "lernen.upload.titel_abschnitt": "Hochladen",
    "lernen.upload.titel": "Eigenes Foto in den Master hochladen",
    "lernen.upload.attr_person": "bestehende Person…",
    "lernen.upload.attr_neu": "oder neue Person",
    "lernen.upload.knopf": "Hochladen",
    "lernen.upload.hinweis":
        "Neue Person (z. B. Alex): den Namen ins Freitextfeld tippen. Gate: buffalo_l "
        "muss ein Gesicht finden (sonst erscheint eine Rückfrage "
        "zum Erzwingen). PNG wird in JPEG umgewandelt. Lade mehrere "
        "Fotos aus verschiedenen Blickwinkeln nacheinander hoch.",
    # --------------------------------------------------- routes/areas ---
    "areas.titel": "Bereiche",
    "areas.kopf.sprung": "In eine Sicht springen:",
    "areas.verwaltung.titel": "Bereiche verwalten",
    "areas.verwaltung.camzahl.eins": "{n} Kamera",
    "areas.verwaltung.camzahl.viele": "{n} Kameras",
    "areas.verwaltung.attr_entfernen":
        "diesen Bereich entfernen — seine Kameras wandern zurück "
        "nach Default",
    "areas.verwaltung.attr_neu": "Name des neuen Bereichs",
    "areas.verwaltung.knopf_anlegen": "Bereich anlegen",
    "areas.verwaltung.titel_zuweisen": "Kameras zuweisen",
    "areas.verwaltung.satz_zuweisen":
        "Eine Kamera gehört zu genau einem Bereich; alles nicht "
        "Zugewiesene bleibt in Default. Speichern braucht keinen "
        "Dienst-Neustart.",
    "areas.verwaltung.pill_nicht_gesehen": "nicht gesehen",
    "areas.verwaltung.attr_nicht_gesehen":
        "früher zugewiesen, gerade nicht in Frigate",
    "areas.verwaltung.hinweis_keine_kameras":
        "Noch keine Kameras bekannt — verbinde zuerst Frigate "
        "(Einstellungen).",
    "areas.verwaltung.knopf_speichern": "Bereiche speichern",
    # -------------------------------------- routes/benachrichtigungen ---
    "benachrichtigungen.titel": "Meldungen",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• gespeichert — leer lassen behält den Wert",
    "benachrichtigungen.felder.secret_leer": "nicht gesetzt",
    "benachrichtigungen.felder.option_an": "an",
    "benachrichtigungen.felder.option_aus": "aus",
    "benachrichtigungen.alerts.titel": "Meldeverhalten",
    "benachrichtigungen.alerts.hinweis":
        "Welche Urteils-Kategorien eine Meldung auslösen — auf "
        "jedem Kanal (Pushover, Telegram, MQTT-Szenen-Topics). Den Push "
        "zur erkannten Person steuert der Anwesenheits-Schalter unten; "
        "die MQTT-Daten-Topics (erkennung, heartbeat) senden immer, "
        "solange das MQTT-Publizieren an ist.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik bestätigt eine andere Person als Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate hat jemanden benannt, suslik sah kein brauchbares "
        "Gesicht",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik hat jemanden erkannt, Frigate nicht",
    "benachrichtigungen.kategorien.beide_unknown":
        "keine der beiden Seiten hat ein Gesicht erkannt",
    "benachrichtigungen.kategorien.erkannt":
        "eine bekannte Person wurde erkannt",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "ein brauchbares Gesicht, aber niemand bestätigt "
        "(womöglich fremd)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "ein Gesicht, zu schwach oder zu klein zum Zuordnen",
    "benachrichtigungen.alerts.stil_label": "Textstil der Meldungen:",
    "benachrichtigungen.alerts.stil_worte": "klare Worte",
    "benachrichtigungen.alerts.stil_worte_zahlen": "Worte + rohe Scores",
    "benachrichtigungen.alerts.stil_hinweis":
        "wie Meldungen einen Treffer beschreiben (klare Worte sind der "
        "Standard; rohe Cosinus-/Score-Zahlen nur, wenn du sie "
        "zurückwillst)",
    "benachrichtigungen.alerts.label_anwesenheit_push": "Anwesenheits-Push:",
    "benachrichtigungen.alerts.label_alert_cooldown":
        "Ruhezeit für Meldungen (s):",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Anwesenheits-Ruhezeit (s):",
    "benachrichtigungen.alerts.label_szene_karenz": "Szenen-Karenz (s):",
    "benachrichtigungen.pushover.label_token": "Token:",
    "benachrichtigungen.pushover.label_user": "User-Key:",
    "benachrichtigungen.pushover.knopf_test": "Pushover testen",
    "benachrichtigungen.telegram.label_modus": "Modus:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=abgeschaltet · ha=über Home Assistant · direkt=direkter "
        "Bot · beide=beides",
    "benachrichtigungen.telegram.label_inhalt": "Anhang:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=kurzer Clip, Bild, wenn nicht verfügbar · bild=nur "
        "Bild (kein Transcoding — schont schwache Hardware)",
    "benachrichtigungen.telegram.label_bot_token": "Bot-Token:",
    "benachrichtigungen.telegram.label_chat_id": "Chat-ID:",
    "benachrichtigungen.telegram.label_cooldown": "Unbekannt-Ruhezeit (s):",
    "benachrichtigungen.telegram.knopf_test": "Telegram testen",
    "benachrichtigungen.mqtt.label_publish": "Erkennungs-Topics publizieren:",
    "benachrichtigungen.mqtt.label_host": "Host:",
    "benachrichtigungen.mqtt.label_port": "Port:",
    "benachrichtigungen.mqtt.label_user": "User:",
    "benachrichtigungen.mqtt.label_password": "Passwort:",
    "benachrichtigungen.mqtt.label_topic_praefix": "Topic-Präfix:",
    "benachrichtigungen.mqtt.knopf_test": "MQTT testen",
    "benachrichtigungen.fuss.knopf_speichern": "Speichern + neu starten",
    # ----------------------------------------------- routes/aehnliche ---
    "aehnliche.kopf.titel": "Passende Gesichter für {person}",
    "aehnliche.kopf.satz":
        "Zwei Quellen: unbekannte Gesichter, die {person} ähneln, "
        "und neue Gesichter aus Events, in denen {person} bereits sicher "
        "erkannt wurde. Anhaken und übernehmen.",
    "aehnliche.kopf.link_zurueck": "zurück",
    "aehnliche.unbekannt.titel": "Aus unbekannten Gesichtern",
    "aehnliche.unbekannt.suche_titel":
        "Suche läuft — die Referenzen werden neu eingelesen.",
    "aehnliche.unbekannt.suche_hinweis":
        "Die Seite aktualisiert sich von selbst.",
    "aehnliche.unbekannt.hinweis_leer":
        "Keine ähnlichen unbekannten Gesichter vorhanden.",
    "aehnliche.unbekannt.aehnlichkeit": "Ähnlichkeit {sim}",
    "aehnliche.unbekannt.knopf_hinzu":
        "Ausgewählte zu {person} hinzufügen",
    "aehnliche.vorschlaege.titel":
        "Neue Gesichter aus erkannten Events (7 Tage)",
    "aehnliche.vorschlaege.suche_titel":
        "Suche läuft — erkannte Events werden durchsucht.",
    "aehnliche.vorschlaege.suche_hinweis":
        "Die Seite aktualisiert sich von selbst; Ergebnis in ein bis "
        "zwei Minuten.",
    "aehnliche.vorschlaege.kachel_zeile":
        "{wann} · {kamera} · Ähnl. {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Empfohlen",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutral — vor dem Übernehmen das Bild ansehen",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Klar diese Person, aber entweder liegt der Treffer unter der "
        "Konfidenzschwelle oder der Ausschnitt ist kleiner / weniger "
        "scharf — ein Blick entscheidet.",
    "aehnliche.vorschlaege.knopf_alle":
        "Alle Empfohlenen übernehmen ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt":
        "Ausgewählte für {person} übernehmen",
    "aehnliche.vorschlaege.knopf_neu": "erneut suchen",
    "aehnliche.vorschlaege.fuss":
        "Stand {stand} · empfohlen = sicher {person} + "
        "Referenzqualität",
    "aehnliche.vorschlaege.hinweis_leer":
        "Nichts Passendes in den erkannten Events gefunden.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Kriterien: eindeutig diese Person, neu gegenüber den "
        "Referenzen, ausreichend groß und scharf.",
    "aehnliche.vorrat.titel": "Neues aus dem Lernvorrat",
    "aehnliche.vorrat.hinweis":
        "Hochwertige Gesichter aus dem Lernlauf, bewertet mit dem "
        "referenzfreien Qualitätsmaß und dem Szenario-Konsens. Sie bleiben "
        "lokal und werden nie zu Frigate exportiert.",
    "aehnliche.vorrat.kachel_zeile": "{wann} · {kamera} · Treffer {sim} · Qualität {norm}",
    "aehnliche.vorrat.auch_anker": "auch in einer Gesichtsgruppe",
    "aehnliche.vorrat.knopf_gewaehlt": "Ausgewählte zu {person} übernehmen",
    # ------------------------------------------------- routes/frigate ---
    "frigate.verbindung.titel": "Verbindung",
    "frigate.verbindung.satz":
        "Mein Programm liest Events und Snapshots über die HTTP-API "
        "aus deinem Frigate — auf der Frigate-Seite wird nichts "
        "installiert.",
    "frigate.verbindung.knopf_aendern": "Verbindung ändern",
    "frigate.verbindung.knopf_speichern": "Speichern &amp; neu starten",
    "frigate.verbindung.knopf_abbrechen": "Abbrechen",
    "frigate.verbindung.hinweis_speichern":
        "Speichern startet den Dienst kurz neu; diese Kachel zeigt "
        "danach live, ob die neue Adresse antwortet",
    "frigate.kameras.titel": "Kameras",
    "frigate.kameras.satz":
        "Welche Kameras deines Frigate dieses Programm beobachtet und "
        "welche Zonen zählen. Alles andere wird ignoriert.",
    "frigate.kameras.beweis_keine_auswahl":
        "noch keine Kameraauswahl gespeichert — jede Kamera, die "
        "Frigate anbietet, wird verwendet",
    "frigate.kameras.knopf": "Kameras verwalten",
    "frigate.sync.titel": "Abgleich",
    "frigate.sync.satz":
        "Hält die Gesichter auf beiden Seiten im Gleichschritt: "
        "durchgesehene Gesichter an Frigate senden, importieren, was nur "
        "Frigate hat &mdash; immer deine Entscheidung, nie automatisch.",
    "frigate.sync.knopf": "Durchsehen &amp; abgleichen",
    "frigate.fr.titel": "Frigates eigene Gesichtserkennung",
    "frigate.fr.satz":
        "Auch Frigate kann Gesichter erkennen. Dieses Programm arbeitet "
        "mit oder ohne sie &mdash; der Schalter liegt in Frigates Config "
        "und wird hier live gelesen, damit du weißt, was ein "
        "Abgleich gerade kann.",
    "frigate.fr.beweis_unbekannt": "Zustand unbekannt — {detail}",
    "frigate.js.url_fehlt": "Frigate-URL eingeben",
    "frigate.js.fehler": "Fehler:",
    # ------------------------------------------- routes/ereignisliste ---
    "ereignisliste.offen.titel": "Offene Fälle zum Benennen ({n})",
    "ereignisliste.offen.satz":
        "Füllt sich automatisch: alle Events mit Gesichtern, die "
        "niemand bestätigt hat und die du noch nicht benannt hast. "
        "Events ohne erkannte Person in der Nähe kommen zuerst — "
        "die lohnen den Blick. Nach dem Benennen verblasst die Karte "
        "und verschwindet beim nächsten Laden.",
    "ereignisliste.offen.frigate_mit": "Frigate: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate: —",
    "ereignisliste.offen.zeile_faces": "{n} Gesichter · bestes: {beste}",
    "ereignisliste.offen.link_video": "Video",
    "ereignisliste.offen.kontext_erkannt":
        "im selben Zeitfenster erkannt: {wer}",
    "ereignisliste.offen.kontext_fehlt":
        "keine bestätigte Erkennung in der Nähe",
    "ereignisliste.blaettern.neuer": "← neuere",
    "ereignisliste.blaettern.aelter": "ältere →",
    "ereignisliste.offen.blaettern_stand":
        "Seite {seite}/{max} ({n} offen)",
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} Event mit schwachem Gesicht ausgeblendet — vermutlich kein "
        "brauchbares Gesicht (in der Nähe auch nichts "
        "bestätigt).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} Events mit schwachen Gesichtern ausgeblendet — vermutlich "
        "kein brauchbares Gesicht (in der Nähe auch nichts "
        "bestätigt).",
    "ereignisliste.offen.schwach_zeigen": "anzeigen",
    "ereignisliste.offen.schwach_alle":
        "Events mit schwachen Gesichtern werden mit angezeigt —",
    "ereignisliste.offen.schwach_zurueck": "zurück zu den lohnenden",
    "ereignisliste.offen.leer_titel": "Nichts offen — alles benannt.",
    "ereignisliste.offen.leer_hinweis":
        "Neue unbestätigte Events mit Gesichtern erscheinen hier "
        "automatisch.",
    "ereignisliste.titel": "Events",
    "ereignisliste.filter.alle_areas": "alle Bereiche",
    "ereignisliste.filter.alle_kameras": "alle Kameras",
    "ereignisliste.filter.alle_personen": "alle Personen",
    "ereignisliste.filter.alle_kategorien": "alle Kategorien",
    "ereignisliste.filter.knopf": "Filtern",
    "ereignisliste.filter.reset": "zurücksetzen",
    "ereignisliste.tabelle.blaettern_stand":
        "Seite {seite}/{max} ({n} Events)",
    "ereignisliste.tabelle.kopf_zeit": "Zeit",
    "ereignisliste.tabelle.kopf_kamera": "Kamera",
    "ereignisliste.tabelle.kopf_kategorie": "Kategorie",
    "ereignisliste.tabelle.kopf_crop": "Ausschnitt",
    "ereignisliste.tabelle.kopf_gt": "Bestätigen oder korrigieren (GT)",
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "Log",
    "ereignisliste.tabelle.link_video": "Video",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "Clip unvollständig — aus dem lesbaren Teil beurteilt",
    "ereignisliste.tabelle.attr_kein_crop":
        "für dieses Event wurde kein brauchbares Gesicht behalten",
    # ------------------------------------------- routes/konfiguration ---
    "konfiguration.kette.gesicht_titel": "Gesicht",
    "konfiguration.kette.gesicht_kosten":
        "Basisanalyse auf dem aufgenommenen Clip — immer an",
    "konfiguration.kette.gesicht_zeitpunkt": "je Event",
    "konfiguration.kette.person_titel": "Person (Körper)",
    "konfiguration.kette.person_kosten":
        "der teuerste lokale Schritt (Körper-Embedding auf deiner "
        "Hardware)",
    "konfiguration.kette.person_zeitpunkt":
        "je Event, entschieden am Urteil über den Durchgang",
    "konfiguration.kette.vision_titel": "Vision",
    "konfiguration.kette.vision_kosten":
        "eine Anfrage je Durchgang an deinen eingerichteten "
        "Vision-Endpunkt",
    "konfiguration.kette.vision_zeitpunkt": "am Ende des Durchgangs",
    "konfiguration.kette.immer_an": "immer",
    "konfiguration.kette.immer_hinweis": "(heute nicht abschaltbar)",
    "konfiguration.kette.gesicht_erkl":
        "der Gesichtspfad ist das Rückgrat jeder Analyse — Person "
        "und Vision hängen an seinem Durchgangsurteil",
    "konfiguration.kette.grund_person":
        "noch kein trainiertes Personenmodell scharfgeschaltet",
    "konfiguration.kette.grund_vision":
        "die Vision-Erkennung ist abgeschaltet",
    "konfiguration.kette.grund_aus": "hier abgeschaltet",
    "konfiguration.kette.status_aus": "Status: läuft nicht ({grund})",
    "konfiguration.kette.zeile_kosten": "Kosten: {kosten}",
    "konfiguration.kette.titel": "Erkennungskette",
    "konfiguration.kette.satz":
        "Welche Erkenner laufen, und in welcher Reihenfolge. Die "
        "Bedingung \"nur_wenn_gesicht_leer\" heißt: Der Schritt "
        "läuft nur, wenn der Gesichtspfad NICHT alle im Durchgang "
        "bestätigen konnte — entschieden über den ganzen "
        "Durchgang, nie über ein einzelnes Event. Die Reihenfolge "
        "selbst zu ändern ist eine spätere Ausbaustufe; heute "
        "beginnt die Kette immer mit dem Gesichtspfad.",
    "konfiguration.knopf_speichern": "Speichern + neu starten",
    "konfiguration.kette_blatt.hinweis":
        "Änderungen werden protokolliert (config_audit.jsonl); "
        "nach dem Speichern startet der Dienst sauber neu.",
    "konfiguration.titel": "Erweiterte Einstellungen",
    "konfiguration.kopf.satz1":
        "Änderungen werden protokolliert (config_audit.jsonl); "
        "nach dem Speichern startet der Dienst sauber neu (er wartet, "
        "bis eine laufende Analyse fertig ist).",
    "konfiguration.feld.option_an": "an",
    "konfiguration.feld.option_aus": "aus",
    "konfiguration.frigate_auth.titel": "Frigate-Anmeldung (optional)",
    "konfiguration.frigate_auth.satz":
        "Nur n\u00f6tig, wenn Ihre Frigate eine Anmeldung verlangt \u2014 das ist am "
        "authentifizierten Port (8971) so, am internen (5000) nicht. Bleiben beide "
        "Felder leer, \u00e4ndert sich nichts: suslik spricht mit Frigate genau wie "
        "bisher.",
    "konfiguration.frigate_auth.erkl_user":
        "Benutzername eines Frigate-Kontos. Leer = keine Anmeldung; wird er "
        "geleert, verf\u00e4llt auch das gespeicherte Passwort",
    "konfiguration.frigate_auth.erkl_password":
        "Passwort zu diesem Konto. Es liegt bei den \u00fcbrigen Einstellungen unter "
        "/data und wird nie wieder angezeigt \u2014 leer lassen beh\u00e4lt es",
    "konfiguration.frigate_auth.erkl_tls":
        "TLS-Zertifikat von Frigate pr\u00fcfen. Frigates authentifizierter Port bringt "
        "ab Werk ein selbstsigniertes Zertifikat mit; schalten Sie das hier aus, wenn "
        "Sie ihn per https ansprechen und das Zertifikat nicht ersetzt haben",
    "konfiguration.frigate_auth.pw_gesetzt": "gespeichert \u2014 leer lassen beh\u00e4lt es",
    "konfiguration.frigate_auth.pw_leer": "kein Passwort gespeichert",
    "konfiguration.abschnitt_alle": "Alle Parameter",
    "konfiguration.tabelle.kopf_parameter": "Parameter",
    "konfiguration.tabelle.kopf_wert": "Wert",
    "konfiguration.tabelle.kopf_bedeutung": "Bedeutung",
    "konfiguration.knopf_setup": "Einrichtungsassistent erneut ausführen",
    "konfiguration.abschnitt_readonly": "Nur lesbar (Konsole/yaml)",
    # ----------------------------------------------- routes/lernanker ---
    "lernanker.eimer.ok": "sauber",
    "lernanker.eimer.unbestaetigt": "unbestätigt",
    "lernanker.eimer.zu_duenn": "dünn",
    "lernanker.eimer.hart": "gemischt",
    "lernanker.bin.frontal": "Frontal",
    "lernanker.bin.links": "Blick nach links",
    "lernanker.bin.rechts": "Blick nach rechts",
    "lernanker.kachel.attr_clip":
        "{kamera} · det {det} · Klick öffnet den Clip",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "Clip öffnen",
    "lernanker.kachel.grund_fehlt": "nicht bewertet",
    "lernanker.detail.gruppe": "Gruppe {pos} von {gesamt}",
    "lernanker.detail.frage": "Wer ist das?",
    "lernanker.badge.stuetz": "{n} Gesichter ({phys} physisch)",
    "lernanker.badge.faces": "{n} Gesichter",
    "lernanker.badge.durchgaenge": "{n} Durchgänge",
    "lernanker.badge.tage": "{n} Tag(e): {spanne}",
    "lernanker.badge.marge": "Marge {marge}",
    "lernanker.link_zurueck": "zurück zu allen Gruppen",
    "lernanker.detail.hinweis_klick":
        "klicke ein Gesicht, um seinen Clip zu öffnen",
    "lernanker.detail.hinweis_auswahl":
        "klicke ein Bild, um es aus- oder abzuwählen",
    "lernanker.detail.hinweis_pfeil":
        "das kleine &#9654; öffnet den Clip",
    "lernanker.detail.weiter": "Nächste Gruppe &#8230;",
    "lernanker.detail.pflege_hinweis":
        "die Referenzpflege liegt auf der Seite Qualität",
    "lernanker.detail.verworfen":
        "von dir gelöscht — die Bilder sind weg; die Gruppe bleibt nur als Eintrag stehen",
    "lernanker.detail.dublette_hinweis":
        "Dublettenprüfung nicht verfügbar (der Anker ist "
        "älter als die Embedding-Persistenz) — physische Dubletten "
        "werden trotzdem gefiltert",
    "lernanker.bekannt.system": "schon in deinem System",
    "lernanker.bekannt.anker": "in einer anderen Gruppe benannt",
    "lernanker.detail.empfohlen": "Empfohlen — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Nicht empfohlen ({n}) — bleibt sichtbar, Grund an jedem Bild",
    "lernanker.detail.skip_weiter": "Diese Gruppe überspringen",
    "lernanker.detail.skip_zurueck": "Überspringen — zurück zu den "
        "Gruppen",
    "lernanker.detail.knopf_ja": "Ja, das ist {name}",
    "lernanker.detail.knopf_andere": "Jemand anderes &#8230;",
    "lernanker.detail.knopf_benennen_easy": "Diese Gruppe benennen &#8230;",
    "lernanker.detail.knopf_alle": "Alle Empfohlenen auswählen",
    "lernanker.detail.knopf_keine": "Alle abwählen",
    "lernanker.detail.attr_name": "Personenname (neu oder bestehend)",
    "lernanker.detail.knopf_benennen": "Diese Gruppe benennen",
    "lernanker.detail.knopf_adopt": "In die Erkennung übernehmen",
    "lernanker.js.fehler": "Fehler:",
    "lernanker.js.nicht_uebernommen": "nicht übernommen",
    "lernanker.js.nicht_gespeichert": "nicht gespeichert",
    "lernanker.liste.frage_lauf":
        "Lauf {lid} mit allen Daten löschen? Das entfernt seine {n} "
        "Gruppe(n) endgültig — auch benannte und aussortierte — "
        "und alle gesammelten Bilder. Bereits in die Erkennung "
        "übernommene Referenzen bleiben. Das lässt sich nicht "
        "rückgängig machen.",
    "lernanker.liste.frage_alle":
        "ALLE {alt} alten Läufe mit ihren {n} Gruppe(n) und allen "
        "gesammelten Bildern löschen? Nur der neueste Lauf "
        "{neuester} bleibt. Bereits in die Erkennung übernommene "
        "Referenzen bleiben. Das lässt sich nicht rückgängig "
        "machen.",
    "lernanker.liste.knopf_alte":
        "Alle alten Läufe löschen ({neuester} bleibt)",
    "lernanker.liste.lauf_zeile":
        "Einen Lauf löschen — entfernt alle seine Gruppen und "
        "gesammelten Bilder endgültig (bereits übernommene "
        "Referenzen bleiben):",
    "lernanker.liste.verworfen":
        "{n} Gruppe(n) von dir gelöscht (Bilder weg, nur noch als Eintrag)",
    "lernanker.titel": "Ankergruppen",
    "lernanker.liste.leer":
        "Noch keine Anker — ein Lernlauf baut sie auf (Vorbereitung "
        "→ Sammeln → Gruppierung).",
    "lernanker.liste.leer_link": "Lernlauf-Seite öffnen",
    "lernanker.liste.kopf":
        "{n} Gruppen aus {ges} ankertauglichen Gesichtern — {ok} "
        "sauber, {rest} zur Durchsicht (abgedunkelt, der Grund steht "
        "dran). Öffne eine Gruppe, um sie durchzusehen und zu "
        "benennen — benannte Gruppen werden direkt dort in die "
        "Erkennung übernommen (Knopf Übernehmen).",
    "lernanker.liste.kopf_link": "Zurück zum Lernlauf",
    "lernanker.liste.mehr": "+{n} weitere Gesichter",
    "lernanker.liste.dublette":
        "dieselbe Gruppe wie {anker} — von einem neueren Lauf erneut "
        "gesammelt; benenne sie dort",
    "lernanker.liste.knopf_review": "Benennung durchsehen",
    "lernanker.liste.knopf_view": "Gruppe ansehen",
    "lernanker.liste.knopf_benennen": "Diese {n} Gesichter benennen",
    "lernanker.liste.frage_verwerfen":
        "Diese Gruppe löschen? Ihre Bilder werden entfernt. Das lässt sich nicht rückgängig machen.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Diese Gruppe löschen? Ihre Bilder werden entfernt, die ausstehende Benennung entfällt. Das lässt sich nicht rückgängig machen.",
    "lernanker.liste.knopf_verwerfen": "Löschen",
    # ---------------------------------------------- routes/syncauswahl ---
    "syncauswahl.titel": "Durchsehen &amp; abgleichen — Referenzen "
        "nach Frigate",
    "syncauswahl.kopf.satz":
        "Frigate schickt jede hochgeladene Referenz durch seinen "
        "eigenen Gesichtsdetektor und weist Bilder ab, in denen es kein "
        "Gesicht findet. Diese Seite prüft zuerst dasselbe, zeigt "
        "dir jeden Kandidaten und sendet nur, was du anhakst.",
    "syncauswahl.fehler.titel": "Kandidaten nicht verfügbar",
    "syncauswahl.fehler.satz":
        "Die Kandidatenliste braucht ein erreichbares Frigate — "
        "seine Gesichter sind die eine Hälfte des Vergleichs.",
    "syncauswahl.link_diagnose_auf": "Diagnose öffnen",
    "syncauswahl.link_diagnose": "Diagnose",
    "syncauswahl.link_system": "zurück zu System",
    "syncauswahl.kachel.frigate_abgelehnt":
        "Frigate hat abgewiesen: {fehler}",
    "syncauswahl.kachel.pruefe": "prüfe …",
    "syncauswahl.kachel.vorpruefung_ok": "Vorprüfung ok",
    "syncauswahl.kachel.wohl_abgelehnt":
        "würde wohl abgewiesen: {grund}",
    "syncauswahl.kachel.kein_gesicht": "kein Gesicht erkennbar",
    "syncauswahl.kachel.kein_grund": "kein Grund angegeben",
    "syncauswahl.kachel.senden": "senden",
    "syncauswahl.kachel.knopf_skip": "überspringen",
    "syncauswahl.kachel.attr_skip":
        "Dieses Bild nie senden — wird gemerkt, auch der "
        "automatische Abgleich überspringt es",
    "syncauswahl.kachel.knopf_restore": "zurückholen",
    "syncauswahl.kachel.attr_restore":
        "Dieses Bild zurück auf die Kandidatenliste setzen",
    "syncauswahl.geloescht.satz_import":
        "kam aus Frigate und ist dort jetzt weg",
    "syncauswahl.geloescht.satz_export":
        "wurde unter genau diesem Namen gesendet und ist dort jetzt weg",
    "syncauswahl.geloescht.badge": "in Frigate gelöscht",
    "syncauswahl.knopf_anbieten": "wieder anbieten",
    "syncauswahl.geloescht.attr_anbieten":
        "Zurück auf die Kandidatenliste — der nächste Abgleich "
        "(manuell oder automatisch) sendet es wieder",
    "syncauswahl.geloescht.knopf_respekt": "Löschung respektieren",
    "syncauswahl.geloescht.attr_respekt":
        "Merken, dass dieses Bild aus Frigate herausbleiben soll",
    "syncauswahl.api.badge": "{person} — früher gesendet",
    "syncauswahl.api.attr_anbieten":
        "Zurück auf die Kandidatenliste (sendet eine zweite Kopie, "
        "falls Frigate die erste noch hat)",
    "syncauswahl.fr.titel_unbekannt": "Frigate-Gesichtserkennung: unbekannt",
    "syncauswahl.fr.satz_unbekannt":
        "suslik konnte es gerade nicht aus Frigate lesen — {detail}. "
        "Senden kann trotzdem klappen; das letzte Wort hat ohnehin "
        "Frigate.",
    "syncauswahl.fr.titel_an": "Frigate-Gesichtserkennung: an",
    "syncauswahl.fr.satz_an":
        "(beim Laden dieser Seite aus Frigate gelesen) — sie nimmt "
        "hochgeladene Referenzen an.",
    "syncauswahl.fr.titel_aus": "Frigate-Gesichtserkennung: aus",
    "syncauswahl.bilanz.titel": "Bilanz",
    "syncauswahl.bilanz.hauptzeile":
        "Referenzbilder · {beide} schon in Frigate · {bereit} bereit "
        "zur Übertragung",
    "syncauswahl.bilanz.abgelehnt": "{n} von Frigate abgewiesen",
    "syncauswahl.bilanz.geloescht": "{n} in Frigate gelöscht",
    "syncauswahl.bilanz.exportiert":
        "{n} früher gesendet (Frigate hat sie umbenannt)",
    "syncauswahl.bilanz.abgewaehlt": "{n} abgewählt",
    "syncauswahl.bilanz.vorrat": "{n} Vorrats-Referenz(en) nur lokal (Embedding-basiert, nicht übertragbar)",
    "syncauswahl.bilanz.nur_frigate": "{n} nur in Frigate",
    "syncauswahl.bilanz.je_person": "In Frigate, je Person:",
    "syncauswahl.bilanz.kandidaten.eins": "{n} Kandidat",
    "syncauswahl.bilanz.kandidaten.viele": "{n} Kandidaten",
    "syncauswahl.bilanz.vorpruefung": "{n} mit bestandener Vorprüfung",
    "syncauswahl.bilanz.gewaehlt_wort": "ausgewählt",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "Frigate würde {n} wohl abweisen (nicht angehakt, du kannst "
        "sie trotzdem senden).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "Frigate hat {n} früher abgewiesen (nicht angehakt; Anhaken "
        "versucht es erneut).",
    "syncauswahl.pruef.fehler":
        "Die Vorprüfung konnte nicht laufen: {fehler} — Bilder "
        "ohne Urteil bleiben ausgewählt.",
    "syncauswahl.pruef.laeuft.eins":
        "prüfe {n} Bild … {fertig}/{gesamt} (diese Seite lädt "
        "neu, wenn es fertig ist)",
    "syncauswahl.pruef.laeuft.viele":
        "prüfe {n} Bilder … {fertig}/{gesamt} (diese Seite lädt "
        "neu, wenn es fertig ist)",
    "syncauswahl.sperre.titel": "Nur-Lesen-Modus ist an",
    "syncauswahl.sperre.satz":
        "suslik schreibt gerade nicht nach Frigate.",
    "syncauswahl.knopf_alle": "Alle auswählen",
    "syncauswahl.knopf_keine": "Alle abwählen",
    "syncauswahl.knopf_transfer": "{n} Ausgewählte nach Frigate "
        "übertragen",
    "syncauswahl.leer.titel": "Nichts zu senden",
    "syncauswahl.leer.satz":
        "Jede Referenz hat Frigate entweder schon erreicht oder ist "
        "abgewählt.",
    "syncauswahl.leer.zusatz":
        "Die Abschnitte darunter listen, was sich nicht einfach "
        "übertragen lässt.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} wohl abgewiesen",
    "syncauswahl.gruppe.prueft": "{n} noch in Prüfung",
    "syncauswahl.geloescht.zusatz": "— deine Entscheidung",
    "syncauswahl.geloescht.satz":
        "Diese sind noch in deinen Referenzen, aber Frigate hat sie "
        "unter dem gespeicherten Namen nicht mehr. suslik sendet sie "
        "nie ohne deine Entscheidung erneut: Ein Gesicht in Frigate zu "
        "löschen kann Absicht sein. Wieder anbieten macht es zum "
        "normalen Kandidaten — ab dann lädt es der nächste "
        "Abgleich hoch, auch der automatische. Löschung respektieren "
        "hält es dauerhaft draußen.",
    "syncauswahl.aufklapp": "— anzeigen",
    "syncauswahl.api.titel":
        "{n} früher exportiert — Frigate führt sie unter "
        "eigenen Namen",
    "syncauswahl.api.satz":
        "Diese wurden über Frigates API hochgeladen, und Frigate benennt "
        "jede angenommene Referenz um. suslik kann deshalb am Namen "
        "nicht erkennen, ob sie noch da sind — keine Zahl auf dieser "
        "Seite kann das beweisen. Nichts wird automatisch erneut "
        "gesendet; wenn du weißt, dass eines fehlt, biete es wieder "
        "an (das sendet eine zweite Kopie, falls die erste noch da ist).",
    "syncauswahl.api.vergleich":
        "{person}: {n} so gesendet · Frigate hält aktuell {bestand} "
        "Bilder",
    "syncauswahl.import.zeile.eins": "{n} Bild:",
    "syncauswahl.import.zeile.viele": "{n} Bilder:",
    "syncauswahl.import.mehr": "… und {n} weitere",
    "syncauswahl.import.satz":
        "Diese Referenzbilder hat Frigate, suslik nicht. Der Import "
        "kopiert sie in deine Referenzen; in Frigate ändert sich "
        "nichts.",
    "syncauswahl.import.warnung":
        "Diese Liste kann von dir Hochgeladenes enthalten: Frigate "
        "benennt jede angenommene Referenz um, deshalb kann suslik sie "
        "nicht von Gesichtern unterscheiden, die du direkt in Frigate "
        "hinzugefügt hast. Sie zurückzuimportieren würde "
        "Inhalte doppeln.",
    "syncauswahl.import.knopf": "In suslik importieren",
    "syncauswahl.raus.satz":
        "Mit Absicht gemerkt: Diese bleiben in deinen Referenzen, "
        "werden aber nie nach Frigate gesendet, auch nicht vom "
        "automatischen Abgleich. Zurückholen setzt eines wieder auf "
        "die Kandidatenliste.",
    "syncauswahl.alter.unbekannt": "Alter unbekannt",
    "syncauswahl.alter.sekunden": "vor {s} s",
    "syncauswahl.alter.minuten": "vor {m} min",
    "syncauswahl.alter.stunden": "vor {h} h {m} min",
    "syncauswahl.ergebnis.titel": "Letzte Übertragung",
    "syncauswahl.ergebnis.stopp": "gestoppt:",
    "syncauswahl.ergebnis.wand":
        "dreimal in Folge derselbe Fehler: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "hochgeladen — {bild}",
    "syncauswahl.ergebnis.zaehler":
        "{hoch} hochgeladen · {weg} nicht angenommen",
    "syncauswahl.ergebnis.auswahl": "von {n} ausgewählten",
    "syncauswahl.ergebnis.uebersprungen": "{n} abgewählt (übersprungen)",
    "syncauswahl.ergebnis.dauer": "dauerte {n} s",
    # ---------------------------------------------------- routes/live ---
    "live.hinweis_gpu":
        "Läuft vorerst nur mit GPU — wir arbeiten an einer "
        "CPU-Variante, versprechen können wir sie nicht.",
    "live.hinweis_cpu":
        "CPU-Modus: Wächter sind hier teuer — die schnelle "
        "Prüfung dauert typisch 1–2 s (ein GPU-Build reagiert in "
        "unter einer Sekunde), und zusätzliche Wächter bremsen "
        "sich gegenseitig. Wie viele du laufen lässt, entscheidest "
        "du; wir empfehlen den Start mit einem.",
    "live.zeile.alter": "({tage} Tag(e) alt)",
    "live.test.zeile":
        "Quellentest {wann}: {aufloesung} → {skala}, {bilder_s} "
        "Bilder/s",
    "live.test.durchsatz":
        "(Durchsatz, nicht Lieferrate — Quellentest erneut "
        "ausführen)",
    "live.test.provider": "Provider {provider}",
    "live.test.sw": "(Software-Decode)",
    "live.test.entwertet":
        "— ENTWERTET: Quelle seit diesem Test geändert",
    "live.test.fehlgeschlagen":
        "letzter Quellentest FEHLGESCHLAGEN ({wann}): {fehler}",
    "live.messung.zeile": "Last gemessen am {wann}: {text}",
    "live.messung.veraltet":
        "— VERALTET: Quelle seit dieser Messung geändert, neu "
        "messen",
    "live.messung.fehlgeschlagen":
        "letzte Lastmessung FEHLGESCHLAGEN ({wann}): {fehler}",
    "live.zaehler.auftritte": "{n} Auftritte",
    "live.zaehler.trigger": "{n} Trigger",
    "live.zaehler.alerts": "{n} Meldungen",
    "live.zaehler.letzter": "letzter Trigger {zeit}",
    "live.zaehler.kopf": "seit Engine-Start:",
    "live.engine.titel_aus": "Live-Engine: läuft nicht",
    "live.engine.satz_aus":
        "Kein Heartbeat vom Engine-Prozess. Die Kacheln zeigen die "
        "gespeicherten Einstellungen; Einschalten, Tests gegen einen "
        "laufenden Wächter und Lastmessungen brauchen die Engine — "
        "der Dienst startet sie automatisch, sobald mindestens ein "
        "Wächter eingeschaltet ist.",
    "live.engine.cpu_mit_limit":
        "suslik-CPU gerade: {kerne} von {limit} erlaubten Kernen "
        "(ganzer Container: Wächter, Analyse, Dienst)",
    "live.engine.cpu_ohne_limit":
        "suslik-CPU gerade: {kerne} Kerne (ganzer Container: "
        "Wächter, Analyse, Dienst)",
    "live.engine.rss": "Engine-RSS {rss} MB",
    "live.engine.grundkosten": "Grundkosten {mb} MB",
    "live.engine.je_stream": "{mb} MB je Stream ({quelle})",
    "live.engine.je_stream_fehlt":
        "RAM je Stream auf dieser Maschine noch nicht gemessen",
    "live.engine.ram_frei": "{mb} MB RAM frei ({quelle})",
    "live.engine.ram_unlesbar": "RAM: kein Container-Limit lesbar",
    "live.engine.detektor": "Detektor {ms} ms/Frame ({quelle})",
    "live.engine.drossel":
        "Drosselstufe {stufe}, Auslastung {auslastung}",
    "live.engine.rest":
        "nach einem weiteren Stream: ~{mb} MB RAM blieben übrig",
    "live.engine.rest_warnung":
        "— UNTER der Sicherheitsreserve, kein weiterer Slot",
    "live.engine.kapazitaet":
        "Kapazität: bis zu {n} Wächter (harte Obergrenze {hart}) "
        "— begrenzt durch: {grund}",
    "live.engine.hart": "harte Obergrenze {hart} Wächter",
    "live.engine.titel_standalone":
        "Live-Engine: läuft (eigenständige Engine erkannt)",
    "live.engine.titel_an": "Live-Engine: läuft",
    "live.gruppe.laufend": "Laufend",
    "live.gruppe.bereit": "Bereit",
    "live.gruppe.rest": "Nicht eingerichtet",
    "live.gruppe.versteckt": "Versteckt",
    "live.gruppe.ohne_area": "Ohne Bereich",
    "live.kachel.attr_fremd":
        "hier eingerichtet, aber diese Kamera ist gerade nicht in "
        "Frigate",
    "live.kachel.pill_fremd": "nicht in Frigate",
    "live.kachel.attr_detect":
        "Frigate-Detect-Stream — die echte Stream-Auflösung "
        "erscheint, sobald der Dienst den Stream sondiert oder ein "
        "Quellentest läuft",
    "live.knopf_konfigurieren": "Einrichten",
    "live.knopf_test": "Quellentest ausführen",
    "live.knopf_messung": "Last messen",
    "live.knopf_enable": "Einschalten",
    "live.knopf_disable": "Ausschalten",
    "live.knopf_zeigen": "Anzeigen",
    "live.knopf_verstecken": "Verstecken",
    "live.banner.kameraliste":
        "Die Frigate-Kameraliste ließ sich nicht lesen: {fehler}",
    "live.schalter.ungruppiert": "ungruppierte Sicht",
    "live.schalter.area": "nach Bereich gruppieren",
    "live.sperre.cpu_titel": "CPU-Modus",
    "live.sperre.titel": "Auf diesem Build nicht verfügbar",
    "live.sperre.satz":
        "Live-Wächter brauchen einen GPU-Build — integrierte "
        "Intel-Grafik (gpu-/gpu-legacy-Images), eine NVIDIA-Karte "
        "(cuda-Image) oder eine AMD-Karte (rocm-Image) kommen alle "
        "infrage.",
    "live.sperre.cpu_only":
        "Auf dem reinen CPU-Image sind sie nicht verfügbar.",
    "live.erklaer.titel":
        "Live-Wächter — sofortige Reaktion am Kamerastream",
    "live.erklaer.satz1":
        "Ein Live-Wächter verbindet sich direkt mit einem "
        "Kamerastream und reagiert, während die Person noch im Bild "
        "ist: Das erste Gesicht startet eine Prüfung, und nach der "
        "eingestellten Zahl übereinstimmender Treffer geht ein "
        "verifiziertes Signal raus — das Ziel ist unter einer "
        "Sekunde (gemessen 199–801 ms auf dem Referenz-Setup). Nutze "
        "es, um Automationen im Haus auszulösen, z. B. über MQTT.",
    "live.erklaer.link": "Mehr lesen: wie Live-Wächter arbeiten",
    "live.titel": "Live-Wächter",
    "live.leer.titel": "Keine Kameras gefunden.",
    "live.leer.hinweis":
        "Richte zuerst die Frigate-Verbindung ein — Kacheln "
        "erscheinen je Kamera.",
    "live.knopf_speichern": "Speichern",
    "live.detail.titel": "Live-Wächter — {name}",
    "live.abschnitt.quelle": "Quelle",
    "live.quelle.proxy":
        "go2rtc-Restream über Frigate (Standard, empfohlen)",
    "live.quelle.direct": "über go2rtc entdeckte Producer-URL der Kamera",
    "live.quelle.url": "eine Stream-URL, die du selbst einträgst",
    "live.detail.url_label": "Stream-URL (nur bei Quelle 'url'):",
    "live.detail.url_hinweis":
        "Zugangsdaten in der URL werden überall maskiert angezeigt "
        "— lass das Feld wie angezeigt, um die gespeicherte URL zu "
        "behalten, oder füge eine neue ein",
    "live.detail.quelle_hinweis":
        "Ein Quellenwechsel entwertet den Quellentest — führe ihn "
        "vor dem Einschalten erneut aus.",
    "live.abschnitt.aufloesung": "Verarbeitungsauflösung",
    "live.hoehe.default": "Standard (1080p)",
    "live.hoehe.h360":
        "360p — Notlösung für schwache GPUs, Name kommt am "
        "spätesten (gemessen)",
    "live.hoehe.h720": "720p — geringere Decode-Kosten, Name kommt später",
    "live.hoehe.h1080":
        "1080p — beste Wahl (gemessen: Name ~2,4 s früher als bei "
        "720p)",
    "live.hoehe.h1440": "1440p — kein gemessener Gewinn gegenüber 1080p",
    "live.hoehe.h2160":
        "2160p — natives 4K, marginaler Gewinn, höchste "
        "Decode-Kosten",
    "live.abschnitt.alarm": "Meldekette",
    "live.detail.ende_label": "Ende ohne Gesicht (s):",
    "live.detail.ende_hinweis":
        "ein Auftritt endet nach so vielen Sekunden ohne Gesicht "
        "(3–120)",
    "live.detail.scharf_label": "Wieder scharf nach (s):",
    "live.detail.scharf_hinweis":
        "Mindest-Sekunden zwischen Meldungen — ist jemand da, meldet "
        "es nach dieser Zeit erneut; 0 = jeder Trigger meldet (0–3600)",
    "live.abschnitt.kanaele": "Meldekanäle",
    "live.detail.namensschaetzung":
        "Meldungen enthalten eine vorläufige Namensschätzung "
        "(\"vermutlich X\"), wenn das Gesicht zu einer bekannten Person "
        "passt — nie gespeichert, nie fürs Anlernen verwendet.",
    "live.abschnitt.test": "Testen &amp; messen",
    "live.detail.gesperrt_hinweis":
        "Testen und Messen sind nicht verfügbar, solange "
        "Live-Wächter auf dieser Maschine gesperrt sind — der "
        "Hinweis oben auf dieser Seite erklärt, warum.",
    "live.knopf_messung_lang": "Last messen (15–30 s)",
    "live.detail.messung_hinweis":
        "die Lastmessung pausiert die anderen Wächter, solange sie "
        "läuft",
    "live.detail.link_zurueck": "zurück zur Übersicht",
    # ----------------------------------------------- routes/erkennung ---
    "erkennung.titel": "Erkennung",
    "erkennung.kopf.satz":
        "Die vier Wege, auf denen dein System jemanden erkennen kann "
        "— jeder als eigene Karte: schalten, sehen, dass es läuft, "
        "einrichten. Der Live-Schalter wirkt sofort; Körper- und "
        "Vision-Änderungen greifen mit Speichern + neu starten.",
    "erkennung.kipp.label": "Eingeschaltet",
    "erkennung.kipp.attr_verriegelt":
        "immer an — jeder andere Weg baut auf dem Gesichtsurteil auf",
    "erkennung.link_how": "So funktioniert es &#8230;",
    "erkennung.live.titel": "Live-Wächter",
    "erkennung.live.beweis_prefix": "beobachtet",
    "erkennung.live.beweis_zaehler": "{an} von {ges}",
    "erkennung.live.beweis_suffix": "eingerichteten Kameras",
    "erkennung.live.beweis_keine_laufend":
        "Kamera(s) eingerichtet, keine läuft",
    "erkennung.live.beweis_keiner": "noch kein Wächter eingerichtet",
    "erkennung.live.expert_schalter":
        "Ausschalten stoppt jeden laufenden Wächter; Einschalten "
        "startet alle eingerichteten Wächter (der Schalter je Kamera "
        "gilt weiterhin)",
    "erkennung.live.link_prokamera": "Steuerung je Kamera",
    "erkennung.live.knopf_kameras": "Kameras wählen …",
    "erkennung.knopf_register_face": "Gesicht registrieren …",
    "erkennung.gesicht.titel": "Gesichtserkennung",
    "erkennung.gesicht.satz":
        "Der präziseste Weg: Jeder Durchgang wird gegen die "
        "Gesichter der Personen geprüft, die du dem System angelernt "
        "hast. Sie ist das Rückgrat — Körper und Vision "
        "hängen an ihrem Durchgangsurteil, deshalb hat sie heute "
        "keinen Aus-Schalter.",
    "erkennung.gesicht.beweis_personen": "{n} Personen",
    "erkennung.gesicht.beweis_bilder": "{n} Referenzbilder",
    "erkennung.gesicht.knopf_verwalten": "Personen verwalten …",
    "erkennung.koerper.titel": "Körpererkennung",
    "erkennung.koerper.satz":
        "Erkennt Bewohner an Statur und Haltung, auch wenn kein "
        "Gesicht sichtbar ist — sie lernt von selbst aus den "
        "durchgesehenen Bildern.",
    "erkennung.koerper.beweis_kein_modell":
        "noch kein Personenmodell — erst anlernen und durchsehen",
    "erkennung.status.kein_modell":
        "läuft nicht (noch kein trainiertes Personenmodell "
        "scharfgeschaltet)",
    "erkennung.status.hier_aus": "läuft nicht (hier abgeschaltet)",
    "erkennung.status.vision_aus":
        "läuft nicht (die Vision-Erkennung ist abgeschaltet)",
    "erkennung.koerper.link_modell": "Modellstatus",
    "erkennung.koerper.knopf_status": "Modellstatus …",
    "erkennung.koerper.knopf_register": "Körper registrieren …",
    "erkennung.vision.titel": "KI-Vision",
    "erkennung.vision.beta": "Beta",
    "erkennung.vision.satz":
        "Eine Bild-KI als Schiedsrichter für die harten Fälle. "
        "Braucht einen Modell-Endpunkt (lokal oder bezahlt) — jede "
        "Prüfung kostet Anfragen.",
    "erkennung.vision.beweis_an": "Endpunkt verbunden",
    "erkennung.vision.beweis_aus": "kein Endpunkt verbunden",
    "erkennung.vision.knopf_connect": "Modell verbinden …",
    "erkennung.vision.knopf_register": "Vision registrieren …",
    "erkennung.abschnitt_property": "Grundstück einrichten",
    "erkennung.areas.titel": "Bereiche",
    "erkennung.areas.satz":
        "Was auf dem Grundstück zählt: Lege Bereiche an, damit "
        "Meldungen nur dort auslösen, wo es dich interessiert — "
        "die Einfahrt zählt, die Straße hinterm Zaun nicht.",
    "erkennung.areas.beweis_zahl": "Bereich(e) definiert",
    "erkennung.areas.beweis_keine": "noch keine Bereiche — alles zählt",
    "erkennung.areas.knopf": "Bereiche verwalten &#8230;",
    "erkennung.knopf_speichern": "Speichern + neu starten",
    # --------------------------------------------------- routes/faces ---
    "faces.titel": "Gesichter",
    "faces.link_how": "So funktioniert es &#8230;",
    "faces.bekannt.titel": "Bekannte Personen",
    "faces.bekannt.knopf_verwalten": "Personen verwalten &#8230;",
    "faces.bekannt.knopf_register": "Gesicht registrieren &#8230;",
    "faces.bekannt.leer":
        "noch keine Personen angelernt — registriere oben das erste "
        "Gesicht",
    "faces.bekannt.beweis_personen": "{n} Personen",
    "faces.bekannt.beweis_bilder": "{n} Referenzbilder",
    "faces.lernen.titel": "Anlernen",
    "faces.lernen.knopf_start": "Anlernen starten &#8230;",
    "faces.lernen.knopf_review": "Vorschläge durchsehen &#8230;",
    "faces.lernen.beweis_offen": "zur Durchsicht offen",
    "faces.lernen.beweis_leer":
        "nichts wartet — das System sammelt von selbst weiter",
    "faces.lernen.satz": "Sieh durch, was die Kameras gesammelt haben.",
    "faces.unbekannt.titel": "Unbekannte",
    "faces.unbekannt.knopf": "Unbekannte durchsehen &#8230;",
    "faces.unbekannt.beweis_offen": "wiederkehrende(r) Unbekannte(r)",
    "faces.unbekannt.beweis_leer":
        "keine wiederkehrenden unbekannten Besucher",
    "faces.unbekannt.satz": "Besucher, die noch keinen Namen haben.",
    "faces.qualitaet.titel": "Bildqualität",
    "faces.qualitaet.stand":
        "zuletzt geprüft {wann} &middot; {n} Fund(e)",
    "faces.qualitaet.knopf_check": "Qualitätscheck für meine Bilder",
    "faces.qualitaet.popup_satz":
        "Misst jedes Referenzbild neu (inkl. Gesichtsqualität) und sucht nach "
        "schwachen Bildern, Beinahe-Dubletten und verwechselten Gesichtern. "
        "Dauert je nach Bildzahl einige Minuten und läuft im Hintergrund.",
    "faces.qualitaet.label_alle": "Alle Personen",
    "faces.qualitaet.label_eine": "Eine Person:",
    "faces.qualitaet.knopf_start": "Qualitätscheck starten",
    "faces.qualitaet.knopf_abbrechen": "Abbrechen",
    "faces.qualitaet.knopf_ergebnisse": "Letzte Ergebnisse &#8230;",
    "faces.qualitaet.satz": "Findet schwache oder verwechselte Bilder.",
    # ----------------------------------------------- routes/qualitaet ---
    "qualitaet.kopf.titel": "Qualität — Referenzen",
    "qualitaet.kopf.hinweis":
        "tippe unten eine Person an, um alle ihre Bilder zu sehen; "
        "die schwachen sind markiert.",
    "qualitaet.kopf.stand": "Stand: {stand} · {n} Referenzen",
    "qualitaet.kopf.knopf_neu": "Jetzt neu prüfen",
    "qualitaet.lauf.fehler":
        "letzter Qualitätscheck FEHLGESCHLAGEN: {fehler} &mdash; "
        "starte ihn erneut.",
    "qualitaet.lauf.checking": "prüfe Bild {i} von {n} &hellip;",
    "qualitaet.lauf.reload_person":
        "lade diese Seite danach neu für das frische Ergebnis.",
    "qualitaet.lauf.abgebrochen":
        "der letzte Qualitätscheck lief nicht zu Ende "
        "(Dienst-Neustart oder gestoppt) &mdash; starte ihn erneut.",
    "qualitaet.tabelle.kopf_person": "Person",
    "qualitaet.tabelle.kopf_bilder": "Bilder",
    "qualitaet.tabelle.kopf_gut": "gut",
    "qualitaet.tabelle.kopf_mittel": "mittel",
    "qualitaet.tabelle.kopf_unter": "zu schwach",
    "qualitaet.tabelle.kopf_links": "&larr; links",
    "qualitaet.tabelle.kopf_front": "frontal",
    "qualitaet.tabelle.kopf_rechts": "rechts &rarr;",
    "qualitaet.tabelle.kopf_doppel": "Dubletten",
    "qualitaet.tabelle.kopf_verwechslung": "Verwechslung",
    "qualitaet.person.funde": "{n} Bild(er) einen Blick wert",
    "qualitaet.person.verwechselt": "womöglich verwechselt",
    "qualitaet.person.alles_gut": "alles gut",
    "qualitaet.ergebnis.alles_gut": "Alles gut.",
    "qualitaet.ergebnis.alles_gut_satz":
        "{n} Bilder von {np} Personen geprüft &mdash; nichts braucht "
        "deine Aufmerksamkeit.",
    "qualitaet.wort.defekt": "defekte Datei",
    "qualitaet.wort.kein_gesicht": "kein Gesicht gefunden",
    "qualitaet.wort.zu_klein": "zu klein",
    "qualitaet.wort.unscharf": "unscharf",
    "qualitaet.wort.schwach": "schwaches Bild",
    "qualitaet.galerie.looks_like": "sieht aus wie {name}",
    "qualitaet.galerie.doppel":
        "Dublette — das behaltene Bild deckt es ab",
    "qualitaet.galerie.gut": "gut",
    "qualitaet.galerie.gut_behalten":
        "gut — aus seinen Dubletten behalten",
    "qualitaet.galerie.vorrat": "aus dem Vorrat",
    "qualitaet.galerie.norm": "Qualität {norm}",
    "qualitaet.galerie.okay": "okay",
    "qualitaet.galerie.satz_gut": "Alle {n} Bilder sehen gut aus.",
    "qualitaet.galerie.satz_funde":
        "{funde} von {n} Bildern sind einen Blick wert — sie stehen in "
        "den beiden rechten Reitern. Hake an, was du entfernen willst "
        "— ohne deinen Klick passiert nichts.",
    "qualitaet.reiter.gut": "Gut ({n})",
    "qualitaet.reiter.check": "Ansehen ({n})",
    "qualitaet.reiter.weg": "Vorschlag: entfernen ({n})",
    "qualitaet.galerie.knopf_alle": "Alle auswählen",
    "qualitaet.galerie.knopf_keine": "Alle abwählen",
    "qualitaet.galerie.knopf_entfernen": "Ausgewählte entfernen",
    "qualitaet.galerie.leer_gruppe": "nichts in dieser Gruppe.",
    "qualitaet.galerie.titel": "{name} — Bildqualität",
    "qualitaet.galerie.link_zurueck": "&larr; zurück zur Übersicht",
    "qualitaet.galerie.leer_person": "keine Bilder zu dieser Person.",
    "qualitaet.leer.titel": "Noch kein Qualitätscheck berechnet.",
    "qualitaet.leer.hinweis": "Klicke oben auf Jetzt neu prüfen.",
    # ---------------------------------------------- routes/lernwizard ---
    "lernwizard.titel": "Lernlauf",
    "lernwizard.link_how": "So funktioniert es &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Vorbereitung",
    "lernwizard.phase.ernte": "Sammeln der Gesichter",
    "lernwizard.phase.anker": "Gruppierung (Anker)",
    "lernwizard.phase.benennung": "Benennung (dein Schritt)",
    "lernwizard.phase.neben_ansichten": "Seitenansichten",
    "lernwizard.phase.ganzkoerper": "Ganzkörper-Referenzen",
    "lernwizard.phase.uebernahme": "Übernahme in den Master",
    "lernwizard.phase.fertig": "Fertig",
    "lernwizard.phase.aktuell": "(aktuell)",
    "lernwizard.phase.link_benennen":
        "öffne die Gruppen und benenne sie",
    "lernwizard.wizard.titel": "Personen anlernen — geführter Lauf",
    "lernwizard.wizard.satz":
        "Plant einen Lernlauf über deine eigenen Aufnahmen. "
        "Vorbereitung, Sammeln, Gruppierung, Benennung und Übernahme "
        "in die Erkennung laufen alle wirklich ab.",
    "lernwizard.wizard.lage_b":
        "B — bestehende Referenzen/Unbekannte werden erweitert",
    "lernwizard.wizard.lage_a": "A — Kaltstart, noch keine Gesichter",
    "lernwizard.badge.unbekannt": "unbekannte Besucher",
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} unbekannter Besucher wartet unter",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} unbekannte Besucher warten unter",
    "lernwizard.link_unbekannte": "Personen &rarr; Unbekannte",
    "lernwizard.wizard.unbekannt_hinweis":
        "Heute gesammelte Gesichter, die zu keiner bekannten Person "
        "passen — du kannst sie dort sofort benennen, "
        "zusammenführen oder stummschalten; dafür ist kein "
        "Lernlauf nötig.",
    "lernwizard.wizard.start_titel": "Ausgangslage",
    "lernwizard.wizard.start_hinweis":
        "Aufräum-Schalter für automatisch gesammelte Unbekannte: "
        "kommt mit der Benennungs-Stufe.",
    "lernwizard.wizard.knopf_letzte": "letzte {n}",
    "lernwizard.wizard.knopf_alle": "ALLE erreichbaren",
    "lernwizard.wizard.attr_eigen": "eigenes N",
    "lernwizard.wizard.knopf_go": "los",
    "lernwizard.wizard.scope_titel": "Umfang (Events, nicht Tage)",
    "lernwizard.wizard.scope_hinweis":
        "ALLE geht die ganze erreichbare Historie durch (begrenzt "
        "durch Frigates Aufbewahrung — die Bilanz unten zeigt, wie "
        "weit).",
    "lernwizard.wizard.auswahl_titel": "Deine Auswahl",
    "lernwizard.wizard.auswahl_zeile":
        "letzte {n} Personen-Events = zurück bis {wann} · {clips} "
        "mit verfügbarem Clip",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} ältere ohne Clip werden übersprungen",
    "lernwizard.wizard.auswahl_hinweis":
        "Der Schnitt ist exakt bei N — das Auffüllen der Auswahl "
        "zu vollen Durchgängen kommt mit der Gruppierungs-Stufe.",
    "lernwizard.wizard.auswahl_durchsucht": "{k} dieser {n} sind schon durchsucht — mit \"Durchsuchtes überspringen\" nimmt der Lauf stattdessen ältere Events (die Karte zeigt, wo er landet).",
    "lernwizard.wizard.q_teilgemessen":
        "Analyse-Tempo auf DIESER Maschine gemessen; die "
        "Download-Schätzung nutzt Standardwerte",
    "lernwizard.wizard.q_gemessen": "auf DIESER Maschine gemessen",
    "lernwizard.wizard.q_skip":
        ", Messung auf dieser Maschine übersprungen ({grund})",
    "lernwizard.wizard.q_wartet":
        ", Messung wartet auf einen freien Analyse-Slot …",
    "lernwizard.wizard.q_laeuft": ", misst gerade …",
    "lernwizard.wizard.q_rueckfall":
        "Ersatzwerte — hier noch nicht gemessen",
    "lernwizard.wizard.dauer_titel": "Geschätzte Dauer",
    "lernwizard.wizard.dauer_zeile":
        "Analyse ~{analyse} · Clip-Downloads ~{download} · "
        "einmaliges Aufwärmen {kalt}",
    "lernwizard.wizard.dauer_gesamt": "gesamt ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Schwellen (einstellbar in den Erweiterten Einstellungen)",
    "lernwizard.wizard.frage":
        "Aus allen {n} Events lernen? Geschätzte Dauer ~{gesamt} "
        "(Analyse {analyse} + Downloads {download}). Der Lauf lässt "
        "sich jederzeit abbrechen.",
    "lernwizard.wizard.fps_titel": "Analyse-Bilder pro Sekunde",
    "lernwizard.wizard.knopf_start": "Diesen Lauf anlegen",
    "lernwizard.seg.vorbereiten": "Vorbereiten",
    "lernwizard.seg.sammeln": "Gesichter sammeln",
    "lernwizard.seg.sortieren": "In Gruppen sortieren",
    "lernwizard.status.laeuft_seit": "läuft seit {dauer}",
    "lernwizard.status.rest": "noch {rest}",
    "lernwizard.status.fertig_in": "fertig nach {dauer}",
    "lernwizard.balken.suchen": "Gesichter suchen",
    "lernwizard.balken.pose": "Kopfhaltung",
    "lernwizard.balken.erkennen": "Gesichter erkennen",
    "lernwizard.balken.z_frames": "Bild {f} von {s}",
    "lernwizard.balken.z_posen.eins": "{n} Pose",
    "lernwizard.balken.z_posen.viele": "{n} Posen",
    "lernwizard.balken.z_erkannt.eins": "{n} erkannt",
    "lernwizard.balken.z_erkannt.viele": "{n} erkannt",
    "lernwizard.balken.wartet": "wartet",
    "lernwizard.balken.clip": "Clip wird geholt …",
    "lernwizard.balken.fertig": "fertig",
    "lernwizard.status.aufnahmen": "Aufnahmen: {n}",
    "lernwizard.status.bilder": "bisher {n} Bilder gesammelt",
    "lernwizard.puls.working": "arbeitet — zuletzt aktualisiert vor {s} s",
    "lernwizard.puls.stumm":
        "seit {s} s keine Aktualisierung — ein langer Clip kann "
        "Minuten dauern; wächst das weiter, sieh in /log nach",
    "lernwizard.zeile.kaputt": "{n} unlesbare Zeilen gezählt",
    "lernwizard.zeile.anker_link": "die {n} Ankergruppen ansehen",
    "lernwizard.ergebnis.bilder.eins": "{n} Bild gesammelt",
    "lernwizard.ergebnis.bilder.viele": "{n} Bilder gesammelt",
    "lernwizard.ergebnis.aufnahmen.eins": "aus {n} Aufnahme",
    "lernwizard.ergebnis.aufnahmen.viele": "aus {n} Aufnahmen",
    "lernwizard.ergebnis.gruppen.eins": "in {n} Gruppe sortiert",
    "lernwizard.ergebnis.gruppen.viele": "in {n} Gruppen sortiert",
    "lernwizard.ergebnis.beiseite": "({n} aussortiert)",
    "lernwizard.kachel.lauf": "Lernlauf",
    "lernwizard.kachel.sammeln": "Sammeln &amp; sortieren",
    "lernwizard.kachel.benennen": "Gruppen benennen",
    "lernwizard.kachel.fertig": "Fertig &mdash; sie zählen",
    "lernwizard.such.titel": "Events nach Gesichtern durchsuchen",
    "lernwizard.such.klein": "geht rückwärts durch deine Aufnahmen",
    "lernwizard.pop.satz":
        "Geht rückwärts durch deine Aufnahmen und sammelt Gesichter. "
        "Im Alltag lernt das System von selbst weiter.",
    "lernwizard.pop.label_letzte": "Gehe rückwärts durch die letzten",
    "lernwizard.pop.wort_events": "Events",
    "lernwizard.pop.hint_n":
        "wie viele der jüngsten Aufnahmen geprüft werden (bis zu "
        "{max})",
    "lernwizard.pop.label_tag": "Ein ganzer Tag:",
    "lernwizard.pop.hint_tag":
        "jede Aufnahme dieses Tages, egal wie viele es sind",
    "lernwizard.pop.label_kameras": "Nur diese Kameras",
    "lernwizard.pop.hint_kameras": "nichts gewählt = alle Kameras; mehrere mit Strg/Cmd",
    "lernwizard.pop.wort_fps": "Bilder pro Sekunde",
    "lernwizard.pop.hint_fps":
        "mehr Bilder finden mehr Blickwinkel, aber die Suche dauert "
        "länger",
    "lernwizard.pop.label_skip": "Schon durchsuchte Events überspringen",
    "lernwizard.pop.hint_skip":
        "jede Suche arbeitet sich weiter in die Vergangenheit vor "
        "&mdash; Haken entfernen, um die neuesten Events erneut zu "
        "durchsuchen",
    "lernwizard.pop.alle_gesichter": "Alle Gesichter",
    "lernwizard.pop.eine_person": "Nur eine Person:",
    "lernwizard.pop.hint_person":
        "mit gewählter Person werden passende Gruppen zuerst "
        "gelistet &mdash; nichts wird versteckt",
    "lernwizard.pop.knopf_start": "Suche starten",
    "lernwizard.knopf_abbrechen": "Abbrechen",
    "lernwizard.k1.unbekannt.eins": "{n} unbekannter Besucher von heute:",
    "lernwizard.k1.unbekannt.viele": "{n} unbekannte Besucher von heute:",
    "lernwizard.k1.gestartet": "Lauf gestartet {wann}",
    "lernwizard.k1.scope": "Umfang {n} Events",
    "lernwizard.k1.kameras": "nur Kameras: {kameras}",
    "lernwizard.k1.tag": "Tag {tag}",
    "lernwizard.k1.mini_belichtung": "Abgleich Helligkeit",
    "lernwizard.k2.satz":
        "Läuft von allein &mdash; du kannst diese Seite "
        "schließen und wiederkommen.",
    "lernwizard.k2.knopf_abort": "Lauf abbrechen",
    "lernwizard.k3.satz_warten":
        "Der einzige Schritt, der dich braucht: Eine Gruppe soll eine "
        "Person sein &mdash; sag, wer es ist, oder überspringe sie.",
    "lernwizard.k3.keine_gesichter":
        "Diesmal keine neuen Gesichter &mdash; nichts zu benennen. Das "
        "ist in Ordnung: Es heißt nur, dass in den Aufnahmen niemand "
        "Neues war.",
    "lernwizard.knopf_neuer_lauf": "Neuen Lauf starten",
    "lernwizard.k3.gruppe_offen":
        "Die aktuelle Gruppe ist unten geöffnet, in voller Breite.",
    "lernwizard.k3.alle_erledigt": "Alle Gruppen sind erledigt.",
    "lernwizard.chip.bilder": "{n} Bilder",
    "lernwizard.k3.verworfen.eins":
        "{n} Gruppe von dir gelöscht &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} Gruppen von dir gelöscht &middot;",
    "lernwizard.k3.link_einsehen": "einsehen",
    "lernwizard.k3.done_weiter":
        "{erledigt} von {gesamt} erledigt &mdash; die nächste steht "
        "bereit.",
    "lernwizard.k3.done_punkt": "{erledigt} von {gesamt} erledigt.",
    "lernwizard.k3.wartend.eins": "{n} Gruppe wartet auf dich.",
    "lernwizard.k3.wartend.viele": "{n} Gruppen warten auf dich.",
    "lernwizard.k4.adopt_bilder.eins": "{n} Bild übernommen für",
    "lernwizard.k4.adopt_bilder.viele": "{n} Bilder übernommen für",
    "lernwizard.k4.adopt_personen.eins": "{n} Person",
    "lernwizard.k4.adopt_personen.viele": "{n} Personen",
    "lernwizard.k4.zaehlen_sofort":
        "sie zählen sofort für die Erkennung.",
    "lernwizard.k4.link_qs": "Qualitätscheck der Referenzen &#8230;",
    "lernwizard.k4.nichts":
        "diesmal wurden keine neuen Bilder übernommen (Gruppen "
        "übersprungen oder schon abgedeckt).",
    "lernwizard.k4.wiederholen":
        "Wiederhole das alle paar Tage, oder lass die Heute-Seite "
        "zwischendurch bekannte Personen auffüllen.",
    "lernwizard.k4.knopf_faces": "Zurück zu Gesichter",
    "lernwizard.k4.hinweis":
        "Benannte Bilder werden zu Referenzen und zählen sofort "
        "für die Erkennung.",
    "lernwizard.zw.grund_maessig": "Bildqualität nur mittel",
    "lernwizard.zw.attr_clip": "Clip öffnen",
    "lernwizard.blick.links": "Blick nach links",
    "lernwizard.blick.frontal": "Frontal",
    "lernwizard.blick.rechts": "Blick nach rechts",
    "lernwizard.blick.leer":
        "keine brauchbaren Bilder aus diesem Blickwinkel in der Gruppe",
    "lernwizard.blick.legende":
        "({gut} gut, {grenz} grenzwertig von {n} geprüften)",
    "lernwizard.zw.titel":
        "Gruppe {pos} von {gesamt} &mdash; wer ist das?",
    "lernwizard.zw.satz":
        "Eine Gruppe soll eine Person sein. Tippe ein Bild an, um es "
        "auszulassen &mdash; dann sag, wer es ist, oder überspringe "
        "die Gruppe.",
    "lernwizard.bekannt.system": "schon in deinem System",
    "lernwizard.bekannt.anker": "in einer anderen Gruppe benannt",
    "lernwizard.zw.knopf_adopt": "Als {name} übernehmen",
    "lernwizard.zw.knopf_ja": "Ja, das ist {name}",
    "lernwizard.zw.fehler":
        "die Bildprüfung konnte nicht laufen (siehe /log) &mdash; "
        "neu laden für einen neuen Versuch; Überspringen und "
        "Löschen gehen weiterhin.",
    "lernwizard.zw.warte":
        "prüfe die Bilder dieser Gruppe gegen die Referenz-Messlatte "
        "&mdash; ein paar Sekunden &hellip;",
    "lernwizard.zw.knopf_andere": "Jemand anderes &#8230;",
    "lernwizard.zw.attr_name": "Personenname (neu oder bestehend)",
    "lernwizard.zw.knopf_save": "Namen speichern",
    "lernwizard.zw.knopf_skip": "Diese Gruppe überspringen",
    "lernwizard.zw.frage_delete":
        "Diese Gruppe löschen? Ihre Bilder werden entfernt, eine ausstehende Benennung entfällt. Das lässt sich nicht rückgängig machen.",
    "lernwizard.zw.knopf_delete": "Diese Gruppe löschen",
    "lernwizard.zw.link_detail": "volle Detailansicht",
    "lernwizard.zw.detail_zusatz":
        "(alle Bilder mit Gründen, Experten-Auswahl)",
    "lernwizard.erfolg.titel": "Gruppierung fertig",
    "lernwizard.erfolg.cluster.eins": "{n} Gesichtergruppe bereit:",
    "lernwizard.erfolg.cluster.viele": "{n} Gesichtergruppen bereit:",
    "lernwizard.erfolg.knopf_anker": "Die Ankergruppen ansehen",
    "lernwizard.erfolg.hinweis": "öffne eine Gruppe, um sie zu benennen",
    "lernwizard.expert.phasen_titel": "Phasen",
    "lernwizard.expert.phasen_hinweis":
        "Vorbereitung, Sammeln, Gruppierung, Benennung und Übernahme "
        "in den Master laufen in diesem Build wirklich ab — "
        "Seitenansichten und die Ganzkörper-Referenzen werden mit "
        "den kommenden Versionen aktiv.",
    "lernwizard.expert.progress_titel": "Fortschritt",
    "lernwizard.expert.anker_bisher": "Anker bisher: {n}",
    "lernwizard.expert.progress_rest":
        "angelegt {wann} · Umfang {n} Events · übersteht "
        "Neustarts (Fortsetzen eingebaut)",
    "lernwizard.expert.lauf_bleibt":
        "dieser Lauf bleibt — seine Anker bleiben verfügbar",
    # -------- Abgleich Helligkeit /lernlauf/belichtung (Phase 1b, 26.08.) --
    "belichtung.titel": "Abgleich Helligkeit",
    "belichtung.satz":
        "Stell die beiden Helligkeits-Linien an eigenen Bildern ein. Jede Reihe "
        "ist ein Gesichts-Cluster, sortiert wie der Server gerade sortiert: "
        "Bilder außerhalb der Linien fallen ans Ende und sind rot markiert. "
        "Gelöscht wird nichts — ein zurückgestuftes Bild lässt sich weiter von "
        "Hand wählen.",
    "belichtung.jetzt": "Aktuell gültig: dunkelste {von}, hellste {bis}.",
    "belichtung.hinweis_aus":
        "Beide Linien sind aus, es fällt nichts zurück — zieh einen Regler, um "
        "zu sehen, was eine Linie täte.",
    "belichtung.aus_wort": "aus",
    "belichtung.regler_min": "dunkelste erlaubte",
    "belichtung.regler_max": "hellste erlaubte",
    "belichtung.regler_hinweis":
        "Helligkeit läuft von 0 (schwarz) bis 255 (weiß); 0 schaltet diese "
        "Seite aus.",
    "belichtung.bilanz": "{n} von {m} Bildern fallen zurück",
    "belichtung.vorschau":
        "Nur Vorschau — die Bilder werden im Browser umsortiert. Speichern "
        "lässt den Server so sortieren.",
    "belichtung.knopf_speichern": "Diese Grenzen speichern",
    "belichtung.reihe_info":
        "{n} von {gesamt} gemessenen Bildern · Helligkeit {von} bis {bis}",
    "belichtung.lage_dunkel": "zu dunkel",
    "belichtung.lage_hell": "überbelichtet",
    "belichtung.lage_ok": "innerhalb der Grenzen",
    "belichtung.zurueck": "zurück zum Lernlauf",
    "belichtung.leer_satz":
        "Noch trägt kein Bild einen Helligkeitswert, es gibt also nichts zum "
        "Abgleichen.",
    "belichtung.leer_hinweis":
        "Die Helligkeit wird beim Ernten der Gesichter gemessen. Sie entsteht "
        "ab dem nächsten Lernlauf oder Durchgangs-Check; ältere Bilder werden "
        "nie nachgemessen.",
    # --------------------------------- Stufe 1: Einhang/Skelett (webui) ---
    "nav.bereich.activity": "Aktivität",
    "nav.bereich.faces": "Gesichter",
    "nav.bereich.learn": "Anlernen",
    "nav.bereich.person": "Person",
    "nav.bereich.vision": "Vision",
    "nav.bereich.live": "Live",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Konfiguration",
    "nav.bereich.erkennungstest": "Erkennungstest",
    "nav.bereich.system": "System",
    "nav.heute": "Heute",
    "nav.ereignisse": "Events",
    "nav.offen": "Zum Benennen",
    "nav.faces": "Gesichter",
    "nav.gesichter": "Bekannte Personen",
    "nav.unbekannte": "Unbekannte",
    "nav.qualitaet": "Qualität",
    "nav.lernlauf": "Lernlauf",
    "nav.anker": "Anker",
    "nav.lernen": "Vorschläge",
    "nav.person": "Körperbilder",
    "nav.person_kontrolle": "Beurteilte Bilder",
    "nav.person_modell": "Modellstatus",
    "nav.personlauf": "Personen-Lernlauf",
    "nav.vision": "Vision-Erkennung",
    "nav.live": "Live-Wächter",
    "nav.live_alerts": "Live-Meldungen",
    "nav.erkennung": "Erkennung",
    "nav.kameras": "Kameras",
    "nav.benachrichtigungen": "Meldungen",
    "nav.areas": "Bereiche",
    "nav.kette": "Erkennungskette",
    "nav.konfiguration": "Erweitert",
    "nav.erkennungstest": "Erkennungstest",
    "nav.system": "System",
    "nav.systemstat": "Systemstatistik",
    "nav.sync_auswahl": "Frigate-Abgleich",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Dienst-Log",
    "ui.fuss.docs": "Doku",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip": "Easy zeigt die Kernseiten — Expert zeigt alles. Nichts wird gelöscht, Easy blendet nur aus.",
    "ui.live.chip": "Live",
    "ui.theme.knopf": "Theme",
    "ui.last.knopf": "Systemstatistik",
    "ui.last.tooltip": "Auslastung: CPU, RAM, Platte, GPU und die Erkennung",
    "ui.theme.tooltip": "Zwischen Hell und Dunkel wechseln",
    "ui.theme.aria": "Farbschema wechseln",
    "ui.sprache.tooltip": "Sprache dieser Installation — gilt für alle Seiten und Meldungen",
    "ui.upd.link": "Update {tag}",
    "ui.upd.tooltip": "Eine neuere suslik-Version ist auf GitHub verfügbar",
    "ui.upd.titel": "Update verfügbar",
    # ui.upd.satz ist der erste deklarierte t_html-Schluessel (HTML_SCHLUESSEL,
    # core/sprache.py) — Tag-Folge muss in jeder Sprache identisch sein.
    "ui.upd.satz": "Ein neueres suslik-Image (<b>{tag}</b>) liegt auf GitHub — <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">Release-Notes</a>. Zum Aktualisieren das neue Image ziehen und neu starten; deine Daten und Einstellungen bleiben erhalten.",
    "ui.wn.titel": "Was ist neu",
    "ui.wn.x_tooltip": "Bis zur nächsten Version ausblenden",
    "ui.wn.x_aria": "Ausblenden",
    "ui.wn.mehr": "Alle zeigen ({n})",
    "ui.wn.weniger": "Weniger zeigen",
    # --------------------------------- Stufe 1: Seitentitel (verifyd) ---
    "titel.setup": "Einrichtung",
    "titel.anker_detail": "Anker",
    "titel.aehnliche": "Passende Gesichter",
    "titel.live_kamera": "Live — {kamera}",
    "titel.video": "Video",
    "titel.event": "Event",
    "titel.vision_galerie": "Galerie aufbauen",
    "titel.hilfe": "So funktioniert es",
    # --------------------------------- Stufe 1: Setup-Wizard Schritt 0 ---
    "setup.sprache.titel": "Sprache",
    "setup.sprache.satz": "Wähle die Sprache dieser Installation — sie gilt sofort und auch für Meldungen. Du kannst sie jederzeit über den Schalter in der Kopfleiste ändern.",
    # --------------------------------- Stufe 1: js.* (window.T, app.js) ---
    # VERTRAG: app.js liest NUR js.*-Schluessel (TT() mit EN-Fallback ==
    # diesem Wert); jede Richtung prueft die Gate-Stufe Sprach-Deckung.
    "js.status.fehler": "Fehler",
    "js.status.fehler_gross": "Fehler",
    "js.status.fehler_detail": "Fehler: {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "wird gespeichert …",
    "js.status.gespeichert": "gespeichert",
    "js.status.senden": "wird gesendet …",
    "js.status.starten": "startet …",
    "js.status.laeuft": "läuft …",
    "js.status.laeuft_wort": "läuft",
    "js.status.pruefen": "wird geprüft …",
    "js.status.suchen": "wird gesucht …",
    "js.status.lernen": "wird angelernt …",
    "js.status.hinzufuegen": "wird hinzugefügt …",
    "js.status.entfernen": "wird entfernt …",
    "js.status.loeschen": "wird gelöscht …",
    "js.status.hochladen": "wird hochgeladen …",
    "js.status.wiederherstellen": "wird wiederhergestellt …",
    "js.status.ueberspringen": "wird übersprungen …",
    "js.status.siehe_log": "siehe Dienst-Log",
    "js.status.diagnose": "Diagnose",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Abbrechen",
    "js.neustart.zurueck": "Dienst ist zurück, lade …",
    "js.neustart.kommt": "Dienst kommt zurück …",
    "js.neustart.gespeichert": "Gespeichert. Dienst startet neu, bitte warten …",
    "js.neustart.warten": "Dienst startet neu, bitte warten …",
    "js.konfig.frage": "Konfiguration speichern und den Dienst neu starten?",
    "js.lernlauf.fps_zeile": "≈ gesamt ~{dauer} bei {fps}/s",
    "js.lernlauf.tag_fehlt": "erst einen Tag wählen",
    "js.lernlauf.abbruch_frage": "Diesen Lernlauf abbrechen?",
    "js.notif.frage": "Meldeeinstellungen speichern und den Dienst neu starten?",
    "js.frigate.ro_frage": "Auf NUR-LESEN umschalten? suslik schreibt dann nichts mehr nach Frigate.",
    "js.frigate.rw_frage": "SCHREIBEN nach Frigate aktivieren (sub_labels + Referenz-Abgleich)?",
    "js.catchup.frage": "Verpasste Ereignisse ab sofort beim Start überspringen? Der Dienst startet dafür neu.",
    "js.restore.frage": "Konfiguration aus \"{name}\" wiederherstellen? Das überschreibt die aktuellen Einstellungen und startet den Dienst neu.",
    "js.vollrestore.frage": "Das KOMPLETTE Backup \"{name}\" wiederherstellen? Das ersetzt Einstellungen, Referenzen und alles gelernte Material und startet den Dienst neu.",
    "js.vollrestore.laeuft": "wird hochgeladen und wiederhergestellt … (große Dateien brauchen ihre Zeit)",
    "js.enroll.fehler": "Fehler: {msg}",
    "js.enroll.person_fehlt": "Person wählen oder eine neue eintragen.",
    "js.upload.fehlt": "Person (Auswahl oder neu) und eine Datei wählen.",
    "js.upload.trotzdem": "{msg}\n\nTrotzdem hinzufügen?",
    "js.anlernen.frage": "Gruppe als \"{person}\" übernehmen (die besten Bilder werden Referenzen)?",
    "js.anlernen.name_frage": "Name der neuen Person:",
    "js.anlernen.person_fehlt": "Bitte eine vorhandene Person wählen.",
    "js.auswahl.gesicht_fehlt": "Bitte mindestens ein Gesicht anhaken.",
    "js.auswahl.bild_fehlt": "Bitte mindestens ein Bild auswählen.",
    "js.vorschlag.keine": "Keine empfohlenen Gesichter.",
    "js.vorschlag.alle_frage": "Alle {n} empfohlenen Gesichter zu {person} hinzufügen? Sie werden sofort Referenzen.",
    "js.vorschlag.frage": "{n} Gesicht(er) zu {person} hinzufügen?",
    "js.vorrat.frage": "{n} Vorrats-Gesicht(er) zu {person} hinzufügen? Sie werden sofort Referenzen (bleiben lokal, kein Export).",
    "js.qs.fortschritt": "prüfe Bild {i} von {n} …",
    "js.sync.frage": "Abgleichen: {richtung}?",
    "js.sync.modell_laedt": "Modell lädt …",
    "js.sync.fortschritt": "{done}/{total} Gesichter ({current}) {pct}%",
    "js.sync.fertig": "fertig: {ok} ok, {gate} übersprungen — Seite lädt neu …",
    "js.sync.fehler": "Abgleich fehlgeschlagen: {grund}",
    "js.syncauswahl.knopf": "{n} Ausgewählte nach Frigate übertragen",
    "js.syncauswahl.nichts": "Nichts ausgewählt",
    "js.syncauswahl.nichts_klein": "nichts ausgewählt",
    "js.syncauswahl.skip": "überspringen",
    "js.syncauswahl.restore": "zurückholen",
    "js.syncauswahl.wieder": "wieder anbieten",
    "js.syncauswahl.zurueck_laeuft": "wird zurückgeholt …",
    "js.syncauswahl.frage": "{n} Referenzbild(er) nach Frigate senden?",
    "js.syncauswahl.fehl_knopf": "Übertragung fehlgeschlagen",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct}%",
    "js.syncauswahl.fertig": "fertig: {ok} hochgeladen, {gate} nicht angenommen — Seite lädt neu …",
    "js.syncauswahl.fehler": "Übertragung fehlgeschlagen: {grund}",
    "js.vorpruef.haengt": "Vorprüfung hängt offenbar — Seite neu laden und erneut versuchen",
    "js.vorpruef.laeuft": "Bilder werden geprüft … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "Vorprüfung fehlgeschlagen: {grund}",
    "js.vorpruef.fertig": "Vorprüfung fertig — Seite lädt neu …",
    "js.import.fortschritt": "Download {done}/{total} ({current}) {pct}%",
    "js.import.fertig_wiz": "✓ {n} importiert — Merkmale werden auf dem Beschleuniger berechnet …",
    "js.import.knopf_fertig": "Importiert ✓",
    "js.import.fehler": "Import fehlgeschlagen: {grund}",
    "js.import.knopf": "Gesichter importieren",
    "js.import.knopf_ges": "Gesichter aus Frigate importieren",
    "js.import.fertig_ges": "✓ {n} importiert — Merkmale werden berechnet, Seite lädt neu …",
    "js.ref.frage": "Referenzbild von {person} entfernen?",
    "js.ref.batch_frage": "{n} Bild(er) löschen?",
    "js.dienst.nicht_erreichbar": "Dienst nicht erreichbar — gleich noch einmal versuchen.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage": "Als bekannten Fremden ignorieren? Er löst dann keine Meldungen mehr aus. (Jederzeit unten unter \"bekannte Besucher\" wieder aktivierbar.)",
    "js.unb.ziel_fehlt": "Zielidentität wählen.",
    "js.unb.merge_frage": "Zusammenführen?",
    "js.unb.name_fehlt": "Namen eingeben (neue oder vorhandene Person).",
    "js.unb.benennen_frage": "Der Person \"{person}\" zuordnen? Die besten Bilder werden Referenzen.",
    "js.person.loesch_frage": "ALLE Referenzen und den Namen \"{person}\" löschen?\nDie Bilder wandern in den Papierkorb-Ordner (wiederherstellbar).\n\nZur Bestätigung den Namen eintippen:",
    "js.person.name_falsch": "Name stimmte nicht überein — nichts gelöscht.",
    "js.areas.fehl": "Speichern fehlgeschlagen — ist der Dienst erreichbar?",
    "js.areas.name_fehlt": "Erst einen Bereichsnamen eingeben.",
    "js.areas.existiert": "Diesen Bereich gibt es schon.",
    # js.areas.entfernen_frage: "Default" ist zugleich Kennung der
    # Standard-Area (Anzeige==Kennung §8.2) — bleibt in jeder Sprache.
    "js.areas.entfernen_frage": "Bereich \"{name}\" entfernen? Seine Kameras wandern zurück nach Default — sonst ändert sich nichts.",
    "js.personlauf.abbruch_frage": "Diesen Personen-Lernlauf abbrechen? Gesammelte Bilder bleiben.",
    "js.personlauf.verwerfen_frage": "Lauf {lid} komplett verwerfen? Alle seine Bilder werden gelöscht; ein neuer Lauf kann jederzeit neu sammeln.",
    "js.vision.nicht_erreichbar": "Dienst nicht erreichbar — nichts wurde gespeichert",
    "js.vision.gespeichert": "gespeichert — die Erkennung nutzt ab jetzt diese Verbindung",
    "js.vision.gespeichert_neustart": "gespeichert — der Dienst startet gleich neu",
    "js.vision.gespeichert_reload": "gespeichert — der Dienst startet neu, die Seite lädt gleich neu",
    "js.vision.treffer": "{n}/2 richtig",
    "js.vision.tokens": "{ist} Tokens vs {soll}",
    "js.vision.dirty_titel": "Diese Verbindung ist nicht gespeichert",
    # js.vision.dirty_text UND js.vision.prompt_zurueck zitieren den
    # Vision-Knopf vision.save.knopf ("Verbindung speichern") WOERTLICH —
    # Zitat-Folge (Tranche C), bei Aenderungen dort hier BEIDE nachziehen.
    "js.vision.dirty_text": "Der Test würde die eben getippten Werte benutzen. Die Erkennung nutzt weiter die GESPEICHERTE Verbindung, bis \"Verbindung speichern\" gedrückt wird — ein grüner Test allein ändert nichts an den Urteilen.",
    "js.vision.dirty_save": "Erst speichern, dann testen",
    "js.vision.dirty_test": "Ohne Speichern testen",
    "js.vision.stufe1": "Erreichbarkeit und Modell",
    "js.vision.stufe2": "Zwangswahl-Formprobe",
    "js.vision.stufe3": "Token-Zahl",
    "js.vision.stufe_laeuft": "Schritt {nr}/3 — {name} … (ein lokales Modell auf CPU kann Minuten brauchen)",
    "js.vision.test_fehl": "der Test konnte nicht laufen",
    "js.vision.stufe_stop": "bei Schritt {nr} gestoppt — siehe Log unten",
    "js.vision.fertig": "fertig — {ampel}",
    "js.vision.stufe_fehl": "Schritt {nr} konnte nicht laufen",
    "js.vision.neustart_warte": "der Dienst antwortet gerade nicht — die Seite lädt gleich neu",
    "js.vision.prompt_frage": "Die Frage auf den Standard-Wortlaut zurücksetzen?",
    "js.vision.prompt_zurueck": "Standard-Wortlaut wiederhergestellt — mit \"Verbindung speichern\" übernehmen",
    "js.vision.kachel_frage": "Es gibt ungespeicherte Änderungen. Ein Anbieterwechsel verwirft sie. Weiter?",
    "js.vision.pick": "— bitte wählen —",
    "js.vision.untested": "hier ungetestet",
    "js.vision.neu_pruefen": "die Verbindung hat sich geändert — erneut prüfen, um ihre Modelle zu sehen",
    "js.vision.key_laeuft": "frage beim Anbieter an, welche Modelle nutzbar sind …",
    "js.vision.key_fehl": "die Prüfung schlug fehl",
    "js.vision.key_fehl2": "die Prüfung konnte nicht laufen",
    "js.rt.start": "Vision-Lauf startet …",
    "js.rt.fehl": "der Lauf konnte nicht starten",
    "js.rt.nach_fehl": "konnte nicht starten",
    "js.vw.geliehen": "aus der Reihe {reihe}",
    "js.vw.vergessen_frage": "Die für diese Galerie aussortierten Bilder vergessen? Sie können wieder vorgeschlagen werden.",
    "js.vw.leer_frage": "{n} Zelle(n) blieben leer. Galerie trotzdem abnehmen?",
    "js.vw.kopiert": "Bilder werden in die Galerie kopiert …",
    # js.live.phase_*: Anzeige-Woerter zu den Status-KENNUNGEN des
    # Live-Polls (Status-replace-Mapping, §8-Nachtrag).
    "js.live.phase_verbinden": "Verbinden",
    "js.live.phase_messen": "Messen",
    "js.live.phase_auswerten": "Auswerten",
    "js.live.phase_abbruch": "Abbrechen",
    "js.live.rest": " — noch {n} s",
    "js.live.auftrag_zeile": "{art} auf {kamera}: {phase}{rest}{pausiert}",
    "js.live.messung": "Lastmessung",
    "js.live.quelltest": "Quellentest",
    "js.live.pausiert": " — Wächter für die Messung pausiert ({liste})",
    "js.live.job_laeuft": "Quellentest läuft (Helfer-Prozess, bis ~2 Minuten) …",
    "js.live.job_ok": "Quellentest fertig: {text}",
    "js.live.job_fehl": "Quellentest FEHLGESCHLAGEN: {text}",
    "js.live.messung_fehl": "Lastmessung fehlgeschlagen: {grund}",
    "js.live.test_fehl": "Quellentest fehlgeschlagen: {grund}",
    # ---- auftritte (Stufe 2, Tranche A) ----
    # Uebersetzung 19.08.2026, Muttersprachler-QS dieser Tranche DURCHLAUFEN
    # (12 Korrekturen); Kontext + Stufe-2-Grenzen: siehe en.py-Abschnittskopf.
    "auftritte.unbek.zaehlung": "+{n} ohne Treffer (meist dieselben Personen)",
    "auftritte.unbek.name": "Unbekannt {nummer}",
    "auftritte.unbek.ohne_treffer.eins": "{n} Event mit Gesicht ohne Treffer",
    "auftritte.unbek.ohne_treffer.viele": "{n} Events mit Gesicht ohne Treffer",
    "auftritte.nav.zurueck_heute": "&#8592; Heute",
    "auftritte.unbek.titel": "Unbekannt",
    "auftritte.unbek.leer_link": "Diesem Link fehlt der Durchgang.",
    "auftritte.unbek.leer_weg":
        "Dieser Durchgang steht nicht mehr auf der Heute-Seite.",
    "auftritte.unbek.leer_weg_hinweis":
        "Der Tag wurde womöglich neu gruppiert — öffne den Durchgang noch "
        "einmal von der Heute-Seite aus.",
    "auftritte.unbek.leer_pool":
        "Keine gesammelten Gesichter zu diesem Durchgang.",
    "auftritte.unbek.leer_pool_hinweis":
        "Die gesammelten Bilder wurden inzwischen womöglich aufgeräumt.",
    "auftritte.knopf.video": "Video",
    "auftritte.karte.faces.eins": "{n} Gesicht",
    "auftritte.karte.faces.viele": "{n} Gesichter",
    "auftritte.karte.kameras.eins": "{n} Kamera",
    "auftritte.karte.kameras.viele": "{n} Kameras",
    "auftritte.unbek.mehr_im_lauf": "mit {n} weiteren in diesem Durchgang",
    "auftritte.unbek.ein_lauf": "ein Durchgang",
    "auftritte.zuweisen.titel": "Wer ist das?",
    "auftritte.zuweisen.satz":
        "Das sind die Gesichter aus DIESEM Durchgang. Hake die an, die "
        "wirklich zur Person gehören &mdash; Unbrauchbares bleibt zurück. Gib "
        "ihnen einen Namen (neu oder bestehend), dann werden sie "
        "angelernt; tust du nichts, bleiben sie unbekannt.",
    "auftritte.zuweisen.knopf_alle": "Alle auswählen",
    "auftritte.zuweisen.knopf_keine": "Keine",
    "auftritte.zuweisen.attr_person": "Person (neu oder bestehend)",
    "auftritte.zuweisen.knopf_zuweisen": "Ausgewählte Gesichter hinzufügen",
    "auftritte.zuweisen.js_keine": "mindestens ein Gesicht anhaken",
    "auftritte.zuweisen.js_name": "einen Personennamen eingeben",
    "auftritte.zuweisen.js_lernt": "wird angelernt…",
    "auftritte.zuweisen.js_fehler": "Fehler",
    "auftritte.unbek.titel_lauf": "Unbekannt {nummer} — Durchgang",
    "auftritte.leer_person": "Diese Person ist nicht bekannt.",
    "auftritte.leer_person_hinweis": "Wähle eine Person auf der Heute-Seite.",
    "auftritte.titel": "Auftritte",
    "auftritte.nav.attr_tag": "zurück zum Tag",
    "auftritte.nav.attr_vortag": "Vortag",
    "auftritte.kopf.passzahl.eins": "{n} Durchgang",
    "auftritte.kopf.passzahl.viele": "{n} Durchgänge",
    "auftritte.nav.attr_kein_morgen": "keine zukünftigen Tage",
    "auftritte.nav.attr_folgetag": "Folgetag",
    "auftritte.titel_person": "{person} — Auftritte",
    "auftritte.leer_passe":
        "Keine bestätigten Durchgänge von {person} an diesem Tag.",
    "auftritte.leer_passe_hinweis": "Blättere mit den Tagespfeilen.",
    "auftritte.karte.kein_bild": "kein Bild",
    "auftritte.thumb.zusatz_unbestaetigt": " — hier nicht bestätigt",
    "auftritte.thumb.zusatz_referenz": " — in den Referenzen",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} Event ohne Gesicht",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} Events ohne Gesicht",
    "auftritte.thumb.hinweis_referenz":
        "grüner Rand = schon in den Referenzen",
    "auftritte.karte.best_punkt": "bestätigt um {zeit}",
    "auftritte.karte.best_spanne": "bestätigt {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "läuft",
    "auftritte.karte.pass_nr": "Durchgang {n}",
    "auftritte.karte.events.eins": "{n} Event",
    "auftritte.karte.events.viele": "{n} Events",
    "auftritte.karte.best_match": "bester Treffer {wert}",
    "auftritte.karte.auch_dabei": "auch in diesem Durchgang: {namen}",
    "auftritte.pass.titel": "Durchgang",
    "auftritte.pass.leer_event": "Event nicht gefunden.",
    "auftritte.pass.leer_event_hinweis":
        "Es ist womöglich zu alt und aus dem Log gefallen.",
    "auftritte.pass.leer_gruppe":
        "Dieses Event gehört zu keinem gruppierten Durchgang.",
    "auftritte.pass.leer_gruppe_hinweis":
        "Die Gruppierung braucht den Zusammenhang des ganzen Tages.",
    "auftritte.nav.zurueck_tag": "&#8592; Tag",
    "auftritte.pass.attr_vor": "voriger Durchgang des Tages",
    "auftritte.pass.attr_nach": "nächster Durchgang des Tages",
    "auftritte.pass.kopf": "Durchgang {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Ohne Treffer",
    "auftritte.pass.label_gt": "Benennung",
    "auftritte.pass.badge_fremd": "als fremd bestätigt",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log enthält keine Zeile mit dem Grund — öffne das Event "
        "für das ganze Log",
    "auftritte.pass.grund_ohne_log":
        "zu diesem Event ist kein analyze.log abgelegt — siehe Dienst-Log",
    "auftritte.pass.label_fehler": "Fehler",
    "auftritte.pass.wer": "Wer",
    "auftritte.pass.titel_zeit": "Durchgang {zeit} — {tag}",
    # ---- verifyd-Innenseiten (Stufe 2, Tranche B) ----
    # Uebersetzung 20.08.2026 (begriffe_tabellen.md, DE-Abschnitt);
    # Kontext + Stufe-2-Grenzen: siehe en.py-Abschnittskopf.
    "banner.schoner":
        "Frigate antwortet nicht — suslik wartet ab und prüft alle paar "
        "Sekunden, bis es wieder erreichbar ist; die Oberfläche zeigt "
        "weiter lokale Daten.",
    "banner.fehler":
        "Frigate nicht erreichbar (letzter Fehler {zeit}): {fehler} — die "
        "Oberfläche zeigt weiter lokale Daten.",
    "banner.nachholen.eins":
        "Verpasste Ereignisse der letzten Stunde werden nachgeholt: "
        "{fertig} von {gesamt}",
    "banner.nachholen.viele":
        "Verpasste Ereignisse der letzten {n} Stunden werden nachgeholt: "
        "{fertig} von {gesamt}",
    "banner.nachholen_aus": "Künftig beim Start nicht mehr nachholen",
    "hinweis.frigate_fr_an": "Frigates eigene Gesichtserkennung ist eingeschaltet. suslik braucht sie nicht — es erkennt selbst und arbeitet unabhaengig davon. Du kannst sie in Frigate ausschalten, wenn du sie sonst nicht nutzt.",
    "ui.hinweis.x_tooltip": "Diesen Hinweis nicht mehr anzeigen",
    "ui.hinweis.x_aria": "Hinweis dauerhaft ausblenden",
    "setupwiz.frigate.status_ok": "✓ Verbunden — {n} Kamera(s) gefunden",
    "setupwiz.frigate.status_fehl": "✗ Frigate nicht erreichbar: {fehler}",
    "setupwiz.frigate.status_fehl_keine": "keine Kameras",
    "setupwiz.frigate.status_fehl_hinweis":
        "Korrigiere die URL (oder setze FRIGATE_URL in deiner .env / "
        "docker-compose) und teste erneut.",
    "setupwiz.frigate.status_leer":
        "Gib deine Frigate-URL ein und teste die Verbindung.",
    "setupwiz.frigate.titel": "Mit Frigate verbinden",
    "setupwiz.frigate.satz":
        "suslik liest deine Kameras direkt aus der Frigate-API "
        "(meist Port 5000). Keine Kamera ist fest verdrahtet.",
    "setupwiz.frigate.knopf_test": "Verbindung testen",
    "setupwiz.kameras.titel": "Kameras &amp; Bedingungen wählen",
    "setupwiz.kameras.satz":
        "Hake an, welche Kameras beobachtet werden sollen; hake eine oder "
        "mehrere Zonen an, um nur Events zu analysieren, die diese Zonen "
        "betreten haben (z. B. Person im Garten). Nichts angehakt = alle "
        "Events.",
    "setupwiz.kameras.satz_ohne":
        "Verbinde dich zuerst mit Frigate — deine Kameras erscheinen hier.",
    "setupwiz.backend.titel": "Beschleunigung",
    "setupwiz.backend.verfuegbar": "Auf dieser Maschine verfügbar:",
    "setupwiz.backend.satz_wahl": "Wähle eines aus — CPU funktioniert immer.",
    "setupwiz.import.titel": "Gesichter aus Frigate importieren",
    "setupwiz.import.zahl_vor": "Frigate hat bereits ",
    "setupwiz.import.zahl_mitte": " Referenzbild(er) von ",
    "setupwiz.import.zahl_nach": " Person(en).",
    "setupwiz.import.satz":
        "Importiere sie, damit suslik alle von Anfang an erkennt. Die "
        "Bilder sind schnell heruntergeladen, danach berechnet suslik "
        "eigene Gesichtsmerkmale auf deinem Beschleuniger (GPU/NPU).",
    "setupwiz.import.knopf": "{n} Gesichter aus Frigate importieren",
    "setupwiz.import.satz_leer":
        "Noch keine Gesichter in Frigate. Hinweis: suslik braucht "
        "mindestens ein Referenzgesicht, bevor es jemanden erkennen kann "
        "— importiere hier aus Frigate oder lade später Fotos auf der "
        "Seite Bekannte Personen hoch.",
    "setupwiz.import.satz_ohne":
        "Verbinde dich zuerst mit Frigate — danach kannst du seine "
        "bekannten Gesichter hier importieren.",
    "setupwiz.fertig.knopf": "Speichern &amp; suslik starten",
    "setupwiz.fertig.satz":
        "Speichert deine Auswahl und startet den Dienst einmal neu.",
    "setupwiz.restore.titel": "Schon eine Konfiguration vorhanden?",
    # "System → Konfigurations-Backup" zitiert system.titel +
    # system.backup.titel (Tranche C) WOERTLICH — Zitat-Folge, bei
    # Aenderungen dort hier nachziehen (en.py-Abschnittskopf Tranche C).
    "setupwiz.restore.satz":
        "Wenn du schon einmal eine suslik-Konfiguration exportiert hast "
        "(System → Konfigurations-Backup), lade sie hier, um alle "
        "Einstellungen wiederherzustellen und den Assistenten zu "
        "überspringen.",
    "setupwiz.restore.knopf": "Konfigurationsdatei laden…",
    "setupwiz.write.titel": "Zurückschreiben nach Frigate?",
    "setupwiz.write.satz":
        "suslik kann seine Urteile nach Frigate zurückschreiben "
        "(sub_labels) und Referenzen spiegeln, damit beide parallel laufen "
        "können. Nur-Lesen ist der sichere Standard.",
    "setupwiz.write.opt_ro":
        "Nur-Lesen (empfohlen) — suslik schreibt nie nach Frigate",
    "setupwiz.write.opt_rw": "Zurückschreiben nach Frigate (Parallelbetrieb)",
    "setupwiz.willkommen.titel": "Willkommen bei suslik",
    "setupwiz.willkommen.satz":
        "Eine kurze geführte Einrichtung — oder lade eine bestehende "
        "Konfiguration, um den Assistenten zu überspringen. Alles hier "
        "lässt sich später auf den normalen Seiten ändern.",
    "leer.passe_area_heute":
        "Heute noch kein Durchgang im Bereich {area}.",
    "leer.passe_area_tag":
        "An diesem Tag kein Durchgang im Bereich {area}.",
    # "All" ist zugleich Chip-Kennung (Anzeige==Kennung, §8.2) — bleibt.
    "leer.passe_area_hinweis":
        "Der All-Chip oben zeigt das ganze Grundstück.",
    "leer.passe_heute": "Heute noch keine Durchgänge mit Gesicht.",
    "leer.passe_heute_hinweis":
        "Sobald jemand über das Grundstück geht, erscheint der Durchgang "
        "hier.",
    "leer.tag": "Nichts mit Gesicht an diesem Tag.",
    "leer.tag_hinweis":
        "Blättere mit den Pfeilen zu einem anderen Tag, oder öffne Events "
        "für die vollständige Liste.",
    "leer.frigate": "Noch kein Frigate verbunden.",
    "leer.frigate_hinweis":
        "Trage deine Frigate-URL im Einrichtungsassistenten ein "
        "(Seite System) — dann erscheinen Durchgänge hier automatisch.",
    "leer.refs":
        "Verbunden — aber noch keine Referenzgesichter, deshalb kann "
        "niemand erkannt werden.",
    "leer.refs_hinweis":
        "Importiere Gesichter aus Frigate oder lade Fotos hoch — beides "
        "auf der Seite Bekannte Personen. suslik lernt danach von selbst "
        "aus den Kameras weiter.",
    "leer.band_heute": "Heute noch nichts mit Gesicht.",
    "leer.band_tag": "Nichts mit Gesicht an diesem Tag.",
    "leer.band_hinweis":
        "Personen erscheinen hier, sobald ein Durchgang analysiert ist.",
    "leer.person_unbekannt": "Person unbekannt.",
    "leer.kamera_unbekannt": "Unbekannte Kamera.",
    "leer.kamera_unbekannt_hinweis":
        "Kacheln kommen nur aus Frigates Kameraliste und von "
        "gespeicherten Wächtern.",
    "unbekannte.name": "Unbekannt {nummer}",
    "unbekannte.badge_eine": "eindeutig eine Person",
    "unbekannte.badge_aehnlich": "Ähnlichkeit {wert}",
    "unbekannte.badge_einmal": "einmal gesehen",
    "unbekannte.meta_zeit": " Auftritte · {zeit}",
    "unbekannte.knopf_reaktivieren": "wieder aktivieren",
    "unbekannte.attr_name": "Name (neu oder bestehend)",
    "unbekannte.knopf_zuweisen": "Person zuweisen",
    "unbekannte.knopf_ignorieren": "Ignorieren",
    "unbekannte.opt_merge": "zusammenführen mit…",
    "unbekannte.knopf_ok": "OK",
    "unbekannte.badge_gleiche": "dieselbe Person?",
    "unbekannte.knopf_merge": "Zusammenführen",
    "unbekannte.knopf_verschieden": "Getrennt lassen",
    "unbekannte.titel": "Unbekannte",
    "unbekannte.kopf_satz":
        "Gesichter ohne bekannten Treffer, gruppiert zu wiederkehrenden "
        "Identitäten.",
    "unbekannte.kopf_satz_zuweisen":
        " verknüpft eine Kachel mit einer Person (neu oder bestehend, den "
        "Namen eintippen),",
    "unbekannte.kopf_satz_ignorieren":
        " schaltet einen bekannten Fremden stumm (keine Meldung).",
    "unbekannte.kopf_satz_auto":
        "Neue Gesichter werden nach jedem Durchgang automatisch "
        "gesammelt.",
    "unbekannte.knopf_reorg": "Jetzt neu gruppieren",
    "unbekannte.hinweis_reorg":
        "prüft die gesammelten Gesichter noch einmal und baut die Gruppen "
        "neu auf — das Sammeln selbst läuft automatisch (1–2 min)",
    "unbekannte.h_wieder": "Wiederkehrende",
    "unbekannte.h_einzeln": "{n} einzelne Auftritte (bisher einmal gesehen)",
    "unbekannte.h_besucher": "{n} bekannte Besucher (stummgeschaltet)",
    "unbekannte.h_objekte":
        "{n} statische Objekte (automatisch erkannt — keine Personen)",
    "unbekannte.satz_objekte":
        "Gruppen, deren Bilder untereinander fast identisch sind und "
        "keiner Person ähneln — typischerweise ein Radkasten, ein "
        "Pflasterstein oder ein Lichtmuster, das der Detektor immer "
        "wieder für ein Gesicht hält. Sie sind eingefroren: Neue Funde "
        "landen nie hier (sie bilden frische, sichtbare Gruppen und "
        "werden nach derselben Regel neu geprüft) — die Gruppen bleiben "
        "gelistet, damit nichts versteckt wird.",
    "unbekannte.leer": "Noch keine unbekannten Gesichter gesammelt.",
    "unbekannte.leer_hinweis":
        "Identitäten erscheinen hier nach dem nächsten unbekannten "
        "Besucher.",
    "livealerts.link_video": "&#9654; Video {n}",
    "livealerts.person_unbekannt": "unbekannt",
    "livealerts.trigger.eins": "{n} Trigger",
    "livealerts.trigger.viele": "{n} Trigger",
    "livealerts.kanal_keiner": "nicht gesendet (kein Kanal)",
    "livealerts.keine_bilder": "keine gespeicherten Bilder",
    "livealerts.titel": "Live-Wächter-Meldungen",
    "livealerts.kopf.auftritte.eins": "{n} Auftritt",
    "livealerts.kopf.auftritte.viele": "{n} Auftritte",
    "livealerts.kopf.satz":
        " am {tag} — Schnellprüfung, vorläufig; das bestätigte Urteil "
        "kommt aus der normalen Analyse.",
    "livealerts.kopf.satz_alt":
        "Zu Einträgen vor 0.1.0.190 sind weder Bild noch Name "
        "gespeichert.",
    "livealerts.leer": "Keine Live-Meldungen an diesem Tag.",
    "video.fehl":
        "&#9888; Transcoding fehlgeschlagen — siehe Dienst-Log (/log).",
    "video.fehl_hinweis":
        "Lade die Seite neu, um es erneut zu versuchen, oder öffne den "
        "Original-Clip:",
    "video.warte": "Browser-Video (H.264) wird vorbereitet&nbsp;…",
    "video.warte_satz":
        "Diese Seite aktualisiert sich von selbst. Die Kopie wird einmal "
        "erstellt und dann zwischengespeichert.",
    "event.ours_zeile.eins": "{person} — {stufe} (in {n} Fenster gesehen)",
    "event.ours_zeile.viele": "{person} — {stufe} (in {n} Fenstern gesehen)",
    "event.ours_keiner": "kein Treffer zu irgendeiner Person",
    "event.ours_rest.eins": " · {n} weitere Person: kein Treffer",
    "event.ours_rest.viele": " · {n} weitere Personen: kein Treffer",
    "event.grenze":
        "unter dieser Linie: schwache Treffer (bester Score &lt; {wert}) "
        "— der Name ist geraten, das kann eine andere Person sein",
    "event.gruppe_ohne": "Ohne Zuordnung",
    "event.badge_unsicher": "unsicher",
    "event.leer_crops":
        "Zu diesem Event sind keine Gesichtsausschnitte gespeichert.",
    "event.knopf_video": "&#9654; Video",
    "event.knopf_log": "Analyse-Log",
    "event.attr_unvollstaendig":
        "Clip unvollständig — {gelesen}/{soll} Frames gelesen; aus dem "
        "lesbaren Teil beurteilt",
    "event.badge_unvollstaendig": "⚠ Clip unvollständig",
    "event.pass_zurueck": "&#8592; voriges",
    "event.pass_weiter": "nächstes &#8594;",
    "event.pass_teil": "Teil eines Durchgangs",
    "event.pass_events.eins": "{n} Event",
    "event.pass_events.viele": "{n} Events",
    "event.pass_knopf": "Durchgang ansehen",
    "event.label_grund": "Fehlergrund",
    "event.grund_ohne_zeile":
        "analyze.log enthält keine Zeile mit dem Grund — nutze den "
        "Log-Knopf unten",
    "event.grund_ohne_log":
        "zu diesem Event ist kein analyze.log abgelegt — siehe Dienst-Log "
        "(Seite System)",
    "event.zurueck": "← Heute",
    "event.label_korrektur": "Korrigieren, falls falsch",
    "event.label_wer": "Wer war das?",
    "event.h_bilder": "Bilder",
    # ---- Routen-Seiten (Stufe 2, Tranche C) ----
    # Uebersetzung 20.08.2026 (begriffe_tabellen.md, DE-Abschnitt);
    # Kontext + Stufe-2-Grenzen: siehe en.py-Abschnittskopf.
    # --- routes/system.py ---
    "system.ampel.service": "Dienst",
    "system.ampel.service_info": "verarbeitet (gesamt): {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — Selbstcheck OK",
    "system.ampel.backend_fail":
        "{backend} — {n} Selbstcheck(s) FEHLGESCHLAGEN, siehe Dienst-Log",
    "system.ampel.analyse": "Analyse",
    "system.ampel.analyse_dauer": "letzte Dauer {s} s",
    "system.ampel.analyse_nie": "noch keine Analyse",
    "system.ampel.retry": "Wiederholungen",
    "system.ampel.retry_info":
        "{offen} offen / {aufgegeben} aufgegeben (Fenster {tage} d)",
    "system.ampel.frigate_unkonfiguriert":
        "noch nicht eingerichtet — trage die URL im "
        "Einrichtungsassistenten ein",
    "system.ampel.frigate_ok": "erreichbar",
    # {zeit} kommt vorformatiert (%H:%M) aus der Route (B19-Stufe).
    "system.ampel.frigate_fehler": "letzter Fehler {zeit}",
    # {s} vorformatiert (:.0f) — Formatspezifika nie in Werte (§8.8).
    "system.ampel.mqtt_hb": "Heartbeat vor {s} s",
    "system.ampel.mqtt_kein_hb": "noch kein Heartbeat",
    "system.ampel.mqtt_pub_aus": "eingerichtet, Publizieren aus",
    "system.ampel.mqtt_pub_kaputt":
        "eingerichtet, Publisher nicht gestartet — siehe Dienst-Log",
    "system.ampel.mqtt_unkonfiguriert": "nicht eingerichtet",
    "system.ampel.disk": "Speicherplatz",
    "system.ampel.disk_info2": "{gb} GB frei · Clip-Cache {cache} GB von {max} GB",
    "system.disk.titel": "Speicherplatz",
    "system.disk.satz": "Clips sind ein Cache: {tage} Tage aufbewahrt, gedeckelt auf {max} GB, und ausgedünnt, sobald weniger als {min} GB frei sind (geprüft nach jedem Event und einmal täglich von einer Speicherplatz-Wache, die bei wenig freiem Platz auf alle 10 Minuten umschaltet).",
    "system.disk.knopf": "Jetzt aufräumen",
    "system.disk.warnung": "Nur noch {gb} GB frei und der Clip-Cache ist schon leer — Platz auf dem Datenvolume schaffen, sonst können neue Events nicht gespeichert werden.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "PRÜFEN",
    "system.drift.banner":
        "DRIFT-PRÜFUNG ROT nach der zuletzt hinzugefügten Referenz:",
    "system.sync.titel": "Abgleich mit Frigate",
    "system.sync.knopf": "Frigate-Abgleich öffnen",
    "system.sync.satz":
        "Die Abgleich-Seite vergleicht beide Seiten Person für Person und "
        "sortiert jedes Referenzbild nach seinem Zustand, unterzieht jeden "
        "Kandidaten derselben Vorprüfung wie Frigate, sendet nur, was du "
        "anhakst, und importiert, was nur Frigate hat.",
    "system.sync.fehlt":
        "noch nicht verfügbar — braucht ein erreichbares Frigate und "
        "mindestens ein Referenzgesicht",
    "system.qc.titel": "Qualitätsbericht",
    "system.qc.stand": "(Stand {stand}, {tage} Tage)",
    "system.qc.kopf_gesicht": "mit Gesicht",
    "system.qc.kopf_bestaetigt": "bestätigt",
    "system.qc.kopf_quote": "Quote im Fenster",
    # WIRD ZITIERT: setupwiz.restore.satz nennt diesen Titel woertlich
    # ("System → Konfigurations-Backup") — bei Aenderung dort nachziehen.
    "system.backup.titel": "Konfigurations-Backup",
    "system.backup.satz":
        "Lade die in /data/config gespeicherten Einstellungen als eine "
        "JSON-Datei herunter, oder stelle sie aus so einer Datei wieder "
        "her. Ehrlicher Umfang: Das ist derzeit das KAMERA-BLATT (inkl. "
        "seiner gespeicherten Werte); Schwellen/Kanäle, die nur in "
        "verifyd.yaml oder über Umgebungsvariablen gesetzt sind, stehen "
        "NICHT in dieser Datei. Gelernte Personen/Referenzen: nimm das "
        "Voll-Backup unten.",
    "system.backup.knopf_download": "Konfiguration herunterladen",
    "system.backup.knopf_restore": "Aus Datei wiederherstellen…",
    "system.backup.careful": "Achtung:",
    # {hinweis} = core.registry.VISION_EXPORT_HINWEIS (zentrale Quelle).
    "system.backup.careful_config":
        "diese Datei {hinweis} (Meldekanäle und Vision-Erkennung), damit "
        "eine Wiederherstellung auf einer anderen Maschine wirklich "
        "funktioniert.",
    "system.backup.restore_satz":
        "Wiederherstellen überschreibt die aktuellen Einstellungen (die "
        "vorherigen bleiben als .bak erhalten) und startet den Dienst "
        "neu.",
    "system.voll.titel": "Voll-Backup",
    "system.voll.satz":
        "Ein portables Archiv mit allem, was du dieser Installation "
        "beigebracht hast: Einstellungen, die Gesichts-Referenzen, "
        "Lernlauf-Ergebnisse, das ganze Material der Personenerkennung "
        "(Bilder, deine Urteile aus der Durchsicht, trainierte Modelle) "
        "und das Event-Protokoll. Gemacht für den Umzug auf eine andere "
        "Maschine. Ehrlicher Umfang: Der Video-Clip-Cache und die "
        "Analyse-Artefakte je Event sind NICHT enthalten — sie bauen "
        "sich mit der Zeit neu auf.",
    "system.voll.knopf_download": "Voll-Backup herunterladen",
    "system.voll.knopf_restore": "Voll-Backup wiederherstellen…",
    "system.voll.careful": "dieses Archiv {hinweis}.",
    "system.voll.restore_satz":
        "Wiederherstellen ersetzt diese Teile (jeder vorherige wird "
        "einmal als *.pre-restore-* aufbewahrt) und startet den Dienst "
        "neu. Ein Upload von ein paar hundert MB kann dauern — lass die "
        "Seite offen.",
    "system.live.titel": "Live-Wächter",
    "system.live.alerts": "Heute gesendete Meldungen: {kanaele}",
    "system.live.stoerungen": "Störungshinweise heute: {n}",
    "system.live.knopf": "Live-Wächter öffnen",
    "system.live.quelle":
        "Gezählt aus dem eigenen Melde-Log der Engine — nur Nachrichten, "
        "die ein Kanal wirklich angenommen hat. Live-Wächter-Meldungen "
        "sind getrennt von den Melde-Zählern der Event-Analyse auf der "
        "Heute-Seite.",
    "system.write.titel": "Zurückschreiben nach Frigate",
    "system.write.satz":
        "Schreibt suslik nach Frigate zurück, oder liest es nur? "
        "Nur-Lesen ist der sichere Standard; schalte das Schreiben nur "
        "für den Parallelbetrieb ein (Frigate-Gesichtserkennung + "
        "suslik).",
    "system.write.aktuell": "Aktuell:",
    "system.write.zustand_ro": "NUR-LESEN — suslik schreibt nicht nach Frigate",
    "system.write.zustand_rw": "SCHREIBT nach Frigate — sub_labels",
    "system.write.zustand_rw_sync": " + Referenz-Abgleich",
    "system.write.knopf_rw": "Schreiben aktivieren",
    "system.write.knopf_ro": "Nur-Lesen",
    # WIRD ZITIERT: setupwiz.restore.satz ("System → Konfigurations-
    # Backup"); wortgleich mit nav.system (Linktext==Seitentitel).
    "system.titel": "System",
    "system.tools.titel": "Tools",
    "system.docs.titel": "Doku",
    "system.docs.link": "Dokumentation auf GitHub",
    # --- routes/vision.py ---
    "vision.zeit.nie": "nie",
    # Seitentitel wortgleich mit nav.vision (Linktext==Seitentitel).
    "vision.titel": "Vision-Erkennung",
    "vision.kopf.dirty": "nicht gespeichert",
    "vision.hinweis.titel": "Was du dafür brauchst",
    "vision.schalter.knopf_aus": "Ausschalten",
    "vision.schalter.knopf_an": "Einschalten",
    "vision.schalter.fehlt": "Fehlt noch:",
    "vision.schalter.titel_an": "Die Vision-Erkennung ist an",
    "vision.schalter.titel_aus": "Die Vision-Erkennung ist aus",
    "vision.schalter.aus_satz":
        "Solange sie aus ist, wird nichts verschickt und kein Bild "
        "verlässt diese Maschine.",
    "vision.frage.titel": "Wie nach einem Vergleich gefragt wird",
    "vision.frage.doppel_titel":
        "Jedes Paar zweimal fragen, mit vertauschten Galerien",
    "vision.frage.doppel_satz":
        "Das ist die Positions-Probe. A im ersten und B im getauschten "
        "Lauf meinen DIESELBE Galerie — ein Widerspruch entlarvt also "
        "ein Modell, das schlicht bevorzugt, was zuerst kommt. Hier "
        "gemessen: Jede falsche Antwort über alle unsere Testreihen war "
        "ein &bdquo;A&ldquo;, nie ein &bdquo;B&ldquo;. Abschalten "
        "halbiert die Anfragen &mdash; ein Vergleich ruht dann aber auf "
        "einer einzigen Antwort, ohne eine zweite, die sie bestätigen "
        "oder widerlegen könnte.",
    "vision.meld.titel": "Zusätzliche Meldungen",
    "vision.meld.satz":
        "Beide sind aus, solange du sie nicht einschaltest, und keine "
        "ändert die bestehenden Meldungen: Vision kann keine auslösen, "
        "keine zurückziehen und weder den Gesichts- noch den Körperpfad "
        "überstimmen.",
    "vision.meld.judged_titel":
        "Sag mir, wenn ein Durchgang beurteilt wurde",
    "vision.meld.judged_satz":
        "Eine kurze Notiz über deine üblichen Kanäle, sobald das Urteil "
        "steht &mdash; mit der echten Voten-Zahl. Sie kommt, nachdem der "
        "Durchgang vorbei ist; bei einem lokalen Modell kann das Minuten "
        "später sein. Information, nichts Dringendes.",
    "vision.meld.alarm_titel":
        "Melde dich, wenn Vision der Körpererkennung widerspricht",
    "vision.meld.alarm_satz":
        "Löst nur aus, wenn wirklich ein Lauf stattgefunden hat, das Modell "
        "geantwortet hat und trotzdem niemanden bestätigt hat. Es bleibt "
        "still, wenn schlicht nicht genug Material da war &mdash; das "
        "wäre Rauschen. Angelernte Personen wiederzuerkennen ist die "
        "starke Seite dieses Wegs, deshalb bedeutet eine "
        "Nicht-Bestätigung etwas; Fremde abzuweisen ist die schwache "
        "Seite, deshalb gibt Vision in diese Richtung nie ein Votum ab.",
    "vision.kachel.was_key": "du trägst einen API-Key ein",
    "vision.kachel.was_host": "du trägst Host und Port ein",
    "vision.kachel.was_url": "du trägst eine URL und optional einen Key ein",
    "vision.kachel.titel": "Wo das Modell läuft",
    "vision.kachel.satz":
        "Wähle einen Anbieter. Bei den drei benannten ist die offizielle "
        "API-Adresse schon eingebaut &mdash; du trägst nur deinen Key "
        "ein. Es wird nichts verschickt, bis du selbst einen Knopf "
        "drückst.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; gespeichert &mdash; leer lassen, um ihn "
        "zu behalten",
    "vision.verb.key_pflicht_ph": "füge hier deinen Key ein",
    "vision.verb.key_frei_ph": "nur falls dein Server einen verlangt",
    "vision.verb.host": "Host",
    "vision.verb.host_ph": "der Name oder die Adresse der Maschine",
    "vision.verb.port": "Port",
    "vision.verb.host_satz":
        "Nur die Maschine &mdash; den Rest der Adresse ergänzt suslik "
        "selbst. Der Beispiel-Port ist der, den llama.cpp standardmäßig "
        "nutzt; nimm den, auf dem deiner lauscht.",
    "vision.verb.endpunkt": "Endpunkt-URL",
    "vision.verb.endpunkt_satz":
        "Das ist ein Beispiel für einen OpenAI-kompatiblen Endpunkt "
        "&mdash; ersetze ihn durch deinen, wenn du einen anderen Anbieter "
        "nutzt.",
    "vision.verb.betriebsart": "Dieser Endpunkt ist",
    "vision.verb.betriebsart_extern": "im Internet",
    "vision.verb.betriebsart_lokal": "in meinem eigenen Netz",
    "vision.verb.adresse": "API-Adresse",
    "vision.verb.adresse_satz":
        "Fest eingebaut &mdash; hier kann man nichts falsch tippen.",
    "vision.verb.key": "API-Key",
    "vision.verb.key_frei_satz":
        "Hier optional &mdash; die meisten lokalen Server verlangen "
        "keinen. Drück den Knopf trotzdem: Er holt auch die Liste der "
        "Modelle, die dein Server hat.",
    "vision.verb.titel": "Verbindung",
    "vision.modell.titel": "Modell",
    "vision.modell.verweigert": "der Endpunkt hat die Verbindung verweigert",
    # {zeit} vorformatiert aus _zeit() — das Format bleibt in der Route (B19).
    "vision.modell.geprueft": "Geprüft {zeit} gegen",
    "vision.modell.opt_wahl": "&mdash; bitte wählen &mdash;",
    "vision.modell.ungetestet": "hier ungetestet",
    "vision.modell.opt_verschollen":
        " — früher gespeichert, der Endpunkt listet es gerade nicht",
    "vision.modell.wahl_satz":
        "Wähle eines aus der Liste &mdash; die Anmerkung neben jedem "
        "Namen ist von uns, die Namen sind die des Endpunkts.",
    "vision.modell.verschollen_satz":
        "Dieses Modell ist gespeichert und weiter in Gebrauch, aber der "
        "Endpunkt hat es diesmal nicht gelistet. Prüfe den Namen, oder "
        "wähle eines aus der Liste.",
    "vision.modell.fremde_plattform": "auf einer anderen Plattform gemessen",
    "vision.modell.kein_rohergebnis": "kein Rohergebnis dazu archiviert",
    "vision.modell.gemessen": "gemessen {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "Hier nicht gemessen &mdash; das ist kein Urteil, nur "
        "Ehrlichkeit. Führe den Verbindungstest unten aus, bevor du dich "
        "darauf verlässt.",
    "vision.modell.manuell": "Modell-ID von Hand",
    "vision.modell.manuell_ph": "exakte Modell-ID",
    "vision.modell.manuell_knopf": "Diese ID prüfen",
    "vision.modell.manuell_satz":
        "Für Endpunkte, die nicht alles listen: Die ID wird zuerst mit "
        "einer winzigen Text-Anfrage geprüft; ungeprüft lässt sich "
        "nichts speichern.",
    "vision.prompt.standard_satz":
        "Das ist der gemessene Standard-Wortlaut. Solange du ihn genau "
        "so lässt, werden Urteile nicht als angepasst markiert.",
    "vision.prompt.titel": "Die Frage, die suslik stellt",
    "vision.prompt.satz":
        "Du kannst den Wortlaut ändern. Der letzte Absatz ist fest: Er "
        "ist die Ein-Wort-Anweisung, an der der Antwort-Parser hängt, "
        "und er ist das, was gemessen wurde.",
    "vision.prompt.knopf_zurueck": "Auf Standard zurücksetzen",
    "vision.zahlen.think": "Das Denken des Modells abschalten",
    "vision.zahlen.think_satz":
        "Seit 0.1.0.211 standardmäßig an: Auf harten Vergleichs-Gittern "
        "kann sich ein denkendes Modell am Token-Budget vorbeireden, und "
        "der Lauf endet ohne Urteil. Strenge Endpunkte lehnen den "
        "Schalter ab; suslik wiederholt die Anfrage dann einmal ohne ihn "
        "und sagt es dazu.",
    "vision.zahlen.titel": "Grenzen",
    "vision.zahlen.max_tokens": "Max. Tokens je Antwort",
    "vision.zahlen.timeout": "Timeout je Anfrage (s)",
    "vision.zahlen.satz":
        "Gemessen: In einem Lauf waren 3000 Tokens zu wenig &mdash; die "
        "Antwort wurde abgeschnitten und zählte als kein Urteil, und "
        "dieselbe Frage war mit 12000 richtig. Ein lokales Modell auf "
        "einer CPU-Maschine braucht Minuten je Anfrage, ein "
        "Online-Modell Sekunden.",
    "vision.cloud.ziel_fallback": "der Endpunkt, den du oben einrichtest",
    "vision.cloud.titel": "Bilder an einen externen Dienst senden",
    "vision.cloud.satz":
        "Auf diesen Bildern sind nicht nur die Menschen, die hier "
        "wohnen: Die unsicheren Fälle sind meist Fremde &mdash; "
        "Besucher, Zusteller, Nachbarn, Passanten. Verantwortlich dafür "
        "bist du, nicht der Betreiber des Dienstes. Deine Bestätigung "
        "wird mit Zeitstempel ins Audit-Log geschrieben; der Wechsel "
        "zurück auf ein lokales Modell zieht sie zurück.",
    "vision.cloud.bestaetigung": "Ich verstehe und bestätige das",
    "vision.cloud.bestaetigt": "(bestätigt {zeit})",
    "vision.test.treffer": "{n}/2 richtig",
    "vision.test.tokens": "{ist} Tokens vs {soll}",
    "vision.test.falsch": " (falsch)",
    # WIRD ZITIERT: js.vision.dirty_text UND js.vision.prompt_zurueck
    # nennen diesen Knopf woertlich ("Verbindung speichern") — bei
    # Aenderung dort BEIDE nachziehen.
    "vision.save.knopf": "Verbindung speichern",
    "vision.save.dirty":
        "ungespeicherte Änderungen &mdash; die Erkennung nutzt weiter "
        "die gespeicherte Verbindung",
    "vision.test.titel": "Diese Verbindung testen",
    "vision.test.knopf": "Test ausführen",
    "vision.test.nicht_gelaufen": "nicht gelaufen",
    "vision.test.stufe1": "Erreichbarkeit",
    "vision.test.stufe2": "Zwangswahl",
    "vision.test.stufe3": "Token-Prüfung",
    "vision.test.ungetestet": "Noch nicht getestet.",
    "vision.test.letzter": "Letzter Lauf {zeit} gegen",
    "vision.galerien.stand_gut": "abgenommen {zeit} &middot; {zellen} Zellen",
    "vision.galerien.pruefen": "braucht einen Blick",
    "vision.galerien.keine": "noch keine Galerie",
    "vision.galerien.zu_wenig":
        "noch nicht genug abgenommene Körperbilder ({n} brauchbar)",
    "vision.galerien.knopf_auffrischen": "Auffrischen",
    # Wortgleich mit titel.vision_galerie (Linktext==Seitentitel).
    "vision.galerien.knopf_bauen": "Galerie aufbauen",
    "vision.galerien.zahl": "{n} brauchbare Bilder &middot; {reihen}",
    "vision.galerien.titel": "Galerien",
    "vision.galerien.stand":
        "{n} Galerien bereit ({min} nötig) &mdash; Vision braucht "
        "mindestens zwei, weil sie immer eine Person gegen eine andere "
        "vergleicht.",
    "vision.galerien.satz":
        "Eine Galerie können nur Personen mit gelerntem Körpermodell "
        "bekommen; die Bilder kommen aus dem Körpermaterial, das du "
        "schon abgenommen hast. Vision beurteilt immer nur Personen, die "
        "eine haben, und sagt das am Urteil dazu.",
    # --- routes/visiontest.py ---
    # Seitentitel wortgleich mit nav.erkennungstest (Linktext==Seitentitel).
    "visiontest.titel": "Erkennungstest",
    "visiontest.kopf.satz":
        "Gesicht und Person kommen aus dem, was damals festgehalten "
        "wurde &mdash; nichts wird neu berechnet. Vision läuft jetzt, "
        "über genau denselben Weg wie im Normalbetrieb.",
    # Frueher Modulkonstante KOSTEN — §8.12: t() nie auf Modulebene.
    "visiontest.kosten":
        "Ein Testlauf kostet echte Anfragen, genau wie der "
        "Normalbetrieb: Der ganze Durchgang geht als ein "
        "Kandidaten-Gitter hinein, und jedes verglichene Galerien-Paar "
        "kostet zwei Anfragen, weil jede Frage mit vertauschten Galerien "
        "noch einmal gestellt wird. Er zählt als manueller Klick und "
        "geht deshalb nicht aufs Tageslimit &mdash; auf einem bezahlten "
        "Endpunkt ist das aber Geld, und auf einem lokalen CPU-Modell "
        "dauert es Minuten.",
    "visiontest.wer.niemand": "niemand erkannt",
    # EN-Klammerformen bleiben EINE Form je Schluessel (§8.18) — im
    # Deutschen als Klammer-Plural, wo die Endung es hergibt.
    "visiontest.wahl.kachel_zahlen":
        "{events} Events &middot; {kameras} Kamera(s)",
    "visiontest.wahl.vision_fertig": " &middot; Vision gelaufen",
    "visiontest.wahl.titel": "1 &middot; Welcher Durchgang",
    "visiontest.wahl.leer":
        "Noch keine Durchgänge vorhanden. Sobald jemand über das "
        "Grundstück geht, erscheint der Durchgang hier.",
    "visiontest.wahl.kopf_zahlen":
        "{events} Event(s) &middot; {kameras} Kamera(s)",
    "visiontest.wahl.anderer": "anderen Durchgang wählen",
    "visiontest.wahl.titel_offen": "1 &middot; Durchgang wählen",
    "visiontest.wahl.anzahl": "{n} jüngste Durchgänge",
    "visiontest.wahl.satz":
        "Die jüngsten Durchgänge, gruppiert genau wie auf der "
        "Heute-Seite.",
    "visiontest.gesicht.kein_match": "kein Treffer",
    "visiontest.gesicht.gezeigt": "zeige {gezeigt} von {gesamt} Bild(ern)",
    "visiontest.gesicht.ohne_bild":
        "zu {fehlt} der {unbek} Event(s) ohne Treffer ist kein Bild "
        "gespeichert",
    "visiontest.gesicht.kein_bild":
        "zu diesem Durchgang ist kein Gesichtsbild gespeichert",
    "visiontest.gesicht.keines": "kein bekanntes Gesicht",
    "visiontest.gesicht.zeile": "{person} &middot; {events} Event(s)",
    # {best} vorformatiert (:.2f) aus der Route (§8.8).
    "visiontest.gesicht.best": " &middot; bester Score {best}",
    "visiontest.gesicht.unbekannt":
        "{n} Event(s) mit Gesicht ohne Treffer",
    "visiontest.gesicht.titel": "Gesicht",
    "visiontest.gesicht.quelle":
        "Embedding-Vergleich gegen deine Referenzgesichter &mdash; aus "
        "dem Protokoll dieses Durchgangs",
    "visiontest.koerper.kandidaten":
        "Kandidaten, keiner erfüllt die Regel: {liste}",
    "visiontest.koerper.nichts": "nichts beurteilt",
    "visiontest.koerper.zeile":
        "{klasse} &middot; Score {score} von {schwelle} &middot; {quelle}",
    "visiontest.koerper.bild_weg": "Bild abgelaufen",
    "visiontest.koerper.titel": "Person",
    "visiontest.koerper.quelle":
        "DINOv2-Embedding + Klassifikator auf den beurteilten Bildern "
        "dieses Durchgangs",
    "visiontest.log.warte":
        "warte auf das Modell &mdash; diese Seite aktualisiert sich von "
        "selbst",
    "visiontest.log.titel": "Was passiert ist",
    "visiontest.gitter.alt": "das Kandidaten-Gitter dieses Laufs",
    "visiontest.gitter.bildunterschrift":
        "das Bild, das dem Modell wirklich gezeigt wurde",
    "visiontest.gitter.zeile":
        "Kandidaten-Gitter: {n} Zelle(n) aus diesem Durchgang, als EIN "
        "Bild abgefragt",
    "visiontest.gitter.luecken": " ({n} Zelle(n) leer gelassen)",
    "visiontest.runden.kein_votum": "kein Votum &mdash; {grund}",
    "visiontest.runden.paar": "{a} vs {b}",
    "visiontest.nach.laeuft": "Dieser Durchgang wird neu analysiert",
    "visiontest.nach.stand":
        "{fertig} von {gesamt} Events fertig &mdash; die beurteilten "
        "Bilder werden dabei mit eingesammelt, das dauert ein paar "
        "Minuten. Es bleibt still: keine Meldungen, nichts geht raus. "
        "Diese Seite aktualisiert sich von selbst.",
    "visiontest.nach.titel": "Zu diesem Durchgang ist nichts gespeichert",
    "visiontest.nach.satz":
        "Eine erneute Analyse bringt die beurteilten Bilder zurück "
        "&mdash; und füllt damit alle drei Wege, nicht nur Vision. Sie "
        "lässt die normale Analyse noch einmal über die Events dieses "
        "Durchgangs laufen: still, ohne Meldungen, und sie wartet auf "
        "die Live-Erkennung, statt sie beiseitezudrängen.",
    "visiontest.nach.knopf": "Diesen Durchgang erneut analysieren",
    "visiontest.felder.zellen": "Gitterzellen für diesen Lauf",
    "visiontest.felder.voten": "nötige Bestätigungen für diesen Lauf",
    "visiontest.felder.doppel": "jedes Paar zweimal fragen (Tausch-Probe)",
    "visiontest.felder.satz":
        "Alle drei gelten nur für DIESEN Lauf &mdash; nichts wird "
        "gespeichert, und der Normalbetrieb behält seine eigenen "
        "Einstellungen. Dieser Durchgang hat {material} brauchbare(s) "
        "Bild(er) &mdash; mehr Zellen anzufragen ist in Ordnung, das "
        "Gitter wird dann nur kleiner. {galerien} abgenommene Galerien "
        "erlauben höchstens {voten_max} Vergleich(e). Mit "
        "eingeschalteter Tausch-Probe kostet ein Vergleich zwei "
        "Anfragen; ohne sie eine &mdash; er ruht dann aber auf einer "
        "einzigen Antwort.",
    "visiontest.laeufe.abgebrochen": "abgebrochen (Dienst neu gestartet)",
    "visiontest.laeufe.kein_urteil": "kein Urteil",
    "visiontest.laeufe.von": "von {n}",
    "visiontest.laeufe.ohne_tausch": "ohne Tausch",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} offen",
    "visiontest.laeufe.titel": "Läufe auf diesem Durchgang",
    "visiontest.laeufe.kopf_wann": "wann",
    "visiontest.laeufe.kopf_zellen": "Zellen",
    "visiontest.laeufe.kopf_noetig": "nötig",
    "visiontest.laeufe.kopf_backend": "Backend",
    "visiontest.laeufe.kopf_urteil": "Urteil",
    "visiontest.laeufe.kopf_voten": "Voten",
    "visiontest.laeufe.kopf_anfragen": "Anfr.",
    "visiontest.laeufe.kopf_zeit": "Zeit",
    "visiontest.laeufe.satz":
        "Neueste zuerst. Nur, was wirklich lief &mdash; die Liste kommt "
        "aus dem eigenen Log dieses Durchgangs und verschwindet mit ihm.",
    "visiontest.vision.titel": "Vision",
    "visiontest.vision.quelle_kurz":
        "ein Vision-Modell, das diesen Durchgang gegen deine Galerien "
        "vergleicht",
    "visiontest.vision.unkonfiguriert": "nicht eingerichtet",
    "visiontest.vision.attr_nichts": "es gibt noch nichts zu vergleichen",
    "visiontest.vision.knopf": "Vision auf diesem Durchgang ausführen",
    "visiontest.vision.nichts_satz":
        "noch nichts zu vergleichen &mdash; analysiere diesen Durchgang "
        "zuerst erneut (Knopf oben)",
    "visiontest.vision.laeuft_satz":
        "ein Lauf ist gerade aktiv &mdash; das Log unten wächst mit",
    "visiontest.vision.startet": "startet &mdash; noch nichts gemeldet",
    "visiontest.vision.quelle":
        "Zwangswahl gegen deine Galerien: Der ganze Durchgang geht als "
        "EIN Kandidaten-Gitter hinein, und jedes Paar wird zweimal "
        "gefragt, mit vertauschten Galerien",
    "visiontest.vision.nicht_gelaufen": "für diesen Durchgang nicht gelaufen",
    "visiontest.vision.verglichen":
        "verglichen: {a} gegen {b} &mdash; über alle anderen sagt es "
        "nichts",
    "visiontest.vision.abgebrochen":
        "Lauf abgebrochen &mdash; der Dienst hat neu gestartet",
    "visiontest.vision.kein_urteil": "kein Urteil &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten} von {bilder} Vergleich(en) gaben eine Antwort &middot; "
        "{anfragen} Anfragen &middot; {dauer} s &middot; Lauf {zeit}",
    "visiontest.vision.reihenfolge": " &middot; Reihenfolge: {quelle}",
    "visiontest.vision.custom_prompt": " &middot; angepasster Wortlaut",
    "visiontest.drei.titel": "2 &middot; Was die drei Wege sagen",
    "visiontest.drei.satz":
        "Derselbe Durchgang, drei unabhängige Urteile. Sie dürfen sich "
        "widersprechen &mdash; genau darum geht es, wenn man sie "
        "zusammen ansieht.",
    # --- routes/visionwizard.py ---
    "visionwizard.schritt.person": "Person wählen",
    "visionwizard.schritt.groesse": "Größe wählen",
    "visionwizard.schritt.vorschlag": "Vorschlag prüfen",
    "visionwizard.schritt.abnahme": "abnehmen",
    # Seitentitel wortgleich mit titel.vision_galerie und
    # vision.galerien.knopf_bauen (Linktext==Seitentitel).
    "visionwizard.titel": "Galerie aufbauen",
    "visionwizard.kopf.satz":
        "Eine Galerie ist ein kleines Bild-Raster einer Person &mdash; "
        "damit vergleicht das Vision-Modell ein neues Bild. Sie wird "
        "aus Körperbildern gebaut, die du schon abgenommen hast; nichts "
        "Neues wird aufgenommen und kein Video geöffnet.",
    "visionwizard.person.stand_gut": "Galerie abgenommen {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} brauchbare Bilder &mdash; noch nicht genug für eine "
        "Galerie. Führe den Personen-Lernlauf über mehr Durchgänge aus.",
    "visionwizard.person.max_gitter":
        "größtes Gitter, das dieses Material trägt: {n}",
    "visionwizard.person.titel": "1 &middot; Welche Person",
    "visionwizard.person.satz":
        "Hier erscheinen nur Personen mit gelerntem Körpermodell, und "
        "die Zahlen sind die Bilder, die den Größenfilter bestehen "
        "(mindestens 350 Pixel hoch) &mdash; nicht alles, was je "
        "gesammelt wurde.",
    "visionwizard.groesse.zellen": "{n} Zellen",
    "visionwizard.groesse.titel": "2 &middot; Wie viele Bilder",
    "visionwizard.zelle.leer":
        "keine weiteren Bilder für diese Reihe &mdash; und auch nichts "
        "mehr zum Ausleihen",
    # {reihe} traegt die (noch englischen) REIHEN_ANZEIGE-Woerter —
    # Wortlaut wie js.vw.geliehen.
    "visionwizard.zelle.geliehen": "aus der Reihe {reihe}",
    "visionwizard.zelle.knopf_weg": "passt nicht",
    "visionwizard.reihe.geliehen":
        "{n} aus einer anderen Ansicht aufgefüllt &mdash; es gab nicht "
        "genug saubere Bilder der Reihe {reihe}",
    "visionwizard.reihe.luecken": "{n} Zelle(n) ließen sich gar nicht füllen",
    "visionwizard.reihe.spreizung": "{tage} Tag(e), {kameras} Kamera(s)",
    "visionwizard.reihe.kopf": "Ansicht {reihe}",
    "visionwizard.reihe.eigene": "{eigene} von {gesamt} aus dieser Ansicht",
    "visionwizard.vorschlag.abgelehnt":
        "{n} früher von dir aussortierte(s) Bild(er) bleiben gemerkt und "
        "kommen nicht wieder.",
    "visionwizard.vorschlag.titel": "3 &middot; Passt das?",
    "visionwizard.vorschlag.grenze":
        "Ehrliche Grenze: Das sind Messungen am Bild, nicht am Moment. "
        "Ein Bild, auf dem sich jemand die Haare bindet oder bückt, "
        "sieht für jede dieser Messungen gut aus &mdash; dafür sind "
        "deine Augen da.",
    "visionwizard.vorschlag.knopf": "Diese Galerie abnehmen",
    "visionwizard.vorschlag.kopie_satz":
        "Die Abnahme kopiert diese Bilder in den Galerie-Ordner. Ab dann "
        "ist die Galerie fest: Ein später gelöschtes Original kann keine "
        "Löcher hineinreißen &mdash; suslik bittet dich nur, sie erneut "
        "abzunehmen.",
    "visionwizard.fertig.geliehen": " &middot; ausgeliehen",
    "visionwizard.fertig.titel": "Abgenommene Galerie",
    "visionwizard.fertig.stand": "{zellen} Zellen, abgenommen {zeit}.",
    "visionwizard.fertig.satz":
        "Das sind Kopien im Galerie-Ordner, mit der Herkunft jedes "
        "Bildes (Lauf, Datei, Prüfsumme) daneben. Sie wandern mit deinem "
        "Backup mit.",
    "visionwizard.fertig.knopf_neu": "Aus aktuellem Material neu aufbauen",
    "visionwizard.fertig.knopf_zurueck": "Zurück zur Vision-Erkennung",
    "visionwizard.neu.titel": "Neues Material verfügbar",
    "visionwizard.neu.satz":
        "Nichts ändert sich von selbst &mdash; die Galerie, die du "
        "abgenommen hast, bleibt genau so, bis du eine neue aufbaust und "
        "abnimmst.",
    # --- routes/personwizard.py ---
    # {wer}-Rahmen sind kasusfest gebaut (an/für + Akkusativ), damit
    # "alle bekannten Personen"/"Fremde"/Personenname überall passen.
    "personwizard.wer.alle": "alle bekannten Personen",
    "personwizard.wer.fremde": "Fremde",
    "personwizard.titel": "Personen anlernen — Körpererkennung",
    "personwizard.kopf.satz":
        "Ein zweiter, unabhängiger Erkennungsweg: Er lernt, wie eine "
        "Person als GANZES aussieht (Statur, Haare, Haltung), und "
        "erkennt Bewohner so auch, wenn kein Gesicht sichtbar ist.",
    "personwizard.kopf.wie_titel":
        "So funktioniert es — du hast das letzte Wort",
    "personwizard.kopf.schritt1":
        "1 · Du wählst, wie viele Events durchsucht werden und WER "
        "angelernt wird (eine Person oder alle bekannten Personen).",
    "personwizard.kopf.schritt2":
        "2 · Der Lauf sammelt Ganzkörper-Bilder aus deinen eigenen "
        "Aufnahmen. Ein Bild wird nur dann an eine Person gebunden, wenn "
        "ein gesichtsbestätigter Durchgang es beweist — bewusst "
        "konservativ.",
    "personwizard.kopf.schritt3":
        "3 · DU siehst jedes gesammelte Bild durch; ein Klick sortiert "
        "ein falsches aus. Ohne deine Abnahme wird nichts gelernt.",
    "personwizard.kopf.schritt4":
        "4 · Das Training läuft danach lokal in Sekunden, und eine "
        "Entscheidungsschwelle wird gemessen, damit Fremde darunter "
        "bleiben.",
    "personwizard.kopf.tempo":
        "Eine Anmerkung zum Tempo: Das Sammeln läuft derzeit auf der "
        "CPU, hab also etwas Geduld mit einem Lauf (grob 15&ndash;30 s "
        "je Event). Der Umzug auf GPU/NPU ist für eine spätere Version "
        "geplant.",
    "personwizard.kopf.warum":
        "Warum zuerst mindestens eine Person: Dieser Weg kann Personen "
        "erst auseinanderhalten, nachdem er gelernt hat — und du "
        "durchgesehen hast —, wie mindestens ein Bewohner aussieht. Bis "
        "dahin bleibt die Körpererkennung AUS und sendet nie eine "
        "Meldung. Wenn sie später meldet (Pushover/Telegram), ist die "
        "Nachricht als Personenerkennung gekennzeichnet, nicht als "
        "Gesichtserkennung.",
    "personwizard.vorb.titel": "Der Lauf wird vorbereitet &hellip;",
    "personwizard.vorb.zeile":
        "binde die letzten {n} Events über bestätigte Durchgänge an "
        "{wer}",
    "personwizard.vorb.satz":
        "Das dauert ein bis zwei Minuten — die Seite aktualisiert sich "
        "von selbst, das Sammeln startet direkt danach.",
    "personwizard.ernte.stand":
        "{events}/{von} Events · {bilder} Bilder gesammelt",
    "personwizard.ernte.startet": "startet …",
    "personwizard.ernte.titel": "Ein Personen-Lernlauf ist aktiv",
    "personwizard.ernte.zeile": "lernt gerade {wer} an · {stand}",
    "personwizard.ernte.satz":
        "Diese Seite aktualisiert sich von selbst. Ein neuer Lauf kann "
        "starten, sobald dieser fertig ist.",
    "personwizard.ernte.knopf_abbruch": "Lauf abbrechen",
    "personwizard.ernte.abbruch_hinweis": "gesammelte Bilder bleiben",
    "personwizard.unterbrochen.titel": "Der letzte Lauf wurde unterbrochen",
    "personwizard.unterbrochen.satz":
        "Vermutlich ein Dienst-Neustart. Starte unten denselben Lauf "
        "erneut — schon gesammelte Events werden automatisch "
        "übersprungen (Fortsetzen eingebaut), nichts geht verloren.",
    "personwizard.abnahme.titel":
        "Der letzte Lauf ist fertig — jetzt kommt deine Durchsicht",
    "personwizard.abnahme.zeile":
        "{n} Bilder für {wer} gesammelt (Lauf {lauf}).",
    "personwizard.abnahme.knopf": "Die Bilder jetzt durchsehen",
    "personwizard.abnahme.hinweis":
        "schließe die Durchsicht ab, um den nächsten Lauf freizuschalten",
    "personwizard.abnahme.knopf_verwerfen": "Diesen Lauf verwerfen",
    "personwizard.abnahme.verwerfen_hinweis":
        "schlechtes Ergebnis? alles wegwerfen",
    "personwizard.leer.verwaist":
        "Mit Absicht übersprungen: {liste} — diese Namen wurden aus "
        "deinen Personen gelöscht; ihre alten bestätigten Events bleiben "
        "als Historie, werden aber nicht gesammelt.",
    "personwizard.leer.titel":
        "Lauf ohne Bilder beendet — hier steht, warum",
    "personwizard.leer.satz":
        "Nichts wurde geändert; du kannst unten jederzeit einen neuen "
        "Lauf starten.",
    "personwizard.fertig.verwaist":
        "Mit Absicht übersprungen: {liste} — gelöschte Personen; ihre "
        "alten bestätigten Events werden nicht gesammelt.",
    "personwizard.fertig.fremd":
        "{n} bestätigte Fremden-Bilder sind in den Fremden-Pool "
        "gewandert — das nächste Training nutzt sie sofort.",
    "personwizard.fertig.titel": "Durchsicht abgeschlossen — Material übernommen",
    "personwizard.fertig.zeile":
        "{abgenommen} Bilder als Lernmaterial abgenommen, {verworfen} "
        "aussortiert (Lauf {lauf}).",
    "personwizard.fertig.knopf": "Das gelernte Material ansehen",
    "personwizard.fehler.titel": "Der letzte Lauf ist fehlgeschlagen",
    "personwizard.auswahl.opt_alle": "Alle bekannten Personen",
    "personwizard.auswahl.opt_fremde":
        "Fremde — Fremden-Bilder sammeln",
    "personwizard.auswahl.titel": "Wen anlernen",
    "personwizard.auswahl.satz":
        "Wähle eine Person, um in kleinen, fokussierten Paketen "
        "durchzusehen — oder alle auf einmal. Die Personen kommen aus "
        "deinen Gesichts-Referenzen; eine nach der anderen anzulernen "
        "hält die Durchsicht kurz.",
    "personwizard.auswahl.fremde_satz":
        "Fremde: sammelt Durchgänge, in denen niemand erkannt wurde "
        "(reine Straßen-Durchgänge, unbestätigte Besucher). In der "
        "Durchsicht bestätigst du, wer wirklich fremd ist — sie wandern "
        "in den Fremden-Pool und schärfen die Entscheidungsschwelle.",
    "personwizard.umfang.knopf_letzte": "letzte {n}",
    "personwizard.umfang.attr_eigen": "eigenes N",
    "personwizard.umfang.knopf_go": "los",
    "personwizard.umfang.titel": "Umfang (Events, nicht Tage)",
    "personwizard.umfang.satz":
        "Fang klein an (50) — du siehst jedes gesammelte Bild von Hand "
        "durch.",
    "personwizard.bilanz.ohne":
        "letzte {n} Personen-Events für {wer} — die Bindungs-Bilanz wird "
        "beim Anlegen des Laufs berechnet",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/nach rahmen die
    # hervorgehobene Zahl, Rand-Leerzeichen gehoeren zum Wert.
    "personwizard.bilanz.zahl_vor": "letzte {n} Personen-Events · ",
    "personwizard.bilanz.zahl_nach":
        " lassen sich über bestätigte Durchgänge an {wer} binden",
    "personwizard.bilanz.fremd": " · {n} Fremden-Kandidaten",
    "personwizard.bilanz.erkl_fremd":
        "Kandidaten sind Durchgänge, in denen niemand erkannt wurde — "
        "reine Straßen-Durchgänge und unbestätigte Besucher. Bis zu "
        "deiner Durchsicht ist alles ein VERDACHT; markiere dort jeden, "
        "der KEIN Fremder ist.",
    "personwizard.bilanz.erkl":
        "Das Binden ist konservativ: Nur Durchgänge mit genau einer "
        "gesichtsbestätigten Person zählen. Alles, was du danach siehst, "
        "lässt sich mit einem Klick aussortieren.",
    "personwizard.bilanz.titel": "Deine Auswahl",
    "personwizard.bilanz.knopf": "Diesen Lauf anlegen",
    "personwizard.review.stempel": "FALSCH",
    "personwizard.review.h_fremde": "Fremde",
    "personwizard.review.frage_fremd":
        "klicke jedes Bild an, auf dem KEIN Fremder zu sehen ist (ein "
        "Bewohner, ein bekannter Besucher), oder das unbrauchbar ist. "
        "Ein zweiter Klick nimmt es zurück. Alles wird sofort "
        "gespeichert; unmarkierte Bilder "
        "werden als bestätigte Fremde übernommen und schärfen die "
        "Entscheidungsschwelle.",
    "personwizard.review.frage":
        "klicke jedes Bild an, das FALSCH ist (nicht diese Person, oder "
        "unbrauchbar). Ein zweiter Klick nimmt es zurück. Alles wird "
        "sofort gespeichert; unmarkierte Bilder zählen als abgenommen.",
    "personwizard.review.titel": "Das Gesammelte durchsehen",
    "personwizard.review.kopf": "Lauf {lauf} — {frage}",
    # Der Zeilenumbruch ist Teil des Originals (Template-Literal) und
    # bleibt fuer die Byte-Treue im Wert.
    "personwizard.review.zurueck": "&larr; zurück zum\nAssistenten",
    "personwizard.review.knopf_fertig":
        "Durchsicht abschließen — abgenommene Bilder übernehmen",
    "personwizard.kontrolle.sammeln_titel": "Der Sammelmodus ist AN",
    "personwizard.kontrolle.sammeln_rest":
        " — jedes beurteilte Bild wird 30 Tage aufbewahrt, damit du die "
        "Entscheidungen später prüfen kannst. Rechne mit grob "
        "20&ndash;40 MB am Tag.",
    "personwizard.kontrolle.schlank_titel": "Schlanker Modus (Standard)",
    "personwizard.kontrolle.schlank_rest":
        " — beurteilte Bilder leben nur, solange ein Durchgang läuft; "
        "danach bleiben nur das Gewinner-Bild und das Urteils-Log unten. "
        "Das ist der datenschutzfreundliche Standard einer frischen "
        "Installation.",
    "personwizard.kontrolle.titel": "Beurteilte Bilder",
    "personwizard.kontrolle.satz":
        "Was die Körpererkennung wirklich angesehen hat, ein Block je "
        "Durchgang: das beurteilte Bild, die Klasse, auf die sie kam, "
        "der Score und woher das Bild stammt. Nützlich, wenn eine Person "
        "übersehen wurde oder jemand erkannt wurde, der nicht hätte "
        "erkannt werden dürfen.",
    "personwizard.kontrolle.leer_titel": "Noch nichts festgehalten",
    "personwizard.kontrolle.tag_fremd": "fremd",
    "personwizard.kontrolle.tag_drueber": "über der Schwelle",
    "personwizard.kontrolle.tag_drunter": "unter der Schwelle",
    "personwizard.kontrolle.schwelle": " &middot; Schwelle {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} beurteilt, {n} Bild aufbewahrt",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} beurteilt, {n} Bilder aufbewahrt",
    "personwizard.tabelle.fremd_zeile": "Fremde (Zusatzklasse)",
    "personwizard.tabelle.kein_fremd":
        "Noch keine Fremden-Klasse — mit einer arbeitet die Erkennung "
        "deutlich besser: Bestätigte Fremden-Bilder zeigen dem Modell, "
        "was NICHT dazugehört, und kalibrieren die "
        "Entscheidungsschwelle.",
    "personwizard.tabelle.q_eichung": "gemessen",
    "personwizard.tabelle.q_user": "von dir gesetzt",
    "personwizard.tabelle.q_standard": "eingebauter Standard",
    "personwizard.tabelle.f_modell": "Aktives Modell",
    "personwizard.tabelle.f_schwelle": "Schwelle",
    "personwizard.tabelle.f_scharf": "Scharf",
    "personwizard.tabelle.scharf_ja": "JA",
    "personwizard.tabelle.scharf_ja_rest": " — beurteilt live",
    "personwizard.tabelle.scharf_nein": "nein — nicht scharf",
    "personwizard.tabelle.konf_vor":
        "Größte gruppenübergreifende Verwechslung in der Kalibrierung: ",
    "personwizard.tabelle.konf_nach":
        " — der stärkste Score, den irgendein Bild für die FALSCHE "
        "Gruppe erreicht hat; je näher an 1, desto näher liegen zwei "
        "Gruppen beieinander.",
    "personwizard.tabelle.titel": "Gelernte Gruppen",
    "personwizard.karte.scharf": "Scharf",
    "personwizard.karte.unscharf": "Noch nicht scharf",
    "personwizard.karte.fehler":
        "Der letzte Trainingsversuch ist FEHLGESCHLAGEN: {fehler} — "
        "diese Karte zeigt das vorige Modell.",
    "personwizard.karte.titel": "Modellstatus",
    "personwizard.karte.zeile":
        "trainiert {wann} in {dauer} s — {bilder} Bilder: {je} · "
        "{modell} · ",
    "personwizard.karte.link": "Details",
    "personwizard.bestand.titel":
        "Personen-Material — was gelernt wurde",
    "personwizard.bestand.satz":
        "Abgenommene Ganzkörper-Bilder je Person. Wähle unten eine "
        "Gruppe, um ihre Bilder zu sehen; lösche ein einzelnes Bild "
        "(&times; auf der Kachel) — ein neuer Lauf kann danach jederzeit "
        "neu sammeln. Löschungen greifen beim nächsten Training.",
    "personwizard.bestand.leer_titel": "Noch kein abgenommenes Material",
    "personwizard.bestand.stark_titel": "Was dieses Modell stark macht",
    "personwizard.bestand.chip_fremde": "Fremde ({n})",
    "personwizard.bestand.zeigen_titel": "Bilder zeigen von",
    "personwizard.bestand.zeigen_satz":
        "Wähle eine Gruppe — ihre Bilder öffnen sich unten, neueste "
        "zuerst.",
    "personwizard.bestand.marker_tage.eins":
        "nur {n} Tag — die Erkennung verbessert sich am meisten, wenn das "
        "Material mehr Tage, Outfits und Lichtverhältnisse abdeckt",
    "personwizard.bestand.marker_tage.viele":
        "nur {n} Tage — die Erkennung verbessert sich am meisten, wenn "
        "das Material mehr Tage, Outfits und Lichtverhältnisse abdeckt",
    "personwizard.bestand.attr_loeschen": "dieses Bild löschen",
    "personwizard.bestand.z_bilder": "{n} Bilder",
    "personwizard.bestand.z_tage.eins": "{n} Tag",
    "personwizard.bestand.z_tage.viele": "{n} Tage",
    "personwizard.bestand.z_kameras.eins": "{n} Kamera",
    "personwizard.bestand.z_kameras.viele": "{n} Kameras",
    "personwizard.modell.titel": "Personenmodell — Status",
    "personwizard.modell.satz":
        "Das Modell der Körpererkennung, trainiert aus deinen "
        "abgenommenen Bildern. Es wird nach jeder abgeschlossenen "
        "Durchsicht und nach Löschungen automatisch neu trainiert.",
    "personwizard.modell.leer_titel": "Noch kein Modell",
    "personwizard.modell.fremd_keine":
        "noch keine — die Schwelle ist nur zwischen deinen Personen "
        "gemessen",
    "personwizard.modell.fremd_gesammelt":
        "{n} gesammelt — {min} nötig, bevor sie mittrainiert werden und "
        "die Schwelle kalibrieren",
    "personwizard.modell.fremd_geeicht":
        "{n} im Training · Schwelle an echten Fremden kalibriert",
    "personwizard.modell.fremd_ungeeicht":
        "{n} im Training — die Schwellen-Kalibrierung lief nicht (siehe "
        "Hinweis unten)",
    "personwizard.modell.f_trainiert": "Trainiert",
    "personwizard.modell.f_dauer": "Trainingsdauer",
    "personwizard.modell.f_modell": "Modell",
    "personwizard.modell.f_bilder": "Bilder gesamt",
    "personwizard.modell.f_personen": "Personen",
    "personwizard.modell.f_fremd": "Fremden-Negative",
    "personwizard.modell.scharf_ja": "JA — Live-Beurteilung aktiv",
    "personwizard.modell.scharf_nein": "nein — noch nicht scharf",
    "personwizard.modell.fehler":
        "Der letzte Trainingsversuch ist FEHLGESCHLAGEN ({zeit}): "
        "{fehler} — das hier gezeigte Modell ist das vorige und enthält "
        "deine letzten Änderungen nicht.",
    "personwizard.modell.aktuell_titel": "Aktuelles Modell",
    "personwizard.modell.material_titel": "Lernmaterial je Person",
    "personwizard.modell.kopf_person": "Person",
    "personwizard.modell.kopf_bilder": "abgenommene Bilder",
    "personwizard.modell.kopf_anteil": "Anteil",
    "personwizard.modell.summe": "gesamt",
    "personwizard.modell.q_eichung": "an deinem Material gemessen",
    # {pct} vorformatiert (round) aus der Route (§8.8).
    "personwizard.modell.eich_fremd":
        "Gemessen per {folds}-facher Kreuzvalidierung über {n} "
        "zurückgehaltene Bilder deiner Personen plus {n_fremd} "
        "bestätigte Fremde: Die stärkste Bewohner-Konfidenz (wie sicher "
        "sich das Modell war), die ein echter Fremder erreichte, war "
        "{max} &rarr; Schwelle {schwelle}; {pct}% der echten Bilder "
        "kommen durch. Die Kehrseite: {ueber} deiner eigenen Bilder "
        "würden diese Schwelle für die FALSCHE Person erreichen "
        "(stärkster Wert {vmax}).",
    "personwizard.modell.eich_intern":
        "Gemessen per {folds}-facher Kreuzvalidierung über {n} "
        "zurückgehaltene Bilder: stärkste Konfidenz (wie sicher sich das "
        "Modell war) für eine FALSCHE Person {max} &rarr; Schwelle "
        "{schwelle}; {pct}% der echten Bilder kommen durch. Ehrliche "
        "Grenze: Das kalibriert ZWISCHEN deinen gelernten Personen — "
        "echte Fremde sind noch nicht im Material.",
    "personwizard.modell.regeln_titel": "Urteils-Einstellungen",
    "personwizard.modell.schwelle_vor": "Entscheidungsschwelle: ",
    "personwizard.modell.r_fenster": "Auslöse-Fenster",
    "personwizard.modell.r_feuer": "Stütz-Events bis zur Meldung",
    "personwizard.modell.r_karenz": "Ruhezeit nach einer Meldung",
    "personwizard.modell.regeln_satz":
        "Lass die Schwelle leer, um automatisch dem gemessenen Wert zu "
        "folgen (er wird mit jedem Training neu gemessen). Die "
        "Auslöse-Regel: gemeldet wird erst nach so vielen Stütz-Events "
        "innerhalb des Fensters, danach bleibt es für die Ruhezeit "
        "still.",
    "personwizard.modell.knopf_speichern": "Einstellungen speichern",
    "personwizard.modell.satz_user":
        "Die Entscheidungsschwelle ist von dir gesetzt ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — die Kalibrierung an {n} bestätigten Fremden ergäbe {alt}",
    "personwizard.modell.satz_geeicht":
        "Die Entscheidungsschwelle ist an {n} bestätigten "
        "Fremden-Bildern kalibriert.",
    "personwizard.modell.satz_ungeeicht":
        "Die Entscheidungsschwelle ist noch nicht an Fremden-Material "
        "kalibriert — betrachte Meldungen als Vorschau und behalte sie "
        "im Auge.",
    "personwizard.modell.satz_fremd_drop":
        " Ein Körper, den das Modell als fremd liest, wird verworfen, "
        "bevor er ein Treffer werden kann.",
    "personwizard.modell.live_titel": "Live-Schalter",
    "personwizard.modell.live_an":
        "SCHARF — der Körperpfad beurteilt Live-Events und darf melden.",
    "personwizard.modell.live_aus":
        "Nicht scharf — der Körperpfad bleibt still.",
    "personwizard.modell.live_hinweis":
        "Meldungen tragen den Hinweis &quot;Personenerkennung, nicht "
        "Gesicht&quot;.",
    "personwizard.modell.knopf_disarm": "Unscharf schalten",
    "personwizard.modell.knopf_arm": "Körpererkennung scharfschalten",
    # --- webui/bausteine.py ---
    # Nur die gt_leiste-ANZEIGE-Texte; die Speicherwerte (GT_OFFEN_LABELS,
    # GT_KEIN_MENSCH) und KAT_LABELS/KAT_FARBE bleiben literal (Kommentar
    # im Modul: §8.12/§8.13, Meldetext-Mitnutzung).
    "baustein.gt.fremd": "Fremd",
    "baustein.gt.kein_mensch": "Keine Person",
    "baustein.gt.add": "Person hinzufügen…",
    "baustein.gt.uebernehmen": "diesen Vorschlag bestätigen (alle Genannten waren da)",
    "baustein.gt.fremd_titel": "ein Fremder war da (kann neben Namen stehen)",
    "baustein.gt.unklar_titel": "unsicher — offen lassen",
    "baustein.gt.kein_mensch_titel": "keine Person in diesem Event (Fehlauslöser)",
    "baustein.gt.opak_titel": "ein altes Urteil, das zu keiner bekannten Person mehr passt — ? oder einen Namen wählen, um es zu ersetzen",
    # ---- Route-JS + Meldungen (Stufe 2, Tranche D) ----
    # Uebersetzung 20.08.2026 (begriffe_tabellen.md, DE-Abschnitt);
    # Gattungen, Kontext + Stufe-2-Grenzen: siehe en.py-Abschnittskopf.
    # Zaehler-/Fragment-Splits: Rand-Leerzeichen gehoeren zum Wert;
    # Namens-Quotes wie im DE-Bestand gerade Doppel-Quotes ("...").
    # --- routes/lernwizard.py (Zuweisungs-Flaeche + Sichtung) ---
    "lernwizard.zw.js_zaehl_mitte": " von ",
    "lernwizard.zw.js_zaehl_nach": " Bildern ausgewählt",
    # Wiederverwendet aus lernanker.js.*: fehler, nicht_uebernommen,
    # nicht_gespeichert (gleiche Texte beider Routen).
    "lernanker.js.uebernimmt": "wird übernommen …",
    "lernanker.js.tag_frage_vor":
        "Seit dem Benennen geänderte Einstellungen:\n",
    "lernanker.js.tag_frage_nach":
        "\nTrotzdem mit der benannten Auswahl übernehmen?",
    "lernanker.js.weiter": "gespeichert — nächste Gruppe …",
    "lernanker.js.speichert": "wird gespeichert …",
    "lernanker.js.koll_vor": "\"",
    # DE-QS: "passt zur vorhandenen \"...\"" liess das Adjektiv ohne Nomen
    # haengen (und die Endung passte nur zu "Person", nie zum Namen).
    "lernanker.js.koll_mitte": "\" gibt es schon als \"",
    "lernanker.js.koll_nach":
        "\" — stattdessen zu dieser Person hinzufügen?",
    "lernwizard.zw.js_gespeichert_vor": "gespeichert als ",
    "lernwizard.zw.js_gespeichert_nach":
        " — die Bilder werden geprüft …",
    "lernwizard.sicht.js_fehl":
        "Prüfung fehlgeschlagen — Seite neu laden und erneut versuchen",
    "lernwizard.zw.js_verbergen":
        "Die übrigen {n} geprüften Bilder ausblenden",
    "lernwizard.zw.js_zeigen": "Alle {n} geprüften Bilder zeigen",
    # --- routes/qualitaet.py ---
    "qualitaet.galerie.js_gewaehlt": " ausgewählt",
    # --- routes/lernanker.py (nur dort) ---
    "lernanker.js.alle_fertig":
        "Alle Gruppen fertig — die benannten Bilder zählen jetzt für "
        "die Erkennung.",
    # --- routes/vision.py (Hand-ID-Script) ---
    "vision.modell.js_id_fehlt": "erst eine ID eintragen",
    "vision.modell.js_prueft": "wird geprüft …",
    "vision.modell.js_fehler": "Fehler",
    # --- routes/personwizard.py (Review-Script + Schalter) ---
    "personwizard.review.js_zaehl": " von {n} als falsch markiert",
    "personwizard.review.js_frage_vor": "Durchsicht abschließen? ",
    "personwizard.review.js_frage_mitte":
        " Bilder werden als Lernmaterial übernommen, ",
    "personwizard.review.js_frage_nach": " aussortiert.",
    "personwizard.modell.js_fehler": "Fehler ",
    # --- verifyd.py POST-Antworten (antwort.*, Nutzungs-Reihenfolge) ---
    "antwort.person_entfernt":
        "{person} entfernt ({n} Referenzbilder in den Papierkorb "
        "verschoben — wiederherstellbar)",
    "antwort.person_name_ungueltig": "ungültiger Name",
    "antwort.person_unbekannt": "unbekannte Person",
    "antwort.pruefung_gestartet": "Prüfung gestartet",
    "antwort.reorg_los":
        "Reorganisation läuft (Pool-Nachprüfung + Neugruppierung, "
        "1–2 min, danach die Seiten neu laden)",
    "antwort.reorg_laeuft":
        "Reorganisation läuft bereits — bitte warten",
    "antwort.paar_notiert":
        "gemerkt — dieses Paar wird nicht mehr vorgeschlagen",
    # §8.11-Anhang an eine Fachschicht-msg (die Basis bleibt Grenze).
    "antwort.nachpruefung_anhang":
        " — die Events dieses Durchgangs werden im Hintergrund "
        "nachgeprüft",
    "antwort.sync_wieder": "{n} wieder auf der Kandidatenliste",
    "antwort.sync_auswahl": "{ab} abgewählt, {zu} wieder aktiv",
    "antwort.sync_laeuft":
        "ein Abgleich läuft bereits — warte, bis er fertig ist",
    "antwort.sync_readonly":
        "Nur-Lesen-Modus: das Schreiben von Referenzen nach Frigate "
        "ist abgeschaltet (siehe den Schalter auf der System-Seite)",
    "antwort.sync_nichts":
        "nichts ausgewählt — hake mindestens ein Bild an",
    "antwort.frigate_url": "Frigate-URL: {fehler}",
    "antwort.sync_transfer": "Übertragung läuft ({n} ausgewählt)",
    "antwort.bruecke_hinzu": "{n} Bild(er) hinzugefügt",
    "antwort.modell_laedt":
        "das Erkennungsmodell lädt — ein paar Sekunden …",
    "antwort.refcache_baut":
        "die Referenzen werden neu aufgebaut — bei vielen Referenzen "
        "kann das eine Minute dauern …",
    "antwort.refcache_fehler":
        "der Neuaufbau der Referenzen ist zweimal in Folge fehlgeschlagen — "
        "siehe Dienst-Log (/log); der nächste Versuch läuft in ein paar Minuten",
    "antwort.cache_aufgeraeumt": "{n} Clip(s) entfernt, {mb} MB frei geworden — Cache {cache} GB, {frei} GB frei",
    "antwort.bruecke_nimmt": "die Prüfung wählt {n} Bild(er) aus",
    "antwort.bruecke_grenz_zusatz":
        " · {n} grenzwertige ohne Haken angezeigt",
    "antwort.bruecke_nur_grenz":
        "nichts eindeutig Hilfreiches — {n} grenzwertige(s) Bild(er) "
        "zurückgehalten (Identität sicher, Bildqualität nur mittel); "
        "du kannst sie trotzdem übernehmen",
    "antwort.bruecke_nichts":
        "nichts zu übernehmen — kein hilfreiches neues Bild in diesem "
        "Durchgang (das ist in Ordnung)",
    "antwort.bruecke_undo": "{n} Bild(er) wieder entfernt",
    "antwort.personlauf_kein_review": "kein Lauf wartet auf Durchsicht",
    "antwort.personlauf_kein_lauf": "kein aktiver Lauf",
    "antwort.events_bereich":
        "Events müssen zwischen 1 und {max} liegen",
    "antwort.personlauf_aktiv":
        "ein Personen-Lernlauf ist bereits aktiv",
    "antwort.lernlauf_tag_ungueltig": "ungültiger Tag (JJJJ-MM-TT)",
    # {phase} ist die interne Phasen-Kennung (sprachneutral, §8.19).
    "antwort.lernlauf_phase":
        "ein Lauf ist bereits in Phase \"{phase}\" — brich ihn zuerst ab",
    "antwort.lernlauf_beschaeftigt":
        "der vorige Lauf beendet noch sein aktuelles Event — "
        "versuch es gleich noch einmal",
    "antwort.lernlauf_schreibfehler":
        "Lauf-Zustand konnte nicht geschrieben werden: {fehler}",
    "antwort.lernlauf_angelegt": "Lauf angelegt",
    "antwort.lernlauf_abgebrochen":
        "abgebrochen — ein laufendes Event kann im Hintergrund noch "
        "fertig werden",
    "antwort.live_nichts": "nichts zu ändern",
    "antwort.live_an": "{ok}/{alle} Wächter gestartet",
    "antwort.live_aus": "{ok}/{alle} Wächter gestoppt",
    "antwort.vision_modell_ok":
        "das Modell hat geantwortet — als von Hand geprüft in die Liste "
        "aufgenommen; wähle es dort aus und speichere",
    "antwort.restore_upload_fehlt": "Upload fehlt oder ist zu groß",
    "antwort.restore_upload_kaputt": "Upload abgeschnitten",
    "antwort.backend_unbekannt": "unbekanntes Backend \"{backend}\"",
    "antwort.kameras_fehlen":
        "Frigate-Kameras nicht verfügbar: {fehler}",
    "antwort.setup_gespeichert":
        "Einrichtung gespeichert — Dienst startet neu",
    "antwort.kameras_gespeichert":
        "{n} Kameras gespeichert — Dienst startet neu",
    "antwort.name_ungueltig":
        "ungültiger Personenname (2–40 Buchstaben, Ziffern, "
        "Leerzeichen, -)",
    "antwort.anker_unbekannt": "unbekannter Anker",
    "antwort.anker_benannt":
        "als \"{name}\" benannt — {n} Bilder ausgewählt, übernimm sie "
        "mit dem Knopf Übernehmen",
    "antwort.anker_nur_unadoptiert":
        "nur Gruppen ohne übernommene Bilder lassen sich aussortieren",
    "antwort.anker_verworfen":
        "gelöscht — {n} Bilder entfernt",
    "antwort.lauf_id_ungueltig": "ungültige Lauf-ID",
    "antwort.lauf_aktiv":
        "dieser Lauf ist noch aktiv — brich ihn zuerst ab",
    "antwort.lauf_nichts":
        "nichts zu Lauf {lauf} gefunden — schon gelöscht?",
    "antwort.lauf_nur_einer":
        "nichts zu löschen — nur ein Lauf vorhanden",
    "antwort.gruppe_unbekannt": "unbekannte oder geschlossene Gruppe",
    "antwort.sichtung_laeuft":
        "die Bilder werden geprüft — ein paar Sekunden …",
    "antwort.anker_unbenannt": "Anker ist nicht benannt (oder unbekannt)",
    "antwort.benennen_mismatch":
        "deine Auswahl passte zu keinem Bild dieses Clusters — Seite neu "
        "laden und erneut anhaken",
    "antwort.adopt_nichts":
        "nichts ausgewählt — hake mindestens ein Bild zum Übernehmen an",
    "antwort.adopt_phantom":
        "die Dubletten-Prüfung traf nur Referenzen, die auf der Platte "
        "nicht mehr existieren — versuch die Übernahme noch einmal; "
        "bleibt das so, melde es",
    "antwort.adopt_gedeckt":
        "schon abgedeckt — alle {n} ausgewählten Bilder sind nahezu "
        "identisch mit vorhandenen Referenzen von {person}; Gruppe als "
        "übernommen markiert, nichts kopiert",
    # §8.10-Plural-Split: t_n statt f-String-Plural (wie en.py).
    "antwort.adopt_fertig.eins": "{n} Referenz für \"{person}\" übernommen",
    "antwort.adopt_fertig.viele":
        "{n} Referenzen für \"{person}\" übernommen",
    "antwort.adopt_skip": ", {n} als nahezu identisch übersprungen",
    "antwort.adopt_watchdog": " — Drift-Wächter läuft (System-Seite)",
    "antwort.areas_gespeichert.eins": "{n} Bereich gespeichert",
    "antwort.areas_gespeichert.viele": "{n} Bereiche gespeichert",
    # text/plain-Antwort der /video- und /clip-Routen (Tranche-B-Rest).
    "antwort.clip_weg":
        "Clip nicht mehr im Cache — Aufbewahrung {tage} Tage",
    # --- Konstante->Schluessel (Kennung/Anzeige-Trennung, Paket 3) ---
    # 3a: {hinweis}-Baustein fuer system.backup.careful_config und
    # system.voll.careful. DE-QS-Auflage aus dem Zusammenbau: pronomenfrei
    # (passt so in "diese Datei ..." UND "dieses Archiv ...") und die
    # API-Keys stehen am ENDE — im config-Rahmen haengen "(Meldekanaele
    # und Vision-Erkennung)" und der damit-Satz genau daran; die frueh
    # eingeschobene Passwort-Aufforderung hat den Satz zerrissen.
    "system.backup.hinweis":
        "ist so vertraulich wie ein Passwort und enthält deine API-Keys",
    # 3b: Anzeige-Woerter der Galerie-Reihen ({reihe} in "Ansicht
    # {reihe}", "aus der Reihe {reihe}"); Kennungen bleiben Store-Werte.
    "visiongalerie.reihe.vorn": "vorn",
    "visiongalerie.reihe.seitlich": "seitlich",
    "visiongalerie.reihe.hinten": "hinten",
    "visiongalerie.reihe.unklar": "unklar",
    # 3c: Kategorie-ANZEIGE (bausteine.kat_wort); Meldetexte lesen
    # weiter KAT_LABELS englisch. Gegenwort-Paar der v1-Achse ist
    # "Uebereinstimmung"/"Widerspruch" (DE-QS: die erste Fassung
    # "Deckung" liest sich als Deckung/Sicherheit, nicht als Einigkeit;
    # "Treffer" ist fuer die Erkennung reserviert).
    "baustein.kat.erkannt": "Erkannt",
    "baustein.kat.fremd_verdacht": "Fremd?",
    "baustein.kat.unbekannt_schwach": "Unbekannt (schwach)",
    "baustein.kat.fehler": "Fehler",
    "baustein.kat.no_person":
        "Keine Person gefunden (vermutlich Fehlauslösung)",
    "baustein.kat.uebersprungen": "Beim Start übersprungen",
    "baustein.kat.deckung": "Übereinstimmung",
    "baustein.kat.widerspruch": "Widerspruch",
    "baustein.kat.frigate_nur": "Nur Frigate",
    "baustein.kat.wir_nur": "Nur suslik",
    "baustein.kat.beide_unknown": "Beide unbekannt",
    # 3d: Wortstufen-ANZEIGE (bausteine.stufe_wort). ZWEI Verwendungen,
    # beide DE-QS-geprueft: im Satzfluss ("{person} — {stufe} (in {n}
    # Fenstern gesehen)", event.ours_zeile) und ALLEIN als title des
    # Heute-Chips (verifyd.py, Score-Pille) — darum klein, das Nomen
    # traegt die Grossschreibung.
    "baustein.stufe.clear": "klarer Treffer",
    "baustein.stufe.narrow": "knapp über der Schwelle",
    "baustein.stufe.below": "unter der Schwelle",
    "baustein.stufe.none": "kein Treffer",
    # ---- Anleitungen /hilfe (Stufe 3) ----
    # Uebersetzung der 76 en.py-Schluessel dieses Abschnitts, gleiche
    # Reihenfolge. Zitat-Kopplungen wortgleich zum DE-Bestand gesetzt
    # (je Fundstelle als Kommentar). Noch ENGLISCHE UI-Elemente werden
    # englisch zitiert (§8.2 Anzeige==Kennung): "Check the key"/"Check
    # the connection", "Always"/"Only if no face"/"If needed" sowie die
    # Mess-Etiketten "residents"/"strangers" (core/registry.py:632, s.
    # Befund bei vision.modell.antwort_satz).
    "hilfe.live.titel": "Live-Wächter, erklärt",
    "hilfe.live.satz1": """<p>Der Live-Wächter schaut auf deine Kameras, sobald sich etwas bewegt.
Betritt eine Person das Grundstück, bekommst du innerhalb von Sekunden eine
Meldung — und kennt das System das Gesicht schon, steht ein Name dran.</p>""",
    "hilfe.live.satz2": """<p>Der Name ist an dieser Stelle eine erste Einschätzung. Die gründliche
Prüfung läuft direkt danach auf der Aufnahme und hat das letzte Wort.</p>""",
    "hilfe.live.satz3": """<p>Der Live-Wächter hängt nicht an Frigate: Er wird nicht von Frigate-Events
angestoßen und läuft komplett eigenständig. Er schaut direkt auf den
Videostream — entweder Frigates Proxy-Stream oder den Stream der Kamera
selbst; das wählst du je Kamera.</p>""",
    # Zitat: <b>Kameras wählen</b> == erkennung.live.knopf_kameras
    # (ohne das " …").
    "hilfe.live.satz4": """<p>Mit <b>Kameras wählen</b> legst du fest, welche Kameras einen Wächter
bekommen. Jede beobachtete Kamera kostet rund um die Uhr Rechenleistung —
fang deshalb dort an, wo Menschen wirklich ankommen: Einfahrt, Haustür,
Tor. Nachlegen geht jederzeit.</p>""",
    "hilfe.live.satz5": """<p>Eine Kamera hier auszuschalten ändert nichts an der Aufnahme. Frigate
nimmt weiter auf wie bisher; der Schalter entscheidet nur, ob suslik sofort
aufs Bild schaut oder auf die Aufnahme wartet.</p>""",
    "hilfe.gesicht.titel": "Gesichtserkennung, erklärt",
    "hilfe.gesicht.satz1": """<p>Das ist der Grundweg, auf dem suslik Gesichter erkennt und lernt. Jeder
aufgenommene Durchgang wird gegen die Gesichter geprüft, die du dem System
angelernt hast.</p>""",
    "hilfe.gesicht.satz2": """<p>Angelernt wird aus deinen eigenen Kameras: suslik sammelt Gesichter, die
es sieht, du schaust die Bilder an und sagst, wer wer ist. Je mehr
verschiedene Situationen und Posen es von einer Person gesehen hat, desto
besser wird es: Tageslicht, Abend, Mütze auf, Mütze ab, von der Seite.</p>""",
    # Zitat: "Frigate-Abgleich" == nav.sync_auswahl.
    "hilfe.gesicht.satz3": """<p>Kennt Frigate schon Gesichter, kannst du sie auf der Seite
Frigate-Abgleich importieren. Die Empfehlung bleibt trotzdem, Gesichter hier
anzulernen: susliks eigenes Anlernen sammelt viele verschiedene Posen und
Situationen je Person, und diese Referenzen liefern in suslik bessere
Ergebnisse als aus Frigate übernommene Gesichter. Was du hier anlernst,
kannst du auf der Abgleich-Seite an Frigate zurückgeben, wenn du willst.</p>""",
    "hilfe.gesicht.satz4": """<p>Alles bleibt auf deiner Maschine. Nichts wird irgendwohin hochgeladen,
und es steht kein Cloud-Dienst dahinter.</p>""",
    # Zitat: "Meldungen" == benachrichtigungen.titel / nav.benachrichtigungen.
    "hilfe.gesicht.satz5": """<p>Wird ein Gesicht erkannt oder taucht ein unbekanntes auf, schickt dir
suslik auf Wunsch direkt eine Meldung: Pushover, Telegram oder MQTT für
deine Hausautomation. Auf der Seite Meldungen wählst du, was wohin geht.
Diese Meldungen kommen von suslik selbst und laufen völlig unabhängig von
Frigate; in Frigate musst du dafür nichts einrichten.</p>""",
    # Zitat: <b>Personen verwalten</b> == erkennung.gesicht.knopf_verwalten,
    # <b>Gesicht registrieren</b> == erkennung.knopf_register_face
    # (jeweils ohne das " …").
    "hilfe.gesicht.satz6": """<p><b>Personen verwalten</b> zeigt alle, die das System kennt — dort
kannst du auch aufräumen. <b>Gesicht registrieren</b> startet einen Lernlauf
für jemand Neues.</p>""",
    "hilfe.koerper.titel": "Körpererkennung, erklärt",
    "hilfe.koerper.satz1": """<p>Manche Durchgänge zeigen nie ein brauchbares Gesicht: Die Person schaut
weg, trägt eine Kapuze oder ist zu weit entfernt. Diese Fälle deckt die
Körpererkennung ab. Sie erkennt Bewohner an Statur und Haltung, mit
Bildern der ganzen Person.</p>""",
    "hilfe.koerper.satz2": """<p>Sie ist genau für diesen Fall gebaut: kein brauchbares Gesicht, du
willst trotzdem wissen, wer es war, und du willst die Bilder dafür nicht
an ein KI-Vision-Modell geben.</p>""",
    # Zitat: <b>Körper registrieren</b> == erkennung.koerper.knopf_register
    # (ohne das " …").
    "hilfe.koerper.satz3": """<p>Sie lernt aus Material, das du abnimmst. <b>Körper registrieren</b>
startet einen kurzen Lernlauf für eine Person: Das System sammelt Bilder
von ihr aus deinen Kameras, du siehst das Ergebnis einmal durch, und ab
dann lernt die Körpererkennung von selbst weiter.</p>""",
    # Unteroptions-Labels noch englisch im UI — englisch zitiert (§8.2).
    "hilfe.koerper.satz4": """<p>Mit dem Schalter oben wählst du, ob und wann sie läuft. <b>Only if no
face</b> heißt: Sie bleibt still, solange die Gesichtsprüfung nicht leer
ausgeht. <b>Always</b> heißt: Sie prüft jeden Durchgang. Aus heißt: Sie
läuft nie.</p>""",
    "hilfe.vision.titel": "KI-Vision, erklärt",
    "hilfe.vision.satz1": """<p>KI-Vision ist ein eigener Erkennungsweg. Sie zeigt die Bilder eines
Durchgangs einem Bildmodell und fragt, welcher registrierten Person sie
ähneln. Du kannst sie als Absicherung für die harten Fälle nutzen oder sie
die Erkennung allein tragen lassen: Auf <b>Always</b> gestellt, beurteilt
sie jeden Durchgang selbst, auch wenn gar keine Gesichter angelernt sind. Sie
urteilt am Ende eines Durchgangs, nicht live.</p>""",
    "hilfe.vision.satz2": """<p>Was sie zum Arbeiten braucht: registrierte Personen mit abgenommenen
Körperbildern (ihren Galerien) und ein verbundenes Modell. Das Modell kann
lokal auf deiner eigenen Hardware laufen oder in der Cloud. Bei einem
Cloud-Modell denk daran, dass die Bilder dein Haus verlassen: Was mit
einem lokalen Modell in Ordnung ist, ist mit einem Cloud-Modell nicht
automatisch erlaubt. Und nimm nicht die kleinsten Modelle; ein
mittelgroßes Modell erledigt die Aufgabe gut.</p>""",
    # Zitat: "Vision-Erkennung" == nav.vision.
    "hilfe.vision.satz3": """<p>Was wir selbst fahren: Qwen 3.5 in der 9B-Größe, und die erledigt die
Aufgabe gut, lokal wie in der Cloud. Getestet haben wir auch Modelle von
Anthropic (Claude), Google (Gemini) und OpenAI (GPT). Nimm das als
getestet, nicht als Empfehlung; die Modellliste auf der Seite
Vision-Erkennung markiert die von uns vermessenen Modelle, genau dort, wo
du wählst.</p>""",
    "hilfe.vision.satz4": """<p>Und es bleibt nicht bei einem Vergleich: Um Verwechslungen
auszuschließen, wird der Durchgang auch gegen die Galerien der anderen
Personen geprüft, in beide Richtungen. Jedes verglichene Paar kostet zwei
Anfragen, bei einem einzelnen Durchgang kann da also einiges
zusammenkommen. <b>If needed</b> hält diese Rechnung klein: Das Modell wird
nur gefragt, wenn die Gesichter Zweifel lassen. Ohne verbundenes Modell
bleibt Vision schlicht außen vor, und die Karte sagt das auch.</p>""",
    "hilfe.faces_bekannt.titel": "Bekannte Personen & Registrieren, erklärt",
    "hilfe.faces_bekannt.satz1": """<p>Hier siehst du jede Person, die dein System kennt &mdash; tippe auf ein
Gesicht und du siehst jedes Bild, das dahinter gespeichert ist.</p>""",
    "hilfe.faces_bekannt.satz2": """<p>Eine neue Person lernst du nicht per Foto-Upload an: Angelernt wird aus
normalem Kameramaterial. Über den Tag sammelt das System Bilder aus
verschiedenen Winkeln, du bestätigst, wer es ist, und erst nach dieser
Prüfung wird ein Bild behalten.</p>""",
    "hilfe.faces_bekannt.satz3": """<p>So bekommt jede Person eine kleine Sammlung echter Alltagsbilder
&mdash; genau das macht die Erkennung stark, auch wenn jemand wegschaut
oder eine Mütze trägt.</p>""",
    "hilfe.faces_lernen.titel": "Anlernen, erklärt",
    "hilfe.faces_lernen.satz1": """<p>Während die Kameras laufen, sammelt das System ständig neue Bilder der
Personen, die es schon kennt. Hier siehst du durch, was zusammengekommen
ist &mdash; alle paar Tage reicht völlig.</p>""",
    "hilfe.faces_lernen.satz2": """<p>Mit einem Klick bestätigst, korrigierst oder sortierst du aus; nichts
wird ohne dich behalten.</p>""",
    "hilfe.faces_lernen.satz3": """<p>Je mehr gute Bilder eine Person hat, desto zuverlässiger wird sie
erkannt &mdash; das Anlernen hört deshalb nie ganz auf, es wird nur
seltener.</p>""",
    "hilfe.faces_unbekannt.titel": "Unbekannte Besucher, erklärt",
    "hilfe.faces_unbekannt.satz1": """<p>Manche Menschen tauchen immer wieder auf, ohne dass das System einen
Namen für sie hat &mdash; ein Zusteller, eine Nachbarin, der Gärtner. Hier
sammelt das System diese wiederkehrenden Unbekannten und fragt dich: Wer
ist das?</p>""",
    "hilfe.faces_unbekannt.satz2": """<p>Gib ihnen einen Namen, und ab dann werden sie erkannt wie alle
anderen. Oder lass sie bewusst unbekannt &mdash; auch das ist eine
Entscheidung, und das System fragt nicht immer wieder nach.</p>""",
    "hilfe.faces_qualitaet.titel": "Qualitätscheck, erklärt",
    "hilfe.faces_qualitaet.satz1": """<p>Mit der Zeit sammeln sich viele Bilder an, und nicht jedes hilft der
Erkennung &mdash; manche sind unscharf, manche zeigen die Person kaum, und
im schlimmsten Fall sehen sich Bilder zweier verschiedener Personen so
ähnlich, dass Verwechslungen drohen.</p>""",
    "hilfe.faces_qualitaet.satz2": """<p>Dieser Check findet solche Schwachstellen, bevor sie dich eine
Erkennung kosten. Du bekommst konkrete Hinweise, welche Bilder du dir
anschauen solltest &mdash; gelöscht wird nichts, außer du entscheidest es
selbst.</p>""",
    "hilfe.faces_lernlauf.titel": "Der Lernlauf, erklärt",
    "hilfe.faces_lernlauf.satz1": """<p>Du startest einen Lauf; das System liest deine letzten Aufnahmen neu
und sammelt selbstständig Gesichter.</p>""",
    "hilfe.faces_lernlauf.satz2":
        "<p>Es sortiert sie in Gruppen. Eine Gruppe soll eine Person sein.</p>",
    "hilfe.faces_lernlauf.satz3": """<p>Du benennst jede Gruppe oder überspringst sie. Das ist der einzige
Schritt, der dich braucht.</p>""",
    "hilfe.faces_lernlauf.satz4": """<p>Benannte Bilder werden Referenzen und zählen sofort für die Erkennung.
Wiederhole das alle paar Tage, oder lass die Heute-Ansicht bekannte
Personen zwischendurch auffüllen.</p>""",
    # B9-Rueck-Links: ganze Saetze je Ziel. Kopplung: "Erkennung" ==
    # nav.erkennung/erkennung.titel, "Gesichter" == nav.faces/faces.titel
    # (als Seitenname unflektiert zitiert), "Lernlauf" == nav.lernlauf.
    "hilfe.zurueck.erkennung": "Zurück zur Erkennung",
    "hilfe.zurueck.faces": "Zurück zur Seite Gesichter",
    "hilfe.zurueck.lernlauf": "Zurück zum Lernlauf",
    # ---- §8.1-Nachzuegler (Stufe 3) ----
    # Zitat: <b>System</b> == system.titel / nav.system.
    "setupwiz.backend.system_satz":
        "Ob der Beschleuniger wirklich greift, bestätigt dir nach dem "
        "Start live die Seite <b>System</b> (suslik fällt nie "
        "stillschweigend auf CPU zurück, ohne es zu sagen).",
    # Zitat: system.titel + konfiguration.knopf_setup, wortgleich
    # (Pfeil verbindet die beiden Zitate).
    "setupwiz.fertig.wieder_satz":
        "Du kannst diesen Assistenten jederzeit über <b>System → "
        "Einrichtungsassistent erneut ausführen</b> aufrufen.",
    "system.sync.diagnose_satz":
        'Meldet ein Abgleich ein Problem, <a href="/sync_diagnose" '
        'target="_blank">öffne die Diagnose</a> — sie bündelt den '
        "suslik-Bericht und das Frigate-Log, fertig zum Kopieren in ein "
        "Issue.",
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">öffne die Diagnose</a> '
        "— bündelt den suslik-Bericht und das Frigate-Log.",
    "vision.kopf.einleitung":
        "Ein dritter Erkennungsweg neben Gesicht und Körper: Ein "
        "Vision-Sprachmodell schaut auf ein Bild aus einem Durchgang und "
        "sagt, welche deiner angelernten Personen es zeigt &mdash; per "
        "Vergleich mit einer kleinen Galerie dieser Person. Dieser Weg "
        "ist eine <b>zusätzliche Stimme</b>, nie der Türsteher: Die "
        "Zwangswahl antwortet &bdquo;A oder B&ldquo;, sie kann also "
        "einen Bewohner bestätigen, aber keinen Fremden abweisen. Das "
        "bleibt Aufgabe der bestehenden Erkennung.",
    # Produktnamen (llama.cpp, Qwen3.5, docker stats) wortgleich (§8.7).
    "vision.hinweis.modell_satz":
        "Ein Vision-Modell, das mehrere Bilder auf einmal anschauen "
        "kann. Du kannst unten einen der Online-Anbieter nutzen oder "
        "selbst eins betreiben &mdash; die hier vermessene Kombination "
        "ist <b>llama.cpp</b> mit einem <b>Qwen3.5</b>-Vision-Modell "
        "(das 4B ist bei dieser Aufgabe genauso gut wie das 9B und "
        "braucht etwa den halben Speicher). Es muss <b>nicht</b> auf "
        "dieser Maschine laufen.",
    "vision.hinweis.host_satz":
        "<b>Dieser Host ist für ein lokales Modell meist zu klein.</b> "
        "Das 9B braucht rund 12 GB Working Set, das 4B etwa 6,6 GB, und "
        "suslik plus Analyse-Worker wohnen schon hier &mdash; der Worker "
        "ist das Erste, was der Kernel abschießt, wenn der Speicher "
        "ausgeht. Eine zweite Maschine oder ein Online-Anbieter ist der "
        "vernünftige Aufbau.",
    "vision.hinweis.mess_satz":
        "Eine Warnung zum Messen dieses Speichers: <code>docker "
        "stats</code> zeigt für den Modell-Container etwa 2,7 GiB, weil "
        "die Gewichte gemappt sind, nicht kopiert. Das echte Working Set "
        "liegt bei ~11,6 GiB. Wenn du <code>--memory</code> danach "
        "bemisst, was <code>docker stats</code> sagt, lädt das Modell "
        "seine Gewichte ununterbrochen neu und alles kriecht.",
    "vision.hinweis.kosten_satz":
        "Tempo und Kosten, gemessen, damit dich später nichts "
        "überrascht: Der ganze Durchgang geht als <b>ein "
        "Kandidaten-Gitter</b> hinein, und jedes <b>verglichene "
        "Galerien-Paar kostet zwei Anfragen</b> (dieselbe Frage wird mit "
        "vertauschten Galerien noch einmal gestellt, um eine "
        "Positions-Vorliebe aufzudecken). Meist entscheidet ein Paar. "
        "Auf einer Maschine der CPU-Klasse sind das etwa 7 Minuten je "
        "Paar; auf den hier vermessenen Online-Endpunkten Sekunden.",
    "vision.verb.key_ort":
        "<b>Trag den Key ins Key-Feld ein, nicht in die URL</b>: Ein "
        "Endpunkt, der Zugangsdaten in seiner Adresse trägt &mdash; vor "
        "dem Hostnamen oder als Query-Parameter &mdash; enthält dasselbe "
        "Geheimnis, und es taucht an weit mehr Stellen auf (Status, "
        "Log, Backup).",
    # Pruef-Knopf noch ENGLISCH im UI (§8.2 Anzeige==Kennung) — deshalb
    # englisch zitiert.
    "vision.modell.leer_key":
        "Noch nichts zu wählen. Trag oben deinen Key ein und drücke "
        "<b>Check the key</b>: suslik verbindet sich mit dem Endpunkt, "
        "fragt dort nach den Modellen und zeigt dir, was es gefunden "
        "hat. Aus dieser Liste wählst du.",
    "vision.modell.leer_verbindung":
        "Noch nichts zu wählen. Füll die Felder oben aus und drücke "
        "<b>Check the connection</b>: suslik verbindet sich mit dem "
        "Endpunkt, fragt dort nach den Modellen und zeigt dir, was es "
        "gefunden hat. Aus dieser Liste wählst du.",
    # MESS-ETIKETTEN (Code-Befund 20.08., DE-Muttersprachler-QS): die
    # Badge-Zeile wird in core/registry.py:632 als ENGLISCHES Literal
    # gebaut ("residents ✓ 12/12 · strangers ✗ 5/6") und ungefiltert
    # ausgegeben — routes/vision.py:400 (`b["text"]` ins <option>) und
    # webui/app.js:1377 (`m.badge.text`). Sie sind damit Anzeige==Kennung
    # (§8.2) und werden hier ENGLISCH zitiert — genau wie in es.py, it.py
    # und fr.py (gegengeprueft 20.08.; de.py war die einzige Abweichung).
    # Prosa-Bewohner/-Fremde (vision.kopf.einleitung) bleiben davon
    # unberuehrt: die zitieren kein UI-Element.
    # Zitat: <b>hier ungetestet</b> == vision.modell.ungetestet.
    "vision.modell.antwort_satz":
        "Das hat der Endpunkt geantwortet, als suslik ihn gefragt hat, "
        "{zeit} &mdash; nichts hier ist ein Vorschlag von uns. Wo wir "
        "ein Modell vermessen haben, sitzt der Hinweis an diesem Modell. "
        "Zwei Fähigkeiten stehen getrennt, weil sie auseinanderfallen: "
        "<b>residents</b> heißt, von zwei bekannten Personen die "
        "richtige zu treffen, <b>strangers</b> heißt, für jemanden, den "
        "du nie angelernt hast, &bdquo;keiner&ldquo; zu antworten. Ein "
        "Haken bedeutet: Jedes Urteil dieser Art in unserer Messung war "
        "richtig; der Bruch daneben zeigt dir das ganze Bild. Bei "
        "Modellen ohne Messung steht <b>hier ungetestet</b> &mdash; das "
        "ist kein Urteil, nur Ehrlichkeit (Messungen vom {stand}).",
    # Zitat: <b>angepasster Wortlaut</b> == visiontest.vision.custom_prompt.
    "vision.prompt.eigen_satz":
        "Das ist dein eigener Wortlaut &mdash; damit gefällte Urteile "
        "sind als <b>angepasster Wortlaut</b> markiert. Setz ihn zurück, "
        "um wieder den vermessenen Standard zu verwenden.",
    "vision.cloud.sendet_satz":
        "Das schickt Bilder von Personen aus deinen Kameras an "
        '<b class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Drei Stufen, weil ein bloßer Erreichbarkeits-Ping nicht reicht: "
        "Ein Backend war erreichbar, hatte das Modell und antwortete "
        "schnell &mdash; und beantwortete trotzdem 5 von 12 "
        "Vergleichsfragen falsch, weil es die Bilder vor dem Hinschauen "
        "verkleinerte.<br><b>1</b> Erreichbarkeit, Modell und "
        "Antwortzeit, mit einem an Ort und Stelle erzeugten "
        "Testbild.<br><b>2</b> ein Zwangswahl-Lauf auf erzeugten "
        "Form-Gittern, bei denen die richtige Antwort bekannt ist "
        "&mdash; das prüft das Antwortformat, den Parser und den "
        "Schalter fürs Denken.<br><b>3</b> eine Token-Zählung gegen "
        "eine vermessene Referenz; so fällt Bild-Verkleinerung "
        "auf.<br><b>Kein Bild einer Person wird dafür verwendet</b>, "
        "und dazu gibt es auch keine Option.",
    "visiontest.kopf.wege_satz":
        "Wähl einen echten Durchgang und sieh nebeneinander, was alle "
        "drei Erkennungswege daraus machen: <b>Gesicht</b>, "
        "<b>Person</b> und <b>Vision</b>.",
    # Zitat: "Vision-Erkennung" == nav.vision.
    "visiontest.vision.einrichten_satz":
        'Richte sie unter <a href="/vision">Vision-Erkennung</a> ein: '
        "ein Modell, ein grüner Verbindungstest und mindestens zwei "
        "abgenommene Galerien. Die anderen beiden Spalten funktionieren "
        "auch ohne.",
    "visionwizard.groesse.satz":
        "Ehrlich gemessen: Die Größe war <b>nicht</b> der Hebel, in "
        "keinem der Fälle, die wir gefahren haben &mdash; ein größeres "
        "Gitter machte die Antworten nicht besser, aber auch nicht "
        "schlechter. Nimm das größere, wenn dein Material es hergibt "
        "(hier: {empfehlung}), das kleinere, wenn nicht. Beide kosten "
        "etwa gleich viel, denn Tokens kostet die Leinwand, nicht die "
        "Zellenzahl.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Vergiss '
        "sie</a>, wenn du neu anfangen willst.",
    # Zitat: <b>passt nicht</b> == visionwizard.zelle.knopf_weg;
    # vorn/seitlich/hinten == visiongalerie.reihe.*.
    "visionwizard.vorschlag.satz":
        "Eine Reihe je Ansicht: vorn, seitlich, hinten. Bilder werden "
        "nach Größe und Schärfe gewählt, danach, wie klar Augen und "
        "Nase da sind, wie viel Licht ausgebrannt ist, wie viel vom "
        "Ausschnitt wirklich die Person ist &mdash; und über "
        "verschiedene Tage, Events und Kameras gestreut. Die Zeile "
        "unter jedem Bild sagt, was daran gemessen wurde. Klick bei "
        "allem Unbrauchbaren auf <b>passt nicht</b> &mdash; das "
        "nächstbeste Bild DERSELBEN Ansicht rückt nach. Dein "
        "Lernmaterial bleibt unberührt; es heißt nur &bdquo;nicht als "
        "Galerie-Zelle&ldquo;.",
    "personwizard.kopf.stark_satz":
        "<b>Was das Modell stark macht:</b> Vielfalt schlägt Menge. "
        "Bilder aus <b>vielen verschiedenen Tagen</b> (Kleidung, Licht, "
        "Kameras) helfen weit mehr als viele Bilder aus einem Durchgang "
        "— starte das Sammeln lieber an neuen Tagen erneut, statt aus "
        "einem einzelnen Tag noch mehr herauszuholen. Bestätigte "
        "Fremden-Bilder schärfen die Entscheidungsschwelle auf dieselbe "
        "Weise.",
    # Zitat: "Modellstatus" == nav.person_modell (+ erkennung.koerper.
    # knopf_status "Modellstatus …").
    "personwizard.fertig.training_satz":
        "Das Training mit dem abgenommenen Material startet automatisch "
        'nach der Durchsicht — siehe <a href="/person/modell">'
        "Modellstatus</a>. Einen weiteren Lauf kannst du unten "
        "jederzeit anstoßen.",
    # Zitat: "Konfiguration" == nav.bereich.configuration, "Erweitert"
    # == nav.konfiguration (EN-Wortlaut von "Settings" auf
    # "Configuration" korrigiert — toter Wegweiser).
    "personwizard.kontrolle.schalter_satz":
        'Schalte es unter <a href="/konfiguration">Konfiguration '
        "&rarr; Erweitert</a>, Schlüssel "
        "<code>diagnostic_collection</code>. Bilder und Log verfallen "
        "zusammen mit dem Treffer-Log nach 30 Tagen &mdash; nichts hier "
        "wird länger aufbewahrt als das Erkennungs-Protokoll selbst.",
    # Zitat: "Modellstatus" == nav.person_modell.
    "personwizard.kontrolle.leer_satz":
        "Einträge erscheinen, sobald die Körpererkennung auf "
        '<a href="/person/modell">Modellstatus</a> scharfgeschaltet ist '
        "und eine Person über das Grundstück geht.",
    # Zitat: "Personen-Lernlauf" == nav.personlauf.
    "personwizard.bestand.leer_satz":
        'Starte den <a href="/personlauf">Personen-Lernlauf</a> und '
        "schließ die Durchsicht ab — abgenommene Bilder erscheinen "
        "hier.",
    "personwizard.bestand.stark_satz":
        "Vielfalt schlägt Menge: Bilder aus <b>vielen verschiedenen "
        "Tagen</b> (Kleidung, Licht) helfen weit mehr als viele Bilder "
        "aus einem Durchgang. Ziel sind mehrere Tage je Person, und "
        "lass das Sammeln alle deine Kameras abdecken.",
    "personwizard.bestand.fremd_satz":
        "<b>Fremde:</b> {n} bestätigte Fremden-Bilder kalibrieren die "
        "Entscheidungsschwelle — je mehr Fremde das Modell gesehen "
        "hat, desto verlässlicher ist diese Linie. (Gesammelt in "
        "<code>personlern/fremd/</code>; eine Seite, um diese Sammlung "
        "aus den Durchgängen an deiner eigenen Straße wachsen zu lassen, "
        "ist geplant.)",
    "personwizard.bestand.fremd_erklaerung":
        "Bestätigte Fremden-Bilder — sie trainieren die Zusatzklasse "
        "und kalibrieren die Entscheidungsschwelle. Löschst du eins, "
        "wird das Modell sofort neu trainiert (die Dateien liegen in "
        "<code>personlern/fremd/</code>).",
    # Zitat: "Personen-Lernlauf" == nav.personlauf.
    "personwizard.modell.leer_satz":
        'Starte den <a href="/personlauf">Personen-Lernlauf</a> und '
        "schließ eine Durchsicht ab — das Training startet danach "
        "automatisch.",
    # Zitat: "Körperbilder" == nav.person.
    "personwizard.modell.material_satz":
        "Verwalte die Bilder unter "
        '<a href="/person">Körperbilder</a> — nach jeder Löschung wird '
        "das Modell automatisch neu trainiert.",
    # ---- Meldetexte (Stufe 4) --------------------------------------------
    # Pushover-/Telegram-TEXTE (Reihenfolge wie en.py). Sie entstehen OHNE
    # Request — die Sprache kommt am Meldeweg aus dem Config-Store.
    # Produktnamen (suslik/Frigate) bleiben wortgleich (§8.6). Drei
    # Platzhalter tragen FREMDE Teile in den deutschen Satz: {wache} die
    # englische Waechter-Kennung ("Live watcher", core.livewache), {wort}
    # die schon uebersetzte Wortstufe (baustein.stufe.*), {label} das
    # Frigate-Objektlabel. Der Rahmen ist so gebaut, dass er sie traegt.
    "meldung.titel.kategorie": "suslik: {wort}",
    # Event-Alert (verifyd._maybe_alert): je Urteils-Zweig ein GANZER Satz.
    # "Fenster(n)" ist Klammerplural (§8.18) — {n} kann 1 sein, und fuer
    # diesen Schluessel gibt es kein t_n-Paar. Wortlaut wie die Ereignis-
    # Zeile im UI (event.ours_zeile: "in {n} Fenstern gesehen").
    "meldung.alert.bestaetigt":
        "{name} bestätigt ({wort}, in {n} Fenster(n) gesehen)",
    # Komma statt Gedankenstrich: der Zweig haengt in meldung.alert.satz
    # schon hinter einem Gedankenstrich ("{kamera} — {urteil}"), zwei
    # Striche im selben Satz lesen sich im Deutschen als Bruch.
    "meldung.alert.keiner_naechster":
        "niemand bestätigt, am nächsten dran ist {name} ({wort})",
    "meldung.alert.keiner_ohne_gesicht":
        "niemand bestätigt, kein brauchbares Gesicht",
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate sah: {label}. {gesichter}",
    "meldung.alert.gesichter.eins": "{n} Gesicht in diesem Event.",
    "meldung.alert.gesichter.viele": "{n} Gesichter in diesem Event.",
    # Rohzahlen-Anhang (nur alert_stil=worte_zahlen): reine Technik, "cos"
    # bleibt wie in der Ereignisliste (ereignisliste.tabelle.frigate_zelle).
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    # Personen-Erkennung ueber den Koerper. Der Klammer-Hinweis steht
    # wortgleich im Wizard (personwizard.modell.live_hinweis), "Stütz-Event"
    # wortgleich in personwizard.modell.r_feuer.
    "meldung.person.titel": "suslik Personenerkennung",
    "meldung.person.satz":
        "{name} über den Körper erkannt (Personenerkennung, nicht "
        "Gesicht) — {wort}, {n} Stütz-Event(s)",
    # Ersatzwort, wenn die geeichte Latte nicht lesbar war (match/Treffer).
    "meldung.person.wort_ersatz": "Treffer",
    "meldung.person.zahl": "[Score {score}]",
    # Vision-Meldungen (verifyd._vision_melden). "Bild(er)"/"Vergleich(en)"
    # bleiben EINE Form (§8.18), der Gedankenstrich-Zusatz ist ein eigener
    # Schluessel (§8.11). "Vision" ist im DE-Bestand der Kurzname des Wegs
    # (vision.meld.satz), das Gitter heisst Gitter (visiontest.gitter.*).
    "meldung.vision.titel": "suslik Vision",
    "meldung.vision.unbestaetigt":
        "Vision konnte in diesem Durchgang niemanden bestätigen",
    "meldung.vision.koerper_zusatz": "— die Körpererkennung nannte {namen}",
    "meldung.vision.bilder_zusatz": "({n} Bild(er) im Gitter)",
    "meldung.vision.einig":
        "Vision: {name} — einstimmig, {voten} von {bilder} Vergleich(en)",
    "meldung.vision.kein_urteil": "Vision: kein Urteil — {grund}",
    # Live-Waechter (core/livewache). Der Trigger-Titel meldet eine
    # DETEKTION, nicht die Wiedererkennung — "erkannt" bleibt der
    # Erkennung vorbehalten (begriffe_tabellen.md, Objekterkennung vs.
    # Erkennung), deshalb "entdeckt".
    "meldung.wache.titel_person": "{wache} {kamera}: Person entdeckt",
    "meldung.wache.titel_stoerung": "{wache} {kamera}: Störung",
    "meldung.wache.caption": "{wache} {kamera}: {text}",
    # "{n}× übereinstimmend" statt Zahl+Nomen: {n} kann 1 sein und hat hier
    # kein t_n-Paar — eine Fuegung wie "{n} übereinstimmende Treffer" waere
    # im Singular falsch dekliniert. Wortfamilie wie live.erklaer.satz1.
    "meldung.wache.name_satz":
        "erkannt (live, vorläufig): {name} ({wort}, {n}× übereinstimmend)",
    "meldung.wache.name_zahl": "[Cosinus {cos}]",
    "meldung.wache.funde.eins": "{n} Gesicht in {sek} s",
    "meldung.wache.funde.viele": "{n} Gesichter in {sek} s",
    "meldung.wache.funde_zahl": "(Score {score}, {ms} ms)",
    # Geteilte Bausteine beider Straenge (core/melden + verifyd).
    "meldung.video_ersatz.satz":
        "(Video nicht verfügbar — stattdessen ein Bild)",
    "meldung.test.satz": "Testmeldung von suslik ✓",
    # ---- D1: ehrliche Begruendung der Pass-Pruefung ----------------------
    # SATZTEILE mit kleinem Anfangswort: sie haengen hinter "nichts zu
    # übernehmen — " (antwort.bruecke_nichts_grund) oder hinter dem
    # Grenzfall-Satz (antwort.bruecke_grund_zusatz). Zahlen UND Schwellen
    # kommen fertig aus der Diagnose — hier steht keine Schwelle als Wert,
    # nur ihr Platzhalter. "Gesicht(er)"/"Event(s)"/"Bild(ern)" bleiben
    # EINE Form (§8.18, wie antwort.bruecke_nimmt).
    "antwort.bruecke_nichts_grund": "nichts zu übernehmen — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    # Die Messwerte stehen in Klammern statt hinter einem zweiten
    # Gedankenstrich: der Grund haengt hinter "nichts zu übernehmen — ".
    "antwort.bruecke_grund_zu_klein":
        "alle {n} gemessenen Gesicht(er) dieses Durchgangs liegen unter "
        "der Mindestgröße (größtes {kante} px, nötig sind {min_kante} px)",
    "antwort.bruecke_grund_zu_unscharf":
        "{n} Gesicht(er) in diesem Durchgang sind zu unscharf für eine "
        "Referenz (beste Schärfe {sharp}, nötig sind {unscharf_max})",
    "antwort.bruecke_grund_kein_gesicht":
        "kein messbares Gesicht in den {n} geprüften Bild(ern) dieses "
        "Durchgangs",
    "antwort.bruecke_grund_gedeckt":
        "{n} der geprüften Gesicht(er) sind fast identisch mit Referenzen, "
        "die {person} schon hat",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} der geprüften Gesicht(er) passen besser zu einer anderen "
        "Person als zu {person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} der geprüften Gesicht(er) waren nicht eindeutig {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} der geprüften Gesicht(er) waren in beidem schwach "
        "(Bildqualität und Identität)",
    "antwort.bruecke_grund_kein_crop":
        "keins der {n} Event(s) dieses Durchgangs hat einen "
        "Gesichtsausschnitt zum Prüfen",
    "antwort.bruecke_grund_keine_events":
        "in keinem Event dieses Durchgangs ist {person} bestätigt oder "
        "bester Treffer",
    "antwort.bruecke_grund_keine_referenzen":
        "{person} hat noch keine Referenzbilder zum Vergleichen",
    # ---- personlauf-Design (Nachzug) ----
    # Kachel-Titel und Kachel-Saetze des /personlauf-Laufflusses. Kachel 1/4,
    # die erste Saeulen-Marke und die Nachbar-Beschriftungen kommen wortgleich
    # aus dem Gesichts-Lernlauf (lernwizard.*) — hier stehen nur die sieben
    # personwizard-eigenen Neuzugaenge.
    "personwizard.kachel.sammeln": "Bilder sammeln",
    "personwizard.kachel.pruefen": "Bilder durchsehen",
    "personwizard.k1.satz":
        "Wähle, wen du anlernst und wie weit der Lauf zurückgeht "
        "&mdash; er sammelt die Bilder dann aus deinen eigenen "
        "Aufnahmen.",
    "personwizard.k2.satz":
        "Sammelt Ganzkörper-Bilder aus deinen Aufnahmen, und zwar nur "
        "aus Durchgängen, die ein Gesicht schon bestätigt hat.",
    "personwizard.k3.satz":
        "Der Schritt, der dich braucht: Jedes gesammelte Bild bekommt "
        "dein Ja oder Nein, bevor irgendetwas gelernt wird.",
    "personwizard.k4.satz":
        "Abgenommene Bilder trainieren sofort das Körpermodell "
        "&mdash; es erkennt Personen dann auch ohne sichtbares Gesicht.",
    "personwizard.such.titel": "Einen Personen-Lernlauf einrichten",
    # --------------------------------------------- routes/systemstat ---
    "systemstat.titel": "Systemauslastung",
    "systemstat.sub":
        "Gesamtauslastung dieser Maschine. Alle {takt} Sekunden eine neue "
        "Messung, aufbewahrt werden {stunden} Stunden. Eine Aufteilung nach "
        "Prozess gibt es hier nicht: Frigate läuft in einem eigenen "
        "Container, sein Anteil ist von hier aus nicht benennbar. Was diese "
        "Hardware nicht messen kann, sagt das \u2014 statt eine Null zu "
        "zeigen.",
    "systemstat.leer.titel": "Noch keine Messungen.",
    "systemstat.leer.hinweis":
        "Die erste Zeile entsteht rund {takt} Sekunden nach dem Start des "
        "Dienstes. Werte, die zwei Messungen brauchen (CPU, NPU, GPU), "
        "folgen eine Runde später.",
    "systemstat.block.hardware": "Hardware",
    "systemstat.block.erkennung": "Erkennung",
    "systemstat.block.live": "Live",
    "systemstat.nicht_verfuegbar": "nicht verfügbar",
    "systemstat.kein_prozent": "kein Prozentwert",
    "systemstat.ja": "ja",
    "systemstat.nein": "nein",
    "systemstat.verlauf.leer": "noch kein Verlauf",
    "systemstat.verlauf.aria": "die letzte Stunde",
    "systemstat.cpu.anzahl": "Kerne",
    "systemstat.cpu.kerne": "je Kern, gerade eben",
    "systemstat.kachel.platte": "Festplatte",
    "systemstat.ram.genutzt": "Belegt",
    "systemstat.ram.grafik": "Grafik (geteilter RAM)",
    "systemstat.ram.prozesse": "Prozesse",
    "systemstat.ram.limit": "Grenze",
    "systemstat.ram.cache": "Rückholbarer Cache",
    "systemstat.platte.frei": "Frei",
    "systemstat.platte.gesamt": "Gesamt",
    "systemstat.platte.cache": "Clip-Cache / Deckel",
    "systemstat.platte.frei_min": "Freihalten",
    "systemstat.gpu.engine": "Belebteste Engine",
    "systemstat.gpu.speicher": "Speicher",
    "systemstat.gpu.temperatur": "Temperatur",
    "systemstat.gpu_eigen.titel": "GPU (Anteil von suslik)",
    "systemstat.gpu.gesamt": "Ganze Karte",
    "systemstat.gpu_eigen.zeile": "Anteil von suslik",
    "systemstat.kachel.worker": "Analyse-Worker",
    "systemstat.worker.laeuft": "läuft",
    "systemstat.worker.ruht": "ruht, startet bei Bedarf",
    "systemstat.worker.tode": "Neustarts in 24 h",
    "systemstat.worker.zuletzt": "Letzter Tod",
    "systemstat.worker.ursache": "Letzte Ursache",
    "systemstat.kachel.durchsatz": "Durchsatz",
    "systemstat.durchsatz.tag": "Letzte 24 h",
    "systemstat.durchsatz.dauer": "Mittlere Dauer",
    "systemstat.kachel.rueckstau": "Rückstau",
    "systemstat.rueckstau.laeuft": "Holt gerade nach",
    "systemstat.rueckstau.fenster": "Rückschau-Fenster",
    "systemstat.kachel.live": "Live-Engine",
    "systemstat.live.waechter": "Wächter aktiv",
    "systemstat.live.supervisor": "Supervisor",
    "systemstat.stand": "Gemessen um {zeit}. Die Seite lädt sich selbst neu.",
    "systemstat.grund.erster_lauf":
        "wartet auf die zweite Messung \u2014 diese Zahl ist die Differenz "
        "zweier Messungen",
    "systemstat.grund.kein_geraet": "kein solches Gerät in dieser Maschine",
    "systemstat.grund.kein_zaehler":
        "das Gerät ist da, sein Treiber führt aber keinen Auslastungszähler",
    "systemstat.grund.gesperrt":
        "den Zähler gibt es, dieser Container darf ihn aber nicht lesen "
        "(Kernel-Performance-Ereignisse brauchen zusätzliche Rechte)",
    "systemstat.grund.werkzeug_fehlt":
        "das Abfrage-Werkzeug für dieses Gerät liegt nicht in diesem Image",
    "systemstat.grund.nicht_lesbar": "diese Quelle ließ sich nicht lesen",
    "systemstat.grund.kein_limit":
        "für diesen Container ist keine Speichergrenze gesetzt, also gibt "
        "es keinen Prozentwert",
    "systemstat.grund.kein_dienst":
        "diese Zahl kennt nur der laufende Dienst",
}
