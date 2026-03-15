from unittest.mock import MagicMock, patch

import pytest

from app.domain.models.system_settings import HomeAssistantSettings, SystemSettings
from app.domain.services.system_settings_service import SystemSettingsService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return SystemSettingsService(mock_repo)


class TestGetSettings:
    def test_returns_stored_settings(self, service, mock_repo):
        stored = SystemSettings(home_assistant=HomeAssistantSettings(ha_url="http://ha:8123"))
        mock_repo.get.return_value = stored
        result = service.get_settings()
        assert result.home_assistant.ha_url == "http://ha:8123"

    def test_returns_empty_when_none(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = service.get_settings()
        assert result.home_assistant.ha_url is None


class TestUpdateHaSettings:
    def test_sets_all_fields(self, service, mock_repo):
        mock_repo.get.return_value = None
        mock_repo.upsert.return_value = SystemSettings(
            home_assistant=HomeAssistantSettings(
                ha_url="http://ha:8123",
                ha_access_token="tok",
                ha_timeout=20,
            ),
        )
        result = service.update_ha_settings("http://ha:8123", "tok", 20)
        assert result.home_assistant.ha_url == "http://ha:8123"
        mock_repo.upsert.assert_called_once()

    def test_preserves_existing_token_when_none(self, service, mock_repo):
        existing = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_access_token="old-token"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = existing

        service.update_ha_settings("http://ha:8123", None, None)
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.home_assistant.ha_access_token == "old-token"

    def test_overwrites_url(self, service, mock_repo):
        existing = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_url="http://old:8123"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = existing

        service.update_ha_settings("http://new:8123", None, None)
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.home_assistant.ha_url == "http://new:8123"


class TestDeleteHaSettings:
    def test_clears_ha_settings(self, service, mock_repo):
        existing = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_url="http://ha:8123"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = SystemSettings()

        result = service.delete_ha_settings()
        assert result is True
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.home_assistant.ha_url is None
        assert upserted.home_assistant.ha_access_token is None

    def test_returns_false_when_none(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = service.delete_ha_settings()
        assert result is False


class TestGetEffectiveHaSettings:
    @patch("app.domain.services.system_settings_service.env_settings")
    def test_db_overrides_env(self, mock_env, service, mock_repo):
        mock_env.ha_url = "http://env:8123"
        mock_env.ha_access_token = "env-token"
        mock_env.ha_timeout = 10

        stored = SystemSettings(
            home_assistant=HomeAssistantSettings(
                ha_url="http://db:8123",
                ha_access_token="db-token",
                ha_timeout=30,
            ),
        )
        mock_repo.get.return_value = stored

        result = service.get_effective_ha_settings()
        assert result["ha_url"] == "http://db:8123"
        assert result["ha_access_token"] == "db-token"
        assert result["ha_timeout"] == 30

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_falls_back_to_env(self, mock_env, service, mock_repo):
        mock_env.ha_url = "http://env:8123"
        mock_env.ha_access_token = "env-token"
        mock_env.ha_timeout = 10

        mock_repo.get.return_value = None

        result = service.get_effective_ha_settings()
        assert result["ha_url"] == "http://env:8123"
        assert result["ha_access_token"] == "env-token"
        assert result["ha_timeout"] == 10


class TestGetHaSettingsWithSource:
    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_db_when_stored(self, mock_env, service, mock_repo):
        mock_env.ha_url = ""
        mock_env.ha_access_token = ""
        mock_env.ha_timeout = 10

        stored = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_url="http://db:8123"),
        )
        mock_repo.get.return_value = stored

        result = service.get_ha_settings_with_source()
        assert result["source_ha_url"] == "db"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_env_when_no_db(self, mock_env, service, mock_repo):
        mock_env.ha_url = "http://env:8123"
        mock_env.ha_access_token = ""
        mock_env.ha_timeout = 10

        mock_repo.get.return_value = None

        result = service.get_ha_settings_with_source()
        assert result["source_ha_url"] == "env"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_default_when_nothing(self, mock_env, service, mock_repo):
        mock_env.ha_url = ""
        mock_env.ha_access_token = ""
        mock_env.ha_timeout = 10

        mock_repo.get.return_value = None

        result = service.get_ha_settings_with_source()
        assert result["source_ha_url"] == "default"


class TestMaskToken:
    def test_mask_long_token(self):
        assert SystemSettingsService.mask_token("abcdefgh12345678") == "****5678"

    def test_mask_short_token(self):
        assert SystemSettingsService.mask_token("ab") == "****"

    def test_mask_exactly_four(self):
        assert SystemSettingsService.mask_token("abcd") == "****"

    def test_mask_five(self):
        assert SystemSettingsService.mask_token("abcde") == "****bcde"

    def test_mask_empty(self):
        assert SystemSettingsService.mask_token("") == ""

    def test_mask_none(self):
        assert SystemSettingsService.mask_token(None) == ""
