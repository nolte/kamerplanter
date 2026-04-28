"""Retention-policy facade (REQ-025 / NFR-011 bridge).

Pure-logic service that exposes the retention windows defined for REQ-025
data-export files, hard-delete schedules, and email-change-request TTLs.
It centralises the constants so that the (future) NFR-011 retention-master
Celery task can pick them up from a single place.

The richer NFR-011 retention master (sensor downsampling, IP anonymisation,
crontab schedules, etc.) is out of scope for this PR and will be wired up
in a dedicated follow-up; this service intentionally keeps a small surface
focused on the four windows REQ-025 itself defines.
"""

from datetime import UTC, datetime, timedelta

from app.config.settings import settings


class RetentionService:
    """Computes retention deadlines for REQ-025 artefacts."""

    def __init__(
        self,
        export_retention_hours: int | None = None,
        hard_delete_after_days: int | None = None,
        email_change_ttl_hours: int | None = None,
        ip_anonymisation_after_days: int = 7,
    ) -> None:
        self._export_retention_hours = (
            export_retention_hours if export_retention_hours is not None else settings.privacy_export_retention_hours
        )
        self._hard_delete_after_days = (
            hard_delete_after_days if hard_delete_after_days is not None else settings.privacy_hard_delete_after_days
        )
        self._email_change_ttl_hours = (
            email_change_ttl_hours if email_change_ttl_hours is not None else settings.privacy_email_change_ttl_hours
        )
        self._ip_anonymisation_after_days = ip_anonymisation_after_days

    # ── Deadline calculators ──────────────────────────────────────

    def export_expires_at(self, completed_at: datetime) -> datetime:
        """Return the moment an export file expires (NFR-011 R-05)."""
        return completed_at + timedelta(hours=self._export_retention_hours)

    def hard_delete_at(self, soft_deleted_at: datetime) -> datetime:
        """Return the moment a soft-deleted user is hard-deleted (NFR-011 R-01)."""
        return soft_deleted_at + timedelta(days=self._hard_delete_after_days)

    def email_change_expires_at(self, requested_at: datetime) -> datetime:
        """Return the moment an email-change request expires (24h default)."""
        return requested_at + timedelta(hours=self._email_change_ttl_hours)

    def ip_anonymisation_at(self, captured_at: datetime) -> datetime:
        """Return the moment a captured IP must be anonymised (NFR-011 R-04)."""
        return captured_at + timedelta(days=self._ip_anonymisation_after_days)

    # ── Predicate helpers ────────────────────────────────────────

    def is_export_expired(
        self,
        completed_at: datetime | None,
        now: datetime | None = None,
    ) -> bool:
        if completed_at is None:
            return False
        moment = now or datetime.now(UTC)
        return self.export_expires_at(completed_at) < moment

    def is_due_for_hard_delete(
        self,
        soft_deleted_at: datetime | None,
        now: datetime | None = None,
    ) -> bool:
        if soft_deleted_at is None:
            return False
        moment = now or datetime.now(UTC)
        return self.hard_delete_at(soft_deleted_at) <= moment

    # ── Window introspection (for documentation / API exposure) ──

    @property
    def export_retention_hours(self) -> int:
        return self._export_retention_hours

    @property
    def hard_delete_after_days(self) -> int:
        return self._hard_delete_after_days

    @property
    def email_change_ttl_hours(self) -> int:
        return self._email_change_ttl_hours

    @property
    def ip_anonymisation_after_days(self) -> int:
        return self._ip_anonymisation_after_days
