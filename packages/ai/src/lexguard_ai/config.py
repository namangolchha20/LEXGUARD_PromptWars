from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_retries: int = 3
    gemini_retry_base_delay: float = 1.0
    gemini_temperature: float = 0.1
    gemini_max_concurrency: int = 5
