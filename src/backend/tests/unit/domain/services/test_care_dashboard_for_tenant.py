"""Tests for CareReminderService.get_care_dashboard_for_tenant.

Covers the tenant-scoped care dashboard aggregation:
- active plants with due reminders produce entries,
- plants with ``removed_on`` set are excluded,
- an empty plant set yields an empty dashboard.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    FrostTolerance,
    HardinessRating,
    ReminderType,
    SpringAction,
    TuberStatus,
    WinterAction,
)
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.services.care_reminder_service import CareReminderService


@pytest.fixture
def engine() -> CareReminderEngine:
    return CareReminderEngine()


@pytest.fixture
def mock_care_repo() -> MagicMock:
    repo = MagicMock()
    # No prior confirmations -> reminders fall due based on profile.created_at.
    repo.get_last_confirmation.return_value = None
    return repo


@pytest.fixture
def mock_plant_repo() -> MagicMock:
    return MagicMock()


def _profile(plant_key: str) -> CareProfile:
    """A watering-enabled profile created far in the past (so watering is overdue)."""
    return CareProfile(
        watering_interval_days=7,
        winter_watering_multiplier=1.5,
        plant_key=plant_key,
        auto_generated=True,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def _plant(key: str, *, removed: bool = False) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key="tenant-1",
        instance_id=f"instance-{key}",
        species_key="species-1",
        plant_name=f"Plant {key}",
        planted_on=date(2024, 1, 1),
        removed_on=date(2024, 6, 1) if removed else None,
    )


def _build_service(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> CareReminderService:
    return CareReminderService(
        mock_care_repo,
        engine,
        plant_repo=mock_plant_repo,
        species_repo=MagicMock(get_by_key=MagicMock(return_value=None)),
        nutrient_plan_repo=MagicMock(get_plant_plan=MagicMock(return_value=None)),
    )


def test_returns_entries_for_active_plants_with_due_reminders(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    plant = _plant("plant-1")
    mock_plant_repo.get_all.return_value = ([plant], 1)
    mock_care_repo.get_profile_by_plant_key.return_value = _profile("plant-1")

    service = _build_service(mock_care_repo, engine, mock_plant_repo)
    entries = service.get_care_dashboard_for_tenant("tenant-1")

    mock_plant_repo.get_all.assert_called_once_with(offset=0, limit=500, tenant_key="tenant-1")
    assert entries, "expected at least one due reminder entry for the active plant"
    assert all(e.plant_key == "plant-1" for e in entries)
    assert entries[0].plant_name == "Plant plant-1"


def test_excludes_removed_plants(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    active = _plant("plant-active")
    removed = _plant("plant-removed", removed=True)
    mock_plant_repo.get_all.return_value = ([active, removed], 2)
    mock_care_repo.get_profile_by_plant_key.side_effect = lambda pk: _profile(pk)

    service = _build_service(mock_care_repo, engine, mock_plant_repo)
    entries = service.get_care_dashboard_for_tenant("tenant-1")

    plant_keys = {e.plant_key for e in entries}
    assert "plant-active" in plant_keys
    assert "plant-removed" not in plant_keys
    # The removed plant must never trigger a profile lookup.
    looked_up = {call.args[0] for call in mock_care_repo.get_profile_by_plant_key.call_args_list}
    assert "plant-removed" not in looked_up


def test_returns_empty_when_no_plants(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    mock_plant_repo.get_all.return_value = ([], 0)

    service = _build_service(mock_care_repo, engine, mock_plant_repo)
    entries = service.get_care_dashboard_for_tenant("tenant-1")

    assert entries == []
    mock_care_repo.get_profile_by_plant_key.assert_not_called()


def test_generates_winter_reminders_from_overwintering_profile(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    """B1 — a frost-tender plant with a dig-and-store overwintering profile must
    surface the winter-protection / tuber-dig / storage-check reminders."""
    plant = _plant("plant-1")
    mock_plant_repo.get_all.return_value = ([plant], 1)
    mock_care_repo.get_profile_by_plant_key.return_value = _profile("plant-1")

    current_month = date.today().month
    owp = OverwinteringProfile(
        plant_key="plant-1",
        hardiness_rating=HardinessRating.DIG_AND_STORE,
        winter_action=WinterAction.DIG_STORE,
        winter_action_month=current_month,
        spring_action=SpringAction.REPLANT,
        spring_action_month=3,
        storage_check_interval_days=30,
        tuber_status=TuberStatus.STORED,
    )
    overwintering_repo = MagicMock()
    overwintering_repo.get_profile_by_plant_key.return_value = owp

    species = Species(scientific_name="Dahlia pinnata", frost_sensitivity=FrostTolerance.SENSITIVE)
    species_repo = MagicMock(
        get_by_key=MagicMock(return_value=species),
        get_cultivar_by_key=MagicMock(return_value=None),
    )

    service = CareReminderService(
        mock_care_repo,
        engine,
        plant_repo=mock_plant_repo,
        species_repo=species_repo,
        nutrient_plan_repo=MagicMock(get_plant_plan=MagicMock(return_value=None)),
        overwintering_repo=overwintering_repo,
    )
    entries = service.get_care_dashboard_for_tenant("tenant-1")

    reminder_types = {e.reminder_type for e in entries}
    assert ReminderType.WINTER_PROTECTION in reminder_types
    assert ReminderType.TUBER_DIG in reminder_types
    assert ReminderType.STORAGE_CHECK in reminder_types
    overwintering_repo.get_profile_by_plant_key.assert_called_once_with("plant-1")


def test_no_winter_reminders_without_overwintering_repo(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    """Existing non-winter behaviour is unchanged when no overwintering repo is
    wired: winter reminder types never appear."""
    plant = _plant("plant-1")
    mock_plant_repo.get_all.return_value = ([plant], 1)
    mock_care_repo.get_profile_by_plant_key.return_value = _profile("plant-1")

    service = _build_service(mock_care_repo, engine, mock_plant_repo)
    entries = service.get_care_dashboard_for_tenant("tenant-1")

    winter_types = {
        ReminderType.WINTER_PROTECTION,
        ReminderType.SPRING_UNCOVER,
        ReminderType.TUBER_DIG,
        ReminderType.STORAGE_CHECK,
    }
    assert not ({e.reminder_type for e in entries} & winter_types)
