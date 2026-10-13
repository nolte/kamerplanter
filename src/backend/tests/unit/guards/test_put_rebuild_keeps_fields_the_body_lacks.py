"""Class guard — an update route that rebuilds its model from the body resets what the body lacks.

A ``PUT``/``PATCH`` handler that builds ``Model(**body.model_dump())`` hands the
service a model whose every field the body schema does not declare sits at its
**default**. A merge-mode repository writes every non-``None`` value it is given,
so a ``False`` / ``[]`` / ``""`` default overwrites the stored value on each edit.
Measured on 2026-10-10: a system location type lost ``is_system`` (and with it the
delete guard), a substrate mix lost ``is_mix`` / ``mix_components``, a species its
``traits`` / ``pruning_months`` / ``green_manure_suitable``, a growth phase its
``is_recurring`` / ``kc_source`` — and, found first by PR #2212 (#2181), a site its
weather-source view, a location its place in the tree, a slot its occupancy.

**What it selects** — the same predicate as the class sweep of this change
(``put_rebuild_sweep.py``, 12 hits): every function under ``app/api`` decorated
with ``<router>.put(...)`` or ``<router>.patch(...)`` that calls a bare name with a
``**<param>.model_dump(...)`` splat, where ``<param>`` is a handler parameter
annotated with a bare name. The called name and the annotation are resolved in the
router module's namespace; when both are Pydantic models, the *missing* fields are
the model's minus the body schema's, minus the bookkeeping fields the repository
and the route manage (:data:`_BOOKKEEPING`) and minus every field the call passes
explicitly (``Site(**body.model_dump(), tenant_key=...)``). A handler with a
missing field is a hit. Routers mounted with ``include_router`` are covered
because the scan walks the *files*, not the mounted route table; that every
``put``/``patch`` route lives under ``app/api`` is checked below.

**What every hit must have** — a decision for each missing field:

* the owning service takes it from the stored record through
  :func:`~app.domain.services.fields_kept_on_edit.keep_stored_fields` — the
  handler is in :data:`_KEPT_BY_SERVICE`, and the field is in the tuple the
  service passes; or
* a written verdict in :data:`_DECIDED`.

An unlisted hit fails, so does a missing field without a decision, and so does a
stale entry (a handler that is no longer a hit, a field that is no longer missing).
A field a service keeps must **not** be a body field — otherwise the body's value
would be silently replaced by the stored one, the inverse defect.

**Spellings it does not select**, measured with a wider probe over the same
handlers (any ``**`` splat or ``model_validate(... model_dump ...)``): 21 sites, of
which the 12 hits, two rebuilds with no missing field (``update_family``,
``update_protocol``) and seven that build a *response* or call a service with
keyword arguments. Not selected at all: a dump bound to a local first
(``data = body.model_dump(); Model(**data)``), ``Model.model_validate(body...)``,
an ``Annotated[...]`` body annotation, and a model built inside the service from a
body passed through — none occurs in a ``put``/``patch`` handler today.
"""

from __future__ import annotations

import ast
import enum
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from app.domain.services.location_type_service import LOCATION_TYPE_FIELDS_KEPT_ON_EDIT
from app.domain.services.phase_service import GROWTH_PHASE_FIELDS_KEPT_ON_EDIT
from app.domain.services.species_service import SPECIES_FIELDS_KEPT_ON_EDIT
from app.domain.services.substrate_service import SUBSTRATE_FIELDS_KEPT_ON_EDIT
from tests.support.execution_guards import find_project_root

_BACKEND = find_project_root(Path(__file__))
_API = _BACKEND / "app" / "api"

#: Fields the repository (``_key``, timestamps) or the route / service (ownership,
#: authorship) set on every write — identical to the sweep's set.
_BOOKKEEPING = frozenset({"key", "tenant_key", "created_at", "updated_at", "created_by", "updated_by", "id"})

#: The smallest number of hits the scan found when it was written. Fewer means the
#: selector broke (or a repair removed the rebuild — then lower it on purpose).
_MIN_HITS = 12


@dataclass(frozen=True)
class _Hit:
    handler: str  # "app/api/v1/<...>/router.py::<function>"
    model: type[BaseModel]
    schema: type[BaseModel]
    missing: frozenset[str]


def _route_decorated(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("put", "patch")
        for d in fn.decorator_list
    )


def _rebuild_hits(label: str, tree: ast.Module, resolve: Callable[[str], object]) -> list[_Hit]:
    """The sweep's predicate, applied to one parsed module; ``resolve`` reads its namespace."""
    hits: list[_Hit] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or not _route_decorated(fn):
            continue
        annotations = {a.arg: a.annotation for a in fn.args.args + fn.args.kwonlyargs}
        for call in ast.walk(fn):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
                continue
            for kw in call.keywords:
                value = kw.value
                if not (
                    kw.arg is None
                    and isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and value.func.attr == "model_dump"
                    and isinstance(value.func.value, ast.Name)
                ):
                    continue
                annotation = annotations.get(value.func.value.id)
                if not isinstance(annotation, ast.Name):
                    continue
                model, schema = resolve(call.func.id), resolve(annotation.id)
                if model is None or schema is None or not hasattr(model, "model_fields"):
                    continue
                explicit = {other.arg for other in call.keywords if other.arg}
                missing = set(model.model_fields) - set(schema.model_fields) - _BOOKKEEPING - explicit
                if missing:
                    hits.append(_Hit(f"{label}::{fn.name}", model, schema, frozenset(missing)))  # type: ignore[arg-type]
    return hits


def _scan_api() -> list[_Hit]:
    hits: list[_Hit] = []
    for path in sorted(_API.rglob("*.py")):
        relative = path.relative_to(_BACKEND)
        module_name = ".".join(relative.with_suffix("").parts)

        def resolve(name: str, module_name: str = module_name) -> object:
            return getattr(import_module(module_name), name, None)

        hits.extend(_rebuild_hits(relative.as_posix(), ast.parse(path.read_text()), resolve))
    return hits


class _Verdict(enum.Enum):
    KEPT = "the route or the service takes it from the stored record"
    DERIVED = "the model or the service derives it from fields the body carries"
    NONE_IN_MERGE_MODE = "defaults to None, and the merge-mode repository drops a None"
    NEVER_WRITTEN = "no server path writes it, so the default is the stored value"


@dataclass(frozen=True)
class _Decision:
    verdict: _Verdict
    reason: str
    #: For NONE_IN_MERGE_MODE: the repository class whose ``update`` writes the model.
    repository: type[BaseArangoRepository] | None = None


#: Handlers whose service keeps the body-less fields through ``keep_stored_fields``.
_KEPT_BY_SERVICE: dict[str, tuple[str, ...]] = {
    "app/api/v1/species/router.py::update_species": SPECIES_FIELDS_KEPT_ON_EDIT,
    "app/api/v1/growth_phases/router.py::update_phase": GROWTH_PHASE_FIELDS_KEPT_ON_EDIT,
    "app/api/v1/location_types/router.py::update_location_type": LOCATION_TYPE_FIELDS_KEPT_ON_EDIT,
    "app/api/v1/substrates/router.py::update_substrate": SUBSTRATE_FIELDS_KEPT_ON_EDIT,
}

#: Repaired in SiteService by PR #2212 (#2181), pinned in
#: tests/api/test_site_edit_keeps_server_maintained_fields.py. Until it merges, the four
#: fields are still reset — this registry records the decision, not the code.
_PR_2212 = "Repaired by PR #2212 (#2181) in SiteService."

#: The measured verdict for every other missing field, per handler.
_DECIDED: dict[str, dict[str, _Decision]] = {
    "app/api/v1/species/router.py::update_species": {
        "scientific_name_normalized": _Decision(
            _Verdict.DERIVED, "Species' model validator derives it from scientific_name, which the body carries."
        ),
    },
    "app/api/v1/cultivars/router.py::update_cultivar": {
        "origin": _Decision(_Verdict.KEPT, "SpeciesService.update_cultivar sets it from the stored cultivar."),
        "watering_guide_override": _Decision(
            _Verdict.NONE_IN_MERGE_MODE,
            "Written by the cultivar seed and migration v0050; the cultivar view of ArangoSpeciesRepository merges.",
            BaseArangoRepository,
        ),
    },
    "app/api/v1/lifecycle_configs/router.py::update_lifecycle": {
        field: _Decision(
            _Verdict.NONE_IN_MERGE_MODE,
            "REQ-003 bounds no API body carries; ArangoLifecycleRepository merges — measured, the payload omits them.",
            ArangoLifecycleRepository,
        )
        for field in ("cycle_restart_phase_order", "expected_productive_years", "first_bearing_year", "max_seasons")
    },
    "app/api/v1/profiles/router.py::update_requirement_profile": {
        field: _Decision(
            _Verdict.NONE_IN_MERGE_MODE,
            "Seed-only profile values; the requirement-profile view is a plain merge-mode repository.",
            BaseArangoRepository,
        )
        for field in ("far_red_fraction", "photosynthesis_temp_opt_c", "vpd_sensitivity", "vpd_threshold_kpa")
    },
    "app/api/v1/profiles/router.py::update_nutrient_profile": {
        field: _Decision(
            _Verdict.NONE_IN_MERGE_MODE,
            "Seed-only micronutrient targets; the nutrient-profile view is a plain merge-mode repository.",
            BaseArangoRepository,
        )
        for field in ("copper_ppm", "manganese_ppm", "molybdenum_ppm", "zinc_ppm")
    },
    "app/api/v1/substrates/router.py::update_batch": {
        "cycles_used": _Decision(
            _Verdict.NEVER_WRITTEN,
            "Read by the EC budget and the reuse check, written by no server path: it is 0 in every "
            "stored batch. The first writer must add it to the batch update's kept fields.",
        ),
        **{
            field: _Decision(
                _Verdict.NONE_IN_MERGE_MODE,
                "The batch view of ArangoSubstrateRepository is a plain merge-mode repository.",
                BaseArangoRepository,
            )
            for field in ("ec_current_ms", "last_amended", "ph_current")
        },
    },
    "app/api/v1/sites/tenant_router.py::update_site": {
        "weather_source_priority": _Decision(_Verdict.KEPT, _PR_2212),
        **{
            field: _Decision(
                _Verdict.KEPT,
                "The route takes them from the stored site unless the body sets a manual hardiness_zone, "
                "which replaces the derived provenance on purpose (REQ-039).",
            )
            for field in ("hardiness_zone_resolved_at", "hardiness_zone_source", "mean_annual_minimum_c")
        },
    },
    "app/api/v1/locations/tenant_router.py::update_location": {
        "depth": _Decision(_Verdict.DERIVED, _PR_2212),
        "path": _Decision(_Verdict.DERIVED, _PR_2212),
    },
    "app/api/v1/slots/tenant_router.py::update_slot": {
        "currently_occupied": _Decision(_Verdict.KEPT, _PR_2212),
        "last_sanitization": _Decision(
            _Verdict.NONE_IN_MERGE_MODE,
            "No server path writes it; the slot view of ArangoSiteRepository is a plain merge-mode repository.",
            BaseArangoRepository,
        ),
    },
}


@pytest.fixture(scope="module")
def hits() -> list[_Hit]:
    return _scan_api()


def test_the_scan_finds_the_measured_rebuilds(hits: list[_Hit]) -> None:
    assert len(hits) >= _MIN_HITS, [h.handler for h in hits]


def test_a_synthetic_rebuild_is_flagged_and_its_missing_field_named() -> None:
    """The selector itself, on a handler written for it — and its two negative arms."""

    class Model(BaseModel):
        key: str | None = None
        name: str
        is_system: bool = False
        owner: str = ""

    class Body(BaseModel):
        name: str

    source = textwrap.dedent(
        """
        @router.put("/{key}")
        def update_thing(key: str, body: Body):
            return service.update(key, Model(**body.model_dump()))

        @router.put("/{key}/owned")
        def update_owned(key: str, body: Body):
            return service.update(key, Model(**body.model_dump(), owner="x", is_system=False))

        @router.post("")
        def create_thing(body: Body):
            return service.create(Model(**body.model_dump()))
        """
    )
    namespace = {"Model": Model, "Body": Body}

    found = _rebuild_hits("synthetic.py", ast.parse(source), namespace.get)

    assert [(h.handler, h.missing) for h in found] == [("synthetic.py::update_thing", {"is_system", "owner"})]


def test_every_put_and_patch_route_lives_under_app_api() -> None:
    """The scan walks ``app/api``; a route decorated elsewhere would be outside it."""
    outside = []
    for path in sorted((_BACKEND / "app").rglob("*.py")):
        if _API in path.parents:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _route_decorated(node):
                outside.append(f"{path.relative_to(_BACKEND)}::{node.name}")
    assert outside == []


def test_every_field_a_rebuild_resets_is_decided(hits: list[_Hit]) -> None:
    undecided: dict[str, list[str]] = {}
    for hit in hits:
        decided = set(_KEPT_BY_SERVICE.get(hit.handler, ())) | set(_DECIDED.get(hit.handler, {}))
        if hit.missing - decided:
            undecided[hit.handler] = sorted(hit.missing - decided)
    assert undecided == {}, (
        "These update routes rebuild the model from the body and reset the listed fields to their "
        "defaults. Keep them in the owning service with keep_stored_fields (and add the handler to "
        "_KEPT_BY_SERVICE), or record the measured verdict in _DECIDED."
    )


def test_no_entry_is_stale(hits: list[_Hit]) -> None:
    by_handler = {hit.handler: hit for hit in hits}
    stale_handlers = sorted((set(_KEPT_BY_SERVICE) | set(_DECIDED)) - set(by_handler))
    stale_fields = {
        handler: sorted(set(fields) - by_handler[handler].missing)
        for handler, fields in _DECIDED.items()
        if handler in by_handler and set(fields) - by_handler[handler].missing
    }
    assert (stale_handlers, stale_fields) == ([], {})


def test_a_field_a_service_keeps_is_not_a_body_field(hits: list[_Hit]) -> None:
    """The inverse defect: a kept field the body *does* carry would drop the client's value."""
    by_handler = {hit.handler: hit for hit in hits}
    editable_but_kept = {
        handler: sorted(set(kept) & set(by_handler[handler].schema.model_fields))
        for handler, kept in _KEPT_BY_SERVICE.items()
        if handler in by_handler and set(kept) & set(by_handler[handler].schema.model_fields)
    }
    assert editable_but_kept == {}


def test_a_none_in_merge_mode_verdict_holds(hits: list[_Hit]) -> None:
    """Re-derive the two premises of the verdict instead of trusting its text."""
    by_handler = {hit.handler: hit for hit in hits}
    broken = []
    for handler, fields in _DECIDED.items():
        for field, decision in fields.items():
            if decision.verdict is not _Verdict.NONE_IN_MERGE_MODE:
                continue
            model = by_handler[handler].model
            if model.model_fields[field].get_default(call_default_factory=True) is not None:
                broken.append(f"{handler}::{field} does not default to None")
            if decision.repository is None or decision.repository._update_is_full_replace:
                broken.append(f"{handler}::{field} is written by a full-replace repository")
    assert broken == []
