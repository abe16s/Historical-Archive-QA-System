from typing import List, Dict, Optional, Any

SYSTEM_INSTRUCTIONS = """You are a historical document analysis assistant. Your task is to answer questions based ONLY on the provided context from historical documents.

CRITICAL INSTRUCTIONS:
1. Base your answer STRICTLY on the provided context below
2. If the answer cannot be found in the context, explicitly state: "I cannot find this information in the provided documents"
3. ALWAYS cite your sources using the EXACT format: [Source: filename, Page: X] - use the actual page number from the context, NOT "Context N" references
4. For EVERY factual claim, include a citation with the source filename and page number
5. Be factual, precise, and maintain historical accuracy
6. Do not make up information or use knowledge outside the provided context
7. If multiple sources are relevant, cite all of them
8. If this is a follow-up question, use the conversation history to understand context

IMPORTANT: When citing sources, use the format [Source: filename, Page: X] where X is the actual page number from the context chunks above. Do NOT use "Context 1" or similar references."""

HUMAN_MESSAGE_TEMPLATE = """CONTEXT FROM DOCUMENTS:
{context_text}

QUESTION: {query}

Please provide a comprehensive answer based on the context above. For EVERY factual claim, include source citations in the format [Source: filename, Page: X] using the actual page numbers from the context."""


def format_prompt_with_context(
    query: str,
    context_chunks: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None,
    use_system_message: bool = True,
) -> List[Dict[str, str]]:
    """Format the prompt with retrieved context using the historical document analysis prompt."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        metadata = chunk.get('metadata', {})
        source = metadata.get('source', 'Unknown')
        page = metadata.get('page', '?')
        text = chunk.get('text') or chunk.get('content', '')
        context_parts.append(f"[Context {i}]\nSource: {source}\nPage: {page}\nContent: {text}\n")
    
    context_text = "\n".join(context_parts)
    
    messages: List[Dict[str, str]] = []
    if use_system_message:
        messages.append({"role": "system", "content": SYSTEM_INSTRUCTIONS})
    
    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append({"role": "human", "content": content})
            elif role == "assistant":
                messages.append({"role": "ai", "content": content})
    
    human_message = HUMAN_MESSAGE_TEMPLATE.format(
        context_text=context_text,
        query=query
    )
    
    messages.append({"role": "human", "content": human_message})
    return messages
