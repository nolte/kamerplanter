from app.domain.models.system_settings import HomeAssistantSettings, SystemSettings


class TestHomeAssistantSettings:
    def test_defaults(self):
        ha = HomeAssistantSettings()
        assert ha.ha_url is None
        assert ha.ha_access_token is None
        assert ha.ha_timeout is None

    def test_with_values(self):
        ha = HomeAssistantSettings(
            ha_url="http://ha.local:8123",
            ha_access_token="secret",
            ha_timeout=30,
        )
        assert ha.ha_url == "http://ha.local:8123"
        assert ha.ha_access_token == "secret"
        assert ha.ha_timeout == 30


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
