import asyncio
import base64
import copy
import json
import logging
import os
import re
import time
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Call, CallLog
from ..brain.fsm import fsm_coordinator
from ..audio import sarvam
from ..config import config_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])
active_connections = {}
recent_starts = {}


@router.get("/capabilities")
def capabilities():
    settings = config_manager.settings
    debug = settings.environment != "production"
    browser_speech = debug and settings.use_mock_stt
    mock_llm = debug and settings.use_mock_llm
    missing = []
    if not mock_llm and not settings.groq_api_key:
        missing.append("GROQ_API_KEY")
    if not browser_speech and not settings.sarvam_api_key:
        missing.append("SARVAM_API_KEY")
    text_ready = mock_llm or bool(settings.groq_api_key)
    return {"ready": not missing, "missing": missing, "text_ready": text_ready,
            "text_message": "Chat is ready." if text_ready else "Chat is not configured on the server: GROQ_API_KEY",
            "speech_provider": "browser" if browser_speech else "sarvam",
            "environment": settings.environment, "booking_available": False,
            "message": "Voice service is ready." if not missing else "Voice service is not configured on the server: " + ", ".join(missing)}


def public_trains(trains):
    return [{k: v for k, v in train.items() if k != "raw_train_data"} for train in trains]


@router.websocket("/ws/{call_id}")
async def call_websocket(websocket: WebSocket, call_id: str, db: Session = Depends(get_db)):
    origins = [v.strip() for v in os.getenv("ALLOWED_ORIGINS", "").split(",") if v.strip()]
    if origins and "*" not in origins and websocket.headers.get("origin") not in origins:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    # Small public demo limits protect the owner's speech budget; no paid calls are started here.
    now = time.monotonic()
    for key in list(recent_starts):
        recent_starts[key] = [started_at for started_at in recent_starts[key] if now - started_at < 300]
        if not recent_starts[key]:
            del recent_starts[key]
    caller = websocket.client.host if websocket.client else "unknown"
    if len(active_connections) >= 2 or len(recent_starts.get(caller, [])) >= 3:
        await websocket.send_json({"type": "error", "message": "Call limit reached. Please try again in a few minutes.", "fatal": True})
        await websocket.close(code=1013)
        return
    if not re.fullmatch(r"[\w-]{1,80}", call_id) or call_id in active_connections or db.get(Call, call_id):
        await websocket.send_json({"type": "error", "message": "This call ID is unavailable. Please start a new call.", "fatal": True})
        await websocket.close(code=1008)
        return
    availability = capabilities()
    if not availability["text_ready"]:
        await websocket.send_json({"type": "error", "message": availability["message"], "fatal": True})
        await websocket.close(code=1013)
        return
    recent_starts.setdefault(caller, []).append(now)

    session = fsm_coordinator.get_or_create_session(call_id)
    record = Call(id=call_id, status="active", start_time=datetime.utcnow(), success=False)
    speech = None
    tasks = []
    turns = asyncio.Queue(maxsize=4)
    send_lock = asyncio.Lock()
    started = False
    voice_mode = True
    processing = False
    failed = False
    deadline = time.monotonic() + 600

    async def send(payload):
        async with send_lock:
            await websocket.send_json(payload)

    async def respond(text, latency=0):
        payload = {"type": "agent_response", "text": text, "state": session.state,
                   "slots": session.slots.copy(), "dialect": session.dialect, "latency_ms": latency,
                   "available_trains": public_trains(session.available_trains),
                   "last_action_result": session.last_action_result}
        if payload["last_action_result"] and "trains" in payload["last_action_result"]:
            payload["last_action_result"] = {**payload["last_action_result"], "trains": public_trains(payload["last_action_result"]["trains"])}
        if voice_mode and availability["speech_provider"] == "sarvam":
            try:
                payload["audio_segments"] = await sarvam.synthesize_text(text, "English" if session.state == "LANGUAGE" else session.dialect)
                payload["audio_mime"] = "audio/wav"
            except Exception:
                logger.warning("Speech synthesis unavailable for call %s", call_id)
                payload["audio_error"] = "Speech output is unavailable. The response is shown as text; you can keep speaking."
        await send(payload)

    async def run_turn(data):
        nonlocal processing
        processing = True
        await send({"type": "processing"})
        before = session.state
        slots_before = session.slots.copy()
        snapshot = copy.deepcopy(session.__dict__)
        started_at = time.monotonic()
        selection = data.get("type") == "select_train"
        text = f"Selected train {data.get('train_no')} class {data.get('class_code')}" if selection else str(data.get("text", ""))[:2000]
        try:
            if selection:
                response = await asyncio.to_thread(fsm_coordinator.select_train, call_id, str(data.get("train_no", "")), str(data.get("class_code", "")))
            else:
                response = await asyncio.to_thread(fsm_coordinator.process_turn, call_id, text)
            latency = (time.monotonic() - started_at) * 1000
            db.add(CallLog(call_id=call_id, direction="inbound", state=before, text=text, slots_snapshot=json.dumps(slots_before)))
            db.add(CallLog(call_id=call_id, direction="outbound", state=session.state, text=response, latency_ms=latency, slots_snapshot=json.dumps(session.slots)))
            db.commit()
            await respond(response, latency)
        except (RuntimeError, ValueError) as exc:
            session.__dict__.update(snapshot)
            await send({"type": "error", "message": str(exc), "fatal": False})
        finally:
            processing = False

    async def worker():
        while True:
            data = await turns.get()
            try:
                await run_turn(data)
            finally:
                turns.task_done()

    async def receive_speech():
        async for raw in speech:
            event = json.loads(raw)
            if event.get("event") == "transcript.final":
                text = str(event.get("text", "")).strip()
                if text and not processing and session.state != "END":
                    await send({"type": "user_transcript", "text": text})
                    await turns.put({"type": "user_transcript", "text": text})
            elif event.get("event") == "error":
                raise RuntimeError("Speech recognition failed. Please reconnect and check the provider's quota.")
        raise RuntimeError("Speech recognition disconnected. Please start a new call.")

    async def keepalive():
        while True:
            await asyncio.sleep(10)
            await speech.send(json.dumps({"event": "ping"}))

    try:
        db.add(record)
        db.commit()
        active_connections[call_id] = {"websocket": websocket, "fsm_session": session}
        while time.monotonic() < deadline:
            if not started and time.monotonic() > deadline - 570:
                raise RuntimeError("Call setup timed out. Please reconnect.")
            for task in tasks:
                if task.done():
                    task.result()
                    raise RuntimeError("A voice connection ended unexpectedly. Please reconnect.")
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=1)
            except asyncio.TimeoutError:
                continue
            if len(raw) > 24000:
                raise ValueError("Audio packet is too large.")
            data = json.loads(raw)
            kind = data.get("type")
            if kind == "start" and not started:
                mode = data.get("mode", "voice")
                if mode not in ("voice", "text"):
                    raise ValueError("Choose voice or text mode.")
                voice_mode = mode == "voice"
                if voice_mode and not availability["ready"]:
                    raise RuntimeError(availability["message"])
                if voice_mode and availability["speech_provider"] == "sarvam":
                    if data.get("sample_rate") != 16000 or data.get("encoding") != "linear16":
                        raise ValueError("Microphone audio must be 16 kHz mono PCM.")
                    speech = await sarvam.connect_transcription()
                    tasks.extend([asyncio.create_task(receive_speech()), asyncio.create_task(keepalive())])
                tasks.append(asyncio.create_task(worker()))
                started = True
                processing = True
                greeting = fsm_coordinator.process_turn(call_id, "GREET")
                db.add(CallLog(call_id=call_id, direction="outbound", state=session.state, text=greeting))
                db.commit()
                await send({"type": "ready"})
                await respond(greeting)
                processing = False
            elif kind == "audio" and started and speech:
                audio = base64.b64decode(data.get("audio", ""), validate=True)
                if not audio or len(audio) % 2 or len(audio) > 16000:
                    raise ValueError("Invalid PCM audio packet.")
                if not processing and session.state != "END":
                    await speech.send(json.dumps({"event": "audio_input", "audio": data["audio"]}))
            elif kind in ("user_transcript", "select_train") and started:
                if processing or not turns.empty():
                    await send({"type": "error", "message": "Please wait for the current response.", "fatal": False})
                    continue
                if kind == "user_transcript" and not str(data.get("text", "")).strip():
                    continue
                await turns.put(data)
            elif kind == "stop":
                break
        else:
            await send({"type": "error", "message": "This call reached the ten-minute limit. Start another call to continue.", "fatal": True})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        failed = True
        logger.warning("Call %s failed (%s)", call_id, type(exc).__name__)
        try:
            await send({"type": "error", "message": str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Voice service disconnected. Please try again.", "fatal": True})
        except Exception:
            pass
    finally:
        # Wait for an already-started turn to finish; never orphan a tool operation.
        while not turns.empty():
            turns.get_nowait()
            turns.task_done()
        if tasks and not tasks[-1].done() and processing:
            await asyncio.shield(turns.join())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if speech:
            try:
                await speech.send(json.dumps({"event": "end"}))
            except Exception:
                pass
            await speech.close()
        try:
            db.rollback()
            record.status = "failed" if failed else "completed"
            record.end_time = datetime.utcnow()
            record.duration_seconds = (record.end_time - record.start_time).total_seconds()
            record.p50_latency_ms, record.p90_latency_ms, _ = session.get_latency_metrics()
            record.success = session.booking_success
            logs = db.query(CallLog).filter(CallLog.call_id == call_id).order_by(CallLog.id).all()
            record.transcription = "\n".join(f"{log.direction}: {log.text}" for log in logs)
            record.summary = f"Intent: {session.intent}. State reached: {session.state}."
            db.commit()
        finally:
            active_connections.pop(call_id, None)
            fsm_coordinator.remove_session(call_id)
            try:
                await websocket.close()
            except Exception:
                pass
