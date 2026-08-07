"""Tests for the API schema-example ratchet (``scripts/check_schema_examples.py``).

**What is under test.** The counting logic, driven against *constructed* schema
modules written into ``tmp_path`` — never against the real
``src/backend/app/api/v1`` tree. A test that asserted "the tree has 711 models"
would fail on the next legitimate schema and teach nobody anything; the property
worth locking down is what the counter does with a given input.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a PR-gating CI check.
The script itself lives outside the backend package, so it is loaded **by path**,
the same mechanism ``test_gherkin_line_classification.py`` uses for
``tests/e2e/_gherkin.py``.

**The bypass this guards.** A check that accepted ``examples=[{}]`` would be
satisfiable by three keystrokes while documenting nothing — the gate would then
measure diligence at typing, not at explaining an API.
:class:`TestEmptyExamplesDoNotCount` pins every empty shape.

Traces to issue #850 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from collections.abc import Callable
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
        "scripts/check_schema_examples.py is unreachable from here",
        allow_module_level=True,
    )

_SCRIPT = _REPO_ROOT / "scripts" / "check_schema_examples.py"
if not _SCRIPT.is_file():  # pragma: no cover — only on a partial checkout
    pytest.skip(f"{_SCRIPT} does not exist", allow_module_level=True)

checker = _load_module_by_path("_schema_example_ratchet_under_test", _SCRIPT)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def write_schema(tmp_path: Path) -> Callable[[str, str], Path]:
    """Return a helper that writes a ``schemas.py`` into a package under ``tmp_path``.

    Each module gets its own package directory with an ``__init__.py``, so the
    script's dotted-name derivation (which walks up while ``__init__.py`` exists)
    sees the same shape as the real tree.
    """

    def _write(package: str, source: str) -> Path:
        directory = tmp_path / package
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
        module = directory / "schemas.py"
        module.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
        return module

    return _write


def _count(root: Path) -> tuple[int, int]:
    """Return ``(models, models_without_example)`` for everything below *root*."""
    models = checker.collect_models(checker.iter_schema_modules([root]))
    return len(models), sum(1 for model in models if not model.has_example)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestModelDetection:
    """Which classes in a ``schemas.py`` are counted at all."""

    def test_counts_direct_basemodel_subclasses(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """The ordinary shape — ``class X(BaseModel)`` — is the unit being counted."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel


            class TankCreate(BaseModel):
                name: str


            class TankResponse(BaseModel):
                key: str
            """,
        )
        assert _count(tmp_path) == (2, 2)

    def test_counts_a_subclass_of_another_model(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """A model deriving from a sibling model is a model.

        This is the shape the #850 audit's ``grep 'class …(BaseModel)'`` missed —
        three real response bodies, hence a baseline of 711 rather than 708.
        """
        write_schema(
            "profiles",
            """
            from pydantic import BaseModel


            class RequirementProfileCreate(BaseModel):
                name: str


            class RequirementProfileResponse(RequirementProfileCreate):
                key: str
            """,
        )
        assert _count(tmp_path) == (2, 2)

    def test_counts_a_subclass_imported_from_another_schema_module(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """A base pulled in from another scanned ``schemas.py`` resolves across modules."""
        write_schema(
            "plant_instances",
            """
            from pydantic import BaseModel


            class SpeciesSummary(BaseModel):
                key: str
            """,
        )
        write_schema(
            "planting_runs",
            """
            from plant_instances.schemas import SpeciesSummary


            class RunSpeciesSummary(SpeciesSummary):
                run_key: str
            """,
        )
        assert _count(tmp_path) == (2, 2)

    def test_ignores_classes_that_are_not_pydantic_models(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """Enums, ``TypedDict``s and plain helpers are not request/response bodies."""
        write_schema(
            "mixed",
            """
            from enum import Enum
            from typing import TypedDict

            from pydantic import BaseModel


            class Severity(str, Enum):
                LOW = "low"


            class RawRow(TypedDict):
                key: str


            class Helper:
                pass


            class AlertResponse(BaseModel):
                severity: str
            """,
        )
        assert _count(tmp_path) == (1, 1)

    def test_ignores_a_class_defined_inside_a_function(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """Only module-level classes count — a local class is not API surface.

        Counting them would tie the number to helper-function refactorings, which
        is exactly the instability that makes a ratchet look like a defect.
        """
        write_schema(
            "factories",
            """
            from pydantic import BaseModel


            def build():
                class Local(BaseModel):
                    key: str

                return Local
            """,
        )
        assert _count(tmp_path) == (0, 0)

    def test_scans_only_files_named_schemas_py(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """A model in a router is out of scope — the convention puts schemas in ``schemas.py``."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel


            class TankResponse(BaseModel):
                key: str
            """,
        )
        (tmp_path / "tanks" / "router.py").write_text(
            "from pydantic import BaseModel\n\n\nclass Inline(BaseModel):\n    key: str\n",
            encoding="utf-8",
        )
        assert _count(tmp_path) == (1, 1)


class TestExampleDetection:
    """Which carriers satisfy BACKEND.md §5.3."""

    def test_model_config_configdict_example_counts(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """The primary carrier: ``ConfigDict(json_schema_extra={"examples": [...]})``."""
        write_schema(
            "species",
            """
            from pydantic import BaseModel, ConfigDict


            class SpeciesCreate(BaseModel):
                scientific_name: str

                model_config = ConfigDict(
                    json_schema_extra={"examples": [{"scientific_name": "Monstera deliciosa"}]}
                )
            """,
        )
        assert _count(tmp_path) == (1, 0)

    def test_model_config_dict_literal_example_counts(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """The dict-literal spelling of ``model_config`` this codebase already uses."""
        write_schema(
            "species",
            """
            from pydantic import BaseModel


            class SpeciesCreate(BaseModel):
                scientific_name: str

                model_config = {
                    "populate_by_name": True,
                    "json_schema_extra": {"examples": [{"scientific_name": "Monstera deliciosa"}]},
                }
            """,
        )
        assert _count(tmp_path) == (1, 0)

    def test_field_level_example_counts(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """The second carrier §5.3 names: ``Field(..., examples=[1.8])``."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel, Field


            class TankStateCreate(BaseModel):
                ec_ms_cm: float = Field(ge=0, examples=[1.8])
                ph: float = Field(ge=0, le=14)
            """,
        )
        assert _count(tmp_path) == (1, 0)

    def test_openapi_30_singular_example_key_counts(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """``json_schema_extra={"example": {...}}`` is as visible to a consumer."""
        write_schema(
            "species",
            """
            from pydantic import BaseModel, ConfigDict


            class SpeciesCreate(BaseModel):
                scientific_name: str

                model_config = ConfigDict(
                    json_schema_extra={"example": {"scientific_name": "Monstera deliciosa"}}
                )
            """,
        )
        assert _count(tmp_path) == (1, 0)

    def test_example_referenced_by_name_counts(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """A payload the checker cannot evaluate is credited, not punished.

        ``examples=SPECIES_EXAMPLES`` points at content; reading it as a bypass
        would push authors away from factoring examples out, for no gain.
        """
        write_schema(
            "species",
            """
            from pydantic import BaseModel, Field

            SPECIES_EXAMPLES = [{"scientific_name": "Monstera deliciosa"}]


            class SpeciesCreate(BaseModel):
                scientific_name: str = Field(examples=SPECIES_EXAMPLES)
            """,
        )
        assert _count(tmp_path) == (1, 0)

    def test_example_is_inherited_from_a_base_model(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """Pydantic merges ``model_config`` down the MRO, so the subclass is documented."""
        write_schema(
            "profiles",
            """
            from pydantic import BaseModel, ConfigDict


            class ProfileCreate(BaseModel):
                name: str

                model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Tomate"}]})


            class ProfileResponse(ProfileCreate):
                key: str
            """,
        )
        assert _count(tmp_path) == (2, 0)

    def test_an_unrelated_config_key_is_not_an_example(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """``model_config`` alone proves nothing — the check looks for the example key."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel


            class TankResponse(BaseModel):
                key: str

                model_config = {"populate_by_name": True}
            """,
        )
        assert _count(tmp_path) == (1, 1)

    def test_field_constraints_without_examples_do_not_count(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path]
    ) -> None:
        """A ``description`` is documentation, but §5.3 asks for a concrete value."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel, Field


            class EcDilutionRequest(BaseModel):
                current_ec_ms: float = Field(gt=0, description="Current EC (mS/cm)")
            """,
        )
        assert _count(tmp_path) == (1, 1)


class TestEmptyExamplesDoNotCount:
    """The bypass guard: a placeholder must not satisfy the rule."""

    @pytest.mark.parametrize(
        ("label", "payload"),
        [
            ("empty list", "[]"),
            ("empty dict", "[{}]"),
            ("empty string", '[""]'),
            ("whitespace string", '["   "]'),
            ("null", "[None]"),
            ("empty nested list", "[[]]"),
        ],
    )
    def test_empty_model_config_example_leaves_the_model_undocumented(
        self,
        tmp_path: Path,
        write_schema: Callable[[str, str], Path],
        label: str,
        payload: str,
    ) -> None:
        """``examples={payload}`` publishes nothing, so the model stays counted."""
        write_schema(
            "species",
            f"""
            from pydantic import BaseModel, ConfigDict


            class SpeciesCreate(BaseModel):
                scientific_name: str

                model_config = ConfigDict(json_schema_extra={{"examples": {payload}}})
            """,
        )
        assert _count(tmp_path) == (1, 1), f"{label} was wrongly accepted as an example"

    @pytest.mark.parametrize(("label", "payload"), [("empty list", "[]"), ("empty dict", "[{}]")])
    def test_empty_field_example_leaves_the_model_undocumented(
        self,
        tmp_path: Path,
        write_schema: Callable[[str, str], Path],
        label: str,
        payload: str,
    ) -> None:
        """The same guard on the field-level carrier."""
        write_schema(
            "tanks",
            f"""
            from pydantic import BaseModel, Field


            class TankStateCreate(BaseModel):
                ec_ms_cm: float = Field(ge=0, examples={payload})
            """,
        )
        assert _count(tmp_path) == (1, 1), f"{label} was wrongly accepted as an example"

    def test_a_zero_is_a_value_not_an_absence(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> None:
        """``examples=[0]`` is poor style, but it is not empty.

        §5.3 asks for a realistic value; whether ``0`` is realistic for a given
        field is a review question, not a machine one. Rejecting a falsy scalar
        here would fail legitimate schemas (``frost_free_days``, ``offset``).
        """
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel, Field


            class OffsetRequest(BaseModel):
                offset: int = Field(examples=[0])
            """,
        )
        assert _count(tmp_path) == (1, 0)


class TestRatchetDirections:
    """Growth fails, equality passes, and a drop fails asking for a new baseline."""

    @pytest.fixture
    def tree(self, tmp_path: Path, write_schema: Callable[[str, str], Path]) -> Path:
        """A tree holding exactly two undocumented models."""
        write_schema(
            "tanks",
            """
            from pydantic import BaseModel


            class TankCreate(BaseModel):
                name: str


            class TankResponse(BaseModel):
                key: str
            """,
        )
        return tmp_path

    def test_equal_to_the_baseline_is_green(self, tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """The steady state: nothing moved, nothing to report."""
        exit_code = checker.main(["--schema-root", str(tree), "--baseline", "2"])
        assert exit_code == checker.EXIT_OK
        assert "OK — 2 model(s) without an example" in capsys.readouterr().out

    def test_growth_fails_and_names_the_carriers(self, tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """One model above the ceiling is a defect, and the message says how to fix it."""
        exit_code = checker.main(["--schema-root", str(tree), "--baseline", "1"])
        assert exit_code == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "1 above the recorded ceiling" in out
        assert "json_schema_extra" in out
        assert "examples=[1.8]" in out
        # The one remediation that must never be offered: raising the number.
        assert "Raising MAX_MODELS_WITHOUT_EXAMPLE is not the fix" in out

    def test_a_drop_passes_and_names_the_headroom_instead_of_a_hand_edit(
        self, tree: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Progress is reported, not punished, and no hand edit is demanded.

        Failing on a drop was rejected from the start: it would block every
        refactoring that merely deletes or renames a schema module. Since #973 the
        drop does not *ask* for the constant to be lowered either — that request
        is what put every pull request adding an example on the same line of the
        same file, and two in flight conflicted on an integer carrying no review
        value.

        What the drop must still print is the **headroom**, because that is the
        cost of the trade: every unit of it is one undocumented schema this gate
        would let through unnoticed.
        """
        exit_code = checker.main(["--schema-root", str(tree), "--baseline", "3"])
        assert exit_code == checker.EXIT_OK
        out = capsys.readouterr().out
        assert "below the recorded ceiling of 3" in out
        assert "1 more undocumented model(s) would still pass" in out
        assert "can be lowered to" not in out

    def test_list_names_every_counted_model(self, tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """``--list`` is how a developer resolves an unexpected delta."""
        checker.main(["--schema-root", str(tree), "--baseline", "2", "--list"])
        out = capsys.readouterr().out
        assert "TankCreate" in out
        assert "TankResponse" in out

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot see its input must not report success.

        The alternative — scanning nothing, counting zero — would read as a
        *drop*, and a hook pointed at a moved directory would look like progress.
        """
        exit_code = checker.main(
            [
                "--schema-root",
                str(tmp_path / "does-not-exist"),
                "--baseline",
                "0",
            ]
        )
        assert exit_code == checker.EXIT_USAGE
        assert "schema root does not exist" in capsys.readouterr().err


class TestConcurrentPullRequests:
    """#973: the recorded number is a ceiling, and no pull request has to move it.

    Before this change the check was *shrink-only*: a drop passed but printed
    "Baseline can be lowered to N", and authors followed the instruction. Every
    pull request that documented a schema therefore edited the same integer in
    the same file, and two of them in flight conflicted — four times in one
    afternoon while landing #954, #967 and #971. The conflict never signalled a
    disagreement between the changes; it was two authors independently reporting
    that the debt had shrunk. Worse, resolving it by taking either side yields a
    number that is too *high*, which loosens the ratchet silently.

    The property to keep across that change is the whole point of the gate, so it
    is asserted in both directions here: adding an undocumented model fails,
    adding an example does not.
    """

    @staticmethod
    def _undocumented(write_schema: Callable[[str, str], Path], package: str, name: str) -> None:
        """Write a package holding exactly one model with no example."""
        write_schema(
            package,
            f"""
            from pydantic import BaseModel


            class {name}(BaseModel):
                key: str
            """,
        )

    def test_adding_an_undocumented_model_still_fails(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The guarantee the ceiling exists for, walked as a two-commit sequence.

        Green both before and after #973 — that is the point: it is the regression
        guard on the property the conflict fix must not trade away.
        """
        self._undocumented(write_schema, "tanks", "TankResponse")
        ceiling = "1"
        assert checker.main(["--schema-root", str(tmp_path), "--baseline", ceiling]) == checker.EXIT_OK
        capsys.readouterr()

        # The pull request under test: one new response body, no example.
        self._undocumented(write_schema, "sensors", "SensorResponse")

        assert checker.main(["--schema-root", str(tmp_path), "--baseline", ceiling]) == checker.EXIT_DEFECTS
        assert "1 above the recorded ceiling" in capsys.readouterr().out

    def test_adding_an_example_passes_without_asking_for_the_constant_to_move(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reverse direction, and the conflict's actual source.

        The author documents a schema, the count falls below the ceiling, and the
        check must be green *and silent about the constant*. Naming a new number
        to record here is what sent every such pull request to the same line.
        """
        self._undocumented(write_schema, "tanks", "TankResponse")
        write_schema(
            "species",
            """
            from pydantic import BaseModel, ConfigDict


            class SpeciesResponse(BaseModel):
                scientific_name: str

                model_config = ConfigDict(
                    json_schema_extra={"examples": [{"scientific_name": "Monstera deliciosa"}]}
                )
            """,
        )

        exit_code = checker.main(["--schema-root", str(tmp_path), "--baseline", "2"])

        assert exit_code == checker.EXIT_OK
        out = capsys.readouterr().out
        assert "MAX_MODELS_WITHOUT_EXAMPLE" not in out
        assert "check_schema_examples.py" not in out

    def test_the_headroom_is_printed_so_the_slack_is_not_invisible(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A ceiling that is never lowered drifts upward, and the drift must be readable.

        This is the price of not demanding a hand edit: the gap between the
        recorded ceiling and the real count is exactly how many undocumented
        models could be added before anything turns red. Printing it in the
        required lane's log keeps that a stated number rather than a discovery.
        """
        self._undocumented(write_schema, "tanks", "TankResponse")

        checker.main(["--schema-root", str(tmp_path), "--baseline", "5"])

        out = capsys.readouterr().out
        assert "4 more undocumented model(s) would still pass" in out

    def test_json_agrees_with_the_human_report_below_the_ceiling(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Two exit codes for one state is a trap for whoever wires the check up next.

        ``--json`` failed on a drop while the human report passed it, so the same
        tree was green through the pre-commit hook and red through the documented
        machine-readable mode.
        """
        self._undocumented(write_schema, "tanks", "TankResponse")

        exit_code = checker.main(["--schema-root", str(tmp_path), "--baseline", "5", "--json"])

        assert exit_code == checker.EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["without_example"] == 1
        assert payload["baseline"] == 5
        assert payload["headroom"] == 4

    def test_json_still_fails_above_the_ceiling(
        self, tmp_path: Path, write_schema: Callable[[str, str], Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Agreement in the other direction: growth is a defect in both modes."""
        self._undocumented(write_schema, "tanks", "TankResponse")
        self._undocumented(write_schema, "sensors", "SensorResponse")

        exit_code = checker.main(["--schema-root", str(tmp_path), "--baseline", "1", "--json"])

        assert exit_code == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert payload["headroom"] == -1


# ── Deliberately absent: an assertion about the real tree ────────────────────
#
# An earlier draft carried ``TestRealTreeIsAtItsBaseline``, comparing the
# constant against ``src/backend/app/api/v1`` itself. It was removed: it is the
# same measurement, against the same constant, through the same code — a second
# runner, not a second signal. The required ``static`` lane already runs the
# checker with ``--all-files`` on every push, unconditionally; this suite runs in
# the path-filtered, non-required backend lane. What the duplicate did add was a
# worse failure: a bare ``assert without == …`` with none of the remediation
# output the script prints, surfacing in the suite where nobody would look for it.
#
# The enforcement against the real tree belongs to the hook. This file stays what
# its module docstring promises: constructed inputs only.
