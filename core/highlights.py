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
STAND = "0.1.0.526"   # .526 ist das RELEASE des Lernlauf-Umbaus (.512-.525). Box-Inhalt
                      # MIT dem User abgestimmt (10.09.2026 ~19:2x, "perfekt";
                      # Fassung tester/whatsnew_box_abgestimmt_525.md): VIER
                      # Eintraege, EN woertlich wie abgestimmt. Der .512-ENTWURF
                      # ist dabei ersetzt worden (nie veroeffentlicht, nie
                      # abgestimmt) — genau die Auflage, unter der er stand.
                      # Dazu die Renderer-Auflage des Users: die Marke faerbt nur
                      # den Kopf bis zum ersten Gedankenstrich rot/fett.
                      # Davor: "0.1.0.525"   # .525 ist eine LOG-/SCHALTER-POLITUR aus dem Prod-Pruefbericht
                      # des .523-Standes: der Auto-Export nach Frigate startet nicht
                      # mehr, wenn Frigates eigene Gesichtserkennung bekanntermassen
                      # aus ist (dann endete jede gelungene Uebernahme in einer
                      # `!! … FAILED`-Zeile); die rohen insightface-Init-Zeilen
                      # ("Applied providers: ['CPUExecutionProvider']") liegen im
                      # Dienst-Log hinter dem debug-Schalter; zwei Log-Etiketten
                      # stimmen wieder (Angebot statt Register, struktur-gesperrte
                      # Funde in der Achsen-Bilanz) und ein deutsches Wort ist
                      # englisch. Alles Darstellung/Hygiene, KEINE
                      # Verhaltensaenderung an der Erkennung — also KEIN Box-Eintrag
                      # ([[whatsnew-inhalt-abstimmen]]: Box-Inhalte nur mit
                      # User-Abstimmung). STAND wandert nur mit, damit das Gate
                      # (STAND == VERSION) faehrt.
                      # Davor: "0.1.0.524"   # .524 baut zwei Fixes AM PASS-KNOPF von .521 (User-Bestellung
                      # 10.09.): Abbrechen an der laufenden Anzeige (Fix 11) und
                      # hoechstens EIN interaktiver Klick-Lauf, weitere reihen sich
                      # FIFO ein (Fix 12). Beides betrifft einen Schritt, der noch
                      # NICHT veroeffentlicht ist — also KEIN Box-Eintrag
                      # ([[whatsnew-inhalt-abstimmen]]: Box-Inhalte nur mit
                      # User-Abstimmung, und die .521-Box steht noch aus). STAND
                      # wandert nur mit, damit das Gate (STAND == VERSION) faehrt.
                      # Davor: "0.1.0.523"   # .523 ist ein GATE-/PIN-ZUG: die fuenf compose-Pins auf die neue
                      # VERSION, die .257-Benenn-Stufe am AST statt am Text-Zaehler,
                      # und der Namen-Scrub der Zuschreibungs-Kommentare aus dem
                      # .515-.522-Bauzug. NICHTS davon ist Nutzer-sichtbar, also KEIN
                      # Box-Eintrag ([[whatsnew-inhalt-abstimmen]]: Box-Inhalte nur mit
                      # User-Abstimmung). STAND wandert nur mit, damit das Gate
                      # (STAND == VERSION) faehrt.
                      # Davor: "0.1.0.522"   # .522 ist ein REPARATUR-ZUG (Widerleger-Befunde des .521-Zugs:
                      # Puls-Luecke am Pass-Knopf, Altdaten-Falle im Norm-Schritt,
                      # rmtree neben laufender Ernte). KEIN Box-Eintrag — er behebt
                      # Fehler eines noch unveroeffentlichten Schritts, es gibt nichts
                      # Neues zu zeigen. STAND wandert nur mit, damit das Gate
                      # (STAND == VERSION) faehrt.
                      # Davor: "0.1.0.521"   # .521 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .521 macht den
                      # PASS-KNOPF zu einem MINI-ERNTELAUF (User-Go 10.09.): der Klick
                      # auf einen Durchgang holt sich die Clips, erntet alle Frames,
                      # siebt mit dem Register „Face catalog" der jeweiligen Kamera,
                      # misst die Feature-Norm gebuendelt nach — und filtert erst
                      # danach auf die Person. Damit urteilt am Knopf DASSELBE System
                      # wie im Lernlauf; die zwei Alt-Wege (Pixel-Latte am
                      # gespeicherten Ausschnitt bzw. Konsens + Vorrats-Linie) sind
                      # ersetzt, nicht danebengestellt. Sichtbar wird das als „mehr
                      # und bessere Vorschlaege je Durchgang". Fuer die Box waere das
                      # ein guter Eintrag; der Wortlaut wird vor der Veroeffentlichung
                      # mit dem User durchgegangen ([[whatsnew-inhalt-abstimmen]]),
                      # solange wandert STAND nur mit, damit das Gate (STAND ==
                      # VERSION) faehrt. Was .521 fachlich tut, steht im CHANGELOG.
                      # (.520 hat STAND nicht mitgezogen — der Regler-Zug war rein
                      # intern; nachgeholt mit diesem Zug.)
                      # Davor: "0.1.0.519"   # .519 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .519 ist FIX 10,
                      # die PRAESENZ-DARSTELLUNG (User-Zuschnitt 10.09.): Weiss auf der
                      # Anwesenheitsleiste heisst ab sofort ausschliesslich "der Dienst
                      # lief in dieser Viertelstunde nicht". Bis .518 hiess es zweierlei
                      # — das und "mindestens ein Ereignis irgendeiner Kamera wurde nicht
                      # analysiert" —, und die zweite Bedeutung war die haeufigere: eine
                      # Viertelstunde mit 106 gelungenen Analysen und 12 Luecken stand
                      # weiss da. Gelaufene Slots sind jetzt gruen, Teil-Luecken eine
                      # kleine Ecke auf der gruenen Kachel mit den Zahlen im Tooltip, und
                      # ein spaeter geglueckter Nachhol-Versuch nimmt seine eigene Luecke
                      # zurueck. Fuer die Box waere das ein guter Eintrag (es ist eine
                      # sichtbare Verhaltensaenderung an einer Seite, die Nutzer taeglich
                      # ansehen) — der Wortlaut wird vor der Veroeffentlichung mit dem
                      # User durchgegangen ([[whatsnew-inhalt-abstimmen]]); solange
                      # wandert STAND nur mit, damit das Gate (STAND == VERSION) faehrt.
                      # Was .519 fachlich tut, steht im CHANGELOG.
                      # Davor: "0.1.0.518"   # .518 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .518 ist der
                      # NORM-NACHMESS-JOB (User-Go 10.09. „so bauen"): der Lernlauf
                      # erntet mit den fuenf leichten Achsen und misst die Feature-Norm
                      # danach in EINEM gebuendelten Schritt statt in jedem Ernte-Job.
                      # Fuer den Betreiber aendert sich am ERGEBNIS nichts (dieselbe
                      # Messbasis, dieselben Latten, dieselben Entscheidungen) — es
                      # aendert sich, WAS ein Lauf an Speicher braucht: die
                      # Analyse-Plaetze bleiben gleich leicht, statt dass jeder von
                      # ihnen eine eigene 2,7-GB-Session bauen kann. Ein Box-Eintrag
                      # ist faellig, sobald der Zug veroeffentlicht wird; solange
                      # bleibt es ein LOKALER Bau, und STAND wandert nur mit, damit das
                      # Gate (STAND == VERSION) faehrt. Der Wortlaut wird vor der
                      # Veroeffentlichung mit dem User durchgegangen
                      # ([[whatsnew-inhalt-abstimmen]]); was .518 fachlich tut, steht
                      # im CHANGELOG.
                      # Davor: "0.1.0.517"   # .517 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .517 ist der
                      # NORM-ENTSCHEID (User 10.09. nach Sichtung am Norm-Schieber):
                      # der Grundwert der Norm-Achse im Register "Face catalog" ist
                      # jetzt 20 statt der geliehenen 22,0 (756 Ernte-Bilder, Median
                      # 20,7), und den Norm-Regler gibt es nur noch DORT — im Register
                      # "Recognition" wird die Feature-Norm nicht gemessen, ein Regler
                      # ohne Wirkung ist schlechter als keiner. Die Achse selbst bleibt
                      # in beiden Registern (je Kamera einstellbar und gespeichert).
                      # Ein Box-Eintrag ist faellig, sobald der Zug veroeffentlicht
                      # wird; solange bleibt es ein LOKALER Bau, und STAND wandert nur
                      # mit, damit das Gate (STAND == VERSION) faehrt. Der Wortlaut wird
                      # vor der Veroeffentlichung mit dem User durchgegangen
                      # ([[whatsnew-inhalt-abstimmen]]); was .517 fachlich tut, steht im
                      # CHANGELOG.
                      # Davor: "0.1.0.516"   # .516 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .516 ist die
                      # ALT-LATTEN-ABLOESUNG (User-Go 10.09., Sechs-Achsen-Verfassung
                      # "keine Altlasten mitschleppen"): die zwei GLOBALEN Guete-Regler
                      # samt ihrer Seite verschwinden, alle ihre Verbraucher lesen das
                      # Register "Face catalog" je Kamera, und die Norm-Achse des
                      # Katalog-Registers geht werksseitig AN. Das ist eine sichtbare
                      # Verhaltensaenderung fuer jeden, der den Lernlauf nutzt (die
                      # Gruppen-Flaeche verwarf bis .515 fast alles, was das Sieb
                      # durchliess) — ein Box-Eintrag ist faellig, sobald der Zug
                      # veroeffentlicht wird; solange bleibt es ein LOKALER Bau, und
                      # STAND wandert nur mit, damit das Gate (STAND == VERSION) faehrt.
                      # Der Wortlaut wird vor der Veroeffentlichung mit dem User
                      # durchgegangen ([[whatsnew-inhalt-abstimmen]]); was .516 fachlich
                      # tut, steht im CHANGELOG.
                      # Davor: "0.1.0.515"   # .515 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .515 baut die zwei
                      # weiteren Sensoren in den Worker ein (User-Go 10.09.): die FEATURE-NORM
                      # und die KANTEN-LATTE werden fuenfte und sechste Achse derselben
                      # Sieb-Mechanik, in beiden Registern, je Kamera und global. Die Norm kommt
                      # werksseitig AUS (0), die Kanten-Latte mit 25 px — also genau dem Wert,
                      # der bisher als Konstante im Stimmweg stand. Nach heutigem Stand aendert
                      # sich am Verhalten des Normalwegs damit NICHTS; im Lernlauf-Sieb ist die
                      # Kanten-Achse neu. Ein Box-Eintrag ist faellig, sobald der Zug
                      # veroeffentlicht wird; solange bleibt es ein LOKALER Bau, und STAND
                      # wandert nur mit, damit das Gate (STAND == VERSION) faehrt. Der Wortlaut
                      # wird vor der Veroeffentlichung mit dem User durchgegangen
                      # ([[whatsnew-inhalt-abstimmen]]); was .515 fachlich tut, steht im CHANGELOG.
                      # Davor: "0.1.0.514"   # .514 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .514 ist Etappe 3 des
                      # Lernlauf-Umbaus ("ein Sieb"): der Lernlauf siebt seitdem mit denselben
                      # vier Reglern wie die Erkennung, nur mit eigenen Werten, und das
                      # Register "Face catalog" bekommt dafuer die zwei fehlenden Regler.
                      # Anders als .513 ist das ausdruecklich KEINE verhaltensneutrale Etappe —
                      # ein Lernlauf behaelt danach anderes Material als vorher. Genau deshalb
                      # ist hier ein Box-Eintrag faellig, sobald der Zug veroeffentlicht wird;
                      # solange bleibt es ein LOKALER Bau auf der Werkbank, und STAND wandert
                      # nur mit, damit das Gate (STAND == VERSION) faehrt. Der Wortlaut wird vor
                      # der Veroeffentlichung mit dem User durchgegangen
                      # ([[whatsnew-inhalt-abstimmen]]); was .514 fachlich tut, steht im CHANGELOG.
                      # Davor: "0.1.0.513"   # .513 PLATZHALTER, MIT DEM USER NICHT ABGESTIMMT. .513 ist Etappe 1 des
                      # Lernlauf-Umbaus ("Messkern") und ausdruecklich VERHALTENSNEUTRAL: keine
                      # Latte, kein Sieb, kein Urteil aendert sich, es gibt also nichts, was ein
                      # Nutzer an seiner Anlage merken wuerde. Deshalb KEIN eigener Box-Eintrag
                      # (User-Entscheid 02.08.: nicht jede Version bekommt einen — abgestimmt sein
                      # muss aber jede, darum wandert STAND mit). Vor jeder Veroeffentlichung wird
                      # der Box-Inhalt mit dem User durchgegangen ([[whatsnew-inhalt-abstimmen]]);
                      # was .513 fachlich tut, steht im CHANGELOG.
                      # Davor: "0.1.0.512"   # .512 ACHTUNG: Box-Inhalt ist ein ENTWURF, NICHT abgestimmt. .512 ist ein
                      # rein LOKALER Bau (vier Fixes aus der Katalog-Diagnose 09.09., kein Push,
                      # kein Deploy); der Eintrag steht hier, damit das Gate (STAND == VERSION)
                      # faehrt, und wird vor jeder Veroeffentlichung mit dem User durchgegangen
                      # und ersetzt ([[whatsnew-inhalt-abstimmen]]).
                      # Davor: "0.1.0.511"   # .511 Box-Inhalt MIT dem User abgestimmt (08.09.2026, EN-Wortlaut vom
                      # User vorgegeben): DREI Eintraege — ROCm-Fix samt neuer Ladeprobe im
                      # Gate, die neu gebaute Katalog-Pruefung samt einmaliger Ruecksetzung
                      # der Katalog-Latte, und der Ausblick auf die Neu-Eichung des
                      # Lernlaufs. Der Ruecksetz-Satz steht ausdruecklich MIT drin: er
                      # ueberschreibt gesetzte Kalibrierwerte, das darf niemand erst am
                      # Verhalten merken.
                      # Davor: "0.1.0.510"   # .510 Box-Inhalt MIT dem User abgestimmt (07.09.2026 20:0x, Fassung in
                      # backups/bau_0510/whatsnew_0510.txt): EIN Eintrag, EN woertlich wie
                      # abgestimmt. Die Interna des Zugs (fail-closed Guete je Fund, Clip-Tor
                      # am Ereignis-Weg, haltende Schlange bei Frigate-Ausfall, Masken im
                      # Support-Export) bleiben BEWUSST draussen — sie stehen im CHANGELOG.
                      # Davor: "0.1.0.509"   # .509 = .508 + Clip-Download-Tor, Lernlauf-Haertung (J13) und die
                      # Review-Fixes. Box-Inhalt UNVERAENDERT (E-O3, User 06.09.: „What's-new-Text
                      # aendern wir nicht.") — der .508-Eintrag traegt jetzt die Nummer .509, wie
                      # schon von .505 auf .506 und von .507 auf .508. .508 wurde nie
                      # veroeffentlicht, verschmolzen verliert also niemand einen Hinweis.
                      # Davor: "0.1.0.508"   # .508 Box-Inhalt User 06.09. frueh: der Satz steht EINMAL. Bis .507 lag
                      # derselbe Wortlaut zweimal in der Liste (Eintrag .506 UND .507), und die
                      # Box zeigt die letzten zehn Eintraege — der Nutzer sah die Zeile also
                      # doppelt untereinander (Befund J3 des .507-Deploy-Zugs). Beide Eintraege
                      # sind zu EINEM ("0.1.0.508") verschmolzen, Text unveraendert in allen
                      # fuenf Sprachen (E-O3 gilt weiter: „What's-new-Text aendern wir nicht.").
                      # .507 wurde nie veroeffentlicht und wandert deshalb mit — genau das
                      # Muster, mit dem .506 den .505-Eintrag uebernommen hat.
                      # Davor: "0.1.0.507"   # .507 Box-Inhalt User 05.09. 23:30 (Entscheid E-O3, bauplan_0507.md §1.3):
                      # „What's-new-Text aendern wir nicht." Der .507-Eintrag traegt WOERTLICH
                      # denselben Text wie der .506-Eintrag in allen fuenf Sprachen, nur die
                      # Nummer wandert. Der Zug selbst (Klick hat Vorfahrt, keine automatische
                      # Pass-Ernte, Personenseite, Kettungs-Modus) bekommt also KEINEN eigenen
                      # Satz in der Box — abgestimmt ist er trotzdem, deshalb STAND hoch.
                      # Davor: "0.1.0.506"   # .506 = .505 + Fix aus dem Prod-Funktionstest (Ereignis-Tabelle lief bei
                      # 900 px in den Body; Gate S9 rot -> fix-forward, Version hoch, Box-Inhalt
                      # UNVERAENDERT: der .505-Eintrag traegt jetzt die Nummer .506, weil .505 nie
                      # veroeffentlicht wurde).
                      # Davor: "0.1.0.505"   # .505 Box-Inhalt User 05.09. ~14:00: EIN Punkt (parallele Analyse
                      # auf beiden Wegen + Lernlauf nutzt freie Plaetze fair mit), OHNE
                      # den "Testversion"-Punkt (User: "bleibt wie es ist nur ohne test").
                      # .505 laeuft zunaechst nur auf den eigenen Maschinen (Haus-Bauzug
                      # bauplan_0505.md), Box-Inhalt trotzdem abgestimmt, weil ins Image gebacken.
                      # Davor: "0.1.0.504"   # .504 = reiner STAND-Bump: Box-Inhalt UNVERAENDERT gegenueber
                      # .503 (der GPU-Schalter-Punkt + "Testversion", User-Wortlaut
                      # 04.09.). .504 traegt nur die drei Oberflaechen-Korrekturen an
                      # der GPU-Seite — Interna, kein Box-Eintrag.
                      # Davor: "0.1.0.503"   # .503 Box-Inhalt User 04.09.: EIN Punkt, der GPU-Schalter fuer
                      # Parallelverarbitung (Wortlaut vom User vorgegeben, s. Eintrag unten).
                      # Davor: "0.1.0.501"   # .501 = Release-Nummer (.500 lief nur intern auf den Testsystemen; der Support-Re-Analyse-Fix 62346ee kam danach — ein Image, ein Commit). Box-Inhalt User 03.09. ~23:55: ein Punkt "deutlich
                      # verbesserte Gesichtserkennung" + die zwei .414-Punkte
                      # (Anwesenheit, Today) unter DIESER Nummer — .414 ist
                      # zurueckgezogen und taucht nirgends mehr auf.
                      # Davor: .416 = reiner STAND-Bump (Haus-Stand Testbett-Einspielung:
                      # POST /support/einspielen schickt ein Szenario gezielt durch
                      # die Erkennung EINER Kamera — Werkzeug fuer die Nachstellung
                      # fremder Systeme, kein Box-Eintrag).
                      # Davor: .415 = reiner STAND-Bump (Hotfix: Deadlock im live_only-Uebersprung,
                      # Tester-Realfall 02.09. abends — kein Box-Eintrag, Bugfix).
                      # Davor: .414 Box-Inhalt User 02.09. 18:45 — RELEASE-Version: GENAU zwei
                      # Eintraege, "Einbau einer Anwesenheitserkennung" und "Neubau der
                      # Today-Seite". Sonst nichts (kein Systemstatus, keine Live-Texte,
                      # keine Bugfixes) — der Wortlaut ist so abgestimmt und wird nicht
                      # ohne neue Abstimmung ergaenzt.
                      # Davor: .413 = reiner STAND-Bump (Today: Live-Namen nur noch aus Stufe-2-
                      # Namensmeldungen, nur-live-Karte fuehrt auf den Live-Auftritt) —
                      # Box-Inhalt unveraendert, vor einem Release mit dem User abstimmen.
                      # Davor: .412 = reiner STAND-Bump (Today neu: Personenkarten mit Anwesenheits-
                      # Miniatur, gedeckelte Durchgaenge, keine Gruppenkachel/kein Live-Block;
                      # Live-Meldetexte kurz; Bilder lazy).
                      # Davor: .411 = reiner STAND-Bump (Marge im Live-Urteil T0c, Pushover-Leerlauf,
                      # tmp-Kollision core/atomar, Live-Einleitungssatz).
                      # Davor: .410 = reiner STAND-Bump (Systemstatus: RAM-Kachel Cache-Trennung, Queue nach
                      # Betriebsart, Backlog-Verlauf, Live-Schalter).
                      # Davor: .409 = reiner STAND-Bump (Anwesenheitsseite /anwesenheit, Z4).
                      # Davor: .408 = reiner STAND-Bump (Anwesenheits-Marken, unsichtbarer Vorlauf).
                      # Davor: Eintraege fuer .380 (Unknown-Umbau, Support-Vollzugriff) VOR Release mit User abstimmen (User 30.08.:
                      # "whatsnew bleibt wie es ist").
                      # Davor: .371 = reiner STAND-Bump (User 30.08.:
                      # "whatsnew bleibt wie es jetzt ist" — die Box
                      # erscheint dadurch nicht neu). Davor: .370 (Anzeige des
                      # Fern-Support-Schalters) — kein Box-Eintrag
                      # .369 = reiner STAND-Bump (Namen mit Apostroph im
                      # Lernlauf) — Box-Eintrag nach Abstimmung
                      # .368 = reiner STAND-Bump (Steckbriefe nur einmal je
                      # Kamera + Auffrisch-Knopf) — Box-Eintrag nach Abstimmung
                      # .367 = reiner STAND-Bump (harte Linien auch im Sieb) —
                      # Box-Eintrag erst nach Abstimmung mit dem User
                      # .366 = reiner STAND-Bump (ein Massstab je Bilderliste,
                      # Veto-Linie 21,75) — Box-Eintrag erst nach Abstimmung
                      # mit dem User, wir veroeffentlichen gerade nicht
                      # .365 = reiner STAND-Bump (Fortsetzungs-Haken
                      # nicht mehr vorbelegt)
                      # .364 = reiner STAND-Bump (intelligentes Lernen, beide
                      # Schalter AUS ausgeliefert — Box-Eintrag erst, wenn der
                      # User ihn abgestimmt hat und die Schalter an sind)
                      # .363 = reiner STAND-Bump (Support-Zugriff; Box-Eintrag
                      # kommt abgestimmt mit dem naechsten Release)
                      # .362 = reiner STAND-Bump (Waechter-Selbstheilung Nachruestung; Box-Eintrag
                      # kommt abgestimmt mit dem naechsten Release)
                      # .351 = reiner STAND-Bump (Kalibrierseite Phase 1b; Box
                      # wird beim naechsten Release MIT dem User abgestimmt).
                      # .350 = reiner STAND-Bump (Belichtungsachse; Box-Eintrag
                      # wird beim naechsten Release MIT dem User abgestimmt).
                      # .349 = reiner STAND-Bump (Issue-26-Fix Anker-Uebernahme);
                      # der .347-Eintrag bleibt der neueste.
                      # .348 = reiner STAND-Bump ohne Box-Aenderung (Feldtester-Fix
                      # self.cfg im /heute-Zweig); der .347-Eintrag (User-diktiert)
                      # bleibt der neueste.
                      # .340 = reiner STAND-Bump ohne Box-Eintrag (Start-Nachhol-
                      # Schalter; Box-Abstimmung mit dem naechsten Release).
                      # .333-.335 = reine STAND-Bumps ohne Box-Eintrag (UI-Fix
                      # Anker-Kacheln, Audit-Fixes, det-size-Logfilter; Box-Abstimmung
                      # kommt mit dem naechsten Release). .322 = RELEASE-KANDIDAT (.312-.319 gingen nie raus; .319 lief
                      # auf Prod, wurde aber nie veroeffentlicht — die Box-Aenderung
                      # vom 22.08. braucht ein eigenes Image, weil ein bereits
                      # gebauter Tag nie stillschweigend neuen Inhalt bekommt).
                      # ABSTIMMUNG 22.08. (User): Box bleibt inhaltlich wie sie
                      # ist, .316-.319 stehen nur im CHANGELOG. GEAENDERT wurde
                      # allein der Wortlaut des betonten Punktes, woertliche
                      # Auflagen: kuerzer (die Texte sind immer sehr lang), "mit
                      # Unterstuetzung gebaut" statt "wurde damit gebaut" (der User
                      # baut, die KI unterstuetzt — das muss klar sein), und die
                      # Bitte um Rueckmeldung mit der oeffentlichen Adresse
                      # suslik_dev@posteo.de (steht so im _PUBLIC_README).
                      # ZWEI NEUE Punkte gegenueber der .313-Abstimmung, beide vom
                      # User am 21.08. abends verlangt: (1) GANZ OBEN der Hinweis auf
                      # das andere Bau-Modell (Opus statt Fable 5) samt Fehler-Vorbehalt
                      # — woertlicher User-Auftrag; (2) der Sichtbarkeits-Fix des
                      # Lernlaufs. Die drei Alt-Punkte bleiben unveraendert.
                      # VEROEFFENTLICHUNG: am 21.08. ausdruecklich NICHT (User:
                      # "aber wir veroeffenlichen heute kein release") — die Box
                      # wirkt erst mit dem naechsten echten Release.
                      # Davor .312 = Release-Kandidat (Box-Eintrag abgestimmt, s. HIGHLIGHTS).
                      # Davor .311 = interner Stand (User 21.08.): Fortschritts-
                      # Balken beim refcache-Neuaufbau in der Gruppen-Benennung
                      # (Sichtung, Benenn-Pruefung, Pass-Check); kein Box-Eintrag.
                      # Davor .310 = interner Stand (User-Funde 21.08.): Fortschritts-
                      # Leiste der Bestands-QS ohne Seiten-Reload, Fremd-Pruefung
                      # der Unbekannt-Vorschlaege, ehrlicher Dauer-Text; kein
                      # Box-Eintrag.
                      # Davor .309 = interner Fix: Beiwert-Einpflege in den refcache
                      # ohne Embedder-Objekt (jede Vorrats-Uebernahme warf sonst
                      # den Cache weg -> Minuten-Neuaufbau; kein Box-Eintrag).
                      # Davor .308 = interner Prod-Stand (K3-Inventur des Norm-Regelwerks:
                      # Pass-Check-Bruecke ueber die neue Kette, Bestands-QS-
                      # Einstufung, Sichtungs-Vorauswahl/Reihung, Bestands-Suche
                      # — alle vier Reststellen auf der Norm) — kein Box-Eintrag.
                      # Davor .307 = interner Prod-Stand (Norm-Weg in der Benennungs-
                      # Sichtung: bild_stufe qualifiziert alternativ zur
                      # Pixel-Latte; Zwillings-Zusammenfassung im Vorrats-
                      # Angebot) — kein Box-Eintrag, nur STAND.
                      # Davor .306 = interner Prod-Stand (Lernvorrat nach Feature-Norm,
                      # Schritt 2: Sammel-Achsen in der Ernte, Szenario-Konsens,
                      # Katalog-Angebote auf /aehnliche, Beiwert-Referenzen;
                      # bauplan_vorrat.md) — kein neuer Box-Eintrag, nur STAND
                      # hochgezogen; der Release-Eintrag wird mit dem User
                      # abgestimmt (Memory whatsnew-inhalt-abstimmen).
                      # Davor .305 = interner Prod-Stand (Modularisierung ME1: Innenseiten
                      # event/unbekannte/setup/live_alerts aus verifyd nach routes/,
                      # -518 Z; /heute ehrlich zurueck in NOCH_ENGLISCH bis zum
                      # heute.*-Einzug).
                      # Davor .304 = interner Prod-Stand (/personlauf im Lauf-Design des
                      # Gesichts-Lernlaufs, CSS zentralisiert als bausteine.
                      # lauffluss_stil; User-Auftrag 20.08.).
                      # Davor .303 (Sprach-Stufe 4: Meldetexte
                      # Pushover/Telegram sprachfaehig, MQTT byte-unveraendert; plus
                      # Nachlade-Fix D1+D2: ehrliche Pass-Check-Begruendung mit Zahlen
                      # + PASS-CHECK-Logzeile; davor .302 Stufe 3, .301 Tranche D) —
                      # kein neuer Box-Eintrag, nur STAND hochgezogen; der naechste
                      # Release-Eintrag wird mit dem User abgestimmt.
                      # Davor .298 (Release 19.08. abends): die zwei
                      # ABGESTIMMTEN Punkte — Absturz-Fix (Wortlaut vom User diktiert)
                      # + Mehrsprachigkeit (EN-Wortlaut vom User abgenommen). Seit .298
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
    # ####################################################################
    # 0.1.0.526 — INHALT MIT DEM USER ABGESTIMMT (10.09.2026 ~19:2x, "perfekt";
    # Fassung tester/whatsnew_box_abgestimmt_525.md). VIER Eintraege, der
    # englische Wortlaut steht WOERTLICH so, wie er abgestimmt wurde;
    # DE/ES/IT/FR sind die Uebersetzung davon (Praxis seit .298/§6.3).
    # Der ENTWURF-Eintrag "0.1.0.512" (Qualitaetsseite/Papierkorb, nie
    # veroeffentlicht, nie abgestimmt) ist damit ERSETZT — genau das war seine
    # Auflage ([[whatsnew-inhalt-abstimmen]]: vor jedem Release durchgehen und
    # ersetzen). Der erste Eintrag traegt die Marke; sie faerbt seit .526 nur
    # den Kopf bis zum ersten Gedankenstrich ("Test release"), nicht mehr den
    # ganzen Satz (User-Auflage zur Box, Renderer webui.whatsnew_block).
    # ####################################################################
    ("0.1.0.526", (
        {"betont": True,
         "de": "Testversion — der Lernlauf ist ganz neu. Bitte teste ihn und "
               "melde alles, was falsch aussieht.",
         "en": "Test release — the learning run is brand new. Please test it "
               "and report anything that looks wrong.",
         "es": "Versión de prueba — el ciclo de aprendizaje es completamente "
               "nuevo. Pruébalo y avisa de todo lo que parezca mal.",
         "it": "Versione di prova — il ciclo di apprendimento è completamente "
               "nuovo. Provalo e segnala tutto ciò che sembra sbagliato.",
         "fr": "Version de test — le cycle d'apprentissage est tout nouveau. "
               "Testez-le et signalez tout ce qui vous semble anormal."},
        {"de": "Der Lernlauf wurde neu gebaut und vereinheitlicht. Ein "
               "Güte-Sieb, überall dieselben Regeln. Im Kern: eine Prüfung auf "
               "einen Klick für jeden Durchgang. Sie erntet die Ereignisse, "
               "filtert auf die Person und bietet die besten Bilder an.",
         "en": "The learning run was rebuilt and harmonised. One quality "
               "sieve, the same rules everywhere. At its core: a one-click "
               "check on any pass. It harvests the events, filters for the "
               "person and offers the best pictures.",
         "es": "El ciclo de aprendizaje se ha reconstruido y unificado. Un "
               "solo tamiz de calidad, las mismas reglas en todas partes. En "
               "su núcleo: una comprobación con un clic para cualquier pasada. "
               "Recoge los eventos, filtra por la persona y ofrece las mejores "
               "imágenes.",
         "it": "Il ciclo di apprendimento è stato ricostruito e uniformato. Un "
               "solo setaccio di qualità, le stesse regole ovunque. Al centro: "
               "un controllo con un clic su qualsiasi passaggio. Raccoglie gli "
               "eventi, filtra sulla persona e propone le immagini migliori.",
         "fr": "Le cycle d'apprentissage a été reconstruit et harmonisé. Un "
               "seul tamis de qualité, les mêmes règles partout. Au cœur : un "
               "contrôle en un clic sur n'importe quel passage. Il récolte les "
               "événements, filtre sur la personne et propose les meilleures "
               "images."},
        {"de": "Die vorgeschlagenen Bilder sind noch nicht eingestellt. "
               "Besser: schau selbst und wähle die Gesichter, die dir am "
               "besten gefallen.",
         "en": "The suggested pictures are not tuned yet. Better: look for "
               "yourself and pick the faces that look best to you.",
         "es": "Las imágenes propuestas todavía no están ajustadas. Mejor: "
               "mira tú mismo y elige las caras que mejor te parezcan.",
         "it": "Le immagini proposte non sono ancora tarate. Meglio: guarda tu "
               "stesso e scegli i volti che ti sembrano migliori.",
         "fr": "Les images proposées ne sont pas encore réglées. Mieux : "
               "regardez vous-même et choisissez les visages qui vous semblent "
               "les meilleurs."},
        {"de": "Wenn dir mein Programm nützt, freue ich mich über einen Stern "
               "auf GitHub.",
         "en": "If my program is useful to you, I would be happy about a star "
               "on GitHub.",
         "es": "Si mi programa te resulta útil, me alegraría una estrella en "
               "GitHub.",
         "it": "Se il mio programma ti è utile, sarei felice di una stella su "
               "GitHub.",
         "fr": "Si mon programme vous est utile, une étoile sur GitHub me "
               "ferait plaisir."},
    )),
    # 0.1.0.511 — INHALT MIT DEM USER ABGESTIMMT (08.09.2026, Wortlaut vom User
    # vorgegeben). DREI Eintraege, der englische Text steht WOERTLICH so, wie er
    # abgestimmt wurde; DE/ES/IT/FR sind die Uebersetzung davon, Begriffe wie in
    # den bisherigen Eintraegen (Katalog-Latte / listón / asticella / barre).
    # Der dritte Eintrag ist bewusst ein AUSBLICK — der Lernlauf ist auf die
    # neue Guete-Skala noch nicht neu geeicht, und das steht in der Box statt
    # dass es jemand aus dem Verhalten erraten muss.
    # Nichts selbststaendig ergaenzt (Memory whatsnew-inhalt-abstimmen): die
    # Interna des Zugs — punktuelle Bericht-/refcache-Pflege, Mess-Sidecar,
    # warmer Worker, Store-Kameras auf der Kalibrier-Uebersicht — stehen im
    # CHANGELOG, nicht hier.
    ("0.1.0.511", (
        {"de": "Das AMD/ROCm-Image nutzt jetzt wirklich die GPU. Zwei fehlende "
               "Bibliotheken verhinderten, dass der Erkennungs-Provider lud — "
               "AMD-Systeme rechneten still auf der CPU. Behoben; und jedes Image "
               "muss vor der Freigabe nachweisen, dass es laden kann, was es "
               "mitbringt.",
         "en": "AMD/ROCm image actually uses the GPU now. Two missing libraries "
               "kept the recognition provider from loading, so AMD systems "
               "silently computed on the CPU. Fixed — and every image now has to "
               "prove it can load what it ships before it leaves the gate.",
         "es": "La imagen AMD/ROCm ya usa la GPU de verdad. Dos bibliotecas "
               "ausentes impedían que se cargara el proveedor de reconocimiento, "
               "así que los sistemas AMD calculaban en la CPU sin decirlo. "
               "Corregido; y ahora cada imagen debe demostrar que puede cargar lo "
               "que trae antes de salir.",
         "it": "L'immagine AMD/ROCm ora usa davvero la GPU. Due librerie mancanti "
               "impedivano il caricamento del provider di riconoscimento, così i "
               "sistemi AMD calcolavano sulla CPU senza dirlo. Risolto; e ora ogni "
               "immagine deve dimostrare di poter caricare ciò che porta con sé "
               "prima di uscire.",
         "fr": "L'image AMD/ROCm utilise enfin vraiment le GPU. Deux bibliothèques "
               "manquantes empêchaient le chargement du fournisseur de "
               "reconnaissance, les systèmes AMD calculaient donc sur le "
               "processeur sans le dire. Corrigé ; et chaque image doit désormais "
               "prouver qu'elle peut charger ce qu'elle embarque avant de sortir."},
        {"de": "Die Qualitätsprüfung des Gesichterkatalogs ist neu gebaut. Sie "
               "urteilt mit der kalibrierten Güte-Skala, gruppiert ihre Funde "
               "(schwache Bilder, identische Kopien, kein Gesicht gefunden, "
               "möglicherweise verwechselte Gesichter) und schlägt Entfernungen "
               "vor — gelöscht wird nichts ohne deinen Klick. Ein Bild zu löschen "
               "geht jetzt sofort, statt den ganzen Katalog neu zu prüfen. Die "
               "Katalog-Latte stand viel zu streng und wird auf allen "
               "Installationen einmalig zurückgesetzt — das automatische Lernen "
               "sammelt wieder Material.",
         "en": "Face catalogue quality check rebuilt. It judges with the "
               "calibrated quality scale, groups its findings (weak pictures, "
               "identical copies, no face found, possibly mixed-up faces) and "
               "suggests removals — nothing is deleted without your click. "
               "Deleting a picture is instant now instead of re-checking the whole "
               "catalogue. The catalogue bar was set far too strict and is reset "
               "once on all installations — automatic learning collects material "
               "again.",
         "es": "El control de calidad del catálogo de caras se ha rehecho. Juzga "
               "con la escala de calidad calibrada, agrupa sus hallazgos "
               "(imágenes débiles, copias idénticas, ninguna cara encontrada, "
               "caras posiblemente confundidas) y propone eliminaciones: no se "
               "borra nada sin tu clic. Borrar una imagen es ahora inmediato en "
               "lugar de revisar todo el catálogo. El listón del catálogo estaba "
               "demasiado estricto y se restablece una vez en todas las "
               "instalaciones: el aprendizaje automático vuelve a reunir material.",
         "it": "Il controllo qualità del catalogo dei volti è stato ricostruito. "
               "Giudica con la scala di qualità calibrata, raggruppa i suoi rilievi "
               "(immagini deboli, copie identiche, nessun volto trovato, volti "
               "forse scambiati) e propone rimozioni: nulla viene cancellato senza "
               "il tuo clic. Cancellare un'immagine è ora immediato invece di "
               "ricontrollare l'intero catalogo. L'asticella del catalogo era "
               "troppo severa e viene reimpostata una volta su tutte le "
               "installazioni: l'apprendimento automatico raccoglie di nuovo "
               "materiale.",
         "fr": "Le contrôle qualité du catalogue de visages a été reconstruit. Il "
               "juge avec l'échelle de qualité calibrée, regroupe ses constats "
               "(images faibles, copies identiques, aucun visage trouvé, visages "
               "peut-être confondus) et propose des suppressions : rien n'est "
               "supprimé sans votre clic. Supprimer une image est maintenant "
               "immédiat au lieu de recontrôler tout le catalogue. La barre du "
               "catalogue était bien trop stricte et est réinitialisée une fois sur "
               "toutes les installations : l'apprentissage automatique récolte de "
               "nouveau du matériel."},
        {"de": "Als Nächstes: der Lernlauf wird auf die neue Güte-Skala neu "
               "geeicht.",
         "en": "Still ahead: recalibrating the learning run on the new quality "
               "scale.",
         "es": "Lo siguiente: recalibrar el ciclo de aprendizaje con la nueva "
               "escala de calidad.",
         "it": "Prossimo passo: ritarare il ciclo di apprendimento sulla nuova "
               "scala di qualità.",
         "fr": "Prochaine étape : réétalonner le cycle d'apprentissage sur la "
               "nouvelle échelle de qualité."},
    )),
    # 0.1.0.510 — INHALT MIT DEM USER ABGESTIMMT (07.09.2026 20:0x; die abgenommene
    # Fassung liegt in backups/bau_0510/whatsnew_0510.txt). GENAU EIN Eintrag, der
    # englische Wortlaut steht WOERTLICH so, wie abgestimmt — DE/ES/IT/FR sind die
    # Uebersetzung davon (DE deckt sich mit der Mitlese-Zeile der Abstimmung),
    # Begriffe wie in den bisherigen Eintraegen (Plaetze / plazas / posti / places).
    # Nichts selbststaendig ergaenzt (Memory whatsnew-inhalt-abstimmen): die Interna
    # des Zugs — fail-closed Guete je Fund (B1/B6), Klick-Suche im warmen Worker
    # (B3/J18), Clip-Tor auch am Ereignis-Weg (B4/J15), haltende Schlange bei
    # Frigate-Ausfall (B5/J16), maskierte Zugangsdaten im Support-Export (B7) —
    # bleiben BEWUSST draussen und stehen im CHANGELOG.
    ("0.1.0.510", (
        {"de": "Bessere Erkennung: die Bestätigungsschwelle wurde nach einer Feldmessung "
               "gesenkt, dadurch bekommen mehr echte Auftritte einen Namen. Alle "
               "Analyse-Plätze bleiben jetzt unter Last ausgelastet. Kleine Fixes.",
         "en": "Better recognition: the confirmation threshold was lowered after a field "
               "measurement, so more real appearances get named. All analysis slots now "
               "stay busy under load. Small fixes.",
         "es": "Mejor reconocimiento: el umbral de confirmación se ha bajado tras una "
               "medición sobre el terreno, así más apariciones reales reciben un nombre. "
               "Todas las plazas de análisis se mantienen ocupadas bajo carga. Pequeñas "
               "correcciones.",
         "it": "Riconoscimento migliore: la soglia di conferma è stata abbassata dopo una "
               "misurazione sul campo, così più comparse reali ricevono un nome. Tutti i "
               "posti di analisi restano ora occupati sotto carico. Piccole correzioni.",
         "fr": "Meilleure reconnaissance : le seuil de confirmation a été abaissé après "
               "une mesure sur le terrain, davantage d'apparitions réelles reçoivent donc "
               "un nom. Toutes les places d'analyse restent occupées en charge. Petites "
               "corrections."},
    )),
    # 0.1.0.509 — EIN Eintrag fuer .505 bis .509. Der Wortlaut ist der des
    # .505-Zugs ("whats new bleibt wie es ist nur ohne test", User 05.09.2026) und
    # bleibt unveraendert (E-O3, User 05.09. 23:30: "What's-new-Text aendern wir
    # nicht.") — nur die Nummer wandert, wie schon von .505 auf .506.
    # Warum EIN Eintrag statt zweier gleichlautender: bis .507 standen .506 UND .507
    # mit demselben Satz in der Liste, und die Box zeigt die letzten zehn Eintraege
    # (webui/__init__.whatsnew_block) — der Nutzer sah die Zeile also zweimal
    # untereinander (Befund J3 des .507-Deploy-Zugs, B7-Bericht Punkt 1). .507 war nie
    # veroeffentlicht; verschmolzen verliert also niemand einen Hinweis, den er schon
    # gesehen hat. Der .507-Zug selbst (Klick hat Vorfahrt, keine automatische
    # Pass-Ernte, Personenseite, Kettungs-Modus je Area) bekommt weiterhin KEINEN
    # eigenen Satz in der Box — er steht im CHANGELOG. Dasselbe gilt fuer .509
    # (Clip-Download-Tor, Lernlauf-Haertung, Review-Fixes): Interna und
    # Fehlerbehebungen, keine Key-Features.
    ("0.1.0.509", (
        {"de": "Parallele Analyse jetzt auf beiden Wegen (Poll und MQTT). Der Lernlauf "
               "nutzt freie Plätze mit, ohne die laufende Erkennung zu verdrängen.",
         "en": "Parallel analysis now on both paths (poll and MQTT). The learning run "
               "uses free slots without pushing the running recognition aside.",
         "es": "Análisis en paralelo ahora en ambas vías (sondeo y MQTT). El aprendizaje "
               "aprovecha las plazas libres sin desplazar el reconocimiento en curso.",
         "it": "Analisi in parallelo ora su entrambe le vie (polling e MQTT). "
               "L'apprendimento usa i posti liberi senza scalzare il riconoscimento in corso.",
         "fr": "Analyse en parallèle désormais sur les deux voies (interrogation et MQTT). "
               "L'apprentissage utilise les places libres sans écarter la reconnaissance "
               "en cours."},
    )),
    # 0.1.0.503 — Box-Inhalt User 04.09.2026, Wortlaut vom User vorgegeben:
    # "Umstellung oder Einbau eines GPU-Schalters, damit Parallelverarbeitung von
    # mehreren Workern und Live moeglich ist, fuer groessere Kamerasysteme."
    # GENAU EIN Eintrag. Alles andere aus diesem Zug (Waechter ueber die Plaetze,
    # Haertung der Broker-Worker-Kommunikation, Lernlauf am Broker) bleibt BEWUSST
    # draussen — Interna, keine Key-Features.
    ("0.1.0.503", (
        # User 04.09.: "Testversion" hervorgehoben voran, danach der normale Text.
        # `betont` faerbt den Punkt rot und fett (webui: li.wn-betont) — dieselbe
        # Marke wie beim Mehr-Personen-Hinweis in .501, keine zweite Mechanik.
        {"betont": True,
         "de": "Testversion.",
         "en": "Test version.",
         "es": "Versión de prueba.",
         "it": "Versione di prova.",
         "fr": "Version de test."},
        {"de": "Neu: ein GPU-Schalter. Damit lassen sich mehrere Worker und die "
               "Live-Wächter parallel auf der Grafikkarte betreiben — gedacht für "
               "größere Kamerasysteme.",
         "en": "New: a GPU switch. It lets several workers and the live watchers run "
               "in parallel on the graphics card — meant for larger camera systems.",
         "es": "Nuevo: un interruptor de GPU. Permite ejecutar varios trabajadores y "
               "los vigilantes en vivo en paralelo en la tarjeta gráfica, pensado para "
               "sistemas de cámaras más grandes.",
         "it": "Novità: un interruttore GPU. Consente di eseguire più worker e le "
               "sentinelle live in parallelo sulla scheda grafica, pensato per impianti "
               "di telecamere più grandi.",
         "fr": "Nouveau : un commutateur GPU. Il permet de faire tourner plusieurs "
               "workers et les veilleurs directs en parallèle sur la carte graphique, "
               "pensé pour les installations de caméras plus grandes."},
    )),
    # .414 — Inhalt vom User festgelegt (02.09. 18:45): GENAU zwei Eintraege,
    # "Einbau einer Anwesenheitserkennung" und "Neubau der Today-Seite". Alles
    # andere aus .407-.413 (Systemstatus, kurze Live-Meldetexte, Marge, lazy)
    # bleibt BEWUSST draussen — nicht ohne neue Abstimmung ergaenzen.
    # EN ist die Quelle, DE/ES/IT/FR wortgleich uebersetzt.
    # 0.1.0.500 — Box-Inhalt User 03.09. ~23:55: EIN neuer Punkt ("bessere
    # Gesichtserkennung, deutlich verbessert, mehr nicht") PLUS die zwei
    # abgestimmten .414-Punkte hierher gezogen — die Zwischenversion .414
    # wurde zurueckgezogen (von GitHub/GHCR entfernt) und darf NIRGENDS mehr
    # auftauchen (User: "alles in dieser Version").
    ("0.1.0.501", (
        {"de": "Deutlich verbesserte Gesichtserkennung.",
         "en": "Greatly improved face recognition.",
         "es": "Reconocimiento facial muy mejorado.",
         "it": "Riconoscimento facciale nettamente migliorato.",
         "fr": "Reconnaissance faciale nettement améliorée."},
        # Betonter Hinweis (User 04.09. frueh, Wortlaut "nur begrenzt funktioniert"):
        # Mehr-Personen-Erkennung im Bild ist in Arbeit (Blockraster/Logbuch, s. stand.md).
        # Mehrsprachige Eintraege tragen die Marke als Feld "betont" (Renderer
        # webui: dict -> txt.get("betont")); das BETONT-Praefix gilt nur fuer
        # englische Alt-Strings.
        {"betont": True,
         "de": "Die Erkennung mehrerer Personen in einem Bild funktioniert derzeit nur "
               "begrenzt — daran arbeite ich.",
         "en": "Recognising several people in one picture works only to a limited extent "
               "for now — I am working on it.",
         "es": "El reconocimiento de varias personas en una misma imagen funciona por "
               "ahora solo de forma limitada — estoy trabajando en ello.",
         "it": "Il riconoscimento di più persone nella stessa immagine per ora funziona "
               "solo in modo limitato — ci sto lavorando.",
         "fr": "La reconnaissance de plusieurs personnes sur une même image ne fonctionne "
               "pour l'instant que de façon limitée — j'y travaille."},
        {"de": "Neu: Anwesenheitserkennung. Die Seite Anwesenheit zeigt je Person den "
               "Tag in Viertelstunden — rot war da, grün nicht da, leer heißt das "
               "System lief nicht. Umschaltbar nach Kamera oder Bereich, 30 Tage "
               "zurückblätterbar. Die Marken kommen aus der Ereignis-Analyse und "
               "vom Live-Wächter gleichermaßen.",
         "en": "New: presence detection. The Presence page shows each person's day "
               "in quarter hours — red was there, green was not, empty means the "
               "system was not running. Switch between all cameras, one camera or "
               "an area, page back 30 days. Marks come from event analysis and the "
               "live watcher alike.",
         "es": "Nuevo: detección de presencia. La página Presencia muestra el día de "
               "cada persona en cuartos de hora: rojo estuvo, verde no estuvo, vacío "
               "significa que el sistema no estaba en marcha. Conmutable por cámara "
               "o zona, con 30 días hacia atrás. Las marcas vienen tanto del análisis "
               "de eventos como del vigilante en vivo.",
         "it": "Novità: rilevamento della presenza. La pagina Presenza mostra la "
               "giornata di ogni persona in quarti d'ora: rosso era presente, verde "
               "no, vuoto significa che il sistema non era in funzione. Selezionabile "
               "per telecamera o area, con 30 giorni indietro. I segni arrivano sia "
               "dall'analisi degli eventi sia dal guardiano live.",
         "fr": "Nouveau : détection de présence. La page Présence montre la journée "
               "de chaque personne par quart d'heure : rouge présent, vert absent, "
               "vide signifie que le système ne tournait pas. Bascule par caméra ou "
               "par zone, 30 jours en arrière. Les marques viennent aussi bien de "
               "l'analyse des événements que du gardien en direct."},
        {"de": "Die Today-Seite ist neu gebaut: eine Karte je erkannter Person mit "
               "Anwesenheits-Miniatur, keine Gruppen-Kacheln mehr, kompakte "
               "Durchgangszeilen, Bilder laden erst beim Scrollen. Live erkannte "
               "Personen stehen als normale Karte mit dem Vermerk „live“.",
         "en": "The Today page is rebuilt: one card per recognized person with a "
               "presence mini-bar, no more group tiles, compact pass rows, images "
               "load as you scroll. People recognized live appear as normal cards "
               "with a “live” badge.",
         "es": "La página Hoy está reconstruida: una tarjeta por persona reconocida "
               "con una mini barra de presencia, sin mosaicos de grupo, filas de "
               "paso compactas, las imágenes se cargan al desplazarse. Las personas "
               "reconocidas en vivo aparecen como tarjetas normales con la marca "
               "“live”.",
         "it": "La pagina Oggi è stata ricostruita: una scheda per persona "
               "riconosciuta con una mini barra di presenza, niente più riquadri di "
               "gruppo, righe dei passaggi compatte, le immagini si caricano "
               "scorrendo. Le persone riconosciute live compaiono come schede "
               "normali con l'etichetta “live”.",
         "fr": "La page Aujourd'hui est reconstruite : une carte par personne "
               "reconnue avec une mini-barre de présence, plus de tuiles de groupe, "
               "des lignes de passage compactes, les images se chargent au "
               "défilement. Les personnes reconnues en direct apparaissent comme "
               "des cartes normales avec la mention “live”."},
    )),
    # .387/.402 — Inhalt vom User abgestimmt (31.08. diktiert; 01.09.: der
    # rote Zwischenversions-Hinweis fliegt wieder raus, "Rest kann alles so
    # bleiben"). Versions-Key beim Release-Lauf auf die finale Nummer ziehen,
    # falls bis dahin weitere Builds kommen.
    ("0.1.0.408", (
        # Zwei Feature-Punkte vom User nachgereicht (31.08.: "neue Kalibrierung
        # pro Kamera und neue Unbekannt-Seite muessen mit rein").
        {"de": "Neu: Kalibrierung pro Kamera. Ein eigener Knopf oben in der "
               "Leiste führt zur Übersicht; je Kamera stellst du an echten "
               "Bildern ein, welche Qualität für Anzeige, Meldung und Lernen "
               "zählt. Fehlt Material, sucht die Kamera auf Knopfdruck selbst "
               "in den letzten Aufnahmen.",
         "en": "New: per-camera calibration. A dedicated button in the top "
               "bar opens the overview; for each camera you use real "
               "pictures to set which quality counts for display, alerts and "
               "learning. If material is missing, the camera searches its "
               "recent recordings at the push of a button.",
         "es": "Nuevo: calibración por cámara. Un botón propio en la barra "
               "superior abre el resumen; en cada cámara ajustas con "
               "imágenes reales qué calidad cuenta para la vista, los avisos "
               "y el aprendizaje. Si faltan imágenes, la cámara busca por sí "
               "misma en las grabaciones recientes con un botón.",
         "it": "Novità: calibrazione per telecamera. Un pulsante dedicato "
               "nella barra superiore apre la panoramica; per ogni "
               "telecamera imposti con immagini reali quale qualità conta "
               "per la visualizzazione, gli avvisi e l'apprendimento. Se "
               "manca materiale, la telecamera cerca da sola nelle "
               "registrazioni recenti con un pulsante.",
         "fr": "Nouveau : calibrage par caméra. Un bouton dédié dans la "
               "barre supérieure ouvre la vue d'ensemble ; pour chaque "
               "caméra, tu règles sur de vraies images quelle qualité "
               "compte pour l'affichage, les alertes et l'apprentissage. "
               "S'il manque des images, la caméra cherche elle-même dans "
               "les enregistrements récents d'un simple bouton."},
        {"de": "Die Unbekannt-Seite ist neu gebaut: Sie bleibt auch bei "
               "großen Beständen schnell, mit Seiten, Filtern und "
               "Sortierung, und mehrere Unbekannte lassen sich in einem Zug "
               "zusammenführen.",
         "en": "The Unknown page is rebuilt: it stays fast even with large "
               "collections, with paging, filters and sorting, and several "
               "unknowns can be merged in one go.",
         "es": "La página de desconocidos está reconstruida: sigue siendo "
               "rápida incluso con colecciones grandes, con páginas, "
               "filtros y ordenación, y varios desconocidos se pueden "
               "fusionar de una vez.",
         "it": "La pagina degli sconosciuti è ricostruita: resta veloce "
               "anche con raccolte grandi, con pagine, filtri e "
               "ordinamento, e più sconosciuti si possono unire in un solo "
               "passaggio.",
         "fr": "La page des inconnus est reconstruite : elle reste rapide "
               "même avec de grandes collections, avec pagination, filtres "
               "et tri, et plusieurs inconnus peuvent être fusionnés en une "
               "fois."},
    )),
    # .377 — INHALT VOM USER ABGESTIMMT (30.08. abends: "zwei Dinge gehen in
    # die What's new, die Kalibrierungsfunktion und der Bug, dass die
    # Personenermittlung bei 17.2 nicht funktioniert hat, sondern erst bei
    # 18"). GENAU diese zwei Punkte, nichts selbststaendig ergaenzt (Memory
    # whatsnew-inhalt-abstimmen). DE ist die Vorlage, EN daraus; ES/IT/FR mit
    # den etablierten Begriffen der Sprachdateien.
    ("0.1.0.377", (
        {"de": "Neu: Kalibrierung. Du stellst an den Bildern deines eigenen "
               "Lernlaufs mit zwei Reglern ein, welche Bildqualität dir zum "
               "Lernen reicht — der Knopf dafür sitzt an der Benennen-Karte "
               "des Lernlaufs.",
         "en": "New: calibration. Using the pictures of your own learning "
               "run, two sliders let you set which picture quality is good "
               "enough for learning — the button sits on the naming card of "
               "the learning run.",
         "es": "Nuevo: calibración. Con las imágenes de tu propio "
               "aprendizaje, dos controles te permiten definir qué calidad "
               "de imagen basta para aprender; el botón está en la tarjeta "
               "de nombres del aprendizaje.",
         "it": "Novità: calibrazione. Con le immagini del tuo apprendimento, "
               "due cursori ti permettono di stabilire quale qualità "
               "d'immagine basta per imparare; il pulsante si trova sulla "
               "scheda dei nomi dell'apprendimento.",
         "fr": "Nouveau : calibrage. À partir des images de votre propre "
               "apprentissage, deux curseurs vous permettent de définir "
               "quelle qualité d'image suffit pour apprendre ; le bouton se "
               "trouve sur la carte de nommage de l'apprentissage."},
        {"de": "Fehler behoben: das Personen-Lernen (Ganzkörper) lieferte "
               "mit Frigate bis 0.17 nie Bilder — es brauchte ein Feld, das "
               "erst Frigate 0.18 kennt. Jetzt lernt es dort aus dem "
               "Schnappschuss je Ereignis.",
         "en": "Fixed: person learning (full body) never produced pictures "
               "with Frigate up to 0.17 — it needed a field only Frigate "
               "0.18 provides. It now learns from the snapshot per event "
               "there.",
         "es": "Corregido: el aprendizaje de personas (cuerpo entero) nunca "
               "producía imágenes con Frigate hasta 0.17 — necesitaba un "
               "campo que solo existe desde Frigate 0.18. Ahora aprende allí "
               "de la instantánea de cada evento.",
         "it": "Corretto: l'apprendimento delle persone (corpo intero) non "
               "produceva mai immagini con Frigate fino alla 0.17 — serviva "
               "un campo che esiste solo da Frigate 0.18. Ora lì impara "
               "dall'istantanea di ogni evento.",
         "fr": "Corrigé : l'apprentissage des personnes (corps entier) ne "
               "produisait jamais d'images avec Frigate jusqu'en 0.17 — il "
               "lui fallait un champ qui n'existe que depuis Frigate 0.18. "
               "Il y apprend désormais à partir de l'instantané de chaque "
               "événement."},
    )),
    # .352 — INHALT VOM USER DIKTIERT (26.08. abends: "Nehmen wir auf, dass wir
    # auf GitHub eine extra Seite erstellt haben, wie man auf einem Proxmox-LXC-
    # Server am besten die CUDA oder die GPU durchreicht", praezisiert:
    # "allgemein unter lxc die gut optimal durchreicht an frigate und suslik").
    # GENAU dieser eine Punkt, nichts selbststaendig ergaenzt (Memory
    # whatsnew-inhalt-abstimmen). Gedeckt: docs/proxmox.md geht seit .352 zum
    # ersten Mal mit raus (Export-Whitelist) und belegt beide Verbraucher —
    # derselbe Render-Knoten kann an mehrere Container gehen, Frigate im einen,
    # suslik im anderen. DE ist die Vorlage, EN daraus; ES/IT/FR
    # Opus-Muttersprachler-Agent nach begriffe_tabellen.md FINAL (FR vous).
    # .359 — INHALT VOM USER FREIGEGEBEN (27.08. abends, "viel viel kuerzer,
    # ein satz pro thema"): genau die zwei abgenommenen Saetze, nichts ergaenzt
    # (Memory whatsnew-inhalt-abstimmen). Eintrag 2 ist der Anlass-Fall der
    # Vorrang-Regel (.356) samt Distanz-Zusatz (.359) und roter Kennzeichnung.
    # DE/EN vom User abgenommen; ES/IT/FR nach den Begriffen der Sprachdateien
    # (recorrido/passaggio/passage, Desconocido/Sconosciuto/Inconnu).
    # .369 — INHALT VOM USER ABGENOMMEN (29.08.: "Lernlauf neu und intelligent
    # gemacht, kurzer Satz, aber besser ausformuliert"). GENAU dieser eine
    # Punkt, nichts selbststaendig ergaenzt (Memory whatsnew-inhalt-abstimmen).
    # Gedeckt sind .364-.369: Qualitaets-Sieb vor der Identitaet, automatische
    # Benennung sicher erkannter Personen, keine Gruppen mehr ohne anzeigbares
    # Bild. DE ist die Vorlage, EN daraus; ES/IT/FR mit den etablierten
    # Begriffen der Sprachdateien (busqueda/ricerca/recherche d'apprentissage).
    ("0.1.0.369", (
        {"de": "Der Lernlauf ist neu gebaut: Er sortiert zuerst nach "
               "Bildqualität, benennt Personen, die er sicher wiedererkennt, "
               "von selbst, und zeigt dir nur noch Gruppen, in denen wirklich "
               "etwas Brauchbares steckt.",
         "en": "The learning run has been rebuilt: it sorts by picture quality "
               "first, names people it recognises with confidence on its own, "
               "and only shows you groups that actually contain something "
               "usable.",
         "es": "La búsqueda de aprendizaje se ha reconstruido: primero ordena "
               "por calidad de imagen, nombra por sí misma a las personas que "
               "reconoce con seguridad y solo te muestra grupos que realmente "
               "contienen algo aprovechable.",
         "it": "La ricerca di apprendimento è stata ricostruita: prima ordina "
               "per qualità dell'immagine, nomina da sola le persone che "
               "riconosce con certezza e ti mostra solo gruppi che contengono "
               "davvero qualcosa di utilizzabile.",
         "fr": "La recherche d'apprentissage a été reconstruite : elle trie "
               "d'abord par qualité d'image, nomme elle-même les personnes "
               "qu'elle reconnaît avec certitude et ne vous montre plus que "
               "des groupes contenant vraiment quelque chose d'exploitable."},
    )),
    ("0.1.0.359", (
        {"de": "Im Lernlauf lassen sich jetzt eine oder mehrere Kameras "
               "auswählen.",
         "en": "A learning run can now be limited to one or more cameras.",
         "es": "En la búsqueda de aprendizaje ahora se pueden elegir una o "
               "varias cámaras.",
         "it": "Nella ricerca di apprendimento ora si possono scegliere una o "
               "più telecamere.",
         "fr": "Lors d'une recherche d'apprentissage, vous pouvez désormais "
               "choisir une ou plusieurs caméras."},
        {"de": "Fehler behoben: die Personenerkennung konnte einem Fremden "
               "einen bekannten Namen geben — solche Durchgänge heißen jetzt "
               "Unbekannt.",
         "en": "Fixed: person recognition could give a stranger a known name "
               "— such passes now stay Unknown.",
         "es": "Corregido: el reconocimiento de personas podía dar a un "
               "extraño un nombre conocido; esos recorridos ahora quedan como "
               "Desconocido.",
         "it": "Corretto: il riconoscimento delle persone poteva dare a un "
               "estraneo un nome conosciuto; questi passaggi ora restano "
               "Sconosciuto.",
         "fr": "Corrigé : la reconnaissance de personnes pouvait donner à un "
               "inconnu un nom connu ; ces passages restent désormais "
               "Inconnu."},
    )),
    ("0.1.0.353", (
        {"de": "Neue Anleitung auf GitHub: wie man auf einem Proxmox-Server "
               "GPU oder CUDA in einen LXC-Container durchreicht, für suslik "
               "und Frigate.",
         "en": "New guide on GitHub: how to pass a GPU or CUDA through to an "
               "LXC container on a Proxmox server, for suslik and Frigate.",
         "es": "Nueva guía en GitHub: cómo pasar la GPU o CUDA a un contenedor "
               "LXC en un servidor Proxmox, para suslik y Frigate.",
         "it": "Nuova guida su GitHub: come passare la GPU o CUDA a un "
               "container LXC su un server Proxmox, per suslik e Frigate.",
         "fr": "Nouveau guide sur GitHub : comment donner accès au GPU ou à "
               "CUDA dans un conteneur LXC sur un serveur Proxmox, pour suslik "
               "et Frigate."},
    )),
    # .347 — INHALT VOM USER DIKTIERT (26.08. nachts: "nimm ins whats new auf,
    # dass wir jetzt eine systemstatistik haben und die erkennung fuer das
    # lernen deutlich beschleunigt") — GENAU diese zwei Punkte, nichts
    # selbststaendig ergaenzt (Memory whatsnew-inhalt-abstimmen). DE ist die
    # Vorlage, EN daraus; ES/IT/FR Opus-Muttersprachler-Agent nach
    # begriffe_tabellen.md FINAL (FR vous). Wortlaut-Abnahme beim Release-Halt.
    # Die Tempo-Zahl "etwa doppelt" ist gemessen (.342: 36-38 s -> 20-24 s).
    ("0.1.0.347", (
        {"de": "Neue Seite Systemstatistik: CPU, Arbeitsspeicher, Platte, GPU "
               "und NPU deiner Maschine auf einen Blick, zu finden oben im "
               "Menü.",
         "en": "New system stats page: CPU, memory, disk, GPU and NPU of your "
               "machine at a glance, found at the top of the menu.",
         "es": "Nueva página Estadísticas del sistema: CPU, memoria RAM, "
               "disco, GPU y NPU de tu equipo de un vistazo, la encuentras "
               "arriba en el menú.",
         "it": "Nuova pagina Statistiche di sistema: CPU, memoria RAM, disco, "
               "GPU e NPU della tua macchina a colpo d'occhio, la trovi in "
               "alto nel menu.",
         "fr": "Nouvelle page Statistiques système : CPU, mémoire vive, "
               "disque, GPU et NPU de votre machine d'un coup d'œil, elle se "
               "trouve en haut du menu."},
        {"de": "Das Einsammeln der Gesichter fürs Lernen ist deutlich "
               "schneller geworden, auf unserem System etwa doppelt so "
               "schnell: Gesichter ohne Chance werden aussortiert, bevor die "
               "teuren Rechenschritte laufen.",
         "en": "Collecting faces for learning got a lot faster, about twice "
               "as fast on our system: faces without a chance are dropped "
               "before the expensive computing steps run.",
         "es": "La extracción de rostros para el aprendizaje se ha vuelto "
               "mucho más rápida, en nuestro sistema aproximadamente el "
               "doble: los rostros que no tienen ninguna posibilidad se "
               "descartan antes de que empiecen los pasos de cálculo "
               "costosos.",
         "it": "L'estrazione dei volti per l'apprendimento è diventata molto "
               "più veloce, sul nostro sistema circa il doppio: i volti senza "
               "possibilità vengono scartati prima delle fasi di calcolo "
               "costose.",
         "fr": "La collecte des visages pour l'apprentissage est bien plus "
               "rapide, environ deux fois plus vite sur notre système : les "
               "visages qui n'ont aucune chance sont écartés avant les "
               "étapes de calcul coûteuses."},
    )),
    # .339 — MIT USER ABGESTIMMT (24.08. ~23:10, Wortlaut-Freigabe "go" nach zwei
    # Kuerzungsrunden: Log-Hygiene-Details und der 3-GB-Erststart-Hinweis flogen
    # raus — "so etwas gehoert doch nicht ins whats new"). ZWEI Punkte: der
    # Feld-Fix (betont, Tester-Dank ohne Namen) und die Start-Rechenpruefung
    # samt FP32-Rettung aelterer GPUs. DE ist die Vorlage; EN/ES/IT/FR von
    # Muttersprachler-Agenten nach begriffe_tabellen.md FINAL.
    ("0.1.0.339", (
        {"betont": True,
         "de": "Auf Maschinen mit wenig Arbeitsspeicher startete der "
               "Analyse-Prozess immer wieder neu, und die Erkennung stand "
               "still — behoben. Gefunden hat es ein Tester im Feld, danke "
               "dafür.",
         "en": "On machines with little memory the analysis process kept "
               "restarting and recognition stood still. Fixed. A tester out "
               "in the field found it, thanks for that.",
         "es": "En equipos con poca memoria RAM, el proceso de análisis se "
               "reiniciaba una y otra vez y el reconocimiento se quedaba "
               "parado. Ya está corregido. Lo encontró un usuario que lo "
               "estaba probando en su instalación, gracias.",
         "it": "Su macchine con poca memoria RAM il processo di analisi si "
               "riavviava di continuo e il riconoscimento restava fermo. Ora "
               "è risolto. L'ha trovato una persona che lo sta provando sul "
               "campo, grazie.",
         "fr": "Sur les machines avec peu de mémoire vive, le processus "
               "d'analyse redémarrait sans arrêt et la reconnaissance restait "
               "à l'arrêt. C'est corrigé. C'est un testeur sur le terrain qui "
               "l'a trouvé, merci à lui."},
        {"de": "Beim Start prüft suslik jetzt, ob GPU und NPU wirklich "
               "richtig rechnen, nicht nur ob sie vorhanden sind. Rechnet "
               "eine ältere GPU ungenau, nutzt suslik sie in einem genaueren "
               "Modus weiter, statt sie zu verwerfen.",
         "en": "At startup suslik now checks whether GPU and NPU really "
               "compute correctly, not just whether they are there. If an "
               "older GPU computes imprecisely, suslik keeps using it in a "
               "more precise mode instead of dropping it.",
         "es": "Al arrancar, suslik ahora comprueba si la GPU y la NPU "
               "calculan bien de verdad, no solo si están presentes. Si una "
               "GPU antigua calcula con poca precisión, suslik la sigue "
               "usando en un modo más preciso en lugar de dejar de usarla.",
         "it": "All'avvio suslik controlla ora se GPU e NPU calcolano davvero "
               "in modo corretto, non solo se ci sono. Se una GPU più vecchia "
               "calcola in modo impreciso, suslik continua a usarla in una "
               "modalità più precisa invece di rinunciarci.",
         "fr": "Au démarrage, suslik vérifie maintenant si le GPU et le NPU "
               "calculent vraiment correctement, et pas seulement s'ils sont "
               "présents. Si un GPU plus ancien calcule de façon imprécise, "
               "suslik continue de l'utiliser dans un mode plus précis au "
               "lieu de l'abandonner."},
    )),
    # .313 (als .312 vorbereitet, 21.08.) — MIT USER ABGESTIMMT (21.08. mittags): drei Punkte, deutscher
    # Wortlaut vom User freigegeben ("das passt, go"), Vorgabe "kürzer, kein
    # KI-Stil, kurz und knapp" (Humanizer-Durchgang); EN daraus, ES/IT/FR
    # von Opus-Muttersprachlern (Begriffe nach begriffe_tabellen.md FINAL;
    # FR bewusst vous, Tabellen-Entscheid). Keine Interim-Zeile (User).
    # .320 — MIT USER ABGESTIMMT (22.08.): Auflage "weniger im Detail, die Leute
    # werden erschlagen von den ganzen Informationen — Oberbegriffe statt jedem
    # einzelnen kleinen Punkt". Aus den fuenf Punkten der .315-Abstimmung wurden
    # deshalb VIER: die alten 2/3 und der Qualitaetswert aus 4 sind EIN Punkt
    # (Lernen), der Platten-Rest aus 4 ein eigener. Rausgefallen als Detail:
    # Fortschrittsbalken, Vorsortierung der Gruppenbenennung, die Ursache der
    # leeren Gruppen, "angehakt sind sie nicht" — alles steht im CHANGELOG.
    # 91 statt 186 Woerter. DE ist die Vorlage, EN/ES/IT/FR daraus abgeleitet;
    # Begriffe nach begriffe_tabellen.md FINAL (IT clip=video, FR clip=sequence,
    # live = en directo / in diretta / en direct), FR bewusst vous.
    ("0.1.0.331", (
        # Der KI-Modell-Hinweis (betonter Kopf-Eintrag der .331-Box: "mit
        # Unterstuetzung eines anderen KI-Modells gebaut ... mehr Fehler als
        # sonst") ist seit .336 ENTFERNT — User-Entscheid 24.08. abends
        # ("whats new nehmen wir den ki hinweis raus"): .336 behebt genau die
        # Regression jener Phase, gebaut wird wieder mit dem Stamm-Modell,
        # der Vorbehalt waere irrefuehrend. Das VEROEFFENTLICHTE .331-Image
        # behaelt seine Box unveraendert (ein gebauter Tag bekommt nie
        # stillschweigend neuen Inhalt); nur Images ab .336 zeigen die Box
        # ohne den Eintrag.
        # EIN Punkt fuer den ganzen Lern-Strang (.299-.318).
        {"en": "Learning faces got better: after every pass suslik looks for "
               "usable pictures on its own, rates their quality, and no longer "
               "drops a group without asking you.",
         "de": "Gesichter lernen geht besser: suslik sucht nach jedem Durchgang "
               "selbst nach brauchbaren Bildern, bewertet ihre Qualität und "
               "nimmt dir keine Gruppe mehr von allein weg.",
         "es": "Aprender rostros funciona mejor: después de cada recorrido por "
               "la propiedad, suslik busca por su cuenta imágenes utilizables, "
               "valora su calidad y ya no descarta ningún grupo por sí solo.",
         "it": "Imparare i volti funziona meglio: dopo ogni passaggio suslik "
               "cerca da solo le immagini utilizzabili, ne valuta la qualità e "
               "non scarta più un gruppo di propria iniziativa.",
         "fr": "L'apprentissage des visages s'est amélioré : après chaque "
               "passage, suslik cherche tout seul les images utilisables, "
               "évalue leur qualité et n'écarte plus un groupe de lui-même."},
        # User 22.08. abends, Wortlaut von ihm gekuerzt ("das reicht"): EIN Satz,
        # kein Doppelpunkt-Zusatz. Gemeint ist die Vergangenheitsbetrachtung
        # (Struktur-Test .322), nicht das laufende Lernen aus dem Punkt darueber.
        # Die Uebersetzungen nehmen den PRODUKTBEGRIFF aus core/texte
        # (nav.lernlauf), nicht eine freie Neuschoepfung.
        {"en": "The learning run over past recordings got a lot better.",
         "de": "Der Lernlauf über vergangene Aufnahmen ist deutlich besser "
               "geworden.",
         "es": "El aprendizaje sobre las grabaciones anteriores ha mejorado "
               "bastante.",
         "it": "La sessione di apprendimento sulle registrazioni passate è "
               "migliorata parecchio.",
         "fr": "La session d'apprentissage sur les enregistrements passés "
               "s'est nettement améliorée."},
        # Platten-Hausarbeit: Clip-Cache (.313) + live/-Raeumer (.315).
        {"en": "suslik keeps the disk clear: it now trims clips and live "
               "pictures on its own before space gets tight.",
         "de": "suslik hält die Platte frei: Clips und Live-Bilder räumt es "
               "jetzt selbst auf, bevor es eng wird.",
         "es": "suslik mantiene el disco despejado: ahora limpia por su cuenta "
               "los clips y las imágenes en directo antes de que se quede sin "
               "sitio.",
         "it": "suslik tiene libero il disco: ora alleggerisce da solo i video "
               "e le immagini in diretta prima che lo spazio si riduca.",
         "fr": "suslik garde de la place sur le disque : il allège maintenant "
               "tout seul les séquences et les images en direct avant que "
               "l'espace ne manque."},
        # User 22.08.: der zweite Satz ("Nur auf der Heute-Seite stehen noch ein
        # paar englische Reste") kann raus — Oberbegriff statt Detail.
        {"en": "Almost everything is translated now.",
         "de": "Fast alles ist übersetzt.",
         "es": "Ya está casi todo traducido.",
         "it": "Ormai è tradotto quasi tutto.",
         "fr": "Presque tout est traduit."},
    )),
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
