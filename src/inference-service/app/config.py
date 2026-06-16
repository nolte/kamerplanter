"""Configuration via environment variables (pydantic-settings)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Inference service configuration -- all values overridable via env vars."""

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
    vectordb_password: str = "changeme"
    vectordb_pool_min_size: int = 1
    vectordb_pool_max_size: int = 5

    # Confidence calibration (REQ-029-A 3.5) -- justified via own evaluation, not literature
    confidence_auto_accept: float = 0.85
    confidence_show_results: float = 0.10

    model_config = {"env_prefix": "", "case_sensitive": False, "protected_namespaces": ()}


settings = Settings()
