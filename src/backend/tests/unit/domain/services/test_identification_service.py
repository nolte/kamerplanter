"""Unit tests for REQ-029 §3.6 IdentificationService.

Covers the core business logic that is not exercised by the adapter/registry
tests: the consent gate, the confidence-based fallback chain (Szenario A4),
species enrichment, image validation and the "no image persistence" invariant
(REQ-029 §5 / REQ-029-A §8).
"""

import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.common.exceptions import ForbiddenError, UnsupportedMediaTypeError
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter
from app.domain.models.identification import (
    IdentificationResult,
    IdentificationSuggestion,
    PlantOrgan,
)
from app.domain.services.identification_service import IdentificationService


def _png_bytes() -> bytes:
    """A minimal real PNG so strip_exif / is_supported_image accept it."""
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (0, 128, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _suggestion(name: str, confidence: float, rank: int = 1) -> IdentificationSuggestion:
    return IdentificationSuggestion(
        rank=rank,
        scientific_name=name,
        common_names=[name.split()[0]],
        confidence=confidence,
        external_id=f"ext:{name}",
    )


class _StubAdapter(PlantIdentificationAdapter):
    """Adapter stub returning a preconfigured result."""

    adapter_key = "stub"  # class-level default satisfies the ABC; overridden per instance
    supports_health_assessment = False
    rate_limit_per_day = None

    def __init__(self, adapter_key: str, result: IdentificationResult) -> None:
        self.adapter_key = adapter_key
        self._result = result
        self.calls = 0

    async def identify(self, image_data, **kwargs):  # noqa: ANN001, ANN003
        self.calls += 1
        return self._result

    async def diagnose(self, image_data, *, language="de"):  # noqa: ANN001
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True


def _make_service(chain, *, consent_allowed: bool, species_known: bool):
    consent_engine = MagicMock()
    consent_engine.is_processing_allowed.return_value = consent_allowed
    consent_repo = MagicMock()
    consent_repo.get_by_user_and_purpose.return_value = None

    species_repo = MagicMock()
    species_repo.get_by_scientific_name.return_value = SimpleNamespace(key="species_x") if species_known else None

    identification_repo = MagicMock()
    identification_repo.create.side_effect = lambda req: SimpleNamespace(key="req_1")

    registry = MagicMock()
    registry.get_fallback_chain.return_value = chain

    service = IdentificationService(
        identification_repo=identification_repo,
        species_repo=species_repo,
        consent_repo=consent_repo,
        consent_engine=consent_engine,
        registry=registry,
    )
    return service, identification_repo


@pytest.mark.asyncio
async def test_identify_requires_consent():
    result = IdentificationResult(suggestions=[_suggestion("Monstera deliciosa", 0.9)])
    adapter = _StubAdapter("local_embedding", result)
    service, _ = _make_service([adapter], consent_allowed=False, species_known=True)

    with pytest.raises(ForbiddenError):
        await service.identify_plant(_png_bytes(), tenant_key="t1", user_key="u1")
    assert adapter.calls == 0  # consent gate blocks before any adapter call


@pytest.mark.asyncio
async def test_identify_rejects_non_image():
    adapter = _StubAdapter("local_embedding", IdentificationResult())
    service, _ = _make_service([adapter], consent_allowed=True, species_known=True)

    with pytest.raises(UnsupportedMediaTypeError):
        await service.identify_plant(b"this is not an image", tenant_key="t1", user_key="u1")


@pytest.mark.asyncio
async def test_identify_success_enriches_and_persists_no_image():
    adapter = _StubAdapter(
        "local_embedding",
        IdentificationResult(suggestions=[_suggestion("Monstera deliciosa", 0.92)]),
    )
    service, repo = _make_service([adapter], consent_allowed=True, species_known=True)

    out = await service.identify_plant(_png_bytes(), organ=PlantOrgan.LEAF, tenant_key="t1", user_key="u1")

    assert out["is_plant"] is True
    assert out["adapter_key"] == "local_embedding"
    assert out["suggestions"][0]["scientific_name"] == "Monstera deliciosa"
    assert out["suggestions"][0]["species_in_database"] is True
    assert out["suggestions"][0]["matched_species_key"] == "species_x"

    # No-image-persistence invariant: only a hash is stored, image_deleted_at set.
    persisted = repo.create.call_args.args[0]
    assert persisted.image_hash.startswith("sha256:")
    assert persisted.image_deleted_at is not None
    assert not hasattr(persisted, "image_bytes")


@pytest.mark.asyncio
async def test_identify_falls_back_on_low_confidence():
    weak = _StubAdapter("local_embedding", IdentificationResult(suggestions=[_suggestion("Ficus", 0.30)]))
    strong = _StubAdapter("plantnet", IdentificationResult(suggestions=[_suggestion("Monstera deliciosa", 0.95)]))
    service, _ = _make_service([weak, strong], consent_allowed=True, species_known=True)

    out = await service.identify_plant(_png_bytes(), tenant_key="t1", user_key="u1")

    assert weak.calls == 1
    assert strong.calls == 1  # chain advanced to the fallback adapter
    assert out["adapter_key"] == "plantnet"
    assert out["suggestions"][0]["scientific_name"] == "Monstera deliciosa"
