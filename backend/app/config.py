import os
import json
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

class AppSettings(BaseModel):
    groq_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    sms_provider: str = "mock"  # "mock" or "twilio" or "msg91"
    
    # LLM config
    llm_model: str = "llama-3.3-70b-versatile"
    
    # TTS config
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    
    # RapidAPI config
    rapidapi_key: str = ""
    rapidapi_host: str = "irctc1.p.rapidapi.com"
    use_real_irctc_api: bool = False
    
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
        # 1. Load from environment variables first
        self.settings.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.settings.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "")
        self.settings.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.settings.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.settings.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.settings.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.settings.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.settings.llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.settings.rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
        self.settings.rapidapi_host = os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")
        self.settings.use_real_irctc_api = os.getenv("USE_REAL_IRCTC_API", "False").lower() in ("true", "1", "yes")
        
        # 2. Override with local json file if exists
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    file_data = json.load(f)
                    for key, val in file_data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, val)
            except Exception as e:
                print(f"Error loading config.json: {e}")
                
        # 3. Dynamic Mock fallback checks
        # If API keys are empty, set mock modes to True
        if not self.settings.groq_api_key:
            self.settings.use_mock_llm = True
        if not self.settings.deepgram_api_key:
            self.settings.use_mock_stt = True
        if not self.settings.elevenlabs_api_key:
            self.settings.use_mock_tts = True

    def save_config(self, new_settings: dict):
        # Merge new settings
        for key, val in new_settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, val)
                
        # Save to file
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.settings.model_dump(), f, indent=4)
        except Exception as e:
            print(f"Error saving config.json: {e}")
            
        # Re-verify mock fallbacks
        if not self.settings.groq_api_key:
            self.settings.use_mock_llm = True
        else:
            self.settings.use_mock_llm = new_settings.get("use_mock_llm", False)
            
        if not self.settings.deepgram_api_key:
            self.settings.use_mock_stt = True
        else:
            self.settings.use_mock_stt = new_settings.get("use_mock_stt", False)
            
        if not self.settings.elevenlabs_api_key:
            self.settings.use_mock_tts = True
        else:
            self.settings.use_mock_tts = new_settings.get("use_mock_tts", False)

config_manager = ConfigManager()
