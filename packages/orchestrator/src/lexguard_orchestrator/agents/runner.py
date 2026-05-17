import logging
from dataclasses import dataclass
from pathlib import Path

from lexguard_agents import AgentRegistry, ClauseStorage, ConsequenceStorage
from lexguard_agents.negotiation.agent import NegotiationAgent
from lexguard_benchmark import BenchmarkComparisonEngine, BenchmarkStorage
from lexguard_ingestion import DocumentStorage, IngestionPipeline
from lexguard_ingestion.validators import validate_upload
from lexguard_risk import RiskAnalysisEngine, RiskStorage
from lexguard_shared.schemas.orchestrator import AgentName

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    document_id: str
    file_path: Path | None
    filename: str | None
    file_bytes: bytes | None
    skip_ingestion: bool
    ingestion_pipeline: IngestionPipeline
    document_storage: DocumentStorage
    clause_storage: ClauseStorage
    risk_engine: RiskAnalysisEngine
    risk_storage: RiskStorage
    benchmark_engine: BenchmarkComparisonEngine
    benchmark_storage: BenchmarkStorage
    consequence_storage: ConsequenceStorage
    agent_registry: AgentRegistry
    negotiation_agent: NegotiationAgent


class AgentRunner:
    """Executes individual pipeline agents against shared context."""

    async def run(self, agent: AgentName, ctx: AgentContext, state) -> None:
        handlers = {
            AgentName.INGESTION: self._run_ingestion,
            AgentName.EXTRACTION: self._run_extraction,
            AgentName.RISK: self._run_risk,
            AgentName.BENCHMARK: self._run_benchmark,
            AgentName.SIMULATION: self._run_simulation,
            AgentName.NEGOTIATION: self._run_negotiation,
        }
        await handlers[agent](ctx, state)

    async def _run_ingestion(self, ctx: AgentContext, state) -> None:
        if ctx.skip_ingestion:
            parsed = await ctx.document_storage.get_result(ctx.document_id)
            if parsed:
                state.parsed_document = parsed
                return
            raise ValueError("skip_ingestion set but no parsed document found")

        if not ctx.file_bytes or not ctx.filename:
            raise ValueError("file required for ingestion")

        from lexguard_ingestion.config import IngestionSettings

        settings = IngestionSettings()
        doc_format = validate_upload(ctx.filename, len(ctx.file_bytes), settings)
        settings.ingestion_temp_dir.mkdir(parents=True, exist_ok=True)
        staging = settings.ingestion_temp_dir / f"{ctx.document_id}{Path(ctx.filename).suffix.lower()}"

        try:
            staging.write_bytes(ctx.file_bytes)
            result = await ctx.ingestion_pipeline.process(ctx.document_id, staging, doc_format)
            state.parsed_document = result
            await ctx.document_storage.save_result(result)
            from lexguard_shared.schemas.document import IngestionStatus

            await ctx.document_storage.update_status(
                ctx.document_id, IngestionStatus.COMPLETED, result=result
            )
        finally:
            staging.unlink(missing_ok=True)

    async def _run_extraction(self, ctx: AgentContext, state) -> None:
        if not state.parsed_document:
            state.parsed_document = await ctx.document_storage.get_result(ctx.document_id)
        if not state.parsed_document:
            raise ValueError("parsed document required for extraction")

        agent = ctx.agent_registry.clause_extraction
        result = await agent.extract(state.parsed_document)
        state.clauses = result
        await ctx.clause_storage.save(result)

    async def _run_risk(self, ctx: AgentContext, state) -> None:
        if not state.clauses:
            state.clauses = await ctx.clause_storage.load(ctx.document_id)
        if not state.clauses:
            raise ValueError("clauses required for risk analysis")

        result = await ctx.risk_engine.analyze(state.clauses)
        state.risk = result
        await ctx.risk_storage.save(result)

    async def _run_benchmark(self, ctx: AgentContext, state) -> None:
        if not state.clauses:
            state.clauses = await ctx.clause_storage.load(ctx.document_id)
        if not state.clauses:
            raise ValueError("clauses required for benchmark comparison")

        result = await ctx.benchmark_engine.compare(state.clauses)
        state.benchmarks = result
        await ctx.benchmark_storage.save(result)

    async def _run_simulation(self, ctx: AgentContext, state) -> None:
        if not state.clauses:
            state.clauses = await ctx.clause_storage.load(ctx.document_id)
        if not state.risk:
            state.risk = await ctx.risk_storage.load(ctx.document_id)
        if not state.clauses or not state.risk:
            raise ValueError("clauses and risk required for simulation")

        agent = ctx.agent_registry.consequence_simulation
        result = await agent.simulate(state.risk, state.clauses)
        state.consequences = result
        await ctx.consequence_storage.save(result)

    async def _run_negotiation(self, ctx: AgentContext, state) -> None:
        if not state.clauses:
            state.clauses = await ctx.clause_storage.load(ctx.document_id)
        if not state.risk:
            state.risk = await ctx.risk_storage.load(ctx.document_id)
        if not state.benchmarks:
            state.benchmarks = await ctx.benchmark_storage.load(ctx.document_id)
        if not state.consequences:
            state.consequences = await ctx.consequence_storage.load(ctx.document_id)

        if not state.clauses or not state.risk or not state.benchmarks:
            raise ValueError("clauses, risk, and benchmarks required for negotiation")

        result = await ctx.negotiation_agent.negotiate(
            ctx.document_id,
            state.clauses,
            state.risk,
            state.benchmarks,
            state.consequences,
        )
        state.negotiation = result
