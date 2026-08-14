"""Seed database with botanical families, common species, cultivars, and default profiles.

All data is loaded from YAML files in the seed_data/ directory.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.dependencies import (
    get_db,
    get_family_repo,
    get_graph_repo,
    get_harvest_repo,
    get_ipm_repo,
    get_lifecycle_repo,
    get_phase_sequence_repo,
    get_species_repo,
    get_task_repo,
)
from app.common.enums import (
    CycleType,
    FloweringStrategy,
    GrowthDeterminacy,
    PhotoperiodType,
    StressTolerance,
)
from app.data_access.arango.phase_sequence_repository import BOUND_BY_SEED
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.harvest import HarvestIndicator
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.species import Species
from app.domain.models.task import TaskTemplate, WorkflowPhase, WorkflowTemplate
from app.migrations.cultivar_seed import build_cultivar, global_cultivars
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _load_families() -> list[BotanicalFamily]:
    """Load botanical families from YAML and construct Pydantic models."""
    data = load_yaml("botanical_families.yaml")
    return [BotanicalFamily.model_validate(f) for f in data["families"]]


def _load_rotation_edges() -> list[tuple[str, str, int, float, str]]:
    """Load rotation edges from YAML."""
    data = load_yaml("botanical_families.yaml")
    return [(e[0], e[1], e[2], e[3], e[4]) for e in data["rotation_edges"]]


def _load_species() -> list[Species]:
    """Load species from YAML and construct Pydantic models."""
    data = load_yaml("species.yaml")
    return [Species.model_validate(s) for s in data["species"]]


def _load_species_family_map() -> dict[str, str]:
    """Build species->family mapping from YAML data."""
    data = load_yaml("species.yaml")
    return {s["scientific_name"]: s["family"] for s in data["species"]}


def _load_cultivars() -> dict[str, list[dict]]:
    """Load cultivar data from YAML."""
    data = load_yaml("species.yaml")
    return data.get("cultivars", {})


def _load_perennial_species() -> set[str]:
    """Load the set of perennial species names."""
    data = load_yaml("species.yaml")
    return set(data.get("perennial_species", []))


def _load_lifecycle_overrides() -> dict[str, dict]:
    """Load per-species lifecycle overrides (cultivation_cycle_type, flowering_strategy)."""
    data = load_yaml("species.yaml")
    return data.get("lifecycle_overrides", {}) or {}


def _load_default_phases() -> list[dict]:
    """Load default growth phases from YAML."""
    data = load_yaml("species.yaml")
    return data.get("default_phases", [])


def _load_companion_planting() -> dict:
    """Load companion planting data from YAML."""
    return load_yaml("companion_planting.yaml")


def _load_ipm_data() -> dict:
    """Load IPM seed data from YAML."""
    return load_yaml("ipm.yaml")


def _load_workflow_data() -> dict:
    """Load workflow and task template data from YAML."""
    return load_yaml("workflows.yaml")


def _load_harvest_indicators() -> list[dict]:
    """Load harvest indicator data from YAML."""
    data = load_yaml("harvest_indicators.yaml")
    return data.get("harvest_indicators", [])


def _enum_value(value: object) -> str | None:
    """Return ``value.value`` for an enum, the string itself, or ``None``."""
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def link_indoor_species_to_phase_sequence() -> None:
    """Bind every indoor species without an edge to its precise phase sequence.

    Attribute-driven fine-typing (REQ-003 D9–D12, audit #576 / #616): the CAM-succulent,
    clonal-monocarp (Kindel), photoperiodic-ornamental and palm/fern/geophyte cohorts are
    routed onto their biologically precise sequence via
    :func:`~app.domain.engines.phase_sequence_resolver.resolve_phase_sequence_name`; every
    remaining perennial lands on ``evergreen_foliage_perennial``; and ``indoor_default`` is
    only the last-resort blanket for annual/biennial species without a better pattern.

    Iterates **all** species (species.yaml base species *and* plant-info species) so the
    resolver — not the blanket — decides. Idempotent: species that already carry a
    HAS_PHASE_SEQUENCE edge (e.g. the explicitly-seeded outdoor lifecycles) are skipped, so
    the resolver never overrides a more-precise binding and a re-run is a no-op.

    The same classifier now also runs at *runtime* — ``SpeciesService.create_species`` and
    the CSV import bind through ``app.domain.services.phase_sequence_binder`` (#1006) — so
    a species minted after seeding is not left unbound the way the identify flow used to
    leave it.
    """
    from app.data_access.arango import collections as col
    from app.domain.engines.cycle_resolver import resolve_effective_cycle
    from app.domain.engines.phase_sequence_resolver import (
        INDOOR_DEFAULT_SEQUENCE,
        resolve_phase_sequence_name,
    )

    ps_repo = get_phase_sequence_repo()
    lifecycle_repo = get_lifecycle_repo()
    species_repo = get_species_repo()
    db = get_db()

    # Resolve the sequence keys once (name -> _key). If the phase sequences have not been
    # seeded yet, nothing can be bound — during the ``core_data`` job on a fresh install
    # that is the normal case, because ``phase_sequences`` is seeded later in the registry.
    #
    # The recovery is the ``lifecycle_to_phase_sequence_reconcile`` job, which is the LAST
    # data job in ``seeds/registry.py`` and calls this function again once every species and
    # every sequence exists — the binding is completed within the same seed run, not on a
    # later boot. ``verify_all_species_bound`` runs at the end of that job and reports at
    # error level if it was not, so this early return can no longer be silent-by-default.
    all_seqs, _ = ps_repo.get_all_sequences(0, 500)
    seq_key_by_name: dict[str, str] = {s.name: (s.key or "") for s in all_seqs}
    indoor_key = seq_key_by_name.get(INDOOR_DEFAULT_SEQUENCE, "")
    if not indoor_key:
        logger.warning(
            "indoor_default_sequence_not_found",
            reason="phase sequences not seeded yet; deferred to the post-seed reconcile job",
            sequences_present=len(seq_key_by_name),
        )
        return

    # Load every species (paginated). ~210 rows — a 1000 page covers it with headroom.
    all_species, _ = species_repo.get_all(0, 1000)

    edge_col = db.collection(col.HAS_PHASE_SEQUENCE)
    linked = 0
    fine_typed = 0

    for sp in all_species:
        sp_key = sp.key or ""
        if not sp_key:
            continue
        species_id = f"{col.SPECIES}/{sp_key}"

        # Skip species that already have an edge (explicit outdoor lifecycles, prior runs).
        existing = list(
            db.aql.execute(
                "FOR e IN @@edge_col FILTER e._from == @from_id LIMIT 1 RETURN 1",
                bind_vars={"@edge_col": col.HAS_PHASE_SEQUENCE, "from_id": species_id},
            )
        )
        if existing:
            continue

        lifecycle = lifecycle_repo.get_lifecycle_by_species(sp_key)
        # Bind on the EFFECTIVE (cultivation-aware) cycle, not the raw botanical one
        # (ADR-006 E1). A tender perennial (tomato) is botanically ``perennial`` but
        # cultivated as an annual (``cultivation_cycle_type=annual``); it must land on
        # ``indoor_default`` (with ripening/harvest), not the harvest-less
        # ``evergreen_foliage_perennial``. Resolve through the ONE SSOT cascade so the
        # linker cannot drift from the restart / season-state consumers.
        effective_cycle = resolve_effective_cycle(None, lifecycle) if lifecycle is not None else None
        target_name = resolve_phase_sequence_name(
            sp.scientific_name,
            cycle_type=_enum_value(effective_cycle),
            flowering_strategy=_enum_value(lifecycle.flowering_strategy) if lifecycle is not None else None,
            photosynthesis_type=_enum_value(sp.photosynthesis_type),
            photoperiod_type=_enum_value(lifecycle.photoperiod_type) if lifecycle is not None else None,
            growth_habit=_enum_value(sp.growth_habit),
        )

        target_key = seq_key_by_name.get(target_name or "", "")
        if target_key:
            fine_typed += 1
        else:
            # ``target_name`` unset → the resolver deliberately chose the blanket for a
            # KNOWN annual/biennial, which is where such a species belongs. ``target_name``
            # set but not found here → the sequence the resolver picked is not seeded, and
            # the species silently lands on an annual harvest cycle instead. That is a
            # seed-data defect, not a routine fallback, so it is logged rather than
            # absorbed (issue #949).
            if target_name:
                logger.warning(
                    "phase_sequence_target_not_seeded",
                    species_key=sp_key,
                    scientific_name=sp.scientific_name,
                    target_sequence=target_name,
                    falling_back_to=INDOOR_DEFAULT_SEQUENCE,
                )
            target_key = indoor_key  # last-resort blanket

        # Provenance (#1146): the reconciler must be able to tell a machine binding
        # it may correct from a human override it must not touch.
        edge_col.insert(
            {
                "_from": species_id,
                "_to": f"{col.PHASE_SEQUENCES}/{target_key}",
                "bound_by": BOUND_BY_SEED,
                "bound_at": datetime.now(UTC).isoformat(),
            }
        )
        linked += 1

    if linked:
        logger.info("indoor_species_linked_to_phase_sequence", count=linked, fine_typed=fine_typed)


def verify_all_species_bound(*, limit: int = 25) -> list[str]:
    """Report species left without a phase sequence after seeding (#1006).

    Called at the end of the ``lifecycle_to_phase_sequence_reconcile`` job — the point
    at which every species and every sequence exists, so "unbound" is a defect rather
    than an ordering artefact.

    Reported at **error** level, not warning: an unbound species produces plants with
    ``current_phase_key: null``, and everything the lifecycle carries hangs off the
    phase. The condition previously had no report at all — the linker's early return
    on a missing ``indoor_default`` was one warning line naming no species, so a run
    that bound nothing looked like a run that had nothing to bind.

    Names the offenders (capped at ``limit``) rather than only counting them, so the
    log answers "which" and not just "how many". Returns the full list of unbound
    scientific names for callers/tests; never raises — a report is not a gate, and
    failing the seed here would take the whole install down for a data gap.
    """
    from app.data_access.arango import collections as col

    db = get_db()
    unbound: list[str] = list(
        db.aql.execute(
            """
            FOR s IN @@species_col
                LET bound = LENGTH(
                    FOR e IN @@edge_col
                        FILTER e._from == CONCAT(@species_prefix, s._key)
                        LIMIT 1
                        RETURN 1
                )
                FILTER bound == 0
                SORT s.scientific_name
                RETURN s.scientific_name
            """,
            bind_vars={
                "@species_col": col.SPECIES,
                "@edge_col": col.HAS_PHASE_SEQUENCE,
                "species_prefix": f"{col.SPECIES}/",
            },
        )
    )

    if unbound:
        logger.error(
            "species_without_phase_sequence_after_seed",
            count=len(unbound),
            species=unbound[:limit],
            truncated=max(0, len(unbound) - limit),
            impact="plants created for these species get current_phase_key=null",
        )
    else:
        logger.info("all_species_bound_to_phase_sequence")
    return unbound


def report_binding_divergence(*, limit: int = 25) -> list[dict[str, str]]:
    """Report species whose stored binding disagrees with the resolver (#1146).

    ``verify_all_species_bound`` above checks **presence**. A species bound to the
    *wrong* sequence passes it — ``Yucca gigantea`` did, while sitting on the
    126-day annual ``indoor_default`` cycle that ``phase_sequence_resolver``'s own
    docstring names as the thing #949 fixed. Fixed in the classifier, not in the
    data.

    **Why the gap exists and cannot close itself.** Both binding paths are
    skip-if-bound — the seed linker (``if existing: continue``) and
    :meth:`PhaseSequenceBinder.bind_default` (``if get_sequence_by_species(...) is
    not None: return None``). Idempotency is the right property for both. The
    problem is that nothing else exists: the only re-homing mechanism is a
    hand-enumerated migration (v0024, v0028, v0029 — and v0039, which this session
    added for exactly one more cohort). So every resolver improvement changes what
    a *newly bound* species gets and leaves every *already bound* species where it
    was, and the two drift apart monotonically with nothing reporting it.

    This is the report half of closing that ratchet. It is deliberately **not** a
    repair: re-homing a species changes plant-visible lifecycle state, so it
    belongs in a versioned migration with a dry-run and a report, not in a job that
    runs on every deployment. What this gives the repair is its work-list — and
    gives an operator the divergence the following boot, instead of at the next
    time someone measures the instance by hand.

    A ``manual`` binding is an override and is excluded, never reported as drift.
    No such edge can exist yet (#1099), which is why the exclusion is written now
    rather than discovered later by a pass that reverts a user's choice.

    Returns ``[{scientific_name, bound_to, resolver_says}]``; never raises.
    """
    from app.data_access.arango import collections as col
    from app.data_access.arango.phase_sequence_repository import BOUND_BY_MANUAL
    from app.domain.engines.cycle_resolver import resolve_effective_cycle
    from app.domain.engines.phase_sequence_resolver import (
        INDOOR_DEFAULT_SEQUENCE,
        resolve_phase_sequence_name,
    )

    db = get_db()
    lifecycle_repo = get_lifecycle_repo()

    rows = list(
        db.aql.execute(
            """
            FOR s IN @@species_col
                FOR e IN @@edge_col
                    FILTER e._from == CONCAT(@species_prefix, s._key)
                    FOR seq IN @@seq_col
                        FILTER seq._id == e._to
                        RETURN {
                            species_key: s._key,
                            scientific_name: s.scientific_name,
                            photosynthesis_type: s.photosynthesis_type,
                            growth_habit: s.growth_habit,
                            bound_to: seq.name,
                            bound_by: e.bound_by
                        }
            """,
            bind_vars={
                "@species_col": col.SPECIES,
                "@edge_col": col.HAS_PHASE_SEQUENCE,
                "@seq_col": col.PHASE_SEQUENCES,
                "species_prefix": f"{col.SPECIES}/",
            },
        )
    )

    diverging: list[dict[str, str]] = []
    for row in rows:
        if row.get("bound_by") == BOUND_BY_MANUAL:
            continue
        lifecycle = lifecycle_repo.get_lifecycle_by_species(row["species_key"])
        effective_cycle = resolve_effective_cycle(None, lifecycle) if lifecycle is not None else None
        target = resolve_phase_sequence_name(
            row.get("scientific_name") or "",
            cycle_type=_enum_value(effective_cycle),
            flowering_strategy=_enum_value(lifecycle.flowering_strategy) if lifecycle is not None else None,
            photosynthesis_type=_enum_value(row.get("photosynthesis_type")),
            photoperiod_type=_enum_value(lifecycle.photoperiod_type) if lifecycle is not None else None,
            growth_habit=_enum_value(row.get("growth_habit")),
        )
        # ``None`` means "the resolver deliberately chose the blanket", which is what
        # both binding paths translate to `indoor_default`. Comparing the raw None
        # against a stored name would report every annual as diverging.
        expected = target or INDOOR_DEFAULT_SEQUENCE
        if row.get("bound_to") != expected:
            diverging.append(
                {
                    "scientific_name": row.get("scientific_name") or "",
                    "bound_to": row.get("bound_to") or "",
                    "resolver_says": expected,
                }
            )

    diverging.sort(key=lambda d: d["scientific_name"])
    if diverging:
        logger.error(
            "phase_sequence_binding_diverges_from_resolver",
            count=len(diverging),
            species=diverging[:limit],
            truncated=max(0, len(diverging) - limit),
            impact="these species are scheduled on a lifecycle the resolver would not give them today",
        )
    else:
        logger.info("all_phase_sequence_bindings_match_the_resolver")
    return diverging


def seed_cultivars(
    species_repo: ISpeciesRepository,
    cultivar_data: dict[str, list[dict[str, Any]]],
    species_key_map: dict[str, str],
) -> None:
    """Upsert the YAML cultivar catalogue as *global* rows, name-matched per species.

    The seed writes the shared catalogue every tenant reads, so it matches only
    against the **global** rows (``tenant_key == ""``) — never a tenant-owned one
    (#1090). The match universe comes from the shared
    :func:`~app.migrations.cultivar_seed.global_cultivars`, which documents why:
    matching a tenant's same-named row would rewrite that record from the YAML
    entry — replacing their field values and, without the repository's ownership
    guard, reassigning the row to the global catalogue — while skipping the entry
    would deny the shared catalogue to every other tenant. The three
    skip-if-exists sibling loaders apply the identical rule through the same helper
    (SEC-002), so no seeder can answer the ownership question differently.

    What is *not* shared is the policy on a match: this loader upserts (the global
    catalogue must track the YAML), while the siblings skip.

    Extracted from :func:`run_seed` so the upsert rule is reachable by a test
    without standing up the whole seed run.
    """
    for sci_name, cv_list in cultivar_data.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("cultivar_species_not_found", species=sci_name)
            continue
        existing_cv_map = {c.name: c for c in global_cultivars(species_repo, sp_key)}
        for cv_data in cv_list:
            cultivar = build_cultivar(cv_data, sp_key)
            found_cv = existing_cv_map.get(cv_data["name"])
            if found_cv:
                species_repo.update_cultivar(found_cv.key or "", cultivar)
                logger.info("cultivar_upserted", species=sci_name, cultivar=cv_data["name"])
            else:
                species_repo.create_cultivar(cultivar)
                logger.info("cultivar_created", species=sci_name, cultivar=cv_data["name"])


def run_seed() -> None:  # noqa: C901, PLR0912, PLR0915
    """Seed all reference data into the database. Idempotent (upsert behavior)."""
    # ── Seed location types (REQ-002) — delegated to startup module ──
    from app.migrations.seed_location_types import seed_location_types

    db = get_family_repo()._db  # reuse connection
    seed_location_types(db)

    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    # ── Load data from YAML ──────────────────────────────────────────
    families = _load_families()
    rotation_edges = _load_rotation_edges()
    species_list = _load_species()
    family_species_map = _load_species_family_map()
    cultivar_data = _load_cultivars()
    perennial_species = _load_perennial_species()
    lifecycle_overrides = _load_lifecycle_overrides()
    default_phases = _load_default_phases()
    profile_gen = ResourceProfileGenerator.from_yaml_phases(default_phases)
    companion_data = _load_companion_planting()
    ipm_data = _load_ipm_data()
    workflow_data = _load_workflow_data()
    harvest_indicator_data = _load_harvest_indicators()

    # ── Seed families (upsert) ───────────────────────────────────────
    family_map: dict[str, str] = {}
    for family in families:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            family_repo.update_family(existing.key or "", family)
            logger.info("family_updated", name=family.name)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name)

    # ── Seed rotation edges ──────────────────────────────────────────
    for from_name, to_name, wait_years, benefit_score, benefit_reason in rotation_edges:
        from_key = family_map.get(from_name, "")
        to_key = family_map.get(to_name, "")
        if from_key and to_key:
            try:
                graph_repo.set_rotation_successor(
                    from_key,
                    to_key,
                    wait_years,
                    benefit_score=benefit_score,
                    benefit_reason=benefit_reason,
                )
                logger.info("rotation_edge_created", from_family=from_name, to_family=to_name)
            except Exception:
                logger.info("rotation_edge_exists", from_family=from_name, to_family=to_name)

    # ── Seed family-level edges ──────────────────────────────────────
    for edge in companion_data.get("family_pest_risk", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_pest_risk(
                    a_key,
                    b_key,
                    edge["shared_pests"],
                    edge["shared_diseases"],
                    edge["risk_level"],
                )
                logger.info("pest_risk_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("pest_risk_edge_exists", a=edge["family_a"], b=edge["family_b"])

    for edge in companion_data.get("family_compatible", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_family_compatible(
                    a_key,
                    b_key,
                    edge["benefit_type"],
                    edge["score"],
                    edge["notes"],
                )
                logger.info("family_compatible_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("family_compatible_edge_exists", a=edge["family_a"], b=edge["family_b"])

    for edge in companion_data.get("family_incompatible", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_family_incompatible(
                    a_key,
                    b_key,
                    edge["reason"],
                    edge["severity"],
                )
                logger.info("family_incompatible_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("family_incompatible_edge_exists", a=edge["family_a"], b=edge["family_b"])

    # ── Seed species ─────────────────────────────────────────────────
    seed_update_fields = (
        "sowing_indoor_weeks_before_last_frost",
        "sowing_outdoor_after_last_frost_days",
        "direct_sow_months",
        "harvest_months",
        "bloom_months",
        "frost_sensitivity",
        "allows_harvest",
        "growing_periods",
        "container_suitable",
        "recommended_container_volume_l",
        "min_container_depth_cm",
        "mature_height_cm",
        "mature_width_cm",
        "spacing_cm",
        "indoor_suitable",
        "balcony_suitable",
        "greenhouse_recommended",
        "support_required",
        # Plant-properties fields (WP-5 / Phase A / WP-10) — keep existing rows in
        # sync on re-seed, otherwise species.yaml species never receive them.
        "growth_habit",
        "propagation_configs",
        "harvest_pattern",
        "harvested_part",
        "climacteric",
    )

    species_key_map: dict[str, str] = {}

    for sp in species_list:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            # Update seed fields if they changed
            needs_update = False
            for field in seed_update_fields:
                if getattr(sp, field) != getattr(existing, field):
                    needs_update = True
                    break
            if needs_update:
                for field in seed_update_fields:
                    setattr(existing, field, getattr(sp, field))
                species_repo.update(existing.key or "", existing)
                logger.info("species_updated", name=sp.scientific_name)
            else:
                logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = family_species_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        # REQ-048 Stufe 1 / SEC-003: route the insert through the atomic dedup
        # UPSERT so a stored normalized-duplicate (× vs x, casing, whitespace)
        # missed by the exact-name lookup resolves onto the existing record
        # instead of minting a second row.
        created_sp = species_repo.upsert_by_normalized_scientific_name(sp)
        species_key = created_sp.key or ""
        species_key_map[sp.scientific_name] = species_key
        logger.info("species_created", name=sp.scientific_name, key=species_key)

        # Create lifecycle — perennials get PERENNIAL cycle type
        cycle = CycleType.PERENNIAL if sp.scientific_name in perennial_species else CycleType.ANNUAL
        ov = lifecycle_overrides.get(sp.scientific_name, {})
        cult_cycle = ov.get("cultivation_cycle_type")
        flower_strat = ov.get("flowering_strategy")
        determinacy = ov.get("growth_determinacy")
        lc = LifecycleConfig(
            species_key=species_key,
            cycle_type=cycle,
            cultivation_cycle_type=CycleType(cult_cycle) if cult_cycle else None,
            flowering_strategy=FloweringStrategy(flower_strat) if flower_strat else None,
            growth_determinacy=GrowthDeterminacy(determinacy) if determinacy else None,
            photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        )
        created_lc = lifecycle_repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        # Create default phases with profiles
        for phase_data in default_phases:
            phase = GrowthPhase(
                name=phase_data["name"],
                display_name=phase_data["display_name"],
                lifecycle_key=lc_key,
                typical_duration_days=phase_data["typical_duration_days"],
                sequence_order=phase_data["sequence_order"],
                is_terminal=phase_data["is_terminal"],
                allows_harvest=phase_data["allows_harvest"],
                stress_tolerance=StressTolerance(phase_data["stress_tolerance"]),
                watering_interval_days=phase_data.get("watering_interval_days"),
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req = profile_gen.generate_requirement_profile(phase_data["name"], phase_key)
            lifecycle_repo.create_requirement_profile(req)

            nut = profile_gen.generate_nutrient_profile(phase_data["name"], phase_key)
            lifecycle_repo.create_nutrient_profile(nut)

            logger.info("phase_created", species=sp.scientific_name, phase=phase_data["name"])

    # ── Link indoor species to their (attribute-resolved) PhaseSequence ─────
    # No-op on the very first boot (phase_sequences seed later in the registry);
    # the post-seed reconcile step and subsequent boots complete the linking.
    link_indoor_species_to_phase_sequence()

    # ── Seed cultivars ───────────────────────────────────────────────
    seed_cultivars(species_repo, cultivar_data, species_key_map)

    # ── Seed companion planting edges (species-level) ────────────────
    for entry in companion_data.get("compatible", []):
        a_sci, b_sci, score = entry[0], entry[1], entry[2]
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_compatibility(a_key, b_key, score)
                logger.info("companion_compatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_compatible_exists", a=a_sci, b=b_sci)

    for entry in companion_data.get("incompatible", []):
        a_sci = entry["species_a"]
        b_sci = entry["species_b"]
        reason = entry["reason"]
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_incompatibility(a_key, b_key, reason)
                logger.info("companion_incompatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_incompatible_exists", a=a_sci, b=b_sci)

    # ── Seed IPM data (REQ-010) ──────────────────────────────────────
    ipm_repo = get_ipm_repo()
    existing_pests, _ = ipm_repo.get_all_pests(0, 200)
    existing_pest_map = {p.scientific_name: p for p in existing_pests}

    pest_key_map: dict[str, str] = {}
    for pest_data in ipm_data.get("pests", []):
        pest = Pest.model_validate(pest_data)
        found = existing_pest_map.get(pest.scientific_name)
        if found:
            pest_key_map[pest.common_name] = found.key or ""
            ipm_repo.update_pest(found.key or "", pest)
            logger.info("pest_upserted", name=pest.common_name)
        else:
            created = ipm_repo.create_pest(pest)
            pest_key_map[pest.common_name] = created.key or ""
            logger.info("pest_created", name=pest.common_name)

    existing_diseases, _ = ipm_repo.get_all_diseases(0, 200)
    existing_disease_map = {d.scientific_name: d for d in existing_diseases}

    disease_key_map: dict[str, str] = {}
    for disease_data in ipm_data.get("diseases", []):
        disease = Disease.model_validate(disease_data)
        found = existing_disease_map.get(disease.scientific_name)
        if found:
            disease_key_map[disease.common_name] = found.key or ""
            ipm_repo.update_disease(found.key or "", disease)
            logger.info("disease_upserted", name=disease.common_name)
        else:
            created = ipm_repo.create_disease(disease)
            disease_key_map[disease.common_name] = created.key or ""
            logger.info("disease_created", name=disease.common_name)

    existing_treatments, _ = ipm_repo.get_all_treatments(0, 200)
    existing_treatment_map = {t.name: t for t in existing_treatments}

    treatment_key_map: dict[str, str] = {}
    for treatment_data in ipm_data.get("treatments", []):
        treatment = Treatment.model_validate(treatment_data)
        found = existing_treatment_map.get(treatment.name)
        if found:
            treatment_key_map[treatment.name] = found.key or ""
            ipm_repo.update_treatment(found.key or "", treatment)
            logger.info("treatment_upserted", name=treatment.name)
        else:
            created = ipm_repo.create_treatment(treatment)
            treatment_key_map[treatment.name] = created.key or ""
            logger.info("treatment_created", name=treatment.name)

    for entry in ipm_data.get("pest_treatments", []):
        treat_name, pest_name = entry[0], entry[1]
        t_key = treatment_key_map.get(treat_name, "")
        p_key = pest_key_map.get(pest_name, "")
        if t_key and p_key:
            try:
                ipm_repo.create_targets_pest_edge(t_key, p_key)
                logger.info("targets_pest_edge", treatment=treat_name, pest=pest_name)
            except Exception:
                logger.info("targets_pest_edge_exists", treatment=treat_name, pest=pest_name)

    for entry in ipm_data.get("disease_treatments", []):
        treat_name, disease_name = entry[0], entry[1]
        t_key = treatment_key_map.get(treat_name, "")
        d_key = disease_key_map.get(disease_name, "")
        if t_key and d_key:
            try:
                ipm_repo.create_targets_disease_edge(t_key, d_key)
                logger.info("targets_disease_edge", treatment=treat_name, disease=disease_name)
            except Exception:
                logger.info("targets_disease_edge_exists", treatment=treat_name, disease=disease_name)

    for entry in ipm_data.get("contraindications", []):
        a_name, b_name = entry[0], entry[1]
        a_key = treatment_key_map.get(a_name, "")
        b_key = treatment_key_map.get(b_name, "")
        if a_key and b_key:
            try:
                ipm_repo.create_contraindicated_edge(a_key, b_key)
                logger.info("contraindicated_edge", a=a_name, b=b_name)
            except Exception:
                logger.info("contraindicated_edge_exists", a=a_name, b=b_name)

    # ── Seed beneficials (REQ-044 WP-8) ──────────────────────────────
    from app.common.dependencies import get_pest_detection_repo
    from app.domain.models.beneficial import Beneficial
    from app.domain.models.pest_taxonomy import beneficial_taxa

    pest_detection_repo = get_pest_detection_repo()
    for taxon in beneficial_taxa():
        beneficial = Beneficial(
            slug=taxon.slug,
            common_name=taxon.common_name_de,
            scientific_name=taxon.scientific_name,
            gbif_taxon_key=taxon.gbif_taxon_key,
            preys_on=list(taxon.preys_on),
        )
        try:
            pest_detection_repo.upsert_beneficial(beneficial)
            logger.info("beneficial_upserted", slug=taxon.slug)
        except Exception:
            logger.info("beneficial_seed_skipped", slug=taxon.slug)

    # ── Seed Harvest indicators (REQ-007) ────────────────────────────
    harvest_repo = get_harvest_repo()
    for ind_data in harvest_indicator_data:
        sp_key = species_key_map.get(ind_data["species_name"], "")
        indicator = HarvestIndicator(
            indicator_type=ind_data["indicator_type"],
            measurement_unit=ind_data["measurement_unit"],
            measurement_method=ind_data["measurement_method"],
            observation_frequency=ind_data["observation_frequency"],
            reliability_score=ind_data["reliability_score"],
            species_key=sp_key or None,
        )
        try:
            harvest_repo.create_indicator(indicator)
            logger.info("harvest_indicator_created", type=ind_data["indicator_type"], species=ind_data["species_name"])
        except Exception:
            logger.info("harvest_indicator_exists", type=ind_data["indicator_type"], species=ind_data["species_name"])

    # ── Deduplicate task templates (one-time cleanup) ────────────────
    from app.data_access.arango import collections as seed_col

    tt_col = db.collection(seed_col.TASK_TEMPLATES)
    dedup_query = (
        f"FOR doc IN {seed_col.TASK_TEMPLATES} "
        f"COLLECT name = doc.name, wfk = doc.workflow_template_key INTO group "
        f"LET docs = group[*].doc "
        f"FILTER LENGTH(docs) > 1 "
        f"LET to_remove = SLICE(docs, 1) "
        f"FOR d IN to_remove RETURN d._key"
    )
    dup_keys = list(db.aql.execute(dedup_query))
    if dup_keys:
        for dk in dup_keys:
            tt_col.delete(dk)
        logger.info("task_template_duplicates_removed", count=len(dup_keys))

    # ── Seed Workflow templates + Task templates (REQ-006) ───────────
    task_repo = get_task_repo()
    existing_wfs, _ = task_repo.get_all_workflow_templates(0, 200)
    existing_wf_map = {w.name: w for w in existing_wfs}
    wf_key_map: dict[str, str] = {}

    for wt_data in workflow_data.get("workflow_templates", []):
        wt = WorkflowTemplate.model_validate(wt_data)
        found = existing_wf_map.get(wt.name)
        if found:
            wf_key_map[wt.name] = found.key or ""
            task_repo.update_workflow_template(found.key or "", wt)
            logger.info("workflow_template_upserted", name=wt.name)
        else:
            created = task_repo.create_workflow_template(wt)
            wf_key_map[wt.name] = created.key or ""
            logger.info("workflow_template_created", name=wt.name)

    # Seed workflow phases
    phase_key_map: dict[str, dict[str, str]] = {}  # {wf_key: {phase_name: phase_key}}
    for ph_data in workflow_data.get("workflow_phases", []):
        wf_name = ph_data["workflow_name"]
        wf_key = wf_key_map.get(wf_name, "")
        if not wf_key:
            continue
        phase = WorkflowPhase(
            name=ph_data["name"],
            workflow_template_key=wf_key,
            phase_order=ph_data.get("phase_order", 0),
            duration_days=ph_data.get("duration_days", 0),
            stress_tolerance=ph_data.get("stress_tolerance", ""),
            trigger_phase=ph_data.get("trigger_phase"),
        )
        existing_phases = task_repo.get_phases_for_workflow(wf_key)
        found_phase = next((p for p in existing_phases if p.name == ph_data["name"]), None)
        if found_phase:
            task_repo.update_phase(found_phase.key or "", phase)
            phase_key_map.setdefault(wf_key, {})[ph_data["name"]] = found_phase.key or ""
            logger.info("workflow_phase_upserted", name=ph_data["name"], workflow=wf_name)
        else:
            created_phase = task_repo.create_phase(phase)
            phase_key_map.setdefault(wf_key, {})[ph_data["name"]] = created_phase.key or ""
            logger.info("workflow_phase_created", name=ph_data["name"], workflow=wf_name)

    # Build lookup of existing task templates per workflow
    existing_tt_map: dict[str, dict[str, TaskTemplate]] = {}
    for _wf_name, wf_key in wf_key_map.items():
        existing_tts = task_repo.get_task_templates_for_workflow(wf_key)
        existing_tt_map[wf_key] = {tt.name: tt for tt in existing_tts}

    for tt_data in workflow_data.get("task_templates", []):
        wf_name = tt_data["workflow_name"]
        wf_key = wf_key_map.get(wf_name, "")
        if not wf_key:
            continue
        # Resolve workflow_phase_key from phase_name
        phase_name = tt_data.get("phase_name") or tt_data.get("trigger_phase")
        wf_phase_key = phase_key_map.get(wf_key, {}).get(phase_name or "") if phase_name else None
        tt = TaskTemplate(
            name=tt_data["name"],
            instruction=tt_data["instruction"],
            category=tt_data["category"],
            trigger_type=tt_data["trigger_type"],
            trigger_phase=tt_data.get("trigger_phase"),
            workflow_phase_key=wf_phase_key,
            days_offset=tt_data["days_offset"],
            stress_level=tt_data["stress_level"],
            estimated_duration_minutes=tt_data["estimated_duration_minutes"],
            requires_photo=tt_data["requires_photo"],
            skill_level=tt_data["skill_level"],
            workflow_template_key=wf_key,
            sequence_order=tt_data["sequence_order"],
            timer_duration_seconds=tt_data.get("timer_duration_seconds"),
            timer_label=tt_data.get("timer_label"),
        )
        found_tt = existing_tt_map.get(wf_key, {}).get(tt_data["name"])
        if found_tt:
            task_repo.update_task_template(found_tt.key or "", tt)
            logger.info("task_template_upserted", name=tt_data["name"], workflow=wf_name)
        else:
            task_repo.create_task_template(tt)
            logger.info("task_template_created", name=tt_data["name"], workflow=wf_name)

    logger.info("seed_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed()
