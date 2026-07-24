from typing import Annotated

import structlog
from fastapi import APIRouter, Cookie, Depends, Path, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1.auth.csrf import set_csrf_cookie, verify_csrf
from app.api.v1.auth.schemas import (
    ApiKeyCreatedResponse,
    ApiKeyCreateRequest,
    ApiKeySummaryResponse,
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
from app.api.v1.mcp.deps import require_mcp_enabled
from app.common.auth import get_current_user, get_refresh_token_from_cookie
from app.common.dependencies import get_auth_service, get_mcp_authenticator, get_oidc_config_repo
from app.common.exceptions import (
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings
from app.core.permissions import list_mcp_permissions
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.mcp_server.auth import McpAuthenticator

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"], responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES})

# AP-7 (FE-S3): the frontend maps these codes to localised messages. The backend
# NEVER forwards a raw provider error string — only one of these fixed codes.
_OAUTH_ERROR_CODES = frozenset(
    {"access_denied", "invalid_state", "provider_error", "account_disabled"},
)


def _oauth_error_redirect(frontend_url: str, error_code: str) -> RedirectResponse:
    """Redirect to the frontend callback with a whitelisted error code (no token)."""
    code = error_code if error_code in _OAUTH_ERROR_CODES else "provider_error"
    return RedirectResponse(url=f"{frontend_url}/auth/callback?error={code}", status_code=302)


def _set_refresh_cookie(
    response: Response,
    raw_refresh_token: str,
    is_persistent: bool = False,
    max_age_days: int = 30,
) -> None:
    kwargs: dict = {
        "key": "kp_refresh",
        "value": raw_refresh_token,
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/api/v1/auth",
    }
    if is_persistent:
        kwargs["max_age"] = max_age_days * 86400
    # When not persistent, omit max_age → browser session cookie
    response.set_cookie(**kwargs)


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="kp_refresh", path="/api/v1/auth")


@router.post("/register", response_model=UserProfileResponse, status_code=201)
@limiter.limit(settings.rate_limit_auth)
def register(
    request: Request,
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new local account with email and password."""
    profile = service.register_local(body.email, body.password, body.display_name)
    return UserProfileResponse(**profile.model_dump())


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password, issuing access and refresh tokens."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    token_pair, raw_refresh, is_persistent = service.login_local(
        body.email,
        body.password,
        user_agent,
        ip_address,
        remember_me=body.remember_me,
    )
    _set_refresh_cookie(response, raw_refresh, is_persistent=is_persistent)
    set_csrf_cookie(response)
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
    """Rotate the refresh cookie and issue a fresh access token."""
    verify_csrf(request)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    token_pair, new_raw_refresh, is_persistent = service.refresh_tokens(kp_refresh, user_agent, ip_address)
    _set_refresh_cookie(response, new_raw_refresh, is_persistent=is_persistent)
    set_csrf_cookie(response)
    return TokenResponse(
        access_token=token_pair.access_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    request: Request,
    kp_refresh: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
):
    """Revoke the current refresh token and clear the refresh cookie."""
    verify_csrf(request)
    if kp_refresh:
        service.logout(kp_refresh)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Revoke all of the current user's active sessions."""
    verify_csrf(request)
    count = service.logout_all(current_user.key or "")
    _clear_refresh_cookie(response)
    return MessageResponse(message=f"Revoked {count} session(s).")


@router.post("/verify-email", response_model=UserProfileResponse)
def verify_email(
    body: VerifyEmailRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Verify a user's email address from a signed token."""
    profile = service.verify_email(body.token)
    return UserProfileResponse(**profile.model_dump())


@router.post("/password-reset/request", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_auth)
def request_password_reset(
    request: Request,
    body: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Send a password-reset link if an account exists for the email."""
    service.request_password_reset(body.email)
    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_auth)
def confirm_password_reset(
    request: Request,
    body: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service),
):
    """Set a new password from a valid password-reset token."""
    service.reset_password(body.token, body.new_password)
    return MessageResponse(message="Password has been reset successfully.")


# ── OAuth/OIDC ─────────────────────────────────────────────────────


@router.get("/oauth/providers", response_model=list[OAuthProviderListItem])
def list_oauth_providers(
    oidc_repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    """List the enabled OAuth/OIDC providers offered for login."""
    configs = oidc_repo.list_enabled()
    return [OAuthProviderListItem(slug=c.slug, display_name=c.display_name, icon_url=c.icon_url) for c in configs]


@router.get("/oauth/{slug}")
def initiate_oauth(
    slug: Annotated[str, Path(description="Slug of the configured OAuth/OIDC provider.")],
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """302 Redirect to the OAuth provider's authorization URL."""
    # Build callback URL from request base
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v1/auth/oauth/{slug}/callback"
    oauth_redirect = service.initiate_oauth(slug, redirect_uri)
    return RedirectResponse(url=oauth_redirect.authorization_url, status_code=302)


@router.get("/oauth/{slug}/callback")
def oauth_callback(
    slug: Annotated[str, Path(description="Slug of the configured OAuth/OIDC provider.")],
    request: Request,
    response: Response,
    code: str | None = Query(default=None, description="Authorization code returned by the provider."),
    state: str | None = Query(default=None, description="Opaque anti-CSRF state echoed by the provider."),
    error: str | None = Query(default=None, description="Error code returned when the provider denied the request."),
    service: AuthService = Depends(get_auth_service),
):
    """OAuth callback: exchange code, set the refresh cookie, redirect to frontend.

    AP-7 (FE-S1): the access token is delivered exclusively through the HttpOnly
    refresh cookie. It is NEVER placed in the redirect URL (neither query nor
    fragment), so it cannot leak via browser history, Referer headers or proxy
    logs. The frontend completes the login through the cookie-based refresh flow.
    """
    frontend_url = service._frontend_url

    # Provider-side denial (e.g. the user cancelled) arrives with an `error`
    # param and without a code — or a malformed callback lacks code/state.
    if error is not None:
        return _oauth_error_redirect(frontend_url, "access_denied")
    if not code or not state:
        return _oauth_error_redirect(frontend_url, "provider_error")

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    try:
        _token_pair, raw_refresh, is_persistent = service.complete_oauth(
            slug,
            code,
            state,
            user_agent,
            ip_address,
        )
    except InvalidTokenError:
        return _oauth_error_redirect(frontend_url, "invalid_state")
    except UnauthorizedError:
        return _oauth_error_redirect(frontend_url, "account_disabled")
    except (NotFoundError, ValidationError) as exc:
        # `as exc` keeps ruff-format from stripping the parens (which would turn
        # this into the `except A, B:` Python-2 syntax error).
        logger.info("oauth_callback_provider_error", provider=slug, error=str(exc))
        return _oauth_error_redirect(frontend_url, "provider_error")
    except Exception:  # noqa: BLE001 — never surface a JSON 500 to the browser
        logger.exception("oauth_callback_failed", provider=slug)
        return _oauth_error_redirect(frontend_url, "provider_error")

    redirect = RedirectResponse(url=f"{frontend_url}/auth/callback", status_code=302)
    _set_refresh_cookie(redirect, raw_refresh, is_persistent=is_persistent)
    set_csrf_cookie(redirect)
    return redirect


# ── M2M API Keys ───────────────────────────────────────────────────


@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=201)
def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Create a new M2M API key for the current user."""
    created = service.create_api_key(current_user.key or "", body.label, body.tenant_scope)
    return ApiKeyCreatedResponse(**created.model_dump())


@router.get("/api-keys", response_model=list[ApiKeySummaryResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """List the current user's M2M API keys (metadata only)."""
    keys = service.list_api_keys(current_user.key or "")
    return [ApiKeySummaryResponse(**k.model_dump()) for k in keys]


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
def revoke_api_key(
    key_id: Annotated[str, Path(description="Identifier of the API key to revoke.")],
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Revoke one of the current user's M2M API keys."""
    service.revoke_api_key(current_user.key or "", key_id)
    return MessageResponse(message="API key revoked.")


# ── REQ-033 §5 — service-account API-key validation (M2M) ──────────────
class ServiceAccountValidateRequest(BaseModel):
    """A raw service-account API key to validate (never logged)."""

    api_key: str


class ServiceAccountValidateResponse(BaseModel):
    """Resolved service-account context for an MCP/M2M client (§4.3, §4.4)."""

    service_account_key: str
    display_name: str
    tenant_key: str
    tenant_slug: str
    role: str
    mcp_permissions: list[str]


@router.post("/service-accounts/validate", response_model=ServiceAccountValidateResponse)
@limiter.limit(settings.rate_limit_auth)
def validate_service_account(
    request: Request,
    body: ServiceAccountValidateRequest,
    _enabled: None = Depends(require_mcp_enabled),
    authenticator: McpAuthenticator = Depends(get_mcp_authenticator),
):
    """Validate a service-account API key and return its tenant + MCP grants (§5).

    The M2M validation entrypoint an external MCP-server process (future
    follow-up) calls to resolve a key into a bound service account. The raw key
    is hashed inside the authenticator and never persisted or logged (AC-S2).

    Hardened per the REQ-033 security review (SEC-003): gated behind the MCP
    enable flag (``require_mcp_enabled`` → 404 when MCP is off), per-IP rate
    limited (reusing the auth limiter) and the valid-non-service case is
    collapsed into the SAME generic 401 as an invalid/revoked key so the
    endpoint can never be used as an oracle to prove a valid non-service key
    exists (``mask_non_service=True``). The client IP is resolved so the key's
    ``ip_allowlist`` (SEC-004) is enforced here too.
    """

    principal = authenticator.authenticate(
        body.api_key,
        client_ip=resolve_client_ip(request),
        mask_non_service=True,
    )
    return ServiceAccountValidateResponse(
        service_account_key=principal.service_account_key,
        display_name=principal.display_name,
        tenant_key=principal.tenant_key,
        tenant_slug=principal.tenant_slug,
        role=principal.role.value,
        mcp_permissions=[p.value for p in list_mcp_permissions(principal.role)],
    )
