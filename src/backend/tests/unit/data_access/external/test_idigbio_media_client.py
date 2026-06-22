"""REQ-044 WP-3 — unit tests for the iDigBio media-search client.

HTTP is mocked; no real network calls. Covers the family-vs-binomial taxon-field
selection, the server-side license filter and candidate mapping. A zero-yield
response is an accepted, non-fatal outcome (specimen-biased source, §4.1).
"""

import json

import pytest

from app.common.enums import PestFindingCategory
from app.common.exceptions import ExternalSourceError
from app.data_access.external.idigbio_media_client import IDigBioMediaClient
from app.domain.models.pest_taxonomy import PestTaxon
from app.domain.models.reference_image import ReferenceLicense


class _FakeResponse:
    def __init__(self, payload, status_code=200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict]] = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        return _FakeResponse(self._payload)


def _pest(name: str) -> PestTaxon:
    return PestTaxon(slug="x", category=PestFindingCategory.PEST, common_name_de="X", scientific_name=name)


def test_family_name_uses_family_field():
    fake = _FakeClient({"items": []})
    client = IDigBioMediaClient(client=fake)

    client.list_media(_pest("Aphididae"), limit=10)

    rq = json.loads(fake.calls[0][1]["rq"])
    assert "family" in rq
    assert rq["family"] == "aphididae"


def test_binomial_uses_scientificname_field():
    fake = _FakeClient({"items": []})
    client = IDigBioMediaClient(client=fake)

    client.list_media(_pest("Tetranychus urticae"), limit=10)

    rq = json.loads(fake.calls[0][1]["rq"])
    assert "scientificname" in rq
    assert rq["scientificname"] == "tetranychus urticae"


def test_license_filter_present_in_media_query():
    fake = _FakeClient({"items": []})
    client = IDigBioMediaClient(client=fake)

    client.list_media(_pest("Tetranychus urticae"), limit=10)

    mq = json.loads(fake.calls[0][1]["mq"])
    assert "dcterms:rights" in mq
    assert "cc0" in mq["dcterms:rights"]


def test_maps_items_to_candidates_with_normalised_license():
    payload = {
        "items": [
            {
                "uuid": "abc",
                "indexTerms": {
                    "accessuri": "http://idigbio/img.jpg",
                    "rights": "http://creativecommons.org/licenses/by/4.0/",
                    "rightsholder": "Some Herbarium",
                    "format": "image/jpeg",
                },
            }
        ]
    }
    client = IDigBioMediaClient(client=_FakeClient(payload))

    candidates = client.list_media(_pest("Tetranychus urticae"), limit=10)

    assert len(candidates) == 1
    assert candidates[0].url == "http://idigbio/img.jpg"
    assert candidates[0].license == ReferenceLicense.CC_BY
    assert candidates[0].source == "idigbio"
    assert candidates[0].source_record_id == "abc"


def test_zero_yield_is_accepted():
    client = IDigBioMediaClient(client=_FakeClient({"items": []}))
    assert client.list_media(_pest("Pseudococcidae"), limit=10) == []


def test_empty_scientific_name_yields_nothing():
    client = IDigBioMediaClient(client=_FakeClient({"items": []}))
    assert client.list_media(_pest(""), limit=10) == []


def test_download_rejects_metadata_endpoint_ssrf():
    # accessuri pointing at the cloud metadata endpoint must be refused.
    client = IDigBioMediaClient(client=_FakeClient({"items": []}))
    with pytest.raises(ExternalSourceError):
        client.download("https://169.254.169.254/latest/meta-data/")


def test_download_rejects_non_https_url():
    # Plain-http accessuri is blocked by the https-only SSRF guard.
    client = IDigBioMediaClient(client=_FakeClient({"items": []}))
    with pytest.raises(ExternalSourceError):
        client.download("http://idigbio.example/img.jpg")
