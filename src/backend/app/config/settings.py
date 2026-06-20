from typing import Annotated, Literal

from pydantic import BaseModel, Field
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

    # REQ-032 Print: base URL for QR codes on plant labels
    app_base_url: str = "http://localhost:5173"

    perenual_api_key: str = ""
    trefle_api_key: str = ""
    enrichment_http_timeout: int = 30

    gbif: GBIFSettings = GBIFSettings()

    # REQ-029 / REQ-029-A Phase 1 — Plant identification (all optional).
    #
    # SEC-001: every identification setting below is defined EXACTLY ONCE here.
    # Python keeps the *last* class-body assignment for a duplicated field, so a
    # second definition would silently shadow these documented defaults and make
    # the effective config non-auditable. ``test_settings_identification_defaults``
    # pins the documented effective values so a re-introduced duplicate fails CI.
    #
    # Pl@ntNet is the Phase-1 primary adapter (free tier, <=500/day).
    plantnet_api_key: str = ""  # Pl@ntNet free API key; empty = adapter disabled
    plantnet_enabled: bool = True  # disable the Pl@ntNet adapter entirely
    plantnet_base_url: str = "https://my-api.plantnet.org/v2"
    # Plant.id remains an operator opt-in (no default, never auto-primary).
    plant_id_api_key: str = ""  # Plant.id (Kindwise) — opt-in only
    plant_id_base_url: str = "https://plant.id/api/v3"
    # Self-hosted DINOv2 inference-service (REQ-029-A Phase 2 priority-1 adapter).
    # Disabled by default until the service is deployed (WS-6); while disabled the
    # local adapter is unavailable and the registry falls back to Pl@ntNet.
    inference_service_enabled: bool = False
    inference_service_url: str = "http://kamerplanter-recognition:8000"
    # Config-driven adapter priority (REQ-029-A §0.1.1 point 1) — never hard-coded.
    # Phase-1 primary adapter is Pl@ntNet (REQ-029-A §0.1.1: DINOv2/local_embedding
    # is Phase 2). Phase 2 switches this to "local_embedding" without touching
    # engine/service/API.
    identification_primary_adapter: str = "plantnet"
    identification_http_timeout: int = 30
    identification_confidence_auto_accept: float = 0.85
    identification_confidence_min_show: float = 0.10
    identification_max_image_size_mb: int = 5
    # Per-user daily rate limit (REQ-029 §7). SEC-003: a sensible per-user floor so
    # a single account cannot consume the whole shared adapter free-tier quota.
    # ``0`` falls back to the adapter's own free-tier default.
    identification_rate_limit_per_user_day: int = 50
    # REQ-034 §4a.3 — operator opt-in for the *external* recognition path
    # (Pl@ntNet) in Light mode. In Light mode (REQ-027) there is no consent
    # subsystem, so sending a gallery photo to a third party requires a deliberate
    # operator decision. Off by default → in Light mode only the self-hosted
    # ``local_embedding`` path is usable (and only once Phase 2 is enabled).
    identification_external_in_light_mode: bool = False
    # REQ-029-A §4 reference-image acquisition (DINOv2 index population).
    reference_image_max_candidates: int = 40  # n_max queried per species
    reference_image_min_usable: int = 5  # below this a species is "not recognizable"
    reference_image_min_dimension: int = 224  # px on the shorter edge (model input)
    reference_image_max_aspect_ratio: float = 3.0  # reject extreme crops/banners
    reference_image_use_wikimedia: bool = True  # query Wikimedia Commons as a 2nd source
    wikimedia_commons_api_url: str = "https://commons.wikimedia.org/w/api.php"

    # REQ-044 Bildbasierte Schädlingserkennung (alle optional, Default-Privacy §8).
    # Das Feature ist standardmäßig AUS; der Self-Hosted-Symptom-Adapter ist der
    # Default-Adapter, der Cloud-Adapter ist opt-in und einwilligungspflichtig.
    pest_detection_enabled: bool = False  # master switch (Default-Privacy)
    # Self-hosted symptom adapter (Modus 2, Phase-1-Default). Nutzt den
    # REQ-029-A-Inferenz-Service; die trainierten Few-Shot-Prototypen sind extern
    # blockiert (WP-3) → bis dahin nur aktiv, wenn der Service erreichbar ist.
    pest_detection_symptom_enabled: bool = True
    # Self-hosted detector (Modus 1, Phase 2 — D-FINE/RF-DETR ONNX, WP-1/2/3).
    pest_detection_detector_enabled: bool = False
    # Demo adapter (no external service, no real model). Lets operators preview
    # the full pest-detection UI flow while the trained backend is externally
    # blocked (WP-1/2/3). Returns clearly-labelled placeholder findings. Off by
    # default; never use in production for real decisions.
    pest_detection_demo_enabled: bool = False
    # Cloud adapter (Kindwise plant.health, opt-in, WP-7). Default aus, bis die
    # Vertrags-/DSGVO-Fragen (WP-7 Show-Stopper) geklärt sind.
    pest_detection_cloud_enabled: bool = False
    pest_detection_cloud_api_key: str = ""
    pest_detection_cloud_base_url: str = "https://plant.id/api/v3"
    # Config-driven primary adapter (analog identification) — nie hart kodiert.
    pest_detection_primary_adapter: str = "local_pest_symptom"
    pest_detection_max_image_size_mb: int = 8  # §6 multipart upload limit
    # EXIF-Strip behält für das Tiling mehr Auflösung als der ID-Pfad (1024).
    pest_detection_max_image_dimension: int = 2048
    pest_detection_tile_size: int = 512  # §4.3 / WP-3.3 SAHI slice
    pest_detection_tile_overlap: float = 0.2  # §4.3 / WP-3.3 SAHI overlap

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
    cookie_secure: bool = True  # Set False for HTTP-only E2E environments

    # Email
    email_adapter: str = "console"  # console | smtp | resend
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@kamerplanter.example"
    smtp_use_tls: bool = True

    # File uploads
    upload_dir: str = "/data/uploads/tasks"

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

    # Knowledge Service (optional — standalone RAG microservice)
    knowledge_service_enabled: bool = False
    knowledge_service_url: str = "http://knowledge-service:8000"

    # mDNS / Zeroconf Discovery
    mdns_enabled: bool = False  # Enable only for local/on-premise deployments (opt-in)
    # Auto-generated UUID prefix if empty; alphanumeric + hyphens only, max 64 chars
    instance_id: Annotated[str, Field(max_length=64, pattern=r"^[a-zA-Z0-9\-]*$")] = ""

    # Rate limiting
    rate_limit_auth: str = "20/minute"
    rate_limit_general: str = "100/minute"

    # REQ-025 Privacy / GDPR
    erasure_tombstone_salt: str = ""  # NFR-011 §4: must be >= 32 chars in production
    privacy_data_controller_name: str = "Kamerplanter Operator"
    privacy_data_controller_email: str = "privacy@kamerplanter.example"
    privacy_export_retention_hours: int = 72  # NFR-011 R-05
    privacy_hard_delete_after_days: int = 90  # NFR-011 R-01
    privacy_email_change_ttl_hours: int = 24

    # REQ-030 Notifications
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_contact_email: str = ""
    # SEC-001 — optional operator allowlist for Web Push endpoints (SSRF hardening).
    # Comma-separated host suffixes (e.g. "fcm.googleapis.com,updates.push.services.mozilla.com").
    # Empty (default) → fall back to https + private-IP rejection so self-hosted push works.
    pwa_push_endpoint_allowed_hosts: str = ""
    notification_quiet_hours_default: str = "22:00-07:00"
    notification_batch_window_minutes: int = 30
    notification_escalation_days: str = "2,4,7"

    # NFR-013 Object storage (§4.1) — defaults target the local-fs backend.
    storage_backend: str = "local-fs"  # local-fs | s3
    storage_max_file_size_mb: int = 25
    storage_presign_ttl_seconds: int = 900
    storage_virus_scan_enabled: bool = False
    storage_virus_scan_endpoint: str = ""
    # NFR-013 §5.1 step 1 — per-tenant attachment quota (0 = unlimited).
    storage_tenant_quota_mb: int = 2048
    # NFR-013 §5.1 step 7 — strip image EXIF/GPS on upload by default.
    storage_strip_exif: bool = True
    # REQ-034 §3 (SR-004) — max gallery photos per plant instance (0 = unlimited).
    storage_max_photos_per_instance: int = 50
    # REQ-034 §4.3 (SR-005a) — per-tenant cap on open ``pending_review``
    # user-contributed DINOv2 reference embeddings (index-poisoning guard).
    reference_contribution_pending_limit: int = 100
    # NFR-013 §5.2 — global MIME whitelist (CSV string). Per-category overrides
    # are read from ``storage_allowed_mime_types_<category>`` (empty = default).
    storage_allowed_mime_types: str = (
        "image/jpeg,image/png,image/webp,image/heic,application/pdf,text/csv,application/zip"
    )
    storage_allowed_mime_types_diary: str = ""
    storage_allowed_mime_types_ipm: str = ""
    storage_allowed_mime_types_harvest: str = ""
    storage_allowed_mime_types_post_harvest: str = ""
    storage_allowed_mime_types_plant: str = ""
    storage_allowed_mime_types_id_recognition: str = ""
    storage_allowed_mime_types_task: str = ""
    storage_allowed_mime_types_import: str = "text/csv,application/zip"
    storage_allowed_mime_types_export: str = "application/pdf,text/csv,application/zip"
    storage_allowed_mime_types_tenant_export: str = "application/pdf,text/csv,application/zip"
    # local-fs backend
    storage_local_fs_root: str = "/data/attachments"
    storage_local_fs_public_base_url: str = ""
    # Signing secret for local-fs token URLs; falls back to jwt_secret_key /
    # fernet_key when left empty (resolved at adapter construction).
    storage_localfs_signing_secret: str = ""
    # s3 backend
    storage_s3_endpoint_url: str = ""
    storage_s3_region: str = ""
    storage_s3_bucket: str = ""
    storage_s3_access_key_id: str = ""
    storage_s3_secret_access_key: str = ""
    storage_s3_use_path_style: bool = False
    storage_s3_kms_key_id: str = ""
    storage_s3_force_tls: bool = True
    # SSRF guard for the admin "test connection" probe (SEC-002, NFR-013).
    # Link-local / cloud-metadata ranges (169.254.0.0/16, fd00:ec2::254) are
    # ALWAYS blocked. Private / loopback S3 endpoints (e.g. an in-cluster MinIO
    # at http://minio.default.svc or http://localhost:9000) are legitimate but
    # are only probed when this opt-in is enabled by the operator.
    storage_s3_allow_private_endpoint: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False, "env_nested_delimiter": "__"}

    def allowed_mime_types_for_category(self, category: str) -> list[str]:
        """Resolve the allowed-MIME whitelist for an attachment category (NFR-013 §5.2).

        Resolution order:
          1. An explicit ``storage_allowed_mime_types_<category>`` override, if set.
          2. For photo categories without an override, an image-only subset of
             the global whitelist (``image/jpeg,png,webp,heic``).
          3. The global ``storage_allowed_mime_types`` list.
        """
        global_types = _split_csv(self.storage_allowed_mime_types)

        override = _split_csv(getattr(self, f"storage_allowed_mime_types_{category}", ""))
        if override:
            return override

        if category in _PHOTO_CATEGORIES:
            image_types = [m for m in global_types if m in _PHOTO_MIME_TYPES]
            return image_types or global_types

        return global_types


# Categories that semantically only accept images (NFR-013 §5.2). Without an
# explicit override these fall back to the image-only subset of the whitelist.
_PHOTO_CATEGORIES: frozenset[str] = frozenset(
    {"diary", "ipm", "harvest", "post_harvest", "plant", "id_recognition", "task"}
)
_PHOTO_MIME_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"})


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


settings = Settings()
