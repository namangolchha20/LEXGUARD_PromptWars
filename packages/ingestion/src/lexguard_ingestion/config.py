from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class IngestionSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ingestion_temp_dir: Path = Path("data/temp")
    ingestion_output_dir: Path = Path("data/parsed")
    ingestion_max_file_size_mb: int = 50
    ingestion_worker_concurrency: int = 2
    ingestion_ocr_min_chars_per_page: int = 30
    ingestion_allowed_extensions: str = ".pdf,.docx"

    @property
    def max_file_size_bytes(self) -> int:
        return self.ingestion_max_file_size_mb * 1024 * 1024

    @property
    def allowed_extensions(self) -> set[str]:
        return {ext.strip().lower() for ext in self.ingestion_allowed_extensions.split(",")}
