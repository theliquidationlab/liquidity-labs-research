# BTC Research & Demo Command Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the coarse public research page with a sanitized, read-only BTC research and demo command center that works from any browser and reflects the actual V3-A research agent and demo bot.

**Architecture:** Keep the existing GitHub Pages deployment and make `export_status.py` the sole public-data boundary. It will read bounded, read-only snapshots from the live bot runtime, research runtime, and SQLite database, shape them into schema version 2, and export only allowlisted fields. The static HTML/CSS/JS client polls the published JSON and renders responsive status cards, tables, and lightweight client-side charts without adding any VPS control surface.

**Tech Stack:** Python 3.12, SQLite read-only queries, pytest, vanilla HTML/CSS/JavaScript, GitHub Pages, existing scheduled publisher.

**Spec:** `docs/superpowers/specs/2026-09-06-btc-command-center-design.md`

## Global Constraints

- Public-by-link with no login; every exported field must be safe for public exposure.
- Never export credentials, API keys, account identifiers, secrets, private network details, raw command lines, environment variables, arbitrary logs, or writable/control endpoints.
- Keep the dashboard strictly read-only; no bot controls, restart/trade buttons, POST endpoints, config editors, or VPS mutation links.
- Keep the existing GitHub Pages URL, QR code, publisher task, and five-minute publisher model.
- Browser refresh interval remains 60 seconds; stale exported data must be visibly flagged.
- Existing V3-A trading and research behavior must remain untouched.

---### Task 1: Public-data boundary and schema v2

**Files:**
- Modify: `export_status.py`
- Modify: `test_export_status.py`

**Interfaces:**
- Consumes: local JSON runtime files and UTC timestamps.
- Produces: `load_json(path) -> dict`, `freshness(path, now=None) -> dict`, `health_state(age_seconds, warn_after, bad_after) -> str`, `sanitize_public(value) -> JSON-safe value`, and `build_status() -> dict` with `schema_version: 2`.

- [ ] **Step 1: Write failing safety/schema tests**

Add tests asserting `build_status()` contains `schema_version == 2`, `generated_utc`, and top-level sections `live`, `research`, `signals`, `promotions`, `history`, `trading`, and `health`. Add a recursive key/value scan that fails on `password`, `secret`, `token`, `api_key`, `account`, `login`, `private_ip`, `commandline`, `C:\\`, and `172.31.`.

- [ ] **Step 2: Run tests and verify RED**

Run: `py -3.12 -m pytest -q test_export_status.py`
Expected: failures because schema v2 and sanitizer helpers do not exist yet.

- [ ] **Step 3: Implement the safety helpers and schema shell**

Add constants for `LIVE_ROOT`, `RESEARCH_ROOT`, `RESEARCH_DB`, and bounded stale thresholds. Implement tolerant JSON loading with `utf-8-sig`, UTC age calculation, three-state health classification, and a sanitizer that only accepts primitives/lists/dicts already selected by explicit shaping functions. Do not serialize arbitrary objects or raw runtime payloads.

- [ ] **Step 4: Run Task 1 tests and verify GREEN**

Run: `py -3.12 -m pytest -q test_export_status.py`
Expected: new schema/safety tests pass while legacy exporter tests remain green.

- [ ] **Step 5: Commit Task 1**

Run: `git add export_status.py test_export_status.py && git commit -m "feat: add safe command center schema"`

---### Task 2: Live bot, research brain, and system-health summaries

**Files:**
- Modify: `export_status.py`
- Modify: `test_export_status.py`

**Interfaces:**
- Consumes: `BTC_MICRO_ORB_V5/runtime/status.json`, `state.json`, `heartbeat.json`, latest `candidate_audit.jsonl` row, and V3-A heartbeats/status JSON files.
- Produces: `build_live_summary() -> dict`, `build_research_summary() -> dict`, `build_health_matrix() -> list[dict]`.

- [ ] **Step 1: Write failing shaping tests**

Create temp fixtures for live/research runtime snapshots. Assert the live summary exposes only decision, side, path/family, trigger, five-minute phase, quote/spread, order-book/flow/OI readiness, and sanitized supply/demand context. Assert research exposes model preference/residency, GPU tunnel, supervisor/collector/MT5/watchdog freshness, current phase, last deep-search time, last directed family, and a short model-error classification without raw log bodies.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `py -3.12 -m pytest -q test_export_status.py -k "live or research or health"`
Expected: failures because summary builders are absent.

- [ ] **Step 3: Implement bounded snapshot readers**

Read only named files, parse only allowlisted fields, and tail at most one candidate-audit JSONL record when needed. Represent missing/corrupt sources as `UNKNOWN`; never propagate exceptions into `build_status()`. Build health rows for bot heartbeat/status, collector, MT5 sync, GPU tunnel, supervisor, watchdog, and live-feed semantics with `GREEN`, `AMBER`, or `RED` plus rounded age seconds.

- [ ] **Step 4: Run focused and full exporter tests**

Run: `py -3.12 -m pytest -q test_export_status.py`
Expected: all exporter tests pass.

- [ ] **Step 5: Commit Task 2**

Run: `git add export_status.py test_export_status.py && git commit -m "feat: expose live research health summaries"`

---### Task 3: Strong-signal discovery, promotions, verifier history, and demo trading summaries

**Files:**
- Modify: `export_status.py`
- Modify: `test_export_status.py`

**Interfaces:**
- Consumes: `deep_signal_search_latest.json`, `advanced_candidate_shortlist.json`, `demo_promotions.json`, and read-only SQLite tables `proposals`, `evaluations`, `agent_runs`, and `trades`.
- Produces: `summarize_candidate(candidate) -> dict`, `build_signal_discovery(limit=24) -> dict`, `build_promotions() -> list[dict]`, `build_history(limit=30) -> dict`, `build_trading(limit=30) -> dict`.

- [ ] **Step 1: Write failing candidate/promotion/history/trade tests**

Use compact fixtures asserting: opportunity/day equals `opportunities_per_hour * 24`; canary and full candidates are labeled separately; promotion output includes proposal/family/tier/verifier/evidence health but not raw file paths; verifier failures preserve rejection reasons; trade output contains side/family/result/profit and rolling wins/losses/win-rate while omitting position/account identifiers.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `py -3.12 -m pytest -q test_export_status.py -k "candidate or promotion or history or trading"`
Expected: failures because the shaping functions are absent.

- [ ] **Step 3: Implement bounded candidate and promotion shaping**

Prefer the latest deep-search shortlist, fall back to the advanced shortlist, cap public rows at 24, and expose sample counts, PF, expectancy, validation/recent metrics, walk-forward metrics, frequency/hour, frequency/day, and eligibility. Read active promotions only from the registry and summarize the rule into a compact allowlisted condition list rather than exporting the entire raw registry object.

- [ ] **Step 4: Implement read-only SQLite history and trading queries**

Open SQLite with URI `mode=ro`, set a short timeout, use explicit column lists, `ORDER BY id DESC LIMIT ?`, and decode JSON fields only to extract named metrics/reasons. Return empty arrays if the DB is locked/unavailable; never export `tool_log_json`, raw prompts, raw payloads, position IDs, volume, entry price, exit price, or broker metadata.

- [ ] **Step 5: Run focused and full exporter tests, then commit**

Run: `py -3.12 -m pytest -q test_export_status.py`
Expected: all tests pass.
Run: `git add export_status.py test_export_status.py && git commit -m "feat: add signals promotions history and trades"`

---### Task 4: Responsive command-center UI and lightweight charts

**Files:**
- Modify: `index.html`
- Modify: `styles.css`
- Modify: `app.js`
- Modify: `test_dashboard_ui.py`

**Interfaces:**
- Consumes: schema-v2 `data/status.json` sections from Tasks 1-3.
- Produces: a read-only responsive browser UI with IDs `livePanel`, `researchPanel`, `signalPanel`, `promotionPanel`, `historyPanel`, `tradingPanel`, `healthPanel`, and `staleBanner`.

- [ ] **Step 1: Write failing UI structure/safety tests**

Assert all seven panels and `staleBanner` exist; viewport metadata remains present; the page contains no `<form`, `method="post"`, `restart`, `place order`, `trade now`, or config-edit controls. Assert `app.js` polls every 60,000 ms and contains renderers for live, research, signals, promotions, history, trading, and health.

- [ ] **Step 2: Run UI tests and verify RED**

Run: `py -3.12 -m pytest -q test_dashboard_ui.py`
Expected: failures because the command-center panels/renderers are not yet present.

- [ ] **Step 3: Replace coarse markup with command-center sections**

Keep the Liquidity Labs identity, URL, and QR code. Put a compact current-state strip above the fold, then responsive cards/tables for live bot, research brain, strong-signal discovery, promotions, verifier/research history, demo trading results, and system health. Use semantic headings and mobile card fallbacks so critical status does not require horizontal scrolling.

- [ ] **Step 4: Implement schema-v2 rendering and stale behavior**

In `app.js`, fetch the same public JSON URL with cache busting, validate `schema_version === 2`, render every section defensively, and show `staleBanner` when generated data is older than 20 minutes. Render four dependency-free mini charts using CSS bars generated from sanitized arrays: family PF/quality, promotion tier counts, research PASS/CANARY/FAIL counts, and recent trade wins/losses. A chart rendering failure must not stop textual sections.

- [ ] **Step 5: Implement responsive styling and run UI tests**

Use CSS grid with desktop two/three-column layouts and a single-column breakpoint below 760px. Tables become stacked cards or overflow-safe blocks on small screens. Run `py -3.12 -m pytest -q test_dashboard_ui.py` and expect all UI tests to pass.

- [ ] **Step 6: Commit Task 4**

Run: `git add index.html styles.css app.js test_dashboard_ui.py && git commit -m "feat: build responsive BTC command center UI"`

---### Task 5: End-to-end export, sensitive-data scan, and deployment verification

**Files:**
- Modify if needed: `publisher.py`
- Modify if needed: `test_export_status.py`
- Modify if needed: `test_dashboard_ui.py`
- Generated: `data/status.json`

**Interfaces:**
- Consumes: complete exporter/UI from Tasks 1-4.
- Produces: a verified schema-v2 public snapshot and successful GitHub Pages publish with no trading/research process changes.

- [ ] **Step 1: Run the complete dashboard test suite**

Run: `py -3.12 -m pytest -q`
Expected: all dashboard tests pass with exit code 0.

- [ ] **Step 2: Generate a fresh public snapshot**

Run: `py -3.12 export_status.py`
Expected: `data/status.json` is atomically replaced and contains `schema_version: 2` plus all command-center sections.

- [ ] **Step 3: Run a hard sensitive-data scan**

Run a Python scanner over the serialized JSON and static assets. Fail deployment if output contains known VPS drive paths, `172.31.`, `password`, `secret`, `token`, `api_key`, `account_number`, `login`, `position_id`, `tool_log_json`, or mutation verbs/controls. Manually inspect the top-level JSON keys and one row from each public section.

- [ ] **Step 4: Verify the exporter against live missing/stale conditions**

Temporarily point unit-test fixtures at missing/corrupt files only; do not alter production runtime files. Confirm exporter tests show `UNKNOWN`/empty sections rather than crashes, and stale classification changes to amber/red at configured thresholds.

- [ ] **Step 5: Publish once through the existing publisher path**

Run: `py -3.12 -c "import publisher; print(publisher.publish_once())"`
Expected: `PUSHED` or `NO_CHANGE` with exit code 0. Do not open VPS inbound ports and do not alter the trading/research scheduled tasks.

- [ ] **Step 6: Verify the public GitHub Pages payload and commit final integration**

Fetch the public `data/status.json` and page once after the push, confirm schema v2 and a recent `generated_utc`, then run `git status --short`. Commit any final test/deployment-only changes with `git add -A && git commit -m "chore: verify command center deployment"`; if there are no changes, record the clean status instead.

## Completion Evidence

The feature is complete only when the full pytest suite exits 0, the fresh public JSON passes the sensitive-data scan, the publisher exits 0, the remote page serves schema version 2, and no BTC bot/research source or scheduled trading/research task was modified by this dashboard work.

## Spec Coverage Map

- Live Demo Bot: Task 2 exporter + Task 4 `livePanel`.
- Research Brain: Task 2 exporter + Task 4 `researchPanel`.
- Strong Signal Discovery: Task 3 candidate shaping + Task 4 `signalPanel`.
- Promotions: Task 3 registry shaping + Task 4 `promotionPanel`.
- Verifier & Research History: Task 3 DB shaping + Task 4 `historyPanel`.
- Demo Trading Results: Task 3 trade shaping + Task 4 `tradingPanel`.
- System Health: Task 2 health matrix + Task 4 `healthPanel`.
- Presentation/refresh/stale behavior: Task 4.
- Safety/export architecture/testing/deployment: Tasks 1 and 5.