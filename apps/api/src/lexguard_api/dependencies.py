from functools import lru_cache

from lexguard_agents import AgentRegistry, AgentSettings, ClauseStorage, ConsequenceStorage
from lexguard_agents.negotiation.agent import NegotiationAgent
from lexguard_ai import AISettings
from lexguard_benchmark import BenchmarkComparisonEngine, BenchmarkSettings, BenchmarkStorage
from lexguard_ingestion import (
    DocumentStorage,
    IngestionJobQueue,
    IngestionPipeline,
    IngestionSettings,
)
from lexguard_orchestrator import OrchestratorSettings, PipelineOrchestrator, StateManager
from lexguard_orchestrator.agents.runner import AgentContext
from lexguard_orchestrator.events import EventBus
from lexguard_risk import RiskAnalysisEngine, RiskSettings, RiskStorage

from lexguard_api.config import settings


@lru_cache
def get_ingestion_settings() -> IngestionSettings:
    return IngestionSettings(
        ingestion_temp_dir=settings.ingestion_temp_dir,
        ingestion_output_dir=settings.ingestion_output_dir,
        ingestion_max_file_size_mb=settings.ingestion_max_file_size_mb,
        ingestion_worker_concurrency=settings.ingestion_worker_concurrency,
        ingestion_ocr_min_chars_per_page=settings.ingestion_ocr_min_chars_per_page,
    )


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings(
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
        gemini_max_retries=settings.gemini_max_retries,
        gemini_retry_base_delay=settings.gemini_retry_base_delay,
        gemini_temperature=settings.gemini_temperature,
        gemini_max_concurrency=settings.gemini_max_concurrency,
    )


@lru_cache
def get_agent_settings() -> AgentSettings:
    return AgentSettings(
        clause_output_dir=settings.clause_output_dir,
        consequence_output_dir=settings.consequence_output_dir,
    )


@lru_cache
def get_document_storage() -> DocumentStorage:
    return DocumentStorage(get_ingestion_settings().ingestion_output_dir)


@lru_cache
def get_clause_storage() -> ClauseStorage:
    return ClauseStorage(get_agent_settings().clause_output_dir)


@lru_cache
def get_consequence_storage() -> ConsequenceStorage:
    return ConsequenceStorage(get_agent_settings().consequence_output_dir)


@lru_cache
def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(get_ingestion_settings())


@lru_cache
def get_benchmark_settings() -> BenchmarkSettings:
    return BenchmarkSettings(benchmark_output_dir=settings.benchmark_output_dir)


@lru_cache
def get_benchmark_storage() -> BenchmarkStorage:
    return BenchmarkStorage(get_benchmark_settings().benchmark_output_dir)


@lru_cache
def get_benchmark_engine() -> BenchmarkComparisonEngine:
    from lexguard_ai import AIClient

    ai_settings = get_ai_settings()
    return BenchmarkComparisonEngine(
        ai_client=AIClient(ai_settings),
        settings=get_benchmark_settings(),
        ai_settings=ai_settings,
    )


@lru_cache
def get_risk_settings() -> RiskSettings:
    return RiskSettings(
        risk_output_dir=settings.risk_output_dir,
        risk_llm_enhancement_threshold=settings.risk_llm_enhancement_threshold,
        risk_rule_weight=settings.risk_rule_weight,
        risk_llm_weight=settings.risk_llm_weight,
    )


@lru_cache
def get_risk_storage() -> RiskStorage:
    return RiskStorage(get_risk_settings().risk_output_dir)


@lru_cache
def get_risk_engine() -> RiskAnalysisEngine:
    from lexguard_ai import AIClient

    ai_settings = get_ai_settings()
    return RiskAnalysisEngine(
        ai_client=AIClient(ai_settings),
        settings=get_risk_settings(),
        ai_settings=ai_settings,
    )


@lru_cache
def get_agent_registry() -> AgentRegistry:
    from lexguard_ai import AIClient

    return AgentRegistry(
        ai_client=AIClient(get_ai_settings()),
        ai_settings=get_ai_settings(),
    )


@lru_cache
def get_orchestrator_settings() -> OrchestratorSettings:
    return OrchestratorSettings(
        orchestrator_state_dir=settings.orchestrator_state_dir,
        orchestrator_max_retries=settings.orchestrator_max_retries,
    )


@lru_cache
def get_event_bus() -> EventBus:
    return EventBus()


@lru_cache
def get_state_manager() -> StateManager:
    manager = StateManager(get_orchestrator_settings().orchestrator_state_dir)
    bus = get_event_bus()

    async def forward(event) -> None:
        await bus.publish(event)

    manager.subscribe(forward)
    return manager


def _build_agent_context() -> AgentContext:
    from lexguard_ai import AIClient

    ai_settings = get_ai_settings()
    return AgentContext(
        document_id="",
        file_path=None,
        filename=None,
        file_bytes=None,
        skip_ingestion=False,
        ingestion_pipeline=get_ingestion_pipeline(),
        document_storage=get_document_storage(),
        clause_storage=get_clause_storage(),
        risk_engine=get_risk_engine(),
        risk_storage=get_risk_storage(),
        benchmark_engine=get_benchmark_engine(),
        benchmark_storage=get_benchmark_storage(),
        consequence_storage=get_consequence_storage(),
        agent_registry=get_agent_registry(),
        negotiation_agent=NegotiationAgent(AIClient(ai_settings), ai_settings),
    )


@lru_cache
def get_orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(
        state_manager=get_state_manager(),
        agent_context_factory=_build_agent_context,
        settings=get_orchestrator_settings(),
    )


_job_queue: IngestionJobQueue | None = None


def get_job_queue() -> IngestionJobQueue:
    global _job_queue
    if _job_queue is None:
        ingestion_settings = get_ingestion_settings()
        _job_queue = IngestionJobQueue(
            pipeline=get_ingestion_pipeline(),
            storage=get_document_storage(),
            settings=ingestion_settings,
        )
    return _job_queue
