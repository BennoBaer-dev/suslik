# NICHT muttersprachlich geprueft (Stand 18.09.2026): diese Fassung ist
# MASCHINELL uebersetzt (Opus-Uebersetzungsagent, in Bloecken gegen en.py
# geprueft: Schluesselmenge, Reihenfolge, Format-Platzhalter, HTML-Tagfolge,
# Randleerzeichen). Die anderen vier Fassungen haben am 19.08.2026 eine
# Muttersprachler-QS durchlaufen, diese noch NICHT. Aktiv seit der
# Registrierung in core/sprache.py (.542).
"""Finnische Uebersetzung der Referenz-Texte (gleiche Schluessel und
Reihenfolge wie en.py; Schluessel-Konvention <modul>.<block>.<rolle>,
konzept_sprache.md v2)."""
T = {
    "gesichter.titel": "Tunnetut henkilöt",
    "gesichter.kopf.knopf_lernen": "Opeta henkilöitä",
    "gesichter.kopf.hinweis_lernen":
        "ohjattu oppimisajo omille tallenteillesi (perusvaihe)",
    "gesichter.kopf.satz":
        "Kaikki opetetut henkilöt ja heidän viitekuvansa. Voit poistaa "
        "yksittäisiä kuvia, liittää lisää tuntemattomista kasvoista "
        "henkilön oman painikkeen kautta tai lähettää alta kuvan, myös "
        "aivan uudelle henkilölle.",
    "gesichter.galerie.bildzahl": "{n} kuvaa",
    "gesichter.galerie.gemischt": "kokoelma vaikuttaa sekalaiselta",
    "gesichter.galerie.vorschlag": "{n} poistoehdotusta",
    "gesichter.galerie.knopf_entfernen": "poista",
    "gesichter.galerie.knopf_aehnliche": "etsi sopivia kasvoja",
    "gesichter.galerie.knopf_qs": "Laatutarkistus",
    "gesichter.galerie.knopf_loeschen": "Poista henkilö…",
    "gesichter.galerie.knopf_umbenennen": "Nimeä henkilö uudelleen…",
    "gesichter.galerie.hinweis_leer": "ei vielä kuvia",
    "gesichter.upload.titel": "Lähetä kuva",
    "gesichter.upload.attr_person": "olemassa oleva henkilö…",
    "gesichter.upload.attr_neu": "tai uusi henkilö",
    "gesichter.upload.knopf": "Lähetä",
    "gesichter.upload.hinweis":
        "Uusi henkilö: kirjoita nimi vapaan tekstin kenttään. Ehto: "
        "buffalo_l:n on löydettävä kasvot (muuten näkyviin tulee kysymys "
        "pakottamisesta).",
    "gesichter.import.titel": "Tuonti / uudelleentäsmäytys Frigatesta",
    "gesichter.import.knopf": "Täsmäytä kasvot Frigatesta",
    "gesichter.import.hinweis":
        "Hakee viitekuvat, jotka Frigatella on ja jotka tästä kirjastosta "
        "vielä puuttuvat — inkrementaalinen, turvallista ajaa milloin "
        "tahansa (paikallisesti ei poisteta mitään). Sama tuonti kuin "
        "ohjatussa asennuksessa, nyt saatavilla ilman sen uudelleen "
        "läpikäymistä (esim. asetusten palauttamisen jälkeen).",
    "gesichter.alle_zeigen": "näytä kaikki kasvot",
    "kameras.steckbrief.knopf": "Tarkista stream-tiedot uudelleen",
    "kameras.steckbrief.hinweis":
        "Streamin tarkkuus selvitetään kameraa kohti kertaalleen ja "
        "muistetaan sen jälkeen. Käytä tätä, jos olet vaihtanut kameran "
        "streamin tai jos jokin näkyy tavoittamattomana.",
    "kameras.steckbrief.stand":
        "{n}/{ges} kameraa tarkistettu, {fehler} ei tavoitettu",
    "kameras.steckbrief.laeuft": "tarkistetaan …",
    "kameras.steckbrief.fertig":
        "tarkistetaan uudelleen seuraavassa käynnistyksessä",
    "readme.einleitung":
        "Kirjoitin tämän, koska nämä kysymykset toistuivat jatkuvasti.",
    "readme.kontakt": "Kuulen sinusta mielelläni:",
    "readme.titel": "Lue tämä ensin",
    "readme.knopf": "Lue tämä ensin",
    "readme.schliessen": "Sulje",
    "readme.zurueck": "Takaisin",
    "readme.fuss":
        "Tämä teksti näkyy kertaalleen jokaisen uudelleenkäynnistyksen "
        "jälkeen.",
    "readme.inhalt": "Sisältö",
    "readme.generell.titel": "Yleistä",
    "readme.generell.text": "Skenaariotunnistukseni nojaa Frigaten henkilöiden havaitsemiseen. Heti kun Frigate ilmoittaa henkilöstä, haen koko henkilötapahtuman. Tällainen tapahtuma on joskus muutaman sekunnin, joskus useita minuutteja pitkä. Käyn sen kokonaan läpi löytääkseni siitä jokaisen henkilön.\n\nSillä ei ole väliä, onko Frigaten oma kasvontunnistus päällä. Sitä tarvitaan vain, jos haluat täsmäyttää kasvot Frigaten kanssa.\n\nTarkistus ei koskaan käytä detect-streamia. Se käyttää tallennetta, eli parasta streamia, jonka kamera antaa Frigatelle.\n\nTarkistus käynnistyy kahdella tavalla. Joko Frigaten henkilötapahtumasta, se on skenaarion tie. Tai live-vahdista: se hakee käynnissä olevan streamin suoraan kamerasta tai Frigaten proxyn kautta, etsii siitä kasvot ja lähtee siitä liikkeelle.\n\nHenkilö tunnistetaan kolmella tavalla. Kasvoista. Koko henkilöstä, pelkästä kuvasta, ilman kasvoja. Vision-mallilla, ja se tie on vielä beta.\n\nMinulla on täällä 4K-kamerat, kuvataajuus niin korkealla kuin se menee, vähintään 15 kuvaa sekunnissa. Bittinopeus yhtä lailla. Matala bittinopeus jättää liikkuvat kasvot epäteräviksi.",
    "readme.aktuell.titel": "Mitä parhaillaan työstän",
    "readme.aktuell.text":
        "Tunnistusta, kun yhdessä tapahtumassa on useita henkilöitä. "
        "Järjestelmän pitäisi päätellä, missä kukin henkilö on kuvassa, "
        "ja ajaa kasvontunnistus erikseen jokaisen henkilön alueelle — "
        "niin että kaksi lähekkäin olevaa henkilöä eivät enää sulaudu "
        "yhdeksi päätelmäksi.",
    "readme.lernen.titel": "Miten opetan uusia kasvoja?",
    "readme.lernen.text": "Näin teen sen omassa järjestelmässäni:\n\nKasvojen oppimisajo. Uudessa järjestelmässä ensimmäinen asia. Laitteiston mukaan viimeiset 500 tapahtumaa, 1000 jos tehoa on varalla. Ohjelma hakee tapahtumat, joissa on henkilö, ryhmittelee ne ja kokoaa kuvat yhteen. Tunnetut se liittää itse. Tuntemattomat se kerää ryhmäksi, ja minä annan ryhmälle nimen. Siitä syntyy alkujoukko. Toimii vain kasvoilla, jotka tunnistettiin siististi.\n\nTänään. Kun alkujoukko on koossa, kaikki uusi tulee täältä: napsauta tapahtumaa tai henkilöä, ota kasvot käyttöön.\n\nTunnetut henkilöt. Valitse henkilö, sitten etsi sopivia kasvoja.\n\nHenkilöiden oppimisajo. Sellainen on vieressä, niitä varten, joiden kasvot eivät ole luettavissa. Kirjoitan siitä myöhemmin enemmän.\n\nLaatu. Käytän tuota välilehteä säännöllisesti. Se näyttää, kuinka hyviä henkilön kuvat todella ovat, mitkä ovat liian heikkoja ja mitkä menevät päällekkäin toisen henkilön kanssa. Liian samanlaiset otan pois.\n\nVälilehti Tuntemattomat on jäänne aiemmasta versiosta. Minä en käytä sitä.",
    "readme.persoenlich.titel": "Henkilökohtaista",
    "readme.persoenlich.text": "Tämä on puhdasta harrastusta. Senior IT-arkkitehtina minulla on hauskaa rakentaa jotain tekoälyn kanssa. Se on tehty kokonaan Claude Codella, pääosin Fable 5:llä, agentteihin Opus 5:llä.\n\nToivoisin palautetta, ja minua ilahduttaa, kun joku ottaa järjestelmän käyttöön. Se on minun palkkani.",
    "kameras.titel": "Kamerat",
    "kameras.banner.config_fehler":
        "Frigaten configia ei voitu lukea: {fehler}",
    "kameras.karte.verwenden": "käytä tätä kameraa",
    "kameras.karte.zonen_hinweis": "ei mitään merkittynä = kaikki tapahtumat",
    "kameras.karte.zonen_keine":
        "Frigatessa ei ole määritelty vyöhykkeitä — kaikki tapahtumat",
    "kameras.karte.rec_an": "tallennus ✓",
    "kameras.karte.rec_aus": "ei tallennusta",
    "kameras.karte.pill_aus": "pois Frigatessa",
    "kameras.karte.pill_keine_detektion_titel":
        "Frigate ei tee tällä streamilla henkilöiden havaitsemista "
        "&mdash; tänne ei voi tulla tapahtumia",
    "kameras.karte.pill_keine_detektion": "ei havaitsemista Frigatessa",
    "kameras.leer.titel": "Frigatesta ei löytynyt kameroita.",
    "kameras.leer.hinweis": "Tarkista, että suslik tavoittaa Frigaten API:n.",
    "kameras.fuss.knopf_speichern": "Tallenna kamerat",
    "lernen.titel": "Ehdotukset — opetettavat henkilöt",
    "lernen.kopf.titel_offen": "Ehdotukset ({n})",
    "lernen.leer.titel": "Ei avoimia opetusehdotuksia.",
    "lernen.leer.hinweis":
        "Hyvät uudet kasvot (isot, terävät, edestä, varmasti tunnistetut "
        "tai selvästi vieraat) ilmestyvät tänne automaattisesti analyysin "
        "jälkeen.",
    "lernen.karte.unbekannt": "Tuntematon/vieras",
    "lernen.karte.metrik_voll":
        "score {score} · uutuus {novelty} · {bw}×{bh}px · edestä {front} "
        "· terävyys {sharp}",
    "lernen.karte.metrik_kurz": "score {score}",
    "lernen.karte.link_video": "Video",
    "lernen.karte.knopf_add_person": "Lisää nimellä {person}",
    "lernen.karte.attr_person": "henkilönä…",
    "lernen.karte.attr_neu": "tai uusi henkilö",
    "lernen.karte.knopf_add": "Lisää",
    "lernen.karte.knopf_ablehnen": "Hylkää",
    "lernen.galerie.titel": "Viitevarasto (Master)",
    "lernen.galerie.bildzahl": "{n} viitettä",
    "lernen.upload.titel_abschnitt": "Lähetys",
    "lernen.upload.titel": "Lähetä oma kuva Masteriin",
    "lernen.upload.attr_person": "olemassa oleva henkilö…",
    "lernen.upload.attr_neu": "tai uusi henkilö",
    "lernen.upload.knopf": "Lähetä",
    "lernen.upload.hinweis":
        "Uusi henkilö (esim. Alex): kirjoita nimi vapaan tekstin "
        "kenttään. Ehto: buffalo_l:n on löydettävä kasvot (muuten "
        "näkyviin tulee kysymys pakottamisesta). PNG muunnetaan JPEG:ksi. "
        "Lähetä useita kuvia eri kuvakulmista peräkkäin.",
    "areas.titel": "Alueet",
    "areas.kopf.sprung": "Hyppää näkymään:",
    "areas.verwaltung.titel": "Hallitse alueita",
    "areas.verwaltung.camzahl.eins": "{n} kamera",
    "areas.verwaltung.camzahl.viele": "{n} kameraa",
    "areas.verwaltung.attr_entfernen":
        "poista tämä alue — sen kamerat siirtyvät takaisin Defaultiin",
    "areas.verwaltung.attr_neu": "uuden alueen nimi",
    "areas.verwaltung.knopf_anlegen": "Lisää alue",
    "areas.verwaltung.titel_zuweisen": "Liitä kamerat",
    "areas.verwaltung.satz_zuweisen":
        "Yksi kamera kuuluu täsmälleen yhteen alueeseen; kaikki "
        "liittämätön jää Defaultiin. Tallennus ei vaadi palvelun "
        "uudelleenkäynnistystä.",
    "areas.verwaltung.pill_nicht_gesehen": "ei nähty",
    "areas.verwaltung.attr_nicht_gesehen":
        "liitetty aiemmin, ei juuri nyt Frigatessa",
    "areas.verwaltung.hinweis_keine_kameras":
        "Kameroita ei vielä tunneta — yhdistä ensin Frigate (Asetukset).",
    "areas.verwaltung.knopf_speichern": "Tallenna alueet",
    "areas.kettung.titel": "Kuinka pitkälle käynti ulottuu",
    "areas.kettung.satz":
        "Käynti on yksi kulku tonttisi läpi: tapahtumat ketjuuntuvat niin "
        "kauan kuin niiden väli pysyy alle kohtauksen välin. Valitse "
        "alueittain, kuinka pitkälle ketju saa ulottua. Tämä muuttaa vain "
        "ryhmittelyä — analyysi katsoo aina jokaista kameraa erikseen, ja "
        "näkymä pysyy alueittain ryhmiteltynä.",
    "areas.kettung.grundstueck": "yksi käynti koko tontille",
    "areas.kettung.area": "yksi käynti aluetta kohti",
    "areas.kettung.kamera": "jokainen kamera erikseen",
    "benachrichtigungen.titel": "Ilmoitukset",
    "benachrichtigungen.felder.secret_gesetzt":
        "•••• tallennettu — tyhjä säilyttää arvon",
    "benachrichtigungen.felder.secret_leer": "ei asetettu",
    "benachrichtigungen.felder.option_an": "päällä",
    "benachrichtigungen.felder.option_aus": "pois",
    "benachrichtigungen.alerts.titel": "Ilmoituskäytäntö",
    "benachrichtigungen.alerts.hinweis":
        "Mitkä päätelmäluokat laukaisevat ilmoituksen — jokaisella "
        "kanavalla (Pushover, Telegram, MQTT-kohtaustopicit). Tunnistetun "
        "henkilön pushia ohjaa alla oleva läsnäolokytkin; "
        "MQTT-datatopicit (erkennung, heartbeat) julkaisevat aina, kun "
        "MQTT-julkaisu on päällä.",
    "benachrichtigungen.kategorien.widerspruch":
        "suslik vahvistaa eri henkilön kuin Frigate",
    "benachrichtigungen.kategorien.frigate_nur":
        "Frigate nimesi jonkun, suslik ei nähnyt käyttökelpoisia kasvoja",
    "benachrichtigungen.kategorien.wir_nur":
        "suslik tunnisti jonkun, Frigate ei",
    "benachrichtigungen.kategorien.beide_unknown":
        "kumpikaan puoli ei tunnistanut kasvoja",
    "benachrichtigungen.kategorien.erkannt": "tunnettu henkilö tunnistettiin",
    "benachrichtigungen.kategorien.fremd_verdacht":
        "käyttökelpoiset kasvot, mutta kukaan ei vahvistanut "
        "(mahdollisesti vieras)",
    "benachrichtigungen.kategorien.unbekannt_schwach":
        "kasvot liian heikot tai pienet tunnistamiseen",
    "benachrichtigungen.alerts.stil_label": "Ilmoitusten tekstityyli:",
    "benachrichtigungen.alerts.stil_worte": "selkeät sanat",
    "benachrichtigungen.alerts.stil_worte_zahlen":
        "sanat + raa'at score-arvot",
    "benachrichtigungen.alerts.stil_hinweis":
        "miten ilmoitukset kuvaavat osuman (selkeät sanat on oletus; "
        "raa'at kosini-/score-luvut vain jos haluat ne takaisin)",
    "benachrichtigungen.alerts.label_anwesenheit_push": "Läsnäolo-push:",
    "benachrichtigungen.alerts.label_alert_cooldown":
        "Ilmoitusten rauhoitusaika (s):",
    "benachrichtigungen.alerts.label_anwesenheit_cooldown":
        "Läsnäolon rauhoitusaika (s):",
    "benachrichtigungen.alerts.label_szene_karenz":
        "Kohtauksen armonaika (s):",
    "benachrichtigungen.pushover.label_token": "Token:",
    "benachrichtigungen.pushover.label_user": "User key:",
    "benachrichtigungen.pushover.knopf_test": "Testaa Pushover",
    "benachrichtigungen.pushover.zustand_an":
        "Aktiivinen — token ja user key on asetettu.",
    "benachrichtigungen.pushover.zustand_aus":
        "Pois — token tai user key puuttuu, tällä kanavalla ei lähetetä "
        "mitään.",
    "benachrichtigungen.pushover.zustand_pause":
        "Tauolla — Pushover hylkäsi {n} ilmoitusta peräkkäin. Tallenna "
        "asetukset tai lähetä onnistunut testi, niin lähetys jatkuu.",
    "benachrichtigungen.telegram.label_modus": "Tila:",
    "benachrichtigungen.telegram.hinweis_modus":
        "aus=pois · ha=Home Assistantin kautta · direkt=suora botti · "
        "beide=molemmat",
    "benachrichtigungen.telegram.label_inhalt": "Liite:",
    "benachrichtigungen.telegram.hinweis_inhalt":
        "video=lyhyt leike, kuva jos ei saatavilla · bild=vain kuva (ei "
        "transkoodausta — säästää heikkoa laitteistoa)",
    "benachrichtigungen.telegram.label_bot_token": "Botin token:",
    "benachrichtigungen.telegram.label_chat_id": "Chat-ID:",
    "benachrichtigungen.telegram.label_cooldown":
        "Tuntemattoman rauhoitusaika (s):",
    "benachrichtigungen.telegram.knopf_test": "Testaa Telegram",
    "benachrichtigungen.mqtt.label_publish": "Julkaise tunnistus-topicit:",
    "benachrichtigungen.mqtt.label_host": "Host:",
    "benachrichtigungen.mqtt.label_port": "Portti:",
    "benachrichtigungen.mqtt.label_user": "Käyttäjä:",
    "benachrichtigungen.mqtt.label_password": "Salasana:",
    "benachrichtigungen.mqtt.label_topic_praefix": "Topic-etuliite:",
    "benachrichtigungen.mqtt.knopf_test": "Testaa MQTT",
    "benachrichtigungen.fuss.knopf_speichern":
        "Tallenna + käynnistä uudelleen",
    "aehnliche.kopf.titel": "Sopivat kasvot henkilölle {person}",
    "aehnliche.kopf.satz":
        "Kaksi lähdettä: tuntemattomat kasvot, jotka muistuttavat "
        "henkilöä {person}, ja uudet kasvot tapahtumista, joissa henkilö "
        "{person} jo tunnistettiin varmasti. Merkitse ja ota käyttöön.",
    "aehnliche.kopf.link_zurueck": "takaisin",
    "aehnliche.unbekannt.titel": "Tuntemattomista kasvoista",
    "aehnliche.unbekannt.suche_titel":
        "Haku käynnissä — viitteet luetaan uudelleen.",
    "aehnliche.unbekannt.kein_cache": "Viitteitä ei ole vielä luettu sisään.",
    "aehnliche.unbekannt.kein_cache_hinweis":
        "Tämä lista tarvitsee viiteindeksin. Viitteiden tarkistus "
        "kirjoittaa sen — sen jälkeen tänne tulee tulos.",
    "aehnliche.unbekannt.knopf_pruefen": "tarkista viitteet",
    "aehnliche.unbekannt.hinweis_leer":
        "Ei samankaltaisia tuntemattomia kasvoja varastossa.",
    "aehnliche.unbekannt.aehnlichkeit": "samankaltaisuus {sim}",
    "aehnliche.unbekannt.knopf_hinzu": "Lisää valitut henkilölle {person}",
    "aehnliche.vorschlaege.titel":
        "Uudet kasvot tunnistetuista tapahtumista (7 päivää)",
    "aehnliche.vorschlaege.suche_titel":
        "Haku käynnissä — tunnistettuja tapahtumia käydään läpi.",
    "aehnliche.vorschlaege.nie_gesucht": "Ei vielä haettu.",
    "aehnliche.vorschlaege.nie_gesucht_hinweis":
        "Haku tunnistettujen tapahtumien yli käynnistyy napsautuksesta, "
        "ei taustalla.",
    "aehnliche.vorschlaege.stand_leer": "haettu viimeksi {stand}",
    "aehnliche.suche.rechnet":
        "Haku on käynnissä; sivu latautuu itsestään uudelleen, kun tulos "
        "on valmis.",
    "aehnliche.suche.wartet_platz":
        "Odottaa vapaata analyysipaikkaa ({belegt}/{plaetze} käytössä); "
        "sivu latautuu itsestään uudelleen, kun tulos on valmis.",
    "aehnliche.vorschlaege.kachel_zeile": "{wann} · {kamera} · sim {sim}",
    "aehnliche.vorschlaege.titel_empfohlen": "Suositellut",
    "aehnliche.vorschlaege.titel_neutral":
        "Neutraali — katso kuva ennen käyttöönottoa",
    "aehnliche.vorschlaege.hinweis_neutral":
        "Selvästi tämä henkilö, mutta osuma on luottamuskynnyksen alla "
        "tai rajaus on pienempi / epäterävämpi — katse ratkaisee.",
    "aehnliche.vorschlaege.knopf_alle":
        "Ota kaikki suositellut käyttöön ({n})",
    "aehnliche.vorschlaege.knopf_gewaehlt":
        "Ota valitut käyttöön henkilölle {person}",
    "aehnliche.vorschlaege.knopf_neu": "hae uudelleen",
    "aehnliche.vorschlaege.fuss":
        "tilanne {stand} · suositeltu = varmasti {person} + viitelaatu",
    "aehnliche.vorschlaege.hinweis_leer":
        "Tunnistetuista tapahtumista ei löytynyt sopivaa.",
    "aehnliche.vorschlaege.hinweis_leer_kriterien":
        "Kriteerit: yksiselitteisesti tämä henkilö, uusi varastoon "
        "verrattuna, riittävän iso ja terävä.",
    "aehnliche.vorrat.titel": "Uutta oppimisvarastosta",
    "aehnliche.vorrat.hinweis":
        "Laadukkaat kasvot, jotka oppimisajo keräsi, arvioitu "
        "viitteettömällä laatumitalla ja skenaarion konsensuksella. Ne "
        "pysyvät paikallisina eikä niitä koskaan viedä Frigateen.",
    "aehnliche.vorrat.kachel_zeile":
        "{wann} · {kamera} · osuma {sim} · laatu {norm}",
    "aehnliche.vorrat.auch_anker": "myös kasvoryhmässä",
    "aehnliche.vorrat.knopf_gewaehlt": "Lisää valitut henkilölle {person}",
    "frigate.verbindung.titel": "Yhteys",
    "frigate.verbindung.satz":
        "Ohjelmani lukee tapahtumat ja snapshotit Frigatestasi sen "
        "HTTP-API:n kautta — Frigaten puolelle ei asenneta mitään.",
    "frigate.verbindung.knopf_aendern": "Muuta yhteyttä",
    "frigate.verbindung.knopf_speichern": "Tallenna &amp; käynnistä uudelleen",
    "frigate.verbindung.knopf_abbrechen": "Peruuta",
    "frigate.verbindung.hinweis_speichern":
        "tallennus käynnistää palvelun hetkeksi uudelleen; tämä ruutu "
        "näyttää sen jälkeen livenä, vastaako uusi osoite",
    "frigate.kameras.titel": "Kamerat",
    "frigate.kameras.satz":
        "Mitä Frigaten kameroita tämä ohjelma tarkkailee ja mitkä "
        "vyöhykkeet lasketaan. Kaikki muu jätetään huomiotta.",
    "frigate.kameras.beweis_keine_auswahl":
        "kameravalintaa ei ole vielä tallennettu — jokaista Frigaten "
        "tarjoamaa kameraa käytetään",
    "frigate.kameras.knopf": "Hallitse kameroita",
    "frigate.sync.titel": "Täsmäytys",
    "frigate.sync.satz":
        "Pitää kasvokirjastot molemmin puolin samassa tahdissa: lähetä "
        "läpikäydyt kasvot Frigateen, tuo se, mikä on vain Frigatella "
        "&mdash; aina sinun päätöksesi, ei koskaan automaattisesti.",
    "frigate.sync.knopf": "Käy läpi &amp; täsmäytä",
    "frigate.fr.titel": "Frigaten oma kasvontunnistus",
    "frigate.fr.satz":
        "Myös Frigate osaa tunnistaa kasvot. Tämä ohjelma toimii sen "
        "kanssa tai ilman sitä &mdash; kytkin on Frigaten configissa, ja "
        "se luetaan tästä livenä, jotta tiedät mihin täsmäytys juuri nyt "
        "pystyy.",
    "frigate.fr.beweis_unbekannt": "tila tuntematon — {detail}",
    "frigate.js.url_fehlt": "syötä Frigaten URL",
    "frigate.js.fehler": "virhe:",
    "ereignisliste.offen.titel": "Avoimet nimettävät tapaukset ({n})",
    "ereignisliste.offen.satz":
        "Täyttyy automaattisesti: kaikki tapahtumat, joissa on kasvot, "
        "joita kukaan ei ole vahvistanut ja joita et ole vielä nimennyt. "
        "Ensin tulevat ne, joiden lähellä ei tunnistettu ketään — ne "
        "kannattaa katsoa. Nimeämisen jälkeen kortti haalistuu ja katoaa "
        "seuraavassa latauksessa.",
    "ereignisliste.offen.frigate_mit": "Frigate: {label} {score}",
    "ereignisliste.offen.frigate_ohne": "Frigate: —",
    "ereignisliste.offen.zeile_faces": "{n} kasvoa · paras: {beste}",
    "ereignisliste.offen.link_video": "Video",
    "ereignisliste.offen.kontext_erkannt":
        "tunnistettu samassa aikaikkunassa: {wer}",
    "ereignisliste.offen.kontext_fehlt": "ei vahvistettua tunnistusta lähellä",
    "ereignisliste.blaettern.neuer": "← uudemmat",
    "ereignisliste.blaettern.aelter": "vanhemmat →",
    "ereignisliste.offen.blaettern_stand": "Sivu {seite}/{max} ({n} avointa)",
    "ereignisliste.offen.schwach_versteckt.eins":
        "{n} heikkojen kasvojen tapahtuma piilotettu — todennäköisesti ei "
        "käyttökelpoisia kasvoja (lähellä ei myöskään vahvistettu "
        "mitään).",
    "ereignisliste.offen.schwach_versteckt.viele":
        "{n} heikkojen kasvojen tapahtumaa piilotettu — todennäköisesti "
        "ei käyttökelpoisia kasvoja (lähellä ei myöskään vahvistettu "
        "mitään).",
    "ereignisliste.offen.schwach_zeigen": "näytä ne",
    "ereignisliste.offen.schwach_alle":
        "heikkojen kasvojen tapahtumat näytetään mukana —",
    "ereignisliste.offen.schwach_zurueck":
        "takaisin niihin, jotka kannattavat",
    "ereignisliste.offen.leer_titel": "Ei mitään avointa — kaikki nimetty.",
    "ereignisliste.offen.leer_hinweis":
        "Uudet vahvistamattomat tapahtumat, joissa on kasvot, ilmestyvät "
        "tänne automaattisesti.",
    "ereignisliste.titel": "Tapahtumat",
    "ereignisliste.filter.alle_areas": "kaikki alueet",
    "ereignisliste.filter.alle_kameras": "kaikki kamerat",
    "ereignisliste.filter.alle_personen": "kaikki henkilöt",
    "ereignisliste.filter.alle_kategorien": "kaikki kategoriat",
    "ereignisliste.filter.knopf": "Suodata",
    "ereignisliste.filter.reset": "nollaa",
    "ereignisliste.tabelle.blaettern_stand":
        "Sivu {seite}/{max} ({n} tapahtumaa)",
    "ereignisliste.tabelle.kopf_zeit": "Aika",
    "ereignisliste.tabelle.kopf_kamera": "Kamera",
    "ereignisliste.tabelle.kopf_kategorie": "Kategoria",
    "ereignisliste.tabelle.kopf_crop": "Rajaus",
    "ereignisliste.tabelle.kopf_gt": "Vahvista tai korjaa (GT)",
    "ereignisliste.tabelle.frigate_zelle": "{label} {score} (cos {cos})",
    "ereignisliste.tabelle.link_log": "loki",
    "ereignisliste.tabelle.link_video": "video",
    "ereignisliste.tabelle.attr_unvollstaendig":
        "leike epätäydellinen — arvioitu luettavasta osasta",
    "ereignisliste.tabelle.attr_kein_crop":
        "tälle tapahtumalle ei säilytetty käyttökelpoisia kasvoja",
    "konfiguration.kette.gesicht_titel": "Kasvot",
    "konfiguration.kette.gesicht_kosten":
        "perusanalyysi tallennetulle leikkeelle — aina päällä",
    "konfiguration.kette.gesicht_zeitpunkt": "tapahtumaa kohti",
    "konfiguration.kette.person_titel": "Henkilö (keho)",
    "konfiguration.kette.person_kosten":
        "kallein paikallinen vaihe (kehon embedding laitteistollasi)",
    "konfiguration.kette.person_zeitpunkt":
        "tapahtumaa kohti, päätetään käynnin päätelmästä",
    "konfiguration.kette.vision_titel": "Vision",
    "konfiguration.kette.vision_kosten":
        "yksi pyyntö käyntiä kohti määrittämääsi Vision-päätepisteeseen",
    "konfiguration.kette.vision_zeitpunkt": "käynnin päätteeksi",
    "konfiguration.kette.immer_an": "aina",
    "konfiguration.kette.immer_hinweis": "(ei tänään kytkettävissä pois)",
    "konfiguration.kette.gesicht_erkl":
        "kasvotie on jokaisen analyysin selkäranka — henkilö ja Vision "
        "riippuvat sen käyntipäätelmästä",
    "konfiguration.kette.grund_person":
        "koulutettua henkilömallia ei ole vielä otettu käyttöön",
    "konfiguration.kette.grund_vision": "Vision-tunnistus on kytketty pois",
    "konfiguration.kette.grund_aus": "kytketty täällä pois",
    "konfiguration.kette.status_aus": "tila: ei käynnissä ({grund})",
    "konfiguration.kette.zeile_kosten": "kustannus: {kosten}",
    "konfiguration.kette.titel": "Tunnistusketju",
    "konfiguration.kette.satz":
        'Mitkä tunnistimet ajetaan ja missä järjestyksessä. Ehto '
        '"nur_wenn_gesicht_leer" tarkoittaa: vaihe ajetaan vain, kun '
        'kasvotie EI voinut vahvistaa kaikkia käynnillä olleita — '
        'päätetään koko käynnistä, ei koskaan yksittäisestä tapahtumasta. '
        'Järjestyksen muuttaminen itse on myöhempi vaihe; tänään ketju '
        'alkaa aina kasvotiestä.',
    "konfiguration.knopf_speichern": "Tallenna + käynnistä uudelleen",
    "konfiguration.kette_blatt.hinweis":
        "Muutokset kirjataan (config_audit.jsonl); tallennuksen jälkeen "
        "palvelu käynnistyy siististi uudelleen.",
    "antwort.support_token_neu":
        "uusi support-token luotu — vanha on mitätön; kopioi se nyt, se "
        "näytetään vain tämän yhden kerran",
    "konfiguration.neustart.titel": "Käynnistä palvelu uudelleen",
    "konfiguration.neustart.satz":
        "Käynnistää tämän palvelun uudelleen paikallaan (kontti jatkaa "
        "käyntiä, kaikki data säilyy). Käytä tätä, jos käsittely näyttää "
        "jumittavan; avoimet tapahtumat otetaan uudelleen käsittelyyn "
        "käynnistyksen jälkeen.",
    "konfiguration.neustart.knopf": "Käynnistä nyt uudelleen",
    "konfiguration.neustart.frage":
        "Käynnistetäänkö palvelu nyt uudelleen? Käsittely pysähtyy "
        "pariksi sekunniksi.",
    "antwort.neustart":
        "Käynnistys käynnissä — tämä sivu vastaa muutamassa sekunnissa "
        "uudelleen.",
    "konfiguration.support.titel": "Etätuen pääsy",
    "konfiguration.support.satz":
        "Vain luku -lataus nimetyistä alueista (lokit, maskattu config, "
        "kasvot, oppimisajot, kehomateriaali, tilatiedostot) sille, jolla "
        "on support-token. Kytkin support_zugriff on alla olevassa "
        "taulukossa, oletuksena pois. Jokainen pyyntö kirjataan palvelun "
        "lokiin. Kasvo- ja kehoalueet sisältävät kuvia oikeista ihmisistä "
        "— luovuta token harkiten. Ilman TLS:ää tämän palvelun edessä "
        "token kulkee selkokielisenä. Versiosta 0.1.0.395 lähtien token "
        "sallii myös yhden toiminnon: tämän palvelun "
        "uudelleenkäynnistyksen etänä (POST /support/restart).",
    "konfiguration.support.token_gesetzt": "Support-token on asetettu.",
    "konfiguration.support.token_fehlt": "Ei vielä support-tokenia.",
    "konfiguration.support.knopf_token": "Luo uusi token",
    "konfiguration.support.einmal_hinweis":
        "Token näkyy tässä täsmälleen kertaalleen luonnin jälkeen — ota "
        "se talteen; sen jälkeen näytetään enää ••• .",
    "konfiguration.titel": "Lisäasetukset",
    "konfiguration.kopf.satz1":
        "Muutokset kirjataan (config_audit.jsonl); tallennuksen jälkeen "
        "palvelu käynnistyy siististi uudelleen (se odottaa käynnissä "
        "olevan analyysin valmistumista).",
    "konfiguration.feld.option_an": "päällä",
    "konfiguration.feld.option_aus": "pois",
    "konfiguration.frigate_auth.titel": "Frigaten kirjautuminen (valinnainen)",
    "konfiguration.frigate_auth.satz":
        "Tarvitaan vain, jos Frigatesi vaatii kirjautumisen — näin on sen "
        "todennetussa portissa (8971), ei sisäisessä (5000). Jätä "
        "molemmat kentät tyhjiksi, eikä mikään muutu: suslik puhuu "
        "Frigaten kanssa täsmälleen kuten tähän asti.",
    "konfiguration.frigate_auth.erkl_user":
        "Frigate-tilin käyttäjätunnus. Tyhjä = ei kirjautumista lainkaan; "
        "tyhjennys poistaa myös tallennetun salasanan",
    "konfiguration.frigate_auth.erkl_password":
        "tilin salasana. Se tallennetaan muiden asetustesi mukana "
        "hakemistoon /data eikä sitä näytetä enää koskaan — jätä kenttä "
        "tyhjäksi, niin se säilyy",
    "konfiguration.frigate_auth.erkl_tls":
        "tarkista Frigaten TLS-varmenne. Frigaten todennettu portti tuo "
        "mukanaan itse allekirjoitetun varmenteen, joten kytke tämä pois, "
        "jos otat siihen yhteyden https:llä etkä ole vaihtanut "
        "varmennetta",
    "konfiguration.frigate_auth.pw_gesetzt":
        "tallennettu — jätä tyhjäksi, niin se säilyy",
    "konfiguration.frigate_auth.pw_leer": "ei salasanaa tallennettuna",
    "konfiguration.abschnitt_alle": "Kaikki parametrit",
    "konfiguration.tabelle.kopf_parameter": "Parametri",
    "konfiguration.tabelle.kopf_wert": "Arvo",
    "konfiguration.tabelle.kopf_bedeutung": "Merkitys",
    "konfiguration.knopf_setup": "Aja ohjattu asennus uudelleen",
    "konfiguration.abschnitt_readonly": "Vain luku (konsoli/yaml)",
    "lernanker.eimer.ok": "siisti",
    "lernanker.eimer.unbestaetigt": "vahvistamaton",
    "lernanker.eimer.zu_duenn": "ohut",
    "lernanker.eimer.hart": "sekalainen",
    "lernanker.bin.frontal": "Edestä",
    "lernanker.bin.links": "Katse vasemmalle",
    "lernanker.bin.rechts": "Katse oikealle",
    "lernanker.kachel.attr_clip":
        "{kamera} · det {det} · napsautus avaa leikkeen",
    "lernanker.kachel.attr_kurz": "{kamera} · det {det}",
    "lernanker.kachel.attr_klick": "avaa leike",
    "lernanker.kachel.grund_fehlt": "ei arvioitu",
    "lernanker.detail.gruppe": "Ryhmä {pos}/{gesamt}",
    "lernanker.detail.frage": "Kuka tämä on?",
    "lernanker.badge.stuetz": "{n} kasvoa ({phys} fyysistä)",
    "lernanker.badge.faces": "{n} kasvoa",
    "lernanker.badge.durchgaenge": "{n} käyntiä",
    "lernanker.badge.tage": "{n} pv: {spanne}",
    "lernanker.badge.marge": "marginaali {marge}",
    "lernanker.link_zurueck": "takaisin kaikkiin ryhmiin",
    "lernanker.detail.hinweis_klick":
        "napsauta kasvoja, niin sen leike avautuu",
    "lernanker.detail.hinweis_auswahl":
        "napsauta kuvaa valitaksesi sen tai poistaaksesi valinnan",
    "lernanker.detail.hinweis_pfeil": "pieni &#9654; avaa leikkeen",
    "lernanker.detail.weiter": "Seuraava ryhmä &#8230;",
    "lernanker.detail.pflege_hinweis": "viitteiden hoito on Laatu-sivulla",
    "lernanker.detail.verworfen":
        "sinun poistamasi — kuvat ovat poissa; ryhmä jää tähän listaan "
        "vain merkinnäksi",
    "lernanker.detail.dublette_hinweis":
        "kaksoiskappaleiden tarkistus ei käytettävissä (ankkuri on "
        "vanhempi kuin embeddingien tallennus) — fyysiset "
        "kaksoiskappaleet suodatetaan silti",
    "lernanker.bekannt.system": "jo järjestelmässäsi",
    "lernanker.bekannt.anker": "nimetty toisessa ryhmässä",
    "lernanker.detail.empfohlen": "Suositellut — {bin} ({n})",
    "lernanker.detail.nicht_empfohlen":
        "Ei suositellut ({n}) — pysyvät näkyvissä, syy jokaisessa kuvassa",
    "lernanker.detail.gewaehlt": "Valitut — {bin} ({n})",
    "lernanker.detail.nicht_gewaehlt": "Ei valitut ({n}) — pysyvät näkyvissä",
    "lernanker.grund.bildpruefung": "ei läpäissyt kuvatarkistusta",
    "lernanker.grund.zu_dunkel":
        "liian tumma (kirkkaus {luma} — tarvitaan {min}+)",
    "lernanker.grund.ueberbelichtet":
        "ylivalottunut (kirkkaus {luma} — enintään {max})",
    "lernanker.grund.dublette_phys":
        "kaksoiskappale (sama kamera ja sama rajaus)",
    "lernanker.grund.fast_gleich": "lähes sama kuin {datei}",
    "lernanker.grund.bin_limit":
        "katsesuunnan yläraja saavutettu ({k} säilytetty)",
    "lernanker.detail.skip_weiter": "Ohita tämä ryhmä",
    "lernanker.detail.skip_zurueck": "Ohita — takaisin ryhmiin",
    "lernanker.detail.knopf_ja": "Kyllä, se on {name}",
    "lernanker.detail.knopf_andere": "Joku muu &#8230;",
    "lernanker.detail.knopf_benennen_easy": "Nimeä tämä ryhmä &#8230;",
    "lernanker.detail.knopf_alle": "Valitse kaikki suositellut",
    "lernanker.detail.knopf_keine": "Poista kaikki valinnat",
    "lernanker.detail.attr_name": "henkilön nimi (uusi tai olemassa oleva)",
    "lernanker.detail.knopf_benennen": "Nimeä tämä ryhmä",
    "lernanker.detail.knopf_adopt": "Ota tunnistukseen käyttöön",
    "lernanker.js.fehler": "virhe:",
    "lernanker.js.nicht_uebernommen": "ei otettu käyttöön",
    "lernanker.js.nicht_gespeichert": "ei tallennettu",
    "lernanker.liste.frage_lauf":
        "Poistetaanko ajo {lid} ja kaikki sen data? Tämä poistaa sen {n} "
        "ryhmää lopullisesti — myös nimetyt ja hylätyt — ja kaikki "
        "kerätyt kuvat. Tunnistukseen jo käyttöön otetut viitteet "
        "säilyvät. Tätä ei voi peruuttaa.",
    "lernanker.liste.frage_alle":
        "Poistetaanko KAIKKI {alt} vanhaa ajoa, niiden {n} ryhmää ja "
        "kaikki kerätyt kuvat? Vain uusin ajo {neuester} säilyy. "
        "Tunnistukseen jo käyttöön otetut viitteet säilyvät. Tätä ei voi "
        "peruuttaa.",
    "lernanker.liste.knopf_alte":
        "Poista kaikki vanhat ajot ({neuester} säilyy)",
    "lernanker.liste.lauf_zeile":
        "Poista yksi ajo — poistaa kaikki sen ryhmät ja kerätyt kuvat "
        "lopullisesti (jo käyttöön otetut viitteet säilyvät):",
    "lernanker.liste.verworfen":
        "{n} ryhmää sinun poistamana (kuvat poissa, jäljellä vain "
        "merkintä)",
    "lernanker.titel": "Ankkuriryhmät",
    "lernanker.liste.leer":
        "Ei vielä ankkureita — oppimisajo rakentaa ne (Valmistelu → "
        "Keräys → Ryhmittely).",
    "lernanker.liste.leer_link": "Avaa oppimisajon sivu",
    "lernanker.liste.kopf":
        "{n} ryhmää {ges} ankkurikelpoisesta kasvosta — {ok} siistiä, "
        "{rest} läpikäyntiin (himmennetty, syy näkyy merkissä). Avaa "
        "ryhmä, käy se läpi ja nimeä se — nimetyt ryhmät otetaan "
        "tunnistukseen käyttöön heti siellä (painike Ota käyttöön).",
    "lernanker.liste.kopf_link": "Takaisin oppimisajoon",
    "lernanker.liste.mehr": "+{n} kasvoa lisää",
    "lernanker.liste.dublette":
        "sama ryhmä kuin {anker} — uudempi ajo keräsi sen uudelleen; "
        "nimeä se siellä",
    "lernanker.liste.knopf_review": "Käy nimeäminen läpi",
    "lernanker.liste.knopf_view": "Katso ryhmä",
    "lernanker.liste.knopf_benennen": "Nimeä nämä {n} kasvoa",
    "lernanker.liste.frage_verwerfen":
        "Poistetaanko tämä ryhmä? Sen kuvat poistetaan. Tätä ei voi "
        "peruuttaa.",
    "lernanker.liste.frage_verwerfen_benannt":
        "Poistetaanko tämä ryhmä? Sen kuvat poistetaan ja odottava "
        "nimeäminen hylätään. Tätä ei voi peruuttaa.",
    "lernanker.liste.knopf_verwerfen": "Poista",
    "syncauswahl.titel": "Käy läpi &amp; täsmäytä — viitteet Frigateen",
    "syncauswahl.kopf.satz":
        "Frigate ajaa jokaisen lähetetyn viitteen oman kasvodetektorinsa "
        "läpi ja hylkää kuvat, joista se ei löydä kasvoja. Tämä sivu "
        "tarkistaa ensin saman asian, näyttää sinulle jokaisen ehdokkaan "
        "ja lähettää vain sen, minkä merkitset.",
    "syncauswahl.fehler.titel": "Ehdokkaat eivät ole käytettävissä",
    "syncauswahl.fehler.satz":
        "Ehdokaslista tarvitsee tavoitettavan Frigaten — sen "
        "kasvokirjasto on vertailun toinen puoli.",
    "syncauswahl.link_diagnose_auf": "avaa diagnoosi",
    "syncauswahl.link_diagnose": "diagnoosi",
    "syncauswahl.link_system": "takaisin Järjestelmään",
    "syncauswahl.kachel.frigate_abgelehnt": "Frigate hylkäsi: {fehler}",
    "syncauswahl.kachel.pruefe": "tarkistetaan …",
    "syncauswahl.kachel.vorpruefung_ok": "esitarkistus ok",
    "syncauswahl.kachel.wohl_abgelehnt":
        "hylättäisiin todennäköisesti: {grund}",
    "syncauswahl.kachel.kein_gesicht": "kasvoja ei havaittavissa",
    "syncauswahl.kachel.kein_grund": "syytä ei ilmoitettu",
    "syncauswahl.kachel.senden": "lähetä",
    "syncauswahl.kachel.knopf_skip": "ohita",
    "syncauswahl.kachel.attr_skip":
        "Älä koskaan lähetä tätä kuvaa — jää muistiin, myös automaattinen "
        "täsmäytys ohittaa sen",
    "syncauswahl.kachel.knopf_restore": "palauta",
    "syncauswahl.kachel.attr_restore":
        "Aseta tämä kuva takaisin ehdokaslistalle",
    "syncauswahl.geloescht.satz_import":
        "tuli Frigatesta ja on siellä nyt poissa",
    "syncauswahl.geloescht.satz_export":
        "lähetettiin täsmälleen tällä nimellä ja on siellä nyt poissa",
    "syncauswahl.geloescht.badge": "poistettu Frigatesta",
    "syncauswahl.knopf_anbieten": "tarjoa uudelleen",
    "syncauswahl.geloescht.attr_anbieten":
        "Takaisin ehdokaslistalle — seuraava täsmäytys (käsin tai "
        "automaattinen) lähettää sen uudelleen",
    "syncauswahl.geloescht.knopf_respekt": "kunnioita poistoa",
    "syncauswahl.geloescht.attr_respekt":
        "Muista, että tämän kuvan on pysyttävä Frigaten ulkopuolella",
    "syncauswahl.api.badge": "{person} — lähetetty aiemmin",
    "syncauswahl.api.attr_anbieten":
        "Takaisin ehdokaslistalle (lähettää toisen kopion, jos Frigatella "
        "on ensimmäinen vielä)",
    "syncauswahl.fr.titel_unbekannt": "Frigaten kasvontunnistus: tuntematon",
    "syncauswahl.fr.satz_unbekannt":
        "suslik ei juuri nyt saanut luettua sitä Frigatesta — {detail}. "
        "Lähetys voi silti onnistua; viimeinen sana on joka tapauksessa "
        "Frigatella.",
    "syncauswahl.fr.titel_an": "Frigaten kasvontunnistus: päällä",
    "syncauswahl.fr.satz_an":
        "(luettu Frigatesta tämän sivun latautuessa) — se ottaa lähetetyt "
        "viitteet vastaan.",
    "syncauswahl.fr.titel_aus": "Frigaten kasvontunnistus: pois",
    "syncauswahl.bilanz.titel": "Yhteenveto",
    "syncauswahl.bilanz.hauptzeile":
        "viitekuvaa · {beide} jo Frigatessa · {bereit} valmiina siirtoon",
    "syncauswahl.bilanz.abgelehnt": "{n} Frigaten hylkäämää",
    "syncauswahl.bilanz.geloescht": "{n} poistettu Frigatesta",
    "syncauswahl.bilanz.exportiert":
        "{n} lähetetty aiemmin (Frigate nimesi ne uudelleen)",
    "syncauswahl.bilanz.abgewaehlt": "{n} valinta poistettu",
    "syncauswahl.bilanz.vorrat":
        "{n} varastoviitettä vain paikallisesti (embedding-pohjaisia, ei "
        "siirrettävissä)",
    "syncauswahl.bilanz.nur_frigate": "{n} vain Frigatessa",
    "syncauswahl.bilanz.je_person": "Frigatessa, henkilöä kohti:",
    "syncauswahl.bilanz.kandidaten.eins": "{n} ehdokas",
    "syncauswahl.bilanz.kandidaten.viele": "{n} ehdokasta",
    "syncauswahl.bilanz.vorpruefung": "{n} läpäisee esitarkistuksen",
    "syncauswahl.bilanz.gewaehlt_wort": "valittu",
    "syncauswahl.bilanz.wohl_abgelehnt":
        "Frigate hylkäisi todennäköisesti {n} (ei merkitty, voit lähettää "
        "ne silti).",
    "syncauswahl.bilanz.frueher_abgelehnt":
        "Frigate hylkäsi aiemmin {n} (ei merkitty; merkitseminen yrittää "
        "uudelleen).",
    "syncauswahl.pruef.fehler":
        "esitarkistus ei voinut ajaa: {fehler} — kuvat ilman päätelmää "
        "pysyvät valittuina.",
    "syncauswahl.pruef.laeuft.eins":
        "tarkistetaan {n} kuva … {fertig}/{gesamt} (tämä sivu latautuu "
        "uudelleen, kun se on valmis)",
    "syncauswahl.pruef.laeuft.viele":
        "tarkistetaan {n} kuvaa … {fertig}/{gesamt} (tämä sivu latautuu "
        "uudelleen, kun se on valmis)",
    "syncauswahl.sperre.titel": "Vain luku -tila on päällä",
    "syncauswahl.sperre.satz": "suslik ei kirjoita juuri nyt Frigateen.",
    "syncauswahl.knopf_alle": "Valitse kaikki",
    "syncauswahl.knopf_keine": "Poista kaikki valinnat",
    "syncauswahl.knopf_transfer": "Siirrä {n} valittua Frigateen",
    "syncauswahl.leer.titel": "Ei mitään lähetettävää",
    "syncauswahl.leer.satz":
        "Jokainen viite on jo päätynyt Frigateen tai sen valinta on "
        "poistettu.",
    "syncauswahl.leer.zusatz":
        "Alla olevat osiot listaavat sen, mikä ei siirry ilman muuta.",
    "syncauswahl.gruppe.wohl_abgelehnt": "{n} todennäköisesti hylättyä",
    "syncauswahl.gruppe.prueft": "{n} vielä tarkistuksessa",
    "syncauswahl.geloescht.zusatz": "— sinun päätöksesi",
    "syncauswahl.geloescht.satz":
        "Nämä ovat vielä kirjastossasi, mutta Frigatella niitä ei enää "
        "ole sillä nimellä, jolla ne tallennettiin. suslik ei koskaan "
        "lähetä niitä uudelleen ilman päätöstäsi: kasvojen poistaminen "
        "Frigatesta voi olla tarkoituksellista. Tarjoa uudelleen tekee "
        "siitä tavallisen ehdokkaan — siitä lähtien seuraava täsmäytys, "
        "myös automaattinen, lähettää sen. Kunnioita poistoa pitää sen "
        "pysyvästi poissa.",
    "syncauswahl.aufklapp": "— näytä",
    "syncauswahl.api.titel":
        "{n} vietiin aiemmin — Frigate pitää näitä omilla nimillään",
    "syncauswahl.api.satz":
        "Nämä lähtivät Frigaten API:n kautta, ja Frigate nimeää uudelleen "
        "jokaisen hyväksymänsä viitteen. Siksi suslik ei voi nimestä "
        "päätellä, ovatko ne vielä siellä — mikään tämän sivun luku ei "
        "voi sitä todistaa suuntaan tai toiseen. Mitään ei lähetetä "
        "automaattisesti uudelleen; jos tiedät jonkin puuttuvan, tarjoa "
        "se uudelleen (se lähettää toisen kopion, jos ensimmäinen on "
        "vielä siellä).",
    "syncauswahl.api.vergleich":
        "{person}: {n} lähetetty tätä tietä · Frigatella on tällä "
        "hetkellä {bestand} kuvaa",
    "syncauswahl.import.zeile.eins": "{n} kuva:",
    "syncauswahl.import.zeile.viele": "{n} kuvaa:",
    "syncauswahl.import.mehr": "… ja {n} muuta",
    "syncauswahl.import.satz":
        "Nämä viitekuvat ovat Frigatella, susliklla ei. Tuonti kopioi ne "
        "kirjastoosi; Frigatessa ei muutu mikään.",
    "syncauswahl.import.warnung":
        "Tässä listassa voi olla omia lähetyksiäsi: Frigate nimeää "
        "uudelleen jokaisen hyväksymänsä viitteen, joten suslik ei voi "
        "erottaa niitä kasvoista, jotka lisäsit suoraan Frigateen. Niiden "
        "tuonti takaisin kaksinkertaistaisi sisältöä.",
    "syncauswahl.import.knopf": "Tuo ne susliklin",
    "syncauswahl.raus.satz":
        "Tarkoituksella muistissa: nämä pysyvät kirjastossasi, mutta "
        "niitä ei koskaan lähetetä Frigateen, ei myöskään automaattisessa "
        "täsmäytyksessä. Palauta nostaa yhden takaisin ehdokaslistalle.",
    "syncauswahl.alter.unbekannt": "ikä tuntematon",
    "syncauswahl.alter.sekunden": "{s} s sitten",
    "syncauswahl.alter.minuten": "{m} min sitten",
    "syncauswahl.alter.stunden": "{h} h {m} min sitten",
    "syncauswahl.ergebnis.titel": "Viimeisin siirto",
    "syncauswahl.ergebnis.stopp": "pysäytetty:",
    "syncauswahl.ergebnis.wand": "kolme kertaa peräkkäin sama virhe: {fehler}",
    "syncauswahl.ergebnis.hochgeladen": "lähetetty — {bild}",
    "syncauswahl.ergebnis.zaehler": "{hoch} lähetetty · {weg} ei hyväksytty",
    "syncauswahl.ergebnis.auswahl": "{n} valitusta",
    "syncauswahl.ergebnis.uebersprungen": "{n} valinta poistettu (ohitettu)",
    "syncauswahl.ergebnis.dauer": "kesti {n} s",
    "live.hinweis_gpu":
        "Toimii toistaiseksi vain GPU:lla — työstämme CPU-vaihtoehtoa, "
        "mutta emme voi luvata sitä.",
    "live.hinweis_cpu":
        "CPU-tila: vahdit ovat täällä kalliita — nopea tarkistus kestää "
        "tyypillisesti 1–2 s (GPU-build vastaa alle sekunnissa), ja "
        "lisävahdit hidastavat toisiaan. Kuinka monta niitä ajat, on "
        "sinun päätöksesi; suosittelemme aloittamaan yhdestä.",
    "live.zeile.alter": "({tage} päivää vanha)",
    "live.test.zeile":
        "lähdetesti {wann}: {aufloesung} → {skala}, {bilder_s} kuvaa/s",
    "live.test.durchsatz":
        "(läpäisy, ei toimitusnopeus — aja lähdetesti uudelleen)",
    "live.test.provider": "provider {provider}",
    "live.test.sw": "(ohjelmistodekoodaus)",
    "live.test.entwertet":
        "— MITÄTÖITY: lähde on muuttunut tämän testin jälkeen",
    "live.test.veraltet_bitte":
        "Tämä tarkistus on {tage} päivää vanha — aja lähdetesti "
        "uudelleen, jotta luvut kuvaavat sitä, mitä kamera tänään "
        "toimittaa.",
    "live.test.fehlgeschlagen":
        "viimeisin lähdetesti EPÄONNISTUI ({wann}): {fehler}",
    "live.messung.zeile": "kuorma mitattu {wann}: {text}",
    "live.messung.veraltet":
        "— VANHENTUNUT: lähde on muuttunut tämän mittauksen jälkeen, "
        "mittaa uudelleen",
    "live.messung.fehlgeschlagen":
        "viimeisin kuormamittaus EPÄONNISTUI ({wann}): {fehler}",
    "live.zaehler.auftritte": "{n} esiintymistä",
    "live.zaehler.funde": "{n} kasvoa löydetty",
    "live.zaehler.trigger": "{n} triggeriä",
    "live.zaehler.alerts": "{n} ilmoitusta",
    "live.zaehler.letzter": "viimeisin trigger {zeit}",
    "live.zaehler.kopf": "enginen käynnistyksen jälkeen:",
    "live.engine.titel_aus": "Live-engine: ei käynnissä",
    "live.engine.satz_aus":
        "Engine-prosessilta ei tule heartbeatia. Ruudut näyttävät "
        "tallennetut asetukset; käyttöönotto, testit käynnissä olevaa "
        "vahtia vasten ja kuormamittaukset vaativat enginen — palvelu "
        "käynnistää sen automaattisesti heti, kun vähintään yksi vahti on "
        "päällä.",
    "live.engine.cpu_mit_limit":
        "suslikin CPU juuri nyt: {kerne}/{limit} sallittua ydintä (koko "
        "kontti: vahdit, analyysi, palvelu)",
    "live.engine.cpu_ohne_limit":
        "suslikin CPU juuri nyt: {kerne} ydintä (koko kontti: vahdit, "
        "analyysi, palvelu)",
    "live.engine.rss": "enginen RSS {rss} MB",
    "live.engine.grundkosten": "peruskustannus {mb} MB",
    "live.engine.je_stream": "{mb} MB streamia kohti ({quelle})",
    "live.engine.je_stream_fehlt":
        "streamia kohti käytettyä muistia ei ole vielä mitattu tällä "
        "koneella",
    "live.engine.ram_frei": "{mb} MB RAMia vapaana ({quelle})",
    "live.engine.ram_unlesbar": "RAM: kontin rajaa ei voi lukea",
    "live.engine.detektor": "detektori {ms} ms/kuva ({quelle})",
    "live.engine.drossel": "rajoitustaso {stufe}, käyttöaste {auslastung}",
    "live.engine.rest":
        "yhden lisästreamin jälkeen: ~{mb} MB RAMia jäisi vapaaksi",
    "live.engine.rest_warnung": "— ALLE turvavaran, ei enää yhtä paikkaa",
    "live.engine.kapazitaet":
        "kapasiteetti: enintään {n} vahtia (kova yläraja {hart}) — "
        "rajoittava tekijä: {grund}",
    "live.engine.hart": "kova yläraja {hart} vahtia",
    "live.engine.titel_standalone":
        "Live-engine: käynnissä (havaittu erillinen engine)",
    "live.engine.titel_an": "Live-engine: käynnissä",
    "live.gruppe.laufend": "Käynnissä",
    "live.gruppe.bereit": "Valmiina",
    "live.gruppe.rest": "Ei asetettu",
    "live.gruppe.versteckt": "Piilotetut",
    "live.gruppe.ohne_area": "Ei aluetta",
    "live.kachel.attr_fremd":
        "asetettu täällä, mutta tätä kameraa ei ole juuri nyt Frigatessa",
    "live.kachel.pill_fremd": "ei Frigatessa",
    "live.kachel.attr_detect":
        "Frigaten detect-stream — todellinen streamin tarkkuus ilmestyy, "
        "kun palvelu luotaa streamin tai lähdetesti ajetaan",
    "live.knopf_konfigurieren": "Aseta",
    "live.knopf_test": "Aja lähdetesti",
    "live.knopf_messung": "Mittaa kuorma",
    "live.knopf_enable": "Ota käyttöön",
    "live.knopf_disable": "Poista käytöstä",
    "live.knopf_zeigen": "Näytä",
    "live.knopf_verstecken": "Piilota",
    "live.banner.kameraliste":
        "Frigaten kameralistaa ei voitu lukea: {fehler}",
    "live.schalter.ungruppiert": "ryhmittelemätön näkymä",
    "live.schalter.area": "ryhmittele alueen mukaan",
    "live.sperre.cpu_titel": "CPU-tila",
    "live.sperre.titel": "Ei käytettävissä tässä buildissa",
    "live.sperre.satz":
        "Live-vahdit vaativat GPU-buildin — Intelin integroitu "
        "näytönohjain (gpu- / gpu-legacy-imaget), NVIDIA-kortti "
        "(cuda-image) tai AMD-kortti (rocm-image) kelpaavat kaikki.",
    "live.sperre.cpu_only":
        "Pelkässä CPU-imagessa niitä ei ole käytettävissä.",
    "live.erklaer.titel": "Live-vahdit — välitön reaktio kamerastreamissa",
    "live.erklaer.satz1":
        "Live-vahti yhdistyy suoraan yhteen kamerastreamiin ja reagoi, "
        "kun henkilö on vielä kuvassa: ensimmäiset kasvot käynnistävät "
        "tarkistuksen, ja asetetun yhtäpitävien havaintojen määrän "
        "jälkeen lähtee varmennettu signaali — tavoite on alle sekunti "
        "(viitekokoonpanolla mitattu 199–801 ms). Käytä sitä kodin "
        "automaatioiden laukaisuun, esim. MQTT:n kautta.",
    "live.erklaer.link": "Lue lisää: miten live-vahdit toimivat",
    "live.titel": "Live-vahdit",
    "live.leer.titel": "Kameroita ei löytynyt.",
    "live.leer.hinweis":
        "Aseta ensin Frigaten yhteys — ruudut ilmestyvät kameraa kohti.",
    "live.knopf_speichern": "Tallenna",
    "live.detail.titel": "Live-vahti — {name}",
    "live.abschnitt.quelle": "Lähde",
    "live.quelle.proxy":
        "go2rtc-restream Frigaten kautta (oletus, suositeltu)",
    "live.quelle.direct": "go2rtc:n löytämä kameran producer-URL",
    "live.quelle.url": "stream-URL, jonka syötät itse",
    "live.detail.url_label": "Stream-URL (vain lähteellä 'url'):",
    "live.detail.url_hinweis":
        "URL:ssä olevat tunnukset näytetään kaikkialla maskattuina — jätä "
        "kenttä näytetyn kaltaiseksi, jos haluat säilyttää tallennetun "
        "URL:n, tai liitä uusi",
    "live.detail.quelle_hinweis":
        "Lähteen vaihto mitätöi lähdetestin — aja se uudelleen ennen "
        "käyttöönottoa.",
    "live.abschnitt.aufloesung": "Käsittelytarkkuus",
    "live.hoehe.default": "oletus (1080p)",
    "live.hoehe.h360":
        "360p — hätäratkaisu heikoille GPU:ille, nimi tulee viimeisimpänä "
        "(mitattu)",
    "live.hoehe.h720": "720p — kevyempi dekoodaus, nimi tulee myöhemmin",
    "live.hoehe.h1080":
        "1080p — paras valinta (mitattu: nimi ~2,4 s aiemmin kuin "
        "720p:llä)",
    "live.hoehe.alt_hinweis":
        "Tallennettu: {alt}p. Tuo porras on poistettu (mitattu: ei hyötyä "
        "{jetzt}p:hen verrattuna) — tämä vahti ajaa tarkkuudella "
        "{jetzt}p. Tallennettu arvo ja lähdetesti pysyvät voimassa; "
        "valitse uusi porras, jos haluat muuttaa sitä.",
    "live.abschnitt.alarm": "Ilmoitusketju",
    "live.detail.ende_label": "Päättyy ilman kasvoja (s):",
    "live.detail.ende_hinweis":
        "esiintyminen päättyy näin monen kasvottoman sekunnin jälkeen "
        "(3–120)",
    "live.detail.scharf_label": "Uudelleen valmiina (s):",
    "live.detail.scharf_hinweis":
        "vähimmäissekunnit ilmoitusten välillä — jos joku on paikalla, se "
        "ilmoittaa uudelleen tämän ajan jälkeen; 0 = jokainen trigger "
        "ilmoittaa (0–3600)",
    "live.abschnitt.kanaele": "Ilmoituskanavat",
    "live.detail.namensschaetzung":
        'Ilmoitukset sisältävät alustavan nimiarvauksen ("todennäköisesti '
        'X"), kun kasvot täsmäävät tunnettuun henkilöön — ei koskaan '
        'tallenneta, ei koskaan käytetä opetukseen.',
    "live.abschnitt.test": "Testaa &amp; mittaa",
    "live.detail.gesperrt_hinweis":
        "testaaminen ja mittaaminen eivät ole käytettävissä, kun "
        "live-vahdit on lukittu tällä koneella — tämän sivun ylälaidan "
        "huomautus kertoo syyn.",
    "live.knopf_messung_lang": "Mittaa kuorma (15–30 s)",
    "live.detail.messung_hinweis":
        "kuormamittaus pysäyttää muut vahdit siksi ajaksi",
    "live.detail.link_zurueck": "takaisin yleisnäkymään",
    "live.detail.kein_bild": "Ei livekuvaa — tämä vahti ei ole käynnissä.",
    "live.detail.kein_bild_test":
        "Viimeisin lähdetesti näki {aufloesung}, käsiteltiin muodossa "
        "{skala}.",
    "live.detail.kein_bild_ohne_test":
        "Lähdetestiä ei ole vielä ajettu, joten tästä syötteestä ei "
        "tiedetä mitään.",
    "live.abschnitt.erkennung": "Tunnistus",
    "live.abschnitt.melden": "Ilmoittaminen",
    "live.abschnitt.frigate": "Frigate-tapahtumat",
    "live.abschnitt.erweitert": "Lisäasetukset",
    "live.abschnitt.abtastung": "Näytteistys",
    "live.abtastung.schalter": "Katso tarkasti vain, kun jokin liikkuu",
    "live.abtastung.erklaerung":
        "Kasvojen havaitseminen on se kallis osa — halpa liiketarkistus "
        "kirkkaustasolla päättää, kannattaako kuva sen. Niin kauan kuin "
        "henkilöä seurataan, vahti ajaa aina täydellä tahdilla; vain "
        "rauhallista näkymää näytteistetään harvemmin.",
    "live.abtastung.ruhe_label": "Katso silti joka",
    "live.abtastung.ruhe_einheit": "s",
    "live.abtastung.ruhe_hinweis":
        "Jätä tyhjäksi, niin käytetään tämän kameran esiintymisen "
        "päättymisaikaa — täysin liikkumatta seisova ei tuota liikettä, "
        "joten vahti vilkaisee silti aika ajoin (1–600 s).",
    "live.abtastung.schwelle_label": "Herkkyys (harmaasävyn muutos):",
    "live.abtastung.flaeche_label": "pienin pinta-ala:",
    "live.abtastung.eich_hinweis":
        "Jätä molemmat tyhjiksi, niin käytetään Frigaten toimitusarvoja. "
        "Pienempi herkkyysluku tai pienempi pinta-ala saa vahdin "
        "katsomaan useammin; suuremmat arvot pitävät sen rauhallisena "
        "tuulisen pensasaidan äärellä. Jokainen paikka on erilainen — "
        "nämä kuuluvat TÄLLE kameralle, eivät koko järjestelmälle.",
    "live.abschnitt.guete": "Kuvanlaadun rajat",
    "live.abschnitt.last": "Kuormamittaus",
    "live.erkennung.det_zeile":
        "Löydös lasketaan kasvoiksi havaintoarvosta {wert} "
        "ylöspäin{marke}.",
    "live.erkennung.det_vorgabe": " (oletus)",
    "live.erkennung.fenster_vor": "Päätösikkuna:",
    "live.erkennung.fenster_nach":
        "s — kerätään ensin äänet, sitten ilmoitetaan paras nimi",
    "live.erkennung.fenster_hinweis":
        "Ensimmäisestä nimiehdokkaasta lähtien vahti odottaa tämän ajan "
        "ja ilmoittaa sitten ehdokkaan, jolla on eniten ääniä — eikä "
        "ensimmäistä rajan ylittäjää. 0 = ilmoita heti (toiminta versioon "
        "0.1.0.395 asti).",
    "live.erkennung.regel_vor": "Tunnistettu, kun on",
    "live.erkennung.regel_mitte": "vahvistusta",
    "live.erkennung.regel_nach": "sekunnin sisällä",
    "live.erkennung.regel_hinweis":
        "0 sekuntia tarkoittaa, että koko esiintyminen lasketaan, niin se "
        "toimi ennen. Aikaikkuna auttaa kameroilla, joilla joku "
        "seisoskelee minuutteja eikä kahta kaukana toisistaan osunutta "
        "onnenpotkua pidä laskea yhdeksi tunnistukseksi.",
    "live.erkennung.vorrat_zeile":
        "Kalibrointikuvia: {n}/{deckel} säilytetty — yksi kuva "
        "esiintymistä kohti, vanhimmat putoavat pois.",
    "live.erkennung.vorrat_aus":
        'Kuvien kerääminen on pois päältä, joten kalibrointisivulla ei '
        'ole mitään näytettävää (Järjestelmä-sivu, "live_kalib_max").',
    "live.erkennung.latte_e": "kuvan vaikutelma arvosta {wert}",
    "live.erkennung.latte_t": "tunnistettavuus arvosta {wert}",
    "live.erkennung.latte_aus": "ei asetettu",
    "live.erkennung.latte_hinweis":
        "Nämä kaksi eivät koskaan päätä, KUKA tunnistetaan — se "
        "kustantaisi vahvistuksia. Ne päättävät, mikä kuva menee "
        "ilmoitukseen ja mitkä kasvot säilytetään kalibrointikuvina. "
        "Aseta ne kalibrointisivulla, jossa näet kuvat.",
    "live.knopf_kalibrieren": "Kalibroi",
    "live.knopf_vorrat_leeren": "Hylkää kuvat",
    "live.workeraus.schalter":
        "Tämä vahti korvaa tämän kameran tapahtuma-analyysin",
    "live.workeraus.erklaerung":
        "Oletuksena pois. Päällä ollessaan tämän kameran "
        "Frigate-tapahtumia ei analysoida toista kertaa — vahti katsoo jo "
        "samaa syötettä, joten työ tehtäisiin kahdesti. Tämä vaikuttaa "
        "vain niin kauan kuin vahti on päällä JA todella käynnissä: jos "
        "engine pysähtyy tai vahti kaatuu, tapahtumat analysoidaan taas "
        "normaalisti. Nimen, jonka Frigate itse väittää, tarkistamme "
        "aina, tästä asetuksesta riippumatta.",
    "live.frigate.schalter": "Luo Frigate-tapahtuma, kun joku tunnistetaan",
    "live.frigate.erklaerung":
        "Oletuksena pois. Päällä ollessaan tämä vahti kirjoittaa "
        "Frigateen oman tapahtumansa, jossa nimi on sub label -kentässä — "
        "oma tallenne, riippumaton Frigaten havainnoista. Kirjoitus "
        "tapahtuu taustalla: vahti ei koskaan odota Frigatea. Vain luku "
        "-tilassa ei kirjoiteta mitään.",
    "live.frigate.abstand_label":
        "Enintään yksi tapahtuma henkilöä kohti joka (s):",
    "live.frigate.abstand_hinweis":
        "Tyhjä tarkoittaa: sama väli kuin yllä ilmoituksille. Raja "
        "lasketaan henkilöä kohti, joten kaksi eri ihmistä voidaan "
        "kirjoittaa samaan aikaan.",
    "livekalib.titel": "Kameran kalibrointi — {name}",
    "livekalib.erklaerung":
        "Nämä ovat oikeita kasvoja, jotka tämä kamera on kerännyt — yksi "
        "kuva esiintymistä kohti. Vedä liukusäätimiä, kunnes valinta "
        "näyttää sinulle oikealta, ja ota se käyttöön. Arvot tallennetaan "
        "vain TÄLLE kameralle, koska laatuasteikot vaihtelevat kamerasta "
        "kameraan.",
    "livekalib.regler_det": "Havaintoarvo",
    "livekalib.regler_det_prosa":
        "Tästä ylöspäin löydös lasketaan ylipäätään kasvoiksi. Tämä "
        "säädin ohjaa tunnistusta todella: kaikki sen alle jäävä ei "
        "koskaan pääse nimitarkistukseen. Matalampi säilyttää enemmän "
        "materiaalia (mitattu: korkea raja heitti pois puolet "
        "käyttökelpoisesta materiaalista); korkeampi pitää pensasaidat ja "
        "valoläikät ulkona.",
    "livekalib.regler_e": "Kuvan vaikutelma",
    "livekalib.regler_e_prosa":
        "Kuinka siistiltä ja valoisalta kuva silmään näyttää. Tämä EI "
        "päätä, kuka tunnistetaan — se päättää, mikä kuva menee "
        "ilmoitukseen ja mitkä kasvot säilytetään tässä "
        "kalibrointikuvina.",
    "livekalib.regler_t": "Tunnistettavuus",
    "livekalib.regler_t_prosa":
        "Kuinka hyvin henkilö on erotettavissa, puoliksi peittyneet "
        "kasvot mukaan lukien. Kuten yllä oleva säädin: se valitsee kuvan "
        "ja täyttää tämän sivun, se ei koskaan karsi ketään pois "
        "tunnistuksesta.",
    "livekalib.regler_p": "Pään asento",
    "livekalib.regler_p_prosa":
        "Kuinka selvästi löytöpaikalla on erotettavissa pää. Se on sama "
        "arvo, jolla asentotarkistus pitää roska-astiat, pensasaidat ja "
        "auton keulat pois ilmoituksista. Tätä mittausta vanhemmat kuvat "
        "eivät kanna arvoa ja pääsevät aina läpi. Se, mitä tässä "
        "asetetaan, tallennetaan tälle kameralle ja vaikuttaa tällä "
        "sivulla; palvelussa se ei vielä karsi mitään.",
    "livekalib.ohne_guete":
        "Kaksi laatumallia puuttuu tästä buildista, joten näillä kuvilla "
        "ei ole laatulukuja eivätkä kaksi alempaa säädintä vaikuta tässä. "
        "Havaintoarvo toimii.",
    "livekalib.ohne_pose":
        "Yksikään näistä kuvista ei vielä kanna pään asennon arvoa "
        "(vanhaa materiaalia tai kuvia, jotka tulivat toista tietä), "
        "joten tämä säädin ei muuta tässä mitään. Uudet kuvat "
        "tapahtuma-analyysistä tuovat arvon mukanaan.",
    "livekalib.katalog.regler_n": "Katalogi: Feature-normi",
    "livekalib.katalog.regler_n_prosa":
        "Kuinka vahvat kasvojen on tunnistusmateriaalina oltava, jotta "
        "oppimisajo säilyttää ne — viitteetön mitta, jolla oppimisvarasto "
        "jo toimii (hyvät suoraan edestä kuvatut kasvot ovat noin 24). "
        "Tehtaalta akseli on PÄÄLLÄ, arvossa 20, asetettu oikeaa kerättyä "
        "materiaalia katsomalla (756 kuvaa, mediaani 20,7). Säädin ei "
        "mene alle 18 — akselia ei voi täällä kytkeä pois, vain asettaa "
        "välille 18–35. Tämä on eri kysymys kuin asetusten varastoraja, "
        "joka päättää, mitkä kuvat sinulle TARJOTAAN.",
    "livekalib.ohne_norm":
        "Yksikään näistä kuvista ei kanna Feature-normin arvoa "
        "(kalibrointivarasto ei mittaa sitä, oppimisajo mittaa), joten "
        "tämä säädin ei muuta tämän galleriaa mitenkään. Oppimisajon "
        "käyttämän arvon se asettaa silti.",
    "livekalib.regler_k": "Pienimmät kasvot (px)",
    "livekalib.regler_k_prosa":
        "Kuinka pienet kasvot saavat olla ja käydä silti äänestä — "
        "mitattuna rajauksen lyhyemmältä sivulta, pikseleinä. Tämä on "
        "pohja hölynpölyä vastaan, ei laaturaja: kenttäaineistossa oikeat "
        "äänet ovat yleiskuvakameroilla 30-49 px ja hölynpölytapaukset "
        "11-19 px, kun taas 70 px kaataisi oikeatkin. Tehdasarvo 25 on "
        "täsmälleen se luku, jolla tämä järjestelmä on mitannut jokaisen "
        "äänen versiosta 0.1.0.400 lähtien; säädin tekee siitä vain "
        "kamerakohtaisen. 0 = pois.",
    "livekalib.katalog.regler_k": "Katalogi: pienimmät kasvot (px)",
    "livekalib.katalog.regler_k_prosa":
        "Sama mitta oppimiseen: kuinka pienet kasvot saavat olla ja "
        "oppimisajo säilyttää ne silti. Aseta se korkeammalle kameralla, "
        "jonka kasvot ovat yksinkertaisesti liian kaukana opittaviksi, ja "
        "huomaa, että tämä on eri kysymys kuin viereisessä välilehdessä — "
        "ilmoituksen saaminen jostakusta vaatii vähemmän tarkkuutta kuin "
        "sen oppiminen, miltä hän näyttää. 0 = pois.",
    "livekalib.ohne_kante":
        "Yksikään näistä kuvista ei kanna kasvojensa kokoa "
        "(kalibrointivarasto ei tallenna sitä, oppimisajo tallentaa), "
        "joten tämä säädin ei muuta tämän galleriaa mitenkään. "
        "Käytettävän arvon se asettaa silti.",
    "livekalib.standard": "Oletukset",
    "livekalib.fueller.laeuft": "materiaalihaku käynnissä",
    "livekalib.fueller.bilanz": "Viimeisin materiaalihaku",
    "livekalib.fueller.bilder": "kuva(a)",
    "livekalib.tab_erkennen": "Tunnistus",
    "livekalib.tab_lernen": "Kasvokatalogi",
    "livekalib.tab_pruefen": "Katalogin tarkistus",
    "livekalib.uebernehmen": "Ota käyttöön",
    "livekalib.leer":
        'Ei vielä kuvia. Ne tulevat itsestään — käynnissä olevalta '
        'vahdilta ja tämän kameran jokaisesta tapahtuma-analyysistä, '
        'yhdet kasvot kerrallaan. Jos et halua odottaa, käytä alla olevaa '
        '"Etsi tuoretta materiaalia".',
    "livekalib.zurueck": "takaisin vahtiin",
    "livekalib.js.genutzt": "{n}/{gesamt} kuvaa pääsee läpi",
    "livekalib.js.gespeichert": "tallennettu",
    "livekalib.js.fehler": "virhe",
    "livekalib.zur_uebersicht": "takaisin kaikkiin kameroihin",
    "livekalib.abschnitt.anzeige": "Ilmoittaminen, näyttäminen ja varasto",
    "livekalib.abschnitt.anzeige_prosa":
        "Nämä kolme päättävät, mikä tämän kameran kuva menee ilmoitukseen "
        "ja mitkä kasvot säilyvät tässä varastona. Ne eivät päätä, kuka "
        "tunnistetaan.",
    "livekalib.abschnitt.katalog": "Katalogin raja",
    "livekalib.abschnitt.pruefen": "Katalogin tarkistuksen raja",
    "livekalib.abschnitt.material": "Materiaali",
    "livekalib.katalog.prosa":
        "Nämä neljä arvoa päättävät, mitä tämä kamera antaa oppimiseen: "
        "oppimisajo säilyttää vain kasvot, jotka läpäisevät kaikki neljä, "
        "ja vain sellaisesta materiaalista voi tulla viite "
        "AUTOMAATTISILLA teillä (oppimisajon käyttöönotto, "
        "ehdotusten/varastotarjousten hyväksyminen). Ne ovat samat neljä "
        "säädintä kuin Tunnistus-välilehdessä ja sama laskutapa — vain "
        "omat lukunsa, koska ilmoittaminen ja oppiminen eivät vaadi "
        "samaa. Kasvot, jotka merkitset ja nimeät itse, ohittavat ne "
        "kokonaan.",
    "livekalib.katalog.grenze":
        "Mitä ne eivät tee: ne eivät koskaan poista jo olevia viitteitä, "
        "eivätkä muuta mitään siinä, kuka tunnistetaan. Kun kuva otetaan "
        "katalogiin, puuttuvat laatuluvut (vanhempi materiaali, build "
        "ilman laatumalleja) päästävät sen läpi koskematta. Oppimisajossa "
        "pätee saman säännön toinen puoli: kasvot, joiden arvoa ei voitu "
        "mitata, putoavat pois — ajon lopussa oleva yhteenveto laskee "
        "nämä tapaukset yksitellen sen sijaan, että ne katoaisivat.",
    "livekalib.katalog.quelle_kamera": "Käytössä: tämän kameran omat arvot.",
    "livekalib.katalog.quelle_global":
        "Käytössä: yleinen varasääntö — tällä kameralla ei ole vielä omia "
        "arvoja.",
    "livekalib.katalog.quelle_aus":
        "Katalogin rajaa ei ole asetettu: mistä tahansa kuvasta voi tulla "
        "viite.",
    "livekalib.katalog.regler_e": "Katalogi: kuvan vaikutelma",
    "livekalib.katalog.regler_e_prosa":
        "Tämän kameran viitteen vähimmäisvaikutelma kuvana. "
        "Tarkoituksella matala: keskinkertainenkin kuva kantaa vielä "
        "jotain opittavaa, ja katalogin tarkistus katsoo sitä uudelleen, "
        "kun se on sisällä.",
    "livekalib.katalog.regler_t": "Katalogi: tunnistettavuus",
    "livekalib.katalog.regler_t_prosa":
        "Tämän kameran viitteen vähimmäistunnistettavuus. Juuri tämä "
        "pitää puoliksi peittyneet kasvot pois katalogista.",
    "livekalib.katalog.regler_det": "Katalogi: havaintoarvo",
    "livekalib.katalog.regler_det_prosa":
        "Mistä lähtien detektori on tarpeeksi varma, että kasvot ovat "
        "ylipäätään olemassa. Sama mittari kuin Tunnistus-välilehdessä, "
        "mutta oppimiseen — ja täällä se saa hyvin olla muualla: se, "
        "mistä haluat ilmoituksen, ei ole sama kuin se, mistä haluat "
        "oppia.",
    "livekalib.katalog.regler_p": "Katalogi: pään asento",
    "livekalib.katalog.regler_p_prosa":
        "Kuinka selvästi löytöpaikalla on erotettavissa pää. Tämä on "
        "säädin roska-astioita, pensasaitoja ja auton keuloja vastaan "
        "oppimismateriaalissa — kaksi laatuarvoa eivät yksin näe "
        "sellaista. Jälleen sama mittari kuin Tunnistus-välilehdessä.",
    "livekalib.pruefen.prosa":
        "Tämä raja arvioi kuvia, jotka sinulla JO on. Sen alapuolella "
        "katalogin tarkistus merkitsee tämän kameran tallennetun kuvan; "
        "yhdessä heikon Feature-normin kanssa siitä tulee poistoehdotus, "
        "jota voit napsauttaa. Se ei koskaan ota kuvaa sisään eikä "
        "koskaan poista kuvaa itse.",
    "livekalib.pruefen.grenze":
        "Se on tarkoituksella erillään yllä olevasta rajasta: kuvan "
        "sisään ottaminen ja sen tarkistaminen myöhemmin ovat kaksi "
        "kysymystä, eikä yhden säätimen veto saa hiljaa vetää toista "
        "mukanaan. Kuvia ilman laatulukua ei koskaan merkitä.",
    "livekalib.pruefen.quelle_kamera": "Käytössä: tämän kameran oma arvo.",
    "livekalib.pruefen.quelle_global":
        "Käytössä: yleinen varasääntö — tällä kameralla ei ole vielä omaa "
        "arvoa.",
    "livekalib.pruefen.quelle_aus":
        "Tarkistusrajaa ei ole asetettu: katalogin tarkistus ei arvioi "
        "kuvanlaatua.",
    "livekalib.pruefen.regler_t": "Tarkistus: tunnistettavuus",
    "livekalib.pruefen.regler_t_prosa":
        "Tämän tunnistettavuusarvon alle jäävä tämän kameran tallennettu "
        "kuva merkitään. Oletus tulee käsin arvioidusta katalogikuvien "
        "joukosta, ei arvauksesta.",
    "livekalib.material.aus":
        "Kuvien kerääminen on kytketty pois (Advanced, calibration "
        "samples). Ilman varastoa tällä sivulla ei ole mitään "
        "näytettävää.",
    "livekalib.material.stand": "{n} kuvaa varastossa, enintään {deckel}",
    "livekalib.material.wann": "viimeksi {wann}",
    "livekalib.material.zeitraum": "kuvia ajalta {von}–{bis}",
    "livekalib.material.fuellen_prosa":
        "Tuoreen materiaalin haku käy läpi tämän kameran viimeisimmät "
        "henkilötapahtumat ja säilyttää jokaisesta parhaat kasvot. Se "
        "pysähtyy {ziel} kuvaan tai {events} tapahtuman jälkeen, sen "
        "mukaan kumpi tulee ensin.",
    "livekalib.material.lauf":
        "Lisäksi {n} tämän kameran kuvaa viimeisimmästä oppimisajosta — "
        "mukana alla ja sellaisiksi merkittyinä.",
    "livekalib.js.katalog": "{n}/{gesamt} pääsisi katalogiin",
    "livekalib.js.pruefen": "{n}/{gesamt} merkittäisiin tarkistuksessa",
    "livekalib.js.lauf": "ajo",
    "livekalib.js.aus": "pois",
    "erkennung.titel": "Tunnistus",
    "erkennung.kopf.satz":
        "Neljä tapaa, joilla järjestelmäsi voi tunnistaa jonkun — "
        "jokainen omana korttinaan: kytke, näe että se toimii, aseta se. "
        "Live-kytkin vaikuttaa heti; kehon ja Visionin muutokset tulevat "
        "voimaan painikkeella Tallenna + käynnistä uudelleen.",
    "erkennung.kipp.label": "Päällä",
    "erkennung.kipp.attr_verriegelt":
        "aina päällä — jokainen muu tapa rakentuu kasvopäätelmän varaan",
    "erkennung.link_how": "Näin se toimii &#8230;",
    "erkennung.live.titel": "Live-vahti",
    "erkennung.live.beweis_prefix": "tarkkailee",
    "erkennung.live.beweis_zaehler": "{an}/{ges}",
    "erkennung.live.beweis_suffix": "asetetusta kamerasta",
    "erkennung.live.beweis_keine_laufend":
        "kameraa asetettu, yksikään ei käynnissä",
    "erkennung.live.beweis_keiner": "vahtia ei ole vielä asetettu",
    "erkennung.live.expert_schalter":
        "pois kytkeminen pysäyttää jokaisen käynnissä olevan vahdin; "
        "päälle kytkeminen käynnistää kaikki asetetut vahdit "
        "(kamerakohtainen kytkin pätee edelleen)",
    "erkennung.live.link_prokamera": "kamerakohtainen ohjaus",
    "erkennung.live.knopf_kameras": "Valitse kamerat …",
    "erkennung.knopf_register_face": "Rekisteröi kasvot …",
    "erkennung.gesicht.titel": "Kasvontunnistus",
    "erkennung.gesicht.satz":
        "Tarkin tapa: jokainen käynti tarkistetaan niiden henkilöiden "
        "kasvoja vasten, jotka olet järjestelmälle opettanut. Se on "
        "selkäranka — keho ja Vision riippuvat sen käyntipäätelmästä, "
        "siksi sillä ei ole tänään pois-kytkintä.",
    "erkennung.gesicht.beweis_personen": "{n} henkilöä",
    "erkennung.gesicht.beweis_bilder": "{n} viitekuvaa",
    "erkennung.gesicht.knopf_verwalten": "Hallitse henkilöitä …",
    "erkennung.koerper.titel": "Kehontunnistus",
    "erkennung.koerper.satz":
        "Tunnistaa talon asukkaat ruumiinrakenteesta ja asennosta myös "
        "silloin, kun kasvot eivät näy — se oppii itse läpikäydyistä "
        "kuvista.",
    "erkennung.koerper.beweis_kein_modell":
        "ei vielä henkilömallia — opeta ja käy läpi ensin",
    "erkennung.status.kein_modell":
        "ei käynnissä (koulutettua henkilömallia ei ole vielä otettu "
        "käyttöön)",
    "erkennung.status.hier_aus": "ei käynnissä (kytketty täällä pois)",
    "erkennung.status.vision_aus":
        "ei käynnissä (Vision-tunnistus on kytketty pois)",
    "erkennung.koerper.link_modell": "mallin tila",
    "erkennung.koerper.knopf_status": "Mallin tila …",
    "erkennung.koerper.knopf_register": "Rekisteröi keho …",
    "erkennung.vision.titel": "Vision-tekoäly",
    "erkennung.vision.beta": "Beta",
    "erkennung.vision.satz":
        "Kuvatekoäly tuomarina vaikeisiin tapauksiin. Vaatii mallin "
        "päätepisteen (paikallinen tai maksullinen) — jokainen tarkistus "
        "kuluttaa pyyntöjä.",
    "erkennung.vision.beweis_an": "päätepiste yhdistetty",
    "erkennung.vision.beweis_aus": "ei yhdistettyä päätepistettä",
    "erkennung.vision.knopf_connect": "Yhdistä malli …",
    "erkennung.vision.knopf_register": "Rekisteröi Vision …",
    "erkennung.abschnitt_property": "Tontin asetukset",
    "erkennung.areas.titel": "Alueet",
    "erkennung.areas.satz":
        "Mikä tontilla lasketaan: piirrä alueet niin, että ilmoitukset "
        "laukeavat vain siellä, missä se sinua kiinnostaa — piha-alue "
        "merkitsee, aidan takana oleva katu ei.",
    "erkennung.areas.beweis_zahl": "aluetta määritelty",
    "erkennung.areas.beweis_keine": "ei vielä alueita — kaikki lasketaan",
    "erkennung.areas.knopf": "Hallitse alueita &#8230;",
    "erkennung.knopf_speichern": "Tallenna + käynnistä uudelleen",
    "faces.titel": "Kasvot",
    "faces.link_how": "Näin se toimii &#8230;",
    "faces.bekannt.titel": "Tunnetut henkilöt",
    "faces.bekannt.knopf_verwalten": "Hallitse henkilöitä &#8230;",
    "faces.bekannt.knopf_register": "Rekisteröi kasvot &#8230;",
    "faces.bekannt.leer":
        "ei vielä opetettuja henkilöitä — rekisteröi ensimmäiset kasvot "
        "ylhäällä",
    "faces.bekannt.beweis_personen": "{n} henkilöä",
    "faces.bekannt.beweis_bilder": "{n} viitekuvaa",
    "faces.lernen.titel": "Opettaminen",
    "faces.lernen.knopf_start": "Aloita opettaminen &#8230;",
    "faces.lernen.knopf_review": "Käy ehdotukset läpi &#8230;",
    "faces.lernen.beweis_offen": "ehdotusta odottaa läpikäyntiä",
    "faces.lernen.beweis_leer":
        "mikään ei odota — järjestelmä kerää itsestään lisää",
    "faces.lernen.satz": "Käy läpi, mitä kamerat ovat keränneet.",
    "faces.unbekannt.titel": "Tuntemattomat",
    "faces.unbekannt.knopf": "Käy tuntemattomat läpi &#8230;",
    "faces.unbekannt.beweis_offen": "toistuvaa tuntematonta vierailijaa",
    "faces.unbekannt.beweis_leer": "ei toistuvia tuntemattomia vierailijoita",
    "faces.unbekannt.satz": "Vierailijat, joilla ei vielä ole nimeä.",
    "faces.qualitaet.titel": "Kuvanlaatu",
    "faces.qualitaet.stand":
        "tarkistettu viimeksi {wann} &middot; {n} löydöstä",
    "faces.qualitaet.knopf_check": "Tarkista kuvieni laatu",
    "faces.qualitaet.popup_satz":
        "Mittaa jokaisen viitekuvan uudelleen (kasvojen laatu mukaan "
        "lukien) ja etsii heikkoja, lähes samanlaisia ja sekaantuneita "
        "kasvoja. Kestää kuvamäärän mukaan muutamia minuutteja ja ajetaan "
        "taustalla.",
    "faces.qualitaet.label_alle": "Kaikki henkilöt",
    "faces.qualitaet.label_eine": "Yksi henkilö:",
    "faces.qualitaet.knopf_start": "Käynnistä tarkistus",
    "faces.qualitaet.knopf_abbrechen": "Peruuta",
    "faces.qualitaet.knopf_ergebnisse": "Viimeisimmät tulokset &#8230;",
    "faces.qualitaet.satz": "Löytää heikot tai sekaantuneet kuvat.",
    "qualitaet.kopf.titel": "Laatu — viitekirjasto",
    "qualitaet.kopf.hinweis":
        "napauta alta henkilöä, niin näet kaikki hänen kuvansa heikot "
        "merkittyinä.",
    "qualitaet.kopf.stand": "Tilanne: {stand} · {n} viitettä",
    "qualitaet.kopf.knopf_neu": "Tarkista nyt uudelleen",
    "qualitaet.lauf.fehler":
        "viimeisin tarkistus EPÄONNISTUI: {fehler} &mdash; käynnistä se "
        "uudelleen.",
    "qualitaet.lauf.checking": "tarkistetaan kuvaa {i}/{n} &hellip;",
    "qualitaet.lauf.reload_person":
        "lataa tämä sivu sen jälkeen uudelleen, niin saat tuoreen "
        "tuloksen.",
    "qualitaet.lauf.abgebrochen":
        "viimeisin tarkistus ei käynyt loppuun (palvelun "
        "uudelleenkäynnistys tai se pysäytettiin) &mdash; käynnistä se "
        "uudelleen.",
    "qualitaet.tabelle.kopf_person": "henkilö",
    "qualitaet.tabelle.kopf_bilder": "kuvat",
    "qualitaet.tabelle.kopf_gut": "hyvä",
    "qualitaet.tabelle.kopf_mittel": "keskitaso",
    "qualitaet.tabelle.kopf_unter": "liian heikko",
    "qualitaet.tabelle.kopf_links": "&larr; vasemmalta",
    "qualitaet.tabelle.kopf_front": "edestä",
    "qualitaet.tabelle.kopf_rechts": "oikealta &rarr;",
    "qualitaet.tabelle.kopf_doppel": "samannäköiset",
    "qualitaet.tabelle.kopf_verwechslung": "sekaannus",
    "qualitaet.person.funde": "{n} kuvaa vilkaisun arvoista",
    "qualitaet.person.verwechselt": "mahdollisesti sekaantunut",
    "qualitaet.person.alles_gut": "kaikki hyvin",
    "qualitaet.person.gemischt": "kokoelma vaikuttaa sekalaiselta",
    "qualitaet.ergebnis.alles_gut": "Kaikki hyvin.",
    "qualitaet.ergebnis.alles_gut_satz":
        "Tarkistettu {n} kuvaa {np} henkilöltä &mdash; mikään ei vaadi "
        "huomiotasi.",
    "qualitaet.wort.kein_gesicht": "kasvoja ei löytynyt",
    "qualitaet.galerie.looks_like": "näyttää kuin {name}",
    "qualitaet.galerie.doppel": "kaksoiskappale — säilytetty kuva kattaa sen",
    "qualitaet.galerie.gut": "hyvä",
    "qualitaet.galerie.gut_behalten": "hyvä — säilytetty kaksoiskappaleistaan",
    "qualitaet.galerie.vorrat": "varastosta",
    "qualitaet.galerie.norm": "laatu {norm}",
    "qualitaet.galerie.okay": "okei",
    "qualitaet.galerie.unter_beide": "tarkistusrajan ja normin pohjan alla",
    "qualitaet.galerie.unter_guete": "tarkistusrajan alla",
    "qualitaet.galerie.unter_norm": "normin pohjan alla",
    "qualitaet.galerie.guete_datei": "arvo mitattu tallennetusta rajauksesta",
    "qualitaet.galerie.rang": "#{rang} tällä henkilöllä",
    "qualitaet.galerie.marge": "identiteettimarginaali {marge}",
    "qualitaet.galerie.dubl_behalten": "säilytä tämä",
    "qualitaet.galerie.dubl_weg": "identtinen kopio",
    "qualitaet.galerie.dubl_hinweis":
        "Nämä tiedostot ovat tavu tavulta samat. ”Valitse kaikki” "
        "merkitsee tässä jokaisen kopion paitsi kunkin sarjan ensimmäisen "
        "— katso ne läpi ja poista, mitä et tarvitse.",
    "qualitaet.galerie.noface_hinweis":
        "Näistä kuvista ei löytynyt kasvoja, joten niistä ei voitu mitata "
        "mitään. Vilkaisu kannattaa: joissakin on kasvot, jotka detektori "
        "ohitti, toisissa ei kasvoja lainkaan.",
    "qualitaet.galerie.gemischt":
        "Tämä kokoelma vaikuttaa sekalaiselta: {neg}/{n} kuvasta on "
        "lähempänä henkilöä {fremd} kuin tätä henkilöä. Katso ne, ennen "
        "kuin opit niistä — mitään ei poisteta ilman että sanot niin.",
    "qualitaet.galerie.satz_gut": "Kaikki {n} kuvaa näyttävät hyviltä.",
    "qualitaet.galerie.satz_funde":
        "{funde}/{n} kuvasta on vilkaisun arvoista — ne ovat kahdessa "
        "oikeanpuoleisessa välilehdessä. Merkitse, mitä haluat poistaa — "
        "ilman napsautustasi ei tapahdu mitään.",
    "qualitaet.reiter.gut": "Hyvät ({n})",
    "qualitaet.reiter.check": "Katso nämä ({n})",
    "qualitaet.reiter.weg": "Ehdotus: poista ({n})",
    "qualitaet.reiter.dubl": "Identtiset kopiot ({n})",
    "qualitaet.reiter.noface": "Kasvoja ei löytynyt ({n})",
    "qualitaet.galerie.knopf_alle": "Valitse kaikki",
    "qualitaet.galerie.knopf_keine": "Poista kaikki valinnat",
    "qualitaet.galerie.knopf_entfernen": "Poista valitut",
    "qualitaet.galerie.leer_gruppe": "tässä ryhmässä ei ole mitään.",
    "qualitaet.galerie.titel": "{name} — kuvanlaatu",
    "qualitaet.galerie.link_zurueck": "&larr; takaisin yleisnäkymään",
    "qualitaet.galerie.leer_person": "tälle henkilölle ei ole kuvia.",
    "qualitaet.leer.titel": "Tarkistusta ei ole vielä laskettu.",
    "qualitaet.leer.hinweis": "Napsauta ylhäältä Tarkista nyt uudelleen.",
    "lernwizard.titel": "Oppimisajo",
    "lernwizard.link_how": "Näin se toimii &#8230;",
    "lernwizard.dauer.lang": "{m} min {s} s",
    "lernwizard.dauer.kurz": "{s} s",
    "lernwizard.phase.vorbereitung": "Valmistelu",
    "lernwizard.phase.ernte": "Keräys (kasvojen keruu)",
    "lernwizard.phase.anker": "Ryhmittely (ankkurit)",
    "lernwizard.phase.benennung": "Nimeäminen (sinun vaiheesi)",
    "lernwizard.phase.neben_ansichten": "Sivukuvat",
    "lernwizard.phase.ganzkoerper": "Kokovartaloviitteet",
    "lernwizard.phase.uebernahme": "Siirto Masteriin",
    "lernwizard.phase.fertig": "Valmis",
    "lernwizard.phase.aktuell": "(nykyinen)",
    "lernwizard.phase.link_benennen": "avaa ryhmät ja nimeä ne",
    "lernwizard.wizard.titel": "Opeta henkilöitä — ohjattu ajo",
    "lernwizard.wizard.satz":
        "Suunnittelee oppimisajon omille tallenteillesi. Valmistelu, "
        "keräys, ryhmittely, nimeäminen ja käyttöönotto tunnistuksessa "
        "ajetaan kaikki oikeasti.",
    "lernwizard.wizard.lage_b":
        "B — olemassa olevia viitteitä/tuntemattomia laajennetaan",
    "lernwizard.wizard.lage_a": "A — kylmä käynnistys, ei vielä kasvoja",
    "lernwizard.badge.unbekannt": "tuntemattomat vierailijat",
    "lernwizard.wizard.unbekannt_wartend.eins":
        "{n} tuntematon vierailija odottaa kohdassa",
    "lernwizard.wizard.unbekannt_wartend.viele":
        "{n} tuntematonta vierailijaa odottaa kohdassa",
    "lernwizard.link_unbekannte": "Henkilöt &rarr; Tuntemattomat",
    "lernwizard.wizard.unbekannt_hinweis":
        "Tänään kerätyt kasvot, jotka eivät sovi yhteenkään tunnettuun "
        "henkilöön — voit nimetä, yhdistää tai vaimentaa ne siellä heti; "
        "siihen ei tarvita oppimisajoa.",
    "lernwizard.wizard.start_titel": "Lähtötilanne",
    "lernwizard.wizard.start_hinweis":
        "Siivouskytkin automaattisesti kerätyille tuntemattomille: tulee "
        "nimeämisvaiheen mukana.",
    "lernwizard.wizard.knopf_letzte": "viimeiset {n}",
    "lernwizard.wizard.knopf_alle": "KAIKKI tavoitettavat",
    "lernwizard.wizard.attr_eigen": "oma N",
    "lernwizard.wizard.knopf_go": "aja",
    "lernwizard.wizard.scope_titel": "Laajuus (tapahtumat, ei päivät)",
    "lernwizard.wizard.scope_hinweis":
        "KAIKKI käy läpi koko tavoitettavan historian (rajana Frigaten "
        "säilytysaika — alla oleva yhteenveto näyttää, kuinka pitkälle).",
    "lernwizard.wizard.auswahl_titel": "Sinun valintasi",
    "lernwizard.wizard.auswahl_zeile":
        "viimeiset {n} henkilötapahtumaa = taaksepäin {wann} asti · "
        "{clips} saatavilla olevan leikkeen kanssa",
    "lernwizard.wizard.auswahl_ohne_clip":
        "{n} vanhempaa ilman leikettä ohitetaan",
    "lernwizard.wizard.auswahl_hinweis":
        "Leikkaus on tarkasti kohdassa N — valinnan täydentäminen "
        "kokonaisiksi käynneiksi tulee ryhmittelyvaiheen mukana.",
    "lernwizard.wizard.auswahl_durchsucht":
        '{k} näistä {n} on jo käyty läpi — valinnalla "ohita läpikäydyt '
        'tapahtumat" ajo ottaa niiden sijaan vanhempia tapahtumia (kortti '
        'näyttää, mihin se päätyy).',
    "lernwizard.wizard.q_teilgemessen":
        "analyysin nopeus mitattu TÄLLÄ koneella; latausarvio käyttää "
        "oletusarvoja",
    "lernwizard.wizard.q_gemessen": "mitattu TÄLLÄ koneella",
    "lernwizard.wizard.q_skip": ", mittaus ohitettu tällä koneella ({grund})",
    "lernwizard.wizard.q_wartet":
        ", mittaus odottaa vapaata analyysipaikkaa …",
    "lernwizard.wizard.q_laeuft": ", mitataan juuri nyt …",
    "lernwizard.wizard.q_rueckfall":
        "korvaavat arvot — täällä ei ole vielä mitattu",
    "lernwizard.wizard.dauer_titel": "Arvioitu kesto",
    "lernwizard.wizard.dauer_zeile":
        "analyysi ~{analyse} · leikkeiden lataukset ~{download} · "
        "kertaluonteinen lämmittely {kalt}",
    "lernwizard.wizard.dauer_gesamt": "yhteensä ~{gesamt}",
    "lernwizard.wizard.schwellen_titel":
        "Kynnysarvot (säädettävissä lisäasetuksissa)",
    "lernwizard.wizard.frage":
        "Opitaanko kaikista {n} tapahtumasta? Arvioitu kesto ~{gesamt} "
        "(analyysi {analyse} + lataukset {download}). Ajon voi keskeyttää "
        "milloin tahansa.",
    "lernwizard.wizard.fps_titel": "Analyysin kuvat sekunnissa",
    "lernwizard.wizard.knopf_start": "Luo tämä ajo",
    "lernwizard.seg.vorbereiten": "Valmistele",
    "lernwizard.seg.sammeln": "Kerää kasvot",
    "lernwizard.seg.sortieren": "Lajittele ryhmiin",
    "lernwizard.status.laeuft_seit": "käynnissä {dauer}",
    "lernwizard.status.rest": "{rest} jäljellä",
    "lernwizard.status.fertig_in": "valmistui ajassa {dauer}",
    "lernwizard.balken.suchen": "Etsitään kasvoja",
    "lernwizard.balken.pose": "Pään asento",
    "lernwizard.balken.erkennen": "Tunnistetaan kasvoja",
    "lernwizard.balken.z_frames": "kuva {f}/{s}",
    "lernwizard.balken.z_posen.eins": "{n} asento",
    "lernwizard.balken.z_posen.viele": "{n} asentoa",
    "lernwizard.balken.z_erkannt.eins": "{n} tunnistettu",
    "lernwizard.balken.z_erkannt.viele": "{n} tunnistettu",
    "lernwizard.balken.wartet": "odottaa",
    "lernwizard.balken.clip": "haetaan leikettä …",
    "lernwizard.balken.fertig": "valmis",
    "lernwizard.status.aufnahmen": "tallenteet: {n}",
    "lernwizard.status.bilder": "tähän asti {n} kuvaa kerätty",
    "lernwizard.status.wartet": "odottaa: {was}",
    "lernwizard.status.unterbrochen": "pysäytetty kohdassa {n}/{m}: {grund}",
    "lernwizard.puls.working": "työskentelee — päivitetty {s} s sitten",
    "lernwizard.puls.stumm":
        "ei päivitystä {s} s aikana — pitkä leike voi kestää minuutteja; "
        "jos tämä kasvaa edelleen, katso /log",
    "lernwizard.zeile.kaputt": "{n} lukukelvotonta riviä laskettu",
    "lernwizard.zeile.anker_link": "katso {n} ankkuriryhmää",
    "lernwizard.ergebnis.bilder.eins": "kerätty {n} kuva",
    "lernwizard.ergebnis.bilder.viele": "kerätty {n} kuvaa",
    "lernwizard.ergebnis.aufnahmen.eins": "{n} tallenteesta",
    "lernwizard.ergebnis.aufnahmen.viele": "{n} tallenteesta",
    "lernwizard.ergebnis.gruppen.eins": "lajiteltu {n} ryhmään",
    "lernwizard.ergebnis.gruppen.viele": "lajiteltu {n} ryhmään",
    "lernwizard.ergebnis.beiseite": "({n} karsittu)",
    "lernwizard.kachel.lauf": "Oppimisajo",
    "lernwizard.kachel.sammeln": "Kerää &amp; lajittele",
    "kalib.titel": "Kameran kalibrointi",
    "kalib.knopf": "Kalibrointi",
    "kalib.knopf_tip":
        "Kameran kalibrointi: rajat ilmoituksille, varastolle ja "
        "viitekatalogille",
    "kalib.uebersicht.erklaerung":
        "Yksi kamera, yksi arvojoukko. Laatuasteikot vaihtelevat "
        "kamerasta kameraan — yhdellä kokoonpanolla mitattuna yhden "
        "kameran tunnistettavuuden mediaani oli yli kaksinkertainen "
        "toiseen verrattuna. Valitse kamera, jonka rajat haluat asettaa.",
    "kalib.uebersicht.leer": "Ei vielä kameroita",
    "kalib.uebersicht.leer_hinweis":
        "Heti kun Frigate ilmoittaa kameroista, ne ilmestyvät tähän.",
    "kalib.grenze.titel": "Mitä kalibrointi tekee — ja mitä se ei tee",
    "kalib.grenze.satz":
        "Se päättää, mikä kuva näytetään tai lähetetään, mitkä kasvot "
        "säilytetään varastona ja mistä niistä voi tulla tallennettu "
        "viite. Se ei koskaan päätä, kuka tunnistetaan: nimitarkistus "
        "näkee jokaiset kasvot, suodattamatta. Se on mitattu, ei oletettu "
        "— suodattaminen ennen äänestystä kustansi vahvistuksia.",
    "kalib.kachel.eigene": "omat arvot",
    "kalib.kachel.vorgabe": "oletusarvot",
    "kalib.kachel.fremd": "ei Frigatessa",
    "kalib.kachel.fremd_tip":
        "Tällä kameralla on kalibrointiarvot, mutta Frigate ei enää "
        "ilmoita siitä. Arvot säilyvät, mitään ei poisteta.",
    "kalib.kachel.offline": "Frigate ei ole yhdistetty",
    "kalib.kachel.offline_tip":
        "Tämä kamera tunnetaan siitä, mitä tänne on tallennettu — sen "
        "arvoista ja kuvista. Frigate ei juuri nyt vastaa, joten on "
        "avoinna, onko sitä siellä enää. Kalibrointi onnistuu silti.",
    "kalib.kachel.vorrat": "{n}/{deckel} kuvaa",
    "kalib.kachel.vorrat_aus":
        "Kuvien kerääminen on pois (Advanced, calibration samples).",
    "kalib.kachel.stand": "viimeksi {wann}",
    "kalib.kachel.leer": "Ei vielä kuvia",
    "kalib.kachel.leer_hinweis":
        "Kuvia tulee käynnissä olevalta vahdilta ja "
        "tapahtuma-analyyseistä — tai hae niitä nyt.",
    "kalib.kachel.bilanz_keine":
        "Materiaalihaku tarkisti {ev} tapahtumaa: tältä kameralta ei "
        "löytynyt kasvoja — näin laaja yleiskuva ei voi syöttää "
        "kalibrointia.",
    "kalib.kachel.bilanz_klein":
        "Materiaalihaku tarkisti {ev} tapahtumaa: kasvoja löytyi, mutta "
        "kaikki olivat liian pieniä tai liian heikkoja varastoon "
        "(keräysrajan alla).",
    "kalib.kachel.bilanz_zulauf":
        "Materiaalihaku tarkisti {ev} tapahtumaa ja löysi käyttökelpoista "
        "materiaalia, mutta mikään ei saavuttanut varaston laatua — aja "
        "haku uudelleen tai ilmoita tästä.",
    "kalib.kachel.werte":
        "havainto {det} · vaikutelma {e} · tunnistettavuus {tw} · asento "
        "{p}",
    "kalib.kachel.katalog": "katalogin raja {e} / {tw}",
    "kalib.quelle.kamera": "oma",
    "kalib.quelle.global": "yleinen varasääntö",
    "kalib.quelle.aus": "pois",
    "kalib.knopf_kalibrieren": "Kalibroi",
    "kalib.knopf_fuellen": "Etsi tuoretta materiaalia",
    "kalib.knopf_leeren": "Poista varasto",
    "kalib.global.titel": "Yleinen varasääntö",
    "kalib.global.satz":
        "Nämä arvot pätevät kameroihin, joilla ei ole omia: ne ovat raja, "
        "jolla oppimisajo päättää, mitkä kasvot se säilyttää ja mistä "
        "niistä voi tulla tallennettu viite.",
    "kalib.global.katalog": "katalogin raja {e} / {tw}",
    "js.kalib.start": "etsitään materiaalia …",
    "js.kalib.lauf": "{i}/{n} tapahtumaa · {bilder} kuvaa",
    "js.kalib.fertig": "{bilder} kuvaa {events} tapahtumasta",
    "js.kalib.fehler": "materiaalihaku ei onnistunut",
    "lernwizard.kachel.benennen": "Älykäs nimeäminen",
    "lernwizard.kachel.fertig": "Valmis &mdash; ne lasketaan",
    "lernwizard.such.titel": "Etsi tapahtumista kasvoja",
    "lernwizard.such.klein": "käy tallenteitasi taaksepäin",
    "lernwizard.pop.satz":
        "Käy tallenteitasi taaksepäin ja kerää kasvoja. Arjessa "
        "järjestelmä oppii itsestään lisää.",
    "lernwizard.pop.label_letzte": "Käy taaksepäin viimeiset",
    "lernwizard.pop.wort_events": "tapahtumaa",
    "lernwizard.pop.hint_n":
        "kuinka monta tuoreinta tallennetta tarkistetaan (enintään {max})",
    "lernwizard.pop.label_tag": "Yksi kokonainen päivä:",
    "lernwizard.pop.hint_tag":
        "jokainen sen päivän tallenne, olkoon niitä kuinka monta",
    "lernwizard.pop.label_kameras": "vain nämä kamerat",
    "lernwizard.pop.hint_kameras":
        "ei mitään valittuna = kaikki kamerat; useita "
        "Ctrl/Cmd-näppäimellä",
    "lernwizard.pop.wort_fps": "kuvaa sekunnissa",
    "lernwizard.pop.hint_fps":
        "useammat kuvat löytävät useampia kuvakulmia, mutta haku kestää "
        "pidempään",
    "lernwizard.pop.label_skip": "Ohita jo läpikäydyt tapahtumat",
    "lernwizard.pop.hint_skip":
        "jokainen haku etenee kauemmas menneisyyteen &mdash; poista "
        "merkintä, jos haluat käydä tuoreimmat tapahtumat uudelleen",
    "lernwizard.pop.alle_gesichter": "Kaikki kasvot",
    "lernwizard.pop.eine_person": "Vain yksi henkilö:",
    "lernwizard.pop.hint_person":
        "kun henkilö on valittu, sopivat ryhmät listataan ensin &mdash; "
        "mitään ei piiloteta",
    "lernwizard.pop.knopf_start": "Käynnistä haku",
    "lernwizard.knopf_abbrechen": "Peruuta",
    "lernwizard.k1.unbekannt.eins": "{n} tuntematon vierailija tänään:",
    "lernwizard.k1.unbekannt.viele": "{n} tuntematonta vierailijaa tänään:",
    "lernwizard.k1.gestartet": "Ajo käynnistetty {wann}",
    "lernwizard.k1.scope": "laajuus {n} tapahtumaa",
    "lernwizard.k1.kameras": "vain kamerat: {kameras}",
    "lernwizard.k1.tag": "päivä {tag}",
    "lernwizard.k2.satz":
        "Ajo etenee itsekseen &mdash; voit sulkea tämän sivun ja tulla "
        "takaisin.",
    "lernwizard.k2.knopf_abort": "Keskeytä ajo",
    "lernwizard.k2.knopf_resume": "Jatka ajoa",
    "lernwizard.k3.satz_warten":
        "Kenet järjestelmä tunnistaa varmasti, sen se nimeää itse. Kaikki "
        "muu tulee sinulle &mdash; kerro, kuka se on, tai ohita se.",
    "lernwizard.k3.keine_gesichter":
        "Tällä kertaa ei uusia kasvoja &mdash; ei mitään nimettävää. Se "
        "on ihan hyvä: se tarkoittaa vain, ettei tallenteissa ollut "
        "ketään uutta.",
    "lernwizard.knopf_neuer_lauf": "Käynnistä uusi ajo",
    "lernwizard.k3.gruppe_offen":
        "Nykyinen ryhmä on avattu alla, koko leveydeltä.",
    "lernwizard.k3.alle_erledigt": "Kaikki ryhmät on käsitelty.",
    "lernwizard.k3.altes_verfahren":
        "Nämä ryhmät ovat vanhemmasta menettelystä, laatutarkistusta "
        "edeltävältä ajalta. Niiden nimeäminen lajittelisi kuvia, joita "
        "ajo ei enää hyväksy. Käynnistä uusi ajo.",
    "lernwizard.chip.bilder": "{n} kuvaa",
    "lernwizard.k3.verworfen.eins": "{n} ryhmä sinun poistamana &middot;",
    "lernwizard.k3.verworfen.viele": "{n} ryhmää sinun poistamana &middot;",
    "lernwizard.k3.link_einsehen": "katso",
    "lernwizard.k3.done_weiter":
        "{erledigt}/{gesamt} käsitelty &mdash; seuraava on valmiina.",
    "lernwizard.k3.done_punkt": "{erledigt}/{gesamt} käsitelty.",
    "lernwizard.k3.wartend.eins": "{n} ryhmä odottaa sinua.",
    "lernwizard.k3.wartend.viele": "{n} ryhmää odottaa sinua.",
    "lernwizard.k3.auto.eins":
        "{n} tunnistettiin automaattisesti &mdash; katso se halutessasi "
        "läpi.",
    "lernwizard.k3.auto.viele":
        "{n} tunnistettiin automaattisesti &mdash; katso ne halutessasi "
        "läpi.",
    "lernwizard.k4.adopt_bilder.eins": "{n} kuva otettu käyttöön",
    "lernwizard.k4.adopt_bilder.viele": "{n} kuvaa otettu käyttöön",
    "lernwizard.k4.adopt_personen.eins": "{n} henkilölle",
    "lernwizard.k4.adopt_personen.viele": "{n} henkilölle",
    "lernwizard.k4.zaehlen_sofort": "ne lasketaan tunnistuksessa heti.",
    "lernwizard.k4.link_qs": "tarkista kirjaston laatu &#8230;",
    "lernwizard.k4.nichts":
        "tällä kertaa ei otettu käyttöön uusia kuvia (ryhmät ohitettu tai "
        "jo katettu).",
    "lernwizard.k4.wiederholen":
        "Toista tämä muutaman päivän välein, tai anna Tänään-sivun "
        "täydentää tunnettuja henkilöitä välillä.",
    "lernwizard.k4.knopf_faces": "Takaisin Kasvoihin",
    "lernwizard.k4.hinweis":
        "Nimetyistä kuvista tulee viitteitä ja ne lasketaan "
        "tunnistuksessa heti.",
    "lernwizard.zw.grund_maessig": "kuvanlaatu vain keskitasoa",
    "lernwizard.zw.attr_clip": "avaa leike",
    "lernwizard.blick.links": "Katse vasemmalle",
    "lernwizard.blick.frontal": "Edestä",
    "lernwizard.blick.rechts": "Katse oikealle",
    "lernwizard.blick.leer":
        "ryhmässä ei ole käyttökelpoisia kuvia tästä kuvakulmasta",
    "lernwizard.blick.legende":
        "({gut} hyvää, {grenz} rajatapausta {n} tarkistetusta)",
    "lernwizard.zw.titel": "Ryhmä {pos}/{gesamt} &mdash; kuka tämä on?",
    "lernwizard.zw.titel_auto":
        "Ryhmä {pos}/{gesamt} &mdash; onko tämä {name}?",
    "lernwizard.zw.satz":
        "Yksi ryhmä on tarkoitettu yhdelle henkilölle. Napauta kuvaa "
        "jättääksesi sen pois &mdash; kerro sitten, kuka se on, tai ohita "
        "ryhmä.",
    "lernwizard.bekannt.system": "jo järjestelmässäsi",
    "lernwizard.bekannt.anker": "nimetty toisessa ryhmässä",
    "lernwizard.zw.knopf_adopt": "Ota käyttöön nimellä {name}",
    "lernwizard.zw.knopf_ja": "Kyllä, se on {name}",
    "lernwizard.zw.fehler":
        "kuvatarkistus ei voinut ajaa (katso /log) &mdash; lataa sivu "
        "uudelleen, niin se yritetään uudelleen; Ohita ja Poista toimivat "
        "edelleen.",
    "lernwizard.zw.warte":
        "tarkistetaan tämän ryhmän kuvia viiterajaa vasten &mdash; pari "
        "sekuntia &hellip;",
    "lernwizard.zw.knopf_andere": "Joku muu &#8230;",
    "lernwizard.zw.attr_name": "henkilön nimi (uusi tai olemassa oleva)",
    "lernwizard.zw.knopf_save": "Tallenna nimi",
    "lernwizard.zw.knopf_skip": "Ohita tämä ryhmä",
    "lernwizard.zw.frage_delete":
        "Poistetaanko tämä ryhmä? Sen kuvat poistetaan ja odottava "
        "nimeäminen hylätään. Tätä ei voi peruuttaa.",
    "lernwizard.zw.knopf_delete": "Poista tämä ryhmä",
    "lernwizard.zw.link_detail": "yksityiskohtainen näkymä",
    "lernwizard.zw.detail_zusatz":
        "(kaikki kuvat syineen, asiantuntijavalinta)",
    "lernwizard.erfolg.titel": "Ryhmittely valmis",
    "lernwizard.erfolg.cluster.eins": "{n} kasvoryhmä valmiina:",
    "lernwizard.erfolg.cluster.viele": "{n} kasvoryhmää valmiina:",
    "lernwizard.erfolg.knopf_anker": "Katso ankkuriryhmät",
    "lernwizard.erfolg.hinweis": "avaa ryhmä, niin voit nimetä sen",
    "lernwizard.expert.phasen_titel": "Vaiheet",
    "lernwizard.expert.phasen_hinweis":
        "Valmistelu, keräys, ryhmittely, nimeäminen ja siirto Masteriin "
        "ajetaan tässä buildissa oikeasti — sivukuvat ja "
        "kokovartaloviitteet aktivoituvat tulevien päivitysten myötä.",
    "lernwizard.expert.progress_titel": "Edistyminen",
    "lernwizard.expert.anker_bisher": "ankkureita tähän asti: {n}",
    "lernwizard.expert.progress_rest":
        "luotu {wann} · laajuus {n} tapahtumaa · selviää "
        "uudelleenkäynnistyksistä (jatkaminen sisäänrakennettuna)",
    "lernwizard.expert.lauf_bleibt":
        "tämä ajo säilyy — sen ankkurit pysyvät käytettävissä",
    "nav.bereich.activity": "Toiminta",
    "nav.bereich.faces": "Kasvot",
    "nav.bereich.learn": "Opetus",
    "nav.bereich.person": "Henkilö",
    "nav.bereich.vision": "Vision",
    "nav.bereich.live": "Live",
    "nav.bereich.frigate": "Frigate",
    "nav.bereich.configuration": "Määritykset",
    "nav.bereich.erkennungstest": "Tunnistustesti",
    "nav.bereich.system": "Järjestelmä",
    "nav.heute": "Tänään",
    "nav.ereignisse": "Tapahtumat",
    "nav.offen": "Nimettävät",
    "nav.faces": "Kasvot",
    "nav.gesichter": "Tunnetut",
    "nav.unbekannte": "Tuntemattomat",
    "nav.qualitaet": "Laatu",
    "nav.lernlauf": "Kasvojen oppimisajo",
    "nav.anker": "Ankkurit",
    "nav.lernen": "Ehdotukset",
    "nav.person": "Kehokuvat",
    "nav.person_kontrolle": "Arvioidut kuvat",
    "nav.person_modell": "Mallin tila",
    "nav.personlauf": "Henkilöiden oppimisajo",
    "nav.vision": "Vision-tunnistus",
    "nav.live": "Live-vahdit",
    "nav.live_alerts": "Live-ilmoitukset",
    "nav.erkennung": "Tunnistus",
    "nav.kameras": "Kamerat",
    "nav.benachrichtigungen": "Ilmoitukset",
    "nav.areas": "Alueet",
    "nav.kette": "Tunnistusketju",
    "nav.konfiguration": "Lisäasetukset",
    "nav.erkennungstest": "Tunnistustesti",
    "nav.system": "Järjestelmä",
    "nav.systemstat": "Järjestelmätilastot",
    "nav.sync_auswahl": "Frigate-täsmäytys",
    "nav.frigate": "Frigate",
    "ui.fuss.log": "Palvelun loki",
    "ui.fuss.docs": "Ohjeet",
    "ui.fuss.health": "health",
    "ui.modus.easy": "Easy",
    "ui.modus.expert": "Expert",
    "ui.modus.tooltip":
        "Easy näyttää ydinsivut — Expert näyttää kaiken. Mitään ei "
        "poisteta, Easy vain piilottaa.",
    "ui.live.chip": "Live",
    "ui.theme.knopf": "Teema",
    "ui.last.knopf": "Järjestelmätilastot",
    "ui.last.tooltip": "Järjestelmän kuorma: CPU, RAM, levy, GPU ja tunnistus",
    "ui.theme.tooltip": "Vaihda vaalean ja tumman välillä",
    "ui.theme.aria": "Vaihda väriteemaa",
    "ui.sprache.tooltip":
        "Tämän asennuksen kieli — pätee kaikkiin sivuihin ja ilmoituksiin",
    "ui.upd.link": "päivitys {tag}",
    "ui.upd.tooltip": "Uudempi suslik-versio on saatavilla GitHubissa",
    "ui.upd.titel": "Päivitys saatavilla",
    "ui.upd.satz":
        'Uudempi suslik-image (<b>{tag}</b>) on GitHubissa — <a '
        'href="{url}" target="_blank" rel="noopener '
        'noreferrer">julkaisutiedot</a>. Päivitä vetämällä uusi image ja '
        'käynnistämällä uudelleen; datasi ja asetuksesi säilyvät.',
    "ui.wn.titel": "Mitä uutta",
    "ui.wn.x_tooltip": "Piilota seuraavaan versioon asti",
    "ui.wn.x_aria": "Piilota",
    "ui.wn.mehr": "Näytä kaikki ({n})",
    "ui.wn.weniger": "Näytä vähemmän",
    "titel.setup": "Asennus",
    "titel.anker_detail": "Ankkuri",
    "titel.aehnliche": "Sopivat kasvot",
    "titel.live_kamera": "Live — {kamera}",
    "titel.video": "Video",
    "titel.event": "Tapahtuma",
    "titel.vision_galerie": "Rakenna galleria",
    "titel.hilfe": "Näin se toimii",
    "setup.sprache.titel": "Kieli",
    "setup.sprache.satz":
        "Valitse tämän asennuksen kieli — se pätee heti ja koskee myös "
        "ilmoituksia. Voit vaihtaa sen milloin tahansa ylälaidan "
        "valitsimesta.",
    "js.status.fehler": "virhe",
    "js.status.fehler_gross": "Virhe",
    "js.status.fehler_detail": "virhe: {msg}",
    "js.status.ok": "ok",
    "js.status.speichern": "tallennetaan …",
    "js.status.gespeichert": "tallennettu",
    "js.status.senden": "lähetetään …",
    "js.status.starten": "käynnistyy …",
    "js.status.laeuft": "käynnissä …",
    "js.status.laeuft_wort": "käynnissä",
    "js.status.pruefen": "tarkistetaan …",
    "js.status.suchen": "etsitään …",
    "js.status.lernen": "opetetaan …",
    "js.status.hinzufuegen": "lisätään …",
    "js.status.entfernen": "poistetaan …",
    "js.status.loeschen": "poistetaan …",
    "js.status.hochladen": "lähetetään …",
    "js.status.wiederherstellen": "palautetaan …",
    "js.status.ueberspringen": "ohitetaan …",
    "js.status.siehe_log": "katso palvelun loki",
    "js.status.diagnose": "diagnoosi",
    "js.einheit.min": "{n} min",
    "js.einheit.s": "{n} s",
    "js.einheit.klammer_s": "({n} s)",
    "js.allg.abbrechen": "Peruuta",
    "js.neustart.zurueck": "Palvelu on takaisin, ladataan …",
    "js.neustart.kommt": "Palvelu palaa kohta …",
    "js.neustart.gespeichert":
        "Tallennettu. Palvelu käynnistyy uudelleen, odota hetki …",
    "js.neustart.warten": "Palvelu käynnistyy uudelleen, odota hetki …",
    "js.konfig.frage":
        "Tallennetaanko määritykset ja käynnistetäänkö palvelu uudelleen?",
    "js.lernlauf.fps_zeile": "≈ yhteensä ~{dauer} nopeudella {fps}/s",
    "js.lernlauf.tag_fehlt": "valitse ensin päivä",
    "js.lernlauf.abbruch_frage": "Keskeytetäänkö tämä oppimisajo?",
    "js.notif.frage":
        "Tallennetaanko ilmoitusasetukset ja käynnistetäänkö palvelu "
        "uudelleen?",
    "js.frigate.ro_frage":
        "Vaihdetaanko VAIN LUKU -tilaan? suslik lakkaa kirjoittamasta "
        "Frigateen.",
    "js.frigate.rw_frage":
        "Otetaanko KIRJOITUS Frigateen käyttöön (sub_labels + viitteiden "
        "täsmäytys)?",
    "js.catchup.frage":
        "Ohitetaanko tästä lähtien käynnistyksessä väliin jääneet "
        "tapahtumat? Palvelu käynnistyy uudelleen tämän vuoksi.",
    "catchup.knopf": "Nouda puuttuvat",
    "catchup.knopf.tooltip": "Käsittelemättömiä tapahtumia odottaa",
    "catchup.dlg.titel": "Nouda käsittelemättömät tapahtumat",
    "catchup.dlg.label_stunden": "Mene taaksepäin",
    "catchup.dlg.wort_stunden": "tuntia",
    "catchup.dlg.label_limit": "Enintään",
    "catchup.dlg.wort_events": "tapahtumaa",
    "catchup.dlg.fuss":
        "Noudetaan vain tapahtumat, joita ei ole koskaan analysoitu. "
        "Asetuksesi pysyvät ennallaan.",
    "catchup.dlg.abbrechen": "Peruuta",
    "catchup.dlg.los": "Nouda",
    "js.catchup.spanne": "{von}–{bis}",
    "js.catchup.geklemmt":
        "Mahdollisia ovat vain {h} h ja {n} tapahtumaa. Ajetaanko niillä?",
    "js.catchup.nicht_bereit":
        "Opeta ensin henkilö, sitten nämä voidaan tarkistaa.",
    "js.catchup.warten": "Käsittelemättömiä tapahtumia jonossa: {n}",
    "antwort.catchup_gestartet":
        "Noudan viimeiset {stunden} h, enintään {n} tapahtumaa.",
    "antwort.catchup_laeuft": "Noutoajo on jo käynnissä.",
    "js.restore.frage":
        'Palautetaanko määritykset kohteesta "{name}"? Tämä korvaa '
        'nykyiset asetukset ja käynnistää palvelun uudelleen.',
    "js.vollrestore.frage":
        'Palautetaanko KOKO varmuuskopio "{name}"? Tämä korvaa asetukset, '
        'viitteet ja kaiken opitun materiaalin ja käynnistää sitten '
        'palvelun uudelleen.',
    "js.vollrestore.laeuft":
        "lähetetään ja palautetaan … (suuret tiedostot vievät aikansa)",
    "js.enroll.fehler": "Virhe: {msg}",
    "js.enroll.person_fehlt": "Valitse henkilö tai syötä uusi.",
    "js.upload.fehlt": "Valitse henkilö (valikosta tai uusi) ja tiedosto.",
    "js.upload.trotzdem": "{msg}\n\nLisätäänkö silti?",
    "js.anlernen.frage":
        'Otetaanko ryhmä käyttöön nimellä "{person}" (parhaista kuvista '
        'tulee viitteitä)?',
    "js.anlernen.name_frage": "Uuden henkilön nimi:",
    "js.anlernen.person_fehlt": "Valitse olemassa oleva henkilö.",
    "js.auswahl.gesicht_fehlt": "Merkitse vähintään yhdet kasvot.",
    "js.auswahl.bild_fehlt": "Valitse vähintään yksi kuva.",
    "js.vorschlag.keine": "Ei suositeltuja kasvoja.",
    "js.vorschlag.alle_frage":
        "Lisätäänkö kaikki {n} suositellut kasvot henkilölle {person}? "
        "Niistä tulee heti viitteitä.",
    "js.vorschlag.frage": "Lisätäänkö {n} kasvot henkilölle {person}?",
    "js.vorrat.frage":
        "Lisätäänkö {n} varastokasvot henkilölle {person}? Niistä tulee "
        "heti viitteitä (pysyvät paikallisina, ei vientiä).",
    "js.qs.fortschritt": "tarkistetaan kuvaa {i}/{n} …",
    "js.sync.frage": "Täsmäytetään: {richtung}?",
    "js.sync.modell_laedt": "malli latautuu …",
    "js.sync.fortschritt": "{done}/{total} kasvoa ({current}) {pct} %",
    "js.sync.fertig":
        "valmis: {ok} ok, {gate} ohitettu — sivu latautuu uudelleen …",
    "js.sync.fehler": "täsmäytys epäonnistui: {grund}",
    "js.syncauswahl.knopf": "Siirrä {n} valittua Frigateen",
    "js.syncauswahl.nichts": "Ei mitään valittuna",
    "js.syncauswahl.nichts_klein": "ei mitään valittuna",
    "js.syncauswahl.skip": "ohita",
    "js.syncauswahl.restore": "palauta",
    "js.syncauswahl.wieder": "tarjoa uudelleen",
    "js.syncauswahl.zurueck_laeuft": "palautetaan …",
    "js.syncauswahl.frage": "Lähetetäänkö {n} viitekuvaa Frigateen?",
    "js.syncauswahl.fehl_knopf": "siirto epäonnistui",
    "js.syncauswahl.fortschritt": "{done}/{total} ({current}) {pct} %",
    "js.syncauswahl.fertig":
        "valmis: {ok} lähetetty, {gate} ei hyväksytty — sivu latautuu "
        "uudelleen …",
    "js.syncauswahl.fehler": "siirto epäonnistui: {grund}",
    "js.vorpruef.haengt":
        "esitarkistus näyttää jumittavan — lataa sivu uudelleen ja yritä "
        "uudestaan",
    "js.vorpruef.laeuft": "kuvia tarkistetaan … {fertig}/{gesamt}",
    "js.vorpruef.fehler": "esitarkistus epäonnistui: {grund}",
    "js.vorpruef.fertig": "esitarkistus valmis — sivu latautuu uudelleen …",
    "js.import.fortschritt": "ladataan {done}/{total} ({current}) {pct} %",
    "js.import.fertig_wiz":
        "✓ {n} tuotu — piirteitä lasketaan kiihdyttimellä …",
    "js.import.knopf_fertig": "Tuotu ✓",
    "js.import.fehler": "tuonti epäonnistui: {grund}",
    "js.import.knopf": "Tuo kasvot",
    "js.import.knopf_ges": "Tuo kasvot Frigatesta",
    "js.import.fertig_ges":
        "✓ {n} tuotu — piirteitä lasketaan, sivu latautuu uudelleen …",
    "js.ref.frage": "Poistetaanko henkilön {person} viitekuva?",
    "js.ref.batch_frage": "Poistetaanko {n} kuvaa?",
    "js.ref.batch_alle_frage":
        "Nämä ovat KAIKKI {n} henkilön {person} viitekuvaa. Ilman "
        "viitettä {person} ei voi enää tunnistaa. Kuvat siirtyvät "
        "roskakorikansioon ja ne voi siirtää takaisin. Jatketaanko?",
    "js.dienst.nicht_erreichbar":
        "palvelua ei tavoiteta — yritä hetken kuluttua uudelleen.",
    "js.unb.tick": "{phase} … {s} s",
    "js.unb.besucher_frage":
        'Sivuutetaanko tunnettuna vieraana? Se ei enää laukaise '
        'ilmoituksia. (Voi aktivoida milloin tahansa uudelleen alta '
        'kohdasta "tunnetut vierailijat".)',
    "js.unb.merge_frage": "Yhdistetäänkö?",
    "js.unb.name_fehlt": "Syötä nimi (uusi tai olemassa oleva henkilö).",
    "js.unb.benennen_frage":
        'Liitetäänkö henkilöön "{person}"? Parhaista kuvista tulee '
        'viitteitä.',
    "js.unb.teil_frage":
        'Liitetäänkö {n} merkittyä kuvaa henkilöön "{person}"? Loppu '
        'ryhmästä jää Tuntemattomiin.',
    "js.unb.objekt_frage":
        'Merkitäänkö "ei henkilö" (pensas, heijastus, pysäköity auto)? Se '
        'ei enää näy vierailijana; kohdassa "ei henkilöitä" tämän voi '
        'peruuttaa.',
    "js.person.loesch_frage": 'Poistetaanko KAIKKI viitteet ja nimi "{person}"?\nKuvat siirtyvät roskakorikansioon (palautettavissa).\n\nKirjoita nimi vahvistukseksi:',
    "js.person.name_falsch": "Nimi ei täsmännyt — mitään ei poistettu.",
    "js.person.umbenennen_frage": 'Nimeä "{person}" uudelleen — korjaa nimi alle.\n\nHuomioi:\n- omat automaatiosi (Home Assistant / MQTT) vertaavat nimeä sanomassa ja ne on päivitettävä\n- jos Frigate-vienti on päällä, vanha nimi jää Frigaten puolelle (sen API ei osaa nimetä uudelleen)\n- menneet snapshotit, lokit ja varmuuskopiot säilyttävät vanhan nimen',
    "js.person.umbenennen_lauf": "nimetään uudelleen — {phase} {i}/{n}",
    "js.areas.fehl": "tallennus epäonnistui — onko palvelu tavoitettavissa?",
    "js.areas.name_fehlt": "Syötä ensin alueen nimi.",
    "js.areas.existiert": "Tämä alue on jo olemassa.",
    "js.areas.entfernen_frage":
        'Poistetaanko alue "{name}"? Sen kamerat siirtyvät takaisin '
        'Defaultiin — muu ei muutu.',
    "js.personlauf.abbruch_frage":
        "Keskeytetäänkö tämä henkilöiden oppimisajo? Kerätyt kuvat "
        "säilyvät.",
    "js.personlauf.verwerfen_frage":
        "Hylätäänkö ajo {lid} kokonaan? Kaikki sen kuvat poistetaan; uusi "
        "ajo voi kerätä uudelleen milloin tahansa.",
    "js.vision.nicht_erreichbar":
        "palvelua ei tavoitettu — mitään ei tallennettu",
    "js.vision.gespeichert":
        "tallennettu — tunnistus käyttää tästä lähtien tätä yhteyttä",
    "js.vision.gespeichert_neustart":
        "tallennettu — palvelu käynnistyy kohta uudelleen",
    "js.vision.gespeichert_reload":
        "tallennettu — palvelu käynnistyy uudelleen, tämä sivu latautuu "
        "kohta uudelleen",
    "js.vision.treffer": "{n}/2 oikein",
    "js.vision.tokens": "{ist} tokenia vs {soll}",
    "js.vision.dirty_titel": "Et ole tallentanut tätä yhteyttä",
    "js.vision.dirty_text":
        'Testi käyttäisi juuri kirjoittamiasi arvoja. Tunnistus käyttää '
        'edelleen TALLENNETTUA yhteyttä, kunnes painat "Tallenna yhteys" '
        '— pelkkä vihreä testi ei muuta päätelmiä.',
    "js.vision.dirty_save": "Tallenna ensin, testaa sitten",
    "js.vision.dirty_test": "Testaa tallentamatta",
    "js.vision.stufe1": "tavoitettavuus ja malli",
    "js.vision.stufe2": "pakkovalinnan muotokoe",
    "js.vision.stufe3": "tokenien määrä",
    "js.vision.stufe_laeuft":
        "vaihe {nr}/3 — {name} … (paikallinen malli CPU:lla voi kestää "
        "minuutteja)",
    "js.vision.test_fehl": "testiä ei voitu ajaa",
    "js.vision.stufe_stop": "pysähtyi vaiheessa {nr} — katso alla oleva loki",
    "js.vision.fertig": "valmis — {ampel}",
    "js.vision.stufe_fehl": "vaihetta {nr} ei voitu ajaa",
    "js.vision.neustart_warte":
        "palvelu ei juuri nyt vastaa — tämä sivu latautuu kohta uudelleen",
    "js.vision.prompt_frage": "Palautetaanko kysymys oletussanamuotoon?",
    "js.vision.prompt_zurueck":
        'oletussanamuoto palautettu — ota se käyttöön painamalla '
        '"Tallenna yhteys"',
    "js.vision.kachel_frage":
        "Sinulla on tallentamattomia muutoksia. Palveluntarjoajan vaihto "
        "hylkää ne. Jatketaanko?",
    "js.vision.pick": "— valitse —",
    "js.vision.untested": "täällä testaamaton",
    "js.vision.neu_pruefen":
        "yhteys on muuttunut — tarkista uudelleen, niin näet sen mallit",
    "js.vision.key_laeuft":
        "kysytään palveluntarjoajalta, mitkä mallit ovat käytettävissä …",
    "js.vision.key_fehl": "tarkistus epäonnistui",
    "js.vision.key_fehl2": "tarkistusta ei voitu ajaa",
    "js.rt.start": "Vision-ajo käynnistyy …",
    "js.rt.fehl": "ajoa ei voitu käynnistää",
    "js.rt.nach_fehl": "ei voitu käynnistää",
    "js.vw.geliehen": "riviltä {reihe}",
    "js.vw.vergessen_frage":
        "Unohdetaanko kuvat, jotka hylkäsit tästä galleriasta? Niitä "
        "voidaan ehdottaa uudelleen.",
    "js.vw.leer_frage":
        "{n} solua ei voitu täyttää. Hyväksytäänkö galleria silti?",
    "js.vw.kopiert": "kuvia kopioidaan galleriaan …",
    "js.live.phase_verbinden": "Yhdistetään",
    "js.live.phase_messen": "Mitataan",
    "js.live.phase_auswerten": "Arvioidaan",
    "js.live.phase_abbruch": "Keskeytetään",
    "js.live.rest": " — {n} s jäljellä",
    "js.live.auftrag_zeile":
        "{art} kamerassa {kamera}: {phase}{rest}{pausiert}",
    "js.live.messung": "Kuormamittaus",
    "js.live.quelltest": "Lähdetesti",
    "js.live.pausiert": " — vahdit pysäytetty mittauksen ajaksi ({liste})",
    "js.live.job_laeuft":
        "lähdetesti käynnissä (apuprosessi, jopa ~2 minuuttia) …",
    "js.live.vorrat_leeren_frage":
        "Poistetaanko tämän kameran kalibrointikuvat? Niitä ei voi "
        "palauttaa; vahti alkaa kerätä uudelleen tästä hetkestä.",
    "js.live.job_ok": "lähdetesti valmis: {text}",
    "js.live.job_fehl": "lähdetesti EPÄONNISTUI: {text}",
    "js.live.messung_fehl": "kuormamittaus epäonnistui: {grund}",
    "js.live.test_fehl": "lähdetesti epäonnistui: {grund}",
    "auftritte.unbek.zaehlung": "+{n} ilman osumaa (yleensä samat henkilöt)",
    "auftritte.unbek.name": "Tuntematon {nummer}",
    "auftritte.unbek.ohne_treffer.eins":
        "{n} tapahtuma, jossa kasvot ilman osumaa",
    "auftritte.unbek.ohne_treffer.viele":
        "{n} tapahtumaa, joissa kasvot ilman osumaa",
    "auftritte.nav.zurueck_heute": "&#8592; Tänään",
    "auftritte.unbek.titel": "Tuntematon",
    "auftritte.unbek.leer_link": "Tältä linkiltä puuttuu käynti.",
    "auftritte.unbek.leer_weg": "Tämä käynti ei ole enää päivänäkymässä.",
    "auftritte.unbek.leer_weg_hinweis":
        "Päivä on mahdollisesti ryhmitelty uudelleen — avaa se uudelleen "
        "Tänään-sivulta.",
    "auftritte.unbek.leer_pool": "Tälle käynnille ei ole kerättyjä kasvoja.",
    "auftritte.unbek.leer_pool_hinweis":
        "Kerätyt kuvat on mahdollisesti sillä välin siivottu.",
    "auftritte.knopf.video": "video",
    "auftritte.karte.faces.eins": "{n} kasvot",
    "auftritte.karte.faces.viele": "{n} kasvoa",
    "auftritte.karte.kameras.eins": "{n} kamera",
    "auftritte.karte.kameras.viele": "{n} kameraa",
    "auftritte.unbek.mehr_im_lauf": "+{n} muuta tässä käynnissä",
    "auftritte.unbek.ein_lauf": "yksi käynti",
    "auftritte.zuweisen.titel": "Kuka tämä on?",
    "auftritte.zuweisen.satz":
        "Nämä ovat TÄMÄN käynnin kasvot. Merkitse ne, jotka todella "
        "kuuluvat henkilölle &mdash; kelvoton jää jäljelle. Anna niille "
        "nimi (uusi tai olemassa oleva), niin ne opetetaan; jos et tee "
        "mitään, ne pysyvät tuntemattomina.",
    "auftritte.zuweisen.knopf_alle": "Valitse kaikki",
    "auftritte.zuweisen.knopf_keine": "Ei mitään",
    "auftritte.zuweisen.attr_person": "henkilö (uusi tai olemassa oleva)",
    "auftritte.zuweisen.knopf_zuweisen": "Lisää valitut kasvot",
    "auftritte.zuweisen.js_keine": "merkitse vähintään yhdet kasvot",
    "auftritte.zuweisen.js_name": "syötä henkilön nimi",
    "auftritte.zuweisen.js_lernt": "opetetaan…",
    "auftritte.zuweisen.js_fehler": "virhe",
    "auftritte.unbek.titel_lauf": "Tuntematon {nummer} — käynti",
    "auftritte.leer_person": "Tuntematon henkilö.",
    "auftritte.leer_person_hinweis": "Valitse henkilö Tänään-sivulta.",
    "auftritte.titel": "Esiintymiset",
    "auftritte.nav.attr_tag": "takaisin päivään",
    "auftritte.nav.attr_vortag": "edellinen päivä",
    "auftritte.kopf.passzahl.eins": "{n} käynti",
    "auftritte.kopf.passzahl.viele": "{n} käyntiä",
    "auftritte.nav.attr_kein_morgen": "ei tulevia päiviä",
    "auftritte.nav.attr_folgetag": "seuraava päivä",
    "auftritte.titel_person": "{person} — esiintymiset",
    "auftritte.leer_passe":
        "Ei vahvistettuja käyntejä henkilöltä {person} tänä päivänä.",
    "auftritte.leer_passe_hinweis": "Katso ympärille päivänuolilla.",
    "auftritte.karte.kein_bild": "ei kuvaa",
    "auftritte.thumb.zusatz_unbestaetigt": " — ei vahvistettu täällä",
    "auftritte.thumb.zusatz_referenz": " — viitteissä",
    "auftritte.thumb.ohne_gesicht.eins": "+{n} tapahtuma ilman kasvoja",
    "auftritte.thumb.ohne_gesicht.viele": "+{n} tapahtumaa ilman kasvoja",
    "auftritte.knopf.ereignis": "etsi tästä kuvasta sopivia kasvoja",
    "auftritte.knopf.durchgang":
        "tarkista myös tämän käynnin muut {n} tapahtumaa",
    "auftritte.thumb.mehr_ereignisse": "+{n} muuta tapahtumaa",
    "auftritte.auch_dabei": "mukana myös: {namen}",
    "auftritte.thumb.hinweis_referenz": "vihreä reunus = jo viitteissä",
    "auftritte.karte.best_punkt": "vahvistettu klo {zeit}",
    "auftritte.karte.best_spanne": "vahvistettu {von} &ndash; {bis}",
    "auftritte.karte.badge_laeuft": "käynnissä",
    "auftritte.karte.pass_nr": "Käynti {n}",
    "auftritte.karte.events.eins": "{n} tapahtuma",
    "auftritte.karte.events.viele": "{n} tapahtumaa",
    "auftritte.karte.best_match": "paras osuma {wert}",
    "auftritte.karte.auch_dabei": "tässä käynnissä myös: {namen}",
    "auftritte.pass.titel": "Käynti",
    "auftritte.pass.leer_event": "Tapahtumaa ei löytynyt.",
    "auftritte.pass.leer_event_hinweis":
        "Se on mahdollisesti liian vanha ja pudonnut lokista.",
    "auftritte.pass.leer_gruppe":
        "Tämä tapahtuma ei kuulu mihinkään ryhmiteltyyn käyntiin.",
    "auftritte.pass.leer_gruppe_hinweis":
        "Ryhmittely tarvitsee koko päivän yhteyden.",
    "auftritte.nav.zurueck_tag": "&#8592; Päivä",
    "auftritte.pass.attr_vor": "päivän edellinen käynti",
    "auftritte.pass.attr_nach": "päivän seuraava käynti",
    "auftritte.pass.kopf": "Käynti {von} &ndash; {bis}",
    "auftritte.pass.label_unbek": "Ei osumaa",
    "auftritte.pass.label_gt": "Nimeäminen",
    "auftritte.pass.badge_fremd": "vahvistettu vieras",
    "auftritte.pass.grund_ohne_zeile":
        "analyze.log ei sisällä riviä syystä — avaa tapahtuma, niin näet "
        "koko lokin",
    "auftritte.pass.grund_ohne_log":
        "tälle tapahtumalle ei ole tallennettu analyze.logia — katso "
        "palvelun loki",
    "auftritte.pass.label_fehler": "Virhe",
    "auftritte.pass.wer": "Kuka",
    "auftritte.pass.titel_zeit": "Käynti {zeit} — {tag}",
    "banner.schoner":
        "Frigate ei vastaa — suslik odottaa ja koettaa muutaman sekunnin "
        "välein, kunnes se palaa; käyttöliittymä näyttää edelleen "
        "paikallista dataa.",
    "banner.fehler":
        "Frigate ei tavoitettavissa (viimeisin virhe {zeit}): {fehler} — "
        "käyttöliittymä näyttää edelleen paikallista dataa.",
    "banner.nachholen.eins":
        "Väliin jääneitä tapahtumia noudetaan viimeiseltä tunnilta: "
        "{gesamt} otettu jonoon, {schlange} jonossa, {arbeit} "
        "analysoitavana",
    "banner.nachholen.viele":
        "Väliin jääneitä tapahtumia noudetaan viimeisiltä {n} tunnilta: "
        "{gesamt} otettu jonoon, {schlange} jonossa, {arbeit} "
        "analysoitavana",
    "banner.nachholen_aus": "Älä nouda jatkossa käynnistyksessä",
    "hinweis.frigate_fr_an":
        "Frigaten oma kasvontunnistus on päällä. suslik ei tarvitse sitä "
        "— se tunnistaa kasvot itse ja toimii kummin päin vain. Voit "
        "kytkeä sen Frigatessa pois, jos et muuten käytä sitä.",
    "ui.hinweis.x_tooltip": "Älä näytä tätä huomautusta enää",
    "ui.hinweis.x_aria": "Piilota huomautus pysyvästi",
    "setupwiz.frigate.status_ok": "✓ Yhdistetty — {n} kameraa löytyi",
    "setupwiz.frigate.status_fehl": "✗ Frigatea ei tavoitettu: {fehler}",
    "setupwiz.frigate.status_fehl_keine": "ei kameroita",
    "setupwiz.frigate.status_fehl_hinweis":
        "Korjaa URL (tai aseta FRIGATE_URL .env-tiedostoon / "
        "docker-composeen) ja testaa uudelleen.",
    "setupwiz.frigate.status_leer": "Syötä Frigaten URL ja testaa yhteys.",
    "setupwiz.frigate.titel": "Yhdistä Frigateen",
    "setupwiz.frigate.satz":
        "suslik lukee kamerasi suoraan Frigaten API:sta (yleensä portti "
        "5000). Yhtäkään kameraa ei ole kovakoodattu.",
    "setupwiz.frigate.knopf_test": "Testaa yhteys",
    "setupwiz.kameras.titel": "Valitse kamerat &amp; ehdot",
    "setupwiz.kameras.satz":
        "Merkitse, mitä kameroita tarkkaillaan; merkitse yksi tai useampi "
        "vyöhyke, jos haluat analysoida vain tapahtumat, jotka ovat "
        "menneet niihin (esim. henkilö puutarhassa). Ei mitään merkittynä "
        "= kaikki tapahtumat.",
    "setupwiz.kameras.satz_ohne":
        "Yhdistä ensin Frigateen — kamerasi ilmestyvät tähän.",
    "setupwiz.backend.titel": "Kiihdytys",
    "setupwiz.backend.verfuegbar": "Käytettävissä tällä koneella:",
    "setupwiz.backend.satz_wahl": "Valitse yksi — CPU toimii aina.",
    "setupwiz.import.titel": "Tuo kasvot Frigatesta",
    "setupwiz.import.zahl_vor": "Frigatella on jo ",
    "setupwiz.import.zahl_mitte": " viitekuvaa ",
    "setupwiz.import.zahl_nach": " henkilöltä.",
    "setupwiz.import.satz":
        "Tuo ne, niin suslik tunnistaa kaikki heti alusta. Kuvat "
        "latautuvat nopeasti, sen jälkeen suslik laskee omat "
        "kasvopiirteensä kiihdyttimelläsi (GPU/NPU).",
    "setupwiz.import.knopf": "Tuo {n} kasvoa Frigatesta",
    "setupwiz.import.satz_leer":
        "Frigatessa ei ole vielä kasvoja. Huomaa: suslik tarvitsee "
        "vähintään yhdet viitekasvot, ennen kuin se voi tunnistaa ketään "
        "— tuo tässä Frigatesta tai lähetä kuvia myöhemmin "
        "Tunnetut-sivulla.",
    "setupwiz.import.satz_ohne":
        "Yhdistä ensin Frigateen — sen jälkeen voit tuoda sen tunnetut "
        "kasvot tässä.",
    "setupwiz.fertig.knopf": "Tallenna &amp; käynnistä suslik",
    "setupwiz.fertig.satz":
        "Tallentaa valintasi ja käynnistää palvelun kertaalleen "
        "uudelleen.",
    "setupwiz.restore.titel": "Onko määritykset jo olemassa?",
    "setupwiz.restore.satz":
        "Jos olet aiemmin vienyt suslikin määritykset (Järjestelmä → "
        "Määritysten varmuuskopio), lataa ne tässä, niin kaikki asetukset "
        "palautuvat ja ohitat ohjatun asennuksen.",
    "setupwiz.restore.knopf": "Lataa määritystiedosto…",
    "setupwiz.write.titel": "Kirjoitetaanko takaisin Frigateen?",
    "setupwiz.write.satz":
        "suslik voi kirjoittaa päätelmänsä takaisin Frigateen "
        "(sub_labels) ja peilata viitteet, jotta molemmat voivat toimia "
        "rinnakkain. Vain luku on turvallinen oletus.",
    "setupwiz.write.opt_ro":
        "Vain luku (suositeltu) — suslik ei koskaan kirjoita Frigateen",
    "setupwiz.write.opt_rw": "Kirjoita takaisin Frigateen (rinnakkaiskäyttö)",
    "setupwiz.willkommen.titel": "Tervetuloa suslikiin",
    "setupwiz.willkommen.satz":
        "Lyhyt ohjattu asennus — tai lataa olemassa olevat määritykset ja "
        "ohita se. Kaikkea tätä voi muokata myöhemmin tavallisilla "
        "sivuilla.",
    "leer.passe_area_heute": "Tänään ei vielä käyntejä alueella {area}.",
    "leer.passe_area_tag": "Tänä päivänä ei käyntejä alueella {area}.",
    "leer.passe_area_hinweis":
        "Ylhäällä oleva All-valinta näyttää koko tontin.",
    "leer.passe_heute": "Tänään ei vielä käyntejä, joissa olisi kasvot.",
    "leer.passe_heute_hinweis":
        "Heti kun joku kulkee tontin yli, käynti ilmestyy tähän.",
    "leer.tag": "Tänä päivänä ei mitään, jossa olisi kasvot.",
    "leer.tag_hinweis":
        "Siirry nuolilla toiseen päivään tai avaa Tapahtumat, niin näet "
        "koko listan.",
    "leer.frigate": "Frigatea ei ole vielä yhdistetty.",
    "leer.frigate_hinweis":
        "Syötä Frigaten URL ohjatussa asennuksessa (Järjestelmä-sivu) — "
        "sitten käynnit ilmestyvät tähän automaattisesti.",
    "leer.refs":
        "Yhdistetty — mutta viitekasvoja ei vielä ole, joten ketään ei "
        "voi tunnistaa.",
    "leer.refs_hinweis":
        "Tuo kasvot Frigatesta tai lähetä kuvia — molemmat "
        "Tunnetut-sivulla. suslik oppii sen jälkeen itse kameroista "
        "lisää.",
    "leer.band_heute": "Tänään ei vielä mitään, jossa olisi kasvot.",
    "leer.band_tag": "Tänä päivänä ei mitään, jossa olisi kasvot.",
    "leer.band_hinweis":
        "Henkilöt ilmestyvät tähän heti, kun käynti on analysoitu.",
    "leer.person_unbekannt": "Henkilö tuntematon.",
    "leer.kamera_unbekannt": "Tuntematon kamera.",
    "leer.kamera_unbekannt_hinweis":
        "Ruudut tulevat vain Frigaten kameralistasta ja tallennetuista "
        "vahdeista.",
    "unbekannte.name": "Tuntematon {nummer}",
    "unbekannte.meta_zeit": " esiintymistä · {zeit}",
    "unbekannte.mehr_bilder": "+{n} kuvaa lisää tässä ryhmässä",
    "unbekannte.knopf_reaktivieren": "aktivoi uudelleen",
    "unbekannte.attr_name": "Nimi (uusi tai olemassa oleva)",
    "unbekannte.attr_wahl": "Valitse tämä ryhmä yhdistämiseen",
    "unbekannte.knopf_zuweisen": "Liitä henkilö",
    "unbekannte.knopf_teil": "Liitä {n} merkittyä",
    "unbekannte.knopf_ignorieren": "Sivuuta",
    "unbekannte.knopf_objekt": "Ei henkilö",
    "unbekannte.knopf_person": "On henkilö",
    "unbekannte.knopf_bulkmerge": "Yhdistä {n} valittua ryhmää",
    "unbekannte.knopf_mehr": "Näytä {n} ryhmää lisää",
    "unbekannte.titel": "Tuntemattomat",
    "unbekannte.anker": "{offen}/{gesamt} ryhmää odottaa vielä sinua",
    "unbekannte.sort_label": "Järjestys",
    "unbekannte.sort_bilder": "eniten kuvia",
    "unbekannte.sort_neu": "uusimmat",
    "unbekannte.filter_label": "Näytä",
    "unbekannte.f_offen": "avoimet",
    "unbekannte.f_wieder": "toistuvat",
    "unbekannte.f_heute": "uudet tänään",
    "unbekannte.f_vorschlag": "ehdotus olemassa",
    "unbekannte.f_besucher": "vaimennetut",
    "unbekannte.f_objekt": "ei henkilöitä",
    "unbekannte.kopf_satz":
        "Kasvot ilman tunnettua osumaa, ryhmiteltyinä toistuviksi "
        "identiteeteiksi.",
    "unbekannte.kopf_satz_zuweisen":
        " liittää ruudun henkilöön (uusi tai olemassa oleva, kirjoita "
        "nimi),",
    "unbekannte.kopf_satz_ignorieren":
        " vaimentaa tunnetun vieraan (ei ilmoitusta).",
    "unbekannte.kopf_satz_auto":
        "Uudet kasvot kerätään automaattisesti jokaisen käynnin jälkeen.",
    "unbekannte.knopf_reorg": "Ryhmittele nyt uudelleen",
    "unbekannte.hinweis_reorg":
        "tarkistaa kerätyt kasvot uudelleen ja rakentaa ryhmät uudestaan "
        "— kerääminen itse tapahtuu automaattisesti (1–2 min)",
    "unbekannte.satz_objekte":
        'Ryhmät, joiden kuvat ovat keskenään lähes samanlaisia eivätkä '
        'muistuta ketään henkilöä — tyypillisesti lokasuoja, katukiveys '
        'tai valokuvio, jota detektori pitää kerta toisensa jälkeen '
        'kasvoina. Ne ovat jäädytettyjä: uusia löytöjä ei koskaan lisätä '
        'tänne (ne muodostavat tuoreita, näkyviä ryhmiä ja ne '
        'tarkistetaan saman säännön mukaan uudelleen) — ryhmät pysyvät '
        'listassa, jotta mitään ei piiloteta. Merkitty käsin tai löydetty '
        'automaattisesti; "On henkilö" palauttaa ryhmän takaisin.',
    "unbekannte.leer": "Tuntemattomia kasvoja ei ole vielä kerätty.",
    "unbekannte.leer_hinweis":
        "Identiteetit ilmestyvät tähän seuraavan tuntemattoman "
        "vierailijan jälkeen.",
    "unbekannte.leer_filter": "Tässä näkymässä ei ole mitään.",
    "unbekannte.leer_filter_hinweis":
        "Muita ryhmiä odottaa ylhäällä toisen suodattimen alla.",
    "livealerts.link_video": "&#9654; video {n}",
    "livealerts.person_unbekannt": "tuntematon",
    "livealerts.trigger.eins": "{n} trigger",
    "livealerts.trigger.viele": "{n} triggeriä",
    "livealerts.kanal_keiner": "ei lähetetty (ei kanavaa)",
    "livealerts.keine_bilder": "ei tallennettuja kuvia",
    "livealerts.titel": "Live-vahtien ilmoitukset",
    "livealerts.kopf.auftritte.eins": "{n} esiintyminen",
    "livealerts.kopf.auftritte.viele": "{n} esiintymistä",
    "livealerts.kopf.satz":
        " {tag} — pikatarkistus, alustava; vahvistettu päätelmä tulee "
        "normaalista analyysistä.",
    "livealerts.kopf.satz_alt":
        "Ennen versiota 0.1.0.190 tehtyihin kirjauksiin ei ole "
        "tallennettu kuvaa eikä nimeä.",
    "livealerts.leer": "Ei live-ilmoituksia sinä päivänä.",
    "video.fehl":
        "&#9888; Transkoodaus epäonnistui — katso palvelun loki (/log).",
    "video.fehl_hinweis":
        "Lataa tämä sivu uudelleen, niin sitä yritetään uudestaan, tai "
        "avaa alkuperäinen leike:",
    "video.warte": "Selainvideota (H.264) valmistellaan&nbsp;…",
    "video.warte_satz":
        "Tämä sivu päivittyy itsestään. Kopio luodaan kertaalleen ja "
        "tallennetaan sen jälkeen välimuistiin.",
    "event.ours_zeile.eins": "{person} — {stufe} (nähty {n} ikkunassa)",
    "event.ours_zeile.viele": "{person} — {stufe} (nähty {n} ikkunassa)",
    "event.ours_keiner": "ei osumaa kenellekään",
    "event.ours_rest.eins": " · {n} muu henkilö: ei osumaa",
    "event.ours_rest.viele": " · {n} muuta henkilöä: ei osumaa",
    "event.grenze":
        "tämän viivan alla: heikot osumat (paras score &lt; {wert}) — "
        "nimi on arvaus, tämä voi olla eri henkilö",
    "event.gruppe_ohne": "Ilman kohdennusta",
    "event.badge_unsicher": "epävarma",
    "event.leer_crops":
        "Tälle tapahtumalle ei ole tallennettu kasvorajauksia.",
    "event.knopf_video": "&#9654; Video",
    "event.knopf_log": "Analyysiloki",
    "event.attr_unvollstaendig":
        "leike epätäydellinen — luettu {gelesen}/{soll} kuvaa; arvioitu "
        "luettavasta osasta",
    "event.badge_unvollstaendig": "⚠ leike epätäydellinen",
    "event.verwurf_grund.analyse_none":
        "Analyysi ei tuottanut tulosta — se keskeytyi tai kaatui",
    "event.verwurf_grund.lesbarkeit_riegel":
        "Alle puolet leikkeen kuvista olivat luettavissa",
    "event.verwurf_grund.clip_fehlt":
        "Leike ei ole enää Frigatessa (säilytysaika umpeutui tai "
        "tapahtuma poistettiin)",
    "event.pass_zurueck": "&#8592; edellinen",
    "event.pass_weiter": "seuraava &#8594;",
    "event.pass_teil": "Osa käyntiä",
    "event.pass_events.eins": "{n} tapahtuma",
    "event.pass_events.viele": "{n} tapahtumaa",
    "event.pass_knopf": "katso käynti",
    "event.label_grund": "Virheen syy",
    "event.grund_ohne_zeile":
        "analyze.log ei sisällä riviä syystä — käytä alla olevaa "
        "loki-painiketta",
    "event.grund_ohne_log":
        "tälle tapahtumalle ei ole tallennettu analyze.logia — katso "
        "palvelun loki (Järjestelmä-sivu)",
    "event.zurueck": "← Tänään",
    "event.label_korrektur": "Korjaa, jos väärin",
    "event.label_wer": "Kuka se oli?",
    "event.h_bilder": "Kuvat",
    "system.ampel.service": "Palvelu",
    "system.ampel.service_info": "käsitelty (yhteensä): {n}",
    "system.ampel.backend": "Backend",
    "system.ampel.backend_ok": "{backend} — itsetarkistus OK",
    "system.ampel.backend_fail":
        "{backend} — {n} itsetarkistusta EPÄONNISTUI, katso palvelun loki",
    "system.ampel.analyse": "Analyysi",
    "system.ampel.analyse_dauer": "viimeisin kesto {s} s",
    "system.ampel.analyse_nie": "ei vielä analyysiä",
    "system.ampel.retry": "Uudelleenyritykset",
    "system.ampel.retry_info":
        "{offen} avointa / {aufgegeben} luovutettu (ikkuna {tage} pv)",
    "system.ampel.frigate_unkonfiguriert":
        "ei vielä asetettu — syötä URL ohjatussa asennuksessa",
    "system.ampel.frigate_ok": "tavoitettavissa",
    "system.ampel.frigate_fehler": "viimeisin virhe {zeit}",
    "system.ampel.mqtt_hb": "heartbeat {s} s sitten",
    "system.ampel.mqtt_kein_hb": "ei vielä heartbeatia",
    "system.ampel.mqtt_pub_aus": "asetettu, julkaisu pois",
    "system.ampel.mqtt_pub_kaputt":
        "asetettu, julkaisija ei käynnistynyt — katso palvelun loki",
    "system.ampel.mqtt_unkonfiguriert": "ei asetettu",
    "system.ampel.disk": "Levytila",
    "system.ampel.disk_info2":
        "{gb} GB vapaana · leikkeiden välimuisti {cache} GB / {max} GB",
    "system.disk.titel": "Levytila",
    "system.disk.satz":
        "Leikkeet ovat välimuisti: säilytetään {tage} päivää, katto {max} "
        "GB, ja karsitaan heti kun vapaana on alle {min} GB (tarkistetaan "
        "jokaisen tapahtuman jälkeen ja päivittäisellä levyvahdilla, joka "
        "tiivistää tahdin 10 minuuttiin, kun tilaa on vähän).",
    "system.disk.knopf": "Siivoa nyt",
    "system.disk.warnung":
        "Vapaana on vain {gb} GB ja leikkeiden välimuisti on jo tyhjä — "
        "vapauta tilaa datalevyltä, muuten uusia tapahtumia ei voi "
        "tallentaa.",
    "system.ampel.ok": "OK",
    "system.ampel.check": "TARKISTA",
    "system.drift.banner":
        "DRIFT-TARKISTUS PUNAINEN viimeksi lisätyn viitteen jälkeen:",
    "system.sync.titel": "Täsmäytys Frigaten kanssa",
    "system.sync.knopf": "Avaa Frigate-täsmäytys",
    "system.sync.satz":
        "Täsmäytyssivu vertaa molempia kirjastoja luokka luokalta, "
        "esitarkistaa jokaisen ehdokkaan samalla tavalla kuin Frigate, "
        "lähettää vain sen, minkä merkitset, ja tuo sen, mikä on vain "
        "Frigatella.",
    "system.sync.fehlt":
        "ei vielä käytettävissä — vaatii tavoitettavan Frigaten ja "
        "vähintään yhdet viitekasvot",
    "system.qc.titel": "Laaturaportti",
    "system.qc.stand": "(tilanne {stand}, {tage} päivää)",
    "system.qc.kopf_gesicht": "kasvot mukana",
    "system.qc.kopf_bestaetigt": "vahvistettu",
    "system.qc.kopf_quote": "osuus ikkunassa",
    "system.backup.titel": "Määritysten varmuuskopio",
    "system.backup.satz":
        "Lataa hakemistoon /data/config tallennetut asetukset yhtenä "
        "JSON-tiedostona tai palauta ne sellaisesta tiedostosta. "
        "Rehellinen laajuus: tänään se on KAMERALEHTI (mukaan lukien sen "
        "tallennetut arvot); kynnykset ja kanavat, jotka on asetettu vain "
        "verifyd.yaml-tiedostossa tai ympäristömuuttujilla, EIVÄT ole "
        "tässä tiedostossa. Opitut henkilöt ja viitteet: käytä alla "
        "olevaa täyttä varmuuskopiota.",
    "system.backup.knopf_download": "Lataa määritykset",
    "system.backup.knopf_restore": "Palauta tiedostosta…",
    "system.backup.careful": "Huomio:",
    "system.backup.careful_config":
        "tämä tiedosto {hinweis} (ilmoituskanavat ja Vision-tunnistus), "
        "jotta palautus toisella koneella todella toimii.",
    "system.backup.restore_satz":
        "Palautus korvaa nykyiset asetukset (edelliset säilyvät "
        ".bak-tiedostona) ja käynnistää palvelun uudelleen.",
    "system.voll.titel": "Täysi varmuuskopio",
    "system.voll.satz":
        "Yksi siirrettävä arkisto, jossa on kaikki, mitä olet tälle "
        "asennukselle opettanut: asetukset, kasvojen viitekirjasto, "
        "oppimisajojen tulokset, koko henkilöntunnistuksen materiaali "
        "(kuvat, läpikäynnistä syntyneet päätelmäsi, koulutetut mallit) "
        "ja tapahtumakirjanpito. Tehty toiselle koneelle siirtymiseen. "
        "Rehellinen laajuus: videoleikkeiden välimuisti ja "
        "tapahtumakohtaiset analyysiartefaktit EIVÄT ole mukana — ne "
        "rakentuvat ajan myötä uudelleen.",
    "system.voll.knopf_download": "Lataa täysi varmuuskopio",
    "system.voll.knopf_restore": "Palauta täysi varmuuskopio…",
    "system.voll.careful": "tämä arkisto {hinweis}.",
    "system.voll.restore_satz":
        "Palautus korvaa nämä osat (jokainen edellinen säilytetään "
        "kertaalleen muodossa *.pre-restore-*) ja käynnistää palvelun "
        "uudelleen. Parin sadan megatavun lähetys voi kestää — jätä sivu "
        "auki.",
    "system.live.titel": "Live-vahdit",
    "system.live.alerts": "Tänään lähetetyt ilmoitukset: {kanaele}",
    "system.live.stoerungen": "Häiriöhuomautuksia tänään: {n}",
    "system.live.knopf": "Avaa Live-vahdit",
    "system.live.quelle":
        "Laskettu enginen omasta ilmoituslokista — vain sanomat, jotka "
        "kanava todella otti vastaan. Live-vahtien ilmoitukset ovat "
        "erillään Tänään-sivun tapahtuma-analyysin ilmoituslaskureista.",
    "system.write.titel": "Takaisinkirjoitus Frigateen",
    "system.write.satz":
        "Kirjoittaako suslik takaisin Frigateen vai lukeeko se vain? Vain "
        "luku on turvallinen oletus; kytke kirjoitus päälle vain "
        "rinnakkaiskäyttöön (Frigaten kasvontunnistus + suslik).",
    "system.write.aktuell": "Nyt:",
    "system.write.zustand_ro": "VAIN LUKU — suslik ei kirjoita Frigateen",
    "system.write.zustand_rw": "KIRJOITTAA Frigateen — sub_labels",
    "system.write.zustand_rw_sync": " + viitteiden täsmäytys",
    "system.write.knopf_rw": "Ota kirjoitus käyttöön",
    "system.write.knopf_ro": "Vain luku",
    "system.titel": "Järjestelmä",
    "system.tools.titel": "Työkalut",
    "system.docs.titel": "Ohjeet",
    "system.docs.link": "Dokumentaatio GitHubissa",
    "vision.zeit.nie": "ei koskaan",
    "vision.titel": "Vision-tunnistus",
    "vision.kopf.dirty": "ei tallennettu",
    "vision.hinweis.titel": "Mitä tähän tarvitset",
    "vision.schalter.knopf_aus": "Kytke pois",
    "vision.schalter.knopf_an": "Kytke päälle",
    "vision.schalter.fehlt": "Puuttuu vielä:",
    "vision.schalter.fehlt_galerien":
        "{n}/{soll} hyväksyttyä galleriaa — rakenna yksi kohdassa "
        "'Rakenna galleria'",
    "vision.schalter.fehlt_test": "vihreä yhteystesti",
    "vision.schalter.fehlt_kandidaten":
        "arvioidut kuvat ehdokkaiden lähteeksi — ne ilmestyvät, kun "
        "käynti on kesken; kytke 'diagnoosikeräys' päälle "
        "Henkilö-sivulla, jos haluat niiden säilyvän",
    "vision.schalter.titel_an": "Vision-tunnistus on päällä",
    "vision.schalter.titel_aus": "Vision-tunnistus on pois",
    "vision.schalter.aus_satz":
        "Niin kauan kuin se on pois, mitään ei lähetetä minnekään eikä "
        "yksikään kuva poistu tältä koneelta.",
    "vision.frage.titel": "Miten vertailua kysytään",
    "vision.frage.doppel_titel":
        "Kysy jokaista paria kahdesti, galleriat vaihdettuina",
    "vision.frage.doppel_satz":
        "Tämä on asemakoe. A ensimmäisessä ajossa ja B vaihdetussa ajossa "
        "tarkoittavat SAMAA galleriaa, joten ristiriita paljastaa mallin, "
        "joka yksinkertaisesti suosii sitä, mikä tulee ensin. Täällä "
        "mitattuna: jokainen väärä vastaus kaikissa testisarjoissamme oli "
        "&bdquo;A&ldquo;, ei koskaan &bdquo;B&ldquo;. Pois kytkeminen "
        "puolittaa pyynnöt &mdash; ja vertailu nojaa silloin yhteen "
        "ainoaan vastaukseen, eikä mikään tarkista sitä.",
    "vision.meld.titel": "Lisäilmoitukset",
    "vision.meld.satz":
        "Molemmat ovat pois, kunnes kytket ne päälle, eikä kumpikaan "
        "muuta olemassa olevia hälytyksiä: Vision ei voi laukaista "
        "hälytystä, peruuttaa sitä eikä kumota kasvo- ja kehoteitä.",
    "vision.meld.judged_titel": "Kerro minulle, kun käynti on arvioitu",
    "vision.meld.judged_satz":
        "Lyhyt huomautus tavanomaisilla kanavillasi heti, kun päätelmä on "
        "valmis &mdash; todellisella äänimäärällä. Se saapuu käynnin "
        "päätyttyä, ja paikallisella mallilla se voi olla minuutteja "
        "myöhemmin. Tietoa, ei hälytys.",
    "vision.meld.alarm_titel":
        "Ilmoita minulle, kun Vision on eri mieltä kuin kehontunnistus",
    "vision.meld.alarm_satz":
        "Laukeaa vain, kun ajo todella tapahtui, malli vastasi eikä se "
        "silti vahvistanut ketään. Se pysyy hiljaa, kun materiaalia ei "
        "yksinkertaisesti ollut tarpeeksi &mdash; se olisi kohinaa. "
        "Opetettujen henkilöiden tunnistaminen on tämän tien vahva puoli, "
        "joten vahvistamatta jättäminen merkitsee jotain; vieraiden "
        "torjuminen on heikko puoli, siksi Vision ei koskaan anna ääntä "
        "siihen suuntaan.",
    "vision.kachel.was_key": "syötät API-avaimen",
    "vision.kachel.was_host": "syötät hostin ja portin",
    "vision.kachel.was_url": "syötät URL:n ja halutessasi avaimen",
    "vision.kachel.titel": "Missä malli ajetaan",
    "vision.kachel.satz":
        "Valitse palveluntarjoaja. Kolmelle nimetylle virallinen "
        "API-osoite on jo sisäänrakennettu &mdash; syötät vain avaimesi. "
        "Mitään ei lähetetä minnekään, ennen kuin painat itse painiketta.",
    "vision.verb.key_gespeichert":
        "&bull;&bull;&bull;&bull; tallennettu &mdash; jätä tyhjäksi, niin "
        "se säilyy",
    "vision.verb.key_pflicht_ph": "liitä avaimesi tähän",
    "vision.verb.key_frei_ph": "vain jos palvelimesi vaatii sellaisen",
    "vision.verb.host": "Host",
    "vision.verb.host_ph": "koneen nimi tai osoite",
    "vision.verb.port": "Portti",
    "vision.verb.host_satz":
        "Vain kone &mdash; osoitteen loput suslik täydentää itse. "
        "Esimerkkiportti on se, jota llama.cpp käyttää oletuksena; ota "
        "se, jota omasi kuuntelee.",
    "vision.verb.endpunkt": "Päätepisteen URL",
    "vision.verb.endpunkt_satz":
        "Tämä on esimerkki OpenAI-yhteensopivasta päätepisteestä &mdash; "
        "korvaa se omallasi, jos käytät toista palveluntarjoajaa.",
    "vision.verb.betriebsart": "Tämä päätepiste on",
    "vision.verb.betriebsart_extern": "internetissä",
    "vision.verb.betriebsart_lokal": "omassa verkossani",
    "vision.verb.adresse": "API-osoite",
    "vision.verb.adresse_satz":
        "Kiinteästi sisäänrakennettu &mdash; tässä ei voi kirjoittaa "
        "väärin.",
    "vision.verb.key": "API-avain",
    "vision.verb.key_frei_satz":
        "Tässä valinnainen &mdash; useimmat paikalliset palvelimet eivät "
        "vaadi avainta. Paina painiketta silti: se hakee myös listan "
        "malleista, joita palvelimellasi on.",
    "vision.verb.titel": "Yhteys",
    "vision.modell.titel": "Malli",
    "vision.modell.verweigert": "päätepiste kieltäytyi yhteydestä",
    "vision.modell.geprueft": "Tarkistettu {zeit} vasten",
    "vision.modell.opt_wahl": "&mdash; valitse &mdash;",
    "vision.modell.ungetestet": "täällä testaamaton",
    "vision.modell.opt_verschollen":
        " — tallennettu aiemmin, päätepiste ei listaa sitä juuri nyt",
    "vision.modell.wahl_satz":
        "Valitse yksi listasta &mdash; nimen vieressä oleva huomautus on "
        "meiltä, nimet ovat päätepisteen omia.",
    "vision.modell.verschollen_satz":
        "Tämä malli on tallennettu ja edelleen käytössä, mutta päätepiste "
        "ei listannut sitä tällä kertaa. Tarkista nimi tai valitse yksi "
        "listasta.",
    "vision.modell.fremde_plattform": "mitattu toisella alustalla",
    "vision.modell.kein_rohergebnis": "tähän ei ole arkistoitu raakatulosta",
    "vision.modell.gemessen": "mitattu {datum} &middot; {quelle}",
    "vision.modell.ungemessen_satz":
        "Täällä ei mitattu &mdash; se ei ole tuomio, vain rehellisyyttä. "
        "Aja alla oleva yhteystesti, ennen kuin luotat siihen.",
    "vision.modell.manuell": "Mallin ID käsin",
    "vision.modell.manuell_ph": "tarkka mallin ID",
    "vision.modell.manuell_knopf": "Tarkista tämä ID",
    "vision.modell.manuell_satz":
        "Päätepisteille, jotka eivät listaa kaikkea: ID tarkistetaan "
        "ensin pienellä tekstipyynnöllä; tarkistamatonta ei voi "
        "tallentaa.",
    "vision.prompt.standard_satz":
        "Tämä on mitattu oletussanamuoto. Niin kauan kuin jätät sen juuri "
        "tällaiseksi, päätelmiä ei merkitä muokatuiksi.",
    "vision.prompt.titel": "Kysymys, jonka suslik esittää",
    "vision.prompt.satz":
        "Voit muuttaa sanamuotoa. Viimeinen kappale on kiinteä: se on "
        "yhden sanan ohje, josta vastauksen jäsennin riippuu, ja se on "
        "se, mikä mitattiin.",
    "vision.prompt.knopf_zurueck": "Palauta oletus",
    "vision.zahlen.think": "Kytke mallin ajattelu pois",
    "vision.zahlen.think_satz":
        "Versiosta 0.1.0.211 lähtien oletuksena päällä: vaikeissa "
        "vertailuruudukoissa ajatteleva malli voi puhua itsensä "
        "tokenibudjetin yli, ja ajo päättyy ilman päätelmää. Tiukat "
        "päätepisteet hylkäävät kytkimen; suslik toistaa pyynnön silloin "
        "kertaalleen ilman sitä ja sanoo sen.",
    "vision.zahlen.titel": "Rajat",
    "vision.zahlen.max_tokens": "Enimmäistokenit vastausta kohti",
    "vision.zahlen.timeout": "Aikakatkaisu pyyntöä kohti (s)",
    "vision.zahlen.satz":
        "Mitattu: yhdessä ajossa 3000 tokenia oli liian vähän &mdash; "
        "vastaus katkesi ja laskettiin päätelmän puuttumiseksi, ja sama "
        "kysymys oli oikein 12000:lla. Paikallinen malli CPU-koneella "
        "tarvitsee minuutteja pyyntöä kohti, verkossa oleva sekunteja.",
    "vision.cloud.ziel_fallback": "päätepiste, jonka asetat yllä",
    "vision.cloud.titel": "Kuvien lähettäminen ulkopuoliseen palveluun",
    "vision.cloud.satz":
        "Näissä kuvissa ei ole vain täällä asuvia ihmisiä: epävarmat "
        "tapaukset ovat useimmiten vieraita &mdash; vierailijoita, "
        "kuriireja, naapureita, ohikulkijoita. Vastuu siitä on sinulla, "
        "ei palvelun ylläpitäjällä. Vahvistuksesi kirjataan aikaleimalla "
        "audit-lokiin; vaihto takaisin paikalliseen malliin peruu sen.",
    "vision.cloud.bestaetigung": "Ymmärrän ja vahvistan tämän",
    "vision.cloud.bestaetigt": "(vahvistettu {zeit})",
    "vision.test.treffer": "{n}/2 oikein",
    "vision.test.tokens": "{ist} tokenia vs {soll}",
    "vision.test.falsch": " (väärin)",
    "vision.save.knopf": "Tallenna yhteys",
    "vision.save.dirty":
        "tallentamattomia muutoksia &mdash; tunnistus käyttää edelleen "
        "tallennettua yhteyttä",
    "vision.test.titel": "Testaa tämä yhteys",
    "vision.test.knopf": "Aja testi",
    "vision.test.nicht_gelaufen": "ei ajettu",
    "vision.test.stufe1": "tavoitettavuus",
    "vision.test.stufe2": "pakkovalinta",
    "vision.test.stufe3": "tokenien tarkistus",
    "vision.test.ungetestet": "Ei vielä testattu.",
    "vision.test.letzter": "Viimeisin ajo {zeit} vasten",
    "vision.galerien.stand_gut": "hyväksytty {zeit} &middot; {zellen} solua",
    "vision.galerien.pruefen": "vaatii vilkaisun",
    "vision.galerien.keine": "ei vielä galleriaa",
    "vision.galerien.zu_wenig":
        "hyväksyttyjä kehokuvia ei ole vielä tarpeeksi ({n} "
        "käyttökelpoista)",
    "vision.galerien.knopf_auffrischen": "Virkistä",
    "vision.galerien.knopf_bauen": "Rakenna galleria",
    "vision.galerien.zahl": "{n} käyttökelpoista kuvaa &middot; {reihen}",
    "vision.galerien.titel": "Galleriat",
    "vision.galerien.stand":
        "{n} galleriaa valmiina ({min} vaaditaan) &mdash; Vision "
        "tarvitsee vähintään kaksi, koska se vertaa aina yhtä henkilöä "
        "toiseen.",
    "vision.galerien.satz":
        "Gallerian voivat saada vain henkilöt, joilla on opittu "
        "kehomalli; kuvat tulevat kehomateriaalista, jonka olet jo "
        "hyväksynyt. Vision arvioi aina vain henkilöitä, joilla on "
        "galleria, ja se kertoo sen päätelmän yhteydessä.",
    "visiontest.titel": "Tunnistustesti",
    "visiontest.kopf.satz":
        "Kasvot ja henkilö luetaan siitä, mikä tallennettiin silloin "
        "&mdash; mitään ei lasketa uudelleen. Vision ajetaan nyt, "
        "täsmälleen samaa tietä kuin normaalikäytössä.",
    "visiontest.kosten":
        "Testiajo kuluttaa oikeita pyyntöjä, täsmälleen kuin "
        "normaalikäyttö: koko käynti menee sisään yhtenä "
        "ehdokasruudukkona, ja jokainen verrattu galleriapari kustantaa "
        "kaksi pyyntöä, koska jokainen kysymys kysytään uudelleen "
        "galleriat vaihdettuina. Se lasketaan käsin tehdyksi "
        "napsautukseksi, joten se ei syö päivärajaasi &mdash; mutta "
        "maksullisella päätepisteellä se on rahaa, ja paikallisella "
        "CPU-mallilla se kestää minuutteja.",
    "visiontest.wer.niemand": "ketään ei tunnistettu",
    "visiontest.wahl.kachel_zahlen":
        "{events} tapahtumaa &middot; {kameras} kameraa",
    "visiontest.wahl.vision_fertig": " &middot; Vision ajettu",
    "visiontest.wahl.titel": "1 &middot; Mikä käynti",
    "visiontest.wahl.leer":
        "Käyntejä ei ole vielä kirjattu. Heti kun joku kulkee tontin yli, "
        "ne ilmestyvät tähän.",
    "visiontest.wahl.kopf_zahlen":
        "{events} tapahtumaa &middot; {kameras} kameraa",
    "visiontest.wahl.anderer": "valitse toinen käynti",
    "visiontest.wahl.titel_offen": "1 &middot; Valitse käynti",
    "visiontest.wahl.anzahl": "{n} tuoreinta käyntiä",
    "visiontest.wahl.satz":
        "Tuoreimmat käynnit, ryhmitelty täsmälleen kuten Tänään-sivulla.",
    "visiontest.gesicht.kein_match": "ei osumaa",
    "visiontest.gesicht.gezeigt": "näytetään {gezeigt}/{gesamt} kuvaa",
    "visiontest.gesicht.ohne_bild":
        "{fehlt} niistä {unbek} tapahtumasta, joilla ei ollut osumaa, ei "
        "säilyttänyt kuvaa",
    "visiontest.gesicht.kein_bild":
        "tälle käynnille ei ole tallennettu kasvokuvaa",
    "visiontest.gesicht.keines": "ei tunnettuja kasvoja",
    "visiontest.gesicht.zeile": "{person} &middot; {events} tapahtumaa",
    "visiontest.gesicht.best": " &middot; paras {best}",
    "visiontest.gesicht.unbekannt":
        "{n} tapahtumaa, joissa kasvot ilman osumaa",
    "visiontest.gesicht.titel": "Kasvot",
    "visiontest.gesicht.quelle":
        "embedding-vertailu viitekasvojasi vasten &mdash; tämän käynnin "
        "kirjanpidosta",
    "visiontest.koerper.kandidaten":
        "ehdokkaita, kukaan ei ylitä sääntöä: {liste}",
    "visiontest.koerper.nichts": "ei mitään arvioitu",
    "visiontest.koerper.zeile":
        "{klasse} &middot; score {score} / {schwelle} &middot; {quelle}",
    "visiontest.koerper.bild_weg": "kuva vanhentunut",
    "visiontest.koerper.titel": "Henkilö",
    "visiontest.koerper.quelle":
        "DINOv2-embedding + luokitin tämän käynnin arvioiduille kuville",
    "visiontest.log.warte":
        "odotetaan mallia &mdash; tämä sivu päivittyy itsestään",
    "visiontest.log.titel": "Mitä tapahtui",
    "visiontest.gitter.alt": "tämän ajon ehdokasruudukko",
    "visiontest.gitter.bildunterschrift":
        "kuva, joka mallille todella näytettiin",
    "visiontest.gitter.zeile":
        "ehdokasruudukko: {n} solua tästä käynnistä, kysytty YHTENÄ "
        "kuvana",
    "visiontest.gitter.luecken": " ({n} solua jätetty tyhjäksi)",
    "visiontest.runden.kein_votum": "ei ääntä &mdash; {grund}",
    "visiontest.runden.paar": "{a} vs {b}",
    "visiontest.nach.laeuft": "Tämä käynti analysoidaan uudelleen",
    "visiontest.nach.stand":
        "{fertig}/{gesamt} tapahtumaa valmiina &mdash; arvioidut kuvat "
        "kerätään samalla mukaan, tämä kestää muutaman minuutin. Se on "
        "hiljaista: ei ilmoituksia, ei mitään ulos. Tämä sivu päivittyy "
        "itsestään.",
    "visiontest.nach.titel": "Tälle käynnille ei ole tallennettu mitään",
    "visiontest.nach.satz":
        "Uusi analyysi tuo arvioidut kuvat takaisin &mdash; ja se täyttää "
        "kaikki kolme tietä, ei vain Visionia. Se ajaa tavallisen "
        "analyysin tämän käynnin tapahtumille kertaalleen uudelleen: "
        "hiljaa, ilman ilmoituksia, ja se odottaa live-tunnistusta sen "
        "sijaan, että työntäisi sen syrjään.",
    "visiontest.nach.knopf": "Analysoi tämä käynti uudelleen",
    "visiontest.felder.zellen": "ruudukon solut tälle ajolle",
    "visiontest.felder.voten": "tälle ajolle vaaditut vahvistukset",
    "visiontest.felder.doppel": "kysy jokaista paria kahdesti (vaihtokoe)",
    "visiontest.felder.satz":
        "Kaikki kolme pätevät vain TÄHÄN ajoon &mdash; mitään ei "
        "tallenneta ja normaalikäyttö säilyttää omat asetuksensa. Tässä "
        "käynnissä on {material} käyttökelpoista kuvaa &mdash; useampaa "
        "solua voi pyytää huoletta, ruudukko vain pienenee. {galerien} "
        "hyväksyttyä galleriaa sallii enintään {voten_max} vertailua. Kun "
        "vaihtokoe on päällä, vertailu kustantaa kaksi pyyntöä; ilman "
        "sitä yhden &mdash; ja se nojaa silloin yhteen ainoaan "
        "vastaukseen.",
    "visiontest.laeufe.abgebrochen":
        "keskeytyi (palvelu käynnistyi uudelleen)",
    "visiontest.laeufe.kein_urteil": "ei päätelmää",
    "visiontest.laeufe.von": "/ {n}",
    "visiontest.laeufe.ohne_tausch": "ei vaihtoa",
    "visiontest.laeufe.auto": "auto",
    "visiontest.laeufe.offen": "+{n} avointa",
    "visiontest.laeufe.titel": "Tämän käynnin ajot",
    "visiontest.laeufe.kopf_wann": "milloin",
    "visiontest.laeufe.kopf_zellen": "solut",
    "visiontest.laeufe.kopf_noetig": "vaaditaan",
    "visiontest.laeufe.kopf_backend": "backend",
    "visiontest.laeufe.kopf_urteil": "päätelmä",
    "visiontest.laeufe.kopf_voten": "äänet",
    "visiontest.laeufe.kopf_anfragen": "pyyn.",
    "visiontest.laeufe.kopf_zeit": "aika",
    "visiontest.laeufe.satz":
        "Uusimmat ensin. Vain se, mikä todella ajettiin &mdash; lista "
        "tulee tämän käynnin omasta lokista ja katoaa sen mukana.",
    "visiontest.vision.titel": "Vision",
    "visiontest.vision.quelle_kurz":
        "Vision-malli, joka vertaa tätä käyntiä gallerioihisi",
    "visiontest.vision.unkonfiguriert": "ei asetettu",
    "visiontest.vision.attr_nichts": "vertailtavaa ei vielä ole",
    "visiontest.vision.knopf": "Aja Vision tälle käynnille",
    "visiontest.vision.nichts_satz":
        "vertailtavaa ei vielä ole &mdash; analysoi tämä käynti ensin "
        "uudelleen (painike ylhäällä)",
    "visiontest.vision.laeuft_satz":
        "ajo on juuri nyt käynnissä &mdash; alla oleva loki kasvaa sen "
        "mukana",
    "visiontest.vision.startet":
        "käynnistyy &mdash; mitään ei ole vielä ilmoitettu",
    "visiontest.vision.quelle":
        "pakkovalinta gallerioitasi vasten: koko käynti menee sisään "
        "YHTENÄ ehdokasruudukkona, ja jokainen pari kysytään kahdesti "
        "galleriat vaihdettuina",
    "visiontest.vision.nicht_gelaufen": "ei ajettu tälle käynnille",
    "visiontest.vision.verglichen":
        "verrattu: {a} vastaan {b} &mdash; kaikista muista se ei sano "
        "mitään",
    "visiontest.vision.abgebrochen":
        "ajo keskeytyi &mdash; palvelu käynnistyi uudelleen",
    "visiontest.vision.kein_urteil": "ei päätelmää &mdash; {grund}",
    "visiontest.vision.bilanz":
        "{voten}/{bilder} vertailua antoi vastauksen &middot; {anfragen} "
        "pyyntöä &middot; {dauer} s &middot; ajo {zeit}",
    "visiontest.vision.reihenfolge": " &middot; järjestys: {quelle}",
    "visiontest.vision.custom_prompt": " &middot; muokattu sanamuoto",
    "visiontest.drei.titel": "2 &middot; Mitä kolme tietä sanovat",
    "visiontest.drei.satz":
        "Sama käynti, kolme riippumatonta päätelmää. Ne saavat olla eri "
        "mieltä &mdash; juuri siitä on kysymys, kun niitä katsotaan "
        "yhdessä.",
    "visionwizard.schritt.person": "valitse henkilö",
    "visionwizard.schritt.groesse": "valitse koko",
    "visionwizard.schritt.vorschlag": "tarkista ehdotus",
    "visionwizard.schritt.abnahme": "hyväksy",
    "visionwizard.titel": "Rakenna galleria",
    "visionwizard.kopf.satz":
        "Galleria on pieni ruudukko yhden henkilön kuvia &mdash; juuri "
        "siihen Vision-malli vertaa uutta kuvaa. Se rakennetaan "
        "kehokuvista, jotka olet jo hyväksynyt; mitään uutta ei "
        "tallenneta eikä yhtään videota avata.",
    "visionwizard.person.stand_gut": "galleria hyväksytty {zeit}",
    "visionwizard.person.zu_wenig":
        "{n} käyttökelpoista kuvaa &mdash; ei vielä tarpeeksi galleriaan. "
        "Aja henkilöiden oppimisajo useammalle käynnille.",
    "visionwizard.person.max_gitter":
        "suurin ruudukko, jonka tämä materiaali kantaa: {n}",
    "visionwizard.person.titel": "1 &middot; Mikä henkilö",
    "visionwizard.person.satz":
        "Tässä näkyvät vain henkilöt, joilla on opittu kehomalli, ja "
        "luvut ovat kuvia, jotka läpäisevät kokosuodattimen (vähintään "
        "350 pikseliä korkeita) &mdash; ei kaikkea, mitä on koskaan "
        "kerätty.",
    "visionwizard.groesse.zellen": "{n} solua",
    "visionwizard.groesse.titel": "2 &middot; Kuinka monta kuvaa",
    "visionwizard.zelle.leer":
        "tälle riville ei ole enempää kuvia &mdash; eikä lainattavaakaan "
        "ole jäljellä",
    "visionwizard.zelle.geliehen": "riviltä {reihe}",
    "visionwizard.zelle.knopf_weg": "ei sovi",
    "visionwizard.reihe.geliehen":
        "{n} täytetty toisesta näkymästä &mdash; siistejä kuvia näkymästä "
        "{reihe} ei ollut tarpeeksi",
    "visionwizard.reihe.luecken": "{n} solua ei voitu täyttää lainkaan",
    "visionwizard.reihe.spreizung": "{tage} päivää, {kameras} kameraa",
    "visionwizard.reihe.kopf": "näkymä {reihe}",
    "visionwizard.reihe.eigene": "{eigene}/{gesamt} tästä näkymästä",
    "visionwizard.vorschlag.abgelehnt":
        "{n} aiemmin hylkäämääsi kuvaa pysyy muistissa eikä tule "
        "takaisin.",
    "visionwizard.vorschlag.titel": "3 &middot; Sopiiko tämä?",
    "visionwizard.vorschlag.grenze":
        "Rehellinen raja: nämä ovat mittauksia kuvasta, eivät hetkestä. "
        "Kuva, jossa joku sitoo hiuksiaan tai kumartuu, näyttää jokaisen "
        "mittauksen silmissä hyvältä &mdash; sitä varten sinulla on "
        "silmät.",
    "visionwizard.vorschlag.knopf": "Hyväksy tämä galleria",
    "visionwizard.vorschlag.kopie_satz":
        "Hyväksyminen kopioi nämä kuvat gallerian kansioon. Siitä lähtien "
        "galleria on kiinteä: myöhemmin poistettu alkuperäinen ei voi "
        "repiä siihen reikiä &mdash; suslik vain pyytää sinua hyväksymään "
        "sen uudelleen.",
    "visionwizard.fertig.geliehen": " &middot; lainattu",
    "visionwizard.fertig.titel": "Hyväksytty galleria",
    "visionwizard.fertig.stand": "{zellen} solua, hyväksytty {zeit}.",
    "visionwizard.fertig.satz":
        "Nämä ovat kopioita gallerian kansiossa, ja jokaisen kuvan "
        "alkuperä (ajo, tiedosto, tarkistussumma) on kirjattu niiden "
        "viereen. Ne siirtyvät varmuuskopiosi mukana.",
    "visionwizard.fertig.knopf_neu":
        "Rakenna uudelleen nykyisestä materiaalista",
    "visionwizard.fertig.knopf_zurueck": "Takaisin Vision-tunnistukseen",
    "visionwizard.neu.titel": "Uutta materiaalia saatavilla",
    "visionwizard.neu.satz":
        "Mikään ei muutu itsestään &mdash; hyväksymäsi galleria pysyy "
        "juuri sellaisena, kunnes rakennat ja hyväksyt uuden.",
    "personwizard.wer.alle": "kaikki tunnetut henkilöt",
    "personwizard.wer.fremde": "vieraat",
    "personwizard.titel": "Opeta henkilöitä — kehontunnistus",
    "personwizard.kopf.satz":
        "Toinen, riippumaton tunnistustie: se oppii, miltä henkilö "
        "näyttää KOKONAISUUTENA (ruumiinrakenne, hiukset, asento), ja "
        "tunnistaa asukkaat myös silloin, kun kasvot eivät näy.",
    "personwizard.kopf.wie_titel":
        "Näin se toimii — sinulla on viimeinen sana",
    "personwizard.kopf.schritt1":
        "1 · Sinä valitset, kuinka monta tapahtumaa käydään läpi ja KUKA "
        "opetetaan (yksi henkilö tai kaikki tunnetut henkilöt).",
    "personwizard.kopf.schritt2":
        "2 · Ajo kerää kokovartalokuvia omista tallenteistasi. Kuva "
        "sidotaan henkilöön vain silloin, kun kasvoilla vahvistettu "
        "käynti sen todistaa — tarkoituksella varovaista.",
    "personwizard.kopf.schritt3":
        "3 · SINÄ käyt läpi jokaisen kerätyn kuvan; yksi napsautus hylkää "
        "väärän. Ilman hyväksyntääsi ei opita mitään.",
    "personwizard.kopf.schritt4":
        "4 · Koulutus ajetaan sen jälkeen paikallisesti sekunneissa, ja "
        "päätöskynnys mitataan niin, että vieraat jäävät sen alle.",
    "personwizard.kopf.tempo":
        "Huomautus nopeudesta: keräys ajetaan tällä hetkellä CPU:lla, "
        "joten malta hetki ajon kanssa (karkeasti 15&ndash;30 s "
        "tapahtumaa kohti). Siirto GPU:lle/NPU:lle on suunniteltu "
        "myöhempään versioon.",
    "personwizard.kopf.warum":
        "Miksi ensin vähintään yksi henkilö: tämä tie voi erottaa ihmiset "
        "toisistaan vasta, kun se on oppinut — ja sinä olet käynyt läpi "
        "—, miltä vähintään yksi asukas näyttää. Siihen asti "
        "kehontunnistus pysyy POIS eikä lähetä koskaan ilmoitusta. Kun se "
        "myöhemmin ilmoittaa (Pushover/Telegram), sanoma on merkitty "
        "henkilöntunnistukseksi, ei kasvontunnistukseksi.",
    "personwizard.vorb.titel": "Ajoa valmistellaan &hellip;",
    "personwizard.vorb.zeile":
        "sidotaan viimeiset {n} tapahtumaa henkilöön {wer} vahvistettujen "
        "käyntien kautta",
    "personwizard.vorb.satz":
        "Tämä kestää minuutin tai kaksi — sivu päivittyy itsestään, "
        "keräys alkaa heti sen jälkeen.",
    "personwizard.ernte.stand":
        "{events}/{von} tapahtumaa · {bilder} kuvaa kerätty",
    "personwizard.ernte.startet": "käynnistyy …",
    "personwizard.ernte.titel": "Henkilöiden oppimisajo on käynnissä",
    "personwizard.ernte.zeile": "opetetaan {wer} · {stand}",
    "personwizard.ernte.satz":
        "Tämä sivu päivittyy itsestään. Uusi ajo voi käynnistyä heti, kun "
        "tämä on valmis.",
    "personwizard.ernte.knopf_abbruch": "Keskeytä ajo",
    "personwizard.ernte.abbruch_hinweis": "kerätyt kuvat säilyvät",
    "personwizard.unterbrochen.titel": "Viimeisin ajo keskeytyi",
    "personwizard.unterbrochen.satz":
        "Todennäköisesti palvelun uudelleenkäynnistys. Käynnistä sama ajo "
        "alta uudelleen — jo kerätyt tapahtumat ohitetaan automaattisesti "
        "(jatkaminen), mitään ei menetetä.",
    "personwizard.abnahme.titel":
        "Viimeisin ajo on valmis — seuraavaksi sinun läpikäyntisi",
    "personwizard.abnahme.zeile":
        "{n} kuvaa kerätty henkilölle {wer} (ajo {lauf}).",
    "personwizard.abnahme.knopf": "Käy kuvat nyt läpi",
    "personwizard.abnahme.hinweis":
        "saata läpikäynti loppuun, niin seuraava ajo avautuu",
    "personwizard.abnahme.knopf_verwerfen": "Hylkää tämä ajo",
    "personwizard.abnahme.verwerfen_hinweis": "huono tulos? heitä kaikki pois",
    "personwizard.leer.verwaist":
        "Ohitettu tarkoituksella: {liste} — nämä nimet on poistettu "
        "henkilöistäsi; niiden vanhat vahvistetut tapahtumat säilyvät "
        "historiana, mutta niitä ei kerätä.",
    "personwizard.leer.titel": "Ajo päättyi ilman kuvia — tässä on syy",
    "personwizard.leer.satz":
        "Mitään ei muutettu; voit käynnistää alta uuden ajon milloin "
        "tahansa.",
    "personwizard.fertig.verwaist":
        "Ohitettu tarkoituksella: {liste} — poistettuja henkilöitä; "
        "niiden vanhoja vahvistettuja tapahtumia ei kerätä.",
    "personwizard.fertig.fremd":
        "{n} vahvistettua vieraan kuvaa siirtyi vieraiden pooliin — "
        "seuraava koulutus käyttää niitä heti.",
    "personwizard.fertig.titel":
        "Läpikäynti valmis — materiaali otettu käyttöön",
    "personwizard.fertig.zeile":
        "{abgenommen} kuvaa hyväksytty oppimateriaaliksi, {verworfen} "
        "hylätty (ajo {lauf}).",
    "personwizard.fertig.knopf": "Katso opittu materiaali",
    "personwizard.fehler.titel": "Viimeisin ajo epäonnistui",
    "personwizard.auswahl.opt_alle": "Kaikki tunnetut henkilöt",
    "personwizard.auswahl.opt_fremde": "Vieraat — kerää vieraiden kuvia",
    "personwizard.auswahl.titel": "Kuka opetetaan",
    "personwizard.auswahl.satz":
        "Valitse yksi henkilö, niin käyt läpi pieniä, kohdennettuja eriä "
        "— tai kaikki kerralla. Henkilöt tulevat kasvokokoelmastasi; "
        "yhden kerrallaan opettaminen pitää läpikäynnin lyhyenä.",
    "personwizard.auswahl.fremde_satz":
        "Vieraat: kerää käyntejä, joissa ketään ei tunnistettu (pelkät "
        "katukäynnit, vahvistamattomat vierailijat). Läpikäynnissä "
        "vahvistat, ketkä todella ovat vieraita — he siirtyvät vieraiden "
        "pooliin ja terävöittävät päätöskynnystä.",
    "personwizard.umfang.knopf_letzte": "viimeiset {n}",
    "personwizard.umfang.attr_eigen": "oma N",
    "personwizard.umfang.knopf_go": "aja",
    "personwizard.umfang.titel": "Laajuus (tapahtumat, ei päivät)",
    "personwizard.umfang.satz":
        "Aloita pienestä (50) — käyt jokaisen kerätyn kuvan läpi käsin.",
    "personwizard.bilanz.ohne":
        "viimeiset {n} henkilötapahtumaa henkilölle {wer} — "
        "sidontayhteenveto lasketaan, kun ajo luodaan",
    "personwizard.bilanz.zahl_vor": "viimeiset {n} henkilötapahtumaa · ",
    "personwizard.bilanz.zahl_nach":
        " voidaan sitoa henkilöön {wer} vahvistettujen käyntien kautta",
    "personwizard.bilanz.fremd": " · {n} vierasehdokasta",
    "personwizard.bilanz.erkl_fremd":
        "Ehdokkaat ovat käyntejä, joissa ketään ei tunnistettu — pelkkiä "
        "katukäyntejä ja vahvistamattomia vierailijoita. Läpikäyntiisi "
        "asti kaikki on EPÄILY; merkitse siellä jokainen, joka EI ole "
        "vieras.",
    "personwizard.bilanz.erkl":
        "Sidonta on varovaista: vain käynnit, joissa on täsmälleen yksi "
        "kasvoilla vahvistettu henkilö, lasketaan. Kaiken, minkä näet sen "
        "jälkeen, voi hylätä yhdellä napsautuksella.",
    "personwizard.bilanz.titel": "Sinun valintasi",
    "personwizard.bilanz.knopf": "Luo tämä ajo",
    "personwizard.review.stempel": "VÄÄRIN",
    "personwizard.review.h_fremde": "Vieraat",
    "personwizard.review.frage_fremd":
        "napsauta jokaista kuvaa, jossa EI ole vierasta (asukas, tunnettu "
        "vierailija) tai joka on käyttökelvoton. Toinen napsautus peruu "
        "sen. Kaikki tallennetaan heti; merkitsemättömät kuvat otetaan "
        "käyttöön vahvistettuina vieraina ja ne terävöittävät "
        "päätöskynnystä.",
    "personwizard.review.frage":
        "napsauta jokaista kuvaa, joka on VÄÄRIN (ei tämä henkilö tai "
        "käyttökelvoton). Toinen napsautus peruu sen. Kaikki tallennetaan "
        "heti; merkitsemättömät kuvat lasketaan hyväksytyiksi.",
    "personwizard.review.titel": "Käy kerätty läpi",
    "personwizard.review.kopf": "Ajo {lauf} — {frage}",
    "personwizard.review.zurueck": "&larr; takaisin ohjattuun\ntoimintoon",
    "personwizard.review.knopf_fertig":
        "Päätä läpikäynti — ota hyväksytyt kuvat käyttöön",
    "personwizard.kontrolle.sammeln_titel": "Keräystila on PÄÄLLÄ",
    "personwizard.kontrolle.sammeln_rest":
        " — jokainen arvioitu kuva säilytetään 30 päivää, jotta voit "
        "tarkistaa päätökset myöhemmin. Varaudu karkeasti 20&ndash;40 MB "
        "päivässä.",
    "personwizard.kontrolle.schlank_titel": "Kevyt tila (oletus)",
    "personwizard.kontrolle.schlank_rest":
        " — arvioidut kuvat elävät vain niin kauan kuin käynti on kesken; "
        "sen jälkeen jäävät vain voittanut kuva ja alla oleva "
        "päätelmäloki. Tämä on tuoreen asennuksen tietosuojaystävällinen "
        "oletus.",
    "personwizard.kontrolle.titel": "Arvioidut kuvat",
    "personwizard.kontrolle.satz":
        "Mitä kehontunnistus todella katsoi, yksi lohko käyntiä kohti: "
        "arvioitu kuva, luokka johon se päätyi, score ja mistä kuva tuli. "
        "Hyödyllinen, kun henkilö jäi huomaamatta tai joku tunnistettiin, "
        "jota ei olisi pitänyt tunnistaa.",
    "personwizard.kontrolle.leer_titel": "Mitään ei ole vielä kirjattu",
    "personwizard.kontrolle.tag_fremd": "vieras",
    "personwizard.kontrolle.tag_drueber": "kynnyksen yllä",
    "personwizard.kontrolle.tag_drunter": "kynnyksen alla",
    "personwizard.kontrolle.schwelle": " &middot; kynnys {schwelle}",
    "personwizard.kontrolle.kopfzeile.eins":
        "{wann} — {judged} arvioitu, {n} kuva säilytetty",
    "personwizard.kontrolle.kopfzeile.viele":
        "{wann} — {judged} arvioitu, {n} kuvaa säilytetty",
    "personwizard.tabelle.fremd_zeile": "Vieraat (lisäluokka)",
    "personwizard.tabelle.kein_fremd":
        "Ei vielä vieraiden luokkaa — sellaisen kanssa tunnistus toimii "
        "selvästi paremmin: vahvistetut vieraiden kuvat opettavat "
        "mallille, mikä EI kuulu joukkoon, ja kalibroivat "
        "päätöskynnyksen.",
    "personwizard.tabelle.q_eichung": "mitattu",
    "personwizard.tabelle.q_user": "itse asettamasi",
    "personwizard.tabelle.q_standard": "sisäänrakennettu oletus",
    "personwizard.tabelle.f_modell": "Aktiivinen malli",
    "personwizard.tabelle.f_schwelle": "Kynnys",
    "personwizard.tabelle.f_scharf": "Aktivoitu",
    "personwizard.tabelle.scharf_ja": "KYLLÄ",
    "personwizard.tabelle.scharf_ja_rest": " — arvioi livenä",
    "personwizard.tabelle.scharf_nein": "ei — ei aktivoitu",
    "personwizard.tabelle.konf_vor":
        "Suurin ryhmien välinen sekaannus kalibroinnissa: ",
    "personwizard.tabelle.konf_nach":
        " — vahvin score, jonka jokin kuva saavutti VÄÄRÄLLE ryhmälle; "
        "mitä lähempänä ykköstä, sitä lähempänä kaksi ryhmää ovat "
        "toisiaan.",
    "personwizard.tabelle.titel": "Opitut ryhmät",
    "personwizard.karte.scharf": "Aktivoitu",
    "personwizard.karte.unscharf": "Ei vielä aktivoitu",
    "personwizard.karte.fehler":
        "Viimeisin koulutusyritys EPÄONNISTUI: {fehler} — tämä kortti "
        "näyttää edellisen mallin.",
    "personwizard.karte.titel": "Mallin tila",
    "personwizard.karte.zeile":
        "koulutettu {wann} ajassa {dauer} s — {bilder} kuvaa: {je} · "
        "{modell} · ",
    "personwizard.karte.link": "tiedot",
    "personwizard.bestand.titel": "Henkilömateriaali — mitä on opittu",
    "personwizard.bestand.satz":
        "Hyväksytyt kokovartalokuvat henkilöä kohti. Valitse alta ryhmä, "
        "niin näet sen kuvat; poista yksittäinen kuva (&times; ruudussa) "
        "— uusi ajo voi aina kerätä uudelleen. Poistot vaikuttavat "
        "seuraavassa koulutuksessa.",
    "personwizard.bestand.leer_titel": "Ei vielä hyväksyttyä materiaalia",
    "personwizard.bestand.stark_titel": "Mikä tekee tästä mallista vahvan",
    "personwizard.bestand.chip_fremde": "Vieraat ({n})",
    "personwizard.bestand.zeigen_titel": "Näytä kuvat kohteesta",
    "personwizard.bestand.zeigen_satz":
        "Valitse ryhmä — sen kuvat avautuvat alle, uusimmat ensin.",
    "personwizard.bestand.marker_tage.eins":
        "vain {n} päivä — tunnistus paranee eniten, kun materiaali kattaa "
        "useampia päiviä, vaatteita ja valo-oloja",
    "personwizard.bestand.marker_tage.viele":
        "vain {n} päivää — tunnistus paranee eniten, kun materiaali "
        "kattaa useampia päiviä, vaatteita ja valo-oloja",
    "personwizard.bestand.attr_loeschen": "poista tämä kuva",
    "personwizard.bestand.z_bilder": "{n} kuvaa",
    "personwizard.bestand.z_tage.eins": "{n} päivä",
    "personwizard.bestand.z_tage.viele": "{n} päivää",
    "personwizard.bestand.z_kameras.eins": "{n} kamera",
    "personwizard.bestand.z_kameras.viele": "{n} kameraa",
    "personwizard.modell.titel": "Henkilömalli — tila",
    "personwizard.modell.satz":
        "Kehontunnistuksen malli, koulutettu hyväksymistäsi kuvista. Se "
        "koulutetaan automaattisesti uudelleen jokaisen päätetyn "
        "läpikäynnin ja jokaisen poiston jälkeen.",
    "personwizard.modell.leer_titel": "Ei vielä mallia",
    "personwizard.modell.fremd_keine":
        "ei vielä yhtään — kynnys on mitattu vain henkilöidesi väliltä",
    "personwizard.modell.fremd_gesammelt":
        "{n} kerätty — {min} tarvitaan, ennen kuin ne otetaan "
        "koulutukseen ja kalibroivat kynnyksen",
    "personwizard.modell.fremd_geeicht":
        "{n} koulutuksessa · kynnys kalibroitu oikeilla vierailla",
    "personwizard.modell.fremd_ungeeicht":
        "{n} koulutuksessa — kynnyksen kalibrointi ei ajettu (katso alla "
        "oleva huomautus)",
    "personwizard.modell.f_trainiert": "Koulutettu",
    "personwizard.modell.f_dauer": "Koulutuksen kesto",
    "personwizard.modell.f_modell": "Malli",
    "personwizard.modell.f_bilder": "Kuvia yhteensä",
    "personwizard.modell.f_personen": "Henkilöt",
    "personwizard.modell.f_fremd": "Vieraiden negatiivit",
    "personwizard.modell.scharf_ja": "KYLLÄ — live-arviointi aktiivinen",
    "personwizard.modell.scharf_nein": "ei — ei vielä aktivoitu",
    "personwizard.modell.fehler":
        "Viimeisin koulutusyritys EPÄONNISTUI ({zeit}): {fehler} — tässä "
        "näkyvä malli on edellinen eikä sisällä viimeisimpiä muutoksiasi.",
    "personwizard.modell.aktuell_titel": "Nykyinen malli",
    "personwizard.modell.material_titel": "Oppimateriaali henkilöä kohti",
    "personwizard.modell.kopf_person": "henkilö",
    "personwizard.modell.kopf_bilder": "hyväksytyt kuvat",
    "personwizard.modell.kopf_anteil": "osuus",
    "personwizard.modell.summe": "yhteensä",
    "personwizard.modell.q_eichung": "mitattu materiaalistasi",
    "personwizard.modell.eich_fremd":
        "Mitattu {folds}-kertaisella ristiinvalidoinnilla {n} sivuun "
        "jätetystä henkilöidesi kuvasta ja {n_fremd} vahvistetusta "
        "vieraasta: vahvin asukasvarmuus, jonka oikea vieras saavutti, "
        "oli {max} &rarr; kynnys {schwelle}; {pct} % aidoista kuvista "
        "pääsee läpi. Kolikon toinen puoli: {ueber} omista kuvistasi "
        "saavuttaisi tämän kynnyksen VÄÄRÄLLE henkilölle (vahvin {vmax}).",
    "personwizard.modell.eich_intern":
        "Mitattu {folds}-kertaisella ristiinvalidoinnilla {n} sivuun "
        "jätetystä kuvasta: vahvin varmuus VÄÄRÄLLE henkilölle {max} "
        "&rarr; kynnys {schwelle}; {pct} % aidoista kuvista pääsee läpi. "
        "Rehellinen raja: tämä kalibroi opittujen henkilöidesi VÄLILLÄ — "
        "oikeita vieraita ei ole vielä materiaalissa.",
    "personwizard.modell.regeln_titel": "Päätelmän asetukset",
    "personwizard.modell.schwelle_vor": "Päätöskynnys: ",
    "personwizard.modell.r_fenster": "Laukaisuikkuna",
    "personwizard.modell.r_feuer": "Tukitapahtumat ilmoitukseen",
    "personwizard.modell.r_karenz": "Rauhoitusaika ilmoituksen jälkeen",
    "personwizard.modell.regeln_satz":
        "Jätä kynnys tyhjäksi, niin se seuraa mitattua arvoa "
        "automaattisesti (se mitataan uudelleen jokaisessa "
        "koulutuksessa). Laukaisusääntö: ilmoitetaan vasta, kun ikkunan "
        "sisällä on näin monta tukitapahtumaa, ja sen jälkeen pysytään "
        "hiljaa rauhoitusajan verran.",
    "personwizard.modell.knopf_speichern": "Tallenna asetukset",
    "personwizard.modell.satz_user":
        "Päätöskynnys on sinun asettamasi ({schwelle})",
    "personwizard.modell.satz_user_eich":
        " — kalibrointi {n} vahvistettua vierasta vasten antaisi {alt}",
    "personwizard.modell.satz_geeicht":
        "Päätöskynnys on kalibroitu {n} vahvistetulla vieraan kuvalla.",
    "personwizard.modell.satz_ungeeicht":
        "Päätöskynnystä ei ole vielä kalibroitu vierasmateriaalilla — "
        "pidä ilmoituksia esikatseluna ja seuraa niitä.",
    "personwizard.modell.satz_fremd_drop":
        " Keho, jonka malli lukee vieraaksi, hylätään ennen kuin siitä "
        "voi tulla osuma.",
    "personwizard.modell.live_titel": "Live-kytkin",
    "personwizard.modell.live_an":
        "AKTIVOITU — kehotie arvioi live-tapahtumia ja saa ilmoittaa.",
    "personwizard.modell.live_aus": "Ei aktivoitu — kehotie pysyy hiljaa.",
    "personwizard.modell.live_hinweis":
        "Ilmoitukset kantavat merkinnän &quot;henkilöntunnistus, ei "
        "kasvot&quot;.",
    "personwizard.modell.knopf_disarm": "Poista aktivointi",
    "personwizard.modell.knopf_arm": "Aktivoi kehontunnistus",
    "baustein.gt.fremd": "Vieras",
    "baustein.gt.kein_mensch": "Ei henkilö",
    "baustein.gt.add": "lisää henkilö…",
    "baustein.gt.uebernehmen":
        "vahvista tämä ehdotus (kaikki luetellut olivat paikalla)",
    "baustein.gt.fremd_titel":
        "paikalla oli vieras (voi olla nimien rinnalla)",
    "baustein.gt.unklar_titel": "epävarma — jätä auki",
    "baustein.gt.kein_mensch_titel":
        "tässä tapahtumassa ei ole henkilöä (virhelaukaisu)",
    "baustein.gt.opak_titel":
        "vanha päätelmä, joka ei enää vastaa mitään tunnettua henkilöä — "
        "valitse ? tai nimi sen tilalle",
    "lernwizard.zw.js_zaehl_mitte": "/",
    "lernwizard.zw.js_zaehl_nach": " kuvaa valittu",
    "lernanker.js.uebernimmt": "otetaan käyttöön …",
    "lernanker.js.tag_frage_vor": "Nimeämisen jälkeen muuttuneet asetukset:\n",
    "lernanker.js.tag_frage_nach": "\nOtetaanko silti käyttöön nimetyllä valinnalla?",
    "lernanker.js.weiter": "tallennettu — seuraava ryhmä …",
    "lernanker.js.speichert": "tallennetaan …",
    "lernanker.js.koll_vor": "”",
    "lernanker.js.koll_mitte": "” on jo olemassa nimellä ”",
    "lernanker.js.koll_nach": "” — lisätäänkö sen sijaan tähän henkilöön?",
    "lernwizard.zw.js_gespeichert_vor": "tallennettu nimellä ",
    "lernwizard.zw.js_gespeichert_nach": " — kuvia tarkistetaan …",
    "lernwizard.sicht.js_fehl":
        "tarkistus epäonnistui — lataa sivu uudelleen ja yritä uudestaan",
    "lernwizard.zw.js_verbergen": "Piilota muut {n} tarkistettua kuvaa",
    "lernwizard.zw.js_zeigen": "Näytä kaikki {n} tarkistettua kuvaa",
    "qualitaet.galerie.js_gewaehlt": " valittu",
    "lernanker.js.alle_fertig":
        "Kaikki ryhmät käsitelty — nimetyt kuvat lasketaan nyt "
        "tunnistuksessa.",
    "vision.modell.js_id_fehlt": "syötä ensin ID",
    "vision.modell.js_prueft": "tarkistetaan …",
    "vision.modell.js_fehler": "virhe",
    "personwizard.review.js_zaehl": "/{n} merkitty vääräksi",
    "personwizard.review.js_frage_vor": "Päätetäänkö läpikäynti? ",
    "personwizard.review.js_frage_mitte":
        " kuvaa otetaan käyttöön oppimateriaalina, ",
    "personwizard.review.js_frage_nach": " hylätään.",
    "personwizard.modell.js_fehler": "virhe ",
    "antwort.person_entfernt":
        "{person} poistettu ({n} viitekuvaa siirretty roskakoriin — "
        "palautettavissa)",
    "antwort.person_name_ungueltig": "virheellinen nimi",
    "antwort.person_unbekannt": "tuntematon henkilö",
    "antwort.person_name_belegt":
        "Tällä nimellä on jo henkilö ({person}) — kahden henkilön "
        "yhdistäminen on suunniteltu myöhempään versioon.",
    "antwort.person_name_gleich": "nimi ennallaan — ei mitään tehtävää",
    "antwort.person_name_reserviert": "tämä nimi on varattu",
    "antwort.person_umbenennen_blockiert":
        "Uudelleennimeäminen ei ole juuri nyt mahdollista — taustalla on "
        "käynnissä: {jobs}. Odota ja yritä uudelleen.",
    "antwort.person_umbenennen_laeuft": "nimetään uudelleen …",
    "antwort.person_umbenennen_laeuft_schon":
        "yhtä henkilöä nimetään jo uudelleen",
    "antwort.pruefung_gestartet": "tarkistus käynnistetty",
    "antwort.pruefung_laeuft":
        "tarkistus käynnissä — lataa tämä sivu uudelleen noin minuutin "
        "kuluttua",
    "antwort.ref_batch_weg": "{n} kuvaa poistettu",
    "antwort.reorg_los":
        "Uudelleenryhmittely käynnissä (poolin tarkistus + ryhmien "
        "uudelleenmuodostus, 1–2 min, lataa sen jälkeen sivut uudelleen)",
    "antwort.reorg_laeuft":
        "Uudelleenryhmittely on jo käynnissä — odota hetki",
    "antwort.paar_notiert": "merkitty muistiin — tätä paria ei ehdoteta enää",
    "antwort.unbek_objekt": "merkitty ei-henkilöksi",
    "antwort.unbek_weg":
        "Tätä ryhmää ei ole enää (yhdistetty tai siivottu sillä välin) — "
        "kortti poistetaan.",
    "antwort.unbek_person": "takaisin vierailijoiden joukkoon",
    "antwort.unbek_gemergt": "{n} ryhmää yhdistetty yhdeksi",
    "antwort.nachpruefung_anhang":
        " — tämän käynnin tapahtumat tarkistetaan taustalla uudelleen",
    "antwort.sync_wieder": "{n} takaisin ehdokaslistalla",
    "antwort.sync_auswahl": "{ab} valinta poistettu, {zu} palautettu",
    "antwort.sync_laeuft":
        "täsmäytys on jo käynnissä — odota, kunnes se on valmis",
    "antwort.sync_readonly":
        "vain luku -tila: viitteiden kirjoittaminen Frigateen on kytketty "
        "pois (katso kytkin Järjestelmä-sivulla)",
    "antwort.sync_nichts":
        "ei mitään valittuna — merkitse vähintään yksi kuva",
    "antwort.frigate_url": "Frigaten URL: {fehler}",
    "antwort.sync_transfer": "siirto käynnissä ({n} valittu)",
    "antwort.bruecke_hinzu": "{n} kuvaa lisätty",
    "antwort.modell_laedt": "tunnistusmalli latautuu — pari sekuntia …",
    "antwort.refcache_baut":
        "viitekirjastoa rakennetaan uudelleen — suuressa kirjastossa tämä "
        "voi kestää minuutin …",
    "antwort.refcache_fehler":
        "viitekirjaston uudelleenrakennus epäonnistui kahdesti peräkkäin "
        "— katso palvelun loki (/log); seuraava yritys on muutaman "
        "minuutin päästä",
    "antwort.cache_aufgeraeumt":
        "{n} leikettä poistettu, {mb} MB vapautui — välimuisti {cache} "
        "GB, {frei} GB vapaana",
    "antwort.bruecke_nimmt": "tarkistus valitsee {n} kuvaa",
    "antwort.bruecke_grenz_zusatz":
        " · {n} rajatapausta näytetään ilman merkintää",
    "antwort.bruecke_nur_grenz":
        "ei mitään selvästi hyödyllistä — {n} rajatapauskuvaa pidätettiin "
        "(henkilöllisyys varma, kuvanlaatu vain keskitasoa); voit ottaa "
        "ne silti",
    "antwort.bruecke_nichts":
        "ei mitään otettavaa — tässä käynnissä ei ollut hyödyllistä uutta "
        "kuvaa (se on ihan hyvä)",
    "antwort.bruecke_undo": "{n} kuvaa poistettu taas",
    "antwort.passernte_verworfen":
        "tarkistus hylätty, kuvat ovat poissa — uusi napsautus tarkistaa "
        "uudelleen",
    "antwort.passernte_abgebrochen":
        "tarkistus keskeytetty — {n}/{m} tapahtumaa hylätty; se mikä on "
        "jo käynnissä, ajetaan loppuun, sen jälkeen kuvat poistetaan",
    "antwort.passernte_abbruch_leer":
        "ei mitään keskeytettävää — tämä tarkistus ei ole enää käynnissä",
    "antwort.personlauf_kein_review": "yksikään ajo ei odota läpikäyntiä",
    "antwort.personlauf_kein_lauf": "ei aktiivista ajoa",
    "antwort.events_bereich": "tapahtumien määrän on oltava 1..{max}",
    "antwort.personlauf_aktiv": "henkilöiden oppimisajo on jo käynnissä",
    "antwort.lernlauf_tag_ungueltig": "virheellinen päivä (VVVV-KK-PP)",
    "antwort.lernlauf_phase":
        "ajo on jo vaiheessa '{phase}' — keskeytä se ensin",
    "antwort.lernlauf_unterbrochen":
        "edellinen ajo keskeytyi — jatka sitä tai keskeytä se ensin ajon "
        "sivulla",
    "antwort.lernlauf_beschaeftigt":
        "edellinen ajo viimeistelee vielä nykyistä tapahtumaansa — yritä "
        "hetken kuluttua uudelleen",
    "antwort.lernlauf_schreibfehler":
        "ajon tilaa ei voitu kirjoittaa: {fehler}",
    "antwort.lernlauf_angelegt": "ajo luotu",
    "antwort.lernlauf_abgebrochen":
        "keskeytetty — käynnissä oleva tapahtuma voi vielä valmistua "
        "taustalla",
    "antwort.lernlauf_abbruch_leer":
        "juuri nyt ajon tilaa ei voi lukea — mitään ei keskeytetty; lataa "
        "sivu uudelleen ja yritä vielä kerran",
    "antwort.lernlauf_resume_unlesbar": "ajon tilaa ei voitu lukea: {fehler}",
    "antwort.lernlauf_resume_keiner": "ei ole ajoa, jota jatkaa",
    "antwort.lernlauf_resume_laeuft":
        "tämä ajo ei ole pysähtynyt — ei mitään jatkettavaa",
    "antwort.lernlauf_resume_fremd": "pysähtynyt ajo on sillä välin eri ajo",
    "antwort.lernlauf_resume_aktiv": "yksi tämän ajon etappi laskee vielä",
    "antwort.lernlauf_resume_etappe":
        "tätä ajoa ei voi jatkaa siitä kohdasta, johon se jäi",
    "antwort.lernlauf_resume_weg": "ajon tila katosi jatkamisen aikana",
    "antwort.lernlauf_resume_ok": "jatketaan",
    "antwort.live_nichts": "ei mitään muutettavaa",
    "antwort.live_nachtests":
        "{n} lähdetestiä ajetaan automaattisesti peräkkäin; jokainen "
        "vahti käynnistyy heti, kun sen testi läpäisee",
    "antwort.live_an": "käynnistetty {ok}/{alle} vahtia",
    "antwort.live_aus": "pysäytetty {ok}/{alle} vahtia",
    "antwort.vision_modell_ok":
        "malli vastasi — lisätty listaan käsin tarkistettuna; valitse se "
        "siellä ja tallenna",
    "antwort.restore_upload_fehlt": "lähetys puuttuu tai on liian suuri",
    "antwort.restore_upload_kaputt": "lähetys katkesi",
    "antwort.backend_unbekannt": "tuntematon backend '{backend}'",
    "antwort.kameras_fehlen":
        "Frigaten kamerat eivät ole käytettävissä: {fehler}",
    "antwort.setup_gespeichert":
        "Asennus tallennettu — palvelu käynnistyy uudelleen",
    "antwort.kameras_gespeichert":
        "{n} kameraa tallennettu — palvelu käynnistyy uudelleen",
    "antwort.name_ungueltig":
        "virheellinen henkilön nimi (2–40 kirjainta, numeroa, väli, -)",
    "antwort.anker_unbekannt": "tuntematon ankkuri",
    "antwort.anker_benannt":
        "nimetty '{name}' — {n} kuvaa valittu, ota ne käyttöön Ota "
        "käyttöön -painikkeella",
    "antwort.anker_nur_unadoptiert":
        "vain ryhmät, joista ei ole otettu kuvia käyttöön, voi hylätä",
    "antwort.anker_verworfen": "poistettu — {n} kuvaa poistettu",
    "antwort.lauf_id_ungueltig": "virheellinen ajon ID",
    "antwort.lauf_aktiv": "tämä ajo on vielä aktiivinen — keskeytä se ensin",
    "antwort.lauf_nichts": "ajolle {lauf} ei löytynyt mitään — jo poistettu?",
    "antwort.lauf_nur_einer":
        "ei mitään poistettavaa — varastossa on vain yksi ajo",
    "antwort.gruppe_unbekannt": "tuntematon tai suljettu ryhmä",
    "antwort.sichtung_laeuft": "kuvia tarkistetaan — pari sekuntia …",
    "antwort.anker_unbenannt":
        "ankkuria ei ole nimetty (tai se on tuntematon)",
    "antwort.benennen_mismatch":
        "valintasi ei vastannut yhtäkään tämän ryhmän kuvaa — lataa sivu "
        "uudelleen ja merkitse kuvat uudestaan",
    "antwort.adopt_nichts":
        "ei mitään valittuna — merkitse vähintään yksi kuva käyttöön "
        "otettavaksi",
    "antwort.adopt_phantom":
        "kaksoiskappaleiden tarkistus osui vain viitteisiin, joita ei "
        "enää ole levyllä — yritä käyttöönottoa uudelleen; jos tämä "
        "jatkuu, ilmoita siitä",
    "antwort.adopt_gedeckt":
        "jo katettu — kaikki {n} valittua kuvaa ovat lähes samanlaisia "
        "kuin henkilön {person} olemassa olevat viitteet; ryhmä merkitty "
        "käyttöön otetuksi, mitään ei kopioitu",
    "antwort.adopt_fertig.eins":
        "otettu käyttöön {n} viite henkilölle '{person}'",
    "antwort.adopt_fertig.viele":
        "otettu käyttöön {n} viitettä henkilölle '{person}'",
    "antwort.adopt_skip": ", {n} ohitettu lähes samanlaisina",
    "antwort.adopt_watchdog": " — drift-vahti käynnissä (Järjestelmä-sivu)",
    "antwort.areas_gespeichert.eins": "{n} alue tallennettu",
    "antwort.areas_gespeichert.viele": "{n} aluetta tallennettu",
    "antwort.clip_weg":
        "Leike ei ole enää välimuistissa — säilytys {tage} päivää",
    "system.backup.hinweis":
        "sisältää API-avaimesi — käsittele tätä tiedostoa kuin salasanaa",
    "visiongalerie.reihe.vorn": "edestä",
    "visiongalerie.reihe.seitlich": "sivulta",
    "visiongalerie.reihe.hinten": "takaa",
    "visiongalerie.reihe.unklar": "epäselvä",
    "baustein.kat.erkannt": "Tunnistettu",
    "baustein.kat.fremd_verdacht": "Vieras?",
    "baustein.kat.unbekannt_schwach": "Tuntematon (heikko)",
    "baustein.kat.fehler": "Virhe",
    "baustein.kat.no_person":
        "Henkilöä ei löytynyt (todennäköisesti virhelaukaisu)",
    "baustein.kat.uebersprungen": "Ohitettu käynnistyksessä",
    "baustein.kat.deckung": "Yhtenevä",
    "baustein.kat.widerspruch": "Ristiriita",
    "baustein.kat.frigate_nur": "Vain Frigate",
    "baustein.kat.wir_nur": "Vain suslik",
    "baustein.kat.beide_unknown": "Molemmat tuntemattomia",
    "baustein.stufe.clear": "selvä osuma",
    "baustein.stufe.narrow": "juuri rajan yllä",
    "baustein.stufe.below": "rajan alla",
    "baustein.stufe.none": "ei osumaa",
    "hilfe.live.titel": "Live-vahti selitettynä",
    "hilfe.live.satz1": "<p>Live-vahti katsoo kameroitasi heti, kun jokin liikkuu. Kun\nhenkilö astuu tontille, saat ilmoituksen sekunneissa — ja\njos järjestelmä tuntee kasvot jo, ilmoituksessa on nimi.</p>",
    "hilfe.live.satz2": "<p>Nimi on tässä vaiheessa ensimmäinen arvio. Perusteellinen tarkistus\najetaan heti sen jälkeen tallenteelle, ja sillä on viimeinen sana.</p>",
    "hilfe.live.satz3": "<p>Live-vahti ei riipu Frigatesta: sitä eivät käynnistä\nFrigaten tapahtumat, ja se toimii täysin omillaan. Se katsoo\nsuoraan videostreamia, joko Frigaten proxy-streamia\ntai kameran omaa streamia; sen valitset kameraa kohti.</p>",
    "hilfe.live.satz4": "<p>Painikkeella <b>Valitse kamerat</b> päätät, mitkä kamerat saavat vahdin. Jokainen\ntarkkailtu kamera kuluttaa laskentatehoa vuorokauden ympäri, joten aloita sieltä, mistä\nihmiset todella saapuvat: piha-alue, ovi, portti. Lisää voi aina ottaa myöhemmin.</p>",
    "hilfe.live.satz5": "<p>Kameran kytkeminen täällä pois ei muuta tallennusta mitenkään.\nFrigate tallentaa edelleen kuten ennen; kytkin päättää\nvain, katsooko suslik kuvaa heti vai odottaako tallennetta.</p>",
    "hilfe.gesicht.titel": "Kasvontunnistus selitettynä",
    "hilfe.gesicht.satz1": "<p>Tämä on perustie, jolla suslik tunnistaa ja oppii kasvot. Jokainen tallennettu\nkäynti tarkistetaan niitä kasvoja vasten, jotka olet järjestelmälle opettanut.</p>",
    "hilfe.gesicht.satz2": "<p>Opettaminen tapahtuu omista kameroistasi: suslik kerää näkemiään\nkasvoja, sinä katsot kuvat ja kerrot, kuka on kuka. Mitä useampia\nerilaisia tilanteita ja asentoja se on henkilöstä nähnyt, sitä paremmaksi\nse tulee: päivänvalo, ilta, pipo päässä, pipo pois, sivulta.</p>",
    "hilfe.gesicht.satz3": "<p>Jos Frigate tuntee kasvot jo, voit tuoda ne Frigate-täsmäytyksen\nsivulta. Suositus on kuitenkin opettaa kasvot täällä:\nsuslikin oma opetus kerää henkilöä kohti monia eri asentoja ja\ntilanteita, ja nämä viitteet antavat suslikissa paremmat tulokset\nkuin Frigatesta otetut kasvot. Sen, mitä täällä opetat, voit\nhalutessasi antaa takaisin Frigatelle täsmäytyssivulla.</p>",
    "hilfe.gesicht.satz4": "<p>Kaikki pysyy omalla koneellasi. Mitään ei lähetetä\nminnekään, eikä takana ole mitään pilvipalvelua.</p>",
    "hilfe.gesicht.satz5": "<p>Kun kasvot tunnistetaan tai paikalle tulee tuntemattomat kasvot,\nsuslik voi ilmoittaa siitä sinulle suoraan: Pushover, Telegram\ntai MQTT kotiautomaatiollesi. Ilmoitukset-sivulla valitset, mikä\nmenee minne. Nämä ilmoitukset ovat suslikin omia ja toimivat täysin\nriippumatta Frigatesta; Frigateen ei tarvitse asettaa mitään.</p>",
    "hilfe.gesicht.satz6": "<p><b>Hallitse henkilöitä</b> näyttää kaikki, jotka järjestelmä tuntee, ja siellä voit\nmyös siivota. <b>Rekisteröi kasvot</b> käynnistää oppimisajon jollekulle uudelle.</p>",
    "hilfe.koerper.titel": "Kehontunnistus selitettynä",
    "hilfe.koerper.satz1": "<p>Joissakin käynneissä ei näy koskaan käyttökelpoisia kasvoja:\nhenkilö katsoo poispäin, hänellä on huppu tai hän on liian kaukana.\nNämä tapaukset kattaa kehontunnistus. Se tunnistaa talon\nasukkaat ruumiinrakenteesta ja asennosta, koko henkilön kuvista.</p>",
    "hilfe.koerper.satz2": "<p>Se on rakennettu juuri tähän tapaukseen: ei käyttökelpoisia\nkasvoja, haluat silti tietää kuka se oli, eikä sitä\nvarten halua antaa kuvia tekoälyn Vision-mallille.</p>",
    "hilfe.koerper.satz3": "<p>Se oppii materiaalista, jonka hyväksyt. <b>Rekisteröi keho</b>\nkäynnistää lyhyen oppimisajon yhdelle henkilölle: järjestelmä\nkerää hänen kuviaan kameroistasi, sinä käyt tuloksen\nkertaalleen läpi, ja siitä lähtien se oppii itsekseen lisää.</p>",
    "hilfe.koerper.satz4": "<p>Yllä olevalla kytkimellä valitset, ajetaanko se ja milloin. <b>Only if no face</b>\ntarkoittaa: se pysyy hiljaa, ellei kasvotarkistus jää tyhjäksi. <b>Always</b>\ntarkoittaa: se tarkistaa jokaisen käynnin. Pois tarkoittaa: sitä ei ajeta koskaan.</p>",
    "hilfe.vision.titel": "Vision-tekoäly selitettynä",
    "hilfe.vision.satz1": "<p>Vision-tekoäly on oma tunnistustiensä. Se näyttää käynnin kuvat kuvamallille\nja kysyy, ketä rekisteröityä henkilöä ne muistuttavat. Voit käyttää sitä\nvarmistuksena vaikeisiin tapauksiin tai antaa sen kantaa tunnistuksen\nyksin: asetuksella <b>Always</b> se arvioi jokaisen käynnin itse, vaikka kasvoja\nei olisi opetettu lainkaan. Se arvioi käynnin päätteeksi, ei livenä.</p>",
    "hilfe.vision.satz2": "<p>Mitä se tarvitsee toimiakseen: rekisteröityjä henkilöitä, joilla on\nhyväksytyt kehokuvat (heidän galleriansa), ja yhdistetyn mallin. Malli voi\najaa paikallisesti omalla laitteistollasi tai pilvessä. Pilvimallin kohdalla\nmuista, että kuvat poistuvat talostasi: se mikä on paikallisen mallin\nkanssa kunnossa, ei ole automaattisesti sallittua pilvimallilla. Äläkä\nvalitse pienimpiä malleja; keskikokoinen malli hoitaa tehtävän hyvin.</p>",
    "hilfe.vision.satz3": "<p>Mitä itse ajamme: Qwen 3.5 koossa 9B, ja se hoitaa tehtävän\nhyvin, niin paikallisesti kuin pilvessä. Testasimme myös Anthropicin\n(Claude), Googlen (Gemini) ja OpenAI:n (GPT) malleja. Ota tämä\ntestattuna, ei suosituksena; Vision-sivun malliluettelo merkitsee\nmittaamamme mallit juuri siihen, missä valinta tehdään.</p>",
    "hilfe.vision.satz4": "<p>Eikä se jää yhteen vertailuun: sekaannusten poissulkemiseksi käynti\ntarkistetaan myös muiden henkilöiden gallerioita vasten, molempiin suuntiin.\nJokainen verrattu pari kustantaa kaksi pyyntöä, joten yhdestä käynnistä\nvoi kertyä jo jotakin. <b>If needed</b> pitää tämän laskun pienenä:\nmallilta kysytään vain, kun kasvot jättävät epäilyksen. Ilman yhdistettyä\nmallia Vision jää yksinkertaisesti pelistä pois, ja kortti sanoo sen.</p>",
    "hilfe.faces_bekannt.titel":
        "Tunnetut henkilöt & rekisteröinti selitettynä",
    "hilfe.faces_bekannt.satz1": "<p>Tässä näet jokaisen henkilön, jonka järjestelmäsi tuntee &mdash;\nnapauta kasvoja, niin näet jokaisen niiden taakse tallennetun kuvan.</p>",
    "hilfe.faces_bekannt.satz2": "<p>Uutta henkilöä ei opeteta kuvaa lähettämällä: opetus tapahtuu\ntavallisesta kameramateriaalista. Päivän mittaan järjestelmä\nkerää kuvia eri kulmista, sinä vahvistat kuka on kysymyksessä,\nja vasta tämän tarkistuksen jälkeen kuva säilytetään.</p>",
    "hilfe.faces_bekannt.satz3": "<p>Näin jokainen henkilö saa pienen kokoelman oikeita arjen\nkuvia &mdash; juuri se tekee tunnistuksesta vahvan, myös\nsilloin kun joku katsoo poispäin tai käyttää lippalakkia.</p>",
    "hilfe.faces_lernen.titel": "Opettaminen selitettynä",
    "hilfe.faces_lernen.satz1": "<p>Kameroiden käydessä järjestelmä kerää jatkuvasti uusia kuvia\nhenkilöistä, jotka se jo tuntee. Täällä käyt läpi sen, mitä\non kertynyt &mdash; muutaman päivän välein riittää hyvin.</p>",
    "hilfe.faces_lernen.satz2": "<p>Yhdellä napsautuksella vahvistat, korjaat tai\nhylkäät; mitään ei säilytetä ilman sinua.</p>",
    "hilfe.faces_lernen.satz3": "<p>Mitä enemmän hyviä kuvia henkilöllä on, sitä luotettavammin hän tunnistetaan\n&mdash; siksi opettaminen ei koskaan lopu täysin, se vain harvenee.</p>",
    "hilfe.faces_unbekannt.titel": "Tuntemattomat vierailijat selitettynä",
    "hilfe.faces_unbekannt.satz1": "<p>Jotkut ihmiset tulevat vastaan kerta toisensa jälkeen, ilman että järjestelmällä\non heille nimeä &mdash; postinkantaja, naapuri, puutarhuri. Täällä\njärjestelmä kerää näitä toistuvia tuntemattomia ja kysyy sinulta: kuka tämä on?</p>",
    "hilfe.faces_unbekannt.satz2": "<p>Anna heille nimi, ja siitä lähtien heidät tunnistetaan kuten\nkaikki muut. Tai jätä heidät tarkoituksella tuntemattomiksi &mdash;\nsekin on päätös, eikä järjestelmä kysele sitä yhä uudelleen.</p>",
    "hilfe.faces_qualitaet.titel": "Laatutarkistus selitettynä",
    "hilfe.faces_qualitaet.satz1": "<p>Ajan myötä kuvia kertyy paljon, eikä jokainen niistä auta tunnistusta &mdash; jotkut\novat epäteräviä, joistakin näkyy henkilöä tuskin lainkaan, ja pahimmassa tapauksessa\nkahden eri henkilön kuvat näyttävät niin samanlaisilta, että sekaannukset uhkaavat.</p>",
    "hilfe.faces_qualitaet.satz2": "<p>Tämä tarkistus löytää sellaiset heikot kohdat, ennen kuin ne kustantavat\nsinulle tunnistuksen. Saat konkreettiset vihjeet siitä, mitkä kuvat\nkannattaa katsoa &mdash; mitään ei poisteta, ellet itse päätä niin.</p>",
    "hilfe.faces_lernlauf.titel": "Oppimisajo selitettynä",
    "hilfe.faces_lernlauf.satz1": "<p>Sinä käynnistät ajon; järjestelmä lukee viimeiset\ntallenteesi uudelleen ja kerää kasvoja itsenäisesti.</p>",
    "hilfe.faces_lernlauf.satz2":
        "<p>Se lajittelee ne ryhmiin. Yksi ryhmä on tarkoitettu yhdelle "
        "henkilölle.</p>",
    "hilfe.faces_lernlauf.satz3": "<p>Sinä nimeät jokaisen ryhmän tai ohitat sen.\nSe on ainoa vaihe, joka tarvitsee sinua.</p>",
    "hilfe.faces_lernlauf.satz4": "<p>Nimetyistä kuvista tulee viitteitä ja ne lasketaan\ntunnistuksessa heti. Toista tämä muutaman päivän välein, tai anna\npäivänäkymän täydentää tunnettuja henkilöitä välillä.</p>",
    "hilfe.zurueck.erkennung": "Takaisin Tunnistukseen",
    "hilfe.zurueck.faces": "Takaisin Kasvot-sivulle",
    "hilfe.zurueck.lernlauf": "Takaisin oppimisajoon",
    "setupwiz.backend.system_satz":
        "Tarttuuko kiihdytin todella, sen vahvistaa käynnistyksen jälkeen "
        "livenä <b>Järjestelmä</b>-sivu (suslik ei koskaan putoa hiljaa "
        "takaisin CPU:lle sanomatta siitä).",
    "setupwiz.fertig.wieder_satz":
        "Voit ajaa tämän ohjatun asennuksen uudelleen milloin tahansa "
        "kohdasta <b>Järjestelmä → Aja ohjattu asennus uudelleen</b>.",
    "system.sync.diagnose_satz":
        'Jos täsmäytys ilmoittaa ongelmasta, <a href="/sync_diagnose" '
        'target="_blank">avaa diagnoosi</a> — se kokoaa suslikin raportin '
        'ja Frigaten lokin, valmiina kopioitavaksi issueen.',
    "system.sync.diagnose_kurz":
        '<a href="/sync_diagnose" target="_blank">avaa diagnoosi</a> — '
        'kokoaa suslikin raportin ja Frigaten lokin.',
    "vision.kopf.einleitung":
        "Kolmas tunnistustie kasvojen ja kehon rinnalla: "
        "Vision-kielimalli katsoo yhtä käynnin kuvaa ja sanoo, kuka "
        "opetetuista henkilöistäsi siinä on &mdash; vertaamalla sitä "
        "pieneen kyseisen henkilön galleriaan. Se on <b>ylimääräinen "
        "ääni</b>, ei koskaan ovimies: pakkovalinta vastaa &bdquo;A vai "
        "B&ldquo;, joten se voi vahvistaa asukkaan, mutta se ei voi "
        "torjua vierasta. Se pysyy olemassa olevan tunnistuksen "
        "tehtävänä.",
    "vision.hinweis.modell_satz":
        "Vision-malli, joka osaa katsoa useita kuvia yhtä aikaa. Voit "
        "käyttää alla olevia verkkopalveluntarjoajia tai ajaa mallia itse "
        "&mdash; tässä mitattu yhdistelmä on <b>llama.cpp</b> ja "
        "<b>Qwen3.5</b>-Vision-malli (4B on tässä tehtävässä yhtä hyvä "
        "kuin 9B ja tarvitsee noin puolet muistista). Sen <b>ei</b> "
        "tarvitse ajaa tällä koneella.",
    "vision.hinweis.host_satz":
        "<b>Tämä host on paikalliselle mallille yleensä liian pieni.</b> "
        "9B tarvitsee noin 12 GB työmuistia, 4B noin 6,6 GB, ja suslik "
        "sekä analyysiworker asuvat täällä jo &mdash; worker on "
        "ensimmäinen, jonka kernel ampuu alas, kun muisti loppuu. Toinen "
        "kone tai verkkopalveluntarjoaja on järkevä kokoonpano.",
    "vision.hinweis.mess_satz":
        "Varoitus tämän muistin mittaamisesta: <code>docker stats</code> "
        "näyttää mallin kontille noin 2,7 GiB, koska painot ovat "
        "mapattuja, ei kopioituja. Todellinen työmuisti on ~11,6 GiB. Jos "
        "mitoitat <code>--memory</code>-arvon sen mukaan, mitä "
        "<code>docker stats</code> sanoo, malli lataa painojaan "
        "lakkaamatta uudelleen ja kaikki matelee.",
    "vision.hinweis.kosten_satz":
        "Nopeus ja kustannus, mitattuina, ettei mikään yllätä myöhemmin: "
        "koko käynti menee sisään <b>yhtenä ehdokasruudukkona</b>, ja "
        "jokainen <b>verrattu galleriapari on kaksi pyyntöä</b> (sama "
        "kysymys kysytään uudelleen kahdella gallerialla vaihdettuina, "
        "jotta asemavinouma paljastuu). Yleensä yksi pari ratkaisee. "
        "CPU-luokan koneella se on noin 7 minuuttia paria kohti; tässä "
        "mitatuilla verkkopäätepisteillä sekunteja.",
    "vision.verb.key_ort":
        "<b>Syötä avain avainkenttään, ei URL:ään</b>: päätepiste, joka "
        "kantaa tunnuksia osoitteessaan &mdash; hostnimen edessä tai "
        "kyselyparametrina &mdash; sisältää saman salaisuuden, ja se "
        "päätyy paljon useampiin paikkoihin (tila, loki, varmuuskopio).",
    "vision.modell.leer_key":
        "Ei vielä mitään valittavaa. Syötä avaimesi ylle ja paina "
        "<b>Check the key</b>: suslik ottaa yhteyden päätepisteeseen, "
        "kysyy mitä siellä on, ja näyttää sinulle mitä se löysi. Siitä "
        "listasta valitset.",
    "vision.modell.leer_verbindung":
        "Ei vielä mitään valittavaa. Täytä yllä olevat kentät ja paina "
        "<b>Check the connection</b>: suslik ottaa yhteyden "
        "päätepisteeseen, kysyy mitä siellä on, ja näyttää sinulle mitä "
        "se löysi. Siitä listasta valitset.",
    "vision.modell.antwort_satz":
        "Tämän päätepiste vastasi, kun suslik kysyi siltä, {zeit} &mdash; "
        "mikään tässä ei ole meidän ehdotus. Siellä missä olemme mallin "
        "mitanneet, huomautus on kiinni siinä mallissa. Kaksi kykyä näkyy "
        "erikseen, koska ne eroavat toisistaan: <b>residents</b> "
        "tarkoittaa oikean valitsemista kahdesta tunnetusta henkilöstä, "
        "<b>strangers</b> tarkoittaa vastausta &bdquo;ei kumpikaan&ldquo; "
        "jollekulle, jota et ole koskaan opettanut. Merkki tarkoittaa: "
        "jokainen tämänlaatuinen päätelmä mittauksessamme oli oikein; "
        "vieressä oleva murtoluku kertoo koko kuvan. Malleista ilman "
        "mittausta lukee <b>täällä testaamaton</b> &mdash; se ei ole "
        "tuomio, vain rehellisyyttä (mittaukset {stand}).",
    "vision.prompt.eigen_satz":
        "Tämä on oma sanamuotosi &mdash; sillä tehdyt päätelmät on "
        "merkitty <b>muokattu sanamuoto</b>. Palauta se, jos haluat "
        "takaisin mitatun oletuksen.",
    "vision.cloud.sendet_satz":
        'Tämä lähettää kuvia ihmisistä kameroistasi kohteeseen <b '
        'class="vs-url">{ziel}</b>.',
    "vision.test.stufen_satz":
        "Kolme vaihetta, koska pelkkä tavoitettavuuden ping ei riitä: "
        "yksi backend oli tavoitettavissa, siinä oli malli ja se vastasi "
        "nopeasti &mdash; ja silti se vastasi 5 vertailukysymykseen "
        "12:sta väärin, koska se pienensi kuvat ennen kuin katsoi "
        "niitä.<br><b>1</b> tavoitettavuus, malli ja vasteaika, paikan "
        "päällä luodulla testikuvalla.<br><b>2</b> pakkovalinta-ajo "
        "luoduilla muotoruudukoilla, joissa oikea vastaus tunnetaan "
        "&mdash; tämä tarkistaa vastausmuodon, jäsentimen ja "
        "ajattelukytkimen.<br><b>3</b> tokenien laskenta mitattua "
        "viitettä vasten; näin kuvien pienentäminen "
        "paljastuu.<br><b>Yhtäkään ihmisen kuvaa ei käytetä tähän</b>, "
        "eikä siihen ole vaihtoehtoa.",
    "visiontest.kopf.wege_satz":
        "Valitse yksi oikea käynti ja katso rinnakkain, mitä kaikki kolme "
        "tunnistustietä siitä tekevät: <b>kasvot</b>, <b>henkilö</b> ja "
        "<b>Vision</b>.",
    "visiontest.vision.einrichten_satz":
        'Aseta se kohdassa <a href="/vision">Vision-tunnistus</a>: malli, '
        'vihreä yhteystesti ja vähintään kaksi hyväksyttyä galleriaa. '
        'Kaksi muuta saraketta toimivat ilmankin.',
    "visionwizard.groesse.satz":
        "Rehellisesti mitattuna: koko <b>ei</b> ollut vipu yhdessäkään "
        "ajamassamme tapauksessa &mdash; isompi ruudukko ei tehnyt "
        "vastauksista parempia, mutta ei myöskään huonompia. Ota isompi, "
        "jos materiaalisi kantaa sen (tässä: {empfehlung}), pienempi jos "
        "ei. Molemmat kustantavat saman verran, koska tokeneita kuluttaa "
        "kangas, ei solujen määrä.",
    "visionwizard.vorschlag.vergessen_satz":
        '<a href="#" onclick="vwVergessen();return false">Unohda ne</a>, '
        'jos haluat aloittaa alusta.',
    "visionwizard.vorschlag.satz":
        "Yksi rivi näkymää kohti: edestä, sivulta, takaa. Kuvat valitaan "
        "koon ja terävyyden mukaan, sen mukaan kuinka selvästi silmät ja "
        "nenä ovat näkyvissä, kuinka paljon valoa on palanut puhki, "
        "kuinka paljon rajauksesta on todella henkilöä &mdash; ja "
        "hajautettuna eri päiville, tapahtumille ja kameroille. Jokaisen "
        "kuvan alla oleva rivi kertoo, mitä siitä mitattiin. Napsauta "
        "kaikessa käyttökelvottomassa <b>ei sovi</b> &mdash; SAMAN "
        "näkymän seuraavaksi paras kuva nousee tilalle. Tämä ei koske "
        "oppimateriaaliasi; se sanoo vain &bdquo;ei gallerian "
        "soluksi&ldquo;.",
    "personwizard.kopf.stark_satz":
        "<b>Mikä tekee mallista vahvan:</b> vaihtelevuus voittaa määrän. "
        "Kuvat <b>monilta eri päiviltä</b> (vaatteet, valo, kamerat) "
        "auttavat paljon enemmän kuin monet kuvat yhdestä käynnistä — "
        "käynnistä keräys mieluummin uudelleen uusina päivinä kuin kaiva "
        "yhdestä päivästä syvemmälle. Vahvistetut vieraiden kuvat "
        "terävöittävät päätöskynnystä samalla tavalla.",
    "personwizard.fertig.training_satz":
        'Koulutus hyväksytyllä materiaalilla käynnistyy automaattisesti '
        'läpikäynnin jälkeen — katso <a href="/person/modell">Mallin '
        'tila</a>. Voit käynnistää alta uuden ajon milloin tahansa.',
    "personwizard.kontrolle.schalter_satz":
        'Kytke se kohdassa <a href="/konfiguration">Määritykset &rarr; '
        'Lisäasetukset</a>, avain <code>diagnostic_collection</code>. '
        'Kuvat ja loki vanhenevat yhdessä osumalokin kanssa 30 päivän '
        'jälkeen &mdash; mitään täällä ei säilytetä pidempään kuin '
        'tunnistuksen kirjanpitoa itseään.',
    "personwizard.kontrolle.leer_satz":
        'Kirjaukset ilmestyvät heti, kun kehontunnistus on aktivoitu '
        'sivulla <a href="/person/modell">Mallin tila</a> ja henkilö '
        'kulkee ohi.',
    "personwizard.bestand.leer_satz":
        'Aja <a href="/personlauf">henkilöiden oppimisajo</a> ja saata '
        'läpikäynti loppuun — hyväksytyt kuvat ilmestyvät tähän.',
    "personwizard.bestand.stark_satz":
        "Vaihtelevuus voittaa määrän: kuvat <b>monilta eri päiviltä</b> "
        "(vaatteet, valo) auttavat paljon enemmän kuin monet kuvat "
        "yhdestä käynnistä. Tavoittele useampia päiviä henkilöä kohti ja "
        "anna keräyksen kattaa kaikki kamerasi.",
    "personwizard.bestand.fremd_satz":
        "<b>Vieraat:</b> {n} vahvistettua vieraan kuvaa kalibroi "
        "päätöskynnystä — mitä useampia vieraita malli on nähnyt, sitä "
        "luotettavampi tämä viiva on. (Kerätään hakemistoon "
        "<code>personlern/fremd/</code>; sivu, jolla tätä joukkoa voi "
        "kasvattaa oman kadun liikenteestä, on suunnitteilla.)",
    "personwizard.bestand.fremd_erklaerung":
        "Vahvistetut vieraiden kuvat — ne kouluttavat lisäluokan ja "
        "kalibroivat päätöskynnyksen. Yhden poistaminen kouluttaa mallin "
        "heti uudelleen (tiedostot ovat hakemistossa "
        "<code>personlern/fremd/</code>).",
    "personwizard.modell.leer_satz":
        'Aja <a href="/personlauf">henkilöiden oppimisajo</a> ja saata '
        'läpikäynti loppuun — koulutus käynnistyy sen jälkeen '
        'automaattisesti.',
    "personwizard.modell.material_satz":
        'Hallitse kuvia kohdassa <a href="/person">Kehokuvat</a> — '
        'poistot kouluttavat mallin automaattisesti uudelleen.',
    "meldung.titel.kategorie": "suslik: {wort}",
    "meldung.alert.bestaetigt":
        "{name} vahvistettu ({wort}, nähty {n} ikkunassa)",
    "meldung.alert.keiner_naechster":
        "kukaan ei vahvistettu — lähimpänä on {name} ({wort})",
    "meldung.alert.keiner_ohne_gesicht":
        "kukaan ei vahvistettu — ei käyttökelpoisia kasvoja",
    "meldung.alert.satz":
        "{kamera} — {urteil}. Frigate näki: {label}. {gesichter}",
    "meldung.alert.gesichter.eins": "{n} kasvot tässä tapahtumassa.",
    "meldung.alert.gesichter.viele": "{n} kasvoa tässä tapahtumassa.",
    "meldung.alert.zahl": "[Frigate {score} (= cos {cos}) | {unsere}]",
    "meldung.person.titel": "suslik henkilöntunnistus",
    "meldung.person.satz":
        "{name} tunnistettu kehosta (henkilöntunnistus, ei kasvot) — "
        "{wort}, {n} tukitapahtumaa",
    "meldung.person.wort_ersatz": "osuma",
    "meldung.person.zahl": "[score {score}]",
    "meldung.vision.titel": "suslik Vision",
    "meldung.vision.unbestaetigt":
        "Vision ei voinut vahvistaa ketään tässä käynnissä",
    "meldung.vision.koerper_zusatz": "— kehontunnistus nimesi {namen}",
    "meldung.vision.bilder_zusatz": "({n} kuvaa ruudukossa)",
    "meldung.vision.einig":
        "Vision: {name} — yksimielinen, {voten}/{bilder} vertailua",
    "meldung.vision.kein_urteil": "Vision: ei päätelmää — {grund}",
    "meldung.wache.titel_person": "{wache} {kamera}: henkilö havaittu",
    "meldung.wache.titel_stoerung": "{wache} {kamera}: häiriö",
    "meldung.wache.caption": "{wache} {kamera}: {text}",
    "meldung.wache.titel_erkannt": "{wache} {kamera}: tunnistettu",
    "meldung.wache.nicht_erkannt": "ei tunnistettu",
    "heute.block.personen": "Henkilöt",
    "heute.block.personen_cnt.eins":
        "{n} tunnistettu · järjestetty viimeisen näkemisen mukaan",
    "heute.block.personen_cnt.viele":
        "{n} tunnistettu · järjestetty viimeisen näkemisen mukaan",
    "heute.person.bestaetigt": "ensimmäinen–viimeinen vahvistus {von}–{bis}",
    "heute.person.bestaetigt_einmal": "vahvistettu {zeit}",
    "heute.person.seit": "vahvistettu klo {zeit} lähtien",
    "heute.person.passes.eins": "{n} käynti",
    "heute.person.passes.viele": "{n} käyntiä",
    "heute.person.auftritte.eins": "{n} esiintyminen",
    "heute.person.auftritte.viele": "{n} esiintymistä",
    "heute.person.zuletzt": "viimeksi {kamera} {zeit}",
    "heute.person.live": "live",
    "heute.person.live_title":
        "nimetty vain live-vahdin toimesta (nimi-ilmoitus useiden "
        "löytöjen jälkeen) — ei vielä vahvistettua käyntiä",
    "heute.person.live_link": "siirry live-ilmoitukseen {zeit} · {kamera}",
    "heute.person.mehr": "kaikki {n} henkilöä ({m} lisää)",
    "heute.anw.dauer": "paikalla noin {h} h",
    "heute.anw.title":
        "läsnäolo tunneittain, kaikki kamerat — punainen: vahvistettu "
        "läsnäolo, vihreä: järjestelmä kävi, ketään ei nähty",
    "heute.anw.title_gesamt":
        "läsnäolo tunneittain — kaikki kamerat, ei suodatettu aluenäkymän "
        "mukaan",
    "heute.pass.mehr_kameras": "kaikki {n} kameraa ({m} lisää)",
    "heute.pass.live": "live",
    "heute.pass.live_title": "live-vahti ilmoitti nimen tämän käynnin aikana",
    "heute.rand.personen": "Henkilöt",
    "heute.rand.personen_title":
        "henkilöt, joilla on vähintään yksi vahvistus tänä päivänä — "
        "workerin päätelmät ja live-vahtien nimet",
    "heute.rand.passes_title":
        "käynnit: tapahtumat ryhmiteltyinä ajan ja paikan mukaan; pelkät "
        "liikekäynnit eivät laskennassa",
    "heute.rand.events_title":
        "tänä päivänä analysoidut tapahtumat, nykyisen näkymän kamerat",
    "heute.rand.unmatched": "ilman kohdennusta käynneissä",
    "heute.rand.unmatched_title":
        "tapahtumat, joiden kasvot eivät osuneet yhteenkään tunnettuun "
        "henkilöön, sellaisissa käynneissä joissa joku tunnistettiin — "
        "yleensä samat ihmiset",
    "heute.rand.unbek_title":
        "poolin tuntemattomat identiteetit, joilla on tukea tänä päivänä; "
        "ilman poolidataa: käynnit ilman yhtään tunnistusta",
    "meldung.wache.name_satz":
        "tunnistettu (live, alustava): {name} ({wort}, {n} yhtäpitävää "
        "vilkaisua)",
    "meldung.wache.name_zahl": "[kosini {cos}]",
    "meldung.wache.funde.eins": "{n} kasvot {sek} sekunnissa",
    "meldung.wache.funde.viele": "{n} kasvoa {sek} sekunnissa",
    "meldung.wache.funde_zahl": "(score {score}, {ms} ms)",
    "meldung.video_ersatz.satz": "(video ei saatavilla — lähetetään kuva)",
    "meldung.test.satz": "Testi-ilmoitus suslikilta ✓",
    "antwort.bruecke_nichts_grund": "ei mitään otettavaa — {grund}",
    "antwort.bruecke_grund_zusatz": " · {grund}",
    "antwort.bruecke_grund_zu_klein":
        "kaikki {n} tässä käynnissä mitatut kasvot ovat alle kasvojen "
        "vähimmäiskoon — suurin {kante} px, tarvitaan {min_kante} px",
    "antwort.bruecke_grund_zu_unscharf":
        "{n} tämän käynnin kasvot ovat liian epäteräviä viitteeksi — "
        "paras terävyys {sharp}, tarvitaan {unscharf_max}",
    "antwort.bruecke_grund_kein_gesicht":
        "ei mitattavia kasvoja tämän käynnin {n} tarkistetussa kuvassa",
    "antwort.bruecke_grund_gedeckt":
        "{n} tarkistetuista kasvoista ovat lähes samanlaisia kuin "
        "viitteet, jotka henkilöllä {person} jo on",
    "antwort.bruecke_grund_fremd_naeher":
        "{n} tarkistetuista kasvoista muistuttavat enemmän jotakuta "
        "toista kuin henkilöä {person}",
    "antwort.bruecke_grund_id_unsicher":
        "{n} tarkistetuista kasvoista ei ollut selvästi {person}",
    "antwort.bruecke_grund_beides_schwach":
        "{n} tarkistetuista kasvoista olivat heikkoja molemmissa — "
        "kuvanlaadussa ja henkilöllisyydessä",
    "antwort.bruecke_grund_kein_crop":
        "yhdelläkään tämän käynnin {n} tapahtumasta ei ole kasvorajausta "
        "tarkistettavaksi",
    "antwort.bruecke_grund_keine_events":
        "yhdessäkään tämän käynnin tapahtumassa {person} ei ole "
        "vahvistettu eikä paras osuma",
    "antwort.bruecke_grund_keine_referenzen":
        "henkilöllä {person} ei ole vielä viitekuvia vertailtavaksi",
    "antwort.einspielen.frigate_fehlt":
        "tähän asennukseen ei ole asetettu frigate_url-arvoa",
    "personwizard.kachel.sammeln": "Kerää kuvia",
    "personwizard.kachel.pruefen": "Käy kuvat läpi",
    "personwizard.k1.satz":
        "Valitse, kuka opetetaan ja kuinka kauas taaksepäin katsotaan "
        "&mdash; ajo kerää kuvat sitten omista tallenteistasi.",
    "personwizard.k2.satz":
        "Kerää kokovartalokuvia tallenteistasi, ja vain käynneistä, jotka "
        "kasvot ovat jo vahvistaneet.",
    "personwizard.k3.satz":
        "Vaihe, joka tarvitsee sinua: jokainen kerätty kuva saa sinun "
        "kyllä- tai ei-vastauksesi, ennen kuin mitään opitaan.",
    "personwizard.k4.satz":
        "Hyväksytyt kuvat kouluttavat kehomallin heti &mdash; se "
        "tunnistaa henkilöt sen jälkeen myös ilman näkyviä kasvoja.",
    "personwizard.such.titel": "Aseta henkilöiden oppimisajo",
    "systemstat.titel": "Järjestelmän kuorma",
    "systemstat.sub":
        "Tämän koneen kokonaiskuorma. Uusi mittaus {takt} sekunnin "
        "välein, säilytetään {stunden} tuntia. Prosessikohtaista jakoa ei "
        "täällä ole: Frigate ajaa omassa kontissaan, joten sen osuutta ei "
        "voi tältä puolelta nimetä. Se, mitä tämä laitteisto ei voi "
        "mitata, sanoo sen — nollan näyttämisen sijaan.",
    "systemstat.sub_live":
        "Tämän koneen kokonaiskuorma. Live: uusi mittaus {takt} sekunnin "
        "välein; historia säilyttää yhden mittauksen {ring} sekunnin "
        "välein {stunden} tunnin ajalta. Prosessikohtaista jakoa ei "
        "täällä ole: Frigate ajaa omassa kontissaan, joten sen osuutta ei "
        "voi tältä puolelta nimetä. Se, mitä tämä laitteisto ei voi "
        "mitata, sanoo sen — nollan näyttämisen sijaan.",
    "systemstat.leer.titel": "Ei vielä mittauksia.",
    "systemstat.leer.hinweis":
        "Ensimmäinen rivi syntyy noin {takt} sekuntia palvelun "
        "käynnistymisen jälkeen. Arvot, jotka tarvitsevat kaksi mittausta "
        "(CPU, NPU, GPU), tulevat kierrosta myöhemmin.",
    "systemstat.block.hardware": "Laitteisto",
    "systemstat.block.erkennung": "Tunnistus",
    "systemstat.block.live": "Live",
    "systemstat.nicht_verfuegbar": "ei käytettävissä",
    "systemstat.kein_prozent": "ei prosenttiarvoa",
    "systemstat.ja": "kyllä",
    "systemstat.nein": "ei",
    "systemstat.verlauf.leer": "ei vielä historiaa",
    "systemstat.verlauf.aria": "viimeinen tunti",
    "systemstat.cpu.anzahl": "Ydinten määrä",
    "systemstat.cpu.kerne": "ydintä kohti, juuri nyt",
    "systemstat.kachel.platte": "Levy",
    "systemstat.ram.genutzt": "Käytössä",
    "systemstat.ram.grafik": "Grafiikka (jaettu RAM)",
    "systemstat.ram.prozesse": "Prosessit",
    "systemstat.ram.limit": "Raja",
    "systemstat.ram.dateicache": "Tiedostovälimuisti",
    "systemstat.ram.dateicache_hinweis":
        "kernelin hallussa nopeampaa leikkeiden käsittelyä varten, "
        "vapautetaan heti kun muistia tarvitaan — ei vuoto, ei virhe",
    "systemstat.ram.belegt":
        "prosessit + grafiikka, ilman tiedostovälimuistia",
    "systemstat.ram.anteil": "Rajasta, sisältää välimuistin",
    "systemstat.ram.anteil_hinweis":
        "docker stats -näkymä: prosessit + grafiikka + tiedostovälimuisti "
        "rajaa vasten",
    "systemstat.platte.frei": "Vapaana",
    "systemstat.platte.gesamt": "Yhteensä",
    "systemstat.platte.cache": "Leikkeiden välimuisti / katto",
    "systemstat.platte.frei_min": "Pidä vapaana",
    "systemstat.gpu.engine": "Vilkkain engine",
    "systemstat.gpu.speicher": "Muisti",
    "systemstat.gpu.temperatur": "Lämpötila",
    "systemstat.gpu_eigen.titel": "GPU (suslikin osuus)",
    "systemstat.gpu.gesamt": "Koko kortti",
    "systemstat.gpu_eigen.zeile": "suslikin osuus",
    "systemstat.kachel.worker": "Analyysiworker",
    "systemstat.worker.laeuft": "käynnissä",
    "systemstat.worker.ruht": "lepää, käynnistyy tarvittaessa",
    "systemstat.worker.tode": "uudelleenkäynnistykset 24 h aikana",
    "systemstat.worker.zuletzt": "Viimeisin kuolema",
    "systemstat.worker.ursache": "Viimeisin syy",
    "systemstat.kachel.durchsatz": "Läpäisy",
    "systemstat.durchsatz.tag": "Viimeiset 24 h",
    "systemstat.durchsatz.dauer": "Keskimääräinen kesto",
    "systemstat.kachel.queue": "Tapahtumajono",
    "systemstat.queue.aeltester": "vanhin odottaa",
    "systemstat.queue.spur": "ilmoitusrata (avoimet · lähetetyt · virheet)",
    "systemstat.queue.poll": "poll-tila",
    "systemstat.queue.poll_hinweis":
        "tapahtumat tulevat suoraan pyyhkäisystä, tässä ei odota mikään — "
        "katso Ruuhka",
    "systemstat.kachel.frigate": "Frigaten vasteaika",
    "systemstat.frigate.mittel": "keskiarvo viime minuutilta",
    "systemstat.frigate.max": "hitain viime minuutilta",
    "systemstat.frigate.anfragen": "pyynnöt viime minuutilta",
    "systemstat.kachel.rueckstau": "Ruuhka",
    "systemstat.rueckstau.laeuft": "Ruuhkaa on",
    "systemstat.rueckstau.stand": "Jonoon otettu · jonossa · työn alla",
    "systemstat.rueckstau.stand_wert": "{gesamt} · {schlange} · {arbeit}",
    "systemstat.rueckstau.fenster": "Takautuva ikkuna",
    "systemstat.kachel.live": "Live-engine",
    "systemstat.live.waechter": "Vahteja aktiivisena",
    "systemstat.live.supervisor": "Supervisor",
    "systemstat.stand":
        "Mitattu klo {zeit}. Sivu latautuu itsestään uudelleen.",
    "systemstat.stand_live":
        "Mitattu klo {zeit}. Live: uusi mittaus {takt} sekunnin välein.",
    "systemstat.live_knopf": "Live",
    "systemstat.live_knopf.an": "Live · {rest} min",
    "systemstat.live_knopf.tip_aus":
        "Lataa uudelleen {takt} sekunnin välein, enintään {minuten} "
        "minuutin ajan, sitten takaisin normaaliin tahtiin. Sivulta "
        "poistuminen päättää sen myös.",
    "systemstat.live_knopf.tip_an":
        "Live vielä noin {rest} minuuttia. Napsautus lopettaa heti.",
    "systemstat.grund.erster_lauf":
        "odottaa toista mittausta — tämä luku on kahden mittauksen erotus",
    "systemstat.grund.kein_geraet": "tällaista laitetta ei ole tässä koneessa",
    "systemstat.grund.kein_zaehler":
        "laite on paikalla, mutta sen ajuri ei julkaise "
        "käyttöastelaskuria",
    "systemstat.grund.gesperrt":
        "laskuri on olemassa, mutta tämä kontti ei saa lukea sitä "
        "(kernelin suorituskykytapahtumat vaativat lisäoikeuksia)",
    "systemstat.grund.werkzeug_fehlt":
        "tämän laitteen kyselytyökalu ei ole osa tätä imagea",
    "systemstat.grund.nicht_lesbar": "tätä lähdettä ei voitu lukea",
    "systemstat.grund.kein_limit":
        "tälle kontille ei ole asetettu muistirajaa, joten prosenttiarvoa "
        "ei ole näytettävänä",
    "systemstat.grund.kein_dienst":
        "tämän luvun tietää vain käynnissä oleva palvelu",
    "systemstat.grund.keine_anfragen":
        "tämän palvelun käynnistymisen jälkeen Frigateen ei ole vielä "
        "mennyt yhtään pyyntöä",
    "anwesenheit.titel": "Läsnäolo",
    "anwesenheit.knopf": "Läsnäolo",
    "anwesenheit.knopf_tip":
        "Läsnäolo: kenen läsnäolo tontilla on vahvistettu, vartti "
        "kerrallaan",
    "anwesenheit.kopf_satz":
        "Yksi rivi henkilöä kohti, päivä varttitunnin soluina. Punainen = "
        "läsnäolo vahvistettu sillä vartilla (tapahtuma-analyysi tai "
        "live-vahti, näytetään kertaalleen). Varovaisella tunnistuksella "
        "vain harvat solut muuttuvat punaisiksi — se on normaalia, ei "
        "virhe.",
    "anwesenheit.seit": "Kirjaus alkaen {datum}.",
    "anwesenheit.fenster_auto":
        "Päiväikkuna {von}–{bis}, asetettu automaattisesti viimeisten "
        "{tage} päivän havaintojen perusteella; sen ulkopuoliset tunnit "
        "ovat yksi solu tuntia kohti.",
    "anwesenheit.fenster_werk":
        "Päiväikkuna {von}–{bis} (tehdasarvo, kunnes havaintoja on "
        "vähintään {n}); sen ulkopuoliset tunnit ovat yksi solu tuntia "
        "kohti.",
    "anwesenheit.fenster_fest":
        "Päiväikkuna {von}–{bis}, kiinteästi asetuksissa; sen "
        "ulkopuoliset tunnit ovat yksi solu tuntia kohti.",
    "anwesenheit.sicht_label": "Näkymä",
    "anwesenheit.sicht_alle": "Kaikki",
    "anwesenheit.sicht_kamera": "Kamera",
    "anwesenheit.sicht_area": "Alue",
    "anwesenheit.sicht_kamera_leer":
        "Yhtäkään kameraa ei ole vielä analysoitu",
    "anwesenheit.sicht_area_leer":
        "Alueita ei ole määritelty — luo ne Alueet-sivulla",
    "anwesenheit.nacht": "yö",
    "anwesenheit.legende_da": "läsnäolo vahvistettu",
    "anwesenheit.legende_weg": "järjestelmä kävi, ketään ei vahvistettu",
    "anwesenheit.legende_leer": "palvelu ei ollut käynnissä",
    "anwesenheit.legende_teil": "kävi, yksittäisiä tapahtumia ei analysoitu",
    "anwesenheit.legende_jetzt": "nyt",
    "anwesenheit.legende_satz":
        "Valkoinen tarkoittaa vain yhtä asiaa: palvelu ei ollut sinä "
        "aikana käynnissä. Vihreä solu, jonka kulma on leikattu, kertoo "
        "että palvelu kävi, mutta osa tapahtumista jäi analysoimatta — "
        "luvut näkyvät, kun viet osoittimen sen päälle.",
    "anwesenheit.zaehler":
        "{zeilen} merkintää luettu, {kaputt} rikkinäistä riviä ohitettu.",
    "anwesenheit.gekappt":
        "Päivän tiedosto on suurempi kuin lukuraja; vain sen loppu "
        "luettiin.",
    "anwesenheit.nie": "Tässä näkymässä ei nähty: {namen}",
    "anwesenheit.alle_leisten": "näytä kaikki henkilöt riveinä",
    "anwesenheit.leer_personen": "Ei vielä tunnettuja henkilöitä",
    "anwesenheit.leer_personen_hinweis":
        "Rivit ilmestyvät heti, kun henkilöitä on opetettu (Henkilöt → "
        "Tunnetut).",
    "anwesenheit.keine_aufzeichnung": "Tältä päivältä ei ole kirjausta.",
    "anwesenheit.tip_da": "{zeit} · {kameras} · {quelle}",
    "anwesenheit.tip_weg": "{zeit} · järjestelmä kävi, ketään ei vahvistettu",
    "anwesenheit.tip_weg_teil":
        "{zeit} · järjestelmä kävi, ketään ei vahvistettu · {gelungen} "
        "tapahtumaa analysoitu, {luecken} ei",
    "anwesenheit.tip_leer": "{zeit} · palvelu ei ollut käynnissä",
    "anwesenheit.tip_zukunft": "{zeit} · ei vielä",
    "anwesenheit.quelle_worker": "tapahtuma-analyysi",
    "anwesenheit.quelle_live": "live-vahti",
    "anwesenheit.quelle_beide": "live-vahti ja tapahtuma-analyysi",
    "anwesenheit.nav.heute": "Tänään",
    "anwesenheit.nav.gestern": "eilen",
    "anwesenheit.nav.attr_vortag": "edellinen päivä",
    "anwesenheit.nav.attr_folgetag": "seuraava päivä",
    "anwesenheit.nav.attr_kein_morgen": "ei tulevia päiviä",
    "anwesenheit.nav.attr_kein_frueher": "ei aiempaa kirjausta",
    "anwesenheit.nav.zurueck_heute": "takaisin tähän päivään",
    "anwesenheit.zeile_niemand": "ei kukaan",
    "gpu.titel": "Näytönohjain",
    "gpu.speicher_gesamt": "näytönmuistia",
    "gpu.keine_karte": "Näytönohjainta ei ole käytössä.",
    "gpu.keine_karte_cpu":
        "Tunnistus ajetaan prosessorilla. Se toimii, mutta on analyysia "
        "kohti noin kuusi kertaa hitaampaa, eikä toinen laskentasäie tuo "
        "siellä mitään: prosessori käyttää yhteen jo kaikkia ytimiään.",
    "gpu.balken.speicher": "Muisti",
    "gpu.balken.rechenzeit": "Laskenta-aika",
    "gpu.worker": "laskentasäie",
    "gpu.waechter": "live-vahti",
    "gpu.dienst": "palvelu",
    "gpu.frei": "vapaana",
    "gpu.reserve": "reservi",
    "gpu.belegt_andere": "käytössä, ei kohdennettavissa",
    "gpu.worker_prozess": "analyysiworker (kaikki säikeet)",
    "gpu.worker_unbekannt": "analyysiworker (osuus ei kohdennettavissa)",
    "gpu.q.gemessen": "mitattu",
    "gpu.q.tabelle": "mittaustaulukko",
    "gpu.q.posten": "suuntaa-antava",
    "gpu.q.config": "asetus",
    "gpu.q.formel": "kaava",
    "gpu.leiste_gemessen":
        "Palkki näyttää kortin sellaisena kuin se juuri nyt mitataan. "
        "Suuntaa-antaviksi merkityt osuudet tulevat vertailuarvoistamme, "
        "koska tämä kortti ei ilmoita niitä prosessia kohti.",
    "gpu.rechen.erklaerung":
        "Live-vahdit purkavat streamiaan yhtäjaksoisesti, olkoon paikalla "
        "joku tai ei. Tapahtuma-analyysi laskee purskeissa eikä ole tässä "
        "mukana.",
    "gpu.rechen.median": "tyypillinen",
    "gpu.rechen.spitze": "enintään, vilkkaalla kameralla",
    "gpu.rechen.bis": "enintään",
    "gpu.engpass.speicher": "Tässä rajoittaa muisti.",
    "gpu.engpass.rechenzeit": "Tässä rajoittaa laskenta-aika, ei muisti.",
    "gpu.noch_moeglich": "Tilaa {n} laskentasäikeelle lisää.",
    "gpu.passt_nicht":
        "Tämä ei mahdu. Vähennä vahteja tai laskentasäikeitä, muuten "
        "järjestelmä ajaa muistirajaan ja kernel päättää, mikä prosessi "
        "kuolee.",
    "gpu.regler.titel": "Laskentasäikeet",
    "gpu.regler.erklaerung":
        "Kuinka monta tapahtumaa analyysiworker saa laskea samaan aikaan. "
        "Taustatyö — keräys, kokoaminen ja kaikki, mitä napsautat — "
        "ajetaan niiden rinnalla omalla säikeellään eikä vie enää "
        "yhdeltäkään tapahtumalta paikkaa.",
    "gpu.regler.legacy":
        "Legacy-tila ilman analyysiworkeria (worker: false) on päällä, ja "
        "siinä tämä asetus ei ohjaa mitään: jokainen tapahtuma lasketaan "
        "omassa prosessissaan, yksi toisensa jälkeen.",
    "gpu.auto": "automaattinen",
    "gpu.vorschlag_ist": "nyt {n}",
    "gpu.speichern": "Tallenna",
    "gpu.neustart_noetig":
        "Tulee voimaan palvelun seuraavassa käynnistyksessä.",
    "gpu.messwerte":
        "Koneillamme mitattuna: {worker} MB laskentasäiettä kohti, "
        "{erster} MB ensimmäiselle live-vahdille (se kantaa mallit) ja "
        "noin {weiterer} MB jokaiselle seuraavalle. Likiarvoja, ei "
        "lupauksia. Rinnakkaiset analyysit olivat nopeimpia laitteistolla "
        "{hw} arvolla {n}; useampi ei testeissämme nopeutunut.",
    "gpu.knopf": "GPU",
    "gpu.knopf_tip":
        "Näytönohjain: mitä se kantaa ja miten se jaetaan analyysin ja "
        "live-vahtien välillä",
    "gpu.gespeichert":
        "Tallennettu. Tulee voimaan seuraavassa käynnistyksessä.",
    "gpu.nicht_messbar":
        "Kiihdytin on käytössä, mutta sen muistia ei voi lukea kontin "
        "sisältä. Tunnistus kyllä ajetaan sillä, vain alla olevat "
        "muistipalkit puuttuvat. Intel-järjestelmissä tämä on normaalia: "
        "ajurin laskurit eivät ole siellä luettavissa ilman "
        "lisäoikeuksia.",
    "gpu.abschnitt.jetzt": "Juuri nyt",
    "gpu.kachel.last": "Kortin kuorma",
    "gpu.kachel.last_unter": "koko kortti, viimeinen tunti",
    "gpu.kachel.last_eigen": "Meidän osuus",
    "gpu.kachel.last_eigen_unter":
        "mitä suslik itse käyttää (ajurin kokonaisluku ei ole kontissa "
        "luettavissa)",
    "gpu.kachel.npu": "NPU",
    "gpu.kachel.npu_unter": "Intelillä tunnistus ajetaan täällä",
    "gpu.kachel.vram": "Näytönmuisti",
    "gpu.kachel.vram_unter": "käytössä kortilla",
    "gpu.kachel.ram": "Meidän muisti",
    "gpu.kachel.ram_unter":
        "integroitu GPU jakaa järjestelmämuistin, omaa sillä ei ole",
    "gpu.kachel.temperatur": "Lämpötila",
    "gpu.kachel.temperatur_unter":
        "kortit alkavat yleensä hidastaa itseään vasta yli 80 °C:ssa",
    "gpu.engine.render": "render",
    "gpu.engine.compute": "compute",
    "gpu.engine.video": "video",
    "gpu.laeuft.titel": "Käynnissä:",
    "gpu.laeuft.zeile":
        "{plaetze} laskentasäiettä, niistä {belegt} varattuna{klassen} · "
        "{waechter} live-vahtia",
    "gpu.klasse.analyse": "analyysi",
    "gpu.klasse.ernte": "keräys (oppimisajo, täydennys)",
    "gpu.klasse.bg": "tausta",
    "gpu.klasse.interaktiv": "interaktiivinen (sinun napsautuksesi)",
    "gpu.klasse.live": "kehon päätelmä (live)",
    "gpu.zu_live": "Live-vahdit →",
    "gpu.noch_alt":
        "Palvelu ajaa vielä {laeuft} säikeellä; asetettu on {gesetzt}, ja "
        "se tulee voimaan seuraavassa käynnistyksessä.",
    "gpu.strang_ez": "laskentasäie",
    "gpu.strang_mz": "laskentasäiettä",
    "gpu.leiter_plaetze":
        "Palvelu ajaa {n} {strang} kortin budjetista; asetus on yläraja.",
    "gpu.leiter_plaetze_wartet":
        "Palvelu siirtyy {n} {strang} kortin budjetista; seuraavaan "
        "workerin käynnistykseen asti käytössä on edelleen {jetzt} "
        "{strang_jetzt}. Asetus on yläraja.",
    "gpu.passt_hoechstens":
        "Nykyisillä vahdeilla muistiin mahtuu enintään {n} säiettä.",
    "gpu.vorschau": "Jättäisi {rest} vapaaksi.",
    "gpu.neustart_knopf": "Käynnistä palvelu nyt uudelleen",
    "gpu.neustart_frage":
        "Käynnistetäänkö palvelu nyt uudelleen? Käynnissä olevat "
        "analyysit keskeytetään ja otetaan sen jälkeen uudelleen "
        "käsittelyyn.",
    "gpu.nicht_erreichbar":
        "Palvelua ei tavoiteta — se on todennäköisesti käynnistymässä "
        "uudelleen. Lataa hetken kuluttua uudelleen.",
    "gpu.laeuft_wie_eingestellt": "Aktiivinen: palvelu laskee {n} säikeellä.",
    "gpu.vorschau_zu_wenig":
        "Ei mahdu — {fehlt} liian vähän. Kytke yksi live-vahti pois tai "
        "ota yksi säie takaisin.",
    "gpu.speichern_gesperrt": "Näytönmuisti ei riitä tälle säiemäärälle.",
}
