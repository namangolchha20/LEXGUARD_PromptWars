from unittest.mock import AsyncMock, MagicMock

import pytest
from lexguard_benchmark.engine import BenchmarkComparisonEngine
from lexguard_benchmark.llm.models import BenchmarkExplanationResponse
from lexguard_shared.schemas.benchmark import FairnessLevel
from lexguard_shared.schemas.clause import ClauseExtractionResult, ClauseType, ExtractedClause


@pytest.fixture
def termination_clause() -> ClauseExtractionResult:
    return ClauseExtractionResult(
        document_id="doc-bench",
        clauses=[
            ExtractedClause(
                clause_id="c1",
                clause_type=ClauseType.TERMINATION,
                title="Termination",
                text="Either party may terminate with one hundred eighty (180) days prior written notice.",
                confidence=0.9,
            ),
        ],
    )


@pytest.fixture
def mock_engine() -> BenchmarkComparisonEngine:
    client = MagicMock()
    client.gemini.generate_structured = AsyncMock(
        return_value=BenchmarkExplanationResponse(
            benchmark_summary="Typical notice period: 30–60 days",
            comparative_explanation="180 days is 3x longer than industry standard.",
            negotiation_recommendation="Request 30–60 days mutual notice.",
            fairness_assessment=FairnessLevel.UNFAVORABLE,
            contract_value="180 days",
        )
    )
    return BenchmarkComparisonEngine(ai_client=client)


@pytest.mark.asyncio
async def test_compare_detects_notice_period_outlier(
    mock_engine: BenchmarkComparisonEngine,
    termination_clause: ClauseExtractionResult,
) -> None:
    result = await mock_engine.compare(termination_clause)

    assert result.document_id == "doc-bench"
    assert len(result.comparisons) >= 1
    notice = next((c for c in result.comparisons if c.metric == "notice_period_days"), None)
    assert notice is not None
    assert notice.deviation_score >= 30
    assert notice.contract_value == "180 days"
    assert notice.fairness_assessment == FairnessLevel.UNFAVORABLE
    assert "180" in notice.contract_value or "180" in notice.comparative_explanation
