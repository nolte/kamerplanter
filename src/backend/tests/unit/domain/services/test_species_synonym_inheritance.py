"""REQ-048 — a sparse species inherits UNSET fields from a synonym-matched fuller record.

Two records describe one taxon: a full ``system`` record (``Yucca elephantipes``,
every resolver-keyed field populated) and a sparse ``tenant`` record
(``Yucca gigantea``) that lists ``Yucca elephantipes`` among its own
``synonyms``. A plant hanging off the sparse record used to see empty
``photosynthesis_type`` + absent lifecycle fields and got routed onto an annual
harvest cycle (#949, #975). At create time the sparse record now copies the
fuller record's genuinely-empty fields, so the phase-sequence resolver sees the
same inputs regardless of which record a plant hangs off.

The inheritance is **additive** and **never identity-changing**: identity /
provenance fields (``key``/``scientific_name``/``scientific_name_normalized``/
``origin``/``synonyms``) and any value the caller actually set are left alone,
and the fuller/global record itself is never modified or hidden (#324).
"""

from __future__ import annotations

from app.common.enums import DataOrigin, GrowthHabit, HarvestPattern, PlantCategory
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService


class _FakeSpeciesRepo:
    """In-memory repo modelling the dedup UPSERT + synonym-match contract.

    Keyed on ``scientific_name_normalized``. Records how many inserts happened and
    which stored documents were mutated, so a test can assert the fuller/global
    record was never touched (#324).
    """

    def __init__(self, existing: list[Species] | None = None) -> None:
        self._by_norm: dict[str, Species] = {}
        for sp in existing or []:
            self._by_norm[sp.scientific_name_normalized] = sp
        self.inserted: list[Species] = []
        self.updated_keys: list[str] = []

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return self._by_norm.get(normalize_scientific_name(name))

    def get_by_normalized_scientific_name_for_tenant(self, name: str, tenant_key: str) -> Species | None:
        """The tenant-scoped lookup the create path uses since #1162.

        Modelled rather than delegated to the unscoped one above: the whole point
        of the per-tenant key is that a *foreign* row must not answer this
        question, and a double that ignored `tenant_key` would hide exactly that.
        """
        found = self._by_norm.get(normalize_scientific_name(name))
        return found if found is not None and found.tenant_key == tenant_key else None

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        existing = self._by_norm.get(species.scientific_name_normalized)
        if existing is not None:
            return existing
        self.inserted.append(species)
        stored = species.model_copy(update={"key": f"species_{len(self.inserted)}"})
        self._by_norm[species.scientific_name_normalized] = stored
        return stored

    def update(self, key: str, species: Species) -> Species:
        self.updated_keys.append(key)
        self._by_norm[species.scientific_name_normalized] = species
        return species

    def find_synonym_match_candidates(self, species: Species) -> list[Species]:
        """Precise synonym-link candidates (mirrors the AQL repo contract).

        Returns every stored record whose normalized name equals one of the new
        record's normalized synonyms, or whose normalized synonyms contain the
        new record's normalized name — excluding an exact normalized-name match.
        """
        new_norm = species.scientific_name_normalized
        new_syn_norms = {normalize_scientific_name(s) for s in species.synonyms}
        candidates: list[Species] = []
        for stored in self._by_norm.values():
            if stored.scientific_name_normalized == new_norm:
                continue
            stored_syn_norms = {normalize_scientific_name(s) for s in stored.synonyms}
            if stored.scientific_name_normalized in new_syn_norms or new_norm in stored_syn_norms:
                candidates.append(stored)
        return candidates

    def list_all_species(self) -> list[Species]:
        return list(self._by_norm.values())


def _service(repo: _FakeSpeciesRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def _full_yucca() -> Species:
    """The authoritative, fully-populated system record for the taxon."""
    return Species(
        _key="species_full",
        scientific_name="Yucca elephantipes",
        origin=DataOrigin.SYSTEM,
        common_names=["Riesen-Palmlilie"],
        genus="Yucca",
        growth_habit=GrowthHabit.SHRUB,
        photosynthesis_type="cam",
        plant_category=PlantCategory.INDOOR_HOUSEPLANT,
        harvest_pattern=HarvestPattern.PERENNIAL,
        native_habitat="Central America",
        allows_harvest=False,
    )


def test_sparse_record_inherits_unset_fields_from_synonym_match():
    """The #949/#975 repro: the sparse record fills its empty resolver-keyed fields."""
    repo = _FakeSpeciesRepo([_full_yucca()])

    sparse = Species(
        scientific_name="Yucca gigantea",
        origin=DataOrigin.TENANT,
        synonyms=["Yucca elephantipes"],
        common_names=["Riesen-Yucca"],  # caller-set — must survive
    )
    result = _service(repo).create_species(sparse)

    # A new record was inserted (not resolved onto the fuller one — names differ).
    assert len(repo.inserted) == 1
    assert result.key == "species_1"

    # Previously-empty resolver-keyed fields are now filled from the fuller record.
    assert result.photosynthesis_type == "cam"
    assert result.plant_category == PlantCategory.INDOOR_HOUSEPLANT
    assert result.harvest_pattern == HarvestPattern.PERENNIAL
    assert result.native_habitat == "Central America"

    # Identity / provenance is untouched.
    assert result.scientific_name == "Yucca gigantea"
    assert result.scientific_name_normalized == normalize_scientific_name("Yucca gigantea")
    assert result.origin == DataOrigin.TENANT
    assert result.synonyms == ["Yucca elephantipes"]

    # A caller-set field is NOT overwritten by the match.
    assert result.common_names == ["Riesen-Yucca"]


def test_caller_set_field_is_not_overwritten():
    repo = _FakeSpeciesRepo([_full_yucca()])

    sparse = Species(
        scientific_name="Yucca gigantea",
        origin=DataOrigin.TENANT,
        synonyms=["Yucca elephantipes"],
        photosynthesis_type="c3",  # deliberately different from the fuller record's "cam"
    )
    result = _service(repo).create_species(sparse)

    assert result.photosynthesis_type == "c3"


def test_non_empty_but_default_field_is_not_corrected():
    """growth_habit=HERB default is a non-empty value → left alone (documented limit)."""
    repo = _FakeSpeciesRepo([_full_yucca()])  # fuller record has growth_habit=SHRUB

    sparse = Species(
        scientific_name="Yucca gigantea",
        origin=DataOrigin.TENANT,
        synonyms=["Yucca elephantipes"],
    )
    result = _service(repo).create_species(sparse)

    # HERB is the model default and non-empty, so it is NOT treated as unset.
    assert result.growth_habit == GrowthHabit.HERB


def test_record_without_match_is_stored_unchanged():
    repo = _FakeSpeciesRepo([_full_yucca()])

    lonely = Species(scientific_name="Solanum lycopersicum", origin=DataOrigin.TENANT)
    result = _service(repo).create_species(lonely)

    assert result.photosynthesis_type is None
    assert result.plant_category is None
    assert result.harvest_pattern is None
    assert result.native_habitat == ""


def test_global_system_record_is_untouched_and_readable():
    """#324: the additive inheritance must never mutate or hide the global catalogue."""
    full = _full_yucca()
    repo = _FakeSpeciesRepo([full])

    sparse = Species(
        scientific_name="Yucca gigantea",
        origin=DataOrigin.TENANT,
        synonyms=["Yucca elephantipes"],
    )
    _service(repo).create_species(sparse)

    # The fuller record was never updated.
    assert repo.updated_keys == []
    still_there = repo.get_by_normalized_scientific_name("Yucca elephantipes")
    assert still_there is not None
    assert still_there.key == "species_full"
    assert still_there.origin == DataOrigin.SYSTEM
    assert still_there.photosynthesis_type == "cam"


def test_reverse_direction_synonym_link_is_matched():
    """The fuller record lists the new record's name as a synonym (other direction)."""
    full = _full_yucca().model_copy(update={"synonyms": ["Yucca gigantea"]})
    repo = _FakeSpeciesRepo([full])

    sparse = Species(scientific_name="Yucca gigantea", origin=DataOrigin.TENANT)
    result = _service(repo).create_species(sparse)

    assert result.photosynthesis_type == "cam"
    assert result.plant_category == PlantCategory.INDOOR_HOUSEPLANT


def test_shadow_report_surfaces_known_pair():
    full = _full_yucca()
    sparse = Species(
        _key="species_sparse",
        scientific_name="Yucca gigantea",
        origin=DataOrigin.TENANT,
        synonyms=["Yucca elephantipes"],
    )
    repo = _FakeSpeciesRepo([full, sparse])

    pairs = _service(repo).list_shadow_pairs()

    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["link"] == "synonym"
    # The richer record leads.
    assert pair["richer"]["scientific_name"] == "Yucca elephantipes"
    assert pair["sparser"]["scientific_name"] == "Yucca gigantea"
    assert pair["richer"]["populated_field_count"] > pair["sparser"]["populated_field_count"]


def test_shadow_report_empty_on_clean_fixture():
    repo = _FakeSpeciesRepo(
        [
            Species(_key="a", scientific_name="Solanum lycopersicum"),
            Species(_key="b", scientific_name="Ocimum basilicum"),
        ]
    )

    assert _service(repo).list_shadow_pairs() == []
