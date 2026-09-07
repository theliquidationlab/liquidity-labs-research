# BTC Research & Demo Command Center — Design

## Goal
Replace the current coarse public research page with one read-only command center that can be opened from any phone, tablet, or laptop and reflects the actual V3-A research agent and demo bot state.

The site remains public-by-link with no login, so every exported field must be safe for public exposure. The dashboard must never expose credentials, API keys, account identifiers, secrets, private network details, writable endpoints, or controls that can alter the bot.

## Existing foundation
The current dashboard already publishes static JSON and GitHub Pages assets from `C:\LiquidityLabs\BTC_RESEARCH_DASHBOARD` every five minutes. The implementation will keep this deployment model and expand `export_status.py`, `data/status.json`, `index.html`, `styles.css`, and `app.js` rather than creating a second monitoring service.

Primary data sources will be read-only snapshots from:
- `BTC_MICRO_ORB_V5\runtime` for live demo status, signal state, futures flow/book/OI, and recent events.
- `BTC_V3A_RESEARCH_AGENT\runtime` for health, model/GPU state, active promotions, learning state, deep-search output, advanced shortlist, and heartbeats.
- `BTC_V3A_RESEARCH_AGENT\reports` and `research.db` for verifier history, research runs, proposal outcomes, and trade/research summaries.

## Safety boundary
Only explicitly allowlisted fields may be exported. Paths are reduced to harmless component labels. No environment variables, raw command lines, account numbers, credentials, tokens, broker login data, private IPs, or arbitrary log bodies are published.

The web UI is strictly read-only. There are no POST endpoints, bot controls, restart buttons, trade buttons, config editors, or links that can mutate the VPS.
## Dashboard sections
### 1. Live Demo Bot
Show running state, demo-only status, current decision, side, signal path, trigger, five-minute phase, quote freshness, spread, order-book readiness, futures-flow readiness, OI readiness, and the active 10-minute supply/demand context. Display stale/warmup conditions prominently.

### 2. Research Brain
Show Frontier model name, preferred/fallback state, GPU tunnel health, supervisor state, collector/MT5 sync/watchdog freshness, current research phase, last deep search, last directed research family, and latest model timeout/error if present.

### 3. Strong Signal Discovery
Render the latest advanced/deep-search shortlist by family. For each candidate show sample size, training/validation/recent results, PF, expectancy, walk-forward stability, estimated opportunities/hour, estimated opportunities/day, objective, and canary/full eligibility. Separate verifier-eligible candidates from exploratory near-misses.

### 4. Promotions
Show all active `DEMO_CANARY` and `FULL` promotions with proposal ID, family, rule summary, promotion time, matched sample, PF/expectancy, health review state, new resolved evidence, and verifier decision/status. Clearly distinguish sample-limited canaries from fully validated promotions.

### 5. Verifier & Research History
Show recent proposals and directed/hourly research runs with timestamp, family, outcome, critic verdict, verifier result, rejection reasons, and whether a promotion occurred. Failures remain visible so progress is not presented as only successful outcomes.

### 6. Demo Trading Results
Show recent completed demo trades, family, side, result, R/PnL fields when safely available, and rolling counts. Summaries include wins/losses, win rate, and trade frequency. Any broker/account identifiers are omitted.

### 7. System Health
Show a compact health matrix for bot heartbeat/status, collector, MT5 sync, GPU tunnel, research supervisor, watchdog, and feed semantics. Each item includes freshness age and green/amber/red state.
## Presentation and refresh behavior
The page uses a responsive dashboard layout that works on phone, tablet, and desktop. The most important current-state cards remain above the fold. Detailed tables collapse cleanly on small screens and never require horizontal scrolling for basic status.

The page polls the published JSON every 60 seconds. The VPS publisher remains responsible for refreshing and pushing sanitized data. If the exported data is older than the configured stale threshold, the entire dashboard displays a visible stale-data warning rather than silently showing old information as current.

Charts use client-side rendering only and are fed by sanitized summary/history arrays in `status.json`. Initial charts cover signal-family quality, promotions, research outcomes, and recent trade results. The page must remain usable if charts fail to render.

## Export architecture
`export_status.py` becomes the single public-data boundary. It will use small helper functions for safe JSON reads, freshness calculations, rule summarization, candidate summarization, promotion summarization, verifier history, research history, and trade summaries.

The exporter must tolerate missing/corrupt runtime files and return `UNKNOWN`/empty sections without crashing the publisher. SQLite reads use read-only queries and bounded result limits. No raw database payloads are exported.

The output schema will be versioned so the UI can detect incompatible data. Existing legacy research fields may remain temporarily for backward compatibility, but new UI code will use the new command-center sections.

## Testing
Tests will cover the sanitizer/allowlist boundary, missing-file behavior, deep-search frequency calculations, canary/full promotion labeling, verifier-history shaping, trade-history shaping, stale-health classification, schema presence, and absence of sensitive keys/paths.

UI tests will verify required sections/IDs, responsive-friendly markup, stale-state behavior, and that the page never exposes mutation controls.

Before deployment, the full dashboard test suite will pass, a fresh export will be inspected for secrets/sensitive paths, and the GitHub Pages publisher will be run once to confirm a successful push.
## Deployment
Keep the existing GitHub Pages URL and publisher task. The publisher continues committing only generated public dashboard data and static assets. Deployment does not change the trading or research processes and does not require opening inbound VPS ports.

The QR code and bookmarkable URL remain available so the same page can be opened from any device with a browser.

## Success criteria
- One public read-only URL works on phone, tablet, and laptop.
- Live demo bot state and stale-feed conditions are visible within the publishing/refresh interval.
- Current Frontier research activity, last deep search, and model/GPU health are visible.
- Strong candidate rules show quality metrics and realistic opportunity-frequency estimates.
- Active canary/full promotions are clearly differentiated and show ongoing evidence health.
- Recent verifier/research outcomes include failures and reasons, not only successes.
- Recent demo trading results and rolling summaries are visible without exposing broker/account secrets.
- A health matrix immediately shows when any monitored subsystem is stale or failing.
- Exported JSON passes a sensitive-data scan and contains no control capability.
- Existing V3-A trading and research behavior is untouched by the dashboard deployment.
