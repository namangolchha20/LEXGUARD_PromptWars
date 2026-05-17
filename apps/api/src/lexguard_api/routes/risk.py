# ruff: noqa: B008 — FastAPI Depends defaults are intentional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from lexguard_agents import ClauseStorage
from lexguard_risk import RiskAnalysisEngine, RiskStorage
from lexguard_shared.schemas.risk import DocumentRiskAnalysis, RiskAnalysisJobResponse

from lexguard_api.dependencies import (
    get_clause_storage,
    get_risk_engine,
    get_risk_storage,
)

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)


@router.post(
    "/{document_id}/risk/analyze",
    response_model=RiskAnalysisJobResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_risk(
    document_id: str,
    clause_storage: ClauseStorage = Depends(get_clause_storage),
    risk_engine: RiskAnalysisEngine = Depends(get_risk_engine),
    risk_storage: RiskStorage = Depends(get_risk_storage),
) -> RiskAnalysisJobResponse:
    clauses = await clause_storage.load(document_id)
    if clauses is None:
        raise HTTPException(
            status_code=404,
            detail="Clauses not found. Run POST /clauses/extract first.",
        )

    if not clauses.clauses:
        raise HTTPException(status_code=422, detail="No clauses available for risk analysis")

    analysis = await risk_engine.analyze(clauses)
    await risk_storage.save(analysis)

    return RiskAnalysisJobResponse(
        document_id=document_id,
        status="completed",
        finding_count=len(analysis.findings),
        overall_severity_score=analysis.overall_severity_score,
        message=f"Identified {len(analysis.findings)} risk findings",
    )


@router.get("/{document_id}/risk", response_model=DocumentRiskAnalysis)
async def get_risk_analysis(
    document_id: str,
    risk_storage: RiskStorage = Depends(get_risk_storage),
) -> DocumentRiskAnalysis:
    analysis = await risk_storage.load(document_id)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Risk analysis not found. Run POST /risk/analyze first.",
        )
    return analysis
