"""Plant diary entries and their REQ-050 AI-analysis state machine.

The analysis half of this service is a lease-protected state machine
(REQ-050 §2.2). Every transition is its own checked method — never the generic
``update_entry`` — because the states are not data a caller may set: they encode
who is currently allowed to write the result, and an entry that changes state
behind the machine's back is an entry two agents can analyse at once.

Three properties carry the design:

* **Claiming is a compare-and-set on the document revision.** Two agents that
  read the same unclaimed entry cannot both win; the loser gets
  ``conflict.concurrent_update`` and retries. Without it the second agent would
  quietly overwrite the first one's claim and the user would pay for the same
  analysis twice (§2.2, AK-05).
* **The lease expires.** A crashed agent must not pin an entry forever, so the
  claim carries a deadline after which the entry is claimable again and shows up
  in the work queue again (AK-06).
* **The disclaimer is the server's, not the agent's.** It is attached here on
  every successful submission, whether or not the agent sent one (AK-11).
"""

import hashlib
import hmac
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.datetimes import ensure_aware_utc, now_utc
from app.common.enums import AttachmentCategory, DiaryAnalysisState, DiaryEnvironmentStatus, TenantRole
from app.common.exceptions import (
    ConsentRequiredError,
    DiaryAnalysisAlreadyClaimedError,
    DiaryAnalysisConcurrentUpdateError,
    DiaryAnalysisLeaseExpiredError,
    DiaryAnalysisNotClaimedError,
    DiaryAnalysisStateError,
    DiaryAnalysisValidationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.config.settings import settings
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter, IPlantDiaryRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.models.plant_diary_entry import DiaryAnalysis, PlantDiaryEntry
from app.domain.services.environment_snapshot_service import EnvironmentSnapshot, EnvironmentSnapshotService

logger = structlog.get_logger()

# ── REQ-050 lease and submission bounds ──────────────────────────────────────

#: Default lease length of a claim (REQ-050 §4.2). Same 15 minutes the stalled
#: data-export restart uses (REQ-025) — long enough for a vision model on five
#: photos, short enough that a crashed agent is not missed for an hour.
DEFAULT_LEASE_SECONDS = 900

#: Hard ceiling for a caller-supplied ``lease_seconds`` (§4.2); above it the call
#: is rejected with ``validation.error`` rather than silently capped — a recipe
#: that thinks it has two hours must find out at claim time, not at submit time.
MAX_LEASE_SECONDS = 3600

#: Upper bound of ``limit`` for the work queue (§4.1).
MAX_PENDING_LIMIT = 100

#: Defensive bound on the agent-chosen worker id. §4.2 leaves it free-form; it is
#: persisted in ``analysis_claimed_by`` and shown in the UI, so it is bounded.
MAX_WORKER_ID_LENGTH = 200

#: Length bounds of a submitted result (§4.5, duplicated in §5 on purpose so a
#: recipe that only reads §4 knows them). The ones the domain model already
#: expresses (``summary``, ``findings``, ``model``, ``recipe_version``) are
#: enforced by the model itself and only translated into ``validation.error``
#: here; these two have no model field to hang on.
MAX_ERROR_LENGTH = 2000
MAX_RECOMMENDED_ACTION_LENGTH = 2000

#: The mandatory reservation attached to every result (§2.4, AK-11). German is
#: the product's fallback language (AK-28); an English mirror belongs to the
#: presentation layer, not to the stored record. It is written server-side so a
#: recipe can neither omit nor soften it.
ANALYSIS_DISCLAIMER = (
    "Diese Einschätzung stammt von einem Sprachmodell, ist eine Hypothese und ersetzt keine fachliche Prüfung."
)

#: States a user may mark from (§2.2): a fresh entry, and a finished one that is
#: to be analysed again (AK-21). ``requested`` is absent because it is already
#: marked, ``in_progress`` because an agent is holding it.
_MARKABLE_STATES: frozenset[DiaryAnalysisState] = frozenset(
    {DiaryAnalysisState.NONE, DiaryAnalysisState.COMPLETED, DiaryAnalysisState.FAILED}
)

#: Roles that may mark an entry at all (REQ-050 §6, REQ-049 vocabulary).
_WRITING_ROLES: frozenset[TenantRole] = frozenset({TenantRole.GROWER, TenantRole.LEAD})

#: REQ-013 §2.3 — photos per diary entry. Enforced on the domain model and here.
MAX_PHOTO_REFS = 5

#: The only attachment category a diary entry may reference (REQ-050 §0,
#: NFR-013 §2.2). The frontend already uploads diary photos as ``diary``; pinning
#: it server-side is what stops an entry from pointing at a ``profile``,
#: ``pest_reference``, ``plant`` gallery or ``export`` object and dragging it into
#: an MCP image delivery.
_DIARY_PHOTO_CATEGORY = AttachmentCategory.DIARY

#: The placeholder shipped in ``settings.jwt_secret_key``. Deriving lease tokens
#: from a publicly known string would let anyone forge one.
_KNOWN_DEFAULT_JWT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"

#: Domain separator of the lease-token derivation (SEC-009). The signing secret
#: is shared with other protocols (the local-fs download tokens resolve the same
#: ``jwt_secret_key``/``fernet_key`` chain); the label makes a digest minted here
#: unusable there and vice versa. Versioned so the derivation can change without
#: ambiguity — bumping it invalidates in-flight leases, which is recoverable.
_LEASE_PURPOSE = "req050-lease-v1"

#: Analysis fields the generic ``update_entry`` must never write. They belong to
#: the state machine below; a caller that could set them through the ordinary
#: update path would walk straight past the lease (see :meth:`update_entry`).
_ANALYSIS_FIELDS: frozenset[str] = frozenset(
    {
        "analysis_state",
        "analysis_requested_at",
        "analysis_requested_by",
        "analysis_claimed_at",
        "analysis_claimed_by",
        "analysis_lease_expires_at",
        "analysis",
        "analysis_error",
    }
)

#: REQ-013 §2.3a — the environment snapshot is machine-written evidence, so an
#: edit may neither change it nor trigger a fresh capture. A later correction of
#: the *text* must not silently restamp the entry with a different climate: the
#: entry would then claim conditions that were never the ones it was written
#: under, which is the one property that makes the snapshot worth having.
#: A corrected value is a *manual* measurement and belongs in ``measurements``.
_ENVIRONMENT_FIELDS: frozenset[str] = frozenset(
    {
        "environment",
        "environment_captured_at",
        "environment_status",
    }
)

#: Signature of the REQ-050 §7.1 consent probe (purpose ``diary_ai_analysis``).
type ConsentChecker = Callable[[str], bool]


def _consent_not_evaluated(_user_key: str) -> bool:
    """Placeholder consent probe — the purpose is not evaluated yet (WP-6).

    REQ-050 §7.1 makes the analysis subject to the revocable consent purpose
    ``diary_ai_analysis``. Wiring that purpose is a separate work package; until
    it is wired the check is *not performed*, which reproduces today's behaviour
    rather than blocking a feature on a record no one writes yet.

    This is the single hook: inject a real checker into
    :class:`PlantDiaryService` and both call sites — the enforcement in
    :meth:`PlantDiaryService.request_analysis` and the ``can_request_analysis``
    display flag of the overview (§2.5.2) — start honouring it at once, because
    both go through :meth:`PlantDiaryService.evaluate_request_permission`.
    """
    return True


@lru_cache(maxsize=1)
def _ephemeral_lease_secret() -> str:
    """Process-local fallback secret for lease tokens, generated once.

    Only reached when neither ``jwt_secret_key`` nor ``fernet_key`` carries a
    strong value. Tokens stay unforgeable, but they do not survive a restart and
    are not shared across replicas: an agent that claimed before the restart then
    gets ``conflict.lease_expired`` on submit and the entry returns to the queue
    when its lease runs out. Recoverable, but it is a misconfiguration — mirrors
    the local-fs signing-secret fallback in ``data_access/storage/registry.py``.
    """
    logger.warning(
        "diary_lease_secret_ephemeral",
        reason="no_strong_signing_secret_configured",
        detail=(
            "Derived REQ-050 analysis lease tokens from an ephemeral process-local secret. "
            "Set a strong JWT_SECRET_KEY, otherwise in-flight leases become invalid after a "
            "restart and across replicas."
        ),
    )
    return secrets.token_hex(32)


def _lease_signing_secret() -> str:
    """Resolve the secret the lease token is derived from (SEC-009).

    The documented chain is ``jwt_secret_key`` → ``fernet_key`` → ephemeral, and
    the candidates are therefore tested **one at a time**. Written as
    ``settings.jwt_secret_key or settings.fernet_key`` the chain silently loses
    its middle link: an instance that left ``JWT_SECRET_KEY`` at the shipped
    placeholder produces a *truthy* first operand, so ``or`` short-circuits and
    ``fernet_key`` is never consulted — a configured Fernet key would be skipped
    and every lease token would come from a process-local secret that does not
    survive a restart or reach a second replica.
    """
    for candidate in (settings.jwt_secret_key, settings.fernet_key):
        if candidate and candidate != _KNOWN_DEFAULT_JWT_SECRET:
            return candidate
    return _ephemeral_lease_secret()


def _canonical_timestamp(value: datetime | str | None) -> str:
    """Normalise a timestamp to one canonical UTC spelling, or ``""``.

    The lease token is derived from timestamps, so the *spelling* matters: a
    value stored as ``…Z`` and one stored as ``…+00:00`` denote the same instant
    but would produce different tokens. Everything is funnelled through
    ``ensure_aware_utc`` and re-rendered here, so the token depends on the
    instant and not on who wrote it.
    """
    moment = ensure_aware_utc(value)
    return moment.astimezone(UTC).isoformat() if moment else ""


def derive_lease_token(
    *,
    entry_key: str,
    claimed_by: str,
    claimed_at: datetime | str | None,
    lease_expires_at: datetime | str | None,
) -> str:
    """Derive the opaque lease token handed to the claiming agent (§4.2).

    **Where the token lives, and why it is derived rather than stored.**
    REQ-050 §5 lists no field for it, and this keeps the persisted shape exactly
    as specified. The token is a keyed hash (HMAC-SHA256, server secret) over the
    entry and the *current* lease, which buys three properties a stored random
    token would not:

    * it cannot be guessed by another tenant member who can see ``claimed_at``
      and ``claimed_by`` in the UI — without the secret the inputs are useless;
    * it cannot drift from the lease it belongs to. Re-claiming an entry changes
      ``analysis_claimed_at``/``analysis_lease_expires_at``, which invalidates the
      previous token automatically. That is precisely the semantics §4.5 asks
      for ("passt nicht zum aktuellen Lease") with no second piece of state to
      keep in sync;
    * it binds to *this* entry, so a token cannot be replayed against another.

    The cost is that a secret must be configured for multi-replica deployments
    (see :func:`_ephemeral_lease_secret`).

    **The derivation is domain-separated** (SEC-009). The signing secret is not
    exclusive to this protocol — the same ``jwt_secret_key`` / ``fernet_key``
    chain also backs the local-fs download tokens — so the payload is prefixed
    with :data:`_LEASE_PURPOSE`. Without a purpose label two protocols that
    happened to hash a structurally identical string under the same key would
    produce the same digest, and a token minted for one would verify in the
    other. The label carries a version so the derivation can be changed later
    without ambiguity; changing it invalidates in-flight leases, which is
    recoverable (the entry returns to the queue when its lease runs out).
    """
    payload = "|".join(
        [
            _LEASE_PURPOSE,
            entry_key,
            claimed_by,
            _canonical_timestamp(claimed_at),
            _canonical_timestamp(lease_expires_at),
        ]
    )
    return hmac.new(
        _lease_signing_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_light_mode() -> bool:
    """Whether this instance runs in the anonymous Light mode (REQ-027)."""
    return settings.kamerplanter_mode != "full"


def lease_expired(entry: PlantDiaryEntry, now: datetime | None = None) -> bool:
    """Whether ``entry``'s analysis lease has run out (§2.2).

    A claimed entry **without** a deadline counts as expired: it can only come
    from a partial write, and the alternative reading — "no deadline, so it never
    expires" — is exactly the permanent block the lease exists to prevent.
    """
    if entry.analysis_state != DiaryAnalysisState.IN_PROGRESS:
        return False
    expires_at = ensure_aware_utc(entry.analysis_lease_expires_at)
    if expires_at is None:
        return True
    return expires_at <= (now or now_utc())


def effective_analysis_state(entry: PlantDiaryEntry, now: datetime | None = None) -> DiaryAnalysisState:
    """The state a reader should *display*, without writing anything (§2.5.2).

    An entry whose lease has run out is back in the work queue even though the
    stored value still says ``in_progress`` — the reset happens on the next write
    to the entry (see :meth:`PlantDiaryService.request_analysis`). A read path
    that must not write (the overview list) uses this to avoid showing "wird
    analysiert" for an entry every agent may already pick up.
    """
    if lease_expired(entry, now):
        return DiaryAnalysisState.REQUESTED
    return entry.analysis_state


@dataclass(frozen=True, slots=True)
class AnalysisRequestPermission:
    """Whether a user may mark an entry for analysis, and why not (§7.2)."""

    allowed: bool
    #: Machine-readable cause when ``allowed`` is ``False``: ``"role"``,
    #: ``"authorship"`` or ``"consent"``. ``None`` when allowed.
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DiaryAnalysisClaim:
    """Result of a successful claim — what §4.2 returns to the agent."""

    entry: PlantDiaryEntry
    lease_token: str
    lease_expires_at: datetime

    @property
    def entry_key(self) -> str:
        return self.entry.key or ""

    @property
    def photo_count(self) -> int:
        return len(self.entry.photo_refs)


def evaluate_analysis_request_permission(
    entry: PlantDiaryEntry,
    *,
    user_key: str,
    role: TenantRole,
    consent_granted: bool,
    light_mode: bool,
) -> AnalysisRequestPermission:
    """Decide whether ``user_key`` may mark ``entry`` for analysis (§7.2, §7.5).

    The rule lives here **once** and is evaluated server-side twice: to enforce
    the marking, and to fill the ``can_request_analysis`` flag of the overview
    (§2.5.2, AK-18a). Rebuilding it in the frontend would mean maintaining it in
    two places and forgetting one of them at the next change; and the flag is a
    display aid, never an authorisation — the enforcement path re-evaluates it.

    Three gates, in order of how much they reveal:

    1. **Role** (§6): observers never mark, anywhere.
    2. **Consent** (§7.1): the purpose ``diary_ai_analysis`` is revocable, and a
       revocation blocks *new* markings while leaving existing results alone.
    3. **Authorship** (§7.2): in a shared tenant a grower may only hand *their
       own* observations and photos to a language model. Marking someone else's
       entry is a lead decision.

    In Light mode gates 2 and 3 fall away (§7.5): there is nobody who could grant
    a consent, and every entry belongs to the same system user, so "only my own"
    has no one to protect. The role gate stays.
    """
    role = TenantRole(role)
    if role not in _WRITING_ROLES:
        return AnalysisRequestPermission(allowed=False, reason="role")
    if light_mode:
        return AnalysisRequestPermission(allowed=True)
    if not consent_granted:
        return AnalysisRequestPermission(allowed=False, reason="consent")
    is_author = bool(user_key) and entry.created_by == user_key
    if role != TenantRole.LEAD and not is_author:
        return AnalysisRequestPermission(allowed=False, reason="authorship")
    return AnalysisRequestPermission(allowed=True)


class PlantDiaryService:
    """Service for managing plant diary entries."""

    def __init__(
        self,
        diary_repo: IPlantDiaryRepository,
        run_repo: IPlantingRunRepository | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
        consent_checker: ConsentChecker | None = None,
        attachment_repo: IAttachmentRepository | None = None,
        environment_service_factory: Callable[[], EnvironmentSnapshotService | None] | None = None,
    ) -> None:
        self._repo = diary_repo
        self._run_repo = run_repo
        self._plant_repo = plant_repo
        #: REQ-013 §2.3a — resolves the plant's environment on create.
        #:
        #: A **factory**, not an instance, and the distinction is load-bearing:
        #: the snapshot service owns six repositories and a Home Assistant
        #: client, none of which this service needs in order to exist. Injecting
        #: the built object made merely *assembling* the diary service open a
        #: database connection, so a unit test about consent wiring — which
        #: touches no environment at all — started needing infrastructure and
        #: failed in CI. It is the same shape ``ActuatorService`` already uses
        #: for ``ha_client_factory``: resolve the collaborator when the work
        #: actually happens.
        #:
        #: ``None`` (or a factory answering ``None``) means "this installation
        #: does not capture", recorded honestly as ``not_attempted`` rather than
        #: silently looking like "we looked and found nothing".
        self._environment_service_factory = environment_service_factory
        #: REQ-050 §7.1 hook — see :func:`_consent_not_evaluated`.
        self._consent_checker = consent_checker or _consent_not_evaluated
        #: SEC-003 — resolves a ``photo_refs`` entry to its attachment record so
        #: tenant, category and uploader can be checked. ``None`` only in the
        #: unit tests that exercise the analysis state machine and never attach a
        #: photo; a *reference* that arrives without a resolver is refused rather
        #: than accepted (see :meth:`_require_attachable_photos`), so a missing
        #: wiring fails closed instead of silently disabling the guard.
        self._attachment_repo = attachment_repo

    def create_entry(
        self,
        plant_key: str,
        entry: PlantDiaryEntry,
        run_key: str | None = None,
        *,
        actor_role: TenantRole,
        capture_environment: bool = True,
    ) -> PlantDiaryEntry:
        """Create a diary entry for a plant.

        If run_key is provided, validates that the plant belongs to the run.

        **The environment snapshot is taken here, and only here** (REQ-013
        §2.3a). ``capture_environment`` is the author's opt-out from the create
        dialog — it says whether to *look*, never what to store; the values
        themselves come from the plant's own location and whatever the caller put
        on ``entry.environment`` is overwritten unconditionally, so the snapshot
        cannot be supplied, shaped or forged through the request body. Capture
        happens on create only: :meth:`update_entry` protects the three fields.

        ``photo_refs`` is validated against the attachment catalogue before
        anything is written (SEC-003): until now it was free-form input that
        nothing ever looked at. See :meth:`_require_attachable_photos` for the
        four rules and why authorship is one of them.

        ``actor_role`` is required and keyword-only. It is only ever used to let
        a tenant lead attach a photo they did not upload — the same exception
        §7.2 already grants for marking someone else's entry — and making it
        required is what stops a future call site from defaulting the guard into
        "everyone is a lead".
        """
        if run_key and self._run_repo:
            plants = self._run_repo.get_run_plants(run_key, include_detached=False)
            plant_keys = {p.get("_key", "") for p in plants}
            if plant_key not in plant_keys:
                raise NotFoundError("PlantInstance in Run", plant_key)

        self._require_attachable_photos(
            entry.photo_refs,
            tenant_key=entry.tenant_key,
            user_key=entry.created_by,
            role=actor_role,
        )

        entry.plant_key = plant_key
        snapshot = self._capture_environment(
            plant_key,
            tenant_key=entry.tenant_key,
            requested=capture_environment,
        )
        entry.environment = snapshot.readings
        entry.environment_captured_at = snapshot.captured_at
        entry.environment_status = snapshot.status
        now = now_utc()
        entry.created_at = now
        entry.updated_at = now
        return self._repo.create(entry)

    def _capture_environment(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        requested: bool,
    ) -> EnvironmentSnapshot:
        """Resolve the snapshot, and never let it stop the write.

        The snapshot service already degrades internally; this second net exists
        because the promise here is absolute. A grower documenting a problem is
        the worst possible moment to refuse an entry over a sensor — so any
        escape at all is recorded as ``unavailable`` and the entry is written.

        **Building the collaborator is itself a fallible step**, which is why it
        sits in its own ``try``: the factory reaches for repositories and a Home
        Assistant client, and a database that is down there means "we tried and
        could not" (``unavailable``) — not "this installation does not capture"
        (``not_attempted``). Collapsing the two would file an infrastructure
        outage as a deliberate configuration choice.
        """
        if not requested:
            return EnvironmentSnapshot.opted_out()
        if self._environment_service_factory is None:
            return EnvironmentSnapshot.not_attempted()
        try:
            environment_service = self._environment_service_factory()
        except Exception as exc:  # noqa: BLE001 — a snapshot never fails a write
            logger.warning(
                "diary_environment_service_unavailable",
                plant_key=plant_key,
                tenant_key=tenant_key,
                error=str(exc),
            )
            return self._degraded_snapshot()
        if environment_service is None:
            return EnvironmentSnapshot.not_attempted()
        try:
            return environment_service.capture_for_plant(plant_key, tenant_key=tenant_key)
        except Exception as exc:  # noqa: BLE001 — a snapshot never fails a write
            logger.warning(
                "diary_environment_capture_skipped",
                plant_key=plant_key,
                tenant_key=tenant_key,
                error=str(exc),
            )
            return self._degraded_snapshot()

    @staticmethod
    def _degraded_snapshot() -> EnvironmentSnapshot:
        """A capture that was attempted and did not get through (REQ-013 §2.3a)."""
        return EnvironmentSnapshot(
            readings=[],
            status=DiaryEnvironmentStatus.UNAVAILABLE,
            captured_at=now_utc(),
        )

    def get_entry(self, key: str) -> PlantDiaryEntry:
        """Get a single diary entry by key."""
        entry = self._repo.get_or_raise(key)
        return entry

    def update_entry(
        self,
        key: str,
        data: dict,
        *,
        tenant_key: str,
        user_key: str,
        actor_role: TenantRole,
    ) -> PlantDiaryEntry:
        """Update a diary entry. Protects immutable fields.

        The REQ-050 analysis fields are protected too. They are not editable
        content: they say who may currently write the result, and setting them
        here would walk past the lease that stops two agents from analysing the
        same entry. Today no request schema carries them — this makes that a
        property of the service rather than of the schema that happens to sit in
        front of it (§2.2).

        ``photo_refs`` is **not** in that protected set — an entry's photos are
        editable content — so it is validated instead (SEC-003). Only the
        *newly added* references are checked, not the ones already on the stored
        entry: the guard exists to stop a member from pulling a foreign photo
        into an analysis, and re-judging an entry's existing references would
        turn documents written before this rule into documents nobody can edit
        any more. The permitted set therefore only ever grows through a checked
        addition.
        """
        existing, _rev = self._load_scoped(key, tenant_key)
        if "photo_refs" in data:
            self._require_attachable_photos(
                data.get("photo_refs") or [],
                tenant_key=tenant_key,
                user_key=user_key,
                role=actor_role,
                already_attached=existing.photo_refs,
            )
        protected_fields = {"key", "plant_key", "created_by", "created_at"} | _ANALYSIS_FIELDS | _ENVIRONMENT_FIELDS
        for field, value in data.items():
            if hasattr(existing, field) and field not in protected_fields:
                setattr(existing, field, value)
        existing.updated_at = now_utc()
        return self._repo.update(key, existing)

    def _require_attachable_photos(
        self,
        photo_refs: Sequence[str],
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        already_attached: Sequence[str] = (),
    ) -> None:
        """Refuse a ``photo_refs`` entry the author may not hand to a model (SEC-003).

        ``photo_refs`` used to be accepted verbatim: no existence check, no
        tenant check, no category check, no bound. Delivery is tenant-bound, so
        this was never a cross-tenant leak — but **inside** a shared tenant it
        defeated §7.2 completely. That rule ("markieren darf nur, wer den Eintrag
        selbst verfasst hat") is justified in the requirement by the sentence that
        a member should not hand "die Notizen **und Fotos** anderer Mitglieder"
        to a language model unasked. It held for the notes and not for the
        photos: a grower wrote an entry of their *own*, put another member's
        attachment id in it, marked it — author, so the gate opened — and their
        external model received the foreign image.

        Four rules, all evaluated before anything is written:

        1. **Bound** — at most :data:`MAX_PHOTO_REFS` (REQ-013 §2.3). Also on the
           domain model; here it also covers a caller that bypasses the schema.
        2. **Exists and is in this tenant** — resolved through the tenant-scoped
           :meth:`IAttachmentRepository.get`. A missing *and* a foreign
           attachment get the same answer, so the endpoint is not an oracle for
           attachment ids of other tenants (AK-12).
        3. **Category is ``diary``** — an entry must not point at a gallery
           photo, an IPM image, a pest reference or an export archive. §4.4
           hands renditions of whatever is listed here to an external model.
        4. **Uploaded by the author, unless the actor leads the tenant** — the
           §7.2 rule applied to the photo instead of only to the entry. A lead
           may already mark someone else's entry, so refusing them the weaker
           action would be inconsistent. In Light mode the rule falls away for
           the reason §7.5 gives: one system user, nobody to protect from whom.

        ``already_attached`` grandfathers the references an entry carries
        already; see :meth:`update_entry`.
        """
        refs = list(photo_refs)
        if len(refs) > MAX_PHOTO_REFS:
            raise ValidationError(
                f"A diary entry carries at most {MAX_PHOTO_REFS} photos.",
                details=[{"field": "photo_refs", "message": f"max {MAX_PHOTO_REFS} entries"}],
            )

        known = set(already_attached)
        added = [ref for ref in dict.fromkeys(refs) if ref not in known]
        if not added:
            return

        if self._attachment_repo is None:
            # Fail closed. A service assembled without the resolver cannot judge
            # a reference, and accepting it "for now" is exactly how a guard ends
            # up inert in production while every test still passes.
            raise ValidationError(
                "Diary photo references cannot be validated: no attachment catalogue is configured.",
                details=[{"field": "photo_refs", "message": "attachment lookup unavailable"}],
            )

        light = is_light_mode()
        for ref in added:
            attachment = self._attachment_repo.get(ref, tenant_key)
            if attachment is None or attachment.category != _DIARY_PHOTO_CATEGORY:
                # One answer for "does not exist", "belongs to another tenant"
                # and "is not a diary photo" — the three are indistinguishable to
                # the caller on purpose.
                raise ValidationError(
                    f"'{ref}' is not a diary photo of this tenant.",
                    details=[{"field": "photo_refs", "message": f"unknown diary attachment '{ref}'"}],
                )
            if light or role == TenantRole.LEAD:
                continue
            if attachment.created_by != user_key:
                raise ForbiddenError("Only the uploader of a photo, or a tenant lead, may attach it to a diary entry.")

    def delete_entry(self, key: str) -> bool:
        """Delete a diary entry. Raises NotFoundError if missing."""
        self.get_entry(key)
        return self._repo.delete(key)

    def list_entries_for_plant(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """List one plant's diary entries inside ``tenant_key`` (SEC-002).

        The tenant travels all the way down to the query; see
        :meth:`~app.domain.interfaces.plant_diary_repository.IPlantDiaryRepository.get_by_plant`
        for why it is not enough to check it in the endpoint.
        """
        return self._repo.get_by_plant(plant_key, tenant_key=tenant_key, offset=offset, limit=limit)

    def list_entries_for_run(
        self,
        run_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """List the diary entries of a run's plants inside ``tenant_key`` (SEC-002)."""
        return self._repo.get_by_run(run_key, tenant_key=tenant_key, offset=offset, limit=limit)

    # ── REQ-050 analysis: reading ────────────────────────────────────────────

    def get_entry_for_tenant(self, key: str, tenant_key: str) -> PlantDiaryEntry:
        """Load an entry, refusing anything outside ``tenant_key`` (§4.0).

        A foreign entry raises :class:`NotFoundError` — never a permission error.
        Distinguishing the two would turn the endpoint into an oracle for the
        existence of other tenants' records (AK-12).
        """
        entry, _rev = self._load_scoped(key, tenant_key)
        return entry

    def evaluate_request_permission(
        self,
        entry: PlantDiaryEntry,
        *,
        user_key: str,
        role: TenantRole,
    ) -> AnalysisRequestPermission:
        """Server-side evaluation of §7.2 for one entry and one user.

        The overview (§2.5.2) calls this per row to fill ``can_request_analysis``;
        :meth:`request_analysis` calls it to enforce the same rule. One function,
        two uses — see :func:`evaluate_analysis_request_permission`.
        """
        return evaluate_analysis_request_permission(
            entry,
            user_key=user_key,
            role=role,
            consent_granted=self._consent_checker(user_key),
            light_mode=is_light_mode(),
        )

    def list_pending_analyses(
        self,
        tenant_key: str,
        *,
        limit: int = 20,
        include_stale: bool = True,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """Work queue of one tenant, oldest request first (§4.1).

        ``total`` is the number of waiting entries regardless of ``limit``, so an
        agent knows whether another round is worth it. An empty queue is not an
        error.
        """
        if limit < 1 or limit > MAX_PENDING_LIMIT:
            raise DiaryAnalysisValidationError(
                f"limit must be between 1 and {MAX_PENDING_LIMIT}.",
                field="limit",
            )
        return self._repo.list_pending_analyses(tenant_key, limit=limit, include_stale=include_stale)

    def list_overview(
        self,
        tenant_key: str,
        filters: DiaryOverviewFilter | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """One page of the tenant-wide diary overview (§2.5.2).

        Filtering, sorting and paging all happen in the storage layer, and
        ``total`` is the number of matches across all pages. This method
        deliberately adds nothing on top: a filter re-applied here would narrow
        the page the repository already selected, which is how a list ends up
        shorter than its own ``total``.
        """
        return self._repo.list_overview(tenant_key, filters, offset=offset, limit=limit)

    # ── REQ-050 analysis: user-driven transitions ────────────────────────────

    def request_analysis(
        self,
        key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
    ) -> PlantDiaryEntry:
        """Mark an entry for analysis — ``none|completed|failed → requested``.

        Marking is always an explicit user action (§2.1); nothing in this service
        marks an entry on its own. A repeat analysis is allowed and keeps the
        previous result visible while it waits — it is overwritten only when a
        new result actually arrives (AK-21).
        """
        entry, rev = self._load_scoped(key, tenant_key)
        self._require_request_permission(entry, user_key=user_key, role=role)
        entry, rev = self._release_expired_lease(entry, rev)

        if entry.analysis_state not in _MARKABLE_STATES:
            raise DiaryAnalysisStateError(key, entry.analysis_state.value, DiaryAnalysisState.REQUESTED.value)

        updated, _new_rev = self._repo.update_fields_checked(
            key,
            {
                "analysis_state": DiaryAnalysisState.REQUESTED.value,
                "analysis_requested_at": now_utc().isoformat(),
                "analysis_requested_by": user_key,
                "analysis_claimed_at": None,
                "analysis_claimed_by": None,
                "analysis_lease_expires_at": None,
                # The error belonged to the previous attempt; keeping it would
                # render an error next to "waiting for analysis". The previous
                # *result* is kept on purpose (AK-21).
                "analysis_error": None,
            },
            expected_rev=rev,
        )
        logger.info("diary_analysis_requested", entry_key=key, tenant_key=tenant_key, user_key=user_key)
        return updated

    def cancel_analysis_request(
        self,
        key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
    ) -> PlantDiaryEntry:
        """Withdraw a marking — ``requested → none`` (AK-03).

        Only while the entry is still waiting. Once an agent holds it the data
        has already left the instance, so "un-marking" it would be a promise the
        server cannot keep; the request is refused instead of silently doing
        nothing. An entry whose lease has expired *is* withdrawable again,
        because it is back in the queue.
        """
        entry, rev = self._load_scoped(key, tenant_key)
        self._require_request_permission(entry, user_key=user_key, role=role)
        entry, rev = self._release_expired_lease(entry, rev)

        if entry.analysis_state != DiaryAnalysisState.REQUESTED:
            raise DiaryAnalysisStateError(key, entry.analysis_state.value, DiaryAnalysisState.NONE.value)

        updated, _new_rev = self._repo.update_fields_checked(
            key,
            {
                "analysis_state": DiaryAnalysisState.NONE.value,
                "analysis_requested_at": None,
                "analysis_requested_by": None,
            },
            expected_rev=rev,
        )
        logger.info("diary_analysis_request_cancelled", entry_key=key, tenant_key=tenant_key, user_key=user_key)
        return updated

    # ── REQ-050 analysis: agent-driven transitions ───────────────────────────

    def claim_analysis(
        self,
        key: str,
        *,
        tenant_key: str,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> DiaryAnalysisClaim:
        """Claim an entry exclusively — ``requested → in_progress`` (§4.2).

        The write is a compare-and-set on the revision read a moment earlier, so
        of two agents racing for the same entry exactly one wins; the loser sees
        ``conflict.concurrent_update`` and may retry immediately. An entry that is
        legitimately held answers ``conflict.already_claimed`` and names holder
        and deadline, which is a different decision for the agent: come back
        later, do not retry now.

        Claiming an entry whose lease has expired is allowed and *is* the reset —
        the single write replaces holder, deadline and state at once, so no stale
        ``analysis_claimed_by`` can survive it.
        """
        worker = (worker_id or "").strip()
        if not worker:
            raise DiaryAnalysisValidationError("worker_id must not be empty.", field="worker_id")
        if len(worker) > MAX_WORKER_ID_LENGTH:
            raise DiaryAnalysisValidationError(
                f"worker_id must not exceed {MAX_WORKER_ID_LENGTH} characters.",
                field="worker_id",
            )
        if lease_seconds < 1 or lease_seconds > MAX_LEASE_SECONDS:
            raise DiaryAnalysisValidationError(
                f"lease_seconds must be between 1 and {MAX_LEASE_SECONDS}.",
                field="lease_seconds",
            )

        entry, rev = self._load_scoped(key, tenant_key)
        now = now_utc()
        claimable = entry.analysis_state == DiaryAnalysisState.REQUESTED or lease_expired(entry, now)
        if not claimable:
            raise DiaryAnalysisAlreadyClaimedError(
                key,
                claimed_by=entry.analysis_claimed_by,
                lease_expires_at=_canonical_timestamp(entry.analysis_lease_expires_at) or None,
            )

        expires_at = now + timedelta(seconds=lease_seconds)
        claimed_at_iso = _canonical_timestamp(now)
        expires_at_iso = _canonical_timestamp(expires_at)
        updated, _new_rev = self._repo.update_fields_checked(
            key,
            {
                "analysis_state": DiaryAnalysisState.IN_PROGRESS.value,
                "analysis_claimed_at": claimed_at_iso,
                "analysis_claimed_by": worker,
                "analysis_lease_expires_at": expires_at_iso,
                # A retry after a failed attempt starts clean.
                "analysis_error": None,
            },
            expected_rev=rev,
        )
        token = derive_lease_token(
            entry_key=key,
            claimed_by=worker,
            claimed_at=claimed_at_iso,
            lease_expires_at=expires_at_iso,
        )
        logger.info(
            "diary_analysis_claimed",
            entry_key=key,
            tenant_key=tenant_key,
            worker_id=worker,
            lease_expires_at=expires_at_iso,
        )
        return DiaryAnalysisClaim(entry=updated, lease_token=token, lease_expires_at=expires_at)

    def submit_analysis(
        self,
        key: str,
        *,
        tenant_key: str,
        lease_token: str,
        status: DiaryAnalysisState | str,
        summary: str | None = None,
        findings: Sequence[dict[str, Any]] | None = None,
        recommended_actions: Sequence[str] | None = None,
        analyzed_photo_ids: Sequence[str] | None = None,
        model: str = "",
        recipe_version: str = "",
        error: str | None = None,
    ) -> PlantDiaryEntry:
        """Write the result back and end the claim (§4.5).

        Order of checks is deliberate: state, then lease, then payload. A caller
        who no longer holds the entry learns exactly that and gets no validation
        feedback about a document that is not theirs.

        A ``completed`` submission replaces the previous result **whole** — no
        findings are merged from an earlier run (AK-21). A ``failed`` one records
        the error and leaves an earlier successful result in place: the retry
        failed, that is not a reason to destroy what the user already had.
        """
        target = self._parse_submit_status(status)
        entry, rev = self._load_scoped(key, tenant_key)

        if entry.analysis_state != DiaryAnalysisState.IN_PROGRESS:
            raise DiaryAnalysisNotClaimedError(key, entry.analysis_state.value)
        if lease_expired(entry):
            # Free the entry on the way out: a crashed agent that reports back
            # late must not leave its name on a lease nobody holds any more. If
            # someone else won the entry in the meantime the reset is already
            # done for us — the caller's answer is the same either way.
            try:
                self._release_expired_lease(entry, rev)
            except DiaryAnalysisConcurrentUpdateError:
                logger.info("diary_analysis_lease_release_race", entry_key=key)
            raise DiaryAnalysisLeaseExpiredError(key)
        if not self._lease_token_matches(entry, lease_token):
            raise DiaryAnalysisLeaseExpiredError(key)

        fields: dict[str, Any] = {
            "analysis_state": target.value,
            "analysis_lease_expires_at": None,
        }
        if target == DiaryAnalysisState.COMPLETED:
            analysis = self._build_analysis(
                entry,
                summary=summary,
                findings=findings,
                recommended_actions=recommended_actions,
                analyzed_photo_ids=analyzed_photo_ids,
                model=model,
                recipe_version=recipe_version,
            )
            fields["analysis"] = analysis.model_dump(mode="json")
            fields["analysis_error"] = None
        else:
            fields["analysis_error"] = self._validated_error_text(error)

        updated, _new_rev = self._repo.update_fields_checked(key, fields, expected_rev=rev)
        logger.info(
            "diary_analysis_submitted",
            entry_key=key,
            tenant_key=tenant_key,
            worker_id=entry.analysis_claimed_by,
            analysis_state=target.value,
        )
        return updated

    # ── Internals ────────────────────────────────────────────────────────────

    def _load_scoped(self, key: str, tenant_key: str) -> tuple[PlantDiaryEntry, str]:
        """Load an entry inside one tenant, together with its revision."""
        if not tenant_key:
            raise ValueError("Diary analysis operations are tenant-scoped and require a non-empty tenant_key.")
        loaded = self._repo.get_with_revision(key)
        if loaded is None:
            raise NotFoundError("PlantDiaryEntry", key)
        entry, rev = loaded
        if entry.tenant_key != tenant_key:
            # Same answer as "does not exist" on purpose (§4.0, AK-12).
            raise NotFoundError("PlantDiaryEntry", key)
        return entry, rev

    def _require_request_permission(
        self,
        entry: PlantDiaryEntry,
        *,
        user_key: str,
        role: TenantRole,
    ) -> None:
        """Enforce §7.2, translating the refusal into the matching error."""
        permission = self.evaluate_request_permission(entry, user_key=user_key, role=role)
        if permission.allowed:
            return
        if permission.reason == "consent":
            raise ConsentRequiredError("diary_ai_analysis")
        if permission.reason == "authorship":
            raise ForbiddenError("Only the author of a diary entry, or a tenant lead, may mark it for analysis.")
        raise ForbiddenError("Marking a diary entry for analysis requires at least the grower role.")

    def _release_expired_lease(self, entry: PlantDiaryEntry, rev: str) -> tuple[PlantDiaryEntry, str]:
        """Put an entry with a run-out lease back into ``requested`` (AK-06).

        **Why the fields are written as ``None`` through the partial-update path:**
        the full-model write dumps with ``exclude_none=True``, so a cleared
        ``analysis_claimed_by`` would simply not reach the document and the
        crashed agent's name would stay on an entry it no longer holds — an entry
        that *looks* claimed while everyone is free to claim it.

        The reset happens on **write** access, not on read. The work queue finds
        stale entries on its own (``include_stale``), so an entry reappears even
        if nobody ever touches it — a read path that had to write first would
        make the queue depend on someone having called the right method.
        """
        if not lease_expired(entry):
            return entry, rev
        released, new_rev = self._repo.update_fields_checked(
            entry.key or "",
            {
                "analysis_state": DiaryAnalysisState.REQUESTED.value,
                "analysis_claimed_at": None,
                "analysis_claimed_by": None,
                "analysis_lease_expires_at": None,
            },
            expected_rev=rev,
        )
        logger.info(
            "diary_analysis_lease_released",
            entry_key=entry.key,
            previous_worker_id=entry.analysis_claimed_by,
        )
        return released, new_rev

    def _lease_token_matches(self, entry: PlantDiaryEntry, presented: str) -> bool:
        """Constant-time comparison against the token of the live lease."""
        expected = derive_lease_token(
            entry_key=entry.key or "",
            claimed_by=entry.analysis_claimed_by or "",
            claimed_at=entry.analysis_claimed_at,
            lease_expires_at=entry.analysis_lease_expires_at,
        )
        return hmac.compare_digest(expected, presented or "")

    @staticmethod
    def _parse_submit_status(status: DiaryAnalysisState | str) -> DiaryAnalysisState:
        """Accept only the two terminal states a submission may report (§4.5)."""
        try:
            parsed = DiaryAnalysisState(status)
        except ValueError as exc:
            raise DiaryAnalysisValidationError(
                "status must be 'completed' or 'failed'.",
                field="status",
            ) from exc
        if parsed not in (DiaryAnalysisState.COMPLETED, DiaryAnalysisState.FAILED):
            raise DiaryAnalysisValidationError("status must be 'completed' or 'failed'.", field="status")
        return parsed

    @staticmethod
    def _validated_error_text(error: str | None) -> str:
        """Validate the mandatory error text of a failed submission (AK-22)."""
        text = (error or "").strip()
        if not text:
            raise DiaryAnalysisValidationError("error is required when status is 'failed'.", field="error")
        if len(text) > MAX_ERROR_LENGTH:
            raise DiaryAnalysisValidationError(
                f"error must not exceed {MAX_ERROR_LENGTH} characters.",
                field="error",
            )
        return text

    def _build_analysis(
        self,
        entry: PlantDiaryEntry,
        *,
        summary: str | None,
        findings: Sequence[dict[str, Any]] | None,
        recommended_actions: Sequence[str] | None,
        analyzed_photo_ids: Sequence[str] | None,
        model: str,
        recipe_version: str,
    ) -> DiaryAnalysis:
        """Validate a completed submission and attach the server's disclaimer.

        The bounds of §4.5 are enforced by the domain model (§5) rather than
        re-implemented here, so there is one definition of "too long"; a model
        rejection is translated into the contract's ``validation.error``. Only
        the rules the model cannot express live in this method: the mandatory
        summary, and the requirement that every analysed photo id actually hangs
        on this entry — an agent reporting on a photo the entry does not have has
        analysed something else, and storing that would misattribute a finding.
        """
        text = (summary or "").strip()
        if not text:
            raise DiaryAnalysisValidationError("summary is required when status is 'completed'.", field="summary")

        photo_ids = list(analyzed_photo_ids or [])
        unknown = [photo_id for photo_id in photo_ids if photo_id not in entry.photo_refs]
        if unknown:
            raise DiaryAnalysisValidationError(
                f"analyzed_photo_ids contains ids that are not attached to this entry: {', '.join(unknown)}.",
                field="analyzed_photo_ids",
            )

        actions = list(recommended_actions or [])
        for action in actions:
            if len(action) > MAX_RECOMMENDED_ACTION_LENGTH:
                raise DiaryAnalysisValidationError(
                    f"recommended_actions entries must not exceed {MAX_RECOMMENDED_ACTION_LENGTH} characters.",
                    field="recommended_actions",
                )

        try:
            return DiaryAnalysis(
                summary=text,
                findings=list(findings or []),
                recommended_actions=actions,
                analyzed_photo_ids=photo_ids,
                model=model,
                recipe_version=recipe_version,
                analyzed_at=now_utc(),
                # AK-11: set here, never taken from the agent. A recipe that
                # sends its own field is ignored — this is the whole point.
                disclaimer=ANALYSIS_DISCLAIMER,
            )
        except PydanticValidationError as exc:
            raise DiaryAnalysisValidationError(_first_model_error(exc)) from exc


def _first_model_error(exc: PydanticValidationError) -> str:
    """Render the first model violation as a caller-facing sentence.

    Deliberately terse: the field path plus pydantic's own message, no internal
    types, no stack (NFR-006).
    """
    errors = exc.errors()
    if not errors:  # pragma: no cover - pydantic always reports at least one
        return "The submitted analysis is invalid."
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ())) or "analysis"
    return f"{location}: {first.get('msg', 'invalid value')}"


__all__ = [
    "ANALYSIS_DISCLAIMER",
    "DEFAULT_LEASE_SECONDS",
    "MAX_LEASE_SECONDS",
    "MAX_PENDING_LIMIT",
    "AnalysisRequestPermission",
    "ConsentChecker",
    "DiaryAnalysisClaim",
    "PlantDiaryService",
    "derive_lease_token",
    "effective_analysis_state",
    "evaluate_analysis_request_permission",
    "is_light_mode",
    "lease_expired",
]
