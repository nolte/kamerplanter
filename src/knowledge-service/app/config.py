"""Configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Knowledge service configuration — all values overridable via env vars."""

    # VectorDB (PostgreSQL + pgvector)
    vectordb_host: str = "localhost"
    vectordb_port: int = 5432
    vectordb_database: str = "kamerplanter_vectors"
    vectordb_username: str = "postgres"
    vectordb_password: str = "changeme"
    vectordb_pool_min_size: int = 1
    vectordb_pool_max_size: int = 5

    # Knowledge YAML path
    knowledge_path: str = "/app/knowledge"

    # Embedding service
    embedding_service_url: str = "http://embedding-service:8080"
    embedding_model: str = "multilingual-e5-large"

    # LLM
    llm_provider: str = "ollama"  # anthropic | ollama | openai_compatible
    llm_api_url: str = "http://ollama:11434"
    llm_api_key: str = ""
    llm_model: str = "gemma3:12b"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1

    # Reranker service (optional — disabled when URL is empty)
    reranker_url: str = ""
    reranker_initial_k: int = 20
    reranker_top_k: int = 5

    # Answer verification (optional second LLM pass)
    answer_verification: bool = False

    # RAG language defaults
    rag_doc_language: str = "de"
    rag_prompt_language: str = "de"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
