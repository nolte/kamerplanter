from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.settings import settings as env_settings
from app.domain.models.system_settings import HomeAssistantSettings, SystemSettings

if TYPE_CHECKING:
    from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository


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

    @staticmethod
    def mask_token(token: str | None) -> str:
        if not token:
            return ""
        if len(token) <= 4:
            return "****"
        return "****" + token[-4:]
