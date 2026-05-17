from enum import StrEnum

from pydantic import BaseModel, Field


class NegotiationPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NegotiationRecommendation(BaseModel):
    topic: str
    priority: NegotiationPriority
    current_term: str
    suggested_term: str
    rationale: str
    clause_id: str | None = None


class NegotiationResult(BaseModel):
    document_id: str
    summary: str
    overall_leverage: str = Field(description="weak | moderate | strong")
    recommendations: list[NegotiationRecommendation] = Field(default_factory=list)
