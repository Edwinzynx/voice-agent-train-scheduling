import os
import json
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"


def configured_origins(default="*"):
    # Browsers send an origin without a trailing slash, even when the owner
    # copies a site URL ending in / from the address bar.
    return [value.strip().rstrip("/") for value in os.getenv("ALLOWED_ORIGINS", default).split(",") if value.strip()]

class AppSettings(BaseModel):
    environment: str = "development"
    admin_token: str = ""
    sarvam_api_key: str = ""
    sarvam_stt_model: str = "saaras:v3-realtime"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_voice: str = "shubh"
    allow_simulated_railway: bool = False
    groq_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    sms_provider: str = "mock"  # "mock" or "twilio" or "msg91"
    
    # LLM config
    llm_model: str = "qwen/qwen3.8-27b"
    
    # TTS config
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    
    # Mode flags
    use_mock_llm: bool = False
    use_mock_stt: bool = False
    use_mock_tts: bool = False
    
    # Server configs
    host: str = "0.0.0.0"
    port: int = 8000
    db_url: str = "sqlite:///./voice_agent.db"

class ConfigManager:
    def __init__(self):
        self.settings = AppSettings()
        self.load_config()

    def load_config(self):
        production = os.getenv("APP_ENV") == "production" or os.getenv("RENDER") == "true"
        values = {}
        if CONFIG_FILE.exists() and not production:
            with open(CONFIG_FILE, encoding="utf-8") as config_file:
                values = json.load(config_file)
        for key in AppSettings.model_fields:
            if key.upper() in os.environ:
                values[key] = os.environ[key.upper()]
        if "PORT" in os.environ:
            values["port"] = os.environ["PORT"]
        if "DATABASE_URL" in os.environ:
            values["db_url"] = os.environ["DATABASE_URL"]
        if production:
            values["environment"] = "production"
        self.settings = AppSettings.model_validate(values)
        if self.settings.environment == "production":
            self.settings.use_mock_llm = False
            self.settings.use_mock_stt = False
            self.settings.use_mock_tts = False
            self.settings.allow_simulated_railway = False
        else:
            if not self.settings.groq_api_key:
                self.settings.use_mock_llm = True
            if not self.settings.sarvam_api_key:
                self.settings.use_mock_stt = True
                self.settings.use_mock_tts = True

    def save_config(self, new_settings: dict):
        if self.settings.environment == "production":
            raise ValueError("Manage production configuration in the hosting environment.")
        values = self.settings.model_dump()
        values.update(new_settings)
        updated = AppSettings.model_validate(values)
        if not updated.groq_api_key:
            updated.use_mock_llm = True
        if not updated.sarvam_api_key:
            updated.use_mock_stt = True
            updated.use_mock_tts = True
        # A failed disk write must not report a successful save.
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(updated.model_dump(), config_file, indent=4)
        self.settings = updated

config_manager = ConfigManager()
