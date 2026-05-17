from lexguard_shared.schemas.risk import AffectedParty, RiskCategory, RiskFlag
from pydantic import BaseModel, Field


class LLMRiskAssessment(BaseModel):
    """Structured LLM output for hybrid risk enrichment."""

    category: RiskCategory
    flag: RiskFlag
    severity_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    plain_language_explanation: str
    legal_reasoning: str
    affected_parties: list[AffectedParty] = Field(default_factory=list)
