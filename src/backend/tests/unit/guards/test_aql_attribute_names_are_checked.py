"""MT-053 (#2144): no attribute name reaches AQL text without passing the field check.

AQL binds values (``@x``) and collections (``@@x``), not attribute names, so an
attribute is interpolated: ``f"doc.{field} == @val{i}"``. ``AQLBuilder.filter``
checked every such name against ``_FIELD_RE``; seven repositories built the same
clause by hand from a ``filters`` dict and checked nothing — a key like
``"x) OR true //"`` would have rewritten the query. Every caller passes router
constants today, so it was defence in depth, not a reachable injection.

Now there is one check, :func:`app.data_access.arango.query_builder.aql_field`,
and this guard holds that **every** interpolation directly after an attribute
access (``<name>.{…}``) in an f-string under ``app/data_access`` is a call to it.
``query_builder.py`` itself is the one exception: ``AQLBuilder.filter``/``sort``
validate the name with the same expression before interpolating.

Spellings this does not see: an attribute assembled outside the f-string and
interpolated whole (``f"FILTER {clause}"``), ``str.format``/``%`` formatting, and
``app/migrations/versions`` (applied sources are frozen; their names are module
constants).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.data_access.arango.activity_repository import ArangoActivityRepository
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.arango.task_repository import ArangoTaskRepository

APP = Path(__file__).resolve().parents[3] / "app"
DATA_ACCESS = APP / "data_access"
_EXEMPT = {"arango/query_builder.py"}
_ATTRIBUTE_ACCESS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.$")
_HOSTILE = "x) OR true //"


def _unchecked_interpolations() -> tuple[list[str], int]:
    unchecked: list[str] = []
    seen = 0
    for path in sorted(DATA_ACCESS.rglob("*.py")):
        rel = path.relative_to(DATA_ACCESS).as_posix()
        if rel in _EXEMPT:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.JoinedStr):
                continue
            for before, value in zip(node.values, node.values[1:], strict=False):
                if not (
                    isinstance(value, ast.FormattedValue)
                    and isinstance(before, ast.Constant)
                    and isinstance(before.value, str)
                    and _ATTRIBUTE_ACCESS.search(before.value)
                ):
                    continue
                seen += 1
                expr = value.value
                checked = isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "aql_field"
                if not checked:
                    unchecked.append(f"{rel}:{node.lineno} {{{ast.unparse(expr)}}}")
    return unchecked, seen


def test_every_interpolated_attribute_name_goes_through_aql_field() -> None:
    unchecked, seen = _unchecked_interpolations()

    assert seen >= 10, "the sweep found almost no interpolation — a blind scan would pass vacuously"
    assert unchecked == [], (
        "An attribute name is interpolated into AQL without aql_field() (MT-053):\n  " + "\n  ".join(unchecked)
    )


@pytest.mark.parametrize("name", ["plant_key", "tenant_key", "a.b", "_x1"])
def test_aql_field_admits_identifiers_and_dotted_paths(name: str) -> None:
    assert aql_field(name) == name


@pytest.mark.parametrize("name", [_HOSTILE, "", "1x", "a b", "a-b", "doc.x == 1 //"])
def test_aql_field_refuses_anything_else(name: str) -> None:
    with pytest.raises(ValueError, match="Invalid AQL field name"):
        aql_field(name)


class _Db:
    """Executes nothing: a hostile name must be refused before any AQL is sent."""

    def __init__(self) -> None:
        self.executed: list[str] = []

        class _Aql:
            def execute(inner, query, bind_vars=None):  # noqa: N805, ANN001
                self.executed.append(query)
                return iter([0])

        self.aql = _Aql()

    def collection(self, _name: str):  # noqa: ANN202
        raise AssertionError("no collection access expected")


@pytest.mark.parametrize(
    "call",
    [
        lambda db: ArangoActivityRepository(db).get_all(filters={_HOSTILE: 1}, tenant_key="t1"),
        lambda db: ArangoFertilizerRepository(db).get_all(filters={_HOSTILE: 1}, tenant_key="t1"),
        lambda db: ArangoNutrientPlanRepository(db).get_all(filters={_HOSTILE: 1}, tenant_key="t1"),
        lambda db: ArangoPlantingRunRepository(db).get_all(filters={_HOSTILE: 1}, tenant_key="t1"),
        lambda db: ArangoTankRepository(db).get_all(filters={_HOSTILE: 1}, tenant_key="t1"),
        lambda db: ArangoTaskRepository(db).get_all_tasks(filters={_HOSTILE: 1}, tenant_key="t1"),
    ],
    ids=["activity", "fertilizer", "nutrient_plan", "planting_run", "tank", "task"],
)
def test_a_hostile_filter_key_is_refused_before_any_query(call) -> None:  # noqa: ANN001
    db = _Db()

    with pytest.raises(ValueError, match="Invalid AQL field name"):
        call(db)

    assert db.executed == []
