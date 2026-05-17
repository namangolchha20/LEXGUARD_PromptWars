# ruff: noqa: B008 — FastAPI Depends defaults are intentional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from lexguard_agents import AgentRegistry, ClauseStorage, ConsequenceStorage
from lexguard_risk import RiskStorage
from lexguard_shared.schemas.consequence import (
    ConsequenceSimulationJobResponse,
    ConsequenceSimulationResult,
)

from lexguard_api.dependencies import (
    get_agent_registry,
    get_clause_storage,
    get_consequence_storage,
    get_risk_storage,
)

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)


@router.post(
    "/{document_id}/consequences/simulate",
    response_model=ConsequenceSimulationJobResponse,
    status_code=status.HTTP_200_OK,
)
async def simulate_consequences(
    document_id: str,
    clause_storage: ClauseStorage = Depends(get_clause_storage),
    risk_storage: RiskStorage = Depends(get_risk_storage),
    consequence_storage: ConsequenceStorage = Depends(get_consequence_storage),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> ConsequenceSimulationJobResponse:
    clauses = await clause_storage.load(document_id)
    if clauses is None:
        raise HTTPException(
            status_code=404,
            detail="Clauses not found. Run POST /clauses/extract first.",
        )

    risk = await risk_storage.load(document_id)
    if risk is None:
        raise HTTPException(
            status_code=404,
            detail="Risk analysis not found. Run POST /risk/analyze first.",
        )

    agent = registry.consequence_simulation
    result = await agent.simulate(risk, clauses)
    await consequence_storage.save(result)

    return ConsequenceSimulationJobResponse(
        document_id=document_id,
        status="completed",
        scenario_count=len(result.scenarios),
        message=f"Generated {len(result.scenarios)} consequence scenario(s)",
    )


@router.get("/{document_id}/consequences", response_model=ConsequenceSimulationResult)
async def get_consequences(
    document_id: str,
    consequence_storage: ConsequenceStorage = Depends(get_consequence_storage),
) -> ConsequenceSimulationResult:
    result = await consequence_storage.load(document_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Consequence simulation not found. Run POST /consequences/simulate first.",
        )
    return result
