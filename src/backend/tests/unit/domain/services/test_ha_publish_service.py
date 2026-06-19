"""Unit tests for the Home Assistant publish-selection service.

Uses an in-memory fake repository to verify the opt-in policy, upsert
semantics and the export-facing enabled-key read.
"""

from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting
from app.domain.services.ha_publish_service import HaPublishService


class _FakeRepo:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str, str], HaPublishSetting] = {}

    def get_for_entity(self, tenant_key, entity_type, entity_key):
        return self.store.get((tenant_key, entity_type.value, entity_key))

    def list_for_tenant(self, tenant_key, entity_type=None):
        return [
            s
            for (t, et, _k), s in self.store.items()
            if t == tenant_key and (entity_type is None or et == entity_type.value)
        ]

    def list_enabled_keys(self, tenant_key, entity_type):
        return [
            s.entity_key
            for (t, et, _k), s in self.store.items()
            if t == tenant_key and et == entity_type.value and s.enabled
        ]

    def upsert(self, setting):
        key = (setting.tenant_key, setting.entity_type.value, setting.entity_key)
        self.store[key] = setting
        return setting


def _service():
    return HaPublishService(_FakeRepo())


def test_is_published_defaults_false_opt_in():
    service = _service()
    assert service.is_published("t1", HaPublishEntityType.PLANT, "plant-1") is False


def test_set_published_then_is_published():
    service = _service()
    service.set_published("t1", HaPublishEntityType.TANK, "tank-1", enabled=True)
    assert service.is_published("t1", HaPublishEntityType.TANK, "tank-1") is True


def test_set_published_false_is_not_published():
    service = _service()
    service.set_published("t1", HaPublishEntityType.PLANT, "plant-1", enabled=False)
    assert service.is_published("t1", HaPublishEntityType.PLANT, "plant-1") is False


def test_list_enabled_keys_only_returns_enabled():
    service = _service()
    service.set_published("t1", HaPublishEntityType.PLANT, "plant-1", enabled=True)
    service.set_published("t1", HaPublishEntityType.PLANT, "plant-2", enabled=False)
    service.set_published("t1", HaPublishEntityType.TANK, "tank-1", enabled=True)
    keys = service.list_enabled_keys("t1", HaPublishEntityType.PLANT)
    assert keys == ["plant-1"]


def test_enabled_keys_are_tenant_scoped():
    service = _service()
    service.set_published("t1", HaPublishEntityType.PLANT, "plant-1", enabled=True)
    service.set_published("t2", HaPublishEntityType.PLANT, "plant-9", enabled=True)
    assert service.list_enabled_keys("t1", HaPublishEntityType.PLANT) == ["plant-1"]
    assert service.list_enabled_keys("t2", HaPublishEntityType.PLANT) == ["plant-9"]


def test_bulk_set_published():
    service = _service()
    result = service.bulk_set_published(
        "t1",
        HaPublishEntityType.LOCATION,
        {"loc-1": True, "loc-2": False, "loc-3": True},
    )
    assert len(result) == 3
    assert sorted(service.list_enabled_keys("t1", HaPublishEntityType.LOCATION)) == ["loc-1", "loc-3"]


def test_set_published_is_idempotent_upsert():
    service = _service()
    service.set_published("t1", HaPublishEntityType.TANK, "tank-1", enabled=True)
    service.set_published("t1", HaPublishEntityType.TANK, "tank-1", enabled=False)
    assert service.is_published("t1", HaPublishEntityType.TANK, "tank-1") is False
    assert service.list_settings("t1", HaPublishEntityType.TANK).__len__() == 1
