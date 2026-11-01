"""Bed templates: the catalogue and its writes (REQ-053 §20.12, §21.7, §21.8 "Beetvorlage"; WP 7.8, #2474).

**Order of the checks (SR-013).** Tenant anchor (a foreign template is a 404, exactly like an absent one) -> role
(403) -> the owner of the row (a system template is a platform admin's, 403 for everybody else) -> references of
the body (422 ``reference.not_found``) -> the write.

**Ownership is resolved here, never in the router** (T-01..T-03, #2107). Every public method that writes takes
``*, tenant_key: str`` without a default. A template is loaded through ``get_visible_by_key`` - the system templates and
the tenant's own, nothing else - and written through ``update_template`` / ``delete_template`` **naming its
owner**, so the write itself matches on the owner and cannot reach the other kind of row.

**Roles (§21.8 "Beetvorlage").** Reading: every member (and every system template, always); creating and changing
a tenant template: from grower; deleting it: lead only; changing or deleting a *system* template: platform admin
only. The router gate says the same for the rank; the service repeats it so a second caller (an MCP tool, a task)
cannot skip it.

**Logs carry no user text** (GP-NFR-060): keys, counts and codes - never a template name.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.common.types import BedTemplateKey
from app.domain.engines.garden_plan_engine import ERROR_REFERENCE_NOT_FOUND
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.bed_template_repository import IBedTemplateRepository
from app.domain.models.bed_template import (
    ERROR_NOT_A_BED_TYPE,
    MAX_TEMPLATES_PER_TENANT,
    BedTemplate,
    BedTemplateInput,
    BedTemplatePatch,
)
from app.domain.services.catalogue_authorization import require_platform_admin_for_global_catalogue

logger = structlog.get_logger()

#: 422 when a tenant already owns the most templates it may.
ERROR_QUOTA = "bed_template.quota_exceeded"

#: The fields a PATCH writes on the document.
_PATCH_COLUMNS: tuple[str, ...] = (
    "name",
    "location_type_key",
    "default_geometry",
    "height_m",
    "default_layout",
    "soil_profile_defaults",
    "recurring_task_templates",
)


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def _not_found(field: str, index: int | None = None) -> PlanValidationError:
    """422 ``reference.not_found`` - one text for a missing and for another tenant's key (GP-NFR-058)."""
    path = field if index is None else f"{field}[{index}]"
    return PlanValidationError([(None, path, ERROR_REFERENCE_NOT_FOUND, {})])


def _quota_exceeded(current: int) -> PlanError:
    """422 ``bed_template.quota_exceeded`` (GP-NFR-017, GP-API-061)."""
    return PlanError(
        ERROR_QUOTA,
        f"A tenant owns at most {MAX_TEMPLATES_PER_TENANT} bed templates.",
        status_code=422,
        limit=MAX_TEMPLATES_PER_TENANT,
        current=current,
    )


class BedTemplateService:
    def __init__(self, repo: IBedTemplateRepository) -> None:
        self._templates = repo

    # ── Roles ─────────────────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_lead(role: TenantRole) -> None:
        if not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Requires lead role.")

    # ── Reads (GET /bed-templates) ────────────────────────────────────────

    def list_templates(self, *, tenant_key: str, offset: int, limit: int) -> list[BedTemplate]:
        """The system templates and the tenant's own by name (bounded window, GP-NFR-017 style)."""
        return self._templates.list_visible(tenant_key=tenant_key, offset=offset, limit=limit)

    def get_template(self, key: BedTemplateKey, *, tenant_key: str) -> BedTemplate:
        """The template behind ``key`` when it is a system one or the tenant's; 404 otherwise."""
        found = self._templates.get_visible_by_key(key, tenant_key=tenant_key)
        if found is None:
            raise NotFoundError("BedTemplate", key)
        return found

    # ── Writes (§21.7, §21.8) ─────────────────────────────────────────────

    def create_template(
        self, *, tenant_key: str, user_key: str, role: TenantRole, data: BedTemplateInput
    ) -> BedTemplate:
        """A template of the tenant (never a system one: those ship with the migration)."""
        self._require_editor(role)
        owned = self._templates.count_owned(tenant_key=tenant_key)
        if owned >= MAX_TEMPLATES_PER_TENANT:
            raise _quota_exceeded(owned)
        template = BedTemplate(
            tenant_key=tenant_key,
            created_by=user_key,
            name=data.name,
            location_type_key=data.location_type_key,
            default_geometry=data.default_geometry,
            height_m=data.height_m,
            default_layout=data.default_layout,
            soil_profile_defaults=data.soil_profile_defaults,
            recurring_task_templates=list(data.recurring_task_templates),
        )
        self._resolve_references(template, tenant_key=tenant_key, only=None)
        created = self._templates.create_template(template)
        self._settle_create_against_quota(created, tenant_key=tenant_key)
        logger.info("bed_template.created", template_key=created.key, kind=created.default_geometry.kind.value)
        return created

    def _settle_create_against_quota(self, created: BedTemplate, *, tenant_key: str) -> None:
        """Take a create back that a concurrent create pushed over :data:`MAX_TEMPLATES_PER_TENANT` (#2529).

        The count before the insert and the insert are two statements, so two creates can both see one free place.
        Re-counted once the row exists, an overshoot is undone and refused - both racing creates may be refused
        then, never both kept. The same settle-after-insert the member limit uses (#2133); ``bed_templates`` has
        no per-tenant document a transaction could serialise on.
        """
        owned = self._templates.count_owned(tenant_key=tenant_key)
        if owned <= MAX_TEMPLATES_PER_TENANT:
            return
        if created.key:
            self._templates.delete_template(created.key, owner_tenant_key=tenant_key)
        logger.info("bed_template.create_taken_back", template_key=created.key, limit=MAX_TEMPLATES_PER_TENANT)
        raise _quota_exceeded(owned)

    def patch_template(
        self,
        key: BedTemplateKey,
        *,
        tenant_key: str,
        role: TenantRole,
        patch: BedTemplatePatch,
        is_platform_admin: bool = False,
    ) -> BedTemplate:
        """Change the fields present. A system template is a platform admin's to change, nobody else's."""
        stored = self.get_template(key, tenant_key=tenant_key)
        self._require_owner_for_write(stored, role=role, is_platform_admin=is_platform_admin, delete=False)
        sent = {name: getattr(patch, name) for name in patch.model_fields_set}
        # The stored row with the change laid over it runs through the model's validation (stripping included).
        merged = BedTemplate(**{**_dump(stored, by_alias=True), **sent})
        before = _dump(stored, mode="json")
        after = _dump(merged, mode="json")
        fields = {name: after.get(name) for name in _PATCH_COLUMNS if after.get(name) != before.get(name)}
        if not fields:
            return stored
        self._resolve_references(merged, tenant_key=tenant_key, only=frozenset(fields))
        updated = self._templates.update_template(key, fields, owner_tenant_key=stored.tenant_key)
        logger.info("bed_template.updated", template_key=key, fields=sorted(fields), system=stored.is_system)
        return updated

    def delete_template(
        self, key: BedTemplateKey, *, tenant_key: str, role: TenantRole, is_platform_admin: bool = False
    ) -> None:
        """Delete a template: a tenant's own by its lead, a system one by a platform admin only."""
        stored = self.get_template(key, tenant_key=tenant_key)
        self._require_owner_for_write(stored, role=role, is_platform_admin=is_platform_admin, delete=True)
        if not self._templates.delete_template(key, owner_tenant_key=stored.tenant_key):
            raise NotFoundError("BedTemplate", key)
        logger.info("bed_template.deleted", template_key=key, system=stored.is_system)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _require_owner_for_write(
        self, stored: BedTemplate, *, role: TenantRole, is_platform_admin: bool, delete: bool
    ) -> None:
        """403 unless the caller may write this row: a system template needs the platform admin, a tenant's own the
        role (grower to change, lead to delete). A foreign template never gets here - it was a 404 already."""
        if stored.is_system:
            require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity="bed template")
            return
        if delete:
            self._require_lead(role)
        else:
            self._require_editor(role)

    def _resolve_references(self, template: BedTemplate, *, tenant_key: str, only: frozenset[str] | None) -> None:
        """References of a body, resolved (GP-NFR-058): the location type must be a bed type, every
        ``recurring_task_templates`` key a task template the tenant can see. Nothing is written.

        A *system* template is read by every tenant, so its task templates must be global ones: resolving them
        under the editing platform admin's own tenant would let a key only that tenant owns be parked on a row
        every tenant reads (#2529)."""
        if only is None or "location_type_key" in only:
            flags = self._templates.bed_type_flags([template.location_type_key])
            if template.location_type_key not in flags:
                raise _not_found("location_type_key")
            if not flags[template.location_type_key]:
                raise PlanError(
                    ERROR_NOT_A_BED_TYPE,
                    "location_type_key must name a bed type (bed, raised bed, planter ...).",
                    status_code=422,
                    field="location_type_key",
                )
        if template.recurring_task_templates and (only is None or "recurring_task_templates" in only):
            visible = (
                self._templates.global_task_template_keys(template.recurring_task_templates)
                if template.is_system
                else self._templates.visible_task_template_keys(
                    template.recurring_task_templates, tenant_key=tenant_key
                )
            )
            findings: list[tuple[int | None, str, str, dict[str, Any]]] = [
                (None, f"recurring_task_templates[{index}]", ERROR_REFERENCE_NOT_FOUND, {})
                for index, task_key in enumerate(template.recurring_task_templates)
                if task_key not in visible
            ]
            if findings:
                raise PlanValidationError(findings)
