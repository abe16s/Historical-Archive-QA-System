from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.deps import get_rag_service, get_conversation_service
from app.services.rag_service import RAGService
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ChatResponse:
    """
    Main chat endpoint with conversation context support.

    Receives a user query and returns a RAG-generated response.
    If conversation_id is provided, includes conversation history in the context.
    """
    try:
        conversation_id = payload.conversation_id
        
        if not conversation_id:
            conversation_id = conversation_service.create_conversation()
        
        conversation_history = None
        recent_messages = conversation_service.get_recent_messages(conversation_id, limit=10)
        if recent_messages:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in recent_messages
            ]
        
        result = await rag_service.answer_question(
            payload.message, 
            conversation_history=conversation_history
        )
        
        conversation_service.add_message(conversation_id, "user", payload.message)
        conversation_service.add_message(conversation_id, "assistant", result.text)
        
        return ChatResponse(
            response=result.text,
            sources=result.sources,
            conversation_id=conversation_id,
            timestamp=result.timestamp,
        )
    except Exception as exc:  # pragma: no cover - simple pass-through
        raise HTTPException(status_code=500, detail=str(exc))
