"""
Turns a raw news/AIS/sanctions text snippet into a structured Signal
using Gemini. This is the "live" ingestion path -- for your demo, the
curated timeline in seed_data.py is what you actually rely on.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from google import genai

from config import settings
from models import SignalIn

# TODO: double-check this is still the model name/tier you want before your
# demo -- verify against Google's current docs, model names shift over time.
_MODEL = "gemini-2.5-flash"

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """
    Lazy singleton -- avoids crashing app startup when GEMINI_API_KEY isn't
    set yet (e.g. while you're still building the risk engine and haven't
    wired up the classifier path).
    """
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

CLASSIFIER_PROMPT = """You are classifying a maritime security or geopolitical event that may affect global crude oil shipping corridors.

Rubric:
Action Intensity (integer 1-5):
1 = Rhetoric: diplomatic protests, verbal threats, policy speeches
2 = Economic/Legal: sanctions declarations, asset freezes, port bans
3 = Military Posturing: live-fire drills, carrier deployments, airspace violations
4 = Maritime Interdiction: boarding, vessel detentions, GPS spoofing
5 = Kinetic Strike/Blockade: missile strikes, sea mines, active blockades

Target Specificity (float 0.0-1.0):
0.2 = general political target or unrelated cargo
0.6 = commercial shipping lane in general
1.0 = direct targeting of crude tankers, pipelines, or export terminals

Actor Capability (float 0.5-1.0):
0.5 = unverified claims or low-capability non-state actor
1.0 = state military force with demonstrated capability

Identify the choke point this relates to: hormuz, bab_el_mandeb, suez, malacca, or none.

News item: "{text}"

Respond with ONLY valid JSON, no markdown fences, in this exact shape:
{{"choke_point": "...", "action_intensity": 0, "target_specificity": 0.0, "actor_capability": 0.0, "confidence": 0.0}}
"""

MIN_CONFIDENCE = 0.5


async def classify_signal(raw_text: str, source_type: str, observed_at: Optional[datetime] = None) -> Optional[SignalIn]:
    """
    Returns a SignalIn built from the model's classification, or None
    if confidence is too low to trust automatically -- route those to
    manual review instead of silently ingesting a bad score.
    """
    if not settings.gemini_api_key:
        return None

    prompt = CLASSIFIER_PROMPT.format(text=raw_text.replace('"', "'"))
    try:
        response = await _get_client().aio.models.generate_content(model=_MODEL, contents=prompt)
        cleaned = response.text.strip().strip("`").removeprefix("json").strip()
        parsed = json.loads(cleaned)

        if parsed.get("confidence", 0) < MIN_CONFIDENCE:
            return None

        return SignalIn(
            choke_point=parsed["choke_point"],
            source_type=source_type,
            action_intensity=int(parsed["action_intensity"]),
            target_specificity=float(parsed["target_specificity"]),
            actor_capability=float(parsed["actor_capability"]),
            raw_text=raw_text,
            observed_at=observed_at or datetime.now(timezone.utc),
        )
    except Exception:
        # Bad/missing API key, malformed JSON from the model, network hiccup, etc.
        # Route to manual review instead of 500ing the endpoint -- same philosophy as advisory.py.
        return None
