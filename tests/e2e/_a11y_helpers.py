"""axe-core against the composed, running app (#1095).

Component-level `vitest-axe` cannot see what only exists once the page is
assembled: landmark structure, heading order, and contrast between a component's
colour and the background some ancestor painted. This runs the same engine
against the real page in a real browser.

WHY THE BUNDLE IS INJECTED RATHER THAN LOADED BY THE PAGE
--------------------------------------------------------
The app must not ship an accessibility scanner. The bundle lives in the E2E
image (``/app/vendor/axe.min.js``, put there by the Dockerfile's ``axe`` stage)
and is pushed into the page per check with ``execute_script``. Nothing about the
application changes to be measurable.

FAIL LOUD, BECAUSE A SILENT SCANNER IS WORSE THAN NONE
------------------------------------------------------
Every failure to *run* raises. A journey that quietly skipped its axe pass —
bundle missing, injection blocked by CSP, ``axe.run`` throwing — would report
green and mean nothing, which is the shape a guard must never take (NFR-018 §2).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: Where the Dockerfile's `axe` stage puts the bundle. A path rather than a
#: `node_modules` lookup: this image has no node tree to search.
AXE_BUNDLE = Path("/app/vendor/axe.min.js")

#: Local fallback so the helper is runnable outside the container during
#: development. Never used in CI, where the image path exists.
_LOCAL_BUNDLE = Path(__file__).parent / "node_modules" / "axe-core" / "axe.min.js"

#: WCAG 2.2 AA plus best practices, matching UI-NFR-002's target. Stated
#: explicitly rather than left to axe's default, so a future axe release cannot
#: widen or narrow what this journey asserts without the change being visible
#: in the diff.
DEFAULT_TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")

#: Budget for one `axe.run`. Generous, because the cost of being too tight is a
#: flaky journey and the cost of being loose is a slower failure.
AXE_RUN_TIMEOUT_SECONDS = 60


class AxeUnavailableError(RuntimeError):
    """The scan could not be performed — never a clean result."""


def _bundle_source() -> str:
    for candidate in (AXE_BUNDLE, _LOCAL_BUNDLE):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise AxeUnavailableError(
        f"axe-core bundle not found at {AXE_BUNDLE} or {_LOCAL_BUNDLE}. "
        "In CI it is copied in by the Dockerfile's `axe` stage; locally run "
        "`npm ci` in tests/e2e/. Refusing to report a clean page that was never scanned."
    )


def run_axe(driver: Any, *, tags: tuple[str, ...] = DEFAULT_TAGS) -> list[dict]:
    """Scan the page currently open in ``driver`` and return its violations.

    Args:
        driver: A Selenium WebDriver on the page to scan.
        tags: axe rule tags to run. Defaults to :data:`DEFAULT_TAGS`.

    Returns:
        The raw ``violations`` array, most severe first as axe orders it.

    Raises:
        AxeUnavailableError: The bundle is missing, injection failed, or
            ``axe.run`` did not return a result. Never returns ``[]`` for any
            of those.
    """
    driver.execute_script(_bundle_source())

    # `window.axe` present is the injection's own post-condition. Asserting it
    # separately turns "the script silently did nothing" — a CSP refusal looks
    # exactly like that — into a named failure instead of an empty violation list.
    if not driver.execute_script("return typeof window.axe !== 'undefined';"):
        raise AxeUnavailableError(
            "axe-core did not define window.axe after injection. A Content-Security-Policy "
            "that blocks inline script produces exactly this, and it must not read as a clean page."
        )

    # Stated rather than inherited: `axe.run` on a composed page takes seconds,
    # and the binding default is not something this suite should depend on. A
    # timeout raises `TimeoutException`, which is the right outcome — a scan that
    # ran out of time must not return an empty violation list.
    driver.set_script_timeout(AXE_RUN_TIMEOUT_SECONDS)
    result = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        axe.run(document, {runOnly: {type: 'tag', values: arguments[0]}})
           .then(r => done({ok: true, violations: r.violations}))
           .catch(e => done({ok: false, error: String(e)}));
        """,
        list(tags),
    )
    if not result or not result.get("ok"):
        raise AxeUnavailableError(
            f"axe.run failed: {(result or {}).get('error', 'no result returned')}"
        )
    return result["violations"]


def format_violations(violations: list[dict]) -> str:
    """Render violations so a failure message names the element, not just the rule.

    A report saying "color-contrast: 3 nodes" sends the reader hunting. The
    selector and the failure summary are what make it actionable.
    """
    if not violations:
        return "no violations"
    lines = []
    for violation in violations:
        nodes = violation.get("nodes", [])
        lines.append(
            f"- [{violation.get('impact', 'unknown')}] {violation.get('id')}: "
            f"{violation.get('help')} ({len(nodes)} node(s))"
        )
        for node in nodes[:3]:
            target = ", ".join(node.get("target", []))
            summary = (node.get("failureSummary") or "").replace("\n", " ")
            lines.append(f"    {target} — {summary[:160]}")
        if len(nodes) > 3:
            lines.append(f"    … and {len(nodes) - 3} more node(s)")
    return "\n".join(lines)


def seed_contrast_violation(driver: Any) -> None:
    """Inject a guaranteed WCAG failure — the negative control for the journey.

    A scan that has never been shown to fail is indistinguishable from one that
    cannot. This paints light-grey text on white at a ratio far below 4.5:1,
    which `color-contrast` (wcag2aa) reports, and it is removed by the next
    navigation because nothing persists it.
    """
    driver.execute_script(
        """
        const el = document.createElement('p');
        el.id = 'a11y-negative-control';
        el.textContent = 'seeded contrast violation';
        el.style.color = '#f4f4f4';
        el.style.backgroundColor = '#ffffff';
        el.style.fontSize = '12px';
        document.body.appendChild(el);
        """
    )


def violations_json(violations: list[dict]) -> str:
    """Compact JSON for the protocol artifact, without axe's full node payload."""
    return json.dumps(
        [
            {
                "id": v.get("id"),
                "impact": v.get("impact"),
                "help": v.get("help"),
                "targets": [t for n in v.get("nodes", []) for t in n.get("target", [])],
            }
            for v in violations
        ],
        ensure_ascii=False,
    )
