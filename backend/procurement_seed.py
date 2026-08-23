"""
Seed data for the Adaptive Procurement Orchestrator + Strategic Reserve
Optimisation Agent. Deliberately kept separate from seed_data.py (the risk
engine's corridor seed) so the two of you can work without merge conflicts.

Run order matters: call POST /demo/seed first (loads corridors), then
POST /procurement/demo/seed (loads refineries + reserve depots, and patches
the existing corridors with the extra fields this module needs).
"""
from models import Refinery, ReserveDepot, GeoPoint

SEED_REFINERIES: list[Refinery] = [
    Refinery(
        id="jamnagar", name="Jamnagar Refinery (Reliance)",
        location=GeoPoint(lat=22.47, lng=69.87), state="Gujarat",
        capacity_bpd=1_400_000, current_processing_bpd=1_150_000,
        base_refining_cost_per_barrel=4.20,
        preferred_crude_grades=["light_sweet", "medium_sour"],
    ),
    Refinery(
        id="kochi", name="Kochi Refinery (BPCL)",
        location=GeoPoint(lat=9.93, lng=76.26), state="Kerala",
        capacity_bpd=310_000, current_processing_bpd=270_000,
        base_refining_cost_per_barrel=4.60,
        preferred_crude_grades=["medium_sour", "heavy_sour"],
    ),
    Refinery(
        id="paradip", name="Paradip Refinery (IOCL)",
        location=GeoPoint(lat=20.31, lng=86.61), state="Odisha",
        capacity_bpd=300_000, current_processing_bpd=240_000,
        base_refining_cost_per_barrel=4.80,
        preferred_crude_grades=["light_sweet", "heavy_sour"],
    ),
    Refinery(
        id="mangalore", name="Mangalore Refinery (MRPL)",
        location=GeoPoint(lat=12.87, lng=74.84), state="Karnataka",
        capacity_bpd=300_000, current_processing_bpd=245_000,
        base_refining_cost_per_barrel=4.55,
        preferred_crude_grades=["medium_sour", "heavy_sour"],
    ),
    Refinery(
        id="mumbai", name="Mumbai Refinery Cluster",
        location=GeoPoint(lat=18.95, lng=72.84), state="Maharashtra",
        capacity_bpd=420_000, current_processing_bpd=350_000,
        base_refining_cost_per_barrel=4.35,
        preferred_crude_grades=["light_sweet", "medium_sour"],
    ),
    Refinery(
        id="chennai", name="Chennai Refinery (CPCL)",
        location=GeoPoint(lat=13.08, lng=80.27), state="Tamil Nadu",
        capacity_bpd=210_000, current_processing_bpd=175_000,
        base_refining_cost_per_barrel=4.70,
        preferred_crude_grades=["light_sweet", "medium_sour"],
    ),
]

# corridor_id -> fields to patch onto the Corridor docs seed_data.py already inserted.
# Applied with $set in procurement_router.seed_procurement_demo_data(), so it never
# needs to touch seed_data.py itself.
CORRIDOR_PATCHES: dict[str, dict] = {
    "hormuz_jamnagar":     {"crude_grade": "light_sweet",  "destination_refinery_id": "jamnagar", "mobilization_days": 1.0},
    "hormuz_kochi":        {"crude_grade": "medium_sour",  "destination_refinery_id": "kochi",    "mobilization_days": 1.5},
    "red_sea_kochi":       {"crude_grade": "medium_sour",  "destination_refinery_id": "kochi",    "mobilization_days": 2.0},
    "malacca_chennai":     {"crude_grade": "light_sweet",  "destination_refinery_id": "chennai",  "mobilization_days": 2.0},
    "basra_jamnagar":      {"crude_grade": "medium_sour",  "destination_refinery_id": "jamnagar", "mobilization_days": 1.0},
    "fujairah_mangalore":  {"crude_grade": "medium_sour",  "destination_refinery_id": "mangalore", "mobilization_days": 1.0},
    "yanbu_jamnagar":      {"crude_grade": "medium_sour",  "destination_refinery_id": "jamnagar", "mobilization_days": 1.5},
    "suez_mumbai":         {"crude_grade": "light_sweet",  "destination_refinery_id": "mumbai",   "mobilization_days": 2.0},
    "singapore_paradip":   {"crude_grade": "light_sweet",  "destination_refinery_id": "paradip",  "mobilization_days": 2.0},
    "malaysia_chennai":    {"crude_grade": "light_sweet",  "destination_refinery_id": "chennai",  "mobilization_days": 1.5},
    "brazil_jamnagar":     {"crude_grade": "heavy_sour",   "destination_refinery_id": "jamnagar", "mobilization_days": 4.0},
    "west_africa_paradip": {"crude_grade": "light_sweet",  "destination_refinery_id": "paradip",  "mobilization_days": 3.0},
}

# India's Strategic Petroleum Reserve: 3 underground caverns. Capacities below
# are illustrative, calibrated so total capacity / INDIA_DAILY_CONSUMPTION_BPD
# lands close to the real-world "~9.5 days of cover" figure -- recalibrate
# against official EIA/PPAC numbers before you cite these outside a demo.
SEED_RESERVE_DEPOTS: list[ReserveDepot] = [
    ReserveDepot(
        id="vizag_spr", name="Visakhapatnam SPR",
        location=GeoPoint(lat=17.68, lng=83.22),
        capacity_barrels=9_700_000, current_stock_barrels=9_700_000,
        max_drawdown_rate_bpd=400_000, linked_refinery_ids=["paradip"],
    ),
    ReserveDepot(
        id="mangalore_spr", name="Mangalore SPR",
        location=GeoPoint(lat=12.87, lng=74.84),
        capacity_barrels=15_600_000, current_stock_barrels=15_600_000,
        max_drawdown_rate_bpd=650_000, linked_refinery_ids=["kochi", "jamnagar", "mangalore", "mumbai"],
    ),
    ReserveDepot(
        id="padur_spr", name="Padur SPR",
        location=GeoPoint(lat=13.36, lng=74.71),
        capacity_barrels=23_200_000, current_stock_barrels=23_200_000,
        max_drawdown_rate_bpd=550_000, linked_refinery_ids=["kochi", "jamnagar", "mangalore", "mumbai", "chennai"],
    ),
]

# ~9.5 days of cover at this consumption rate, given the depot capacities above.
INDIA_DAILY_CONSUMPTION_BPD = 5_100_000
