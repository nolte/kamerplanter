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
from app.common.enums import AttachmentCategory, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import AttachmentNotFoundError, KamerplanterError, NotFoundError
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
    # Nothing but this task references the photo: the normal case, because a staged
    # upload is in no `photo_refs` at all until the completion request writes it
    # (#1388). Asked through the attachment service, which consults every carrier —
    # a tasks-only question missed a plant gallery holding the same deduplicated row.
    attachment_service.deletable_from_task.return_value = True
    attachment_service.get_attachment.return_value = SimpleNamespace(
        key=ATTACHMENT, tenant_key=TENANT, category=AttachmentCategory.TASK
    )
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
    """Idempotent by contract, driven through the path production takes.

    The first version of this test flipped only ``delete`` to return ``False`` and
    left ``get_attachment`` returning a live attachment — so it never reached the
    production path, where ``get_attachment`` raises ``AttachmentNotFoundError``
    **first** and the route answered 404. It certified idempotence the route did not
    have, while the docstring and the client both promised it.

    It matters in practice: the nightly sweep may collect the row minutes before the
    user clicks remove, and `PhotoUpload.handleRemove` skips its `onChange` on
    error — so a 404 left the already-deleted photo in the list for ever.
    """

    def test_an_attachment_that_no_longer_exists_answers_204(self, client, services):
        _task_service, attachment_service = services
        attachment_service.get_attachment.side_effect = AttachmentNotFoundError(ATTACHMENT)

        assert client.delete(_url(OWN_TASK)).status_code == 204

    def test_it_does_not_try_to_delete_what_is_gone(self, client, services):
        _task_service, attachment_service = services
        attachment_service.get_attachment.side_effect = AttachmentNotFoundError(ATTACHMENT)

        client.delete(_url(OWN_TASK))

        attachment_service.delete.assert_not_awaited()

    def test_a_delete_that_reports_nothing_removed_is_still_204(self, client, services):
        """The other race: the row vanished between the read and the delete."""
        _task_service, attachment_service = services
        attachment_service.delete = AsyncMock(return_value=False)

        assert client.delete(_url(OWN_TASK)).status_code == 204


class TestAPhotoAnotherCarrierReferences:
    """The task key in the path has to mean something (#1424 findings 6 and, later, 2).

    On its own it proves only that the caller owns *some* task. A lead could pass any
    pending task of theirs plus a **completed** task's photo id and destroy
    documentation — undoing the invariant ``delete_task``'s status gate exists to
    protect.

    The first version asked a tasks-only, exact-match question, which review found
    wrong twice over: sha256 deduplication makes one stored object shared with a
    *plant gallery* too, and a legacy reference spelling matched nothing. It now asks
    the attachment service, which consults every carrier through the same query the
    deletion path uses.

    An unreferenced photo stays deletable: that is the staged upload this route
    normally serves.
    """

    def test_a_photo_another_carrier_references_is_refused(self, client, services):
        _task_service, attachment_service = services
        attachment_service.deletable_from_task.return_value = False

        response = client.delete(_url(OWN_TASK))

        assert response.status_code == 404
        attachment_service.delete.assert_not_awaited()

    def test_a_photo_only_this_task_references_is_deletable(self, client, services):
        _task_service, attachment_service = services
        attachment_service.deletable_from_task.return_value = True

        assert client.delete(_url(OWN_TASK)).status_code == 204
        attachment_service.delete.assert_awaited_once()


class TestAGrowerIsRefused:
    """The boundary, asserted rather than discovered.

    ``DELETE`` on ``ATTACHMENT`` is lead-only (REQ-024 §1a.1); ``CREATE`` is
    lead-and-grower. So a grower can upload a task photo and cannot remove it, which
    is a deliberate spec decision and not an oversight of this route.

    Its UI consequence changed in review round 1: hiding the button from growers
    took away their only way to de-stage a wrong photo, so it got submitted
    instead. `PhotoUpload` now shows the control to everyone and only *destroys*
    for a caller who may — a grower de-stages, and the nightly orphan sweep
    collects what they left behind.
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


class TestAnAttachmentOfAnotherCategory:
    """A task-photo route may delete task photos, and nothing else.

    Without the category check this is a second door onto every attachment of the
    tenant: passing a plant-gallery id here destroys it while bypassing
    `PlantPhotoService.delete`, the path that also prunes ``plant.photo_refs`` and
    repairs ``cover_photo_ref``. The gallery would be left with a dangling reference
    and possibly a cover pointing at nothing.

    Answered 404, not 403: a wrong-category id gets the same answer as one that does
    not exist, so the route never confirms that some other attachment is real
    (REQ-049 §2.4).
    """

    def test_a_plant_photo_is_not_deletable_through_the_task_route(self, client, services):
        _task_service, attachment_service = services
        attachment_service.get_attachment.return_value = SimpleNamespace(
            key=ATTACHMENT, tenant_key=TENANT, category=AttachmentCategory.PLANT
        )

        response = client.delete(_url(OWN_TASK))

        assert response.status_code == 404
        attachment_service.delete.assert_not_awaited()
