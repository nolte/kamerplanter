"""#2162: ``create_email_invitation`` mails the accept link after storing the invitation and reports the outcome.

The end-to-end measurement (real routes, real repositories, the real templates) is
``tests/integration/test_email_invitation_delivery_reach.py``; this holds the service's contract with
doubles: the mail is sent only once the invitation is stored, to the invited address, with the stored
token's link; a send that does not leave is reported (``delivered=False``) and neither raised nor
swallowed into "sent"; an error outside that set (a defect) is not hidden.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import structlog.testing

from app.common.enums import TenantRole
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.email_service import EmailUndeliverableError
from app.domain.models.invitation import Invitation
from app.domain.models.tenant import Tenant
from app.domain.services.tenant_service import TenantService

TENANT = "t-garden"
INVITED = "friend@example.org"
FRONTEND = "https://garden.example.net"


def _service(mailer: MagicMock | None) -> tuple[TenantService, MagicMock, list[str]]:
    order: list[str] = []
    invitations = MagicMock()

    def _create(invitation: Invitation) -> Invitation:
        order.append("stored")
        return invitation.model_copy(update={"key": "i-1"})

    invitations.create.side_effect = _create
    if mailer is not None:

        def _send(**_: object) -> None:
            if mailer.fail is not None:
                raise mailer.fail
            order.append("mailed")

        mailer.send_invitation_email.side_effect = _send
    tenants = MagicMock()
    tenants.get_by_key.return_value = Tenant(_key=TENANT, name="Garden", slug="garden", owner_user_key="u-lead")
    service = TenantService(
        tenant_repo=tenants,
        membership_repo=MagicMock(),
        invitation_repo=invitations,
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        email_service=mailer,
        frontend_url=FRONTEND,
    )
    return service, invitations, order


def _mailer(fail: BaseException | None = None) -> MagicMock:
    mailer = MagicMock()
    mailer.fail = fail
    return mailer


def test_the_stored_invitation_is_mailed_with_its_own_link() -> None:
    mailer = _mailer()
    service, invitations, order = _service(mailer)

    link = service.create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.VIEWER)

    assert order == ["stored", "mailed"]
    mailer.send_invitation_email.assert_called_once_with(to_email=INVITED, token=link.token, frontend_url=FRONTEND)
    stored: Invitation = invitations.create.call_args.args[0]
    assert stored.token_hash == InvitationEngine.hash_token(link.token)
    assert link.delivered is True
    assert link.accept_url == f"{FRONTEND}/invitations/accept?token={link.token}"


@pytest.mark.parametrize(
    "failure",
    [EmailUndeliverableError("console outside debug"), NotImplementedError(), OSError("smtp down")],
    ids=["undeliverable", "not-implemented", "transport"],
)
def test_a_mail_that_does_not_leave_is_reported_not_raised(failure: BaseException) -> None:
    service, invitations, _ = _service(_mailer(failure))

    with structlog.testing.capture_logs() as logs:
        link = service.create_email_invitation(TENANT, "u-lead", INVITED)

    assert link.delivered is False
    invitations.create.assert_called_once()
    (warning,) = [entry for entry in logs if entry["event"] == "email_invitation_not_sent"]
    assert warning["error_type"] == type(failure).__name__
    assert INVITED not in repr(logs)
    assert link.token not in repr(logs)


def test_without_a_mailer_nothing_is_claimed() -> None:
    service, _, _ = _service(None)

    link = service.create_email_invitation(TENANT, "u-lead", INVITED)

    assert link.delivered is False
    assert link.accept_url.endswith(link.token)


def test_a_defect_in_the_send_is_not_reported_as_an_undelivered_mail() -> None:
    """Only "the mail did not leave" becomes ``delivered=False``; a programming error still surfaces."""
    service, _, _ = _service(_mailer(TypeError("bug")))

    with pytest.raises(TypeError):
        service.create_email_invitation(TENANT, "u-lead", INVITED)


def test_a_link_invitation_sends_nothing_and_claims_nothing() -> None:
    mailer = _mailer()
    service, _, _ = _service(mailer)

    link = service.create_link_invitation(TENANT, "u-lead")

    mailer.send_invitation_email.assert_not_called()
    assert link.delivered is None
    assert link.accept_url == f"{FRONTEND}/invitations/accept?token={link.token}"
