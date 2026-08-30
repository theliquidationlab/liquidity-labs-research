from pathlib import Path
import json, re, subprocess, datetime

ROOT = Path(r"C:\LiquidityLabs\BTC_CLEANROOM_V1")
OUT = Path(__file__).resolve().parent / "data" / "status.json"
MT5_ATLAS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_TARGET_RUN_ATLAS_V1" / "00_STATUS.json"
MT5_FEATURE = ROOT / "12_LIVE_PARITY" / "MT5_TICK_CAUSAL_FEATURE_BINS_V1" / "00_STATUS.json"
MT5_FEATURE_LOG = ROOT / "RUNS" / "mt5_tick_causal_feature_bins_v1.stdout.log"
MT5_BASE = ROOT / "12_LIVE_PARITY" / "MT5_SETUP_BROKER_OUTCOME_SCREEN_V1" / "00_STATUS.json"
BIN_STRENGTH = ROOT / "12_LIVE_PARITY" / "MT5_SETUP_BINANCE_STRENGTH_SEARCH_V1" / "00_STATUS.json"
ACTIVE_WORKER = ROOT / "RUNS" / "ACTIVE_RESEARCH_WORKER.json"
MINING_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_TICK_BACKWARD_WINNER_MINING_V1" / "00_STATUS.json"
MINING_WORK_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_BACKWARD_WINNER_MINING_V1_WORK" / "PROGRESS.json"
MINING_FINAL_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_BACKWARD_WINNER_MINING_V1" / "PROGRESS.json"

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

def tail_text(path, limit=200000):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[-limit:]
    except Exception:
        return ""
def process_running(needle):
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-CimInstance Win32_Process | Select-Object -ExpandProperty CommandLine"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return needle.lower() in (r.stdout or "").lower()
    except Exception:
        return False

def feature_progress():
    st = load_json(MT5_FEATURE)
    if st.get("complete"):
        return 365, 365, True
    text = tail_text(MT5_FEATURE_LOG)
    hits = [int(x) for x in re.findall(r"BIN_DAYS=(\d+)/365", text)]
    done = max(hits) if hits else 0
    return done, 365, False

def pct(x):
    return None if x is None else round(float(x) * 100.0, 2)

def stage(name, state, detail, weight, fraction=1.0, finding="", subchecklist=None):
    fraction = max(0.0, min(1.0, float(fraction)))
    return {"name": name, "state": state, "detail": detail,
            "weight": weight, "fraction": fraction, "percent": round(fraction * 100.0, 2),
            "finding": finding, "subchecklist": subchecklist or {}}

def mining_stage_state(progress, final_status, active_phase, running):
    if final_status.get("complete"):
        return "complete", 1.0, "183/183 Discovery days mined; single-state enrichment census complete.", progress.get("checklist", {})
    done = int(progress.get("days_complete", 0) or 0)
    total = int(progress.get("days_total", 183) or 183)
    fraction = max(0.0, min(1.0, float(progress.get("percent", 0.0) or 0.0) / 100.0))
    if active_phase == "MT5_TICK_BACKWARD_WINNER_MINING_V1" and running:
        return "working", fraction, f"{done}/{total} Discovery days mined from exact MT5 tick-index joins.", progress.get("checklist", {})
    return "pending", fraction, f"{done}/{total} Discovery days mined; worker is not currently active.", progress.get("checklist", {})

def build_status():
    atlas = load_json(MT5_ATLAS)
    base = load_json(MT5_BASE)
    bstrength = load_json(BIN_STRENGTH)
    bin_days, total_days, feature_done = feature_progress()
    active = load_json(ACTIVE_WORKER)
    active_phase = str(active.get("phase", ""))
    mining_final = load_json(MINING_FINAL)
    mining_progress = load_json(MINING_FINAL_PROGRESS) or load_json(MINING_WORK_PROGRESS)
    mining_running = process_running("mt5_tick_backward_winner_mining_v1.py")
    mining_state, mining_fraction, mining_detail, mining_subchecklist = mining_stage_state(
        mining_progress, mining_final, active_phase, mining_running)

    mt5_wr = pct(base.get("branch_decision", {}).get("best_full_wr"))
    bin_wr = pct(bstrength.get("branch_decision", {}).get("best_full_wr"))
    combined_wr = None
    qualifying_tpd = 0.0
    feature_fraction = min(1.0, bin_days / 365.0)

    stages = [
        stage("Full-year PU Prime MT5 tick history", "complete", "365/365 BTCUSD days cached from PUPrime-Demo.", 8, finding="62,299,358 historical bid/ask ticks available."),
        stage("+$1-at-0.01 MT5 outcome atlas", "complete", "Every tick labeled for a +$100 BTC move using executable bid/ask sides.", 12, finding="BUY askâ†’future bid; SELL bidâ†’future ask; 900-second forward path."),
        stage("MT5 causal tick feature engine", "complete", "81 causal tick-level broker features built and regression tested.", 6, finding="Uses bid/ask microstructure, spread, velocity, range, efficiency, pressure and range position."),
        stage("Discovery threshold fitting", "complete", "Thresholds fitted only on the 183-day Discovery period.", 6, finding="Untouched Confirmation/Hard/Holdout outcomes were not used for fitting."),
        stage("Full-year MT5 state matrix", "complete" if feature_done else "working", f"{bin_days}/365 days binned with frozen MT5 thresholds.", 12, feature_fraction, finding="This creates the searchable MT5 state infrastructure for backward winner mining."),
        stage("Backward mining of +$1 winners", mining_state, mining_detail, 12, mining_fraction,
              finding="All 810 exact MT5 states are measured against hit and non-hit controls across both directions, nine horizons and six Discovery blocks.",
              subchecklist=mining_subchecklist),
        stage("MT5 precursor discovery", "pending", "Find repeatable MT5-native winning precursor families.", 10, 0.0),
        stage("Exact MT5 broker replay", "pending", "Replay frozen MT5 precursors with spread, bid/ask, one-position and LOSS_FIRST semantics.", 8, 0.0),
        stage("Binance strength cross-reference", "pending", "Use Binance only after MT5 precursor rules are frozen.", 8, 0.0, finding="Earlier single-condition experiment raised one MT5 setup from ~45.8% to 91.67%, but produced zero stable â‰¥98% rules."),
        stage("Combined high-precision union", "pending", "Preserve â‰¥98% families and combine non-conflicting executable trades.", 6, 0.0),
        stage("Robustness / delays / friction", "pending", "Re-test surviving combined rules under execution stress scenarios.", 4, 0.0),
        stage("Confirmation", "pending", "73 untouched chronological days.", 3, 0.0),
        stage("Hard Validation", "pending", "55 untouched chronological days.", 2, 0.0),
        stage("Final Holdout", "pending", "54 sealed chronological days.", 2, 0.0),
        stage("Shadow / demo readiness", "pending", "No promotion until all research and validation gates pass.", 1, 0.0),
    ]
    overall = sum(s["weight"] * s["fraction"] for s in stages)
    data_progress = (4.0 + feature_fraction) / 5.0 * 100.0
    validation_progress = 0.0
    working = mining_state == "working"
    active_stage = "MT5 tick backward winner mining" if working else ("MT5 backward mining complete" if mining_state == "complete" else "Awaiting next research stage")
    return {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "system": {"working": bool(working), "label": "WORKING" if working else ("READY FOR NEXT STAGE" if feature_done else "STOPPED"),
                   "active_stage": active_stage, "active_phase": active_phase},
        "progress": {"overall": round(overall, 1), "data_build": round(data_progress, 1), "validation": round(validation_progress, 1)},
        "metrics": {
            "mt5_win_rate": mt5_wr, "mt5_label": "Previous broker-native MT5 baseline",
            "binance_win_rate": bin_wr, "binance_label": "Best prior single Binance confirmation",
            "combined_win_rate": combined_wr, "combined_label": "Current MT5-backward-mined + Binance system",
            "qualifying_trades_per_day": qualifying_tpd, "trade_target_per_day": 100.0,
            "target_win_rate": 98.0
        },
        "counts": {"mt5_ticks": int(atlas.get("ticks", 62299358) or 62299358), "market_days": 365,
                   "mt5_features": 81, "state_days_complete": bin_days, "state_days_total": total_days,
                   "prior_exact_bin_rules": int(bstrength.get("exact_rules_measured", 461040) or 461040),
                   "prior_stable98_rules": int(bstrength.get("stable98_rules", 0) or 0)},
        "stages": stages,
        "notes": [
            "Current active research mines MT5 tick outcomes first; Binance is confirmation only.",
            "No live orders are sent by this research pipeline.",
            "A displayed PENDING metric has not yet been scientifically measured for the current architecture."
        ]
    }

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(build_status(), indent=2), encoding="utf-8")
    tmp.replace(OUT)
    print(OUT)

if __name__ == "__main__":
    main()
