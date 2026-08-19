"""Zentrale Quelle der Release-Highlights fuer die What's-new-Box im UI (Task #16).

INHALTS-REGEL (User-Vorgabe 01.08.): NUR Key-Features, und der Inhalt wird vor
JEDEM Release MIT dem User abgestimmt — nie selbststaendig fuellen
(Memory whatsnew-inhalt-abstimmen; Runbook-Stufe-0-Halt). K3-Regel: die Box
liest AUSSCHLIESSLICH diese Liste. Das Gate prueft, dass der neueste Eintrag
der VERSION entspricht. Import-frei wie core/registry.py.

Stand .101 (User-Entscheid 01.08.): GENAU zwei Punkte — Learn-Modul und Areas."""

# STAND = bis zu welcher VERSION der Box-Inhalt MIT dem User abgestimmt ist (das Gate
# prueft STAND == VERSION). NICHT jede Version bekommt einen Eintrag (User 02.08.:
# .104/.105 nur ins CHANGELOG) — ein Release ohne Box-Aenderung zieht NUR STAND hoch,
# die Box erscheint dann nicht neu. Eintraege bleiben Key-Features-only.
STAND = "0.1.0.298"   # .298 = Release-Stand (User 19.08. abends): die zwei ABGESTIMMTEN
                      # Punkte — Absturz-Fix (Wortlaut vom User diktiert, FIX) +
                      # Mehrsprachigkeit (EN-Wortlaut vom User abgenommen). Seit .298
                      # sind Eintraege MEHRSPRACHIG (§6.3): dict {en,de,es,it,fr
                      # [,betont]}, Alt-Eintraege bleiben str (= nur englisch);
                      # webui.whatsnew_block kann beides, das Gate prueft beide Formen.
                      # Davor .297 = Sprach-Stufe 1 (Sprachschalter live; kein
                      # Box-Eintrag).
                      # Davor .296 = Sprach-Stufe 0 komplett (alle 16 Anzeige-Routen lesen ihre
                      # Texte aus core/texte/en.py, byte-gleich bewiesen) + Recognized-
                      # live-Karten im Grid (kein Box-Eintrag).
                      # Davor .295 = verworfene Gruppen unsichtbar im Streifen (Sammelzeile), Zaehler ehrlich
                      # (kein Box-Eintrag).
                      # Davor .290 = Erzeugungs-Modus auch im ANALYZE-Weg — der
                      # Nachhol-Backlog alter Events leakte sonst weiter
                      # (Realbeleg 20:26 e16pp1); dazu settimeout-Griff
                      # gehaertet (kein Box-Eintrag).
                      # Davor .289 = Erzeugungs-Aufbau-Timeout
                      # (Haertungstest-Fang; kein Box-Eintrag).
                      # Davor .288 = Ernte-Haertung nach Leak-Beweis (Task #11,
                      # Serie E): Erzeugungs-Modus fuer Alt-Clips (Probe-
                      # Warte statt Leak-Abbruch), Vorlader-Serialisierung,
                      # Nachhol ohne clip.mp4-HEAD (kein Box-Eintrag).
                      # Davor .287 = Clip-Debug-Trace [clipdbg] hinter dem
                      # debug-Schalter (Frigate-Haenger-Beweissicherung,
                      # Task #11; kein Box-Eintrag).
                      # Davor .286 = RELEASE-Respin 2 (S9: Expert-Tabelle
                      # /qualitaet scrollt statt 785-px-Ueberlauf auf
                      # Handy-Breiten; Box-Text UNVERAENDERT). .285 ging nie raus.
                      # Davor .285 = Respin 1 (Betreiber-Genitiv in 2 Alt-
                      # Kommentaren, Image-Audit-Fang; Box-Text UNVERAENDERT).
                      # .284 ging nie raus.
                      # Davor .283 = Probe raeumt Fehler auch ohne Sperre
                      # (kein Box-Eintrag).
                      # Davor .282 = Galerie ohne Auto-Refresh, lauter qsStart
                      # (kein Box-Eintrag).
                      # Davor .281 = Banner-Entwarnung + Schoner-Probe-Loop
                      # (kein Box-Eintrag).
                      # Davor .280 = Kachel-Knoepfe oben, Galerie ersetzt
                      # Alt-Tabs (kein Box-Eintrag).
                      # Davor .279 = Galerie-Reiter + Faces-Kurztexte
                      # (kein Box-Eintrag).
                      # Davor .255 = Lernlauf-Feinschliff (Neulern-Schalter in der
                      # Kachel, Erklaer-Satz weg; kein Box-Eintrag).
                      # Davor .254 = Learn zurueck als Hauptmenue-Punkt (User-Wunsch;
                      # Startseite = neuer Lernfluss; kein Box-Eintrag).
                      # Davor .253 = HOTFIX /live-NameError (Lastzeile-Parameter
                      # erreichte _engine_karte nicht; Gate-Stufe ergaenzt).
                      # Davor .252 = CPU-Modus: Empfehlung statt Verbot (User-
                      # Entscheid; Warnungen, Lastzeile, Label-Fix).
                      # Davor .251 = Feinschliff (M6 Anwesenheits-Push: Score/Latenz
                      # nur noch im Zahlen-Stil; kein Box-Eintrag).
                      # Davor .250 = Feinschliff (Event-Zeile: no-match-Schwanz
                      # gezaehlt statt aufgezaehlt; kein Box-Eintrag).
                      # Davor .249 = interner Stand (Kosinus-raus Haeppchen 1:
                      # Wortstufen core/vertrauen in Meldetexten M1-M6,
                      # MQTT-stufe additiv, alert_stil-Option; Box unveraendert).
                      # Davor .248 = interner Fix (Quelltest nutzt guard.hoehe statt
                      # stur Default — Fund beim CPU-Setup; kein Box-Eintrag).
                      # Davor .247 = interner Stand (CPU-Runde: Live auf der cpu-
                      # Variante BEGRENZT erlaubt, 1 Waechter, ehrliche
                      # 1-2-s-Erwartung — User-Go nach Messung 17.08.).
                      # Davor .246 = interner Prod-Stand (Lernfluss-Redesign: Vier-
                      # Kachel-Fluss + Saeule + Zuweisungs-Flaeche), Box
                      # unveraendert. Davor .245 = Live-Journal ohne Meldekanal,
                      # .244 = Lernlauf-Lauf-Seite Teil 1+2.
                      # Davor: .243 = RELEASE (zweiter Respin: das Export-Gate fand
# nach dem Anlegen neuer Identitaeten weitere Namen in vier Alt-Kommentaren —
# mehrteilige Ordnernamen fielen aus der Audit-Namensliste, Audit um
# Segment-Zerlegung ergaenzt; die schon gepushten .242-Tags werden von GHCR
# entfernt. Davor .242 = Respin von .241: Bewohnername in drei Kommentaren +
# CHANGELOG-Beispiel. Box-Text durch beide Respins UNVERAENDERT; .241/.242
# gingen nie als Release raus).
# Box-Eintrag vom User diktiert: Zwischenversion, Vereinfachung/Klarheit,
# Feedback-Appell.
# Davor .240 = interner Prod-Schritt (Change-connection als
# Inline-Form — kein Box-Eintrag).
# Davor .239 = interner Prod-Schritt (Unbekannt-Klick = EIN Lauf,
# dritte Fassung — kein Box-Eintrag).
# Davor .238 = interner Prod-Schritt (Unbekannt-Sicht: Gruppen-
# Zusammenfuehrung + Layout-Paritaet — kein Box-Eintrag).
# Davor .237 = interner Prod-Schritt (Unbekannt-Tagessicht mit
# Zuweisen — kein Box-Eintrag).
# Davor .236 = interner Fix (refcache-Einpflege statt Verwerfen
# — kein Box-Eintrag).
# Davor .235 = interner Fix (Bruecke auf svc.embedder/OV
# — kein Box-Eintrag).
# Davor .234 = interner Prod-Schritt (Unbekannt-Karte = Link,
# EIN Klick-Gesetz — kein Box-Eintrag).
# Davor .233 = interner Prod-Schritt (Pass-Knopf-Optik mit Icons
# — kein Box-Eintrag).
# Davor .232 = interner Prod-Schritt (Vorwaermen+Leerlauf-Freigabe
# +Lade-Anzeige — kein Box-Eintrag).
# Davor .231 = interner Prod-Schritt (Grenzfaelle im Overlay,
# ehrliche Meldung — kein Box-Eintrag).
# Davor .230 = interner Fix (Embedder-Cache fuer Vorschlags-/
# Bruecken-Strecke — kein Box-Eintrag).
# Davor .229 = interner Prod-Schritt (Legende am gruenen Rand
# — kein Box-Eintrag).
# Davor .228 = interner Fix (eid ueberlebt refs_meta-Neuzeilen
# — kein Box-Eintrag).
# Davor .227 = interner Prod-Schritt (Referenz-Marker an den
# Thumbs — kein Box-Eintrag).
# Davor .226 = interner Prod-Schritt (Lern-Bruecke zweistufig
# mit Auswahl-Overlay — kein Box-Eintrag).
# Davor .225 = interner Prod-Schritt (Lern-Bruecke je Pass
# — kein Box-Eintrag).
# Davor .224 = interner Prod-Schritt (Benennungs-Karte mit
# Weiter-Automatik — kein Box-Eintrag).
# Davor .223 = interner Prod-Schritt (Lernlauf als gefuehrter
# Fluss — kein Box-Eintrag).
# Davor .222 = interner Prod-Schritt (Areas in die
# Property-set-up-Reihe der Configuration — kein Box-Eintrag).
# Davor .221 = interner Prod-Schritt (Faces-Anleitungen,
# Frigate-Feinschliff, Namens-Fix — kein Box-Eintrag).
# Davor .220 = interner Prod-Schritt (Faces-Startseite,
# People+Learn eingedampft — Box-Eintrag erst beim Release mit User-Abstimmung).
# Davor .219 = interner Prod-Schritt (Beta-Marke AI-vision-Kachel
# — kein Box-Eintrag).
# Davor .218 = interner Fix (Bewohnernamen aus .217-Kommentaren,
# Gate-Fang — kein Box-Eintrag).
# Davor .217 = interner Prod-Schritt (Vision-Diagnose-Paket V1-V3
# — kein Box-Eintrag).
# Davor .216 = interner Prod-Schritt (Frigate-Kachel-Startseite,
# Nav "Frigate sync" -> "Frigate" — Box-Eintrag erst beim Release mit User-Abstimmung).
# Davor .215 = interner Fix (Probe ohne Urteils-Anhang, roh=True —
# kein Box-Eintrag).
# Davor .214 = interner Fix (Probe-Deckel 512 — kein Box-Eintrag).
# Davor .213 = interner Prod-Schritt (Vision-Modell-ID von
# Hand eintragen, real am Endpunkt geprueft — kein Box-Eintrag).
# Davor .212 = interner Prod-Schritt (Hilfe-Links deutlich
# hervorgehoben — kein Box-Eintrag).
# Davor .211 = interner Prod-Schritt (think_aus Default AN fuer
# custom/lokal nach dem Token-Befund — kein Box-Eintrag).
# Davor .210 = interner Prod-Schritt (Reiter Configuration statt
# Settings, Ungespeichert-Warnung auf /erkennung — kein Box-Eintrag).
# Davor .209 = interner Prod-Schritt (Anleitungs-Feinschliff
# nach der Erst-Lektuere des Users — kein Box-Eintrag).
# Davor .208 = interner Prod-Schritt (In-progress-Hinweis in der
# Recognized-Zeile von /heute, Register-Knoepfe, Anleitungen — kein Box-Eintrag).
# Davor .207 = interner Prod-Schritt (/erkennung wird Settings-
# Startseite, Unterreiter nur-expert; Face-Zaehler-Fix — kein Box-Eintrag).
# Davor .206 = interner Prod-Schritt (Fix /erkennung-Crash +
# neue Gate-Stufe Seiten-Sweep im Image — kein Box-Eintrag).
# Davor .205 = interner Prod-Schritt (Vier-Saeulen-Seite
# /erkennung, erste Easy/Expert-Seite — Box-Eintrag kommt ERST mit dem Release
# und wird wie immer mit dem User abgestimmt).
# Davor .204 = interner Prod-Schritt (Easy/Expert-Schalter in der
# Kopfzeile, nur der Schalter — Box-Eintrag kommt ERST mit dem Release und wird
# wie immer mit dem User abgestimmt).
# Davor .203 = interner Prod-Schritt (Person-Backbone dinov2 ->
# Intel OMZ 0277 mit Selbst-Migration + person_backend-Schalter — Box-Eintrag
# kommt ERST mit dem Release und wird wie immer mit dem User abgestimmt).
# Davor .202 = interner Prod-Schritt (P1 Speicher-Redesign:
# personwork-Prozess, Budget-Gate scharf, Wellen als Schlange — Box-Eintrag
# kommt ERST mit dem Release und wird wie immer mit dem User abgestimmt).
# Davor .201 = interner Prod-Schritt: basis_url/Push-Link aus
# .200 wieder ENTFERNT (User-Entscheid 14.08.: erdachtes Personas-Beduerfnis, kein
# realer Nutzerwunsch), kein Box-Eintrag.
# Davor .200 = interner Prod-Schritt (Fix-Runde aus dem
# Usersicht-Review 14.08.: Save-400 frische Installation, Kategorien wirken
# auf alle Kanaele, Waechter-Kanal-Default aus konfigurierten Kanaelen,
# Pushover-Link in die UI, fuenf veraltete Texte, /live_alerts in der Nav),
# kein Box-Eintrag.
# Davor .199 = RELEASE (Buendel .184-.198), Box-Eintraege vom
# User diktiert + abgestimmt (13.08. ~18:20 "das passt").
# Davor .198 = Fix des .197-Start-Absturzes (livewached las den
# abgeschafften Haken; referenzen_noetig + S10-Drift-Wache), kein Box-Eintrag.
# Davor .197 = interner Prod-Schritt (Quick-verdict-Haken weg:
# jeder enabled-Waechter erkennt Namen; live_speichern Felder-Fix: fehlende
# Felder behalten Gespeichertes), kein Box-Eintrag.
# Davor .196 = interner Prod-Schritt (Vereinfachungs-Schnitt:
# Slot-Vergabe ohne Lastmodell — enabled = laeuft, Notbremsen nur harter
# Deckel + RAM-Boden; Ueberlast regelt die Drossel; Quelltest misst echte
# Lieferrate), kein Box-Eintrag.
# Davor .195 = interner Prod-Schritt (Auftritts-Sicht der Live-
# Alerts: Tagesansicht + Today-Karten zeigen je Auftritt ALLE Gesichts-Crops
# + Rueckblick-Videos, analog der Pass-Ansicht; Slot-Riegel rechnet mit der
# gemessenen Lieferrate statt Test-Durchsatz), kein Box-Eintrag.
# Davor .194 = interner Prod-Schritt (Verarbeitungshoehe je Kachel
# 360-2160, Default 1080; Beweisbild-Klick an Live-Karten), kein Box-Eintrag.
# Davor .193 = interner Prod-Schritt (kontinuierliches Namens-Voting:
# Stufe-2-Namens-Meldung nach NAME_STIMMEN konsistenten Treffern je Auftritt),
# kein Box-Eintrag.
# Davor .192 = interner Prod-Schritt (/live_alerts Tagesuebersicht
# aller Trigger als Klickziel der Sidebar-Zeile), kein Box-Eintrag.
# Davor .191 = interner Prod-Schritt (Recognized live zeigt NUR
# erkannte Trigger — unknown erschlaegt die Reihe nicht mehr), kein Box-Eintrag.
# Davor .190 = interner Prod-Schritt (Recognized-live-Kartenreihe
# auf Today mit Beweisbild + Schnell-Urteils-Name), KEIN Box-Eintrag.
# Davor .189 = interner Prod-Schritt (Recognition chain als vierter
# Settings-Menuepunkt, eigenes Blatt /kette), KEIN Box-Eintrag.
# Davor .188 = interner Prod-Schritt (Today zeigt Live-Alerts als
# separate Liste mit Meldetext), KEIN Box-Eintrag.
# Davor .187 = interner Prod-Schritt (Recognition-chain-Sektion in
# Settings, ersetzt die zwei generischen Dropdowns), KEIN Box-Eintrag.
# Davor .186 = interner Prod-Schritt (Zustands-Gruppen + Hide +
# Stream-Steckbrief-Probe + Area-Schalter im Live-Reiter), KEIN Box-Eintrag.
# Davor .185 = interner Prod-Schritt (Kachel-Vorschau + echte
# Kopf-Aufloesung im Live-Reiter), KEIN Box-Eintrag ohne Abstimmung.
# Davor .184 = interner Prod-Schritt (umask-022-Fix, Backup-
# Klasse root:600), KEIN Box-Eintrag — Box bleibt auf dem .183-Stand.
# BOX-DIKTAT fuers NAECHSTE Release (User 13.08. ~11:45, ERWEITERT ~14:15;
# vor dem Release nochmal bestaetigen lassen). Kern und WICHTIGSTER Punkt:
# der Appell um Rueckmeldung. Sinngemaess: Entwickeln macht Spass, aber es
# kommt viel zu wenig Rueckmeldung — ohne sie weiss der Autor nicht, ob das
# Gebaute wirklich Bedarf trifft und gewuenscht ist; die Downloads sieht er,
# Rueckmeldung fehlt. Positiv WIE negativ erwuenscht. Speziell: zu rocm und
# gpu-legacy kam bisher GAR NICHTS — dabei kann er diese Hardware nicht
# selbst testen und weiss deshalb nicht einmal, ob es funktioniert (gerne
# mit Log melden). Erreichbar auf ZWEI Wegen: suslik_dev@posteo.de und
# GitHub. Dazu: Version 1.0 ist geplant, wenn das so funktioniert.
# Davor: .183 = Live-Release (Respin von .182: Kameranamen-Leck
# in Code-Kommentaren gefixt, Audit-Stufe 8b ergaenzt; Box-Text unveraendert).
# Box-Inhalt vom User DIKTIERT und abgestimmt (12.08. ~22:50 im Chat):
# (1) BETONTER Hinweis ungetestete Zwischenversion/ganzer Live-Part neu,
# (2) die Live-Story mit den gemessenen 199-801 ms. Weitere Kandidaten
# (Unknown-Sichtbarkeit, Topic-Praefix .176) blieben BEWUSST draussen —
# nicht ohne neue Abstimmung ergaenzen.

# HERVORHEBUNG (0.1.0.168): ein Eintrag kann optisch herausstechen — genau EIN
# Fall ist dafuer vorgesehen, der Vorab-Hinweis am Anfang eines Releases. Die
# Markierung ist ein PRAEFIX am Text, kein neues Schema: die Eintraege bleiben
# Strings, damit Gate, Beweis und jeder Leser unveraendert weiterlaufen. Der
# Renderer nimmt das Praefix ab und setzt den Eintrag fett und in Warnfarbe;
# wer die Liste roh liest, sieht die Marke und weiss, was gemeint ist.
BETONT = "!! "
# .139/.140 (Erkennungs-Review Baustein 1, Fremd-Klasse + Schwellen-Eichung)
# bekommen BEWUSST keinen Box-Eintrag: interne Prod-Schritte, kein Release. Der
# Box-Inhalt der naechsten Veroeffentlichung wird wie immer vorher mit dem User
# abgestimmt — hier wird nur STAND nachgezogen, die Box bleibt unveraendert.
# .171 (Vision-Favorit aus Zellen-Stimmen, Analyse-Watchdog + RAM-Gate)
# bekommt BEWUSST keinen Box-Eintrag: interner Prod-Schritt, Box-Inhalt der
# naechsten Veroeffentlichung wird vorher mit dem User abgestimmt — hier wird
# nur STAND nachgezogen, die Box bleibt unveraendert.
# .172 (Tester-Paket: CPU-Thread-Kappung, Analyse-nice, Wanduhr-Serialisierung,
# Ketten-Schalter, In-Job-RSS-Wache, Vision-Stimme, Vision-Seiten-CSS) bekommt
# BEWUSST keinen Box-Eintrag: interner Prod-Schritt, Box-Inhalt der naechsten
# Veroeffentlichung wird vorher mit dem User abgestimmt — nur STAND nachgezogen.

# Neueste zuerst: (version, (eintraege ...)).
HIGHLIGHTS = (
    # .298 — MIT USER ABGESTIMMT (19.08. abends): Punkt 1 Wortlaut vom User
    # diktiert (stand.md What's-new-Kandidaten, "kurz, ohne Frigate-Details");
    # Punkt 2 EN-Wortlaut vom User abgenommen ("Wortlaut ok"). Uebersetzungen
    # laufen durch dieselbe Muttersprachler-QS wie core/texte (Stufe-2-Runde).
    ("0.1.0.298", (
        # User 19.08. spaetabends: Interim-Hinweis wie .286 vorangestellt
        # ("ok incl dem interims hinweis"); Rest-Wortlaut unveraendert diktiert.
        {"en": "Interim release — found and fixed a bug that could cause a "
               "crash of Frigate during very large, long learning runs with many events.",
         "de": "Zwischenversion — einen Fehler gefunden und behoben, der bei sehr großen, "
               "langen Lernläufen mit vielen Events zum Absturz von Frigate führen konnte.",
         "es": "Versión intermedia: encontrado y corregido un fallo que podía provocar un cierre "
               "inesperado de Frigate en ejecuciones de aprendizaje muy grandes y largas "
               "con muchos eventos.",
         "it": "Versione intermedia — trovato e corretto un errore che poteva causare un crash di Frigate "
               "durante sessioni di apprendimento molto grandi e lunghe, "
               "con molti eventi.",
         "fr": "Version intermédiaire — un bug pouvant provoquer un plantage de Frigate lors de sessions "
               "d'apprentissage très longues et de grande ampleur, avec de "
               "nombreux événements, a été trouvé et corrigé."},
        {"en": "suslik now speaks five languages — English, German, Spanish, "
               "Italian and French. Pick yours in the header; pages not yet "
               "translated say so and follow with the next releases.",
         "de": "suslik spricht jetzt fünf Sprachen — Englisch, Deutsch, "
               "Spanisch, Italienisch und Französisch. Wähle deine Sprache "
               "in der Kopfleiste. Noch nicht übersetzte Seiten sagen es "
               "dir; die Übersetzung folgt mit den nächsten Versionen.",
         "es": "suslik ahora habla cinco idiomas: inglés, alemán, español, "
               "italiano y francés. Elige el tuyo en la cabecera; las páginas "
               "aún sin traducir lo indican y llegarán con las próximas "
               "versiones.",
         "it": "suslik ora parla cinque lingue: inglese, tedesco, spagnolo, "
               "italiano e francese. Scegli la tua nell’intestazione; le "
               "pagine non ancora tradotte lo segnalano e arriveranno con le "
               "prossime versioni.",
         "fr": "suslik parle désormais cinq langues : anglais, allemand, "
               "espagnol, italien et français. Choisissez la vôtre dans "
               "l'en-tête ; les pages pas encore traduites l'indiquent et "
               "arriveront avec les prochaines versions."},
    )),
    # .284 — MIT USER ABGESTIMMT (18.08. nachmittags, Inhalt von ihm
    # diktiert: "Zwischenversion; fokussiert an den Lernmoeglichkeiten
    # fuer Gesichter gearbeitet, am Zuweisen, an der Qualitaet der
    # Gesichtserkennung, an der Konfiguration wie man Kameras hinterlegt";
    # drei englische Zeilen im Chat abgenommen: "die zeilen passen").
    ("0.1.0.286", (
        "Interim release — focused work on face learning: guided learning "
        "runs and easier assigning of faces to people.",
        "Picture quality: a one-click check finds weak, duplicate and "
        "mixed-up reference pictures for you.",
        "Clearer camera setup and configuration.",
    )),
    # .243 — MIT USER ABGESTIMMT (16./17.08. nachts, Inhalt von ihm diktiert:
    # "Zwischenversion, Fokus auf Vereinfachung und Klarheit. Mittendrin,
    # Umbau easy/expert, gerne mal auf Config, Today etc. schauen und gerne
    # Rueckmeldung ob ich auf dem richtigen Weg bin per E-Mail" — englische
    # Fassung im Chat bestaetigt, Adresse die oeffentliche posteo.
    # Respin von .241/.242, Text identisch).
    ("0.1.0.243", (
        "Intermediate release — focus on simplification and clarity. We are "
        "mid-way through the Easy/Expert rebuild: have a look at the new "
        "Configuration start page, the Faces area, the Today cards and the "
        "guided learning flow. Honest feedback on whether this direction "
        "feels right is very welcome — suslik_dev@posteo.de.",
    )),
    # .202 — MIT USER ABGESTIMMT (15.08. abends, "go aber nehme ergaenzend
    # mit auf ..."): Speicherfix-Eintrag wie vorgeschlagen + Ausblick
    # Easy/Expert-Mode + Feedback-Mail.
    ("0.1.0.202", (
        BETONT + "Important memory fix — please update. A burst of events "
        "could exhaust memory and freeze the whole service; body recognition "
        "now runs in its own supervised, memory-capped process. If suslik "
        "ever felt sluggish or died on you, this is why.",
        "Next up I'm working on a simpler Easy mode (with an Expert mode "
        "keeping every control) — the current UI simply grew too complex. "
        "Feedback keeps making a real difference and is very welcome: "
        "suslik_dev@posteo.de.",
    )),
    # .199 — User-DIKTAT (13.08. ~11:45, erweitert ~14:15, deutscher Entwurf
    # abgestimmt "das passt" ~18:20): TOP = Feedback-Appell (rocm/gpu-legacy
    # ungetestet, zwei Kontaktwege, 1.0-Plan), dann die fuenf Feature-Kerne
    # des .184-.198-Buendels.
    ("0.1.0.199", (
        BETONT + "A personal note from the author: I can see the downloads, "
        "but I get almost no feedback. Building this is fun — yet without "
        "feedback I don't know whether it actually meets a need. Positive "
        "and negative reports are equally welcome. Especially the rocm and "
        "gpu-legacy variants: not a single report so far, and I cannot test "
        "that hardware myself — I don't even know whether they work (a short "
        "note with a log would be great). If this works out, version 1.0 is "
        "the next step. You can reach me at suslik_dev@posteo.de or on "
        "GitHub.",
        "Recognized live, with a name: watchers now send a preliminary name "
        "verdict seconds after the trigger, with a proof picture — several "
        "people in the same pass are reported individually.",
        "Appearance view: the live day view bundles each pass into one card "
        "with all face pictures and recap videos; Today links straight to "
        "it.",
        "Per-camera processing resolution (360p-2160p, default 1080p) — "
        "measurably faster name recognition than before.",
        "Simpler and predictable: enabled means running — no load model "
        "refuses a watcher anymore, overload is handled by the runtime "
        "throttle; the source test now shows the camera's real delivery "
        "rate.",
        "A tidier Live tab: preview through the agent's eyes, real stream "
        "resolution, grouping by state and area; recognition chain as its "
        "own settings page.",
    )),
    # .183 — User-DIKTAT (12.08. ~22:50, Text im Chat abgestimmt; HALT-Gate
    # dafuer abgegolten): betonter Zwischenversions-Hinweis + Live-Story.
    # (.182 wurde nie als Release beworben — Respin wegen Kameranamen-Leck,
    # der Eintrag wandert mit auf die ausgelieferte Version.)
    ("0.1.0.183", (
        BETONT + "Untested in-between release: the entire live-watcher part "
        "is brand new in this version and has not seen wider testing yet — "
        "expect rough edges and please report what breaks.",
        "Live watchers: pick cameras to watch directly on the live stream — "
        "first face to verified signal in under one second (measured "
        "199-801 ms), e.g. to trigger Home Assistant via MQTT.",
    )),
    # .173 — mit dem User abgestimmt (11.08., Auswahl-Frage + Diktat-Ergaenzung):
    # der BETONTE Test-Release-Hinweis fuer cpu/gpu-legacy plus der Auto-Default;
    # #19/#9/#10 bleiben bewusst nur im CHANGELOG.
    ("0.1.0.173", (
        BETONT + "This build doubles as a test release for small machines: it "
        "ships as version tags for the cpu and gpu-legacy variants, so "
        "low-power boxes and older Intel iGPUs (5th–10th gen Core) can try "
        "it. The recent load cuts — thread caps on every model session, "
        "per-path recognition switches, conservative defaults on weak "
        "hardware — are aimed exactly at that hardware. Feedback welcome.",
        "Weak machines now default themselves: on the first start of this "
        "version every install measures its usable physical cores, and below "
        "the floor the recognition chain and the CPU thread cap are pre-set "
        "conservatively — loud in the start log, explained next to the "
        "settings, and never touching values you set yourself.",
    )),
    # .170 — Release-Eintrag, mit dem User abgestimmt (10.08.): die
    # KI-/Vision-Geschichte bleibt der Kern der Box (.168), .170 traegt NUR den
    # kurzen Fix-Hinweis zur Galerie; der fruehere .169-Block ging darin auf.
    ("0.1.0.170", (
        "Fixes for the gallery comparison: the candidate grid now uses up to "
        "12 cells (matching your reference galleries), the exact grid shown "
        "to the model is saved and visible on the walk-through's page, and "
        "the recognition test shows the face pictures alongside person and "
        "vision.",
    )),
    # .168 — mit dem User abgestimmt (09.08.); der fruehere Betont-Punkt
    # "early working version" wurde am 10.08. auf User-Anweisung ENTFERNT
    # (kein Arbeitsversions-Hinweis mehr in der Box).
    ("0.1.0.168", (
        "Vision detect: a third, independent recognition path — each "
        "walk-through is judged as one candidate grid against your approved "
        "galleries (local llama.cpp or your own API endpoint).",
        "Gallery wizard with automatic curation: proposals are scored on face "
        "visibility, lighting and completeness, with a reason line per cell.",
        "Recognition test: face, person and vision side by side for any past "
        "walk-through, with a live narrative log.",
    )),
    # .138 mit User abgestimmt 06.08. ("go" auf den Zwei-Punkte-Vorschlag).
    ("0.1.0.138", (
        "New \"Frigate sync\" page: a full reconciliation of your reference "
        "library with Frigate — see what is on both sides and what is "
        "missing where, pick exactly which images to send, and get a "
        "per-image result, including Frigate's own reason when it refuses "
        "one. Images you deleted in Frigate become explicit decisions "
        "instead of silent re-uploads.",
        "Sync problems now explain themselves: the export never stops on a "
        "single bad image, a live status line shows whether Frigate's face "
        "recognition is on, and a one-click diagnosis bundles the suslik "
        "report together with Frigate's log — ready to attach to a bug "
        "report.",
    )),
    ("0.1.0.129", (
        "Clean up your learning area: runs can now be deleted completely "
        "— per run or all old ones with a single click. Dismissed "
        "clusters are remembered, so re-harvests of the same events stay "
        "quiet.",
        "\"Looks like\" suggestions now also recognize people already in "
        "your system — resident clusters no longer show up unlabeled.",
        "Events without any person in them can be marked as false triggers "
        "— they get their own silent class and stop cluttering the "
        "label flow.",
    )),
    ("0.1.0.118", (
        "Recognition got a lot faster: video decoding now runs on the GPU "
        "(Intel via VAAPI, NVIDIA via NVDEC) and only the frames that matter "
        "leave the decoder. On the author's machine a learning run dropped "
        "from 6.6 to 2.9 seconds per event.",
        "Face and person recognition now work together on Today: a pass with "
        "no usable face is attributed to the person the body path recognized "
        "\u2014 clearly marked 'via person recognition, no face'.",
        "Full backup: one portable archive with everything you taught your "
        "installation (settings, face references, learned person material, "
        "models) and a restore that brings it all back \u2014 made for moving "
        "to another machine.",
        "The person path's decision threshold is now measured from your own "
        "material after every training, and the fire rule (window, supporting "
        "events, cool-down) is configurable under Person \u2192 Model status.",
    )),
    ("0.1.0.113", (
        "Person learn (preview): a second recognition path that learns "
        "residents by their whole appearance — start under Learn → Person "
        "learn, harvest full-body images and review every picture. Body "
        "recognition stays off until at least one person is learned and "
        "reviewed, and you arm it yourself under Person → Model status.",
        "A note on speed: this new path still runs on the CPU, so learning "
        "runs take a while (roughly 15–30 s per event) — please bear with "
        "it. Moving it to the GPU/NPU is planned for a later version.",
    )),
    ("0.1.0.103-alpha", (
        "Learning module: run guided learning over your past events — harvest faces, group recurring people, name them and adopt them into recognition.",
        "Camera areas: group cameras into parts of your property and use them as views on Today, Appearances and Events.",
    )),
)
