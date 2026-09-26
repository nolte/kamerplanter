"""Bundle C of the reference-key sweep (#1872), part 2: feeding, watering, Home Assistant, AI.

* **C6** — ``tank_fill_event_key`` on feeding events (REST and the MCP tool both
  go through ``FeedingService.create_event``), watering events and watering
  logs. A fill event has no tenant of its own; it is resolved through its tank.
* **C7** — ``nutrient_plan_key`` on watering events and logs: global or own.
* **C8** — a Home Assistant publish setting names a plant, tank or location of
  the tenant; a foreign key showed up in the tenant's own ``enabled-keys`` list.
* **C9** — a plant / run AI context key belongs to the tenant before a tip card,
  conversation or audit row stores it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ApplicationMethod
from app.common.exceptions import NotFoundError
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.ha_publish_setting import HaPublishEntityType
from app.domain.models.tank import FillType, TankFillEvent
from app.domain.models.watering_event import WateringEvent
from app.domain.models.watering_log import WateringLog
from app.domain.services.feeding_service import FeedingService
from app.domain.services.ha_publish_service import HaPublishService
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


class _Tanks:
    """Fill events ``fill_own`` (own tank), ``fill_foreign`` (another tenant's tank), ``fill_orphan`` (no tank)."""

    def get_fill_event(self, key: str):
        tanks = {"fill_own": "tank_own", "fill_foreign": "tank_foreign", "fill_orphan": ""}
        if key not in tanks:
            return None
        return TankFillEvent(_key=key, tank_key=tanks[key], fill_type=FillType.FULL_CHANGE, volume_liters=10)

    def get_by_key(self, key: str):
        owner = {"tank_own": OWN, "tank_foreign": "t_b"}.get(key)
        return SimpleNamespace(key=key, tenant_key=owner) if owner else None


class _Plans:
    def get_by_key(self, key: str):
        owner = {"plan_global": "", "plan_own": OWN, "plan_foreign": "t_b"}.get(key)
        return None if owner is None else SimpleNamespace(key=key, tenant_key=owner)


FOREIGN_FILLS = ["fill_foreign", "fill_orphan", "no-such-fill"]


@pytest.mark.parametrize("fill", FOREIGN_FILLS)
def test_a_feeding_event_names_only_a_fill_of_the_tenants_tank(fill: str) -> None:
    repo = MagicMock()
    service = FeedingService(repo, fill_event_anchors=_Tanks())

    with pytest.raises(NotFoundError):
        service.create_event(
            FeedingEvent(tenant_key=OWN, plant_key="p1", volume_applied_liters=1, tank_fill_event_key=fill)
        )

    repo.create.assert_not_called()


def test_a_feeding_event_with_an_own_fill_is_stored() -> None:
    repo = MagicMock()

    FeedingService(repo, fill_event_anchors=_Tanks()).create_event(
        FeedingEvent(tenant_key=OWN, plant_key="p1", volume_applied_liters=1, tank_fill_event_key="fill_own")
    )

    repo.create.assert_called_once()


def _watering_service() -> tuple[WateringService, MagicMock]:
    repo = MagicMock()
    service = WateringService(
        repo,
        WateringEngine(),
        FakeSiteRepo(),  # type: ignore[arg-type]
        nutrient_plan_repo=_Plans(),
        fill_event_anchors=_Tanks(),
    )
    service._slot_for_plant = lambda *a: None  # type: ignore[method-assign]  # noqa: SLF001
    return service, repo


@pytest.mark.parametrize(
    "fields",
    [
        *({"tank_fill_event_key": f} for f in FOREIGN_FILLS),
        {"nutrient_plan_key": "plan_foreign"},
        {"nutrient_plan_key": "x"},
    ],
)
def test_a_watering_event_names_only_the_tenants_fill_and_plan(fields: dict) -> None:
    service, repo = _watering_service()

    with pytest.raises(NotFoundError):
        service.create_event(WateringEvent(tenant_key=OWN, volume_liters=1, plant_keys=["p1"], **fields))

    repo.create.assert_not_called()


def _log(**fields) -> WateringLog:  # noqa: ANN003
    return WateringLog(
        tenant_key=OWN,
        logged_at=datetime(2026, 9, 26, tzinfo=UTC),
        application_method=ApplicationMethod.DRENCH,
        volume_liters=1.0,
        slot_keys=["slot_own"],
        **fields,
    )


@pytest.mark.parametrize(
    "fields",
    [*({"tank_fill_event_key": f} for f in FOREIGN_FILLS), {"nutrient_plan_key": "plan_foreign"}],
)
def test_a_watering_log_names_only_the_tenants_fill_and_plan(fields: dict) -> None:
    repo = MagicMock()
    service = WateringLogService(
        repo,
        WateringEngine(),
        site_repo=FakeSiteRepo(),
        nutrient_plan_repo=_Plans(),
        fill_event_anchors=_Tanks(),  # type: ignore[arg-type]
    )

    with pytest.raises(NotFoundError):
        service.create_log(_log(**fields))

    repo.create.assert_not_called()


def test_a_watering_log_with_an_own_fill_and_a_global_plan_is_stored() -> None:
    repo = MagicMock()
    repo.create.side_effect = lambda log: log
    service = WateringLogService(
        repo,
        WateringEngine(),
        site_repo=FakeSiteRepo(),
        nutrient_plan_repo=_Plans(),
        fill_event_anchors=_Tanks(),  # type: ignore[arg-type]
    )

    service.create_log(_log(tank_fill_event_key="fill_own", nutrient_plan_key="plan_global"))

    repo.create.assert_called_once()


# ── C8 Home Assistant publish settings ──────────────────────────────────────


def _ha() -> tuple[HaPublishService, MagicMock]:
    repo = MagicMock()
    plants = MagicMock()
    plants.get_by_key.side_effect = lambda k: SimpleNamespace(key=k, tenant_key=OWN if k == "p_own" else "t_b")
    return HaPublishService(repo, plant_repo=plants, tank_repo=_Tanks(), site_anchors=FakeSiteRepo()), repo


@pytest.mark.parametrize(
    "entity_type,key",
    [
        (HaPublishEntityType.PLANT, "p_foreign"),
        (HaPublishEntityType.TANK, "tank_foreign"),
        (HaPublishEntityType.TANK, "no-such-tank"),
        (HaPublishEntityType.LOCATION, "loc_foreign"),
    ],
)
def test_a_publish_setting_names_only_the_tenants_entity(entity_type: HaPublishEntityType, key: str) -> None:
    service, repo = _ha()

    with pytest.raises(NotFoundError):
        service.set_published(OWN, entity_type, key, True)

    repo.upsert.assert_not_called()


def test_a_bulk_publish_with_one_foreign_key_writes_nothing() -> None:
    service, repo = _ha()

    with pytest.raises(NotFoundError):
        service.bulk_set_published(OWN, HaPublishEntityType.PLANT, {"p_own": True, "p_foreign": True})

    repo.upsert.assert_not_called()


# ── C9 AI context keys ──────────────────────────────────────────────────────


def _ai():  # noqa: ANN202
    from app.domain.services.ai_assistant_service import AiAssistantService

    consent = MagicMock()
    plants = MagicMock()
    plants.get_by_key.side_effect = lambda k: SimpleNamespace(key=k, tenant_key=OWN if k == "p_own" else "t_b")
    conversations = MagicMock()
    service = AiAssistantService(
        knowledge_adapter=MagicMock(),
        consent_guard=consent,
        audit_logger=MagicMock(),
        tip_cache_repo=MagicMock(),
        conversation_repo=conversations,
        provider_repo=MagicMock(),
        plant_repo=plants,
        planting_run_repo=MagicMock(get_by_key=MagicMock(return_value=None)),
    )
    return service, conversations


@pytest.mark.parametrize("context", [("plant_instance", "p_foreign"), ("planting_run", "r_any")])
def test_a_conversation_names_only_the_tenants_plant_or_run(context: tuple[str, str]) -> None:
    service, conversations = _ai()
    ctx = SimpleNamespace(tenant_key=OWN, user_key="u1")

    with pytest.raises(NotFoundError):
        service.create_conversation(ctx, context_type=context[0], context_key=context[1])

    conversations.create.assert_not_called()


def test_a_general_conversation_names_no_entity() -> None:
    service, conversations = _ai()

    service.create_conversation(SimpleNamespace(tenant_key=OWN, user_key="u1"), context_type="general", context_key="x")

    conversations.create.assert_called_once()
