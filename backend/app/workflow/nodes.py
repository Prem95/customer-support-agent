import asyncio
import logging

from app.config import Settings
from app.knowledge.retriever import KnowledgeRetriever
from app.services.llm import LLMClient
from app.workflow import prompts
from app.workflow.outputs import IntentAnalysis, Recommendations, SummaryOutput
from app.workflow.state import WorkflowState

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = "AI assistance is temporarily unavailable, continue the conversation manually."

# a failing LLM node routes back to itself until MAX_RETRIES, then to handle_failure
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5


def _token_fields(usage: dict) -> dict:
    return {
        "tokens_input": usage.get("input_tokens", 0),
        "tokens_output": usage.get("output_tokens", 0),
    }


class WorkflowNodes:
    def __init__(self, llm: LLMClient, retriever: KnowledgeRetriever, settings: Settings):
        self._llm = llm
        self._retriever = retriever
        self._settings = settings

    @staticmethod
    async def _backoff(state: WorkflowState) -> None:
        attempt = state.get("retries", 0)
        if attempt:
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

    @staticmethod
    def _failure(state: WorkflowState, node: str, exc: Exception) -> dict:
        retries = state.get("retries", 0) + 1
        logger.warning("%s failed (attempt %d/%d): %s", node, retries, MAX_RETRIES + 1, exc)
        return {"error": f"{node} failed: {exc}", "retries": retries}

    def _transcript(self, state: WorkflowState) -> str:
        recent = state.get("messages", [])[-self._settings.transcript_window :]
        transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        transcript = transcript or "(no messages yet)"
        if previous := state.get("summary", ""):
            transcript = f"Previous summary: {previous}\n\nRecent messages:\n{transcript}"
        return transcript

    async def analyze_intent(self, state: WorkflowState) -> dict:
        await self._backoff(state)
        try:
            result, usage = await self._llm.complete(
                prompts.INTENT_SYSTEM, self._transcript(state), IntentAnalysis
            )
            return {
                **_token_fields(usage),
                "intent": result.intent,
                "intent_confidence": result.confidence,
                "reasoning": result.reasoning,
                "needs_retrieval": result.needs_retrieval,
                "search_query": result.search_query,
                "error": None,
                "retries": 0,
            }
        except Exception as exc:  # noqa: BLE001
            return self._failure(state, "intent analysis", exc)

    async def retrieve_knowledge(self, state: WorkflowState) -> dict:
        query = f"{state.get('search_query', '')} {state.get('intent', '')}".replace("_", " ")
        last_customer = next(
            (m["content"] for m in reversed(state.get("messages", [])) if m["role"] == "customer"),
            "",
        )
        results = self._retriever.search(
            f"{query} {last_customer}", top_k=self._settings.retrieval_top_k
        )
        return {"knowledge": results}

    async def generate_recommendations(self, state: WorkflowState) -> dict:
        await self._backoff(state)
        try:
            knowledge_block = (
                "\n\n".join(f"[{ref.title}]\n{ref.snippet}" for ref in state.get("knowledge", []))
                or "(no internal knowledge retrieved)"
            )
            user_prompt = (
                f"Detected intent: {state.get('intent')}\n\n"
                f"Retrieved knowledge:\n{knowledge_block}\n\n"
                f"Conversation:\n{self._transcript(state)}"
            )
            result, usage = await self._llm.complete(
                prompts.RECOMMEND_SYSTEM, user_prompt, Recommendations
            )
            return {
                **_token_fields(usage),
                "suggested_response": result.suggested_response,
                "missing_info": result.missing_info,
                "next_action": result.next_action,
                "error": None,
                "retries": 0,
            }
        except Exception as exc:  # noqa: BLE001
            return self._failure(state, "recommendation generation", exc)

    async def update_summary(self, state: WorkflowState) -> dict:
        try:
            result, usage = await self._llm.complete(
                prompts.SUMMARY_SYSTEM, self._transcript(state), SummaryOutput
            )
            return {**_token_fields(usage), "summary": result.summary}
        except Exception:
            # stale summary beats a failed run
            logger.exception("update_summary failed")
            return {}

    async def handle_failure(self, state: WorkflowState) -> dict:
        return {
            "intent": state.get("intent") or "unknown",
            "suggested_response": state.get("suggested_response") or FALLBACK_RESPONSE,
            "next_action": state.get("next_action")
            or "Handle the conversation without AI support.",
        }
