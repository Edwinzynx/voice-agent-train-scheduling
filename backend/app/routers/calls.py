import json
import uuid
import time
import base64
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Call, CallLog
from ..brain.fsm import fsm_coordinator
from ..audio import deepgram, elevenlabs
from ..config import config_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/calls",
    tags=["calls"]
)

# Active live calls stored in memory for real-time dashboard listeners to query.
active_connections = {}

@router.websocket("/ws/{call_id}")
async def call_websocket(websocket: WebSocket, call_id: str, db: Session = Depends(get_db)):
    """
    WebSocket handling real-time voice stream or text events from Twilio or browser.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for call: {call_id}")
    
    # Initialize Call DB model
    call_record = Call(
        id=call_id,
        caller_number="WebRTC-User",
        status="active",
        start_time=datetime.utcnow(),
        success=False
    )
    db.add(call_record)
    db.commit()
    
    # Register connection in active registry
    active_connections[call_id] = {
        "websocket": websocket,
        "fsm_session": fsm_coordinator.get_or_create_session(call_id)
    }
    
    # Send initial greeting
    greeting_text = fsm_coordinator.process_turn(call_id, "GREET")
    
    # Log greeting turn in database
    greet_log = CallLog(
        call_id=call_id,
        direction="outbound",
        state="GREET",
        text=greeting_text,
        latency_ms=0.0,
        slots_snapshot=json.dumps(active_connections[call_id]["fsm_session"].slots)
    )
    db.add(greet_log)
    db.commit()
    
    # Send greeting to browser
    await websocket.send_json({
        "type": "agent_response",
        "text": greeting_text,
        "state": "GREET",
        "slots": active_connections[call_id]["fsm_session"].slots,
        "dialect": active_connections[call_id]["fsm_session"].dialect
    })
    
    try:
        while True:
            # Wait for client packets
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            
            # Case 1: Browser WebSpeech client sending pre-transcribed text
            if data.get("type") == "user_transcript":
                user_text = data.get("text", "")
                if not user_text:
                    continue
                
                # Run the FSM turn
                fsm_session = active_connections[call_id]["fsm_session"]
                current_state_before = fsm_session.state
                
                start_time = time.time()
                response_text = fsm_coordinator.process_turn(call_id, user_text)
                turn_latency = (time.time() - start_time) * 1000
                
                # Persist turn in SQLite
                # 1. User turn
                user_log = CallLog(
                    call_id=call_id,
                    direction="inbound",
                    state=current_state_before,
                    text=user_text,
                    latency_ms=0.0,
                    slots_snapshot=json.dumps(fsm_session.slots)
                )
                db.add(user_log)
                
                # 2. Agent turn
                agent_log = CallLog(
                    call_id=call_id,
                    direction="outbound",
                    state=fsm_session.state,
                    text=response_text,
                    latency_ms=turn_latency,
                    slots_snapshot=json.dumps(fsm_session.slots)
                )
                db.add(agent_log)
                db.commit()
                
                # Send text response to client
                response_payload = {
                    "type": "agent_response",
                    "text": response_text,
                    "state": fsm_session.state,
                    "slots": fsm_session.slots,
                    "latency_ms": turn_latency,
                    "dialect": fsm_session.dialect
                }
                
                # If we're using real TTS, synthesize and add base64 audio
                if not config_manager.settings.use_mock_tts:
                    audio_bytes = await elevenlabs.synthesize_text(response_text)
                    if audio_bytes:
                        response_payload["audio"] = base64.b64encode(audio_bytes).decode("utf-8")
                        
                await websocket.send_json(response_payload)
                
                # Check if call is completed
                if fsm_session.state == "END":
                    # Let the final message play, then disconnect
                    call_record.success = fsm_session.booking_success
                    db.commit()
                    
            # Case 2: Streaming raw audio from Twilio (Media Stream protocol)
            elif data.get("event") == "media":
                # Twilio payload: base64 mulaw audio chunks
                payload = data["media"]["payload"]
                raw_audio = base64.b64decode(payload)
                
                # In real scenario: feed raw_audio to Deepgram WebSocket.
                # If Deepgram returns final transcript -> run FSM turn and play output.
                # Since Twilio requires full bidirectional streaming logic, we log here.
                pass
                
            elif data.get("event") == "stop":
                logger.info(f"Twilio call stop received for {call_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call: {call_id}")
    except Exception as e:
        logger.error(f"Error handling websocket for call {call_id}: {e}")
    finally:
        # Finalize DB call records
        fsm_session = active_connections.get(call_id, {}).get("fsm_session")
        if fsm_session:
            p50, p90, _ = fsm_session.get_latency_metrics()
            
            call_record.status = "completed"
            call_record.end_time = datetime.utcnow()
            call_record.duration_seconds = (call_record.end_time - call_record.start_time).total_seconds()
            call_record.p50_latency_ms = p50
            call_record.p90_latency_ms = p90
            call_record.success = fsm_session.booking_success
            
            # Combine all logs text into transcription field for full-text search
            all_logs = db.query(CallLog).filter(CallLog.call_id == call_id).order_by(CallLog.id).all()
            call_record.transcription = "\n".join([f"{l.direction.upper()}: {l.text}" for l in all_logs])
            
            # Simple summary
            call_record.summary = f"Intent: {fsm_session.intent or 'None'}. State reached: {fsm_session.state}. Slots: {json.dumps(fsm_session.slots)}"
            
            db.commit()
            
        if call_id in active_connections:
            del active_connections[call_id]
        fsm_coordinator.remove_session(call_id)
