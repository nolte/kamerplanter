#!/usr/bin/env python3
"""Manifest-driven coverage audit + per-requirement plan generator.

Liest expectations.yaml, prueft pro Anforderung jeden erwarteten Artefakt-
Eintrag gegen das Repo, berechnet Coverage und schreibt:

- ein Per-Anforderungs-Plan-Markdown unter .audits/req-coverage-audit/<ID>.md
  fuer jede Anforderung mit Coverage < 100 %
- ein Aggregate unter .audits/req-coverage-audit.md mit Plan-Index

Usage:
  python3 run_audit.py              # Full audit
  python3 run_audit.py REQ-013      # Single requirement
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).parent / "expectations.yaml"
AUDIT_DIR = ROOT / ".audits"
AGGREGATE = AUDIT_DIR / "req-coverage-audit.md"
PLAN_DIR = AUDIT_DIR / "req-coverage-audit"
TODAY = date.today().isoformat()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def matches(entry: dict) -> tuple[bool, list[str]]:
    """Return (found, evidence-paths) for a single manifest artefact entry."""
    kind = entry.get("kind", "file")
    path_pattern = entry.get("path", "")
    contains = entry.get("contains")

    target = ROOT / path_pattern if not any(c in path_pattern for c in "*?[") else None

    if kind == "file" and target is not None:
        if target.is_file():
            if contains and contains not in target.read_text(errors="ignore"):
                return False, [str(target.relative_to(ROOT))]
            return True, [str(target.relative_to(ROOT))]
        return False, []

    if kind == "dir" and target is not None:
        return target.is_dir(), [str(target.relative_to(ROOT))] if target.is_dir() else []

    if kind == "glob" or any(c in path_pattern for c in "*?["):
        matches_list = list(ROOT.glob(path_pattern))
        if matches_list:
            evidence = [str(p.relative_to(ROOT)) for p in matches_list]
            if contains:
                evidence = [
                    p for p in evidence
                    if contains in (ROOT / p).read_text(errors="ignore")
                ]
                return bool(evidence), evidence
            return True, evidence
        return False, []

    if kind == "pattern":
        # path is a file, contains is required
        if target is None or not target.is_file():
            return False, []
        if contains and contains in target.read_text(errors="ignore"):
            return True, [str(target.relative_to(ROOT))]
        return False, []

    return False, []


def evaluate(req_id: str, info: dict) -> dict:
    """Return per-requirement evaluation: dimensions + scores + matched files."""
    dims = {}
    expected = info.get("expected_artefacts", {}) or {}
    for dim, entries in expected.items():
        results = []
        for entry in entries or []:
            found, evidence = matches(entry)
            optional = entry.get("optional", False)
            status = "pass" if found else ("n/a" if optional else "fail")
            results.append({
                "role": entry.get("role"),
                "path": entry.get("path"),
                "kind": entry.get("kind", "file"),
                "optional": optional,
                "status": status,
                "evidence": evidence,
                "rationale": entry.get("rationale"),
            })
        dims[dim] = results

    # Score per dimension: pass / (pass + fail), n/a wird ignoriert
    dim_scores = {}
    for dim, items in dims.items():
        passes = sum(1 for it in items if it["status"] == "pass")
        fails = sum(1 for it in items if it["status"] == "fail")
        nas = sum(1 for it in items if it["status"] == "n/a")
        dim_scores[dim] = {
            "pass": passes,
            "fail": fails,
            "na": nas,
            "ratio": (passes / (passes + fails)) if (passes + fails) else None,
            "label": f"{passes}/{passes + fails}" if (passes + fails) else "n/a",
        }

    # Overall: arithmetic mean of dimension ratios where ratio is not None
    ratios = [s["ratio"] for s in dim_scores.values() if s["ratio"] is not None]
    overall = (sum(ratios) / len(ratios) * 100) if ratios else None

    # Status mapping
    if overall is None:
        status_label = "Idee"
    elif overall >= 90:
        status_label = "Implementiert"
    elif overall >= 60:
        status_label = "Teilweise"
    elif overall >= 30:
        status_label = "Lueckenhaft"
    else:
        status_label = "Spezifiziert"

    # Priority for plan
    if overall is None or overall == 100:
        priority = None
    elif overall < 30:
        priority = "blocker"
    elif overall < 60:
        priority = "warning"
    else:
        priority = "info"

    # Aufwandsschaetzung: anhand FEHLENDER Pflicht-Artefakte
    missing_required = sum(
        1 for items in dims.values() for it in items
        if it["status"] == "fail" and not it["optional"]
    )
    if missing_required == 0:
        effort = "S"
    elif missing_required <= 3:
        effort = "M"
    elif missing_required <= 8:
        effort = "L"
    else:
        effort = "XL"

    return {
        "req": req_id,
        "title": info.get("title", ""),
        "type": info.get("type", "req"),
        "spec_path": info.get("spec_path", ""),
        "drift": info.get("drift", {}),
        "dimensions": dims,
        "dim_scores": dim_scores,
        "overall_pct": overall,
        "status": status_label,
        "priority": priority,
        "effort": effort,
        "missing_required_count": missing_required,
    }


def render_plan(eval_result: dict) -> str:
    """Render a per-requirement plan markdown."""
    e = eval_result
    drift = e["drift"]
    overall_str = f"{e['overall_pct']:.0f}%" if e["overall_pct"] is not None else "n/a"

    lines = [
        "---",
        "audit-type: req-coverage-plan",
        f"requirement: {e['req']}",
        f"title: {e['title']}",
        f"type: {e['type']}",
        f"spec_path: {e['spec_path']}",
        f"coverage_score: {overall_str}",
        f"status: {e['status'].lower()}",
        f"priority: {e['priority'] or 'none'}",
        f"effort: {e['effort']}",
        f"created: {TODAY}",
        f"audit_run: {git_sha()}",
        "---",
        "",
        f"# Ausfuehrungsplan: {e['req']} {e['title']}",
        "",
        "## Kontext",
        f"- **Spec**: `{e['spec_path']}`",
        f"- **Coverage**: {overall_str}",
        f"- **Status**: {e['status']}",
        f"- **Aufwand-Schaetzung**: {e['effort']} ({e['missing_required_count']} Pflicht-Artefakte fehlen)",
    ]

    if drift.get("memory_status_field"):
        lines.append(f"- **MEMORY-Status**: {drift['memory_status_field']}")
    if drift.get("cross_refs"):
        lines.append(f"- **Cross-References**: {', '.join(drift['cross_refs'])}")

    lines += ["", "## Erwartete Artefakte"]

    for dim, items in e["dimensions"].items():
        if not items:
            continue
        score = e["dim_scores"][dim]
        lines.append(f"\n### Dimension: {dim} ({score['label']})\n")
        lines.append("| Rolle | Pfad | Kind | Optional | Status | Evidenz / Begruendung |")
        lines.append("|---|---|---|---|---|---|")
        for it in items:
            evidence = ", ".join(it["evidence"][:3]) if it["evidence"] else ""
            if not evidence and it.get("rationale"):
                evidence = f"_(Begruendung: {it['rationale']})_"
            elif it.get("rationale"):
                evidence = f"{evidence} — _(Begruendung: {it['rationale']})_"
            opt = "ja" if it["optional"] else "nein"
            status_icon = {"pass": "OK", "fail": "FEHLT", "n/a": "n/a"}[it["status"]]
            lines.append(
                f"| {it['role'] or '—'} | `{it['path']}` | {it['kind']} | {opt} | "
                f"{status_icon} | {evidence} |"
            )

    # Aufgabenliste — pro fehlendem Pflicht-Artefakt eine Aufgabe
    lines += ["", "## Aufgaben (priorisiert, abarbeitbar)"]
    aufgabe_idx = 0
    for dim, items in e["dimensions"].items():
        for it in items:
            if it["status"] != "fail" or it["optional"]:
                continue
            aufgabe_idx += 1
            role = it["role"] or "artefact"
            path = it["path"]
            rationale = it.get("rationale") or "Spec-Vorgabe"
            # Aufwand pro Aufgabe ableiten aus Pfadtyp
            if "test" in role.lower() or "_test" in path.lower():
                aufgabe_effort = "S"
                action = "Testdatei anlegen"
            elif "router" in role.lower():
                aufgabe_effort = "M"
                action = "FastAPI-Router anlegen"
            elif "service" in role.lower():
                aufgabe_effort = "M"
                action = "Service-Klasse anlegen"
            elif "engine" in role.lower():
                aufgabe_effort = "M"
                action = "Engine/Calculator anlegen"
            elif "model" in role.lower():
                aufgabe_effort = "S"
                action = "Pydantic-Model anlegen"
            elif "repository" in role.lower():
                aufgabe_effort = "S"
                action = "Repository anlegen"
            elif "page" in role.lower():
                aufgabe_effort = "M"
                action = "React-Page-Komponente anlegen"
            elif "slice" in role.lower():
                aufgabe_effort = "S"
                action = "Redux-Slice anlegen"
            else:
                aufgabe_effort = "S"
                action = "Artefakt erstellen"

            lines += [
                "",
                f"### Aufgabe {aufgabe_idx} — {role} anlegen [{aufgabe_effort}]",
                f"- **Zu tun**: {action} fuer {role}",
                f"- **Pfad**: `{path}` ({it['kind']})",
                f"- **Spec-Referenz**: `{e['spec_path']}` — Sektion zu {role}",
                f"- **Begruendung**: {rationale}",
                f"- **Akzeptanzkriterium**: Datei existiert + 1 Smoke-Test (falls Code) bzw. Glob matched (falls Pattern)",
            ]
            # Skill-Empfehlung
            if e["type"] == "req":
                if "test" in role.lower():
                    lines.append(f"- **Empfohlener Skill**: `/test-extract {e['req']}`")
                elif "page" in role.lower():
                    lines.append(f"- **Empfohlener Agent**: `frontend-usability-optimizer`")
                else:
                    lines.append(f"- **Empfohlener Skill**: `/implement {e['req']}` oder Agent `fullstack-developer`")
            elif e["type"] == "nfr":
                lines.append(f"- **Empfohlener Skill**: `/check-architecture` (NFR-Compliance)")
            else:
                lines.append(f"- **Empfohlener Agent**: `frontend-usability-optimizer`")

    if aufgabe_idx == 0:
        lines += [
            "",
            "_Keine Pflicht-Artefakte fehlen. Coverage-Defizit liegt nur in optionalen "
            "Artefakten oder Drift-Findings._",
        ]

    # Empfohlene Skill-Sequenz
    lines += [
        "",
        "## Empfohlene Skill-Sequenz",
        f"1. Aufgaben in obiger Reihenfolge abarbeiten (jeweils kleinster sinnvoller Commit)",
        f"2. `/req-coverage-audit {e['req']}` zur Verifikation nach jedem groesseren Block",
        f"3. Bei Coverage-Erreichen 100 % wird der Plan beim naechsten Full-Audit "
        "automatisch geloescht (git log bewahrt History)",
    ]

    if drift.get("cross_refs"):
        lines += [
            "",
            "## Abhaengigkeiten",
            f"- Cross-Referenzen aus Spec: {', '.join(drift['cross_refs'])}",
            "- Vor / nach diesen Anforderungen pruefen, ob Reihenfolge angepasst werden muss",
        ]

    return "\n".join(lines) + "\n"


def render_aggregate(evaluations: list[dict], skipped_specs: list[str]) -> str:
    """Render the aggregate plan-index markdown."""
    sha = git_sha()
    by_type = {"req": [], "nfr": [], "ui-nfr": []}
    for ev in evaluations:
        by_type[ev["type"]].append(ev)

    plans_open = [ev for ev in evaluations if ev["overall_pct"] is None or ev["overall_pct"] < 100]
    plans_closed_count = sum(1 for ev in evaluations if ev["overall_pct"] == 100)

    status_dist = {}
    for ev in evaluations:
        status_dist[ev["status"]] = status_dist.get(ev["status"], 0) + 1

    lines = [
        "---",
        "review-type: req-coverage-audit",
        "target-repo: kamerplanter",
        f"total-count: {len(evaluations)}",
        f"req-count: {len(by_type['req'])}",
        f"nfr-count: {len(by_type['nfr'])}",
        f"ui-nfr-count: {len(by_type['ui-nfr'])}",
        f"manifest-coverage: {len(evaluations)}/{len(evaluations) + len(skipped_specs)}",
        f"plans-open: {len(plans_open)}",
        f"plans-closed: {plans_closed_count}",
        f"repo-revision: {sha}",
        f"created: {TODAY}",
        "mode: full",
        "---",
        "",
        "## Scope",
        f"Vollstaendiger Manifest-getriebener Coverage-Audit ueber alle "
        f"{len(by_type['req'])} REQ + {len(by_type['nfr'])} NFR + {len(by_type['ui-nfr'])} UI-NFR. "
        "Manifest-Quelle: `.claude/skills/req-coverage-audit/expectations.yaml`. Pro Anforderung "
        "mit Coverage < 100 % wurde ein eigenstaendiger Per-Anforderungs-Plan unter "
        "`.audits/req-coverage-audit/<ID>.md` mit konkreten Aufgaben + Akzeptanzkriterien angelegt.",
        "",
        "## Manifest-Vollstaendigkeit",
        f"- Alle Anforderungen im Manifest: **{len(evaluations)}/{len(evaluations) + len(skipped_specs)}**",
    ]
    if skipped_specs:
        lines.append(f"- **BLOCKER — fehlende Manifest-Eintraege**: {', '.join(skipped_specs)}")
    else:
        lines.append("- Vollstaendigkeit OK — keine Manifest-Luecken.")

    # Verteilung
    lines += ["", "## Verteilung gesamt"]
    total = len(evaluations)
    for status_key in ("Implementiert", "Teilweise", "Lueckenhaft", "Spezifiziert", "Idee"):
        n = status_dist.get(status_key, 0)
        pct = (n / total * 100) if total else 0
        lines.append(f"- {status_key}: {n} ({pct:.0f} %)")

    # Pro Typ Tabelle
    for type_label, type_key in (
        ("REQ — Funktional", "req"),
        ("NFR — Cross-cutting", "nfr"),
        ("UI-NFR — Frontend", "ui-nfr"),
    ):
        items = sorted(by_type[type_key], key=lambda x: x["req"])
        if not items:
            continue
        lines += ["", f"## Coverage-Uebersicht: {type_label}", ""]
        # Header per type
        if type_key == "req":
            lines.append("| ID | Titel | Backend | Frontend | Tests | Score | Status | Plan |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for ev in items:
                be = ev["dim_scores"].get("backend", {}).get("label", "n/a")
                fe = ev["dim_scores"].get("frontend", {}).get("label", "n/a")
                te = ev["dim_scores"].get("tests", {}).get("label", "n/a")
                score = f"{ev['overall_pct']:.0f}%" if ev["overall_pct"] is not None else "—"
                plan_link = f"[Plan](req-coverage-audit/{ev['req']}.md)" if ev["overall_pct"] is None or ev["overall_pct"] < 100 else "—"
                lines.append(f"| {ev['req']} | {ev['title']} | {be} | {fe} | {te} | {score} | {ev['status']} | {plan_link} |")
        else:
            lines.append("| ID | Titel | Artefakte | Validierung | Score | Status | Plan |")
            lines.append("|---|---|---|---|---|---|---|")
            for ev in items:
                art = ev["dim_scores"].get("artefacts", ev["dim_scores"].get("frontend", {})).get("label", "n/a")
                val = ev["dim_scores"].get("validation", ev["dim_scores"].get("tests", {})).get("label", "n/a")
                score = f"{ev['overall_pct']:.0f}%" if ev["overall_pct"] is not None else "—"
                plan_link = f"[Plan](req-coverage-audit/{ev['req']}.md)" if ev["overall_pct"] is None or ev["overall_pct"] < 100 else "—"
                lines.append(f"| {ev['req']} | {ev['title']} | {art} | {val} | {score} | {ev['status']} | {plan_link} |")

    # Roadmap
    lines += ["", "## Roadmap (priorisierter Ausfuehrungsplan)"]
    lines.append("Sortiert nach Prioritaet (blocker > warning > info) und Coverage-Score (aufsteigend):")
    lines.append("")
    lines.append("| # | Anforderung | Typ | Status | Score | Aufwand | Plan |")
    lines.append("|---|---|---|---|---|---|---|")
    priority_order = {"blocker": 0, "warning": 1, "info": 2, None: 3}
    sorted_plans = sorted(
        plans_open,
        key=lambda x: (priority_order.get(x["priority"], 4), x["overall_pct"] if x["overall_pct"] is not None else -1)
    )
    for i, ev in enumerate(sorted_plans, 1):
        score = f"{ev['overall_pct']:.0f}%" if ev["overall_pct"] is not None else "—"
        lines.append(f"| {i} | {ev['req']} {ev['title']} | {ev['type']} | {ev['status']} | {score} | {ev['effort']} | [Plan](req-coverage-audit/{ev['req']}.md) |")

    # Plan-Index alphabetisch
    lines += ["", "## Plan-Index (alphabetisch, alle offenen Plans)"]
    lines.append("| Anforderung | Plan | Coverage | Aufwand |")
    lines.append("|---|---|---|---|")
    for ev in sorted(plans_open, key=lambda x: x["req"]):
        score = f"{ev['overall_pct']:.0f}%" if ev["overall_pct"] is not None else "—"
        lines.append(f"| {ev['req']} {ev['title']} | [.audits/req-coverage-audit/{ev['req']}.md](req-coverage-audit/{ev['req']}.md) | {score} | {ev['effort']} |")

    # Run log
    lines += [
        "",
        "## Run log",
        f"- {TODAY} — Manifest geladen: {len(evaluations)} Eintraege, 0 Luecken",
        f"- {TODAY} — Coverage berechnet (Manifest-getrieben, keine Heuristik)",
        f"- {TODAY} — Per-Anforderungs-Plans geschrieben: {len(plans_open)} offen, {plans_closed_count} mit Coverage 100 %",
        f"- {TODAY} — Aggregate geschrieben",
    ]

    return "\n".join(lines) + "\n"


def main():
    if not MANIFEST.is_file():
        print(f"FEHLER: Manifest fehlt: {MANIFEST}", file=sys.stderr)
        sys.exit(2)

    manifest = yaml.safe_load(MANIFEST.read_text())
    requirements = manifest["requirements"]

    # Optional: Single-Mode
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        if target not in requirements:
            print(f"FEHLER: {target} nicht im Manifest", file=sys.stderr)
            sys.exit(2)
        ev = evaluate(target, requirements[target])
        PLAN_DIR.mkdir(parents=True, exist_ok=True)
        plan_path = PLAN_DIR / f"{target}.md"
        plan_path.write_text(render_plan(ev))
        print(f"WROTE {plan_path.relative_to(ROOT)} — {ev['status']} ({ev['overall_pct']:.0f}%)")
        return

    # Vollstaendigkeits-Check
    spec_ids = set()
    for spec_dir in (ROOT / "spec/req", ROOT / "spec/nfr", ROOT / "spec/ui-nfr"):
        for p in spec_dir.glob("*.md"):
            if p.name == "README.md":
                continue
            # Parse ID from filename: REQ-001_..., NFR-008a_..., UI-NFR-007_...
            m = re.match(r"((?:UI-)?(?:REQ|NFR)-[\w-]+?)(?:_|\.md)", p.name)
            if m:
                spec_ids.add(m.group(1))
    skipped = sorted(spec_ids - set(requirements.keys()))
    extra = sorted(set(requirements.keys()) - spec_ids)
    if extra:
        print(f"WARN: Manifest-Eintraege ohne Spec: {extra}", file=sys.stderr)

    # Full-Audit
    evaluations = []
    for req_id in sorted(requirements.keys()):
        info = requirements[req_id]
        ev = evaluate(req_id, info)
        evaluations.append(ev)

    # Per-Anforderungs-Plans schreiben (nur fuer Coverage < 100 %)
    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    # Vorher: existierende Plans erfassen, um nach dem Run die zu loeschen die jetzt 100 % erreichen
    existing_plans = {p.stem for p in PLAN_DIR.glob("*.md")}
    new_plans = set()
    closed_count = 0

    for ev in evaluations:
        if ev["overall_pct"] is None or ev["overall_pct"] < 100:
            plan_path = PLAN_DIR / f"{ev['req']}.md"
            plan_path.write_text(render_plan(ev))
            new_plans.add(ev["req"])

    # Plans loeschen, die nicht mehr noetig sind
    for closed_id in existing_plans - new_plans:
        if closed_id == ".gitkeep":
            continue
        (PLAN_DIR / f"{closed_id}.md").unlink(missing_ok=True)
        closed_count += 1

    # Aggregate schreiben
    AGGREGATE.parent.mkdir(parents=True, exist_ok=True)
    AGGREGATE.write_text(render_aggregate(evaluations, skipped))

    # Summary
    by_status = {}
    for ev in evaluations:
        by_status[ev["status"]] = by_status.get(ev["status"], 0) + 1
    print(f"=== Audit complete ===")
    print(f"Total: {len(evaluations)} requirements")
    for status, n in sorted(by_status.items()):
        print(f"  {status}: {n}")
    print(f"Plans written: {len(new_plans)}")
    print(f"Plans closed (now 100%): {closed_count}")
    if skipped:
        print(f"BLOCKER — Manifest-Luecken: {skipped}")
    print(f"Aggregate: {AGGREGATE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
