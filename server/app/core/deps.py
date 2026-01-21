from functools import lru_cache

from app.core.config import settings
from app.infra.rag_engine import initialize_llm
from app.infra.vector_store import initialize_vector_store
from app.infra.embeddings import initialize_embedding_model
from app.services.rag_service import RAGService
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService


@lru_cache
def get_vector_store_collection():
    """
    Lazily initialize and cache the ChromaDB collection.
    """
    client, collection = initialize_vector_store(persist_directory=settings.VECTOR_DB_PATH)
    return collection


@lru_cache
def get_embedding_model():
    """
    Lazily initialize and cache the embedding model.
    """
    return initialize_embedding_model(model_name=settings.EMBEDDING_MODEL)


@lru_cache
def get_llm_client():
    """
    Lazily initialize and cache the LLM client (Gemini / OpenAI via LangChain).
    """
    return initialize_llm()


@lru_cache
def get_rag_service() -> RAGService:
    """
    Provide a singleton RAGService instance for use in route dependencies.
    """
    return RAGService(
        vector_store_collection=get_vector_store_collection(),
        embedding_model=get_embedding_model(),
        llm_client=get_llm_client(),
        top_k=settings.TOP_K_RETRIEVAL,
        temperature=settings.LLM_TEMPERATURE,
    )


@lru_cache
def get_storage_service() -> StorageService:
    """
    Provide a singleton StorageService for local file operations.
    """
    return StorageService()


@lru_cache
def get_document_service() -> DocumentService:
    """
    Provide a singleton DocumentService for document ingestion and listing.
    """
    return DocumentService(
        storage=get_storage_service(),
        collection=get_vector_store_collection(),
        embedding_model=get_embedding_model(),
    )


