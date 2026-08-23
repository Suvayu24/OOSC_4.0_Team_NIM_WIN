"""
Standalone calibration harness. No server, no Mongo needed.
Run this locally to tune decay_lambda, logistic_k and logistic_r0
BEFORE putting the final numbers into .env / config.py.

Usage: python calibrate.py
"""
from datetime import datetime, timedelta, timezone

from models import Signal
from risk_engine import compute_risk_index, disruption_probability

DECAY_LAMBDA = 0.231   # ~3 day half-life: ln(2)/3
LOGISTIC_K = 1.5
LOGISTIC_R0 = 2.0


def make_signal(id_, source_type, A, T, C, text, days_ago=0.0, hours_ago=0.0):
    return Signal(
        id=id_, choke_point="hormuz", source_type=source_type,
        action_intensity=A, target_specificity=T, actor_capability=C,
        raw_text=text,
        observed_at=datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago),
    )


TIMELINE = [
    make_signal("1", "news_alert", 1, 1.0, 1.0, "Iranian general threatens to close Hormuz", days_ago=5),
    make_signal("2", "ais_anomaly", 4, 1.0, 0.9, "Multiple VLCCs report GPS spoofing near Hormuz", days_ago=1),
    make_signal("3", "news_alert", 5, 1.0, 0.9, "Houthi forces hit a crude oil tanker with a drone", hours_ago=2),
]

if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    print(f"{'signal added':<48} {'R':>6} {'P(disruption)':>15}")
    print("-" * 71)
    for i in range(1, len(TIMELINE) + 1):
        active = TIMELINE[:i]
        R = compute_risk_index(active, now, DECAY_LAMBDA)
        P = disruption_probability(R, LOGISTIC_K, LOGISTIC_R0)
        label = active[-1].raw_text[:46]
        print(f"{label:<48} {R:>6.2f} {P:>14.1%}")
