"""Unit tests for the shared cultivar seed builder and seed-match universe.

``build_cultivar`` is the single source of truth for turning a seed YAML cultivar
entry into a ``Cultivar`` model, used by every plant seeder. These tests pin the
field mapping — most importantly that fields which used to be silently dropped by
individual loaders (``breeding_year``, ``disease_resistances``,
``phase_watering_overrides``, …) now survive the round trip (issue #302, B5.6).

``global_cultivars`` is the second thing those seeders share since #1090: which
existing rows a seed write may match at all. Its rule is pinned here once
(SEC-002); that each seeder actually routes through it is pinned behaviourally in
``test_sibling_seeder_cultivar_ownership.py`` and
``test_seed_data_cultivar_ownership.py``.
"""

from __future__ import annotations

from app.common.enums import DtmReference, PlantTrait
from app.domain.models.species import Cultivar
from app.migrations.cultivar_seed import build_cultivar, global_cultivars


def test_full_entry_maps_every_field() -> None:
    entry = {
        "name": "Yolo Wonder",
        "breeder": "PetoSeed",
        "breeding_year": 1952,
        "patent_status": "expired",
        "days_to_maturity": 75,
        "dtm_reference": "transplant",
        "bearing_start_year_min": 1,
        "bearing_start_year_max": 2,
        "traits": ["disease_resistant", "high_yield"],
        "seed_type": "open_pollinated",
        "disease_resistances": ["TMV", "PVY"],
        "phase_watering_overrides": {"flowering": 3},
        "watering_guide_override": {"interval_days": 4, "volume_ml_min": 200, "volume_ml_max": 600},
    }

    cultivar = build_cultivar(entry, species_key="sp-123")

    assert cultivar.name == "Yolo Wonder"
    assert cultivar.species_key == "sp-123"
    assert cultivar.breeder == "PetoSeed"
    assert cultivar.breeding_year == 1952
    assert cultivar.patent_status == "expired"
    assert cultivar.days_to_maturity == 75
    assert cultivar.dtm_reference is DtmReference.TRANSPLANT
    assert cultivar.bearing_start_year_min == 1
    assert cultivar.bearing_start_year_max == 2
    assert cultivar.traits == [PlantTrait.DISEASE_RESISTANT, PlantTrait.HIGH_YIELD]
    assert cultivar.seed_type == "open_pollinated"
    assert cultivar.disease_resistances == ["TMV", "PVY"]
    assert cultivar.phase_watering_overrides == {"flowering": 3}
    assert cultivar.watering_guide_override is not None
    assert cultivar.watering_guide_override.interval_days == 4


def test_breeding_year_survives_minimal_entry() -> None:
    """Regression: breeding_year present in data must not be dropped on import."""
    cultivar = build_cultivar({"name": "Marketmore 76", "breeding_year": 1976}, species_key="sp-9")

    assert cultivar.breeding_year == 1976


def test_missing_optional_fields_default_cleanly() -> None:
    cultivar = build_cultivar({"name": "Bare"}, species_key="sp-1")

    assert cultivar.breeding_year is None
    assert cultivar.patent_status == ""
    assert cultivar.dtm_reference is None
    assert cultivar.days_to_maturity is None
    assert cultivar.traits == []
    assert cultivar.disease_resistances == []
    assert cultivar.watering_guide_override is None
    assert cultivar.phase_watering_overrides is None


def test_unknown_traits_are_skipped_not_raised() -> None:
    cultivar = build_cultivar(
        {"name": "Mixed", "traits": ["compact", "not_a_real_trait", "heirloom"]},
        species_key="sp-1",
    )

    assert cultivar.traits == [PlantTrait.COMPACT, PlantTrait.HEIRLOOM]


def test_null_dtm_reference_is_none() -> None:
    cultivar = build_cultivar({"name": "X", "dtm_reference": None}, species_key="sp-1")

    assert cultivar.dtm_reference is None


def test_nonpositive_days_to_maturity_coerced_to_none() -> None:
    """The model enforces ge=1; a stray 0/negative (e.g. ornamentals) must not crash."""
    assert build_cultivar({"name": "Zero", "days_to_maturity": 0}, species_key="sp-1").days_to_maturity is None
    assert build_cultivar({"name": "Neg", "days_to_maturity": -5}, species_key="sp-1").days_to_maturity is None
    assert build_cultivar({"name": "Ok", "days_to_maturity": 60}, species_key="sp-1").days_to_maturity == 60


# ── the shared seed-match universe (SEC-002, #1090) ──────────────────────────


class _RecordingRepo:
    """Returns a fixed cultivar list and records how the read was called."""

    def __init__(self, cultivars: list[Cultivar]) -> None:
        self._cultivars = cultivars
        self.calls: list[tuple[tuple, dict]] = []

    def get_cultivars(self, species_key: str, **kwargs) -> list[Cultivar]:
        self.calls.append(((species_key,), kwargs))
        return [c for c in self._cultivars if c.species_key == species_key]


def _rows() -> list[Cultivar]:
    return [
        Cultivar(_key="cv_global", name="Genovese", species_key="sp-1", tenant_key=""),
        Cultivar(_key="cv_legacy", name="Napoletano", species_key="sp-1"),
        Cultivar(_key="cv_tenant", name="Genovese", species_key="sp-1", tenant_key="tenant_42"),
        Cultivar(_key="cv_other_species", name="Genovese", species_key="sp-2", tenant_key=""),
    ]


def test_global_cultivars_excludes_tenant_owned_rows() -> None:
    # The SEC-002 rule: a tenant-owned row is never a seed-match candidate, even when
    # its name collides with a YAML entry.
    names = {c.key for c in global_cultivars(_RecordingRepo(_rows()), "sp-1")}

    assert names == {"cv_global", "cv_legacy"}


def test_global_cultivars_keeps_pre_1090_rows_without_the_attribute() -> None:
    # v0038 left every legacy row global; dropping them would duplicate the whole
    # catalogue on the first boot after the cutover.
    legacy = Cultivar(_key="cv_legacy", name="Napoletano", species_key="sp-1")

    assert global_cultivars(_RecordingRepo([legacy]), "sp-1") == [legacy]


def test_global_cultivars_reads_unscoped_so_the_filter_is_the_only_narrowing() -> None:
    # Pins *how* the rows are fetched: a scoped repository read (tenant_key="") would
    # look equivalent while hiding the tenant rows from the caller entirely.
    repo = _RecordingRepo(_rows())

    global_cultivars(repo, "sp-1")

    assert repo.calls == [(("sp-1",), {})]


def test_global_cultivars_is_empty_when_only_tenant_rows_exist() -> None:
    tenant_only = [Cultivar(_key="cv_tenant", name="Genovese", species_key="sp-1", tenant_key="tenant_42")]

    assert global_cultivars(_RecordingRepo(tenant_only), "sp-1") == []
