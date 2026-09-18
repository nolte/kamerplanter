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

from unittest.mock import MagicMock, patch

import pytest

from app.common.enums import OidcProviderType
from tests.support.oidc_admin import (
    BASE,
    DISCOVERY,
    DISCOVERY_TARGET,
    admin_client,
    create_body,
    provider_repo,
    stored_provider,
)


def _stored(provider_type: str = "GitHub"):
    """A record carrying a spelling the new boundary refuses.

    Constructed directly, exactly as `repo.get_by_key` constructs it from a
    stored document — which is why the domain model keeps `provider_type: str`.
    An enum on the model would raise here, and a pre-gate record would answer 500
    on every read including the `/test` endpoint meant to report it.
    """
    return stored_provider(provider_type=provider_type, scopes=["user:email"])


class TestCreate:
    @pytest.mark.parametrize("spelling", ["GitHub", "GITHUB", "Google", "gitHub ", "twitter", ""])
    def test_a_spelling_outside_the_vocabulary_is_refused_with_422(self, spelling: str) -> None:
        """Was 201 before #1497, followed by silent service from the generic branch."""
        repo = provider_repo()
        resp = admin_client(repo).post(BASE, json=create_body(provider_type=spelling))
        assert resp.status_code == 422, resp.text
        assert "provider_type" in resp.text
        repo.create.assert_not_called()

    @pytest.mark.parametrize("spelling", ["google", "github", "apple", "oidc"])
    def test_every_member_of_the_vocabulary_is_accepted(self, spelling: str) -> None:
        """The control: without it the 422 above could refuse everything."""
        repo = provider_repo()
        resp = admin_client(repo).post(BASE, json=create_body(provider_type=spelling))
        assert resp.status_code == 201, resp.text
        assert resp.json()["provider_type"] == spelling

    def test_the_stored_value_is_a_plain_str_not_an_enum_member(self) -> None:
        """What reaches persistence must be the bare spelling, not a member object.

        `== "github"` is true for a `StrEnum` member too, so an equality check
        here would pass whether or not the router converts. The type is what
        distinguishes the two.

        On THIS path the assertion holds for two independent reasons, measured:
        removing `_plain()` from the create route leaves it green, because
        `OidcProviderConfig(...)` coerces on construction. The route that needs
        the rule is the update one below, which assigns with `setattr`; that test
        does go red without it. Recorded so the redundancy here is not mistaken
        for the falsification.
        """
        repo = provider_repo()
        assert admin_client(repo).post(BASE, json=create_body()).status_code == 201
        written = repo.create.call_args.args[0].provider_type
        assert written == "github"
        assert type(written) is str, f"stored as {type(written).__name__}, not a plain str"

    def test_the_omitted_field_still_defaults_to_generic_oidc(self) -> None:
        repo = provider_repo()
        body = create_body()
        body.pop("provider_type")
        resp = admin_client(repo).post(BASE, json=body)
        assert resp.status_code == 201, resp.text
        assert resp.json()["provider_type"] == OidcProviderType.OIDC.value
        assert type(repo.create.call_args.args[0].provider_type) is str

    def test_local_is_not_a_federated_provider_type(self) -> None:
        """`AuthProviderType` carries `local`; this vocabulary must not.

        A provider registered as `local` would dispatch to the generic OIDC
        branch — the exact silence this issue closes — while naming the one
        authentication kind that has no federation at all.
        """
        repo = provider_repo()
        resp = admin_client(repo).post(BASE, json=create_body(provider_type="local"))
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
        repo = provider_repo(_stored(provider_type="github"))
        resp = admin_client(repo).put(f"{BASE}/cfg1", json={"provider_type": spelling})
        assert resp.status_code == 422, resp.text
        repo.update.assert_not_called()

    def test_a_member_of_the_vocabulary_is_accepted_and_stored_as_a_plain_str(self) -> None:
        """The load-bearing one: `setattr` does not validate, so nothing coerces.

        Measured: with `_plain()` removed from the update route this reads
        `stored as OidcProviderType, not a plain str`.
        """
        repo = provider_repo(_stored(provider_type="github"))
        resp = admin_client(repo).put(f"{BASE}/cfg1", json={"provider_type": "oidc"})
        assert resp.status_code == 200, resp.text
        written = repo.update.call_args.args[1].provider_type
        assert written == "oidc"
        assert type(written) is str, f"stored as {type(written).__name__}, not a plain str"

    def test_an_unrelated_edit_to_a_pre_gate_record_still_works(self) -> None:
        """A record stored before the gate stays editable.

        The gate is on the request, not on the stored state: refusing every edit
        to a pre-gate record would leave it unrepairable.
        """
        repo = provider_repo(_stored())
        resp = admin_client(repo).put(f"{BASE}/cfg1", json={"display_name": "GitHub Enterprise"})
        assert resp.status_code == 200, resp.text
        repo.update.assert_called_once()

    def test_a_pre_gate_record_can_be_repaired(self) -> None:
        repo = provider_repo(_stored())
        resp = admin_client(repo).put(f"{BASE}/cfg1", json={"provider_type": "github"})
        assert resp.status_code == 200, resp.text
        written = repo.update.call_args.args[1].provider_type
        assert written == "github"
        assert type(written) is str

    def test_an_unrelated_field_survives_the_conversion_rule_unchanged(self) -> None:
        """`_plain()` is narrow on purpose: it must only strip enum members.

        The rule it replaced (`model_dump(mode="json")`) would have converted
        every field on its way to an unvalidated `setattr`.
        """
        repo = provider_repo(_stored(provider_type="github"))
        resp = admin_client(repo).put(f"{BASE}/cfg1", json={"scopes": ["user:email", "read:user"]})
        assert resp.status_code == 200, resp.text
        assert repo.update.call_args.args[1].scopes == ["user:email", "read:user"]


class TestTheTestEndpoint:
    """The only path on which a record stored before the gate reports itself."""

    def _post_test(self, repo: MagicMock):
        with patch(DISCOVERY_TARGET, return_value=DISCOVERY):
            return admin_client(repo).post(f"{BASE}/cfg1/test")

    def test_it_reports_a_stored_spelling_outside_the_vocabulary(self) -> None:
        resp = self._post_test(provider_repo(_stored()))
        assert resp.status_code == 200, resp.text
        check = resp.json()["provider_type_check"]
        assert check["ok"] is False
        assert check["provider_type"] == "GitHub"
        assert check["known_provider_types"] == [m.value for m in OidcProviderType]
        assert "github" in check["detail"]

    def test_a_record_inside_the_vocabulary_reports_ok(self) -> None:
        """The control: without it `ok` could be hard-wired to False."""
        resp = self._post_test(provider_repo(_stored(provider_type="github")))
        assert resp.status_code == 200, resp.text
        assert resp.json()["provider_type_check"]["ok"] is True

    def test_the_verdict_survives_a_failing_discovery_fetch(self) -> None:
        """GitHub publishes no discovery document, so this is its only path."""
        with patch(DISCOVERY_TARGET, side_effect=RuntimeError("404 Not Found")):
            resp = admin_client(provider_repo(_stored())).post(f"{BASE}/cfg1/test")
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"].startswith("Discovery fetch failed")
        assert resp.json()["provider_type_check"]["ok"] is False

    def test_the_scope_verdict_from_1477_is_still_carried(self) -> None:
        resp = self._post_test(provider_repo(_stored(provider_type="github")))
        assert resp.json()["scope_check"]["ok"] is True
