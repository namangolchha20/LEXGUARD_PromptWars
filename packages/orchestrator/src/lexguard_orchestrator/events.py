import asyncio
import logging
from collections import defaultdict

from lexguard_shared.schemas.orchestrator import OrchestratorEvent

from lexguard_orchestrator.state import EventCallback

logger = logging.getLogger(__name__)


class EventBus:
    """Broadcasts orchestrator events to WebSocket and other subscribers."""

    def __init__(self) -> None:
        self._document_subscribers: dict[str, list[EventCallback]] = defaultdict(list)
        self._global_subscribers: list[EventCallback] = []

    def subscribe_document(self, document_id: str, callback: EventCallback) -> None:
        self._document_subscribers[document_id].append(callback)

    def unsubscribe_document(self, document_id: str, callback: EventCallback) -> None:
        subs = self._document_subscribers.get(document_id, [])
        if callback in subs:
            subs.remove(callback)

    def subscribe_all(self, callback: EventCallback) -> None:
        self._global_subscribers.append(callback)

    async def publish(self, event: OrchestratorEvent) -> None:
        callbacks = list(self._global_subscribers) + list(
            self._document_subscribers.get(event.document_id, [])
        )
        if not callbacks:
            return
        await asyncio.gather(
            *(self._safe_invoke(cb, event) for cb in callbacks),
            return_exceptions=True,
        )

    async def _safe_invoke(self, callback: EventCallback, event: OrchestratorEvent) -> None:
        try:
            await callback(event)
        except Exception as exc:
            logger.warning("Event callback failed: %s", exc)
