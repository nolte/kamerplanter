"""#2082 — the care reminders resolve a plant's stored species under the plant's tenant.

A legacy plant can carry another tenant's private ``species_key``. The care service must
treat that species as unknown (no frost gating, no name), and its species cache must not
hand one tenant's answer to another tenant asking for the same key.
"""

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import CareStyleType, FrostTolerance, HardinessRating, SeasonPhase, SpringAction, WinterAction
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.services.care_reminder_service import CareReminderService

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
KEY = "sp-private"


class _SpeciesRepo:
    """Just the three calls the visibility rule and the service make; grants are explicit."""

    def __init__(self, species: Species, granted_to: tuple[str, ...] = ()) -> None:
        self._species = species
        self._granted_to = granted_to

    def get_by_key(self, key: str) -> Species | None:
        return self._species if key == KEY else None

    def is_granted_to(self, key: str, tenant_key: str) -> bool:
        return key == KEY and tenant_key in self._granted_to

    def get_cultivar_by_key(self, key: str):  # noqa: ANN201
        return None


def _private_species() -> Species:
    return Species(
        _key=KEY,
        tenant_key=TENANT_B,
        scientific_name="Foreign private species",
        common_names=["Foreign private species"],
        family_key="Foreignaceae",
        frost_sensitivity=FrostTolerance.SENSITIVE,
    )


def _plant(tenant_key: str, plant_key: str) -> PlantInstance:
    return PlantInstance(
        _key=plant_key,
        tenant_key=tenant_key,
        instance_id=plant_key,
        species_key=KEY,
        plant_name=plant_key,
        planted_on=date(2024, 1, 1),
        site_key="site-1",
    )


def _owp(plant_key: str) -> OverwinteringProfile:
    return OverwinteringProfile(
        plant_key=plant_key,
        hardiness_rating=HardinessRating.NEEDS_PROTECTION,
        winter_action=WinterAction.MULCH,
        winter_action_month=10,
        spring_action=SpringAction.UNCOVER,
        spring_action_month=3,
    )


def _service(plants: dict[str, PlantInstance], species_repo: _SpeciesRepo) -> CareReminderService:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.side_effect = lambda key: CareProfile(
        care_style=CareStyleType.FROST_TENDER_TUBER, plant_key=key
    )
    task_repo = MagicMock()
    task_repo.find_open_care_task.return_value = None
    task_repo.create_task.side_effect = lambda t: t
    plant_repo = MagicMock()
    plant_repo.get_by_key.side_effect = plants.get
    overwintering_repo = MagicMock()
    overwintering_repo.get_profile_by_plant_key.side_effect = _owp
    return CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo=task_repo,
        plant_repo=plant_repo,
        species_repo=species_repo,
        overwintering_repo=overwintering_repo,
    )


def test_a_foreign_private_species_is_not_resolved_for_another_tenants_plant() -> None:
    service = _service({}, _SpeciesRepo(_private_species()))

    assert service._resolve_species(KEY, {}, TENANT_A) is None


def test_the_owning_tenant_and_a_grantee_resolve_the_species() -> None:
    service = _service({}, _SpeciesRepo(_private_species(), granted_to=(TENANT_A,)))

    assert service._resolve_species(KEY, {}, TENANT_B) is not None
    assert service._resolve_species(KEY, {}, TENANT_A) is not None


def test_the_species_cache_does_not_carry_one_tenants_answer_to_another() -> None:
    service = _service({}, _SpeciesRepo(_private_species()))
    cache: dict = {}

    owner_first = service._resolve_species(KEY, cache, TENANT_B)
    foreign_after = service._resolve_species(KEY, cache, TENANT_A)

    assert owner_first is not None
    assert foreign_after is None


def test_the_winter_gate_of_a_foreign_species_plant_gets_no_frost_data() -> None:
    plants = {"plant-a": _plant(TENANT_A, "plant-a"), "plant-b": _plant(TENANT_B, "plant-b")}
    service = _service(plants, _SpeciesRepo(_private_species()))
    seen: dict[str, FrostTolerance | None] = {}
    real = service._engine.should_generate_reminder

    def _spy(profile, reminder_type, **kwargs):  # noqa: ANN001, ANN202
        seen[profile.plant_key] = kwargs.get("frost_sensitivity")
        return real(profile, reminder_type, **kwargs)

    service._engine.should_generate_reminder = _spy

    service.ensure_seasonal_winter_tasks("plant-a", SeasonPhase.PRE_WINTER)
    service.ensure_seasonal_winter_tasks("plant-b", SeasonPhase.PRE_WINTER)

    assert seen["plant-b"] == FrostTolerance.SENSITIVE, "the owning tenant keeps its species' frost data"
    assert seen["plant-a"] is None, "a foreign species' frost data must not reach tenant A's reminders"


def test_the_care_inputs_of_a_foreign_species_plant_carry_no_species_data() -> None:
    plants = {"plant-a": _plant(TENANT_A, "plant-a"), "plant-b": _plant(TENANT_B, "plant-b")}
    service = _service(plants, _SpeciesRepo(_private_species()))

    foreign = service.care_inputs_for_plant("plant-a")
    owner = service.care_inputs_for_plant("plant-b")

    assert owner.family_name == "Foreignaceae"
    assert foreign.family_name is None
