from pydantic import BaseModel, Field


class BlockRequest(BaseModel):
    """POST body for closing one or more corridors/choke points on the Simulation map."""
    corridor_ids: list[str] = Field(default_factory=list)
    choke_points: list[str] = Field(default_factory=list)   # e.g. "hormuz" -- resolves to every corridor through it
    top_n: int = 5
    horizon_days: int = 15


class ReservePlanRequest(BaseModel):
    """POST body for drilling into the reserve drawdown plan behind one specific alternate route."""
    corridor_ids: list[str] = Field(default_factory=list)   # same blocked set used in the /scenario/block call
    choke_points: list[str] = Field(default_factory=list)
    alternate_corridor_id: str
    horizon_days: int = 15
