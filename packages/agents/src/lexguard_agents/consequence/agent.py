import asyncio
import logging

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.clause import ClauseExtractionResult, ExtractedClause
from lexguard_shared.schemas.consequence import ConsequenceScenario, ConsequenceSimulationResult
from lexguard_shared.schemas.risk import DocumentRiskAnalysis, RiskFinding

from lexguard_agents.consequence.models import ScenariosResponse
from lexguard_agents.consequence.prompts import CONSEQUENCE_SYSTEM, CONSEQUENCE_USER
from lexguard_agents.consequence.templates import template_scenarios

logger = logging.getLogger(__name__)

_MIN_FINDING_SEVERITY = 25.0


class ConsequenceSimulationAgent:
    """Simulates real-world consequences of risky clauses."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        settings: AISettings | None = None,
    ) -> None:
        self._ai = ai_client or AIClient(settings)
        self._settings = settings or AISettings()
        self._semaphore = asyncio.Semaphore(self._settings.gemini_max_concurrency)

    async def simulate(
        self,
        risk_analysis: DocumentRiskAnalysis,
        clauses: ClauseExtractionResult,
    ) -> ConsequenceSimulationResult:
        clause_map = {c.clause_id: c for c in clauses.clauses}
        findings = [
            f for f in risk_analysis.findings if f.severity_score >= _MIN_FINDING_SEVERITY
        ]

        if not findings:
            return ConsequenceSimulationResult(
                document_id=risk_analysis.document_id,
                scenarios=[],
                summary="No significant risks identified — no consequence scenarios generated.",
            )

        tasks = [
            self._simulate_finding(finding, clause_map.get(finding.clause_id))
            for finding in findings
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_scenarios: list[ConsequenceScenario] = []
        for finding, result in zip(findings, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Consequence simulation failed for finding %s: %s",
                    finding.finding_id,
                    result,
                )
                clause = clause_map.get(finding.clause_id)
                if clause:
                    all_scenarios.extend(template_scenarios(finding, clause))
                continue
            all_scenarios.extend(result)

        all_scenarios.sort(key=lambda s: s.severity * s.likelihood / 100, reverse=True)
        summary = self._build_summary(all_scenarios)

        return ConsequenceSimulationResult(
            document_id=risk_analysis.document_id,
            scenarios=all_scenarios,
            summary=summary,
        )

    async def _simulate_finding(
        self,
        finding: RiskFinding,
        clause: ExtractedClause | None,
    ) -> list[ConsequenceScenario]:
        if clause is None:
            logger.warning("Clause %s not found for finding %s", finding.clause_id, finding.finding_id)
            return []

        async with self._semaphore:
            try:
                return await self._llm_scenarios(finding, clause)
            except Exception as exc:
                logger.warning("LLM consequence failed, using templates: %s", exc)
                return template_scenarios(finding, clause)

    async def _llm_scenarios(
        self,
        finding: RiskFinding,
        clause: ExtractedClause,
    ) -> list[ConsequenceScenario]:
        parties = ", ".join(f"{p.party} ({p.role})" for p in finding.affected_parties) or "unspecified"
        prompt = CONSEQUENCE_USER.format(
            clause_title=clause.title,
            clause_text=clause.text,
            risk_category=finding.category.value,
            risk_flag=finding.flag.value,
            risk_explanation=finding.plain_language_explanation,
            legal_reasoning=finding.legal_reasoning,
            affected_parties=parties,
        )
        response = await self._ai.gemini.generate_structured(
            prompt=prompt,
            response_model=ScenariosResponse,
            system_instruction=CONSEQUENCE_SYSTEM,
        )

        return [
            ConsequenceScenario(
                scenario=s.scenario,
                impact=s.impact,
                likelihood=s.likelihood,
                severity=s.severity,
                explanation=s.explanation,
                clause_id=clause.clause_id,
                clause_title=clause.title,
                finding_id=finding.finding_id,
            )
            for s in response.scenarios
        ]

    def _build_summary(self, scenarios: list[ConsequenceScenario]) -> str:
        if not scenarios:
            return "No consequence scenarios generated."

        top = scenarios[0]
        high_impact = [s for s in scenarios if s.severity >= 70 and s.likelihood >= 50]
        return (
            f"Generated {len(scenarios)} consequence scenario(s). "
            f"Highest combined risk: '{top.scenario}' "
            f"(severity {top.severity:.0f}, likelihood {top.likelihood:.0f}). "
            f"{len(high_impact)} scenario(s) rated high severity and likely."
        )
