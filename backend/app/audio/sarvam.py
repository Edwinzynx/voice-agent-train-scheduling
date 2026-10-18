"""Sarvam realtime transcription and speech synthesis; keys stay on the server."""
import asyncio
import base64
import json
from urllib.parse import urlencode
import httpx
import websockets
from ..config import config_manager
from ..brain.language import spoken_text


async def connect_transcription():
    settings = config_manager.settings
    if not settings.sarvam_api_key:
        raise RuntimeError("Speech service is not configured. Set SARVAM_API_KEY on the server.")
    params = urlencode({"model": settings.sarvam_stt_model, "language_code": "auto",
                        "encoding": "linear16", "sample_rate": 16000, "mode": "codemix",
                        "stream_type": "fast", "endpointing": "vad", "silence_duration_ms": 650,
                        "min_speech_duration_ms": 150})
    connection = await websockets.connect(
        "wss://api.sarvam.ai/speech-to-text-realtime/ws?" + params,
        extra_headers={"Api-Subscription-Key": settings.sarvam_api_key},
        open_timeout=15, close_timeout=3, max_size=1_000_000,
    )
    try:
        message = json.loads(await asyncio.wait_for(connection.recv(), timeout=15))
        if message.get("event") != "session.begin":
            raise RuntimeError("Speech provider could not start a session. Check its credentials and quota.")
    except BaseException:
        await connection.close()
        raise
    return connection


async def synthesize_text(text, dialect="English"):
    settings = config_manager.settings
    if not settings.sarvam_api_key:
        raise RuntimeError("Speech output is not configured.")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": settings.sarvam_api_key},
            json={"text": spoken_text(text, dialect)[:2500], "language_code": "en-IN" if dialect == "English" else "hi-IN",
                  "model": settings.sarvam_tts_model, "speaker": settings.sarvam_voice,
                  "pace": 1.2,
                  "output_audio_codec": "wav", "speech_sample_rate": 22050},
        )
        if response.status_code != 200:
            raise RuntimeError("Speech output is unavailable. Check the speech provider's quota and configuration.")
        audios = response.json().get("audios", [])
        if not audios:
            raise RuntimeError("Speech provider returned no audio.")
        # Each provider item is a complete WAV; play independently, never concatenate WAV headers.
        for audio in audios:
            if not isinstance(audio, str) or not base64.b64decode(audio, validate=True):
                raise RuntimeError("Speech provider returned invalid audio.")
        return audios
