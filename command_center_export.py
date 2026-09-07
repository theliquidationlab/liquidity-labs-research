from pathlib import Path
import datetime
import json
import sqlite3

LIVE_ROOT = Path(r"C:\LiquidityLabs\BTC_MICRO_ORB_V5\runtime")
RESEARCH_ROOT = Path(r"C:\LiquidityLabs\BTC_V3A_RESEARCH_AGENT\runtime")
RESEARCH_DB = RESEARCH_ROOT / "research.db"
SAMPLE_ONLY_REASONS = {
    "INSUFFICIENT_WALK_FORWARD_SAMPLE",
    "INSUFFICIENT_VALIDATION_SAMPLE",
    "INSUFFICIENT_RECENT_HOLDOUT",
}

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

def _parse_utc(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None

def age_seconds(value, now=None):
    dt = _parse_utc(value)
    if dt is None:
        return None
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return max(0.0, (now - dt).total_seconds())

def health_state(age, warn_after, bad_after):
    if age is None or age > bad_after:
        return "RED"
    if age > warn_after:
        return "AMBER"
    return "GREEN"

def safe_zone(zone):
    if not isinstance(zone, dict):
        return None
    keys = ("state", "age_min", "last_touch_age_min", "touch_bars", "touch_episodes", "broken")
    return {k: zone.get(k) for k in keys if k in zone}

def metric_summary(block):
    block = block or {}
    keys = ("resolved", "wins", "losses", "profit_factor_r", "expectancy_r", "max_drawdown_r", "opportunities_per_hour")
    return {k: block.get(k) for k in keys}

def safe_price_zone(zone, state=None):
    if not isinstance(zone, dict):
        return None
    return {"high": zone.get("high"), "low": zone.get("low"), "state": state}

def build_live_summary():
    st = load_json(LIVE_ROOT / "status.json")
    book = st.get("futures_book") or {}
    flow = st.get("futures_flow") or {}
    oi = st.get("futures_oi") or {}
    zones = st.get("zone_lifecycle") or {}
    active = st.get("ten_minute_active_context") or {}
    return {
        "running": bool(st.get("running")),
        "demo_only": bool(st.get("demo_only")),
        "dry_run": bool(st.get("dry_run")),
        "decision": st.get("decision") or "UNKNOWN",
        "signal_ready": bool(st.get("signal_ready")),
        "side": st.get("signal_side") or "NEUTRAL",
        "path": st.get("signal_path") or "NONE",
        "reason": st.get("signal_reason") or st.get("normal_signal_reason") or "UNKNOWN",
        "five_minute_phase": st.get("five_minute_phase") or "UNKNOWN",
        "trigger": st.get("one_minute_trigger") or "UNKNOWN",
        "trigger_kind": st.get("one_minute_trigger_kind") or "NONE",
        "quote_age_ms": st.get("quote_age_ms"),
        "spread": st.get("spread"),
        "updated_utc": st.get("utc"),
        "zones": {"demand": safe_zone(zones.get("demand")), "supply": safe_zone(zones.get("supply"))},
        "ten_minute_context": {"demand": safe_price_zone(active.get("demand"), (zones.get("demand") or {}).get("state")), "supply": safe_price_zone(active.get("supply"), (zones.get("supply") or {}).get("state"))},
        "order_book": {k: book.get(k) for k in ("ready", "stale", "age_ms", "pressure_now", "pressure_1s", "pressure_3s")},
        "futures_flow": {k: flow.get(k) for k in ("ready", "stale", "age_ms", "flow_30s", "flow_1m", "flow_3m", "flow_5m", "accel_30s_vs_3m", "accel_1m_vs_5m")},
        "open_interest": {k: oi.get(k) for k in ("ready", "stale", "change_pct")},
    }

def build_research_summary():
    learning = load_json(RESEARCH_ROOT / "learning_state.json")
    watchdog = load_json(RESEARCH_ROOT / "watchdog_status.json")
    model = watchdog.get("model") or {}
    supervisor = load_json(RESEARCH_ROOT / "supervisor_heartbeat.json")
    deep = load_json(RESEARCH_ROOT / "deep_signal_search_latest.json")
    collector = load_json(RESEARCH_ROOT / "collector_heartbeat.json")
    mt5 = load_json(RESEARCH_ROOT / "mt5_sync_heartbeat.json")
    return {
        "model": model.get("model") or "UNKNOWN",
        "model_degraded": model.get("degraded"),
        "model_state": model.get("reason") or "UNKNOWN",
        "gpu_endpoint": model.get("endpoint") or "UNKNOWN",
        "supervisor_status": supervisor.get("status") or "UNKNOWN",
        "research_phase": supervisor.get("phase") or "UNKNOWN",
        "last_deep_search_utc": deep.get("utc"),
        "last_directed_family": learning.get("last_directed_family"),
        "last_directed_outcome": learning.get("last_directed_outcome"),
        "directed_runs": int(learning.get("directed_runs", 0) or 0),
        "hourly_runs": int(learning.get("hourly_runs", 0) or 0),
        "full_promotions": int(learning.get("validated_promotions", 0) or 0),
        "canary_promotions": int(learning.get("demo_canary_promotions", 0) or 0),
        "overall": watchdog.get("overall") or "UNKNOWN",
        "collector_age_seconds": age_seconds(collector.get("utc")),
        "mt5_sync_age_seconds": age_seconds(mt5.get("utc")),
        "watchdog_age_seconds": age_seconds(watchdog.get("utc")),
    }

def candidate_eligibility(evaluation):
    if str(evaluation.get("decision", "")).upper() == "PASS":
        return "FULL"
    reasons = set(evaluation.get("reasons") or [])
    long_term = evaluation.get("long_term") or {}
    validation = evaluation.get("validation") or {}
    recent = evaluation.get("recent") or {}
    canary = (
        reasons
        and reasons.issubset(SAMPLE_ONLY_REASONS)
        and int(evaluation.get("matched_resolved", 0) or 0) >= 8
        and int(validation.get("resolved", 0) or 0) >= 3
        and int(recent.get("resolved", 0) or 0) >= 3
        and float(long_term.get("profit_factor_r", 0) or 0) >= 1.5
        and float(long_term.get("expectancy_r", -99) or -99) > 0
    )
    return "CANARY" if canary else "EXPLORATORY"

def safe_rule_summary(rule):
    if not isinstance(rule, dict):
        return []
    skip = {"family", "entry_mode", "entry_stage", "research_scope"}
    rows = []
    for key, value in sorted(rule.items()):
        if key not in skip and isinstance(value, (str, int, float, bool)):
            rows.append({"field": str(key), "value": value})
    return rows[:8]

def summarize_candidate(candidate):
    evaluation = candidate.get("evaluation") or {}
    long_term = evaluation.get("long_term") or {}
    validation = evaluation.get("validation") or {}
    recent = evaluation.get("recent") or {}
    walk = evaluation.get("walk_forward") or {}
    frequency = validation.get("opportunities_per_hour")
    if frequency is None:
        frequency = long_term.get("opportunities_per_hour")
    frequency = float(frequency or 0.0)
    return {
        "family": candidate.get("family") or "UNKNOWN",
        "objective": candidate.get("objective") or "UNKNOWN",
        "eligibility": candidate_eligibility(evaluation),
        "decision": evaluation.get("decision") or "UNKNOWN",
        "reasons": list(evaluation.get("reasons") or [])[:8],
        "matched_resolved": int(evaluation.get("matched_resolved", 0) or 0),
        "long_term": metric_summary(long_term),
        "training": metric_summary(evaluation.get("training")),
        "validation": metric_summary(validation),
        "recent": metric_summary(recent),
        "walk_forward": {"stable": walk.get("stable"), "positive_fraction": walk.get("positive_fraction"), "min_profit_factor_r": walk.get("min_profit_factor_r"), "min_expectancy_r": walk.get("min_expectancy_r")},
        "opportunities_per_hour": round(frequency, 4),
        "opportunities_per_day": round(frequency * 24.0, 2),
        "rule": safe_rule_summary(candidate.get("rule") or {}),
    }

def build_signal_discovery(limit=24):
    data = load_json(RESEARCH_ROOT / "deep_signal_search_latest.json")
    if not data:
        data = load_json(RESEARCH_ROOT / "advanced_candidate_shortlist.json")
    rows = [summarize_candidate(x) for x in (data.get("shortlist") or [])[:limit]]
    return {"updated_utc": data.get("utc"), "status": data.get("status") or "UNKNOWN", "count": len(rows), "candidates": rows}

def build_promotions():
    registry = load_json(RESEARCH_ROOT / "demo_promotions.json")
    output = []
    for family, item in (registry.get("active") or {}).items():
        metrics = item.get("metrics") or {}
        health = item.get("health") or {}
        long_term = metrics.get("long_term") or {}
        output.append({
            "proposal_id": item.get("proposal_id"),
            "family": family,
            "tier": item.get("promotion_tier") or "UNKNOWN",
            "status": item.get("status") or "UNKNOWN",
            "promoted_utc": item.get("promoted_utc"),
            "demoted_utc": item.get("demoted_utc"),
            "verifier_decision": item.get("verifier_decision"),
            "verifier_status": item.get("verifier_status"),
            "matched_resolved": metrics.get("matched_resolved"),
            "profit_factor_r": long_term.get("profit_factor_r"),
            "expectancy_r": long_term.get("expectancy_r"),
            "opportunities_per_hour": long_term.get("opportunities_per_hour"),
            "health_decision": health.get("decision"),
            "new_resolved": health.get("new_resolved"),
            "demotion_reasons": list(item.get("demotion_reasons") or [])[:6],
            "rule": safe_rule_summary(item.get("rule") or {}),
        })
    return output

def _ro_connection():
    try:
        return sqlite3.connect("file:" + str(RESEARCH_DB) + "?mode=ro", uri=True, timeout=1.0)
    except Exception:
        return None

def build_history(limit=30):
    con = _ro_connection()
    if con is None:
        return {"verifier": [], "research": []}
    verifier = []
    research = []
    try:
        rows = con.execute("select proposal_id,created_utc,stage,decision,metrics_json,details_json from evaluations order by id desc limit ?", (limit,))
        for proposal_id, utc, stage, decision, metrics_json, details_json in rows:
            if stage not in ("verifier", "critic"):
                continue
            try:
                metrics = json.loads(metrics_json or "{}")
                details = json.loads(details_json or "{}")
            except Exception:
                metrics, details = {}, {}
            verifier.append({
                "proposal_id": proposal_id,
                "utc": utc,
                "stage": stage,
                "decision": decision,
                "family": (metrics.get("rule") or {}).get("family"),
                "reasons": list(metrics.get("reasons") or details.get("objections") or [])[:6],
            })
        rows = con.execute("select created_utc,role,result_json,model from agent_runs order by id desc limit ?", (limit,))
        for utc, role, result_json, model in rows:
            try:
                result = json.loads(result_json or "{}")
            except Exception:
                result = {}
            research.append({
                "utc": utc,
                "role": role,
                "family": result.get("family"),
                "outcome": result.get("research_outcome") or result.get("decision") or result.get("status"),
                "proposal_id": result.get("proposal_id"),
                "model": model,
            })
    except Exception:
        return {"verifier": verifier, "research": research}
    finally:
        con.close()
    return {"verifier": verifier[:limit], "research": research[:limit]}

def recent_order_families():
    rows=[]
    try:
        for line in (LIVE_ROOT / "events.jsonl").read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                event=json.loads(line)
            except Exception:
                continue
            if event.get("kind") != "ORDER_FILLED":
                continue
            plan=event.get("plan") or {}
            family=plan.get("smart_family") or (plan.get("smart_entry") or {}).get("family")
            rows.append({"utc":event.get("utc"),"side":plan.get("side"),"family":family})
    except Exception:
        return []
    return rows[-100:]

def match_trade_family(entry_utc, side, fills):
    entry=_parse_utc(entry_utc)
    best=(999999.0,"UNKNOWN")
    for row in fills:
        if side and row.get("side") and row.get("side") != side:
            continue
        when=_parse_utc(row.get("utc"))
        if entry is None or when is None:
            continue
        delta=abs((entry-when).total_seconds())
        if delta < best[0]:
            best=(delta,row.get("family") or "UNKNOWN")
    return best[1] if best[0] <= 10.0 else "UNKNOWN"

def build_trading(limit=30):
    con = _ro_connection()
    recent = []
    fills = recent_order_families()
    if con is not None:
        try:
            rows = con.execute("select entry_utc,exit_utc,side,profit,reason from trades order by rowid desc limit ?", (limit,))
            for entry_utc, exit_utc, side, profit, reason in rows:
                value = float(profit or 0.0)
                recent.append({
                    "entry_utc": entry_utc,
                    "exit_utc": exit_utc,
                    "side": side or "UNKNOWN",
                    "family": match_trade_family(entry_utc, side, fills),
                    "result": "WIN" if value > 0 else ("LOSS" if value < 0 else "FLAT"),
                    "profit": round(value, 2),
                    "reason": str(reason or ""),
                })
        except Exception:
            recent = []
        finally:
            con.close()
    wins = sum(1 for row in recent if row["result"] == "WIN")
    losses = sum(1 for row in recent if row["result"] == "LOSS")
    resolved = wins + losses
    summary = {
        "trades": len(recent), "wins": wins, "losses": losses,
        "win_rate": round(100.0 * wins / resolved, 1) if resolved else 0.0,
        "net_profit": round(sum(row["profit"] for row in recent), 2),
    }
    return {"recent": recent, "summary": summary}

def build_health_matrix():
    watchdog = load_json(RESEARCH_ROOT / "watchdog_status.json")
    checks = watchdog.get("checks") or {}
    names = [
        ("Bot heartbeat", "bot_heartbeat"), ("Bot status", "bot_status"),
        ("Collector", "collector"), ("MT5 sync", "mt5_sync"),
        ("GPU tunnel", "gpu_tunnel"), ("Hourly research", "hourly_cycle"),
        ("Live feed", "live_feed_semantics"),
    ]
    output = []
    for label, key in names:
        check = checks.get(key) or {}
        age = check.get("age_seconds")
        if key == "live_feed_semantics" and age is None:
            state = "GREEN" if check.get("ok") else "RED"
        else:
            max_age = float(check.get("max_age_seconds", 180) or 180)
            state = health_state(age, max_age * 0.75, max_age)
        output.append({"name": label, "state": state, "age_seconds": round(float(age), 1) if age is not None else None, "detail": check.get("state") or ("OK" if check.get("ok") else "UNKNOWN")})
    supervisor = load_json(RESEARCH_ROOT / "supervisor_heartbeat.json")
    age = age_seconds(supervisor.get("utc"))
    output.append({"name": "Research supervisor", "state": health_state(age, 90, 180), "age_seconds": round(age, 1) if age is not None else None, "detail": supervisor.get("phase") or supervisor.get("status") or "UNKNOWN"})
    return output

def build_command_center():
    return {
        "schema_version": 2,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "live": build_live_summary(),
        "research": build_research_summary(),
        "signals": build_signal_discovery(),
        "promotions": build_promotions(),
        "history": build_history(),
        "trading": build_trading(),
        "health": build_health_matrix(),
    }
