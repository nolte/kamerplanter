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


class SystemSettings(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    home_assistant: HomeAssistantSettings = Field(default_factory=HomeAssistantSettings)
    plant_identification: PlantIdentificationSettings = Field(
        default_factory=PlantIdentificationSettings,
    )
    storage: StorageSettings = Field(default_factory=StorageSettings)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
