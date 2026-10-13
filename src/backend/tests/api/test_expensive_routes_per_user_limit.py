"""#2109 — expensive authenticated write paths carry a per-user rate limit.

Through the production principal resolution: ``get_current_user`` runs for real
(only the auth provider is a fake), so the bucket key is read from the request
state the real dependency writes — not from a stand-in the test sets itself.
"""

from __future__ import annotations

import io

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image
from slowapi.errors import RateLimitExceeded

from app.api.v1.attachments.tenant_router import router as attachments_router
from app.api.v1.auth.router import limiter
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_attachment_service, get_auth_provider
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError, UnauthorizedError
from app.config.settings import Settings, settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.attachment_service import AttachmentService
from tests.api.test_attachments_router import _FakeRepo

TENANT_SLUG = "anna"


class _TokenAuth(IAuthProvider):
    """Maps a bearer token to a user; everything else is unauthenticated."""

    _USERS = {
        "token-anna": User(_key="user_anna", email="anna@example.org", display_name="Anna"),
        "token-ben": User(_key="user_ben", email="ben@example.org", display_name="Ben"),
    }

    def resolve_user(self, authorization: str | None, *, client_ip: str | None) -> User:
        user = self.resolve_user_optional(authorization, client_ip=client_ip)
        if user is None:
            raise UnauthorizedError("no token")
        return user

    def resolve_user_optional(self, authorization: str | None, *, client_ip: str | None) -> User | None:
        token = (authorization or "").removeprefix("Bearer ")
        return self._USERS.get(token)

    def is_authentication_required(self) -> bool:
        return True


def _tenant(user: User = Depends(get_current_user)) -> TenantContext:
    return TenantContext(
        tenant_key="tenant_anna", tenant_slug=TENANT_SLUG, user_key=user.key or "", role=TenantRole.LEAD
    )


def _jpeg(shade: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (shade, 120, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    import app.tasks.storage_tasks as storage_tasks
    from app.main import app as production_app

    monkeypatch.setattr(storage_tasks.generate_thumbnails, "delay", lambda *a, **k: None)
    adapter = LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://testserver/api/v1/attachments/token",
        signing_secret="api-test-secret",
        max_object_size_bytes=25 * 1024 * 1024,
    )
    service = AttachmentService(storage=adapter, attachment_repo=_FakeRepo(), settings=Settings())

    app = FastAPI()
    app.include_router(attachments_router, prefix="/api/v1/t/{tenant_slug}")
    app.state.limiter = limiter
    # The production 429 handler, as main.py registers it.
    app.add_exception_handler(RateLimitExceeded, production_app.exception_handlers[RateLimitExceeded])

    def _error(request: Request, exc: KamerplanterError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})

    app.add_exception_handler(KamerplanterError, _error)
    app.dependency_overrides[get_auth_provider] = _TokenAuth
    app.dependency_overrides[get_current_tenant] = _tenant
    app.dependency_overrides[get_attachment_service] = lambda: service
    return TestClient(app)


def _upload(client: TestClient, token: str, shade: int) -> int:
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/attachments",
        files={"file": ("p.jpg", _jpeg(shade), "image/jpeg")},
        data={"category": "diary"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.status_code


def test_the_31st_upload_in_a_minute_is_refused_with_retry_after(client: TestClient) -> None:
    budget = int(settings.rate_limit_upload.split("/")[0])
    assert budget == 30

    statuses = [_upload(client, "token-anna", shade) for shade in range(budget)]
    assert statuses == [201] * budget

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/attachments",
        files={"file": ("p.jpg", _jpeg(200), "image/jpeg")},
        data={"category": "diary"},
        headers={"Authorization": "Bearer token-anna"},
    )
    assert resp.status_code == 429
    assert 1 <= int(resp.headers["Retry-After"]) <= 60


def test_the_bucket_is_the_user_not_the_address(client: TestClient) -> None:
    for shade in range(30):
        assert _upload(client, "token-anna", shade) == 201
    assert _upload(client, "token-anna", 201) == 429

    # Same TestClient address, another account: its own budget.
    assert _upload(client, "token-ben", 202) == 201
