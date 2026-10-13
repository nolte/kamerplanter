"""#2173 — a self-hosted match never answers a tenant with another tenant's species.

The DINOv2 reference index is one table for every tenant, and rows of tenant-owned
species can already be in it (indexed by the acquisition run before #2173, or a
quarantined user contribution a platform admin later activated). The index row
carries no owner, so ``/match`` returns ``species_key`` + ``scientific_name`` of such
a row to whoever asks. The engine therefore resolves every ``local:<species_key>``
suggestion under the caller's tenant (``readable_species``: global, own or granted)
before the result leaves the domain — for the identification history *and* for the
photo-quality assessment, which stores the suggestions on the attachment.

Real wiring: the real ``LocalEmbeddingAdapter`` (only its HTTP client is doubled —
the owned I/O boundary) feeds the real ``IdentificationEngine``; the species
repository double models ownership and grants the way ``readable_species`` reads
them (``get_by_key`` + ``is_granted_to``).
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.data_access.external.local_embedding_adapter import LocalEmbeddingAdapter
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.engines.identification_engine import IdentificationEngine
from app.domain.interfaces.plant_identification_adapter import (
    IdentificationResult,
    IdentificationSuggestion,
    PlantOrgan,
)
from app.domain.models.identification import IdentificationRequest
from app.domain.models.species import Species


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color=(0, 128, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _SpeciesRepo:
    def __init__(self, species: list[Species], grants: set[tuple[str, str]] | None = None) -> None:
        self._by_key = {s.key: s for s in species}
        self._grants = grants or set()

    def get_by_key(self, key: str) -> Species | None:
        return self._by_key.get(key)

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        return (species_key, tenant_key) in self._grants

    def find_visible_by_normalized_scientific_name(self, name: str, tenant_key: str) -> Species | None:
        target = normalize_scientific_name(name)
        for species in self._by_key.values():
            if normalize_scientific_name(species.scientific_name) == target and species.tenant_key in ("", tenant_key):
                return species
        return None


class _IdentRepo:
    def __init__(self) -> None:
        self.created: list[IdentificationRequest] = []

    def create(self, request: IdentificationRequest) -> IdentificationRequest:
        request.key = f"ident_{len(self.created) + 1}"
        self.created.append(request)
        return request


_GLOBAL = Species(_key="sp_basil", scientific_name="Ocimum basilicum", tenant_key="")
_OWN_A = Species(_key="sp_own_a", scientific_name="Mentha propria", tenant_key="tenant_a")
_PRIVATE_B = Species(_key="sp_private_b", scientific_name="Secretus privatus", tenant_key="tenant_b")
_SHARED_B = Species(_key="sp_shared_b", scientific_name="Communis donatus", tenant_key="tenant_b")


def _match_response(*species: Species) -> dict:
    return {
        "suggestions": [
            {"rank": i, "species_key": s.key, "scientific_name": s.scientific_name, "score": 0.9, "confidence": 0.9}
            for i, s in enumerate(species, start=1)
        ],
        "is_plant": True,
    }


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> LocalEmbeddingAdapter:
    monkeypatch.setattr("app.data_access.external.local_embedding_adapter.settings.inference_service_enabled", True)
    return LocalEmbeddingAdapter()


def _engine(repo: _SpeciesRepo, ident: _IdentRepo | None = None) -> IdentificationEngine:
    return IdentificationEngine(species_repo=repo, identification_repo=ident or _IdentRepo())  # type: ignore[arg-type]


def _names(suggestions: list) -> list[str]:
    return [s["scientific_name"] if isinstance(s, dict) else s.scientific_name for s in suggestions]


def test_identify_drops_another_tenants_private_species_from_the_match(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_PRIVATE_B, _GLOBAL))
    ident = _IdentRepo()
    repo = _SpeciesRepo([_GLOBAL, _PRIVATE_B])

    out = _engine(repo, ident).identify(adapter, _jpeg(), organ=PlantOrgan.AUTO, tenant_key="tenant_a", user_key="u1")

    assert _names(out["suggestions"]) == ["Ocimum basilicum"]
    assert all(s["external_id"] != "local:sp_private_b" for s in out["suggestions"])
    # Re-ranked from 1, so a gap cannot reveal that a foreign row was dropped.
    assert [s["rank"] for s in out["suggestions"]] == [1]
    # Nor does the persisted history keep it.
    assert _names(ident.created[0].results) == ["Ocimum basilicum"]


def test_identify_keeps_own_global_and_granted_species(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_OWN_A, _SHARED_B, _GLOBAL))
    repo = _SpeciesRepo([_GLOBAL, _OWN_A, _SHARED_B], grants={("sp_shared_b", "tenant_a")})

    out = _engine(repo).identify(adapter, _jpeg(), tenant_key="tenant_a", user_key="u1")

    assert _names(out["suggestions"]) == ["Mentha propria", "Communis donatus", "Ocimum basilicum"]
    assert [s["rank"] for s in out["suggestions"]] == [1, 2, 3]


def test_the_owner_still_gets_its_own_species(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_PRIVATE_B))

    out = _engine(_SpeciesRepo([_PRIVATE_B])).identify(adapter, _jpeg(), tenant_key="tenant_b", user_key="u2")

    assert _names(out["suggestions"]) == ["Secretus privatus"]


def test_a_match_of_only_foreign_species_answers_like_an_empty_index(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_PRIVATE_B))

    out = _engine(_SpeciesRepo([_PRIVATE_B])).identify(adapter, _jpeg(), tenant_key="tenant_a", user_key="u1")

    # The local adapter's is_plant is "the index matched something"; a match that
    # only named a foreign species must look exactly like no match at all.
    assert out["is_plant"] is False
    assert out["suggestions"] == []


def test_identify_raw_for_the_quality_assessment_drops_foreign_species_too(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_PRIVATE_B, _GLOBAL))

    result = _engine(_SpeciesRepo([_GLOBAL, _PRIVATE_B])).identify_raw(adapter, _jpeg(), tenant_key="tenant_a")

    assert _names(result.suggestions) == ["Ocimum basilicum"]
    assert [s.rank for s in result.suggestions] == [1]


def test_a_local_suggestion_whose_species_no_longer_exists_is_dropped(adapter):
    adapter._client.match = MagicMock(return_value=_match_response(_PRIVATE_B, _GLOBAL))

    # sp_private_b was deleted from the catalogue; its stale index row still matches.
    result = _engine(_SpeciesRepo([_GLOBAL])).identify_raw(adapter, _jpeg(), tenant_key="tenant_a")

    assert _names(result.suggestions) == ["Ocimum basilicum"]


class _ExternalAdapter:
    adapter_key = "plantnet"

    def identify(self, image_data, *, organ=PlantOrgan.AUTO, max_results=5, include_health=False, language="de"):
        return IdentificationResult(
            suggestions=[
                IdentificationSuggestion(
                    rank=1, scientific_name="Secretus privatus", confidence=0.9, external_id="plantnet:42"
                )
            ],
            is_plant=True,
        )


def test_external_taxonomy_suggestions_are_not_resolved_against_the_catalogue():
    # A Pl@ntNet answer names public taxonomy, not a catalogue row: it is never
    # filtered, even when its name equals a foreign tenant's private species.
    result = _engine(_SpeciesRepo([_PRIVATE_B])).identify_raw(_ExternalAdapter(), _jpeg(), tenant_key="tenant_a")  # type: ignore[arg-type]

    assert _names(result.suggestions) == ["Secretus privatus"]
    assert result.is_plant is True
