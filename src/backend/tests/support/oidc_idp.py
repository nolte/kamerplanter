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

**The follow-ups of #1987 need the awkward provider too:** a key set that carries a
key of an unknown type (``bad_jwks_entries``), a rotated signing key
(``rotate``) and a token whose header names a key id the set does not hold
(``token_header_kid``), an answer that is far larger than any key set
(``jwks_padding``), one that fails (``jwks_status``), and a hook that runs while
the token request is in flight (``on_token_request``) so a test can change the
world between the callback's configuration load and its link write.

**#2007 adds the token and userinfo answers to that:** a token response or userinfo
answer far larger than any real one (``token_padding``, ``userinfo_padding``), and the
headers of both requests, so a test can see what reached an endpoint.

**DNS is doubled as well.** Login now checks every provider-supplied URL through
:mod:`app.common.url_safety`, which resolves the host; the fixture hosts of these
tests (``idp-a.example``) resolve to nothing. ``dns`` maps a host to the address it
resolves to (default: a public one), so a test can make a provider's key endpoint
resolve into a private range — or name the cloud metadata address directly.
"""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.jose import JsonWebKey, JsonWebToken

from app.common import url_safety
from app.domain.engines import jwks_cache, oauth_engine

ACCESS_TOKEN = "idp-access-token"

#: Where a host with no ``dns`` entry resolves: a documentation-adjacent public address.
PUBLIC_ADDRESS = "93.184.216.34"

#: What a token request must carry (RFC 6749 4.1.3 + PKCE).
_TOKEN_FIELDS = ("grant_type", "code", "redirect_uri", "client_id", "code_verifier")

_jwt = JsonWebToken(["RS256"])
_KEYS: dict[str, Any] = {}


def _key(kid: str):  # noqa: ANN202
    if kid not in _KEYS:
        _KEYS[kid] = JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": kid})
    return _KEYS[kid]


class _Dribble(httpx.SyncByteStream):
    """A body that arrives one byte per read."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __iter__(self):  # noqa: ANN204
        for index in range(len(self._body)):
            yield self._body[index : index + 1]


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
        #: Key ids the JWKS publishes. Defaults to the signing key; ``rotate`` replaces it.
        self.published_kids: list[str] = [self.kid]
        #: Raw JWK objects appended to the key set (a key of an unknown ``kty``, say).
        self.bad_jwks_entries: list[dict[str, Any]] = []
        #: Put this ``kid`` in the token header instead of the signing key's.
        self.token_header_kid: str | None = None
        #: Whitespace appended to the JWKS body, to make it larger than any real key set.
        self.jwks_padding = 0
        #: Answer the JWKS request with exactly this body instead of the key set.
        self.jwks_raw: str | None = None
        #: Send the JWKS body one byte at a time (a response that dribbles in).
        self.jwks_dribble = False
        #: Headers of every JWKS request.
        self.jwks_request_headers: list[httpx.Headers] = []
        #: Answer the JWKS request with this status instead of the key set.
        self.jwks_status = 200
        #: Runs while a token request is being answered.
        self.on_token_request: Callable[[], None] | None = None
        #: Whitespace appended to the discovery document, likewise.
        self.discovery_padding = 0
        #: Whitespace appended to the token response and the userinfo answer (#2007).
        self.token_padding = 0
        self.userinfo_padding = 0
        #: Headers of every token and userinfo request (#2007).
        self.token_request_headers: list[httpx.Headers] = []
        self.userinfo_request_headers: list[httpx.Headers] = []
        #: The clock the key cache runs on (seconds); ``advance`` moves it.
        self.now = 1_000.0
        #: Host -> address it resolves to; a host not listed resolves to ``PUBLIC_ADDRESS``.
        self.dns: dict[str, str] = {}
        self.token_requests: list[dict[str, str]] = []
        self.jwks_requests = 0
        self.jwks_urls: list[str] = []
        self.discovery_requests: list[str] = []
        self.userinfo_requests = 0

    # ── keys and tokens ──────────────────────────────────────────────

    def jwks(self) -> dict[str, Any]:
        """The public key set — never the private half."""
        keys = [_key(kid).as_dict(is_private=False) for kid in self.published_kids]
        return {"keys": [*self.bad_jwks_entries, *keys]}

    def rotate(self, new_kid: str, *, keep_old: bool = False) -> None:
        """The provider starts signing with *new_kid* and publishes it (and, optionally, still the old key)."""
        old = self.kid
        self.kid = new_kid
        self.published_kids = [old, new_kid] if keep_old else [new_kid]

    def sign(self, claims: dict[str, Any], *, kid: str | None = None) -> str:
        signing_kid = kid or self.forge_with or self.kid
        header = {"alg": "RS256", "typ": "JWT", "kid": self.token_header_kid or self.kid}
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
            self.token_request_headers.append(request.headers)
            if self.on_token_request is not None:
                self.on_token_request()
            body: dict[str, Any] = {"access_token": ACCESS_TOKEN, "token_type": "Bearer"}
            if self.id_token_override is not None:
                body["id_token"] = self.id_token_override
            elif not self.omit_id_token:
                body["id_token"] = self.sign(self.claims)
            return httpx.Response(
                200, content=json.dumps(body) + " " * self.token_padding, headers={"content-type": "application/json"}
            )
        if path.endswith("/jwks"):
            self.jwks_requests += 1
            self.jwks_urls.append(str(request.url))
            if self.jwks_status != 200:
                return httpx.Response(self.jwks_status)
            self.jwks_request_headers.append(request.headers)
            body = self.jwks_raw if self.jwks_raw is not None else json.dumps(self.jwks()) + " " * self.jwks_padding
            if self.jwks_dribble:
                return httpx.Response(
                    200, content=_Dribble(body.encode()), headers={"content-type": "application/json"}
                )
            return httpx.Response(200, content=body, headers={"content-type": "application/json"})
        if path.endswith("/.well-known/openid-configuration"):
            self.discovery_requests.append(origin)
            document = {
                "issuer": origin,
                "authorization_endpoint": f"{origin}/authorize",
                "token_endpoint": f"{origin}/token",
                "jwks_uri": f"{origin}/jwks",
                **self.discovery_extra,
            }
            return httpx.Response(
                200,
                content=json.dumps(document) + " " * self.discovery_padding,
                headers={"content-type": "application/json"},
            )
        if path.endswith("/userinfo"):
            if request.headers.get("authorization") != f"Bearer {ACCESS_TOKEN}":
                return httpx.Response(401, json={"error": "invalid_token"})
            self.userinfo_requests += 1
            self.userinfo_request_headers.append(request.headers)
            if self.userinfo is None:
                return httpx.Response(404)
            return httpx.Response(
                200,
                content=json.dumps(self.userinfo) + " " * self.userinfo_padding,
                headers={"content-type": "application/json"},
            )
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
        monkeypatch.setattr(url_safety, "_resolved_addresses", self._resolve)
        # The key cache is process-wide: a test starts with none and runs it on this clock.
        jwks_cache.reset_jwks_cache()
        monkeypatch.setattr(jwks_cache, "_clock", lambda: self.now, raising=False)

    def advance(self, seconds: float) -> None:
        """Move the key cache's clock forward."""
        self.now += seconds

    def _resolve(self, host: str) -> list[ipaddress._BaseAddress]:
        """The address a host resolves to — a literal is its own address, as with the real resolver."""
        try:
            return [ipaddress.ip_address(host)]
        except ValueError:
            return [ipaddress.ip_address(self.dns.get(host, PUBLIC_ADDRESS))]
