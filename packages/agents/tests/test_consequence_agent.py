from unittest.mock import AsyncMock, MagicMock

import pytest
from lexguard_agents.consequence.agent import ConsequenceSimulationAgent
from lexguard_agents.consequence.models import ScenarioOutput, ScenariosResponse
from lexguard_shared.schemas.clause import ClauseExtractionResult, ClauseType, ExtractedClause
from lexguard_shared.schemas.risk import DocumentRiskAnalysis, RiskCategory, RiskFinding, RiskFlag


@pytest.fixture
def mock_agent() -> ConsequenceSimulationAgent:
    client = MagicMock()
    client.gemini.generate_structured = AsyncMock(
        return_value=ScenariosResponse(
            scenarios=[
                ScenarioOutput(
                    scenario="Uncapped indemnification costs",
                    impact="You may pay unlimited legal fees and damages.",
                    likelihood=70.0,
                    severity=85.0,
                    explanation="The indemnity clause has no cap on your financial exposure.",
                ),
            ]
        )
    )
    return ConsequenceSimulationAgent(ai_client=client)


@pytest.fixture
def risk_and_clauses() -> tuple[DocumentRiskAnalysis, ClauseExtractionResult]:
    clause = ExtractedClause(
        clause_id="c1",
        clause_type=ClauseType.INDEMNIFICATION,
        title="Indemnification",
        text="Licensee shall indemnify Licensor for all claims without limitation.",
        confidence=0.9,
    )
    finding = RiskFinding(
        finding_id="f1",
        clause_id="c1",
        clause_title="Indemnification",
        category=RiskCategory.FINANCIAL_RISK,
        flag=RiskFlag.HIDDEN_LIABILITY,
        severity_score=80.0,
        confidence=0.9,
        plain_language_explanation="Unlimited financial exposure.",
        legal_reasoning="No cap on indemnification.",
        affected_parties=[],
        rule_evidence=[],
    )
    return (
        DocumentRiskAnalysis(
            document_id="doc-1",
            overall_severity_score=80.0,
            overall_confidence=0.9,
            summary="High risk",
            findings=[finding],
        ),
        ClauseExtractionResult(document_id="doc-1", clauses=[clause]),
    )


@pytest.mark.asyncio
async def test_simulate_generates_scenarios(
    mock_agent: ConsequenceSimulationAgent,
    risk_and_clauses: tuple[DocumentRiskAnalysis, ClauseExtractionResult],
) -> None:
    risk, clauses = risk_and_clauses
    result = await mock_agent.simulate(risk, clauses)

    assert result.document_id == "doc-1"
    assert len(result.scenarios) == 1
    scenario = result.scenarios[0]
    assert scenario.scenario
    assert scenario.impact
    assert 0 <= scenario.likelihood <= 100
    assert 0 <= scenario.severity <= 100
    assert scenario.explanation
    assert scenario.clause_id == "c1"
    assert scenario.finding_id == "f1"


@pytest.mark.asyncio
async def test_template_fallback_on_llm_failure(
    risk_and_clauses: tuple[DocumentRiskAnalysis, ClauseExtractionResult],
) -> None:
    client = MagicMock()
    client.gemini.generate_structured = AsyncMock(side_effect=RuntimeError("API down"))
    agent = ConsequenceSimulationAgent(ai_client=client)

    risk, clauses = risk_and_clauses
    result = await agent.simulate(risk, clauses)

    assert len(result.scenarios) >= 1
    assert result.scenarios[0].clause_id == "c1"
