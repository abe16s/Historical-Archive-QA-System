# services/evaluation_service.py
"""
Service for evaluating factual grounding of RAG responses.
"""
from typing import List, Dict, Any
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationMetrics,
)
from app.infra.evaluation import (
    evaluate_citation_accuracy,
    evaluate_context_relevance,
    evaluate_answer_faithfulness,
    compute_overall_score,
    generate_recommendations,
)


class EvaluationService:
    """Service for evaluating RAG responses for factual grounding."""
    
    def evaluate(
        self,
        query: str,
        answer: str,
        context_chunks: List[Dict[str, Any]],
        sources: List[str] = None
    ) -> EvaluationResponse:
        """
        Evaluate a RAG response for factual grounding.
        
        Args:
            query: The original question
            answer: The generated answer
            context_chunks: Retrieved context chunks used to generate answer
            sources: List of source documents with page numbers (e.g., ["doc.pdf (Page 188)"])
        
        Returns:
            EvaluationResponse with comprehensive metrics
        """
        # Evaluate citation accuracy (now uses provided sources)
        citation_accuracy = evaluate_citation_accuracy(answer, context_chunks, provided_sources=sources)
        
        # Evaluate context relevance (now uses actual similarity scores)
        context_relevance = evaluate_context_relevance(context_chunks, query)
        
        # Evaluate answer faithfulness
        answer_faithfulness = evaluate_answer_faithfulness(answer, context_chunks)
        
        # Compute overall score
        overall_score = compute_overall_score(
            citation_accuracy,
            context_relevance,
            answer_faithfulness
        )
        
        # Create metrics object
        metrics = EvaluationMetrics(
            citation_accuracy=citation_accuracy,
            context_relevance=context_relevance,
            answer_faithfulness=answer_faithfulness,
            overall_score=overall_score
        )
        
        # Generate recommendations
        recommendations = generate_recommendations(metrics)
        
        return EvaluationResponse(
            query=query,
            answer=answer,
            metrics=metrics,
            recommendations=recommendations
        )
