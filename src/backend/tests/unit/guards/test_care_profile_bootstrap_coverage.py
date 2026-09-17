"""#1444 — every path that creates a plant must reach the care-profile bootstrap.

REQ-022 reminders exist only for a plant that has a stored ``CareProfile``: the
nightly generator iterates stored profiles, so a plant without one is not skipped,
it is absent from the run. Until #1440 the profile appeared as a side effect of
somebody *reading* the care dashboard; that write was removed (#1422, a viewer
must not persist on a GET) and replaced by a bootstrap on the creation paths.

"The creation paths" is the part that drifts. The bootstrap shipped on
``PlantInstanceService.create_plant`` and immediately missed two siblings —
``PlantingRunService.create_plants`` (a run of forty plants, none of which would
ever have received a reminder) and ``_spawn_clonal_pup`` — both found by review
rather than by a check. That is the #948 shape this repository keeps paying for:
a guard that is opt-in at the call site drifts between siblings.

So this guard ENUMERATES rather than listing. It parses ``app/``, finds every
function that creates a ``PlantInstance`` row, computes which functions reach the
bootstrap (directly or through a call), and requires the first set to be contained
in the second. A new creation path reddens it on the commit that adds it.

**The scanner is itself under test.** The failure class here is not "the guard is
wrong", it is "the guard's *pattern* does not know a spelling" — a sweep that
looks complete and misses ``post(BASE, payload)`` because its regex wanted a
string literal. Each detector is therefore driven from synthetic source in both
directions, and the real-tree assertions carry floors: a scanner that suddenly
finds nothing would otherwise be green.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Directories under ``app/`` whose ``PlantInstance(...)`` calls are HYDRATION, not
#: creation: a repository turning a stored document back into a model
#: (``PlantInstance(**doc)``) has created no row. Scanning them would report every
#: read path as an unbootstrapped creation site and the guard would be abandoned as
#: noise — the useful failure mode for a guard is a small true positive, never a
#: large false one.
_HYDRATION_DIRS = ("data_access", "domain/models")

#: What counts as "this function creates a plant row".
#:
#: Two detectors, not one, because the two known shapes do not share a spelling:
#: ``PlantingRunService.create_plants`` builds the model and persists it in the same
#: function, while a future import path could take already-built models and only
#: persist them. A single detector would know one of those.
_MODEL_FACTORIES = ("model_validate", "model_construct", "model_copy")

#: Argument names that mean "a plant row is being written" when passed to a
#: ``.create``/``.insert``. Deliberately generous: a false positive here costs a
#: line in an allowlist, a false negative costs a plant its reminders forever.
_PLANTISH_ARGS = frozenset({"plant", "pup", "instance", "plant_instance", "new_plant", "created_plant", "child"})

#: The bootstrap and its aliases. ``get_or_create_profile`` is included because it
#: is what the hook ultimately calls: a path that calls it directly with
#: ``may_create=True`` has bootstrapped, whatever it names the step.
_BOOTSTRAP_CALLS = frozenset(
    {
        "_bootstrap_care_profile_for",
        "_bootstrap_care_profile",
        "_care_profile_bootstrap",
        "care_profile_bootstrap",
        "get_or_create_profile",
    }
)


def _module_files() -> list[Path]:
    files = []
    for path in sorted(_APP.rglob("*.py")):
        rel = path.relative_to(_APP).as_posix()
        if any(rel.startswith(f"{d}/") for d in _HYDRATION_DIRS):
            continue
        files.append(path)
    return files


def _called_names(node: ast.AST) -> set[str]:
    """Every simple name called anywhere inside ``node``.

    ``self._bootstrap_care_profile_for(x)``, ``bootstrap(x)`` and
    ``service.create_plant(p)`` all reduce to the trailing name: the scan is
    name-based on purpose, because resolving receivers would need the type
    information this repository does not carry into a test, and an unresolved
    receiver is how a real call site gets silently dropped.
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _creates_a_plant(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        # D1 — the model is constructed: `PlantInstance(...)`,
        # `PlantInstance.model_validate(...)`.
        if isinstance(func, ast.Name) and func.id == "PlantInstance":
            return True
        if isinstance(func, ast.Attribute):
            value = func.value
            if func.attr in _MODEL_FACTORIES and isinstance(value, ast.Name) and value.id == "PlantInstance":
                return True
            # D2 — a plant-shaped value is persisted: `self._plant_repo.create(plant)`,
            # `repo.insert(pup)`, `service.create_plant(plant)`.
            if func.attr in ("create", "create_plant", "insert"):
                args = child.args
                if args and isinstance(args[0], ast.Name) and args[0].id in _PLANTISH_ARGS:
                    return True
    return False


def _functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node


def scan_source(source: str, *, label: str = "<memory>") -> tuple[dict[str, dict], set[str]]:
    """Return ``(creation_sites, direct_bootstrappers)`` for one module.

    A creation site is keyed by ``label::function`` — qualified, because two modules
    may hold a function of the same name and an unqualified key would let one
    module's bootstrap answer for the other's.
    """
    tree = ast.parse(source)
    creation_sites: dict[str, dict] = {}
    direct: set[str] = set()
    for func in _functions(tree):
        qualified = f"{label}::{func.name}"
        called = _called_names(func)
        if called & _BOOTSTRAP_CALLS:
            direct.add(qualified)
        if _creates_a_plant(func):
            creation_sites[qualified] = {
                "where": f"{label}:{func.lineno}",
                "name": func.name,
                "calls": called,
            }
    return creation_sites, direct


def scan_tree() -> tuple[dict[str, dict], set[str]]:
    """Scan ``app/`` and return ``(creation_sites, bootstrapped)``.

    ``bootstrapped`` spreads along **creation sites only**, and that restriction is
    the whole difficulty of this scan. The obvious version — "a function that calls
    a bootstrapper is one" over every function in ``app/`` — closes over 201 names
    on this tree, among them ``run``, ``main``, ``execute``, ``up`` and ``upgrade``.
    ``upgrade`` is the entry point of every migration in
    ``app/migrations/versions/``: under that rule a migration that created plants
    without a profile would have been declared covered by an unrelated namesake, and
    a migration is one of the paths this guard exists to watch.

    So delegation is what propagates: a function passes when it bootstraps itself,
    or when it hands the creation to another creation site that passes — which is
    how the REST router and the onboarding wizard pass through
    ``PlantInstanceService.create_plant``. A function that merely shares a name with
    something unrelated inherits nothing.
    """
    creation_sites: dict[str, dict] = {}
    direct: set[str] = set()
    for path in _module_files():
        label = path.relative_to(_APP.parent).as_posix()
        sites, module_direct = scan_source(path.read_text(encoding="utf-8"), label=label)
        creation_sites.update(sites)
        direct |= module_direct

    bootstrapped = {key for key in creation_sites if key in direct}
    changed = True
    while changed:
        changed = False
        covered_names = {creation_sites[key]["name"] for key in bootstrapped}
        for key, site in creation_sites.items():
            if key not in bootstrapped and site["calls"] & covered_names:
                bootstrapped.add(key)
                changed = True
    return creation_sites, bootstrapped


# ── The guard ────────────────────────────────────────────────────────────────


class TestEveryCreationPathBootstrapsTheCareProfile:
    def test_no_plant_is_created_without_a_care_profile(self) -> None:
        creation_sites, bootstrapped = scan_tree()

        unbootstrapped = {key: site["where"] for key, site in creation_sites.items() if key not in bootstrapped}

        assert not unbootstrapped, (
            "these functions create a PlantInstance without reaching the care-profile "
            f"bootstrap, so the plants they create get no REQ-022 reminder ever: {unbootstrapped}. "
            "Call `_bootstrap_care_profile_for(created)` (or route through a function that "
            "does) — see #1444."
        )

    @pytest.mark.parametrize(
        "function_name",
        [
            # The three real writers of a `plant_instances` row, measured 2026-09-17
            # (`plant_instance_service.create_plant` / `_spawn_pup`,
            # `planting_run_service.create_plants`), plus the wizard that reaches one
            # of them. A floor, not a list: if the scan stops finding these it has
            # stopped finding anything, and the assertion above would pass over a tree
            # full of unbootstrapped paths.
            "create_plant",
            "create_plants",
            "_spawn_pup",
            "_create_plants",
        ],
    )
    def test_the_scan_still_finds_the_known_creation_paths(self, function_name: str) -> None:
        creation_sites, _bootstrapped = scan_tree()

        assert function_name in {site["name"] for site in creation_sites.values()}

    def test_the_scan_reads_more_than_a_handful_of_modules(self) -> None:
        """A `rglob` that silently matched nothing — a moved `app/`, a renamed
        directory — would make every assertion here vacuous."""
        assert len(_module_files()) > 100


# ── The scanner, driven from synthetic source ────────────────────────────────


_BOOTSTRAPPED = """
class Service:
    def create_plant(self, data):
        plant = PlantInstance(**data)
        created = self._repo.create(plant)
        self._bootstrap_care_profile_for(created)
        return created
"""

_UNBOOTSTRAPPED = """
class Service:
    def import_plant(self, data):
        plant = PlantInstance(**data)
        return self._repo.create(plant)
"""

_PERSIST_ONLY = """
class Service:
    def store(self, plant):
        return self._plant_repo.create(plant)
"""

_HYDRATION = """
class Repo:
    def get(self, key):
        doc = self._db.get(key)
        return PlantInstance(**doc)
"""

_DELEGATING = """
class Wizard:
    def seed(self, service, data):
        plant = PlantInstance(**data)
        return service.create_plant(plant)
"""

#: A bootstrapping function that happens to be called `upgrade` — the name every
#: migration in `app/migrations/versions/` uses for its entry point.
_BOOTSTRAPPED_UPGRADE = (
    _BOOTSTRAPPED
    + """
class Other:
    def upgrade(self, data):
        plant = PlantInstance(**data)
        created = self._repo.create(plant)
        self._bootstrap_care_profile_for(created)
"""
)

_MIGRATION_CREATING_PLANTS = """
class Migration:
    def upgrade(self, db):
        plant = PlantInstance(instance_id="m1")
        db.plants.insert(plant)
"""


def _names(sites: dict[str, dict]) -> set[str]:
    return {site["name"] for site in sites.values()}


def _scan_fake_tree(monkeypatch, tmp_path, modules: dict[str, str]) -> tuple[dict[str, dict], set[str]]:
    """Run the REAL ``scan_tree`` over a throwaway ``app/`` made of ``modules``.

    Driving the actual tree walk rather than re-assembling its result by hand: the
    closure is what these cases are about, and a hand-assembled closure would be the
    test agreeing with itself.
    """
    app = tmp_path / "app"
    app.mkdir()
    for name, source in modules.items():
        (app / name).write_text(source, encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "_APP", app)
    return scan_tree()


class TestTheScannerItself:
    """Both directions for each detector. A detector that fired on everything would
    satisfy the positive cases alone, and one that fired on nothing would satisfy
    the guard above."""

    def test_a_constructed_and_persisted_plant_is_a_creation_site(self) -> None:
        sites, _direct = scan_source(_UNBOOTSTRAPPED)

        assert _names(sites) == {"import_plant"}

    def test_persisting_a_plant_built_elsewhere_is_a_creation_site(self) -> None:
        """The shape a future import path would have: the model arrives ready-made
        and only the write happens here. A construction-only detector misses it."""
        sites, _direct = scan_source(_PERSIST_ONLY)

        assert _names(sites) == {"store"}

    def test_a_function_that_touches_no_plant_is_not_a_creation_site(self) -> None:
        sites, _direct = scan_source("def f(x):\n    return other.create(thing)\n")

        assert sites == {}

    def test_hydration_is_excluded_by_directory_not_by_the_detector(self) -> None:
        """`PlantInstance(**doc)` in a repository read has created no row — and the
        detector cannot tell the two apart, which is why the exclusion has to be
        stated rather than assumed."""
        sites, _direct = scan_source(_HYDRATION)

        assert _names(sites) == {"get"}, "the detector alone reads hydration as creation …"
        assert not [p for p in _module_files() if "/data_access/" in p.as_posix()], (
            "… so the directory exclusion is what keeps read paths out of the tree scan"
        )

    def test_the_bootstrap_call_is_recognised(self) -> None:
        _sites, direct = scan_source(_BOOTSTRAPPED, label="svc")

        assert "svc::create_plant" in direct

    def test_a_creation_path_without_the_bootstrap_is_reported(self) -> None:
        """The red-first case, in miniature: the guard's verdict over source that
        contains exactly the defect it exists for."""
        sites, direct = scan_source(_UNBOOTSTRAPPED, label="svc")

        assert set(sites) - direct == {"svc::import_plant"}


class TestTheClosure:
    """What the tree scan propagates, and — the part that took two attempts — what
    it must not."""

    def test_a_delegating_caller_inherits_the_bootstrap(self, monkeypatch, tmp_path) -> None:
        """How the REST router and the onboarding wizard pass: they build the model
        and hand it to ``create_plant``, which bootstraps."""
        sites, bootstrapped = _scan_fake_tree(
            monkeypatch,
            tmp_path,
            {
                "service.py": _BOOTSTRAPPED,
                "wizard.py": _DELEGATING,
            },
        )

        assert _names(sites) == {"create_plant", "seed"}
        assert _names({k: v for k, v in sites.items() if k in bootstrapped}) == {"create_plant", "seed"}

    def test_a_namesake_does_not_cover_a_migration(self, monkeypatch, tmp_path) -> None:
        """The reason the closure runs over creation sites only.

        A closure over every function in ``app/`` makes 201 names "bootstrappers" on
        this tree, ``upgrade`` among them — and ``upgrade`` is the entry point of
        every migration in ``app/migrations/versions/``. Under that rule this very
        case passed: a migration creating plants with no profile, declared covered by
        an unrelated function of the same name.
        """
        sites, bootstrapped = _scan_fake_tree(
            monkeypatch,
            tmp_path,
            {
                "service.py": _BOOTSTRAPPED_UPGRADE,
                "migration.py": _MIGRATION_CREATING_PLANTS,
            },
        )

        assert _names(sites) == {"create_plant", "upgrade"}
        offenders = {sites[key]["where"] for key in sites if key not in bootstrapped}
        assert offenders == {"app/migration.py:3"}, (
            "the migration must be reported although a bootstrapping function shares its name"
        )

    def test_a_synthetic_unbootstrapped_path_in_the_real_tree_reddens_the_guard(self) -> None:
        """The mutation, against the real ``app/`` scan rather than a fragment.

        Without it the guard could be inert for a reason no synthetic case shows — an
        exclusion that skips the services directory, a closure that swallows every
        name — and still pass every test above.
        """
        creation_sites, bootstrapped = scan_tree()
        assert {key for key in creation_sites if key not in bootstrapped} == set(), "the real tree is clean"

        injected, _direct = scan_source(_UNBOOTSTRAPPED, label="app/services/fake_import.py")
        creation_sites.update(injected)

        assert {key for key in creation_sites if key not in bootstrapped} == {
            "app/services/fake_import.py::import_plant"
        }
