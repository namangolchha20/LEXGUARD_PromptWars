import asyncio
import logging
from collections.abc import Callable
from uuid import uuid4

from lexguard_shared.schemas.orchestrator import (
    AgentName,
    AgentRunStatus,
    AnalysisState,
    OrchestratorEventType,
    PipelineStatus,
)

from lexguard_orchestrator.agents.runner import AgentContext, AgentRunner
from lexguard_orchestrator.config import OrchestratorSettings
from lexguard_orchestrator.graph import execution_layers
from lexguard_orchestrator.state import StateManager

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Coordinates multi-agent analysis with dependency graph execution."""

    def __init__(
        self,
        state_manager: StateManager,
        agent_context_factory: Callable[[], AgentContext],
        settings: OrchestratorSettings | None = None,
    ) -> None:
        self._state = state_manager
        self._context_factory = agent_context_factory
        self._settings = settings or OrchestratorSettings()
        self._runner = AgentRunner()

    async def run_pipeline(
        self,
        document_id: str | None = None,
        *,
        file_bytes: bytes | None = None,
        filename: str | None = None,
        skip_ingestion: bool = False,
        agents: list[AgentName] | None = None,
    ) -> AnalysisState:
        doc_id = document_id or uuid4().hex
        agent_set = set(agents or list(AgentName))
        if skip_ingestion:
            agent_set.discard(AgentName.INGESTION)

        state = await self._state.load(doc_id)
        if state is None:
            state = await self._state.create_run(doc_id, list(agent_set))
        await self._state.emit(
            OrchestratorEventType.RUN_STARTED,
            state,
            message=f"Pipeline started with {len(agent_set)} agents",
            progress=0.0,
        )

        ctx = self._context_factory()
        ctx.document_id = doc_id
        ctx.file_bytes = file_bytes
        ctx.filename = filename
        ctx.skip_ingestion = skip_ingestion

        try:
            layers = execution_layers(agent_set)
            failed_agents: list[AgentName] = []

            for layer in layers:
                await self._execute_layer(layer, ctx, state, failed_agents)

            if failed_agents and not self._settings.orchestrator_fail_fast:
                status = PipelineStatus.PARTIAL
                message = f"Completed with {len(failed_agents)} failed agent(s)"
                event_type = OrchestratorEventType.RUN_COMPLETED
            elif failed_agents:
                status = PipelineStatus.FAILED
                message = f"Pipeline failed at {failed_agents[0].value}"
                event_type = OrchestratorEventType.RUN_FAILED
            else:
                status = PipelineStatus.COMPLETED
                message = "All agents completed successfully"
                event_type = OrchestratorEventType.RUN_COMPLETED

            await self._state.complete_run(state, status)
            await self._state.emit(event_type, state, message=message, progress=1.0)
            return state

        except Exception as exc:
            logger.exception("Pipeline failed for %s", doc_id)
            await self._state.complete_run(state, PipelineStatus.FAILED)
            await self._state.emit(
                OrchestratorEventType.RUN_FAILED,
                state,
                message=str(exc),
                payload={"error": str(exc)},
            )
            raise

    async def _execute_layer(
        self,
        layer: list[AgentName],
        ctx: AgentContext,
        state: AnalysisState,
        failed_agents: list[AgentName],
    ) -> None:
        tasks = [
            self._run_agent_with_retry(agent, ctx, state, failed_agents)
            for agent in layer
        ]
        await asyncio.gather(*tasks)

    async def _run_agent_with_retry(
        self,
        agent: AgentName,
        ctx: AgentContext,
        state: AnalysisState,
        failed_agents: list[AgentName],
    ) -> None:
        max_retries = self._settings.orchestrator_max_retries
        delay = self._settings.orchestrator_retry_base_delay

        for attempt in range(max_retries + 1):
            await self._state.update_agent(
                state,
                agent,
                status=AgentRunStatus.RUNNING if attempt == 0 else AgentRunStatus.RETRYING,
                progress=0.1,
                message=f"Running {agent.value}" + (f" (retry {attempt})" if attempt else ""),
            )
            await self._state.emit(
                OrchestratorEventType.AGENT_STARTED if attempt == 0 else OrchestratorEventType.AGENT_RETRYING,
                state,
                agent=agent,
                message=f"{agent.value} started",
            )

            try:
                await self._runner.run(agent, ctx, state)
                await self._state.update_agent(
                    state,
                    agent,
                    status=AgentRunStatus.COMPLETED,
                    progress=1.0,
                    message=f"{agent.value} completed",
                )
                await self._state.emit(
                    OrchestratorEventType.AGENT_COMPLETED,
                    state,
                    agent=agent,
                    message=f"{agent.value} completed",
                )
                return
            except Exception as exc:
                logger.warning("Agent %s failed (attempt %d): %s", agent.value, attempt + 1, exc)
                if attempt < max_retries:
                    await asyncio.sleep(delay * (2**attempt))
                    continue

                await self._state.update_agent(
                    state,
                    agent,
                    status=AgentRunStatus.FAILED,
                    progress=0.0,
                    message=f"{agent.value} failed",
                    error=str(exc),
                )
                await self._state.emit(
                    OrchestratorEventType.AGENT_FAILED,
                    state,
                    agent=agent,
                    message=str(exc),
                    payload={"error": str(exc)},
                )
                failed_agents.append(agent)

                if self._settings.orchestrator_fail_fast:
                    raise
                return
