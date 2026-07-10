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
        ("http://creativecommons.org/licenses/by-nd/4.0/", ReferenceLicense.CC_BY_ND),
        ("CC_BY_ND_4_0", ReferenceLicense.CC_BY_ND),
        # Compound NC variants must NOT collapse to CC-BY-NC / CC-BY.
        ("http://creativecommons.org/licenses/by-nc-sa/4.0/", ReferenceLicense.CC_BY_NC_SA),
        ("CC_BY_NC_SA_4_0", ReferenceLicense.CC_BY_NC_SA),
        ("http://creativecommons.org/licenses/by-nc-nd/4.0/", ReferenceLicense.CC_BY_NC_ND),
        ("CC_BY_NC_ND_4_0", ReferenceLicense.CC_BY_NC_ND),
        ("", ReferenceLicense.UNKNOWN),
        (None, ReferenceLicense.UNKNOWN),
        ("All rights reserved", ReferenceLicense.UNKNOWN),
    ],
)
def test_normalize_license(raw, expected):
    assert normalize_license(raw) == expected


def test_only_cc0_and_ccby_acceptable():
    # Default (commercial-safe) stance: CC0/CC-BY only.
    assert is_acceptable(ReferenceLicense.CC0)
    assert is_acceptable(ReferenceLicense.CC_BY)
    assert not is_acceptable(ReferenceLicense.CC_BY_NC)
    assert not is_acceptable(ReferenceLicense.CC_BY_SA)
    assert not is_acceptable(ReferenceLicense.UNKNOWN)


def test_ccbync_acceptable_only_with_noncommercial_flag():
    # CC-BY-NC is gated behind the non-commercial flag.
    assert not is_acceptable(ReferenceLicense.CC_BY_NC, allow_noncommercial=False)
    assert is_acceptable(ReferenceLicense.CC_BY_NC, allow_noncommercial=True)
    # CC0/CC-BY stay acceptable regardless of the flag.
    assert is_acceptable(ReferenceLicense.CC0, allow_noncommercial=True)
    assert is_acceptable(ReferenceLicense.CC_BY, allow_noncommercial=True)


def test_copyleft_and_noderivatives_rejected_even_noncommercially():
    # -SA / -ND obligations persist even non-commercially → never acceptable.
    for blocked in (
        ReferenceLicense.CC_BY_SA,
        ReferenceLicense.CC_BY_ND,
        ReferenceLicense.CC_BY_NC_SA,
        ReferenceLicense.CC_BY_NC_ND,
        ReferenceLicense.UNKNOWN,
    ):
        assert not is_acceptable(blocked, allow_noncommercial=True)
        assert not is_acceptable(blocked, allow_noncommercial=False)


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


def _make_service(candidates, *, image_bytes=None, wikimedia_candidates=None):
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

    wikimedia = None
    if wikimedia_candidates is not None:
        wikimedia = MagicMock()
        wikimedia.list_media.return_value = wikimedia_candidates
        wikimedia.download.return_value = image_bytes if image_bytes is not None else _image()

    service = ReferenceImageService(gbif, media, inference, repo, wikimedia_client=wikimedia)
    return service, inference, repo, wikimedia


def test_szenario_a3_license_filter(monkeypatch):
    # 10 CC0 + 12 CC-BY accepted, 8 CC-BY-NC rejected.
    candidates = _candidates(10, 12, 8)
    service, inference, repo, _ = _make_service(candidates)

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
    service, inference, _, _ = _make_service(candidates, image_bytes=_image(100, 100))

    result = service.acquire_for_species("species_x", "Ficus lyrata")

    assert result.rejected_quality == 6
    assert result.accepted == 0
    inference.upsert_reference.assert_not_called()


def test_below_minimum_marked_not_usable():
    # 3 accepted < min_usable (5) → not recognizable.
    candidates = _candidates(3, 0, 0)
    service, _, _, _ = _make_service(candidates)

    result = service.acquire_for_species("species_rare", "Alocasia zebrina")

    assert result.accepted == 3
    assert result.usable_for_recognition is False


def test_no_taxon_match_yields_empty_job():
    service, inference, repo, _ = _make_service(_candidates(5, 5, 0))
    service._gbif.match_species.return_value = None

    result = service.acquire_for_species("species_unknown", "Nonexistent plantus")

    # GBIF has no taxon, but with no Wikimedia client there are no candidates.
    assert result.candidates_found == 0
    assert result.accepted == 0
    assert result.usable_for_recognition is False
    inference.embed.assert_not_called()
    repo.upsert.assert_called_once()


# ── Wikimedia Commons as a second source ────────────────────────────────


def _wikimedia_candidates(n: int) -> list[MediaCandidate]:
    return [
        MediaCandidate(url=f"http://commons/wiki_{i}.jpg", license=ReferenceLicense.CC0, source="wikimedia")
        for i in range(n)
    ]


def test_wikimedia_augments_gbif():
    # GBIF: 4 CC-BY, Wikimedia: 3 CC0 → 7 accepted from both sources.
    service, inference, _, wikimedia = _make_service(
        _candidates(0, 4, 0), wikimedia_candidates=_wikimedia_candidates(3)
    )

    result = service.acquire_for_species("species_monstera", "Monstera deliciosa")

    assert result.candidates_found == 7
    assert result.accepted == 7
    assert result.license_breakdown == {"CC-BY": 4, "CC0": 3}
    wikimedia.list_media.assert_called_once()
    # Wikimedia images are downloaded via the Wikimedia client (its User-Agent).
    assert wikimedia.download.call_count == 3


def test_dedupe_across_sources():
    shared = [MediaCandidate(url="http://shared/img.jpg", license=ReferenceLicense.CC0, source="gbif")]
    wiki_shared = [MediaCandidate(url="http://shared/img.jpg", license=ReferenceLicense.CC0, source="wikimedia")]
    service, inference, _, _ = _make_service(shared, wikimedia_candidates=wiki_shared)

    result = service.acquire_for_species("species_x", "Ficus lyrata")

    # Same URL from both sources is processed only once.
    assert result.candidates_found == 1
    assert result.accepted == 1


def test_sets_representative_image_on_species():
    # The first accepted image is promoted to the species' representative thumbnail.
    service, _, _, _ = _make_service(_candidates(0, 3, 0))
    species_repo = MagicMock()
    service._species_repo = species_repo

    result = service.acquire_for_species("species_monstera", "Monstera deliciosa")

    assert result.representative_url is not None
    species_repo.set_representative_image.assert_called_once()
    kwargs = species_repo.set_representative_image.call_args.kwargs
    assert kwargs["url"] == result.representative_url
    assert kwargs["license"] == "CC-BY"


def test_no_representative_image_when_nothing_accepted():
    service, _, _, _ = _make_service(_candidates(0, 0, 4))  # all CC-BY-NC → rejected
    species_repo = MagicMock()
    service._species_repo = species_repo

    service.acquire_for_species("species_x", "Ficus lyrata")

    species_repo.set_representative_image.assert_not_called()


def test_wikimedia_runs_without_gbif_taxon():
    service, inference, _, wikimedia = _make_service(
        _candidates(0, 0, 0), wikimedia_candidates=_wikimedia_candidates(6)
    )
    service._gbif.match_species.return_value = None  # GBIF finds nothing

    result = service.acquire_for_species("species_rare", "Alocasia zebrina")

    # Wikimedia only needs the scientific name, so it still contributes.
    assert result.candidates_found == 6
    assert result.accepted == 6
    assert result.usable_for_recognition is True
    wikimedia.list_media.assert_called_once()


# ── issue #447 — reuse an identification photo as a reference ────────────


def test_contribute_user_reference_embeds_and_upserts():
    service, inference, _, _ = _make_service(_candidates(0, 0, 0))

    result = service.contribute_user_reference("species_monstera", "Monstera deliciosa", _image())

    inference.embed.assert_called_once()
    inference.upsert_reference.assert_called_once()
    _, kwargs = inference.upsert_reference.call_args
    assert kwargs["species_key"] == "species_monstera"
    assert kwargs["scientific_name"] == "Monstera deliciosa"
    # User contributions are tagged so admin curation can exclude them later.
    assert kwargs["source"] == "user_contribution"
    # Only the embedding is indexed — no original image is forwarded/persisted.
    assert kwargs["embedding"] == [0.1] * 384
    assert "image_data" not in kwargs
    assert result == {"status": "ok"}
