from typing import Any

from app.config.settings import settings as env_settings
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from app.domain.models.system_settings import (
    HomeAssistantSettings,
    PlantIdentificationSettings,
    StorageSettings,
    SystemSettings,
)

#: Supported storage backends (NFR-013 §3.1). Validated on update so the UI
#: cannot persist an unknown backend that would later break the adapter build.
_VALID_STORAGE_BACKENDS = ("local-fs", "s3")


class SystemSettingsService:
    def __init__(self, repo: ArangoSystemSettingsRepository) -> None:
        self._repo = repo

    def get_settings(self) -> SystemSettings:
        stored = self._repo.get()
        return stored if stored else SystemSettings()

    def update_ha_settings(
        self,
        ha_url: str | None,
        ha_access_token: str | None,
        ha_timeout: int | None,
    ) -> SystemSettings:
        stored = self._repo.get()
        if stored is None:
            stored = SystemSettings()

        ha = stored.home_assistant
        if ha_url is not None:
            ha.ha_url = ha_url
        if ha_access_token is not None:
            ha.ha_access_token = ha_access_token
        if ha_timeout is not None:
            ha.ha_timeout = ha_timeout

        stored.home_assistant = ha
        return self._repo.upsert(stored)

    def delete_ha_settings(self) -> bool:
        stored = self._repo.get()
        if stored is None:
            return False
        stored.home_assistant = HomeAssistantSettings()
        self._repo.upsert(stored)
        return True

    def get_effective_ha_settings(self) -> dict[str, str | int]:
        """Return effective HA settings: DB values take precedence over env."""
        stored = self.get_settings()
        ha = stored.home_assistant

        ha_url = ha.ha_url if ha.ha_url else env_settings.ha_url
        ha_access_token = ha.ha_access_token if ha.ha_access_token else env_settings.ha_access_token
        ha_timeout = ha.ha_timeout if ha.ha_timeout is not None else env_settings.ha_timeout

        return {
            "ha_url": ha_url,
            "ha_access_token": ha_access_token,
            "ha_timeout": ha_timeout,
        }

    def get_ha_settings_with_source(self) -> dict:
        """Return effective HA settings with source info for each field."""
        stored = self.get_settings()
        ha = stored.home_assistant

        def _resolve(db_val: str | int | None, env_val: str | int, default: str | int | None = None) -> tuple:
            if db_val is not None and db_val != "":
                return db_val, "db"
            if env_val:
                return env_val, "env"
            return default if default is not None else env_val, "default"

        ha_url, url_source = _resolve(ha.ha_url, env_settings.ha_url)
        ha_token, token_source = _resolve(ha.ha_access_token, env_settings.ha_access_token)
        ha_timeout, timeout_source = _resolve(ha.ha_timeout, env_settings.ha_timeout, env_settings.ha_timeout)

        return {
            "ha_url": ha_url,
            "source_ha_url": url_source,
            "ha_access_token": ha_token,
            "source_ha_access_token": token_source,
            "ha_timeout": ha_timeout,
            "source_ha_timeout": timeout_source,
        }

    # ── REQ-029 Pl@ntNet / plant identification ─────────────────────────

    def update_plant_identification_settings(
        self,
        plantnet_api_key: str | None,
    ) -> SystemSettings:
        """Persist the instance-wide Pl@ntNet API key (DB overrides env)."""
        stored = self._repo.get()
        if stored is None:
            stored = SystemSettings()

        pi = stored.plant_identification
        if plantnet_api_key is not None:
            pi.plantnet_api_key = plantnet_api_key

        stored.plant_identification = pi
        return self._repo.upsert(stored)

    def delete_plant_identification_settings(self) -> bool:
        """Clear the DB Pl@ntNet key so resolution falls back to the env value."""
        stored = self._repo.get()
        if stored is None:
            return False
        stored.plant_identification = PlantIdentificationSettings()
        self._repo.upsert(stored)
        return True

    def get_effective_plantnet_api_key(self) -> str:
        """Return the effective Pl@ntNet key: DB value takes precedence over env."""
        stored = self.get_settings()
        db_key = stored.plant_identification.plantnet_api_key
        if db_key:
            return db_key
        return env_settings.plantnet_api_key

    def get_plantnet_settings_with_source(self) -> dict:
        """Return effective Pl@ntNet key with its source (``db``/``env``/``none``)."""
        stored = self.get_settings()
        db_key = stored.plant_identification.plantnet_api_key

        if db_key:
            return {"plantnet_api_key": db_key, "source_plantnet_api_key": "db"}
        if env_settings.plantnet_api_key:
            return {
                "plantnet_api_key": env_settings.plantnet_api_key,
                "source_plantnet_api_key": "env",
            }
        return {"plantnet_api_key": "", "source_plantnet_api_key": "none"}

    # ── NFR-013 Object storage backend selection (§4.1) ─────────────────
    #
    # SECRET HANDLING (NFR-013 §4.1, variant "a" — env/ESO only):
    #   The S3 access_key_id / secret_access_key are NEVER persisted to the
    #   database. They are resolved exclusively from the environment (supplied
    #   by the External Secrets Operator in production). The settings UI sets
    #   only non-secret fields; effective resolution layers the DB override on
    #   top of the env defaults, then injects the env-only credentials when an
    #   ad-hoc adapter is built for the connection test.

    def update_storage_settings(
        self,
        *,
        backend: str | None = None,
        local_fs_root: str | None = None,
        local_fs_public_base_url: str | None = None,
        s3_endpoint_url: str | None = None,
        s3_region: str | None = None,
        s3_bucket: str | None = None,
        s3_use_path_style: bool | None = None,
        s3_kms_key_id: str | None = None,
        s3_force_tls: bool | None = None,
    ) -> SystemSettings:
        """Persist the active backend + its non-secret config (DB overrides env).

        Raises ``ValueError`` for an unknown ``backend`` so the API layer can
        return a 422 rather than persisting a value the adapter cannot build.
        """
        if backend is not None and backend not in _VALID_STORAGE_BACKENDS:
            raise ValueError(
                f"Unknown storage backend '{backend}'. Allowed: {', '.join(_VALID_STORAGE_BACKENDS)}.",
            )

        stored = self._repo.get() or SystemSettings()
        st = stored.storage

        if backend is not None:
            st.backend = backend
        if local_fs_root is not None:
            st.local_fs_root = local_fs_root
        if local_fs_public_base_url is not None:
            st.local_fs_public_base_url = local_fs_public_base_url
        if s3_endpoint_url is not None:
            st.s3_endpoint_url = s3_endpoint_url
        if s3_region is not None:
            st.s3_region = s3_region
        if s3_bucket is not None:
            st.s3_bucket = s3_bucket
        if s3_use_path_style is not None:
            st.s3_use_path_style = s3_use_path_style
        if s3_kms_key_id is not None:
            st.s3_kms_key_id = s3_kms_key_id
        if s3_force_tls is not None:
            st.s3_force_tls = s3_force_tls

        stored.storage = st
        return self._repo.upsert(stored)

    def get_effective_storage_settings(self) -> dict[str, Any]:
        """Return effective storage config: DB override on top of env.

        The returned dict carries **only non-secret** fields plus the resolved
        credential *presence* flags. Raw credentials are never included here —
        they are injected directly from env when building the test adapter
        (``build_storage_test_adapter``), so they cannot leak through a response.
        """
        st = self.get_settings().storage

        def _resolve(db_val: Any, env_val: Any) -> Any:
            return db_val if db_val is not None and db_val != "" else env_val

        return {
            "backend": _resolve(st.backend, env_settings.storage_backend),
            "local_fs_root": _resolve(st.local_fs_root, env_settings.storage_local_fs_root),
            "local_fs_public_base_url": _resolve(
                st.local_fs_public_base_url, env_settings.storage_local_fs_public_base_url
            ),
            "s3_endpoint_url": _resolve(st.s3_endpoint_url, env_settings.storage_s3_endpoint_url),
            "s3_region": _resolve(st.s3_region, env_settings.storage_s3_region),
            "s3_bucket": _resolve(st.s3_bucket, env_settings.storage_s3_bucket),
            "s3_use_path_style": (
                st.s3_use_path_style if st.s3_use_path_style is not None else env_settings.storage_s3_use_path_style
            ),
            "s3_kms_key_id": _resolve(st.s3_kms_key_id, env_settings.storage_s3_kms_key_id),
            "s3_force_tls": (st.s3_force_tls if st.s3_force_tls is not None else env_settings.storage_s3_force_tls),
            # Credential presence only — never the values (NFR-013 §4.1).
            "s3_access_key_id_configured": bool(env_settings.storage_s3_access_key_id),
            "s3_secret_access_key_configured": bool(env_settings.storage_s3_secret_access_key),
        }

    def get_storage_settings_with_source(self) -> dict[str, Any]:
        """Effective storage settings plus a per-field source (``db``/``env``)."""
        st = self.get_settings().storage
        effective = self.get_effective_storage_settings()

        def _source(db_val: Any) -> str:
            return "db" if db_val is not None and db_val != "" else "env"

        return {
            **effective,
            "source_backend": _source(st.backend),
            "source_local_fs_root": _source(st.local_fs_root),
            "source_local_fs_public_base_url": _source(st.local_fs_public_base_url),
            "source_s3_endpoint_url": _source(st.s3_endpoint_url),
            "source_s3_region": _source(st.s3_region),
            "source_s3_bucket": _source(st.s3_bucket),
            "source_s3_use_path_style": "db" if st.s3_use_path_style is not None else "env",
            "source_s3_kms_key_id": _source(st.s3_kms_key_id),
            "source_s3_force_tls": "db" if st.s3_force_tls is not None else "env",
        }

    def delete_storage_settings(self) -> bool:
        """Reset the DB storage override so resolution falls back to env vars."""
        stored = self._repo.get()
        if stored is None:
            return False
        stored.storage = StorageSettings()
        self._repo.upsert(stored)
        return True

    @staticmethod
    def mask_token(token: str | None) -> str:
        if not token:
            return ""
        if len(token) <= 4:
            return "****"
        return "****" + token[-4:]
