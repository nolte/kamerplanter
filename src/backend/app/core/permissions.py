"""REQ-024 v1.4 RBAC Permission Matrix.

Granular CRUD permissions per resource type and per ``TenantRole``,
exposed via a ``require_permission(...)`` FastAPI dependency factory
that the routers can drop in front of any tenant-scoped handler.

The matrix is intentionally explicit (resource × action × role → allow)
so that adding a new resource forces the implementer to make a
conscious call on every role's access. The default for unknown
combinations is *deny*.

Spec: ``spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md``
v1.4. The ``require_permission`` dependency is also referenced from
REQ-023 (Service Accounts) and REQ-027 (Light-Modus) — both follow up
on the same primitive once their respective surfaces land.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from app.common.enums import TenantRole


class ResourceType(StrEnum):
    """Top-level resource types in the tenant scope."""

    PLANT = "plant"
    SITE = "site"
    LOCATION = "location"
    PLANTING_RUN = "planting_run"
    HARVEST = "harvest"
    TANK = "tank"
    NUTRIENT_PLAN = "nutrient_plan"
    FERTILIZER = "fertilizer"
    TASK = "task"
    OBSERVATION = "observation"
    SENSOR = "sensor"
    CARE_PROFILE = "care_profile"
    IPM_TREATMENT = "ipm_treatment"
    CALENDAR_FEED = "calendar_feed"
    NOTIFICATION_CHANNEL = "notification_channel"
    TENANT = "tenant"
    MEMBERSHIP = "membership"
    INVITATION = "invitation"
    PRIVACY_REQUEST = "privacy_request"
    NOTE = "note"
    ATTACHMENT = "attachment"


class Action(StrEnum):
    """CRUD actions plus a few common verbs."""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    INVITE = "invite"  # tenant-only — issue a membership invitation
    EXPORT = "export"  # write to file (REQ-032 print/export)
    CONFIRM = "confirm"  # care reminders, harvest readiness


# Pseudo-roles only used internally by the matrix to mirror "anyone with
# membership" / "platform-level admin" without bloating TenantRole.
_PLATFORM_ADMIN = "platform_admin"


# ---------------------------------------------------------------------
# Permission matrix
# ---------------------------------------------------------------------
#
# The dict is keyed by (ResourceType, Action). Each entry is a frozenset
# of TenantRole values that are permitted to perform that action.
# Anything not listed is denied by default.
#
# The matrix mirrors REQ-024 §4 ("Roles & Permissions") without listing
# every spec table verbatim — instead it follows the three guard-rails:
#
#   1. ADMIN can do everything inside the tenant.
#   2. GROWER can read+create+update+delete every plant-domain resource
#      but cannot manage the tenant itself (memberships, invitations,
#      tenant settings) and cannot read foreign privacy requests.
#   3. VIEWER is read-only on plant-domain resources and has no access
#      to membership / invitation / privacy management.

_RBAC: dict[tuple[ResourceType, Action], frozenset[TenantRole]] = {}


def _grant(resource: ResourceType, actions: list[Action], roles: list[TenantRole]) -> None:
    for action in actions:
        existing = _RBAC.get((resource, action), frozenset())
        _RBAC[(resource, action)] = existing | frozenset(roles)


# Plant domain — admin + grower full CRUD, viewer read-only.
_PLANT_DOMAIN: list[ResourceType] = [
    ResourceType.PLANT,
    ResourceType.SITE,
    ResourceType.LOCATION,
    ResourceType.PLANTING_RUN,
    ResourceType.HARVEST,
    ResourceType.TANK,
    ResourceType.NUTRIENT_PLAN,
    ResourceType.FERTILIZER,
    ResourceType.TASK,
    ResourceType.OBSERVATION,
    ResourceType.SENSOR,
    ResourceType.CARE_PROFILE,
    ResourceType.IPM_TREATMENT,
    ResourceType.CALENDAR_FEED,
    ResourceType.NOTIFICATION_CHANNEL,
    ResourceType.NOTE,
    ResourceType.ATTACHMENT,
]
for _resource in _PLANT_DOMAIN:
    _grant(_resource, [Action.READ], [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER])
    _grant(
        _resource,
        [Action.CREATE, Action.UPDATE, Action.DELETE],
        [TenantRole.ADMIN, TenantRole.GROWER],
    )

# Domain-specific verbs.
_grant(ResourceType.HARVEST, [Action.CONFIRM], [TenantRole.ADMIN, TenantRole.GROWER])
_grant(ResourceType.TASK, [Action.CONFIRM], [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER])
_grant(
    ResourceType.CARE_PROFILE,
    [Action.CONFIRM],
    [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(ResourceType.CALENDAR_FEED, [Action.EXPORT], [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER])

# Tenant management — admin only.
_grant(
    ResourceType.TENANT,
    [Action.READ, Action.UPDATE],
    [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(ResourceType.TENANT, [Action.DELETE], [TenantRole.ADMIN])
_grant(
    ResourceType.MEMBERSHIP,
    [Action.READ],
    [TenantRole.ADMIN, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(
    ResourceType.MEMBERSHIP,
    [Action.CREATE, Action.UPDATE, Action.DELETE, Action.INVITE],
    [TenantRole.ADMIN],
)
_grant(
    ResourceType.INVITATION,
    [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE],
    [TenantRole.ADMIN],
)

# Privacy requests are owned by the user, not the tenant — admins
# cannot peek; viewers cannot read; the user always reaches them
# directly via REQ-025 endpoints.
# (No grant here — handled by per-user ownership checks instead.)


def has_permission(role: TenantRole, resource: ResourceType, action: Action) -> bool:
    """Return ``True`` when ``role`` may perform ``action`` on ``resource``."""

    return role in _RBAC.get((resource, action), frozenset())


def assert_permission(role: TenantRole, resource: ResourceType, action: Action) -> None:
    """Raise ``PermissionError`` when ``role`` cannot perform ``action``."""

    if not has_permission(role, resource, action):
        raise PermissionError(f"Tenant role '{role.value}' may not '{action.value}' on '{resource.value}'.")


def require_permission(
    resource: ResourceType,
    action: Action,
) -> Callable[..., Any]:
    """FastAPI dependency factory.

    Routers use it like::

        router = APIRouter(
            prefix="/plants",
            dependencies=[Depends(require_permission(ResourceType.PLANT, Action.READ))],
        )

    The dependency expects ``current_role`` to be resolved upstream by
    ``get_current_membership`` (provided by the tenant_scoped router).
    Until that dependency lands as a hard requirement on every route,
    the factory returns a callable that simply asserts the permission
    when given a role; if no role is supplied (e.g. unauthenticated
    contexts that should already have been filtered out) it raises.
    """

    def _dependency(current_role: TenantRole | None = None) -> TenantRole:
        if current_role is None:
            raise PermissionError(
                "require_permission needs a TenantRole — wire the dependency tree so get_current_membership runs first."
            )
        assert_permission(current_role, resource, action)
        return current_role

    return _dependency


def list_permissions(role: TenantRole) -> list[tuple[ResourceType, Action]]:
    """Return every (resource, action) tuple the given role may perform."""

    return sorted(
        ((resource, action) for (resource, action), roles in _RBAC.items() if role in roles),
        key=lambda pair: (pair[0].value, pair[1].value),
    )
