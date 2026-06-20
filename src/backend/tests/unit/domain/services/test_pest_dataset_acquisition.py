"""REQ-044 WP-3 — dataset acquisition: license filter, quality gate, indexing."""

import io

from PIL import Image

from app.domain.models.pest_taxonomy import get_taxon
from app.domain.models.reference_image import MediaCandidate, ReferenceLicense
from app.domain.services.pest_dataset_acquisition import PestDatasetAcquisitionService


def _jpeg(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 120, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _FakeMedia:
    def __init__(self, candidates, images) -> None:
        self._candidates = candidates
        self._images = images

    def list_media(self, taxon_key, *, limit=40):
        return self._candidates[:limit]

    def download(self, url):
        return self._images[url]


class _FakeInference:
    def __init__(self) -> None:
        self.indexed: list[dict] = []

    def upsert_prototype(self, image, **kwargs):
        self.indexed.append(kwargs)
        return {"status": "ok"}


def _candidate(url, license_value, rid):
    return MediaCandidate(
        url=url, license=license_value, source="gbif", source_record_id=rid, attribution="A. Photographer"
    )


class TestAcquireForClass:
    def test_only_cc0_and_ccby_indexed_with_manifest(self) -> None:
        good = _jpeg(400, 400)
        candidates = [
            _candidate("u1", ReferenceLicense.CC0, "r1"),
            _candidate("u2", ReferenceLicense.CC_BY_NC, "r2"),  # rejected (license)
            _candidate("u3", ReferenceLicense.CC_BY, "r3"),
            _candidate("u4", ReferenceLicense.UNKNOWN, "r4"),  # rejected (license)
        ]
        images = {"u1": good, "u3": good}
        inference = _FakeInference()
        svc = PestDatasetAcquisitionService(_FakeMedia(candidates, images), inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 2
        assert summary["rejected_license"] == 2
        assert len(inference.indexed) == 2
        # provenance is carried through for CC-BY attribution compliance
        labels = {row["label"] for row in inference.indexed}
        assert labels == {"spider_mite"}
        assert inference.indexed[0]["source_url"] in {"u1", "u3"}
        assert inference.indexed[0]["attribution"] == "A. Photographer"
        assert len(summary["manifest"]) == 2

    def test_too_small_image_rejected_on_quality(self) -> None:
        candidates = [_candidate("u1", ReferenceLicense.CC0, "r1")]
        images = {"u1": _jpeg(100, 100)}  # below min dimension
        inference = _FakeInference()
        svc = PestDatasetAcquisitionService(_FakeMedia(candidates, images), inference)

        summary = svc.acquire_for_class(get_taxon("spider_mite"))

        assert summary["accepted"] == 0
        assert summary["rejected_quality"] == 1
        assert inference.indexed == []

    def test_beneficial_class_carries_category(self) -> None:
        candidates = [_candidate("u1", ReferenceLicense.CC0, "r1")]
        images = {"u1": _jpeg(400, 400)}
        inference = _FakeInference()
        svc = PestDatasetAcquisitionService(_FakeMedia(candidates, images), inference)

        svc.acquire_for_class(get_taxon("ladybird"))

        assert inference.indexed[0]["category"] == "beneficial"
