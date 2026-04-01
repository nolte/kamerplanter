"""Test fixtures for knowledge-service tests."""

import pytest

from app.prompt_engine import PromptEngine


@pytest.fixture
def prompt_engine() -> PromptEngine:
    """Provide a PromptEngine instance for tests."""
    return PromptEngine()
