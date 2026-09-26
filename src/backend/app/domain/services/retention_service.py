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
  email-change request (``PrivacyService.request_email_change``);
  ``retention_email_change_revert_days`` — the revert window of a confirmed one
  (``PrivacyService.confirm_email_change``, #1848) and (#1800, R-07b) the
  hard-delete of the whole document once that window has elapsed;
* R-04 ``retention_consent_retention_years`` — a consent record is purged this
  many years after ``revoked_at`` (``retention.purge_expired_consent_records``,
  #1800);
* R-04a ``retention_consent_ip_anonymization_days`` — a consent record's IP is
  anonymised this many days after it was recorded
  (``retention.anonymize_consent_ips``, #1800);
* R-12 ``retention_invitation_retention_days`` — an expired invitation is
  hard-deleted this many days after ``expires_at``
  (``tenant_tasks.cleanup_expired_invitations``, #1800).

The tasks and the Art. 13 retention summary read the periods here, so the text
a data subject reads cannot name a period the code does not apply (#1772,
#1782). A constructor argument overrides the setting (tests, one-off callers);
it is held to the same floor as the setting.

The remaining NFR-011 periods (sensor downsampling, a retention master task)
are not wired here yet.
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
        email_change_revert_days: int | None = None,
        ip_anonymisation_after_days: int | None = None,
        unverified_account_days: int | None = None,
        erasure_record_retention_years: int | None = None,
        consent_retention_years: int | None = None,
        consent_ip_anonymization_days: int | None = None,
        invitation_retention_days: int | None = None,
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
        self._email_change_revert_days = (
            email_change_revert_days
            if email_change_revert_days is not None
            else settings.retention_email_change_revert_days
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
        self._consent_retention_years = (
            consent_retention_years
            if consent_retention_years is not None
            else settings.retention_consent_retention_years
        )
        self._consent_ip_anonymization_days = (
            consent_ip_anonymization_days
            if consent_ip_anonymization_days is not None
            else settings.retention_consent_ip_anonymization_days
        )
        self._invitation_retention_days = (
            invitation_retention_days
            if invitation_retention_days is not None
            else settings.retention_invitation_retention_days
        )
        # The settings carry the same floors (``ge=1``); a caller constructing
        # the service directly must not get past them either.
        floors = (
            (self._hard_delete_after_days, "NFR-011 R-01: the soft-delete grace period must be at least one day."),
            (self._unverified_account_days, "NFR-011 R-02: the unverified-account period must be at least one day."),
            (self._ip_anonymisation_after_days, "NFR-011 R-03: the IP-anonymisation period must be at least one day."),
            (
                self._consent_retention_years,
                "NFR-011 R-04: consent records are kept at least one year after revocation.",
            ),
            (
                self._consent_ip_anonymization_days,
                "NFR-011 R-04a: the consent-record IP-anonymisation period must be at least one day.",
            ),
            (self._export_retention_hours, "NFR-011 R-05: an export file must stay available at least one hour."),
            (
                self._erasure_record_retention_years,
                "NFR-011 R-06: erasure records are kept at least one year after completion.",
            ),
            (self._email_change_ttl_hours, "NFR-011 R-07: an email-change link must stay valid at least one hour."),
            (self._email_change_revert_days, "NFR-011 R-07: the email-change revert link must stay valid a day."),
            (self._invitation_retention_days, "NFR-011 R-12: an expired invitation must be kept at least one day."),
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

    def email_change_revert_expires_at(self, confirmed_at: datetime) -> datetime:
        """Return the moment the revert link of a confirmed email change stops working (NFR-011 R-07, #1848)."""
        return confirmed_at + timedelta(days=self._email_change_revert_days)

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

    def consent_record_purge_cutoff(self, now: datetime) -> datetime:
        """Return the revocation time before which a consent record is purged (NFR-011 R-04, #1800).

        Counted in calendar years, like :meth:`erasure_record_purge_cutoff` (R-06)
        and for the same reason: "3 Jahre nach Widerruf" must never be undercut by
        a fixed ``365 * years`` day count. Normalised to UTC and truncated to whole
        seconds so the cutoff compares and logs the same way (#1773 review GDPR-008).
        """
        now = now.astimezone(UTC)
        year = now.year - self._consent_retention_years
        return replace_year(now, year).replace(microsecond=0)

    def consent_ip_anonymisation_cutoff(self, now: datetime) -> datetime:
        """Return the ``granted_at`` before which a consent record's IP is anonymised (NFR-011 R-04a, #1800).

        The R-03 analogue for ``consent_records`` instead of ``refresh_tokens``:
        the IP and ``granted_at`` are written together by
        ``PrivacyService.grant_consent``, so ``granted_at`` is the "recorded" instant
        R-04a counts from.
        """
        return now.astimezone(UTC) - timedelta(days=self._consent_ip_anonymization_days)

    def invitation_purge_cutoff(self, now: datetime) -> datetime:
        """Return the expiry time before which an expired invitation is hard-deleted (NFR-011 R-12, #1800)."""
        return now.astimezone(UTC) - timedelta(days=self._invitation_retention_days)

    def email_change_document_purge_cutoff(self, now: datetime) -> datetime:
        """Return the ``confirmed_at`` before which a confirmed change is fully hard-deleted (NFR-011 R-07b, #1800).

        Recomputed from ``confirmed_at`` with the same period as
        :meth:`email_change_revert_expires_at` rather than read back from the
        stored ``revert_expires_at``: R-07a nulls that field once its window
        closes, and R-07b must not depend on R-07a's own write having already
        run in the same beat cycle.
        """
        return now.astimezone(UTC) - timedelta(days=self._email_change_revert_days)

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

    @property
    def consent_retention_years(self) -> int:
        return self._consent_retention_years

    @property
    def consent_ip_anonymization_days(self) -> int:
        return self._consent_ip_anonymization_days

    @property
    def invitation_retention_days(self) -> int:
        return self._invitation_retention_days
