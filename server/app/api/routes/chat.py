from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.deps import get_rag_service
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    """
    Main chat endpoint.

    Receives a user query and returns a RAG-generated response.
    """
    try:
        result = await rag_service.answer_question(payload.message)
        return ChatResponse(
            response=result.text,
            sources=result.sources,
            conversation_id=result.conversation_id,
            timestamp=result.timestamp,
        )
    except Exception as exc:  # pragma: no cover - simple pass-through
        raise HTTPException(status_code=500, detail=str(exc))
