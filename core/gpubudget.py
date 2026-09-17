"""core/gpubudget — was die Beschleuniger-Karte traegt, in ZWEI Groessen.

Warum zwei und nicht eine (gemessen 04.09.2026, Konzept `konzept_broker_phase2.md` §P5):
Analyse-Worker und Live-Waechter belasten die Karte VERSCHIEDEN, und wer nur eine
Zahl anzeigt, verspricht dem Nutzer etwas Falsches.

  * SPEICHER (VRAM) verbrauchen BEIDE, ungefaehr in derselben Groessenordnung.
    Je Analyse-Worker 1,2-1,4 GB (eigener Prozess, eigene Modell-Sitzung, gemessen
    ueber `nvidia-smi --query-compute-apps` je Prozess). Live-Waechter teilen sich
    EINEN Prozess: der erste zahlt die Modelle (~1,5 GB), jeder weitere rund 0,7 GB.
  * RECHENZEIT verbrauchen praktisch nur die WAECHTER, und zwar dauerhaft: sie
    dekodieren ihren Stream, ob jemand da ist oder nicht. Feldmessung an 6 Kameras
    (Feldtester-Anlage, dort in der Config als `messung.gpu_budget_anteil` hinterlegt):
    Median 8 %, Spanne 7-36 % je Waechter. Die Analyse dagegen rechnet in Schueben.

Die zweite Groesse ist nicht Zierde: fuenf Waechter koennen die halbe Karte binden,
ohne nennenswert Speicher zu belegen — und umgekehrt kann der Speicher voll sein,
waehrend die Karte Langeweile hat. Welche der beiden Waende zuerst kommt, haengt an
der Karte und am Betrieb; deshalb zeigt die Oberflaeche beide.

ALLE ZAHLEN HIER SIND MESSWERTE MIT STREUUNG, keine Zusagen. Die Waechter-Werte
stammen aus 3 Messpunkten (531-864 MB Zuwachs); wir rechnen mit dem Mittel und
sagen es an der Oberflaeche auch so. Wer sie aendert, misst neu und schreibt den
Messweg dazu.
"""

# --- gemessen 04.09.2026, RTX 2060 Mobile (CUDA), je Prozess ueber nvidia-smi ---
VRAM_JE_WORKER_MB = 1300        # Analyse-Worker: 1200-1400 gemessen, linear
VRAM_ERSTER_WAECHTER_MB = 1500  # erster Live-Waechter, traegt die Modelle
VRAM_JE_WEITEREM_WAECHTER_MB = 700   # jeder weitere (gemessen 531 und 864)
VRAM_DIENST_MB = 1144           # der Dienstprozess selbst
# .531 NACHGEMESSEN (15.09.2026): der Dienstprozess haelt auf der Karte deutlich
# mehr als die 92 MiB, die am 04.09. je PID abgelesen wurden — im Ruhelauf 614
# MiB (vram_proben_20260915/ergebnis.md §1, Laeufe B2/D2/C3) und UNTER LAST bis
# 1144 MiB (NB-Abnahme .531, Schritt (a)/(d1) am 15.09.: der Dienst waechst,
# waehrend die Analyse laeuft). Geplant wird mit der oberen Kante — dieselbe
# Hausregel wie bei DECODER_CUDA_MB, und hier besonders wichtig: diese Zahl gilt
# nur noch fuer den GERECHNETEN Zweig, also fuer den Fall, in dem die Karte gar
# nicht messbar ist. Dort soll sie vorsichtig sein.
# WO ER GILT UND WO NICHT (Korrektur vom 15.09., nachgerechnet): auf der
# GERECHNETEN Seite (aus `gesamt`) geht er ab, denn dort ist nichts gemessen, was
# ihn schon enthielte. Vom GEMESSENEN `frei` geht er NICHT ab — der Dienst startet
# den Worker, er liegt zur Messzeit also zwangslaeufig schon auf der Karte, und
# ein zweiter Abzug waere derselbe Speicher zweimal. Der Preis dieses Fehlers war
# beziffert: er haette der 6-GB-Karte ohne Waechter einen Strang genommen, der am
# 14.09. sauber durchlief (Kartenspitze 5332 von 6144).

# --- gemessen 05.09.2026, RTX 2060 Mobile, .506 (Feature-Norm auf CUDA) ---
# Ein Analyse-Worker traegt seit .506 neben dem Embedder eine CUDA-Norm-Session:
# 1236 MiB gemessen (Embedder allein 1172) — bleibt unter VRAM_JE_WORKER_MB, weil der
# CUDA-Kontext im Prozess schon steht. Ein FREMDER Prozess ohne Kontext (der
# Vorschlaege-/anlernen-Subprozess baut seine eigene warme NormMass) zahlt dagegen
# Kontext + 249-MB-Modell = 620 MiB als ERSTE Session. Das ist der Posten, der auf
# einer 6-GB-Karte mit drei Workern (gemessene Spitze 5501 MiB) nicht mehr passt —
# deshalb fest reserviert, sobald mindestens ein Worker geplant ist (Widerleger
# W-Norm B1, 05.09.2026). Je Backend: auf cuda ein echter VRAM-Posten; auf
# openvino (Intel) ist es geteilter Systemspeicher und hier nur eine
# Sicherheitsmarge; auf cpu und migraphx laeuft die Norm auf der CPU, dort ist der
# Posten null, die Reserve bleibt als Marge stehen (Deckungs-Vertrag: alle vier kinds).
VRAM_NORM_FREMDPROZESS_MB = 620

# --- Feldmessung an der Feldtester-Anlage, 6 Kameras (config live.guards[*].messung) ---
RECHEN_JE_WAECHTER = 0.08       # Median-Anteil am GPU-Budget je Waechter
RECHEN_JE_WAECHTER_MAX = 0.36   # belebte Kamera, gemessene Obergrenze

# --- Reserve (User-Entscheid 04.09.): 15 %, mindestens 1 GB ---
# Sie ist NICHT vergebbar. Grund ist nicht Vorsicht um ihrer selbst willen: auf der
# Karte liegen ausser uns die Anzeige-Transcodes, und bei manchem Nutzer noch ein
# zweiter Verbraucher (Frigate). Wer bis aufs letzte Byte plant, laesst den
# Kernel-OOM-Killer entscheiden, welcher Prozess stirbt — und der fragt nicht.
RESERVE_ANTEIL = 0.15
RESERVE_MIN_MB = 1024


def reserve_mb(gesamt_mb):
    """Nicht vergebbarer Anteil des Kartenspeichers."""
    if not gesamt_mb or gesamt_mb <= 0:
        return 0
    return int(max(RESERVE_MIN_MB, round(gesamt_mb * RESERVE_ANTEIL)))


def vram_waechter_mb(n):
    """Speicherbedarf von n Live-Waechtern. NICHT linear: der erste traegt die
    Modelle, die weiteren teilen sie sich."""
    n = max(0, int(n or 0))
    if n == 0:
        return 0
    return VRAM_ERSTER_WAECHTER_MB + (n - 1) * VRAM_JE_WEITEREM_WAECHTER_MB


def vram_worker_mb(n):
    """Speicherbedarf von n Analyse-Workern. Linear — jeder ist ein eigener
    Prozess mit eigener Modell-Sitzung."""
    return max(0, int(n or 0)) * VRAM_JE_WORKER_MB


def rechenlast(n_waechter):
    """-> (median_anteil, max_anteil) der Karte, die n Waechter dauerhaft binden."""
    n = max(0, int(n_waechter or 0))
    return (n * RECHEN_JE_WAECHTER, n * RECHEN_JE_WAECHTER_MAX)


def budget(gesamt_mb, n_worker, n_waechter):
    """Die ganze Rechnung fuer die Oberflaeche — rein, ohne Seiteneffekt.

    -> dict mit beiden Groessen. `passt` ist die einzige Ja/Nein-Aussage der Seite:
    True heisst, die geplante Aufteilung bleibt unter der Reserve UND unter 100 %
    Rechenzeit im Median-Fall.
    """
    gesamt = int(gesamt_mb or 0)
    res = reserve_mb(gesamt)
    w = vram_worker_mb(n_worker)
    g = vram_waechter_mb(n_waechter)
    nf = VRAM_NORM_FREMDPROZESS_MB if n_worker else 0        # .506: Norm-Session des Vorschlaege-Prozesses
    belegt = w + g + nf + (VRAM_DIENST_MB if (n_worker or n_waechter) else 0)
    frei = gesamt - res - belegt
    med, hoch = rechenlast(n_waechter)
    return {
        "gesamt_mb": gesamt,
        "reserve_mb": res,
        "worker_mb": w,
        "waechter_mb": g,
        "norm_fremd_mb": nf,
        "dienst_mb": VRAM_DIENST_MB if (n_worker or n_waechter) else 0,
        "belegt_mb": belegt,
        "frei_mb": frei,
        "speicher_anteil": (belegt / (gesamt - res)) if gesamt - res > 0 else 0.0,
        "rechen_median": med,
        "rechen_max": hoch,
        "passt": frei >= 0 and med < 1.0,
        # Welche Wand kommt zuerst? Das ist die eigentliche Auskunft der Seite —
        # sie ist je Karte und Betrieb verschieden, deshalb wird sie ausgerechnet
        # und nicht behauptet.
        "engpass": ("speicher" if frei < 0 else
                    "rechenzeit" if med >= 1.0 else
                    "speicher" if gesamt - res > 0
                    and belegt / (gesamt - res) > med else "rechenzeit"),
    }


def vorschlag_geklemmt(vorschlag, gesamt_mb, n_waechter):
    """Der Hardware-Vorschlag, begrenzt durch den vorhandenen Speicher.

    Warum das noetig ist (User 04.09. an der Seite gesehen): der reine Messwert sagt
    „auf CUDA sind 3 Plaetze am schnellsten". Auf einer 6-GB-Karte mit zwei Waechtern
    passen aber nur zwei. Die Seite riet damit zu etwas, das sie im selben Atemzug
    ausschloss — zwei richtige Saetze, die zusammen eine Sackgasse ergeben. Der
    Vorschlag ist deshalb IMMER der kleinere von beiden, und die Oberflaeche sagt,
    welche der beiden Grenzen gerade zieht."""
    passt = max(1, int(gesamt_mb and
                       (gesamt_mb - reserve_mb(gesamt_mb)
                        - vram_waechter_mb(n_waechter) - VRAM_DIENST_MB
                        - VRAM_NORM_FREMDPROZESS_MB)               # .506, s. Konstante
                       // VRAM_JE_WORKER_MB or 1))
    return min(int(vorschlag or 1), passt), passt


def worker_noch_moeglich(gesamt_mb, n_waechter, n_worker_jetzt=0):
    """Wie viele Analyse-Worker passen bei dieser Waechterzahl noch dazu?
    Fuer den Vorschlag an der Oberflaeche und fuer Support-Antworten."""
    gesamt = int(gesamt_mb or 0)
    rest = (gesamt - reserve_mb(gesamt) - vram_waechter_mb(n_waechter) - VRAM_DIENST_MB
            - VRAM_NORM_FREMDPROZESS_MB)                          # .506, s. Konstante
    return max(0, int(rest // VRAM_JE_WORKER_MB) - max(0, int(n_worker_jetzt or 0)))


# ============================================================================
# E3.2 (14.09.2026) — DIE THREAD-FORMEL. Ab hier geht es nicht mehr um Prozesse.
# ============================================================================
# Alles oberhalb dieser Linie beschreibt die ALTE Bauart: ein Analyse-PROZESS je
# Platz, jeder mit eigenem Kontext und eigener Modell-Sitzung (VRAM_JE_WORKER_MB
# = 1300, linear). Seit E3.1 traegt EIN langlebiger worker_dienst N RECHENSTRAENGE
# in EINEM Prozess — ein Kontext, ein Kompilat-Satz, ein Speicher-Konto. Die
# Zahlen der alten Bauart gelten fuer die neue NICHT (W2-B16: 4 Prozesse sind
# nicht 4 Threads; der Versuch, sie gleichzusetzen, hat den OOM reproduziert).
#
# Die Formel, User-Auflage 13.09. (worker_neubau.md §2), Posten fuer Posten:
#
#     Fussabdruck(N, G) = BASIS + G x GEOMETRIE + N x STRANG + A x DECODER
#                         + WAECHTER-POSTEN                       (A <= N)
#
#   BASIS      was steht, bevor der erste Strang rechnet (Kontext + Modelle).
#   GEOMETRIE  je ZUSAETZLICHER Aufloesung ueber die hinaus, die in den Ankern
#              unten schon stecken (der gt5-Mix traegt 1080p UND 4K).
#   STRANG     der Grenzpreis eines weiteren Rechenstrangs, OHNE seinen Decoder.
#   DECODER    das ffmpeg je AKTIVEM Job — der Posten, den die Auflage
#              ausdruecklich explizit sehen will (v4 mass 330/660/990 MiB bei
#              1/2/3 Straengen, also sauber linear je laufendem Job).
#   WAECHTER   die Live-Wache auf derselben Karte. Seit dem Live-Stoertest vom
#              14.09. Pflichtteil und nicht laenger Kulanz: auf der 6-GB-Karte
#              sind neben zwei Waechtern 2 Straenge ein sicherer OOM (Beleg
#              unten), 1 Strang laeuft mit Luft.
#
# DIE RECHENGROESSE IST DIE DAUERLAST-SPITZE, NICHT DER 5er-LAUF (W2-B14). Der
# Unterschied ist gemessen und betraegt auf CUDA 1070 MiB: derselbe 2-Strang-Lauf
# kommt ueber 5 Ereignisse auf 4262 MiB und ueber 30 Jobs auf 5332 MiB. Wer mit
# dem kurzen Lauf plant, plant eine Karte voll, die im Dauerbetrieb ueberlaeuft.
#
# ALLE STUETZWERTE SIND MESSWERTE MIT FUNDSTELLE. Erfundene, geschaetzte oder
# aus einer anderen Modell-Generation herueberkopierte Zahlen haben hier nichts
# verloren; wer einen Wert aendert, misst neu und schreibt den Messweg dazu.

# --- CUDA: RTX 2060 Mobile 6 GB, gemessen 12.-14.09.2026 --------------------
# Anker (14.09., nvidia-smi-Abtaster je 0,23 s, Spalte memory.used, Maximum;
# Belegort .suslik_tmp/gt5/runs/schlusszug_20260914/nb_cuda/<lauf>/abtaster.log):
#     1 Strang,  5 Ereignisse   2594 MiB   (d_bas_1t_a, d_fix_1t_a; d_fix_1t_b 2591)
#     2 Straenge, 5 Ereignisse  4262 MiB   (d_fix_5_b1)
#     2 Straenge, 30 Jobs       5332 MiB   (d_v8_30_a)  <- DAUERLAST-SPITZE
#                               4598 MiB   (d_fix_30_b, derselbe Lauf mit dem
#                                          f32-Fix; geplant wird mit dem groesseren)
# Daraus, ohne weitere Annahme:
#     Grenzpreis Strang+Decoder = 4262 - 2594 = 1668 MiB
#     Dauerlast-Zuwachs je Strang = (5332 - 4262) / 2 = 535 MiB
#     BASIS = 2594 - 1310 - 358 = 926 MiB
# Der so bestimmte Strang-Preis (1310 MiB ohne Decoder) liegt im UNABHAENGIG
# gemessenen Band 1040-1470 MiB (v4-Messreihe 12.09., stand.md: Spitzen
# 2768/4352/5737 MiB bei 1/2/3 Straengen) — zwei Messwege, ein Ergebnis.
STRANG_CUDA_MB = 1310            # Grenzpreis je Rechenstrang, OHNE ffmpeg
STRANG_DAUERLAST_CUDA_MB = 535   # was ein Strang im DAUERLAUF zusaetzlich zieht
DECODER_CUDA_MB = 358            # je aktivem Job-ffmpeg; gemessenes Band 330-358,
#                                  hier die obere Kante (v4: 330/660/990 linear)
BASIS_CUDA_MB = 926              # Rest des 1T-Ankers nach Strang und Decoder
GEOMETRIE_CUDA_MB = 700          # je ZUSAETZLICHER Aufloesung (v5-Messung 12.09.:
#                                  Zweitgeometrie ~700 statt vorher ~1600 MiB)

# --- Live-Waechter auf CUDA, gemessen 14.09.2026 ---------------------------
# Belegort .suslik_tmp/gt5/runs/live_stoertest_cuda_20260914/ (2 Waechter,
# nativ 4K, NVDEC): Kartenbelegung im Ruhezustand Median 2182 MiB, aufgeteilt in
# Live-Engine 1434-1468 MiB (sie traegt die Modelle EINMAL fuer alle Waechter)
# + je Waechter ein ffmpeg/NVDEC mit 330 MiB + Dienstprozess 92 MiB.
WAECHTER_ENGINE_CUDA_MB = 1434   # die Engine, einmal
WAECHTER_DECODER_CUDA_MB = 330   # je Waechter ein NVDEC-ffmpeg

# --- Intel (openvino): der Fussabdruck ist SYSTEMSPEICHER, nicht VRAM -------
# Gemessen wird deshalb anon + cgroup-shmem (worker_dienst.fussabdruck_mb) und
# NIE VmRSS: die i915-Objekte der iGPU haengen an shmem und fehlen im RSS
# (12.09. gemessen 1,9 GB RSS gegen 6,85 GB cgroup).
# Anker:
#     1 Strang    3,41 GiB = 3492 MB   (v7-Messung 12.09., worker_neubau.md §2)
#     2 Straenge  3,94-4,97 GiB        (v7/v8-Klasse; geplant wird mit der OBEREN
#                                       Kante 4,97 GiB = 5120 MB)
# Gegenprobe am Feld-nahen Lauf (14.09., live_stoertest_intel_20260914/proben/
# probe.csv, Spalte last_fuss): der Dauerlast-Container mit 2 Straengen kam auf
# 4386 MB — die Planung liegt also 17 % darueber, bewusst.
# Beide Anker sind DAUERLAST-Messungen (8 Runden a 30 Jobs), deshalb gibt es hier
# keinen gesonderten Dauerlast-Zuschlag wie auf CUDA.
STRANG_OV_MB = 1553              # (5120 - 3492) - DECODER_OV_MB
DECODER_OV_MB = 75               # Decoder-Puffer je Strang (W2-B30: VORLAUF-
#                                  Queue + Pipe, ~75 MB) — der ffmpeg-Posten
#                                  der RAM-Seite
BASIS_OV_MB = 1864               # 3492 - STRANG - DECODER
GEOMETRIE_OV_MB = 700            # UEBERNOMMEN von CUDA, auf Intel NICHT getrennt
#                                  gemessen. Ehrlich als solcher gekennzeichnet:
#                                  er wird nur fuer ZUSAETZLICHE Aufloesungen
#                                  faellig, die Anker tragen den Mix schon.

# --- Der Dienstprozess selbst (er liegt im selben Speicher-Konto) ----------
# CUDA: 92 MiB VRAM gemessen (14.09.) -> es gilt VRAM_DIENST_MB (100), eine Quelle.
# Intel: verifyd selbst, gemessen 14.09. am Prod-Container (anon+shmem):
#   761 MB im Leerlauf, 1926 MB unter Nachbarlast. Geplant wird mit dem groesseren
#   (probe.csv, Phase LAST_OHNE_WAECHTER) — auf Intel teilt sich der Worker die
#   cgroup mit dem Dienst, der Posten ist also wirklich abzuziehen.
DIENST_OV_MB = 1926

# --- Live-Waechter auf Intel, gemessen 14.09.2026 --------------------------
# Beim Einschalten von EINEM Waechter (4K, VAAPI) stieg der Prod-Fussabdruck von
# 1926 MB auf 4348 MB (fortschritt_live_intel.md, Schritt 3). Differenz = 2422 MB.
# EHRLICHE GRENZE: nur n=1 gemessen. Weitere Waechter werden deshalb LINEAR
# fortgeschrieben — das ist die konservative Richtung (auf CUDA kostet jeder
# weitere Waechter nur seinen Decoder, auf Intel ist das unbelegt).
WAECHTER_OV_MB = 2422

# --- Reserve der Strang-Formel (NICHT die Reserve der Seite) ---------------
# Warum eine eigene: die 15 %/1 GB oben sind eine PLANUNGS-Marge fuer eine
# Empfehlung an den Nutzer und standen dabei auch fuer Nachbarn, die diese Formel
# jetzt EXPLIZIT abzieht (Live-Waechter, Dienstprozess). Vor allem aber
# widerspraechen sie der Messung: der 2-Strang-Dauerlauf auf der 6-GB-Karte lief
# am 14.09. sauber durch (30/30 Jobs, rc=0) mit einer Kartenspitze von 5332 von
# 6144 MiB — 812 MiB blieben frei. Eine Politik, die genau diesen GEMESSENEN
# Betriebspunkt verbietet, ist nicht vorsichtig, sondern falsch. 10 % lassen auf
# der 6-GB-Karte 614 MiB stehen, also ungefaehr die real gemessene Luft.
RESERVE_STRANG_ANTEIL = 0.10
RESERVE_STRANG_MIN_MB = 512

# --- Marge der Speicher-WACHE ----------------------------------------------
# Die Politik-Grenze, die der Dienst als `fussabdruck_max_mb` mitbekommt, ist
# NICHT die Vorhersage selbst: die Wache soll ein LECK fangen, nicht die normale
# Streuung. Gemessene Bezugspunkte vom 14.09. auf Intel (probe.csv; in Prod
# liegen Dienst, Waechter und Straenge in DERSELBEN cgroup, deshalb werden die
# beiden getrennt gemessenen Konten hier addiert):
#   ohne Waechter   1926 (Dienst) + 4386 (2 Straenge) =  6312 MB gemessen,
#                   Formel 1926 + 5120 = 7046 MB (+11,6 %), Grenze 8808 MB
#   mit 1 Waechter  4714 + 3921 = 8635 MB gemessen (die Tagesspitze),
#                   Formel 1926 + 2422 + 5120 = 9468 MB (+9,6 %), Grenze 11835 MB
# Eine Marge von 15 % laege im ersten Fall nur 795 MB ueber der gemessenen
# Spitze — das riefe die Wache im Normalbetrieb. 25 % lassen dort rund 2,5 GB
# Luft und fangen trotzdem jedes echte Weglaufen.
WACHE_MARGE_ANTEIL = 0.25

# --- CONTAINER-RAM auf Backends OHNE RAM-Messung (.528, gemessen 14.09.2026) --
# WOZU DIESE POSTEN UEBERHAUPT DA SIND, und was ohne sie passiert ist:
# die Speicher-Wache des Dienstes misst anon + cgroup-shmem des GANZEN
# CONTAINERS (worker_dienst.fussabdruck_mb) — Dienst, Live-Engine, Waechter-
# ffmpegs und der Worker zusammen. Auf Intel rechnet die Formel oben genau diese
# Groesse, dort kommt die Grenze aus ihr. Auf CUDA rechnet sie KARTENSPEICHER;
# fuer den RAM desselben Prozesses hatte sie bis .527 nichts zu sagen und gab
# ersatzweise die KONFIGURIERTE `worker_rss_max_mb` weiter (Default 4096,
# geeicht auf VmRSS EINES Workers). Eine Je-Worker-Zahl gegen ein Container-Mass:
# genau die Uebertragung, die der Kopfkommentar von worker_dienst.SpeicherWache
# ausdruecklich verbietet — und sie ist am 14.09. auf dem CUDA-Notebook
# eingetreten. Der Container trug OHNE Worker schon 3310 MB, der Geometriebau
# eines 4K-Clips kam auf 5108 MB, die Grenze stand bei 4096: die Wache schoss den
# Worker im Catch-up-Takt alle 600 s geordnet ab (tode_24h=2, je 56 offene Jobs
# als fremdverschuldet gebucht), ohne dass irgendetwas leckte.
# Belegort: .suslik_tmp/gt5/runs/abnahme_nb_527_20260914/ — fortschritt.md und
# nb/ps_container_end.txt (Endzustand: 2 Waechter aktiv, Worker tot).
#
#   Live-Engine (core.livewached, traegt die Modelle einmal)  2293428 KiB
#   Dienstprozess (verifyd.py)                                1026012 KiB
#   nvdec-ffmpeg je Waechter                          587088 / 523272 KiB
#   cgroup zum selben Zeitpunkt: anon 3470 + shmem 44 = 3514 MB (das Mass
#   der Wache; die ps-Summe liegt darueber, weil RSS geteilte Seiten doppelt
#   zaehlt — die Posten sind also die vorsichtigere Seite).
#
# EINHEIT, ehrlich benannt: ps meldet RSS in KiB, die Wache rechnet
# Bytes // 1048576 (MiB). Die Zahlen hier sind KiB/1000, also DURCHWEG die
# groessere Lesart (2293 statt 2240 MiB, 1026 statt 1002, 587 statt 573). Bei
# einer Grenze, deren Fehler in der einen Richtung den Worker abschiesst und in
# der anderen nur ein Leck spaeter faengt, ist das die richtige Richtung.
# Der ffmpeg-Posten ist die OBERE der beiden gemessenen Kanten (587 gegen 523),
# gleiche Regel wie bei DECODER_CUDA_MB.
_RAM_POSTEN_CUDA = {
    "dienst_mb": 1026,
    "waechter_engine_mb": 2293,
    "waechter_decoder_mb": 587,
    "beleg": "RTX 2060 Mobile Notebook, 14.09.2026, "
             "abnahme_nb_527_20260914/nb/ps_container_end.txt",
}

# DECKUNGS-VERTRAG wie bei STUETZWERTE: je Backend-kind der Registry genau ein
# Eintrag. `None` heisst „dieses Backend braucht hier nichts" und ist eine
# Aussage, kein Loch — openvino rechnet die Formel oben selbst in RAM.
# cpu und migraphx UEBERNEHMEN die CUDA-Posten; getrennt gemessen ist das nicht,
# und das steht hier so. Die Richtung ist auch hier die vorsichtige: ohne NVDEC
# ist der Waechter-Decoder auf diesen Wegen eher kleiner, die Grenze also eher
# zu weit als zu eng. Eine zu weite Grenze kostet nichts ausser Zeit bis zum
# Fang — eine zu enge kostet Analysen (s. o.).
CONTAINER_RAM_POSTEN = {
    "cuda": _RAM_POSTEN_CUDA,
    "cpu": _RAM_POSTEN_CUDA,          # uebernommen, nicht getrennt gemessen
    "migraphx": _RAM_POSTEN_CUDA,     # uebernommen, nicht getrennt gemessen
    "openvino": None,                 # mass == "ram": die Formel rechnet selbst
}

# DECKUNGS-VERTRAG (qs_ebenen.md: fachliche Aufzaehlungen kommen aus der EINEN
# Quelle oder tragen einen Vertrag): je Backend-kind der Registry genau ein
# Eintrag. `None` heisst AUSDRUECKLICH "fuer dieses Backend gibt es keine
# Messung" — das ist eine Aussage, kein Loch, und die Formel sagt es dann laut.
# Waechst die Registry um ein kind, faellt die Gate-Probe auf, statt dass das
# neue Backend still in einen Vorgabewert rutscht.
STUETZWERTE = {
    "cuda": {
        "mass": "vram",
        "basis_mb": BASIS_CUDA_MB,
        "geometrie_mb": GEOMETRIE_CUDA_MB,
        "strang_mb": STRANG_CUDA_MB,
        "strang_dauerlast_mb": STRANG_DAUERLAST_CUDA_MB,
        "decoder_mb": DECODER_CUDA_MB,
        "dienst_mb": VRAM_DIENST_MB,
        "waechter_engine_mb": WAECHTER_ENGINE_CUDA_MB,
        "waechter_decoder_mb": WAECHTER_DECODER_CUDA_MB,
        "beleg": "RTX 2060 Mobile, 14.09.2026, nb_cuda/*/abtaster.log",
    },
    "openvino": {
        "mass": "ram",
        "basis_mb": BASIS_OV_MB,
        "geometrie_mb": GEOMETRIE_OV_MB,
        "strang_mb": STRANG_OV_MB,
        "strang_dauerlast_mb": 0,       # Anker sind bereits Dauerlast
        "decoder_mb": DECODER_OV_MB,
        "dienst_mb": DIENST_OV_MB,
        "waechter_engine_mb": 0,        # auf Intel nicht aufgeteilt messbar
        "waechter_decoder_mb": WAECHTER_OV_MB,   # je Waechter, linear (s. o.)
        "beleg": "Intel Core Ultra 9 285H iGPU, 14.09.2026, "
                 "live_stoertest_intel_20260914/proben/probe.csv",
    },
    # UNGEMESSEN, und das bleibt sichtbar: der neue Worker ist auf diesen beiden
    # Wegen noch nicht gebaut (E4 cpu, E6 migraphx). Eine geratene Zahl waere hier
    # schlimmer als keine — die Formel faellt auf den gemessenen Durchsatz-Wert
    # zurueck und sagt den Grund.
    "cpu": None,
    "migraphx": None,
}

# BACKENDS MIT EIGENEM GERAETESPEICHER, ABER OHNE DURCHSETZBAREN DECKEL (E6,
# 17.09.2026). Sie bekommen OHNE Messung genau EINEN Rechenstrang statt des
# Durchsatz-Vorschlags — die vorsichtige Richtung, dieselbe wie `_fail_closed`.
#
# Warum migraphx hier steht, belegt statt vermutet: die Provider-Optionen
# `migraphx_mem_limit` und `migraphx_arena_extend_strategy` gibt es zwar, sie
# werden in onnxruntime 1.27.1 aber NICHT ausgewertet — `mem_limit_` und
# `arena_extend_strategy_` setzt der EP-Konstruktor nicht aus `info`
# (migraphx_execution_provider.h:129-130, .cc:233-234), und
# `CreatePreferredAllocators` baut die Arena mit `AllocatorCreationInfo(factory,
# id)`, also Vorgabe `use_arena=true` und `arena_cfg = {0,-1,-1,-1,-1,-1}` ohne
# Deckel (allocator_utils.h:17-35). Der .531-Kartenhaushalt hat auf diesem EP
# damit keine Entsprechung: Es gibt nichts, wogegen eine Leiter planen koennte.
# Beobachtet wird der Speicher statt dessen ueber sysfs
# (engine_migraphx.SysfsSpeicher, eine Zeile je Ereignis).
# cpu steht ausdruecklich NICHT hier: dort gibt es keinen Geraetespeicher, und der
# Durchsatz-Vorschlag ist der richtige Rueckfall.
OHNE_DECKEL = {
    "migraphx": ("the MIGraphX execution provider has no enforceable memory cap "
                 "(migraphx_mem_limit is not evaluated in onnxruntime 1.27.1) and "
                 "no memory measurements exist for it yet — the worker plans for "
                 "ONE compute thread. Set worker_straenge if you measured that "
                 "your card carries more; the card-memory lines in the worker "
                 "log (vram/gtt from sysfs) are the number to watch"),
}


def stuetzwerte(kind):
    """-> Stuetzwerte dieses Backends oder None, wenn es keine Messung gibt."""
    return STUETZWERTE.get(str(kind or ""))


def reserve_strang_mb(gesamt_mb, wunsch=-1):
    """Nicht vergebbarer Anteil fuer die Strang-Formel (s. RESERVE_STRANG_*).
    -> int, oder (int, quelle) wenn `wunsch` gesetzt ist? NEIN — immer int;
    WOHER die Zahl kommt, sagt `reserve_quelle_mb`. Zwei Rueckgabearten aus
    einer Funktion waeren die Art Falle, die spaeter jemand uebersieht.

    `wunsch` ist der Config-Wert `worker_vram_reserve_mb` (.534): -1 (oder
    kleiner) heisst Automatik nach Formel wie bisher, 0 ist erlaubt und
    heisst „keine Reserve", und nach oben wird gegen die Karte geklemmt —
    eine Reserve, die groesser ist als die Karte, liesse keinen Strang mehr
    uebrig und waere eine Zahl, die sich selbst widerspricht."""
    if not gesamt_mb or gesamt_mb <= 0:
        return 0
    w = int(wunsch if wunsch is not None else -1)
    if w >= 0:
        return max(0, min(w, int(gesamt_mb)))
    return int(max(RESERVE_STRANG_MIN_MB, round(gesamt_mb * RESERVE_STRANG_ANTEIL)))


def reserve_quelle_mb(wunsch=-1):
    """Woher die Reserve kommt: "config" oder "formel". -> str"""
    return "config" if int(wunsch if wunsch is not None else -1) >= 0 else "formel"


def waechter_posten_mb(n_waechter, kind="cuda"):
    """Was N Live-Waechter auf diesem Backend dauerhaft belegen.

    CUDA: die Engine traegt die Modelle einmal, jeder Waechter sein eigenes
    NVDEC-ffmpeg (14.09. gemessen). WO ZWEI MESSUNGEN STREITEN, NIMMT DIE FORMEL
    DIE GROESSERE: die aeltere Reihe vom 04.09. (`vram_waechter_mb`, erster
    Waechter 1500, jeder weitere 700) sagt fuer drei und mehr Waechter MEHR
    voraus als die Zerlegung vom 14.09.; der Widerspruch wird nicht
    stillschweigend aufgeloest, sondern konservativ.
    Intel: je Waechter ein voller Posten, linear (nur n=1 gemessen, s. o.)."""
    n = max(0, int(n_waechter or 0))
    if n == 0:
        return 0
    s = stuetzwerte(kind)
    if not s:
        return 0
    neu = s["waechter_engine_mb"] + n * s["waechter_decoder_mb"]
    if s["mass"] == "vram":
        return max(neu, vram_waechter_mb(n))          # 04.09. gegen 14.09.
    return neu


def container_ram_grundlast_mb(kind, n_waechter):
    """Was im Container an SYSTEMSPEICHER steht, BEVOR der Analyse-Worker startet
    (.528). -> (mb, posten) · posten = {} heisst „fuer dieses Backend gibt es hier
    nichts" (openvino: dort rechnet die Formel die Groesse selbst).

    Die Posten sind die des Endzustands der NB-Abnahme: Dienstprozess IMMER,
    Live-Engine nur wenn ueberhaupt ein Waechter laeuft (ohne Waechter existiert
    der Prozess nicht), dazu je Waechter sein Decoder-ffmpeg. Der Dienst-Posten
    wurde MIT zwei laufenden Waechtern gemessen und bleibt auch ohne sie stehen —
    dieselbe vorsichtige Richtung wie ueberall in diesem Modul."""
    p = CONTAINER_RAM_POSTEN.get(str(kind or ""))
    if not p:
        return 0, {}
    n = max(0, int(n_waechter or 0))
    wae = (p["waechter_engine_mb"] + n * p["waechter_decoder_mb"]) if n else 0
    posten = {"dienst_mb": p["dienst_mb"], "waechter_n": n,
              "waechter_engine_mb": p["waechter_engine_mb"] if n else 0,
              "waechter_decoder_mb": p["waechter_decoder_mb"],
              "waechter_mb": wae, "beleg": p["beleg"]}
    return p["dienst_mb"] + wae, posten


def fussabdruck_mb(n_straenge, kind="cuda", g_zusatz=0, n_aktiv=None):
    """Fussabdruck(N, G) OHNE Waechter und OHNE Dienst — die reine Worker-Seite.

    `g_zusatz` = Aufloesungen UEBER die hinaus, die in den Ankern schon stecken
    (die Messlaeufe fuhren den gt5-Mix mit 1080p und 4K). Wer eine dritte
    Aufloesung hinzunimmt, rechnet sie hier mit.
    `n_aktiv` = wie viele Jobs gleichzeitig einen Decoder halten (A <= N);
    Vorgabe ist der ungemuetliche Fall A = N.
    -> None, wenn es fuer dieses Backend keine Messung gibt."""
    s = stuetzwerte(kind)
    if not s:
        return None
    n = max(0, int(n_straenge or 0))
    a = n if n_aktiv is None else max(0, min(n, int(n_aktiv)))
    g = max(0, int(g_zusatz or 0))
    return (s["basis_mb"] + g * s["geometrie_mb"]
            + n * (s["strang_mb"] + s["strang_dauerlast_mb"])
            + a * s["decoder_mb"])


# HARTER DECKEL fuer die Nutzer-Wahl (User-Entscheid 14.09.2026). Wer die Zahl
# selbst setzt, darf ueber die Formel hinaus — Tester werden nicht bevormundet,
# und ein Worker-OOM bleibt nachgewiesen isoliert (Live-Test 14.09.: der
# betroffene Job scheitert, die anderen 29 rechnen zu Ende, die Live-Waechter
# merken nichts). Was NICHT geht, ist eine beliebige Zahl: jenseits von vier
# Straengen gibt es auf keinem gemessenen Weg noch einen Gewinn (CUDA saettigt
# bei 3, die iGPU bei 2), es waere nur Speicher. Werte darueber werden deshalb
# gekappt — LAUT, nie still.
# .535 (Inhaber-Entscheid 15.09.2026, aus der Feldmessung): VON VIER AUF SECHS.
# Anlass sind die Zahlen desselben Abends — drei Straenge ohne Live-Waechter:
# GPU-Auslastung im Mittel 55 %, Median 62 %, Kartenspitze 2769 MiB, gemessener
# Strang-Preis 654 MiB (Plateau n3 - n2, RTX 3060). Da ist Luft, und wo der Knick
# wirklich liegt, muss gemessen werden statt geraten. Die 4 war seit .528 ein
# Erfahrungswert unserer eigenen zwei Karten und stand einer Messung im Weg.
# WAS DIE ZAHL NICHT IST: eine Empfehlung. Sie ist der harte Riegel; geplant wird
# weiter aus dem Speicher (Leiter), und ohne ausdruecklichen `worker_straenge`
# deckelt der gemessene Durchsatz-Vorschlag die Automatik wie bisher.
STRAENGE_MAX = 6


# ============================================================================
# .535 — DIE MESSTABELLE (Fassung 4, Inhaber-Entscheid 15.09.2026 19:4x:
# „Warum nehmen wir das nicht einfach als Basis, 10 % auf jede Steigerung
# drauf")
# ============================================================================
# SIE ERSETZT DIE EICHUNG. Bis .534 plante die Leiter aus Ankern einer
# 6-GB-Referenzkarte und liess den Worker im Betrieb nachmessen (Plateau je
# Konstellation, Aufstieg Stufe fuer Stufe). Das hat an drei Tagen drei
# verschiedene Fehlerklassen erzeugt — vergiftete Plateaus durch spaet ladende
# Waechter, Preise, die ohne pid-Sicht gar nicht zu messen waren, und eine
# Anlage, die ihren eigenen Verbrauch gegen sich rechnete. Jetzt steht eine
# TABELLE, gemessen am 15.09.2026 auf zwei echten Karten, je Posten das
# gemessene MAXIMUM plus 10 % Sicherheit:
#
#   Prozess mit erstem Strang   1940 MiB  (gemessen 1762: RTX 2060 Mobile, 4K,
#                                          205 Gesichter, EIN Strang)
#   jeder weitere Strang        720 MiB   (gemessen 654: Feldtester-Anlage,
#                                          RTX 3060, Plateau n3 - n2)
#   jede weitere Geometrie      1235 MiB  (gemessen 1123: Feldtester-Anlage,
#                                          drei Straenge)
#
# Die erste Geometrie steckt im Prozess-Preis; eine zweite ist fest eingeplant
# (GEOMETRIEN_IN_ANKERN, unveraendert 2), mehr als drei fuehrt ein Prozess
# ohnehin nicht (der Geometrie-Verfall in worker_dienst raeumt die aelteste weg).
# Die Auswahl „welche Aufloesungen braucht DIESE Anlage wirklich" ist bewusst
# NICHT hier — sie steht als Folgeversion in `analysen/bauplan_534_eichung.md`
# §15.
#
# WAS DIE TABELLE ENTHAELT und deshalb NICHT zweimal gezaehlt werden darf: den
# CUDA-Kontext, die Handles, den NVDEC-Decoder je Strang und die Dauerlast ueber
# viele Analysen — es sind kartenweite Messwerte eines laufenden Betriebs. Der
# Arena-Deckel zieht die Posten ausserhalb der Arena weiterhin ab (s.
# `arena_deckel_mb`), aber NUR dort und nur beim Umrechnen des Budgets.
TABELLE_FASSUNG = 4
TAB_PROZESS_MB = 1940        # Prozess mit erstem Strang UND erster Geometrie
TAB_STRANG_MB = 720          # jeder weitere Strang, Decoder inbegriffen
TAB_GEOMETRIE_MB = 1235      # jede weitere Geometrie
TABELLE_BELEG = ("gemessen 15.09.2026, RTX 2060 Mobile (1762 MiB, 4K, ein "
                 "Strang) und RTX 3060 (654 MiB je weiterem Strang, 1123 MiB "
                 "je weiterer Geometrie), je Posten Maximum + 10 %")


def tabelle_summe(n_straenge, geometrien=None):
    """Was `n` Rechenstraenge mit `g` Geometrien nach der Tabelle kosten. -> MB

    EINE Formel fuer Leiter, Rueckrechnung und Probe: Prozess + je weitere
    Geometrie + je weiterer Strang. Ohne `geometrien` gilt die feste Annahme
    (`GEOMETRIEN_IN_ANKERN`)."""
    n = max(1, int(n_straenge or 1))
    g = max(1, int(GEOMETRIEN_IN_ANKERN if geometrien is None else geometrien))
    return (TAB_PROZESS_MB + (g - 1) * TAB_GEOMETRIE_MB
            + (n - 1) * TAB_STRANG_MB)


# ============================================================================
# .531 (15.09.2026) — DIE LEITER. Ab hier plant der Kartenhaushalt in STUFEN.
# ============================================================================
# DIE LEITER IST DIE EINE RECHNUNG FUER STRAENGE UND GEOMETRIEN; Preise sind
# kartenweite `memory.used`-Deltas und enthalten den CUDA-Kontext BEREITS — er
# wird nur beim Umrechnen in den Arena-Deckel abgezogen, nie gegen die Preise.
#
# Anlass (Diagnose `analysen/diagnose_530_vram.md`): bis .530 rechnete der Dienst
# `fussabdruck_mb(N)` gegen den freien Platz und den Geometrie-Deckel in einer
# ZWEITEN, anders gebauten Rechnung. Auf einer 12-GB-Karte liess das drei
# Straenge zu, der Geometriebau fuellte die Karte in unter einer Minute, und
# jede Analyse endete im CUDA-BFC-OOM. Die Leiter schaltet die Verbraucher
# statt dessen von unten nach oben ein, solange die KUMULIERTE Summe ins Budget
# passt — Strang vor Zusatzgeometrie, weil der Engpass Durchsatz ist.
#
# Kumulierte Anker-Schwellen (RTX 2060 Mobile, s. STUETZWERTE) — seit .535 bis
# sechs Straenge, weil STRAENGE_MAX von 4 auf 6 gegangen ist:
#     S1 3129 | S2 5332 | S3 6032 | S4 8235 | S5 8935 | S6 11138 |
#     S7 13341 | S8 15544
# KORREKTUR ZUM KONZEPT (`konzept_531_vram.md` §4, QS-Plan-Fund B1): die dortige
# Baender-Tabelle nannte 7535 als Kante — das ist `fussabdruck_mb(3)` der alten
# Formel, NICHT die Leitersumme. Massgeblich ist die Leiter.
#
# .532 — WAS DIE LEITER NICHT IST: sie ist nicht der Arena-Deckel. Die Leiter
# entscheidet, WIE VIEL gebaut wird (Straenge, Geometrien); der Deckel ist die
# Grenze, an der dieser Prozess die KARTE nicht mehr gefaehrden darf, und die
# bemisst sich am ganzen Budget (s. `arena_deckel_mb`). Bis .531 war beides
# dieselbe Zahl, und im Feld war der so gerechnete Deckel nach sechs
# Ereignissen voll, obwohl die Karte noch rund 2 GB frei hatte.
# .535: HIER STAND AUCH `ANKER_FASSUNG` — die Fassungsnummer der Stuetzwerte.
# Sie war Teil des Eich-Schluessels und sonst nichts; mit ihm ist sie ohne
# Leser. Die Stuetzwerte selbst bleiben (Decoder- und Dienst-Posten, die
# RAM-Backends), nur ihre Kennung ist weg.

# .535: HIER STAND `EICH_FASSUNG` — die Fassungsnummer der Eichdatei
# `state/vram_eichung.json`. Die Datei ist mit der Preis-Messung entfallen;
# was eine Stufe kostet, steht in der Messtabelle oben.
# CUDA-Kontext + cuBLAS-/cuDNN-Handles + alles, was ORT ueber `Reserve()` holt:
# der Teil des Kartenspeichers DIESES Prozesses, den die gedeckelte Arena NICHT
# deckt. Gemessen als „Anteil des Worker-Prozesses minus registrierter Deckel"
# bei voll gelaufener Arena: 310-726 MiB ueber drei Laeufe. Hier steht die OBERE
# Kante — dieselbe Hausregel wie bei DECODER_CUDA_MB, und in der richtigen
# Richtung: ein zu grosser Posten macht den Arena-Deckel kleiner, ein zu kleiner
# liesse die Karte ueberlaufen.
# 0 hiesse AUSDRUECKLICH „ungemessen" und nicht „null"; dann saehe man das in
# /health am Feld `posten_gemessen`.
KONTEXT_HANDLES_CUDA_MB = 726
KONTEXT_HANDLES_GEMESSEN = True
KONTEXT_HANDLES_BELEG = ("vram_proben_20260915/ergebnis.md, Proben C1/C2/C4, "
                         "RTX 2060 Mobile, 15.09.2026")
# Der NVDEC-ffmpeg je Strang ist ein EIGENER Prozess mit eigener PID und steckt
# deshalb NICHT in dieser Zahl (sie ist der Anteil des Worker-Prozesses). Er
# bleibt der eigene Posten DECODER_CUDA_MB (358) und wird in
# `posten_ausserhalb_mb` getrennt gefuehrt.

# Kleinster Arena-Deckel, den wir ueberhaupt registrieren. Er ist kein
# Betriebspunkt, sondern ein Riegel gegen eine Rechnung, die sich verrechnet
# hat: ein Deckel von 0 hiesse in ORT „unbegrenzt" (allocator_utils.cc:24), und
# genau das Gegenteil ist gemeint.
ARENA_DECKEL_MIN_MB = 256

# Mindestabstand zwischen zwei druckbedingten Worker-Neustarts (P5). Ohne ihn
# antwortet der Dienst auf einen dauerhaft fremden Verbraucher mit einer
# Neustart-Schleife, und die kostet mehr Analysen als der Druck selbst.
DRUCK_NEUSTART_ABSTAND_S = 600

# Ab wann der Anteil der Live-Engine im GEMESSENEN `memory.free` wirklich drin
# ist. Im Feld kamen Engine und fuenf Decoder binnen 15 s hoch (WL3-T6); 60 s
# sind das Vierfache davon und damit die vorsichtige Kante. Solange die Engine
# juenger ist — oder gar nicht laeuft —, wird ihr voller Posten RESERVIERT, denn
# er kann noch kommen. Ist sie laenger da, steht ihr Speicher schon im Messwert
# und ein zweiter Abzug waere doppelt gezaehlt.
LIVE_WARM_S = 60

# .535: HIER STANDEN `STUFEN_ORDNUNG`, `_stufen_preis` und `stuetzwerte_eich`
# — die Wahl-Reihenfolge der alten Leiter und die Ueberlagerung der Anker durch
# die Eichdatei. Alle drei sind mit der Messtabelle ersatzlos entfallen: es gibt
# keine Anker mehr zu ueberlagern, keine Stufenarten mehr zu mischen und keine
# Preisquelle ausser der Tabelle. Mit ihnen ist die ganze Preis-Messung
# ausgebaut — die Eichdatei `state/vram_eichung.json` wird nicht mehr
# geschrieben und nicht mehr gelesen (Inhaber-Entscheid 15.09.2026: „Baue die
# ganze Messung und Eichung aus. Wir bauen nachher etwas Neues dafuer."). Was
# diese Karte WIRKLICH haelt, misst weiterhin die Prozess-Sonde je Moment
# (/health `laufend_eigen_mb`/`laufend_eigen_grund`), und wer eine Stufe
# nachmessen will, nimmt die Feinmessung.


def pflicht_preis_mb(kind):
    """WAS EIN RECHNENDER PROZESS MINDESTENS KOSTET — S0 + S1.

    EINE Groesse fuer Verweigerung, Wartebedingung, Leiter-Tabelle und Probe
    (WL1-T3): Basis + ein Strang mit Dauerlast und seinem Decoder. Auf den
    Ankern sind das 3129 MiB. Wer irgendwo eine zweite Zahl fuer denselben
    Sachverhalt hinschreibt, hat die Stelle, an der die beiden auseinanderlaufen,
    schon gebaut."""
    s = stuetzwerte(kind)
    if not s:
        return 0
    if s.get("mass") != "vram":
        # RAM-Backends haben keine Tabelle und keine Leiter — dort gilt der
        # Fussabdruck, nicht der Pflichtpreis.
        return 0
    return tabelle_summe(1)


def straenge_preis_mb(kind, n):
    """WAS `n` RECHENSTRAENGE NACH DEN GELTENDEN PREISEN KOSTEN (.535).

    Basis + n × Strang-Paket, ohne Zusatzgeometrien — also dieselbe Summe, die
    `leiter_summe_bis` aus einer fertigen Leiter zieht, nur ohne dass es die
    Leiter dafuer schon geben muss. `pflicht_preis_mb` ist der Sonderfall n = 1.

    WOZU: auf Anlagen ohne Prozess-Sonde muss die Leiter den LAUFENDEN Worker
    aus dem gemessenen Frei-Wert zurueckrechnen, bevor sie ueberhaupt eine
    Leiter bauen kann — und in diesem Moment gibt es noch keine."""
    s = stuetzwerte(kind)
    if not s or s.get("mass") != "vram" or int(n or 0) <= 0:
        return 0
    return tabelle_summe(int(n))


def posten_ausserhalb_mb(kind, n_straenge):
    """WAS DIE GEDECKELTE ARENA NICHT DECKT. -> (mb, posten)

    Zwei Dinge liegen auf der Karte, ohne je durch die ORT-Arena zu gehen:
      * das NVDEC-ffmpeg je Strang — ein EIGENER Prozess (engine_cuda.py,
        worker_kern.py), also ausserhalb jeder Arena dieses Prozesses;
      * der CUDA-Kontext samt cuBLAS-/cuDNN-Handles und allem, was ORT ueber
        `Reserve()` holt (das umgeht den Deckel bauartbedingt).
    Beide stecken in den Leiter-PREISEN schon drin (die sind kartenweite
    Deltas). Abgezogen werden sie NUR HIER — beim Umrechnen der Leitersumme in
    den Arena-Deckel. Ein zweiter Abzug gegen die Preise waere doppelt gezaehlt.

    Nur auf Backends mit eigenem Kartenspeicher; auf RAM-Backends gibt es keine
    Arena, die man deckeln koennte, und die Funktion sagt 0/leer."""
    s = stuetzwerte(kind)
    if not s or s["mass"] != "vram":
        return 0, {}
    n = max(0, int(n_straenge or 0))
    dec = n * int(s["decoder_mb"])
    kon = int(KONTEXT_HANDLES_CUDA_MB)
    return dec + kon, {"decoder_je_strang_mb": int(s["decoder_mb"]),
                       "straenge": n, "decoder_mb": dec,
                       "kontext_und_handles_mb": kon,
                       "gemessen": bool(KONTEXT_HANDLES_GEMESSEN),
                       "beleg": KONTEXT_HANDLES_BELEG}


def waechter_abzug_mb(n_waechter, kind, engine_alter_s=None):
    """Was vom GEMESSENEN freien Kartenspeicher fuer die Live-Waechter noch
    zurueckzulegen ist. -> (mb, grund)

    DIE REGEL, und sie ist der ganze Unterschied: was zum Messzeitpunkt schon auf
    der Karte liegt, steht im Messwert — es ein zweites Mal abzuziehen heisst,
    denselben Speicher zweimal zu bezahlen. Was noch KOMMEN kann, wird dagegen
    reserviert.

    Die Live-Engine ist genau der Grenzfall (WL3-T6): im Feld kamen sie und fuenf
    Decoder binnen 15 s hoch. Wer in diesem Fenster misst, sieht den Platz noch
    frei, den sie gleich nimmt. Deshalb:
      * Engine laeuft nicht oder ihr Alter ist unbekannt -> voller Posten,
      * Engine juenger als LIVE_WARM_S                    -> voller Posten,
      * Engine laenger da                                 -> 0, sie steckt im Messwert.

    Auf der GERECHNETEN Seite (aus `gesamt`) bleibt der volle Posten immer stehen
    — dort ist nichts gemessen, was ihn schon enthalten koennte."""
    voll = waechter_posten_mb(n_waechter, kind)
    if voll <= 0:
        return 0, "keine Waechter"
    if engine_alter_s is None:
        return voll, "Live-Engine laeuft nicht oder ihr Alter ist unbekannt — Posten reserviert"
    try:
        alter = float(engine_alter_s)
    except (TypeError, ValueError):
        return voll, "Engine-Alter unlesbar — Posten reserviert"
    if alter < LIVE_WARM_S:
        return voll, (f"Live-Engine erst {alter:.0f}s alt (< {LIVE_WARM_S}s) — "
                      f"ihr Speicher steht womoeglich noch nicht im Messwert")
    return 0, (f"Live-Engine laeuft seit {alter:.0f}s — ihr Speicher steckt "
               f"bereits im gemessenen Wert")


def arena_deckel_mb(kind, budget_mb, n_straenge):
    """Der ORT-Deckel: das GANZE Budget minus der Posten ausserhalb der Arena.

    .532, GEMESSEN IM FELD: bis .531 stand hier die LEITERSUMME statt des
    Budgets — also die Summe der Anker-Preise, und die sind auf einer
    6-GB-Karte mit kleinen Bildern entstanden. Auf der Feldmaschine ergab das
    am 15.09. einen Deckel von 4590 MiB, obwohl 6638 MiB Budget da waren; nach
    SECHS Ereignissen (zwei Straenge, 1080p und 4K gemischt, bis 40 Gesichter
    je Bild) war er voll und jede weitere Analyse scheiterte am EIGENEN Deckel,
    waehrend die Karte noch rund 2 GB frei hatte. Die Leiter entscheidet
    weiterhin, WIE VIEL gebaut wird (Straenge, Geometrien); der Deckel ist
    etwas anderes — die Grenze, an der dieser Prozess die KARTE nicht mehr
    gefaehrden darf. Die Anker als Deckel zu nehmen hiess, eine fremde Karte
    zum Mass der eigenen zu machen.

    Der Deckel gilt fuer die PROZESS-LEBENSZEIT (bfc_arena.cc:39 setzt
    `memory_limit_` bei der Konstruktion); ein kleinerer ist nur ueber einen
    geordneten Neustart erreichbar."""
    roh = int(budget_mb or 0) - posten_ausserhalb_mb(kind, n_straenge)[0]
    return max(ARENA_DECKEL_MIN_MB, int(roh))


def leiter(kind, worker_budget_mb, vorschlag, nutzer_n=0):
    """DIE LEITER, seit .535 aus der MESSTABELLE statt aus Ankern/Eichung.

    -> dict {n, g_zusatz, geometrien_max, summe_mb, stufen[], quelle, grund, …}
    oder None auf einem Backend ohne eigenen Kartenspeicher.

    DIE RECHNUNG, in einer Zeile: `Prozess (1940, erste Geometrie darin) + die
    fest eingeplante zweite Geometrie (1235) + je weiterem Strang 720`, und
    genommen wird die hoechste Strangzahl, deren Summe noch ins Budget passt.
    Keine Wahl mehr zwischen Strang und Geometrie: die Geometrien stehen fest
    (`GEOMETRIEN_IN_ANKERN`), der Rest des Budgets geht in Straenge.

    OBERE GRENZE ist `min(nutzer_n or vorschlag, STRAENGE_MAX)`: OHNE
    ausdrueckliche Nutzer-Zahl deckelt der gemessene Durchsatz-Wert die
    Automatik; MIT Nutzer-Zahl gilt diese statt seiner (Feldbefund 15.09. 18:15
    — unser Laborwert darf den Betreiber nicht deckeln). Auf Karten-Backends
    ist die Nutzer-Zahl eine OBERGRENZE und kein Zwang ueber den Speicher
    hinaus.

    `grund` = `durchsatz` bzw. `nutzer`, wenn der naechste Strang noch ins
    Budget gepasst haette und nur die obere Grenze ihn verhindert hat; sonst
    `speicher`.

    .535 (Ausbau): `eich`, `karte`, `gesamt_mb`, `waechter_n` und `planung`
    sind aus der Signatur VERSCHWUNDEN. Sie gehoerten zur Preis-Messung, die es
    nicht mehr gibt; als tote Parameter stehenzulassen hiesse, dem naechsten
    Leser eine Wahl vorzugaukeln, die keine ist."""
    s = stuetzwerte(kind)
    if not s or s.get("mass") != "vram":
        return None
    budget = int(worker_budget_mb or 0)
    wunsch = max(0, int(nutzer_n or 0))
    # .535: DIE OBERGRENZE IST DER HARTE RIEGEL ODER DIE NUTZER-ZAHL — NICHT
    # MEHR UNSER DURCHSATZ-VORSCHLAG. Der war ein Laborwert unserer eigenen
    # zwei Karten („more did not get faster in our tests") und deckelte im Feld
    # einen Betreiber, dessen Karte mehr trug (15.09. 18:15). `vorschlag` steht
    # nur noch in der Signatur, weil die Aufrufer ihn mitgeben; die Leiter
    # liest ihn nicht mehr. Was wirklich schneller ist, sagt die Messung, und
    # wem das zu viel ist, setzt `worker_straenge`.
    obergrenze = min(wunsch or STRAENGE_MAX, STRAENGE_MAX)
    g = int(GEOMETRIEN_IN_ANKERN)
    pflicht = tabelle_summe(1, g)
    stufen = [{"stufe": "S0", "art": "prozess", "preis_mb": TAB_PROZESS_MB,
               "gebaut": True, "grund": "pflicht: Prozess mit erstem Strang "
                                        "und erster Geometrie"}]
    for _ in range(max(0, g - 1)):
        stufen.append({"stufe": f"S{len(stufen)}", "art": "geometrie",
                       "preis_mb": TAB_GEOMETRIE_MB, "gebaut": True,
                       "grund": "pflicht: fest eingeplante Aufloesung"})
    n, summe = 1, pflicht
    durchsatz_moeglich = False
    while True:
        name = f"S{len(stufen)}"
        if n >= STRAENGE_MAX:
            # Der harte Riegel. Traegt die Karte noch mehr, ist das eine
            # Auskunft und keine Nebensache — sie steht als `grund: max` in
            # /health, damit niemand den Riegel fuer die Karte haelt.
            if summe + TAB_STRANG_MB <= budget:
                durchsatz_moeglich = True
                stufen.append({"stufe": f"S{len(stufen)}", "art": "strang",
                               "preis_mb": TAB_STRANG_MB, "gebaut": False,
                               "grund": f"uebersprungen: harter Riegel "
                                        f"STRAENGE_MAX {STRAENGE_MAX}"})
            break
        if n + 1 > obergrenze:
            if summe + TAB_STRANG_MB <= budget:
                durchsatz_moeglich = True
            stufen.append({"stufe": name, "art": "strang",
                           "preis_mb": TAB_STRANG_MB, "gebaut": False,
                           "grund": f"uebersprungen: obergrenze {obergrenze} "
                                    f"({'nutzerwahl' if wunsch else 'durchsatz'})"})
            break
        if summe + TAB_STRANG_MB > budget:
            stufen.append({"stufe": name, "art": "strang",
                           "preis_mb": TAB_STRANG_MB, "gebaut": False,
                           "grund": (f"ausgelassen: preis {TAB_STRANG_MB} MiB > "
                                     f"rest {max(0, budget - summe)} MiB")})
            break
        summe += TAB_STRANG_MB
        n += 1
        stufen.append({"stufe": name, "art": "strang",
                       "preis_mb": TAB_STRANG_MB, "gebaut": True, "grund": None})
    quelle = f"tabelle (fassung {TABELLE_FASSUNG})"
    return {"n": n, "g_zusatz": 0, "geometrien_max": g,
            "summe_mb": summe, "stufen": stufen, "quelle": "tabelle",
            "preis_quelle": {"prozess": quelle, "strang": quelle,
                             "geometrie": quelle},
            "preise_mb": {"prozess": TAB_PROZESS_MB, "strang": TAB_STRANG_MB,
                          "geometrie": TAB_GEOMETRIE_MB},
            "gemessen_mb": {}, "tabelle_beleg": TABELLE_BELEG,
            "obergrenze": obergrenze,
            "budget_mb": budget, "pflicht_preis_mb": pflicht,
            "unter_pflicht": budget < pflicht,
            # .535: DREI GRUENDE, und sie sagen Verschiedenes. `speicher` =
            # die Karte traegt nicht mehr. `nutzer` = die ausdrueckliche
            # Einstellung hat gedeckelt. `max` = der harte Riegel
            # STRAENGE_MAX; da waere noch Platz, aber jenseits davon ist nichts
            # gemessen.
            "grund": (("nutzer" if wunsch else "max")
                      if durchsatz_moeglich else "speicher")}


def leiter_text(kind, lt):
    """Die Leiter als EINE Log-Zeile (Englisch wie die Nachbarzeilen)."""
    if not lt:
        return ""
    gebaut = [st["stufe"] for st in lt["stufen"] if st["gebaut"]]
    pm = lt.get("preise_mb") or {}
    herkunft = ", ".join(f"{art} {pm.get(art, '?')} MiB"
                         for art in ("prozess", "geometrie", "strang"))
    return (f"ladder {','.join(gebaut)} = {lt['summe_mb']} MiB "
            f"({lt['n']} thread(s), {lt['geometrien_max']} geometries) of "
            f"{lt['budget_mb']} MiB budget; prices from the measurement table "
            f"(version {TABELLE_FASSUNG}, {TABELLE_BELEG})"
            + (f" [{herkunft}]" if herkunft else ""))


def _fail_closed(aus, kind, vor, warum):
    """DIE KARTE IST NICHT MESSBAR — ein Strang, Tabellen-Deckel, rot.

    Bis .530 fiel dieser Fall auf den gemessenen Durchsatz-Wert zurueck, also
    auf CUDA auf drei Straenge OHNE Deckel. Das ist fail-OPEN: ausgerechnet in
    der Lage, in der wir ueber die Karte nichts wissen, wird am meisten
    gewagt. Der Durchsatz-Vorschlag ist auf Karten-Backends nie mehr der
    Rueckfall. Die Nutzer-Zahl gilt hier ebenfalls nicht nach oben — sie ist auf
    diesem Backend eine Obergrenze, und die kleinste Obergrenze ist ein Strang."""
    pflicht = pflicht_preis_mb(kind)
    posten_mb, posten = posten_ausserhalb_mb(kind, 1)
    # HIER ist der Pflichtpreis wirklich das Budget: es gibt keine Messung, aus
    # der ein groesseres folgen koennte (.532 aendert nur den gemessenen Weg).
    deckel = arena_deckel_mb(kind, pflicht, 1)
    aus.update({
        "n": 1, "formel_n": 1, "grund": "nicht_messbar", "zustand": "rot",
        "worker_budget_mb": 0, "arena_deckel_mb": deckel,
        # .535: der Deckel kommt aus der MESSTABELLE (Pflichtpreis), nicht mehr
        # aus den Ankern — die Quelle heisst deshalb, was sie ist.
        "deckel_quelle": "tabelle",
        "posten_ausserhalb_mb": posten_mb, "posten": posten,
        "geometrien_max": GEOMETRIEN_IN_ANKERN, "fussabdruck_mb": pflicht,
        "hinweis": (f"card memory is not measurable ({warum}) — fail-closed: one "
                    f"compute thread, arena cap {deckel} MiB from the measurement "
                    f"table, no extra geometry. Set worker_vram_mb by hand to the "
                    f"card memory "
                    f"the worker may use, or check that the container can reach "
                    f"nvidia-smi (nvidia-container-toolkit)"),
        "rechenweg": (f"{kind}/vram: card not measurable ({warum}) -> fail-closed: "
                      f"1 thread, arena cap {deckel} MiB (mandatory price "
                      f"{pflicht} MiB - {posten_mb} MiB outside the arena)"),
    })
    if aus["nutzer_n"] > 1:
        aus["unter_formel"] = (
            f"worker_straenge={aus['nutzer_n']} is not used while the card cannot "
            f"be measured — on a card backend the setting is an upper limit, and "
            f"without a measurement the worker plans for one thread")
    return aus


def _kartenhaushalt(aus, s, kind, worker_budget, vor, gesamt,
                    n_waechter, gem, res, dienst, wae):
    """DER KARTENHAUSHALT (.531): aus dem Budget die Leiter, aus der Leiter den
    Arena-Deckel. EINE Rechnung fuer Straenge UND Geometrien (Defekt 4)."""
    lt = leiter(kind, worker_budget, vor, nutzer_n=aus["nutzer_n"])
    # Dieselbe Leiter OHNE die Nutzer-Obergrenze: das ist die Zahl, die neben der
    # gewaehlten stehen muss ('du hast 3 gewaehlt, die Karte traegt 1').
    lt_formel = leiter(kind, worker_budget, vor, nutzer_n=0)
    pflicht = lt["pflicht_preis_mb"]
    aus["leiter"] = lt
    aus["worker_budget_mb"] = worker_budget
    aus["preis_quelle"] = lt["quelle"]
    # .534: dieselbe Auskunft JE STUFE, dazu die Preise selbst — /health und das
    # Log sollen nennen koennen, welche Zahl gemessen ist und welche der
    # skalierte Anker einer fremden Karte.
    aus["preis_quelle_stufen"] = dict(lt.get("preis_quelle") or {})
    aus["preise_mb"] = dict(lt.get("preise_mb") or {})
    aus["gemessen_mb"] = dict(lt.get("gemessen_mb") or {})
    aus["_formel_n_vram"] = lt_formel["n"]
    einheit = "MiB"
    if lt["unter_pflicht"]:
        # .535: KEIN EICHLAUF MEHR. Bis .534 lief hier ein Lauf mit minimaler
        # Leiter, der die Preise dieser Karte nachmessen sollte — die Preise
        # stehen jetzt in der Tabelle, es gibt nichts mehr zu messen. Bleibt die
        # ehrliche Absage: was die Tabelle als Pflicht nennt (Prozess mit erstem
        # Strang plus die fest eingeplante zweite Geometrie), muss da sein.
        posten_mb, posten = posten_ausserhalb_mb(kind, 1)
        deckel = max(ARENA_DECKEL_MIN_MB, worker_budget - posten_mb)
        n, g = 1, 0
        grund = "zu_klein"
        aus["zustand"] = "rot"
        aus["verweigert"] = True
        aus["hinweis"] = (
            f"the card does not carry one compute thread: {worker_budget} "
            f"{einheit} budget against {pflicht} {einheit} from the measurement "
            f"table ({TAB_PROZESS_MB} process incl. first geometry + "
            f"{TAB_GEOMETRIE_MB} for the second). The worker is NOT started "
            f"into this. Turn off live watchers, lower worker_vram_reserve_mb, "
            f"set worker_vram_mb by hand if you know better, or run the cpu "
            f"image variant")
    else:
        n, g = lt["n"], lt["g_zusatz"]
        posten_mb, posten = posten_ausserhalb_mb(kind, n)
        # .532: DAS GANZE BUDGET, nicht die Leitersumme (s. arena_deckel_mb).
        # Der Rest zwischen Leitersumme und Budget ist kein Puffer, den wir
        # verschenken duerfen — er ist genau der Platz, den die Bilder dieser
        # Anlage mehr brauchen als die Anker einer fremden Karte.
        deckel = arena_deckel_mb(kind, worker_budget, n)
        grund = lt["grund"]
    # .534 (Nachpruefung, Punkt 2): `fussabdruck_mb` ist die Zahl, mit der der
    # Prozess WIRKLICH faehrt. Unter dem Pflichtpreis wird nicht gestartet, dort
    # steht das Budget selbst; sonst ist es die Leitersumme. .535: den dritten
    # Fall (`ungeeicht` — Pflichtpreis trotz groesserer Leiter) gibt es nicht
    # mehr, seit die Preise aus der Tabelle kommen.
    _fuss = worker_budget if lt["unter_pflicht"] else lt["summe_mb"]
    aus.update({"n": n, "g_zusatz": g, "grund": grund,
                "geometrien_max": GEOMETRIEN_IN_ANKERN + g,
                "fussabdruck_mb": _fuss,
                "arena_deckel_mb": deckel, "deckel_quelle": "formel",
                "posten_ausserhalb_mb": posten_mb, "posten": posten})
    if aus["frei_quelle"] == "gemessen":
        _eig = int(aus.get("laufend_eigen_mb") or 0)
        frei_text = (f"{gem} {einheit} really free on the card (measured)"
                     + (f" + {_eig} {einheit} the running worker holds itself "
                        f"(already counted in the ladder, not foreign use)"
                        if _eig else "")
                     + f" - {res} "
                     f"reserve ({aus.get('reserve_quelle') or 'formel'}) "
                     f"- {aus['waechter_abzug_mb']} guards"
                     f"({aus['waechter_n']}, {aus['waechter_abzug_grund']}) "
                     f"= {worker_budget} {einheit} budget, less than the "
                     f"{aus['frei_gerechnet_mb']} {einheit} the posten sum would "
                     f"have allowed — free measured instead of computed")
    else:
        frei_text = (f"{gesamt} - {res} reserve "
                     f"({aus.get('reserve_quelle') or 'formel'}) - {dienst} service - {wae} "
                     f"guards({aus['waechter_n']}) = {worker_budget} {einheit} budget"
                     + (f" (measured free {gem} {einheit} was not tighter)"
                        if gem > 0 else ""))
    aus["rechenweg"] = (
        f"{kind}/vram: {frei_text}; {leiter_text(kind, lt)}; arena cap {deckel} "
        f"{einheit} (the whole budget minus what lies outside the arena, not the "
        f"ladder sum); outside the arena {posten_mb} {einheit} ({n} decoder + "
        f"context/handles"
        + ("" if posten.get("gemessen") else ", context/handles UNMEASURED")
        + f") -> {n} thread(s), {aus['geometrien_max']} geometries ({grund})")
    return _nutzer_wahl(aus)


def straenge(gesamt_mb, n_waechter, kind, vorschlag, g_zusatz=0, nutzer_n=0,
             frei_gemessen_mb=0, engine_alter_s=None,
             laufend_eigen_mb=0, reserve_wunsch=-1, laufend_n=0):
    """WIE VIELE RECHENSTRAENGE DIESE MASCHINE TRAEGT — die eine Antwort.

    Sie ist das Minimum aus zwei Groessen, und beide sind gemessen:
      SPEICHER   was nach Reserve, Dienst und Waechtern noch fuer Straenge
                 uebrig ist, gegen Fussabdruck(N, G) gerechnet.
      DURCHSATZ  der Wert, der auf diesem Beschleuniger am schnellsten war
                 (`vorschlag`, aus Service.PLAETZE_VORSCHLAG — EINE Quelle,
                 diese Zahl wird hier nicht zweitgeschrieben). Mehr Straenge als
                 das bringt nichts, kostet aber Speicher.
    Der kleinere gewinnt; welcher es war, steht im Ergebnis (`grund`).

    NUTZER-WAHL (`nutzer_n`, User-Entscheid 14.09.): ist die Zahl ausdruecklich
    gesetzt, GILT SIE — auch ueber dem gerechneten Deckel. Dann wird gewarnt und
    nicht eingegriffen (`ueber_formel`), und beide Zahlen bleiben sichtbar
    (`n` und `formel_n`). Der einzige harte Riegel ist STRAENGE_MAX; was
    darueber liegt, wird gekappt und gemeldet (`deckel_meldung`). NICHT gemeint
    ist der alte `analyse_plaetze`-Wert — der ist eine Platz-Zahl und wird nie
    als Strang-Zahl gedeutet (Migrations-Klemme, s. verifyd.worker_straenge).

    OHNE LESBARE MASCHINEN-GRENZE (gesamt_mb <= 0) wird NICHT geraten: es gilt
    der gemessene Durchsatz-Wert — also genau das heutige Verhalten — und der
    Grund wird laut gesagt. Das ist der Fall 'Olivier' aus Konzept §2, und er
    trifft die eigene Prod: deren cgroup meldet memory.max = 'max' (das
    LXC-Limit liegt auf einem von innen unsichtbaren Eltern-cgroup).

    REAL FREIES VRAM (`frei_gemessen_mb`, .529, Feldvorfall 15.09.): die Rechnung
    `gesamt - Reserve - Dienst - Waechter` zaehlt nur die EIGENEN Posten und
    unterstellt damit, die Karte gehoere uns allein. Auf der Feldtester-Anlage
    (RTX 3060, 12 GB, fuenf Waechter) kam sie auf 6659 MiB frei und liess zwei
    Straenge zu; in Wahrheit lag auf derselben Karte noch der Anzeige-Transcode
    und Fremdverbrauch, und der Geometrie-Bau endete im CUDA-BFC-OOM
    (`Failed to allocate memory for requested buffer of size 99532800`). Wird
    ein GEMESSENER Frei-Wert hereingereicht (nvidia-smi `memory.free`, dieselbe
    Sonde wie die Systemstatistik), gilt die kleinere der beiden Mengen. Warum
    nicht schlicht der Messwert: er wird VOR dem Worker-Start genommen, und wenn
    die Live-Waechter dann noch nicht stehen, sagt er MEHR frei als nachher
    wirklich da ist — er waere dann die optimistischere Zahl und liesse mehr
    Straenge zu als heute. Das Minimum ist dieselbe Regel, die in
    `waechter_posten_mb` schon steht: wo zwei Messungen streiten, nimmt die
    Formel die vorsichtigere. Welche gezogen hat, steht als `frei_quelle` im
    Ergebnis und im Rechenweg.

    WAS DER LAUFENDE WORKER HAELT (`laufend_eigen_mb`, .534): auf Karten-
    Backends ist `frei_gemessen_mb` das JETZT der Karte — ein schon laufender
    Worker steht darin als belegt, waehrend die Leiter ihn daneben von null auf
    plant. Wer diese Zahl hereinreicht (das saubere Plateau der laufenden
    Konstellation), bekommt sie zum Messwert zurueckgerechnet; wer nichts
    reicht, rechnet wie bisher. Ohne sie kann die Leiter im Betrieb nie wachsen,
    und die Aufstiegs-Frage der Eichung war strukturell mit „nein" beantwortet.

    .531 AUF KARTEN-BACKENDS (`mass == "vram"`): ab hier rechnet nicht mehr
    `fussabdruck_mb(N)` gegen den freien Platz, sondern die LEITER (s. dort) —
    eine Rechnung fuer Straenge UND Geometrien, dazu der Arena-Deckel und die
    Posten, die ausserhalb der Arena liegen. Ohne Messwert wird nicht mehr
    geraten: nicht messbar heisst ein Strang mit Anker-Deckel und /health rot.
    Container-RAM-Backends (Intel) laufen unveraendert durch den Zweig darunter,
    einschliesslich des `max(1, …)`-Bodens.

    -> dict: n, grund, rechenweg (Klartext, eine Zeile), plus die Posten.
    """
    vor = max(1, int(vorschlag or 1))
    s = stuetzwerte(kind)
    gesamt = int(gesamt_mb or 0)
    aus = {"n": vor, "kind": kind, "vorschlag": vor, "gesamt_mb": gesamt,
           "mass": (s or {}).get("mass"), "reserve_mb": 0, "dienst_mb": 0,
           "waechter_mb": 0, "waechter_n": max(0, int(n_waechter or 0)),
           "frei_mb": 0, "fussabdruck_mb": None, "g_zusatz": max(0, int(g_zusatz or 0)),
           # .529: welche der beiden Frei-Mengen gezogen hat, und beide Zahlen
           # daneben — eine Auskunft, die man nachrechnen kann.
           "frei_quelle": "gerechnet", "frei_gerechnet_mb": 0,
           "frei_gemessen_mb": max(0, int(frei_gemessen_mb or 0)),
           "laufend_eigen_mb": 0, "laufend_eigen_quelle": None,
           "reserve_quelle": "formel",
           "grund": "durchsatz", "hinweis": None,
           "nutzer_n": max(0, int(nutzer_n or 0)), "deckel_meldung": None,
           "ueber_formel": None,
           # .531: der Kartenhaushalt. `leiter` ist None auf allen Wegen, die
           # gar keine Karte planen (RAM-Backends, Backend ohne Messung) — das
           # ist eine Aussage und kein Loch.
           "waechter_abzug_mb": 0, "waechter_abzug_grund": None,
           "engine_alter_s": None,
           "leiter": None, "worker_budget_mb": 0, "arena_deckel_mb": 0,
           "deckel_quelle": "formel", "posten_ausserhalb_mb": 0, "posten": {},
           "geometrien_max": None, "preis_quelle": "anker",
           # .534: je Stufe, immer vorhanden — ein fehlendes Feld liest sich wie
           # „gemessen", und das waere genau die luegende Diagnose.
           "preis_quelle_stufen": {}, "preise_mb": {},
           "zustand": "gruen", "verweigert": False, "unter_formel": None}
    if not s:
        if kind in OHNE_DECKEL:
            # E6 (17.09.2026): ein Backend MIT eigenem Geraetespeicher, aber OHNE
            # jede Moeglichkeit, ihn zu deckeln — der Durchsatz-Vorschlag waere hier
            # fail-OPEN in genau der Lage, in der wir am wenigsten wissen (dieselbe
            # Richtung wie `_fail_closed` auf den Karten-Backends). Die Nutzer-Zahl
            # gilt weiter, sie laeuft unten durch `_nutzer_wahl`.
            aus["n"] = 1
            aus["grund"] = "kein_deckel_moeglich"
            aus["hinweis"] = OHNE_DECKEL[kind]
            aus["rechenweg"] = (f"{kind}: no memory measurements and no enforceable "
                                f"arena cap -> 1 compute thread (conservative)")
            return _nutzer_wahl(aus)
        aus["grund"] = "backend_ungemessen"
        aus["hinweis"] = (f"no memory measurements exist for backend '{kind}' yet — "
                          f"falling back to the measured throughput value ({vor}); "
                          f"the memory formula is NOT applied on this path")
        aus["rechenweg"] = f"{kind}: no measurements -> throughput value {vor}"
        return _nutzer_wahl(aus)
    if gesamt <= 0:
        if s["mass"] == "vram":
            # .531 FAIL-CLOSED (Defekt 7): bis .530 fiel dieser Zweig auf den
            # Durchsatz-Vorschlag zurueck — auf CUDA also auf DREI Straenge ohne
            # jeden Deckel, genau in der Lage, in der wir ueber die Karte gar
            # nichts wissen. Das ist die Richtung, in der der Feldvorfall vom
            # 15.09. lag. Jetzt: ein Strang, Anker-Deckel, rot.
            return _fail_closed(aus, kind, vor,
                                "no card size readable (nvidia-smi total is 0)")
        aus["grund"] = "keine_grenze"
        aus["hinweis"] = (f"no readable machine limit (no cgroup memory.max, no "
                          f"nvidia-smi total) — the memory formula cannot be applied; "
                          f"falling back to the measured throughput value ({vor}). "
                          f"Set a container memory limit to get the computed value")
        aus["rechenweg"] = f"{kind}: no readable limit -> throughput value {vor}"
        return _nutzer_wahl(aus)
    if s["mass"] == "vram" and max(0, int(frei_gemessen_mb or 0)) <= 0:
        # Die Karte ist da, sagt aber nicht, was frei ist (nvidia-smi fehlt,
        # haengt oder antwortet unlesbar). Eine Planung ohne Messwert waere auf
        # diesem Mass eine Behauptung — s. o.
        return _fail_closed(aus, kind, vor,
                            "free card memory not measurable (no usable "
                            "nvidia-smi answer)")
    res = reserve_strang_mb(gesamt, reserve_wunsch)
    aus["reserve_quelle"] = reserve_quelle_mb(reserve_wunsch)
    dienst = s["dienst_mb"]
    wae = waechter_posten_mb(n_waechter, kind)
    wae_abzug, wae_grund = (waechter_abzug_mb(n_waechter, kind, engine_alter_s)
                            if s["mass"] == "vram" else (wae, "ram-Zweig"))
    frei_gerechnet = gesamt - res - dienst - wae
    frei = frei_gerechnet
    frei_quelle = "gerechnet"
    gem = max(0, int(frei_gemessen_mb or 0))
    # .534 (NB-2): WAS DER LAUFENDE WORKER SELBST HAELT, IST KEIN FREMDVERBRAUCH.
    # `frei_gemessen_mb` ist `memory.free` der Karte im JETZT — laeuft bereits ein
    # Worker, liegt sein Kartenanteil darin als BELEGT. Die Leiter plant daneben
    # den Worker von null auf (basis + strang + geometrie), also denselben
    # Speicher ein zweites Mal. Solange die Zahl nur einen Prozess-START deckt,
    # faellt das nicht auf (da laeuft keiner); fuer die Aufstiegs-Frage im Betrieb
    # ist es der Unterschied zwischen „passt" und „passt nicht", und zwar immer in
    # die klemmende Richtung: die Leiter konnte im Betrieb nie wachsen. Gemessen
    # auf der 6-GB-Karte am 15.09.: 6143 MiB frei vor dem Start, 5044 MiB frei
    # waehrend des Laufs bei 738 MiB eigenem Plateau. Es ist dieselbe Regel, die
    # fuer Dienst und Live-Engine schon darunter steht — wer zur Messzeit auf der
    # Karte liegt, wird nicht ein zweites Mal abgezogen.
    # Die ROHE Messung bleibt `gem` — sie steht so im Rechenweg. Verrechnet wird
    # `gem_plus`, und der Zuschlag steht als eigene Zahl daneben.
    # .535: WAS DER LAUFENDE WORKER HAELT, KOMMT AUS DER TABELLE. `gem` ist
    # `memory.free` im JETZT — laeuft schon ein Worker, liegt sein Anteil darin
    # als BELEGT, waehrend die Leiter ihn daneben von null auf plant. Derselbe
    # Speicher zaehlte zweimal, und zwar immer klemmend: die Zahl sank unter
    # Last und stieg im Leerlauf, /health flatterte (Feldbefund 15.09. 18:06:
    # frei 10578 im Leerlauf gegen 8590 unter Last, n sprang zwischen 3 und 2).
    # Zurueckgerechnet wird deshalb der TABELLENWERT der laufenden Stufe — eine
    # feste Zahl, die nicht mit der Last atmet. Die Prozess-Sonde misst
    # weiterhin und steht als Diagnose in /health, aber sie plant NICHT mit
    # (nie beides, sonst zaehlt derselbe Speicher wieder doppelt).
    # GEKLEMMT an dem, was die Karte ueberhaupt belegt hat, abzueglich der
    # Posten fuer Dienst und Waechter: mehr als das kann der Worker nicht
    # halten, und eine Rueckrechnung ueber die Wirklichkeit hinaus waere
    # dieselbe Klasse Fehler in die andere Richtung.
    eigen_lauf, eigen_quelle = 0, None
    if s["mass"] == "vram" and gem > 0 and int(laufend_n or 0) > 0:
        _geplant = tabelle_summe(int(laufend_n))
        _rest = max(0, gesamt - gem - dienst - wae)
        eigen_lauf = min(int(_geplant), int(_rest))
        eigen_quelle = "tabelle" if eigen_lauf else None
    gem_plus = gem + eigen_lauf
    aus["laufend_eigen_mb"] = eigen_lauf
    aus["laufend_eigen_quelle"] = eigen_quelle
    # Was die PROZESS-SONDE im selben Moment gemessen hat — reine Diagnose
    # (/health), geht seit .535 nicht mehr in die Planung ein.
    aus["laufend_eigen_gemessen_mb"] = max(0, int(laufend_eigen_mb or 0))
    if gem > 0 and s["mass"] == "vram":
        # .531 AUF KARTEN-BACKENDS GILT DER MESSWERT, nicht das Minimum aus
        # Messung und Posten-Rechnung. Der Grund ist genau die Regel oben: die
        # Posten-Rechnung zieht Dienst UND Waechter ab, obwohl beide zur Messzeit
        # schon auf der Karte liegen koennen — als Klemme haette sie damit
        # dauerhaft denselben Speicher zweimal berechnet und der 6-GB-Karte ohne
        # Waechter einen Strang weggenommen, der am 14.09. sauber lief.
        # Was die Klemme frueher abfing (der Messwert wird VOR dem Start der
        # Waechter genommen und ist dann zu optimistisch), erledigt jetzt
        # `waechter_abzug_mb` ausdruecklich: solange die Engine jung oder aus ist,
        # bleibt ihr voller Posten reserviert.
        # Die gerechnete Zahl bleibt im Ergebnis stehen — sie ist die
        # Vergleichsgroesse, nicht mehr die Grenze.
        frei, frei_quelle = gem_plus - res - wae_abzug, "gemessen"
    elif gem > 0:
        # Der Messwert ist das, was die Karte JETZT noch hergibt — Fremd-
        # verbraucher inbegriffen. Die Reserve bleibt auch auf ihm stehen, sie
        # ist nicht vergebbar (s. RESERVE_STRANG_*).
        # .531 auf Karten-Backends: vom GEMESSENEN Wert geht nur ab, was zur
        # Messzeit NOCH NICHT auf der Karte lag.
        #   * Der DIENSTPROZESS liegt immer schon darauf — er startet den Worker,
        #     es gibt ihn also zwangslaeufig vor der Messung. Sein Posten steckt
        #     im Messwert; ein zweiter Abzug waere derselbe Speicher zweimal.
        #   * Die LIVE-ENGINE ist der Grenzfall: sie kann binnen Sekunden
        #     dazukommen (WL3-T6). Solange sie jung oder aus ist, wird ihr Posten
        #     reserviert; ist sie warm, steckt sie im Messwert (s.
        #     `waechter_abzug_mb`).
        # Auf der GERECHNETEN Seite bleiben beide Posten stehen — dort ist nichts
        # gemessen, was sie schon enthalten koennte.
        frei_gemessen_netto = (gem_plus - res - wae_abzug if s["mass"] == "vram"
                               else gem - res)
        if frei_gemessen_netto < frei:
            frei, frei_quelle = frei_gemessen_netto, "gemessen"
    aus.update({"reserve_mb": res, "dienst_mb": dienst, "waechter_mb": wae,
                "frei_mb": frei, "frei_gerechnet_mb": frei_gerechnet,
                "frei_quelle": frei_quelle, "waechter_abzug_mb": wae_abzug,
                "waechter_abzug_grund": wae_grund,
                "engine_alter_s": engine_alter_s})
    if s["mass"] == "vram":
        return _kartenhaushalt(aus, s, kind, frei, vor, gesamt,
                               n_waechter, gem, res, dienst, wae)
    # Der groesste Strang-Satz, der noch hineinpasst — hoechstens der Vorschlag.
    passt = 0
    for n in range(1, vor + 1):
        if fussabdruck_mb(n, kind, g_zusatz) <= frei:
            passt = n
        else:
            break
    # MINDESTENS EINER. Ein Dienst mit null Rechenstraengen waere kein Schutz,
    # sondern ein Ausfall; reicht der Speicher rechnerisch nicht einmal fuer
    # einen, laeuft er trotzdem mit einem und sagt es.
    n = max(1, min(vor, passt))
    aus["n"] = n
    aus["fussabdruck_mb"] = fussabdruck_mb(n, kind, g_zusatz)
    if passt < 1:
        aus["grund"] = "speicher_knapp"
        aus["hinweis"] = (f"the memory formula does not even fit one compute thread "
                          f"({aus['fussabdruck_mb']} MB needed, {frei} MB free after "
                          f"reserve/service/guards) — running with one anyway, watch "
                          f"for out-of-memory errors")
    elif n < vor:
        aus["grund"] = "speicher"
    else:
        aus["grund"] = "durchsatz" if passt == vor else "speicher"
    einheit = "MiB" if s["mass"] == "vram" else "MB"
    if frei_quelle == "gemessen":
        frei_text = (f"{gem} {einheit} really free on the card (measured) - "
                     f"{res} reserve ({aus.get('reserve_quelle') or 'formel'}) "
                     f"= {frei} {einheit} free, less than the "
                     f"{frei_gerechnet} {einheit} the posten sum "
                     f"({gesamt} - {res} reserve - {dienst} service - {wae} "
                     f"guards({aus['waechter_n']})) would have allowed — free "
                     f"measured instead of computed")
    else:
        frei_text = (f"{gesamt} - {res} reserve "
                     f"({aus.get('reserve_quelle') or 'formel'}) - {dienst} service "
                     f"- {wae} guards({aus['waechter_n']}) = {frei} {einheit} free"
                     + (f" (measured free {gem} {einheit} was not tighter)"
                        if gem > 0 else ""))
    aus["rechenweg"] = (
        f"{kind}/{s['mass']}: {frei_text}; "
        f"footprint({n}) = {aus['fussabdruck_mb']} {einheit}; "
        f"throughput value {vor} -> {n} thread(s) ({aus['grund']})")
    return _nutzer_wahl(aus)


def _nutzer_wahl(aus):
    """Die ausdrueckliche Nutzer-Zahl ueber das Formel-Ergebnis legen.

    EINE Stelle fuer alle Wege (auch fuer die beiden, auf denen die Formel gar
    nicht rechnen konnte) — sonst hinge die Nutzer-Wahl an drei Rueckgabepunkten
    und einer davon wuerde sie irgendwann vergessen.

    Das Formel-Ergebnis bleibt als `formel_n` stehen. Es wird nicht ueberschrieben,
    weil beide Zahlen zusammen die Auskunft sind: 'du hast 3 gewaehlt, gerechnet
    sind 2'. Eine Zahl allein waere entweder Bevormundung oder blindes Gehorchen.

    .531, DIE EINE STELLE (Konzept §9.1): auf Backends mit eigenem Kartenspeicher
    ist die Nutzer-Zahl eine OBERGRENZE der Leiter und kein Zwang ueber den
    Deckel hinaus. Das nimmt den 14.09.-Entscheid fuer diese Backends zurueck,
    und zwar hier und nirgends sonst — faellt der Entscheid anders, ist es diese
    Stelle plus ein Probenfall. Auf Container-RAM-Backends (Intel) bleibt alles
    wie am 14.09.: dort GILT die Zahl, auch ueber der Formel.

    .534 (Inhaber 15.09., ausdruecklich): der Testschalter „Nutzer-Zahl darf die
    Leiter auf Karten-Backends auch nach OBEN ueberstimmen" wurde erwogen und
    VERWORFEN — der richtige Weg gegen zu kleine Leitern ist nicht der Zwang,
    sondern ein belastbarer Preis. .535 hat ihn geliefert: die Messtabelle oben
    (gemessen an zwei Karten, je Posten Maximum + 10 %) statt der Anker einer
    fremden. Diese Stelle bleibt deshalb, wie .531 sie angelegt hat."""
    aus["formel_n"] = aus.pop("_formel_n_vram", None) or aus["n"]
    wunsch = max(0, int(aus.get("nutzer_n") or 0))
    if wunsch <= 0:
        return aus                                    # Vorgabe: die Formel gilt
    if aus.get("mass") == "vram":
        # Die Leiter hat die Zahl als Obergrenze schon eingerechnet; hier wird
        # sie nur noch gemeldet. Ein `max()` waere an dieser Stelle genau der
        # Fehler, den .531 abstellt.
        if wunsch > STRAENGE_MAX:
            aus["deckel_meldung"] = (
                f"worker_straenge={wunsch} is above the hard ceiling of "
                f"{STRAENGE_MAX} compute threads and was capped to "
                f"{STRAENGE_MAX} — beyond that no measured setup got faster, it "
                f"would only cost memory")
        n = min(wunsch, aus["n"])
        if wunsch > aus["formel_n"]:
            aus["unter_formel"] = (
                f"worker_straenge={wunsch} is above what the card budget carries "
                f"({aus['formel_n']} thread(s)) — on this backend your setting is "
                f"an UPPER LIMIT, not a forced value: the worker builds what fits "
                f"and shows both numbers. Free card memory (fewer live watchers) "
                f"or set worker_vram_mb if you want a different cap")
        elif n < aus["formel_n"]:
            aus["grund"] = "nutzer"
        aus["n"] = n
        aus["rechenweg"] = (f"{aus['rechenweg']}; user setting worker_straenge="
                            f"{wunsch} (upper limit) -> {n} thread(s)")
        return aus
    n = min(wunsch, STRAENGE_MAX)
    if wunsch > STRAENGE_MAX:
        aus["deckel_meldung"] = (
            f"worker_straenge={wunsch} is above the hard ceiling of "
            f"{STRAENGE_MAX} compute threads and was capped to {STRAENGE_MAX} — "
            f"beyond that no measured setup got faster, it would only cost memory")
    if n > aus["formel_n"]:
        aus["ueber_formel"] = (
            f"worker_straenge={n} is above what the memory formula computes for "
            f"this machine ({aus['formel_n']}) — your setting is used as asked. "
            f"Watch for out-of-memory errors: a thread that runs out is reported "
            f"as a failed job, the other jobs and the live watchers keep running")
    aus["n"] = n
    aus["grund"] = "nutzer"
    aus["rechenweg"] = (f"{aus['rechenweg']}; user setting worker_straenge="
                        f"{wunsch} -> {n} thread(s)")
    return aus


# Wie viele Clip-GEOMETRIEN in den Ankern oben schon stecken. Der gt5-Mix, aus dem
# alle Stuetzwerte stammen, fuhr 1080p UND 4K — die Anker tragen also zwei
# Aufloesungen, und `geometrie_mb` wird erst fuer die DRITTE faellig (so steht es
# bei GEOMETRIE_OV_MB und in fussabdruck_mb `g_zusatz`). Die Zahl ist damit
# abgelesen, nicht gesetzt.
GEOMETRIEN_IN_ANKERN = 2


def geometrien_deckel(kind, n_straenge, n_waechter, gesamt_mb, g_zusatz=0):
    """WIE VIELE CLIP-GEOMETRIEN DIESER WORKER GLEICHZEITIG HALTEN DARF (W2-B29).
    -> (n, rechenweg) · n = 0 heisst „nicht ableitbar, also kein Deckel".

    NUR NOCH FUER CONTAINER-RAM-BACKENDS (.531): auf Karten-Backends kommt die
    Zahl aus der LEITER, aus demselben `n` und demselben Budget wie die
    Strang-Zahl (`straenge()['geometrien_max']`). Zwei getrennt gebaute
    Rechnungen fuer dasselbe Konto waren Defekt 4 der Diagnose — diese hier
    rechnete den Geometrie-Platz aus `gesamt`, waehrend die Strang-Zahl aus dem
    GEMESSENEN freien Platz kam, und gab auf der vollen Feldkarte Geometrien
    frei, die es nicht mehr gab.

    DAS PROBLEM, das der Deckel loest: Geometrien entstehen zur LAUFZEIT (jede neue
    Clip-Groesse baut ihre eigenen Graphen plus je Rechenstrang einen Puffersatz),
    und bis E2d gab der Prozess nie eine zurueck. Die Speicher-Formel plant aber mit
    einer ENDLICHEN Zahl (`g_zusatz`) — eine Anlage mit wechselnden Substreams oder
    eingespielten Fremd-Clips laeuft ihr also davon.

    DIE RECHNUNG NIMMT NICHTS NEUES AN: was nach Reserve, Dienst, Waechtern und dem
    Fussabdruck der Straenge (bei den in den Ankern enthaltenen Aufloesungen) noch
    frei ist, geteilt durch den gemessenen Posten je zusaetzlicher Geometrie. Dazu
    die Geometrien, die in den Ankern schon stecken. Untergrenze ist deshalb
    GEOMETRIEN_IN_ANKERN: weniger duerfte der Prozess gar nicht halten, ohne bei
    jedem Wechsel zwischen 1080p und 4K neu zu kompilieren (gemessen 24-36 s).

    Backends ohne Messung (cpu/migraphx) und Maschinen ohne lesbare Groesse
    bekommen 0 — dann gibt es KEINEN Deckel und der Dienst sagt das laut. Eine
    geratene Zahl waere hier schlimmer als keine (dieselbe Regel wie bei den
    Stuetzwerten)."""
    s = stuetzwerte(kind)
    if not s:
        return 0, f"backend {kind!r} has no memory measurements — no geometry cap"
    gesamt = int(gesamt_mb or 0)
    if gesamt <= 0:
        return 0, "machine memory not readable — no geometry cap"
    je = int(s["geometrie_mb"] or 0)
    if je <= 0:
        return 0, "no measured cost per geometry — no geometry cap"
    belegt = (s["dienst_mb"] + waechter_posten_mb(n_waechter, kind)
              + (fussabdruck_mb(n_straenge, kind, g_zusatz) or 0))
    frei = gesamt - reserve_strang_mb(gesamt) - belegt
    zusatz = max(0, int(frei // je))
    n = GEOMETRIEN_IN_ANKERN + zusatz
    return n, (f"{gesamt} MB total - {reserve_strang_mb(gesamt)} MB reserve - "
               f"{belegt} MB (service + watchers + {n_straenge} thread(s)) = "
               f"{frei} MB free / {je} MB per geometry = {zusatz} extra + "
               f"{GEOMETRIEN_IN_ANKERN} already in the anchors -> {n}")


def wache_grenze_rechnung(kind, n_straenge, n_waechter, gesamt_mb=0, g_zusatz=0,
                          konfiguriert_mb=0, maschine_ram_mb=0,
                          nutzer_gesetzt=False):
    """Die Politik-Grenze fuer die Speicher-Wache des Dienstes (Job-Feld
    `fussabdruck_max_mb`) MIT IHREN POSTEN. -> dict.

    -> {"mb", "quelle", "hinweis", "posten", "rechenweg"}
       quelle: "formel"        die Strang-Formel rechnet in RAM (Intel)
               "wirt-reserve"  der Maschinen-RAM ist lesbar -> Maschine minus
                               Reserve (.529, s. u.)
               "config+posten" ERSATZ, wenn der Maschinen-RAM NICHT lesbar ist:
                               gemessene Container-Posten + konfiguriertes
                               Worker-Budget (cuda/cpu/migraphx, .528)
               "config"        der Betreiber hat `worker_rss_max_mb` bewusst
                               auf einen Nicht-Werkswert gestellt — dann gilt
                               SEINE Zahl (plus die gemessenen Nachbarn), auch
                               wenn der Maschinen-RAM lesbar waere
               "keine"         kein Budget gesetzt -> Politik-Regel AUS

    WAS SICH IN .529 GEAENDERT HAT (Feldvorfall Feldtester-Anlage 15.09. lokal
    ~05:46 AEST, Rundordner .suslik_tmp/gt5/runs/feldtester_baseline_526_20260914/):
    die .528-Rechnung addierte gemessene Container-Posten und das konfigurierte
    Je-Worker-Budget — auf einer Anlage mit FUENF Waechtern ergab das
    1026 + 2293 + 5 x 587 + 4096 = 10350 MB. Der Container kam auf 10384 MB und
    die Wache fuhr den Worker geordnet herunter, OBWOHL der Wirt rund 48 GB RAM
    hat: die Grenze haengt in dieser Rechnung an der WAECHTERZAHL und am Budget,
    nicht an der Maschine. Umgekehrt konnte dieselbe Summe auf dem 8-GB-Notebook
    ueber der Maschine liegen (8589 gegen 8192) — eine Zusage, die der
    OOM-Killer vorher kassiert. Beide Schiefstaende haben DIESELBE Ursache:
    es wurde alles gerechnet ausser der Groesse, um die es geht.

    IST DER MASCHINEN-RAM LESBAR, gilt deshalb dieselbe Regel wie im ram-Zweig
    darunter — Maschine minus der Reserve der Strang-Formel (`reserve_strang_mb`,
    10 % / mindestens 512 MB, KEINE neue Zahl, dieselbe Konstante und dieselbe
    Untergrenze). Das ist die Groesse, die der Kernel wirklich durchsetzt, und
    sie steht in DEMSELBEN Mass wie die Wache misst (Systemspeicher).

    WOHER DER MASCHINEN-RAM KOMMT, und woher NICHT: aus der eigenen cgroup
    (`memory.max`, das ist die Zahl, die `docker info` als MemTotal meldet).
    NIE aus /proc/meminfo — das zeigt im Container den Wirt und ist als Quelle
    hier verboten (wiki/maschinen.md, dieselbe Regel wie in
    `verifyd._maschine_speicher_mb`). EHRLICHE GRENZE, die im Feld zieht: laeuft
    der Container ohne `--memory` und liegt das echte Limit auf einem von innen
    unsichtbaren Eltern-cgroup, ist der Maschinen-RAM NICHT lesbar — dann bleibt
    es bei der .528-Rechnung, und der Feldvorfall oben waere mit diesem Zweig
    allein NICHT geheilt. Das steht hier, damit niemand die Heilung annimmt,
    ohne die Voraussetzung geprueft zu haben.

    DER BETREIBER GEWINNT WEITER: hat er `worker_rss_max_mb` bewusst auf einen
    Nicht-Werkswert gestellt, gilt seine Zahl (Quelle "config"), denn sie ist
    eine Ansage und kein Vorgabewert. 0 heisst weiterhin AUS. Auch hier eine
    ehrliche Grenze: wer den Werkswert von Hand noch einmal hinschreibt, ist von
    der Vorgabe nicht unterscheidbar — dann rechnet die Maschine.

    WARUM DAS NICHT IMMER DIE FORMEL SEIN KANN, und warum das gesagt werden muss:
    die Wache drueben misst anon + cgroup-shmem, also SYSTEMSPEICHER. Auf Intel
    ist das genau die Groesse, die diese Formel rechnet — dort kommt die Grenze
    aus der Formel. Auf CUDA rechnet die Formel KARTENSPEICHER; der RAM-Bedarf
    des WORKERS ist auf diesem Weg nicht gemessen.

    WAS SICH IN .528 GEAENDERT HAT (Feldfund NB-Abnahme 14.09., s.
    CONTAINER_RAM_POSTEN): dort stand bis .527 die konfigurierte
    `worker_rss_max_mb` ALLEIN als Grenze. Die behaelt ihre Bedeutung — sie ist
    das Budget EINES Workers —, aber sie ist nicht die Grenze eines
    CONTAINER-Masses. Die Nachbarn im selben Speicher-Konto sind gemessen, also
    werden sie ADDIERT statt stillschweigend im Budget unterstellt:

        Grenze = Dienst + Live-Engine + n x Waechter-Decoder
                 + Straenge x worker_rss_max_mb

    (.534: der letzte Posten mal der STRANGZAHL — s. dort. Bis .533 stand er
    einmal da, und die Startdiagnose des Dienstes rechnete daneben schon mit
    N x Budget.)

    Auf die gemessenen Posten kommt KEINE Marge: `worker_rss_max_mb` ist schon
    eine Politik-Zahl mit eigener Luft (Default 4096 gegen warm real ~1,9 GB
    VmRSS), und die Posten stehen ohnehin in der groesseren Lesart (s. dort).
    Eine zweite Marge daraufzulegen hiesse, dieselbe Vorsicht zweimal zu zahlen.

    KEIN DECKEL AUF `gesamt_mb` in diesem Zweig, und das ist Absicht: auf CUDA
    ist `gesamt_mb` der KARTENSPEICHER. Ihn gegen eine RAM-Grenze zu klemmen
    waere genau derselbe Masse-Fehler in klein (auf dem NB: 6144 MiB Karte gegen
    8 GB Wirt-RAM). Der ram-Zweig darunter klemmt weiter, dort ist `gesamt_mb`
    wirklich die Maschinen-Groesse desselben Masses.

    EHRLICHE GRENZE, benannt: eine so gerechnete Grenze kann ueber dem liegen,
    was die Maschine an RAM ueberhaupt hat (NB: 8589 gegen 8 GB). Dann faengt der
    Kernel bzw. die cgroup-Regel der Wache zuerst — was in Ordnung ist, denn
    diese Politik-Zahl soll ein LECK fangen, nicht die Maschine verwalten. Wer
    sie eng haben will, setzt `worker_rss_max_mb` bewusst kleiner; wer sie ganz
    aus haben will, setzt 0 (dann wacht nur die cgroup-Regel)."""
    s = stuetzwerte(kind)
    kfg = max(0, int(konfiguriert_mb or 0))
    if not s or s["mass"] != "ram":
        grund = ("this backend has no memory measurements yet" if not s else
                 "the thread formula measures card memory here, the process guard "
                 "measures system memory — the worker's RAM footprint is unmeasured "
                 "on this backend")
        if kfg <= 0:
            return {"mb": 0, "quelle": "keine", "posten": {},
                    "rechenweg": f"{kind}: worker_rss_max_mb=0 -> policy rule off",
                    "hinweis": (f"the footprint POLICY rule is OFF: {grund}, and "
                                f"worker_rss_max_mb is 0 — only the cgroup rule "
                                f"guards this process (it aborts open jobs when the "
                                f"container is about to run out). Set "
                                f"worker_rss_max_mb to a per-worker budget to get a "
                                f"policy limit back")}
        grund_mb, posten = container_ram_grundlast_mb(kind, n_waechter)
        # .534: `worker_rss_max_mb` ist eine JE-WORKER-Zahl aus der Zeit, in der
        # jeder Platz ein eigener Prozess war. Der neue Worker ist EIN Prozess mit
        # N Rechenstraengen — die getreue Uebersetzung ist deshalb N x Budget, und
        # genau so rechnet die Startdiagnose des Dienstes seit .528 („guard scales
        # to N x …"). Bis .533 tat sie das ALLEIN: die Wache im Worker bekam das
        # Budget EINMAL, und beide Zahlen widersprachen sich. Im Feldtest der .533
        # (zwei Straenge, Werkswert) riss die Grenze nach dem ersten Ereignis, weil
        # sie einen Ein-Strang-Prozess bemass. Seitdem ist DIESE Rechnung die eine
        # Quelle fuer beide Seiten.
        n_str = max(1, int(n_straenge or 0))
        budget = kfg * n_str
        posten = dict(posten, worker_budget_mb=kfg, straenge=n_str,
                      worker_budget_gesamt_mb=budget, grundlast_mb=grund_mb,
                      ersatz_mb=grund_mb + budget)
        ram = max(0, int(maschine_ram_mb or 0))
        # .529: die Maschine schlaegt die Postensumme — ausser der Betreiber hat
        # bewusst eine eigene Zahl gesetzt. Die Postensumme bleibt als `ersatz_mb`
        # in den Posten stehen, damit an der Oberflaeche BEIDE Zahlen lesbar sind
        # (was gilt und was ohne Maschinen-RAM gegolten haette).
        if ram > 0 and not nutzer_gesetzt:
            res = reserve_strang_mb(ram)
            mb = max(1, ram - res)
            posten = dict(posten, maschine_ram_mb=ram, reserve_mb=res,
                          reserve_anteil=RESERVE_STRANG_ANTEIL,
                          reserve_min_mb=RESERVE_STRANG_MIN_MB)
            return {"mb": mb, "quelle": "wirt-reserve", "posten": posten,
                    "rechenweg": (f"{kind}/host-ram: {ram} MB machine memory "
                                  f"(own cgroup, the number docker info reports as "
                                  f"MemTotal) - {res} MB reserve -> {mb} MB "
                                  f"(instead of the posten sum {grund_mb + budget} "
                                  f"MB)"),
                    "hinweis": (f"footprint limit {mb} MB = {ram} MB machine memory "
                                f"minus a {res} MB reserve, because {grund} — so the "
                                f"limit is tied to the MACHINE, not to the number of "
                                f"live watchers. Adding up the measured container "
                                f"neighbours plus the configured worker_rss_max_mb "
                                f"per compute thread would have given "
                                f"{grund_mb + budget} MB here. Set "
                                f"worker_rss_max_mb to a value of your own if you "
                                f"want a tighter budget, 0 to switch the policy rule "
                                f"off")}
        quelle = "config" if (ram > 0 and nutzer_gesetzt) else "config+posten"
        weg = (f"{kind}/ram-posten: {posten.get('dienst_mb', 0)} service + "
               f"{posten.get('waechter_engine_mb', 0)} live engine + "
               f"{posten.get('waechter_n', 0)} x {posten.get('waechter_decoder_mb', 0)} "
               f"guard decoder = {grund_mb} MB container base + {n_str} x {kfg} MB "
               f"configured worker_rss_max_mb (one per compute thread) = {budget} MB "
               f"-> {grund_mb + budget} MB")
        if quelle == "config":
            weg += (f" (your own worker_rss_max_mb wins over the machine-derived "
                    f"limit of {ram - reserve_strang_mb(ram)} MB)")
        return {"mb": grund_mb + budget, "quelle": quelle, "posten": posten,
                "rechenweg": weg,
                "hinweis": (f"footprint limit {grund_mb + budget} MB = {grund_mb} MB "
                            f"measured container base (service, live engine and "
                            f"{posten.get('waechter_n', 0)} guard decoder(s)) + "
                            f"{n_str} x {kfg} MB configured worker_rss_max_mb, "
                            f"because {grund}. "
                            f"The configured value keeps its PER-WORKER meaning and "
                            f"is counted once per COMPUTE THREAD, because the new "
                            f"worker runs {n_str} of them in ONE process; the "
                            f"guard measures the WHOLE container, so the measured "
                            f"neighbours are added instead of being assumed inside it"
                            + (". Your own setting is used as asked; the machine "
                               "memory would have given a different limit"
                               if quelle == "config" else
                               ". The machine's own memory size is NOT readable here "
                               "(no cgroup memory limit set, and /proc/meminfo shows "
                               "the host, not this container) — set a container "
                               "memory limit to get a machine-derived limit"))}
    roh = (s["dienst_mb"] + waechter_posten_mb(n_waechter, kind)
           + (fussabdruck_mb(n_straenge, kind, g_zusatz) or 0))
    mb = int(round(roh * (1.0 + WACHE_MARGE_ANTEIL)))
    gesamt = int(gesamt_mb or 0)
    gedeckelt = False
    if gesamt > 0:
        # Nie ueber das, was die Maschine ueberhaupt hergibt — sonst waere die
        # Grenze eine Zusage, die der OOM-Killer vorher kassiert. Gilt NUR hier:
        # in diesem Zweig misst `gesamt_mb` dasselbe wie die Grenze (RAM).
        if gesamt - reserve_strang_mb(gesamt) < mb:
            mb, gedeckelt = gesamt - reserve_strang_mb(gesamt), True
    mb = max(1, mb)
    posten = {"dienst_mb": s["dienst_mb"],
              "waechter_n": max(0, int(n_waechter or 0)),
              "waechter_mb": waechter_posten_mb(n_waechter, kind),
              "fussabdruck_mb": fussabdruck_mb(n_straenge, kind, g_zusatz) or 0,
              "roh_mb": roh, "marge_anteil": WACHE_MARGE_ANTEIL,
              "maschine_gedeckelt": gedeckelt, "beleg": s["beleg"]}
    return {"mb": mb, "quelle": "formel", "posten": posten, "hinweis": None,
            "rechenweg": (f"{kind}/formel: {posten['dienst_mb']} service + "
                          f"{posten['waechter_mb']} guards({posten['waechter_n']}) + "
                          f"{posten['fussabdruck_mb']} threads({max(0, int(n_straenge or 0))}) "
                          f"= {roh} MB x {1.0 + WACHE_MARGE_ANTEIL:.2f} margin -> {mb} MB"
                          + (" (capped by machine size)" if gedeckelt else ""))}


def wache_grenze_mb(kind, n_straenge, n_waechter, gesamt_mb=0, g_zusatz=0,
                    konfiguriert_mb=0, maschine_ram_mb=0, nutzer_gesetzt=False):
    """Nur Zahl, Quelle und Hinweis der Rechnung oben — EINE Arithmetik, zwei
    Griffe. -> (mb, quelle, hinweis)"""
    r = wache_grenze_rechnung(kind, n_straenge, n_waechter, gesamt_mb, g_zusatz,
                              konfiguriert_mb, maschine_ram_mb, nutzer_gesetzt)
    return r["mb"], r["quelle"], r["hinweis"]
