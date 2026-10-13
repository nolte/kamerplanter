"""#2038 — an MCP tool reads only attributes the model it was handed actually has.

**The defect class.** ``GetLocation`` read ``location.type`` and five
``getattr(location, "<literal>")`` fields that ``Location`` does not carry. The
attribute read raised ``AttributeError`` on every call; the ``getattr`` reads with
a default returned ``None`` forever (the model field is ``area_m2``, not
``area_sqm``). mypy could not say so: while ``ToolContext`` returned untyped
services the receiver was ``Any`` (#2040 typed it, which is how the defect
surfaced).

**What is asserted.** For every function under ``app/mcp_server/tools/``:

* a name assigned from ``ctx.<service>.<method>(...)`` is resolved to the
  pydantic model in that method's return annotation (``Model``, ``Model | None``,
  ``list[Model]``; a loop or comprehension target over a ``list[Model]`` is one
  ``Model``), the service class coming from the ``ToolContext`` property's
  return annotation;
* every ``<name>.<attr>`` load and every ``getattr(<name>, "<literal>")`` on such
  a name must name a field, alias, property or method of that model.

**What it cannot see**, so nobody reads its silence as coverage: a receiver that
reaches the tool through a helper's untyped parameter, a ``dict``-valued service
reply, a name rebound to a different type inside one function, a ``getattr`` with
a computed name, and a method whose return annotation is not a model. Those are
mypy's to catch once their receiver is typed. The scan reports how many reads it
resolved, and the non-vacuity tests below fail if that collapses or if the scan
stops flagging a read of an attribute the model lacks.

Measured 2026-10-04 on develop fec68ae88 plus the #2038 repair: 331 resolved
reads, 1 finding beside ``GetLocation`` (``GetDisease`` read ``description_de``
which ``Disease`` lacks; the value was always the ``description`` fallback).
"""

from __future__ import annotations

import ast
import importlib
import types
import typing
from pathlib import Path

from pydantic import BaseModel

import app.mcp_server.context as context_module

_APP = Path(context_module.__file__).resolve().parents[1]
_TOOLS = _APP / "mcp_server" / "tools"

#: The scan must resolve at least this many reads or it has stopped seeing them.
_MIN_RESOLVED_READS = 250


def _service_classes() -> dict[str, type]:
    """``ToolContext`` property name -> service class, from the property's return annotation."""

    tree = ast.parse(Path(context_module.__file__).read_text())
    imported: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            for alias in node.names:
                imported[alias.asname or alias.name] = (node.module, alias.name)
    classes: dict[str, type] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.returns is not None:
            name = ast.unparse(node.returns).strip("'\"")
            if name in imported:
                module, attr = imported[name]
                classes[node.name] = getattr(importlib.import_module(module), attr)
    return classes


def _model_of(annotation: object) -> tuple[type[BaseModel], bool] | None:
    """The pydantic model an annotation names and whether it is a ``list`` of it."""

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation, False
    origin = typing.get_origin(annotation)
    args = [a for a in typing.get_args(annotation) if a is not type(None)]
    if origin in (typing.Union, types.UnionType) and len(args) == 1:
        return _model_of(args[0])
    if origin is list and args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
        return args[0], True
    return None


def _model_attributes(model: type[BaseModel]) -> set[str]:
    aliases = {f.alias for f in model.model_fields.values() if f.alias}
    return set(model.model_fields) | aliases | {n for n in dir(model) if not n.startswith("_")}


def _call_model(call: ast.expr, services: dict[str, type]) -> tuple[type[BaseModel], bool] | None:
    """Resolve ``[await] ctx.<service>.<method>(...)`` to its return model."""

    if isinstance(call, ast.Await):
        call = call.value
    if not (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Attribute)
        and isinstance(call.func.value.value, ast.Name)
        and call.func.value.value.id == "ctx"
        and call.func.value.attr in services
    ):
        return None
    method = getattr(services[call.func.value.attr], call.func.attr, None)
    if method is None:
        return None
    try:
        hints = typing.get_type_hints(method)
    except Exception:  # an unresolvable annotation is a receiver the scan cannot see
        return None
    return _model_of(hints.get("return"))


def _bind(
    target: ast.expr,
    value: ast.expr,
    services: dict[str, type],
    one: dict[str, type[BaseModel]],
    many: dict[str, type[BaseModel]],
) -> None:
    if not isinstance(target, ast.Name):
        return
    hit = _call_model(value, services)
    if hit is None and isinstance(value, ast.Name) and value.id in many:
        hit = (many[value.id], True)
    if hit is not None:
        (many if hit[1] else one)[target.id] = hit[0]


def scan(source: str, services: dict[str, type]) -> tuple[int, list[str]]:
    """Return ``(resolved reads, findings)`` for one module's source."""

    resolved = 0
    findings: list[str] = []
    for fn in ast.walk(ast.parse(source)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        one: dict[str, type[BaseModel]] = {}
        many: dict[str, type[BaseModel]] = {}

        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                _bind(node.targets[0], node.value, services, one, many)
        for node in ast.walk(fn):
            iterations: list[tuple[ast.expr, ast.expr]] = []
            if isinstance(node, ast.For):
                iterations.append((node.target, node.iter))
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                iterations.extend((g.target, g.iter) for g in node.generators)
            for target, iterable in iterations:
                if not isinstance(target, ast.Name):
                    continue
                hit = _call_model(iterable, services)
                if hit is not None and hit[1]:
                    one[target.id] = hit[0]
                elif isinstance(iterable, ast.Name) and iterable.id in many:
                    one[target.id] = many[iterable.id]
        for node in ast.walk(fn):
            name: str | None = None
            attr: str | None = None
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and isinstance(node.value, ast.Name):
                name, attr = node.value.id, node.attr
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                name, attr = node.args[0].id, node.args[1].value
            if name is None or name not in one:
                continue
            resolved += 1
            if attr not in _model_attributes(one[name]):
                findings.append(f"line {node.lineno}: {name}.{attr} ({one[name].__name__} has no {attr!r})")
    return resolved, findings


def test_every_tool_read_names_an_attribute_the_model_has():
    services = _service_classes()
    total = 0
    findings: list[str] = []
    for path in sorted(_TOOLS.glob("*.py")):
        resolved, found = scan(path.read_text(), services)
        total += resolved
        findings.extend(f"{path.name} {f}" for f in found)
    assert total >= _MIN_RESOLVED_READS, f"the scan resolved only {total} reads"
    assert findings == []


def test_the_scan_flags_an_attribute_the_model_lacks():
    """Non-vacuity: the original #2038 spellings, as source, must be flagged."""

    source = (
        "async def run(ctx, args):\n"
        "    location = ctx.site_service.get_location(args.k, ctx.tenant_key)\n"
        "    a = location.type\n"
        "    b = getattr(location, 'area_sqm', None)\n"
        "    c = location.area_m2\n"
        "    d = getattr(location, 'frost_exposed', None)\n"
    )
    resolved, findings = scan(source, _service_classes())
    assert resolved == 4
    assert len(findings) == 2
    assert "location.type" in findings[0]
    assert "location.area_sqm" in findings[1]


def test_the_scan_follows_a_list_through_a_loop_and_a_comprehension():
    source = (
        "async def run(ctx, args):\n"
        "    locs = ctx.site_service.get_location_tree('k', tenant_key='t')\n"
        "    for s in locs:\n"
        "        s.nonexistent_a\n"
        "    return [x.nonexistent_b for x in ctx.site_service.get_location_tree('k', tenant_key='t')]\n"
    )
    _, findings = scan(source, _service_classes())
    assert [f.split(" ")[2] for f in findings] == ["s.nonexistent_a", "x.nonexistent_b"]
