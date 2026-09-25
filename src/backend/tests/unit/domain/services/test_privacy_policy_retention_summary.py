"""#1772 — the Art. 13 retention summary names the periods the code enforces.

``GET /api/v1/privacy/policy`` lists the retention categories to the data
subject. It named neither the unverified-account period (NFR-011 R-02) nor the
erasure-record period (R-06), and labelled IP anonymisation "R-04" — R-04 is
consent records; IP anonymisation is R-03. The two new entries are read from
the same :class:`RetentionService` the retention tasks compute their cutoffs
with, so the text cannot state a period the task does not apply.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.domain.engines.consent_engine import ConsentEngine
from app.domain.models.privacy import PrivacyPolicyInfo
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService


def _policy(retention: RetentionService) -> dict[str, str]:
    return {entry.category: entry.retention_period for entry in _full_policy(retention).retention_summary}


def _full_policy(retention: RetentionService) -> PrivacyPolicyInfo:
    service = PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=MagicMock(),
        consent_engine=ConsentEngine(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=retention,
    )
    return service.get_privacy_policy()


class TestTheRetentionSummary:
    def test_unverified_accounts_are_listed_with_the_r02_period(self):
        summary = _policy(RetentionService(unverified_account_days=7))

        assert summary["unverified_accounts"] == "Deleted 7 days after registration if not confirmed (NFR-011 R-02)."

    def test_erasure_records_are_listed_with_the_r06_period(self):
        summary = _policy(RetentionService(erasure_record_retention_years=1))

        assert summary["erasure_records"] == (
            "Pseudonymised at erasure, deleted 1 year(s) after completion (NFR-011 R-06)."
        )

    def test_the_listed_periods_follow_the_configuration(self):
        summary = _policy(RetentionService(unverified_account_days=10, erasure_record_retention_years=2))

        assert "10 days" in summary["unverified_accounts"]
        assert "2 year(s)" in summary["erasure_records"]

    def test_ip_anonymisation_carries_the_r03_label(self):
        summary = _policy(RetentionService())

        assert summary["ip_addresses"] == "Anonymised after 7 days (NFR-011 R-03)."

    def test_the_ip_entry_names_only_what_the_anonymisation_reaches(self):
        """GDPR-005 (#1773 review): ``anonymize_old_ips`` walks ``refresh_tokens`` only.

        The entry claimed IPs "captured during authentication / consent" are
        anonymised after 7 days; the consent records' IPs are not touched by any
        task (#1782). Art. 13 text must not promise what the code does not do.
        """
        policy = _full_policy(RetentionService())
        entry = next(e for e in policy.retention_summary if e.category == "ip_addresses")

        assert "consent" not in entry.description.lower()
        assert "session" in entry.description.lower()


class TestThePeriodsWiredIn1782:
    """#1782 — R-03 and R-05 are read from the service the tasks use, like R-02/R-06."""

    def test_the_ip_period_follows_the_configuration(self):
        summary = _policy(RetentionService(ip_anonymisation_after_days=3))

        assert summary["ip_addresses"] == "Anonymised after 3 days (NFR-011 R-03)."

    def test_the_export_period_follows_the_configuration(self):
        summary = _policy(RetentionService(export_retention_hours=12))

        assert summary["export_files"] == "12 hours after completion (NFR-011 R-05)."

    def test_the_default_texts_name_the_spec_periods(self):
        summary = _policy(RetentionService(ip_anonymisation_after_days=7, export_retention_hours=72))

        assert summary["ip_addresses"] == "Anonymised after 7 days (NFR-011 R-03)."
        assert summary["export_files"] == "72 hours after completion (NFR-011 R-05)."

    def test_the_account_entry_names_the_r01_grace_period(self):
        summary = _policy(RetentionService(hard_delete_after_days=45))

        assert "45 days" in summary["account_data"]
        assert "R-01" in summary["account_data"]
