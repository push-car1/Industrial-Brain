import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Industrial Knowledge Brain"
    app_version: str = "1.0.0"
    debug: bool = True

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    llm_model: str = os.getenv("LLM_MODEL", "mistral:7b")
    llm_temperature: float = 0.1
    llm_max_tokens: int = 128

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_device: str = "cpu"

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database: str = "neo4j"

    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "/app/data/embeddings")
    chroma_collection_name: str = "industrial_docs"

    max_chunk_size: int = 512
    chunk_overlap: int = 64
    max_file_size_mb: int = 50
    allowed_extensions: list = [".pdf", ".png", ".jpg", ".jpeg", ".csv", ".xlsx", ".txt", ".md"]

    retriever_top_k: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
