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
        "scartato — immagini rimosse; il gruppo resta memorizzato, così "
        "le nuove estrazioni degli stessi eventi restano silenziose",
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
        "{n} gruppi scartati memorizzati — le nuove estrazioni degli "
        "stessi eventi restano silenziose",
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
        "Scartare questo gruppo? Le sue immagini vengono rimosse; il "
        "gruppo resta memorizzato, così le nuove estrazioni degli stessi "
        "eventi restano silenziose.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Scartare questo gruppo? Le sue immagini vengono rimosse e la "
        "denominazione in sospeso viene annullata; il gruppo resta "
        "memorizzato, così le nuove estrazioni degli stessi eventi "
        "restano silenziose.",
    "lernanker.liste.knopf_verwerfen": "Scarta",
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
        "Rimisura ogni immagine di riferimento e cerca quelle deboli, i "
        "quasi-duplicati e i volti scambiati. Richiede circa un minuto "
        "e gira in background.",
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
    "qualitaet.lauf.reload_auto": "la pagina si aggiorna da sola.",
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
        "{n} gruppo scartato (nessun volto utilizzabile o per tua "
        "scelta) &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} gruppi scartati (nessun volto utilizzabile o per tua "
        "scelta) &middot;",
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
        "Eliminare questo gruppo? Le sue immagini vengono rimosse e una "
        "denominazione in sospeso viene annullata; il gruppo resta "
        "memorizzato, così le nuove estrazioni degli stessi eventi "
        "restano silenziose.",
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
    "js.unb.besucher_frage": "Ignorare come estraneo conosciuto? Non attiverà più avvisi. (Riattivabile in qualsiasi momento qui sotto, in \"known visitors\".)",
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
    # js.vision.dirty_text: "Save" ist der (noch englische) Knopf der
    # Vision-Seite — bleibt woertlich, bis die Seite selbst einzieht.
    "js.vision.dirty_text": "Il test userebbe i valori appena digitati. Il riconoscimento continua a usare la connessione SALVATA finché non premi Save — un test verde da solo non cambia nulla nei verdetti.",
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
    "js.vision.prompt_zurueck": "formulazione predefinita ripristinata — premi Save per salvarla",
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
}
