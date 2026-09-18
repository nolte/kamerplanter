"""A GitHub provider whose scopes cannot yield the email claim is refused (#1477).

`_fetch_github_user_info` needs `GET /user/emails`, which GitHub answers only for
a token carrying `user:email` (or its parent scope `user`). Without it every
sign-in falls into the "no claim → not verified → no auto-link" branch of #1403,
and the only trace is one `github_email_verification_unavailable` log line per
sign-in — nowhere near the administration screen where the scope list was typed.

The decision on #1477 is to refuse the configuration rather than to carry a
status field: there is no admin UI consuming `/admin/oidc-providers` (measured
2026-09-17: no frontend caller of any of its six routes), so a status field
would have had no reader.

The predicate lives next to its consumer, in the engine that performs the
`/user/emails` request, and reads the provider type through the same helper the
sign-in dispatch uses — a second spelling of "is this GitHub" is exactly how the
gate and the branch it guards drift apart.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import ValidationError
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig


def _config(provider_type: str, scopes: list[str]) -> OidcProviderConfig:
    return OidcProviderConfig(
        slug="gh",
        display_name="GitHub",
        provider_type=provider_type,
        issuer_url="https://github.com",
        client_id="cid",
        scopes=scopes,
    )


class TestTheScopeCheck:
    """`check_provider_scopes` — the structured answer, no exception."""

    def test_github_without_the_email_scope_is_not_ok(self) -> None:
        check = OAuthEngine().check_provider_scopes(_config("github", ["openid", "email", "profile"]))
        assert check.ok is False
        assert check.missing_scopes == ["user:email"]
        assert "user:email" in check.detail

    def test_the_default_scope_list_is_the_failing_one(self) -> None:
        """The default is not a corner case — it is what an operator gets by not typing."""
        default = OidcProviderConfig(
            slug="gh",
            display_name="GitHub",
            provider_type="github",
            issuer_url="https://github.com",
            client_id="cid",
        )
        assert OAuthEngine().check_provider_scopes(default).ok is False

    def test_github_with_the_email_scope_is_ok(self) -> None:
        check = OAuthEngine().check_provider_scopes(_config("github", ["user:email"]))
        assert check.ok is True
        assert check.missing_scopes == []

    def test_a_non_github_provider_is_ok_without_the_scope(self) -> None:
        """The control: without it the assertions above would hold for every provider."""
        for provider_type in ("oidc", "google", "apple"):
            check = OAuthEngine().check_provider_scopes(_config(provider_type, ["openid", "email"]))
            assert check.ok is True, provider_type
            assert check.missing_scopes == []


class TestSpellingsOfTheSameScope:
    """Name a spelling of the same thing my pattern does not match.

    `scopes` is a `list[str]`, but the value an operator pastes is an OAuth scope
    *string*, and both GitHub's documentation and every copy-paste source write
    it space-delimited. A membership test against the list (`"user:email" in
    config.scopes`) reads as complete and refuses a provider that works.
    """

    @pytest.mark.parametrize(
        "scopes",
        [
            pytest.param(["user:email"], id="own-entry"),
            pytest.param(["read:user user:email"], id="space-delimited-in-one-entry"),
            pytest.param(["openid", "profile user:email"], id="space-delimited-among-others"),
            pytest.param(["read:user,user:email"], id="comma-delimited"),
            pytest.param(["  user:email  "], id="padded"),
            pytest.param(["user"], id="parent-scope-user-grants-user-email"),
            pytest.param(["read:user user"], id="parent-scope-among-others"),
        ],
    )
    def test_every_working_spelling_is_accepted(self, scopes: list[str]) -> None:
        assert OAuthEngine().check_provider_scopes(_config("github", scopes)).ok is True

    @pytest.mark.parametrize(
        "scopes",
        [
            pytest.param(["read:user"], id="read-user-does-not-grant-addresses"),
            pytest.param(["user:follow"], id="a-different-user-subscope"),
            pytest.param(["useremail"], id="missing-colon"),
            pytest.param([], id="empty"),
        ],
    )
    def test_a_non_granting_spelling_is_refused(self, scopes: list[str]) -> None:
        assert OAuthEngine().check_provider_scopes(_config("github", scopes)).ok is False

    def test_the_wrong_case_is_refused_on_purpose(self) -> None:
        """GitHub scope names are lower-case; `USER:EMAIL` is not one of them.

        Accepting it case-insensitively would wave through a configuration that
        still answers 403 on `/user/emails` — the very silence this gate exists
        to end. The refusal names the casing so the operator is not left
        guessing.
        """
        check = OAuthEngine().check_provider_scopes(_config("github", ["USER:EMAIL"]))
        assert check.ok is False
        assert "lower-case" in check.detail


class TestTheRaisingGuard:
    """`require_supported_scopes` — what a write route calls."""

    def test_it_raises_a_422_validation_error_for_github_without_the_scope(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            OAuthEngine().require_supported_scopes(_config("github", ["openid", "email"]))
        assert excinfo.value.status_code == 422
        assert "user:email" in excinfo.value.message

    def test_it_passes_a_github_provider_that_carries_the_scope(self) -> None:
        OAuthEngine().require_supported_scopes(_config("github", ["read:user", "user:email"]))

    def test_it_passes_a_generic_oidc_provider(self) -> None:
        OAuthEngine().require_supported_scopes(_config("oidc", ["openid", "email", "profile"]))


class TestTheProviderTypeDiscriminator:
    """One spelling of "is this GitHub", shared with the sign-in dispatch."""

    def test_the_sign_in_dispatch_and_the_gate_read_the_same_helper(self) -> None:
        import inspect

        from app.domain.models.oidc_config import is_github_provider

        source = inspect.getsource(OAuthEngine.extract_user_info)
        assert "is_github_provider(" in source, (
            "extract_user_info must decide GitHub through the shared helper; a second "
            "literal comparison lets the gate and the branch it guards drift apart."
        )
        assert is_github_provider("github") is True
        assert is_github_provider("oidc") is False

    def test_a_case_variant_is_not_github_on_either_side(self) -> None:
        """Measured, not assumed: `extract_user_info` matches `"github"` exactly.

        A provider typed as `GitHub` therefore takes the generic OIDC branch at
        sign-in and never calls `/user/emails`, so it must not be refused for a
        scope it does not need. Whether that silent fallback is itself a defect
        is out of this issue's scope (follow-up: #1497).
        """
        from app.domain.models.oidc_config import is_github_provider

        assert is_github_provider("GitHub") is False
        assert OAuthEngine().check_provider_scopes(_config("GitHub", ["openid"])).ok is True
