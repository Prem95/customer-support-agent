import os

import pytest

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.config import Settings
from app.knowledge.retriever import KnowledgeRetriever
from app.workflow.graph import build_graph
from app.workflow.nodes import WorkflowNodes
from app.workflow.outputs import IntentAnalysis, Recommendations, SummaryOutput


class FakeLLM:
    def __init__(
        self,
        intent: str = "claim_rejection_inquiry",
        needs_retrieval: bool = True,
        fail_on: set[str] | None = None,
        fail_times: int | None = None,
    ):
        self.intent = intent
        self.needs_retrieval = needs_retrieval
        self.fail_on = fail_on or set()
        # None means fail forever, an int means fail that many calls then recover
        self.fail_times = fail_times
        self.calls: dict[str, int] = {}

    def _should_fail(self, key: str) -> bool:
        if key not in self.fail_on:
            return False
        self.calls[key] = self.calls.get(key, 0) + 1
        return self.fail_times is None or self.calls[key] <= self.fail_times

    async def complete(self, system: str, user: str, output_type: type):
        usage = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
        if output_type is IntentAnalysis:
            if self._should_fail("intent"):
                raise RuntimeError("simulated intent failure")
            return IntentAnalysis(
                intent=self.intent,
                confidence=0.9,
                reasoning="test",
                needs_retrieval=self.needs_retrieval,
                search_query="claim rejected",
            ), usage
        if output_type is Recommendations:
            if self._should_fail("recommend"):
                raise RuntimeError("simulated recommendation failure")
            return Recommendations(
                suggested_response="Could you share your claim reference number?",
                missing_info=["claim reference number"],
                next_action="Ask for the claim reference number",
            ), usage
        return SummaryOutput(summary="Issue: rejected claim | Still missing: claim ref"), usage


@pytest.fixture
def settings() -> Settings:
    return Settings(openrouter_api_key="test-key")


@pytest.fixture
def retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever()


def make_graph(llm: FakeLLM, retriever: KnowledgeRetriever, settings: Settings):
    return build_graph(WorkflowNodes(llm, retriever, settings))
