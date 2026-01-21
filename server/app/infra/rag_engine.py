from typing import List, Dict, Optional, Any

from app.infra.llm import LLMClient
from app.infra.prompts import format_prompt_with_context
from app.infra.vector_store import search_similar_documents


def retrieve_relevant_context(
    query: str,
    vector_store_collection: Any,
    embedding_model: Any,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Retrieve relevant document chunks for a query from the vector store."""
    return search_similar_documents(query, vector_store_collection, embedding_model, top_k)

def generate_response(
    prompt_messages: List[Dict[str, str]],
    llm_client: LLMClient,
    temperature: float = 0.7,
) -> str:
    """Generate a response using the configured LLM via direct API calls."""
    if hasattr(llm_client, "temperature"):
        llm_client.temperature = temperature

    response = llm_client.invoke(prompt_messages)
    return response.content


def rag_pipeline(
    query: str,
    vector_store_collection: Any,
    embedding_model: Any,
    llm_client: LLMClient,
    top_k: int = 3,
    temperature: float = 0.7,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Complete RAG pipeline: retrieve context, build prompt, generate answer."""
    context_chunks = retrieve_relevant_context(
        query, vector_store_collection, embedding_model, top_k
    )
    prompt_messages = format_prompt_with_context(query, context_chunks, conversation_history)
    answer = generate_response(prompt_messages, llm_client, temperature)

    sources = list(
        {chunk.get("metadata", {}).get("source", "unknown") for chunk in context_chunks}
    )

    return {"response": answer, "sources": sources}


