import asyncio
import logging
import re
import time
import uuid
from datetime import UTC, datetime

from fastapi import WebSocket
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.schemas import (
    ChatMessage,
    ConversationSummary,
    ErrorEvent,
    MessageEvent,
    SidebarEvent,
    SidebarUpdate,
    StageEvent,
)

logger = logging.getLogger(__name__)

SIDEBAR_FIELDS = set(SidebarUpdate.model_fields)
CLAIM_RE = re.compile(r"\bCLM-\w{4,}\b", re.IGNORECASE)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    def connect(self, conversation_id: str, websocket: WebSocket) -> None:
        self._connections.setdefault(conversation_id, set()).add(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket) -> None:
        self._connections.get(conversation_id, set()).discard(websocket)

    async def broadcast(self, conversation_id: str, event: BaseModel) -> None:
        payload = event.model_dump()
        for websocket in list(self._connections.get(conversation_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001
                self.disconnect(conversation_id, websocket)


class ConversationService:
    def __init__(self, graph: CompiledStateGraph, connections: ConnectionManager):
        self._graph = graph
        self._connections = connections
        self._runs: dict[str, asyncio.Task] = {}
        self._registry: dict[str, dict] = {}

    @staticmethod
    def _config(conversation_id: str) -> dict:
        return {"configurable": {"thread_id": conversation_id}}

    def touch(self, conversation_id: str) -> None:
        entry = self._registry.setdefault(conversation_id, {"label": None})
        entry["updated_at"] = time.time()

    async def export_conversation(self, conversation_id: str) -> dict:
        snapshot = await self._graph.aget_state(self._config(conversation_id))
        values = snapshot.values or {}
        messages = values.get("messages", [])
        tokens_input = values.get("tokens_input", 0)
        tokens_output = values.get("tokens_output", 0)
        return {
            "conversation_id": conversation_id,
            "label": self._registry.get(conversation_id, {}).get("label"),
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "message_count": len(messages),
            "tokens_used": {
                "input": tokens_input,
                "output": tokens_output,
                "total": tokens_input + tokens_output,
            },
            "analysis": {
                "intent": values.get("intent"),
                "intent_confidence": values.get("intent_confidence"),
                "reasoning": values.get("reasoning"),
                "missing_info": values.get("missing_info"),
                "next_action": values.get("next_action"),
                "summary": values.get("summary"),
            },
            "messages": messages,
        }

    async def delete_conversation(self, conversation_id: str) -> None:
        self._cancel_run(conversation_id)
        self._runs.pop(conversation_id, None)
        self._registry.pop(conversation_id, None)
        await self._graph.checkpointer.adelete_thread(conversation_id)

    def list_conversations(self) -> list[ConversationSummary]:
        ordered = sorted(self._registry.items(), key=lambda kv: kv[1]["updated_at"], reverse=True)
        return [
            ConversationSummary(conversation_id=cid, label=entry["label"]) for cid, entry in ordered
        ]

    async def get_sidebar(self, conversation_id: str) -> SidebarUpdate:
        snapshot = await self._graph.aget_state(self._config(conversation_id))
        return self._sidebar_from_state(snapshot.values or {})

    async def get_messages(self, conversation_id: str) -> list[ChatMessage]:
        snapshot = await self._graph.aget_state(self._config(conversation_id))
        return [ChatMessage(**m) for m in (snapshot.values or {}).get("messages", [])]

    async def handle_message(self, conversation_id: str, message: ChatMessage) -> None:
        message = message.model_copy(update={"ts": datetime.now(UTC).isoformat(timespec="seconds")})
        self.touch(conversation_id)
        if match := CLAIM_RE.search(message.content):
            entry = self._registry[conversation_id]
            entry["label"] = entry["label"] or match.group().upper()
        if message.role == "agent":
            if await self._is_duplicate_agent_message(conversation_id, message):
                logger.info("dropped duplicate agent message conversation_id=%s", conversation_id)
                return
            await self._connections.broadcast(conversation_id, MessageEvent(message=message))
            # agent turns join the conversation memory but don't trigger a run
            await self._graph.aupdate_state(
                self._config(conversation_id),
                {"messages": [message.model_dump()]},
                as_node="__start__",
            )
            return
        await self._connections.broadcast(conversation_id, MessageEvent(message=message))
        self._cancel_run(conversation_id)
        self._runs[conversation_id] = asyncio.create_task(
            self._run_workflow(conversation_id, message)
        )

    async def _is_duplicate_agent_message(self, conversation_id: str, message: ChatMessage) -> bool:
        snapshot = await self._graph.aget_state(self._config(conversation_id))
        messages = (snapshot.values or {}).get("messages", [])
        return bool(
            messages
            and messages[-1]["role"] == "agent"
            and messages[-1]["content"] == message.content
        )

    def _cancel_run(self, conversation_id: str) -> None:
        # latest customer message wins, drop any in-flight run
        task = self._runs.get(conversation_id)
        if task and not task.done():
            task.cancel()

    async def _run_workflow(self, conversation_id: str, message: ChatMessage) -> None:
        run_id = uuid.uuid4().hex[:8]
        log = logging.LoggerAdapter(logger, {"conversation_id": conversation_id, "run_id": run_id})
        log.info("workflow run started")
        state: dict = {}
        try:
            async for update in self._graph.astream(
                {"messages": [message.model_dump()]},
                self._config(conversation_id),
                stream_mode="updates",
            ):
                for node_name, node_output in update.items():
                    state.update(node_output or {})
                    await self._connections.broadcast(conversation_id, StageEvent(stage=node_name))
            await self._connections.broadcast(
                conversation_id, SidebarEvent(sidebar=self._sidebar_from_state(state))
            )
            log.info("workflow run finished intent=%s", state.get("intent"))
        except asyncio.CancelledError:
            log.info("workflow run superseded by newer message")
        except Exception as exc:
            log.exception("workflow run failed")
            await self._connections.broadcast(
                conversation_id, ErrorEvent(detail=f"workflow run failed: {exc}")
            )

    @staticmethod
    def _sidebar_from_state(state: dict) -> SidebarUpdate:
        fields = {k: v for k, v in state.items() if k in SIDEBAR_FIELDS and v is not None}
        fields["degraded"] = bool(state.get("error"))
        return SidebarUpdate(**fields)
