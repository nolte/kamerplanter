from __future__ import annotations

import hashlib
import ipaddress
import secrets
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from app.common.enums import AuthProviderType

#: Cap on the client-supplied device label a paired device may attach to its
#: session (#1118). It lives here, next to the model that carries the field,
#: because both enforcing boundaries need it and neither may import the other:
#: ``app.api.v1.auth.schemas`` bounds the HTTP request (over-long input becomes
#: a 422, never a 500 — BACKEND.md §5.4) and ``AuthService`` bounds every
#: non-HTTP caller, but a domain service importing an API schema would invert
#: the NFR-001 layer order. One constant, two boundaries, no second literal.
DEVICE_NAME_MAX_LENGTH = 64

#: The prefix every raw API key carries; the bearer resolver tells a key from a JWT by it.
API_KEY_PREFIX = "kp_"

#: #2137 (MT-041) — the bounds of the controls a key is minted with. One home for both
#: minting doors (``AuthService.create_api_key`` and the service-account routes of
#: ``TenantService``) and for the request schemas that document them.
#:
#: At most this many allowlist entries: a list longer than this is a configuration
#: nobody can review, and every entry is parsed on each request of the key.
API_KEY_IP_ALLOWLIST_MAX_ENTRIES = 32
#: The widest range an allowlist entry may name, per address family (REQ-023 §5b.6:
#: "Maximale Range: /8 (IPv4), /32 (IPv6) — verhindert 0.0.0.0/0"). An allowlist
#: that admits everything is no allowlist; it only looks like one.
API_KEY_MIN_PREFIX_LENGTH = {4: 8, 6: 32}
#: The rate-limit bounds of the stored model (``ApiKey.rate_limit_per_minute``).
API_KEY_RATE_LIMIT_MIN = 1
API_KEY_RATE_LIMIT_MAX = 10000
#: How far ahead an expiry may be set. Two years: long enough for an integration
#: nobody wants to touch twice a year, short enough that a forgotten key ends.
API_KEY_MAX_LIFETIME_DAYS = 730


class AuthProvider(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    provider: AuthProviderType
    provider_user_id: str
    #: The configuration the link was made through, and the ``iss`` of its ID token
    #: (#1815 review SEC-001). A link type alone (``oidc``) cannot tell two generic
    #: OIDC providers apart; the step-up re-authentication matches a link only to its
    #: own configuration, and the login matches a link only through it (#1869).
    #: ``None`` on links made before these fields existed. Migration v0064 bound
    #: every such link whose type had exactly one configuration; one still unbound
    #: matches nothing — neither the login (``AuthService._login_link``) nor the
    #: step-up (``FederatedReauthPolicy``) guesses it. ``issuer`` is recorded on the
    #: first sign-in of a link that has none.
    oidc_config_slug: str | None = None
    #: The immutable ``_key`` of that configuration (#1987). A slug can be deleted and
    #: re-used; the key cannot, so a link written by a login that loaded the OLD
    #: configuration — slug and all — is recognisable as an orphan of it and is never
    #: matched by the new one. ``None`` on links made before #1987 (and on those of a
    #: configuration whose key the writer did not know): those are matched by slug alone,
    #: exactly as before, which is why no migration rewrites them.
    oidc_config_key: str | None = None
    issuer: str | None = None
    provider_email: str | None = None
    provider_display_name: str | None = None
    avatar_url: str | None = None
    access_token_encrypted: str | None = None
    refresh_token_encrypted: str | None = None
    token_expires_at: datetime | None = None
    last_used_at: datetime | None = None
    linked_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AuthProviderInfo(BaseModel):
    key: str
    provider: AuthProviderType
    provider_email: str | None
    provider_display_name: str | None
    linked_at: datetime | None
    last_used_at: datetime | None = None


class RefreshToken(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    token_hash: str
    user_agent: str | None = None
    #: Label a paired device supplied for itself (#1118), so a phone is
    #: distinguishable from a browser in the session list. ``None`` for every
    #: session minted by the browser login and OAuth paths, and for every
    #: document written before this field existed — ArangoDB is schemaless, so
    #: those documents simply arrive without the key and default here.
    #:
    #: Deliberately **unconstrained on the model**: the length cap is enforced
    #: on the two write boundaries (see :data:`DEVICE_NAME_MAX_LENGTH`), because
    #: a ``max_length`` here would turn a single over-long stored value into a
    #: 500 on ``GET /users/me/sessions`` — a read path failing on data it did
    #: not create is how "422 at the boundary" becomes "500 in the list".
    device_name: str | None = None
    ip_address: str | None = None
    ip_anonymized_at: datetime | None = None
    expires_at: datetime
    is_persistent: bool = False
    revoked: bool = False
    created_at: datetime | None = None
    #: The login this token descends from (REQ-023 §3.2a, #2116): every successor a
    #: rotation mints inherits it, every new login starts a new one. A replayed
    #: rotated token revokes the whole family. ``None`` on a token minted before
    #: families existed; its first rotation adopts the token's own key as the family.
    family_key: str | None = None
    #: When a rotation consumed this token; ``None`` while it is the live end of its
    #: family. A rotated token is also ``revoked`` and is kept until ``expires_at``,
    #: because presenting it again is the replay signal.
    rotated_at: datetime | None = None
    #: Document key of the token the rotation minted in its place.
    successor_key: str | None = None
    #: ``User.session_generation`` at the login the family descends from (#2116).
    #: A refresh is refused once the account's generation moved past it (logout
    #: everywhere, password reset or change, deactivation) — even if a revocation
    #: write raced the rotation that minted this token.
    session_generation: int = 0

    model_config = {"populate_by_name": True}


class TokenPayload(BaseModel):
    sub: str  # user_key
    tenant_roles: dict[str, str] = Field(default_factory=dict)
    is_platform_admin: bool = False
    exp: int
    iat: int
    jti: str
    type: str = "access"
    #: ``User.access_token_generation`` when the token was minted (#2116, claim
    #: ``gen``). A token minted before the claim existed reads as ``0`` and stays
    #: valid until its expiry unless the account's generation has moved since.
    gen: int = 0
    #: The refresh-token family the token was minted for (claim ``sid``); ``None``
    #: on tokens minted before #2116.
    sid: str | None = None


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class OAuthRedirect(BaseModel):
    authorization_url: str
    state: str
    nonce: str = ""
    code_verifier: str = ""


class OAuthUserInfo(BaseModel):
    provider: AuthProviderType
    provider_user_id: str
    email: str
    display_name: str
    avatar_url: str | None = None
    #: The provider's ``email_verified`` claim, or ``None`` when it said nothing
    #: (#1403). Three states, not two, and the third is the interesting one: many
    #: OIDC providers omit the claim entirely, and collapsing "absent" into
    #: ``False`` at the parse site would hide *which* providers are silent from
    #: the place that has to decide what silence means. The decision itself lives
    #: in :meth:`OAuthEngine.should_auto_link`.
    #:
    #: Until #1403 this field did not exist and the auto-link call site supplied
    #: a literal ``True`` for it, so the claim was never read at all.
    email_verified: bool | None = None


class SessionInfo(BaseModel):
    key: str
    user_agent: str | None
    #: ``None`` unless the session was created by a device pairing that supplied
    #: a label; the session list falls back to ``user_agent`` then.
    device_name: str | None = None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool = False
    is_persistent: bool = False


def new_api_key_secret() -> tuple[str, str, str]:
    """A fresh raw key, the SHA-256 digest that is stored, and the display prefix.

    The raw key leaves the server once, in the creation response; only the digest is
    kept (``authenticate_api_key`` / the MCP authenticator look keys up by it).
    """
    raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    return raw_key, hashlib.sha256(raw_key.encode()).hexdigest(), raw_key[:8]


def api_key_control_errors(
    *,
    ip_allowlist: list[str] | None,
    rate_limit_per_minute: int | None,
    expires_at: datetime | None,
    now: datetime,
) -> tuple[list[str] | None, list[dict[str, str]]]:
    """Check the controls a key is to be minted with (#2137); returns the canonical allowlist and the errors.

    Pure: the caller raises (422) when the error list is not empty, and stores the
    canonical allowlist otherwise. Canonical means each entry is written as a
    network (``192.0.2.10`` becomes ``192.0.2.10/32``) and an empty list becomes
    ``None`` — both admit everything on the enforcing side, one stored spelling.

    An entry is refused when it is no network, has host bits set (``10.0.0.5/8``
    almost always means something narrower than what it admits), or is wider than
    :data:`API_KEY_MIN_PREFIX_LENGTH` allows. An expiry must carry a timezone, lie
    in the future and at most :data:`API_KEY_MAX_LIFETIME_DAYS` ahead.
    """
    errors: list[dict[str, str]] = []
    canonical: list[str] | None = None
    if ip_allowlist:
        if len(ip_allowlist) > API_KEY_IP_ALLOWLIST_MAX_ENTRIES:
            errors.append(
                {
                    "field": "ip_allowlist",
                    "reason": f"At most {API_KEY_IP_ALLOWLIST_MAX_ENTRIES} entries.",
                    "code": "ip_allowlist_too_long",
                }
            )
        canonical = []
        for entry in ip_allowlist:
            try:
                network = ipaddress.ip_network(entry, strict=True)
            except ValueError:
                errors.append(
                    {
                        "field": "ip_allowlist",
                        "reason": f"{entry!r} is not a network in CIDR notation, or has host bits set.",
                        "code": "ip_allowlist_invalid_entry",
                    }
                )
                continue
            widest = API_KEY_MIN_PREFIX_LENGTH[network.version]
            if network.prefixlen < widest:
                errors.append(
                    {
                        "field": "ip_allowlist",
                        "reason": f"{entry!r} is wider than /{widest}.",
                        "code": "ip_allowlist_too_wide",
                    }
                )
                continue
            canonical.append(str(network))
        canonical = canonical or None
    if rate_limit_per_minute is not None and not (
        API_KEY_RATE_LIMIT_MIN <= rate_limit_per_minute <= API_KEY_RATE_LIMIT_MAX
    ):
        errors.append(
            {
                "field": "rate_limit_per_minute",
                "reason": f"Between {API_KEY_RATE_LIMIT_MIN} and {API_KEY_RATE_LIMIT_MAX}.",
                "code": "rate_limit_out_of_bounds",
            }
        )
    if expires_at is not None:
        if expires_at.tzinfo is None:
            errors.append(
                {"field": "expires_at", "reason": "Must carry a timezone.", "code": "expires_at_without_timezone"}
            )
        elif expires_at <= now:
            errors.append({"field": "expires_at", "reason": "Must lie in the future.", "code": "expires_at_past"})
        elif expires_at > now + timedelta(days=API_KEY_MAX_LIFETIME_DAYS):
            errors.append(
                {
                    "field": "expires_at",
                    "reason": f"At most {API_KEY_MAX_LIFETIME_DAYS} days ahead.",
                    "code": "expires_at_beyond_horizon",
                }
            )
    return canonical, errors


class ApiKey(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    label: str = Field(min_length=1, max_length=100)
    key_hash: str
    key_prefix: str  # First 8 chars for identification
    tenant_scope: str | None = None  # If set, key only works for this tenant
    # REQ-023 v1.10 service-account hardening: optional CIDR allowlist
    # and per-key rate limit (requests per minute). Both fields default
    # to None which means "no restriction" — applies to both interactive
    # user keys and service-account keys.
    ip_allowlist: list[str] | None = None
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=10000)
    revoked: bool = False
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


def successor_api_key(
    previous: ApiKey | None,
    *,
    user_key: str,
    tenant_scope: str,
    label: str,
    key_hash: str,
    key_prefix: str,
    expires_at: datetime | None,
) -> ApiKey:
    """The key a rotation mints (#2137): the predecessor's network controls, a new secret and expiry.

    The allowlist and the rate limit carry over from *previous* — a rotation replaces the secret, it
    must not quietly widen what the key admits. The tenant scope is the caller's (the service account's
    tenant), never read off the predecessor. Built here because the controls are read off a stored key
    in this module only (``test_api_key_controls_bind_every_key_surface``).
    """
    return ApiKey(
        user_key=user_key,
        label=label,
        key_hash=key_hash,
        key_prefix=key_prefix,
        tenant_scope=tenant_scope,
        ip_allowlist=previous.ip_allowlist if previous else None,
        rate_limit_per_minute=previous.rate_limit_per_minute if previous else None,
        expires_at=expires_at,
    )


def api_key_scope_admits(scope: str | None, *, tenant_key: str) -> bool:
    """Whether an API key restricted to *scope* may act in the tenant *tenant_key* (REQ-023).

    The one predicate both key-accepting surfaces decide on — the REST tenant
    resolvers (``app.common.auth``) and the MCP authenticator — so they can never
    disagree about which tenant a key reaches (#1817). An absent or empty scope
    restricts nothing.

    **Matched on the tenant key only (#1852).** A slug is not an identity: a
    rename re-derives it and a deleted tenant's slug can be issued again, so a
    slug-form scope would follow the *name* to whichever tenant holds it now.
    ``AuthService.create_api_key`` therefore stores the resolved tenant key, and
    migration ``v0063`` rewrote the slug-form scopes stored before.
    """
    if not scope:
        return True
    return scope == tenant_key


def api_key_ip_admits(allowlist: list[str] | None, client_ip: str | None) -> bool:
    """Whether a request from *client_ip* passes an API key's ``ip_allowlist`` (SEC-004).

    An empty or absent allowlist admits every address. A configured one fails
    **closed**: an unresolvable or unparsable client IP, and an address outside
    every listed range, are refused. A malformed entry never widens access — it
    is skipped, not read as "everything".
    """
    if not allowlist:
        return True
    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for entry in allowlist:
        try:
            network = ipaddress.ip_network(entry, strict=False)
        except ValueError:
            continue
        if addr in network:
            return True
    return False


class ApiKeySummary(BaseModel):
    key: str
    label: str
    key_prefix: str
    tenant_scope: str | None
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime | None
    #: #2137 — the controls the key was minted with, so its owner can see what binds it.
    ip_allowlist: list[str] | None = None
    rate_limit_per_minute: int | None = None
    expires_at: datetime | None = None

    @classmethod
    def of(cls, api_key: ApiKey) -> ApiKeySummary:
        """The metadata of a stored key — never its digest.

        Built here, next to the model, because the controls are read off the key in
        this module only (``test_api_key_controls_bind_every_key_surface``).
        """
        return cls(
            key=api_key.key or "",
            label=api_key.label,
            key_prefix=api_key.key_prefix,
            tenant_scope=api_key.tenant_scope,
            revoked=api_key.revoked,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
            ip_allowlist=api_key.ip_allowlist,
            rate_limit_per_minute=api_key.rate_limit_per_minute,
            expires_at=api_key.expires_at,
        )


class ApiKeyCreated(BaseModel):
    """A freshly minted key: its metadata plus the raw key, shown this once."""

    key: str
    label: str
    raw_key: str  # Only shown once at creation
    key_prefix: str
    tenant_scope: str | None
    created_at: datetime | None
    ip_allowlist: list[str] | None = None
    rate_limit_per_minute: int | None = None
    expires_at: datetime | None = None

    @classmethod
    def minted(cls, api_key: ApiKey, raw_key: str) -> ApiKeyCreated:
        return cls(
            key=api_key.key or "",
            label=api_key.label,
            raw_key=raw_key,
            key_prefix=api_key.key_prefix,
            tenant_scope=api_key.tenant_scope,
            created_at=api_key.created_at,
            ip_allowlist=api_key.ip_allowlist,
            rate_limit_per_minute=api_key.rate_limit_per_minute,
            expires_at=api_key.expires_at,
        )
