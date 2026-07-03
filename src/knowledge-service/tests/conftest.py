"""Test fixtures for knowledge-service tests."""

import pytest

from app.prompt_engine import PromptEngine

# Shared service token used across the auth tests (AP-4, INF-S1).
TEST_SERVICE_TOKEN = "test-service-token"


@pytest.fixture
def prompt_engine() -> PromptEngine:
    """Provide a PromptEngine instance for tests."""
    return PromptEngine()


class _FakeConn:
    """Stand-in for VectorDbConnection (always connected)."""

    def is_connected(self) -> bool:
        return True


@pytest.fixture
def unauth_client(monkeypatch):
    """A TestClient with a configured service token but NO Authorization header.

    The real lifespan (pgvector connect + component build) is skipped because
    the TestClient is used without its context-manager form. A fake vectordb
    connection keeps /health responsive. Used by the auth tests to assert
    protected endpoints reject unauthenticated callers.
    """
    from fastapi.testclient import TestClient

    from app import main

    monkeypatch.setattr(main, "_vec_conn", _FakeConn())
    monkeypatch.setattr(main.settings, "internal_service_token", TEST_SERVICE_TOKEN)
    return TestClient(main.app)
