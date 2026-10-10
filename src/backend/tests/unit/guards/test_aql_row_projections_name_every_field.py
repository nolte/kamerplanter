"""#2166 class guard: an AQL row projection hydrated into a model names every field that has a default.

``ArangoMembershipRepository.list_by_tenant`` built :class:`MemberInfo` from
``RETURN { key: …, role: …, is_active: … }`` — and left ``admin_scopes`` out.
The field has a default (``[]``), so nothing failed: the member list reported
*no scope* for every member, the ``management`` holder included, and the UI and
every API client read that as the truth. A required field left out raises on the
first read; a defaulted one silently reports its default. That is the class.

**The rule.** In ``app/``, a function whose AQL returns an object literal
(``RETURN { … }``) and that hydrates a model from a *whole cursor row* —
``Model(**row)`` or ``Model.model_validate(row)``, where ``row`` is the target of a
``for`` loop or comprehension in the same function — names every field of that
model which has a default (by field name or alias) in the object literal. A field
deliberately left to its default is listed in :data:`ALLOWED` with the reason.

Spellings this does NOT see
---------------------------

* a projection whose AQL is built by concatenating strings across statements
  (only string literals and f-string literal parts inside the function are read);
* a model hydrated from a nested key of the row (``Model(**row["entry"])``) — that
  is a whole document, not a projection;
* a model class not importable from the module that hydrates it.
"""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
ROOT = APP.parent

#: ``"path:function->Model.field"`` → why the projection leaves the field at its default.
ALLOWED: dict[str, str] = {}

_RETURN_OBJECT = re.compile(r"RETURN\s*\{")
_KEY = re.compile(r"(?:^|[,{\s])\"?([A-Za-z_][A-Za-z0-9_]*)\"?\s*:")


@dataclass(frozen=True)
class Projection:
    site: str
    model: type
    keys: frozenset[str]


def _strings(fn: ast.FunctionDef) -> list[str]:
    texts: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.JoinedStr):
            texts.append(
                "".join(p.value for p in node.values if isinstance(p, ast.Constant) and isinstance(p.value, str))
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            texts.append(node.value)
    return [t for t in texts if _RETURN_OBJECT.search(t)]


def _row_names(fn: ast.FunctionDef) -> set[str]:
    return {
        node.target.id
        for node in ast.walk(fn)
        if isinstance(node, ast.For | ast.comprehension) and isinstance(node.target, ast.Name)
    }


def _hydrated_models(fn: ast.FunctionDef) -> set[str]:
    rows = _row_names(fn)
    models: set[str] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and any(
            k.arg is None and isinstance(k.value, ast.Name) and k.value.id in rows for k in node.keywords
        ):
            models.add(node.func.id)
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "model_validate"
            and isinstance(node.func.value, ast.Name)
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in rows
        ):
            models.add(node.func.value.id)
    return models


@cache
def _projections() -> tuple[Projection, ...]:
    found: dict[tuple[str, str], set[str]] = {}
    classes: dict[tuple[str, str], type] = {}
    for path in sorted(APP.rglob("*.py")):
        module = None
        for fn in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(fn, ast.FunctionDef):
                continue
            texts = _strings(fn)
            models = _hydrated_models(fn) if texts else set()
            if not models:
                continue
            if module is None:
                module = importlib.import_module(".".join(path.relative_to(ROOT).with_suffix("").parts))
            site = f"{path.relative_to(ROOT).as_posix()}:{fn.name}"
            keys = {k for t in texts for k in _KEY.findall(t[_RETURN_OBJECT.search(t).end() :])}
            for name in models:
                cls = getattr(module, name, None)
                if cls is None or not hasattr(cls, "model_fields"):
                    continue
                found.setdefault((site, name), set()).update(keys)
                classes[(site, name)] = cls
    return tuple(Projection(key[0], classes[key], frozenset(keys)) for key, keys in sorted(found.items()))


def _missing(projection: Projection) -> list[str]:
    return [
        f"{projection.site}->{projection.model.__name__}.{name}"
        for name, field in projection.model.model_fields.items()
        if not field.is_required() and name not in projection.keys and (field.alias or name) not in projection.keys
    ]


def test_the_population_is_read():
    sites = {f"{p.site}->{p.model.__name__}" for p in _projections()}
    # Non-vacuity: the projection #2166 was found in is part of the population.
    assert "app/data_access/arango/membership_repository.py:list_by_tenant->MemberInfo" in sites


def test_every_row_projection_names_its_defaulted_fields():
    missing = [m for p in _projections() for m in _missing(p) if m not in ALLOWED]
    assert missing == [], (
        "An AQL row projection leaves a defaulted model field out — the field then silently reports its "
        f"default for every row (#2166). Name it in the RETURN object or decide it in ALLOWED: {missing}"
    )


def test_the_allow_list_stays_true():
    every = {m for p in _projections() for m in _missing(p)}
    assert [entry for entry in ALLOWED if entry not in every] == []
