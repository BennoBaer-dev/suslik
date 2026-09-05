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
VRAM_DIENST_MB = 100            # der Dienstprozess selbst (gemessen 92)

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
