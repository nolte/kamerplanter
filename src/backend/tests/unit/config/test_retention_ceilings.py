"""NFR-011 §4 / AK-14 — every configurable retention period has a ceiling (#1806 GDPR-004).

The ceiling is the NFR's own default: an operator may shorten a period for
extra data minimisation (Art. 5(1)(c)) but not lengthen it. A value above it
stops the process from loading its settings, which is what keeps API **and**
worker from starting (both import ``app.config.settings``). The error names the
variable and the limit, never the configured value.
"""

from __future__ import annotations

import pytest

from app.config.settings import Settings, SettingsError, load_settings

# (environment variable, ceiling) — NFR-011 §4, the twelve settings with a ceiling
# (the seven of Q-R9 plus R-04 / R-04a / R-12, #1946, R-01a, #1960, and R-01b, #2123).
CEILINGS = [
    ("RETENTION_SOFT_DELETE_RETENTION_DAYS", 90),
    ("RETENTION_UNVERIFIED_ACCOUNT_DAYS", 7),
    ("RETENTION_IP_ANONYMIZATION_DAYS", 7),
    ("RETENTION_EXPORT_FILE_RETENTION_HOURS", 72),
    ("RETENTION_ERASURE_AUDIT_RETENTION_YEARS", 3),
    ("RETENTION_EMAIL_CHANGE_RETENTION_HOURS", 24),
    ("RETENTION_EMAIL_CHANGE_REVERT_DAYS", 7),
    ("RETENTION_CONSENT_RETENTION_YEARS", 3),
    ("RETENTION_CONSENT_IP_ANONYMIZATION_DAYS", 7),
    ("RETENTION_INVITATION_RETENTION_DAYS", 30),
    ("RETENTION_ERASURE_MEMBER_NOTICE_DAYS", 7),
    # #2123 (MT-027) — the cancellable grace of a tenant deletion; floor 0 (self-hosted).
    ("RETENTION_TENANT_ERASURE_GRACE_DAYS", 90),
]
# The pre-#1782 names still accepted as aliases (NFR-011 §4 last column).
ALIAS_CEILINGS = [
    ("PRIVACY_HARD_DELETE_AFTER_DAYS", 90),
    ("PRIVACY_EXPORT_RETENTION_HOURS", 72),
    ("PRIVACY_EMAIL_CHANGE_TTL_HOURS", 24),
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name, _ in CEILINGS + ALIAS_CEILINGS:
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(("variable", "ceiling"), CEILINGS + ALIAS_CEILINGS)
def test_a_value_above_the_ceiling_refuses_to_load(monkeypatch, variable, ceiling):
    monkeypatch.setenv(variable, str(ceiling + 1))
    with pytest.raises(SettingsError) as raised:
        load_settings()
    message = str(raised.value)
    assert str(ceiling) in message  # the limit is named ...
    assert str(ceiling + 1) not in message  # ... the configured value is not
    assert "retention" in message.lower() or "privacy" in message.lower()  # ... nor is it nameless


@pytest.mark.parametrize(("variable", "ceiling"), CEILINGS + ALIAS_CEILINGS)
def test_a_value_at_the_ceiling_still_loads(monkeypatch, variable, ceiling):
    monkeypatch.setenv(variable, str(ceiling))
    load_settings()


@pytest.mark.parametrize(("variable", "ceiling"), CEILINGS)
def test_a_shorter_period_still_loads(monkeypatch, variable, ceiling):
    # More minimisation than the NFR asks for is the operator's call.
    monkeypatch.setenv(variable, "1")
    load_settings()


def test_every_default_is_within_its_own_ceiling():
    settings = Settings()
    for variable, ceiling in CEILINGS:
        assert getattr(settings, variable.lower()) <= ceiling, variable


def test_the_legal_minimum_periods_have_no_ceiling():
    # R-16..R-18 carry a legal floor and no Q-R9 ceiling (a ceiling equal to the floor
    # would make the setting inert); R-04/R-04a/R-12 do have one since #1946.
    Settings(retention_harvest_data_min_retention_years=50, retention_treatment_min_retention_years=50)


def test_the_ceiling_table_names_every_ceilinged_setting():
    from app.config.settings import RETENTION_CEILINGS

    assert set(RETENTION_CEILINGS) == {variable.lower() for variable, _ in CEILINGS}


class TestTheServiceRepeatsTheCeilings:
    @pytest.mark.parametrize(
        ("keyword", "ceiling", "rule"),
        [
            ("hard_delete_after_days", 90, "R-01"),
            ("unverified_account_days", 7, "R-02"),
            ("ip_anonymisation_after_days", 7, "R-03"),
            ("export_retention_hours", 72, "R-05"),
            ("erasure_record_retention_years", 3, "R-06"),
            ("email_change_ttl_hours", 24, "R-07"),
            ("email_change_revert_days", 7, "R-07a"),
            ("consent_retention_years", 3, "R-04"),
            ("consent_ip_anonymization_days", 7, "R-04a"),
            ("invitation_retention_days", 30, "R-12"),
            ("erasure_member_notice_days", 7, "R-01a"),
        ],
    )
    def test_an_explicit_period_above_the_ceiling_is_refused(self, keyword, ceiling, rule):
        from app.domain.services.retention_service import RetentionService

        RetentionService(**{keyword: ceiling})  # at the ceiling: fine
        with pytest.raises(ValueError, match=rule) as raised:
            RetentionService(**{keyword: ceiling + 1})
        # Value-free: the message is the same whatever the offending value was
        # (a digit check would false-positive on "R-04" for a ceiling of 3).
        with pytest.raises(ValueError, match=rule) as other:
            RetentionService(**{keyword: ceiling + 987})
        assert str(raised.value) == str(other.value)


class TestADeprecatedNameIsNeverSilent:
    """#1806 GDPR-008 — ``PRIVACY_*`` still works, but not unannounced."""

    def _run(self, environ):
        from structlog.testing import capture_logs

        from app.config.settings import report_retention_alias_use

        with capture_logs() as logs:
            found = report_retention_alias_use(environ)
        return found, logs

    def test_a_deprecated_name_alone_is_a_warning(self):
        found, logs = self._run({"PRIVACY_EXPORT_RETENTION_HOURS": "48"})
        assert found == [("PRIVACY_EXPORT_RETENTION_HOURS", "RETENTION_EXPORT_FILE_RETENTION_HOURS", False)]
        assert [(entry["event"], entry["log_level"]) for entry in logs] == [
            ("retention_setting_deprecated_name", "warning")
        ]

    def test_both_names_with_different_values_is_an_error_naming_the_winner(self):
        found, logs = self._run({"PRIVACY_HARD_DELETE_AFTER_DAYS": "30", "RETENTION_SOFT_DELETE_RETENTION_DAYS": "60"})
        assert found[0][2] is True
        assert [(entry["event"], entry["log_level"]) for entry in logs] == [("retention_setting_conflict", "error")]
        assert logs[0]["effective"] == "RETENTION_SOFT_DELETE_RETENTION_DAYS"

    def test_both_names_with_the_same_value_is_only_the_deprecation_warning(self):
        _, logs = self._run({"PRIVACY_HARD_DELETE_AFTER_DAYS": "30", "RETENTION_SOFT_DELETE_RETENTION_DAYS": "30"})
        assert [entry["log_level"] for entry in logs] == ["warning"]

    def test_no_value_is_ever_logged(self):
        _, logs = self._run({"PRIVACY_HARD_DELETE_AFTER_DAYS": "1234", "RETENTION_SOFT_DELETE_RETENTION_DAYS": "5678"})
        assert "1234" not in repr(logs)
        assert "5678" not in repr(logs)

    def test_the_names_are_matched_case_insensitively_like_the_settings_are(self):
        found, _ = self._run({"privacy_export_retention_hours": "48"})
        assert len(found) == 1

    def test_the_documented_name_alone_logs_nothing(self):
        found, logs = self._run({"RETENTION_EXPORT_FILE_RETENTION_HOURS": "48"})
        assert (found, logs) == ([], [])
