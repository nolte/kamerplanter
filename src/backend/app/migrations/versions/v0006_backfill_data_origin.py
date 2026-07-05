"""v0006_backfill_data_origin — stamp ``origin`` on master data that predates it.

The ``origin`` provenance marker (``DataOrigin``) was added to species, cultivars,
diseases and treatments *after* those records already existed.  A document written
before the field existed has **no** stored ``origin``; the Pydantic model then reads
it back as its default ``DataOrigin.SYSTEM``.  That silently flipped every legacy
record — including user-created master data — to ``system``, which the frontend
treats as read-only and deletion-protected (UI-NFR-018).  Users were locked out of
their own data.

This migration classifies each ``origin``-less document deterministically:

* ``system`` when its natural key is part of the **current seed set** — the species
  scientific names, cultivar ``(species, name)`` identities, disease scientific
  names and treatment names shipped in the seed YAMLs (``species.yaml``,
  ``ipm.yaml`` and every ``plant_info*.yaml``).  Seed data is curated and stays
  read-only.
* ``tenant`` otherwise — i.e. user-created records, which become editable again.

The classification is intentionally biased towards ``tenant``: a record that fails
to match the (frozen) seed set is treated as user data and unlocked, so the
migration can never *re*-lock a user out of their own record.  A genuine seed
record that a future rename removed from the YAML would merely become editable —
and is re-stamped ``system`` on the next seed run anyway (seeds re-write the full
document).  The seed set is read from the YAML files as they exist at this version;
migrations are immutable, so this snapshot is exactly the right basis for
back-filling the data that predates the field.

Only documents missing ``origin`` are touched (``FILTER doc.origin == null``);
re-running is a no-op.  Irreversible (M-6): the pre-migration state carried no
provenance signal, so there is no honest inverse.
"""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml
from arango.database import StandardDatabase

from app.common.enums import DataOrigin
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.yaml_loader import SEED_DATA_DIR

logger = structlog.get_logger()


def _load_yaml(path: Path) -> dict:
    """Load one seed YAML file, tolerating an empty/malformed file as ``{}``."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _plant_info_files() -> list[Path]:
    """Every ``plant_info*.yaml`` in the seed-data directory (sorted, stable)."""
    return sorted(SEED_DATA_DIR.glob("plant_info*.yaml"))


def _seed_species_names() -> set[str]:
    """Scientific names of every seeded species (``species.yaml`` + ``plant_info*``)."""
    names: set[str] = set()
    species_yaml = _load_yaml(SEED_DATA_DIR / "species.yaml")
    for entry in species_yaml.get("species", []) or []:
        sci = entry.get("scientific_name")
        if sci:
            names.add(sci)
    for path in _plant_info_files():
        data = _load_yaml(path)
        for entry in data.get("new_species", []) or []:
            sci = entry.get("scientific_name")
            if sci:
                names.add(sci)
    return names


def _seed_cultivar_identities() -> set[tuple[str, str]]:
    """``(species_scientific_name, cultivar_name)`` pairs of every seeded cultivar."""
    identities: set[tuple[str, str]] = set()
    sources = [SEED_DATA_DIR / "species.yaml", *_plant_info_files()]
    for path in sources:
        data = _load_yaml(path)
        cultivars = data.get("cultivars", {}) or {}
        for sci_name, cv_list in cultivars.items():
            for cv in cv_list or []:
                name = cv.get("name")
                if name:
                    identities.add((sci_name, name))
    return identities


def _seed_disease_names() -> set[str]:
    """Scientific names of every seeded disease (``ipm.yaml`` + ``plant_info*``)."""
    names: set[str] = set()
    ipm_yaml = _load_yaml(SEED_DATA_DIR / "ipm.yaml")
    for entry in ipm_yaml.get("diseases", []) or []:
        sci = entry.get("scientific_name")
        if sci:
            names.add(sci)
    for path in _plant_info_files():
        data = _load_yaml(path)
        for entry in data.get("new_diseases", []) or []:
            sci = entry.get("scientific_name")
            if sci:
                names.add(sci)
    return names


def _seed_treatment_names() -> set[str]:
    """Names of every seeded treatment (``ipm.yaml`` + ``plant_info*``)."""
    names: set[str] = set()
    ipm_yaml = _load_yaml(SEED_DATA_DIR / "ipm.yaml")
    for entry in ipm_yaml.get("treatments", []) or []:
        name = entry.get("name")
        if name:
            names.add(name)
    for path in _plant_info_files():
        data = _load_yaml(path)
        for entry in data.get("new_treatments", []) or []:
            name = entry.get("name")
            if name:
                names.add(name)
    return names


class BackfillDataOriginMigration(Migration):
    version = "0006"
    name = "backfill_data_origin"
    description = "Stamp origin (system/tenant) on species/cultivars/diseases/treatments that predate the field."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        assignments: dict[str, dict[str, str]] = {}

        species_names = _seed_species_names()
        cultivar_ids = _seed_cultivar_identities()
        disease_names = _seed_disease_names()
        treatment_names = _seed_treatment_names()

        # ── Species ──────────────────────────────────────────────────────────
        species_assign: dict[str, str] = {}
        for row in db.aql.execute(
            f"FOR d IN {col.SPECIES} FILTER d.origin == null RETURN {{key: d._key, scientific_name: d.scientific_name}}"
        ):
            is_seed = row.get("scientific_name") in species_names
            species_assign[row["key"]] = (DataOrigin.SYSTEM if is_seed else DataOrigin.TENANT).value
        assignments[col.SPECIES] = species_assign

        # ── Cultivars (need the parent species' scientific name) ──────────────
        sci_by_species_key: dict[str, str] = {
            r["key"]: r.get("scientific_name")
            for r in db.aql.execute(
                f"FOR s IN {col.SPECIES} RETURN {{key: s._key, scientific_name: s.scientific_name}}"
            )
        }
        cultivar_assign: dict[str, str] = {}
        for row in db.aql.execute(
            f"FOR d IN {col.CULTIVARS} FILTER d.origin == null "
            f"RETURN {{key: d._key, name: d.name, species_key: d.species_key}}"
        ):
            parent_sci = sci_by_species_key.get(row.get("species_key"))
            is_seed = parent_sci is not None and (parent_sci, row.get("name")) in cultivar_ids
            cultivar_assign[row["key"]] = (DataOrigin.SYSTEM if is_seed else DataOrigin.TENANT).value
        assignments[col.CULTIVARS] = cultivar_assign

        # ── Diseases ─────────────────────────────────────────────────────────
        disease_assign: dict[str, str] = {}
        for row in db.aql.execute(
            f"FOR d IN {col.DISEASES} FILTER d.origin == null "
            f"RETURN {{key: d._key, scientific_name: d.scientific_name}}"
        ):
            is_seed = row.get("scientific_name") in disease_names
            disease_assign[row["key"]] = (DataOrigin.SYSTEM if is_seed else DataOrigin.TENANT).value
        assignments[col.DISEASES] = disease_assign

        # ── Treatments ───────────────────────────────────────────────────────
        treatment_assign: dict[str, str] = {}
        for row in db.aql.execute(
            f"FOR d IN {col.TREATMENTS} FILTER d.origin == null RETURN {{key: d._key, name: d.name}}"
        ):
            is_seed = row.get("name") in treatment_names
            treatment_assign[row["key"]] = (DataOrigin.SYSTEM if is_seed else DataOrigin.TENANT).value
        assignments[col.TREATMENTS] = treatment_assign

        scanned = sum(len(a) for a in assignments.values())
        counts = {
            collection: {
                "system": sum(1 for v in mapping.values() if v == DataOrigin.SYSTEM.value),
                "tenant": sum(1 for v in mapping.values() if v == DataOrigin.TENANT.value),
            }
            for collection, mapping in assignments.items()
        }

        if dry_run:
            logger.info("backfill_data_origin_dry_run", scanned=scanned, counts=counts)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={"counts": counts},
            )

        changed = 0
        for collection, mapping in assignments.items():
            for origin_value in (DataOrigin.SYSTEM.value, DataOrigin.TENANT.value):
                keys = [key for key, value in mapping.items() if value == origin_value]
                if not keys:
                    continue
                db.aql.execute(
                    "FOR k IN @keys UPDATE {_key: k, origin: @origin} IN @@collection",
                    bind_vars={"keys": keys, "origin": origin_value, "@collection": collection},
                )
                changed += len(keys)

        logger.info("backfill_data_origin_applied", changed=changed, counts=counts)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={"counts": counts},
        )


migration = BackfillDataOriginMigration()
