from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Path, Request

from app.api.v1.auth.router import limiter, step_up_callback_url
from app.api.v1.auth.schemas import (
    AuthProviderResponse,
    MessageResponse,
    SessionResponse,
    UserProfileResponse,
)
from app.api.v1.privacy.schemas import ErasureCreateRequest
from app.api.v1.users.schemas import (
    ChangePasswordRequest,
    ProfileUpdateRequest,
    ProviderUnlinkRequest,
    StepUpCodeRequest,
    StepUpCodeResponse,
    StepUpReauthRequest,
    StepUpReauthStart,
)
from app.common.auth import (
    get_authenticated_with_api_key,
    get_current_user,
    get_is_platform_admin,
    refuse_in_light_mode,
    require_account_principal,
)
from app.common.dependencies import get_auth_service, get_privacy_service, get_user_service
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    STEP_UP_CODE_UNDELIVERABLE_RESPONSE,
    STEP_UP_CODE_VALIDATION_RESPONSE,
    STEP_UP_REAUTH_VALIDATION_RESPONSE,
    STEP_UP_RESPONSES,
    UNAUTHORIZED_RESPONSE,
)
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User, UserProfileUpdate
from app.domain.services.auth_service import AuthService
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE},
)


@router.get("/me", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
    platform_admin: bool = Depends(get_is_platform_admin),
):
    """Return the current user's profile plus platform-admin flag.

    Admits a tenant-scoped API key (#1851): the Home Assistant integration reads
    its identity here. The flag comes from :func:`get_is_platform_admin`, which
    answers ``False`` for such a key, so the profile never advertises a
    platform role the key cannot exercise.
    """
    profile = service.get_profile(current_user.key or "")
    return UserProfileResponse(
        **profile.model_dump(),
        is_platform_admin=platform_admin,
    )


@router.patch("/me", response_model=UserProfileResponse)
def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(require_account_principal),
    service: UserService = Depends(get_user_service),
):
    """Update the current user's profile."""
    update = UserProfileUpdate(**body.model_dump(exclude_none=True))
    profile = service.update_profile(current_user.key or "", update)
    return UserProfileResponse(**profile.model_dump())


@router.get("/me/providers", response_model=list[AuthProviderResponse])
def list_providers(
    current_user: User = Depends(require_account_principal),
    auth_service: AuthService = Depends(get_auth_service),
):
    """List the OAuth providers linked to the current user's account."""
    providers = auth_service.list_providers(current_user.key or "")
    return [AuthProviderResponse(**p.model_dump()) for p in providers]


@router.delete("/me/providers/{provider_key}", response_model=MessageResponse, responses=STEP_UP_RESPONSES)
def unlink_provider(
    provider_key: Annotated[str, Path(description="Document key of the linked auth provider.")],
    body: ProviderUnlinkRequest | None = None,
    current_user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Unlink an OAuth provider from the current user's account.

    **Step-up (#1847):** removing a sign-in method is a credential change — the
    current password in the body (or, for an account without one,
    ``step_up_token`` / ``step_up_code``); 401 without it, 403 from an API-key
    request, 429 ``STEP_UP_LOCKED``.
    """
    step_up = body or ProviderUnlinkRequest()
    auth_service.unlink_provider(
        current_user.key or "",
        provider_key,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Provider unlinked.")


@router.post(
    "/me/password",
    response_model=MessageResponse,
    responses=STEP_UP_RESPONSES,
    dependencies=[Depends(refuse_in_light_mode)],
)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change the current user's password and revoke all sessions.

    The current password is a step-up (#1816): refused from an API-key request
    (403), throttled per account and address — 429 ``STEP_UP_LOCKED`` after too
    many failures, in the same budget as account erasure and tenant deletion. An
    account without a local password (setting its first one) sends the code from
    ``POST /users/me/step-up-code`` as ``step_up_code`` instead — 401
    ``STEP_UP_CODE_REQUIRED`` without it (#1815).

    Refused in light mode (403, #1844): the shared system account has no
    password, so the step-up would let any unauthenticated caller set its first
    one — a sign-in that starts working when the instance is switched to full.
    """
    auth_service.change_password(
        current_user.key or "",
        body.current_password,
        body.new_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Password changed. All sessions revoked.")


@router.post(
    "/me/step-up-code",
    response_model=StepUpCodeResponse,
    status_code=202,
    responses={
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **CONFLICT_RESPONSE,
        **STEP_UP_RESPONSES,
        **STEP_UP_CODE_VALIDATION_RESPONSE,
        **STEP_UP_CODE_UNDELIVERABLE_RESPONSE,
    },
    dependencies=[Depends(refuse_in_light_mode)],
)
@limiter.limit(settings.rate_limit_auth)
def send_step_up_code(
    request: Request,
    body: StepUpCodeRequest,
    current_user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Mail a one-time confirmation code to an account without a local password (#1815).

    An account that signs in only through a federated provider has no password to
    re-enter before an irreversible act or a credential change — account erasure,
    tenant deletion, setting a first password, changing the e-mail address. It
    confirms those with this code, sent back as ``step_up_code``. The body names the
    act (``action``); the code confirms that act only and the mail says which it is
    (review SEC-003). The code is eight digits, valid for ten minutes, spent by the
    first act that presents it, and a new request replaces the previous code — but
    not within 60 seconds while it is unspent, and at most five codes per account
    and hour (review SEC-002). It is only ever mailed to the account's own address,
    never returned here.

    **Target (#1884).** An act on something other than the requester's own account
    names it as ``target`` (see the field); the code confirms that target only, and
    is mailed only when the target exists and the requester may act on it.

    Answers: 202 mailed; 403 a request authenticated with an API key or a service
    account, or a target the requester may not act on; 404 the target does not
    exist; 422 the account has a local password and confirms with it, the act is
    missing/unknown, or ``target`` is missing for a targeted act or given for
    another; 429 ``STEP_UP_LOCKED`` (``details[0].retry_after_minutes``)
    while too many failed confirmations hold the step-up, an unspent code is younger
    than a minute, or the account's hourly code budget is spent — and a plain 429
    when the per-address budget ``settings.rate_limit_auth`` is spent; 503
    ``STEP_UP_CODE_UNDELIVERABLE`` when the mail cannot be delivered (the console
    e-mail adapter outside ``debug``, an SMTP failure) — the code is then withdrawn
    and its issuance given back, so the retry is not held by the wait or budget.

    ``request`` is required by the rate-limit decorator (slowapi inspects the signature).
    """
    expires_at = auth_service.send_step_up_code(
        current_user.key or "",
        action=body.action,
        target=body.target,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return StepUpCodeResponse(
        expires_at=expires_at,
        expires_in=max(0, round((expires_at - datetime.now(UTC)).total_seconds())),
    )


@router.post(
    "/me/step-up/oidc",
    response_model=StepUpReauthStart,
    responses={
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **CONFLICT_RESPONSE,
        **STEP_UP_RESPONSES,
        **STEP_UP_REAUTH_VALIDATION_RESPONSE,
    },
    dependencies=[Depends(refuse_in_light_mode)],
)
@limiter.limit(settings.rate_limit_auth)
def start_step_up_reauth(
    request: Request,
    body: StepUpReauthRequest,
    current_user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Start a fresh sign-in at a linked identity provider to confirm one act (#1815).

    For an account without a local password whose linked provider supports it
    (OpenID Connect — Google, a generic OIDC provider; not GitHub, which is plain
    OAuth2, and not Apple, which reports no sign-in time). Answers the provider's
    authorization URL: the login request plus ``prompt=login`` and ``max_age=0``.
    The provider redirects to ``/auth/oauth/{slug}/callback``; that callback signs
    nobody in but redirects to ``{frontend}/auth/step-up/callback`` with
    ``#step_up_token=…&action=…`` in the fragment — or ``?error=step_up_failed``,
    ``step_up_stale`` (the sign-in was older than five minutes) or
    ``step_up_cancelled``. The act's body then carries the token as ``step_up_token``.

    The token is bound to the act's ``target`` (#1884) the same way the mailed code
    is; the target is checked here, before the browser leaves.

    Answers: 200 the URL; 403 an API-key request, a service account, light mode, or
    a target the requester may not act on; 404 the target does not exist; 422 the
    account has a local password, no linked provider (or not ``provider_key``)
    supports a fresh sign-in — it confirms with the e-mailed code — the act is
    unknown, or ``target`` is missing for a targeted act or given for another; 429
    ``STEP_UP_LOCKED`` while the step-up is locked.

    ``request`` is required by the rate-limit decorator. The callback URL is built
    from ``settings.app_base_url``, never from the request's Host header.
    """
    url = auth_service.start_step_up_reauth(
        current_user.key or "",
        action=body.action,
        target=body.target,
        provider_key=body.provider_key,
        client_nonce=body.client_nonce,
        # The public base URL, not ``request.base_url`` (review SEC-002): the Host
        # header is the caller's to choose, and the callback URL must be the one
        # registered at the provider. ``app_base_url`` is the address /api is
        # reachable under (the QR-code and device-pairing SSOT).
        callback_url=lambda slug: step_up_callback_url(slug),
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return StepUpReauthStart(authorization_url=url)


@router.get("/me/sessions", response_model=list[SessionResponse])
def list_sessions(
    current_user: User = Depends(require_account_principal),
    kp_refresh: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """List the current user's active sessions."""
    current_hash = TokenEngine.hash_token(kp_refresh) if kp_refresh else None
    sessions = auth_service.list_sessions(current_user.key or "", current_hash)
    return [SessionResponse(**s.model_dump()) for s in sessions]


@router.delete("/me/sessions/{session_key}", response_model=MessageResponse)
def revoke_session(
    session_key: Annotated[str, Path(description="Document key of the session to revoke.")],
    current_user: User = Depends(require_account_principal),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke one of the current user's sessions."""
    auth_service.revoke_session(current_user.key or "", session_key)
    return MessageResponse(message="Session revoked.")


@router.delete("/me", response_model=MessageResponse, responses=STEP_UP_RESPONSES)
def delete_account(
    body: ErasureCreateRequest,
    current_user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Request the erasure of the current user's account (REQ-025 Art. 17).

    The same act as ``POST /privacy/erasure`` and the same service entry (#1813).
    Until #1813 this route tombstoned the user document on a bare session — no
    password, no erasure record, and every personal record left behind. It now
    opens the Art. 17 request: the account is closed at once and hard-deleted after
    the grace period (``RETENTION_SOFT_DELETE_RETENTION_DAYS``).

    **Step-up:** the body echoes the account's e-mail (422) and carries the current
    password for an account that has one (401), the code from
    ``POST /users/me/step-up-code`` as ``step_up_code`` for one without (401
    ``STEP_UP_CODE_REQUIRED``, #1815); an API-key request or a service account is
    refused (403); 429 ``STEP_UP_LOCKED`` after too many failures (#1816).
    """
    service.request_erasure(
        current_user.key or "",
        confirmation=body.to_confirmation(),
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Account erasure requested.")
