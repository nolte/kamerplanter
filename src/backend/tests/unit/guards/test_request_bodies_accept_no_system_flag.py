"""#2027 follow-up — no request body a tenant can send carries ``is_system``.

``is_system`` marks a row the seed ships. Accepted from a tenant it locks the row
against its owner (every write path refuses an ``is_system`` row), lists it to every
tenant where a read trusts the flag (``get_system_activities``), and until the same
change kept it through the tenant erasure. ``POST /api/v1/t/{slug}/tasks/workflows``
accepted it until the #2027 review removed the field from ``WorkflowTemplateCreate``
— one schema, found by reading it.

**The class held here** is every request body of every write route of the assembled
app (walked through the nested ``_IncludedRouter`` wrappers, include-level
dependencies included), and every model nested in such a body: none may declare
``is_system`` or admit undeclared fields (``extra="allow"``, through which the flag
would pass), unless the route is gated by ``require_platform_admin`` — a platform
admin writes the global catalogue the seed writes — or is listed in
:data:`_ACCEPTED_WITH_REASON`. A listed route that stops matching fails too, so the
list cannot outlive its reason.
"""

from __future__ import annotations

import types
import typing
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.dependencies.utils import get_dependant
from fastapi.routing import APIRoute
from pydantic import BaseModel

_FLAG = "is_system"

_WRITE_METHODS = {"POST", "PUT", "PATCH"}

#: Write routes whose body may carry ``is_system`` although no platform-admin gate
#: protects them, each with the reason. Keyed ``(method, path)``.
_ACCEPTED_WITH_REASON: dict[tuple[str, str], str] = {}


def _routes(routes: list[Any], prefix: str = "", inherited: tuple[Any, ...] = ()) -> list[tuple[str, APIRoute, list]]:
    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            path = prefix + route.path_format
            out.append((path, route, [route.dependant, *(get_dependant(path=path, call=c) for c in inherited)]))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            calls = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + calls))
    return out


def _calls(dependants: list[Any]) -> set[Any]:
    found: set[Any] = set()
    stack = list(dependants)
    while stack:
        dependant = stack.pop()
        found.add(dependant.call)
        stack.extend(dependant.dependencies)
    return found


def _models_in(annotation: Any, seen: set[type[BaseModel]]) -> None:
    """Every ``BaseModel`` reachable from *annotation* (``X | None``, ``list[X]``, nested fields)."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if annotation in seen:
            return
        seen.add(annotation)
        for field in annotation.model_fields.values():
            _models_in(field.annotation, seen)
        return
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        _models_in(typing.get_args(annotation)[0], seen)
        return
    if origin is not None or isinstance(annotation, types.UnionType):
        for arg in typing.get_args(annotation):
            _models_in(arg, seen)


def _accepts_the_flag(model: type[BaseModel]) -> bool:
    return _FLAG in model.model_fields or model.model_config.get("extra") == "allow"


def _bodies_with_the_flag(app: Any) -> tuple[list[tuple[str, str, str]], int]:
    """``(method, path, model)`` of every non-admin write body that accepts the flag, and the body count."""
    from app.common.auth import require_platform_admin

    offenders: list[tuple[str, str, str]] = []
    bodies = 0
    for path, route, dependants in _routes(app.routes):
        methods = sorted(route.methods & _WRITE_METHODS)
        params = [param for dependant in dependants for param in dependant.body_params]
        if not methods or not params:
            continue
        bodies += 1
        if require_platform_admin in _calls(dependants):
            continue
        models: set[type[BaseModel]] = set()
        for param in params:
            _models_in(param.field_info.annotation, models)
        for model in sorted(models, key=lambda m: m.__qualname__):
            if _accepts_the_flag(model):
                offenders.extend((method, path, model.__qualname__) for method in methods)
    return offenders, bodies


def test_no_tenant_write_body_accepts_the_system_flag() -> None:
    from app.main import app

    offenders, bodies = _bodies_with_the_flag(app)
    found = {(method, path) for method, path, _ in offenders}
    unexplained = sorted(o for o in offenders if (o[0], o[1]) not in _ACCEPTED_WITH_REASON)
    stale = sorted(set(_ACCEPTED_WITH_REASON) - found)

    assert bodies > 200, bodies  # non-vacuity: the walk reaches the nested routers' bodies
    assert unexplained == [], (
        f"write bodies a tenant can send that carry {_FLAG!r} (only the seed or a platform admin writes it): "
        f"{unexplained}"
    )
    assert stale == [], f"listed routes that no longer accept {_FLAG!r} — drop the entry: {stale}"


class _Inner(BaseModel):
    is_system: bool = False


class _Wrapper(BaseModel):
    items: list[_Inner] | None = None


class _Loose(BaseModel):
    model_config = {"extra": "allow"}


class _Clean(BaseModel):
    name: str


def test_the_walk_flags_a_tenant_body_and_admits_an_admin_one() -> None:
    """Module-level bodies: the string annotations of ``from __future__ import annotations`` must resolve."""
    from app.common.auth import get_current_user, require_platform_admin

    router = APIRouter()

    @router.post("/things")
    def create(body: _Wrapper) -> None: ...

    @router.put("/things/{key}")
    def update(key: str, body: _Loose) -> None: ...

    @router.post("/clean")
    def clean(body: _Clean) -> None: ...

    @router.post("/admin/things", dependencies=[Depends(require_platform_admin)])
    def admin_create(body: _Inner) -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

    offenders, bodies = _bodies_with_the_flag(app)
    assert bodies == 4
    assert sorted(offenders) == [
        ("POST", "/api/v1/things", "_Inner"),
        ("PUT", "/api/v1/things/{key}", "_Loose"),
    ]
