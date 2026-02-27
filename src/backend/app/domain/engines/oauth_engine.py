"""OAuth/OIDC engine — STUB for follow-up implementation.

Full implementation will handle:
- OIDC discovery document fetching
- Authorization URL generation with PKCE
- Token exchange (authorization code -> tokens)
- UserInfo endpoint parsing
- Provider-specific quirks (Apple, GitHub)
"""

from app.domain.models.auth import OAuthRedirect, OAuthUserInfo


class OAuthEngine:
    """Pure logic for OAuth/OIDC flows — STUB."""

    def generate_authorization_url(
        self,
        issuer_url: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
    ) -> OAuthRedirect:
        raise NotImplementedError("OAuth engine not yet implemented. Coming in follow-up.")

    def exchange_code(
        self,
        issuer_url: str,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthUserInfo:
        raise NotImplementedError("OAuth engine not yet implemented. Coming in follow-up.")
