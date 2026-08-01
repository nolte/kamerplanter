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

Usage:
    zap_gate.py REPORT.json [--profile baseline|api|full] [--rules FILE.tsv]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ZAP encodes both axes as 0..3 integers in the traditional JSON report.
RISK = {0: "Informational", 1: "Low", 2: "Medium", 3: "High"}
CONFIDENCE = {0: "False Positive", 1: "Low", 2: "Medium", 3: "High"}

BLOCKING_RISK = 3  # High
MIN_BLOCKING_CONFIDENCE = 2  # Medium

# `<PluginID>\t<THRESHOLD>\t<Confidence>\t<Note>` per NFR-015 §6.1. Every IGNORE
# row must carry an expiry in its note; see check_rules_file.
IGNORE_EXPIRY = re.compile(r"expires\s+(\d{4}-\d{2}-\d{2})")


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


def check_rules_file(path: Path) -> list[str]:
    """Return violations of the IGNORE-needs-an-unexpired-expiry rule (§6.1)."""
    if not path.exists():
        return []
    problems: list[str] = []
    today = date.today()
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 2 or parts[1].strip().upper() != "IGNORE":
            continue
        note = parts[3] if len(parts) > 3 else ""
        match = IGNORE_EXPIRY.search(note)
        if not match:
            problems.append(
                f"{path}:{lineno}: IGNORE for rule {parts[0].strip()} has no `expires YYYY-MM-DD` note"
            )
            continue
        expires = date.fromisoformat(match.group(1))
        if expires < today:
            problems.append(
                f"{path}:{lineno}: IGNORE for rule {parts[0].strip()} expired on {expires.isoformat()}"
            )
    return problems


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
        "--rules", type=Path, help="rule-tuning TSV whose IGNORE expiries to validate"
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

    rule_problems = check_rules_file(args.rules) if args.rules else []
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

    return 1 if (blocking or rule_problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
