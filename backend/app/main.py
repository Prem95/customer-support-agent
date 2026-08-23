import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.config import get_settings
from app.knowledge.retriever import KnowledgeRetriever
from app.services.conversation import ConnectionManager, ConversationService
from app.services.llm import LLMClient
from app.workflow.graph import build_graph
from app.workflow.nodes import WorkflowNodes


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    retriever = KnowledgeRetriever()
    llm = LLMClient(settings)
    graph = build_graph(WorkflowNodes(llm, retriever, settings))

    # for arch design
    try:
        export_graph = graph.get_graph().draw_mermaid_png()
        Path("graph_design.png").write_bytes(export_graph)
    except Exception:
        # rendering calls mermaid.ink, so never let it stop startup
        logging.getLogger(__name__).warning("graph diagram export failed", exc_info=True)

    connections = ConnectionManager()

    app.state.retriever = retriever
    app.state.connections = connections
    app.state.conversation_service = ConversationService(graph, connections)

    logging.getLogger(__name__).info(
        "startup complete env=%s model=%s knowledge_docs=%d",
        settings.environment,
        settings.llm_model,
        retriever.document_count,
    )
    yield


def create_app(debug: bool = False) -> FastAPI:
    app = FastAPI(title="Copilot Backend", lifespan=lifespan, debug=debug)
    app.include_router(api_router)
    app.include_router(ws_router)
    return app

app = create_app(debug=True)
