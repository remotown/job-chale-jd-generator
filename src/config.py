import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    PORT: int = int(os.getenv("PORT", 8000))
    API_KEY: str = os.getenv("API_KEY", "")

    # DeepSeek / OpenAI Configs
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Security Configs
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds
    ENABLE_SECURITY_VALIDATION: bool = os.getenv("ENABLE_SECURITY_VALIDATION", "true").lower() == "true"
    SECURITY_LOG_LEVEL: str = os.getenv("SECURITY_LOG_LEVEL", "WARNING")

settings = Settings()
