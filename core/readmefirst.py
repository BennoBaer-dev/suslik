"""Read me first — die eine Seite, die jeder neue Nutzer einmal sieht.

User-Auftrag 29.08.2026: „Ein Anzeigepunkt, der heisst Read me first. Der muss
einmal als Knopf deutlich sichtbar sein, am besten ueberall. Und er muss auch
auftauchen, wenn einer das erste Mal auf das System zugreift beziehungsweise
nach einem Neustart muss es angezeigt werden. Ich wuerde aktuell noch nicht
bauen, dass der Benutzer das fest entfernen kann, sondern er muss es natuerlich
schliessen koennen." Dazu: „waer super, wenn das, was angezeigt wird, auch hin-
und herklickbar ist, dass wir mit Ueberschriften arbeiten koennten oder
Kapiteln."

MECHANIK (User-Vorgabe, ersetzt einen ersten Browser-Entwurf): eine
Marker-Datei im Datenverzeichnis, sonst nichts.
  - Beim Start des Dienstes wird die Marke GELOESCHT (start_zuruecksetzen).
  - Fehlt die Marke, geht die Seite von selbst auf (soll_zeigen).
  - Schliesst der Nutzer sie, wird die Marke GESETZT (gesehen_merken).
Bewusste Folge dieser Bauform: Der Zustand gilt fuer die INSTALLATION, nicht je
Geraet. Wer die Seite am Rechner schliesst, sieht sie auch am Handy nicht mehr,
bis zum naechsten Neustart. Fuer den Zweck reicht das, und es spart jeden
Browser-Zustand.

TON (User-Vorgabe 29.08., verbindlich): „Alles, was in das Read me first
kommt, darf auf keinen Fall KI geschrieben wirken, sondern muss immer kurz,
knapp und auf den Punkt kommen. Kein grosser Prosatext, sondern Faktenbasis."
Also: Saetze, die eine Tatsache nennen und dann aufhoeren. Keine Einleitungen,
keine Dreier-Aufzaehlungen, keine Ueberleitungen, kein „nicht nur X, sondern
auch Y". Wer hier Text einfuegt, schickt ihn vorher durch den Humanizer-
Stilpass und laesst ihn vom User abnehmen — der Inhalt kommt von ihm, nicht
von uns (dieselbe Regel wie bei der What's-new-Box).

KAPITEL: Die Reihenfolge steht HIER, die Texte stehen in core/texte/*.py wie
alles andere. Ein Kapitel ist ein Schluesselpaar (Titel/Text) plus eine Marke
fuer den Anker. Der Inhalt kommt vom User, nicht von uns (dieselbe Regel wie
bei der What's-new-Box) — bis er ihn diktiert hat, traegt jedes Kapitel seinen
Platzhalter und die Seite sagt das auch.
"""
import os

MARKE = "readmefirst_gesehen"      # <data_dir>/state/…

# Kontaktadresse unter dem Text (User 29.08.: „Ich freu mich ueber Rueckmeldung,
# da kann ja meine Adresse rein"). BEWUSST hier als eine Konstante und nicht in
# den Sprachdateien: sie ist in allen Sprachen dieselbe, und wer sie aendert,
# soll genau eine Stelle anfassen. Leer = die Zeile erscheint gar nicht.
KONTAKT = "suslik_dev@posteo.de"


# Reihenfolge der Kapitel. Je Eintrag: (anker, textschluessel-praefix).
# Der Titel kommt aus "<praefix>.titel", der Fliesstext aus "<praefix>.text".
# Neue Kapitel hier anhaengen und die beiden Schluessel in allen fuenf
# Sprachdateien ergaenzen — mehr ist nicht zu tun.
KAPITEL = (
    ("generell", "readme.generell"),
    ("lernen", "readme.lernen"),
    ("aktuell", "readme.aktuell"),
    ("persoenlich", "readme.persoenlich"),
)


def _pfad(data_dir):
    return os.path.join(data_dir or ".", "state", MARKE)


def start_zuruecksetzen(data_dir, log=None):
    """Beim Dienststart aufrufen: Marke weg, die Seite zeigt sich wieder.
    Fehler sind nie ein Grund, den Start zu verhindern — schlimmstenfalls
    bleibt die Seite diesmal aus."""
    try:
        p = _pfad(data_dir)
        if os.path.exists(p):
            os.remove(p)
            if log:
                log("read-me-first: shown again after this restart")
    except Exception as e:
        if log:
            log(f"read-me-first: marker not cleared ({type(e).__name__}: {e})")


def soll_zeigen(data_dir):
    """-> True, wenn die Seite von selbst aufgehen soll (Marke fehlt).
    Fail-safe False: kann der Zustand nicht gelesen werden, draengt sich
    nichts auf; der Knopf bleibt ja immer erreichbar."""
    try:
        return not os.path.exists(_pfad(data_dir))
    except Exception:
        return False


def gesehen_merken(data_dir):
    """Der Nutzer hat die Seite geschlossen. -> (ok, meldung)."""
    try:
        p = _pfad(data_dir)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("")
            f.flush()
            os.fsync(f.fileno())
        return True, "ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def kapitel(t):
    """-> [{anker, titel, text}] in der Reihenfolge von KAPITEL.
    t ist die Uebersetzungsfunktion (core.sprache.t). Ein Kapitel ohne
    hinterlegten Text faellt NICHT weg, sondern zeigt seinen Platzhalter —
    sonst merkt niemand, dass da noch etwas fehlt."""
    aus = []
    for anker, praefix in KAPITEL:
        aus.append({"anker": anker,
                    "titel": t(f"{praefix}.titel"),
                    "text": t(f"{praefix}.text")})
    return aus
