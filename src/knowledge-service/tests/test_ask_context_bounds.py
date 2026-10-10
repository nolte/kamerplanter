"""SEC-002 (#2175, defence in depth): ``/ask`` bounds the plant context like the question.

The context values are rendered into the same LLM prompt as the question. The
backend's ``KnowledgeAskRequest`` bounds them; this service bounds them again, so
a caller holding the service token cannot lift the question's 2 000-character
limit through the context. A refused body never reaches ``KnowledgeService.ask``.
"""

from unittest.mock import MagicMock

import pytest

from app import main
from tests.conftest import TEST_SERVICE_TOKEN

_HEADERS = {"Authorization": f"Bearer {TEST_SERVICE_TOKEN}"}


@pytest.fixture
def service(monkeypatch) -> MagicMock:
    double = MagicMock()
    double.ask.return_value = MagicMock(answer="a", question_type="factual", model="m", usage={}, sources=[])
    monkeypatch.setattr(main, "_service", double)
    return double


@pytest.mark.parametrize(
    ("field", "value"),
    [("species", "x" * 10_000), ("phase", "x" * 101), ("substrate", "x" * 101), ("ec", 21), ("ec", -1), ("ph", 14.1)],
    ids=["species-10k", "phase-101", "substrate-101", "ec-21", "ec-negative", "ph-14.1"],
)
def test_an_unbounded_context_value_is_refused(unauth_client, service: MagicMock, field: str, value) -> None:
    resp = unauth_client.post("/ask", json={"question": "Why yellow?", "context": {field: value}}, headers=_HEADERS)

    assert resp.status_code == 422
    service.ask.assert_not_called()


def test_a_bounded_context_reaches_the_service(unauth_client, service: MagicMock) -> None:
    """The control — the bounds refuse the oversize body, not every body."""
    context = {"species": "x" * 100, "phase": "flowering", "substrate": "coco", "ec": 20, "ph": 0}

    resp = unauth_client.post("/ask", json={"question": "Why yellow?", "context": context}, headers=_HEADERS)

    assert resp.status_code == 200, resp.text
    service.ask.assert_called_once()
