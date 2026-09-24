#!/usr/bin/env python3
"""Refuse a layer break at either end of the business logic (NFR-001).

Two rules, one gate, because they are the same rule seen from two sides:

* **Rule 1 — the API layer does not import ``app.data_access``.** A router
  reaches persistence *through* a service, never past it.
* **Rule 2 — the business logic does not hold or reach a persistence handle.**
  A service or engine reaches persistence *through* a repository, never past it.

Rule 2 exists because #1556 measured only ``_repo._db`` and concluded there were
"only two" breaks left. That grep sees exactly one spelling — reaching *through*
a repository into its private handle — and is blind to the other and larger one:
a service that is *handed* a ``StandardDatabase`` and runs AQL on it directly.
Measured across ``app/domain`` on 2026-09-21 that is four more modules and ~22
more sites. A gate written to the two literal call sites would have certified
the tree clean while the bigger half stood untouched, which is the #948 class
this repository has repaired four times in a week.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_layer_imports.py
    python3 scripts/check_layer_imports.py --list   # name every import, allowed or not
    python3 scripts/check_layer_imports.py --json   # machine-readable

**What it enforces.** NFR-001's layer order: Presentation → API → Business Logic
→ Data Access → Persistence. A router reaches persistence *through a service*,
never past it. When it reaches around, three things stop holding at once — the
tenant predicate that the service anchors on its parent entity, the domain
validation that turns bad input into 422 instead of 500, and the ability to test
the endpoint against a fake. Cluster B of the 2026-08-08 issue-pattern audit is
seven issues of exactly that (#1020, #1019, #1018, #997, #991, #968, #456).

**Why a gate and not review.** The import is one line at the top of a file
nobody re-reads, and it is *convenient*: the alternative is a service method
that does not exist yet. Every review that let one through was a review that had
no reason to look at line 18. The audit found ≥11 routers past the boundary and
no import-linter, no ruff ``TID`` rule, nothing that measured it.

**The baseline is an allowlist, not a number.** ``check_schema_examples.py``
counts, because its debt is one homogeneous population where any member is as
good as any other to pay off. This debt is not: each of these imports is a
specific missing service method, and a count would let a reviewer clear an easy
one while a new hard one lands in the same pull request. Every entry below names
the file, the module, and why it is still there.

**An allowlist entry that no longer matches is an error**, the same rule
``seed_steckbrief_consistency.ALLOWED_DISCREPANCIES`` carries. A stale entry is
a hole nobody opened deliberately: it silently re-permits the import the moment
somebody re-adds it. Removing the import means removing its entry, in the same
change.

**The escape hatch is the allowlist**, deliberately, and not an in-line comment
marker like the sibling checks use. A hatch that can be typed at the call site
is right where the reason is local (this ``date.today()`` is a log file name);
here the reason is architectural and belongs where all of them can be read at
once. Adding an entry is a visible edit to this file, which is the review that
the import itself never got.

**Rule 2 has no allowlist, and that is the point.** It carried one while four
modules still held a handle (``favorites_service``, ``starter_kit_service``,
``onboarding_service``, ``calendar_aggregation_engine``); #1638 moved every one of
them behind a repository and then removed the entry mechanism itself. An empty
allowlist is still a door: a crossing could be *recorded* instead of *fixed*, and
the gate would pass. Without the mechanism the only way to satisfy rule 2 is to
not cross. Reinstating an allowlist is therefore a visible change to this file's
structure, not a one-entry edit.

Both rules are reported by the same process with the same exit codes.

Standard library only, no application import, no running stack.

Traces to the 2026-08-08 issue-pattern audit, measure P1.3 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The layer that may not reach past the business logic.
DEFAULT_SCAN_ROOT = "src/backend/app/api"

#: The package it may not reach into.
FORBIDDEN_PACKAGE = "app.data_access"

#: The business-logic layer that may not hold or reach a persistence handle.
DEFAULT_HANDLE_SCAN_ROOT = "src/backend/app/domain"

#: The persistence driver. Business logic that imports it is typing, catching or
#: constructing something only the data-access layer should know exists.
DRIVER_PACKAGE = "arango"

#: The private attribute every ``BaseArangoRepository`` stores its handle under.
#: Business logic naming it is either holding one (``self._db = db``) or reaching
#: through a repository to borrow one (``self._user_repo._db``) — two spellings of
#: the same break, and only the second is the one #1556's grep could see.
HANDLE_ATTRIBUTE = "_db"

#: The driver's query entry point. Detected *as well as* the handle attribute,
#: because a module that stored the handle under any other name — ``self.db``,
#: a local, a ``getattr`` — still has to reach ``.aql`` to use it. Asking only
#: "is the attribute called ``_db``" would be the #1556 mistake one level down:
#: a rule shaped like the offenders that happen to exist today.
QUERY_ATTRIBUTE = "aql"

#: One marker for every way of holding or reaching a handle. Deliberately NOT
#: one marker per spelling: while rule 2 still had an allowlist, one keyed on the
#: spelling would have gone green the moment a recorded module switched from
#: ``self._db`` to ``getattr``. Kept as one marker now that the allowlist is gone
#: (#1638), so a finding reads the same whichever spelling produced it.
HANDLE_MARKER = "handle"

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class LayerImportCheckError(Exception):
    """A usage or environment problem — not a finding about the code."""


@dataclass(frozen=True)
class AllowedImport:
    """One recorded, deliberate crossing of the API → data-access boundary.

    Attributes:
        path: Repository-relative path of the importing module.
        module: The imported ``app.data_access.*`` module.
        reason: Why it is still there, and what would remove it.
    """

    path: str
    module: str
    reason: str

    @property
    def identity(self) -> tuple[str, str]:
        return (self.path, self.module)


# --------------------------------------------------------------------------- #
# The recorded baseline
# --------------------------------------------------------------------------- #
#
# Measured on 2026-08-08: 22 imports across 18 modules; #1019 removed the
# admin/platform/router.py crossing (family 2), leaving 21 across 17. Every entry is debt, not
# an exemption on the merits — the fix in each case is a service method that
# does not exist yet. Adding an entry needs a reviewer to agree in this file;
# removing the import means deleting its entry in the same change, because an
# entry that matches nothing fails this check (see the module docstring).
#
# Four rough families, in descending order of how much they actually cost:
#
#   1. A repository constructed inside a router and driven directly. The tenant
#      predicate then lives in the router, or nowhere — the #1019/#997 shape.
#   2. `app.data_access.arango.collections` imported for raw AQL in the router.
#      Same problem, one level lower.
#   3. An *external* adapter (inference service, knowledge service, weather,
#      Home Assistant) called from the router. Cheaper: no tenant predicate is
#      at stake and the adapter is already an interface. Still the wrong layer —
#      the endpoint cannot be tested without stubbing HTTP.
#   4. A constant table (`WEATHER_ATTRIBUTIONS`) that is data, not access. The
#      cheapest of all to move, and the least urgent.
#
ALLOWED_IMPORTS: tuple[AllowedImport, ...] = (
    # -- family 1: repositories constructed and driven inside a router -------- #
    AllowedImport(
        path="src/backend/app/api/v1/admin/oidc_providers/router.py",
        module="app.data_access.arango.oidc_config_repository",
        reason=(
            "Admin CRUD over OIDC provider configuration goes straight to the "
            "repository; there is no OidcConfigService. Global resource, so no "
            "tenant predicate is at stake — this is the cheap half of family 1."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/auth/router.py",
        module="app.data_access.arango.oidc_config_repository",
        reason=(
            "The login route reads the enabled providers to render the buttons. "
            "Same missing service as the admin router above; both go when it exists."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/botanical_families/router.py",
        module="app.data_access.arango.botanical_family_repository",
        reason=(
            "Global catalogue read with no service in front of it. No tenant "
            "predicate at stake; the endpoint is untestable without ArangoDB."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/crop_rotation/router.py",
        module="app.data_access.arango.graph_repository",
        reason=(
            "Rotation reads traverse the named graph directly from the router "
            "(#1019 family). The traversal is the domain logic and belongs in an "
            "engine; moving it is a rewrite, not an import change."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/family_relationships/router.py",
        module="app.data_access.arango.graph_repository",
        reason="Same graph traversal as crop_rotation/router.py; the two move together.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/glossar/admin_router.py",
        module="app.data_access.arango.glossary_repository",
        reason=(
            "Glossary admin CRUD with no GlossaryService. Global resource, so the "
            "tenant predicate is not at stake, but the router owns persistence."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/ki_assistent/deps.py",
        module="app.data_access.arango.tenant_repository",
        reason=(
            "A FastAPI dependency assembling the assistant's tenant context. "
            "Wiring code, one layer too low: the composition root "
            "(app/common/dependencies.py) is where a repository is constructed."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/overwintering_profiles/tenant_router.py",
        module="app.data_access.arango.plant_instance_repository",
        reason=(
            "The tenant-scoped overwintering router resolves plants itself "
            "(#997 family). This is the expensive kind: the tenant predicate is "
            "assembled in the router, so a missed FILTER here is a cross-tenant read."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/overwintering_profiles/tenant_router.py",
        module="app.data_access.arango.site_repository",
        reason="Second of three repositories the same router drives; see the entry above.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/overwintering_profiles/tenant_router.py",
        module="app.data_access.arango.species_repository",
        reason="Third of three repositories the same router drives; see the entry above.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/privacy/router.py",
        module="app.data_access.arango.mcp_repository",
        reason=(
            "The DSGVO self-service route reads the MCP audit trail directly. "
            "PrivacyService exists — this call was simply not routed through it."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/species/router.py",
        module="app.data_access.arango.botanical_family_repository",
        reason=(
            "Species creation resolves the botanical family in the router instead "
            "of in SpeciesService, which exists and is used beside it."
        ),
    ),
    # -- family 2: raw collection names for AQL written in the router --------- #
    #
    # Emptied by #1019: ``admin/platform/router.py`` was the sole member. Its
    # writes (membership add/remove/role, the ``delete_user`` cascade) now route
    # through ``TenantService.admin_*_membership`` / ``UserService`` and its reads
    # (stats, tenant/user/member listings) through the service+repository layer,
    # so the router no longer imports ``app.data_access.arango.collections`` at
    # all. The family header stays as a placeholder for the shape; add a new
    # member only if a router starts writing raw AQL again (which is what this
    # gate exists to refuse).
    # -- family 3: external adapters called from a router --------------------- #
    AllowedImport(
        path="src/backend/app/api/v1/admin/pests/router.py",
        module="app.data_access.external.pest_inference_client",
        reason=(
            "The pest moderation screen calls the inference client directly. No "
            "tenant predicate at stake; the cost is that the endpoint cannot be "
            "tested without stubbing HTTP."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/admin/recognition/router.py",
        module="app.data_access.external.inference_service_client",
        reason="Recognition admin screen calls the inference service directly; family 3.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/admin/reference_images/router.py",
        module="app.data_access.external.inference_service_client",
        reason="Reference-image curation calls the inference service directly; family 3.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/species/router.py",
        module="app.data_access.external.inference_service_client",
        reason="Species thumbnails call the inference service directly; family 3.",
    ),
    AllowedImport(
        path="src/backend/app/api/v1/admin/settings/router.py",
        module="app.data_access.storage.registry",
        reason=(
            "The 'test this storage configuration' button builds a throwaway "
            "storage adapter. The action is inherently about the adapter, but the "
            "construction belongs behind a service method."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/admin/settings/router.py",
        module="app.data_access.external.ha_notification_channel",
        reason=(
            "The 'send a test notification' button builds the Home Assistant "
            "channel in the router, inside the handler body. Same shape as the "
            "storage test above."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/knowledge/router.py",
        module="app.data_access.external.knowledge_service_client",
        reason="RAG queries call the knowledge service client directly; family 3.",
    ),
    # -- family 4: a constant table that is data, not access ------------------ #
    AllowedImport(
        path="src/backend/app/api/v1/admin/weather_providers/router.py",
        module="app.data_access.external.weather_attributions",
        reason=(
            "WEATHER_ATTRIBUTIONS is a static licence-attribution table that "
            "happens to live under data_access. Not a boundary crossing in "
            "substance; the fix is to move the table, not the call."
        ),
    ),
    AllowedImport(
        path="src/backend/app/api/v1/tenant_scoped/weather/tenant_router.py",
        module="app.data_access.external.weather_attributions",
        reason="Second reader of the same constant table; see the entry above.",
    ),
)


@dataclass(frozen=True)
class HandleSite:
    """One persistence-handle crossing found in the business-logic layer."""

    path: Path
    line: int
    marker: str

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)

    @property
    def identity(self) -> tuple[str, str]:
        return (self.relative(), self.marker)


def _is_driver(dotted: str) -> bool:
    """True for the driver package itself and anything below it."""
    return dotted == DRIVER_PACKAGE or dotted.startswith(f"{DRIVER_PACKAGE}.")


def _is_handle_node(node: ast.AST) -> bool:
    """True for any of the three ways business logic reaches a persistence handle.

    ``self._db`` / ``repo._db`` (the attribute), ``getattr(repo, "_db")`` (the
    string), and ``x.aql`` (the handle stored under some other name and used
    anyway). One predicate rather than three markers — see :data:`HANDLE_MARKER`.
    """
    if isinstance(node, ast.Attribute):
        return node.attr in {HANDLE_ATTRIBUTE, QUERY_ATTRIBUTE}
    return isinstance(node, ast.Constant) and node.value == HANDLE_ATTRIBUTE


def scan_file_for_handle(path: Path) -> list[HandleSite]:
    """Find every persistence-handle crossing in one business-logic module.

    Two detections, deliberately both:

    * an ``arango`` import, in either spelling — the module holds or types a
      handle of its own;
    * a handle, reported as the single ``handle`` marker and detected three ways:
      an attribute named ``_db`` (``self._db = db``, ``self._user_repo._db``), the
      string ``"_db"`` (the ``getattr`` escape), and an attribute named ``aql``
      (the module stored the handle under some other name and still has to reach
      the driver's query entry point to use it).

    The second is what makes the rule a rule about the CLASS rather than about
    ``_repo._db``. Collapsing its three detections into one marker is deliberate:
    a per-spelling marker would let a recorded module change spelling and pass.

    One site per (module, marker); the earliest line is reported, because the
    question a reviewer asks is "does this module cross at all", not "how often".
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LayerImportCheckError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise LayerImportCheckError(f"cannot parse {path}: {exc}") from exc

    earliest: dict[str, int] = {}

    def record(marker: str, line: int) -> None:
        if marker not in earliest or line < earliest[marker]:
            earliest[marker] = line

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_driver(alias.name):
                    record(f"import:{alias.name}", node.lineno)
        elif isinstance(node, ast.ImportFrom):
            # A relative import cannot reach the third-party driver, so level>0
            # is never the driver and is skipped rather than resolved.
            if not node.level and node.module and _is_driver(node.module):
                record(f"import:{node.module}", node.lineno)
        elif _is_handle_node(node):
            record(HANDLE_MARKER, node.lineno)

    return [HandleSite(path=path, line=line, marker=marker) for marker, line in sorted(earliest.items())]


def collect_handles(scan_root: Path) -> list[HandleSite]:
    """Every persistence-handle crossing below *scan_root*, allowed or not."""
    if not scan_root.exists():
        raise LayerImportCheckError(f"scan root does not exist: {scan_root}")
    sites: list[HandleSite] = []
    for path in sorted(scan_root.rglob("*.py")):
        sites.extend(scan_file_for_handle(path))
    return sites


@dataclass(frozen=True)
class ImportSite:
    """One ``app.data_access`` import found in the API layer."""

    path: Path
    line: int
    module: str
    names: tuple[str, ...]

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)

    @property
    def identity(self) -> tuple[str, str]:
        return (self.relative(), self.module)


def _is_forbidden(dotted: str) -> bool:
    """True for ``app.data_access`` itself and anything below it."""
    return dotted == FORBIDDEN_PACKAGE or dotted.startswith(f"{FORBIDDEN_PACKAGE}.")


def scan_file(path: Path) -> list[ImportSite]:
    """Find every data-access import in one source file.

    Both spellings are read: ``import app.data_access.x`` and
    ``from app.data_access.x import Y``. A *relative* import cannot reach
    ``app.data_access`` from inside ``app.api`` without escaping the package
    (``from ....data_access import x``), which nothing in this tree does; the
    resolution is performed anyway so the check does not depend on that staying
    true.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LayerImportCheckError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise LayerImportCheckError(f"cannot parse {path}: {exc}") from exc

    dotted_self = _dotted_module_name(path)
    sites: list[ImportSite] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_forbidden(alias.name):
                    sites.append(ImportSite(path=path, line=node.lineno, module=alias.name, names=()))
        elif isinstance(node, ast.ImportFrom):
            origin = _resolve_relative(dotted_self, node.module, node.level) if node.level else (node.module or "")
            if _is_forbidden(origin):
                sites.append(
                    ImportSite(
                        path=path,
                        line=node.lineno,
                        module=origin,
                        names=tuple(alias.name for alias in node.names),
                    )
                )
    return sorted(sites, key=lambda site: (site.line, site.module))


def _dotted_module_name(path: Path) -> str:
    """Derive the dotted import name of *path* by walking up its packages."""
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").is_file():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts))


def _resolve_relative(importer: str, module: str | None, level: int) -> str:
    """Resolve a relative import against the importing module's dotted name."""
    base = importer.split(".")
    trimmed = base[: max(len(base) - level, 0)]
    return ".".join([*trimmed, module]) if module else ".".join(trimmed)


def collect(scan_root: Path) -> list[ImportSite]:
    """Every data-access import below *scan_root*, allowed or not."""
    if not scan_root.exists():
        raise LayerImportCheckError(f"scan root does not exist: {scan_root}")
    sites: list[ImportSite] = []
    for path in sorted(scan_root.rglob("*.py")):
        sites.extend(scan_file(path))
    return sites


def classify(
    sites: list[ImportSite], allowlist: tuple[AllowedImport, ...] | None = None
) -> tuple[list[ImportSite], list[AllowedImport]]:
    """Split *sites* into new violations, and name the obsolete allowlist entries.

    Args:
        sites: The imports found in the scanned tree.
        allowlist: The recorded crossings; :data:`ALLOWED_IMPORTS` when omitted.
            Resolved here rather than as a default *argument* value, which
            Python would bind once at import time — a test substituting the
            module constant would then be judging the real allowlist while
            believing it had replaced it.

    Returns:
        ``(violations, obsolete)`` — imports with no allowlist entry, and
        allowlist entries no import matches any more.
    """
    entries = ALLOWED_IMPORTS if allowlist is None else allowlist
    allowed = {entry.identity: entry for entry in entries}
    matched: set[tuple[str, str]] = set()
    violations: list[ImportSite] = []
    for site in sites:
        if site.identity in allowed:
            matched.add(site.identity)
        else:
            violations.append(site)
    obsolete = [entry for entry in entries if entry.identity not in matched]
    return violations, obsolete


def report(
    sites: list[ImportSite],
    violations: list[ImportSite],
    obsolete: list[AllowedImport],
    *,
    list_all: bool,
    as_json: bool,
    handle_sites: list[HandleSite] | None = None,
) -> int:
    """Print the outcome of both rules and return the process exit code.

    Every handle site is a violation: rule 2 has no allowlist (#1638).
    """
    handle_violations = handle_sites or []
    if as_json:
        print(
            json.dumps(
                {
                    "imports": len(sites),
                    "allowlisted": len(sites) - len(violations),
                    "violations": [
                        {
                            "file": site.relative(),
                            "line": site.line,
                            "module": site.module,
                            "names": list(site.names),
                        }
                        for site in violations
                    ],
                    "obsolete_allowlist": [{"file": entry.path, "module": entry.module} for entry in obsolete],
                    "handle_violations": [
                        {"file": site.relative(), "line": site.line, "marker": site.marker}
                        for site in handle_violations
                    ],
                },
                indent=2,
            )
        )
        bad = violations or obsolete or handle_violations
        return EXIT_DEFECTS if bad else EXIT_OK

    exit_code = EXIT_OK

    if violations:
        exit_code = EXIT_DEFECTS
        print(f"check_layer_imports: {len(violations)} API module(s) import the data-access layer\n")
        for site in violations:
            names = f" ({', '.join(site.names)})" if site.names else ""
            print(f"  {site.relative()}:{site.line}: {site.module}{names}")
        print(
            "\nNFR-001: the API layer talks to the business logic, and the business logic\n"
            "owns persistence. A router that constructs a repository also owns the tenant\n"
            "predicate — and that is where cross-tenant reads come from (#1019, #997).\n"
            "\n"
            "Move the call behind a service method, or — if the crossing is deliberate and\n"
            "a reviewer agrees — record it in ALLOWED_IMPORTS in\n"
            "scripts/check_layer_imports.py with a reason naming what would remove it."
        )

    if obsolete:
        exit_code = EXIT_DEFECTS
        if violations:
            print()
        print(f"check_layer_imports: {len(obsolete)} allowlist entr(y/ies) match no import any more\n")
        for entry in obsolete:
            print(f"  {entry.path}: {entry.module}")
        print(
            "\nThe import is gone — delete the entry too. An allowlist entry that matches\n"
            "nothing is a hole nobody opened on purpose: it re-permits the import silently\n"
            "the moment somebody adds it back (same rule as\n"
            "seed_steckbrief_consistency.ALLOWED_DISCREPANCIES)."
        )

    if handle_violations:
        if exit_code == EXIT_DEFECTS:
            print()
        exit_code = EXIT_DEFECTS
        print(
            f"check_layer_imports: {len(handle_violations)} business-logic module(s) hold or "
            "reach a persistence handle\n"
        )
        for site in handle_violations:
            print(f"  {site.relative()}:{site.line}: {site.marker}")
        print(
            "\nNFR-001: Business Logic → Data Access → Persistence. A service or engine\n"
            "reaches the database THROUGH a repository. `import:<module>` means it imports\n"
            "the `arango` driver. `handle` means it holds or reaches one — an attribute\n"
            'named `_db`, the string "_db" behind a getattr, or a reach for `.aql` under\n'
            "any other name. All three are one finding on purpose, so changing spelling\n"
            "does not clear it.\n"
            "\n"
            "Move the query behind a repository method reached through an interface under\n"
            "app/domain/interfaces/, and inject the repository via app/common/dependencies.py.\n"
            "There is no allowlist for this rule (#1638): a crossing cannot be recorded,\n"
            "only removed."
        )

    if exit_code == EXIT_OK:
        print(
            f"check_layer_imports: OK — {len(sites)} recorded data-access import(s) in the API "
            "layer, no new ones, and no persistence handle in the business logic."
        )
        if list_all:
            for site in sites:
                print(f"  {site.relative()}:{site.line}: {site.module}")

    return exit_code


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every data-access import in the API layer is recorded and every
        recorded one still exists, 1 otherwise, 2 on a usage error.
    """
    parser = argparse.ArgumentParser(
        prog="check_layer_imports.py",
        description=(
            "Refuse a new app.data_access import under app/api, and a new persistence "
            "handle under app/domain (NFR-001). The existing crossings are recorded in "
            "ALLOWED_IMPORTS; an entry that matches nothing is an error too. Rule 2 has no "
            "allowlist."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the API package to scan for rule 1 (default: {DEFAULT_SCAN_ROOT})",
    )
    parser.add_argument(
        "--handle-scan-root",
        metavar="PATH",
        default=None,
        help=f"the business-logic package to scan for rule 2 (default: {DEFAULT_HANDLE_SCAN_ROOT})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every recorded import when the check passes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    def _root(raw: str) -> Path:
        return Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw

    scan_root = _root(args.scan_root or DEFAULT_SCAN_ROOT)
    handle_scan_root = _root(args.handle_scan_root or DEFAULT_HANDLE_SCAN_ROOT)

    try:
        sites = collect(scan_root)
        handle_sites = collect_handles(handle_scan_root)
    except LayerImportCheckError as exc:
        print(f"check_layer_imports: {exc}", file=sys.stderr)
        return EXIT_USAGE

    violations, obsolete = classify(sites)
    return report(
        sites,
        violations,
        obsolete,
        list_all=args.list_all,
        as_json=args.json,
        handle_sites=handle_sites,
    )


if __name__ == "__main__":
    raise SystemExit(main())
