"""Service-to-service authentication (AP-4, INF-S1/S2).

The knowledge-service is a cluster-internal M2M microservice (ClusterIP, not
publicly exposed). It authenticates callers with a static shared secret carried
in an ``Authorization: Bearer <token>`` header, mirroring the REQ-023 service
account model (API-key-only M2M access). Kubernetes liveness/readiness probes
stay auth-free so the container remains observable without the secret.
"""

import hmac

from fastapi import Header, HTTPException, Request, status

from app.config import settings

_BEARER_PREFIX = "Bearer "

# Probe endpoints stay auth-free so the kubelet can reach them without a secret.
_PUBLIC_PATHS = frozenset({"/health", "/ready"})


def check_insecure_config() -> list[str]:
    """Return the names of default/missing secrets that block a secure startup.

    Empty list => safe to start. Evaluated against the module-level ``settings``
    so it can be unit-tested by monkeypatching individual fields.
    """
    insecure: list[str] = []
    if settings.vectordb_password == "changeme":
        insecure.append("vectordb_password")
    if not settings.internal_service_token:
        insecure.append("internal_service_token")
    return insecure


def require_service_token(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    """Reject any non-probe request without a valid service token.

    Fail-closed: when no token is configured the endpoint is unavailable (503)
    rather than open. The comparison is constant-time to avoid timing oracles.
    """
    if request.url.path in _PUBLIC_PATHS:
        return

    expected = settings.internal_service_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service authentication is not configured.",
        )

    provided = ""
    if authorization and authorization.startswith(_BEARER_PREFIX):
        provided = authorization[len(_BEARER_PREFIX) :]
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token.",
        )
