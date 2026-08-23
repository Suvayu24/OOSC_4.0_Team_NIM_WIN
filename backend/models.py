from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Signal(BaseModel):
    id: str
    choke_point: str               # "hormuz", "bab_el_mandeb", "malacca", ...
    source_type: str               # key into SOURCE_WEIGHTS in risk_engine.py
    action_intensity: int          # A, 1-5
    target_specificity: float      # T, 0.0-1.0
    actor_capability: float        # C, 0.5-1.0
    raw_text: str
    observed_at: datetime          # t_i, used for time decay


class SignalIn(BaseModel):
    """What you POST to /signals before an id is assigned."""
    choke_point: str
    source_type: str
    action_intensity: int
    target_specificity: float
    actor_capability: float
    raw_text: str
    observed_at: Optional[datetime] = None


class GeoPoint(BaseModel):
    lat: float
    lng: float


class Corridor(BaseModel):
    id: str
    name: str
    origin: GeoPoint
    destination: GeoPoint
    waypoints: list[list[float]] = Field(default_factory=list)   # [[lng, lat], ...] for map rendering
    oil_type: Literal["crude", "refined"] = "crude"
    distance_km: float
    transit_days: float
    cost_per_barrel: float          # landed cost/bbl (commodity + freight), pre-refining
    capacity_bpd: float
    current_throughput_bpd: float
    choke_points: list[str] = Field(default_factory=list)
    risk_score: float = 0.0        # 0-100, written by the risk engine
    status: Literal["active", "disrupted", "rerouted"] = "active"

    # --- Added for Adaptive Procurement Orchestrator / Strategic Reserve Agent ---
    crude_grade: Literal["light_sweet", "medium_sour", "heavy_sour"] = "medium_sour"
    destination_refinery_id: Optional[str] = None   # links to Refinery.id below
    mobilization_days: float = 2.0                  # lead time to arrange a new charter/contract on a *cold* route


class Refinery(BaseModel):
    """An Indian refining hub -- the demand side that corridors deliver into."""
    id: str
    name: str
    location: GeoPoint
    state: str
    capacity_bpd: float
    current_processing_bpd: float
    base_refining_cost_per_barrel: float
    preferred_crude_grades: list[str] = Field(default_factory=lambda: ["medium_sour"])


class ReserveDepot(BaseModel):
    """One of India's Strategic Petroleum Reserve caverns (Vizag / Mangalore / Padur, etc.)."""
    id: str
    name: str
    location: GeoPoint
    capacity_barrels: float
    current_stock_barrels: float
    max_drawdown_rate_bpd: float     # physical pumping/pipeline limit, not a policy limit
    linked_refinery_ids: list[str] = Field(default_factory=list)
