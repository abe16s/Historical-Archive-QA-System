from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone
import chromadb
from chromadb.config import Settings
from app.infra.embeddings import generate_embeddings, generate_embedding


def initialize_vector_store(persist_directory: str = "./vector_db"):
    """Initialize the vector database."""
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(name="documents")
    return client, collection


def add_documents_to_vector_store(
    documents: List[Dict[str, Any]],
    collection,
    embedding_model,
):
    """Add documents to the vector store."""
    texts = [doc["content"] for doc in documents]
    embeddings = generate_embeddings(texts, embedding_model)
    ids = [str(uuid.uuid4()) for _ in range(len(documents))]

    indexed_at = datetime.now(timezone.utc).isoformat()
    metadatas: List[Dict[str, Any]] = []
    for doc in documents:
        md = doc.get("metadata", {}).copy()
        md.setdefault("indexed_at", indexed_at)
        metadatas.append(md)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def search_similar_documents(
    query: str,
    collection,
    embedding_model,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Search for similar documents in the vector store."""
    query_embedding = generate_embedding(query, embedding_model)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    formatted_results: List[Dict[str, Any]] = []
    if results.get("documents") and len(results["documents"]) > 0:
        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else [{}] * len(documents)
        ids = results.get("ids", [[]])[0] if results.get("ids") else [None] * len(documents)
        distances = results.get("distances", [[]])[0] if results.get("distances") else [None] * len(documents)

        for doc, metadata, doc_id, distance in zip(documents, metadatas, ids, distances):
            similarity = None
            if distance is not None:
                similarity = max(0.0, 1.0 - float(distance))
            
            formatted_results.append(
                {
                    "text": doc,
                    "content": doc,  # Keep both for compatibility
                    "metadata": metadata or {},
                    "id": doc_id,
                    "distance": distance,
                    "similarity": similarity,
                }
            )

    return formatted_results


def list_indexed_documents(collection) -> List[Dict[str, Any]]:
    """List high-level information about indexed documents in the vector store."""
    results = collection.get(include=["metadatas"])

    indexed: Dict[str, Dict[str, Any]] = {}

    raw_metadatas = results.get("metadatas") or []

    if raw_metadatas and isinstance(raw_metadatas[0], dict):
        metadatas_iterable = [raw_metadatas]
    else:
        metadatas_iterable = raw_metadatas

    for metadatas in metadatas_iterable:
        for md in metadatas:
            if not isinstance(md, dict) or not md:
                continue
            source = md.get("source")
            if not source:
                continue
            indexed_at = md.get("indexed_at")

            if source not in indexed:
                indexed[source] = {
                    "source": source,
                    "chunks_count": 0,
                    "last_indexed_at": indexed_at,
                }

            indexed[source]["chunks_count"] += 1

            if indexed_at:
                current_last = indexed[source]["last_indexed_at"]
                if not current_last or indexed_at > current_last:
                    indexed[source]["last_indexed_at"] = indexed_at

    return list(indexed.values())


def delete_documents_by_source(collection, source: str) -> int:
    """Delete all document chunks in the vector store for a given source."""
    try:
        all_results = collection.get(include=["metadatas"])
        all_ids = all_results.get("ids") or []
        all_metadatas = all_results.get("metadatas") or []
        
        if all_ids and isinstance(all_ids[0], list):
            all_ids = [id for sublist in all_ids for id in sublist]
        if all_metadatas and isinstance(all_metadatas[0], list):
            all_metadatas = [md for sublist in all_metadatas for md in sublist]
        
        matching_ids = []
        for idx, metadata in enumerate(all_metadatas):
            if isinstance(metadata, dict) and metadata.get("source") == source:
                if idx < len(all_ids):
                    matching_ids.append(all_ids[idx])
        
        if matching_ids:
            collection.delete(ids=matching_ids)
            return len(matching_ids)
        
        return 0
    except Exception as e:
        print(f"Error deleting documents by source '{source}': {e}")
        raise


