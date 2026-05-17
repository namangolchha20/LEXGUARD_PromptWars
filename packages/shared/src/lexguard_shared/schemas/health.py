from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response — keep in sync with @lexguard/shared TypeScript types."""

    status: str = "ok"
    service: str
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
