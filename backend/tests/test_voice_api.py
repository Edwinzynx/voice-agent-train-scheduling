import asyncio
import base64
import json
import pytest
from app.config import config_manager, ConfigManager
from app.routers import calls
from app.audio import sarvam


def test_owner_only_admin_and_no_key_write(client):
    config_manager.settings.admin_token = "owner-test-token"
    for path in ["/dashboard/stats", "/dashboard/calls", "/dashboard/config", "/eval/runs"]:
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": "Bearer owner-test-token"}).status_code == 200
    assert client.post("/eval/run").status_code == 401
    assert client.post("/dashboard/config", json={"groq_api_key": "visitor-key"}).status_code == 405
    assert config_manager.settings.groq_api_key == ""


def test_capabilities_and_socket_reject_missing_providers(client):
    config_manager.settings.groq_api_key = ""
    config_manager.settings.sarvam_api_key = ""
    result = client.get("/calls/capabilities").json()
    assert not result["ready"]
    with client.websocket_connect("/calls/ws/missing") as websocket:
        result = websocket.receive_json()
        assert result["type"] == "error" and result["fatal"]
    assert not calls.active_connections


class FakeSpeech:
    def __init__(self):
        self.messages = []
        self.closed = False
        self.events = asyncio.Queue()

    async def send(self, raw):
        message = json.loads(raw)
        self.messages.append(message)
        if message.get("event") == "audio_input":
            await self.events.put(json.dumps({"event": "transcript.final", "text": "English"}))

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.events.get()

    async def close(self):
        self.closed = True


@pytest.fixture
def speech_provider(monkeypatch):
    provider = FakeSpeech()
    config_manager.settings.groq_api_key = "test-only"
    config_manager.settings.sarvam_api_key = "test-only"
    async def connect():
        return provider
    async def synthesize(*args):
        return [base64.b64encode(b"test audio").decode()]
    monkeypatch.setattr(sarvam, "connect_transcription", connect)
    monkeypatch.setattr(sarvam, "synthesize_text", synthesize)
    return provider


def start(websocket):
    websocket.send_json({"type": "start", "sample_rate": 16000, "encoding": "linear16"})
    assert websocket.receive_json()["type"] == "ready"
    greeting = websocket.receive_json()
    assert greeting["state"] == "LANGUAGE"
    assert greeting["audio_segments"]


def test_microphone_to_transcription_to_response(client, speech_provider):
    with client.websocket_connect("/calls/ws/audio-regression") as websocket:
        start(websocket)
        audio = base64.b64encode(b"\0\0" * 1600).decode()
        websocket.send_json({"type": "audio", "audio": audio})
        assert websocket.receive_json() == {"type": "user_transcript", "text": "English"}
        assert websocket.receive_json()["type"] == "processing"
        response = websocket.receive_json()
        assert response["type"] == "agent_response"
        assert response["state"] == "INTENT"
        assert response["dialect"] == "English"
        assert response["audio_segments"]
        websocket.send_json({"type": "stop"})
        assert websocket.receive()["type"] == "websocket.close"
    assert any(message.get("audio") == audio for message in speech_provider.messages)
    assert speech_provider.closed
    assert not calls.active_connections


def test_bad_audio_is_not_forwarded(client, speech_provider):
    with client.websocket_connect("/calls/ws/invalid-audio") as websocket:
        start(websocket)
        websocket.send_json({"type": "audio", "audio": "not base64!"})
        result = websocket.receive_json()
        assert result["type"] == "error" and result["fatal"]
        assert websocket.receive()["type"] == "websocket.close"
    assert not any(message.get("event") == "audio_input" for message in speech_provider.messages)


def test_tts_failure_keeps_text_visible(client, speech_provider, monkeypatch):
    async def failure(*args):
        raise RuntimeError("provider down")
    monkeypatch.setattr(sarvam, "synthesize_text", failure)
    with client.websocket_connect("/calls/ws/tts-failure") as websocket:
        websocket.send_json({"type": "start", "sample_rate": 16000, "encoding": "linear16"})
        assert websocket.receive_json()["type"] == "ready"
        response = websocket.receive_json()
        assert response["text"] and response["audio_error"]
        assert "audio_segments" not in response
        websocket.send_json({"type": "stop"})
        assert websocket.receive()["type"] == "websocket.close"
    assert not calls.active_connections


def test_render_environment_ignores_debug_flags(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setenv("ALLOW_SIMULATED_RAILWAY", "true")
    monkeypatch.setenv("PORT", "10000")
    settings = ConfigManager().settings
    assert settings.environment == "production"
    assert not settings.use_mock_llm and not settings.allow_simulated_railway
    assert settings.port == 10000


def test_text_chat_works_without_speech_key_or_speech_calls(client, monkeypatch):
    config_manager.settings.groq_api_key = "test-only"
    async def unexpected_speech(*args):
        pytest.fail("Text chat must not consume speech credits")
    monkeypatch.setattr(sarvam, "connect_transcription", unexpected_speech)
    monkeypatch.setattr(sarvam, "synthesize_text", unexpected_speech)
    result = client.get("/calls/capabilities").json()
    assert result["text_ready"] and not result["ready"]
    with client.websocket_connect("/calls/ws/text-only") as websocket:
        websocket.send_json({"type": "start", "mode": "text"})
        assert websocket.receive_json()["type"] == "ready"
        greeting = websocket.receive_json()
        assert greeting["state"] == "LANGUAGE"
        assert "audio_segments" not in greeting and "audio_error" not in greeting
        websocket.send_json({"type": "user_transcript", "text": "English"})
        assert websocket.receive_json()["type"] == "processing"
        response = websocket.receive_json()
        assert response["state"] == "INTENT"
        assert "audio_segments" not in response
        websocket.send_json({"type": "stop"})
        assert websocket.receive()["type"] == "websocket.close"
    assert not calls.active_connections


def test_voice_still_requires_speech_key(client):
    config_manager.settings.groq_api_key = "test-only"
    with client.websocket_connect("/calls/ws/no-speech-key") as websocket:
        websocket.send_json({"type": "start", "mode": "voice", "sample_rate": 16000, "encoding": "linear16"})
        result = websocket.receive_json()
        assert result["type"] == "error" and result["fatal"]
        assert "SARVAM_API_KEY" in result["message"]
        assert websocket.receive()["type"] == "websocket.close"


def test_unknown_session_mode_rejected(client, speech_provider):
    with client.websocket_connect("/calls/ws/invalid-mode") as websocket:
        websocket.send_json({"type": "start", "mode": "anything"})
        result = websocket.receive_json()
        assert result["type"] == "error" and result["fatal"]
        assert websocket.receive()["type"] == "websocket.close"
    assert not speech_provider.messages


def test_debug_train_reply_does_not_dump_provider_payload():
    from app.brain.llm import run_mock_brain_step
    result = run_mock_brain_step("EXECUTE", "", {"result": {
        "success": True, "trains": [{"no": "14217", "raw_train_data": {"internal": "large upstream payload"}}]
    }})
    assert "Found 1 trains" in result["response"]
    assert "raw_train_data" not in result["response"]
    assert "upstream payload" not in result["response"]


def test_allowed_origin_url_trailing_slash(client, speech_provider, monkeypatch):
    from app.config import configured_origins
    from starlette.websockets import WebSocketDisconnect
    origin = "https://locovoice-skkrrt-train-agent.vercel.app"
    monkeypatch.setenv("ALLOWED_ORIGINS", f" {origin}/ ")
    assert configured_origins() == [origin]
    with client.websocket_connect("/calls/ws/allowed-origin", headers={"origin": origin}) as websocket:
        websocket.send_json({"type": "start", "mode": "text"})
        assert websocket.receive_json()["type"] == "ready"
        assert websocket.receive_json()["type"] == "agent_response"
        websocket.send_json({"type": "stop"})
        assert websocket.receive()["type"] == "websocket.close"
    with pytest.raises(WebSocketDisconnect) as denied:
        with client.websocket_connect("/calls/ws/denied-origin", headers={"origin": "https://untrusted.example"}):
            pass
    assert denied.value.code == 1008
