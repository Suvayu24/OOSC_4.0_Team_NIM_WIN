"""
Pure math for the Adaptive Procurement Orchestrator: cost breakdown for a
single route, and a ranking model for alternate routes when one or more
corridors go down. No DB or network calls on purpose -- mirrors
risk_engine.py so this stays trivially unit-testable.

Usage sketch (see procurement_router.py for the wired-up version):

    candidates = [RouteCandidate(...) for corridor in live_alternate_corridors]
    ranked = rank_alternate_routes(candidates, gap_bpd=lost_throughput)
    top5 = ranked[:5]
"""
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Tunable assumptions -- all illustrative, calibrate against real freight /
# refining benchmarks before you trust the numbers in front of judges.
# ---------------------------------------------------------------------------
FREIGHT_USD_PER_BBL_PER_KM = 0.0016   # blended VLCC/Suezmax freight-rate assumption
PORT_HANDLING_USD_PER_BBL = 1.20      # fixed port + handling charge, applied to every route
GRADE_MISMATCH_PENALTY = 0.12         # +12% refining cost if crude grade isn't in the refinery's preferred slate

# Ranking weights for suitability_score -- must sum to 1.0
W_RISK = 0.35        # lower risk_score is better
W_COST = 0.30        # lower total landed cost/bbl is better
W_CAPACITY = 0.20     # more of the gap covered is better
W_SPEED = 0.15        # fewer days until barrels actually arrive is better


# ---------------------------------------------------------------------------
# Cost breakdown for a single route
# ---------------------------------------------------------------------------

def transport_cost_per_barrel(distance_km: float) -> float:
    """Freight + handling component of landed cost, purely a function of distance."""
    return round(distance_km * FREIGHT_USD_PER_BBL_PER_KM + PORT_HANDLING_USD_PER_BBL, 2)


def crude_price_per_barrel(stored_cost_per_barrel: float, distance_km: float) -> float:
    """
    Corridor.cost_per_barrel in the DB is the all-in landed cost. Back out the
    commodity price by subtracting our transport-cost model from it, so the
    UI can show "crude price" and "freight" as separate line items.
    """
    return round(max(0.0, stored_cost_per_barrel - transport_cost_per_barrel(distance_km)), 2)


def refining_cost_per_barrel(base_refining_cost: float, crude_grade: str, preferred_grades: list[str]) -> float:
    """Refineries configured for a different slate pay a processing penalty for an off-spec crude grade."""
    penalty = 0.0 if crude_grade in preferred_grades else GRADE_MISMATCH_PENALTY
    return round(base_refining_cost * (1 + penalty), 2)


def landed_cost_total(crude_price: float, transport_cost: float, refining_cost: float) -> float:
    """The number procurement actually cares about: everything in, per barrel, at the refinery gate."""
    return round(crude_price + transport_cost + refining_cost, 2)


# ---------------------------------------------------------------------------
# Ranking alternate routes
# ---------------------------------------------------------------------------

@dataclass
class RouteCandidate:
    corridor_id: str
    risk_score: float           # 0-100, lower = safer (from risk_engine.py)
    total_landed_cost: float    # $/bbl, at the refinery gate
    spare_capacity_bpd: float   # capacity_bpd - current_throughput_bpd, floored at 0
    days_to_supply: float       # mobilization_days + transit_days -- time until barrels actually land


def _normalize(value: float, lo: float, hi: float, invert: bool = False) -> float:
    """Min-max normalize to 0..1 across the candidate pool. invert=True: lower raw value scores higher."""
    if hi == lo:
        return 1.0
    n = (value - lo) / (hi - lo)
    n = max(0.0, min(1.0, n))
    return 1 - n if invert else n


def suitability_score(candidate: RouteCandidate, pool: list[RouteCandidate], gap_bpd: float) -> float:
    """
    0-100 composite suitability score for `candidate` replacing lost volume,
    scored relative to the other routes in `pool` (so it's a genuine ranking,
    not an absolute grade). Higher is better.
    """
    risks = [c.risk_score for c in pool]
    costs = [c.total_landed_cost for c in pool]
    days = [c.days_to_supply for c in pool]

    risk_n = _normalize(candidate.risk_score, min(risks), max(risks), invert=True)
    cost_n = _normalize(candidate.total_landed_cost, min(costs), max(costs), invert=True)
    speed_n = _normalize(candidate.days_to_supply, min(days), max(days), invert=True)

    # Capacity: reward routes that can cover more of the gap, saturating once they cover 100% of it.
    coverage = (min(candidate.spare_capacity_bpd, gap_bpd) / gap_bpd) if gap_bpd > 0 else 1.0
    capacity_n = max(0.0, min(1.0, coverage))

    score = (W_RISK * risk_n + W_COST * cost_n + W_CAPACITY * capacity_n + W_SPEED * speed_n) * 100
    return round(score, 1)


def rank_alternate_routes(
    candidates: list[RouteCandidate], gap_bpd: float, top_n: int = 5
) -> list[tuple[RouteCandidate, float]]:
    """Returns [(candidate, score), ...] sorted best-first, truncated to top_n."""
    if not candidates:
        return []
    scored = [(c, suitability_score(c, candidates, gap_bpd)) for c in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_n]


def cumulative_coverage(ranked: list[tuple[RouteCandidate, float]], gap_bpd: float) -> list[dict]:
    """
    Walks the ranked list in order and tracks how much of the gap is filled
    if procurement activates routes one by one in ranked order. Useful for
    telling the team "you need the top 2 routes, not just #1, to fully cover this."
    """
    covered = 0.0
    rows = []
    for candidate, score in ranked:
        take = min(candidate.spare_capacity_bpd, max(0.0, gap_bpd - covered))
        covered += take
        rows.append({
            "corridor_id": candidate.corridor_id,
            "score": score,
            "bpd_contributed": round(take, 0),
            "cumulative_coverage_pct": round(min(100.0, (covered / gap_bpd) * 100) if gap_bpd > 0 else 100.0, 1),
        })
    return rows
