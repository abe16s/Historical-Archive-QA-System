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
    context_chunks: List[Dict[str, Any]],
    provided_sources: List[str] = None
) -> CitationAccuracy:
    """
    Evaluate the accuracy of citations/sources.
    
    Since citations are no longer in the answer text, we check if:
    1. Sources are provided separately and match context
    2. All context sources are represented in provided sources
    """
    available_sources = get_available_sources(context_chunks)
    context_sources = set(available_sources.keys())
    
    # Try to extract citations from answer (for backward compatibility)
    citations = extract_citations(answer)
    
    # If sources are provided separately, use those
    if provided_sources:
        # Parse each source individually (each source+page combination is a separate citation)
        source_page_pairs = []
        for source_str in provided_sources:
            # Match format: "source.pdf (Page 188)" or just "source.pdf"
            match = re.match(r'^(.+?)\s*\(Page\s+(\d+|\?)\)$', source_str.strip())
            if match:
                source_name = match.group(1).strip()
                page = match.group(2).strip()
                source_page_pairs.append((source_name, page, source_str))
            else:
                # No page number, just source name
                source_page_pairs.append((source_str.strip(), None, source_str))
        
        # Validate each source+page pair against context
        valid_citations = 0
        invalid_citations = []
        
        for source_name, page, original_str in source_page_pairs:
            is_valid = False
            
            if source_name in available_sources:
                context_pages = available_sources[source_name]
                
                # If page is specified
                if page is not None:
                    if page == '?':
                        # '?' is acceptable as unknown page
                        is_valid = True
                    elif context_pages:
                        # Check if the specific page exists in context
                        # Normalize page numbers for comparison
                        page_str = str(page).strip()
                        # Try both string and int comparison
                        page_int = None
                        try:
                            page_int = int(page_str)
                        except (ValueError, TypeError):
                            pass
                        
                        # Check if page matches (as string or int)
                        if page_str in context_pages:
                            is_valid = True
                        elif page_int is not None:
                            # Try matching as integer
                            context_pages_ints = {int(p) for p in context_pages if str(p).isdigit()}
                            if page_int in context_pages_ints:
                                is_valid = True
                        
                        if not is_valid:
                            invalid_citations.append(original_str)
                    else:
                        # No page info in context, but source exists - accept it
                        is_valid = True
                else:
                    # No page specified, just check source exists
                    is_valid = True
            else:
                # Source doesn't exist in context
                invalid_citations.append(original_str)
                is_valid = False
            
            if is_valid:
                valid_citations += 1
        
        # Find sources in context but not in provided sources
        provided_source_names = {pair[0] for pair in source_page_pairs}
        missing_sources = list(context_sources - provided_source_names)
        
        total_citations = len(provided_sources)
        citation_accuracy = valid_citations / total_citations if total_citations > 0 else 0.0
        
        return CitationAccuracy(
            total_citations=total_citations,
            valid_citations=valid_citations,
            citation_accuracy=citation_accuracy,
            missing_sources=missing_sources,
            invalid_citations=invalid_citations
        )
    
    # Fallback: use citations from answer text (for backward compatibility)
    if citations:
        valid_citations = 0
        invalid_citations = []
        
        for citation in citations:
            source = citation['source']
            page = citation['page']
            
            if source in available_sources:
                page_str = str(page).strip()
                if page_str == '?' or len(available_sources[source]) == 0:
                    valid_citations += 1
                elif page_str in available_sources[source]:
                    valid_citations += 1
                else:
                    invalid_citations.append(citation['full_match'])
            else:
                invalid_citations.append(citation['full_match'])
        
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
    
    # No citations or sources provided - all sources are missing
    return CitationAccuracy(
        total_citations=0,
        valid_citations=0,
        citation_accuracy=0.0,
        missing_sources=list(context_sources),
        invalid_citations=[]
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
        # Get similarity score (now included in search results)
        similarity = chunk.get('similarity')
        if similarity is not None and isinstance(similarity, (int, float)):
            similarities.append(float(similarity))
        else:
            distance = chunk.get('distance')
            if distance is not None and isinstance(distance, (int, float)):
                similarity = max(0.0, 1.0 - float(distance))
                similarities.append(similarity)
    
    if not similarities:
        # If no similarity scores available, cannot evaluate relevance accurately
        # Return low scores to indicate uncertainty
        return ContextRelevance(
            average_similarity=0.0,
            min_similarity=0.0,
            max_similarity=0.0,
            relevant_chunks=0,
            total_chunks=len(context_chunks)
        )
    
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    min_similarity = min(similarities) if similarities else 0.0
    max_similarity = max(similarities) if similarities else 0.0
    relevant_chunks = sum(1 for s in similarities if s >= similarity_threshold)
    
    return ContextRelevance(
        average_similarity=round(avg_similarity, 3),
        min_similarity=round(min_similarity, 3),
        max_similarity=round(max_similarity, 3),
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
    
    Uses improved semantic matching with keyword overlap and phrase matching.
    """
    if not claim or len(claim.strip()) < 10:
        return False
    
    claim_lower = claim.lower().strip()
    
    # Remove common stop words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
    claim_words = set(re.findall(r'\b\w{3,}\b', claim_lower))
    claim_words = {w for w in claim_words if w not in stop_words and len(w) > 2}
    
    if not claim_words:
        return False
    
    # Check each context chunk
    for chunk in context_chunks:
        chunk_text = (chunk.get('text') or chunk.get('content') or '').lower()
        if not chunk_text:
            continue
        
        chunk_words = set(re.findall(r'\b\w{3,}\b', chunk_text))
        chunk_words = {w for w in chunk_words if w not in stop_words and len(w) > 2}
        
        # Calculate word overlap
        overlap = claim_words & chunk_words
        overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0
        
        # Check for key phrases (3+ word sequences)
        claim_phrases = []
        claim_tokens = claim_lower.split()
        for i in range(len(claim_tokens) - 2):
            phrase = ' '.join(claim_tokens[i:i+3])
            if len(phrase) > 10:  # Only meaningful phrases
                claim_phrases.append(phrase)
        
        # If a key phrase appears in context, likely supported
        if claim_phrases and any(phrase in chunk_text for phrase in claim_phrases):
            return True
        
        # If significant word overlap (40% of meaningful words), consider supported
        if overlap_ratio >= 0.4:
            return True
        
        # Check for important named entities or numbers (likely factual claims)
        important_terms = re.findall(r'\b\d+\b|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', claim)
        if important_terms:
            # If important terms appear in context, likely supported
            if any(term.lower() in chunk_text for term in important_terms):
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
    citation_acc = metrics.citation_accuracy
    if citation_acc.citation_accuracy < 0.8:
        invalid_count = len(citation_acc.invalid_citations)
        total = citation_acc.total_citations
        valid = citation_acc.valid_citations
        
        if invalid_count > 0:
            recommendations.append(
                f"Citation accuracy is {citation_acc.citation_accuracy:.1%} ({valid}/{total} valid). "
                f"{invalid_count} invalid citation(s) found. Ensure all source citations match the retrieved context chunks."
            )
        elif total > 0:
            # Low accuracy but no invalid citations - might be missing sources
            recommendations.append(
                f"Citation accuracy is {citation_acc.citation_accuracy:.1%} ({valid}/{total} valid). "
                "Some sources may not be properly cited or may not match the context."
            )
        else:
            recommendations.append(
                "No sources were provided. Include source citations to improve factual grounding."
            )
    
    if citation_acc.missing_sources:
        recommendations.append(
            f"Missing sources: {len(citation_acc.missing_sources)} source(s) from the retrieved context are not cited. "
            f"Consider citing: {', '.join(citation_acc.missing_sources[:3])}"
            + ("..." if len(citation_acc.missing_sources) > 3 else "")
        )
    
    # Relevance recommendations
    relevance = metrics.context_relevance
    if relevance.average_similarity < 0.5:
        recommendations.append(
            f"Low context relevance (average similarity: {relevance.average_similarity:.1%}). "
            f"Only {relevance.relevant_chunks}/{relevance.total_chunks} chunks are above the relevance threshold. "
            "Consider refining the query or adjusting retrieval parameters to get more relevant context."
        )
    elif relevance.average_similarity < 0.6:
        recommendations.append(
            f"Moderate context relevance (average similarity: {relevance.average_similarity:.1%}). "
            "The retrieved chunks could be more relevant to the query."
        )
    
    # Faithfulness recommendations
    faithfulness = metrics.answer_faithfulness
    if faithfulness.faithfulness_score < 0.7:
        unsupported_count = len(faithfulness.unsupported_claims)
        recommendations.append(
            f"Answer faithfulness is {faithfulness.faithfulness_score:.1%} ({faithfulness.supported_claims}/{faithfulness.total_claims} claims supported). "
            f"{unsupported_count} claim(s) cannot be verified in the provided context. "
            "Ensure all factual claims are directly supported by the retrieved context."
        )
    
    # Overall recommendations
    if metrics.overall_score < 0.6:
        recommendations.append(
            f"Overall factual grounding score is {metrics.overall_score:.1%}, which needs significant improvement. "
            "Focus on improving citation accuracy, context relevance, and ensuring all claims are properly grounded."
        )
    elif metrics.overall_score < 0.7:
        recommendations.append(
            f"Overall factual grounding score is {metrics.overall_score:.1%}. "
            "There is room for improvement in citation accuracy and context relevance."
        )
    elif metrics.overall_score >= 0.9:
        recommendations.append(
            f"Excellent factual grounding! Overall score: {metrics.overall_score:.1%}. "
            "The answer is well-grounded in the provided context with accurate citations."
        )
    
    return recommendations if recommendations else ["Factual grounding is good. No specific recommendations."]
