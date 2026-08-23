from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import ChatMessage, ConversationSummary, KnowledgeUpload, SidebarUpdate

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict:
    return {
        "status": "ok",
        "knowledge_documents": request.app.state.retriever.document_count,
    }


@router.get("/conversations", response_model=list[ConversationSummary])
async def conversations(request: Request) -> list[ConversationSummary]:
    return request.app.state.conversation_service.list_conversations()


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, request: Request) -> JSONResponse:
    data = await request.app.state.conversation_service.export_conversation(conversation_id)
    data["model"] = get_settings().llm_model
    filename = f"{data['label'] or conversation_id}.json"
    return JSONResponse(data, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, request: Request) -> dict:
    await request.app.state.conversation_service.delete_conversation(conversation_id)
    return {"deleted": conversation_id}


@router.post("/knowledge")
async def add_knowledge(payload: KnowledgeUpload, request: Request) -> dict:
    count = request.app.state.retriever.add_document(payload.title, payload.content)
    return {"knowledge_documents": count}


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessage])
async def conversation_messages(conversation_id: str, request: Request) -> list[ChatMessage]:
    return await request.app.state.conversation_service.get_messages(conversation_id)


@router.get("/conversations/{conversation_id}/sidebar", response_model=SidebarUpdate)
async def conversation_sidebar(conversation_id: str, request: Request) -> SidebarUpdate:
    return await request.app.state.conversation_service.get_sidebar(conversation_id)
