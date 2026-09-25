"""Configuration via environment variables."""

from typing import Final

from pydantic_settings import BaseSettings

#: Characters the reranker may score per search: ``reranker_initial_k`` x
#: ``reranker_max_document_chars`` (15 x 500), the measured envelope that fits
#: the sidecar's 25 s deadline (docker/reranker-service/limits.py
#: MAX_INFERENCE_SECONDS) at the chart's 2 CPUs. Raise it only with a new
#: measurement — the backend guard tests/unit/guards/test_ml_sidecar_limits.py
#: holds the defaults and every deployment file to it.
#:
#: Measured 2026-09-25 (#1751). Cost is model compute, ~6 ms per pair token.
#: The old 20 full documents (pairs capped at 512 tokens; 44 % of the real
#: pairs hit that cap) needed ~54 s: 10/10 HTTP probes answered 503 timeout
#: after 25.6-28.6 s, so reranking never ran and every search paid the wait.
#: 500 characters give pairs of median 166, max 222 tokens; a real HTTP probe
#: with all 100 benchmark questions (bge image, ``--cpus 2 -m 4g``) answered
#: 100/100 with 200, p50 12.9 s, p90 15.0 s, max 16.0 s. 10 x 800 answered
#: 100/100 too, but at max 24.4 s under host load — no margin.
#: Topic recall of the returned context over 54 benchmark questions:
#: top_k=5 — no rerank 0.927, 10 x 800 0.969, 15 x 500 0.974, unbounded
#: (512 tokens, k=20) 0.982; top_k=10 — 0.978, 0.978, 0.979, 0.995.
RERANK_SCORED_CHARS_BUDGET: Final = 7500


class Settings(BaseSettings):
    """Knowledge service configuration — all values overridable via env vars."""

    # Operational mode: when True the startup security gate (default-secret /
    # missing service-token fail-fast) is skipped so local development and the
    # test-suite can run against defaults. MUST stay False in production.
    debug: bool = False

    # Service-to-service authentication (AP-4, INF-S1). Shared secret required in
    # the ``Authorization: Bearer <token>`` header on every non-probe endpoint.
    # Empty => fail-closed (protected endpoints return 503) and, outside debug,
    # the service refuses to start. Provision via INTERNAL_SERVICE_TOKEN.
    internal_service_token: str = ""

    # VectorDB (PostgreSQL + pgvector)
    vectordb_host: str = "localhost"
    vectordb_port: int = 5432
    vectordb_database: str = "kamerplanter_vectors"
    vectordb_username: str = "postgres"
    # Default is a placeholder only — the startup gate refuses to boot with it
    # outside debug mode (AP-4, INF-S4).
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
    # Budget (#1751): see RERANK_SCORED_CHARS_BUDGET above. Both must stay
    # literal ints: the backend guard tests/unit/guards/test_ml_sidecar_limits.py
    # reads them from this file's AST and holds their product to the budget.
    reranker_initial_k: int = 15
    reranker_max_document_chars: int = 500
    reranker_top_k: int = 5

    # Answer verification (optional second LLM pass)
    answer_verification: bool = False

    # RAG language defaults
    rag_doc_language: str = "de"
    rag_prompt_language: str = "de"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
