"""Unit tests for REQ-029-A §4 reference-image acquisition (WS-4).

Covers license normalisation/filtering and the acquisition pipeline incl.
Szenario A3 (license filter) and the "no original image persisted" invariant.
"""

import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.domain.models.reference_image import MediaCandidate, ReferenceLicense
from app.domain.services.reference_image_license import is_acceptable, normalize_license
from app.domain.services.reference_image_service import ReferenceImageService

# ── License normalisation ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://creativecommons.org/publicdomain/zero/1.0/legalcode", ReferenceLicense.CC0),
        ("CC0_1_0", ReferenceLicense.CC0),
        ("http://creativecommons.org/licenses/by/4.0/", ReferenceLicense.CC_BY),
        ("CC_BY_4_0", ReferenceLicense.CC_BY),
        ("http://creativecommons.org/licenses/by-nc/4.0/", ReferenceLicense.CC_BY_NC),
        ("CC_BY_NC_4_0", ReferenceLicense.CC_BY_NC),
        ("http://creativecommons.org/licenses/by-sa/4.0/", ReferenceLicense.CC_BY_SA),
        ("CC_BY_SA_4_0", ReferenceLicense.CC_BY_SA),
        ("", ReferenceLicense.UNKNOWN),
        (None, ReferenceLicense.UNKNOWN),
        ("All rights reserved", ReferenceLicense.UNKNOWN),
    ],
)
def test_normalize_license(raw, expected):
    assert normalize_license(raw) == expected


def test_only_cc0_and_ccby_acceptable():
    assert is_acceptable(ReferenceLicense.CC0)
    assert is_acceptable(ReferenceLicense.CC_BY)
    assert not is_acceptable(ReferenceLicense.CC_BY_NC)
    assert not is_acceptable(ReferenceLicense.CC_BY_SA)
    assert not is_acceptable(ReferenceLicense.UNKNOWN)


# ── Acquisition pipeline ────────────────────────────────────────────────


def _image(width: int = 300, height: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (0, 120, 0)).save(buf, format="JPEG")
    return buf.getvalue()


def _candidates(n_cc0: int, n_ccby: int, n_ccbync: int) -> list[MediaCandidate]:
    out: list[MediaCandidate] = []
    for i in range(n_cc0):
        out.append(MediaCandidate(url=f"http://x/cc0_{i}.jpg", license=ReferenceLicense.CC0))
    for i in range(n_ccby):
        out.append(MediaCandidate(url=f"http://x/by_{i}.jpg", license=ReferenceLicense.CC_BY))
    for i in range(n_ccbync):
        out.append(MediaCandidate(url=f"http://x/nc_{i}.jpg", license=ReferenceLicense.CC_BY_NC))
    return out


def _make_service(candidates, *, image_bytes=None, min_usable=5):
    gbif = MagicMock()
    gbif.match_species.return_value = SimpleNamespace(usage_key=4711)

    media = MagicMock()
    media.list_media.return_value = candidates
    media.download.return_value = image_bytes if image_bytes is not None else _image()

    inference = MagicMock()
    inference.embed.return_value = [0.1] * 384
    inference.upsert_reference.return_value = {"status": "ok"}

    repo = MagicMock()
    repo.upsert.side_effect = lambda job: job

    service = ReferenceImageService(gbif, media, inference, repo)
    return service, inference, repo


def test_szenario_a3_license_filter(monkeypatch):
    # 10 CC0 + 12 CC-BY accepted, 8 CC-BY-NC rejected.
    candidates = _candidates(10, 12, 8)
    service, inference, repo = _make_service(candidates)

    result = service.acquire_for_species("species_monstera", "Monstera deliciosa")

    assert result.candidates_found == 30
    assert result.accepted == 22
    assert result.rejected_license == 8
    assert result.license_breakdown == {"CC0": 10, "CC-BY": 12}
    assert result.usable_for_recognition is True
    # 22 embeddings indexed, only vector + provenance — never the raw image.
    assert inference.upsert_reference.call_count == 22
    for call in inference.upsert_reference.call_args_list:
        assert "embedding" in call.kwargs
        assert "image_data" not in call.kwargs


def test_low_resolution_rejected_as_quality():
    candidates = _candidates(0, 6, 0)
    service, inference, _ = _make_service(candidates, image_bytes=_image(100, 100))

    result = service.acquire_for_species("species_x", "Ficus lyrata")

    assert result.rejected_quality == 6
    assert result.accepted == 0
    inference.upsert_reference.assert_not_called()


def test_below_minimum_marked_not_usable():
    # 3 accepted < min_usable (5) → not recognizable.
    candidates = _candidates(3, 0, 0)
    service, _, _ = _make_service(candidates)

    result = service.acquire_for_species("species_rare", "Alocasia zebrina")

    assert result.accepted == 3
    assert result.usable_for_recognition is False


def test_no_taxon_match_yields_empty_job():
    service, inference, repo = _make_service(_candidates(5, 5, 0))
    service._gbif.match_species.return_value = None

    result = service.acquire_for_species("species_unknown", "Nonexistent plantus")

    assert result.candidates_found == 0
    assert result.accepted == 0
    assert result.usable_for_recognition is False
    inference.embed.assert_not_called()
    repo.upsert.assert_called_once()
