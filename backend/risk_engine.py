"""
Pure math for the risk scoring model. No database or network calls in
this file on purpose -- it should be trivially unit-testable, which is
exactly what calibrate.py does.
"""
import math
from datetime import datetime

from models import Signal

SOURCE_WEIGHTS: dict[str, float] = {
    "ais_anomaly": 0.4,
    "news_alert": 0.3,
    "insurance_rate_hike": 0.3,
    "sanctions_announcement": 0.35,
    "government_advisory": 0.3,
}
DEFAULT_SOURCE_WEIGHT = 0.25


def compute_severity(action_intensity: int, target_specificity: float, actor_capability: float) -> int:
    """S_i = round(clamp(A * (0.6*T + 0.4*C), 1, 5))"""
    raw = action_intensity * (0.6 * target_specificity + 0.4 * actor_capability)
    return round(max(1, min(5, raw)))


def compute_risk_index(signals: list[Signal], now: datetime, decay_lambda: float) -> float:
    """R(c,t) = sum( w_i * S_i(c,t) * e^(-lambda * (t - t_i)) )  -- (t - t_i) in days"""
    total = 0.0
    for sig in signals:
        weight = SOURCE_WEIGHTS.get(sig.source_type, DEFAULT_SOURCE_WEIGHT)
        severity = compute_severity(sig.action_intensity, sig.target_specificity, sig.actor_capability)
        days_elapsed = max(0.0, (now - sig.observed_at).total_seconds() / 86400)
        decay = math.exp(-decay_lambda * days_elapsed)
        total += weight * severity * decay
    return total


def disruption_probability(risk_index: float, k: float, r0: float) -> float:
    """P(Disruption) = 1 / (1 + e^(-k * (R - R0)))"""
    return 1 / (1 + math.exp(-k * (risk_index - r0)))


def risk_score_percent(risk_index: float, k: float, r0: float) -> int:
    """Convenience wrapper: 0-100 score for display on the live map."""
    return round(disruption_probability(risk_index, k, r0) * 100)
