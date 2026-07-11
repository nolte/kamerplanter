import uuid


class KamerplanterError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self.error_id = f"err_{uuid.uuid4()}"
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(KamerplanterError):
    def __init__(self, entity: str, key: str) -> None:
        super().__init__(
            message=f"{entity} with key '{key}' not found.",
            error_code="ENTITY_NOT_FOUND",
            status_code=404,
            details=[{"field": "key", "reason": f"No {entity} with key '{key}'.", "code": "ENTITY_NOT_FOUND"}],
        )


class DuplicateError(KamerplanterError):
    def __init__(self, entity: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{entity} with {field}='{value}' already exists.",
            error_code="DUPLICATE_ENTRY",
            status_code=409,
            details=[{"field": field, "reason": f"Value '{value}' is already taken.", "code": "DUPLICATE_ENTRY"}],
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
