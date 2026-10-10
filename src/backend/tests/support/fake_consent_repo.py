"""In-memory stand-in for :class:`IConsentRepository` lookups (#2174).

Holds one consent state per ``(user_key, purpose)``: absent (never asked),
granted, or revoked (``granted=False`` plus ``revoked_at`` — what
``PrivacyService.revoke_consent`` stores). ``reads``
records every lookup so a test can assert that a refused request read the
opt-in and a short-circuited one did not.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.models.privacy import ConsentRecord


class FakeConsentRepo:
    def __init__(self, records: dict[tuple[str, str], bool] | None = None) -> None:
        self._records = dict(records or {})
        self.reads: list[tuple[str, str]] = []

    def set(self, user_key: str, purpose: str, *, granted: bool) -> None:
        self._records[(user_key, purpose)] = granted

    def get_by_user_and_purpose(self, user_key: str, purpose: str) -> ConsentRecord | None:
        self.reads.append((user_key, purpose))
        granted = self._records.get((user_key, purpose))
        if granted is None:
            return None
        if granted:
            return ConsentRecord(user_key=user_key, purpose=purpose, granted=True, granted_at=datetime.now(UTC))
        # A revocation always stamps revoked_at (privacy_service.revoke_consent).
        return ConsentRecord(user_key=user_key, purpose=purpose, granted=False, revoked_at=datetime.now(UTC))


class GrantAllConsentRepo(FakeConsentRepo):
    """Every lookup answers "granted" — for tests whose subject is not consent."""

    def get_by_user_and_purpose(self, user_key: str, purpose: str) -> ConsentRecord | None:
        self.reads.append((user_key, purpose))
        return ConsentRecord(user_key=user_key, purpose=purpose, granted=True)
