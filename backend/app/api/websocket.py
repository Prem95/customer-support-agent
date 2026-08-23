import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas import ErrorEvent, InboundEvent, TypingEvent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{conversation_id}")
async def conversation_socket(websocket: WebSocket, conversation_id: str) -> None:
    connections = websocket.app.state.connections
    service = websocket.app.state.conversation_service

    await websocket.accept()
    connections.connect(conversation_id, websocket)
    service.touch(conversation_id)
    logger.info("websocket connected conversation_id=%s", conversation_id)
    try:
        while True:
            raw = await websocket.receive_json()
            try:
                event = InboundEvent.model_validate(raw)
            except ValidationError as exc:
                await websocket.send_json(ErrorEvent(detail=str(exc)).model_dump())
                continue
            if event.type == "typing" and event.role:
                await connections.broadcast(conversation_id, TypingEvent(role=event.role))
            elif event.type == "message" and event.message:
                await service.handle_message(conversation_id, event.message)
    except WebSocketDisconnect:
        logger.info("websocket disconnected conversation_id=%s", conversation_id)
    finally:
        connections.disconnect(conversation_id, websocket)
