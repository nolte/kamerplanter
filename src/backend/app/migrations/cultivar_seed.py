"""Single source of truth for constructing and *matching* a ``Cultivar`` from seed YAML.

All plant seeders (``seed_plant_info``, ``seed_plant_info_extended``,
``seed_data``, ``seed_adventskalender``) build cultivars from the same YAML
cultivar-entry shape. They used to each inline a slightly different subset of
fields, so a field present on the model / cultivar schema (e.g. ``breeding_year``)
was silently dropped by some loaders — issue #302, drift B5.6.

Centralising the field mapping here keeps every loader field-consistent with the
``Cultivar`` model and the ``plant_info`` cultivar schema; the mapping is pinned
by ``test_seed_schema_conformance`` (schema ↔ model) and ``test_cultivar_seed``
(entry ↔ model).

Since #1090 the same four loaders also share the question *which existing rows a
seed write may match* — see :func:`global_cultivars`. Both halves of "what does a
seeder do with a YAML cultivar entry" therefore live here, so a fifth loader
cannot get either one wrong by omission.
"""

from __future__ import annotations

from typing import Any

from app.common.enums import DtmReference, PlantTrait
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, WateringGuide

_VALID_TRAITS = set(PlantTrait.__members__.values())


def global_cultivars(species_repo: ISpeciesRepository, species_key: str) -> list[Cultivar]:
    """Return the *global* cultivars of a species — the seed-match universe (SEC-002, #1090).

    Every plant seeder identifies an already-seeded cultivar by its **name** under
    its species. Since #1090 gave ``Cultivar`` an owner, that name is no longer
    unique across the collection: a tenant may create their own ``Genovese``.
    Matching against the whole collection therefore lets a tenant-controlled string
    decide what the *shared* catalogue contains — the tenant's row shadows the YAML
    entry, and the global ``Genovese`` every other tenant should see is never
    written (a cross-tenant denial of catalogue content produced by an ordinary,
    permitted write). Restricting the match to the global rows leaves the tenant's
    record untouched **and** still materialises the seed entry it was shadowing.

    One place states the rule for all four seeders: the upsert-style
    :func:`~app.migrations.seed_data.seed_cultivars` and the three skip-if-exists
    loaders (``seed_plant_info``, ``seed_plant_info_extended``,
    ``seed_adventskalender``). They keep their own create/update/skip policies —
    only "which rows may a seed write match?" is shared.

    The underlying read stays the *unscoped* system-context one
    (``tenant_key=None``) and the filter is applied here, on rows the seeder can
    actually see. Asking the repository for ``tenant_key=""`` would look equivalent
    but hides tenant rows from the caller entirely, so a future seeder that needs
    to know a tenant row is in the way (to warn, say) would silently get nothing.

    Rows written before #1090 carry no ``tenant_key`` attribute at all; the model
    default makes them global, which is exactly the ``v0038`` cutover rule — so the
    idempotent re-seed keeps finding them and the first boot after the cutover does
    not duplicate the catalogue.

    Args:
        species_repo: Repository providing the unscoped cultivar read.
        species_key: Document key of the parent species.

    Returns:
        The species' cultivars owned by no tenant, i.e. the shared catalogue.
    """
    return [c for c in species_repo.get_cultivars(species_key) if not c.tenant_key]


def build_cultivar(cv_entry: dict[str, Any], species_key: str) -> Cultivar:
    """Construct a ``Cultivar`` from a seed cultivar entry.

    Unknown ``traits`` are skipped rather than raising, so a stray free-form
    descriptor in the data cannot break a seed run. Callers keep their own
    create/update/skip-if-exists policy; this only owns field mapping.
    """
    dtm_ref_raw = cv_entry.get("dtm_reference")
    watering_override_raw = cv_entry.get("watering_guide_override")
    # days_to_maturity is not meaningful for ornamentals; the model enforces
    # ge=1, so coerce any stray 0/negative value to None instead of crashing.
    dtm = cv_entry.get("days_to_maturity")
    if dtm is not None and dtm < 1:
        dtm = None
    return Cultivar(
        name=cv_entry["name"],
        species_key=species_key,
        breeder=cv_entry.get("breeder"),
        breeding_year=cv_entry.get("breeding_year"),
        patent_status=cv_entry.get("patent_status", ""),
        days_to_maturity=dtm,
        dtm_reference=DtmReference(dtm_ref_raw) if dtm_ref_raw else None,
        bearing_start_year_min=cv_entry.get("bearing_start_year_min"),
        bearing_start_year_max=cv_entry.get("bearing_start_year_max"),
        traits=[PlantTrait(t) for t in cv_entry.get("traits", []) if t in _VALID_TRAITS],
        seed_type=cv_entry.get("seed_type"),
        disease_resistances=cv_entry.get("disease_resistances", []),
        watering_guide_override=(WateringGuide(**watering_override_raw) if watering_override_raw else None),
        phase_watering_overrides=cv_entry.get("phase_watering_overrides"),
    )
