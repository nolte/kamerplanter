"""#1834 — the reconciliation ships report-only, with a floor that cannot be set away."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_the_reconciliation_is_report_only_unless_an_operator_arms_it():
    """Operator decision (Datenschutzplan): the first release deletes nothing.

    A default flipped to true arms a nightly job that removes stored bytes on every
    installation that has not set the variable; the diff line that does it reads
    like a tuning change. Change this test only with the reasoning in the issue.
    """
    assert Settings().storage_reconcile_delete_enabled is False


def test_the_safety_margin_ships_at_24_hours():
    assert Settings().storage_reconcile_min_age_hours == 24


@pytest.mark.parametrize("hours", [0, -1])
def test_the_safety_floor_cannot_be_set_below_the_upload_window(hours):
    """An upload writes the object before its record; a zero floor deletes it in flight."""
    with pytest.raises(ValidationError):
        Settings(storage_reconcile_min_age_hours=hours)


def test_the_floor_and_the_switch_are_settable():
    armed = Settings(storage_reconcile_delete_enabled=True, storage_reconcile_min_age_hours=48)
    assert armed.storage_reconcile_delete_enabled is True
    assert armed.storage_reconcile_min_age_hours == 48


@pytest.mark.parametrize("fraction", [0, -0.1, 1.5])
def test_the_orphan_brake_must_be_a_share_between_zero_and_one(fraction):
    with pytest.raises(ValidationError):
        Settings(storage_reconcile_max_orphan_fraction=fraction)


def test_the_orphan_brake_ships_at_half():
    assert Settings().storage_reconcile_max_orphan_fraction == 0.5
