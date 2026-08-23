from app.workflow.nodes import MAX_RETRIES
from tests.conftest import FakeLLM, make_graph

CONFIG = {"configurable": {"thread_id": "test-thread"}}


def customer(content: str) -> dict:
    return {"messages": [{"role": "customer", "content": content}]}


async def test_full_run_populates_sidebar_state(settings, retriever):
    graph = make_graph(FakeLLM(), retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected, why?"), CONFIG)
    assert state["intent"] == "claim_rejection_inquiry"
    assert state["tokens_input"] == 300  # 3 LLM calls x 100 fake tokens
    assert state["tokens_output"] == 60
    assert state["knowledge"], "retrieval should have run"
    assert state["suggested_response"]
    assert state["next_action"]
    assert state["summary"]
    assert state["missing_info"] == ["claim reference number"]


async def test_greeting_skips_retrieval(settings, retriever):
    graph = make_graph(
        FakeLLM(intent="general_support", needs_retrieval=False), retriever, settings
    )
    state = await graph.ainvoke(customer("Hi there, how are you?"), CONFIG)
    assert state.get("knowledge") in (None, [])
    assert state["suggested_response"]


async def test_intent_failure_routes_to_fallback(settings, retriever):
    graph = make_graph(FakeLLM(fail_on={"intent"}), retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    assert state["error"]
    assert "temporarily unavailable" in state["suggested_response"]


async def test_recommendation_failure_routes_to_fallback(settings, retriever):
    graph = make_graph(FakeLLM(fail_on={"recommend"}), retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    assert state["error"]
    assert state["intent"] == "claim_rejection_inquiry"


async def test_transient_failure_is_retried_then_succeeds(settings, retriever):
    llm = FakeLLM(fail_on={"intent"}, fail_times=1)
    graph = make_graph(llm, retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    assert llm.calls["intent"] == 2, "the node should have been retried once"
    assert state["error"] is None
    assert state["retries"] == 0
    assert state["intent"] == "claim_rejection_inquiry"


async def test_retries_are_bounded_and_stop_at_the_fallback(settings, retriever):
    llm = FakeLLM(fail_on={"intent"})
    graph = make_graph(llm, retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    assert llm.calls["intent"] == MAX_RETRIES + 1, "no infinite loop"
    assert state["retries"] == MAX_RETRIES + 1
    assert "temporarily unavailable" in state["suggested_response"]


async def test_recommendation_retry_is_bounded(settings, retriever):
    llm = FakeLLM(fail_on={"recommend"})
    graph = make_graph(llm, retriever, settings)
    state = await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    assert llm.calls["recommend"] == MAX_RETRIES + 1
    assert state["error"]


async def test_conversation_memory_accumulates_across_runs(settings, retriever):
    graph = make_graph(FakeLLM(), retriever, settings)
    await graph.ainvoke(customer("My claim was rejected"), CONFIG)
    state = await graph.ainvoke(customer("The reference is CLM-123"), CONFIG)
    contents = [m["content"] for m in state["messages"]]
    assert contents == ["My claim was rejected", "The reference is CLM-123"]
