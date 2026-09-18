"""No HTTP handler builds an enum out of a request field (#1520).

``SubstrateType(body.substrate_type)`` inside a handler is a 500 waiting for the
first typo. The value arrives as a free ``str`` because the request schema said
``str``; the enum call raises a bare ``ValueError``, which is neither a
``KamerplanterError`` nor a ``RequestValidationError``, so it falls past both
handlers registered in ``main.py`` and lands on the ``Exception`` one. The caller
is told ``INTERNAL_ERROR`` for input the application itself considers invalid,
and the endpoint looks broken rather than misused. ``"Coco"`` answered 500 and
``"coco"`` answered 200 on three routes of ``nutrient_calculations/router.py``
until #1520; #966 was the same shape and stood for 274 days.

**Why this and not the boundary gate.** ``scripts/check_boundary_validation.py``
pairs a request schema with a domain model at a *construction site*
(``DomainModel(**body.model_dump())``) and says so in its own docstring. These
handlers never construct a domain model — they hand the value to an engine — so
they were invisible there by construction, and no ceiling adjustment would have
found them. This test asks the complementary question: does a handler convert a
request value to an enum *itself*, instead of letting Pydantic do it at the
boundary? The repair is always the same one line: put the enum type on the
request schema. OpenAPI then documents the members for free.

**What "a request field" means here.** A handler parameter whose default is not
``Depends(...)``/``Security(...)`` is, in FastAPI, request input — body, path,
query, header or form. That is the rule used, rather than a list of parameter
names or a filename pattern: ``body``, ``payload``, ``request`` and a bare
``phase: str = Query(...)`` are all the same defect, and the #1353 sweep is on
record for having missed three routes by keying on the file name
``tenant_router.py``. Local aliases are followed (``value = body.phase`` →
``PhaseName(value)``), and ``EnumType[body.field]`` — lookup by *name*, which
raises ``KeyError`` — counts too. The enum vocabulary is read from
``app.common.enums`` at runtime rather than matched by a name pattern, so an
enum whose name follows no convention is still seen.

**Two deliberate silences**, both one-directional — they can hide a finding,
never invent one, because a check with false positives gets switched off:

* A conversion inside a ``try`` that catches ``ValueError``/``KeyError`` cannot
  reach the 500 handler. ``attachments/tenant_router.py:_parse_category`` is that
  shape and translates the failure into a 422 with ``details[].field`` itself.
  (A catch that re-raises the same ``ValueError`` unchanged would be missed here.)
* Taint does not cross a **call**. ``notif = service.get(key)`` followed by
  ``ReminderType(notif.data[...])`` reads a value out of the *database*, not out
  of the request; the path parameter only selected the row. Both shapes were
  measured as findings before this rule and neither is the defect.
"""

import ast
import enum
import pathlib

import pytest

import app.common.enums as enums_module

#: Everything under here is scanned — every module, not the ones whose name
#: happens to contain "router". A handler is recognised by its decorator.
API_ROOT = pathlib.Path(enums_module.__file__).resolve().parents[1] / "api"

#: Decorator attributes that make a function an HTTP handler.
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

#: Defaults that mark a parameter as *injected* rather than request input.
INJECTION_MARKERS = frozenset({"Depends", "Security"})

#: Exceptions a caught ``try`` must name for the conversion to be considered handled.
HANDLED_EXCEPTIONS = frozenset({"ValueError", "KeyError", "Exception"})

#: Every enum class the application defines centrally, by name.
ENUM_NAMES = frozenset(
    name for name, obj in vars(enums_module).items() if isinstance(obj, type) and issubclass(obj, enum.Enum)
)

#: Handler conversions that are deliberate, each with the reason it is safe.
#:
#: Key: ``(module path relative to app/api, function name, enum name)``.
#: An entry that matches no finding fails the test — an allowlist that outlives
#: its subject is how the next one gets waved through.
ALLOWLIST: dict[tuple[str, str, str], str] = {
    (
        "v1/tasks/tenant_router.py",
        "_resolve_task_provenance",
        "TaskOrigin",
    ): (
        "Server-decided provenance (#1082), not a boundary conversion: the body "
        "value is honoured only when it is already a member of the machine-origin "
        "set tested on the same line, and falls back to PIPELINE otherwise, so the "
        "call cannot raise. The schema stays free-form on purpose — an interactive "
        "caller's `origin` is discarded rather than rejected."
    ),
}


def _iter_api_modules() -> list[pathlib.Path]:
    return sorted(p for p in API_ROOT.rglob("*.py") if p.name != "__init__.py")


def _is_handler(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True when the function is mounted as an HTTP route."""
    for deco in node.decorator_list:
        call = deco.func if isinstance(deco, ast.Call) else deco
        if isinstance(call, ast.Attribute) and call.attr in HTTP_METHODS:
            return True
    return False


def _request_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Parameter names that carry request input (everything not injected)."""
    args = node.args
    positional = args.posonlyargs + args.args
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    pairs = list(zip(positional, defaults, strict=True))
    pairs += list(zip(args.kwonlyargs, args.kw_defaults, strict=True))

    request_params: set[str] = set()
    for arg, default in pairs:
        if isinstance(default, ast.Call):
            func = default.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name in INJECTION_MARKERS:
                continue
        request_params.add(arg.arg)
    return request_params


def _attribute_root(node: ast.expr) -> str | None:
    """The base name of ``a.b.c`` — ``a`` — or None when it is not a plain chain."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _reads_request(node: ast.expr, names: set[str]) -> bool:
    """True when the expression reads one of ``names`` directly or through attributes."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and _attribute_root(sub) in names:
            return True
        if isinstance(sub, ast.Name) and sub.id in names:
            return True
    return False


def _tainted_names(node: ast.AST, request_params: set[str]) -> set[str]:
    """Locals aliasing a request value, following assignments to a fixed point.

    Taint stops at a call: the result of ``service.get(key)`` is whatever the
    database holds, not what the caller typed.
    """
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for assign in ast.walk(node):
            if not isinstance(assign, ast.Assign | ast.AnnAssign):
                continue
            value = assign.value
            if value is None or any(isinstance(sub, ast.Call) for sub in ast.walk(value)):
                continue
            if not _reads_request(value, request_params | tainted):
                continue
            targets = assign.targets if isinstance(assign, ast.Assign) else [assign.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in tainted:
                    tainted.add(target.id)
                    changed = True
    return tainted


def _handled_nodes(func: ast.AST) -> set[int]:
    """Node ids inside a ``try`` body whose handlers catch the conversion failure."""
    handled: set[int] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.Try):
            continue
        names: set[str] = set()
        for handler in node.handlers:
            for part in ast.walk(handler.type) if handler.type is not None else []:
                if isinstance(part, ast.Name):
                    names.add(part.id)
        if not (names & HANDLED_EXCEPTIONS):
            continue
        for statement in node.body:
            for sub in ast.walk(statement):
                handled.add(id(sub))
    return handled


def scan_tree(tree: ast.AST, module: str) -> list[tuple[str, str, str, int]]:
    """Every ``EnumType(<request value>)`` / ``EnumType[<request value>]`` in a handler."""
    findings: list[tuple[str, str, str, int]] = []
    # Handlers plus the module-level helpers they delegate to: the neighbour in
    # `tasks/tenant_router.py` converts inside `_resolve_task_provenance`, one
    # call away from the decorated function, and a handler-only walk misses it.
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
    for func in functions:
        if not (_is_handler(func) or func.name.startswith("_")):
            continue
        request_params = _request_parameters(func)
        if not request_params:
            continue
        reachable = request_params | _tainted_names(func, request_params)
        handled = _handled_nodes(func)

        for node in ast.walk(func):
            if id(node) in handled:
                continue
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ENUM_NAMES:
                arguments = list(node.args) + [kw.value for kw in node.keywords]
                if any(_reads_request(arg, reachable) for arg in arguments):
                    findings.append((module, func.name, node.func.id, node.lineno))
            elif (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id in ENUM_NAMES
                and _reads_request(node.slice, reachable)
            ):
                findings.append((module, func.name, node.value.id, node.lineno))
    return findings


def _findings() -> list[tuple[str, str, str, int]]:
    findings: list[tuple[str, str, str, int]] = []
    for path in _iter_api_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings += scan_tree(tree, path.relative_to(API_ROOT).as_posix())
    return findings


def test_no_handler_constructs_an_enum_from_a_request_field():
    """A handler that converts a request value to an enum answers 500 on a typo."""
    offenders = [f for f in _findings() if (f[0], f[1], f[2]) not in ALLOWLIST]
    assert not offenders, (
        "Handler builds an enum from request input — a misspelt value answers 500 "
        "instead of 422 (#1520). Declare the enum type on the request schema instead:\n"
        + "\n".join(f"  {path}:{line} {func}() → {enum_name}(...)" for path, func, enum_name, line in offenders)
    )


def test_the_scan_reaches_the_handlers():
    """A scanner that walks nothing proves nothing."""
    modules = _iter_api_modules()
    assert len(modules) > 50, f"only {len(modules)} api modules parsed"
    handlers = sum(
        1
        for path in modules
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_handler(node)
    )
    assert handlers > 300, f"only {handlers} handlers recognised"
    assert {"SubstrateType", "PhaseName", "NutrientDemandLevel"} <= ENUM_NAMES


@pytest.mark.parametrize("key", sorted(ALLOWLIST))
def test_allowlist_entry_still_matches_a_finding(key):
    """An allowlist entry that outlives its subject is how the next one gets waved through."""
    assert key in {(f[0], f[1], f[2]) for f in _findings()}, f"stale allowlist entry: {key}"


#: A probe module exercising every spelling of the defect and every near-miss that
#: must stay silent. It goes through :func:`scan_tree`, the same function the repo
#: sweep uses — a probe with its own copy of the rule proves nothing about the rule.
_PROBE = '''
from app.common.enums import PhaseName, SubstrateType

router = APIRouter()


@router.post("/flushing")
def flushing_protocol(body: FlushingRequest, service: X = Depends(get_x)):
    """The #1520 shape, verbatim."""
    substrate = SubstrateType(body.substrate_type)
    return substrate


@router.post("/aliased")
def aliased(payload: Req):
    """The same defect spelt through a local alias, on a differently-named parameter."""
    raw = payload.phase
    still_raw = raw
    return PhaseName(still_raw)


@router.post("/by-name")
async def by_name(request: Req):
    """Lookup by member NAME raises KeyError — also a 500."""
    return SubstrateType[request.substrate]


@router.post("/query")
def from_query(phase: str = Query("vegetative")):
    """A query parameter is request input too — no body in sight."""
    return PhaseName(phase)


@router.post("/kwarg")
def as_keyword(body: Req):
    """The value can arrive as a keyword argument."""
    return PhaseName(value=body.phase)


@router.post("/injected")
def injected(body: Req, ctx: TenantContext = Depends(get_current_tenant)):
    """Control: a value read from an injected dependency is not request input."""
    return PhaseName(ctx.default_phase)


@router.post("/stored")
def stored(key: str, service: X = Depends(get_x)):
    """Control: the path parameter selects a row; the value comes from the row."""
    row = service.get(key)
    return PhaseName(row.phase)


@router.post("/handled")
def handled(body: Req):
    """Control: the conversion is caught and translated into a 422."""
    try:
        return PhaseName(body.phase)
    except ValueError as exc:
        raise ValidationError("nope") from exc


@router.post("/literal")
def literal(body: Req):
    """Control: a constant is not request input."""
    return PhaseName("vegetative")
'''


def test_the_detector_sees_every_spelling_of_the_defect():
    """Name a spelling of the same thing my pattern does not hit — then test it."""
    findings = scan_tree(ast.parse(_PROBE), "probe.py")
    assert sorted(name for _, name, _, _ in findings) == [
        "aliased",
        "as_keyword",
        "by_name",
        "flushing_protocol",
        "from_query",
    ]


@pytest.mark.parametrize("control", ["injected", "stored", "handled", "literal"])
def test_the_detector_stays_silent_on_the_near_misses(control):
    """A check with false positives gets switched off, and then it guards nothing."""
    assert control not in {name for _, name, _, _ in scan_tree(ast.parse(_PROBE), "probe.py")}
