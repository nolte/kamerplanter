"""REQ-044 WP-3 — dataset acquisition: license filter, quality gate, indexing.

Covers the multi-source orchestration (GBIF + iNaturalist + iDigBio), per-source
de-duplication, the CC-BY-NC non-commercial gate, attribution enforcement and
the quality gate. All HTTP is mocked via fake sources — no network calls.
"""

import io

from PIL import Image

from app.domain.models.pest_taxonomy import PestTaxon, get_taxon
from app.domain.models.reference_image import MediaCandidate, ReferenceLicense
from app.domain.services.pest_dataset_acquisition import PestDatasetAcquisitionService


def _jpeg(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 120, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _FakeSource:
    """A fake :class:`PestMediaSource` returning canned candidates/images."""

    def __init__(self, source_key, candidates, images) -> None:
        self.source_key = source_key
        self._candidates = candidates
        self._images = images
        self.last_taxon: PestTaxon | None = None

    def list_media(self, taxon, *, limit=40):
        self.last_taxon = taxon
        return self._candidates[:limit]

    def download(self, url):
        return self._images[url]

    def close(self) -> None:
        return None


class _FailingSource:
    """A source whose list_media raises — must be skipped, not fatal."""

    source_key = "boom"

    def list_media(self, taxon, *, limit=40):
        raise RuntimeError("source unavailable")

    def download(self, url):  # pragma: no cover - never reached
        raise RuntimeError("source unavailable")

    def close(self) -> None:
        return None


class _FakeInference:
    def __init__(self) -> None:
        self.indexed: list[dict] = []

    def upsert_prototype(self, image, **kwargs):
        self.indexed.append(kwargs)
        return {"status": "ok"}


def _candidate(url, license_value, rid, *, source="gbif", attribution="A. Photographer"):
    return MediaCandidate(url=url, license=license_value, source=source, source_record_id=rid, attribution=attribution)


def _service(sources, inference, *, allow_noncommercial=False):
    return PestDatasetAcquisitionService(sources, inference, allow_noncommercial=allow_noncommercial)


class TestAcquireForClass:
    def test_only_cc0_and_ccby_indexed_with_manifest(self) -> None:
        good = _jpeg(400, 400)
        candidates = [
            _candidate("u1", ReferenceLicense.CC0, "r1"),
            _candidate("u2", ReferenceLicense.CC_BY_NC, "r2"),  # rejected (NC off)
            _candidate("u3", ReferenceLicense.CC_BY, "r3"),
            _candidate("u4", ReferenceLicense.UNKNOWN, "r4"),  # rejected (license)
        ]
        images = {"u1": good, "u3": good}
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, images)], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 2
        assert summary["rejected_license"] == 2
        assert len(inference.indexed) == 2
        labels = {row["label"] for row in inference.indexed}
        assert labels == {"spider_mite"}
        assert inference.indexed[0]["source_url"] in {"u1", "u3"}
        assert inference.indexed[0]["attribution"] == "A. Photographer"
        assert len(summary["manifest"]) == 2

    def test_too_small_image_rejected_on_quality(self) -> None:
        candidates = [_candidate("u1", ReferenceLicense.CC0, "r1")]
        images = {"u1": _jpeg(100, 100)}  # below min dimension
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, images)], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 0
        assert summary["rejected_quality"] == 1
        assert inference.indexed == []

    def test_ccby_without_attribution_rejected_cc0_kept(self) -> None:
        good = _jpeg(400, 400)
        candidates = [
            MediaCandidate(
                url="u1", license=ReferenceLicense.CC_BY, source="gbif", source_record_id="r1", attribution=None
            ),
            MediaCandidate(
                url="u2", license=ReferenceLicense.CC0, source="gbif", source_record_id="r2", attribution=None
            ),
        ]
        images = {"u1": good, "u2": good}
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, images)], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        # CC-BY without attribution dropped; CC0 without attribution is fine.
        assert summary["accepted"] == 1
        assert summary["rejected_attribution"] == 1
        assert inference.indexed[0]["license"] == "CC0"

    def test_beneficial_class_carries_category(self) -> None:
        candidates = [_candidate("u1", ReferenceLicense.CC0, "r1")]
        images = {"u1": _jpeg(400, 400)}
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, images)], inference)

        svc.acquire_for_class(get_taxon("ladybird"))

        assert inference.indexed[0]["category"] == "beneficial"


class TestNonCommercialGate:
    def test_ccbync_rejected_when_flag_off(self) -> None:
        good = _jpeg(400, 400)
        candidates = [_candidate("u1", ReferenceLicense.CC_BY_NC, "r1")]
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, {"u1": good})], inference, allow_noncommercial=False)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 0
        assert summary["rejected_license"] == 1

    def test_ccbync_accepted_with_attribution_when_flag_on(self) -> None:
        good = _jpeg(400, 400)
        candidates = [_candidate("u1", ReferenceLicense.CC_BY_NC, "r1")]
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, {"u1": good})], inference, allow_noncommercial=True)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 1
        assert inference.indexed[0]["license"] == "CC-BY-NC"

    def test_ccbync_requires_attribution_even_with_flag(self) -> None:
        good = _jpeg(400, 400)
        candidates = [_candidate("u1", ReferenceLicense.CC_BY_NC, "r1", attribution=None)]
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, {"u1": good})], inference, allow_noncommercial=True)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 0
        assert summary["rejected_attribution"] == 1

    def test_share_alike_rejected_even_non_commercially(self) -> None:
        good = _jpeg(400, 400)
        candidates = [
            _candidate("u1", ReferenceLicense.CC_BY_SA, "r1"),
            _candidate("u2", ReferenceLicense.CC_BY_NC_SA, "r2"),
            _candidate("u3", ReferenceLicense.CC_BY_ND, "r3"),
        ]
        images = {"u1": good, "u2": good, "u3": good}
        inference = _FakeInference()
        svc = _service([_FakeSource("gbif", candidates, images)], inference, allow_noncommercial=True)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 0
        assert summary["rejected_license"] == 3


class TestMultiSourceOrchestration:
    def test_candidates_collected_from_all_sources(self) -> None:
        good = _jpeg(400, 400)
        gbif = _FakeSource("gbif", [_candidate("g1", ReferenceLicense.CC0, "r1", source="gbif")], {"g1": good})
        inat = _FakeSource(
            "inaturalist",
            [_candidate("i1", ReferenceLicense.CC_BY, "r2", source="inaturalist")],
            {"i1": good},
        )
        inference = _FakeInference()
        svc = _service([gbif, inat], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["candidates_found"] == 2
        assert summary["accepted"] == 2
        sources = {row["source"] for row in inference.indexed}
        assert sources == {"gbif", "inaturalist"}

    def test_dedup_same_record_across_sources(self) -> None:
        good = _jpeg(400, 400)
        # Same upstream record id from two sources → counted once.
        gbif = _FakeSource("gbif", [_candidate("g1", ReferenceLicense.CC0, "shared", source="gbif")], {"g1": good})
        inat = _FakeSource(
            "inaturalist",
            [_candidate("i1", ReferenceLicense.CC0, "shared", source="gbif")],
            {"i1": good},
        )
        inference = _FakeInference()
        svc = _service([gbif, inat], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["candidates_found"] == 1
        assert summary["accepted"] == 1

    def test_dedup_same_url_without_record_id(self) -> None:
        good = _jpeg(400, 400)
        c1 = MediaCandidate(url="http://x/same.jpg", license=ReferenceLicense.CC0, source="gbif")
        c2 = MediaCandidate(url="http://x/same.jpg", license=ReferenceLicense.CC0, source="inaturalist")
        gbif = _FakeSource("gbif", [c1], {"http://x/same.jpg": good})
        inat = _FakeSource("inaturalist", [c2], {"http://x/same.jpg": good})
        inference = _FakeInference()
        svc = _service([gbif, inat], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["candidates_found"] == 1
        assert summary["accepted"] == 1

    def test_failing_source_is_skipped(self) -> None:
        good = _jpeg(400, 400)
        ok = _FakeSource("gbif", [_candidate("g1", ReferenceLicense.CC0, "r1")], {"g1": good})
        inference = _FakeInference()
        svc = _service([_FailingSource(), ok], inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        # The failing source is logged and skipped; the healthy one still works.
        assert summary["accepted"] == 1

    def test_priority_order_fills_quota_from_first_source(self) -> None:
        # First source already provides everything; verify both sources receive
        # the same taxon (so iNat could apply its lifeStage filter).
        good = _jpeg(400, 400)
        gbif = _FakeSource("gbif", [_candidate("g1", ReferenceLicense.CC0, "r1")], {"g1": good})
        inat = _FakeSource("inaturalist", [_candidate("i1", ReferenceLicense.CC0, "r2")], {"i1": good})
        inference = _FakeInference()
        svc = _service([gbif, inat], inference)

        svc.acquire_for_class(get_taxon("ladybird"))

        assert gbif.last_taxon is not None and gbif.last_taxon.slug == "ladybird"
        assert inat.last_taxon is not None and inat.last_taxon.slug == "ladybird"


class TestConstruction:
    def test_empty_sources_rejected(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            PestDatasetAcquisitionService([], _FakeInference())
