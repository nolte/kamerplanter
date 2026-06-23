"""REQ-044 WP-3 — unit tests for the iNaturalist direct-API media client.

All HTTP is mocked through a fake httpx-like client; no real network calls.
Covers taxon-id resolution, the per-photo license filter (request params + the
re-check on each photo), and the lifeStage annotation filter for larvae.
"""

import json

import pytest

from app.common.enums import PestFindingCategory
from app.common.exceptions import ExternalSourceError
from app.data_access.external.inaturalist_media_client import INaturalistMediaClient
from app.domain.models.pest_taxonomy import PestTaxon, get_taxon
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
    """Records requests and replays canned responses keyed by path."""

    def __init__(self, responses) -> None:
        self._responses = responses
        self.calls: list[tuple[str, dict]] = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        return _FakeResponse(self._responses[path])


def _photo(pid, license_code, *, url="http://inat/photos/1/square.jpg"):
    return {"id": pid, "license_code": license_code, "url": url, "attribution": f"(c) user {pid}"}


def _observation(oid, photos):
    return {"id": oid, "user": {"login": "observer"}, "photos": photos}


def test_resolves_taxon_id_by_name_then_queries_observations():
    responses = {
        "/taxa": {"results": [{"id": 48623}]},
        "/observations": {"results": [_observation(1, [_photo(11, "cc-by")])]},
    }
    fake = _FakeClient(responses)
    client = INaturalistMediaClient(client=fake)

    taxon = PestTaxon(
        slug="x", category=PestFindingCategory.PEST, common_name_de="X", scientific_name="Tetranychus urticae"
    )
    candidates = client.list_media(taxon, limit=10)

    # /taxa lookup happened with the scientific name.
    taxa_call = next(c for c in fake.calls if c[0] == "/taxa")
    assert taxa_call[1]["q"] == "Tetranychus urticae"
    # /observations used the resolved id + research grade + per-photo license filter.
    obs_call = next(c for c in fake.calls if c[0] == "/observations")
    assert obs_call[1]["taxon_id"] == 48623
    assert obs_call[1]["quality_grade"] == "research"
    assert "cc0" in obs_call[1]["photo_license"]
    assert len(candidates) == 1
    assert candidates[0].license == ReferenceLicense.CC_BY
    assert candidates[0].source == "inaturalist"


def test_explicit_inat_taxon_id_skips_name_lookup():
    responses = {"/observations": {"results": [_observation(1, [_photo(11, "cc0")])]}}
    fake = _FakeClient(responses)
    client = INaturalistMediaClient(client=fake)

    taxon = PestTaxon(
        slug="x",
        category=PestFindingCategory.PEST,
        common_name_de="X",
        scientific_name="Whatever",
        inat_taxon_id=12345,
    )
    client.list_media(taxon, limit=10)

    assert all(c[0] != "/taxa" for c in fake.calls)
    obs_call = next(c for c in fake.calls if c[0] == "/observations")
    assert obs_call[1]["taxon_id"] == 12345


def test_per_photo_license_recheck_marks_unknown_for_unlicensed_photo():
    # iNat returns a null license_code for all-rights-reserved photos.
    responses = {
        "/taxa": {"results": [{"id": 1}]},
        "/observations": {"results": [_observation(1, [_photo(11, None)])]},
    }
    client = INaturalistMediaClient(client=_FakeClient(responses))
    taxon = PestTaxon(slug="x", category=PestFindingCategory.PEST, common_name_de="X", scientific_name="Some name")

    candidates = client.list_media(taxon, limit=10)

    assert candidates[0].license == ReferenceLicense.UNKNOWN  # rejected downstream


def test_life_stage_filter_applied_for_larvae_beneficial():
    responses = {
        "/taxa": {"results": [{"id": 7782}]},
        "/observations": {"results": [_observation(1, [_photo(11, "cc-by-nc")])]},
    }
    fake = _FakeClient(responses)
    client = INaturalistMediaClient(client=fake)

    ladybird = get_taxon("ladybird")
    assert ladybird.inat_life_stage == "Larva"  # taxonomy opted it in

    client.list_media(ladybird, limit=10)

    obs_call = next(c for c in fake.calls if c[0] == "/observations")
    assert obs_call[1]["term_id"] == 1  # Life Stage controlled term
    assert obs_call[1]["term_value_id"] == 6  # Larva


def test_no_life_stage_filter_when_unset():
    responses = {
        "/taxa": {"results": [{"id": 1}]},
        "/observations": {"results": []},
    }
    fake = _FakeClient(responses)
    client = INaturalistMediaClient(client=fake)
    taxon = get_taxon("aphid")  # no inat_life_stage

    client.list_media(taxon, limit=10)

    obs_call = next(c for c in fake.calls if c[0] == "/observations")
    assert "term_id" not in obs_call[1]
    assert "term_value_id" not in obs_call[1]


def test_unresolved_taxon_yields_no_candidates():
    responses = {"/taxa": {"results": []}}
    client = INaturalistMediaClient(client=_FakeClient(responses))
    taxon = PestTaxon(slug="x", category=PestFindingCategory.PEST, common_name_de="X", scientific_name="Nonexistent")

    assert client.list_media(taxon, limit=10) == []


def test_photo_url_upgraded_to_medium_size():
    responses = {
        "/taxa": {"results": [{"id": 1}]},
        "/observations": {"results": [_observation(1, [_photo(11, "cc0", url="http://inat/photos/9/square.jpeg")])]},
    }
    client = INaturalistMediaClient(client=_FakeClient(responses))
    taxon = PestTaxon(slug="x", category=PestFindingCategory.PEST, common_name_de="X", scientific_name="Some name")

    candidates = client.list_media(taxon, limit=10)

    assert candidates[0].url == "http://inat/photos/9/medium.jpeg"


def test_observations_params_are_json_serialisable():
    # Guard: every observations param must be a primitive (httpx query-safe).
    responses = {
        "/taxa": {"results": [{"id": 1}]},
        "/observations": {"results": []},
    }
    fake = _FakeClient(responses)
    client = INaturalistMediaClient(client=fake)
    taxon = get_taxon("hoverfly")

    client.list_media(taxon, limit=5)

    obs_call = next(c for c in fake.calls if c[0] == "/observations")
    json.dumps(obs_call[1])  # raises if a non-serialisable value leaked in


def test_download_rejects_loopback_url_ssrf():
    # A photo url resolving to loopback must be refused before any dial.
    client = INaturalistMediaClient(client=_FakeClient({}))
    with pytest.raises(ExternalSourceError):
        client.download("https://127.0.0.1/photos/9/medium.jpg")


def test_download_rejects_non_https_url():
    # http (and anything but https) is blocked by the SSRF guard.
    client = INaturalistMediaClient(client=_FakeClient({}))
    with pytest.raises(ExternalSourceError):
        client.download("http://static.inaturalist.org/photos/9/medium.jpg")
