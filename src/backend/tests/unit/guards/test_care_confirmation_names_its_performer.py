"""#2517 (REQ-053 §32.8 Pkt. 2) — every care-reminder confirmation stores its caller as performer.

A confirmation logs a care event whose ``performed_by_user_key`` is the person (or service account) that confirmed.
Until #2517 the REST route and the notification action passed the caller, while the task-queue bridge and the MCP
tool stored ``null``: ``user_key: str = ""`` was an opt-in, and two of four entry paths did not opt in.

**The rule, by construction.** The service methods a confirmation passes through take ``user_key`` keyword-only and
**without** a default, so leaving it out is a ``TypeError`` rather than a silent ``null``. Pinned twice:

* the signatures themselves (a default re-appearing fails here), and
* every call of those methods under ``app/`` names ``user_key`` - a static check, so a caller on a path no test
  exercises is caught too. A call that forwards ``**kwargs`` cannot be read statically and is refused.

The behaviour per entry path is measured beside the paths: REST in
``tests/unit/domain/services/test_care_confirmation_bed_event.py``, the task queue there and in
``tests/unit/api/test_tasks_care_bridge_routing.py``, MCP in ``tests/unit/mcp_server/test_tools.py``.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.domain.services.care_reminder_service import CareReminderService
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: The confirmation paths of ``CareReminderService`` that end in a care event with a performer.
_PERFORMER_METHODS = ("confirm_reminder", "record_care_task_completion", "_bed_event_for")


@pytest.mark.parametrize("method", _PERFORMER_METHODS)
def test_the_performer_is_a_required_keyword(method: str) -> None:
    parameter = inspect.signature(getattr(CareReminderService, method)).parameters.get("user_key")

    assert parameter is not None, f"CareReminderService.{method} lost its user_key parameter"
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, f"{method}: user_key must be keyword-only"
    assert parameter.default is inspect.Parameter.empty, (
        f"{method}: user_key has a default again - an entry path that forgets it would store no performer (#2517)"
    )


def _calls_without_performer() -> tuple[list[str], int]:
    missing: list[str] = []
    seen = 0
    for path in sorted(_APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in _PERFORMER_METHODS:
                continue
            seen += 1
            names = {keyword.arg for keyword in node.keywords}
            if "user_key" not in names or None in names:
                missing.append(f"{path.relative_to(_APP.parent)}:{node.lineno} {node.func.attr}")
    return missing, seen


def test_every_confirmation_call_names_its_performer() -> None:
    missing, seen = _calls_without_performer()

    # REST, notification action, task queue, MCP, plus the two internal _bed_event_for calls. A drop below means the
    # scan no longer finds the paths it claims to check.
    assert seen >= 6, f"the scan found only {seen} confirmation calls - it no longer sees the entry paths"
    assert missing == [], "a confirmation path stores no performer:\n" + "\n".join(missing)
