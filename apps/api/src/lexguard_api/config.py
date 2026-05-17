from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://lexguard:lexguard@localhost:5432/lexguard"
    redis_url: str = "redis://localhost:6379/0"

    ingestion_temp_dir: Path = Path("data/temp")
    ingestion_output_dir: Path = Path("data/parsed")
    ingestion_max_file_size_mb: int = 50
    ingestion_worker_concurrency: int = 2
    ingestion_ocr_min_chars_per_page: int = 30

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_retries: int = 3
    gemini_retry_base_delay: float = 1.0
    gemini_temperature: float = 0.1
    gemini_max_concurrency: int = 5
    clause_output_dir: Path = Path("data/clauses")
    risk_output_dir: Path = Path("data/risk")
    risk_llm_enhancement_threshold: float = 0.3
    risk_rule_weight: float = 0.55
    risk_llm_weight: float = 0.45
    consequence_output_dir: Path = Path("data/consequences")
    benchmark_output_dir: Path = Path("data/benchmarks")
    orchestrator_state_dir: Path = Path("data/orchestrator")
    orchestrator_max_retries: int = 2

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


settings = Settings()
