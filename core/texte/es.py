# Muttersprachler-QS durchlaufen 19.08.2026 (Opus-Pruefagent je Sprache, Bericht im
# Session-Transkript); aktiv erst mit Registrierung in core/sprache.py (Stufe 1).
"""Spanische UI-Texte (es) — Schluessel und Struktur identisch zu
core/texte/en.py; verbindliche Begriffe: begriffe_tabellen.md (ES-Abschnitt)."""
T = {
    # ------------------------------------------------ routes/gesichter ---
    "gesichter.titel": "Personas conocidas",
    "gesichter.kopf.knopf_lernen": "Aprender personas",
    "gesichter.kopf.hinweis_lernen":
        "aprendizaje guiado sobre tus propias grabaciones (fase inicial)",
    "gesichter.kopf.satz":
        "Todas las personas aprendidas y sus imágenes de referencia. Puedes "
        "quitar imágenes sueltas, asignar más desde los rostros desconocidos "
        "con el botón de cada persona o subir una foto abajo, también para "
        "una persona completamente nueva.",
    "gesichter.galerie.bildzahl": "{n} imágenes",
    "gesichter.galerie.knopf_entfernen": "quitar",
    "gesichter.galerie.knopf_aehnliche": "buscar rostros coincidentes",
    "gesichter.galerie.knopf_qs": "Comprobar calidad",
    "gesichter.galerie.knopf_loeschen": "Eliminar persona\u2026",
    "gesichter.galerie.hinweis_leer": "aún sin imágenes",
    "gesichter.upload.titel": "Subir foto",
    "gesichter.upload.attr_person": "persona existente\u2026",
    "gesichter.upload.attr_neu": "o persona nueva",
    "gesichter.upload.knopf": "Subir",
    "gesichter.upload.hinweis":
        "Persona nueva: escribe el nombre en el campo de texto libre. "
        "Condición: buffalo_l debe encontrar un rostro (si no, aparece una "
        "pregunta para forzar la subida).",
    "gesichter.import.titel": "Importar / resincronizar desde Frigate",
    "gesichter.import.knopf": "Sincronizar rostros desde Frigate",
    "gesichter.import.hinweis":
        "Trae las imágenes de referencia que Frigate tiene y que aún faltan "
        "en tus referencias \u2014 incremental, se puede ejecutar en "
        "cualquier momento (no se borra nada local). Es la misma "
        "importación que en el asistente inicial, ahora accesible sin "
        "repetirlo (p. ej. tras restaurar una configuración).",
    # ------------------------------------------------- routes/kameras ---
    "kameras.titel": "Cámaras",
    "kameras.banner.config_fehler":
        "No se pudo leer la configuración de Frigate: {fehler}",
    "kameras.karte.verwenden": "usar esta cámara",
    "kameras.karte.zonen_hinweis": "ninguna marcada = todos los eventos",
    "kameras.karte.zonen_keine":
        "sin zonas definidas en Frigate \u2014 todos los eventos",
    "kameras.karte.rec_an": "rec \u2713",
    "kameras.karte.rec_aus": "sin rec",
    "kameras.karte.pill_aus": "apagada en Frigate",
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate no ejecuta detección de personas en este stream &mdash; "
        "aquí no pueden llegar eventos",
    "kameras.karte.pill_keine_detektion": "sin detección en Frigate",
    "kameras.leer.titel": "No se han encontrado cámaras en Frigate.",
    "kameras.leer.hinweis":
        "Comprueba que suslik puede acceder a la API de Frigate.",
    "kameras.fuss.knopf_speichern": "Guardar cámaras",
    # -------------------------------------------------- routes/lernen ---
    "lernen.titel": "Sugerencias — personas por incorporar",
    "lernen.kopf.titel_offen": "Sugerencias ({n})",
    "lernen.leer.titel": "No hay sugerencias pendientes.",
    "lernen.leer.hinweis":
        "Los rostros nuevos que sean buenos (grandes, nítidos, frontales, "
        "reconocidos con confianza o claramente de un extraño) aparecen "
        "aquí automáticamente tras el análisis.",
    "lernen.karte.unbekannt": "Persona desconocida/extraña",
    "lernen.karte.metrik_voll":
        "puntuación {score} · novedad {novelty} · {bw}×{bh}px · "
        "frontal {front} · nitidez {sharp}",
    "lernen.karte.metrik_kurz": "puntuación {score}",
    "lernen.karte.link_video": "Vídeo",
    "lernen.karte.knopf_add_person": "Añadir como {person}",
    "lernen.karte.attr_person": "como persona…",
    "lernen.karte.attr_neu": "o persona nueva",
    "lernen.karte.knopf_add": "Añadir",
    "lernen.karte.knopf_ablehnen": "Descartar",
    "lernen.galerie.titel": "Banco de referencias (Master)",
    "lernen.galerie.bildzahl": "{n} referencias",
    "lernen.upload.titel_abschnitt": "Subida",
    "lernen.upload.titel": "Subir tu propia foto al Master",
    "lernen.upload.attr_person": "persona existente…",
    "lernen.upload.attr_neu": "o persona nueva",
    "lernen.upload.knopf": "Subir",
    "lernen.upload.hinweis":
        "Persona nueva (p. ej. Alex): escribe el nombre en el campo de "
        "texto libre. Condición: buffalo_l debe encontrar un rostro (si "
        "no, aparece una pregunta para forzar la subida). Los PNG se "
        "convierten a JPEG. Sube varias fotos desde distintos ángulos, "
        "una tras otra.",
    # --------------------------------------------------- routes/areas ---
    "areas.titel": "Áreas",
    "areas.kopf.sprung": "Saltar a una vista:",
    "areas.verwaltung.titel": "Gestionar áreas",
    "areas.verwaltung.camzahl.eins": "{n} cámara",
    "areas.verwaltung.camzahl.viele": "{n} cámaras",
    "areas.verwaltung.attr_entfernen":
        "quitar esta área — sus cámaras vuelven a Default",
    "areas.verwaltung.attr_neu": "nombre de la nueva área",
    "areas.verwaltung.knopf_anlegen": "Añadir área",
    "areas.verwaltung.titel_zuweisen": "Asignar cámaras",
    "areas.verwaltung.satz_zuweisen":
        "Cada cámara pertenece exactamente a un área; todo lo no asignado "
        "se queda en Default. Guardar no requiere reiniciar el servicio.",
    "areas.verwaltung.pill_nicht_gesehen": "no vista",
    "areas.verwaltung.attr_nicht_gesehen":
        "asignada antes, ahora mismo no está en Frigate",
    "areas.verwaltung.hinweis_keine_kameras":
        "Aún no se conocen cámaras — conecta primero Frigate (Ajustes).",
    "areas.verwaltung.knopf_speichern": "Guardar áreas",
    # -------------------------------------- routes/benachrichtigungen ---
    "benachrichtigungen.titel": "Notificaciones",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• guardado — en blanco se conserva",
    "benachrichtigungen.felder.secret_leer": "sin definir",
    "benachrichtigungen.felder.option_an": "activado",
    "benachrichtigungen.felder.option_aus": "desactivado",
    "benachrichtigungen.alerts.titel": "Avisos",
    "benachrichtigungen.alerts.hinweis":
        "Qué categorías de veredicto generan un aviso — en todos los "
        "canales (Pushover, Telegram, topics de escena MQTT). El push de "
        "persona reconocida se rige por el interruptor de Presencia de "
        "abajo; los topics de datos MQTT (erkennung, heartbeat) publican "
        "siempre mientras la publicación MQTT esté activada.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik confirma una persona distinta a la de Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate etiquetó a alguien, suslik no vio ningún rostro utilizable",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik reconoció a alguien, Frigate no",
    "benachrichtigungen.kategorien.beide_unknown":
        "ninguno de los dos lados identificó un rostro",
    "benachrichtigungen.kategorien.erkannt":
        "se reconoció a una persona conocida",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "un rostro utilizable, pero no se confirmó a nadie (posible "
        "persona extraña)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "un rostro demasiado débil o pequeño para identificarlo",
    "benachrichtigungen.alerts.stil_label": "Estilo del texto de aviso:",
    "benachrichtigungen.alerts.stil_worte": "palabras sencillas",
    "benachrichtigungen.alerts.stil_worte_zahlen":
        "palabras + puntuaciones en bruto",
    "benachrichtigungen.alerts.stil_hinweis":
        "cómo describen los avisos una coincidencia (palabras sencillas "
        "es lo predeterminado; números en bruto de coseno/puntuación solo "
        "si quieres recuperarlos)",
    "benachrichtigungen.alerts.label_anwesenheit_push": "Push de presencia:",
    "benachrichtigungen.alerts.label_alert_cooldown":
        "Pausa entre avisos (s):",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Pausa de presencia (s):",
    "benachrichtigungen.alerts.label_szene_karenz": "Margen de escena (s):",
    "benachrichtigungen.pushover.label_token": "Token:",
    "benachrichtigungen.pushover.label_user": "Clave de usuario:",
    "benachrichtigungen.pushover.knopf_test": "Probar Pushover",
    "benachrichtigungen.telegram.label_modus": "Modo:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=apagado · ha=vía Home Assistant · direkt=bot directo · "
        "beide=ambos",
    "benachrichtigungen.telegram.label_inhalt": "Adjunto:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=clip corto, imagen si no está disponible · bild=solo imagen "
        "(sin transcodificación — más ligero en hardware modesto)",
    "benachrichtigungen.telegram.label_bot_token": "Token del bot:",
    "benachrichtigungen.telegram.label_chat_id": "Chat ID:",
    "benachrichtigungen.telegram.label_cooldown":
        "Pausa para desconocidos (s):",
    "benachrichtigungen.telegram.knopf_test": "Probar Telegram",
    "benachrichtigungen.mqtt.label_publish":
        "Publicar topics de reconocimiento:",
    "benachrichtigungen.mqtt.label_host": "Host:",
    "benachrichtigungen.mqtt.label_port": "Puerto:",
    "benachrichtigungen.mqtt.label_user": "Usuario:",
    "benachrichtigungen.mqtt.label_password": "Contraseña:",
    "benachrichtigungen.mqtt.label_topic_praefix": "Prefijo de topic:",
    "benachrichtigungen.mqtt.knopf_test": "Probar MQTT",
    "benachrichtigungen.fuss.knopf_speichern": "Guardar + reiniciar",
    # ----------------------------------------------- routes/aehnliche ---
    "aehnliche.kopf.titel": "Rostros coincidentes para {person}",
    "aehnliche.kopf.satz":
        "Dos fuentes: rostros desconocidos que se parecen a {person} y "
        "rostros nuevos de eventos en los que ya se reconoció a {person} "
        "con confianza. Marca y aplica.",
    "aehnliche.kopf.link_zurueck": "volver",
    "aehnliche.unbekannt.titel": "De rostros desconocidos",
    "aehnliche.unbekannt.suche_titel":
        "Búsqueda en curso — se están releyendo las referencias.",
    "aehnliche.unbekannt.suche_hinweis": "La página se actualiza sola.",
    "aehnliche.unbekannt.hinweis_leer":
        "No hay rostros desconocidos parecidos guardados.",
    "aehnliche.unbekannt.aehnlichkeit": "similitud {sim}",
    "aehnliche.unbekannt.knopf_hinzu": "Añadir la selección a {person}",
    "aehnliche.vorschlaege.titel":
        "Rostros nuevos de eventos reconocidos (7 días)",
    "aehnliche.vorschlaege.suche_titel":
        "Búsqueda en curso — se están repasando los eventos reconocidos.",
    "aehnliche.vorschlaege.suche_hinweis":
        "La página se actualiza sola; resultado en uno o dos minutos.",
    "aehnliche.vorschlaege.kachel_zeile": "{wann} · {kamera} · sim {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Recomendados",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutrales — revisa la imagen antes de aplicar",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Claramente esta persona, pero o la coincidencia está por debajo "
        "del umbral de confianza o el recorte es más pequeño / menos "
        "nítido — un vistazo lo decide.",
    "aehnliche.vorschlaege.knopf_alle":
        "Aplicar todos los recomendados ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt": "Aplicar la selección a {person}",
    "aehnliche.vorschlaege.knopf_neu": "buscar de nuevo",
    "aehnliche.vorschlaege.fuss":
        "a fecha de {stand} · recomendado = {person} con confianza + "
        "calidad de referencia",
    "aehnliche.vorschlaege.hinweis_leer":
        "No se encontró nada coincidente en los eventos reconocidos.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Criterios: inequívocamente esta persona, novedoso frente a las "
        "referencias, suficientemente grande y nítido.",
    # ------------------------------------------------- routes/frigate ---
    "frigate.verbindung.titel": "Conexión",
    "frigate.verbindung.satz":
        "Mi programa lee eventos e instantáneas de tu Frigate a través de "
        "su API HTTP — no se instala nada en el lado de Frigate.",
    "frigate.verbindung.knopf_aendern": "Cambiar conexión",
    "frigate.verbindung.knopf_speichern": "Guardar y reiniciar",
    "frigate.verbindung.knopf_abbrechen": "Cancelar",
    "frigate.verbindung.hinweis_speichern":
        "guardar reinicia brevemente el servicio; esta tarjeta muestra "
        "después en directo si la nueva dirección responde",
    "frigate.kameras.titel": "Cámaras",
    "frigate.kameras.satz":
        "Qué cámaras de Frigate observa este programa y qué zonas "
        "cuentan. Todo lo demás se ignora.",
    "frigate.kameras.beweis_keine_auswahl":
        "aún no hay selección de cámaras guardada — se usan todas las "
        "cámaras que ofrece Frigate",
    "frigate.kameras.knopf": "Gestionar cámaras",
    "frigate.sync.titel": "Sincronización",
    "frigate.sync.satz":
        "Mantiene al día los dos bancos de rostros: envía a Frigate "
        "rostros revisados, importa lo que solo tiene Frigate &mdash; "
        "siempre lo decides tú, nunca automático.",
    "frigate.sync.knopf": "Revisar y sincronizar",
    "frigate.fr.titel": "Reconocimiento facial propio de Frigate",
    "frigate.fr.satz":
        "Frigate también puede reconocer rostros. Este programa funciona "
        "con o sin él &mdash; el interruptor vive en la configuración de "
        "Frigate y se lee aquí en directo, para que sepas qué puede hacer "
        "una sincronización ahora mismo.",
    "frigate.fr.beweis_unbekannt": "estado desconocido — {detail}",
    "frigate.js.url_fehlt": "introduce la URL de Frigate",
    "frigate.js.fehler": "error:",
    # ------------------------------------------- routes/ereignisliste ---
    "ereignisliste.offen.titel": "Casos abiertos por etiquetar ({n})",
    "ereignisliste.offen.satz":
        "Se rellena automáticamente: todos los eventos con rostros que "
        "nadie confirmó y que aún no has etiquetado. Primero van los que "
        "no tienen a nadie reconocido cerca — esos son los que merece la "
        "pena mirar. Tras etiquetar, la tarjeta se atenúa y desaparece en "
        "la siguiente carga.",
    "ereignisliste.offen.frigate_mit": "Frigate: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate: —",
    "ereignisliste.offen.zeile_faces": "{n} rostros · mejor: {beste}",
    "ereignisliste.offen.link_video": "Vídeo",
    "ereignisliste.offen.kontext_erkannt":
        "con reconocimiento en la misma ventana de tiempo: {wer}",
    "ereignisliste.offen.kontext_fehlt":
        "sin reconocimiento confirmado cerca",
    "ereignisliste.blaettern.neuer": "← más recientes",
    "ereignisliste.blaettern.aelter": "más antiguos →",
    "ereignisliste.offen.blaettern_stand":
        "Página {seite}/{max} ({n} abiertos)",
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} evento de rostro débil oculto — probablemente sin rostro "
        "utilizable (tampoco hay nada confirmado cerca).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} eventos de rostro débil ocultos — probablemente sin rostro "
        "utilizable (tampoco hay nada confirmado cerca).",
    "ereignisliste.offen.schwach_zeigen": "mostrarlos",
    "ereignisliste.offen.schwach_alle":
        "mostrando también los eventos de rostro débil —",
    "ereignisliste.offen.schwach_zurueck":
        "volver a los que merecen la pena",
    "ereignisliste.offen.leer_titel": "Nada abierto — todo etiquetado.",
    "ereignisliste.offen.leer_hinweis":
        "Los eventos nuevos sin confirmar con rostros aparecen aquí "
        "automáticamente.",
    "ereignisliste.titel": "Eventos",
    "ereignisliste.filter.alle_areas": "todas las áreas",
    "ereignisliste.filter.alle_kameras": "todas las cámaras",
    "ereignisliste.filter.alle_personen": "todas las personas",
    "ereignisliste.filter.alle_kategorien": "todas las categorías",
    "ereignisliste.filter.knopf": "Filtrar",
    "ereignisliste.filter.reset": "restablecer",
    "ereignisliste.tabelle.blaettern_stand":
        "Página {seite}/{max} ({n} eventos)",
    "ereignisliste.tabelle.kopf_zeit": "Hora",
    "ereignisliste.tabelle.kopf_kamera": "Cámara",
    "ereignisliste.tabelle.kopf_kategorie": "Categoría",
    "ereignisliste.tabelle.kopf_crop": "Recorte",
    "ereignisliste.tabelle.kopf_gt": "Confirmar o corregir (GT)",
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "log",
    "ereignisliste.tabelle.link_video": "vídeo",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "clip incompleto — juzgado a partir de la parte legible",
    # ------------------------------------------- routes/konfiguration ---
    "konfiguration.kette.gesicht_titel": "Rostro",
    "konfiguration.kette.gesicht_kosten":
        "análisis base sobre el clip grabado — siempre activo",
    "konfiguration.kette.gesicht_zeitpunkt": "por evento",
    "konfiguration.kette.person_titel": "Persona (cuerpo)",
    "konfiguration.kette.person_kosten":
        "el paso local más costoso (embedding corporal en tu hardware)",
    "konfiguration.kette.person_zeitpunkt":
        "por evento, decidido según el veredicto del recorrido",
    "konfiguration.kette.vision_titel": "Visión",
    "konfiguration.kette.vision_kosten":
        "una petición por recorrido a tu endpoint de visión configurado",
    "konfiguration.kette.vision_zeitpunkt": "al final del recorrido",
    "konfiguration.kette.immer_an": "siempre",
    "konfiguration.kette.immer_hinweis": "(hoy no desactivable)",
    "konfiguration.kette.gesicht_erkl":
        "la vía del rostro es la columna vertebral de todo análisis — "
        "persona y visión dependen de su veredicto del recorrido",
    "konfiguration.kette.grund_person":
        "aún no hay un modelo de persona entrenado activo",
    "konfiguration.kette.grund_vision":
        "la detección de visión está desconectada",
    "konfiguration.kette.grund_aus": "desconectado aquí",
    "konfiguration.kette.status_aus": "estado: inactivo ({grund})",
    "konfiguration.kette.zeile_kosten": "coste: {kosten}",
    "konfiguration.kette.titel": "Cadena de reconocimiento",
    "konfiguration.kette.satz":
        "Qué reconocedores se ejecutan y en qué orden. La condición "
        "\"nur_wenn_gesicht_leer\" significa: el paso solo se ejecuta "
        "cuando la vía del rostro NO pudo confirmar a todos en el "
        "recorrido por la propiedad — se decide a partir del recorrido "
        "completo, nunca de un evento aislado. Cambiar el orden en sí "
        "llegará en una fase posterior; hoy la cadena siempre empieza "
        "por la vía del rostro.",
    "konfiguration.knopf_speichern": "Guardar + reiniciar",
    "konfiguration.kette_blatt.hinweis":
        "Los cambios quedan auditados (config_audit.jsonl); tras guardar, "
        "el servicio se reinicia limpiamente.",
    "konfiguration.titel": "Ajustes avanzados",
    "konfiguration.kopf.satz1":
        "Los cambios quedan auditados (config_audit.jsonl); tras guardar, "
        "el servicio se reinicia limpiamente (espera a que termine un "
        "análisis en curso).",
    "konfiguration.feld.option_an": "activado",
    "konfiguration.feld.option_aus": "desactivado",
    "konfiguration.abschnitt_alle": "Todos los parámetros",
    "konfiguration.tabelle.kopf_parameter": "Parámetro",
    "konfiguration.tabelle.kopf_wert": "Valor",
    "konfiguration.tabelle.kopf_bedeutung": "Significado",
    "konfiguration.knopf_setup": "Volver a ejecutar el asistente inicial",
    "konfiguration.abschnitt_readonly": "Solo lectura (consola/yaml)",
    # ----------------------------------------------- routes/lernanker ---
    "lernanker.eimer.ok": "limpio",
    "lernanker.eimer.unbestaetigt": "sin confirmar",
    "lernanker.eimer.zu_duenn": "escaso",
    "lernanker.eimer.hart": "mezclado",
    "lernanker.bin.frontal": "Frontal",
    "lernanker.bin.links": "Mirando a la izquierda",
    "lernanker.bin.rechts": "Mirando a la derecha",
    "lernanker.kachel.attr_clip":
        "{kamera} · det {det} · un clic abre el clip",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "abrir el clip",
    "lernanker.kachel.grund_fehlt": "sin valorar",
    "lernanker.detail.gruppe": "Grupo {pos} de {gesamt}",
    "lernanker.detail.frage": "¿Quién es?",
    "lernanker.badge.stuetz": "{n} rostros ({phys} físicos)",
    "lernanker.badge.faces": "{n} rostros",
    "lernanker.badge.durchgaenge": "{n} recorridos",
    "lernanker.badge.tage": "{n} día(s): {spanne}",
    "lernanker.badge.marge": "margen {marge}",
    "lernanker.link_zurueck": "volver a todos los grupos",
    "lernanker.detail.hinweis_klick":
        "haz clic en un rostro para abrir su clip",
    "lernanker.detail.hinweis_auswahl":
        "haz clic en una imagen para seleccionarla o quitarla de la "
        "selección",
    "lernanker.detail.hinweis_pfeil": "el pequeño &#9654; abre el clip",
    "lernanker.detail.weiter": "Siguiente grupo &#8230;",
    "lernanker.detail.pflege_hinweis":
        "el mantenimiento de las referencias vive en la página Calidad",
    "lernanker.detail.verworfen":
        "descartado — imágenes eliminadas; el grupo queda recordado para "
        "que las nuevas extracciones de los mismos eventos sigan en "
        "silencio",
    "lernanker.detail.dublette_hinweis":
        "comprobación de duplicados no disponible (el ancla es anterior a "
        "la persistencia de embeddings) — los duplicados físicos se "
        "filtran igualmente",
    "lernanker.bekannt.system": "ya está en tu sistema",
    "lernanker.bekannt.anker": "con nombre en otro grupo",
    "lernanker.detail.empfohlen": "Recomendadas — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "No recomendadas ({n}) — siguen visibles, con el motivo en cada "
        "imagen",
    "lernanker.detail.skip_weiter": "Omitir este grupo",
    "lernanker.detail.skip_zurueck": "Omitir — volver a los grupos",
    "lernanker.detail.knopf_ja": "Sí, es {name}",
    "lernanker.detail.knopf_andere": "Otra persona &#8230;",
    "lernanker.detail.knopf_benennen_easy":
        "Poner nombre a este grupo &#8230;",
    "lernanker.detail.knopf_alle": "Seleccionar todas las recomendadas",
    "lernanker.detail.knopf_keine": "Quitar toda la selección",
    "lernanker.detail.attr_name": "nombre de la persona (nuevo o existente)",
    "lernanker.detail.knopf_benennen": "Poner nombre a este grupo",
    "lernanker.detail.knopf_adopt": "Incorporar al reconocimiento",
    "lernanker.js.fehler": "error:",
    "lernanker.js.nicht_uebernommen": "sin incorporar",
    "lernanker.js.nicht_gespeichert": "sin guardar",
    "lernanker.liste.frage_lauf":
        "¿Eliminar la ejecución {lid} y todos sus datos? Esto elimina de "
        "forma permanente sus {n} grupo(s) — incluidos los nombrados y "
        "descartados — y todas las imágenes extraídas. Las referencias ya "
        "incorporadas al reconocimiento se conservan. No se puede "
        "deshacer.",
    "lernanker.liste.frage_alle":
        "¿Eliminar TODAS las {alt} ejecución(es) antigua(s) con sus {n} "
        "grupo(s) y todas las imágenes extraídas? Solo se conserva la "
        "ejecución más reciente {neuester}. Las referencias ya "
        "incorporadas al reconocimiento se conservan. No se puede "
        "deshacer.",
    "lernanker.liste.knopf_alte":
        "Eliminar todas las ejecuciones antiguas (conservar {neuester})",
    "lernanker.liste.lauf_zeile":
        "Eliminar una ejecución — elimina de forma permanente todos sus "
        "grupos e imágenes extraídas (las referencias que ya incorporaste "
        "se conservan):",
    "lernanker.liste.verworfen":
        "{n} grupo(s) descartado(s) recordado(s) — las nuevas "
        "extracciones de los mismos eventos siguen en silencio",
    "lernanker.titel": "Grupos de anclas",
    "lernanker.liste.leer":
        "Aún no hay anclas — se construyen con el aprendizaje "
        "(Preparación → Extracción → Agrupación).",
    "lernanker.liste.leer_link": "Abrir la página Aprendizaje",
    "lernanker.liste.kopf":
        "{n} grupos a partir de {ges} rostros aptos como ancla — {ok} "
        "limpios, {rest} por revisar (atenuados, con el motivo en la "
        "insignia). Abre un grupo para revisarlo y ponerle nombre — los "
        "grupos nombrados se incorporan al reconocimiento allí mismo "
        "(botón Incorporar).",
    "lernanker.liste.kopf_link": "Volver al aprendizaje",
    "lernanker.liste.mehr": "+{n} rostros más",
    "lernanker.liste.dublette":
        "el mismo grupo que {anker} — extraído de nuevo por una ejecución "
        "más reciente; ponle nombre allí",
    "lernanker.liste.knopf_review": "Revisar nombre",
    "lernanker.liste.knopf_view": "Ver grupo",
    "lernanker.liste.knopf_benennen": "Poner nombre a estos {n} rostros",
    "lernanker.liste.frage_verwerfen":
        "¿Descartar este grupo? Sus imágenes se eliminan; el grupo queda "
        "recordado para que las nuevas extracciones de los mismos eventos "
        "sigan en silencio.",
    "lernanker.liste.frage_verwerfen_benannt":
        "¿Descartar este grupo? Sus imágenes se eliminan y el nombre "
        "pendiente se descarta; el grupo queda recordado para que las "
        "nuevas extracciones de los mismos eventos sigan en silencio.",
    "lernanker.liste.knopf_verwerfen": "Descartar",
    # ---------------------------------------------- routes/syncauswahl ---
    "syncauswahl.titel": "Revisar y sincronizar — referencias a Frigate",
    "syncauswahl.kopf.satz":
        "Frigate pasa cada referencia subida por su propio detector de "
        "rostros y rechaza las imágenes en las que no encuentra ninguno. "
        "Esta página comprueba primero lo mismo, te muestra cada "
        "candidata y envía solo lo que marques.",
    "syncauswahl.fehler.titel": "Candidatas no disponibles",
    "syncauswahl.fehler.satz":
        "La lista de candidatas necesita un Frigate accesible — su banco "
        "de rostros es una de las dos mitades de la comparación.",
    "syncauswahl.link_diagnose_auf": "abrir el diagnóstico",
    "syncauswahl.link_diagnose": "diagnóstico",
    "syncauswahl.link_system": "volver a Sistema",
    "syncauswahl.kachel.frigate_abgelehnt": "Frigate rechazó: {fehler}",
    "syncauswahl.kachel.pruefe": "comprobando …",
    "syncauswahl.kachel.vorpruefung_ok": "comprobación previa correcta",
    "syncauswahl.kachel.wohl_abgelehnt":
        "probablemente sería rechazada: {grund}",
    "syncauswahl.kachel.kein_gesicht": "no se detecta ningún rostro",
    "syncauswahl.kachel.kein_grund": "sin motivo indicado",
    "syncauswahl.kachel.senden": "enviar",
    "syncauswahl.kachel.knopf_skip": "omitir",
    "syncauswahl.kachel.attr_skip":
        "No enviar nunca esta imagen — queda recordada y la "
        "sincronización automática también la omite",
    "syncauswahl.kachel.knopf_restore": "restaurar",
    "syncauswahl.kachel.attr_restore":
        "Devolver esta imagen a la lista de candidatas",
    "syncauswahl.geloescht.satz_import":
        "vino de Frigate y allí ya no está",
    "syncauswahl.geloescht.satz_export":
        "se envió exactamente con este nombre y allí ya no está",
    "syncauswahl.geloescht.badge": "eliminada en Frigate",
    "syncauswahl.knopf_anbieten": "ofrecer de nuevo",
    "syncauswahl.geloescht.attr_anbieten":
        "Devolverla a la lista de candidatas — la próxima sincronización "
        "(manual o automática) la envía de nuevo",
    "syncauswahl.geloescht.knopf_respekt": "respetar el borrado",
    "syncauswahl.geloescht.attr_respekt":
        "Recordar que esta imagen debe quedarse fuera de Frigate",
    "syncauswahl.api.badge": "{person} — enviada antes",
    "syncauswahl.api.attr_anbieten":
        "Devolverla a la lista de candidatas (envía una segunda copia si "
        "Frigate aún conserva la primera)",
    "syncauswahl.fr.titel_unbekannt":
        "Reconocimiento facial de Frigate: desconocido",
    "syncauswahl.fr.satz_unbekannt":
        "suslik no pudo leerlo de Frigate ahora mismo — {detail}. Enviar "
        "puede funcionar igualmente; en cualquier caso, Frigate tiene la "
        "última palabra.",
    "syncauswahl.fr.titel_an": "Reconocimiento facial de Frigate: activado",
    "syncauswahl.fr.satz_an":
        "(leído de Frigate al cargar esta página) — acepta subidas de "
        "referencias.",
    "syncauswahl.fr.titel_aus":
        "Reconocimiento facial de Frigate: desactivado",
    "syncauswahl.bilanz.titel": "Balance",
    "syncauswahl.bilanz.hauptzeile":
        "imágenes de referencia · {beide} ya en Frigate · {bereit} listas "
        "para transferir",
    "syncauswahl.bilanz.abgelehnt": "{n} rechazadas por Frigate",
    "syncauswahl.bilanz.geloescht": "{n} eliminadas en Frigate",
    "syncauswahl.bilanz.exportiert":
        "{n} enviadas antes (Frigate las renombró)",
    "syncauswahl.bilanz.abgewaehlt": "{n} deseleccionadas",
    "syncauswahl.bilanz.nur_frigate": "{n} solo en Frigate",
    "syncauswahl.bilanz.je_person": "En Frigate, por persona:",
    "syncauswahl.bilanz.kandidaten.eins": "{n} candidata",
    "syncauswahl.bilanz.kandidaten.viele": "{n} candidatas",
    "syncauswahl.bilanz.vorpruefung": "{n} superan la comprobación previa",
    "syncauswahl.bilanz.gewaehlt_wort": "seleccionadas",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "{n} probablemente serían rechazadas por Frigate (sin marcar, "
        "pero aun así puedes enviarlas).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "{n} fueron rechazadas antes por Frigate (sin marcar; al marcar "
        "una se intenta de nuevo).",
    "syncauswahl.pruef.fehler":
        "la comprobación previa no pudo ejecutarse: {fehler} — las "
        "imágenes sin veredicto siguen seleccionadas.",
    "syncauswahl.pruef.laeuft.eins":
        "comprobando {n} imagen … {fertig}/{gesamt} (esta página se "
        "recarga al terminar)",
    "syncauswahl.pruef.laeuft.viele":
        "comprobando {n} imágenes … {fertig}/{gesamt} (esta página se "
        "recarga al terminar)",
    "syncauswahl.sperre.titel": "El modo de solo lectura está activado",
    "syncauswahl.sperre.satz":
        "suslik no escribe en Frigate ahora mismo.",
    "syncauswahl.knopf_alle": "Seleccionar todo",
    "syncauswahl.knopf_keine": "Quitar toda la selección",
    "syncauswahl.knopf_transfer": "Transferir {n} seleccionadas a Frigate",
    "syncauswahl.leer.titel": "Nada que enviar",
    "syncauswahl.leer.satz":
        "Cada referencia o bien ya llegó a Frigate o bien está "
        "deseleccionada.",
    "syncauswahl.leer.zusatz":
        "Las secciones de abajo enumeran lo que no se puede transferir "
        "sin más.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} probablemente rechazadas",
    "syncauswahl.gruppe.prueft": "{n} aún comprobándose",
    "syncauswahl.geloescht.zusatz": "— tú decides",
    "syncauswahl.geloescht.satz":
        "Estas siguen en tus referencias, pero Frigate ya no las tiene "
        "con el nombre con el que se guardaron. suslik nunca las reenvía "
        "sin tu decisión: borrar un rostro en Frigate puede ser "
        "intencionado. Ofrécela de nuevo para convertirla en candidata "
        "normal — desde entonces la siguiente sincronización, incluida la "
        "automática, la sube. Respeta el borrado para dejarla fuera "
        "definitivamente.",
    "syncauswahl.aufklapp": "— mostrar",
    "syncauswahl.api.titel":
        "{n} exportadas antes — Frigate las guarda con sus propios "
        "nombres",
    "syncauswahl.api.satz":
        "Estas se subieron a través de la API de Frigate, y Frigate "
        "renombra cada referencia que acepta. Por eso suslik no puede "
        "saber por el nombre si siguen allí — ningún contador de esta "
        "página puede demostrarlo en ningún sentido. Nada se reenvía "
        "automáticamente; si sabes que falta una, ofrécela de nuevo (eso "
        "envía una segunda copia si la primera sigue allí).",
    "syncauswahl.api.vergleich":
        "{person}: {n} enviadas por esta vía · Frigate tiene ahora "
        "{bestand} imágenes",
    "syncauswahl.import.zeile.eins": "{n} imagen:",
    "syncauswahl.import.zeile.viele": "{n} imágenes:",
    "syncauswahl.import.mehr": "… y {n} más",
    "syncauswahl.import.satz":
        "Frigate tiene estas imágenes de referencia y suslik no. Al "
        "importarlas se copian a tus referencias; nada cambia en Frigate.",
    "syncauswahl.import.warnung":
        "Esta lista puede incluir tus propias subidas: Frigate renombra "
        "cada referencia que acepta, así que suslik no puede "
        "distinguirlas de los rostros que añadiste directamente en "
        "Frigate. Volver a importarlas duplicaría contenido.",
    "syncauswahl.import.knopf": "Importarlas a suslik",
    "syncauswahl.raus.satz":
        "Recordadas a propósito: estas se quedan en tus referencias, "
        "pero nunca se envían a Frigate, ni siquiera con la sincronización "
        "automática. Restaurar devuelve una a la lista de candidatas.",
    "syncauswahl.alter.unbekannt": "antigüedad desconocida",
    "syncauswahl.alter.sekunden": "hace {s} s",
    "syncauswahl.alter.minuten": "hace {m} min",
    "syncauswahl.alter.stunden": "hace {h} h {m} min",
    "syncauswahl.ergebnis.titel": "Última transferencia",
    "syncauswahl.ergebnis.stopp": "detenida:",
    "syncauswahl.ergebnis.wand":
        "el mismo error tres veces seguidas: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "subida — {bild}",
    "syncauswahl.ergebnis.zaehler": "{hoch} subidas · {weg} no aceptadas",
    "syncauswahl.ergebnis.auswahl": "de {n} seleccionadas",
    "syncauswahl.ergebnis.uebersprungen": "{n} deseleccionadas (omitidas)",
    "syncauswahl.ergebnis.dauer": "duró {n} s",
    # ---------------------------------------------------- routes/live ---
    "live.hinweis_gpu":
        "Por ahora solo funciona con GPU — trabajamos en una opción de "
        "CPU, pero no podemos prometerla.",
    "live.hinweis_cpu":
        "Modo CPU: aquí las vigilancias resultan costosas — la "
        "comprobación rápida suele tardar 1–2 s (una versión con GPU "
        "reacciona en menos de un segundo), y las vigilancias adicionales "
        "se ralentizan entre sí. Cuántas ejecutas lo decides tú; "
        "recomendamos empezar con una.",
    "live.zeile.alter": "(antigüedad: {tage} día(s))",
    "live.test.zeile":
        "prueba de fuente {wann}: {aufloesung} → {skala}, {bilder_s} "
        "fotogramas/s",
    "live.test.durchsatz":
        "(rendimiento, no tasa de entrega — repite la prueba de fuente)",
    "live.test.provider": "proveedor {provider}",
    "live.test.sw": "(descodificación por software)",
    "live.test.entwertet":
        "— INVALIDADA: la fuente cambió desde esta prueba",
    "live.test.fehlgeschlagen":
        "la última prueba de fuente FALLÓ ({wann}): {fehler}",
    "live.messung.zeile": "carga medida el {wann}: {text}",
    "live.messung.veraltet":
        "— OBSOLETA: la fuente cambió desde esta medición, mide de nuevo",
    "live.messung.fehlgeschlagen":
        "la última medición de carga FALLÓ ({wann}): {fehler}",
    "live.zaehler.auftritte": "{n} apariciones",
    "live.zaehler.trigger": "{n} activaciones",
    "live.zaehler.alerts": "{n} avisos",
    "live.zaehler.letzter": "última activación {zeit}",
    "live.zaehler.kopf": "desde el arranque del motor:",
    "live.engine.titel_aus": "Motor en directo: parado",
    "live.engine.satz_aus":
        "Sin latido del proceso del motor. Las tarjetas muestran los "
        "ajustes guardados; activar, probar contra una vigilancia en "
        "marcha y medir la carga necesitan el motor — el servicio lo "
        "arranca automáticamente en cuanto al menos una vigilancia esté "
        "activada.",
    "live.engine.cpu_mit_limit":
        "CPU de suslik ahora mismo: {kerne} de {limit} núcleos permitidos "
        "(todo el contenedor: vigilancias, análisis, servicio)",
    "live.engine.cpu_ohne_limit":
        "CPU de suslik ahora mismo: {kerne} núcleos (todo el contenedor: "
        "vigilancias, análisis, servicio)",
    "live.engine.rss": "RSS del motor {rss} MB",
    "live.engine.grundkosten": "coste base {mb} MB",
    "live.engine.je_stream": "{mb} MB por stream ({quelle})",
    "live.engine.je_stream_fehlt":
        "RAM por stream aún sin medir en esta máquina",
    "live.engine.ram_frei": "{mb} MB de RAM libres ({quelle})",
    "live.engine.ram_unlesbar":
        "RAM: no se puede leer el límite del contenedor",
    "live.engine.detektor": "detector {ms} ms/fotograma ({quelle})",
    "live.engine.drossel":
        "nivel de limitación {stufe}, uso {auslastung}",
    "live.engine.rest":
        "tras un stream más: quedarían ~{mb} MB de RAM",
    "live.engine.rest_warnung":
        "— POR DEBAJO del mínimo de seguridad, sin hueco adicional",
    "live.engine.kapazitaet":
        "capacidad: hasta {n} vigilancia(s) (tope duro {hart}) — limitada "
        "por: {grund}",
    "live.engine.hart": "tope duro de {hart} vigilancias",
    "live.engine.titel_standalone":
        "Motor en directo: en marcha (motor independiente detectado)",
    "live.engine.titel_an": "Motor en directo: en marcha",
    "live.gruppe.laufend": "En marcha",
    "live.gruppe.bereit": "Listas",
    "live.gruppe.rest": "Sin configurar",
    "live.gruppe.versteckt": "Ocultas",
    "live.gruppe.ohne_area": "Sin área",
    "live.kachel.attr_fremd":
        "configurada aquí, pero esta cámara ahora mismo no está en "
        "Frigate",
    "live.kachel.pill_fremd": "no está en Frigate",
    "live.kachel.attr_detect":
        "stream detect de Frigate — la resolución real del stream aparece "
        "cuando el servicio lo sondea o se ejecuta una prueba de fuente",
    "live.knopf_konfigurieren": "Configurar",
    "live.knopf_test": "Ejecutar prueba de fuente",
    "live.knopf_messung": "Medir carga",
    "live.knopf_enable": "Activar",
    "live.knopf_disable": "Desactivar",
    "live.knopf_zeigen": "Mostrar",
    "live.knopf_verstecken": "Ocultar",
    "live.banner.kameraliste":
        "No se pudo leer la lista de cámaras de Frigate: {fehler}",
    "live.schalter.ungruppiert": "vista sin agrupar",
    "live.schalter.area": "agrupar por área",
    "live.sperre.cpu_titel": "Modo CPU",
    "live.sperre.titel": "No disponible en esta versión",
    "live.sperre.satz":
        "La vigilancia en directo requiere una versión con GPU — valen "
        "los gráficos integrados de Intel (imágenes gpu / gpu-legacy), "
        "una tarjeta NVIDIA (imagen cuda) o una tarjeta AMD (imagen "
        "rocm).",
    "live.sperre.cpu_only":
        "No está disponible en la imagen de solo CPU.",
    "live.erklaer.titel":
        "Vigilancia en directo — reacción inmediata en el stream de la "
        "cámara",
    "live.erklaer.satz1":
        "Una vigilancia en directo se conecta directamente a un stream de "
        "cámara y reacciona mientras la persona sigue en la imagen: el "
        "primer rostro inicia una comprobación y, tras el número "
        "configurado de detecciones consistentes, sale una señal "
        "verificada — el objetivo es menos de un segundo (medido: "
        "199–801 ms en el equipo de referencia). Úsala para disparar "
        "automatizaciones del hogar, p. ej. vía MQTT.",
    "live.erklaer.link":
        "Leer más: cómo funciona la vigilancia en directo",
    "live.titel": "Vigilancia en directo",
    "live.leer.titel": "No se han encontrado cámaras.",
    "live.leer.hinweis":
        "Configura primero la conexión con Frigate — las tarjetas "
        "aparecen por cámara.",
    "live.knopf_speichern": "Guardar",
    "live.detail.titel": "Vigilancia en directo — {name}",
    "live.abschnitt.quelle": "Fuente",
    "live.quelle.proxy":
        "restream de go2rtc vía Frigate (predeterminado, recomendado)",
    "live.quelle.direct":
        "URL del productor de la cámara, descubierta vía go2rtc",
    "live.quelle.url": "una URL de stream que introduces tú",
    "live.detail.url_label": "URL del stream (solo con fuente 'url'):",
    "live.detail.url_hinweis":
        "las credenciales de la URL se enmascaran en todos los sitios "
        "donde se muestran — deja el campo tal como aparece para "
        "conservar la URL guardada, o pega una nueva",
    "live.detail.quelle_hinweis":
        "Cambiar la fuente invalida la prueba de fuente — ejecútala de "
        "nuevo antes de activar.",
    "live.abschnitt.aufloesung": "Resolución de procesado",
    "live.hoehe.default": "predeterminada (1080p)",
    "live.hoehe.h360":
        "360p — reserva para GPU débil, el nombre salta lo más tarde "
        "(medido)",
    "live.hoehe.h720":
        "720p — descodificación más ligera, el nombre salta más tarde",
    "live.hoehe.h1080":
        "1080p — punto óptimo (medido: el nombre ~2,4 s antes que con "
        "720p)",
    "live.hoehe.h1440": "1440p — sin ganancia medida frente a 1080p",
    "live.hoehe.h2160":
        "2160p — 4K nativo, ganancia marginal, máximo coste de "
        "descodificación",
    "live.abschnitt.alarm": "Cadena de avisos",
    "live.detail.ende_label": "Fin tras ausencia de rostro (s):",
    "live.detail.ende_hinweis":
        "una aparición termina tras estos segundos sin rostro (3–120)",
    "live.detail.scharf_label": "Rearme tras (s):",
    "live.detail.scharf_hinweis":
        "segundos mínimos entre avisos — con alguien presente vuelve a "
        "avisar pasado este tiempo; 0 = cada activación avisa (0–3600)",
    "live.abschnitt.kanaele": "Canales de notificación",
    "live.detail.namensschaetzung":
        "Los avisos incluyen una estimación preliminar del nombre "
        "(\"probablemente X\") cuando el rostro coincide con una persona "
        "conocida — nunca se guarda, nunca se usa para el aprendizaje.",
    "live.abschnitt.test": "Probar y medir",
    "live.detail.gesperrt_hinweis":
        "probar y medir no están disponibles mientras la vigilancia en "
        "directo esté bloqueada en esta máquina — la nota al principio de "
        "esta página explica por qué.",
    "live.knopf_messung_lang": "Medir carga (15–30 s)",
    "live.detail.messung_hinweis":
        "la medición de carga pausa las demás vigilancias mientras se "
        "ejecuta",
    "live.detail.link_zurueck": "volver a la vista general",
    # ----------------------------------------------- routes/erkennung ---
    "erkennung.titel": "Reconocimiento",
    "erkennung.kopf.satz":
        "Las cuatro vías por las que tu sistema puede reconocer a alguien "
        "— cada una es su propia tarjeta: actívala o desactívala, "
        "comprueba que funciona, configúrala. El interruptor de Directo "
        "actúa al momento; los cambios de cuerpo y visión se aplican con "
        "Guardar + reiniciar.",
    "erkennung.kipp.label": "Activado",
    "erkennung.kipp.attr_verriegelt":
        "siempre activo — todas las demás vías se apoyan en el veredicto "
        "del rostro",
    "erkennung.link_how": "Cómo funciona &#8230;",
    "erkennung.live.titel": "Vigilancia en directo",
    "erkennung.live.beweis_prefix": "observando",
    "erkennung.live.beweis_zaehler": "{an} de {ges}",
    "erkennung.live.beweis_suffix": "cámaras configuradas",
    "erkennung.live.beweis_keine_laufend":
        "cámara(s) configurada(s), ninguna en marcha",
    "erkennung.live.beweis_keiner":
        "aún no hay ninguna vigilancia configurada",
    "erkennung.live.expert_schalter":
        "desactivar detiene todas las vigilancias en marcha; activar "
        "arranca todas las vigilancias configuradas (el filtro por cámara "
        "sigue aplicándose)",
    "erkennung.live.link_prokamera": "control por cámara",
    "erkennung.live.knopf_kameras": "Elegir cámaras …",
    "erkennung.knopf_register_face": "Registrar rostro …",
    "erkennung.gesicht.titel": "Reconocimiento facial",
    "erkennung.gesicht.satz":
        "La vía más precisa: cada recorrido por la propiedad se coteja "
        "con los rostros de las personas que has enseñado al sistema. Es "
        "la columna vertebral — cuerpo y visión dependen de su veredicto "
        "del recorrido, así que hoy no tiene interruptor de apagado.",
    "erkennung.gesicht.beweis_personen": "{n} personas",
    "erkennung.gesicht.beweis_bilder": "{n} imágenes de referencia",
    "erkennung.gesicht.knopf_verwalten": "Gestionar personas …",
    "erkennung.koerper.titel": "Reconocimiento corporal",
    "erkennung.koerper.satz":
        "Reconoce a los miembros del hogar incluso cuando no se ve ningún "
        "rostro, por complexión y postura — aprende por sí solo de las "
        "imágenes revisadas.",
    "erkennung.koerper.beweis_kein_modell":
        "aún no hay modelo de persona — primero aprende y revisa",
    "erkennung.status.kein_modell":
        "inactivo (aún no hay un modelo de persona entrenado activo)",
    "erkennung.status.hier_aus": "inactivo (desconectado aquí)",
    "erkennung.status.vision_aus":
        "inactivo (la detección de visión está desconectada)",
    "erkennung.koerper.link_modell": "estado del modelo",
    "erkennung.koerper.knopf_status": "Estado del modelo …",
    "erkennung.koerper.knopf_register": "Registrar cuerpo …",
    "erkennung.vision.titel": "Visión por IA",
    "erkennung.vision.beta": "Beta",
    "erkennung.vision.satz":
        "Una IA de imágenes como árbitro para los casos difíciles. "
        "Necesita un endpoint de modelo (local o de pago) — cada "
        "comprobación cuesta peticiones.",
    "erkennung.vision.beweis_an": "endpoint conectado",
    "erkennung.vision.beweis_aus": "sin endpoint conectado",
    "erkennung.vision.knopf_connect": "Conectar un modelo …",
    "erkennung.vision.knopf_register": "Registrar visión …",
    "erkennung.abschnitt_property": "Preparación de la propiedad",
    "erkennung.areas.titel": "Áreas",
    "erkennung.areas.satz":
        "Qué parte de la propiedad cuenta: define áreas para que los "
        "avisos solo salten donde te importa — la entrada de coches "
        "cuenta, la calle detrás de la valla no.",
    "erkennung.areas.beweis_zahl": "área(s) definida(s)",
    "erkennung.areas.beweis_keine": "aún no hay áreas — todo cuenta",
    "erkennung.areas.knopf": "Gestionar áreas &#8230;",
    "erkennung.knopf_speichern": "Guardar + reiniciar",
    # --------------------------------------------------- routes/faces ---
    "faces.titel": "Rostros",
    "faces.link_how": "Cómo funciona &#8230;",
    "faces.bekannt.titel": "Personas conocidas",
    "faces.bekannt.knopf_verwalten": "Gestionar personas &#8230;",
    "faces.bekannt.knopf_register": "Registrar rostro &#8230;",
    "faces.bekannt.leer":
        "aún no hay personas aprendidas — registra el primer rostro "
        "arriba",
    "faces.bekannt.beweis_personen": "{n} personas",
    "faces.bekannt.beweis_bilder": "{n} imágenes de referencia",
    "faces.lernen.titel": "Aprendizaje",
    "faces.lernen.knopf_start": "Iniciar aprendizaje &#8230;",
    "faces.lernen.knopf_review": "Revisar sugerencias &#8230;",
    "faces.lernen.beweis_offen": "sugerencia(s) a la espera de revisión",
    "faces.lernen.beweis_leer":
        "nada en espera — el sistema sigue recogiendo por su cuenta",
    "faces.lernen.satz": "Revisa lo que han recogido las cámaras.",
    "faces.unbekannt.titel": "Desconocidos",
    "faces.unbekannt.knopf": "Revisar desconocidos &#8230;",
    "faces.unbekannt.beweis_offen":
        "visitante(s) desconocido(s) recurrente(s)",
    "faces.unbekannt.beweis_leer": "sin visitantes desconocidos recurrentes",
    "faces.unbekannt.satz": "Visitantes aún sin nombre.",
    "faces.qualitaet.titel": "Calidad de imagen",
    "faces.qualitaet.stand":
        "última comprobación {wann} &middot; {n} hallazgo(s)",
    "faces.qualitaet.knopf_check": "Comprobar la calidad de mis imágenes",
    "faces.qualitaet.popup_satz":
        "Vuelve a medir cada imagen de referencia y busca imágenes "
        "débiles, casi duplicadas y rostros confundidos. Tarda alrededor "
        "de un minuto y se ejecuta en segundo plano.",
    "faces.qualitaet.label_alle": "Todas las personas",
    "faces.qualitaet.label_eine": "Una persona:",
    "faces.qualitaet.knopf_start": "Iniciar comprobación",
    "faces.qualitaet.knopf_abbrechen": "Cancelar",
    "faces.qualitaet.knopf_ergebnisse": "Últimos resultados &#8230;",
    "faces.qualitaet.satz": "Encuentra imágenes débiles o confundidas.",
    # ----------------------------------------------- routes/qualitaet ---
    "qualitaet.kopf.titel": "Calidad — banco de referencias",
    "qualitaet.kopf.hinweis":
        "toca una persona abajo para ver todas sus imágenes con las "
        "débiles marcadas.",
    "qualitaet.kopf.stand": "A fecha de: {stand} · {n} referencias",
    "qualitaet.kopf.knopf_neu": "Volver a comprobar ahora",
    "qualitaet.lauf.fehler":
        "la última comprobación FALLÓ: {fehler} &mdash; iníciala de "
        "nuevo.",
    "qualitaet.lauf.checking": "comprobando imagen {i} de {n} &hellip;",
    "qualitaet.lauf.reload_person":
        "recarga esta página después para ver el resultado nuevo.",
    "qualitaet.lauf.reload_auto": "la página se actualiza sola.",
    "qualitaet.lauf.abgebrochen":
        "la última comprobación no terminó (reinicio del servicio o se "
        "detuvo) &mdash; iníciala de nuevo.",
    "qualitaet.tabelle.kopf_person": "persona",
    "qualitaet.tabelle.kopf_bilder": "imágenes",
    "qualitaet.tabelle.kopf_gut": "buenas",
    "qualitaet.tabelle.kopf_mittel": "aceptables",
    "qualitaet.tabelle.kopf_unter": "bajo el listón",
    "qualitaet.tabelle.kopf_links": "&larr; izquierda",
    "qualitaet.tabelle.kopf_front": "frontal",
    "qualitaet.tabelle.kopf_rechts": "derecha &rarr;",
    "qualitaet.tabelle.kopf_doppel": "duplicadas",
    "qualitaet.tabelle.kopf_verwechslung": "confusión",
    "qualitaet.person.funde": "{n} imagen(es) que merecen un vistazo",
    "qualitaet.person.verwechselt": "posible confusión",
    "qualitaet.person.alles_gut": "todo bien",
    "qualitaet.ergebnis.alles_gut": "Todo bien.",
    "qualitaet.ergebnis.alles_gut_satz":
        "Comprobadas {n} imágenes de {np} personas &mdash; nada requiere "
        "tu atención.",
    "qualitaet.wort.defekt": "archivo dañado",
    "qualitaet.wort.kein_gesicht": "ningún rostro encontrado",
    "qualitaet.wort.zu_klein": "demasiado pequeña",
    "qualitaet.wort.unscharf": "borrosa",
    "qualitaet.wort.schwach": "imagen débil",
    "qualitaet.galerie.looks_like": "se parece a {name}",
    "qualitaet.galerie.doppel": "duplicada — la conservada la cubre",
    "qualitaet.galerie.gut": "buena",
    "qualitaet.galerie.gut_behalten":
        "buena — la conservada de sus duplicadas",
    "qualitaet.galerie.okay": "aceptable",
    "qualitaet.galerie.satz_gut": "Las {n} imágenes se ven bien.",
    "qualitaet.galerie.satz_funde":
        "{funde} de {n} imágenes merecen un vistazo — las dos pestañas de "
        "la derecha las contienen. Marca lo que quieras quitar — nada "
        "ocurre sin tu clic.",
    "qualitaet.reiter.gut": "Buenas ({n})",
    "qualitaet.reiter.check": "Revisar estas ({n})",
    "qualitaet.reiter.weg": "Se sugiere quitar ({n})",
    "qualitaet.galerie.knopf_alle": "Seleccionar todo",
    "qualitaet.galerie.knopf_keine": "Quitar toda la selección",
    "qualitaet.galerie.knopf_entfernen": "Quitar seleccionadas",
    "qualitaet.galerie.leer_gruppe": "nada en este grupo.",
    "qualitaet.galerie.titel": "{name} — calidad de imagen",
    "qualitaet.galerie.link_zurueck": "&larr; volver a la vista general",
    "qualitaet.galerie.leer_person": "no hay imágenes de esta persona.",
    "qualitaet.leer.titel": "Aún no se ha calculado ninguna comprobación.",
    "qualitaet.leer.hinweis":
        "Pulsa arriba en Volver a comprobar ahora.",
    # ---------------------------------------------- routes/lernwizard ---
    "lernwizard.titel": "Aprendizaje",
    "lernwizard.link_how": "Cómo funciona &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Preparación",
    "lernwizard.phase.ernte": "Extracción (recoger rostros)",
    "lernwizard.phase.anker": "Agrupación (anclas)",
    "lernwizard.phase.benennung": "Poner nombres (tu paso)",
    "lernwizard.phase.neben_ansichten": "Vistas laterales",
    "lernwizard.phase.ganzkoerper": "Referencias de cuerpo entero",
    "lernwizard.phase.uebernahme": "Incorporación al Master",
    "lernwizard.phase.fertig": "Terminado",
    "lernwizard.phase.aktuell": "(actual)",
    "lernwizard.phase.link_benennen": "abre los grupos y ponles nombre",
    "lernwizard.wizard.titel": "Aprender personas — ejecución guiada",
    "lernwizard.wizard.satz":
        "Planifica un aprendizaje sobre tus propias grabaciones. "
        "Preparación, extracción, agrupación, nombres e incorporación al "
        "reconocimiento se ejecutan de verdad.",
    "lernwizard.wizard.lage_b":
        "B — se ampliarán las referencias/desconocidos existentes",
    "lernwizard.wizard.lage_a": "A — arranque en frío, aún sin rostros",
    "lernwizard.badge.unbekannt": "visitantes desconocidos",
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} visitante desconocido espera en",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} visitantes desconocidos esperan en",
    "lernwizard.link_unbekannte": "Personas &rarr; Desconocidos",
    "lernwizard.wizard.unbekannt_hinweis":
        "Rostros recogidos hoy que no coinciden con ninguna persona "
        "conocida — allí puedes ponerles nombre, fusionarlos o "
        "silenciarlos al momento; para eso no hace falta ningún "
        "aprendizaje.",
    "lernwizard.wizard.start_titel": "Punto de partida",
    "lernwizard.wizard.start_hinweis":
        "Interruptor de limpieza para los desconocidos recogidos "
        "automáticamente: llega con la fase de nombres.",
    "lernwizard.wizard.knopf_letzte": "últimos {n}",
    "lernwizard.wizard.knopf_alle": "TODOS los alcanzables",
    "lernwizard.wizard.attr_eigen": "N propio",
    "lernwizard.wizard.knopf_go": "ir",
    "lernwizard.wizard.scope_titel": "Alcance (eventos, no días)",
    "lernwizard.wizard.scope_hinweis":
        "TODOS repasa todo el historial alcanzable (limitado por la "
        "retención de Frigate — el balance de abajo muestra hasta dónde).",
    "lernwizard.wizard.auswahl_titel": "Tu selección",
    "lernwizard.wizard.auswahl_zeile":
        "últimos {n} eventos de persona = hasta {wann} · {clips} con clip "
        "disponible",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} más antiguos sin clip se omitirán",
    "lernwizard.wizard.auswahl_hinweis":
        "El corte es exacto en N — completar selecciones hasta recorridos "
        "completos por la propiedad llega con la fase de agrupación.",
    "lernwizard.wizard.q_teilgemessen":
        "velocidad de análisis medida en ESTA máquina; la estimación de "
        "descarga usa valores por defecto",
    "lernwizard.wizard.q_gemessen": "medido en ESTA máquina",
    "lernwizard.wizard.q_skip":
        ", medición omitida en esta máquina ({grund})",
    "lernwizard.wizard.q_wartet":
        ", la medición espera un hueco de análisis libre …",
    "lernwizard.wizard.q_laeuft": ", midiendo ahora …",
    "lernwizard.wizard.q_rueckfall":
        "valores de reserva — aún sin medir aquí",
    "lernwizard.wizard.dauer_titel": "Duración estimada",
    "lernwizard.wizard.dauer_zeile":
        "análisis ~{analyse} · descargas de clips ~{download} · "
        "calentamiento único {kalt}",
    "lernwizard.wizard.dauer_gesamt": "total ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Umbrales (ajustables en Avanzado)",
    "lernwizard.wizard.frage":
        "¿Aprender de todos los {n} eventos? Duración estimada ~{gesamt} "
        "(análisis {analyse} + descargas {download}). La ejecución se "
        "puede abortar en cualquier momento.",
    "lernwizard.wizard.fps_titel": "Fotogramas de análisis por segundo",
    "lernwizard.wizard.knopf_start": "Crear esta ejecución",
    "lernwizard.seg.vorbereiten": "Preparar",
    "lernwizard.seg.sammeln": "Recoger rostros",
    "lernwizard.seg.sortieren": "Ordenar en grupos",
    "lernwizard.status.laeuft_seit": "en marcha desde hace {dauer}",
    "lernwizard.status.rest": "quedan {rest}",
    "lernwizard.status.fertig_in": "terminado en {dauer}",
    "lernwizard.status.aufnahmen": "grabaciones: {n}",
    "lernwizard.status.bilder": "{n} imágenes recogidas hasta ahora",
    "lernwizard.puls.working": "trabajando — actualizado hace {s}s",
    "lernwizard.puls.stumm":
        "sin novedades desde hace {s}s — un clip largo puede tardar "
        "minutos; si esto sigue creciendo, mira /log",
    "lernwizard.zeile.kaputt": "{n} líneas ilegibles contadas",
    "lernwizard.zeile.anker_link": "ver los {n} grupos de anclas",
    "lernwizard.ergebnis.bilder.eins": "recogida {n} imagen",
    "lernwizard.ergebnis.bilder.viele": "recogidas {n} imágenes",
    "lernwizard.ergebnis.aufnahmen.eins": "de {n} grabación",
    "lernwizard.ergebnis.aufnahmen.viele": "de {n} grabaciones",
    "lernwizard.ergebnis.gruppen.eins": "ordenadas en {n} grupo",
    "lernwizard.ergebnis.gruppen.viele": "ordenadas en {n} grupos",
    "lernwizard.ergebnis.beiseite": "({n} descartadas)",
    "lernwizard.kachel.lauf": "Aprendizaje",
    "lernwizard.kachel.sammeln": "Recoger y ordenar",
    "lernwizard.kachel.benennen": "Poner nombre a los grupos",
    "lernwizard.kachel.fertig": "Hecho &mdash; ya cuentan",
    "lernwizard.such.titel": "Buscar rostros en los eventos",
    "lernwizard.such.klein": "repasa tus grabaciones hacia atrás",
    "lernwizard.pop.satz":
        "Repasa tus grabaciones hacia atrás y recoge rostros. En el día a "
        "día, el sistema sigue aprendiendo por su cuenta.",
    "lernwizard.pop.label_letzte": "Repasar los últimos",
    "lernwizard.pop.wort_events": "eventos",
    "lernwizard.pop.hint_n":
        "cuántas grabaciones recientes comprobar (hasta {max})",
    "lernwizard.pop.label_tag": "Un día entero:",
    "lernwizard.pop.hint_tag":
        "todas las grabaciones de ese día, sean cuantas sean",
    "lernwizard.pop.wort_fps": "imágenes por segundo",
    "lernwizard.pop.hint_fps":
        "más imágenes encuentran más ángulos, pero la búsqueda tarda más",
    "lernwizard.pop.label_skip": "Omitir eventos ya buscados",
    "lernwizard.pop.hint_skip":
        "cada búsqueda continúa más hacia el pasado &mdash; desmarca para "
        "volver a buscar en los eventos más recientes",
    "lernwizard.pop.alle_gesichter": "Todos los rostros",
    "lernwizard.pop.eine_person": "Solo una persona:",
    "lernwizard.pop.hint_person":
        "con una persona elegida, los grupos coincidentes se listan "
        "primero &mdash; no se oculta nada",
    "lernwizard.pop.knopf_start": "Iniciar búsqueda",
    "lernwizard.knopf_abbrechen": "Cancelar",
    "lernwizard.k1.unbekannt.eins": "{n} visitante desconocido de hoy:",
    "lernwizard.k1.unbekannt.viele": "{n} visitantes desconocidos de hoy:",
    "lernwizard.k1.gestartet": "Ejecución iniciada {wann}",
    "lernwizard.k1.scope": "alcance {n} eventos",
    "lernwizard.k1.tag": "día {tag}",
    "lernwizard.k2.satz":
        "Se ejecuta solo &mdash; puedes cerrar esta página y volver más "
        "tarde.",
    "lernwizard.k2.knopf_abort": "Abortar ejecución",
    "lernwizard.k3.satz_warten":
        "El único paso que te necesita: un grupo debería ser una persona "
        "&mdash; di quién es, o sáltalo.",
    "lernwizard.k3.keine_gesichter":
        "Esta vez no hay rostros nuevos &mdash; nada que nombrar. No pasa "
        "nada: solo significa que en las grabaciones no había nadie "
        "nuevo.",
    "lernwizard.knopf_neuer_lauf": "Iniciar una ejecución nueva",
    "lernwizard.k3.gruppe_offen":
        "El grupo actual está abierto abajo, a ancho completo.",
    "lernwizard.k3.alle_erledigt": "Todos los grupos están atendidos.",
    "lernwizard.chip.bilder": "{n} imágenes",
    "lernwizard.k3.verworfen.eins":
        "{n} grupo descartado (sin rostros utilizables o por ti) "
        "&middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} grupos descartados (sin rostros utilizables o por ti) "
        "&middot;",
    "lernwizard.k3.link_einsehen": "ver",
    "lernwizard.k3.done_weiter":
        "{erledigt} de {gesamt} hechos &mdash; el siguiente está listo.",
    "lernwizard.k3.done_punkt": "{erledigt} de {gesamt} hechos.",
    "lernwizard.k3.wartend.eins": "{n} grupo te espera.",
    "lernwizard.k3.wartend.viele": "{n} grupos te esperan.",
    "lernwizard.k4.adopt_bilder.eins": "{n} imagen incorporada para",
    "lernwizard.k4.adopt_bilder.viele": "{n} imágenes incorporadas para",
    "lernwizard.k4.adopt_personen.eins": "{n} persona",
    "lernwizard.k4.adopt_personen.viele": "{n} personas",
    "lernwizard.k4.zaehlen_sofort":
        "cuentan para el reconocimiento de inmediato.",
    "lernwizard.k4.link_qs":
        "comprobar la calidad de las referencias &#8230;",
    "lernwizard.k4.nichts":
        "esta vez no se incorporó ninguna imagen nueva (grupos omitidos o "
        "ya cubiertos).",
    "lernwizard.k4.wiederholen":
        "Repítelo cada pocos días, o deja que la vista del día complete "
        "entretanto a las personas conocidas.",
    "lernwizard.k4.knopf_faces": "Volver a Rostros",
    "lernwizard.k4.hinweis":
        "Las imágenes con nombre se convierten en referencias y cuentan "
        "para el reconocimiento de inmediato.",
    "lernwizard.zw.grund_maessig": "calidad de imagen solo aceptable",
    "lernwizard.zw.attr_clip": "abrir el clip",
    "lernwizard.blick.links": "Mirando a la izquierda",
    "lernwizard.blick.frontal": "Frontal",
    "lernwizard.blick.rechts": "Mirando a la derecha",
    "lernwizard.blick.leer":
        "no hay imágenes utilizables de este ángulo en el grupo",
    "lernwizard.blick.legende":
        "({gut} buenas, {grenz} al límite de {n} comprobadas)",
    "lernwizard.zw.titel": "Grupo {pos} de {gesamt} &mdash; ¿quién es?",
    "lernwizard.zw.satz":
        "Un grupo debería ser una persona. Toca una imagen para dejarla "
        "fuera &mdash; luego di quién es, o salta el grupo.",
    "lernwizard.bekannt.system": "ya está en tu sistema",
    "lernwizard.bekannt.anker": "con nombre en otro grupo",
    "lernwizard.zw.knopf_adopt": "Incorporar como {name}",
    "lernwizard.zw.knopf_ja": "Sí, es {name}",
    "lernwizard.zw.fehler":
        "la comprobación de imágenes no pudo ejecutarse (mira /log) "
        "&mdash; recarga para reintentar; Omitir y Eliminar siguen "
        "funcionando.",
    "lernwizard.zw.warte":
        "comprobando las imágenes de este grupo contra el listón de "
        "referencia &mdash; unos segundos &hellip;",
    "lernwizard.zw.knopf_andere": "Otra persona &#8230;",
    "lernwizard.zw.attr_name": "nombre de la persona (nuevo o existente)",
    "lernwizard.zw.knopf_save": "Guardar nombre",
    "lernwizard.zw.knopf_skip": "Omitir este grupo",
    "lernwizard.zw.frage_delete":
        "¿Eliminar este grupo? Sus imágenes se eliminan y un nombre "
        "pendiente se descarta; el grupo queda recordado para que las "
        "nuevas extracciones de los mismos eventos sigan en silencio.",
    "lernwizard.zw.knopf_delete": "Eliminar este grupo",
    "lernwizard.zw.link_detail": "vista de detalle completa",
    "lernwizard.zw.detail_zusatz":
        "(todas las imágenes con motivos, selección experta)",
    "lernwizard.erfolg.titel": "Agrupación terminada",
    "lernwizard.erfolg.cluster.eins": "{n} grupo de rostros listo:",
    "lernwizard.erfolg.cluster.viele": "{n} grupos de rostros listos:",
    "lernwizard.erfolg.knopf_anker": "Ver los grupos de anclas",
    "lernwizard.erfolg.hinweis": "abre un grupo para ponerle nombre",
    "lernwizard.expert.phasen_titel": "Fases",
    "lernwizard.expert.phasen_hinweis":
        "Preparación, extracción, agrupación, nombres e incorporación al "
        "Master se ejecutan de verdad en esta versión — las vistas "
        "laterales y las referencias de cuerpo entero se activarán con "
        "las próximas actualizaciones.",
    "lernwizard.expert.progress_titel": "Progreso",
    "lernwizard.expert.anker_bisher": "anclas hasta ahora: {n}",
    "lernwizard.expert.progress_rest":
        "creada {wann} · alcance {n} eventos · sobrevive a reinicios "
        "(reanudación incorporada)",
    "lernwizard.expert.lauf_bleibt":
        "esta ejecución se queda — sus anclas siguen disponibles",
    # --------------------------------- Stufe 1: Einhang/Skelett (webui) ---
    "nav.bereich.activity": "Actividad",
    "nav.bereich.faces": "Rostros",
    "nav.bereich.learn": "Aprender",
    "nav.bereich.person": "Persona",
    "nav.bereich.vision": "Visión",
    "nav.bereich.live": "En directo",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Configuración",
    "nav.bereich.erkennungstest": "Prueba de reconocimiento",
    "nav.bereich.system": "Sistema",
    "nav.heute": "Hoy",
    "nav.ereignisse": "Eventos",
    "nav.offen": "Por etiquetar",
    "nav.faces": "Rostros",
    "nav.gesichter": "Conocidos",
    "nav.unbekannte": "Desconocidos",
    "nav.qualitaet": "Calidad",
    "nav.lernlauf": "Aprendizaje",
    "nav.anker": "Anclas",
    "nav.lernen": "Sugerencias",
    "nav.person": "Imágenes de cuerpo entero",
    "nav.person_kontrolle": "Imágenes evaluadas",
    "nav.person_modell": "Estado del modelo",
    "nav.personlauf": "Aprendizaje de persona",
    "nav.vision": "Detección de visión",
    "nav.live": "Vigilancia en directo",
    "nav.live_alerts": "Avisos en directo",
    "nav.erkennung": "Reconocimiento",
    "nav.kameras": "Cámaras",
    "nav.benachrichtigungen": "Notificaciones",
    "nav.areas": "Áreas",
    "nav.kette": "Cadena de reconocimiento",
    "nav.konfiguration": "Avanzado",
    "nav.erkennungstest": "Prueba de reconocimiento",
    "nav.system": "Sistema",
    "nav.sync_auswahl": "Sincronización con Frigate",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Registro del servicio",
    "ui.fuss.docs": "Documentación",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip": "Easy muestra las páginas esenciales — Expert lo muestra todo. Nada se borra, Easy solo oculta.",
    "ui.live.chip": "En directo",
    "ui.theme.knopf": "Tema",
    "ui.theme.tooltip": "Cambiar entre claro y oscuro",
    "ui.theme.aria": "Cambiar el tema de color",
    "ui.sprache.tooltip": "Idioma de esta instalación — se aplica a todas las páginas y a las notificaciones",
    "ui.upd.link": "actualización {tag}",
    "ui.upd.tooltip": "Hay una versión más reciente de suslik en GitHub",
    "ui.upd.titel": "Actualización disponible",
    # ui.upd.satz ist der erste deklarierte t_html-Schluessel (HTML_SCHLUESSEL,
    # core/sprache.py) — Tag-Folge muss in jeder Sprache identisch sein.
    "ui.upd.satz": "Hay una imagen de suslik más reciente (<b>{tag}</b>) en GitHub — <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">notas de la versión</a>. Descarga la nueva imagen y reinicia para actualizar; tus datos y ajustes se conservan.",
    "ui.wn.titel": "Novedades",
    "ui.wn.x_tooltip": "Ocultar hasta la próxima versión",
    "ui.wn.x_aria": "Descartar",
    "ui.wn.mehr": "Mostrar todo ({n})",
    "ui.wn.weniger": "Mostrar menos",
    "ui.hinweis.englisch": "Esta página aún no está traducida — su contenido se muestra de momento en inglés.",
    # --------------------------------- Stufe 1: Seitentitel (verifyd) ---
    "titel.setup": "Asistente inicial",
    "titel.anker_detail": "Ancla",
    "titel.aehnliche": "Rostros coincidentes",
    "titel.live_kamera": "En directo — {kamera}",
    "titel.video": "Vídeo",
    "titel.event": "Evento",
    "titel.vision_galerie": "Crear una galería",
    "titel.hilfe": "Cómo funciona",
    # --------------------------------- Stufe 1: Setup-Wizard Schritt 0 ---
    "setup.sprache.titel": "Idioma",
    "setup.sprache.satz": "Elige el idioma de esta instalación — se aplica de inmediato y también a las notificaciones. Puedes cambiarlo en cualquier momento con el selector de la cabecera.",
    # --------------------------------- Stufe 1: js.* (window.T, app.js) ---
    # VERTRAG: app.js liest NUR js.*-Schluessel (TT() mit EN-Fallback ==
    # diesem Wert); jede Richtung prueft die Gate-Stufe Sprach-Deckung.
    "js.status.fehler": "error",
    "js.status.fehler_gross": "Error",
    "js.status.fehler_detail": "error: {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "guardando …",
    "js.status.gespeichert": "guardado",
    "js.status.senden": "enviando …",
    "js.status.starten": "iniciando …",
    "js.status.laeuft": "en curso …",
    "js.status.laeuft_wort": "en curso",
    "js.status.pruefen": "comprobando …",
    "js.status.suchen": "buscando …",
    "js.status.lernen": "aprendiendo …",
    "js.status.hinzufuegen": "añadiendo …",
    "js.status.entfernen": "quitando …",
    "js.status.loeschen": "eliminando …",
    "js.status.hochladen": "subiendo …",
    "js.status.wiederherstellen": "restaurando …",
    "js.status.ueberspringen": "omitiendo …",
    "js.status.siehe_log": "ver el registro del servicio",
    "js.status.diagnose": "diagnóstico",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Cancelar",
    "js.neustart.zurueck": "El servicio ha vuelto, cargando …",
    "js.neustart.kommt": "El servicio está volviendo …",
    "js.neustart.gespeichert": "Guardado. El servicio se reinicia, espera …",
    "js.neustart.warten": "El servicio se reinicia, espera …",
    "js.konfig.frage": "¿Guardar la configuración y reiniciar el servicio?",
    "js.lernlauf.fps_zeile": "≈ total ~{dauer} a {fps}/s",
    "js.lernlauf.tag_fehlt": "elige primero un día",
    "js.lernlauf.abbruch_frage": "¿Abortar este aprendizaje?",
    "js.notif.frage": "¿Guardar los ajustes de notificaciones y reiniciar el servicio?",
    "js.frigate.ro_frage": "¿Cambiar a SOLO LECTURA? suslik dejará de escribir en Frigate.",
    "js.frigate.rw_frage": "¿Activar la ESCRITURA en Frigate (sub_labels + sincronización de referencias)?",
    "js.restore.frage": "¿Restaurar la configuración desde \"{name}\"? Esto sobrescribe los ajustes actuales y reinicia el servicio.",
    "js.vollrestore.frage": "¿Restaurar la copia de seguridad COMPLETA \"{name}\"? Esto sustituye los ajustes, las referencias y todo el material aprendido, y luego reinicia el servicio.",
    "js.vollrestore.laeuft": "subiendo + restaurando … (los archivos grandes tardan)",
    "js.enroll.fehler": "Error: {msg}",
    "js.enroll.person_fehlt": "Elige una persona o introduce una nueva.",
    "js.upload.fehlt": "Elige una persona (desplegable o nueva) y un archivo.",
    "js.upload.trotzdem": "{msg}\n\n¿Añadir de todos modos?",
    "js.anlernen.frage": "¿Añadir el grupo como \"{person}\" (las mejores imágenes pasan a ser referencias)?",
    "js.anlernen.name_frage": "Nombre de la nueva persona:",
    "js.anlernen.person_fehlt": "Elige una persona existente.",
    "js.auswahl.gesicht_fehlt": "Marca al menos un rostro.",
    "js.auswahl.bild_fehlt": "Selecciona al menos una imagen.",
    "js.vorschlag.keine": "No hay rostros recomendados.",
    "js.vorschlag.alle_frage": "¿Añadir los {n} rostros recomendados a {person}? Pasan a ser referencias de inmediato.",
    "js.vorschlag.frage": "¿Añadir {n} rostro(s) a {person}?",
    "js.sync.frage": "¿Sincronizar: {richtung}?",
    "js.sync.modell_laedt": "cargando el modelo …",
    "js.sync.fortschritt": "{done}/{total} rostros ({current}) {pct}%",
    "js.sync.fertig": "hecho: {ok} ok, {gate} omitidos — recargando …",
    "js.sync.fehler": "la sincronización falló: {grund}",
    "js.syncauswahl.knopf": "Transferir {n} seleccionadas a Frigate",
    "js.syncauswahl.nichts": "Nada seleccionado",
    "js.syncauswahl.nichts_klein": "nada seleccionado",
    "js.syncauswahl.skip": "omitir",
    "js.syncauswahl.restore": "restaurar",
    "js.syncauswahl.wieder": "ofrecer de nuevo",
    "js.syncauswahl.zurueck_laeuft": "devolviéndola …",
    "js.syncauswahl.frage": "¿Enviar {n} imagen(es) de referencia a Frigate?",
    "js.syncauswahl.fehl_knopf": "la transferencia falló",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct}%",
    "js.syncauswahl.fertig": "hecho: {ok} subidas, {gate} no aceptadas — recargando …",
    "js.syncauswahl.fehler": "la transferencia falló: {grund}",
    "js.vorpruef.haengt": "la comprobación previa parece atascada — recarga la página para reintentar",
    "js.vorpruef.laeuft": "comprobando imágenes … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "la comprobación previa falló: {grund}",
    "js.vorpruef.fertig": "comprobación previa hecha — recargando …",
    "js.import.fortschritt": "descargando {done}/{total} ({current}) {pct}%",
    "js.import.fertig_wiz": "✓ {n} importados — calculando las características en el acelerador …",
    "js.import.knopf_fertig": "Importado ✓",
    "js.import.fehler": "la importación falló: {grund}",
    "js.import.knopf": "Importar rostros",
    "js.import.knopf_ges": "Importar rostros desde Frigate",
    "js.import.fertig_ges": "✓ {n} importados — calculando características, la página se recarga …",
    "js.ref.frage": "¿Quitar la imagen de referencia de {person}?",
    "js.ref.batch_frage": "¿Eliminar {n} imagen(es)?",
    "js.dienst.nicht_erreichbar": "no se puede contactar con el servicio — inténtalo de nuevo en un momento.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage": "¿Ignorar como extraño conocido? Ya no disparará avisos. (Puedes volver a activarlo cuando quieras, más abajo en \"known visitors\".)",
    "js.unb.ziel_fehlt": "Elige una identidad de destino.",
    "js.unb.merge_frage": "¿Fusionar?",
    "js.unb.name_fehlt": "Introduce un nombre (persona nueva o existente).",
    "js.unb.benennen_frage": "¿Asignar a \"{person}\"? Las mejores imágenes pasan a ser referencias.",
    "js.person.loesch_frage": "¿Eliminar TODAS las referencias y el nombre \"{person}\"?\nLas imágenes pasan a la papelera (recuperables).\n\nEscribe el nombre para confirmar:",
    "js.person.name_falsch": "El nombre no coincide — no se ha eliminado nada.",
    "js.areas.fehl": "no se pudo guardar — ¿está accesible el servicio?",
    "js.areas.name_fehlt": "Introduce primero un nombre de área.",
    "js.areas.existiert": "Esta área ya existe.",
    # js.areas.entfernen_frage: "Default" ist zugleich Kennung der
    # Standard-Area (Anzeige==Kennung §8.2) — bleibt in jeder Sprache.
    "js.areas.entfernen_frage": "¿Quitar el área \"{name}\"? Sus cámaras vuelven a Default — nada más cambia.",
    "js.personlauf.abbruch_frage": "¿Abortar este aprendizaje de persona? Las imágenes extraídas se conservan.",
    "js.personlauf.verwerfen_frage": "¿Descartar por completo la ejecución {lid}? Todas sus imágenes se eliminan; una nueva ejecución puede volver a extraerlas en cualquier momento.",
    "js.vision.nicht_erreichbar": "no se pudo contactar con el servicio — no se guardó nada",
    "js.vision.gespeichert": "guardado — el reconocimiento usa esta conexión a partir de ahora",
    "js.vision.gespeichert_neustart": "guardado — el servicio se reinicia en un momento",
    "js.vision.gespeichert_reload": "guardado — el servicio se está reiniciando, la página se recarga en un momento",
    "js.vision.treffer": "{n}/2 correctas",
    "js.vision.tokens": "{ist} tokens frente a {soll}",
    "js.vision.dirty_titel": "No has guardado esta conexión",
    # js.vision.dirty_text: "Save" ist der (noch englische) Knopf der
    # Vision-Seite — bleibt woertlich, bis die Seite selbst einzieht.
    "js.vision.dirty_text": "La prueba usaría los valores que acabas de escribir. El reconocimiento sigue usando la conexión GUARDADA hasta que pulses Save — una prueba verde por sí sola no cambia nada en los veredictos.",
    "js.vision.dirty_save": "Guardar primero y luego probar",
    "js.vision.dirty_test": "Probar sin guardar",
    "js.vision.stufe1": "accesibilidad y modelo",
    "js.vision.stufe2": "cuadrículas de formas con elección forzada",
    "js.vision.stufe3": "recuento de tokens",
    "js.vision.stufe_laeuft": "paso {nr}/3 — {name} … (un modelo local en CPU puede tardar minutos)",
    "js.vision.test_fehl": "la prueba no se pudo ejecutar",
    "js.vision.stufe_stop": "detenido en el paso {nr} — mira el registro de abajo",
    "js.vision.fertig": "hecho — {ampel}",
    "js.vision.stufe_fehl": "el paso {nr} no se pudo ejecutar",
    "js.vision.neustart_warte": "el servicio no responde ahora mismo — la página se recarga en un momento",
    "js.vision.prompt_frage": "¿Restablecer la pregunta al texto por defecto?",
    "js.vision.prompt_zurueck": "texto por defecto restablecido — pulsa Save para guardarlo",
    "js.vision.kachel_frage": "Hay cambios sin guardar. Cambiar de proveedor los descarta. ¿Continuar?",
    "js.vision.pick": "— elige uno —",
    "js.vision.untested": "sin probar aquí",
    "js.vision.neu_pruefen": "la conexión cambió — compruébala de nuevo para ver qué modelos tiene",
    "js.vision.key_laeuft": "preguntando al proveedor qué modelos puedes usar …",
    "js.vision.key_fehl": "la comprobación falló",
    "js.vision.key_fehl2": "la comprobación no se pudo ejecutar",
    "js.rt.start": "iniciando la ejecución de visión …",
    "js.rt.fehl": "no se pudo iniciar la ejecución",
    "js.rt.nach_fehl": "no se pudo iniciar",
    "js.vw.geliehen": "de la fila {reihe}",
    "js.vw.vergessen_frage": "¿Olvidar las imágenes rechazadas para esta galería? Podrán proponerse de nuevo.",
    "js.vw.leer_frage": "{n} celda(s) no se pudieron rellenar. ¿Aprobar la galería de todos modos?",
    "js.vw.kopiert": "copiando las imágenes a la galería …",
    # js.live.phase_*: Anzeige-Woerter zu den Status-KENNUNGEN des
    # Live-Polls (Status-replace-Mapping, §8-Nachtrag).
    "js.live.phase_verbinden": "Conectando",
    "js.live.phase_messen": "Midiendo",
    "js.live.phase_auswerten": "Evaluando",
    "js.live.phase_abbruch": "Abortando",
    "js.live.rest": " — quedan {n} s",
    "js.live.auftrag_zeile": "{art} en {kamera}: {phase}{rest}{pausiert}",
    "js.live.messung": "Medición de carga",
    "js.live.quelltest": "Prueba de fuente",
    "js.live.pausiert": " — vigilancias en pausa por la medición ({liste})",
    "js.live.job_laeuft": "prueba de fuente en curso (proceso auxiliar, hasta ~2 minutos) …",
    "js.live.job_ok": "prueba de fuente hecha: {text}",
    "js.live.job_fehl": "prueba de fuente FALLIDA: {text}",
    "js.live.messung_fehl": "la medición de carga falló: {grund}",
    "js.live.test_fehl": "la prueba de fuente falló: {grund}",
    # ---- auftritte (Stufe 2, Tranche A) ----
    # Projektroot-Route /heute-Personensicht + /pass/<eid> (auftritte.py);
    # Stufe-2-Grenzen s. en.py-Abschnittskommentar. Muttersprachler-QS der
    # Tranche durchlaufen 19.08.2026.
    "auftritte.unbek.zaehlung":
        "+{n} sin identificar (suelen ser las mismas personas)",
    "auftritte.unbek.name": "Persona desconocida {nummer}",
    "auftritte.unbek.ohne_treffer.eins":
        "{n} evento con un rostro sin identificar",
    "auftritte.unbek.ohne_treffer.viele":
        "{n} eventos con rostro sin identificar",
    "auftritte.nav.zurueck_heute": "&#8592; Hoy",
    "auftritte.unbek.titel": "Persona desconocida",
    "auftritte.unbek.leer_link": "A este enlace le falta el recorrido.",
    "auftritte.unbek.leer_weg":
        "Este recorrido ya no está en la vista del día.",
    "auftritte.unbek.leer_weg_hinweis":
        "Puede que el día se haya reagrupado — ábrelo de nuevo desde Hoy.",
    "auftritte.unbek.leer_pool": "No hay rostros recogidos de este recorrido.",
    "auftritte.unbek.leer_pool_hinweis":
        "Puede que la limpieza los haya retirado mientras tanto.",
    "auftritte.knopf.video": "vídeo",
    "auftritte.karte.faces.eins": "{n} rostro",
    "auftritte.karte.faces.viele": "{n} rostros",
    "auftritte.karte.kameras.eins": "{n} cámara",
    "auftritte.karte.kameras.viele": "{n} cámaras",
    "auftritte.unbek.mehr_im_lauf": "+{n} más en este recorrido",
    "auftritte.unbek.ein_lauf": "un recorrido",
    "auftritte.zuweisen.titel": "¿Quién es?",
    "auftritte.zuweisen.satz":
        "Estos son los rostros de ESTE recorrido. Marca los que de verdad "
        "son de la persona &mdash; lo que no sirve se queda fuera. Ponles "
        "un nombre (nuevo o existente) y el sistema los aprende; si no haces "
        "nada, siguen como desconocidos.",
    "auftritte.zuweisen.knopf_alle": "Seleccionar todos",
    "auftritte.zuweisen.knopf_keine": "Ninguno",
    "auftritte.zuweisen.attr_person": "persona (nueva o existente)",
    "auftritte.zuweisen.knopf_zuweisen": "Añadir los rostros seleccionados",
    "auftritte.zuweisen.js_keine": "marca al menos un rostro",
    "auftritte.zuweisen.js_name": "escribe un nombre de persona",
    "auftritte.zuweisen.js_lernt": "aprendiendo…",
    "auftritte.zuweisen.js_fehler": "error",
    "auftritte.unbek.titel_lauf": "Persona desconocida {nummer} — recorrido",
    "auftritte.leer_person": "Persona desconocida.",
    "auftritte.leer_person_hinweis": "Elige una persona en la página Hoy.",
    "auftritte.titel": "Apariciones",
    "auftritte.nav.attr_tag": "volver al día",
    "auftritte.nav.attr_vortag": "día anterior",
    "auftritte.kopf.passzahl.eins": "{n} recorrido",
    "auftritte.kopf.passzahl.viele": "{n} recorridos",
    "auftritte.nav.attr_kein_morgen": "no hay días futuros",
    "auftritte.nav.attr_folgetag": "día siguiente",
    "auftritte.titel_person": "{person} — Apariciones",
    "auftritte.leer_passe":
        "No hay recorridos confirmados de {person} en este día.",
    "auftritte.leer_passe_hinweis":
        "Usa las flechas para moverte por los días.",
    "auftritte.karte.kein_bild": "sin imagen",
    "auftritte.thumb.zusatz_unbestaetigt": " — sin confirmar aquí",
    "auftritte.thumb.zusatz_referenz": " — en las referencias",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} evento sin rostro",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} eventos sin rostro",
    "auftritte.thumb.hinweis_referenz":
        "borde verde = ya en las referencias",
    "auftritte.karte.best_punkt": "se confirmó a las {zeit}",
    "auftritte.karte.best_spanne": "se confirmó {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "en curso",
    "auftritte.karte.pass_nr": "Recorrido {n}",
    "auftritte.karte.events.eins": "{n} evento",
    "auftritte.karte.events.viele": "{n} eventos",
    "auftritte.karte.best_match": "mejor coincidencia {wert}",
    "auftritte.karte.auch_dabei": "también en este recorrido: {namen}",
    "auftritte.pass.titel": "Recorrido",
    "auftritte.pass.leer_event": "No se ha encontrado el evento.",
    "auftritte.pass.leer_event_hinweis":
        "Puede que ya haya salido del registro por antigüedad.",
    "auftritte.pass.leer_gruppe":
        "Este evento no forma parte de un recorrido agrupado.",
    "auftritte.pass.leer_gruppe_hinweis":
        "La agrupación necesita el contexto de la vista del día.",
    "auftritte.nav.zurueck_tag": "&#8592; Día",
    "auftritte.pass.attr_vor": "recorrido anterior del día",
    "auftritte.pass.attr_nach": "recorrido siguiente del día",
    "auftritte.pass.kopf": "Recorrido {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Sin identificar",
    "auftritte.pass.label_gt": "Etiqueta",
    "auftritte.pass.badge_fremd": "extraño confirmado",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log no contiene ninguna línea con el motivo — abre el "
        "evento para ver el registro completo",
    "auftritte.pass.grund_ohne_log":
        "no se conservó analyze.log para este evento — mira el registro "
        "del servicio",
    "auftritte.pass.label_fehler": "Error",
    "auftritte.pass.wer": "Quién",
    "auftritte.pass.titel_zeit": "Recorrido {zeit} — {tag}",
}
