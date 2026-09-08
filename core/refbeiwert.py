"""core/refbeiwert — der A2-Embedding-Beiwert von Vorrats-Referenzen
(bauplan_vorrat.md B4b, 20.08.2026).

MESSBEFUND, der dieses Modul erzwingt: 28/40 der norm-starken Klein-Crops sind
als Referenz-DATEI tot — `embed()` (Detektion+Alignment auf der Datei) findet in
ihnen kein Gesicht, und ein Umfeld-Rand heilt das nicht (Faktor 3,0 laesst
13/40 tot, Drift bis cos 0,83). Die WAHRHEIT einer Vorrats-Referenz ist ihr
Vollbild-Embedding aus dem Ernte-Lauf; die Bilddatei ist Anzeige-Artefakt.
Der Beiwert steht in refs_meta.jsonl (`"emb"` + `"emb_modell"`), und JEDER
Datei-Re-Embedder muss ihn kennen, sonst stirbt die Referenz beim naechsten
Cache-Neuaufbau still (Konzept-QS W1.1-3, W2.6, W2.12).

DECKUNGS-VERTRAG (QS-Ebenen-Regel: Aufzaehlung mit Vertrag statt Streu-Logik) —
die Anschluss-Stellen, die `beiwerte()` nutzen MUESSEN; wer einen weiteren
Datei-Re-Embedder baut, traegt ihn hier ein:
  1. anlernen.lade_master_refs        (deckt core/livewache mit ab)
  2. analyze.load_refs                (der URTEILSPFAD — schreibt den refcache)
  3. anlernen._person_refs            (Nachpruefung nach dem Anlernen)
  4. abnahme.lade_master_refs         (Drift-Waechter des Release-Gates)
  5. anlernen.lade_master_bilder      (Bestands-QS: Beiwert-Referenzen sind
                                       vollwertige Messzeilen der Klasse
                                       'vorrat', nie 'kein_gesicht'-Loeschware)
  6. anlernen.refcache_ergaenzen      (Sofort-Einpflege bei der Uebernahme)

DIE ZWEITE BILLIGE QUELLE (Stufe B, .511) — wer hier liest, muss sie kennen:
`core/refmess.py`, der MESS-SIDECAR des Katalogs (`faces/refs_mess.json`). Der
Beiwert deckt nur die Referenzen aus Ernte/Vorrat ab (im Feldtester-Bestand
602 von 1229);
fuer alle uebrigen haelt der Sidecar die Datei-Messwerte (kante/sharp/norm/pose/
fiqa_t/empf/wh/camera) samt Frische-Anker fest, und das zugehoerige EMBEDDING
kommt aus `clips/refcache.npz` ueber dessen `§rows`-Karte. Die Rangfolge in
`anlernen.lade_master_bilder` (Stelle 5) lautet seit .511:
    A2-Beiwert  ->  Sidecar + refcache-Vektor  ->  volle Datei-Messung
Regel fuer neue Datei-Re-Embedder: der Beiwert bleibt Pflicht (sonst stirbt die
Vorrats-Referenz still, s. oben); der Sidecar ist eine reine Beschleunigung und
darf ausfallen — aber ein Vektor aus dem refcache darf NIE zu einer Sidecar-
Zeile genommen werden, die der Datei-Anker nicht mehr deckt (die npz fuehrt
keinen eigenen Anker; sonst liefe eine ausgetauschte Datei mit altem Vektor).
"""
import json
import os


def beiwerte(master_dir, modell, alle=None):
    """refs_meta.jsonl -> ({(person, datei): meta_zeile}, fremdmodell_n).

    Die meta_zeile ist der VOLLE refs_meta-Eintrag (traegt neben "emb" auch die
    Lauf-Messwerte kante/sharp/norm — die Bestands-QS fuehrt Beiwert-Referenzen
    damit als vollwertige Messzeilen statt sie an der Datei zu messen).
    Last-wins je (person, datei) wie ueberall im Meta-Buch; nur AKTIVE Eintraege
    mit Beiwert zaehlen. Eintraege, deren Beiwert zu einem ANDEREN Recognition-
    Modell gehoert, kommen NICHT in die Karte, werden aber GEZAEHLT
    zurueckgegeben — der Aufrufer meldet sie laut (nie still mit falschem
    Vektor weiterleben, nie still verschwinden).

    `alle` (Stufe B, .511): ein Dict, das nebenbei mit dem VOLLEN last-wins-Stand
    JEDER aktiven Referenz gefuellt wird — auch der ohne Beiwert. Anlass, ein
    Fehler aus dem Bau selbst: der Kamera-Nachtrag las zuerst `karte` und fand
    dort natuerlich nur die 602 Beiwert-Referenzen; `eid` und `camera` stehen
    aber in JEDER Meta-Zeile (Feldtester-Bestand: 1155 bzw. 692 von 1229).
    Ein zweiter
    Journal-Leser waere die naheliegende, falsche Antwort gewesen: Tombstones
    und die `wieder_anbieten`-Ausnahme unten muessten dort noch einmal richtig
    stehen (K3). Deshalb EIN Leser, zwei Ausgaben."""
    karte, fremd = {}, {}
    if alle is None:
        alle = {}
    p = os.path.join(master_dir, "refs_meta.jsonl")
    if not os.path.exists(p):
        return karte, 0
    with open(p, encoding="utf-8") as f:
        for zeile in f:
            try:
                d = json.loads(zeile)
            except Exception:
                continue
            person, datei = d.get("person"), d.get("datei")
            if not (person and datei):
                continue
            key = (person, datei)
            if not d.get("aktiv", True):
                # .314b (Widerleger, HOCH): "offer again" auf der Sync-Seite
                # schreibt aktiv=False fuer eine Datei, die im Master LIEGEN
                # BLEIBT — das ist KEINE Loeschung (sync_refs.wieder_anbieten,
                # Marker GRUND_WIEDER_ANBIETEN; anlernen.vorschlaege ueberspringt
                # sie seit .138 am selben Marker). Ohne diese Ausnahme verlor die
                # Referenz hier ihren A2-Beiwert dauerhaft: das Bild bliebe im
                # Master, faellt aber aus refcache und Bestands-QS, weil die
                # Nach-Detektion auf dem Klein-Crop nicht traegt (28/40-Befund).
                from sync_refs import GRUND_WIEDER_ANBIETEN as _GRUND_WA
                if str(d.get("grund") or "") == _GRUND_WA:
                    continue                  # Beiwert der Zeile davor bleibt gueltig
                karte.pop(key, None)
                fremd.pop(key, None)
                alle.pop(key, None)
                continue
            alle[key] = d
            if not d.get("emb"):
                continue
            if str(d.get("emb_modell") or "") == str(modell):
                karte[key] = d
                fremd.pop(key, None)
            else:
                fremd[key] = True
                karte.pop(key, None)
    return karte, len(fremd)
