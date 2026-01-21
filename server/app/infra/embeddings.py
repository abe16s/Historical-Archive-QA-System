"""
Text embedding utilities.

This module provides a thin wrapper around sentence-transformers
so that the rest of the codebase can depend on a simple interface.
"""

from typing import List

from sentence_transformers import SentenceTransformer


def initialize_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """
    Initialize the embedding model.

    Args:
        model_name: Name of the model to use

    Returns:
        The embedding model
    """
    device = 'cpu'
    try:
        model = SentenceTransformer(model_name, device=device)
        # Explicitly move to CPU if needed
        model = model.to(device)
        return model
    except Exception as e:
        # If there's still an issue, try clearing cache and retrying
        raise RuntimeError(f"Failed to load embedding model: {e}. Try clearing cache: rm -rf ~/.cache/huggingface/")
def generate_embeddings(texts: List[str], model) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed
        model: The embedding model (from initialize_embedding_model)

    Returns:
        List of embedding vectors (each is a list of floats)
    """
    return model.encode(texts).tolist()


def generate_embedding(text: str, model) -> List[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Text string to embed
        model: The embedding model

    Returns:
        Embedding vector as a list of floats
    """
    return generate_embeddings([text], model)[0]


