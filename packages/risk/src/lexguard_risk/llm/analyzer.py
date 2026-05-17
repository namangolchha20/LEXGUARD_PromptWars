import logging

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.clause import ExtractedClause
from lexguard_shared.schemas.risk import RiskCategory, RiskFlag

from lexguard_risk.llm.models import LLMRiskAssessment
from lexguard_risk.llm.prompts import RISK_ANALYSIS_SYSTEM, RISK_ANALYSIS_USER
from lexguard_risk.rules.base import RuleHit

logger = logging.getLogger(__name__)


class LLMRiskAnalyzer:
    """Enriches rule-based hits with LLM legal reasoning."""

    def __init__(
        self, ai_client: AIClient | None = None, settings: AISettings | None = None
    ) -> None:
        self._ai = ai_client or AIClient(settings)

    async def enrich(
        self,
        clause: ExtractedClause,
        flag: RiskFlag,
        category: RiskCategory,
        hits: list[RuleHit],
    ) -> LLMRiskAssessment:
        evidence_lines = "\n".join(
            f'- [{h.rule_id}] {h.rule_name}: "{h.matched_text}" (weight={h.weight:.2f})'
            for h in hits
        )
        prompt = RISK_ANALYSIS_USER.format(
            title=clause.title,
            clause_type=clause.clause_type.value,
            text=clause.text,
            flag=flag.value,
            category=category.value,
            evidence=evidence_lines or "No specific pattern matches.",
            obligations="; ".join(clause.obligations) or "None",
            penalties="; ".join(clause.penalties) or "None",
            financial_liabilities="; ".join(clause.financial_liabilities) or "None",
        )
        return await self._ai.gemini.generate_structured(
            prompt=prompt,
            response_model=LLMRiskAssessment,
            system_instruction=RISK_ANALYSIS_SYSTEM,
        )
