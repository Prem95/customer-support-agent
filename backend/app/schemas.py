from typing import Literal, get_args

from pydantic import BaseModel, Field

Role = Literal["customer", "agent"]

IntentName = Literal[
    "product_inquiry",
    "coverage_inquiry",
    "claim_status_inquiry",
    "claim_rejection_inquiry",
    "policy_question",
    "complaint",
    "general_support",
    "unknown",
]

INTENTS = list(get_args(IntentName))


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=4000)
    ts: str | None = None  # stamped server-side on receipt


class KnowledgeRef(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float


class SidebarUpdate(BaseModel):
    intent: str = "unknown"
    intent_confidence: float = 0.0
    reasoning: str = ""
    suggested_response: str = ""
    knowledge: list[KnowledgeRef] = []
    missing_info: list[str] = []
    next_action: str = ""
    summary: str = ""
    degraded: bool = False


class InboundEvent(BaseModel):
    type: Literal["message", "typing"]
    message: ChatMessage | None = None
    role: Role | None = None


class TypingEvent(BaseModel):
    type: Literal["typing"] = "typing"
    role: Role


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    message: ChatMessage


class StageEvent(BaseModel):
    type: Literal["workflow_stage"] = "workflow_stage"
    stage: str


class SidebarEvent(BaseModel):
    type: Literal["workflow_update"] = "workflow_update"
    sidebar: SidebarUpdate


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    detail: str


class ConversationSummary(BaseModel):
    conversation_id: str
    label: str | None = None


class KnowledgeUpload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)
