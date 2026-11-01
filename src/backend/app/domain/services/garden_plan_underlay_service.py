"""The background picture of a garden plan (REQ-053 GP-FR-033, WP 7.14): set, replace, remove, read for print.

**One underlay per site**, stored on the site's plan (``SitePlan.underlay``) so every member sees the same
calibrated picture; whether it is *shown* is each user's choice and lives in the browser. The picture is an
attachment of category ``garden_plan_underlay`` (NFR-013: size limit, magic bytes, EXIF/GPS strip, quota). It is
presentation only: never part of the JSON export (GP-FR-140, ``ExportPlanSettings`` has no field for it) and in
the PDF only when the caller asks for it.

Every public method resolves the site **inside the method** through the tenant anchor
(``location_ownership.require_owned_site``) and takes ``*, tenant_key: str`` without a default. The attachment is
read with the same tenant (``IAttachmentRepository.get`` is tenant-scoped); a key that is absent, another
tenant's, of another category or outside its tenant's storage namespace answers one 422 ``reference.not_found``
(GP-NFR-058), so the response is no oracle for another tenant's attachments. Replacing or removing the picture
deletes the superseded attachment through :meth:`AttachmentService.delete_if_unreferenced` (no other site or carrier
names it) and then the delete that asks whether another record holds the stored object (#1770).
"""

from __future__ import annotations

import structlog

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import ForbiddenError, PlanError, PlanValidationError
from app.common.types import SiteKey
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.attachment import Attachment
from app.domain.models.site import Site, SiteUnderlay
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.location_ownership import require_owned_site

logger = structlog.get_logger(__name__)

ERROR_REFERENCE_NOT_FOUND = "reference.not_found"
ERROR_PLAN_REQUIRED = "plan.required"


class GardenPlanUnderlayService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        attachment_repo: IAttachmentRepository,
        attachment_service: AttachmentService,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._attachment_repo = attachment_repo
        self._attachments = attachment_service

    def _owned_site(self, site_key: SiteKey, *, tenant_key: str) -> Site:
        return require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    def _underlay_attachment(self, attachment_key: str, *, tenant_key: str) -> Attachment:
        """The tenant's own ``garden_plan_underlay`` attachment, else 422 ``reference.not_found``."""
        attachment = self._attachment_repo.get(attachment_key, tenant_key)
        if (
            attachment is None
            or attachment.category != AttachmentCategory.GARDEN_PLAN_UNDERLAY
            or not AttachmentService.in_own_namespace(attachment)
        ):
            raise PlanValidationError([(None, "attachment_key", ERROR_REFERENCE_NOT_FOUND, {})])
        return attachment

    def get_underlay(self, site_key: SiteKey, *, tenant_key: str) -> SiteUnderlay | None:
        site = self._owned_site(site_key, tenant_key=tenant_key)
        return site.plan.underlay if site.plan is not None else None

    async def set_underlay(
        self, site_key: SiteKey, *, tenant_key: str, role: TenantRole, underlay: SiteUnderlay
    ) -> SiteUnderlay:
        """Set or replace the site's underlay; the picture it replaces is deleted when nothing else holds it.

        422 ``plan.required`` when the site has no plan yet (the picture is traced over a plan, it does not
        create one); 422 ``reference.not_found`` for an attachment that is not the caller's own underlay.
        """
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        if site.plan is None:
            raise PlanError(ERROR_PLAN_REQUIRED, "The site has no garden plan yet.", status_code=422, field="plan")
        self._underlay_attachment(underlay.attachment_key, tenant_key=tenant_key)
        written, previous = self._plan.set_site_underlay(site_key, tenant_key=tenant_key, underlay=underlay)
        if not written:
            raise PlanError(ERROR_PLAN_REQUIRED, "The site has no garden plan yet.", status_code=422, field="plan")
        await self.discard(previous, keep=underlay.attachment_key, tenant_key=tenant_key)
        return underlay

    async def remove_underlay(self, site_key: SiteKey, *, tenant_key: str, role: TenantRole) -> bool:
        """Remove the site's underlay and its attachment (unless another record holds the object). Idempotent."""
        site = self._owned_site(site_key, tenant_key=tenant_key)
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        if site.plan is None or site.plan.underlay is None:
            return False
        written, previous = self._plan.set_site_underlay(site_key, tenant_key=tenant_key, underlay=None)
        if written:
            await self.discard(previous, keep=None, tenant_key=tenant_key)
        return written

    async def discard(self, attachment_key: str | None, *, keep: str | None, tenant_key: str) -> None:
        """Delete a superseded picture unless something else still names it.

        The upload dedupes per sha256, so two sites of one tenant can hold the same attachment: the picture goes
        only when no carrier references it any more (another site's underlay, a gallery, a task - the reference
        scan of :meth:`AttachmentService.delete_if_unreferenced`, which runs after this site's own reference is
        gone, in the transaction of the record's removal) and then through the delete that asks the other record
        holders first. Also the site delete's step for the picture of the deleted plan (``SiteService``, #2545).
        """
        if attachment_key is None or attachment_key == keep:
            return
        attachment = self._attachment_repo.get(attachment_key, tenant_key)
        if attachment is None or attachment.category != AttachmentCategory.GARDEN_PLAN_UNDERLAY:
            return
        if await self._attachments.delete_if_unreferenced(attachment_key, tenant_key):
            logger.info("garden_plan.underlay_discarded", attachment_id=attachment_key)


__all__ = ["ERROR_PLAN_REQUIRED", "ERROR_REFERENCE_NOT_FOUND", "GardenPlanUnderlayService"]
