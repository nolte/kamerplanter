from datetime import UTC, datetime, timedelta

MAX_ATTEMPTS = 5
BASE_LOCKOUT_MINUTES = 15
MAX_LOCKOUT_MINUTES = 240  # 4 hours


class LoginThrottleEngine:
    """Pure logic for login throttling — no DB access."""

    def check_allowed(self, failed_attempts: int, locked_until: datetime | None) -> bool:
        """Check if a login attempt is allowed."""
        return not (locked_until is not None and datetime.now(UTC) < locked_until)

    def calculate_lockout(self, failed_attempts: int) -> datetime | None:
        """Calculate lockout expiry after a failed attempt. Returns None if no lockout needed."""
        if failed_attempts < MAX_ATTEMPTS:
            return None
        # Exponential backoff: 15min, 30min, 60min, 120min, 240min (cap)
        exponent = failed_attempts - MAX_ATTEMPTS
        minutes = min(BASE_LOCKOUT_MINUTES * (2**exponent), MAX_LOCKOUT_MINUTES)
        return datetime.now(UTC) + timedelta(minutes=minutes)

    def get_lockout_minutes(self, locked_until: datetime | None) -> int:
        """Get remaining lockout minutes."""
        if locked_until is None:
            return 0
        remaining = (locked_until - datetime.now(UTC)).total_seconds() / 60
        return max(0, int(remaining) + 1)

    def should_lock(self, failed_attempts: int) -> bool:
        """Check if the account should be locked after this attempt."""
        return failed_attempts >= MAX_ATTEMPTS
