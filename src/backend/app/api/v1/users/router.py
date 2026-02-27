from fastapi import APIRouter, Cookie, Depends

from app.api.v1.auth.schemas import (
    AuthProviderResponse,
    MessageResponse,
    SessionResponse,
    UserProfileResponse,
)
from app.api.v1.users.schemas import ChangePasswordRequest, ProfileUpdateRequest
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service, get_user_service
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User, UserProfileUpdate
from app.domain.services.auth_service import AuthService
from app.domain.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    profile = service.get_profile(current_user.key or "")
    return UserProfileResponse(**profile.model_dump())


@router.patch("/me", response_model=UserProfileResponse)
def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    update = UserProfileUpdate(**body.model_dump(exclude_none=True))
    profile = service.update_profile(current_user.key or "", update)
    return UserProfileResponse(**profile.model_dump())


@router.get("/me/providers", response_model=list[AuthProviderResponse])
def list_providers(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    providers = auth_service.list_providers(current_user.key or "")
    return [AuthProviderResponse(**p.model_dump()) for p in providers]


@router.delete("/me/providers/{provider_key}", response_model=MessageResponse)
def unlink_provider(
    provider_key: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.unlink_provider(current_user.key or "", provider_key)
    return MessageResponse(message="Provider unlinked.")


@router.post("/me/password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.change_password(current_user.key or "", body.current_password, body.new_password)
    return MessageResponse(message="Password changed. All sessions revoked.")


@router.get("/me/sessions", response_model=list[SessionResponse])
def list_sessions(
    current_user: User = Depends(get_current_user),
    kp_refresh: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    current_hash = TokenEngine.hash_token(kp_refresh) if kp_refresh else None
    sessions = auth_service.list_sessions(current_user.key or "", current_hash)
    return [SessionResponse(**s.model_dump()) for s in sessions]


@router.delete("/me/sessions/{session_key}", response_model=MessageResponse)
def revoke_session(
    session_key: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.revoke_session(current_user.key or "", session_key)
    return MessageResponse(message="Session revoked.")


@router.delete("/me", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    service.delete_account(current_user.key or "")
    return MessageResponse(message="Account deleted.")
