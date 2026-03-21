"""Substrate EC adapter for runtime EC target conversion between substrate types.

Converts reference EC values calibrated for one substrate type to effective EC
targets for a different runtime substrate. This enables substrate-independent
nutrient plans: plans define plant nutritional needs in the context of a
reference substrate, and the adapter adjusts at runtime.

Conversion factors are derived from EC_MAX_TABLE midpoints (REQ-004):
  HYDRO VEG mid=2.0, FLOWER mid=2.3
  COCO  VEG mid=1.8, FLOWER mid=2.1
  SOIL  VEG mid=1.1, FLOWER mid=1.3

Factors are expressed relative to HYDRO (=1.0).
"""

import structlog

from app.common.enums import PhaseName, SubstrateType

logger = structlog.get_logger()

# ── Substrate class groupings ────────────────────────────────────────

SUBSTRATE_CLASS_MAP: dict[SubstrateType, str] = {
    SubstrateType.HYDRO_SOLUTION: "hydro",
    SubstrateType.CLAY_PEBBLES: "hydro",
    SubstrateType.PERLITE: "hydro",
    SubstrateType.ROCKWOOL_SLAB: "hydro",
    SubstrateType.ROCKWOOL_PLUG: "hydro",
    SubstrateType.VERMICULITE: "hydro",
    SubstrateType.NONE: "hydro",
    SubstrateType.COCO: "coco",
    SubstrateType.SPHAGNUM: "coco",
    SubstrateType.PON_MINERAL: "coco",
    SubstrateType.ORCHID_BARK: "coco",
    SubstrateType.SOIL: "soil",
    SubstrateType.PEAT: "soil",
    SubstrateType.LIVING_SOIL: "living_soil",
}

# String-based lookup for convenience (SubstrateType.value -> class)
_SUBSTRATE_CLASS_BY_VALUE: dict[str, str] = {k.value: v for k, v in SUBSTRATE_CLASS_MAP.items()}

# ── Phase-dependent EC correction factors (relative to HYDRO=1.0) ────

# Derived from EC_MAX_TABLE midpoints:
#   seedling: HYDRO mid=1.0, COCO mid=0.9, SOIL mid=0.5
#   vegetative: HYDRO mid=2.0, COCO mid=1.8, SOIL mid=1.1
#   flowering: HYDRO mid=2.3, COCO mid=2.1, SOIL mid=1.3
EC_FACTORS: dict[str, dict[str, float]] = {
    "hydro": {
        "seedling": 1.00,
        "vegetative": 1.00,
        "flowering": 1.00,
        "default": 1.00,
    },
    "coco": {
        "seedling": 0.90,
        "vegetative": 0.90,
        "flowering": 0.91,
        "default": 0.90,
    },
    "soil": {
        "seedling": 0.50,
        "vegetative": 0.55,
        "flowering": 0.57,
        "default": 0.55,
    },
}

# Phase name mapping: PhaseName enum values -> factor key
_PHASE_KEY_MAP: dict[str, str] = {
    PhaseName.GERMINATION.value: "seedling",
    PhaseName.SEEDLING.value: "seedling",
    PhaseName.VEGETATIVE.value: "vegetative",
    PhaseName.FLOWERING.value: "flowering",
    PhaseName.HARVEST.value: "flowering",
    PhaseName.FLUSHING.value: "flowering",
    PhaseName.DORMANCY.value: "vegetative",
}


class SubstrateEcAdapter:
    """Converts EC targets between substrate types at runtime.

    Formula:
        hydro_ec = reference_ec / factor[from_substrate][phase]
        effective_ec = hydro_ec * factor[to_substrate][phase]

    LIVING_SOIL is a bypass: returns 0.0 (no EC dosing — microbiome manages nutrients).
    """

    def convert_ec(
        self,
        reference_ec: float,
        from_substrate: str,
        to_substrate: str,
        phase_name: str,
    ) -> float:
        """Convert an EC value from one substrate context to another.

        Args:
            reference_ec: EC target in the context of from_substrate.
            from_substrate: SubstrateType value the EC was calibrated for.
            to_substrate: SubstrateType value to convert to.
            phase_name: PhaseName enum value (e.g. "vegetative", "flowering").

        Returns:
            Effective EC for the target substrate. Returns 0.0 for living_soil.
        """
        if reference_ec <= 0:
            return 0.0

        from_class = self._resolve_class(from_substrate)
        to_class = self._resolve_class(to_substrate)

        # Living soil bypass — no EC-based dosing
        if to_class == "living_soil":
            logger.info(
                "substrate_ec_bypass",
                reason="living_soil",
                reference_ec=reference_ec,
            )
            return 0.0

        if from_class == "living_soil":
            logger.warning(
                "substrate_ec_from_living_soil",
                msg="Cannot convert from living_soil reference — returning reference EC unchanged",
            )
            return reference_ec

        # Same class — no conversion needed
        if from_class == to_class:
            return reference_ec

        phase_key = self._resolve_phase_key(phase_name)
        from_factor = EC_FACTORS[from_class][phase_key]
        to_factor = EC_FACTORS[to_class][phase_key]

        if from_factor <= 0:
            return reference_ec

        # Normalize to hydro, then scale to target
        hydro_ec = reference_ec / from_factor
        effective_ec = round(hydro_ec * to_factor, 2)

        logger.debug(
            "substrate_ec_converted",
            from_substrate=from_substrate,
            to_substrate=to_substrate,
            from_class=from_class,
            to_class=to_class,
            phase=phase_name,
            reference_ec=reference_ec,
            hydro_ec=round(hydro_ec, 4),
            effective_ec=effective_ec,
        )

        return effective_ec

    def get_factor(self, substrate: str, phase_name: str) -> float:
        """Get the EC correction factor for a substrate/phase combination.

        Returns 0.0 for living_soil (bypass signal).
        """
        substrate_class = self._resolve_class(substrate)
        if substrate_class == "living_soil":
            return 0.0
        phase_key = self._resolve_phase_key(phase_name)
        return EC_FACTORS[substrate_class][phase_key]

    @staticmethod
    def _resolve_class(substrate: str) -> str:
        """Map a SubstrateType value to its substrate class."""
        return _SUBSTRATE_CLASS_BY_VALUE.get(substrate, "soil")

    @staticmethod
    def _resolve_phase_key(phase_name: str) -> str:
        """Map a PhaseName value to a factor table key."""
        return _PHASE_KEY_MAP.get(phase_name, "default")
