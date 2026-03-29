from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class GBIFSettings(BaseModel):
    base_url: str = "https://api.gbif.org/v1"
    rate_limit_per_minute: int = 60
    http_timeout: int = 30
    incremental_exact_threshold: int = 97
    incremental_fuzzy_threshold: int = 95
    full_exact_threshold: int = 80
    full_fuzzy_threshold: int = 90
    vernacular_languages: list[str] = ["deu", "eng"]
    backbone_dataset_key: str = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
    plantae_taxon_key: int = 6
    max_description_length: int = 2000
    max_habitat_length: int = 500


class Settings(BaseSettings):
    app_name: str = "Kamerplanter API"
    app_version: str = "1.0.0"
    debug: bool = False

    arangodb_host: str = "localhost"
    arangodb_port: int = 8529
    arangodb_database: str = "kamerplanter"
    arangodb_username: str = "root"
    arangodb_password: str = "rootpassword"

    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # REQ-027 Light-Modus
    kamerplanter_mode: Literal["light", "full"] = "full"

    perenual_api_key: str = ""
    trefle_api_key: str = ""
    enrichment_http_timeout: int = 30

    gbif: GBIFSettings = GBIFSettings()

    # REQ-023 Auth
    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    session_token_expire_hours: int = 24
    fernet_key: str = ""  # For encrypting OIDC provider secrets
    frontend_url: str = "http://localhost:5173"
    hibp_enabled: bool = False
    require_email_verification: bool = False  # Set True in production

    # Email
    email_adapter: str = "console"  # console | smtp | resend
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@kamerplanter.example"
    smtp_use_tls: bool = True

    # File uploads
    upload_dir: str = "uploads/tasks"

    # Home Assistant (optional — for sensor live-query)
    ha_url: str = ""  # e.g. "http://homeassistant.local:8123"
    ha_access_token: str = ""  # Long-Lived Access Token
    ha_timeout: int = 10  # HTTP timeout in seconds

    # TimescaleDB (optional — for sensor time-series)
    timescaledb_enabled: bool = False
    timescaledb_host: str = "localhost"
    timescaledb_port: int = 5432
    timescaledb_database: str = "kamerplanter_sensors"
    timescaledb_username: str = "postgres"
    timescaledb_password: str = "changeme"
    timescaledb_pool_min_size: int = 2
    timescaledb_pool_max_size: int = 10

    # VectorDB (optional — PostgreSQL + pgvector for AI/RAG)
    vectordb_enabled: bool = False
    vectordb_host: str = "localhost"
    vectordb_port: int = 5432
    vectordb_database: str = "kamerplanter_vectors"
    vectordb_username: str = "postgres"
    vectordb_password: str = "changeme"
    vectordb_pool_min_size: int = 1
    vectordb_pool_max_size: int = 5
    knowledge_path: str = "/app/knowledge"
    embedding_service_url: str = "http://embedding-service:8080"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Rate limiting
    rate_limit_auth: str = "20/minute"
    rate_limit_general: str = "100/minute"

    # REQ-030 Notifications
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_contact_email: str = ""
    notification_quiet_hours_default: str = "22:00-07:00"
    notification_batch_window_minutes: int = 30
    notification_escalation_days: str = "2,4,7"

    model_config = {"env_prefix": "", "case_sensitive": False, "env_nested_delimiter": "__"}


settings = Settings()
