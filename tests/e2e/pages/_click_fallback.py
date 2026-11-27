"""Record every covering-blind click fallback instead of taking it silently (#3157).

## Why this exists

:meth:`BasePage.scroll_and_click` -- and through it ``wait_and_click``,
``toggle_switch``, ``click_row_via_column`` and the header helpers -- falls back
to a JavaScript activation when the driver refuses the native click with
``ElementClickInterceptedException`` or ``ElementNotInteractableException``. A
JS ``click()`` (or the mousedown pair a MUI Select trigger gets) is dispatched
on the element **whatever lies on top of it**: a control a fixed bar, a
snackbar or a dialog covers for a real user is still activated, and the test
passes. ``NotificationCenterPage.close_drawer`` had the same shape with an
``Escape`` key in place of the JS click, until step 2 removed it.

Step 1 of #3157 measured how many of the ~850 E2E tests relied on it: at each
fallback site this module records one event -- which helper, which locator,
which exception, and what ``document.elementFromPoint`` returns at the target's
centre *before* the fallback activation. Nothing here can fail a test: every
read is wrapped, and a read that cannot be made is recorded as ``probe_failed``.

## Step 2: a covered control is refused, not clicked through

The measuring nightly (run 46027854891, six profiles) found 26 fallbacks, every
one on a **covered** control (app bar over the notification drawer's close
button, snackbars over the next control, an overflow menu left open) and none on
an uncovered one. So :func:`decide` now turns a refused click on a covered
control into a failure (``outcome: "raised"``, message from
:func:`refusal_message`, no click sent), keeps the JS fallback for an uncovered
control and for the no-verdict / failed-probe cases, and honours an explicit,
reasoned opt-out (``covered_ok``). The event records the ``outcome``; the
reporter counts ``raised`` and ``covered_ok`` on the summary line. The decision
is taken by the caller (``BasePage.scroll_and_click``); this module still never
raises.

## The second kind: direct coordinate-free clicks

:meth:`BasePage.click_coordinate_free` (and ``wait_and_click_coordinate_free``)
dispatch a JS ``click()`` **without** trying a native click first -- deliberately,
because the form submits they serve sit at the bottom of a page taller than the
viewport, where a coordinate click can miss (see that method's docstring). They
are as covering-blind as the fallback, and since the mobile bottom navigation
(#3149) the bottom of the page is exactly where a user can be blocked. They are
recorded with the same probe as ``kind: "direct"`` (``trigger: "direct"``, no
exception); fallbacks carry ``kind: "fallback"``. The reporter keeps the two
apart in its summary.

For a direct click ``relation: "outside_viewport"`` is its own outcome rather
than noise: the helper exists because the centre can lie below the fold. Such a
control is not *covered* -- but a user would have had to scroll to reach it.

Deliberately **not** measured: ``click_menu_option`` and
``dispatch_menu_trigger_open`` act on an open menu's options / a Select trigger
whose popover is the top layer by construction (a covering element would be the
menu itself), and ``expand_all_fields`` toggles a control inside the dialog it
reveals. Their coordinate independence protects against *moving* targets, not
against covered ones, so a probe there would measure nothing #3157 decides on.

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
var hr = at ? at.getBoundingClientRect() : null;
var relation = !at ? 'outside_viewport'
  : at === el ? 'self'
  : el.contains(at) ? 'descendant'
  : at.contains(el) ? 'ancestor'
  : 'other';
return {
  relation: relation,
  target: describe(el),
  hit: describe(at),
  hit_rect: hr ? {x: hr.left, y: hr.top, width: hr.width, height: hr.height} : null,
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
    ``covered``, ``target``, ``hit``, ``hit_rect`` (the covering element's box),
    ``rect``, ``point`` and ``viewport``, or
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
        "hit_rect": answer.get("hit_rect"),
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
    kind: str = "fallback",
    outcome: str | None = None,
    covered_ok: str | None = None,
) -> dict[str, Any] | None:
    """Append one fallback event to :data:`_pending` and return it; never raises.

    *kind* is ``"fallback"`` (a fallback after a refused native click) or
    ``"direct"`` (a deliberately coordinate-free click, see the module docstring).
    *probe* is :func:`probe_cover`'s answer, or ``None`` when the caller could not
    ask (an open user prompt must not receive a script) -- recorded as
    ``probe_failed`` with the reason in ``probe_error``. *outcome* is what the
    caller did with the refused click (see :func:`decide`), and *covered_ok* the
    reason a caller gave for expecting the covering; both are recorded only when
    given, so a direct click's event keeps the step-1 shape.
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
            "kind": kind,
            "helper": helper,
            "caller": _caller(),
            "activation": activation,
            "locator": describe_locator(locator),
            "trigger": trigger_name,
            "trigger_message": trigger_message,
        }
        if outcome is not None:
            event["outcome"] = outcome
        if covered_ok is not None:
            event["covered_ok"] = covered_ok
        event.update(
            probe
            if probe is not None
            else {"probe": "probe_failed", "probe_error": "probe skipped: a user prompt is open"}
        )
        _pending.append(event)
        return event
    except Exception:  # noqa: BLE001 -- recording must never fail the click it records
        return None


#: What a guarded click does after the driver refused the native click (#3157, step 2).
#: ``raised``: the target is covered and nobody said that is expected -- the test
#: fails naming the cover, no click is sent. ``covered_ok``: covered, but the caller
#: gave a reason (:func:`decide`); the JS activation runs. ``js_fallback``: the
#: centre hits the target (or there is no verdict); the JS activation runs.
OUTCOME_RAISED = "raised"
OUTCOME_COVERED_OK = "covered_ok"
OUTCOME_JS_FALLBACK = "js_fallback"


def decide(probe: dict[str, Any] | None, covered_ok: str | None) -> str:
    """Decide what a refused native click turns into, from the cover probe's answer.

    * **Covered** (``relation`` ``other`` or ``ancestor``): a user's press at the
      control's centre would reach another element. The JS activation would reach
      the control anyway, i.e. the test would pass where a user is blocked -- so it
      is refused (:data:`OUTCOME_RAISED`), unless the caller passed *covered_ok*, a
      reason why covering is expected there (:data:`OUTCOME_COVERED_OK`).
    * **Not covered** (``self`` / ``descendant``): the centre is the control's own;
      the driver refused for another reason (an animation in flight, its own
      scroll putting the control under a fixed bar before ours moved it back). The
      JS activation is what a pointer would do here: :data:`OUTCOME_JS_FALLBACK`.
    * **No verdict** (``outside_viewport``, ``detached``) and a **failed probe**
      (the script could not run, an open user prompt): kept as the JS fallback and
      recorded as such. Neither occurred once in the measuring nightly (run
      46027854891, six profiles: no_verdict=0, probe_failed=0), so failing on them
      would refuse clicks on evidence nobody has; the summary line counts both, and
      a nightly that shows them is the evidence to decide on.
    """
    if isinstance(probe, dict) and probe.get("probe") == "ok" and probe.get("covered") is True:
        return OUTCOME_COVERED_OK if covered_ok else OUTCOME_RAISED
    return OUTCOME_JS_FALLBACK


def _describe(node: object) -> str:
    """``tag[data-testid='…']#id.cls`` of a probe's element description."""
    if not isinstance(node, dict):
        return "<nothing>"
    text = str(node.get("tag") or "?")
    if node.get("testid"):
        text += f"[data-testid='{node['testid']}']"
    if node.get("id"):
        text += f"#{node['id']}"
    if node.get("cls"):
        text += " (class " + repr(str(node["cls"])) + ")"
    return text


def _box(rect: object) -> str:
    if not isinstance(rect, dict):
        return "<unknown>"
    try:
        return (
            f"x={float(rect['x']):.0f} y={float(rect['y']):.0f} "
            f"w={float(rect['width']):.0f} h={float(rect['height']):.0f}"
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return "<unknown>"


def refusal_message(event: dict[str, Any], helper: str) -> str:
    """The ``AssertionError`` text for a covered control: what covers what, where (#3157)."""
    viewport = event.get("viewport") if isinstance(event.get("viewport"), dict) else {}
    return (
        f"{helper}(): the native click on {_describe(event.get('target'))} "
        f"(locator {event.get('locator') or '<raw element>'}) was refused "
        f"({event.get('trigger')}) because {_describe(event.get('hit'))} lies on top of it "
        f"(relation {event.get('relation')}): a user's press at the control's centre "
        f"{event.get('point')} would reach that element, not the control. "
        f"Control box {_box(event.get('rect'))}, covering box {_box(event.get('hit_rect'))}, "
        f"viewport {viewport.get('width')}x{viewport.get('height')}. No click was sent. "
        f"Find out why it covers the control -- a snackbar to wait for or close, a menu "
        f"still open, a layout defect -- instead of clicking through it; a caller that "
        f"expects the covering passes covered_ok='<reason>' (#3157)."
    )


def drain() -> list[dict[str, Any]]:
    """Return and forget every event recorded since the last drain."""
    events = list(_pending)
    _pending.clear()
    return events
