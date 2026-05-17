import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lexguard_shared.schemas.orchestrator import OrchestratorEvent
from lexguard_shared.schemas.websocket import WsEnvelope, WsMessageType

from lexguard_api.dependencies import get_event_bus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/orchestrator/{document_id}")
async def orchestrator_stream(websocket: WebSocket, document_id: str) -> None:
    await websocket.accept()
    bus = get_event_bus()

    async def forward_event(event: OrchestratorEvent) -> None:
        if event.document_id != document_id:
            return
        envelope = WsEnvelope(
            type=WsMessageType.ORCHESTRATOR,
            payload=event.model_dump(mode="json"),
        )
        await websocket.send_text(envelope.model_dump_json())

    bus.subscribe_document(document_id, forward_event)

    connected = WsEnvelope(
        type=WsMessageType.CONNECTED,
        payload={"message": f"subscribed to orchestrator events for {document_id}"},
    )
    await websocket.send_text(connected.model_dump_json())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                envelope = WsEnvelope.model_validate_json(raw)
            except Exception:
                await websocket.send_text(
                    WsEnvelope(
                        type=WsMessageType.ERROR,
                        payload={"message": "invalid envelope"},
                    ).model_dump_json()
                )
                continue

            if envelope.type == WsMessageType.PING:
                await websocket.send_text(
                    WsEnvelope(type=WsMessageType.PONG, payload={}).model_dump_json()
                )
    except WebSocketDisconnect:
        bus.unsubscribe_document(document_id, forward_event)
        logger.info("Orchestrator WS disconnected for %s", document_id)
