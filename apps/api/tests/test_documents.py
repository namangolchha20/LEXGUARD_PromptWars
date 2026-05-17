import io
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from lexguard_api.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("INGESTION_TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("INGESTION_OUTPUT_DIR", str(tmp_path / "parsed"))
    monkeypatch.setenv("INGESTION_WORKER_CONCURRENCY", "1")

    from lexguard_api import dependencies

    dependencies.get_ingestion_settings.cache_clear()
    dependencies.get_document_storage.cache_clear()
    dependencies.get_ingestion_pipeline.cache_clear()
    dependencies._job_queue = None

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    dependencies.get_ingestion_settings.cache_clear()
    dependencies.get_document_storage.cache_clear()
    dependencies.get_ingestion_pipeline.cache_clear()
    dependencies._job_queue = None


def _make_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test Section", fontsize=16)
    page.insert_text((72, 110), "Test body content.", fontsize=12)
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


def test_upload_pdf_returns_202(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert "document_id" in data


def test_upload_rejects_invalid_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415


def test_get_document_status(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
    )
    document_id = upload.json()["document_id"]

    import time

    for _ in range(30):
        status = client.get(f"/api/v1/documents/{document_id}")
        if status.status_code == 200 and status.json().get("status") in ("completed", "failed"):
            break
        time.sleep(0.2)

    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert status.json()["result"] is not None
    assert len(status.json()["result"]["sections"]) >= 1
