#!/usr/bin/env python3
"""Refuse a chart version on the develop tree that a release could publish too.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_chart_develop_version.py
    python3 scripts/check_chart_develop_version.py --chart helm/kamerplanter/Chart.yaml
    python3 scripts/check_chart_develop_version.py --list   # name every site
    python3 scripts/check_chart_develop_version.py --json   # machine-readable

**The incident (#1222).** ``helm/kamerplanter/Chart.yaml`` carried
``version: 0.2.0`` on ``develop``, and ``0.2.0`` is a *published release*.
``docker-publish.yml``'s ``Update chart version for release`` step only rewrites
that value on a tag ref, so every ``helm/**`` merge to ``develop`` packaged the
committed version verbatim and pushed it. ``helm push`` derives the OCI tag from
the chart version, so the merge overwrote the tag the release had published.

Measured: an anonymous read of
``ghcr.io/v2/nolte/charts/kamerplanter/manifests/0.2.0`` returned
``org.opencontainers.image.created: 2026-08-18T14:09:14Z`` and layer digest
``sha256:d328e879db866ca8745302da2d210011ac664bc59357cbea079bb06a0997925e``,
while release ``v0.2.0`` was published ``2026-08-13T18:09:49Z``. The chart under
a published release's version reference was rebuilt from ``develop`` five days
later. ``spec/project/continuous-delivery/en.md:53`` forbids exactly that:
"republishing different content under an existing version reference is
prohibited".

The condition was not observable from inside the repository — you had to pull the
OCI tag and diff it. This checker makes it observable from the diff.

**What it enforces.** For every ``helm/*/Chart.yaml``, the ``version`` value

1. MUST parse as SemVer 2.0.0 (the strict grammar: no leading ``v``, no
   two-segment ``1.0``), and
2. MUST carry a pre-release whose **first dot-separated identifier is exactly**
   ``dev`` — ``0.3.0-dev``, ``0.3.0-dev.4`` pass; ``0.3.0``, ``0.3.0-rc1``,
   ``0.3.0-development``, ``0.3.0-DEV`` do not.

Identifier comparison is case-sensitive and exact, because SemVer pre-release
identifiers are, and because "starts with dev" would admit ``development`` — a
value a release could plausibly carry.

**Why not the obvious, stronger rule.** The rule one actually wants is *"the
chart version on a non-tag ref must never equal a version that has been published
as a release"*. That rule is not statically decidable, and every way of making it
decidable makes the guard inert exactly where it must not be:

* **A live API call** (``gh release list`` / the GHCR tags list) from a
  pre-commit hook makes the required ``static`` lane depend on network
  reachability. It either fails closed on every offline commit — and a gate that
  goes red for a reason unrelated to the diff gets bypassed — or fails open on
  every blip, which is not a gate at all.
* **Deriving the set from git tags in the checkout** is the decisive rejection.
  The ``static`` lane checks out with ``actions/checkout`` carrying no
  ``fetch-depth`` and no ``fetch-tags``, i.e. the shallow default with no tags,
  while a developer's checkout has all 26. A rule whose outcome depends on
  whether tags happened to be fetched is **green locally and inert in CI** — the
  failure class this repository has paid for repeatedly. Worse, a *draft* release
  has no git tag at all (``v0.2.1`` is a draft as this is written), so even a
  full fetch would permit a version that is about to become a release.
* **Hard-coding the published set** here means editing this file after every
  release, and a list nobody updates silently stops covering the newest release —
  precisely the version most likely to be collided with.

**Why the weaker rule is sufficient — and on what premise.** The committed value
is only ever published from a non-tag ref, because the release path overwrites it
unconditionally (``docker-publish.yml``'s ``yq -i ".version = …"``). A release
version reference is ``${REF_NAME#v}`` for a tag ``v<x>``. So *if no release tag
ever carries a ``dev`` pre-release*, a ``dev``-marked committed version can never
equal a published one.

That premise is an assumption, not a fact, and this checker cannot observe it —
it is enforced on the release side by ``scripts/ci/determine_chart_version.sh``
(work package P3 of #1222), which rejects a resolved release version whose
pre-release begins with ``dev``. **Without that script in place this guard proves
strictly less than it appears to**: it would still forbid every version published
so far, but nothing would stop a future ``v0.9.0-dev`` tag from making a
``dev``-marked develop value collide after all. Reserving the *first identifier*
rather than "any pre-release" is what keeps ``-rc1`` releases legal while making
that rejection narrow and exact.

**The escape hatch.** A chart may stand by carrying a justification on the
``version:`` line itself or in the comment block directly above it::

    # chart-develop-version-ok: vendored subchart, never published from this repo

The reason is mandatory and must be more than a word, so the hatch cannot be used
as a silencer. This mirrors ``scripts/check_workflow_gate_integrity.py``'s
``# gate-integrity-ok:`` and ``scripts/check_attest_registry_credentials.py``'s
``# attest-credentials-ok:`` deliberately: one convention, not three.

**Precision, and what is deliberately not checked.**

* Only ``helm/*/Chart.yaml`` — the charts this repository publishes. A
  ``charts/`` subdirectory holding fetched dependencies is not scanned; those
  versions are somebody else's and rewriting them would be wrong.
* ``appVersion`` is not checked. The release path overwrites it too, but it names
  the *application*, not the packaging artifact, and no OCI tag is derived from
  it.
* Nothing here reads the registry, the git tags, or the network. That is the
  whole design decision above, restated as a property of the file.
* A chart whose ``version`` key is absent or is not a scalar is a finding, not a
  pass: ``helm package`` would fail on it anyway, and reporting clean on an input
  that was never examined is the shape NFR-018 §2 forbids.

**Why not import the sibling checkers' helpers.** These gates run in the required
``static`` job on a bare runner, invoked one file at a time by pre-commit; they
are scripts, not a package, and ``scripts/`` is on no import path. The
justification helper is therefore duplicated rather than shared — twenty lines
against a cross-file import that only works by accident of the working directory.

Standard library plus PyYAML — the same isolated pre-commit environment the
gate-integrity and attest-credentials hooks use, because the required ``static``
job runs on a bare runner with none of the project's dependencies installed.

Traces to issue #1222 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the published charts live, relative to the repository root.
DEFAULT_HELM_ROOT = "helm"

#: One level deep only: ``helm/<chart>/Chart.yaml``. A nested ``charts/``
#: directory holds fetched dependencies, whose versions are not ours to set.
CHART_GLOB = "*/Chart.yaml"

#: The marker that exempts a chart, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption.
JUSTIFICATION_MARKER = "# chart-develop-version-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: The reserved first pre-release identifier of the develop channel. Compared
#: case-sensitively and in full: SemVer identifiers are case-sensitive, and a
#: prefix test would admit ``development``, which a release could carry.
DEVELOP_CHANNEL = "dev"

#: The official SemVer 2.0.0 grammar, verbatim from semver.org. Strict on
#: purpose: ``v0.2.0`` and ``1.0`` are the two spellings a hand edit produces,
#: and Helm's own parser is lenient enough to accept the first — which would let
#: a value through that this rule cannot reason about.
SEMVER = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

#: The top-level ``version:`` key of a Chart.yaml — column zero, because a
#: ``version:`` indented under ``dependencies:`` names a dependency's version and
#: anchoring the finding there would put the escape hatch on the wrong key.
VERSION_KEY = re.compile(r"^version:\s*(?P<value>.*?)\s*$")

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class ChartDevelopVersionCheckError(Exception):
    """A usage or environment problem — not a finding about the charts."""


@dataclass(frozen=True)
class Finding:
    """One chart carrying a version the develop channel must not carry."""

    path: Path
    line: int
    kind: str
    detail: str
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)


#: Human wording per finding kind, used in the report.
KIND_LABELS = {
    "chart_version_missing": "the chart declares no version",
    "chart_version_not_semver": "the chart version is not SemVer 2.0",
    "chart_version_releasable": "the develop tree carries a releasable chart version",
    "chart_version_wrong_channel": "the pre-release names a channel other than 'dev'",
}


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the site on *line*, or ``None``.

    Accepted on the site's own line (trailing comment) and anywhere in the
    contiguous comment block directly above it. The block form matters here: a
    ``Chart.yaml`` explains a version choice in the comment paragraph above the
    key, and a marker is most useful inside the paragraph that already argues the
    point.

    Args:
        lines: The file's lines, without terminators.
        line: 1-based line the finding is anchored to.

    Returns:
        The reason text when a marker with a long-enough reason is present.
    """
    candidates = [lines[line - 1]] if 0 < line <= len(lines) else []
    index = line - 2
    while index >= 0 and lines[index].strip().startswith("#"):
        candidates.append(lines[index].strip())
        index -= 1
    for candidate in candidates:
        marker = candidate.find(JUSTIFICATION_MARKER)
        if marker == -1:
            continue
        reason = candidate[marker + len(JUSTIFICATION_MARKER) :].strip()
        if len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def version_line(lines: list[str]) -> int:
    """The 1-based line of the top-level ``version:`` key, or 1 when absent.

    Falling back to line 1 rather than raising: a chart with no ``version`` key
    is itself a finding, and it still needs somewhere to anchor — the head of the
    file, which is where a reader would add the key.
    """
    for number, line in enumerate(lines, start=1):
        if VERSION_KEY.match(line):
            return number
    return 1


def _raw_version(document: Any) -> Any:
    """The ``version`` value of a parsed Chart.yaml, or ``None`` when absent."""
    if not isinstance(document, dict):
        return None
    return document.get("version")


def _as_version_text(raw: Any) -> str | None:
    """The ``version`` value as the text SemVer must parse, or ``None``.

    A YAML scalar that is not a string still has a spelling — ``version: 1.0``
    parses as the float ``1.0`` — and reporting that spelling is more useful than
    reporting its Python type. Mappings and sequences have no spelling worth
    quoting, so they read as absent-and-malformed.
    """
    if raw is None or isinstance(raw, (dict, list)):
        return None
    if isinstance(raw, bool):
        return str(raw).lower()
    return str(raw).strip()


def _suggestion(match: re.Match[str] | None) -> str:
    """A concrete replacement to put in the message, given a parsed version.

    The next *minor* rather than the same version with ``-dev`` appended:
    ``0.2.0-dev`` sorts *below* the published ``0.2.0``, which is legal here but
    makes "newest" listings read wrong. Purely advisory — every ``dev``-marked
    SemVer value satisfies the rule, and no periodic bump is required, because a
    stale ``0.3.0-dev`` after ``v0.3.0`` ships still cannot collide.
    """
    if match is None:
        return "0.3.0-dev"
    return f"{match.group('major')}.{int(match.group('minor')) + 1}.0-dev"


def evaluate(text: str | None) -> tuple[str, str] | None:
    """Judge one ``version`` value; return ``(kind, detail)`` or ``None`` if fine.

    Args:
        text: The version as spelled in the file, or ``None`` when the key is
            absent or holds a collection.

    Returns:
        The finding kind and its explanation, or ``None`` when the value parses
        as SemVer 2.0 and carries the ``dev`` channel identifier.
    """
    if text is None or not text:
        return (
            "chart_version_missing",
            (
                "the chart declares no top-level `version` — `helm package` cannot run on it, "
                f"and the develop tree must carry a SemVer 2.0 version with a '{DEVELOP_CHANNEL}' "
                f"pre-release (for example {_suggestion(None)})"
            ),
        )

    match = SEMVER.match(text)
    if match is None:
        return (
            "chart_version_not_semver",
            (
                f"version {text} does not parse as SemVer 2.0 — the develop tree must carry a "
                f"SemVer 2.0 version whose first pre-release identifier is '{DEVELOP_CHANNEL}' "
                f"(for example {_suggestion(None)})"
            ),
        )

    prerelease = match.group("prerelease")
    if prerelease is None:
        return (
            "chart_version_releasable",
            (
                f"version {text} carries no pre-release, so it is a releasable version: a push to a "
                f"non-tag ref packages it verbatim and `helm push` overwrites the OCI chart tag "
                f"{text} — the #1222 incident. The develop tree must carry a "
                f"'{DEVELOP_CHANNEL}' pre-release (for example {_suggestion(match)})"
            ),
        )

    first = prerelease.split(".")[0]
    if first != DEVELOP_CHANNEL:
        return (
            "chart_version_wrong_channel",
            (
                f"version {text} carries the pre-release '{prerelease}', whose first identifier is "
                f"'{first}' and not '{DEVELOP_CHANNEL}' — that is a release channel (an -rc tag is a "
                f"release), so it may collide with a published version. The develop tree must carry a "
                f"'{DEVELOP_CHANNEL}' pre-release (for example {_suggestion(match)})"
            ),
        )
    return None


def scan_file(path: Path) -> list[Finding]:
    """Every finding in one ``Chart.yaml``."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ChartDevelopVersionCheckError(f"cannot read {path}: {exc}") from exc
    lines = source.splitlines()
    try:
        document = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise ChartDevelopVersionCheckError(f"cannot parse {path}: {exc}") from exc

    verdict = evaluate(_as_version_text(_raw_version(document)))
    if verdict is None:
        return []
    kind, detail = verdict
    line = version_line(lines)
    return [
        Finding(
            path=path,
            line=line,
            kind=kind,
            detail=detail,
            justification=justification_for(lines, line),
        )
    ]


def discover(helm_root: Path) -> list[Path]:
    """Every publishable ``Chart.yaml`` below *helm_root*.

    Raises:
        ChartDevelopVersionCheckError: when the root is absent or holds no chart.
            Scanning nothing and reporting clean is the shape NFR-018 §2 forbids,
            so it is an error rather than a pass — and it is the failure mode a
            renamed directory would otherwise produce silently.
    """
    if not helm_root.exists():
        raise ChartDevelopVersionCheckError(f"helm root does not exist: {helm_root}")
    charts = sorted(helm_root.glob(CHART_GLOB))
    if not charts:
        raise ChartDevelopVersionCheckError(f"no {CHART_GLOB} under {helm_root}")
    return charts


def collect(charts: list[Path]) -> list[Finding]:
    """Every finding across *charts*, justified or not.

    Raises:
        ChartDevelopVersionCheckError: when a named chart does not exist. An
            explicit ``--chart`` that silently scans nothing is worse than a
            usage error, because the caller believes it was checked.
    """
    findings: list[Finding] = []
    for path in charts:
        if not path.is_file():
            raise ChartDevelopVersionCheckError(f"chart file does not exist: {path}")
        findings.extend(scan_file(path))
    return sorted(findings, key=lambda finding: (finding.relative(), finding.line))


def report(findings: list[Finding], *, scanned: int, list_all: bool, as_json: bool) -> int:
    """Print the outcome and return the process exit code."""
    unjustified = [finding for finding in findings if not finding.justified]
    justified = [finding for finding in findings if finding.justified]

    if as_json:
        print(
            json.dumps(
                {
                    "charts": scanned,
                    "sites": len(findings),
                    "justified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                            "reason": finding.justification,
                        }
                        for finding in justified
                    ],
                    "unjustified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                        }
                        for finding in unjustified
                    ],
                },
                indent=2,
            )
        )
        return EXIT_DEFECTS if unjustified else EXIT_OK

    if unjustified:
        print(f"check_chart_develop_version: {len(unjustified)} chart(s) not on the develop channel\n")
        for finding in unjustified:
            print(f"  {finding.relative()}:{finding.line}: {KIND_LABELS[finding.kind]}")
            print(f"      {finding.detail}")
        print(
            "\n`helm push` derives the OCI tag from the chart version, and\n"
            "docker-publish.yml only rewrites that version on a tag ref. So whatever is\n"
            "committed here is what every `helm/**` merge to develop publishes — and on\n"
            "2026-08-18 that republished charts/kamerplanter:0.2.0, five days after release\n"
            "v0.2.0 had published it (issue #1222). spec/project/continuous-delivery/en.md\n"
            "prohibits republishing different content under an existing version reference.\n"
            "\n"
            "Give the develop tree a channel a release tag can never name:\n"
            "\n"
            "    version: 0.3.0-dev\n"
            "\n"
            "The release path overwrites it from the tag, so this value is never what a\n"
            "release publishes. Its counterpart on the release side is\n"
            "scripts/ci/determine_chart_version.sh, which refuses a release tag carrying a\n"
            f"'{DEVELOP_CHANNEL}' pre-release.\n"
            "\n"
            "…or say — on the `version:` line, or in the comment block directly above it —\n"
            "why this chart is not published from develop:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <why this version cannot collide with a release>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    print(
        f"check_chart_develop_version: OK — {scanned} chart(s) on the develop channel "
        f"({len(justified)} justified site(s))."
    )
    if list_all:
        for finding in justified:
            print(f"  {finding.relative()}:{finding.line} [{finding.kind}]: {finding.justification}")
    return EXIT_OK


def _resolve(raw: str) -> Path:
    """A CLI path, taken as given when absolute and against the repo root when not."""
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every scanned chart carries a ``dev``-channel SemVer version (or a
        reason), 1 when at least one does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_chart_develop_version.py",
        description=(
            "Refuse a helm/*/Chart.yaml whose `version` is a releasable SemVer value "
            "instead of a develop-channel pre-release (issue #1222). A chart may stand by "
            f"carrying a '{JUSTIFICATION_MARKER} <reason>' comment."
        ),
    )
    parser.add_argument(
        "--chart",
        metavar="PATH",
        action="append",
        default=None,
        help="check this Chart.yaml instead of the default scan (repeatable)",
    )
    parser.add_argument(
        "--helm-root",
        metavar="PATH",
        default=None,
        help=f"the chart directory to scan for {CHART_GLOB} (default: {DEFAULT_HELM_ROOT})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every justified chart when the check passes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    if args.chart and args.helm_root:
        parser.error("--chart and --helm-root are mutually exclusive")

    try:
        charts = (
            [_resolve(raw) for raw in args.chart]
            if args.chart
            else discover(_resolve(args.helm_root or DEFAULT_HELM_ROOT))
        )
        findings = collect(charts)
    except ChartDevelopVersionCheckError as exc:
        print(f"check_chart_develop_version: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(findings, scanned=len(charts), list_all=args.list_all, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
