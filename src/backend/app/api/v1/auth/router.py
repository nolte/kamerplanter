from fastapi import APIRouter, Cookie, Depends, Request, Response

from app.api.v1.auth.schemas import (
    LoginRequest,
    MessageResponse,
    OAuthProviderListItem,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
    VerifyEmailRequest,
)
from app.common.auth import get_current_user, get_refresh_token_from_cookie
from app.common.dependencies import get_auth_service, get_oidc_config_repo
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, raw_refresh_token: str, max_age_days: int = 30) -> None:
    response.set_cookie(
        key="kp_refresh",
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=max_age_days * 86400,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="kp_refresh", path="/api/v1/auth")


@router.post("/register", response_model=UserProfileResponse, status_code=201)
def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    profile = service.register_local(body.email, body.password, body.display_name)
    return UserProfileResponse(**profile.model_dump())


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    token_pair, raw_refresh = service.login_local(
        body.email, body.password, user_agent, ip_address,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=token_pair.access_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    request: Request,
    kp_refresh: str = Depends(get_refresh_token_from_cookie),
    service: AuthService = Depends(get_auth_service),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    token_pair, new_raw_refresh = service.refresh_tokens(kp_refresh, user_agent, ip_address)
    _set_refresh_cookie(response, new_raw_refresh)
    return TokenResponse(
        access_token=token_pair.access_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    kp_refresh: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
):
    if kp_refresh:
        service.logout(kp_refresh)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    count = service.logout_all(current_user.key or "")
    _clear_refresh_cookie(response)
    return MessageResponse(message=f"Revoked {count} session(s).")


@router.post("/verify-email", response_model=UserProfileResponse)
def verify_email(
    body: VerifyEmailRequest,
    service: AuthService = Depends(get_auth_service),
):
    profile = service.verify_email(body.token)
    return UserProfileResponse(**profile.model_dump())


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(
    body: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
):
    service.request_password_reset(body.email)
    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    body: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
):
    service.reset_password(body.token, body.new_password)
    return MessageResponse(message="Password has been reset successfully.")


@router.get("/oauth/providers", response_model=list[OAuthProviderListItem])
def list_oauth_providers(
    oidc_repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    configs = oidc_repo.list_enabled()
    return [
        OAuthProviderListItem(slug=c.slug, display_name=c.display_name, icon_url=c.icon_url)
        for c in configs
    ]


@router.get("/oauth/{slug}")
def initiate_oauth(slug: str):
    """STUB: Initiates OAuth flow. Coming in follow-up."""
    return {"message": f"OAuth initiation for '{slug}' not yet implemented."}


@router.get("/oauth/{slug}/callback")
def oauth_callback(slug: str):
    """STUB: OAuth callback handler. Coming in follow-up."""
    return {"message": f"OAuth callback for '{slug}' not yet implemented."}
