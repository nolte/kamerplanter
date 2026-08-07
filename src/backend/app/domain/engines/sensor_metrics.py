"""SSOT for classifying a ``Sensor.metric_type`` string (REQ-005 §2).

``Sensor.metric_type`` is a bare ``str`` — the frontend offers a fixed pick list
(``SensorCreateDialog.tsx``), but nothing stops an importer, the Home-Assistant
suggestion mapper or an older document from carrying a name outside it. Every
consumer that wants to know *"is this an ambient air temperature?"* therefore has
to guess, and until this module existed two consumers guessed **differently**:

* :func:`app.domain.engines.frost_warning_engine.pick_air_temperature` used an
  exact allow-list that *includes* ``water_temp_celsius``.
* ``QuarterClimateService._is_air_temperature`` used the substring rule
  ``"temp" in metric and "water" not in metric``, which *excludes*
  ``water_temp_celsius`` but *accepts* ``substrate_temp_celsius``.

Those two answers cannot both be right, and a third copy was about to be written
for the diary environment snapshot. This module is that one place; both existing
call sites consume it.

**The reconciliation, spelled out** — because unifying two heuristics necessarily
picks a winner:

* ``water_temp_celsius`` is **not** an air temperature. It is accepted by the
  frost path only as a *tolerated alias*, and only there, because
  :meth:`SensorService.get_ha_entities` maps every Home-Assistant ``temperature``
  device class onto that key, so a location sensor created from an HA suggestion
  legitimately carries it. That is a naming accident of the suggestion mapper,
  not a statement about the probe — which is why it needs an opt-in
  (``accept_aliases=True``) instead of living in the canonical tuple.
* ``substrate_temp_celsius`` / ``soil_temp…`` / ``leaf_temp…`` / ``root_temp…``
  are **not** air temperatures either, and the old quarter-climate heuristic
  accepted them. A winter quarter that reads "too cold" from a substrate probe is
  answering a different question than the one asked ("is the room too cold for the
  plant"), so the narrowing is a fix, not a regression.
* Anything else containing ``temp`` is treated as ambient. The vocabulary is open,
  so an unknown ``room_temp_c`` from an import must still work; the exclusion
  markers carry the knowledge, not an exhaustive allow-list.
"""

from __future__ import annotations

#: Canonical ambient-air-temperature metric types, in priority order.
#:
#: ``temperature_celsius`` is what the frontend writes for a non-tank sensor;
#: ``air_temp_celsius`` is in use on location sensors (see the quarter-climate
#: tests) and is the unambiguous spelling.
AIR_TEMPERATURE_METRIC_TYPES: tuple[str, ...] = (
    "temperature_celsius",
    "air_temp_celsius",
)

#: Metric types a consumer MAY accept as an air temperature although they do not
#: name one — opt-in via ``accept_aliases=True``. See the module docstring for
#: why ``water_temp_celsius`` is on this list rather than in the canonical tuple.
TOLERATED_AIR_TEMPERATURE_ALIASES: tuple[str, ...] = ("water_temp_celsius",)

#: Ordered candidates for a consumer that reads a live-state ``values`` map keyed
#: by ``metric_type`` and wants the single best air temperature: canonical first,
#: tolerated alias last.
AIR_TEMPERATURE_LIVE_PRIORITY: tuple[str, ...] = AIR_TEMPERATURE_METRIC_TYPES + TOLERATED_AIR_TEMPERATURE_ALIASES

#: Canonical relative-humidity metric types, in priority order.
HUMIDITY_METRIC_TYPES: tuple[str, ...] = (
    "humidity_percent",
    "relative_humidity_percent",
)

#: Substrings that disqualify a ``…temp…`` metric from being ambient air: each
#: names a *different* physical quantity measured by a differently-placed probe.
NON_AIR_TEMPERATURE_MARKERS: tuple[str, ...] = (
    "water",
    "nutrient",
    "reservoir",
    "solution",
    "substrate",
    "soil",
    "root",
    "leaf",
    "canopy",
)

#: Substrings that disqualify a ``…humidity…`` metric from being ambient air
#: humidity — substrate/soil moisture is a wholly different measurement that some
#: integrations nonetheless label "humidity".
NON_AIR_HUMIDITY_MARKERS: tuple[str, ...] = (
    "substrate",
    "soil",
    "root",
)


def normalize_metric_type(metric_type: str | None) -> str:
    """Lower-case, whitespace-stripped form used by every check in this module."""
    return (metric_type or "").strip().lower()


def is_air_temperature(metric_type: str | None, *, accept_aliases: bool = False) -> bool:
    """Whether ``metric_type`` denotes the **ambient air** temperature.

    Args:
        metric_type: The raw ``Sensor.metric_type`` value; ``None``/blank is not
            an air temperature.
        accept_aliases: Also accept :data:`TOLERATED_AIR_TEMPERATURE_ALIASES`.
            Only the frost-warning path sets this, and the module docstring
            records why. A caller that is deciding whether a *room* is warm
            enough must leave it off, or a heated reservoir answers for the room.

    Returns:
        ``True`` for a canonical name, for an accepted alias, or for any other
        name mentioning ``temp`` that carries none of
        :data:`NON_AIR_TEMPERATURE_MARKERS`.
    """
    normalized = normalize_metric_type(metric_type)
    if not normalized:
        return False
    if normalized in AIR_TEMPERATURE_METRIC_TYPES:
        return True
    if accept_aliases and normalized in TOLERATED_AIR_TEMPERATURE_ALIASES:
        return True
    if normalized in TOLERATED_AIR_TEMPERATURE_ALIASES:
        return False
    if any(marker in normalized for marker in NON_AIR_TEMPERATURE_MARKERS):
        return False
    return "temp" in normalized


def is_humidity(metric_type: str | None) -> bool:
    """Whether ``metric_type`` denotes ambient **relative air humidity**.

    Mirrors :func:`is_air_temperature`: canonical names first, then an open
    substring rule minus the markers that name substrate moisture instead. There
    is no tolerated-alias case — no suggestion mapper misfiles humidity.
    """
    normalized = normalize_metric_type(metric_type)
    if not normalized:
        return False
    if normalized in HUMIDITY_METRIC_TYPES:
        return True
    if any(marker in normalized for marker in NON_AIR_HUMIDITY_MARKERS):
        return False
    return "humidity" in normalized
