"""Tests for the seeded-catalogue page-size check (``scripts/check_seed_catalogue_page_size.py``).

**What is under test.** The detection logic, driven against *constructed* trees
written into ``tmp_path`` — a seed directory, a seeder module and a frontend
module built per test. Asserting "the tree has 31 fertilizers" would go red on
the next seeded product and teach nobody anything; what is worth locking down is
what the check does with a given input.

**The deliberately-broken catalogue.** :class:`TestItCanFail` builds the exact
situation #995 describes — more seeded rows than the list view's page holds — and
asserts the check goes red, names the catalogue and says how many rows are
unreachable. A gate nobody has watched fail is a gate nobody knows works. The
same class covers the two other red paths: a ``complete`` catalogue whose owner
quietly went back to a bounded fetch, and a seed file no seeder loads.

**The two tests that do touch the real tree** are
:class:`TestTheRealTreeIsClean`, which runs the check exactly as the pre-commit
hook does, and :class:`TestTheRecordedExceptionsAreReal`, which asserts every
entry in ``KNOWN_UNLOADED_SEED_FILES`` still names a file that exists and is
still genuinely unloaded. Neither pins a count. The second exists because a
recorded exception that has quietly become untrue is the mechanism by which an
escape hatch turns into a permanent blind spot.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded **by path** — the same
mechanism ``test_boundary_validation_check.py`` uses.

Traces to issue #995 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

# ── Loading the script under test by path ────────────────────────────────────


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it.

    Registration in ``sys.modules`` happens **before** ``exec_module`` because the
    script defines ``@dataclass`` types, and ``dataclass`` resolves its own module
    through ``sys.modules`` while the module body is still running.

    Args:
        module_name: Private name to register under.
        path: The ``.py`` file to execute.

    Returns:
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and scripts/); "
        "scripts/check_seed_catalogue_page_size.py is unreachable from here",
        allow_module_level=True,
    )

_SCRIPT = _REPO_ROOT / "scripts" / "check_seed_catalogue_page_size.py"
if not _SCRIPT.is_file():  # pragma: no cover — only on a partial checkout
    pytest.skip(f"{_SCRIPT} does not exist", allow_module_level=True)

checker = _load_module_by_path("_seed_catalogue_page_size_check_under_test", _SCRIPT)


# ── A miniature tree ─────────────────────────────────────────────────────────


class Tree:
    """A constructed seed / seeder / frontend tree the check can be run against."""

    def __init__(self, root: Path) -> None:
        """Create the three directories the check reads."""
        self.seed_dir = root / "seed_data"
        self.migrations_dir = root / "migrations"
        self.frontend_src = root / "frontend"
        for directory in (self.seed_dir, self.migrations_dir, self.frontend_src):
            directory.mkdir(parents=True, exist_ok=True)

    def seed_file(self, name: str, body: str) -> None:
        """Write a seed YAML."""
        (self.seed_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (self.seed_dir / name).write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")

    def seeder(self, loads: list[str], name: str = "seed_things.py") -> None:
        """Write a seeder module that loads the named YAML files."""
        lines = "\n".join(f'    load_yaml("{target}")' for target in loads) or "    pass"
        (self.migrations_dir / name).write_text(
            f"def run():\n{lines}\n",
            encoding="utf-8",
        )

    def frontend_module(self, name: str, body: str) -> None:
        """Write a frontend module the check will scan for a loader symbol."""
        (self.frontend_src / name).parent.mkdir(parents=True, exist_ok=True)
        (self.frontend_src / name).write_text(body, encoding="utf-8")

    def measure(self, *catalogues: object) -> list[object]:
        """Run the check against this tree with an injected registry."""
        return checker.measure(
            self.seed_dir,
            self.migrations_dir,
            self.frontend_src,
            tuple(catalogues),
        )


def _widgets(count: int, prefix: str = "w") -> str:
    """A seed document with *count* named widget rows."""
    rows = "\n".join(f'  - name: "{prefix}{index}"' for index in range(count))
    return f"widgets:\n{rows}\n"


@pytest.fixture
def tree(tmp_path: Path) -> Tree:
    """A fresh constructed tree per test."""
    return Tree(tmp_path)


def _bounded(page_size: int, owner: str = "slice.ts") -> object:
    """A registry entry whose list view fetches one bounded page."""
    return checker.Catalogue(
        name="widgets",
        seed_keys=("widgets",),
        identity=("name",),
        owner=owner,
        page_size=page_size,
    )


def _complete(loader: str = "listAllWidgets", owner: str = "slice.ts") -> object:
    """A registry entry whose list view loads the whole catalogue."""
    return checker.Catalogue(
        name="widgets",
        seed_keys=("widgets",),
        identity=("name",),
        owner=owner,
        loader=loader,
    )


# ── The red paths ────────────────────────────────────────────────────────────


class TestItCanFail:
    """The three ways a catalogue can be unreachable, each watched failing."""

    def test_more_seeded_rows_than_the_page_holds_is_red(self, tree: Tree) -> None:
        """#995's exact shape: 53 rows against a page of 50 loses the last three."""
        tree.seed_file("widgets.yaml", _widgets(53))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listWidgets(0, 50);")

        results = tree.measure(_bounded(50))

        assert results[0].rows == 53
        assert results[0].failed is True

    def test_the_report_names_how_many_rows_are_unreachable(
        self, tree: Tree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A count nobody can read is a count nobody acts on."""
        tree.seed_file("widgets.yaml", _widgets(53))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listWidgets(0, 50);")

        exit_code = checker.report(tree.measure(_bounded(50)), False, 200)
        output = capsys.readouterr().out

        assert exit_code == checker.EXIT_DEFECTS
        assert "widgets" in output
        assert "3 row(s) unreachable" in output
        assert "53 seeded row(s) against a page of 50" in output

    def test_exactly_at_the_page_size_is_green_with_no_headroom(self, tree: Tree) -> None:
        """Rows are lost above the bound, not at it — and the report says so."""
        tree.seed_file("widgets.yaml", _widgets(50))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listWidgets(0, 50);")

        results = tree.measure(_bounded(50))

        assert results[0].failed is False
        assert results[0].rows == 50

    def test_one_row_past_the_page_size_is_red(self, tree: Tree) -> None:
        """The boundary the gate exists for: the *next* entry turns it red."""
        tree.seed_file("widgets.yaml", _widgets(51))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listWidgets(0, 50);")

        assert tree.measure(_bounded(50))[0].failed is True

    def test_a_complete_catalogue_reverting_to_a_bounded_fetch_is_red(self, tree: Tree) -> None:
        """The regression this fix must survive: the slice quietly pages again."""
        tree.seed_file("widgets.yaml", _widgets(5))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listWidgets(0, 50);")

        results = tree.measure(_complete())

        assert results[0].missing_loader is True
        assert results[0].failed is True

    def test_a_seed_file_no_seeder_loads_is_red(self, tree: Tree) -> None:
        """Rows in an unloaded file reach no database — and poison every count."""
        tree.seed_file("widgets.yaml", _widgets(5))
        tree.seed_file("widgets_supplement.yaml", _widgets(9, prefix="s"))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        results = tree.measure(_complete())

        assert results[0].rows == 5, "the unloaded file must not be counted as reachable"
        assert results[0].orphans == [("widgets_supplement.yaml", 9)]
        assert results[0].failed is True

    def test_the_orphan_report_says_what_to_do(self, tree: Tree, capsys: pytest.CaptureFixture[str]) -> None:
        """Both routes out are named, because either is a legitimate answer."""
        tree.seed_file("widgets.yaml", _widgets(5))
        tree.seed_file("widgets_supplement.yaml", _widgets(9, prefix="s"))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        checker.report(tree.measure(_complete()), False, 200)
        output = capsys.readouterr().out

        assert "widgets_supplement.yaml" in output
        assert "registry.py" in output
        assert "delete it" in output


# ── The green paths ──────────────────────────────────────────────────────────


class TestItPasses:
    """What a correct tree looks like, so the red tests above mean something."""

    def test_a_complete_loader_makes_any_row_count_green(self, tree: Tree) -> None:
        """The point of the `complete` contract: the count stops being a risk."""
        tree.seed_file("widgets.yaml", _widgets(500))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        results = tree.measure(_complete())

        assert results[0].rows == 500
        assert results[0].failed is False

    def test_the_green_report_prints_the_cost_of_loading_completely(
        self, tree: Tree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The price is stated rather than hidden: 500 rows is three round-trips."""
        tree.seed_file("widgets.yaml", _widgets(500))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        exit_code = checker.report(tree.measure(_complete()), False, 200)
        output = capsys.readouterr().out

        assert exit_code == checker.EXIT_OK
        assert "3 request(s)" in output


# ── Counting rules ───────────────────────────────────────────────────────────


class TestCounting:
    """The rules that decide what a row is, and which file it may come from."""

    def test_rows_are_deduplicated_across_files_by_identity(self, tree: Tree) -> None:
        """The same species in a base file and a plant-info file is one row."""
        tree.seed_file("a.yaml", "widgets:\n  - name: shared\n  - name: only-a\n")
        tree.seed_file("b.yaml", "widgets:\n  - name: shared\n  - name: only-b\n")
        tree.seeder(["a.yaml", "b.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        assert tree.measure(_complete())[0].rows == 3

    def test_a_compound_identity_keeps_same_named_rows_apart(self, tree: Tree) -> None:
        """Two products share a name under different brands — two rows, not one."""
        tree.seed_file(
            "a.yaml",
            """
            widgets:
              - name: CalMag
                brand: Terra Aquatica
              - name: CalMag
                brand: Canna
            """,
        )
        tree.seeder(["a.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        catalogue = checker.Catalogue(
            name="widgets",
            seed_keys=("widgets",),
            identity=("name", "brand"),
            owner="slice.ts",
            loader="listAllWidgets",
        )

        assert tree.measure(catalogue)[0].rows == 2

    def test_several_seed_keys_feed_one_catalogue(self, tree: Tree) -> None:
        """`families` and `new_families` are one collection, counted together."""
        tree.seed_file("a.yaml", "widgets:\n  - name: one\nnew_widgets:\n  - name: two\n")
        tree.seeder(["a.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        catalogue = checker.Catalogue(
            name="widgets",
            seed_keys=("widgets", "new_widgets"),
            identity=("name",),
            owner="slice.ts",
            loader="listAllWidgets",
        )

        assert tree.measure(catalogue)[0].rows == 2

    def test_a_glob_pattern_in_a_seeder_marks_its_matches_as_loaded(self, tree: Tree) -> None:
        """`glob("plant_info*.yaml")` must not read as nine orphaned files."""
        tree.seed_file("plant_info_1.yaml", _widgets(2, prefix="a"))
        tree.seed_file("plant_info_2.yaml", _widgets(2, prefix="b"))
        tree.seeder(["plant_info*.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        results = tree.measure(_complete())

        assert results[0].orphans == []
        assert results[0].rows == 4

    def test_the_schemas_directory_is_not_seed_content(self, tree: Tree) -> None:
        """Validation schemas live in seed_data/ but are neither rows nor orphans."""
        tree.seed_file("widgets.yaml", _widgets(3))
        tree.seed_file("schemas/widgets.schema.yaml", "widgets:\n  - name: not-a-row\n")
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        results = tree.measure(_complete())

        assert results[0].rows == 3
        assert results[0].orphans == []

    def test_a_recorded_unloaded_file_is_reported_but_not_red(self, tree: Tree) -> None:
        """The escape hatch defers the decision without hiding the number."""
        tree.seed_file("widgets.yaml", _widgets(5))
        tree.seed_file("fertilizers_supplement.yaml", "widgets:\n  - name: deferred\n")
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "listAllWidgets")

        results = tree.measure(_complete())

        assert results[0].failed is False
        assert results[0].orphans == []
        assert results[0].known_unloaded == [("fertilizers_supplement.yaml", 1)]
        assert results[0].rows == 5, "a deferred file is still not counted as reachable"


# ── Registry hygiene ─────────────────────────────────────────────────────────


class TestTheRegistryIsWellFormed:
    """A registry entry that declares nothing enforceable must not be accepted."""

    def test_declaring_neither_contract_is_rejected(self) -> None:
        with pytest.raises(checker.SeedCatalogueError):
            checker.Catalogue(name="widgets", seed_keys=("widgets",), identity=("name",), owner="slice.ts")

    def test_declaring_both_contracts_is_rejected(self) -> None:
        """Two contracts means the weaker one is silently ignored."""
        with pytest.raises(checker.SeedCatalogueError):
            checker.Catalogue(
                name="widgets",
                seed_keys=("widgets",),
                identity=("name",),
                owner="slice.ts",
                loader="listAllWidgets",
                page_size=50,
            )

    def test_an_owner_that_does_not_exist_is_an_error_not_a_pass(self, tree: Tree) -> None:
        """A renamed slice must not make its catalogue quietly stop being checked."""
        tree.seed_file("widgets.yaml", _widgets(3))
        tree.seeder(["widgets.yaml"])

        with pytest.raises(checker.SeedCatalogueError):
            tree.measure(_complete(owner="gone.ts"))


# ── The real tree ────────────────────────────────────────────────────────────


class TestTheRealTreeIsClean:
    """Runs the check over the real repository, exactly as the hook does."""

    def test_every_seeded_catalogue_is_reachable(self) -> None:
        assert checker.main([]) == checker.EXIT_OK

    def test_the_json_mode_agrees_with_the_exit_code(self, capsys: pytest.CaptureFixture[str]) -> None:
        """One tree, one verdict — the two modes derive it from the same predicate."""
        import json

        exit_code = checker.main(["--json"])
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == checker.EXIT_OK
        assert payload["failed"] == 0


class TestTheRecordedExceptionsAreReal:
    """An exception that has quietly become untrue is a permanent blind spot."""

    @pytest.mark.parametrize("filename", sorted(checker.KNOWN_UNLOADED_SEED_FILES))
    def test_the_file_still_exists(self, filename: str) -> None:
        """A stale entry would silence a *different*, future file of the same name."""
        assert (checker.SEED_DATA_DIR / filename).is_file(), (
            f"{filename} is recorded in KNOWN_UNLOADED_SEED_FILES but no longer exists — drop the entry"
        )

    @pytest.mark.parametrize("filename", sorted(checker.KNOWN_UNLOADED_SEED_FILES))
    def test_the_file_is_still_unloaded(self, filename: str) -> None:
        """Once it is wired in, the entry stops deferring anything and must go."""
        patterns = checker.loaded_yaml_patterns(checker.MIGRATIONS_DIR)
        assert not checker.is_loaded(Path(filename), patterns), (
            f"{filename} is now loaded by a seeder — remove it from KNOWN_UNLOADED_SEED_FILES so its rows are counted"
        )

    @pytest.mark.parametrize("filename", sorted(checker.KNOWN_UNLOADED_SEED_FILES))
    def test_the_reason_is_a_reason(self, filename: str) -> None:
        """The hatch is a reason a reviewer can argue with, not a checkbox."""
        assert len(checker.KNOWN_UNLOADED_SEED_FILES[filename]) > 40
