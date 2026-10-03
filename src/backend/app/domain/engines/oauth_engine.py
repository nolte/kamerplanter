"""OAuth/OIDC engine — full implementation with Authlib PKCE.

Handles authorization URL generation, token exchange, provider-specific
user info extraction (Google, GitHub, Apple, generic OIDC).
"""

import base64
import hashlib
import hmac
import json
import math
import secrets
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
import structlog
from authlib.jose import JsonWebKey, JsonWebToken, KeySet
from authlib.jose.errors import JoseError

from app.common.enums import AuthProviderType, OidcProviderType
from app.common.exceptions import ValidationError
from app.common.url_safety import https_endpoint_problem, validate_oidc_fetch_url
from app.domain.engines import jwks_cache
from app.domain.engines.jwks_cache import JwksFetchError
from app.domain.models.auth import OAuthRedirect, OAuthUserInfo
from app.domain.models.oidc_config import (
    GITHUB_EMAIL_SCOPES,
    GITHUB_REQUIRED_SCOPE,
    OidcProviderConfig,
    ProviderIssuerCheck,
    ProviderJwksCheck,
    ProviderScopeCheck,
    ProviderTypeCheck,
    is_github_provider,
    is_known_provider_type,
    scope_tokens,
    scopes_grant_github_email,
)

logger = structlog.get_logger()


def _as_optional_bool(claim: object) -> bool | None:
    """Normalise a provider's ``email_verified`` claim to three states (#1403).

    ``None`` means the provider said nothing, which is NOT the same as ``False``
    and is why this returns an optional rather than defaulting. OIDC Core 5.1
    specifies a boolean, but the claim is optional and real deployments send the
    strings ``"true"`` / ``"false"`` often enough that reading only ``bool``
    would turn a provider that *does* assert verification into one that appears
    silent — and under the rule in :meth:`OAuthEngine.should_auto_link` silence
    refuses the link, so that error is user-visible rather than merely untidy.

    Anything else — a number, a list, a typo — is ``None``. Guessing at a
    malformed claim is exactly the kind of leniency this issue exists to remove.
    """
    if isinstance(claim, bool):
        return claim
    if isinstance(claim, str):
        lowered = claim.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    return None


# Well-known endpoints for built-in providers.
#
# Keyed from ``OidcProviderType`` so the vocabulary the API boundary enforces and
# the table this dispatch reads cannot drift (#1497): a key the boundary refuses
# would be unreachable, and a member missing here silently falls through to
# discovery. ``tests/unit/domain/engines/test_provider_type_vocabulary.py`` holds
# both directions. ``OidcProviderType.OIDC`` is absent on purpose — the generic
# branch resolves its endpoints from the discovery document.
_PROVIDER_ENDPOINTS: dict[str, dict[str, str]] = {
    OidcProviderType.GOOGLE.value: {
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    },
    OidcProviderType.GITHUB.value: {
        "authorization_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
    },
    OidcProviderType.APPLE.value: {
        "authorization_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "userinfo_url": "",  # Apple doesn't have a userinfo endpoint; data is in id_token
    },
}


#: Provider types that answer a fresh re-authentication (#1815): an OpenID Connect
#: sign-in forced with ``prompt=login`` and ``max_age=0``, whose ID token carries
#: ``auth_time``. GitHub is absent because it is plain OAuth2 — no ID token, so
#: nothing proves *when* the person signed in. Apple is absent because its ID token
#: carries no ``auth_time``. Keyed from ``OidcProviderType`` like the tables above.
_FRESH_REAUTH_PROVIDER_TYPES: frozenset[str] = frozenset({OidcProviderType.GOOGLE.value, OidcProviderType.OIDC.value})

#: Issuers a provider type is known to put in ``iss`` when no discovery document
#: names one. Google documents both spellings.
_KNOWN_ISSUERS: dict[str, frozenset[str]] = {
    OidcProviderType.GOOGLE.value: frozenset({"https://accounts.google.com", "accounts.google.com"}),
    OidcProviderType.APPLE.value: frozenset({"https://appleid.apple.com"}),
}

#: How old the provider sign-in may be when its ID token arrives (#1815). The
#: request asked for ``max_age=0``; five minutes covers a slow typist and a second
#: factor at the provider, and no more.
FRESH_REAUTH_MAX_AGE_SECONDS = 300

#: Clock skew tolerated between this server and the provider for ``auth_time`` and
#: ``exp``. Thirty seconds is what NTP-synced hosts stay well inside; more would
#: stretch the five-minute window by an amount nobody reviews.
FRESH_REAUTH_CLOCK_SKEW_SECONDS = 30

#: Where a provider type publishes its signing keys when no discovery document names
#: them. Google and Apple document these; GitHub issues no ID token at all.
_KNOWN_JWKS_URLS: dict[str, str] = {
    OidcProviderType.GOOGLE.value: "https://www.googleapis.com/oauth2/v3/certs",
    OidcProviderType.APPLE.value: "https://appleid.apple.com/auth/keys",
}

#: What a signed ID token may use (#1936): the asymmetric algorithms of RFC 7518 and
#: EdDSA. Never ``none`` and never ``HS*`` — a symmetric algorithm would let whoever
#: knows the client secret mint a token for it.
_LOGIN_ID_TOKEN_ALGORITHMS = ["RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "EdDSA"]

#: The fields OIDC Discovery 3 marks REQUIRED that this application reads. ``issuer``
#: is checked separately, against the issuer the document was fetched from (4.3).
_DISCOVERY_REQUIRED_ENDPOINTS = ("authorization_endpoint", "token_endpoint", "jwks_uri")

#: Clock skew tolerated for ``iat``, ``nbf`` and ``exp`` of a login ID token.
_LOGIN_CLOCK_SKEW_SECONDS = FRESH_REAUTH_CLOCK_SKEW_SECONDS

#: How old a login ID token's ``iat`` may be (#1987). The provider issues the token in the
#: response to the code exchange this server just made, seconds after the person finished
#: signing in, and the state that carries the nonce lives five minutes; a token issued an hour
#: ago is a replayed or long-held one, whatever its ``exp`` says. Ten minutes leaves room for
#: a slow second factor and a skewed provider clock, and no more.
_LOGIN_ID_TOKEN_MAX_AGE_SECONDS = 600


def supports_fresh_reauth(config: OidcProviderConfig) -> bool:
    """Whether *config* can re-authenticate a person freshly (#1815).

    True for an enabled Google or generic OIDC provider that requests the
    ``openid`` scope — without it there is no ID token and so no ``auth_time``.
    Exact spelling like :func:`is_github_provider`: the dispatch is exact too.
    """
    return (
        config.enabled
        and config.provider_type in _FRESH_REAUTH_PROVIDER_TYPES
        and "openid" in scope_tokens(config.scopes)
        and _token_endpoint_is_tls(config)
    )


def _token_endpoint_is_tls(config: OidcProviderConfig) -> bool:
    """Whether the token endpoint is HTTPS (review SEC-003).

    The ID token is trusted without a signature check *because* it comes straight
    from the token endpoint over TLS (OIDC Core 3.1.3.7 step 6). Over plain HTTP
    that reason is gone, so such a provider cannot confirm a step-up.
    """
    try:
        token_url = OAuthEngine()._resolve_token_url(config)
    except ValueError:
        return False
    return token_url.lower().startswith("https://")


def _subject_text(value: object) -> str:
    """A provider's account identifier as text; ``""`` when it names none (#1936).

    ``str(None)`` is ``"None"`` — a subject, to every check downstream — so an
    absent or null identifier is mapped to the empty string, which
    :meth:`OAuthEngine.authenticate_login` refuses. A JSON string or integer is an
    identifier; a bool, list or object is not.
    """
    if isinstance(value, bool) or not isinstance(value, str | int):
        return ""
    return str(value)


def _is_finite_number(value: object) -> bool:
    """A JSON number that can be compared with a clock: not a bool, not NaN, not ±Infinity (review SEC-004)."""
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _refuse_non_finite(constant: str) -> float:
    raise ValueError(f"Non-finite number {constant} in id_token.")


class DiscoveryIssuerMismatchError(ValueError):
    """The discovery document names another issuer than the one it was fetched from (OIDC Discovery 4.3).

    A ``ValueError`` like every other reason a document is refused, but one that keeps what
    the provider announced, so ``POST /admin/oidc-providers/{key}/test`` can tell the operator
    which issuer to configure (#1987).
    """

    def __init__(self, announced: str) -> None:
        super().__init__("The discovery document's issuer is not the issuer it was fetched from.")
        self.announced = announced


class FreshReauthRejectedError(Exception):
    """The ID token of a step-up callback does not prove a fresh sign-in of the account (#1815).

    ``reason`` is ``"stale"`` when the only problem is the age of the sign-in
    (the person may simply retry) and ``"failed"`` otherwise. The detail is for the
    log line; it never reaches the browser.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class LoginIdentityRejectedError(Exception):
    """A login's ID token or subject failed a check (#1936).

    ``reason`` is one word from a fixed vocabulary (``signature``, ``iss``, ``aud``,
    ``azp``, ``nonce``, ``exp``, ``iat``, ``sub_missing``, ``sub_mismatch``,
    ``id_token_missing``, ``jwks_unavailable``, ``malformed``) — it names the check,
    never the value that failed it, so it is safe in a log line and carries no
    secret. The caller answers every refusal with the same generic error.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class InsecureEndpointError(ValueError):
    """A provider endpoint is unusable (not ``https``, no host, ...); the text names a rule, never a value (#1987)."""


def _https_endpoint(url: str, what: str) -> str:
    """*url* if it is an acceptable endpoint, else ``ValueError`` — the login never dials a plain-http one (#1987).

    The request schemas refuse such a URL since #1987, but a configuration stored before
    that is still read, and so is a stored discovery document: this is the check at the
    point of use. ``ValueError`` is what the resolvers already raise for "cannot
    resolve", so :func:`_token_endpoint_is_tls` and the callers treat it the same way.
    """
    problem = https_endpoint_problem(url)
    if problem is not None:
        raise InsecureEndpointError(f"The {what} {problem}.")
    return url


def _get_json_bounded(client: httpx.Client, url: str) -> Any:
    """GET *url* and parse it as JSON, reading no more than ``JWKS_MAX_BYTES`` of the body (#1987).

    Streamed and counted on the DECODED bytes, so neither a huge ``Content-Length`` nor a
    compressed body that inflates past the cap is read to the end. No redirect is followed
    (httpx's default): a provider answering with a redirect to an internal address is an
    error, not a detour.

    Raises:
        httpx.HTTPError: the request failed or the status is not 2xx.
        ValueError: the body is larger than the cap, or is not JSON.
    """
    limit = jwks_cache.JWKS_MAX_BYTES
    deadline = time.monotonic() + jwks_cache.JWKS_FETCH_DEADLINE_SECONDS
    # ``identity``: the cap counts decoded bytes, and a decoder inflates a whole raw chunk at once —
    # a small compressed chunk can be many megabytes. A key set is a few kilobytes; nothing is lost.
    headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
    with client.stream("GET", url, headers=headers) as response:
        response.raise_for_status()
        declared = response.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > limit:
            raise ValueError("The response is larger than the limit.")
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body) > limit:
                raise ValueError("The response is larger than the limit.")
            # httpx's timeout is per phase: a provider that sends a byte every few seconds would
            # otherwise hold the request (and the per-configuration fetch lock) for as long as it
            # cares to — and every sign-in at that configuration with it.
            if time.monotonic() > deadline:
                raise ValueError("The response took longer than the limit.")
    return json.loads(bytes(body), parse_constant=_refuse_non_finite)


def _unverified_kid(token: str) -> str | None:
    """The ``kid`` a compact JWT's header claims — used only to decide whether the cached keys can verify it.

    Nothing is trusted from the header: the signature is checked against the key set afterwards,
    and a header that cannot be read yields ``None`` (the decode then fails on its own).
    """
    try:
        header_b64 = token.split(".", 1)[0]
        header = json.loads(base64.urlsafe_b64decode(header_b64 + "=" * (-len(header_b64) % 4)))
    except ValueError, TypeError:
        return None
    kid = header.get("kid") if isinstance(header, dict) else None
    return kid if isinstance(kid, str) else None


def _import_key_set(document: Any) -> tuple[KeySet, int]:
    """The usable keys of a JWKS document, and how many entries were skipped (#1987).

    One key the library cannot import — an unknown ``kty``, a malformed modulus, an entry that
    is not an object — used to discard the whole set, so a provider that added a key type this
    library does not know locked everybody out. It is skipped. A symmetric (``oct``) key is
    skipped as well: login accepts asymmetric algorithms only (``_LOGIN_ID_TOKEN_ALGORITHMS``),
    so one in the set can only be a mistake or an attack.

    Raises:
        ValueError: the document is no key set, or no key in it is usable.
    """
    entries = document.get("keys") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise ValueError("The JWKS document has no key list.")
    keys = []
    skipped = 0
    for entry in entries:
        try:
            key = JsonWebKey.import_key(entry)
            usable = isinstance(entry, dict) and entry.get("kty") in _ASYMMETRIC_KEY_TYPES
        except JoseError, ValueError, KeyError, TypeError, AttributeError:
            usable = False
        if usable:
            keys.append(key)
        else:
            skipped += 1
    if not keys:
        raise ValueError("The JWKS document holds no usable key.")
    return KeySet(keys), skipped


#: The JWK key types an ID token signature can be verified with here (RFC 7518 6, RFC 8037).
_ASYMMETRIC_KEY_TYPES = frozenset({"RSA", "EC", "OKP"})


def _canonical_issuer(value: str) -> str:
    """The comparison form of an issuer for a discovery document: no surrounding space, no trailing ``/``."""
    return value.strip().rstrip("/")


#: Which stored ``provider_type`` becomes which ``AuthProviderType`` on the link
#: record. Keyed from ``OidcProviderType`` for the same reason as
#: ``_PROVIDER_ENDPOINTS`` (#1497); anything not listed falls back to the generic
#: ``AuthProviderType.OIDC``, which is what ``OidcProviderType.OIDC`` means.
_AUTH_PROVIDER_BY_TYPE: dict[str, AuthProviderType] = {
    OidcProviderType.GOOGLE.value: AuthProviderType.GOOGLE,
    OidcProviderType.GITHUB.value: AuthProviderType.GITHUB,
    OidcProviderType.APPLE.value: AuthProviderType.APPLE,
}


class OAuthEngine:
    """Pure logic for OAuth/OIDC flows."""

    @staticmethod
    def usable_discovery(config: OidcProviderConfig) -> dict | None:
        """The stored discovery document of *config*, only while it is the configured issuer's (#1969).

        OIDC Discovery 4.3: a document belongs to the issuer it was fetched from,
        and its ``issuer`` equals that issuer. A stored document that names another
        issuer — left by a repoint of ``issuer_url`` before the repoint cleared it —
        or none is **ignored**, not read: sign-in prefers a discovery endpoint to the
        configured one, so honouring it would send the authorization request, the
        code and the client secret to the issuer the provider was moved away from.
        """
        document = config.discovery_document
        if not isinstance(document, dict):
            return None
        issuer = document.get("issuer")
        if not isinstance(issuer, str) or _canonical_issuer(issuer) != _canonical_issuer(config.issuer_url):
            return None
        return document

    def build_authorization_url(
        self,
        config: OidcProviderConfig,
        redirect_uri: str,
        *,
        fresh_login: bool = False,
    ) -> OAuthRedirect:
        """Build authorization URL with PKCE (S256) and state/nonce.

        ``fresh_login`` (#1815) adds ``prompt=login`` and ``max_age=0``: the
        provider must authenticate the person again instead of answering from its
        own session, and report when it did (``auth_time``).
        """
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(16)
        code_verifier = secrets.token_urlsafe(64)

        # S256 code challenge
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        import base64

        code_challenge_b64 = base64.urlsafe_b64encode(code_challenge).rstrip(b"=").decode()

        auth_url = self._resolve_authorization_url(config)
        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge_b64,
            "code_challenge_method": "S256",
        }
        if fresh_login:
            params["prompt"] = "login"
            params["max_age"] = "0"
        # Apple requires response_mode=form_post
        if config.provider_type == OidcProviderType.APPLE:
            params["response_mode"] = "form_post"

        # Encoded (review SEC-006): a redirect URI or scope carrying ``&``/``#``/space
        # must reach the provider as one value, not split into parameters.
        full_url = f"{auth_url}?{urlencode(params)}"

        return OAuthRedirect(
            authorization_url=full_url,
            state=state,
            nonce=nonce,
            code_verifier=code_verifier,
        )

    def exchange_code_for_tokens(
        self,
        config: OidcProviderConfig,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        client_secret: str,
    ) -> dict:
        """Exchange authorization code for tokens (synchronous with httpx)."""
        token_url = self._resolve_token_url(config)

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config.client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        }

        headers = {"Accept": "application/json"}

        with httpx.Client(timeout=30) as client:
            resp = client.post(token_url, data=data, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def check_provider_type(self, config: OidcProviderConfig) -> ProviderTypeCheck:
        """Judge a stored ``provider_type`` against the vocabulary this engine dispatches on (#1497).

        ``extract_user_info`` takes the GitHub branch on ``github`` and the Apple
        branch on ``apple``, and ``_PROVIDER_ENDPOINTS`` is keyed the same way, so
        a record typed ``GitHub`` is served by the GENERIC OIDC branch: no
        well-known endpoints, no address-list request, and — before this — no
        complaint anywhere.

        Since #1497 the API boundary refuses such a spelling on create and update,
        so this can only answer ``ok=False`` for a record written earlier. It
        returns a verdict and raises nothing, exactly like
        :meth:`check_provider_scopes`: refusing the read would take away the only
        screen on which that record is visible, and there is no migration —
        rewriting stored operator data on the strength of a measurement that found
        no records at all would be guessing.
        """
        known = [member.value for member in OidcProviderType]
        if is_known_provider_type(config.provider_type):
            return ProviderTypeCheck(
                ok=True,
                provider_type=config.provider_type,
                known_provider_types=known,
                detail="This provider type is one the sign-in flow dispatches on.",
            )
        return ProviderTypeCheck(
            ok=False,
            provider_type=config.provider_type,
            known_provider_types=known,
            detail=(
                f"'{config.provider_type}' is not a provider type this installation dispatches on, so "
                "sign-in through it uses the generic OIDC branch: no well-known endpoints are filled "
                f"in and no provider-specific step runs. The accepted values are {', '.join(known)}, "
                "spelled lower-case. Correct the provider type with PUT on this configuration."
            ),
        )

    def check_provider_scopes(self, config: OidcProviderConfig) -> ProviderScopeCheck:
        """Judge a configured scope list against what the provider branch needs (#1477).

        Only GitHub has a requirement today: ``_fetch_github_user_info`` reads
        ``GET /user/emails`` for the ``verified`` flag, and GitHub answers that
        endpoint with 403 unless the token carries ``user:email`` (or its parent
        scope ``user``). Without it every sign-in produces no claim, #1403 refuses
        the auto-link, and the only trace is one log line per sign-in — far from
        the administration screen where the scope list was typed.

        This returns a verdict and raises nothing, so ``/{key}/test`` can report
        on a configuration that already exists.
        """
        tokens = scope_tokens(config.scopes)

        if not is_github_provider(config.provider_type):
            return ProviderScopeCheck(
                ok=True,
                provider_type=config.provider_type,
                configured_scopes=tokens,
                detail="This provider type has no scope requirement beyond the OIDC defaults.",
            )

        if scopes_grant_github_email(config.scopes):
            return ProviderScopeCheck(
                ok=True,
                provider_type=config.provider_type,
                configured_scopes=tokens,
                detail=(
                    "The scopes grant read access to the GitHub address list, so sign-in can "
                    "read the `verified` flag and auto-linking stays available."
                ),
            )

        detail = (
            "GitHub exposes the per-address `verified` flag only on `GET /user/emails`, which "
            f"needs the `{GITHUB_REQUIRED_SCOPE}` scope (the parent scope `user` also grants it). "
            "Without it every sign-in through this provider reports no verification, so accounts "
            "are never auto-linked."
        )
        if any(token.lower() in GITHUB_EMAIL_SCOPES for token in tokens):
            detail += (
                " A scope differing only in case is configured: GitHub scope names are "
                "lower-case and no other casing is recognised."
            )
        return ProviderScopeCheck(
            ok=False,
            provider_type=config.provider_type,
            configured_scopes=tokens,
            missing_scopes=[GITHUB_REQUIRED_SCOPE],
            detail=detail,
        )

    def require_supported_scopes(self, config: OidcProviderConfig) -> None:
        """Refuse a provider configuration whose scopes cannot serve its own branch.

        The write routes of ``/admin/oidc-providers`` call this; the check itself
        lives here, beside the request it protects, so a second write route
        cannot spell the requirement differently.
        """
        check = self.check_provider_scopes(config)
        if check.ok:
            return
        raise ValidationError(
            f"Provider '{config.slug}' is missing the scope {', '.join(check.missing_scopes)}. {check.detail}",
            details=[{"field": "scopes", "message": check.detail}],
        )

    def extract_user_info(
        self,
        config: OidcProviderConfig,
        token_response: dict,
        access_token: str,
    ) -> OAuthUserInfo:
        """Extract user info, dispatching to provider-specific logic."""
        provider_type = config.provider_type

        if is_github_provider(provider_type):
            return self._fetch_github_user_info(access_token)
        elif provider_type == OidcProviderType.APPLE:
            return self._extract_apple_user_info(token_response)
        else:
            # Google and generic OIDC — use userinfo endpoint
            userinfo_url = self._resolve_userinfo_url(config)
            if userinfo_url:
                return self._fetch_userinfo_endpoint(
                    userinfo_url,
                    access_token,
                    config.provider_type,
                )
            # Fallback: parse id_token claims
            return self._extract_from_id_token(token_response, config.provider_type)

    def _fetch_github_user_info(self, access_token: str) -> OAuthUserInfo:
        """GitHub requires separate API calls for profile and email."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        with httpx.Client(timeout=15) as client:
            # Get profile
            resp = client.get("https://api.github.com/user", headers=headers)
            resp.raise_for_status()
            profile = resp.json()

            # Get primary email (may be private)
            email = profile.get("email")

            # `/user` carries NO verification flag — GitHub keeps it on
            # `/user/emails`, one entry per address with its own `verified`
            # boolean (#1403). The list is fetched unconditionally, not only when
            # the profile email is private: without it the claim is `None` for
            # every GitHub caller whose address is public, and under the
            # "absent means unverified" rule that switches auto-linking off for
            # most of them.
            #
            # **This request needs the `user:email` scope, and the default
            # provider configuration does not grant it.**
            # `OidcProviderConfig.scopes` defaults to
            # `["openid", "email", "profile"]`, which GitHub ignores, so a
            # provider registered without an explicit `user:email` answers 403
            # here on every sign-in. The consequence is bounded and one-directional
            # — no claim, therefore no auto-link — but it is installation-wide and
            # invisible outside this log line, which is why the line names the
            # scope rather than only the error.
            verified: bool | None = None
            try:
                email_resp = client.get("https://api.github.com/user/emails", headers=headers)
                email_resp.raise_for_status()
                entries = email_resp.json()

                # SHAPE-CHECKED, not assumed. `raise_for_status` guards the status
                # code only: a 200 carrying an error envelope (`{"message": ...}`,
                # a GHE proxy page, a JSON `null`) would reach the loops below,
                # and iterating a dict yields `str` keys whose `.get` raises
                # `AttributeError` — a class the first version of this `except`
                # did not name. That exception escapes `extract_user_info`, which
                # `complete_oauth` calls BEFORE the existing-link lookup, so it
                # would have broken sign-in for every GitHub user including those
                # already linked. The commit that introduced this block claimed
                # the opposite in its own message.
                if not isinstance(entries, list):
                    raise TypeError(f"/user/emails returned {type(entries).__name__}, expected a list")
                addresses = [entry for entry in entries if isinstance(entry, dict)]

                if not email:
                    primary = next((entry for entry in addresses if entry.get("primary")), None)
                    chosen = primary if primary is not None else (addresses[0] if addresses else None)
                    if chosen is not None:
                        email = chosen.get("email")
                        verified = _as_optional_bool(chosen.get("verified"))
                else:
                    match = next((entry for entry in addresses if entry.get("email") == email), None)
                    if match is not None:
                        verified = _as_optional_bool(match.get("verified"))
            except (httpx.HTTPError, TypeError, AttributeError, KeyError, IndexError, ValueError) as exc:
                logger.warning(
                    "github_email_verification_unavailable",
                    error=str(exc),
                    hint="the provider configuration needs the `user:email` scope for GitHub",
                )

        # A verification gap degrades to "not verified"; NO ADDRESS AT ALL is a
        # different failure and must not wear the same clothes. `OAuthUserInfo.email`
        # is a required `str`, so letting `None` through here raises a pydantic
        # ValidationError from the model constructor — a 500 far from its cause,
        # under a log line that calls it a verification problem.
        if not email:
            raise ValueError("GitHub returned no usable email address for this account.")

        return OAuthUserInfo(
            provider=AuthProviderType.GITHUB,
            provider_user_id=_subject_text(profile.get("id")),
            email=email,
            display_name=profile.get("name") or profile.get("login", ""),
            avatar_url=profile.get("avatar_url"),
            email_verified=verified,
        )

    def _extract_apple_user_info(self, token_response: dict) -> OAuthUserInfo:
        """Apple embeds user info in the id_token JWT."""
        return self._extract_from_id_token(token_response, OidcProviderType.APPLE.value)

    def _fetch_userinfo_endpoint(
        self,
        userinfo_url: str,
        access_token: str,
        provider_type: str,
    ) -> OAuthUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client(timeout=15) as client:
            resp = client.get(userinfo_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return OAuthUserInfo(
            provider=self._to_provider_type(provider_type),
            provider_user_id=_subject_text(data.get("sub")),
            email=data.get("email", ""),
            display_name=data.get("name", data.get("preferred_username", "")),
            avatar_url=data.get("picture"),
            # OIDC Core 5.1: a standard boolean claim, and genuinely optional —
            # `None` when the provider omits it, which is a different answer from
            # `False` and is treated as one (#1403).
            email_verified=_as_optional_bool(data.get("email_verified")),
        )

    def _extract_from_id_token(self, token_response: dict, provider_type: str) -> OAuthUserInfo:
        """Decode id_token JWT claims without verification (tokens just received from IdP)."""
        id_token = token_response.get("id_token", "")
        if not id_token:
            raise ValueError("No id_token in token response.")

        claims = self.id_token_claims(token_response)

        return OAuthUserInfo(
            provider=self._to_provider_type(provider_type),
            provider_user_id=_subject_text(claims.get("sub")),
            email=claims.get("email", ""),
            display_name=claims.get("name", claims.get("email", "")),
            avatar_url=claims.get("picture"),
            email_verified=_as_optional_bool(claims.get("email_verified")),
        )

    @staticmethod
    def id_token_claims(token_response: dict) -> dict:
        """The claims of the ID token in a token response, decoded without a signature check.

        Only for a token that came straight from the provider's token endpoint over
        TLS in a client-authenticated exchange — OIDC Core 3.1.3.7 step 6 lets the
        client use TLS server validation instead of the signature there.
        """
        id_token = token_response.get("id_token", "")
        if not id_token:
            raise ValueError("No id_token in token response.")
        parts = id_token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed id_token.")
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        # NaN / Infinity are not JSON; Python accepts them by default and they defeat
        # every time comparison (``now - NaN > max`` is False) — review SEC-004.
        claims = json.loads(base64.urlsafe_b64decode(payload_b64), parse_constant=_refuse_non_finite)
        if not isinstance(claims, dict):
            raise ValueError("Malformed id_token.")
        return claims

    @staticmethod
    def same_issuer(stored: str, presented: str | None) -> bool:
        """Whether *presented* (an ID token's ``iss``) names the issuer *stored* on a provider link.

        Compared without a trailing ``/`` and with a missing scheme read as
        ``https://`` — Google documents ``iss`` in both spellings,
        ``https://accounts.google.com`` and ``accounts.google.com`` (/code-review of
        #1937). Anything else must be equal.
        """
        if not presented:
            return False

        def canonical(value: str) -> str:
            value = value.strip().rstrip("/")
            return value if "://" in value else f"https://{value}"

        return canonical(stored) == canonical(presented)

    @staticmethod
    def expected_issuers(config: OidcProviderConfig) -> frozenset[str]:
        """The ``iss`` values this provider may send: a known spelling set, else the configured issuer.

        Never the stored discovery document's ``issuer`` (#1969): a document is
        accepted only while it equals ``issuer_url`` (:meth:`usable_discovery`), so
        reading it added nothing but a way for a stale one to keep the issuer a
        provider was moved away from in force.
        """
        known = _KNOWN_ISSUERS.get(config.provider_type)
        if known:
            return known
        return frozenset({config.issuer_url.rstrip("/")})

    def validate_fresh_reauth_claims(
        self,
        claims: dict,
        *,
        config: OidcProviderConfig,
        nonce: str,
        now: datetime,
    ) -> str:
        """Check an ID token proves a fresh sign-in at *config*; return its ``sub`` (#1815).

        OIDC Core 3.1.3.7: ``iss`` is the provider's issuer, ``aud`` contains our
        client id (and, with several audiences, ``azp`` is our client id), ``nonce``
        is the one this request sent, ``exp`` has not passed — plus the step-up
        rule: ``auth_time`` is present and at most
        :data:`FRESH_REAUTH_MAX_AGE_SECONDS` old (with
        :data:`FRESH_REAUTH_CLOCK_SKEW_SECONDS` tolerance). Whose ``sub`` it is is
        the caller's check: only the service knows the account's provider links.

        Raises:
            FreshReauthRejectedError: ``reason="stale"`` for an old sign-in, ``"failed"`` otherwise.
        """
        issuer = str(claims.get("iss", "")).rstrip("/")
        if issuer not in self.expected_issuers(config):
            raise FreshReauthRejectedError("failed", "iss is not the provider's issuer")
        audience = claims.get("aud")
        audiences = [audience] if isinstance(audience, str) else audience if isinstance(audience, list) else []
        if config.client_id not in audiences:
            raise FreshReauthRejectedError("failed", "aud does not contain the client id")
        if (len(audiences) > 1 or "azp" in claims) and claims.get("azp") != config.client_id:
            raise FreshReauthRejectedError("failed", "azp is not the client id")
        if not isinstance(claims.get("nonce"), str) or not hmac.compare_digest(claims["nonce"], nonce):
            raise FreshReauthRejectedError("failed", "nonce does not match")
        epoch = now.timestamp()
        exp = claims.get("exp")
        if not _is_finite_number(exp) or exp + FRESH_REAUTH_CLOCK_SKEW_SECONDS < epoch:
            raise FreshReauthRejectedError("failed", "exp has passed")
        auth_time = claims.get("auth_time")
        if not _is_finite_number(auth_time):
            raise FreshReauthRejectedError("failed", "auth_time is missing")
        if auth_time > epoch + FRESH_REAUTH_CLOCK_SKEW_SECONDS:
            raise FreshReauthRejectedError("failed", "auth_time lies in the future")
        if epoch - auth_time > FRESH_REAUTH_MAX_AGE_SECONDS + FRESH_REAUTH_CLOCK_SKEW_SECONDS:
            raise FreshReauthRejectedError("stale", "auth_time is too old")
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            raise FreshReauthRejectedError("failed", "sub is missing")
        return sub

    def fetch_discovery_document(self, issuer_url: str) -> dict:
        """Fetch OIDC discovery document from .well-known/openid-configuration.

        The one validator every caller shares (#1969): the rotation task, the admin
        test and the login's own key lookup. A document that is not a JSON object,
        whose ``issuer`` is not the issuer it was fetched from (OIDC Discovery 4.3),
        or that lacks the endpoints this application reads, raises ``ValueError``
        and is never returned — so none of them can store it.
        """
        _https_endpoint(issuer_url, "issuer")
        url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        with httpx.Client(timeout=15) as client:
            document = _get_json_bounded(client, url)
        return self.validate_discovery_document(document, issuer_url)

    @staticmethod
    def validate_discovery_document(document: Any, issuer_url: str) -> dict:
        """Check *document* is the discovery document of *issuer_url*; return it or raise ``ValueError``."""
        if not isinstance(document, dict):
            raise ValueError("The discovery document is not a JSON object.")
        issuer = document.get("issuer")
        if not isinstance(issuer, str) or not issuer:
            raise ValueError("The discovery document names no issuer.")
        if _canonical_issuer(issuer) != _canonical_issuer(issuer_url):
            raise DiscoveryIssuerMismatchError(issuer)
        missing = [
            field
            for field in _DISCOVERY_REQUIRED_ENDPOINTS
            if not isinstance(document.get(field), str) or not document[field]
        ]
        if missing:
            raise ValueError(f"The discovery document lacks {', '.join(missing)}.")
        # The endpoints carry the code, the client secret and the identity; over plain
        # HTTP a network attacker answers them (security review SEC-002).
        insecure = [
            field
            for field in (*_DISCOVERY_REQUIRED_ENDPOINTS, "userinfo_endpoint")
            if isinstance(document.get(field), str) and not document[field].lower().startswith("https://")
        ]
        if insecure:
            raise ValueError(f"The discovery document's {', '.join(insecure)} is not https.")
        return document

    # ── The login's identity checks (#1936) ──────────────────────────

    def authenticate_login(
        self,
        config: OidcProviderConfig,
        token_response: dict,
        access_token: str,
        *,
        nonce: str,
        now: datetime,
    ) -> OAuthUserInfo:
        """The identity of a login callback, with the ID token and the ``sub`` checked (OIDC Core 3.1.3.7, 5.3.2).

        Where the provider issues an ID token it is verified — signature against
        the provider's JWKS, ``iss``, ``aud`` / ``azp``, the ``nonce`` stored with
        the state, ``exp`` and ``iat`` — and its ``sub`` must be non-empty. The
        identity itself then comes from the provider's own branch
        (:meth:`extract_user_info`); where that is the userinfo endpoint its ``sub``
        must equal the ID token's. A login whose ``sub`` is empty or missing is
        refused whether or not there was an ID token: it is no identity, and two of
        them at one configuration would land on the same link.

        Raises:
            LoginIdentityRejectedError: any check failed. The reason names the check only.
        """
        claims: dict | None = None
        if token_response.get("id_token"):
            claims = self.verify_login_id_token(config, token_response["id_token"], nonce=nonce, now=now)
        elif self._expects_id_token(config):
            raise LoginIdentityRejectedError("id_token_missing")

        user = self.extract_user_info(config, token_response, access_token)

        subject = user.provider_user_id
        if not isinstance(subject, str) or not subject.strip():
            raise LoginIdentityRejectedError("sub_missing")
        if claims is not None and not hmac.compare_digest(str(claims["sub"]).encode(), subject.encode()):
            raise LoginIdentityRejectedError("sub_mismatch")
        return user

    @staticmethod
    def _expects_id_token(config: OidcProviderConfig) -> bool:
        """Whether a token response of *config* must carry an ID token.

        OIDC Core 3.1.3.3: an authorization request with the ``openid`` scope is
        answered with one. Apple always does; GitHub is plain OAuth2.
        """
        if is_github_provider(config.provider_type):
            return False
        return config.provider_type == OidcProviderType.APPLE.value or "openid" in scope_tokens(config.scopes)

    def verify_login_id_token(self, config: OidcProviderConfig, id_token: str, *, nonce: str, now: datetime) -> dict:
        """Verify *id_token* for a login at *config* and return its claims (OIDC Core 3.1.3.7).

        Raises:
            LoginIdentityRejectedError: the signature, ``iss``, ``aud``, ``azp``, ``nonce``,
                ``exp``, ``iat`` or ``sub`` check failed (the reason names which).
        """
        key_set = self._load_jwks(config, kid=_unverified_kid(id_token))
        try:
            claims = dict(JsonWebToken(_LOGIN_ID_TOKEN_ALGORITHMS).decode(id_token, key_set))
        except (JoseError, ValueError, KeyError, TypeError) as exc:
            raise LoginIdentityRejectedError("signature") from exc

        issuer = claims.get("iss")
        if not isinstance(issuer, str) or not any(
            self.same_issuer(expected, issuer) for expected in self.expected_issuers(config)
        ):
            raise LoginIdentityRejectedError("iss")
        audience = claims.get("aud")
        audiences = [audience] if isinstance(audience, str) else audience if isinstance(audience, list) else []
        if config.client_id not in audiences:
            raise LoginIdentityRejectedError("aud")
        if (len(audiences) > 1 or "azp" in claims) and claims.get("azp") != config.client_id:
            raise LoginIdentityRejectedError("azp")
        claimed_nonce = claims.get("nonce")
        if (
            not nonce
            or not isinstance(claimed_nonce, str)
            or not hmac.compare_digest(claimed_nonce.encode(), nonce.encode())
        ):
            raise LoginIdentityRejectedError("nonce")
        epoch = now.timestamp()
        exp = claims.get("exp")
        if not _is_finite_number(exp) or exp + _LOGIN_CLOCK_SKEW_SECONDS < epoch:
            raise LoginIdentityRejectedError("exp")
        iat = claims.get("iat")
        if (
            not _is_finite_number(iat)
            or iat > epoch + _LOGIN_CLOCK_SKEW_SECONDS
            or iat < epoch - _LOGIN_ID_TOKEN_MAX_AGE_SECONDS - _LOGIN_CLOCK_SKEW_SECONDS
        ):
            raise LoginIdentityRejectedError("iat")
        # ``nbf`` is optional (OIDC Core 2, RFC 7519 4.1.5), but a token that carries one is
        # not valid before it: present-and-wrong is a refusal, not an absence (#1987).
        if "nbf" in claims:
            nbf = claims["nbf"]
            if not _is_finite_number(nbf) or nbf - _LOGIN_CLOCK_SKEW_SECONDS > epoch:
                raise LoginIdentityRejectedError("nbf")
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise LoginIdentityRejectedError("sub_missing")
        return claims

    def _load_jwks(self, config: OidcProviderConfig, *, kid: str | None = None) -> Any:
        """The provider's signing keys, from the per-configuration cache or fetched over TLS (#1987).

        ``kid`` is the key id the token claims; the cache refetches once, rate-limited, when it
        holds no such key (:mod:`app.domain.engines.jwks_cache`). A failure refuses the login
        (fail closed) and is remembered for seconds only.
        """
        discovery = self.usable_discovery(config)
        stored_uri = discovery.get("jwks_uri") if discovery else None
        cache_key = (config.key, config.slug, config.provider_type, config.issuer_url, config.jwks_url, stored_uri)
        try:
            return jwks_cache.cached_key_set(cache_key, lambda: self._fetch_key_set(config), kid=kid)
        except JwksFetchError as exc:
            raise LoginIdentityRejectedError("jwks_unavailable") from exc

    def _fetch_key_set(self, config: OidcProviderConfig) -> tuple[KeySet, frozenset[str]]:
        """Resolve where *config*'s keys live, check that URL, and read the set — bounded.

        Raises:
            JwksFetchError: every way this can fail; the cause is logged value-free.
        """
        try:
            key_set, _skipped, _url = self._fetch_key_set_detailed(config)
        except Exception as exc:  # noqa: BLE001 — whatever it was, the failure must be cached and the login refused
            # Not an enumerated list: an exception that escaped it (``RecursionError`` from a document
            # of nested brackets, ``httpx.InvalidURL`` for a port out of range) would skip the negative
            # cache and the refetch interval, and every login would fetch again.
            logger.info("oidc_jwks_unavailable", provider=config.slug, error_type=type(exc).__name__)
            raise JwksFetchError(type(exc).__name__) from exc
        return key_set, frozenset(str(key.kid) for key in key_set.keys if key.kid)

    def _fetch_key_set_detailed(self, config: OidcProviderConfig) -> tuple[KeySet, int, str]:
        """:meth:`_fetch_key_set` without the translation: the set, the skipped count and the URL used."""
        url, origin = self._resolve_jwks_source(config)
        # An explicitly configured URL is the admin's, behind a step-up — as trusted as the issuer
        # they typed, so a private address is theirs to choose. One the provider's discovery
        # document supplies is the provider's: private only on the provider's own host.
        validate_oidc_fetch_url(
            url,
            field="jwks_uri",
            trusted_host=urlsplit(config.issuer_url).hostname if origin == "discovery" else None,
            allow_private=origin == "configured",
        )
        with httpx.Client(timeout=15) as client:
            document = _get_json_bounded(client, url)
        key_set, skipped = _import_key_set(document)
        return key_set, skipped, url

    def _resolve_jwks_source(self, config: OidcProviderConfig) -> tuple[str, str]:
        """Where *config*'s signing keys are published, and whose word that is.

        The configured ``jwks_url`` (``"configured"``), else the ``jwks_uri`` of its (current)
        discovery document (``"discovery"``), else the documented URL of a built-in provider
        type (``"known"``), else a discovery document fetched now — a provider stored without
        one still signs in, and the fetched document is validated like any other.

        Raises:
            ValueError: no source can be found.
        """
        if config.jwks_url:
            return config.jwks_url, "configured"
        discovery = self.usable_discovery(config)
        if discovery and isinstance(discovery.get("jwks_uri"), str):
            return discovery["jwks_uri"], "discovery"
        known = _KNOWN_JWKS_URLS.get(config.provider_type)
        if known:
            return known, "known"
        try:
            fetched = self.fetch_discovery_document(config.issuer_url)
        except (httpx.HTTPError, ValueError) as exc:  # `as exc` keeps ruff-format from rewriting the tuple
            logger.info("oidc_login_discovery_unavailable", provider=config.slug, error_type=type(exc).__name__)
            raise ValueError("No key endpoint can be resolved.") from exc
        return fetched["jwks_uri"], "discovery"

    # ── What ``POST /admin/oidc-providers/{key}/test`` reports about the login's own checks (#1987) ──

    def check_jwks(
        self, config: OidcProviderConfig, *, discovery: dict | None = None, discovery_error: str | None = None
    ) -> ProviderJwksCheck:
        """Whether the login could fetch and use *config*'s signing keys right now — a verdict, never an exception.

        Reads the provider fresh (the cache is neither consulted nor filled), through exactly the
        steps a login takes: where the keys live, that URL checked, the bounded read, the import.
        *discovery* is the document the caller has just fetched, so a provider whose stored
        document is stale is judged by the current one; *discovery_error* is why that fetch failed.
        """
        if not self._expects_id_token(config):
            return ProviderJwksCheck(
                ok=True, applicable=False, detail="This provider issues no ID token; there is no key set to verify."
            )
        probe = config.model_copy(update={"discovery_document": discovery}) if discovery else config
        if not probe.jwks_url and not self.usable_discovery(probe) and not _KNOWN_JWKS_URLS.get(probe.provider_type):
            reason = discovery_error or "The provider's discovery document names no key endpoint."
            return ProviderJwksCheck(ok=False, detail=f"No key endpoint could be resolved: {reason}")
        try:
            key_set, skipped, url = self._fetch_key_set_detailed(probe)
        except ValidationError as exc:
            return ProviderJwksCheck(ok=False, detail=f"The key endpoint is not acceptable: {exc.message}")
        except Exception as exc:  # noqa: BLE001 — a verdict, never an exception
            return ProviderJwksCheck(ok=False, detail=f"The key set could not be read ({type(exc).__name__}): {exc}")
        key_ids = sorted(str(key.kid) for key in key_set.keys if key.kid)
        return ProviderJwksCheck(
            ok=True,
            jwks_url=url,
            key_count=len(key_set.keys),
            skipped_key_count=skipped,
            key_ids=key_ids,
            detail=(
                f"{len(key_set.keys)} usable key(s) fetched"
                + (f"; {skipped} entr{'y' if skipped == 1 else 'ies'} skipped as unusable." if skipped else ".")
            ),
        )

    def check_issuer(
        self, config: OidcProviderConfig, *, announced: str | None = None, discovery_error: str | None = None
    ) -> ProviderIssuerCheck:
        """Whether the ``iss`` the provider announces is one the login accepts — a verdict, never an exception.

        *announced* is the ``issuer`` of the provider's discovery document — also when the
        document was refused for naming another issuer than the one it was fetched from, which
        is exactly the case an operator needs to see.
        """
        accepted = sorted(self.expected_issuers(config))
        if not self._expects_id_token(config):
            return ProviderIssuerCheck(
                ok=True,
                applicable=False,
                configured_issuer=config.issuer_url,
                accepted_issuers=accepted,
                detail="This provider issues no ID token; there is no issuer to check.",
            )
        if not isinstance(announced, str) or not announced:
            reason = discovery_error or "The discovery document names no issuer."
            return ProviderIssuerCheck(
                ok=False,
                configured_issuer=config.issuer_url,
                accepted_issuers=accepted,
                detail=f"The issuer the provider announces could not be read: {reason}",
            )
        if any(self.same_issuer(expected, announced) for expected in accepted):
            return ProviderIssuerCheck(
                ok=True,
                configured_issuer=config.issuer_url,
                accepted_issuers=accepted,
                discovery_issuer=announced,
                detail="The provider announces an issuer the login accepts.",
            )
        return ProviderIssuerCheck(
            ok=False,
            configured_issuer=config.issuer_url,
            accepted_issuers=accepted,
            discovery_issuer=announced,
            detail=(
                f"The provider announces the issuer {announced}, but the login accepts only {', '.join(accepted)}: "
                "every sign-in would be refused (reason iss). Set issuer_url to the announced value."
            ),
        )

    def should_auto_link(self, existing_email_verified: bool, oauth_email_verified: bool | None) -> bool:
        """Auto-link only if BOTH sides are verified, with absent counting as unverified.

        Auto-linking hands an OAuth assertion control of an existing local
        account purely because the two addresses match. The provider's
        ``email_verified`` claim is what bounds that: without it, any provider
        that will assert ``email = victim@example.org`` — one misconfigured in
        good faith, one that never verifies addresses, or one that is
        compromised — can log in as the victim, provided the victim's local
        account is email-verified, which every normally-registered account is.

        **Until #1403 the second argument was a literal ``True`` at the call
        site.** The parameter existed, its docstring said "both", and the value
        it guarded was hard-coded to the permissive answer, so the predicate
        reduced to a fact about the *victim's* account rather than about the
        assertion being trusted. NFR-018 §1 in its purest form: a check that
        cannot fail.

        **``None`` refuses**, and that is a decision rather than a default
        (operator, 2026-09-11). Many providers omit the claim; treating absence
        as ``True`` reproduces exactly the hole above, so absence is treated as
        "not asserted" and the caller is sent down the "log in with your
        password, then link" path that already exists. It is a behaviour change
        for any installation whose provider is silent, which is why it is
        written here and not only in the issue.

        **Links created before the fix are not touched by any of this**, and the
        decision on them is: measure first (operator, 2026-09-14).
        ``scripts/audit_oauth_links.py`` reports two things, read-only, because a forged
        link and a legitimate one are indistinguishable at the data layer and acting
        without the numbers would be guessing:

        1. the ``oidc_provider_configs`` REGISTRATIONS that predate #1399's gate, and
           which of them are still enabled — the worse case, because a provider
           nobody has signed in through yet produces no links at all and reads as an
           all-clear while it keeps minting them;
        2. the ``auth_providers`` links in two separate windows, the gate's and the
           auto-link branch's, which reached ``develop`` 29 hours apart.

        No number has been taken yet. A first run against the dev database reported
        no ``auth_providers`` collection, which was read as "nothing has ever been
        linked"; that reading was wrong. The collection is created unconditionally
        at bootstrap, so its absence means the database was never initialised — the
        wrong target, not an empty one. The script now says so and exits non-zero
        instead of reporting an all-clear. The number that matters is the production
        one and it is still outstanding.
        """
        return existing_email_verified and oauth_email_verified is True

    @staticmethod
    def validate_state(state: str, expected: str) -> bool:
        """Constant-time comparison to prevent timing attacks."""
        return hmac.compare_digest(state, expected)

    # ── Internal helpers ─────────────────────────────────────────────

    # The three resolvers hand back an endpoint the caller is about to dial with a code, a
    # client secret or an access token: each passes it through ``_https_endpoint`` (#1987),
    # whichever of the configuration, the built-in table or the stored discovery document
    # it came from.

    def _resolve_authorization_url(self, config: OidcProviderConfig) -> str:
        if config.authorization_url:
            return _https_endpoint(config.authorization_url, "authorization endpoint")
        known = _PROVIDER_ENDPOINTS.get(config.provider_type, {})
        if known.get("authorization_url"):
            return known["authorization_url"]
        # Try discovery
        discovery = self.usable_discovery(config)
        if discovery:
            return _https_endpoint(discovery.get("authorization_endpoint", ""), "authorization endpoint")
        raise ValueError(f"Cannot resolve authorization URL for provider '{config.slug}'.")

    def _resolve_token_url(self, config: OidcProviderConfig) -> str:
        if config.token_url:
            return _https_endpoint(config.token_url, "token endpoint")
        known = _PROVIDER_ENDPOINTS.get(config.provider_type, {})
        if known.get("token_url"):
            return known["token_url"]
        discovery = self.usable_discovery(config)
        if discovery:
            return _https_endpoint(discovery.get("token_endpoint", ""), "token endpoint")
        raise ValueError(f"Cannot resolve token URL for provider '{config.slug}'.")

    def _resolve_userinfo_url(self, config: OidcProviderConfig) -> str | None:
        if config.userinfo_url:
            return _https_endpoint(config.userinfo_url, "userinfo endpoint")
        known = _PROVIDER_ENDPOINTS.get(config.provider_type, {})
        if known.get("userinfo_url"):
            return known["userinfo_url"]
        discovery = self.usable_discovery(config)
        if discovery and discovery.get("userinfo_endpoint"):
            return _https_endpoint(discovery["userinfo_endpoint"], "userinfo endpoint")
        return None

    @staticmethod
    def link_type(config: OidcProviderConfig) -> AuthProviderType:
        """The ``AuthProviderType`` a provider link of *config* is stored under."""
        return OAuthEngine.link_type_for(config.provider_type)

    @staticmethod
    def link_type_for(provider_type: str) -> AuthProviderType:
        """The ``AuthProviderType`` a link of a configuration of *provider_type* is stored under."""
        return _AUTH_PROVIDER_BY_TYPE.get(provider_type, AuthProviderType.OIDC)

    @staticmethod
    def _to_provider_type(provider_type: str) -> AuthProviderType:
        return _AUTH_PROVIDER_BY_TYPE.get(provider_type, AuthProviderType.OIDC)
