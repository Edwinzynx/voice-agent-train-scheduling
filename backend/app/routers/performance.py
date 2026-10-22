"""Public aggregate performance, without individual call data."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Call

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/summary")
def performance_summary(response: Response, db: Session = Depends(get_db)):
    completed = db.query(Call).filter(Call.status == "completed")
    count, duration = completed.with_entities(func.count(Call.id), func.avg(Call.duration_seconds)).one()
    measured, p50, p90 = completed.filter(Call.p50_latency_ms > 0).with_entities(
        func.count(Call.id), func.avg(Call.p50_latency_ms), func.avg(Call.p90_latency_ms)
    ).one()
    response.headers["Cache-Control"] = "public, max-age=60"
    return {
        "completed_sessions": count,
        "measured_sessions": measured,
        "avg_session_p50_ms": round(p50, 4) if p50 is not None else None,
        "avg_session_p90_ms": round(p90, 4) if p90 is not None else None,
        "avg_session_duration_seconds": round(duration, 2) if duration is not None else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
