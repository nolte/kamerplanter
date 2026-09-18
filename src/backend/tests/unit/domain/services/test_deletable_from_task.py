"""#1393 — what the task key in ``DELETE /tasks/{key}/photos/{id}`` actually scopes.

The route reads as "delete this photo from this task", and for a photo the task
references that is what it does. For a **staged** photo it did not, and the gap was
in the predicate rather than in the route.

A staged upload is in no ``photo_refs`` anywhere until the completion request writes
it (#1388). ``deletable_from_task`` asked one question — "does anything other than
the named task reference it" — and for such a photo that is vacuously true through
**any** task key of the tenant: a task the caller has nothing to do with, a task
another member is filling in right now. The path segment looked like a scope and
constrained nothing.

So the predicate now asks a second question when the first one finds no reference at
all: a photo nothing links belongs to whoever uploaded it, and only they may destroy
it through this route. That is the same person the control is rendered for —
``PhotoUpload`` shows the remove button only for ids staged in the current session.

Tested at the service, not through the route: the route's own tests double this
service, so a rule asserted only there would be asserting the double.
"""

from __future__ import annotations

import pytest

from app.domain.services.attachment_service import AttachmentService

TENANT = "tenant-a"
PHOTO = "att-1"
OWN_TASK = "task-own"
OTHER_TASK = "task-other"
UPLOADER = "user-uploader"
SOMEONE_ELSE = "user-other"


class _Repo:
    """A repository whose reference answers come from an explicit reference map.

    ``references`` maps a task key to the photos it links, and the state is *derived*
    from it rather than stubbed per case — stubbing the branches apart is how a double
    ends up describing a state the database cannot be in (a photo simultaneously
    referenced by nothing and by the named task), and such a state makes a branch pass
    for the wrong reason.

    The real query is exercised against ArangoDB in
    ``tests/integration/test_task_photo_delete_state.py``; this file pins what the
    *service* does with each answer.
    """

    def __init__(self, references: dict[str, list[str]], created_by: str = UPLOADER):
        self.references = references
        self.created_by = created_by

    def task_photo_delete_state(self, attachment_id, tenant_key, *, task_key):
        assert tenant_key == TENANT
        if attachment_id != PHOTO:
            return "missing", None
        elsewhere = {photo for task, photos in self.references.items() if task != task_key for photo in photos}
        if attachment_id in elsewhere:
            return "shared", self.created_by
        own = set(self.references.get(task_key, ()))
        if attachment_id in own:
            return "task", self.created_by
        return "staged", self.created_by


def _service(repo) -> AttachmentService:
    service = AttachmentService.__new__(AttachmentService)
    service._repo = repo
    return service


def test_the_uploader_may_delete_their_own_staged_photo():
    """The normal case the route exists for, asserted positively.

    Without this, every rule below could be satisfied by a predicate that refuses
    everything — and the remove button would be permanently broken while the lane
    stayed green.
    """
    service = _service(_Repo(references={}))
    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=True) is True


def test_another_member_may_not_delete_a_staged_photo_through_an_unrelated_task():
    """The finding. Nothing references the photo, so the old question said yes.

    The task key names a task that links nothing of this caller's; before the
    uploader check it constrained nothing at all, and any task key of the tenant
    admitted the deletion of a photo another member had just staged.
    """
    service = _service(_Repo(references={}))
    assert service.deletable_from_task(PHOTO, OTHER_TASK, TENANT, actor_key=SOMEONE_ELSE, is_lead=True) is False


def test_a_photo_the_named_task_references_is_deletable_by_a_non_uploader():
    """The uploader rule must not leak into task documentation.

    A completed task's photo is the task's, not the uploader's; whoever may delete
    the tenant's attachments may delete it. Asserting only the refusal above would
    leave a predicate that demands uploadership everywhere looking correct.
    """
    service = _service(_Repo(references={OWN_TASK: [PHOTO]}))
    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=SOMEONE_ELSE, is_lead=True) is True


@pytest.mark.parametrize("actor", [UPLOADER, SOMEONE_ELSE])
def test_a_photo_another_carrier_references_is_never_deletable(actor: str):
    """The pre-existing rule, re-asserted against both actors.

    sha256 deduplication gives one stored object to several carriers, so the
    uploader of a photo a plant gallery now uses as its cover still may not destroy
    it here. The uploader check is an *additional* condition, not an override.
    """
    service = _service(_Repo(references={OTHER_TASK: [PHOTO]}))
    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=actor, is_lead=True) is False


def test_a_photo_that_resolves_to_nothing_is_refused():
    """An id in no collection at all cannot be attributed to an uploader.

    ``by_keys`` skips what does not exist, so this is the empty-list branch. Refusing
    is right and also harmless: the route already answers 204 for a missing row
    before the predicate runs, so this only covers a row the catalogue lost between
    the two reads.
    """
    service = _service(_Repo(references={}))
    assert service.deletable_from_task("att-unknown", OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=True) is False


@pytest.mark.parametrize("is_lead", [True, False])
def test_the_uploader_may_withdraw_their_staged_photo_whatever_their_role(is_lead: bool):
    """Finding 4. Growers upload the photos, so they must be able to take one back.

    Gating the whole route on the lead-only DELETE grant made a grower's remove
    button a local no-op: the reference vanished from the form and the stored object
    stayed, counted against the tenant quota, with the sweep that would collect it
    shipped disabled.
    """
    service = _service(_Repo(references={}))
    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=is_lead) is True


def test_a_grower_may_not_destroy_the_tasks_completion_record():
    """The half REQ-024 §1a.1 reserves to leads, and the reason the split exists.

    A photo the task references is its documentation. Losing the staged/record
    distinction in either direction is a defect: admitting growers here would make
    the deletion of a completion record a grower operation, and refusing them above
    would leave the leak open.
    """
    service = _service(_Repo(references={OWN_TASK: [PHOTO]}))

    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=False) is False
    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=True) is True


def test_no_role_may_destroy_a_photo_another_carrier_holds():
    """`shared` is not a permission question. Lead included.

    sha256 deduplication gives one stored object to several carriers, so destroying
    it strands a reference no matter who asked.
    """
    service = _service(_Repo(references={OTHER_TASK: [PHOTO]}))

    assert service.deletable_from_task(PHOTO, OWN_TASK, TENANT, actor_key=UPLOADER, is_lead=True) is False
