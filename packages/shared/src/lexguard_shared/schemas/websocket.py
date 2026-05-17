from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WsMessageType(StrEnum):
    """WebSocket message types — mirrored in TypeScript WsMessageType."""

    PING = "ping"
    PONG = "pong"
    CONNECTED = "connected"
    ERROR = "error"
    ORCHESTRATOR = "orchestrator"
    SUBSCRIBE = "subscribe"


class WsEnvelope(BaseModel):
    """Canonical WebSocket envelope for all LEXGUARD real-time messages."""

    type: WsMessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
