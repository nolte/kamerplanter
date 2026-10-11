"""#2138 (REQ-056 AK-29, AK-31) — the tenant export is the tenant-erasure inventory, and every key is declared.

Two declarations keep a tenant archive honest, and both are derived here rather
than remembered:

* **What the archive holds (AK-29).** Every collection of
  :attr:`TenantErasureEngine.INVENTORY` is either exported or named in
  :attr:`TenantExportEngine.EXCLUDED` with a reason — in both directions: a new
  inventory collection fails until someone decides, and an exclusion of a
  collection the inventory no longer has fails as stale. What the deletion of a
  tenant reaches is what belongs to it; the export takes exactly that.
* **Which fields are references (AK-31).** An import gives every document a new
  key, so every field naming another document must be rewritten. The models of
  every exported collection are read (the #1708 derivation maps collections to
  models), every ``*_key`` / ``*_keys`` field — nested ones through lists and
  sub-models included — must have a declaration in
  :meth:`TenantExportEngine.references_of`. An undeclared one would be written
  unchanged by an import, pointing at whatever row of whatever tenant carries
  that key in the target database; the import refuses such a document at run
  time as well (``IMPORT_UNDECLARED_REFERENCE``).

What this does not see: a field written by raw AQL that no model declares (the
run-time refusal covers it), and a reference whose name does not end in ``_key``
(``photo_refs`` and the account fields like ``created_by`` are declared by hand
and from the account erasure respectively).
"""

from __future__ import annotations

import importlib
import types
import typing
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.engines.tenant_export_engine import TenantExportEngine
from app.domain.models.ha_publish_setting import HaPublishSetting
from tests.support.execution_guards import find_project_root
from tests.unit.guards.test_tenant_scoped_reads_are_derived import build_inventory

_APP = find_project_root(Path(__file__)) / "app"

#: Collections the derivation maps to no model, with the model (or the reason there is none).
_MODELS_BY_HAND: dict[str, type[BaseModel] | str] = {
    "ha_publish_settings": HaPublishSetting,  # written by a raw repository, the model is the shape
    "diagnosis_requests": "declared and indexed in collections.py; no code path writes it (inventory comment)",
}


def coverage_findings(inventory: list[str], excluded: dict[str, str]) -> list[str]:
    """Every inventory collection exported or excluded with a reason; no stale exclusion."""
    findings = [f"{name}: excluded without a reason" for name, reason in sorted(excluded.items()) if not reason]
    findings += [
        f"{name}: excluded but not in the tenant-erasure inventory" for name in sorted(set(excluded) - set(inventory))
    ]
    return findings


def _inner_models(annotation: object) -> list[type[BaseModel]]:
    origin = typing.get_origin(annotation)
    if origin in (list, set, tuple, frozenset, dict, typing.Union, types.UnionType):
        return [model for arg in typing.get_args(annotation) for model in _inner_models(arg)]
    if origin is typing.Annotated:
        return _inner_models(typing.get_args(annotation)[0])
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    return []


def reference_paths(model: type[BaseModel], prefix: str = "", seen: frozenset[type] = frozenset()) -> set[str]:
    """Every ``*_key`` / ``*_keys`` field path of *model*, through nested models and lists."""
    paths: set[str] = set()
    for name, field in model.model_fields.items():
        alias = field.alias or name
        if alias.startswith("_"):
            continue
        path = f"{prefix}{alias}"
        if TenantExportEngine.looks_like_reference(alias):
            paths.add(path)
        for inner in _inner_models(field.annotation):
            if inner not in seen:
                paths |= reference_paths(inner, f"{path}.", seen | {model})
    return paths


def undeclared_findings(collection: str, paths: set[str]) -> list[str]:
    declared = TenantExportEngine.references_of(collection)
    return [f"{collection}.{path}: not declared as a reference (or opaque)" for path in sorted(paths - set(declared))]


@pytest.fixture(scope="module")
def models_by_collection() -> dict[str, list[type[BaseModel]]]:
    derived = build_inventory(_APP)
    out: dict[str, list[type[BaseModel]]] = {}
    for collection in TenantExportEngine.exported_collections():
        classes: list[type[BaseModel]] = []
        for module_name, class_name in sorted(derived.collection_models.get(collection, set())):
            cls = getattr(importlib.import_module(module_name), class_name, None)
            if isinstance(cls, type) and issubclass(cls, BaseModel):
                classes.append(cls)
        by_hand = _MODELS_BY_HAND.get(collection)
        if isinstance(by_hand, type):
            classes.append(by_hand)
        out[collection] = classes
    return out


class TestTheArchiveIsTheInventory:
    def test_every_inventory_collection_is_exported_or_excluded(self) -> None:
        inventory = [entry.collection for entry in TenantErasureEngine.INVENTORY]
        assert coverage_findings(inventory, TenantExportEngine.EXCLUDED) == []
        exported = set(TenantExportEngine.exported_collections())
        assert exported | set(TenantExportEngine.EXCLUDED) == set(inventory)
        assert exported & set(TenantExportEngine.EXCLUDED) == set()

    def test_the_declarations_validate(self) -> None:
        TenantExportEngine.validate()

    def test_not_vacuous(self) -> None:
        # Measured 2026-10-11: 76 of 97 inventory collections are exported.
        assert len(TenantExportEngine.exported_collections()) >= 70
        assert "plant_instances" in TenantExportEngine.exported_collections()

    def test_credentials_and_audit_logs_are_never_exported(self) -> None:
        # REQ-056 §8.3 / AK-30 — the classes the spec names, held by name.
        for name in (
            "api_keys",
            "invitations",
            "ai_provider_configs",
            "inventree_connections",
            "security_audit_log",
            "calendar_feeds",
            "memberships",
            "tenant_export_requests",
        ):
            assert name in TenantExportEngine.EXCLUDED, name


class TestEveryReferenceIsDeclared:
    def test_every_key_field_of_every_exported_model_is_declared(self, models_by_collection) -> None:
        findings: list[str] = []
        for collection, classes in models_by_collection.items():
            for cls in classes:
                findings += undeclared_findings(collection, reference_paths(cls))
        assert findings == [], "\n".join(findings)

    def test_every_exported_collection_has_a_model_or_a_reason(self, models_by_collection) -> None:
        unmapped = [c for c, classes in models_by_collection.items() if not classes and c not in _MODELS_BY_HAND]
        assert unmapped == []

    def test_the_reader_sees_nested_fields(self, models_by_collection) -> None:
        # Non-vacuity: a nested reference the reader must find (inside a list of sub-models).
        paths = set().union(*(reference_paths(cls) for cls in models_by_collection["nutrient_plan_phase_entries"]))
        assert "delivery_channels.fertilizer_dosages.fertilizer_key" in paths


class TestTheDetectorFires:
    def test_a_new_inventory_collection_needs_a_decision(self) -> None:
        assert coverage_findings(["sites"], {"gone": "was secret"}) == [
            "gone: excluded but not in the tenant-erasure inventory"
        ]

    def test_an_undeclared_nested_key_is_found(self) -> None:
        class Inner(BaseModel):
            brand_new_key: str

        class Outer(BaseModel):
            site_key: str
            parts: list[Inner] = []

        assert undeclared_findings("sites", reference_paths(Outer)) == [
            "sites.parts.brand_new_key: not declared as a reference (or opaque)"
        ]
