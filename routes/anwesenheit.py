"""routes/anwesenheit — die Anwesenheitsseite /anwesenheit (Z4, 0.1.0.409;
Konzept analysen/anwesenheit_konzept.md §1/§4/§6, Befunde K7/M4/M5/M9/S4,
User-Entscheide §9: Variante A mit LEERER dritter Zelle, drei Filter als
Registerschalter, 30 Tage Zurueckblaettern, Scroll mit klebendem Namen).

Was die Seite zeigt (User-Auftrag 02.09., woertlich "wie die Partitionierung
von Platten"): eine Zeile je Person, dahinter der Tag in Viertelstunden-
Zellen. Rot = in dieser Viertelstunde bestaetigt da (Worker-Urteil ODER
Live-Waechter, nie doppelt — der Leser dedupliziert auf Person+Zelle).
Gruen = das System lief und hat niemanden bestaetigt. LEER = das System
lief nicht oder hat nicht hingesehen (keine Lauf-Marke, oder Lauf-Marke mit
Luecke). Die Semantik steht im Kopf von core/anwesenheit.py; hier gibt es
GENAU EINE Funktion dafuer (zustand), die Zellen, Nachtzellen und Legende
gemeinsam benutzen.

Tag und Nacht (Konzept §4): das Tagesfenster (fenster(cfg): Perzentil-
Automatik ueber 14 Tage, Werkswert unter 20 Marken, oder feste Vorgabe)
zeigt Viertelstunden; die Nachtstunden links und rechts davon werden je
Stunde EINE schmalere, gedaempfte Zelle — rot, sobald eine der vier
Viertelstunden rot ist; gruen nur, wenn alle vier gruen sind; sonst leer.
Alle Zeilen sind by construction gleich lang (feste Spaltenliste). Die
Leiste liegt in einem eigenen overflow-x-Container, der Name klebt links
(M5: die Seite selbst laeuft nie ueber; S9 misst 360/390/900/1280).

Filter (User §9.7, "drei kleine Registerschalter, die man einfach
anklickt"): Alle · Kamera · Area. Der Handler loest die Sicht in eine
Kameramenge auf und liest den Tag GENAU EINMAL damit; hier kommt das
fertige tag_lesen-Ergebnis herein. Die Nie-Gesehenen beziehen sich auf die
gewaehlte Sicht. Kein Filter-Formular, kein JS: jeder Schalter ist ein
Link, die URL traegt den ganzen Zustand, damit Vortag/Folgetag/"back to
today" die Sicht behalten.

ME1-Muster (routes/unbekannte.py): Daten als Parameter, kein Store-, kein
Dateizugriff im Renderer. Sprachschicht anwesenheit.* (fuenf Sprachen,
Deckungsvertrag; alle Schluessel stehen woertlich im Code — der Deckungs-
Scanner sieht keine gebauten Schluessel)."""
import datetime
import html
import urllib.parse

import webui
from core import anwesenheit as _anw
from core import areas as _areas
from core.sprache import t

# EINE Quelle der Sicht-Arten (Registerschalter) und der Zellzustaende
# (Zellen, Nachtzellen, Legende, Gate-Probe) — QS-Ebenen-Regel: fachliche
# Aufzaehlungen nie als Streu-Literal.
SICHTEN = ("alle", "kamera", "area")
ZUSTAENDE = ("da", "weg", "leer")
NACHT_JE_STUNDE = 4          # Viertelstunden je Nachtzelle
NACHT_LABEL_AB = 5           # Nachtblock traegt sein Label erst ab so vielen Stunden
DATUM_FMT = "%Y-%m-%d"


# ------------------------------------------------------------ Auswahl (rein)
def tag_waehlen(par, heute):
    """?tag=JJJJ-MM-TT -> gueltiges Datum oder heute. Unsinn (kein Datum,
    Jahr 9999 — /heute-Lehre 25.07.: strptime kommt durch, timestamp()
    wirft) und ZUKUNFT fallen still auf heute: ein Link in die Zukunft
    waere ein Versprechen, das die Seite nicht halten kann."""
    p = (par or "").strip()
    if not p:
        return heute
    try:
        d = datetime.datetime.strptime(p, DATUM_FMT)
        d.timestamp()
        (d + datetime.timedelta(days=1)).timestamp()
    except (ValueError, OverflowError, OSError):
        return heute
    return heute if p > heute else p


def sicht_waehlen(kameras, areas, kamera_par, area_par):
    """?kamera= / ?area= -> (art, name, kameramenge|None). Kamera vor Area
    (ein Registerschalter zur Zeit). Unbekannte Werte fallen still auf
    "alle" (Konzept §7); die Area loest core.areas.sicht_aufloesen ueber die
    BEOBACHTETEN Kameras auf (Default = Komplement, keine Areas = keine
    Sichten)."""
    k = (kamera_par or "").strip()
    if k and k in set(kameras):
        return "kamera", k, {k}
    if (area_par or "").strip() and areas:
        name, menge = _areas.sicht_aufloesen(areas, area_par, kameras)
        if menge is not None:
            return "area", name, menge
    return "alle", None, None


# ------------------------------------------------------------ Semantik (rein)
def zustand(zelle, person_eintrag):
    """DIE Renderer-Regel (core/anwesenheit Kopfkommentar): Person -> da
    (gewinnt immer, auch ohne Lauf-Marke); Lauf ohne Luecke -> weg; sonst
    leer. zelle = tag_lesen()["zellen"][c], person_eintrag = der Eintrag
    der Person fuer diese Zelle oder None."""
    if person_eintrag:
        return "da"
    if zelle and zelle.get("lauf") and not zelle.get("luecke_n"):
        return "weg"
    return "leer"


def nacht_zustand(zustaende):
    """Vier Viertelstunden -> eine Nachtzelle: rot, sobald eine rot ist;
    gruen nur, wenn ALLE gruen sind; sonst leer (eine leere Viertelstunde
    macht die Stunde zur "keine Aussage"-Stunde — ehrlicher als gruen)."""
    if "da" in zustaende:
        return "da"
    if zustaende and all(z == "weg" for z in zustaende):
        return "weg"
    return "leer"


def spalten(fenster):
    """Feste Spaltenliste des Tages: [("n", stunde)] links, [("t", zelle)]
    im Tagesfenster, [("n", stunde)] rechts. Jede Zeile und der Stunden-
    kopf laufen ueber DIESELBE Liste — deshalb sind alle Zeilen exakt
    gleich lang."""
    von, bis = int(fenster["von"]), int(fenster["bis"])
    von = max(0, min(23, von))
    bis = max(von + 1, min(24, bis))
    return ([("n", h) for h in range(0, von)]
            + [("t", c) for c in range(von * NACHT_JE_STUNDE, bis * NACHT_JE_STUNDE)]
            + [("n", h) for h in range(bis, 24)])


def _hhmm(zelle):
    return f"{zelle // 4:02d}:{(zelle % 4) * 15:02d}"


def _spanne(art, wert):
    if art == "t":
        return f"{_hhmm(wert)}–{_hhmm(wert + 1)}"
    return f"{wert:02d}:00–{wert + 1:02d}:00"


def _zellen_der_spalte(art, wert):
    if art == "t":
        return [wert]
    return [wert * NACHT_JE_STUNDE + i for i in range(NACHT_JE_STUNDE)]


# ------------------------------------------------------------ HTML-Bausteine
def _url(datum, heute, sicht, tag_erzwingen=False):
    """/anwesenheit?tag=&kamera=|area= — der ganze Zustand in der URL."""
    q = {}
    if datum != heute or tag_erzwingen:
        q["tag"] = datum
    art, name, _m = sicht
    if art == "kamera":
        q["kamera"] = name
    elif art == "area":
        q["area"] = name
    qs = urllib.parse.urlencode(q)
    return "/anwesenheit" + (f"?{qs}" if qs else "")


def _quelle_text(quellen):
    # Statisches Mapping auf den QUELLEN-Vertrag von core/anwesenheit (kein
    # gebauter Schluessel; der assert haelt beide deckungsgleich).
    texte = {"worker": t("anwesenheit.quelle_worker"),
             "live": t("anwesenheit.quelle_live")}
    assert set(texte) == set(_anw.QUELLEN)
    q = set(quellen or ())
    if q >= set(_anw.QUELLEN):
        return t("anwesenheit.quelle_beide")
    return ", ".join(texte[x] for x in _anw.QUELLEN if x in q) or "?"


def _zelle_html(person, art, wert, z, eintrag, datum, heute, sicht,
                jetzt_zelle, vergangen):
    """EINE Zelle. Rot ist ein Link (eid -> /pass/<eid>, sonst Personensicht
    des Tages — K7: dort gibt es keinen Slot-Filter, nur den Tag); gruen und
    leer sind spans. title + aria-label tragen die Aussage (M9: Farbe ist
    nie der einzige Traeger; dazu gefuellt/rahmenlos/leer per CSS)."""
    zeit = _spanne(art, wert)
    # Zustands-/Lagen-Klassen IMMER mit anw-Praefix: "leer" allein traefe die
    # Leerzustands-Regel .leer des Hauses (24 px Padding), "n"/"da" waeren
    # ebenso freie Kurznamen — Fund der Offline-Sicht 02.09.
    kl = ["anw-z", f"anw-{z}"]
    if art == "n":
        kl.append("anw-n")
    zellen = _zellen_der_spalte(art, wert)
    if jetzt_zelle is not None and jetzt_zelle in zellen:
        kl.append("anw-jetzt")
    if z == "da":
        tip = t("anwesenheit.tip_da", zeit=zeit,
                kameras=", ".join(eintrag["kameras"]) or "?",
                quelle=_quelle_text(eintrag["quellen"]))
        eids = eintrag["eids"]
        if eids:
            href = f"/pass/{urllib.parse.quote(eids[0])}"
        else:
            href = ("/auftritte?" + urllib.parse.urlencode(
                {"person": person, "tag": datum}))
        return (f'<a class="{" ".join(kl)}" href="{href}" '
                f'title="{html.escape(tip, quote=True)}" '
                f'aria-label="{html.escape(person + ": " + tip, quote=True)}"></a>')
    if not vergangen:
        tip = t("anwesenheit.tip_zukunft", zeit=zeit)
        kl.append("anw-zukunft")
    elif z == "weg":
        tip = t("anwesenheit.tip_weg", zeit=zeit)
    else:
        tip = t("anwesenheit.tip_leer", zeit=zeit)
    return (f'<span class="{" ".join(kl)}" title="{html.escape(tip, quote=True)}" '
            f'aria-label="{html.escape(person + ": " + tip, quote=True)}"></span>')


def _zeile_html(person, je_zelle, zellen, sp, datum, heute, sicht, jetzt_zelle):
    """Eine Personen-Zeile ueber die feste Spaltenliste. Zellen NACH jetzt
    (nur am laufenden Tag) bleiben leer und heissen "noch nicht" — nicht
    "keine Aussage"."""
    teile = []
    for art, wert in sp:
        cs = _zellen_der_spalte(art, wert)
        eintraege = [je_zelle.get(c) for c in cs]
        zs = [zustand(zellen.get(c), e) for c, e in zip(cs, eintraege)]
        z = zs[0] if art == "t" else nacht_zustand(zs)
        vergangen = jetzt_zelle is None or cs[0] <= jetzt_zelle
        if z != "da" and not vergangen:
            z = "leer"
        eintrag = None
        if z == "da":
            # Nachtzelle: die vier Eintraege zu EINEM Tooltip/Klickziel
            # vereinigen (Set-Semantik wie im Leser).
            eintrag = {"quellen": sorted({q for e in eintraege if e for q in e["quellen"]}),
                       "kameras": sorted({k for e in eintraege if e for k in e["kameras"]}),
                       "eids": sorted({x for e in eintraege if e for x in e["eids"]})}
        teile.append(_zelle_html(person, art, wert, z, eintrag, datum, heute,
                                 sicht, jetzt_zelle, vergangen))
    return (f'<div class="anw-r"><div class="anw-nm" title="{html.escape(person, quote=True)}">'
            f'{html.escape(person)}</div><div class="anw-l">{"".join(teile)}</div></div>')


def _kopf_html(sp):
    """Stundenkopf ueber DERSELBEN Spaltenliste: Tagesstunden als Zahl je
    vier Zellen, Nachtblock links/rechts als ein Label (Breite = Zellzahl,
    Pixel-Pitch liegt NUR in style.css)."""
    teile, i = [], 0
    while i < len(sp):
        art, wert = sp[i]
        if art == "n":
            j = i
            while j < len(sp) and sp[j][0] == "n":
                j += 1
            # Label nur, wenn der Block es traegt (unter NACHT_LABEL_AB Stunden
            # bliebe ein abgeschnittenes Wort); der Tooltip sagt es immer.
            txt = html.escape(t("anwesenheit.nacht"))
            teile.append(f'<span class="anw-hn" style="--n:{j - i}" title="{txt}">'
                         f'{txt if j - i >= NACHT_LABEL_AB else ""}</span>')
            i = j
        else:
            teile.append(f'<span class="anw-h">{wert // 4:02d}</span>')
            i += NACHT_JE_STUNDE
    return f'<div class="anw-kopf"><div class="anw-nm"></div><div class="anw-l">{"".join(teile)}</div></div>'


def _tagnav(datum, heute, sicht, tage):
    """Exakt der tagnav-Baustein von /heute: <- Vortag, Datum + Unterzeile,
    -> Folgetag (in der Zukunft gesperrt), "back to today". Untere Grenze =
    aeltester Tag mit Tagesdatei (User §9.4: Zurueckblaettern ueber die
    Aufbewahrung, keine Vergangenheit davor) — der Pfeil dorthin ist wie der
    Zukunfts-Pfeil gesperrt, nicht versteckt."""
    d = datetime.datetime.strptime(datum, DATUM_FMT)
    h = datetime.datetime.strptime(heute, DATUM_FMT)
    ist_heute = datum == heute
    aeltester = tage[0] if tage else heute
    zur = (d - datetime.timedelta(days=1)).strftime(DATUM_FMT)
    vor = (d + datetime.timedelta(days=1)).strftime(DATUM_FMT)
    titel = t("anwesenheit.nav.heute") if ist_heute else d.strftime("%A, %d %B %Y")
    unter = (d.strftime("%A, %d %B %Y") if ist_heute else
             (t("anwesenheit.nav.gestern") if (h - d).days == 1 else ""))
    if datum <= aeltester:
        links = (f'<span class="gtb" aria-disabled="true" '
                 f'title="{html.escape(t("anwesenheit.nav.attr_kein_frueher"), quote=True)}">&#8592;</span>')
    else:
        links = (f'<a class="gtb" href="{_url(zur, heute, sicht, tag_erzwingen=True)}" '
                 f'title="{html.escape(t("anwesenheit.nav.attr_vortag"), quote=True)}">&#8592;</a>')
    if ist_heute:
        rechts = (f'<span class="gtb" aria-disabled="true" '
                  f'title="{html.escape(t("anwesenheit.nav.attr_kein_morgen"), quote=True)}">&#8594;</span>')
    else:
        rechts = (f'<a class="gtb" href="{_url(vor, heute, sicht)}" '
                  f'title="{html.escape(t("anwesenheit.nav.attr_folgetag"), quote=True)}">&#8594;</a>')
    zurueck = ("" if ist_heute else
               f'<a class="gtb on" href="{_url(heute, heute, sicht)}">{html.escape(t("anwesenheit.nav.zurueck_heute"))}</a>')
    return (f'<div class="tagnav">{links}'
            f'<div class="tagnav-mitte"><div class="tagnav-t">{html.escape(titel)}</div>'
            f'<div class="tagnav-u">{html.escape(unter)}</div></div>{rechts}{zurueck}</div>')


def _filter_html(datum, heute, sicht, kameras, areas):
    """Drei Registerschalter (Pillen wie die Filterleiste von /unbekannte),
    daneben die Auswahl der gewaehlten Art. Ohne Kameras bzw. ohne Areas
    ist der Schalter deaktiviert und sagt warum (Tooltip)."""
    art, name, _m = sicht
    texte = {"alle": t("anwesenheit.sicht_alle"),
             "kamera": t("anwesenheit.sicht_kamera"),
             "area": t("anwesenheit.sicht_area")}
    assert set(texte) == set(SICHTEN)

    def pille(txt, ziel_sicht, aktiv, tip=""):
        if ziel_sicht is None:
            return (f'<span class="uk-f aus" title="{html.escape(tip, quote=True)}" '
                    f'aria-disabled="true">{html.escape(txt)}</span>')
        return (f'<a class="uk-f{" an" if aktiv else ""}" '
                f'href="{_url(datum, heute, ziel_sicht)}">{html.escape(txt)}</a>')

    area_namen = sorted(areas) + ["Default"] if areas else []
    erste_area = area_namen[0] if area_namen else None
    teile = [f'<span class="uk-lab">{html.escape(t("anwesenheit.sicht_label"))}</span>',
             pille(texte["alle"], ("alle", None, None), art == "alle"),
             pille(texte["kamera"],
                   ("kamera", name if art == "kamera" else kameras[0], None) if kameras else None,
                   art == "kamera", t("anwesenheit.sicht_kamera_leer")),
             pille(texte["area"],
                   ("area", name if art == "area" else erste_area, None) if erste_area else None,
                   art == "area", t("anwesenheit.sicht_area_leer"))]
    if art == "kamera":
        teile.append('<span class="uk-lab anw-sep" aria-hidden="true">&middot;</span>')
        teile += [pille(k, ("kamera", k, None), k == name) for k in kameras]
    elif art == "area":
        teile.append('<span class="uk-lab anw-sep" aria-hidden="true">&middot;</span>')
        teile += [pille(a, ("area", a, None), a == name) for a in area_namen]
    return f'<div class="uk-leiste anw-filter">{"".join(teile)}</div>'


def _fenster_satz(fenster):
    """Der Zwei-Drittel-Satz im Kopf (User §9.6): welches Fenster gilt und
    woher es kommt — Automatik (Perzentil ueber FENSTER_TAGE), Werkswert
    (unter FENSTER_MIN_MARKEN) oder feste Vorgabe. Zahlen aus dem Modul,
    nie aus einem Literal."""
    von, bis = int(fenster["von"]), int(fenster["bis"])
    q = fenster.get("quelle")
    if q == "override":
        return t("anwesenheit.fenster_fest", von=f"{von:02d}", bis=f"{bis:02d}")
    if q == "werk":
        return t("anwesenheit.fenster_werk", von=f"{von:02d}", bis=f"{bis:02d}",
                 n=_anw.FENSTER_MIN_MARKEN)
    return t("anwesenheit.fenster_auto", von=f"{von:02d}", bis=f"{bis:02d}",
             tage=_anw.FENSTER_TAGE)


def _seit_html(aeltester):
    """"Aufzeichnung seit <Datum>" — das Datum unumbrechbar (auf 360 px brach
    es mitten im Wert um). Der Text bleibt escaped, nur der Platzhalter wird
    durch das eine span ersetzt."""
    return (html.escape(t("anwesenheit.seit", datum="\x00"))
            .replace("\x00", f'<span class="anw-datum">{html.escape(aeltester)}</span>'))


def _legende():
    texte = {"da": t("anwesenheit.legende_da"),
             "weg": t("anwesenheit.legende_weg"),
             "leer": t("anwesenheit.legende_leer")}
    assert set(texte) == set(ZUSTAENDE)
    teile = "".join(f'<span><span class="anw-z anw-{z}" aria-hidden="true"></span>{html.escape(texte[z])}</span>'
                    for z in ZUSTAENDE)
    teile += (f'<span><span class="anw-z anw-leer anw-jetzt" aria-hidden="true"></span>'
              f'{html.escape(t("anwesenheit.legende_jetzt"))}</span>')
    return f'<div class="anw-legende">{teile}</div>'


# ------------------------------------------------------------ Seite
def render(daten, datum, heute, fenster, personen, kameras, areas, sicht,
           tage, jetzt=None):
    """-> Seiten-INHALT (Layout/Banner bleiben beim Handler).
    daten = core.anwesenheit.tag_lesen(cfg, datum, kameramenge der Sicht) ·
    datum/heute = JJJJ-MM-TT · fenster = core.anwesenheit.fenster(cfg) ·
    personen = master_persons(cfg) · kameras = beobachtete Kameras (dieselbe
    Liste wie der Ereignisliste-Filter) · areas = core.areas.normalisieren(…)
    · sicht = sicht_waehlen(…) · tage = core.anwesenheit.tage_vorhanden(cfg)
    · jetzt = Epoche (Jetzt-Marke; injizierbar fuer Proben)."""
    sp = spalten(fenster)
    ist_heute = datum == heute
    jetzt_zelle = None
    if ist_heute:
        jetzt_zelle = _anw.zelle_von_ts(jetzt if jetzt is not None else datetime.datetime.now().timestamp())
    zellen = daten.get("zellen") or {}
    je_person = daten.get("personen") or {}
    # Zeilen: jede Person mit mindestens einer roten Zelle in der Sicht,
    # sortiert nach erster Sichtung; danach die Nie-Gesehenen der Sicht
    # (bekannte Personen aus den Referenzen) als Namensliste.
    gesehen = sorted((p for p, z in je_person.items() if z),
                     key=lambda p: (min(je_person[p]), p))
    nie = [p for p in personen if p not in je_person or not je_person[p]]
    aeltester = tage[0] if tage else heute
    kopf = (f'<h2>{html.escape(t("anwesenheit.titel"))}</h2>'
            f'<p class="sub">{html.escape(t("anwesenheit.kopf_satz"))} '
            f'{_seit_html(aeltester)}</p>'
            + _tagnav(datum, heute, sicht, tage)
            + _filter_html(datum, heute, sicht, kameras, areas)
            + f'<p class="dim anw-fenster">{html.escape(_fenster_satz(fenster))}</p>')
    inhalt = kopf
    if not daten.get("zeilen") and not je_person:
        inhalt += (f'<p class="dim">{html.escape(t("anwesenheit.keine_aufzeichnung"))} '
                   f'{_seit_html(aeltester)}</p>')
    if not gesehen and not personen:
        return inhalt + webui.leer(t("anwesenheit.leer_personen"),
                                   t("anwesenheit.leer_personen_hinweis"))
    zeilen = [_zeile_html(p, je_person[p], zellen, sp, datum, heute, sicht, jetzt_zelle)
              for p in gesehen]
    if not zeilen:
        # Niemand rot: EINE Systemzeile statt einer Leiste je Person (Prod-
        # Sicht 02.09.: 20 identische gruene Zeilen in einer Kamera-Sicht
        # waren genau das Rauschen aus Konzept §8b). Die gruene/leere Flaeche
        # IST die Aussage — sie steht einmal da, die Nie-Gesehenen bleiben
        # Namensliste mit Umschalter wie sonst.
        zeilen = [_zeile_html(t("anwesenheit.zeile_niemand"), {}, zellen, sp,
                              datum, heute, sicht, jetzt_zelle)]
    inhalt += f'<div class="anw-wrap">{_kopf_html(sp)}{"".join(zeilen)}</div>' + _legende()
    if daten.get("kaputt") or daten.get("gekappt"):
        inhalt += (f'<p class="dim anw-zaehler">'
                   f'{html.escape(t("anwesenheit.zaehler", zeilen=daten.get("zeilen", 0), kaputt=daten.get("kaputt", 0)))}'
                   + (f' {html.escape(t("anwesenheit.gekappt"))}' if daten.get("gekappt") else "")
                   + '</p>')
    if nie:
        leisten = "".join(_zeile_html(p, {}, zellen, sp, datum, heute, sicht, jetzt_zelle)
                          for p in nie)
        inhalt += (f'<p class="anw-nie">{html.escape(t("anwesenheit.nie", namen=", ".join(nie)))}</p>'
                   f'<details class="anw-alle"><summary>{html.escape(t("anwesenheit.alle_leisten"))}</summary>'
                   f'<div class="anw-wrap">{_kopf_html(sp)}{leisten}</div></details>')
    return inhalt
