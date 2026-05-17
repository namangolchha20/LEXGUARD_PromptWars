# ruff: noqa: B008 — FastAPI Depends defaults are intentional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from lexguard_agents import AgentRegistry, ClauseStorage
from lexguard_ingestion.storage import DocumentStorage
from lexguard_shared.schemas.clause import (
    ClauseExtractionJobResponse,
    ClauseExtractionResult,
)
from lexguard_shared.schemas.document import IngestionStatus

from lexguard_api.dependencies import (
    get_agent_registry,
    get_clause_storage,
    get_document_storage,
)

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)


@router.post(
    "/{document_id}/clauses/extract",
    response_model=ClauseExtractionJobResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_clauses(
    document_id: str,
    document_storage: DocumentStorage = Depends(get_document_storage),
    clause_storage: ClauseStorage = Depends(get_clause_storage),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> ClauseExtractionJobResponse:
    parsed = await _require_parsed_document(document_id, document_storage)

    agent = registry.clause_extraction
    result = await agent.extract(parsed)
    await clause_storage.save(result)

    return ClauseExtractionJobResponse(
        document_id=document_id,
        status="completed",
        clause_count=len(result.clauses),
        message=f"Extracted {len(result.clauses)} clauses",
    )


@router.get("/{document_id}/clauses", response_model=ClauseExtractionResult)
async def get_clauses(
    document_id: str,
    clause_storage: ClauseStorage = Depends(get_clause_storage),
) -> ClauseExtractionResult:
    result = await clause_storage.load(document_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Clause extraction not found. Run POST /clauses/extract first.",
        )
    return result


async def _require_parsed_document(document_id: str, storage: DocumentStorage):
    status_response = await storage.get_status(document_id)
    if status_response is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if status_response.status != IngestionStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Document ingestion not complete (status: {status_response.status})",
        )

    parsed = await storage.get_result(document_id)
    if parsed is None:
        raise HTTPException(status_code=404, detail="Parsed document not found")
    return parsed
