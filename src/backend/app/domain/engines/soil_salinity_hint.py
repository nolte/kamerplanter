"""The salt-limit hint of a field-soil bed: "check salt content" (REQ-053 §15.1, GP-FR-125; E-17 variant A).

Operator decision E-17 variant A: the conductivity of a field soil (``SoilProfile.ec_ms_cm``) is **no EC target**
and never scales or computes a dose. It is read only as a salt-limit hint: above a configured threshold the bed
summary says "check salt content" - nothing more.

**No threshold without a source (E-10).** The threshold, the extraction method it holds for and its ``source`` are
configuration; :data:`DEFAULT_SALINITY_CONFIG` has none of them (research item R-001 is open), so the hint is inert
until somebody configures a sourced value.

**No conversion between methods (U-002).** Salt thresholds hold for one extraction method (mostly the saturated
paste, ECe); a 1:2, 1:5 or probe value is not comparable with it and no lossless conversion exists. The hint
therefore only fires when the profile's ``ec_method`` *equals* the configured method. ``unknown`` is comparable with
nothing and cannot be configured.

Pure logic, no database.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.enums import EcMethod
from app.domain.models.site import SoilProfile


@dataclass(frozen=True)
class SoilSalinityConfig:
    """The salt limit of a field soil. All ``None`` by default: no value has a closed research item (R-001).

    * ``threshold_ms_cm`` - conductivity in mS/cm above which the hint fires.
    * ``ec_method`` - the extraction method the threshold holds for; a profile measured otherwise is never compared.
    * ``source`` - the citation of the threshold; without one the rule takes no part (E-10).
    """

    threshold_ms_cm: float | None = None
    ec_method: EcMethod | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if self.threshold_ms_cm is not None and self.threshold_ms_cm <= 0:
            raise ValueError("threshold_ms_cm must be positive.")
        if self.ec_method == EcMethod.UNKNOWN:
            raise ValueError("ec_method 'unknown' is comparable with nothing and cannot carry a salt threshold.")

    @property
    def active(self) -> bool:
        """Whether the rule takes part: a threshold, the method it holds for, and a non-blank source."""
        return (
            self.threshold_ms_cm is not None
            and self.ec_method is not None
            and self.source is not None
            and bool(self.source.strip())
        )


#: The shipped configuration: no threshold, no method, no source (R-001 open; E-10).
DEFAULT_SALINITY_CONFIG = SoilSalinityConfig()


def needs_salt_check(soil_profile: SoilProfile | None, config: SoilSalinityConfig = DEFAULT_SALINITY_CONFIG) -> bool:
    """``True`` when the bed's soil conductivity lies above the sourced salt limit of the same extraction method.

    ``False`` for an inactive configuration, a profile without a conductivity, and a conductivity measured by
    another method than the one the threshold holds for (no conversion). Never a dose, never an EC target.
    """
    if soil_profile is None or not config.active:
        return False
    ec_ms_cm = soil_profile.ec_ms_cm
    if ec_ms_cm is None or soil_profile.ec_method != config.ec_method:
        return False
    return ec_ms_cm > float(config.threshold_ms_cm or 0)
