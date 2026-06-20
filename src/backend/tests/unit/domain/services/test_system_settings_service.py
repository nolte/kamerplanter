from unittest.mock import MagicMock, patch

import pytest

from app.domain.models.system_settings import (
    HomeAssistantSettings,
    PlantIdentificationSettings,
    StorageSettings,
    SystemSettings,
)
from app.domain.services.system_settings_service import SystemSettingsService


def _patch_storage_env(env):
    env.storage_backend = "local-fs"
    env.storage_local_fs_root = "/data/attachments"
    env.storage_local_fs_public_base_url = ""
    env.storage_s3_endpoint_url = ""
    env.storage_s3_region = ""
    env.storage_s3_bucket = ""
    env.storage_s3_access_key_id = ""
    env.storage_s3_secret_access_key = ""
    env.storage_s3_use_path_style = False
    env.storage_s3_kms_key_id = ""
    env.storage_s3_force_tls = True


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


class TestUpdatePlantIdentificationSettings:
    def test_sets_key(self, service, mock_repo):
        mock_repo.get.return_value = None
        mock_repo.upsert.return_value = SystemSettings(
            plant_identification=PlantIdentificationSettings(plantnet_api_key="new-key"),
        )
        result = service.update_plant_identification_settings("new-key")
        assert result.plant_identification.plantnet_api_key == "new-key"
        mock_repo.upsert.assert_called_once()

    def test_preserves_existing_when_none(self, service, mock_repo):
        existing = SystemSettings(
            plant_identification=PlantIdentificationSettings(plantnet_api_key="old-key"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = existing

        service.update_plant_identification_settings(None)
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.plant_identification.plantnet_api_key == "old-key"

    def test_does_not_touch_ha(self, service, mock_repo):
        existing = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_url="http://ha:8123"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = existing

        service.update_plant_identification_settings("key")
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.home_assistant.ha_url == "http://ha:8123"


class TestDeletePlantIdentificationSettings:
    def test_clears_key(self, service, mock_repo):
        existing = SystemSettings(
            plant_identification=PlantIdentificationSettings(plantnet_api_key="db-key"),
        )
        mock_repo.get.return_value = existing
        mock_repo.upsert.return_value = SystemSettings()

        result = service.delete_plant_identification_settings()
        assert result is True
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.plant_identification.plantnet_api_key == ""

    def test_returns_false_when_none(self, service, mock_repo):
        mock_repo.get.return_value = None
        assert service.delete_plant_identification_settings() is False


class TestGetEffectivePlantnetApiKey:
    @patch("app.domain.services.system_settings_service.env_settings")
    def test_db_overrides_env(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = "env-key"
        mock_repo.get.return_value = SystemSettings(
            plant_identification=PlantIdentificationSettings(plantnet_api_key="db-key"),
        )
        assert service.get_effective_plantnet_api_key() == "db-key"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_falls_back_to_env(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = "env-key"
        mock_repo.get.return_value = None
        assert service.get_effective_plantnet_api_key() == "env-key"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_empty_when_neither(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = ""
        mock_repo.get.return_value = None
        assert service.get_effective_plantnet_api_key() == ""


class TestGetPlantnetSettingsWithSource:
    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_db_when_stored(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = "env-key"
        mock_repo.get.return_value = SystemSettings(
            plant_identification=PlantIdentificationSettings(plantnet_api_key="db-key"),
        )
        result = service.get_plantnet_settings_with_source()
        assert result["plantnet_api_key"] == "db-key"
        assert result["source_plantnet_api_key"] == "db"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_env_when_no_db(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = "env-key"
        mock_repo.get.return_value = None
        result = service.get_plantnet_settings_with_source()
        assert result["plantnet_api_key"] == "env-key"
        assert result["source_plantnet_api_key"] == "env"

    @patch("app.domain.services.system_settings_service.env_settings")
    def test_source_none_when_nothing(self, mock_env, service, mock_repo):
        mock_env.plantnet_api_key = ""
        mock_repo.get.return_value = None
        result = service.get_plantnet_settings_with_source()
        assert result["plantnet_api_key"] == ""
        assert result["source_plantnet_api_key"] == "none"


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


class TestStorageSettings:
    def test_update_persists_non_secret_fields(self, service, mock_repo):
        mock_repo.get.return_value = None
        mock_repo.upsert.side_effect = lambda s: s
        result = service.update_storage_settings(backend="s3", s3_bucket="kp-prod", s3_region="eu-central-1")
        assert result.storage.backend == "s3"
        assert result.storage.s3_bucket == "kp-prod"
        assert result.storage.s3_region == "eu-central-1"

    def test_update_rejects_unknown_backend(self, service, mock_repo):
        mock_repo.get.return_value = None
        with pytest.raises(ValueError, match="Unknown storage backend"):
            service.update_storage_settings(backend="gdrive")
        mock_repo.upsert.assert_not_called()

    def test_effective_db_overrides_env(self, service, mock_repo):
        mock_repo.get.return_value = SystemSettings(storage=StorageSettings(backend="s3", s3_bucket="db-bucket"))
        with patch("app.domain.services.system_settings_service.env_settings") as env:
            _patch_storage_env(env)
            env.storage_s3_bucket = "env-bucket"
            effective = service.get_effective_storage_settings()
        assert effective["backend"] == "s3"
        assert effective["s3_bucket"] == "db-bucket"

    def test_effective_falls_back_to_env(self, service, mock_repo):
        mock_repo.get.return_value = SystemSettings()  # no DB override
        with patch("app.domain.services.system_settings_service.env_settings") as env:
            _patch_storage_env(env)
            env.storage_backend = "s3"
            env.storage_s3_bucket = "env-bucket"
            effective = service.get_effective_storage_settings()
        assert effective["backend"] == "s3"
        assert effective["s3_bucket"] == "env-bucket"

    def test_effective_never_exposes_raw_credentials(self, service, mock_repo):
        mock_repo.get.return_value = SystemSettings()
        with patch("app.domain.services.system_settings_service.env_settings") as env:
            _patch_storage_env(env)
            env.storage_s3_access_key_id = "AKIASECRET"
            env.storage_s3_secret_access_key = "topsecret"
            effective = service.get_effective_storage_settings()
        # Only presence flags — never the values.
        assert effective["s3_access_key_id_configured"] is True
        assert effective["s3_secret_access_key_configured"] is True
        assert "AKIASECRET" not in str(effective)
        assert "topsecret" not in str(effective)

    def test_source_reporting(self, service, mock_repo):
        mock_repo.get.return_value = SystemSettings(storage=StorageSettings(backend="s3"))
        with patch("app.domain.services.system_settings_service.env_settings") as env:
            _patch_storage_env(env)
            info = service.get_storage_settings_with_source()
        assert info["source_backend"] == "db"
        assert info["source_s3_bucket"] == "env"

    def test_delete_resets_override(self, service, mock_repo):
        mock_repo.get.return_value = SystemSettings(storage=StorageSettings(backend="s3", s3_bucket="x"))
        mock_repo.upsert.side_effect = lambda s: s
        assert service.delete_storage_settings() is True
        upserted = mock_repo.upsert.call_args[0][0]
        assert upserted.storage.backend is None
