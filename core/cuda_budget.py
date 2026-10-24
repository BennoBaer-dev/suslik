"""CUDA-Gesamtzustände statt Einzelpreise (Bauplan CUDA-Messsteuerung, MS1).

Die Vorgaben stammen aus den Messungen der .025 am 18.10.2026. Anlauf und
Schritt sind vorläufige Beobachtungen, keine Zusage für andere Karten oder
sechs materialisierte Sätze. Reserve ist eine Politikzahl, einmal je Prozess.
Sonden, Persistenz, Staffelung und Druckbehandlung bleiben bei ihren Besitzern.
"""

PROFILE = {
    "startup_mb": 1196,
    "step_mb": 512,
    "reserve_mb": 64,
    "status": "provisional",
    "source": "0.1.1.025 CUDA measurements 2026-10-18; one thread/one geometry",
}


class MaterializationError(RuntimeError):
    """Eine gedeckelte Materialisierung konnte nicht freigegeben werden."""


def reserve(total, wish=-1):
    """Liest die einmalige absolute CUDA-Reserve oder den ausdrücklichen Wunsch.
    -> MiB; keine Multiplikation mit Strängen oder Geometrien."""
    value = int(wish if wish is not None else -1)
    return min(max(0, int(total or 0)), value if value >= 0 else PROFILE["reserve_mb"])


def state(prices, n=1, g=1):
    """Liest einen passenden gemessenen Gesamtzustand ohne Posten-Ableitung.
    -> (Worker-PID-Spitze, Quelle); ohne Zustand den markierten Anlaufwert."""
    matching = [t for t in ((prices or {}).get("zustaende") or {}).values()
                if t.get("straenge") == n and t.get("geometrien") == g]
    mb = max((t.get("max_mb", 0) for t in matching), default=0)
    if type(mb) is int and mb > 0:
        return mb, "measured worker PID peak on this hardware/engine/model"
    return PROFILE["startup_mb"], f"provisional: {PROFILE['source']}; matching state unavailable"


def pair_reason(measured, total):
    """Prüft Karten-/PID-Gruppe aus demselben lebenden Prozess und Messzyklus.
    -> Grund oder None; fehlend, veraltet und fremder Zyklus sind getrennt benannt,
    fehlende/alte Werte sind keine Nullmessung. Die Gründe bleiben ohne Messzahlen
    (gleicher Grund, gleiche Meldung); Zeiten und Alter stehen im Debugweg des Dienstes."""
    if not measured:
        return "missing measurement: no card/worker pair for the running worker"
    card, own = measured["card"], measured["own"]
    now, age = measured["now"], measured["max_age"]
    if not measured.get("alive", True):
        return "worker no longer alive"
    if card.get("grund") or own.get("grund"):
        return f"missing measurement: card={card.get('grund')}, own={own.get('grund')}"
    if card.get("worker") != measured["worker"] or own.get("worker") != measured["worker"]:
        return "worker generation mismatch"
    if not card.get("ts") or not own.get("ts"):
        return "missing measurement: card or own sample without time"
    if own.get("karte_ts") != card["ts"]:
        return "card and own samples from different measurement cycles"
    if not 0 <= now - own.get("ende", own["ts"]) <= age:
        return f"stale measurement: own sample older than {age} s"
    if (not 0 <= card.get("ende", card["ts"]) - card["ts"] <= age
            or not 0 <= own["ts"] - card.get("ende", card["ts"]) <= age
            or not 0 <= own.get("ende", own["ts"]) - own["ts"] <= age):
        return f"stale measurement: card and own samples more than {age} s apart in one cycle"
    if (type(card.get("mb")) is not int or type(own.get("mb")) is not int
            or card["mb"] < 0 or own["mb"] <= 0 or own["mb"] + card["mb"] > total):
        return "invalid card and own amounts"
    return None


def ladder(budget, wish, maximum, prices, decoder_mb):
    """Wählt Nutzerzahl oder einen Strang; Materialisierung wird einzeln zugelassen.
    -> Plan mit gekennzeichnetem Erstbedarf, ohne erfundene Sechs-Satz-Summe."""
    n = min(maximum, max(1, int(wish or 1)))
    own, source = state(prices,n,1)
    need = own + n * decoder_mb
    return {"n": n, "g_zusatz": 0, "geometrien_max": 1,
            "summe_mb": need, "pflicht_preis_mb": need, "unter_pflicht": budget < need,
            "budget_mb": budget, "obergrenze": n, "quelle": source,
            "preis_quelle": {"gesamtzustand": source}, "preise_mb": {"gesamtzustand": own},
            "gemessen_mb": {"gesamtzustand": own} if source.startswith("measured") else {},
            "tabelle_beleg": PROFILE["source"], "stufen": [],
            "grund": "nutzer" if wish else "vorgabe"}


def selection(out, free, own, reason, guards, guard_reason, running_n, stock,
              prices, maximum, decoder_mb):
    """Plant CUDA aus nativfrei und gültigem Eigenbestand, ohne Tabellen-Rückgutschrift.
    -> Ergebnis im bestehenden Dienstformat; echte Knappheit bleibt verweigert."""
    total, wish = out["gesamt_mb"], out["reserve_wunsch_mb"]
    res = reserve(total, wish)
    budget = max(0, free + own - res - guards)
    lt = ladder(budget, out["nutzer_n"], maximum, prices, decoder_mb)
    n = lt["n"]
    if running_n and own:
        peak, source = state(prices,max(n,running_n),max(1,stock or 1))
        lt["summe_mb"] = max(lt["summe_mb"], own, peak)
        lt["current_peak_mb"] = peak if source.startswith("measured") else None
    refused = total <= 0 or reason is not None or lt["unter_pflicht"]
    cap = max(1, stock or 0) if running_n else 1
    arena = max(1, budget - n * decoder_mb)
    # MP1: Anlaufbedarf (vorläufig oder gemessener Zustand) und gültige laufende
    # Messung getrennt benennen; nur Aussagen, keine Rechen- oder Freigaberegel.
    if not running_n:
        own_text = "no running worker"
    elif reason is not None:
        own_text = "running worker measurement unavailable, not credited"
    else:
        own_text = f"running worker measured {own} MiB (worker/decoders)"
    need_kind = "measured state need" if lt["gemessen_mb"] else "provisional startup need"
    peak = lt.get("current_peak_mb")
    arena_text = (f"recomputed arena proposal {arena} MiB for a next start (the held arena "
                  f"of the running worker is unchanged)" if running_n
                  else f"arena cap {arena} MiB for this start")
    text = (f"cuda measured budget: native free {free} + own {own} ({own_text}) "
            f"- absolute reserve {res} - pending guards {guards} = {budget} MiB budget; "
            f"{n} thread(s), {need_kind} {lt['preise_mb']['gesamtzustand']} MiB "
            f"({lt['quelle']})"
            + (f", running measured peak {peak} MiB" if peak else "")
            + f", pending decoder allowance {n * decoder_mb} MiB; "
            f"next materialization {PROFILE['step_mb']} MiB provisional, serialized; "
            f"{arena_text}, not a worker PID measurement")
    warning = reason or (f"no measured state for {n} thread(s)/one geometry yet, startup need "
                         f"stays provisional ({lt['quelle']})" if not lt["gemessen_mb"] else None)
    out.update(n=n, formel_n=n, leiter=lt, g_zusatz=max(0, cap - 2), geometrien_max=cap,
               reserve_mb=res, reserve_quelle="config" if wish >= 0 else "absolute CUDA profile",
               worker_budget_mb=budget, frei_mb=budget, frei_quelle="gemessen",
               laufend_eigen_mb=own, laufend_eigen_quelle="measured" if own else None,
               waechter_abzug_mb=guards, waechter_abzug_grund=guard_reason,
               fussabdruck_mb=lt["summe_mb"], arena_deckel_mb=arena,
               posten_ausserhalb_mb=n * decoder_mb,
               posten={"decoder_mb": n * decoder_mb, "straenge": n},
               deckel_quelle="native free and own measurement",
               preis_quelle=lt["quelle"], preis_quelle_stufen=lt["preis_quelle"],
               preise_mb=lt["preise_mb"], gemessen_mb=lt["gemessen_mb"],
               verweigert=refused, zustand="rot" if refused else "gruen",
               grund="nicht_messbar" if reason else "zu_klein" if refused else lt["grund"],
               hinweis=f"CUDA memory planning: {warning}" if warning else None,
               rechenweg=text, geometrien_rechenweg=text, cuda_messgrund=reason)
    if out["nutzer_n"] > maximum:
        out["deckel_meldung"] = f"worker_straenge={out['nutzer_n']} capped to hard ceiling {maximum}"
    if refused:
        cause = reason or "insufficient native free memory"
        out["hinweis"] = (f"CUDA memory planning unavailable for running worker: {cause}; {text}"
                          if running_n else f"CUDA worker start blocked: {cause}; {text}")
    return out


def fallback(out, guards, guard_reason, decoder_mb):
    """Plans the start when card size and native free memory are both unknown (Bauplan KG1).
    -> Result in the service format: one thread, fixed profile arena cap, red, not refused.

    Wie bis 0.1.1.025 (`afd57621:core/gpubudget.py` `_fail_closed`) startet der Worker trotzdem,
    statt gesperrt zu sein (Eigentuemer 22.10.2026 15:34:14). Es gibt keine Messung, aus der ein Budget
    folgen koennte: Budget und Frei bleiben 0 bzw. leer, nichts wird als Messwert ausgegeben. Der
    Deckel ist der vorlaeufige Anlaufbedarf des Profils; ein Config-Deckel ersetzt ihn im Dienst
    wie den errechneten. Ein gesetzter worker_straenge gilt hier nicht nach oben; der Dienst
    nennt die Kuerzung in seiner ERROR-Zeile (ED001)."""
    cap = PROFILE["startup_mb"]
    lt = ladder(0, 1, 1, None, decoder_mb)
    lt["grund"] = "nicht_messbar"
    text = (f"cuda: card not measurable (card size and native free memory unknown) -> "
            f"1 thread, fixed arena cap {cap} MiB from the provisional profile "
            f"({PROFILE['source']}), no free-memory check before the start")
    out.update(n=1, formel_n=1, leiter=lt, g_zusatz=0, geometrien_max=1,
               reserve_mb=0, reserve_quelle="config" if out["reserve_wunsch_mb"] >= 0
               else "absolute CUDA profile",
               worker_budget_mb=0, frei_mb=0, frei_quelle="nicht_messbar",
               frei_gemessen_mb=None, frei_moment_mb=None,
               laufend_eigen_mb=0, laufend_eigen_quelle=None,
               waechter_abzug_mb=guards, waechter_abzug_grund=guard_reason,
               fussabdruck_mb=lt["summe_mb"], arena_deckel_mb=cap,
               posten_ausserhalb_mb=decoder_mb,
               posten={"decoder_mb": decoder_mb, "straenge": 1},
               deckel_quelle="provisional CUDA profile",
               preis_quelle=lt["quelle"], preis_quelle_stufen=lt["preis_quelle"],
               preise_mb=lt["preise_mb"], gemessen_mb={},
               verweigert=False, zustand="rot", grund="nicht_messbar",
               hinweis=(f"CUDA memory planning: card not measurable (card size and native "
                        f"free memory unknown) — one thread with the fixed profile arena cap "
                        f"{cap} MiB, no free-memory check before the start"),
               rechenweg=text, geometrien_rechenweg=text,
               cuda_messgrund="card not measurable", unmeasurable_card=True)
    return out


def geometry_plan(st, arena_mb, running_n=0, stock_known=True, measured=None):
    """Erhält vorhandene Geometrien und erlaubt höchstens den nächsten Aufbauschritt.
    -> Plan; die Worker-Klammer prüft jeden Satz und Warm-up erneut gegen nativfrei."""
    if st.get("kind") != "cuda" or st.get("verweigert"):
        return st
    out = dict(st)
    reason = pair_reason(measured, st["gesamt_mb"]) if running_n else None
    cap = max(1, st.get("geometrien_max") or 1)
    held_decoders = int(((measured or {}).get("own") or {}).get("decoder_mb") or 0)
    pending = max(0, int(st.get("posten_ausserhalb_mb") or 0) - held_decoders)
    own_pid = int(st.get("laufend_eigen_mb") or 0) - held_decoders
    processing = max(0, int((st.get("leiter") or {}).get("current_peak_mb") or 0) - own_pid)
    headroom = max(0, int(st["worker_budget_mb"]) - int(st.get("laufend_eigen_mb") or 0) - pending - processing)
    if st.get("zustand") == "rot" or st.get("modus") in ("minimal", "reduziert"):
        reason = f"protection mode: {st.get('modus') or st.get('grund')}"
    if not stock_known:
        reason = "current geometry count unknown"
    if not arena_mb:
        reason = "arena cap unknown"
    elif arena_mb < PROFILE["step_mb"]:
        reason = "arena cap below next provisional step"
    if not reason and headroom >= PROFILE["step_mb"]:
        cap += 1
    text = (f"geometry cap {cap}: native headroom {headroom} MiB, next serialized step "
            f"{PROFILE['step_mb']} MiB provisional; held arena {arena_mb} MiB; "
            f"{reason or 'fresh measurements; stock retained, worker rechecks every materialization'}")
    out.update(geometrien_max=cap, geometrien_grund=reason or "native free",
               geometrien_rechenweg=text, geometrien_messung=measured,
               geometrien_budget_mb=st["worker_budget_mb"],
               geometrien_budget_quelle="native free and own worker/decoder group",
               rechenweg=st["rechenweg"] + "; " + text)
    out["leiter"] = dict(st["leiter"], geometrien_max=cap)
    return out
