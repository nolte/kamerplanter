from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.validators import DisplayName

# The cap on the client-supplied device label (#1118) is defined **once**, on
# the domain model that persists the field, and imported here: ``AuthService``
# enforces the same bound for non-HTTP callers and a domain service may not
# import an API schema (NFR-001). This boundary is where an over-long value
# becomes a 422 instead of a 500 (BACKEND.md §5.4).
from app.domain.models.auth import DEVICE_NAME_MAX_LENGTH

# ── Request schemas ────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: DisplayName


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    #: Opt-in to the native-client transport (#1134): return the refresh token in
    #: the response body and set **no** ``kp_refresh`` cookie.
    #:
    #: Default ``False``, and the default is the load-bearing part. A browser must
    #: never receive its refresh token as readable JSON — XSS that reads a
    #: response body would harvest a 30-day credential where the HttpOnly cookie
    #: gives it nothing. So the weaker transport is never the fallback and never
    #: inferred from a header, a user agent or the absence of a cookie jar: it is
    #: reachable only by a client that names it, which is a decision that shows up
    #: in the request and in the audit trail rather than in a heuristic.
    #:
    #: A client that sets this gets exactly one transport for the credential, the
    #: same rule ``/refresh`` and ``/device-pairing/redeem`` already follow.
    refresh_token_in_body: bool = False


class VerifyEmailRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)


#: Upper bound on the raw refresh token accepted in a request body (#1118).
#: The tokens this service mints are ``secrets.token_urlsafe(64)`` → 86
#: characters; the cap is deliberately far above that so a future widening of the
#: token does not silently start answering 422, while still keeping an
#: unauthenticated caller from posting an unbounded string that would be hashed
#: before anything could reject it.
REFRESH_TOKEN_MAX_LENGTH = 512


class RefreshRequest(BaseModel):
    """Body-borne refresh transport for clients without a cookie jar (#1118).

    Optional on ``POST /auth/refresh``. A browser sends **no body at all** and
    keeps the HttpOnly ``kp_refresh`` cookie plus the CSRF double-submit — that
    path is untouched and remains the stronger transport wherever a cookie jar
    exists. A device paired by QR code (REQ-023 §device pairing) has neither a
    cookie jar nor a way to obtain the ``csrf_token`` cookie, so it presents the
    raw refresh token it received from the redemption response here instead.

    Without this, the pair handed to a paired device would expire 15 minutes
    later with no way to rotate — the feature would be inert on arrival.

    ``refresh_token`` is nullable so an explicit ``null`` reads exactly like an
    omitted body (fall through to the cookie), while ``min_length=1`` refuses an
    empty string outright rather than letting it degrade quietly into spending
    the ambient cookie credential.
    """

    refresh_token: str | None = Field(
        default=None,
        min_length=1,
        max_length=REFRESH_TOKEN_MAX_LENGTH,
        description=(
            "Raw refresh token of a paired device. Omit the field (or the whole body) "
            "to rotate the HttpOnly `kp_refresh` cookie instead."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl"},
            ]
        }
    )


class ApiKeyCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    tenant_scope: str | None = None


class SetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


class DevicePairingRedeemRequest(BaseModel):
    """Exchange a scanned QR pairing code for a token pair (#1118).

    **The absent field is the contract.** There is no ``user_key``, ``email`` or
    any other identity here, and there must never be one: the code *is* the
    identity assertion — it was bound to its issuing account when it was minted
    — and the endpoint is unauthenticated. An identity field would be a
    caller-supplied claim on an unauthenticated route, i.e. exactly the input a
    handler must not be tempted to trust. ``AuthService.redeem_device_pairing``
    carries an absence test for the same property one layer down.
    """

    code: str = Field(
        min_length=1,
        max_length=512,
        description="The raw one-time pairing code read from the QR payload.",
    )
    #: Free text from an unauthenticated caller, hence bounded here rather than
    #: only in the service: over-long input answers 422, never 500 (§5.4).
    device_name: str | None = Field(
        default=None,
        max_length=DEVICE_NAME_MAX_LENGTH,
        description="Optional client-supplied label shown in the session list.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
                    "device_name": "Pixel 8 (Gewächshaus)",
                }
            ]
        }
    )


# ── Response schemas ───────────────────────────────────────────────


class UserProfileResponse(BaseModel):
    key: str
    email: str
    display_name: str
    email_verified: bool
    is_active: bool
    avatar_url: str | None
    locale: str
    timezone: str = "Europe/Berlin"
    last_login_at: datetime | None
    created_at: datetime | None
    # Global platform-admin flag (admin membership in the "platform" tenant).
    # Gates admin-only UI such as reference-image curation. Defaults to False so
    # other construction sites need not supply it.
    is_platform_admin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPairResponse(BaseModel):
    """The REQ-023 token pair with the refresh token **in the body** (#1118).

    ``TokenResponse`` is the browser shape: the refresh token never appears in
    the JSON, it leaves as an HttpOnly ``kp_refresh`` cookie (AP-7 / FE-S1), and
    that is the stronger transport wherever a cookie jar exists.

    A native client has none. It stores the refresh token in the platform
    keystore, so it has to *receive* it — and if it cannot, the pair it was
    handed dies 15 minutes later with no way to rotate, which is the whole
    feature being inert. The deviation is therefore deliberate, operator-approved
    and confined to the routes that serve non-browser clients; the browser flow
    keeps its cookie unchanged. Responses using this model MUST NOT also set the
    refresh cookie: two transports for one credential doubles its exposure and
    leaves no single place that revokes it.
    """

    access_token: str
    token_type: str = "bearer"
    #: Lifetime of ``access_token`` in seconds — not of the refresh token.
    expires_in: int
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MjcxNjM0In0.sIgn4tur3",
                    "token_type": "bearer",
                    "expires_in": 900,
                    "refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl",
                }
            ]
        }
    )


class DevicePairingCreateResponse(BaseModel):
    """Everything the browser needs to render one QR pairing code (#1118).

    The three payload fields (``payload_version``, ``server_url``, ``code``) are
    what the scanner reads; ``expires_at`` and ``expires_in`` drive the countdown
    and are two views of one instant, so a client with a skewed clock can use the
    relative one and a client that stores the code can use the absolute one.
    """

    #: Version of the QR payload contract ``{"v": …, "url": …, "code": …}``.
    #: Present from v1 so a future scanner can refuse a payload it predates,
    #: rather than mis-parsing it.
    payload_version: int
    #: Base URL the paired client must call — ``settings.app_base_url``, the
    #: REQ-032 QR-code SSOT, and never ``request.base_url``: behind Traefik the
    #: latter is an in-cluster address the phone cannot reach.
    server_url: str
    code: str
    expires_at: datetime
    #: Seconds remaining at the moment of the response, derived from
    #: ``expires_at`` so the two can never disagree.
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "payload_version": 1,
                    "server_url": "https://garten.example.org",
                    "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
                    "expires_at": "2026-08-11T14:32:41Z",
                    "expires_in": 90,
                }
            ]
        }
    )


class AuthProviderResponse(BaseModel):
    key: str
    provider: str
    provider_email: str | None
    provider_display_name: str | None
    linked_at: datetime | None
    last_used_at: datetime | None = None


class SessionResponse(BaseModel):
    """One revocable session in ``GET /users/me/sessions``.

    The example below shows a **paired device** (#1118): ``device_name`` is the
    label that device supplied for itself, and it is ``null`` for every session
    a browser login or an OAuth callback created — the list falls back to
    ``user_agent`` there. Sessions stored before the field existed simply carry
    no key in the document and read as ``null`` too, which is why the field is
    optional rather than required.
    """

    key: str
    user_agent: str | None
    #: Self-chosen label of a paired device, capped at
    #: :data:`DEVICE_NAME_MAX_LENGTH` characters on the way in; ``null`` for
    #: browser and OAuth sessions.
    device_name: str | None = None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool
    is_persistent: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "4711829",
                    "user_agent": "Kamerplanter/1.0 (Android 15)",
                    "device_name": "Pixel 8 (Gewächshaus)",
                    "ip_address": "203.0.113.7",
                    "created_at": "2026-08-11T14:31:11Z",
                    "expires_at": "2026-09-10T14:31:11Z",
                    "is_current": False,
                    "is_persistent": True,
                }
            ]
        }
    )


class OAuthProviderListItem(BaseModel):
    slug: str
    display_name: str
    icon_url: str | None


class ApiKeyCreatedResponse(BaseModel):
    key: str
    label: str
    raw_key: str
    key_prefix: str
    tenant_scope: str | None
    created_at: datetime | None


class ApiKeySummaryResponse(BaseModel):
    key: str
    label: str
    key_prefix: str
    tenant_scope: str | None
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime | None


class MessageResponse(BaseModel):
    message: str
