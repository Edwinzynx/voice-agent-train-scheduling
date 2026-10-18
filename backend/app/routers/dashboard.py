from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Call, CallLog, EvalRun
from ..config import config_manager
from .calls import active_connections
from ..auth import require_admin

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_admin)],
)

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated call analytics.
    """
    total_calls = db.query(Call).count()
    completed_calls = db.query(Call).filter(Call.status == "completed").count()
    successful_calls = db.query(Call).filter(Call.success == True).count()
    
    success_rate = (successful_calls / completed_calls * 100.0) if completed_calls > 0 else 0.0
    
    # Calculate average latencies
    latencies = db.query(
        func.avg(Call.p50_latency_ms),
        func.avg(Call.p90_latency_ms),
        func.avg(Call.duration_seconds)
    ).filter(Call.status == "completed").first()
    
    avg_p50 = latencies[0] or 0.0
    avg_p90 = latencies[1] or 0.0
    avg_duration = latencies[2] or 0.0
    
    # Active calls in memory
    active_count = len(active_connections)
    
    # Fetch recent eval scores
    latest_eval = db.query(EvalRun).order_by(EvalRun.run_time.desc()).first()
    eval_score = latest_eval.overall_success_rate if latest_eval else 0.0
    
    return {
        "total_calls": total_calls,
        "success_rate": round(success_rate, 2),
        "avg_p50_ms": round(avg_p50, 2),
        "avg_p90_ms": round(avg_p90, 2),
        "avg_duration_seconds": round(avg_duration, 2),
        "active_calls": active_count,
        "latest_eval_accuracy": round(eval_score, 2)
    }

@router.get("/calls")
def get_calls(
    page: int = 1, 
    limit: int = 10, 
    search: str = "", 
    success_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List past calls (paginated, with search criteria).
    """
    offset = (page - 1) * limit
    query = db.query(Call)
    
    if search:
        query = query.filter(
            (Call.caller_number.ilike(f"%{search}%")) |
            (Call.transcription.ilike(f"%{search}%")) |
            (Call.summary.ilike(f"%{search}%"))
        )
        
    if success_only:
        query = query.filter(Call.success == True)
        
    total = query.count()
    calls = query.order_by(Call.start_time.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "calls": calls
    }

@router.get("/calls/{call_id}")
def get_call_details(call_id: str, db: Session = Depends(get_db)):
    """
    Returns full metadata and turn-by-turn logs for a specific call.
    """
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found")
        
    logs = db.query(CallLog).filter(CallLog.call_id == call_id).order_by(CallLog.timestamp.asc()).all()
    
    return {
        "call": call,
        "logs": logs
    }

@router.get("/config")
def get_config():
    settings = config_manager.settings
    return {
        "environment": settings.environment,
        "has_sarvam": bool(settings.sarvam_api_key),
        "has_groq": bool(settings.groq_api_key),
        "llm_model": settings.llm_model,
        "speech_provider": "sarvam",
        "sarvam_stt_model": settings.sarvam_stt_model,
        "sarvam_tts_model": settings.sarvam_tts_model,
        "configuration_source": "server environment",
    }
