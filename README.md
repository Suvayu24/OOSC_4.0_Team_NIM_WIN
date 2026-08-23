# Oil Risk Command Center

An AI-assisted supply-chain resilience console for India's crude oil imports — a live geopolitical risk map, and a what-if simulator that ranks alternate supply routes and models strategic reserve drawdown when a corridor goes down.

Built for the problem statement **"AI-Driven Energy Supply Chain Resilience for Import-Dependent Economies"**.

---

## 1. The problem

India imports roughly 88% of its crude oil. 40–45% of that volume transits the Strait of Hormuz. Recent years have shown how fragile that is: the 2025 US–Iran standoff, renewed Iranian sanctions, and Red Sea shipping attacks have each disrupted supply and pricing in turn — while India's strategic reserves cover only about **9.5 days** of national consumption.

Existing supply-chain planning tools can't model geopolitical risk in real time, or coordinate a rerouting response across refiners, logistics providers, and reserves in the hours that actually matter during a disruption.

**This project answers four of the challenge's illustrative directions:**

| Direction | Where it lives |
|---|---|
| Geopolitical Risk Intelligence Agent | Risk Engine (backend) → Live Map (frontend) |
| Disruption Scenario Modeller | Simulation tab (corridor closure + advisory) |
| Adaptive Procurement Orchestrator | Simulation tab (top-5 ranked alternate routes) |
| Strategic Reserve Optimisation Agent | Simulation tab (day-by-day drawdown schedule) |

---

## 2. Architecture at a glance

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   React + Vite frontend │  REST   │   FastAPI backend            │
│   (Leaflet map, 2 tabs) │◄───────►│   (Motor / MongoDB, Gemini)  │
│                         │  WS     │                              │
└─────────────────────────┘         └──────────────────────────────┘
```

- **Frontend**: React 18 + Vite, `react-leaflet`/Leaflet for the interactive map, no CSS framework (hand-rolled `index.css`). No demo-fixture dependency at runtime — it fetches from the real backend and falls back to bundled fixtures (`src/data/demoData.js`) only if the backend is unreachable, so the UI is presentable offline too.
- **Backend**: FastAPI + Motor (async MongoDB driver) + Google Gemini (`gemini-2.5-flash`) for two narrow, well-scoped AI tasks — classifying raw signal text, and writing the plain-English procurement/reserve advisory. All ranking, scoring, and scheduling math is deterministic Python, not LLM output.
- **Two tabs**: **Live Map** (current-state monitoring) and **Simulation** (hypothetical "what if this corridor closes" planning) — matching the original two-screen plan.

---

## 3. Feature tour

### 3.1 Live Map tab

- **Interactive world map** (OpenStreetMap tiles via Leaflet) showing every monitored crude corridor as a colored line — green/amber/red by risk tier — plus markers for Indian refineries, Strategic Reserve depots, and the foreign ports/straits each corridor originates from.
- **Legend sidebar**: marker key (refinery / reserve / oil selling point) and the risk color bands (Low 0–44, Medium 45–69, High 70–100).
- **Corridor click → detail panel**: route name, crude grade, distance, live risk score, volume exposed, and — once the procurement detail call resolves — the full landed-cost breakdown (crude price / transport / refining) as proportional bars, plus days-to-supply.
- **Session risk trend chart**: a lightweight line chart of how the selected corridor's risk score has moved since the page loaded, built from real WebSocket ticks (not synthetic data).
- **Trigger event feed**: a running log of real risk-update events received over the session.
- **AI decision panel**: summarizes current priority (high/monitored) and hands off to the Simulation tab to model an actual disruption for that corridor.
- **Live updates**: a WebSocket connection (`/ws/risk-updates`) pushes risk-score changes to the map in real time as new signals are ingested or the demo clock is advanced — no polling.
- **Header stats**: count of monitored corridors, count currently high-risk, and total volume monitored (mb/d).

### 3.2 Simulation tab

- **Scenario selector**: pick a corridor to close and a planning horizon (3–30 days), then run the model.
- **Map reflects the closure**: the chosen corridor renders dashed and grey on the same Leaflet map used in Live Map.
- **Scenario advisory**: a Gemini-generated, plain-English summary of what to do, built around the top-ranked alternate route and its reserve implications.
- **Adaptive Procurement Orchestrator table**: the top-5 ranked alternate routes for the lost volume, each with risk, landed cost/bbl, ETA, and spare capacity — click any row to drill in.
- **Recommended action card**: the currently-selected alternate's lead time, landed cost, and risk, alongside the advisory text.
- **Strategic reserve gauge**: current days-of-cover, the safety floor, and what % of the supply gap the selected alternate covers.
- **Reserve drawdown chart**: a day-by-day bar chart of how many mb/d would be drawn from India's Strategic Petroleum Reserve while the chosen alternate route ramps up.
- **Reserve plan summary**: the specific route, the size of the gap being bridged, and the lead time driving the drawdown schedule.

---

## 4. The math, in full

Every number in this app traces back to one of four deterministic models, plus one narrow LLM step. Nothing here is hard-coded per-scenario — the same formulas run for any corridor you close.

### 4.1 Geopolitical Risk Intelligence (`backend/risk_engine.py`)

**Step 1 — Severity of a single signal.** Each incoming signal (a news alert, an AIS anomaly, a sanctions announcement, etc.) is scored 1–5:

```
S_i = round(clamp(A × (0.6·T + 0.4·C), 1, 5))
```

| Term | Meaning | Range |
|---|---|---|
| `A` | Action intensity — rhetoric (1) up to kinetic strike/blockade (5) | 1–5 |
| `T` | Target specificity — general political noise (0.2) up to a direct strike on a crude tanker/terminal (1.0) | 0.0–1.0 |
| `C` | Actor capability — unverified/low-capability actor (0.5) up to a state military force (1.0) | 0.5–1.0 |

**Step 2 — Time-decayed, source-weighted risk index for a corridor.** Every signal touching that corridor's choke point(s) contributes, decaying exponentially with age:

```
R(c, t) = Σ  w_i · S_i · e^(−λ·(t − t_i))
```

`w_i` is a per-source-type weight (AIS anomaly 0.40, sanctions announcement 0.35, news alert / insurance rate hike / government advisory 0.30–0.25), `λ` is the decay constant (default `0.231`, i.e. roughly a 3-day half-life — `ln(2)/3`), and `(t − t_i)` is the signal's age in days.

**Step 3 — Convert the index to a 0–100 disruption-probability score.** A logistic curve maps the unbounded risk index onto a bounded probability:

```
P(disruption) = 1 / (1 + e^(−k·(R − R₀)))
risk_score    = round(P(disruption) × 100)
```

`k` (steepness, default `1.5`) and `R₀` (the risk index that maps to 50%, default `2.0`) are both tunable via `.env`. This is the number rendered on the Live Map and used everywhere downstream (route ranking, the color of a corridor's line, etc.).

A companion Gemini-based classifier (`classifier.py`) turns free-text news/AIS/sanctions snippets into the structured `(A, T, C, choke_point)` tuple above, gated by a confidence threshold — low-confidence extractions are routed to manual review instead of silently entering the model.

### 4.2 Adaptive Procurement Orchestrator (`backend/orchestrator_engine.py`)

**Cost breakdown per route.** The stored `cost_per_barrel` is an all-in landed figure; the model decomposes it into three line items so procurement can see what's driving the price:

```
transport_cost   = distance_km × FREIGHT_USD_PER_BBL_PER_KM + PORT_HANDLING_USD_PER_BBL
crude_price      = stored_cost_per_barrel − transport_cost
refining_cost    = base_refining_cost × (1 + GRADE_MISMATCH_PENALTY)   if crude grade ∉ refinery's preferred slate
                  = base_refining_cost                                  otherwise
landed_cost      = crude_price + transport_cost + refining_cost
```

`GRADE_MISMATCH_PENALTY` (default 12%) captures the real-world fact that a refinery configured for light sweet crude pays more to process an off-spec heavy sour barrel.

**Ranking alternate routes.** When a corridor (or an entire choke point) closes, every remaining active route is scored for suitability as a replacement, relative to the other candidates in the pool — this is a genuine ranking, not an absolute grade:

```
score = 100 × ( W_RISK·risk_n + W_COST·cost_n + W_CAPACITY·capacity_n + W_SPEED·speed_n )
```

| Component | How it's computed | Weight |
|---|---|---|
| `risk_n` | Min-max normalized risk score across candidates, inverted (lower risk → higher score) | 0.35 |
| `cost_n` | Min-max normalized landed cost, inverted (cheaper → higher score) | 0.30 |
| `capacity_n` | `min(spare_capacity, gap) / gap`, saturating at 100% gap coverage | 0.20 |
| `speed_n` | Min-max normalized days-to-supply (`mobilization_days + transit_days`), inverted | 0.15 |

The top 5 by score are returned. A separate **cumulative coverage** pass then walks the ranked list in order and tracks how much of the lost volume is actually filled if procurement activates routes one at a time — useful for showing "you need the top 2 routes, not just #1."

### 4.3 Strategic Reserve Optimisation Agent (`backend/reserve_engine.py`)

Given the volume gap left by the closure and the lead time before a chosen alternate route is fully online, this simulates a day-by-day drawdown against India's aggregated Strategic Petroleum Reserve pool:

```
supply_from_ramp(day) = 0                      if day < day_online
                       = spare_capacity_bpd     if day ≥ day_online      (step-function ramp)

remaining_gap(day)    = max(0, gap_bpd − supply_from_ramp(day))
drawdown(day)         = min( max_drawdown_rate_bpd,        ← physical pumping/pipeline limit
                              remaining_gap(day),           ← never draw more than the actual shortfall
                              stock(day) − strategic_floor  ← never breach the strategic floor
                            )
stock(day+1)           = stock(day) − drawdown(day)
days_of_cover(day)      = stock(day) / national_daily_consumption_bpd
```

The **strategic floor** is set at 15% of nameplate SPR capacity — a genuine "break glass" level below which the agent should be recommending emergency spot-market purchases in parallel, not more drawdown (surfaced via `strategic_floor_breached`). Any shortfall the ramp-up *and* the reserve together can't cover is reported explicitly as `unmet_shortfall_bpd`, rather than silently hidden.

The plan is summarized into headline numbers — total barrels drawn, minimum days-of-cover reached, days with an uncovered shortfall, and whether the plan fully bridges the gap — which drive the Reserve Gauge and Drawdown Chart on the Simulation tab.

### 4.4 AI Advisory layer (`backend/advisory.py`)

Everything above is deterministic math computed *before* any LLM call. Gemini's only job is to turn the resulting numbers (which route, what gap, what reserve impact) into a short, readable set of actions for a procurement desk — it does not decide the ranking or the schedule, it narrates them. If Gemini is unavailable or the API key isn't set, a deterministic templated recommendation is generated from the same numbers instead, so the feature never goes blank.

---

## 5. Data model

| Model | Key fields |
|---|---|
| `Corridor` | `origin`/`destination` (lat/lng), `waypoints`, `oil_type`, `crude_grade`, `distance_km`, `transit_days`, `cost_per_barrel`, `capacity_bpd`, `current_throughput_bpd`, `choke_points`, `risk_score`, `status`, `destination_refinery_id`, `mobilization_days` |
| `Signal` | `choke_point`, `source_type`, `action_intensity`, `target_specificity`, `actor_capability`, `observed_at`, `raw_text` |
| `Refinery` | `location`, `state`, `capacity_bpd`, `current_processing_bpd`, `base_refining_cost_per_barrel`, `preferred_crude_grades` |
| `ReserveDepot` | `location`, `capacity_barrels`, `current_stock_barrels`, `max_drawdown_rate_bpd`, `linked_refinery_ids` |

Seeded demo dataset: 5 corridors (Hormuz→Jamnagar, Hormuz→Kochi, Bab-el-Mandeb→Kochi, Malacca→Chennai, West Africa→Paradip), 3 Indian refineries (Jamnagar, Kochi, Paradip), 3 Strategic Reserve depots (Visakhapatnam, Mangalore, Padur — India's real SPR caverns).

---

## 6. API reference

### Risk engine (`routers.py`)

| Method & path | Purpose |
|---|---|
| `GET /corridors` | List all corridors with live risk scores |
| `GET /corridors/{id}` | Single corridor |
| `POST /signals` | Ingest a pre-structured signal, recompute affected corridors |
| `POST /signals/classify` | Classify raw text via Gemini, then ingest if confident |
| `POST /demo/seed` | Wipe and reseed corridors |
| `POST /demo/load-timeline` | Load the curated escalating Hormuz signal timeline |
| `POST /demo/advance?step_hours=6` | Fast-forward the demo clock, recompute every corridor |
| `WS /ws/risk-updates` | Live push of `{type: "risk_update", corridorId, riskScore}` |

### Procurement + Reserve (`procurement_router.py`)

| Method & path | Purpose |
|---|---|
| `POST /procurement/demo/seed` | Load refineries + reserve depots, patch corridors (run **after** `/demo/seed`) |
| `GET /procurement/routes/{id}` | Full cost/ETA/risk detail card for one route |
| `GET /procurement/refineries` | Refinery locations, for the map legend |
| `GET /procurement/reserves` | Current state of the aggregated reserve pool |
| `POST /procurement/scenario/block` | Close corridor(s)/choke point(s) → top-N ranked alternates + advisory |
| `POST /procurement/scenario/reserve-plan` | Day-by-day drawdown schedule for one chosen alternate |

`POST /procurement/scenario/block` body: `{ corridor_ids?, choke_points?, top_n?, horizon_days? }` — pass `corridor_ids` to close one named corridor surgically, or `choke_points` (e.g. `["hormuz"]`) to close an entire strait and every corridor through it.

`POST /procurement/scenario/reserve-plan` body: `{ corridor_ids?, choke_points?, alternate_corridor_id, horizon_days? }` — same blocked set as the `/scenario/block` call, plus which of the returned alternates to plan around.

---

## 7. Tech stack

**Frontend**: React 18, Vite, react-leaflet + Leaflet, vanilla CSS.
**Backend**: FastAPI, Motor (async MongoDB), Pydantic v2, Google Gemini (`gemini-2.5-flash`) via `google-genai`.
**Database**: MongoDB (local or Atlas).

---

## 8. Running it

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # fill in MONGO_URI and GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

If `/demo/seed` fails with a generic 500, run `python test_db_connection.py` first — it prints the real Mongo connection error (missing `dnspython`, an IP not allow-listed on Atlas, a paused free-tier cluster, or a credential mismatch).

Seed in order, once the server is up (via `http://localhost:8000/docs`):

1. `POST /demo/seed` — loads corridors
2. `POST /procurement/demo/seed` — loads refineries + reserve depots, patches corridors
3. `POST /demo/load-timeline` (optional) — populates a realistic escalating risk timeline

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local address Vite prints (usually `http://localhost:5173`). Map tiles require an internet connection. Set `VITE_API_URL` (and optionally `VITE_WS_URL`) if the backend isn't at `http://localhost:8000`.

---

## 9. Model assumptions worth knowing before you present this

These are the tunable constants and demo-scale simplifications baked into the math above — none are secret, all are commented at their definition site:

- **Freight cost model** (`orchestrator_engine.py`): `$0.0016/bbl/km` + `$1.20/bbl` handling — an illustrative blended VLCC/Suezmax assumption, not a live freight index.
- **Ranking weights** (risk 35% / cost 30% / capacity 20% / speed 15%) are a starting point, not a validated procurement policy.
- **Strategic Reserve depot capacities** (`procurement_seed.py`) are calibrated so total capacity ÷ assumed national consumption (5.1M bpd) lands close to the real-world "~9.5 days of cover" figure — illustrative, not sourced from official PPAC/EIA data.
- **Risk-scoring calibration** (`decay_lambda`, `logistic_k`, `logistic_r0`) ships with defaults in `config.py`; `calibrate.py` exists specifically to help you tune these against real signal data before trusting the numbers in front of judges.
