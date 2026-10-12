from collections.abc import Callable
from datetime import UTC, datetime
from itertools import batched
from typing import Any

import structlog

from app.common.dependencies import (
    get_lifecycle_repo,
    get_phase_service,
    get_plant_repo,
    get_site_repo,
    get_tenant_repo,
)
from app.common.enums import CycleType, LightType, TenantStatus, TransitionTrigger, TransitionTriggerType
from app.common.log_privacy import loggable_error
from app.domain.calculators.photoperiod_calculator import effective_light_hours
from app.domain.calculators.sun_calculator import calculate_sun_times
from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.engines.cyclic_lifecycle_engine import CyclicLifecycleEngine
from app.domain.engines.transition_trigger_evaluator import TransitionTriggerEvaluator
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase import PhaseTransitionRule
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site, Slot
from app.domain.services.location_ownership import SiteAnchorSource, find_owned_location
from app.domain.services.phase_service import PhaseService, SequenceAutoTarget
from app.tasks import celery_app

logger = structlog.get_logger()

#: Plants per evaluation batch — the walk's own page size, so one batch is one page
#: of the keyset walk and the batched reads cover exactly what the walk holds.
_PAGE_SIZE = 1000


def _day_length_for_plant(plant, site_repo) -> float | None:
    """Effective photoperiod (hours of light) for the plant's transition trigger.

    Resolves the indoor grow-light schedule (REQ-018) first: an artificially lit
    Location provides a fixed photoperiod the plant actually experiences, unlike
    the astronomical day length. Falls back to the outdoor GPS/sun path when the
    location has no usable artificial schedule (or none is set). Returns ``None``
    when neither source yields a value (the photoperiod trigger is then skipped).
    """
    indoor = _indoor_light_hours_for_plant(plant, site_repo)
    if indoor is not None:
        return indoor
    return _outdoor_day_length_for_plant(plant, site_repo)


def _indoor_light_hours_for_plant(plant, site_repo) -> float | None:
    """Light-on hours from a usable artificial schedule on the plant's Location.

    A schedule is "usable" when the location uses an artificial light source
    (``light_type != NATURAL``), has ``use_dynamic_sunrise`` disabled (a
    sun-tracking schedule is treated as outdoor and falls through), and yields a
    parseable ``lights_on``/``lights_off`` duration. Returns ``None`` otherwise
    so the caller falls back to the outdoor path.
    """
    location_key = getattr(plant, "location_key", None)
    if not location_key:
        return None
    plant_tenant = getattr(plant, "tenant_key", None)
    # get_location_by_key is not tenant-scoped and this system task iterates all
    # tenants (SEC-B4). Only trust a location that belongs to the plant's tenant.
    #
    # Anchored on the parent site (#1397). The previous form carried
    # ``and location.tenant_key and`` in the middle, and that field is persisted
    # empty on every row — so the condition short-circuited and the guard trusted
    # every location it was handed, which is the opposite of what it says.
    location = (
        find_owned_location(site_repo, location_key, plant_tenant)
        if plant_tenant
        else site_repo.get_location_by_key(location_key)
    )
    if location is None:
        return None
    if location.light_type == LightType.NATURAL or location.use_dynamic_sunrise:
        return None
    return effective_light_hours(location.lights_on, location.lights_off)


def _outdoor_day_length_for_plant(plant, site_repo) -> float | None:
    """Astronomical day length (hours) for the plant's outdoor GPS site, or None
    when no site / GPS is known (the photoperiod trigger is then skipped)."""
    if not plant.site_key:
        return None
    site = site_repo.get_site_by_key(plant.site_key)
    if site is None or site.gps_coordinates is None:
        return None
    lat, lon = site.gps_coordinates
    times = calculate_sun_times(lat, lon, datetime.now(UTC).date(), site.timezone)
    return float(times["day_length_hours"])


def _should_restart_cycle(
    cyclic, lifecycle, cycle_number: int, phase_name: str, effective_cycle: CycleType | None
) -> tuple[bool, str]:
    """WP-2/E1 — whether a PhaseSequence-driven plant restarts its cycle out of the
    terminal phase, honouring the per-instance effective cycle (ADR-006 E1).

    An instance grown as an annual (``effective_cycle == ANNUAL``) never loops, even
    on a perennial species. Otherwise it delegates to
    :meth:`CyclicLifecycleEngine.should_restart_cycle` when a LifecycleConfig is
    present (so a biennial ``max_seasons`` / monocarpic lifecycle terminates instead
    of looping); without a LifecycleConfig the sequence's own ``is_repeating`` gate —
    already applied when the restart target was resolved — governs, so the restart is
    allowed."""
    if effective_cycle == CycleType.ANNUAL:
        return False, "effective cycle is annual (instance/species override) — no restart"
    if lifecycle is not None:
        return cyclic.should_restart_cycle(lifecycle, cycle_number, phase_name, effective_cycle=effective_cycle)
    return True, "no lifecycle config — sequence is_repeating governs the restart"


def _advance_sequence_plant(
    plant, info: dict, days_in_phase: int, lifecycle, phase_service, cyclic, reads: _PageReads
) -> bool:
    """WP-2 — advance one PhaseSequence-driven plant along its sequence (Weg B).

    Fires a time-based forward step once the current phase's duration has elapsed and,
    from the terminal phase, the perennial cycle restart at ``cycle_restart_entry_order``
    (gated by :func:`_should_restart_cycle`). Returns ``True`` when a transition fired.
    """
    advance = reads.sequence_target(plant.species_key, plant.current_phase_key)
    if advance is None or days_in_phase < advance.duration_days:
        return False

    phase_name = info.get("phase", "")
    # E4: an indeterminate species stays in its stable productive phase — suppress
    # any onward auto-advance (concurrent veg/flower/fruit, continuous harvest).
    if lifecycle is not None and cyclic.stays_in_productive_phase(lifecycle, phase_name):
        logger.info("auto_transition_suppressed_indeterminate", plant_key=plant.key, current_phase=phase_name)
        return False

    if advance.is_restart:
        # ADR-006 E1: the per-instance override wins over the species cycle for the
        # restart decision (an instance grown as an annual does not loop).
        effective_cycle = resolve_effective_cycle(plant, lifecycle, None)
        should, detail = _should_restart_cycle(
            cyclic, lifecycle, info.get("cycle_number", 1), phase_name, effective_cycle
        )
        if not should:
            logger.info("cycle_restart_suppressed", plant_key=plant.key, current_phase=phase_name, reason=detail)
            return False
        reason = "auto_cycle_restart"
    else:
        reason = "auto_time_based"

    phase_service.transition_phase(
        plant.key or "", advance.target_phase_key, reason=reason, trigger=TransitionTrigger.AUTO
    )
    logger.info(
        "auto_transition",
        plant_key=plant.key,
        to_phase=advance.target_phase_key,
        trigger="sequence",
        is_restart=advance.is_restart,
    )
    return True


class _MemoSiteReads:
    """The site reads of one page, each key read once (MT-032, #2128).

    Satisfies :class:`~app.domain.services.location_ownership.SiteAnchorSource`, so
    the SEC-B4 ownership walk (:func:`find_owned_location`) runs unchanged on every
    plant — only the documents it reads are shared between the plants of a page that
    stand in the same location or site. A read that raises is not remembered.
    """

    def __init__(self, site_repo: SiteAnchorSource) -> None:
        self._site_repo = site_repo
        self._sites: dict[str, Site | None] = {}
        self._locations: dict[str, Location | None] = {}
        self._slots: dict[str, Slot | None] = {}

    def get_site_by_key(self, key: str) -> Site | None:
        return _remembered(self._sites, key, lambda: self._site_repo.get_site_by_key(key))

    def get_location_by_key(self, key: str) -> Location | None:
        return _remembered(self._locations, key, lambda: self._site_repo.get_location_by_key(key))

    def get_slot_by_key(self, key: str) -> Slot | None:
        return _remembered(self._slots, key, lambda: self._site_repo.get_slot_by_key(key))


class _PageReads:
    """Catalogue and site reads of one page of plants, each distinct key read once (MT-032, #2128).

    The scan used to ask for the species' lifecycle, the phase's transition rules,
    the sequence's next entry and the plant's location/site once **per plant**, so
    its query count grew with the plant count. Plants of a page share species,
    phases and locations; this answers the second plant from the first one's read.
    The memo lives for one page only, so the worker's memory is bounded by the page
    and not by the installation. A read that raises is not remembered: the next plant
    asks again and fails on its own, as before.
    """

    def __init__(
        self, phase_service: PhaseService, lifecycle_repo: IPhaseRepository, site_repo: SiteAnchorSource
    ) -> None:
        self._phase_service = phase_service
        self._lifecycle_repo = lifecycle_repo
        self.sites = _MemoSiteReads(site_repo)
        self._lifecycles: dict[str, LifecycleConfig | None] = {}
        self._rules: dict[str, list[PhaseTransitionRule]] = {}
        self._targets: dict[tuple[str | None, str | None], SequenceAutoTarget | None] = {}

    def lifecycle(self, species_key: str) -> LifecycleConfig | None:
        return _remembered(
            self._lifecycles, species_key, lambda: self._lifecycle_repo.get_lifecycle_by_species(species_key)
        )

    def transition_rules(self, phase_key: str) -> list[PhaseTransitionRule]:
        return _remembered(self._rules, phase_key, lambda: self._phase_service.get_transition_rules(phase_key))

    def sequence_target(self, species_key: str | None, phase_key: str | None) -> SequenceAutoTarget | None:
        return _remembered(
            self._targets,
            (species_key, phase_key),
            lambda: self._phase_service.resolve_sequence_auto_target(species_key, phase_key),
        )


def _remembered[K, V](cache: dict[K, V], key: K, read: Callable[[], V]) -> V:
    """``cache[key]``, reading it first when absent; an exception leaves the cache untouched."""
    if key not in cache:
        cache[key] = read()
    return cache[key]


def _evaluate_rules(
    plant: PlantInstance,
    info: dict[str, Any],
    lifecycle: LifecycleConfig | None,
    reads: _PageReads,
    evaluator: TransitionTriggerEvaluator,
    cyclic: CyclicLifecycleEngine,
    phase_service: PhaseService,
) -> bool:
    """The legacy GrowthPhase rule path for one plant; ``True`` when a transition fired."""
    days_in_phase = info["days_in_phase"]
    for rule in reads.transition_rules(plant.current_phase_key or ""):
        fire = False
        reason = ""

        if (
            rule.trigger_type == TransitionTriggerType.TIME_BASED
            and rule.auto_transition_after_days
            and days_in_phase >= rule.auto_transition_after_days
        ):
            fire, reason = True, "auto_time_based"
        elif rule.trigger_type == TransitionTriggerType.PHOTOPERIOD_BASED and lifecycle:
            day_length = _day_length_for_plant(plant, reads.sites)
            if day_length is not None and evaluator.photoperiod_should_fire(
                lifecycle.photoperiod_type,
                lifecycle.critical_day_length_hours,
                day_length,
            ):
                fire, reason = True, "auto_photoperiod"
        elif (
            rule.trigger_type == TransitionTriggerType.VERNALIZATION_BASED
            and lifecycle
            and evaluator.vernalization_should_fire(
                lifecycle.vernalization_min_days,
                plant.chill_days_accumulated,
            )
        ):
            fire, reason = True, "auto_vernalization"

        # E4: an indeterminate species stays in its stable productive phase —
        # suppress any onward auto-advance even though the trigger would fire.
        current_phase_name = info.get("phase", "")
        if fire and lifecycle and cyclic.stays_in_productive_phase(lifecycle, current_phase_name):
            logger.info(
                "auto_transition_suppressed_indeterminate",
                plant_key=plant.key,
                current_phase=current_phase_name,
            )
            continue

        if fire:
            # AUTO trigger: the D10 clonal-pup spawn only reacts to
            # automatic transitions (a manual API correction must not).
            phase_service.transition_phase(
                plant.key or "", rule.to_phase_key, reason=reason, trigger=TransitionTrigger.AUTO
            )
            logger.info(
                "auto_transition",
                plant_key=plant.key,
                to_phase=rule.to_phase_key,
                trigger=rule.trigger_type.value,
            )
            return True
    return False


def _check_page(
    page: list[PlantInstance],
    phase_service: PhaseService,
    lifecycle_repo: IPhaseRepository,
    site_repo: SiteAnchorSource,
    evaluator: TransitionTriggerEvaluator,
    cyclic: CyclicLifecycleEngine,
) -> tuple[int, int]:
    """Evaluate one page of plants; returns ``(transitioned, errors)``.

    The page's phase positions come from one batched read
    (:meth:`PhaseService.get_current_phases`) and every catalogue/site read from a
    page-scoped memo (:class:`_PageReads`), so a plant that shares its species, phase
    and location with an earlier plant of the page costs no query (MT-032, #2128).
    If the batched read itself fails, every plant of the page that would have been
    evaluated counts as an error — the same count the per-plant read produced when
    the store was unreachable.
    """
    candidates = [plant for plant in page if plant.current_phase_key]
    if not candidates:
        return 0, 0
    try:
        positions = phase_service.get_current_phases(candidates)
    except Exception as e:
        logger.error("auto_transition_page_error", plants=len(candidates), error=loggable_error(e))
        return 0, len(candidates)

    reads = _PageReads(phase_service, lifecycle_repo, site_repo)
    transitioned = 0
    errors = 0
    for plant in candidates:
        try:
            info = positions[plant.key or ""]
            lifecycle = reads.lifecycle(plant.species_key)

            # WP-2: PhaseSequence-driven plants (Weg B) advance along their sequence,
            # including the terminal→restart cycle loop. This is the cyclic path after
            # the #565 migration; the legacy GrowthPhase rule loop is unchanged.
            if info.get("source") == "phase_sequence":
                fired = _advance_sequence_plant(
                    plant, info, info["days_in_phase"], lifecycle, phase_service, cyclic, reads
                )
            else:
                fired = _evaluate_rules(plant, info, lifecycle, reads, evaluator, cyclic, phase_service)
            if fired:
                transitioned += 1
        except Exception as e:
            errors += 1
            logger.error("auto_transition_error", plant_key=plant.key, error=loggable_error(e))
    return transitioned, errors


@celery_app.task(name="check_auto_transitions")
def check_auto_transitions() -> dict:
    """Check active plants for automatic phase transitions.

    PhaseSequence-driven plants (Weg B — strawberry & the migrated perennials, #565)
    advance directly along their sequence, including the terminal→restart edge that
    fires the perennial cycle restart (WP-2). Legacy GrowthPhase plants keep the
    rule-based path: time-based (elapsed days), photoperiod-based (E1) and
    vernalization-based (E2) triggers. gdd-based wiring needs a per-plant GDD
    accumulation source and is a follow-up.

    **Not scheduled (MT-051, #2144).** Nothing starts this task — no beat entry, no
    dispatch; the decision and its prerequisite are recorded in
    ``tests/unit/guards/test_every_task_is_scheduled_or_dispatched.py``
    (``_NOT_STARTED_BY_THE_APP``), which fails the day something does start it.
    """
    plant_repo = get_plant_repo()
    phase_service = get_phase_service()
    lifecycle_repo = get_lifecycle_repo()
    site_repo = get_site_repo()
    evaluator = TransitionTriggerEvaluator()
    cyclic = CyclicLifecycleEngine()

    transitioned = 0
    errors = 0
    checked = 0

    # REQ-056 §5.2 / MT-032 (#2128): only the plants of active tenants that are not removed, selected in
    # AQL and read one page at a time; each page is evaluated with batched reads (no query per plant).
    active_tenants = get_tenant_repo().keys_in_status({TenantStatus.ACTIVE})
    walk = plant_repo.iter_for_tenants(active_tenants, filters=[("removed_on", "==", None)], page_size=_PAGE_SIZE)
    for page in batched(walk, _PAGE_SIZE, strict=False):
        checked += len(page)
        page_transitioned, page_errors = _check_page(
            list(page), phase_service, lifecycle_repo, site_repo, evaluator, cyclic
        )
        transitioned += page_transitioned
        errors += page_errors

    return {"transitioned": transitioned, "errors": errors, "checked": checked}
