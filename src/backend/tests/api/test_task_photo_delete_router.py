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
from unittest.mock import AsyncMock, MagicMock, create_autospec

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
from app.domain.services.attachment_service import AttachmentService

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
    # ``create_autospec``, not a bare ``MagicMock``: this file's whole job is to pin
    # what the handler asks the service, and a bare mock accepts a call the real
    # service would reject — a renamed parameter, a dropped argument, an argument
    # added to the service and not to the handler. Every assertion below would stay
    # green while the route raised ``TypeError`` in production. The autospec binds
    # each method's real signature, so the drift fails here instead.
    attachment_service = create_autospec(AttachmentService, instance=True)
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


class TestWhichRoleReachesWhichHalf:
    """The route admits a grower; the *state* of the photo decides what happens.

    This class used to be ``TestAGrowerIsRefused`` and asserted a 403, because the
    route was gated on ``ATTACHMENT``/``DELETE`` — lead-only per REQ-024 §1a.1. Its
    own docstring then explained the UI consequence: "a grower de-stages, and the
    nightly orphan sweep collects what they left behind."

    That backstop stopped existing when the sweep shipped disabled. What was left was
    a remove button that growers see, that drops the photo from their form, and that
    leaves the stored object in place for ever — the leak #1393 exists to close, on
    the path most travelled, since growers are the role that completes tasks and
    uploads the photos in the first place.

    So the boundary moved from the route to the state. A photo the task references is
    its completion record and is still lead-only. A *staged* upload — referenced by
    nothing, made moments ago by this caller — may be withdrawn by whoever made it,
    which is the undo of the ``CREATE`` they were already granted.
    """

    def _client(self, services, role: TenantRole) -> TestClient:
        task_service, attachment_service = services
        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(photo_router, prefix="/api/v1/t/{tenant_slug}")
        app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
        app.dependency_overrides[get_task_service] = lambda: task_service
        app.dependency_overrides[get_attachment_service] = lambda: attachment_service
        return TestClient(app, raise_server_exceptions=False)

    def test_a_grower_now_reaches_the_route(self, services):
        """No 403 before the predicate runs — otherwise the state can never decide."""
        _task_service, attachment_service = services
        response = self._client(services, TenantRole.GROWER).delete(_url(OWN_TASK))

        assert response.status_code == 204
        attachment_service.delete.assert_awaited_once()

    def test_a_viewer_is_still_refused(self, services):
        """The control. ``CREATE`` is lead-and-grower, so a viewer must still bounce.

        Without this, relaxing the dependency could have opened the route to every
        member and the two cases above would not have noticed.
        """
        _task_service, attachment_service = services
        response = self._client(services, TenantRole.VIEWER).delete(_url(OWN_TASK))

        assert response.status_code == 403
        attachment_service.delete.assert_not_awaited()

    @pytest.mark.parametrize(
        ("role", "expected"),
        [(TenantRole.LEAD, True), (TenantRole.GROWER, False)],
        ids=["lead", "grower"],
    )
    def test_the_role_is_handed_to_the_predicate(self, services, role: TenantRole, expected: bool):
        """``is_lead`` must reflect the caller, or the state split decides nothing.

        Asserted on the argument rather than on the outcome: the service is doubled
        here, so an outcome assertion would only be checking the double's stub. What
        this route owes the service is the caller's role, and that is what is pinned.
        """
        _task_service, attachment_service = services
        self._client(services, role).delete(_url(OWN_TASK))

        assert attachment_service.deletable_from_task.call_args.kwargs["is_lead"] is expected


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


class TestTheTwoNotFoundCasesAreDistinguishable:
    """#1437 — the route answers 404 for two different things, and the client must tell them apart.

    ``task_service.get_task`` raises ``NotFoundError("Task", …)`` and every
    attachment branch raises ``AttachmentNotFoundError``, which *inherits* from it.
    Both therefore carry ``error_code="ENTITY_NOT_FOUND"`` and the same HTTP status,
    and differ only in the human-readable ``message`` — which is English prose a
    client may not parse (NFR-003 keeps API messages English while the UI renders
    German).

    The consequence was in ``PhotoUpload.handleRemove``: it de-staged on *every*
    404. When the **task** was the thing that had vanished, nothing had been
    deleted, the entry left the list anyway, and the attachment orphaned — with the
    orphan sweep shipping disabled, for ever.

    So the signal is additive (operator decision 1): ``error_code`` stays
    ``ENTITY_NOT_FOUND`` so nothing matching on it breaks, and ``details[0].entity``
    carries the entity name machine-readably. Asserted on the wire, through the real
    error handler, because that is what the client reads.
    """

    def test_a_missing_task_names_the_task(self, client):
        body = client.delete(_url(FOREIGN_TASK)).json()

        assert body["details"][0]["entity"] == "task"

    def test_a_refused_attachment_names_the_attachment(self, client, services):
        _task_service, attachment_service = services
        attachment_service.deletable_from_task.return_value = False

        body = client.delete(_url(OWN_TASK)).json()

        assert body["details"][0]["entity"] == "attachment"

    def test_the_two_cases_are_not_the_same_answer(self, client, services):
        """The point of the change, stated as one assertion.

        Both above could pass against a constant, and both did pass against
        ``error_code`` before the change — because both cases carry the *same* one.
        """
        _task_service, attachment_service = services
        task_gone = client.delete(_url(FOREIGN_TASK)).json()
        attachment_service.deletable_from_task.return_value = False
        attachment_gone = client.delete(_url(OWN_TASK)).json()

        assert task_gone["error_code"] == attachment_gone["error_code"] == "ENTITY_NOT_FOUND"
        assert task_gone["details"][0]["entity"] != attachment_gone["details"][0]["entity"]

    def test_the_entity_name_does_not_depend_on_how_the_raiser_spelled_it(self):
        """``NotFoundError("Task", …)`` and ``NotFoundError("task", …)`` both occur.

        The call sites spell entities every which way — ``"PlantInstance"``,
        ``"attachment"``, ``"memberships"``, ``"nutrient plan phase entry"`` — so a
        verbatim echo would hand the client a value that changes when someone
        re-words a raiser. Normalised in the constructor, once, rather than at each
        of the ~150 call sites.
        """
        assert NotFoundError("Task", "k").details[0]["entity"] == "task"
        assert NotFoundError("task", "k").details[0]["entity"] == "task"
        assert NotFoundError("PlantInstance", "k").details[0]["entity"] == "plant_instance"
        assert NotFoundError("nutrient plan phase entry", "k").details[0]["entity"] == "nutrient_plan_phase_entry"

    def test_normalisation_is_idempotent(self):
        """An already-normalised name survives unchanged, or the contract drifts.

        ``entity`` is what a client branches on; if feeding a normalised name back
        through produced a *different* one, the value would depend on how many
        layers had touched it.
        """
        once = NotFoundError("PlantDiaryEntry", "k").details[0]["entity"]

        assert NotFoundError(once, "k").details[0]["entity"] == once

    def test_the_prose_reason_is_untouched(self, client):
        """Additive means additive: ``field``, ``reason`` and ``code`` keep their values."""
        detail = client.delete(_url(FOREIGN_TASK)).json()["details"][0]

        assert detail["field"] == "key"
        assert detail["code"] == "ENTITY_NOT_FOUND"
        assert FOREIGN_TASK in detail["reason"]
