from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import structlog

from app.common.datetimes import ensure_aware_utc
from app.common.decoys import email_digest
from app.common.enums import (
    AdminScope,
    InvitationStatus,
    InvitationType,
    TenantRole,
    TenantType,
)
from app.common.exceptions import (
    DuplicateError,
    FeatureNotConfiguredError,
    ForbiddenError,
    NotFoundError,
    TenantErasureClaimLostError,
    TenantErasureIncompleteError,
    ValidationError,
    WriteConflictError,
)
from app.common.log_privacy import log_subject
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, UNAVAILABLE_LOG_SUBJECT, ErasureEngine
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
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
from app.domain.interfaces.tenant_erasure_executor import ITenantErasureExecutor
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.invitation import Invitation, InvitationLink
from app.domain.models.location_assignment import LocationAssignment
from app.domain.models.membership import MemberInfo, Membership, UserMembershipInfo
from app.domain.models.privacy import PersonalTenantErasure, PersonalTenantErasurePreview
from app.domain.models.tenant import Tenant, TenantWithRole
from app.domain.models.tenant_erasure import (
    TenantDeletionConfirmation,
    TenantDeletionStepUp,
    TenantErasureOrigin,
    TenantErasureRecord,
)
from app.domain.models.user import User, allows_interactive_auth
from app.domain.services.location_ownership import SiteAnchorSource, resolve_owned_location
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
    ) -> None:
        # The location → site reads a location assignment is checked through
        # (#1871 B3). Without them an assignment is refused, never stored unchecked.
        self._site_anchors = site_anchors
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
        tenant = self._tenant_repo.create(tenant)

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant.key,
            # REQ-049 §6: the founder gets the top domain role and both
            # administrative scopes — a tenant whose creator could not invite
            # anyone would be stranded from the first second.
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT, AdminScope.TECHNICAL],
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        self._membership_repo.create(membership)

        logger.info("personal_tenant_created", subject=log_subject(user_key), tenant_key=tenant.key)
        return tenant

    def create_organization(
        self, user_key: str, name: str, description: str | None = None, max_members: int = 50
    ) -> Tenant:
        """Create an organization tenant."""
        errors = self._tenant_engine.validate_tenant_name(name)
        if errors:
            raise ValidationError(errors[0])

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
            max_members=max_members,
        )
        tenant = self._tenant_repo.create(tenant)

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant.key,
            # REQ-049 §6: the founder gets the top domain role and both
            # administrative scopes — a tenant whose creator could not invite
            # anyone would be stranded from the first second.
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT, AdminScope.TECHNICAL],
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        self._membership_repo.create(membership)

        logger.info("organization_created", subject=log_subject(user_key), tenant_key=tenant.key)
        return tenant

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

        Two endpoints reach this, and both do the former:

        * ``PATCH /t/{slug}`` with ``TenantUpdateRequest`` (``name``,
          ``description``, ``max_members``);
        * ``PATCH /admin/platform/tenants/{key}`` with ``AdminTenantUpdate``
          (the same three plus ``is_active``, which only a platform admin may
          set) — routed here by #997, which ended a router that wrote to the
          tenants collection itself.

        Neither schema sets ``extra="allow"``, and that closedness is the only
        thing keeping ``owner_user_key``, ``is_platform``, ``tenant_type``,
        ``slug`` and ``settings`` out of the payload: ``update_fields`` applies
        ``data`` through ``model_copy(update=...)``, which does not validate.
        ``slug`` is derived here, from ``name``, and never accepted from a
        caller.

        **The platform tenant cannot be deactivated (#1021).** ``delete_tenant``
        already refuses the platform tenant (``is_platform`` → 403) from the
        router; deactivating it via ``{"is_active": False}`` slipped through
        because this path had no such guard. The check lives here, not on the
        router, so both entry points are covered — the platform-admin
        ``PATCH /admin/platform/tenants/{key}`` and the tenant-scoped
        ``PATCH /t/{slug}`` (which does not carry ``is_active`` today, but would
        be guarded if it ever did). It refuses with the same
        :class:`ForbiddenError` (403) shape ``delete_tenant`` uses, and is scoped
        to deactivation only — renaming or re-describing the platform tenant
        still works.
        """
        if data.get("is_active") is False:
            tenant = self._tenant_repo.get_by_key(tenant_key)
            if not tenant:
                raise NotFoundError("Tenant", tenant_key)
            if tenant.is_platform:
                raise ForbiddenError("The platform tenant cannot be deactivated.")

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
           collides, 409) and freeze the tenant: every membership is deactivated,
           so no member request writes into it while it is erased.
        3. Run the erasure. ``completed`` only when the executor found nothing
           left; otherwise ``partially_completed`` with a backoff that
           :meth:`resume_tenant_erasures` (daily beat) retries.

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
        requested_by = log_subject(requester.key)
        logger.info(
            "tenant_erasure.authorized",
            tenant_key=tenant_key,
            origin=origin,
            step_up=step_up,
            subject=requested_by,
        )

        if record is None:
            try:
                record = self._require_tenant_erasure_repo().create_with_key(
                    TenantErasureRecord(
                        tenant_key=tenant_key,
                        tenant_type=str(tenant.tenant_type) if tenant is not None else "unknown",
                        origin=origin,
                        requested_by_subject=requested_by,
                        step_up=step_up,
                        slug_digest=self._tenant_slug_digest(tenant.slug) if tenant is not None else None,
                        requested_at=now,
                    ),
                    record_key,
                )
            except (DuplicateError, WriteConflictError) as exc:
                raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION) from exc

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
        self._membership_repo.deactivate_all_for_tenant(tenant_key)
        self._dispatch_tenant_erasure(record_key)
        return record

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
            logger.info("tenant_erasure.dispatched", record_key=record_key)
        except Exception as exc:  # noqa: BLE001 — broker outage is survivable, the beat retries
            logger.error("tenant_erasure.dispatch_failed", record_key=record_key, error_type=type(exc).__name__)

    def run_tenant_erasure_task(self, record_key: str, now: datetime | None = None) -> dict[str, object]:
        """Run the deletion *record_key* names, as the Celery worker (#1792).

        Claims the record atomically — a second dispatch, the daily beat, or a run
        that is still alive finds it held and does nothing — then runs the same
        batched, heartbeat-refreshing erasure as every other path. Never raises for
        a failed run: the failure is recorded on the record (backoff, escalation)
        and the beat retries it.
        """
        now = now or datetime.now(UTC)
        repo = self._require_tenant_erasure_repo()
        record = repo.get(record_key)
        if record is None or record.status == "completed":
            return {"record_key": record_key, "outcome": "nothing_to_do"}
        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            logger.error("tenant_erasure.run_not_configured", record_key=record_key, reason=configuration_error)
            return {"record_key": record_key, "outcome": "held"}
        claimed = self._claim_tenant_erasure(record_key, now)
        if claimed is None:
            return {"record_key": record_key, "outcome": "not_claimed"}
        self._membership_repo.deactivate_all_for_tenant(claimed.tenant_key)
        finished = self._run_tenant_erasure(claimed, now, raise_on_failure=False)
        return {"record_key": record_key, "outcome": finished.status}

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
        candidates = repo.list_due(stale_before_iso=stale_before.isoformat())
        result = {"candidates": len(candidates), "completed": 0, "open": 0, "deferred": 0, "held": 0, "escalated": 0}
        if not candidates:
            return result
        configuration_error = self._tenant_erasure_configuration_error()
        if configuration_error is not None:
            result["held"] = len(candidates)
            logger.error("tenant_erasure.retry_not_configured", reason=configuration_error, held=len(candidates))
            return result
        for record in candidates:
            if record.next_attempt_at is not None and record.next_attempt_at > now + _TENANT_ERASURE_RETRY_SLACK:
                result["deferred"] += 1
                logger.info(
                    "tenant_erasure.deferred",
                    record_key=record.key,
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
                logger.info("tenant_erasure.awaiting_account_erasure", record_key=record.key)
                continue
            claimed = self._claim_tenant_erasure(record.key or "", now)
            if claimed is None:
                continue
            self._membership_repo.deactivate_all_for_tenant(claimed.tenant_key)
            finished = self._run_tenant_erasure(claimed, now, raise_on_failure=False)
            result["completed" if finished.status == "completed" else "open"] += 1
            if finished.status != "completed" and finished.attempt_count >= TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS:
                result["escalated"] += 1
        logger.info("tenant_erasure.retry_completed", **result)
        return result

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
        kept, the record withdrawn; before #1825 the joiner was silently
        deactivated and the tenant erased. A record an earlier attempt left
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
            # AK-IE-07 — the record is in place, so every later join is refused
            # or rolls itself back (:meth:`accept_invitation`); whoever is an
            # active member now and was not in the first read joined late.
            retained = self._personal_tenant_retention(
                tenant_key,
                user_key,
                known_members=known_members,
                frozen_at=record.requested_at if record is not None else None,
                requested_at=requested_at,
            )
            if retained is not None:
                if not self._require_tenant_erasure_repo().delete_unclaimed(record_key):
                    # A run claimed the record in between; it decides, and the
                    # account erasure is retried against what it leaves.
                    raise WriteConflictError(TenantErasureEngine.RECORD_COLLECTION)
                return retained
        finished = self._erase_tenant_for_account_erasure(tenant_key, tenant, now=now)
        if finished.status != "completed":
            raise TenantErasureIncompleteError(list(finished.unreached) or [TenantErasureEngine.TENANT_COLLECTION])
        return PersonalTenantErasure(tenant_key=tenant_key, outcome="erased", tenant_erasure_record_key=record_key)

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

    def _create_membership_unless_erasing(self, membership: Membership) -> Membership:
        """Insert a membership into an existing tenant, and take it back if the tenant froze meanwhile.

        REQ-025 AK-IE-07 (#1825 SEC-003 b). The caller's
        :meth:`_refuse_while_erasing` and this insert are two writes: a deletion
        record inserted between them froze the tenant while the membership was
        on its way in. Checked again once the membership exists, and removed,
        so no active membership stays in a tenant that is being erased — the
        counterpart of the second membership read in
        :meth:`erase_personal_tenant_of`. Every path that joins an account to
        an existing tenant goes through here.
        """
        created = self._membership_repo.create(membership)
        try:
            self._refuse_while_erasing(membership.tenant_key)
        except ForbiddenError:
            if created.key:
                self._membership_repo.delete(created.key)
            raise
        return created

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
            logger.warning("tenant_erasure.claim_lost", record_key=record_key)
            if raise_on_failure:
                raise
            return record
        except Exception as exc:
            attempt = record.attempt_count + 1
            next_attempt_at = TenantErasureEngine.next_attempt_at(attempt, now)
            logger.error(
                "tenant_erasure.attempt_failed",
                record_key=record_key,
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
                logger.warning("tenant_erasure.claim_lost", record_key=record_key)
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
                record_key=record_key,
                attempt=attempt,
                unreached=report.unreached,
            )
            try:
                updated = conclude(fields)
            except TenantErasureClaimLostError:
                logger.warning("tenant_erasure.claim_lost", record_key=record_key)
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
            logger.warning("tenant_erasure.claim_lost", record_key=record_key)
            if raise_on_failure:
                raise
            return record
        logger.info("tenant_deleted", tenant_key=record.tenant_key, record_key=record_key)
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
        logger.error("tenant_erasure.escalated", record_key=record.key, attempt=attempt)
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
        logger.info("tenant_sensor_readings_deleted", tenant_key=tenant_key, removed=removed)
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
                tenant_key=tenant_key,
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
                tenant_key=tenant_key,
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
                tenant_key=tenant_key,
                prefix=prefix,
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

    def admin_add_membership(self, tenant_key: str, user_key: str, role: TenantRole) -> Membership:
        """Add a user to a tenant on the platform-admin path.

        Single implementation behind both ``POST .../tenants/{tk}/members`` and
        ``POST .../users/{uk}/memberships``. The membership row and its two graph
        edges are created by :meth:`IMembershipRepository.create`, so the edge
        management the two router copies duplicated now lives in one place.

        Raises :class:`NotFoundError` when the tenant is unknown and
        :class:`DuplicateError` when the user is already a member. The *user's*
        existence is verified by the router (it needs the user for the response
        anyway), which keeps this method free of a user-repository dependency.
        """
        tenant = self._tenant_repo.get_by_key(tenant_key)
        if not tenant:
            raise NotFoundError("Tenant", tenant_key)

        self._refuse_while_erasing(tenant_key)
        existing = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
        if existing:
            raise DuplicateError("memberships", "user_key+tenant_key", "already a member")

        membership = Membership(
            user_key=user_key,
            tenant_key=tenant_key,
            role=role,
            is_active=True,
            joined_at=datetime.now(UTC).isoformat(),
        )
        return self._create_membership_unless_erasing(membership)

    def admin_change_membership_role(
        self,
        membership_key: str,
        new_role: TenantRole,
        *,
        tenant_key: str | None = None,
        user_key: str | None = None,
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
        """
        self._resolve_admin_membership(membership_key, tenant_key=tenant_key, user_key=user_key)
        result = self._membership_repo.update_fields(membership_key, {"role": new_role})
        if not result:
            raise NotFoundError("Membership", membership_key)
        return result

    def admin_remove_membership(
        self,
        membership_key: str,
        *,
        tenant_key: str | None = None,
        user_key: str | None = None,
    ) -> bool:
        """Remove a membership on the platform-admin path.

        Single implementation behind both perspectives' delete endpoints. The
        removal goes through :meth:`IMembershipRepository.delete`, which also
        drops the ``has_membership`` / ``membership_in`` edges **and** any
        location assignments for the membership — the latter was orphaned by the
        pre-#1019 router, which deleted only the two edges.
        """
        self._resolve_admin_membership(membership_key, tenant_key=tenant_key, user_key=user_key)
        return self._membership_repo.delete(membership_key)

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
    ) -> Membership:
        """Change a member's domain role (REQ-049 axis 1).

        Gated on the actor's ``MANAGEMENT`` scope, not on their own rank:
        handing out a role is member management, and the secretary who does it
        need not be a gardener.
        """
        if not self._membership_engine.can_manage_members(actor_scopes):
            raise ForbiddenError("Requires the management administrative scope")

        if not self._membership_engine.can_assign_role(actor_scopes, new_role):
            raise ForbiddenError("Requires the management administrative scope")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        result = self._membership_repo.update_fields(membership_key, {"role": new_role})
        if not result:
            raise NotFoundError("Membership", membership_key)
        return result

    def change_member_scopes(
        self,
        tenant_key: str,
        membership_key: str,
        new_scopes: list[AdminScope],
        actor_scopes: list[AdminScope],
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
        return result

    def remove_member(self, tenant_key: str, membership_key: str, actor_scopes: list[AdminScope]) -> bool:
        if not self._membership_engine.can_manage_members(actor_scopes):
            raise ForbiddenError("Requires the management administrative scope")

        membership = self._membership_repo.get_by_key(membership_key)
        if not membership or membership.tenant_key != tenant_key:
            raise NotFoundError("Membership", membership_key)

        if membership.has_management:
            self._guard_last_manager(tenant_key, "Cannot remove the last member with the management scope")

        return self._membership_repo.delete(membership_key)

    def leave_tenant(self, tenant_key: str, user_key: str) -> bool:
        membership = self._membership_repo.get_by_user_and_tenant(user_key, tenant_key)
        if not membership:
            raise NotFoundError("Membership", f"user={user_key}")

        if membership.has_management:
            self._guard_last_manager(
                tenant_key,
                "Cannot leave as the last member with the management scope. Hand it over first.",
            )

        return self._membership_repo.delete(membership.key)

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

        logger.info("email_invitation_created", tenant_key=tenant_key, email_sha256=email_digest(email))
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

        logger.info("link_invitation_created", tenant_key=tenant_key)
        return InvitationLink(
            invitation_key=invitation.key,
            token=raw_token,
            expires_at=expires_at,
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

    def accept_invitation(self, token: str, user_key: str) -> Membership:
        token_hash = self._invitation_engine.hash_token(token)
        invitation = self._invitation_repo.get_by_token_hash(token_hash)
        if not invitation:
            raise NotFoundError("Invitation", "token")

        is_expired = self._invitation_engine.is_expired(invitation.expires_at)
        is_pending = invitation.status == InvitationStatus.PENDING
        self._refuse_while_erasing(invitation.tenant_key)
        existing = self._membership_repo.get_by_user_and_tenant(user_key, invitation.tenant_key)

        can_accept, reason = self._invitation_engine.can_accept(
            is_expired=is_expired,
            is_pending=is_pending,
            is_already_member=existing is not None,
        )
        if not can_accept:
            raise ValidationError(reason)

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

        logger.info(
            "invitation_accepted",
            tenant_key=invitation.tenant_key,
            subject=log_subject(user_key),
        )
        return membership

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
