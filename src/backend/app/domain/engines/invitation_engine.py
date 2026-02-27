import hashlib
import secrets
from datetime import UTC, datetime, timedelta


class InvitationEngine:
    """Pure logic for invitation operations."""

    @staticmethod
    def create_invitation_token() -> tuple[str, str]:
        """Create a random token and its hash.

        Returns (raw_token, token_hash).
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return raw_token, token_hash

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Hash a raw invitation token for lookup."""
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @staticmethod
    def calculate_expiry(days: int = 7) -> datetime:
        """Calculate invitation expiry datetime."""
        return datetime.now(UTC) + timedelta(days=days)

    @staticmethod
    def is_expired(expires_at: datetime) -> bool:
        """Check if invitation has expired."""
        now = datetime.now(UTC)
        if expires_at.tzinfo is None:
            return now.replace(tzinfo=None) > expires_at
        return now > expires_at

    @staticmethod
    def can_accept(
        is_expired: bool,
        is_pending: bool,
        is_already_member: bool,
    ) -> tuple[bool, str]:
        """Check if invitation can be accepted. Returns (can_accept, reason)."""
        if not is_pending:
            return False, "Invitation is no longer pending"
        if is_expired:
            return False, "Invitation has expired"
        if is_already_member:
            return False, "User is already a member of this tenant"
        return True, ""
