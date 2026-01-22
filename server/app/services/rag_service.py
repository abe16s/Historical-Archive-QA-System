from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Any, Optional, Dict

from app.core.config import settings
from app.infra.rag_engine import rag_pipeline


@dataclass
class RAGResult:
    text: str
    sources: List[str]
    conversation_id: str
    timestamp: datetime


class RAGService:
    """Orchestrates the RAG pipeline."""

    def __init__(
        self,
        vector_store_collection: Any,
        embedding_model: Any,
        llm_client: Any,
        top_k: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self._vector_store_collection = vector_store_collection
        self._embedding_model = embedding_model
        self._llm_client = llm_client
        self._top_k = top_k or settings.TOP_K_RETRIEVAL
        self._temperature = temperature or settings.LLM_TEMPERATURE

    async def answer_question(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        return_context: bool = False,
    ) -> RAGResult:
        """
        Run the RAG pipeline for a query and return a structured result.
        
        Args:
            query: The user's question
            conversation_history: Previous messages in the conversation
            return_context: If True, includes context_chunks in the result for evaluation
        """
        result = rag_pipeline(
            query=query,
            vector_store_collection=self._vector_store_collection,
            embedding_model=self._embedding_model,
            llm_client=self._llm_client,
            top_k=self._top_k,
            temperature=self._temperature,
            conversation_history=conversation_history,
            return_context=return_context,
        )

        timestamp = datetime.now(timezone.utc)
        
        rag_result = RAGResult(
            text=result["response"],
            sources=result.get("saved", result.get("sources", []))
            if isinstance(result, dict)
            else [],
            conversation_id="",  # Will be set by the route handler
            timestamp=timestamp,
        )
        
        # Add context_chunks to result if requested (for evaluation)
        if return_context and isinstance(result, dict) and "context_chunks" in result:
            rag_result.context_chunks = result["context_chunks"]
        
        return rag_result