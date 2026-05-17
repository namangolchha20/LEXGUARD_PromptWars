from enum import StrEnum

from pydantic import BaseModel, Field


class FairnessLevel(StrEnum):
    FAVORABLE = "favorable"
    NEUTRAL = "neutral"
    UNFAVORABLE = "unfavorable"


class BenchmarkComparison(BaseModel):
    clause_id: str
    clause_title: str
    metric: str
    benchmark_summary: str
    contract_value: str
    benchmark_range: str
    deviation_score: float = Field(ge=0.0, le=100.0)
    fairness_assessment: FairnessLevel
    is_outlier: bool
    similarity_score: float = Field(ge=0.0, le=1.0)
    comparative_explanation: str
    negotiation_recommendation: str


class DocumentBenchmarkResult(BaseModel):
    document_id: str
    benchmark_summary: str
    overall_deviation_score: float = Field(ge=0.0, le=100.0)
    overall_fairness: FairnessLevel
    comparisons: list[BenchmarkComparison] = Field(default_factory=list)
    outlier_count: int = 0


class BenchmarkJobResponse(BaseModel):
    document_id: str
    status: str
    comparison_count: int = 0
    overall_deviation_score: float = 0.0
    message: str | None = None
