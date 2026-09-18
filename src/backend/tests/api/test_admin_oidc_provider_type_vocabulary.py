"""`/admin/oidc-providers` refuses a provider type outside the vocabulary (#1497).

Before this, `provider_type` was a free-form `str` on the request schemas. A
provider registered as `GitHub`, `Google` or `GITHUB` was stored happily and then
served by the **generic OIDC branch** of `OAuthEngine.extract_user_info`: no
well-known endpoints were filled in, the GitHub address-list request never
happened, and nothing anywhere complained.

The decision (#1497) is the stricter of the two candidates in the issue —
constrain the boundary, do not normalise on write. Measured on the kind dev
cluster on 2026-09-18, read-only
(`FOR p IN oidc_provider_configs RETURN p.provider_type`): the collection holds
**zero** documents, so the measurement neither shows a stored odd spelling nor
excludes one. A vacuous measurement is not a licence to rewrite stored data,
which is why there is no migration and no normalisation; it is also why
`POST /{key}/test` reports the verdict on a stored record, the same shape #1477
used for the scope check.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.oidc_providers.router import router as oidc_router
from app.common.auth import require_platform_admin
from app.common.dependencies import get_encryption_engine, get_oauth_engine, get_oidc_config_repo
from app.common.enums import OidcProviderType
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


def _stored(provider_type: str = "GitHub") -> OidcProviderConfig:
    """A record carrying a spelling the new boundary refuses.

    Constructed directly, exactly as `repo.get_by_key` constructs it from a
    stored document — which is why the domain model keeps `provider_type: str`.
    An enum on the model would raise here, and a pre-gate record would answer 500
    on every read including the `/test` endpoint meant to report it.
    """
    return OidcProviderConfig(
        _key="cfg1",
        slug="gh",
        display_name="GitHub",
        provider_type=provider_type,
        issuer_url="https://github.com",
        client_id="cid",
        scopes=["user:email"],
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
        # `github` needs this scope since #1477; without it the 422 under test
        # could come from the scope gate instead of the vocabulary.
        "scopes": ["read:user", "user:email"],
    }
    body.update(overrides)
    return body


class TestCreate:
    @pytest.mark.parametrize("spelling", ["GitHub", "GITHUB", "Google", "gitHub ", "twitter", ""])
    def test_a_spelling_outside_the_vocabulary_is_refused_with_422(self, spelling: str) -> None:
        """Was 201 before #1497, followed by silent service from the generic branch."""
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(provider_type=spelling))
        assert resp.status_code == 422, resp.text
        assert "provider_type" in resp.text
        repo.create.assert_not_called()

    @pytest.mark.parametrize("spelling", ["google", "github", "apple", "oidc"])
    def test_every_member_of_the_vocabulary_is_accepted(self, spelling: str) -> None:
        """The control: without it the 422 above could refuse everything."""
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(provider_type=spelling))
        assert resp.status_code == 201, resp.text
        assert resp.json()["provider_type"] == spelling

    def test_the_stored_value_is_a_plain_string(self) -> None:
        """What reaches persistence must still be the bare spelling.

        The domain model keeps `str`; a member object leaking into the document
        would compare fine in Python and read back differently.
        """
        repo = _repo()
        assert _client(repo).post(BASE, json=_create_body()).status_code == 201
        stored = repo.create.call_args.args[0]
        assert stored.provider_type == "github"
        assert stored.model_dump()["provider_type"] == "github"

    def test_the_omitted_field_still_defaults_to_generic_oidc(self) -> None:
        repo = _repo()
        body = _create_body()
        body.pop("provider_type")
        resp = _client(repo).post(BASE, json=body)
        assert resp.status_code == 201, resp.text
        assert resp.json()["provider_type"] == OidcProviderType.OIDC.value

    def test_local_is_not_a_federated_provider_type(self) -> None:
        """`AuthProviderType` carries `local`; this vocabulary must not.

        A provider registered as `local` would dispatch to the generic OIDC
        branch — the exact silence this issue closes — while naming the one
        authentication kind that has no federation at all.
        """
        repo = _repo()
        resp = _client(repo).post(BASE, json=_create_body(provider_type="local"))
        assert resp.status_code == 422, resp.text
        repo.create.assert_not_called()


class TestUpdate:
    @pytest.mark.parametrize("spelling", ["GitHub", "GOOGLE", "twitter"])
    def test_a_spelling_outside_the_vocabulary_is_refused_with_422(self, spelling: str) -> None:
        """The update path matters more than create.

        The router writes body fields onto the loaded model with `setattr`, and
        pydantic does not validate on assignment — an unknown value would be
        stored first and only then take effect, silently.
        """
        repo = _repo(_stored(provider_type="github"))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"provider_type": spelling})
        assert resp.status_code == 422, resp.text
        repo.update.assert_not_called()

    def test_a_member_of_the_vocabulary_is_accepted(self) -> None:
        repo = _repo(_stored(provider_type="github"))
        resp = _client(repo).put(f"{BASE}/cfg1", json={"provider_type": "oidc"})
        assert resp.status_code == 200, resp.text
        assert repo.update.call_args.args[1].provider_type == "oidc"

    def test_an_unrelated_edit_to_a_pre_gate_record_still_works(self) -> None:
        """A record stored before the gate stays editable.

        The gate is on the request, not on the stored state: refusing every edit
        to a pre-gate record would leave it unrepairable.
        """
        repo = _repo(_stored())
        resp = _client(repo).put(f"{BASE}/cfg1", json={"display_name": "GitHub Enterprise"})
        assert resp.status_code == 200, resp.text
        repo.update.assert_called_once()

    def test_a_pre_gate_record_can_be_repaired(self) -> None:
        repo = _repo(_stored())
        resp = _client(repo).put(f"{BASE}/cfg1", json={"provider_type": "github"})
        assert resp.status_code == 200, resp.text
        assert repo.update.call_args.args[1].provider_type == "github"


class TestTheTestEndpoint:
    """The only path on which a record stored before the gate reports itself."""

    def _post_test(self, repo: MagicMock):
        target = "app.domain.engines.oauth_engine.OAuthEngine.fetch_discovery_document"
        with patch(target, return_value=DISCOVERY):
            return _client(repo).post(f"{BASE}/cfg1/test")

    def test_it_reports_a_stored_spelling_outside_the_vocabulary(self) -> None:
        resp = self._post_test(_repo(_stored()))
        assert resp.status_code == 200, resp.text
        check = resp.json()["provider_type_check"]
        assert check["ok"] is False
        assert check["provider_type"] == "GitHub"
        assert check["known_provider_types"] == [m.value for m in OidcProviderType]
        assert "github" in check["detail"]

    def test_a_record_inside_the_vocabulary_reports_ok(self) -> None:
        """The control: without it `ok` could be hard-wired to False."""
        resp = self._post_test(_repo(_stored(provider_type="github")))
        assert resp.status_code == 200, resp.text
        assert resp.json()["provider_type_check"]["ok"] is True

    def test_the_verdict_survives_a_failing_discovery_fetch(self) -> None:
        """GitHub publishes no discovery document, so this is its only path."""
        target = "app.domain.engines.oauth_engine.OAuthEngine.fetch_discovery_document"
        with patch(target, side_effect=RuntimeError("404 Not Found")):
            resp = _client(_repo(_stored())).post(f"{BASE}/cfg1/test")
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"].startswith("Discovery fetch failed")
        assert resp.json()["provider_type_check"]["ok"] is False

    def test_the_scope_verdict_from_1477_is_still_carried(self) -> None:
        resp = self._post_test(_repo(_stored(provider_type="github")))
        assert resp.json()["scope_check"]["ok"] is True
