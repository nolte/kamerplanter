"""#1444 — the nightly run says how many plants it cannot see.

``generate_due_care_reminders`` iterates **stored care profiles**. A plant without
one is therefore not "skipped" by it: it never enters the iteration, neither
counter is reached by it, and before this the run logged
``created=… skipped=…`` — two figures that describe only the profiled population —
and nothing else. A plant created before #1440, in a tenant where nobody ever
opened the care dashboard, received no REQ-022 reminder and no log line said so.

So the run now counts that population up front and warns. Four things are pinned
here, and the middle two are the ones that keep the warning honest:

* it fires, with the real count, when plants are unprofiled;
* it stays silent at zero — a warning on every run of a healthy installation is a
  warning nobody reads;
* it does NOT create anything: a nightly beat that writes profiles would be the
  "a path persists on the side" shape #1422 was filed over, moved into a task
  nobody watches;
* a failing count costs diagnostics, never a night of reminders.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
import structlog

from app.domain.interfaces.care_reminder_repository import ICareReminderRepository


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    """Install a mock ``app.common.dependencies`` so no ArangoDB import chain runs."""
    mock_deps = ModuleType("app.common.dependencies")
    for getter in (
        "get_care_reminder_service",
        "get_lifecycle_repo",
        "get_nutrient_plan_repo",
        "get_phase_sequence_repo",
        "get_plant_repo",
        "get_planting_run_repo",
        "get_season_state_repo",
        "get_task_repo",
    ):
        setattr(mock_deps, getter, MagicMock())
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)
    yield mock_deps


def _wire(deps, *, unprofiled):
    """A run with no profiles at all, whose unprofiled-plant count answers ``unprofiled``.

    No stored profiles on purpose: that is precisely the state in which the old
    ``created=0 skipped=0`` line was indistinguishable from "nothing was due".
    """
    care_service = MagicMock()
    # The repository double is spec'd against the real interface (SCR-005, and the
    # #1155 lesson). It was a bare MagicMock, and the assertion below then named
    # `create_profile`/`create_profile_edge` — methods the repository has not had
    # since #1292 — so the check could not fail whatever the run did. A spec'd
    # double raises AttributeError on a name that no longer exists, which is what
    # turns "asserted" back into "measured".
    care_service._repo = MagicMock(spec=ICareReminderRepository)
    care_service._repo.get_all_profiles.return_value = []
    if isinstance(unprofiled, Exception):
        care_service._repo.count_plants_without_profile.side_effect = unprofiled
    else:
        care_service._repo.count_plants_without_profile.return_value = unprofiled
    deps.get_care_reminder_service.return_value = care_service

    run_repo = MagicMock()
    run_repo.get_plant_keys_with_active_schedule.return_value = set()
    deps.get_planting_run_repo.return_value = run_repo
    deps.get_plant_repo.return_value = MagicMock()
    deps.get_nutrient_plan_repo.return_value = MagicMock()
    deps.get_lifecycle_repo.return_value = MagicMock()
    deps.get_phase_sequence_repo.return_value = None
    deps.get_task_repo.return_value = MagicMock()
    deps.get_season_state_repo.return_value = MagicMock()
    return care_service


def _run(**kwargs):
    from app.tasks.care_tasks import generate_due_care_reminders

    with structlog.testing.capture_logs() as logs:
        result = generate_due_care_reminders(**kwargs)
    return result, logs


def _events(logs, name):
    return [entry for entry in logs if entry.get("event") == name]


class TestUnprofiledPlantWarning:
    def test_the_run_warns_with_the_count(self, _mock_dependencies):
        service = _wire(_mock_dependencies, unprofiled=4)

        result, logs = _run()

        warnings = _events(logs, "plants_without_care_profile")
        assert len(warnings) == 1
        assert warnings[0]["count"] == 4
        assert warnings[0]["log_level"] == "warning"
        assert result == {"created": 0, "skipped": 0}, "the gap is reported beside the figures, not folded into them"
        service._repo.count_plants_without_profile.assert_called_once_with(tenant_key=None)

    def test_a_healthy_installation_stays_silent(self, _mock_dependencies):
        """The control. Without it, "always warn" would satisfy the case above and
        the line would carry no information."""
        _wire(_mock_dependencies, unprofiled=0)

        _result, logs = _run()

        assert _events(logs, "plants_without_care_profile") == []

    def test_a_scoped_run_counts_only_its_own_tenant(self, _mock_dependencies):
        """The manual trigger at ``POST /t/{slug}/tasks/generate-care-reminders``
        passes its caller's tenant. Counting installation-wide there would report
        another tenant's gap to a member who cannot see those plants — the #1204
        shape, one log line over."""
        service = _wire(_mock_dependencies, unprofiled=2)

        _result, logs = _run(tenant_key="tenant-a")

        service._repo.count_plants_without_profile.assert_called_once_with(tenant_key="tenant-a")
        warning = _events(logs, "plants_without_care_profile")[0]
        assert warning["tenant_key"] == "tenant-a"
        assert warning["scope"] == "tenant"

    def test_the_run_creates_no_profile_for_them(self, _mock_dependencies):
        """Reported, not repaired — creating the rows is the #1444 migration's job."""
        service = _wire(_mock_dependencies, unprofiled=3)

        _run()

        service.get_or_create_profile.assert_not_called()
        service._repo.create_linked_profile.assert_not_called()

    def test_a_failing_count_costs_diagnostics_and_not_the_run(self, _mock_dependencies):
        """Best-effort: the count is diagnostics, the reminders are the feature."""
        _wire(_mock_dependencies, unprofiled=RuntimeError("arango is having a night"))

        result, logs = _run()

        assert result == {"created": 0, "skipped": 0}
        failures = _events(logs, "care_profile_gap_count_failed")
        assert len(failures) == 1
        assert failures[0]["log_level"] == "error"
        assert _events(logs, "plants_without_care_profile") == []
