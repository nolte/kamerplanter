from __future__ import annotations

import hashlib
import hmac
import html
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from app.common.datetimes import ensure_aware_utc
from app.common.decoys import email_digest
from app.common.enums import (
    AdminScope,
    InvitationStatus,
    InvitationType,
    SecurityAuditAction,
    SecurityAuditVia,
    TenantRole,
    TenantStatus,
    TenantType,
)
from app.common.exceptions import (
    DuplicateError,
    FeatureNotConfiguredError,
    ForbiddenError,
    InvalidStatusTransitionError,
    MemberLimitReachedError,
    NotFoundError,
    TenantErasureClaimLostError,
    TenantErasureIncompleteError,
    ValidationError,
    WriteConflictError,
)
from app.common.log_privacy import log_subject, log_tenant, log_tenant_record_key
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, UNAVAILABLE_LOG_SUBJECT, ErasureEngine
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.erasure_repository import IErasureRepository
from app.domain.interfaces.invitation_repository import IInvitationRepository
from app.domain.interfaces.location_assignment_repository import (
    ILocationAssignmentRepository,
)
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.interfaces.pest_prototype_store import IPestPrototypeStore
from app.domain.interfaces.reference_index_store import IReferenceIndexStore
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.interfaces.tenant_erasure_executor import ITenantErasureExecutor
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.invitation import Invitation, InvitationLink
from app.domain.models.location_assignment import LocationAssignment
from app.domain.models.membership import MemberInfo, Membership, UserMembershipInfo
from app.domain.models.privacy import (
    OrganisationErasurePreview,
    OrganisationSettlement,
    PersonalTenantErasure,
    PersonalTenantErasurePreview,
)
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant, TenantWithRole
from app.domain.models.tenant_erasure import (
    TenantDeletionConfirmation,
    TenantDeletionStepUp,
    TenantErasureCancelConfirmation,
    TenantErasureOrigin,
    TenantErasureRecord,
)
from app.domain.models.user import User, allows_interactive_auth
from app.domain.services.location_ownership import SiteAnchorSource, resolve_owned_location
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.step_up_service import StepUpVerifier, default_step_up_verifier, echo_matches

logger = structlog.get_logger()

# SEC-004: tenant keys are ArangoDB document keys (system-generated numeric IDs
# or sanitised slugs). Restrict the storage-prefix builder to this safe charset
# so a malformed/empty key can never widen the delete prefix to ``t//`` (which
# would otherwise collapse to ``t`` and match *every* tenant).
_TENANT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:@()=;$!*',+%-]+$")

#: Absorbs the daily beat's own jitter so a one-day backoff does not miss the
#: next run by seconds (the account erasure's ``ERASURE_RETRY_SLACK``).
_TENANT_ERASURE_RETRY_SLACK = timedelta(hours=1)

#: Key of the technical tenant whose ``lead`` members are platform admins
#: (REQ-049 §2.5; the same lookup ``app.common.auth.is_platform_admin`` makes).
_PLATFORM_TENANT_KEY = "platform"

#: The states a platform admin's ``is_active`` toggle moves between (REQ-024 AK-56).
#: A tenant whose deletion is scheduled, running or that was orphaned leaves its state
#: only through the erasure itself or :meth:`TenantService.cancel_tenant_erasure` (#2123).
_TOGGLEABLE_STATUSES = frozenset({TenantStatus.ACTIVE, TenantStatus.SUSPENDED})

#: Fields of the tenant document no partial update may write: the lifecycle state
#: moves only through the step-up paths that own it (#2009, #2123).
_LIFECYCLE_FIELDS = frozenset({"is_active", "status", "deletion_scheduled_at"})


class TenantService:
    def __init__(
        self,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
        invitation_repo: IInvitationRepository,
        assignment_repo: ILocationAssignmentRepository,
        tenant_engine: TenantEngine,
        membership_engine: MembershipEngine,
        invitation_engine: InvitationEngine,
        storage_adapter: IObjectStorageAdapter | None = None,
        reference_index_store: IReferenceIndexStore | None = None,
        pest_image_repo: IPestImageRepository | None = None,
        pest_prototype_store: IPestPrototypeStore | None = None,
        observation_repo: IObservationRepository | None = None,
        tenant_erasure_executor: ITenantErasureExecutor | None = None,
        tenant_erasure_repo: ITenantErasureRepository | None = None,
        tombstone_salt: str = "",
        light_mode: bool = False,
        password_engine: PasswordEngine | None = None,
        step_up_verifier: StepUpVerifier | None = None,
        site_anchors: SiteAnchorSource | None = None,
        erasure_repo: IErasureRepository | None = None,
        security_audit: SecurityAuditService | None = None,
        task_repo: ITaskRepository | None = None,
        tenant_erasure_grace_days: int | None = None,
        email_service: IEmailService | None = None,
        user_repo: IUserRepository | None = None,
        max_members_ceiling: int = 50,
    ) -> None:
        # REQ-024 AK-64 (#2133) — the platform ceiling of every tenant's member limit
        # (``TENANT_MAX_MEMBERS_CEILING``); ``get_tenant_service`` passes the setting, and the class guard
        # ``test_membership_mutations_write_the_security_audit`` holds that it does.
        if max_members_ceiling < 1:
            raise ValueError("max_members_ceiling must be at least 1")
        self._max_members_ceiling = max_members_ceiling
        # #2123 (MT-027, REQ-024 AK-52) — how long an accepted tenant deletion stays
        # cancellable. ``None`` reads ``RETENTION_TENANT_ERASURE_GRACE_DAYS`` (default 90):
        # an unwired construction schedules rather than erases at once. ``0`` keeps the
        # immediate erasure of #1792 (self-hosted floor).
        if tenant_erasure_grace_days is None:
            from app.config.settings import settings as _settings

            tenant_erasure_grace_days = _settings.retention_tenant_erasure_grace_days
        if tenant_erasure_grace_days < 0:
            raise ValueError("tenant_erasure_grace_days must not be negative")
        self._tenant_erasure_grace = timedelta(days=tenant_erasure_grace_days)
        # #2123 — the members of a tenant whose deletion is scheduled are told the date
        # (Art. 20 export window). Best effort: ``None`` (doubles, light mode) skips the mail.
        self._email_service = email_service
        self._user_repo = user_repo
        # The tasks a membership that ends takes its assignee off (#2114). ``None`` only where no membership
        # is ever ended (doubles); ``get_tenant_service`` always wires it, and the class guard holds that every
        # method that deletes a membership calls :meth:`_end_task_assignments`.
        self._task_repo = task_repo
        # The persistent security audit of every membership, role and scope change
        # (MT-014, #2111). ``None`` only where no membership is ever changed (read-only
        # call sites, doubles); ``get_tenant_service`` always wires it, and
        # ``test_membership_mutations_write_the_security_audit`` holds that every
        # mutating method calls :meth:`_audit_membership`.
        self._security_audit = security_audit
        # The location → site reads a location assignment is checked through
        # (#1871 B3). Without them an assignment is refused, never stored unchecked.
        self._site_anchors = site_anchors
        # The account-erasure requests (REQ-025 AK-IE-06, #1924): who has asked to be
        # erased decides whether anybody may still be invited into their personal
        # tenant. Optional so non-invitation call sites stay unaffected; without it
        # the invitation gate does not apply.
        self._erasure_repo = erasure_repo
        self._tenant_repo = tenant_repo
        self._membership_repo = membership_repo
        self._invitation_repo = invitation_repo
        self._assignment_repo = assignment_repo
        self._tenant_engine = tenant_engine
        self._membership_engine = membership_engine
        self._invitation_engine = invitation_engine
        # NFR-013 §6.1 / REQ-025 — tenant deletion must also purge the tenant's
        # binary data (object storage) and its contributed reference-index
        # vectors. Optional so non-deletion call sites stay unaffected.
        self._storage_adapter = storage_adapter
        self._reference_index_store = reference_index_store
        # REQ-010 — pest-image link documents are a separate ArangoDB collection
        # (not covered by the object-storage prefix sweep). They are dropped on
        # tenant deletion alongside the attachment metadata.
        self._pest_image_repo = pest_image_repo
        # SEC-001 — a promoted contribution also has a DINOv2 embedding in the
        # recognition index; it is retracted on tenant deletion. Both optional so
        # non-deletion callers stay unaffected; the retract is a no-op when either
        # is unwired (it cannot resolve a label without the IPM repo).
        self._pest_prototype_store = pest_prototype_store
        # #1769 — the declared tenant-erasure inventory, its executor and the
        # persisted proof. The salt pseudonymises the account keys on retained
        # harvest/treatment/inspection rows; it never leaves this service.
        # #1769 review GDPR-001 — the tenant's raw sensor readings live in
        # TimescaleDB, outside the ArangoDB transaction; removed in the external
        # phase. ``None`` only where no deletion runs (other callers).
        self._observation_repo = observation_repo
        self._tenant_erasure_engine = TenantErasureEngine()
        self._tenant_erasure_executor = tenant_erasure_executor
        self._tenant_erasure_repo = tenant_erasure_repo
        self._tombstone_salt = tombstone_salt
        self._light_mode = light_mode
        # #1791 — the password step-up of a tenant deletion. Stateless (bcrypt).
        self._password_engine = password_engine or PasswordEngine()
        # #1816 — the one throttled step-up every irreversible account action passes.
        self._step_up_verifier = step_up_verifier or default_step_up_verifier(self._password_engine)

    # --- Tenant CRUD ---

    def create_personal_tenant(self, user_key: str, display_name: str) -> Tenant:
        """Auto-create a personal tenant during registration."""
        slug = self._tenant_engine.generate_slug(display_name)
        slug = self._ensure_unique_slug(slug)

        tenant = Tenant(
            name=display_name,
            slug=slug,
            tenant_type=TenantType.PERSONAL,
            owner_user_key=user_key,
            max_members=1,
        )
        tenant = self._found_tenant(tenant, user_key, via=SecurityAuditVia.REGISTRATION)

        logger.info("personal_tenant_created", subject=log_subject(user_key), tenant=log_tenant(tenant.key))
        return tenant

    def create_organization(
        self, user_key: str, name: str, description: str | None = None, max_members: int | None = None
    ) -> Tenant:
        """Create an organization tenant.

        ``max_members`` is at most the platform ceiling (REQ-024 AK-65, 422 above it); omitted, the
        organisation takes the ceiling.
        """
        errors = self._tenant_engine.validate_tenant_name(name)
        if errors:
            raise ValidationError(errors[0])
        member_limit = self._max_members_ceiling if max_members is None else max_members
        self._refuse_limit_above_ceiling(member_limit)

        org_count = self._tenant_repo.count_organizations_by_owner(user_key)
        if not self._tenant_engine.can_create_organization(org_count):
            raise ValidationError("Maximum number of organizations reached")

        slug = self._tenant_engine.generate_slug(name)
        slug = self._ensure_unique_slug(slug)

        tenant = Tenant(
            name=name,
            slug=slug,
            tenant_type=TenantType.ORGANIZATION,
            description=description,
            owner_user_key=user_key,
            max_members=member_limit,
        )
        tenant = self._found_tenant(tenant, user_key, via=SecurityAuditVia.TENANT_CREATION)

        logger.info("organization_created", subject=log_subject(user_key), tenant=log_tenant(tenant.key))
        return tenant

    def _found_tenant(self, tenant: Tenant, user_key: str, *, via: SecurityAuditVia) -> Tenant:
        """Write a new tenant, its founder's lead membership, both edges and the audit row atomically (#2118).

        REQ-049 §6: the founder gets the top domain role and both administrative scopes - a tenant whose
        creator could not invite anyone would be stranded from the first second. The four writes (and the
        security-audit row of #2111) are one transaction in :meth:`ITenantRepository.create_with_lead_membership`:
        written one by one, a failure between two of them left a tenant nobody could reach or delete, its
        slug taken. The one gate of the audit for a founding (the class guard
        ``test_membership_mutations_write_the_security_audit`` holds that every membership-creating method
        reaches it).
        """
        membership = Membership(
            user_key=user_key,
            tenant_key="",  # the tenant's own key, set by the repository once the tenant exists
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT, AdminScope.TECHNICAL],
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        written: list[SecurityAuditEntry] = []
        audit = self._security_audit

        def build_audit_row(stored_tenant: Tenant, stored_membership: Membership) -> SecurityAuditEntry:
            assert audit is not None  # only handed to the repository when it is wired
            entry = audit.membership_entry(
                action=SecurityAuditAction.MEMBERSHIP_ADDED,
                via=via,
                actor_user_key=user_key,
                target_user_key=user_key,
                tenant_key=stored_tenant.key or "",
                membership_key=stored_membership.key,
                new_role=str(stored_membership.role),
                new_scopes=[str(scope) for scope in stored_membership.admin_scopes],
            )
            written.append(entry)
            return entry

        stored_tenant, _founder = self._tenant_repo.create_with_lead_membership(
            tenant, membership, audit=build_audit_row if audit is not None else None
        )
        for entry in written:
            audit.announce(entry)  # type: ignore[union-attr]  # ``written`` is only filled when audit is wired
        return stored_tenant

    def get_tenant(self, tenant_key: str) -> Tenant:
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if not tenant:
            raise NotFoundError("Tenant", tenant_key)
        return tenant

    def get_personal_tenant(self, user_key: str) -> Tenant | None:
        """The active user's own personal tenant, or ``None`` if they have none.

        Every registered user gets exactly one auto-created ``PERSONAL`` tenant
        they own (:meth:`create_personal_tenant`, REQ-024), and in light mode the
        single anonymous system user carries one too (``seed_light_mode``). This
        resolves it by owner + type — the newest wins on the (unexpected) chance a
        user owns several — and returns ``None`` rather than raising, so a caller
        on a global route can fall back to the shared catalogue instead of failing
        the request.

        This is the F-3 write-stamping anchor for the *global* species route,
        which has no ``/t/{slug}/`` segment for :func:`get_current_tenant` to bind
        to. F-5 introduces the general active-tenant resolution for global-but-
        tenant-aware routes; when it lands, an interactive create can bind to the
        tenant the caller is actually acting in rather than always their personal
        one (see #808 A1).
        """
        owned = self._tenant_repo.list_by_owner(user_key)
        personal = [t for t in owned if t.tenant_type == TenantType.PERSONAL]
        if not personal:
            return None
        personal.sort(key=lambda t: t.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return personal[0]

    def get_tenant_by_slug(self, slug: str) -> Tenant:
        tenant = self._tenant_repo.get_by_slug(slug)
        if not tenant:
            raise NotFoundError("Tenant", slug)
        return tenant

    def update_tenant(self, tenant_key: str, data: dict) -> Tenant:
        """Apply a partial update to one tenant, re-deriving the slug on rename.

        ``data`` is a partial payload and is passed through to
        :meth:`ITenantRepository.update_fields`, so the **caller owns the
        allow-list**: build it from a closed request schema's ``model_dump()``
        or from named fields, never from a raw request body.

        The tenant-scoped ``PATCH /t/{slug}`` reaches this with
        ``TenantUpdateRequest`` (``name``, ``description``, ``max_members``).
        Neither that schema nor ``AdminTenantUpdate`` sets ``extra="allow"``, and
        that closedness is the only thing keeping ``owner_user_key``,
        ``is_platform``, ``tenant_type``, ``slug`` and ``settings`` out of the
        payload: ``update_fields`` applies ``data`` through
        ``model_copy(update=...)``, which does not validate. ``slug`` is derived
        here, from ``name``, and never accepted from a caller.

        **``is_active`` is refused here (#2009).** Deactivating a tenant locks every
        member out of it; it is a step-up act and goes through
        :meth:`admin_update_tenant`, which verifies the platform admin's step-up
        before it writes. A payload carrying ``is_active`` on this path is a
        programming error (no request schema of this path has the field), so it
        fails loudly instead of writing the flag past the step-up.
        """
        if _LIFECYCLE_FIELDS & set(data):
            raise ValueError(
                "lifecycle changes go through admin_update_tenant / delete_tenant / cancel_tenant_erasure, "
                "which verify the step-up (#2009, #2123)"
            )
        return self._apply_tenant_update(tenant_key, data)

    def admin_update_tenant(
        self,
        tenant_key: str,
        data: dict,
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> Tenant:
        """Apply a partial platform-admin update to one tenant (#997, #2009).

        ``PATCH /admin/platform/tenants/{key}`` with ``AdminTenantUpdate`` — the
        fields of the tenant-scoped update plus ``is_active``, which only a platform
        admin may set. Routed here by #997, which ended a router that wrote to the
        tenants collection itself.

        **Step-up when ``is_active`` changes (#2009, REQ-024 AK-56).** Deactivating a
        tenant locks every member out of it with one request. The rule of #1992 — "a
        change that can lead to erasure or lockout of another account is a step-up
        act" — therefore applies: any actual change of ``is_active`` passes the
        admin's *own* step-up (``requester`` — the password, the fresh
        re-authentication or the mailed code; an API key is 403, 429 when locked),
        bound to this tenant (#1884). Reactivating is gated as well, as it is for an
        account (#1857): it restores access a deliberate deactivation took away. A
        rename, a description or a re-send of the current value needs none, so the
        edit form stays one click — and a re-sent value is not written back, so it
        cannot undo a concurrent change (#1992 review SEC-003).

        The platform tenant is refused (403, #1021) before any step-up is asked for.
        Without a valid step-up nothing is written.
        """
        current = self._tenant_repo.get_by_key(tenant_key)
        if current is None:
            raise NotFoundError("Tenant", tenant_key)
        if (_LIFECYCLE_FIELDS - {"is_active"}) & set(data):
            raise ValueError("status changes go through delete_tenant / cancel_tenant_erasure (#2123)")
        wanted = data.get("is_active")
        changes_active = wanted is not None and bool(wanted) != bool(current.is_active)
        if changes_active and not wanted and current.is_platform:
            raise ForbiddenError("The platform tenant cannot be deactivated.")
        if changes_active and current.status not in _TOGGLEABLE_STATUSES:
            # #2123 — reactivating a tenant whose deletion is scheduled would hand it back to
            # its members while the beat still erases it at the end of the grace; a running
            # (``deleted``) one cannot be stopped at all. Cancel the deletion instead.
            raise InvalidStatusTransitionError(
                str(current.status), str(TenantStatus.ACTIVE if wanted else TenantStatus.SUSPENDED)
            )
        if changes_active:
            self._step_up_verifier.verify(
                requester,
                action="admin_tenant_update",
                # #1884 — a factor obtained to deactivate this tenant confirms this one only.
                target=tenant_key,
                echo_ok=None,
                password=current_password,
                code=step_up_code,
                reauth_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )
        data = {k: v for k, v in data.items() if k != "is_active"}
        if changes_active:
            # #2123 — the bool of the request is the admin's suspension switch on the status model.
            data["status"] = TenantStatus.ACTIVE if wanted else TenantStatus.SUSPENDED
        if not data:
            return current
        return self._apply_tenant_update(tenant_key, data)

    def _apply_tenant_update(self, tenant_key: str, data: dict) -> Tenant:
        """The write both update paths share: the #1021 guard, the slug on rename, the store.

        **The platform tenant cannot be deactivated (#1021).** ``delete_tenant``
        refuses the platform tenant (``is_platform`` → 403); deactivating it via
        ``{"is_active": False}`` (since #2123 ``{"status": "suspended"}``) slipped through because this path had no such
        guard. It stays here, under both entry points, with the same
        :class:`ForbiddenError` (403) shape ``delete_tenant`` uses, scoped to
        deactivation only — renaming or re-describing the platform tenant still
        works.
        """
        if data.get("status", TenantStatus.ACTIVE) != TenantStatus.ACTIVE:
            tenant = self._tenant_repo.get_by_key(tenant_key)
            if not tenant:
                raise NotFoundError("Tenant", tenant_key)
            if tenant.is_platform:
                raise ForbiddenError("The platform tenant cannot be deactivated.")

        if "max_members" in data:
            # REQ-024 AK-64 (#2133): set to at most the ceiling, by a tenant manager and a platform admin
            # alike. Lowering it below the current member count removes nobody; it stops the next join.
            self._refuse_limit_above_ceiling(data["max_members"])

        if "name" in data:
            errors = self._tenant_engine.validate_tenant_name(data["name"])
            if errors:
                raise ValidationError(errors[0])
            data["slug"] = self._tenant_engine.generate_slug(data["name"])
            data["slug"] = self._ensure_unique_slug(data["slug"], exclude_key=tenant_key)

        tenant = self._tenant_repo.update_fields(tenant_key, data)
        if not tenant:
            raise NotFoundError("Tenant", tenant_key)
        return tenant

    # --- Tenant deletion (REQ-024 / REQ-025 / NFR-011, #1769) ---

    def delete_tenant(
        self,
        tenant_key: str,
        *,
        requester: User,
        authenticated_with_api_key: bool,
        confirmation: TenantDeletionConfirmation,
        origin: TenantErasureOrigin,
        client_ip: str | None,
        now: datetime | None = None,
    ) -> TenantErasureRecord:
        """Erase the tenant and everything it holds, and persist the proof.

        What goes and what stays is :attr:`TenantErasureEngine.INVENTORY`, not
        this method: the external phase (contributed reference vectors and pest
        prototypes, attachment metadata, pest-image links, the ``t/{key}/``
        storage prefix) runs first, then one ArangoDB transaction deletes every
        ``delete`` entry and every edge touching it, pseudonymises the retention
        rows (CanG / PflSchG) and removes the tenant document.

        **Who may (#1791).** Checked here, not only at the routers, so both entry
        points share it and neither can drift (``requester``, ``confirmation``
        and ``origin`` are keyword-only without a default for that reason):

        * ``origin="tenant_management"`` — the requester holds an *active*
          membership in the tenant with the lead role **and** the ``management``
          scope (:meth:`MembershipEngine.can_delete_tenant`, REQ-024 §1a.2);
        * ``origin="platform_admin"`` — the requester is a platform admin (an
          active ``lead`` membership in the ``platform`` tenant, REQ-049 §2.5);
        * never a service account, and never a request authenticated with an API
          key — even one a human account issued (#1791 review SEC-001): a key
          is a stored M2M credential, not a person who can re-authenticate;
        * both: the step-up in *confirmation* — the tenant's slug typed back, and
          the current password when the account has one, the one-time code
          mailed to it when it has none (a federated account, #1815; before, the
          slug echo alone confirmed it). Checked by the shared
          :class:`~app.domain.services.step_up_service.StepUpVerifier`, which
          also throttles the password per account and ``client_ip`` (#1816):
          a locked step-up is 429 before the password is tested.

        ``origin`` is set by the router, never by the client, and it only picks
        *which* membership is proven — claiming ``platform_admin`` without the
        platform membership is refused like any other caller.

        Order of effects:

        1. Refuse a requester without the right (403), the platform tenant (403),
           a wrong slug echo (422), a missing or wrong password (401) and a
           deployment that cannot erase (503) — before anything changes.
        2. Persist the record (one per tenant, so a concurrent second deletion
           collides, 409). **With a grace (#2123, REQ-024 AK-52)** the record is
           ``scheduled`` until ``now + RETENTION_TENANT_ERASURE_GRACE_DAYS``, the tenant
           becomes ``pending_deletion`` (it resolves for nobody, its memberships stay
           as they are so :meth:`cancel_tenant_erasure` restores them unchanged), the
           members are told the date, and the request returns. A repeated request
           inside the grace re-asserts the state and returns the same record.
        3. After the grace (or at once with a grace of ``0``) the tenant becomes
           ``deleted``, every membership is deactivated and the erasure runs:
           ``completed`` only when the executor found nothing left; otherwise
           ``partially_completed`` with a backoff that :meth:`resume_tenant_erasures`
           (daily beat) retries.

        Raises:
            NotFoundError: no such tenant (and no open record for it).
            ForbiddenError: the requester may not delete this tenant, or the
                platform tenant / the light-mode tenant.
            ValidationError: the echoed slug is not the tenant's (HTTP 422).
            UnauthorizedError: the password or code is missing or wrong (HTTP 401;
                ``STEP_UP_CODE_REQUIRED`` when a federated account sent no code).
            FeatureNotConfiguredError: the deployment cannot erase (HTTP 503).
            WriteConflictError: another run holds the deletion (HTTP 409).
            TenantErasureIncompleteError: something still holds the tenant; the
                record stays open and is retried (HTTP 500).
            Exception: whatever the run raised, after the failed attempt was
                recorded.
        """
        now = now or datetime.now(UTC)
        record_key = TenantErasureEngine.record_key(tenant_key)
        self._authorize_tenant_deletion(
            tenant_key, requester=requester, authenticated_with_api_key=authenticated_with_api_key, origin=origin
        )
        tenant = self._tenant_repo.get_by_key(tenant_key)
        record = self._require_tenant_erasure_repo().get(record_key)
        if tenant is None and (record is None or record.status == "completed"):
            raise NotFoundError("Tenant", tenant_key)
        if tenant is not None and tenant.is_platform:
            raise ForbiddenError("The platform tenant cannot be deleted.")
        if tenant is not None and self._light_mode:
            # #1769 review SEC-002 — in light mode the single system tenant IS the
            # installation, and the light-mode seed does not re-create it.
            raise ForbiddenError("The tenant of a light-mode installation cannot be deleted.")
        # A tenant whose document an earlier attempt already removed has no slug
        # left to read. The open record keeps a salted digest of it, so the slug
        # the caller saw still confirms; the key does too (a record written
        # before the digest existed, or a caller who only has the key).
        step_up = self._verify_tenant_deletion_step_up(
            tenant.slug if tenant is not None else None,
            tenant_key=tenant_key,
            slug_digest=record.slug_digest if record is not None else None,
            requester=requester,
            confirmation=confirmation,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            raise FeatureNotConfiguredError("tenant_deletion", configuration_error)
        requested_by_ref = log_subject(requester.key)
        logger.info(
            "tenant_erasure.authorized",
            tenant=log_tenant(tenant_key),
            origin=origin,
            step_up=step_up,
            subject=requested_by_ref,
        )

        if record is None:
            # #2123 (MT-027) — a tenant that still exists is scheduled, not erased: the
            # grace is the window in which the management can cancel and every member can
            # export what is theirs (Art. 20). ``0`` keeps the immediate erasure.
            scheduled_for = now + self._tenant_erasure_grace if tenant is not None else None
            if scheduled_for is not None and scheduled_for <= now:
                scheduled_for = None
            try:
                record = self._require_tenant_erasure_repo().create_with_key(
                    TenantErasureRecord(
                        tenant_key=tenant_key,
                        tenant_type=str(tenant.tenant_type) if tenant is not None else "unknown",
                        origin=origin,
                        requested_by_subject=requested_by_ref,
                        step_up=step_up,
                        slug_digest=self._tenant_slug_digest(tenant.slug) if tenant is not None else None,
                        status="scheduled" if scheduled_for is not None else "in_progress",
                        requested_at=now,
                        scheduled_for=scheduled_for,
                    ),
                    record_key,
                )
            except (DuplicateError, WriteConflictError) as exc:
                raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION) from exc
            if scheduled_for is not None and tenant is not None:
                self._schedule_tenant_erasure(tenant, scheduled_for, requester_key=requester.key)
                return record

        elif record.status == "scheduled":
            # #2123 — a repeated request inside the grace changes nothing but re-asserts the
            # freeze (a first request whose status write failed left the record only); the
            # date stays the one the members were told.
            if tenant is not None and record.scheduled_for is not None:
                self._set_tenant_status(tenant_key, TenantStatus.PENDING_DELETION, record.scheduled_for)
            return record

        elif self._is_held_by_a_live_run(record, now):
            # An earlier request's run is working on it right now (its heartbeat is
            # fresh): refuse as before, do not queue a second one. A record a failed run left
            # ``partially_completed`` is re-dispatched at once instead of waiting for its
            # backoff — an authorised caller asking again is an operator retry (as it was
            # before #1792, when the repeated request re-ran the erasure inline).
            raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION)

        # Freeze, then hand the work to a Celery task (#1792). The task claims the
        # record atomically; a request that repeats an open deletion only
        # re-dispatches it, and of two tasks the claim lets one run.
        self._mark_tenant_erasing(tenant_key)
        self._membership_repo.deactivate_all_for_tenant(tenant_key)
        self._dispatch_tenant_erasure(record_key)
        return record

    # --- Tenant lifecycle: grace and cancellation (REQ-024 AK-52, MT-027 #2123) ---

    def _set_tenant_status(self, tenant_key: str, status: TenantStatus, scheduled_at: datetime | None) -> None:
        """Write the lifecycle state; a tenant document an earlier attempt already removed is left alone."""
        self._tenant_repo.update_fields(tenant_key, {"status": status, "deletion_scheduled_at": scheduled_at})

    def _mark_tenant_erasing(self, tenant_key: str) -> None:
        """The grace is over and a run holds the deletion: the tenant is ``deleted``, no longer cancellable.

        Called after every claim (and on the immediate path of a zero grace). The tenant
        already resolved for nobody while ``pending_deletion``; the state now tells the
        admin panel and :meth:`cancel_tenant_erasure` that nothing can be taken back.
        """
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if tenant is None or tenant.status == TenantStatus.DELETED:
            return
        self._set_tenant_status(tenant_key, TenantStatus.DELETED, tenant.deletion_scheduled_at)

    def _schedule_tenant_erasure(
        self, tenant: Tenant, scheduled_for: datetime, *, requester_key: str | None, orphaned: bool = False
    ) -> None:
        """Freeze *tenant* for the grace and tell its members the date (#2123).

        The freeze is the state, not the memberships: a ``pending_deletion`` (or
        ``orphaned``) tenant resolves for nobody (``Tenant.is_active``, #2105), while
        every membership stays as it is — so a cancellation restores each member's
        access unchanged, and the management that may cancel is still provable from the
        stored membership. The memberships are deactivated when the grace is over and a
        run claims the deletion (:meth:`_mark_tenant_erasing`).
        """
        tenant_key = tenant.key or ""
        status = TenantStatus.ORPHANED if orphaned else TenantStatus.PENDING_DELETION
        self._set_tenant_status(tenant_key, status, scheduled_for)
        logger.info(
            "tenant_erasure.scheduled",
            tenant=log_tenant(tenant_key),
            status=status.value,
            scheduled_for=scheduled_for.isoformat(),
        )
        self._notify_members_of_scheduled_erasure(tenant, scheduled_for, skip_user_key=requester_key, orphaned=orphaned)

    def _notify_members_of_scheduled_erasure(
        self, tenant: Tenant, scheduled_for: datetime, *, skip_user_key: str | None, orphaned: bool = False
    ) -> int:
        """Mail every active member the deletion date and how to keep what is theirs (Art. 20); best effort.

        Never raises: the deletion is accepted whatever a mailbox does. Organisations are
        named (their members know them by that name); a personal tenant is not — its name
        is its owner's display name (the rule of the account-erasure notice, #1824).
        Returns how many members were mailed.
        """
        if self._email_service is None or self._user_repo is None:
            logger.warning("tenant_erasure.members_not_notified", tenant=log_tenant(tenant.key), reason="no_mailer")
            return 0
        body = self._scheduled_erasure_notice_body(tenant, scheduled_for, orphaned=orphaned)
        sent = 0
        try:
            member_keys = self._membership_repo.active_member_user_keys(tenant_key=tenant.key or "")
        except Exception as exc:  # noqa: BLE001 - the deletion stands; the notice is best effort
            logger.error(
                "tenant_erasure.members_notice_failed", tenant=log_tenant(tenant.key), error_type=type(exc).__name__
            )
            return 0
        for member_key in member_keys:
            if member_key == skip_user_key:
                continue
            try:
                member = self._user_repo.get_by_key(member_key)
                if member is None or not member.email:
                    continue
                self._email_service.send_notification_email(
                    to_email=member.email,
                    subject="Kamerplanter — a garden you are a member of will be deleted",
                    html_body=body,
                )
            except Exception as exc:  # noqa: BLE001 - one mailbox must not stop the others
                logger.warning(
                    "tenant_erasure.member_notice_failed", member=log_subject(member_key), error_type=type(exc).__name__
                )
                continue
            sent += 1
        logger.info("tenant_erasure.members_notified", tenant=log_tenant(tenant.key), notified=sent)
        return sent

    @staticmethod
    def _scheduled_erasure_notice_body(tenant: Tenant, scheduled_for: datetime, *, orphaned: bool = False) -> str:
        due = html.escape(scheduled_for.strftime("%Y-%m-%d"))
        if tenant.tenant_type == TenantType.ORGANIZATION:
            which = f"The organisation <strong>{html.escape(tenant.name)}</strong>"
        else:
            which = "A personal garden you are a member of"
        if orphaned:
            # #2134 — nobody is left who could administer it, so nobody can cancel.
            who_can_stop = (
                "Nobody is left who can administer it: its last person with the management right deleted their account."
            )
        else:
            who_can_stop = "The garden's management can cancel the deletion until then."
        return (
            "<h2>A garden you are a member of will be deleted</h2>"
            f"<p>{which} is scheduled for deletion on {due} (UTC), including its sites, plants, diary entries, "
            "tasks and photos. Until then it is closed for everybody.</p>"
            "<p>What you entered there yourself is part of your personal data export: download it under "
            f"<em>Settings &rarr; Privacy</em> before that date if you want to keep it. {who_can_stop}</p>"
            "<p>Your own account is not affected.</p>"
        )

    def _is_due(self, record: TenantErasureRecord, now: datetime) -> bool:
        """Whether *record* may be run now: not ``scheduled``, or its grace has ended (#2123)."""
        if record.status != "scheduled":
            return True
        due_at = ensure_aware_utc(record.scheduled_for)
        return due_at is None or due_at <= now

    def cancel_tenant_erasure(
        self,
        tenant_key: str,
        *,
        requester: User,
        authenticated_with_api_key: bool,
        confirmation: TenantErasureCancelConfirmation,
        origin: TenantErasureOrigin,
        client_ip: str | None,
    ) -> Tenant:
        """Withdraw a scheduled tenant deletion inside its grace and reopen the tenant (#2123, REQ-024 AK-52).

        **Who may** is the rule of :meth:`delete_tenant`, proven from the stored
        membership: ``tenant_management`` — the requester's active membership holds the
        lead role **and** the ``management`` scope; ``platform_admin`` — an active
        ``lead`` membership in the platform tenant. Never a service account, never an
        API key. Then the requester's own step-up (``tenant_erasure_cancel``, bound to
        the tenant's key). Nothing changes before both pass.

        The record is removed only while it is still ``scheduled``
        (:meth:`ITenantErasureRepository.delete_scheduled`): of a cancellation and the
        beat's claim exactly one wins, and a deletion a run already holds cannot be
        taken back (422, ``deleted``). The tenant returns to ``active`` with every
        membership as it was — the grace never touched them. An ``orphaned``
        organisation (#2134) is not cancellable (422): nobody is left who could
        administer it, so it runs out its grace and is erased (REQ-024 AK-65).

        Raises:
            ForbiddenError: the requester may not, or authenticated with an API key.
            NotFoundError: no such tenant.
            InvalidStatusTransitionError: nothing is scheduled (HTTP 422).
            UnauthorizedError / StepUpLockedError: the step-up failed (401 / 429).
        """
        self._authorize_tenant_deletion(
            tenant_key, requester=requester, authenticated_with_api_key=authenticated_with_api_key, origin=origin
        )
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if tenant is None:
            raise NotFoundError("Tenant", tenant_key)
        if tenant.status != TenantStatus.PENDING_DELETION:
            # #2134 — an ``orphaned`` organisation has nobody left who could administer it; handing it
            # back would recreate the stranded tenant the settlement exists to end (REQ-023 §5a.5 dropped).
            raise InvalidStatusTransitionError(str(tenant.status), str(TenantStatus.ACTIVE))
        self._step_up_verifier.verify(
            requester,
            action="tenant_erasure_cancel",
            # #1884 — a factor obtained to cancel this tenant's deletion confirms this one only.
            target=tenant_key,
            echo_ok=None,
            password=confirmation.password,
            code=confirmation.step_up_code,
            reauth_token=confirmation.step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        record_key = TenantErasureEngine.record_key(tenant_key)
        if not self._require_tenant_erasure_repo().delete_scheduled(record_key):
            # A run claimed it between the read above and now (or nothing was recorded).
            raise InvalidStatusTransitionError(str(TenantStatus.DELETED), str(TenantStatus.ACTIVE))
        self._set_tenant_status(tenant_key, TenantStatus.ACTIVE, None)
        logger.info(
            "tenant_erasure.cancelled", tenant=log_tenant(tenant_key), origin=origin, subject=log_subject(requester.key)
        )
        restored = self._tenant_repo.get_by_key(tenant_key)
        if restored is None:  # pragma: no cover - the tenant was read above and nothing deletes it in between
            raise NotFoundError("Tenant", tenant_key)
        return restored

    def cancel_tenant_erasure_by_slug(self, slug: str, **kwargs: Any) -> Tenant:
        """:meth:`cancel_tenant_erasure` for the tenant-scoped route, which knows the slug only (#2123).

        A ``pending_deletion`` tenant resolves for nobody (#2105), so the route cannot go
        through :func:`~app.common.auth.get_current_tenant`. An unknown slug answers like
        a tenant the requester may not administer (403, one message): the route is no
        existence oracle.
        """
        tenant = self._tenant_repo.get_by_slug(slug)
        if tenant is None or not tenant.key:
            raise ForbiddenError("Deleting a tenant requires the lead role and the management scope.")
        return self.cancel_tenant_erasure(tenant.key, **kwargs)

    def _is_held_by_a_live_run(self, record: TenantErasureRecord, now: datetime) -> bool:
        """Whether a run claimed *record* and its heartbeat is still inside the stale window."""
        if record.status != "in_progress" or record.last_attempt_at is None or record.updated_at is None:
            return False
        return record.updated_at > now - timedelta(hours=TenantErasureEngine.STALE_AFTER_HOURS)

    def _dispatch_tenant_erasure(self, record_key: str) -> None:
        """Enqueue the worker that runs the deletion of *record_key* (#1792).

        Lazy import — the task module imports the dependency wiring that imports
        this service. A broker outage must not undo the freeze or fail the request:
        the record stays open and the daily ``resume_tenant_erasures`` beat claims it
        once its ``updated_at`` is stale (the same recovery as a crashed worker).
        """
        try:
            from app.tasks.tenant_tasks import run_tenant_erasure

            # A short, bounded publish retry: an unreachable broker must not hold the request thread
            # (kombu's default retries for a long time); the beat is the safety net.
            run_tenant_erasure.apply_async(
                (record_key,), retry=True, retry_policy={"max_retries": 1, "interval_start": 0, "interval_max": 1}
            )
            logger.info("tenant_erasure.dispatched", record_key=log_tenant_record_key(record_key))
        except Exception as exc:  # noqa: BLE001 — broker outage is survivable, the beat retries
            logger.error(
                "tenant_erasure.dispatch_failed",
                record_key=log_tenant_record_key(record_key),
                error_type=type(exc).__name__,
            )

    def run_tenant_erasure_task(self, record_key: str, now: datetime | None = None) -> dict[str, object]:
        """Run the deletion *record_key* names, as the Celery worker (#1792).

        Claims the record atomically — a second dispatch, the daily beat, or a run
        that is still alive finds it held and does nothing — then runs the same
        batched, heartbeat-refreshing erasure as every other path. Never raises for
        a failed run: the failure is recorded on the record (backoff, escalation)
        and the beat retries it.

        The returned ``record_key`` is the log form (``ter_ten_…``, #2020): the worker
        logs a task's return value on its ``succeeded in …`` line, and the result is
        read by nobody (no result backend, the caller ``apply_async``s and moves on).
        """
        now = now or datetime.now(UTC)
        repo = self._require_tenant_erasure_repo()
        record = repo.get(record_key)
        if record is None or record.status == "completed":
            return {"record_key": log_tenant_record_key(record_key), "outcome": "nothing_to_do"}
        if not self._is_due(record, now):
            # #2123 — inside its grace a deletion is the beat's to start, never a stray dispatch's.
            return {"record_key": log_tenant_record_key(record_key), "outcome": "scheduled"}
        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            logger.error(
                "tenant_erasure.run_not_configured",
                record_key=log_tenant_record_key(record_key),
                reason=configuration_error,
            )
            return {"record_key": log_tenant_record_key(record_key), "outcome": "held"}
        claimed = self._claim_tenant_erasure(record_key, now)
        if claimed is None:
            return {"record_key": log_tenant_record_key(record_key), "outcome": "not_claimed"}
        self._mark_tenant_erasing(claimed.tenant_key)
        self._membership_repo.deactivate_all_for_tenant(claimed.tenant_key)
        finished = self._run_tenant_erasure(claimed, now, raise_on_failure=False)
        return {"record_key": log_tenant_record_key(record_key), "outcome": finished.status}

    def _authorize_tenant_deletion(
        self, tenant_key: str, *, requester: User, authenticated_with_api_key: bool, origin: TenantErasureOrigin
    ) -> None:
        """Refuse a requester who may not erase *tenant_key* (403, #1791).

        Proven from the stored membership, not from the request context the
        router resolved: the service is the one place both routes pass, and it
        must not trust a caller-supplied role.
        """
        if not allows_interactive_auth(requester) or authenticated_with_api_key:
            raise ForbiddenError("A tenant can only be deleted from a signed-in session, not with an API key.")
        user_key = requester.key or ""
        if origin == "platform_admin":
            membership = self._membership_repo.get_by_user_and_tenant(user_key, _PLATFORM_TENANT_KEY)
            allowed = bool(membership and membership.is_active and membership.role == TenantRole.LEAD)
        else:
            membership = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
            allowed = bool(
                membership
                and membership.is_active
                and MembershipEngine.can_delete_tenant(membership.role, membership.admin_scopes)
            )
        if not allowed:
            raise ForbiddenError("Deleting a tenant requires the lead role and the management scope.")

    def _tenant_slug_digest(self, slug: str) -> str:
        """Salted HMAC of a tenant slug, purpose-separated from every other use of the salt (#1791)."""
        return hmac.new(
            self._tombstone_salt.encode(), f"tenant-deletion-slug:{slug}".encode(), hashlib.sha256
        ).hexdigest()

    def _verify_tenant_deletion_step_up(
        self,
        expected_slug: str | None,
        *,
        tenant_key: str,
        slug_digest: str | None,
        requester: User,
        confirmation: TenantDeletionConfirmation,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> TenantDeletionStepUp:
        """Check the step-up of a tenant deletion; return how it was confirmed (#1791, #1816).

        The slug echo is this act's own part — which spellings name the tenant.
        Everything else (who may re-authenticate, the throttle, the password of a
        local account, the mailed one-time code of a federated one, #1815) is the
        shared :class:`StepUpVerifier`, the same rule account erasure runs. Its
        result (``password`` / ``email_code``) is what the record stores.
        """
        echoed = confirmation.confirm_slug
        if expected_slug is not None:
            matches = echo_matches(echoed, expected_slug)
        else:
            matches = echo_matches(echoed, tenant_key) or (
                slug_digest is not None and hmac.compare_digest(self._tenant_slug_digest(echoed.strip()), slug_digest)
            )
        return self._step_up_verifier.verify(
            requester,
            action="tenant_deletion",
            # #1884 — a factor obtained to delete this tenant confirms this one only.
            target=tenant_key,
            echo_ok=matches,
            password=confirmation.password,
            code=confirmation.step_up_code,
            reauth_token=confirmation.step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

    def resume_tenant_erasures(self, now: datetime) -> dict[str, int]:
        """Retry every open tenant deletion whose backoff has passed (daily beat).

        A deployment that cannot erase holds every record untouched — one error
        line, no attempt spent — so the first run after the fix executes them all
        (#1666). A record still inside its backoff is skipped with an info line.
        """
        repo = self._require_tenant_erasure_repo()
        stale_before = now - timedelta(hours=TenantErasureEngine.STALE_AFTER_HOURS)
        # #2123 — a scheduled deletion is due once its grace has ended.
        candidates = repo.list_due(stale_before_iso=stale_before.isoformat(), scheduled_due_before_iso=now.isoformat())
        result = {"candidates": len(candidates), "completed": 0, "open": 0, "deferred": 0, "held": 0, "escalated": 0}
        if not candidates:
            return result
        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            result["held"] = len(candidates)
            logger.error("tenant_erasure.retry_not_configured", reason=configuration_error, held=len(candidates))
            return result
        for record in candidates:
            if not self._is_due(record, now):
                result["deferred"] += 1
                continue
            if record.next_attempt_at is not None and record.next_attempt_at > now + _TENANT_ERASURE_RETRY_SLACK:
                result["deferred"] += 1
                logger.info(
                    "tenant_erasure.deferred",
                    record_key=log_tenant_record_key(record.key),
                    attempt_count=record.attempt_count,
                    next_attempt_at=record.next_attempt_at.isoformat(),
                )
                continue
            if self._is_unclaimed_account_erasure(record):
                # REQ-025 AK-IE-07 (#1825 SEC-003): an account erasure stopped
                # between inserting this record and its second membership read.
                # Its own retry (the open erasure request) re-reads before it
                # claims; the beat must not deactivate a late joiner blind.
                result["deferred"] += 1
                logger.info("tenant_erasure.awaiting_account_erasure", record_key=log_tenant_record_key(record.key))
                continue
            claimed = self._claim_tenant_erasure(record.key or "", now)
            if claimed is None:
                continue
            self._mark_tenant_erasing(claimed.tenant_key)
            self._membership_repo.deactivate_all_for_tenant(claimed.tenant_key)
            finished = self._run_tenant_erasure(claimed, now, raise_on_failure=False)
            result["completed" if finished.status == "completed" else "open"] += 1
            if finished.status != "completed" and finished.attempt_count >= TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS:
                result["escalated"] += 1
        logger.info("tenant_erasure.retry_completed", **result)
        return result

    # --- Organisations of an erased account (REQ-025 §3.1.3, MT-038 #2134) ---

    def _organisations_of(self, user_key: str) -> list[tuple[Tenant, Membership]]:
        """The organisations *user_key* holds an active membership in whose lifecycle is still open.

        Personal tenants go with the account (#1788) and the platform tenant is never
        settled here (its leads are the platform admins, REQ-049 §2.5); a tenant whose
        deletion is already scheduled, running or orphaned needs no second decision.
        """
        found: list[tuple[Tenant, Membership]] = []
        for membership in self._membership_repo.list_by_user(user_key):
            if not membership.is_active:
                continue
            tenant = self._tenant_repo.get_by_key(membership.tenant_key)
            if (
                tenant is None
                or tenant.tenant_type != TenantType.ORGANIZATION
                or tenant.is_platform
                or tenant.status not in _TOGGLEABLE_STATUSES
            ):
                continue
            found.append((tenant, membership))
        return found

    def _remaining_members(self, tenant_key: str, leaving_user_key: str) -> list[Membership]:
        return [
            member
            for member in self._membership_repo.active_memberships_of(tenant_key=tenant_key)
            if member.user_key != leaving_user_key
        ]

    def organisation_erasure_preview(self, user_key: str) -> list[OrganisationErasurePreview]:
        """The organisations an erasure of *user_key* would change, before it is confirmed (#2134).

        Read-only and caller-scoped (the route passes the authenticated account). Names
        the organisation and the outcome — never who takes over or who remains.
        """
        preview: list[OrganisationErasurePreview] = []
        for tenant, membership in self._organisations_of(user_key):
            outcome, _heir = self._membership_engine.departure_settlement(
                membership, self._remaining_members(tenant.key or "", user_key)
            )
            if outcome != "unaffected":
                preview.append(OrganisationErasurePreview(name=tenant.name, outcome=outcome))
        return preview

    def settle_organisations_of_erased_account(
        self, user_key: str, *, now: datetime | None = None
    ) -> list[OrganisationSettlement]:
        """Keep every organisation of an erased account administrable, or schedule it for deletion (#2134).

        Called by the account erasure before its ArangoDB plan removes the subject's
        memberships — the cascade that bypassed INV-1 (MT-038). Per organisation
        (:meth:`MembershipEngine.departure_settlement`):

        * ``management_passes_to_lead`` — the longest-serving remaining ``lead``
          receives the ``management`` scope (security audit ``via=account_erasure``)
          and every remaining member is told;
        * ``orphaned`` — nobody left who can administer it: the tenant becomes
          ``orphaned`` and its deletion is scheduled with the grace of #2123
          (origin ``orphaned_organisation``); the remaining members and the platform
          admins are told;
        * ``unaffected`` — another ``management`` holder remains.

        Idempotent: a retry finds the heir holding ``management`` (unaffected) or the
        tenant already ``orphaned`` (skipped). Raises what a failed write raises — the
        account erasure is retried as a whole.
        """
        now = now or datetime.now(UTC)
        settled: list[OrganisationSettlement] = []
        for tenant, membership in self._organisations_of(user_key):
            tenant_key = tenant.key or ""
            remaining = self._remaining_members(tenant_key, user_key)
            outcome, heir = self._membership_engine.departure_settlement(membership, remaining)
            if outcome == "management_passes_to_lead" and heir is not None:
                self._hand_management_to(heir, tenant, subject_user_key=user_key, remaining=remaining)
            elif outcome == "orphaned":
                self._orphan_organisation(tenant, subject_user_key=user_key, now=now)
            settled.append(OrganisationSettlement(tenant_key=tenant_key, outcome=outcome))
        if settled:
            logger.info(
                "account_erasure.organisations_settled",
                subject=log_subject(user_key),
                outcomes=[item.outcome for item in settled],
            )
        return settled

    def _hand_management_to(
        self, heir: Membership, tenant: Tenant, *, subject_user_key: str, remaining: list[Membership]
    ) -> None:
        """Give *heir* the ``management`` scope the erased account held last (INV-1, #2134); audited and told."""
        # REQ-049 INV-2: duplicate-free, in declaration order — the order the model normalises to.
        scopes = [scope for scope in AdminScope if scope in heir.admin_scopes or scope == AdminScope.MANAGEMENT]
        result = self._membership_repo.update_fields(heir.key or "", {"admin_scopes": scopes})
        if not result:
            raise NotFoundError("Membership", heir.key or "")
        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_SCOPES_CHANGED,
            via=SecurityAuditVia.ACCOUNT_ERASURE,
            actor_user_key=subject_user_key,
            target_user_key=heir.user_key,
            tenant_key=tenant.key or "",
            membership=result,
            old_scopes=heir.admin_scopes,
        )
        logger.info(
            "account_erasure.management_handed_over", tenant=log_tenant(tenant.key), heir=log_subject(heir.user_key)
        )
        name = html.escape(tenant.name)
        body = (
            "<h2>The management of your organisation has passed on</h2>"
            f"<p>The last person with the management right in <strong>{name}</strong> has deleted their account. "
            "The longest-serving lead of the organisation now holds the management right, "
            "so members can still be invited and the organisation administered.</p>"
            "<p>Nothing else changes for you.</p>"
        )
        self._mail_accounts(
            [member.user_key for member in remaining],
            subject="Kamerplanter — the management of your organisation has passed on",
            body=body,
            event="account_erasure.handover_notice",
        )

    def _orphan_organisation(self, tenant: Tenant, *, subject_user_key: str, now: datetime) -> None:
        """Schedule the deletion of an organisation nobody can administer any more (#2134, #2123 grace)."""
        tenant_key = tenant.key or ""
        scheduled_for = now + self._tenant_erasure_grace
        record_key = TenantErasureEngine.record_key(tenant_key)
        repo = self._require_tenant_erasure_repo()
        if repo.get(record_key) is None:
            try:
                repo.create_with_key(
                    TenantErasureRecord(
                        tenant_key=tenant_key,
                        tenant_type=str(tenant.tenant_type),
                        origin="orphaned_organisation",
                        requested_by_subject=log_subject(subject_user_key),
                        step_up="account_erasure_no_interactive_step_up",
                        slug_digest=self._tenant_slug_digest(tenant.slug),
                        status="scheduled",
                        requested_at=now,
                        scheduled_for=scheduled_for,
                    ),
                    record_key,
                )
            except (DuplicateError, WriteConflictError) as exc:
                raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION) from exc
        self._schedule_tenant_erasure(tenant, scheduled_for, requester_key=subject_user_key, orphaned=True)
        due = html.escape(scheduled_for.strftime("%Y-%m-%d"))
        name = html.escape(tenant.name)
        body = (
            "<h2>An organisation was orphaned by an account deletion</h2>"
            f"<p>After an account deletion nobody can administer the organisation <strong>{name}</strong> any more. "
            f"It is shown as orphaned in the admin area and will be deleted with all its data on {due} (UTC).</p>"
        )
        platform_leads = [
            member.user_key
            for member in self._membership_repo.active_memberships_of(tenant_key=_PLATFORM_TENANT_KEY)
            if member.role == TenantRole.LEAD
        ]
        self._mail_accounts(
            platform_leads,
            subject="Kamerplanter — an organisation was orphaned",
            body=body,
            event="account_erasure.orphan_notice",
        )

    def _mail_accounts(self, user_keys: list[str], *, subject: str, body: str, event: str) -> int:
        """Mail each account once; best effort — a failing mailbox never stops the erasure (#2134)."""
        if self._email_service is None or self._user_repo is None:
            logger.warning(f"{event}_not_sent", reason="no_mailer")
            return 0
        sent = 0
        for user_key in dict.fromkeys(user_keys):
            try:
                account = self._user_repo.get_by_key(user_key)
                if account is None or not account.email:
                    continue
                self._email_service.send_notification_email(to_email=account.email, subject=subject, html_body=body)
            except Exception as exc:  # noqa: BLE001 - one mailbox must not stop the others
                logger.warning(f"{event}_failed", member=log_subject(user_key), error_type=type(exc).__name__)
                continue
            sent += 1
        logger.info(event, notified=sent)
        return sent

    # --- Personal tenants of an erased account (REQ-025 Art. 17, #1788) ---

    def tenant_erasure_configuration_error(self) -> str | None:
        """Why this deployment cannot erase a tenant, or ``None`` (#1788).

        The account erasure holds on it before touching anything: it erases the
        subject's personal tenant through the tenant-erasure inventory, so a deployment
        that cannot erase a tenant cannot finish an account erasure either.
        """
        return self._tenant_erasure_configuration_error()

    def personal_tenant_keys_of(self, user_key: str) -> list[str]:
        """Every ``PERSONAL`` tenant *user_key* owns — normally the one of registration.

        By owner and type, like :meth:`get_personal_tenant`, but all of them, not
        the newest: an account erasure must not leave a second one behind.
        """
        return self._tenant_repo.personal_tenant_keys_by_owner(user_key)

    def revoke_invitations_into_personal_tenants_of(self, user_key: str) -> int:
        """Revoke every pending invitation into every personal tenant of *user_key* (REQ-025 AK-IE-06).

        Called when an erasure of the account is **requested** — by
        :meth:`PrivacyService.request_erasure` and
        :meth:`PrivacyService.erase_account_now` alike — and once more by
        :meth:`erase_personal_tenant_of` right before the membership decision.
        Until #1825 an invitation (a link invitation is bound to no address)
        stayed acceptable for the whole R-01 grace: whoever held the token
        could join, keep the tenant from being erased and read the subject's
        garden.

        E-mail and link invitations alike, ``tenant_type: personal`` only —
        invitations into an organisation the subject owns are not the
        subject's personal data decision. A revoked invitation is refused by
        :meth:`accept_invitation` (``Invitation is no longer pending``).
        Idempotent; returns how many invitations were revoked.
        """
        revoked = sum(
            self._invitation_repo.revoke_pending_for_tenant(tenant_key)
            for tenant_key in self._tenant_repo.personal_tenant_keys_by_owner(user_key)
        )
        if revoked:
            logger.info(
                "tenant_erasure.personal_tenant_invitations_revoked", subject=log_subject(user_key), revoked=revoked
            )
        return revoked

    def erase_personal_tenant_of(
        self,
        user_key: str,
        tenant_key: str,
        *,
        now: datetime | None = None,
        requested_at: datetime | None = None,
    ) -> PersonalTenantErasure:
        """Erase *tenant_key*, a personal tenant of the erased account *user_key*, unless someone else uses it.

        The account erasure calls this for every personal tenant of the subject
        before its own ArangoDB plan runs (#1788). Until #1788 that plan only
        replaced the owner reference and renamed the tenant, and the tenant's
        sites, plants, diary, tasks … outlived the account — the subject's own
        data, kept without purpose (Art. 5(1)(e), Art. 17).

        * A deletion already ``completed`` for it → ``erased`` (a retry after the
          tenant went, or a deletion someone else finished).
        * Neither tenant nor deletion record → ``absent``.
        * No deletion open yet → the tenant goes, **whoever else is a member**
          (erasure together, REQ-025 §3.1.3 / NFR-011 AK-PT-03, #1824): the
          members are notified when the erasure is requested
          (:meth:`PrivacyService.request_erasure`), not here. The one exception
          is a member who joined *after* the first read — see below —
          → ``retained_late_joiner``: the tenant is kept and only the owner
          reference is removed (REQ-025 AK-IE-07).
        * Otherwise — nobody joined late, or a deletion of it
          is already running (its memberships are frozen then) — the tenant-erasure
          inventory runs with origin ``account_erasure``
          (:meth:`_erase_tenant_for_account_erasure`): same inventory, same
          persisted record, same retry as :meth:`delete_tenant`.

        The membership is read **twice** (REQ-025 AK-IE-07, #1825 SEC-003): once
        before the deletion record is inserted — who is a member *now* — and
        again right after; with ``requested_at`` — when the account erasure was
        asked for — a member whose membership began after it also counts as late,
        because the notice (REQ-025 §3.1.3) went to those who were members at
        that moment. The record is the freeze :meth:`_refuse_while_erasing`
        keys on, so a join that slipped between the first read and the insert is
        seen by the second as someone the first did not list. Such a tenant is
        kept, the record withdrawn — and the members read once more after the
        withdrawal, so a joiner the freeze took back meanwhile does not keep it
        for nobody (:meth:`_decide_retention_under_freeze`, #1924); before #1825
        the joiner was silently deactivated and the tenant erased. A record an earlier attempt left
        unclaimed has no first read to compare with; there a member whose
        membership began at or after the record's ``requested_at`` — or whose
        start is not recorded — counts as late. The decision is
        :meth:`_personal_tenant_retention`, the one place that decides whether
        a membership keeps the tenant.

        Raises what a failed tenant deletion raises (the record stays open and
        the daily tenant beat retries it too), :class:`TenantErasureIncompleteError`
        when it did not complete, and :class:`ValidationError` when the tenant is
        no longer a personal tenant of *user_key* — a state no write path
        produces, so it stops the account erasure instead of erasing a tenant
        that is not the subject's.
        """
        record_key = TenantErasureEngine.record_key(tenant_key)
        record = self._require_tenant_erasure_repo().get(record_key)
        if record is not None and record.status == "completed":
            return PersonalTenantErasure(tenant_key=tenant_key, outcome="erased", tenant_erasure_record_key=record_key)
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if tenant is None and record is None:
            return PersonalTenantErasure(tenant_key=tenant_key, outcome="absent")
        if (
            record is None
            and tenant is not None
            and tenant.tenant_type == TenantType.PERSONAL
            and tenant.owner_user_key == ANONYMIZED_MARKER
        ):
            # #1788 code review — a recorded key whose tenant the account plan
            # already handed over (owner replaced) was retained on an earlier
            # attempt; a retry must not fail on it and block the Art. 17 duty.
            return PersonalTenantErasure(
                tenant_key=tenant_key,
                outcome="retained_late_joiner",
                reason="Kept on an earlier attempt of this erasure; its owner reference is already removed.",
            )
        if tenant is not None and (tenant.owner_user_key != user_key or tenant.tenant_type != TenantType.PERSONAL):
            raise ValidationError("The tenant recorded for this account erasure is not the subject's personal tenant.")
        now = now or datetime.now(UTC)
        # A record no run ever claimed was inserted by an attempt that stopped
        # before its re-check (or before its claim): nothing is deactivated yet,
        # so the membership still says who uses the tenant.
        never_started = record is not None and self._is_unclaimed_account_erasure(record)
        known_members: frozenset[str] | None = None
        if record is None:
            # AK-IE-06 backstop — revoked at request time already; an invitation
            # issued since (or a request-time revocation that failed) goes here,
            # before the membership is read.
            self._invitation_repo.revoke_pending_for_tenant(tenant_key)
            # #1824 — the first read no longer decides anything: whoever is a
            # member now goes with the tenant. It only records who they are, so
            # the read after the freeze can tell a late joiner from them.
            known_members = self._other_active_members(tenant_key, user_key)
            self._open_account_erasure_record(tenant_key, tenant, subject_user_key=user_key, now=now)
        if record is None or never_started:
            retained = self._decide_retention_under_freeze(
                tenant_key,
                tenant,
                user_key,
                known_members=known_members,
                frozen_at=record.requested_at if record is not None else None,
                requested_at=requested_at,
                now=now,
            )
            if retained is not None:
                return retained
        finished = self._erase_tenant_for_account_erasure(tenant_key, tenant, now=now)
        if finished.status != "completed":
            raise TenantErasureIncompleteError(list(finished.unreached) or [TenantErasureEngine.TENANT_COLLECTION])
        return PersonalTenantErasure(tenant_key=tenant_key, outcome="erased", tenant_erasure_record_key=record_key)

    #: How often the retention decision re-freezes the tenant after a joiner it
    #: counted was taken back by the freeze (see :meth:`_decide_retention_under_freeze`).
    _RETENTION_ROUNDS = 3

    def _decide_retention_under_freeze(
        self,
        tenant_key: str,
        tenant: Tenant | None,
        subject_user_key: str,
        *,
        known_members: frozenset[str] | None,
        frozen_at: datetime | None,
        requested_at: datetime | None,
        now: datetime,
    ) -> PersonalTenantErasure | None:
        """The retained outcome — or ``None`` when the tenant is to be erased — with the freeze in place (#1924).

        AK-IE-07 — the record is in place, so every later join is refused or
        rolls itself back (:meth:`_create_membership_unless_erasing`); whoever
        is an active member now and was not in the first read joined late.

        Two decisions meet on a join that landed between the freeze and the
        read below: this one counts the joiner and keeps the tenant, the joiner's
        own re-check finds the freeze and takes the membership back. Before #1924
        both could fire for the same joiner and the tenant stayed with nobody in
        it. The record's withdrawal is therefore **part of the decision**, not
        what follows it: the record is withdrawn first, and the members are read
        again. The joiner's rollback is atomic against the withdrawal
        (:meth:`IMembershipRepository.delete_while_tenant_frozen`), so a joiner
        counted here is one the rollback can no longer take — it either committed
        before the withdrawal and the re-read does not list it, or it finds no
        record and the membership stands. A re-read that lists nobody means the
        joiner was taken back: the tenant is frozen again and the decision is
        repeated, at most :attr:`_RETENTION_ROUNDS` times; then the run stops
        with a write conflict and the daily retry picks the open record up.
        """
        erasure_repo = self._require_tenant_erasure_repo()
        record_key = TenantErasureEngine.record_key(tenant_key)

        def late_member() -> PersonalTenantErasure | None:
            return self._personal_tenant_retention(
                tenant_key,
                subject_user_key,
                known_members=known_members,
                frozen_at=frozen_at,
                requested_at=requested_at,
            )

        for _round in range(self._RETENTION_ROUNDS):
            if late_member() is None:
                return None
            if not erasure_repo.delete_unclaimed(record_key):
                # A run claimed the record in between; it decides, and the
                # account erasure is retried against what it leaves.
                raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION)
            retained = late_member()
            if retained is not None:
                return retained
            # The joiner this decision counted was taken back by the freeze it
            # raced with: nobody keeps the tenant — freeze it again and decide anew.
            self._open_account_erasure_record(tenant_key, tenant, subject_user_key=subject_user_key, now=now)
        raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION)

    @staticmethod
    def _is_unclaimed_account_erasure(record: TenantErasureRecord) -> bool:
        """Whether *record* was opened by an account erasure and no run has claimed it yet."""
        return (
            record.origin == "account_erasure"
            and record.status == "in_progress"
            and record.last_attempt_at is None
            and record.attempt_count == 0
        )

    def _other_active_members(self, tenant_key: str, subject_user_key: str) -> frozenset[str]:
        """The active accounts other than the subject that use *tenant_key* (#1788)."""
        return frozenset(
            key
            for key in self._membership_repo.active_member_user_keys(tenant_key=tenant_key)
            if key != subject_user_key
        )

    def _personal_tenant_retention(
        self,
        tenant_key: str,
        subject_user_key: str,
        *,
        known_members: frozenset[str] | None,
        frozen_at: datetime | None,
        requested_at: datetime | None = None,
    ) -> PersonalTenantErasure | None:
        """The retained outcome when a *late* member keeps the subject's personal tenant, else ``None``.

        Erasure together (#1824): another active member no longer keeps the
        tenant — only one who joined after the erasure froze it does
        (REQ-025 AK-IE-07). Called with the freeze in place.

        * ``known_members`` — the members the read before the freeze listed:
          whoever is active now and is not among them joined late.
        * ``None`` — a retried record no run claimed has no such read; a member
          is late when the membership began at or after ``frozen_at`` (the
          record's ``requested_at``). A start that is not recorded does not make
          a member late: every production path stamps ``joined_at``, so only a
          membership from before the field existed (seeds) lacks it.
        * ``requested_at`` — when the **account erasure** was requested. Whoever
          joined after it was not among the members the notice went to (an
          invitation created during the grace, an administrator adding a
          member) and is late whichever read lists them.

        """
        current = self._other_active_members(tenant_key, subject_user_key)
        joined = (
            self._membership_repo.active_member_joined_at(tenant_key=tenant_key)
            if known_members is None or requested_at is not None
            else {}
        )
        late: set[str] = set()
        if known_members is not None:
            late |= current - known_members
        else:
            cutoff = ensure_aware_utc(frozen_at)
            for key in current:
                began = ensure_aware_utc(joined.get(key))
                if cutoff is None or (began is not None and began >= cutoff):
                    late.add(key)
        if requested_at is not None:
            asked = ensure_aware_utc(requested_at)
            for key in current:
                began = ensure_aware_utc(joined.get(key))
                if began is not None and asked is not None and began > asked:
                    late.add(key)
        if not late:
            return None
        # #1788 review GDPR-05 — no tenant key beside the subject digest: the key
        # is on the pseudonymised retention rows, and joining a log line to them
        # is what the salted ``log_subject`` prevents.
        logger.info(
            "tenant_erasure.personal_tenant_retained",
            subject=log_subject(subject_user_key),
            late_members=len(late),
        )
        reason = (
            f"{len(late)} member(s) joined this tenant after its deletion was requested "
            "(REQ-025 AK-IE-07); it is kept for them and only the owner reference is removed."
        )
        return PersonalTenantErasure(tenant_key=tenant_key, outcome="retained_late_joiner", reason=reason)

    def other_active_members_of_personal_tenants_of(self, user_key: str) -> list[str]:
        """The distinct accounts, other than *user_key*, that use one of its personal tenants (#1824).

        Who has to be told before an erasure takes the tenant with it. An
        account whose own erasure is pending is not among them (it is already
        inactive, #1788 review GDPR-01).
        """
        members: dict[str, None] = {}
        for tenant_key in self._tenant_repo.personal_tenant_keys_by_owner(user_key):
            for key in sorted(self._other_active_members(tenant_key, user_key)):
                members.setdefault(key)
        return list(members)

    def personal_tenant_erasure_preview(self, user_key: str) -> list[PersonalTenantErasurePreview]:
        """What an account erasure would take with it, per personal tenant, before it is confirmed (AK-FK-06, #1824).

        The subject's own tenant name and a *count* of the others — nothing
        about who they are. Read-only and caller-scoped: the keys are those the
        subject owns.
        """
        preview: list[PersonalTenantErasurePreview] = []
        for tenant_key in self._tenant_repo.personal_tenant_keys_by_owner(user_key):
            tenant = self._tenant_repo.get_by_key(tenant_key)
            if tenant is None:
                continue
            preview.append(
                PersonalTenantErasurePreview(
                    name=tenant.name, other_member_count=len(self._other_active_members(tenant_key, user_key))
                )
            )
        return preview

    def _guard_account_erasure_of_tenant(self, tenant: Tenant | None) -> None:
        """Refuse before anything is written: a tenant that cannot be deleted, a deployment that cannot erase."""
        if tenant is not None and (tenant.is_platform or self._light_mode):
            raise ForbiddenError("This tenant cannot be deleted.")
        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            raise FeatureNotConfiguredError("tenant_deletion", configuration_error)

    def _open_account_erasure_record(
        self, tenant_key: str, tenant: Tenant | None, *, subject_user_key: str, now: datetime
    ) -> None:
        """Insert the one-per-tenant deletion record — the membership freeze — for an account erasure."""
        self._guard_account_erasure_of_tenant(tenant)
        try:
            self._require_tenant_erasure_repo().create_with_key(
                TenantErasureRecord(
                    tenant_key=tenant_key,
                    tenant_type=str(tenant.tenant_type) if tenant is not None else "unknown",
                    origin="account_erasure",
                    # #1791 provenance fields: the erased account as the salted
                    # log reference (never its key), and an explicit statement
                    # that no interactive step-up belongs to this deletion.
                    requested_by_subject=log_subject(subject_user_key),
                    step_up="account_erasure_no_interactive_step_up",
                    slug_digest=self._tenant_slug_digest(tenant.slug) if tenant is not None else None,
                    requested_at=now,
                ),
                TenantErasureEngine.record_key(tenant_key),
            )
        except (DuplicateError, WriteConflictError) as exc:
            raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION) from exc

    def _erase_tenant_for_account_erasure(
        self,
        tenant_key: str,
        tenant: Tenant | None,
        *,
        now: datetime,
    ) -> TenantErasureRecord:
        """Claim and run a deletion the account erasure decided and recorded (#1788).

        The record exists by now — inserted by :meth:`_open_account_erasure_record`
        and confirmed by the second membership read, or left open by an earlier
        attempt.

        Not :meth:`delete_tenant` itself: that is the entry of a *person* deleting
        a tenant, and #1791 puts the requester's authorisation and step-up there.
        Here nobody is asking — the account erasure (itself authorised by the
        subject's re-authenticated request, a platform admin or the unverified
        cleanup) decided the tenant goes. Everything that makes the deletion
        provable is the same: the configuration hold, the one-per-tenant record
        (``origin: account_erasure``), the atomic claim, the membership freeze
        and :meth:`_run_tenant_erasure` with its residue check and backoff; the
        daily :meth:`resume_tenant_erasures` retries the record like any other.
        """
        self._guard_account_erasure_of_tenant(tenant)
        record_key = TenantErasureEngine.record_key(tenant_key)
        claimed = self._claim_tenant_erasure(record_key, now)
        if claimed is None:
            raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION)
        # #2123 — a deletion scheduled by the tenant's management does not wait out its grace
        # here: the account erasure decided this personal tenant goes with its owner.
        self._mark_tenant_erasing(tenant_key)
        self._membership_repo.deactivate_all_for_tenant(tenant_key)
        return self._run_tenant_erasure(claimed, now, raise_on_failure=True)

    def _refuse_while_erasing(self, tenant_key: str) -> None:
        """No new membership in a tenant whose deletion is open (#1769 review SEC-006).

        The deletion deactivates every membership before it runs; a membership
        created afterwards would grant access to a tenant being erased until the
        transaction commits.
        """
        if self._tenant_erasure_repo is None:
            return
        record = self._tenant_erasure_repo.get(TenantErasureEngine.record_key(tenant_key))
        if record is not None and record.status != "completed":
            raise ForbiddenError("This tenant is being deleted.")

    def _refuse_invitation_while_owner_erasing(self, *, tenant_key: str) -> None:
        """No invitation into a personal tenant whose owner has an open erasure request (REQ-025 AK-IE-06, #1924).

        AK-IE-06 revokes the invitations that exist when the erasure is
        requested; this is the other half — one created *during* the grace (a
        member with the ``MANAGEMENT`` scope can still create one) or accepted
        in it would let somebody join the subject's garden after the subject
        asked for it to go. Every way in — both invitation types, creation and
        acceptance — asks here, so the predicate is written once. Only a
        ``PERSONAL`` tenant is the subject's own data decision; an organisation
        the subject owns keeps inviting. The refusal does not say why: whoever holds
        a token is not one of the members the erasure notice went to.
        """
        if self._erasure_repo is None:
            return
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if tenant is None or tenant.tenant_type != TenantType.PERSONAL:
            return
        if self._erasure_repo.find_active_for_user(tenant.owner_user_key) is not None:
            raise ForbiddenError("No new members can be invited into this tenant.")

    def _create_membership_unless_erasing(self, membership: Membership) -> Membership:
        """Insert a membership into an existing tenant, and take it back if the tenant froze meanwhile.

        REQ-025 AK-IE-07 (#1825 SEC-003 b). The caller's
        :meth:`_refuse_while_erasing` and this insert are two writes: a deletion
        record inserted between them froze the tenant while the membership was
        on its way in. Checked again once the membership exists
        (:meth:`_settle_join_against_freeze`), so no active membership stays in
        a tenant that is being erased — the counterpart of the second membership
        read in :meth:`erase_personal_tenant_of`. Every path that joins an
        account to an existing tenant goes through here.

        **The member limit (REQ-024 AK-65, #2133)** is decided here too, for the same
        reason: it is the one door every join passes (the class guards in
        ``tests/unit/guards/`` hold that). Counted before the insert and again after
        it - two concurrent joins can both pass the first count, and the one that
        finds the tenant over its limit afterwards takes itself back
        (:meth:`_settle_join_against_member_limit`).
        """
        limit = self._refuse_beyond_member_limit(membership.tenant_key)
        created = self._membership_repo.create(membership)
        self._settle_join_against_freeze(created)
        self._settle_join_against_member_limit(created, limit)
        return created

    def _member_limit(self, tenant: Tenant) -> int:
        """The effective member limit: the tenant's own, never above the platform ceiling (REQ-024 AK-65)."""
        return min(tenant.max_members, self._max_members_ceiling)

    def _refuse_limit_above_ceiling(self, max_members: int) -> None:
        """422 for a ``max_members`` above the platform ceiling (REQ-024 AK-65, #2133)."""
        if max_members > self._max_members_ceiling:
            raise ValidationError(
                f"max_members may not exceed the platform ceiling of {self._max_members_ceiling}.",
                details=[
                    {
                        "field": "max_members",
                        "reason": f"At most {self._max_members_ceiling}.",
                        "code": "max_members_above_ceiling",
                    }
                ],
            )

    def _refuse_beyond_member_limit(self, tenant_key: str) -> int:
        """422 ``MEMBER_LIMIT_REACHED`` when the tenant's active memberships reached its limit; else the limit.

        REQ-024 AK-64 (#2133). Counts *active* memberships against the effective limit
        (:meth:`_member_limit`). Applies to a new membership only: a tenant that already
        holds more members than its limit - written before the limit was enforced, or
        after it was lowered - keeps all of them and refuses the next join.
        """
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if tenant is None:
            raise NotFoundError("Tenant", tenant_key)
        limit = self._member_limit(tenant)
        if self._membership_repo.count_active_members(tenant_key=tenant_key) >= limit:
            logger.info("member_limit_reached", tenant=log_tenant(tenant_key), limit=limit)
            raise MemberLimitReachedError(limit)
        return limit

    def _settle_join_against_member_limit(self, created: Membership, limit: int) -> None:
        """Take a join back that a concurrent join pushed over the limit after the first count (#2133).

        The count before the insert and the insert are two statements: two joins can both
        see one free seat. Re-counted once the membership exists, an overshoot is undone
        and refused - both racing joins may be refused then, never both kept.
        """
        if self._membership_repo.count_active_members(tenant_key=created.tenant_key) <= limit:
            return
        if created.key:
            self._membership_repo.delete(created.key)
        logger.info("member_limit_join_taken_back", tenant=log_tenant(created.tenant_key), limit=limit)
        raise MemberLimitReachedError(limit)

    def _settle_join_against_freeze(self, created: Membership) -> None:
        """The re-check of a join after its insert: raises ``ForbiddenError`` when the membership was taken back.

        The take-back is atomic against the erasure's withdrawal of the record
        (:meth:`IMembershipRepository.delete_while_tenant_frozen`, #1924): a
        membership the erasure counted as a late joiner and kept the tenant for
        is not removed after the fact, and one removed first is not counted. A
        withdrawn record means the erasure decided to keep the tenant — the
        membership stands.
        """
        try:
            self._refuse_while_erasing(created.tenant_key)
        except ForbiddenError:
            if not created.key:
                raise
            try:
                taken_back = self._membership_repo.delete_while_tenant_frozen(created.key, created.tenant_key)
            except WriteConflictError:
                # The record kept conflicting. Refusing a join is always safe
                # for the subject's erasure; keeping an unchecked one is not.
                self._membership_repo.delete(created.key)
                raise
            if taken_back:
                raise

    def _require_tenant_erasure_repo(self) -> ITenantErasureRepository:
        if self._tenant_erasure_repo is None:
            raise FeatureNotConfiguredError("tenant_deletion", "No tenant-erasure record store is wired.")
        return self._tenant_erasure_repo

    def _claim_tenant_erasure(self, record_key: str, now: datetime) -> TenantErasureRecord | None:
        stale_before = now - timedelta(hours=TenantErasureEngine.STALE_AFTER_HOURS)
        return self._require_tenant_erasure_repo().claim_for_run(
            record_key, now_iso=now.isoformat(), stale_before_iso=stale_before.isoformat()
        )

    def _tenant_erasure_wiring_error(self) -> str | None:
        """Executor, stores and salts — the process-independent part of the tenant-erasure configuration."""
        if self._tenant_erasure_executor is None or self._tenant_erasure_repo is None:
            return "No tenant-erasure executor or record store is wired on this deployment."
        if self._observation_repo is None:
            return "No sensor-reading store is wired, so the tenant's time-series data cannot be erased."
        try:
            ErasureEngine.compute_tombstone_hash("configuration-probe", self._tombstone_salt)
        except ValueError:
            return "Set ERASURE_TOMBSTONE_SALT to a secret of at least 32 characters."
        # #1812 review SEC-001: the record's ``requested_by_subject`` (and the
        # redacted error texts it keeps) are log pseudonyms. Without the log salt
        # they would be persisted as the constant ``anon_unavailable`` — a proof
        # that no longer says who asked for the erasure. Refused like the
        # tombstone salt, before anything changes (the start gate does not run
        # with DEBUG=true).
        if log_subject("configuration-probe") == UNAVAILABLE_LOG_SUBJECT:
            return "Set LOG_PSEUDONYM_SALT to a secret of at least 32 characters."
        return None

    def tenant_erasure_wiring_error(self) -> str | None:
        """The deployment-wide half of :meth:`tenant_erasure_configuration_error` (#1843).

        Executor, record store, sensor store and salts — the same in every
        process. The derived-store checks (reference index, pest prototypes)
        depend on the process that runs the erasure and are left to it: a
        self-service request filed in the API process is executed by the
        worker's beat, which holds it if *its* process cannot reach them.
        """
        return self._tenant_erasure_wiring_error()

    def _tenant_erasure_configuration_error(self) -> str | None:
        """Why this deployment cannot erase a tenant, or ``None`` when it can (#1666 shape).

        Checked before anything changes: a configuration fault is not a property
        of one tenant and would fail every attempt identically.
        """
        wiring_error = self._tenant_erasure_wiring_error()
        if wiring_error is not None:
            return wiring_error
        if self._reference_index_store is not None:
            reference_error = self._reference_index_store.configuration_error()
            if reference_error is not None:
                return reference_error
        if self._pest_image_repo is not None and self._pest_prototype_store is None:
            return "No pest-prototype store is wired, so contributed pest-recognition prototypes cannot be erased."
        if self._pest_prototype_store is not None:
            return self._pest_prototype_store.configuration_error()
        return None

    def _run_tenant_erasure(
        self, record: TenantErasureRecord, now: datetime, *, raise_on_failure: bool
    ) -> TenantErasureRecord:
        """External phase, then the ArangoDB inventory; the record says what happened.

        *now* is the instant the caller's claim stamped on the record
        (``last_attempt_at``): it is the claim's identity, and every heartbeat of
        this run is conditional on it still standing (#1792). The heartbeat is
        refreshed after the external phase, after every ArangoDB batch and before
        the time-series purge, so a long run is not claimed a second time while a
        crashed one — whose heartbeat stops — is.
        """
        record_key = record.key or TenantErasureEngine.record_key(record.tenant_key)
        repo = self._require_tenant_erasure_repo()
        executor = self._tenant_erasure_executor
        assert executor is not None  # checked by _tenant_erasure_configuration_error
        salt = self._tombstone_salt
        claimed_at_iso = now.isoformat()
        persisted_parent_keys: dict[str, list[str]] = dict(record.parent_keys)

        def heartbeat(parent_keys: dict[str, list[str]] | None = None) -> None:
            nonlocal persisted_parent_keys
            changed = parent_keys is not None and parent_keys != persisted_parent_keys
            if not repo.heartbeat(
                record_key,
                claimed_at_iso=claimed_at_iso,
                now_iso=datetime.now(UTC).isoformat(),
                parent_keys=parent_keys if changed else None,
            ):
                raise TenantErasureClaimLostError
            if changed and parent_keys is not None:
                persisted_parent_keys = {name: list(keys) for name, keys in parent_keys.items()}

        def conclude(fields: dict[str, object]) -> TenantErasureRecord:
            """Write the run's outcome, only while its own claim stands (#1792 review SEC-001)."""
            written = repo.update_fields_while_claimed(record_key, claimed_at_iso=claimed_at_iso, fields=fields)
            if written is None:
                raise TenantErasureClaimLostError
            return written

        try:
            external = self._purge_tenant_storage(record.tenant_key, on_step=heartbeat)
            heartbeat()
            report = executor.run_tenant_erasure(
                self._tenant_erasure_engine.build_plan(record.tenant_key, known_parent_keys=record.parent_keys),
                pseudonymize=lambda user_key: ErasureEngine.compute_tombstone_hash(user_key, salt),
                on_progress=heartbeat,
            )
            heartbeat()
            external.update(self._purge_tenant_readings(record.tenant_key))
        except TenantErasureClaimLostError:
            # The record is another run's now; writing a failure onto it would
            # clobber that run's state. Stop quietly.
            logger.warning("tenant_erasure.claim_lost", record_key=log_tenant_record_key(record_key))
            if raise_on_failure:
                raise
            return record
        except Exception as exc:
            attempt = record.attempt_count + 1
            next_attempt_at = TenantErasureEngine.next_attempt_at(attempt, now)
            logger.error(
                "tenant_erasure.attempt_failed",
                record_key=log_tenant_record_key(record_key),
                attempt=attempt,
                error_type=type(exc).__name__,
                next_attempt_at=next_attempt_at.isoformat(),
            )
            try:
                conclude(
                    {
                        "status": "partially_completed",
                        "attempt_count": attempt,
                        "next_attempt_at": next_attempt_at.isoformat(),
                        "error_message": (
                            f"Attempt {attempt} failed ({type(exc).__name__}); "
                            f"the next one is due after {next_attempt_at.date()}."
                        ),
                        **self._escalation_fields(record, attempt, now),
                    }
                )
            except TenantErasureClaimLostError:
                # The record is another run's now: its state is not ours to overwrite.
                logger.warning("tenant_erasure.claim_lost", record_key=log_tenant_record_key(record_key))
                if raise_on_failure:
                    raise
                return record
            if raise_on_failure:
                raise
            return record.model_copy(update={"status": "partially_completed", "attempt_count": attempt})

        fields: dict[str, object] = {
            **external,
            "outcomes": [outcome.model_dump() for outcome in report.outcomes],
            "edges_removed": report.edges_removed,
            "unreached": list(report.unreached),
            "parent_keys": report.parent_keys,
        }
        if report.unreached:
            attempt = record.attempt_count + 1
            next_attempt_at = TenantErasureEngine.next_attempt_at(attempt, now)
            fields.update(
                {
                    "status": "partially_completed",
                    "attempt_count": attempt,
                    "next_attempt_at": next_attempt_at.isoformat(),
                    "error_message": (
                        f"Still holding the tenant after attempt {attempt}: {', '.join(report.unreached)}."
                    ),
                    **self._escalation_fields(record, attempt, now),
                }
            )
            logger.error(
                "tenant_erasure.unreached",
                record_key=log_tenant_record_key(record_key),
                attempt=attempt,
                unreached=report.unreached,
            )
            try:
                updated = conclude(fields)
            except TenantErasureClaimLostError:
                logger.warning("tenant_erasure.claim_lost", record_key=log_tenant_record_key(record_key))
                if raise_on_failure:
                    raise
                return record
            if raise_on_failure:
                raise TenantErasureIncompleteError(list(report.unreached))
            return updated
        fields.update(
            {
                "status": "completed",
                "completed_at": now.isoformat(),
                "next_attempt_at": None,
                "error_message": None,
            }
        )
        try:
            updated = conclude(fields)
        except TenantErasureClaimLostError:
            logger.warning("tenant_erasure.claim_lost", record_key=log_tenant_record_key(record_key))
            if raise_on_failure:
                raise
            return record
        logger.info(
            "tenant_deleted", tenant=log_tenant(record.tenant_key), record_key=log_tenant_record_key(record_key)
        )
        return updated

    @staticmethod
    def _escalation_fields(record: TenantErasureRecord, attempt: int, now: datetime) -> dict[str, object]:
        """Escalate a deletion that failed ``ESCALATE_AFTER_ATTEMPTS`` times: one alert event per failing attempt.

        #1792 — a deterministic failure (a batch the server refuses every time)
        used to repeat at the backoff, one error line among many. From the n-th
        failed attempt on, each failing run also emits ``tenant_erasure.escalated``
        (the event an operator alert keys on) and the record carries ``escalated_at``
        from the first one. Retries continue at the existing backoff: a person fixes
        the cause, the beat then finishes the deletion.
        """
        if attempt < TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS:
            return {}
        logger.error("tenant_erasure.escalated", record_key=log_tenant_record_key(record.key), attempt=attempt)
        if record.escalated_at is not None:
            return {}
        return {"escalated_at": now.isoformat()}

    def _purge_tenant_readings(self, tenant_key: str) -> dict[str, object]:
        """#1769 review GDPR-001 — the tenant's raw sensor readings (TimescaleDB).

        Runs **after** the ArangoDB transaction committed (#1769 code review): the
        sensors are gone by then, so ingestion — which does not depend on a
        membership and is not stopped by the freeze — has nothing left to write
        readings for. A failure here leaves the record open like any other step,
        and the retry repeats it. A deployment without TimescaleDB wires the null
        repository (0 rows).
        """
        if self._observation_repo is None:
            return {}
        removed = self._observation_repo.delete_by_tenant(tenant_key)
        logger.info("tenant_sensor_readings_deleted", tenant=log_tenant(tenant_key), removed=removed)
        return {"timeseries_rows_removed": removed}

    def _purge_tenant_storage(self, tenant_key: str, on_step: Callable[[], None] | None = None) -> dict[str, object]:
        """NFR-013 §6.1 — the phase outside ArangoDB.

        Steps (with audit logs):
          1. Remove the tenant's user-contributed reference-index vectors
             (inference-service; fails loud, #1753).
          2. Remove the tenant's contributed pest prototypes (#1759).
          3. ``delete_prefix("t/{tenant_key}/")`` — every binary object.

        Any step that raises stops the purge before the ArangoDB inventory runs,
        so the tenant document still exists and the retry starts from the same
        state. Every step is idempotent. Returns what each step reported, for the
        record.

        ``delete_prefix`` / reference-index calls are async; this method is
        invoked from a synchronous request handler, so it bridges via
        ``run_async`` (a loop-isolated runner — safe even if the caller's
        thread already owns an event loop).
        """
        from app.common.async_bridge import run_async

        # SEC-004 — never build a storage prefix from an empty / malformed key.
        # An empty key yields ``t//`` which the local-fs adapter would collapse
        # to ``t`` (matching every tenant) and S3 would pass unchecked to
        # ``list_objects_v2(Prefix=...)`` — both a mass cross-tenant deletion.
        if not tenant_key or not _TENANT_KEY_PATTERN.match(tenant_key):
            raise ValidationError(f"Refusing to purge storage for an invalid tenant key: {tenant_key!r}")

        reported: dict[str, object] = {}
        # REQ-024 / REQ-025 AK-OS-05 — the tenant's contributed reference vectors
        # go first: they live in a separate service, and when that delete fails
        # (ExternalSourceError, HTTP 502) nothing else has been removed yet, so
        # a retry starts from the same state (#1753).
        if self._reference_index_store is not None:
            removed_vectors = run_async(self._reference_index_store.delete_tenant_contributions(tenant_key))
            reported["reference_index_binding"] = self._reference_index_store.binding
            reported["reference_index_removed"] = removed_vectors
            logger.info(
                "tenant_reference_index_cleanup",
                tenant=log_tenant(tenant_key),
                binding=self._reference_index_store.binding,
                removed=removed_vectors,
            )
            if on_step is not None:
                on_step()  # a slow external service must not let the claim go stale (#1792)

        # #1759 — the tenant's contributed pest-recognition prototypes, by tenant
        # rather than by contribution key, so a prototype whose contribution
        # document is already gone is reached too. A missing store is refused by
        # the configuration check before anything changes.
        if self._pest_prototype_store is not None:
            removed_prototypes = run_async(self._pest_prototype_store.delete_tenant_contributions(tenant_key))
            reported["pest_prototype_binding"] = self._pest_prototype_store.binding
            reported["pest_prototypes_removed"] = removed_prototypes
            logger.info(
                "tenant_pest_prototype_cleanup",
                tenant=log_tenant(tenant_key),
                binding=self._pest_prototype_store.binding,
                removed=removed_prototypes,
            )
            if on_step is not None:
                on_step()

        # The ``attachments`` metadata and the ``pest_image_contributions`` link
        # documents are ArangoDB rows of the tenant: the inventory removes them in
        # the transaction below, not this phase (#1769 — one path per row).
        if self._storage_adapter is not None:
            prefix = f"t/{tenant_key}/"
            deleted_objects = run_async(self._storage_adapter.delete_prefix(prefix))
            reported["storage_objects_removed"] = deleted_objects
            logger.info(
                "tenant_storage_prefix_deleted",
                tenant=log_tenant(tenant_key),
                deleted=deleted_objects,
            )
        return reported

    def list_my_tenants(self, user_key: str) -> list[TenantWithRole]:
        memberships = self._membership_repo.list_by_user(user_key)
        result: list[TenantWithRole] = []
        for m in memberships:
            if not m.is_active:
                continue
            tenant = self._tenant_repo.get_by_key(m.tenant_key)
            if tenant and tenant.is_active:
                result.append(
                    TenantWithRole(
                        key=tenant.key,
                        name=tenant.name,
                        slug=tenant.slug,
                        tenant_type=tenant.tenant_type,
                        description=tenant.description,
                        role=m.role,
                        admin_scopes=m.admin_scopes,
                        is_active=tenant.is_active,
                    )
                )
        return result

    # --- Platform-admin catalogue reads (#1019) ---

    def list_all_tenants(self) -> list[Tenant]:
        """Every tenant, newest first — the platform-admin cross-tenant listing.

        Distinct from :meth:`list_my_tenants`, which is scoped to one user's
        memberships. This is a system-context read the platform-admin panel used
        to hand-write as raw AQL in the router (#1019); the per-tenant member
        count is derived by the caller from :meth:`list_members`.
        """
        return self._tenant_repo.list_all()

    def count_tenants(self, *, active_only: bool = False) -> int:
        """Number of tenants; ``active_only`` counts only ``is_active`` ones (#1019)."""
        return self._tenant_repo.count(active_only=active_only)

    def count_memberships(self) -> int:
        """Total number of membership documents (platform-admin statistics, #1019)."""
        return self._membership_repo.count()

    def list_user_memberships(self, user_key: str) -> list[UserMembershipInfo]:
        """A user's memberships, each enriched with its tenant's name and slug.

        The user-perspective read the platform-admin panel needs (#1019). Routed
        through the single :meth:`IMembershipRepository.list_by_user_with_tenant`
        join so ``list_user_memberships``, ``list_all_users`` and the
        ``update_user`` roles block stop each re-deriving it as raw AQL.
        """
        return self._membership_repo.list_by_user_with_tenant(user_key)

    # --- Member Management ---

    def list_members(self, tenant_key: str) -> list[MemberInfo]:
        return self._membership_repo.list_by_tenant(tenant_key)

    # --- Platform-admin membership writes (#1019) ---
    #
    # These are the convergence point for the two admin perspectives — the
    # tenant view (``/admin/platform/tenants/{tk}/members``) and the user view
    # (``/admin/platform/users/{uk}/memberships``) — which previously each
    # hand-wrote the same membership insert / role update / delete with their own
    # edge management, so a fix to one copy missed the other. Authorization is
    # the platform-admin gate on the router (``require_platform_admin``), a
    # different axis from the tenant-scoped ``admin_scopes`` check the
    # tenant-scoped ``change_member_role`` / ``remove_member`` enforce — so these
    # deliberately do not take ``actor_scopes``.

    def admin_add_membership(
        self,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> Membership:
        """Add a user to a tenant on the platform-admin path.

        Single implementation behind both ``POST .../tenants/{tk}/members`` and
        ``POST .../users/{uk}/memberships``. The membership row and its two graph
        edges are created by :meth:`IMembershipRepository.create`, so the edge
        management the two router copies duplicated now lives in one place.

        **Step-up (#2106, REQ-024 AK-59).** Giving an account access to a tenant - in the
        ``platform`` tenant with ``lead``, the platform-admin role - is as consequential as taking
        it away, so it passes the admin's *own* step-up (``requester``: the password, the fresh
        re-authentication or the mailed code; an API key is 403, 429 when locked), bound to the pair
        ``<tenant_key>|<user_key>`` (#1884). It lives here, not on the routes, so both views pass the
        same check; the step-up arguments are keyword-only without a default, so a new caller cannot
        forget them. What cannot succeed is refused first and is not asked for a password: an unknown
        tenant (404), a platform admin adding themselves to the platform tenant (422), a ``lead`` in
        the platform tenant by someone who does not hold it (403, :meth:`_refuse_role_grant`), a tenant
        being erased (403), an account that is already a member (409), a tenant at its member limit (422
        ``MEMBER_LIMIT_REACHED``, #2133). Without a valid step-up nothing is written; the written membership
        is recorded in the security audit (#2111).

        Raises :class:`NotFoundError` when the tenant is unknown and
        :class:`DuplicateError` when the user is already a member. The *user's*
        existence is verified by the router (it needs the user for the response
        anyway), which keeps this method free of a user-repository dependency.
        """
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if not tenant:
            raise NotFoundError("Tenant", tenant_key)

        if tenant.is_platform and user_key == requester.key:
            raise ValidationError("A platform administrator cannot add themselves to the platform tenant.")
        # Behind the route's ``require_platform_admin``, the same rule the tenant-scoped grants meet (#2078):
        # ``lead`` in the platform tenant is handed out only by someone who holds it.
        self._refuse_role_grant(
            tenant_key=tenant_key,
            actor_user_key=requester.key or "",
            target_role=role,
            current_role=None,
            is_own_membership=False,
        )
        self._refuse_while_erasing(tenant_key)
        existing = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
        if existing:
            raise DuplicateError("memberships", "user_key+tenant_key", "already a member")
        # #2133 - a full tenant cannot succeed, so it is refused before the step-up asks for a password.
        self._refuse_beyond_member_limit(tenant_key)

        self._step_up_verifier.verify(
            requester,
            action="admin_membership_add",
            # #1884 - a factor obtained to add this account to this tenant confirms this pair only.
            target=f"{tenant_key}|{user_key}",
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant_key,
            role=role,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        created = self._create_membership_unless_erasing(membership)
        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_ADDED,
            via=SecurityAuditVia.PLATFORM_ADMIN,
            actor_user_key=requester.key or "",
            target_user_key=user_key,
            tenant_key=tenant_key,
            membership=created,
        )
        return created

    def admin_change_membership_role(
        self,
        membership_key: str,
        new_role: TenantRole,
        *,
        tenant_key: str | None = None,
        user_key: str | None = None,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> Membership:
        """Change a membership's domain role on the platform-admin path.

        Single implementation behind both perspectives' role-change endpoints.
        ``tenant_key`` / ``user_key`` are the caller's ownership constraint (the
        path segment the membership must belong to); either or both may be given,
        and a mismatch is a :class:`NotFoundError`, matching the pre-#1019 router
        behaviour of 404-ing when the membership does not belong to the addressed
        parent. The write goes through
        :meth:`IMembershipRepository.update_fields`, which re-validates the merged
        model (#968).

        **Step-up when the role changes (#2032, REQ-024 AK-57).** Demoting a tenant's
        last ``lead`` — or promoting someone to it — changes who may delete in the
        tenant and who may lock others out, so an actual change of the role passes
        the admin's *own* step-up (``requester``: the password, the fresh
        re-authentication or the mailed code; an API key is 403, 429 when locked),
        bound to this membership (#1884). It lives here, not on the routes, so both
        views pass the same check; the step-up arguments are keyword-only without a
        default, so a new caller cannot forget them. A role re-sent unchanged (the
        edit form re-sends what it loaded) needs none and writes nothing. The
        membership is resolved first (404 for an unknown one or one under another
        parent); without a valid step-up nothing is written.
        """
        membership = self._resolve_admin_membership(membership_key, tenant_key=tenant_key, user_key=user_key)
        if membership.role == new_role:
            return membership
        self._step_up_verifier.verify(
            requester,
            action="admin_membership_role_change",
            # #1884 — a factor obtained to change this membership's role confirms this one only.
            target=membership_key,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        result = self._membership_repo.update_fields(membership_key, {"role": new_role})
        if not result:
            raise NotFoundError("Membership", membership_key)
        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED,
            via=SecurityAuditVia.PLATFORM_ADMIN,
            actor_user_key=requester.key or "",
            target_user_key=membership.user_key,
            tenant_key=membership.tenant_key,
            membership=result,
            old_role=membership.role,
        )
        return result

    def admin_remove_membership(
        self,
        membership_key: str,
        *,
        tenant_key: str | None = None,
        user_key: str | None = None,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> bool:
        """Remove a membership on the platform-admin path.

        Single implementation behind both perspectives' delete endpoints. The
        removal goes through :meth:`IMembershipRepository.delete`, which also
        drops the ``has_membership`` / ``membership_in`` edges **and** any
        location assignments for the membership — the latter was orphaned by the
        pre-#1019 router, which deleted only the two edges.

        **Step-up (#2009, REQ-024 AK-56).** Removing a member — also a tenant's last
        ``lead`` — locks that person out of the tenant, so it passes the admin's
        *own* step-up (``requester``: the password, the fresh re-authentication or
        the mailed code; an API key is 403, 429 when locked), bound to this
        membership (#1884). It lives here, not on the routes, so both views pass
        the same check; the step-up arguments are keyword-only without a default,
        so a new caller cannot forget them. The membership is resolved first (404
        for an unknown one or one under another parent); without a valid step-up
        nothing is removed.
        """
        membership = self._resolve_admin_membership(membership_key, tenant_key=tenant_key, user_key=user_key)
        self._step_up_verifier.verify(
            requester,
            action="admin_membership_removal",
            # #1884 — a factor obtained to remove this membership confirms this one only.
            target=membership_key,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        removed = self._membership_repo.delete(membership_key)
        if removed:
            self._audit_membership(
                action=SecurityAuditAction.MEMBERSHIP_REMOVED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=requester.key or "",
                target_user_key=membership.user_key,
                tenant_key=membership.tenant_key,
                membership=membership,
            )
            self._end_task_assignments(membership.tenant_key, membership.user_key)
        return removed

    def _resolve_admin_membership(
        self,
        membership_key: str,
        *,
        tenant_key: str | None,
        user_key: str | None,
    ) -> Membership:
        """Load a membership for a platform-admin op, enforcing the ownership constraint.

        Fails with :class:`NotFoundError` when the membership is unknown or does
        not belong to the addressed tenant (tenant perspective) / user (user
        perspective). Returning the same 404 for "unknown" and "belongs to a
        different parent" avoids a cross-parent existence oracle.
        """
        membership = self._membership_repo.get_by_key(membership_key)
        if not membership:
            raise NotFoundError("Membership", membership_key)
        if tenant_key is not None and membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)
        if user_key is not None and membership.user_key != user_key:
            raise NotFoundError("Membership", membership_key)
        return membership

    def change_member_role(
        self,
        tenant_key: str,
        membership_key: str,
        new_role: TenantRole,
        actor_scopes: list[AdminScope],
        *,
        actor_user_key: str,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> Membership:
        """Change a member's domain role (REQ-049 axis 1).

        Gated on the actor's ``MANAGEMENT`` scope, not on their own rank:
        handing out a role is member management, and the secretary who does it
        need not be a gardener.

        **Step-up when the role changes (#2032, REQ-024 AK-57).** The same rule as
        :meth:`admin_change_membership_role`, for the tenant's own member
        administrator: an actual change passes the actor's step-up
        (``tenant_member_role_change``, bound to the membership — #1884); a role
        re-sent unchanged needs none and writes nothing. The scope gate and the
        tenant-ownership 404 come first.

        **Escalation (#2078, REQ-024 AK-58).** The step-up proves who is asking, not that
        they may be given the role: before it, :meth:`_refuse_role_grant` refuses a member
        raising their *own* role (``actor_user_key`` is the acting account, compared with the
        membership's owner) and a non-lead granting ``lead`` in the platform tenant, where it
        is the platform role (403, nothing written, no password asked for).
        """
        if not self._membership_engine.can_manage_members(actor_scopes):
            raise ForbiddenError("Requires the management administrative scope")

        if not self._membership_engine.can_assign_role(actor_scopes, new_role):
            raise ForbiddenError("Requires the management administrative scope")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        if membership.role == new_role:
            return membership

        self._refuse_role_grant(
            tenant_key=tenant_key,
            actor_user_key=actor_user_key,
            target_role=new_role,
            current_role=membership.role,
            is_own_membership=membership.user_key == actor_user_key,
        )

        self._step_up_verifier.verify(
            requester,
            action="tenant_member_role_change",
            # #1884 — a factor obtained to change this membership's role confirms this one only.
            target=membership_key,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        result = self._membership_repo.update_fields(membership_key, {"role": new_role})
        if not result:
            raise NotFoundError("Membership", membership_key)
        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED,
            via=SecurityAuditVia.TENANT_ADMIN,
            actor_user_key=actor_user_key,
            target_user_key=membership.user_key,
            tenant_key=tenant_key,
            membership=result,
            old_role=membership.role,
        )
        return result

    def _refuse_role_grant(
        self,
        *,
        tenant_key: str,
        actor_user_key: str,
        target_role: TenantRole,
        current_role: TenantRole | None,
        is_own_membership: bool,
    ) -> None:
        """Raise :class:`ForbiddenError` when this role grant may not stand (#2078, REQ-024 AK-58).

        The one place the escalation rule of :meth:`MembershipEngine.role_grant_refusal` meets
        stored state: the actor's role comes from their stored, *active* membership in the
        tenant, and whether the tenant is the platform tenant from the tenant row - never from
        the request. Every service function that hands out a membership role through the
        tenant-scoped routes (:meth:`change_member_role`, the two invitations) calls it; the
        class guard ``test_membership_role_grants_check_for_escalation`` holds that.
        """
        # The rule only bites on a self-raise or on ``lead``; skip the two reads otherwise.
        if not is_own_membership and target_role != TenantRole.LEAD:
            return
        actor = self._membership_repo.get_by_user_and_tenant(actor_user_key, tenant_key)
        tenant = self._tenant_repo.get_by_key(tenant_key)
        reason = self._membership_engine.role_grant_refusal(
            target_role=target_role,
            current_role=current_role,
            is_own_membership=is_own_membership,
            tenant_is_platform=bool(tenant and tenant.is_platform),
            actor_role=actor.role if actor and actor.is_active else None,
        )
        if reason:
            raise ForbiddenError(reason)

    def change_member_scopes(
        self,
        tenant_key: str,
        membership_key: str,
        new_scopes: list[AdminScope],
        actor_scopes: list[AdminScope],
        *,
        actor_user_key: str,
    ) -> Membership:
        """Change a member's administrative scopes (REQ-049 axis 2).

        Enforces INV-1: the last membership carrying ``MANAGEMENT`` cannot drop
        it. Losing it would strand the tenant — nobody left could invite anyone,
        not even the people still in it.
        """
        if not self._membership_engine.can_manage_members(actor_scopes):
            raise ForbiddenError("Requires the management administrative scope")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        losing_management = membership.has_management and AdminScope.MANAGEMENT not in new_scopes
        if losing_management:
            self._guard_last_manager(
                tenant_key,
                "Cannot remove the management scope from the last member who has it",
            )

        result = self._membership_repo.update_fields(membership_key, {"admin_scopes": list(new_scopes)})
        if not result:
            raise NotFoundError("Membership", membership_key)
        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_SCOPES_CHANGED,
            via=SecurityAuditVia.TENANT_ADMIN,
            actor_user_key=actor_user_key,
            target_user_key=membership.user_key,
            tenant_key=tenant_key,
            membership=result,
            old_scopes=membership.admin_scopes,
        )
        return result

    def remove_member(
        self,
        tenant_key: str,
        membership_key: str,
        actor_scopes: list[AdminScope],
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> bool:
        """Remove a member from the tenant (the tenant's own member administrator).

        **Step-up (#2032, REQ-024 AK-57).** Removing a member — also the tenant's last
        ``lead`` — locks that person out, so it passes the actor's *own* step-up
        (``tenant_member_removal``, bound to the membership — #1884), as the
        platform-admin removal does (#2009). The scope gate, the tenant-ownership 404
        and INV-1 (the last ``management`` holder stays, 422) come first: a request that
        cannot succeed is not asked for a password. The step-up arguments are
        keyword-only without a default, so a new caller cannot forget them.
        """
        if not self._membership_engine.can_manage_members(actor_scopes):
            raise ForbiddenError("Requires the management administrative scope")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        if membership.has_management:
            self._guard_last_manager(tenant_key, "Cannot remove the last member with the management scope")

        self._step_up_verifier.verify(
            requester,
            action="tenant_member_removal",
            # #1884 — a factor obtained to remove this membership confirms this one only.
            target=membership_key,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        removed = self._membership_repo.delete(membership_key)
        if removed:
            self._audit_membership(
                action=SecurityAuditAction.MEMBERSHIP_REMOVED,
                via=SecurityAuditVia.TENANT_ADMIN,
                actor_user_key=requester.key or "",
                target_user_key=membership.user_key,
                tenant_key=tenant_key,
                membership=membership,
            )
            self._end_task_assignments(tenant_key, membership.user_key)
        return removed

    def leave_tenant(self, tenant_key: str, user_key: str) -> bool:
        membership = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
        if not membership:
            raise NotFoundError("Membership", f"user={user_key}")

        if membership.has_management:
            self._guard_last_manager(
                tenant_key,
                "Cannot leave as the last member with the management scope. Hand it over first.",
            )

        left = self._membership_repo.delete(membership.key)
        if left:
            self._audit_membership(
                action=SecurityAuditAction.MEMBERSHIP_LEFT,
                via=SecurityAuditVia.SELF,
                actor_user_key=user_key,
                target_user_key=user_key,
                tenant_key=tenant_key,
                membership=membership,
            )
            self._end_task_assignments(tenant_key, user_key)
        return left

    def _end_task_assignments(self, tenant_key: str, user_key: str) -> None:
        """Take *user_key* off the assignee of *tenant_key*'s tasks after its membership ended (#2114).

        Called after the membership delete succeeded. A failing clear does not undo the removal and is
        not raised: the membership is gone, and the care-reminder beat asks the stored membership before it
        notifies (``notification_tasks``), so a leftover assignment reaches nobody - the clear is the tidy-up,
        the beat's check the barrier. The failure is logged (pseudonymised, no key, no exception text).
        """
        if self._task_repo is None:
            return
        try:
            cleared = self._task_repo.clear_assignee(tenant_key=tenant_key, user_key=user_key)
        except Exception as exc:  # noqa: BLE001 - see the docstring: the removal stands, the beat checks membership
            logger.warning(
                "task_assignments_not_cleared",
                tenant=log_tenant(tenant_key),
                subject=log_subject(user_key),
                error_type=type(exc).__name__,
            )
            return
        if cleared:
            logger.info(
                "task_assignments_cleared",
                tenant=log_tenant(tenant_key),
                subject=log_subject(user_key),
                tasks=int(cleared),
            )

    def _audit_membership(
        self,
        *,
        action: SecurityAuditAction,
        via: SecurityAuditVia,
        actor_user_key: str,
        target_user_key: str,
        tenant_key: str,
        membership: Membership,
        old_role: str | None = None,
        old_scopes: list[AdminScope] | None = None,
    ) -> None:
        """Write the persistent security-audit row of one membership change (MT-014, #2111).

        The one place every mutating method of this service hands its change to
        (``test_membership_mutations_write_the_security_audit`` holds that). Called
        **after** the change succeeded; a failing audit write raises, so the change
        never goes unrecorded without somebody seeing the error. The roles and scopes
        recorded are the stored membership's, never a request's claim.
        """
        if self._security_audit is None:
            return
        now_role, now_scopes = str(membership.role), [str(x) for x in membership.admin_scopes]
        before_scopes = [str(x) for x in old_scopes] if old_scopes is not None else None
        # What each action says about "before" and "after": a grant has only an after, a
        # removal only a before, a change both.
        fields: dict[str, Any]
        if action in (SecurityAuditAction.MEMBERSHIP_REMOVED, SecurityAuditAction.MEMBERSHIP_LEFT):
            fields = {"old_role": now_role, "old_scopes": now_scopes}
        elif action == SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED:
            fields = {"old_role": None if old_role is None else str(old_role), "new_role": now_role}
        elif action == SecurityAuditAction.MEMBERSHIP_SCOPES_CHANGED:
            fields = {"old_scopes": before_scopes, "new_scopes": now_scopes}
        else:
            fields = {"new_role": now_role, "new_scopes": now_scopes}
        self._security_audit.record_membership_change(
            action=action,
            via=via,
            actor_user_key=actor_user_key,
            target_user_key=target_user_key,
            tenant_key=tenant_key,
            membership_key=membership.key,
            **fields,
        )

    def _guard_last_manager(self, tenant_key: str, message: str) -> None:
        """Raise unless the tenant keeps at least one ``MANAGEMENT`` membership (INV-1)."""
        manager_count = self._membership_repo.count_managers(tenant_key)
        if not self._membership_engine.validate_not_last_manager(manager_count, True):
            raise ValidationError(message)

    # --- Invitations ---

    def create_email_invitation(
        self,
        tenant_key: str,
        invited_by_user_key: str,
        email: str,
        role: TenantRole = TenantRole.VIEWER,
    ) -> InvitationLink:
        self._refuse_invitation_while_owner_erasing(tenant_key=tenant_key)
        self._refuse_role_grant(
            tenant_key=tenant_key,
            actor_user_key=invited_by_user_key,
            target_role=role,
            current_role=None,
            is_own_membership=False,
        )
        raw_token, token_hash = self._invitation_engine.create_invitation_token()
        expires_at = self._invitation_engine.calculate_expiry(days=7)

        invitation = Invitation(
            tenant_key=tenant_key,
            invited_by_user_key=invited_by_user_key,
            invitation_type=InvitationType.EMAIL,
            email=email,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at.isoformat(),
        )
        invitation = self._invitation_repo.create(invitation)

        logger.info("email_invitation_created", tenant=log_tenant(tenant_key), email_sha256=email_digest(email))
        return InvitationLink(
            invitation_key=invitation.key,
            token=raw_token,
            expires_at=expires_at,
        )

    def create_link_invitation(
        self,
        tenant_key: str,
        invited_by_user_key: str,
        role: TenantRole = TenantRole.VIEWER,
    ) -> InvitationLink:
        self._refuse_invitation_while_owner_erasing(tenant_key=tenant_key)
        self._refuse_role_grant(
            tenant_key=tenant_key,
            actor_user_key=invited_by_user_key,
            target_role=role,
            current_role=None,
            is_own_membership=False,
        )
        raw_token, token_hash = self._invitation_engine.create_invitation_token()
        expires_at = self._invitation_engine.calculate_expiry(days=7)

        invitation = Invitation(
            tenant_key=tenant_key,
            invited_by_user_key=invited_by_user_key,
            invitation_type=InvitationType.LINK,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at.isoformat(),
        )
        invitation = self._invitation_repo.create(invitation)

        logger.info("link_invitation_created", tenant=log_tenant(tenant_key))
        return InvitationLink(
            invitation_key=invitation.key,
            token=raw_token,
            expires_at=expires_at,
        )

    def email_invitation_admits(self, *, email: str, token: str) -> bool:
        """Whether *token* names an e-mail invitation that admits creating an account for *email* (#2132).

        REQ-023 §3.2d: the exception to ``invite_only`` and to the domain allowlist on a **local**
        registration. The token proves that its holder received the invitation; the invitation must be
        of type ``email``, pending, unexpired and issued for *email* (case-insensitive). A link
        invitation admits nobody: it is meant to be shared, and one leaked link would reopen the
        installation to everybody holding it.
        """
        invitation = self._invitation_repo.get_by_token_hash(self._invitation_engine.hash_token(token))
        return invitation is not None and self._invitation_admits_address(invitation, email)

    def email_invitation_pending_for(self, *, email: str) -> bool:
        """Whether a pending, unexpired e-mail invitation was issued for *email* (#2132).

        The exception on the **first OIDC sign-in**, which carries no token: the caller asks only for an
        address its identity provider asserted as verified, which is the proof the token is locally.
        """
        return any(
            self._invitation_admits_address(invitation, email)
            for invitation in self._invitation_repo.list_pending_email_invitations(email)
        )

    def _invitation_admits_address(self, invitation: Invitation, email: str) -> bool:
        address = email.strip().lower()
        return (
            bool(address)
            and invitation.invitation_type == InvitationType.EMAIL
            and invitation.status == InvitationStatus.PENDING
            and (invitation.email or "").strip().lower() == address
            and not self._invitation_engine.is_expired(invitation.expires_at)
        )

    def list_invitations(self, tenant_key: str) -> list[Invitation]:
        return self._invitation_repo.list_by_tenant(tenant_key)

    def revoke_invitation(self, tenant_key: str, invitation_key: str) -> Invitation:
        invitation = self._invitation_repo.get_by_key(invitation_key)
        if not invitation or invitation.tenant_key != tenant_key:
            raise NotFoundError("Invitation", invitation_key)

        result = self._invitation_repo.update_fields(invitation_key, {"status": InvitationStatus.REVOKED})
        if not result:
            raise NotFoundError("Invitation", invitation_key)
        return result

    def accept_invitation(self, token: str, account: User) -> Membership:
        """Accept an invitation with the signed-in *account* (REQ-024 §1a.2).

        **An e-mail invitation belongs to the address it was sent to (#2115, REQ-024 AK-61).**
        The token alone used to be enough: a forwarded or intercepted link granted a membership,
        up to ``lead``, to whoever opened it signed in. For an invitation of type ``email`` the
        accepting account must carry the invited address **and** have proven it
        (:attr:`User.address_proven` - the verified flag alone proves nothing, #1948); otherwise
        403, before anything about the invitation (status, tenant, role) is told and with nothing
        written. A link invitation is meant to be shared and stays open to any account.
        """
        user_key = account.key or ""
        token_hash = self._invitation_engine.hash_token(token)
        invitation = self._invitation_repo.get_by_token_hash(token_hash)
        if not invitation:
            raise NotFoundError("Invitation", "token")
        self._require_invited_account(invitation, account)

        is_expired = self._invitation_engine.is_expired(invitation.expires_at)
        is_pending = invitation.status == InvitationStatus.PENDING
        self._refuse_while_erasing(invitation.tenant_key)
        self._refuse_invitation_while_owner_erasing(tenant_key=invitation.tenant_key)
        existing = self._membership_repo.get_by_user_and_tenant(user_key, invitation.tenant_key)

        can_accept, reason = self._invitation_engine.can_accept(
            is_expired=is_expired,
            is_pending=is_pending,
            is_already_member=existing is not None,
        )
        if not can_accept:
            raise ValidationError(reason)
        # #2133 - a full tenant is refused before the invitation is touched; it stays pending.
        self._refuse_beyond_member_limit(invitation.tenant_key)

        # Accepted first, and only while still pending (#1825 SEC-001 and PR
        # review): a revocation that landed after the status read above — the
        # request-time revocation of an account erasure — wins before any
        # membership exists, so no erasure decision can count a member that is
        # about to be taken back, and a failing write leaves no membership.
        accepted = self._invitation_repo.mark_accepted_if_pending(
            invitation.key or "",
            {"accepted_by_user_key": user_key, "accepted_at": datetime.now(UTC).isoformat()},
        )
        if accepted is None:
            raise ValidationError("Invitation is no longer pending")

        membership = Membership(
            user_key=user_key,
            tenant_key=invitation.tenant_key,
            role=invitation.role,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        try:
            # Refused and taken back if the tenant froze meanwhile.
            membership = self._create_membership_unless_erasing(membership)
        except Exception:
            # The join did not happen: the invitation is handed back as it was.
            self._invitation_repo.update_fields(
                invitation.key or "",
                {"status": InvitationStatus.PENDING, "accepted_by_user_key": None, "accepted_at": None},
            )
            raise

        self._audit_membership(
            action=SecurityAuditAction.MEMBERSHIP_ADDED,
            via=SecurityAuditVia.INVITATION,
            actor_user_key=user_key,
            target_user_key=user_key,
            tenant_key=invitation.tenant_key,
            membership=membership,
        )
        logger.info(
            "invitation_accepted",
            tenant=log_tenant(invitation.tenant_key),
            subject=log_subject(user_key),
        )
        return membership

    @staticmethod
    def _require_invited_account(invitation: Invitation, account: User) -> None:
        """403 unless *account* may use *invitation* (#2115): an e-mail invitation needs its proven address.

        One answer for "another address", "address not proven" and "an e-mail invitation that names no
        address" (a malformed row is never admitted): whoever holds the token learns nothing about
        which of the three applies, nor the invited address.
        """
        if invitation.invitation_type != InvitationType.EMAIL:
            return
        invited = (invitation.email or "").strip().lower()
        if invited and account.email.strip().lower() == invited and account.address_proven:
            return
        raise ForbiddenError(
            "This invitation was issued for another address, or the address of your account is not confirmed."
        )

    # --- Location Assignments ---

    def list_assignments(self, tenant_key: str) -> list[LocationAssignment]:
        return self._assignment_repo.list_by_tenant(tenant_key)

    def create_assignment(
        self,
        tenant_key: str,
        membership_key: str,
        location_key: str,
        can_edit: bool = True,
        notes: str | None = None,
    ) -> LocationAssignment:
        # Verify membership belongs to tenant
        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        # The location is resolved through its site under the tenant (#1871 B3):
        # it used to be taken as given, even an unknown one, and an
        # ASSIGNED_TO_LOCATION edge written to it.
        if self._site_anchors is None:
            raise NotFoundError("Location", location_key)
        resolve_owned_location(self._site_anchors, location_key, tenant_key)

        # Check for duplicate
        existing = self._assignment_repo.get_by_membership_and_location(membership_key, location_key)
        if existing:
            raise ValidationError("Assignment already exists")

        assignment = LocationAssignment(
            membership_key=membership_key,
            location_key=location_key,
            tenant_key=tenant_key,
            can_edit=can_edit,
            notes=notes,
        )
        return self._assignment_repo.create(assignment)

    def update_assignment(self, tenant_key: str, assignment_key: str, data: dict) -> LocationAssignment:
        """Apply a partial update to one location assignment.

        ``data`` is a partial payload and is passed through to
        :meth:`ILocationAssignmentRepository.update_fields`, so the **caller owns
        the allow-list**: build it from ``AssignmentUpdateRequest.model_dump()``
        or from named fields, never from a raw request body. The only endpoint
        that reaches this (``PATCH /t/{slug}/assignments/{key}``) does the
        former, and that closed schema is what keeps ``tenant_key`` /
        ``membership_key`` / ``location_key`` out of the payload.
        """
        assignment = self._assignment_repo.get_by_key(assignment_key)
        if not assignment or assignment.tenant_key != tenant_key:
            raise NotFoundError("LocationAssignment", assignment_key)

        result = self._assignment_repo.update_fields(assignment_key, data)
        if not result:
            raise NotFoundError("LocationAssignment", assignment_key)
        return result

    def delete_assignment(self, tenant_key: str, assignment_key: str) -> bool:
        assignment = self._assignment_repo.get_by_key(assignment_key)
        if not assignment or assignment.tenant_key != tenant_key:
            raise NotFoundError("LocationAssignment", assignment_key)
        return self._assignment_repo.delete(assignment_key)

    # --- Helpers ---

    def get_membership(self, user_key: str, tenant_key: str) -> Membership | None:
        return self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)

    def _ensure_unique_slug(self, slug: str, exclude_key: str | None = None) -> str:
        """Append numeric suffix if slug already exists."""
        candidate = slug
        counter = 1
        while True:
            existing = self._tenant_repo.get_by_slug(candidate)
            if existing is None:
                return candidate
            if exclude_key and existing.key == exclude_key:
                return candidate
            counter += 1
            candidate = f"{slug}-{counter}"
