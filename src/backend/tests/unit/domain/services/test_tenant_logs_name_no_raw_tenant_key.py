"""The invitation and tenant-erasure log lines carry no raw tenant key (#1928).

The tenant key sits on the pseudonymised retention rows, and for a personal
tenant it identifies its owner; a line that carries it beside the salted
``subject=`` joins the two. The lines now carry ``tenant=<ten_…>``
(``ErasureEngine.log_tenant`` under ``LOG_PSEUDONYM_SALT``).

The tests drive the real :class:`TenantService` methods over the repository
doubles (the harnesses of ``test_erasure_invitations_and_late_join`` and
``test_tenant_erasure_service``) and read what structlog receives.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import structlog.testing

from app.common.log_privacy import log_tenant, log_tenant_record_key
from app.config.settings import settings
from app.domain.engines.erasure_engine import UNAVAILABLE_LOG_TENANT, ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from tests.support.tenant_erasure_doubles import authorized, delete_and_run, tenant, tenant_service_for_deletion
from tests.unit.domain.services.test_erasure_invitations_and_late_join import JOINER, PERSONAL, Tenants, account

LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"
#: Distinctive, so a substring hit cannot be a coincidence.
TENANT_KEY = "tenant-1928-owner-garden"


@pytest.fixture(autouse=True)
def _log_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", LOG_SALT)


def _leaks(logs: list[dict[str, Any]], key: str) -> list[str]:
    return [event.get("event", "?") for event in logs if key in json.dumps(event, default=str)]


class TestLogTenant:
    def test_a_salted_stable_reference_that_names_nobody(self) -> None:
        reference = log_tenant(TENANT_KEY)

        assert reference == log_tenant(TENANT_KEY) != log_tenant("other")
        assert reference is not None and reference.startswith("ten_") and TENANT_KEY not in reference

    def test_it_is_keyed_with_the_log_salt_and_purpose_separated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        before = log_tenant(TENANT_KEY)
        monkeypatch.setattr(settings, "log_pseudonym_salt", "another-log-pseudonym-salt-0123456789")

        assert log_tenant(TENANT_KEY) != before
        # not the subject reference of the same string, not the tombstone
        assert ErasureEngine.log_subject(TENANT_KEY, LOG_SALT).removeprefix("sub_") != before.removeprefix("ten_")

    @pytest.mark.parametrize("salt", ["", "short"])
    def test_a_missing_or_short_salt_yields_the_constant_never_the_key(
        self, monkeypatch: pytest.MonkeyPatch, salt: str
    ) -> None:
        monkeypatch.setattr(settings, "log_pseudonym_salt", salt)

        assert log_tenant(TENANT_KEY) == UNAVAILABLE_LOG_TENANT

    def test_no_key_no_reference(self) -> None:
        assert log_tenant(None) is None and log_tenant("") is None


class TestLogTenantRecordKey:
    """``ter_<tenant_key>`` is the tenant key under another spelling: ``record_key=`` lines name the tenant too."""

    def test_the_record_key_of_a_tenant_loses_the_tenant_segment_and_keeps_the_prefix(self) -> None:
        logged = log_tenant_record_key(TenantErasureEngine.record_key(TENANT_KEY))

        assert logged == f"ter_{log_tenant(TENANT_KEY)}"
        assert TENANT_KEY not in str(logged)

    def test_no_key_no_reference(self) -> None:
        assert log_tenant_record_key(None) is None and log_tenant_record_key("") is None


class TestInvitationLines:
    def test_accepting_an_invitation_logs_the_pseudonymised_tenant_beside_the_subject(self) -> None:
        tenants = Tenants()
        token = tenants.invite()

        with structlog.testing.capture_logs() as logs:
            tenants.service.accept_invitation(token, account(JOINER))

        accepted = next(event for event in logs if event["event"] == "invitation_accepted")
        assert accepted["tenant"] == log_tenant(PERSONAL)
        assert accepted["subject"].startswith("sub_")
        assert "tenant_key" not in accepted
        assert _leaks(logs, PERSONAL) == []

    @pytest.mark.parametrize(
        ("by_link", "event"), [(True, "link_invitation_created"), (False, "email_invitation_created")]
    )
    def test_creating_an_invitation_names_the_tenant_by_reference(self, by_link: bool, event: str) -> None:
        tenants = Tenants()

        with structlog.testing.capture_logs() as logs:
            tenants.invite(by_link=by_link)

        created = next(entry for entry in logs if entry["event"] == event)
        assert created["tenant"] == log_tenant(PERSONAL)
        assert _leaks(logs, PERSONAL) == []


class TestTenantErasureLines:
    def test_a_deletion_names_the_tenant_only_by_reference(self) -> None:
        service = tenant_service_for_deletion(existing=tenant(TENANT_KEY))

        with structlog.testing.capture_logs() as logs:
            delete_and_run(service, TENANT_KEY, **authorized(TENANT_KEY))

        by_event = {event["event"]: event for event in logs}
        assert by_event["tenant_erasure.authorized"]["tenant"] == log_tenant(TENANT_KEY)
        assert by_event["tenant_erasure.authorized"]["subject"].startswith("sub_")
        assert "tenant_deleted" in by_event
        assert _leaks(logs, TENANT_KEY) == [], _leaks(logs, TENANT_KEY)
