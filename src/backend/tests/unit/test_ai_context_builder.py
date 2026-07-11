"""REQ-031 §4.2 / ADR-002 — unit tests for ``AiContextBuilder``.

Verifies the genus/family fallback for tenant-owned species and that the base
context stays PII-free.
"""

from __future__ import annotations

from app.common.enums import DataOrigin
from app.domain.interfaces.knowledge_service import ConfidenceLevel
from app.domain.models.species import Species
from app.domain.services.ai_context_builder import AiContextBuilder


def _species(**overrides) -> Species:
    defaults = {"scientific_name": "Solanum lycopersicum", "genus": "Solanum"}
    defaults.update(overrides)
    return Species(**defaults)


def test_global_species_resolves_directly_high_confidence() -> None:
    builder = AiContextBuilder()
    species = _species(origin=DataOrigin.SYSTEM)

    value, hint, confidence = builder.resolve_species_for_ks(species)

    assert value == "Solanum lycopersicum"
    assert hint is None
    assert confidence == ConfidenceLevel.HIGH


def test_tenant_species_without_parent_uses_genus_fallback() -> None:
    builder = AiContextBuilder()
    species = _species(
        scientific_name="Solanum meinesorte",
        genus="Solanum",
        origin=DataOrigin.TENANT,
    )

    value, hint, confidence = builder.resolve_species_for_ks(species)

    assert value == "Solanum sp."
    assert hint == "Solanum meinesorte"
    assert confidence == ConfidenceLevel.LOW


def test_tenant_species_no_botanical_anchor_yields_none() -> None:
    builder = AiContextBuilder()
    species = _species(
        scientific_name="Meine Pflanze",
        genus="",
        family_key=None,
        origin=DataOrigin.TENANT,
    )

    value, hint, confidence = builder.resolve_species_for_ks(species)

    assert value is None
    assert confidence == ConfidenceLevel.NONE
    # The tenant name is still carried as a hint (not to the KS species field).
    assert hint == "Meine Pflanze"


def test_build_base_context_only_carries_master_values() -> None:
    builder = AiContextBuilder()
    species = _species(origin=DataOrigin.SYSTEM)

    context = builder.build_base_context(species=species, phase="flowering", substrate="coco", ec=1.8, ph=6.2)

    payload = context.to_ks_payload()
    assert payload == {
        "species": "Solanum lycopersicum",
        "phase": "flowering",
        "substrate": "coco",
        "ec": 1.8,
        "ph": 6.2,
    }
    # The backend-only confidence marker never leaks into the KS payload.
    assert "confidence" not in payload
