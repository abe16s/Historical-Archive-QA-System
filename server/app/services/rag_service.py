from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Any
from uuid import uuid4

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

    async def answer_question(self, query: str) -> RAGResult:
        """Run the RAG pipeline for a query and return a structured result."""
        result = rag_pipeline(
            query=query,
            vector_store_collection=self._vector_store_collection,
            embedding_model=self._embedding_model,
            llm_client=self._llm_client,
            top_k=self._top_k,
            temperature=self._temperature,
        )

        conversation_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)

        return RAGResult(
            text=result["response"],
            sources=result.get("saved", result.get("sources", []))
            if isinstance(result, dict)
            else [],
            conversation_id=conversation_id,
            timestamp=timestamp,
        )
