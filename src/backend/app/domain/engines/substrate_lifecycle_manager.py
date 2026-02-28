import statistics
from datetime import date, timedelta

from app.common.enums import IrrigationStrategy, SubstrateType
from app.common.exceptions import SubstrateExhaustedError
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import Substrate, SubstrateBatch

# Substrate types that cannot be reused (disposable)
DISPOSABLE_TYPES: frozenset[SubstrateType] = frozenset({
    SubstrateType.ROCKWOOL_PLUG,
    SubstrateType.PEAT,
})

# pH standard deviation thresholds per substrate type
PH_STDDEV_THRESHOLDS: dict[SubstrateType, float] = {
    SubstrateType.COCO: 0.3,
    SubstrateType.LIVING_SOIL: 0.7,
    SubstrateType.SOIL: 0.5,
    SubstrateType.CLAY_PEBBLES: 0.4,
    SubstrateType.PERLITE: 0.4,
    SubstrateType.ROCKWOOL_SLAB: 0.3,
    SubstrateType.VERMICULITE: 0.5,
    SubstrateType.ORCHID_BARK: 0.5,
    SubstrateType.PON_MINERAL: 0.4,
    SubstrateType.SPHAGNUM: 0.5,
}

# Default EC delta threshold (max acceptable change from base)
EC_DELTA_THRESHOLD_MS = 1.5

# Irrigation strategy map for all substrate types
IRRIGATION_STRATEGY_MAP: dict[SubstrateType, IrrigationStrategy] = {
    SubstrateType.SOIL: IrrigationStrategy.MODERATE,
    SubstrateType.COCO: IrrigationStrategy.FREQUENT,
    SubstrateType.CLAY_PEBBLES: IrrigationStrategy.FREQUENT,
    SubstrateType.PERLITE: IrrigationStrategy.FREQUENT,
    SubstrateType.LIVING_SOIL: IrrigationStrategy.INFREQUENT,
    SubstrateType.PEAT: IrrigationStrategy.MODERATE,
    SubstrateType.ROCKWOOL_SLAB: IrrigationStrategy.CONTINUOUS,
    SubstrateType.ROCKWOOL_PLUG: IrrigationStrategy.CONTINUOUS,
    SubstrateType.VERMICULITE: IrrigationStrategy.MODERATE,
    SubstrateType.NONE: IrrigationStrategy.CONTINUOUS,
    SubstrateType.ORCHID_BARK: IrrigationStrategy.INFREQUENT,
    SubstrateType.PON_MINERAL: IrrigationStrategy.MODERATE,
    SubstrateType.SPHAGNUM: IrrigationStrategy.MODERATE,
    SubstrateType.HYDRO_SOLUTION: IrrigationStrategy.CONTINUOUS,
}

# Preparation steps per substrate type
_PREPARATION_STEPS: dict[SubstrateType, list[dict[str, str | float]]] = {
    SubstrateType.COCO: [
        {"step": "Soak in CalMag solution (EC 1.0) for 24 hours", "hours": 24},
        {"step": "Flush with pH-adjusted water until runoff EC < 0.3", "hours": 2},
        {"step": "Drain and fluff", "hours": 1},
    ],
    SubstrateType.CLAY_PEBBLES: [
        {"step": "Soak in H2O2 solution (3%) for 30 minutes", "hours": 0.5},
        {"step": "Rinse thoroughly with clean water", "hours": 0.5},
        {"step": "Air dry completely", "hours": 24},
    ],
    SubstrateType.ROCKWOOL_SLAB: [
        {"step": "Steam sterilize at 100°C for 30 minutes", "hours": 1},
        {"step": "Soak in pH 5.5 adjusted water for 24 hours", "hours": 24},
        {"step": "Drain until field capacity", "hours": 2},
    ],
    SubstrateType.PERLITE: [
        {"step": "Rinse with H2O2 solution (3%)", "hours": 0.5},
        {"step": "Flush with clean water", "hours": 0.5},
        {"step": "Air dry", "hours": 12},
    ],
    SubstrateType.LIVING_SOIL: [
        {"step": "Add compost tea and amendments", "hours": 1},
        {"step": "Inoculate with mycorrhizae", "hours": 0.5},
        {"step": "Rest period for microbial recolonization", "hours": 168},
    ],
    SubstrateType.SOIL: [
        {"step": "Solarize or steam sterilize", "hours": 48},
        {"step": "Add fresh compost (20% by volume)", "hours": 1},
        {"step": "Adjust pH if needed", "hours": 1},
    ],
    SubstrateType.VERMICULITE: [
        {"step": "Rinse thoroughly to remove salt buildup", "hours": 1},
        {"step": "Sterilize in oven at 200°C for 30 minutes", "hours": 1},
    ],
    SubstrateType.ORCHID_BARK: [
        {"step": "Soak in boiling water for 10 minutes", "hours": 0.5},
        {"step": "Rinse and drain", "hours": 0.5},
        {"step": "Air dry", "hours": 24},
    ],
    SubstrateType.PON_MINERAL: [
        {"step": "Rinse with clean water to remove residues", "hours": 0.5},
        {"step": "Soak in diluted H2O2 solution", "hours": 1},
        {"step": "Rinse and drain", "hours": 0.5},
    ],
    SubstrateType.SPHAGNUM: [
        {"step": "Rehydrate with pH-adjusted water", "hours": 2},
        {"step": "Squeeze out excess water gently", "hours": 0.5},
    ],
}


class SubstrateLifecycleManager:
    """Manages substrate batch reuse and lifecycle."""

    def __init__(self, substrate_repo: ISubstrateRepository) -> None:
        self._substrate_repo = substrate_repo

    def check_reusability(
        self, batch_key: str,
    ) -> tuple[bool, list[str], list[dict[str, str | float]], float, date | None]:
        """Check if a substrate batch can be reused.

        Returns (can_reuse, issues, preparation_steps, estimated_prep_time_hours, ready_date).
        """
        batch = self._substrate_repo.get_batch_by_key(batch_key)
        if batch is None:
            return False, ["Batch not found"], [], 0, None

        substrate = self._substrate_repo.get_substrate_by_key(batch.substrate_key)
        if substrate is None:
            return False, ["Substrate type not found"], [], 0, None

        # Disposable check
        if substrate.type in DISPOSABLE_TYPES:
            return False, [f"Substrate type '{substrate.type}' is disposable and cannot be reused"], [], 0, None

        if not substrate.reusable:
            return False, ["Substrate type is not reusable"], [], 0, None

        if batch.cycles_used >= substrate.max_reuse_cycles:
            return (
                False,
                [f"Max reuse cycles exceeded ({batch.cycles_used}/{substrate.max_reuse_cycles})"],
                [],
                0,
                None,
            )

        issues: list[str] = []

        # pH stability check (stddev-based)
        if batch.ph_history and len(batch.ph_history) >= 2:
            ph_stddev = statistics.stdev(batch.ph_history)
            threshold = PH_STDDEV_THRESHOLDS.get(substrate.type, 0.5)
            if ph_stddev > threshold:
                issues.append(
                    f"pH instability detected (stddev: {ph_stddev:.2f}, threshold: {threshold})"
                )

        # EC delta check
        if batch.ec_current_ms is not None:
            ec_delta = abs(batch.ec_current_ms - substrate.ec_base_ms)
            if ec_delta > EC_DELTA_THRESHOLD_MS:
                issues.append(
                    f"EC drift too high (delta: {ec_delta:.2f} mS, threshold: {EC_DELTA_THRESHOLD_MS} mS)"
                )

        if issues:
            return False, issues, [], 0, None

        # Get preparation steps
        prep_steps, prep_time = self.prepare_for_reuse(substrate, batch)
        ready = date.today() + timedelta(hours=prep_time)

        return True, [], prep_steps, prep_time, ready

    def prepare_for_reuse(
        self, substrate: Substrate, batch: SubstrateBatch,
    ) -> tuple[list[dict[str, str | float]], float]:
        """Get type-specific preparation steps for substrate reuse.

        Returns (preparation_steps, estimated_prep_time_hours).
        """
        steps = _PREPARATION_STEPS.get(substrate.type, [
            {"step": "Sanitize before reuse", "hours": 2},
        ])
        total_hours = sum(float(s["hours"]) for s in steps)
        return list(steps), total_hours

    def check_or_raise(self, batch_key: str) -> None:
        can_reuse, issues, *_ = self.check_reusability(batch_key)
        if not can_reuse:
            batch = self._substrate_repo.get_batch_by_key(batch_key)
            cycles = batch.cycles_used if batch else 0
            raise SubstrateExhaustedError(batch_key, cycles)

    @staticmethod
    def get_irrigation_strategy(substrate_type: SubstrateType) -> IrrigationStrategy:
        """Get recommended irrigation strategy for a substrate type."""
        return IRRIGATION_STRATEGY_MAP.get(substrate_type, IrrigationStrategy.MODERATE)
