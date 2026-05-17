# ruff: noqa: B008 — FastAPI Depends/File defaults are intentional
import logging
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from lexguard_ingestion import (
    FileTooLargeError,
    IngestionJob,
    IngestionJobQueue,
    IngestionSettings,
    UnsupportedFormatError,
    ValidationError,
)
from lexguard_ingestion.pipeline import IngestionPipeline
from lexguard_ingestion.storage import DocumentStorage
from lexguard_ingestion.validators import validate_upload
from lexguard_shared.schemas.document import (
    IngestionJobResponse,
    IngestionStatus,
    IngestionStatusResponse,
    ParsedDocument,
)

from lexguard_api.dependencies import get_document_storage, get_ingestion_settings, get_job_queue

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024


@router.post(
    "/upload",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    settings: IngestionSettings = Depends(get_ingestion_settings),
    storage: DocumentStorage = Depends(get_document_storage),
    queue: IngestionJobQueue = Depends(get_job_queue),
) -> IngestionJobResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await _read_upload(file, settings)
    doc_format = _validate(file.filename, len(content), settings)

    document_id = IngestionPipeline.new_document_id()
    settings.ingestion_temp_dir.mkdir(parents=True, exist_ok=True)
    staging_path = (
        settings.ingestion_temp_dir / f"{document_id}{Path(file.filename).suffix.lower()}"
    )

    try:
        async with aiofiles.open(staging_path, "wb") as f:
            await f.write(content)

        await storage.update_status(document_id, IngestionStatus.PENDING)
        await queue.enqueue(
            IngestionJob(
                document_id=document_id,
                file_path=staging_path,
                format=doc_format,
            )
        )
    except Exception:
        staging_path.unlink(missing_ok=True)
        raise

    return IngestionJobResponse(
        document_id=document_id,
        status=IngestionStatus.PENDING,
        message="Document queued for processing",
    )


@router.get("/{document_id}", response_model=IngestionStatusResponse)
async def get_document(
    document_id: str,
    storage: DocumentStorage = Depends(get_document_storage),
) -> IngestionStatusResponse:
    status_response = await storage.get_status(document_id)
    if status_response is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if status_response.status == IngestionStatus.COMPLETED and status_response.result is None:
        result = await storage.get_result(document_id)
        if result:
            status_response = IngestionStatusResponse(
                document_id=document_id,
                status=status_response.status,
                result=result,
            )

    return status_response


@router.get("/{document_id}/result", response_model=ParsedDocument)
async def get_document_result(
    document_id: str,
    storage: DocumentStorage = Depends(get_document_storage),
) -> ParsedDocument:
    status_response = await storage.get_status(document_id)
    if status_response is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if status_response.status == IngestionStatus.FAILED:
        raise HTTPException(
            status_code=422,
            detail=status_response.error or "Document processing failed",
        )

    if status_response.status != IngestionStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready (status: {status_response.status})",
        )

    result = await storage.get_result(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Parsed result not found")

    return result


async def _read_upload(file: UploadFile, settings: IngestionSettings) -> bytes:
    chunks: list[bytes] = []
    total = 0

    while chunk := await file.read(CHUNK_SIZE):
        total += len(chunk)
        if total > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {settings.ingestion_max_file_size_mb} MB",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _validate(filename: str, size: int, settings: IngestionSettings):
    try:
        return validate_upload(filename, size, settings)
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
