"""A platform admin cannot lock the platform out by a deactivation — MT-045.4 (#2144).

``PATCH /admin/platform/users/{key}`` with ``is_active: false`` passed the admin's
step-up and deactivated whoever it named: the admin themselves, or the last
account holding the platform role. Either way nobody was left who could
reactivate anyone — recovery only through the database.

Two refusals, both before the step-up asks for a password (a refusal never
spends a factor), both the project's business-rule answer (``ValidationError``,
422) like INV-1's "last manager" refusal:

* the requester deactivating their own account;
* deactivating an active platform admin when no *other* active account holds the
  platform role (``lead`` in the ``platform`` tenant, an active membership of an
  active user).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.dependencies import get_user_service
from app.common.enums import TenantRole
from app.common.exceptions import ValidationError
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.user_service import UserService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

_REQUESTER = User(_key="admin-1", email="admin-1@example.org", display_name="Admin 1")


def _user(key: str, *, active: bool = True) -> User:
    return User(_key=key, email=f"{key}@example.org", display_name=key, is_active=active)


def _lead(user_key: str, *, role: TenantRole = TenantRole.LEAD) -> Membership:
    return Membership(_key=f"m-{user_key}", user_key=user_key, tenant_key="platform", role=role)


def _service(users: dict[str, User], platform: list[Membership]) -> tuple[UserService, MagicMock, PassedStepUpVerifier]:
    user_repo = MagicMock()
    user_repo.get_or_raise.side_effect = lambda key: users[key]
    user_repo.get_by_key.side_effect = users.get
    user_repo.update_fields.side_effect = lambda key, data: users[key].model_copy(update=data)
    memberships = MagicMock()
    memberships.active_memberships_of.side_effect = lambda *, tenant_key: platform if tenant_key == "platform" else []
    verifier = PassedStepUpVerifier()
    service = UserService(user_repo, step_up_verifier=verifier, membership_repo=memberships)  # type: ignore[arg-type]
    return service, user_repo, verifier


def _deactivate(service: UserService, key: str) -> User:
    return service.admin_update_user(key, {"is_active": False}, requester=_REQUESTER, client_ip=None, **STEP_UP_PASSED)


def test_an_admin_cannot_deactivate_their_own_account() -> None:
    users = {"admin-1": _user("admin-1"), "admin-2": _user("admin-2")}
    service, repo, verifier = _service(users, [_lead("admin-1"), _lead("admin-2")])

    with pytest.raises(ValidationError, match="own account"):
        _deactivate(service, "admin-1")

    repo.update_fields.assert_not_called()
    assert verifier.actions == []


def test_the_last_other_platform_admin_cannot_be_deactivated() -> None:
    # admin-1 acts without holding the platform role in the store (a stale or
    # light-mode session); admin-2 is the only active platform lead.
    users = {"admin-1": _user("admin-1"), "admin-2": _user("admin-2")}
    service, repo, verifier = _service(users, [_lead("admin-2")])

    with pytest.raises(ValidationError, match="last platform administrator"):
        _deactivate(service, "admin-2")

    repo.update_fields.assert_not_called()
    assert verifier.actions == []


def test_a_deactivated_co_admin_does_not_count_as_a_remaining_admin() -> None:
    users = {"admin-1": _user("admin-1"), "admin-2": _user("admin-2"), "admin-3": _user("admin-3", active=False)}
    service, repo, _ = _service(users, [_lead("admin-2"), _lead("admin-3")])

    with pytest.raises(ValidationError, match="last platform administrator"):
        _deactivate(service, "admin-2")

    repo.update_fields.assert_not_called()


def test_a_platform_admin_may_be_deactivated_while_another_remains() -> None:
    users = {"admin-1": _user("admin-1"), "admin-2": _user("admin-2")}
    service, repo, verifier = _service(users, [_lead("admin-1"), _lead("admin-2")])

    _deactivate(service, "admin-2")

    repo.update_fields.assert_called_once()
    assert verifier.actions == ["admin_account_update"]


def test_an_ordinary_account_may_be_deactivated() -> None:
    users = {"admin-1": _user("admin-1"), "grower-1": _user("grower-1")}
    service, repo, _ = _service(users, [_lead("admin-1"), _lead("grower-1", role=TenantRole.VIEWER)])

    _deactivate(service, "grower-1")

    repo.update_fields.assert_called_once()


def test_reactivating_oneself_is_not_refused() -> None:
    users = {"admin-1": _user("admin-1", active=False)}
    service, repo, _ = _service(users, [])

    service.admin_update_user("admin-1", {"is_active": True}, requester=_REQUESTER, client_ip=None, **STEP_UP_PASSED)

    repo.update_fields.assert_called_once()


def test_the_production_provider_wires_the_membership_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    """The last-admin rule reads memberships; a provider without them would make it inert."""
    monkeypatch.setattr("app.common.dependencies.get_db", lambda: SimpleNamespace())

    service = get_user_service()

    assert service._membership_repo is not None
