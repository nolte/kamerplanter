"""#1948 — e-mail verification is required unless an operator switches it off.

With ``REQUIRE_EMAIL_VERIFICATION`` defaulting to ``false``, registration stamped
``email_verified = True`` on any address without a confirmation, so every gate
that trusts ``email_verified`` (the e-mail notification recipient of REQ-030
§3.4, OAuth auto-link) admitted an address the registrant need not own. The
operator decision of 2026-10-03 (REQ-023 v1.28) flips the default to ``true``;
an installation without outbound mail sets ``false`` explicitly.

Asserted on the shipped default — which value an installation gets when it says
nothing — and on the stacks that run without mail, which must keep saying
``false`` out loud now that silence means ``true``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.config.settings import Settings

_REPO_ROOT = Path(__file__).resolve().parents[4]


def test_verification_is_required_when_the_installation_says_nothing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("REQUIRE_EMAIL_VERIFICATION", raising=False)

    assert Settings().require_email_verification is True, (
        "REQUIRE_EMAIL_VERIFICATION no longer defaults to true: every installation that has not "
        "set it marks self-registered addresses as verified without a confirmation (#1948)."
    )


def test_an_installation_without_mail_can_still_switch_it_off(monkeypatch: pytest.MonkeyPatch):
    """The control: the default is a default, not a constant."""
    monkeypatch.setenv("REQUIRE_EMAIL_VERIFICATION", "false")

    assert Settings().require_email_verification is False


def _compose_backend_env(path: Path, service: str) -> dict[str, str]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document["services"][service]["environment"]


@pytest.mark.skipif(not (_REPO_ROOT / "docker-compose.e2e.yml").exists(), reason="repository files not shipped")
def test_the_mail_less_stacks_switch_verification_off_explicitly():
    """The E2E compose stack and the Skaffold dev values register accounts and log
    straight in without a mailbox; with the default now ``true`` they only keep
    working because they set ``false`` themselves."""
    e2e = yaml.safe_load((_REPO_ROOT / "docker-compose.e2e.yml").read_text(encoding="utf-8"))
    backends = {
        name: service["environment"]
        for name, service in e2e["services"].items()
        if isinstance(service.get("environment"), dict) and "REQUIRE_EMAIL_VERIFICATION" in service["environment"]
    }
    dev_values = yaml.safe_load((_REPO_ROOT / "helm/kamerplanter/values-dev.yaml").read_text(encoding="utf-8"))
    dev_env = dev_values["controllers"]["backend"]["containers"]["main"]["env"]

    # Non-vacuity: both e2e backends (full and light) are found.
    assert len(backends) == 2, sorted(backends)
    assert {name: env["REQUIRE_EMAIL_VERIFICATION"] for name, env in backends.items()} == dict.fromkeys(
        backends, "false"
    )
    assert dev_env["REQUIRE_EMAIL_VERIFICATION"] == "false"


def test_the_service_default_agrees_with_the_settings_default(monkeypatch: pytest.MonkeyPatch):
    """The wiring passes the setting, but a service built without it (a test, a
    script) must not quietly fall back to the old, unverified behaviour."""
    import inspect

    from app.domain.services.auth_service import AuthService

    monkeypatch.delenv("REQUIRE_EMAIL_VERIFICATION", raising=False)
    parameter = inspect.signature(AuthService.__init__).parameters["require_email_verification"]

    assert parameter.default is Settings().require_email_verification
