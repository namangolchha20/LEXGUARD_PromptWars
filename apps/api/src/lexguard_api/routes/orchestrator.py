# ruff: noqa: B008 — FastAPI Depends defaults are intentional
import logging
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from lexguard_orchestrator import PipelineOrchestrator
from lexguard_orchestrator.state import StateManager
from lexguard_shared.schemas.orchestrator import (
    AgentName,
    AnalysisState,
    PipelineRunResponse,
    PipelineStatus,
)

from lexguard_api.dependencies import get_orchestrator, get_state_manager

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024


@router.post(
    "/analyze",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_document_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
    state_manager: StateManager = Depends(get_state_manager),
) -> PipelineRunResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await _read_file(file)
    document_id = uuid4().hex

    state = await state_manager.create_run(document_id, list(AgentName))
    background_tasks.add_task(
        _run_pipeline_background,
        orchestrator,
        document_id,
        content,
        file.filename,
        False,
    )

    return PipelineRunResponse(
        document_id=document_id,
        run_id=state.run_id,
        status=PipelineStatus.PENDING,
        message="Analysis pipeline queued",
    )


@router.post(
    "/{document_id}/analyze",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_existing_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
    state_manager: StateManager = Depends(get_state_manager),
) -> PipelineRunResponse:
    state = await state_manager.create_run(document_id, list(AgentName))
    background_tasks.add_task(
        _run_pipeline_background,
        orchestrator,
        document_id,
        None,
        None,
        True,
    )

    return PipelineRunResponse(
        document_id=document_id,
        run_id=state.run_id,
        status=PipelineStatus.PENDING,
        message="Analysis pipeline queued (existing document)",
    )


@router.get("/{document_id}/analysis", response_model=AnalysisState)
async def get_analysis_state(
    document_id: str,
    state_manager: StateManager = Depends(get_state_manager),
) -> AnalysisState:
    state = await state_manager.load(document_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Analysis state not found")
    return state


async def _run_pipeline_background(
    orchestrator: PipelineOrchestrator,
    document_id: str,
    file_bytes: bytes | None,
    filename: str | None,
    skip_ingestion: bool,
) -> None:
    try:
        await orchestrator.run_pipeline(
            document_id,
            file_bytes=file_bytes,
            filename=filename,
            skip_ingestion=skip_ingestion,
        )
    except Exception as exc:
        logger.exception("Background pipeline failed for %s: %s", document_id, exc)


async def _read_file(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    while chunk := await file.read(CHUNK_SIZE):
        chunks.append(chunk)
    return b"".join(chunks)
