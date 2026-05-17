from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from lexguard_shared.schemas.benchmark import DocumentBenchmarkResult
from lexguard_shared.schemas.clause import ClauseExtractionResult
from lexguard_shared.schemas.consequence import ConsequenceSimulationResult
from lexguard_shared.schemas.document import ParsedDocument
from lexguard_shared.schemas.negotiation import NegotiationResult
from lexguard_shared.schemas.risk import DocumentRiskAnalysis


class AgentName(StrEnum):
    INGESTION = "ingestion"
    EXTRACTION = "extraction"
    RISK = "risk"
    SIMULATION = "simulation"
    BENCHMARK = "benchmark"
    NEGOTIATION = "negotiation"


class AgentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class PipelineStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class AgentRunState(BaseModel):
    agent: AgentName
    status: AgentRunStatus = AgentRunStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0


class OrchestratorEventType(StrEnum):
    RUN_STARTED = "run_started"
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_RETRYING = "agent_retrying"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class OrchestratorEvent(BaseModel):
    type: OrchestratorEventType
    document_id: str
    run_id: str
    agent: AgentName | None = None
    message: str = ""
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalysisState(BaseModel):
    """Centralized shared analysis state across all agents."""

    document_id: str
    run_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    agents: dict[str, AgentRunState] = Field(default_factory=dict)
    parsed_document: ParsedDocument | None = None
    clauses: ClauseExtractionResult | None = None
    risk: DocumentRiskAnalysis | None = None
    consequences: ConsequenceSimulationResult | None = None
    benchmarks: DocumentBenchmarkResult | None = None
    negotiation: NegotiationResult | None = None
    overall_progress: float = 0.0
    errors: dict[str, str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineRunResponse(BaseModel):
    document_id: str
    run_id: str
    status: PipelineStatus
    message: str | None = None
