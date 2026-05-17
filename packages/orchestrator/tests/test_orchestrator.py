from unittest.mock import AsyncMock, MagicMock

import pytest
from lexguard_orchestrator.config import OrchestratorSettings
from lexguard_orchestrator.orchestrator import PipelineOrchestrator
from lexguard_orchestrator.state import StateManager
from lexguard_shared.schemas.clause import ClauseExtractionResult, ClauseType, ExtractedClause
from lexguard_shared.schemas.document import DocumentSection, ParsedDocument
from lexguard_shared.schemas.orchestrator import AgentName, PipelineStatus


@pytest.fixture
def state_manager(tmp_path) -> StateManager:
    return StateManager(tmp_path / "orchestrator")


@pytest.fixture
def mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.document_id = ""
    ctx.skip_ingestion = True
    return ctx


@pytest.fixture
def orchestrator(state_manager: StateManager, mock_context: MagicMock) -> PipelineOrchestrator:
    parsed = ParsedDocument(
        document_id="doc-orch",
        sections=[DocumentSection(title="Termination", content="30 days notice.", page=1)],
    )
    clauses = ClauseExtractionResult(
        document_id="doc-orch",
        clauses=[
            ExtractedClause(
                clause_id="c1",
                clause_type=ClauseType.TERMINATION,
                title="Termination",
                text="30 days notice.",
                confidence=0.9,
            ),
        ],
    )

    async def fake_run(agent, ctx, state):
        if agent == AgentName.INGESTION:
            state.parsed_document = parsed
        elif agent == AgentName.EXTRACTION:
            state.clauses = clauses
        elif agent == AgentName.RISK:
            from lexguard_shared.schemas.risk import DocumentRiskAnalysis

            state.risk = DocumentRiskAnalysis(
                document_id="doc-orch",
                overall_severity_score=10.0,
                overall_confidence=0.8,
                summary="Low risk",
            )
        elif agent == AgentName.BENCHMARK:
            from lexguard_shared.schemas.benchmark import DocumentBenchmarkResult, FairnessLevel

            state.benchmarks = DocumentBenchmarkResult(
                document_id="doc-orch",
                benchmark_summary="OK",
                overall_deviation_score=5.0,
                overall_fairness=FairnessLevel.NEUTRAL,
            )
        elif agent == AgentName.SIMULATION:
            from lexguard_shared.schemas.consequence import ConsequenceSimulationResult

            state.consequences = ConsequenceSimulationResult(
                document_id="doc-orch",
                scenarios=[],
                summary="None",
            )
        elif agent == AgentName.NEGOTIATION:
            from lexguard_shared.schemas.negotiation import NegotiationResult

            state.negotiation = NegotiationResult(
                document_id="doc-orch",
                summary="No major issues",
                overall_leverage="strong",
            )

    runner = MagicMock()
    runner.run = AsyncMock(side_effect=fake_run)

    orch = PipelineOrchestrator(
        state_manager,
        lambda: mock_context,
        OrchestratorSettings(orchestrator_max_retries=0),
    )
    orch._runner = runner
    return orch


@pytest.mark.asyncio
async def test_pipeline_completes_all_agents(
    orchestrator: PipelineOrchestrator,
) -> None:
    agents = [
        AgentName.EXTRACTION,
        AgentName.RISK,
        AgentName.BENCHMARK,
        AgentName.SIMULATION,
        AgentName.NEGOTIATION,
    ]
    state = await orchestrator.run_pipeline(
        "doc-orch",
        skip_ingestion=True,
        agents=agents,
    )

    assert state.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
    assert state.clauses is not None
    assert state.risk is not None
    assert state.benchmarks is not None
    assert state.negotiation is not None
