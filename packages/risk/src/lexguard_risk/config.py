from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class RiskSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    risk_output_dir: Path = Path("data/risk")
    risk_llm_enhancement_threshold: float = 0.3
    risk_rule_weight: float = 0.55
    risk_llm_weight: float = 0.45
