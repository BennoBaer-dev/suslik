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
        "aussortiert — Bilder entfernt; die Gruppe bleibt gemerkt, "
        "damit erneutes Sammeln derselben Events still bleibt",
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
        "{n} aussortierte Gruppe(n) gemerkt — erneutes Sammeln "
        "derselben Events bleibt still",
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
        "Diese Gruppe aussortieren? Ihre Bilder werden entfernt; die "
        "Gruppe bleibt gemerkt, damit erneutes Sammeln derselben "
        "Events still bleibt.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Diese Gruppe aussortieren? Ihre Bilder werden entfernt, die "
        "ausstehende Benennung entfällt; die Gruppe bleibt gemerkt, "
        "damit erneutes Sammeln derselben Events still bleibt.",
    "lernanker.liste.knopf_verwerfen": "Aussortieren",
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
        "Misst jedes Referenzbild neu und sucht nach schwachen "
        "Bildern, Beinahe-Dubletten und verwechselten Gesichtern. "
        "Dauert etwa eine Minute und läuft im Hintergrund.",
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
    "qualitaet.lauf.reload_auto":
        "die Seite aktualisiert sich von selbst.",
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
    "lernwizard.k1.tag": "Tag {tag}",
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
        "{n} Gruppe aussortiert (keine brauchbaren Gesichter oder "
        "durch dich) &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} Gruppen aussortiert (keine brauchbaren Gesichter oder "
        "durch dich) &middot;",
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
        "Diese Gruppe löschen? Ihre Bilder werden entfernt, eine "
        "ausstehende Benennung entfällt; die Gruppe bleibt gemerkt, "
        "damit erneutes Sammeln derselben Events still bleibt.",
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
    "ui.hinweis.englisch": "Diese Seite ist noch nicht übersetzt — ihr Inhalt erscheint vorerst auf Englisch.",
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
    "js.unb.besucher_frage": "Als bekannten Fremden ignorieren? Er löst dann keine Meldungen mehr aus. (Jederzeit unten unter \"known visitors\" wieder aktivierbar.)",
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
    # js.vision.dirty_text: "Save" ist der (noch englische) Knopf der
    # Vision-Seite — bleibt woertlich, bis die Seite selbst einzieht.
    "js.vision.dirty_text": "Der Test würde die eben getippten Werte benutzen. Die Erkennung nutzt weiter die GESPEICHERTE Verbindung, bis Save gedrückt wird — ein grüner Test allein ändert nichts an den Urteilen.",
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
    "js.vision.prompt_zurueck": "Standard-Wortlaut wiederhergestellt — mit Save speichern",
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
}
