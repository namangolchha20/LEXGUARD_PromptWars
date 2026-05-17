import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import aiofiles
from lexguard_shared.schemas.orchestrator import (
    AgentName,
    AgentRunState,
    AgentRunStatus,
    AnalysisState,
    OrchestratorEvent,
    OrchestratorEventType,
    PipelineStatus,
)

logger = logging.getLogger(__name__)

EventCallback = Callable[[OrchestratorEvent], Awaitable[None]]


class StateManager:
    """Centralized analysis state with persistence and event broadcasting."""

    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._listeners: list[EventCallback] = []
        self._active: dict[str, AnalysisState] = {}

    def subscribe(self, callback: EventCallback) -> None:
        self._listeners.append(callback)

    async def create_run(self, document_id: str, agents: list[AgentName]) -> AnalysisState:
        run_id = uuid4().hex
        state = AnalysisState(
            document_id=document_id,
            run_id=run_id,
            status=PipelineStatus.PENDING,
            agents={
                agent.value: AgentRunState(agent=agent) for agent in agents
            },
        )
        self._active[run_id] = state
        await self._persist(state)
        return state

    def get(self, run_id: str) -> AnalysisState | None:
        return self._active.get(run_id)

    async def load(self, document_id: str) -> AnalysisState | None:
        path = self._state_path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            raw = await f.read()
        if not raw.strip():
            return None
        state = AnalysisState.model_validate(json.loads(raw))
        self._active[state.run_id] = state
        return state

    async def update_agent(
        self,
        state: AnalysisState,
        agent: AgentName,
        *,
        status: AgentRunStatus | None = None,
        progress: float | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        run = state.agents[agent.value]
        if status is not None:
            run.status = status
            if status == AgentRunStatus.RUNNING and run.started_at is None:
                run.started_at = datetime.now(UTC)
            if status in (AgentRunStatus.COMPLETED, AgentRunStatus.FAILED, AgentRunStatus.SKIPPED):
                run.completed_at = datetime.now(UTC)
        if progress is not None:
            run.progress = progress
        if message is not None:
            run.message = message
        if error is not None:
            run.error = error
            state.errors[agent.value] = error

        state.updated_at = datetime.now(UTC)
        state.overall_progress = self._compute_overall_progress(state)
        await self._persist(state)

    async def complete_run(
        self,
        state: AnalysisState,
        status: PipelineStatus,
    ) -> None:
        state.status = status
        state.updated_at = datetime.now(UTC)
        state.overall_progress = 1.0 if status == PipelineStatus.COMPLETED else state.overall_progress
        await self._persist(state)

    async def emit(
        self,
        event_type: OrchestratorEventType,
        state: AnalysisState,
        *,
        agent: AgentName | None = None,
        message: str = "",
        progress: float | None = None,
        payload: dict | None = None,
    ) -> None:
        event = OrchestratorEvent(
            type=event_type,
            document_id=state.document_id,
            run_id=state.run_id,
            agent=agent,
            message=message,
            progress=progress if progress is not None else state.overall_progress,
            payload=payload or {},
        )
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception as exc:
                logger.warning("Event listener failed: %s", exc)

    def _compute_overall_progress(self, state: AnalysisState) -> float:
        if not state.agents:
            return 0.0
        from lexguard_orchestrator.graph import AGENT_WEIGHTS

        total = 0.0
        for name, run in state.agents.items():
            weight = AGENT_WEIGHTS.get(AgentName(name), 1 / len(state.agents))
            total += weight * run.progress
        return round(min(total, 1.0), 3)

    def _state_path(self, document_id: str) -> Path:
        return self._state_dir / f"{document_id}.state.json"

    async def _persist(self, state: AnalysisState) -> None:
        path = self._state_path(state.document_id)
        tmp = path.with_suffix(".tmp")
        payload = state.model_dump_json(indent=2)
        async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
            await f.write(payload)
        os.replace(tmp, path)
