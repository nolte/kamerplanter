"""Shared harness for the `/admin/oidc-providers` API tests (#1477, #1497).

Both suites that exercise this router — the GitHub scope gate and the
provider-type vocabulary — need the same four pieces: a stored configuration, a
repository double, a client with the platform-admin dependency overridden, and a
valid create body. They were written twice, and two copies of a double are two
places for a double to start accepting what the real thing rejects.

`stored_provider` constructs `OidcProviderConfig` DIRECTLY, exactly as
`repo.get_by_key` constructs it from a stored document. That is deliberate: it is
what makes a record carrying a pre-gate spelling representable at all, and it is
the reason the vocabulary lives on the request schemas rather than on the domain
model.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.oidc_providers.router import router as oidc_router
from app.common.auth import require_platform_admin
from app.common.dependencies import get_encryption_engine, get_oauth_engine, get_oidc_config_repo
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig

BASE = "/api/v1/admin/oidc-providers"

#: A discovery document with the three fields `POST /{key}/test` requires.
DISCOVERY = {
    "issuer": "https://idp.example",
    "authorization_endpoint": "https://idp.example/authorize",
    "token_endpoint": "https://idp.example/token",
}

#: Where `OAuthEngine.fetch_discovery_document` is patched by both suites.
DISCOVERY_TARGET = "app.domain.engines.oauth_engine.OAuthEngine.fetch_discovery_document"


def stored_provider(provider_type: str = "github", scopes: list[str] | None = None) -> OidcProviderConfig:
    """A configuration as the repository hands it back from a stored document."""
    return OidcProviderConfig(
        _key="cfg1",
        slug="gh",
        display_name="GitHub",
        provider_type=provider_type,
        issuer_url="https://github.com",
        client_id="cid",
        scopes=["openid", "email", "profile"] if scopes is None else scopes,
    )


def provider_repo(stored: OidcProviderConfig | None = None) -> MagicMock:
    """A repository double that records what the router would have written."""
    repo = MagicMock()
    repo.get_by_slug.return_value = None
    repo.get_by_key.return_value = stored
    repo.create.side_effect = lambda c: c.model_copy(update={"key": "cfg1"})
    repo.update.side_effect = lambda key, c: c
    return repo


def admin_client(repo: MagicMock) -> TestClient:
    """The router with a platform admin signed in and the real error handlers.

    The handlers matter: without them a `ValidationError` from the engine would
    surface as an unhandled exception instead of the 422 the gate promises.
    """
    app = FastAPI()
    app.include_router(oidc_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="user_admin")
    app.dependency_overrides[get_oidc_config_repo] = lambda: repo
    app.dependency_overrides[get_encryption_engine] = lambda: EncryptionEngine(Fernet.generate_key().decode())
    app.dependency_overrides[get_oauth_engine] = OAuthEngine
    return TestClient(app)


def create_body(**overrides) -> dict:
    """A body the GitHub scope gate (#1477) accepts, so a 422 is about the type."""
    body = {
        "slug": "gh",
        "display_name": "GitHub",
        "provider_type": "github",
        "issuer_url": "https://github.com",
        "client_id": "cid",
        "client_secret": "secret",
        "scopes": ["read:user", "user:email"],
    }
    body.update(overrides)
    return body
