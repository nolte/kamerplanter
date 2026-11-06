"""Soil analyses as care events: what lands in the bed's profile, and the series over time (REQ-053 §15.1, GP-FR-122).

Pure rules, no database (WP 8.7, #2650).

* **The profile holds the latest state only** (:func:`profile_patch`): ``ph`` with its ``ph_method``, ``ec_ms_cm`` with
  its ``ec_method``, ``humus_percent``, ``caco3_percent`` and ``last_analysis_at``. A value is taken over exactly as
  measured and only when its unit is the profile's own (``pH``, ``mS/cm`` = ``dS/m``, ``%``); a value in another unit
  is left out - **the system never converts** (U-002/U-003, E-10). P, K, Mg and N-min are not profile fields.
* **Series are per method** (:func:`build_series`): a conductivity is read per ``ec_method``, a pH per ``ph_method``,
  the rest per ``extraction_method``; ``unknown`` is its own method. When the method of a parameter changes from one
  analysis to the next, the change is marked. Values of different methods are never merged or compared.
* **"Liming likely" is a hint, never an amount** (:func:`liming_hint`): only for grown soil, only for a pH measured in
  CaCl2 (the reference of the lab target ranges, R-008), only with a known ``soil_texture`` and only against a
  ``target_ph`` someone *stated* (the profile never derives one, "stays null" item 17). Every other case says why no
  assessment is possible - a pH by water or by probe is never converted to CaCl2 (hint-only list).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from app.common.enums import GrowingMediumKind, PhMethod, SoilTexture
from app.domain.models.site import SoilProfile

#: The unit each profile parameter is stored in; ``mS/cm`` and ``dS/m`` are the same number.
_PROFILE_UNITS: dict[str, frozenset[str]] = {
    "ph": frozenset({"ph"}),
    "ec": frozenset({"ms/cm", "ds/m"}),
    "humus": frozenset({"%", "percent"}),
    "caco3": frozenset({"%", "percent"}),
}
#: Profile field(s) written by each parameter.
_PROFILE_FIELDS: dict[str, str] = {"ph": "ph", "ec": "ec_ms_cm", "humus": "humus_percent", "caco3": "caco3_percent"}

UNKNOWN_METHOD = "unknown"


@dataclass(frozen=True)
class SoilProfilePatch:
    """The values one analysis writes into the profile; ``fields`` always includes ``last_analysis_at``."""

    fields: Mapping[str, Any]
    last_analysis_at: datetime


def profile_patch(measurements: Sequence[Mapping[str, Any]] | None, performed_at: datetime) -> SoilProfilePatch | None:
    """The profile update of one analysis, or ``None`` when none of its measurements is a profile value.

    Of several measurements of one parameter the last one listed wins. A pH always replaces ``ph_method`` (a new value
    never keeps the method of the old one); a conductivity carries its ``ec_method``.
    """
    fields: dict[str, Any] = {}
    measurement: Mapping[str, Any]
    for measurement in measurements or ():
        parameter = str(measurement["parameter"])
        unit: str = str(measurement["unit"])
        if parameter not in _PROFILE_UNITS or unit.strip().lower() not in _PROFILE_UNITS[parameter]:
            continue
        fields[_PROFILE_FIELDS[parameter]] = measurement["value"]
        if parameter == "ph":
            fields["ph_method"] = measurement.get("ph_method")
        elif parameter == "ec":
            fields["ec_method"] = measurement.get("ec_method") or UNKNOWN_METHOD
    if not fields:
        return None
    return SoilProfilePatch(fields={**fields, "last_analysis_at": performed_at}, last_analysis_at=performed_at)


def is_newer(performed_at: datetime, last_analysis_at: datetime | None) -> bool:
    """Whether an analysis may write into a profile last updated at ``last_analysis_at``: not an *older* one.

    An analysis entered late (older than the profile's state) never overwrites it. At the **same instant** the latest
    write wins, so the correction of the newest analysis (which keeps its ``performed_at``) refreshes the profile.
    """
    return last_analysis_at is None or performed_at >= last_analysis_at


@dataclass(frozen=True)
class SeriesPoint:
    performed_at: datetime
    value: float
    unit: str
    source: str
    event_key: str
    sample_depth_cm: float | None = None
    content_class: str | None = None


@dataclass
class Series:
    """The points of one parameter measured by one method, oldest first."""

    parameter: str
    method: str
    points: list[SeriesPoint] = field(default_factory=list)


@dataclass(frozen=True)
class MethodChange:
    """The method of ``parameter`` changed at ``at``: the values before and after are not comparable."""

    parameter: str
    at: datetime
    from_method: str
    to_method: str


def method_of(measurement: Mapping[str, Any]) -> str:
    """The method a measurement is read by: ``ec_method`` (conductivity), ``ph_method`` (pH), else the extraction."""
    parameter = measurement["parameter"]
    key = "ec_method" if parameter == "ec" else "ph_method" if parameter == "ph" else "extraction_method"
    value = measurement.get(key)
    return str(value) if value else UNKNOWN_METHOD


@dataclass(frozen=True)
class AnalysisEvent:
    """What the series need of a stored ``soil_analysis`` care event."""

    key: str
    performed_at: datetime
    measurements: Sequence[Mapping[str, Any]]


def build_series(
    events: Iterable[AnalysisEvent], parameter: str | None = None
) -> tuple[list[Series], list[MethodChange]]:
    """Series per ``(parameter, method)`` and the marked method changes; never merges two methods."""
    by_series: dict[tuple[str, str], Series] = {}
    timeline: dict[str, list[tuple[datetime, str]]] = {}
    event: AnalysisEvent
    measurement: Mapping[str, Any]
    for event in sorted(events, key=lambda each: each.performed_at):
        for measurement in event.measurements:
            name = str(measurement["parameter"])
            if parameter is not None and name != parameter:
                continue
            method = method_of(measurement)
            series = by_series.setdefault((name, method), Series(parameter=name, method=method))
            series.points.append(
                SeriesPoint(
                    performed_at=event.performed_at,
                    value=float(measurement["value"]),
                    unit=str(measurement["unit"]),
                    source=str(measurement.get("source") or "manual"),
                    event_key=event.key,
                    sample_depth_cm=measurement.get("sample_depth_cm"),
                    content_class=measurement.get("content_class"),
                )
            )
            entries = timeline.setdefault(name, [])
            if not entries or entries[-1][0] != event.performed_at:
                entries += [
                    (event.performed_at, method)
                ]  # one entry per analysis: two methods inside one event are no change
    changes: list[MethodChange] = []
    for name, entries in timeline.items():
        for (_, before), (at, after) in zip(entries, entries[1:], strict=False):
            if before != after:
                changes += [MethodChange(parameter=name, at=at, from_method=before, to_method=after)]
    ordered = sorted(by_series.values(), key=lambda each: (each.parameter, each.method))
    return ordered, sorted(changes, key=lambda each: (each.at, each.parameter))


LimingStatus = Literal["likely", "not_indicated", "not_assessable"]
LimingReason = Literal[
    "below_target",
    "at_or_above_target",
    "no_ph",
    "not_native_soil",
    "ph_method_not_cacl2",
    "texture_unknown",
    "no_target_ph",
]


@dataclass(frozen=True)
class LimingHint:
    """Whether liming is *likely* worth it, and why - a text, never an amount (hint-only list: no lime amount)."""

    status: LimingStatus
    reason: LimingReason


def liming_hint(profile: SoilProfile | None) -> LimingHint:
    """The liming hint of a bed profile; the first missing precondition is the reason when none is possible.

    ``likely`` only when the bed is grown soil, its pH was measured in CaCl2, its texture is known and the pH is below
    the stated ``target_ph``. ``ph`` and ``target_ph`` are compared as they are - nothing is converted or derived.
    """
    if profile is None or profile.ph is None:
        return LimingHint("not_assessable", "no_ph")
    if profile.growing_medium_kind != GrowingMediumKind.NATIVE_SOIL:
        return LimingHint("not_assessable", "not_native_soil")
    if profile.ph_method != PhMethod.CACL2:
        return LimingHint("not_assessable", "ph_method_not_cacl2")
    if profile.soil_texture == SoilTexture.UNKNOWN:
        return LimingHint("not_assessable", "texture_unknown")
    if profile.target_ph is None:
        return LimingHint("not_assessable", "no_target_ph")
    if profile.ph < profile.target_ph:
        return LimingHint("likely", "below_target")
    return LimingHint("not_indicated", "at_or_above_target")
