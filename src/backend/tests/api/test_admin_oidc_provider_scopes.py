"""`/admin/oidc-providers` refuses a GitHub provider without `user:email` (#1477).

Before this, the only signal was one `github_email_verification_unavailable` log
line per sign-in: the provider stored fine, every sign-in silently produced no
`email_verified` claim, #1403 refused the auto-link, and the operator learned of
it from a user who could not link.

The decision (#1477, 2026-09-17) is to refuse at the configuration rather than to
carry a status field on the record — measured: no frontend calls any of the six
`/admin/oidc-providers` routes, so a status field would have had no reader.
`POST /{key}/test` reports the same verdict for configurations stored before the
gate existed; there is no migration, because nothing seeds an OIDC provider.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.oidc_providers.router import router as oidc_router
from app.common.auth import require_platform_admin
from app.common.dependencies import get_encryption_engine, get_oauth_engine, get_oidc_config_repo
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig

BASE = "/api/v1/admin/oidc-providers"

DISCOVERY = {
    "issuer": "https://idp.example",
    "authorization_endpoint": "https://idp.example/authorize",
    "token_endpoint": "https://idp.example/token",
}


def _stored(provider_type: str = "github", scopes: list[str] | None = None) -> OidcProviderConfig:
    return OidcProviderConfig(
        _key="cfg1",
        slug="gh",
        display_name="GitHub",
        provider_type=provider_type,
        issuer_url="https://github.com",
        client_id="cid",
        scopes=["openid", "email", "profile"] if scopes is None else scopes,
    )


def _repo(stored: OidcProviderConfig | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_slug.return_value = None
    repo.get_by_key.return_value = stored
    repo.create.side_effect = lambda c: c.model_copy(update={"key": "cfg1"})
    repo.update.side_effect = lambda key, c: c
    return repo


def _client(repo: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(oidc_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="user_admin")
    app.dependency_overrides[get_oidc_config_repo] = lambda: repo
    app.dependency_overrides[get_encryption_engine] = lambda: EncryptionEngine(Fernet.generate_key().decode())
    app.dependency_overrides[get_oauth_engine] = OAuthEngine
    return TestClient(app)


def _create_body(**overrides) -> dict:
    body = {
        "slug": "gh",
        "display_name": "GitHub",
        "provider_type": "github",
        "issuer_url": "https://github.com",
        "client_id": "cid",
        "client_secret": "secret",
    }
    body.update(overrides)
    return body


class TestCreate:
    def test_a_github_provider_without_the_scope_is_refused_with_422(self) -> None:
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body())
        assert resp.status_code == 422, resp.text
        assert "user:email" in resp.text
        # The refusal is the point: nothing was written.
        repo.create.assert_not_called()

    def test_the_omitted_scope_list_is_refused_too(self) -> None:
        """The default `["openid", "email", "profile"]` is what GitHub ignores."""
        repo = _repo()
        body = _create_body()
        body.pop("scopes", None)
        resp = _client(repo).post(BASE, json=body)
        assert resp.status_code == 422, resp.text
        repo.create.assert_not_called()

    def test_a_github_provider_with_the_scope_is_created(self) -> None:
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(scopes=["read:user", "user:email"]))
        assert resp.status_code == 201, resp.text
        repo.create.assert_called_once()

    def test_a_space_delimited_scope_string_is_created(self) -> None:
        """The spelling a membership test against the list would have refused."""
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(scopes=["read:user user:email"]))
        assert resp.status_code == 201, resp.text

    def test_a_generic_oidc_provider_is_unaffected(self) -> None:
        """The control: without it the 422 above could come from any provider."""
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(provider_type="oidc"))
        assert resp.status_code == 201, resp.text


class TestUpdate:
    def test_dropping_the_scope_from_a_github_provider_is_refused(self) -> None:
        repo = _repo(_stored(scopes=["user:email"]))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"scopes": ["openid", "email"]})
        assert resp.status_code == 422, resp.text
        repo.update.assert_not_called()

    def test_switching_an_existing_provider_to_github_is_refused(self) -> None:
        """The merged state decides — the body names no scope at all."""
        repo = _repo(_stored(provider_type="oidc", scopes=["openid", "email"]))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"provider_type": "github"})
        assert resp.status_code == 422, resp.text
        repo.update.assert_not_called()

    def test_repairing_a_stored_provider_succeeds(self) -> None:
        """A body that adds the scope to a stored GitHub provider goes through.

        Also the control for the merge: checking the body alone would refuse this
        one, because the body names no `provider_type`.
        """
        repo = _repo(_stored(scopes=["openid"]))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"scopes": ["openid", "user:email"]})
        assert resp.status_code == 200, resp.text
        repo.update.assert_called_once()

    def test_an_unrelated_edit_to_a_healthy_provider_still_works(self) -> None:
        repo = _repo(_stored(scopes=["user:email"]))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"display_name": "GitHub Enterprise"})
        assert resp.status_code == 200, resp.text


class TestTheTestEndpoint:
    """The path for configurations stored before the gate existed."""

    def _post_test(self, repo: MagicMock, *, discovery_raises: bool = False):
        target = "app.domain.engines.oauth_engine.OAuthEngine.fetch_discovery_document"
        side_effect = RuntimeError("404 Not Found") if discovery_raises else None
        with patch(target, side_effect=side_effect, return_value=DISCOVERY):
            return _client(repo).post(f"{BASE}/cfg1/test")

    def test_it_reports_the_missing_scope_as_a_structured_field(self) -> None:
        resp = self._post_test(_repo(_stored()))
        assert resp.status_code == 200, resp.text
        check = resp.json()["scope_check"]
        assert check["ok"] is False
        assert check["missing_scopes"] == ["user:email"]
        assert check["provider_type"] == "github"
        assert "user:email" in check["detail"]

    def test_the_verdict_survives_a_failing_discovery_fetch(self) -> None:
        """GitHub publishes no discovery document, so this is GitHub's ONLY path.

        A verdict computed after the early return would be unreachable for every
        provider it is about.
        """
        resp = self._post_test(_repo(_stored()), discovery_raises=True)
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"].startswith("Discovery fetch failed")
        assert resp.json()["scope_check"]["ok"] is False

    def test_a_healthy_provider_reports_ok(self) -> None:
        """The control: without it `ok` could be hard-wired to False."""
        resp = self._post_test(_repo(_stored(scopes=["user:email"])))
        assert resp.status_code == 200, resp.text
        check = resp.json()["scope_check"]
        assert check["ok"] is True
        assert check["missing_scopes"] == []

    def test_the_discovery_message_is_still_carried(self) -> None:
        resp = self._post_test(_repo(_stored(provider_type="oidc", scopes=["openid"])))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "validated successfully" in body["message"]
        assert body["scope_check"]["ok"] is True
