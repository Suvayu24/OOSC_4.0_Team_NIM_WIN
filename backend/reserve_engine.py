"""
Pure math for the Strategic Reserve Optimisation Agent. Given a supply gap
(bpd) caused by a blocked corridor, and the day an alternate route comes
fully online, this produces a day-by-day plan for how many barrels/day to
draw from India's Strategic Petroleum Reserve (SPR) to bridge the gap.

No DB or network calls here either -- procurement_router.py loads
ReserveDepot docs from Mongo, aggregates them into a ReservePool, and calls
into this module.
"""
from dataclasses import dataclass

# India holds ~9.5 days of consumption in strategic reserve. We never plan to
# draw the pool below this fraction of nameplate capacity -- it's the
# genuine "break glass" floor, kept as a safety margin below which the
# agent should be recommending emergency import contracts, not more drawdown.
STRATEGIC_MINIMUM_FRACTION = 0.15


@dataclass
class ReservePool:
    total_capacity_barrels: float
    current_stock_barrels: float
    max_drawdown_rate_bpd: float   # summed physical pumping/pipeline limit across all linked depots


@dataclass
class DayPlan:
    day: int
    gap_bpd: float                       # remaining shortfall that day, after ramp-up supply
    covered_by_ramp_bpd: float           # volume coming from the alternate route that day
    drawdown_bpd: float                  # volume drawn from strategic reserve that day
    reserve_stock_after_barrels: float
    reserve_days_of_cover_after: float   # stock / national daily consumption
    strategic_floor_breached: bool
    unmet_shortfall_bpd: float           # gap that NEITHER the ramp-up NOR the reserve could cover


def ramp_up_supply_bpd(day: int, day_online: float, spare_capacity_bpd: float) -> float:
    """
    Step-function ramp: 0 barrels before the alternate route is mobilized and
    in transit, full spare capacity from day_online onward. Swap this for a
    linear or S-curve ramp if a step change looks unrealistic in the demo.
    """
    return spare_capacity_bpd if day >= day_online else 0.0


def build_drawdown_plan(
    pool: ReservePool,
    gap_bpd: float,
    day_online: float,
    ramp_spare_capacity_bpd: float,
    daily_national_consumption_bpd: float,
    horizon_days: int = 15,
) -> list[DayPlan]:
    """
    Simulates day 0..horizon_days. Each day: figure out how much of the gap
    the alternate route already covers, draw reserve to cover the rest (up
    to the depot's physical pumping limit and down to the strategic floor),
    and report whatever's still unmet so the UI can flag a real shortfall.
    """
    plan: list[DayPlan] = []
    stock = pool.current_stock_barrels
    floor = pool.total_capacity_barrels * STRATEGIC_MINIMUM_FRACTION

    for day in range(0, horizon_days + 1):
        supply_from_ramp = ramp_up_supply_bpd(day, day_online, ramp_spare_capacity_bpd)
        remaining_gap = max(0.0, gap_bpd - supply_from_ramp)

        drawable_room = max(0.0, stock - floor)
        drawdown = min(pool.max_drawdown_rate_bpd, remaining_gap, drawable_room)

        stock -= drawdown
        unmet = max(0.0, remaining_gap - drawdown)
        days_of_cover = (stock / daily_national_consumption_bpd) if daily_national_consumption_bpd else 0.0

        plan.append(DayPlan(
            day=day,
            gap_bpd=round(remaining_gap, 0),
            covered_by_ramp_bpd=round(supply_from_ramp, 0),
            drawdown_bpd=round(drawdown, 0),
            reserve_stock_after_barrels=round(stock, 0),
            reserve_days_of_cover_after=round(days_of_cover, 2),
            strategic_floor_breached=stock <= floor + 1e-6,
            unmet_shortfall_bpd=round(unmet, 0),
        ))

    return plan


def summarize_plan(plan: list[DayPlan]) -> dict:
    """Headline numbers for a plan -- what goes on the recommendation card before drilling into the daily chart."""
    if not plan:
        return {}
    total_drawn = sum(p.drawdown_bpd for p in plan)   # 1 day granularity, so bpd-per-day sums ~ barrels
    return {
        "total_barrels_drawn": round(total_drawn, 0),
        "minimum_days_of_cover_reached": min(p.reserve_days_of_cover_after for p in plan),
        "days_with_uncovered_shortfall": sum(1 for p in plan if p.unmet_shortfall_bpd > 0),
        "floor_breached": any(p.strategic_floor_breached for p in plan),
        "fully_bridged": all(p.unmet_shortfall_bpd == 0 for p in plan),
    }
