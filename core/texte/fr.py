# Muttersprachler-QS durchlaufen 19.08.2026 (Opus-Pruefagent je Sprache, Bericht im
# Session-Transkript); aktiv erst mit Registrierung in core/sprache.py (Stufe 1).
"""Franzoesische Texte (Uebersetzung von en.py, Schluessel identisch in
identischer Reihenfolge; verbindliche Vorlage: begriffe_tabellen.md, FR)."""
T = {
    # ------------------------------------------------ routes/gesichter ---
    "gesichter.titel": "Personnes connues",
    "gesichter.kopf.knopf_lernen": "Apprendre des personnes",
    "gesichter.kopf.hinweis_lernen":
        "session d'apprentissage guidée sur vos propres enregistrements "
        "(étape de base)",
    "gesichter.kopf.satz":
        "Toutes les personnes apprises et leurs images de référence. Vous "
        "pouvez retirer des images individuelles, en attribuer d'autres "
        "depuis les visages inconnus via le bouton de chaque personne, ou "
        "téléverser une photo ci-dessous, y compris pour une personne "
        "entièrement nouvelle.",
    "gesichter.galerie.bildzahl": "{n} images",
    "gesichter.galerie.knopf_entfernen": "retirer",
    "gesichter.galerie.knopf_aehnliche": "trouver les visages correspondants",
    "gesichter.galerie.knopf_qs": "Vérifier la qualité",
    "gesichter.galerie.knopf_loeschen": "Supprimer la personne\u2026",
    "gesichter.galerie.hinweis_leer": "aucune image pour l'instant",
    "gesichter.upload.titel": "Téléverser une photo",
    "gesichter.upload.attr_person": "personne existante\u2026",
    "gesichter.upload.attr_neu": "ou nouvelle personne",
    "gesichter.upload.knopf": "Téléverser",
    "gesichter.upload.hinweis":
        "Nouvelle personne&nbsp;: saisissez le nom dans le champ libre. "
        "Garde-fou&nbsp;: buffalo_l doit trouver un visage (sinon une "
        "invite de forçage apparaît).",
    "gesichter.import.titel": "Import / resynchronisation depuis Frigate",
    "gesichter.import.knopf": "Synchroniser les visages depuis Frigate",
    "gesichter.import.hinweis":
        "Récupère les images de référence que Frigate possède et qui "
        "manquent encore à cette bibliothèque — incrémental, "
        "utilisable à tout moment sans risque (rien n'est supprimé en "
        "local). Même import que dans l'assistant d'installation, "
        "désormais accessible sans le relancer (p. ex. après la "
        "restauration d'une configuration).",
    # ------------------------------------------------- routes/kameras ---
    "kameras.titel": "Caméras",
    "kameras.banner.config_fehler":
        "Impossible de lire la config Frigate&nbsp;: {fehler}",
    "kameras.karte.verwenden": "utiliser cette caméra",
    "kameras.karte.zonen_hinweis": "aucune cochée = tous les événements",
    "kameras.karte.zonen_keine":
        "aucune zone définie dans Frigate — tous les événements",
    "kameras.karte.rec_an": "rec \u2713",
    "kameras.karte.rec_aus": "pas de rec",
    "kameras.karte.pill_aus": "désactivée dans Frigate",
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate n'exécute aucune détection de personne sur ce flux "
        "&mdash; aucun événement ne peut arriver ici",
    "kameras.karte.pill_keine_detektion": "pas de détection dans Frigate",
    "kameras.leer.titel": "Aucune caméra trouvée dans Frigate.",
    "kameras.leer.hinweis":
        "Vérifiez que suslik peut joindre l'API Frigate.",
    "kameras.fuss.knopf_speichern": "Enregistrer les caméras",
    # -------------------------------------------------- routes/lernen ---
    "lernen.titel": "Suggestions — personnes à apprendre",
    "lernen.kopf.titel_offen": "Suggestions ({n})",
    "lernen.leer.titel": "Aucune suggestion en attente.",
    "lernen.leer.hinweis":
        "Les bons nouveaux visages (grands, nets, de face, reconnus avec "
        "un bon niveau de confiance ou relevant clairement d'une présence "
        "inhabituelle) apparaissent ici automatiquement après l'analyse.",
    "lernen.karte.unbekannt": "Inconnu/Intrus",
    "lernen.karte.metrik_voll":
        "score {score} · nouveauté {novelty} · {bw}×{bh}px · frontal "
        "{front} · netteté {sharp}",
    "lernen.karte.metrik_kurz": "score {score}",
    "lernen.karte.link_video": "Vidéo",
    "lernen.karte.knopf_add_person": "Ajouter comme {person}",
    "lernen.karte.attr_person": "comme personne…",
    "lernen.karte.attr_neu": "ou nouvelle personne",
    "lernen.karte.knopf_add": "Ajouter",
    "lernen.karte.knopf_ablehnen": "Écarter",
    "lernen.galerie.titel": "Références (Master)",
    "lernen.galerie.bildzahl": "{n} références",
    "lernen.upload.titel_abschnitt": "Téléversement",
    "lernen.upload.titel":
        "Téléverser votre propre photo dans le Master",
    "lernen.upload.attr_person": "personne existante…",
    "lernen.upload.attr_neu": "ou nouvelle personne",
    "lernen.upload.knopf": "Téléverser",
    "lernen.upload.hinweis":
        "Nouvelle personne (p. ex. Alex)&nbsp;: saisissez le nom dans le "
        "champ libre. Garde-fou&nbsp;: buffalo_l doit trouver un visage "
        "(sinon une invite de forçage apparaît). Le PNG est converti en "
        "JPEG. Téléversez plusieurs photos sous différents angles, l'une "
        "après l'autre.",
    # --------------------------------------------------- routes/areas ---
    "areas.titel": "Secteurs",
    "areas.kopf.sprung": "Accéder à une vue&nbsp;:",
    "areas.verwaltung.titel": "Gérer les secteurs",
    "areas.verwaltung.camzahl.eins": "{n} caméra",
    "areas.verwaltung.camzahl.viele": "{n} caméras",
    "areas.verwaltung.attr_entfernen":
        "retirer ce secteur — ses caméras retournent dans Default",
    "areas.verwaltung.attr_neu": "nom du nouveau secteur",
    "areas.verwaltung.knopf_anlegen": "Ajouter un secteur",
    "areas.verwaltung.titel_zuweisen": "Attribuer les caméras",
    "areas.verwaltung.satz_zuweisen":
        "Une caméra appartient à exactement un secteur&nbsp;; tout ce qui "
        "n'est pas attribué reste dans Default. L'enregistrement ne "
        "nécessite aucun redémarrage du service.",
    "areas.verwaltung.pill_nicht_gesehen": "non vue",
    "areas.verwaltung.attr_nicht_gesehen":
        "attribuée auparavant, absente de Frigate en ce moment",
    "areas.verwaltung.hinweis_keine_kameras":
        "Aucune caméra connue pour l'instant — connectez d'abord Frigate "
        "(Paramètres).",
    "areas.verwaltung.knopf_speichern": "Enregistrer les secteurs",
    # -------------------------------------- routes/benachrichtigungen ---
    "benachrichtigungen.titel": "Notifications",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• enregistré — laisser vide pour le conserver",
    "benachrichtigungen.felder.secret_leer": "non défini",
    "benachrichtigungen.felder.option_an": "activé",
    "benachrichtigungen.felder.option_aus": "désactivé",
    "benachrichtigungen.alerts.titel": "Alertes",
    "benachrichtigungen.alerts.hinweis":
        "Quelles catégories de verdict déclenchent une alerte — sur tous "
        "les canaux (Pushover, Telegram, topics de scène MQTT). Le push "
        "de personne reconnue lui-même dépend de l'interrupteur Présence "
        "ci-dessous&nbsp;; les topics de données MQTT (erkennung, "
        "heartbeat) publient toujours tant que la publication MQTT est "
        "activée.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik confirme une autre personne que Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate a étiqueté quelqu'un, suslik n'a vu aucun visage "
        "exploitable",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik a reconnu quelqu'un, Frigate non",
    "benachrichtigungen.kategorien.beide_unknown":
        "aucun des deux côtés n'a reconnu de visage",
    "benachrichtigungen.kategorien.erkannt":
        "une personne connue a été reconnue",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "un visage exploitable, mais aucune personne confirmée (présence "
        "inhabituelle possible)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "un visage trop faible ou trop petit pour être reconnu",
    "benachrichtigungen.alerts.stil_label":
        "Style du texte des alertes&nbsp;:",
    "benachrichtigungen.alerts.stil_worte": "mots simples",
    "benachrichtigungen.alerts.stil_worte_zahlen": "mots + scores bruts",
    "benachrichtigungen.alerts.stil_hinweis":
        "la façon dont les alertes décrivent une correspondance (mots "
        "simples par défaut&nbsp;; valeurs brutes cosinus/score seulement "
        "si vous voulez les retrouver)",
    "benachrichtigungen.alerts.label_anwesenheit_push":
        "Push de présence&nbsp;:",
    "benachrichtigungen.alerts.label_alert_cooldown":
        "Délai entre alertes (s)&nbsp;:",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Délai entre push de présence (s)&nbsp;:",
    "benachrichtigungen.alerts.label_szene_karenz":
        "Délai de grâce de scène (s)&nbsp;:",
    "benachrichtigungen.pushover.label_token": "Token&nbsp;:",
    "benachrichtigungen.pushover.label_user": "Clé utilisateur&nbsp;:",
    "benachrichtigungen.pushover.knopf_test": "Tester Pushover",
    "benachrichtigungen.telegram.label_modus": "Mode&nbsp;:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=désactivé · ha=via Home Assistant · direkt=bot direct · "
        "beide=les deux",
    "benachrichtigungen.telegram.label_inhalt": "Pièce jointe&nbsp;:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=séquence courte, image si indisponible · bild=image seule "
        "(pas de transcodage — plus léger sur le matériel modeste)",
    "benachrichtigungen.telegram.label_bot_token": "Token du bot&nbsp;:",
    "benachrichtigungen.telegram.label_chat_id": "Chat ID&nbsp;:",
    "benachrichtigungen.telegram.label_cooldown":
        "Délai pour inconnus (s)&nbsp;:",
    "benachrichtigungen.telegram.knopf_test": "Tester Telegram",
    "benachrichtigungen.mqtt.label_publish":
        "Publier les topics de reconnaissance&nbsp;:",
    "benachrichtigungen.mqtt.label_host": "Hôte&nbsp;:",
    "benachrichtigungen.mqtt.label_port": "Port&nbsp;:",
    "benachrichtigungen.mqtt.label_user": "Utilisateur&nbsp;:",
    "benachrichtigungen.mqtt.label_password": "Mot de passe&nbsp;:",
    "benachrichtigungen.mqtt.label_topic_praefix":
        "Préfixe de topic&nbsp;:",
    "benachrichtigungen.mqtt.knopf_test": "Tester MQTT",
    "benachrichtigungen.fuss.knopf_speichern": "Enregistrer + redémarrer",
    # ----------------------------------------------- routes/aehnliche ---
    "aehnliche.kopf.titel": "Visages correspondants pour {person}",
    "aehnliche.kopf.satz":
        "Deux sources&nbsp;: les visages inconnus qui ressemblent à "
        "{person}, et les nouveaux visages issus d'événements où le "
        "système a déjà reconnu {person} avec un bon niveau de confiance. "
        "Cochez puis appliquez.",
    "aehnliche.kopf.link_zurueck": "retour",
    "aehnliche.unbekannt.titel": "Depuis les visages inconnus",
    "aehnliche.unbekannt.suche_titel":
        "Recherche en cours — les références sont relues.",
    "aehnliche.unbekannt.suche_hinweis": "La page s'actualise d'elle-même.",
    "aehnliche.unbekannt.hinweis_leer":
        "Aucun visage inconnu similaire dans la bibliothèque.",
    "aehnliche.unbekannt.aehnlichkeit": "similarité {sim}",
    "aehnliche.unbekannt.knopf_hinzu": "Ajouter la sélection à {person}",
    "aehnliche.vorschlaege.titel":
        "Nouveaux visages issus d'événements reconnus (7 jours)",
    "aehnliche.vorschlaege.suche_titel":
        "Recherche en cours — les événements reconnus sont parcourus.",
    "aehnliche.vorschlaege.suche_hinweis":
        "La page s'actualise d'elle-même&nbsp;; résultat dans une à deux "
        "minutes.",
    "aehnliche.vorschlaege.kachel_zeile": "{wann} · {kamera} · sim {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Recommandés",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutres — vérifiez l'image avant d'appliquer",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Clairement cette personne, mais soit la correspondance est sous "
        "le seuil de confiance, soit le cadrage est plus petit / moins "
        "net — un coup d'œil tranche.",
    "aehnliche.vorschlaege.knopf_alle":
        "Appliquer tous les recommandés ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt":
        "Appliquer la sélection à {person}",
    "aehnliche.vorschlaege.knopf_neu": "relancer la recherche",
    "aehnliche.vorschlaege.fuss":
        "au {stand} · recommandé = {person} avec un bon niveau de "
        "confiance + qualité de référence",
    "aehnliche.vorschlaege.hinweis_leer":
        "Rien de correspondant dans les événements reconnus.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Critères&nbsp;: sans ambiguïté cette personne, nouveau par "
        "rapport à la bibliothèque, suffisamment grand et net.",
    # ------------------------------------------------- routes/frigate ---
    "frigate.verbindung.titel": "Connexion",
    "frigate.verbindung.satz":
        "Mon programme lit les événements et les instantanés depuis votre "
        "Frigate via son API HTTP — rien n'est installé côté Frigate.",
    "frigate.verbindung.knopf_aendern": "Modifier la connexion",
    "frigate.verbindung.knopf_speichern": "Enregistrer &amp; redémarrer",
    "frigate.verbindung.knopf_abbrechen": "Annuler",
    "frigate.verbindung.hinweis_speichern":
        "l'enregistrement redémarre brièvement le service&nbsp;; cette "
        "tuile montre ensuite en direct si la nouvelle adresse répond",
    "frigate.kameras.titel": "Caméras",
    "frigate.kameras.satz":
        "Quelles caméras de Frigate ce programme surveille, et quelles "
        "zones comptent. Tout le reste est ignoré.",
    "frigate.kameras.beweis_keine_auswahl":
        "aucune sélection de caméras enregistrée pour l'instant — toutes "
        "les caméras proposées par Frigate sont utilisées",
    "frigate.kameras.knopf": "Gérer les caméras",
    "frigate.sync.titel": "Synchronisation",
    "frigate.sync.satz":
        "Maintient les deux bibliothèques de visages alignées&nbsp;: "
        "envoyer à Frigate les visages examinés, importer ce que seul "
        "Frigate possède &mdash; toujours votre décision, jamais "
        "automatique.",
    "frigate.sync.knopf": "Examiner &amp; synchroniser",
    "frigate.fr.titel": "La reconnaissance faciale propre à Frigate",
    "frigate.fr.satz":
        "Frigate sait aussi reconnaître les visages. Ce programme "
        "fonctionne avec ou sans &mdash; l'interrupteur se trouve dans la "
        "config de Frigate, lue ici en direct pour que vous sachiez ce "
        "qu'une synchronisation peut faire à l'instant.",
    "frigate.fr.beweis_unbekannt": "état inconnu — {detail}",
    "frigate.js.url_fehlt": "saisissez l'URL de Frigate",
    "frigate.js.fehler": "erreur\u00a0:",
    # ------------------------------------------- routes/ereignisliste ---
    "ereignisliste.offen.titel": "Cas ouverts à étiqueter ({n})",
    "ereignisliste.offen.satz":
        "Se remplit automatiquement&nbsp;: tous les événements avec des "
        "visages que personne n'a confirmés et que vous n'avez pas encore "
        "étiquetés. Ceux sans personne reconnue à proximité viennent en "
        "premier — ce sont ceux qui valent le coup d'œil. Après "
        "l'étiquetage, la carte s'estompe et disparaît au prochain "
        "chargement.",
    "ereignisliste.offen.frigate_mit": "Frigate&nbsp;: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate&nbsp;: —",
    "ereignisliste.offen.zeile_faces": "{n} visages · meilleur&nbsp;: {beste}",
    "ereignisliste.offen.link_video": "Vidéo",
    "ereignisliste.offen.kontext_erkannt":
        "reconnu dans la même fenêtre temporelle&nbsp;: {wer}",
    "ereignisliste.offen.kontext_fehlt":
        "aucune reconnaissance confirmée à proximité",
    "ereignisliste.blaettern.neuer": "← plus récents",
    "ereignisliste.blaettern.aelter": "plus anciens →",
    "ereignisliste.offen.blaettern_stand":
        "Page {seite}/{max} ({n} ouverts)",
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} événement à visage faible masqué — probablement aucun visage "
        "exploitable (rien de confirmé à proximité non plus).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} événements à visage faible masqués — probablement aucun "
        "visage exploitable (rien de confirmé à proximité non plus).",
    "ereignisliste.offen.schwach_zeigen": "les afficher",
    "ereignisliste.offen.schwach_alle":
        "les événements à visage faible sont aussi affichés —",
    "ereignisliste.offen.schwach_zurueck": "revenir à ceux qui comptent",
    "ereignisliste.offen.leer_titel": "Rien d'ouvert — tout est étiqueté.",
    "ereignisliste.offen.leer_hinweis":
        "Les nouveaux événements non confirmés avec visages apparaissent "
        "ici automatiquement.",
    "ereignisliste.titel": "Événements",
    "ereignisliste.filter.alle_areas": "tous les secteurs",
    "ereignisliste.filter.alle_kameras": "toutes les caméras",
    "ereignisliste.filter.alle_personen": "toutes les personnes",
    "ereignisliste.filter.alle_kategorien": "toutes les catégories",
    "ereignisliste.filter.knopf": "Filtrer",
    "ereignisliste.filter.reset": "réinitialiser",
    "ereignisliste.tabelle.blaettern_stand":
        "Page {seite}/{max} ({n} événements)",
    "ereignisliste.tabelle.kopf_zeit": "Heure",
    "ereignisliste.tabelle.kopf_kamera": "Caméra",
    "ereignisliste.tabelle.kopf_kategorie": "Catégorie",
    "ereignisliste.tabelle.kopf_crop": "Cadrage",
    "ereignisliste.tabelle.kopf_gt": "Confirmer ou corriger (GT)",
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "log",
    "ereignisliste.tabelle.link_video": "vidéo",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "séquence incomplète — jugée sur la portion lisible",
    # ------------------------------------------- routes/konfiguration ---
    "konfiguration.kette.gesicht_titel": "Visage",
    "konfiguration.kette.gesicht_kosten":
        "analyse de base sur la séquence enregistrée — toujours active",
    "konfiguration.kette.gesicht_zeitpunkt": "par événement",
    "konfiguration.kette.person_titel": "Personne (corps)",
    "konfiguration.kette.person_kosten":
        "l'étape locale la plus coûteuse (embedding du corps sur votre "
        "matériel)",
    "konfiguration.kette.person_zeitpunkt":
        "par événement, décidé selon le verdict du passage",
    "konfiguration.kette.vision_titel": "Vision",
    "konfiguration.kette.vision_kosten":
        "une requête par passage vers l'endpoint vision configuré",
    "konfiguration.kette.vision_zeitpunkt": "à la fin du passage",
    "konfiguration.kette.immer_an": "toujours",
    "konfiguration.kette.immer_hinweis": "(non désactivable aujourd'hui)",
    "konfiguration.kette.gesicht_erkl":
        "la voie du visage est l'épine dorsale de chaque analyse — "
        "personne et vision dépendent de son verdict de passage",
    "konfiguration.kette.grund_person":
        "aucun modèle de personne entraîné n'est encore armé",
    "konfiguration.kette.grund_vision": "la détection vision est désactivée",
    "konfiguration.kette.grund_aus": "désactivé ici",
    "konfiguration.kette.status_aus": "état&nbsp;: à l'arrêt ({grund})",
    "konfiguration.kette.zeile_kosten": "coût&nbsp;: {kosten}",
    "konfiguration.kette.titel": "Chaîne de reconnaissance",
    "konfiguration.kette.satz":
        "Quels moteurs de reconnaissance tournent, et dans quel ordre. La "
        "condition \"nur_wenn_gesicht_leer\" signifie&nbsp;: l'étape ne "
        "s'exécute que si la voie du visage n'a PAS pu confirmer tout le "
        "monde lors du passage — décidé sur l'ensemble du passage, jamais "
        "sur un événement isolé. Modifier l'ordre lui-même viendra plus "
        "tard&nbsp;; aujourd'hui la chaîne commence toujours par la voie "
        "du visage.",
    "konfiguration.knopf_speichern": "Enregistrer + redémarrer",
    "konfiguration.kette_blatt.hinweis":
        "Les modifications sont journalisées (config_audit.jsonl)&nbsp;; "
        "après l'enregistrement, le service redémarre proprement.",
    "konfiguration.titel": "Paramètres avancés",
    "konfiguration.kopf.satz1":
        "Les modifications sont journalisées (config_audit.jsonl)&nbsp;; "
        "après l'enregistrement, le service redémarre proprement (il "
        "attend la fin d'une analyse en cours).",
    "konfiguration.feld.option_an": "activé",
    "konfiguration.feld.option_aus": "désactivé",
    "konfiguration.abschnitt_alle": "Tous les paramètres",
    "konfiguration.tabelle.kopf_parameter": "Paramètre",
    "konfiguration.tabelle.kopf_wert": "Valeur",
    "konfiguration.tabelle.kopf_bedeutung": "Signification",
    "konfiguration.knopf_setup": "Relancer l'assistant d'installation",
    "konfiguration.abschnitt_readonly": "Lecture seule (console/yaml)",
    # ----------------------------------------------- routes/lernanker ---
    "lernanker.eimer.ok": "propre",
    "lernanker.eimer.unbestaetigt": "non confirmé",
    "lernanker.eimer.zu_duenn": "mince",
    "lernanker.eimer.hart": "mixte",
    "lernanker.bin.frontal": "De face",
    "lernanker.bin.links": "Regard vers la gauche",
    "lernanker.bin.rechts": "Regard vers la droite",
    "lernanker.kachel.attr_clip":
        "{kamera} · det {det} · un clic ouvre la séquence",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "ouvrir la séquence",
    "lernanker.kachel.grund_fehlt": "non évalué",
    "lernanker.detail.gruppe": "Groupe {pos} sur {gesamt}",
    "lernanker.detail.frage": "Qui est-ce&nbsp;?",
    "lernanker.badge.stuetz": "{n} visages ({phys} physiques)",
    "lernanker.badge.faces": "{n} visages",
    "lernanker.badge.durchgaenge": "{n} passages",
    "lernanker.badge.tage": "{n} jour(s)&nbsp;: {spanne}",
    "lernanker.badge.marge": "marge {marge}",
    "lernanker.link_zurueck": "retour à tous les groupes",
    "lernanker.detail.hinweis_klick":
        "cliquez sur un visage pour ouvrir sa séquence",
    "lernanker.detail.hinweis_auswahl":
        "cliquez sur une image pour la sélectionner ou la désélectionner",
    "lernanker.detail.hinweis_pfeil": "le petit &#9654; ouvre la séquence",
    "lernanker.detail.weiter": "Groupe suivant &#8230;",
    "lernanker.detail.pflege_hinweis":
        "l'entretien des références se fait sur la page Qualité",
    "lernanker.detail.verworfen":
        "écarté — images supprimées&nbsp;; le groupe reste mémorisé pour "
        "que les prochaines collectes des mêmes événements restent "
        "silencieuses",
    "lernanker.detail.dublette_hinweis":
        "vérification des doublons indisponible (le point d'ancrage "
        "précède la persistance des embeddings) — les doublons physiques "
        "sont tout de même filtrés",
    "lernanker.bekannt.system": "déjà dans votre système",
    "lernanker.bekannt.anker": "nommé sur un autre groupe",
    "lernanker.detail.empfohlen": "Recommandés — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Non recommandés ({n}) — laissés visibles, raison sur chaque image",
    "lernanker.detail.skip_weiter": "Passer ce groupe",
    "lernanker.detail.skip_zurueck": "Passer — retour aux groupes",
    "lernanker.detail.knopf_ja": "Oui, c'est {name}",
    "lernanker.detail.knopf_andere": "Quelqu'un d'autre &#8230;",
    "lernanker.detail.knopf_benennen_easy": "Nommer ce groupe &#8230;",
    "lernanker.detail.knopf_alle": "Sélectionner tous les recommandés",
    "lernanker.detail.knopf_keine": "Tout désélectionner",
    "lernanker.detail.attr_name": "nom de la personne (nouvelle ou existante)",
    "lernanker.detail.knopf_benennen": "Nommer ce groupe",
    "lernanker.detail.knopf_adopt": "Intégrer à la reconnaissance",
    "lernanker.js.fehler": "erreur\u00a0:",
    "lernanker.js.nicht_uebernommen": "non intégré",
    "lernanker.js.nicht_gespeichert": "non enregistré",
    "lernanker.liste.frage_lauf":
        "Supprimer la session {lid} et toutes ses données&nbsp;? Cela "
        "supprime définitivement ses {n} groupe(s) — y compris les nommés "
        "et les écartés — et toutes les images collectées. Les références "
        "déjà intégrées à la reconnaissance restent. Impossible à annuler.",
    "lernanker.liste.frage_alle":
        "Supprimer TOUTES les {alt} ancienne(s) session(s) avec leurs {n} "
        "groupe(s) et toutes les images collectées&nbsp;? Seule la "
        "session la plus récente {neuester} est conservée. Les références "
        "déjà intégrées à la reconnaissance restent. Impossible à annuler.",
    "lernanker.liste.knopf_alte":
        "Supprimer toutes les anciennes sessions (garder {neuester})",
    "lernanker.liste.lauf_zeile":
        "Supprimer une session — retire définitivement tous ses groupes "
        "et les images collectées (les références déjà intégrées "
        "restent)&nbsp;:",
    "lernanker.liste.verworfen":
        "{n} groupe(s) écarté(s) mémorisé(s) — les prochaines collectes "
        "des mêmes événements restent silencieuses",
    "lernanker.titel": "Groupes d'ancrage",
    "lernanker.liste.leer":
        "Aucun point d'ancrage pour l'instant — une session "
        "d'apprentissage les construit (Préparation → Collecte → "
        "Regroupement).",
    "lernanker.liste.leer_link": "Ouvrir la page de la session d'apprentissage",
    "lernanker.liste.kopf":
        "{n} groupes à partir de {ges} visages aptes à l'ancrage — {ok} "
        "propres, {rest} à examiner (grisés, avec la raison sur le "
        "badge). Ouvrez un groupe pour l'examiner et le nommer — les "
        "groupes nommés sont intégrés à la reconnaissance sur place "
        "(bouton Intégrer).",
    "lernanker.liste.kopf_link": "Retour à la session d'apprentissage",
    "lernanker.liste.mehr": "+{n} autres visages",
    "lernanker.liste.dublette":
        "même groupe que {anker} — collecté à nouveau par une session "
        "plus récente&nbsp;; nommez-le là-bas",
    "lernanker.liste.knopf_review": "Examiner le nommage",
    "lernanker.liste.knopf_view": "Voir le groupe",
    "lernanker.liste.knopf_benennen": "Nommer ces {n} visages",
    "lernanker.liste.frage_verwerfen":
        "Écarter ce groupe&nbsp;? Ses images sont supprimées&nbsp;; le "
        "groupe reste mémorisé pour que les prochaines collectes des "
        "mêmes événements restent silencieuses.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Écarter ce groupe&nbsp;? Ses images sont supprimées et le "
        "nommage en attente est abandonné&nbsp;; le groupe reste mémorisé "
        "pour que les prochaines collectes des mêmes événements restent "
        "silencieuses.",
    "lernanker.liste.knopf_verwerfen": "Écarter",
    # ---------------------------------------------- routes/syncauswahl ---
    "syncauswahl.titel":
        "Examiner &amp; synchroniser — références vers Frigate",
    "syncauswahl.kopf.satz":
        "Frigate passe chaque référence téléversée dans son propre "
        "détecteur de visages et refuse les images où il n'en trouve "
        "aucun. Cette page vérifie d'abord la même chose, vous montre "
        "chaque candidat et n'envoie que ce que vous cochez.",
    "syncauswahl.fehler.titel": "Candidats indisponibles",
    "syncauswahl.fehler.satz":
        "La liste des candidats nécessite un Frigate joignable — sa "
        "bibliothèque de visages est une moitié de la comparaison.",
    "syncauswahl.link_diagnose_auf": "ouvrir le diagnostic",
    "syncauswahl.link_diagnose": "diagnostic",
    "syncauswahl.link_system": "retour à Système",
    "syncauswahl.kachel.frigate_abgelehnt": "Refusée par Frigate&nbsp;: {fehler}",
    "syncauswahl.kachel.pruefe": "vérification …",
    "syncauswahl.kachel.vorpruefung_ok": "vérification préalable ok",
    "syncauswahl.kachel.wohl_abgelehnt":
        "serait probablement refusée&nbsp;: {grund}",
    "syncauswahl.kachel.kein_gesicht": "aucun visage détectable",
    "syncauswahl.kachel.kein_grund": "aucune raison indiquée",
    "syncauswahl.kachel.senden": "envoyer",
    "syncauswahl.kachel.knopf_skip": "ignorer",
    "syncauswahl.kachel.attr_skip":
        "Ne jamais envoyer cette image — mémorisé, la synchronisation "
        "automatique l'ignore aussi",
    "syncauswahl.kachel.knopf_restore": "rétablir",
    "syncauswahl.kachel.attr_restore":
        "Remettre cette image sur la liste des candidats",
    "syncauswahl.geloescht.satz_import":
        "venait de Frigate et n'y est plus",
    "syncauswahl.geloescht.satz_export":
        "a été envoyée sous ce nom exact et n'y est plus",
    "syncauswahl.geloescht.badge": "supprimée dans Frigate",
    "syncauswahl.knopf_anbieten": "proposer à nouveau",
    "syncauswahl.geloescht.attr_anbieten":
        "La remettre sur la liste des candidats — la prochaine "
        "synchronisation (manuelle ou automatique) l'enverra à nouveau",
    "syncauswahl.geloescht.knopf_respekt": "respecter la suppression",
    "syncauswahl.geloescht.attr_respekt":
        "Mémoriser que cette image doit rester hors de Frigate",
    "syncauswahl.api.badge": "{person} — envoyée auparavant",
    "syncauswahl.api.attr_anbieten":
        "La remettre sur la liste des candidats (envoie une seconde "
        "copie si Frigate possède encore la première)",
    "syncauswahl.fr.titel_unbekannt":
        "Reconnaissance faciale de Frigate&nbsp;: état inconnu",
    "syncauswahl.fr.satz_unbekannt":
        "suslik n'a pas pu le lire depuis Frigate à l'instant — {detail}. "
        "L'envoi peut quand même fonctionner&nbsp;; Frigate a le dernier "
        "mot de toute façon.",
    "syncauswahl.fr.titel_an":
        "Reconnaissance faciale de Frigate&nbsp;: activée",
    "syncauswahl.fr.satz_an":
        "(lue depuis Frigate au chargement de cette page) — il accepte "
        "les téléversements de références.",
    "syncauswahl.fr.titel_aus":
        "Reconnaissance faciale de Frigate&nbsp;: désactivée",
    "syncauswahl.bilanz.titel": "Bilan",
    "syncauswahl.bilanz.hauptzeile":
        "images de référence · {beide} déjà dans Frigate · {bereit} "
        "prêtes au transfert",
    "syncauswahl.bilanz.abgelehnt": "{n} refusées par Frigate",
    "syncauswahl.bilanz.geloescht": "{n} supprimées dans Frigate",
    "syncauswahl.bilanz.exportiert":
        "{n} envoyées auparavant (Frigate les a renommées)",
    "syncauswahl.bilanz.abgewaehlt": "{n} désélectionnées",
    "syncauswahl.bilanz.nur_frigate": "{n} seulement dans Frigate",
    "syncauswahl.bilanz.je_person": "Dans Frigate, par personne&nbsp;:",
    "syncauswahl.bilanz.kandidaten.eins": "{n} candidat",
    "syncauswahl.bilanz.kandidaten.viele": "{n} candidats",
    "syncauswahl.bilanz.vorpruefung":
        "{n} passent la vérification préalable",
    "syncauswahl.bilanz.gewaehlt_wort": "sélectionnées",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "{n} seraient probablement refusées par Frigate (décochées, mais "
        "vous pouvez quand même les envoyer).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "{n} ont déjà été refusées par Frigate (décochées&nbsp;; en "
        "cocher une retente l'envoi).",
    "syncauswahl.pruef.fehler":
        "la vérification préalable n'a pas pu s'exécuter&nbsp;: {fehler} "
        "— les images sans verdict restent sélectionnées.",
    "syncauswahl.pruef.laeuft.eins":
        "vérification de {n} image … {fertig}/{gesamt} (cette page se "
        "recharge dès que c'est terminé)",
    "syncauswahl.pruef.laeuft.viele":
        "vérification de {n} images … {fertig}/{gesamt} (cette page se "
        "recharge dès que c'est terminé)",
    "syncauswahl.sperre.titel": "Mode lecture seule activé",
    "syncauswahl.sperre.satz":
        "suslik n'écrit pas dans Frigate en ce moment.",
    "syncauswahl.knopf_alle": "Tout sélectionner",
    "syncauswahl.knopf_keine": "Tout désélectionner",
    "syncauswahl.knopf_transfer":
        "Transférer {n} sélectionnées vers Frigate",
    "syncauswahl.leer.titel": "Rien à envoyer",
    "syncauswahl.leer.satz":
        "Chaque référence a déjà atteint Frigate ou est désélectionnée.",
    "syncauswahl.leer.zusatz":
        "Les sections ci-dessous listent ce qui ne peut pas être "
        "transféré tel quel.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} probablement refusées",
    "syncauswahl.gruppe.prueft": "{n} encore en vérification",
    "syncauswahl.geloescht.zusatz": "— votre décision",
    "syncauswahl.geloescht.satz":
        "Celles-ci sont encore dans votre bibliothèque, mais Frigate ne "
        "les a plus sous le nom avec lequel elles avaient été "
        "enregistrées. suslik ne les renvoie jamais sans votre "
        "décision&nbsp;: supprimer un visage dans Frigate peut être "
        "volontaire. Proposez-la à nouveau pour en faire un candidat "
        "normal — dès lors la prochaine synchronisation, y compris "
        "l'automatique, la téléverse. Respectez la suppression pour la "
        "garder définitivement à l'écart.",
    "syncauswahl.aufklapp": "— afficher",
    "syncauswahl.api.titel":
        "{n} exportées auparavant — Frigate les conserve sous ses "
        "propres noms",
    "syncauswahl.api.satz":
        "Celles-ci sont passées par l'API de Frigate, et Frigate renomme "
        "chaque référence qu'il accepte. suslik ne peut donc pas savoir "
        "par le nom si elles y sont encore — aucun compteur de cette "
        "page ne peut le prouver dans un sens ou dans l'autre. Rien "
        "n'est renvoyé automatiquement&nbsp;; si vous savez qu'une "
        "manque, proposez-la à nouveau (cela envoie une seconde copie si "
        "la première y est encore).",
    "syncauswahl.api.vergleich":
        "{person}&nbsp;: {n} envoyées par cette voie · Frigate détient "
        "actuellement {bestand} images",
    "syncauswahl.import.zeile.eins": "{n} image&nbsp;:",
    "syncauswahl.import.zeile.viele": "{n} images&nbsp;:",
    "syncauswahl.import.mehr": "… et {n} de plus",
    "syncauswahl.import.satz":
        "Frigate possède ces images de référence, suslik non. L'import "
        "les copie dans votre bibliothèque&nbsp;; rien ne change dans "
        "Frigate.",
    "syncauswahl.import.warnung":
        "Cette liste peut inclure vos propres téléversements&nbsp;: "
        "Frigate renomme chaque référence qu'il accepte, suslik ne peut "
        "donc pas les distinguer des visages ajoutés directement dans "
        "Frigate. Les réimporter dupliquerait du contenu.",
    "syncauswahl.import.knopf": "Les importer dans suslik",
    "syncauswahl.raus.satz":
        "Mémorisées volontairement&nbsp;: celles-ci restent dans votre "
        "bibliothèque mais ne sont jamais envoyées à Frigate, pas même "
        "par la synchronisation automatique. Rétablir en remet une sur "
        "la liste des candidats.",
    "syncauswahl.alter.unbekannt": "âge inconnu",
    "syncauswahl.alter.sekunden": "il y a {s} s",
    "syncauswahl.alter.minuten": "il y a {m} min",
    "syncauswahl.alter.stunden": "il y a {h} h {m} min",
    "syncauswahl.ergebnis.titel": "Dernier transfert",
    "syncauswahl.ergebnis.stopp": "arrêté&nbsp;:",
    "syncauswahl.ergebnis.wand":
        "même erreur trois fois de suite&nbsp;: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "téléversée — {bild}",
    "syncauswahl.ergebnis.zaehler":
        "{hoch} téléversées · {weg} non acceptées",
    "syncauswahl.ergebnis.auswahl": "sur {n} sélectionnées",
    "syncauswahl.ergebnis.uebersprungen": "{n} désélectionnées (ignorées)",
    "syncauswahl.ergebnis.dauer": "a duré {n} s",
    # ---------------------------------------------------- routes/live ---
    "live.hinweis_gpu":
        "Fonctionne pour l'instant uniquement avec un GPU — nous "
        "travaillons sur une option CPU sans pouvoir la promettre.",
    "live.hinweis_cpu":
        "Mode CPU&nbsp;: les surveillances coûtent cher ici — la "
        "vérification rapide prend typiquement 1–2 s (une version GPU "
        "réagit en moins d'une seconde), et les surveillances "
        "supplémentaires se ralentissent mutuellement. Leur nombre reste "
        "votre choix&nbsp;; nous recommandons de commencer par une seule.",
    "live.zeile.alter": "(âgé de {tage} jour(s))",
    "live.test.zeile":
        "test de source {wann}&nbsp;: {aufloesung} → {skala}, "
        "{bilder_s} images/s",
    "live.test.durchsatz":
        "(débit, pas la cadence de livraison — relancez le test de source)",
    "live.test.provider": "provider {provider}",
    "live.test.sw": "(décodage logiciel)",
    "live.test.entwertet":
        "— INVALIDÉ&nbsp;: la source a changé depuis ce test",
    "live.test.fehlgeschlagen":
        "dernier test de source ÉCHOUÉ ({wann})&nbsp;: {fehler}",
    "live.messung.zeile": "charge mesurée le {wann}&nbsp;: {text}",
    "live.messung.veraltet":
        "— OBSOLÈTE&nbsp;: la source a changé depuis cette mesure, "
        "mesurez à nouveau",
    "live.messung.fehlgeschlagen":
        "dernière mesure de charge ÉCHOUÉE ({wann})&nbsp;: {fehler}",
    "live.zaehler.auftritte": "{n} apparitions",
    "live.zaehler.trigger": "{n} déclenchements",
    "live.zaehler.alerts": "{n} alertes",
    "live.zaehler.letzter": "dernier déclenchement {zeit}",
    "live.zaehler.kopf": "depuis le démarrage du moteur&nbsp;:",
    "live.engine.titel_aus": "Moteur de surveillance&nbsp;: à l'arrêt",
    "live.engine.satz_aus":
        "Aucun signal de vie du processus moteur. Les tuiles montrent la "
        "configuration enregistrée&nbsp;; activer, tester sur une "
        "surveillance en cours et mesurer la charge nécessitent le "
        "moteur — le service le démarre automatiquement dès qu'au moins "
        "une surveillance est activée.",
    "live.engine.cpu_mit_limit":
        "CPU suslik à l'instant&nbsp;: {kerne} sur {limit} cœurs "
        "autorisés (conteneur entier&nbsp;: surveillances, analyse, "
        "service)",
    "live.engine.cpu_ohne_limit":
        "CPU suslik à l'instant&nbsp;: {kerne} cœurs (conteneur "
        "entier&nbsp;: surveillances, analyse, service)",
    "live.engine.rss": "RSS du moteur {rss} Mo",
    "live.engine.grundkosten": "coût de base {mb} Mo",
    "live.engine.je_stream": "{mb} Mo par flux ({quelle})",
    "live.engine.je_stream_fehlt":
        "RAM par flux pas encore mesurée sur cette machine",
    "live.engine.ram_frei": "{mb} Mo de RAM libre ({quelle})",
    "live.engine.ram_unlesbar":
        "RAM&nbsp;: aucune limite de conteneur lisible",
    "live.engine.detektor": "détecteur {ms} ms/image ({quelle})",
    "live.engine.drossel":
        "niveau de bridage {stufe}, utilisation {auslastung}",
    "live.engine.rest":
        "après un flux de plus&nbsp;: il resterait ~{mb} Mo de RAM",
    "live.engine.rest_warnung":
        "— SOUS le plancher de sécurité, aucun slot supplémentaire",
    "live.engine.kapazitaet":
        "capacité&nbsp;: jusqu'à {n} surveillance(s) (plafond fixe "
        "{hart}) — limité par&nbsp;: {grund}",
    "live.engine.hart": "plafond fixe de {hart} surveillances",
    "live.engine.titel_standalone":
        "Moteur de surveillance&nbsp;: actif (moteur autonome détecté)",
    "live.engine.titel_an": "Moteur de surveillance&nbsp;: actif",
    "live.gruppe.laufend": "En cours",
    "live.gruppe.bereit": "Prêtes",
    "live.gruppe.rest": "Non configurées",
    "live.gruppe.versteckt": "Masquées",
    "live.gruppe.ohne_area": "Sans secteur",
    "live.kachel.attr_fremd":
        "configurée ici, mais cette caméra n'est pas dans Frigate en ce "
        "moment",
    "live.kachel.pill_fremd": "absente de Frigate",
    "live.kachel.attr_detect":
        "flux detect de Frigate — la vraie résolution du flux apparaît "
        "après que le service a sondé le flux ou qu'un test de source a "
        "tourné",
    "live.knopf_konfigurieren": "Configurer",
    "live.knopf_test": "Lancer le test de source",
    "live.knopf_messung": "Mesurer la charge",
    "live.knopf_enable": "Activer",
    "live.knopf_disable": "Désactiver",
    "live.knopf_zeigen": "Afficher",
    "live.knopf_verstecken": "Masquer",
    "live.banner.kameraliste":
        "Impossible de lire la liste des caméras Frigate&nbsp;: {fehler}",
    "live.schalter.ungruppiert": "vue non groupée",
    "live.schalter.area": "regrouper par secteur",
    "live.sperre.cpu_titel": "Mode CPU",
    "live.sperre.titel": "Indisponible sur cette version",
    "live.sperre.satz":
        "La surveillance en direct nécessite une version GPU — une puce "
        "graphique Intel intégrée (images gpu / gpu-legacy), une carte "
        "NVIDIA (image cuda) ou une carte AMD (image rocm) conviennent "
        "toutes.",
    "live.sperre.cpu_only":
        "Elle n'est pas disponible sur l'image CPU seule.",
    "live.erklaer.titel":
        "Surveillance en direct — réaction immédiate sur le flux caméra",
    "live.erklaer.satz1":
        "Une surveillance en direct se connecte directement à un flux "
        "caméra et réagit pendant que la personne est encore à "
        "l'image&nbsp;: le premier visage lance une vérification, et "
        "après le nombre configuré de détections cohérentes, un signal "
        "vérifié part — l'objectif est sous la seconde (199–801 ms "
        "mesurés sur l'installation de référence). Utilisez-la pour "
        "déclencher vos automatisations domotiques, p. ex. via MQTT.",
    "live.erklaer.link":
        "En savoir plus&nbsp;: comment fonctionne la surveillance en "
        "direct",
    "live.titel": "Surveillance en direct",
    "live.leer.titel": "Aucune caméra trouvée.",
    "live.leer.hinweis":
        "Configurez d'abord la connexion Frigate — les tuiles "
        "apparaissent par caméra.",
    "live.knopf_speichern": "Enregistrer",
    "live.detail.titel": "Surveillance en direct — {name}",
    "live.abschnitt.quelle": "Source",
    "live.quelle.proxy":
        "restream go2rtc via Frigate (par défaut, recommandé)",
    "live.quelle.direct": "URL producer de la caméra, découverte via go2rtc",
    "live.quelle.url": "une URL de flux que vous saisissez vous-même",
    "live.detail.url_label": "URL du flux (source 'url' uniquement)&nbsp;:",
    "live.detail.url_hinweis":
        "les identifiants dans l'URL sont masqués partout où ils "
        "s'affichent — laissez le champ tel quel pour conserver l'URL "
        "enregistrée, ou collez-en une nouvelle",
    "live.detail.quelle_hinweis":
        "Changer la source invalide le test de source — relancez-le "
        "avant d'activer.",
    "live.abschnitt.aufloesung": "Résolution de traitement",
    "live.hoehe.default": "par défaut (1080p)",
    "live.hoehe.h360":
        "360p — repli pour GPU faible, le nom part le plus tard (mesuré)",
    "live.hoehe.h720":
        "720p — décodage plus léger, le nom part plus tard",
    "live.hoehe.h1080":
        "1080p — point idéal (mesuré&nbsp;: nom ~2,4 s plus tôt qu'en "
        "720p)",
    "live.hoehe.h1440": "1440p — aucun gain mesuré par rapport au 1080p",
    "live.hoehe.h2160":
        "2160p — 4K natif, gain marginal, coût de décodage le plus élevé",
    "live.abschnitt.alarm": "Chaîne d'alerte",
    "live.detail.ende_label": "Fin après absence de visage (s)&nbsp;:",
    "live.detail.ende_hinweis":
        "une apparition se termine après ce nombre de secondes sans "
        "visage (3–120)",
    "live.detail.scharf_label": "Réarmé après (s)&nbsp;:",
    "live.detail.scharf_hinweis":
        "secondes minimales entre alertes — si quelqu'un est présent, une "
        "nouvelle alerte part après ce délai&nbsp;; 0 = chaque "
        "déclenchement alerte (0–3600)",
    "live.abschnitt.kanaele": "Canaux de notification",
    "live.detail.namensschaetzung":
        "Les alertes incluent une estimation préliminaire du nom "
        "(\"probablement X\") quand le visage correspond à une personne "
        "connue — jamais enregistrée, jamais utilisée pour "
        "l'apprentissage.",
    "live.abschnitt.test": "Tester &amp; mesurer",
    "live.detail.gesperrt_hinweis":
        "tester et mesurer sont indisponibles tant que la surveillance "
        "en direct est verrouillée sur cette machine — la note en haut "
        "de cette page explique pourquoi.",
    "live.knopf_messung_lang": "Mesurer la charge (15–30 s)",
    "live.detail.messung_hinweis":
        "la mesure de charge met en pause les autres surveillances "
        "pendant son exécution",
    "live.detail.link_zurueck": "retour à la vue d'ensemble",
    # ----------------------------------------------- routes/erkennung ---
    "erkennung.titel": "Reconnaissance",
    "erkennung.kopf.satz":
        "Les quatre façons dont votre système peut reconnaître quelqu'un "
        "— chacune a sa carte&nbsp;: l'activer, voir qu'elle fonctionne, "
        "la configurer. L'interrupteur de la surveillance en direct agit "
        "immédiatement&nbsp;; les changements corps et vision "
        "s'appliquent avec Enregistrer + redémarrer.",
    "erkennung.kipp.label": "Activé",
    "erkennung.kipp.attr_verriegelt":
        "toujours actif — toutes les autres méthodes s'appuient sur le "
        "verdict du visage",
    "erkennung.link_how": "Comment ça marche &#8230;",
    "erkennung.live.titel": "Surveillance en direct",
    "erkennung.live.beweis_prefix": "surveille",
    "erkennung.live.beweis_zaehler": "{an} des {ges}",
    "erkennung.live.beweis_suffix": "caméras configurées",
    "erkennung.live.beweis_keine_laufend":
        "caméra(s) configurée(s), aucune en cours",
    "erkennung.live.beweis_keiner":
        "aucune surveillance configurée pour l'instant",
    "erkennung.live.expert_schalter":
        "désactiver arrête toutes les surveillances en cours&nbsp;; "
        "activer démarre toutes les surveillances configurées (le verrou "
        "par caméra s'applique toujours)",
    "erkennung.live.link_prokamera": "gestion par caméra",
    "erkennung.live.knopf_kameras": "Choisir les caméras …",
    "erkennung.knopf_register_face": "Enregistrer un visage …",
    "erkennung.gesicht.titel": "Reconnaissance faciale",
    "erkennung.gesicht.satz":
        "La voie la plus précise&nbsp;: chaque passage est confronté aux "
        "visages des personnes que vous avez apprises au système. C'est "
        "l'épine dorsale — corps et vision dépendent de son verdict de "
        "passage, elle n'a donc pas d'interrupteur aujourd'hui.",
    "erkennung.gesicht.beweis_personen": "{n} personnes",
    "erkennung.gesicht.beweis_bilder": "{n} images de référence",
    "erkennung.gesicht.knopf_verwalten": "Gérer les personnes …",
    "erkennung.koerper.titel": "Reconnaissance corporelle",
    "erkennung.koerper.satz":
        "Reconnaît les membres du foyer même sans visage visible, à la "
        "carrure et à la posture — elle apprend d'elle-même à partir des "
        "photos examinées.",
    "erkennung.koerper.beweis_kein_modell":
        "aucun modèle de personne pour l'instant — apprenez et examinez "
        "d'abord",
    "erkennung.status.kein_modell":
        "à l'arrêt (aucun modèle de personne entraîné n'est encore armé)",
    "erkennung.status.hier_aus": "à l'arrêt (désactivé ici)",
    "erkennung.status.vision_aus":
        "à l'arrêt (la détection vision est désactivée)",
    "erkennung.koerper.link_modell": "état du modèle",
    "erkennung.koerper.knopf_status": "État du modèle …",
    "erkennung.koerper.knopf_register": "Enregistrer un corps …",
    "erkennung.vision.titel": "Vision IA",
    "erkennung.vision.beta": "Bêta",
    "erkennung.vision.satz":
        "Une IA d'image comme arbitre pour les cas difficiles. Nécessite "
        "un endpoint de modèle (local ou payant) — chaque vérification "
        "coûte des requêtes.",
    "erkennung.vision.beweis_an": "endpoint connecté",
    "erkennung.vision.beweis_aus": "aucun endpoint connecté",
    "erkennung.vision.knopf_connect": "Connecter un modèle …",
    "erkennung.vision.knopf_register": "Enregistrer la vision …",
    "erkennung.abschnitt_property": "Paramétrage de la propriété",
    "erkennung.areas.titel": "Secteurs",
    "erkennung.areas.satz":
        "Ce qui compte sur la propriété&nbsp;: tracez des secteurs pour "
        "que les alertes ne partent que là où cela vous importe — "
        "l'allée compte, la rue derrière la clôture non.",
    "erkennung.areas.beweis_zahl": "secteur(s) défini(s)",
    "erkennung.areas.beweis_keine":
        "aucun secteur pour l'instant — tout compte",
    "erkennung.areas.knopf": "Gérer les secteurs &#8230;",
    "erkennung.knopf_speichern": "Enregistrer + redémarrer",
    # --------------------------------------------------- routes/faces ---
    "faces.titel": "Visages",
    "faces.link_how": "Comment ça marche &#8230;",
    "faces.bekannt.titel": "Personnes connues",
    "faces.bekannt.knopf_verwalten": "Gérer les personnes &#8230;",
    "faces.bekannt.knopf_register": "Enregistrer un visage &#8230;",
    "faces.bekannt.leer":
        "aucune personne apprise pour l'instant — enregistrez le premier "
        "visage ci-dessus",
    "faces.bekannt.beweis_personen": "{n} personnes",
    "faces.bekannt.beweis_bilder": "{n} images de référence",
    "faces.lernen.titel": "Apprentissage",
    "faces.lernen.knopf_start": "Démarrer l'apprentissage &#8230;",
    "faces.lernen.knopf_review": "Examiner les suggestions &#8230;",
    "faces.lernen.beweis_offen": "suggestion(s) à examiner",
    "faces.lernen.beweis_leer":
        "rien en attente — le système continue de collecter tout seul",
    "faces.lernen.satz": "Examinez ce que les caméras ont collecté.",
    "faces.unbekannt.titel": "Inconnus",
    "faces.unbekannt.knopf": "Examiner les inconnus &#8230;",
    "faces.unbekannt.beweis_offen": "visiteur(s) inconnu(s) récurrent(s)",
    "faces.unbekannt.beweis_leer": "aucun visiteur inconnu récurrent",
    "faces.unbekannt.satz": "Des visiteurs encore sans nom.",
    "faces.qualitaet.titel": "Qualité des photos",
    "faces.qualitaet.stand":
        "dernière vérification {wann} &middot; {n} constat(s)",
    "faces.qualitaet.knopf_check": "Vérifier la qualité des photos",
    "faces.qualitaet.popup_satz":
        "Remesure chaque photo de référence et repère les faibles, les "
        "quasi-doublons et les visages confondus. Prend environ une "
        "minute et tourne en arrière-plan.",
    "faces.qualitaet.label_alle": "Toutes les personnes",
    "faces.qualitaet.label_eine": "Une personne&nbsp;:",
    "faces.qualitaet.knopf_start": "Lancer la vérification",
    "faces.qualitaet.knopf_abbrechen": "Annuler",
    "faces.qualitaet.knopf_ergebnisse": "Derniers résultats &#8230;",
    "faces.qualitaet.satz": "Trouve les photos faibles ou confondues.",
    # ----------------------------------------------- routes/qualitaet ---
    "qualitaet.kopf.titel": "Qualité — bibliothèque de références",
    "qualitaet.kopf.hinweis":
        "touchez une personne ci-dessous pour voir toutes ses photos "
        "avec les faibles marquées.",
    "qualitaet.kopf.stand": "État&nbsp;: {stand} · {n} références",
    "qualitaet.kopf.knopf_neu": "Revérifier maintenant",
    "qualitaet.lauf.fehler":
        "dernière vérification ÉCHOUÉE&nbsp;: {fehler} &mdash; "
        "relancez-la.",
    "qualitaet.lauf.checking":
        "vérification de la photo {i} sur {n} &hellip;",
    "qualitaet.lauf.reload_person":
        "rechargez ensuite cette page pour le résultat à jour.",
    "qualitaet.lauf.reload_auto": "la page s'actualise d'elle-même.",
    "qualitaet.lauf.abgebrochen":
        "la dernière vérification ne s'est pas terminée (redémarrage du "
        "service ou arrêt manuel) &mdash; relancez-la.",
    "qualitaet.tabelle.kopf_person": "personne",
    "qualitaet.tabelle.kopf_bilder": "photos",
    "qualitaet.tabelle.kopf_gut": "bonnes",
    "qualitaet.tabelle.kopf_mittel": "moyennes",
    "qualitaet.tabelle.kopf_unter": "sous la barre",
    "qualitaet.tabelle.kopf_links": "&larr; gauche",
    "qualitaet.tabelle.kopf_front": "de face",
    "qualitaet.tabelle.kopf_rechts": "droite &rarr;",
    "qualitaet.tabelle.kopf_doppel": "doublons",
    "qualitaet.tabelle.kopf_verwechslung": "confusion",
    "qualitaet.person.funde": "{n} photo(s) à regarder de près",
    "qualitaet.person.verwechselt": "confusion possible",
    "qualitaet.person.alles_gut": "tout va bien",
    "qualitaet.ergebnis.alles_gut": "Tout va bien.",
    "qualitaet.ergebnis.alles_gut_satz":
        "{n} photos de {np} personnes vérifiées &mdash; rien ne réclame "
        "votre attention.",
    "qualitaet.wort.defekt": "fichier défectueux",
    "qualitaet.wort.kein_gesicht": "aucun visage trouvé",
    "qualitaet.wort.zu_klein": "trop petite",
    "qualitaet.wort.unscharf": "floue",
    "qualitaet.wort.schwach": "photo faible",
    "qualitaet.galerie.looks_like": "ressemble à {name}",
    "qualitaet.galerie.doppel": "doublon — celle conservée la couvre",
    "qualitaet.galerie.gut": "bonne",
    "qualitaet.galerie.gut_behalten": "bonne — conservée parmi ses doublons",
    "qualitaet.galerie.okay": "correcte",
    "qualitaet.galerie.satz_gut": "Les {n} photos semblent toutes bonnes.",
    "qualitaet.galerie.satz_funde":
        "{funde} des {n} photos méritent un coup d'œil — les deux "
        "onglets de droite les regroupent. Cochez ce que vous voulez "
        "retirer — rien ne se passe sans votre clic.",
    "qualitaet.reiter.gut": "Bonnes ({n})",
    "qualitaet.reiter.check": "À vérifier ({n})",
    "qualitaet.reiter.weg": "Suppression proposée ({n})",
    "qualitaet.galerie.knopf_alle": "Tout sélectionner",
    "qualitaet.galerie.knopf_keine": "Tout désélectionner",
    "qualitaet.galerie.knopf_entfernen": "Retirer la sélection",
    "qualitaet.galerie.leer_gruppe": "rien dans ce groupe.",
    "qualitaet.galerie.titel": "{name} — qualité des photos",
    "qualitaet.galerie.link_zurueck": "&larr; retour à la vue d'ensemble",
    "qualitaet.galerie.leer_person": "aucune photo pour cette personne.",
    "qualitaet.leer.titel": "Aucune vérification calculée pour l'instant.",
    "qualitaet.leer.hinweis":
        "Cliquez sur Revérifier maintenant ci-dessus.",
    # ---------------------------------------------- routes/lernwizard ---
    "lernwizard.titel": "Session d'apprentissage",
    "lernwizard.link_how": "Comment ça marche &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Préparation",
    "lernwizard.phase.ernte": "Collecte (rassembler les visages)",
    "lernwizard.phase.anker": "Regroupement (points d'ancrage)",
    "lernwizard.phase.benennung": "Nommage (votre étape)",
    "lernwizard.phase.neben_ansichten": "Vues de profil",
    "lernwizard.phase.ganzkoerper": "Références corps entier",
    "lernwizard.phase.uebernahme": "Intégration dans le Master",
    "lernwizard.phase.fertig": "Terminé",
    "lernwizard.phase.aktuell": "(en cours)",
    "lernwizard.phase.link_benennen": "ouvrir les groupes et les nommer",
    "lernwizard.wizard.titel":
        "Apprentissage des personnes — session guidée",
    "lernwizard.wizard.satz":
        "Planifie une session d'apprentissage sur vos propres "
        "enregistrements. Préparation, collecte, regroupement, nommage "
        "et intégration à la reconnaissance s'exécutent tous "
        "réellement.",
    "lernwizard.wizard.lage_b":
        "B — les références et inconnus existants seront étendus",
    "lernwizard.wizard.lage_a":
        "A — démarrage à froid, aucun visage pour l'instant",
    "lernwizard.badge.unbekannt": "visiteurs inconnus",
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} visiteur inconnu attend sous",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} visiteurs inconnus attendent sous",
    "lernwizard.link_unbekannte": "Personnes &rarr; Inconnus",
    "lernwizard.wizard.unbekannt_hinweis":
        "Des visages collectés aujourd'hui qui ne correspondent à aucune "
        "personne connue — vous pouvez les nommer, les fusionner ou les "
        "mettre en sourdine là-bas tout de suite&nbsp;; aucune session "
        "d'apprentissage n'est nécessaire pour cela.",
    "lernwizard.wizard.start_titel": "Point de départ",
    "lernwizard.wizard.start_hinweis":
        "Interrupteur de nettoyage pour les inconnus collectés "
        "automatiquement&nbsp;: arrive avec l'étape de nommage.",
    "lernwizard.wizard.knopf_letzte": "les {n} derniers",
    "lernwizard.wizard.knopf_alle": "TOUS les accessibles",
    "lernwizard.wizard.attr_eigen": "N au choix",
    "lernwizard.wizard.knopf_go": "Valider",
    "lernwizard.wizard.scope_titel": "Étendue (événements, pas jours)",
    "lernwizard.wizard.scope_hinweis":
        "TOUS parcourt tout l'historique accessible (borné par la "
        "rétention de Frigate — le bilan ci-dessous montre jusqu'où).",
    "lernwizard.wizard.auswahl_titel": "Votre sélection",
    "lernwizard.wizard.auswahl_zeile":
        "les {n} derniers événements de personne = retour jusqu'à {wann} "
        "· {clips} avec séquence disponible",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} plus anciens sans séquence seront ignorés",
    "lernwizard.wizard.auswahl_hinweis":
        "La coupe est exacte à N — compléter la sélection en passages "
        "entiers arrive avec l'étape de regroupement.",
    "lernwizard.wizard.q_teilgemessen":
        "vitesse d'analyse mesurée sur CETTE machine&nbsp;; l'estimation "
        "de téléchargement utilise les valeurs par défaut",
    "lernwizard.wizard.q_gemessen": "mesuré sur CETTE machine",
    "lernwizard.wizard.q_skip":
        ", mesure sautée sur cette machine ({grund})",
    "lernwizard.wizard.q_wartet":
        ", la mesure attend un slot d'analyse libre …",
    "lernwizard.wizard.q_laeuft": ", mesure en cours …",
    "lernwizard.wizard.q_rueckfall":
        "valeurs de repli — pas encore mesurées ici",
    "lernwizard.wizard.dauer_titel": "Durée estimée",
    "lernwizard.wizard.dauer_zeile":
        "analyse ~{analyse} · téléchargements de séquences ~{download} · "
        "préchauffage unique {kalt}",
    "lernwizard.wizard.dauer_gesamt": "total ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Seuils (modifiables dans Paramètres avancés)",
    "lernwizard.wizard.frage":
        "Apprendre à partir de l'ensemble des {n} événements&nbsp;? "
        "Durée estimée ~{gesamt} (analyse {analyse} + téléchargements "
        "{download}). La session peut être interrompue à tout moment.",
    "lernwizard.wizard.fps_titel": "Images analysées par seconde",
    "lernwizard.wizard.knopf_start": "Créer cette session",
    "lernwizard.seg.vorbereiten": "Préparer",
    "lernwizard.seg.sammeln": "Collecter les visages",
    "lernwizard.seg.sortieren": "Trier en groupes",
    "lernwizard.status.laeuft_seit": "en cours depuis {dauer}",
    "lernwizard.status.rest": "{rest} restant",
    "lernwizard.status.fertig_in": "terminé en {dauer}",
    "lernwizard.status.aufnahmen": "enregistrements&nbsp;: {n}",
    "lernwizard.status.bilder": "{n} photos collectées jusqu'ici",
    "lernwizard.puls.working": "en cours — mis à jour il y a {s}s",
    "lernwizard.puls.stumm":
        "aucune mise à jour depuis {s}s — une longue séquence peut "
        "prendre des minutes&nbsp;; si cela continue de croître, "
        "consultez /log",
    "lernwizard.zeile.kaputt": "{n} lignes illisibles comptées",
    "lernwizard.zeile.anker_link": "voir les {n} groupes d'ancrage",
    "lernwizard.ergebnis.bilder.eins": "{n} photo collectée",
    "lernwizard.ergebnis.bilder.viele": "{n} photos collectées",
    "lernwizard.ergebnis.aufnahmen.eins": "depuis {n} enregistrement",
    "lernwizard.ergebnis.aufnahmen.viele": "depuis {n} enregistrements",
    "lernwizard.ergebnis.gruppen.eins": "triées en {n} groupe",
    "lernwizard.ergebnis.gruppen.viele": "triées en {n} groupes",
    "lernwizard.ergebnis.beiseite": "({n} écartées)",
    "lernwizard.kachel.lauf": "Session d'apprentissage",
    "lernwizard.kachel.sammeln": "Collecter &amp; trier",
    "lernwizard.kachel.benennen": "Nommer les groupes",
    "lernwizard.kachel.fertig": "Terminé &mdash; elles comptent",
    "lernwizard.such.titel": "Chercher des visages dans les événements",
    "lernwizard.such.klein": "remonte dans vos enregistrements",
    "lernwizard.pop.satz":
        "Remonte dans vos enregistrements et collecte les visages. Au "
        "quotidien, le système continue d'apprendre tout seul.",
    "lernwizard.pop.label_letzte": "Remonter les",
    "lernwizard.pop.wort_events": "derniers événements",
    "lernwizard.pop.hint_n":
        "combien d'enregistrements récents vérifier (jusqu'à {max})",
    "lernwizard.pop.label_tag": "Une journée entière&nbsp;:",
    "lernwizard.pop.hint_tag":
        "chaque enregistrement de ce jour, quel qu'en soit le nombre",
    "lernwizard.pop.wort_fps": "images par seconde",
    "lernwizard.pop.hint_fps":
        "plus d'images trouvent plus d'angles, mais la recherche dure "
        "plus longtemps",
    "lernwizard.pop.label_skip": "Ignorer les événements déjà parcourus",
    "lernwizard.pop.hint_skip":
        "chaque recherche remonte plus loin dans le passé &mdash; "
        "décochez pour parcourir à nouveau les événements les plus "
        "récents",
    "lernwizard.pop.alle_gesichter": "Tous les visages",
    "lernwizard.pop.eine_person": "Une seule personne&nbsp;:",
    "lernwizard.pop.hint_person":
        "avec une personne choisie, les groupes correspondants sont "
        "listés en premier &mdash; rien n'est masqué",
    "lernwizard.pop.knopf_start": "Lancer la recherche",
    "lernwizard.knopf_abbrechen": "Annuler",
    "lernwizard.k1.unbekannt.eins":
        "{n} visiteur inconnu d'aujourd'hui&nbsp;:",
    "lernwizard.k1.unbekannt.viele":
        "{n} visiteurs inconnus d'aujourd'hui&nbsp;:",
    "lernwizard.k1.gestartet": "Session démarrée {wann}",
    "lernwizard.k1.scope": "étendue {n} événements",
    "lernwizard.k1.tag": "jour {tag}",
    "lernwizard.k2.satz":
        "Tourne toute seule &mdash; vous pouvez fermer cette page et "
        "revenir.",
    "lernwizard.k2.knopf_abort": "Interrompre la session",
    "lernwizard.k3.satz_warten":
        "La seule étape qui a besoin de vous&nbsp;: un groupe doit être "
        "une seule personne &mdash; dites qui c'est, ou passez-le.",
    "lernwizard.k3.keine_gesichter":
        "Aucun nouveau visage cette fois &mdash; rien à nommer. Ce n'est "
        "pas grave&nbsp;: cela signifie simplement que les "
        "enregistrements ne contenaient personne de nouveau.",
    "lernwizard.knopf_neuer_lauf": "Démarrer une nouvelle session",
    "lernwizard.k3.gruppe_offen":
        "Le groupe en cours est ouvert ci-dessous, en pleine largeur.",
    "lernwizard.k3.alle_erledigt": "Tous les groupes sont traités.",
    "lernwizard.chip.bilder": "{n} photos",
    "lernwizard.k3.verworfen.eins":
        "{n} groupe écarté (aucun visage exploitable ou par vous) "
        "&middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} groupes écartés (aucun visage exploitable ou par vous) "
        "&middot;",
    "lernwizard.k3.link_einsehen": "voir",
    "lernwizard.k3.done_weiter":
        "{erledigt} sur {gesamt} traités &mdash; le suivant est prêt.",
    "lernwizard.k3.done_punkt": "{erledigt} sur {gesamt} traités.",
    "lernwizard.k3.wartend.eins": "{n} groupe vous attend.",
    "lernwizard.k3.wartend.viele": "{n} groupes vous attendent.",
    "lernwizard.k4.adopt_bilder.eins": "{n} photo intégrée pour",
    "lernwizard.k4.adopt_bilder.viele": "{n} photos intégrées pour",
    "lernwizard.k4.adopt_personen.eins": "{n} personne",
    "lernwizard.k4.adopt_personen.viele": "{n} personnes",
    "lernwizard.k4.zaehlen_sofort":
        "elles comptent immédiatement pour la reconnaissance.",
    "lernwizard.k4.link_qs":
        "vérifier la qualité de la bibliothèque &#8230;",
    "lernwizard.k4.nichts":
        "aucune nouvelle photo intégrée cette fois (groupes passés ou "
        "déjà couverts).",
    "lernwizard.k4.wiederholen":
        "Répétez à quelques jours d'intervalle, ou laissez la vue du "
        "jour compléter les personnes connues entre-temps.",
    "lernwizard.k4.knopf_faces": "Retour à Visages",
    "lernwizard.k4.hinweis":
        "Les photos nommées deviennent des références et comptent "
        "immédiatement pour la reconnaissance.",
    "lernwizard.zw.grund_maessig": "qualité de photo seulement moyenne",
    "lernwizard.zw.attr_clip": "ouvrir la séquence",
    "lernwizard.blick.links": "Regard vers la gauche",
    "lernwizard.blick.frontal": "De face",
    "lernwizard.blick.rechts": "Regard vers la droite",
    "lernwizard.blick.leer":
        "aucune photo exploitable sous cet angle dans le groupe",
    "lernwizard.blick.legende":
        "({gut} bonnes, {grenz} limites sur {n} vérifiées)",
    "lernwizard.zw.titel":
        "Groupe {pos} sur {gesamt} &mdash; qui est-ce&nbsp;?",
    "lernwizard.zw.satz":
        "Un groupe doit être une seule personne. Touchez une photo pour "
        "l'exclure &mdash; puis dites qui c'est, ou passez le groupe.",
    "lernwizard.bekannt.system": "déjà dans votre système",
    "lernwizard.bekannt.anker": "nommé sur un autre groupe",
    "lernwizard.zw.knopf_adopt": "Intégrer comme {name}",
    "lernwizard.zw.knopf_ja": "Oui, c'est {name}",
    "lernwizard.zw.fehler":
        "la vérification des photos n'a pas pu s'exécuter (voir /log) "
        "&mdash; rechargez pour réessayer&nbsp;; Passer et Supprimer "
        "fonctionnent toujours.",
    "lernwizard.zw.warte":
        "vérification des photos de ce groupe par rapport à la barre de "
        "référence &mdash; quelques secondes &hellip;",
    "lernwizard.zw.knopf_andere": "Quelqu'un d'autre &#8230;",
    "lernwizard.zw.attr_name": "nom de la personne (nouvelle ou existante)",
    "lernwizard.zw.knopf_save": "Enregistrer le nom",
    "lernwizard.zw.knopf_skip": "Passer ce groupe",
    "lernwizard.zw.frage_delete":
        "Supprimer ce groupe&nbsp;? Ses photos sont supprimées et un "
        "nommage en attente est abandonné&nbsp;; le groupe reste "
        "mémorisé pour que les prochaines collectes des mêmes événements "
        "restent silencieuses.",
    "lernwizard.zw.knopf_delete": "Supprimer ce groupe",
    "lernwizard.zw.link_detail": "vue détaillée complète",
    "lernwizard.zw.detail_zusatz":
        "(toutes les photos avec raisons, sélection experte)",
    "lernwizard.erfolg.titel": "Regroupement terminé",
    "lernwizard.erfolg.cluster.eins":
        "{n} groupe de visages prêt&nbsp;:",
    "lernwizard.erfolg.cluster.viele":
        "{n} groupes de visages prêts&nbsp;:",
    "lernwizard.erfolg.knopf_anker": "Voir les groupes d'ancrage",
    "lernwizard.erfolg.hinweis": "ouvrez un groupe pour le nommer",
    "lernwizard.expert.phasen_titel": "Phases",
    "lernwizard.expert.phasen_hinweis":
        "Préparation, Collecte, Regroupement, Nommage et intégration "
        "dans le Master s'exécutent réellement dans cette version — les "
        "vues de profil et les références corps entier s'activeront avec "
        "les prochaines mises à jour.",
    "lernwizard.expert.progress_titel": "Progression",
    "lernwizard.expert.anker_bisher": "points d'ancrage jusqu'ici&nbsp;: {n}",
    "lernwizard.expert.progress_rest":
        "créée {wann} · étendue {n} événements · survit aux redémarrages "
        "(reprise intégrée)",
    "lernwizard.expert.lauf_bleibt":
        "cette session reste — ses points d'ancrage demeurent disponibles",
    # --------------------------------- Stufe 1: Einhang/Skelett (webui) ---
    "nav.bereich.activity": "Passages",
    "nav.bereich.faces": "Visages",
    "nav.bereich.learn": "Apprentissage",
    "nav.bereich.person": "Personne",
    "nav.bereich.vision": "Vision",
    "nav.bereich.live": "En direct",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Configuration",
    "nav.bereich.erkennungstest": "Test de reconnaissance",
    "nav.bereich.system": "Système",
    "nav.heute": "Aujourd'hui",
    "nav.ereignisse": "Événements",
    "nav.offen": "À étiqueter",
    "nav.faces": "Visages",
    "nav.gesichter": "Connus",
    "nav.unbekannte": "Inconnus",
    "nav.qualitaet": "Qualité",
    "nav.lernlauf": "Session d'apprentissage",
    "nav.anker": "Points d'ancrage",
    "nav.lernen": "Suggestions",
    "nav.person": "Images de corps",
    "nav.person_kontrolle": "Images évaluées",
    "nav.person_modell": "État du modèle",
    "nav.personlauf": "Apprentissage de la personne",
    "nav.vision": "Détection par vision",
    "nav.live": "Surveillance en direct",
    "nav.live_alerts": "Alertes en direct",
    "nav.erkennung": "Reconnaissance",
    "nav.kameras": "Caméras",
    "nav.benachrichtigungen": "Notifications",
    "nav.areas": "Secteurs",
    "nav.kette": "Chaîne de reconnaissance",
    "nav.konfiguration": "Avancé",
    "nav.erkennungstest": "Test de reconnaissance",
    "nav.system": "Système",
    "nav.sync_auswahl": "Synchronisation Frigate",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Journal du service",
    "ui.fuss.docs": "Documentation",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip": "Easy affiche les pages essentielles — Expert affiche tout. Rien n'est supprimé, Easy ne fait que masquer.",
    "ui.live.chip": "En direct",
    "ui.theme.knopf": "Thème",
    "ui.theme.tooltip": "Basculer entre clair et sombre",
    "ui.theme.aria": "Changer de thème de couleur",
    "ui.sprache.tooltip": "Langue de cette installation — s'applique à toutes les pages et aux notifications",
    "ui.upd.link": "mise à jour {tag}",
    "ui.upd.tooltip": "Une version plus récente de suslik est disponible sur GitHub",
    "ui.upd.titel": "Mise à jour disponible",
    # ui.upd.satz ist der erste deklarierte t_html-Schluessel (HTML_SCHLUESSEL,
    # core/sprache.py) — Tag-Folge muss in jeder Sprache identisch sein.
    "ui.upd.satz": "Une image suslik plus récente (<b>{tag}</b>) est sur GitHub — <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">notes de version</a>. Récupérer la nouvelle image et redémarrer pour mettre à jour ; les données et les paramètres sont conservés.",
    "ui.wn.titel": "Nouveautés",
    "ui.wn.x_tooltip": "Masquer jusqu'à la prochaine version",
    "ui.wn.x_aria": "Fermer",
    "ui.wn.mehr": "Tout afficher ({n})",
    "ui.wn.weniger": "En afficher moins",
    "ui.hinweis.englisch": "Cette page n'est pas encore traduite — son contenu reste pour l'instant en anglais.",
    # --------------------------------- Stufe 1: Seitentitel (verifyd) ---
    "titel.setup": "Assistant d'installation",
    "titel.anker_detail": "Point d'ancrage",
    "titel.aehnliche": "Visages correspondants",
    "titel.live_kamera": "En direct — {kamera}",
    "titel.video": "Vidéo",
    "titel.event": "Événement",
    "titel.vision_galerie": "Composer une galerie",
    "titel.hilfe": "Comment ça marche",
    # --------------------------------- Stufe 1: Setup-Wizard Schritt 0 ---
    "setup.sprache.titel": "Langue",
    "setup.sprache.satz": "Choisir la langue de cette installation — elle s'applique immédiatement, notifications comprises. Modifiable à tout moment via le sélecteur de l'en-tête.",
    # --------------------------------- Stufe 1: js.* (window.T, app.js) ---
    # VERTRAG: app.js liest NUR js.*-Schluessel (TT() mit EN-Fallback ==
    # diesem Wert); jede Richtung prueft die Gate-Stufe Sprach-Deckung.
    "js.status.fehler": "erreur",
    "js.status.fehler_gross": "Erreur",
    "js.status.fehler_detail": "erreur : {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "enregistrement …",
    "js.status.gespeichert": "enregistré",
    "js.status.senden": "envoi …",
    "js.status.starten": "démarrage …",
    "js.status.laeuft": "en cours …",
    "js.status.laeuft_wort": "en cours",
    "js.status.pruefen": "vérification …",
    "js.status.suchen": "recherche …",
    "js.status.lernen": "apprentissage …",
    "js.status.hinzufuegen": "ajout …",
    "js.status.entfernen": "retrait …",
    "js.status.loeschen": "suppression …",
    "js.status.hochladen": "téléversement …",
    "js.status.wiederherstellen": "restauration …",
    "js.status.ueberspringen": "mise à l'écart …",
    "js.status.siehe_log": "voir le journal du service",
    "js.status.diagnose": "diagnostic",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Annuler",
    "js.neustart.zurueck": "Le service est revenu, chargement …",
    "js.neustart.kommt": "Le service revient …",
    "js.neustart.gespeichert": "Enregistré. Le service redémarre, patientez …",
    "js.neustart.warten": "Le service redémarre, patientez …",
    "js.konfig.frage": "Enregistrer la configuration et redémarrer le service ?",
    "js.lernlauf.fps_zeile": "≈ total ~{dauer} à {fps}/s",
    "js.lernlauf.tag_fehlt": "choisir d'abord un jour",
    "js.lernlauf.abbruch_frage": "Interrompre cette session d'apprentissage ?",
    "js.notif.frage": "Enregistrer les paramètres de notification et redémarrer le service ?",
    "js.frigate.ro_frage": "Passer en LECTURE SEULE ? suslik cessera d'écrire dans Frigate.",
    "js.frigate.rw_frage": "Activer l'ÉCRITURE dans Frigate (sub_labels + synchronisation des références) ?",
    "js.restore.frage": "Restaurer la configuration depuis \"{name}\" ? Cela écrase les paramètres actuels et redémarre le service.",
    "js.vollrestore.frage": "Restaurer la sauvegarde COMPLÈTE \"{name}\" ? Cela remplace les paramètres, les références et tout le matériel appris, puis redémarre le service.",
    "js.vollrestore.laeuft": "téléversement + restauration … (les gros fichiers prennent du temps)",
    "js.enroll.fehler": "Erreur : {msg}",
    "js.enroll.person_fehlt": "Choisir une personne ou en saisir une nouvelle.",
    "js.upload.fehlt": "Choisir une personne (liste ou nouvelle) et un fichier.",
    "js.upload.trotzdem": "{msg}\n\nAjouter quand même ?",
    "js.anlernen.frage": "Ajouter le groupe comme \"{person}\" (les meilleures images deviennent des références) ?",
    "js.anlernen.name_frage": "Nom de la nouvelle personne :",
    "js.anlernen.person_fehlt": "Choisir une personne existante.",
    "js.auswahl.gesicht_fehlt": "Cocher au moins un visage.",
    "js.auswahl.bild_fehlt": "Sélectionner au moins une image.",
    "js.vorschlag.keine": "Aucun visage recommandé.",
    "js.vorschlag.alle_frage": "Ajouter les {n} visages recommandés à {person} ? Ils deviennent aussitôt des références.",
    "js.vorschlag.frage": "Ajouter {n} visage(s) à {person} ?",
    "js.sync.frage": "Synchroniser : {richtung} ?",
    "js.sync.modell_laedt": "chargement du modèle …",
    "js.sync.fortschritt": "{done}/{total} visages ({current}) {pct} %",
    "js.sync.fertig": "terminé : {ok} ok, {gate} ignorés — rechargement …",
    "js.sync.fehler": "échec de la synchronisation : {grund}",
    "js.syncauswahl.knopf": "Transférer les {n} images sélectionnées vers Frigate",
    "js.syncauswahl.nichts": "Aucune sélection",
    "js.syncauswahl.nichts_klein": "aucune sélection",
    "js.syncauswahl.skip": "ignorer",
    "js.syncauswahl.restore": "rétablir",
    "js.syncauswahl.wieder": "proposer à nouveau",
    "js.syncauswahl.zurueck_laeuft": "remise en place …",
    "js.syncauswahl.frage": "Envoyer {n} image(s) de référence vers Frigate ?",
    "js.syncauswahl.fehl_knopf": "échec du transfert",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct} %",
    "js.syncauswahl.fertig": "terminé : {ok} téléversées, {gate} refusées — rechargement …",
    "js.syncauswahl.fehler": "échec du transfert : {grund}",
    "js.vorpruef.haengt": "la vérification préalable semble bloquée — recharger la page pour réessayer",
    "js.vorpruef.laeuft": "vérification des images … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "échec de la vérification préalable : {grund}",
    "js.vorpruef.fertig": "vérification préalable terminée — rechargement …",
    "js.import.fortschritt": "téléchargement {done}/{total} ({current}) {pct} %",
    "js.import.fertig_wiz": "✓ {n} importés — calcul des caractéristiques sur l'accélérateur …",
    "js.import.knopf_fertig": "Importés ✓",
    "js.import.fehler": "échec de l'importation : {grund}",
    "js.import.knopf": "Importer les visages",
    "js.import.knopf_ges": "Importer les visages depuis Frigate",
    "js.import.fertig_ges": "✓ {n} importés — calcul des caractéristiques, la page se recharge …",
    "js.ref.frage": "Retirer l'image de référence de {person} ?",
    "js.ref.batch_frage": "Supprimer {n} image(s) ?",
    "js.dienst.nicht_erreichbar": "service injoignable — réessayer dans un instant.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage": "Ignorer comme visiteur inconnu habituel ? Il ne déclenchera plus d'alertes. (Réactivable à tout moment ci-dessous, dans \"known visitors\".)",
    "js.unb.ziel_fehlt": "Choisir une identité cible.",
    "js.unb.merge_frage": "Fusionner ?",
    "js.unb.name_fehlt": "Saisir un nom (personne nouvelle ou existante).",
    "js.unb.benennen_frage": "Attribuer à \"{person}\" ? Les meilleures images deviennent des références.",
    "js.person.loesch_frage": "Supprimer TOUTES les références et le nom \"{person}\" ?\nLes images vont dans le dossier corbeille (récupérables).\n\nSaisir le nom pour confirmer :",
    "js.person.name_falsch": "Le nom ne correspond pas — rien n'a été supprimé.",
    "js.areas.fehl": "échec de l'enregistrement — le service est-il joignable ?",
    "js.areas.name_fehlt": "Saisir d'abord un nom de secteur.",
    "js.areas.existiert": "Ce secteur existe déjà.",
    # js.areas.entfernen_frage: "Default" ist zugleich Kennung der
    # Standard-Area (Anzeige==Kennung §8.2) — bleibt in jeder Sprache.
    "js.areas.entfernen_frage": "Retirer le secteur \"{name}\" ? Ses caméras reviennent à Default — rien d'autre ne change.",
    "js.personlauf.abbruch_frage": "Interrompre cette session d'apprentissage de la personne ? Les images collectées sont conservées.",
    "js.personlauf.verwerfen_frage": "Abandonner complètement la session {lid} ? Toutes ses images sont supprimées ; une nouvelle session peut les collecter à nouveau à tout moment.",
    "js.vision.nicht_erreichbar": "service injoignable — rien n'a été enregistré",
    "js.vision.gespeichert": "enregistré — la reconnaissance utilise désormais cette connexion",
    "js.vision.gespeichert_neustart": "enregistré — le service redémarre dans un instant",
    "js.vision.gespeichert_reload": "enregistré — le service redémarre, la page se recharge dans un instant",
    "js.vision.treffer": "{n}/2 justes",
    "js.vision.tokens": "{ist} tokens contre {soll}",
    "js.vision.dirty_titel": "Cette connexion n'est pas enregistrée",
    # js.vision.dirty_text: "Save" ist der (noch englische) Knopf der
    # Vision-Seite — bleibt woertlich, bis die Seite selbst einzieht.
    "js.vision.dirty_text": "Le test utiliserait les valeurs qui viennent d'être saisies. La reconnaissance continue d'utiliser la connexion ENREGISTRÉE tant que vous n'avez pas cliqué sur Save — un test vert seul ne change rien aux verdicts.",
    "js.vision.dirty_save": "Enregistrer d'abord, puis tester",
    "js.vision.dirty_test": "Tester sans enregistrer",
    "js.vision.stufe1": "accessibilité et modèle",
    "js.vision.stufe2": "grilles de formes à choix forcé",
    "js.vision.stufe3": "nombre de tokens",
    "js.vision.stufe_laeuft": "étape {nr}/3 — {name} … (un modèle local sur CPU peut prendre plusieurs minutes)",
    "js.vision.test_fehl": "le test n'a pas pu être exécuté",
    "js.vision.stufe_stop": "arrêté à l'étape {nr} — voir le journal ci-dessous",
    "js.vision.fertig": "terminé — {ampel}",
    "js.vision.stufe_fehl": "l'étape {nr} n'a pas pu être exécutée",
    "js.vision.neustart_warte": "le service ne répond pas pour le moment — la page se recharge dans un instant",
    "js.vision.prompt_frage": "Rétablir la question dans sa formulation par défaut ?",
    "js.vision.prompt_zurueck": "formulation par défaut rétablie — cliquer sur Save pour l'enregistrer",
    "js.vision.kachel_frage": "Certaines modifications ne sont pas enregistrées. Changer de fournisseur les abandonne. Continuer ?",
    "js.vision.pick": "— choisir —",
    "js.vision.untested": "non testé ici",
    "js.vision.neu_pruefen": "la connexion a changé — la vérifier à nouveau pour voir ses modèles",
    "js.vision.key_laeuft": "interrogation du fournisseur sur les modèles utilisables …",
    "js.vision.key_fehl": "la vérification a échoué",
    "js.vision.key_fehl2": "la vérification n'a pas pu être exécutée",
    "js.rt.start": "lancement de l'analyse par vision …",
    "js.rt.fehl": "l'analyse n'a pas pu démarrer",
    "js.rt.nach_fehl": "le démarrage a échoué",
    "js.vw.geliehen": "de la rangée {reihe}",
    "js.vw.vergessen_frage": "Oublier les images écartées pour cette galerie ? Elles pourront être proposées à nouveau.",
    "js.vw.leer_frage": "{n} case(s) restées vides. Valider quand même la galerie ?",
    "js.vw.kopiert": "copie des images dans la galerie …",
    # js.live.phase_*: Anzeige-Woerter zu den Status-KENNUNGEN des
    # Live-Polls (Status-replace-Mapping, §8-Nachtrag).
    "js.live.phase_verbinden": "Connexion",
    "js.live.phase_messen": "Mesure",
    "js.live.phase_auswerten": "Évaluation",
    "js.live.phase_abbruch": "Interruption",
    "js.live.rest": " — {n} s restantes",
    "js.live.auftrag_zeile": "{art} sur {kamera} : {phase}{rest}{pausiert}",
    "js.live.messung": "Mesure de charge",
    "js.live.quelltest": "Test de la source",
    "js.live.pausiert": " — surveillances en pause pour la mesure ({liste})",
    "js.live.job_laeuft": "test de la source en cours (processus auxiliaire, jusqu'à ~2 minutes) …",
    "js.live.job_ok": "test de la source terminé : {text}",
    "js.live.job_fehl": "test de la source EN ÉCHEC : {text}",
    "js.live.messung_fehl": "échec de la mesure de charge : {grund}",
    "js.live.test_fehl": "échec du test de la source : {grund}",
    # ---- auftritte (Stufe 2, Tranche A) ----
    # Projektroot-Route /heute-Personensicht + /pass/<eid> (auftritte.py);
    # Stufe-2-Grenzen s. en.py-Abschnittskommentar.
    "auftritte.unbek.zaehlung":
        "+{n} sans correspondance (généralement les mêmes personnes)",
    "auftritte.unbek.name": "Inconnu {nummer}",
    "auftritte.unbek.ohne_treffer.eins":
        "{n} événement avec un visage sans correspondance",
    "auftritte.unbek.ohne_treffer.viele":
        "{n} événements avec un visage sans correspondance",
    "auftritte.nav.zurueck_heute": "&#8592; Aujourd'hui",
    "auftritte.unbek.titel": "Inconnu",
    "auftritte.unbek.leer_link": "Ce lien ne renvoie à aucun passage.",
    "auftritte.unbek.leer_weg":
        "Ce passage n'apparaît plus dans la vue du jour.",
    "auftritte.unbek.leer_weg_hinweis":
        "La journée a peut-être été regroupée autrement — rouvrez-la "
        "depuis la page Aujourd'hui.",
    "auftritte.unbek.leer_pool": "Aucun visage collecté pour ce passage.",
    "auftritte.unbek.leer_pool_hinweis":
        "La collecte a peut-être été purgée entre-temps.",
    "auftritte.knopf.video": "vidéo",
    "auftritte.karte.faces.eins": "{n} visage",
    "auftritte.karte.faces.viele": "{n} visages",
    "auftritte.karte.kameras.eins": "{n} caméra",
    "auftritte.karte.kameras.viele": "{n} caméras",
    "auftritte.unbek.mehr_im_lauf": "+{n} de plus dans ce passage",
    "auftritte.unbek.ein_lauf": "un passage",
    "auftritte.zuweisen.titel": "Qui est-ce ?",
    "auftritte.zuweisen.satz":
        "Voici les visages de CE passage. Cochez ceux qui appartiennent "
        "vraiment à la personne &mdash; les rebuts restent écartés. "
        "Donnez-leur un nom (nouveau ou existant) et ils seront "
        "appris ; ne rien faire les laisse inconnus.",
    "auftritte.zuweisen.knopf_alle": "Tout sélectionner",
    "auftritte.zuweisen.knopf_keine": "Aucun",
    "auftritte.zuweisen.attr_person": "personne (nouvelle ou existante)",
    "auftritte.zuweisen.knopf_zuweisen": "Ajouter les visages sélectionnés",
    "auftritte.zuweisen.js_keine": "cochez au moins un visage",
    "auftritte.zuweisen.js_name": "saisissez un nom de personne",
    "auftritte.zuweisen.js_lernt": "apprentissage…",
    "auftritte.zuweisen.js_fehler": "erreur",
    "auftritte.unbek.titel_lauf": "Inconnu {nummer} — passage",
    "auftritte.leer_person": "Personne inconnue.",
    "auftritte.leer_person_hinweis":
        "Choisissez une personne sur la page Aujourd'hui.",
    "auftritte.titel": "Apparitions",
    "auftritte.nav.attr_tag": "retour à la journée",
    "auftritte.nav.attr_vortag": "jour précédent",
    "auftritte.kopf.passzahl.eins": "{n} passage",
    "auftritte.kopf.passzahl.viele": "{n} passages",
    "auftritte.nav.attr_kein_morgen": "aucun jour à venir",
    "auftritte.nav.attr_folgetag": "jour suivant",
    "auftritte.titel_person": "{person} — Apparitions",
    "auftritte.leer_passe":
        "Aucun passage confirmé de {person} ce jour-là.",
    "auftritte.leer_passe_hinweis":
        "Utilisez les flèches pour parcourir les jours.",
    "auftritte.karte.kein_bild": "pas d'image",
    "auftritte.thumb.zusatz_unbestaetigt": " — non confirmé ici",
    "auftritte.thumb.zusatz_referenz": " — dans les références",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} événement sans visage",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} événements sans visage",
    "auftritte.thumb.hinweis_referenz":
        "bordure verte = déjà dans les références",
    "auftritte.karte.best_punkt": "présence confirmée à {zeit}",
    "auftritte.karte.best_spanne":
        "présence confirmée {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "en cours",
    "auftritte.karte.pass_nr": "Passage {n}",
    "auftritte.karte.events.eins": "{n} événement",
    "auftritte.karte.events.viele": "{n} événements",
    "auftritte.karte.best_match": "meilleure correspondance {wert}",
    "auftritte.karte.auch_dabei": "également dans ce passage : {namen}",
    "auftritte.pass.titel": "Passage",
    "auftritte.pass.leer_event": "Événement introuvable.",
    "auftritte.pass.leer_event_hinweis":
        "Il a peut-être disparu du journal avec le temps.",
    "auftritte.pass.leer_gruppe":
        "Cet événement ne fait partie d'aucun passage regroupé.",
    "auftritte.pass.leer_gruppe_hinweis":
        "Le regroupement nécessite le contexte de la vue du jour.",
    "auftritte.nav.zurueck_tag": "&#8592; Jour",
    "auftritte.pass.attr_vor": "passage précédent de la journée",
    "auftritte.pass.attr_nach": "passage suivant de la journée",
    "auftritte.pass.kopf": "Passage {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Sans correspondance",
    "auftritte.pass.label_gt": "Étiquette",
    "auftritte.pass.badge_fremd": "intrusion confirmée",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log ne contient aucune ligne de motif — ouvrez "
        "l'événement pour le journal complet",
    "auftritte.pass.grund_ohne_log":
        "aucun analyze.log conservé pour cet événement — voir le journal "
        "du service",
    "auftritte.pass.label_fehler": "Erreur",
    "auftritte.pass.wer": "Qui",
    "auftritte.pass.titel_zeit": "Passage {zeit} — {tag}",
}
