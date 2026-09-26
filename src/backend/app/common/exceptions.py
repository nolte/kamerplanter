import re
from typing import Any

from app.common.error_ids import new_error_id


class KamerplanterError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self.error_id = new_error_id()
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


def normalise_entity_name(entity: str) -> str:
    """Fold an entity name into the stable, machine-readable form ``details[0].entity`` carries.

    The ~150 raisers spell the same kind of thing every which way — ``"Task"``,
    ``"attachment"``, ``"PlantInstance"``, ``"memberships"``,
    ``"nutrient plan phase entry"``. Echoing that verbatim would hand a client a
    value that changes whenever someone re-words a raiser, and would make
    ``entity == "attachment"`` depend on a capital letter. Normalising here, once,
    is what makes the field a contract rather than a debug string.

    ``snake_case`` because that is the spelling the rest of the wire uses
    (NFR-006 §2.1 fields, every payload key). Idempotent: feeding an already
    normalised name back through returns it unchanged.
    """
    spaced = re.sub(r"[\s\-]+", "_", entity.strip())
    # Two boundaries, so acronyms fold the way a reader expects:
    # ``OidcProviderConfig`` -> ``oidc_provider_config``, not ``o_idc_…``.
    spaced = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", spaced)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", spaced)
    return re.sub(r"_+", "_", spaced).strip("_").lower()


class NotFoundError(KamerplanterError):
    """404 with a machine-readable ``entity``, so two 404s can be told apart (#1437).

    Every subclass of this one — ``AttachmentNotFoundError`` among them — carries
    ``error_code="ENTITY_NOT_FOUND"``, so a route that resolves a parent and then a
    child answers the *same* code for "the parent is gone" and "the child is gone",
    differing only in the English ``message``. A client that has to act differently
    on the two (``PhotoUpload`` must de-stage a photo only when the **attachment**
    is the missing thing, never when the task is) had nothing to branch on.

    The signal is therefore additive: the code and the status are unchanged, and
    ``details[0]["entity"]`` names the missing entity in normalised form. Set here
    for *every* ``NotFoundError`` rather than on one subclass — a field only one
    branch populates is the exception a client then has to special-case.
    """

    def __init__(self, entity: str, key: str) -> None:
        super().__init__(
            message=f"{entity} with key '{key}' not found.",
            error_code="ENTITY_NOT_FOUND",
            status_code=404,
            details=[
                {
                    "field": "key",
                    "reason": f"No {entity} with key '{key}'.",
                    "code": "ENTITY_NOT_FOUND",
                    "entity": normalise_entity_name(entity),
                }
            ],
        )


class DuplicateError(KamerplanterError):
    def __init__(self, entity: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{entity} with {field}='{value}' already exists.",
            error_code="DUPLICATE_ENTRY",
            status_code=409,
            details=[{"field": field, "reason": f"Value '{value}' is already taken.", "code": "DUPLICATE_ENTRY"}],
        )


class WriteConflictError(KamerplanterError):
    """ArangoDB refused a write as a write-write conflict (error code ``1200``).

    Strictly distinct from :class:`DuplicateError` (code ``1210``), and the
    distinction is the whole point of having a second type:

    * ``1210`` — *unique constraint violated* — is a statement **about the
      data**: a committed, visible document already occupies the unique key. A
      caller may safely read it as "an equivalent record exists".
    * ``1200`` — *conflict* — is a statement **about timing**: a concurrent
      transaction holds the same document key or unique-index entry and this
      write could not be serialized against it. It says nothing about whether
      that other transaction went on to commit or to roll back, so it must
      **never** be read as "an equivalent record exists". A caller that wants
      that answer has to re-read and see for itself.

    ``python-arango`` keeps the same separation: :data:`arango.errno.CONFLICT`
    (1200) is a different constant from
    :data:`arango.errno.UNIQUE_CONSTRAINT_VIOLATED` (1210), and the driver's own
    bulk paths turn a per-document ``1200`` into ``DocumentRevisionError`` — a
    revision/serialization failure — never into a uniqueness verdict.

    409 like :class:`DuplicateError`, because the request is well-formed and
    conflicts with the current state; a retry is the appropriate reaction.
    """

    def __init__(self, entity: str, reason: str = "a concurrent write held the same key") -> None:
        super().__init__(
            message=f"Write on '{entity}' conflicted with a concurrent write: {reason}.",
            error_code="WRITE_CONFLICT",
            status_code=409,
            details=[{"field": "key", "reason": reason, "code": "WRITE_CONFLICT"}],
        )


class AccountBeingErasedError(KamerplanterError):
    """The account is closed and queued for erasure, so the e-mail revert cannot restore it (#1848).

    409: the request is well-formed and conflicts with the account's state. The
    revert token stays unspent; the operator can still act within the grace period.
    """

    def __init__(self) -> None:
        super().__init__(
            message="This account is closed and scheduled for deletion. Contact the operator of this installation.",
            error_code="ACCOUNT_BEING_ERASED",
            status_code=409,
        )


class PhaseTransitionError(KamerplanterError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="PHASE_TRANSITION_INVALID",
            status_code=422,
        )


class RotationViolationError(KamerplanterError):
    def __init__(self, family: str, slot: str, years: int) -> None:
        super().__init__(
            message=f"Family '{family}' was planted in slot '{slot}' within the last {years} years.",
            error_code="ROTATION_VIOLATION",
            status_code=422,
        )


class CompanionConflictError(KamerplanterError):
    def __init__(self, species_a: str, species_b: str) -> None:
        super().__init__(
            message=f"Species '{species_a}' and '{species_b}' are incompatible companions.",
            error_code="INCOMPATIBLE_COMPANION",
            status_code=422,
        )


class SubstrateExhaustedError(KamerplanterError):
    def __init__(self, batch_id: str, cycles: int) -> None:
        super().__init__(
            message=f"Substrate batch '{batch_id}' has exceeded max reuse cycles ({cycles}).",
            error_code="SUBSTRATE_EXHAUSTED",
            status_code=422,
        )


class ExternalSourceError(KamerplanterError):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(
            message=f"External source '{source}' error: {message}",
            error_code="EXTERNAL_SOURCE_ERROR",
            status_code=502,
        )


class RateLimitError(KamerplanterError):
    def __init__(self, source: str, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(
            message=f"Rate limit exceeded for source '{source}'. Retry after {retry_after}s.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class AdapterNotFoundError(KamerplanterError):
    def __init__(self, source_key: str) -> None:
        super().__init__(
            message=f"No adapter registered for source '{source_key}'.",
            error_code="ADAPTER_NOT_FOUND",
            status_code=404,
            details=[
                {"field": "source_key", "reason": f"Unknown source: '{source_key}'.", "code": "ADAPTER_NOT_FOUND"}
            ],
        )


class InvalidStatusTransitionError(KamerplanterError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            message=f"Cannot transition from '{current}' to '{target}'.",
            error_code="INVALID_STATUS_TRANSITION",
            status_code=422,
        )


class InvalidRunStateError(KamerplanterError):
    def __init__(self, operation: str, status: str) -> None:
        super().__init__(
            message=f"Operation '{operation}' not allowed in status '{status}'.",
            error_code="INVALID_RUN_STATE",
            status_code=409,
        )


class ValidationError(KamerplanterError):
    def __init__(self, message: str, details: list[dict[str, str]] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class OAuthAutoLinkRefusedError(ValidationError):
    """The OAuth address matches a local account, and one side is unverified (#1403).

    A `ValidationError` subclass so existing handlers keep catching it, but its own
    type so the OAuth callback can answer with a code the frontend can explain.
    Without it the case collapses into the generic `provider_error` — "The provider
    reported an error. Please try again later." — which is wrong in both halves:
    the provider reported nothing wrong, and trying again cannot help.

    That matters more since #1403 than before it. A provider that omits
    `email_verified` now refuses the auto-link, and omitting it is the DEFAULT for
    a GitHub provider registered without the `user:email` scope, so this is an
    ordinary path rather than a corner.
    """


class WinterPathViolationError(KamerplanterError):
    """REQ-022 §D5 — ``OverwinteringProfile.winter_action`` contradicts the
    hardiness-derived winter path (in-situ path A vs. relocated path B)."""

    def __init__(self, winter_action: str, path: str, allowed: list[str]) -> None:
        super().__init__(
            message=(
                f"Winter action '{winter_action}' is not allowed on winter path {path}. "
                f"Allowed actions: {', '.join(allowed)}."
            ),
            error_code="WINTER_PATH_VIOLATION",
            status_code=422,
            details=[
                {
                    "field": "winter_action",
                    "reason": (f"Path {path} requires one of {', '.join(allowed)}; got '{winter_action}'."),
                    "code": "WINTER_PATH_VIOLATION",
                }
            ],
        )


class SeasonStateUnavailableError(KamerplanterError):
    """REQ-047 §4.4 — a season state was requested for a site that has none.

    Only outdoor/greenhouse sites run a season state machine; a pure indoor site
    has no season, so the request is well-formed but conflicts with the site's
    type (HTTP 409).
    """

    def __init__(self, site_key: str) -> None:
        super().__init__(
            message=f"Site '{site_key}' has no season state (only outdoor/greenhouse sites do).",
            error_code="SEASON_STATE_UNAVAILABLE",
            status_code=409,
            details=[
                {
                    "field": "site",
                    "reason": "Season states exist only for outdoor/greenhouse sites.",
                    "code": "SEASON_STATE_UNAVAILABLE",
                }
            ],
        )


class FeedExpiredError(KamerplanterError):
    """REQ-015 v1.6 CF-005 — calendar feed past expires_at returns HTTP 410."""

    def __init__(self, feed_key: str) -> None:
        super().__init__(
            message=f"Calendar feed '{feed_key}' has expired.",
            error_code="FEED_EXPIRED",
            status_code=410,
        )


class KarenzViolationError(KamerplanterError):
    def __init__(self, active_ingredient: str, days_remaining: int) -> None:
        super().__init__(
            message=f"Cannot harvest: safety interval for '{active_ingredient}' has {days_remaining} days remaining.",
            error_code="KARENZ_VIOLATION",
            status_code=422,
            details=[
                {
                    "field": "active_ingredient",
                    "reason": f"Safety interval not elapsed: {days_remaining} days remaining.",
                    "code": "KARENZ_VIOLATION",
                }
            ],
        )


class ResistanceWarningError(KamerplanterError):
    def __init__(self, active_ingredient: str, application_count: int) -> None:
        super().__init__(
            message=f"Resistance risk: '{active_ingredient}' applied {application_count} times in rotation window.",
            error_code="RESISTANCE_WARNING",
            status_code=422,
            details=[
                {
                    "field": "active_ingredient",
                    "reason": f"Applied {application_count} times, exceeds maximum consecutive applications.",
                    "code": "RESISTANCE_WARNING",
                }
            ],
        )


class HSTViolationError(KamerplanterError):
    def __init__(self, task_name: str, phase: str, reason: str) -> None:
        super().__init__(
            message=f"HST violation: '{task_name}' not allowed in phase '{phase}'. {reason}",
            error_code="HST_VIOLATION",
            status_code=422,
            details=[
                {
                    "field": "task_name",
                    "reason": reason,
                    "code": "HST_VIOLATION",
                }
            ],
        )


# ── REQ-023 Auth ──


class UnauthorizedError(KamerplanterError):
    def __init__(self, message: str = "Invalid or expired credentials.") -> None:
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenError(KamerplanterError):
    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
        )


class AccountLockedError(KamerplanterError):
    def __init__(self, retry_after_minutes: int) -> None:
        super().__init__(
            message=f"Account temporarily locked. Try again in {retry_after_minutes} minutes.",
            error_code="ACCOUNT_LOCKED",
            status_code=423,
            details=[
                {
                    "field": "account",
                    "reason": f"Too many failed login attempts. Locked for {retry_after_minutes} minutes.",
                    "code": "ACCOUNT_LOCKED",
                }
            ],
        )


class StepUpLockedError(KamerplanterError):
    """A password step-up is locked after too many failures (#1816) — HTTP 429.

    Not :class:`AccountLockedError` (423): the *account* is not locked — signing
    in still works, only the re-confirmation of an irreversible act or a password
    change is held back. ``details[0].retry_after_minutes`` carries the wait so a
    client can render it in its own language.

    Also raised when an e-mailed step-up code may not be issued yet (review
    SEC-002: an unspent code younger than a minute, or the hourly budget spent) —
    same code and detail, so a client needs no second handling, with its own
    ``message`` (``code_issue=True``).
    """

    def __init__(self, retry_after_minutes: int, *, code_issue: bool = False) -> None:
        self.retry_after_minutes = retry_after_minutes
        message = (
            f"No new confirmation code can be sent yet. Try again in {retry_after_minutes} minutes."
            if code_issue
            else f"Too many failed confirmations. Try again in {retry_after_minutes} minutes."
        )
        super().__init__(
            message=message,
            error_code="STEP_UP_LOCKED",
            status_code=429,
            details=[
                {
                    "field": "password",
                    "reason": f"Too many failed step-up confirmations. Locked for {retry_after_minutes} minutes.",
                    "code": "STEP_UP_LOCKED",
                    "retry_after_minutes": str(retry_after_minutes),
                }
            ],
        )


class StepUpCodeRequiredError(KamerplanterError):
    """A step-up needs the e-mailed one-time code and none was sent (#1815) — HTTP 401.

    An account without a local password (federated sign-in only) has no secret of
    its own to re-enter; it confirms an irreversible act or a credential change
    with a code mailed to its address (``POST /users/me/step-up-code``). Its own
    error code, not ``UNAUTHORIZED``, so a client can tell "ask for the code" from
    "the code or password was wrong" without parsing ``message``.
    """

    def __init__(self) -> None:
        super().__init__(
            message="This account confirms with a one-time code sent by e-mail. Request one and send it back.",
            error_code="STEP_UP_CODE_REQUIRED",
            status_code=401,
            details=[
                {
                    "field": "step_up_code",
                    "reason": "Request a confirmation code (POST /api/v1/users/me/step-up-code) and send it back.",
                    "code": "STEP_UP_CODE_REQUIRED",
                }
            ],
        )


class StepUpReauthRequiredError(KamerplanterError):
    """A step-up needs a fresh sign-in at the account's identity provider (#1815) — 401 (422 on code issue).

    The account has no local password but a linked provider that can
    re-authenticate a person freshly (OpenID Connect: Google, a generic OIDC
    provider). It confirms with the one-time ``step_up_token`` that
    ``POST /users/me/step-up/oidc`` leads to — not with the e-mailed code, which
    proves only the mailbox. ``details[0].field`` is ``step_up_token``, the field
    to fill, so a client shows the "sign in again" button rather than the code form.
    """

    def __init__(self, *, status_code: int = 401) -> None:
        super().__init__(
            message=(
                "This account confirms by signing in again at its identity provider. "
                "Start it with POST /api/v1/users/me/step-up/oidc and send the step_up_token back."
            ),
            error_code="STEP_UP_REAUTH_REQUIRED",
            status_code=status_code,
            details=[
                {
                    "field": "step_up_token",
                    "reason": "Sign in again at your identity provider (POST /api/v1/users/me/step-up/oidc).",
                    "code": "STEP_UP_REAUTH_REQUIRED",
                }
            ],
        )


class StepUpPasswordRequiredError(KamerplanterError):
    """The account has a local password and confirms with it — not with a code or a re-authentication (422).

    Answered by ``POST /users/me/step-up-code`` and ``POST /users/me/step-up/oidc``
    (#1815 review), so a client can tell "show the password field" from the other
    422s of those routes without parsing ``message``.
    """

    def __init__(self) -> None:
        super().__init__(
            message="This account confirms with its current password.",
            error_code="STEP_UP_PASSWORD_REQUIRED",
            status_code=422,
            details=[
                {
                    "field": "password",
                    "reason": "Confirm with the current password.",
                    "code": "STEP_UP_PASSWORD_REQUIRED",
                }
            ],
        )


class StepUpReauthUnavailableError(KamerplanterError):
    """No linked provider of the account can re-authenticate freshly — it confirms with the mailed code (422).

    Answered by ``POST /users/me/step-up/oidc`` (#1815 review): GitHub/Apple-only
    links, a link whose configuration is ambiguous or disabled, or a provider
    without a TLS token endpoint. The client shows the e-mailed-code path.
    """

    def __init__(self) -> None:
        super().__init__(
            message="No linked sign-in provider of this account can confirm it; use the e-mailed code.",
            error_code="STEP_UP_REAUTH_UNAVAILABLE",
            status_code=422,
            details=[
                {
                    "field": "step_up_code",
                    "reason": "Request a code with POST /api/v1/users/me/step-up-code.",
                    "code": "STEP_UP_REAUTH_UNAVAILABLE",
                }
            ],
        )


class StepUpReauthFailedError(KamerplanterError):
    """The provider callback of a step-up proves no fresh sign-in of the account (#1815).

    Never rendered as JSON: the callback is a browser redirect, and the route
    turns ``reason`` (``stale`` / ``failed`` / ``cancelled``) into a whitelisted
    error code on the frontend's step-up page. ``action`` is the act the
    re-authentication was for, when the state named one.
    """

    def __init__(self, reason: str, *, action: str | None = None) -> None:
        self.reason = reason
        self.action = action
        #: The starting page's ``client_nonce``, set by the callback handler.
        self.client_nonce: str | None = None
        super().__init__(
            message="The sign-in at the identity provider could not confirm this action.",
            error_code="STEP_UP_REAUTH_FAILED",
            status_code=401,
        )


class StepUpCodeUndeliverableError(KamerplanterError):
    """The step-up code could not be mailed (/code-review of #1862) — HTTP 503.

    The code was withdrawn and its issuance given back, so a retry after the
    operator fixed the mail setup is not held by the one-minute wait or the
    hourly budget. Typically the console e-mail adapter outside ``debug`` or an
    SMTP outage; the requester can only ask the operator.
    """

    def __init__(self) -> None:
        super().__init__(
            message="The confirmation code cannot be delivered by e-mail. Contact the operator of this installation.",
            error_code="STEP_UP_CODE_UNDELIVERABLE",
            status_code=503,
        )


class PayloadTooLargeError(KamerplanterError):
    def __init__(self, max_bytes: int) -> None:
        max_mb = max_bytes / (1024 * 1024)
        super().__init__(
            message=f"File exceeds maximum allowed size of {max_mb:.0f} MB.",
            error_code="PAYLOAD_TOO_LARGE",
            status_code=413,
        )


class UnsupportedMediaTypeError(KamerplanterError):
    def __init__(self, content_type: str, allowed: list[str]) -> None:
        super().__init__(
            message=f"Unsupported file type. Allowed types: {', '.join(allowed)}.",
            error_code="UNSUPPORTED_MEDIA_TYPE",
            status_code=415,
        )


class EmailNotVerifiedError(KamerplanterError):
    def __init__(self) -> None:
        super().__init__(
            message="Email address has not been verified.",
            error_code="EMAIL_NOT_VERIFIED",
            status_code=403,
        )


class InvalidTokenError(KamerplanterError):
    def __init__(self, token_type: str = "token") -> None:
        super().__init__(
            message=f"Invalid or expired {token_type}.",
            error_code="INVALID_TOKEN",
            status_code=401,
        )


# ── NFR-013 Object storage / attachments ──


class StorageQuotaExceededError(KamerplanterError):
    """NFR-013 §5.1 step 1 — tenant attachment quota exceeded."""

    def __init__(self, tenant_key: str, limit_mb: float) -> None:
        super().__init__(
            message=f"Storage quota of {limit_mb:.0f} MB exceeded for this tenant.",
            error_code="STORAGE_QUOTA_EXCEEDED",
            status_code=409,
            details=[
                {
                    "field": "tenant",
                    "reason": f"Tenant '{tenant_key}' has reached its {limit_mb:.0f} MB attachment quota.",
                    "code": "STORAGE_QUOTA_EXCEEDED",
                }
            ],
        )


class PhotoQuotaExceededError(KamerplanterError):
    """REQ-034 §3 (SR-004) — per-instance gallery photo limit reached."""

    def __init__(self, plant_instance_key: str, limit: int) -> None:
        super().__init__(
            message=f"Gallery photo limit of {limit} reached for this plant instance.",
            error_code="PHOTO_QUOTA_EXCEEDED",
            status_code=409,
            details=[
                {
                    "field": "plant_instance",
                    "reason": (
                        f"Plant instance '{plant_instance_key}' already holds the maximum of {limit} gallery photos."
                    ),
                    "code": "PHOTO_QUOTA_EXCEEDED",
                }
            ],
        )


class InvalidFileTypeError(KamerplanterError):
    """NFR-013 §5.1 steps 2 & 3 — type not allowed, or content/MIME mismatch."""

    def __init__(self, declared_mime: str, allowed: list[str]) -> None:
        super().__init__(
            message=f"File type '{declared_mime}' is not allowed. Allowed types: {', '.join(allowed)}.",
            error_code="INVALID_FILE_TYPE",
            status_code=415,
            details=[
                {
                    "field": "file",
                    "reason": f"'{declared_mime}' rejected (not allowed or content does not match declared type).",
                    "code": "INVALID_FILE_TYPE",
                }
            ],
        )


class FileTooLargeError(KamerplanterError):
    """NFR-013 §5.1 step 4 — upload exceeds the per-file size limit."""

    def __init__(self, max_bytes: int) -> None:
        max_mb = max_bytes / (1024 * 1024)
        super().__init__(
            message=f"File exceeds maximum allowed size of {max_mb:.0f} MB.",
            error_code="FILE_TOO_LARGE",
            status_code=413,
        )


class VirusScanRejectedError(KamerplanterError):
    """NFR-013 §5.1 step 5 — the optional virus scan reported a finding."""

    def __init__(self, finding: str = "malware detected") -> None:
        super().__init__(
            message="The uploaded file was rejected by the virus scanner.",
            error_code="VIRUS_SCAN_REJECTED",
            status_code=422,
            details=[{"field": "file", "reason": finding, "code": "VIRUS_SCAN_REJECTED"}],
        )


class AttachmentNotFoundError(NotFoundError):
    """NFR-013 — attachment record not found in the current tenant."""

    def __init__(self, attachment_id: str) -> None:
        super().__init__("attachment", attachment_id)


# ── REQ-029 Plant identification ──


class ConsentRequiredError(KamerplanterError):
    """REQ-029 §5 — processing blocked because a required consent is missing."""

    def __init__(self, purpose: str) -> None:
        super().__init__(
            message=f"Consent for '{purpose}' is required for this action.",
            error_code="CONSENT_REQUIRED",
            status_code=403,
            details=[
                {
                    "field": "consent",
                    "reason": f"Grant consent for '{purpose}' to use this feature.",
                    "code": "CONSENT_REQUIRED",
                }
            ],
        )


class FeatureNotConfiguredError(KamerplanterError):
    """REQ-029 §6.3 — an optional feature is not configured on this instance."""

    def __init__(self, feature: str, hint: str | None = None) -> None:
        message = f"Feature '{feature}' is not configured."
        if hint:
            message = f"{message} {hint}"
        super().__init__(
            message=message,
            error_code="FEATURE_NOT_CONFIGURED",
            status_code=503,
        )


class ErasureIncompleteError(KamerplanterError):
    """An immediate account erasure ran but did not account for every declared step (#1767).

    The platform-admin delete and the unverified-account cleanup run the erasure
    at once instead of after the self-service grace. When the run leaves a
    declared step unreached, the request is recorded ``partially_completed`` with
    a backoff and the daily beat retries it — the duty is persisted, not
    dropped — and the caller is told the account is **not** erased yet.
    """

    def __init__(self, unreached: list[str]) -> None:
        # No request key in the answer (#1767 review SEC-C): the log line
        # ``retention.erasure.steps_unreached`` carries it for the operator.
        super().__init__(
            message=(
                "The account erasure did not finish; it is recorded and retried automatically. "
                f"Unreached steps: {', '.join(unreached)}."
            ),
            error_code="ERASURE_INCOMPLETE",
            status_code=500,
        )


class TenantErasureIncompleteError(KamerplanterError):
    """A tenant deletion ran but something still holds the tenant (#1769).

    The run is recorded ``partially_completed`` with a backoff and the daily
    beat retries it; the caller is told the tenant is **not** fully erased yet.
    The collection names say *where*, never whose — no tenant or account key.
    """

    def __init__(self, unreached: list[str]) -> None:
        super().__init__(
            message=(
                "The tenant deletion did not finish; it is recorded and retried automatically. "
                f"Still holding the tenant: {', '.join(unreached)}."
            ),
            error_code="TENANT_ERASURE_INCOMPLETE",
            status_code=500,
        )


class AiDisabledError(KamerplanterError):
    """REQ-031 §1.3 stage 2 — KI features are disabled for this tenant.

    Distinct from the operator-level stage-1 toggle (``AI_FEATURES_ENABLED``),
    which returns a plain 404 at the router boundary. Body carries the stable
    ``ai.disabled_for_tenant`` marker the frontend keys its hint off.
    """

    def __init__(self) -> None:
        super().__init__(
            message="ai.disabled_for_tenant",
            error_code="AI_DISABLED_FOR_TENANT",
            status_code=403,
            details=[
                {
                    "field": "ai",
                    "reason": "ai.disabled_for_tenant",
                    "code": "AI_DISABLED_FOR_TENANT",
                }
            ],
        )


class AdapterNotAvailableError(KamerplanterError):
    """REQ-034 §4a.3 — the requested recognition adapter cannot be used here.

    A 409 (conflict with the current configuration), not a 503, because the
    caller explicitly chose an adapter (e.g. ``local_embedding`` while the
    inference service is still disabled, or the external path in Light mode
    without the operator opt-in) — the request is well-formed but conflicts with
    the instance's current state.
    """

    def __init__(self, adapter_key: str, reason: str) -> None:
        super().__init__(
            message=f"Recognition adapter '{adapter_key}' is not available: {reason}",
            error_code="ADAPTER_NOT_AVAILABLE",
            status_code=409,
            details=[
                {
                    "field": "adapter",
                    "reason": reason,
                    "code": "ADAPTER_NOT_AVAILABLE",
                }
            ],
        )


class ResourceInUseError(KamerplanterError):
    """A resource cannot be deleted because a dependent state still exists.

    REQ-026 §4: deleting an aquaponic system with a live fish stock, or a fish
    stock that still holds fish, is a 409 conflict — the request is well-formed
    but conflicts with the current state.
    """

    def __init__(self, entity: str, reason: str) -> None:
        super().__init__(
            message=f"{entity} cannot be removed: {reason}",
            error_code="RESOURCE_IN_USE",
            status_code=409,
            details=[{"field": "key", "reason": reason, "code": "RESOURCE_IN_USE"}],
        )


class FeatureDisabledError(KamerplanterError):
    """An optional feature is switched off or not configured.

    REQ-016: the InvenTree integration is optional. When it is disabled (no
    active connection / kill-switch off) an operation that *requires* a live
    connection returns a well-formed 409 conflict instead of crashing (500) —
    the request is valid but conflicts with the current, un-configured state.
    """

    def __init__(self, feature: str, reason: str) -> None:
        super().__init__(
            message=f"{feature} is not available: {reason}",
            error_code="FEATURE_DISABLED",
            status_code=409,
            details=[{"field": "feature", "reason": reason, "code": "FEATURE_DISABLED"}],
        )


# ── REQ-050 Diary AI analysis — state machine, lease, submit contract ──


class ContractError(KamerplanterError):
    """An application error that already carries its **published** error code.

    REQ-050 §4.0 publishes lowercase dotted codes (``conflict.already_claimed``,
    ``validation.error``) as *the* machine-readable contract an external recipe
    branches on — it must never branch on ``message``, which is free to change.
    Subclasses of this class are therefore born with the published code instead
    of a SCREAMING_CASE house code that a transport would have to translate.
    That translation table exists (``_CONTRACT_ERROR_CODES`` in
    ``app/api/v1/mcp/router.py``) precisely because the *generic* errors carry
    the wrong vocabulary for this contract; giving one condition two names is
    the failure this avoids. ``_contract_error_code`` passes an already-dotted
    code through untouched, so these errors reach the MCP wire unchanged and the
    REST alias derives its HTTP status from ``status_code`` as usual.

    Two shapes of ``details`` are kept in parallel, deliberately:

    * :attr:`error_details` — the free-form MCP ``details`` **object** with the
      original value types (``lease_expires_at`` stays a string, not a
      stringified list entry);
    * the inherited ``details`` **list** — the NFR-006 ``ErrorResponse``
      projection, so a REST response stays schema-conformant.

    ``None`` values are kept in :attr:`error_details` (§4.0 wants the key
    present with an explicit ``null`` so the structure is stable across
    responses) but skipped in the NFR-006 list, where a literal ``"None"``
    string would be noise.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.error_details: dict[str, Any] = dict(details or {})
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=[
                {"field": key, "reason": str(value), "code": error_code}
                for key, value in self.error_details.items()
                if value is not None
            ],
        )


class DiaryAnalysisValidationError(ContractError):
    """REQ-050 §4.5 / AK-22 — a submitted analysis violates the input contract.

    Covers every ``validation.error`` case of §4.2 and §4.5: a missing
    ``worker_id``, a ``lease_seconds`` above the ceiling, ``completed`` without a
    ``summary``, ``failed`` without an ``error``, a length limit, a ``confidence``
    outside 0.0–1.0, or a photo id that is not attached to the entry.
    """

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(
            "validation.error",
            message,
            status_code=422,
            details={"field": field} if field else None,
        )


class DiaryAnalysisStateError(ContractError):
    """REQ-050 §2.2 — the requested transition is not allowed from this state.

    Raised for the *user-driven* edges of the state machine (marking and
    un-marking). An invalid transition fails loudly rather than silently doing
    nothing: "un-mark" on an entry an agent is already analysing must not look
    like it worked (AK-03).
    """

    def __init__(self, entry_key: str, current: str, target: str) -> None:
        super().__init__(
            "conflict.invalid_state",
            f"Diary entry cannot move from analysis state '{current}' to '{target}'.",
            status_code=409,
            details={"entry_key": entry_key, "analysis_state": current, "target_state": target},
        )


class DiaryAnalysisAlreadyClaimedError(ContractError):
    """REQ-050 §4.2 — the entry is held by a live lease (AK-05).

    Carries ``claimed_by`` and ``lease_expires_at`` in ``details`` so an agent
    can decide whether to come back later. Strictly distinct from
    :class:`DiaryAnalysisConcurrentUpdateError`, which invites an *immediate*
    retry — collapsing the two would make every agent either give up too early
    or hammer an entry that is legitimately taken.
    """

    def __init__(self, entry_key: str, *, claimed_by: str | None, lease_expires_at: str | None) -> None:
        super().__init__(
            "conflict.already_claimed",
            "Diary entry is already being analysed.",
            status_code=409,
            details={
                "entry_key": entry_key,
                "claimed_by": claimed_by,
                "lease_expires_at": lease_expires_at,
            },
        )


class DiaryAnalysisConcurrentUpdateError(ContractError):
    """REQ-050 §4.2 — the document revision changed between read and write.

    The compare-and-set on ``_rev`` lost its race. This says nothing about who
    holds the entry: the correct reaction is an immediate retry, which will then
    either succeed or fail with :class:`DiaryAnalysisAlreadyClaimedError`.
    """

    def __init__(self, entry_key: str) -> None:
        super().__init__(
            "conflict.concurrent_update",
            "Diary entry was modified concurrently; retry the call.",
            status_code=409,
            details={"entry_key": entry_key},
        )


class DiaryAnalysisNotClaimedError(ContractError):
    """REQ-050 §4.5 — a result was submitted for an entry that is not claimed."""

    def __init__(self, entry_key: str, current_state: str) -> None:
        super().__init__(
            "conflict.not_claimed",
            "Diary entry is not claimed for analysis.",
            status_code=409,
            details={"entry_key": entry_key, "analysis_state": current_state},
        )


class DiaryAnalysisLeaseExpiredError(ContractError):
    """REQ-050 §4.5 — the presented ``lease_token`` does not match the live lease.

    Both the expired lease and a token belonging to a *different* claim land
    here: from the caller's side they are the same fact — the entry is no longer
    theirs to write.
    """

    def __init__(self, entry_key: str) -> None:
        super().__init__(
            "conflict.lease_expired",
            "The analysis lease for this diary entry is no longer valid.",
            status_code=409,
            details={"entry_key": entry_key},
        )
