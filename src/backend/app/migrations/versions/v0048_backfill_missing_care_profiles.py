"""v0048 — give every stored plant the ``CareProfile`` the nightly run needs (#1444 part 2).

``CareReminderService.get_or_create_profile`` is the only thing that creates a
``CareProfile``, and until PR #1440 it was reached by two **read** paths: the
profile endpoint and the tenant care dashboard, the latter for every unprofiled
plant of the tenant at once. #1422 removed that write (a read that persists, and
a viewer-writable one at that) and moved the creation onto the plant-creation
paths, where ``tests/unit/guards/test_care_profile_bootstrap_coverage.py`` now
holds it.

That covers plants created **from then on**. A plant created earlier, in a tenant
where nobody ever opened the care dashboard, still has no profile — and
``generate_due_care_reminders`` iterates *stored profiles*, so such a plant is
not "skipped" by the nightly run, it is absent from the iteration entirely. No
counter in that task is reached by it. This migration creates the missing
profiles, once, for exactly that population.

## The population is not spelled out here

``unprofiled_plant_count_aql`` / ``unprofiled_plant_keys_aql`` are **imported**
from :mod:`app.data_access.arango.care_reminder_repository`. The audit script
(``scripts/audit_care_profiles.py``), the nightly warning in ``care_tasks.py``
and this migration therefore select the same rows; a second copy of the FILTER
would be a second answer to "how many plants are affected", and the audit is this
migration's positive control (its ``expected_profiles_to_create`` must read ``0``
afterwards, with ``plants_active`` unchanged). ``tests/unit/migrations/versions/
test_v0048_backfill_missing_care_profiles.py`` pins the *identity* of the imported
functions, so replacing the import with a local copy turns red.

The predicate hangs on the profile's ``plant_key`` **field**, not on the
``has_care_profile`` edge, because only the field is ever read back
(``get_profile_by_plant_key`` → ``find_one_by_field("plant_key", …)``). Removed
plants (``removed_on != null``) are outside it, as they are outside the nightly
run.

## What one plant gets

The species is resolved and passed on, and leaving it out was the round-1 defect
of #1440: ``auto_generate_profile`` derives the care style from the botanical
family and falls back to the ``TROPICAL`` 7-day preset when it has none, so a
backfill without it would give every plant in the installation — a Cactaceae
included — tropical presets. The profile is created once and read thereafter, so
those values would be the plant's for good.

**The family is resolved to its NAME, not passed as the stored key.** Measured,
not assumed: ``Species.family_key`` holds the ArangoDB ``_key`` of a
``botanical_families`` document (``seed_data.py`` builds ``family_map[name] =
created.key``, and ``BaseArangoRepository._to_doc`` pops ``_key`` before every
insert, so that key is server-assigned and numeric). ``FAMILY_CARE_MAP`` is keyed
by the family **name** (``"Cactaceae"``). Handing it the stored key matches
nothing and yields ``TROPICAL`` — which is what ``_bootstrap_care_profile`` in
``app/common/dependencies.py`` does today, so the very defect #1440 fixed is
still live on the creation path (reported separately; a backfill repeating it
would be irreversible for the whole historic population). A ``family_key`` that
resolves to no document is used verbatim as the family name instead, so an
installation whose species carry family *names* is served correctly too, and the
row is reported under ``family_unresolved`` either way.

``watering_guide`` is deliberately **not** passed: no production caller passes one
(#1481), so a backfill that synthesised one would give migrated plants presets no
freshly created plant receives.

The profile carries ``plant_key`` and **no** ``tenant_key`` — the model has none;
a ``CareProfile`` is tenant-anchored through its plant, the shape ``Location`` and
``Slot`` have through their site. The write goes through
``ArangoCareReminderRepository.create_linked_profile``, the single call
``get_or_create_profile`` makes, rather than hand-written inserts, so the document
shape and the edge cannot drift from the production path.

## The edge race, and why a loser is not an abort

``has_care_profile`` carries a unique index on ``_from`` (``ensure_collections``),
so a second writer for the same plant is refused with 1200/1210 (PR #1486). This
migration runs under the migration lock during startup, with no concurrent
requests — but a plant can *already* own an edge that points at a profile whose
``plant_key`` names somebody else (or nothing), and such a plant is inside the
predicate while its ``_from`` slot is taken. Rather than abort a whole
installation's backfill on it, that one plant is reported as ``already_profiled``
and the run continues: since #1292 the profile and the edge are one transaction,
so the refused attempt rolls itself back and the database is left exactly as it
was found for that row, with nothing to delete afterwards. The audit will keep
naming the plant.

**Only those two rejections mean "the slot is taken".** Anything else a write can
fail with — a transaction that cannot be opened, a commit that cannot be made, a
connection that drops — is a *failed write*, and reporting it as
``already_profiled`` would tell an operator the row was fine when it was not. Such
a failure propagates and aborts the migration.

**Idempotent (M-3):** the predicate excludes every plant this migration profiled,
so a second run counts 0 and writes nothing. **Dry-run (M-5):** the full report —
including each planned row and its resolved care style — is computed without a
single write.

**Preconditions.** ``plant_instances``, ``care_profiles``, ``has_care_profile``
and the two catalogue collections ``species`` / ``botanical_families`` are all
created unconditionally by ``ensure_collections`` at bootstrap. An absent one
therefore means a partially bootstrapped or restored database, not an empty one,
and it would change what gets *written*: without the catalogues every plant would
be profiled ``TROPICAL``, irreversibly. So the run reports ``precondition_unmet``
and stays pending for a later boot (``framework/runner.py``, M-1) instead of
being recorded applied over work it did wrong or could not do.

**Not reversible (M-6).** Deleting the profiles again would be indistinguishable
from deleting profiles a user edited in the meantime, and the state restored
would be the defect. Every created row is itemised in ``details["created"]``
(capped; the counts are exact), and the dry-run fills that list identically, so a
run can be read position by position before and after it happens.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.exceptions import DuplicateError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.care_reminder_repository import (
    ArangoCareReminderRepository,
    unprofiled_plant_count_aql,
    unprofiled_plant_keys_aql,
)
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Everything this migration reads from or writes to. All five are in
#: ``DOCUMENT_COLLECTIONS``/``EDGE_COLLECTIONS`` and created unconditionally at
#: bootstrap, so an absence is a partially bootstrapped database — see the module
#: docstring for why that is reported rather than worked around.
REQUIRED_COLLECTIONS: tuple[str, ...] = (
    col.PLANT_INSTANCES,
    col.CARE_PROFILES,
    col.HAS_CARE_PROFILE,
    col.SPECIES,
    col.BOTANICAL_FAMILIES,
)

#: How many ``created`` / ``species_missing`` / ``already_profiled`` rows the
#: report carries verbatim. The ``*_total`` counters are always exact; only the
#: itemised lists are capped, so a large installation cannot turn one report into
#: a memory problem.
_REPORT_SAMPLE_LIMIT = 500


class BackfillMissingCareProfilesMigration(Migration):
    version = "0048"
    name = "backfill_missing_care_profiles"
    description = (
        "Create the CareProfile every plant without one needs, with its species' "
        "family presets, so the nightly care-reminder run can see it (#1444)."
    )
    reversible = False

    # ── reads ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _population_bind_vars() -> dict[str, str]:
        """The two collections the shared predicate binds — one spelling, one place."""
        return {"@plants": col.PLANT_INSTANCES, "@profiles": col.CARE_PROFILES}

    def _count_unprofiled(self, db: StandardDatabase) -> int:
        """How many plants the nightly run cannot see (installation-wide).

        ``scoped=False`` is explicit: a migration has no tenant, it repairs the
        whole installation, and the builder refuses to answer that by default.
        """
        cursor = db.aql.execute(
            unprofiled_plant_count_aql(scoped=False),
            bind_vars=self._population_bind_vars(),
        )
        return int(next(iter(cursor), 0) or 0)

    def _unprofiled_plants(self, db: StandardDatabase, limit: int) -> list[dict[str, Any]]:
        """The plants themselves, through the same predicate that counted them.

        ``limit`` is the count taken immediately before, under the migration lock
        and therefore without a concurrent writer: the listing is the counted
        population, not a sample of it. The projection is small (six scalars per
        plant), so the whole set is held rather than paged — and it *has* to be the
        same builder, because a listing from a second FILTER would backfill a
        population the count never described.
        """
        cursor = db.aql.execute(
            unprofiled_plant_keys_aql(),
            bind_vars={**self._population_bind_vars(), "limit": limit},
        )
        return [dict(row) for row in cursor]

    @staticmethod
    def _species_keys_of(db: StandardDatabase, plant_keys: list[str]) -> dict[str, str]:
        """``plant _key → species_key`` for the plants being backfilled.

        A separate read because the shared listing projection does not carry
        ``species_key`` — and widening that projection would change what the audit
        reports for a question the audit does not ask.
        """
        query = f"FOR p IN {col.PLANT_INSTANCES} FILTER p._key IN @keys RETURN {{key: p._key, species: p.species_key}}"
        return {
            str(row["key"]): str(row["species"] or "") for row in db.aql.execute(query, bind_vars={"keys": plant_keys})
        }

    @staticmethod
    def _species_index(db: StandardDatabase, species_keys: list[str]) -> dict[str, dict[str, str]]:
        """``species _key → {scientific_name, family_key}``, batched into one read."""
        query = (
            f"FOR s IN {col.SPECIES} FILTER s._key IN @keys "
            f"RETURN {{key: s._key, name: s.scientific_name, family: s.family_key}}"
        )
        return {
            str(row["key"]): {"name": str(row["name"] or ""), "family_key": str(row["family"] or "")}
            for row in db.aql.execute(query, bind_vars={"keys": species_keys})
        }

    @staticmethod
    def _family_names(db: StandardDatabase, family_keys: list[str]) -> dict[str, str]:
        """``botanical_families _key → name`` — the value ``FAMILY_CARE_MAP`` is keyed by."""
        query = f"FOR f IN {col.BOTANICAL_FAMILIES} FILTER f._key IN @keys RETURN {{key: f._key, name: f.name}}"
        return {
            str(row["key"]): str(row["name"] or "") for row in db.aql.execute(query, bind_vars={"keys": family_keys})
        }

    # ── entry point ───────────────────────────────────────────────────────────

    def _preconditions_unmet(self, db: StandardDatabase, *, dry_run: bool) -> MigrationReport | None:
        """Refuse to run against a database that is missing what this write needs."""
        missing = [name for name in REQUIRED_COLLECTIONS if not db.has_collection(name)]
        if not missing:
            return None
        logger.warning(
            "backfill_missing_care_profiles_precondition_unmet",
            missing_collections=missing,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=0,
            changed=0,
            dry_run=dry_run,
            precondition_unmet=True,
            details={
                "reason": "required_collections_missing",
                "missing_collections": missing,
                "created": [],
                "created_total": 0,
                "species_missing": [],
                "species_missing_total": 0,
                "family_unresolved": [],
                "family_unresolved_total": 0,
                "already_profiled": [],
                "already_profiled_total": 0,
                "by_care_style": {},
            },
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        unmet = self._preconditions_unmet(db, dry_run=dry_run)
        if unmet is not None:
            return unmet

        pending = self._count_unprofiled(db)
        if pending == 0:
            logger.info("backfill_missing_care_profiles_noop", scanned=0, changed=0, dry_run=dry_run)
            return self._report(dry_run=dry_run, scanned=0, changed=0)

        plants = self._unprofiled_plants(db, pending)
        species_of_plant = self._species_keys_of(db, [str(plant["key"]) for plant in plants])
        species = self._species_index(db, sorted({key for key in species_of_plant.values() if key}))
        families = self._family_names(
            db,
            sorted({entry["family_key"] for entry in species.values() if entry["family_key"]}),
        )

        engine = CareReminderEngine()
        repository = ArangoCareReminderRepository(db)

        created: list[dict[str, Any]] = []
        species_missing: list[dict[str, Any]] = []
        family_unresolved: list[dict[str, Any]] = []
        already_profiled: list[dict[str, Any]] = []
        created_total = 0
        species_missing_total = 0
        family_unresolved_total = 0
        already_profiled_total = 0
        by_care_style: dict[str, int] = {}

        for plant in plants:
            plant_key = str(plant["key"])
            tenant_key = plant.get("tenant_key")
            species_key = species_of_plant.get(plant_key, "")
            record = species.get(species_key) if species_key else None

            species_name: str | None = None
            botanical_family: str | None = None
            if record is None:
                species_missing_total += 1
                self._append(
                    species_missing,
                    {
                        "plant_key": plant_key,
                        "tenant_key": tenant_key,
                        "species_key": species_key or None,
                        "reason": "no_species_key" if not species_key else "species_document_missing",
                    },
                )
            else:
                species_name = record["name"] or None
                family_key = record["family_key"]
                if family_key:
                    # A stored key that names no family document is used verbatim:
                    # it is then either a family NAME (an installation that stores
                    # it that way) or a dangling reference, and both are better
                    # served by trying the value than by silently going tropical.
                    botanical_family = families.get(family_key) or family_key
                    if family_key not in families:
                        family_unresolved_total += 1
                        self._append(
                            family_unresolved,
                            {
                                "plant_key": plant_key,
                                "species_key": species_key,
                                "family_key": family_key,
                            },
                        )

            profile = engine.auto_generate_profile(
                species_name=species_name,
                botanical_family=botanical_family,
                plant_key=plant_key,
            )
            care_style = profile.care_style.value
            by_care_style[care_style] = by_care_style.get(care_style, 0) + 1

            row = {
                "plant_key": plant_key,
                "tenant_key": tenant_key,
                "species_key": species_key or None,
                "species_name": species_name,
                "botanical_family": botanical_family,
                "care_style": care_style,
            }

            if dry_run:
                created_total += 1
                self._append(created, row)
                continue

            outcome = self._persist(repository, profile, plant_key)
            if outcome is None:
                already_profiled_total += 1
                by_care_style[care_style] -= 1
                self._append(
                    already_profiled,
                    {
                        "plant_key": plant_key,
                        "tenant_key": tenant_key,
                        "reason": "profile_edge_already_present",
                    },
                )
                continue

            created_total += 1
            self._append(created, {**row, "profile_key": outcome})

        logger.info(
            "backfill_missing_care_profiles",
            scanned=len(plants),
            changed=created_total,
            species_missing=species_missing_total,
            family_unresolved=family_unresolved_total,
            already_profiled=already_profiled_total,
            dry_run=dry_run,
        )
        return self._report(
            dry_run=dry_run,
            scanned=len(plants),
            changed=created_total,
            created=created,
            created_total=created_total,
            species_missing=species_missing,
            species_missing_total=species_missing_total,
            family_unresolved=family_unresolved,
            family_unresolved_total=family_unresolved_total,
            already_profiled=already_profiled,
            already_profiled_total=already_profiled_total,
            by_care_style={style: count for style, count in sorted(by_care_style.items()) if count},
        )

    # ── the write ─────────────────────────────────────────────────────────────

    @staticmethod
    def _persist(
        repository: ArangoCareReminderRepository,
        profile: CareProfile,
        plant_key: str,
    ) -> str | None:
        """Store profile and edge as the service does; ``None`` **only** when the edge is taken.

        The call is ``get_or_create_profile``'s own. Since #1292 that is a single
        transactional write (``create_linked_profile``) rather than a profile insert
        followed by an edge insert, and this migration follows it for the same reason
        the service does: ``has_care_profile`` is unique on ``_from`` (PR #1486), so
        a plant that already owns an edge — pointing at a profile whose ``plant_key``
        names somebody else, which is exactly how it can sit inside this migration's
        predicate — refuses the insert.

        The rejection now leaves nothing to undo. Before, the profile document had
        already been committed and had to be deleted again on the way out; a
        concurrent nightly run could read it in between through the non-unique
        ``plant_key`` field. The aborted transaction leaves no document at all, so
        the row is left exactly as it was found.
        """
        try:
            stored = repository.create_linked_profile(profile, plant_key)
        # ``as exc`` is not decoration: ``ruff format`` rewrites a parenthesised
        # tuple in a bare ``except`` into the Python-2 spelling this file went red
        # on once already, and the binding prevents that rewrite.
        #
        # EXACTLY these two, and the narrowing is the point (SCR-002).
        # ``WriteConflictError`` (ArangoDB ``1200``) belongs beside ``DuplicateError``
        # (``1210``) because both are the unique ``_from`` index refusing a taken
        # slot — and ``WriteConflictError`` is a domain type, not an ``ArangoError``,
        # so it used to fall through and abort the backfill. ``ArangoError`` itself
        # does NOT belong: it also covers ``TransactionInitError``,
        # ``TransactionCommitError`` and every transport failure, and catching it
        # here counted a write that never happened as ``profile_edge_already_present``
        # — an operator reading the report would have seen a healthy row.
        except (DuplicateError, WriteConflictError) as exc:
            logger.warning(
                "backfill_missing_care_profiles_edge_taken",
                plant_key=plant_key,
                exc_info=exc,
            )
            return None
        # ``stored.key`` is always set — the driver echoes ``_key`` back and
        # ``create_linked_profile`` wraps the returned document — but an empty one
        # would silently take the ``already_profiled`` branch above, which is the
        # same lie in a different spelling. Fail loudly instead.
        if not stored.key:  # pragma: no cover - defensive; see the comment above
            raise RuntimeError(f"care profile for plant {plant_key!r} was stored without a key")
        return stored.key

    # ── report plumbing ───────────────────────────────────────────────────────

    @staticmethod
    def _append(sink: list[dict[str, Any]], row: Mapping[str, Any]) -> None:
        """Append one report row, up to :data:`_REPORT_SAMPLE_LIMIT`."""
        if len(sink) >= _REPORT_SAMPLE_LIMIT:
            return
        sink.append(dict(row))

    def _report(self, *, dry_run: bool, scanned: int, changed: int, **details: Any) -> MigrationReport:
        """One report shape for every exit, so a consumer never has to probe keys."""
        payload: dict[str, Any] = {
            "created": [],
            "created_total": 0,
            "species_missing": [],
            "species_missing_total": 0,
            "family_unresolved": [],
            "family_unresolved_total": 0,
            "already_profiled": [],
            "already_profiled_total": 0,
            "by_care_style": {},
        }
        payload.update(details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            details=payload,
        )


migration = BackfillMissingCareProfilesMigration()
