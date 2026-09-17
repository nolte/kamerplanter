#!/usr/bin/env python3
"""Refuse a local ``.claude/`` skill or agent that shadows a portfolio-plugin one.

CLAUDE.md §"Claude Code plugin adoption" gives this repository a DRY rule:
generic delivery capabilities come from the ``nolte-shared`` / ``nolte-engineering``
plugins, only domain assets stay under ``.claude/``. Until #1405 nothing measured
it, and the measurement is what this script is. Two shadows had accumulated,
``check-test-pyramid`` over ``nolte-engineering:test-pyramid-check`` and ``pre-pr``
over ``nolte-engineering:quality-gate``, and both were found by reading.

**What this check can and cannot see — read this before trusting a zero.**

It compares *names*, in two ways:

* **exact** — a local asset whose name equals a plugin asset's name;
* **token-set** — a local asset whose hyphen-separated tokens are the same
  *multiset* as a plugin asset's. This is the rung that matters: the #1405 pair
  ``check-test-pyramid`` / ``test-pyramid-check`` is an anagram of hyphen tokens,
  so an exact-name guard — the obvious one to write — would have reported green
  on the exact case it was built for.

It **cannot** see a shadow whose names share no tokens. ``pre-pr`` over
``quality-gate`` is precisely that shape: the same capability under two unrelated
names, discoverable only by reading both assets. A zero here therefore means "no
lexically detectable shadow", never "no shadow". The reading pass is not
replaced by this script; it is only made unnecessary for the cheap half.

**Where the plugin inventory comes from.** Preferably the live checkout, at
``$NOLTE_CLAUDE_SHARED`` or ``~/repos/github/claude-shared``. CI has no such
checkout — the required ``static`` lane runs on a bare single-repo runner — so
the names are additionally kept in ``.claude/plugin-adoption.yml`` and the check
runs off that snapshot when the checkout is absent. The snapshot holds *names
only*: it is an inventory, not a copy of plugin content, so the no-copies rule is
untouched. When the checkout *is* present, the snapshot is verified against it and
a divergence is a finding — otherwise the snapshot would rot into a guard that
measures a portfolio that no longer exists. ``--refresh`` rewrites it.

A missing checkout is announced loudly on stderr and never silently skipped: the
check still runs, against the snapshot, and says so.

Exit codes: 0 clean, 1 findings, 2 usage/IO error.

Traces to #1405.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

ADOPTION_FILE = Path(".claude/plugin-adoption.yml")
LOCAL_SKILLS = Path(".claude/skills")
LOCAL_AGENTS = Path(".claude/agents")
DEFAULT_CHECKOUT = Path("~/repos/github/claude-shared").expanduser()
ENV_VAR = "NOLTE_CLAUDE_SHARED"

# The hub plugin ships its own skills/agents at the repository root; the other
# plugins carry theirs under plugins/<name>/.
ROOT_PLUGIN = "nolte-shared"


@dataclass(frozen=True)
class Asset:
    """A skill or agent, identified by the name Claude Code addresses it with."""

    name: str
    kind: str  # "skill" | "agent"
    plugin: str | None = None  # None for local assets

    @property
    def label(self) -> str:
        return f"{self.plugin}:{self.name}" if self.plugin else self.name


def token_key(name: str) -> tuple[tuple[str, int], ...]:
    """Return the order-insensitive multiset of a name's hyphen tokens.

    A multiset, not a set: ``a-b-b`` and ``a-b`` are different capabilities, and
    collapsing repeats would equate them. Sorted, so the key is hashable and
    comparable.
    """
    return tuple(sorted(Counter(name.split("-")).items()))


def read_local(repo_root: Path) -> list[Asset]:
    """Collect the repository's own skills and agents."""
    assets: list[Asset] = []
    skills_dir = repo_root / LOCAL_SKILLS
    if skills_dir.is_dir():
        assets += [
            Asset(p.name, "skill")
            for p in sorted(skills_dir.iterdir())
            if p.is_dir() and (p / "SKILL.md").is_file()
        ]
    agents_dir = repo_root / LOCAL_AGENTS
    if agents_dir.is_dir():
        assets += [Asset(p.stem, "agent") for p in sorted(agents_dir.glob("*.md"))]
    return assets


def read_checkout(checkout: Path) -> list[Asset]:
    """Collect the plugin skills and agents from a live ``claude-shared`` checkout."""
    assets: list[Asset] = []
    skill_dirs = [(ROOT_PLUGIN, checkout / "skills")]
    agent_dirs = [(ROOT_PLUGIN, checkout / "agents")]
    plugins_root = checkout / "plugins"
    if plugins_root.is_dir():
        for plugin_dir in sorted(plugins_root.iterdir()):
            if plugin_dir.is_dir():
                skill_dirs.append((plugin_dir.name, plugin_dir / "skills"))
                agent_dirs.append((plugin_dir.name, plugin_dir / "agents"))
    for plugin, directory in skill_dirs:
        if directory.is_dir():
            assets += [
                Asset(p.name, "skill", plugin)
                for p in sorted(directory.iterdir())
                if p.is_dir() and (p / "SKILL.md").is_file()
            ]
    for plugin, directory in agent_dirs:
        if directory.is_dir():
            assets += [Asset(p.stem, "agent", plugin) for p in sorted(directory.glob("*.md"))]
    return assets


def resolve_checkout() -> Path | None:
    """Return the ``claude-shared`` checkout, or None when it is not reachable."""
    override = os.environ.get(ENV_VAR)
    candidate = Path(override).expanduser() if override else DEFAULT_CHECKOUT
    return candidate if (candidate / ".claude-plugin").is_dir() else None


def load_adoption(path: Path) -> dict:
    """Read ``.claude/plugin-adoption.yml``; an absent file is an empty document."""
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def inventory_from_document(document: dict) -> list[Asset]:
    """Rebuild the plugin asset list from the snapshot document."""
    assets: list[Asset] = []
    for plugin, kinds in (document.get("inventory") or {}).items():
        for kind in ("skills", "agents"):
            for name in kinds.get(kind) or []:
                assets.append(Asset(name, kind.rstrip("s"), plugin))
    return assets


def document_from_inventory(assets: list[Asset], version: str | None) -> dict:
    """Render the snapshot mapping for a collected plugin asset list."""
    inventory: dict[str, dict[str, list[str]]] = {}
    for asset in assets:
        assert asset.plugin is not None
        bucket = inventory.setdefault(asset.plugin, {"skills": [], "agents": []})
        bucket[f"{asset.kind}s"].append(asset.name)
    for bucket in inventory.values():
        for kind in bucket:
            bucket[kind] = sorted(bucket[kind])
    return {"marketplace_version": version, "inventory": dict(sorted(inventory.items()))}


def marketplace_version(checkout: Path) -> str | None:
    """Read the version the checkout's marketplace manifest declares."""
    manifest = checkout / ".claude-plugin" / "marketplace.json"
    if not manifest.is_file():
        return None
    import json

    try:
        return (json.loads(manifest.read_text(encoding="utf-8")).get("metadata") or {}).get(
            "version"
        )
    except (ValueError, OSError):  # pragma: no cover — defensive
        return None


def find_shadows(local: list[Asset], plugin: list[Asset]) -> list[tuple[Asset, Asset, str]]:
    """Pair every local asset with the plugin assets whose name collides with it."""
    by_exact: dict[str, list[Asset]] = {}
    by_token: dict[tuple, list[Asset]] = {}
    for asset in plugin:
        by_exact.setdefault(asset.name, []).append(asset)
        by_token.setdefault(token_key(asset.name), []).append(asset)

    findings: list[tuple[Asset, Asset, str]] = []
    for asset in local:
        seen: set[str] = set()
        for match in by_exact.get(asset.name, []):
            findings.append((asset, match, "exact"))
            seen.add(match.label)
        for match in by_token.get(token_key(asset.name), []):
            if match.label not in seen:
                findings.append((asset, match, "token-set"))
                seen.add(match.label)
    return findings


def allowlist_index(document: dict) -> dict[str, str]:
    """Map an allowlisted ``local`` name to its recorded reason."""
    index: dict[str, str] = {}
    for entry in document.get("allowlist") or []:
        name = entry.get("local")
        reason = (entry.get("reason") or "").strip()
        if name:
            index[name] = reason
    return index


def run(repo_root: Path, refresh: bool = False) -> int:
    document = load_adoption(repo_root / ADOPTION_FILE)
    checkout = resolve_checkout()
    problems: list[str] = []

    if checkout is None:
        print(
            f"NOTE: no claude-shared checkout found (set ${ENV_VAR} or clone to "
            f"{DEFAULT_CHECKOUT}). The shadow check still runs, against the "
            f"{ADOPTION_FILE} snapshot; the snapshot itself could not be verified "
            "against the live plugins.",
            file=sys.stderr,
        )
        plugin_assets = inventory_from_document(document)
        if not plugin_assets:
            print(
                f"ERROR: {ADOPTION_FILE} carries no inventory and no checkout is "
                "reachable, so this check would examine nothing.",
                file=sys.stderr,
            )
            return 2
    else:
        plugin_assets = read_checkout(checkout)
        if refresh:
            payload = document_from_inventory(plugin_assets, marketplace_version(checkout))
            document.update(payload)
            (repo_root / ADOPTION_FILE).write_text(
                _render(document), encoding="utf-8"
            )
            print(f"Refreshed {ADOPTION_FILE} from {checkout}.")
            return 0
        snapshot = {a.label for a in inventory_from_document(document)}
        live = {a.label for a in plugin_assets}
        if snapshot != live:
            added = sorted(live - snapshot)
            removed = sorted(snapshot - live)
            problems.append(
                f"{ADOPTION_FILE} has drifted from {checkout}: "
                f"{len(added)} added ({', '.join(added) or '-'}), "
                f"{len(removed)} gone ({', '.join(removed) or '-'}). "
                "Run `task check:plugin-shadowing -- --refresh` and review the diff."
            )

    local_assets = read_local(repo_root)
    allowed = allowlist_index(document)
    findings = find_shadows(local_assets, plugin_assets)
    shadowed_names = {local.name for local, _, _ in findings}

    for local, match, how in findings:
        if local.name in allowed:
            continue
        problems.append(
            f".claude/{local.kind}s/{local.name} shadows {match.label} ({match.kind}) "
            f"— {how} name collision. Adopt the plugin asset and retire the local one, "
            f"or record a reasoned entry in {ADOPTION_FILE} `allowlist`."
        )

    for name, reason in sorted(allowed.items()):
        if name not in shadowed_names:
            problems.append(
                f"{ADOPTION_FILE} allowlists `{name}`, which no longer collides with any "
                f"plugin asset. Remove the entry (recorded reason: {reason or 'none'})."
            )
        elif not reason:
            problems.append(
                f"{ADOPTION_FILE} allowlists `{name}` with no reason. An unexplained "
                "exemption is indistinguishable from an oversight."
            )

    if problems:
        print("Plugin-shadowing check FAILED:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nRule: CLAUDE.md §'Claude Code plugin adoption' — no local copy of a "
            "plugin-owned capability (#1405).",
            file=sys.stderr,
        )
        return 1

    source = str(checkout) if checkout else f"{ADOPTION_FILE} snapshot"
    print(
        f"Plugin-shadowing check passed: {len(local_assets)} local asset(s) against "
        f"{len(plugin_assets)} plugin asset(s) from {source}; "
        f"{len(allowed)} reasoned exemption(s)."
    )
    print(
        "Name-based only — a shadow under an unrelated name (the `pre-pr` / "
        "`quality-gate` shape) is invisible here and needs a reading pass."
    )
    return 0


_HEADER = """\
# Inventory of the portfolio-plugin skills and agents, plus the reasoned
# exemptions from the no-shadowing rule. Consumed by
# scripts/check_skill_plugin_shadowing.py (#1405).
#
# NAMES ONLY. This is not a copy of plugin content -- CLAUDE.md
# §"Claude Code plugin adoption" forbids that, and an inventory is what lets the
# check run in CI, where no claude-shared checkout exists. Regenerate with
# `task check:plugin-shadowing -- --refresh` against a live checkout; the check
# itself goes red when the two diverge, so the snapshot cannot rot unnoticed.
"""


def _render(document: dict) -> str:
    allowlist = document.get("allowlist")
    body = {
        "marketplace_version": document.get("marketplace_version"),
        "inventory": document.get("inventory") or {},
    }
    text = _HEADER + yaml.safe_dump(body, sort_keys=False, allow_unicode=True, width=100)
    if allowlist is not None:
        text += "\n" + yaml.safe_dump(
            {"allowlist": allowlist}, sort_keys=False, allow_unicode=True, width=100
        )
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="rewrite the inventory snapshot from the live checkout and exit",
    )
    parser.add_argument(
        "--repo-root", default=".", help="repository root to check (default: cwd)"
    )
    args = parser.parse_args(argv)
    return run(Path(args.repo_root).resolve(), refresh=args.refresh)


if __name__ == "__main__":
    raise SystemExit(main())
