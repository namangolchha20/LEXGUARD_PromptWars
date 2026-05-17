from enum import StrEnum

from pydantic import BaseModel, Field


class ClauseType(StrEnum):
    NON_COMPETE = "non_compete"
    ARBITRATION = "arbitration"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    PAYMENT = "payment"
    LIABILITY = "liability"
    PRIVACY = "privacy"
    INDEMNIFICATION = "indemnification"
    OTHER = "other"


class ExtractedClause(BaseModel):
    clause_id: str
    clause_type: ClauseType
    title: str
    text: str
    obligations: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    rights: list[str] = Field(default_factory=list)
    durations: list[str] = Field(default_factory=list)
    financial_liabilities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ClauseExtractionResult(BaseModel):
    document_id: str
    clauses: list[ExtractedClause] = Field(default_factory=list)


class ClauseExtractionJobResponse(BaseModel):
    document_id: str
    status: str
    clause_count: int = 0
    message: str | None = None
