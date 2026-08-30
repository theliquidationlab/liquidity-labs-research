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
FRONTIER_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_TICK_PRECURSOR_FRONTIER_V1" / "00_STATUS.json"
FRONTIER_WORK_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_PRECURSOR_FRONTIER_V1_WORK" / "PROGRESS.json"
FRONTIER_FINAL_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_PRECURSOR_FRONTIER_V1" / "PROGRESS.json"
SEQ_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1" / "00_STATUS.json"
SEQ_WORK_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1_WORK" / "PROGRESS.json"
SEQ_FINAL_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1" / "PROGRESS.json"
CORRECTION_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_DISCOVERY_BOUNDARY_CENSOR_CORRECTION_V1" / "00_STATUS.json"
CORRECTED_PAIR_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_TICK_PRECURSOR_FRONTIER_V2_BOUNDARY_CENSORED" / "00_STATUS.json"
CORRECTED_SEQ_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V2_BOUNDARY_CENSORED" / "00_STATUS.json"
BROKER_FINAL = ROOT / "12_LIVE_PARITY" / "MT5_PRECURSOR_BROKER_SCREEN_V1" / "00_STATUS.json"
BROKER_WORK_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_PRECURSOR_BROKER_SCREEN_V1_WORK" / "PROGRESS.json"
BROKER_FINAL_PROGRESS = ROOT / "12_LIVE_PARITY" / "MT5_PRECURSOR_BROKER_SCREEN_V1" / "PROGRESS.json"
BROKER_STDERR = ROOT / "RUNS" / "mt5_precursor_broker_screen_v1.stderr.log"

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

def frontier_stage_state(progress, final_status, active_phase, running):
    if final_status.get("complete"):
        pairs=int(final_status.get("pair_candidates",0) or 0)
        stable=int(final_status.get("stable_enriched_pairs",0) or 0)
        return "complete", 1.0, f"183/183 Discovery days pair-screened; {pairs:,} retained pairs measured; {stable:,} stable-enriched pairs preserved.", progress.get("checklist", {})
    done=int(progress.get("days_complete",0) or 0)
    total=int(progress.get("days_total",183) or 183)
    pairs=int(progress.get("pair_candidates",572000) or 572000)
    fraction=max(0.0,min(1.0,float(progress.get("percent",0.0) or 0.0)/100.0))
    if active_phase=="MT5_TICK_PRECURSOR_FRONTIER_V1" and running:
        return "working", fraction, f"{done}/{total} Discovery days screening {pairs:,} retained concurrent MT5 pairs.", progress.get("checklist", {})
    return "pending", fraction, f"{done}/{total} pair-screen days complete; frontier worker is not currently active.", progress.get("checklist", {})
def precursor_stage_state(frontier_final, seq_progress, seq_final, active_phase, seq_running):
    pair_done=bool(frontier_final.get("complete")); pair_pct=100.0 if pair_done else 0.0
    seq_pct=max(0.0,min(100.0,float(seq_progress.get("percent",0.0) or 0.0)))
    sub={"concurrent_pair_frontier":pair_pct}; sub.update(seq_progress.get("checklist",{}) or {})
    if seq_final.get("complete"):
        stable=int(seq_final.get("stable_enriched_temporal",0) or 0)
        return "complete",1.0,f"Concurrent pairs and 1s/2s/5s temporal frontier complete; {stable:,} stable-enriched temporal precursors preserved.",sub
    fraction=(0.5 if pair_done else 0.0)+(0.5*seq_pct/100.0)
    done=int(seq_progress.get("days_complete",0) or 0); total=int(seq_progress.get("days_total",183) or 183)
    n=int(seq_progress.get("transition_candidates",3492438) or 3492438)
    if active_phase=="MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1" and seq_running:
        return "working",fraction,f"{done}/{total} Discovery days screening {n:,} ordered 1s/2s/5s MT5 transitions/persistence candidates.",sub
    return "pending",fraction,f"Pair frontier complete; temporal frontier is {seq_pct:.2f}% complete.",sub

def broker_stage_state(progress, final_status, active_phase, running, stderr_bytes):
    cond=int(final_status.get("conditions_total",progress.get("conditions_total",733848)) or 733848)
    geom=int(final_status.get("geometry_total",progress.get("geometry_total",1638)) or 1638)
    anchors=int(progress.get("anchor_B1_survivors",final_status.get("anchor_B1_survivors",0)) or 0)
    raw95=int(progress.get("raw95_survivors",final_status.get("raw95_survivors",0)) or 0)
    final98=int(progress.get("exact98_finalists",final_status.get("exact98_finalists",0)) or 0)
    sub={"conditions":cond,"geometries":geom,"anchor_b1_survivors":anchors,"raw_95_survivors":raw95,"exact_98_finalists":final98,"stderr_bytes":int(stderr_bytes or 0)}
    if final_status.get("complete"):
        return "complete",1.0,f"Exact MT5 broker certification complete; {raw95:,} raw ≥95% families and {final98:,} exact ≥98% one-position finalists from {cond:,} corrected precursor masks.",sub
    pctv=max(0.0,min(100.0,float(progress.get("percent",0.0) or 0.0)))
    phase=str(progress.get("active_stage","pending")).replace("_"," ")
    done=int(progress.get("days_complete",0) or 0); total=int(progress.get("days_total",183) or 183)
    detail=f"{phase}; {cond:,} corrected conditions × {geom:,} broker geometries"
    if done: detail+=f"; {done}/{total} days complete"
    if raw95 or final98: detail+=f"; raw ≥95%: {raw95:,}; exact ≥98%: {final98:,}"
    if active_phase=="MT5_PRECURSOR_BROKER_SCREEN_V1" and running:
        return "working",pctv/100.0,detail,sub
    return "pending",pctv/100.0,detail+"; broker worker is not currently active.",sub

def build_status():
    atlas = load_json(MT5_ATLAS)
    base = load_json(MT5_BASE)
    bstrength = load_json(BIN_STRENGTH)
    correction = load_json(CORRECTION_FINAL)
    corrected_pair = load_json(CORRECTED_PAIR_FINAL)
    corrected_seq = load_json(CORRECTED_SEQ_FINAL)
    broker_final = load_json(BROKER_FINAL)
    broker_progress = load_json(BROKER_FINAL_PROGRESS) or load_json(BROKER_WORK_PROGRESS)
    bin_days, total_days, feature_done = feature_progress()
    active = load_json(ACTIVE_WORKER)
    active_phase = str(active.get("phase", ""))
    mining_final = load_json(MINING_FINAL)
    mining_progress = load_json(MINING_FINAL_PROGRESS) or load_json(MINING_WORK_PROGRESS)
    mining_running = (active_phase == "MT5_TICK_BACKWARD_WINNER_MINING_V1" and str(mining_progress.get("state", "")).upper() == "RUNNING") or process_running("mt5_tick_backward_winner_mining_v1.py")
    mining_state, mining_fraction, mining_detail, mining_subchecklist = mining_stage_state(
        mining_progress, mining_final, active_phase, mining_running)
    frontier_final = load_json(FRONTIER_FINAL)
    frontier_progress = load_json(FRONTIER_FINAL_PROGRESS) or load_json(FRONTIER_WORK_PROGRESS)
    frontier_running = (active_phase == "MT5_TICK_PRECURSOR_FRONTIER_V1" and str(frontier_progress.get("state", "")).upper() == "RUNNING") or process_running("mt5_tick_precursor_frontier_v1.py")
    frontier_state, frontier_fraction, frontier_detail, frontier_subchecklist = frontier_stage_state(
        frontier_progress, frontier_final, active_phase, frontier_running)
    seq_final = load_json(SEQ_FINAL)
    seq_progress = load_json(SEQ_FINAL_PROGRESS) or load_json(SEQ_WORK_PROGRESS)
    seq_running = (active_phase == "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1" and str(seq_progress.get("state", "")).upper() == "RUNNING") or process_running("mt5_tick_sequence_persistence_frontier_v1.py")
    precursor_state, precursor_fraction, precursor_detail, precursor_subchecklist = precursor_stage_state(
        frontier_final, seq_progress, seq_final, active_phase, seq_running)
    if correction.get("complete"):
        precursor_state="complete"; precursor_fraction=1.0
        precursor_detail=f"Boundary-corrected MT5 precursor census complete: 4,402 stable singles, {int(corrected_pair.get('stable_enriched_pairs',540672)):,} stable pairs and {int(corrected_seq.get('stable_enriched_temporal',3355724)):,} stable temporal rows."
        precursor_subchecklist={"boundary_correction":100.0,"corrected_single_catalog":100.0,"corrected_pair_frontier":100.0,"corrected_temporal_frontier":100.0}
    try: broker_stderr_bytes=BROKER_STDERR.stat().st_size
    except Exception: broker_stderr_bytes=0
    broker_running=(active_phase=="MT5_PRECURSOR_BROKER_SCREEN_V1" and str(broker_progress.get("state","")).upper()=="RUNNING") or process_running("mt5_precursor_broker_screen_v1.py")
    broker_state,broker_fraction,broker_detail,broker_subchecklist=broker_stage_state(broker_progress,broker_final,active_phase,broker_running,broker_stderr_bytes)

    best=broker_final.get("best_finalist",{}) or broker_final.get("branch_decision",{}).get("best_finalist",{}) or {}
    mt5_wr = pct(best.get("full_wr")) if best else None
    bin_wr = pct(bstrength.get("branch_decision", {}).get("best_full_wr"))
    combined_wr = None
    qualifying_tpd = float(best.get("trades_per_day",0.0) or 0.0) if best else 0.0
    feature_fraction = min(1.0, bin_days / 365.0)

    stages = [
        stage("Full-year PU Prime MT5 tick history", "complete", "365/365 BTCUSD days cached from PUPrime-Demo.", 8, finding="62,299,358 historical bid/ask ticks available."),
        stage("+$1-at-0.01 MT5 outcome atlas", "complete", "Every tick labeled for a +$100 BTC move using executable bid/ask sides.", 12, finding="BUY askÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢future bid; SELL bidÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢future ask; 900-second forward path."),
        stage("MT5 causal tick feature engine", "complete", "81 causal tick-level broker features built and regression tested.", 6, finding="Uses bid/ask microstructure, spread, velocity, range, efficiency, pressure and range position."),
        stage("Discovery threshold fitting", "complete", "Thresholds fitted only on the 183-day Discovery period.", 6, finding="Untouched Confirmation/Hard/Holdout outcomes were not used for fitting."),
        stage("Full-year MT5 state matrix", "complete" if feature_done else "working", f"{bin_days}/365 days binned with frozen MT5 thresholds.", 12, feature_fraction, finding="This creates the searchable MT5 state infrastructure for backward winner mining."),
        stage("Backward mining of +$1 winners", mining_state, mining_detail, 12, mining_fraction,
              finding="All 810 exact MT5 states are measured against hit and non-hit controls across both directions, nine horizons and six Discovery blocks.",
              subchecklist=mining_subchecklist),
        stage("MT5 precursor discovery", precursor_state, precursor_detail, 10, precursor_fraction,
              finding="Concurrent pairs plus the exhaustive 1s/2s/5s ordered transition/persistence frontier define the MT5-native precursor search; raw target hits are not final trade wins.",
              subchecklist=precursor_subchecklist),
        stage("Exact MT5 broker replay", broker_state, broker_detail, 6, broker_fraction,
              finding="Corrected 733,848 precursor masks are screened across the full 1,638-geometry PU Prime grid; final families require exact chronological one-position ≥98% certification.",
              subchecklist=broker_subchecklist),
        stage("MT5 signal build-up construction", "pending", "Combine broker-certified current/1s/2s/5s precursor pieces into exact causal build-up definitions, then broker-replay the completed sequences before Binance.", 4, 0.0,
              finding="This stage answers what forms first, what confirms next, and the exact terminal MT5 state that turns a build-up into a proper entry."),
        stage("Binance strength cross-reference", "pending", "Use Binance only after MT5 precursor and signal-build-up rules are frozen.", 6, 0.0, finding="Earlier single-condition experiment raised one MT5 setup from ~45.8% to 91.67%, but produced zero stable ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¥98% rules."),
        stage("Combined high-precision union", "pending", "Preserve ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¥98% families and combine non-conflicting executable trades.", 6, 0.0),
        stage("Robustness / delays / friction", "pending", "Re-test surviving combined rules under execution stress scenarios.", 4, 0.0),
        stage("Confirmation", "pending", "73 untouched chronological days.", 3, 0.0),
        stage("Hard Validation", "pending", "55 untouched chronological days.", 2, 0.0),
        stage("Final Holdout", "pending", "54 sealed chronological days.", 2, 0.0),
        stage("Shadow / demo readiness", "pending", "No promotion until all research and validation gates pass.", 1, 0.0),
    ]
    overall = sum(s["weight"] * s["fraction"] for s in stages)
    data_progress = (4.0 + feature_fraction) / 5.0 * 100.0
    validation_progress = 0.0
    working = broker_state == "working" or precursor_state == "working" or frontier_state == "working" or mining_state == "working"
    if broker_state == "working": active_stage = "MT5 broker certification: " + str(broker_progress.get("active_stage","working")).replace("_"," ")
    elif broker_state == "complete": active_stage = "MT5 broker certification complete"
    elif precursor_state == "working" and active_phase == "MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1": active_stage = "MT5 sequence / persistence frontier"
    elif frontier_state == "working": active_stage = "MT5 precursor concurrent-pair frontier"
    elif mining_state == "working": active_stage = "MT5 tick backward winner mining"
    elif precursor_state == "complete": active_stage = "MT5 precursor discovery complete; broker certification ready"
    elif frontier_state == "complete": active_stage = "MT5 precursor pair frontier complete"
    elif mining_state == "complete": active_stage = "MT5 backward mining complete"
    else: active_stage = "Awaiting next research stage"
    return {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "system": {"working": bool(working), "label": "WORKING" if working else ("READY FOR NEXT STAGE" if feature_done else "STOPPED"),
                   "active_stage": active_stage, "active_phase": active_phase},
        "progress": {"overall": round(overall, 1), "data_build": round(data_progress, 1), "validation": round(validation_progress, 1)},
        "metrics": {
            "mt5_win_rate": mt5_wr, "mt5_label": "Best exact MT5 broker-certified family" if mt5_wr is not None else "Exact MT5 broker certification pending",
            "binance_win_rate": bin_wr, "binance_label": "Best prior single Binance confirmation",
            "combined_win_rate": combined_wr, "combined_label": "Current MT5-backward-mined + Binance system",
            "qualifying_trades_per_day": qualifying_tpd, "trade_target_per_day": 100.0,
            "target_win_rate": 98.0
        },
        "counts": {"mt5_ticks": int(atlas.get("ticks", 62299358) or 62299358), "market_days": 365,
                   "mt5_features": 81, "state_days_complete": bin_days, "state_days_total": total_days,
                   "prior_exact_bin_rules": int(bstrength.get("exact_rules_measured", 461040) or 461040),
                   "prior_stable98_rules": int(bstrength.get("stable98_rules", 0) or 0),
                   "broker_conditions": int(broker_subchecklist.get("conditions",733848)),
                   "broker_geometries": int(broker_subchecklist.get("geometries",1638)),
                   "broker_anchor_survivors": int(broker_subchecklist.get("anchor_b1_survivors",0)),
                   "broker_raw95_survivors": int(broker_subchecklist.get("raw_95_survivors",0)),
                   "broker_exact98_finalists": int(broker_subchecklist.get("exact_98_finalists",0))},
        "broker": {"broker_stage": str(broker_progress.get("active_stage","complete" if broker_final.get("complete") else "pending")),
                   "broker_progress": round(broker_fraction*100.0,2),
                   "broker_conditions": int(broker_subchecklist.get("conditions",733848)),
                   "broker_geometries": int(broker_subchecklist.get("geometries",1638)),
                   "broker_anchor_survivors": int(broker_subchecklist.get("anchor_b1_survivors",0)),
                   "broker_raw95_survivors": int(broker_subchecklist.get("raw_95_survivors",0)),
                   "broker_exact98_finalists": int(broker_subchecklist.get("exact_98_finalists",0)),
                   "broker_health": "HEALTHY" if (broker_final.get("complete") or (broker_running and broker_stderr_bytes==0)) else ("ERROR" if broker_stderr_bytes else "WAITING"),
                   "broker_error_bytes": int(broker_stderr_bytes),
                   "days_complete": int(broker_progress.get("days_complete",183 if broker_final.get("complete") else 0) or 0),
                   "days_total": int(broker_progress.get("days_total",183) or 183)},
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
