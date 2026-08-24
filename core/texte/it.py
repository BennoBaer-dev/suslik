# Muttersprachler-QS durchlaufen 19.08.2026 (Opus-Pruefagent je Sprache, Bericht im
# Session-Transkript); aktiv erst mit Registrierung in core/sprache.py (Stufe 1).
"""Italienische Uebersetzung der Referenz-Texte (gleiche Schluessel und
Reihenfolge wie en.py; verbindliche Vorlage: begriffe_tabellen.md, IT-Abschnitt;
Schluessel-Konvention <modul>.<block>.<rolle>, konzept_sprache.md v2)."""
T = {
    # ------------------------------------------------ routes/gesichter ---
    "gesichter.titel": "Persone conosciute",
    "gesichter.kopf.knopf_lernen": "Apprendi le persone",
    "gesichter.kopf.hinweis_lernen":
        "sessione di apprendimento guidata sulle tue registrazioni "
        "(fase di base)",
    "gesichter.kopf.satz":
        "Tutte le persone apprese e le loro immagini di riferimento. Puoi "
        "rimuovere singole immagini, assegnarne altre dai volti sconosciuti "
        "con il pulsante di ogni persona, oppure caricare una foto qui "
        "sotto, anche per una persona del tutto nuova.",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "images"; der
    # Plural-Feinschliff (eins/viele via t_n) ist eine BEWUSSTE spaetere
    # Verhaltensaenderung, nie Teil des Einzugs.
    "gesichter.galerie.bildzahl": "{n} immagini",
    "gesichter.galerie.knopf_entfernen": "rimuovi",
    "gesichter.galerie.knopf_aehnliche": "trova volti corrispondenti",
    "gesichter.galerie.knopf_qs": "Controlla la qualità",
    "gesichter.galerie.knopf_loeschen": "Elimina persona…",
    "gesichter.galerie.hinweis_leer": "ancora nessuna immagine",
    "gesichter.upload.titel": "Carica foto",
    "gesichter.upload.attr_person": "persona esistente…",
    "gesichter.upload.attr_neu": "o nuova persona",
    "gesichter.upload.knopf": "Carica",
    "gesichter.upload.hinweis":
        "Nuova persona: scrivi il nome nel campo di testo libero. "
        "Requisito: buffalo_l deve trovare un volto (altrimenti compare "
        "una richiesta per forzare il caricamento).",
    "gesichter.import.titel": "Importazione / risincronizzazione da Frigate",
    "gesichter.import.knopf": "Sincronizza i volti da Frigate",
    "gesichter.import.hinweis":
        "Recupera le immagini di riferimento che Frigate ha e questo "
        "archivio ancora no — incrementale, si può eseguire in "
        "qualsiasi momento senza rischi (niente di locale viene "
        "eliminato). La stessa importazione della procedura guidata "
        "iniziale, ora raggiungibile senza doverla rifare (ad es. dopo "
        "il ripristino delle impostazioni).",
    # ------------------------------------------------- routes/kameras ---
    "kameras.titel": "Telecamere",
    "kameras.banner.config_fehler":
        "Impossibile leggere la config di Frigate: {fehler}",
    "kameras.karte.verwenden": "usa questa telecamera",
    "kameras.karte.zonen_hinweis": "nessuna spuntata = tutti gli eventi",
    "kameras.karte.zonen_keine":
        "nessuna zona definita in Frigate — tutti gli eventi",
    "kameras.karte.rec_an": "rec ✓",
    "kameras.karte.rec_aus": "niente rec",
    "kameras.karte.pill_aus": "spenta in Frigate",
    # Byte-Treue: das HTML-Entity &mdash; stammt aus dem Original-Attribut
    # (title=...) und bleibt Stufe 0 exakt erhalten; huebscher machen ist
    # eine spaetere bewusste Aenderung, nie Teil des Einzugs.
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate non esegue alcun rilevamento persone su questo stream "
        "&mdash; qui non può arrivare nessun evento",
    "kameras.karte.pill_keine_detektion": "nessun rilevamento in Frigate",
    "kameras.leer.titel": "Nessuna telecamera trovata in Frigate.",
    "kameras.leer.hinweis":
        "Controlla che suslik possa raggiungere l’API di Frigate.",
    "kameras.fuss.knopf_speichern": "Salva telecamere",
    # -------------------------------------------------- routes/lernen ---
    "lernen.titel": "Suggerimenti — persone da registrare",
    "lernen.kopf.titel_offen": "Suggerimenti ({n})",
    "lernen.leer.titel": "Nessun suggerimento di registrazione in sospeso.",
    "lernen.leer.hinweis":
        "I volti nuovi di buona qualità (grandi, nitidi, frontali, "
        "riconosciuti con sicurezza o chiaramente estranei) compaiono "
        "qui automaticamente dopo l’analisi.",
    "lernen.karte.unbekannt": "Sconosciuto/Estraneo",
    # {sharp} kommt vorformatiert (:.0f) aus der Route — Formatspezifika
    # gehoeren nicht in Textwerte (Gate-Formatprobe kennt nur {name}).
    "lernen.karte.metrik_voll":
        "punteggio {score} · novità {novelty} · {bw}×{bh}px · frontalità "
        "{front} · nitidezza {sharp}",
    "lernen.karte.metrik_kurz": "punteggio {score}",
    "lernen.karte.link_video": "Video",
    "lernen.karte.knopf_add_person": "Aggiungi come {person}",
    "lernen.karte.attr_person": "come persona…",
    "lernen.karte.attr_neu": "o nuova persona",
    "lernen.karte.knopf_add": "Aggiungi",
    "lernen.karte.knopf_ablehnen": "Rifiuta",
    "lernen.galerie.titel": "Archivio di riferimento (Master)",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "references" —
    # Plural-Feinschliff (t_n) ist eine BEWUSSTE spaetere Aenderung.
    "lernen.galerie.bildzahl": "{n} riferimenti",
    "lernen.upload.titel_abschnitt": "Caricamento",
    "lernen.upload.titel": "Carica una tua foto nel Master",
    "lernen.upload.attr_person": "persona esistente…",
    "lernen.upload.attr_neu": "o nuova persona",
    "lernen.upload.knopf": "Carica",
    "lernen.upload.hinweis":
        "Nuova persona (ad es. Alex): scrivi il nome nel campo di testo "
        "libero. Requisito: buffalo_l deve trovare un volto (altrimenti "
        "compare una richiesta per forzare il caricamento). I PNG vengono "
        "convertiti in JPEG. Carica più foto da angolazioni diverse, una "
        "dopo l’altra.",
    # --------------------------------------------------- routes/areas ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Chip-Texte "All"/
    # "Default" sind zugleich Sicht-KENNUNGEN (Vergleich gegen aktiv +
    # URL-Wert aus core/areas.sicht_aufloesen) — Anzeige==Kennung ist erst
    # mit einer Entkopplung uebersetzbar; dazu zwei Absaetze mit Inline-
    # Markup mitten im Satz (<b>Default</b>, <b>view</b> + konditionalem
    # Satzteil), die auf den t_html-Weg spaeterer Stufen warten.
    "areas.titel": "Aree",
    "areas.kopf.sprung": "Vai a una vista:",
    "areas.verwaltung.titel": "Gestisci le aree",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "areas.verwaltung.camzahl.eins": "{n} telecamera",
    "areas.verwaltung.camzahl.viele": "{n} telecamere",
    "areas.verwaltung.attr_entfernen":
        "rimuovi quest’area — le sue telecamere tornano in Default",
    "areas.verwaltung.attr_neu": "nome della nuova area",
    "areas.verwaltung.knopf_anlegen": "Aggiungi area",
    "areas.verwaltung.titel_zuweisen": "Assegna le telecamere",
    "areas.verwaltung.satz_zuweisen":
        "Ogni telecamera appartiene esattamente a un’area; tutto ciò che "
        "non è assegnato resta in Default. Il salvataggio non richiede "
        "il riavvio del servizio.",
    "areas.verwaltung.pill_nicht_gesehen": "non vista",
    "areas.verwaltung.attr_nicht_gesehen":
        "assegnata in passato, al momento non presente in Frigate",
    "areas.verwaltung.hinweis_keine_kameras":
        "Nessuna telecamera nota — collega prima Frigate (Impostazioni).",
    "areas.verwaltung.knopf_speichern": "Salva aree",
    # -------------------------------------- routes/benachrichtigungen ---
    # NICHT eingezogen (bewusst): der Einleitungs-Absatz (<b>/data</b>,
    # <b>Test</b>) und der Topic-Praefix-Hinweis (<b>verifyd</b>) tragen
    # Inline-Markup mitten im Satz (t_html-Weg spaeterer Stufen); die
    # Karten-Titel Pushover/Telegram/MQTT sind reine Produktnamen; die
    # Option-WERTE aus/ha/direkt/beide und video/bild sind Config-Werte
    # (technische Bezeichner), nur ihre Erklaerzeile ist Text.
    "benachrichtigungen.titel": "Notifiche",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• memorizzato — lascia vuoto per mantenerlo",
    "benachrichtigungen.felder.secret_leer": "non impostato",
    "benachrichtigungen.felder.option_an": "attivo",
    "benachrichtigungen.felder.option_aus": "disattivato",
    "benachrichtigungen.alerts.titel": "Avvisi",
    "benachrichtigungen.alerts.hinweis":
        "Quali categorie di esito generano un avviso — su ogni canale "
        "(Pushover, Telegram, topic di scena MQTT). La notifica push "
        "della persona riconosciuta è governata dall’interruttore "
        "Presenza qui sotto; i topic dati MQTT (erkennung, heartbeat) "
        "pubblicano sempre finché la pubblicazione MQTT è attiva.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik conferma una persona diversa da quella di Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate ha etichettato qualcuno, suslik non ha visto alcun "
        "volto utilizzabile",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik ha riconosciuto qualcuno, Frigate no",
    "benachrichtigungen.kategorien.beide_unknown":
        "nessuna delle due parti ha identificato un volto",
    "benachrichtigungen.kategorien.erkannt":
        "è stata riconosciuta una persona conosciuta",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "un volto utilizzabile, ma nessuna conferma (possibile estraneo)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "un volto troppo debole o piccolo per identificarlo",
    "benachrichtigungen.alerts.stil_label": "Stile del testo degli avvisi:",
    "benachrichtigungen.alerts.stil_worte": "parole semplici",
    "benachrichtigungen.alerts.stil_worte_zahlen": "parole + punteggi grezzi",
    "benachrichtigungen.alerts.stil_hinweis":
        "come gli avvisi descrivono una corrispondenza (parole semplici "
        "è l’impostazione predefinita; numeri grezzi di coseno/punteggio "
        "solo se li rivuoi)",
    "benachrichtigungen.alerts.label_anwesenheit_push": "Push di presenza:",
    "benachrichtigungen.alerts.label_alert_cooldown":
        "Pausa tra gli avvisi (s):",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Pausa presenza (s):",
    "benachrichtigungen.alerts.label_szene_karenz": "Tolleranza scena (s):",
    "benachrichtigungen.pushover.label_token": "Token:",
    "benachrichtigungen.pushover.label_user": "Chiave utente:",
    "benachrichtigungen.pushover.knopf_test": "Prova Pushover",
    "benachrichtigungen.telegram.label_modus": "Modalità:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=disattivato · ha=tramite Home Assistant · direkt=bot "
        "diretto · beide=entrambi",
    "benachrichtigungen.telegram.label_inhalt": "Allegato:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=breve video, immagine se non disponibile · bild=solo "
        "immagine (nessuna transcodifica — più leggero su hardware "
        "modesto)",
    "benachrichtigungen.telegram.label_bot_token": "Token del bot:",
    "benachrichtigungen.telegram.label_chat_id": "Chat ID:",
    "benachrichtigungen.telegram.label_cooldown": "Pausa sconosciuti (s):",
    "benachrichtigungen.telegram.knopf_test": "Prova Telegram",
    "benachrichtigungen.mqtt.label_publish":
        "Pubblica i topic di riconoscimento:",
    "benachrichtigungen.mqtt.label_host": "Host:",
    "benachrichtigungen.mqtt.label_port": "Porta:",
    "benachrichtigungen.mqtt.label_user": "Utente:",
    "benachrichtigungen.mqtt.label_password": "Password:",
    "benachrichtigungen.mqtt.label_topic_praefix": "Prefisso topic:",
    "benachrichtigungen.mqtt.knopf_test": "Prova MQTT",
    "benachrichtigungen.fuss.knopf_speichern": "Salva + riavvia",
    # ----------------------------------------------- routes/aehnliche ---
    # {sim} kommt vorformatiert (:.2f) aus der Route (wie lernen.{sharp}).
    "aehnliche.kopf.titel": "Volti corrispondenti per {person}",
    "aehnliche.kopf.satz":
        "Due fonti: volti sconosciuti che somigliano a {person} e volti "
        "nuovi da eventi in cui il riconoscimento di {person} era già "
        "sicuro. Seleziona e applica.",
    "aehnliche.kopf.link_zurueck": "indietro",
    "aehnliche.unbekannt.titel": "Dai volti sconosciuti",
    "aehnliche.unbekannt.suche_titel":
        "Ricerca in corso — i riferimenti vengono riletti.",
    "aehnliche.unbekannt.suche_hinweis": "La pagina si aggiorna da sola.",
    "aehnliche.unbekannt.hinweis_leer":
        "Nessun volto sconosciuto simile in archivio.",
    "aehnliche.unbekannt.aehnlichkeit": "somiglianza {sim}",
    "aehnliche.unbekannt.knopf_hinzu": "Aggiungi i selezionati a {person}",
    "aehnliche.vorschlaege.titel":
        "Volti nuovi da eventi riconosciuti (7 giorni)",
    "aehnliche.vorschlaege.suche_titel":
        "Ricerca in corso — scansione degli eventi riconosciuti.",
    "aehnliche.vorschlaege.suche_hinweis":
        "La pagina si aggiorna da sola; risultato in uno o due minuti.",
    "aehnliche.vorschlaege.kachel_zeile": "{wann} · {kamera} · sim {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Consigliati",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutri — controlla l’immagine prima di applicare",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Chiaramente questa persona, ma la corrispondenza è sotto la "
        "soglia di confidenza oppure il ritaglio è più piccolo o meno "
        "nitido — decide un’occhiata.",
    "aehnliche.vorschlaege.knopf_alle": "Applica tutti i consigliati ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt": "Applica i selezionati a {person}",
    "aehnliche.vorschlaege.knopf_neu": "cerca di nuovo",
    "aehnliche.vorschlaege.fuss":
        "aggiornato al {stand} · consigliato = {person} con sicurezza + "
        "qualità da riferimento",
    "aehnliche.vorschlaege.hinweis_leer":
        "Nessuna corrispondenza trovata negli eventi riconosciuti.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Criteri: senza dubbio questa persona, nuovo rispetto "
        "all’archivio, abbastanza grande e nitido.",
    "aehnliche.vorrat.titel": "Novità dal materiale di apprendimento",
    "aehnliche.vorrat.hinweis":
        "Volti di alta qualità raccolti dalla sessione di apprendimento, "
        "valutati con la misura di qualità senza riferimenti e il consenso "
        "dello scenario. Restano in locale e non vengono mai esportati a Frigate.",
    "aehnliche.vorrat.kachel_zeile": "{wann} · {kamera} · corrispondenza {sim} · qualità {norm}",
    "aehnliche.vorrat.auch_anker": "anche in un gruppo di volti",
    "aehnliche.vorrat.knopf_gewaehlt": "Applica la selezione a {person}",
    # ------------------------------------------------- routes/frigate ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Beweis-Zeilen der
    # Verbindungs-, Kamera- und FR-Kachel (bis auf "state unknown") tragen
    # <b>/<br>/<a>/<code> mitten im Satz — t_html-Weg spaeterer Stufen;
    # ebenso der Seiten-Einleitungssatz (Link im Satz) und die Expert-
    # Zeilen. Der h2 "Frigate" ist reiner Produktname. Zwei JS-Statustexte
    # tragen \\u-Escape-Folgen im JS-Quelltext und warten auf den
    # window.T-Weg (Stufe 1). HTML-Entities (&mdash; &rsquo; &amp;) in
    # Werten sind Byte-Treue zum Original.
    "frigate.verbindung.titel": "Connessione",
    "frigate.verbindung.satz":
        "Il mio programma legge eventi e istantanee dal tuo Frigate "
        "tramite la sua API HTTP — non viene installato nulla sul lato "
        "Frigate.",
    "frigate.verbindung.knopf_aendern": "Cambia connessione",
    "frigate.verbindung.knopf_speichern": "Salva &amp; riavvia",
    "frigate.verbindung.knopf_abbrechen": "Annulla",
    "frigate.verbindung.hinweis_speichern":
        "il salvataggio riavvia brevemente il servizio; questo riquadro "
        "mostra poi in diretta se il nuovo indirizzo risponde",
    "frigate.kameras.titel": "Telecamere",
    "frigate.kameras.satz":
        "Quali telecamere di Frigate questo programma osserva e quali "
        "zone contano. Tutto il resto viene ignorato.",
    "frigate.kameras.beweis_keine_auswahl":
        "nessuna selezione di telecamere salvata — vengono usate tutte "
        "le telecamere offerte da Frigate",
    "frigate.kameras.knopf": "Gestisci telecamere",
    "frigate.sync.titel": "Sincronizzazione",
    "frigate.sync.satz":
        "Mantiene allineati i due archivi di volti: invia a Frigate i "
        "volti rivisti, importa ciò che ha solo Frigate &mdash; sempre "
        "su tua decisione, mai in automatico.",
    "frigate.sync.knopf": "Rivedi &amp; sincronizza",
    "frigate.fr.titel": "Il riconoscimento facciale di Frigate",
    "frigate.fr.satz":
        "Anche Frigate sa riconoscere i volti. Questo programma funziona "
        "con o senza &mdash; l’interruttore sta nella config di Frigate, "
        "letta qui in diretta così sai cosa può fare una "
        "sincronizzazione in questo momento.",
    "frigate.fr.beweis_unbekannt": "stato sconosciuto — {detail}",
    "frigate.js.url_fehlt": "inserisci l’URL di Frigate",
    "frigate.js.fehler": "errore:",
    # ------------------------------------------- routes/ereignisliste ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): die Tabellen-Kopfzellen
    # "Frigate" und "suslik" sind reine Produktnamen; die Kategorie-Labels
    # kommen aus webui.bausteine.KAT_LABELS (zentrale Quelle, eigene
    # Tranche); das Datumsformat %d.%m bleibt in der Route (B19-Stufe).
    "ereignisliste.offen.titel": "Casi aperti da etichettare ({n})",
    "ereignisliste.offen.satz":
        "Si riempie da sola: tutti gli eventi con volti che nessuno ha "
        "confermato e che non hai ancora etichettato. Vengono prima "
        "quelli in cui non è stato riconosciuto nessuno nelle vicinanze "
        "— sono quelli che vale la pena guardare. Dopo l’etichettatura "
        "la scheda sbiadisce e sparisce al caricamento successivo.",
    # {score} kommt vorformatiert (:.2f) aus der Route (Format-Regel §8.8).
    "ereignisliste.offen.frigate_mit": "Frigate: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate: —",
    # Stufe 0 = byte-treu: das Original sagt auch bei 1 "faces".
    "ereignisliste.offen.zeile_faces": "{n} volti · migliore: {beste}",
    "ereignisliste.offen.link_video": "Video",
    "ereignisliste.offen.kontext_erkannt":
        "riconosciuti nella stessa finestra temporale: {wer}",
    "ereignisliste.offen.kontext_fehlt":
        "nessun riconoscimento confermato nelle vicinanze",
    "ereignisliste.blaettern.neuer": "← più recenti",
    "ereignisliste.blaettern.aelter": "più vecchi →",
    "ereignisliste.offen.blaettern_stand":
        "Pagina {seite}/{max} ({n} aperti)",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} evento con volto debole nascosto — probabilmente nessun "
        "volto utilizzabile (e nessuna conferma nelle vicinanze).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} eventi con volti deboli nascosti — probabilmente nessun "
        "volto utilizzabile (e nessuna conferma nelle vicinanze).",
    "ereignisliste.offen.schwach_zeigen": "mostrali",
    "ereignisliste.offen.schwach_alle":
        "mostrati anche gli eventi con volti deboli —",
    "ereignisliste.offen.schwach_zurueck": "torna a quelli che contano",
    "ereignisliste.offen.leer_titel": "Niente di aperto — tutto etichettato.",
    "ereignisliste.offen.leer_hinweis":
        "I nuovi eventi non confermati con volti compaiono qui "
        "automaticamente.",
    "ereignisliste.titel": "Eventi",
    "ereignisliste.filter.alle_areas": "tutte le aree",
    "ereignisliste.filter.alle_kameras": "tutte le telecamere",
    "ereignisliste.filter.alle_personen": "tutte le persone",
    "ereignisliste.filter.alle_kategorien": "tutte le categorie",
    "ereignisliste.filter.knopf": "Filtra",
    "ereignisliste.filter.reset": "azzera",
    "ereignisliste.tabelle.blaettern_stand":
        "Pagina {seite}/{max} ({n} eventi)",
    "ereignisliste.tabelle.kopf_zeit": "Ora",
    "ereignisliste.tabelle.kopf_kamera": "Telecamera",
    "ereignisliste.tabelle.kopf_kategorie": "Categoria",
    "ereignisliste.tabelle.kopf_crop": "Ritaglio",
    "ereignisliste.tabelle.kopf_gt": "Conferma o correggi (GT)",
    # {score} vorformatiert; {cos} bleibt roh (Original druckt auch None).
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "log",
    "ereignisliste.tabelle.link_video": "video",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "video incompleto — giudicato dalla parte leggibile",
    "ereignisliste.tabelle.attr_kein_crop":
        "per questo evento non è stato conservato nessun volto utilizzabile",
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
    "konfiguration.kette.gesicht_titel": "Volto",
    "konfiguration.kette.gesicht_kosten":
        "analisi di base sul video registrato — sempre attiva",
    "konfiguration.kette.gesicht_zeitpunkt": "per evento",
    "konfiguration.kette.person_titel": "Persona (corpo)",
    "konfiguration.kette.person_kosten":
        "il passo locale più costoso (embedding del corpo sul tuo "
        "hardware)",
    "konfiguration.kette.person_zeitpunkt":
        "per evento, deciso sull’esito del passaggio",
    "konfiguration.kette.vision_titel": "Visione",
    "konfiguration.kette.vision_kosten":
        "una richiesta per passaggio al tuo endpoint di visione "
        "configurato",
    "konfiguration.kette.vision_zeitpunkt": "alla fine del passaggio",
    "konfiguration.kette.immer_an": "sempre",
    "konfiguration.kette.immer_hinweis": "(oggi non disattivabile)",
    "konfiguration.kette.gesicht_erkl":
        "il percorso del volto è la spina dorsale di ogni analisi — "
        "persona e visione dipendono dal suo esito sul passaggio",
    "konfiguration.kette.grund_person":
        "nessun modello persona appreso è ancora attivo",
    "konfiguration.kette.grund_vision":
        "il rilevamento visione è disattivato",
    "konfiguration.kette.grund_aus": "disattivato qui",
    "konfiguration.kette.status_aus": "stato: non in funzione ({grund})",
    "konfiguration.kette.zeile_kosten": "costo: {kosten}",
    "konfiguration.kette.titel": "Catena di riconoscimento",
    "konfiguration.kette.satz":
        "Quali riconoscitori sono attivi e in quale ordine. La condizione "
        "\"nur_wenn_gesicht_leer\" significa: il passo si attiva solo "
        "quando il percorso del volto NON è riuscito a confermare tutti "
        "nel passaggio — deciso sull’intero passaggio, mai su un singolo "
        "evento. Cambiare l’ordine è una fase futura; oggi la catena "
        "parte sempre dal percorso del volto.",
    "konfiguration.knopf_speichern": "Salva + riavvia",
    "konfiguration.kette_blatt.hinweis":
        "Le modifiche vengono tracciate (config_audit.jsonl); dopo il "
        "salvataggio il servizio si riavvia in modo pulito.",
    "konfiguration.titel": "Impostazioni avanzate",
    "konfiguration.kopf.satz1":
        "Le modifiche vengono tracciate (config_audit.jsonl); dopo il "
        "salvataggio il servizio si riavvia in modo pulito (attende la "
        "fine di un’analisi in corso).",
    "konfiguration.feld.option_an": "attivo",
    "konfiguration.feld.option_aus": "disattivato",
    "konfiguration.abschnitt_alle": "Tutti i parametri",
    "konfiguration.tabelle.kopf_parameter": "Parametro",
    "konfiguration.tabelle.kopf_wert": "Valore",
    "konfiguration.tabelle.kopf_bedeutung": "Significato",
    "konfiguration.knopf_setup": "Riesegui la procedura guidata iniziale",
    "konfiguration.abschnitt_readonly": "Sola lettura (console/yaml)",
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
    "lernanker.eimer.ok": "pulito",
    "lernanker.eimer.unbestaetigt": "non confermato",
    "lernanker.eimer.zu_duenn": "scarso",
    "lernanker.eimer.hart": "misto",
    "lernanker.bin.frontal": "Frontale",
    "lernanker.bin.links": "Sguardo a sinistra",
    "lernanker.bin.rechts": "Sguardo a destra",
    # {kamera} kommt je Kontext vorbehandelt aus der Route (attr_clip:
    # einzeln escaped; attr_kurz: Gesamtwert wird danach escaped).
    "lernanker.kachel.attr_clip": "{kamera} · det {det} · un clic apre il video",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "apri il video",
    "lernanker.kachel.grund_fehlt": "non giudicato",
    "lernanker.detail.gruppe": "Gruppo {pos} di {gesamt}",
    "lernanker.detail.frage": "Chi è?",
    "lernanker.badge.stuetz": "{n} volti ({phys} fisici)",
    "lernanker.badge.faces": "{n} volti",
    "lernanker.badge.durchgaenge": "{n} passaggi",
    "lernanker.badge.tage": "{n} giorno/i: {spanne}",
    "lernanker.badge.marge": "margine {marge}",
    "lernanker.link_zurueck": "torna a tutti i gruppi",
    "lernanker.detail.hinweis_klick":
        "fai clic su un volto per aprirne il video",
    "lernanker.detail.hinweis_auswahl":
        "fai clic su un’immagine per selezionarla o deselezionarla",
    "lernanker.detail.hinweis_pfeil": "il piccolo &#9654; apre il video",
    "lernanker.detail.weiter": "Prossimo gruppo &#8230;",
    "lernanker.detail.pflege_hinweis":
        "la cura dei riferimenti sta nella pagina Qualità",
    "lernanker.detail.verworfen":
        "eliminato da te — le immagini non ci sono più; il gruppo resta solo come voce",
    "lernanker.detail.dublette_hinweis":
        "controllo duplicati non disponibile (l’ancora precede la "
        "persistenza degli embedding) — i duplicati fisici vengono "
        "comunque filtrati",
    "lernanker.bekannt.system": "già nel tuo sistema",
    "lernanker.bekannt.anker": "nominato in un altro gruppo",
    "lernanker.detail.empfohlen": "Consigliati — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Non consigliati ({n}) — restano visibili, motivo su ogni "
        "immagine",
    "lernanker.detail.skip_weiter": "Salta questo gruppo",
    "lernanker.detail.skip_zurueck": "Salta — torna ai gruppi",
    "lernanker.detail.knopf_ja": "Sì, è {name}",
    "lernanker.detail.knopf_andere": "Qualcun altro &#8230;",
    "lernanker.detail.knopf_benennen_easy":
        "Dai un nome a questo gruppo &#8230;",
    "lernanker.detail.knopf_alle": "Seleziona tutti i consigliati",
    "lernanker.detail.knopf_keine": "Deseleziona tutto",
    "lernanker.detail.attr_name": "nome della persona (nuovo o esistente)",
    "lernanker.detail.knopf_benennen": "Dai un nome a questo gruppo",
    "lernanker.detail.knopf_adopt": "Acquisisci nel riconoscimento",
    "lernanker.js.fehler": "errore:",
    "lernanker.js.nicht_uebernommen": "non acquisito",
    "lernanker.js.nicht_gespeichert": "non salvato",
    "lernanker.liste.frage_lauf":
        "Eliminare la sessione {lid} e tutti i suoi dati? Questo rimuove "
        "definitivamente i suoi {n} gruppi — inclusi quelli nominati e "
        "scartati — e tutte le immagini estratte. I riferimenti già "
        "acquisiti nel riconoscimento restano. Non si può annullare.",
    "lernanker.liste.frage_alle":
        "Eliminare TUTTE le {alt} vecchie sessioni con i loro {n} gruppi "
        "e tutte le immagini estratte? Resta solo la sessione più "
        "recente {neuester}. I riferimenti già acquisiti nel "
        "riconoscimento restano. Non si può annullare.",
    "lernanker.liste.knopf_alte":
        "Elimina tutte le vecchie sessioni (mantieni {neuester})",
    "lernanker.liste.lauf_zeile":
        "Elimina una sessione — rimuove definitivamente tutti i suoi "
        "gruppi e le immagini estratte (i riferimenti già acquisiti "
        "restano):",
    "lernanker.liste.verworfen":
        "{n} gruppi eliminati da te (immagini rimosse, restano solo come voce)",
    "lernanker.titel": "Gruppi di ancore",
    "lernanker.liste.leer":
        "Non ci sono ancore — le costruisce una sessione di "
        "apprendimento (Preparazione → Estrazione → Raggruppamento).",
    "lernanker.liste.leer_link":
        "Apri la pagina della sessione di apprendimento",
    "lernanker.liste.kopf":
        "{n} gruppi da {ges} volti adatti come ancora — {ok} puliti, "
        "{rest} da rivedere (attenuati, con il motivo sul badge). Apri "
        "un gruppo per rivederlo e dargli un nome — i gruppi nominati "
        "vengono acquisiti nel riconoscimento lì stesso (pulsante "
        "Acquisisci).",
    "lernanker.liste.kopf_link": "Torna alla sessione di apprendimento",
    "lernanker.liste.mehr": "+{n} altri volti",
    "lernanker.liste.dublette":
        "stesso gruppo di {anker} — estratto di nuovo da una sessione "
        "più recente; dagli un nome lì",
    "lernanker.liste.knopf_review": "Rivedi la denominazione",
    "lernanker.liste.knopf_view": "Vedi il gruppo",
    "lernanker.liste.knopf_benennen": "Dai un nome a questi {n} volti",
    "lernanker.liste.frage_verwerfen":
        "Eliminare questo gruppo? Le sue immagini vengono rimosse. Non si può annullare.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Eliminare questo gruppo? Le sue immagini vengono rimosse e la denominazione in sospeso viene annullata. Non si può annullare.",
    "lernanker.liste.knopf_verwerfen": "Elimina",
    # ---------------------------------------------- routes/syncauswahl ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): FR_AUS_HINWEIS kommt aus
    # sync_refs (zentrale Quelle, eigene Tranche); die Satzreste mit
    # <a>-Link mitten im Satz (Read-only-Karte, "… more (full list in the
    # diagnosis)") bleiben literal; die Zaehler-Hauptzeile beginnt nach
    # der <b>-Zahl (Split an der Markup-Grenze — neue Gattung §8).
    "syncauswahl.titel": "Rivedi &amp; sincronizza — riferimenti verso Frigate",
    "syncauswahl.kopf.satz":
        "Frigate fa passare ogni riferimento caricato nel proprio "
        "rilevatore di volti e rifiuta le immagini in cui non trova un "
        "volto. Questa pagina controlla prima la stessa cosa, ti mostra "
        "ogni candidato e invia solo ciò che selezioni.",
    "syncauswahl.fehler.titel": "Candidati non disponibili",
    "syncauswahl.fehler.satz":
        "La lista dei candidati richiede un Frigate raggiungibile — il "
        "suo archivio di volti è una metà del confronto.",
    "syncauswahl.link_diagnose_auf": "apri la diagnosi",
    "syncauswahl.link_diagnose": "diagnosi",
    "syncauswahl.link_system": "torna a Sistema",
    "syncauswahl.kachel.frigate_abgelehnt": "Frigate ha rifiutato: {fehler}",
    "syncauswahl.kachel.pruefe": "controllo in corso …",
    "syncauswahl.kachel.vorpruefung_ok": "controllo preliminare ok",
    "syncauswahl.kachel.wohl_abgelehnt":
        "probabilmente verrebbe rifiutata: {grund}",
    "syncauswahl.kachel.kein_gesicht": "nessun volto rilevabile",
    "syncauswahl.kachel.kein_grund": "nessun motivo indicato",
    "syncauswahl.kachel.senden": "invia",
    "syncauswahl.kachel.knopf_skip": "salta",
    "syncauswahl.kachel.attr_skip":
        "Non inviare mai questa immagine — memorizzata, anche la "
        "sincronizzazione automatica la salta",
    "syncauswahl.kachel.knopf_restore": "ripristina",
    "syncauswahl.kachel.attr_restore":
        "Rimetti questa immagine nella lista dei candidati",
    "syncauswahl.geloescht.satz_import":
        "proveniva da Frigate e lì ora non c’è più",
    "syncauswahl.geloescht.satz_export":
        "era stata inviata esattamente con questo nome e lì ora non "
        "c’è più",
    "syncauswahl.geloescht.badge": "eliminata in Frigate",
    "syncauswahl.knopf_anbieten": "proponi di nuovo",
    "syncauswahl.geloescht.attr_anbieten":
        "Rimettila nella lista dei candidati — la prossima "
        "sincronizzazione (manuale o automatica) la invia di nuovo",
    "syncauswahl.geloescht.knopf_respekt": "rispetta l’eliminazione",
    "syncauswahl.geloescht.attr_respekt":
        "Ricorda che questa immagine deve restare fuori da Frigate",
    "syncauswahl.api.badge": "{person} — inviata in precedenza",
    "syncauswahl.api.attr_anbieten":
        "Rimettila nella lista dei candidati (invia una seconda copia "
        "se Frigate ha ancora la prima)",
    "syncauswahl.fr.titel_unbekannt":
        "Riconoscimento facciale di Frigate: sconosciuto",
    "syncauswahl.fr.satz_unbekannt":
        "suslik non è riuscito a leggerlo da Frigate in questo momento "
        "— {detail}. L’invio potrebbe comunque funzionare; in ogni caso "
        "l’ultima parola spetta a Frigate.",
    "syncauswahl.fr.titel_an": "Riconoscimento facciale di Frigate: attivo",
    "syncauswahl.fr.satz_an":
        "(letto da Frigate al caricamento di questa pagina) — accetta "
        "il caricamento dei riferimenti.",
    "syncauswahl.fr.titel_aus":
        "Riconoscimento facciale di Frigate: disattivato",
    "syncauswahl.bilanz.titel": "Bilancio",
    "syncauswahl.bilanz.hauptzeile":
        "immagini di riferimento · {beide} già in Frigate · {bereit} "
        "pronte al trasferimento",
    "syncauswahl.bilanz.abgelehnt": "{n} rifiutate da Frigate",
    "syncauswahl.bilanz.geloescht": "{n} eliminate in Frigate",
    "syncauswahl.bilanz.exportiert":
        "{n} inviate in precedenza (Frigate le ha rinominate)",
    "syncauswahl.bilanz.abgewaehlt": "{n} deselezionate",
    "syncauswahl.bilanz.vorrat": "{n} riferimento/i del materiale solo in locale (basati su embedding, non trasferibili)",
    "syncauswahl.bilanz.nur_frigate": "{n} solo in Frigate",
    "syncauswahl.bilanz.je_person": "In Frigate, per persona:",
    # echter Plural schon im Original — t_n loest .eins/.viele auf.
    "syncauswahl.bilanz.kandidaten.eins": "{n} candidato",
    "syncauswahl.bilanz.kandidaten.viele": "{n} candidati",
    "syncauswahl.bilanz.vorpruefung": "{n} superano il controllo preliminare",
    "syncauswahl.bilanz.gewaehlt_wort": "selezionati",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "{n} verrebbero probabilmente rifiutati da Frigate "
        "(deselezionati, ma puoi comunque inviarli).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "{n} erano già stati rifiutati da Frigate (deselezionati; "
        "selezionandone uno si riprova).",
    "syncauswahl.pruef.fehler":
        "il controllo preliminare non è partito: {fehler} — le immagini "
        "senza esito restano selezionate.",
    "syncauswahl.pruef.laeuft.eins":
        "controllo di {n} immagine … {fertig}/{gesamt} (questa pagina "
        "si ricarica al termine)",
    "syncauswahl.pruef.laeuft.viele":
        "controllo di {n} immagini … {fertig}/{gesamt} (questa pagina "
        "si ricarica al termine)",
    "syncauswahl.sperre.titel": "La modalità sola lettura è attiva",
    "syncauswahl.sperre.satz":
        "suslik al momento non scrive su Frigate.",
    "syncauswahl.knopf_alle": "Seleziona tutto",
    "syncauswahl.knopf_keine": "Deseleziona tutto",
    "syncauswahl.knopf_transfer": "Trasferisci {n} selezionati a Frigate",
    "syncauswahl.leer.titel": "Niente da inviare",
    "syncauswahl.leer.satz":
        "Ogni riferimento è già arrivato a Frigate oppure è deselezionato.",
    "syncauswahl.leer.zusatz":
        "Le sezioni qui sotto elencano ciò che non si può semplicemente "
        "trasferire.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} probabilmente rifiutati",
    "syncauswahl.gruppe.prueft": "{n} ancora in controllo",
    "syncauswahl.geloescht.zusatz": "— decidi tu",
    "syncauswahl.geloescht.satz":
        "Queste sono ancora nel tuo archivio, ma Frigate non le ha più "
        "con il nome con cui erano state salvate. suslik non le rinvia "
        "mai senza una tua decisione: eliminare un volto in Frigate può "
        "essere una scelta voluta. Proponila di nuovo per farne di "
        "nuovo un candidato normale — da quel momento la prossima "
        "sincronizzazione, anche quella automatica, la carica. Rispetta "
        "l’eliminazione per tenerla fuori definitivamente.",
    "syncauswahl.aufklapp": "— mostra",
    "syncauswahl.api.titel":
        "{n} esportate in precedenza — Frigate le conserva con nomi "
        "suoi",
    "syncauswahl.api.satz":
        "Queste sono state caricate tramite l’API di Frigate, e Frigate "
        "rinomina ogni riferimento che accetta. suslik quindi non può "
        "capire dal nome se ci sono ancora — nessun conteggio su questa "
        "pagina può dimostrarlo. Non viene rinviato nulla in automatico; "
        "se sai che una manca, proponila di nuovo (questo invia una "
        "seconda copia se la prima c’è ancora).",
    "syncauswahl.api.vergleich":
        "{person}: {n} inviate per questa via · Frigate al momento ha "
        "{bestand} immagini",
    "syncauswahl.import.zeile.eins": "{n} immagine:",
    "syncauswahl.import.zeile.viele": "{n} immagini:",
    "syncauswahl.import.mehr": "… e altre {n}",
    "syncauswahl.import.satz":
        "Frigate ha queste immagini di riferimento, suslik no. "
        "L’importazione le copia nel tuo archivio; in Frigate non "
        "cambia nulla.",
    "syncauswahl.import.warnung":
        "Questa lista può includere caricamenti fatti da te: Frigate "
        "rinomina ogni riferimento che accetta, quindi suslik non può "
        "distinguerli dai volti aggiunti direttamente in Frigate. "
        "Reimportarli duplicherebbe il contenuto.",
    "syncauswahl.import.knopf": "Importali in suslik",
    "syncauswahl.raus.satz":
        "Memorizzate di proposito: restano nel tuo archivio ma non "
        "vengono mai inviate a Frigate, nemmeno dalla sincronizzazione "
        "automatica. Ripristina ne rimette una nella lista dei "
        "candidati.",
    "syncauswahl.alter.unbekannt": "età sconosciuta",
    "syncauswahl.alter.sekunden": "{s} s fa",
    "syncauswahl.alter.minuten": "{m} min fa",
    "syncauswahl.alter.stunden": "{h} h {m} min fa",
    "syncauswahl.ergebnis.titel": "Ultimo trasferimento",
    "syncauswahl.ergebnis.stopp": "interrotto:",
    "syncauswahl.ergebnis.wand":
        "stesso errore tre volte di fila: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "caricata — {bild}",
    "syncauswahl.ergebnis.zaehler": "{hoch} caricate · {weg} non accettate",
    "syncauswahl.ergebnis.auswahl": "su {n} selezionate",
    "syncauswahl.ergebnis.uebersprungen": "{n} deselezionate (saltate)",
    "syncauswahl.ergebnis.dauer": "durata {n} s",
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
        "Per ora funziona solo con una GPU — stiamo lavorando a "
        "un’opzione CPU ma non possiamo prometterla.",
    "live.hinweis_cpu":
        "Modalità CPU: qui le sentinelle costano caro — il controllo "
        "rapido richiede in genere 1–2 s (una build GPU reagisce in "
        "meno di un secondo) e più sentinelle si rallentano a vicenda. "
        "Quante attivarne decidi tu; consigliamo di iniziare con una.",
    "live.zeile.alter": "({tage} giorno/i fa)",
    "live.test.zeile":
        "test sorgente {wann}: {aufloesung} → {skala}, {bilder_s} frame/s",
    "live.test.durchsatz":
        "(portata, non frequenza di consegna — riesegui il test sorgente)",
    "live.test.provider": "provider {provider}",
    "live.test.sw": "(decodifica software)",
    "live.test.entwertet":
        "— INVALIDATO: la sorgente è cambiata dopo questo test",
    "live.test.fehlgeschlagen":
        "ultimo test sorgente FALLITO ({wann}): {fehler}",
    "live.messung.zeile": "carico misurato il {wann}: {text}",
    "live.messung.veraltet":
        "— OBSOLETA: la sorgente è cambiata dopo questa misurazione, "
        "misura di nuovo",
    "live.messung.fehlgeschlagen":
        "ultima misurazione del carico FALLITA ({wann}): {fehler}",
    "live.zaehler.auftritte": "{n} apparizioni",
    "live.zaehler.trigger": "{n} trigger",
    "live.zaehler.alerts": "{n} avvisi",
    "live.zaehler.letzter": "ultimo trigger {zeit}",
    "live.zaehler.kopf": "dall’avvio del motore:",
    "live.engine.titel_aus": "Motore live: fermo",
    "live.engine.satz_aus":
        "Nessun heartbeat dal processo del motore. I riquadri mostrano "
        "le impostazioni salvate; attivazione, prova contro una "
        "sentinella in funzione e misurazioni del carico richiedono il "
        "motore — il servizio lo avvia automaticamente appena almeno "
        "una sentinella è attivata.",
    "live.engine.cpu_mit_limit":
        "CPU di suslik adesso: {kerne} di {limit} core consentiti "
        "(intero container: sentinelle, analisi, servizio)",
    "live.engine.cpu_ohne_limit":
        "CPU di suslik adesso: {kerne} core (intero container: "
        "sentinelle, analisi, servizio)",
    "live.engine.rss": "RSS del motore {rss} MB",
    "live.engine.grundkosten": "costo base {mb} MB",
    "live.engine.je_stream": "{mb} MB per stream ({quelle})",
    "live.engine.je_stream_fehlt":
        "RAM per stream non ancora misurata su questa macchina",
    "live.engine.ram_frei": "{mb} MB di RAM liberi ({quelle})",
    "live.engine.ram_unlesbar": "RAM: nessun limite del container leggibile",
    "live.engine.detektor": "rilevatore {ms} ms/frame ({quelle})",
    "live.engine.drossel":
        "livello di rallentamento {stufe}, utilizzo {auslastung}",
    "live.engine.rest":
        "con un altro stream: resterebbero ~{mb} MB di RAM",
    "live.engine.rest_warnung":
        "— SOTTO la soglia di sicurezza, nessun altro posto",
    "live.engine.kapazitaet":
        "capacità: fino a {n} sentinella/e (tetto rigido {hart}) — "
        "limitata da: {grund}",
    "live.engine.hart": "tetto rigido {hart} sentinelle",
    "live.engine.titel_standalone":
        "Motore live: in funzione (rilevato motore autonomo)",
    "live.engine.titel_an": "Motore live: in funzione",
    "live.gruppe.laufend": "In funzione",
    "live.gruppe.bereit": "Pronte",
    "live.gruppe.rest": "Non impostate",
    "live.gruppe.versteckt": "Nascoste",
    "live.gruppe.ohne_area": "Senza area",
    "live.kachel.attr_fremd":
        "impostata qui, ma questa telecamera al momento non è in Frigate",
    "live.kachel.pill_fremd": "non in Frigate",
    "live.kachel.attr_detect":
        "stream detect di Frigate — la risoluzione reale dello stream "
        "compare dopo che il servizio lo ha sondato o dopo un test "
        "sorgente",
    "live.knopf_konfigurieren": "Configura",
    "live.knopf_test": "Esegui test sorgente",
    "live.knopf_messung": "Misura il carico",
    "live.knopf_enable": "Attiva",
    "live.knopf_disable": "Disattiva",
    "live.knopf_zeigen": "Mostra",
    "live.knopf_verstecken": "Nascondi",
    "live.banner.kameraliste":
        "Impossibile leggere l’elenco telecamere di Frigate: {fehler}",
    "live.schalter.ungruppiert": "vista non raggruppata",
    "live.schalter.area": "raggruppa per area",
    "live.sperre.cpu_titel": "Modalità CPU",
    "live.sperre.titel": "Non disponibile su questa build",
    "live.sperre.satz":
        "Le sentinelle live richiedono una build GPU — vanno bene la "
        "grafica integrata Intel (immagini gpu / gpu-legacy), una "
        "scheda NVIDIA (immagine cuda) o una scheda AMD (immagine "
        "rocm).",
    "live.sperre.cpu_only":
        "Non sono disponibili sull’immagine solo CPU.",
    "live.erklaer.titel":
        "Sentinelle live — reazione immediata sullo stream della "
        "telecamera",
    "live.erklaer.satz1":
        "Una sentinella live si collega direttamente allo stream di una "
        "telecamera e reagisce mentre la persona è ancora "
        "nell’inquadratura: il primo volto avvia un controllo e, dopo "
        "il numero impostato di rilevamenti coerenti, parte un segnale "
        "verificato — l’obiettivo è sotto il secondo (misurati 199–801 "
        "ms sul sistema di riferimento). Usala per attivare le "
        "automazioni di casa, ad es. via MQTT.",
    "live.erklaer.link": "Scopri di più: come funzionano le sentinelle live",
    "live.titel": "Sentinelle live",
    "live.leer.titel": "Nessuna telecamera trovata.",
    "live.leer.hinweis":
        "Imposta prima la connessione a Frigate — i riquadri compaiono "
        "per ogni telecamera.",
    "live.knopf_speichern": "Salva",
    "live.detail.titel": "Sentinella live — {name}",
    "live.abschnitt.quelle": "Sorgente",
    "live.quelle.proxy":
        "restream go2rtc tramite Frigate (predefinito, consigliato)",
    "live.quelle.direct": "URL producer della telecamera scoperto via go2rtc",
    "live.quelle.url": "un URL di stream che inserisci tu",
    "live.detail.url_label": "URL dello stream (solo sorgente 'url'):",
    "live.detail.url_hinweis":
        "le credenziali nell’URL sono mascherate ovunque vengano "
        "mostrate — lascia il campo com’è per mantenere l’URL salvato, "
        "oppure incollane uno nuovo",
    "live.detail.quelle_hinweis":
        "Cambiare la sorgente invalida il test sorgente — rieseguilo "
        "prima di attivare.",
    "live.abschnitt.aufloesung": "Risoluzione di elaborazione",
    "live.hoehe.default": "predefinita (1080p)",
    "live.hoehe.h360":
        "360p — ripiego per GPU deboli, il nome scatta più tardi di "
        "tutte (misurato)",
    "live.hoehe.h720": "720p — decodifica più leggera, il nome scatta più tardi",
    "live.hoehe.h1080":
        "1080p — punto ideale (misurato: nome ~2,4 s prima rispetto a 720p)",
    "live.hoehe.h1440": "1440p — nessun guadagno misurato rispetto a 1080p",
    "live.hoehe.h2160":
        "2160p — 4K nativo, guadagno marginale, costo di decodifica "
        "massimo",
    "live.abschnitt.alarm": "Catena di avviso",
    "live.detail.ende_label": "Fine dopo assenza di volto (s):",
    "live.detail.ende_hinweis":
        "un’apparizione termina dopo questi secondi senza volto (3–120)",
    "live.detail.scharf_label": "Riarmo dopo (s):",
    "live.detail.scharf_hinweis":
        "secondi minimi tra gli avvisi — con qualcuno presente avvisa "
        "di nuovo dopo questo tempo; 0 = ogni trigger avvisa (0–3600)",
    "live.abschnitt.kanaele": "Canali di notifica",
    "live.detail.namensschaetzung":
        "Gli avvisi includono una stima preliminare del nome "
        "(\"probabilmente X\") quando il volto corrisponde a una "
        "persona conosciuta — mai salvata, mai usata per "
        "l’apprendimento.",
    "live.abschnitt.test": "Prova &amp; misura",
    "live.detail.gesperrt_hinweis":
        "prova e misurazione non sono disponibili finché le sentinelle "
        "live sono bloccate su questa macchina — la nota in cima a "
        "questa pagina spiega il perché.",
    "live.knopf_messung_lang": "Misura il carico (15–30 s)",
    "live.detail.messung_hinweis":
        "durante la misurazione del carico le altre sentinelle vengono "
        "messe in pausa",
    "live.detail.link_zurueck": "torna alla panoramica",
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
    "erkennung.titel": "Riconoscimento",
    "erkennung.kopf.satz":
        "I quattro modi in cui il tuo sistema può riconoscere qualcuno "
        "— ognuno ha la sua scheda: attivalo, controlla che funzioni, "
        "impostalo. L’interruttore Live agisce subito; le modifiche a "
        "corpo e visione si applicano con Salva + riavvia.",
    "erkennung.kipp.label": "Attivo",
    "erkennung.kipp.attr_verriegelt":
        "sempre attivo — ogni altro metodo si basa sull’esito del volto",
    "erkennung.link_how": "Come funziona &#8230;",
    "erkennung.live.titel": "Sentinelle live",
    # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze, Fragmente
    # duerfen klein beginnen.
    "erkennung.live.beweis_prefix": "sorveglia",
    "erkennung.live.beweis_zaehler": "{an} di {ges}",
    "erkennung.live.beweis_suffix": "telecamere impostate",
    "erkennung.live.beweis_keine_laufend":
        "telecamere impostate, nessuna in funzione",
    "erkennung.live.beweis_keiner": "nessuna sentinella ancora impostata",
    "erkennung.live.expert_schalter":
        "disattivare ferma ogni sentinella in funzione; attivare avvia "
        "tutte le sentinelle impostate (resta valido il controllo per "
        "telecamera)",
    "erkennung.live.link_prokamera": "controllo per telecamera",
    "erkennung.live.knopf_kameras": "Scegli le telecamere …",
    "erkennung.knopf_register_face": "Registra volto …",
    "erkennung.gesicht.titel": "Riconoscimento facciale",
    "erkennung.gesicht.satz":
        "Il metodo più preciso: ogni passaggio viene confrontato con i "
        "volti delle persone che hai fatto conoscere al sistema. È la "
        "spina dorsale — corpo e visione dipendono dal suo esito sul "
        "passaggio, perciò oggi non ha interruttore di spegnimento.",
    "erkennung.gesicht.beweis_personen": "{n} persone",
    "erkennung.gesicht.beweis_bilder": "{n} immagini di riferimento",
    "erkennung.gesicht.knopf_verwalten": "Gestisci le persone …",
    "erkennung.koerper.titel": "Riconoscimento del corpo",
    "erkennung.koerper.satz":
        "Riconosce chi vive in casa anche quando nessun volto è "
        "visibile, dalla corporatura e dalla postura — apprende da solo "
        "dalle immagini riviste.",
    "erkennung.koerper.beweis_kein_modell":
        "ancora nessun modello persona — prima servono apprendimento e "
        "revisione",
    "erkennung.status.kein_modell":
        "non in funzione (nessun modello persona appreso è ancora attivo)",
    "erkennung.status.hier_aus": "non in funzione (disattivato qui)",
    "erkennung.status.vision_aus":
        "non in funzione (il rilevamento visione è disattivato)",
    "erkennung.koerper.link_modell": "stato del modello",
    "erkennung.koerper.knopf_status": "Stato del modello …",
    "erkennung.koerper.knopf_register": "Registra corpo …",
    "erkennung.vision.titel": "Visione AI",
    "erkennung.vision.beta": "Beta",
    "erkennung.vision.satz":
        "Un’AI per immagini come arbitro nei casi difficili. Richiede "
        "un endpoint di modello (locale o a pagamento) — ogni controllo "
        "costa richieste.",
    "erkennung.vision.beweis_an": "endpoint collegato",
    "erkennung.vision.beweis_aus": "nessun endpoint collegato",
    "erkennung.vision.knopf_connect": "Collega un modello …",
    "erkennung.vision.knopf_register": "Registra visione …",
    "erkennung.abschnitt_property": "Impostazione della proprietà",
    "erkennung.areas.titel": "Aree",
    "erkennung.areas.satz":
        "Quali punti della proprietà contano: disegna le aree così gli "
        "avvisi scattano solo dove ti interessa — il vialetto conta, la "
        "strada dietro la recinzione no.",
    "erkennung.areas.beweis_zahl": "aree definite",
    "erkennung.areas.beweis_keine": "ancora nessun’area — conta tutto",
    "erkennung.areas.knopf": "Gestisci aree &#8230;",
    "erkennung.knopf_speichern": "Salva + riavvia",
    # --------------------------------------------------- routes/faces ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): der dim-Einleitungs-
    # Satz traegt einen <a>-Link mitten im Satz (t_html-Weg spaeterer
    # Stufen). Das Datumsformat %d.%m. %H:%M der Stand-Zeile bleibt in
    # der Route (B19/§8.9); {wann}/{n} kommen vorformatiert (§8.8).
    "faces.titel": "Volti",
    "faces.link_how": "Come funziona &#8230;",
    "faces.bekannt.titel": "Persone conosciute",
    "faces.bekannt.knopf_verwalten": "Gestisci le persone &#8230;",
    "faces.bekannt.knopf_register": "Registra volto &#8230;",
    "faces.bekannt.leer":
        "ancora nessuna persona appresa — registra il primo volto qui "
        "sopra",
    # Zaehler mit <b>-Zahl (§8.10): Split an der Markup-Grenze.
    "faces.bekannt.beweis_personen": "{n} persone",
    "faces.bekannt.beweis_bilder": "{n} immagini di riferimento",
    "faces.lernen.titel": "Apprendimento",
    "faces.lernen.knopf_start": "Avvia apprendimento &#8230;",
    "faces.lernen.knopf_review": "Rivedi i suggerimenti &#8230;",
    "faces.lernen.beweis_offen": "suggerimenti in attesa di revisione",
    "faces.lernen.beweis_leer":
        "niente in attesa — il sistema continua a estrarre da solo",
    "faces.lernen.satz": "Rivedi ciò che le telecamere hanno estratto.",
    "faces.unbekannt.titel": "Sconosciuti",
    "faces.unbekannt.knopf": "Rivedi gli sconosciuti &#8230;",
    "faces.unbekannt.beweis_offen": "visitatori sconosciuti ricorrenti",
    "faces.unbekannt.beweis_leer": "nessun visitatore sconosciuto ricorrente",
    "faces.unbekannt.satz": "Visitatori ancora senza nome.",
    "faces.qualitaet.titel": "Qualità delle immagini",
    "faces.qualitaet.stand": "ultimo controllo {wann} &middot; {n} segnalazioni",
    # EIN Schluessel fuer Popup-Titel UND grossen Knopf (wortgleich im
    # Original — bewusste Wiederverwendung, kein Duplikat).
    "faces.qualitaet.knopf_check": "Controlla la qualità delle mie immagini",
    "faces.qualitaet.popup_satz":
        "Rimisura ogni immagine di riferimento (inclusa la qualità del volto) e "
        "cerca quelle deboli, i quasi-duplicati e i volti scambiati. Richiede "
        "alcuni minuti a seconda del numero di immagini e gira in background.",
    "faces.qualitaet.label_alle": "Tutte le persone",
    "faces.qualitaet.label_eine": "Una persona:",
    "faces.qualitaet.knopf_start": "Avvia controllo",
    "faces.qualitaet.knopf_abbrechen": "Annulla",
    "faces.qualitaet.knopf_ergebnisse": "Ultimi risultati &#8230;",
    "faces.qualitaet.satz": "Trova immagini deboli o scambiate.",
    # ----------------------------------------------- routes/qualitaet ---
    # NICHT eingezogen (bewusst, Stufe-0-Grenzen): der Luecken-Block
    # ("no X and no Y yet …" — Satzteil-Splicing ueber " and no ".join,
    # §8.3), die filt-Zeile (showing only <b>X</b> + <a>-Link im Satz,
    # §8.1), der Ergebnis-Satz des Funde-Zweigs (", "/" and "-Join der
    # <b>-Zaehler-Fragmente, §8.3) und der JS-Text '" selected"' in
    # qgZaehl (window.T, Stufe 1). Datumsformate %d.%m. %H:%M bleiben in
    # der Route (B19/§8.9); {fehler} kommt escaped+gesliced aus der Route
    # (Slice-vor-Format-Stelle [:180], §8.14 — nur markiert).
    "qualitaet.kopf.titel": "Qualità — archivio di riferimento",
    "qualitaet.kopf.hinweis":
        "tocca una persona qui sotto per vedere tutte le sue immagini "
        "con quelle deboli contrassegnate.",
    "qualitaet.kopf.stand": "Aggiornato al: {stand} · {n} riferimenti",
    "qualitaet.kopf.knopf_neu": "Ricontrolla ora",
    "qualitaet.lauf.fehler":
        "ultimo controllo FALLITO: {fehler} &mdash; avvialo di nuovo.",
    "qualitaet.lauf.checking": "controllo dell’immagine {i} di {n} &hellip;",
    "qualitaet.lauf.reload_person":
        "poi ricarica questa pagina per il risultato aggiornato.",
    "qualitaet.lauf.abgebrochen":
        "l’ultimo controllo non è arrivato in fondo (riavvio del "
        "servizio o interruzione) &mdash; avvialo di nuovo.",
    "qualitaet.tabelle.kopf_person": "persona",
    "qualitaet.tabelle.kopf_bilder": "immagini",
    "qualitaet.tabelle.kopf_gut": "buone",
    "qualitaet.tabelle.kopf_mittel": "discrete",
    "qualitaet.tabelle.kopf_unter": "sotto soglia",
    "qualitaet.tabelle.kopf_links": "&larr; sinistra",
    "qualitaet.tabelle.kopf_front": "frontale",
    "qualitaet.tabelle.kopf_rechts": "destra &rarr;",
    "qualitaet.tabelle.kopf_doppel": "duplicati",
    "qualitaet.tabelle.kopf_verwechslung": "scambi",
    "qualitaet.person.funde": "{n} immagini che meritano uno sguardo",
    "qualitaet.person.verwechselt": "forse scambiata",
    "qualitaet.person.alles_gut": "tutto a posto",
    # Ergebnis-Satz "alles gut": die <b>-Grenze trennt zwei VOLLSTAENDIGE
    # Saetze — B9-sicherer Split (der Funde-Zweig dagegen bleibt literal,
    # s. Abschnittskommentar).
    "qualitaet.ergebnis.alles_gut": "Tutto a posto.",
    "qualitaet.ergebnis.alles_gut_satz":
        "Controllate {n} immagini di {np} persone &mdash; niente "
        "richiede la tua attenzione.",
    "qualitaet.wort.defekt": "file danneggiato",
    "qualitaet.wort.kein_gesicht": "nessun volto trovato",
    "qualitaet.wort.zu_klein": "troppo piccola",
    "qualitaet.wort.unscharf": "sfocata",
    "qualitaet.wort.schwach": "immagine debole",
    # {name} kommt escaped aus der Route (Muster lernanker {kamera}).
    "qualitaet.galerie.looks_like": "somiglia a {name}",
    "qualitaet.galerie.doppel": "duplicata — è coperta da quella tenuta",
    "qualitaet.galerie.gut": "buona",
    "qualitaet.galerie.gut_behalten": "buona — tenuta tra i suoi duplicati",
    "qualitaet.galerie.vorrat": "dal materiale",
    "qualitaet.galerie.norm": "qualità {norm}",
    "qualitaet.galerie.okay": "discreta",
    "qualitaet.galerie.satz_gut": "Tutte le {n} immagini sembrano a posto.",
    "qualitaet.galerie.satz_funde":
        "{funde} immagini su {n} meritano uno sguardo — stanno nelle "
        "due schede a destra. Spunta ciò che vuoi rimuovere — senza il "
        "tuo clic non succede nulla.",
    "qualitaet.reiter.gut": "Buone ({n})",
    "qualitaet.reiter.check": "Da controllare ({n})",
    "qualitaet.reiter.weg": "Rimozione consigliata ({n})",
    "qualitaet.galerie.knopf_alle": "Seleziona tutto",
    "qualitaet.galerie.knopf_keine": "Deseleziona tutto",
    "qualitaet.galerie.knopf_entfernen": "Rimuovi le selezionate",
    "qualitaet.galerie.leer_gruppe": "niente in questo gruppo.",
    "qualitaet.galerie.titel": "{name} — qualità delle immagini",
    "qualitaet.galerie.link_zurueck": "&larr; torna alla panoramica",
    "qualitaet.galerie.leer_person": "nessuna immagine per questa persona.",
    "qualitaet.leer.titel": "Nessun controllo ancora calcolato.",
    "qualitaet.leer.hinweis": "Fai clic su Ricontrolla ora qui sopra.",
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
    "lernwizard.titel": "Sessione di apprendimento",
    "lernwizard.link_how": "Come funziona &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Preparazione",
    "lernwizard.phase.ernte": "Estrazione (dei volti)",
    "lernwizard.phase.anker": "Raggruppamento (ancore)",
    "lernwizard.phase.benennung": "Denominazione (il tuo passo)",
    "lernwizard.phase.neben_ansichten": "Viste laterali",
    "lernwizard.phase.ganzkoerper": "Archivio a figura intera",
    "lernwizard.phase.uebernahme": "Acquisizione nel master",
    "lernwizard.phase.fertig": "Fatto",
    "lernwizard.phase.aktuell": "(attuale)",
    "lernwizard.phase.link_benennen": "apri i gruppi e dai loro un nome",
    "lernwizard.wizard.titel": "Apprendimento persone — sessione guidata",
    "lernwizard.wizard.satz":
        "Pianifica una sessione di apprendimento sulle tue "
        "registrazioni. Preparazione, estrazione, raggruppamento, "
        "denominazione e acquisizione nel riconoscimento avvengono "
        "tutti per davvero.",
    "lernwizard.wizard.lage_b":
        "B — riferimenti/sconosciuti esistenti verranno ampliati",
    "lernwizard.wizard.lage_a": "A — partenza da zero, ancora nessun volto",
    "lernwizard.badge.unbekannt": "visitatori sconosciuti",
    # echter Plural schon im Original (is/are) — t_n loest .eins/.viele.
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} visitatore sconosciuto è in attesa in",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} visitatori sconosciuti sono in attesa in",
    "lernwizard.link_unbekannte": "Persone &rarr; Sconosciuti",
    "lernwizard.wizard.unbekannt_hinweis":
        "Volti estratti oggi che non corrispondono a nessuna persona "
        "conosciuta — lì puoi subito dar loro un nome, unirli o "
        "silenziarli; per questo non serve una sessione di "
        "apprendimento.",
    "lernwizard.wizard.start_titel": "Punto di partenza",
    "lernwizard.wizard.start_hinweis":
        "Interruttore di pulizia per gli sconosciuti estratti in "
        "automatico: arriva con la fase di denominazione.",
    "lernwizard.wizard.knopf_letzte": "ultimi {n}",
    "lernwizard.wizard.knopf_alle": "TUTTI i raggiungibili",
    "lernwizard.wizard.attr_eigen": "N personalizzato",
    "lernwizard.wizard.knopf_go": "vai",
    "lernwizard.wizard.scope_titel": "Ambito (eventi, non giorni)",
    "lernwizard.wizard.scope_hinweis":
        "TUTTI percorre l’intera cronologia raggiungibile (limitata "
        "dalla retention di Frigate — il bilancio qui sotto mostra fino "
        "a dove).",
    "lernwizard.wizard.auswahl_titel": "La tua selezione",
    # {wann}/{clips} kommen vorformatiert aus der Route (§8.8/§8.9).
    "lernwizard.wizard.auswahl_zeile":
        "ultimi {n} eventi persona = indietro fino a {wann} · {clips} "
        "con video disponibile",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} più vecchi senza video verranno saltati",
    "lernwizard.wizard.auswahl_hinweis":
        "Il taglio è esatto a N — il completamento della selezione a "
        "passaggi interi arriva con la fase di raggruppamento.",
    "lernwizard.wizard.auswahl_durchsucht": "{k} di questi {n} sono già stati esaminati — con \"salta gli eventi già esaminati\" la sessione prende eventi più vecchi (la scheda mostra dove arriva).",
    "lernwizard.wizard.q_teilgemessen":
        "velocità di analisi misurata su QUESTA macchina; la stima dei "
        "download usa valori predefiniti",
    "lernwizard.wizard.q_gemessen": "misurato su QUESTA macchina",
    # Konditionale Annotations-Anhaenge (§8.11): eigene Schluessel, Werte
    # duerfen mit ", " beginnen.
    "lernwizard.wizard.q_skip":
        ", misurazione saltata su questa macchina ({grund})",
    "lernwizard.wizard.q_wartet":
        ", misurazione in attesa di uno slot di analisi libero …",
    "lernwizard.wizard.q_laeuft": ", misurazione in corso …",
    "lernwizard.wizard.q_rueckfall":
        "valori di riserva — non ancora misurati qui",
    "lernwizard.wizard.dauer_titel": "Durata stimata",
    "lernwizard.wizard.dauer_zeile":
        "analisi ~{analyse} · download dei video ~{download} · "
        "riscaldamento una tantum {kalt}",
    "lernwizard.wizard.dauer_gesamt": "totale ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Soglie (regolabili in Avanzate)",
    "lernwizard.wizard.frage":
        "Apprendere da tutti i {n} eventi? Durata stimata ~{gesamt} "
        "(analisi {analyse} + download {download}). La sessione si può "
        "interrompere in qualsiasi momento.",
    "lernwizard.wizard.fps_titel": "Frame al secondo per l’analisi",
    "lernwizard.wizard.knopf_start": "Crea questa sessione",
    "lernwizard.seg.vorbereiten": "Preparazione",
    "lernwizard.seg.sammeln": "Estrazione volti",
    "lernwizard.seg.sortieren": "Raggruppamento",
    "lernwizard.status.laeuft_seit": "in corso da {dauer}",
    "lernwizard.status.rest": "mancano {rest}",
    "lernwizard.status.fertig_in": "completato in {dauer}",
    "lernwizard.status.aufnahmen": "registrazioni: {n}",
    "lernwizard.status.bilder": "{n} immagini estratte finora",
    "lernwizard.puls.working": "al lavoro — aggiornato {s}s fa",
    "lernwizard.puls.stumm":
        "nessun aggiornamento da {s}s — un video lungo può richiedere "
        "minuti; se continua a crescere, controlla /log",
    "lernwizard.zeile.kaputt": "{n} righe illeggibili contate",
    "lernwizard.zeile.anker_link": "vedi i {n} gruppi di ancore",
    # DREI Plurale in EINEM Satz: je Plural ein t_n-Fragment, Trenner
    # bleiben literal in der Route (Zaehler, keine Prosa — §8.10).
    "lernwizard.ergebnis.bilder.eins": "estratta {n} immagine",
    "lernwizard.ergebnis.bilder.viele": "estratte {n} immagini",
    "lernwizard.ergebnis.aufnahmen.eins": "da {n} registrazione",
    "lernwizard.ergebnis.aufnahmen.viele": "da {n} registrazioni",
    "lernwizard.ergebnis.gruppen.eins": "smistate in {n} gruppo",
    "lernwizard.ergebnis.gruppen.viele": "smistate in {n} gruppi",
    "lernwizard.ergebnis.beiseite": "({n} messe da parte)",
    "lernwizard.kachel.lauf": "Sessione di apprendimento",
    "lernwizard.kachel.sammeln": "Estrai &amp; raggruppa",
    "lernwizard.kachel.benennen": "Dai un nome ai gruppi",
    "lernwizard.kachel.fertig": "Fatto &mdash; ora contano",
    "lernwizard.such.titel": "Cerca volti negli eventi",
    "lernwizard.such.klein": "ripercorre le tue registrazioni",
    "lernwizard.pop.satz":
        "Ripercorre le tue registrazioni ed estrae i volti. Giorno per "
        "giorno il sistema continua ad apprendere da solo.",
    "lernwizard.pop.label_letzte": "Ripercorri gli ultimi",
    "lernwizard.pop.wort_events": "eventi",
    "lernwizard.pop.hint_n":
        "quante registrazioni recenti controllare (fino a {max})",
    "lernwizard.pop.label_tag": "Un giorno intero:",
    "lernwizard.pop.hint_tag":
        "ogni registrazione di quel giorno, quante che siano",
    "lernwizard.pop.wort_fps": "immagini al secondo",
    "lernwizard.pop.hint_fps":
        "più immagini trovano più angolazioni, ma la ricerca dura di più",
    "lernwizard.pop.label_skip": "Salta gli eventi già esaminati",
    "lernwizard.pop.hint_skip":
        "ogni ricerca prosegue più indietro nel passato &mdash; togli "
        "la spunta per cercare di nuovo negli eventi più recenti",
    "lernwizard.pop.alle_gesichter": "Tutti i volti",
    "lernwizard.pop.eine_person": "Solo una persona:",
    "lernwizard.pop.hint_person":
        "con una persona scelta, i gruppi corrispondenti sono elencati "
        "per primi &mdash; non viene nascosto nulla",
    "lernwizard.pop.knopf_start": "Avvia ricerca",
    "lernwizard.knopf_abbrechen": "Annulla",
    "lernwizard.k1.unbekannt.eins": "{n} visitatore sconosciuto di oggi:",
    "lernwizard.k1.unbekannt.viele": "{n} visitatori sconosciuti di oggi:",
    "lernwizard.k1.gestartet": "Sessione avviata {wann}",
    "lernwizard.k1.scope": "ambito {n} eventi",
    "lernwizard.k1.tag": "giorno {tag}",
    "lernwizard.k2.satz":
        "Procede da sola &mdash; puoi chiudere questa pagina e tornare "
        "più tardi.",
    "lernwizard.k2.knopf_abort": "Interrompi sessione",
    "lernwizard.k3.satz_warten":
        "L’unico passo in cui servi tu: un gruppo deve essere una sola "
        "persona &mdash; indica chi è, oppure saltalo.",
    "lernwizard.k3.keine_gesichter":
        "Nessun volto nuovo questa volta &mdash; niente da nominare. Va "
        "bene così: significa solo che nelle registrazioni non c’era "
        "nessuno di nuovo.",
    "lernwizard.knopf_neuer_lauf": "Avvia una nuova sessione",
    "lernwizard.k3.gruppe_offen":
        "Il gruppo attuale è aperto qui sotto, a tutta larghezza.",
    "lernwizard.k3.alle_erledigt": "Tutti i gruppi sono stati gestiti.",
    "lernwizard.chip.bilder": "{n} immagini",
    # .295-Sammelzeile — Anker der qs.sh-PYAD-Stufe (Text wohnt jetzt
    # hier, die Route referenziert den Schluessel).
    "lernwizard.k3.verworfen.eins":
        "{n} gruppo eliminato da te &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} gruppi eliminati da te &middot;",
    "lernwizard.k3.link_einsehen": "vedi",
    # B9: je Zweig ein GANZER Satz-Schluessel (statt Punkt-Anhaengsel).
    "lernwizard.k3.done_weiter":
        "{erledigt} di {gesamt} completati &mdash; il prossimo è pronto.",
    "lernwizard.k3.done_punkt": "{erledigt} di {gesamt} completati.",
    "lernwizard.k3.wartend.eins": "{n} gruppo ti aspetta.",
    "lernwizard.k3.wartend.viele": "{n} gruppi ti aspettano.",
    # ZWEI Plurale in einem <b>-Zaehler: zwei t_n-Fragmente (§8.10).
    "lernwizard.k4.adopt_bilder.eins": "{n} immagine acquisita per",
    "lernwizard.k4.adopt_bilder.viele": "{n} immagini acquisite per",
    "lernwizard.k4.adopt_personen.eins": "{n} persona",
    "lernwizard.k4.adopt_personen.viele": "{n} persone",
    "lernwizard.k4.zaehlen_sofort":
        "contano subito per il riconoscimento.",
    "lernwizard.k4.link_qs": "controlla la qualità dell’archivio &#8230;",
    "lernwizard.k4.nichts":
        "questa volta nessuna nuova immagine è stata acquisita (gruppi "
        "saltati o già coperti).",
    "lernwizard.k4.wiederholen":
        "Ripeti ogni pochi giorni, oppure lascia che nel frattempo la "
        "vista del giorno integri le persone conosciute.",
    "lernwizard.k4.knopf_faces": "Torna a Volti",
    "lernwizard.k4.hinweis":
        "Le immagini nominate diventano riferimenti e contano subito "
        "per il riconoscimento.",
    "lernwizard.zw.grund_maessig": "qualità dell’immagine solo discreta",
    "lernwizard.zw.attr_clip": "apri il video",
    "lernwizard.blick.links": "Sguardo a sinistra",
    "lernwizard.blick.frontal": "Frontale",
    "lernwizard.blick.rechts": "Sguardo a destra",
    "lernwizard.blick.leer":
        "nessuna immagine utilizzabile di questa angolazione nel gruppo",
    "lernwizard.blick.legende":
        "({gut} buone, {grenz} al limite su {n} controllate)",
    "lernwizard.zw.titel": "Gruppo {pos} di {gesamt} &mdash; chi è?",
    "lernwizard.zw.satz":
        "Un gruppo deve essere una sola persona. Tocca un’immagine per "
        "escluderla &mdash; poi indica chi è, oppure salta il gruppo.",
    "lernwizard.bekannt.system": "già nel tuo sistema",
    "lernwizard.bekannt.anker": "nominato in un altro gruppo",
    # {name} kommt escaped aus der Route.
    "lernwizard.zw.knopf_adopt": "Acquisisci come {name}",
    "lernwizard.zw.knopf_ja": "Sì, è {name}",
    "lernwizard.zw.fehler":
        "il controllo delle immagini non è partito (vedi /log) &mdash; "
        "ricarica per riprovare; Salta ed Elimina funzionano comunque.",
    "lernwizard.zw.warte":
        "controllo delle immagini di questo gruppo rispetto alla soglia "
        "dei riferimenti &mdash; qualche secondo &hellip;",
    "lernwizard.zw.knopf_andere": "Qualcun altro &#8230;",
    "lernwizard.zw.attr_name": "nome della persona (nuovo o esistente)",
    "lernwizard.zw.knopf_save": "Salva nome",
    "lernwizard.zw.knopf_skip": "Salta questo gruppo",
    "lernwizard.zw.frage_delete":
        "Eliminare questo gruppo? Le sue immagini vengono rimosse e una denominazione in sospeso viene annullata. Non si può annullare.",
    "lernwizard.zw.knopf_delete": "Elimina questo gruppo",
    "lernwizard.zw.link_detail": "vista di dettaglio completa",
    "lernwizard.zw.detail_zusatz":
        "(tutte le immagini con i motivi, selezione per esperti)",
    "lernwizard.erfolg.titel": "Raggruppamento completato",
    "lernwizard.erfolg.cluster.eins": "{n} gruppo di volti pronto:",
    "lernwizard.erfolg.cluster.viele": "{n} gruppi di volti pronti:",
    "lernwizard.erfolg.knopf_anker": "Vedi i gruppi di ancore",
    "lernwizard.erfolg.hinweis": "apri un gruppo per dargli un nome",
    "lernwizard.expert.phasen_titel": "Fasi",
    "lernwizard.expert.phasen_hinweis":
        "Preparazione, estrazione, raggruppamento, denominazione e "
        "acquisizione nel master sono reali in questa build — le viste "
        "laterali e l’archivio a figura intera si attiveranno con i "
        "prossimi aggiornamenti.",
    "lernwizard.expert.progress_titel": "Avanzamento",
    "lernwizard.expert.anker_bisher": "ancore finora: {n}",
    "lernwizard.expert.progress_rest":
        "creata {wann} · ambito {n} eventi · sopravvive ai riavvii "
        "(ripartenza integrata)",
    "lernwizard.expert.lauf_bleibt":
        "questa sessione resta — le sue ancore rimangono disponibili",
    # --------------------------------- Stufe 1: Einhang/Skelett (webui) ---
    "nav.bereich.activity": "Attività",
    "nav.bereich.faces": "Volti",
    "nav.bereich.learn": "Apprendimento",
    "nav.bereich.person": "Persona",
    "nav.bereich.vision": "Visione",
    "nav.bereich.live": "Live",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Configurazione",
    "nav.bereich.erkennungstest": "Test di riconoscimento",
    "nav.bereich.system": "Sistema",
    "nav.heute": "Oggi",
    "nav.ereignisse": "Eventi",
    "nav.offen": "Da etichettare",
    "nav.faces": "Volti",
    "nav.gesichter": "Conosciuti",
    "nav.unbekannte": "Sconosciuti",
    "nav.qualitaet": "Qualità",
    "nav.lernlauf": "Sessione di apprendimento",
    "nav.anker": "Ancore",
    "nav.lernen": "Suggerimenti",
    "nav.person": "Immagini del corpo",
    "nav.person_kontrolle": "Immagini valutate",
    "nav.person_modell": "Stato del modello",
    "nav.personlauf": "Apprendimento della persona",
    "nav.vision": "Rilevamento visione",
    "nav.live": "Sentinelle live",
    "nav.live_alerts": "Avvisi live",
    "nav.erkennung": "Riconoscimento",
    "nav.kameras": "Telecamere",
    "nav.benachrichtigungen": "Notifiche",
    "nav.areas": "Aree",
    "nav.kette": "Catena di riconoscimento",
    "nav.konfiguration": "Avanzate",
    "nav.erkennungstest": "Test di riconoscimento",
    "nav.system": "Sistema",
    "nav.sync_auswahl": "Sincronizzazione Frigate",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Log del servizio",
    "ui.fuss.docs": "Documentazione",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip": "Easy mostra le pagine essenziali — Expert mostra tutto. Nulla viene cancellato, Easy nasconde soltanto.",
    "ui.live.chip": "Live",
    "ui.theme.knopf": "Tema",
    "ui.theme.tooltip": "Alterna tra chiaro e scuro",
    "ui.theme.aria": "Cambia il tema dei colori",
    "ui.sprache.tooltip": "Lingua di questa installazione — vale per tutte le pagine e le notifiche",
    "ui.upd.link": "aggiornamento {tag}",
    "ui.upd.tooltip": "Su GitHub è disponibile una versione più recente di suslik",
    "ui.upd.titel": "Aggiornamento disponibile",
    # ui.upd.satz ist der erste deklarierte t_html-Schluessel (HTML_SCHLUESSEL,
    # core/sprache.py) — Tag-Folge muss in jeder Sprache identisch sein.
    "ui.upd.satz": "Su GitHub c’è un’immagine suslik più recente (<b>{tag}</b>) — <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">note di rilascio</a>. Scarica la nuova immagine e riavvia per aggiornare; i tuoi dati e le impostazioni restano intatti.",
    "ui.wn.titel": "Novità",
    "ui.wn.x_tooltip": "Nascondi fino alla prossima versione",
    "ui.wn.x_aria": "Chiudi",
    "ui.wn.mehr": "Mostra tutto ({n})",
    "ui.wn.weniger": "Mostra meno",
    "ui.hinweis.englisch": "Questa pagina non è ancora tradotta — il suo contenuto è per ora in inglese.",
    # --------------------------------- Stufe 1: Seitentitel (verifyd) ---
    "titel.setup": "Configurazione iniziale",
    "titel.anker_detail": "Dettaglio ancora",
    "titel.aehnliche": "Volti corrispondenti",
    "titel.live_kamera": "Live — {kamera}",
    "titel.video": "Video",
    "titel.event": "Evento",
    "titel.vision_galerie": "Crea una galleria",
    "titel.hilfe": "Come funziona",
    # --------------------------------- Stufe 1: Setup-Wizard Schritt 0 ---
    "setup.sprache.titel": "Lingua",
    "setup.sprache.satz": "Scegli la lingua di questa installazione — si applica subito e vale anche per le notifiche. Puoi cambiarla in qualsiasi momento con il selettore nell’intestazione.",
    # --------------------------------- Stufe 1: js.* (window.T, app.js) ---
    # VERTRAG: app.js liest NUR js.*-Schluessel (TT() mit EN-Fallback ==
    # diesem Wert); jede Richtung prueft die Gate-Stufe Sprach-Deckung.
    "js.status.fehler": "errore",
    "js.status.fehler_gross": "Errore",
    "js.status.fehler_detail": "errore: {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "salvataggio …",
    "js.status.gespeichert": "salvato",
    "js.status.senden": "invio …",
    "js.status.starten": "avvio …",
    "js.status.laeuft": "in corso …",
    "js.status.laeuft_wort": "in corso",
    "js.status.pruefen": "verifica …",
    "js.status.suchen": "ricerca …",
    "js.status.lernen": "apprendimento …",
    "js.status.hinzufuegen": "aggiunta …",
    "js.status.entfernen": "rimozione …",
    "js.status.loeschen": "eliminazione …",
    "js.status.hochladen": "caricamento …",
    "js.status.wiederherstellen": "ripristino …",
    "js.status.ueberspringen": "salto …",
    "js.status.siehe_log": "vedi il log del servizio",
    "js.status.diagnose": "diagnosi",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Annulla",
    "js.neustart.zurueck": "Il servizio è tornato, caricamento …",
    "js.neustart.kommt": "Il servizio sta tornando …",
    "js.neustart.gespeichert": "Salvato. Il servizio si riavvia, attendi …",
    "js.neustart.warten": "Il servizio si riavvia, attendi …",
    "js.konfig.frage": "Salvare la configurazione e riavviare il servizio?",
    "js.lernlauf.fps_zeile": "≈ totale ~{dauer} a {fps}/s",
    "js.lernlauf.tag_fehlt": "scegli prima un giorno",
    "js.lernlauf.abbruch_frage": "Interrompere questa sessione di apprendimento?",
    "js.notif.frage": "Salvare le impostazioni delle notifiche e riavviare il servizio?",
    "js.frigate.ro_frage": "Passare a SOLA LETTURA? suslik smetterà di scrivere su Frigate.",
    "js.frigate.rw_frage": "Attivare la SCRITTURA su Frigate (sub_labels + sincronizzazione dei riferimenti)?",
    "js.restore.frage": "Ripristinare la configurazione da \"{name}\"? Sovrascrive le impostazioni attuali e riavvia il servizio.",
    "js.vollrestore.frage": "Ripristinare il backup COMPLETO \"{name}\"? Sostituisce impostazioni, riferimenti e tutto il materiale appreso, poi riavvia il servizio.",
    "js.vollrestore.laeuft": "caricamento + ripristino … (i file grandi richiedono tempo)",
    "js.enroll.fehler": "Errore: {msg}",
    "js.enroll.person_fehlt": "Scegli una persona o inseriscine una nuova.",
    "js.upload.fehlt": "Scegli una persona (dal menu o nuova) e un file.",
    "js.upload.trotzdem": "{msg}\n\nAggiungere comunque?",
    "js.anlernen.frage": "Aggiungere il gruppo come \"{person}\" (le immagini migliori diventano riferimenti)?",
    "js.anlernen.name_frage": "Nome della nuova persona:",
    "js.anlernen.person_fehlt": "Scegli una persona esistente.",
    "js.auswahl.gesicht_fehlt": "Seleziona almeno un volto.",
    "js.auswahl.bild_fehlt": "Seleziona almeno un’immagine.",
    "js.vorschlag.keine": "Nessun volto consigliato.",
    "js.vorschlag.alle_frage": "Aggiungere tutti i {n} volti consigliati a {person}? Diventano subito riferimenti.",
    "js.vorschlag.frage": "Aggiungere {n} volto/i a {person}?",
    "js.vorrat.frage": "Aggiungere {n} volto/i del materiale a {person}? Diventano subito riferimenti (restano in locale, nessuna esportazione).",
    "js.qs.fortschritt": "controllo immagine {i} di {n} …",
    "js.sync.frage": "Sincronizzare: {richtung}?",
    "js.sync.modell_laedt": "caricamento del modello …",
    "js.sync.fortschritt": "{done}/{total} volti ({current}) {pct}%",
    "js.sync.fertig": "fatto: {ok} ok, {gate} saltati — la pagina si ricarica …",
    "js.sync.fehler": "sincronizzazione non riuscita: {grund}",
    "js.syncauswahl.knopf": "Trasferisci {n} selezionate a Frigate",
    "js.syncauswahl.nichts": "Nessuna selezione",
    "js.syncauswahl.nichts_klein": "nessuna selezione",
    "js.syncauswahl.skip": "salta",
    "js.syncauswahl.restore": "ripristina",
    "js.syncauswahl.wieder": "riproponi",
    "js.syncauswahl.zurueck_laeuft": "ripropongo …",
    "js.syncauswahl.frage": "Inviare {n} immagine/i di riferimento a Frigate?",
    "js.syncauswahl.fehl_knopf": "trasferimento non riuscito",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct}%",
    "js.syncauswahl.fertig": "fatto: {ok} caricate, {gate} non accettate — la pagina si ricarica …",
    "js.syncauswahl.fehler": "trasferimento non riuscito: {grund}",
    "js.vorpruef.haengt": "il controllo preliminare sembra bloccato — ricarica la pagina per riprovare",
    "js.vorpruef.laeuft": "controllo delle immagini … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "controllo preliminare non riuscito: {grund}",
    "js.vorpruef.fertig": "controllo preliminare completato — la pagina si ricarica …",
    "js.import.fortschritt": "download {done}/{total} ({current}) {pct}%",
    "js.import.fertig_wiz": "✓ {n} importati — calcolo delle caratteristiche sull’acceleratore …",
    "js.import.knopf_fertig": "Importati ✓",
    "js.import.fehler": "importazione non riuscita: {grund}",
    "js.import.knopf": "Importa volti",
    "js.import.knopf_ges": "Importa volti da Frigate",
    "js.import.fertig_ges": "✓ {n} importati — calcolo delle caratteristiche, la pagina si ricarica …",
    "js.ref.frage": "Rimuovere l’immagine di riferimento di {person}?",
    "js.ref.batch_frage": "Eliminare {n} immagine/i?",
    "js.dienst.nicht_erreichbar": "servizio non raggiungibile — riprova tra un momento.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage": "Ignorare come estraneo conosciuto? Non attiverà più avvisi. (Riattivabile in qualsiasi momento qui sotto, in \"visitatori conosciuti\".)",
    "js.unb.ziel_fehlt": "Scegli un’identità di destinazione.",
    "js.unb.merge_frage": "Unire?",
    "js.unb.name_fehlt": "Inserisci un nome (persona nuova o esistente).",
    "js.unb.benennen_frage": "Assegnare a \"{person}\"? Le immagini migliori diventano riferimenti.",
    "js.person.loesch_frage": "Eliminare TUTTI i riferimenti e il nome \"{person}\"?\nLe immagini finiscono nella cartella cestino (recuperabili).\n\nDigita il nome per confermare:",
    "js.person.name_falsch": "Il nome non corrisponde — nulla è stato eliminato.",
    "js.areas.fehl": "salvataggio non riuscito — il servizio è raggiungibile?",
    "js.areas.name_fehlt": "Inserisci prima un nome per l’area.",
    "js.areas.existiert": "Quest’area esiste già.",
    # js.areas.entfernen_frage: "Default" ist zugleich Kennung der
    # Standard-Area (Anzeige==Kennung §8.2) — bleibt in jeder Sprache.
    "js.areas.entfernen_frage": "Rimuovere l’area \"{name}\"? Le sue telecamere tornano a Default — non cambia altro.",
    "js.personlauf.abbruch_frage": "Interrompere questa sessione di apprendimento della persona? Le immagini estratte restano.",
    "js.personlauf.verwerfen_frage": "Scartare completamente la sessione {lid}? Tutte le sue immagini vengono eliminate; una nuova sessione può estrarle di nuovo in qualsiasi momento.",
    "js.vision.nicht_erreichbar": "servizio non raggiungibile — non è stato salvato nulla",
    "js.vision.gespeichert": "salvato — il riconoscimento usa questa connessione da ora in poi",
    "js.vision.gespeichert_neustart": "salvato — il servizio si riavvia a breve",
    "js.vision.gespeichert_reload": "salvato — il servizio si sta riavviando, la pagina si ricarica a breve",
    "js.vision.treffer": "{n}/2 corrette",
    "js.vision.tokens": "{ist} token contro {soll}",
    "js.vision.dirty_titel": "Questa connessione non è salvata",
    # Zitat-Folge Tranche C: zitiert vision.save.knopf ("Salva
    # connessione") wortgleich — gleiche Kopplung in
    # js.vision.prompt_zurueck, bei Knopf-Aenderung BEIDE nachziehen.
    "js.vision.dirty_text": "Il test userebbe i valori appena digitati. Il riconoscimento continua a usare la connessione SALVATA finché non premi «Salva connessione» — un test verde da solo non cambia nulla negli esiti.",
    "js.vision.dirty_save": "Prima salva, poi testa",
    "js.vision.dirty_test": "Testa senza salvare",
    "js.vision.stufe1": "raggiungibilità e modello",
    "js.vision.stufe2": "griglie di forme a scelta obbligata",
    "js.vision.stufe3": "conteggio dei token",
    "js.vision.stufe_laeuft": "passo {nr}/3 — {name} … (un modello locale su CPU può richiedere diversi minuti)",
    "js.vision.test_fehl": "il test non è stato eseguito",
    "js.vision.stufe_stop": "fermato al passo {nr} — vedi il log qui sotto",
    "js.vision.fertig": "fatto — {ampel}",
    "js.vision.stufe_fehl": "il passo {nr} non è stato eseguito",
    "js.vision.neustart_warte": "il servizio al momento non risponde — la pagina si ricarica a breve",
    "js.vision.prompt_frage": "Riportare la domanda alla formulazione predefinita?",
    "js.vision.prompt_zurueck": "formulazione predefinita ripristinata — premi «Salva connessione» per salvarla",
    "js.vision.kachel_frage": "Ci sono modifiche non salvate. Cambiando fornitore vengono scartate. Continuare?",
    "js.vision.pick": "— scegline uno —",
    "js.vision.untested": "non testato qui",
    "js.vision.neu_pruefen": "la connessione è cambiata — verificala di nuovo per vedere quali modelli offre",
    "js.vision.key_laeuft": "chiedo al fornitore quali modelli puoi usare …",
    "js.vision.key_fehl": "la verifica non è riuscita",
    "js.vision.key_fehl2": "la verifica non è stata eseguita",
    "js.rt.start": "avvio il rilevamento visione …",
    "js.rt.fehl": "non è stato possibile avviare il rilevamento",
    "js.rt.nach_fehl": "non è stato possibile avviare l’analisi",
    "js.vw.geliehen": "dalla riga {reihe}",
    "js.vw.vergessen_frage": "Dimenticare le immagini scartate per questa galleria? Potranno essere riproposte.",
    "js.vw.leer_frage": "Non è stato possibile riempire {n} cella/e. Approvare comunque la galleria?",
    "js.vw.kopiert": "copio le immagini nella galleria …",
    # js.live.phase_*: Anzeige-Woerter zu den Status-KENNUNGEN des
    # Live-Polls (Status-replace-Mapping, §8-Nachtrag).
    "js.live.phase_verbinden": "Connessione",
    "js.live.phase_messen": "Misurazione",
    "js.live.phase_auswerten": "Valutazione",
    "js.live.phase_abbruch": "Interruzione",
    "js.live.rest": " — mancano {n} s",
    "js.live.auftrag_zeile": "{art} su {kamera}: {phase}{rest}{pausiert}",
    "js.live.messung": "Misurazione del carico",
    "js.live.quelltest": "Test sorgente",
    "js.live.pausiert": " — sentinelle in pausa per la misurazione ({liste})",
    "js.live.job_laeuft": "test sorgente in corso (processo ausiliario, fino a ~2 minuti) …",
    "js.live.job_ok": "test sorgente completato: {text}",
    "js.live.job_fehl": "test sorgente NON RIUSCITO: {text}",
    "js.live.messung_fehl": "misurazione del carico non riuscita: {grund}",
    "js.live.test_fehl": "test sorgente non riuscito: {grund}",
    # ---- auftritte (Stufe 2, Tranche A) ----
    # Projektroot-Route /heute-Personensicht + /pass/<eid> (auftritte.py);
    # Stufe-2-Grenzen s. en.py-Abschnittskommentar.
    "auftritte.unbek.zaehlung":
        "+{n} senza corrispondenza (di solito le stesse persone)",
    "auftritte.unbek.name": "Sconosciuto {nummer}",
    "auftritte.unbek.ohne_treffer.eins":
        "{n} evento con un volto senza corrispondenza",
    "auftritte.unbek.ohne_treffer.viele":
        "{n} eventi con un volto senza corrispondenza",
    "auftritte.nav.zurueck_heute": "&#8592; Oggi",
    "auftritte.unbek.titel": "Sconosciuto",
    "auftritte.unbek.leer_link": "A questo link manca il passaggio.",
    "auftritte.unbek.leer_weg":
        "Questo passaggio non è più nella vista del giorno.",
    "auftritte.unbek.leer_weg_hinweis":
        "Il giorno potrebbe essere stato raggruppato di nuovo — riaprilo "
        "da Oggi.",
    "auftritte.unbek.leer_pool":
        "Nessun volto estratto per questo passaggio.",
    "auftritte.unbek.leer_pool_hinweis":
        "I volti estratti potrebbero essere stati eliminati nel frattempo.",
    "auftritte.knopf.video": "video",
    "auftritte.karte.faces.eins": "{n} volto",
    "auftritte.karte.faces.viele": "{n} volti",
    "auftritte.karte.kameras.eins": "{n} telecamera",
    "auftritte.karte.kameras.viele": "{n} telecamere",
    "auftritte.unbek.mehr_im_lauf": "+{n} in questo passaggio",
    "auftritte.unbek.ein_lauf": "un passaggio",
    "auftritte.zuweisen.titel": "Chi è?",
    "auftritte.zuweisen.satz":
        "Questi sono i volti di QUESTO passaggio. Spunta quelli che "
        "appartengono davvero alla persona &mdash; gli scarti restano "
        "fuori. Assegna un nome (nuovo o esistente) e i volti vengono "
        "appresi; se non fai nulla, restano sconosciuti.",
    "auftritte.zuweisen.knopf_alle": "Seleziona tutto",
    "auftritte.zuweisen.knopf_keine": "Nessuno",
    "auftritte.zuweisen.attr_person": "persona (nuova o esistente)",
    "auftritte.zuweisen.knopf_zuweisen": "Aggiungi i volti selezionati",
    "auftritte.zuweisen.js_keine": "spunta almeno un volto",
    "auftritte.zuweisen.js_name": "inserisci il nome della persona",
    "auftritte.zuweisen.js_lernt": "apprendimento…",
    "auftritte.zuweisen.js_fehler": "errore",
    "auftritte.unbek.titel_lauf": "Sconosciuto {nummer} — passaggio",
    "auftritte.leer_person": "Persona sconosciuta.",
    "auftritte.leer_person_hinweis": "Scegli una persona nella pagina Oggi.",
    "auftritte.titel": "Apparizioni",
    "auftritte.nav.attr_tag": "torna al giorno",
    "auftritte.nav.attr_vortag": "giorno precedente",
    "auftritte.kopf.passzahl.eins": "{n} passaggio",
    "auftritte.kopf.passzahl.viele": "{n} passaggi",
    "auftritte.nav.attr_kein_morgen": "nessun giorno futuro",
    "auftritte.nav.attr_folgetag": "giorno successivo",
    "auftritte.titel_person": "{person} — Apparizioni",
    "auftritte.leer_passe":
        "Nessun passaggio confermato di {person} in questo giorno.",
    "auftritte.leer_passe_hinweis":
        "Usa le frecce per spostarti tra i giorni.",
    "auftritte.karte.kein_bild": "nessuna immagine",
    "auftritte.thumb.zusatz_unbestaetigt": " — senza conferma qui",
    "auftritte.thumb.zusatz_referenz": " — tra i riferimenti",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} evento senza volto",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} eventi senza volto",
    "auftritte.thumb.hinweis_referenz":
        "bordo verde = già tra i riferimenti",
    "auftritte.karte.best_punkt": "presenza confermata alle {zeit}",
    "auftritte.karte.best_spanne": "presenza confermata {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "in corso",
    "auftritte.karte.pass_nr": "Passaggio {n}",
    "auftritte.karte.events.eins": "{n} evento",
    "auftritte.karte.events.viele": "{n} eventi",
    "auftritte.karte.best_match": "miglior corrispondenza {wert}",
    "auftritte.karte.auch_dabei": "altre persone in questo passaggio: {namen}",
    "auftritte.pass.titel": "Passaggio",
    "auftritte.pass.leer_event": "Evento non trovato.",
    "auftritte.pass.leer_event_hinweis":
        "Con il tempo potrebbe essere uscito dal log.",
    "auftritte.pass.leer_gruppe":
        "Questo evento non fa parte di un passaggio raggruppato.",
    "auftritte.pass.leer_gruppe_hinweis":
        "Il raggruppamento richiede il contesto della vista del giorno.",
    "auftritte.nav.zurueck_tag": "&#8592; Giorno",
    "auftritte.pass.attr_vor": "passaggio precedente del giorno",
    "auftritte.pass.attr_nach": "passaggio successivo del giorno",
    "auftritte.pass.kopf": "Passaggio {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Senza corrispondenza",
    "auftritte.pass.label_gt": "Etichetta",
    "auftritte.pass.badge_fremd": "estraneo confermato",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log non contiene una riga con il motivo — apri l’evento "
        "per il log completo",
    "auftritte.pass.grund_ohne_log":
        "nessun analyze.log conservato per questo evento — vedi il log "
        "del servizio",
    "auftritte.pass.label_fehler": "Errore",
    "auftritte.pass.wer": "Chi",
    "auftritte.pass.titel_zeit": "Passaggio {zeit} — {tag}",
    # ---- verifyd-Innenseiten (Stufe 2, Tranche B) ----
    # Inline-Handler in verifyd.py (_banner, Setup-Wizard, Today-Leer-
    # zustaende, /unbekannte, /live_alerts, /video, /event/<id>);
    # Stufe-2-Grenzen s. en.py-Abschnittskommentar.
    "banner.schoner":
        "Frigate non risponde — nuovi tentativi ogni pochi secondi finché "
        "non torna disponibile; l’interfaccia continua a mostrare i dati "
        "locali.",
    "banner.fehler":
        "Frigate non raggiungibile (ultimo errore {zeit}): {fehler} — "
        "l’interfaccia continua a mostrare i dati locali.",
    "setupwiz.frigate.status_ok":
        "✓ Connessione riuscita — telecamere trovate: {n}",
    "setupwiz.frigate.status_fehl":
        "✗ Impossibile raggiungere Frigate: {fehler}",
    "setupwiz.frigate.status_fehl_keine": "nessuna telecamera",
    "setupwiz.frigate.status_fehl_hinweis":
        "Correggi l’URL (o imposta FRIGATE_URL nel tuo .env / "
        "docker-compose) e ripeti il test.",
    "setupwiz.frigate.status_leer":
        "Inserisci l’URL di Frigate e testa la connessione.",
    "setupwiz.frigate.titel": "Connessione a Frigate",
    "setupwiz.frigate.satz":
        "suslik legge le tue telecamere direttamente dall’API di Frigate "
        "(di solito sulla porta 5000). Nessuna telecamera è fissata nel "
        "codice.",
    "setupwiz.frigate.knopf_test": "Testa la connessione",
    "setupwiz.kameras.titel": "Scegli telecamere &amp; condizioni",
    "setupwiz.kameras.satz":
        "Spunta le telecamere da sorvegliare; spunta una o più zone per "
        "analizzare solo gli eventi che vi sono entrati (ad es. persona "
        "in giardino). Nessuna spunta = tutti gli eventi.",
    "setupwiz.kameras.satz_ohne":
        "Collegati prima a Frigate — le tue telecamere compariranno qui.",
    "setupwiz.backend.titel": "Accelerazione",
    "setupwiz.backend.verfuegbar": "Disponibili su questa macchina:",
    "setupwiz.backend.satz_wahl": "Scegline uno — la CPU funziona sempre.",
    "setupwiz.import.titel": "Importa volti da Frigate",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/mitte/nach rahmen die
    # hervorgehobenen Zahlen, Rand-Leerzeichen gehoeren zum Wert.
    "setupwiz.import.zahl_vor": "Frigate ha già ",
    "setupwiz.import.zahl_mitte": " immagine/i di riferimento di ",
    "setupwiz.import.zahl_nach": " persona/e.",
    "setupwiz.import.satz":
        "Importale: così suslik riconosce tutti fin dall’inizio. Le "
        "immagini vengono scaricate rapidamente, poi suslik calcola le "
        "proprie caratteristiche dei volti sul tuo acceleratore (GPU/NPU).",
    "setupwiz.import.knopf": "Importa {n} volti da Frigate",
    "setupwiz.import.satz_leer":
        "Ancora nessun volto in Frigate. Nota: suslik ha bisogno di "
        "almeno un volto di riferimento prima di poter riconoscere "
        "qualcuno — importa qui da Frigate, oppure carica delle foto più "
        "tardi nella pagina Conosciuti.",
    "setupwiz.import.satz_ohne":
        "Collegati prima a Frigate — poi potrai importare qui i suoi "
        "volti conosciuti.",
    "setupwiz.fertig.knopf": "Salva &amp; avvia suslik",
    "setupwiz.fertig.satz":
        "Salva le tue scelte e riavvia il servizio una sola volta.",
    "setupwiz.restore.titel": "Hai già una configurazione?",
    # Zitat-Folge Tranche C: nennt system.titel + system.backup.titel
    # wortgleich ("Sistema" / "Backup della configurazione").
    "setupwiz.restore.satz":
        "Se in passato hai esportato una configurazione di suslik "
        "(Sistema → Backup della configurazione), caricala qui per "
        "ripristinare tutte le impostazioni e saltare la procedura "
        "guidata.",
    "setupwiz.restore.knopf": "Carica il file di configurazione…",
    "setupwiz.write.titel": "Scrivere su Frigate?",
    "setupwiz.write.satz":
        "suslik può riscrivere i suoi esiti su Frigate (sub_labels) e "
        "sincronizzare i riferimenti, per farli funzionare in parallelo. "
        "La sola lettura è l’impostazione predefinita sicura.",
    "setupwiz.write.opt_ro":
        "Sola lettura (consigliata) — suslik non scrive mai su Frigate",
    "setupwiz.write.opt_rw":
        "Scrittura su Frigate (funzionamento in parallelo)",
    "setupwiz.willkommen.titel": "Ti diamo il benvenuto in suslik",
    "setupwiz.willkommen.satz":
        "Una breve procedura guidata — oppure carica una configurazione "
        "esistente per saltarla. Tutto ciò che vedi qui si può modificare "
        "più tardi nelle pagine normali.",
    # leer.*: Today-Leerzustaende + verstreute webui.leer()-Stellen.
    # "All" ist Anzeige==Kennung (§8.2, routes/areas) — bleibt woertlich.
    "leer.passe_area_heute":
        "Oggi nessun passaggio ha ancora toccato {area}.",
    "leer.passe_area_tag":
        "Nessun passaggio ha toccato {area} in questo giorno.",
    "leer.passe_area_hinweis":
        "Il chip All qui sopra mostra l’intera proprietà.",
    "leer.passe_heute": "Oggi ancora nessun passaggio con un volto.",
    "leer.passe_heute_hinweis":
        "Appena qualcuno attraversa la proprietà, il passaggio compare "
        "qui.",
    "leer.tag": "Niente con un volto in questo giorno.",
    "leer.tag_hinweis":
        "Usa le frecce per guardare un altro giorno, oppure apri Eventi "
        "per l’elenco completo.",
    "leer.frigate": "Ancora nessun Frigate collegato.",
    "leer.frigate_hinweis":
        "Imposta l’URL di Frigate nella procedura guidata "
        "(pagina Sistema) — poi i passaggi compaiono qui da soli.",
    "leer.refs":
        "Collegato — ma ancora nessun volto di riferimento, quindi "
        "nessuno può essere riconosciuto.",
    "leer.refs_hinweis":
        "Importa i volti da Frigate o carica delle foto — entrambe le "
        "cose nella pagina Conosciuti. Poi suslik continua ad apprendere "
        "da solo dalle telecamere.",
    "leer.band_heute": "Oggi ancora niente con un volto.",
    "leer.band_tag": "Niente con un volto in questo giorno.",
    "leer.band_hinweis":
        "Le persone compaiono qui appena un passaggio viene analizzato.",
    "leer.person_unbekannt": "Persona sconosciuta.",
    "leer.kamera_unbekannt": "Telecamera sconosciuta.",
    "leer.kamera_unbekannt_hinweis":
        "I riquadri provengono solo dall’elenco telecamere di Frigate e "
        "dalle sentinelle salvate.",
    "unbekannte.name": "Sconosciuto {nummer}",
    "unbekannte.badge_eine": "chiaramente una sola persona",
    "unbekannte.badge_aehnlich": "somiglianza {wert}",
    "unbekannte.badge_einmal": "visto una volta",
    "unbekannte.meta_zeit": " apparizioni · {zeit}",
    "unbekannte.knopf_reaktivieren": "riattiva",
    "unbekannte.attr_name": "Nome (nuovo o esistente)",
    "unbekannte.knopf_zuweisen": "Assegna persona",
    "unbekannte.knopf_ignorieren": "Ignora",
    "unbekannte.opt_merge": "unisci a…",
    "unbekannte.knopf_ok": "OK",
    "unbekannte.badge_gleiche": "stessa persona?",
    "unbekannte.knopf_merge": "Unisci",
    "unbekannte.knopf_verschieden": "Persone diverse",
    "unbekannte.titel": "Sconosciuti",
    "unbekannte.kopf_satz":
        "Volti che non corrispondono a nessuna persona conosciuta, "
        "raggruppati in identità ricorrenti.",
    # Kopf-Erklaerung an den <b>-Grenzen gesplittet; die Fett-Teile sind
    # die knopf_*-Schluessel selbst (eine Quelle, kein Drift).
    "unbekannte.kopf_satz_zuweisen":
        " collega un riquadro a una persona (nuova o esistente, digita "
        "il nome),",
    "unbekannte.kopf_satz_ignorieren":
        " silenzia un estraneo conosciuto (nessun avviso).",
    "unbekannte.kopf_satz_auto":
        "I volti nuovi arrivano qui automaticamente dopo ogni passaggio.",
    "unbekannte.knopf_reorg": "Riorganizza ora",
    "unbekannte.hinweis_reorg":
        "ricontrolla i volti estratti e ricostruisce i gruppi — "
        "l’estrazione vera e propria avviene automaticamente (1-2 min)",
    "unbekannte.h_wieder": "Ricorrenti",
    "unbekannte.h_einzeln":
        "{n} apparizioni singole (viste una sola volta finora)",
    "unbekannte.h_besucher": "{n} visitatori conosciuti (silenziati)",
    "unbekannte.h_objekte":
        "{n} oggetti statici (rilevati automaticamente — non persone)",
    "unbekannte.satz_objekte":
        "Gruppi le cui immagini sono quasi identiche tra loro e non "
        "somigliano a nessuna persona — in genere un passaruota, la "
        "pavimentazione o un gioco di luce che il rilevatore continua a "
        "scambiare per un volto. Sono congelati: i nuovi volti trovati "
        "non vengono mai aggiunti qui (formano gruppi nuovi e visibili e "
        "vengono ricontrollati dalla stessa regola) — i gruppi restano "
        "in elenco, così nulla viene nascosto.",
    "unbekannte.leer": "Ancora nessun volto sconosciuto.",
    "unbekannte.leer_hinweis":
        "Le identità compaiono qui dopo il prossimo visitatore "
        "sconosciuto.",
    "livealerts.link_video": "&#9654; video {n}",
    "livealerts.person_unbekannt": "sconosciuto",
    # "trigger" ist im IT-Bestand etabliertes Lehnwort (live.zaehler.*),
    # im Plural unveraendert — beide t_n-Formen identisch.
    "livealerts.trigger.eins": "{n} trigger",
    "livealerts.trigger.viele": "{n} trigger",
    "livealerts.kanal_keiner": "non inviato (nessun canale)",
    "livealerts.keine_bilder": "nessuna immagine salvata",
    "livealerts.titel": "Avvisi delle sentinelle live",
    "livealerts.kopf.auftritte.eins": "{n} apparizione",
    "livealerts.kopf.auftritte.viele": "{n} apparizioni",
    "livealerts.kopf.satz":
        " il {tag} — controllo rapido, preliminare; l’esito confermato "
        "arriva dall’analisi normale.",
    "livealerts.kopf.satz_alt":
        "Le voci precedenti alla 0.1.0.190 non hanno immagine né nome "
        "registrati.",
    "livealerts.leer": "Nessun avviso live in quel giorno.",
    "video.fehl":
        "&#9888; Transcodifica non riuscita — vedi il log del servizio "
        "(/log).",
    "video.fehl_hinweis":
        "Ricarica questa pagina per riprovare, oppure apri il video "
        "originale:",
    "video.warte": "Preparazione del video per il browser (H.264)&nbsp;…",
    "video.warte_satz":
        "Questa pagina si aggiorna da sola. La copia viene creata una "
        "volta e poi resta nella cache.",
    "event.ours_zeile.eins": "{person} — {stufe} (presente in {n} finestra)",
    "event.ours_zeile.viele":
        "{person} — {stufe} (presente in {n} finestre)",
    "event.ours_keiner": "nessuna corrispondenza con nessuno",
    "event.ours_rest.eins": " · {n} altra: nessuna corrispondenza",
    "event.ours_rest.viele": " · {n} altre: nessuna corrispondenza",
    "event.grenze":
        "sotto questa linea: corrispondenze deboli (miglior punteggio "
        "&lt; {wert}) — il nome è solo un’ipotesi, potrebbe trattarsi di "
        "un’altra persona",
    "event.gruppe_ohne": "Senza attribuzione",
    "event.badge_unsicher": "incerto",
    "event.leer_crops": "Nessun ritaglio di volto salvato per questo evento.",
    "event.knopf_video": "&#9654; Video",
    "event.knopf_log": "Log dell’analisi",
    "event.attr_unvollstaendig":
        "video incompleto — letti {gelesen}/{soll} fotogrammi; esito "
        "basato sulla parte leggibile",
    "event.badge_unvollstaendig": "⚠ video incompleto",
    "event.pass_zurueck": "&#8592; precedente",
    "event.pass_weiter": "successivo &#8594;",
    "event.pass_teil": "Parte di un passaggio",
    "event.pass_events.eins": "{n} evento",
    "event.pass_events.viele": "{n} eventi",
    "event.pass_knopf": "vedi passaggio",
    "event.label_grund": "Motivo dell’errore",
    "event.grund_ohne_zeile":
        "analyze.log non contiene una riga con il motivo — usa il "
        "pulsante del log qui sotto",
    "event.grund_ohne_log":
        "nessun analyze.log conservato per questo evento — vedi il log "
        "del servizio (pagina Sistema)",
    "event.zurueck": "← Oggi",
    "event.label_korrektur": "Correggi se è sbagliato",
    "event.label_wer": "Chi era?",
    "event.h_bilder": "Immagini",
    # ---- Routen-Seiten (Stufe 2, Tranche C) ----
    # routes/system.py, routes/vision.py, routes/visiontest.py,
    # routes/visionwizard.py, routes/personwizard.py, webui/bausteine.py.
    # Grenzen wie en.py-Abschnittskommentar. Terminologie: begriffe_tabellen.md
    # (IT): passaggio/volto/avviso/estraneo/gruppo/esito/corrispondenza;
    # Modell-Training -> apprendimento (ML-Sperrwort der Tabelle vermieden);
    # armed -> inserito/disinserito (Alarmanlagen-Register); Lernlauf-run ->
    # sessione, Vision-Testlauf -> esecuzione.
    # --- routes/system.py ---
    "system.ampel.service": "Servizio",
    # "(session)" = seit Dienststart — "dall’avvio" statt "sessione"
    # (Kollision mit sessione = Lernlauf, Muster live.zaehler.kopf).
    "system.ampel.service_info": "elaborati in totale: {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — autotest OK",
    "system.ampel.backend_fail":
        "{backend} — autotest FALLITI: {n} (vedi il log del servizio)",
    "system.ampel.analyse": "Analisi",
    "system.ampel.analyse_dauer": "ultima durata {s} s",
    "system.ampel.analyse_nie": "ancora nessuna analisi",
    "system.ampel.retry": "Coda dei nuovi tentativi",
    "system.ampel.retry_info":
        "{offen} aperti / {aufgegeben} abbandonati (finestra {tage} gg)",
    "system.ampel.frigate_unkonfiguriert":
        "non ancora configurato — imposta l’URL nella procedura guidata "
        "iniziale",
    "system.ampel.frigate_ok": "raggiungibile",
    # {zeit} kommt vorformatiert (%H:%M) aus der Route (B19-Stufe).
    "system.ampel.frigate_fehler": "ultimo errore {zeit}",
    # {s} vorformatiert (:.0f) — Formatspezifika nie in Werte (§8.8).
    "system.ampel.mqtt_hb": "heartbeat {s} s fa",
    "system.ampel.mqtt_kein_hb": "ancora nessun heartbeat",
    "system.ampel.mqtt_pub_aus": "configurato, pubblicazione disattivata",
    "system.ampel.mqtt_pub_kaputt":
        "configurato, publisher non avviato — vedi il log del servizio",
    "system.ampel.mqtt_unkonfiguriert": "non configurato",
    "system.ampel.disk": "Disco",
    "system.ampel.disk_info2": "{gb} GB liberi · cache dei clip {cache} GB su {max} GB",
    "system.disk.titel": "Spazio su disco",
    "system.disk.satz": "I clip sono una cache: conservati {tage} giorni, con un tetto di {max} GB, e sfoltiti non appena restano meno di {min} GB liberi (verifica dopo ogni evento e controllo giornaliero del disco, che passa a ogni 10 minuti finché lo spazio scarseggia).",
    "system.disk.knopf": "Pulisci ora",
    "system.disk.warnung": "Restano solo {gb} GB liberi e la cache dei clip è già vuota — libera spazio sul volume dati, altrimenti i nuovi eventi non potranno essere salvati.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "CONTROLLA",
    "system.drift.banner":
        "CONTROLLO ANTI-DERIVA IN ROSSO dopo l’ultima aggiunta di "
        "riferimenti:",
    "system.sync.titel": "Sincronizzazione con Frigate",
    "system.sync.knopf": "Apri la sincronizzazione Frigate",
    "system.sync.satz":
        "La pagina di sincronizzazione confronta i due archivi di volti "
        "persona per persona, sottopone ogni candidato al controllo "
        "preliminare proprio come fa Frigate, invia solo ciò che spunti e "
        "importa ciò che ha solo Frigate.",
    "system.sync.fehlt":
        "non ancora disponibile — servono un Frigate raggiungibile e "
        "almeno un volto di riferimento",
    "system.qc.titel": "Rapporto controllo qualità",
    "system.qc.stand": "(aggiornato al {stand}, {tage} giorni)",
    "system.qc.kopf_gesicht": "con volto",
    "system.qc.kopf_bestaetigt": "confermati",
    "system.qc.kopf_quote": "quota finestra",
    # WIRD ZITIERT: setupwiz.restore.satz nennt diesen Titel wortgleich.
    "system.backup.titel": "Backup della configurazione",
    "system.backup.satz":
        "Scarica le impostazioni salvate in /data/config come un unico "
        "file JSON, oppure ripristinale da un file di questo tipo. Limite "
        "onesto: oggi si tratta della SCHEDA TELECAMERE (inclusi i suoi "
        "valori salvati); le soglie e i canali impostati solo in "
        "verifyd.yaml o tramite variabili d’ambiente NON sono in questo "
        "file. Persone apprese/riferimenti: usa il backup completo qui "
        "sotto.",
    "system.backup.knopf_download": "Scarica la configurazione",
    "system.backup.knopf_restore": "Ripristina da file…",
    "system.backup.careful": "Attenzione:",
    # {hinweis} = seit Tranche D der Schluessel system.backup.hinweis
    # (Konstante VISION_EXPORT_HINWEIS ist auf die Sprachschicht umgezogen).
    "system.backup.careful_config":
        "questo file {hinweis} (canali di notifica e rilevamento visione), "
        "in modo che un ripristino su un’altra macchina funzioni davvero.",
    "system.backup.restore_satz":
        "Il ripristino sovrascrive le impostazioni attuali (le precedenti "
        "restano come .bak) e riavvia il servizio.",
    "system.voll.titel": "Backup completo",
    "system.voll.satz":
        "Un unico archivio portabile con tutto ciò che hai insegnato a "
        "questa installazione: impostazioni, l’archivio dei volti di "
        "riferimento, i risultati delle sessioni di apprendimento, tutto "
        "il materiale del riconoscimento della persona (immagini, i tuoi "
        "giudizi di revisione, i modelli appresi) e il registro degli "
        "eventi. Pensato per il trasferimento su un’altra macchina. Limite "
        "onesto: la cache dei video e gli artefatti di analisi per evento "
        "NON sono inclusi — si ricostruiscono col tempo.",
    "system.voll.knopf_download": "Scarica il backup completo",
    "system.voll.knopf_restore": "Ripristina il backup completo…",
    "system.voll.careful": "questo archivio {hinweis}.",
    "system.voll.restore_satz":
        "Il ripristino sostituisce quelle parti (ognuna delle precedenti "
        "viene conservata una volta come *.pre-restore-*) e riavvia il "
        "servizio. Caricare qualche centinaio di MB può richiedere un "
        "po’ — lascia la pagina aperta.",
    "system.live.titel": "Sentinelle live",
    "system.live.alerts": "Avvisi inviati oggi: {kanaele}",
    "system.live.stoerungen": "Segnalazioni di anomalia oggi: {n}",
    "system.live.knopf": "Apri le sentinelle live",
    "system.live.quelle":
        "Contati dal log dei messaggi del motore stesso — solo i "
        "messaggi realmente accettati da un canale. Gli avvisi delle "
        "sentinelle live sono separati dai contatori degli avvisi "
        "dell’analisi eventi nella pagina Oggi.",
    "system.write.titel": "Scrittura su Frigate",
    "system.write.satz":
        "suslik riscrive su Frigate o si limita a leggere? La sola "
        "lettura è l’impostazione predefinita sicura; attiva la scrittura "
        "solo per il funzionamento in parallelo (riconoscimento facciale "
        "di Frigate + suslik).",
    "system.write.aktuell": "Attuale:",
    "system.write.zustand_ro":
        "SOLA LETTURA — suslik non scrive su Frigate",
    "system.write.zustand_rw": "SCRITTURA su Frigate — sub_labels",
    "system.write.zustand_rw_sync": " + sincronizzazione dei riferimenti",
    "system.write.knopf_rw": "Attiva la scrittura",
    "system.write.knopf_ro": "Sola lettura",
    # WIRD ZITIERT: setupwiz.restore.satz — wortgleich mit nav.system.
    "system.titel": "Sistema",
    "system.tools.titel": "Strumenti",
    "system.docs.titel": "Documentazione",
    "system.docs.link": "Documentazione su GitHub",
    # --- routes/vision.py ---
    "vision.zeit.nie": "mai",
    "vision.titel": "Rilevamento visione",
    "vision.kopf.dirty": "non salvato",
    "vision.hinweis.titel": "Cosa ti serve per questo",
    "vision.schalter.knopf_aus": "Disattiva",
    "vision.schalter.knopf_an": "Attiva",
    "vision.schalter.fehlt": "Manca ancora:",
    "vision.schalter.titel_an": "Il rilevamento visione è attivo",
    "vision.schalter.titel_aus": "Il rilevamento visione è disattivato",
    "vision.schalter.aus_satz":
        "Finché è disattivato non viene inviato nulla a nessuno e nessuna "
        "immagine lascia questa macchina.",
    "vision.frage.titel": "Come viene posto un confronto",
    "vision.frage.doppel_titel":
        "Chiedi ogni coppia due volte, con le gallerie scambiate",
    "vision.frage.doppel_satz":
        "È il controllo di posizione. A nella prima esecuzione e B in "
        "quella scambiata indicano la STESSA galleria, quindi una "
        "contraddizione smaschera un modello che preferisce semplicemente "
        "ciò che viene prima. Misurato qui: in tutte le nostre serie di "
        "test ogni risposta sbagliata è stata una «A», mai una «B». "
        "Disattivarlo dimezza le richieste &mdash; ma allora un confronto "
        "si regge su una sola risposta, senza nulla che la verifichi.",
    "vision.meld.titel": "Messaggi aggiuntivi",
    "vision.meld.satz":
        "Entrambi sono disattivati finché non li attivi tu, e nessuno dei "
        "due cambia gli avvisi esistenti: la visione non può crearne uno, "
        "annullarne uno o scavalcare i percorsi del volto e del corpo.",
    "vision.meld.judged_titel":
        "Fammi sapere quando un passaggio è stato giudicato",
    "vision.meld.judged_satz":
        "Una breve nota sui tuoi canali abituali quando l’esito è pronto "
        "&mdash; con il conteggio reale dei voti. Arriva dopo la fine del "
        "passaggio; con un modello locale possono passare minuti. "
        "Un’informazione, non un’emergenza.",
    "vision.meld.alarm_titel":
        "Avvisami quando la visione contraddice il riconoscimento del "
        "corpo",
    "vision.meld.alarm_satz":
        "Scatta solo quando un’esecuzione c’è stata davvero, il modello "
        "ha risposto e comunque non ha confermato nessuno. Resta in "
        "silenzio quando semplicemente non c’era abbastanza materiale "
        "&mdash; sarebbe solo rumore. Riconoscere le persone che gli hai "
        "insegnato è il lato forte di questo percorso, quindi una mancata "
        "conferma significa qualcosa; respingere gli estranei è il lato "
        "debole, quindi la visione non vota mai in quella direzione.",
    "vision.kachel.was_key": "inserisci una chiave API",
    "vision.kachel.was_host": "inserisci host e porta",
    "vision.kachel.was_url": "inserisci un URL e una chiave facoltativa",
    "vision.kachel.titel": "Dove gira il modello",
    "vision.kachel.satz":
        "Scegli un fornitore. Per i tre indicati per nome l’indirizzo API "
        "ufficiale è già integrato &mdash; inserisci solo la tua chiave. "
        "Non viene inviato nulla a nessuno finché non sei tu a premere un "
        "pulsante.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; memorizzata &mdash; lascia vuoto per "
        "mantenerla",
    "vision.verb.key_pflicht_ph": "incolla qui la tua chiave",
    "vision.verb.key_frei_ph": "solo se il tuo server la richiede",
    "vision.verb.host": "Host",
    "vision.verb.host_ph": "il nome o l’indirizzo di quella macchina",
    "vision.verb.port": "Porta",
    "vision.verb.host_satz":
        "Solo la macchina &mdash; il resto dell’indirizzo lo aggiunge "
        "suslik da solo. La porta d’esempio è quella che llama.cpp usa in "
        "modo predefinito; usa quella su cui il tuo server è in ascolto.",
    "vision.verb.endpunkt": "URL dell’endpoint",
    "vision.verb.endpunkt_satz":
        "Quello è un esempio di endpoint compatibile OpenAI &mdash; "
        "sostituiscilo con il tuo se usi un altro fornitore.",
    "vision.verb.betriebsart": "Questo endpoint è",
    "vision.verb.betriebsart_extern": "su internet",
    "vision.verb.betriebsart_lokal": "nella mia rete",
    "vision.verb.adresse": "Indirizzo API",
    "vision.verb.adresse_satz":
        "Integrato &mdash; qui non c’è nulla che si possa digitare male.",
    "vision.verb.key": "Chiave API",
    "vision.verb.key_frei_satz":
        "Qui è facoltativa &mdash; la maggior parte dei server locali non "
        "la richiede. Premi comunque il pulsante: recupera anche l’elenco "
        "dei modelli del tuo server.",
    "vision.verb.titel": "Connessione",
    "vision.modell.titel": "Modello",
    "vision.modell.verweigert": "l’endpoint ha rifiutato la connessione",
    # {zeit} vorformatiert aus _zeit() — das Format bleibt in der Route (B19).
    "vision.modell.geprueft": "Verificato {zeit} su",
    "vision.modell.opt_wahl": "&mdash; scegline uno &mdash;",
    "vision.modell.ungetestet": "non testato qui",
    "vision.modell.opt_verschollen":
        " — salvato in precedenza, ora l’endpoint non lo elenca",
    "vision.modell.wahl_satz":
        "Scegline uno dall’elenco &mdash; la nota accanto a ogni nome è "
        "nostra, i nomi sono dell’endpoint.",
    "vision.modell.verschollen_satz":
        "Questo modello è salvato e ancora in uso, ma stavolta l’endpoint "
        "non lo ha elencato. Controlla il nome, oppure scegline uno "
        "dall’elenco.",
    "vision.modell.fremde_plattform": "misurato su un’altra piattaforma",
    "vision.modell.kein_rohergebnis":
        "nessun risultato grezzo archiviato per questo",
    "vision.modell.gemessen": "misurato {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "Non misurato qui &mdash; non è un giudizio, solo onestà. Esegui "
        "il test di connessione qui sotto prima di farci affidamento.",
    "vision.modell.manuell": "ID del modello a mano",
    "vision.modell.manuell_ph": "ID esatto del modello",
    "vision.modell.manuell_knopf": "Verifica questo ID",
    "vision.modell.manuell_satz":
        "Per gli endpoint che non elencano tutto: l’ID viene prima "
        "verificato con una minuscola richiesta di testo; nulla di non "
        "verificato può essere salvato.",
    "vision.prompt.standard_satz":
        "Questa è la formulazione predefinita misurata. Finché la lasci "
        "esattamente così, gli esiti non vengono contrassegnati come "
        "personalizzati.",
    "vision.prompt.titel": "La domanda che suslik pone",
    "vision.prompt.satz":
        "Puoi cambiare la formulazione. L’ultimo paragrafo è fisso: è "
        "l’istruzione di una sola parola da cui dipende il parser delle "
        "risposte, ed è ciò che è stato misurato.",
    "vision.prompt.knopf_zurueck": "Ripristina la formulazione predefinita",
    "vision.zahlen.think": "Disattiva il ragionamento del modello",
    "vision.zahlen.think_satz":
        "Attivo per impostazione predefinita dalla 0.1.0.211: sulle "
        "griglie di confronto difficili un modello che ragiona può "
        "parlare fino a esaurire il budget di token e l’esecuzione "
        "finisce senza esito. Gli endpoint rigorosi rifiutano l’opzione; "
        "suslik allora ripete la richiesta una volta senza di essa e lo "
        "dichiara.",
    "vision.zahlen.titel": "Limiti",
    "vision.zahlen.max_tokens": "Token massimi per risposta",
    "vision.zahlen.timeout": "Timeout per richiesta (s)",
    "vision.zahlen.satz":
        "In un’esecuzione 3000 token si sono rivelati insufficienti "
        "&mdash; la risposta è stata troncata e contata come «nessun "
        "esito», e la stessa domanda era corretta con 12000. Un modello "
        "locale su una macchina CPU richiede minuti per richiesta, uno "
        "online secondi.",
    "vision.cloud.ziel_fallback": "l’endpoint che configuri qui sopra",
    "vision.cloud.titel": "Invio di immagini a un servizio esterno",
    "vision.cloud.satz":
        "Quelle immagini non ritraggono solo chi vive qui: i casi incerti "
        "sono per lo più estranei &mdash; visitatori, corrieri, vicini, "
        "passanti. Il responsabile sei tu, non il gestore del servizio. "
        "La tua conferma viene scritta nel log di audit con data e ora; "
        "il ritorno a un modello locale la revoca.",
    "vision.cloud.bestaetigung": "Ho capito e confermo",
    "vision.cloud.bestaetigt": "(confermato {zeit})",
    "vision.test.treffer": "{n}/2 corrette",
    "vision.test.tokens": "{ist} token contro {soll}",
    "vision.test.falsch": " (sbagliata)",
    # ZITAT-FOLGE: js.vision.dirty_text UND js.vision.prompt_zurueck
    # zitieren diesen Knopf wortgleich — bei Aenderungen beide nachziehen.
    "vision.save.knopf": "Salva connessione",
    "vision.save.dirty":
        "modifiche non salvate &mdash; il riconoscimento usa ancora la "
        "connessione salvata",
    "vision.test.titel": "Testa questa connessione",
    "vision.test.knopf": "Esegui il test",
    "vision.test.nicht_gelaufen": "non eseguito",
    "vision.test.stufe1": "raggiungibilità",
    "vision.test.stufe2": "scelta obbligata",
    "vision.test.stufe3": "verifica dei token",
    "vision.test.ungetestet": "Ancora nessun test.",
    "vision.test.letzter": "Ultima esecuzione {zeit} su",
    "vision.galerien.stand_gut": "approvata {zeit} &middot; {zellen} celle",
    "vision.galerien.pruefen": "merita uno sguardo",
    "vision.galerien.keine": "ancora nessuna galleria",
    "vision.galerien.zu_wenig":
        "ancora troppo poche immagini del corpo approvate ({n} "
        "utilizzabili)",
    "vision.galerien.knopf_auffrischen": "Aggiornala",
    "vision.galerien.knopf_bauen": "Crea una galleria",
    "vision.galerien.zahl": "{n} immagini utilizzabili &middot; {reihen}",
    "vision.galerien.titel": "Gallerie",
    "vision.galerien.stand":
        "{n} gallerie pronte ({min} richieste) &mdash; alla visione ne "
        "servono almeno due, perché confronta sempre una persona con "
        "un’altra.",
    "vision.galerien.satz":
        "Una galleria può averla solo chi ha un modello del corpo "
        "appreso; le immagini vengono dal materiale del corpo che hai già "
        "approvato. La visione giudica solo le persone che ne hanno una, "
        "e lo dichiara nell’esito.",
    # --- routes/visiontest.py ---
    "visiontest.titel": "Test di riconoscimento",
    "visiontest.kopf.satz":
        "Volto e persona vengono letti da ciò che è stato registrato "
        "allora &mdash; nulla viene ricalcolato. La visione gira adesso, "
        "esattamente attraverso lo stesso percorso che usa nel "
        "funzionamento normale.",
    # Frueher Modulkonstante KOSTEN — §8.12: t() nie auf Modulebene.
    "visiontest.kosten":
        "Un’esecuzione di prova costa richieste reali, esattamente come "
        "il funzionamento normale: l’intero passaggio entra come una sola "
        "griglia di candidati, e ogni coppia di gallerie confrontata "
        "costa due richieste, perché ogni domanda viene posta di nuovo "
        "con le gallerie scambiate. Conta come clic manuale, quindi non "
        "consuma il tuo limite giornaliero &mdash; ma su un endpoint a "
        "pagamento sono soldi, e con un modello locale su CPU servono "
        "minuti.",
    "visiontest.wer.niemand": "nessuno riconosciuto",
    # EN-Klammerformen bleiben EINE Form je Schluessel (§8.18) —
    # IT-Muster "telecamera/e" wie js.syncauswahl/js.vw.
    "visiontest.wahl.kachel_zahlen":
        "{events} eventi &middot; {kameras} telecamera/e",
    "visiontest.wahl.vision_fertig": " &middot; visione completata",
    "visiontest.wahl.titel": "1 &middot; Quale passaggio",
    "visiontest.wahl.leer":
        "Ancora nessun passaggio registrato. Appena qualcuno attraversa "
        "la proprietà, compare qui.",
    "visiontest.wahl.kopf_zahlen":
        "{events} evento/i &middot; {kameras} telecamera/e",
    "visiontest.wahl.anderer": "scegli un altro passaggio",
    "visiontest.wahl.titel_offen": "1 &middot; Scegli un passaggio",
    "visiontest.wahl.anzahl": "passaggi recenti: {n}",
    "visiontest.wahl.satz":
        "I passaggi più recenti, raggruppati esattamente come nella "
        "pagina Oggi.",
    "visiontest.gesicht.kein_match": "senza corrispondenza",
    "visiontest.gesicht.gezeigt": "mostrate {gezeigt} di {gesamt} immagini",
    "visiontest.gesicht.ohne_bild":
        "nessuna immagine conservata per {fehlt} dei {unbek} eventi senza "
        "corrispondenza",
    "visiontest.gesicht.kein_bild":
        "per questo passaggio non è stata conservata nessuna immagine "
        "del volto",
    "visiontest.gesicht.keines": "nessun volto conosciuto",
    "visiontest.gesicht.zeile": "{person} &middot; {events} evento/i",
    # {best} vorformatiert (:.2f) aus der Route (§8.8).
    "visiontest.gesicht.best": " &middot; migliore {best}",
    "visiontest.gesicht.unbekannt":
        "{n} evento/i con un volto senza corrispondenza",
    "visiontest.gesicht.titel": "Volto",
    "visiontest.gesicht.quelle":
        "confronto degli embedding con i tuoi volti di riferimento "
        "&mdash; dai dati registrati di questo passaggio",
    "visiontest.koerper.kandidaten":
        "candidati, nessuno sopra la regola: {liste}",
    "visiontest.koerper.nichts": "nulla valutato",
    "visiontest.koerper.zeile":
        "{klasse} &middot; punteggio {score} su {schwelle} &middot; "
        "{quelle}",
    "visiontest.koerper.bild_weg": "immagine scaduta",
    "visiontest.koerper.titel": "Persona",
    "visiontest.koerper.quelle":
        "embedding DINOv2 + classificatore sulle immagini valutate di "
        "questo passaggio",
    "visiontest.log.warte":
        "in attesa del modello &mdash; questa pagina si aggiorna da sola",
    "visiontest.log.titel": "Cosa è successo",
    "visiontest.gitter.alt": "la griglia dei candidati di questa esecuzione",
    "visiontest.gitter.bildunterschrift":
        "l’immagine realmente mostrata al modello",
    "visiontest.gitter.zeile":
        "griglia dei candidati: {n} cella/e da questo passaggio, chieste "
        "come UNA sola immagine",
    "visiontest.gitter.luecken": " ({n} cella/e lasciate vuote)",
    "visiontest.runden.kein_votum": "nessun voto &mdash; {grund}",
    "visiontest.runden.paar": "{a} contro {b}",
    "visiontest.nach.laeuft": "Nuova analisi di questo passaggio in corso",
    "visiontest.nach.stand":
        "{fertig} di {gesamt} eventi completati &mdash; le immagini "
        "valutate si accumulano strada facendo, servono alcuni minuti. È "
        "silenziosa: niente avvisi, niente notifiche. Questa pagina si "
        "aggiorna da sola.",
    "visiontest.nach.titel":
        "Nulla è stato conservato per questo passaggio",
    "visiontest.nach.satz":
        "Analizzarlo di nuovo riporta le immagini valutate &mdash; e "
        "questo riempie tutti e tre i percorsi, non solo la visione. "
        "Esegue di nuovo l’analisi ordinaria sugli eventi di questo "
        "passaggio: silenziosa, senza avvisi, e aspetta il riconoscimento "
        "live invece di scavalcarlo.",
    "visiontest.nach.knopf": "Analizza di nuovo questo passaggio",
    "visiontest.felder.zellen": "celle della griglia per questa esecuzione",
    "visiontest.felder.voten": "conferme necessarie per questa esecuzione",
    "visiontest.felder.doppel":
        "chiedi ogni coppia due volte (controllo con scambio)",
    "visiontest.felder.satz":
        "Tutti e tre valgono solo per QUESTA esecuzione &mdash; nulla "
        "viene salvato e il funzionamento normale mantiene le proprie "
        "impostazioni. Questo passaggio ha {material} immagini "
        "utilizzabili &mdash; chiedere più celle di così va bene, la "
        "griglia diventa solo più piccola. {galerien} gallerie approvate "
        "permettono al massimo {voten_max} confronto/i. Con il controllo "
        "con scambio attivo un confronto costa due richieste; senza, una "
        "&mdash; e allora si regge su una sola risposta.",
    "visiontest.laeufe.abgebrochen":
        "interrotta (il servizio si è riavviato)",
    "visiontest.laeufe.kein_urteil": "nessun esito",
    "visiontest.laeufe.von": "di {n}",
    "visiontest.laeufe.ohne_tausch": "senza scambio",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} in sospeso",
    "visiontest.laeufe.titel": "Esecuzioni su questo passaggio",
    "visiontest.laeufe.kopf_wann": "quando",
    "visiontest.laeufe.kopf_zellen": "celle",
    "visiontest.laeufe.kopf_noetig": "necessari",
    "visiontest.laeufe.kopf_backend": "backend",
    "visiontest.laeufe.kopf_urteil": "esito",
    "visiontest.laeufe.kopf_voten": "voti",
    "visiontest.laeufe.kopf_anfragen": "rich.",
    "visiontest.laeufe.kopf_zeit": "tempo",
    "visiontest.laeufe.satz":
        "Le più recenti per prime. Solo ciò che è stato eseguito davvero "
        "&mdash; l’elenco viene dal log di questo passaggio e sparisce "
        "con lui.",
    "visiontest.vision.titel": "Visione",
    "visiontest.vision.quelle_kurz":
        "un modello di visione che confronta questo passaggio con le tue "
        "gallerie",
    "visiontest.vision.unkonfiguriert": "non configurato",
    "visiontest.vision.attr_nichts": "non c’è ancora nulla da confrontare",
    "visiontest.vision.knopf": "Esegui la visione su questo passaggio",
    "visiontest.vision.nichts_satz":
        "ancora nulla da confrontare &mdash; prima analizza di nuovo "
        "questo passaggio (pulsante qui sopra)",
    "visiontest.vision.laeuft_satz":
        "un’esecuzione è in corso proprio ora &mdash; il log qui sotto "
        "cresce man mano",
    "visiontest.vision.startet": "avvio &mdash; ancora nessun dato",
    "visiontest.vision.quelle":
        "scelta obbligata contro le tue gallerie: l’intero passaggio "
        "entra come UNA sola griglia di candidati, e ogni coppia viene "
        "chiesta due volte con le gallerie scambiate",
    "visiontest.vision.nicht_gelaufen": "non eseguita per questo passaggio",
    "visiontest.vision.verglichen":
        "ha confrontato {a} con {b} &mdash; non dice nulla su nessun "
        "altro",
    "visiontest.vision.abgebrochen":
        "esecuzione interrotta &mdash; il servizio si è riavviato",
    "visiontest.vision.kein_urteil": "nessun esito &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten} di {bilder} confronto/i hanno dato una risposta "
        "&middot; {anfragen} richieste &middot; {dauer} s &middot; "
        "esecuzione {zeit}",
    "visiontest.vision.reihenfolge": " &middot; ordine: {quelle}",
    "visiontest.vision.custom_prompt": " &middot; prompt personalizzato",
    "visiontest.drei.titel": "2 &middot; Cosa dicono i tre percorsi",
    "visiontest.drei.satz":
        "Stesso passaggio, tre giudizi indipendenti. Possono non essere "
        "d’accordo &mdash; è proprio il senso di guardarli insieme.",
    # --- routes/visionwizard.py ---
    "visionwizard.schritt.person": "scegli una persona",
    "visionwizard.schritt.groesse": "scegli una dimensione",
    "visionwizard.schritt.vorschlag": "controlla la proposta",
    "visionwizard.schritt.abnahme": "approva",
    "visionwizard.titel": "Crea una galleria",
    "visionwizard.kopf.satz":
        "Una galleria è una piccola griglia di immagini di una persona "
        "&mdash; è ciò con cui il modello di visione confronta una nuova "
        "immagine. Viene costruita dalle immagini del corpo che hai già "
        "approvato; non viene registrato nulla di nuovo e nessun video "
        "viene aperto.",
    "visionwizard.person.stand_gut": "galleria approvata {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} immagini utilizzabili &mdash; non bastano ancora per una "
        "galleria. Esegui l’apprendimento della persona su altri "
        "passaggi.",
    "visionwizard.person.max_gitter":
        "griglia più grande possibile con questo materiale: {n}",
    "visionwizard.person.titel": "1 &middot; Quale persona",
    "visionwizard.person.satz":
        "Qui compaiono solo le persone con un modello del corpo appreso, "
        "e i conteggi sono le immagini che superano il filtro di "
        "dimensione (almeno 350 pixel di altezza) &mdash; non tutto ciò "
        "che è mai stato estratto.",
    "visionwizard.groesse.zellen": "{n} celle",
    "visionwizard.groesse.titel": "2 &middot; Quante immagini",
    "visionwizard.zelle.leer":
        "niente più immagini per questa riga &mdash; e nemmeno nulla da "
        "prendere in prestito",
    "visionwizard.zelle.geliehen": "dalla riga {reihe}",
    "visionwizard.zelle.knopf_weg": "non va bene",
    # Tranche D: {reihe} traegt Adjektive im Singular (frontale/laterale/
    # posteriore/incerta) — Rahmen numerus-neutral gestellt (frueher
    # "immagini {reihe} pulite", das braeuchte Plural-Adjektive).
    "visionwizard.reihe.geliehen":
        "{n} riempite da un’altra vista &mdash; non c’erano abbastanza "
        "immagini pulite della vista {reihe}",
    "visionwizard.reihe.luecken":
        "non è stato possibile riempire {n} cella/e",
    "visionwizard.reihe.spreizung": "{tage} giorno/i, {kameras} telecamera/e",
    "visionwizard.reihe.kopf": "vista {reihe}",
    "visionwizard.reihe.eigene": "{eigene} di {gesamt} da questa vista",
    "visionwizard.vorschlag.abgelehnt":
        "{n} immagine/i che avevi rifiutato restano memorizzate e non "
        "torneranno.",
    "visionwizard.vorschlag.titel": "3 &middot; Va bene così?",
    "visionwizard.vorschlag.grenze":
        "Limite onesto: sono misurazioni dell’immagine, non del momento. "
        "Un’immagine in cui qualcuno si lega i capelli o si china le "
        "supera tutte quante &mdash; è per questo che servono i tuoi "
        "occhi.",
    "visionwizard.vorschlag.knopf": "Approva questa galleria",
    "visionwizard.vorschlag.kopie_satz":
        "Con l’approvazione queste immagini vengono copiate nella "
        "cartella della galleria. Da quel momento la galleria è fissa: "
        "eliminare più tardi un originale non può bucarla &mdash; suslik "
        "ti chiede solo di approvarla di nuovo.",
    "visionwizard.fertig.geliehen": " &middot; in prestito",
    "visionwizard.fertig.titel": "Galleria approvata",
    "visionwizard.fertig.stand": "{zellen} celle, approvata {zeit}.",
    "visionwizard.fertig.satz":
        "Sono copie dentro la cartella della galleria, con l’origine di "
        "ogni immagine (sessione, file, checksum) annotata accanto. "
        "Viaggiano con il tuo backup.",
    "visionwizard.fertig.knopf_neu": "Ricostruiscila dal materiale attuale",
    "visionwizard.fertig.knopf_zurueck": "Torna a Rilevamento visione",
    "visionwizard.neu.titel": "Nuovo materiale disponibile",
    "visionwizard.neu.satz":
        "Non cambia nulla da solo &mdash; la galleria che hai approvato "
        "resta esattamente com’è finché non ne costruisci e approvi una "
        "nuova.",
    # --- routes/personwizard.py ---
    "personwizard.wer.alle": "tutte le persone conosciute",
    "personwizard.wer.fremde": "estranei",
    "personwizard.titel": "Apprendimento persone — riconoscimento del corpo",
    "personwizard.kopf.satz":
        "Un secondo percorso di riconoscimento indipendente: apprende "
        "l’aspetto COMPLESSIVO di una persona (corporatura, capelli, "
        "postura) per riconoscere chi vive in casa anche quando nessun "
        "volto è visibile.",
    "personwizard.kopf.wie_titel":
        "Come funziona — il controllo resta a te",
    "personwizard.kopf.schritt1":
        "1 · Scegli tu quanti eventi esaminare e CHI apprendere (una "
        "persona, o tutte le persone conosciute).",
    "personwizard.kopf.schritt2":
        "2 · La sessione estrae immagini a figura intera dalle tue "
        "registrazioni. Un’immagine viene collegata a una persona solo "
        "quando lo dimostra un passaggio confermato dal volto — "
        "volutamente prudente.",
    "personwizard.kopf.schritt3":
        "3 · TU rivedi ogni immagine estratta; un clic rifiuta quella "
        "sbagliata. Nulla viene appreso senza la tua approvazione.",
    "personwizard.kopf.schritt4":
        "4 · L’apprendimento del modello avviene poi in locale in pochi "
        "secondi, e viene misurata una soglia di decisione così che gli "
        "estranei restino sotto.",
    "personwizard.kopf.tempo":
        "Una nota sulla velocità: l’estrazione per ora gira sulla CPU, "
        "quindi porta pazienza se una sessione richiede un po’ di tempo "
        "(circa 15&ndash;30 s per evento). Lo spostamento su GPU/NPU è "
        "previsto per una versione futura.",
    "personwizard.kopf.warum":
        "Perché prima almeno una persona: questo percorso sa distinguere "
        "le persone solo dopo aver appreso — con la tua revisione — "
        "l’aspetto di almeno una persona di casa. Fino ad allora il "
        "riconoscimento del corpo resta SPENTO e non invia mai avvisi. "
        "Quando più avanti avviserà (Pushover/Telegram), il messaggio "
        "sarà contrassegnato come proveniente dal riconoscimento della "
        "persona, non dal riconoscimento facciale.",
    "personwizard.vorb.titel": "Preparazione della sessione &hellip;",
    "personwizard.vorb.zeile":
        "collegamento degli ultimi {n} eventi a {wer} tramite passaggi "
        "confermati",
    "personwizard.vorb.satz":
        "Richiede un minuto o due — la pagina si aggiorna da sola, "
        "subito dopo parte l’estrazione.",
    "personwizard.ernte.stand":
        "{events}/{von} eventi · {bilder} immagini estratte",
    "personwizard.ernte.startet": "avvio …",
    "personwizard.ernte.titel":
        "Una sessione di apprendimento della persona è in corso",
    "personwizard.ernte.zeile": "in apprendimento: {wer} · {stand}",
    "personwizard.ernte.satz":
        "Questa pagina si aggiorna da sola. Una nuova sessione si può "
        "avviare quando questa è finita.",
    "personwizard.ernte.knopf_abbruch": "Interrompi la sessione",
    "personwizard.ernte.abbruch_hinweis": "le immagini estratte restano",
    "personwizard.unterbrochen.titel":
        "L’ultima sessione è stata interrotta",
    "personwizard.unterbrochen.satz":
        "Probabilmente un riavvio del servizio. Avvia di nuovo la stessa "
        "sessione qui sotto — gli eventi già estratti vengono saltati "
        "automaticamente (ripartenza), non si perde nulla.",
    "personwizard.abnahme.titel":
        "Ultima sessione completata — ora tocca alla tua revisione",
    "personwizard.abnahme.zeile":
        "{n} immagini estratte per {wer} (sessione {lauf}).",
    "personwizard.abnahme.knopf": "Rivedi subito le immagini",
    "personwizard.abnahme.hinweis":
        "completa la revisione per sbloccare la prossima sessione",
    "personwizard.abnahme.knopf_verwerfen": "Scarta questa sessione",
    "personwizard.abnahme.verwerfen_hinweis":
        "risultato scadente? butta via tutto",
    "personwizard.leer.verwaist":
        "Saltati di proposito: {liste} — questi nomi sono stati eliminati "
        "dall’elenco delle tue persone; i loro vecchi eventi confermati "
        "restano come cronologia ma non vengono estratti.",
    "personwizard.leer.titel":
        "Sessione finita senza immagini — ecco perché",
    "personwizard.leer.satz":
        "Non è stato cambiato nulla; puoi avviare un’altra sessione qui "
        "sotto in qualsiasi momento.",
    "personwizard.fertig.verwaist":
        "Saltati di proposito: {liste} — persone eliminate; i loro "
        "vecchi eventi confermati non vengono estratti.",
    "personwizard.fertig.fremd":
        "{n} immagini di estranei confermate trasferite nel gruppo degli "
        "estranei — il prossimo apprendimento le usa subito.",
    "personwizard.fertig.titel":
        "Revisione completata — materiale acquisito",
    "personwizard.fertig.zeile":
        "{abgenommen} immagini approvate come materiale di "
        "apprendimento, {verworfen} rifiutate (sessione {lauf}).",
    "personwizard.fertig.knopf": "Vedi il materiale appreso",
    "personwizard.fehler.titel": "L’ultima sessione è fallita",
    "personwizard.auswahl.opt_alle": "Tutte le persone conosciute",
    "personwizard.auswahl.opt_fremde":
        "Estranei — estrai immagini di estranei",
    "personwizard.auswahl.titel": "Chi apprendere",
    "personwizard.auswahl.satz":
        "Scegli una sola persona per una revisione in lotti piccoli e "
        "mirati — oppure tutte insieme. Le persone vengono dal tuo "
        "archivio dei volti; apprenderne una alla volta tiene corta la "
        "revisione.",
    "personwizard.auswahl.fremde_satz":
        "Estranei: estrae dai passaggi in cui non è stato riconosciuto "
        "nessuno (passaggi solo in strada, visitatori non confermati). "
        "Nella revisione confermi tu chi è davvero un estraneo — "
        "finiscono nel gruppo degli estranei e affinano la soglia di "
        "decisione.",
    "personwizard.umfang.knopf_letzte": "ultimi {n}",
    "personwizard.umfang.attr_eigen": "N personalizzato",
    "personwizard.umfang.knopf_go": "vai",
    "personwizard.umfang.titel": "Ambito (eventi, non giorni)",
    "personwizard.umfang.satz":
        "Inizia in piccolo (50) — ogni immagine estratta la rivedrai a "
        "mano.",
    "personwizard.bilanz.ohne":
        "ultimi {n} eventi persona per {wer} — il bilancio dei "
        "collegamenti viene calcolato alla creazione della sessione",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/nach rahmen die
    # hervorgehobene Zahl, Rand-Leerzeichen gehoeren zum Wert.
    "personwizard.bilanz.zahl_vor": "ultimi {n} eventi persona · ",
    "personwizard.bilanz.zahl_nach":
        " collegabili a {wer} tramite passaggi confermati",
    "personwizard.bilanz.fremd": " · {n} candidati estranei",
    "personwizard.bilanz.erkl_fremd":
        "I candidati sono passaggi in cui non è stato riconosciuto "
        "nessuno — passaggi solo in strada e visitatori non confermati. "
        "Fino alla tua revisione è tutto un SOSPETTO; lì contrassegna "
        "chi NON è un estraneo.",
    "personwizard.bilanz.erkl":
        "Il collegamento è prudente: contano solo i passaggi con "
        "esattamente una persona confermata dal volto. Tutto ciò che "
        "vedrai dopo si può rifiutare con un clic.",
    "personwizard.bilanz.titel": "La tua selezione",
    "personwizard.bilanz.knopf": "Crea questa sessione",
    "personwizard.review.stempel": "SBAGLIATA",
    "personwizard.review.h_fremde": "Estranei",
    "personwizard.review.frage_fremd":
        "fai clic su ogni immagine che NON è un estraneo (una persona di "
        "casa, un visitatore conosciuto) o che è inutilizzabile. Un "
        "secondo clic annulla. Tutto viene salvato all’istante; le "
        "immagini non contrassegnate vengono acquisite come estranei "
        "confermati e affinano la soglia di decisione.",
    "personwizard.review.frage":
        "fai clic su ogni immagine SBAGLIATA (non questa persona, o "
        "inutilizzabile). Un secondo clic annulla. Tutto viene salvato "
        "all’istante; le immagini non contrassegnate contano come "
        "approvate.",
    "personwizard.review.titel": "Rivedi le immagini estratte",
    "personwizard.review.kopf": "Sessione {lauf} — {frage}",
    # Der Zeilenumbruch ist Teil des Originals (Template-Literal) und
    # bleibt fuer die Byte-Treue im Wert.
    "personwizard.review.zurueck": "&larr; torna alla\nprocedura guidata",
    "personwizard.review.knopf_fertig":
        "Concludi la revisione — acquisisci le immagini approvate",
    "personwizard.kontrolle.sammeln_titel":
        "La modalità di conservazione è ATTIVA",
    "personwizard.kontrolle.sammeln_rest":
        " — ogni immagine valutata viene conservata per 30 giorni, così "
        "puoi controllare le decisioni più tardi. Aspettati circa "
        "20&ndash;40 MB al giorno.",
    "personwizard.kontrolle.schlank_titel":
        "Modalità leggera (predefinita)",
    "personwizard.kontrolle.schlank_rest":
        " — le immagini valutate vivono solo mentre un passaggio è in "
        "corso; dopo restano solo l’immagine vincente e il log degli "
        "esiti qui sotto. È l’impostazione predefinita rispettosa della "
        "privacy per un’installazione nuova.",
    "personwizard.kontrolle.titel": "Immagini valutate",
    "personwizard.kontrolle.satz":
        "Che cosa ha guardato davvero il riconoscimento del corpo, un "
        "blocco per passaggio: l’immagine valutata, la classe risultata, "
        "il punteggio e da dove veniva l’immagine. Utile quando una "
        "persona è sfuggita, o è stato riconosciuto qualcuno che non "
        "doveva esserlo.",
    "personwizard.kontrolle.leer_titel": "Ancora nulla di registrato",
    "personwizard.kontrolle.tag_fremd": "estraneo",
    "personwizard.kontrolle.tag_drueber": "sopra soglia",
    "personwizard.kontrolle.tag_drunter": "sotto soglia",
    "personwizard.kontrolle.schwelle": " &middot; soglia {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} valutate, {n} immagine conservata",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} valutate, {n} immagini conservate",
    "personwizard.tabelle.fremd_zeile": "Estranei (classe extra)",
    "personwizard.tabelle.kein_fremd":
        "Ancora nessuna classe estranei — con una il riconoscimento "
        "funziona molto meglio: le immagini di estranei confermate "
        "insegnano al modello cosa NON appartiene e calibrano la soglia "
        "di decisione.",
    "personwizard.tabelle.q_eichung": "misurata",
    "personwizard.tabelle.q_user": "impostata da te",
    "personwizard.tabelle.q_standard": "predefinita",
    "personwizard.tabelle.f_modell": "Modello attivo",
    "personwizard.tabelle.f_schwelle": "Soglia",
    "personwizard.tabelle.f_scharf": "Inserito",
    "personwizard.tabelle.scharf_ja": "SÌ",
    "personwizard.tabelle.scharf_ja_rest": " — valuta in diretta",
    "personwizard.tabelle.scharf_nein": "no — non inserito",
    "personwizard.tabelle.konf_vor":
        "La confusione più alta tra gruppi nella calibrazione: ",
    "personwizard.tabelle.konf_nach":
        " — il punteggio più alto raggiunto da un’immagine per il gruppo "
        "SBAGLIATO; più è vicino a 1, più due gruppi sono vicini.",
    "personwizard.tabelle.titel": "Gruppi appresi",
    "personwizard.karte.scharf": "Inserito",
    "personwizard.karte.unscharf": "Non ancora inserito",
    "personwizard.karte.fehler":
        "L’ultimo tentativo di apprendimento è FALLITO: {fehler} — "
        "questa scheda mostra il modello precedente.",
    "personwizard.karte.titel": "Stato del modello",
    "personwizard.karte.zeile":
        "appreso {wann} in {dauer} s — {bilder} immagini: {je} · "
        "{modell} · ",
    "personwizard.karte.link": "dettagli",
    "personwizard.bestand.titel":
        "Materiale della persona — ciò che è stato appreso",
    "personwizard.bestand.satz":
        "Immagini a figura intera approvate per persona. Scegli un "
        "gruppo qui sotto per vederne le immagini; elimina una singola "
        "immagine (&times; sul riquadro) — una nuova sessione può sempre "
        "estrarla di nuovo. Le eliminazioni hanno effetto al prossimo "
        "apprendimento.",
    "personwizard.bestand.leer_titel": "Ancora nessun materiale approvato",
    "personwizard.bestand.stark_titel": "Cosa rende forte questo modello",
    "personwizard.bestand.chip_fremde": "Estranei ({n})",
    "personwizard.bestand.zeigen_titel": "Mostra le immagini di",
    "personwizard.bestand.zeigen_satz":
        "Scegli un gruppo — le sue immagini si aprono qui sotto, le più "
        "recenti per prime.",
    "personwizard.bestand.marker_tage.eins":
        "solo {n} giorno — il riconoscimento migliora soprattutto con "
        "immagini di giorni, abiti e luci differenti",
    "personwizard.bestand.marker_tage.viele":
        "solo {n} giorni — il riconoscimento migliora soprattutto con "
        "immagini di giorni, abiti e luci differenti",
    "personwizard.bestand.attr_loeschen": "elimina questa immagine",
    "personwizard.bestand.z_bilder": "{n} immagini",
    "personwizard.bestand.z_tage.eins": "{n} giorno",
    "personwizard.bestand.z_tage.viele": "{n} giorni",
    "personwizard.bestand.z_kameras.eins": "{n} telecamera",
    "personwizard.bestand.z_kameras.viele": "{n} telecamere",
    "personwizard.modell.titel": "Modello persona — stato",
    "personwizard.modell.satz":
        "Il modello di riconoscimento del corpo, appreso dalle immagini "
        "che hai approvato. Viene appreso di nuovo automaticamente dopo "
        "ogni revisione conclusa e dopo le eliminazioni.",
    "personwizard.modell.leer_titel": "Ancora nessun modello",
    "personwizard.modell.fremd_keine":
        "ancora nessuno — soglia misurata solo tra le tue persone",
    "personwizard.modell.fremd_gesammelt":
        "{n} accumulati — ne servono {min} prima che entrino "
        "nell’apprendimento e calibrino la soglia",
    "personwizard.modell.fremd_geeicht":
        "{n} nell’apprendimento · soglia calibrata su estranei reali",
    "personwizard.modell.fremd_ungeeicht":
        "{n} nell’apprendimento — la calibrazione della soglia non è "
        "stata eseguita (vedi la nota qui sotto)",
    "personwizard.modell.f_trainiert": "Appreso",
    "personwizard.modell.f_dauer": "Tempo di apprendimento",
    "personwizard.modell.f_modell": "Modello",
    "personwizard.modell.f_bilder": "Immagini totali",
    "personwizard.modell.f_personen": "Persone",
    "personwizard.modell.f_fremd": "Negativi (estranei)",
    "personwizard.modell.scharf_ja": "SÌ — valutazione live attiva",
    "personwizard.modell.scharf_nein": "no — non ancora inserito",
    "personwizard.modell.fehler":
        "L’ultimo tentativo di apprendimento è FALLITO ({zeit}): "
        "{fehler} — il modello mostrato qui è quello precedente e non "
        "include le tue ultime modifiche.",
    "personwizard.modell.aktuell_titel": "Modello attuale",
    "personwizard.modell.material_titel":
        "Materiale di apprendimento per persona",
    "personwizard.modell.kopf_person": "persona",
    "personwizard.modell.kopf_bilder": "immagini approvate",
    "personwizard.modell.kopf_anteil": "quota",
    "personwizard.modell.summe": "totale",
    "personwizard.modell.q_eichung": "misurata sul tuo materiale",
    # {pct} vorformatiert (round) aus der Route (§8.8).
    "personwizard.modell.eich_fremd":
        "Misurata con validazione incrociata a {folds} parti su {n} "
        "immagini delle tue persone tenute da parte, più {n_fremd} "
        "estranei confermati: la confidenza più alta come persona di casa "
        "raggiunta da un estraneo reale è stata {max} &rarr; soglia "
        "{schwelle}; il {pct}% delle immagini genuine la supera. Il "
        "rovescio della medaglia: {ueber} delle tue immagini "
        "raggiungerebbero quella soglia per la persona SBAGLIATA "
        "(massimo {vmax}).",
    "personwizard.modell.eich_intern":
        "Misurata con validazione incrociata a {folds} parti su {n} "
        "immagini tenute da parte: confidenza più alta per una persona "
        "SBAGLIATA {max} &rarr; soglia {schwelle}; il {pct}% delle "
        "immagini genuine la supera. Limite onesto: questa calibrazione "
        "avviene TRA le tue persone apprese — gli estranei reali non "
        "sono ancora nel materiale.",
    "personwizard.modell.regeln_titel": "Impostazioni di giudizio",
    "personwizard.modell.schwelle_vor": "Soglia di decisione: ",
    "personwizard.modell.r_fenster": "Finestra di attivazione",
    "personwizard.modell.r_feuer": "Eventi a supporto per l’avviso",
    "personwizard.modell.r_karenz": "Pausa dopo un avviso",
    "personwizard.modell.regeln_satz":
        "Lascia la soglia vuota per seguire automaticamente il valore "
        "misurato (viene rimisurato a ogni apprendimento). La regola di "
        "attivazione: un avviso solo dopo questo numero di eventi a "
        "supporto dentro la finestra, poi silenzio per la durata della "
        "pausa.",
    "personwizard.modell.knopf_speichern": "Salva impostazioni",
    "personwizard.modell.satz_user":
        "La soglia di decisione è impostata da te ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — la calibrazione su {n} estranei confermati sarebbe {alt}",
    "personwizard.modell.satz_geeicht":
        "La soglia di decisione è calibrata su {n} immagini di estranei "
        "confermate.",
    "personwizard.modell.satz_ungeeicht":
        "La soglia di decisione non è ancora calibrata su materiale di "
        "estranei — considera gli avvisi un’anteprima e tienili "
        "d’occhio.",
    "personwizard.modell.satz_fremd_drop":
        " Un corpo che il modello legge come estraneo viene escluso "
        "prima che possa diventare una corrispondenza.",
    "personwizard.modell.live_titel": "Interruttore live",
    "personwizard.modell.live_an":
        "INSERITO — il percorso del corpo valuta gli eventi live e può "
        "inviare avvisi.",
    "personwizard.modell.live_aus":
        "Non inserito — il percorso del corpo resta in silenzio.",
    "personwizard.modell.live_hinweis":
        "Gli avvisi portano la nota &quot;riconoscimento della persona, "
        "non del volto&quot;.",
    "personwizard.modell.knopf_disarm": "Disinserisci",
    "personwizard.modell.knopf_arm":
        "Inserisci il riconoscimento del corpo",
    # --- webui/bausteine.py ---
    # Nur die gt_leiste-ANZEIGE-Texte; Speicherwerte und KAT_LABELS/
    # KAT_FARBE bleiben literal (§8.12/§8.13, s. en.py).
    "baustein.gt.fremd": "Estraneo",
    "baustein.gt.kein_mensch": "Nessuna persona",
    "baustein.gt.add": "aggiungi persona…",
    "baustein.gt.uebernehmen": "conferma questa proposta (tutte le persone indicate erano presenti)",
    "baustein.gt.fremd_titel": "c’era uno sconosciuto (può stare accanto ai nomi)",
    "baustein.gt.unklar_titel": "non sono sicuro — lascia aperto",
    "baustein.gt.kein_mensch_titel": "nessuna persona in questo evento (falso attivatore)",
    "baustein.gt.opak_titel": "un giudizio vecchio che non corrisponde più a nessuna persona nota — scegli ? o un nome per sostituirlo",
    # ---- Route-JS + Meldungen (Stufe 2, Tranche D) ----
    # Gattungen + Grenzen wie der en.py-Abschnittskommentar. Terminologie
    # begriffe_tabellen.md (IT): volto/passaggio/avviso/estraneo/esito/
    # corrispondenza; adopt -> acquisire, Lernlauf-run -> sessione,
    # trash -> cestino (js.person.loesch_frage), borderline -> al limite,
    # fair -> discreta (fair/okay-Glaettung wie Tranche C), candidate
    # list -> lista dei candidati (Sync-Bestand), pool -> volti estratti
    # (unbekannte.hinweis_reorg). Bar-Metapher der Wortstufen -> soglia
    # (Bestandston "soglia di decisione"). Teilnehmerlose Erfolgs-Toasts
    # partizip-zuerst, invariabel maskulin ("rimosso \"{person}\"" — Muster
    # "Eliminato \"X\"", umgeht die Genus-Falle bei Personennamen).
    # Muttersprachler-QS: Namen/Kennungen stehen in GERADEN DOPPEL-
    # Anfuehrungszeichen wie der IT-Bestand (js.unb.benennen_frage
    # "Assegnare a \"{person}\"?", js.person.loesch_frage) — die
    # EN-Einfachzeichen '…' und erst recht ’…’ lesen sich im Italienischen
    # als Apostroph-Tippfehler (’ ist hier ueberall l’ancora/un’immagine);
    # DE/ES/FR haben die EN-Zeichen ebenso auf ihre Konvention gedreht.
    # Reihen-Woerter als Singular-Adjektive (frontale/laterale/posteriore/
    # incerta); der eine Plural-Rahmen visionwizard.reihe.geliehen ist
    # oben numerus-neutral gestellt. EN-"(s)"-Schluessel behalten ihre
    # Numerus-Marke als Bestands-Schraegform (immagine/i, wie cella/e in
    # visionwizard.reihe.luecken) — §8.18 laesst sie offen, und ein blosser
    # Plural erzeugt bei n=1 echtes Falschitalienisch.
    # --- routes/lernwizard.py (Zuweisungs-Flaeche + Sichtung) ---
    "lernwizard.zw.js_zaehl_mitte": " su ",
    "lernwizard.zw.js_zaehl_nach": " immagini selezionate",
    "lernanker.js.uebernimmt": "acquisizione…",
    "lernanker.js.tag_frage_vor":
        "Impostazioni cambiate dopo la denominazione:\n",
    "lernanker.js.tag_frage_nach":
        "\nAcquisire comunque con la selezione denominata?",
    "lernanker.js.weiter": "salvato — prossimo gruppo…",
    "lernanker.js.speichert": "salvataggio…",
    "lernanker.js.koll_vor": "\"",
    "lernanker.js.koll_mitte": "\" coincide con la persona esistente \"",
    "lernanker.js.koll_nach": "\" — aggiungerlo invece a quella persona?",
    "lernwizard.zw.js_gespeichert_vor": "salvato come ",
    "lernwizard.zw.js_gespeichert_nach": " — controllo delle immagini …",
    "lernwizard.sicht.js_fehl": "controllo fallito — ricarica per riprovare",
    "lernwizard.zw.js_verbergen":
        "Nascondi le altre {n} immagini controllate",
    "lernwizard.zw.js_zeigen": "Mostra tutte le {n} immagini controllate",
    # --- routes/qualitaet.py ---
    "qualitaet.galerie.js_gewaehlt": " selezionate",
    # --- routes/lernanker.py (nur dort) ---
    "lernanker.js.alle_fertig":
        "Tutti i gruppi completati — le immagini denominate ora contano "
        "per il riconoscimento.",
    # --- routes/vision.py (Hand-ID-Script; ID/verifica wie Bestand
    # vision.modell.manuell_knopf "Verifica questo ID") ---
    "vision.modell.js_id_fehlt": "inserisci prima un ID",
    "vision.modell.js_prueft": "verifica in corso …",
    "vision.modell.js_fehler": "errore",
    # --- routes/personwizard.py (Review-Script + Schalter) ---
    "personwizard.review.js_zaehl": " su {n} contrassegnate come sbagliate",
    "personwizard.review.js_frage_vor": "Concludere la revisione? ",
    "personwizard.review.js_frage_mitte":
        " immagini saranno acquisite come materiale di apprendimento, ",
    "personwizard.review.js_frage_nach": " rifiutate.",
    "personwizard.modell.js_fehler": "errore ",
    # --- verifyd.py POST-Antworten (antwort.*, Nutzungs-Reihenfolge) ---
    "antwort.person_entfernt":
        "rimosso \"{person}\" ({n} immagini di riferimento spostate nel "
        "cestino — recuperabili)",
    "antwort.person_name_ungueltig": "nome non valido",
    "antwort.person_unbekannt": "persona sconosciuta",
    "antwort.pruefung_gestartet": "controllo avviato",
    "antwort.reorg_los":
        "Riorganizzazione in corso (ricontrollo dei volti estratti + "
        "ricostruzione dei gruppi, 1-2 min, poi ricarica le pagine)",
    "antwort.reorg_laeuft": "Riorganizzazione già in corso — attendi",
    "antwort.paar_notiert":
        "annotato — questa coppia non verrà più proposta",
    # §8.11-Anhang an eine Fachschicht-msg (die Basis bleibt Grenze).
    "antwort.nachpruefung_anhang":
        " — ricontrollo in background degli eventi di questo passaggio",
    "antwort.sync_wieder": "{n} di nuovo nella lista dei candidati",
    "antwort.sync_auswahl": "{ab} deselezionate, {zu} ripristinate",
    "antwort.sync_laeuft":
        "una sincronizzazione è già in corso — attendi che finisca",
    "antwort.sync_readonly":
        "modalità sola lettura: la scrittura dei riferimenti verso "
        "Frigate è disattivata (vedi l’interruttore nella pagina Sistema)",
    "antwort.sync_nichts":
        "nessuna selezione — spunta almeno un’immagine",
    "antwort.frigate_url": "URL di Frigate: {fehler}",
    "antwort.sync_transfer": "trasferimento in corso ({n} selezionate)",
    "antwort.bruecke_hinzu": "{n} immagine/i aggiunta/e",
    "antwort.modell_laedt":
        "caricamento del modello di riconoscimento — qualche secondo …",
    "antwort.refcache_baut":
        "ricostruzione dell’archivio di riferimento — con un archivio "
        "grande può volerci un minuto …",
    "antwort.refcache_fehler":
        "la ricostruzione dell’archivio di riferimento non è riuscita due volte "
        "di seguito — vedi il log del servizio (/log); il prossimo tentativo "
        "partirà tra qualche minuto",
    "antwort.cache_aufgeraeumt": "{n} clip rimossi, {mb} MB liberati — cache {cache} GB, {frei} GB liberi",
    "antwort.bruecke_nimmt": "il controllo sceglie {n} immagine/i",
    "antwort.bruecke_grenz_zusatz": " · {n} al limite mostrate senza spunta",
    "antwort.bruecke_nur_grenz":
        "niente di chiaramente utile — {n} immagine/i al limite tenuta/e "
        "da parte (identità sicura, qualità dell’immagine solo discreta); "
        "puoi comunque prenderle",
    "antwort.bruecke_nichts":
        "niente da prendere — nessuna nuova immagine utile in questo "
        "passaggio (va bene così)",
    "antwort.bruecke_undo": "{n} immagine/i rimossa/e di nuovo",
    "antwort.personlauf_kein_review":
        "nessuna sessione in attesa di revisione",
    "antwort.personlauf_kein_lauf": "nessuna sessione attiva",
    "antwort.events_bereich":
        "il numero di eventi deve essere compreso tra 1 e {max}",
    "antwort.personlauf_aktiv":
        "una sessione di apprendimento della persona è già attiva",
    "antwort.lernlauf_tag_ungueltig": "giorno non valido (YYYY-MM-DD)",
    # {phase} ist die interne Phasen-Kennung (sprachneutral, §8.19).
    "antwort.lernlauf_phase":
        "una sessione è già nella fase \"{phase}\" — interrompila prima",
    "antwort.lernlauf_beschaeftigt":
        "la sessione precedente sta ancora completando l’evento corrente "
        "— riprova tra un attimo",
    "antwort.lernlauf_schreibfehler":
        "impossibile scrivere lo stato della sessione: {fehler}",
    "antwort.lernlauf_angelegt": "sessione creata",
    "antwort.lernlauf_abgebrochen":
        "interrotta — un evento in corso può ancora concludersi in "
        "background",
    "antwort.live_nichts": "niente da cambiare",
    "antwort.live_an": "sentinelle avviate: {ok}/{alle}",
    "antwort.live_aus": "sentinelle fermate: {ok}/{alle}",
    "antwort.vision_modell_ok":
        "il modello ha risposto — aggiunto all’elenco come verificato a "
        "mano; selezionalo lì e salva",
    "antwort.restore_upload_fehlt": "caricamento mancante o troppo grande",
    "antwort.restore_upload_kaputt": "caricamento troncato",
    "antwort.backend_unbekannt": "backend sconosciuto \"{backend}\"",
    "antwort.kameras_fehlen":
        "telecamere di Frigate non disponibili: {fehler}",
    # Muttersprachler-QS: "Setup" = die Erst-Einrichtung (titel.setup
    # "Configurazione iniziale"), NICHT die Einstellungen — "Impostazioni
    # salvate" haette nach der Settings-Seite geklungen (impostazioni ist
    # das gebundene Wort fuer settings). Linie wie ES/DE/FR.
    "antwort.setup_gespeichert":
        "Configurazione iniziale salvata — riavvio in corso",
    "antwort.kameras_gespeichert":
        "{n} telecamere salvate — riavvio in corso",
    "antwort.name_ungueltig":
        "nome persona non valido (2-40 lettere, cifre, spazio, -)",
    "antwort.anker_unbekannt": "ancora sconosciuta",
    "antwort.anker_benannt":
        "denominato \"{name}\" — {n} immagini selezionate, acquisiscilo "
        "con il pulsante Acquisisci",
    "antwort.anker_nur_unadoptiert":
        "si possono scartare solo i gruppi senza immagini acquisite",
    "antwort.anker_verworfen":
        "eliminato — {n} immagini rimosse",
    "antwort.lauf_id_ungueltig": "ID della sessione non valido",
    "antwort.lauf_aktiv":
        "questa sessione è ancora attiva — interrompila prima",
    "antwort.lauf_nichts":
        "niente trovato per la sessione {lauf} — già eliminata?",
    "antwort.lauf_nur_einer":
        "niente da eliminare — c’è solo una sessione in archivio",
    "antwort.gruppe_unbekannt": "gruppo sconosciuto o chiuso",
    "antwort.sichtung_laeuft": "controllo delle immagini — qualche secondo …",
    "antwort.anker_unbenannt": "l’ancora non è denominata (o è sconosciuta)",
    "antwort.adopt_nichts":
        "nessuna selezione — spunta almeno un’immagine da acquisire",
    "antwort.adopt_phantom":
        "la deduplicazione ha trovato solo riferimenti che non esistono "
        "più su disco — riprova l’acquisizione; se il problema persiste, "
        "segnalalo",
    "antwort.adopt_gedeckt":
        "già coperto — tutto ciò che hai selezionato ({n}) è quasi "
        "identico ai riferimenti esistenti di {person}; gruppo "
        "contrassegnato come acquisito, niente copiato",
    # §8.10-Plural-Split: frueher {'s' if n != 1} im f-String, jetzt t_n.
    "antwort.adopt_fertig.eins": "acquisito {n} riferimento per \"{person}\"",
    "antwort.adopt_fertig.viele":
        "acquisiti {n} riferimenti per \"{person}\"",
    "antwort.adopt_skip": ", {n} saltati perché quasi identici",
    "antwort.adopt_watchdog":
        " — controllo anti-deriva in corso (pagina Sistema)",
    "antwort.areas_gespeichert.eins": "{n} area salvata",
    "antwort.areas_gespeichert.viele": "{n} aree salvate",
    # text/plain-Antwort der /video- und /clip-Routen (Tranche-B-Rest).
    "antwort.clip_weg":
        "Video non più nella cache — conservazione {tage} giorni",
    # --- Konstante->Schluessel (Kennung/Anzeige-Trennung, Paket 3) ---
    # 3a: {hinweis}-Satz — muss in BEIDE Rahmen passen ("questo file …"
    # und "questo archivio …", danach der Konjunktiv-Rahmen "in modo che
    # … funzioni"); "trattalo" statt "tratta questo file", damit der
    # voll.careful-Rahmen (archivio) nicht bricht.
    "system.backup.hinweis":
        "contiene le tue chiavi API — trattalo come una password",
    # 3b: Anzeige-Woerter der Galerie-Reihen; Kennungen (vorn/seitlich/
    # hinten/unklar) bleiben Store-/JSON-Werte. Singular-Adjektive fuer
    # die Rahmen "dalla riga {reihe}" / "vista {reihe}".
    "visiongalerie.reihe.vorn": "frontale",
    "visiongalerie.reihe.seitlich": "laterale",
    "visiongalerie.reihe.hinten": "posteriore",
    "visiongalerie.reihe.unklar": "incerta",
    # 3c: Kategorie-ANZEIGE (bausteine.kat_wort) — Meldetexte (verifyd
    # push, Stufe 4) lesen weiter KAT_LABELS englisch. "falso
    # rilevamento" statt "falso allarme" (allarme laut Tabelle gesperrt).
    "baustein.kat.erkannt": "Riconosciuto",
    "baustein.kat.fremd_verdacht": "Estraneo?",
    "baustein.kat.unbekannt_schwach": "Sconosciuto (debole)",
    "baustein.kat.fehler": "Errore",
    "baustein.kat.no_person":
        "Nessuna persona trovata (probabile falso rilevamento)",
    "baustein.kat.deckung": "Corrispondenza",
    "baustein.kat.widerspruch": "Conflitto",
    "baustein.kat.frigate_nur": "Solo Frigate",
    "baustein.kat.wir_nur": "Solo suslik",
    "baustein.kat.beide_unknown": "Entrambi sconosciuti",
    # 3d: Wortstufen-ANZEIGE (bausteine.stufe_wort), klein im Satzfluss
    # (event.ours_zeile "{person} — {stufe} (presente in {n} finestre)").
    "baustein.stufe.clear": "corrispondenza netta",
    "baustein.stufe.narrow": "appena sopra la soglia",
    "baustein.stufe.below": "sotto la soglia",
    "baustein.stufe.none": "nessuna corrispondenza",
    # ---- Anleitungen /hilfe (Stufe 3) ----
    # Zitat-Kopplungen wortgleich zum IT-Bestand gesetzt: Scegli le
    # telecamere (erkennung.live.knopf_kameras ohne " …"), Notifiche
    # (benachrichtigungen.titel), Sincronizzazione Frigate
    # (nav.sync_auswahl), Gestisci le persone / Registra volto / Registra
    # corpo (erkennung.*-Knoepfe), Rilevamento visione (nav.vision),
    # Stato del modello (nav.person_modell), Apprendimento della persona
    # (nav.personlauf), Immagini del corpo (nav.person), non va bene
    # (visionwizard.zelle.knopf_weg), prompt personalizzato
    # (visiontest.vision.custom_prompt), non testato qui
    # (vision.modell.ungetestet), Configurazione &rarr; Avanzate
    # (nav.bereich.configuration + nav.konfiguration), Sistema
    # (system.titel), Riesegui la procedura guidata iniziale
    # (konfiguration.knopf_setup). NOCH ENGLISCHE UI-Elemente englisch
    # zitiert (Anzeige==Kennung §8.2): Always / Only if no face /
    # If needed (Literale in routes/erkennung.py:152/153/190) sowie
    # Check the key / Check the connection (Literale ueber
    # core/vision.pruef_wort, routes/vision.py:_verbindung) und die
    # Mess-Etiketten residents / strangers in vision.modell.antwort_satz
    # (Muttersprachler-QS IT 20.08.: der Badge-Text kommt woertlich aus
    # core/registry.vision_badge und wird in routes/vision.py:401/430
    # unuebersetzt gerendert — deshalb ENGLISCH zitiert wie in fr.py,
    # die frueheren „persone di casa"/„estranei" liefen am Bildschirm
    # vorbei).
    "hilfe.live.titel": "Le sentinelle live, spiegate",
    "hilfe.live.satz1": """<p>Le sentinelle live guardano le tue telecamere nel momento in cui qualcosa
si muove. Quando una persona mette piede nella proprietà, ricevi un avviso
entro pochi secondi, e se il sistema conosce già il volto, l’avviso porta
con sé un nome.</p>""",
    "hilfe.live.satz2": """<p>Il nome in questa fase è una prima ipotesi. Il controllo approfondito
parte subito dopo, sulla registrazione, e ha l’ultima parola.</p>""",
    "hilfe.live.satz3": """<p>Le sentinelle live non dipendono da Frigate: non vengono attivate dagli
eventi di Frigate e funzionano in modo del tutto autonomo. Guardano
direttamente lo stream video, lo stream proxy di Frigate oppure quello della
telecamera stessa; lo scegli per ogni telecamera.</p>""",
    "hilfe.live.satz4": """<p>Con <b>Scegli le telecamere</b> decidi a quali assegnare una sentinella.
Ogni telecamera sorvegliata costa potenza di calcolo giorno e notte, quindi
comincia dove le persone arrivano davvero: vialetto, porta d’ingresso,
cancello. Potrai aggiungerne altre più avanti.</p>""",
    "hilfe.live.satz5": """<p>Spegnere qui una telecamera non cambia nulla nella registrazione. Frigate
continua a registrare come prima; l’interruttore decide solo se suslik
guarda subito l’immagine o aspetta la registrazione.</p>""",
    "hilfe.gesicht.titel": "Il riconoscimento facciale, spiegato",
    "hilfe.gesicht.satz1": """<p>È il percorso di base con cui suslik riconosce e apprende i volti. Ogni
passaggio registrato viene confrontato con i volti che hai insegnato al
sistema.</p>""",
    "hilfe.gesicht.satz2": """<p>L’insegnamento parte dalle tue telecamere: suslik accumula i volti che
vede, tu guardi le immagini e gli dici chi è chi. Più situazioni e pose
diverse ha visto di una persona, più diventa bravo: luce del giorno, sera,
con il cappello, senza cappello, di lato.</p>""",
    "hilfe.gesicht.satz3": """<p>Se Frigate conosce già dei volti, puoi importarli dalla pagina
Sincronizzazione Frigate. Il consiglio resta comunque di insegnare i volti
qui: l’apprendimento di suslik mette insieme molte pose e situazioni diverse
per ogni persona, e quei riferimenti danno risultati migliori in suslik
rispetto ai volti importati da Frigate. Ciò che insegni qui può tornare a
Frigate dalla pagina di sincronizzazione, se vuoi.</p>""",
    "hilfe.gesicht.satz4": """<p>Tutto resta sulla tua macchina. Nulla viene caricato da nessuna parte, e
dietro non c’è nessun servizio cloud.</p>""",
    "hilfe.gesicht.satz5": """<p>Quando un volto viene riconosciuto, o ne compare uno sconosciuto, suslik
può avvisarti direttamente: Pushover, Telegram o MQTT per le tue automazioni
di casa. Sulla pagina Notifiche scegli che cosa viene inviato e dove. Questi
avvisi sono propri di suslik e funzionano in modo del tutto indipendente da
Frigate; Frigate non ha bisogno di alcuna configurazione di notifica.</p>""",
    "hilfe.gesicht.satz6": """<p><b>Gestisci le persone</b> mostra tutti quelli che il sistema conosce e
ti permette di fare ordine. <b>Registra volto</b> avvia una sessione di
apprendimento per qualcuno di nuovo.</p>""",
    "hilfe.koerper.titel": "Il riconoscimento del corpo, spiegato",
    "hilfe.koerper.satz1": """<p>Alcuni passaggi non mostrano mai un volto utilizzabile: la persona guarda
altrove, porta un cappuccio o è troppo lontana. Il riconoscimento del corpo
copre questi casi. Riconosce le persone di casa dalla corporatura e dalla
postura, usando immagini della persona intera.</p>""",
    "hilfe.koerper.satz2": """<p>È fatto esattamente per questo caso: nessun volto utilizzabile, vuoi
comunque sapere chi era, e non vuoi consegnare le immagini a un modello di
visione AI per scoprirlo.</p>""",
    "hilfe.koerper.satz3": """<p>Apprende dal materiale che approvi. <b>Registra corpo</b> avvia una breve
sessione di apprendimento per una persona: il sistema estrae dalle tue
telecamere le immagini di quella persona, tu rivedi il risultato una volta,
e da lì in poi continua ad apprendere da solo.</p>""",
    "hilfe.koerper.satz4": """<p>Con l’interruttore qui sopra decidi se e quando entra in funzione. <b>Only
if no face</b> significa che resta fermo a meno che il controllo del volto
non sia rimasto a mani vuote. <b>Always</b> significa che controlla ogni
passaggio. Spento significa che non entra mai in funzione.</p>""",
    "hilfe.vision.titel": "La visione AI, spiegata",
    "hilfe.vision.satz1": """<p>La visione AI è un percorso di riconoscimento a sé. Mostra le immagini di
un passaggio a un modello per immagini e gli chiede a quale persona
registrata somigliano. Puoi usarla come riserva per i casi difficili, oppure
lasciare che regga da sola il riconoscimento: impostata su <b>Always</b>,
giudica ogni passaggio da sé, anche se non è stato insegnato nessun volto.
Giudica alla fine del passaggio, non in diretta.</p>""",
    "hilfe.vision.satz2": """<p>Cosa le serve per funzionare: persone registrate con immagini del corpo
approvate (le loro gallerie) e un modello collegato. Il modello può girare
in locale sul tuo hardware oppure nel cloud. Con un modello cloud, ricorda
che le immagini escono da casa tua: ciò che va bene con un modello locale
non è automaticamente lecito con uno nel cloud. E non scegliere i modelli
più piccoli; un modello di taglia media fa benissimo il suo lavoro.</p>""",
    "hilfe.vision.satz3": """<p>Quello che facciamo girare noi: Qwen 3.5 nella taglia 9B, e fa bene il
suo lavoro, in locale come nel cloud. Abbiamo provato anche modelli di
Anthropic (Claude), Google (Gemini) e OpenAI (GPT). Consideralo un dato
delle nostre prove, non una raccomandazione; l’elenco dei modelli sulla
pagina Rilevamento visione contrassegna quelli che abbiamo misurato, proprio
lì dove scegli.</p>""",
    "hilfe.vision.satz4": """<p>E non si ferma a un solo confronto: per escludere gli scambi di persona,
il passaggio viene confrontato anche con le gallerie delle altre persone,
in entrambe le direzioni. Ogni coppia confrontata costa due richieste,
quindi un solo passaggio può pesare. <b>If needed</b> tiene basso quel
conto: il modello viene interpellato solo quando i volti lasciano dubbi.
Senza un modello collegato, la visione resta semplicemente fuori dal gioco,
e la scheda lo dice.</p>""",
    "hilfe.faces_bekannt.titel": "Persone conosciute e registrazione, spiegate",
    "hilfe.faces_bekannt.satz1": """<p>Qui vedi ogni persona che il tuo sistema conosce &mdash; tocca un volto e
vedi tutte le immagini che ci sono dietro.</p>""",
    "hilfe.faces_bekannt.satz2": """<p>Una nuova persona non si insegna caricando una foto: viene appresa dalle
normali registrazioni delle telecamere. Nel corso della giornata il sistema
mette insieme immagini da angolazioni diverse, tu confermi chi è, e solo
dopo quel controllo un’immagine viene conservata.</p>""",
    "hilfe.faces_bekannt.satz3": """<p>Così ogni persona ottiene un piccolo insieme di immagini vere di tutti i
giorni &mdash; esattamente ciò che rende forte il riconoscimento, anche
quando qualcuno guarda altrove o porta un berretto.</p>""",
    "hilfe.faces_lernen.titel": "L’apprendimento, spiegato",
    "hilfe.faces_lernen.satz1": """<p>Mentre le telecamere girano, il sistema continua ad accumulare nuove
immagini delle persone che già conosce. Qui guardi che cosa si è accumulato
&mdash; basta farlo ogni pochi giorni.</p>""",
    "hilfe.faces_lernen.satz2": """<p>Confermi, correggi o scarti con un clic; nulla viene conservato senza di
te.</p>""",
    "hilfe.faces_lernen.satz3": """<p>Più immagini buone ha una persona, più viene riconosciuta in modo
affidabile &mdash; per questo l’apprendimento non si ferma mai del tutto,
diventa solo più raro.</p>""",
    "hilfe.faces_unbekannt.titel": "I visitatori sconosciuti, spiegati",
    "hilfe.faces_unbekannt.satz1": """<p>Alcune persone continuano a comparire senza che il sistema abbia un nome
per loro &mdash; il postino, un vicino, il giardiniere. Qui il sistema
riunisce questi sconosciuti ricorrenti e ti chiede: chi è?</p>""",
    "hilfe.faces_unbekannt.satz2": """<p>Dai loro un nome e da quel momento vengono riconosciuti come tutti gli
altri. Oppure lasciali sconosciuti di proposito &mdash; anche questa è una
decisione, e il sistema non continuerà a chiedere.</p>""",
    "hilfe.faces_qualitaet.titel": "Il controllo qualità, spiegato",
    "hilfe.faces_qualitaet.satz1": """<p>Col tempo si accumulano molte immagini, e non tutte aiutano il
riconoscimento &mdash; alcune sono sfocate, altre mostrano appena la
persona, e nel caso peggiore le immagini di due persone diverse si
somigliano così tanto che gli scambi sono dietro l’angolo.</p>""",
    "hilfe.faces_qualitaet.satz2": """<p>Questo controllo trova questi punti deboli prima che ti costino un
riconoscimento. Ricevi indicazioni concrete su quali immagini guardare
&mdash; nulla viene eliminato se non lo decidi tu.</p>""",
    "hilfe.faces_lernlauf.titel": "La sessione di apprendimento, spiegata",
    "hilfe.faces_lernlauf.satz1": """<p>Avvii una sessione; il sistema rilegge le tue registrazioni recenti ed
estrae i volti da solo.</p>""",
    "hilfe.faces_lernlauf.satz2":
        "<p>Li ordina in gruppi. Un gruppo deve essere una sola persona.</p>",
    "hilfe.faces_lernlauf.satz3": """<p>Dai un nome a ogni gruppo, oppure saltalo. È l’unico passo in cui servi
tu.</p>""",
    "hilfe.faces_lernlauf.satz4": """<p>Le immagini nominate diventano riferimenti e contano subito per il
riconoscimento. Ripeti ogni pochi giorni, oppure lascia che nel frattempo la
vista del giorno integri le persone conosciute.</p>""",
    "hilfe.zurueck.erkennung": "Torna a Riconoscimento",
    "hilfe.zurueck.faces": "Torna a Volti",
    "hilfe.zurueck.lernlauf": "Torna alla sessione di apprendimento",
    # ---- §8.1-Nachzuegler (Stufe 3): Inline-Markup-Prosa der Tranchen ----
    "setupwiz.backend.system_satz":
        "Se l’acceleratore entra davvero in funzione lo vedi confermato "
        "sulla pagina <b>Sistema</b> dopo l’avvio (suslik non ripiega mai "
        "in silenzio sulla CPU senza dirlo).",
    "setupwiz.fertig.wieder_satz":
        "Puoi rieseguire questa procedura guidata in qualsiasi momento da "
        "<b>Sistema → Riesegui la procedura guidata iniziale</b>.",
    "system.sync.diagnose_satz":
        'Se una sincronizzazione segnala un problema, <a '
        'href="/sync_diagnose" target="_blank">apri la diagnosi</a> — '
        "riunisce il rapporto di suslik e il log di Frigate, pronti da "
        "copiare in una segnalazione.",
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">apri la diagnosi</a> '
        "— riunisce il rapporto di suslik e il log di Frigate.",
    "vision.kopf.einleitung":
        "Un terzo percorso di riconoscimento accanto a volto e corpo: un "
        "modello linguistico visivo guarda un’immagine di un passaggio e "
        "dice quale delle tue persone conosciute mostra &mdash; "
        "confrontandola con una piccola galleria di quella persona. È una "
        "<b>voce in più</b>, mai il buttafuori: la scelta obbligata "
        "risponde &bdquo;A o B&ldquo;, quindi può confermare una persona "
        "di casa ma non può respingere un estraneo. Quello resta il "
        "compito del riconoscimento esistente.",
    "vision.hinweis.modell_satz":
        "Un modello di visione capace di guardare più immagini insieme. "
        "Puoi usare uno dei fornitori online qui sotto, oppure farne "
        "girare uno tu stesso &mdash; la combinazione misurata qui è "
        "<b>llama.cpp</b> con un modello di visione <b>Qwen3.5</b> (il 4B "
        "è bravo quanto il 9B in questo compito e richiede circa metà "
        "della memoria). <b>Non</b> deve per forza girare su questa "
        "macchina.",
    "vision.hinweis.host_satz":
        "<b>Questo host di solito è troppo piccolo per un modello "
        "locale.</b> Il 9B richiede circa 12 GB di working set, il 4B "
        "circa 6,6 GB, e qui vivono già suslik e il worker di analisi "
        "&mdash; il worker è la prima cosa che il kernel uccide quando la "
        "memoria finisce. Una seconda macchina, o un fornitore online, è "
        "la configurazione sensata.",
    "vision.hinweis.mess_satz":
        "Un avvertimento sulla misura di quella memoria: <code>docker "
        "stats</code> mostra circa 2,7 GiB per il container del modello "
        "perché i pesi sono mappati, non copiati. Il working set reale è "
        "~11,6 GiB. Se dimensioni <code>--memory</code> in base a ciò che "
        "dice <code>docker stats</code>, il modello ricarica i suoi pesi "
        "in continuazione e tutto rallenta a passo d’uomo.",
    "vision.hinweis.kosten_satz":
        "Velocità e costi, misurati, così dopo niente ti sorprende: "
        "l’intero passaggio entra come <b>una sola griglia di "
        "candidati</b>, e ogni <b>coppia di gallerie confrontata costa "
        "due richieste</b> (la stessa domanda viene posta di nuovo con le "
        "due gallerie scambiate, per intercettare una preferenza di "
        "posizione). Di solito una coppia decide. Su una macchina di "
        "classe CPU sono circa 7 minuti per coppia; sugli endpoint online "
        "misurati qui, secondi.",
    "vision.verb.key_ort":
        "<b>Metti la chiave nel campo della chiave, non nell’URL</b>: un "
        "endpoint che porta le credenziali nel suo indirizzo &mdash; "
        "davanti al nome host, o come parametro di query &mdash; contiene "
        "lo stesso segreto, e compare in molti più posti (stato, log, "
        "backup).",
    "vision.modell.leer_key":
        "Ancora nulla da scegliere. Inserisci la tua chiave qui sopra e "
        "premi <b>Check the key</b>: suslik si collega all’endpoint, "
        "chiede che cosa c’è e ti mostra ciò che ha trovato. Scegli da "
        "quell’elenco.",
    "vision.modell.leer_verbindung":
        "Ancora nulla da scegliere. Compila i campi qui sopra e premi "
        "<b>Check the connection</b>: suslik si collega all’endpoint, "
        "chiede che cosa c’è e ti mostra ciò che ha trovato. Scegli da "
        "quell’elenco.",
    "vision.modell.antwort_satz":
        "Questo è ciò che l’endpoint ha risposto quando suslik gliel’ha "
        "chiesto, {zeit} &mdash; nulla qui è un suggerimento nostro. Dove "
        "abbiamo misurato un modello, la nota sta su quel modello. Due "
        "capacità sono mostrate separatamente, perché non vanno di pari "
        "passo: <b>residents</b> è scegliere quella giusta tra due persone "
        "conosciute, <b>strangers</b> è rispondere &bdquo;nessuno dei "
        "due&ldquo; per qualcuno che non gli hai mai insegnato. Una "
        "spunta significa che ogni giudizio di quel tipo nella nostra "
        "misurazione era corretto; la frazione accanto dice tutto. "
        "I modelli senza una misurazione qui dicono <b>non "
        "testato qui</b> &mdash; non è un esito, solo onestà (misurazioni "
        "del {stand}).",
    "vision.prompt.eigen_satz":
        "Questa è la tua formulazione &mdash; gli esiti prodotti con essa "
        "sono contrassegnati <b>prompt personalizzato</b>. Ripristinala "
        "per tornare alla formulazione predefinita misurata.",
    "vision.cloud.sendet_satz":
        "Questo invia immagini di persone dalle tue telecamere a "
        '<b class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Tre passi, perché un semplice ping di raggiungibilità non basta: "
        "un backend era raggiungibile, aveva il modello e rispondeva in "
        "fretta &mdash; e ha comunque sbagliato 5 domande di confronto su "
        "12, perché rimpiccioliva le immagini prima di guardarle."
        "<br><b>1</b> raggiungibilità, modello e tempo di risposta, con "
        "un’immagine di prova generata al momento.<br><b>2</b> "
        "un’esecuzione a scelta obbligata su griglie di forme generate "
        "dove la risposta giusta è nota &mdash; controlla il formato "
        "della risposta, il parser e l’interruttore del ragionamento."
        "<br><b>3</b> un conteggio dei token rispetto a un riferimento "
        "misurato, che è il modo in cui il rimpicciolimento delle "
        "immagini si fa vedere.<br><b>Per questo non viene usata nessuna "
        "immagine di persone</b>, e non esiste alcuna opzione per farlo.",
    "visiontest.kopf.wege_satz":
        "Scegli un passaggio reale e guarda che cosa ne fanno i tre "
        "percorsi di riconoscimento, fianco a fianco: <b>volto</b>, "
        "<b>persona</b> e <b>visione</b>.",
    "visiontest.vision.einrichten_satz":
        'Configurala in <a href="/vision">Rilevamento visione</a>: un '
        "modello, un test di connessione verde e almeno due gallerie "
        "approvate. Le altre due colonne funzionano senza.",
    "visionwizard.groesse.satz":
        "Misurato, onestamente: la dimensione <b>non</b> è stata la leva "
        "in nessuno dei casi che abbiamo eseguito &mdash; una griglia più "
        "grande non ha reso le risposte migliori, e nemmeno peggiori. "
        "Prendi la più grande se il tuo materiale la regge (qui: "
        "{empfehlung}), la più piccola se no. Costano più o meno uguale, "
        "perché a costare token è la superficie dell’immagine, non il "
        "numero di celle.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Dimenticale</a> '
        "se vuoi ripartire da zero.",
    "visionwizard.vorschlag.satz":
        "Una riga per vista: frontale, laterale, posteriore. Le immagini "
        "sono scelte per dimensione e nitidezza, per quanto chiaramente "
        "si vedano occhi e naso, per quanta luce è bruciata, per quanta "
        "parte del ritaglio è davvero la persona &mdash; e distribuite su "
        "giorni, eventi e telecamere diversi. La riga sotto ogni immagine "
        "dice che cosa vi è stato misurato. Fai clic su <b>non va "
        "bene</b> su tutto ciò che non è utilizzabile &mdash; la migliore "
        "immagine successiva della STESSA vista sale al suo posto. Questo "
        "non tocca il tuo materiale di apprendimento; dice solo &bdquo;"
        "non come cella della galleria&ldquo;.",
    "personwizard.kopf.stark_satz":
        "<b>Cosa rende forte il modello:</b> la varietà batte la "
        "quantità. Immagini di <b>molti giorni diversi</b> (abiti, luce, "
        "telecamere) aiutano molto più di tante immagini di un solo "
        "passaggio — riesegui l’estrazione su giorni nuovi invece di "
        "scavare più a fondo in un solo giorno. Le immagini di estranei "
        "confermate affinano allo stesso modo la soglia di decisione.",
    "personwizard.fertig.training_satz":
        "L’apprendimento del modello sul materiale approvato parte "
        "automaticamente dopo la revisione — vedi <a "
        'href="/person/modell">Stato del modello</a>. Qui sotto puoi '
        "avviare un’altra sessione in qualsiasi momento.",
    "personwizard.kontrolle.schalter_satz":
        'Lo attivi e lo disattivi in <a href="/konfiguration">'
        "Configurazione &rarr; Avanzate</a>, chiave "
        "<code>diagnostic_collection</code>. Immagini e log scadono "
        "insieme al log dei riconoscimenti dopo 30 giorni &mdash; nulla "
        "qui viene conservato più a lungo dei riconoscimenti stessi.",
    "personwizard.kontrolle.leer_satz":
        "Le voci compaiono quando il riconoscimento del corpo è inserito "
        'in <a href="/person/modell">Stato del modello</a> e una persona '
        "passa.",
    "personwizard.bestand.leer_satz":
        'Esegui <a href="/personlauf">Apprendimento della persona</a> e '
        "completa la revisione — le immagini approvate compaiono qui.",
    "personwizard.bestand.stark_satz":
        "La varietà batte la quantità: immagini di <b>molti giorni "
        "diversi</b> (abiti, luce) aiutano molto più di tante immagini di "
        "un solo passaggio. Punta a più giorni per persona e lascia che "
        "l’estrazione copra tutte le tue telecamere.",
    "personwizard.bestand.fremd_satz":
        "<b>Estranei:</b> {n} immagini di estranei confermate calibrano "
        "la soglia di decisione — più estranei ha visto il modello, più "
        "quella linea è affidabile. (Conservate in "
        "<code>personlern/fremd/</code>; una pagina per far crescere "
        "questo insieme dal viavai della tua strada è in programma.)",
    "personwizard.bestand.fremd_erklaerung":
        "Immagini di estranei confermate — alimentano la classe "
        "aggiuntiva e calibrano la soglia di decisione. Eliminarne una fa "
        "ripartire subito l’apprendimento del modello (i file stanno in "
        "<code>personlern/fremd/</code>).",
    "personwizard.modell.leer_satz":
        'Esegui <a href="/personlauf">Apprendimento della persona</a> e '
        "completa una revisione — l’apprendimento del modello parte poi "
        "automaticamente.",
    "personwizard.modell.material_satz":
        "Gestisci le immagini in "
        '<a href="/person">Immagini del corpo</a> — le eliminazioni '
        "fanno ripartire automaticamente l’apprendimento del modello.",
    # ---- Meldetexte (Stufe 4) --------------------------------------------
    # Push-/Telegram-Texte; Reihenfolge, Platzhalter und Abschnitts-Grenzen
    # exakt wie im en.py-Abschnitt (deutsche Alt-Meldetexte, Stoerungs-
    # Diagnosen, Schnell-Urteil und MQTT-Felder bleiben dort BEWUSST
    # draussen). Produktnamen (suslik/Frigate/Pushover/Telegram) und die
    # Waechter-Kennung {wache} bleiben wortgleich (§8.6 / Invariante §6).
    #
    # IT-Entscheide dieses Abschnitts:
    # - Genus-Falle bei Personennamen (kein Geschlecht bekannt). Die Regel
    #   "Partizip zuerst, invariabel maskulin" ist nach der
    #   Muttersprachler-QS GESCHAERFT: sie traegt nur, wo das Partizip ein
    #   ETIKETT vor dem Doppelpunkt ist ("riconosciuto dal corpo: {name}",
    #   "riconosciuto (in diretta, preliminare): {name}") — dort liest es
    #   sich als Schlagzeilen-Rubrik, dasselbe Muster wie die
    #   Erfolgs-Toasts oben ("rimosso \"{person}\"", s. Abschnitts-
    #   kommentar Tranche C/D). Steht das Partizip dagegen DIREKT am Namen
    #   im laufenden Satz, erwartet das Italienische Kongruenz
    #   ("confermato Anna" ist schlicht falsch) — der eine Fall
    #   (meldung.alert.bestaetigt) bindet das Genus deshalb an ein
    #   Substantiv: "persona confermata: {name}", wortgleich zu
    #   antwort.bruecke_grund_keine_events ("come persona confermata").
    #   Zweite Substantiv-Bindung: "la corrispondenza più vicina è {name}".
    # - Keine zwei Lineette in EINER Push-Zeile (Muttersprachler-QS): wo
    #   der RAHMEN schon eine setzt ("{kamera} — {urteil}", "niente da
    #   prendere — {grund}"), traegt der eingesetzte Teil einen
    #   Doppelpunkt statt einer zweiten Lineetta. Gleiche Entscheidung wie
    #   in es.py; die EN-Bauform bleibt inhaltlich unangetastet, nur die
    #   Interpunktion folgt dem italienischen Lesefluss.
    # - Die Wortstufe {wort} kommt uebersetzt aus baustein.stufe.*
    #   (core/vertrauen.label_sprachig) — hier steht sie nie als Literal.
    # - Bestands-Kopplungen (Muttersprachler-QS): "presente in {n}
    #   finestra/e" nach event.ours_zeile · "riconoscimento della persona,
    #   non del volto" WORTGLEICH zu personwizard.modell.live_hinweis ·
    #   disturbance -> anomalia (system.live.stoerungen) · verdict ->
    #   esito · cosine -> coseno · score -> punteggio · test -> prova
    #   (Knopf "Prova Pushover") · "volto utilizzabile" wie die
    #   Kategorien-Erklaerungen · niente da prendere wie bruecke_nichts.
    # - Numerus: EN-"(s)"-Formen bleiben Bestands-Schraegform (volto/i,
    #   immagine/i, confronto/i, evento/i), echte t_n-Paare bekommen echte
    #   Formen (volto/volti). EN-Klarplurale bekommen die Schraegform NUR
    #   dort, wo n=1 im Code wirklich erreichbar ist (win3s/win_min,
    #   feuer_ab) — "rilevamenti coerenti" bleibt Plural, weil
    #   core.livewache.NAME_STIMMEN fest 2 ist.
    "meldung.titel.kategorie": "suslik: {wort}",
    # "finestra/e": {n} ist win3s und kann 1 sein (win_min ab 1 einstellbar,
    # verifyd Feld-Grenzen) — Anlehnung an event.ours_zeile, die dort mit
    # t_n echte Formen hat.
    "meldung.alert.bestaetigt":
        "persona confermata: {name} ({wort}, presente in {n} finestra/e)",
    # Doppelpunkt statt Lineetta: der Rahmen meldung.alert.satz setzt schon
    # eine ("{kamera} — {urteil}") — s. Abschnittskommentar.
    "meldung.alert.keiner_naechster":
        "nessuna conferma: la corrispondenza più vicina è {name} ({wort})",
    "meldung.alert.keiner_ohne_gesicht":
        "nessuna conferma: nessun volto utilizzabile",
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate ha visto: {label}. {gesichter}",
    "meldung.alert.gesichter.eins": "{n} volto in questo evento.",
    "meldung.alert.gesichter.viele": "{n} volti in questo evento.",
    # Reine Zahlenzeile: "cos" ist auch im Italienischen die Kurzform von
    # coseno — nichts zu uebersetzen.
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    # Push-Titel kurz und im Bau der Kategorie-Zeile oben ("suslik: …").
    # "riconoscimento persona" war eine Substantiv-Reihung nach englischem
    # Muster (Muttersprachler-QS): das Italienische baut sie nur mit Plural
    # ("riconoscimento volti/targhe"), im Singular klingt sie wie ein
    # halbuebersetztes Label. "dal corpo" sagt zugleich, WELCHER Weg
    # gefeuert hat — derselbe Wortlaut wie im Meldesatz darunter.
    "meldung.person.titel": "suslik: riconoscimento dal corpo",
    # Die Klammer-Notiz WORTGLEICH zu personwizard.modell.live_hinweis
    # ("Gli avvisi portano la nota …") — die UI verspricht genau sie.
    # "evento/i": feuer_ab ist ein freies Feld und kann 1 sein.
    "meldung.person.satz":
        "riconosciuto dal corpo: {name} (riconoscimento della persona, "
        "non del volto) — {wort}, {n} evento/i a supporto",
    "meldung.person.wort_ersatz": "corrispondenza",
    "meldung.person.zahl": "[punteggio {score}]",
    "meldung.vision.titel": "suslik: visione",
    "meldung.vision.unbestaetigt":
        "la visione non ha potuto confermare nessuno in questo passaggio",
    # "the body ranking" NICHT als "classifica": das Wort gehoert im
    # Italienischen der Tabelle/Hitparade (Muttersprachler-QS), "la
    # classifica del corpo" liest sich wie eine Rangliste VON Koerpern.
    # Gemeint ist, worauf der Koerper-Weg gezeigt hat — genau das sagt
    # "il riconoscimento dal corpo indicava …" (Wortlaut wie
    # meldung.person.titel/.satz).
    "meldung.vision.koerper_zusatz":
        "— il riconoscimento dal corpo indicava {namen}",
    "meldung.vision.bilder_zusatz": "({n} immagine/i nella griglia)",
    "meldung.vision.einig":
        "visione: {name} — esito unanime, {voten} confronto/i su {bilder}",
    "meldung.vision.kein_urteil": "visione: nessun esito — {grund}",
    "meldung.wache.titel_person": "{wache} {kamera}: persona rilevata",
    "meldung.wache.titel_stoerung": "{wache} {kamera}: anomalia",
    "meldung.wache.caption": "{wache} {kamera}: {text}",
    "meldung.wache.name_satz":
        "riconosciuto (in diretta, preliminare): {name} ({wort}, {n} "
        "rilevamenti coerenti)",
    "meldung.wache.name_zahl": "[coseno {cos}]",
    "meldung.wache.funde.eins": "{n} volto in {sek} s",
    "meldung.wache.funde.viele": "{n} volti in {sek} s",
    "meldung.wache.funde_zahl": "(punteggio {score}, {ms} ms)",
    "meldung.video_ersatz.satz":
        "(video non disponibile — invio dell’immagine)",
    "meldung.test.satz": "Notifica di prova da suslik ✓",
    # ---- D1: ehrliche Begruendung der Pass-Pruefung ----------------------
    # Satzteile mit kleinem Anfangswort: sie haengen hinter "niente da
    # prendere — " (bruecke_nichts_grund) oder hinter dem Grenzfall-Satz
    # (bruecke_grund_zusatz). Zahlen und Schwellen kommen fertig aus der
    # Diagnose — hier steht KEINE Schwelle als Literal, nur ihr Platzhalter.
    # zu_klein und kein_crop numerus-fest gebaut ("…, nessuno raggiunge/ha",
    # Verb im Singular), damit die Aussage auch bei n=1 heil bleibt; die
    # uebrigen Zweige spiegeln die EN-Bauform samt ihrer n=1-Unschaerfe
    # ("1 of the checked face(s) ARE …") — Glaettung waere eine bewusste
    # EN-Textaenderung, nie eine stille Abweichung der Uebersetzung.
    # Interpunktion: die Zahlen-Nachsaetze haengen an einem DOPPELPUNKT,
    # nicht an einer zweiten Lineetta — der Rahmen "niente da prendere — "
    # bringt seine schon mit (Muttersprachler-QS, s. Abschnittskommentar).
    "antwort.bruecke_nichts_grund": "niente da prendere — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    "antwort.bruecke_grund_zu_klein":
        "{n} volto/i misurato/i in questo passaggio, nessuno raggiunge la "
        "dimensione minima: il più grande {kante} px, ne servono "
        "{min_kante} px",
    # "ne serve almeno": das blosse "ne serve {unscharf_max}" liess die
    # Schwelle in der Luft haengen (Muttersprachler-QS) — "almeno" macht
    # aus der Zahl eine Untergrenze, wie es "ne servono … px" oben schon
    # tut.
    "antwort.bruecke_grund_zu_unscharf":
        "{n} volto/i in questo passaggio troppo sfocato/i per un "
        "riferimento: nitidezza migliore {sharp}, ne serve almeno "
        "{unscharf_max}",
    "antwort.bruecke_grund_kein_gesicht":
        "nessun volto misurabile su {n} immagine/i controllata/e in questo "
        "passaggio",
    "antwort.bruecke_grund_gedeckt":
        "{n} dei volti controllati sono quasi identici ai riferimenti che "
        "{person} ha già",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} dei volti controllati somigliano più a qualcun altro che a "
        "{person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} dei volti controllati non erano chiaramente {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} dei volti controllati erano deboli su entrambi i fronti: "
        "qualità dell’immagine e identità",
    "antwort.bruecke_grund_kein_crop":
        "{n} evento/i in questo passaggio, nessuno ha un ritaglio di volto "
        "da controllare",
    "antwort.bruecke_grund_keine_events":
        "nessun evento di questo passaggio indica {person} come persona "
        "confermata o come miglior corrispondenza",
    "antwort.bruecke_grund_keine_referenzen":
        "{person} non ha ancora immagini di riferimento per il confronto",
    # ---- personlauf-Design (Nachzug) ----
    # Kachel-Titel und Kachel-Saetze des /personlauf-Laufflusses. Kachel 1/4,
    # die erste Saeulen-Marke und die Nachbar-Beschriftungen kommen wortgleich
    # aus dem Gesichts-Lernlauf (lernwizard.*) — hier stehen nur die sieben
    # personwizard-eigenen Neuzugaenge. Kachel 2 traegt zugleich die zweite
    # Saeulen-Marke neben "Preparazione" und steht darum wie die IT-Phasen
    # im Substantiv.
    "personwizard.kachel.sammeln": "Estrazione immagini",
    "personwizard.kachel.pruefen": "Revisione delle immagini",
    "personwizard.k1.satz":
        "Scegli chi apprendere e quanto indietro andare &mdash; poi la "
        "sessione estrae le immagini dalle tue registrazioni.",
    "personwizard.k2.satz":
        "Estrae immagini a figura intera dalle tue registrazioni, e solo "
        "dai passaggi che un volto ha già confermato.",
    "personwizard.k3.satz":
        "Il passo in cui servi tu: ogni immagine estratta riceve il tuo "
        "sì o il tuo no, e nulla viene appreso prima.",
    "personwizard.k4.satz":
        "Con le immagini approvate il modello del corpo viene appreso "
        "subito &mdash; così riconosce le persone anche senza un volto "
        "visibile.",
    "personwizard.such.titel": "Imposta l’apprendimento della persona",
}
