from lexguard_shared.schemas.clause import ClauseType
from pydantic import BaseModel, Field


class ClauseAnalysisResponse(BaseModel):
    """Gemini structured output schema — validated before mapping to ExtractedClause."""

    clause_type: ClauseType
    title: str
    obligations: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    rights: list[str] = Field(default_factory=list)
    durations: list[str] = Field(default_factory=list)
    financial_liabilities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
