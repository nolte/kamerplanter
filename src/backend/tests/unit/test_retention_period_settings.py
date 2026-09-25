"""#1782 — every NFR-011 period this package wires is one setting under its documented name.

NFR-011 §4 and the data-retention guide name ``RETENTION_SOFT_DELETE_RETENTION_DAYS``
(R-01), ``RETENTION_IP_ANONYMIZATION_DAYS`` (R-03),
``RETENTION_EXPORT_FILE_RETENTION_HOURS`` (R-05) and
``RETENTION_EMAIL_CHANGE_RETENTION_HOURS`` (R-07). Until #1782 the settings
carried other names (``PRIVACY_*``) and R-03 had none at all — and none of them
was read by the code that applies the period. The three ``PRIVACY_*`` names an
operator may already have set keep working as aliases; the documented name wins
when both are set.

The values are read through a fresh :class:`Settings` built from the process
environment, the way the running application reads them.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings

#: (field, documented env name, legacy env name or None, NFR-011 default)
PERIODS = [
    (
        "retention_soft_delete_retention_days",
        "RETENTION_SOFT_DELETE_RETENTION_DAYS",
        "PRIVACY_HARD_DELETE_AFTER_DAYS",
        90,
    ),
    ("retention_ip_anonymization_days", "RETENTION_IP_ANONYMIZATION_DAYS", None, 7),
    (
        "retention_export_file_retention_hours",
        "RETENTION_EXPORT_FILE_RETENTION_HOURS",
        "PRIVACY_EXPORT_RETENTION_HOURS",
        72,
    ),
    (
        "retention_email_change_retention_hours",
        "RETENTION_EMAIL_CHANGE_RETENTION_HOURS",
        "PRIVACY_EMAIL_CHANGE_TTL_HOURS",
        24,
    ),
]

LEGACY = [p for p in PERIODS if p[2] is not None]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for _field, documented, legacy, _default in PERIODS:
        monkeypatch.delenv(documented, raising=False)
        if legacy:
            monkeypatch.delenv(legacy, raising=False)


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), PERIODS)
def test_the_default_is_the_spec_period(field, documented, legacy, default):
    assert getattr(Settings(), field) == default


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), PERIODS)
def test_the_documented_env_name_sets_the_period(monkeypatch, field, documented, legacy, default):
    monkeypatch.setenv(documented, str(default + 3))

    assert getattr(Settings(), field) == default + 3


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), LEGACY)
def test_the_legacy_env_name_still_sets_the_period(monkeypatch, field, documented, legacy, default):
    monkeypatch.setenv(legacy, str(default + 5))

    assert getattr(Settings(), field) == default + 5


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), LEGACY)
def test_the_documented_name_wins_when_both_are_set(monkeypatch, field, documented, legacy, default):
    monkeypatch.setenv(legacy, str(default + 5))
    monkeypatch.setenv(documented, str(default + 3))

    assert getattr(Settings(), field) == default + 3


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), PERIODS)
def test_zero_is_refused(monkeypatch, field, documented, legacy, default):
    # The positive case first: a name the settings do not know is ignored, not
    # refused, and the negative case alone would then pass vacuously.
    monkeypatch.setenv(documented, "1")
    assert getattr(Settings(), field) == 1

    monkeypatch.setenv(documented, "0")
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(("field", "documented", "legacy", "default"), LEGACY)
def test_zero_is_refused_under_the_legacy_name_too(monkeypatch, field, documented, legacy, default):
    monkeypatch.setenv(legacy, "0")
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    "legacy_field",
    ["privacy_export_retention_hours", "privacy_hard_delete_after_days", "privacy_email_change_ttl_hours"],
)
def test_the_legacy_names_are_no_longer_attributes(legacy_field):
    """One period, one attribute: a reader of the old attribute would silently see a second value."""
    assert legacy_field not in Settings.model_fields
