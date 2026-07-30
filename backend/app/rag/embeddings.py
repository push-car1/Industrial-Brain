from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings


_embeddings_instance = None


def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        model_name = f"sentence-transformers/{settings.embedding_model}"
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": settings.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_instance
