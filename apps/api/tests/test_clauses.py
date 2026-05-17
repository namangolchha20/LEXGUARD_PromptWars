import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import fitz
import pytest
from fastapi.testclient import TestClient
from lexguard_agents.clause.models import ClauseAnalysisResponse
from lexguard_shared.schemas.clause import ClauseType


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("INGESTION_TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("INGESTION_OUTPUT_DIR", str(tmp_path / "parsed"))
    monkeypatch.setenv("CLAUSE_OUTPUT_DIR", str(tmp_path / "clauses"))
    monkeypatch.setenv("INGESTION_WORKER_CONCURRENCY", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from lexguard_api import dependencies

    for fn in (
        dependencies.get_ingestion_settings,
        dependencies.get_document_storage,
        dependencies.get_clause_storage,
        dependencies.get_ingestion_pipeline,
        dependencies.get_ai_settings,
        dependencies.get_agent_settings,
        dependencies.get_agent_registry,
    ):
        fn.cache_clear()
    dependencies._job_queue = None

    mock_analysis = ClauseAnalysisResponse(
        clause_type=ClauseType.TERMINATION,
        title="Termination",
        obligations=["Provide 30 days written notice"],
        penalties=[],
        rights=["Either party may terminate"],
        durations=["30 days notice period"],
        financial_liabilities=[],
        confidence=0.88,
    )

    with patch(
        "lexguard_ai.gemini.GeminiClient.generate_structured", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = mock_analysis
        from lexguard_api.main import create_app

        with TestClient(create_app()) as test_client:
            yield test_client

    for fn in (
        dependencies.get_ingestion_settings,
        dependencies.get_document_storage,
        dependencies.get_clause_storage,
        dependencies.get_ingestion_pipeline,
        dependencies.get_ai_settings,
        dependencies.get_agent_settings,
        dependencies.get_agent_registry,
    ):
        fn.cache_clear()
    dependencies._job_queue = None


def _make_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Termination", fontsize=16)
    page.insert_text(
        (72, 110),
        "Either party may terminate this agreement with thirty (30) days written notice.",
        fontsize=12,
    )
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def test_extract_clauses_flow(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.pdf", _make_pdf_bytes(), "application/pdf")},
    )
    document_id = upload.json()["document_id"]

    import time

    for _ in range(30):
        status = client.get(f"/api/v1/documents/{document_id}")
        if status.json()["status"] == "completed":
            break
        time.sleep(0.2)

    extract = client.post(f"/api/v1/documents/{document_id}/clauses/extract")
    assert extract.status_code == 200
    assert extract.json()["clause_count"] >= 1

    clauses = client.get(f"/api/v1/documents/{document_id}/clauses")
    assert clauses.status_code == 200
    data = clauses.json()
    assert data["document_id"] == document_id
    assert len(data["clauses"]) >= 1
    assert "confidence" in data["clauses"][0]
