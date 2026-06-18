import httpx
import logging
from ..config import config_manager

logger = logging.getLogger(__name__)

async def transcribe_audio_chunk(audio_bytes: bytes) -> str:
    """
    Transcribes a raw audio buffer using Deepgram API (HTTP REST).
    Used for single-turn uploads or testing.
    """
    settings = config_manager.settings
    if settings.use_mock_stt or not settings.deepgram_api_key:
        logger.info("Deepgram STT in mock mode. Returning blank transcription.")
        return ""
        
    try:
        headers = {
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "audio/wav"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
                content=audio_bytes,
                headers=headers,
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                return transcript
            else:
                logger.error(f"Deepgram STT API returned error {response.status_code}: {response.text}")
                return ""
    except Exception as e:
        logger.error(f"Error in Deepgram STT transcription: {e}")
        return ""
