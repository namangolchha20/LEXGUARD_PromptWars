from lexguard_shared.schemas.benchmark import FairnessLevel
from pydantic import BaseModel


class BenchmarkExplanationResponse(BaseModel):
    benchmark_summary: str
    comparative_explanation: str
    negotiation_recommendation: str
    fairness_assessment: FairnessLevel
    contract_value: str
