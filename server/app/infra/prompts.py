from typing import List, Dict, Optional, Any

SYSTEM_INSTRUCTIONS = """You are a historical document analysis assistant. Your task is to answer questions based on the provided context from historical documents and conversation history.

CRITICAL INSTRUCTIONS:
1. Base your answer on the provided context below AND the conversation history
2. Use conversation history to understand references like "it", "they", "this", "that", "when did it happen", etc.
3. If a question asks about what was discussed earlier (e.g., "what were we talking about?"), use the conversation history to answer
4. If the answer cannot be found in either the context or conversation history, explicitly state: "I cannot find this information in the provided documents"
5. Be factual, precise, and maintain historical accuracy
6. Do not make up information or use knowledge outside the provided context or conversation history
7. Provide a clear, comprehensive answer without including source citations in the text
8. The sources will be provided separately, so focus on delivering a clean, readable answer"""

HUMAN_MESSAGE_TEMPLATE = """{conversation_context}CONTEXT FROM DOCUMENTS:
{context_text}

CURRENT QUESTION: {query}

Provide a comprehensive answer based on the context above and the conversation history.

IMPORTANT: 
- If this is a follow-up question, use the conversation history to understand what "it", "they", "this", etc. refer to
- Answer the question clearly and completely using information from the provided context and conversation history
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
        context_parts.append(
            f"[Context {i}]\n"
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content: {text}\n"
        )
    
    context_text = "\n".join(context_parts)
    
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        conversation_context = "PREVIOUS CONVERSATION:\n"
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                conversation_context += f"User: {content}\n"
            elif role == "assistant":
                conversation_context += f"Assistant: {content}\n"
        conversation_context += "\n"
    
    messages: List[Dict[str, str]] = []
    if use_system_message:
        messages.append({"role": "system", "content": SYSTEM_INSTRUCTIONS})
    
    human_message = HUMAN_MESSAGE_TEMPLATE.format(
        conversation_context=conversation_context,
        context_text=context_text,
        query=query
    )
    
    messages.append({"role": "human", "content": human_message})
    return messages
