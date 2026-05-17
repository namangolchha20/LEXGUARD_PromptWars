# ruff: noqa: B008 — FastAPI Depends defaults are intentional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from lexguard_agents import ClauseStorage
from lexguard_benchmark import BenchmarkComparisonEngine, BenchmarkStorage
from lexguard_shared.schemas.benchmark import BenchmarkJobResponse, DocumentBenchmarkResult

from lexguard_api.dependencies import (
    get_benchmark_engine,
    get_benchmark_storage,
    get_clause_storage,
)

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)


@router.post(
    "/{document_id}/benchmarks/compare",
    response_model=BenchmarkJobResponse,
    status_code=status.HTTP_200_OK,
)
async def compare_benchmarks(
    document_id: str,
    clause_storage: ClauseStorage = Depends(get_clause_storage),
    engine: BenchmarkComparisonEngine = Depends(get_benchmark_engine),
    storage: BenchmarkStorage = Depends(get_benchmark_storage),
) -> BenchmarkJobResponse:
    clauses = await clause_storage.load(document_id)
    if clauses is None:
        raise HTTPException(
            status_code=404,
            detail="Clauses not found. Run POST /clauses/extract first.",
        )

    if not clauses.clauses:
        raise HTTPException(status_code=422, detail="No clauses available for benchmark comparison")

    result = await engine.compare(clauses)
    await storage.save(result)

    return BenchmarkJobResponse(
        document_id=document_id,
        status="completed",
        comparison_count=len(result.comparisons),
        overall_deviation_score=result.overall_deviation_score,
        message=f"Generated {len(result.comparisons)} benchmark comparison(s)",
    )


@router.get("/{document_id}/benchmarks", response_model=DocumentBenchmarkResult)
async def get_benchmarks(
    document_id: str,
    storage: BenchmarkStorage = Depends(get_benchmark_storage),
) -> DocumentBenchmarkResult:
    result = await storage.load(document_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Benchmark comparison not found. Run POST /benchmarks/compare first.",
        )
    return result
