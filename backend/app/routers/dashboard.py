from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from pydantic import BaseModel
from ..database import get_db
from ..models import Call, CallLog, EvalRun
from ..config import config_manager
from .calls import active_connections

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

class ConfigSchema(BaseModel):
    groq_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    sms_provider: str = "mock"
    use_mock_llm: bool = False
    use_mock_stt: bool = False
    use_mock_tts: bool = False

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
    """
    Returns current configuration settings. Sensitive keys are partially masked.
    """
    settings = config_manager.settings
    
    def mask(s: str) -> str:
        if not s:
            return ""
        return s[:4] + "*" * (len(s) - 8) + s[-4:] if len(s) > 8 else "****"

    return {
        "groq_api_key_masked": mask(settings.groq_api_key),
        "deepgram_api_key_masked": mask(settings.deepgram_api_key),
        "elevenlabs_api_key_masked": mask(settings.elevenlabs_api_key),
        "twilio_account_sid": settings.twilio_account_sid,
        "twilio_auth_token_masked": mask(settings.twilio_auth_token),
        "twilio_phone_number": settings.twilio_phone_number,
        "sms_provider": settings.sms_provider,
        "use_mock_llm": settings.use_mock_llm,
        "use_mock_stt": settings.use_mock_stt,
        "use_mock_tts": settings.use_mock_tts,
        "has_groq": bool(settings.groq_api_key),
        "has_deepgram": bool(settings.deepgram_api_key),
        "has_elevenlabs": bool(settings.elevenlabs_api_key)
    }

@router.post("/config")
def update_config(payload: ConfigSchema):
    """
    Updates configuration variables and saves to disk config.json.
    """
    update_data = payload.model_dump()
    
    # Do not overwrite if string is masked
    settings = config_manager.settings
    if payload.groq_api_key.endswith("****") or not payload.groq_api_key:
        update_data.pop("groq_api_key", None)
    if payload.deepgram_api_key.endswith("****") or not payload.deepgram_api_key:
        update_data.pop("deepgram_api_key", None)
    if payload.elevenlabs_api_key.endswith("****") or not payload.elevenlabs_api_key:
        update_data.pop("elevenlabs_api_key", None)
    if payload.twilio_auth_token.endswith("****") or not payload.twilio_auth_token:
        update_data.pop("twilio_auth_token", None)
        
    config_manager.save_config(update_data)
    return {"success": True, "message": "Configuration updated and saved to config.json."}
