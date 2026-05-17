from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    orchestrator_state_dir: Path = Path("data/orchestrator")
    orchestrator_max_retries: int = 2
    orchestrator_retry_base_delay: float = 1.0
    orchestrator_fail_fast: bool = False
