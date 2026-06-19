"""API tests for the tenant-scoped Home Assistant publish-selection router."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ha_publish.tenant_router import router as ha_publish_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ha_publish_service
from app.common.enums import TenantRole
from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting
from app.domain.models.tenant_context import TenantContext

TENANT_KEY = "t-test-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _build_app(service) -> FastAPI:
    app = FastAPI()
    app.include_router(ha_publish_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_ha_publish_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    return app


def test_get_status_defaults_false():
    service = MagicMock()
    service.is_published.return_value = False
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/test-slug/ha-publish/plant/plant-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"entity_type": "plant", "entity_key": "plant-1", "enabled": False}


def test_set_status_enables_entity():
    service = MagicMock()
    service.set_published.return_value = HaPublishSetting(
        tenant_key=TENANT_KEY,
        entity_type=HaPublishEntityType.TANK,
        entity_key="tank-1",
        enabled=True,
    )
    client = TestClient(_build_app(service))
    resp = client.put(
        "/api/v1/t/test-slug/ha-publish/tank/tank-1",
        json={"enabled": True},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True
    service.set_published.assert_called_once_with(TENANT_KEY, HaPublishEntityType.TANK, "tank-1", True)


def test_list_settings_filtered_by_type():
    service = MagicMock()
    service.list_settings.return_value = [
        HaPublishSetting(
            tenant_key=TENANT_KEY,
            entity_type=HaPublishEntityType.PLANT,
            entity_key="plant-1",
            enabled=True,
        )
    ]
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/test-slug/ha-publish?entity_type=plant")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["entity_key"] == "plant-1"
    service.list_settings.assert_called_once_with(TENANT_KEY, HaPublishEntityType.PLANT)


def test_enabled_keys_export_endpoint():
    service = MagicMock()
    service.list_enabled_keys.return_value = ["plant-1", "plant-2"]
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/test-slug/ha-publish/enabled-keys/plant")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"entity_type": "plant", "entity_keys": ["plant-1", "plant-2"]}


def test_bulk_set():
    service = MagicMock()
    service.bulk_set_published.return_value = [
        HaPublishSetting(
            tenant_key=TENANT_KEY,
            entity_type=HaPublishEntityType.LOCATION,
            entity_key="loc-1",
            enabled=True,
        ),
        HaPublishSetting(
            tenant_key=TENANT_KEY,
            entity_type=HaPublishEntityType.LOCATION,
            entity_key="loc-2",
            enabled=False,
        ),
    ]
    client = TestClient(_build_app(service))
    resp = client.put(
        "/api/v1/t/test-slug/ha-publish",
        json={
            "entity_type": "location",
            "entries": [
                {"entity_key": "loc-1", "enabled": True},
                {"entity_key": "loc-2", "enabled": False},
            ],
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    service.bulk_set_published.assert_called_once_with(
        TENANT_KEY,
        HaPublishEntityType.LOCATION,
        {"loc-1": True, "loc-2": False},
    )


def test_invalid_entity_type_rejected():
    service = MagicMock()
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/test-slug/ha-publish/banana/x-1")
    assert resp.status_code == 422
