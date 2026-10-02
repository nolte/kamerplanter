"""A fake OpenID Connect provider for the login tests (#1936, #1969).

It answers, over :class:`httpx.MockTransport`, exactly the requests the real
:class:`~app.domain.engines.oauth_engine.OAuthEngine` makes — token endpoint,
userinfo endpoint, discovery document, JWKS — so the engine under test is the
production one and the only thing doubled is the network.

**It signs real JWTs.** The ID token is an RS256 JWT signed with a private key
generated for the process; the JWKS the engine fetches carries the public half
only. A test forges a token by signing with *another* key (``forge_with``) or by
putting a wrong claim in ``claims`` — the engine must refuse it for the reason a
real provider's consumer would. An earlier double handed back an unsigned
``h.payload.sssss`` and so could not tell a verifying engine from one that never
looked at the signature.

**It rejects what a real provider rejects:** a token request without the form
fields RFC 6749 4.1.3 requires is a 400, a userinfo request without the bearer
token it issued is a 401, and the JWKS holds no private material.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.jose import JsonWebKey, JsonWebToken

from app.domain.engines import oauth_engine

ACCESS_TOKEN = "idp-access-token"

#: What a token request must carry (RFC 6749 4.1.3 + PKCE).
_TOKEN_FIELDS = ("grant_type", "code", "redirect_uri", "client_id", "code_verifier")

_jwt = JsonWebToken(["RS256"])
_KEYS: dict[str, Any] = {}


def _key(kid: str):  # noqa: ANN202
    if kid not in _KEYS:
        _KEYS[kid] = JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": kid})
    return _KEYS[kid]


class FakeIdp:
    """One signing key, a mutable set of claims, and a record of what was asked of it."""

    def __init__(self) -> None:
        self.kid = "idp-key-1"
        #: The ID token payload the token endpoint signs. Set per test.
        self.claims: dict[str, Any] = {}
        #: The userinfo answer; ``None`` means the endpoint answers 404.
        self.userinfo: dict[str, Any] | None = None
        #: Sign with this key id instead of the published one — a forged token.
        self.forge_with: str | None = None
        #: Answer the token request without an ``id_token`` (plain OAuth2).
        self.omit_id_token = False
        #: Answer with exactly this string as the ID token (an ``alg: none`` token, say).
        self.id_token_override: str | None = None
        #: Publish this JWKS URI in the discovery document.
        self.discovery_extra: dict[str, Any] = {}
        self.token_requests: list[dict[str, str]] = []
        self.jwks_requests = 0
        self.discovery_requests: list[str] = []
        self.userinfo_requests = 0

    # ── keys and tokens ──────────────────────────────────────────────

    def jwks(self) -> dict[str, Any]:
        """The public key set — never the private half."""
        return {"keys": [_key(self.kid).as_dict(is_private=False)]}

    def sign(self, claims: dict[str, Any], *, kid: str | None = None) -> str:
        signing_kid = kid or self.forge_with or self.kid
        header = {"alg": "RS256", "typ": "JWT", "kid": self.kid}
        token = _jwt.encode(header, claims, _key(signing_kid))
        return token.decode() if isinstance(token, bytes) else token

    @property
    def redirect_uris(self) -> list[str]:
        return [request["redirect_uri"] for request in self.token_requests]

    # ── the network ──────────────────────────────────────────────────

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        origin = f"{request.url.scheme}://{request.url.host}"
        if path.endswith("/token") and request.method == "POST":
            form = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
            if any(not form.get(field) for field in _TOKEN_FIELDS):
                return httpx.Response(400, json={"error": "invalid_request"})
            self.token_requests.append(form)
            body: dict[str, Any] = {"access_token": ACCESS_TOKEN, "token_type": "Bearer"}
            if self.id_token_override is not None:
                body["id_token"] = self.id_token_override
            elif not self.omit_id_token:
                body["id_token"] = self.sign(self.claims)
            return httpx.Response(200, json=body)
        if path.endswith("/jwks"):
            self.jwks_requests += 1
            return httpx.Response(200, json=self.jwks())
        if path.endswith("/.well-known/openid-configuration"):
            self.discovery_requests.append(origin)
            document = {
                "issuer": origin,
                "authorization_endpoint": f"{origin}/authorize",
                "token_endpoint": f"{origin}/token",
                "jwks_uri": f"{origin}/jwks",
                **self.discovery_extra,
            }
            return httpx.Response(200, content=json.dumps(document), headers={"content-type": "application/json"})
        if path.endswith("/userinfo"):
            if request.headers.get("authorization") != f"Bearer {ACCESS_TOKEN}":
                return httpx.Response(401, json={"error": "invalid_token"})
            self.userinfo_requests += 1
            if self.userinfo is None:
                return httpx.Response(404)
            return httpx.Response(200, json=self.userinfo)
        return httpx.Response(404)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Route every ``httpx.Client`` the engine opens to this provider.

        The real class is captured first: patching ``httpx.Client`` with a factory
        that builds ``httpx.Client`` would recurse.
        """
        real = httpx.Client
        transport = httpx.MockTransport(self.handle)

        def client(*args: Any, **kwargs: Any) -> httpx.Client:
            kwargs["transport"] = transport
            return real(*args, **kwargs)

        monkeypatch.setattr(oauth_engine.httpx, "Client", client)
