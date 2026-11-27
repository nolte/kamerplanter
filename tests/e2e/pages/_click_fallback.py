"""Record every covering-blind click fallback instead of taking it silently (#3157).

## Why this exists

:meth:`BasePage.scroll_and_click` -- and through it ``wait_and_click``,
``toggle_switch``, ``click_row_via_column`` and the header helpers -- falls back
to a JavaScript activation when the driver refuses the native click with
``ElementClickInterceptedException`` or ``ElementNotInteractableException``. A
JS ``click()`` (or the mousedown pair a MUI Select trigger gets) is dispatched
on the element **whatever lies on top of it**: a control a fixed bar, a
snackbar or a dialog covers for a real user is still activated, and the test
passes. ``NotificationCenterPage.close_drawer`` has the same shape with an
``Escape`` key in place of the JS click.

Making that fallback fail is the goal of #3157, but nobody knows how many of the
~850 E2E tests rely on it today. This module is the **measurement step**: at
each fallback site it records one event -- which helper, which locator, which
exception, and what ``document.elementFromPoint`` returns at the target's centre
*before* the fallback activation -- and then lets the fallback proceed exactly
as before. No click is added, removed or redirected, and nothing here can fail a
test: every read is wrapped, and a read that cannot be made is recorded as
``probe_failed``.

## Where the events go

Events are kept in :data:`_pending`, a per-process list. The reporting plugin
(``tests/e2e/_click_fallback_report.py``) drains it after every test phase,
attaches the events to that phase's report, and the controlling pytest process
-- the xdist controller, or the only process without xdist -- writes them as
JSON Lines and prints a summary at the end of the session. This module itself
knows nothing about pytest, so it stays importable by the browser-free
self-tests and by any page object.

## What ``covered`` means

``relation`` is how the element at the target's centre point relates to the
target:

* ``self`` / ``descendant`` -- a pointer press at the centre would reach the
  target: ``covered`` is ``False``. The native click was refused for another
  reason (an animation in flight, a zero-size box, the driver's own scroll
  putting it under a fixed bar *before* ours moved it back).
* ``other`` -- an unrelated element lies on top: ``covered`` is ``True``.
* ``ancestor`` -- the centre hits a container of the target, i.e. the target
  itself is not hittable there (``pointer-events: none``, collapsed box). A
  press would reach the ancestor, not the target, so ``covered`` is ``True``;
  the relation is kept so triage can tell it from a real overlay.
* ``outside_viewport`` / ``detached`` -- there is no centre point in the
  viewport, or the node is gone. ``covered`` is ``None``: no verdict, not a
  guess.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

#: Events recorded since the last :func:`drain` -- one test phase's worth, because
#: one pytest process runs one test at a time.
_pending: list[dict[str, Any]] = []

#: The longest exception message kept per event. Chrome's interception message
#: names the element that would receive the click and carries its whole opening
#: tag, which is useful up to a point and noise beyond it.
MESSAGE_LIMIT = 300

#: Reads, in one round trip, what a pointer press at the target's centre would
#: hit. The leading comment is the script's identity for the self-test's fake
#: driver, the same convention as ``/* settledHit */`` in ``base_page.py``.
COVER_PROBE_JS = """/* coverProbe */
var el = arguments[0];
function describe(n) {
  if (!n || n.nodeType !== 1) return null;
  var cls = String(n.getAttribute('class') || '').trim().split(/\\s+/).slice(0, 4).join(' ');
  return {
    tag: n.tagName.toLowerCase(),
    testid: n.getAttribute('data-testid'),
    id: n.id || null,
    cls: cls.slice(0, 120)
  };
}
var viewport = {width: window.innerWidth, height: window.innerHeight};
if (!el.isConnected) {
  return {relation: 'detached', target: describe(el), hit: null, rect: null, point: null,
          viewport: viewport};
}
var r = el.getBoundingClientRect();
var x = r.left + r.width / 2, y = r.top + r.height / 2;
var at = document.elementFromPoint(x, y);
var relation = !at ? 'outside_viewport'
  : at === el ? 'self'
  : el.contains(at) ? 'descendant'
  : at.contains(el) ? 'ancestor'
  : 'other';
return {
  relation: relation,
  target: describe(el),
  hit: describe(at),
  rect: {x: r.left, y: r.top, width: r.width, height: r.height},
  point: {x: x, y: y},
  viewport: viewport
};
"""

#: ``relation`` -> ``covered``. See the module docstring for the reasoning.
COVERED_BY_RELATION: dict[str, bool | None] = {
    "self": False,
    "descendant": False,
    "ancestor": True,
    "other": True,
    "outside_viewport": None,
    "detached": None,
}

#: The files whose frames are skipped when naming the caller of a fallback: the
#: helper chain itself, so the caller is the page object or test that asked.
_HELPER_FILES = ("base_page.py", "_click_fallback.py")


def describe_locator(locator: object) -> str | None:
    """Render a Selenium ``(By, value)`` locator as ``"<by>: <value>"``, else ``None``."""
    if isinstance(locator, tuple) and len(locator) == 2:
        return f"{locator[0]}: {locator[1]}"
    return None


def _short(text: object) -> str:
    first = str(text).strip().splitlines()[0] if str(text).strip() else ""
    return first[:MESSAGE_LIMIT]


def _caller() -> str | None:
    """Name the first frame outside the click helpers as ``<dir>/<file>:<line> <qualname>``."""
    try:
        frame = sys._getframe(1)
        while frame is not None:
            filename = frame.f_code.co_filename
            if not filename.endswith(_HELPER_FILES):
                parts = filename.replace("\\", "/").split("/")
                where = "/".join(parts[-2:])
                return f"{where}:{frame.f_lineno} {frame.f_code.co_qualname}"
            frame = frame.f_back
    except Exception:  # noqa: BLE001 -- a naming aid must never fail the click it names
        return None
    return None


def probe_cover(execute_script: Callable[..., object], element: object) -> dict[str, Any]:
    """Ask what a press at *element*'s centre would hit; never raises.

    Answers the probe fields of an event: ``probe`` is ``"ok"`` with ``relation``,
    ``covered``, ``target``, ``hit``, ``rect``, ``point`` and ``viewport``, or
    ``"probe_failed"`` with ``probe_error``. The catch is deliberately broad:
    the probe runs on the way to a click the test is relying on, and a
    measurement that could break that click would change what it measures.
    """
    try:
        answer = execute_script(COVER_PROBE_JS, element)
    except Exception as exc:  # noqa: BLE001 -- see the docstring
        return {"probe": "probe_failed", "probe_error": f"{type(exc).__name__}: {_short(exc)}"}
    if not isinstance(answer, dict) or answer.get("relation") not in COVERED_BY_RELATION:
        return {"probe": "probe_failed", "probe_error": f"unexpected answer: {_short(answer)}"}
    relation = answer["relation"]
    return {
        "probe": "ok",
        "relation": relation,
        "covered": COVERED_BY_RELATION[relation],
        "target": answer.get("target"),
        "hit": answer.get("hit"),
        "rect": answer.get("rect"),
        "point": answer.get("point"),
        "viewport": answer.get("viewport"),
    }


def record_fallback(
    *,
    helper: str,
    activation: str,
    trigger: BaseException | str,
    locator: object = None,
    probe: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Append one fallback event to :data:`_pending` and return it; never raises.

    *probe* is :func:`probe_cover`'s answer, or ``None`` when the caller could not
    ask (an open user prompt must not receive a script) -- recorded as
    ``probe_failed`` with the reason in ``probe_error``.
    """
    try:
        if isinstance(trigger, BaseException):
            trigger_name, trigger_message = type(trigger).__name__, _short(trigger)
        else:
            trigger_name, trigger_message = trigger, ""
        event: dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds"),
            # Provisional: the reporting plugin overwrites both with the report's own
            # nodeid and phase, which are authoritative. Kept for an event that is
            # drained by something else (a self-test, a debugging session).
            "nodeid": os.environ.get("PYTEST_CURRENT_TEST", "").rsplit(" (", 1)[0] or None,
            "worker": os.environ.get("PYTEST_XDIST_WORKER"),
            "helper": helper,
            "caller": _caller(),
            "activation": activation,
            "locator": describe_locator(locator),
            "trigger": trigger_name,
            "trigger_message": trigger_message,
        }
        event.update(
            probe
            if probe is not None
            else {"probe": "probe_failed", "probe_error": "probe skipped: a user prompt is open"}
        )
        _pending.append(event)
        return event
    except Exception:  # noqa: BLE001 -- recording must never fail the click it records
        return None


def drain() -> list[dict[str, Any]]:
    """Return and forget every event recorded since the last drain."""
    events = list(_pending)
    _pending.clear()
    return events
