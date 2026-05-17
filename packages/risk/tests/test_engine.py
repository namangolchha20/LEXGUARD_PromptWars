from unittest.mock import AsyncMock, MagicMock

import pytest
from lexguard_risk.engine import RiskAnalysisEngine
from lexguard_risk.llm.models import LLMRiskAssessment
from lexguard_shared.schemas.clause import ClauseExtractionResult, ClauseType, ExtractedClause
from lexguard_shared.schemas.risk import AffectedParty, RiskCategory, RiskFlag


@pytest.fixture
def risky_clauses() -> ClauseExtractionResult:
    return ClauseExtractionResult(
        document_id="doc-risk",
        clauses=[
            ExtractedClause(
                clause_id="c1",
                clause_type=ClauseType.INDEMNIFICATION,
                title="Indemnification",
                text=(
                    "Licensee shall indemnify and hold harmless Licensor from any claims "
                    "at Licensee's sole cost, including attorneys fees and consequential damages "
                    "without limitation."
                ),
                obligations=["Licensee shall indemnify Licensor"],
                penalties=["All damages including consequential damages"],
                financial_liabilities=["Unlimited indemnification costs"],
                confidence=0.9,
            ),
            ExtractedClause(
                clause_id="c2",
                clause_type=ClauseType.NON_COMPETE,
                title="Non-Compete",
                text=(
                    "Employee shall not engage in any business worldwide for a perpetual period. "
                    "Employee shall comply with all restrictions at employer sole discretion."
                ),
                obligations=["Employee shall not compete worldwide"],
                confidence=0.85,
            ),
        ],
    )


@pytest.fixture
def mock_engine() -> RiskAnalysisEngine:
    mock_ai = MagicMock()
    mock_ai.gemini.generate_structured = AsyncMock(
        return_value=LLMRiskAssessment(
            category=RiskCategory.FINANCIAL_RISK,
            flag=RiskFlag.HIDDEN_LIABILITY,
            severity_score=78.0,
            confidence=0.88,
            plain_language_explanation="You may face unlimited financial exposure.",
            legal_reasoning="Broad indemnification without caps creates asymmetric liability.",
            affected_parties=[
                AffectedParty(
                    party="licensee",
                    role="indemnitor",
                    impact="Bears unlimited defense costs",
                    risk_level="high",
                ),
            ],
        )
    )
    return RiskAnalysisEngine(ai_client=mock_ai)


@pytest.mark.asyncio
async def test_analyze_produces_findings(
    mock_engine: RiskAnalysisEngine,
    risky_clauses: ClauseExtractionResult,
) -> None:
    result = await mock_engine.analyze(risky_clauses)

    assert result.document_id == "doc-risk"
    assert len(result.findings) >= 2
    assert result.overall_severity_score > 0
    assert result.overall_confidence > 0
    assert len(result.category_scores) >= 1

    finding = result.findings[0]
    assert finding.severity_score > 0
    assert finding.plain_language_explanation
    assert finding.legal_reasoning
    assert len(finding.rule_evidence) >= 1
    assert finding.flag in RiskFlag
