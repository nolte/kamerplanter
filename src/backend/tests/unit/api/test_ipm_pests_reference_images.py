"""REQ-044 — pest list/detail expose ``has_reference_images``.

The IPM router enriches every :class:`PestResponse` with whether the pest's
``detection_slug`` has usable few-shot reference images indexed. The coverage is
loaded in a SINGLE bundled call to the inference client (no N+1) and is gated by
the ``pest_detection_enabled`` master switch (Default-Privacy).

House style: the router functions are invoked directly with a fake service; the
inference client and settings are monkeypatched on the router module.
"""

from __future__ import annotations

import pytest

from app.api.v1.ipm import router as ipm_router
from app.domain.models.ipm import Pest


class _FakeIpmService:
    def __init__(self, pests: list[Pest]) -> None:
        self._pests = pests

    def list_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]:
        return self._pests, len(self._pests)

    def get_pest(self, key: str) -> Pest:
        for pest in self._pests:
            if pest.key == key:
                return pest
        raise AssertionError(f"unexpected key {key}")


class _FakeInferenceClient:
    """Returns a fixed coverage payload and records whether it was called."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls = 0

    def coverage(self) -> list[dict]:
        self.calls += 1
        return self._rows


def _pest(key: str, *, detection_slug: str | None) -> Pest:
    return Pest(
        _key=key,
        scientific_name="Tetranychus urticae",
        common_name="Spider mite",
        detection_slug=detection_slug,
    )


@pytest.fixture
def patched(monkeypatch):
    """Patch the inference client + enable the feature on the router module."""

    rows = [
        {"label": "spider_mite", "total": 30, "active": 30},
        {"label": "aphid", "total": 5, "active": 0},  # indexed but all deselected
    ]
    client = _FakeInferenceClient(rows)
    monkeypatch.setattr(ipm_router.settings, "pest_detection_enabled", True)
    monkeypatch.setattr(ipm_router, "get_pest_inference_client", lambda: client)
    return client


def test_list_pests_marks_pest_with_reference_images(patched):
    service = _FakeIpmService(
        [
            _pest("p_mite", detection_slug="spider_mite"),
            _pest("p_aphid", detection_slug="aphid"),
            _pest("p_none", detection_slug=None),
            _pest("p_unmapped", detection_slug="nonexistent_slug"),
        ]
    )

    responses = ipm_router.list_pests(offset=0, limit=50, service=service)

    by_key = {r.key: r for r in responses}
    # 30 active prototypes → marked, count surfaced.
    assert by_key["p_mite"].has_reference_images is True
    assert by_key["p_mite"].reference_image_count == 30
    # Indexed but all prototypes deselected (active=0) → NOT usable.
    assert by_key["p_aphid"].has_reference_images is False
    assert by_key["p_aphid"].reference_image_count == 0
    # No detection_slug → never marked.
    assert by_key["p_none"].has_reference_images is False
    # Slug with no coverage row → not marked.
    assert by_key["p_unmapped"].has_reference_images is False
    # Coverage loaded exactly once for the whole list (no N+1).
    assert patched.calls == 1


def test_list_pests_no_marker_when_feature_disabled(monkeypatch):
    client = _FakeInferenceClient([{"label": "spider_mite", "total": 30, "active": 30}])
    monkeypatch.setattr(ipm_router.settings, "pest_detection_enabled", False)
    monkeypatch.setattr(ipm_router, "get_pest_inference_client", lambda: client)
    service = _FakeIpmService([_pest("p_mite", detection_slug="spider_mite")])

    responses = ipm_router.list_pests(offset=0, limit=50, service=service)

    assert responses[0].has_reference_images is False
    assert responses[0].reference_image_count == 0
    # Disabled feature must never reach out to the inference service.
    assert client.calls == 0


def test_get_pest_marks_single_pest(patched):
    service = _FakeIpmService([_pest("p_mite", detection_slug="spider_mite")])

    response = ipm_router.get_pest(key="p_mite", service=service)

    assert response.has_reference_images is True
    assert response.reference_image_count == 30
