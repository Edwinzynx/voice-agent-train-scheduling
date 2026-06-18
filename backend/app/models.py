import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True, index=True)
    caller_number = Column(String, default="WebRTC-User")
    status = Column(String, default="active")  # active, completed, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    transcription = Column(Text, default="")
    summary = Column(Text, default="")
    recording_path = Column(String, default="")
    p50_latency_ms = Column(Float, default=0.0)
    p90_latency_ms = Column(Float, default=0.0)
    success = Column(Boolean, default=False)
    
    logs = relationship("CallLog", back_populates="call", cascade="all, delete-orphan")

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    direction = Column(String)  # inbound (user speaking), outbound (agent speaking), system (state changes/events)
    state = Column(String)      # GREET, INTENT, COLLECT, etc.
    text = Column(Text)
    latency_ms = Column(Float, default=0.0)
    slots_snapshot = Column(Text, default="{}")  # JSON string of slots filled up to this turn

    call = relationship("Call", back_populates="logs")

    def get_slots(self):
        try:
            return json.loads(self.slots_snapshot)
        except Exception:
            return {}

class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String, primary_key=True, index=True)
    run_time = Column(DateTime, default=datetime.utcnow)
    dataset_version = Column(String, default="1.0")
    total_cases = Column(Integer, default=0)
    completed_cases = Column(Integer, default=0)
    overall_success_rate = Column(Float, default=0.0)
    avg_slot_accuracy = Column(Float, default=0.0)
    p50_latency = Column(Float, default=0.0)
    p90_latency = Column(Float, default=0.0)
    p99_latency = Column(Float, default=0.0)
    raw_results = Column(Text, default="[]")  # JSON string representation of all run detail results
