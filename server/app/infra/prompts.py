from typing import List, Dict, Optional, Any

SYSTEM_INSTRUCTIONS = """You are a historical document analysis assistant. Your task is to answer questions based ONLY on the provided context from historical documents.

CRITICAL INSTRUCTIONS FOR CITATIONS:
1. Base your answer STRICTLY on the provided context below
2. If the answer cannot be found in the context, explicitly state: "I cannot find this information in the provided documents"
3. For EVERY factual claim, you MUST include a citation with the EXACT format: [Source: filename, Page: X]
4. The page number X MUST be the EXACT page number shown in the "Page:" field of the context chunk you are citing
5. DO NOT guess, estimate, or approximate page numbers - use ONLY the exact page number from the context
6. DO NOT use page numbers from your memory or general knowledge
7. If you cite information from "[Context 1]" which shows "Page: 188", you MUST cite it as "Page: 188" - NOT any other number
8. Copy the page number EXACTLY as it appears in the context - if it says "Page: 188", use "Page: 188"
9. Be factual, precise, and maintain historical accuracy
10. Do not make up information or use knowledge outside the provided context
11. If multiple sources are relevant, cite all of them with their exact page numbers
12. If this is a follow-up question, use the conversation history to understand context

CRITICAL: The page number in your citation MUST match EXACTLY the "Page:" number shown in the context chunk. Look at the context carefully and copy the page number exactly. If the context shows "Page: 188", your citation must say "Page: 188" - nothing else."""

HUMAN_MESSAGE_TEMPLATE = """CONTEXT FROM DOCUMENTS:
{context_text}

QUESTION: {query}

CRITICAL: Provide a comprehensive answer based ONLY on the context above. 

For EVERY factual claim, you MUST include source citations in the EXACT format: [Source: filename, Page: X]

IMPORTANT: The page number X must be copied EXACTLY from the "Page:" field shown in the context chunk you are citing. 
- If the context shows "Page: 188", your citation MUST say "Page: 188"
- If the context shows "Page: 194", your citation MUST say "Page: 194"
- DO NOT use approximate or estimated page numbers
- DO NOT use page numbers from memory
- Copy the page number EXACTLY as it appears in the context above

Example: If you see "[Context 1]\nSource: document.pdf\nPage: 188\nContent: ...", then cite it as [Source: document.pdf, Page: 188]"""


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
        # Make page number very explicit and prominent
        context_parts.append(
            f"[Context {i}]\n"
            f"Source: {source}\n"
            f"Page: {page} <-- USE THIS EXACT PAGE NUMBER IN YOUR CITATION\n"
            f"Content: {text}\n"
        )
    
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
