"""Request-path reads must see every row, not the first ``get_all`` page (#2015).

Each service below read ``repo.get_all(offset=0, limit=<N>, ...)`` once and treated
the page as the collection. Past ``N`` rows the rest were silently dropped: a plant
missing from the care dashboard and the printed checklist, a tank whose maintenance
was never reported due, an existing species not recognised as an import duplicate,
an activity left out of a generated plan, a species left out of the sowing calendar,
a CalMag product reported as absent.

Every test drives the **real service method** with a repository double holding one
row more than the old window, the row that matters placed **last** in the
repository's sort order, and asserts on the collection the service built from the
read. The doubles page like the real repositories: same ``get_all`` signature (an
argument the real one does not take is a ``TypeError`` here too), same sort order,
``offset``/``limit`` honoured, the full ``total``, and the same ``ValueError`` for a
tenant-scoped collection read without ``tenant_key``/``all_tenants``.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from app.common.enums import EntityType, FertilizerType
from app.domain.models.activity import Activity
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.models.tank import Tank
from app.domain.services.activity_plan_service import ActivityPlanService
from app.domain.services.calendar_service import CalendarService
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.import_service import ImportService
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.print_service import PrintService
from app.domain.services.tank_service import TankService

TENANT = "t-1"


def _window(rows: list[Any], offset: int, limit: int) -> tuple[list[Any], int]:
    if limit < 1 or offset < 0:
        raise ValueError("bad paging window")
    return list(rows[offset : offset + limit]), len(rows)


def _scope(tenant_key: str | None, all_tenants: bool) -> None:
    # BaseArangoRepository._enforce_tenant_scope: "" counts as "not provided".
    if not tenant_key and not all_tenants:
        raise ValueError("tenant-scoped: pass a tenant_key or all_tenants=True")


class _OwnedKeyed:
    """A tenant-scoped collection sorted by ``_key`` (``BaseArangoRepository.get_all``)."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = sorted(rows, key=lambda r: r.key)
        self.calls = 0

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        _scope(tenant_key, all_tenants)
        self.calls += 1
        rows = self.rows if all_tenants and not tenant_key else [r for r in self.rows if r.tenant_key == tenant_key]
        return _window(rows, offset, limit)


class _TankRepo(_OwnedKeyed):
    """``ArangoTankRepository.get_all(offset, limit, filters, tenant_key, *, all_tenants)``."""

    def get_all(self, offset=0, limit=50, filters=None, tenant_key=None, *, all_tenants=False):  # type: ignore[override]
        assert not filters
        return super().get_all(offset, limit, tenant_key, all_tenants=all_tenants)


class _SpeciesRepo:
    """``ArangoSpeciesRepository.get_all(offset, limit, *, tenant_key)``: ``None`` = whole catalogue."""

    def __init__(self, rows: list[Species]) -> None:
        self.rows = sorted(rows, key=lambda r: r.key or "")

    def get_all(self, offset=0, limit=50, *, tenant_key=None):
        if tenant_key is None:
            return _window(self.rows, offset, limit)
        return _window([r for r in self.rows if r.tenant_key in ("", tenant_key)], offset, limit)


class _CatalogueRepo:
    """A global, not tenant-scoped catalogue on the base ``get_all`` (botanical families)."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = sorted(rows, key=lambda r: r.key)

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        return _window(self.rows, offset, limit)


class _ActivityRepo:
    """``ArangoActivityRepository.get_all(offset, limit, filters)``: no tenant arguments."""

    def __init__(self, rows: list[Activity]) -> None:
        self.rows = sorted(rows, key=lambda r: r.key or "")

    def get_all(self, offset=0, limit=50, filters=None):
        assert not filters
        return _window(self.rows, offset, limit)


class _FertilizerRepo:
    """``ArangoFertilizerRepository.get_all``: hybrid union, equality filters, sorted by name then key."""

    def __init__(self, rows: list[Fertilizer]) -> None:
        self.rows = sorted(rows, key=lambda r: (r.product_name, r.key or ""))

    def get_all(self, offset=0, limit=50, filters=None, tenant_key=None, *, all_tenants=False):
        _scope(tenant_key, all_tenants)
        rows = self.rows if not tenant_key else [r for r in self.rows if r.tenant_key in ("", tenant_key)]
        for field, value in (filters or {}).items():
            rows = [r for r in rows if _value(getattr(r, field)) == value]
        return _window(rows, offset, limit)


def _value(v: Any) -> Any:
    return getattr(v, "value", v)


def _plant(i: int) -> PlantInstance:
    return PlantInstance(
        _key=f"p{i:05d}",
        tenant_key=TENANT,
        instance_id=f"i{i:05d}",
        species_key="",
        plant_name=f"Plant {i:05d}",
        planted_on=date(2024, 1, 1),
    )


# ── care dashboard (care_reminder_service._build_plant_data_for_tenant, old limit 500) ──


def test_care_dashboard_sees_the_plant_past_the_old_500_window() -> None:
    plants = [_plant(i) for i in range(501)]
    service = CareReminderService(
        MagicMock(),
        MagicMock(),
        plant_repo=_OwnedKeyed(plants),
        species_repo=MagicMock(get_by_key=MagicMock(return_value=None)),
        nutrient_plan_repo=MagicMock(get_plant_plan=MagicMock(return_value=None)),
    )

    plant_data = service._build_plant_data_for_tenant(TENANT)

    assert [d["plant_key"] for d in plant_data] == [p.key for p in plants]


# ── printed care checklist (print_service.generate_care_checklist_pdf, old limit 500) ──


def test_care_checklist_pdf_hands_every_plant_to_the_dashboard() -> None:
    plants = [_plant(i) for i in range(501)]
    care = MagicMock()
    care.get_care_dashboard.return_value = []
    engine = MagicMock()
    engine.render_pdf.return_value = b"%PDF"
    service = PrintService(
        nutrient_plan_service=MagicMock(),
        care_reminder_service=care,
        fertilizer_repo=MagicMock(),
        plant_repo=_OwnedKeyed(plants),
        species_repo=MagicMock(),
        print_engine=engine,
        site_repo=MagicMock(),
        app_base_url="https://app.example.com",
    )

    service.generate_care_checklist_pdf(TENANT)

    plant_data = care.get_care_dashboard.call_args[0][0]
    assert [d["plant_key"] for d in plant_data] == [p.key for p in plants]


# ── due maintenances across tanks (tank_service.get_all_due_maintenances, old limit 1000) ──


def test_due_maintenances_cover_the_tank_past_the_old_1000_window() -> None:
    tanks = [
        Tank(_key=f"tk{i:05d}", tenant_key=TENANT, name=f"Tank {i:05d}", tank_type="nutrient", volume_liters=10)
        for i in range(1001)
    ]
    service = TankService(_TankRepo(tanks), MagicMock())
    service.get_due_maintenances = lambda tank_key: [{"tank_key": tank_key}]  # type: ignore[method-assign]

    dues = service.get_all_due_maintenances(tenant_key=TENANT)

    assert [d["tank_key"] for d in dues] == [t.key for t in tanks]


# ── import duplicate detection (import_service._get_existing_keys, old limit 10000) ──


def test_import_duplicate_check_sees_the_species_past_the_old_10000_window() -> None:
    rows = [SimpleNamespace(key=f"s{i:06d}", scientific_name=f"Genus species{i:06d}") for i in range(10_001)]
    service = ImportService(MagicMock(), species_repo=_CatalogueRepo(rows))

    existing = service._get_existing_keys(EntityType.SPECIES)

    assert existing == {r.scientific_name for r in rows}


def test_import_duplicate_check_sees_the_family_past_the_old_10000_window() -> None:
    rows = [SimpleNamespace(key=f"f{i:06d}", name=f"Familyaceae{i:06d}") for i in range(10_001)]
    service = ImportService(MagicMock(), family_repo=_CatalogueRepo(rows))

    existing = service._get_existing_keys(EntityType.BOTANICAL_FAMILY)

    assert existing == {r.name for r in rows}


def test_import_duplicate_check_reads_the_species_catalogue_through_its_real_signature() -> None:
    """The species repository takes no ``all_tenants``; the read must not invent one."""
    rows = [Species(_key=f"s{i:04d}", scientific_name=f"Genus species{i:04d}", tenant_key="t-x") for i in range(3)]
    service = ImportService(MagicMock(), species_repo=_SpeciesRepo(rows))

    assert service._get_existing_keys(EntityType.SPECIES) == {r.scientific_name for r in rows}


# ── generated activity plan (activity_plan_service.generate_plan, old limit 500) ──


def test_generated_plan_is_offered_every_catalogue_activity() -> None:
    activities = [Activity(_key=f"a{i:05d}", name=f"Activity {i:05d}") for i in range(501)]
    engine = MagicMock()
    engine.generate_plan.return_value = (MagicMock(), [])
    phase_repo = MagicMock()
    phase_repo.get_lifecycle_by_species.return_value = SimpleNamespace(key="lc1")
    phase_repo.get_phases_by_lifecycle.return_value = [MagicMock()]
    service = ActivityPlanService(
        engine,
        _ActivityRepo(activities),
        phase_repo,
        MagicMock(),
        MagicMock(),
        species_repo=MagicMock(get_by_key=MagicMock(return_value=None)),
    )

    service.generate_plan("sp1")

    offered = engine.generate_plan.call_args.kwargs["activities"]
    assert [a.key for a in offered] == [a.key for a in activities]


# ── sowing calendar (calendar_service.get_sowing_calendar, old limit 5000) ──


def test_sowing_calendar_considers_the_species_past_the_old_5000_window() -> None:
    species = [
        Species(_key=f"s{i:05d}", scientific_name=f"Genus species{i:05d}", direct_sow_months=[4], tenant_key="")
        for i in range(5001)
    ]
    sowing = MagicMock()
    sowing.build_calendar.return_value = []
    service = CalendarService(
        MagicMock(), MagicMock(), MagicMock(), species_repo=_SpeciesRepo(species), sowing_engine=sowing
    )

    service.get_sowing_calendar(None, 2026, tenant_key=TENANT)

    species_data = sowing.build_calendar.call_args[0][0]
    assert [d.key for d in species_data] == [s.key for s in species]


# ── CalMag lookup (nutrient_plan_service._find_calmag_product, old limit 100) ──


def _supplement(key: str, name: str, tenant_key: str = "") -> Fertilizer:
    return Fertilizer(
        _key=key, product_name=name, fertilizer_type=FertilizerType.SUPPLEMENT, tenant_key=tenant_key, brand="b"
    )


def test_calmag_sorted_past_the_old_100_window_is_found() -> None:
    rows = [_supplement(f"f{i:04d}", f"Additive {i:04d}") for i in range(100)]
    rows.append(_supplement("f9999", "CalMag Pro"))
    service = NutrientPlanService(MagicMock(), _FertilizerRepo(rows), MagicMock())

    found = service._find_calmag_product(TENANT)

    assert found is not None and found.key == "f9999"


def test_calmag_lookup_without_tenant_reads_all_tenants_and_keeps_the_filter() -> None:
    rows = [_supplement(f"f{i:04d}", f"Additive {i:04d}", tenant_key="t-other") for i in range(100)]
    rows.append(
        Fertilizer(_key="f0000x", product_name="Base CalMag", fertilizer_type=FertilizerType.BASE, brand="b")
    )  # not a supplement: the filter must still exclude it
    rows.append(_supplement("f9999", "CalMag Pro", tenant_key="t-other"))
    service = NutrientPlanService(MagicMock(), _FertilizerRepo(rows), MagicMock())

    found = service._find_calmag_product("")

    assert found is not None and found.key == "f9999"
