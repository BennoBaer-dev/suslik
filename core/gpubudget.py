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

from core import cuda_budget as _cuda

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


# Bestehender Mindestabstand für geordnete Druckneustarts.
DRUCK_NEUSTART_ABSTAND_S = 600

# Ab wann der Anteil der Live-Engine im GEMESSENEN `memory.free` wirklich drin
# ist. Im Feld kamen Engine und fuenf Decoder binnen 15 s hoch (WL3-T6); 60 s
# sind das Vierfache davon und damit die vorsichtige Kante. Solange die Engine
# juenger ist — oder gar nicht laeuft —, wird ihr voller Posten RESERVIERT, denn
# er kann noch kommen. Ist sie laenger da, steht ihr Speicher schon im Messwert
# und ein zweiter Abzug waere doppelt gezaehlt.
LIVE_WARM_S = 60

# --- .544 M1: DAS FREI-BAND STATT DES MOMENTWERTS ---------------------------
# ANLASS, in Feldzahlen (Feldtester-Anlage, RTX 3060 mit 12288 MiB, Werktag
# 21.09.2026, Belege Feldtester-Nachtauswertung 21.09.2026, Befund §4.4 im nicht getrackten Laborordner (s. stand.md)): die
# Leiter mass „frei" als EINE Momentaufnahme, sah 6 Straenge passen und baute
# sie mit 69 MiB Luft. Danach meldete die Takt-Wache im Worker 145 mal an EINEM
# Tag „frei unter Reserve" und beendete den Prozess — bei 381 bis 1226 MiB noch
# freiem Speicher. Der „Fremdverbraucher" waren die EIGENEN fuenf Live-Waechter,
# deren Verbrauch atmet: 4K-Decode, Nachtsicht-Umschaltung, Bewegungsschuebe.
# Die Momentaufnahme traf regelmaessig ein TAL dieser Welle und plante darauf.
#
# WAS SICH AENDERT: geplant wird auf dem MINIMUM des kartenweit freien Speichers
# ueber ein Fenster — der schlechteste Moment, den die Karte in dieser Zeit
# wirklich hatte, statt des Moments, in dem zufaellig gefragt wurde. Das ist
# dieselbe Hausregel wie ueberall hier: wo zwei Messungen streiten, nimmt die
# Formel die vorsichtigere.
#
# WARUM 600 s: die Quelle ist der Ringpuffer der Systemstatistik
# (`core.systemstat`, eine Zeile je `TAKT_S` = 60 s) — eine Zahl, die es schon
# gibt, keine neue Sonde. 600 s sind zehn seiner Takte, also zehn Stuetzstellen,
# und decken die Wellen, in denen die Waechter-Ausschlaege am 21.09. sichtbar
# wurden (die Ausstiege kamen in Buendeln ueber wenige Minuten). Kuerzer waere
# wieder fast ein Moment; laenger schleppte die Leiter Taeler mit, die die
# jetzige Konstellation gar nicht mehr hat (ein abgeschalteter Waechter wirkte
# dann eine halbe Stunde nach).
FREI_BAND_FENSTER_S = 600
# WIE VIELE STUETZSTELLEN ES MINDESTENS BRAUCHT. Unter drei ist es kein Band,
# sondern ein Moment mit Umweg — bei einem frischen Start (Ring noch leer), auf
# Anlagen ohne nvidia-smi im Ring oder nach einem Datenverlust. Dann faellt die
# Leiter LAUT auf den Momentwert zurueck (`frei_band_grund` in /health und im
# Rechenweg), statt so zu tun, als haette sie ein Band gemessen.
FREI_BAND_MIN_PROBEN = 3

# --- .544 M2/M3: DIE EINE WARTE-FRIST AUF FREIEN KARTENSPEICHER -------------
# SIE IST NICHT NEU. Bis .543 stand sie als `verifyd.KARTE_WARTE_FRIST_S` an
# genau einer Stelle (dem Start-Tor des Workers) und war dort richtig
# hergeleitet: ausdruecklich NICHT `worker_kern.BARRIERE_FRIST` (1800 s, die
# Frist einer Warmlauf-Barriere INNERHALB des Prozesses), sondern gegen den
# Platzwaechter gerechnet — der zieht einen Platz nach 120 s ohne Lebenszeichen
# ein, 45 s sind weniger als die Haelfte davon, und in der Schleife pulst es.
# SEIT .544 BRAUCHT SIE AUCH DER WORKER (M2: warten statt eine neue Geometrie zu
# bauen, solange fremder Druck steht; M3a: warten nach `karte_voll`, bevor der
# eine Retry faehrt). Zwei Prozesse, dieselbe Frage, dieselbe Zahl — deshalb
# steht sie ab jetzt HIER, und `verifyd` liest sie von hier. Ein zweites Literal
# im Worker waere genau die K3-Klasse (die Erweiterung erreicht nicht alle
# Stellen), die dieses Haus schon mehrfach bezahlt hat.
KARTE_WARTE_FRIST_S = 45.0


def frei_mess_kennung(aus):
    """WIE DER GEMESSENE FREI-WERT ZUSTANDE KAM — ein Satzstueck, EINE Stelle.

    Steht in beiden Rechenwegen (Karten- und RAM-Zweig). Ohne die gemeinsame
    Stelle stuende in einem von beiden irgendwann wieder „measured", waehrend
    die Zahl laengst aus dem Band kommt — genau die luegende Diagnose (K1).

    .546: ein VERWORFENES Band ist kein Band. Die Zahl daneben ist dann der
    Momentwert, und genau das muss dastehen — sonst laese sich der Rechenweg
    des Dienststarts wie eine 600-s-Messung, die er nicht ist."""
    if (aus or {}).get("frei_band_verworfen"):
        return "momentary value, band discarded"
    n = int((aus or {}).get("frei_band_n") or 0)
    if n >= FREI_BAND_MIN_PROBEN:
        return (f"band (min over {int(aus.get('frei_band_fenster_s') or 0)}s, "
                f"{n} samples)")
    return "measured"


def frei_vergleich_text(frei_mb, gerechnet_mb, einheit, posten_text=""):
    """GEMESSEN GEGEN GERECHNET — die Richtung kommt aus den ZAHLEN, nicht aus
    dem Zweig (.544 Teil 6, BEF-1 der CUDA-Abnahme 21.09.2026).

    Beide Rechenwege sagten bisher „less than", sobald der gemessene Wert
    gezogen hatte. Das stimmte, solange der Messwert nur KLEMMEN konnte; seit
    .531 gewinnt er auf Karten-Backends auch, wenn er GROESSER ist (s. den
    Zweig `s["mass"] == "vram"` in `straenge`). Auf dem CUDA-Testsystem stand
    deshalb `3512 MiB budget, less than the 2186 MiB …` im Rechenweg und in
    /health — die Zahlen daneben widersprachen dem eigenen Satz, und eine
    Gleichheit (`4386, less than the 4386`) las sich genauso falsch.

    EINE Stelle fuer beide Zweige, aus demselben Grund wie bei
    `frei_mess_kennung`: sonst steht der alte Satz irgendwann wieder in einem
    von beiden."""
    f, g = int(frei_mb or 0), int(gerechnet_mb or 0)
    p = f" ({posten_text})" if posten_text else ""
    if f < g:
        return (f"less than the {g} {einheit} the posten sum{p} would have "
                f"allowed — free measured instead of computed")
    if f > g:
        return (f"more than the {g} {einheit} the posten sum{p} would have "
                f"allowed — measured free wins over the computed value")
    return (f"as much as the {g} {einheit} the posten sum{p} would have "
            f"allowed — measured and computed agree")


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


def pflicht_preis_mb(kind, preise=None):
    """Liest den notwendigen CUDA-Erstzustand einschließlich eines Decoders.
    -> MiB; andere Backends verwenden ihre bestehenden RAM-Regeln."""
    return _cuda.state(preise)[0] + DECODER_CUDA_MB if kind == "cuda" else 0



def straenge_preis_mb(kind, n, preise=None):
    """Liest einen Gesamtzustand und berücksichtigt die bevorstehenden Decoder.
    -> MiB; keine Summierung alter Strang-/Geometriepreise."""
    if kind != "cuda" or int(n or 0) <= 0:
        return 0
    return _cuda.state(preise, int(n))[0] + int(n) * DECODER_CUDA_MB



def posten_ausserhalb_mb(kind, n_straenge):
    """Nennt die getrennten Decoderprozesse außerhalb der CUDA-Arena.
    -> (MiB, Herkunft); Kontext ist Bestandteil der gemessenen PID, kein zweiter Preis."""
    if kind != "cuda":
        return 0, {}
    dec = max(0, int(n_straenge or 0)) * DECODER_CUDA_MB
    return dec, {"decoder_mb":dec, "straenge":n_straenge, "gemessen":True,
                 "beleg":"decoder allowance; PID and arena are distinct"}



def mindest_preis_mb(kind, preise=None):
    """Liest den minimalen Erstbedarf ohne abgeleitete Postenpreise.
    -> MiB; identisch mit dem Einstrang-Startbedarf."""
    return pflicht_preis_mb(kind, preise)



def waechter_frei_mb(n_jetzt, n_weg, kind):
    """WAS DAS ABSCHALTEN VON `n_weg` WAECHTERN FREI MACHT. -> MB

    Aus den GEMESSENEN Posten (`waechter_posten_mb`), nicht aus einer eigenen
    Rechnung: die Engine traegt die Modelle EINMAL, jeder Waechter sein eigenes
    ffmpeg — der erste abgeschaltete Waechter gibt deshalb weniger her als der
    letzte, und eine lineare Schaetzung waere in beide Richtungen falsch.

    EHRLICHE GRENZE, benannt: das ist eine VORHERSAGE aus unseren Posten, keine
    Messung dieser Anlage ([[ersatzmessungen-sind-hypothesen]]). Ob wirklich so
    viel frei wird, zeigt erst der gemessene Frei-Wert danach — und genau
    deshalb entscheidet die Leiter beim naechsten Start neu, statt diese Zahl zu
    glauben."""
    n = max(0, int(n_jetzt or 0))
    weg = max(0, min(n, int(n_weg or 0)))
    if weg <= 0:
        return 0
    return max(0, waechter_posten_mb(n, kind) - waechter_posten_mb(n - weg, kind))


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
    """Begrenzt die gemeinsame Arena auf das Budget ohne bevorstehende Decoder.
    -> Positive MiB auf CUDA; die tatsächliche Materialisierung prüft natives Frei erneut."""
    if kind != "cuda":
        return 0
    return max(1, int(budget_mb or 0) - posten_ausserhalb_mb(kind,n_straenge)[0])



def leiter(kind, worker_budget_mb, vorschlag, nutzer_n=0, preise=None):
    """Liefert die CUDA-Auswahl ohne eine automatisch wachsende Einzelpreisleiter.
    -> Plan oder None für andere Backends; jeder Aufbau wird zusätzlich gemessen."""
    if kind != "cuda":
        return None
    return _cuda.ladder(int(worker_budget_mb or 0),nutzer_n,STRAENGE_MAX,preise,DECODER_CUDA_MB)



def geometry_plan(st, arena_mb, running_n=0, stock_known=True, prices=None, measured=None):
    """Ergaenzt die gewaehlte Leiter nach den Vorrang-Stufen um bezahlbare Geometrien.
    -> neuer Plan; Strangauswahl, Preise und Schutzentscheidungen bleiben erhalten."""
    return _cuda.geometry_plan(st, arena_mb, running_n, stock_known, measured)








def straenge(gesamt_mb, n_waechter, kind, vorschlag, g_zusatz=0, nutzer_n=0,
             frei_gemessen_mb=0, engine_alter_s=None,
             laufend_eigen_mb=0, reserve_wunsch=-1, laufend_n=0,
             frei_band=None, preise=None, running_geometries=None, measured=None):
    """Plant CUDA aus Messungen, andere Backends nach ihrer bestehenden RAM-Regel.
    -> Bestehendes Planformat mit Quelle, Grenzen und Fehlgrund."""
    vor = max(1, int(vorschlag or 1))
    s = stuetzwerte(kind)
    gesamt = int(gesamt_mb or 0)
    # .543: unlesbarer Wunsch = Automatik, und zwar HIER abgefangen. Ohne diesen
    # Griff braechte ein krummer Config-Wert die fruehen Rueckgabewege (die
    # `reserve_strang_mb` nie erreichen) neu zum Absturz.
    try:
        res_wunsch = int(reserve_wunsch if reserve_wunsch is not None else -1)
    except (TypeError, ValueError):
        res_wunsch = -1
    aus = {"n": vor, "kind": kind, "vorschlag": vor, "gesamt_mb": gesamt,
           "mass": (s or {}).get("mass"), "reserve_mb": 0, "dienst_mb": 0,
           "waechter_mb": 0, "waechter_n": max(0, int(n_waechter or 0)),
           "frei_mb": 0, "fussabdruck_mb": None, "g_zusatz": max(0, int(g_zusatz or 0)),
           # .529: welche der beiden Frei-Mengen gezogen hat, und beide Zahlen
           # daneben — eine Auskunft, die man nachrechnen kann.
           "frei_quelle": "gerechnet", "frei_gerechnet_mb": 0,
           "frei_gemessen_mb": max(0, int(frei_gemessen_mb or 0)),
           # .544 M1: WORAUF GEPLANT WURDE — das Band, sein Fenster, seine
           # Stuetzstellen und der Momentwert daneben. Alle vier stehen auf
           # JEDEM Rueckgabeweg (auch den frueh abbiegenden), denn ein fehlendes
           # Feld liest sich wie „kein Band" und waere dort eine Behauptung.
           "frei_band_mb": None, "frei_band_fenster_s": 0, "frei_band_n": 0,
           "frei_moment_mb": max(0, int(frei_gemessen_mb or 0)),
           "frei_band_grund": None,
           # .546: … und ob das Band auf diesem Weg VERWORFEN wurde. Auf jedem
           # Rueckgabeweg, aus demselben Grund wie die vier Felder darueber: ein
           # fehlendes Feld liest sich wie „das Band hat gegolten".
           "frei_band_verworfen": False,
           "laufend_eigen_mb": 0, "laufend_eigen_quelle": None,
           "reserve_quelle": "formel",
           # .543 (Issue #32): DER ROHE WUNSCH, auf JEDEM Rueckgabeweg — auch auf
           # den fruehen (fail-closed, keine lesbare Grenze), wo die Rechnung gar
           # nicht bis `reserve_strang_mb` kommt. Er ist nicht `reserve_mb` (das
           # ist die GERECHNETE Zahl in MiB), sondern der Config-Wert mit seiner
           # Semantik: -1 Automatik, 0 keine Reserve, sonst MiB. Der Dienst gibt
           # ihn von hier an den Worker-Prozess weiter, dessen Laufzeit-Wachen
           # sonst gegen die Automatik-Formel messen statt gegen die eingestellte
           # Reserve.
           "reserve_wunsch_mb": res_wunsch,
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
    if kind == "cuda":
        # MS1: alle aktiven CUDA-Wege vor der alten Postenrechnung abzweigen.
        why = _cuda.pair_reason(measured, gesamt) if laufend_n else None
        own = measured["own"]["mb"] if laufend_n and why is None else 0
        free = (measured["card"]["mb"] if laufend_n and why is None
                else max(0, int(frei_gemessen_mb or 0)))
        if isinstance(frei_band, dict) and frei_band.get("moment_mb") is not None and not laufend_n:
            free = max(0, int(frei_band["moment_mb"]))
        if gesamt <= 0 or frei_gemessen_mb is None:
            why = why or "native card memory unavailable"
        guards, guard_reason = waechter_abzug_mb(n_waechter, kind, engine_alter_s)
        aus.update(dienst_mb=s["dienst_mb"], waechter_mb=waechter_posten_mb(n_waechter, kind),
                   frei_gerechnet_mb=gesamt - _cuda.reserve(gesamt, res_wunsch)
                   - s["dienst_mb"] - waechter_posten_mb(n_waechter, kind),
                   engine_alter_s=engine_alter_s)
        result = _cuda.selection(aus, free, own, why, guards, guard_reason, laufend_n,
                               running_geometries, preise, STRAENGE_MAX, DECODER_CUDA_MB)
        for source, target in (("band_mb", "frei_band_mb"), ("fenster_s", "frei_band_fenster_s"),
                               ("n", "frei_band_n"), ("moment_mb", "frei_moment_mb"),
                               ("grund", "frei_band_grund")):
            if isinstance(frei_band, dict) and source in frei_band:
                result[target] = frei_band[source]
        result["frei_gemessen_mb"] = free
        if result.get("frei_band_mb") is not None:
            result["frei_band_verworfen"] = True
            result["frei_band_grund"] = "historical free band is diagnostic only; CUDA uses current native free"
            result["rechenweg"] += "; " + result["frei_band_grund"]
        result["laufend_eigen_gemessen_mb"] = laufend_eigen_mb
        result["rechenweg"] += "; " + frei_vergleich_text(
            result["worker_budget_mb"], result["frei_gerechnet_mb"], "MiB")
        return result
    _fb = frei_band if isinstance(frei_band, dict) else {}
    if _fb:
        aus["frei_band_mb"] = _fb.get("band_mb")
        aus["frei_band_fenster_s"] = int(_fb.get("fenster_s") or 0)
        aus["frei_band_n"] = int(_fb.get("n") or 0)
        aus["frei_band_grund"] = _fb.get("grund")
        if _fb.get("moment_mb") is not None:
            aus["frei_moment_mb"] = max(0, int(_fb.get("moment_mb") or 0))
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
        aus["grund"] = "keine_grenze"
        aus["hinweis"] = (f"no readable machine limit (no cgroup memory.max, no "
                          f"nvidia-smi total) — the memory formula cannot be applied; "
                          f"falling back to the measured throughput value ({vor}). "
                          f"Set a container memory limit to get the computed value")
        aus["rechenweg"] = f"{kind}: no readable limit -> throughput value {vor}"
        return _nutzer_wahl(aus)
    # .543: DERSELBE gepruefte Wert wie im Ergebnis oben, nicht der rohe. Sonst
    # entschieden die beiden Stellen bei einem krummen Config-Wert verschieden —
    # das Ergebnis saegte „Automatik", die Rechnung fiele mit ValueError.
    res = reserve_strang_mb(gesamt, res_wunsch)
    aus["reserve_quelle"] = reserve_quelle_mb(res_wunsch)
    dienst = s["dienst_mb"]
    wae = waechter_posten_mb(n_waechter, kind)
    wae_abzug, wae_grund = wae, "ram-Zweig"
    frei_gerechnet = gesamt - res - dienst - wae
    frei, frei_quelle = frei_gerechnet, "gerechnet"
    gem = max(0, int(frei_gemessen_mb or 0))
    if gem > 0 and gem - res < frei:
        frei, frei_quelle = gem - res, "gemessen"
    aus.update({"reserve_mb": res, "dienst_mb": dienst, "waechter_mb": wae,
                "frei_mb": frei, "frei_gerechnet_mb": frei_gerechnet,
                "frei_quelle": frei_quelle, "waechter_abzug_mb": wae_abzug,
                "waechter_abzug_grund": wae_grund,
                "engine_alter_s": engine_alter_s})
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
        frei_text = (f"{gem} {einheit} really free on the card "
                     f"({frei_mess_kennung(aus)}) - "
                     f"{res} reserve ({aus.get('reserve_quelle') or 'formel'}) "
                     f"= {frei} {einheit} free, "
                     + frei_vergleich_text(
                         frei, frei_gerechnet, einheit,
                         f"{gesamt} - {res} reserve - {dienst} service - "
                         f"{wae} guards({aus['waechter_n']})"))
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
    """Übernimmt die ausdrückliche Nutzerzahl auf den anderen Backends.
    -> Bestehendes Planformat mit Quelle, Grenzen und Fehlgrund."""
    aus["formel_n"] = aus.pop("_formel_n_vram", None) or aus["n"]
    wunsch = max(0, int(aus.get("nutzer_n") or 0))
    if wunsch <= 0:
        return aus                                    # Vorgabe: die Formel gilt
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
