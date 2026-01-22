from typing import List, Dict, Optional, Any
from urllib.parse import quote

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
    return_context: bool = False,
    api_base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """
    Complete RAG pipeline: retrieve context, build prompt, generate answer.
    
    Args:
        return_context: If True, includes context_chunks in return dict for evaluation
        api_base_url: Base URL for generating source document links
    """
    context_chunks = retrieve_relevant_context(
        query, vector_store_collection, embedding_model, top_k
    )
    prompt_messages = format_prompt_with_context(query, context_chunks, conversation_history)
    answer = generate_response(prompt_messages, llm_client, temperature)

    source_info_map = {}
    for chunk in context_chunks:
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "unknown")
        page = metadata.get("page")
        pdf_page_index = metadata.get("pdf_page_index")
        
        page_str = str(page).strip() if page is not None and page != "?" and str(page).strip() else None
        key = (source, page_str)
        
        if key not in source_info_map:
            if page_str:
                display_text = f"{source} (Page {page_str})"
            else:
                display_text = source
            
            encoded_source = quote(source, safe='')
            url = f"{api_base_url}/documents/view/{encoded_source}"
            
            page_for_url = pdf_page_index if pdf_page_index is not None else page
            if page_for_url is not None:
                try:
                    page_num = int(page_for_url)
                    url += f"#page={page_num}"
                except (ValueError, TypeError):
                    pass
            
            source_info_map[key] = {
                "source": source,
                "page": int(page_str) if page_str and page_str.isdigit() else None,
                "display_text": display_text,
                "url": url
            }
    
    # Sort sources by source name, then by page number
    sources = sorted(
        list(source_info_map.values()),
        key=lambda x: (x["source"], x["page"] or 0)
    )

    result = {"response": answer, "sources": sources}
    
    if return_context:
        result["context_chunks"] = context_chunks
    
    return result


