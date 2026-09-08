"""core/refurteil — DAS URTEIL des Bestands-Pruefers (Stufe C, .511).

WOZU: bis .510 urteilte die Bestands-QS ueber ein Katalogbild ausschliesslich
mit dem ALT-NORM-PAKET — Pixel-Kante, Laplacian-Schaerfe, Feature-Norm. Die
zwei KALIBRIERTEN Guete-Masse (`fiqa_t`, `empfinden` aus `core/guete.py`), an
denen der Nutzer seine Kameras einstellt, kannte der QS-Pfad an keiner Stelle.
Seit Stufe B misst der Lauf sie mit (Sidecar `core/refmess.py`); dieses Modul
faellt daraus das Urteil.

ROLLEN-ZUSCHNITT (User-Entscheid 08.09., eigene Korrektur des Vormittags):
**Die QS ist der BESTANDS-Pruefer, kein Aufnahme-Gate.** Jedes Bild darf ueber
jeden Weg in den Katalog (die Aufnahme-Wege behalten ihre eigenen Regeln,
`core/kamerakalib.py` mit `UEBERNAHME_STELLEN`). Dieses Modul prueft die schon
VORHANDENEN Bilder und schlaegt Aussortierungen vor. Deshalb hat es eine
EIGENE Latte und nimmt ausdruecklich NICHT die Katalog-Aufnahme-Latte mit:
waeren es dieselben Zahlen, verschoebe ein Zug am Aufnahme-Regler still den
Bestands-Befund (und umgekehrt) — zwei Fragen, zwei Latten.

NIE AUTO-LOESCHEN ([[nicht-loeschen-mehrdeutigkeit-aufloesen]]): dieses Modul
liefert Woerter, keine Handlungen. Kein Aufruf hier entfernt jemals eine Datei;
was der Nutzer wegklickt, entscheidet er auf der Seite.

DIE DREI ACHSEN, die hier zusammenkommen:

  1. BILDGUETE, zweistufig (User-Entscheid 08.09. ~15:4x):
       unter der fiqa_t-Latte UND unter dem Norm-Boden -> Vorschlag "raus"
       unter genau einer der beiden                    -> Markierung "auffaellig"
     Startwert der Latte `PRUEF_STARTWERTE["t"]`, Norm-Boden ist der BESTEHENDE
     Lernvorrat-Boden aus der Config (`vorrat_norm_min`, reist als
     `norm_latte["min"]`) — kein zweiter Boden.
     `sharp` (Laplacian) ist hier bewusst KEIN Kriterium mehr: gemessen AUC
     0,48 gegen die Sicht-Urteile und 0,17 gegen die Klick-Urteile (Stufe B §3d
     und `backups/nutzwert_0908/bericht.md` §4c) — es trennt nicht. Als
     technischer Pixel-Boden lebt es in `REF_LATTE` weiter, es faellt nur aus
     dem QUALITAETS-Urteil.

  2. IDENTITAET, als PERSONEN-Bericht (Fremdbild-Nachschau 08.09., §5): die
     Marge (Naehe zum eigenen Personen-Kern minus Naehe zum naechsten fremden
     Kern) taugt als EINZELBILD-Signal kaum — 63 der 65 messbaren negativen
     Bilder lagen ohnehin unter der Guete-Latte, exklusiv brachte sie zwei
     Bilder. Als PERSONEN-Signal lieferte sie den einzigen sauberen Treffer:
     eine Person, deren 5 von 5 Bildern negativ sind. Deshalb warnt dieses
     Modul JE PERSON (`gemischt`), und die Einzelbild-Marge bleibt eine
     Info-Zahl ohne Vorschlag.

  3. VIELFALT/REDUNDANZ: Byte-Dubletten (md5) als eigene Gruppe. Sie laufen
     VOR den Achsen (Bauplan-Punkt): der Medoid einer Person und ihre
     Negativ-Quote duerfen nicht davon abhaengen, wie oft dasselbe Bild im
     Ordner liegt. Auf dem Feldtester-Bestand sind das 96 Gruppen mit
     135 ueberzaehligen Dateien (11 %).

BASISPAKET-RANG: je Person werden die Referenzen nach `empfinden` gereiht
(AUC 0,955 an der Lern-Frage, strikter 19er-Schnitt in
`backups/nutzwert_0908/bericht.md` §4a3; 0,795 am vollen 72er-Eichsatz). Der
Rang ist ANZEIGE — keine Latte, kein Vorschlag (User-Entscheid: der Nutzer
soll sehen, welche Bilder sein Basispaket tragen, nicht welche gehen sollen).

MESSBARKEIT: alles hier ist FAIL-OPEN. Ein nicht gemessener Wert erzeugt nie
einen Vorschlag — das Gegenteil der `stimme_ok`-Regel, und zwar mit Absicht:
dort geht es um eine STIMME (eine ungemessene Stimme ist keine gemessene), hier
um einen LOESCH-Vorschlag (ein ungemessenes Bild wegzuschlagen waere ein
Verlust ohne Grundlage). Ungemessenes traegt das Wort `ungemessen` und landet
in keiner Vorschlagsgruppe.
"""
import collections
import hashlib
import os

# ---------------------------------------------------------------- Vertrag
# DIE Aufzaehlung der Urteilsworte (QS-Ebenen-Regel: eine zentrale Quelle statt
# verstreuter Literale). Reihenfolge = Strenge, aufsteigend.
URTEILE = ("ok", "auffaellig", "raus", "ungemessen")

# Werks-Startwert der PRUEFER-Latte. GEMESSEN, nicht gesetzt: 0,3425 ist die
# Youden-beste Schwelle von `fiqa_t` am 78er-Eichsatz (Stufe B §3a). Gegen die
# zweite Wahrheit desselben Tages — die 104 Klick-Urteile des Users an der
# Fremdbild-Nachschau — traf sie zusammen mit dem Norm-Boden 40 seiner 58
# "raus" als Vorschlag, 9 weitere als "auffaellig", und keinen einzigen seiner
# 28 "ok" als Vorschlag (9 der 58 waren zum Messzeitpunkt ungemessen).
# EINE Quelle: der Config-Default und der Vorgaben-Knopf der Kalibrierseite
# lesen von HIER (K3-Regel gegen Zweit-Literale, Muster core.guete.STARTWERTE).
PRUEF_STARTWERTE = {"t": 0.3425}

# Personen-Warnung "catalog looks mixed" ab welchem Anteil negativer Margen?
# Startwert MEHR ALS die Haelfte (User 08.09.): am Feldtester-Bestand faengt
# das genau den Fall, um den es geht — eine Person mit 5 von 5 negativen
# Bildern, deren Sichtpruefung ein Fremdbild bestaetigte —, und lasst die
# naechste Person (3 von 6 = genau 50 %) noch durch. Strikt groesser, damit
# "die Haelfte" nicht schon warnt.
GEMISCHT_ANTEIL = 0.5
# ... aber nie bei winzigen Personen: bei 1 Bild ist die Quote entweder 0 oder
# 100 %, und eine Ein-Bild-Person hat gar keinen eigenen Kern (ihre Marge ist
# nicht messbar). 3 ist die kleinste Zahl, bei der "mehr als die Haelfte" mehr
# als ein Bild bedeutet.
GEMISCHT_MIN_N = 3


# ---------------------------------------------------------------- Latten
def _zahl(wert, lo=0.0, hi=1.0):
    """Eine optionale Latten-Zahl -> float oder None. Unbrauchbares wird zu
    None (= keine Latte), nie zu einem geratenen Wert — dieselbe Regel wie
    core.kamerakalib._zahl, und aus demselben Grund: eine kaputte Zahl darf
    keinen Loesch-Vorschlag erzeugen."""
    if wert in (None, ""):
        return None
    try:
        z = float(wert)
    except (TypeError, ValueError):
        return None
    return z if lo <= z <= hi else None


def pruef_latten(cfg):
    """Das REISE-FERTIGE Latten-Dict des Bestands-Pruefers (Muster
    kamerakalib.katalog_latten: die Latte reist als fertiges Dict, der
    Verbraucher waehlt nie selbst Config-Schluessel aus).

    -> {"global": {"t": float|None}, "kameras": {name: {"t": float|None}}}

    Ablageort ist bewusst KEIN zweiter Store: die Kamera-Werte liegen im
    vorhandenen Guard-Block `live.guards.<kamera>.pruef_t_min` (EIN Schreibweg
    live_speichern, EINE Normalisierung guards_lesen), der globale Rueckfall
    in `pruef_guete_t_min`. Gelesen wird ueber core.kamerakalib.guards — kein
    zweiter Leser des Store-Blocks.

    Je Aufruf frisch aus cfg (kein Env-Transport): ein Zug am Regler muss
    SOFORT gelten, dieselbe Zusage wie bei den Katalog-Latten."""
    from core import kamerakalib as _kk
    aus = {"global": {"t": _zahl((cfg or {}).get("pruef_guete_t_min"))},
           "kameras": {}}
    for name, g in (_kk.guards(cfg or {}) or {}).items():
        t = _zahl(g.get("pruef_t_min"))
        if t is not None:
            aus["kameras"][str(name)] = {"t": t}
    return aus


def pruef_werte(latten, kamera):
    """Die WIRKSAME Pruef-Latte fuer eine Kamera -> {"t", "quelle"}.
    quelle: 'kamera' | 'global' | 'aus'. Kamera schlaegt global, global gilt
    fuer alles ohne eigenen Wert — auf dem Feldtester-Bestand sind das die
    133 Referenzen, deren Kamera auch der Nachtrag nicht aufloesen konnte
    (Stufe B §2.6)."""
    l = latten or {}
    kam = (l.get("kameras") or {}).get(str(kamera or ""))
    if kam and kam.get("t") is not None:
        return {"t": kam.get("t"), "quelle": "kamera"}
    gl = l.get("global") or {}
    if gl.get("t") is not None:
        return {"t": gl.get("t"), "quelle": "global"}
    return {"t": None, "quelle": "aus"}


# ---------------------------------------------------------------- Bild-Urteil
def bild_urteil(latten, kamera, fiqa_t, norm, norm_boden):
    """DIE eine Frage des Bestands-Pruefers ueber EIN vorhandenes Bild:
    -> (urteil, gruende) mit urteil aus URTEILE und gruende als Liste
    ('guete', 'norm') der Achsen, die unter ihrer Latte liegen.

    ZWEISTUFIG (User 08.09.):
      beide Achsen gemessen UND beide unterschritten -> "raus"  (Vorschlag)
      genau eine unterschritten                      -> "auffaellig" (Markierung)
      keine unterschritten                           -> "ok"
      keine der beiden Achsen ueberhaupt beurteilbar -> "ungemessen"

    FAIL-OPEN, dreifach:
      * Latte nicht gesetzt (quelle 'aus', norm_boden None) -> diese Achse
        urteilt nicht. Steht KEINE Latte, kommt "ungemessen" zurueck und der
        Bestand bleibt unmarkiert — genau wie vor diesem Bau.
      * Wert nicht gemessen (None) -> diese Achse urteilt nicht. Ein Bild ohne
        Guete-Messung (Alt-Image ohne die ONNX-Dateien, tote Nach-Detektion)
        darf nie ueber eine Zahl fallen, die niemand hat.
      * Nur eine Achse verfuegbar -> hoechstens "auffaellig". "Raus" verlangt
        ZWEI unabhaengige Anzeichen; das ist der Sinn der Zweistufigkeit.

    Bewusst NICHT dabei: `sharp`. Gemessen trennt es weder die Sicht-Urteile
    (AUC 0,48) noch die Klick-Urteile (0,17) — es bleibt technischer
    Pixel-Boden in REF_LATTE, aber es urteilt hier nicht mit."""
    w = pruef_werte(latten, kamera)
    gruende = []
    achsen = 0
    t_latte = w.get("t")
    if t_latte is not None:
        t_ist = _zahl(fiqa_t, -10.0, 10.0)
        if t_ist is not None:
            achsen += 1
            if t_ist < float(t_latte):
                gruende.append("guete")
    nb = None if norm_boden in (None, "") else _zahl(norm_boden, 0.0, 100.0)
    if nb is not None:
        n_ist = _zahl(norm, 0.0, 100.0)
        if n_ist is not None:
            achsen += 1
            if n_ist < float(nb):
                gruende.append("norm")
    if not achsen:
        return "ungemessen", []
    if len(gruende) >= 2:
        return "raus", gruende
    if gruende:
        return "auffaellig", gruende
    return "ok", []


# ---------------------------------------------------------------- Dubletten
def md5_gruppen(master_dir, dateien):
    """Byte-gleiche Dateien -> [{"md5", "person", "behalten", "weg": [...]}].

    Gruppiert wird ueber den DATEI-Inhalt, nicht ueber eine Aehnlichkeit: das
    ist die eine Dubletten-Klasse, bei der es nichts abzuwaegen gibt (die
    Nah-Dubletten macht die vorhandene `doppel`-Achse mit `dup_sim`). Auf dem
    Feldtester-Bestand: 96 Gruppen, 135 ueberzaehlige Dateien, KEINE davon
    ueber eine Personengrenze hinweg.

    `behalten` ist der erste Name in sortierter Reihenfolge — stabil ueber
    Laeufe, damit ein Vorschlag nicht bei jedem Lauf auf ein anderes Bild
    zeigt. Ein Grund, einen bestimmten Zwilling vorzuziehen, gibt es bei
    BYTE-Gleichheit nicht; jede andere Wahl waere eine erfundene Ordnung.

    Gruppen ueber Personengrenzen hinweg werden je Person aufgeteilt: dasselbe
    Bild bei zwei Personen ist ein IDENTITAETS-Befund (die Verwechslungs-Achse
    fuehrt ihn ohnehin mit sim 1,0) und kein Aufraeum-Vorschlag — welche der
    beiden Personen es abgeben soll, kann keine Rechnung wissen."""
    je_hash = collections.defaultdict(list)
    for p, f in dateien or ():
        pfad = os.path.join(master_dir, p, f)
        try:
            with open(pfad, "rb") as fh:
                h = hashlib.md5(fh.read()).hexdigest()      # noqa: S324
        except OSError:
            continue                     # nicht lesbar -> keine Dubletten-Aussage
        je_hash[h].append((p, f))
    aus = []
    for h, paare in sorted(je_hash.items()):
        je_person = collections.defaultdict(list)
        for p, f in paare:
            je_person[p].append(f)
        for p, fs in sorted(je_person.items()):
            if len(fs) < 2:
                continue
            fs = sorted(fs)
            aus.append({"md5": h, "person": p, "behalten": fs[0],
                        "weg": fs[1:]})
    return aus


def ueberzaehlig(gruppen):
    """{(person, datei)} aller ueberzaehligen Dubletten — die Menge, die VOR
    der Achsen-Rechnung aus Kern und Quote faellt (Bauplan-Punkt)."""
    return {(g["person"], d) for g in (gruppen or ()) for d in g["weg"]}


# ---------------------------------------------------------------- Identitaet
def achsen(BE, S, ueberzaehlig_set=(), np=None):
    """Die relationalen Achsen ueber die Bilder MIT Embedding.

    BE  = Liste der Bild-Dicts (person/datei/emb), wie sie pruefe_referenzen
          ohnehin fuehrt; S = die schon gerechnete Aehnlichkeits-Matrix
          (S = M @ M.T) derselben Reihenfolge — hier wird KEINE zweite Matrix
          gebaut (auf 1158 Bildern sind das 5 MB, die es bereits gibt).
    ueberzaehlig_set = die Byte-Dubletten, die NICHT in Kern und Quote
          eingehen (Entdopplung vor den Achsen). Sie bekommen trotzdem ihre
          eigene Marge gegen den entdoppelten Kern — sonst fehlte dem Nutzer
          die Zahl zu einem Bild, das er vor sich sieht.

    -> (je_bild, je_person)
       je_bild[(p, d)]   = {"marge", "sim_eigen", "fremd", "nn_eigen"}
       je_person[p]      = {"marge_n", "marge_neg", "gemischt", "fremd"}

    `nn_eigen` ist das EXPERIMENT des Bauplans (Abstand zum naechsten EIGENEN
    Bild statt zum Kern): gemessen, berichtet, KEINE Achse — es hat den
    bestaetigten Fremdbild-Fall der einen Klasse nicht getrennt (Rang 332 von
    1045 nach Entdopplung), waehrend es den anderen auf Rang 4 setzte.
    Ohne User-Entscheid faellt daraus kein Vorschlag."""
    if np is None:
        import numpy as np           # noqa: PLC0415
    n = len(BE)
    je_bild, je_person = {}, {}
    if n < 2 or S is None:
        return je_bild, je_person
    schluessel = [(b["person"], b["datei"]) for b in BE]
    weg = set(ueberzaehlig_set or ())
    idx = collections.defaultdict(list)          # person -> Zeilen (Vertreter)
    for i, (p, d) in enumerate(schluessel):
        if (p, d) not in weg:
            idx[p].append(i)
    if not idx:
        return je_bild, je_person
    personen = sorted(idx)
    # Voll-Medoid je Person EINMAL (der fremde Kern); Vertreter-Zeilen only.
    kern = {}
    for p in personen:
        ii = idx[p]
        if len(ii) == 1:
            kern[p] = ii[0]
            continue
        sub = S[np.ix_(ii, ii)]
        kern[p] = ii[int(np.argmax(sub.sum(axis=1)))]
    kern_zeilen = [kern[p] for p in personen]
    for i, (p, d) in enumerate(schluessel):
        ii = idx.get(p) or []
        # eigener Kern OHNE das Bild selbst (leave-one-out): sonst waere jedes
        # Bild sich selbst am naechsten und die Marge eine Tautologie.
        rest = [j for j in ii if j != i]
        if not rest:
            je_bild[(p, d)] = {"marge": None, "sim_eigen": None,
                               "fremd": None, "nn_eigen": None}
            continue
        if len(rest) == 1:
            j_med = rest[0]
        else:
            sub = S[np.ix_(rest, rest)]
            j_med = rest[int(np.argmax(sub.sum(axis=1)))]
        sim_eigen = float(S[i, j_med])
        nn_eigen = max(float(S[i, j]) for j in rest)
        best, best_p = None, None
        for k, q in enumerate(personen):
            if q == p:
                continue
            s = float(S[i, kern_zeilen[k]])
            if best is None or s > best:
                best, best_p = s, q
        je_bild[(p, d)] = {
            "marge": (round(sim_eigen - best, 4) if best is not None else None),
            "sim_eigen": round(sim_eigen, 4),
            "fremd": best_p,
            "nn_eigen": round(nn_eigen, 4)}
    # --- je Person: Quote der negativen Margen ueber die VERTRETER ----------
    for p in personen:
        werte = [je_bild[schluessel[i]]["marge"] for i in idx[p]
                 if je_bild.get(schluessel[i], {}).get("marge") is not None]
        if not werte:
            continue
        neg = sum(1 for m in werte if m < 0)
        fremd = collections.Counter(
            je_bild[schluessel[i]].get("fremd") for i in idx[p]
            if je_bild.get(schluessel[i], {}).get("marge") is not None
            and je_bild[schluessel[i]].get("marge") < 0
            and je_bild[schluessel[i]].get("fremd"))
        je_person[p] = {
            "marge_n": len(werte), "marge_neg": neg,
            "gemischt": bool(len(werte) >= GEMISCHT_MIN_N
                             and neg > GEMISCHT_ANTEIL * len(werte)),
            "fremd": (fremd.most_common(1)[0][0] if fremd else None)}
    return je_bild, je_person


# ---------------------------------------------------------------- Basispaket
def basispaket_rang(B):
    """Je Person die Reihung nach `empfinden` -> {(person, datei): rang},
    1 = bestes Bild dieser Person.

    WARUM `empfinden` und nicht `fiqa_t`: an der Lern-Frage ("taugt das Bild
    zum Lernen?") ist es das staerkere Mass — AUC 0,955 auf dem strikten
    19er-Schnitt, 0,795 am vollen 78er-Eichsatz gegen 0,660 fuer `fiqa_t`
    (Stufe B §3b/§3d). Die n=9-Hypothese, `empfinden` laufe gegenlaeufig, ist
    am groesseren Satz widerlegt.

    Es ist AUSDRUECKLICH keine Latte: der Rang sagt, welche Bilder das
    Basispaket einer Person tragen — er schlaegt nie vor, den Rest zu
    entfernen. Bilder ohne `empfinden` bekommen keinen Rang (None), statt
    hinten einsortiert zu werden: "nicht gemessen" ist nicht "schlecht"."""
    je_person = collections.defaultdict(list)
    for b in B or ():
        e = b.get("empf")
        if e is None:
            continue
        try:
            je_person[b["person"]].append((float(e), b["datei"]))
        except (TypeError, ValueError):
            continue
    aus = {}
    for p, lst in je_person.items():
        for r, (_e, d) in enumerate(sorted(lst, key=lambda x: (-x[0], x[1])), 1):
            aus[(p, d)] = r
    return aus
