from typing import List, Dict, Optional, Any

SYSTEM_INSTRUCTIONS = """You are a historical document analysis assistant. Your task is to answer questions based ONLY on the provided context from historical documents.

CRITICAL INSTRUCTIONS:
1. Base your answer STRICTLY on the provided context below
2. If the answer cannot be found in the context, explicitly state: "I cannot find this information in the provided documents"
3. Be factual, precise, and maintain historical accuracy
4. Do not make up information or use knowledge outside the provided context
5. If this is a follow-up question, use the conversation history to understand context
6. Provide a clear, comprehensive answer without including source citations in the text
7. The sources will be provided separately, so focus on delivering a clean, readable answer"""

HUMAN_MESSAGE_TEMPLATE = """CONTEXT FROM DOCUMENTS:
{context_text}

QUESTION: {query}

Provide a comprehensive answer based ONLY on the context above. 

IMPORTANT: 
- Answer the question clearly and completely using only the information from the provided context
- Do NOT include source citations or references in your answer text
- The sources will be provided separately by the system
- Focus on delivering a clean, readable, and informative response"""


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
            f"Page: {page}\n"
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
