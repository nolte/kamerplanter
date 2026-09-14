"""REQ-006 — task photo upload, on the NFR-013 attachment fundament (#1339).

Mounted under ``/api/v1/t/{tenant_slug}/tasks/{key}/photos``, the same shape as
the REQ-034 plant gallery (``/plant-instances/{key}/photos``) so the frontend
consumes both the same way.

**Why this exists.** REQ-006 has required task photos since v1: ``requires_photo``
is on ``TaskTemplate`` and ``TaskItem``, ``photo_refs`` is on ``TaskItem``,
completion enforces the pair (``TaskService.complete_task`` refuses a
``requires_photo`` task with no photo), ``AttachmentCategory.TASK`` is in
NFR-013's category list and ``"task"`` is in the image-only MIME whitelist. Every
part of the capability was built **except the route**: the upload button on the
task-completion form posted to ``POST /tasks/{key}/photos``, which no router had
ever served, so a ``requires_photo`` task could not be completed at all — the
enforcement had no way to be satisfied. #1339 measured the 404; this is the
missing half.

**What it deliberately does not do.** It does not write ``task.photo_refs``. The
completion form stages its photos and submits the list with
``POST /tasks/{key}/complete``, which is what writes them and what the
``requires_photo`` gate reads; appending here as well would have the two writers
disagree the moment the user removes a staged photo before submitting. The
attachment itself is persisted and tenant-owned either way, so an abandoned
upload is a listed, deletable attachment rather than a lost object — though no
UI reaches that list for this category yet, which is #1393.

**What goes into ``photo_refs`` is the bare ``attachment_id``**, never the
``uri`` this response also carries. NFR-013 §2.2 and AC-09 define every
``photo_refs`` list — REQ-006's included — as a list of attachment ids, the
shipped ``migrate_photo_refs`` migration lists ``col.TASKS`` and rewrites exactly
the ``/attachments/{id}`` URI shape *back* to ids, and the diary sibling stores
ids and builds the URI at render. Storing the URI would have been wrong three
ways: a tenant rename re-derives the slug and would break every stored ref
permanently, running the migration would rewrite the refs into ids the client
then fetched verbatim, and the two photo features would disagree about their own
field. ``uri`` and ``thumbnail_uris`` are here for the immediate preview, which
needs no round trip.

Permissions (REQ-024 §1a — the "Attachments" matrix row, as for plant photos):
upload → ``Action.CREATE`` on ``ATTACHMENT``; a viewer is refused. The task is
loaded tenant-scoped *first*, so a foreign task key answers the same 404 as a
key that does not exist.

Responses expose only ``attachment_id`` plus stable tenant-scoped URIs — never
bucket / backend / storage-key details (NFR-013 AC-03/AC-04).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response, UploadFile

from app.api.v1.attachments.permissions import require_attachment_permission
from app.api.v1.attachments.schemas import ThumbnailUris
from app.api.v1.attachments.tenant_router import _parse_content_length, _read_upload_bounded
from app.api.v1.tasks.schemas import TaskPhotoResponse
from app.common.dependencies import get_attachment_service, get_task_service
from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import AttachmentNotFoundError, FileTooLargeError, InvalidFileTypeError
from app.common.openapi_responses import CRUD_RESPONSES
from app.core.permissions import Action
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render
from app.domain.models.attachment import Attachment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.task_service import TaskService

router = APIRouter(prefix="/tasks/{key}/photos", tags=["task-photos"], responses=CRUD_RESPONSES)


def _photo_response(attachment: Attachment, tenant_slug: str) -> TaskPhotoResponse:
    attachment_id = attachment.key or ""
    uri = f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"
    thumbnail_uris: ThumbnailUris | None = None
    if can_render(attachment.mime_type):
        small, medium, large = THUMBNAIL_SIZES
        thumbnail_uris = ThumbnailUris(
            small=f"{uri}/thumbnails/{small}",
            medium=f"{uri}/thumbnails/{medium}",
            large=f"{uri}/thumbnails/{large}",
        )
    return TaskPhotoResponse(
        attachment_id=attachment_id,
        uri=uri,
        thumbnail_uris=thumbnail_uris,
        mime_type=attachment.mime_type,
        byte_size=attachment.byte_size,
        original_filename=attachment.original_filename,
    )


@router.post("", response_model=TaskPhotoResponse, status_code=201)
async def upload_task_photo(
    key: Annotated[str, Path(description="Document key of the task.")],
    request: Request,
    file: UploadFile,
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    task_service: TaskService = Depends(get_task_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> TaskPhotoResponse:
    """Upload a photo for a task and return its stable attachment URI (REQ-006).

    The task is resolved tenant-scoped before a single byte is read, so neither
    an unknown nor a foreign task ever reaches the storage pipeline — and both
    answer the same 404.
    """
    task_service.get_task(key, tenant_key=ctx.tenant_key)

    mime_type = (file.content_type or "").lower().strip()
    if not mime_type:
        raise InvalidFileTypeError("", [])

    # SEC-005 — reject an oversized upload before buffering the body.
    max_bytes = attachment_service.max_upload_bytes()
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise FileTooLargeError(max_bytes)
    data = await _read_upload_bounded(file, max_bytes)

    attachment = await attachment_service.upload(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        data=data,
        mime_type=mime_type,
        original_filename=file.filename or "photo",
        category=AttachmentCategory.TASK,
    )
    return _photo_response(attachment, ctx.tenant_slug)


@router.delete("/{attachment_id}", status_code=204)
async def delete_task_photo(
    key: Annotated[str, Path(description="Document key of the task.")],
    attachment_id: Annotated[str, Path(description="Attachment id of the task photo.")],
    # ``Action.CREATE``, not ``DELETE``, and the split moved into the service.
    #
    # Growers are the role that completes tasks and uploads their photos, and gating
    # the whole route on the lead-only ``ATTACHMENT``/``DELETE`` grant made a grower's
    # remove button a local no-op: the client dropped the reference and issued no
    # request, so the stored object stayed for ever, counted against the tenant quota,
    # with the sweep that would collect it shipped disabled. That is the leak #1393
    # exists to close, still open on its most common path.
    #
    # ``deletable_from_task`` now decides per state: a photo the task references is
    # its completion record and stays lead-only (REQ-024 §1a.1), while a *staged*
    # upload — referenced by nothing, made moments ago — may be withdrawn by whoever
    # made it. Undoing one's own not-yet-submitted CREATE is not the irreversible
    # destruction the boundary reserves to leads.
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    task_service: TaskService = Depends(get_task_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> Response:
    """Delete a task photo, storage object and thumbnails included (#1393).

    **The route the remove button needed.** ``PhotoUpload`` dropped the reference
    from local state and issued no request, because there was nothing to issue it
    to — so a control that looks like a delete left the bytes behind, counting
    against the tenant quota with no surface that reached them.

    The task is resolved tenant-scoped first, exactly as on the upload above, so an
    unknown and a foreign task answer the same 404 and neither reaches storage.
    Deletion itself is idempotent: removing an id that is already gone answers 204
    rather than 404, so a double click, a retry, or a race with the orphan sweep is
    not an error the user has to understand.

    Known gap (#1437): when a lead deletes a photo the task itself references, the
    entry stays in ``task.photo_refs`` and the gallery renders a broken image with
    no surface that repairs it. The orphan sweep is the general reconciliation and
    ships disabled.

    This does **not** rewrite ``task.photo_refs``. The single-writer rule from
    #1388 stands — ``TaskService.complete_task`` owns that list, and the staged
    photos this route deletes are not in it yet. A photo already referenced by a
    completed task is deleted here too, and its id then dangles in ``photo_refs``;
    that is the same state a manual ``DELETE /attachments/{id}`` has always
    produced, and the readers resolve ids against the catalogue rather than trusting
    the list.
    """
    task_service.get_task(key, tenant_key=ctx.tenant_key)

    # Already gone is success, not an error. The docstring promises idempotence and
    # the client relies on it: ``get_attachment`` raises 404 for a missing row, so
    # without this the nightly sweep collecting the photo minutes earlier — or a
    # double click — answered an error toast, and `handleRemove` then skipped its
    # `onChange`, leaving the deleted photo in the list for ever.
    try:
        attachment = attachment_service.get_attachment(attachment_id, ctx.tenant_key)
    except AttachmentNotFoundError:
        return Response(status_code=204)

    # The category is checked, not assumed. Without it this route is a second door
    # onto every attachment of the tenant: a caller could pass a plant-gallery id and
    # destroy it here, bypassing ``PlantPhotoService.delete`` — the path that also
    # prunes ``plant.photo_refs`` and repairs ``cover_photo_ref``, so the gallery
    # would be left with a dangling reference and possibly a cover pointing at
    # nothing. A task-photo route may delete task photos.
    #
    # 404 rather than 403, so a refused id gets the same answer as one that does not
    # exist and the route never confirms that some other attachment is real
    # (REQ-049 §2.4).
    if attachment.category is not AttachmentCategory.TASK:
        raise AttachmentNotFoundError(attachment_id)

    # The task key in the path has to mean something, and "no *task* links it" is
    # not enough to say. sha256 deduplication makes one stored object shared across
    # carriers, so a photo staged here can be the same row a plant gallery links as
    # its cover — destroying it there leaves a dangling reference and possibly a
    # cover pointing at nothing.
    #
    # The question is therefore "does anything **other than this task** reference
    # it", asked through the same repository query the deletion path uses, so the two
    # cannot disagree — and so the answer survives legacy reference spellings, which
    # a tasks-only exact match did not.
    #
    # An unreferenced photo is the normal case: a staged upload is in no
    # ``photo_refs`` until completion writes it (#1388) — which is why ``actor_key``
    # goes in as well. For such a photo the task key in the path constrains nothing
    # (it is in no task's list, so "no *other* task references it" holds for every
    # task of the tenant), and the predicate falls back to the uploader instead.
    if not attachment_service.deletable_from_task(
        attachment_id,
        key,
        ctx.tenant_key,
        actor_key=ctx.user_key,
        is_lead=ctx.role is TenantRole.LEAD,
    ):
        raise AttachmentNotFoundError(attachment_id)

    await attachment_service.delete(attachment_id, ctx.tenant_key)
    return Response(status_code=204)
