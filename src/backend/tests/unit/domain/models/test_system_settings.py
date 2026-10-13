from app.domain.models.system_settings import HomeAssistantSettings, PlantIdentificationSettings, SystemSettings


class TestHomeAssistantSettings:
    def test_defaults(self):
        ha = HomeAssistantSettings()
        assert ha.ha_url is None
        assert ha.ha_access_token_encrypted is None
        assert ha.ha_timeout is None

    def test_with_values(self):
        ha = HomeAssistantSettings(
            ha_url="http://ha.local:8123",
            ha_access_token_encrypted="ciphertext",
            ha_timeout=30,
        )
        assert ha.ha_url == "http://ha.local:8123"
        assert ha.ha_access_token_encrypted == "ciphertext"
        assert ha.ha_timeout == 30


class TestLegacyPlaintextSecrets:
    """#2113 — a document stored before the rename is read into the ``_encrypted`` field."""

    def test_a_legacy_ha_token_is_read_into_the_encrypted_field(self):
        ha = HomeAssistantSettings(**{"ha_url": "http://ha.local:8123", "ha_access_token": "legacy"})
        assert ha.ha_access_token_encrypted == "legacy"
        assert "ha_access_token" not in ha.model_dump()

    def test_the_encrypted_field_wins_over_a_legacy_key_beside_it(self):
        ha = HomeAssistantSettings(**{"ha_access_token": "older", "ha_access_token_encrypted": "newer"})
        assert ha.ha_access_token_encrypted == "newer"

    def test_an_empty_legacy_plantnet_key_reads_as_no_key(self):
        assert PlantIdentificationSettings(**{"plantnet_api_key": ""}).plantnet_api_key_encrypted is None

    def test_a_legacy_plantnet_key_is_read_into_the_encrypted_field(self):
        pi = PlantIdentificationSettings(**{"plantnet_api_key": "legacy"})
        assert pi.plantnet_api_key_encrypted == "legacy"


class TestSystemSettings:
    def test_defaults(self):
        ss = SystemSettings()
        assert ss.key is None
        assert ss.home_assistant.ha_url is None
        assert ss.created_at is None

    def test_key_alias(self):
        ss = SystemSettings(**{"_key": "default"})
        assert ss.key == "default"

    def test_populate_by_name(self):
        ss = SystemSettings(key="test")
        assert ss.key == "test"

    def test_with_home_assistant(self):
        ss = SystemSettings(
            home_assistant=HomeAssistantSettings(ha_url="http://ha.local:8123"),
        )
        assert ss.home_assistant.ha_url == "http://ha.local:8123"
