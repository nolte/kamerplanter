"""Retention-policy facade (REQ-025 / NFR-011 bridge).

Pure-logic service and the **one place** the NFR-011 periods below are read
from settings and turned into deadlines or cutoffs:

* R-01 ``retention_soft_delete_retention_days`` — hard-delete date of an
  erasure request (``PrivacyService.request_erasure``);
* R-02 ``retention_unverified_account_days`` — ``cleanup_unverified_accounts``;
* R-03 ``retention_ip_anonymization_days`` — ``anonymize_old_ips``;
* R-05 ``retention_export_file_retention_hours`` — ``expires_at`` of a built
  export (``PrivacyService.process_data_export``);
* R-06 ``retention_erasure_audit_retention_years`` —
  ``retention.purge_expired_erasure_records``;
* R-07 ``retention_email_change_retention_hours`` — ``expires_at`` of an
  email-change request (``PrivacyService.request_email_change``).

The tasks and the Art. 13 retention summary read the periods here, so the text
a data subject reads cannot name a period the code does not apply (#1772,
#1782). A constructor argument overrides the setting (tests, one-off callers);
it is held to the same floor as the setting.

The remaining NFR-011 periods (consent records, invitations, sensor
downsampling, a retention master task) are not wired here yet.
"""

from datetime import UTC, datetime, timedelta

from app.common.datetimes import replace_year
from app.config.settings import settings


class RetentionService:
    """Computes retention deadlines for REQ-025 artefacts."""

    def __init__(
        self,
        export_retention_hours: int | None = None,
        hard_delete_after_days: int | None = None,
        email_change_ttl_hours: int | None = None,
        ip_anonymisation_after_days: int | None = None,
        unverified_account_days: int | None = None,
        erasure_record_retention_years: int | None = None,
    ) -> None:
        self._export_retention_hours = (
            export_retention_hours
            if export_retention_hours is not None
            else settings.retention_export_file_retention_hours
        )
        self._hard_delete_after_days = (
            hard_delete_after_days
            if hard_delete_after_days is not None
            else settings.retention_soft_delete_retention_days
        )
        self._email_change_ttl_hours = (
            email_change_ttl_hours
            if email_change_ttl_hours is not None
            else settings.retention_email_change_retention_hours
        )
        self._ip_anonymisation_after_days = (
            ip_anonymisation_after_days
            if ip_anonymisation_after_days is not None
            else settings.retention_ip_anonymization_days
        )
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
        floors = (
            (self._hard_delete_after_days, "NFR-011 R-01: the soft-delete grace period must be at least one day."),
            (self._unverified_account_days, "NFR-011 R-02: the unverified-account period must be at least one day."),
            (self._ip_anonymisation_after_days, "NFR-011 R-03: the IP-anonymisation period must be at least one day."),
            (self._export_retention_hours, "NFR-011 R-05: an export file must stay available at least one hour."),
            (
                self._erasure_record_retention_years,
                "NFR-011 R-06: erasure records are kept at least one year after completion.",
            ),
            (self._email_change_ttl_hours, "NFR-011 R-07: an email-change link must stay valid at least one hour."),
        )
        for period, message in floors:
            if period < 1:
                raise ValueError(message)

    # ── Deadline calculators ──────────────────────────────────────

    def export_expires_at(self, completed_at: datetime) -> datetime:
        """Return the moment an export file expires (NFR-011 R-05)."""
        return completed_at + timedelta(hours=self._export_retention_hours)

    def hard_delete_at(self, soft_deleted_at: datetime) -> datetime:
        """Return the moment a soft-deleted user is hard-deleted (NFR-011 R-01)."""
        return soft_deleted_at + timedelta(days=self._hard_delete_after_days)

    def email_change_expires_at(self, requested_at: datetime) -> datetime:
        """Return the moment an email-change request expires (NFR-011 R-07)."""
        return requested_at + timedelta(hours=self._email_change_ttl_hours)

    def ip_anonymisation_cutoff(self, now: datetime) -> datetime:
        """Return the capture time before which an IP is anonymised (NFR-011 R-03).

        ``anonymize_old_ips`` selects every session issued before it. In UTC
        whatever offset *now* carries: the task hands the ``isoformat`` on and
        logs it, like the R-02 cutoff (#1773 review GDPR-008). Replaces an
        unused ``ip_anonymisation_at`` so the period has one computation.
        """
        return now.astimezone(UTC) - timedelta(days=self._ip_anonymisation_after_days)

    def unverified_account_cutoff(self, now: datetime) -> datetime:
        """Return the registration time before which an unverified account is erased (NFR-011 R-02).

        In UTC whatever offset *now* carries: the caller passes the ``isoformat``
        to a string comparison against UTC timestamps (#1773 review GDPR-008).
        """
        return now.astimezone(UTC) - timedelta(days=self._unverified_account_days)

    def erasure_record_purge_cutoff(self, now: datetime) -> datetime:
        """Return the completion time before which an erasure record is purged (NFR-011 R-06).

        Counted in **calendar years**, not ``365 * years`` days: "1 Jahr nach
        Abschluss" must never be undercut, and 365 days back from a date after
        a 29 February is one day short of a year. A ``now`` on 29 February
        counts back to 28 February. The result is truncated to whole seconds
        and normalised to UTC (#1773 review GDPR-008): the purge repository
        compares instants (``DATE_TIMESTAMP``), but the cutoff is also what the
        run logs and hands on as an ISO string, and a string that kept
        ``+02:00`` or a fraction would be read — and, by any string comparison,
        ordered — two hours or a separator off.
        """
        now = now.astimezone(UTC)
        year = now.year - self._erasure_record_retention_years
        return replace_year(now, year).replace(microsecond=0)

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
