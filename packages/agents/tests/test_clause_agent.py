from unittest.mock import AsyncMock, MagicMock

import pytest
from lexguard_agents.clause.agent import ClauseExtractionAgent
from lexguard_agents.clause.models import ClauseAnalysisResponse
from lexguard_shared.schemas.clause import ClauseType
from lexguard_shared.schemas.document import DocumentSection, ParsedDocument


@pytest.fixture
def mock_ai_client() -> MagicMock:
    client = MagicMock()
    client.gemini = MagicMock()
    client.gemini.generate_structured = AsyncMock(
        return_value=ClauseAnalysisResponse(
            clause_type=ClauseType.CONFIDENTIALITY,
            title="Confidentiality",
            obligations=["Party shall not disclose confidential information"],
            penalties=["Injunctive relief available for breach"],
            rights=["Right to use information for permitted purpose"],
            durations=["Obligation survives for 3 years after termination"],
            financial_liabilities=[],
            confidence=0.92,
        )
    )
    return client


@pytest.fixture
def sample_document() -> ParsedDocument:
    return ParsedDocument(
        document_id="doc-test",
        sections=[
            DocumentSection(
                title="Confidentiality",
                content=(
                    "The receiving party shall not disclose any confidential information. "
                    "Breach may result in injunctive relief. This obligation survives "
                    "for three (3) years after termination."
                ),
                page=1,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_extract_clauses(
    mock_ai_client: MagicMock,
    sample_document: ParsedDocument,
) -> None:
    agent = ClauseExtractionAgent(ai_client=mock_ai_client)
    result = await agent.extract(sample_document)

    assert result.document_id == "doc-test"
    assert len(result.clauses) >= 1
    clause = result.clauses[0]
    assert clause.clause_type == ClauseType.CONFIDENTIALITY
    assert clause.confidence >= 0.9
    assert len(clause.obligations) >= 1
    assert len(clause.penalties) >= 1
    assert len(clause.rights) >= 1
    assert len(clause.durations) >= 1
