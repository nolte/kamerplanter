"""Service-token auth + startup fail-fast tests (AP-4, INF-S1/S4)."""

import pytest

from app import auth, main
from tests.conftest import TEST_SERVICE_TOKEN

_ASK_BODY = {"question": "How do I fix yellow leaves on my tomato plant?"}


# -- endpoint auth ---------------------------------------------------------


class TestServiceTokenAuth:
    def test_ask_rejects_missing_token(self, unauth_client):
        assert unauth_client.post("/ask", json=_ASK_BODY).status_code == 401

    def test_search_rejects_missing_token(self, unauth_client):
        assert unauth_client.get("/search", params={"q": "vpd"}).status_code == 401

    def test_ingest_rejects_missing_token(self, unauth_client):
        assert unauth_client.post("/ingest").status_code == 401

    def test_rejects_wrong_token(self, unauth_client):
        resp = unauth_client.post(
            "/ask",
            json=_ASK_BODY,
            headers={"Authorization": "Bearer not-the-token"},
        )
        assert resp.status_code == 401

    def test_rejects_malformed_header(self, unauth_client):
        resp = unauth_client.post(
            "/ask",
            json=_ASK_BODY,
            headers={"Authorization": TEST_SERVICE_TOKEN},  # missing "Bearer "
        )
        assert resp.status_code == 401

    def test_valid_token_passes_auth(self, unauth_client):
        # /classify needs no service singleton (uses a fresh PromptEngine), so a
        # 200 here proves the auth layer admitted the request.
        resp = unauth_client.post(
            "/classify",
            json={"question": "My leaves are turning yellow, what is wrong?"},
            headers={"Authorization": f"Bearer {TEST_SERVICE_TOKEN}"},
        )
        assert resp.status_code == 200
        assert "question_type" in resp.json()


class TestProbesStayPublic:
    def test_health_without_token(self, unauth_client):
        assert unauth_client.get("/health").status_code == 200


class TestFailClosedWhenUnconfigured:
    def test_returns_503_when_token_not_configured(self, unauth_client, monkeypatch):
        monkeypatch.setattr(main.settings, "internal_service_token", "")
        resp = unauth_client.post(
            "/ask",
            json=_ASK_BODY,
            headers={"Authorization": "Bearer anything"},
        )
        assert resp.status_code == 503


# -- startup fail-fast -----------------------------------------------------


class TestCheckInsecureConfig:
    def test_default_password_flagged(self, monkeypatch):
        monkeypatch.setattr(auth.settings, "vectordb_password", "changeme")
        monkeypatch.setattr(auth.settings, "internal_service_token", "set")
        assert "vectordb_password" in auth.check_insecure_config()

    def test_missing_token_flagged(self, monkeypatch):
        monkeypatch.setattr(auth.settings, "vectordb_password", "real-password")
        monkeypatch.setattr(auth.settings, "internal_service_token", "")
        assert "internal_service_token" in auth.check_insecure_config()

    def test_secure_config_is_empty(self, monkeypatch):
        monkeypatch.setattr(auth.settings, "vectordb_password", "real-password")
        monkeypatch.setattr(auth.settings, "internal_service_token", "a-real-token")
        assert auth.check_insecure_config() == []


class TestLifespanFailFast:
    async def test_lifespan_aborts_on_insecure_defaults(self, monkeypatch):
        # asyncio_mode=auto -> pytest-asyncio manages the loop; using async def
        # (not asyncio.run) avoids tearing down the shared event loop.
        monkeypatch.setattr(main.settings, "debug", False)
        monkeypatch.setattr(main.settings, "vectordb_password", "changeme")
        monkeypatch.setattr(main.settings, "internal_service_token", "")

        with pytest.raises(SystemExit):
            async with main.lifespan(main.app):
                pass  # pragma: no cover
