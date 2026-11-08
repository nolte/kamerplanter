#!/usr/bin/env python3
"""Report of the renderer measurement D-01 (REQ-053 WP 9.6, GP-NFR-033/034) from what the E2E run recorded.

``test_req053_renderer_profile.py`` writes one record per case and profile, twice: as the JUnit property
``renderer_record`` (a JSON string) and as a sidecar file ``renderer-profile-<case>-<profile>.json`` (next to the
screenshots, or in ``E2E_RENDERER_REPORT_DIR``). This script reads either - JUnit XML files, JSON files or
directories searched for both (``junit*.xml``, ``renderer-profile-*.json``) - and writes the Markdown report
with the p95 frame time per case and the Go/No-Go for WP 9.7::

    python3 tests/e2e/_renderer_report.py test-reports/e2e
    python3 tests/e2e/_renderer_report.py test-reports/e2e/junit-default.xml --date 2026-11-09
    python3 tests/e2e/_renderer_report.py test-reports/e2e --output - --allow-empty   # to stdout (CI summary)

Default output: ``.audits/req-053/renderer-measurement-<date>.md`` in the repository.

THE DECISION (D-01)
-------------------
D-01 makes the Konva renderer (WP 9.7) due when the measurement crosses GP-NFR-013's threshold: **more than 3 000
visible objects, or a frame time over 16 ms while dragging**. Read here as:

* the object count is judged on the **large** class only - the synthetic plan is built *at* 3 000 visible objects
  to measure the frame time there; its count is its premise, not a finding;
* the frame time is the drag's p95 against 16 ms on **every** profile, with the probe's refresh tolerance
  (``_inp_probe.VSYNC_TOLERANCE``: an idle 60 Hz page already reads 16.7 ms per frame);
* a measured violation is a Go even when another record is missing; without one, a missing record or an
  unavailable CPU throttle leaves the decision **open** instead of reading as No-Go.

The placeholder assumption (3) of #2759 narrows the Go to a violation on the **mobile** profile (CPU 4x); the
report shows that reading next to the literal one. Which one counts is the operator's call (question 3).

Standard library only: it runs on a bare CI runner after the suite, without the E2E extras.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

RECORD_PROPERTY = "renderer_record"
RECORD_FILE_PREFIX = "renderer-profile-"
RECORD_SCHEMA = 1

CASES = ("large", "synthetic_3000")
PROFILES = ("desktop", "mobile")
CASE_TITLES = {
    "large": "Klasse „large“ (250 Beete × 20 Pflanzen)",
    "synthetic_3000": "Synthetisch, 3 000 sichtbare Objekte (30 Beete × 100 Pflanzen)",
}
PROFILE_TITLES = {"desktop": "Desktop", "mobile": "Mobile (CPU 4×)"}

#: D-01 / GP-NFR-013.
D01_VISIBLE_OBJECTS = 3000
D01_DRAG_FRAME_MS = 16.0
#: Mirrors ``_inp_probe.VSYNC_TOLERANCE`` (this script must not import Selenium).
VSYNC_TOLERANCE = 0.1

#: The repository root when the module runs from a checkout (tests/e2e/<this>); inside the E2E container the file
#: sits at /app/<this> and there is no repository above it - the report is then written next to the records.
_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[2] if len(_HERE.parents) > 2 else _HERE.parent


# ── Reading ─────────────────────────────────────────────────────────────────


def _records_from_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def _records_from_junit(path: Path) -> list[dict]:
    records = []
    for prop in ET.parse(path).getroot().iter("property"):
        if prop.get("name") == RECORD_PROPERTY:
            records.append(json.loads(prop.get("value") or "null"))
    return records


def _files(paths: Iterable[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found += sorted(path.rglob(f"{RECORD_FILE_PREFIX}*.json"))
            found += sorted(path.rglob("junit*.xml"))
        elif path.is_file():
            found.append(path)
        else:
            raise FileNotFoundError(f"no such report input: {path}")
    return found


def load_records(paths: Iterable[Path]) -> tuple[list[dict], list[Path]]:
    """Every record in *paths*; one per (case, profile), the latest ``recorded_at`` winning; the sources read."""
    latest: dict[tuple[str, str], dict] = {}
    sources: list[Path] = []
    for path in _files(paths):
        records = _records_from_junit(path) if path.suffix == ".xml" else _records_from_json(path)
        records = [record for record in records if isinstance(record, dict)]
        if not records:
            continue
        sources.append(path)
        for record in records:
            if record.get("schema") != RECORD_SCHEMA:
                raise ValueError(f"{path}: a renderer record of schema {record.get('schema')!r}")
            key = (str(record["case"]), str(record["profile"]))
            if key not in latest or str(record.get("recorded_at", "")) > str(
                latest[key].get("recorded_at", "")
            ):
                latest[key] = record
    ordered = sorted(
        latest.values(),
        key=lambda r: (_rank(CASES, r["case"]), _rank(PROFILES, r["profile"])),
    )
    return ordered, sources


def _rank(order: tuple[str, ...], value: str) -> int:
    return order.index(value) if value in order else len(order)


# ── Deciding ────────────────────────────────────────────────────────────────


def gesture(record: dict, name: str) -> dict | None:
    for item in record.get("gestures") or []:
        if item.get("name") == name:
            return item
    return None


def max_visible(record: dict) -> int:
    return max(
        int((record.get(part) or {}).get("visible_objects") or 0)
        for part in ("census_fit", "census_zoomed")
    )


def drag_bound(record: dict) -> float:
    drag = gesture(record, "drag") or {}
    vsync = drag.get("vsync_ms")
    return D01_DRAG_FRAME_MS + (VSYNC_TOLERANCE * float(vsync) if vsync else 0.0)


def drag_violates(record: dict) -> bool | None:
    """``True`` = drag p95 over D-01's 16 ms, ``None`` = no drag frame time recorded."""
    drag = gesture(record, "drag")
    if not drag or drag.get("frame_p95_ms") is None:
        return None
    return float(drag["frame_p95_ms"]) > drag_bound(record)


def is_throttled(record: dict) -> bool:
    return record.get("profile") != "mobile" or record.get("throttle") == "applied"


@dataclass
class Reading:
    """One reading of D-01 over a set of records."""

    verdict: str  # "Go", "No-Go" or "offen"
    reasons: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


def _read_d01(records: list[dict], profiles: tuple[str, ...]) -> Reading:
    reading = Reading(verdict="No-Go")
    by_key = {(r["case"], r["profile"]): r for r in records}
    for case in CASES:
        for profile in profiles:
            record = by_key.get((case, profile))
            label = f"{case}/{profile}"
            if record is None:
                reading.gaps.append(f"{label}: keine Messung")
                continue
            if not is_throttled(record):
                reading.gaps.append(
                    f"{label}: CPU-Drosselung nicht verfügbar, ungedrosselt gemessen"
                )
            violated = drag_violates(record)
            if violated is None:
                reading.gaps.append(f"{label}: keine Drag-Frametime")
            elif violated:
                p95 = float(gesture(record, "drag")["frame_p95_ms"])
                reading.reasons.append(
                    f"{label}: Drag-Frametime p95 {p95:.1f} ms > {D01_DRAG_FRAME_MS:g} ms "
                    f"(Grenze mit Bildwechsel-Toleranz {drag_bound(record):.1f} ms)"
                )
            if case == "large" and max_visible(record) > D01_VISIBLE_OBJECTS:
                reading.reasons.append(
                    f"{label}: {max_visible(record)} sichtbare Objekte > {D01_VISIBLE_OBJECTS}"
                )
    if reading.reasons:
        reading.verdict = "Go"
    elif reading.gaps:
        reading.verdict = "offen"
    return reading


def decide(records: list[dict]) -> tuple[Reading, Reading]:
    """D-01 as written (every profile) and as placeholder (3) of #2759 narrows it (mobile profile only)."""
    literal = _read_d01(records, PROFILES)
    # A mobile record measured un-throttled is not "the mobile profile": it counts as missing here.
    mobile = _read_d01([record for record in records if is_throttled(record)], ("mobile",))
    return literal, mobile


# ── Writing ─────────────────────────────────────────────────────────────────


def _ms(value: object) -> str:
    return "–" if value is None else f"{float(value):.1f}"


def _budget_cell(item: dict) -> str:
    """GP-NFR-033/034 for one gesture: its p95 against its budget, with the same refresh tolerance as D-01."""
    p95, budget = item.get("frame_p95_ms"), item.get("frame_budget_ms")
    if p95 is None or budget is None:
        return "keine Messung"
    bound = float(budget) + VSYNC_TOLERANCE * float(item.get("vsync_ms") or 0.0)
    return "über Budget" if float(p95) > bound else "im Budget"


def render(records: list[dict], *, date: str, sources: list[Path]) -> str:
    literal, mobile = decide(records)
    lines = [
        f"# Renderer-Messung D-01 — {date}",
        "",
        "REQ-053 WP 9.6 (#2746), GP-NFR-033/034. Erzeugt von `tests/e2e/_renderer_report.py` aus den Messwerten",
        "von `tests/e2e/test_req053_renderer_profile.py`; nicht von Hand bearbeiten, neu erzeugen.",
        "",
        f"**Go/No-Go für WP 9.7 (D-01 wörtlich):** {literal.verdict}",
        "",
        f"**Lesart Platzhalter (3) aus #2759 (nur Mobile-Profil, CPU 4×):** {mobile.verdict}",
        "",
        "## Messwerte",
        "",
        "| Fall | Profil | CPU | Viewport | gespeichert (Beete/Slots/Pflanzen) | sichtbar Fit / gezoomt | Geste "
        "| Frames | p95 ms | max ms | Budget ms | GP-NFR-033/034 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        plan = record.get("plan") or {}
        stored = f"{plan.get('beds', '–')}/{plan.get('slots', '–')}/{plan.get('plants', '–')}"
        fit = (record.get("census_fit") or {}).get("visible_objects", "–")
        zoomed = (record.get("census_zoomed") or {}).get("visible_objects", "–")
        viewport = "×".join(str(v) for v in record.get("viewport") or []) or "–"
        cpu = f"{record.get('cpu_slowdown', 1)}×"
        if record.get("throttle") == "unavailable":
            cpu += " (Drosselung nicht verfügbar)"
        for item in record.get("gestures") or []:
            lines.append(
                f"| {CASE_TITLES.get(record['case'], record['case'])} "
                f"| {PROFILE_TITLES.get(record['profile'], record['profile'])} | {cpu} | {viewport} "
                f"| {stored} | {fit} / {zoomed} | {item.get('name')} | {item.get('frames', 0)} "
                f"| {_ms(item.get('frame_p95_ms'))} | {_ms(item.get('frame_max_ms'))} "
                f"| {_ms(item.get('frame_budget_ms'))} | {_budget_cell(item)} |"
            )
    if not records:
        lines.append("| – | – | – | – | – | – | – | – | – | – | – | keine Messung |")

    lines += ["", "## Entscheidung", ""]
    for title, reading in (("D-01 wörtlich", literal), ("Platzhalter (3), nur Mobile", mobile)):
        lines.append(f"**{title}: {reading.verdict}**")
        lines.append("")
        for reason in reading.reasons:
            lines.append(f"- Schwelle gerissen: {reason}")
        for gap in reading.gaps:
            lines.append(f"- Lücke: {gap}")
        if not reading.reasons and not reading.gaps:
            lines.append("- Keine Schwelle gerissen, alle Fälle gemessen.")
        lines.append("")

    lines += [
        "## Sichtbare Objekte",
        "",
        "| Fall | Profil | Beete | Marker einzeln | Marker gebündelt | Cluster | SVG-Knoten | px/m |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        for part, label in (("census_fit", "Fit"), ("census_zoomed", "gezoomt")):
            census = record.get(part) or {}
            px = record.get(f"px_per_m_{part.removeprefix('census_')}")
            lines.append(
                f"| {record['case']} ({label}) | {record['profile']} | {census.get('beds', '–')} "
                f"| {census.get('markers_single', '–')} | {census.get('markers_batched', '–')} "
                f"| {census.get('clusters', '–')} | {census.get('svg_nodes', '–')} | {_ms(px)} |"
            )

    if any(r["case"] == "synthetic_3000" and r["profile"] == "mobile" for r in records):
        lines += [
            "",
            "Hinweis: Auf dem Smartphone (390 × 844) kann der Plan „3 000 Objekte“ in der Gesamtansicht keine "
            "3 000 Objekte zeigen — die Fit-Zoomstufe liegt dort weit unter der Marker-LOD-Schwelle (10 px "
            "Markerabstand), der Renderer zeichnet Beete und Cluster. Der Mobile-Fall misst diese Last, nicht die "
            "D-01-Last; die Objektzahl wird so berichtet, wie sie gezeichnet wurde.",
        ]
    lines += [
        "",
        "## Methode",
        "",
        "- Frametime: Abstand aufeinanderfolgender `requestAnimationFrame`-Rückrufe während der Geste "
        "(`tests/e2e/_inp_probe.py`), 95. Perzentil nach Rangverfahren. Ein leerlaufender 60-Hz-Browser liest "
        "16,7 ms je Bild; eine Grenze gilt deshalb mit einer Toleranz von 10 % des gemessenen Leerlauf-Bildabstands "
        "als eingehalten (16,7 ms = kein Bild verloren).",
        "- Drag: ein Beet nahe der Canvas-Mitte, 30 Zeigerbewegungen à 16 ms hin und zurück, Netto-Versatz klein; "
        "danach Rückgängig. Zoom: Strg + Mausrad, 10 Rasten hinein und 10 heraus im Abstand von 40 ms, ab der "
        "Fit-Ansicht (überquert die Marker-LOD-Schwelle).",
        "- Sichtbare Objekte: was der SVG-Renderer nach Culling (20 % Rand) und LOD gezeichnet hat — Beete, "
        "Gartenobjekte, jeder Marker (einzeln oder gebündelt), jeder Cluster; die Grenze zählt nicht.",
        "- Profile: Desktop = Fenster 1920 × 1080 ohne Drosselung (Budget 16 ms); Mobile = Viewport 390 × 844 im "
        "Planungsmodus, CPU über CDP `Emulation.setCPUThrottlingRate` 4× gedrosselt (Budget 33 ms).",
        "- Beratend: eine Überschreitung ist eine Warnung im Testlauf, kein Fehler. Die Messung läuft im "
        "Selenium-Grid neben anderen Workern; Ausreißer sind möglich, eine knappe Entscheidung ist zu wiederholen.",
        "",
        "## Quellen",
        "",
    ]
    lines += [f"- `{_shown(path)}`" for path in sources] or ["- keine"]
    lines.append("")
    return "\n".join(lines)


def _shown(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "inputs", nargs="+", type=Path, help="JUnit XML / JSON files or directories"
    )
    parser.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument(
        "--output",
        default=None,
        help="target file, '-' for stdout (default: .audits/req-053/renderer-measurement-<date>.md)",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="exit 0 when the inputs hold no renderer record (a profile that skips the measurement)",
    )
    args = parser.parse_args(argv)
    records, sources = load_records(args.inputs)
    if not records and not args.allow_empty:
        print(f"no '{RECORD_PROPERTY}' record in {[str(p) for p in args.inputs]}", file=sys.stderr)
        return 1
    if not records:
        print("No renderer measurement in this run (skipped on this profile).")
        return 0
    text = render(records, date=args.date, sources=sources)
    if args.output == "-":
        print(text)
        return 0
    target = (
        Path(args.output)
        if args.output
        else REPO_ROOT / ".audits" / "req-053" / f"renderer-measurement-{args.date}.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
