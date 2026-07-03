"""Configuration via environment variables (pydantic-settings)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Inference service configuration -- all values overridable via env vars."""

    # Operational mode: when True the startup security gate (default-secret /
    # missing service-token fail-fast) is skipped so local development and the
    # test-suite can run against defaults. MUST stay False in production.
    debug: bool = False

    # Service-to-service authentication (AP-4, INF-S2). Shared secret required in
    # the ``Authorization: Bearer <token>`` header on every non-probe endpoint.
    # Empty => fail-closed (protected endpoints return 503) and, outside debug,
    # the service refuses to start. Provision via INTERNAL_SERVICE_TOKEN.
    internal_service_token: str = ""

    # ONNX model
    model_path: str = "/app/models/dinov2"
    model_name: str = "dinov2_vits14"
    model_dim: int = 384
    input_size: int = 224

    # VectorDB (PostgreSQL + pgvector) -- shared cluster, own table
    vectordb_host: str = "localhost"
    vectordb_port: int = 5432
    vectordb_database: str = "kamerplanter_vectors"
    vectordb_username: str = "postgres"
    # Default is a placeholder only — the startup gate refuses to boot with it
    # outside debug mode (AP-4, INF-S4).
    vectordb_password: str = "changeme"
    vectordb_pool_min_size: int = 1
    vectordb_pool_max_size: int = 5

    # Confidence calibration (REQ-029-A 3.5) -- justified via own evaluation, not literature
    confidence_auto_accept: float = 0.85
    confidence_show_results: float = 0.10

    # REQ-044 pest few-shot: cosine floor below which a tile classification is
    # dropped (returned findings are still subject to the backend's abstention
    # gate, ABSTAIN_CONFIDENCE). Day-1 default; final calibration is WP-5.
    pest_show_results: float = 0.20

    model_config = {"env_prefix": "", "case_sensitive": False, "protected_namespaces": ()}


settings = Settings()
