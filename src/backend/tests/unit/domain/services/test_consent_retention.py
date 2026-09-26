"""#1800 — NFR-011 R-04 / R-04a: consent records get real enforcement.

Until #1800, ``erase_account`` hard-deleted a subject's ``consent_records``
outright (see ``test_privacy_service.py::TestTheConfirmationListsAllThreeCategories``
and ``test_privacy_engines.py`` for the erasure-plan side of that fix), and
nothing purged a consent record for an account that was never erased at all —
R-04's "3 years after revocation" ran nowhere. Likewise nothing anonymised
``consent_records.ip_address`` (R-04a), and ``anonymize_old_ips`` covered
``refresh_tokens`` only.

:meth:`PrivacyService.purge_expired_consent_records` and
:meth:`PrivacyService.anonymize_consent_ips` are the two new enforcement paths,
following the R-06 (``purge_expired_erasure_records``) and R-03
(``auth_tasks.anonymize_old_ips``) patterns respectively. The actual AQL is
measured against real ArangoDB in
``tests/integration/test_retention_instant_comparisons.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import structlog.testing

from app.config.settings import Settings
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService

NOW = datetime(2026, 9, 25, 4, 35, tzinfo=UTC)


def _service(consent_repo: object, *, retention: RetentionService | None = None) -> PrivacyService:
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=consent_repo,  # type: ignore[arg-type]
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=retention or RetentionService(),
    )


class TestPurgeExpiredConsentRecords:
    async def test_only_revoked_records_past_the_period_are_purged(self):
        repo = MagicMock()
        repo.delete_revoked_before.return_value = 2
        service = _service(repo, retention=RetentionService(consent_retention_years=3))

        purged = await service.purge_expired_consent_records(now=NOW)

        assert purged == 2
        repo.delete_revoked_before.assert_called_once()

    async def test_the_cutoff_is_now_minus_the_configured_calendar_years(self):
        repo = MagicMock()
        repo.delete_revoked_before.return_value = 0
        service = _service(repo, retention=RetentionService(consent_retention_years=3))

        await service.purge_expired_consent_records(now=NOW)

        (cutoff_arg,) = repo.delete_revoked_before.call_args.args
        assert datetime.fromisoformat(cutoff_arg) == datetime(2023, 9, 25, 4, 35, tzinfo=UTC)

    async def test_the_setting_reaches_the_cutoff(self, monkeypatch):
        """End to end from ``settings.retention_consent_retention_years`` to the selection."""
        from app.config.settings import settings

        monkeypatch.setattr(settings, "retention_consent_retention_years", 2)
        repo = MagicMock()
        repo.delete_revoked_before.return_value = 0
        service = _service(repo, retention=RetentionService())

        await service.purge_expired_consent_records(now=NOW)

        (cutoff_arg,) = repo.delete_revoked_before.call_args.args
        assert datetime.fromisoformat(cutoff_arg) == datetime(2024, 9, 25, 4, 35, tzinfo=UTC)

    async def test_the_cutoff_is_utc(self):
        repo = MagicMock()
        repo.delete_revoked_before.return_value = 0
        service = _service(repo)
        plus_two = datetime(2026, 9, 25, 6, 35, tzinfo=timezone(timedelta(hours=2)))

        await service.purge_expired_consent_records(now=plus_two)

        (cutoff_arg,) = repo.delete_revoked_before.call_args.args
        assert cutoff_arg == "2023-09-25T04:35:00+00:00"

    async def test_the_run_is_logged_with_counts_only(self):
        repo = MagicMock()
        repo.delete_revoked_before.return_value = 5
        service = _service(repo)

        with structlog.testing.capture_logs() as logs:
            await service.purge_expired_consent_records(now=NOW)

        (event,) = [e for e in logs if e["event"] == "retention.purge_expired_consent_records.completed"]
        assert event["purged"] == 5


class TestTheR04Setting:
    def test_the_default_is_the_spec_period(self):
        """NFR-011 R-04 / §4 ``CONSENT_RETENTION_YEARS = 3``."""
        assert Settings.model_fields["retention_consent_retention_years"].default == 3

    def test_the_service_refuses_a_period_under_one_year(self):
        with pytest.raises(ValueError, match="R-04"):
            RetentionService(consent_retention_years=0)


class TestAnonymizeConsentIps:
    """NFR-011 R-04a (#1800): the R-03 analogue for ``consent_records``."""

    async def test_every_selected_record_is_anonymised_and_stamped(self):
        repo = MagicMock()
        repo.list_unanonymized_ips_before.return_value = [("c1", "192.0.2.42"), ("c2", "2001:db8:85a3:1::1")]
        repo.mark_ip_anonymized.return_value = True
        service = _service(repo)

        count = await service.anonymize_consent_ips(now=NOW)

        assert count == 2
        written = [call.args for call in repo.mark_ip_anonymized.call_args_list]
        assert [(key, previous_ip, anon_ip) for key, previous_ip, anon_ip, _ in written] == [
            ("c1", "192.0.2.42", "192.0.2.0"),
            ("c2", "2001:db8:85a3:1::1", "2001:db8:85a3::"),
        ]
        assert len({stamp for _, _, _, stamp in written}) == 1

    async def test_a_concurrent_regrant_is_not_counted(self):
        """#1800 security review (SEC-003): a write the repository skipped (race) must not inflate the count."""
        repo = MagicMock()
        repo.list_unanonymized_ips_before.return_value = [("c1", "192.0.2.42"), ("c2", "2001:db8:85a3:1::1")]
        repo.mark_ip_anonymized.side_effect = [False, True]
        service = _service(repo)

        count = await service.anonymize_consent_ips(now=NOW)

        assert count == 1

    async def test_the_cutoff_is_the_configured_days_before_now(self):
        repo = MagicMock()
        repo.list_unanonymized_ips_before.return_value = []
        service = _service(repo, retention=RetentionService(consent_ip_anonymization_days=3))

        await service.anonymize_consent_ips(now=NOW)

        (cutoff_arg,) = repo.list_unanonymized_ips_before.call_args.args
        assert datetime.fromisoformat(cutoff_arg) == NOW - timedelta(days=3)

    async def test_nothing_to_anonymise_returns_zero(self):
        repo = MagicMock()
        repo.list_unanonymized_ips_before.return_value = []
        service = _service(repo)

        assert await service.anonymize_consent_ips(now=NOW) == 0
        repo.mark_ip_anonymized.assert_not_called()


class TestTheR04aSetting:
    def test_the_default_is_the_spec_period(self):
        """NFR-011 R-04a / §4 ``CONSENT_IP_ANONYMIZATION_DAYS = 7`` (R-03 analogue default)."""
        assert Settings.model_fields["retention_consent_ip_anonymization_days"].default == 7

    def test_the_service_refuses_a_period_under_one_day(self):
        with pytest.raises(ValueError, match="R-04a"):
            RetentionService(consent_ip_anonymization_days=0)
