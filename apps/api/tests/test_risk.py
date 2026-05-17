import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import fitz
import pytest
from fastapi.testclient import TestClient
from lexguard_agents.clause.models import ClauseAnalysisResponse
from lexguard_risk.llm.models import LLMRiskAssessment
from lexguard_shared.schemas.clause import ClauseType
from lexguard_shared.schemas.risk import AffectedParty, RiskCategory, RiskFlag


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("INGESTION_TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("INGESTION_OUTPUT_DIR", str(tmp_path / "parsed"))
    monkeypatch.setenv("CLAUSE_OUTPUT_DIR", str(tmp_path / "clauses"))
    monkeypatch.setenv("RISK_OUTPUT_DIR", str(tmp_path / "risk"))
    monkeypatch.setenv("INGESTION_WORKER_CONCURRENCY", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from lexguard_api import dependencies

    caches = [
        dependencies.get_ingestion_settings,
        dependencies.get_document_storage,
        dependencies.get_clause_storage,
        dependencies.get_risk_storage,
        dependencies.get_risk_settings,
        dependencies.get_risk_engine,
        dependencies.get_ingestion_pipeline,
        dependencies.get_ai_settings,
        dependencies.get_agent_settings,
        dependencies.get_agent_registry,
    ]
    for fn in caches:
        fn.cache_clear()
    dependencies._job_queue = None

    clause_response = ClauseAnalysisResponse(
        clause_type=ClauseType.INDEMNIFICATION,
        title="Indemnification",
        obligations=["Indemnify licensor"],
        penalties=["All damages"],
        financial_liabilities=["Unlimited costs"],
        confidence=0.9,
    )
    risk_response = LLMRiskAssessment(
        category=RiskCategory.FINANCIAL_RISK,
        flag=RiskFlag.HIDDEN_LIABILITY,
        severity_score=75.0,
        confidence=0.85,
        plain_language_explanation="Significant financial exposure.",
        legal_reasoning="Broad indemnity creates uncapped liability.",
        affected_parties=[
            AffectedParty(
                party="licensee", role="indemnitor", impact="High costs", risk_level="high"
            ),
        ],
    )

    with (
        patch(
            "lexguard_ai.gemini.GeminiClient.generate_structured", new_callable=AsyncMock
        ) as mock_gen,
    ):
        mock_gen.side_effect = [clause_response, risk_response, risk_response]
        from lexguard_api.main import create_app

        with TestClient(create_app()) as test_client:
            yield test_client

    for fn in caches:
        fn.cache_clear()
    dependencies._job_queue = None


def _make_risky_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Indemnification", fontsize=16)
    page.insert_text(
        (72, 110),
        "Licensee shall indemnify and hold harmless Licensor from any claims at sole discretion "
        "including attorneys fees and consequential damages without limitation.",
        fontsize=12,
    )
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def test_risk_analysis_flow(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.pdf", _make_risky_pdf(), "application/pdf")},
    )
    document_id = upload.json()["document_id"]

    import time

    for _ in range(30):
        if client.get(f"/api/v1/documents/{document_id}").json()["status"] == "completed":
            break
        time.sleep(0.2)

    client.post(f"/api/v1/documents/{document_id}/clauses/extract")

    analyze = client.post(f"/api/v1/documents/{document_id}/risk/analyze")
    assert analyze.status_code == 200
    assert analyze.json()["finding_count"] >= 1

    risk = client.get(f"/api/v1/documents/{document_id}/risk")
    assert risk.status_code == 200
    data = risk.json()
    assert data["overall_severity_score"] > 0
    assert len(data["findings"]) >= 1
    assert data["findings"][0]["rule_evidence"]
