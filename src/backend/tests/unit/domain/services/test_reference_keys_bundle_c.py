"""Bundle C of the reference-key sweep (#1872): every stored reference resolved under the tenant.

Each hit stored a caller-supplied key of another entity without resolving it —
no edge was written and no reader followed it yet, so nothing leaked; the day a
reader trusted the key it would have. Each test drives the write path with a
foreign key (and, where the resolution could distinguish them, an unknown one)
and asserts the same 404 and that nothing was stored. Service-level, over
doubles; the route tests of #1874/#1876 hold the wiring pattern.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.actuator import (
    ActionCommand,
    ConditionOperator,
    ControlRule,
    HysteresisConfig,
    RuleAction,
    RuleCondition,
)
from app.domain.models.propagation import PropagationBatch, PropagationEvent, RootingProtocol
from app.domain.models.site import Location
from app.domain.services.actuator_service import ActuatorService
from app.domain.services.propagation_service import PropagationService
from app.domain.services.site_service import SiteService
from app.domain.services.task_entity_guard import TaskEntityGuard
from tests.unit.domain.services.test_actuator_service import FakeActuatorRepo
from tests.unit.domain.services.test_actuator_service import FakeSiteRepo as ActuatorSites

OWN = "t1"
READABLE_SPECIES = {"sp_global", "sp_own"}


def _species(key: str, *, tenant_key: str) -> None:
    if key not in READABLE_SPECIES:
        raise NotFoundError("Species", key)


# ── C1 planting run source plant ────────────────────────────────────────────


def test_a_clone_run_cannot_name_another_tenants_mother_plant() -> None:
    from app.common.enums import PlantingRunType
    from app.domain.models.planting_run import PlantingRun
    from app.domain.services.planting_run_service import PlantingRunService
    from tests.unit.domain.services.test_planting_run_location_ownership import FakeRunRepo, FakeSiteRepo

    plants = MagicMock()
    plants.get_by_key.side_effect = lambda k: SimpleNamespace(key=k, tenant_key="t_b") if k == "p_foreign" else None
    repo = FakeRunRepo()
    service = PlantingRunService(repo, plants, engine=MagicMock(), site_repo=FakeSiteRepo(), species_resolver=_species)

    for source in ("p_foreign", "no-such-plant"):
        run = PlantingRun(tenant_key="tenant_own", name="Klon", run_type=PlantingRunType.CLONE, source_plant_key=source)
        with pytest.raises(NotFoundError):
            service.create_run(run, [])

    assert repo.store == {}


# ── C2 / C3 / C11 / C12 propagation ─────────────────────────────────────────


def _propagation() -> tuple[PropagationService, MagicMock]:
    prop = MagicMock()
    prop.get_plant.side_effect = lambda k, t: SimpleNamespace(key=k) if k.startswith("p_own") else None
    prop.get_protocol.side_effect = lambda k, t: SimpleNamespace(key=k, tenant_key="") if k == "proto_global" else None
    prop.get_batch.side_effect = lambda k, t: SimpleNamespace(key=k) if k == "b_own" else None
    runs = MagicMock()
    runs.get_by_key.side_effect = lambda k: SimpleNamespace(key=k, tenant_key=OWN if k == "r_own" else "t_b")
    service = PropagationService(propagation_repo=prop, planting_run_repo=runs, species_resolver=_species)
    return service, prop


@pytest.mark.parametrize(
    "fields",
    [
        {"parent_plant_keys": ["p_own", "p_foreign"]},
        {"child_plant_keys": ["p_foreign"]},
        {"protocol_key": "proto_foreign"},
        {"batch_key": "b_foreign"},
        {"species_key": "sp_foreign"},
    ],
    ids=["parent", "child", "protocol", "batch", "species"],
)
def test_a_propagation_event_names_only_the_tenants_references(fields: dict) -> None:
    service, prop = _propagation()

    with pytest.raises(NotFoundError):
        service.create_event(PropagationEvent(tenant_key=OWN, method="cutting", **fields))

    prop.create_event.assert_not_called()


def test_a_propagation_event_with_own_and_global_references_is_stored() -> None:
    service, prop = _propagation()
    prop.create_event.side_effect = lambda e: e

    service.create_event(
        PropagationEvent(
            tenant_key=OWN,
            method="cutting",
            parent_plant_keys=["p_own1"],
            child_plant_keys=["p_own2"],
            protocol_key="proto_global",
            batch_key="b_own",
            species_key="sp_global",
        )
    )

    prop.create_event.assert_called_once()


def test_a_batch_cannot_target_another_tenants_run() -> None:
    service, prop = _propagation()

    with pytest.raises(NotFoundError):
        service.create_batch(
            PropagationBatch(tenant_key=OWN, name="B", method="cutting", target_planting_run_key="r_foreign")
        )

    prop.create_batch.assert_not_called()


def test_finalize_refuses_a_run_it_cannot_look_up() -> None:
    # The finalize check used to be skipped entirely without a run repository.
    prop = MagicMock()
    prop.get_batch.return_value = PropagationBatch(tenant_key=OWN, name="B", method="cutting")
    service = PropagationService(propagation_repo=prop, species_resolver=_species)

    with pytest.raises(NotFoundError):
        service.finalize_batch("b1", OWN, "r_own")

    prop.update_batch.assert_not_called()


@pytest.mark.parametrize("path", ["create", "update"])
def test_a_protocol_recommends_only_readable_species(path: str) -> None:
    service, prop = _propagation()
    prop.get_protocol.side_effect = lambda k, t: SimpleNamespace(key=k, tenant_key=OWN)
    protocol = RootingProtocol(
        name="P", method="cutting", tenant_key=OWN, recommended_species_keys=["sp_own", "sp_foreign"]
    )

    with pytest.raises(NotFoundError):
        if path == "create":
            service.create_protocol(protocol)
        else:
            service.update_protocol("proto1", OWN, protocol)

    prop.create_protocol.assert_not_called()
    prop.update_protocol.assert_not_called()


# ── C4 location parent and tank on update / create ──────────────────────────


class _Sites:
    def __init__(self) -> None:
        self.locations = {
            "loc_own": Location(_key="loc_own", name="A", area_m2=1.0, site_key="site_own"),
            "loc_foreign": Location(_key="loc_foreign", name="B", area_m2=1.0, site_key="site_foreign"),
        }
        self.writes: list[str] = []

    def get_site_by_key(self, key: str):
        return SimpleNamespace(key=key, tenant_key=OWN if key == "site_own" else "t_b")

    def get_site_or_raise(self, key: str):
        return self.get_site_by_key(key)

    def get_location_by_key(self, key: str):
        return self.locations.get(key)

    def get_location_or_raise(self, key: str):
        if key not in self.locations:
            raise NotFoundError("Location", key)
        return self.locations[key]

    def get_slot_by_key(self, key: str):
        return None

    def update_location(self, key: str, location: Location) -> Location:
        self.writes.append(key)
        return location

    def create_location(self, location: Location) -> Location:
        self.writes.append("new")
        return location


class _Tanks:
    def get_by_key(self, key: str):
        return (
            SimpleNamespace(key=key, tenant_key=OWN)
            if key == "tank_own"
            else (SimpleNamespace(key=key, tenant_key="t_b") if key == "tank_foreign" else None)
        )


@pytest.mark.parametrize(
    "change",
    [{"parent_location_key": "loc_foreign"}, {"tank_key": "tank_foreign"}, {"tank_key": "no-such-tank"}],
    ids=["parent", "tank", "unknown-tank"],
)
def test_a_location_update_names_only_the_tenants_parent_and_tank(change: dict) -> None:
    sites = _Sites()
    service = SiteService(sites, tank_repo=_Tanks())
    location = Location(name="A", area_m2=1.0, site_key="site_own", **change)

    with pytest.raises(NotFoundError):
        service.update_location("loc_own", location, tenant_key=OWN)

    assert sites.writes == []


def test_a_location_is_not_its_own_parent() -> None:
    sites = _Sites()

    with pytest.raises(ValidationError):
        SiteService(sites, tank_repo=_Tanks()).update_location(
            "loc_own",
            Location(name="A", area_m2=1.0, site_key="site_own", parent_location_key="loc_own"),
            tenant_key=OWN,
        )

    assert sites.writes == []


def test_a_new_location_names_only_the_tenants_tank() -> None:
    sites = _Sites()

    with pytest.raises(NotFoundError):
        SiteService(sites, tank_repo=_Tanks()).create_location(
            Location(name="N", area_m2=1.0, site_key="site_own", tank_key="tank_foreign"), tenant_key=OWN
        )

    assert sites.writes == []


def test_an_own_tank_and_parent_are_accepted_on_update() -> None:
    sites = _Sites()
    sites.locations["loc_parent"] = Location(_key="loc_parent", name="P", area_m2=1.0, site_key="site_own")

    SiteService(sites, tank_repo=_Tanks()).update_location(
        "loc_own",
        Location(name="A", area_m2=1.0, site_key="site_own", parent_location_key="loc_parent", tank_key="tank_own"),
        tenant_key=OWN,
    )

    assert sites.writes == ["loc_own"]


# ── C5 actuator rule sensor location ────────────────────────────────────────


def _rule(**fields) -> ControlRule:
    return ControlRule(
        name="R",
        sensor_parameter="vpd",
        condition=RuleCondition(operator=ConditionOperator.GT, threshold=1.5),
        action=RuleAction(command=ActionCommand.TURN_ON),
        hysteresis=HysteresisConfig(
            on_threshold=1.5, off_threshold=1.2, min_on_duration_seconds=0, min_off_duration_seconds=0
        ),
        **fields,
    )


def _actuators() -> tuple[ActuatorService, FakeActuatorRepo]:
    repo = FakeActuatorRepo()
    repo.location_foreign = Location(_key="loc_foreign", name="X", area_m2=1.0, site_key="site_x")
    original = repo.get_location
    repo.get_location = lambda k: repo.location_foreign if k == "loc_foreign" else original(k)  # type: ignore[method-assign]
    from tests.unit.domain.services.test_actuator_service import _ha_actuator

    repo.actuators["act1"] = _ha_actuator()
    return ActuatorService(repo, site_repo=ActuatorSites()), repo


@pytest.mark.parametrize("location", ["loc_foreign", "no-such-location"])
def test_a_rule_reads_only_the_tenants_sensor_location(location: str) -> None:
    service, repo = _actuators()

    with pytest.raises(NotFoundError):
        service.create_rule("act1", "t1", _rule(sensor_location_key=location))

    assert repo.rules == {}


def test_a_rule_update_cannot_repoint_the_sensor_location() -> None:
    service, repo = _actuators()
    created = service.create_rule("act1", "t1", _rule(sensor_location_key="loc1"))

    with pytest.raises(NotFoundError):
        service.update_rule("act1", created.key, "t1", {"sensor_location_key": "loc_foreign"})

    assert repo.rules[created.key].sensor_location_key == "loc1"


# ── C10 task entity binding without an edge-writing type ────────────────────


@pytest.mark.parametrize("entity_type", [None, "generic", "plant", "actuator"])
def test_a_task_key_needs_an_edge_writing_type(entity_type: str | None) -> None:
    guard = TaskEntityGuard(MagicMock, MagicMock, MagicMock, MagicMock)

    with pytest.raises(ValidationError):
        guard.verify(entity_type, "some-key", tenant_key=OWN)


def test_a_system_task_keeps_its_free_binding() -> None:
    guard = TaskEntityGuard(MagicMock, MagicMock, MagicMock, MagicMock)

    guard.verify("actuator", "act1", tenant_key="")  # no tenant: the system context


# ── C13 succession plan species, and the fail-open anchors ─────────────────


def _succession(site_repo=object()):  # noqa: ANN001, ANN202
    from app.domain.services.succession_plan_service import SuccessionPlanService

    repo = MagicMock()
    repo.create.side_effect = lambda p: p
    sites = MagicMock() if site_repo is not None else None
    return SuccessionPlanService(repo, MagicMock(), site_repo=sites, species_resolver=_species), repo


def _plan(**fields):  # noqa: ANN003, ANN202
    from app.domain.models.succession_plan import SuccessionPlan

    return SuccessionPlan(
        tenant_key=OWN,
        name="S",
        species_key=fields.pop("species_key", "sp_own"),
        interval_days=14,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 1),
        plants_per_batch=4,
        **fields,
    )


def test_a_succession_plan_names_only_a_readable_species() -> None:
    service, repo = _succession()

    with pytest.raises(NotFoundError):
        service.create_plan(_plan(species_key="sp_foreign"))

    repo.create.assert_not_called()


def test_a_succession_plan_location_is_refused_without_the_anchor() -> None:
    # #1876 review SEC-004: without a site repository the check was skipped.
    service, repo = _succession(site_repo=None)

    with pytest.raises(NotFoundError):
        service.create_plan(_plan(location_key="loc_any"))

    repo.create.assert_not_called()


def test_a_run_location_is_refused_without_the_anchor() -> None:
    from app.domain.services.planting_run_service import PlantingRunService

    service = PlantingRunService(
        MagicMock(), MagicMock(), engine=MagicMock(), site_repo=None, species_resolver=_species
    )

    with pytest.raises(NotFoundError):
        service._require_owned_location_key("loc_any", OWN)  # noqa: SLF001


# ── C14 species default nutrient plan ───────────────────────────────────────


def _species_service():  # noqa: ANN202
    from app.domain.services.species_service import SpeciesService

    plans = MagicMock()
    plans.get_by_key.side_effect = lambda k: {
        "plan_global": SimpleNamespace(key=k, tenant_key=""),
        "plan_own": SimpleNamespace(key=k, tenant_key=OWN),
        "plan_foreign": SimpleNamespace(key=k, tenant_key="t_b"),
    }.get(k)
    return SpeciesService(MagicMock(), MagicMock(), nutrient_plan_repo=plans)


@pytest.mark.parametrize(
    "owner,plan,allowed",
    [
        (OWN, "plan_global", True),
        (OWN, "plan_own", True),
        (OWN, "plan_foreign", False),
        (OWN, "no-such-plan", False),
        ("", "plan_global", True),
        ("", "plan_own", False),  # a global species must not carry a tenant's private plan
    ],
)
def test_a_species_default_plan_is_global_or_the_owners(owner: str, plan: str, allowed: bool) -> None:
    service = _species_service()

    if allowed:
        service._require_usable_nutrient_plan(plan, owner)  # noqa: SLF001
    else:
        with pytest.raises(NotFoundError):
            service._require_usable_nutrient_plan(plan, owner)  # noqa: SLF001


# ── C15 substrate batch re-pointed on update ────────────────────────────────


def test_a_substrate_batch_update_cannot_repoint_to_a_foreign_substrate() -> None:
    from app.domain.models.substrate import SubstrateBatch
    from app.domain.services.substrate_service import SubstrateService

    repo = MagicMock()
    repo.get_batch_by_key.return_value = SubstrateBatch(
        _key="b1", batch_id="B1", volume_liters=10, mixed_on=date(2026, 1, 1), substrate_key="sub_own", tenant_key=OWN
    )
    service = SubstrateService(repo)
    service.get_batch = lambda key, tenant_key=None: repo.get_batch_by_key(key)  # type: ignore[method-assign]
    service.get_substrate = MagicMock(side_effect=NotFoundError("Substrate", "sub_foreign"))  # type: ignore[method-assign]
    service._authorize_batch_write = lambda *a: None  # type: ignore[method-assign]  # noqa: SLF001

    with pytest.raises(NotFoundError):
        service.update_batch(
            "b1",
            SubstrateBatch(batch_id="B1", volume_liters=10, mixed_on=date(2026, 1, 1), substrate_key="sub_foreign"),
            tenant_key=OWN,
        )

    repo.update_batch.assert_not_called()
    service.get_substrate.assert_called_once_with("sub_foreign", tenant_key=OWN)


# ── recurring task assignee (#1876 review, Info) ────────────────────────────


def test_a_recurring_task_does_not_carry_a_departed_assignee() -> None:
    from app.domain.models.task import Task
    from app.domain.services.task_service import TaskService

    repo = MagicMock()
    repo.create_task.side_effect = lambda t: t
    service = TaskService(repo, MagicMock(), MagicMock(), membership_lookup=lambda user, tenant: None)
    done = Task(
        _key="t1",
        tenant_key=OWN,
        name="Giessen",
        category="watering",
        recurrence_rule="FREQ=DAILY",
        assigned_to_user_key="u_left",
        due_date=datetime.now(UTC) - timedelta(days=1),
    )

    follow_up = service._create_next_recurring_task(done)  # noqa: SLF001

    assert follow_up is not None
    assert follow_up.assigned_to_user_key is None


# ── /code-review of #1899 ───────────────────────────────────────────────────


def test_a_location_cannot_move_below_its_own_descendant() -> None:
    # A→B→A made every ancestor walk (the location page's breadcrumb) loop forever.
    sites = _Sites()
    sites.locations["loc_child"] = Location(
        _key="loc_child", name="C", area_m2=1.0, site_key="site_own", parent_location_key="loc_own"
    )

    with pytest.raises(ValidationError):
        SiteService(sites, tank_repo=_Tanks()).update_location(
            "loc_own",
            Location(name="A", area_m2=1.0, site_key="site_own", parent_location_key="loc_child"),
            tenant_key=OWN,
        )

    assert sites.writes == []


def test_a_parent_location_lies_in_the_same_site() -> None:
    sites = _Sites()
    sites.locations["loc_other_site"] = Location(_key="loc_other_site", name="O", area_m2=1.0, site_key="site_own2")
    original = sites.get_site_by_key
    sites.get_site_by_key = lambda key: original("site_own" if key == "site_own2" else key)  # type: ignore[method-assign]

    with pytest.raises(ValidationError):
        SiteService(sites, tank_repo=_Tanks()).update_location(
            "loc_own",
            Location(name="A", area_m2=1.0, site_key="site_own", parent_location_key="loc_other_site"),
            tenant_key=OWN,
        )

    assert sites.writes == []
