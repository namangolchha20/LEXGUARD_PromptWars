from pathlib import Path

from lexguard_shared.config import BaseSettings
from pydantic_settings import SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    clause_output_dir: Path = Path("data/clauses")
    consequence_output_dir: Path = Path("data/consequences")
