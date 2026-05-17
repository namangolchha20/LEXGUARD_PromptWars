import logging

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.benchmark import DocumentBenchmarkResult
from lexguard_shared.schemas.clause import ClauseExtractionResult
from lexguard_shared.schemas.consequence import ConsequenceSimulationResult
from lexguard_shared.schemas.negotiation import (
    NegotiationPriority,
    NegotiationRecommendation,
    NegotiationResult,
)
from lexguard_shared.schemas.risk import DocumentRiskAnalysis

from lexguard_agents.negotiation.models import NegotiationLLMResponse
from lexguard_agents.negotiation.prompts import NEGOTIATION_SYSTEM, NEGOTIATION_USER

logger = logging.getLogger(__name__)


class NegotiationAgent:
    """Aggregates analysis outputs into prioritized negotiation recommendations."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        settings: AISettings | None = None,
    ) -> None:
        self._ai = ai_client or AIClient(settings)

    async def negotiate(
        self,
        document_id: str,
        clauses: ClauseExtractionResult,
        risk: DocumentRiskAnalysis,
        benchmarks: DocumentBenchmarkResult,
        consequences: ConsequenceSimulationResult | None = None,
    ) -> NegotiationResult:
        try:
            return await self._llm_negotiate(document_id, risk, benchmarks, consequences)
        except Exception as exc:
            logger.warning("LLM negotiation failed, using rule-based fallback: %s", exc)
            return self._fallback_negotiate(document_id, risk, benchmarks, consequences)

    async def _llm_negotiate(
        self,
        document_id: str,
        risk: DocumentRiskAnalysis,
        benchmarks: DocumentBenchmarkResult,
        consequences: ConsequenceSimulationResult | None,
    ) -> NegotiationResult:
        risk_findings = "\n".join(
            f"- [{f.severity_score:.0f}] {f.clause_title}: {f.plain_language_explanation}"
            for f in risk.findings[:8]
        )
        benchmark_lines = "\n".join(
            f"- {c.metric}: {c.contract_value} vs {c.benchmark_range} "
            f"(deviation {c.deviation_score:.0f}) — {c.negotiation_recommendation}"
            for c in benchmarks.comparisons[:8]
        )
        consequence_lines = (
            "\n".join(
                f"- {s.scenario}: {s.impact}"
                for s in (consequences.scenarios[:6] if consequences else [])
            )
            or "None generated"
        )

        prompt = NEGOTIATION_USER.format(
            document_id=document_id,
            risk_summary=risk.summary,
            risk_findings=risk_findings or "None",
            consequences=consequence_lines,
            benchmarks=benchmark_lines or "None",
        )
        response = await self._ai.gemini.generate_structured(
            prompt=prompt,
            response_model=NegotiationLLMResponse,
            system_instruction=NEGOTIATION_SYSTEM,
        )
        return NegotiationResult(
            document_id=document_id,
            summary=response.summary,
            overall_leverage=response.overall_leverage,
            recommendations=response.recommendations,
        )

    def _fallback_negotiate(
        self,
        document_id: str,
        risk: DocumentRiskAnalysis,
        benchmarks: DocumentBenchmarkResult,
        consequences: ConsequenceSimulationResult | None,
    ) -> NegotiationResult:
        recommendations: list[NegotiationRecommendation] = []

        for comp in sorted(benchmarks.comparisons, key=lambda c: -c.deviation_score)[:5]:
            priority = (
                NegotiationPriority.CRITICAL
                if comp.deviation_score >= 70
                else NegotiationPriority.HIGH
                if comp.deviation_score >= 40
                else NegotiationPriority.MEDIUM
            )
            recommendations.append(
                NegotiationRecommendation(
                    topic=comp.metric,
                    priority=priority,
                    current_term=comp.contract_value,
                    suggested_term=comp.benchmark_range,
                    rationale=comp.negotiation_recommendation,
                    clause_id=comp.clause_id,
                )
            )

        for finding in sorted(risk.findings, key=lambda f: -f.severity_score)[:3]:
            recommendations.append(
                NegotiationRecommendation(
                    topic=finding.flag.value,
                    priority=NegotiationPriority.HIGH,
                    current_term=finding.clause_title,
                    suggested_term="Align with industry standard / mutual terms",
                    rationale=finding.plain_language_explanation,
                    clause_id=finding.clause_id,
                )
            )

        leverage = "weak" if risk.overall_severity_score >= 60 else "moderate"
        return NegotiationResult(
            document_id=document_id,
            summary=f"Identified {len(recommendations)} negotiation points from risk and benchmark analysis.",
            overall_leverage=leverage,
            recommendations=recommendations,
        )
