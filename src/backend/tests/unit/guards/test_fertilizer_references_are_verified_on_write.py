"""#1713 — a fertilizer key that gets stored is checked on the way in, derived not listed.

The write-side counterpart of ``test_tenant_scoped_reads_are_derived.py`` (#1708).
#1713 found every writer of a fertilizer reference storing whatever key arrived,
so the question for a guard is not "do the six known writers check?" — the
integration test answers that — but "does a *new* writer check?". A hand list of
writers is the opt-in shape this repository keeps paying for (#948, #1402), so
both halves are derived:

**Which models carry a fertilizer reference.** Every Pydantic model under
``app/domain/models`` with a field named ``fertilizer_key(s)`` or ``product_key``
(the latter only exists on the fertilizer snapshots), and — transitively — every
model with a field whose annotation reaches one of those. That yields the line
models (``WateringLogFertilizer``, ``FertilizerDosage`` …), their containers
(``DeliveryChannel``) and the persisted roots (``WateringLog``,
``NutrientPlanPhaseEntry`` …). :data:`EXPECTED_ROOTS` pins the roots as a floor, so
a reader that stopped seeing them cannot pass by finding nothing.

**Where such a model is built with a reference in it.** Every call in ``app/``
(outside ``domain/models``, ``data_access`` and ``migrations``) that constructs one
of those models and passes a reference-bearing field by keyword — or a ``**``
splat, which can carry one. A construction that names no such field stores no
reference (``WateringLog(..., notes=...)`` after a task completion) and is not a
site; that is decided per call, not listed.

**The rule.** The function holding a site must reach a check within two resolved
calls of the typed call graph (``tests/unit/api/_write_call_graph.py``): itself,
a callee (the route handing the model to its service), or a callee's callee (the
service's own helper). A check is ``assert_fertilizers_visible`` /
``require_visible_fertilizer`` from ``app/domain/services/fertilizer_references.py``,
or ``get_fertilizer`` called *with* a tenant — the catalogue read that answers 404
for a foreign product, which the stock and MCP paths use.

**What this does not see**, named rather than discovered later:

* a key stored as a **bare argument**, with no model built — the channel
  assignment (``add_fertilizer_to_channel``) and the incompatibility edge
  (``add_incompatibility``). Both are pinned by
  ``tests/integration/test_fertilizer_reference_tenant_visibility.py``;
* a key reaching a writer inside a **dict** (``update_phase_entry(data)``), for the
  same reason and with the same pin;
* a check reached through an **unrelated** callee within the two hops: the rule
  proves a check is on the path, not that it covers the key that is stored;
* a construction through a receiver the call graph could not type counts as not
  reaching its callee — that fails loudly rather than passing.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import types
import typing
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

import app.domain.models as models_pkg
from tests.unit.api._write_call_graph import FunctionNode, call_graph

#: A field that stores a key into the fertilizer catalogue.
REFERENCE_FIELD_NAMES = frozenset({"fertilizer_key", "fertilizer_keys", "product_key"})

#: The persisted models measured on 2026-09-24 as carrying a reference. A floor,
#: not the rule: the derivation below must find at least these.
EXPECTED_ROOTS = frozenset(
    {"WateringLog", "FeedingEvent", "WateringEvent", "TankFillEvent", "NutrientPlanPhaseEntry", "FertilizerStock"}
)

CHECK_FUNCTIONS = frozenset({"assert_fertilizers_visible", "require_visible_fertilizer"})

#: Module prefixes whose constructions are not writes of caller input: the models
#: themselves, repositories rebuilding a model from a stored row, and seeds.
_OUT_OF_SCOPE = ("app.domain.models", "app.data_access", "app.migrations")


def _model_classes() -> dict[str, type[BaseModel]]:
    found: dict[str, type[BaseModel]] = {}
    for info in pkgutil.iter_modules(models_pkg.__path__):
        module = importlib.import_module(f"{models_pkg.__name__}.{info.name}")
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == module.__name__:
                found[value.__name__] = value
    return found


def _nested_models(annotation: object) -> set[type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return {annotation}
    out: set[type[BaseModel]] = set()
    if isinstance(annotation, types.UnionType) or typing.get_origin(annotation) is not None:
        for arg in typing.get_args(annotation):
            out |= _nested_models(arg)
    return out


@dataclass(frozen=True)
class Bearing:
    models: frozenset[str]
    fields: frozenset[str]
    roots: frozenset[str]


def derive_bearing(classes: dict[str, type[BaseModel]]) -> Bearing:
    """Models carrying a fertilizer reference, the fields that carry it, and the persisted roots."""
    bearing = {name for name, cls in classes.items() if REFERENCE_FIELD_NAMES & set(cls.model_fields)}
    fields = set(REFERENCE_FIELD_NAMES)
    changed = True
    while changed:
        changed = False
        for name, cls in classes.items():
            for field_name, info in cls.model_fields.items():
                if {m.__name__ for m in _nested_models(info.annotation)} & bearing:
                    fields.add(field_name)
                    if name not in bearing:
                        bearing.add(name)
                        changed = True
    roots = {
        name
        for name in bearing
        if "key" in classes[name].model_fields and classes[name].model_fields["key"].alias == "_key"
    }
    return Bearing(frozenset(bearing), frozenset(fields), frozenset(roots))


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def is_check_call(call: ast.Call) -> bool:
    name = _callee_name(call)
    if name in CHECK_FUNCTIONS:
        return True
    # The catalogue read with a tenant: answers 404 for a foreign product.
    return name == "get_fertilizer" and (len(call.args) >= 2 or any(k.arg == "tenant_key" for k in call.keywords))


def is_reference_site(call: ast.Call, bearing: Bearing) -> bool:
    """A construction of a bearing model that can put a reference into it."""
    if not isinstance(call.func, ast.Name) or call.func.id not in bearing.models:
        return False
    return any(k.arg is None or k.arg in bearing.fields for k in call.keywords)


def reaches_check(fn: FunctionNode, graph, depth: int = 2) -> bool:
    if any(is_check_call(call) for call in fn._call_nodes):
        return True
    if depth == 0:
        return False
    return any(
        reaches_check(callee, graph, depth - 1)
        for callee in fn.callees
        if (fn.id, callee.id) not in graph.fallback_edges
    )


def unchecked_sites(graph, bearing: Bearing) -> list[str]:
    missing = []
    for fn in graph.functions:
        if not fn.module.startswith("app.") or fn.module.startswith(_OUT_OF_SCOPE):
            continue
        sites = [call for call in fn._call_nodes if is_reference_site(call, bearing)]
        if sites and not reaches_check(fn, graph):
            names = sorted({_callee_name(call) or "?" for call in sites})
            missing.append(f"{fn.id} builds {names} and reaches no fertilizer visibility check")
    return missing


@pytest.fixture(scope="module")
def bearing() -> Bearing:
    return derive_bearing(_model_classes())


class TestTheDerivationIsNotVacuous:
    def test_the_measured_roots_are_found(self, bearing: Bearing) -> None:
        assert bearing.roots >= EXPECTED_ROOTS, sorted(EXPECTED_ROOTS - bearing.roots)

    def test_the_container_fields_are_followed(self, bearing: Bearing) -> None:
        # ``delivery_channels -> fertilizer_dosages -> fertilizer_key``: two hops.
        assert {"fertilizers_used", "fertilizer_dosages", "delivery_channels"} <= bearing.fields

    def test_there_are_sites_to_check(self, bearing: Bearing) -> None:
        graph = call_graph()
        sites = [
            fn.id
            for fn in graph.functions
            if fn.module.startswith("app.")
            and not fn.module.startswith(_OUT_OF_SCOPE)
            and any(is_reference_site(call, bearing) for call in fn._call_nodes)
        ]
        # Measured 2026-09-24: routes for logs, events, fills, entries, stocks;
        # the two confirmation services; the MCP feeding tool.
        assert len(sites) >= 9, sites


class TestEveryStoredFertilizerReferenceIsChecked:
    def test_every_site_reaches_a_check(self, bearing: Bearing) -> None:
        assert unchecked_sites(call_graph(), bearing) == []


class TestTheRuleFires:
    """Falsification on synthetic calls: the predicates are the production ones."""

    @staticmethod
    def _call(source: str) -> ast.Call:
        node = ast.parse(source, mode="eval").body
        assert isinstance(node, ast.Call)
        return node

    def test_a_construction_with_a_reference_is_a_site(self, bearing: Bearing) -> None:
        assert is_reference_site(self._call("WateringLog(tenant_key=t, fertilizers_used=f)"), bearing)
        assert is_reference_site(self._call("FeedingEvent(**body.model_dump())"), bearing)
        assert is_reference_site(
            self._call("FertilizerSnapshot(product_key=k, product_name=n, ml_per_liter=1)"), bearing
        )

    def test_a_construction_without_one_is_not(self, bearing: Bearing) -> None:
        assert not is_reference_site(self._call("WateringLog(tenant_key=t, notes=n)"), bearing)
        assert not is_reference_site(self._call("Task(**body.model_dump())"), bearing)

    def test_a_tenantless_catalogue_read_is_not_a_check(self) -> None:
        assert is_check_call(self._call("service.get_fertilizer(key, tenant_key=t)"))
        assert is_check_call(self._call("self.get_fertilizer(key, tenant_key)"))
        assert not is_check_call(self._call("self.get_fertilizer(key)"))

    def test_an_unchecked_writer_is_reported(self, bearing: Bearing) -> None:
        """The whole rule, on a graph where one site's function reaches nothing."""
        site = FunctionNode("app.domain.services.fake", "FakeService.create", "create", 1, "FakeService")
        site._call_nodes = [self._call("WateringLog(tenant_key=t, fertilizers_used=f)")]
        graph = types.SimpleNamespace(functions=[site], fallback_edges=set())

        assert unchecked_sites(graph, bearing) == [
            "app.domain.services.fake::FakeService.create builds ['WateringLog'] "
            "and reaches no fertilizer visibility check"
        ]

        helper = FunctionNode("app.domain.services.fake", "FakeService._check", "_check", 2, "FakeService")
        helper._call_nodes = [self._call("assert_fertilizers_visible(repo, keys, tenant_key=t, field=f, owner=o)")]
        site.callees = [helper]
        assert unchecked_sites(graph, bearing) == []
