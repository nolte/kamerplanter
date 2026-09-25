from datetime import datetime

from pydantic import BaseModel, Field


class HomeAssistantSettings(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = None


class PlantIdentificationSettings(BaseModel):
    """Instance-wide plant identification settings (REQ-029 Phase 1).

    The Pl@ntNet API key applies to the whole instance (free-tier key,
    not tenant-scoped). An empty value means "fall back to the environment
    variable ``PLANTNET_API_KEY``" — see ``SystemSettingsService``.
    """

    plantnet_api_key: str = ""


class StorageSettings(BaseModel):
    """Instance-wide object-storage backend selection (NFR-013 §4.1).

    Only **non-secret** fields are persisted here. The S3 credentials
    (``access_key_id`` / ``secret_access_key``) are *deliberately not* part of
    this model: per NFR-013 §4.1 they MUST come from the environment / External
    Secrets Operator and are never stored in ArangoDB. An empty field means
    "fall back to the corresponding ``STORAGE_*`` environment variable" — see
    ``SystemSettingsService.get_effective_storage_settings``.

    ``backend = None`` means "use the env default" (``STORAGE_BACKEND``,
    default ``local-fs``). All other ``None`` fields likewise fall back to env.
    """

    backend: str | None = None  # "local-fs" | "s3" | None (= env default)
    # local-fs (non-secret)
    local_fs_root: str | None = None
    local_fs_public_base_url: str | None = None
    # s3 (non-secret only — credentials stay in env / ESO)
    s3_endpoint_url: str | None = None
    s3_region: str | None = None
    s3_bucket: str | None = None
    s3_use_path_style: bool | None = None
    s3_kms_key_id: str | None = None
    s3_force_tls: bool | None = None


class WeatherProviderSettings(BaseModel):
    """Instance-wide public weather-provider configuration (REQ-046 follow-up).

    Central admin override for the public weather services (Open-Meteo, DWD,
    OpenWeatherMap), mirroring the Home-Assistant DB-override + env-fallback
    pattern. A ``None`` field means "fall back to the corresponding environment
    variable" — see ``WeatherSettingsService.get_effective_weather_settings``.

    The global OpenWeatherMap key is stored **Fernet-encrypted**
    (``openweathermap_global_api_key_encrypted``) — never plaintext. It acts as
    the instance-wide fallback key when a site has not configured its own
    per-site OpenWeatherMap key.
    """

    open_meteo_enabled: bool | None = None
    open_meteo_base_url: str | None = None
    dwd_enabled: bool | None = None
    dwd_base_url: str | None = None
    openweathermap_enabled: bool | None = None
    openweathermap_base_url: str | None = None
    # Fernet ciphertext of the global OWM fallback key (never plaintext).
    openweathermap_global_api_key_encrypted: str | None = None
    fetch_timeout_s: int | None = None
    default_public_source: str | None = None


class PestPrototypeOrphanSweepRecord(BaseModel):
    """#1771 — what the pest-prototype orphan sweep removed (counts only, no keys)."""

    first_run_at: datetime | None = None
    last_run_at: datetime | None = None
    #: Contribution keys the index held in the last run.
    last_examined: int = 0
    #: Of those, keys without a ``pest_image_contributions`` document.
    last_orphaned: int = 0
    #: Prototype rows the last run deleted (a key can have several rows).
    last_removed: int = 0
    #: Prototype rows every run so far deleted together.
    total_removed: int = 0
    #: Store binding of the last run (``inference_service`` / ``noop``).
    binding: str | None = None


class SystemSettings(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    home_assistant: HomeAssistantSettings = Field(default_factory=HomeAssistantSettings)
    plant_identification: PlantIdentificationSettings = Field(
        default_factory=PlantIdentificationSettings,
    )
    storage: StorageSettings = Field(default_factory=StorageSettings)
    weather_providers: WeatherProviderSettings = Field(default_factory=WeatherProviderSettings)
    #: #1753 — set when the first user contribution was written to the DINOv2
    #: reference index; never cleared. See ``IReferenceContributionMarker``.
    reference_contributions_since: datetime | None = None
    #: #1759 — set before the first promoted pest-image contribution was
    #: indexed as a recognition prototype; never cleared. See
    #: ``IPestPrototypeContributionMarker``.
    pest_prototype_contributions_since: datetime | None = None
    #: #1771 — the last completed run of the pest-prototype orphan sweep.
    pest_prototype_orphan_sweep: PestPrototypeOrphanSweepRecord | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
