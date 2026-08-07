"""How a live-state map is keyed, and how one number is derived from it (REQ-005 §2).

A live reading belongs to a **sensor**, not to a metric. Keying a live-state map
by ``metric_type`` encodes an assumption the product does not enforce — one
sensor per metric per location — and growers break it on purpose: two
thermometers at opposite ends of a tent is exactly what you install when you
suspect a gradient. A map keyed by metric physically cannot hold both, so one of
them disappears (Issue #977).

The live state therefore carries **two** maps:

* ``readings`` — keyed by sensor key, one entry per sensor that answered. This is
  the full truth and the only map that can be trusted to be complete.
* ``values`` — the **derived single-value view**, keyed by ``metric_type``, for
  the consumers that legitimately want one number per metric (the frost warning,
  a watering suggestion, a gauge on a dashboard). It is *derived*, never
  authoritative, and it says so in-band: every entry carries ``sensor_count`` and
  ``superseded_sensor_keys``, so a consumer can always tell that more than one
  reading existed.

**The selection rule of the derived view: the freshest reading wins.**

* The measurement instant is taken from ``last_reported`` → ``last_updated`` →
  ``last_changed``, in that order — Home Assistant's own order of decreasing
  reliability, and the same order the diary environment snapshot uses to judge
  staleness.
* A reading with **no** timestamp at all ranks last. Its freshness is
  unfalsifiable, and an unfalsifiable claim must not beat a dated one.
* Ties — including "none of them is timestamped" — are broken by the
  lexicographically smallest sensor key, so the view is **deterministic** and
  never depends on repository order. "First candidate wins" is what the old code
  did by accident; this is the same class of answer made deliberate and stable.

Why freshest, and not something else:

* **Not a named primary sensor.** ``Sensor`` has no such field, and introducing
  one would leave every existing installation on whatever accident it has today
  until the grower acts. A rule that needs a migration *and* a human is not a
  rule, it is a plan.
* **Not an average.** Averaging the two ends of a tent reports a temperature that
  no point in the tent has, and erases the very gradient the second sensor was
  installed to reveal.
* **Freshest** answers the question a *live* view is asked — "what is it right
  now" — from data Home Assistant already returns with every state.

A consumer that needs a different answer takes it from ``readings`` and says so.
:func:`app.domain.engines.frost_warning_engine.pick_air_temperature` is exactly
such a consumer: a frost warning must fire when *any* thermometer sees frost, so
it reads all of them and picks the coldest.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from app.common.datetimes import ensure_aware_utc

__all__ = [
    "READING_TIMESTAMP_FIELDS",
    "derive_single_value_view",
    "reading_measured_at",
    "sort_readings",
]

#: The fields a live reading may carry its measurement instant in, most reliable
#: first. ``last_changed`` moves only when the state *string* changes, so a
#: healthy sensor reporting a constant 22.0 °C carries one that is hours old;
#: ``last_updated`` has nearly the same problem. ``last_reported`` (Home
#: Assistant >= 2024.6) moves on every report and is the only one that answers
#: "when was this measured". Older installations fall through to the others.
READING_TIMESTAMP_FIELDS: tuple[str, ...] = ("last_reported", "last_updated", "last_changed")


def reading_measured_at(reading: Mapping[str, Any]) -> datetime | None:
    """When a live reading was actually taken, or ``None`` if it does not say.

    Args:
        reading: One live-state reading entry.

    Returns:
        The first parsable instant among :data:`READING_TIMESTAMP_FIELDS`, as an
        aware UTC datetime, or ``None`` when the reading carries no usable
        timestamp. An unparsable timestamp is treated as absent rather than
        raised: Home Assistant is an external system, and one malformed stamp
        must not take a whole live query down.
    """
    for field in READING_TIMESTAMP_FIELDS:
        raw = reading.get(field)
        if raw is None:
            continue
        # NB: the ``as exc`` binding is deliberate — a bare tuple-except without
        # it is miscompiled by ``ruff format`` into invalid ``except A, B:``.
        try:
            stamp = ensure_aware_utc(raw)
        except (ValueError, TypeError) as exc:  # noqa: F841
            continue
        if stamp is not None:
            return stamp
    return None


def _selection_key(reading: Mapping[str, Any]) -> tuple[bool, float, str]:
    """Sort key implementing the module's selection rule — best reading first."""
    stamp = reading_measured_at(reading)
    return (
        # Untimestamped readings last …
        stamp is None,
        # … timestamped ones freshest-first (negated, since sorting is ascending) …
        -stamp.timestamp() if stamp is not None else 0.0,
        # … and ties broken by sensor key, never by input order.
        str(reading.get("sensor_key") or reading.get("entity_id") or ""),
    )


def sort_readings(readings: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Order live readings by the selection rule — the best candidate first.

    Args:
        readings: The reading entries to order (any iterable).

    Returns:
        A new list of shallow copies, freshest first, ties broken by sensor key.
        Deterministic for any input order.
    """
    return [dict(reading) for reading in sorted(readings, key=_selection_key)]


def derive_single_value_view(readings: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Derive the single-value-per-metric view from the full readings map.

    Args:
        readings: The lossless live-state map, keyed by sensor key.

    Returns:
        A map keyed by ``metric_type``. Each entry is the winning reading (see
        the module docstring for the rule) plus two fields that keep the
        collapse visible:

        * ``sensor_count`` — how many sensors answered this metric. ``1`` means
          nothing was left out.
        * ``superseded_sensor_keys`` — the keys of the readings this view does
          **not** show, in selection order, so a consumer can look them up in
          ``readings``. Empty when ``sensor_count`` is ``1``.

        A reading without a ``metric_type`` is skipped: it cannot be filed under
        one, and inventing a key for it would be worse than omitting it from a
        view that is derived anyway — it stays in ``readings``.
    """
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for reading in readings.values():
        metric_type = str(reading.get("metric_type") or "")
        if not metric_type:
            continue
        grouped.setdefault(metric_type, []).append(reading)

    view: dict[str, dict[str, Any]] = {}
    for metric_type, group in grouped.items():
        ordered = sort_readings(group)
        winner = ordered[0]
        winner["sensor_count"] = len(ordered)
        winner["superseded_sensor_keys"] = [
            str(other.get("sensor_key")) for other in ordered[1:] if other.get("sensor_key")
        ]
        view[metric_type] = winner
    return view
