import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from classifier import classify_signal
from config import settings
from db import db
from models import Signal, SignalIn
from risk_engine import compute_risk_index, risk_score_percent
from seed_data import SEED_CORRIDORS, corridors_for_choke_point, demo_news_event_feed, demo_signal_timeline
from ws_manager import manager

router = APIRouter()

# In-memory demo clock override so you can fast-forward through the
# curated timeline on stage instead of waiting in real time.
# None means "use real wall-clock time".
_demo_now: Optional[datetime] = None


def current_time() -> datetime:
    return _demo_now or datetime.now(timezone.utc)


async def recompute_and_broadcast(corridor_id: str):
    corridor = await db.corridors.find_one({"id": corridor_id}, {"_id": 0})
    if not corridor:
        return

    choke_points = corridor.get("choke_points", [])
    signals_raw = await db.signals.find({"choke_point": {"$in": choke_points}}, {"_id": 0}).to_list(None)
    signals = [Signal(**s) for s in signals_raw]

    risk_index = compute_risk_index(signals, current_time(), settings.decay_lambda)
    score = risk_score_percent(risk_index, settings.logistic_k, settings.logistic_r0)

    await db.corridors.update_one({"id": corridor_id}, {"$set": {"risk_score": score}})
    await manager.broadcast({"type": "risk_update", "corridorId": corridor_id, "riskScore": score})


async def recompute_all():
    corridors = await db.corridors.find({}, {"_id": 0}).to_list(None)
    for c in corridors:
        await recompute_and_broadcast(c["id"])


@router.post("/signals")
async def ingest_structured_signal(signal_in: SignalIn):
    signal = Signal(
        id=str(uuid.uuid4()),
        observed_at=signal_in.observed_at or current_time(),
        **signal_in.model_dump(exclude={"observed_at"}),
    )
    await db.signals.insert_one(signal.model_dump())
    for corridor_id in corridors_for_choke_point(signal.choke_point):
        await recompute_and_broadcast(corridor_id)
    return signal


@router.post("/signals/classify")
async def ingest_raw_signal(raw_text: str, source_type: str):
    """Runs the Gemini classifier on raw text, then ingests the result if confident enough."""
    signal_in = await classify_signal(raw_text, source_type)
    if signal_in is None:
        return {"status": "low_confidence", "message": "Needs manual review"}
    return await ingest_structured_signal(signal_in)


@router.get("/corridors")
async def list_corridors():
    return await db.corridors.find({}, {"_id": 0}).to_list(None)


@router.get("/corridors/{corridor_id}")
async def get_corridor(corridor_id: str):
    return await db.corridors.find_one({"id": corridor_id}, {"_id": 0})


@router.post("/demo/seed")
async def seed_demo_data():
    """Wipes and reseeds corridors. Run this once before you start a demo."""
    global _demo_now
    await db.corridors.delete_many({})
    await db.signals.delete_many({})
    await db.corridors.insert_many([c.model_dump() for c in SEED_CORRIDORS])
    _demo_now = None
    return {"status": "seeded", "corridors": len(SEED_CORRIDORS)}


@router.post("/demo/load-timeline")
async def load_demo_timeline():
    """Inserts the curated escalation timeline from seed_data.py."""
    now = current_time()
    inserted = []
    affected_choke_points = set()
    for s in demo_signal_timeline(now):
        signal = Signal(id=str(uuid.uuid4()), **s.model_dump())
        await db.signals.insert_one(signal.model_dump())
        inserted.append(signal.id)
        affected_choke_points.add(signal.choke_point)
    for choke_point in affected_choke_points:
        for corridor_id in corridors_for_choke_point(choke_point):
            await recompute_and_broadcast(corridor_id)
    return {"inserted": len(inserted), "choke_points": sorted(affected_choke_points)}


@router.post("/demo/classify-news")
async def classify_demo_news():
    """
    Runs the seeded raw news feed through Gemini, inserts confident
    classifications as Signals, and recomputes the affected corridors.
    Requires GEMINI_API_KEY; low-confidence or failed classifications are
    returned for review instead of being inserted.
    """
    now = current_time()
    inserted = []
    skipped = []
    affected_choke_points = set()

    for event in demo_news_event_feed(now):
        signal_in = await classify_signal(
            raw_text=event["raw_text"],
            source_type=event["source_type"],
            observed_at=event["observed_at"],
        )
        if signal_in is None or signal_in.choke_point == "none":
            skipped.append({"raw_text": event["raw_text"], "source_type": event["source_type"]})
            continue

        signal = Signal(id=str(uuid.uuid4()), **signal_in.model_dump())
        await db.signals.insert_one(signal.model_dump())
        inserted.append(signal.id)
        affected_choke_points.add(signal.choke_point)

    for choke_point in affected_choke_points:
        for corridor_id in corridors_for_choke_point(choke_point):
            await recompute_and_broadcast(corridor_id)

    return {
        "inserted": len(inserted),
        "skipped": len(skipped),
        "choke_points": sorted(affected_choke_points),
        "review": skipped,
        "gemini_enabled": bool(settings.gemini_api_key),
    }


@router.post("/demo/advance")
async def advance_demo_clock(step_hours: float = 6.0):
    """Moves the demo clock forward and recomputes every corridor -- call this on stage."""
    global _demo_now
    base = _demo_now or datetime.now(timezone.utc)
    _demo_now = base + timedelta(hours=step_hours)
    await recompute_all()
    return {"demo_time": _demo_now.isoformat()}


@router.websocket("/ws/risk-updates")
async def risk_updates_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive; client doesn't need to send anything
    except WebSocketDisconnect:
        manager.disconnect(websocket)
