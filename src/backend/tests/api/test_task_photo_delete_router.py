"""#1393 decision 3 — ``DELETE /tasks/{key}/photos/{attachment_id}``, the route the button needed.

`PhotoUpload.handleRemove` filtered the reference out of local state and issued no
request, because there was no route to issue one to. The stored object stayed,
counting against ``STORAGE_TENANT_QUOTA_MB``, and no surface in the product reached
it for the ``task`` category: a control that looked like a delete and was not.

What is asserted here is the route's *contract*, not the storage mechanics —
`AttachmentService.delete` has its own tests:

* the task is resolved tenant-scoped **first**, so a foreign task never reaches the
  attachment layer and answers the same 404 as an unknown one (no ownership
  oracle, REQ-049 §2.4);
* the gate is ``Action.DELETE`` on ``ATTACHMENT``, so a viewer is refused;
* deleting an id that is already gone answers 204, so a double click, a retry, or
  a race with the nightly orphan sweep is not an error the user has to understand.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tasks.photo_router import router as photo_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_attachment_service, get_task_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.tenant_context import TenantContext

OWN_TASK = "task-own"
FOREIGN_TASK = "task-foreign"
ATTACHMENT = "att-1"
TENANT = "tenant-a"
SLUG = "my-garden"


# LEAD, not GROWER: ``DELETE`` on ``ATTACHMENT`` is the REQ-024 §1a.1
# irreversibility boundary and is granted to lead alone. A grower may upload and
# may not delete — see `TestAGrowerIsRefused` below, which pins that rather than
# leaving it as a surprise.
def _ctx(role: TenantRole = TenantRole.LEAD) -> TenantContext:
    return TenantContext(tenant_key=TENANT, tenant_slug=SLUG, user_key="user-1", role=role)


@pytest.fixture
def services():
    task_service = MagicMock()

    def _get_task(key: str, *, tenant_key: str):
        if key != OWN_TASK:
            raise NotFoundError("Task", key)
        return SimpleNamespace(key=key, tenant_key=tenant_key, photo_refs=[ATTACHMENT])

    task_service.get_task.side_effect = _get_task

    attachment_service = MagicMock()
    attachment_service.delete = AsyncMock(return_value=True)
    return task_service, attachment_service


@pytest.fixture
def client(services):
    task_service, attachment_service = services
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(photo_router, prefix="/api/v1/t/{tenant_slug}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service
    return TestClient(app, raise_server_exceptions=False)


def _url(task: str, attachment: str = ATTACHMENT) -> str:
    return f"/api/v1/t/{SLUG}/tasks/{task}/photos/{attachment}"


class TestTheCallerOwnPhotoIsDeleted:
    def test_it_answers_204(self, client):
        assert client.delete(_url(OWN_TASK)).status_code == 204

    def test_it_reaches_the_attachment_service_with_the_caller_tenant(self, client, services):
        _task_service, attachment_service = services

        client.delete(_url(OWN_TASK))

        attachment_service.delete.assert_awaited_once_with(ATTACHMENT, TENANT)


class TestAForeignTaskNeverReachesStorage:
    def test_it_answers_404(self, client):
        assert client.delete(_url(FOREIGN_TASK)).status_code == 404

    def test_the_attachment_layer_is_not_touched(self, client, services):
        """The order matters, not just the status.

        A 404 returned *after* the delete would satisfy the assertion above and
        still have destroyed another tenant's photo.
        """
        _task_service, attachment_service = services

        client.delete(_url(FOREIGN_TASK))

        attachment_service.delete.assert_not_awaited()


class TestDeletingWhatIsAlreadyGone:
    def test_it_still_answers_204(self, client, services):
        """Idempotent by contract.

        The nightly orphan sweep may have collected the same row minutes earlier,
        and a user who clicks twice should not see an error either. The service
        returns ``False`` for an unknown id rather than raising, and the route does
        not turn that into a 404 — the caller asked for the photo to be gone, and it
        is gone.
        """
        _task_service, attachment_service = services
        attachment_service.delete = AsyncMock(return_value=False)

        assert client.delete(_url(OWN_TASK)).status_code == 204


class TestAGrowerIsRefused:
    """The boundary, asserted rather than discovered.

    ``DELETE`` on ``ATTACHMENT`` is lead-only (REQ-024 §1a.1); ``CREATE`` is
    lead-and-grower. So a grower can upload a task photo and cannot remove it, which
    is a deliberate spec decision and not an oversight of this route.

    It has a UI consequence: the remove button must be hidden for a grower, or it is
    a control that answers a refusal (#1261). `PhotoUpload` gates it on `canDelete`
    for exactly this reason, and an abandoned upload is what the nightly orphan
    sweep exists to collect.
    """

    def test_the_route_refuses_a_grower(self, services):
        task_service, attachment_service = services
        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(photo_router, prefix="/api/v1/t/{tenant_slug}")
        app.dependency_overrides[get_current_tenant] = lambda: _ctx(TenantRole.GROWER)
        app.dependency_overrides[get_task_service] = lambda: task_service
        app.dependency_overrides[get_attachment_service] = lambda: attachment_service
        grower_client = TestClient(app, raise_server_exceptions=False)

        response = grower_client.delete(_url(OWN_TASK))

        assert response.status_code == 403
        attachment_service.delete.assert_not_awaited()
