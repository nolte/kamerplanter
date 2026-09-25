"""Retention-policy facade (REQ-025 / NFR-011 bridge).

Pure-logic service that exposes the retention windows defined for REQ-025
data-export files, hard-delete schedules, and email-change-request TTLs,
and computes the cutoffs of the NFR-011 periods the retention tasks enforce
from settings: R-02 (unverified accounts, ``cleanup_unverified_accounts``)
and R-06 (erasure records, ``retention.purge_expired_erasure_records``).
Both tasks and the Art. 13 retention summary read those two periods here, so
the text a data subject reads cannot name a period the task does not apply
(#1772).

The richer NFR-011 retention master (sensor downsampling, IP anonymisation,
crontab schedules, etc.) is out of scope and will be wired up in a dedicated
follow-up.
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
        unverified_account_days: int | None = None,
        erasure_record_retention_years: int | None = None,
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
        self._unverified_account_days = (
            unverified_account_days
            if unverified_account_days is not None
            else settings.retention_unverified_account_days
        )
        self._erasure_record_retention_years = (
            erasure_record_retention_years
            if erasure_record_retention_years is not None
            else settings.retention_erasure_audit_retention_years
        )
        # The settings carry the same floors (``ge=1``); a caller constructing
        # the service directly must not get past them either.
        if self._unverified_account_days < 1:
            msg = "NFR-011 R-02: the unverified-account period must be at least one day."
            raise ValueError(msg)
        if self._erasure_record_retention_years < 1:
            msg = "NFR-011 R-06: erasure records are kept at least one year after completion."
            raise ValueError(msg)

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
        """Return the moment a captured IP must be anonymised (NFR-011 R-03)."""
        return captured_at + timedelta(days=self._ip_anonymisation_after_days)

    def unverified_account_cutoff(self, now: datetime) -> datetime:
        """Return the registration time before which an unverified account is erased (NFR-011 R-02)."""
        return now - timedelta(days=self._unverified_account_days)

    def erasure_record_purge_cutoff(self, now: datetime) -> datetime:
        """Return the completion time before which an erasure record is purged (NFR-011 R-06).

        Counted in **calendar years**, not ``365 * years`` days: "1 Jahr nach
        Abschluss" must never be undercut, and 365 days back from a date after
        a 29 February is one day short of a year. A ``now`` on 29 February
        counts back to 28 February. The result is truncated to whole seconds:
        the repository compares ISO strings, and a stored timestamp without a
        fraction against a cutoff with one would order by the separator, not
        by the instant.
        """
        year = now.year - self._erasure_record_retention_years
        try:
            cutoff = now.replace(year=year)
        except ValueError:  # 29 February in a non-leap target year
            cutoff = now.replace(year=year, day=28)
        return cutoff.replace(microsecond=0)

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

    @property
    def unverified_account_days(self) -> int:
        return self._unverified_account_days

    @property
    def erasure_record_retention_years(self) -> int:
        return self._erasure_record_retention_years
