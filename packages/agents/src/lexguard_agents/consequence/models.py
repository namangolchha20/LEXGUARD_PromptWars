from pydantic import BaseModel, Field


class ScenarioOutput(BaseModel):
    """Single consequence scenario — Gemini structured output."""

    scenario: str
    impact: str
    likelihood: float = Field(ge=0.0, le=100.0)
    severity: float = Field(ge=0.0, le=100.0)
    explanation: str


class ScenariosResponse(BaseModel):
    """One or more scenarios per risk finding."""

    scenarios: list[ScenarioOutput] = Field(min_length=1, max_length=3)
