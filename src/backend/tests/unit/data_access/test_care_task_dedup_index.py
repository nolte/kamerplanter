"""The care-task dedup index and the dedup *lookup* must agree on "open" (#1301).

``ensure_care_task_dedup_index`` constrains the tasks whose status the computed
value calls open; ``ArangoTaskRepository.find_open_care_task`` skips creation for
the tasks whose status *it* calls open. If those two sets ever drift apart, one of
them is silently wrong:

* a status the lookup treats as open but the index does not → the constraint stops
  covering it and #1301's race comes back for that status;
* a status the index treats as open but the lookup does not → the application
  believes it may create a task that storage will reject, turning a normal
  generation run into a rejected insert.

Both halves are string lists in two different modules, which is exactly the shape
that drifts, so this pins them to each other. Pure module-attribute assertions —
no database, no connection (#978).
"""

from __future__ import annotations

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository


def test_index_and_lookup_agree_on_open_statuses():
    assert col.CARE_TASK_OPEN_STATUSES == ArangoTaskRepository._CARE_OPEN_STATUSES


def test_open_statuses_are_real_task_statuses():
    """Guards against a typo that would make the expression match nothing."""
    valid = {status.value for status in TaskStatus}
    assert set(col.CARE_TASK_OPEN_STATUSES) <= valid


def test_completed_is_not_an_open_status():
    """The whole point of the *sparse* index: completed care tasks stay unconstrained.

    A plant is watered many times, and each watering leaves another completed task
    with the same name. An index that covered them would reject the second one and
    break normal use — worse than the duplicate bug it set out to fix.
    """
    assert TaskStatus.COMPLETED.value not in col.CARE_TASK_OPEN_STATUSES
    assert TaskStatus.SKIPPED.value not in col.CARE_TASK_OPEN_STATUSES


def test_dedup_expression_selects_the_care_category_and_unsets_otherwise():
    expression = col.CARE_TASK_DEDUP_EXPRESSION
    assert f"'{TaskCategory.CARE_REMINDER.value}'" in expression
    # ``: null`` is the branch that releases the slot; without it the attribute
    # would be written for every task and the sparse index would degenerate.
    assert expression.rstrip().endswith(": null")


def test_computed_value_is_database_maintained_and_unforgeable():
    """The three flags that make the discriminator a *derived* field, not a data field."""
    definition = col.CARE_TASK_DEDUP_COMPUTED_VALUE
    assert definition["name"] == col.CARE_TASK_DEDUP_FIELD
    # Recomputed on every write shape, so no application path can leave it stale.
    assert sorted(definition["computeOn"]) == ["insert", "replace", "update"]
    # A client-supplied value is ignored — the key can never be forged from a body.
    assert definition["overwrite"] is True
    # null result unsets the attribute, which is what a sparse index skips.
    assert definition["keepNull"] is False


def test_name_separator_matches_the_reminder_type_suffix_the_lookup_matches_on():
    """The expression reads the reminder type back out of the task name.

    ``find_open_care_task`` builds its suffix as ``f"— {reminder_type.value}"``;
    the computed value splits on :data:`collections.CARE_TASK_NAME_SEPARATOR` and
    takes the last segment. Same separator or the index groups the wrong things.
    """
    suffix = f"{col.CARE_TASK_NAME_SEPARATOR}{ReminderType.WATERING.value}"
    assert f"Basil {suffix}".split(col.CARE_TASK_NAME_SEPARATOR)[-1] == ReminderType.WATERING.value
    assert suffix == f"— {ReminderType.WATERING.value}"
