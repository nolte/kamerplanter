#!/usr/bin/env python3
"""Refuse a seeded catalogue that has outgrown the page its list view fetches.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_seed_catalogue_page_size.py
    python3 scripts/check_seed_catalogue_page_size.py --list   # name every seed file counted
    python3 scripts/check_seed_catalogue_page_size.py --json   # machine-readable

**The defect it closes (#995).** A list view that issues one bounded request and
renders the result as if it were the whole set loses every row past the page
size, silently. ``DataTable`` makes that worse rather than visible: its search,
sort and pagination all run **client-side**, over the rows already in the store.
So a user who types the name of a row that never arrived is told "no results" —
the UI actively denies the row exists. Nothing marks the list as truncated.

The failure is invisible from both ends. Nobody counts the seed files, and
nobody notices a catalogue is short unless they already know what should be in
it, which on reference data is nobody. It was reported as a *search* defect
(#956) two milestones after it started.

**Why a static check and not a test.** The two numbers that must not cross live
in different languages, on different sides of the API, and neither knows about
the other: the seed row count is YAML under ``src/backend``, the page size is
TypeScript under ``src/frontend``. No unit test on either side can see both, and
an end-to-end test would only catch it with a database seeded to the exact size
that trips it — which is the state nobody notices in the first place. A gate
that reads both trees is the only place the comparison exists.

What it enforces
----------------

Per registered catalogue, one of two contracts:

* **complete** — the frontend module named in the registry must reference the
  complete-catalogue loader. Then the catalogue cannot outgrow anything and only
  the resulting request count is reported.
* **bounded: N** — the list view fetches one page of N. Green while the seeded
  row count is at or below N; **red above it**, because at that point rows exist
  that the list view cannot show.

Plus one precondition without which the counts are fiction: **every seed file
that declares rows for a registered catalogue must be loaded by some seeder.**
``fertilizers_supplement.yaml`` (22 fertilizers) and ``nutrient_plans_hydro.yaml``
(12 plans) fail this — they have been in ``seed_data/`` since #8 and no code path
reads them, so the products in them reach no database and no browser. That is why
the fertilizer count here is 31 and not the 53 a naive ``grep`` of the seed
directory reports; counting the orphans would demand a page-size fix for rows
that do not exist, and a check with false positives gets suppressed.

Those two are **recorded** in :data:`KNOWN_UNLOADED_SEED_FILES` with a reason, so
they do not turn the gate red while the decision they need is pending — a *new*
orphan still fails. The escape hatch is a reason rather than a count, following
``check_utc_calendar_day.py``'s ``# local-clock:`` sites: a reviewer can argue
with a reason. Their row counts stay in the report on every run, so this is a
deferral somebody reads, not a suppression.

Why the counts are derived, not recorded
----------------------------------------

There is no hand-maintained "expected 53" anywhere in this file. #973 was filed
because a ratchet with a hand-edited constant put every concurrent pull request
on the same line of the same file. Both sides of the comparison are read from
the tree instead:

* the **row count** by parsing the seed YAML;
* the **loaded-file set** by parsing the migration modules for ``.yaml`` string
  literals (``load_yaml("x.yaml")`` and ``YAML_FILES = [...]`` alike), treated as
  ``fnmatch`` patterns so ``seed_steckbrief_consistency.py``'s
  ``glob("plant_info*.yaml")`` resolves too;
* the **complete-loader contract** by checking the frontend module for the loader
  symbol.

What *is* declared is structure, not quantity: which seed keys belong to which
catalogue, which field identifies a row, and which frontend module owns the load.
Those change when a catalogue is added or moved — not when somebody adds a row —
so two concurrent pull requests do not collide on them.

The one number still written by hand is a ``bounded`` page size, and only for a
list view that deliberately fetches one page. Every catalogue is ``complete``
after #995, so the field currently has no users; it exists because the next
catalogue may legitimately want paging, and a bound the check cannot see is a
bound it cannot enforce.

Counting rules — and why the count is approximate
--------------------------------------------------

A row counts when it appears under one of the catalogue's seed keys in a loaded
file. Rows are de-duplicated by the identity field(s) the corresponding seeder
upserts on — ``scientific_name`` for species, ``(product_name, brand)`` for
fertilizers, and so on — because the same species defined in ``species.yaml`` and
again in a ``plant_info`` file is one row in the collection, not two.

The number is **stable and monotone**, not exact. It cannot see a row a seeder
creates in code, a row a seeder skips because a referenced species is missing, or
anything a tenant creates at runtime. All of those make the real collection
*larger* than this count, never smaller, so the check under-reports rather than
crying wolf — and a catalogue that is over the bound here is over it for certain.

Tenant-created rows are the honest gap: a tenant with 30 fertilizers of its own
crosses a bound of 50 that this check calls green, because that row does not
exist in any tree. The answer to that is not a bigger number, it is the
``complete`` contract — which is why every catalogue uses it.

Traces to issue #995 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the seed YAML lives.
SEED_DATA_DIR = REPO_ROOT / "src/backend/app/migrations/seed_data"

#: Modules scanned for the names of the YAML files they load.
MIGRATIONS_DIR = REPO_ROOT / "src/backend/app/migrations"

#: Frontend source root, against which a catalogue's ``owner`` is resolved.
FRONTEND_SRC = REPO_ROOT / "src/frontend/src"

#: Subdirectories of ``seed_data`` that hold no seed rows. ``schemas/`` carries
#: the JSON-Schema documents the seed files are validated against; they are not
#: catalogue content and must not be counted or reported as orphaned.
NON_SEED_SUBDIRS = ("schemas",)

#: Seed files that carry catalogue rows and that no seeder loads, each with the
#: reason it is not red **yet**. A file listed here is still counted as zero rows
#: and still reported on every run — this defers a decision, it does not hide one.
#:
#: A file not listed here fails the check, which is the point: an orphan is how a
#: catalogue silently ships short, and it makes every count taken from
#: ``seed_data/`` wrong, this check's own included.
#:
#: Removing an entry is the goal, by one of two routes: wire the file into
#: ``app/migrations/seeds/registry.py``, or delete it. Both are product-data
#: decisions, which is exactly why they are not taken as a side effect of a
#: frontend fix.
KNOWN_UNLOADED_SEED_FILES: dict[str, str] = {
    "fertilizers_supplement.yaml": (
        "22 Canna/BioBizz/Hesi/Terra-Aquatica products, unreferenced since #8. Wiring "
        "them in adds 22 rows to every installation's global catalogue and takes the "
        "fertilizer catalogue to 53 — a product-data decision, raised in #995."
    ),
    "nutrient_plans_hydro.yaml": (
        "12 hydro/coco plans, unreferenced since #8. They dose the products in "
        "fertilizers_supplement.yaml by name, so the two files are one decision: "
        "loading these without those would log fertilizer_not_found for every dosage."
    ),
}

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class SeedCatalogueError(RuntimeError):
    """Raised when the check cannot run at all (missing tree, unparsable file)."""


@dataclass(frozen=True)
class Catalogue:
    """One seeded reference catalogue and the list view that renders it.

    Attributes
    ----------
    name:
        Stable identifier used in the report.
    seed_keys:
        Top-level YAML keys carrying this catalogue's rows. Several exist because
        the same collection is fed from a base file and from the ``plant_info``
        files (``families`` + ``new_families``).
    identity:
        Field names forming a row's dedup identity, in the order the seeder
        compares them. The first *present* field of each name is used, so a
        catalogue whose files disagree on the spelling (``name`` here,
        ``common_name`` there) still de-duplicates.
    owner:
        Frontend module, relative to ``src/frontend/src``, that loads the
        catalogue for its list view.
    loader:
        Symbol the owner must reference for the ``complete`` contract. ``None``
        means the owner fetches a bounded page and ``page_size`` applies.
    page_size:
        The bound, when ``loader`` is ``None``. Rows beyond it are unreachable.
    """

    name: str
    seed_keys: tuple[str, ...]
    identity: tuple[str, ...]
    owner: str
    loader: str | None = None
    page_size: int | None = None

    def __post_init__(self) -> None:
        """Reject a registry entry that declares neither contract."""
        if (self.loader is None) == (self.page_size is None):
            raise SeedCatalogueError(
                f"catalogue {self.name!r} must declare exactly one of loader / page_size"
            )


#: The seeded reference catalogues rendered by a list view.
#:
#: Only *global reference data* belongs here — rows that ship with the product
#: and that a fresh installation shows before the user has created anything.
#: Tenant-owned collections (plants, tasks, harvests) are deliberately absent:
#: they start empty, so a seed count says nothing about them, and listing them
#: would make this check report on numbers it cannot see.
CATALOGUES: tuple[Catalogue, ...] = (
    Catalogue(
        name="fertilizers",
        seed_keys=("fertilizers",),
        identity=("product_name", "brand"),
        owner="store/slices/fertilizersSlice.ts",
        loader="fetchAllFertilizers",
    ),
    Catalogue(
        name="nutrient_plans",
        seed_keys=("nutrient_plans",),
        identity=("name",),
        owner="store/slices/nutrientPlansSlice.ts",
        loader="fetchAllNutrientPlans",
    ),
    Catalogue(
        name="botanical_families",
        seed_keys=("families", "new_families"),
        identity=("name",),
        owner="store/slices/botanicalFamiliesSlice.ts",
        loader="listAllBotanicalFamilies",
    ),
    Catalogue(
        name="species",
        seed_keys=("species", "new_species"),
        identity=("scientific_name",),
        owner="store/slices/speciesSlice.ts",
        loader="listAllSpecies",
    ),
    Catalogue(
        name="substrates",
        seed_keys=("substrates",),
        identity=("name_de", "brand"),
        owner="store/slices/substratesSlice.ts",
        loader="listAllSubstrates",
    ),
    Catalogue(
        name="activities",
        seed_keys=("activities",),
        identity=("name",),
        owner="store/slices/activitiesSlice.ts",
        loader="listAllActivities",
    ),
    Catalogue(
        name="ipm_pests",
        seed_keys=("pests",),
        identity=("common_name", "name"),
        owner="store/slices/ipmSlice.ts",
        loader="listAllPests",
    ),
    Catalogue(
        name="ipm_diseases",
        seed_keys=("diseases",),
        identity=("common_name", "name"),
        owner="store/slices/ipmSlice.ts",
        loader="listAllDiseases",
    ),
    Catalogue(
        name="ipm_treatments",
        seed_keys=("treatments",),
        identity=("name",),
        owner="store/slices/ipmSlice.ts",
        loader="listAllTreatments",
    ),
)


@dataclass
class CatalogueResult:
    """What the check measured for one catalogue."""

    catalogue: Catalogue
    rows: int
    #: Seed files that contributed rows, with their per-file row counts.
    sources: list[tuple[str, int]] = field(default_factory=list)
    #: Files declaring rows for this catalogue that no seeder loads and that are
    #: **not** recorded in :data:`KNOWN_UNLOADED_SEED_FILES`. These fail.
    orphans: list[tuple[str, int]] = field(default_factory=list)
    #: Unloaded files that *are* recorded, reported but not failing.
    known_unloaded: list[tuple[str, int]] = field(default_factory=list)
    #: Set when the ``complete`` contract is declared but the owner does not honour it.
    missing_loader: bool = False

    @property
    def orphan_rows(self) -> int:
        """Rows sitting in unrecorded files that nothing loads."""
        return sum(count for _, count in self.orphans)

    @property
    def known_unloaded_rows(self) -> int:
        """Rows sitting in recorded-but-unloaded files."""
        return sum(count for _, count in self.known_unloaded)

    @property
    def failed(self) -> bool:
        """Whether this catalogue fails the check."""
        if self.missing_loader or self.orphans:
            return True
        return self.catalogue.page_size is not None and self.rows > self.catalogue.page_size


# ── Deriving which seed files are actually loaded ────────────────────────────


def loaded_yaml_patterns(migrations_dir: Path) -> set[str]:
    """Collect every ``.yaml`` filename literal appearing in the seeder modules.

    Every string constant ending in ``.yaml`` counts, wherever it appears —
    ``load_yaml("species.yaml")``, a ``YAML_FILES = [...]`` list, or a
    ``glob("plant_info*.yaml")`` pattern. Distinguishing the call shapes would
    buy nothing and would miss the next one; the returned values are treated as
    ``fnmatch`` patterns so the glob resolves like the literals.

    Deliberately generous: an unused ``.yaml`` literal would wrongly mark a file
    as loaded, and that error direction is the safe one — it under-reports
    orphans rather than inventing them.

    Args:
        migrations_dir: Directory holding the seeder modules.

    Returns:
        The patterns.

    Raises:
        SeedCatalogueError: If the directory is missing or a module cannot be parsed.
    """
    if not migrations_dir.is_dir():
        raise SeedCatalogueError(f"migrations directory does not exist: {migrations_dir}")

    patterns: set[str] = set()
    for module in sorted(migrations_dir.rglob("*.py")):
        try:
            tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        except (OSError, SyntaxError) as exc:
            raise SeedCatalogueError(f"cannot parse {module}: {exc}") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.endswith(".yaml"):
                    patterns.add(node.value)
    return patterns


def is_loaded(relative_path: Path, patterns: set[str]) -> bool:
    """Report whether a seed file is named by any seeder.

    Matches on both the path relative to ``seed_data`` and the bare filename,
    because seeders name files without a directory prefix.
    """
    return any(
        fnmatch.fnmatch(str(relative_path), pattern) or fnmatch.fnmatch(relative_path.name, pattern)
        for pattern in patterns
    )


def iter_seed_files(seed_dir: Path) -> list[Path]:
    """List every seed YAML, excluding the non-seed subdirectories.

    Raises:
        SeedCatalogueError: If the seed directory is missing.
    """
    if not seed_dir.is_dir():
        raise SeedCatalogueError(f"seed data directory does not exist: {seed_dir}")
    return sorted(
        path
        for path in seed_dir.rglob("*.yaml")
        if not any(part in NON_SEED_SUBDIRS for part in path.relative_to(seed_dir).parts[:-1])
    )


# ── Counting rows ────────────────────────────────────────────────────────────


def row_identity(row: dict[str, Any], identity: tuple[str, ...]) -> tuple[str, ...]:
    """Build a row's dedup key from the declared identity fields.

    A missing field contributes an empty string rather than dropping the row: a
    row that carries none of them still counts once, and only collapses with
    another equally anonymous row — which is the conservative direction, since
    over-collapsing lowers the count and this check only fails on a *high* one.
    """
    return tuple(str(row.get(name, "")) for name in identity)


def load_seed_document(path: Path) -> dict[str, Any]:
    """Parse one seed file into a mapping (non-mappings yield an empty one).

    Raises:
        SeedCatalogueError: If the file cannot be read or parsed.
    """
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SeedCatalogueError(f"cannot parse {path}: {exc}") from exc
    return document if isinstance(document, dict) else {}


def catalogue_rows(document: dict[str, Any], catalogue: Catalogue) -> list[dict[str, Any]]:
    """Return the rows one seed document contributes to one catalogue."""
    rows: list[dict[str, Any]] = []
    for key in catalogue.seed_keys:
        value = document.get(key)
        if isinstance(value, list):
            rows.extend(entry for entry in value if isinstance(entry, dict))
    return rows


def measure(
    seed_dir: Path,
    migrations_dir: Path,
    frontend_src: Path,
    catalogues: tuple[Catalogue, ...] = CATALOGUES,
) -> list[CatalogueResult]:
    """Measure every registered catalogue against its list view's contract.

    Args:
        seed_dir: ``seed_data`` directory.
        migrations_dir: Directory holding the seeder modules.
        frontend_src: ``src/frontend/src``, for resolving a catalogue's owner.
        catalogues: The registry (injectable for the check's own tests).

    Returns:
        One result per catalogue, in registry order.

    Raises:
        SeedCatalogueError: If a tree is missing or a file cannot be parsed.
    """
    patterns = loaded_yaml_patterns(migrations_dir)
    documents = [(path, load_seed_document(path)) for path in iter_seed_files(seed_dir)]

    results: list[CatalogueResult] = []
    for catalogue in catalogues:
        seen: set[tuple[str, ...]] = set()
        sources: list[tuple[str, int]] = []
        orphans: list[tuple[str, int]] = []
        known_unloaded: list[tuple[str, int]] = []

        for path, document in documents:
            rows = catalogue_rows(document, catalogue)
            if not rows:
                continue
            relative = path.relative_to(seed_dir)
            if is_loaded(relative, patterns):
                sources.append((str(relative), len(rows)))
                seen.update(row_identity(row, catalogue.identity) for row in rows)
            elif str(relative) in KNOWN_UNLOADED_SEED_FILES:
                known_unloaded.append((str(relative), len(rows)))
            else:
                orphans.append((str(relative), len(rows)))

        result = CatalogueResult(
            catalogue=catalogue,
            rows=len(seen),
            sources=sources,
            orphans=orphans,
            known_unloaded=known_unloaded,
        )

        if catalogue.loader is not None:
            owner = frontend_src / catalogue.owner
            if not owner.is_file():
                raise SeedCatalogueError(f"owner module does not exist: {owner}")
            result.missing_loader = catalogue.loader not in owner.read_text(encoding="utf-8")

        results.append(result)
    return results


# ── Reporting ────────────────────────────────────────────────────────────────


def _requests_for(rows: int, page_size: int) -> int:
    """Number of sequential requests a complete load costs at this size."""
    return max(1, -(-rows // page_size))


def _contract(catalogue: Catalogue) -> str:
    """Render a catalogue's contract for the report."""
    if catalogue.loader is not None:
        return f"complete ({catalogue.loader})"
    return f"bounded ({catalogue.page_size})"


def report(results: list[CatalogueResult], list_sources: bool, page_size: int) -> int:
    """Print the measurement and return the process exit code.

    Args:
        results: One entry per catalogue.
        list_sources: Whether to name every seed file counted.
        page_size: Page size assumed when costing a complete load.

    Returns:
        ``EXIT_OK`` when every catalogue holds its contract, ``EXIT_DEFECTS`` otherwise.
    """
    print("Seeded catalogue vs. list-view page size (#995)")
    print()
    print(f"  {'catalogue':<20} {'rows':>6}  {'contract':<34} verdict")
    for result in results:
        catalogue = result.catalogue
        if result.missing_loader:
            verdict = f"FAIL — {catalogue.owner} does not use {catalogue.loader}()"
        elif result.orphans:
            verdict = f"FAIL — {result.orphan_rows} row(s) in an unloaded seed file"
        elif catalogue.page_size is None:
            deferred = (
                f", {result.known_unloaded_rows} not seeded" if result.known_unloaded else ""
            )
            verdict = f"ok — {_requests_for(result.rows, page_size)} request(s){deferred}"
        elif result.rows > catalogue.page_size:
            verdict = f"FAIL — {result.rows - catalogue.page_size} row(s) unreachable"
        else:
            verdict = f"ok — {catalogue.page_size - result.rows} row(s) of headroom"
        print(f"  {catalogue.name:<20} {result.rows:>6}  {_contract(catalogue):<34} {verdict}")
    print()

    if list_sources:
        for result in results:
            for path, count in result.sources:
                print(f"  counted   {result.catalogue.name:<20} {count:>4}  {path}")
        print()

    deferred = [result for result in results if result.known_unloaded]
    if deferred:
        print("Recorded but not loaded — rows that reach no database and no browser:")
        for result in deferred:
            for path, count in result.known_unloaded:
                print(f"  {path}  ({count} row(s), catalogue {result.catalogue.name})")
                print(f"    {KNOWN_UNLOADED_SEED_FILES[path]}")
        print(
            "  Not counted above, and deliberately not red — see "
            "KNOWN_UNLOADED_SEED_FILES.\n  Printed on every run so the number stays a "
            "number somebody reads."
        )
        print()

    failures = [result for result in results if result.failed]
    if not failures:
        print("OK — every seeded catalogue is fully reachable from its list view.")
        print(
            "  A green result is about the *seeded* rows. Tenant-created rows are "
            "invisible here, which is why every catalogue holds the `complete` "
            "contract rather than a bound this check would have to trust."
        )
        return EXIT_OK

    print(f"FAILED — {len(failures)} catalogue(s):\n")
    for result in failures:
        catalogue = result.catalogue
        if result.orphans:
            print(f"  {catalogue.name}: seed rows that no seeder loads")
            for path, count in result.orphans:
                print(f"    {path}  ({count} row(s))")
            print(
                "    These rows reach no database and no browser. Either wire the file "
                "into\n    app/migrations/seeds/registry.py, or delete it — leaving it "
                "in seed_data/\n    makes every count taken from that directory wrong, "
                "this one included."
            )
        if result.missing_loader:
            print(f"  {catalogue.name}: {catalogue.owner} must load the complete catalogue")
            print(
                f"    It is registered as `complete` but does not reference "
                f"{catalogue.loader}().\n    A bounded fetch here does not paginate: the "
                "list view searches and sorts\n    client-side, so the rows past the page "
                "are reported as non-existent."
            )
        if catalogue.page_size is not None and result.rows > catalogue.page_size:
            over = result.rows - catalogue.page_size
            print(
                f"  {catalogue.name}: {result.rows} seeded row(s) against a page of "
                f"{catalogue.page_size}"
            )
            print(
                f"    {over} row(s) cannot be reached from {catalogue.owner}. They are not "
                "merely\n    off-screen — the search is client-side, so it answers \"no "
                "results\" for them.\n    Load the complete catalogue (see "
                "src/frontend/src/api/paginate.ts) rather than\n    raising the bound: the "
                "next row would disappear the same way."
            )
        print()
    return EXIT_DEFECTS


def main(argv: list[str] | None = None) -> int:
    """Run the seeded-catalogue page-size check.

    Returns:
        0 when every catalogue is fully reachable, 1 when one is not, 2 on a
        usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_seed_catalogue_page_size.py",
        description=(
            "Compare the number of seeded rows per reference catalogue against the page "
            "its list view fetches. Both numbers are derived from the tree; nothing here "
            "is a recorded count."
        ),
    )
    parser.add_argument(
        "--seed-dir",
        metavar="PATH",
        help=f"seed data directory (default: {SEED_DATA_DIR.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--migrations-dir",
        metavar="PATH",
        help=f"seeder modules (default: {MIGRATIONS_DIR.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--frontend-src",
        metavar="PATH",
        help=f"frontend source root (default: {FRONTEND_SRC.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        metavar="N",
        help="page size assumed when costing a complete load (default: 200, the backend cap)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_sources",
        help="name every seed file counted, with its row count",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the measurement as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    def resolve(value: str | None, default: Path) -> Path:
        if value is None:
            return default
        path = Path(value)
        return path if path.is_absolute() else REPO_ROOT / path

    try:
        results = measure(
            resolve(args.seed_dir, SEED_DATA_DIR),
            resolve(args.migrations_dir, MIGRATIONS_DIR),
            resolve(args.frontend_src, FRONTEND_SRC),
        )
    except SeedCatalogueError as exc:
        print(f"check_seed_catalogue_page_size: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(
            json.dumps(
                {
                    "catalogues": [
                        {
                            "name": result.catalogue.name,
                            "rows": result.rows,
                            "loader": result.catalogue.loader,
                            "page_size": result.catalogue.page_size,
                            "owner": result.catalogue.owner,
                            "missing_loader": result.missing_loader,
                            "orphan_files": [
                                {"path": path, "rows": count} for path, count in result.orphans
                            ],
                            "sources": [
                                {"path": path, "rows": count} for path, count in result.sources
                            ]
                            if args.list_sources
                            else [],
                            "failed": result.failed,
                        }
                        for result in results
                    ],
                    "failed": sum(1 for result in results if result.failed),
                },
                indent=2,
            )
        )
        # Same rule as the human report, derived from the same predicate, so the
        # two modes cannot disagree about one tree.
        return EXIT_DEFECTS if any(result.failed for result in results) else EXIT_OK

    return report(results, args.list_sources, args.page_size)


if __name__ == "__main__":
    raise SystemExit(main())
