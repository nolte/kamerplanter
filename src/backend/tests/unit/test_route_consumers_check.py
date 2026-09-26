"""Tests for the route-consumer inventory (``scripts/check_route_consumers.py``).

**What is under test.** The reverse of the join
``test_frontend_calls_served_check.py`` covers: not "does every call reach a
route" but "does every route reach a consumer" (#1478, of which #1416 was one
instance). Three things have to hold for the number it prints to mean anything.

*The route operand must not drift from the one already trusted.* This script
walks the mounted app a second time, because it needs the route **object** — the
owning module and the auth gate — and the sibling's :func:`collect_mounted_routes`
returns bare ``(method, path)`` pairs. Two walks of FastAPI's ``_IncludedRouter``
nesting is exactly how a second, quietly different route table gets into a
repository, so :class:`TestTheRouteOperand` asserts the two walks agree on the
real app, set for set. ``include_router`` does not flatten: read ``app.routes``
directly and you get six routes instead of 800, and every number here becomes
fiction — so both operands are size-checked too, an empty side being a broken
scan and never a pass.

*The join must actually discriminate.* A suffix match with no floor matches
everything: ``/{}`` is a suffix of half the route table. :class:`TestTheJoin`
pins the floor from both sides — a three-segment suffix counts, a two-segment one
does not, and a route shorter than three segments is matched by its whole
remainder rather than being made unreachable by its own length.

*The registry must not be able to hide anything silently.* An exemption without a
stated reason is indistinguishable from an oversight, and an exemption nobody
prunes hides the next dead route. :class:`TestTheExemptionRegistry` pins both:
the loader refuses a reasonless entry, and an entry whose operation gained a
consumer is reported as stale rather than left standing.

**The controls are constructed, not pinned to today's tree**, except where the
measurement itself is the point: :func:`test_the_measured_candidate_count` records
800 mounted operations — 797 when #1478 was filed, plus the two write routes
#1461/#1460 added when generation moved off the read path, minus the global
dashboard summary #1853 removed, plus ``POST /users/me/step-up-code`` and
``POST /users/me/step-up/oidc`` (#1815) — and a change
to it should be *noticed*. Everything else runs against miniature inputs, so a
triage decision that legitimately gives a route a consumer does not turn this file
red for the wrong reason.

Traces to #1478 / #1416 (no TC-ID: a source-tree instrument is not a user-facing
case).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import APIRouter, FastAPI

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("check_route_consumers")
sibling = load_repo_script("check_frontend_calls_served")

REPO_ROOT = find_repo_root(Path(__file__).resolve())


def build_app() -> FastAPI:
    """A real app mounted the way the production one is: nested prefixes.

    Built with the real ``include_router`` so the wrappers the walk has to see
    through are real ``_IncludedRouter`` objects rather than a hand-written
    double inventing a shape production never has.
    """
    plants = APIRouter(prefix="/plants")

    @plants.get("/{key}/photos")
    async def list_photos(key: str) -> dict[str, str]:
        return {"key": key}

    @plants.post("/{key}/photos")
    async def add_photo(key: str) -> dict[str, str]:
        return {"key": key}

    tenant = APIRouter(prefix="/t/{tenant_slug}")
    tenant.include_router(plants)

    species = APIRouter(prefix="/species")

    @species.get("")
    async def list_species() -> list[str]:
        return []

    api = APIRouter(prefix="/api/v1")
    api.include_router(tenant)
    api.include_router(species)

    app = FastAPI()
    app.include_router(api)
    return app


def write_surface(root: Path, name: str, body: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(body, encoding="utf-8")


@pytest.fixture
def constructed(tmp_path: Path) -> tuple[list, list]:
    """A mini app plus one consumer surface naming exactly one of its paths.

    ``/plants/{}/photos`` is written down; ``/species`` is not. That asymmetry is
    what makes the positive and the negative control below mean opposite things
    on the *same* run, rather than two runs that could both be wrong.
    """
    write_surface(
        tmp_path / "ui",
        "gallery.ts",
        "const load = () => client.get(`/plants/${key}/photos`);\n",
    )
    surfaces = (("ui", "ui", ("**/*.ts",)),)
    operations = checker.collect_operations(build_app())
    references = checker.collect_references(tmp_path, surfaces)
    return operations, references


class TestTheRouteOperand:
    """The second walk of the mounted app must not drift from the first."""

    def test_it_agrees_with_the_sibling_walk_on_the_real_app(self) -> None:
        """Set for set, on the production app — not on a double.

        The sibling's walk is the one #1339 hardened and the one a required gate
        already runs. If this script's walk ever disagrees with it, one of the
        two is wrong about what the app serves, and the inventory's denominator
        is fiction.
        """
        backend_dir = REPO_ROOT / "src" / "backend"
        app = checker.load_app(backend_dir)

        mine = {(op.method, op.path) for op in checker.collect_operations(app)}
        theirs = {pair for pair in sibling.collect_mounted_routes(app) if pair[1].startswith(checker.API_PREFIX)}

        assert mine, "the walk found no operations — a broken scan, never a pass"
        assert theirs, "the sibling walk found no routes — a broken scan"
        assert mine == theirs

    def test_the_measured_candidate_count(self) -> None:
        """800 mounted ``/api/v1`` operations.

        Pinned deliberately. The candidate *count* moves with every triage
        decision and is not pinned anywhere; the denominator moving is a route
        added or removed, which is worth seeing — and it is exactly what this
        assertion made visible here.

        797 was the figure #1478 was filed on. #1461/#1460 added the two routes
        that took generation off the read path, and nothing else:

        * ``POST /t/{tenant_slug}/ai/daily-tip/refresh``
        * ``POST /t/{tenant_slug}/glossary/term/{slug}/generate``

        #1853 removed ``GET /dashboard/summary``, which read any tenant's
        dashboard from a ``?tenant_key=`` the caller chose.

        +1: ``POST /users/me/step-up-code`` (#1815) — the e-mailed step-up code
        of an account without a local password; consumed by ``requestStepUpCode``
        in ``src/frontend/src/api/endpoints/auth.ts``.

        +1: ``POST /users/me/step-up/oidc`` (#1815) — the fresh OIDC
        re-authentication of a federated account's step-up.
        """
        app = checker.load_app(REPO_ROOT / "src" / "backend")
        assert len(checker.collect_operations(app)) == 800

    def test_it_reads_the_gate_from_the_factory_not_the_closure(self) -> None:
        """Every guard in ``app/common/auth.py`` returns a closure named ``_check``.

        Reading ``__name__`` would label eight different gates identically, which
        makes the Gate column of the report worthless precisely where it matters.
        """
        app = checker.load_app(REPO_ROOT / "src" / "backend")
        labels = {name for op in checker.collect_operations(app) for name in op.gate.split(", ")}

        assert "_check" not in labels
        # The three closure-produced gates. Reading ``__name__`` yields ``_check``
        # for all of them, which the name filter then drops — so the Gate column
        # would silently come out ``-`` on every permission-gated route while the
        # ``_check`` assertion above still held. These are the same expression the
        # rule is about.
        assert {"require_permission", "require_tenant_role", "require_admin_scope"} <= labels


class TestTheJoin:
    """Positive and negative control over one constructed run."""

    def test_a_route_with_a_consumer_counts_one(self, constructed: tuple[list, list]) -> None:
        operations, references = constructed
        joined = checker.find_consumers(operations, references)

        photos = [op for op in operations if op.path.endswith("/plants/{}/photos")]
        assert len(photos) == 2, "the mini app should mount GET and POST there"
        for operation in photos:
            assert len(joined[operation]) == 1, operation.describe()

    def test_a_route_without_a_consumer_counts_zero(self, constructed: tuple[list, list]) -> None:
        operations, references = constructed
        joined = checker.find_consumers(operations, references)

        species = next(op for op in operations if op.path == "/api/v1/species")
        assert joined[species] == []
        findings = checker.find_unconsumed(joined, [])
        assert [f.operation.describe() for f in findings] == ["GET /api/v1/species"]

    def test_a_two_segment_suffix_does_not_count(self) -> None:
        """The floor, asserted from the side that would make the join vacuous.

        Without it ``/{}/photos`` — which is a suffix of a dozen unrelated routes
        — would mark them all consumed, and the check would report a clean tree
        while looking at nothing.
        """
        assert not checker.matches("/api/v1/t/{}/plants/{}/photos", "/{}/photos")
        assert checker.matches("/api/v1/t/{}/plants/{}/photos", "/plants/{}/photos")

    def test_a_short_route_is_matched_by_its_whole_remainder(self) -> None:
        """``/species`` has one segment; the floor must not make it unmatchable."""
        assert checker.matches("/api/v1/species", "/species")
        assert checker.matches("/api/v1/species", "/api/v1/species")
        assert not checker.matches("/api/v1/species", "/cultivars")

    def test_a_reference_longer_than_the_route_does_not_count(self) -> None:
        """A sub-resource path must not mark its parent consumed."""
        assert not checker.matches("/api/v1/species", "/foo/bar/species")


class TestTheExemptionRegistry:
    """The registry must not be able to hide a route silently."""

    def test_the_shipped_registry_loads(self) -> None:
        """It ships empty, and an empty registry is still a valid one."""
        registry = REPO_ROOT / checker.DEFAULT_EXEMPTIONS
        assert registry.is_file()
        assert checker.load_exemptions(registry) == []

    def test_an_exemption_suppresses_its_finding(self, constructed: tuple[list, list], tmp_path: Path) -> None:
        operations, references = constructed
        joined = checker.find_consumers(operations, references)
        assert checker.find_unconsumed(joined, []), "precondition: there is a finding"

        registry = tmp_path / "exemptions.yaml"
        registry.write_text(
            "exemptions:\n"
            "  - method: GET\n"
            "    path: /api/v1/species\n"
            "    reason: consumed by an external catalogue importer\n",
            encoding="utf-8",
        )
        exemptions = checker.load_exemptions(registry)

        assert checker.find_unconsumed(joined, exemptions) == []
        assert checker.stale_exemptions(joined, exemptions) == []

    def test_an_exemption_without_a_reason_is_refused(self, tmp_path: Path) -> None:
        registry = tmp_path / "exemptions.yaml"
        registry.write_text(
            "exemptions:\n  - method: GET\n    path: /api/v1/species\n",
            encoding="utf-8",
        )
        with pytest.raises(checker.RouteConsumerCheckError, match="states no reason"):
            checker.load_exemptions(registry)

    def test_an_exemption_that_gained_a_consumer_is_stale(self, constructed: tuple[list, list], tmp_path: Path) -> None:
        """The half that keeps the registry from outliving the routes it excuses."""
        operations, references = constructed
        joined = checker.find_consumers(operations, references)

        registry = tmp_path / "exemptions.yaml"
        registry.write_text(
            "exemptions:\n"
            "  - method: GET\n"
            "    path: /api/v1/t/{tenant_slug}/plants/{key}/photos\n"
            "    reason: consumed by Home Assistant only\n"
            "  - method: GET\n"
            "    path: /api/v1/gone\n"
            "    reason: route was removed yesterday\n",
            encoding="utf-8",
        )
        exemptions = checker.load_exemptions(registry)

        stale = {(item.method, item.path) for item in checker.stale_exemptions(joined, exemptions)}
        assert stale == {
            ("GET", "/api/v1/t/{}/plants/{}/photos"),
            ("GET", "/api/v1/gone"),
        }


class TestTheExtraction:
    """The literal scan must pick up what the surfaces actually write."""

    def test_both_interpolation_dialects_normalise_alike(self) -> None:
        assert checker._normalise("/plants/${key}/photos") == "/plants/{}/photos"
        assert checker._normalise("/plants/{key}/photos") == "/plants/{}/photos"
        assert checker._normalise("/plants/x/photos?limit=5") == "/plants/x/photos"

    def test_a_non_path_literal_is_dropped(self) -> None:
        assert checker._normalise("plants") is None
        assert checker._normalise("/a path with spaces") is None
        assert checker._normalise("") is None

    def test_a_missing_surface_is_an_error_not_an_empty_scan(self, tmp_path: Path) -> None:
        """A surface that scans nothing would mark the whole tree unconsumed."""
        with pytest.raises(checker.RouteConsumerCheckError, match="not a directory"):
            checker.collect_references(tmp_path, (("ui", "does-not-exist", ("*.ts",)),))

    def test_the_endpoint_surface_is_resolved_by_the_sibling(self) -> None:
        """598 resolved calls — the operand figure #1478 names, reproduced here."""
        references = checker.collect_endpoint_references(REPO_ROOT / checker.DEFAULT_ENDPOINT_DIR)
        assert len(references) >= 500
        assert all(ref.path.startswith(checker.API_PREFIX) for ref in references)
        assert any(ref.path.startswith(checker.TENANT_PREFIX) for ref in references)
