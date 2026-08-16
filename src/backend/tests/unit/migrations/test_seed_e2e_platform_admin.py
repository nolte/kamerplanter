"""The E2E platform-admin seed must refuse everywhere except an E2E stack (#1155).

This seed mints an account with full platform-admin rights from configuration.
That is a dangerous shape, and the module argues in its docstring that two gates
make it acceptable. An argument is not a control — these tests are the control.

The one that matters most is `test_refuses_when_cookie_secure_is_on`: it is the
difference between "a stray environment variable creates an administrator" and
"it takes a deployment that has also disabled cookie security". If that test is
ever deleted or weakened, the second gate is gone and only the docstring still
claims it exists.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.migrations import seed_e2e_platform_admin as seed


class _FakeUserRepo:
    def __init__(self, existing: Any = None) -> None:
        self.existing = existing
        self.created: list[Any] = []

    def get_by_email(self, email: str) -> Any:
        return self.existing

    def create(self, user: Any) -> Any:
        user.key = "u-seeded"
        self.created.append(user)
        return user


class _FakeTenantRepo:
    def __init__(self) -> None:
        self.created: list[Any] = []
        self.by_key: dict[str, Any] = {}

    def get_by_key(self, key: str) -> Any:
        return self.by_key.get(key)

    def create(self, tenant: Any) -> Any:
        if not getattr(tenant, "key", None):
            tenant.key = f"t-{len(self.created)}"
        self.created.append(tenant)
        self.by_key[tenant.key] = tenant
        return tenant


class _FakeMembershipRepo:
    def __init__(self) -> None:
        self.created: list[Any] = []

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Any:
        for m in self.created:
            if m.user_key == user_key and m.tenant_key == tenant_key:
                return m
        return None

    def create(self, membership: Any) -> Any:
        self.created.append(membership)
        return membership


@pytest.fixture
def repos(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any, Any]:
    """Wire the seed's three repository lookups to in-memory doubles."""
    user_repo, tenant_repo, membership_repo = _FakeUserRepo(), _FakeTenantRepo(), _FakeMembershipRepo()
    monkeypatch.setattr(seed, "get_user_repo", lambda: user_repo)
    monkeypatch.setattr(seed, "get_tenant_repo", lambda: tenant_repo)
    monkeypatch.setattr(seed, "get_membership_repo", lambda: membership_repo)
    return user_repo, tenant_repo, membership_repo


def _configure(
    monkeypatch: pytest.MonkeyPatch,
    *,
    email: str | None = "e2e-admin@kamerplanter.example",
    password: str | None = "e2e-admin-password",
    cookie_secure: bool = False,
) -> None:
    monkeypatch.setattr(seed.settings, "e2e_platform_admin_email", email, raising=False)
    monkeypatch.setattr(seed.settings, "e2e_platform_admin_password", password, raising=False)
    monkeypatch.setattr(seed.settings, "cookie_secure", cookie_secure, raising=False)


def test_seeds_the_account_when_both_gates_allow_it(
    monkeypatch: pytest.MonkeyPatch, repos: tuple[Any, Any, Any]
) -> None:
    """The positive control: without it the refusal tests could pass vacuously."""
    user_repo, tenant_repo, membership_repo = repos
    _configure(monkeypatch)

    seed.run_seed_e2e_platform_admin()

    assert len(user_repo.created) == 1, "the E2E stack must get its admin account"
    assert user_repo.created[0].email == "e2e-admin@kamerplanter.example"
    assert any(m.tenant_key == "platform" for m in membership_repo.created), (
        "the account is useless to the suite without the platform membership — that "
        "membership is the whole point of the seed"
    )


def test_refuses_when_cookie_secure_is_on(monkeypatch: pytest.MonkeyPatch, repos: tuple[Any, Any, Any]) -> None:
    """The second gate, and the reason the env var alone is not a backdoor.

    A deployment that sets the two E2E variables by accident — copied compose
    file, leaked CI environment — still gets nothing, because it will not also
    have turned off cookie security.
    """
    user_repo, _tenant_repo, membership_repo = repos
    _configure(monkeypatch, cookie_secure=True)

    seed.run_seed_e2e_platform_admin()

    assert user_repo.created == [], (
        "an account was created on a stack with cookie_secure on. The env-var gate "
        "is then the only thing standing between a stray variable and a platform "
        "administrator."
    )
    assert membership_repo.created == []


@pytest.mark.parametrize(
    ("email", "password"),
    [
        (None, None),
        ("e2e-admin@kamerplanter.example", None),
        (None, "e2e-admin-password"),
    ],
    ids=["neither", "email-only", "password-only"],
)
def test_refuses_a_missing_or_half_configured_pair(
    monkeypatch: pytest.MonkeyPatch,
    repos: tuple[Any, Any, Any],
    email: str | None,
    password: str | None,
) -> None:
    """Half-configured is a configuration error, never an invitation to improvise."""
    user_repo, _tenant_repo, _membership_repo = repos
    _configure(monkeypatch, email=email, password=password)

    seed.run_seed_e2e_platform_admin()

    assert user_repo.created == []


def test_leaves_an_existing_account_untouched(monkeypatch: pytest.MonkeyPatch, repos: tuple[Any, Any, Any]) -> None:
    """Re-seeding must not reset a password the running suite holds a token for.

    Startup seeds run on every boot, and the E2E stack is re-created often. A
    seed that rewrote the credential would work perfectly on a cold stack and
    fail only when a container restarted mid-run.
    """
    user_repo, _tenant_repo, membership_repo = repos
    existing = type("U", (), {"key": "u-existing", "password_hash": "original"})()
    user_repo.existing = existing
    _configure(monkeypatch)

    seed.run_seed_e2e_platform_admin()

    assert user_repo.created == [], "an existing account must not be re-created"
    assert existing.password_hash == "original"
    assert any(m.user_key == "u-existing" and m.tenant_key == "platform" for m in membership_repo.created), (
        "the membership is still ensured, so a database seeded before this seed existed gains it on the next boot"
    )
