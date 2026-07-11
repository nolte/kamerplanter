"""REQ-037 — reference-evapotranspiration & irrigation water-balance calculator.

Pure domain calculation (no I/O). Produces the two physically-grounded quantities
that drive the outdoor irrigation logic:

* ``calculate_et0`` — reference evapotranspiration ET₀ (mm/day) for a grass
  reference crop, via the **FAO-56 Penman-Monteith** equation (Allen et al., 1998)
  when humidity and wind are available, falling back to the **Hargreaves**
  equation when only the daily temperature range is known.
* ``calculate_water_balance`` — turns ET₀ into a crop-specific net irrigation
  demand: ETc = ET₀ × Kc, minus effective precipitation, clamped to the
  substrate water-holding capacity, expressed as both millimetres and litres
  (1 mm = 1 L/m²).

The FAO-56 equations are provided by :mod:`aquacropeto` (BSD-3-Clause, a maintained
fork of PyETo). The library reproduces FAO-56 Example 18 (Uccle, Belgium) to
ET₀ = 3.9 mm/day, which the unit tests pin as a regression reference vector.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import aquacropeto as eto

#: Estimation method used for an ET₀ result (surfaced to the API/UI).
Et0Method = Literal["fao56_penman_monteith", "hargreaves"]

#: Confidence class of an ET₀ result, derived from how complete the driving
#: weather inputs were (high = full Penman-Monteith with measured radiation).
Et0Quality = Literal["high", "medium", "low"]

#: FAO-56 reference albedo of the hypothetical grass reference crop.
_REFERENCE_ALBEDO = 0.23

#: FAO-56 rule-of-thumb precipitation threshold (mm): below it a shower largely
#: evaporates without recharging the root zone; above it 80 % is counted effective.
_EFFECTIVE_PRECIP_THRESHOLD_MM = 5.0
_EFFECTIVE_PRECIP_FACTOR = 0.8

#: Standard meteorological wind-measurement height (m) assumed when a source does
#: not state one; the FAO-56 logarithmic profile scales it to the 2 m reference.
_DEFAULT_WIND_HEIGHT_M = 10.0

#: Hargreaves radiation adjustment coefficient krs (FAO-56 eq. 50) for interior
#: locations, used to estimate solar radiation from the diurnal temperature range
#: when no measured radiation is available.
_KRS_INLAND = 0.16

#: Global fallback crop coefficient when no phase/species/category value resolves.
GLOBAL_DEFAULT_KC = 0.8


@dataclass(frozen=True)
class Et0Result:
    """Reference evapotranspiration for one day."""

    et0_mm: float
    method: Et0Method
    quality: Et0Quality
    method_reason: str


@dataclass(frozen=True)
class WaterBalanceResult:
    """Crop water balance derived from an :class:`Et0Result` and a Kc."""

    et0_mm: float
    kc_used: float
    etc_mm: float
    effective_precipitation_mm: float
    net_demand_mm: float
    net_demand_mm_capped: float
    recommended_volume_liters: float


def _estimate_solar_from_temp(et_rad: float, clear_sky_rad: float, temp_min_c: float, temp_max_c: float) -> float:
    """Estimate incoming solar radiation Rs from the diurnal temperature range.

    Hargreaves radiation formula (FAO-56 eq. 50):
    ``Rs = krs · √(Tmax − Tmin) · Ra``, capped at the clear-sky radiation Rso. Used
    instead of :func:`aquacropeto.sol_rad_from_t`, whose 0.1.1 release ships a bug
    (``np.min(sol_rad, cs_rad)`` misuses the NumPy reduction signature).
    """
    temp_range = max(0.0, temp_max_c - temp_min_c)
    estimated = _KRS_INLAND * math.sqrt(temp_range) * et_rad
    return float(min(estimated, clear_sky_rad))


class EvapotranspirationCalculator:
    """FAO-56 reference ET₀ and irrigation water-balance (REQ-037).

    Stateless: every method is a pure function of its arguments. Instantiate once
    and reuse, or call the methods on a throwaway instance.
    """

    def calculate_et0(
        self,
        *,
        latitude_deg: float,
        day_of_year: int,
        temp_min_c: float,
        temp_max_c: float,
        humidity_percent: float | None = None,
        wind_speed_kmh: float | None = None,
        solar_radiation_mj_m2: float | None = None,
        elevation_m: float = 0.0,
        wind_measurement_height_m: float = _DEFAULT_WIND_HEIGHT_M,
    ) -> Et0Result:
        """Estimate reference evapotranspiration ET₀ (mm/day).

        Uses FAO-56 Penman-Monteith when both ``humidity_percent`` and
        ``wind_speed_kmh`` are available; the quality is ``high`` when the incoming
        solar radiation was measured (``solar_radiation_mj_m2``, e.g. from NASA
        POWER, REQ-041) and ``medium`` when it had to be estimated from the daily
        temperature range. Otherwise falls back to Hargreaves (``medium``), which
        needs only the temperature range.

        ``temp_min_c`` / ``temp_max_c`` are the only hard requirements; a physically
        impossible ``temp_max_c < temp_min_c`` is normalised by swapping so the
        radiation term never goes imaginary.
        """
        if temp_max_c < temp_min_c:
            temp_min_c, temp_max_c = temp_max_c, temp_min_c
        temp_mean_c = (temp_min_c + temp_max_c) / 2.0

        # Extraterrestrial radiation Ra and clear-sky radiation Rso are needed by
        # both paths (Hargreaves for its radiation proxy, PM for net radiation).
        latitude_rad = eto.deg2rad(latitude_deg)
        sol_dec = eto.sol_dec(day_of_year)
        sunset_hour_angle = eto.sunset_hour_angle(latitude_rad, sol_dec)
        ird = eto.inv_rel_dist_earth_sun(day_of_year)
        et_rad = eto.et_rad(latitude_rad, sol_dec, sunset_hour_angle, ird)
        clear_sky_rad = eto.cs_rad(elevation_m, et_rad)

        has_humidity = humidity_percent is not None
        has_wind = wind_speed_kmh is not None

        if has_humidity and has_wind:
            return self._penman_monteith(
                latitude_rad=latitude_rad,
                temp_min_c=temp_min_c,
                temp_max_c=temp_max_c,
                temp_mean_c=temp_mean_c,
                humidity_percent=float(humidity_percent),  # type: ignore[arg-type]
                wind_speed_kmh=float(wind_speed_kmh),  # type: ignore[arg-type]
                solar_radiation_mj_m2=solar_radiation_mj_m2,
                elevation_m=elevation_m,
                wind_measurement_height_m=wind_measurement_height_m,
                et_rad=et_rad,
                clear_sky_rad=clear_sky_rad,
            )

        missing = []
        if not has_humidity:
            missing.append("humidity")
        if not has_wind:
            missing.append("wind")
        reason = "hargreaves_fallback: missing " + "+".join(missing)
        et0 = eto.hargreaves(temp_min_c, temp_max_c, temp_mean_c, et_rad)
        return Et0Result(
            et0_mm=round(float(max(0.0, et0)), 3),
            method="hargreaves",
            quality="medium",
            method_reason=reason,
        )

    def _penman_monteith(
        self,
        *,
        latitude_rad: float,
        temp_min_c: float,
        temp_max_c: float,
        temp_mean_c: float,
        humidity_percent: float,
        wind_speed_kmh: float,
        solar_radiation_mj_m2: float | None,
        elevation_m: float,
        wind_measurement_height_m: float,
        et_rad: float,
        clear_sky_rad: float,
    ) -> Et0Result:
        """FAO-56 Penman-Monteith ET₀ (mm/day)."""
        # Actual vapour pressure from mean relative humidity (FAO-56 eq. 19).
        svp_tmin = eto.svp_from_t(temp_min_c)
        svp_tmax = eto.svp_from_t(temp_max_c)
        avp = eto.avp_from_rhmean(svp_tmin, svp_tmax, humidity_percent)

        # Solar radiation: measured (high quality) or estimated from the diurnal
        # temperature range via the Hargreaves radiation formula (medium quality).
        if solar_radiation_mj_m2 is not None:
            solar_rad = float(solar_radiation_mj_m2)
            quality: Et0Quality = "high"
            reason = "penman_monteith: measured solar radiation"
        else:
            solar_rad = _estimate_solar_from_temp(et_rad, clear_sky_rad, temp_min_c, temp_max_c)
            quality = "medium"
            reason = "penman_monteith: solar radiation estimated from temperature range"

        net_in = eto.net_in_sol_rad(solar_rad, albedo=_REFERENCE_ALBEDO)
        net_out = eto.net_out_lw_rad(
            eto.celsius2kelvin(temp_min_c),
            eto.celsius2kelvin(temp_max_c),
            solar_rad,
            clear_sky_rad,
            avp,
        )
        net_rad = eto.net_rad(net_in, net_out)

        # Wind speed reduced to the FAO-56 reference height of 2 m.
        wind_ms = wind_speed_kmh / 3.6
        wind_2m = eto.wind_speed_2m(wind_ms, wind_measurement_height_m)

        svp = eto.mean_svp(temp_min_c, temp_max_c)
        delta = eto.delta_svp(temp_mean_c)
        atm_pressure = eto.atm_pressure(elevation_m)
        psy = eto.psy_const(atm_pressure)

        et0 = eto.fao56_penman_monteith(
            net_rad=net_rad,
            t=eto.celsius2kelvin(temp_mean_c),
            ws=wind_2m,
            svp=svp,
            avp=avp,
            delta_svp=delta,
            psy=psy,
            shf=0.0,
        )
        return Et0Result(
            et0_mm=round(float(max(0.0, et0)), 3),
            method="fao56_penman_monteith",
            quality=quality,
            method_reason=reason,
        )

    def calculate_water_balance(
        self,
        *,
        et0_mm: float,
        crop_coefficient_kc: float,
        precipitation_mm: float = 0.0,
        water_holding_capacity_mm: float | None = None,
        area_m2: float = 1.0,
    ) -> WaterBalanceResult:
        """Derive the crop water balance from ET₀ and a crop coefficient.

        * ``ETc = ET₀ × Kc`` — crop evapotranspiration.
        * Effective precipitation: 80 % of rainfall above the FAO-56 threshold of
          5 mm, otherwise the full (small) amount.
        * ``net_demand_mm = ETc − effective_precipitation`` — may be **negative**
          when rain covers the demand.
        * ``net_demand_mm_capped`` clamps that to ``[0, water_holding_capacity_mm]``:
          never irrigate below zero, and never above what the root zone can retain
          (excess would drain away).
        * ``recommended_volume_liters = net_demand_mm_capped × area_m2``
          (1 mm = 1 L/m²).
        """
        etc_mm = et0_mm * crop_coefficient_kc

        if precipitation_mm > _EFFECTIVE_PRECIP_THRESHOLD_MM:
            effective_precip = precipitation_mm * _EFFECTIVE_PRECIP_FACTOR
        else:
            effective_precip = max(0.0, precipitation_mm)

        net_demand_mm = etc_mm - effective_precip

        capped = max(0.0, net_demand_mm)
        if water_holding_capacity_mm is not None:
            capped = min(capped, water_holding_capacity_mm)

        recommended_liters = capped * area_m2

        return WaterBalanceResult(
            et0_mm=round(et0_mm, 3),
            kc_used=round(crop_coefficient_kc, 3),
            etc_mm=round(etc_mm, 3),
            effective_precipitation_mm=round(effective_precip, 3),
            net_demand_mm=round(net_demand_mm, 3),
            net_demand_mm_capped=round(capped, 3),
            recommended_volume_liters=round(recommended_liters, 2),
        )
