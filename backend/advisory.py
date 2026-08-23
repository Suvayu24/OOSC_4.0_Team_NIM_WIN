"""
Turns the computed procurement + reserve numbers into short, human-readable
actionable recommendations, using Gemini. Falls back to a deterministic
templated recommendation if GEMINI_API_KEY isn't set or the call fails for
any reason -- a live demo should never go blank because of a network hiccup
or a rate limit, so this function is designed to never raise.

Mirrors the lazy-singleton pattern in classifier.py.
"""
import json
from typing import Optional

from google import genai

from config import settings

_MODEL = "gemini-2.5-flash"
_client: Optional[genai.Client] = None


def _get_client() -> Optional[genai.Client]:
    global _client
    if not settings.gemini_api_key:
        return None
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


ADVISORY_PROMPT = """You are an energy-security procurement advisor for an Indian oil company war room.
A supply corridor has been disrupted. Based on the structured data below, write SHORT, concrete, actionable
recommendations -- the kind a procurement desk could act on within hours. No fluff, no hedging disclaimers.

Disruption: {blocked_summary}
Volume lost: {gap_bpd:,.0f} bpd
Top ranked alternate route: {top_route_name} (crude grade {crude_grade}, {distance_km:.0f} km, landed cost ${landed_cost:.2f}/bbl, {days_to_supply:.1f} days to first delivery, risk score {risk_score:.0f}/100)
Reserve plan: drawing down at up to {drawdown_bpd:,.0f} bpd, reserve cover falls to a minimum of {min_days_cover:.1f} days before the alternate route ramps up, strategic floor breached: {floor_breached}

Respond with ONLY valid JSON, no markdown fences, in this exact shape:
{{"headline": "one sentence summary", "procurement_actions": ["action 1", "action 2", "action 3"], "reserve_actions": ["action 1", "action 2"]}}
Keep each action under 20 words. 3-4 procurement_actions, 2-3 reserve_actions.
"""


def _fallback_advisory(top_route_name: str, gap_bpd: float, min_days_cover: float, floor_breached: bool) -> dict:
    """Deterministic template used when Gemini is unavailable -- keeps the feature functional offline/keyless."""
    return {
        "headline": f"Redirect volume to {top_route_name} and begin a measured reserve drawdown to bridge the gap.",
        "procurement_actions": [
            f"Issue emergency tender to cover {gap_bpd:,.0f} bpd via {top_route_name}.",
            "Lock in freight charters now -- rates rise fast once other buyers react to the same disruption.",
            "Notify the destination refinery to adjust its crude slate for the incoming grade.",
        ],
        "reserve_actions": [
            f"Begin phased reserve drawdown; cover will dip to about {min_days_cover:.1f} days before new supply lands.",
            (
                "Reserve floor is at risk -- escalate for emergency spot-market purchases in parallel."
                if floor_breached else
                "Cap drawdown at the depot's physical pumping limit to keep the strategic floor intact."
            ),
        ],
        "source": "fallback_template",
    }


async def generate_advisory(
    blocked_summary: str,
    gap_bpd: float,
    top_route: dict,
    reserve_summary: dict,
) -> dict:
    """
    top_route: {"corridor_id", "name", "crude_grade", "distance_km", "landed_cost", "days_to_supply", "risk_score"}
    reserve_summary: output of reserve_engine.summarize_plan(), with a "drawdown_bpd" key added by the caller
                      (a representative day-0 drawdown rate, for the narrative).
    """
    min_days_cover = reserve_summary.get("minimum_days_of_cover_reached", 0.0)
    floor_breached = reserve_summary.get("floor_breached", False)
    route_name = top_route.get("name", "the top alternate route")

    client = _get_client()
    if client is None:
        return _fallback_advisory(route_name, gap_bpd, min_days_cover, floor_breached)

    prompt = ADVISORY_PROMPT.format(
        blocked_summary=blocked_summary,
        gap_bpd=gap_bpd,
        top_route_name=route_name,
        crude_grade=top_route.get("crude_grade", "unknown"),
        distance_km=top_route.get("distance_km", 0.0),
        landed_cost=top_route.get("landed_cost", 0.0),
        days_to_supply=top_route.get("days_to_supply", 0.0),
        risk_score=top_route.get("risk_score", 0.0),
        drawdown_bpd=reserve_summary.get("drawdown_bpd", 0.0),
        min_days_cover=min_days_cover,
        floor_breached=floor_breached,
    )

    try:
        response = await client.aio.models.generate_content(model=_MODEL, contents=prompt)
        cleaned = response.text.strip().strip("`").removeprefix("json").strip()
        parsed = json.loads(cleaned)
        if not all(k in parsed for k in ("headline", "procurement_actions", "reserve_actions")):
            raise ValueError("Gemini response missing expected keys")
        parsed["source"] = "gemini"
        return parsed
    except Exception:
        # Any parsing/network/API failure -- don't let an LLM hiccup break the demo.
        return _fallback_advisory(route_name, gap_bpd, min_days_cover, floor_breached)
