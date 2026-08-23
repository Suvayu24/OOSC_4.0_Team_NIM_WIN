"""
Adaptive Procurement Orchestrator + Strategic Reserve Optimisation Agent.

Endpoints (all prefixed /procurement):
  POST /procurement/demo/seed              seed refineries + reserve depots, patch corridors
  GET  /procurement/routes/{corridor_id}   full detail card for one route (map click)
  GET  /procurement/refineries             refinery locations, for the map's refinery markers
  GET  /procurement/reserves               current state of India's strategic reserve pool
  POST /procurement/scenario/block         close corridor(s)/choke point(s) -> ranked top-N alternates + advisory
  POST /procurement/scenario/reserve-plan  day-by-day drawdown schedule for ONE chosen alternate

Frontend flow for the Simulation tab:
  1. User closes a corridor on the map -> POST /scenario/block -> render the top-5 cards.
  2. User clicks one of the 5 cards -> POST /scenario/reserve-plan with that corridor's id
     -> render the daily drawdown chart + reserve-specific advisory.
"""
from dataclasses import asdict
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter

from advisory import generate_advisory
from db import db
from orchestrator_engine import (
    RouteCandidate,
    crude_price_per_barrel,
    cumulative_coverage,
    landed_cost_total,
    rank_alternate_routes,
    refining_cost_per_barrel,
    transport_cost_per_barrel,
)
from procurement_models import BlockRequest, ReservePlanRequest
from procurement_seed import (
    CORRIDOR_PATCHES,
    INDIA_DAILY_CONSUMPTION_BPD,
    SEED_REFINERIES,
    SEED_RESERVE_DEPOTS,
)
from reserve_engine import ReservePool, build_drawdown_plan, summarize_plan
from routers import current_time   # reuse the same demo clock the risk engine uses

router = APIRouter(prefix="/procurement", tags=["procurement"])

DEFAULT_REFINING_COST = 4.50   # used only when a corridor has no destination_refinery_id on record


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _route_detail(corridor: dict, refinery: Optional[dict], now, cold_start: bool) -> dict:
    """
    Builds the full detail card for a single route -- what renders when you
    click it on either map. cold_start=True adds mobilization_days to the
    ETA (route isn't currently flowing, e.g. it's being proposed as a
    replacement); cold_start=False is for an already-active corridor.
    """
    distance_km = corridor["distance_km"]
    transit_days = corridor["transit_days"]
    mobilization_days = corridor.get("mobilization_days", 2.0)
    crude_grade = corridor.get("crude_grade", "medium_sour")

    lead_days = transit_days + (mobilization_days if cold_start else 0.0)
    eta = now + timedelta(days=lead_days)

    transport_cost = transport_cost_per_barrel(distance_km)
    crude_price = crude_price_per_barrel(corridor["cost_per_barrel"], distance_km)

    if refinery:
        refining_cost = refining_cost_per_barrel(
            refinery["base_refining_cost_per_barrel"], crude_grade, refinery.get("preferred_crude_grades", [])
        )
        refinery_name = refinery["name"]
    else:
        refining_cost = refining_cost_per_barrel(DEFAULT_REFINING_COST, crude_grade, [])
        refinery_name = None

    landed_cost = landed_cost_total(crude_price, transport_cost, refining_cost)
    spare_capacity = max(0.0, corridor["capacity_bpd"] - corridor["current_throughput_bpd"])

    return {
        "corridor_id": corridor["id"],
        "name": corridor["name"],
        "oil_type": corridor["oil_type"],
        "crude_grade": crude_grade,
        "distance_km": distance_km,
        "transit_days": transit_days,
        "mobilization_days": mobilization_days,
        "days_to_supply": round(lead_days, 1),
        "eta": eta.isoformat(),
        "crude_price_per_barrel": crude_price,
        "transport_cost_per_barrel": transport_cost,
        "refining_cost_per_barrel": refining_cost,
        "landed_cost_per_barrel": landed_cost,
        "capacity_bpd": corridor["capacity_bpd"],
        "current_throughput_bpd": corridor["current_throughput_bpd"],
        "spare_capacity_bpd": spare_capacity,
        "risk_score": corridor.get("risk_score", 0.0),
        "status": corridor.get("status", "active"),
        "choke_points": corridor.get("choke_points", []),
        "destination_refinery_id": corridor.get("destination_refinery_id"),
        "destination_refinery_name": refinery_name,
    }


async def _get_refinery(refinery_id: Optional[str]) -> Optional[dict]:
    if not refinery_id:
        return None
    return await db.refineries.find_one({"id": refinery_id}, {"_id": 0})


async def _resolve_blocked(corridor_ids: list[str], choke_points: list[str]) -> tuple[list[dict], set[str]]:
    """
    Resolves a block request into the actual corridor docs affected, plus the
    set of choke points to exclude candidates on.

    Two distinct use cases, both supported:
      - Surgical close: pass corridor_ids=["hormuz_jamnagar"]. Only that
        corridor is blocked; hormuz_kochi (same strait, different corridor)
        stays eligible as an alternate.
      - Strategic close: pass choke_points=["hormuz"]. Every corridor
        through the Strait of Hormuz is blocked AND excluded from the
        alternates pool, since the whole passage is down.

    Only explicitly-passed choke_points feed the exclusion set -- we
    deliberately don't infer it from each blocked corridor's own choke
    points, or closing one named corridor would silently disqualify every
    sibling route through the same strait.
    """
    ids = set(corridor_ids)
    if choke_points:
        via_choke_point = await db.corridors.find({"choke_points": {"$in": choke_points}}, {"_id": 0}).to_list(None)
        ids.update(c["id"] for c in via_choke_point)

    if not ids:
        return [], set()

    blocked_docs = await db.corridors.find({"id": {"$in": list(ids)}}, {"_id": 0}).to_list(None)
    return blocked_docs, set(choke_points)


async def _aggregate_reserve_pool() -> ReservePool:
    depots = await db.reserve_depots.find({}, {"_id": 0}).to_list(None)
    return ReservePool(
        total_capacity_barrels=sum(d["capacity_barrels"] for d in depots),
        current_stock_barrels=sum(d["current_stock_barrels"] for d in depots),
        max_drawdown_rate_bpd=sum(d["max_drawdown_rate_bpd"] for d in depots),
    )


def _route_summary_for_advisory(detail: dict) -> dict:
    return {
        "corridor_id": detail["corridor_id"],
        "name": detail["name"],
        "crude_grade": detail["crude_grade"],
        "distance_km": detail["distance_km"],
        "landed_cost": detail["landed_cost_per_barrel"],
        "days_to_supply": detail["days_to_supply"],
        "risk_score": detail["risk_score"],
    }


# ---------------------------------------------------------------------------
# Demo seeding
# ---------------------------------------------------------------------------

@router.post("/demo/seed")
async def seed_procurement_demo_data():
    """Run AFTER /demo/seed (corridors must already exist to be patched)."""
    await db.refineries.delete_many({})
    await db.reserve_depots.delete_many({})
    await db.refineries.insert_many([r.model_dump() for r in SEED_REFINERIES])
    await db.reserve_depots.insert_many([d.model_dump() for d in SEED_RESERVE_DEPOTS])

    patched = 0
    for corridor_id, patch in CORRIDOR_PATCHES.items():
        result = await db.corridors.update_one({"id": corridor_id}, {"$set": patch})
        if result.matched_count:
            patched += 1

    return {
        "status": "seeded",
        "refineries": len(SEED_REFINERIES),
        "reserve_depots": len(SEED_RESERVE_DEPOTS),
        "corridors_patched": patched,
    }


# ---------------------------------------------------------------------------
# Live/simulation map: single-route detail card
# ---------------------------------------------------------------------------

@router.get("/routes/{corridor_id}")
async def route_detail(corridor_id: str):
    now = current_time()
    corridor = await db.corridors.find_one({"id": corridor_id}, {"_id": 0})
    if not corridor:
        return {"error": f"Unknown corridor '{corridor_id}'."}
    refinery = await _get_refinery(corridor.get("destination_refinery_id"))
    cold_start = corridor.get("status") != "active"
    return _route_detail(corridor, refinery, now, cold_start=cold_start)


@router.get("/refineries")
async def list_refineries():
    """
    Read-only list of Indian refining hubs, for the map's refinery legend/markers.
    Purely additive -- doesn't touch any ranking/costing logic, just exposes
    the Refinery docs procurement_seed.py already loads into Mongo.
    """
    return await db.refineries.find({}, {"_id": 0}).to_list(None)


@router.get("/reserves")
async def get_reserves():
    """Current state of India's strategic reserve pool -- for a reserves panel/legend on either map."""
    depots = await db.reserve_depots.find({}, {"_id": 0}).to_list(None)
    pool = await _aggregate_reserve_pool()
    days_of_cover = (pool.current_stock_barrels / INDIA_DAILY_CONSUMPTION_BPD) if INDIA_DAILY_CONSUMPTION_BPD else 0.0
    return {
        "depots": depots,
        "total_capacity_barrels": pool.total_capacity_barrels,
        "total_current_stock_barrels": pool.current_stock_barrels,
        "national_daily_consumption_bpd": INDIA_DAILY_CONSUMPTION_BPD,
        "days_of_cover": round(days_of_cover, 2),
    }


# ---------------------------------------------------------------------------
# Adaptive Procurement Orchestrator
# ---------------------------------------------------------------------------

@router.post("/scenario/block")
async def block_and_recommend(req: BlockRequest):
    """
    Closes the given corridor(s)/choke point(s) and returns the top-N ranked
    alternate routes, each with a full cost/ETA/risk breakdown, plus an
    AI-generated advisory built around the #1 recommendation.
    """
    now = current_time()
    blocked_docs, blocked_choke_points = await _resolve_blocked(req.corridor_ids, req.choke_points)
    if not blocked_docs:
        return {"error": "No matching corridors found for the given corridor_ids/choke_points."}

    gap_bpd = sum(c["current_throughput_bpd"] for c in blocked_docs)
    blocked_ids = {c["id"] for c in blocked_docs}

    all_corridors = await db.corridors.find({}, {"_id": 0}).to_list(None)
    candidate_docs = [
        c for c in all_corridors
        if c["id"] not in blocked_ids
        and c.get("status") == "active"
        and not (set(c.get("choke_points", [])) & blocked_choke_points)
    ]

    blocked_summary = ", ".join(c["name"] for c in blocked_docs)

    if not candidate_docs:
        return {
            "gap_bpd": gap_bpd,
            "blocked_corridors": [{"id": c["id"], "name": c["name"]} for c in blocked_docs],
            "blocked_choke_points": list(blocked_choke_points),
            "alternates": [],
            "warning": "No viable alternate corridors in the current dataset -- every route shares a blocked choke point.",
        }

    refinery_cache: dict[str, Optional[dict]] = {}
    details = []
    for c in candidate_docs:
        rid = c.get("destination_refinery_id")
        if rid and rid not in refinery_cache:
            refinery_cache[rid] = await _get_refinery(rid)
        details.append(_route_detail(c, refinery_cache.get(rid), now, cold_start=True))

    candidates = [
        RouteCandidate(
            corridor_id=d["corridor_id"],
            risk_score=d["risk_score"],
            total_landed_cost=d["landed_cost_per_barrel"],
            spare_capacity_bpd=d["spare_capacity_bpd"],
            days_to_supply=d["days_to_supply"],
        )
        for d in details
    ]
    ranked = rank_alternate_routes(candidates, gap_bpd=gap_bpd, top_n=req.top_n)
    coverage_by_id = {row["corridor_id"]: row for row in cumulative_coverage(ranked, gap_bpd)}
    detail_by_id = {d["corridor_id"]: d for d in details}

    alternates = []
    for candidate, score in ranked:
        d = dict(detail_by_id[candidate.corridor_id])
        d["suitability_score"] = score
        d["coverage"] = coverage_by_id[candidate.corridor_id]
        alternates.append(d)

    # Advisory narrative built around the #1 recommendation, using a quick reserve-plan preview.
    top = alternates[0]
    pool = await _aggregate_reserve_pool()
    preview_plan = build_drawdown_plan(
        pool, gap_bpd=gap_bpd, day_online=top["days_to_supply"],
        ramp_spare_capacity_bpd=top["spare_capacity_bpd"],
        daily_national_consumption_bpd=INDIA_DAILY_CONSUMPTION_BPD,
        horizon_days=req.horizon_days,
    )
    reserve_summary = summarize_plan(preview_plan)
    reserve_summary["drawdown_bpd"] = preview_plan[0].drawdown_bpd if preview_plan else 0

    advisory = await generate_advisory(
        blocked_summary=blocked_summary,
        gap_bpd=gap_bpd,
        top_route=_route_summary_for_advisory(top),
        reserve_summary=reserve_summary,
    )

    return {
        "gap_bpd": gap_bpd,
        "blocked_corridors": [{"id": c["id"], "name": c["name"]} for c in blocked_docs],
        "blocked_choke_points": list(blocked_choke_points),
        "alternates": alternates,
        "advisory": advisory,
    }


# ---------------------------------------------------------------------------
# Strategic Reserve Optimisation Agent
# ---------------------------------------------------------------------------

@router.post("/scenario/reserve-plan")
async def reserve_plan_for_alternate(req: ReservePlanRequest):
    """
    Full day-by-day reserve drawdown schedule for ONE chosen alternate route
    (one of the top-5 cards from /scenario/block). Opens when the user clicks
    a specific recommendation.
    """
    now = current_time()
    blocked_docs, _ = await _resolve_blocked(req.corridor_ids, req.choke_points)
    if not blocked_docs:
        return {"error": "No matching blocked corridors found."}
    gap_bpd = sum(c["current_throughput_bpd"] for c in blocked_docs)
    blocked_summary = ", ".join(c["name"] for c in blocked_docs)

    alt = await db.corridors.find_one({"id": req.alternate_corridor_id}, {"_id": 0})
    if not alt:
        return {"error": f"Unknown alternate corridor '{req.alternate_corridor_id}'."}

    refinery = await _get_refinery(alt.get("destination_refinery_id"))
    detail = _route_detail(alt, refinery, now, cold_start=True)

    pool = await _aggregate_reserve_pool()
    plan = build_drawdown_plan(
        pool, gap_bpd=gap_bpd, day_online=detail["days_to_supply"],
        ramp_spare_capacity_bpd=detail["spare_capacity_bpd"],
        daily_national_consumption_bpd=INDIA_DAILY_CONSUMPTION_BPD,
        horizon_days=req.horizon_days,
    )
    summary = summarize_plan(plan)
    summary["drawdown_bpd"] = plan[0].drawdown_bpd if plan else 0

    advisory = await generate_advisory(
        blocked_summary=blocked_summary,
        gap_bpd=gap_bpd,
        top_route=_route_summary_for_advisory(detail),
        reserve_summary=summary,
    )

    return {
        "gap_bpd": gap_bpd,
        "alternate_route": detail,
        "reserve_pool": {
            "total_capacity_barrels": pool.total_capacity_barrels,
            "current_stock_barrels": pool.current_stock_barrels,
            "max_drawdown_rate_bpd": pool.max_drawdown_rate_bpd,
            "national_daily_consumption_bpd": INDIA_DAILY_CONSUMPTION_BPD,
        },
        "daily_plan": [asdict(p) for p in plan],
        "summary": summary,
        "advisory": advisory,
    }
