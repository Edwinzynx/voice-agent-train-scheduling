import httpx
import logging
from ..config import config_manager

logger = logging.getLogger(__name__)

# Default standard voice ID (Rachel)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

async def synthesize_text(text: str) -> bytes:
    """
    Synthesizes text to speech using ElevenLabs API.
    Returns binary audio bytes (MPEG).
    """
    settings = config_manager.settings
    if settings.use_mock_tts or not settings.elevenlabs_api_key:
        logger.info("ElevenLabs TTS is in mock mode. Returning empty audio bytes.")
        return b""
        
    try:
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "accept": "audio/mpeg"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        voice_id = settings.elevenlabs_voice_id or DEFAULT_VOICE_ID
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json=data,
                headers=headers,
                timeout=15.0
            )
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"ElevenLabs TTS API returned error {response.status_code}: {response.text}")
                return b""
    except Exception as e:
        logger.error(f"Error in ElevenLabs TTS: {e}")
        return b""
