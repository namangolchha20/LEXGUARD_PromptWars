from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class BenchmarkSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    benchmark_output_dir: Path = Path("data/benchmarks")
    benchmark_data_path: Path | None = None
    benchmark_outlier_threshold: float = 50.0
    benchmark_similarity_threshold: float = 0.25
