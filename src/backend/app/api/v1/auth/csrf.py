"""CSRF Double-Submit Cookie pattern (SEC-K-004).

Sets a non-HttpOnly csrf_token cookie that the frontend reads and sends
back as the X-CSRF-Token header. Verified on state-changing endpoints
that use cookie-based auth (refresh, logout, logout-all).
"""

import hmac
import secrets
from typing import TYPE_CHECKING

from app.common.exceptions import ForbiddenError

if TYPE_CHECKING:
    from fastapi import Request, Response

_CSRF_COOKIE = "csrf_token"
_CSRF_HEADER = "x-csrf-token"


def set_csrf_cookie(response: Response) -> str:
    """Generate and set a CSRF token cookie. Returns the token."""
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=token,
        httponly=False,  # Frontend must read this
        secure=True,
        samesite="lax",
        path="/",
    )
    return token


def verify_csrf(request: Request) -> None:
    """Verify CSRF double-submit: cookie value must match header value."""
    cookie_token = request.cookies.get(_CSRF_COOKIE)
    header_token = request.headers.get(_CSRF_HEADER)

    if not cookie_token or not header_token:
        raise ForbiddenError("Missing CSRF token.")

    if not hmac.compare_digest(cookie_token, header_token):
        raise ForbiddenError("CSRF token mismatch.")
