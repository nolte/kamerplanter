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
