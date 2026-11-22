"""v0101 - the bed-template index and the system templates (REQ-053 WP 7.8, #2474; P-5).

Two things, both additive:

* ``bed_templates (tenant_key, name)`` - the catalogue of a tenant by name (``GET /bed-templates``); ``tenant_key``
  leads because the template carries it (E-01, ``test_tenant_unique_indexes_are_scoped`` style even though this
  one is not unique).
* the **system templates** - the standard sizes of GP-FR-044/045 as global rows (``tenant_key`` absent = ``null``,
  the global marker of §20.12), each under a fixed ``_key`` so every installation holds the same keys and a
  ``Location.template_key`` in an exported plan resolves on another installation.

**What the templates hold.** Only what the requirement states: a shape in the bed frame and the bed type. The
raised-bed standard differs between GP-FR-044 (1.2 x 2.4 m) and GP-FR-045 (2 x 1 x 0.8 m), so both are shipped as
separate templates (operator decision of 2026-10-19, #2466 item 9). ``height_m`` is set only where the requirement
names a height (0.8 m); ``default_layout`` and ``soil_profile_defaults`` are absent - no spacing or soil value is
invented for a template (E-10).

**Idempotent (M-3).** A template whose ``_key`` exists is left exactly as it is - an operator's edit of a system
template is never overwritten - so a second run, and a volume that already holds the rows, change nothing.
Dry-run (M-5) reports what would be created without writing. Irreversible (M-6): the bootstrap creates the index on
every boot, and a template an operator has since edited is theirs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import indexes_on

logger = structlog.get_logger(__name__)

#: Frozen here so a later change of the bootstrap constant does not change what this version did.
#: Equal to ``collections.BED_TEMPLATE_TENANT_INDEX_FIELDS`` (unit test).
TEMPLATE_INDEX_FIELDS: tuple[str, ...] = ("tenant_key", "name")


def _rect(width_m: float, length_m: float) -> dict[str, Any]:
    return {"kind": "rect", "origin": [0, 0], "width_m": width_m, "length_m": length_m, "rotation_deg": 0}


def _circle(radius_m: float) -> dict[str, Any]:
    return {"kind": "circle", "origin": [0, 0], "radius_m": radius_m}


#: ``(_key, name, location_type_key, default_geometry, height_m)`` - GP-FR-044 / GP-FR-045, nothing else.
SYSTEM_TEMPLATES: tuple[tuple[str, str, str, dict[str, Any], float | None], ...] = (
    ("sys_bed_1x1", "Bed 1 x 1 m", "bed", _rect(1.0, 1.0), None),
    ("sys_bed_2x1", "Bed 2 x 1 m", "bed", _rect(2.0, 1.0), None),
    ("sys_bed_3x1_2", "Bed 3 x 1.2 m", "bed", _rect(3.0, 1.2), None),
    ("sys_bed_4x1_2", "Bed 4 x 1.2 m", "bed", _rect(4.0, 1.2), None),
    ("sys_raised_bed_1_2x2_4", "Raised bed 1.2 x 2.4 m", "raised_bed", _rect(1.2, 2.4), None),
    ("sys_raised_bed_2x1x0_8", "Raised bed 2 x 1 x 0.8 m", "raised_bed", _rect(2.0, 1.0), 0.8),
    ("sys_planter_d0_3", "Planter diameter 0.3 m", "planter", _circle(0.15), None),
    ("sys_planter_d0_4", "Planter diameter 0.4 m", "planter", _circle(0.2), None),
    ("sys_planter_d0_5", "Planter diameter 0.5 m", "planter", _circle(0.25), None),
)


class BedTemplateIndexAndSystemTemplatesMigration(Migration):
    version = "0101"
    name = "bed_template_index_and_system_templates"
    description = (
        "Add the bed_templates (tenant_key, name) index on existing volumes and insert the system bed templates "
        "(standard sizes of GP-FR-044/045) under fixed keys (REQ-053 WP 7.8)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        present = bool(db.has_collection(col.BED_TEMPLATES))
        details: dict[str, Any] = {
            "index_fields": list(TEMPLATE_INDEX_FIELDS),
            "template_keys": [key for key, *_ in SYSTEM_TEMPLATES],
            "collection_absent": not present,
        }
        if not present:
            # Not reachable on a running installation (the bootstrap and v0093 create it); stated, not assumed.
            logger.warning("bed_template_migration_collection_absent")
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details=details
            )

        collection = db.collection(col.BED_TEMPLATES)
        index_present = bool(indexes_on(collection, TEMPLATE_INDEX_FIELDS))
        missing = [row for row in SYSTEM_TEMPLATES if not collection.has(row[0])]
        details.update(
            {
                "index_present": index_present,
                "will_create": [row[0] for row in missing],
            }
        )
        scanned = len(SYSTEM_TEMPLATES) + 1

        if dry_run:
            logger.info("bed_template_migration_dry_run", index_present=index_present, missing=len(missing))
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )

        changed = 0
        if not index_present:
            collection.add_persistent_index(fields=list(TEMPLATE_INDEX_FIELDS), unique=False, in_background=True)
            changed += 1
        now = datetime.now(UTC).isoformat()
        for key, name, location_type_key, geometry, height_m in missing:
            document: dict[str, Any] = {
                "_key": key,
                "name": name,
                "location_type_key": location_type_key,
                "default_geometry": geometry,
                "default_layout": {},
                "recurring_task_templates": [],
                "created_at": now,
                "updated_at": now,
            }
            if height_m is not None:
                document["height_m"] = height_m
            # ``ignore``: a key another instance inserted a moment ago is kept, not overwritten and not an error.
            collection.insert(document, overwrite_mode="ignore", silent=True)
            changed += 1

        logger.info("bed_template_migration_applied", created=len(missing), index_created=not index_present)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={**details, "created": [row[0] for row in missing], "index_created": not index_present},
        )


migration = BedTemplateIndexAndSystemTemplatesMigration()
