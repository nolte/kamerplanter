"""The manual care-reminder trigger threads its tenant into the work it starts.

``POST /t/{slug}/tasks/generate-care-reminders`` is addressed per tenant and
permission-gated per tenant. Until #1204 it was not *bounded* per tenant: ``ctx``
was resolved, checked against ``TASK/CREATE`` — and then never used. The Celery
task it started iterated every care profile in the installation, so a grower
exercising a permission granted in tenant A wrote task rows in B, C and D, and
the returned counts described the whole installation's volume.

The shape is what makes it worth pinning at the router: a route whose ``ctx``
is resolved and checked and then dropped reads as correctly scoped at every
call site. Only the wiring shows otherwise. The scoping *behaviour* behind this
call is covered in ``tests/unit/tasks/test_care_tasks.py::TestTenantScope``;
this file asserts only that the router reaches it.
"""

from __future__ import annotations

import pytest

from app.api.v1.tasks.tenant_router import generate_care_reminders_now
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext

TENANT = "tenant-A"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT,
        tenant_slug="mein-garten",
        user_key="user-a",
        role=TenantRole.GROWER,
    )


class _EagerResult:
    def __init__(self, result):
        self.result = result


class _TaskSpy:
    """Stands in for the Celery task; records how the route invoked it."""

    def __init__(self):
        self.calls: list[dict] = []

    def apply(self, args=None, kwargs=None):
        self.calls.append(dict(kwargs or {}))
        return _EagerResult({"created": 0, "skipped": 0})


@pytest.fixture
def task_spy(monkeypatch):
    spy = _TaskSpy()
    # The route imports the task inside the function body, so patching the
    # module attribute is what the call actually resolves.
    monkeypatch.setattr("app.tasks.care_tasks.generate_due_care_reminders", spy)
    return spy


def test_the_route_passes_its_own_tenant_into_the_task(task_spy):
    generate_care_reminders_now(ctx=_ctx())

    assert task_spy.calls == [{"tenant_key": TENANT}]


def test_the_route_does_not_start_an_installation_wide_sweep(task_spy):
    """The regression itself: an argument-free ``apply()`` is the defect.

    Asserted separately from the positive case because the two fail for
    different reasons — this one stays red if a later change reintroduces the
    unscoped call while still passing something else along.
    """
    generate_care_reminders_now(ctx=_ctx())

    (call,) = task_spy.calls
    assert call.get("tenant_key") is not None, "the sweep must not be startable from a tenant route"


def test_the_result_is_returned_unchanged(task_spy):
    assert generate_care_reminders_now(ctx=_ctx()) == {"created": 0, "skipped": 0}
