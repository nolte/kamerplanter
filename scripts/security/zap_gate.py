#!/usr/bin/env python3
"""Apply the NFR-015 severity policy to a ZAP JSON report.

ZAP's own exit codes are too coarse for the policy NFR-015 §5.1/§5.2 declares.
``zap-baseline.py`` exits 1 when any rule is at FAIL and 2 when any is at WARN,
with no notion of confidence and no way to say "High blocks, Medium warns". Using
those exit codes directly would force a choice between failing on everything —
which makes the gate a nuisance that gets disabled — and failing on nothing,
which is the vacuous-gate shape NFR-018 §1 catalogues.

So ZAP runs with ``-I`` (do not fail on warnings) and this script owns the
verdict:

  §5.1  High -> fail. Medium -> warn. Low / Informational -> report only.
  §5.2  Only findings with confidence >= Medium can fail the build. A Low or
        False-Positive confidence finding is a warning regardless of risk.

It refuses to treat an unreadable or structurally unexpected report as clean: a
report it cannot parse is a failed scan, not a passed one.

**Suppression is applied HERE, not by ZAP.** `zap-api-scan.py` decides its active
scan policy from whether a `-c` config file produced any entries at all::

    scan_policy = 'API-Minimal'
    if config_dict:
        scan_policy = 'Default Policy'
        zap.ascan.enable_all_scanners(scanpolicyname=scan_policy)

So the first suppression handed to that script swaps a 23-rule minimal policy for
the full active rule set — an unrelated, unbounded widening of the scan — and the
only shape it can express is "turn this rule off everywhere". Neither is what a
single measured false positive warrants. The rule files are therefore consumed by
this script alone (`--rules`), which drops matching INSTANCES by URL and leaves the
scanner's policy untouched. See `tests/security/zap-rules.tsv` for the format.

Usage:
    zap_gate.py REPORT.json [--profile baseline|api|full] [--rules FILE.tsv]
                [--emit-blocking OUT.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

# ZAP encodes both axes as 0..3 integers in the traditional JSON report.
RISK = {0: "Informational", 1: "Low", 2: "Medium", 3: "High"}
CONFIDENCE = {0: "False Positive", 1: "Low", 2: "Medium", 3: "High"}

BLOCKING_RISK = 3  # High
MIN_BLOCKING_CONFIDENCE = 2  # Medium

# `<PluginID>\t<THRESHOLD>\t<Confidence>\t<Note>` per NFR-015 §6.1. Every IGNORE
# row must carry an expiry AND a `scope=` URL regex in its note; see load_rules.
IGNORE_EXPIRY = re.compile(r"expires\s+(\d{4}-\d{2}-\d{2})")
IGNORE_SCOPE = re.compile(r"scope=(\S+)")

# The grace `tests/security/zap-rules.tsv` promises between an expiry and a red
# build: past the date is a warning the reviewer sees, past the grace is a
# failure. `src/backend/tests/unit/guards/test_zap_rule_suppressions.py` asserts the
# same number, so the two enforcement points cannot drift into disagreeing about
# when a suppression has lapsed.
GRACE_DAYS = 30


@dataclass(frozen=True)
class Suppression:
    """One IGNORE row, already validated. Applies to instances, not to rules."""

    plugin_id: str
    scope: re.Pattern[str]
    expires: date
    source: str

    def covers(self, plugin_id: str, uri: str) -> bool:
        return plugin_id == self.plugin_id and bool(self.scope.search(uri))


def load_report(path: Path) -> list[dict[str, Any]]:
    """Return every alert in the report, failing loudly on anything unexpected."""
    if not path.exists():
        print(
            f"::error::ZAP report {path} does not exist — the scan did not produce one.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error::ZAP report {path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    sites = data.get("site")
    if not isinstance(sites, list):
        print(
            f"::error::ZAP report {path} has no `site` array. The report format "
            f"changed or the scan aborted; refusing to read that as 'no findings'.",
            file=sys.stderr,
        )
        sys.exit(2)

    alerts: list[dict[str, Any]] = []
    for site in sites:
        for alert in site.get("alerts", []):
            alert = dict(alert)
            alert["_site"] = site.get("@name", "?")
            alerts.append(alert)
    return alerts


def load_rules(
    path: Path, today: date | None = None
) -> tuple[list[Suppression], list[str], list[str]]:
    """Parse the rule file into ``(suppressions, problems, warnings)``.

    A row this function cannot fully validate is reported AND not applied. That
    ordering is the point: a malformed suppression must never fall back to
    suppressing more than it says, and it must never go quietly inert either.

    Expiry follows the grace the file's own header promises — expired is a
    warning, expired by more than ``GRACE_DAYS`` is a problem and the row stops
    applying, so the finding it was hiding reappears in the same run that fails.
    """
    if not path.exists():
        return [], [], []

    today = today or date.today()
    suppressions: list[Suppression] = []
    problems: list[str] = []
    warnings: list[str] = []

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        where = f"{path}:{lineno}"

        # No `continue` without a message. A row split by spaces instead of tabs
        # arrives here as a single field and used to be skipped in silence, so the
        # suppression simply did not apply and nobody was told — the failure mode
        # this whole file exists to prevent, reached through the parser.
        if len(parts) != 4:
            problems.append(
                f"{where}: expected 4 tab-separated fields "
                f"(<PluginID>\\t<THRESHOLD>\\t<Confidence>\\t<Note>), found {len(parts)}. "
                f"Spaces instead of tabs look identical in a diff and parse to one field."
            )
            continue

        plugin_id = parts[0].strip()
        threshold = parts[1].strip().upper()
        note = parts[3]

        if threshold != "IGNORE":
            # WARN / FAIL / INFO / PASS are ZAP's vocabulary, and ZAP no longer
            # reads these files (see the module docstring). Accepting such a row
            # would mean accepting a threshold override that changes nothing —
            # someone following NFR-015 §6.1's own example would expect a rule to
            # start blocking and get silence.
            problems.append(
                f"{where}: threshold {threshold!r} is not honoured. This gate implements "
                f"IGNORE only; a WARN/FAIL/INFO/PASS row would be inert because the files "
                f"are no longer passed to ZAP. Express the severity policy in zap_gate.py."
            )
            continue

        expiry_match = IGNORE_EXPIRY.search(note)
        if not expiry_match:
            problems.append(
                f"{where}: IGNORE for rule {plugin_id} has no `expires YYYY-MM-DD` note"
            )
            continue

        scope_match = IGNORE_SCOPE.search(note)
        if not scope_match:
            problems.append(
                f"{where}: IGNORE for rule {plugin_id} has no `scope=<url regex>` in its "
                f"note. A suppression with no scope would silence the rule across the "
                f"whole target; say so explicitly with `scope=.*` if that is the intent."
            )
            continue
        try:
            scope = re.compile(scope_match.group(1))
        except re.error as exc:
            problems.append(
                f"{where}: IGNORE for rule {plugin_id} has an unusable "
                f"`scope={scope_match.group(1)}`: {exc}"
            )
            continue

        try:
            expires = date.fromisoformat(expiry_match.group(1))
        except ValueError as exc:
            # `IGNORE_EXPIRY` matches the SHAPE. `2026-02-30` has the shape and no
            # day; unguarded, that ends the process before a single alert is read,
            # and — since --emit-blocking writes at the end — leaves no verdict
            # file, which the issue-opening step cannot distinguish from a profile
            # that simply had nothing to report.
            problems.append(
                f"{where}: IGNORE for rule {plugin_id} has an impossible expiry "
                f"{expiry_match.group(1)!r}: {exc}"
            )
            continue
        overdue = (today - expires).days
        if overdue > GRACE_DAYS:
            problems.append(
                f"{where}: IGNORE for rule {plugin_id} expired on {expires.isoformat()}, "
                f"{overdue} days ago — past the {GRACE_DAYS}-day grace. It no longer "
                f"applies; re-verify the finding and renew or remove the row."
            )
            continue
        if overdue > 0:
            warnings.append(
                f"{where}: IGNORE for rule {plugin_id} expired on {expires.isoformat()} "
                f"and fails the build in {GRACE_DAYS - overdue + 1} day(s)."
            )

        suppressions.append(
            Suppression(plugin_id=plugin_id, scope=scope, expires=expires, source=where)
        )

    return suppressions, problems, warnings


def apply_suppressions(
    alerts: list[dict[str, Any]], suppressions: list[Suppression]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Drop suppressed INSTANCES; return the surviving alerts and what happened.

    Instance-level, not alert-level: one ZAP alert carries every URL the rule
    fired on, so dropping the alert would hide a genuine injection elsewhere
    behind the one endpoint that was measured false. An alert keeps blocking
    while any unsuppressed instance remains.

    A suppression that matched nothing is reported. That is the stale-suppression
    signal — the row outlived the finding and nobody noticed.
    """
    if not suppressions:
        return alerts, []

    notes: list[str] = []
    hits: dict[str, int] = {s.source: 0 for s in suppressions}
    survivors: list[dict[str, Any]] = []

    for alert in alerts:
        plugin_id = str(alert.get("pluginid", ""))
        instances = alert.get("instances", [])
        kept = []
        for inst in instances:
            uri = str(inst.get("uri", ""))
            # EVERY covering row is credited, not just the first match. With a
            # narrow scope and a broader one over the same endpoint, crediting only
            # the first made the second report "matched no finding … remove the
            # row" — the designed signal to delete a suppression, pointed at one
            # that was doing its job.
            covering = [s for s in suppressions if s.covers(plugin_id, uri)]
            if not covering:
                kept.append(inst)
                continue
            for suppression in covering:
                hits[suppression.source] += 1
        if instances and not kept:
            notes.append(
                f"suppressed: [{RISK.get(alert.get('riskcode_int', -1), '?')}] "
                f"{alert.get('alert', '?')} (plugin {plugin_id}, "
                f"{len(instances)} instance(s)) on {alert['_site']}"
            )
            continue
        if len(kept) != len(instances):
            notes.append(
                f"partially suppressed: {alert.get('alert', '?')} (plugin {plugin_id}) — "
                f"{len(instances) - len(kept)} of {len(instances)} instance(s) dropped, "
                f"{len(kept)} still counted"
            )
        alert = dict(alert)
        alert["instances"] = kept
        survivors.append(alert)

    for suppression in suppressions:
        if hits[suppression.source] == 0:
            notes.append(
                f"{suppression.source}: suppression for rule {suppression.plugin_id} "
                f"matched no finding in this report. Either the finding is gone — remove "
                f"the row — or its scope no longer matches what ZAP reports."
            )

    return survivors, notes


def describe(alert: dict[str, Any]) -> str:
    risk = RISK.get(alert.get("riskcode_int", -1), "?")
    conf = CONFIDENCE.get(alert.get("confidence_int", -1), "?")
    count = len(alert.get("instances", []))
    return (
        f"[{risk}/{conf}] {alert.get('alert', '?')} "
        f"(plugin {alert.get('pluginid', '?')}, {count} instance(s)) on {alert['_site']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--profile", default="baseline")
    parser.add_argument(
        "--rules",
        type=Path,
        help="rule-tuning TSV: validated, and its IGNORE rows applied to the report",
    )
    parser.add_argument(
        "--emit-blocking",
        type=Path,
        help=(
            "write the post-suppression blocking findings here as JSON. The "
            "issue-opening step reads this instead of re-deriving the verdict from "
            "the raw report, so there is one owner of what 'blocking' means."
        ),
    )
    args = parser.parse_args()

    alerts = load_report(args.report)

    # `riskcode` and `confidence` are strings in the JSON report; normalise once
    # so every later comparison is numeric rather than lexicographic ("10" < "3").
    for alert in alerts:
        for src, dst in (
            ("riskcode", "riskcode_int"),
            ("confidence", "confidence_int"),
        ):
            try:
                alert[dst] = int(alert.get(src, -1))
            except (TypeError, ValueError):
                alert[dst] = -1

    suppressions, rule_problems, rule_warnings = (
        load_rules(args.rules) if args.rules else ([], [], [])
    )
    alerts, suppression_notes = apply_suppressions(alerts, suppressions)

    def is_blocking(a: dict[str, Any]) -> bool:
        return (
            a["riskcode_int"] >= BLOCKING_RISK
            and a["confidence_int"] >= MIN_BLOCKING_CONFIDENCE
        )

    blocking = [a for a in alerts if is_blocking(a)]
    # Medium risk, plus High risk that the §5.2 confidence filter spares. Derived
    # from the same predicate rather than by `not in blocking`, which compares
    # dicts by value and would mis-bucket two genuinely identical alerts.
    warnings = [a for a in alerts if not is_blocking(a) and a["riskcode_int"] >= 2]
    low = [a for a in alerts if a["riskcode_int"] < 2]

    print(
        f"ZAP {args.profile} scan — {len(alerts)} alert(s): "
        f"{len(blocking)} blocking, {len(warnings)} warning, {len(low)} low/informational."
    )

    for a in warnings:
        print(f"::warning::{describe(a)}")
    for a in low:
        print(f"  {describe(a)}")
    for note in suppression_notes:
        print(f"::warning::{note}")
    for warning in rule_warnings:
        print(f"::warning::{warning}")
    for problem in rule_problems:
        print(f"::error::{problem}", file=sys.stderr)

    if blocking:
        print(
            "::error::ZAP findings at High risk with at least Medium confidence (NFR-015 §5.1):",
            file=sys.stderr,
        )
        for a in blocking:
            print(f"  {describe(a)}", file=sys.stderr)
            for inst in a.get("instances", [])[:5]:
                print(
                    f"      {inst.get('method', '?')} {inst.get('uri', '?')}",
                    file=sys.stderr,
                )

    if args.emit_blocking:
        # Written unconditionally, including the empty case: the consumer has to
        # be able to tell "the gate ran and found nothing" from "the gate never
        # ran", and a missing file is the only honest spelling of the latter.
        args.emit_blocking.write_text(
            json.dumps(
                [
                    {
                        "profile": args.profile,
                        "plugin": a.get("pluginid", "?"),
                        "name": a.get("alert", "?"),
                        "site": a["_site"],
                        "count": len(a.get("instances", [])),
                        "instances": [
                            {
                                "method": inst.get("method", "?"),
                                "uri": inst.get("uri", "?"),
                            }
                            for inst in a.get("instances", [])[:5]
                        ],
                    }
                    for a in blocking
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

    return 1 if (blocking or rule_problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
