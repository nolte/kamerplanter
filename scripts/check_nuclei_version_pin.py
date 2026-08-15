#!/usr/bin/env python3
"""Refuse an unpinned Nuclei binary in any security lane (#1177).

**What went wrong.** ``projectdiscovery/nuclei-action`` defaults to
``version: latest`` and every lane was left at that default. The consequence was
not the one #1177 assumed — the validator and the scanners were never on
*different* versions, they were all on whatever "latest" meant that morning. The
consequence is that the gate's meaning changed with no commit in this repository:

* 2026-08-01, nuclei **v3.11.0** — validated 6 templates, green;
* 2026-08-15, nuclei **v3.11.1** — the same ``kamerplanter-jwt-leak.yaml``
  matcher fails to compile.

That template carried a negative lookahead from #122 onward. Go's ``regexp`` is
RE2 and has never supported lookaheads, so a *critical*-severity check could never
run — and the gate built to catch exactly that called it fine for two weeks,
because ``-validate`` did not compile matchers until v3.11.1 did.

**What this guard enforces.** Every ``nuclei-action`` step passes an explicit
``version:``, and every such value resolves to the single pin in
``.github/renovate-pins.yaml``. Two properties, and the second matters as much as
the first: a lane pinned to its *own* literal would satisfy "not latest" while
reintroducing the validator-vs-scanner drift the issue was filed about.

The pin is not a freeze. Renovate tracks ``nuclei_version`` and opens a pull
request on each release; that pull request is where the new binary meets the whole
template set and a human reads the result — which is the review "latest" silently
skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _REPO_ROOT / ".github" / "workflows"
_PINS = _REPO_ROOT / ".github" / "renovate-pins.yaml"

#: The action whose ``version:`` input decides which binary a lane installs.
_ACTION = "projectdiscovery/nuclei-action"

#: The one sanctioned way to spell the version: a reference to the step that read
#: the pin. A literal would pin *a* version without keeping the lanes together.
_EXPECTED_VALUE = re.compile(r"\$\{\{\s*steps\.nuclei_pin\.outputs\.version\s*\}\}")

_PIN_KEY = re.compile(r"^nuclei_version:\s*(\S+)\s*$", re.MULTILINE)


def _pinned_version(text: str) -> str | None:
    match = _PIN_KEY.search(text)
    return match.group(1) if match else None


def _action_steps(text: str) -> list[tuple[int, str]]:
    """Every ``nuclei-action`` usage as ``(line number, the step's block)``.

    The block runs to the next line at the same or lower indentation that starts
    a new list item, which is enough to contain a step's ``with:`` mapping.
    """
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if _ACTION not in line:
            continue
        indent = len(line) - len(line.lstrip())
        block = [line]
        for follower in lines[index + 1 :]:
            stripped = follower.lstrip()
            if stripped.startswith("- ") and (len(follower) - len(stripped)) <= indent:
                break
            if stripped and (len(follower) - len(stripped)) < indent and not stripped.startswith("-"):
                break
            block.append(follower)
        found.append((index + 1, "\n".join(block)))
    return found


def check() -> list[str]:
    """Return a problem per offending site; empty means the invariant holds."""
    problems: list[str] = []

    if not _PINS.is_file():
        return [f"{_PINS} is missing — nothing pins the Nuclei binary."]
    pinned = _pinned_version(_PINS.read_text(encoding="utf-8"))
    if not pinned:
        problems.append(
            f"{_PINS.relative_to(_REPO_ROOT)}: no `nuclei_version:` key. Every lane "
            "would fall back to `latest`, and the gate's meaning would change "
            "again without a commit (#1177)."
        )

    if not _WORKFLOW_DIR.is_dir():
        return [*problems, f"{_WORKFLOW_DIR} is missing — this guard cannot run."]

    sites = 0
    for workflow in sorted(_WORKFLOW_DIR.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for line_no, block in _action_steps(text):
            sites += 1
            where = f"{workflow.relative_to(_REPO_ROOT)}:{line_no}"
            if "version:" not in block:
                problems.append(
                    f"{where}: uses {_ACTION} without a `version:` input, so it installs "
                    "`latest`. Pass `version: ${{ steps.nuclei_pin.outputs.version }}` and "
                    "add the resolving step (#1177)."
                )
            elif not _EXPECTED_VALUE.search(block):
                problems.append(
                    f"{where}: uses {_ACTION} with a `version:` that is not the shared pin. "
                    "A per-lane literal keeps this off `latest` but lets the validator and "
                    "the scanners drift onto different binaries — the drift #1177 was filed "
                    "about. Use `${{ steps.nuclei_pin.outputs.version }}`."
                )

    if sites == 0:
        # Loud, not silent. A guard that finds nothing to check and reports
        # success is the shape NFR-018 §2 forbids and the shape this whole issue
        # is an instance of.
        problems.append(
            f"No {_ACTION} usage found under {_WORKFLOW_DIR.relative_to(_REPO_ROOT)}. Either the "
            "security lanes were removed — in which case this guard should go with them — or "
            "the action was renamed and this check has been passing on nothing."
        )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filenames", nargs="*", help="ignored; the check is repo-wide")
    parser.parse_args(argv)

    problems = check()
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if problems:
        print(
            "\nThe Nuclei binary must be pinned in .github/renovate-pins.yaml and read by "
            "every lane through the `nuclei_pin` step. See this file's docstring for what "
            "`latest` cost.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
