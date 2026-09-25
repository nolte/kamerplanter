from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Path

from app.api.v1.auth.schemas import (
    AuthProviderResponse,
    MessageResponse,
    SessionResponse,
    UserProfileResponse,
)
from app.api.v1.privacy.schemas import ErasureCreateRequest
from app.api.v1.users.schemas import ChangePasswordRequest, ProfileUpdateRequest
from app.common.auth import (
    get_authenticated_with_api_key,
    get_current_user,
    get_is_platform_admin,
    refuse_in_light_mode,
    require_account_principal,
)
from app.common.dependencies import get_auth_service, get_privacy_service, get_user_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.common.request_ip import resolve_client_ip
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


@router.delete("/me/providers/{provider_key}", response_model=MessageResponse)
def unlink_provider(
    provider_key: Annotated[str, Path(description="Document key of the linked auth provider.")],
    current_user: User = Depends(require_account_principal),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Unlink an OAuth provider from the current user's account."""
    auth_service.unlink_provider(current_user.key or "", provider_key)
    return MessageResponse(message="Provider unlinked.")


@router.post("/me/password", response_model=MessageResponse, dependencies=[Depends(refuse_in_light_mode)])
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
    many failures, in the same budget as account erasure and tenant deletion.

    Refused in light mode (403, #1844): the shared system account has no
    password, so the step-up would let any unauthenticated caller set its first
    one — a sign-in that starts working when the instance is switched to full.
    """
    auth_service.change_password(
        current_user.key or "",
        body.current_password,
        body.new_password,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Password changed. All sessions revoked.")


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


@router.delete("/me", response_model=MessageResponse)
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
    password for an account that has one (401); an API-key request or a service
    account is refused (403); 429 ``STEP_UP_LOCKED`` after too many failures
    (#1816).
    """
    service.request_erasure(
        current_user.key or "",
        confirmation=body.to_confirmation(),
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return MessageResponse(message="Account erasure requested.")
