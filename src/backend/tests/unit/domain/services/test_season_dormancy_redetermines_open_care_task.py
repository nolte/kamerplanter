"""ADR-008 F-8 acceptance-4 — an ENGINE-driven interval change retimes the open task AND its note.

The user's interval edit (:meth:`CareReminderService.update_profile`) has retimed
the pending care task and its in-app notification since #622/#742/#769. It is
the template here, deliberately not the test target: a pairing test on that path
would certify behaviour that was already green.

The edge under test is the one nobody edits. The REQ-047 season state machine
switches a plant into the dormancy-care regime on ``winter_dormancy`` and out of
it on ``pre_spring``/``growing`` (:class:`DormancyCareActivator`), and that
switch changes what :meth:`CareReminderEngine._get_interval_days` answers for
watering (REQ-047 §3.5: ``minimal`` → 38 days). Before F-8 the open watering task
kept its pre-switch date until it was completed — and its notification with it.

**Both halves are asserted on the same pass**, so the test fails when either is
missing: the task's ``due_date`` (half 1) and the care note's ``due_date`` /
body (half 2). Every collaborator between the season transition and the two
stores is real — :class:`SeasonStateService`, :class:`DormancyCareActivator`,
:class:`CareReminderService`, :class:`CareReminderEngine`,
:class:`NotificationPropagationService` — over stateful fakes, so no mock can
answer for a step that did not happen.

The edge also carries the owner's two invariants (F-8 acceptance-2/-3): a repeated
transition converges on one note and one task write; no resolvable tenant writes
nothing.

Traces to issue #1061, feature F-8 (no TC-ID: a service-level pairing test).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.enums import (
    ConfirmAction,
    ReminderType,
    SeasonPhase,
    SiteType,
    TaskCategory,
    TaskStatus,
    WinterWatering,
)
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.season_state_engine import SeasonStateTransition
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.notification import Notification, NotificationStatus
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.dormancy_care_activator import DormancyCareActivator
from app.domain.services.notification_propagation_service import NotificationPropagationService
from app.domain.services.season_state_service import SeasonStateService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo
from tests.unit.domain.services.notification_fakes import FakeNotificationRepo

TENANT = "tenant-1"
OTHER_TENANT = "tenant-2"
USER = "user-a"
PLANT_KEY = "plant-1"
PLANT_LABEL = "Fuchsia"
CARE_GROUP = f"care.{ReminderType.WATERING.value}:{PLANT_KEY}"

BASE_INTERVAL = 7
#: REQ-047 §3.5 — the ``minimal`` dormancy watering regime.
DORMANT_INTERVAL = 38
CONFIRMED_AT = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
ANCHOR = datetime(2026, 11, 2, tzinfo=UTC)
NORMAL_DUE = ANCHOR + timedelta(days=BASE_INTERVAL)
DORMANT_DUE = ANCHOR + timedelta(days=DORMANT_INTERVAL)


class _CareRepo:
    """Stateful slice of ``ICareReminderRepository``: the activator's write is visible to the retiming read."""

    def __init__(self, profile: CareProfile) -> None:
        self.profile = profile
        self.profile_writes = 0

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None:
        return self.profile.model_copy(deep=True) if plant_key == self.profile.plant_key else None

    def update_profile(self, _key: str, profile: CareProfile) -> CareProfile:
        self.profile = profile.model_copy(deep=True)
        self.profile_writes += 1
        return profile

    def get_last_confirmation(self, plant_key: str, reminder_type: ReminderType) -> CareConfirmation | None:
        if plant_key != PLANT_KEY or reminder_type != ReminderType.WATERING:
            return None
        return CareConfirmation(
            _key="conf-1",
            plant_key=PLANT_KEY,
            care_profile_key="cp-1",
            reminder_type=ReminderType.WATERING,
            action=ConfirmAction.CONFIRMED,
            confirmed_at=CONFIRMED_AT,
        )


def _profile(*, dormant: bool = False, regime: WinterWatering = WinterWatering.MINIMAL) -> CareProfile:
    return CareProfile(
        _key="cp-1",
        plant_key=PLANT_KEY,
        watering_interval_days=BASE_INTERVAL,
        winter_watering_multiplier=1.0,
        auto_create_watering_task=True,
        adaptive_learning_enabled=False,
        dormancy_care_mode=dormant,
        dormancy_watering=regime.value if dormant else None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _open_watering_task(due: datetime, *, tenant_key: str = TENANT) -> Task:
    # The instruction as the daily producer builds it (`ensure_next_watering_task`
    # passes no phase interval into the text), not as the retiming path would.
    return Task(
        _key="task-water",
        name=f"{PLANT_LABEL} — {ReminderType.WATERING.value}",
        instruction=f"Water {PLANT_LABEL} (every {BASE_INTERVAL} days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=tenant_key,
        status=TaskStatus.PENDING,
        due_date=due,
    )


def _seed_care_note(repo: FakeNotificationRepo, due: datetime) -> Notification:
    note = repo.create(
        Notification(
            tenant_key=TENANT,
            user_key=USER,
            notification_type=f"care.{ReminderType.WATERING.value}",
            title=PLANT_LABEL,
            body=f"{ReminderType.WATERING.value} due on {due.date().isoformat()}: {PLANT_LABEL}",
            data={"plant_key": PLANT_KEY, "task_key": "task-water", "due_date": due.isoformat()},
            group_key=CARE_GROUP,
            status=NotificationStatus.DELIVERED,
        )
    )
    note.read_at = CONFIRMED_AT  # the user has seen it; a retiming must not resurface it (#769)
    return note


class _PhaseCoupler:
    """ADR-006 E3 stand-in: moves the plant into its dormancy growth phase, as the real coupler's transition does."""

    def __init__(self, care_plant: SimpleNamespace, dormancy_phase_key: str) -> None:
        self._care_plant = care_plant
        self._dormancy_phase_key = dormancy_phase_key

    def enter_dormancy(self, _plant: PlantInstance) -> bool:
        self._care_plant.current_phase_key = self._dormancy_phase_key
        return True

    def restart_cycle(self, _plant: PlantInstance) -> bool:
        return False


class _World:
    """The season service wired to real collaborators over stateful fakes."""

    def __init__(
        self,
        *,
        dormant: bool,
        task_due: datetime,
        plant_tenant: str = TENANT,
        regime: WinterWatering = WinterWatering.MINIMAL,
        phase_key: str | None = None,
        phase_intervals: dict[str, int] | None = None,
        dormancy_phase_key: str | None = None,
    ) -> None:
        self.care_repo = _CareRepo(_profile(dormant=dormant, regime=regime))
        self.task_repo = FakeTaskRepo([_open_watering_task(task_due)])
        self.notification_repo = FakeNotificationRepo()
        _seed_care_note(self.notification_repo, task_due)

        care_plant = SimpleNamespace(
            key=PLANT_KEY,
            plant_name=PLANT_LABEL,
            instance_id="FU-1",
            tenant_key=plant_tenant,
            current_phase_key=phase_key,
            slot_key=None,
            removed_on=None,
        )
        self.care_plant = care_plant
        intervals = phase_intervals or {}
        lifecycle_repo = MagicMock()
        lifecycle_repo.get_phase_by_key.side_effect = lambda key: (
            SimpleNamespace(watering_interval_days=intervals[key]) if key in intervals else None
        )
        care_plant_repo = MagicMock()
        care_plant_repo.get_by_key.return_value = care_plant
        care_plant_repo.get_or_raise.return_value = care_plant
        self.care_service = CareReminderService(
            self.care_repo,
            CareReminderEngine(),
            self.task_repo,
            plant_repo=care_plant_repo,
            lifecycle_repo=lifecycle_repo,
            notification_propagation=NotificationPropagationService(self.notification_repo),
        )

        overwintering_repo = MagicMock()
        overwintering_repo.get_profile_by_plant_key.return_value = OverwinteringProfile.model_construct(
            key="ow-1",
            plant_key=PLANT_KEY,
            winter_watering=regime,
            storage_check_interval_days=None,
            dormancy_care_active=dormant,
        )
        season_plant_repo = MagicMock()
        season_plant_repo.find_by_field.return_value = [
            PlantInstance(
                _key=PLANT_KEY,
                tenant_key=TENANT,
                instance_id="FU-1",
                species_key="species-1",
                planted_on=date(2024, 1, 1),
                site_key="site-1",
            )
        ]
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        self.season = SeasonStateService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),  # materializer
            DormancyCareActivator(self.care_repo),
            self.care_service,
            overwintering_repo,
            season_plant_repo,
            site_repo,
            phase_coupler=_PhaseCoupler(care_plant, dormancy_phase_key) if dormancy_phase_key else None,
        )

    def transition(self, to_phase: SeasonPhase) -> None:
        self.season._apply_side_effects(
            Site(key="site-1", tenant_key=TENANT, name="Garden", type=SiteType.OUTDOOR),
            SeasonStateTransition(
                changed=True,
                from_phase=SeasonPhase.GROWING,
                to_phase=to_phase,
                season_year=2026,
                consecutive_signal_days=0,
                reason_i18n_key="pages.season.trigger.frostForecast",
            ),
        )

    def task(self) -> Task:
        tasks = self.task_repo.open_care_tasks(ReminderType.WATERING)
        assert len(tasks) == 1, f"expected exactly one open watering task, got {len(tasks)}"
        return tasks[0]

    def note(self) -> Notification:
        rows = [row for row in self.notification_repo.all_rows() if row.group_key == CARE_GROUP]
        assert len(rows) == 1, f"expected exactly one care note, got {len(rows)}"
        return rows[0]


# ── acceptance-4: both halves, one pass ─────────────────────────────────────


def test_entering_dormancy_retimes_the_open_task_and_its_note_in_the_same_pass() -> None:
    world = _World(dormant=False, task_due=NORMAL_DUE)

    world.transition(SeasonPhase.WINTER_DORMANCY)

    # The engine's answer did change — otherwise the two assertions below would be vacuous.
    assert world.care_repo.profile.dormancy_care_mode is True
    # Half 1 — the open task moved to the dormancy cadence.
    task = world.task()
    assert task.due_date == DORMANT_DUE
    assert task.instruction == f"Water {PLANT_LABEL} (every {DORMANT_INTERVAL} days)."
    # Half 2 — its notification followed, in place (single entry, same recipient, read state kept).
    note = world.note()
    assert note.data["due_date"] == DORMANT_DUE.isoformat()
    assert note.data["task_key"] == task.key
    assert DORMANT_DUE.date().isoformat() in note.body
    assert NORMAL_DUE.date().isoformat() not in note.body
    assert note.user_key == USER
    assert note.read_at == CONFIRMED_AT


def test_leaving_dormancy_retimes_the_open_task_and_its_note_back() -> None:
    world = _World(dormant=True, task_due=DORMANT_DUE)

    world.transition(SeasonPhase.GROWING)

    assert world.care_repo.profile.dormancy_care_mode is False
    assert world.task().due_date == NORMAL_DUE
    note = world.note()
    assert note.data["due_date"] == NORMAL_DUE.isoformat()
    assert NORMAL_DUE.date().isoformat() in note.body


# ── acceptance-2: idempotent on this edge ───────────────────────────────────


def test_a_repeated_transition_leaves_one_note_and_writes_the_task_once() -> None:
    world = _World(dormant=False, task_due=NORMAL_DUE)

    world.transition(SeasonPhase.WINTER_DORMANCY)
    world.transition(SeasonPhase.WINTER_DORMANCY)

    assert world.task().due_date == DORMANT_DUE
    assert world.note().data["due_date"] == DORMANT_DUE.isoformat()
    assert len(world.task_repo.updated) == 1, "the second pass found nothing to move and must write nothing"


# ── no real switch, no write ────────────────────────────────────────────────


def test_a_hand_moved_task_of_a_never_dormant_plant_survives_spring_and_growing() -> None:
    """``deactivate`` runs for every frost-exposed plant; only a real regime switch may retime.

    The user moved the task three days out. ``pre_spring`` and ``growing`` leave a
    plant that never was dormant in the same regime, so recomputing its task from
    the last confirmation would silently undo the user's date.
    """
    moved = NORMAL_DUE + timedelta(days=3)
    world = _World(dormant=False, task_due=moved)
    note_before = world.note().model_copy(deep=True)

    world.transition(SeasonPhase.PRE_SPRING)
    world.transition(SeasonPhase.GROWING)

    assert world.task_repo.updated == []
    assert world.task().due_date == moved
    assert world.note() == note_before


def test_a_phase_interval_task_is_not_rewritten_when_the_regime_did_not_switch() -> None:
    """The stored instruction ignores the phase interval; that difference is not a cadence change."""
    phase_due = ANCHOR + timedelta(days=10)
    world = _World(dormant=False, task_due=phase_due, phase_key="phase-veg", phase_intervals={"phase-veg": 10})
    note_before = world.note().model_copy(deep=True)

    world.transition(SeasonPhase.GROWING)

    assert world.task_repo.updated == []
    assert world.note() == note_before


def test_the_new_growth_phase_feeds_the_retimed_interval() -> None:
    """The redetermination runs AFTER the ADR-006 phase coupling: ``reduced`` scales the dormancy phase's base.

    Vegetative base 7 → ``reduced`` would give 10; the dormancy growth phase's
    base 10 gives 15. Retiming before the coupler moved the phase lands on 10.
    """
    world = _World(
        dormant=False,
        task_due=NORMAL_DUE,
        regime=WinterWatering.REDUCED,
        phase_key="phase-veg",
        phase_intervals={"phase-veg": BASE_INTERVAL, "phase-dormant": 10},
        dormancy_phase_key="phase-dormant",
    )

    world.transition(SeasonPhase.WINTER_DORMANCY)

    expected = ANCHOR + timedelta(days=15)
    assert world.task().due_date == expected
    assert world.note().data["due_date"] == expected.isoformat()


# ── acceptance-3: fail-closed per tenant on this edge ───────────────────────


def test_no_resolvable_tenant_writes_nothing() -> None:
    world = _World(dormant=True, task_due=NORMAL_DUE)
    note_before = world.note().model_copy(deep=True)

    retimed = world.care_service.redetermine_open_care_task(PLANT_KEY, ReminderType.WATERING, tenant_key="")

    assert retimed is None
    assert world.task_repo.updated == []
    assert world.note() == note_before


def test_a_plant_of_another_tenant_writes_nothing() -> None:
    """The season run's tenant does not own the plant the care service would retime."""
    world = _World(dormant=False, task_due=NORMAL_DUE, plant_tenant=OTHER_TENANT)
    note_before = world.note().model_copy(deep=True)

    world.transition(SeasonPhase.WINTER_DORMANCY)

    assert world.task_repo.updated == []
    assert world.note() == note_before
