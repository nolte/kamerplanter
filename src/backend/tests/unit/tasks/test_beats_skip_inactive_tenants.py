"""REQ-056 §5.2 (AK-08) — the tenant-writing beats #2166 left out skip a tenant that is not ``active``.

Measured on develop before this change: thirteen beats that write into a tenant or notify about
one asked neither ``ActiveTenants`` nor the tenant's ``status``, so a ``suspended`` or
``pending_deletion`` tenant went on getting Home Assistant readings, weather, climate normals,
hardiness zones, irrigation demand, season transitions, quarter-climate tasks, InvenTree syncs,
actuator commands and state polls, tank-alert checks — and its members a digest of what had been
notified about it. Each test below runs one beat over two tenants, one ``active`` and one closed,
and asserts that only the active one is processed. The classification of every beat is held by
``tests/unit/guards/test_beats_skip_inactive_tenants.py``; the care, watering, notification, frost
and three tank beats of #2166 by ``test_care_beats_skip_closed_tenants.py``.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.enums import TenantStatus, TenantType
from app.domain.models.tenant import Tenant
from tests.support.ha_entity_grants import grant_service
from tests.support.tenant_walk import TenantRows

OPEN = "t-open"
CLOSED = "t-closed"
CLOSED_STATES = [TenantStatus.SUSPENDED, TenantStatus.PENDING_DELETION]


class _Tenants:
    """``ITenantRepository.get_by_key`` over one active and one closed tenant."""

    def __init__(self, closed_status: TenantStatus) -> None:
        self.stored = {
            key: Tenant(
                _key=key, name=key, slug=key, tenant_type=TenantType.ORGANIZATION, owner_user_key="o", status=status
            )
            for key, status in ((OPEN, TenantStatus.ACTIVE), (CLOSED, closed_status))
        }

    def get_by_key(self, key: str) -> Tenant | None:
        return self.stored.get(key)

    def keys_in_status(self, statuses: Any) -> dict[str, TenantStatus]:
        """The walk of MT-032 (#2128): the stored tenants in one of *statuses*."""
        return {key: t.status for key, t in self.stored.items() if t.status in set(statuses)}


class _Deps(ModuleType):
    """``app.common.dependencies`` with a ``MagicMock`` for every getter a task imports."""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        getter = MagicMock(name=name)
        setattr(self, name, getter)
        return getter


@pytest.fixture(params=CLOSED_STATES, ids=lambda status: status.value)
def deps(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> _Deps:
    module = _Deps("app.common.dependencies")
    module.get_tenant_repo.return_value = _Tenants(request.param)
    module.get_ha_entity_grant_service = lambda: grant_service(  # type: ignore[attr-defined]
        {OPEN: {"sensor.open", "switch.open"}, CLOSED: {"sensor.closed", "switch.closed"}}
    )
    monkeypatch.setitem(sys.modules, "app.common.dependencies", module)
    from app.config.settings import settings

    for flag in (
        "timescaledb_enabled",
        "weather_enabled",
        "nasa_power_climate_enabled",
        "hardiness_zone_refresh_enabled",
        "irrigation_demand_enabled",
        "season_state_eval_enabled",
        "actuator_control_loop_enabled",
        "inventree_enabled",
    ):
        monkeypatch.setattr(settings, flag, True, raising=False)
    return module


def _site_doc(key: str, tenant_key: str) -> dict[str, Any]:
    return {"_key": key, "name": key, "type": "outdoor", "tenant_key": tenant_key, "gps_coordinates": [52.5, 13.4]}


def _paging(rows: list[Any]) -> MagicMock:
    """A row repository that answers only the tenant walk (MT-032, #2128) — ``get_all`` refuses."""
    walk = TenantRows(rows)
    repo = MagicMock()
    repo.get_all.side_effect = walk.get_all
    repo.iter_for_tenants.side_effect = walk.iter_for_tenants
    repo.iter_without_tenant.side_effect = walk.iter_without_tenant
    return repo


# ── Tanks ────────────────────────────────────────────────────────────────────


def test_check_tank_alerts_checks_the_tanks_of_the_active_tenant_only(deps: _Deps) -> None:
    tank_repo = _paging(
        [SimpleNamespace(key=f"tank-{t}", name=t, tenant_key=t) for t in (OPEN, CLOSED)],
    )
    tank_repo.get_latest_state.return_value = None
    deps.get_tank_repo.return_value = tank_repo

    from app.tasks.tank_maintenance_tasks import check_tank_alerts

    check_tank_alerts()

    assert [call.args[0] for call in tank_repo.get_latest_state.call_args_list] == [f"tank-{OPEN}"]


# ── Notifications ────────────────────────────────────────────────────────────


def test_send_email_digests_hands_the_tenant_gate_to_the_digest(deps: _Deps) -> None:
    deps.get_notification_preference_repo.return_value.list_users_with_digest_enabled.return_value = [
        SimpleNamespace(user_key="u-1")
    ]
    service = MagicMock()
    service.send_email_digest = AsyncMock(return_value={"status": "sent", "count": 1})
    deps.get_notification_service.return_value = service

    from app.tasks.notification_tasks import send_email_digests

    send_email_digests.run()

    gate = service.send_email_digest.await_args.kwargs["tenant_is_active"]
    assert gate(OPEN) is True
    assert gate(CLOSED) is False


# ── Home Assistant ingestion ─────────────────────────────────────────────────


def test_ingest_ha_readings_reads_the_sensors_of_the_active_tenant_only(deps: _Deps) -> None:
    ha_client = MagicMock()
    ha_client.get_state.return_value = {"value": 21.5, "unit": "°C"}
    deps.get_ha_client.return_value = ha_client
    deps.get_observation_repo.return_value.is_available.return_value = True
    service = deps.get_observation_service.return_value
    service.owning_tenant_key.side_effect = {"s-open": OPEN, "s-closed": CLOSED}.get
    service.record_readings_batch.return_value = 1
    sensor_repo = MagicMock()
    sensor_repo._db.aql.execute.return_value = iter(
        [
            {"_key": "s-open", "metric_type": "temperature", "ha_entity_id": "sensor.open"},
            {"_key": "s-closed", "metric_type": "temperature", "ha_entity_id": "sensor.closed"},
        ]
    )
    deps.get_sensor_repo.return_value = sensor_repo

    from app.tasks.sensor_ingestion_tasks import ingest_ha_readings

    result = ingest_ha_readings()

    assert [call.args[0] for call in ha_client.get_state.call_args_list] == ["sensor.open"]
    assert [call.args[0] for call in service.record_readings_batch.call_args_list] == ["s-open"]
    assert result["inserted"] == 1


# ── Weather, climate normals, hardiness, irrigation ──────────────────────────


def test_fetch_weather_forecasts_fetches_for_the_active_tenant_only(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.domain.services import weather_source_resolver

    asked: list[str] = []

    class _Resolver:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def resolve_daily(self, site: Any, _config: Any) -> list:
            asked.append(site.tenant_key)
            return []

    monkeypatch.setattr(weather_source_resolver, "WeatherSourceResolver", _Resolver)
    config_repo = MagicMock()
    config_repo._db.aql.execute.return_value = iter(
        [{"site_key": f"site-{t}", "tenant_key": t, "enabled": True} for t in (OPEN, CLOSED)]
    )
    config_repo._from_doc.side_effect = lambda doc: doc
    deps.get_weather_source_config_repo.return_value = config_repo
    deps.get_site_repo.return_value.get_site_by_key.side_effect = lambda key: SimpleNamespace(
        gps_coordinates=(52.5, 13.4), tenant_key=key.removeprefix("site-")
    )

    from app.tasks.weather_tasks import fetch_weather_forecasts

    fetch_weather_forecasts.run()

    assert asked == [OPEN]


def test_fetch_climate_normals_fetches_for_the_active_tenant_only(deps: _Deps, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.domain.services import weather_adapter_registry as registry

    asked: list[float] = []

    class _Adapter:
        source_name = "nasa-power"

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def fetch_climate_normals(self, *, latitude: float, longitude: float) -> None:
            asked.append(latitude)

    monkeypatch.setattr(registry.WeatherAdapterRegistry, "get", classmethod(lambda _cls, _name: _Adapter))
    deps.get_db.return_value.aql.execute.return_value = iter(
        [{**_site_doc("site-open", OPEN), "gps_coordinates": [1.0, 0.0]}, _site_doc("site-closed", CLOSED)]
    )
    deps.get_site_repo.return_value._from_doc.side_effect = lambda doc: doc
    deps.get_climate_normal_repo.return_value.find_one.return_value = None

    from app.tasks.climate_tasks import fetch_climate_normals

    fetch_climate_normals.run()

    assert asked == [1.0]


def test_refresh_site_hardiness_zones_resolves_the_sites_of_the_active_tenant_only(deps: _Deps) -> None:
    deps.get_db.return_value.aql.execute.return_value = iter(
        [_site_doc("site-open", OPEN), _site_doc("site-closed", CLOSED)]
    )
    deps.get_site_repo.return_value._from_doc.side_effect = lambda doc: doc
    service = deps.get_hardiness_zone_service.return_value

    from app.tasks.hardiness_tasks import refresh_site_hardiness_zones

    refresh_site_hardiness_zones.run()

    assert [call.args for call in service.resolve_for_site.call_args_list] == [("site-open", OPEN)]


def test_compute_irrigation_demand_materialises_for_the_active_tenant_only(deps: _Deps) -> None:
    site_repo = deps.get_site_repo.return_value
    site_repo.find_site_docs_by_types.return_value = [_site_doc("site-open", OPEN), _site_doc("site-closed", CLOSED)]
    site_repo._from_doc.side_effect = lambda doc: doc
    forecast_repo = deps.get_weather_forecast_repo.return_value
    forecast_repo.find_by_site.return_value = []

    from app.tasks.irrigation_tasks import compute_irrigation_demand

    compute_irrigation_demand.run()

    assert [call.args for call in forecast_repo.find_by_site.call_args_list] == [("site-open", OPEN)]


# ── Season ───────────────────────────────────────────────────────────────────


def test_evaluate_season_states_advances_the_sites_of_the_active_tenant_only(deps: _Deps) -> None:
    site_repo = deps.get_site_repo.return_value
    site_repo.find_site_docs_by_types.return_value = [_site_doc("site-open", OPEN), _site_doc("site-closed", CLOSED)]
    site_repo.find_site_keys_with_frost_exposed_location.return_value = []
    site_repo.find_site_docs_by_keys.return_value = []
    service = deps.get_season_state_service.return_value
    service.evaluate_site_detailed.return_value = (None, False)

    from app.tasks.season_tasks import evaluate_season_states

    evaluate_season_states.run()

    assert [call.args[0].key for call in service.evaluate_site_detailed.call_args_list] == ["site-open"]


def test_evaluate_quarter_climate_evaluates_the_plants_of_the_active_tenant_only(deps: _Deps) -> None:
    deps.get_plant_repo.return_value = _paging(
        [SimpleNamespace(key=f"plant-{t}", removed_on=None, tenant_key=t) for t in (OPEN, CLOSED)]
    )
    service = deps.get_quarter_climate_service.return_value
    service.evaluate_plant.return_value = None

    from app.tasks.season_tasks import evaluate_quarter_climate

    result = evaluate_quarter_climate.run()

    assert [call.args[0] for call in service.evaluate_plant.call_args_list] == [f"plant-{OPEN}"]
    assert result["evaluated"] == 1


# ── Actuators ────────────────────────────────────────────────────────────────


def _actuators() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            key=f"act-{t}",
            tenant_key=t,
            location_key=f"loc-{t}",
            ha_entity_id=f"switch.{t.removeprefix('t-')}",
            is_online=True,
        )
        for t in (OPEN, CLOSED)
    ]


def test_evaluate_control_rules_evaluates_the_actuators_of_the_active_tenant_only(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.tasks.actuator_tasks as module

    monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})
    deps.get_actuator_repo.return_value = _paging(_actuators())
    service = deps.get_actuator_service.return_value
    service.evaluate_actuator.return_value = None

    module.evaluate_control_rules.run()

    assert [call.args[0].key for call in service.evaluate_actuator.call_args_list] == [f"act-{OPEN}"]
    # SEC-003 — the closed tenant's device is driven to a safe state instead, not left as it was.
    assert [call.args[0].key for call in service.drive_to_safe_state.call_args_list] == [f"act-{CLOSED}"]


def test_evaluate_control_rules_leaves_the_device_of_an_erased_tenant_alone(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.tasks.actuator_tasks as module

    deps.get_tenant_repo.return_value.stored[CLOSED] = deps.get_tenant_repo.return_value.stored[CLOSED].model_copy(
        update={"status": TenantStatus.DELETED}
    )
    monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})
    deps.get_actuator_repo.return_value = _paging(_actuators())
    service = deps.get_actuator_service.return_value
    service.evaluate_actuator.return_value = None

    module.evaluate_control_rules.run()

    service.drive_to_safe_state.assert_not_called()


@pytest.mark.parametrize("closed_status", CLOSED_STATES + [TenantStatus.ORPHANED], ids=lambda s: s.value)
def test_a_valve_left_open_when_the_tenant_closed_is_closed_on_the_next_tick(
    monkeypatch: pytest.MonkeyPatch, closed_status: TenantStatus
) -> None:
    """SEC-003, through the real ``ActuatorService``: the last command must not stay latched."""
    import app.tasks.actuator_tasks as module
    from app.common.enums import ActuatorType
    from app.domain.models.actuator import Actuator
    from tests.unit.domain.services.test_actuator_service import FakeActuatorRepo, FakeHaClient, FakeTaskRepo
    from tests.unit.domain.services.test_actuator_service import _service as actuator_service

    valve = Actuator(
        _key="valve",
        tenant_key="t1",
        location_key="loc1",
        name="Beet-Ventil",
        actuator_type=ActuatorType.IRRIGATION_VALVE,
        protocol="home_assistant",
        ha_entity_id="switch.valve",
        current_state="on",  # opened by a schedule before the suspension
    )
    repo = FakeActuatorRepo()
    repo.actuators["valve"] = valve
    ha = FakeHaClient()
    service = actuator_service(repo, ha=ha, task_repo=FakeTaskRepo())

    tenants = _Tenants(closed_status)
    tenants.stored["t1"] = tenants.stored[CLOSED].model_copy(update={"key": "t1"})
    deps = _Deps("app.common.dependencies")
    deps.get_tenant_repo.return_value = tenants
    deps.get_actuator_service.return_value = service
    deps.get_actuator_repo.return_value = _paging([valve])
    deps.get_ha_entity_grant_service = lambda: grant_service({"t1": {"switch.valve"}})  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)
    monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})
    from app.config.settings import settings

    monkeypatch.setattr(settings, "actuator_control_loop_enabled", True, raising=False)

    module.evaluate_control_rules.run()

    assert repo.actuators["valve"].current_state == "off"
    assert [call[1] for call in ha.calls] == ["turn_off"]


def test_an_actuator_without_a_tenant_is_driven_to_a_safe_state_not_dropped(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#2128 review W1: a device nobody owns keeps the fail-safe sweep; it is not silently left latched.

    Before #2128 it ran through ``evaluate_actuator``; the first per-tenant walk dropped it, so a heater
    left on stayed on. It now gets the closed-tenant treatment: safety rules, then off — no schedule.
    """
    import app.tasks.actuator_tasks as module

    monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})
    orphan = SimpleNamespace(key="act-nobody", tenant_key="", location_key="loc-x", ha_entity_id="switch.x")
    deps.get_actuator_repo.return_value = _paging([*_actuators(), orphan])
    service = deps.get_actuator_service.return_value
    service.evaluate_actuator.return_value = None

    module.evaluate_control_rules.run()

    assert [call.args[0].key for call in service.evaluate_actuator.call_args_list] == [f"act-{OPEN}"]
    assert [call.args[0].key for call in service.drive_to_safe_state.call_args_list] == [
        f"act-{CLOSED}",
        "act-nobody",
    ]


def test_one_invalid_actuator_document_does_not_hide_the_devices_behind_it(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#2128 review W2: through the real repository, a document the model refuses is skipped.

    The walk used to wrap a whole page at once; one refused document ended the generator, and since
    the loop sits outside the per-actuator ``try`` the run aborted — every later device, including the
    closed tenant's safe state (SEC-003), was never reached.
    """
    import app.tasks.actuator_tasks as module
    from app.data_access.arango.actuator_repository import ArangoActuatorRepository
    from tests.support.tenant_walk import AqlRowsDb

    def _doc(key: str, tenant: str) -> dict[str, Any]:
        return {"_key": key, "tenant_key": tenant, "name": key, "actuator_type": "heater", "ha_entity_id": "switch.h"}

    broken = {"_key": "b-broken", "tenant_key": OPEN, "name": "", "actuator_type": "no-such-type"}
    db = AqlRowsDb([_doc("a-open", OPEN), broken, _doc("c-closed", CLOSED)])
    monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})
    deps.get_actuator_repo.return_value = ArangoActuatorRepository(db)
    service = deps.get_actuator_service.return_value
    service.evaluate_actuator.return_value = None

    module.evaluate_control_rules.run()

    assert [call.args[0].key for call in service.evaluate_actuator.call_args_list] == ["a-open"]
    assert [call.args[0].key for call in service.drive_to_safe_state.call_args_list] == ["c-closed"]


def test_check_tank_alerts_keeps_the_installation_sweep_for_a_tank_without_a_tenant(deps: _Deps) -> None:
    """#2128 review W1: as before #2128, a tenantless tank is checked (read and logged, nothing written)."""
    tank_repo = _paging(
        [
            SimpleNamespace(key=f"tank-{OPEN}", name="o", tenant_key=OPEN),
            SimpleNamespace(key="tank-nobody", name="n", tenant_key=""),
        ]
    )
    tank_repo.get_latest_state.return_value = None
    deps.get_tank_repo.return_value = tank_repo

    from app.tasks.tank_maintenance_tasks import check_tank_alerts

    check_tank_alerts()

    assert [call.args[0] for call in tank_repo.get_latest_state.call_args_list] == [f"tank-{OPEN}", "tank-nobody"]


def test_sync_actuator_states_polls_the_actuators_of_the_active_tenant_only(deps: _Deps) -> None:
    deps.get_actuator_repo.return_value = _paging(_actuators())
    ha_client = deps.get_ha_client.return_value
    ha_client.get_state.return_value = {"value": "on"}

    from app.tasks.actuator_tasks import sync_actuator_states

    sync_actuator_states.run()

    assert [call.args[0] for call in ha_client.get_state.call_args_list] == ["switch.open"]


# ── InvenTree ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("operation", ["sync", "push"])
def test_inventree_syncs_the_connection_of_the_active_tenant_only(
    deps: _Deps, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    import app.domain.services.inventree_service as service_module
    import app.tasks.inventree_tasks as module

    synced: list[str] = []

    class _Engine:
        def __init__(self, tenant_key: str) -> None:
            self._tenant_key = tenant_key

        async def sync_stock_levels(self) -> None:
            synced.append(self._tenant_key)

        async def push_pending_transactions(self) -> None:
            synced.append(self._tenant_key)

    class _Service:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def _sync_engine_for(self, _connection: Any, tenant_key: str) -> _Engine:
            return _Engine(tenant_key)

    monkeypatch.setattr(service_module, "InvenTreeService", _Service)
    monkeypatch.setattr(
        module, "_active_connections", lambda: iter([(t, SimpleNamespace(key=f"c-{t}")) for t in (OPEN, CLOSED)])
    )

    task = module.sync_stock_levels if operation == "sync" else module.push_pending_transactions
    result = task.run()

    assert synced == [OPEN]
    assert result["connections"] == 1
