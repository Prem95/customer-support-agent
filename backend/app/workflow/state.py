import operator
from typing import Annotated, TypedDict

from app.schemas import KnowledgeRef


class Message(TypedDict):
    role: str
    content: str
    ts: str | None

# workflow state actually represent the complete lifecycle of the "agent"
class WorkflowState(TypedDict, total=False):
    messages: Annotated[list[Message], operator.add]
    tokens_input: Annotated[int, operator.add]
    tokens_output: Annotated[int, operator.add]
    retries: int
    intent: str
    intent_confidence: float
    reasoning: str
    search_query: str
    needs_retrieval: bool
    knowledge: list[KnowledgeRef]
    suggested_response: str
    missing_info: list[str]
    next_action: str
    summary: str
    error: str | None
