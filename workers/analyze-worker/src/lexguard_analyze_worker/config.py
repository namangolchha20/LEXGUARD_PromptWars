from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://lexguard:lexguard@localhost:5432/lexguard"
    analyze_worker_concurrency: int = 2


settings = WorkerSettings()
