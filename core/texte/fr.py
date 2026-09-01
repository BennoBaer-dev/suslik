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
    "kameras.steckbrief.knopf": "Rev\u00e9rifier le flux",
    "kameras.steckbrief.hinweis":
        "La r\u00e9solution du flux est relev\u00e9e une fois par cam\u00e9ra puis m\u00e9moris\u00e9e. Utilise ceci si tu as chang\u00e9 le flux d'une cam\u00e9ra ou si l'une est indiqu\u00e9e comme injoignable.",
    "kameras.steckbrief.stand": "{n} sur {ges} cam\u00e9ra(s) relev\u00e9e(s), {fehler} injoignables",
    "kameras.steckbrief.laeuft": "v\u00e9rification \u2026",
    "kameras.steckbrief.fertig": "sera relev\u00e9 au prochain red\u00e9marrage",
    "readme.einleitung": "J'ai écrit ceci parce que ces questions revenaient sans cesse.",
    "readme.kontakt": 'Vos retours sont les bienvenus :',
    "readme.titel": "À lire d'abord",
        "readme.knopf": "À lire d'abord",
        "readme.schliessen": 'Fermer',
    "readme.zurueck": 'Retour',
        "readme.fuss": 'Ce texte apparaît une fois après chaque redémarrage.',
        "readme.inhalt": 'Sommaire',
        "readme.generell.titel": 'Généralités',
    "readme.generell.text": "Ma détection de scénario repose sur la détection de personne de Frigate. Dès que Frigate signale une personne, je récupère tout l'événement personne. Un tel événement dure parfois quelques secondes, parfois plusieurs minutes. Je le parcours en entier pour y trouver toutes les personnes.\n\nQue la reconnaissance faciale de Frigate soit activée n'a pas d'importance. Elle ne sert que si vous voulez synchroniser les visages avec Frigate.\n\nLa vérification n'utilise jamais le flux de détection, mais l'enregistrement, c'est-à-dire le meilleur flux que la caméra fournit à Frigate.\n\nUne vérification démarre de deux façons. Soit par l'événement personne de Frigate, c'est la voie du passage. Soit par la veille en direct : elle prend le flux en cours, directement de la caméra ou via le proxy de Frigate, y cherche des visages et démarre à partir de là.\n\nUne personne est reconnue par trois voies. Par le visage. Par la personne entière, à partir de l'image seule, sans visage. Par un modèle de vision, et cette voie est encore en bêta.\n\nJ'utilise ici des caméras 4K avec la fréquence d'images la plus élevée possible, au moins 15 images par seconde. Le débit aussi haut que possible. Un débit faible rend flous les visages en mouvement.",
    "readme.aktuell.titel": 'Ce sur quoi je travaille',
    "readme.aktuell.text": "Un bouton de calibrage. Les flux des caméras sont très différents, et avec eux la netteté et la reconnaissance. Le calibrage doit compenser cela.\n\nLa reconnaissance par modèle de vision : identifier une personne quand le visage n'est pas visible. C'est en bêta et cela doit s'améliorer.\n\nDétection de présence : enregistrer si une personne connue est là ou non. D'autres systèmes peuvent s'y raccorder, une alarme par exemple, ou un pointage horaire.",
    "readme.lernen.titel": "Comment j'apprends de nouveaux visages ?",
    "readme.lernen.text": "Voici comment j'apprends avec mon système :\n\nApprentissage du visage. La première chose sur un nouveau système. Selon le matériel, les 500 derniers événements, 1000 avec de la marge. Le programme récupère les événements personne, les regroupe et réunit les images. Les connus, il les attribue lui-même. Les inconnus, il les rassemble en groupe, et je donne un nom au groupe. Cela donne la base. Ne s'applique qu'aux visages qui ont été correctement reconnus.\n\nAujourd'hui. Une fois la base en place, ce qui s'ajoute vient d'ici : cliquer sur un événement ou une personne, intégrer le visage.\n\nConnus. Choisir la personne, laisser le programme trouver les visages correspondants.\n\nApprentissage de la personne. Il existe en parallèle, pour les personnes dont le visage n'est pas lisible. J'écrirai plus tard à ce sujet.\n\nQualité. Cet onglet, je l'utilise régulièrement. Il montre à quel point les images d'une personne sont vraiment bonnes, lesquelles sont trop faibles et lesquelles se recoupent avec une autre personne. Celles qui se ressemblent trop, je les enlève.\n\nL'onglet Inconnus est encore là, il vient d'une version antérieure. Je ne l'utilise pas.",
    "readme.persoenlich.titel": 'Personnel',
    "readme.persoenlich.text": "C'est purement un loisir. En tant qu'architecte informatique senior, j'ai plaisir à développer quelque chose avec l'IA. Le tout est développé avec Claude Code, principalement avec Fable 5, et avec Opus 5 pour les agents.\n\nCe que je souhaite, ce sont des retours, et cela me fait plaisir quand quelqu'un utilise le système. C'est ma paie.",
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
    "aehnliche.vorrat.titel": "Nouveautés du stock d'apprentissage",
    "aehnliche.vorrat.hinweis":
        "Visages de haute qualité collectés par la passe d'apprentissage, "
        "évalués par la mesure de qualité sans références et le consensus "
        "du scénario. Ils restent en local et ne sont jamais exportés vers Frigate.",
    "aehnliche.vorrat.kachel_zeile": "{wann} · {kamera} · correspondance {sim} · qualité {norm}",
    "aehnliche.vorrat.auch_anker": "aussi dans un groupe de visages",
    "aehnliche.vorrat.knopf_gewaehlt": "Appliquer la sélection à {person}",
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
    "ereignisliste.tabelle.attr_kein_crop":
        "aucun visage exploitable n'a été conservé pour cet événement",
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
    "antwort.support_token_neu": "nouveau token de support cree — l'ancien n'est plus valable ; copiez-le maintenant, il n'est montre que cette fois",
    "konfiguration.neustart.titel": "Redémarrer le service",
    "konfiguration.neustart.satz": "Redémarre ce service sur place (le conteneur continue de tourner, toutes les données restent). À utiliser quand le traitement semble bloqué ; les événements en attente sont repris après le redémarrage.",
    "konfiguration.neustart.knopf": "Redémarrer maintenant",
    "konfiguration.neustart.frage": "Redémarrer le service maintenant ? Le traitement s'interrompt quelques secondes.",
    "antwort.neustart": "Redémarrage en cours — cette page répond de nouveau dans quelques secondes.",
    "konfiguration.support.titel": "Acces support a distance",
    "konfiguration.support.satz": "Telechargement en lecture seule de zones nommees (logs, config masquee, visages, passes d'apprentissage, materiel corporel, fichiers d'etat) pour le detenteur du token de support. L'interrupteur support_zugriff se trouve dans le tableau ci-dessous, desactive par defaut. Chaque requete est ecrite dans le log du service. Les zones visages et corps contiennent des images de personnes reelles — remettez le token avec prudence. Sans TLS devant ce service, le token circule en clair. Depuis 0.1.0.395 le jeton permet aussi une action : redemarrer ce service a distance (POST /support/restart).",
    "konfiguration.support.token_gesetzt": "Un token de support est defini.",
    "konfiguration.support.token_fehlt": "Pas encore de token de support.",
    "konfiguration.support.knopf_token": "Creer un nouveau token",
    "konfiguration.support.einmal_hinweis": "Le token apparait ici exactement une fois apres sa creation — conservez-le ; ensuite seul ••• est affiche.",
    "konfiguration.titel": "Paramètres avancés",
    "konfiguration.kopf.satz1":
        "Les modifications sont journalisées (config_audit.jsonl)&nbsp;; "
        "après l'enregistrement, le service redémarre proprement (il "
        "attend la fin d'une analyse en cours).",
    "konfiguration.feld.option_an": "activé",
    "konfiguration.feld.option_aus": "désactivé",
    "konfiguration.frigate_auth.titel": "Connexion \u00e0 Frigate (facultatif)",
    "konfiguration.frigate_auth.satz":
        "N\u00e9cessaire uniquement si votre Frigate demande une connexion \u2014 c'est le cas "
        "sur son port authentifi\u00e9 (8971), pas sur le port interne (5000). Si vous "
        "laissez les deux champs vides, rien ne change : suslik parle \u00e0 Frigate "
        "exactement comme aujourd'hui.",
    "konfiguration.frigate_auth.erkl_user":
        "nom d'utilisateur d'un compte Frigate. Vide = aucune connexion ; le vider "
        "efface aussi le mot de passe enregistr\u00e9",
    "konfiguration.frigate_auth.erkl_password":
        "mot de passe de ce compte. Il est enregistr\u00e9 avec vos autres r\u00e9glages dans "
        "/data et n'est jamais r\u00e9affich\u00e9 \u2014 laissez le champ vide pour le conserver",
    "konfiguration.frigate_auth.erkl_tls":
        "v\u00e9rifier le certificat TLS de Frigate. Le port authentifi\u00e9 de Frigate est "
        "livr\u00e9 avec un certificat auto-sign\u00e9 : d\u00e9sactivez ceci si vous l'atteignez en "
        "https sans avoir remplac\u00e9 ce certificat",
    "konfiguration.frigate_auth.pw_gesetzt": "enregistr\u00e9 \u2014 laissez vide pour le conserver",
    "konfiguration.frigate_auth.pw_leer": "aucun mot de passe enregistr\u00e9",
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
        "supprimé par vous — les images ont disparu&nbsp;; le groupe ne reste qu’à titre d’enregistrement",
    "lernanker.detail.dublette_hinweis":
        "vérification des doublons indisponible (le point d'ancrage "
        "précède la persistance des embeddings) — les doublons physiques "
        "sont tout de même filtrés",
    "lernanker.bekannt.system": "déjà dans votre système",
    "lernanker.bekannt.anker": "nommé sur un autre groupe",
    "lernanker.detail.empfohlen": "Recommandés — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Non recommandés ({n}) — laissés visibles, raison sur chaque image",
    "lernanker.detail.gewaehlt": "Sélectionnés — {bin} ({n})",
    "lernanker.detail.nicht_gewaehlt":
        "Non sélectionnés ({n}) — laissés visibles",
    "lernanker.grund.bildpruefung": "n'a pas passé le contrôle de l'image",
    "lernanker.grund.zu_dunkel":
        "trop sombre (luminosité {luma} — il faut {min}+)",
    "lernanker.grund.ueberbelichtet":
        "surexposé (luminosité {luma} — {max} au maximum)",
    "lernanker.grund.dublette_phys":
        "détection en double (même caméra et même cadre)",
    "lernanker.grund.fast_gleich": "quasi identique à {datei}",
    "lernanker.grund.bin_limit":
        "limite par perspective atteinte ({k} conservés)",
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
        "{n} groupe(s) supprimé(s) par vous (images effacées, conservés à titre d’enregistrement)",
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
        "Supprimer ce groupe&nbsp;? Ses images sont effacées. Cette action est irréversible.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Supprimer ce groupe&nbsp;? Ses images sont effacées et le nommage en attente est abandonné. Cette action est irréversible.",
    "lernanker.liste.knopf_verwerfen": "Supprimer",
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
    "syncauswahl.bilanz.vorrat": "{n} référence(s) du stock en local uniquement (basées sur l'embedding, non transférables)",
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
    "live.test.veraltet_bitte":
        "Ce contrôle a {tage} jours — relance le test de source pour que les "
        "chiffres décrivent ce que la caméra livre aujourd\u2019hui.",
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
    "live.hoehe.alt_hinweis":
        "Enregistré : {alt}p. Ce palier n\u2019existe plus (mesuré : aucun "
        "gain par rapport au {jetzt}p) — cette surveillance tourne en "
        "{jetzt}p. La valeur enregistrée et le test de source restent "
        "valables ; choisis un palier ci-dessus pour changer.",
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
    # --- Live-Umbau 31.08. (s. en.py)
    "live.detail.kein_bild": "Pas d\u2019image en direct — cette surveillance ne tourne pas.",
    "live.detail.kein_bild_test":
        "Le dernier test de source a vu {aufloesung}, traité en {skala}.",
    "live.detail.kein_bild_ohne_test":
        "Aucun test de source n\u2019a encore tourné, on ne sait donc rien de "
        "ce flux.",
    "live.abschnitt.erkennung": "Reconnaissance",
    "live.abschnitt.melden": "Alertes",
    "live.abschnitt.frigate": "Événements Frigate",
    "live.abschnitt.erweitert": "Réglages avancés",
    "live.abschnitt.abtastung": "Échantillonnage",
    "live.abtastung.schalter": "Regarder de près seulement quand ça bouge",
    "live.abtastung.erklaerung":
        "La détection de visages est la partie coûteuse — un contrôle de "
        "mouvement bon marché sur le plan de luminance décide si une image en "
        "vaut la peine. Tant qu\u2019une personne est suivie, la surveillance "
        "tourne toujours à plein régime ; seule une scène calme est "
        "échantillonnée moins souvent.",
    "live.abtastung.ruhe_label": "Regarder quand même toutes les",
    "live.abtastung.ruhe_einheit": "s",
    "live.abtastung.ruhe_hinweis":
        "Laisse vide pour reprendre le délai de fin d\u2019apparition de cette "
        "caméra — quelqu\u2019un d\u2019immobile ne crée aucun mouvement, la "
        "surveillance jette donc un œil de temps en temps (1–600 s).",
    "live.abtastung.schwelle_label": "Sensibilité (variation de gris)\u00a0:",
    "live.abtastung.flaeche_label": "surface minimale\u00a0:",
    "live.abtastung.eich_hinweis":
        "Laisse les deux vides pour les valeurs d\u2019origine de Frigate. Des "
        "chiffres plus bas font regarder la surveillance plus souvent\u00a0; "
        "plus haut, elle reste calme devant une haie dans le vent. Chaque "
        "site est différent — ces valeurs appartiennent à CETTE caméra, pas "
        "au système entier.",
    "live.abschnitt.guete": "Seuils de qualité d\u2019image",
    "live.abschnitt.last": "Mesure de charge",
    "live.erkennung.det_zeile":
        "À partir d\u2019un score de détection de {wert}, une trouvaille "
        "compte comme un visage{marke}.",
    "live.erkennung.det_vorgabe": " (par défaut)",
    "live.erkennung.fenster_vor": "Fenetre de decision :",
    "live.erkennung.fenster_nach": "s — d'abord recueillir les votes, puis annoncer le meilleur nom",
    "live.erkennung.fenster_hinweis": "Des le premier candidat, le guetteur attend ce delai puis annonce le candidat avec le plus de votes, au lieu du premier au-dessus de la barre. 0 = annoncer immediatement (comportement jusqu'a 0.1.0.395).",
    "live.erkennung.regel_vor": "Reconnu après",
    "live.erkennung.regel_mitte": "confirmations en",
    "live.erkennung.regel_nach": "secondes",
    "live.erkennung.regel_hinweis":
        "0 seconde signifie que tout le passage compte, comme jusqu\u2019ici. "
        "Une fenêtre de temps aide sur les caméras où quelqu\u2019un reste "
        "planté plusieurs minutes et où deux coups de chance très espacés ne "
        "devraient pas valoir une reconnaissance.",
    "live.erkennung.vorrat_zeile":
        "Échantillons de calibrage : {n} sur {deckel} \u2014 une image par "
        "passage, les plus anciennes disparaissent.",
    "live.erkennung.vorrat_aus":
        "La collecte est désactivée, la page de calibrage n\u2019a donc rien "
        "à montrer (page Système, \"live_kalib_max\").",
    "live.erkennung.latte_e": "impression d\u2019image à partir de {wert}",
    "live.erkennung.latte_t": "lisibilité du visage à partir de {wert}",
    "live.erkennung.latte_aus": "non défini",
    "live.erkennung.latte_hinweis":
        "Ces deux-là ne décident jamais QUI est reconnu, cela coûterait des "
        "confirmations. Ils décident quelle image part dans l\u2019alerte et "
        "quels visages sont gardés comme échantillons. On les règle sur la "
        "page de calibrage, où l\u2019on voit les images.",
    "live.knopf_kalibrieren": "Calibrer",
    "live.knopf_vorrat_leeren": "Effacer les échantillons",
    "live.frigate.schalter": "Créer un événement Frigate quand quelqu\u2019un est reconnu",
    "live.frigate.erklaerung":
        "Désactivé par défaut. Activé, ce veilleur écrit son propre événement "
        "dans Frigate, le nom dans le sous-libellé \u2014 un enregistrement "
        "à lui, indépendant de la détection de Frigate. L\u2019écriture se "
        "fait en arrière-plan : le veilleur n\u2019attend jamais Frigate. En "
        "mode lecture seule, rien n\u2019est écrit.",
    "live.frigate.abstand_label": "Au plus un événement par personne toutes les (s) :",
    "live.frigate.abstand_hinweis":
        "Vide signifie : le même écart que ci-dessus pour les alertes. La "
        "limite compte par personne, deux personnes différentes peuvent donc "
        "être écrites en même temps.",
    "livekalib.titel": "Calibrage de la caméra — {name}",
    "livekalib.erklaerung":
        "Ce sont de vrais visages que cette caméra a collectés \u2014 une "
        "image par passage. Déplace les curseurs jusqu\u2019à ce que la "
        "sélection te convienne, puis applique. Les valeurs ne valent que "
        "pour CETTE caméra, car les échelles de qualité diffèrent d\u2019une "
        "caméra à l\u2019autre.",
    "livekalib.regler_det": "Score de détection",
    "livekalib.regler_det_prosa":
        "À partir d\u2019ici, une trouvaille compte comme visage. Celui-ci "
        "pilote vraiment la reconnaissance : tout ce qui est en dessous "
        "n\u2019atteint jamais la vérification du nom. Plus bas garde plus "
        "de matière (mesuré : une barre haute jetait la moitié de la matière "
        "utilisable) ; plus haut laisse dehors les haies et les taches de "
        "lumière.",
    "livekalib.regler_e": "Impression d\u2019image",
    "livekalib.regler_e_prosa":
        "À quel point l\u2019image paraît nette et claire à l\u2019œil. Cela "
        "ne décide PAS qui est reconnu \u2014 cela décide quelle image part "
        "dans l\u2019alerte et quels visages restent ici comme échantillons.",
    "livekalib.regler_t": "Lisibilité du visage",
    "livekalib.regler_t_prosa":
        "À quel point la personne se distingue, visages à moitié couverts "
        "compris. Comme le curseur du dessus : il choisit l\u2019image et "
        "remplit cette page, il n\u2019écarte jamais personne de la "
        "reconnaissance.",
    "livekalib.ohne_guete":
        "Les deux modèles de qualité manquent dans cette version : les "
        "échantillons ne portent donc pas de chiffres de qualité et les deux "
        "curseurs du bas n\u2019ont aucun effet ici. Le score de détection "
        "fonctionne.",
    "livekalib.standard": "Valeurs par défaut",
    "livekalib.fueller.laeuft": "recherche de matériel en cours",
    "livekalib.fueller.bilanz": "dernière recherche de matériel",
    "livekalib.fueller.bilder": "image(s)",
    "livekalib.tab_erkennen": "Reconnaître",
    "livekalib.tab_lernen": "Catalogue des visages",
    "livekalib.uebernehmen": "Appliquer",
    "livekalib.leer": "Pas encore d'échantillons. Ils arrivent d'eux-mêmes — d'un veilleur en marche et de chaque analyse d'événement de cette caméra, un visage à chaque fois. Si vous ne voulez pas attendre, utilisez ci-dessous « Chercher du matériel frais ».",
    "livekalib.zurueck": "retour au veilleur",
    "livekalib.js.genutzt": "{n} échantillons sur {gesamt} passent",
    "livekalib.js.gespeichert": "enregistré",
    "livekalib.js.fehler": "erreur",
    # --- Kalibrier-Zentralumbau 31.08.: Abschnitte, Katalog-Latte, Material
    "livekalib.zur_uebersicht": "retour à toutes les caméras",
    "livekalib.abschnitt.anzeige": "Alertes, affichage et échantillons",
    "livekalib.abschnitt.anzeige_prosa": "Ces trois-là décident quelle image de cette caméra part dans une alerte et quels visages restent ici comme échantillons. Ils ne décident pas qui est reconnu.",
    "livekalib.abschnitt.katalog": "Seuil du catalogue",
    "livekalib.abschnitt.material": "Matériel",
    "livekalib.katalog.prosa": "Une barre propre et plus stricte : la qualite qu'un visage de cette camera doit avoir pour devenir reference par les voies AUTOMATIQUES (reprise du cycle d'apprentissage, acceptation de propositions/reserves). Ce que tu coches et nommes toi-meme la contourne volontairement : ce qui est coche est appris, et le controle qualite peut trier ensuite.",
    "livekalib.katalog.grenze": "Ce qu'il ne fait pas : il ne supprime jamais les références existantes et ne change pas qui est reconnu. Les images sans scores de qualité (matériel ancien ou build sans les modèles de qualité) passent intactes — un seuil sans mesure jetterait à l'aveugle.",
    "livekalib.katalog.quelle_kamera": "Actif : les valeurs propres de cette caméra.",
    "livekalib.katalog.quelle_global": "Actif : la valeur globale de repli — cette caméra n'a pas encore de valeurs propres.",
    "livekalib.katalog.quelle_aus": "Aucun seuil de catalogue : toute image peut devenir une référence.",
    "livekalib.katalog.regler_e": "Catalogue : impression de l'image",
    "livekalib.katalog.regler_e_prosa": "Impression minimale pour une référence de cette caméra. Gardez-la au-dessus du curseur plus haut : ce qui suffit à montrer ne suffit pas automatiquement à apprendre.",
    "livekalib.katalog.regler_t": "Catalogue : reconnaissabilité",
    "livekalib.katalog.regler_t_prosa": "Reconnaissabilité minimale pour une référence de cette caméra. C'est elle qui garde les visages à moitié couverts hors du catalogue.",
    "livekalib.material.aus": "La collecte d'échantillons est désactivée (Advanced, calibration samples). Sans échantillons cette page n'a rien à montrer.",
    "livekalib.material.stand": "{n} sur {deckel} échantillons au maximum",
    "livekalib.material.wann": "dernier {wann}",
    "livekalib.material.fuellen_prosa": "La recherche de matériel parcourt les derniers événements personne de cette caméra et garde le meilleur visage de chacun. Elle s'arrête à {ziel} images ou après {events} événements, au premier des deux.",
    "livekalib.material.lauf": "Plus {n} image(s) de cette caméra issues du dernier passage d'apprentissage — affichées ci-dessous et marquées.",
    "livekalib.js.katalog": "{n} sur {gesamt} pourraient entrer au catalogue",
    "livekalib.js.lauf": "passage",
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
        "Remesure chaque photo de référence (qualité du visage comprise) et "
        "repère les faibles, les quasi-doublons et les visages confondus. Prend "
        "quelques minutes selon le nombre de photos et tourne en arrière-plan.",
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
    "qualitaet.galerie.vorrat": "du stock",
    "qualitaet.galerie.norm": "qualité {norm}",
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
    "lernwizard.wizard.auswahl_durchsucht": "{k} de ces {n} ont déjà été parcourus — avec \"ignorer les événements déjà parcourus\", la session prend des événements plus anciens (la carte indique où elle aboutit).",
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
    "lernwizard.balken.suchen": "Recherche des visages",
    "lernwizard.balken.pose": "Position de la tête",
    "lernwizard.balken.erkennen": "Reconnaissance des visages",
    "lernwizard.balken.z_frames": "image {f} sur {s}",
    "lernwizard.balken.z_posen.eins": "{n} pose",
    "lernwizard.balken.z_posen.viele": "{n} poses",
    "lernwizard.balken.z_erkannt.eins": "{n} reconnu",
    "lernwizard.balken.z_erkannt.viele": "{n} reconnus",
    "lernwizard.balken.wartet": "en attente",
    "lernwizard.balken.clip": "récupération du clip …",
    "lernwizard.balken.fertig": "terminé",
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
    "kalib.titel": "Calibrage des caméras",
    "kalib.erklaerung": "Ces deux seuils décident quels visages les prochains apprentissages conservent. Faites glisser jusqu'à ce que la limite vous convienne — tout ce qui est grisé serait écarté. Ci-dessous, les images du dernier passage, meilleure impression d'abord. Cadre jaune = image retenue pour l'adoption.",
    "kalib.leer": "Rien à calibrer pour l'instant : le dernier passage ne porte pas de valeurs de qualité. Lancez d'abord un apprentissage avec cette version.",
    "kalib.regler_e": "Impression d'image",
    "kalib.regler_e_prosa": "À quel point l'image paraît nette et lumineuse. Plus bas garde davantage, mais des images plus sombres et plus grossières.",
    "kalib.regler_t": "Reconnaissabilité",
    "kalib.regler_t_prosa": "À quel point la personne est identifiable. Écarte aussi les visages à moitié masqués.",
    "kalib.standard": "Rétablir les valeurs par défaut",
    "kalib.uebernehmen": "Appliquer les seuils",
    "kalib.js.genutzt": "Conservées : {n} sur {gesamt}",
    "kalib.js.gespeichert": "Enregistré — le passage est réévalué avec les nouvelles limites, retour à l'apprentissage dans un instant …",
    "kalib.js.fehler": "Échec de l'enregistrement",
    # --- zentrale Kamera-Uebersicht + globaler Rueckfall (31.08.)
    "kalib.knopf": "Calibrage",
    "kalib.knopf_tip": "Calibrage des caméras : les seuils pour les alertes, les échantillons et le catalogue de références",
    "kalib.uebersicht.erklaerung": "Une caméra, un jeu de valeurs. Les échelles de qualité diffèrent d'une caméra à l'autre — mesuré sur une seule installation, la reconnaissabilité médiane d'une caméra était plus du double de celle d'une autre. Choisissez une caméra pour régler ses seuils.",
    "kalib.uebersicht.leer": "Pas encore de caméras",
    "kalib.uebersicht.leer_hinweis": "Dès que Frigate signale des caméras, elles apparaissent ici.",
    "kalib.grenze.titel": "Ce que le calibrage fait — et ce qu'il ne fait pas",
    "kalib.grenze.satz": "Il décide quelle image est montrée ou envoyée, quels visages restent comme échantillons et lesquels peuvent devenir une référence. Il ne décide jamais qui est reconnu : la vérification des noms voit tous les visages, sans filtre. C'est mesuré, pas supposé — filtrer avant le vote a coûté des confirmations.",
    "kalib.kachel.eigene": "valeurs propres",
    "kalib.kachel.vorgabe": "valeurs par défaut",
    "kalib.kachel.fremd": "absente de Frigate",
    "kalib.kachel.fremd_tip": "Cette caméra a des valeurs de calibrage mais Frigate ne la signale plus. Les valeurs restent, rien n'est supprimé.",
    "kalib.kachel.vorrat": "{n} sur {deckel} échantillons",
    "kalib.kachel.vorrat_aus": "La collecte d'échantillons est désactivée (Advanced, calibration samples).",
    "kalib.kachel.stand": "dernier {wann}",
    "kalib.kachel.leer": "Pas encore d'échantillons",
    "kalib.kachel.leer_hinweis": "Les échantillons viennent d'un veilleur en marche et des analyses d'événements — ou allez en chercher maintenant.",
    "kalib.kachel.bilanz_keine": "La recherche de matiere a examine {ev} evenement(s) : aucun visage trouve sur cette camera — une vue d'ensemble aussi large ne peut pas alimenter le calibrage.",
    "kalib.kachel.bilanz_klein": "La recherche de matiere a examine {ev} evenement(s) : des visages ont ete trouves, mais tous trop petits ou trop faibles pour la reserve (sous la barre de recolte).",
    "kalib.kachel.bilanz_zulauf": "La recherche de matiere a examine {ev} evenement(s) et trouve de la matiere utilisable, mais rien n'a atteint la qualite de la reserve — relance la recherche ou signale-le.",
    "kalib.kachel.werte": "détection {det} · impression {e} · reconnaissabilité {tw}",
    "kalib.kachel.katalog": "seuil du catalogue {e} / {tw}",
    "kalib.quelle.kamera": "propre",
    "kalib.quelle.global": "repli global",
    "kalib.quelle.aus": "désactivé",
    "kalib.knopf_kalibrieren": "Calibrer",
    "kalib.knopf_fuellen": "Chercher du matériel frais",
    "kalib.knopf_leeren": "Supprimer les échantillons",
    "kalib.global.titel": "Repli global",
    "kalib.global.satz": "Elles valent pour les caméras sans valeurs propres et servent de seuil quand un passage d'apprentissage décide quels visages garder.",
    "kalib.global.werte": "impression {e} · reconnaissabilité {tw}",
    "kalib.global.katalog": "seuil du catalogue {e} / {tw}",
    "kalib.global.knopf": "Régler sur le dernier passage d'apprentissage",
    "kalib.global.kein_lauf": "Pas encore de passage d'apprentissage avec des scores de qualité — réglable dès qu'un passage est terminé.",
    "kalib.lauf.titel": "Seuils globaux — dernier passage d'apprentissage",
    "kalib.zurueck": "retour à toutes les caméras",
    "js.kalib.start": "recherche de matériel …",
    "js.kalib.lauf": "{i} sur {n} événements · {bilder} image(s)",
    "js.kalib.fertig": "{bilder} image(s) de {events} événement(s)",
    "js.kalib.fehler": "recherche de matériel impossible",
    "lernwizard.kachel.benennen": "Attribution intelligente",
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
    "lernwizard.pop.label_kameras": "uniquement ces caméras",
    "lernwizard.pop.hint_kameras": "rien de sélectionné = toutes les caméras ; plusieurs avec Ctrl/Cmd",
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
    "lernwizard.k1.kameras": "caméras uniquement : {kameras}",
    "lernwizard.k1.tag": "jour {tag}",
    "lernwizard.k2.satz":
        "Tourne toute seule &mdash; vous pouvez fermer cette page et "
        "revenir.",
    "lernwizard.k2.knopf_abort": "Interrompre la session",
    "lernwizard.k3.satz_warten":
        "Le système nomme lui-même les personnes qu'il reconnaît avec certitude. Le reste vous revient &mdash; dites qui c'est, ou passez.",
    "lernwizard.k3.keine_gesichter":
        "Aucun nouveau visage cette fois &mdash; rien à nommer. Ce n'est "
        "pas grave&nbsp;: cela signifie simplement que les "
        "enregistrements ne contenaient personne de nouveau.",
    "lernwizard.knopf_neuer_lauf": "Démarrer une nouvelle session",
    "lernwizard.k3.gruppe_offen":
        "Le groupe en cours est ouvert ci-dessous, en pleine largeur.",
    "lernwizard.k3.alle_erledigt": "Tous les groupes sont traités.",
    "lernwizard.k3.altes_verfahren":
        "Ces groupes viennent de l'ancienne méthode, sans contrôle de qualité. Les nommer reviendrait à trier des images que la session n'accepte plus. Lancez une nouvelle session.",
    "lernwizard.chip.bilder": "{n} photos",
    "lernwizard.k3.verworfen.eins":
        "{n} groupe supprimé par vous &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} groupes supprimés par vous &middot;",
    "lernwizard.k3.link_einsehen": "voir",
    "lernwizard.k3.done_weiter":
        "{erledigt} sur {gesamt} traités &mdash; le suivant est prêt.",
    "lernwizard.k3.done_punkt": "{erledigt} sur {gesamt} traités.",
    "lernwizard.k3.wartend.eins": "{n} groupe vous attend.",
    "lernwizard.k3.wartend.viele": "{n} groupes vous attendent.",
    "lernwizard.k3.auto.eins": "{n} a été reconnu automatiquement &mdash; vérifiez-le si vous voulez.",
    "lernwizard.k3.auto.viele": "{n} ont été reconnus automatiquement &mdash; vérifiez-les si vous voulez.",
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
    "lernwizard.zw.titel_auto": "Groupe {pos} sur {gesamt} &mdash; est-ce {name} ?",
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
        "Supprimer ce groupe&nbsp;? Ses photos sont effacées et un nommage en attente est abandonné. Cette action est irréversible.",
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
    "nav.lernlauf": "Apprentissage du visage",
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
    "nav.systemstat": "Statistiques système",
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
    "ui.last.knopf": "Statistiques",
    "ui.last.tooltip": "Charge du système : CPU, RAM, disque, GPU et la reconnaissance",
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
    "js.catchup.frage": "Ne plus rattraper les événements manqués au démarrage ? Le service redémarre pour appliquer ce choix.",
    "catchup.knopf": 'Rattraper',
    "catchup.knopf.tooltip": 'Des événements non traités sont en attente',
    "catchup.dlg.titel": 'Récupérer les événements non traités',
    "catchup.dlg.label_stunden": 'Remonter de',
    "catchup.dlg.wort_stunden": 'heures',
    "catchup.dlg.label_limit": 'Au maximum',
    "catchup.dlg.wort_events": 'événements',
    "catchup.dlg.fuss": 'Seuls les événements jamais analysés sont récupérés. Les paramètres restent inchangés.',
    "catchup.dlg.abbrechen": 'Annuler',
    "catchup.dlg.los": 'Récupérer',
    "js.catchup.spanne": '{von} à {bis}',
    "js.catchup.geklemmt": 'Ne sont possibles que {h} h et {n} événements. Lancer avec ces valeurs ?',
    "js.catchup.nicht_bereit": "Apprenez d'abord une personne, ces événements pourront ensuite être vérifiés.",
    "js.catchup.warten": 'Événements non traités en attente : {n}',
    "antwort.catchup_gestartet": 'Récupération des dernières {stunden} h, au maximum {n} événements.',
    "antwort.catchup_laeuft": 'Un rattrapage est déjà en cours.',
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
    "js.vorrat.frage": "Ajouter {n} visage(s) du stock à {person} ? Ils deviennent aussitôt des références (restent en local, pas d'export).",
    "js.qs.fortschritt": "vérification de la photo {i} sur {n} …",
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
    "js.unb.besucher_frage": "Ignorer comme visiteur inconnu habituel ? Il ne déclenchera plus d'alertes. (Réactivable à tout moment ci-dessous, dans \"visiteurs habituels\".)",
    "js.unb.merge_frage": "Fusionner ?",
    "js.unb.name_fehlt": "Saisir un nom (personne nouvelle ou existante).",
    "js.unb.benennen_frage": "Attribuer à \"{person}\" ? Les meilleures images deviennent des références.",
    "js.unb.teil_frage": "Attribuer les {n} images cochées à « {person} » ? Le reste du groupe reste dans Inconnus.",
    "js.unb.objekt_frage": "Marquer comme « pas une personne » (un buisson, un reflet, une voiture garée) ? Ce groupe n'apparaîtra plus comme visiteur ; annulation possible sous « pas des personnes ».",
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
    # js.vision.dirty_text zitiert vision.save.knopf WOERTLICH und VOLL
    # (« Enregistrer la connexion », Tranche C) — bei Umbenennung nachziehen.
    "js.vision.dirty_text": "Le test utiliserait les valeurs qui viennent d'être saisies. La reconnaissance continue d'utiliser la connexion ENREGISTRÉE tant que vous n'avez pas cliqué sur « Enregistrer la connexion » — un test vert seul ne change rien aux verdicts.",
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
    "js.vision.prompt_zurueck": "formulation par défaut rétablie — cliquer sur « Enregistrer la connexion » pour la conserver",
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
    "js.live.vorrat_leeren_frage":
        "Effacer les échantillons de calibrage de cette caméra ? Ils sont irrécupérables ; le veilleur en collecte de nouveaux à partir de maintenant.",
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
    # ---- verifyd-Innenseiten (Stufe 2, Tranche B) ----
    # Inline-Handler in verifyd.py (_banner, Setup-Wizard, Today-Leer-
    # zustaende, /unbekannte, /live_alerts, /video, /event/<id>);
    # Stufe-2-Grenzen s. en.py-Abschnittskommentar.
    "banner.schoner":
        "Frigate ne répond pas — nouvelles tentatives espacées de "
        "quelques secondes jusqu'à son retour ; l'interface continue "
        "de fonctionner avec les données locales.",
    "banner.fehler":
        "Frigate injoignable (dernière erreur {zeit}) : {fehler} — "
        "l'interface continue de fonctionner avec les données locales.",
    "banner.nachholen.eins":
        "Rattrapage des événements manqués de la dernière heure :"
        " {fertig} sur {gesamt}",
    "banner.nachholen.viele":
        "Rattrapage des événements manqués des {n} dernières heures :"
        " {fertig} sur {gesamt}",
    "banner.nachholen_aus": "Ne plus rattraper au démarrage à l'avenir",
    "hinweis.frigate_fr_an": "La reconnaissance faciale de Frigate est activee. suslik n\u2019en a pas besoin : il reconnait lui-meme et fonctionne dans les deux cas. Vous pouvez la desactiver dans Frigate si vous ne vous en servez pas par ailleurs.",
    "ui.hinweis.x_tooltip": "Ne plus afficher cet avis",
    "ui.hinweis.x_aria": "Masquer definitivement cet avis",
    "setupwiz.frigate.status_ok":
        "✓ Connexion établie — {n} caméra(s) trouvée(s)",
    "setupwiz.frigate.status_fehl":
        "✗ Impossible de joindre Frigate : {fehler}",
    "setupwiz.frigate.status_fehl_keine": "aucune caméra",
    "setupwiz.frigate.status_fehl_hinweis":
        "Corrigez l'URL (ou définissez FRIGATE_URL dans votre .env / "
        "docker-compose), puis testez à nouveau.",
    "setupwiz.frigate.status_leer":
        "Saisissez l'URL de Frigate et testez la connexion.",
    "setupwiz.frigate.titel": "Se connecter à Frigate",
    "setupwiz.frigate.satz":
        "suslik lit les caméras directement depuis l'API de Frigate "
        "(généralement le port 5000). Aucune caméra n'est codée en dur.",
    "setupwiz.frigate.knopf_test": "Tester la connexion",
    "setupwiz.kameras.titel": "Choisir les caméras et les conditions",
    "setupwiz.kameras.satz":
        "Cochez les caméras à surveiller ; cochez une ou plusieurs zones "
        "pour n'analyser que les événements qui y sont entrés (p. ex. "
        "une personne dans le jardin). Aucune case cochée = tous les "
        "événements.",
    "setupwiz.kameras.satz_ohne":
        "Connectez-vous d'abord à Frigate — les caméras apparaîtront ici.",
    "setupwiz.backend.titel": "Accélération",
    "setupwiz.backend.verfuegbar": "Disponible sur cette machine :",
    "setupwiz.backend.satz_wahl":
        "Choisissez une option — le CPU fonctionne toujours.",
    "setupwiz.import.titel": "Importer les visages depuis Frigate",
    # Zaehler-Split an der <b>-Grenze (§8.10) wie in en.py; Rand-
    # Leerzeichen gehoeren zum Wert.
    "setupwiz.import.zahl_vor": "Frigate contient déjà ",
    "setupwiz.import.zahl_mitte": " image(s) de référence de ",
    "setupwiz.import.zahl_nach": " personne(s).",
    "setupwiz.import.satz":
        "Importez-les pour que suslik reconnaisse tout le monde dès le "
        "départ. Les images sont téléchargées rapidement, puis suslik "
        "calcule lui-même les caractéristiques faciales sur votre "
        "accélérateur (GPU/NPU).",
    "setupwiz.import.knopf": "Importer les {n} visages depuis Frigate",
    "setupwiz.import.satz_leer":
        "Aucun visage dans Frigate pour l'instant. À noter : suslik a "
        "besoin d'au moins un visage de référence avant de pouvoir "
        "reconnaître qui que ce soit — importez ici depuis Frigate, ou "
        "téléversez des photos plus tard sur la page Connus.",
    "setupwiz.import.satz_ohne":
        "Connectez-vous d'abord à Frigate — vous pourrez ensuite "
        "importer ici ses visages connus.",
    "setupwiz.fertig.knopf": "Enregistrer et démarrer suslik",
    "setupwiz.fertig.satz":
        "Enregistre vos choix et redémarre le service une seule fois.",
    "setupwiz.restore.titel": "Vous avez déjà une configuration ?",
    # Zitiert system.titel + system.backup.titel woertlich (Tranche C).
    "setupwiz.restore.satz":
        "Si vous avez déjà exporté une configuration suslik (Système → "
        "Sauvegarde de la configuration), chargez-la ici pour restaurer "
        "tous les paramètres et sauter l'assistant.",
    "setupwiz.restore.knopf": "Charger un fichier de configuration…",
    "setupwiz.write.titel": "Écrire dans Frigate ?",
    "setupwiz.write.satz":
        "suslik peut écrire ses verdicts dans Frigate (sub_labels) et "
        "synchroniser les références, pour faire fonctionner les deux "
        "en parallèle. La lecture seule est le choix sûr par défaut.",
    "setupwiz.write.opt_ro":
        "Lecture seule (recommandé) — suslik n'écrit jamais dans Frigate",
    "setupwiz.write.opt_rw":
        "Écrire dans Frigate (fonctionnement en parallèle)",
    "setupwiz.willkommen.titel": "Bienvenue dans suslik",
    "setupwiz.willkommen.satz":
        "Une installation guidée rapide — ou chargez une configuration "
        "existante pour la sauter. Tout ce qui suit reste modifiable "
        "plus tard sur les pages habituelles.",
    "leer.passe_area_heute":
        "Aucun passage n'a encore traversé le secteur {area} "
        "aujourd'hui.",
    "leer.passe_area_tag":
        "Aucun passage n'a traversé le secteur {area} ce jour-là.",
    "leer.passe_area_hinweis":
        "Le filtre « All » ci-dessus affiche l'ensemble de la propriété.",
    "leer.passe_heute": "Pas encore de passage avec un visage aujourd'hui.",
    "leer.passe_heute_hinweis":
        "Dès que quelqu'un traverse la propriété, le passage apparaît "
        "ici.",
    "leer.tag": "Rien avec un visage ce jour-là.",
    "leer.tag_hinweis":
        "Utilisez les flèches pour consulter un autre jour, ou ouvrez "
        "Événements pour la liste complète.",
    "leer.frigate": "Aucun Frigate connecté pour l'instant.",
    "leer.frigate_hinweis":
        "Renseignez l'URL de Frigate dans l'assistant d'installation "
        "(page Système) — les passages apparaîtront ensuite ici "
        "automatiquement.",
    "leer.refs":
        "Connecté — mais aucun visage de référence pour l'instant, "
        "personne ne peut donc être reconnu.",
    "leer.refs_hinweis":
        "Importez des visages depuis Frigate ou téléversez des photos — "
        "les deux sur la page Connus. suslik continue ensuite "
        "d'apprendre tout seul à partir des caméras.",
    "leer.band_heute": "Encore rien avec un visage aujourd'hui.",
    "leer.band_tag": "Rien avec un visage ce jour-là.",
    "leer.band_hinweis":
        "Les personnes apparaissent ici dès qu'un passage est analysé.",
    "leer.person_unbekannt": "Personne inconnue.",
    "leer.kamera_unbekannt": "Caméra inconnue.",
    "leer.kamera_unbekannt_hinweis":
        "Les tuiles proviennent uniquement de la liste des caméras de "
        "Frigate et des surveillances enregistrées.",
    "unbekannte.name": "Inconnu {nummer}",
    "unbekannte.meta_zeit": " apparitions · {zeit}",
    "unbekannte.mehr_bilder": "+{n} autres images dans ce groupe",
    "unbekannte.knopf_reaktivieren": "réactiver",
    "unbekannte.attr_name": "Nom (nouveau ou existant)",
    "unbekannte.attr_wahl": "Choisir ce groupe pour la fusion",
    "unbekannte.knopf_zuweisen": "Attribuer",
    "unbekannte.knopf_teil": "Attribuer les {n} cochées",
    "unbekannte.knopf_ignorieren": "Ignorer",
    "unbekannte.knopf_objekt": "Pas une personne",
    "unbekannte.knopf_person": "C'est une personne",
    "unbekannte.knopf_bulkmerge": "Fusionner les {n} groupes choisis",
    "unbekannte.knopf_mehr": "Afficher {n} groupes de plus",
    "unbekannte.titel": "Inconnus",
    "unbekannte.anker": "{offen} groupes sur {gesamt} attendent encore",
    "unbekannte.sort_label": "Tri",
    "unbekannte.sort_bilder": "le plus d'images",
    "unbekannte.sort_neu": "les plus récents",
    "unbekannte.filter_label": "Afficher",
    "unbekannte.f_offen": "à traiter",
    "unbekannte.f_wieder": "récurrents",
    "unbekannte.f_heute": "nouveaux aujourd'hui",
    "unbekannte.f_vorschlag": "fusion suggérée",
    "unbekannte.f_besucher": "en sourdine",
    "unbekannte.f_objekt": "pas des personnes",
    "unbekannte.kopf_satz":
        "Visages sans correspondance connue, regroupés en identités "
        "récurrentes.",
    # Kopf-Erklaerung an den <b>-Grenzen gesplittet; die Fett-Teile sind
    # die knopf_*-Schluessel selbst (eine Quelle, kein Drift).
    "unbekannte.kopf_satz_zuweisen":
        " relie une identité à une personne (nouvelle ou existante, "
        "saisissez le nom),",
    "unbekannte.kopf_satz_ignorieren":
        " met en sourdine un visiteur inconnu habituel (aucune alerte).",
    "unbekannte.kopf_satz_auto":
        "Les nouveaux visages sont collectés automatiquement après "
        "chaque passage.",
    "unbekannte.knopf_reorg": "Réorganiser maintenant",
    "unbekannte.hinweis_reorg":
        "revérifie les visages collectés et reconstruit les groupes — "
        "la collecte elle-même s'exécute automatiquement (1-2 min)",
    "unbekannte.satz_objekte":
        "Des groupes dont les images sont quasi identiques entre elles "
        "et ne ressemblent à aucune personne — typiquement une aile de "
        "voiture, un revêtement de sol ou un motif lumineux que le "
        "détecteur prend sans cesse pour un visage. Ils sont figés : "
        "les nouvelles découvertes ne sont jamais ajoutées ici (elles "
        "forment de nouveaux groupes visibles, revérifiés par la même "
        "règle) — les groupes restent listés pour que rien ne soit "
        "caché. Marqués à la main ou trouvés automatiquement ; « C'est une personne » en ramène un.",
    "unbekannte.leer": "Aucun visage inconnu collecté pour l'instant.",
    "unbekannte.leer_hinweis":
        "Les identités apparaissent ici après le prochain visiteur "
        "inconnu.",
    "unbekannte.leer_filter": "Rien dans cette vue.",
    "unbekannte.leer_filter_hinweis": "D'autres groupes attendent sous un autre filtre ci-dessus.",
    "livealerts.link_video": "&#9654; vidéo {n}",
    "livealerts.person_unbekannt": "inconnu",
    "livealerts.trigger.eins": "{n} déclenchement",
    "livealerts.trigger.viele": "{n} déclenchements",
    "livealerts.kanal_keiner": "sans envoi (aucun canal)",
    "livealerts.keine_bilder": "aucune image enregistrée",
    "livealerts.titel": "Alertes de la surveillance en direct",
    "livealerts.kopf.auftritte.eins": "{n} apparition",
    "livealerts.kopf.auftritte.viele": "{n} apparitions",
    "livealerts.kopf.satz":
        " le {tag} — vérification rapide, provisoire ; le verdict "
        "confirmé vient de l'analyse normale.",
    "livealerts.kopf.satz_alt":
        "Les entrées antérieures à 0.1.0.190 n'ont ni image ni nom "
        "enregistrés.",
    "livealerts.leer": "Aucune alerte en direct ce jour-là.",
    "video.fehl":
        "&#9888; Échec du transcodage — voir le journal du service "
        "(/log).",
    "video.fehl_hinweis":
        "Rechargez cette page pour réessayer, ou ouvrez la séquence "
        "d'origine :",
    "video.warte": "Préparation de la vidéo pour le navigateur (H.264) …",
    "video.warte_satz":
        "Cette page s'actualise automatiquement. La copie n'est créée "
        "qu'une seule fois, puis mise en cache.",
    "event.ours_zeile.eins":
        "{person} — {stufe} (visible dans {n} fenêtre)",
    "event.ours_zeile.viele":
        "{person} — {stufe} (visible dans {n} fenêtres)",
    "event.ours_keiner": "personne ne correspond",
    "event.ours_rest.eins": " · {n} autre : aucune correspondance",
    "event.ours_rest.viele": " · {n} autres : aucune correspondance",
    "event.grenze":
        "sous cette ligne : correspondances faibles (meilleur score "
        "&lt; {wert}) — le nom est une supposition, il peut s'agir "
        "d'une autre personne",
    "event.gruppe_ohne": "Sans attribution",
    "event.badge_unsicher": "incertain",
    "event.leer_crops":
        "Aucun cadrage de visage conservé pour cet événement.",
    "event.knopf_video": "&#9654; Vidéo",
    "event.knopf_log": "Journal d'analyse",
    "event.attr_unvollstaendig":
        "séquence incomplète — {gelesen}/{soll} images lues ; le "
        "verdict porte sur la partie lisible",
    "event.badge_unvollstaendig": "⚠ séquence incomplète",
    "event.pass_zurueck": "&#8592; préc.",
    "event.pass_weiter": "suiv. &#8594;",
    "event.pass_teil": "Fait partie d'un passage",
    "event.pass_events.eins": "{n} événement",
    "event.pass_events.viele": "{n} événements",
    "event.pass_knopf": "voir le passage",
    "event.label_grund": "Motif de l'erreur",
    "event.grund_ohne_zeile":
        "analyze.log ne contient aucune ligne de motif — utilisez le "
        "bouton journal ci-dessous",
    "event.grund_ohne_log":
        "aucun analyze.log conservé pour cet événement — voir le "
        "journal du service (page Système)",
    "event.zurueck": "← Aujourd'hui",
    "event.label_korrektur": "Corriger en cas d'erreur",
    "event.label_wer": "Qui était-ce ?",
    "event.h_bilder": "Images",
    # ---- Routen-Seiten (Stufe 2, Tranche C) ----
    # Uebersetzung der en.py-Tranche C (429 Schluessel); Grenzen und
    # Wiederverwendungen s. en.py-Abschnittskommentar. FR-Interpunktion:
    # echtes U+00A0 vor : ; ! ? und in « » (§8.21). Seitentitel wortgleich
    # zu ihren nav.*-Linktexten (system.titel==nav.system,
    # vision.titel==nav.vision, visiontest.titel==nav.erkennungstest,
    # personwizard.kontrolle.titel==nav.person_kontrolle,
    # personwizard.karte.titel==nav.person_modell). "stranger" folgt F3
    # (begriffe_tabellen.md): Personen-Label « intrus ».
    # --- routes/system.py ---
    "system.ampel.service": "Service",
    "system.ampel.service_info": "traités (au total) : {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — autotest OK",
    "system.ampel.backend_fail":
        "{backend} — {n} échec(s) d'autotest, voir le journal du service",
    "system.ampel.analyse": "Analyse",
    "system.ampel.analyse_dauer": "dernière durée {s} s",
    "system.ampel.analyse_nie": "aucune analyse pour l'instant",
    "system.ampel.retry": "File de rattrapage",
    "system.ampel.retry_info":
        "{offen} ouverts / {aufgegeben} abandonnés (fenêtre {tage} j)",
    "system.ampel.frigate_unkonfiguriert":
        "pas encore configuré — renseignez l'URL dans l'assistant "
        "d'installation",
    "system.ampel.frigate_ok": "joignable",
    # {zeit} kommt vorformatiert (%H:%M) aus der Route (B19-Stufe).
    "system.ampel.frigate_fehler": "dernière erreur {zeit}",
    # {s} vorformatiert (:.0f) — Formatspezifika nie in Werte (§8.8).
    "system.ampel.mqtt_hb": "heartbeat il y a {s} s",
    "system.ampel.mqtt_kein_hb": "aucun heartbeat pour l'instant",
    "system.ampel.mqtt_pub_aus": "configuré, publication désactivée",
    "system.ampel.mqtt_pub_kaputt":
        "configuré, la publication n'a pas démarré — voir le journal du "
        "service",
    "system.ampel.mqtt_unkonfiguriert": "non configuré",
    "system.ampel.disk": "Disque",
    "system.ampel.disk_info2": "{gb} Go libres · cache des clips {cache} Go sur {max} Go",
    "system.disk.titel": "Espace disque",
    "system.disk.satz": "Les clips sont un cache : conservés {tage} jours, plafonnés à {max} Go, et allégés dès que moins de {min} Go sont libres (vérification après chaque événement, plus une surveillance quotidienne du disque qui passe à toutes les 10 minutes tant que l'espace est faible).",
    "system.disk.knopf": "Nettoyer maintenant",
    "system.disk.warnung": "Il ne reste que {gb} Go libres et le cache des clips est déjà vide — libérez de l'espace sur le volume de données, sinon les nouveaux événements ne pourront pas être enregistrés.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "À VÉRIFIER",
    "system.drift.banner":
        "GARDE-FOU DE DÉRIVE AU ROUGE après le dernier ajout de "
        "référence :",
    "system.sync.titel": "Synchronisation avec Frigate",
    "system.sync.knopf": "Ouvrir la synchronisation Frigate",
    "system.sync.satz":
        "La page de synchronisation compare les deux bibliothèques "
        "personne par personne, soumet chaque candidat à la même "
        "vérification préalable que Frigate, n'envoie que ce que vous "
        "cochez, et importe ce que seul Frigate possède.",
    "system.sync.fehlt":
        "pas encore disponible — nécessite un Frigate joignable et au "
        "moins un visage de référence",
    "system.qc.titel": "Rapport qualité",
    "system.qc.stand": "(au {stand}, {tage} jours)",
    "system.qc.kopf_gesicht": "avec visage",
    "system.qc.kopf_bestaetigt": "confirmés",
    "system.qc.kopf_quote": "taux (fenêtre)",
    # WIRD ZITIERT: setupwiz.restore.satz nennt diesen Titel woertlich
    # (in dieser Runde nachgezogen: « Sauvegarde de la configuration »).
    "system.backup.titel": "Sauvegarde de la configuration",
    "system.backup.satz":
        "Téléchargez les paramètres stockés dans /data/config en un seul "
        "fichier JSON, ou restaurez-les depuis un tel fichier. Portée "
        "honnête : aujourd'hui, c'est la FICHE CAMÉRAS (avec ses valeurs "
        "enregistrées) ; les seuils/canaux définis uniquement dans "
        "verifyd.yaml ou via l'environnement ne sont PAS dans ce fichier. "
        "Personnes apprises/références : utilisez la sauvegarde complète "
        "ci-dessous.",
    "system.backup.knopf_download": "Télécharger la configuration",
    "system.backup.knopf_restore": "Restaurer depuis un fichier…",
    "system.backup.careful": "Attention :",
    # {hinweis} = core.registry.VISION_EXPORT_HINWEIS (zentrale Quelle,
    # noch englisch).
    "system.backup.careful_config":
        "ce fichier {hinweis} (canaux de notification et détection par "
        "vision), afin qu'une restauration sur une autre machine "
        "fonctionne vraiment.",
    "system.backup.restore_satz":
        "La restauration écrase les paramètres actuels (les précédents "
        "sont conservés en .bak) et redémarre le service.",
    "system.voll.titel": "Sauvegarde complète",
    "system.voll.satz":
        "Une seule archive portable avec tout ce que vous avez appris à "
        "cette installation : les paramètres, la bibliothèque de "
        "références, les résultats des sessions d'apprentissage, tout le "
        "matériel de la reconnaissance corporelle (images, vos verdicts "
        "d'examen, modèles entraînés) et l'historique des événements. "
        "Prévue pour un changement de machine. Portée "
        "honnête : le cache des séquences vidéo et les artefacts "
        "d'analyse par événement n'y sont PAS — ils se reconstruisent "
        "avec le temps.",
    "system.voll.knopf_download": "Télécharger la sauvegarde complète",
    "system.voll.knopf_restore": "Restaurer une sauvegarde complète…",
    "system.voll.careful": "cette archive {hinweis}.",
    "system.voll.restore_satz":
        "La restauration remplace ces éléments (chaque état précédent est "
        "conservé une fois en *.pre-restore-*) et redémarre le service. "
        "Téléverser quelques centaines de Mo peut prendre un moment — "
        "laissez la page ouverte.",
    "system.live.titel": "Surveillance en direct",
    "system.live.alerts": "Alertes envoyées aujourd'hui : {kanaele}",
    "system.live.stoerungen": "Avis d'incident aujourd'hui : {n}",
    "system.live.knopf": "Ouvrir la surveillance en direct",
    "system.live.quelle":
        "Compté d'après le journal de messages du moteur lui-même — "
        "seuls les messages réellement acceptés par un canal. Les alertes "
        "de la surveillance en direct sont distinctes des compteurs "
        "d'alertes de l'analyse d'événements sur la page Aujourd'hui.",
    "system.write.titel": "Écriture dans Frigate",
    "system.write.satz":
        "suslik écrit-il dans Frigate, ou lit-il seulement ? La lecture "
        "seule est le choix sûr par défaut ; n'activez l'écriture que "
        "pour le fonctionnement en parallèle (reconnaissance faciale "
        "Frigate + suslik).",
    "system.write.aktuell": "Actuellement :",
    "system.write.zustand_ro":
        "LECTURE SEULE — suslik n'écrit pas dans Frigate",
    "system.write.zustand_rw": "ÉCRITURE dans Frigate — sub_labels",
    "system.write.zustand_rw_sync": " + synchronisation des références",
    "system.write.knopf_rw": "Activer l'écriture",
    "system.write.knopf_ro": "Lecture seule",
    # WIRD ZITIERT: setupwiz.restore.satz nennt die Seite woertlich —
    # wortgleich mit nav.system (Linktext==Seitentitel).
    "system.titel": "Système",
    "system.tools.titel": "Outils",
    "system.docs.titel": "Documentation",
    "system.docs.link": "Documentation sur GitHub",
    # --- routes/vision.py ---
    "vision.zeit.nie": "jamais",
    # Wortgleich mit nav.vision (Linktext==Seitentitel).
    "vision.titel": "Détection par vision",
    "vision.kopf.dirty": "non enregistré",
    "vision.hinweis.titel": "Ce qu'il vous faut pour cela",
    "vision.schalter.knopf_aus": "Désactiver",
    "vision.schalter.knopf_an": "Activer",
    "vision.schalter.fehlt": "Il manque encore :",
    "vision.schalter.fehlt_galerien": "{n} sur {soll} galeries approuvees — creez-en une sous 'Creer une galerie'",
    "vision.schalter.fehlt_test": "un test de connexion au vert",
    "vision.schalter.fehlt_kandidaten": "des images jugees comme source de candidats — elles apparaissent pendant un passage ; activez la 'collecte de diagnostic' sous Personne si vous voulez les garder",
    "vision.schalter.titel_an": "La détection par vision est activée",
    "vision.schalter.titel_aus": "La détection par vision est désactivée",
    "vision.schalter.aus_satz":
        "Tant qu'elle est désactivée, rien n'est envoyé nulle part et "
        "aucune image ne quitte cette machine.",
    "vision.frage.titel": "Comment une comparaison est demandée",
    "vision.frage.doppel_titel":
        "Demander chaque paire deux fois, en permutant les galeries",
    "vision.frage.doppel_satz":
        "C'est la vérification de position. A à la première demande et B "
        "à la demande permutée désignent la MÊME galerie, une "
        "contradiction démasque donc un modèle qui préfère simplement ce "
        "qui vient en premier. Mesuré ici : chaque mauvaise réponse de "
        "toutes nos séries de test était un « A », jamais un « B ». La "
        "désactiver divise les requêtes par deux &mdash; et une "
        "comparaison repose alors sur une réponse unique, sans rien pour "
        "la contre-vérifier.",
    "vision.meld.titel": "Messages supplémentaires",
    "vision.meld.satz":
        "Les deux sont désactivés tant que vous ne les activez pas, et "
        "aucun ne change les alertes existantes : la vision ne peut ni "
        "en déclencher une, ni en annuler une, ni passer outre les voies "
        "visage et corps.",
    "vision.meld.judged_titel":
        "Me prévenir quand un passage a été jugé",
    "vision.meld.judged_satz":
        "Un petit mot par vos canaux habituels une fois le verdict rendu "
        "&mdash; avec le vrai nombre de votes. Il arrive après la fin du "
        "passage, avec un modèle local cela peut être plusieurs minutes "
        "plus tard. Une information, pas une alerte.",
    "vision.meld.alarm_titel":
        "M'alerter quand la vision contredit la reconnaissance corporelle",
    "vision.meld.alarm_satz":
        "Ne se déclenche que lorsqu'une exécution a réellement eu lieu, "
        "que le modèle a répondu, et qu'il n'a malgré tout confirmé "
        "personne. Elle reste silencieuse quand le matériel manquait "
        "tout simplement &mdash; ce ne serait que du bruit. Reconnaître "
        "les personnes que vous lui avez apprises est le point fort de "
        "cette voie, une non-confirmation veut donc dire quelque chose ; "
        "refouler les inconnus est son point faible, la vision ne vote "
        "donc jamais dans ce sens.",
    "vision.kachel.was_key": "vous saisissez une clé API",
    "vision.kachel.was_host": "vous saisissez l'hôte et le port",
    "vision.kachel.was_url":
        "vous saisissez une URL et une clé facultative",
    "vision.kachel.titel": "Où s'exécute le modèle",
    "vision.kachel.satz":
        "Choisissez un fournisseur. Pour les trois fournisseurs nommés, "
        "l'adresse API officielle est déjà intégrée &mdash; vous ne "
        "saisissez que votre clé. Rien n'est envoyé nulle part tant que "
        "vous n'appuyez pas vous-même sur un bouton.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; enregistrée &mdash; laisser vide pour "
        "la conserver",
    "vision.verb.key_pflicht_ph": "collez votre clé ici",
    "vision.verb.key_frei_ph": "seulement si votre serveur en demande une",
    "vision.verb.host": "Hôte",
    "vision.verb.host_ph": "le nom ou l'adresse de cette machine",
    "vision.verb.port": "Port",
    "vision.verb.host_satz":
        "Seulement la machine &mdash; suslik complète lui-même le reste "
        "de l'adresse. Le port d'exemple est celui que llama.cpp utilise "
        "par défaut ; utilisez celui sur lequel le vôtre écoute.",
    "vision.verb.endpunkt": "URL de l'endpoint",
    "vision.verb.endpunkt_satz":
        "C'est un exemple d'endpoint compatible OpenAI &mdash; "
        "remplacez-le par le vôtre si vous utilisez un autre fournisseur.",
    "vision.verb.betriebsart": "Cet endpoint est",
    "vision.verb.betriebsart_extern": "sur Internet",
    "vision.verb.betriebsart_lokal": "dans mon propre réseau",
    "vision.verb.adresse": "Adresse API",
    "vision.verb.adresse_satz":
        "Intégrée &mdash; ici, rien ne peut être mal saisi.",
    "vision.verb.key": "Clé API",
    "vision.verb.key_frei_satz":
        "Facultative ici &mdash; la plupart des serveurs locaux n'en "
        "demandent pas. Appuyez quand même sur le bouton : il récupère "
        "aussi la liste des modèles de votre serveur.",
    "vision.verb.titel": "Connexion",
    "vision.modell.titel": "Modèle",
    "vision.modell.verweigert": "l'endpoint a refusé la connexion",
    # {zeit} vorformatiert aus _zeit() — das Format bleibt in der Route (B19).
    "vision.modell.geprueft": "Vérifié {zeit} auprès de",
    "vision.modell.opt_wahl": "&mdash; choisir &mdash;",
    "vision.modell.ungetestet": "non testé ici",
    "vision.modell.opt_verschollen":
        " — enregistré auparavant, l'endpoint ne le liste plus",
    "vision.modell.wahl_satz":
        "Choisissez-en un dans la liste &mdash; l'annotation à côté de "
        "chaque nom vient de nous, les noms viennent de l'endpoint.",
    "vision.modell.verschollen_satz":
        "Ce modèle est enregistré et toujours utilisé, mais l'endpoint ne "
        "l'a pas listé cette fois. Vérifiez le nom, ou choisissez-en un "
        "dans la liste.",
    "vision.modell.fremde_plattform": "mesuré sur une autre plateforme",
    "vision.modell.kein_rohergebnis":
        "aucun résultat brut archivé pour celui-ci",
    "vision.modell.gemessen": "mesuré {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "Pas mesuré ici &mdash; ce n'est pas un verdict, juste de "
        "l'honnêteté. Lancez le test de connexion ci-dessous avant de "
        "vous y fier.",
    "vision.modell.manuell": "Identifiant de modèle à la main",
    "vision.modell.manuell_ph": "identifiant exact du modèle",
    "vision.modell.manuell_knopf": "Vérifier cet identifiant",
    "vision.modell.manuell_satz":
        "Pour les endpoints qui ne listent pas tout : l'identifiant est "
        "d'abord vérifié par une minuscule requête texte ; rien ne peut "
        "être enregistré sans avoir été vérifié.",
    "vision.prompt.standard_satz":
        "C'est la formulation par défaut, celle qui a été mesurée. Tant "
        "que vous la laissez exactement telle quelle, les verdicts ne "
        "sont pas marqués comme personnalisés.",
    "vision.prompt.titel": "La question que pose suslik",
    "vision.prompt.satz":
        "Vous pouvez modifier la formulation. Le dernier paragraphe est "
        "figé : c'est l'instruction en un mot dont dépend l'analyseur de "
        "réponse, et c'est elle qui a été mesurée.",
    "vision.prompt.knopf_zurueck": "Rétablir la formulation par défaut",
    "vision.zahlen.think": "Désactiver la réflexion du modèle",
    "vision.zahlen.think_satz":
        "Activé par défaut depuis 0.1.0.211 : sur les grilles de "
        "comparaison difficiles, un modèle qui réfléchit peut épuiser son "
        "budget de tokens en discourant, et l'exécution se termine sans "
        "verdict. Les endpoints stricts rejettent cette option ; suslik "
        "répète alors la requête une fois sans elle et le signale.",
    "vision.zahlen.titel": "Limites",
    "vision.zahlen.max_tokens": "Tokens max par réponse",
    "vision.zahlen.timeout": "Délai d'expiration par requête (s)",
    "vision.zahlen.satz":
        "3000 tokens se sont révélés insuffisants sur une exécution "
        "mesurée &mdash; la réponse a été coupée et comptée comme absence "
        "de verdict, et la même question était juste avec 12000. Un "
        "modèle local sur une machine CPU met plusieurs minutes par "
        "requête, un modèle en ligne quelques secondes.",
    "vision.cloud.ziel_fallback": "l'endpoint que vous configurez ci-dessus",
    "vision.cloud.titel": "Envoi d'images vers un service extérieur",
    "vision.cloud.satz":
        "Ces images ne montrent pas que les personnes qui vivent ici : "
        "les cas incertains sont surtout des inconnus &mdash; visiteurs, "
        "livreurs, voisins, passants. C'est vous qui en êtes responsable, "
        "pas l'exploitant du service. Votre confirmation est consignée "
        "dans le journal d'audit avec un horodatage ; revenir à un "
        "modèle local la retire.",
    "vision.cloud.bestaetigung": "Je comprends et je confirme",
    "vision.cloud.bestaetigt": "(confirmé {zeit})",
    "vision.test.treffer": "{n}/2 justes",
    "vision.test.tokens": "{ist} tokens contre {soll}",
    "vision.test.falsch": " (faux)",
    # ZITAT-FOLGE: js.vision.dirty_text UND js.vision.prompt_zurueck
    # zitieren diesen Knopf WOERTLICH und VOLL (« Enregistrer la
    # connexion ») — beim Umbenennen beide nachziehen.
    "vision.save.knopf": "Enregistrer la connexion",
    "vision.save.dirty":
        "modifications non enregistrées &mdash; la reconnaissance utilise "
        "toujours la connexion enregistrée",
    "vision.test.titel": "Tester cette connexion",
    "vision.test.knopf": "Lancer le test",
    "vision.test.nicht_gelaufen": "pas encore exécutée",
    "vision.test.stufe1": "accessibilité",
    "vision.test.stufe2": "choix forcé",
    "vision.test.stufe3": "audit des tokens",
    "vision.test.ungetestet": "Pas encore testé.",
    "vision.test.letzter": "Dernière exécution {zeit} auprès de",
    "vision.galerien.stand_gut": "validée {zeit} &middot; {zellen} cases",
    "vision.galerien.pruefen": "à regarder de près",
    "vision.galerien.keine": "pas encore de galerie",
    "vision.galerien.zu_wenig":
        "pas encore assez d'images de corps validées ({n} utilisables)",
    "vision.galerien.knopf_auffrischen": "L'actualiser",
    "vision.galerien.knopf_bauen": "Composer une galerie",
    "vision.galerien.zahl": "{n} images utilisables &middot; {reihen}",
    "vision.galerien.titel": "Galeries",
    "vision.galerien.stand":
        "{n} galeries prêtes ({min} requises) &mdash; la vision en a "
        "besoin d'au moins deux, parce qu'elle compare toujours une "
        "personne à une autre.",
    "vision.galerien.satz":
        "Seules les personnes avec un modèle de personne appris peuvent "
        "avoir une galerie ; celle-ci est composée des images de corps "
        "que vous avez déjà validées. La vision ne juge que des "
        "personnes qui en ont une, et elle le dit sur le verdict.",
    # --- routes/visiontest.py ---
    # Wortgleich mit nav.erkennungstest (Linktext==Seitentitel).
    "visiontest.titel": "Test de reconnaissance",
    "visiontest.kopf.satz":
        "Visage et personne sont lus depuis ce qui a été consigné sur le "
        "moment &mdash; rien n'est recalculé. La vision, elle, s'exécute "
        "maintenant, exactement par la même voie qu'en fonctionnement "
        "normal.",
    # Frueher Modulkonstante KOSTEN — §8.12: t() nie auf Modulebene.
    "visiontest.kosten":
        "Une exécution de test coûte de vraies requêtes, exactement "
        "comme le fonctionnement normal : tout le passage entre comme "
        "une seule grille de candidats, et chaque paire de galeries "
        "comparée coûte deux requêtes, parce que chaque question est "
        "posée à nouveau avec les galeries permutées. Elle compte comme "
        "un clic manuel, elle n'entame donc pas votre limite quotidienne "
        "&mdash; mais sur un endpoint payant c'est de l'argent, et sur "
        "un modèle local en CPU cela prend plusieurs minutes.",
    "visiontest.wer.niemand": "personne de reconnu",
    # EN-Klammerformen bleiben EINE Form je Schluessel (§8.18).
    "visiontest.wahl.kachel_zahlen":
        "{events} événements &middot; {kameras} caméra(s)",
    "visiontest.wahl.vision_fertig": " &middot; vision effectuée",
    "visiontest.wahl.titel": "1 &middot; Quel passage",
    "visiontest.wahl.leer":
        "Aucun passage consigné pour l'instant. Dès que quelqu'un "
        "traverse la propriété, son passage apparaît ici.",
    "visiontest.wahl.kopf_zahlen":
        "{events} événement(s) &middot; {kameras} caméra(s)",
    "visiontest.wahl.anderer": "choisir un autre passage",
    "visiontest.wahl.titel_offen": "1 &middot; Choisir un passage",
    "visiontest.wahl.anzahl": "{n} passage(s) récent(s)",
    "visiontest.wahl.satz":
        "Les passages les plus récents, regroupés exactement comme sur "
        "la page Aujourd'hui.",
    "visiontest.gesicht.kein_match": "sans correspondance",
    "visiontest.gesicht.gezeigt":
        "{gezeigt} image(s) affichée(s) sur {gesamt}",
    "visiontest.gesicht.ohne_bild":
        "{fehlt} des {unbek} événement(s) sans correspondance n'ont "
        "conservé aucune image",
    "visiontest.gesicht.kein_bild":
        "aucune image de visage conservée pour ce passage",
    "visiontest.gesicht.keines": "aucun visage connu",
    "visiontest.gesicht.zeile": "{person} &middot; {events} événement(s)",
    # {best} vorformatiert (:.2f) aus der Route (§8.8).
    "visiontest.gesicht.best": " &middot; meilleur {best}",
    "visiontest.gesicht.unbekannt":
        "{n} événement(s) avec un visage sans correspondance",
    "visiontest.gesicht.titel": "Visage",
    "visiontest.gesicht.quelle":
        "comparaison d'embeddings avec vos visages de référence &mdash; "
        "d'après ce qui a été consigné pour ce passage",
    "visiontest.koerper.kandidaten":
        "candidats, aucun au-dessus de la règle : {liste}",
    "visiontest.koerper.nichts": "rien d'évalué",
    "visiontest.koerper.zeile":
        "{klasse} &middot; score {score} sur {schwelle} &middot; {quelle}",
    "visiontest.koerper.bild_weg": "image expirée",
    "visiontest.koerper.titel": "Personne",
    "visiontest.koerper.quelle":
        "embedding DINOv2 + classifieur sur les images évaluées de ce "
        "passage",
    "visiontest.log.warte":
        "en attente du modèle &mdash; cette page s'actualise d'elle-même",
    "visiontest.log.titel": "Ce qui s'est passé",
    "visiontest.gitter.alt": "la grille de candidats de cette exécution",
    "visiontest.gitter.bildunterschrift":
        "l'image réellement montrée au modèle",
    "visiontest.gitter.zeile":
        "grille de candidats : {n} case(s) de ce passage, soumises en "
        "UNE seule image",
    "visiontest.gitter.luecken": " ({n} case(s) restées vides)",
    "visiontest.runden.kein_votum": "aucun vote &mdash; {grund}",
    "visiontest.runden.paar": "{a} contre {b}",
    "visiontest.nach.laeuft": "Nouvelle analyse de ce passage en cours",
    "visiontest.nach.stand":
        "{fertig} des {gesamt} événements traités &mdash; les images "
        "évaluées sont rassemblées en chemin, cela prend quelques "
        "minutes. C'est silencieux : aucune alerte, aucune notification. "
        "Cette page s'actualise d'elle-même.",
    "visiontest.nach.titel": "Rien n'a été conservé pour ce passage",
    "visiontest.nach.satz":
        "L'analyser à nouveau fait revenir les images évaluées &mdash; "
        "et cela alimente les trois voies, pas seulement la vision. Cela "
        "relance une fois l'analyse ordinaire sur les événements de ce "
        "passage : silencieuse, sans alertes, et elle attend la "
        "reconnaissance en direct au lieu de la bousculer.",
    "visiontest.nach.knopf": "Analyser ce passage à nouveau",
    "visiontest.felder.zellen": "cases de la grille pour cette exécution",
    "visiontest.felder.voten":
        "confirmations nécessaires pour cette exécution",
    "visiontest.felder.doppel":
        "demander chaque paire deux fois (test de permutation)",
    "visiontest.felder.satz":
        "Les trois ne valent que pour CETTE exécution &mdash; rien n'est "
        "enregistré et le fonctionnement normal garde ses propres "
        "paramètres. Ce passage a {material} image(s) utilisable(s) "
        "&mdash; demander plus de cases que cela ne pose aucun problème, "
        "la grille devient simplement plus petite. {galerien} galeries "
        "validées permettent au plus {voten_max} comparaison(s). Avec le "
        "test de permutation, une comparaison coûte deux requêtes ; sans "
        "lui, une seule &mdash; et elle repose alors sur une réponse "
        "unique.",
    "visiontest.laeufe.abgebrochen": "interrompue (le service a redémarré)",
    "visiontest.laeufe.kein_urteil": "aucun verdict",
    "visiontest.laeufe.von": "sur {n}",
    "visiontest.laeufe.ohne_tausch": "sans permutation",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} en attente",
    "visiontest.laeufe.titel": "Exécutions sur ce passage",
    "visiontest.laeufe.kopf_wann": "quand",
    "visiontest.laeufe.kopf_zellen": "cases",
    "visiontest.laeufe.kopf_noetig": "requis",
    "visiontest.laeufe.kopf_backend": "backend",
    "visiontest.laeufe.kopf_urteil": "verdict",
    "visiontest.laeufe.kopf_voten": "votes",
    "visiontest.laeufe.kopf_anfragen": "req.",
    "visiontest.laeufe.kopf_zeit": "durée",
    "visiontest.laeufe.satz":
        "Les plus récentes d'abord. Seulement ce qui a réellement tourné "
        "&mdash; la liste vient du journal propre à ce passage et "
        "disparaît avec lui.",
    "visiontest.vision.titel": "Vision",
    "visiontest.vision.quelle_kurz":
        "un modèle de vision qui compare ce passage à vos galeries",
    "visiontest.vision.unkonfiguriert": "non configurée",
    "visiontest.vision.attr_nichts": "rien à comparer pour l'instant",
    "visiontest.vision.knopf": "Lancer la vision sur ce passage",
    "visiontest.vision.nichts_satz":
        "rien à comparer pour l'instant &mdash; analysez d'abord ce "
        "passage à nouveau (bouton ci-dessus)",
    "visiontest.vision.laeuft_satz":
        "une exécution est en cours &mdash; le journal ci-dessous "
        "s'allonge au fil du travail",
    "visiontest.vision.startet":
        "démarrage &mdash; rien de signalé pour l'instant",
    "visiontest.vision.quelle":
        "choix forcé face à vos galeries : tout le passage entre comme "
        "UNE seule grille de candidats, et chaque paire est demandée "
        "deux fois avec les galeries permutées",
    "visiontest.vision.nicht_gelaufen": "pas exécutée sur ce passage",
    "visiontest.vision.verglichen":
        "a comparé {a} à {b} &mdash; cela ne dit rien de qui que ce soit "
        "d'autre",
    "visiontest.vision.abgebrochen":
        "exécution interrompue &mdash; le service a redémarré",
    "visiontest.vision.kein_urteil": "aucun verdict &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten} des {bilder} comparaison(s) ont donné une réponse "
        "&middot; {anfragen} requêtes &middot; {dauer} s &middot; "
        "exécution {zeit}",
    "visiontest.vision.reihenfolge": " &middot; ordre : {quelle}",
    "visiontest.vision.custom_prompt": " &middot; question personnalisée",
    "visiontest.drei.titel": "2 &middot; Ce que disent les trois voies",
    "visiontest.drei.satz":
        "Même passage, trois jugements indépendants. Ils ont le droit de "
        "diverger &mdash; c'est tout l'intérêt de les regarder ensemble.",
    # --- routes/visionwizard.py ---
    "visionwizard.schritt.person": "choisir une personne",
    "visionwizard.schritt.groesse": "choisir une taille",
    "visionwizard.schritt.vorschlag": "vérifier la proposition",
    "visionwizard.schritt.abnahme": "valider",
    # Wortgleich mit titel.vision_galerie (Seitentitel der Galerie-Seite).
    "visionwizard.titel": "Composer une galerie",
    "visionwizard.kopf.satz":
        "Une galerie est une petite grille d'images d'une même personne "
        "&mdash; c'est à elle que le modèle de vision compare une "
        "nouvelle image. Elle se compose d'images de corps que vous avez "
        "déjà validées ; rien de nouveau n'est enregistré et aucune "
        "vidéo n'est ouverte.",
    "visionwizard.person.stand_gut": "galerie validée {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} images utilisables &mdash; pas encore assez pour une "
        "galerie. Lancez l'apprentissage de la personne sur plus de "
        "passages.",
    "visionwizard.person.max_gitter":
        "plus grande grille possible avec ce matériel : {n}",
    "visionwizard.person.titel": "1 &middot; Quelle personne",
    "visionwizard.person.satz":
        "Seules les personnes avec un modèle de personne appris "
        "apparaissent ici, et les nombres indiqués ne comptent que les "
        "images qui passent le filtre de taille (au moins 350 pixels de "
        "haut) &mdash; pas tout ce qui a jamais été collecté.",
    "visionwizard.groesse.zellen": "{n} cases",
    "visionwizard.groesse.titel": "2 &middot; Combien d'images",
    "visionwizard.zelle.leer":
        "plus aucune image pour cette rangée &mdash; et plus rien à "
        "emprunter non plus",
    # {reihe} = REIHEN_ANZEIGE-Wort (noch englisch, zentrale Quelle).
    "visionwizard.zelle.geliehen": "de la rangée {reihe}",
    "visionwizard.zelle.knopf_weg": "ne convient pas",
    "visionwizard.reihe.geliehen":
        "{n} remplies depuis une autre vue &mdash; pas assez d'images "
        "propres pour la vue {reihe}",
    "visionwizard.reihe.luecken":
        "{n} case(s) n'ont pas pu être remplies du tout",
    "visionwizard.reihe.spreizung": "{tage} jour(s), {kameras} caméra(s)",
    "visionwizard.reihe.kopf": "vue {reihe}",
    "visionwizard.reihe.eigene": "{eigene} sur {gesamt} de cette vue",
    "visionwizard.vorschlag.abgelehnt":
        "{n} image(s) que vous aviez écartées restent mémorisées et ne "
        "reviendront pas.",
    "visionwizard.vorschlag.titel": "3 &middot; Cela convient-il ?",
    "visionwizard.vorschlag.grenze":
        "Limite honnête : ce sont des mesures de l'image, pas de "
        "l'instant. Une image où quelqu'un s'attache les cheveux ou se "
        "penche leur paraît bonne à toutes &mdash; c'est à cela que "
        "servent vos yeux.",
    "visionwizard.vorschlag.knopf": "Valider cette galerie",
    "visionwizard.vorschlag.kopie_satz":
        "La validation copie ces images dans le dossier de la galerie. "
        "Dès lors, la galerie est figée : supprimer un original plus "
        "tard ne peut pas y percer de trous &mdash; suslik vous demande "
        "seulement de la valider à nouveau.",
    "visionwizard.fertig.geliehen": " &middot; empruntée",
    "visionwizard.fertig.titel": "Galerie validée",
    "visionwizard.fertig.stand": "{zellen} cases, validée {zeit}.",
    "visionwizard.fertig.satz":
        "Ce sont des copies dans le dossier de la galerie, avec "
        "l'origine de chaque image (session, fichier, somme de contrôle) "
        "notée à côté. Elles voyagent avec votre sauvegarde.",
    "visionwizard.fertig.knopf_neu":
        "La recomposer depuis le matériel actuel",
    "visionwizard.fertig.knopf_zurueck": "Retour à Détection par vision",
    "visionwizard.neu.titel": "Nouveau matériel disponible",
    "visionwizard.neu.satz":
        "Rien ne change tout seul &mdash; la galerie que vous avez "
        "validée reste exactement telle quelle jusqu'à ce que vous en "
        "composiez et validiez une nouvelle.",
    # --- routes/personwizard.py ---
    # {wer}-Werte muessen hinter « à / de / pour » funktionieren (auch
    # Personennamen landen dort) — deshalb « la catégorie intrus ».
    "personwizard.wer.alle": "toutes les personnes connues",
    "personwizard.wer.fremde": "la catégorie intrus",
    "personwizard.titel": "Apprendre des personnes — reconnaissance corporelle",
    "personwizard.kopf.satz":
        "Une seconde voie de reconnaissance, indépendante : elle apprend "
        "à quoi ressemble une personne dans son ENSEMBLE (carrure, "
        "cheveux, posture) pour reconnaître les membres du foyer même "
        "quand aucun visage n'est visible.",
    "personwizard.kopf.wie_titel":
        "Comment ça marche — vous gardez la main",
    "personwizard.kopf.schritt1":
        "1 · Vous choisissez combien d'événements parcourir et QUI "
        "apprendre (une personne, ou toutes les personnes connues).",
    "personwizard.kopf.schritt2":
        "2 · La session collecte des images du corps entier depuis vos "
        "propres enregistrements. Une image n'est rattachée à une "
        "personne que lorsqu'un passage confirmé par le visage le prouve "
        "— volontairement prudent.",
    "personwizard.kopf.schritt3":
        "3 · VOUS examinez chaque image collectée ; un clic écarte celle "
        "qui est fausse. Rien n'est appris sans votre validation.",
    "personwizard.kopf.schritt4":
        "4 · L'entraînement s'exécute ensuite localement en quelques "
        "secondes, et un seuil de décision est mesuré pour que les "
        "intrus restent en dessous.",
    "personwizard.kopf.tempo":
        "Un mot sur la vitesse : la collecte s'exécute pour l'instant "
        "sur le CPU, une session peut donc prendre un peu de temps "
        "(environ 15&ndash;30 s par événement). Son portage vers le "
        "GPU/NPU est prévu pour une version ultérieure.",
    "personwizard.kopf.warum":
        "Pourquoi au moins une personne d'abord : cette voie ne peut "
        "distinguer les personnes qu'après avoir appris — et vous avoir "
        "laissé examiner — à quoi ressemble au moins un membre du foyer. "
        "D'ici là, la reconnaissance corporelle reste DÉSACTIVÉE et "
        "n'envoie jamais d'alerte. Quand elle alertera plus tard "
        "(Pushover/Telegram), le message sera marqué comme venant de la "
        "reconnaissance corporelle, pas de la reconnaissance faciale.",
    "personwizard.vorb.titel": "Préparation de la session &hellip;",
    "personwizard.vorb.zeile":
        "rattachement des {n} derniers événements à {wer} via les "
        "passages confirmés",
    "personwizard.vorb.satz":
        "Cela prend une à deux minutes — la page s'actualise "
        "d'elle-même, la collecte démarre juste après.",
    "personwizard.ernte.stand":
        "{events}/{von} événements · {bilder} images collectées",
    "personwizard.ernte.startet": "démarrage …",
    "personwizard.ernte.titel":
        "Une session d'apprentissage de la personne est en cours",
    "personwizard.ernte.zeile": "apprentissage de {wer} · {stand}",
    "personwizard.ernte.satz":
        "Cette page s'actualise d'elle-même. Une nouvelle session pourra "
        "être lancée dès que celle-ci sera terminée.",
    "personwizard.ernte.knopf_abbruch": "Interrompre la session",
    "personwizard.ernte.abbruch_hinweis":
        "les images collectées sont conservées",
    "personwizard.unterbrochen.titel":
        "La dernière session a été interrompue",
    "personwizard.unterbrochen.satz":
        "Probablement un redémarrage du service. Relancez la même "
        "session ci-dessous — les événements déjà collectés sont ignorés "
        "automatiquement (reprise), rien n'est perdu.",
    "personwizard.abnahme.titel":
        "Dernière session terminée — à vous d'examiner",
    "personwizard.abnahme.zeile":
        "{n} images collectées pour {wer} (session {lauf}).",
    "personwizard.abnahme.knopf": "Examiner les images maintenant",
    "personwizard.abnahme.hinweis":
        "terminez l'examen pour débloquer la session suivante",
    "personwizard.abnahme.knopf_verwerfen": "Abandonner cette session",
    "personwizard.abnahme.verwerfen_hinweis":
        "mauvais résultat ? tout jeter",
    "personwizard.leer.verwaist":
        "Ignorés volontairement : {liste} — ces noms ont été supprimés "
        "de votre liste de personnes ; leurs anciens événements "
        "confirmés restent dans l'historique mais ne sont pas "
        "collectés.",
    "personwizard.leer.titel":
        "Session terminée sans images — voici pourquoi",
    "personwizard.leer.satz":
        "Rien n'a été modifié ; vous pouvez lancer une autre session "
        "ci-dessous à tout moment.",
    "personwizard.fertig.verwaist":
        "Ignorés volontairement : {liste} — personnes supprimées ; "
        "leurs anciens événements confirmés ne sont pas collectés.",
    "personwizard.fertig.fremd":
        "{n} images d'intrus confirmés versées dans la réserve d'intrus "
        "— le prochain entraînement les utilise aussitôt.",
    "personwizard.fertig.titel": "Examen terminé — matériel intégré",
    "personwizard.fertig.zeile":
        "{abgenommen} images validées comme matériel d'apprentissage, "
        "{verworfen} écartées (session {lauf}).",
    "personwizard.fertig.knopf": "Voir le matériel appris",
    "personwizard.fehler.titel": "La dernière session a échoué",
    "personwizard.auswahl.opt_alle": "Toutes les personnes connues",
    "personwizard.auswahl.opt_fremde":
        "Intrus — collecter des images d'intrus",
    "personwizard.auswahl.titel": "Qui apprendre",
    "personwizard.auswahl.satz":
        "Choisissez une personne à examiner par petits lots ciblés — ou "
        "toutes à la fois. Les personnes viennent de votre bibliothèque "
        "de références ; en apprendre une à la fois raccourcit "
        "l'examen.",
    "personwizard.auswahl.fremde_satz":
        "Intrus : la collecte parcourt les passages où personne n'a été "
        "reconnu (passages uniquement côté rue, visiteurs non "
        "confirmés). Vous confirmez lors de l'examen lesquels sont "
        "réellement des intrus — ils rejoignent la réserve d'intrus et "
        "affinent le seuil de décision.",
    "personwizard.umfang.knopf_letzte": "les {n} derniers",
    "personwizard.umfang.attr_eigen": "N au choix",
    "personwizard.umfang.knopf_go": "OK",
    "personwizard.umfang.titel": "Étendue (événements, pas jours)",
    "personwizard.umfang.satz":
        "Commencez petit (50) — vous examinerez chaque image collectée à "
        "la main.",
    "personwizard.bilanz.ohne":
        "les {n} derniers événements de personne pour {wer} — le bilan "
        "qui fait foi est calculé à la création de la session",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/nach rahmen die
    # hervorgehobene Zahl, Rand-Leerzeichen gehoeren zum Wert.
    "personwizard.bilanz.zahl_vor":
        "les {n} derniers événements de personne · ",
    "personwizard.bilanz.zahl_nach":
        " peuvent être rattachés à {wer} via les passages confirmés",
    "personwizard.bilanz.fremd": " · {n} candidats intrus",
    "personwizard.bilanz.erkl_fremd":
        "Les candidats sont les passages où personne n'a été reconnu — "
        "passages uniquement côté rue et visiteurs non confirmés. Tout "
        "reste une PRÉSOMPTION jusqu'à votre examen ; marquez-y "
        "quiconque n'est PAS un intrus.",
    "personwizard.bilanz.erkl":
        "Le rattachement est prudent : seuls comptent les passages avec "
        "exactement une personne confirmée par le visage. Tout ce que "
        "vous verrez ensuite peut être écarté d'un clic.",
    "personwizard.bilanz.titel": "Votre sélection",
    "personwizard.bilanz.knopf": "Créer cette session",
    "personwizard.review.stempel": "FAUX",
    "personwizard.review.h_fremde": "Intrus",
    "personwizard.review.frage_fremd":
        "cliquez sur chaque image qui n'est PAS un intrus (un membre du "
        "foyer, un visiteur connu) ou qui est inutilisable. Un second "
        "clic annule. Tout est enregistré aussitôt ; les images non "
        "marquées sont intégrées comme intrus confirmés et affinent le "
        "seuil de décision.",
    "personwizard.review.frage":
        "cliquez sur chaque image FAUSSE (pas cette personne, ou "
        "inutilisable). Un second clic annule. Tout est enregistré "
        "aussitôt ; les images non marquées comptent comme validées.",
    "personwizard.review.titel": "Examiner la collecte",
    "personwizard.review.kopf": "Session {lauf} — {frage}",
    # Der Zeilenumbruch ist Teil des Originals (Template-Literal) und
    # bleibt fuer die Byte-Treue im Wert.
    "personwizard.review.zurueck": "&larr; retour à\nl'assistant",
    "personwizard.review.knopf_fertig":
        "Terminer l'examen — intégrer les images validées",
    "personwizard.kontrolle.sammeln_titel": "Le mode collecte est ACTIVÉ",
    "personwizard.kontrolle.sammeln_rest":
        " — chaque image évaluée est conservée 30 jours pour que vous "
        "puissiez vérifier les décisions plus tard. Comptez environ "
        "20&ndash;40 Mo par jour.",
    "personwizard.kontrolle.schlank_titel": "Mode allégé (par défaut)",
    "personwizard.kontrolle.schlank_rest":
        " — les images évaluées ne vivent que pendant un passage ; "
        "ensuite ne restent que l'image gagnante et le journal des "
        "verdicts ci-dessous. C'est le mode par défaut d'une "
        "installation neuve, respectueux de la vie privée.",
    # Wortgleich mit nav.person_kontrolle (Linktext==Seitentitel).
    "personwizard.kontrolle.titel": "Images évaluées",
    "personwizard.kontrolle.satz":
        "Ce que la reconnaissance corporelle a réellement regardé, un "
        "bloc par passage : l'image qu'elle a évaluée, la classe "
        "retenue, le score, et d'où vient l'image. Utile quand une "
        "personne a été manquée, ou que quelqu'un a été reconnu à tort.",
    "personwizard.kontrolle.leer_titel": "Rien de consigné pour l'instant",
    "personwizard.kontrolle.tag_fremd": "intrus",
    "personwizard.kontrolle.tag_drueber": "au-dessus du seuil",
    "personwizard.kontrolle.tag_drunter": "sous le seuil",
    "personwizard.kontrolle.schwelle": " &middot; seuil {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} évaluées, {n} image conservée",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} évaluées, {n} images conservées",
    "personwizard.tabelle.fremd_zeile": "Intrus (classe supplémentaire)",
    "personwizard.tabelle.kein_fremd":
        "Pas encore de classe d'intrus — la reconnaissance fonctionne "
        "bien mieux quand il y en a une : les images d'intrus "
        "confirmés apprennent au modèle ce qui n'a PAS sa place et "
        "calibrent le seuil de décision.",
    "personwizard.tabelle.q_eichung": "mesuré",
    "personwizard.tabelle.q_user": "défini par vous",
    "personwizard.tabelle.q_standard": "valeur par défaut intégrée",
    "personwizard.tabelle.f_modell": "Modèle actif",
    "personwizard.tabelle.f_schwelle": "Seuil",
    "personwizard.tabelle.f_scharf": "Armé",
    "personwizard.tabelle.scharf_ja": "OUI",
    "personwizard.tabelle.scharf_ja_rest": " — juge en direct",
    "personwizard.tabelle.scharf_nein": "non — pas armé",
    "personwizard.tabelle.konf_vor":
        "Plus grande confusion entre groupes lors du calibrage : ",
    "personwizard.tabelle.konf_nach":
        " — le score le plus fort qu'une image ait atteint pour le "
        "MAUVAIS groupe ; plus il est proche de 1, plus les deux "
        "groupes sont proches.",
    "personwizard.tabelle.titel": "Groupes appris",
    "personwizard.karte.scharf": "Armé",
    "personwizard.karte.unscharf": "Pas encore armé",
    "personwizard.karte.fehler":
        "Dernière tentative d'entraînement EN ÉCHEC : {fehler} — cette "
        "carte montre le modèle précédent.",
    # Wortgleich mit nav.person_modell (Linktext==Seitentitel).
    "personwizard.karte.titel": "État du modèle",
    "personwizard.karte.zeile":
        "entraîné {wann} en {dauer} s — {bilder} images : {je} · "
        "{modell} · ",
    "personwizard.karte.link": "détails",
    "personwizard.bestand.titel":
        "Images de corps — ce qui a été appris",
    "personwizard.bestand.satz":
        "Images du corps entier validées, par personne. Choisissez un "
        "groupe ci-dessous pour voir ses images ; supprimez une image "
        "isolée (&times; sur la tuile) — une nouvelle session peut "
        "toujours les collecter à nouveau ensuite. Les suppressions "
        "prennent effet au prochain entraînement.",
    "personwizard.bestand.leer_titel": "Aucun matériel validé pour l'instant",
    "personwizard.bestand.stark_titel": "Ce qui rend ce modèle fort",
    "personwizard.bestand.chip_fremde": "Intrus ({n})",
    "personwizard.bestand.zeigen_titel": "Afficher les images de",
    "personwizard.bestand.zeigen_satz":
        "Choisissez un groupe — ses images s'ouvrent ci-dessous, les "
        "plus récentes d'abord.",
    "personwizard.bestand.marker_tage.eins":
        "seulement {n} jour — la reconnaissance progresse surtout si "
        "les images couvrent plus de jours, de tenues et d'éclairages",
    "personwizard.bestand.marker_tage.viele":
        "seulement {n} jours — la reconnaissance progresse surtout si "
        "les images couvrent plus de jours, de tenues et d'éclairages",
    "personwizard.bestand.attr_loeschen": "supprimer cette image",
    "personwizard.bestand.z_bilder": "{n} images",
    "personwizard.bestand.z_tage.eins": "{n} jour",
    "personwizard.bestand.z_tage.viele": "{n} jours",
    "personwizard.bestand.z_kameras.eins": "{n} caméra",
    "personwizard.bestand.z_kameras.viele": "{n} caméras",
    "personwizard.modell.titel": "Modèle de personne — état",
    "personwizard.modell.satz":
        "Le modèle de la reconnaissance corporelle, entraîné à partir de "
        "vos images validées. Il se réentraîne automatiquement après "
        "chaque examen terminé et après des suppressions.",
    "personwizard.modell.leer_titel": "Pas encore de modèle",
    "personwizard.modell.fremd_keine":
        "aucun pour l'instant — seuil mesuré seulement entre vos "
        "personnes",
    "personwizard.modell.fremd_gesammelt":
        "{n} collectés — il en faut {min} avant qu'ils n'entrent à "
        "l'entraînement et ne calibrent le seuil",
    "personwizard.modell.fremd_geeicht":
        "{n} à l'entraînement · seuil calibré sur de véritables intrus",
    "personwizard.modell.fremd_ungeeicht":
        "{n} à l'entraînement — le calibrage du seuil n'a pas tourné "
        "(voir la note ci-dessous)",
    "personwizard.modell.f_trainiert": "Entraîné",
    "personwizard.modell.f_dauer": "Durée d'entraînement",
    "personwizard.modell.f_modell": "Modèle",
    "personwizard.modell.f_bilder": "Images au total",
    "personwizard.modell.f_personen": "Personnes",
    "personwizard.modell.f_fremd": "Contre-exemples (intrus)",
    "personwizard.modell.scharf_ja": "OUI — évaluation en direct active",
    "personwizard.modell.scharf_nein": "non — pas encore armé",
    "personwizard.modell.fehler":
        "Dernière tentative d'entraînement EN ÉCHEC ({zeit}) : {fehler} "
        "— le modèle affiché ici est le précédent et n'inclut pas vos "
        "derniers changements.",
    "personwizard.modell.aktuell_titel": "Modèle actuel",
    "personwizard.modell.material_titel":
        "Matériel d'apprentissage par personne",
    "personwizard.modell.kopf_person": "personne",
    "personwizard.modell.kopf_bilder": "images validées",
    "personwizard.modell.kopf_anteil": "part",
    "personwizard.modell.summe": "total",
    "personwizard.modell.q_eichung": "mesuré sur votre matériel",
    # {pct} vorformatiert (round) aus der Route (§8.8).
    "personwizard.modell.eich_fremd":
        "Mesuré par validation croisée à {folds} plis sur {n} images "
        "hors entraînement de vos personnes plus {n_fremd} intrus "
        "confirmés : le plus haut niveau de confiance « membre du "
        "foyer » atteint par un véritable intrus était {max} &rarr; "
        "seuil {schwelle} ; {pct} % des images authentiques passent. Le "
        "revers de la médaille : {ueber} de vos propres images "
        "atteindraient ce seuil pour la MAUVAISE personne (au plus fort "
        "{vmax}).",
    "personwizard.modell.eich_intern":
        "Mesuré par validation croisée à {folds} plis sur {n} images "
        "hors entraînement : plus haut niveau de confiance pour une "
        "MAUVAISE personne {max} &rarr; seuil {schwelle} ; {pct} % des "
        "images authentiques passent. Limite honnête : ce calibrage se "
        "fait ENTRE vos personnes apprises — aucun véritable intrus "
        "n'est encore dans le matériel.",
    "personwizard.modell.regeln_titel": "Paramètres du jugement",
    "personwizard.modell.schwelle_vor": "Seuil de décision : ",
    "personwizard.modell.r_fenster": "Fenêtre de déclenchement",
    "personwizard.modell.r_feuer":
        "Événements concordants pour déclencher",
    "personwizard.modell.r_karenz": "Délai après une alerte",
    "personwizard.modell.regeln_satz":
        "Laissez le seuil vide pour suivre automatiquement la valeur "
        "mesurée (elle est remesurée à chaque entraînement). La règle de "
        "déclenchement : alerter seulement après ce nombre d'événements "
        "concordants dans la fenêtre, puis rester silencieux pendant le "
        "délai.",
    "personwizard.modell.knopf_speichern": "Enregistrer les paramètres",
    "personwizard.modell.satz_user":
        "Le seuil de décision est défini par vous ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — le calibrage sur {n} intrus confirmés donnerait {alt}",
    "personwizard.modell.satz_geeicht":
        "Le seuil de décision est calibré sur {n} images d'intrus "
        "confirmés.",
    "personwizard.modell.satz_ungeeicht":
        "Le seuil de décision n'est pas encore calibré sur du matériel "
        "d'intrus — considérez les alertes comme un aperçu et gardez-les "
        "à l'œil.",
    "personwizard.modell.satz_fremd_drop":
        " Un corps que le modèle lit comme un intrus est écarté avant de "
        "pouvoir devenir une correspondance.",
    "personwizard.modell.live_titel": "Fonctionnement en direct",
    "personwizard.modell.live_an":
        "ARMÉ — la voie corps évalue les événements en direct et peut "
        "alerter.",
    "personwizard.modell.live_aus":
        "Pas armé — la voie corps reste silencieuse.",
    "personwizard.modell.live_hinweis":
        "Les alertes portent la mention « reconnaissance corporelle, pas "
        "faciale ».",
    "personwizard.modell.knopf_disarm": "Désarmer",
    "personwizard.modell.knopf_arm": "Armer la reconnaissance corporelle",
    # --- webui/bausteine.py ---
    # Nur die gt_leiste-ANZEIGE-Texte (Speicherwerte und KAT_LABELS
    # bleiben literal, s. en.py-Kommentar). « Intrus » nach F3.
    "baustein.gt.fremd": "Intrus",
    "baustein.gt.kein_mensch": "Aucune personne",
    "baustein.gt.add": "ajouter une personne…",
    "baustein.gt.uebernehmen": "confirmer cette proposition (toutes les personnes citées étaient là)",
    "baustein.gt.fremd_titel": "un inconnu était là (peut figurer à côté des noms)",
    "baustein.gt.unklar_titel": "pas sûr — laisser ouvert",
    "baustein.gt.kein_mensch_titel": "aucune personne dans cet événement (faux déclenchement)",
    "baustein.gt.opak_titel": "un ancien jugement qui ne correspond plus à aucune personne connue — choisissez ? ou un nom pour le remplacer",
    # ---- Route-JS + Meldungen (Stufe 2, Tranche D) ----
    # Uebersetzung der en.py-Tranche D (109 Schluessel): Route-JS (via
    # json.dumps/js_literal injiziert), JSON-msg-Antworten der POST-Handler
    # (antwort.*) und die Konstante->Schluessel-Umzuege. FR-Interpunktion:
    # echtes U+00A0 vor : ; ! ? und in « » (§8.21) — diese Werte laufen
    # durch json.dumps/escapende Pfade, nie &nbsp;. Splits und Grenzen wie
    # im en.py-Abschnittskommentar; Rand-Leerzeichen gehoeren zum Wert.
    # --- routes/lernwizard.py (Zuweisungs-Flaeche + Sichtung) ---
    "lernwizard.zw.js_zaehl_mitte": " sur ",
    "lernwizard.zw.js_zaehl_nach": " images sélectionnées",
    "lernanker.js.uebernimmt": "intégration…",
    "lernanker.js.tag_frage_vor":
        "Paramètres modifiés depuis le nommage :\n",
    "lernanker.js.tag_frage_nach":
        "\nIntégrer quand même avec la sélection nommée ?",
    "lernanker.js.weiter": "enregistré — groupe suivant…",
    "lernanker.js.speichert": "enregistrement…",
    # EN rahmt Namen mit ’…’ — FR nimmt « » mit echtem U+00A0 (§8.21).
    "lernanker.js.koll_vor": "« ",
    "lernanker.js.koll_mitte":
        " » correspond à la personne existante « ",
    "lernanker.js.koll_nach":
        " » — ajouter plutôt ce groupe à cette personne ?",
    "lernwizard.zw.js_gespeichert_vor": "enregistré sous ",
    "lernwizard.zw.js_gespeichert_nach": " — vérification des photos …",
    "lernwizard.sicht.js_fehl":
        "échec de la vérification — rechargez pour réessayer",
    "lernwizard.zw.js_verbergen":
        "Masquer les {n} autres photos vérifiées",
    "lernwizard.zw.js_zeigen": "Afficher toutes les {n} photos vérifiées",
    # --- routes/qualitaet.py ---
    "qualitaet.galerie.js_gewaehlt": " sélectionnées",
    # --- routes/lernanker.py (nur dort) ---
    "lernanker.js.alle_fertig":
        "Tous les groupes sont traités — les photos nommées comptent "
        "désormais pour la reconnaissance.",
    # --- routes/vision.py (Hand-ID-Script) ---
    "vision.modell.js_id_fehlt": "saisissez d'abord un identifiant",
    "vision.modell.js_prueft": "vérification …",
    "vision.modell.js_fehler": "erreur",
    # --- routes/personwizard.py (Review-Script + Schalter) ---
    "personwizard.review.js_zaehl": " sur {n} marquées comme fausses",
    "personwizard.review.js_frage_vor": "Terminer l'examen ? ",
    "personwizard.review.js_frage_mitte":
        " images seront intégrées comme matériel d'apprentissage, ",
    "personwizard.review.js_frage_nach": " écartées.",
    "personwizard.modell.js_fehler": "erreur ",
    # --- verifyd.py POST-Antworten (antwort.*, Nutzungs-Reihenfolge) ---
    "antwort.person_entfernt":
        "suppression de {person} ({n} images de référence déplacées "
        "vers la corbeille — récupérables)",
    "antwort.person_name_ungueltig": "nom invalide",
    "antwort.person_unbekannt": "personne inconnue",
    "antwort.pruefung_gestartet": "vérification lancée",
    "antwort.reorg_los":
        "Réorganisation en cours (revérification de la collecte + "
        "reconstruction des groupes, 1-2 min, puis rechargez les pages)",
    "antwort.reorg_laeuft":
        "Une réorganisation est déjà en cours — patientez",
    "antwort.paar_notiert": "noté — cette paire ne sera plus proposée",
    "antwort.unbek_objekt": "marqué comme n'étant pas une personne",
    "antwort.unbek_weg": "Ce groupe n'existe plus (fusionné ou nettoyé entre-temps) ; la carte est retirée.",
    "antwort.unbek_person": "de nouveau parmi les visiteurs",
    "antwort.unbek_gemergt": "{n} groupes fusionnés en un seul",
    # §8.11-Anhang an eine Fachschicht-msg (die Basis bleibt Grenze).
    "antwort.nachpruefung_anhang":
        " — revérification des événements de ce passage en arrière-plan",
    "antwort.sync_wieder": "{n} de retour sur la liste des candidats",
    "antwort.sync_auswahl": "{ab} désélectionnées, {zu} rétablies",
    "antwort.sync_laeuft":
        "une synchronisation est déjà en cours — attendez qu'elle se "
        "termine",
    "antwort.sync_readonly":
        "mode lecture seule : l'écriture des références dans Frigate "
        "est désactivée (voir l'interrupteur de la page Système)",
    "antwort.sync_nichts": "aucune sélection — cochez au moins une image",
    "antwort.frigate_url": "URL de Frigate : {fehler}",
    "antwort.sync_transfer": "transfert en cours ({n} sélectionnées)",
    "antwort.bruecke_hinzu": "{n} image(s) ajoutée(s)",
    "antwort.modell_laedt":
        "chargement du modèle de reconnaissance — quelques secondes …",
    "antwort.refcache_baut":
        "reconstruction de la bibliothèque de références — avec une "
        "grande bibliothèque, cela peut prendre une minute …",
    "antwort.refcache_fehler":
        "la reconstruction de la bibliothèque de références a échoué deux fois "
        "de suite — voir le journal du service (/log) ; la prochaine tentative "
        "aura lieu dans quelques minutes",
    "antwort.cache_aufgeraeumt": "{n} clip(s) supprimé(s), {mb} Mo libérés — cache {cache} Go, {frei} Go libres",
    "antwort.bruecke_nimmt": "la vérification retient {n} image(s)",
    "antwort.bruecke_grenz_zusatz":
        " · {n} images limites affichées non cochées",
    "antwort.bruecke_nur_grenz":
        "rien de clairement utile — {n} image(s) limite(s) gardée(s) en "
        "réserve (identité sûre, qualité d'image seulement "
        "moyenne) ; vous pouvez quand même les prendre",
    "antwort.bruecke_nichts":
        "rien à prendre — aucune nouvelle image utile dans ce passage "
        "(ce n'est pas grave)",
    "antwort.bruecke_undo": "{n} image(s) retirée(s)",
    "antwort.personlauf_kein_review": "aucune session en attente d'examen",
    "antwort.personlauf_kein_lauf": "aucune session active",
    "antwort.events_bereich":
        "le nombre d'événements doit être entre 1 et {max}",
    "antwort.personlauf_aktiv":
        "une session d'apprentissage de la personne est déjà active",
    "antwort.lernlauf_tag_ungueltig": "jour invalide (YYYY-MM-DD)",
    # {phase} ist die interne Phasen-Kennung (sprachneutral, §8.19).
    "antwort.lernlauf_phase":
        "une session est déjà en phase « {phase} » — "
        "interrompez-la d'abord",
    "antwort.lernlauf_beschaeftigt":
        "la session précédente termine encore son événement en cours — "
        "réessayez dans un instant",
    "antwort.lernlauf_schreibfehler":
        "impossible d'écrire l'état de la session : {fehler}",
    "antwort.lernlauf_angelegt": "session créée",
    "antwort.lernlauf_abgebrochen":
        "interrompue — un événement en cours peut encore se terminer en "
        "arrière-plan",
    "antwort.live_nichts": "rien à modifier",
    "antwort.live_nachtests": "{n} test(s) de source s'executent automatiquement l'un apres l'autre ; chaque surveillant demarre des que son test reussit",
    "antwort.live_an": "{ok}/{alle} surveillance(s) démarrée(s)",
    "antwort.live_aus": "{ok}/{alle} surveillance(s) arrêtée(s)",
    "antwort.vision_modell_ok":
        "le modèle a répondu — ajouté à la liste comme vérifié à la "
        "main ; choisissez-le puis enregistrez",
    "antwort.restore_upload_fehlt":
        "téléversement manquant ou trop volumineux",
    "antwort.restore_upload_kaputt": "téléversement tronqué",
    "antwort.backend_unbekannt": "backend inconnu « {backend} »",
    "antwort.kameras_fehlen":
        "caméras Frigate indisponibles : {fehler}",
    "antwort.setup_gespeichert": "Configuration enregistrée — redémarrage",
    "antwort.kameras_gespeichert":
        "{n} caméras enregistrées — redémarrage",
    "antwort.name_ungueltig":
        "nom de personne invalide (2-40 lettres, chiffres, espace, -)",
    "antwort.anker_unbekannt": "point d'ancrage inconnu",
    "antwort.anker_benannt":
        "nommé « {name} » — {n} images sélectionnées, "
        "intégrez-le avec le bouton Intégrer",
    "antwort.anker_nur_unadoptiert":
        "seuls les groupes sans images intégrées peuvent être écartés",
    "antwort.anker_verworfen":
        "supprimé — {n} images effacées",
    "antwort.lauf_id_ungueltig": "identifiant de session invalide",
    "antwort.lauf_aktiv":
        "cette session est encore active — interrompez-la d'abord",
    "antwort.lauf_nichts":
        "rien trouvé pour la session {lauf} — déjà supprimée ?",
    "antwort.lauf_nur_einer":
        "rien à supprimer — il ne reste qu'une seule session",
    "antwort.gruppe_unbekannt": "groupe inconnu ou fermé",
    "antwort.sichtung_laeuft":
        "vérification des photos — quelques secondes …",
    "antwort.anker_unbenannt":
        "le point d'ancrage n'est pas nommé (ou inconnu)",
    "antwort.benennen_mismatch":
        "votre sélection ne correspond à aucune image de ce groupe — "
        "rechargez la page et cochez à nouveau les images",
    "antwort.adopt_nichts":
        "aucune sélection — cochez au moins une image à intégrer",
    "antwort.adopt_phantom":
        "la déduplication n'a trouvé que des références qui n'existent "
        "plus sur le disque — réessayez l'intégration ; si cela "
        "persiste, signalez-le",
    "antwort.adopt_gedeckt":
        "déjà couvert — les {n} image(s) sélectionnée(s) sont quasi "
        "identiques aux références existantes de {person} ; groupe "
        "marqué comme intégré, rien n'a été copié",
    # §8.10-Plural-Split: frueher {'s' if n != 1} im f-String, jetzt t_n.
    "antwort.adopt_fertig.eins":
        "{n} référence intégrée pour « {person} »",
    "antwort.adopt_fertig.viele":
        "{n} références intégrées pour « {person} »",
    "antwort.adopt_skip": ", {n} ignorées car quasi identiques",
    "antwort.adopt_watchdog":
        " — garde-fou de dérive en cours (page Système)",
    "antwort.areas_gespeichert.eins": "{n} secteur enregistré",
    "antwort.areas_gespeichert.viele": "{n} secteurs enregistrés",
    # text/plain-Antwort der /video- und /clip-Routen (Tranche-B-Rest).
    "antwort.clip_weg":
        "Séquence absente du cache — rétention de {tage} jours",
    # --- Konstante->Schluessel (Kennung/Anzeige-Trennung, Paket 3) ---
    # 3a: {hinweis}-Wert; muss hinter « ce fichier … » (careful_config)
    # UND « cette archive … » (voll.careful) tragen — deshalb die
    # genuslose Fassung « à traiter comme un mot de passe ».
    "system.backup.hinweis":
        "contient vos clés API — à traiter comme un mot de passe",
    # 3b: Anzeige-Woerter der Galerie-Reihen; Kennungen (vorn/seitlich/
    # hinten/unklar) bleiben Store-/JSON-Werte. Muessen in den Rahmen
    # « vue {reihe} » und « de la rangée {reihe} » funktionieren.
    "visiongalerie.reihe.vorn": "de face",
    "visiongalerie.reihe.seitlich": "de profil",
    "visiongalerie.reihe.hinten": "de dos",
    "visiongalerie.reihe.unklar": "indéterminée",
    # 3c: Kategorie-ANZEIGE (bausteine.kat_wort) — Meldetexte lesen
    # weiter KAT_LABELS englisch. fremd_verdacht ist die VERDACHTS-Stufe
    # und etikettiert nach F3 die SITUATION, nicht die Person:
    # « Présence inhabituelle » (bestaetigte Stufe: « intrusion »).
    # « Intrus » bleibt dem Personen-Label vorbehalten (baustein.gt).
    "baustein.kat.erkannt": "Reconnu",
    "baustein.kat.fremd_verdacht": "Présence inhabituelle",
    "baustein.kat.unbekannt_schwach": "Inconnu (faible)",
    "baustein.kat.fehler": "Erreur",
    "baustein.kat.no_person":
        "Aucune personne trouvée (probablement un faux déclenchement)",
    "baustein.kat.uebersprungen": "Ignoré au démarrage",
    "baustein.kat.deckung": "Correspondance",
    "baustein.kat.widerspruch": "Contradiction",
    "baustein.kat.frigate_nur": "Frigate seul",
    "baustein.kat.wir_nur": "suslik seul",
    "baustein.kat.beide_unknown": "Inconnu des deux côtés",
    # 3d: Wortstufen-ANZEIGE (bausteine.stufe_wort) — klein im Satzfluss,
    # Rahmen event.ours_zeile « {person} — {stufe} (visible dans …) ».
    "baustein.stufe.clear": "correspondance nette",
    "baustein.stufe.narrow": "juste au-dessus de la barre",
    "baustein.stufe.below": "sous la barre",
    "baustein.stufe.none": "aucune correspondance",
    # ---- Anleitungen /hilfe (Stufe 3) ----
    # Aufbau wie en.py: je Seite ein Titel (t) + die <p>-Absaetze als
    # t_html-Schluessel (Tag-Folge identisch zu en.py, texte_pruefen).
    # ZITAT-KOPPLUNGEN wortgleich zu den fr-Werten: Choisir les caméras
    # (erkennung.live.knopf_kameras), page Notifications
    # (benachrichtigungen.titel), page Synchronisation Frigate
    # (nav.sync_auswahl), Gérer les personnes / Enregistrer un visage /
    # Enregistrer un corps (erkennung.*), page Détection par vision
    # (nav.vision). Die Unteroptions-Labels Only if no face / Always /
    # If needed sind noch englische Anzeige==Kennung (§8.2, Literale in
    # routes/erkennung.py) und bleiben deshalb ENGLISCH zitiert.
    # §8.21: echtes U+00A0 vor : ; ! ? und in « » — auch in t_html.
    "hilfe.live.titel": "La surveillance en direct, expliquée",
    "hilfe.live.satz1": """<p>La surveillance en direct regarde vos caméras dès que quelque chose
bouge. Quand une personne entre sur la propriété, vous recevez une alerte
en quelques secondes, et si le système connaît déjà le visage, l'alerte
porte un nom.</p>""",
    "hilfe.live.satz2": """<p>À ce stade, le nom est une première estimation. La vérification
approfondie s'exécute juste après, sur l'enregistrement, et c'est elle qui
a le dernier mot.</p>""",
    "hilfe.live.satz3": """<p>La surveillance en direct ne dépend pas de Frigate : elle n'est pas
déclenchée par les événements Frigate et fonctionne de façon totalement
autonome. Elle regarde directement le flux vidéo, soit le flux proxy de
Frigate, soit le flux de la caméra elle-même ; vous le choisissez
caméra par caméra.</p>""",
    "hilfe.live.satz4": """<p>Utilisez <b>Choisir les caméras</b> pour décider quelles caméras
reçoivent une surveillance. Chaque caméra surveillée coûte de la puissance
de calcul en continu ; commencez donc là où les gens arrivent
réellement : l'allée, la porte d'entrée, le portail. Vous pourrez en
ajouter d'autres plus tard.</p>""",
    "hilfe.live.satz5": """<p>Désactiver une caméra ici ne change rien à l'enregistrement. Frigate
continue d'enregistrer comme avant ; l'interrupteur décide seulement si
suslik regarde l'image immédiatement ou attend l'enregistrement.</p>""",
    "hilfe.gesicht.titel": "La reconnaissance faciale, expliquée",
    "hilfe.gesicht.satz1": """<p>C'est la voie de base par laquelle suslik reconnaît et apprend les
visages. Chaque passage enregistré est confronté aux visages que vous avez
appris au système.</p>""",
    "hilfe.gesicht.satz2": """<p>L'apprentissage se fait à partir de vos propres caméras : suslik collecte
les visages qu'il voit, vous regardez les images et lui dites qui est qui.
Plus il a vu une personne dans des situations et des poses différentes,
plus il devient précis : lumière du jour, soir, avec chapeau, sans
chapeau, de profil.</p>""",
    "hilfe.gesicht.satz3": """<p>Si Frigate connaît déjà des visages, vous pouvez les importer sur la
page Synchronisation Frigate. La recommandation reste d'apprendre les
visages ici : l'apprentissage propre à suslik collecte beaucoup de poses
et de situations différentes par personne, et ces références donnent de
meilleurs résultats dans suslik que des visages repris de Frigate. Ce que
vous apprenez ici peut être rendu à Frigate sur la page de synchronisation
si vous le souhaitez.</p>""",
    "hilfe.gesicht.satz4": """<p>Tout reste sur votre machine. Rien n'est envoyé nulle part, et aucun
service cloud ne se cache derrière.</p>""",
    "hilfe.gesicht.satz5": """<p>Quand un visage est reconnu, ou qu'un inconnu apparaît, suslik peut
vous alerter directement : Pushover, Telegram ou MQTT pour votre
domotique. Vous choisissez sur la page Notifications ce qui est envoyé et
où. Ces alertes sont propres à suslik et fonctionnent de façon totalement
indépendante de Frigate ; Frigate n'a besoin d'aucune configuration de
notification.</p>""",
    "hilfe.gesicht.satz6": """<p><b>Gérer les personnes</b> montre toutes les personnes que le système
connaît et vous permet de faire le ménage. <b>Enregistrer un visage</b>
lance une session d'apprentissage pour quelqu'un de nouveau.</p>""",
    "hilfe.koerper.titel": "La reconnaissance corporelle, expliquée",
    "hilfe.koerper.satz1": """<p>Certains passages ne montrent jamais de visage exploitable : la
personne regarde ailleurs, porte une capuche ou est trop loin. La
reconnaissance corporelle couvre ces cas. Elle reconnaît les membres du
foyer à la carrure et à la posture, à partir d'images montrant la personne
en entier.</p>""",
    "hilfe.koerper.satz2": """<p>Elle est faite exactement pour ce cas : pas de visage exploitable,
vous voulez quand même savoir qui c'était, et vous ne voulez pas confier
les images à un modèle de vision IA pour cela.</p>""",
    "hilfe.koerper.satz3": """<p>Elle apprend à partir du matériel que vous validez. <b>Enregistrer un
corps</b> lance une courte session d'apprentissage pour une personne : le
système collecte des images de cette personne sur vos caméras, vous
examinez le résultat une fois, et ensuite la reconnaissance continue
d'apprendre toute seule.</p>""",
    "hilfe.koerper.satz4": """<p>Avec l'interrupteur ci-dessus, vous choisissez si elle
s'exécute, et à quel moment. <b>Only if no face</b> signifie qu'elle reste silencieuse, sauf
si la vérification du visage n'a rien donné. <b>Always</b> signifie
qu'elle vérifie chaque passage. Désactivée, elle ne s'exécute jamais.</p>""",
    "hilfe.vision.titel": "La vision IA, expliquée",
    "hilfe.vision.satz1": """<p>La vision IA est une voie de reconnaissance à part entière. Elle
montre les images d'un passage à un modèle d'image et lui demande à quelle
personne enregistrée elles ressemblent. Vous pouvez l'utiliser en renfort
pour les cas difficiles, ou la laisser assurer seule la reconnaissance :
réglée sur <b>Always</b>, elle juge chaque passage par elle-même, même si
aucun visage n'est appris. Elle juge à la fin d'un passage, pas en
direct.</p>""",
    "hilfe.vision.satz2": """<p>Ce qu'il lui faut pour fonctionner : des personnes enregistrées avec
des images de corps validées (leurs galeries), et un modèle connecté. Le
modèle peut s'exécuter localement sur votre propre matériel ou dans le
cloud. Avec un modèle cloud, gardez à l'esprit que les images quittent
votre maison : ce qui va de soi avec un modèle local n'est pas
automatiquement permis avec un modèle cloud. Et ne choisissez pas les
modèles les plus petits ; un modèle de taille moyenne fait très bien le
travail.</p>""",
    "hilfe.vision.satz3": """<p>Ce que nous utilisons nous-mêmes : Qwen 3.5 en version 9B, et il fait
bien le travail, en local comme dans le cloud. Nous avons aussi testé des
modèles d'Anthropic (Claude), de Google (Gemini) et d'OpenAI (GPT).
Considérez cela comme testé, pas comme une recommandation ; la liste des
modèles sur la page Détection par vision marque ceux que nous avons
mesurés, là où vous choisissez.</p>""",
    "hilfe.vision.satz4": """<p>Et elle ne s'arrête pas à une comparaison : pour exclure les
confusions, le passage est aussi confronté aux galeries des autres
personnes, dans les deux sens. Chaque paire comparée coûte deux requêtes ;
un seul passage peut donc vite chiffrer. <b>If needed</b> limite la
facture : le modèle n'est interrogé que lorsque les visages
laissent un doute. Sans modèle connecté, la vision reste simplement hors
jeu, et la carte le dit.</p>""",
    "hilfe.faces_bekannt.titel":
        "Personnes connues et enregistrement, expliqués",
    "hilfe.faces_bekannt.satz1": """<p>Vous voyez ici toutes les personnes que votre système connaît
&mdash; touchez un visage et vous voyez chaque image conservée derrière
lui.</p>""",
    "hilfe.faces_bekannt.satz2": """<p>Une nouvelle personne ne s'apprend pas en téléversant une photo :
le système l'apprend à partir des images ordinaires de vos caméras. Au
fil de la journée, il collecte des images sous différents angles, vous
confirmez de qui il s'agit, et ce n'est qu'après cette vérification qu'une
image est conservée.</p>""",
    "hilfe.faces_bekannt.satz3": """<p>Chaque personne dispose ainsi d'une petite collection d'images
réelles du quotidien &mdash; exactement ce qui rend la reconnaissance
solide, même quand quelqu'un regarde ailleurs ou porte une
casquette.</p>""",
    "hilfe.faces_lernen.titel": "L'apprentissage, expliqué",
    "hilfe.faces_lernen.satz1": """<p>Pendant que les caméras tournent, le système continue de collecter
de nouvelles images des personnes qu'il connaît déjà. Vous parcourez ici
ce qui s'est accumulé &mdash; un coup d'œil tous les deux ou trois jours
suffit largement.</p>""",
    "hilfe.faces_lernen.satz2": """<p>Vous confirmez, corrigez ou écartez d'un clic ; rien n'est conservé
sans vous.</p>""",
    "hilfe.faces_lernen.satz3": """<p>Plus une personne a de bonnes images, plus elle est reconnue de
façon fiable &mdash; l'apprentissage ne s'arrête donc jamais tout à fait,
il devient simplement plus rare.</p>""",
    "hilfe.faces_unbekannt.titel": "Les visiteurs inconnus, expliqués",
    "hilfe.faces_unbekannt.satz1": """<p>Certaines personnes reviennent régulièrement sans que le système ait
un nom à leur donner &mdash; le facteur, un voisin, le jardinier. Le système
rassemble ici ces inconnus récurrents et vous demande : qui
est-ce ?</p>""",
    "hilfe.faces_unbekannt.satz2": """<p>Donnez-leur un nom et ils seront reconnus comme tout le
monde. Ou laissez-les volontairement inconnus &mdash; c'est aussi une
décision, et le système ne posera plus la question.</p>""",
    "hilfe.faces_qualitaet.titel":
        "La vérification de la qualité, expliquée",
    "hilfe.faces_qualitaet.satz1": """<p>Avec le temps, beaucoup d'images s'accumulent, et toutes n'aident
pas la reconnaissance &mdash; certaines sont floues, d'autres montrent à
peine la personne, et dans le pire des cas les images de deux personnes
différentes se ressemblent au point que la confusion menace.</p>""",
    "hilfe.faces_qualitaet.satz2": """<p>Cette vérification repère ces points faibles avant qu'ils ne vous
coûtent une reconnaissance. Vous recevez des indications concrètes sur les
images à regarder &mdash; rien n'est supprimé tant que vous ne le décidez
pas vous-même.</p>""",
    "hilfe.faces_lernlauf.titel": "La session d'apprentissage, expliquée",
    "hilfe.faces_lernlauf.satz1": """<p>Vous lancez une session ; le système relit vos enregistrements
récents et collecte les visages tout seul.</p>""",
    "hilfe.faces_lernlauf.satz2":
        "<p>Il les trie en groupes. Un groupe doit correspondre à une "
        "personne.</p>",
    "hilfe.faces_lernlauf.satz3": """<p>Vous nommez chaque groupe, ou vous le passez. C'est la seule étape
qui a besoin de vous.</p>""",
    "hilfe.faces_lernlauf.satz4": """<p>Les images nommées deviennent des références et comptent aussitôt
pour la reconnaissance. Répétez tous les deux ou trois jours, ou laissez
la page Aujourd'hui compléter entre-temps les images des personnes
connues.</p>""",
    # B9: je Ziel ein GANZER Satz-Schluessel. Kopplung: "Visages" ==
    # nav.faces/faces.titel, "Reconnaissance" == nav.erkennung/
    # erkennung.titel, Lauf-Seite == nav.lernlauf; Bestands-Muster
    # "Retour à Visages" / "Retour à la session d'apprentissage".
    "hilfe.zurueck.erkennung": "Retour à la Reconnaissance",
    "hilfe.zurueck.faces": "Retour aux Visages",
    "hilfe.zurueck.lernlauf": "Retour à la session d'apprentissage",
    # ---- §8.1-Nachzuegler (Stufe 3): Inline-Markup-Prosa der Tranchen ----
    # Tag-Folge, <code>-Inhalte und hrefs byte-gleich zu en.py; die
    # EN-Entities &bdquo;/&ldquo; werden nach Bestands-Muster (vision.
    # frage.doppel_satz) zu « » mit echtem U+00A0.
    # Zitiert die Seite <b>Système</b> == system.titel / nav.system.
    "setupwiz.backend.system_satz":
        "L'activation réelle de l'accélérateur se confirme en direct sur "
        "la page <b>Système</b> après le démarrage (suslik ne se rabat "
        "jamais sur le CPU sans le dire).",
    # Wortgleich system.titel + konfiguration.knopf_setup (der Pfeil
    # verbindet die beiden Zitate).
    "setupwiz.fertig.wieder_satz":
        "Vous pouvez relancer cet assistant à tout moment depuis "
        "<b>Système → Relancer l'assistant d'installation</b>.",
    "system.sync.diagnose_satz":
        'Si une synchronisation signale un problème, <a '
        'href="/sync_diagnose" target="_blank">ouvrez le diagnostic</a> '
        "— il rassemble le rapport suslik et le journal Frigate, prêts "
        "à coller dans un ticket.",
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">ouvrez le '
        "diagnostic</a> — rassemble le rapport suslik et le journal "
        "Frigate.",
    "vision.kopf.einleitung":
        "Une troisième voie de reconnaissance à côté du visage et du "
        "corps : un modèle de vision-langage regarde une image d'un "
        "passage et dit laquelle des personnes apprises elle montre "
        "&mdash; en la comparant à une petite galerie de cette personne. "
        "C'est une <b>voix supplémentaire</b>, jamais le portier : le "
        "choix forcé répond « A ou B », il peut donc confirmer un "
        "membre du foyer, mais ne peut pas refouler un inconnu. Cela "
        "reste le travail de la reconnaissance existante.",
    # Produktnamen (llama.cpp, Qwen3.5, docker stats) wortgleich (§8.7).
    "vision.hinweis.modell_satz":
        "Un modèle de vision capable de regarder plusieurs images à la "
        "fois. Vous pouvez utiliser l'un des fournisseurs en ligne "
        "ci-dessous, ou en faire tourner un vous-même &mdash; la "
        "combinaison mesurée ici est <b>llama.cpp</b> avec un modèle de "
        "vision <b>Qwen3.5</b> (le 4B vaut le 9B sur cette tâche et "
        "demande environ moitié moins de mémoire). Il n'a <b>pas</b> "
        "besoin de tourner sur cette machine.",
    "vision.hinweis.host_satz":
        "<b>Cette machine est en général trop petite pour un modèle "
        "local.</b> Le 9B demande environ 12 Go de mémoire de travail, "
        "le 4B environ 6,6 Go, et suslik plus le worker d'analyse "
        "vivent déjà ici &mdash; le worker est la première chose que le "
        "noyau tue quand la mémoire s'épuise. Une seconde machine, ou "
        "un fournisseur en ligne, est la configuration raisonnable.",
    "vision.hinweis.mess_satz":
        "Un avertissement sur la mesure de cette mémoire : "
        "<code>docker stats</code> affiche environ 2,7 GiB pour le "
        "conteneur du modèle, parce que les poids sont mappés, pas "
        "copiés. La mémoire de travail réelle est d'environ 11,6 GiB. "
        "Si vous dimensionnez <code>--memory</code> d'après ce que dit "
        "<code>docker stats</code>, le modèle recharge ses poids en "
        "continu et tout se traîne.",
    "vision.hinweis.kosten_satz":
        "Vitesse et coût, mesurés, pour que rien ne vous surprenne plus "
        "tard : tout le passage est envoyé en <b>une seule grille de "
        "candidats</b>, et chaque <b>paire de galeries comparée coûte "
        "deux requêtes</b> (la même question est posée à nouveau avec "
        "les deux galeries permutées, pour débusquer un biais de "
        "position). En général, une seule paire tranche. Sur une "
        "machine de classe CPU, cela fait environ 7 minutes par "
        "paire ; sur les endpoints en ligne mesurés ici, quelques "
        "secondes.",
    "vision.verb.key_ort":
        "<b>Mettez la clé dans le champ de clé, pas dans l'URL</b> : "
        "un endpoint qui porte des identifiants dans son adresse "
        "&mdash; devant le nom d'hôte, ou en paramètre de requête "
        "&mdash; contient le même secret, et il apparaît dans bien plus "
        "d'endroits (statut, journal, sauvegarde).",
    # Der Pruef-Knopf ist noch ein ENGLISCHES B9-Literal in
    # routes/vision.py — Anzeige==Kennung (§8.2), englisch zitiert.
    "vision.modell.leer_key":
        "Rien à choisir pour l'instant. Saisissez votre clé ci-dessus "
        "et appuyez sur <b>Check the key</b> : suslik se connecte à "
        "l'endpoint, lui demande ce qui s'y trouve, et vous montre ce "
        "qu'il a trouvé. Vous choisissez dans cette liste.",
    "vision.modell.leer_verbindung":
        "Rien à choisir pour l'instant. Remplissez les champs ci-dessus "
        "et appuyez sur <b>Check the connection</b> : suslik se "
        "connecte à l'endpoint, lui demande ce qui s'y trouve, et vous "
        "montre ce qu'il a trouvé. Vous choisissez dans cette liste.",
    # residents/strangers = englische Mess-Etiketten aus
    # core/registry.py (Anzeige==Kennung, englisch zitiert);
    # "non testé ici" wortgleich vision.modell.ungetestet.
    "vision.modell.antwort_satz":
        "Voici ce que l'endpoint a répondu quand suslik le lui a "
        "demandé, {zeit} &mdash; rien ici n'est une suggestion de notre "
        "part. Là où nous avons mesuré un modèle, la mention figure sur "
        "ce modèle. Deux capacités sont affichées séparément, parce "
        "qu'elles ne vont pas de pair : <b>residents</b>, c'est "
        "désigner la bonne des deux personnes connues ; "
        "<b>strangers</b>, c'est répondre « aucun des deux » pour "
        "quelqu'un que vous ne lui avez jamais appris. Une coche "
        "signifie que chaque jugement de ce type dans notre mesure "
        "était juste ; la fraction à côté dit tout. Les modèles sans "
        "mesure ici affichent <b>non testé ici</b> &mdash; ce n'est pas "
        "un verdict, juste de l'honnêteté (mesures de {stand}).",
    # <b>question personnalisée</b> == visiontest.vision.custom_prompt.
    "vision.prompt.eigen_satz":
        "C'est votre propre formulation &mdash; les verdicts rendus "
        "avec elle sont marqués <b>question personnalisée</b>. "
        "Réinitialisez-la pour revenir à la formulation par défaut, celle "
        "qui a été mesurée.",
    "vision.cloud.sendet_satz":
        "Ceci envoie des images de personnes issues de vos caméras "
        'vers <b class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Trois étapes, parce qu'un simple ping d'accessibilité ne "
        "suffit pas : un backend était joignable, avait le modèle et "
        "répondait vite &mdash; et s'est quand même trompé sur 5 des 12 "
        "questions de comparaison, parce qu'il réduisait les images "
        "avant de les regarder.<br><b>1</b> accessibilité, modèle et "
        "temps de réponse, avec une image de test générée à la "
        "volée.<br><b>2</b> une exécution en choix forcé sur des "
        "grilles de formes générées dont la bonne réponse est connue "
        "&mdash; cela vérifie le format de réponse, l'analyseur et "
        "l'interrupteur de réflexion.<br><b>3</b> un décompte de tokens "
        "comparé à une référence mesurée, où la réduction d'images se "
        "voit.<br><b>Aucune image de personne n'est utilisée pour "
        "cela</b>, et il n'existe aucune option pour le faire.",
    "visiontest.kopf.wege_satz":
        "Choisissez un passage réel et voyez ce qu'en font les trois "
        "voies de reconnaissance, côte à côte : <b>visage</b>, "
        "<b>personne</b> et <b>vision</b>.",
    # "Détection par vision" == nav.vision.
    "visiontest.vision.einrichten_satz":
        'Configurez-la sous <a href="/vision">Détection par '
        "vision</a> : un modèle, un test de connexion au vert et au "
        "moins deux galeries validées. Les deux autres colonnes "
        "fonctionnent sans elle.",
    "visionwizard.groesse.satz":
        "Mesuré, honnêtement : la taille n'a été le levier dans "
        "<b>aucun</b> des cas que nous avons testés &mdash; une "
        "grille plus grande n'a pas rendu les réponses meilleures, et "
        "ne les a pas rendues pires non plus. Prenez la plus grande si "
        "votre matériel le permet (ici : {empfehlung}), la plus "
        "petite sinon. Les deux coûtent à peu près pareil, parce que "
        "c'est le canevas qui coûte des tokens, pas le nombre de cases.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Oubliez-les</a> '
        "si vous voulez repartir de zéro.",
    # <b>ne convient pas</b> == visionwizard.zelle.knopf_weg.
    "visionwizard.vorschlag.satz":
        "Une rangée par vue : de face, de profil, de dos. Les images "
        "sont choisies selon la taille et la netteté, la présence nette "
        "des yeux et du nez, la part de lumière brûlée, la part du "
        "cadrage qui est réellement la personne &mdash; et réparties "
        "sur des jours, des événements et des caméras différents. La "
        "ligne sous chaque image dit ce qui y a été mesuré. Cliquez sur "
        "<b>ne convient pas</b> pour tout ce qui est inutilisable "
        "&mdash; la meilleure image suivante de la MÊME vue prend sa "
        "place. Cela ne touche pas votre matériel d'apprentissage ; "
        "cela dit seulement « pas comme case de galerie ».",
    "personwizard.kopf.stark_satz":
        "<b>Ce qui rend le modèle solide :</b> la variété l'emporte "
        "sur le volume. Des images issues de <b>beaucoup de jours "
        "différents</b> (tenues, lumière, caméras) aident bien plus que "
        "beaucoup d'images d'un seul passage — relancez la collecte "
        "sur de nouveaux jours plutôt que de creuser davantage la "
        "même journée. Les images d'intrus confirmés affinent le seuil de "
        "décision de la même façon.",
    # "État du modèle" == nav.person_modell.
    "personwizard.fertig.training_satz":
        "L'entraînement sur le matériel validé démarre automatiquement "
        "après l'examen — voir "
        '<a href="/person/modell">État du modèle</a>. Vous pouvez '
        "lancer une autre session ci-dessous à tout moment.",
    # "Configuration" == nav.bereich.configuration, "Avancé" ==
    # nav.konfiguration.
    "personwizard.kontrolle.schalter_satz":
        'Changez-le sous <a href="/konfiguration">Configuration &rarr; '
        "Avancé</a>, clé <code>diagnostic_collection</code>. Les images et "
        "le journal expirent avec le journal des verdicts après 30 jours "
        "&mdash; rien ici n'est conservé plus longtemps que la trace de "
        "reconnaissance elle-même.",
    "personwizard.kontrolle.leer_satz":
        "Des entrées apparaissent dès que la reconnaissance corporelle "
        'est armée sur <a href="/person/modell">État du modèle</a> et '
        "qu'une personne passe.",
    # "Apprentissage de la personne" == nav.personlauf.
    "personwizard.bestand.leer_satz":
        'Lancez <a href="/personlauf">Apprentissage de la personne</a> '
        "et terminez l'examen — les images validées apparaissent ici.",
    "personwizard.bestand.stark_satz":
        "La variété l'emporte sur le volume : des images issues de "
        "<b>beaucoup de jours différents</b> (tenues, lumière) aident "
        "bien plus que beaucoup d'images d'un seul passage. Visez "
        "plusieurs jours par personne et laissez la collecte couvrir "
        "toutes vos caméras.",
    "personwizard.bestand.fremd_satz":
        "<b>Intrus :</b> {n} images d'intrus confirmés calibrent le "
        "seuil de décision — plus le modèle a vu d'intrus, plus cette "
        "limite est fiable. (Collectées dans "
        "<code>personlern/fremd/</code> ; une page est prévue pour "
        "enrichir cette réserve à partir des passants de votre rue.)",
    "personwizard.bestand.fremd_erklaerung":
        "Des images d'intrus confirmés — elles entraînent la classe "
        "supplémentaire et calibrent le seuil de décision. En supprimer "
        "une réentraîne le modèle aussitôt (les fichiers se trouvent dans "
        "<code>personlern/fremd/</code>).",
    "personwizard.modell.leer_satz":
        'Lancez <a href="/personlauf">Apprentissage de la personne</a> '
        "et terminez un examen — l'entraînement démarre "
        "automatiquement ensuite.",
    # "Images de corps" == nav.person.
    "personwizard.modell.material_satz":
        "Gérez les images sous "
        '<a href="/person">Images de corps</a> — les suppressions '
        "réentraînent le modèle automatiquement.",
    # ---- Meldetexte (Stufe 4) --------------------------------------------
    # Pushover-/Telegram-TEXTE: PLAINTEXT ohne Escaping-Pfad — hier steht
    # deshalb IMMER echtes U+00A0 ( ) vor : ; ! ?, nie "&nbsp;"
    # (§8.21; ein Entity erschiene im Push woertlich).
    # Produktnamen (suslik/Frigate/Pushover/Telegram) bleiben wortgleich
    # (§8.6). ENGLISCH bleiben ausserdem die eingesetzten KENNUNGEN:
    # {wache} (core.livewache.WATCHER_TITEL "Live watcher"), {label}
    # (Frigate-Label), {grund} der Vision, {kamera}, {unsere} — der
    # franzoesische Rahmen umschliesst sie wie einen Eigennamen.
    #
    # FR-Entscheide dieses Abschnitts:
    # - Titel-Bauform "suslik<NBSP>: <Sache>" durchgehend (im Original
    #   traegt nur meldung.titel.kategorie einen Doppelpunkt; die blosse
    #   Apposition "suslik reconnaissance corporelle" ist im FR ein
    #   Stolperer). Push-Titel bleiben kurz.
    # - Genus des Personennamens ist unbekannt -> Klammerform
    #   "confirmé(e)"/"reconnu(e)", dieselbe Konvention wie die
    #   Klammerplurale "image(s)" (§8.18).
    # - Wortstufe {wort} kommt uebersetzt aus core/vertrauen
    #   (baustein.stufe.*: "correspondance nette" … "sous la barre") —
    #   la barre = Qualitaets-Latte, seuil = Schwelle (begriffe_tabellen).
    # - ZWEITER Gedankenstrich -> Doppelpunkt (Muttersprachler-QS): wo ein
    #   Satzteil in einen Rahmen faellt, der schon einen Strich setzt
    #   ("{kamera} — {urteil}", "rien à prendre — {grund}"), traegt der
    #   Doppelpunkt die Erlaeuterung — zwei Striche in EINEM Satz sind im
    #   FR ein Bruch (gleiche Entscheidung wie ES).
    "meldung.titel.kategorie": "suslik : {wort}",
    "meldung.alert.bestaetigt":
        "{name} confirmé(e) ({wort}, visible dans {n} fenêtre(s))",
    # "aucune personne confirmée" == benachrichtigungen.kategorien.*:
    # das Subjekt "personne" haelt das Genus stabil, unabhaengig davon,
    # wer erkannt wurde.
    "meldung.alert.keiner_naechster":
        "aucune personne confirmée : la meilleure correspondance est "
        "{name} ({wort})",
    "meldung.alert.keiner_ohne_gesicht":
        "aucune personne confirmée : aucun visage exploitable",
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate a vu : {label}. {gesichter}",
    "meldung.alert.gesichter.eins": "{n} visage dans cet événement.",
    "meldung.alert.gesichter.viele": "{n} visages dans cet événement.",
    # Reiner Zahlen-Anhang: nichts zu uebersetzen (Produktname, Zahlen,
    # die Kuerzel "cos"/{unsere} aus dem Dienst) — bleibt wortgleich.
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    # "reconnaissance corporelle, pas faciale" == der Wortlaut, den
    # personwizard.modell.live_hinweis dem Nutzer ankuendigt.
    "meldung.person.titel": "suslik : reconnaissance corporelle",
    "meldung.person.satz":
        "{name} reconnu(e) d'après le corps (reconnaissance corporelle, "
        "pas faciale) — {wort}, {n} événements concordants",
    # match == correspondance (begriffe_tabellen, Nachgetragene Tragworte).
    "meldung.person.wort_ersatz": "correspondance",
    "meldung.person.zahl": "[score {score}]",
    # "Vision IA" == erkennung.vision.titel; im Fliesstext bleibt das
    # kurze "vision" wie im Original. "image(s)"/"comparaison(s)"
    # bleiben EINE Form (§8.18).
    "meldung.vision.titel": "suslik : vision IA",
    "meldung.vision.unbestaetigt":
        "la vision n'a confirmé personne lors de ce passage",
    # "the body ranking" -> die PRODUKT-Benennung des Wegs
    # (personwizard/nav: "reconnaissance corporelle"); "classement
    # corporel" ist im FR keine Fuegung (corporel bindet an
    # châtiment/schéma/masse) und liest sich anthropometrisch. Das
    # Imperfekt "indiquait" haelt den Vorbehalt des Originals.
    "meldung.vision.koerper_zusatz":
        "— la reconnaissance corporelle indiquait {namen}",
    "meldung.vision.bilder_zusatz": "({n} image(s) dans la grille)",
    "meldung.vision.einig":
        "vision : {name} — à l'unanimité, {voten} des {bilder} "
        "comparaison(s)",
    "meldung.vision.kein_urteil": "vision : aucun verdict — {grund}",
    # {wache} = englische Waechter-Kennung, sie fuehrt den Titel wie ein
    # Eigenname. "incident" == system.live.stoerungen ("Avis d'incident").
    "meldung.wache.titel_person": "{wache} {kamera} : personne détectée",
    "meldung.wache.titel_stoerung": "{wache} {kamera} : incident",
    "meldung.wache.caption": "{wache} {kamera} : {text}",
    # Nominalform statt Partizip: haelt den Satzanfang genusfrei, der Name
    # steht wie im Original hinter dem Doppelpunkt. "provisoire" ==
    # livealerts.kopf.satz.
    "meldung.wache.name_satz":
        "reconnaissance (en direct, provisoire) : {name} ({wort}, {n} "
        "observations concordantes)",
    "meldung.wache.name_zahl": "[cosinus {cos}]",
    "meldung.wache.funde.eins": "{n} visage en {sek} s",
    "meldung.wache.funde.viele": "{n} visages en {sek} s",
    "meldung.wache.funde_zahl": "(score {score}, {ms} ms)",
    "meldung.video_ersatz.satz": "(vidéo indisponible — envoi de l'image)",
    "meldung.test.satz": "Notification de test suslik ✓",
    # ---- D1: ehrliche Begruendung der Pass-Pruefung ----------------------
    # SATZTEILE mit kleinem Anfangswort: sie haengen hinter "rien à
    # prendre — " (bruecke_nichts_grund) oder hinter " · "
    # (bruecke_grund_zusatz). "visage(s)"/"image(s)"/"événement(s)"
    # bleiben EINE Form (§8.18, wie antwort.adopt_skip); "cadrage de
    # visage" == event.leer_crops, "quasi identiques" == adopt_gedeckt.
    "antwort.bruecke_nichts_grund": "rien à prendre — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    "antwort.bruecke_grund_zu_klein":
        "les {n} visage(s) mesuré(s) dans ce passage sont tous en dessous "
        "de la taille minimale de visage : le plus grand fait {kante} px, "
        "il en faut {min_kante}",
    "antwort.bruecke_grund_zu_unscharf":
        "{n} visage(s) de ce passage sont trop flou(s) pour servir de "
        "référence : meilleure netteté {sharp}, le minimum est de "
        "{unscharf_max}",
    "antwort.bruecke_grund_kein_gesicht":
        "aucun visage mesurable dans les {n} image(s) vérifiée(s) de ce "
        "passage",
    "antwort.bruecke_grund_gedeckt":
        "{n} des visage(s) vérifié(s) sont quasi identiques aux références "
        "que {person} possède déjà",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} des visage(s) vérifié(s) ressemblent davantage à quelqu'un "
        "d'autre qu'à {person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} des visage(s) vérifié(s) n'étaient pas clairement {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} des visage(s) vérifié(s) étaient faibles sur les deux "
        "plans : qualité d'image et identité",
    "antwort.bruecke_grund_kein_crop":
        "aucun des {n} événement(s) de ce passage n'a de cadrage de visage "
        "à vérifier",
    "antwort.bruecke_grund_keine_events":
        "aucun événement de ce passage n'a {person} comme personne "
        "confirmée ni comme meilleure correspondance",
    "antwort.bruecke_grund_keine_referenzen":
        "{person} n'a pas encore d'images de référence pour la comparaison",
    # ---- personlauf-Design (Nachzug) ----
    # Kachel-Titel und Kachel-Saetze des /personlauf-Laufflusses. Kachel 1/4,
    # die erste Saeulen-Marke und die Nachbar-Beschriftungen kommen wortgleich
    # aus dem Gesichts-Lernlauf (lernwizard.*) — hier stehen nur die sieben
    # personwizard-eigenen Neuzugaenge. §8.21: der Doppelpunkt in .k3.satz
    # traegt ein echtes U+00A0, kein &nbsp;-Entity.
    "personwizard.kachel.sammeln": "Collecter les images",
    "personwizard.kachel.pruefen": "Examiner les images",
    "personwizard.k1.satz":
        "Choisissez qui apprendre et jusqu'où remonter &mdash; la session "
        "collecte ensuite les images depuis vos propres enregistrements.",
    "personwizard.k2.satz":
        "Collecte des images du corps entier depuis vos enregistrements, "
        "et seulement à partir de passages qu'un visage a déjà confirmés.",
    "personwizard.k3.satz":
        "L'étape qui a besoin de vous : chaque image collectée reçoit "
        "votre oui ou votre non avant que quoi que ce soit ne soit "
        "appris.",
    "personwizard.k4.satz":
        "Les images validées entraînent aussitôt le modèle de personne "
        "&mdash; il peut alors reconnaître des personnes même quand aucun "
        "visage n'est visible.",
    "personwizard.such.titel": "Configurer l'apprentissage de la personne",
    # --------------------------------------------- routes/systemstat ---
    "systemstat.titel": "Charge du système",
    "systemstat.sub":
        "Charge totale de cette machine. Une nouvelle mesure toutes les "
        "{takt} secondes, conservée pendant {stunden} heures. Il n\u2019y a "
        "pas de répartition par processus ici : Frigate tourne dans son "
        "propre conteneur, sa part ne peut pas être nommée depuis ce "
        "côté-ci. Ce que ce matériel ne sait pas mesurer, il le dit, au "
        "lieu d\u2019afficher un zéro.",
    "systemstat.leer.titel": "Pas encore de mesures.",
    "systemstat.leer.hinweis":
        "La première ligne est écrite environ {takt} secondes après le "
        "démarrage du service. Les valeurs qui demandent deux mesures "
        "(CPU, NPU, GPU) suivent un tour plus tard.",
    "systemstat.block.hardware": "Matériel",
    "systemstat.block.erkennung": "Reconnaissance",
    "systemstat.block.live": "Direct",
    "systemstat.nicht_verfuegbar": "non disponible",
    "systemstat.kein_prozent": "pas de pourcentage",
    "systemstat.ja": "oui",
    "systemstat.nein": "non",
    "systemstat.verlauf.leer": "pas encore d\u2019historique",
    "systemstat.verlauf.aria": "la dernière heure",
    "systemstat.cpu.anzahl": "Cœurs",
    "systemstat.cpu.kerne": "par cœur, à l\u2019instant",
    "systemstat.kachel.platte": "Disque",
    "systemstat.ram.genutzt": "Utilisé",
    "systemstat.ram.grafik": "Graphique (RAM partagée)",
    "systemstat.ram.prozesse": "Processus",
    "systemstat.ram.limit": "Limite",
    "systemstat.ram.cache": "Cache récupérable",
    "systemstat.platte.frei": "Libre",
    "systemstat.platte.gesamt": "Total",
    "systemstat.platte.cache": "Cache des clips / plafond",
    "systemstat.platte.frei_min": "Garder libre",
    "systemstat.gpu.engine": "Moteur le plus chargé",
    "systemstat.gpu.speicher": "Mémoire",
    "systemstat.gpu.temperatur": "Température",
    "systemstat.gpu_eigen.titel": "GPU (part de suslik)",
    "systemstat.gpu.gesamt": "Carte entière",
    "systemstat.gpu_eigen.zeile": "part de suslik",
    "systemstat.kachel.worker": "Processus d\u2019analyse",
    "systemstat.worker.laeuft": "en marche",
    "systemstat.worker.ruht": "au repos, démarre à la demande",
    "systemstat.worker.tode": "redémarrages en 24 h",
    "systemstat.worker.zuletzt": "Dernière mort",
    "systemstat.worker.ursache": "Dernière cause",
    "systemstat.kachel.durchsatz": "Débit",
    "systemstat.durchsatz.tag": "Dernières 24 h",
    "systemstat.durchsatz.dauer": "Durée moyenne",
    "systemstat.kachel.queue": "File d'evenements",
    "systemstat.queue.aeltester": "plus ancien en attente",
    "systemstat.queue.spur": "voie d'envoi (ouverts · envoyes · echecs)",
    "systemstat.kachel.rueckstau": "Retard à rattraper",
    "systemstat.rueckstau.laeuft": "Rattrapage en cours",
    "systemstat.rueckstau.fenster": "Fenêtre rétrospective",
    "systemstat.kachel.live": "Moteur en direct",
    "systemstat.live.waechter": "Veilleurs actifs",
    "systemstat.live.supervisor": "Superviseur",
    "systemstat.stand":
        "Mesuré à {zeit}. La page se recharge d\u2019elle-même.",
    "systemstat.grund.erster_lauf":
        "en attente de la deuxième mesure \u2014 ce nombre est la "
        "différence entre deux mesures",
    "systemstat.grund.kein_geraet":
        "aucun appareil de ce genre sur cette machine",
    "systemstat.grund.kein_zaehler":
        "l\u2019appareil est là, mais son pilote ne publie aucun compteur "
        "d\u2019utilisation",
    "systemstat.grund.gesperrt":
        "le compteur existe, mais ce conteneur n\u2019a pas le droit de le "
        "lire (les événements de performance du noyau demandent des droits "
        "supplémentaires)",
    "systemstat.grund.werkzeug_fehlt":
        "l\u2019outil d\u2019interrogation de cet appareil n\u2019est pas "
        "dans cette image",
    "systemstat.grund.nicht_lesbar":
        "cette source n\u2019a pas pu être lue",
    "systemstat.grund.kein_limit":
        "aucune limite de mémoire n\u2019est fixée pour ce conteneur, il "
        "n\u2019y a donc pas de pourcentage à afficher",
    "systemstat.grund.kein_dienst":
        "ce nombre, seul le service en marche le connaît",
}
