# core/selfcheck.py — SD1 minimal (Paket 3 Zug B, Bauplan v2 / Anti-Selbstzweck-Schnitt):
# nimmt die im Startup-Selbstcheck gesammelten Records entgegen und schreibt sie ATOMAR
# nach state/startup.json. KEIN Rendering, KEINE verifyd-Importe (Injektion pur) — das
# Menschen-Log bleibt unveraendert die Quelle fuer Leser; die Records sind die Quelle
# fuer Maschinen: /health leitet 'ok' daraus ab (B8-Fang: Selbstcheck-FAIL und health-ok
# koennen nie wieder gleichzeitig wahr sein) und Tester-startup.json wird auswertbar.
import json
import os
import time


def schreiben(data_dir, version, records):
    """records = Liste {schritt, name, mark, detail}. -> (pfad, fails)."""
    fails = sum(1 for r in records if str(r.get("mark", "")).strip().upper() == "FAIL")
    d = {"ts": round(time.time(), 1), "version": version,
         "fails": fails, "records": records}
    sd = os.path.join(data_dir, "state")
    os.makedirs(sd, exist_ok=True)
    pfad = os.path.join(sd, "startup.json")
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)
    return pfad, fails
