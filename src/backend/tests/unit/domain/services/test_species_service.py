"""REQ-048 Stufe 1 — SpeciesService.create_species idempotent deduplication.

A create whose canonical key already exists must resolve to the existing species
(idempotent), never raise or insert a duplicate — even when the incoming name
only differs by the hybrid marker (× vs x), casing or whitespace.
"""

from __future__ import annotations

from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService


class _FakeSpeciesRepo:
    """Models the atomic UPSERT contract of the real repository (SEC-003).

    Keyed on the canonical ``scientific_name_normalized``: a create whose key
    already exists returns the stored row unchanged; otherwise it inserts.
    """

    def __init__(self, existing: list[Species] | None = None) -> None:
        self._by_norm: dict[str, Species] = {}
        for sp in existing or []:
            self._by_norm[sp.scientific_name_normalized] = sp
        self.inserted: list[Species] = []

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return self._by_norm.get(normalize_scientific_name(name))

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        existing = self._by_norm.get(species.scientific_name_normalized)
        if existing is not None:
            return existing
        self.inserted.append(species)
        stored = species.model_copy(update={"key": f"species_{len(self.inserted)}"})
        self._by_norm[species.scientific_name_normalized] = stored
        return stored


def _service(repo: _FakeSpeciesRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def test_create_new_species_inserts():
    repo = _FakeSpeciesRepo()
    created = _service(repo).create_species(Species(scientific_name="Solanum lycopersicum"))
    assert len(repo.inserted) == 1
    assert created.key == "species_1"


def test_create_hybrid_marker_duplicate_returns_existing():
    existing = Species(_key="species_fragaria", scientific_name="Fragaria x ananassa")
    repo = _FakeSpeciesRepo([existing])

    result = _service(repo).create_species(Species(scientific_name="Fragaria × ananassa"))

    # Idempotent: the existing record is returned, nothing new is inserted.
    assert result.key == "species_fragaria"
    assert result.scientific_name == "Fragaria x ananassa"
    assert repo.inserted == []


def test_create_casing_and_whitespace_duplicate_returns_existing():
    existing = Species(_key="species_tomato", scientific_name="Solanum lycopersicum")
    repo = _FakeSpeciesRepo([existing])

    result = _service(repo).create_species(Species(scientific_name="solanum   LYCOPERSICUM"))

    assert result.key == "species_tomato"
    assert repo.inserted == []


def test_repeated_variant_creates_do_not_duplicate():
    """SEC-003 UPSERT contract: two creates of the same normalized key → one row.

    Models the guarantee the atomic UPSERT provides against the (previously
    check-then-insert) duplicate window: the second create of a hybrid-marker
    variant resolves to the row inserted by the first, never a second document.
    """
    repo = _FakeSpeciesRepo()
    service = _service(repo)

    first = service.create_species(Species(scientific_name="Fragaria × ananassa"))
    second = service.create_species(Species(scientific_name="Fragaria x ananassa"))

    assert len(repo.inserted) == 1
    assert first.key == second.key


class _FakeUpdateRepo:
    """Minimal repo supporting the get_or_raise/update contract for update tests."""

    def __init__(self, existing: Species) -> None:
        self._existing = existing
        self.updated: Species | None = None

    def get_or_raise(self, key: str) -> Species:  # noqa: ARG002
        return self._existing

    def update(self, key: str, species: Species) -> Species:  # noqa: ARG002
        self.updated = species
        return species


def test_update_preserves_cultivation_flexible_master_data():
    """ADR-006 E6 (#615): a form update never resets the master-data flag.

    The edit form (SpeciesCreate) does not submit ``cultivation_flexible`` — the
    incoming Species therefore defaults it to False. The service must carry the
    stored value across the full-replace update, mirroring the origin/reference-
    image preservation.
    """
    stored = Species(_key="sp-1", scientific_name="Solanum lycopersicum", cultivation_flexible=True)
    repo = _FakeUpdateRepo(stored)
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]

    incoming = Species(scientific_name="Solanum lycopersicum")  # flag defaults False
    result = service.update_species("sp-1", incoming)

    assert result.cultivation_flexible is True
    assert repo.updated is not None
    assert repo.updated.cultivation_flexible is True
