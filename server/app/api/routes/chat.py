from fastapi import APIRouter, Depends, HTTPException, Request
from urllib.parse import quote

from app.schemas.chat import ChatRequest, ChatResponse, SourceInfo
from app.core.deps import get_rag_service, get_conversation_service
from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.conversation_service import ConversationService
from app.infra.llm import QuotaExceededError

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
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
        
        # Generate API base URL for source links
        base_url = str(request.base_url).rstrip('/')
        api_base_url = base_url or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        result = await rag_service.answer_question(
            payload.message, 
            conversation_history=conversation_history,
            api_base_url=api_base_url
        )
        
        conversation_service.add_message(conversation_id, "user", payload.message)
        conversation_service.add_message(conversation_id, "assistant", result.text)
        
        source_infos = []
        for source in result.sources:
            if isinstance(source, dict):
                source_infos.append(SourceInfo(**source))
            else:
                encoded_source = quote(str(source), safe='')
                source_infos.append(SourceInfo(
                    source=str(source),
                    page=None,
                    display_text=str(source),
                    url=f"{api_base_url}/documents/view/{encoded_source}"
                ))
        
        return ChatResponse(
            response=result.text,
            sources=source_infos,
            conversation_id=conversation_id,
            timestamp=result.timestamp,
        )
    except QuotaExceededError as exc:
        # Return user-friendly quota error
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": exc.message,
                "retry_after": exc.retry_after,
                "quota_limit": exc.quota_limit
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like quota errors) as-is
        raise
    except Exception as exc:  # pragma: no cover - simple pass-through
        raise HTTPException(status_code=500, detail=str(exc))
