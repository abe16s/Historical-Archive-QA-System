from typing import List
from sentence_transformers import SentenceTransformer


def initialize_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Initialize the embedding model."""
    device = 'cpu'
    try:
        model = SentenceTransformer(model_name, device=device)
        model = model.to(device)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load embedding model: {e}. Try clearing cache: rm -rf ~/.cache/huggingface/")

def generate_embeddings(texts: List[str], model) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    return model.encode(texts).tolist()


def generate_embedding(text: str, model) -> List[float]:
    """Generate embedding for a single text."""
    return generate_embeddings([text], model)[0]
