from enum import StrEnum

from pydantic import BaseModel, Field


class RiskCategory(StrEnum):
    EMPLOYMENT_RISK = "employment_risk"
    PRIVACY_RISK = "privacy_risk"
    FINANCIAL_RISK = "financial_risk"
    IP_RISK = "ip_risk"
    ARBITRATION_RISK = "arbitration_risk"
    COMPLIANCE_RISK = "compliance_risk"


class RiskFlag(StrEnum):
    EXPLOITATIVE_LANGUAGE = "exploitative_language"
    VAGUE_LANGUAGE = "vague_language"
    HIDDEN_LIABILITY = "hidden_liability"
    ONE_SIDED_OBLIGATION = "one_sided_obligation"
    EXCESSIVE_RESTRICTION = "excessive_restriction"


class AffectedParty(BaseModel):
    party: str
    role: str
    impact: str
    risk_level: str = Field(description="low | medium | high")


class RuleEvidence(BaseModel):
    rule_id: str
    rule_name: str
    matched_text: str
    pattern: str
    weight: float = Field(ge=0.0, le=1.0)


class RiskFinding(BaseModel):
    finding_id: str
    clause_id: str
    clause_title: str
    category: RiskCategory
    flag: RiskFlag
    severity_score: float = Field(ge=0.0, le=100.0, description="Weighted severity 0-100")
    confidence: float = Field(ge=0.0, le=1.0)
    plain_language_explanation: str
    legal_reasoning: str
    affected_parties: list[AffectedParty] = Field(default_factory=list)
    rule_evidence: list[RuleEvidence] = Field(default_factory=list)
    llm_enhanced: bool = False


class CategoryScore(BaseModel):
    category: RiskCategory
    score: float = Field(ge=0.0, le=100.0)
    finding_count: int = 0


class DocumentRiskAnalysis(BaseModel):
    document_id: str
    overall_severity_score: float = Field(ge=0.0, le=100.0)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    findings: list[RiskFinding] = Field(default_factory=list)
    category_scores: list[CategoryScore] = Field(default_factory=list)


class RiskAnalysisJobResponse(BaseModel):
    document_id: str
    status: str
    finding_count: int = 0
    overall_severity_score: float = 0.0
    message: str | None = None
