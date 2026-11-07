"""Soil analyses as care events: what lands in the bed's profile, and the series over time (REQ-053 §15.1, GP-FR-122).

Pure rules, no database (WP 8.7, #2650).

* **The profile is a function of the open analyses** (:func:`derive_profile`, #2706): after every store, void,
  correction or withdrawal of a soil analysis the measured fields - ``ph`` with ``ph_method``, ``ec_ms_cm`` with
  ``ec_method``, ``humus_percent``, ``caco3_percent`` - and ``last_analysis_at`` are derived again, per parameter
  from the newest open analysis that measured it (:func:`profile_values`). A value is taken over exactly as measured
  and only when its unit is the profile's own (``pH``, ``mS/cm`` = ``dS/m``, ``%``) - **the system never converts**
  (U-002/U-003, E-10). P, K, Mg and N-min are not profile fields. Per field **the newest observation wins**: the hand
  entry (``hand_values``) or the newest open analysis, so a void returns to whichever of the rest is newer.
* **Series are per method and unit** (:func:`build_series`): a conductivity is read per ``ec_method``, a pH per
  ``ph_method``, the rest per ``extraction_method``; ``unknown`` is its own method, and a value in another unit is
  another series. When the method of a parameter changes from one analysis to the next, the change is marked. Values
  of different methods or units are never merged or compared.
* **"Liming likely" is a hint, never an amount** (:func:`liming_hint`): only for grown soil, only for a pH measured in
  CaCl2 (the reference of the lab target ranges, R-008), only with a known ``soil_texture`` and only against a
  ``target_ph`` someone *stated* (the profile never derives one, "stays null" item 17). Every other case says why no
  assessment is possible - a pH by water or by probe is never converted to CaCl2 (hint-only list).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.common.datetimes import ensure_aware_utc
from app.common.enums import GrowingMediumKind, PhMethod, SoilTexture
from app.domain.models.site import SoilProfile

#: The care-event category of a soil analysis.
SOIL_ANALYSIS_CATEGORY = "soil_analysis"

#: Unit spellings that are the same number (strip + lower first): ``dS/m`` is ``mS/cm``, ``percent`` is ``%``.
_UNIT_ALIASES: dict[str, str] = {"ds/m": "ms/cm", "percent": "%"}
#: How a normalised unit is reported; a unit not listed is reported in its normalised (lower-case) form.
_UNIT_DISPLAY: dict[str, str] = {"ph": "pH", "ms/cm": "mS/cm", "%": "%"}
#: The normalised unit each profile parameter is stored in; a value in any other unit is left out, never converted.
_PROFILE_UNITS: dict[str, str] = {"ph": "ph", "ec": "ms/cm", "humus": "%", "caco3": "%"}
#: Per parameter: the profile's value field and its method field (``None`` where it has none).
_PROFILE_GROUPS: dict[str, tuple[str, str | None]] = {
    "ph": ("ph", "ph_method"),
    "ec": ("ec_ms_cm", "ec_method"),
    "humus": ("humus_percent", None),
    "caco3": ("caco3_percent", None),
}
#: The measured profile fields with their method fields (``None`` where there is none), in one place: the derivation,
#: the hand entries of ``PATCH /locations`` and the services all read this tuple.
PROFILE_MEASURED_FIELDS: tuple[tuple[str, str | None], ...] = tuple(_PROFILE_GROUPS.values())

#: The server-owned bookkeeping of the profile; a derivation writes them, a location write never takes them as sent.
_SERVER_FIELDS: tuple[str, ...] = ("last_analysis_at", "hand_values")
#: The instant of a hand entry classified from a row stored before ``hand_values``: older than every analysis, so
#: any open analysis that measured the field supersedes it, and it survives otherwise.
LEGACY_HAND_AT = datetime.min.replace(tzinfo=UTC)

UNKNOWN_METHOD = "unknown"


def writes_the_soil_profile(category: Any, measurements: Any) -> bool:
    """The one predicate (#2706): whether an event of ``category`` with ``measurements`` feeds the bed's profile.

    A soil analysis with at least one measurement; storing, voiding, correcting or withdrawing one derives the
    profile again. Every caller (insert, void, supersede, task completion and its undo) asks this.
    """
    return category == SOIL_ANALYSIS_CATEGORY and bool(measurements)


def normal_unit(unit: Any) -> str:
    """A unit as the profile and the series compare it: stripped, lower-case, aliases folded (``dS/m`` = ``mS/cm``)."""
    text: str = str(unit)
    stripped: str = text.strip()
    folded: str = stripped.lower()
    aliases: dict[str, str] = _UNIT_ALIASES
    return aliases.get(folded, folded)


def _spelling(unit: Any) -> str:
    """A unit as entered, without surrounding blanks (the reported spelling of a unit the profile does not know)."""
    text: str = str(unit)
    return text.strip()


def _known_display(normal: str) -> str | None:
    """The fixed spelling of a unit the profile knows (``pH``, ``mS/cm``, ``%``), else ``None``."""
    display: dict[str, str] = _UNIT_DISPLAY
    return display.get(normal)


def read_instant(value: Any) -> datetime | None:
    """A stored instant as aware UTC through :func:`~app.common.datetimes.ensure_aware_utc`; ``None`` when unreadable.

    Stored documents are not trusted to hold valid ISO text: an unreadable value reads as absent instead of failing
    the derivation of a whole bed.
    """
    if not isinstance(value, datetime | str):
        return None
    try:
        return ensure_aware_utc(value)
    except ValueError:
        return None


def _utc(instant: datetime) -> datetime:
    aware = ensure_aware_utc(instant)
    return aware if aware is not None else instant


def _depth_rank(measurement: Mapping[str, Any]) -> float:
    depth = measurement.get("sample_depth_cm")
    return float(depth) if isinstance(depth, int | float) and not isinstance(depth, bool) else float("inf")


def _in_profile_unit(measurement: Mapping[str, Any]) -> bool:
    parameter = str(measurement["parameter"])
    return parameter in _PROFILE_UNITS and normal_unit(measurement["unit"]) == _PROFILE_UNITS[parameter]


def profile_values(measurements: Sequence[Mapping[str, Any]] | None) -> dict[str, dict[str, Any]]:
    """The profile values of one analysis, per parameter: ``{"ph": {"ph": 6.4, "ph_method": "cacl2"}, ...}``.

    Only values in the profile's unit, taken as measured (no conversion). A pH always brings its ``ph_method`` (a new
    value never keeps the method of an old one), a conductivity its ``ec_method`` (``unknown`` when absent). Of several
    measurements of one parameter the **shallowest** sample depth wins (the topsoil is what the profile describes); a
    measurement without a depth ranks after every one with a depth; at an equal rank the last one listed wins.
    """
    chosen: dict[str, tuple[float, Mapping[str, Any]]] = {}
    measurement: Mapping[str, Any]
    for measurement in measurements or ():
        if not _in_profile_unit(measurement):
            continue
        parameter = str(measurement["parameter"])
        rank = _depth_rank(measurement)
        if parameter not in chosen or rank <= chosen[parameter][0]:
            chosen[parameter] = (rank, measurement)
    values: dict[str, dict[str, Any]] = {}
    for parameter, (_, measurement) in chosen.items():
        value_field, method_field = _PROFILE_GROUPS[parameter]
        group: dict[str, Any] = {value_field: measurement["value"]}
        if parameter == "ph" and method_field:
            group[method_field] = measurement.get("ph_method")
        elif parameter == "ec" and method_field:
            group[method_field] = measurement.get("ec_method") or UNKNOWN_METHOD
        values[parameter] = group
    return values


def _legacy_hand_values(current: Mapping[str, Any], history: Iterable[AnalysisEvent]) -> dict[str, dict[str, Any]]:
    """The hand entries of a profile stored before ``hand_values`` (#2706).

    A present value equal to one some analysis of the bed (open, voided or superseded) measured for its parameter in
    the profile's unit is analysis-sourced - the forward writes before #2706 stored values as measured, so an equal
    value is the trace they left. Any other present value becomes a hand entry at :data:`LEGACY_HAND_AT`.
    """
    measured: dict[str, set[float]] = {}
    for analysis in history:
        for measurement in analysis.measurements:
            if _in_profile_unit(measurement):
                measured.setdefault(str(measurement["parameter"]), set()).add(float(measurement["value"]))
    entries: dict[str, dict[str, Any]] = {}
    groups: dict[str, tuple[str, str | None]] = _PROFILE_GROUPS
    for parameter, (value_field, method_field) in groups.items():
        value = current.get(value_field)
        if not isinstance(value, int | float) or float(value) in measured.get(parameter, set()):
            continue
        entries[value_field] = {
            "value": value,
            "method": current.get(method_field) if method_field else None,
            "at": LEGACY_HAND_AT,
        }
    return entries


def _hand_entries(raw: Any) -> dict[str, dict[str, Any]]:
    """The stored hand entries with readable instants; an entry without one is dropped."""
    entries: dict[str, dict[str, Any]] = {}
    stored: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
    for name in stored:
        item = stored[name]
        if not isinstance(item, Mapping):
            continue
        entry: Mapping[str, Any] = item
        at = read_instant(entry.get("at"))
        if at is not None:
            entries[str(name)] = {"value": entry.get("value"), "method": entry.get("method"), "at": at}
    return entries


def hand_values_after_edit(
    stored: Mapping[str, Any], sent: Mapping[str, Any], at: datetime
) -> dict[str, dict[str, Any]]:
    """The hand entries after a location write (``PATCH /locations``, #2706): one new entry per edited field.

    ``stored`` is the profile as stored (its measured fields are the effective values), ``sent`` the body's profile.
    A measured field whose ``(value, method)`` differs from the stored one gets the entry ``{value, method, at}``
    (``value = null`` = cleared by hand); an unchanged field gets none - also on a row without ``hand_values``, whose
    other values the derivation's legacy rule classifies (the caller derives such a row before the edit).
    """
    raw = stored.get("hand_values")
    entries: dict[str, dict[str, Any]] = {
        str(name): dict(entry) for name, entry in (raw.items() if isinstance(raw, Mapping) else ())
    }
    for value_field, method_field in PROFILE_MEASURED_FIELDS:
        sent_pair = (sent.get(value_field), sent.get(method_field) if method_field else None)
        stored_pair = (stored.get(value_field), stored.get(method_field) if method_field else None)
        if sent_pair != stored_pair:
            entries[value_field] = {"value": sent_pair[0], "method": sent_pair[1], "at": at}
    return entries


def derive_profile(
    current: Mapping[str, Any], analyses: Iterable[AnalysisEvent], *, history: Iterable[AnalysisEvent] = ()
) -> dict[str, Any]:
    """The bed's profile from its hand entries and its open analyses: per field the newest observation wins (#2706).

    ``analyses`` are the bed's **open** soil analyses (neither voided nor superseded); ``history`` every analysis of
    the bed (only read for a row stored before ``hand_values``, see :func:`_legacy_hand_values`). Per measured-value
    field the candidates are its hand entry (``at``) and the newest open analysis that measured it in the profile's
    unit (``performed_at``; at an equal ``performed_at`` the one listed first - the caller lists the later written
    first). The later one wins, a tie goes to the hand entry; a hand entry with ``value = null`` clears the field. No
    candidate: the field is empty. A void therefore returns to the newer of what is left. ``last_analysis_at`` is the
    ``performed_at`` of the newest analysis whose value won, absent when none did. Every other field of ``current``
    is kept as it is. A bed without a profile, a hand entry or an analysis value stays without one (``{}``).
    """
    stored = current.get("hand_values")
    hand = _hand_entries(stored) if isinstance(stored, Mapping) else _legacy_hand_values(current, history)
    newest: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for analysis in sorted(analyses, key=lambda each: _utc(each.performed_at), reverse=True):
        for parameter, group in profile_values(analysis.measurements).items():
            newest.setdefault(parameter, (_utc(analysis.performed_at), group))
    measured_fields = {name for pair in PROFILE_MEASURED_FIELDS for name in pair if name}
    groups: dict[str, tuple[str, str | None]] = _PROFILE_GROUPS
    derived = {
        name: value for name, value in current.items() if name not in _SERVER_FIELDS and name not in measured_fields
    }
    last: datetime | None = None
    for parameter, (value_field, method_field) in groups.items():
        entry = hand.get(value_field)
        candidate = newest.get(parameter)
        if entry is not None and (candidate is None or entry["at"] >= candidate[0]):
            if entry["value"] is not None:
                derived[value_field] = entry["value"]
                if method_field is not None:
                    derived[method_field] = entry["method"]
        elif candidate is not None:
            at, group = candidate
            derived.update(group)
            last = at if last is None or at > last else last
    if not current and not hand and last is None:
        return {}
    if last is not None:
        derived["last_analysis_at"] = last
    derived["hand_values"] = {name: dict(entry) for name, entry in sorted(hand.items())}
    return derived


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
    """The points of one parameter measured by one method in one unit, oldest first.

    The unit is part of the series (#2706): ``1100 µS/cm`` and ``1.1 mS/cm`` of the same method are two series,
    because the system never converts. Series are grouped on the unit normalised as the profile reads it, so
    ``mS/cm``, ``ms/cm `` and ``dS/m`` are one series; each point keeps the unit as entered.
    """

    parameter: str
    method: str
    unit: str = ""
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
    """Series per ``(parameter, method, unit)`` and the marked method changes; never merges two methods or units.

    A change is marked per analysis (not per instant, so two analyses at the same ``performed_at`` are two steps):
    when an analysis measures a parameter by **no** method the previous analysis of that parameter used, its values
    are comparable with none before - one change per ``(from, to)`` pair of the two method sets. Two methods inside
    one analysis are no change, and neither is a later analysis that keeps one of them.
    """
    by_series: dict[tuple[str, str, str], Series] = {}
    timeline: dict[str, list[tuple[datetime, tuple[str, ...]]]] = {}
    event: AnalysisEvent
    measurement: Mapping[str, Any]
    for event in sorted(events, key=lambda each: (_utc(each.performed_at), each.key)):
        methods: dict[str, list[str]] = {}
        for measurement in event.measurements:
            name = str(measurement["parameter"])
            if parameter is not None and name != parameter:
                continue
            method = method_of(measurement)
            unit_key = normal_unit(measurement["unit"])
            # The series reports the fixed spelling of a known unit, else the spelling of its **oldest** measurement
            # (events run oldest first); grouping is on the normalised key either way.
            series = by_series.setdefault(
                (name, method, unit_key),
                Series(
                    parameter=name,
                    method=method,
                    unit=_known_display(unit_key) or _spelling(measurement["unit"]),
                ),
            )
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
            used = methods.setdefault(name, [])
            if method not in used:
                used.append(method)
        for name, used in methods.items():
            timeline.setdefault(name, []).append((event.performed_at, tuple(sorted(used))))
    changes: list[MethodChange] = []
    for name, entries in timeline.items():
        for (_, before), (at, after) in zip(entries, entries[1:], strict=False):
            if set(before) & set(after):
                continue
            changes += [
                MethodChange(parameter=name, at=at, from_method=old, to_method=new) for old in before for new in after
            ]
    ordered = [by_series[key] for key in sorted(by_series)]
    return ordered, sorted(changes, key=lambda each: (_utc(each.at), each.parameter))


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
