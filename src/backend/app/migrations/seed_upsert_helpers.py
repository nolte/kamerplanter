"""Shared upsert helpers for seed scripts.

Provides common functions for upserting fertilizers, nutrient plans,
and phase entries so all seed scripts consistently sync YAML → DB.
"""

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.exceptions import DuplicateError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: The seed files that ship fertilizer products (the plan-only files carry none).
_FERTILIZER_SEED_FILES = ("fertilizers.yaml", "plagron.yaml", "gardol.yaml")


def global_fertilizer_map(fert_repo: ArangoFertilizerRepository) -> dict[tuple[str, str], Fertilizer]:
    """``(product_name, brand) → global fertilizer`` — the seed-match universe (#2000).

    Global rows only (``tenant_key`` empty or absent), the whole catalogue, through
    :meth:`ArangoFertilizerRepository.get_global_fertilizers`. The loaders used to
    match over ``get_all(offset=0, limit=1000, all_tenants=True)``: a tenant's own
    product with a seed's ``(product_name, brand)`` was found, rewritten from the seed
    model as global and overwritten; and past row 1000 a seed was treated as missing.
    The first row per identity wins; the rows come ordered by ``_key``.
    """
    rows: dict[tuple[str, str], Fertilizer] = {}
    for fert in fert_repo.get_global_fertilizers():
        rows.setdefault((fert.product_name, fert.brand), fert)
    return rows


def global_fertilizer_keys(fert_repo: ArangoFertilizerRepository) -> dict[str, str]:
    """``product_name → key`` over the global fertilizers, for a plan seed's dosages (#2000).

    A seed plan is global, so a dosage it names must resolve to a global product —
    never to a tenant's private one that happens to share the name (which every other
    tenant would then see referenced by key in a shared plan).

    A plan's dosage names a product by ``product_name`` alone, and two global products
    may share a name under different brands. The product the seed files themselves
    ship under that name wins — ``(product_name, brand)`` as ``fertilizers.yaml``,
    ``plagron.yaml`` and ``gardol.yaml`` give it; only a name no seed file ships falls
    back to the first row by ``_key``. Without that, a global "CalMag" of another brand
    with a lower ``_key`` (one created before the seed product) took the dosage.
    """
    seeded = seed_fertilizer_identities()
    rows = [fert for fert in fert_repo.get_global_fertilizers() if fert.key]
    keys: dict[str, str] = {}
    for fert in sorted(rows, key=lambda f: (f.product_name, f.brand) not in seeded):
        keys.setdefault(fert.product_name, fert.key or "")
    return keys


def seed_fertilizer_identities() -> frozenset[tuple[str, str]]:
    """``(product_name, brand)`` of every fertilizer the seed files ship."""
    pairs = (
        (entry["product_name"], entry.get("brand", ""))
        for name in _FERTILIZER_SEED_FILES
        for entry in load_yaml(name).get("fertilizers", [])
    )
    return frozenset(pairs)


def upsert_fertilizers(
    fert_repo: ArangoFertilizerRepository,
    fertilizers: list[Fertilizer],
) -> dict[str, str]:
    """Upsert fertilizers among the global rows: update existing, create new.

    Returns the ``product_name → key`` map of the rows written. Only a global row is
    ever matched (:func:`global_fertilizer_map`); a tenant's same-named product is
    neither found nor touched. The unique index is ``(tenant_key, product_name,
    brand)`` since v0069, so the global seed row and a tenant's own product of the
    same name coexist.

    A create that the unique index refuses means another process (a second replica
    booting at the same time) wrote the same global row between the read and the
    insert: the row is re-read and updated instead, so concurrent boots converge on
    one row rather than failing the job.
    """
    existing_map = global_fertilizer_map(fert_repo)

    fert_keys: dict[str, str] = {}
    for fert in fertilizers:
        found = existing_map.get((fert.product_name, fert.brand))
        if found is None:
            try:
                created = fert_repo.create(fert)
            except (DuplicateError, WriteConflictError) as exc:
                found = global_fertilizer_map(fert_repo).get((fert.product_name, fert.brand))
                if found is None:
                    raise
                logger.info(
                    "fertilizer_created_concurrently",
                    name=fert.product_name,
                    brand=fert.brand,
                    refused_with=type(exc).__name__,
                )
            else:
                fert_keys[fert.product_name] = created.key or ""
                logger.info("fertilizer_created", name=fert.product_name, brand=fert.brand)
                continue
        fert_keys[fert.product_name] = found.key or ""
        fert.key = found.key
        fert_repo.update(found.key or "", fert)
        logger.info("fertilizer_upserted", name=fert.product_name, brand=fert.brand)

    return fert_keys


def load_species_key_map(db: StandardDatabase) -> dict[str, str]:
    """``scientific_name → _key`` over the species catalogue (#1618).

    No tenant filter, deliberately: ``species.scientific_name`` carries a
    collection-wide unique index (``ensure_collections``), so a seeded name
    resolves to exactly one row, and that row is the global seed species — the
    species seeds run before the plan seeds in the registry.
    """
    if not db.has_collection(col.SPECIES):
        return {}
    cursor = db.aql.execute(
        """
        FOR s IN @@species
            RETURN { name: s.scientific_name, key: s._key }
        """,
        bind_vars={"@species": col.SPECIES},
    )
    return {row["name"]: row["key"] for row in cursor}


def resolve_plan_species_keys(
    species_names: list[str],
    species_key_map: dict[str, str],
    *,
    plan_name: str,
) -> list[str]:
    """Resolve a seed plan's ``species_names`` to species keys (#1618).

    ``species_names`` are scientific names taken from the plan's source document
    (``spec/knowledge/nutrient-plans/*.md``, "Pflanze:"), never guessed from its
    name or tags; a plan whose source names no species carries none and matches
    no species in the onboarding wizard. A name the catalogue does not hold is
    logged and skipped — the unit guard
    ``test_seed_plan_species_names_resolve`` keeps that at zero for the shipped
    seed files.
    """
    keys: list[str] = []
    for name in species_names:
        key = species_key_map.get(name)
        if key is None:
            logger.warning("seed_plan_species_not_found", plan=plan_name, species=name)
            continue
        if key not in keys:
            keys.append(key)
    return keys


def global_plan_map(plan_repo: ArangoNutrientPlanRepository) -> dict[str, NutrientPlan]:
    """``name → global plan`` for the nutrient-plan seed loaders (#1957).

    A seed is matched to a row only when that row is global (``tenant_key`` empty),
    through :meth:`ArangoNutrientPlanRepository.get_global_plans`: not a paged
    ``get_all`` (a fixed ``limit`` cut the catalogue and re-created a seed beyond
    it on every boot) and not across tenants (``nutrient_plans.name`` is not
    unique, so a tenant's own plan named like a seed was found by name, rewritten
    from the seed model as global, and stripped of the phase entries the YAML does
    not carry). The first row per name wins; the rows come ordered by ``_key``.
    """
    plans: dict[str, NutrientPlan] = {}
    for plan in plan_repo.get_global_plans():
        plans.setdefault(plan.name, plan)
    return plans


def upsert_nutrient_plan_with_entries(
    plan_repo: ArangoNutrientPlanRepository,
    plan: NutrientPlan,
    desired_entries: list[NutrientPlanPhaseEntry],
    existing_plan_map: dict[str, Any],
    *,
    species_keys: list[str],
) -> str:
    """Upsert a nutrient plan and its phase entries. Returns the plan key.

    ``species_keys`` is the plan's species relation (#1618), resolved by
    :func:`resolve_plan_species_keys`. Keyword-only with no default so a seed
    loader cannot upsert a plan without deciding its relation (#948 drift
    class); the seed is the source of truth for it and overwrites it on every run.
    """
    plan.species_keys = list(species_keys)
    if plan.name in existing_plan_map:
        existing = existing_plan_map[plan.name]
        plan_key = existing.key or ""

        # Upsert plan metadata
        plan.key = existing.key
        plan_repo.update(plan_key, plan)
        logger.info("plan_upserted", name=plan.name)

        # Upsert phase entries
        existing_entries = plan_repo.get_phase_entries(plan_key)
        existing_by_seq = {e.sequence_order: e for e in existing_entries}
        desired_seqs = {e.sequence_order for e in desired_entries}

        for entry in desired_entries:
            entry.plan_key = plan_key
            dosage_count = sum(len(ch.fertilizer_dosages) for ch in entry.delivery_channels)
            if entry.sequence_order in existing_by_seq:
                existing_entry = existing_by_seq[entry.sequence_order]
                plan_repo.update_phase_entry(existing_entry.key or "", entry)
                logger.info(
                    "phase_entry_upserted",
                    plan=plan.name,
                    phase=entry.phase_name,
                    seq=entry.sequence_order,
                    dosages=dosage_count,
                )
            else:
                created_entry = plan_repo.create_phase_entry(entry)
                logger.info(
                    "phase_entry_created",
                    plan=plan.name,
                    phase=entry.phase_name,
                    seq=entry.sequence_order,
                    dosages=dosage_count,
                    key=created_entry.key,
                )

        # Remove entries from DB that are no longer in YAML
        for seq, existing_entry in existing_by_seq.items():
            if seq not in desired_seqs:
                plan_repo.delete_phase_entry(existing_entry.key or "")
                logger.info("phase_entry_removed", plan=plan.name, seq=seq)
    else:
        created_plan = plan_repo.create(plan)
        plan_key = created_plan.key or ""
        logger.info("plan_created", name=plan.name, key=plan_key)

        for entry in desired_entries:
            entry.plan_key = plan_key
            dosage_count = sum(len(ch.fertilizer_dosages) for ch in entry.delivery_channels)
            created_entry = plan_repo.create_phase_entry(entry)
            logger.info(
                "phase_entry_created",
                plan=plan.name,
                phase=entry.phase_name,
                week=f"{entry.week_start}-{entry.week_end}",
                dosages=dosage_count,
                key=created_entry.key,
            )

    return plan_key
