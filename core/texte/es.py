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
    "aehnliche.vorrat.titel": "Nuevo del material de aprendizaje",
    "aehnliche.vorrat.hinweis":
        "Caras de alta calidad recogidas por la pasada de aprendizaje, "
        "evaluadas con la medida de calidad sin referencias y el consenso "
        "del escenario. Se quedan en local y nunca se exportan a Frigate.",
    "aehnliche.vorrat.kachel_zeile": "{wann} · {kamera} · coincidencia {sim} · calidad {norm}",
    "aehnliche.vorrat.auch_anker": "también en un grupo de caras",
    "aehnliche.vorrat.knopf_gewaehlt": "Aplicar la selección a {person}",
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
    "ereignisliste.tabelle.attr_kein_crop":
        "no se ha conservado ningún rostro utilizable para este evento",
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
        "eliminado por ti — las imágenes ya no existen; el grupo solo queda como registro",
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
        "{n} grupo(s) eliminado(s) por ti (imágenes borradas, solo queda el registro)",
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
        "¿Eliminar este grupo? Sus imágenes se borran. No se puede deshacer.",
    "lernanker.liste.frage_verwerfen_benannt":
        "¿Eliminar este grupo? Sus imágenes se borran y el nombre pendiente se descarta. No se puede deshacer.",
    "lernanker.liste.knopf_verwerfen": "Eliminar",
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
    "syncauswahl.bilanz.vorrat": "{n} referencia(s) del material solo en local (basadas en embedding, no transferibles)",
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
        "Vuelve a medir cada imagen de referencia (incl. la calidad facial) y "
        "busca imágenes débiles, casi duplicadas y rostros confundidos. Tarda "
        "unos minutos según el número de imágenes y se ejecuta en segundo plano.",
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
    "qualitaet.galerie.vorrat": "del material",
    "qualitaet.galerie.norm": "calidad {norm}",
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
    "lernwizard.wizard.auswahl_durchsucht": "{k} de estos {n} ya están revisados — con \"omitir los ya revisados\" la ejecución toma eventos más antiguos (la tarjeta muestra dónde acaba).",
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
        "{n} grupo eliminado por ti &middot;",
    "lernwizard.k3.verworfen.viele":
        "{n} grupos eliminados por ti &middot;",
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
        "¿Eliminar este grupo? Sus imágenes se borran y un nombre pendiente se descarta. No se puede deshacer.",
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
    "js.vorrat.frage": "¿Añadir {n} cara(s) del material a {person}? Se convierten en referencias de inmediato (se quedan en local, sin exportar).",
    "js.qs.fortschritt": "comprobando la imagen {i} de {n} …",
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
    "js.unb.besucher_frage": "¿Ignorar como extraño conocido? Ya no generará avisos. (Puedes volver a activarlo cuando quieras, más abajo en \"visitantes conocidos\".)",
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
    # js.vision.dirty_text UND js.vision.prompt_zurueck zitieren
    # vision.save.knopf ("Guardar la conexión") woertlich — Zitat-Folge
    # Tranche C, bei Aenderungen dort beide nachziehen.
    "js.vision.dirty_text": "La prueba usaría los valores que acabas de escribir. El reconocimiento sigue usando la conexión GUARDADA hasta que pulses «Guardar la conexión» — una prueba verde por sí sola no cambia nada en los veredictos.",
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
    "js.vision.prompt_zurueck": "texto por defecto restablecido — pulsa «Guardar la conexión» para guardarlo",
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
    # ---- verifyd-Innenseiten (Stufe 2, Tranche B) ----
    # Inline-Handler in verifyd.py (_banner, Setup-Wizard, Today-Leer-
    # zustaende, /unbekannte, /live_alerts, /video, /event/<id>); Grenzen
    # und Wiederverwendung s. en.py-Abschnittskommentar. Begriffe:
    # begriffe_tabellen.md (ES-Abschnitt).
    "banner.schoner":
        "Frigate no responde — se espacian los intentos y se sondea cada "
        "pocos segundos hasta que se recupere; la interfaz sigue "
        "mostrando los datos locales.",
    "banner.fehler":
        "Frigate inaccesible (último error {zeit}): {fehler} — la "
        "interfaz sigue mostrando los datos locales.",
    "setupwiz.frigate.status_ok":
        "✓ Conectado — {n} cámara(s) encontrada(s)",
    "setupwiz.frigate.status_fehl":
        "✗ No se pudo contactar con Frigate: {fehler}",
    "setupwiz.frigate.status_fehl_keine": "sin cámaras",
    "setupwiz.frigate.status_fehl_hinweis":
        "Corrige la URL (o define FRIGATE_URL en tu .env / "
        "docker-compose) y prueba de nuevo.",
    "setupwiz.frigate.status_leer":
        "Introduce la URL de tu Frigate y prueba la conexión.",
    "setupwiz.frigate.titel": "Conectar con Frigate",
    "setupwiz.frigate.satz":
        "suslik lee tus cámaras directamente de la API de Frigate "
        "(normalmente el puerto 5000). Ninguna cámara está fijada en el "
        "código.",
    "setupwiz.frigate.knopf_test": "Probar la conexión",
    "setupwiz.kameras.titel": "Elegir cámaras y condiciones",
    "setupwiz.kameras.satz":
        "Marca las cámaras que quieres observar; marca una o más zonas "
        "para analizar solo los eventos que hayan entrado en ellas "
        "(p. ej. una persona en el jardín). Ninguna marcada = todos los "
        "eventos.",
    "setupwiz.kameras.satz_ohne":
        "Conecta primero con Frigate — tus cámaras aparecerán aquí.",
    "setupwiz.backend.titel": "Aceleración",
    "setupwiz.backend.verfuegbar": "Disponible en esta máquina:",
    "setupwiz.backend.satz_wahl": "Elige uno — la CPU siempre funciona.",
    "setupwiz.import.titel": "Importar rostros desde Frigate",
    # Zaehler-Split an der <b>-Grenze (§8.10) wie in en.py: vor/mitte/nach
    # rahmen die hervorgehobenen Zahlen, Rand-Leerzeichen gehoeren zum Wert.
    "setupwiz.import.zahl_vor": "Frigate ya tiene ",
    "setupwiz.import.zahl_mitte": " imagen(es) de referencia de ",
    "setupwiz.import.zahl_nach": " persona(s).",
    "setupwiz.import.satz":
        "Impórtalas para que suslik reconozca a todos desde el "
        "principio. Las imágenes se descargan rápidamente y después "
        "suslik calcula sus propias características faciales en tu "
        "acelerador (GPU/NPU).",
    "setupwiz.import.knopf": "Importar {n} rostros desde Frigate",
    "setupwiz.import.satz_leer":
        "Aún no hay rostros en Frigate. Nota: suslik necesita al menos "
        "un rostro de referencia antes de poder reconocer a alguien — "
        "importa aquí desde Frigate o sube fotos más adelante en la "
        "página Conocidos.",
    "setupwiz.import.satz_ohne":
        "Conecta primero con Frigate — después podrás importar aquí sus "
        "rostros conocidos.",
    "setupwiz.fertig.knopf": "Guardar e iniciar suslik",
    "setupwiz.fertig.satz":
        "Guarda tu selección y reinicia el servicio una sola vez.",
    "setupwiz.restore.titel": "¿Ya tienes una configuración?",
    # Zitiert system.titel + system.backup.titel WOERTLICH (Zitat-Folge
    # Tranche C) — bei Aenderungen dort hier nachziehen.
    "setupwiz.restore.satz":
        "Si ya has exportado una configuración de suslik (Sistema → "
        "Copia de seguridad de la configuración), cárgala aquí para "
        "restaurar todos los ajustes y saltarte el asistente.",
    "setupwiz.restore.knopf": "Cargar archivo de configuración…",
    "setupwiz.write.titel": "¿Escribir en Frigate?",
    "setupwiz.write.satz":
        "suslik puede devolver sus veredictos a Frigate (sub_labels) y "
        "reflejar las referencias, para que ambos funcionen en paralelo. "
        "Solo lectura es la opción predeterminada y segura.",
    "setupwiz.write.opt_ro":
        "Solo lectura (recomendado) — suslik nunca escribe en Frigate",
    "setupwiz.write.opt_rw":
        "Escribir en Frigate (funcionamiento en paralelo)",
    "setupwiz.willkommen.titel": "Te damos la bienvenida a suslik",
    "setupwiz.willkommen.satz":
        "Una puesta en marcha rápida y guiada — o carga una "
        "configuración existente para saltártela. Todo esto se puede "
        "cambiar después en las páginas normales.",
    # leer.*: passe_area/band sind je Zweig VOLLE Saetze (B9-Umbau, en.py).
    "leer.passe_area_heute":
        "Hoy todavía ningún recorrido ha pasado por el área {area}.",
    "leer.passe_area_tag":
        "En este día ningún recorrido pasó por el área {area}.",
    # Der Chip "All" ist Anzeige==Kennung (§8.2) und bleibt woertlich.
    "leer.passe_area_hinweis":
        "El filtro \"All\" de arriba muestra toda la propiedad.",
    "leer.passe_heute": "Hoy todavía no hay recorridos con rostro.",
    "leer.passe_heute_hinweis":
        "En cuanto alguien cruce la propiedad, el recorrido aparecerá "
        "aquí.",
    "leer.tag": "Nada con rostro en este día.",
    "leer.tag_hinweis":
        "Usa las flechas para ver otro día, o abre Eventos para la "
        "lista completa.",
    "leer.frigate": "Aún no hay ningún Frigate conectado.",
    "leer.frigate_hinweis":
        "Configura la URL de tu Frigate en el asistente inicial "
        "(página Sistema) — después los recorridos aparecerán aquí "
        "automáticamente.",
    "leer.refs":
        "Conectado — pero aún no hay rostros de referencia, así que no "
        "se puede reconocer a nadie.",
    "leer.refs_hinweis":
        "Importa rostros desde Frigate o sube fotos — ambas cosas en la "
        "página Conocidos. Después suslik sigue aprendiendo por su "
        "cuenta a partir de las cámaras.",
    "leer.band_heute": "Hoy todavía no hay nada con rostro.",
    "leer.band_tag": "Nada con rostro en este día.",
    "leer.band_hinweis":
        "Las personas aparecen aquí en cuanto se analiza un recorrido.",
    "leer.person_unbekannt": "Persona desconocida.",
    "leer.kamera_unbekannt": "Cámara desconocida.",
    "leer.kamera_unbekannt_hinweis":
        "Las tarjetas proceden únicamente de la lista de cámaras de "
        "Frigate y de las vigilancias guardadas.",
    "unbekannte.name": "Persona desconocida {nummer}",
    "unbekannte.badge_eine": "claramente una sola persona",
    "unbekannte.badge_aehnlich": "similitud {wert}",
    "unbekannte.badge_einmal": "una sola aparición",
    "unbekannte.meta_zeit": " apariciones · {zeit}",
    "unbekannte.knopf_reaktivieren": "reactivar",
    "unbekannte.attr_name": "Nombre (nuevo o existente)",
    "unbekannte.knopf_zuweisen": "Asignar persona",
    "unbekannte.knopf_ignorieren": "Ignorar",
    "unbekannte.opt_merge": "fusionar con…",
    "unbekannte.knopf_ok": "OK",
    "unbekannte.badge_gleiche": "¿misma persona?",
    "unbekannte.knopf_merge": "Fusionar",
    "unbekannte.knopf_verschieden": "Personas distintas",
    "unbekannte.titel": "Desconocidos",
    "unbekannte.kopf_satz":
        "Rostros sin coincidencia conocida, agrupados en identidades "
        "recurrentes.",
    # Kopf-Erklaerung an den <b>-Grenzen gesplittet; die Fett-Teile sind
    # die knopf_*-Schluessel selbst (eine Quelle, kein Drift).
    "unbekannte.kopf_satz_zuweisen":
        " vincula una tarjeta con una persona (nueva o existente, "
        "escribe el nombre),",
    "unbekannte.kopf_satz_ignorieren":
        " silencia a un extraño conocido (sin aviso).",
    "unbekannte.kopf_satz_auto":
        "Los rostros nuevos se recogen automáticamente tras cada "
        "recorrido.",
    "unbekannte.knopf_reorg": "Reorganizar ahora",
    "unbekannte.hinweis_reorg":
        "vuelve a comprobar los rostros recogidos y reconstruye los "
        "grupos — la recogida en sí se ejecuta automáticamente (1-2 min)",
    "unbekannte.h_wieder": "Recurrentes",
    "unbekannte.h_einzeln":
        "{n} apariciones sueltas (una sola vez hasta ahora)",
    "unbekannte.h_besucher": "{n} visitantes conocidos (silenciados)",
    "unbekannte.h_objekte":
        "{n} objetos estáticos (detectados automáticamente — no son "
        "personas)",
    "unbekannte.satz_objekte":
        "Grupos cuyas imágenes son casi idénticas entre sí y no se "
        "parecen a ninguna persona — típicamente un paso de rueda, el "
        "pavimento o un patrón de luz que el detector confunde una y "
        "otra vez con un rostro. Están congelados: los hallazgos nuevos "
        "nunca se añaden aquí (forman grupos nuevos y visibles, y la "
        "misma regla los vuelve a comprobar) — los grupos siguen en la "
        "lista para que nada quede oculto.",
    "unbekannte.leer": "Aún no se han recogido rostros desconocidos.",
    "unbekannte.leer_hinweis":
        "Las identidades aparecerán aquí tras el próximo visitante "
        "desconocido.",
    "livealerts.link_video": "&#9654; vídeo {n}",
    "livealerts.person_unbekannt": "sin identificar",
    "livealerts.trigger.eins": "{n} activación",
    "livealerts.trigger.viele": "{n} activaciones",
    "livealerts.kanal_keiner": "no enviado (sin canal)",
    "livealerts.keine_bilder": "sin imágenes guardadas",
    "livealerts.titel": "Avisos de la vigilancia en directo",
    "livealerts.kopf.auftritte.eins": "{n} aparición",
    "livealerts.kopf.auftritte.viele": "{n} apariciones",
    "livealerts.kopf.satz":
        " el {tag} — comprobación rápida, preliminar; el veredicto "
        "confirmado procede del análisis normal.",
    "livealerts.kopf.satz_alt":
        "Las entradas anteriores a 0.1.0.190 no tienen imagen ni nombre "
        "registrados.",
    "livealerts.leer": "No hay avisos en directo ese día.",
    "video.fehl":
        "&#9888; La transcodificación ha fallado — mira el registro del "
        "servicio (/log).",
    "video.fehl_hinweis":
        "Recarga esta página para reintentar, o abre el clip original:",
    "video.warte": "Preparando el vídeo para el navegador (H.264)&nbsp;…",
    "video.warte_satz":
        "Esta página se actualiza sola. La copia se genera una sola vez "
        "y luego queda en caché.",
    "event.ours_zeile.eins": "{person} — {stufe} (aparece en {n} ventana)",
    "event.ours_zeile.viele":
        "{person} — {stufe} (aparece en {n} ventanas)",
    "event.ours_keiner": "sin coincidencia con nadie",
    "event.ours_rest.eins": " · {n} persona más: sin coincidencia",
    "event.ours_rest.viele": " · {n} personas más: sin coincidencia",
    "event.grenze":
        "por debajo de esta línea: coincidencias débiles (mejor "
        "puntuación &lt; {wert}) — el nombre es una suposición, podría "
        "tratarse de otra persona",
    "event.gruppe_ohne": "Sin atribuir",
    "event.badge_unsicher": "sin certeza",
    "event.leer_crops":
        "No hay recortes de rostro guardados para este evento.",
    "event.knopf_video": "&#9654; Vídeo",
    "event.knopf_log": "Registro del análisis",
    "event.attr_unvollstaendig":
        "clip incompleto — leídos {gelesen}/{soll} fotogramas; juzgado a "
        "partir de la parte legible",
    "event.badge_unvollstaendig": "⚠ clip incompleto",
    "event.pass_zurueck": "&#8592; anterior",
    "event.pass_weiter": "siguiente &#8594;",
    "event.pass_teil": "Parte de un recorrido",
    "event.pass_events.eins": "{n} evento",
    "event.pass_events.viele": "{n} eventos",
    "event.pass_knopf": "ver el recorrido",
    "event.label_grund": "Motivo del error",
    "event.grund_ohne_zeile":
        "analyze.log no contiene ninguna línea con el motivo — usa el "
        "botón de registro de abajo",
    "event.grund_ohne_log":
        "no se conservó analyze.log para este evento — mira el registro "
        "del servicio (página Sistema)",
    "event.zurueck": "← Hoy",
    "event.label_korrektur": "Corrígelo si está mal",
    "event.label_wer": "¿Quién era?",
    "event.h_bilder": "Imágenes",
    # ---- Routen-Seiten (Stufe 2, Tranche C) ----
    # routes/system.py, routes/vision.py, routes/visiontest.py,
    # routes/visionwizard.py, routes/personwizard.py, webui/bausteine.py;
    # Grenzen und Wiederverwendung s. en.py-Abschnittskommentar. Begriffe:
    # begriffe_tabellen.md (ES-Abschnitt). Zitat-Folgen eingearbeitet:
    # setupwiz.restore.satz zitiert system.titel + system.backup.titel,
    # js.vision.dirty_text und js.vision.prompt_zurueck zitieren
    # vision.save.knopf.
    # --- routes/system.py ---
    "system.ampel.service": "Servicio",
    "system.ampel.service_info": "procesados (en total): {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — autocomprobación OK",
    "system.ampel.backend_fail":
        "{backend} — {n} FALLO(s) de autocomprobación, mira el registro "
        "del servicio",
    "system.ampel.analyse": "Análisis",
    "system.ampel.analyse_dauer": "última duración {s} s",
    "system.ampel.analyse_nie": "aún sin análisis",
    "system.ampel.retry": "Cola de reintentos",
    "system.ampel.retry_info":
        "{offen} abiertos / {aufgegeben} abandonados (ventana {tage} d)",
    "system.ampel.frigate_unkonfiguriert":
        "aún sin configurar — define la URL en el asistente inicial",
    "system.ampel.frigate_ok": "accesible",
    # {zeit} kommt vorformatiert (%H:%M) aus der Route (B19-Stufe).
    "system.ampel.frigate_fehler": "último error {zeit}",
    # {s} vorformatiert (:.0f) — Formatspezifika nie in Werte (§8.8).
    "system.ampel.mqtt_hb": "heartbeat hace {s} s",
    "system.ampel.mqtt_kein_hb": "aún sin heartbeat",
    "system.ampel.mqtt_pub_aus": "configurado, publicación desactivada",
    "system.ampel.mqtt_pub_kaputt":
        "configurado, el publicador no se ha iniciado — mira el registro "
        "del servicio",
    "system.ampel.mqtt_unkonfiguriert": "sin configurar",
    "system.ampel.disk": "Disco",
    "system.ampel.disk_info2": "{gb} GB libres · caché de clips {cache} GB de {max} GB",
    "system.disk.titel": "Espacio en disco",
    "system.disk.satz": "Los clips son una caché: se guardan {tage} días, con un tope de {max} GB, y se recortan en cuanto quedan menos de {min} GB libres (se comprueba tras cada evento y una vez al día con una vigilancia del disco que pasa a cada 10 minutos mientras queda poco espacio).",
    "system.disk.knopf": "Limpiar ahora",
    "system.disk.warnung": "Solo quedan {gb} GB libres y la caché de clips ya está vacía — libera espacio en el volumen de datos; si no, los eventos nuevos no se podrán guardar.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "REVISAR",
    "system.drift.banner":
        "COMPROBACIÓN DE DERIVA EN ROJO tras añadir la última referencia:",
    "system.sync.titel": "Sincronización con Frigate",
    "system.sync.knopf": "Abrir la sincronización con Frigate",
    "system.sync.satz":
        "La página de sincronización compara los dos bancos de rostros "
        "persona por persona, somete cada candidata a la misma "
        "comprobación previa que hace Frigate, envía solo lo que marques "
        "e importa lo que solo tiene Frigate.",
    "system.sync.fehlt":
        "aún no disponible — necesita un Frigate accesible y al menos un "
        "rostro de referencia",
    "system.qc.titel": "Informe de calidad",
    "system.qc.stand": "(a fecha de {stand}, {tage} días)",
    "system.qc.kopf_gesicht": "con rostro",
    "system.qc.kopf_bestaetigt": "confirmados",
    "system.qc.kopf_quote": "tasa en la ventana",
    # WIRD ZITIERT: setupwiz.restore.satz nennt diesen Titel woertlich.
    "system.backup.titel": "Copia de seguridad de la configuración",
    "system.backup.satz":
        "Descarga los ajustes guardados en /data/config como un único "
        "archivo JSON, o restáuralos desde un archivo así. Alcance "
        "honesto: hoy eso es la HOJA DE CÁMARAS (incl. sus valores "
        "guardados); los umbrales/canales definidos solo en verifyd.yaml "
        "o por variables de entorno NO están en este archivo. Personas "
        "aprendidas/referencias: usa la copia completa de abajo.",
    "system.backup.knopf_download": "Descargar la configuración",
    "system.backup.knopf_restore": "Restaurar desde archivo…",
    "system.backup.careful": "Cuidado:",
    # {hinweis} = seit Tranche D der Schluessel system.backup.hinweis
    # (Konstante VISION_EXPORT_HINWEIS ist auf die Sprachschicht umgezogen).
    "system.backup.careful_config":
        "este archivo {hinweis} (canales de notificación y detección de "
        "visión), para que una restauración en otra máquina funcione de "
        "verdad.",
    "system.backup.restore_satz":
        "Restaurar sobrescribe los ajustes actuales (los anteriores se "
        "conservan como .bak) y reinicia el servicio.",
    "system.voll.titel": "Copia de seguridad completa",
    "system.voll.satz":
        "Un único archivo portátil con todo lo que has enseñado a esta "
        "instalación: los ajustes, el banco de referencias de rostros, "
        "los resultados del aprendizaje, todo el material del "
        "reconocimiento de personas (imágenes, tus veredictos de "
        "revisión, modelos entrenados) y el registro de eventos. Pensado "
        "para trasladarlo todo a otra máquina. Alcance honesto: la caché "
        "de clips de vídeo y los artefactos de análisis por evento NO se "
        "incluyen — se reconstruyen con el tiempo.",
    "system.voll.knopf_download": "Descargar la copia completa",
    "system.voll.knopf_restore": "Restaurar la copia completa…",
    "system.voll.careful": "este archivo {hinweis}.",
    "system.voll.restore_satz":
        "Restaurar sustituye esas partes (cada versión anterior se "
        "conserva una vez como *.pre-restore-*) y reinicia el servicio. "
        "Subir unos cientos de MB puede tardar — deja la página abierta.",
    "system.live.titel": "Vigilancias en directo",
    "system.live.alerts": "Avisos enviados hoy: {kanaele}",
    "system.live.stoerungen": "Avisos de incidencia hoy: {n}",
    "system.live.knopf": "Abrir Vigilancia en directo",
    "system.live.quelle":
        "Contado a partir del registro de mensajes del propio motor — "
        "solo mensajes que un canal aceptó de verdad. Los avisos de la "
        "vigilancia en directo son independientes de los contadores de "
        "avisos del análisis de eventos de la página Hoy.",
    "system.write.titel": "Escritura en Frigate",
    "system.write.satz":
        "¿Escribe suslik de vuelta en Frigate o solo lee? Solo lectura "
        "es la opción predeterminada y segura; activa la escritura solo "
        "para el funcionamiento en paralelo (Frigate-Face + suslik).",
    "system.write.aktuell": "Actual:",
    "system.write.zustand_ro":
        "SOLO LECTURA — suslik no escribe en Frigate",
    "system.write.zustand_rw": "ESCRITURA en Frigate — sub_labels",
    "system.write.zustand_rw_sync": " + sincronización de referencias",
    "system.write.knopf_rw": "Activar la escritura",
    "system.write.knopf_ro": "Solo lectura",
    # WIRD ZITIERT: setupwiz.restore.satz nennt die Seite woertlich;
    # wortgleich mit nav.system (Linktext==Seitentitel).
    "system.titel": "Sistema",
    "system.tools.titel": "Herramientas",
    "system.docs.titel": "Documentación",
    "system.docs.link": "Documentación en GitHub",
    # --- routes/vision.py ---
    "vision.zeit.nie": "nunca",
    "vision.titel": "Detección de visión",
    "vision.kopf.dirty": "sin guardar",
    "vision.hinweis.titel": "Qué necesitas para esto",
    "vision.schalter.knopf_aus": "Desactivar",
    "vision.schalter.knopf_an": "Activar",
    "vision.schalter.fehlt": "Aún pendiente:",
    "vision.schalter.titel_an": "La detección de visión está activada",
    "vision.schalter.titel_aus": "La detección de visión está desactivada",
    "vision.schalter.aus_satz":
        "Mientras está desactivada no se envía nada a ninguna parte y "
        "ninguna imagen sale de esta máquina.",
    "vision.frage.titel": "Cómo se pregunta una comparación",
    "vision.frage.doppel_titel":
        "Preguntar cada par dos veces, con las galerías intercambiadas",
    "vision.frage.doppel_satz":
        "Es la comprobación de posición. A en la primera ronda y B en la "
        "ronda intercambiada señalan la MISMA galería, así que una "
        "contradicción delata a un modelo que simplemente prefiere lo "
        "que llega primero. Medido aquí: todas las respuestas erróneas "
        "de todas nuestras series de prueba fueron una «A», nunca una "
        "«B». Desactivarlo reduce las peticiones a la mitad &mdash; y "
        "una comparación descansa entonces en una sola respuesta, sin "
        "nada con que contrastarla.",
    "vision.meld.titel": "Mensajes adicionales",
    "vision.meld.satz":
        "Los dos están desactivados hasta que los actives, y ninguno "
        "cambia los avisos existentes: la visión no puede generar uno, "
        "cancelar uno ni imponerse a las vías del rostro y del cuerpo.",
    "vision.meld.judged_titel":
        "Avísame cuando se haya evaluado un recorrido",
    "vision.meld.judged_satz":
        "Una nota breve por tus canales habituales en cuanto está el "
        "veredicto &mdash; con el recuento real de votos. Llega cuando "
        "el recorrido ya ha terminado; con un modelo local pueden ser "
        "minutos más tarde. Información, sin urgencia.",
    "vision.meld.alarm_titel":
        "Avísame cuando la visión contradiga al reconocimiento corporal",
    "vision.meld.alarm_satz":
        "Solo salta cuando de verdad hubo una ejecución, el modelo "
        "respondió y aun así no confirmó a nadie. Guarda silencio cuando "
        "simplemente no había material suficiente &mdash; eso sería "
        "ruido. Reconocer a las personas que le has enseñado es el lado "
        "fuerte de esta vía, así que una no confirmación significa algo; "
        "rechazar a los extraños es su lado débil, así que la visión "
        "nunca vota en esa dirección.",
    "vision.kachel.was_key": "introduces una clave de API",
    "vision.kachel.was_host": "introduces host y puerto",
    "vision.kachel.was_url": "introduces una URL y una clave opcional",
    "vision.kachel.titel": "Dónde se ejecuta el modelo",
    "vision.kachel.satz":
        "Elige un proveedor. Para los tres con nombre, la dirección "
        "oficial de la API ya viene incorporada &mdash; tú solo "
        "introduces tu clave. No se envía nada a ninguna parte hasta que "
        "pulses tú un botón.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; guardada &mdash; déjala en blanco para "
        "conservarla",
    "vision.verb.key_pflicht_ph": "pega aquí tu clave",
    "vision.verb.key_frei_ph": "solo si tu servidor la pide",
    "vision.verb.host": "Host",
    "vision.verb.host_ph": "el nombre o la dirección de esa máquina",
    "vision.verb.port": "Puerto",
    "vision.verb.host_satz":
        "Solo la máquina &mdash; suslik añade el resto de la dirección "
        "por su cuenta. El puerto de ejemplo es el que llama.cpp usa por "
        "defecto; pon el que escuche el tuyo.",
    "vision.verb.endpunkt": "URL del endpoint",
    "vision.verb.endpunkt_satz":
        "Es un ejemplo de un endpoint compatible con OpenAI &mdash; "
        "sustitúyelo por el tuyo si usas otro proveedor.",
    "vision.verb.betriebsart": "Este endpoint está",
    "vision.verb.betriebsart_extern": "en internet",
    "vision.verb.betriebsart_lokal": "en mi propia red",
    "vision.verb.adresse": "Dirección de la API",
    "vision.verb.adresse_satz":
        "Incorporada &mdash; aquí no hay nada que se pueda escribir mal.",
    "vision.verb.key": "Clave de API",
    "vision.verb.key_frei_satz":
        "Opcional aquí &mdash; la mayoría de los servidores locales no "
        "piden ninguna. Pulsa el botón de todos modos: también obtiene "
        "la lista de modelos que tiene tu servidor.",
    "vision.verb.titel": "Conexión",
    "vision.modell.titel": "Modelo",
    "vision.modell.verweigert": "el endpoint rechazó la conexión",
    # {zeit} vorformatiert aus _zeit() — das Format bleibt in der Route (B19).
    "vision.modell.geprueft": "Comprobado {zeit} contra",
    "vision.modell.opt_wahl": "&mdash; elige uno &mdash;",
    "vision.modell.ungetestet": "sin probar aquí",
    "vision.modell.opt_verschollen":
        " — guardado antes, el endpoint ya no lo lista",
    "vision.modell.wahl_satz":
        "Elige uno de la lista &mdash; la nota junto a cada nombre es "
        "nuestra, los nombres son del endpoint.",
    "vision.modell.verschollen_satz":
        "Este modelo está guardado y sigue en uso, pero el endpoint no "
        "lo ha listado esta vez. Comprueba el nombre o elige uno de la "
        "lista.",
    "vision.modell.fremde_plattform": "medido en otra plataforma",
    "vision.modell.kein_rohergebnis":
        "sin resultado en bruto archivado para este",
    "vision.modell.gemessen": "medido {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "No medido aquí &mdash; no es un veredicto, solo honestidad. "
        "Ejecuta la prueba de conexión de abajo antes de confiar en él.",
    "vision.modell.manuell": "Id del modelo a mano",
    "vision.modell.manuell_ph": "id exacto del modelo",
    "vision.modell.manuell_knopf": "Comprobar este id",
    "vision.modell.manuell_satz":
        "Para endpoints que no listan todo: el id se comprueba primero "
        "con una petición de texto mínima; no se puede guardar nada sin "
        "comprobar.",
    "vision.prompt.standard_satz":
        "Esta es la formulación por defecto, la que se midió. Mientras "
        "la dejes exactamente así, los veredictos no se marcan como "
        "personalizados.",
    "vision.prompt.titel": "La pregunta que hace suslik",
    "vision.prompt.satz":
        "Puedes cambiar la formulación. El último párrafo es fijo: es la "
        "instrucción de una sola palabra de la que depende el analizador "
        "de respuestas, y es lo que se midió.",
    "vision.prompt.knopf_zurueck": "Restablecer el texto por defecto",
    "vision.zahlen.think": "Desactivar el razonamiento del modelo",
    "vision.zahlen.think_satz":
        "Activado por defecto desde 0.1.0.211: en cuadrículas de "
        "comparación difíciles, un modelo con razonamiento puede hablar "
        "hasta agotar el presupuesto de tokens y la ejecución termina "
        "sin veredicto. Los endpoints estrictos rechazan el parámetro; "
        "suslik repite entonces la petición una vez sin él y lo dice.",
    "vision.zahlen.titel": "Límites",
    "vision.zahlen.max_tokens": "Máximo de tokens por respuesta",
    "vision.zahlen.timeout": "Tiempo límite por petición (s)",
    "vision.zahlen.satz":
        "En una ejecución se midió que 3000 tokens no bastaban &mdash; "
        "la respuesta quedó cortada y contó como sin veredicto, y la "
        "misma pregunta salió bien con 12000. Un modelo local en una "
        "máquina de CPU necesita minutos por petición; uno en línea, "
        "segundos.",
    "vision.cloud.ziel_fallback": "el endpoint que configuras arriba",
    "vision.cloud.titel": "Envío de imágenes a un servicio externo",
    "vision.cloud.satz":
        "Esas imágenes no son solo de las personas que viven aquí: los "
        "casos dudosos son sobre todo extraños &mdash; visitas, "
        "repartidores, vecinos, transeúntes. La responsabilidad de eso "
        "es tuya, no del operador del servicio. Tu confirmación se "
        "escribe en el registro de auditoría con marca de tiempo; volver "
        "a un modelo local la retira.",
    "vision.cloud.bestaetigung": "Lo entiendo y lo confirmo",
    "vision.cloud.bestaetigt": "(confirmado {zeit})",
    "vision.test.treffer": "{n}/2 correctas",
    "vision.test.tokens": "{ist} tokens frente a {soll}",
    "vision.test.falsch": " (incorrecta)",
    # WIRD ZITIERT: js.vision.dirty_text UND js.vision.prompt_zurueck nennen
    # diesen Knopf woertlich — bei Aenderungen beide nachziehen
    # (Zitat-Folge Tranche C).
    "vision.save.knopf": "Guardar la conexión",
    "vision.save.dirty":
        "cambios sin guardar &mdash; el reconocimiento sigue usando la "
        "conexión guardada",
    "vision.test.titel": "Probar esta conexión",
    "vision.test.knopf": "Ejecutar la prueba",
    "vision.test.nicht_gelaufen": "sin ejecutar",
    "vision.test.stufe1": "accesibilidad",
    "vision.test.stufe2": "elección forzada",
    "vision.test.stufe3": "auditoría de tokens",
    "vision.test.ungetestet": "Aún sin probar.",
    "vision.test.letzter": "Última ejecución {zeit} contra",
    "vision.galerien.stand_gut":
        "aprobada {zeit} &middot; {zellen} celdas",
    "vision.galerien.pruefen": "necesita un vistazo",
    "vision.galerien.keine": "aún sin galería",
    "vision.galerien.zu_wenig":
        "aún no hay suficientes imágenes de cuerpo entero aprobadas "
        "({n} utilizables)",
    "vision.galerien.knopf_auffrischen": "Actualizarla",
    "vision.galerien.knopf_bauen": "Crear una galería",
    "vision.galerien.zahl": "{n} imágenes utilizables &middot; {reihen}",
    "vision.galerien.titel": "Galerías",
    "vision.galerien.stand":
        "{n} galerías listas ({min} necesarias) &mdash; la visión "
        "necesita al menos dos, porque siempre compara a una persona con "
        "otra.",
    "vision.galerien.satz":
        "Solo las personas con un modelo corporal aprendido pueden tener "
        "galería; las imágenes salen del material corporal que ya "
        "aprobaste. La visión solo evalúa a personas que tienen una, y "
        "lo indica en el veredicto.",
    # --- routes/visiontest.py ---
    "visiontest.titel": "Prueba de reconocimiento",
    "visiontest.kopf.satz":
        "Rostro y persona se leen de lo que se registró en su momento "
        "&mdash; nada se recalcula. La visión se ejecuta ahora, por "
        "exactamente la misma vía que usa en el funcionamiento normal.",
    "visiontest.kosten":
        "Una ejecución de prueba cuesta peticiones reales, exactamente "
        "como el funcionamiento normal: el recorrido completo entra como "
        "una sola cuadrícula de candidatos, y cada par de galerías "
        "comparado cuesta dos peticiones, porque cada pregunta se repite "
        "con las galerías intercambiadas. Cuenta como clic manual, así "
        "que no consume tu límite diario &mdash; pero en un endpoint de "
        "pago es dinero, y con un modelo local en CPU tarda minutos.",
    "visiontest.wer.niemand": "no se reconoció a nadie",
    # EN-Klammerformen bleiben EINE Form je Schluessel (§8.18).
    "visiontest.wahl.kachel_zahlen":
        "{events} eventos &middot; {kameras} cámara(s)",
    "visiontest.wahl.vision_fertig": " &middot; visión hecha",
    "visiontest.wahl.titel": "1 &middot; Qué recorrido",
    "visiontest.wahl.leer":
        "Aún no hay recorridos registrados. En cuanto alguien cruce la "
        "propiedad, aparecerán aquí.",
    "visiontest.wahl.kopf_zahlen":
        "{events} evento(s) &middot; {kameras} cámara(s)",
    "visiontest.wahl.anderer": "elegir otro recorrido",
    "visiontest.wahl.titel_offen": "1 &middot; Elige un recorrido",
    "visiontest.wahl.anzahl": "{n} recorrido(s) reciente(s)",
    "visiontest.wahl.satz":
        "Los recorridos más recientes, agrupados exactamente como en la "
        "página Hoy.",
    "visiontest.gesicht.kein_match": "sin coincidencia",
    "visiontest.gesicht.gezeigt":
        "mostrando {gezeigt} de {gesamt} imagen(es)",
    "visiontest.gesicht.ohne_bild":
        "{fehlt} de los {unbek} evento(s) sin coincidencia no "
        "conservaron ninguna imagen",
    "visiontest.gesicht.kein_bild":
        "no se conservó ninguna imagen de rostro de este recorrido",
    "visiontest.gesicht.keines": "ningún rostro conocido",
    "visiontest.gesicht.zeile": "{person} &middot; {events} evento(s)",
    # {best} vorformatiert (:.2f) aus der Route (§8.8).
    "visiontest.gesicht.best": " &middot; mejor {best}",
    "visiontest.gesicht.unbekannt":
        "{n} evento(s) con un rostro sin coincidencia",
    "visiontest.gesicht.titel": "Rostro",
    "visiontest.gesicht.quelle":
        "comparación de embeddings con tus rostros de referencia &mdash; "
        "a partir del registro de este recorrido",
    "visiontest.koerper.kandidaten":
        "candidatos, ninguno por encima de la regla: {liste}",
    "visiontest.koerper.nichts": "nada evaluado",
    "visiontest.koerper.zeile":
        "{klasse} &middot; puntuación {score} de {schwelle} &middot; "
        "{quelle}",
    "visiontest.koerper.bild_weg": "imagen caducada",
    "visiontest.koerper.titel": "Persona",
    "visiontest.koerper.quelle":
        "embedding DINOv2 + clasificador sobre las imágenes evaluadas de "
        "este recorrido",
    "visiontest.log.warte":
        "esperando al modelo &mdash; esta página se actualiza sola",
    "visiontest.log.titel": "Qué ha pasado",
    "visiontest.gitter.alt": "la cuadrícula de candidatos de esta ejecución",
    "visiontest.gitter.bildunterschrift":
        "la imagen que realmente se mostró al modelo",
    "visiontest.gitter.zeile":
        "cuadrícula de candidatos: {n} celda(s) de este recorrido, "
        "preguntadas como UNA sola imagen",
    "visiontest.gitter.luecken": " ({n} celda(s) sin rellenar)",
    "visiontest.runden.kein_votum": "sin voto &mdash; {grund}",
    "visiontest.runden.paar": "{a} frente a {b}",
    "visiontest.nach.laeuft": "Reanalizando este recorrido",
    "visiontest.nach.stand":
        "{fertig} de {gesamt} eventos hechos &mdash; las imágenes "
        "evaluadas se recogen por el camino, esto tarda unos minutos. Es "
        "silencioso: sin avisos, sin notificaciones. Esta página se "
        "actualiza sola.",
    "visiontest.nach.titel": "No se conservó nada de este recorrido",
    "visiontest.nach.satz":
        "Analizarlo de nuevo recupera las imágenes evaluadas &mdash; y "
        "eso llena las tres vías, no solo la visión. Se vuelve a "
        "ejecutar el análisis normal sobre los eventos de este "
        "recorrido: silencioso, sin avisos, y esperando al "
        "reconocimiento en directo en lugar de apartarlo.",
    "visiontest.nach.knopf": "Analizar este recorrido de nuevo",
    "visiontest.felder.zellen": "celdas de la cuadrícula para esta ejecución",
    "visiontest.felder.voten": "confirmaciones necesarias para esta ejecución",
    "visiontest.felder.doppel":
        "preguntar cada par dos veces (comprobación de intercambio)",
    "visiontest.felder.satz":
        "Los tres valen solo para ESTA ejecución &mdash; no se guarda "
        "nada y el funcionamiento normal conserva sus propios ajustes. "
        "Este recorrido tiene {material} imagen(es) utilizable(s) "
        "&mdash; no pasa nada por pedir más celdas que eso, la "
        "cuadrícula simplemente se hace más pequeña. {galerien} "
        "galerías aprobadas permiten como máximo {voten_max} "
        "comparación(es). Con la comprobación de intercambio activada, "
        "una comparación cuesta dos peticiones; sin ella, una &mdash; y "
        "descansa entonces en una sola respuesta.",
    "visiontest.laeufe.abgebrochen": "abortada (el servicio se reinició)",
    "visiontest.laeufe.kein_urteil": "sin veredicto",
    "visiontest.laeufe.von": "de {n}",
    "visiontest.laeufe.ohne_tausch": "sin intercambio",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} sin resolver",
    "visiontest.laeufe.titel": "Ejecuciones sobre este recorrido",
    "visiontest.laeufe.kopf_wann": "cuándo",
    "visiontest.laeufe.kopf_zellen": "celdas",
    "visiontest.laeufe.kopf_noetig": "necesarias",
    "visiontest.laeufe.kopf_backend": "backend",
    "visiontest.laeufe.kopf_urteil": "veredicto",
    "visiontest.laeufe.kopf_voten": "votos",
    "visiontest.laeufe.kopf_anfragen": "petic.",
    "visiontest.laeufe.kopf_zeit": "tiempo",
    "visiontest.laeufe.satz":
        "Lo más reciente primero. Solo lo que se ejecutó de verdad "
        "&mdash; la lista sale del registro propio de este recorrido y "
        "desaparece con él.",
    "visiontest.vision.titel": "Visión",
    "visiontest.vision.quelle_kurz":
        "un modelo de visión que compara este recorrido con tus galerías",
    "visiontest.vision.unkonfiguriert": "sin configurar",
    "visiontest.vision.attr_nichts": "aún no hay nada que comparar",
    "visiontest.vision.knopf": "Ejecutar la visión sobre este recorrido",
    "visiontest.vision.nichts_satz":
        "aún no hay nada que comparar &mdash; analiza primero este "
        "recorrido de nuevo (botón de arriba)",
    "visiontest.vision.laeuft_satz":
        "hay una ejecución en marcha ahora mismo &mdash; el registro de "
        "abajo crece mientras trabaja",
    "visiontest.vision.startet": "iniciando &mdash; aún sin novedades",
    "visiontest.vision.quelle":
        "elección forzada contra tus galerías: el recorrido completo "
        "entra como UNA sola cuadrícula de candidatos, y cada par se "
        "pregunta dos veces con las galerías intercambiadas",
    "visiontest.vision.nicht_gelaufen": "sin ejecutar para este recorrido",
    "visiontest.vision.verglichen":
        "se comparó a {a} con {b} &mdash; no dice nada sobre nadie más",
    "visiontest.vision.abgebrochen":
        "ejecución abortada &mdash; el servicio se reinició",
    "visiontest.vision.kein_urteil": "sin veredicto &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten} de {bilder} comparación(es) dieron respuesta &middot; "
        "{anfragen} peticiones &middot; {dauer} s &middot; ejecución "
        "{zeit}",
    "visiontest.vision.reihenfolge": " &middot; orden: {quelle}",
    "visiontest.vision.custom_prompt": " &middot; pregunta personalizada",
    "visiontest.drei.titel": "2 &middot; Qué dicen las tres vías",
    "visiontest.drei.satz":
        "El mismo recorrido, tres juicios independientes. Pueden "
        "discrepar &mdash; ese es el sentido de mirarlos juntos.",
    # --- routes/visionwizard.py ---
    "visionwizard.schritt.person": "elige una persona",
    "visionwizard.schritt.groesse": "elige un tamaño",
    "visionwizard.schritt.vorschlag": "revisa la propuesta",
    "visionwizard.schritt.abnahme": "aprueba",
    "visionwizard.titel": "Crear una galería",
    "visionwizard.kopf.satz":
        "Una galería es una pequeña cuadrícula de imágenes de una "
        "persona &mdash; es con ella con la que el modelo de visión "
        "compara una imagen nueva. Se construye a partir de imágenes de "
        "cuerpo entero que ya aprobaste; no se graba nada nuevo y no se "
        "abre ningún vídeo.",
    "visionwizard.person.stand_gut": "galería aprobada {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} imágenes utilizables &mdash; aún no bastan para una "
        "galería. Ejecuta el Aprendizaje de persona sobre más "
        "recorridos.",
    "visionwizard.person.max_gitter":
        "la cuadrícula más grande que admite este material: {n}",
    "visionwizard.person.titel": "1 &middot; Qué persona",
    "visionwizard.person.satz":
        "Aquí solo aparecen personas con un modelo corporal aprendido, "
        "y los recuentos son las imágenes que superan el filtro de "
        "tamaño (al menos 350 píxeles de alto) &mdash; no todo lo que se "
        "extrajo alguna vez.",
    "visionwizard.groesse.zellen": "{n} celdas",
    "visionwizard.groesse.titel": "2 &middot; Cuántas imágenes",
    "visionwizard.zelle.leer":
        "no quedan imágenes para esta fila &mdash; y tampoco queda nada "
        "que tomar prestado",
    "visionwizard.zelle.geliehen": "de la fila {reihe}",
    "visionwizard.zelle.knopf_weg": "no encaja",
    "visionwizard.reihe.geliehen":
        "{n} rellenadas desde otra vista &mdash; no había suficientes "
        "imágenes limpias de la vista {reihe}",
    "visionwizard.reihe.luecken": "{n} celda(s) no se pudieron rellenar",
    "visionwizard.reihe.spreizung": "{tage} día(s), {kameras} cámara(s)",
    "visionwizard.reihe.kopf": "vista {reihe}",
    "visionwizard.reihe.eigene": "{eigene} de {gesamt} de esta vista",
    "visionwizard.vorschlag.abgelehnt":
        "{n} imagen(es) que descartaste antes quedan recordadas y no "
        "volverán.",
    "visionwizard.vorschlag.titel": "3 &middot; ¿Encaja esto?",
    "visionwizard.vorschlag.grenze":
        "Límite honesto: son mediciones de la imagen, no del momento. "
        "Una imagen en la que alguien se está atando el pelo o "
        "agachándose les parece bien a todas ellas &mdash; para eso "
        "están tus ojos.",
    "visionwizard.vorschlag.knopf": "Aprobar esta galería",
    "visionwizard.vorschlag.kopie_satz":
        "Al aprobar, estas imágenes se copian a la carpeta de la "
        "galería. Desde entonces la galería queda fija: borrar un "
        "original más tarde no puede abrirle agujeros &mdash; suslik "
        "solo te pide aprobarla de nuevo.",
    "visionwizard.fertig.geliehen": " &middot; prestada",
    "visionwizard.fertig.titel": "Galería aprobada",
    "visionwizard.fertig.stand": "{zellen} celdas, aprobada {zeit}.",
    "visionwizard.fertig.satz":
        "Son copias dentro de la carpeta de la galería, con el origen de "
        "cada imagen (ejecución, archivo, suma de comprobación) anotado "
        "al lado. Viajan con tu copia de seguridad.",
    "visionwizard.fertig.knopf_neu":
        "Crearla de nuevo con el material actual",
    "visionwizard.fertig.knopf_zurueck": "Volver a Detección de visión",
    "visionwizard.neu.titel": "Material nuevo disponible",
    "visionwizard.neu.satz":
        "Nada cambia por sí solo &mdash; la galería que aprobaste se "
        "queda exactamente como está hasta que crees y apruebes una "
        "nueva.",
    # --- routes/personwizard.py ---
    "personwizard.wer.alle": "todas las personas conocidas",
    "personwizard.wer.fremde": "extraños",
    "personwizard.titel":
        "Aprendizaje de personas — reconocimiento corporal",
    "personwizard.kopf.satz":
        "Una segunda vía de reconocimiento independiente: aprende el "
        "aspecto de una persona en su CONJUNTO (complexión, pelo, "
        "postura) para reconocer a los miembros del hogar incluso cuando "
        "no se ve ningún rostro.",
    "personwizard.kopf.wie_titel":
        "Cómo funciona — tú mantienes el control",
    "personwizard.kopf.schritt1":
        "1 · Tú eliges cuántos eventos repasar y a QUIÉN aprender a "
        "reconocer (una persona o todas las conocidas).",
    "personwizard.kopf.schritt2":
        "2 · La ejecución extrae imágenes de cuerpo entero de tus "
        "propias grabaciones. Una imagen solo se vincula a una persona "
        "cuando lo demuestra un recorrido confirmado por rostro — "
        "conservador a propósito.",
    "personwizard.kopf.schritt3":
        "3 · TÚ revisas cada imagen extraída; un clic descarta una "
        "equivocada. No se aprende nada sin tu aprobación.",
    "personwizard.kopf.schritt4":
        "4 · El entrenamiento se ejecuta después en local en segundos, y "
        "se mide un umbral de decisión para que los extraños queden por "
        "debajo.",
    "personwizard.kopf.tempo":
        "Una nota sobre la velocidad: la extracción se ejecuta por ahora "
        "en la CPU, así que ten paciencia si una ejecución tarda un poco "
        "(unos 15&ndash;30 s por evento). Llevarla a la GPU/NPU está "
        "previsto para una versión posterior.",
    "personwizard.kopf.warum":
        "Por qué primero al menos una persona: esta vía solo puede "
        "distinguir personas después de haber aprendido — y de que tú "
        "hayas revisado — el aspecto de al menos un miembro del hogar. "
        "Hasta entonces el reconocimiento corporal permanece APAGADO y "
        "nunca envía un aviso. Cuando más adelante avise "
        "(Pushover/Telegram), el mensaje va marcado como procedente del "
        "reconocimiento de persona, no del facial.",
    "personwizard.vorb.titel": "Preparando la ejecución &hellip;",
    "personwizard.vorb.zeile":
        "vinculando los últimos {n} eventos con {wer} mediante "
        "recorridos confirmados",
    "personwizard.vorb.satz":
        "Esto tarda un minuto o dos — la página se actualiza sola, la "
        "extracción empieza justo después.",
    "personwizard.ernte.stand":
        "{events}/{von} eventos · {bilder} imágenes extraídas",
    "personwizard.ernte.startet": "iniciando …",
    "personwizard.ernte.titel": "Hay un aprendizaje de persona en marcha",
    "personwizard.ernte.zeile":
        "aprendiendo a reconocer a {wer} · {stand}",
    "personwizard.ernte.satz":
        "Esta página se actualiza sola. Una ejecución nueva se puede "
        "iniciar cuando esta termine.",
    "personwizard.ernte.knopf_abbruch": "Abortar ejecución",
    "personwizard.ernte.abbruch_hinweis":
        "las imágenes extraídas se conservan",
    "personwizard.unterbrochen.titel":
        "La última ejecución se interrumpió",
    "personwizard.unterbrochen.satz":
        "Probablemente un reinicio del servicio. Inicia abajo la misma "
        "ejecución de nuevo — los eventos ya extraídos se omiten "
        "automáticamente (reanudación), no se pierde nada.",
    "personwizard.abnahme.titel":
        "La última ejecución ha terminado — ahora te toca revisar",
    "personwizard.abnahme.zeile":
        "{n} imágenes extraídas para {wer} (ejecución {lauf}).",
    "personwizard.abnahme.knopf": "Revisar las imágenes ahora",
    "personwizard.abnahme.hinweis":
        "termina la revisión para desbloquear la siguiente ejecución",
    "personwizard.abnahme.knopf_verwerfen": "Descartar esta ejecución",
    "personwizard.abnahme.verwerfen_hinweis":
        "¿mal resultado? tíralo todo",
    "personwizard.leer.verwaist":
        "Omitidos a propósito: {liste} — estos nombres se eliminaron de "
        "tus personas; sus eventos confirmados antiguos se quedan como "
        "historial, pero no se extraen.",
    "personwizard.leer.titel":
        "La ejecución terminó sin imágenes — este es el porqué",
    "personwizard.leer.satz":
        "No se cambió nada; puedes iniciar otra ejecución abajo en "
        "cualquier momento.",
    "personwizard.fertig.verwaist":
        "Omitidos a propósito: {liste} — personas eliminadas; sus "
        "eventos confirmados antiguos no se extraen.",
    "personwizard.fertig.fremd":
        "{n} imágenes de extraños confirmadas han pasado al conjunto de "
        "extraños — el próximo entrenamiento las usa de inmediato.",
    "personwizard.fertig.titel": "Revisión terminada — material incorporado",
    "personwizard.fertig.zeile":
        "{abgenommen} imágenes aprobadas como material de aprendizaje, "
        "{verworfen} descartadas (ejecución {lauf}).",
    "personwizard.fertig.knopf": "Ver el material aprendido",
    "personwizard.fehler.titel": "La última ejecución ha fallado",
    "personwizard.auswahl.opt_alle": "Todas las personas conocidas",
    "personwizard.auswahl.opt_fremde":
        "Extraños — recoger imágenes de extraños",
    "personwizard.auswahl.titel": "A quién aprender a reconocer",
    "personwizard.auswahl.satz":
        "Elige una persona para revisar en tandas pequeñas y centradas — "
        "o todas a la vez. Las personas vienen de tu banco de rostros; "
        "hacerlo de una en una mantiene la revisión corta.",
    "personwizard.auswahl.fremde_satz":
        "Extraños: extrae imágenes de los recorridos en los que no se "
        "reconoció a nadie (recorridos solo por la calle, visitantes sin "
        "confirmar). En la revisión confirmas cuáles son de verdad "
        "extraños — van al conjunto de extraños y afinan el umbral de "
        "decisión.",
    "personwizard.umfang.knopf_letzte": "últimos {n}",
    "personwizard.umfang.attr_eigen": "N propio",
    "personwizard.umfang.knopf_go": "ir",
    "personwizard.umfang.titel": "Alcance (eventos, no días)",
    "personwizard.umfang.satz":
        "Empieza en pequeño (50) — revisarás a mano cada imagen "
        "extraída.",
    "personwizard.bilanz.ohne":
        "últimos {n} eventos de persona para {wer} — el balance de "
        "vinculación se calcula al crear la ejecución",
    # Zaehler-Split an der <b>-Grenze (§8.10): vor/nach rahmen die
    # hervorgehobene Zahl, Rand-Leerzeichen gehoeren zum Wert.
    "personwizard.bilanz.zahl_vor": "últimos {n} eventos de persona · ",
    "personwizard.bilanz.zahl_nach":
        " se pueden vincular con {wer} mediante recorridos confirmados",
    "personwizard.bilanz.fremd": " · {n} candidatos a extraño",
    "personwizard.bilanz.erkl_fremd":
        "Los candidatos son recorridos en los que no se reconoció a "
        "nadie — recorridos solo por la calle y visitantes sin "
        "confirmar. Todo es una SOSPECHA hasta tu revisión; marca allí a "
        "quien NO sea un extraño.",
    "personwizard.bilanz.erkl":
        "La vinculación es conservadora: solo cuentan los recorridos con "
        "exactamente una persona confirmada por rostro. Todo lo que veas "
        "después se puede descartar con un clic.",
    "personwizard.bilanz.titel": "Tu selección",
    "personwizard.bilanz.knopf": "Crear esta ejecución",
    "personwizard.review.stempel": "MAL",
    "personwizard.review.h_fremde": "Extraños",
    "personwizard.review.frage_fremd":
        "haz clic en cada imagen que NO sea un extraño (un miembro del "
        "hogar, una visita conocida) o que no sirva. Un segundo clic lo "
        "deshace. Todo se guarda al instante; las imágenes sin marcar se "
        "incorporan como extraños confirmados y afinan el umbral de "
        "decisión.",
    "personwizard.review.frage":
        "haz clic en cada imagen que esté MAL (no es esta persona o no "
        "sirve). Un segundo clic lo deshace. Todo se guarda al instante; "
        "las imágenes sin marcar cuentan como aprobadas.",
    "personwizard.review.titel": "Revisar la extracción",
    "personwizard.review.kopf": "Ejecución {lauf} — {frage}",
    # Der Zeilenumbruch ist Teil des Originals (Template-Literal) und
    # bleibt fuer die Byte-Treue im Wert.
    "personwizard.review.zurueck": "&larr; volver al\nasistente",
    "personwizard.review.knopf_fertig":
        "Terminar la revisión — incorporar las aprobadas",
    "personwizard.kontrolle.sammeln_titel":
        "El modo de recogida está ACTIVADO",
    "personwizard.kontrolle.sammeln_rest":
        " — cada imagen evaluada se conserva 30 días para que puedas "
        "comprobar las decisiones más tarde. Cuenta con unos "
        "20&ndash;40 MB al día.",
    "personwizard.kontrolle.schlank_titel": "Modo ligero (predeterminado)",
    "personwizard.kontrolle.schlank_rest":
        " — las imágenes evaluadas solo viven mientras hay un recorrido "
        "en curso; después solo quedan la imagen ganadora y el registro "
        "de veredictos de abajo. Es la opción predeterminada, respetuosa "
        "con la privacidad, para una instalación nueva.",
    "personwizard.kontrolle.titel": "Imágenes evaluadas",
    "personwizard.kontrolle.satz":
        "Lo que el reconocimiento corporal miró de verdad, un bloque por "
        "recorrido: la imagen que evaluó, la clase que le salió, la "
        "puntuación y de dónde vino la imagen. Útil cuando se pasó por "
        "alto a una persona, o se reconoció a alguien que no debía.",
    "personwizard.kontrolle.leer_titel": "Aún no hay nada registrado",
    # Genus-Regel: Label unter einem Bild, nie generisch maskulin.
    "personwizard.kontrolle.tag_fremd": "persona extraña",
    "personwizard.kontrolle.tag_drueber": "por encima del umbral",
    "personwizard.kontrolle.tag_drunter": "por debajo del umbral",
    "personwizard.kontrolle.schwelle": " &middot; umbral {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} evaluadas, {n} imagen conservada",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} evaluadas, {n} imágenes conservadas",
    "personwizard.tabelle.fremd_zeile": "Extraños (clase adicional)",
    "personwizard.tabelle.kein_fremd":
        "Aún no hay clase de extraños — el reconocimiento funciona mucho "
        "mejor con una: las imágenes de extraños confirmadas enseñan al "
        "modelo lo que NO pertenece y calibran el umbral de decisión.",
    "personwizard.tabelle.q_eichung": "medido",
    "personwizard.tabelle.q_user": "definido por ti",
    "personwizard.tabelle.q_standard": "valor por defecto incorporado",
    "personwizard.tabelle.f_modell": "Modelo activo",
    "personwizard.tabelle.f_schwelle": "Umbral",
    "personwizard.tabelle.f_scharf": "Armado",
    "personwizard.tabelle.scharf_ja": "SÍ",
    "personwizard.tabelle.scharf_ja_rest": " — evaluando en directo",
    "personwizard.tabelle.scharf_nein": "no — sin armar",
    "personwizard.tabelle.konf_vor":
        "Mayor confusión entre grupos en la calibración: ",
    "personwizard.tabelle.konf_nach":
        " — la puntuación más alta que alguna imagen alcanzó para el "
        "grupo EQUIVOCADO; cuanto más cerca de 1, más se parecen dos "
        "grupos.",
    "personwizard.tabelle.titel": "Grupos aprendidos",
    "personwizard.karte.scharf": "Armado",
    "personwizard.karte.unscharf": "Aún sin armar",
    "personwizard.karte.fehler":
        "El último intento de entrenamiento FALLÓ: {fehler} — esta "
        "tarjeta muestra el modelo anterior.",
    "personwizard.karte.titel": "Estado del modelo",
    "personwizard.karte.zeile":
        "entrenado {wann} en {dauer} s — {bilder} imágenes: {je} · "
        "{modell} · ",
    "personwizard.karte.link": "detalles",
    "personwizard.bestand.titel":
        "Material de persona — lo que se ha aprendido",
    "personwizard.bestand.satz":
        "Imágenes de cuerpo entero aprobadas por persona. Elige abajo un "
        "grupo para ver sus imágenes; elimina una imagen suelta "
        "(&times; en la miniatura) — una ejecución nueva siempre puede "
        "volver a extraerlas. Las eliminaciones surten efecto en el "
        "próximo entrenamiento.",
    "personwizard.bestand.leer_titel": "Aún no hay material aprobado",
    "personwizard.bestand.stark_titel": "Qué hace fuerte a este modelo",
    "personwizard.bestand.chip_fremde": "Extraños ({n})",
    "personwizard.bestand.zeigen_titel": "Mostrar imágenes de",
    "personwizard.bestand.zeigen_satz":
        "Elige un grupo — sus imágenes se abren abajo, las más recientes "
        "primero.",
    "personwizard.bestand.marker_tage.eins":
        "solo {n} día — el reconocimiento mejora sobre todo con imágenes "
        "de más días, distintas ropas y distinta luz",
    "personwizard.bestand.marker_tage.viele":
        "solo {n} días — el reconocimiento mejora sobre todo con "
        "imágenes de más días, distintas ropas y distinta luz",
    "personwizard.bestand.attr_loeschen": "eliminar esta imagen",
    "personwizard.bestand.z_bilder": "{n} imágenes",
    "personwizard.bestand.z_tage.eins": "{n} día",
    "personwizard.bestand.z_tage.viele": "{n} días",
    "personwizard.bestand.z_kameras.eins": "{n} cámara",
    "personwizard.bestand.z_kameras.viele": "{n} cámaras",
    "personwizard.modell.titel": "Modelo de persona — estado",
    "personwizard.modell.satz":
        "El modelo del reconocimiento corporal, entrenado con tus "
        "imágenes aprobadas. Se reentrena automáticamente tras cada "
        "revisión terminada y tras las eliminaciones.",
    "personwizard.modell.leer_titel": "Aún no hay modelo",
    "personwizard.modell.fremd_keine":
        "aún ninguno — umbral medido solo entre tus personas",
    "personwizard.modell.fremd_gesammelt":
        "{n} recogidos — hacen falta {min} antes de que entren en el "
        "entrenamiento y calibren el umbral",
    "personwizard.modell.fremd_geeicht":
        "{n} en el entrenamiento · umbral calibrado contra extraños "
        "reales",
    "personwizard.modell.fremd_ungeeicht":
        "{n} en el entrenamiento — la calibración del umbral no se "
        "ejecutó (mira la nota de abajo)",
    "personwizard.modell.f_trainiert": "Entrenado",
    "personwizard.modell.f_dauer": "Tiempo de entrenamiento",
    "personwizard.modell.f_modell": "Modelo",
    "personwizard.modell.f_bilder": "Imágenes en total",
    "personwizard.modell.f_personen": "Personas",
    "personwizard.modell.f_fremd": "Negativos de extraños",
    "personwizard.modell.scharf_ja": "SÍ — evaluación en directo activa",
    "personwizard.modell.scharf_nein": "no — aún sin armar",
    "personwizard.modell.fehler":
        "El último intento de entrenamiento FALLÓ ({zeit}): {fehler} — "
        "el modelo que se muestra aquí es el anterior y no incluye tus "
        "últimos cambios.",
    "personwizard.modell.aktuell_titel": "Modelo actual",
    "personwizard.modell.material_titel":
        "Material de aprendizaje por persona",
    "personwizard.modell.kopf_person": "persona",
    "personwizard.modell.kopf_bilder": "imágenes aprobadas",
    "personwizard.modell.kopf_anteil": "proporción",
    "personwizard.modell.summe": "total",
    "personwizard.modell.q_eichung": "medido con tu material",
    # {pct} vorformatiert (round) aus der Route (§8.8).
    "personwizard.modell.eich_fremd":
        "Medido por validación cruzada de {folds} particiones sobre {n} "
        "imágenes reservadas de tus personas más {n_fremd} extraños "
        "confirmados: la mayor confianza como miembro del hogar que "
        "alcanzó un extraño real fue {max} &rarr; umbral {schwelle}; el "
        "{pct}% de las imágenes genuinas lo supera. La otra cara de la "
        "moneda: {ueber} de tus propias imágenes alcanzarían ese umbral "
        "para la persona EQUIVOCADA (máximo {vmax}).",
    "personwizard.modell.eich_intern":
        "Medido por validación cruzada de {folds} particiones sobre {n} "
        "imágenes reservadas: mayor confianza para una persona "
        "EQUIVOCADA {max} &rarr; umbral {schwelle}; el {pct}% de las "
        "imágenes genuinas lo supera. Límite honesto: esto calibra ENTRE "
        "tus personas aprendidas — aún no hay extraños reales en el "
        "material.",
    "personwizard.modell.regeln_titel": "Ajustes de decisión",
    "personwizard.modell.schwelle_vor": "Umbral de decisión: ",
    "personwizard.modell.r_fenster": "Ventana de disparo",
    "personwizard.modell.r_feuer": "Eventos de apoyo para disparar",
    "personwizard.modell.r_karenz": "Pausa tras un aviso",
    "personwizard.modell.regeln_satz":
        "Deja el umbral vacío para seguir automáticamente el valor "
        "medido (se vuelve a medir con cada entrenamiento). La regla de "
        "disparo: avisar solo tras este número de eventos de apoyo "
        "dentro de la ventana, y después guardar silencio durante la "
        "pausa.",
    "personwizard.modell.knopf_speichern": "Guardar ajustes",
    "personwizard.modell.satz_user":
        "El umbral de decisión lo has definido tú ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — la calibración contra {n} extraños confirmados sería {alt}",
    "personwizard.modell.satz_geeicht":
        "El umbral de decisión está calibrado contra {n} imágenes de "
        "extraños confirmadas.",
    "personwizard.modell.satz_ungeeicht":
        "El umbral de decisión aún no está calibrado contra material de "
        "extraños — trata los avisos como una vista previa y no los "
        "pierdas de vista.",
    "personwizard.modell.satz_fremd_drop":
        " Un cuerpo que el modelo interpreta como extraño se descarta "
        "antes de que pueda convertirse en una coincidencia.",
    "personwizard.modell.live_titel": "Interruptor de directo",
    "personwizard.modell.live_an":
        "ARMADO — la vía del cuerpo evalúa los eventos en directo y "
        "puede avisar.",
    "personwizard.modell.live_aus":
        "Sin armar — la vía del cuerpo guarda silencio.",
    "personwizard.modell.live_hinweis":
        "Los avisos llevan la nota &quot;reconocimiento de persona, no "
        "facial&quot;.",
    "personwizard.modell.knopf_disarm": "Desarmar",
    "personwizard.modell.knopf_arm": "Armar el reconocimiento corporal",
    # --- webui/bausteine.py ---
    # Nur die gt_leiste-ANZEIGE-Texte; Speicherwerte und KAT_LABELS bleiben
    # literal (§8.12/§8.13). Genus-Regel (begriffe_tabellen.md ES): kein
    # fester maskuliner Personen-String unterm Bild — "Persona extraña".
    "baustein.gt.fremd": "Persona extraña",
    "baustein.gt.kein_mensch": "No es una persona",
    "baustein.gt.add": "añadir persona…",
    "baustein.gt.uebernehmen": "confirmar esta propuesta (todas las personas indicadas estaban)",
    "baustein.gt.fremd_titel": "había un desconocido (puede ir junto a nombres)",
    "baustein.gt.unklar_titel": "no estoy seguro — dejar abierto",
    "baustein.gt.kein_mensch_titel": "ninguna persona en este evento (falsa activación)",
    "baustein.gt.opak_titel": "un juicio antiguo que ya no corresponde a ninguna persona conocida — elige ? o un nombre para sustituirlo",
    # ---- Route-JS + Meldungen (Stufe 2, Tranche D) ----
    # Spiegel des gleichnamigen en.py-Abschnitts (Gattungen, Grenzen und
    # deklarierte Splits dort). Rand-Leerzeichen gehoeren zum Wert;
    # Namens-/Kennungs-Zitate im Toast/confirm mit «…» (es.py-Konvention).
    # Wiederverwendet aus dem Bestand: lernanker.js.fehler /
    # nicht_uebernommen / nicht_gespeichert (beide Routen, s. oben).
    # --- routes/lernwizard.py (Zuweisungs-Flaeche + Sichtung) ---
    "lernwizard.zw.js_zaehl_mitte": " de ",
    "lernwizard.zw.js_zaehl_nach": " imágenes seleccionadas",
    "lernanker.js.uebernimmt": "incorporando…",
    "lernanker.js.tag_frage_vor":
        "Los ajustes han cambiado desde que pusiste el nombre:\n",
    "lernanker.js.tag_frage_nach":
        "\n¿Incorporar de todos modos la selección ya nombrada?",
    "lernanker.js.weiter": "guardado — siguiente grupo…",
    "lernanker.js.speichert": "guardando…",
    "lernanker.js.koll_vor": "«",
    "lernanker.js.koll_mitte": "» coincide con la persona ya existente «",
    "lernanker.js.koll_nach":
        "» — ¿añadir el grupo a esa persona en su lugar?",
    "lernwizard.zw.js_gespeichert_vor": "guardado como ",
    "lernwizard.zw.js_gespeichert_nach": " — comprobando las imágenes …",
    "lernwizard.sicht.js_fehl":
        "la comprobación ha fallado — recarga la página para reintentar",
    "lernwizard.zw.js_verbergen":
        "Ocultar las otras {n} imágenes comprobadas",
    "lernwizard.zw.js_zeigen": "Mostrar todas las {n} imágenes comprobadas",
    # --- routes/qualitaet.py ---
    "qualitaet.galerie.js_gewaehlt": " seleccionadas",
    # --- routes/lernanker.py (nur dort) ---
    "lernanker.js.alle_fertig":
        "Todos los grupos listos — las imágenes nombradas ya cuentan "
        "para el reconocimiento.",
    # --- routes/vision.py (Hand-ID-Script) ---
    "vision.modell.js_id_fehlt": "escribe primero un id",
    "vision.modell.js_prueft": "comprobando …",
    "vision.modell.js_fehler": "error",
    # --- routes/personwizard.py (Review-Script + Schalter) ---
    "personwizard.review.js_zaehl": " de {n} marcadas como MAL",
    "personwizard.review.js_frage_vor": "¿Terminar la revisión? ",
    "personwizard.review.js_frage_mitte":
        " imágenes se incorporarán como material de aprendizaje, ",
    "personwizard.review.js_frage_nach": " descartadas.",
    "personwizard.modell.js_fehler": "error ",
    # --- verifyd.py POST-Antworten (antwort.*, Nutzungs-Reihenfolge) ---
    "antwort.person_entfernt":
        "Se ha eliminado a {person} ({n} imágenes de referencia movidas "
        "a la papelera — recuperables)",
    "antwort.person_name_ungueltig": "nombre no válido",
    "antwort.person_unbekannt": "persona desconocida",
    "antwort.pruefung_gestartet": "comprobación iniciada",
    "antwort.reorg_los":
        "Reorganizando (se vuelven a comprobar los rostros recogidos y se "
        "reagrupan; 1-2 min, después recarga las páginas)",
    "antwort.reorg_laeuft":
        "La reorganización ya está en marcha — espera un momento",
    "antwort.paar_notiert": "anotado — no se volverá a proponer este par",
    # §8.11-Anhang an eine Fachschicht-msg (die Basis bleibt Grenze).
    "antwort.nachpruefung_anhang":
        " — comprobando de nuevo los eventos de este recorrido en "
        "segundo plano",
    "antwort.sync_wieder": "{n} de vuelta en la lista de candidatas",
    "antwort.sync_auswahl": "{ab} deseleccionadas, {zu} devueltas",
    "antwort.sync_laeuft":
        "ya hay una sincronización en curso — espera a que termine",
    "antwort.sync_readonly":
        "modo de solo lectura: la escritura de referencias en Frigate "
        "está desactivada (mira el interruptor de la página Sistema)",
    "antwort.sync_nichts":
        "no hay nada seleccionado — marca al menos una imagen",
    "antwort.frigate_url": "URL de Frigate: {fehler}",
    "antwort.sync_transfer": "transferencia en curso ({n} seleccionadas)",
    "antwort.bruecke_hinzu": "{n} imagen(es) añadida(s)",
    "antwort.modell_laedt":
        "cargando el modelo de reconocimiento — unos segundos …",
    "antwort.refcache_baut":
        "reconstruyendo el banco de referencias — con un banco grande "
        "puede tardar un minuto …",
    "antwort.refcache_fehler":
        "la reconstrucción del banco de referencias ha fallado dos veces "
        "seguidas — mira el registro del servicio (/log); el siguiente intento "
        "se hará en unos minutos",
    "antwort.cache_aufgeraeumt": "{n} clip(s) eliminado(s), {mb} MB liberados — caché {cache} GB, {frei} GB libres",
    "antwort.bruecke_nimmt": "la comprobación elige {n} imagen(es)",
    "antwort.bruecke_grenz_zusatz":
        " · otras {n} al límite se muestran sin marcar",
    "antwort.bruecke_nur_grenz":
        "nada claramente útil — {n} imagen(es) al límite retenida(s) "
        "(identidad segura, calidad de imagen solo aceptable); aun así "
        "puedes tomarlas",
    "antwort.bruecke_nichts":
        "nada que tomar — ninguna imagen nueva útil en este recorrido "
        "(no pasa nada)",
    "antwort.bruecke_undo": "{n} imagen(es) quitada(s) de nuevo",
    "antwort.personlauf_kein_review":
        "ninguna ejecución pendiente de revisión",
    "antwort.personlauf_kein_lauf": "ninguna ejecución activa",
    "antwort.events_bereich": "los eventos deben estar entre 1 y {max}",
    "antwort.personlauf_aktiv":
        "ya hay un aprendizaje de persona en marcha",
    # Muster lokalisiert (AAAA-MM-DD), nicht zitiert: die Eingabe ist ein
    # <input type="date"> (routes/lernwizard.py lf-pop-tag), das seinen
    # Format-Hinweis in der Browsersprache zeigt (es: dd/mm/aaaa) — das
    # Token YYYY-MM-DD steht NIRGENDS in der Oberflaeche.
    "antwort.lernlauf_tag_ungueltig": "día no válido (AAAA-MM-DD)",
    # {phase} ist die interne Phasen-Kennung (sprachneutral, §8.19).
    "antwort.lernlauf_phase":
        "ya hay una ejecución en la fase «{phase}» — abórtala primero",
    "antwort.lernlauf_beschaeftigt":
        "la ejecución anterior aún está terminando su evento actual — "
        "inténtalo de nuevo en un momento",
    "antwort.lernlauf_schreibfehler":
        "no se pudo escribir el estado de la ejecución: {fehler}",
    "antwort.lernlauf_angelegt": "ejecución creada",
    "antwort.lernlauf_abgebrochen":
        "abortada — un evento en marcha todavía puede terminar en "
        "segundo plano",
    "antwort.live_nichts": "nada que cambiar",
    "antwort.live_an": "vigilancias iniciadas: {ok}/{alle}",
    "antwort.live_aus": "vigilancias detenidas: {ok}/{alle}",
    "antwort.vision_modell_ok":
        "el modelo ha respondido — añadido a la lista como comprobado a "
        "mano; elígelo allí y guarda",
    "antwort.restore_upload_fehlt": "falta la subida o es demasiado grande",
    "antwort.restore_upload_kaputt": "subida truncada",
    "antwort.backend_unbekannt": "backend desconocido «{backend}»",
    "antwort.kameras_fehlen": "cámaras de Frigate no disponibles: {fehler}",
    "antwort.setup_gespeichert":
        "Configuración inicial guardada — reiniciando",
    "antwort.kameras_gespeichert": "{n} cámaras guardadas — reiniciando",
    "antwort.name_ungueltig":
        "nombre de persona no válido (2-40 letras, dígitos, espacio, -)",
    "antwort.anker_unbekannt": "ancla desconocida",
    "antwort.anker_benannt":
        "nombrado como «{name}» — {n} imágenes seleccionadas; "
        "incorpóralas con el botón «Incorporar»",
    "antwort.anker_nur_unadoptiert":
        "solo se pueden descartar grupos sin imágenes incorporadas",
    "antwort.anker_verworfen":
        "eliminado — {n} imágenes borradas",
    "antwort.lauf_id_ungueltig": "id de ejecución no válido",
    "antwort.lauf_aktiv": "esta ejecución sigue activa — abórtala primero",
    "antwort.lauf_nichts":
        "no se encontró nada de la ejecución {lauf} — ¿ya estaba "
        "eliminada?",
    "antwort.lauf_nur_einer":
        "nada que eliminar — solo queda una ejecución guardada",
    "antwort.gruppe_unbekannt": "grupo desconocido o cerrado",
    "antwort.sichtung_laeuft":
        "comprobando las imágenes — unos segundos …",
    "antwort.anker_unbenannt":
        "el ancla no tiene nombre (o es desconocida)",
    "antwort.adopt_nichts":
        "no hay nada seleccionado — marca al menos una imagen para "
        "incorporar",
    "antwort.adopt_phantom":
        "la deduplicación solo encontró coincidencias con referencias "
        "que ya no existen en el disco — reintenta la incorporación; si "
        "se repite, informa del problema",
    "antwort.adopt_gedeckt":
        "ya cubierto — todo lo seleccionado ({n}) es casi idéntico a las "
        "referencias que {person} ya tiene; el grupo queda marcado como "
        "incorporado, no se ha copiado nada",
    # §8.10-Plural-Split via t_n (wie EN).
    "antwort.adopt_fertig.eins":
        "{n} referencia incorporada para «{person}»",
    "antwort.adopt_fertig.viele":
        "{n} referencias incorporadas para «{person}»",
    "antwort.adopt_skip": ", {n} omitidas por ser casi idénticas",
    "antwort.adopt_watchdog":
        " — comprobación de deriva en marcha (página Sistema)",
    "antwort.areas_gespeichert.eins": "{n} área guardada",
    "antwort.areas_gespeichert.viele": "{n} áreas guardadas",
    # text/plain-Antwort der /video- und /clip-Routen (Tranche-B-Rest).
    "antwort.clip_weg":
        "El clip ya no está en la caché — retención de {tage} días",
    # --- Konstante->Schluessel (Kennung/Anzeige-Trennung, Paket 3) ---
    # 3a: {hinweis}-Baustein fuer system.backup.careful_config und
    # system.voll.careful („este archivo {hinweis}" — „trátalo" greift
    # das Rahmen-Subjekt auf, statt „este archivo" zu wiederholen).
    "system.backup.hinweis":
        "contiene tus claves de API — trátalo como una contraseña",
    # 3b: Reihen-Woerter fuer die {reihe}-Rahmen („vista/fila {reihe}",
    # js.vw.geliehen) — alle Rahmen sind feminin: frontal/lateral/posterior
    # sind genusinvariant, indeterminada steht feminin zu vista/fila. Das
    # Trio frontal/lateral/posterior ist der uebliche spanische Ansichten-
    # Satz (trasera gehoert ins Fahrzeug-Register).
    "visiongalerie.reihe.vorn": "frontal",
    "visiongalerie.reihe.seitlich": "lateral",
    "visiongalerie.reihe.hinten": "posterior",
    "visiongalerie.reihe.unklar": "indeterminada",
    # 3c: Kategorie-ANZEIGE (bausteine.kat_wort) — Genus-Regel: nie
    # generisch maskulin fuer Personen-Labels („Persona …-Muster").
    "baustein.kat.erkannt": "Persona reconocida",
    "baustein.kat.fremd_verdacht": "¿Persona extraña?",
    "baustein.kat.unbekannt_schwach": "Sin identificar (débil)",
    "baustein.kat.fehler": "Error",
    "baustein.kat.no_person":
        "No se encontró ninguna persona (probablemente una falsa "
        "detección)",
    "baustein.kat.deckung": "Coincidencia",
    # „Discrepancia" ist das Gegenwort zu „Coincidencia" (die zwei Seiten
    # stimmen ueberein / weichen ab); „contradicción" ist in es.py schon
    # fuer den Modell-Widerspruch der Vision-Seite vergeben.
    "baustein.kat.widerspruch": "Discrepancia",
    "baustein.kat.frigate_nur": "Solo Frigate",
    "baustein.kat.wir_nur": "Solo suslik",
    "baustein.kat.beide_unknown": "Ambos sin identificar",
    # 3d: Wortstufen-ANZEIGE (bausteine.stufe_wort), klein im Satzfluss —
    # Rahmen event.ours_zeile: "{person} — {stufe} (aparece en {n} …)".
    "baustein.stufe.clear": "coincidencia clara",
    "baustein.stufe.narrow": "justo por encima del umbral",
    "baustein.stufe.below": "por debajo del umbral",
    "baustein.stufe.none": "sin coincidencia",
    # ---- Anleitungen /hilfe (Stufe 3) ----
    # Struktur/Grenzen s. en.py-Abschnittskommentar (ein <p>-Absatz = ein
    # Schluessel, Tag-Folge gepinnt). ZITAT-KOPPLUNGEN dieser Sprache,
    # wortgleich zum es.py-Bestand: "Elegir cámaras"
    # (erkennung.live.knopf_kameras), "Notificaciones"
    # (benachrichtigungen.titel), "Sincronización con Frigate"
    # (nav.sync_auswahl), "Gestionar personas" / "Registrar rostro"
    # (erkennung.gesicht.knopf_verwalten / erkennung.knopf_register_face),
    # "Registrar cuerpo" (erkennung.koerper.knopf_register), "Detección de
    # visión" (nav.vision). Die Unteroptions-Labels "Always" / "Only if no
    # face" / "If needed" sind Anzeige==Kennung (§8.2, noch englische
    # Literale in routes/erkennung.py) und bleiben deshalb ENGLISCH
    # zitiert.
    "hilfe.live.titel": "La vigilancia en directo, explicada",
    "hilfe.live.satz1": """<p>La vigilancia en directo mira tus cámaras en cuanto algo se mueve.
Cuando una persona entra en la propiedad, recibes un aviso en cuestión de
segundos, y si el sistema ya conoce el rostro, el aviso lleva un
nombre.</p>""",
    "hilfe.live.satz2": """<p>En esta fase el nombre es una primera estimación. La comprobación a
fondo llega justo después, sobre la grabación, y tiene la última
palabra.</p>""",
    "hilfe.live.satz3": """<p>La vigilancia en directo no depende de Frigate: no la disparan los
eventos de Frigate y funciona completamente por su cuenta. Observa el
stream de vídeo directamente, ya sea el stream proxy de Frigate o el propio
de la cámara; eso lo eliges por cámara.</p>""",
    "hilfe.live.satz4": """<p>Con <b>Elegir cámaras</b> decides qué cámaras se vigilan. Cada cámara
vigilada cuesta potencia de cálculo las veinticuatro horas, así que empieza
por donde la gente llega de verdad: la entrada de coches, la puerta
principal, la verja. Después puedes añadir más.</p>""",
    "hilfe.live.satz5": """<p>Apagar aquí una cámara no cambia nada en la grabación. Frigate sigue
grabando como hasta ahora; el interruptor solo decide si suslik mira la
imagen al momento o espera a la grabación.</p>""",
    "hilfe.gesicht.titel": "El reconocimiento facial, explicado",
    "hilfe.gesicht.satz1": """<p>Esta es la vía básica con la que suslik reconoce y aprende rostros.
Cada recorrido grabado se coteja con los rostros que le has enseñado al
sistema.</p>""",
    "hilfe.gesicht.satz2": """<p>El aprendizaje parte de tus propias cámaras: suslik recoge los rostros
que ve, tú miras las imágenes y le dices quién es quién. Cuantas más
situaciones y poses distintas haya visto de una persona, mejor funciona:
luz de día, atardecer, con gorro, sin gorro, de perfil.</p>""",
    "hilfe.gesicht.satz3": """<p>Si Frigate ya conoce rostros, puedes importarlos en la página
Sincronización con Frigate. La recomendación sigue siendo aprender los
rostros aquí: el aprendizaje propio de suslik recoge muchas poses y
situaciones distintas por persona, y esas referencias dan mejores
resultados en suslik que los rostros incorporados desde Frigate. Lo que
enseñes aquí puede devolverse a Frigate en la página de sincronización si
quieres.</p>""",
    "hilfe.gesicht.satz4": """<p>Todo se queda en tu máquina. No se sube nada a ninguna parte y no hay
ningún servicio en la nube detrás.</p>""",
    "hilfe.gesicht.satz5": """<p>Cuando se reconoce un rostro, o aparece uno desconocido, suslik puede
avisarte directamente: Pushover, Telegram o MQTT para tu domótica. En la
página Notificaciones eliges qué se envía y adónde. Estos avisos son
propios de suslik y funcionan con total independencia de Frigate; Frigate
no necesita ninguna configuración de notificaciones.</p>""",
    "hilfe.gesicht.satz6": """<p><b>Gestionar personas</b> muestra a todas las personas que el sistema
conoce y te deja poner orden. <b>Registrar rostro</b> inicia un
aprendizaje para alguien nuevo.</p>""",
    "hilfe.koerper.titel": "El reconocimiento corporal, explicado",
    "hilfe.koerper.satz1": """<p>Algunos recorridos nunca muestran un rostro utilizable: la persona
mira hacia otro lado, lleva capucha o está demasiado lejos. El
reconocimiento corporal cubre estos casos. Reconoce a los miembros del
hogar por complexión y postura, con imágenes de la persona entera.</p>""",
    "hilfe.koerper.satz2": """<p>Está hecho exactamente para este caso: no hay rostro utilizable, aun
así quieres saber quién era, y no quieres entregar las imágenes a un modelo
de visión por IA para ello.</p>""",
    "hilfe.koerper.satz3": """<p>Aprende de material que tú apruebas. <b>Registrar cuerpo</b> inicia un
aprendizaje corto para una persona: el sistema recoge imágenes suyas de tus
cámaras, tú revisas el resultado una vez, y a partir de ahí sigue
aprendiendo por sí solo.</p>""",
    "hilfe.koerper.satz4": """<p>Con el interruptor de arriba eliges si se ejecuta y cuándo. <b>Only if
no face</b> significa que se queda quieto salvo que la comprobación del
rostro haya salido vacía. <b>Always</b> significa que comprueba cada
recorrido. Desactivado significa que no se ejecuta nunca.</p>""",
    "hilfe.vision.titel": "La visión por IA, explicada",
    "hilfe.vision.satz1": """<p>La visión por IA es una vía propia de reconocimiento. Muestra las
imágenes de un recorrido a un modelo de imagen y le pregunta a qué persona
registrada se parecen. Puedes usarla como respaldo para los casos
difíciles, o dejar que cargue ella sola con el reconocimiento: puesta en
<b>Always</b>, evalúa cada recorrido por sí misma, aunque no haya ningún
rostro enseñado. Evalúa al final del recorrido, no en directo.</p>""",
    "hilfe.vision.satz2": """<p>Lo que necesita para funcionar: personas registradas con imágenes de
cuerpo entero aprobadas (sus galerías) y un modelo conectado. El modelo
puede ejecutarse en local, en tu propio hardware, o en la nube. Con un
modelo en la nube, recuerda que las imágenes salen de tu casa: lo que con
un modelo local no supone un problema no está permitido sin más con uno en
la nube. Y no elijas los modelos más pequeños; un modelo de tamaño medio
hace bien el trabajo.</p>""",
    "hilfe.vision.satz3": """<p>Lo que usamos nosotros: Qwen 3.5 en el tamaño 9B, y cumple bien, tanto
en local como en la nube. También probamos modelos de Anthropic (Claude),
Google (Gemini) y OpenAI (GPT). Tómalo como probado, no como
recomendación; la lista de modelos de la página Detección de visión marca
los que hemos medido, justo donde eliges.</p>""",
    "hilfe.vision.satz4": """<p>Y no se queda en una comparación: para descartar confusiones, el
recorrido se coteja también con las galerías de las demás personas, en
ambos sentidos. Cada par comparado cuesta dos peticiones, así que un solo
recorrido puede acumular unas cuantas. <b>If needed</b> mantiene pequeña
esa factura: al modelo solo se le pregunta cuando los rostros dejan dudas.
Sin un modelo conectado, la visión simplemente se queda fuera del juego, y
la tarjeta lo dice.</p>""",
    "hilfe.faces_bekannt.titel": "Personas conocidas y registro, explicados",
    "hilfe.faces_bekannt.satz1": """<p>Aquí ves a todas las personas que tu sistema conoce &mdash; toca un
rostro y verás todas las imágenes que hay guardadas detrás.</p>""",
    "hilfe.faces_bekannt.satz2": """<p>A una persona nueva no la enseñas subiendo una foto: se aprende del
material normal de las cámaras. A lo largo del día el sistema recoge
imágenes desde distintos ángulos, tú confirmas quién es, y solo tras esa
comprobación se conserva una imagen.</p>""",
    "hilfe.faces_bekannt.satz3": """<p>Así cada persona reúne una pequeña colección de imágenes reales del
día a día &mdash; justo lo que hace fuerte el reconocimiento, incluso
cuando alguien mira hacia otro lado o lleva gorra.</p>""",
    "hilfe.faces_lernen.titel": "El aprendizaje, explicado",
    "hilfe.faces_lernen.satz1": """<p>Mientras las cámaras funcionan, el sistema sigue recogiendo imágenes
nuevas de las personas que ya conoce. Aquí repasas lo que se ha ido
juntando &mdash; cada pocos días es más que suficiente.</p>""",
    "hilfe.faces_lernen.satz2": """<p>Confirmas, corriges o descartas con un clic; nada se conserva sin
ti.</p>""",
    "hilfe.faces_lernen.satz3": """<p>Cuantas más imágenes buenas tiene una persona, más fiable es su
reconocimiento &mdash; por eso el aprendizaje nunca se detiene del todo,
solo se va espaciando.</p>""",
    "hilfe.faces_unbekannt.titel": "Los visitantes desconocidos, explicados",
    "hilfe.faces_unbekannt.satz1": """<p>Algunas personas aparecen una y otra vez sin que el sistema tenga un
nombre para ellas &mdash; el cartero, un vecino, el jardinero. Aquí el
sistema reúne a estos desconocidos recurrentes y te pregunta: ¿quién
es?</p>""",
    "hilfe.faces_unbekannt.satz2": """<p>Ponles un nombre y a partir de ahí se les reconoce como a todos los
demás. O déjalos como desconocidos a propósito &mdash; eso también es una
decisión, y el sistema no seguirá preguntando.</p>""",
    "hilfe.faces_qualitaet.titel": "La comprobación de calidad, explicada",
    "hilfe.faces_qualitaet.satz1": """<p>Con el tiempo se acumulan muchas imágenes, y no todas ayudan al
reconocimiento &mdash; algunas están borrosas, otras apenas muestran a la
persona, y en el peor de los casos las imágenes de dos personas distintas
se parecen tanto que la confusión está servida.</p>""",
    "hilfe.faces_qualitaet.satz2": """<p>Esta comprobación encuentra esos puntos débiles antes de que te
cuesten un reconocimiento. Recibes indicaciones concretas sobre qué
imágenes mirar &mdash; no se borra nada salvo que lo decidas tú.</p>""",
    # Titel: einzige Stelle mit der Vollform "ejecución de aprendizaje" —
    # der Titel muss allein neben "El aprendizaje, explicado"
    # (faces_lernen) unterscheidbar sein; im Fliesstext danach nur die
    # Tabellen-Kurzform "ejecución" (begriffe_tabellen.md ES).
    "hilfe.faces_lernlauf.titel": "La ejecución de aprendizaje, explicada",
    "hilfe.faces_lernlauf.satz1": """<p>Inicias una ejecución; el sistema vuelve a leer tus grabaciones
recientes y recoge rostros por su cuenta.</p>""",
    "hilfe.faces_lernlauf.satz2":
        "<p>Los ordena en grupos. Un grupo debería ser una persona.</p>",
    "hilfe.faces_lernlauf.satz3": """<p>Pones nombre a cada grupo, o lo saltas. Es el único paso que te
necesita.</p>""",
    "hilfe.faces_lernlauf.satz4": """<p>Las imágenes con nombre se convierten en referencias y cuentan para el
reconocimiento de inmediato. Repite cada pocos días, o deja que la vista
del día vaya completando a las personas conocidas entre medias.</p>""",
    # B9: je Ziel ein GANZER Satz-Schluessel (§4.0). Kopplung: "Rostros"
    # == nav.faces/faces.titel, "Reconocimiento" == nav.erkennung/
    # erkennung.titel, "al aprendizaje" nennt die Lauf-Seite (nav.lernlauf
    # "Aprendizaje") im Satz.
    "hilfe.zurueck.erkennung": "Volver a Reconocimiento",
    "hilfe.zurueck.faces": "Volver a Rostros",
    "hilfe.zurueck.lernlauf": "Volver al aprendizaje",
    # ---- §8.1-Nachzuegler (Stufe 3): Inline-Markup-Prosa der Tranchen ----
    # Tag-Folge, <code>-Inhalte, hrefs und Platzhalter byte-gleich zu
    # en.py. ZITAT-KOPPLUNGEN: <b>Sistema</b> == system.titel; "Sistema →
    # Volver a ejecutar el asistente inicial" == system.titel +
    # konfiguration.knopf_setup; "Detección de visión" == nav.vision;
    # "pregunta personalizada" == visiontest.vision.custom_prompt;
    # "sin probar aquí" == vision.modell.ungetestet; "no encaja" ==
    # visionwizard.zelle.knopf_weg; "Estado del modelo" ==
    # nav.person_modell; "Aprendizaje de persona" == nav.personlauf;
    # "Imágenes de cuerpo entero" == nav.person; "Configuración &rarr;
    # Avanzado" == nav.bereich.configuration + nav.konfiguration.
    # "Check the key"/"Check the connection" zitieren den noch englischen
    # Pruef-Knopf (routes/vision.py:_verbindung, Anzeige==Kennung §8.2).
    # Ebenso ENGLISCH zitiert (Muttersprachler-QS 20.08., am Code geprueft):
    # "residents"/"strangers" in vision.modell.antwort_satz — der Badge-Text
    # wird in core/registry.py:632 als hartes englisches Literal gebaut
    # ("residents ✓ 6/6 · strangers ✗ 3/6", kein t()) und in
    # routes/vision.py:401/430 unveraendert gerendert. Anzeige==Kennung
    # (§8.2), also zitiert der Satz die Etiketten so, wie sie auf der Seite
    # stehen — sonst zeigt die Erklaerung Woerter, die die UI nirgends fuehrt.
    "setupwiz.backend.system_satz":
        "Si el acelerador entra de verdad lo ves con el sistema en marcha, "
        "en la página <b>Sistema</b>, tras el arranque (suslik nunca pasa "
        "a la CPU en silencio, sin decirlo).",
    "setupwiz.fertig.wieder_satz":
        "Puedes lanzar este asistente otra vez cuando quieras desde "
        "<b>Sistema → Volver a ejecutar el asistente inicial</b>.",
    "system.sync.diagnose_satz":
        "Si una sincronización informa de un problema, "
        '<a href="/sync_diagnose" target="_blank">abre el diagnóstico</a> '
        "— reúne el informe de suslik y el registro de Frigate, listos "
        "para copiar en una issue.",
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">abre el diagnóstico</a> '
        "— reúne el informe de suslik y el registro de Frigate.",
    "vision.kopf.einleitung":
        "Una tercera vía de reconocimiento junto al rostro y el cuerpo: un "
        "modelo de visión y lenguaje mira una imagen de un recorrido y "
        "dice cuál de tus personas conocidas aparece en ella &mdash; "
        "comparándola con una pequeña galería de esa persona. Es una "
        "<b>voz adicional</b>, nunca el portero: la elección forzada "
        "responde «A o B», así que puede confirmar a un residente, pero "
        "no puede rechazar a un extraño. Eso sigue siendo tarea del "
        "reconocimiento existente.",
    "vision.hinweis.modell_satz":
        "Un modelo de visión que pueda mirar varias imágenes a la vez. "
        "Puedes usar uno de los proveedores en línea de abajo, o ejecutar "
        "uno tú mismo &mdash; la combinación medida aquí es "
        "<b>llama.cpp</b> con un modelo de visión <b>Qwen3.5</b> (el 4B es "
        "tan bueno como el 9B en esta tarea y necesita más o menos la "
        "mitad de memoria). <b>No</b> tiene que ejecutarse en esta "
        "máquina.",
    "vision.hinweis.host_satz":
        "<b>Este host suele quedarse pequeño para un modelo local.</b> El "
        "9B necesita unos 12 GB de working set, el 4B unos 6,6 GB, y aquí "
        "ya viven suslik y el worker de análisis &mdash; el worker es lo "
        "primero que el kernel mata cuando se acaba la memoria. Una "
        "segunda máquina, o un proveedor en línea, es la opción sensata.",
    "vision.hinweis.mess_satz":
        "Una advertencia sobre cómo medir esa memoria: <code>docker "
        "stats</code> muestra unos 2,7 GiB para el contenedor del modelo "
        "porque los pesos están mapeados, no copiados. El working set real "
        "es de ~11,6 GiB. Si dimensionas <code>--memory</code> por lo que "
        "dice <code>docker stats</code>, el modelo recarga sus pesos "
        "continuamente y todo se arrastra.",
    "vision.hinweis.kosten_satz":
        "Velocidad y coste, medidos, para que nada te sorprenda después: "
        "el recorrido entero entra como <b>una sola cuadrícula de "
        "candidatos</b>, y cada <b>par de galerías comparado cuesta dos "
        "peticiones</b> (la misma pregunta se hace otra vez con las dos "
        "galerías intercambiadas, para cazar un sesgo de posición). "
        "Normalmente un par lo zanja. En una máquina de clase CPU eso son "
        "unos 7 minutos por par; en los endpoints en línea medidos aquí, "
        "segundos.",
    "vision.verb.key_ort":
        "<b>Pon la clave en el campo de la clave, no en la URL</b>: un "
        "endpoint que lleva credenciales en su dirección &mdash; delante "
        "del nombre del host, o como parámetro de consulta &mdash; "
        "contiene el mismo secreto, y aparece en muchos más sitios "
        "(estado, registro, copia de seguridad).",
    "vision.modell.leer_key":
        "Todavía no hay nada que elegir. Introduce tu clave arriba y pulsa "
        "<b>Check the key</b>: suslik se conecta al endpoint, pregunta qué "
        "hay y te muestra lo que ha encontrado. Tú eliges de esa lista.",
    "vision.modell.leer_verbindung":
        "Todavía no hay nada que elegir. Rellena los campos de arriba y "
        "pulsa <b>Check the connection</b>: suslik se conecta al endpoint, "
        "pregunta qué hay y te muestra lo que ha encontrado. Tú eliges de "
        "esa lista.",
    "vision.modell.antwort_satz":
        "Esto es lo que respondió el endpoint cuando suslik le preguntó, "
        "{zeit} &mdash; nada de esto es una sugerencia nuestra. Donde "
        "hemos medido un modelo, la nota está en ese modelo. Se muestran "
        "dos capacidades por separado, porque van cada una por su lado: "
        "<b>residents</b> es elegir a la correcta de dos personas "
        "conocidas, <b>strangers</b> es responder «ninguno de los dos» "
        "ante alguien que nunca le has enseñado. Una marca de "
        "verificación significa que todos los veredictos de ese tipo en "
        "nuestra medición fueron correctos; la fracción de al lado lo "
        "cuenta todo. Los modelos sin medición aquí dicen <b>sin probar "
        "aquí</b> &mdash; eso no es un veredicto, solo honestidad "
        "(mediciones de {stand}).",
    "vision.prompt.eigen_satz":
        "Esta es tu propia formulación &mdash; los veredictos emitidos "
        "con ella se marcan como <b>pregunta personalizada</b>. "
        "Restablécela para volver a la formulación por defecto, la que "
        "hemos medido.",
    "vision.cloud.sendet_satz":
        "Esto envía imágenes de personas tomadas por tus cámaras a "
        '<b class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Tres pasos, porque un simple ping de disponibilidad no basta: un "
        "backend estaba accesible, tenía el modelo y respondía rápido "
        "&mdash; y aun así falló 5 de 12 preguntas de comparación, porque "
        "encogía las imágenes antes de mirarlas.<br><b>1</b> "
        "disponibilidad, modelo y tiempo de respuesta, con una imagen de "
        "prueba generada en el momento.<br><b>2</b> una ronda de elección "
        "forzada sobre cuadrículas de formas generadas donde la respuesta "
        "correcta se conoce &mdash; esto comprueba el formato de "
        "respuesta, el analizador y el interruptor de "
        "razonamiento.<br><b>3</b> un recuento de tokens frente a una "
        "referencia medida, que es donde se delata el encogimiento de "
        "imágenes.<br><b>Para esto no se usa "
        "ninguna imagen de una persona</b>, y no existe la opción de "
        "hacerlo.",
    "visiontest.kopf.wege_satz":
        "Elige un recorrido real y mira qué hacen con él las tres vías de "
        "reconocimiento, lado a lado: <b>rostro</b>, <b>persona</b> y "
        "<b>visión</b>.",
    "visiontest.vision.einrichten_satz":
        'Configúrala en <a href="/vision">Detección de visión</a>: un '
        "modelo, una prueba de conexión en verde y al menos dos galerías "
        "aprobadas. Las otras dos columnas funcionan sin ella.",
    "visionwizard.groesse.satz":
        "Medido, con honestidad: el tamaño <b>no</b> fue la palanca en "
        "ninguno de los casos que ejecutamos &mdash; una cuadrícula más "
        "grande no mejoró las respuestas, y tampoco las empeoró. Toma la "
        "mayor si tu material la sostiene (aquí: {empfehlung}), la menor "
        "si no. Las dos cuestan más o menos lo "
        "mismo, porque lo que cuesta tokens es el lienzo, no el número de "
        "celdas.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Olvídalas</a> '
        "si quieres empezar de cero.",
    "visionwizard.vorschlag.satz":
        "Una fila por vista: frontal, lateral, posterior. Las imágenes se "
        "eligen por tamaño y nitidez, por lo claros que se ven los ojos y "
        "la nariz, por cuántas luces están quemadas, por cuánto del "
        "recorte es de verdad la persona &mdash; y repartidas entre días, "
        "eventos y cámaras distintos. La línea bajo cada imagen dice qué "
        "se midió en ella. Pulsa <b>no encaja</b> en lo que no sirva "
        "&mdash; asciende la siguiente mejor imagen de la MISMA vista. "
        "Esto no toca tu material de aprendizaje; solo dice «no como "
        "celda de galería».",
    "personwizard.kopf.stark_satz":
        "<b>Qué hace fuerte al modelo:</b> la variedad gana al volumen. "
        "Las imágenes de <b>muchos días distintos</b> (ropa, luz, "
        "cámaras) ayudan mucho más que muchas imágenes de un solo "
        "recorrido — vuelve a lanzar la extracción en días nuevos antes "
        "que exprimir más un mismo día. Las imágenes confirmadas de "
        "extraños afinan el umbral de decisión de la misma manera.",
    "personwizard.fertig.training_satz":
        "El entrenamiento con el material aprobado empieza "
        "automáticamente tras la revisión — mira "
        '<a href="/person/modell">Estado del modelo</a>. Abajo puedes '
        "iniciar otra ejecución cuando quieras.",
    "personwizard.kontrolle.schalter_satz":
        'El interruptor está en <a href="/konfiguration">Configuración '
        "&rarr; Avanzado</a>, clave <code>diagnostic_collection</code>. "
        "Las imágenes y su registro caducan junto con el registro de "
        "aciertos a los 30 días &mdash; nada de esto se conserva más "
        "tiempo que el propio historial de reconocimiento.",
    "personwizard.kontrolle.leer_satz":
        "Las entradas aparecen en cuanto el reconocimiento corporal esté "
        'activado en <a href="/person/modell">Estado del modelo</a> y una '
        "persona haga un recorrido.",
    "personwizard.bestand.leer_satz":
        'Lanza <a href="/personlauf">Aprendizaje de persona</a> y termina '
        "la revisión — las imágenes aprobadas aparecen aquí.",
    "personwizard.bestand.stark_satz":
        "La variedad gana al volumen: las imágenes de <b>muchos días "
        "distintos</b> (ropa, luz) ayudan mucho más que muchas imágenes "
        "de un solo recorrido. Busca varios días por persona y deja que "
        "la extracción cubra todas tus cámaras.",
    "personwizard.bestand.fremd_satz":
        "<b>Extraños:</b> {n} imágenes confirmadas de extraños calibran "
        "el umbral de decisión — cuantos más extraños haya visto el "
        "modelo, más fiable es esa línea. (Se recogen en "
        "<code>personlern/fremd/</code>; está prevista una página para "
        "ampliar este conjunto con el tráfico de tu propia calle.)",
    "personwizard.bestand.fremd_erklaerung":
        "Imágenes confirmadas de extraños — entrenan la clase adicional y "
        "calibran el umbral de decisión. Borrar una reentrena el modelo "
        "al momento (los archivos viven en <code>personlern/fremd/</code>).",
    "personwizard.modell.leer_satz":
        'Lanza <a href="/personlauf">Aprendizaje de persona</a> y termina '
        "una revisión — después el entrenamiento empieza automáticamente.",
    "personwizard.modell.material_satz":
        "Gestiona las imágenes en "
        '<a href="/person">Imágenes de cuerpo entero</a> — los borrados '
        "reentrenan el modelo automáticamente.",
    # ---- Meldetexte (Stufe 4) --------------------------------------------
    # Struktur, Nutzungs-Reihenfolge und die NICHT eingezogenen Gattungen
    # (a)-(d) s. en.py-Abschnittskommentar. Produktnamen (suslik/Frigate/
    # Pushover/Telegram) bleiben wortgleich (§8.6), ebenso die Kennung
    # {wache} (core.livewache.WATCHER_TITEL, "Live watcher").
    #
    # ES-Entscheide dieses Abschnitts:
    #  - GENUS (Begriffs-Tabelle ES, verbindlich): KEIN fester generisch
    #    maskuliner String ueber einem Personennamen — statt „{name}
    #    confirmado" traegt ein neutrales Substantiv die Endung
    #    („identidad confirmada", „reconocimiento por el cuerpo",
    #    „como persona confirmada"). {person}/{name} koennen weiblich sein.
    #  - aviso = alert (nie „alerta"), rostro = face, recorrido = pass,
    #    umbral = bar/threshold, puntuación = score, veredicto = verdict,
    #    „reconocimiento corporal" wortgleich zum Bestand
    #    (erkennung.koerper.titel), NICHT „clasificación corporal".
    #  - ZEITFORM (Muttersprachler-QS 20.08.): frisches Ereignis ->
    #    pretérito perfecto compuesto („no se ha confirmado", „Frigate ha
    #    visto", „no ha podido"). Das indefinido („vio", „pudo") ist im
    #    peninsularen Register die Vergangenheit OHNE Jetzt-Bezug und
    #    liest sich in einer Sekunden alten Push-Meldung falsch.
    #  - „ventanas" wortgleich zum Bestand event.ours_zeile
    #    („aparece en {n} ventanas"); „hallazgos" wie qualitaet/system
    #    („{n} hallazgo(s)") fuer die Waechter-Funde.
    #  - Push-TITEL bleiben kurz; die spanische Form setzt den Doppelpunkt
    #    („suslik: visión") wie meldung.titel.kategorie — „suslik visión"
    #    waere im Spanischen ungrammatisch.
    #  - Roh-Zahlen-Anhaenge: „cos" bleibt als Kurz-Token stehen (Formel-
    #    Klammer), das ausgeschriebene „coseno" nur im Waechter-Anhang wie
    #    im Bestand (benachrichtigungen-Hinweis).
    "meldung.titel.kategorie": "suslik: {wort}",
    "meldung.alert.bestaetigt":
        "{name}: identidad confirmada ({wort}, aparece en {n} ventana(s))",
    # Doppelpunkt statt Raya: der Rahmen meldung.alert.satz setzt schon eine
    # („{kamera} — {urteil}"), zwei Rayas in einem Satz sind im Spanischen
    # unueblich (gilt auch fuer die bruecke_grund-Saetze unten).
    "meldung.alert.keiner_naechster":
        "no se ha confirmado a nadie: el mayor parecido es con {name} "
        "({wort})",
    "meldung.alert.keiner_ohne_gesicht":
        "no se ha confirmado a nadie: sin rostros utilizables",
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate ha visto: {label}. {gesichter}",
    "meldung.alert.gesichter.eins": "{n} rostro en este evento.",
    "meldung.alert.gesichter.viele": "{n} rostros en este evento.",
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    "meldung.person.titel": "suslik: reconocimiento corporal",
    "meldung.person.satz":
        "{name}: reconocimiento por el cuerpo, no por el rostro — {wort}, "
        "{n} eventos de apoyo",
    "meldung.person.wort_ersatz": "coincidencia",
    "meldung.person.zahl": "[puntuación {score}]",
    "meldung.vision.titel": "suslik: visión",
    "meldung.vision.unbestaetigt":
        "la visión no ha podido confirmar a nadie en este recorrido",
    "meldung.vision.koerper_zusatz":
        "— el reconocimiento corporal apuntaba a {namen}",
    "meldung.vision.bilder_zusatz": "({n} imagen(es) en la cuadrícula)",
    "meldung.vision.einig":
        "visión: {name} — por unanimidad, {voten} de {bilder} "
        "comparación(es)",
    "meldung.vision.kein_urteil": "visión: sin veredicto — {grund}",
    "meldung.wache.titel_person": "{wache} {kamera}: persona detectada",
    "meldung.wache.titel_stoerung": "{wache} {kamera}: incidencia",
    "meldung.wache.caption": "{wache} {kamera}: {text}",
    "meldung.wache.name_satz":
        "reconocimiento (en directo, provisional): {name} ({wort}, {n} "
        "hallazgos consistentes)",
    "meldung.wache.name_zahl": "[coseno {cos}]",
    "meldung.wache.funde.eins": "{n} rostro en {sek} s",
    "meldung.wache.funde.viele": "{n} rostros en {sek} s",
    "meldung.wache.funde_zahl": "(puntuación {score}, {ms} ms)",
    "meldung.video_ersatz.satz":
        "(vídeo no disponible — se envía una imagen)",
    "meldung.test.satz": "Aviso de prueba de suslik ✓",
    # ---- D1: ehrliche Begruendung der Pass-Pruefung ----------------------
    # Anlass + Bauform s. en.py. SATZTEILE (kleines Anfangswort): sie haengen
    # hinter „nada que tomar — " oder hinter dem Grenzfall-Satz; die
    # Kennung->Satz-Wahl trifft webui.bausteine.bruecke_grund, die Zahlen
    # kommen fertig aus anlernen.vorschlaege_person (KEINE Schwelle als
    # Literal, nur ihr Platzhalter). Klammerplurale „rostro(s)"/
    # „imagen(es)"/„evento(s)" wie im ES-Bestand (§8.18). {person} steht nie
    # mit einem festen maskulinen Partizip (Genus-Regel).
    # SCHWELLEN-WORTLAUT (Muttersprachler-QS 20.08.): „hacen falta {…}" statt
    # „el mínimo es {…}" — neben „el mayor mide {kante} px" liest sich „el
    # mínimo" als zweiter Superlativ ueber DENSELBEN gemessenen Rostros und
    # widerspricht der Zahl davor; „hacen falta" sagt eindeutig: gefordert.
    "antwort.bruecke_nichts_grund": "nada que tomar — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    "antwort.bruecke_grund_zu_klein":
        "los {n} rostro(s) medido(s) en este recorrido son todos demasiado "
        "pequeños: el mayor mide {kante} px, hacen falta {min_kante} px",
    "antwort.bruecke_grund_zu_unscharf":
        "{n} rostro(s) de este recorrido están demasiado borroso(s) para "
        "servir de referencia: la mejor nitidez es {sharp}, hacen falta "
        "{unscharf_max}",
    "antwort.bruecke_grund_kein_gesicht":
        "ningún rostro medible en las {n} imagen(es) comprobada(s) de este "
        "recorrido",
    "antwort.bruecke_grund_gedeckt":
        "{n} de los rostro(s) comprobado(s) son casi idénticos a "
        "referencias que {person} ya tiene",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} de los rostro(s) comprobado(s) se parecen más a otra persona "
        "que a {person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} de los rostro(s) comprobado(s) no eran claramente {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} de los rostro(s) comprobado(s) eran débiles en los dos "
        "aspectos: calidad de imagen e identidad",
    "antwort.bruecke_grund_kein_crop":
        "ninguno de los {n} evento(s) de este recorrido tiene un recorte de "
        "rostro que comprobar",
    "antwort.bruecke_grund_keine_events":
        "en ningún evento de este recorrido aparece {person} como persona "
        "confirmada ni como mejor coincidencia",
    "antwort.bruecke_grund_keine_referenzen":
        "{person} aún no tiene imágenes de referencia con las que comparar",
    # ---- personlauf-Design (Nachzug) ----
    # Kachel-Titel und Kachel-Saetze des /personlauf-Laufflusses. Kachel 1/4,
    # die erste Saeulen-Marke und die Nachbar-Beschriftungen kommen wortgleich
    # aus dem Gesichts-Lernlauf (lernwizard.*) — hier stehen nur die sieben
    # personwizard-eigenen Neuzugaenge.
    "personwizard.kachel.sammeln": "Extraer imágenes",
    "personwizard.kachel.pruefen": "Revisar las imágenes",
    "personwizard.k1.satz":
        "Elige a quién aprender a reconocer y cuánto repasar hacia atrás "
        "&mdash; después la ejecución extrae las imágenes de tus propias "
        "grabaciones.",
    "personwizard.k2.satz":
        "Extrae imágenes de cuerpo entero de tus grabaciones, y solo de "
        "recorridos que ya haya confirmado un rostro.",
    "personwizard.k3.satz":
        "El paso que te necesita: cada imagen extraída recibe tu sí o tu "
        "no antes de que se aprenda nada.",
    "personwizard.k4.satz":
        "Las imágenes aprobadas entrenan el modelo corporal enseguida "
        "&mdash; así puede reconocer a personas aunque no se vea ningún "
        "rostro.",
    "personwizard.such.titel": "Configurar un aprendizaje de persona",
}
