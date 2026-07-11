"""REQ-029 §3.5 — identification engine: matching, persistence, select_result."""

import io

import pytest
from PIL import Image

from app.common.exceptions import NotFoundError, UnsupportedMediaTypeError, ValidationError
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.engines.identification_engine import IdentificationEngine
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    IdentificationSuggestion,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.models.identification import IdentificationRequest
from app.domain.models.species import Species


def _real_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color=(0, 128, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _StubAdapter(PlantIdentificationAdapter):
    adapter_key = "stub"
    supports_health_assessment = False
    rate_limit_per_day = 100

    def __init__(self, result: IdentificationResult) -> None:
        self._result = result
        self.received_image: bytes | None = None

    def is_configured(self) -> bool:
        return True

    def identify(self, image_data: bytes, *, organ=PlantOrgan.AUTO, max_results=5, include_health=False, language="de"):
        self.received_image = image_data
        return self._result

    def diagnose(self, image_data: bytes, *, language: str = "de") -> HealthAssessment:
        raise NotImplementedError


class _FakeSpeciesRepo:
    """Duck-typed species repo that matches on the canonical dedup key.

    Mirrors ``ArangoSpeciesRepository``: the strict lookup keys on the exact
    ``scientific_name`` while the normalized lookup collapses hybrid-marker/
    casing/whitespace variants, so ``Fragaria × ananassa`` resolves to a stored
    ``Fragaria x ananassa`` (REQ-048 Stufe 1).
    """

    def __init__(self, known: dict[str, Species] | None = None) -> None:
        self._known = known or {}

    def get_by_scientific_name(self, name: str) -> Species | None:
        return self._known.get(name)

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        target = normalize_scientific_name(name)
        for species in self._known.values():
            if normalize_scientific_name(species.scientific_name) == target:
                return species
        return None


class _FakeIdentRepo:
    def __init__(self) -> None:
        self.created: list[IdentificationRequest] = []
        self.selected: list[tuple[str, str, int]] = []
        self._store: dict[str, IdentificationRequest] = {}

    def create(self, request: IdentificationRequest) -> IdentificationRequest:
        request.key = f"ident_{len(self.created) + 1}"
        self.created.append(request)
        self._store[request.key] = request
        return request

    def get(self, key: str, tenant_key: str) -> IdentificationRequest | None:
        req = self._store.get(key)
        if req is None or req.tenant_key != tenant_key:
            return None
        return req

    def set_selected_rank(self, key: str, tenant_key: str, selected_rank: int):
        self.selected.append((key, tenant_key, selected_rank))
        req = self._store.get(key)
        if req:
            req.selected_result_rank = selected_rank
        return req

    def list_for_user(self, tenant_key, user_key, limit=20):
        return list(self._store.values())


def _engine(species_repo=None, ident_repo=None):
    return IdentificationEngine(
        species_repo=species_repo or _FakeSpeciesRepo(),
        identification_repo=ident_repo or _FakeIdentRepo(),
    )


def test_identify_matches_local_species_and_persists():
    species = Species(_key="species_monstera", scientific_name="Monstera deliciosa")
    species_repo = _FakeSpeciesRepo({"Monstera deliciosa": species})
    ident_repo = _FakeIdentRepo()
    result = IdentificationResult(
        suggestions=[
            IdentificationSuggestion(
                rank=1,
                scientific_name="Monstera deliciosa",
                confidence=0.94,
                external_id="plantnet:2868543",
                gbif_id=2868543,
            ),
            IdentificationSuggestion(
                rank=2,
                scientific_name="Monstera adansonii",
                confidence=0.03,  # below CONFIDENCE_SHOW_RESULTS (0.10) -> filtered
                external_id="plantnet:111",
            ),
        ],
        is_plant=True,
        api_response_time_ms=1200,
    )
    adapter = _StubAdapter(result)
    engine = _engine(species_repo, ident_repo)

    out = engine.identify(
        adapter,
        _real_jpeg(),
        organ=PlantOrgan.LEAF,
        tenant_key="t1",
        user_key="u1",
    )

    assert out["is_plant"] is True
    assert len(out["suggestions"]) == 1  # low-confidence suggestion filtered out
    top = out["suggestions"][0]
    assert top["matched_species_key"] == "species_monstera"
    assert top["species_in_database"] is True
    assert top["auto_accept"] is True  # 0.94 >= 0.85

    # Request persisted without image; image_hash present, image marked deleted.
    assert len(ident_repo.created) == 1
    saved = ident_repo.created[0]
    assert saved.image_hash.startswith("sha256:")
    assert saved.image_deleted_at is not None
    assert saved.selected_result_rank is None
    assert out["request_key"] == saved.key


def test_identify_strips_exif_before_sending_to_adapter():
    adapter = _StubAdapter(IdentificationResult(suggestions=[], is_plant=False))
    engine = _engine()

    engine.identify(adapter, _real_jpeg(), tenant_key="t1", user_key="u1")

    # Whatever the adapter received must be a clean JPEG without EXIF.
    assert adapter.received_image is not None
    with Image.open(io.BytesIO(adapter.received_image)) as img:
        assert img.format == "JPEG"
        assert img.info.get("exif") is None


def test_identify_unmatched_species_marks_not_in_database():
    result = IdentificationResult(
        suggestions=[
            IdentificationSuggestion(
                rank=1,
                scientific_name="Alocasia zebrina",
                confidence=0.87,
                external_id="plantnet:999",
            )
        ],
        is_plant=True,
    )
    out = _engine().identify(_StubAdapter(result), _real_jpeg(), tenant_key="t", user_key="u")
    assert out["suggestions"][0]["matched_species_key"] is None
    assert out["suggestions"][0]["species_in_database"] is False


def test_identify_hybrid_marker_variant_matches_existing_species():
    """REQ-048 R4 — a ×-spelled suggestion resolves to an existing x-spelled row.

    The stored species uses the ASCII hybrid marker; the recognition service
    returns the U+00D7 multiplication sign. Normalized matching must map the two
    onto one another so the candidate is flagged as already in the database and
    no duplicate is ever created.
    """
    species = Species(_key="species_fragaria", scientific_name="Fragaria x ananassa")
    species_repo = _FakeSpeciesRepo({"Fragaria x ananassa": species})
    result = IdentificationResult(
        suggestions=[
            IdentificationSuggestion(
                rank=1,
                scientific_name="Fragaria × ananassa",  # U+00D7, spaced
                confidence=0.91,
                external_id="plantnet:2",
            )
        ],
        is_plant=True,
    )
    out = _engine(species_repo).identify(_StubAdapter(result), _real_jpeg(), tenant_key="t", user_key="u")

    top = out["suggestions"][0]
    assert top["matched_species_key"] == "species_fragaria"
    assert top["species_in_database"] is True


def test_identify_not_a_plant():
    result = IdentificationResult(suggestions=[], is_plant=False)
    ident_repo = _FakeIdentRepo()
    out = _engine(ident_repo=ident_repo).identify(_StubAdapter(result), _real_jpeg(), tenant_key="t", user_key="u")
    assert out["is_plant"] is False
    assert out["suggestions"] == []
    # The request is still logged (audit), but with no results.
    assert len(ident_repo.created) == 1


def test_identify_rejects_non_image():
    with pytest.raises(UnsupportedMediaTypeError):
        _engine().identify(_StubAdapter(IdentificationResult()), b"not-an-image", tenant_key="t", user_key="u")


def test_select_result_persists_choice_and_returns_species():
    species = Species(_key="species_monstera", scientific_name="Monstera deliciosa")
    species_repo = _FakeSpeciesRepo({"Monstera deliciosa": species})
    ident_repo = _FakeIdentRepo()
    engine = _engine(species_repo, ident_repo)

    result = IdentificationResult(
        suggestions=[
            IdentificationSuggestion(
                rank=1, scientific_name="Monstera deliciosa", confidence=0.94, external_id="plantnet:1"
            ),
            IdentificationSuggestion(
                rank=2, scientific_name="Alocasia zebrina", confidence=0.40, external_id="plantnet:2"
            ),
        ],
        is_plant=True,
    )
    identified = engine.identify(_StubAdapter(result), _real_jpeg(), tenant_key="t1", user_key="u1")
    request_key = identified["request_key"]

    selection = engine.select_result(request_key, 1, tenant_key="t1")

    assert selection["selected_rank"] == 1
    assert selection["matched_species_key"] == "species_monstera"
    assert selection["scientific_name"] == "Monstera deliciosa"
    assert selection["species_in_database"] is True
    assert ident_repo.selected == [(request_key, "t1", 1)]


def test_select_result_unknown_request_raises_not_found():
    with pytest.raises(NotFoundError):
        _engine().select_result("missing", 1, tenant_key="t1")


def test_select_result_invalid_rank_raises_validation_error():
    ident_repo = _FakeIdentRepo()
    engine = _engine(ident_repo=ident_repo)
    result = IdentificationResult(
        suggestions=[IdentificationSuggestion(rank=1, scientific_name="X", confidence=0.9, external_id="plantnet:1")],
        is_plant=True,
    )
    identified = engine.identify(_StubAdapter(result), _real_jpeg(), tenant_key="t1", user_key="u1")

    with pytest.raises(ValidationError):
        engine.select_result(identified["request_key"], 5, tenant_key="t1")


def test_select_result_wrong_tenant_raises_not_found():
    ident_repo = _FakeIdentRepo()
    engine = _engine(ident_repo=ident_repo)
    result = IdentificationResult(
        suggestions=[IdentificationSuggestion(rank=1, scientific_name="X", confidence=0.9, external_id="plantnet:1")],
        is_plant=True,
    )
    identified = engine.identify(_StubAdapter(result), _real_jpeg(), tenant_key="t1", user_key="u1")

    with pytest.raises(NotFoundError):
        engine.select_result(identified["request_key"], 1, tenant_key="other-tenant")
