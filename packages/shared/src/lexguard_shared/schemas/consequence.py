from pydantic import BaseModel, Field


class ConsequenceScenario(BaseModel):
    scenario: str
    impact: str
    likelihood: float = Field(ge=0.0, le=100.0, description="Probability estimate 0-100")
    severity: float = Field(ge=0.0, le=100.0, description="Impact severity 0-100")
    explanation: str
    clause_id: str
    clause_title: str
    finding_id: str | None = None


class ConsequenceSimulationResult(BaseModel):
    document_id: str
    scenarios: list[ConsequenceScenario] = Field(default_factory=list)
    summary: str = ""


class ConsequenceSimulationJobResponse(BaseModel):
    document_id: str
    status: str
    scenario_count: int = 0
    message: str | None = None
