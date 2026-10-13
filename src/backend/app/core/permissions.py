"""REQ-024 v1.4 RBAC Permission Matrix.

Granular CRUD permissions per resource type and per ``TenantRole``,
declared as an explicit table (resource × action × role → allow) plus
the ``has_permission`` predicate that reads it. Adding a new resource
forces the implementer to make a conscious call on every role's access;
the default for unknown combinations is *deny*.

**One permission source (MT-045.6, #2144).** Every tenant-scoped CRUD gate —
:func:`app.common.auth.require_permission` and, since #2144, the attachment
guard too — decides through :func:`app.common.auth.role_permits` on the pure
:class:`app.domain.engines.membership_engine.MembershipEngine` predicates,
the single source of truth for the grower/lead delete boundary (REQ-049 §2.3).
This table describes; it does not decide. The guard
``tests/unit/guards/test_one_permission_source.py`` holds it equal to the gate
for every ``(resource, action)`` a router wires (REQ-024 AK-44c), so neither
is maintained alone. This module also keeps the MCP permission binding
(REQ-033 §4.4) below.

Spec: ``spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md``
v1.4. The permission model is also referenced from REQ-023 (Service
Accounts) and REQ-027 (Light-Modus).
"""

from __future__ import annotations

from enum import StrEnum

from app.common.enums import McpPermission, TenantRole


class ResourceType(StrEnum):
    """Top-level resource types in the tenant scope."""

    PLANT = "plant"
    SITE = "site"
    LOCATION = "location"
    PLANTING_RUN = "planting_run"
    SUCCESSION_PLAN = "succession_plan"
    HARVEST = "harvest"
    TANK = "tank"
    NUTRIENT_PLAN = "nutrient_plan"
    FERTILIZER = "fertilizer"
    TASK = "task"
    OBSERVATION = "observation"
    SENSOR = "sensor"
    CARE_PROFILE = "care_profile"
    OVERWINTERING_PROFILE = "overwintering_profile"
    IPM_TREATMENT = "ipm_treatment"
    CALENDAR_FEED = "calendar_feed"
    NOTIFICATION_CHANNEL = "notification_channel"
    TENANT = "tenant"
    MEMBERSHIP = "membership"
    INVITATION = "invitation"
    PRIVACY_REQUEST = "privacy_request"
    NOTE = "note"
    ATTACHMENT = "attachment"
    #: Named by their routers as free strings until MT-045.6 (#2144): the matrix
    #: could not describe them and said "denied" where the gate admits.
    DIARY_ENTRY = "diary-entry"
    FEEDING_EVENT = "feeding-event"
    WATERING_EVENT = "watering-event"
    WATERING_LOG = "watering-log"
    #: REQ-005 publishing a location's state to Home Assistant — an update only.
    HA_PUBLISH = "ha-publish"
    #: REQ-035 — the KI terminology glossary. Installation-wide content, not a
    #: tenant-owned record, so it is deliberately NOT in ``_PLANT_DOMAIN``: every
    #: member may READ it, a grower or lead may spend an LLM call to CREATE a
    #: cached explanation (#1460), and there is nothing here to update or delete —
    #: the cache is machine-managed (``glossary.cleanup_expired_cache``,
    #: ``glossary.invalidate_after_reingest``), never edited by hand.
    GLOSSARY = "glossary"


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
    ResourceType.SUCCESSION_PLAN,
    ResourceType.HARVEST,
    ResourceType.TANK,
    ResourceType.NUTRIENT_PLAN,
    ResourceType.FERTILIZER,
    ResourceType.TASK,
    ResourceType.OBSERVATION,
    ResourceType.SENSOR,
    ResourceType.CARE_PROFILE,
    ResourceType.OVERWINTERING_PROFILE,
    ResourceType.IPM_TREATMENT,
    ResourceType.CALENDAR_FEED,
    ResourceType.NOTIFICATION_CHANNEL,
    ResourceType.NOTE,
    ResourceType.ATTACHMENT,
    ResourceType.DIARY_ENTRY,
    ResourceType.FEEDING_EVENT,
    ResourceType.WATERING_EVENT,
    ResourceType.WATERING_LOG,
]
for _resource in _PLANT_DOMAIN:
    _grant(_resource, [Action.READ], [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER])
    _grant(_resource, [Action.CREATE, Action.UPDATE], [TenantRole.LEAD, TenantRole.GROWER])
    # DELETE is the irreversibility boundary: lead only (REQ-024 §1a.1 "❌D"
    # throughout, REQ-049 §2.3), as MembershipEngine.can_delete_resource decides.
    # The guard test_one_permission_source compares every wired pair (AK-44c).
    _grant(_resource, [Action.DELETE], [TenantRole.LEAD])

_grant(ResourceType.HA_PUBLISH, [Action.UPDATE], [TenantRole.LEAD, TenantRole.GROWER])

# Domain-specific verbs.
_grant(ResourceType.HARVEST, [Action.CONFIRM], [TenantRole.LEAD, TenantRole.GROWER])
_grant(ResourceType.TASK, [Action.CONFIRM], [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER])
_grant(
    ResourceType.CARE_PROFILE,
    [Action.CONFIRM],
    [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(ResourceType.CALENDAR_FEED, [Action.EXPORT], [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER])

# REQ-035 glossary — read for everyone, generation for a writer (#1460).
_grant(ResourceType.GLOSSARY, [Action.READ], [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER])
_grant(ResourceType.GLOSSARY, [Action.CREATE], [TenantRole.LEAD, TenantRole.GROWER])

# Tenant management — admin only.
_grant(
    ResourceType.TENANT,
    [Action.READ, Action.UPDATE],
    [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(ResourceType.TENANT, [Action.DELETE], [TenantRole.LEAD])
_grant(
    ResourceType.MEMBERSHIP,
    [Action.READ],
    [TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER],
)
_grant(
    ResourceType.MEMBERSHIP,
    [Action.CREATE, Action.UPDATE, Action.DELETE, Action.INVITE],
    [TenantRole.LEAD],
)
_grant(
    ResourceType.INVITATION,
    [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE],
    [TenantRole.LEAD],
)

# Privacy requests are owned by the user, not the tenant — admins
# cannot peek; viewers cannot read; the user always reaches them
# directly via REQ-025 endpoints.
# (No grant here — handled by per-user ownership checks instead.)


def has_permission(role: TenantRole, resource: ResourceType, action: Action) -> bool:
    """Return ``True`` when the matrix says ``role`` may perform ``action`` on ``resource``.

    Descriptive, not a gate (MT-045.6, #2144): no router decides on it. Its one
    reader is the guard ``test_one_permission_source``, which holds it equal to
    :func:`app.common.auth.role_permits` — the decision every router gate takes —
    for every pair a router wires (REQ-024 AK-44c).
    """

    return role in _RBAC.get((resource, action), frozenset())


# ---------------------------------------------------------------------
# REQ-033 MCP permission binding (§4.4)
# ---------------------------------------------------------------------
#
# MCP tools declare one of three permission classes (mcp.read / mcp.write /
# mcp.setup). A service account's *tenant role* decides which classes it may
# use — this keeps the binding inside the existing RBAC primitive (a service
# account is just a User with a membership) instead of introducing a parallel
# per-account permission store:
#
#   * viewer → read-only assistant ("diagnose-bot")           → {mcp.read}
#   * grower → day-to-day bot (care, diary, inspections)      → {mcp.read, mcp.write}
#   * admin  → one-off onboarding agent ("setup-agent")       → {mcp.read, mcp.write, mcp.setup}
#
# This mirrors REQ-033 §4.4's three-tier table exactly and makes mcp.setup —
# the destructive site/location class — admin-only (AC-S6). Anything not listed
# is denied by default.

_MCP_ROLE_PERMISSIONS: dict[TenantRole, frozenset[McpPermission]] = {
    TenantRole.VIEWER: frozenset({McpPermission.READ}),
    TenantRole.GROWER: frozenset({McpPermission.READ, McpPermission.WRITE}),
    TenantRole.LEAD: frozenset({McpPermission.READ, McpPermission.WRITE, McpPermission.SETUP}),
}


def has_mcp_permission(role: TenantRole, permission: McpPermission) -> bool:
    """Return ``True`` when ``role`` may invoke a tool guarded by ``permission``."""

    return permission in _MCP_ROLE_PERMISSIONS.get(role, frozenset())


def assert_mcp_permission(role: TenantRole, permission: McpPermission) -> None:
    """Raise :class:`ForbiddenError` when ``role`` lacks ``permission``.

    Raised with the MCP-protocol error code ``permission.denied`` (REQ-033 §8.1
    AC-2) so the transport layer forwards a stable, non-leaking code to the LLM
    client.
    """

    if not has_mcp_permission(role, permission):
        from app.common.exceptions import ForbiddenError

        raise ForbiddenError(f"MCP permission '{permission.value}' is not granted to role '{role.value}'.")


def list_mcp_permissions(role: TenantRole) -> list[McpPermission]:
    """Return the sorted MCP permission classes granted to ``role``."""

    return sorted(_MCP_ROLE_PERMISSIONS.get(role, frozenset()), key=lambda p: p.value)
