"""core/kamerakalib — DIE eine Auslegung der Kamera-Kalibrierwerte
(User-Entscheid 31.08. "EIN Menuepunkt Kamera-Kalibrierung", Drei-Latten-Semantik).

WARUM JE KAMERA: die Gueteskalen sind kameraabhaengig. Gemessen am 31.08. an
Feldmaterial: Median fiqa_t 0,181 auf der einen Kamera gegen 0,073 auf der
anderen. Eine gemeinsame Zahl ist fuer die eine grosszuegig und fuer die andere
ein Kahlschlag — globale Latten sind damit konzeptionell ueberholt.

DREI LATTEN, DREI ZWECKE (die Semantik, gegen die dieses Modul geschrieben ist):
  (1) ERKENNEN bleibt UNGESIEBT. Wer vor dem Namens-Voting siebt, verliert
      Bestaetigungen (Messung 31.08.: ohne Siebe 41 % mehr). Dieses Modul wird
      auf dem Urteils-Pfad NICHT gefragt und liefert dafuer auch keine Latte.
  (2) ANZEIGE/MELDEN + VORRAT: die Kamera-Kalibrierwerte (det_min, guete_e_min,
      guete_t_min). Sie entscheiden, WELCHES Bild in Meldung/Anzeige geht und
      WAS in den Kalibrier-Vorrat kommt — existierte schon (.383), liegt im
      Guard-Block des Config-Stores und wird hier nur ZUSAMMENGEFASST gelesen.
  (3) KATALOG-AUFNAHME: eine eigene, strengere Latte je Kamera
      (katalog_e_min/katalog_t_min). Sie greift an ALLEN Uebernahme-Stellen in
      den Referenz-Katalog und ist der Grund, warum es dieses Modul gibt:
      der Deckungs-Vertrag braucht EINE Funktion (katalog_ok), nicht fuenf
      verstreute Vergleiche (QS-Ebenen-Regel K3).

ABLAGEORT (bewusst KEIN zweiter): alle Kamera-Werte liegen im schon
vorhandenen Guard-Block `live.guards.<kamera>` des Config-Stores. Damit gibt es
genau EINEN Schreibweg (core.livewache.live_speichern, samt Riegeln und Audit)
und EINE Normalisierung (guards_lesen). Ein Guard-Block ohne `enabled` ist
reine Kalibrierung — eine Kamera braucht keinen Live-Waechter, um kalibriert zu
werden (Etappe 3 speist den Vorrat auch aus dem Event-Weg).

MIGRATIONS-SEMANTIK (Bestandsschutz, ausdruecklich):
  * Die GLOBALEN Werte guete_empfinden_min/guete_t_min (.377) wirken WEITER
    GENAU DORT, wo sie schon wirkten: Lernlauf-Sieb, Gruppen-Flaeche,
    Pool-Zulauf. Sie werden hier NICHT umgebogen — eine Kamera-Latte, die
    ploetzlich den Lernlauf siebt, waere eine stille Verhaltensaenderung.
  * Fuer die ANZEIGE-Latte (2) gilt: Kamera-Wert gesetzt -> er gilt; nicht
    gesetzt -> KEINE Latte (None), exakt wie vor diesem Bau. Der globale Wert
    faellt hier bewusst NICHT ein: auf dem Live-Weg galt nie eine globale
    Latte, und die Messung 31.08. zeigt, dass die Werks-Latte an Fernmaterial
    das gesamte Namensmaterial verwirft (Guete-Werkslatte -> 0 Bestaetigungen).
    Was der globale Wert dort waere, ist deshalb als HINWEIS auf der Seite
    sichtbar, nicht als stille Wirkung.
  * Fuer die KATALOG-Latte (3) gilt: Kamera-Wert -> global (katalog_guete_*)
    -> nicht gesetzt = keine Latte. Ungemessene Bilder (fiqa_t/empf fehlen,
    Alt-Bestand oder Alt-Image ohne die Guete-Modelle) urteilen IMMER alt:
    eine Latte ohne Messgrundlage waere ein stiller Verlust (dieselbe Haltung
    wie core.benennung.guete_weg_aktiv).
  * Vorhandene Referenzen werden NIE rueckwirkend entfernt. Die Latte
    entscheidet ausschliesslich ueber NEUE Aufnahmen.

Dieses Modul rechnet nicht und misst nicht — es LIEST Werte und beantwortet
genau eine Frage (katalog_ok). Zahlen kommen aus der Config bzw. aus
core.guete.STARTWERTE, nie von hier (Haus-Regel, Muster norm_latte/REF_LATTE).
"""

# ---------------------------------------------------------------- Ablageort
# Die zwei Guard-Felder der Katalog-Latte. Sie stehen zusaetzlich in
# core.livewache.GUARD_USER_FELDER (dem Deckungs-Vertrag des Guard-Blocks) —
# hier als Namens-Quelle fuer Leser und Schreiber dieses Moduls, damit der
# Feldname nicht an vier Stellen als Literal steht.
KAT_FELDER = ("katalog_e_min", "katalog_t_min")

# Die drei Anzeige-/Vorrats-Felder (Latte 2) — schon vorhanden, hier nur
# benannt, damit die Seite sie ueber DIESE Quelle liest.
ANZ_FELDER = ("det_min", "guete_e_min", "guete_t_min")

# ---------------------------------------------------------------- Inventar
# DIE Liste der Stellen, an denen ein Bild in den Referenz-Katalog wandert
# ("modul:funktion"). Sie ist der Deckungs-Vertrag der Katalog-Latte: jede
# dieser Funktionen MUSS katalog_ok() fragen, und eine neue Uebernahme-Stelle
# muss hier eingetragen werden. Die Gate-Stufe "Katalog-Latte" prueft beides —
# Eintrag ohne Aufruf ist rot, und ein Fund am refs_meta-Schreibweg, der weder
# hier noch in AUSNAHMEN steht, ebenfalls (K3: erreicht die Erweiterung ALLE
# Stellen?).
UEBERNAHME_STELLEN = (
    "anlernen:benenne",                 # Pool -> Katalog (Today-Karte, Cluster-
    #                                     Anlernen, Unbekannt-Benennung; die
    #                                     Pool-Zeile traegt seit .380 camera +
    #                                     fiqa_t/empf, die Latte beisst hier real)
    "core.uebernahme:plan_bauen",       # Lernlauf-Anker -> Katalog (Mitglieder
    #                                     tragen kamera + fiqa_t/empf; der Plan
    #                                     ist die Stelle, an der ein Bild
    #                                     ausgesondert werden kann, BEVOR
    #                                     uebernehmen() Dateien anfasst)
    "anlernen:vorschlag_aufnehmen",     # Bestands-Vorschlag -> Katalog
    "anlernen:vorrat_aufnehmen",        # Vorrats-Angebot -> Katalog
    "verifyd:enroll_entscheiden",       # Enrollment-Kandidat -> Katalog
)

# Schreibwege auf refs_meta.jsonl, die KEINE Uebernahme sind (Begruendung je
# Zeile — eine Ausnahme ohne Grund waere ein Schlupfloch):
AUSNAHMEN = {
    "anlernen:entferne_referenz":
        "Tombstone: entfernt eine Referenz, nimmt keine auf",
    "verifyd:upload_referenz":
        "Foto-Upload durch den Nutzer: kein Kameramaterial, keine Kamera und "
        "keine Guete-Messung — eine Kamera-Latte hat hier keine Bedeutung "
        "(Haus-Entscheid 'Personen nie per Upload anlernen' betrifft den "
        "Bedienweg, der Upload selbst bleibt als bewusste Handtuer bestehen)",
    "verifyd:do_POST":
        "Lernlauf-Uebernahme: die Zeile wird geschrieben, NACHDEM "
        "core.uebernahme.plan_bauen gesiebt hat — der Filter sitzt dort",
    "sync_refs:meta_append":
        "Journal-Schreiber des Frigate-Abgleichs: haengt Export-/"
        "Wieder-anbieten-Zeilen zu Bildern an, die BEREITS im Katalog liegen — "
        "er nimmt nie eines auf",
}


# ---------------------------------------------------------------- Lesen
def _zahl(wert, lo=0.0, hi=1.0):
    """Eine optionale Latten-Zahl -> float oder None. Unbrauchbares wird zu
    None (= keine Latte), nie zu einem geratenen Wert: eine kaputte Zahl darf
    keine Bilder verwerfen."""
    if wert in (None, ""):
        return None
    try:
        z = float(wert)
    except (TypeError, ValueError):
        return None
    return z if lo <= z <= hi else None


def guards(cfg):
    """Die normalisierten Guard-Bloecke -> {kamera: block}. EINE Normalisierung
    (core.livewache.guards_lesen), kein zweiter Leser des Store-Blocks. Der Log
    ist hier bewusst stumm: dieselben Werte werden beim Engine-Start laut
    geprueft, und eine Kalibrier-Seite soll das Dienst-Log nicht doppelt
    fuellen."""
    from core import livewache as _lw          # lazy: dieses Modul bleibt leicht
    try:
        _d, g = _lw.guards_lesen(cfg, log=lambda *_a, **_k: None)
    except Exception:                                       # noqa: BLE001
        return {}
    return g


def anzeige_latte(cfg, kamera, guard=None):
    """Latte 2 (Anzeige/Melden/Vorrat) DIESER Kamera.
    -> {"det": float|None, "e": float|None, "t": float|None}
    None heisst "keine Latte" — exakt wie vor diesem Bau (Migrations-Semantik
    im Modulkopf). Der Aufrufer darf einen bereits gelesenen Guard-Block
    hereinreichen, damit die Uebersicht nicht je Kachel neu normalisiert."""
    g = guard if guard is not None else (guards(cfg).get(kamera) or {})
    return {"det": _zahl(g.get("det_min")),
            "e": _zahl(g.get("guete_e_min")),
            "t": _zahl(g.get("guete_t_min"))}


def global_latte(cfg):
    """Die GLOBALEN Guete-Werte (.377) — Fallback und Hinweis, nie stille
    Wirkung auf dem Live-Weg (Modulkopf). Sie sind zugleich die Latte, mit der
    Lernlauf-Sieb und Pool-Zulauf unveraendert weiterarbeiten."""
    return {"e": _zahl(cfg.get("guete_empfinden_min")),
            "t": _zahl(cfg.get("guete_t_min"))}


def katalog_start():
    """Werks-Vorgabe der KATALOG-Latte -> {"e", "t"}.

    BEWUSST KEINE neue Zahl: es sind die Werks-Startwerte der Guete-Eichung
    (core.guete.STARTWERTE, am Feldmaterial geeicht, Messtag 30.08.) — die
    NAH-/Lernlauf-Eichung. Genau daraus wird die "strengere" Latte: die
    KAMERA-Latte senkt der Nutzer, wenn seine Kamera Fernmaterial liefert
    (Feld-Eichpunkte 31.08.: 0,120/0,300 gegen Werk 0,200/0,400) — der Katalog
    macht diese Senkung NICHT mit. Wer eine Kamera-Latte ueber die Werks-Werte
    hebt, bekommt keinen strengeren Katalog geschenkt; die Seite sagt das
    ausdruecklich, statt heimlich das Maximum zu bilden."""
    from core import guete as _guete
    return {"e": float(_guete.STARTWERTE["empfinden"]),
            "t": float(_guete.STARTWERTE["t"])}


def katalog_latten(cfg):
    """Das REISE-FERTIGE Latten-Dict der Katalog-Aufnahme — der Aufrufer reicht
    es an die Uebernahme-Stellen weiter (Muster norm_latte/guete_latte: die
    Latte reist als fertiges Dict, der Verbraucher waehlt nie selbst
    Config-Schluessel aus).

    -> {"global": {"e", "t"}, "kameras": {name: {"e", "t"}}}

    BEWUSST je Aufruf frisch aus cfg gelesen (kein Env-Transport, keine
    Zwischenspeicherung): die Werte werden auf der Kalibrier-Seite geaendert
    und muessen SOFORT gelten — dieselbe Zusage wie bei den zwei
    .378-Schwellen ("wirkt live, kein Neustart")."""
    aus = {"global": {"e": _zahl(cfg.get("katalog_guete_e_min")),
                      "t": _zahl(cfg.get("katalog_guete_t_min"))},
           "kameras": {}}
    for name, g in (guards(cfg) or {}).items():
        e, t = _zahl(g.get("katalog_e_min")), _zahl(g.get("katalog_t_min"))
        if e is not None or t is not None:
            aus["kameras"][str(name)] = {"e": e, "t": t}
    return aus


def katalog_werte(latten, kamera):
    """Die WIRKSAME Katalog-Latte fuer eine Kamera -> {"e", "t", "quelle"}.
    quelle: 'kamera' | 'global' | 'aus'. Gemischt wird NICHT: hat die Kamera
    eigene Werte, gelten ihre (auch wenn nur einer gesetzt ist — der andere
    bleibt dann offen). Eine Halb-Mischung waere eine dritte, nirgends
    sichtbare Zahl."""
    l = latten or {}
    kam = (l.get("kameras") or {}).get(str(kamera or ""))
    if kam and (kam.get("e") is not None or kam.get("t") is not None):
        return {"e": kam.get("e"), "t": kam.get("t"), "quelle": "kamera"}
    gl = l.get("global") or {}
    if gl.get("e") is not None or gl.get("t") is not None:
        return {"e": gl.get("e"), "t": gl.get("t"), "quelle": "global"}
    return {"e": None, "t": None, "quelle": "aus"}


# ---------------------------------------------------------------- Uebersicht
def anzeige_start():
    """Werks-Vorgabe der ANZEIGE-Latte -> {"e","t"} (Quelle core.guete
    .ANZEIGE_STARTWERTE, User-Vorgabe 31.08. — Muster katalog_start)."""
    from core import guete as _guete
    return {"e": float(_guete.ANZEIGE_STARTWERTE["empfinden"]),
            "t": float(_guete.ANZEIGE_STARTWERTE["t"])}


def ist_subkamera(name):
    """Sub-/Zweitstrom-Kameras gehoeren nicht auf die Kalibrier-Uebersicht
    (User 31.08.: "cams die als sub sind ... gar nicht erst anzeigen").
    Erkennung am Namens-Baustein `_sub` (unterstrich-gebunden, z.B.
    Hof_CAM_sub_rec) — die Direkt-Adresse /kalibrierung/<name> bleibt
    erreichbar, nur die Uebersicht blendet aus."""
    n = str(name).lower()
    return "_sub_" in n or n.endswith("_sub")


def uebersicht_daten(cfg, kameras):
    """Der Stand ALLER Kameras fuer die zentrale Uebersichts-Seite.

    `kameras` kommt vom Aufrufer (verifyd.frigate_cameras) — hier wird NIE
    eine zweite Kameraliste gebaut (Deckungs-Regel). Kameras, die nur noch im
    Store stehen (aus Frigate entfernt, aber kalibriert), kommen HINTEN dazu
    und sind als solche markiert: ihre Werte still verschwinden zu lassen
    waere ein Verlust ohne Ansage.

    -> [{name, in_frigate, vorrat_n, vorrat_ts, det, e, t, eigene,
         kat_e, kat_t, kat_quelle}]"""
    from core import livewache as _lw
    g_alle = guards(cfg)
    latten = katalog_latten(cfg)
    namen = [str(k) for k in (kameras or []) if not ist_subkamera(k)]
    bekannt = set(namen)
    extra = sorted(n for n in g_alle
                   if n not in bekannt and not ist_subkamera(n))
    aus = []
    for name in namen + extra:
        g = g_alle.get(name) or {}
        anz = anzeige_latte(cfg, name, guard=g)
        kat = katalog_werte(latten, name)
        vorrat = _lw.kalib_lesen(cfg, name)
        aus.append({
            "name": name,
            "in_frigate": name in bekannt,
            "vorrat_n": len(vorrat),
            # Der juengste Eintrag des Rings = "zuletzt aktualisiert". Aus den
            # Daten gerechnet, nicht aus einer Datei-mtime: der Ring wird beim
            # Kappen neu geschrieben, die mtime waere dann eine Luege.
            "vorrat_ts": max((e["ts"] for e in vorrat), default=0.0),
            "det": anz["det"], "e": anz["e"], "t": anz["t"],
            # "eigene": traegt diese Kamera ueberhaupt einen eigenen Wert?
            # Genau die Frage, die die Kachel beantworten muss — sonst sieht
            # der Nutzer drei Zahlen und weiss nicht, ob sie IHM gehoeren.
            "eigene": any(v is not None for v in
                          (anz["det"], anz["e"], anz["t"])),
            "kat_e": kat["e"], "kat_t": kat["t"], "kat_quelle": kat["quelle"]})
    return aus


# ---------------------------------------------------------------- Das Urteil
def katalog_ok(latten, kamera, empf, fiqa_t):
    """DIE eine Frage aller Uebernahme-Stellen: darf dieses Bild in den
    Referenz-Katalog? -> (ok, grund).

    grund ist None, wenn ok — sonst ein kurzer, ehrlicher Satz MIT ZAHLEN
    (der Nutzer sieht ihn in der Uebersprungen-Liste; "abgelehnt" ohne Wert
    waere nicht nachvollziehbar).

    DURCHLASSEN ist der Rueckfall in JEDEM Zweifelsfall:
      * latten fehlt/leer            -> durch (Latte aus, Alt-Verhalten)
      * keine Latte fuer die Kamera  -> durch
      * empf/fiqa_t nicht gemessen   -> durch ("ungemessene Bilder urteilen
        alt" — Alt-Bestand, Alt-Image ohne die Guete-Modelle, Messfehler)
    Gesperrt wird nur, was GEMESSEN unter einer GESETZTEN Latte liegt."""
    w = katalog_werte(latten, kamera)
    if w["quelle"] == "aus":
        return True, None
    if empf is None or fiqa_t is None:
        return True, None
    try:
        e_ist, t_ist = float(empf), float(fiqa_t)
    except (TypeError, ValueError):
        return True, None
    if w["e"] is not None and e_ist < float(w["e"]):
        return False, (f"below the catalogue bar for picture impression "
                       f"({e_ist:.3f} < {float(w['e']):.3f})")
    if w["t"] is not None and t_ist < float(w["t"]):
        return False, (f"below the catalogue bar for recognisability "
                       f"({t_ist:.3f} < {float(w['t']):.3f})")
    return True, None
