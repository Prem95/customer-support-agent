from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflow.nodes import MAX_RETRIES, WorkflowNodes
from app.workflow.state import WorkflowState


def build_graph(nodes: WorkflowNodes) -> CompiledStateGraph:
    graph = StateGraph(WorkflowState)
    graph.add_node("analyze_intent", nodes.analyze_intent)
    graph.add_node("retrieve_knowledge", nodes.retrieve_knowledge)
    graph.add_node("generate_recommendations", nodes.generate_recommendations)
    graph.add_node("update_summary", nodes.update_summary)
    graph.add_node("handle_failure", nodes.handle_failure)

    graph.add_edge(START, "analyze_intent")
    graph.add_conditional_edges(
        "analyze_intent",
        _route_after_intent,
        ["analyze_intent", "retrieve_knowledge", "generate_recommendations", "handle_failure"],
    )
    graph.add_edge("retrieve_knowledge", "generate_recommendations")
    graph.add_conditional_edges(
        "generate_recommendations",
        _route_after_recommendations,
        ["generate_recommendations", "update_summary", "handle_failure"],
    )
    graph.add_edge("update_summary", END)
    graph.add_edge("handle_failure", END)

    return graph.compile(checkpointer=MemorySaver())


def _can_retry(state: WorkflowState) -> bool:
    return state.get("retries", 0) <= MAX_RETRIES


def _route_after_intent(state: WorkflowState) -> str:
    if state.get("error"):
        return "analyze_intent" if _can_retry(state) else "handle_failure"
    if state.get("needs_retrieval", True):
        return "retrieve_knowledge"
    return "generate_recommendations"


def _route_after_recommendations(state: WorkflowState) -> str:
    if state.get("error"):
        return "generate_recommendations" if _can_retry(state) else "handle_failure"
    return "update_summary"
