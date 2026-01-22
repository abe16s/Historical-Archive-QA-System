# schemas/evaluation.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class EvaluationRequest(BaseModel):
    """Request model for evaluating a RAG response."""
    query: str = Field(..., description="The original question")
    answer: str = Field(..., description="The generated answer")
    context_chunks: List[Dict[str, Any]] = Field(
        ..., 
        description="The retrieved context chunks used to generate the answer"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of source documents cited in the answer"
    )


class CitationAccuracy(BaseModel):
    """Metrics for citation accuracy."""
    total_citations: int = Field(..., description="Total number of citations found in answer")
    valid_citations: int = Field(..., description="Number of citations that match actual sources")
    citation_accuracy: float = Field(..., description="Ratio of valid citations to total citations")
    missing_sources: List[str] = Field(
        default_factory=list,
        description="Sources in context but not cited in answer"
    )
    invalid_citations: List[str] = Field(
        default_factory=list,
        description="Citations in answer that don't match any source"
    )


class ContextRelevance(BaseModel):
    """Metrics for context relevance."""
    average_similarity: float = Field(..., description="Average similarity score of retrieved chunks")
    min_similarity: float = Field(..., description="Minimum similarity score")
    max_similarity: float = Field(..., description="Maximum similarity score")
    relevant_chunks: int = Field(..., description="Number of chunks with similarity above threshold")
    total_chunks: int = Field(..., description="Total number of retrieved chunks")


class AnswerFaithfulness(BaseModel):
    """Metrics for answer faithfulness to context."""
    faithfulness_score: float = Field(
        ..., 
        description="Score from 0-1 indicating how well answer is grounded in context"
    )
    supported_claims: int = Field(..., description="Number of claims that can be verified in context")
    total_claims: int = Field(..., description="Total number of factual claims in answer")
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims that cannot be verified in the provided context"
    )


class EvaluationMetrics(BaseModel):
    """Comprehensive evaluation metrics for factual grounding."""
    citation_accuracy: CitationAccuracy
    context_relevance: ContextRelevance
    answer_faithfulness: AnswerFaithfulness
    overall_score: float = Field(
        ..., 
        description="Weighted overall score (0-1) for factual grounding"
    )
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvaluationResponse(BaseModel):
    """Response model for evaluation results."""
    query: str
    answer: str
    metrics: EvaluationMetrics
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improving factual grounding"
    )
