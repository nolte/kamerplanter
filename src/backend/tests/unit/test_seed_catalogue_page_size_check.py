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


def _with_reader_scan(owner: str = "slice.ts") -> object:
    """A ``complete`` registry entry that also declares its capped reader.

    ``endpoint_module`` is matched against the end of an import specifier, so a
    constructed module can import from ``@/api/endpoints/widgets`` and resolve.
    """
    return checker.Catalogue(
        name="widgets",
        seed_keys=("widgets",),
        identity=("name",),
        owner=owner,
        loader="listAllWidgets",
        endpoint_module="endpoints/widgets",
        capped_reader="listWidgets",
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
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

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
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

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
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

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
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        results = tree.measure(_complete())

        assert results[0].orphans == []
        assert results[0].rows == 4

    def test_the_schemas_directory_is_not_seed_content(self, tree: Tree) -> None:
        """Validation schemas live in seed_data/ but are neither rows nor orphans."""
        tree.seed_file("widgets.yaml", _widgets(3))
        tree.seed_file("schemas/widgets.schema.yaml", "widgets:\n  - name: not-a-row\n")
        tree.seeder(["widgets.yaml"])
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

        results = tree.measure(_complete())

        assert results[0].rows == 3
        assert results[0].orphans == []

    def test_a_recorded_unloaded_file_is_reported_but_not_red(self, tree: Tree) -> None:
        """The escape hatch defers the decision without hiding the number."""
        tree.seed_file("widgets.yaml", _widgets(5))
        tree.seed_file("fertilizers_supplement.yaml", "widgets:\n  - name: deferred\n")
        tree.seeder(["widgets.yaml"])
        # A *call*, because that is what a real owner contains. This fixture
        # used to be the bare name, which only passed while the `complete`
        # contract was a raw substring test (#1568 review, SCR-005).
        tree.frontend_module("slice.ts", "export const list = () => listAllWidgets();")

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


class TestEveryReadingModuleIsSeen:
    """#1560: the gate binds every module that reads the catalogue, not one owner.

    **What made this necessary.** The check bound a single ``owner`` module per
    catalogue and asserted it referenced the complete loader. ``speciesSlice.ts``
    did, so the gate was green — while eight pickers in eight other modules read
    ``listSpecies(0, 200)`` against 207 seeded species. Seven species were
    unpickable in production and this check returned 0. A gate that cannot go red
    against the defect it is named for is the measurement gap this repository pays
    for most often, so the cases below exist as much to watch it fail as to watch
    it pass.
    """

    def _seeded(self, tree: Tree) -> None:
        """A small, loaded catalogue plus an owner that honours the contract."""
        tree.seed_file("widgets.yaml", _widgets(3))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", "export const load = () => listAllWidgets();\n")

    def test_a_picker_reading_the_capped_reader_is_red(self, tree: Tree) -> None:
        """The production shape, reduced: a namespace import and a bounded call."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "export const load = () => widgetApi.listWidgets(0, 200);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed
        assert [module for module, _line in result.capped_readers] == ["pages/Picker.tsx"]

    def test_the_report_names_the_module_and_the_line(self, tree: Tree, capsys: pytest.CaptureFixture[str]) -> None:
        """A finding a reader cannot locate is a finding that gets suppressed."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "\n"
            "export const load = () => widgetApi.listWidgets(0, 200);\n",
        )

        results = tree.measure(_with_reader_scan())
        assert checker.report(results, False, 200) == checker.EXIT_DEFECTS

        output = capsys.readouterr().out
        assert "pages/Picker.tsx:3" in output
        assert "listAllWidgets()" in output

    def test_the_receiver_may_be_split_from_the_method_by_a_newline(self, tree: Tree) -> None:
        """The spelling that defeated the first sweep.

        Six of the twenty-two sites #1560 found are written this way, and a
        ``widgetApi.listWidgets`` grep reports none of them. The first version of
        the sweep found sixteen and looked complete.
        """
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "export const load = () =>\n"
            "  widgetApi\n"
            "    .listWidgets(0, 200)\n"
            "    .then((r) => r.items);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed
        assert [module for module, _line in result.capped_readers] == ["pages/Picker.tsx"]

    def test_a_named_import_of_the_capped_reader_is_red(self, tree: Tree) -> None:
        """``import { listWidgets } from …`` — the other half of the class."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import { listWidgets, listCultivars } from '@/api/endpoints/widgets';\n"
            "export const load = () => listWidgets(0, 500);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed

    def test_a_relative_import_specifier_resolves_too(self, tree: Tree) -> None:
        """Not every module imports through the ``@/`` alias."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/deep/Picker.tsx",
            "import * as widgetApi from '../../api/endpoints/widgets';\n"
            "export const load = () => widgetApi.listWidgets(0, 200);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed

    def test_a_same_named_export_from_a_different_module_is_not_a_finding(self, tree: Tree) -> None:
        """The false positive that decided the predicate's shape.

        ``dispatch(fetchFertilizers({}))`` is the *slice thunk*, which loads the
        complete catalogue. It shares its name with the capped reader, so a name
        grep calls the repair a defect — and a check with false positives gets
        suppressed, which is worse than the gap it closes.
        """
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import { listWidgets } from '@/store/slices/widgetsSlice';\n"
            "export const load = (dispatch) => dispatch(listWidgets({}));\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed
        assert result.capped_readers == []

    def test_a_comment_naming_the_capped_reader_is_not_a_finding(self, tree: Tree) -> None:
        """``fertilizersSlice.ts`` carries exactly this comment, warning callers off it."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "// Do not call widgetApi.listWidgets(0, 200) here — it is bounded.\n"
            "/* widgetApi.listWidgets(0, 200) is the wrong reader. */\n"
            "export const load = () => widgetApi.listAllWidgets();\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed

    def test_the_endpoint_module_itself_is_not_a_finding(self, tree: Tree) -> None:
        """The complete loader is defined next to the capped one and calls it."""
        self._seeded(tree)
        tree.frontend_module(
            "api/endpoints/widgets.ts",
            "export async function listWidgets(offset = 0, limit = 50) { return []; }\n"
            "export async function listAllWidgets() { return listWidgets(0, 200); }\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed

    def test_test_modules_are_not_findings(self, tree: Tree) -> None:
        """A test asserting the capped reader's own behaviour must stay legal."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.test.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "it('pages', () => widgetApi.listWidgets(0, 200));\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed

    def test_an_aliased_named_import_is_red(self, tree: Tree) -> None:
        """The spelling the docstring claimed to catch and did not.

        `import { listWidgets as loadWidgets }` matched the clause, after which
        the scan searched for `listWidgets(` — but the call is `loadWidgets(`, so
        the module came back clean. Text and code disagreed, and a comment
        describing a guarantee the code does not give is how #1393 spent four
        rounds not looking. The finding now hangs on the binding.
        """
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import { listWidgets as loadWidgets } from '@/api/endpoints/widgets';\n"
            "export const load = () => loadWidgets(0, 200);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed
        assert [module for module, _line in result.capped_readers] == [
            "pages/Picker.tsx",
            "pages/Picker.tsx",
        ]

    def test_a_re_export_is_red(self, tree: Tree) -> None:
        """`export { listWidgets } from …` puts it in a second public surface.

        It carries no `import` keyword, so the import-only pattern never saw it.
        """
        self._seeded(tree)
        tree.frontend_module(
            "pages/reexport.ts",
            "export { listWidgets } from '@/api/endpoints/widgets';\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed

    def test_a_dynamic_import_is_red(self, tree: Tree) -> None:
        """`const { listWidgets } = await import(…)` has no static import at all."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Lazy.tsx",
            "export const load = async () => {\n"
            "  const { listWidgets } = await import('@/api/endpoints/widgets');\n"
            "  return listWidgets(0, 200);\n"
            "};\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed

    def test_a_wrapper_under_api_is_red(self, tree: Tree) -> None:
        """`api/` was excluded wholesale, hiding a wrapper twice over.

        Only the catalogue's own endpoint module is exempt now — it defines the
        capped reader and its complete loader legitimately calls it.
        """
        self._seeded(tree)
        tree.frontend_module(
            "api/wrappers/widgets.ts",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "export const loadPage = () => widgetApi.listWidgets(0, 200);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed
        assert [module for module, _line in result.capped_readers] == ["api/wrappers/widgets.ts"]

    def test_the_endpoint_module_itself_stays_exempt(self, tree: Tree) -> None:
        """The counterpart to widening the scan: the definition is not a defect."""
        self._seeded(tree)
        tree.frontend_module(
            "api/endpoints/widgets.ts",
            "export async function listWidgets(offset = 0, limit = 50) { return []; }\n"
            "export async function listAllWidgets() { return listWidgets(0, 200); }\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed

    def test_a_bound_reference_without_a_call_is_red(self, tree: Tree) -> None:
        """`const read = widgetApi.listWidgets` — bound now, called later.

        The namespace branch required a `(`, so the assignment slipped past and
        the call through `read(` carried no trace of the module it came from.
        """
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "const read = widgetApi.listWidgets;\n"
            "export const load = () => read(0, 200);\n",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert result.failed

    def test_an_allowlisted_module_is_not_red(self, tree: Tree, monkeypatch: pytest.MonkeyPatch) -> None:
        """A caller that genuinely wants one page is a reason, not a silence."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "export const load = () => widgetApi.listWidgets(0, 200);\n",
        )
        monkeypatch.setitem(
            checker.KNOWN_CAPPED_READERS,
            "widgets:pages/Picker.tsx",
            "search-as-you-type; the user never sees the whole catalogue here",
        )

        (result,) = tree.measure(_with_reader_scan())

        assert not result.failed

    def test_a_catalogue_without_a_declared_reader_is_not_scanned(self, tree: Tree) -> None:
        """The scan is opt-in per catalogue, so an entry can be added incrementally."""
        self._seeded(tree)
        tree.frontend_module(
            "pages/Picker.tsx",
            "import * as widgetApi from '@/api/endpoints/widgets';\n"
            "export const load = () => widgetApi.listWidgets(0, 200);\n",
        )

        (result,) = tree.measure(_complete())

        assert not result.failed
        assert result.capped_readers == []


class TestTheCompleteContractNeedsACall:
    """The ``complete`` half must not be satisfiable by prose (#1568 review, SCR-005).

    It was. The check read the owner's **unstripped** source and asked whether the
    loader's name appeared anywhere in it, while the reader scan next to it
    stripped comments properly. Two owners name their loader in a comment head
    (``fertilizersSlice.ts:4``, ``activitiesSlice.ts:5``), so removing the real
    call and leaving the comment kept the gate green — measured at exit 0 by
    replacing ``api.listAllActivities(arg)`` with a hand-rolled bounded
    ``fetch()``. That is the vacuum class from PR #1545.
    """

    def _tree(self, tree: Tree, owner_body: str) -> None:
        tree.seed_file("widgets.yaml", _widgets(3))
        tree.seeder(["widgets.yaml"])
        tree.frontend_module("slice.ts", owner_body)

    def test_the_loader_named_only_in_a_comment_is_red(self, tree: Tree) -> None:
        """A line comment naming the loader is prose about it, not a call to it."""
        self._tree(
            tree,
            "// This slice loads the complete catalogue via listAllWidgets().\n"
            "export const load = () => fetch('/api/v1/widgets?limit=50');\n",
        )

        (result,) = tree.measure(_complete())

        assert result.missing_loader
        assert result.failed

    def test_the_loader_named_only_in_a_block_comment_is_red(self, tree: Tree) -> None:
        """The same through the other comment syntax, which the owners actually use."""
        self._tree(
            tree,
            "/**\n * The complete catalogue, via listAllWidgets().\n */\n"
            "export const load = () => fetch('/api/v1/widgets?limit=50');\n",
        )

        (result,) = tree.measure(_complete())

        assert result.missing_loader

    def test_a_real_call_is_green_even_with_the_comment_present(self, tree: Tree) -> None:
        """The counterpart: the repair must not be red just because prose exists.

        Both real owners carry exactly this shape — a comment head naming the
        loader *and* the call — so a fix that only looked outside comments in the
        wrong direction would have turned the tree red.
        """
        self._tree(
            tree,
            "// The complete catalogue, via listAllWidgets().\nexport const load = () => listAllWidgets();\n",
        )

        (result,) = tree.measure(_complete())

        assert not result.missing_loader
        assert not result.failed

    def test_the_bare_name_without_a_call_is_red(self, tree: Tree) -> None:
        """Mentioning the symbol in code is not calling it either."""
        self._tree(tree, "export const loaderName = 'listAllWidgets';\n")

        (result,) = tree.measure(_complete())

        assert result.missing_loader


class TestEveryCatalogueEndpointIsRegistered:
    """The registry must not be a list somebody has to remember (#1568 review, SCR-003).

    Every check runs *per registered catalogue*, so a new
    ``api/endpoints/<x>.ts`` exporting ``listAll<X>``, with a picker reading
    ``list<X>(0, 200)``, was green — the scan never looked at that catalogue.
    That is #1560's blind spot one level up, and the existing meta-test only
    asserts the opposite direction.
    """

    def _endpoints(self, tree: Tree, filename: str, body: str) -> None:
        tree.frontend_module(f"api/endpoints/{filename}", body)

    def test_an_unregistered_module_with_a_complete_loader_is_red(self, tree: Tree) -> None:
        """The production shape of the gap, reduced."""
        self._endpoints(
            tree,
            "widgets.ts",
            "export async function listWidgets(offset = 0, limit = 50) { return []; }\n"
            "export async function listAllWidgets() { return listWidgets(0, 200); }\n",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, ())

        assert findings == [("endpoints/widgets", "listAllWidgets")]

    def test_a_registered_module_is_not_a_finding(self, tree: Tree) -> None:
        """The counterpart, so the check is not simply always red."""
        self._endpoints(
            tree,
            "widgets.ts",
            "export async function listAllWidgets() { return []; }\n",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, (_with_reader_scan(),))

        assert findings == []

    def test_the_fetch_all_spelling_counts_too(self, tree: Tree) -> None:
        """Half the real loaders are `fetchAll*`, not `listAll*`."""
        self._endpoints(
            tree,
            "widgets.ts",
            "export async function fetchAllWidgets() { return []; }\n",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, ())

        assert findings == [("endpoints/widgets", "fetchAllWidgets")]

    def test_a_module_without_a_complete_loader_is_not_a_catalogue(self, tree: Tree) -> None:
        """Most endpoint modules are not catalogues and must stay silent."""
        self._endpoints(
            tree,
            "widgets.ts",
            "export async function getWidget(key: string) { return { key }; }\n",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, ())

        assert findings == []

    def test_a_recorded_module_is_not_a_finding(self, tree: Tree, monkeypatch) -> None:
        """The escape hatch carries a reason, like every other one here."""
        self._endpoints(
            tree,
            "widgets.ts",
            "export async function listAllWidgets() { return []; }\n",
        )
        monkeypatch.setitem(
            checker.KNOWN_UNREGISTERED_LOADERS,
            "endpoints/widgets",
            "tenant-owned collection, starts empty; a seed count says nothing about it",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, ())

        assert findings == []

    def test_a_comment_mentioning_a_loader_does_not_invent_a_catalogue(self, tree: Tree) -> None:
        """The same vacuum from the other side: prose must not create a finding."""
        self._endpoints(
            tree,
            "widgets.ts",
            "// One day this will export listAllWidgets().\n"
            "export async function getWidget(key: string) { return { key }; }\n",
        )

        findings = checker.unregistered_catalogue_modules(tree.frontend_src, ())

        assert findings == []


class TestEveryRegisteredCatalogueDeclaresItsReader:
    """The scan is opt-in per catalogue, so absence of an entry must be visible.

    Without this, adding a catalogue to the registry and forgetting its
    ``capped_reader`` would reproduce #1560's blind spot one catalogue at a time,
    silently and with a green gate.
    """

    @pytest.mark.parametrize("catalogue", checker.CATALOGUES, ids=lambda c: str(getattr(c, "name", c)))
    def test_the_reader_scan_is_declared(self, catalogue: object) -> None:
        """Every registered catalogue names the module and reader to scan for."""
        assert catalogue.endpoint_module is not None
        assert catalogue.capped_reader is not None


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
