# api/routes/evaluation.py
"""
API routes for evaluating RAG responses for factual grounding.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import EvaluationService
from app.services.rag_service import RAGService
from app.core.deps import get_rag_service

router = APIRouter()


def get_evaluation_service() -> EvaluationService:
    """Dependency to get evaluation service instance."""
    return EvaluationService()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_response(
    request: EvaluationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    """
    Evaluate a RAG response for factual grounding.
    
    This endpoint evaluates:
    - Citation accuracy (whether citations match actual sources)
    - Context relevance (how relevant retrieved chunks are to the query)
    - Answer faithfulness (whether claims in the answer are supported by context)
    - Overall factual grounding score
    
    Returns comprehensive metrics and recommendations for improvement.
    """
    try:
        result = evaluation_service.evaluate(
            query=request.query,
            answer=request.answer,
            context_chunks=request.context_chunks,
            sources=request.sources,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(exc)}")


@router.post("/evaluate-chat", response_model=EvaluationResponse)
async def evaluate_chat_response(
    query: str,
    rag_service: RAGService = Depends(get_rag_service),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    """
    Evaluate a chat response by running the RAG pipeline and evaluating the result.
    
    This is a convenience endpoint that:
    1. Runs the RAG pipeline for the given query
    2. Evaluates the generated response for factual grounding
    3. Returns both the answer and evaluation metrics
    
    This is useful for real-time evaluation during chat interactions.
    """
    try:
        # Run RAG pipeline with context chunks returned
        rag_result = await rag_service.answer_question(
            query=query,
            return_context=True
        )
        
        if not rag_result.context_chunks:
            raise HTTPException(
                status_code=400,
                detail="No context chunks retrieved. Cannot evaluate response."
            )
        
        # Evaluate the response
        result = evaluation_service.evaluate(
            query=query,
            answer=rag_result.text,
            context_chunks=rag_result.context_chunks,
            sources=rag_result.sources,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(exc)}")
