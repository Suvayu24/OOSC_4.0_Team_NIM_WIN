from datetime import datetime, timedelta, timezone
from typing import Optional

from models import Corridor, GeoPoint, SignalIn

CHOKE_POINT_CORRIDORS: dict[str, list[str]] = {
    "hormuz": ["hormuz_jamnagar", "hormuz_kochi", "basra_jamnagar", "fujairah_mangalore"],
    "bab_el_mandeb": ["red_sea_kochi", "yanbu_jamnagar", "suez_mumbai"],
    "suez": ["suez_mumbai"],
    "malacca": ["malacca_chennai", "singapore_paradip", "malaysia_chennai"],
}


def corridors_for_choke_point(choke_point: str) -> list[str]:
    return CHOKE_POINT_CORRIDORS.get(choke_point, [])


SEED_CORRIDORS: list[Corridor] = [
    Corridor(
        id="hormuz_jamnagar",
        name="Strait of Hormuz -> Jamnagar",
        origin=GeoPoint(lat=26.5, lng=56.25),
        destination=GeoPoint(lat=22.47, lng=69.87),
        waypoints=[[56.25, 26.5], [60.0, 22.0], [65.0, 20.0], [69.87, 22.47]],
        oil_type="crude",
        distance_km=3200,
        transit_days=8,
        cost_per_barrel=68.5,
        capacity_bpd=1_200_000,
        current_throughput_bpd=980_000,
        choke_points=["hormuz"],
    ),
    Corridor(
        id="hormuz_kochi",
        name="Strait of Hormuz -> Kochi",
        origin=GeoPoint(lat=26.5, lng=56.25),
        destination=GeoPoint(lat=9.93, lng=76.26),
        waypoints=[[56.25, 26.5], [62.0, 18.0], [70.0, 12.0], [76.26, 9.93]],
        oil_type="crude",
        distance_km=3600,
        transit_days=9,
        cost_per_barrel=69.0,
        capacity_bpd=500_000,
        current_throughput_bpd=310_000,
        choke_points=["hormuz"],
    ),
    Corridor(
        id="red_sea_kochi",
        name="Bab-el-Mandeb -> Kochi",
        origin=GeoPoint(lat=12.6, lng=43.4),
        destination=GeoPoint(lat=9.93, lng=76.26),
        waypoints=[[43.4, 12.6], [55.0, 10.0], [70.0, 8.0], [76.26, 9.93]],
        oil_type="crude",
        distance_km=4600,
        transit_days=11,
        cost_per_barrel=71.0,
        capacity_bpd=600_000,
        current_throughput_bpd=410_000,
        choke_points=["bab_el_mandeb"],
    ),
    Corridor(
        id="malacca_chennai",
        name="Strait of Malacca -> Chennai",
        origin=GeoPoint(lat=1.43, lng=102.75),
        destination=GeoPoint(lat=13.08, lng=80.27),
        waypoints=[[102.75, 1.43], [95.0, 5.0], [85.0, 8.0], [80.27, 13.08]],
        oil_type="crude",
        distance_km=3400,
        transit_days=8,
        cost_per_barrel=70.0,
        capacity_bpd=350_000,
        current_throughput_bpd=210_000,
        choke_points=["malacca"],
    ),
    Corridor(
        id="basra_jamnagar",
        name="Basra Gulf -> Jamnagar",
        origin=GeoPoint(lat=29.95, lng=48.2),
        destination=GeoPoint(lat=22.47, lng=69.87),
        waypoints=[[48.2, 29.95], [56.25, 26.5], [61.5, 22.5], [69.87, 22.47]],
        oil_type="crude",
        distance_km=2950,
        transit_days=7,
        cost_per_barrel=67.8,
        capacity_bpd=650_000,
        current_throughput_bpd=520_000,
        choke_points=["hormuz"],
    ),
    Corridor(
        id="fujairah_mangalore",
        name="Fujairah -> Mangalore",
        origin=GeoPoint(lat=25.12, lng=56.34),
        destination=GeoPoint(lat=12.87, lng=74.84),
        waypoints=[[56.34, 25.12], [60.5, 20.0], [67.0, 14.0], [74.84, 12.87]],
        oil_type="crude",
        distance_km=2850,
        transit_days=7,
        cost_per_barrel=68.2,
        capacity_bpd=420_000,
        current_throughput_bpd=260_000,
        choke_points=["hormuz"],
    ),
    Corridor(
        id="yanbu_jamnagar",
        name="Yanbu / Red Sea -> Jamnagar",
        origin=GeoPoint(lat=24.08, lng=38.06),
        destination=GeoPoint(lat=22.47, lng=69.87),
        waypoints=[[38.06, 24.08], [43.4, 12.6], [55.0, 12.0], [64.0, 18.0], [69.87, 22.47]],
        oil_type="crude",
        distance_km=4300,
        transit_days=10,
        cost_per_barrel=70.6,
        capacity_bpd=520_000,
        current_throughput_bpd=360_000,
        choke_points=["bab_el_mandeb"],
    ),
    Corridor(
        id="suez_mumbai",
        name="Suez Canal -> Mumbai",
        origin=GeoPoint(lat=31.24, lng=32.32),
        destination=GeoPoint(lat=18.95, lng=72.84),
        waypoints=[[32.32, 31.24], [43.4, 12.6], [55.0, 13.0], [65.0, 17.0], [72.84, 18.95]],
        oil_type="crude",
        distance_km=6200,
        transit_days=14,
        cost_per_barrel=72.4,
        capacity_bpd=380_000,
        current_throughput_bpd=230_000,
        choke_points=["suez", "bab_el_mandeb"],
    ),
    Corridor(
        id="singapore_paradip",
        name="Singapore -> Paradip",
        origin=GeoPoint(lat=1.29, lng=103.85),
        destination=GeoPoint(lat=20.31, lng=86.61),
        waypoints=[[103.85, 1.29], [99.0, 5.5], [94.0, 10.0], [86.61, 20.31]],
        oil_type="crude",
        distance_km=3300,
        transit_days=8,
        cost_per_barrel=69.7,
        capacity_bpd=300_000,
        current_throughput_bpd=190_000,
        choke_points=["malacca"],
    ),
    Corridor(
        id="malaysia_chennai",
        name="Malaysia Tapis -> Chennai",
        origin=GeoPoint(lat=4.35, lng=103.45),
        destination=GeoPoint(lat=13.08, lng=80.27),
        waypoints=[[103.45, 4.35], [99.5, 5.8], [90.0, 8.0], [80.27, 13.08]],
        oil_type="crude",
        distance_km=3100,
        transit_days=7,
        cost_per_barrel=69.4,
        capacity_bpd=240_000,
        current_throughput_bpd=150_000,
        choke_points=["malacca"],
    ),
    Corridor(
        id="brazil_jamnagar",
        name="Brazil Atlantic -> Jamnagar",
        origin=GeoPoint(lat=-22.9, lng=-43.2),
        destination=GeoPoint(lat=22.47, lng=69.87),
        waypoints=[[-43.2, -22.9], [-20.0, -30.0], [18.5, -34.4], [55.0, -20.0], [69.87, 22.47]],
        oil_type="crude",
        distance_km=14800,
        transit_days=29,
        cost_per_barrel=77.5,
        capacity_bpd=280_000,
        current_throughput_bpd=120_000,
        choke_points=[],
    ),
    Corridor(
        id="west_africa_paradip",
        name="West Africa -> Paradip",
        origin=GeoPoint(lat=4.0, lng=6.0),
        destination=GeoPoint(lat=20.31, lng=86.61),
        waypoints=[[6.0, 4.0], [30.0, -10.0], [60.0, -5.0], [86.61, 20.31]],
        oil_type="crude",
        distance_km=11800,
        transit_days=21,
        cost_per_barrel=74.0,
        capacity_bpd=400_000,
        current_throughput_bpd=250_000,
        choke_points=[],
    ),
]


def demo_signal_timeline(now: Optional[datetime] = None) -> list[SignalIn]:
    """
    A curated, escalating signal timeline for the route-risk demo.
    Timestamps are relative to `now`, so re-seeding right before your
    pitch always produces a fresh-looking escalation across several
    choke points. These are already structured SignalIn objects; the live
    /signals/classify path uses Gemini to derive the same fields from raw text.
    """
    now = now or datetime.now(timezone.utc)
    return [
        SignalIn(
            choke_point="hormuz", source_type="news_alert",
            action_intensity=1, target_specificity=1.0, actor_capability=1.0,
            raw_text="Iranian general threatens to close the Strait of Hormuz",
            observed_at=now - timedelta(days=5),
        ),
        SignalIn(
            choke_point="hormuz", source_type="ais_anomaly",
            action_intensity=4, target_specificity=1.0, actor_capability=0.9,
            raw_text="Multiple VLCCs report GPS spoofing near the Strait of Hormuz",
            observed_at=now - timedelta(days=1),
        ),
        SignalIn(
            choke_point="hormuz", source_type="news_alert",
            action_intensity=5, target_specificity=1.0, actor_capability=0.9,
            raw_text="Houthi-aligned forces strike a crude oil tanker with a drone near Hormuz",
            observed_at=now - timedelta(hours=2),
        ),
        SignalIn(
            choke_point="bab_el_mandeb", source_type="news_alert",
            action_intensity=4, target_specificity=1.0, actor_capability=0.8,
            raw_text="Security bulletin reports attempted boarding of a crude tanker near Bab-el-Mandeb",
            observed_at=now - timedelta(days=3, hours=6),
        ),
        SignalIn(
            choke_point="bab_el_mandeb", source_type="insurance_rate_hike",
            action_intensity=3, target_specificity=0.8, actor_capability=0.8,
            raw_text="War-risk underwriters raise Red Sea tanker premiums after repeated drone alerts",
            observed_at=now - timedelta(days=2),
        ),
        SignalIn(
            choke_point="bab_el_mandeb", source_type="ais_anomaly",
            action_intensity=4, target_specificity=0.9, actor_capability=0.8,
            raw_text="AIS tracks show crude carriers slowing and bunching at the Bab-el-Mandeb entrance",
            observed_at=now - timedelta(hours=9),
        ),
        SignalIn(
            choke_point="suez", source_type="news_alert",
            action_intensity=3, target_specificity=0.7, actor_capability=0.8,
            raw_text="Suez Canal authority reports convoy delays after a disabled product tanker blocks one lane",
            observed_at=now - timedelta(days=1, hours=12),
        ),
        SignalIn(
            choke_point="suez", source_type="government_advisory",
            action_intensity=2, target_specificity=0.6, actor_capability=0.9,
            raw_text="Shipping advisory warns energy carriers to plan extra time for northbound Suez transits",
            observed_at=now - timedelta(hours=18),
        ),
        SignalIn(
            choke_point="malacca", source_type="news_alert",
            action_intensity=2, target_specificity=0.6, actor_capability=0.6,
            raw_text="Singapore maritime alert flags congestion and inspection delays for tankers entering Malacca",
            observed_at=now - timedelta(days=4),
        ),
        SignalIn(
            choke_point="malacca", source_type="ais_anomaly",
            action_intensity=3, target_specificity=0.7, actor_capability=0.7,
            raw_text="AIS anomaly cluster shows multiple crude tankers making unusual speed changes in Malacca",
            observed_at=now - timedelta(days=1),
        ),
        SignalIn(
            choke_point="malacca", source_type="sanctions_announcement",
            action_intensity=2, target_specificity=0.6, actor_capability=0.8,
            raw_text="Regional authorities announce targeted inspections of sanctioned tankers near Malacca approaches",
            observed_at=now - timedelta(hours=5),
        ),
    ]


def demo_news_event_feed(now: Optional[datetime] = None) -> list[dict]:
    """
    Raw demo headlines for the Gemini classifier path. Unlike
    demo_signal_timeline(), these do not pre-bake the choke point or severity;
    /demo/classify-news asks Gemini to classify each item into SignalIn fields.
    """
    now = now or datetime.now(timezone.utc)
    return [
        {
            "source_type": "news_alert",
            "raw_text": "Iranian naval commander says Hormuz tanker traffic could be halted if sanctions escalate",
            "observed_at": now - timedelta(days=5),
        },
        {
            "source_type": "ais_anomaly",
            "raw_text": "Crude tankers report GPS spoofing and erratic AIS tracks near the Strait of Hormuz",
            "observed_at": now - timedelta(days=1),
        },
        {
            "source_type": "news_alert",
            "raw_text": "Drone strike damages a crude carrier transiting near the Strait of Hormuz",
            "observed_at": now - timedelta(hours=2),
        },
        {
            "source_type": "news_alert",
            "raw_text": "Armed boarding attempt reported against oil tanker near Bab-el-Mandeb",
            "observed_at": now - timedelta(days=3, hours=6),
        },
        {
            "source_type": "insurance_rate_hike",
            "raw_text": "War-risk premiums rise for crude tankers using Red Sea and Bab-el-Mandeb lanes",
            "observed_at": now - timedelta(days=2),
        },
        {
            "source_type": "ais_anomaly",
            "raw_text": "AIS data shows several crude carriers slowing sharply at the Bab-el-Mandeb entrance",
            "observed_at": now - timedelta(hours=9),
        },
        {
            "source_type": "news_alert",
            "raw_text": "Disabled product tanker causes convoy delays in the Suez Canal",
            "observed_at": now - timedelta(days=1, hours=12),
        },
        {
            "source_type": "government_advisory",
            "raw_text": "Maritime advisory tells energy carriers to add buffer time for northbound Suez Canal transits",
            "observed_at": now - timedelta(hours=18),
        },
        {
            "source_type": "news_alert",
            "raw_text": "Singapore port notice flags tanker congestion at the Strait of Malacca approaches",
            "observed_at": now - timedelta(days=4),
        },
        {
            "source_type": "ais_anomaly",
            "raw_text": "Multiple crude tankers make unusual speed changes in the Malacca Strait traffic lane",
            "observed_at": now - timedelta(days=1),
        },
        {
            "source_type": "sanctions_announcement",
            "raw_text": "Regional authorities announce targeted inspections of sanctioned tankers near Malacca",
            "observed_at": now - timedelta(hours=5),
        },
    ]
