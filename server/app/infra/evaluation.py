# infra/evaluation.py
"""
Evaluation module for measuring factual grounding in RAG responses.

This module provides metrics to assess:
- Answer faithfulness to retrieved context
- Citation accuracy
- Context relevance
- Overall factual grounding quality
"""
import re
from typing import List, Dict, Any, Tuple
from app.schemas.evaluation import (
    CitationAccuracy,
    ContextRelevance,
    AnswerFaithfulness,
    EvaluationMetrics,
)


def extract_citations(answer: str) -> List[Dict[str, str]]:
    """
    Extract citations from answer text.
    
    Expected format: [Source: filename, Page: X]
    Returns list of dicts with 'source' and 'page' keys.
    """
    citations = []
    # Pattern to match [Source: filename, Page: X] or [Source: filename, Page: X, ...]
    pattern = r'\[Source:\s*([^,]+),\s*Page:\s*(\d+|\?)\]'
    
    matches = re.finditer(pattern, answer, re.IGNORECASE)
    for match in matches:
        citations.append({
            'source': match.group(1).strip(),
            'page': match.group(2).strip(),
            'full_match': match.group(0)
        })
    
    return citations


def get_available_sources(context_chunks: List[Dict[str, Any]]) -> Dict[str, set]:
    """
    Extract all available sources and pages from context chunks.
    
    Returns dict mapping source names to sets of page numbers.
    """
    sources = {}
    for chunk in context_chunks:
        metadata = chunk.get('metadata', {})
        source = metadata.get('source', 'Unknown')
        page = metadata.get('page')
        
        if source not in sources:
            sources[source] = set()
        
        if page is not None:
            # Normalize page numbers to strings for consistent comparison
            # This ensures citations (which are strings) can match stored page numbers
            try:
                # Convert to string, but preserve numeric value for comparison
                page_str = str(page).strip()
                sources[source].add(page_str)
            except (ValueError, TypeError):
                sources[source].add(str(page))
    
    return sources


def evaluate_citation_accuracy(
    answer: str,
    context_chunks: List[Dict[str, Any]]
) -> CitationAccuracy:
    """
    Evaluate the accuracy of citations in the answer.
    
    Checks if citations match actual sources in context.
    """
    citations = extract_citations(answer)
    available_sources = get_available_sources(context_chunks)
    
    # Get all source names from context
    context_sources = set(available_sources.keys())
    
    valid_citations = 0
    invalid_citations = []
    
    for citation in citations:
        source = citation['source']
        page = citation['page']
        
        # Check if source exists in context
        if source in available_sources:
            # Check if page is valid (or if '?' is used, that's acceptable)
            # Page numbers are normalized to strings in get_available_sources, so direct comparison works
            page_str = str(page).strip()
            if page_str == '?' or len(available_sources[source]) == 0:
                valid_citations += 1
            elif page_str in available_sources[source]:
                valid_citations += 1
            else:
                invalid_citations.append(citation['full_match'])
        else:
            invalid_citations.append(citation['full_match'])
    
    # Find sources in context but not cited
    cited_sources = {c['source'] for c in citations}
    missing_sources = list(context_sources - cited_sources)
    
    total_citations = len(citations)
    citation_accuracy = valid_citations / total_citations if total_citations > 0 else 0.0
    
    return CitationAccuracy(
        total_citations=total_citations,
        valid_citations=valid_citations,
        citation_accuracy=citation_accuracy,
        missing_sources=missing_sources,
        invalid_citations=invalid_citations
    )


def evaluate_context_relevance(
    context_chunks: List[Dict[str, Any]],
    query: str,
    similarity_threshold: float = 0.5
) -> ContextRelevance:
    """
    Evaluate the relevance of retrieved context chunks.
    
    Uses similarity scores from vector search if available.
    """
    if not context_chunks:
        return ContextRelevance(
            average_similarity=0.0,
            min_similarity=0.0,
            max_similarity=0.0,
            relevant_chunks=0,
            total_chunks=0
        )
    
    similarities = []
    for chunk in context_chunks:
        # Try to get similarity score from metadata or distance
        similarity = chunk.get('similarity') or chunk.get('distance')
        if similarity is not None:
            # Convert distance to similarity if needed (assuming cosine distance)
            if isinstance(similarity, (int, float)) and similarity <= 1.0:
                # If it's a distance, convert to similarity (1 - distance)
                if similarity < 0:
                    similarity = 1.0 - abs(similarity)
                similarities.append(float(similarity))
    
    if not similarities:
        # If no similarity scores available, assume moderate relevance
        similarities = [0.6] * len(context_chunks)
    
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    min_similarity = min(similarities) if similarities else 0.0
    max_similarity = max(similarities) if similarities else 0.0
    relevant_chunks = sum(1 for s in similarities if s >= similarity_threshold)
    
    return ContextRelevance(
        average_similarity=avg_similarity,
        min_similarity=min_similarity,
        max_similarity=max_similarity,
        relevant_chunks=relevant_chunks,
        total_chunks=len(context_chunks)
    )


def extract_claims(answer: str) -> List[str]:
    """
    Extract factual claims from the answer.
    
    Simple heuristic: split by sentences and filter out questions/citations.
    """
    # Remove citations first
    answer_clean = re.sub(r'\[Source:[^\]]+\]', '', answer)
    
    # Split by sentence endings
    sentences = re.split(r'[.!?]+', answer_clean)
    
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Filter out very short sentences, questions, and empty strings
        if len(sentence) > 20 and not sentence.endswith('?') and sentence:
            # Remove common prefixes
            sentence = re.sub(r'^(According to|Based on|The document|It|This)', '', sentence, flags=re.IGNORECASE).strip()
            if len(sentence) > 20:
                claims.append(sentence)
    
    return claims


def check_claim_support(claim: str, context_chunks: List[Dict[str, Any]]) -> bool:
    """
    Check if a claim is supported by the context chunks.
    
    Uses simple keyword matching and text overlap as a heuristic.
    """
    # Extract key terms from claim (simple approach)
    claim_lower = claim.lower()
    claim_words = set(re.findall(r'\b\w{4,}\b', claim_lower))  # Words with 4+ chars
    
    if not claim_words:
        return False
    
    # Check each context chunk
    for chunk in context_chunks:
        chunk_text = (chunk.get('text') or chunk.get('content') or '').lower()
        chunk_words = set(re.findall(r'\b\w{4,}\b', chunk_text))
        
        # Check overlap - if significant overlap, claim is likely supported
        overlap = len(claim_words & chunk_words)
        overlap_ratio = overlap / len(claim_words) if claim_words else 0
        
        # Also check for direct substring match (for exact quotes)
        if any(word in chunk_text for word in claim_words if len(word) > 5):
            return True
        
        # If significant word overlap, consider it supported
        if overlap_ratio >= 0.3:  # 30% word overlap threshold
            return True
    
    return False


def evaluate_answer_faithfulness(
    answer: str,
    context_chunks: List[Dict[str, Any]]
) -> AnswerFaithfulness:
    """
    Evaluate how well the answer is grounded in the provided context.
    
    Checks if claims in the answer can be verified in context.
    """
    claims = extract_claims(answer)
    
    if not claims:
        return AnswerFaithfulness(
            faithfulness_score=0.0,
            supported_claims=0,
            total_claims=0,
            unsupported_claims=[]
        )
    
    supported_claims = []
    unsupported_claims = []
    
    for claim in claims:
        if check_claim_support(claim, context_chunks):
            supported_claims.append(claim)
        else:
            unsupported_claims.append(claim)
    
    total_claims = len(claims)
    faithfulness_score = len(supported_claims) / total_claims if total_claims > 0 else 0.0
    
    return AnswerFaithfulness(
        faithfulness_score=faithfulness_score,
        supported_claims=len(supported_claims),
        total_claims=total_claims,
        unsupported_claims=unsupported_claims[:5]  # Limit to first 5 for brevity
    )


def compute_overall_score(
    citation_accuracy: CitationAccuracy,
    context_relevance: ContextRelevance,
    answer_faithfulness: AnswerFaithfulness,
    weights: Dict[str, float] = None
) -> float:
    """
    Compute weighted overall factual grounding score.
    
    Default weights:
    - Citation accuracy: 0.3
    - Context relevance: 0.2
    - Answer faithfulness: 0.5
    """
    if weights is None:
        weights = {
            'citation': 0.3,
            'relevance': 0.2,
            'faithfulness': 0.5
        }
    
    citation_score = citation_accuracy.citation_accuracy
    relevance_score = context_relevance.average_similarity
    faithfulness_score = answer_faithfulness.faithfulness_score
    
    overall = (
        citation_score * weights['citation'] +
        relevance_score * weights['relevance'] +
        faithfulness_score * weights['faithfulness']
    )
    
    return round(overall, 3)


def generate_recommendations(metrics: EvaluationMetrics) -> List[str]:
    """
    Generate recommendations for improving factual grounding.
    """
    recommendations = []
    
    # Citation recommendations
    if metrics.citation_accuracy.citation_accuracy < 0.8:
        invalid_count = len(metrics.citation_accuracy.invalid_citations)
        recommendations.append(
            f"Improve citation accuracy: {invalid_count} invalid citations found. "
            "Ensure all citations match sources in the retrieved context."
        )
    
    if metrics.citation_accuracy.missing_sources:
        recommendations.append(
            f"Cite all relevant sources: {len(metrics.citation_accuracy.missing_sources)} sources in context are not cited."
        )
    
    # Relevance recommendations
    if metrics.context_relevance.average_similarity < 0.6:
        recommendations.append(
            "Improve context retrieval: Retrieved chunks have low relevance. "
            "Consider adjusting retrieval parameters or improving query formulation."
        )
    
    # Faithfulness recommendations
    if metrics.answer_faithfulness.faithfulness_score < 0.7:
        recommendations.append(
            f"Improve answer grounding: {len(metrics.answer_faithfulness.unsupported_claims)} claims cannot be verified. "
            "Ensure all factual claims are supported by the retrieved context."
        )
    
    # Overall recommendations
    if metrics.overall_score < 0.7:
        recommendations.append(
            "Overall factual grounding needs improvement. Focus on ensuring answers are "
            "strictly based on retrieved context and all claims are properly cited."
        )
    elif metrics.overall_score >= 0.9:
        recommendations.append(
            "Excellent factual grounding! The answer is well-grounded in the provided context."
        )
    
    return recommendations if recommendations else ["No specific recommendations. Factual grounding is good."]
