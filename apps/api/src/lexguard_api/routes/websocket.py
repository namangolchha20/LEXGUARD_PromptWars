import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lexguard_shared.schemas.websocket import WsEnvelope, WsMessageType

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    connected = WsEnvelope(
        type=WsMessageType.CONNECTED,
        payload={"message": "connected to LEXGUARD"},
    )
    await websocket.send_text(connected.model_dump_json())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                envelope = WsEnvelope.model_validate_json(raw)
            except Exception:
                error = WsEnvelope(
                    type=WsMessageType.ERROR,
                    payload={"message": "invalid envelope"},
                )
                await websocket.send_text(error.model_dump_json())
                continue

            if envelope.type == WsMessageType.PING:
                pong = WsEnvelope(type=WsMessageType.PONG, payload={})
                await websocket.send_text(pong.model_dump_json())
            else:
                logger.debug("Received ws message: %s", envelope.type)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
