from lexguard_shared.schemas.negotiation import NegotiationRecommendation
from pydantic import BaseModel, Field


class NegotiationLLMResponse(BaseModel):
    summary: str
    overall_leverage: str
    recommendations: list[NegotiationRecommendation] = Field(min_length=1, max_length=10)
