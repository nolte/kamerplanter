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

from unittest.mock import MagicMock, patch

from tests.support.oidc_admin import (
    BASE,
    DISCOVERY,
    DISCOVERY_TARGET,
    admin_client,
    provider_repo,
    stored_provider,
)


def _stored(provider_type: str = "github", scopes: list[str] | None = None):
    return stored_provider(provider_type=provider_type, scopes=scopes)


def _repo(stored=None) -> MagicMock:
    return provider_repo(stored)


def _client(repo: MagicMock):
    return admin_client(repo)


def _create_body(**overrides) -> dict:
    """The #1477 body: NO scopes by default, because the scope gate is the subject.

    Deliberately not `tests.support.oidc_admin.create_body`, which carries
    `user:email` so that a 422 there is about the provider type (#1497). Sharing
    that default here would make every scope test pass for the wrong reason.
    """
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
        side_effect = RuntimeError("404 Not Found") if discovery_raises else None
        with patch(DISCOVERY_TARGET, side_effect=side_effect, return_value=DISCOVERY):
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
