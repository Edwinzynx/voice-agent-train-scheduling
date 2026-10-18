import asyncio
import base64
import json
from urllib.parse import urlparse, parse_qs
import pytest
from app.audio import sarvam
from app.config import config_manager


def test_streaming_provider_contract(monkeypatch):
    config_manager.settings.sarvam_api_key = "server-only-secret"
    captured = {}
    class Connection:
        closed = False
        async def recv(self):
            return json.dumps({"event": "session.begin"})
        async def close(self):
            self.closed = True
    connection = Connection()
    async def connect(url, **kwargs):
        captured.update(url=url, **kwargs)
        return connection
    monkeypatch.setattr(sarvam.websockets, "connect", connect)
    assert asyncio.run(sarvam.connect_transcription()) is connection
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["sample_rate"] == ["16000"]
    assert params["encoding"] == ["linear16"]
    assert params["language_code"] == ["auto"]
    assert "server-only-secret" not in captured["url"]
    assert captured["extra_headers"]["Api-Subscription-Key"] == "server-only-secret"


def test_failed_provider_handshake_closes_socket(monkeypatch):
    config_manager.settings.sarvam_api_key = "test"
    class Connection:
        closed = False
        async def recv(self):
            return json.dumps({"event": "error", "is_fatal": True})
        async def close(self):
            self.closed = True
    connection = Connection()
    async def connect(*args, **kwargs):
        return connection
    monkeypatch.setattr(sarvam.websockets, "connect", connect)
    with pytest.raises(RuntimeError):
        asyncio.run(sarvam.connect_transcription())
    assert connection.closed


def test_tts_auth_language_and_multiple_wav_segments(monkeypatch):
    config_manager.settings.sarvam_api_key = "server-only-secret"
    audio = base64.b64encode(b"RIFF-test-wave").decode()
    captured = {}
    class Response:
        status_code = 200
        def json(self):
            return {"audios": [audio, audio]}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            captured.update(url=url, **kwargs)
            return Response()
    monkeypatch.setattr(sarvam.httpx, "AsyncClient", Client)
    assert asyncio.run(sarvam.synthesize_text("Namaste", "Hinglish")) == [audio, audio]
    assert captured["headers"]["api-subscription-key"] == "server-only-secret"
    assert captured["json"]["language_code"] == "hi-IN"
    assert captured["json"]["output_audio_codec"] == "wav"
