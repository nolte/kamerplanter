"""Single source of truth for constructing a ``Cultivar`` from seed YAML.

All plant seeders (``seed_plant_info``, ``seed_plant_info_extended``,
``seed_data``, ``seed_adventskalender``) build cultivars from the same YAML
cultivar-entry shape. They used to each inline a slightly different subset of
fields, so a field present on the model / cultivar schema (e.g. ``breeding_year``)
was silently dropped by some loaders — issue #302, drift B5.6.

Centralising the field mapping here keeps every loader field-consistent with the
``Cultivar`` model and the ``plant_info`` cultivar schema; the mapping is pinned
by ``test_seed_schema_conformance`` (schema ↔ model) and ``test_cultivar_seed``
(entry ↔ model).
"""

from __future__ import annotations

from typing import Any

from app.common.enums import DtmReference, PlantTrait
from app.domain.models.species import Cultivar, WateringGuide

_VALID_TRAITS = set(PlantTrait.__members__.values())


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
