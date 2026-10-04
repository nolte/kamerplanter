"""Does a route handler reach a persistence write? A static call-graph detector (#1443).

`test_write_route_gates.py` decided "this is a write route" from the HTTP method.
A method is a convention: two routes in this codebase were measured persisting on
a ``GET`` (#1422 review), and the sweep could not see either of them. This module
is the detector that replaces the convention with a measurement.

**How it decides.** Every module under the imported ``app`` package is parsed
**once** and cached for the session. Within that tree it finds the *direct*
persistence writes — a call to a python-arango collection primitive
(``insert``/``update``/``replace``/``delete``/…) on a collection receiver, or a
query string whose shape is an ``INSERT``/``UPDATE``/``REPLACE``/``REMOVE``/
``UPSERT`` (AQL) or an ``INSERT INTO``/``DELETE FROM``/``CREATE TABLE`` (the
TimescaleDB migrations). A query literal counts whether it is spelled out in the
function body or bound to a **module-level constant** the body merely references
— ``data_access/timescale/observation_repository.py`` holds its ``INSERT INTO
sensor_readings`` that way, and until SEC-004 of the #1443 review this docstring
claimed a coverage the scan did not have. Everything else is derived: a function
writes if it can reach one of those through the call graph.

**How it resolves a call.** By receiver type, not by method name. ``self.X`` is
resolved through the enclosing class and the type its methods give ``X`` — an
annotation wins, otherwise the union of every bare ``self.X = value`` in ANY
method, constructor calls only (#2039); a local or a parameter through its
annotation, its constructor call, or the return annotation of the call it came
from; a loop or comprehension variable through the element type of what it
iterates (in-tree classes only); a name in a tuple-unpacking target through its
POSITION in a fixed-arity ``tuple[...]`` element (``enumerate``, ``zip`` and
``.items()`` included; an unstated arity or a starred target types nothing); a
``with … as x`` name through a ``@contextmanager``'s ``Iterator[X]`` or an
annotated ``__enter__`` (an unannotated one types nothing); a class
named directly through itself; ``a or b`` / ``a if c else b`` through both
operands, in a body and in an ``__init__`` assignment alike; an attribute that is
a ``@property`` through the property's return annotation. A method found on a type is then
looked up across that type's bases **and** its subclasses — the services here are
annotated against ``I*Repository`` interfaces whose bodies are ``...``, so
ignoring implementors would miss every write in the application.

Name-only resolution was measured first and is not usable: with it, **356 of 356**
mounted read operations came out as writers, because ``api.mapping.to_response``
collides with ``BaseArangoRepository.update`` on the bare name ``update`` and
``ArangoMcpIdempotencyRepository.get`` collides with every ``.get()`` in the tree.

**What it deliberately cannot see**, so that nobody reads more into a green run
than it says:

* **Dynamic dispatch.** ``getattr(obj, name)()``, a callable pulled out of a dict
  or a registry, a handler invoked by string name. The dispatch target is a value
  at run time and no annotation names it.
* **Celery tasks.** ``some_task.delay(...)`` enqueues; the write happens in a
  worker, in a different process, outside any request. That is not a write *on
  the request path* and is intentionally not reported — a route that only
  enqueues is gated on the task, not here. ``BackgroundTasks.add_task(fn, ...)``
  is **not** this case and is followed (SEC-005): Starlette runs ``fn`` in this
  process, under the same request, once the response body is on the wire.
* **Writes through a receiver this module could not type.** Every one of those is
  counted and exposed as :func:`unresolved_call_count`; the sweep asserts a
  ceiling on it, so the blind spot cannot grow silently. For the subset that
  matters most — a call whose *name* belongs to the repository write vocabulary —
  an untyped receiver falls back to every definition of that name, which
  over-reports rather than missing.
* **Anything outside the ``app`` package.** A write performed by a library on the
  application's behalf is invisible.

**How a sink is named.** ``<receiver>.<method>() in <module>::<qualname>`` for a
collection primitive, ``raw query write in <module>::<qualname>`` (and its
``(f-string)`` variant) for a literal, ``module-level query write <NAME> in
<module>::<qualname>`` for a bound constant. Deliberately **without a line
number**: the identity is what exemptions in ``test_write_route_gates.py`` pin,
and #1436 — which inserted lines above two sinks in ``base_repository.py`` —
turned every one of those pins red without a single write moving. A witness that
goes red on an unrelated edit is lifted blind the third time, which is the exact
drift this detector exists to prevent. At most one sink is recorded per function
(the first the walk reaches), so the enclosing function id makes the name unique
by construction; the line number is preserved for humans in
:attr:`FunctionNode.write_site`, which only :meth:`CallGraph.write_path` emits.

The residual risk is stated rather than implied: this is a conservative
over-approximation of the *typed* call graph, and an exact one only where the
types are written down.
"""

import ast
import pathlib
import re
from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from functools import lru_cache
from typing import Any

import app as _app_package

#: The source tree of the ``app`` package **as imported**, not as guessed from
#: this file's location. A worktree without its own virtualenv resolves `app`
#: through an editable install pointing at another checkout; deriving the path
#: from `__file__` would then parse one tree while the route walk mounts another,
#: and the two would disagree without saying so.
APP_ROOT = pathlib.Path(_app_package.__file__).resolve().parent

#: A write in a query string, matched on STATEMENT SHAPE rather than on the
#: keyword. Keyword-only matching was measured first and it seeded
#: ``BaseArangoRepository._to_doc`` — from the word "UPDATE" in its docstring —
#: which made 2585 of 6047 functions writers and every route a hit. Docstrings
#: are excluded outright for the same reason; a docstring is prose about a write,
#: not a write.
_QUERY_WRITE = re.compile(
    r"\bINSERT\s+(?:\S+\s+)?INTO\b"
    r"|\bINSERT\s+\S+\s+IN\b"
    r"|\bUPDATE\s+\S+\s+(?:WITH|IN|SET)\b"
    r"|\bREPLACE\s+\S+\s+(?:WITH|IN)\b"
    r"|\bREMOVE\s+\S+\s+IN\b"
    r"|\bUPSERT\s*\{"
    r"|\bDELETE\s+FROM\b"
    r"|\bCREATE\s+(?:TABLE|INDEX|MATERIALIZED)\b"
)

#: python-arango collection mutators. ``get``/``find``/``all`` are absent on
#: purpose: this set is the persistence boundary, and a read across it is not a
#: write.
_COLLECTION_MUTATORS = frozenset(
    {
        "insert",
        "insert_many",
        "update",
        "update_many",
        "update_match",
        "replace",
        "replace_many",
        "replace_match",
        "delete",
        "delete_many",
        "delete_match",
        "truncate",
    }
)

#: A receiver that is a collection handle. ``self.collection``, ``col``,
#: ``self._db.collection(col.X)`` all match; ``data.update(...)`` on a plain dict
#: — the reason a bare mutator-name rule cannot work — does not.
_COLLECTION_RECEIVER = re.compile(r"\bcollection\b|\bcol\b")

#: Type constructors to look *through* when reading an annotation: the interesting
#: name is the element, not the container.
_TRANSPARENT_GENERICS = frozenset(
    {
        "list",
        "set",
        "tuple",
        "frozenset",
        "Sequence",
        "Iterable",
        "Iterator",
        "Awaitable",
        "Coroutine",
        "Optional",
        "Union",
        "Annotated",
        "Final",
        "ClassVar",
        "Generator",
        "AsyncIterator",
    }
)

#: Return types of the few library calls whose result is then used as a receiver
#: in this tree. `api/mapping.to_response` — which every read route funnels
#: through — does `data = model.model_dump()` and then `data.update(overrides)`;
#: without this, `data` is untyped, `update` is in the repository write
#: vocabulary, and `to_response` reads as a writer. That single edge was measured
#: turning 40 read routes into hits.
_EXTERNAL_RETURN_TYPES = {
    "model_dump": "dict",
    "model_dump_json": "str",
    "dict": "dict",
    "json": "str",
    "model_copy": "BaseModel",
}

#: Builtin and stdlib containers constructed by call rather than by literal.
#: `date_set = set()` followed by `date_set.update(...)` is a set union; without
#: this the receiver is untyped, `update` is in the repository write vocabulary,
#: and `PlantingRunService._build_channel_calendars` reads as a writer — measured
#: as one of the fourteen hits, and the only one of them that was not a real
#: write nor a guarded one.
_BUILTIN_CONTAINER_FACTORIES = frozenset(
    {"dict", "list", "set", "tuple", "frozenset", "bytearray", "defaultdict", "Counter", "OrderedDict", "deque"}
)

#: Methods whose FIRST POSITIONAL ARGUMENT is a callable this process will run,
#: on the request path. The call itself resolves to nothing in this tree (the
#: method belongs to Starlette), so without an edge to that argument the work it
#: schedules is invisible. `Celery.delay`/`apply_async` are deliberately NOT here
#: — those really do hand the work to another process.
_CALLABLE_ARGUMENT_SINKS = frozenset({"add_task"})

_MAX_TYPE_DEPTH = 6


class FunctionNode:
    """One `def` in the app tree, with its call sites and whether it writes itself."""

    __slots__ = (
        "module",
        "qualname",
        "name",
        "lineno",
        "owner",
        "direct_write",
        "direct_write_lineno",
        "_call_nodes",
        "_assignments",
        "_iterations",
        "_unpacked_iterations",
        "_context_bindings",
        "context_manager",
        "_annotations",
        "_return_annotation",
        "callees",
        "unresolved",
    )

    def __init__(self, module: str, qualname: str, name: str, lineno: int, owner: str | None) -> None:
        self.module = module
        self.qualname = qualname
        self.name = name
        self.lineno = lineno
        self.owner = owner
        self.direct_write: str | None = None
        self.direct_write_lineno: int | None = None
        self._call_nodes: list[ast.Call] = []
        self._assignments: dict[str, list[ast.expr]] = defaultdict(list)
        #: `for plant in plants:` and `[p.key for p in plants]` — the ITERABLE a
        #: loop variable is drawn from, so the variable is typed by its element.
        self._iterations: dict[str, list[ast.expr]] = defaultdict(list)
        #: `for repo, svc in pairs:` — the iterable and the POSITION PATH of each
        #: name inside the yielded value, `((0, 2),)` being "first of two". The
        #: variable is typed by that position of the element's annotation, never
        #: by the element as a whole (#2039).
        self._unpacked_iterations: dict[str, list[tuple[ast.expr, tuple[tuple[int, int], ...]]]] = defaultdict(list)
        #: `with open_conn() as conn:` — the context-manager expression a name is
        #: bound to by `with` / `async with` (#2039).
        self._context_bindings: dict[str, list[ast.expr]] = defaultdict(list)
        #: Decorated `@contextmanager` / `@asynccontextmanager`: the return
        #: annotation `Iterator[X]` then names what `with` binds, not what a call
        #: returns.
        self.context_manager = False
        self._annotations: dict[str, ast.expr] = {}
        self._return_annotation: ast.expr | None = None
        self.callees: list[FunctionNode] = []
        self.unresolved: list[str] = []

    @property
    def id(self) -> str:
        return f"{self.module}::{self.qualname}"

    @property
    def write_site(self) -> str | None:
        """:attr:`direct_write` plus the source line — for HUMANS, never for identity.

        The line number used to sit inside :attr:`direct_write` itself, and #1443
        measured what that costs: #1436 inserted lines above two sinks in
        ``base_repository.py`` and every pinned witness in
        ``_GUARDED_PERSISTING_READS`` went red without a single write moving,
        changing or appearing. An exemption that goes red on unrelated edits is
        lifted blind the third time. So the identity names the enclosing function
        — ``<receiver>.<method>() in <module>::<qualname>`` — which only moves when
        the write itself moves, and the line is carried here, where nothing
        compares it.
        """
        if self.direct_write is None:
            return None
        if self.direct_write_lineno is None:  # pragma: no cover - set together
            return self.direct_write
        return f"{self.direct_write}   [line {self.direct_write_lineno}]"

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return f"<FunctionNode {self.id}>"


class ClassNode:
    """One `class` in the app tree: its bases, its methods and its attribute types."""

    __slots__ = ("module", "name", "bases", "methods", "attributes", "explicit_attributes")

    def __init__(self, module: str, name: str) -> None:
        self.module = module
        self.name = name
        self.bases: list[str] = []
        self.methods: dict[str, list[FunctionNode]] = defaultdict(list)
        self.attributes: dict[str, ast.expr] = {}
        #: Attributes whose type is WRITTEN DOWN — a class-level or `self.X: T`
        #: annotation, a property's return type. A bare `self.X = value` in any
        #: method only adds to the others; an explicit annotation is not widened.
        self.explicit_attributes: set[str] = set()

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return f"<ClassNode {self.module}.{self.name}>"


def _base_names(annotation: ast.expr | None, depth: int = 0) -> set[str]:
    """Simple type names an annotation can denote, containers looked through."""
    if annotation is None or depth > _MAX_TYPE_DEPTH:
        return set()
    if isinstance(annotation, ast.Name):
        return {annotation.id}
    if isinstance(annotation, ast.Attribute):
        return {annotation.attr}
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        try:
            return _base_names(ast.parse(annotation.value, mode="eval").body, depth + 1)
        except SyntaxError:  # pragma: no cover - defensive
            return set()
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _base_names(annotation.left, depth + 1) | _base_names(annotation.right, depth + 1)
    if isinstance(annotation, ast.Subscript):
        head = _base_names(annotation.value, depth + 1)
        if head & _TRANSPARENT_GENERICS:
            inner = annotation.slice
            parts = inner.elts if isinstance(inner, ast.Tuple) else [inner]
            found: set[str] = set()
            for part in parts:
                found |= _base_names(part, depth + 1)
            return (head - _TRANSPARENT_GENERICS) | found
        # A generic repository (`BaseArangoRepository[Activity]`) — the head is
        # the type that carries the methods.
        return head
    return set()


def _is_query_write(value: ast.expr | None) -> bool:
    """Is this bound expression a query string whose shape is a write? (SEC-004)

    Only a literal — a plain string, an implicit concatenation of them, or an
    f-string's constant parts. A query assembled at run time out of values is not
    decidable here and is covered by the same statement of limits the module
    docstring makes for every other dynamic construction.
    """
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return bool(_QUERY_WRITE.search(value.value))
    if isinstance(value, ast.JoinedStr):
        literal = "FMT".join(
            part.value for part in value.values if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
        return bool(_QUERY_WRITE.search(literal))
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        return _is_query_write(value.left) or _is_query_write(value.right)
    return False


_SEQUENCE_HEADS = frozenset(
    {
        "list",
        "set",
        "frozenset",
        "deque",
        "Sequence",
        "MutableSequence",
        "Iterable",
        "Iterator",
        "Collection",
        "AsyncIterator",
        "AsyncIterable",
        "Generator",
        "AsyncGenerator",
    }
)
_MAPPING_HEADS = frozenset({"dict", "Mapping", "MutableMapping", "defaultdict", "OrderedDict"})

#: An annotation that denotes nothing: a position `zip()` could not type. `Any`
#: is the annotation saying "unknown", and `_base_names` of it is never a class.
_UNKNOWN_ANNOTATION = ast.Name(id="Any", ctx=ast.Load())


def _is_context_manager(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
        if name in {"contextmanager", "asynccontextmanager"}:
            return True
    return False


def _unpacked_targets(
    target: ast.expr, prefix: tuple[tuple[int, int], ...] = ()
) -> Iterator[tuple[str, tuple[tuple[int, int], ...]]]:
    """Names bound by a tuple target, each with its position path: `(i, (a, b))` -> i:(0,2), a:(1,2),(0,2).

    A target with a starred element is skipped whole: the position of the names
    after the star depends on a length the annotation need not state.
    """
    if isinstance(target, ast.Name):
        if prefix:
            yield target.id, prefix
        return
    if isinstance(target, ast.Tuple | ast.List):
        if any(isinstance(element, ast.Starred) for element in target.elts):
            return
        arity = len(target.elts)
        for index, element in enumerate(target.elts):
            yield from _unpacked_targets(element, (*prefix, (index, arity)))


def _alternatives(annotation: ast.expr, depth: int = 0) -> list[ast.expr]:
    """The non-`None` members of an annotation: `X | None`, `Optional[X]`, `"X"`, `Union[...]`."""
    if depth > _MAX_TYPE_DEPTH:
        return []
    if isinstance(annotation, ast.Constant):
        if isinstance(annotation.value, str):
            try:
                return _alternatives(ast.parse(annotation.value, mode="eval").body, depth + 1)
            except SyntaxError:  # pragma: no cover - defensive
                return []
        return []
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _alternatives(annotation.left, depth + 1) + _alternatives(annotation.right, depth + 1)
    head, parts = _subscript_parts(annotation)
    if head in {"Optional", "Union"}:
        found: list[ast.expr] = []
        for part in parts:
            found += _alternatives(part, depth + 1)
        return found
    return [annotation]


def _subscript_parts(annotation: ast.expr) -> tuple[str | None, list[ast.expr]]:
    """`dict[str, Repo]` -> ("dict", [str, Repo]); anything not subscripted -> (None, [])."""
    if not isinstance(annotation, ast.Subscript):
        return None, []
    value = annotation.value
    head = value.attr if isinstance(value, ast.Attribute) else getattr(value, "id", None)
    inner = annotation.slice
    return head, list(inner.elts) if isinstance(inner, ast.Tuple) else [inner]


def _tuple_annotation(members: list[ast.expr]) -> ast.expr:
    return ast.Subscript(
        value=ast.Name(id="tuple", ctx=ast.Load()), slice=ast.Tuple(elts=members, ctx=ast.Load()), ctx=ast.Load()
    )


def _union_annotation(members: list[ast.expr]) -> ast.expr:
    """Join annotations flat: a left-nested `a | b | c` chain would exhaust `_MAX_TYPE_DEPTH`."""
    flat: list[ast.expr] = []
    seen: set[str] = set()
    for member in members:
        for part in _flatten_union(member):
            marker = ast.dump(part)
            if marker not in seen:
                seen.add(marker)
                flat.append(part)
    if len(flat) == 1:
        return flat[0]
    return ast.Subscript(
        value=ast.Name(id="Union", ctx=ast.Load()), slice=ast.Tuple(elts=flat, ctx=ast.Load()), ctx=ast.Load()
    )


def _flatten_union(annotation: ast.expr) -> list[ast.expr]:
    head, parts = _subscript_parts(annotation)
    if head == "Union":
        return [flat for part in parts for flat in _flatten_union(part)]
    return [annotation]


def _navigate_tuple(annotation: ast.expr, path: tuple[tuple[int, int], ...]) -> list[ast.expr]:
    """Walk `path` into fixed-arity `tuple[...]` annotations; anything else yields nothing."""
    current = [annotation]
    for index, arity in path:
        following: list[ast.expr] = []
        for candidate in current:
            for alternative in _alternatives(candidate):
                head, parts = _subscript_parts(alternative)
                is_fixed = head in {"tuple", "Tuple"} and not any(
                    isinstance(part, ast.Constant) and part.value is Ellipsis for part in parts
                )
                if is_fixed and len(parts) == arity:
                    following.append(parts[index])
        current = following
        if not current:
            return []
    return current


def _record_attribute(klass: ClassNode, name: str, annotation: ast.expr, *, explicit: bool) -> None:
    """Remember what `klass.<name>` can hold.

    A written-down annotation is authoritative and is not widened. Bare
    `self.X = value` assignments, in ANY method, are alternatives of one another:
    the attribute can hold either, so the type is their union — the first one
    winning would hide the others from the call graph.
    """
    if name in klass.explicit_attributes:
        return
    if explicit:
        klass.attributes[name] = annotation
        klass.explicit_attributes.add(name)
        return
    existing = klass.attributes.get(name)
    klass.attributes[name] = annotation if existing is None else _union_annotation([existing, annotation])


class CallGraph:
    """The parsed app tree, its typed call graph, and write reachability over it."""

    def __init__(self) -> None:
        self.functions: list[FunctionNode] = []
        self.by_id: dict[str, FunctionNode] = {}
        self.by_name: dict[str, list[FunctionNode]] = defaultdict(list)
        self.classes: dict[str, list[ClassNode]] = defaultdict(list)
        #: Per module: the names it can call without a receiver — its own
        #: top-level `def`s and whatever it imported. A bare `get_db()` must
        #: resolve inside its own module, not against every `get_db` in the
        #: tree; resolving bare names globally was measured linking
        #: `common.dependencies::get_db` to `inventree.tenant_router::get_connection`
        #: and reporting four admin reads as writers through it.
        self.module_symbols: dict[str, dict[str, str]] = defaultdict(dict)
        #: Module-level names and the expression each was bound to. `router =
        #: APIRouter(...)` lives here; without it every `@router.delete(...)`
        #: decorator is an untyped receiver calling a name in the repository
        #: write vocabulary, which was measured producing 160 spurious edges.
        self.module_globals: dict[str, dict[str, ast.expr]] = defaultdict(dict)
        #: Per module: the module-level names bound to a query string whose shape
        #: is a write. `data_access/timescale/observation_repository.py` holds its
        #: `INSERT INTO sensor_readings` as `_INSERT_SQL` at module level and
        #: `insert()` only REFERENCES the name, so a scan looking for literals
        #: inside function bodies alone saw the whole TimescaleDB write surface as
        #: read-only — while this module's docstring named `INSERT INTO` a sink.
        #: SEC-004 of the #1443 review. A function that mentions one of these
        #: names is a direct writer, on the same terms as one that spells the
        #: query out in its own body.
        self.query_write_globals: dict[str, set[str]] = defaultdict(set)
        self.subclasses: dict[str, list[ClassNode]] = defaultdict(list)
        self.modules_parsed = 0
        self.unresolved_calls = 0
        #: The two parts of `unresolved_calls` (#2039). `genuine` is a receiver
        #: nothing in the tree types and no external library owns — a missing
        #: annotation someone can add. `external` is a receiver typed as, or
        #: reached from, a class or module outside the tree (`structlog`'s
        #: logger, `self._db.aql`, `datetime.now()`): typing it can never resolve
        #: the call, so counting it would let the ceiling move on work that is
        #: not a gap.
        self.genuine_unresolved_calls = 0
        self.external_unresolved_calls = 0
        #: Per module: the names bound by an import of something outside `app`.
        self.external_names: dict[str, set[str]] = defaultdict(set)
        #: `(caller id, callee id)` pairs linked by NAME because nothing typed the
        #: receiver. Reported inside the path so a triage can see which hop is a
        #: guess rather than a resolution.
        self.fallback_edges: set[tuple[str, str]] = set()
        self._writers: set[str] | None = None
        self._resolving: set[int] = set()

    # ── parsing ────────────────────────────────────────────────────────────

    def parse_tree(self, root: pathlib.Path) -> None:
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(root)
            module = "app." + str(relative).removesuffix(".py").replace("/", ".")
            module = module.removesuffix(".__init__")
            self._parse_module(module, ast.parse(path.read_text(encoding="utf-8")))
            self.modules_parsed += 1

    def _parse_module(self, module: str, tree: ast.Module) -> None:
        docstrings = _docstring_ids(tree)
        symbols = self.module_symbols[module]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                for alias in node.names:
                    symbols[alias.asname or alias.name] = f"{node.module}::{alias.name}"
                    if node.module.split(".")[0] != "app":
                        self.external_names[module].add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] != "app":
                        self.external_names[module].add(alias.asname or alias.name.split(".")[0])
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                symbols[node.name] = f"{module}::{node.name}"
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.module_globals[module][node.target.id] = node.annotation
                if _is_query_write(node.value):
                    self.query_write_globals[module].add(node.target.id)
            elif isinstance(node, ast.Assign) and node.value is not None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.module_globals[module].setdefault(target.id, node.value)
                        if _is_query_write(node.value):
                            self.query_write_globals[module].add(target.id)

        def visit(node: ast.AST, prefix: str, owner: ClassNode | None) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    function = FunctionNode(
                        module, prefix + child.name, child.name, child.lineno, owner.name if owner else None
                    )
                    function.context_manager = _is_context_manager(child)
                    self._scan_function(child, function, docstrings, self.query_write_globals[module])
                    self.functions.append(function)
                    self.by_id[function.id] = function
                    self.by_name[function.name].append(function)
                    if owner is not None:
                        owner.methods[child.name].append(function)
                        # Every method, not `__init__` alone (#2039): a connection
                        # a `connect()` opens is `self._conn` all the same.
                        _harvest_self_attributes(child, owner)
                        if child.returns is not None and _is_property(child):
                            # `ctx.plant_service.get(...)` reads an attribute whose
                            # type is the property's return annotation; it is not
                            # a call of `plant_service`, so nothing else types it.
                            _record_attribute(owner, child.name, child.returns, explicit=True)
                    visit(child, function.qualname + ".<locals>.", None)
                elif isinstance(child, ast.ClassDef):
                    klass = ClassNode(module, child.name)
                    for base in child.bases:
                        klass.bases.extend(_base_names(base))
                    for statement in child.body:
                        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                            _record_attribute(klass, statement.target.id, statement.annotation, explicit=True)
                    self.classes[child.name].append(klass)
                    for base_name in klass.bases:
                        self.subclasses[base_name].append(klass)
                    visit(child, prefix + child.name + ".", klass)
                else:
                    visit(child, prefix, owner)

        visit(tree, "", None)

    def _scan_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        fn: FunctionNode,
        docstrings: set[int],
        query_write_globals: set[str],
    ) -> None:
        fn._return_annotation = node.returns
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            if argument.annotation is not None:
                fn._annotations[argument.arg] = argument.annotation
        for inner in ast.walk(node):
            if isinstance(inner, ast.AnnAssign) and isinstance(inner.target, ast.Name):
                fn._annotations.setdefault(inner.target.id, inner.annotation)
            elif isinstance(inner, ast.Assign) and inner.value is not None:
                for target in inner.targets:
                    if isinstance(target, ast.Name):
                        fn._assignments[target.id].append(inner.value)
            elif isinstance(inner, ast.For | ast.AsyncFor | ast.comprehension):
                if isinstance(inner.target, ast.Name):
                    fn._iterations[inner.target.id].append(inner.iter)
                else:
                    for name, path in _unpacked_targets(inner.target):
                        fn._unpacked_iterations[name].append((inner.iter, path))
            elif isinstance(inner, ast.With | ast.AsyncWith):
                for item in inner.items:
                    if isinstance(item.optional_vars, ast.Name):
                        fn._context_bindings[item.optional_vars.id].append(item.context_expr)
            elif isinstance(inner, ast.Call):
                fn._call_nodes.append(inner)
                callee = inner.func
                if isinstance(callee, ast.Attribute) and callee.attr in _COLLECTION_MUTATORS and not fn.direct_write:
                    receiver = ast.unparse(callee.value)
                    if _COLLECTION_RECEIVER.search(receiver):
                        fn.direct_write = f"{receiver}.{callee.attr}() in {fn.id}"
                        fn.direct_write_lineno = inner.lineno
            elif isinstance(inner, ast.Constant) and isinstance(inner.value, str) and id(inner) not in docstrings:
                if not fn.direct_write and _QUERY_WRITE.search(inner.value):
                    fn.direct_write = f"raw query write in {fn.id}"
                    fn.direct_write_lineno = inner.lineno
            elif isinstance(inner, ast.JoinedStr) and not fn.direct_write:
                literal = "FMT".join(
                    part.value
                    for part in inner.values
                    if isinstance(part, ast.Constant) and isinstance(part.value, str)
                )
                if _QUERY_WRITE.search(literal):
                    fn.direct_write = f"raw query write (f-string) in {fn.id}"
                    fn.direct_write_lineno = inner.lineno
            elif isinstance(inner, ast.Name) and not fn.direct_write and inner.id in query_write_globals:
                # SEC-004: the query lives at module level and the body only names
                # it. `ArangoObservationRepository.insert` is `cursor.execute(
                # _INSERT_SQL, ...)` and nothing else, so without this the whole
                # TimescaleDB write surface reads as clean.
                fn.direct_write = f"module-level query write {inner.id} in {fn.id}"
                fn.direct_write_lineno = inner.lineno

    # ── type resolution ────────────────────────────────────────────────────

    def _types_of(self, expression: ast.expr, scope: FunctionNode, depth: int = 0) -> set[str]:
        if depth > _MAX_TYPE_DEPTH or id(expression) in self._resolving:
            return set()
        self._resolving.add(id(expression))
        try:
            return self._types_of_inner(expression, scope, depth)
        finally:
            self._resolving.discard(id(expression))

    def _types_of_inner(self, expression: ast.expr, scope: FunctionNode, depth: int) -> set[str]:
        if isinstance(expression, ast.Name):
            if expression.id in {"self", "cls"} and scope.owner:
                return {scope.owner}
            if expression.id in scope._annotations:
                return _base_names(scope._annotations[expression.id])
            found: set[str] = set()
            for assigned in scope._assignments.get(expression.id, ()):
                found |= self._types_of(assigned, scope, depth + 1)
            for iterable in scope._iterations.get(expression.id, ()):
                # The element of `plants: list[Plant]` is a `Plant` — containers
                # are already looked through by `_base_names`. Only a type defined
                # in this tree is taken: an unparameterised `list` or a `dict`
                # (whose iteration yields KEYS) must leave the variable untyped,
                # so a write-vocabulary call on it still falls back by name.
                found |= {name for name in self._types_of(iterable, scope, depth + 1) if name in self.classes}
            for iterable, path in scope._unpacked_iterations.get(expression.id, ()):
                found |= self._unpacked_types(iterable, path, scope, depth + 1)
            for manager in scope._context_bindings.get(expression.id, ()):
                found |= self._entered_types(manager, scope, depth + 1)
            if not found:
                module_level = self.module_globals.get(scope.module, {}).get(expression.id)
                if module_level is not None:
                    found |= self._types_of(module_level, scope, depth + 1)
            if not found and expression.id in self.classes and expression.id in self.module_symbols[scope.module]:
                # A class named directly — `TenantErasureEngine.plan(...)`, a
                # static or class method. The name is bound to the class by its
                # own `class` statement or by an import, not by a guess.
                found = {expression.id}
            return found
        if isinstance(expression, ast.Attribute):
            found = set()
            for owner in self._types_of(expression.value, scope, depth + 1):
                for klass in self._related_classes(owner):
                    annotation = klass.attributes.get(expression.attr)
                    if annotation is not None:
                        found |= _base_names(annotation)
            return found
        if isinstance(expression, ast.Await):
            return self._types_of(expression.value, scope, depth + 1)
        if isinstance(expression, ast.Call):
            callee = expression.func
            if isinstance(callee, ast.Name) and callee.id == "super" and scope.owner:
                return {scope.owner}
            if isinstance(callee, ast.Name) and callee.id in _BUILTIN_CONTAINER_FACTORIES:
                return {callee.id}
            if isinstance(callee, ast.Attribute) and callee.attr in _EXTERNAL_RETURN_TYPES:
                return {_EXTERNAL_RETURN_TYPES[callee.attr]}
            if isinstance(callee, ast.Name) and callee.id in self.classes:
                return {callee.id}
            if isinstance(callee, ast.Attribute) and callee.attr in self.classes:
                return {callee.attr}
            if isinstance(callee, ast.Subscript):
                # `BaseArangoRepository[ControlSchedule](db, ...)` — the sub-repositories
                # `ArangoActuatorRepository` builds in its `__init__` are all written
                # this way, and a Name-only rule types none of them.
                head = _base_names(callee)
                if head & set(self.classes):
                    return head & set(self.classes)
            found = set()
            targets = self._call_targets(expression, scope, depth + 1)
            for target in targets:
                found |= _base_names(target._return_annotation)
            if not targets and isinstance(callee, ast.Name) and callee.id[:1].isupper():
                # An external constructor: `router = APIRouter(...)`,
                # `now = Path(...)`. The class is not in this tree, so nothing
                # can be resolved ON it — but the receiver is TYPED, and that is
                # what keeps `@router.delete(...)` out of the untyped fallback
                # (144 spurious edges when it was missing).
                return {callee.id}
            return found
        if isinstance(expression, ast.Dict | ast.DictComp):
            return {"dict"}
        if isinstance(expression, ast.List | ast.ListComp):
            return {"list"}
        if isinstance(expression, ast.Set | ast.SetComp):
            return {"set"}
        if isinstance(expression, ast.Tuple):
            return {"tuple"}
        if isinstance(expression, ast.JoinedStr):
            return {"str"}
        if isinstance(expression, ast.Constant):
            return {type(expression.value).__name__}
        if isinstance(expression, ast.Subscript):
            return self._types_of(expression.value, scope, depth + 1)
        if isinstance(expression, ast.IfExp):
            return self._types_of(expression.body, scope, depth + 1) | self._types_of(
                expression.orelse, scope, depth + 1
            )
        if isinstance(expression, ast.BoolOp):
            # `repo or DefaultRepository()` — either operand can be the value.
            found = set()
            for operand in expression.values:
                found |= self._types_of(operand, scope, depth + 1)
            return found
        return set()

    def _unpacked_types(
        self,
        iterable: ast.expr,
        path: tuple[tuple[int, int], ...],
        scope: FunctionNode,
        depth: int,
    ) -> set[str]:
        """The type names position `path` of what `iterable` yields can denote (#2039).

        Positional, never wholesale: `for repo, svc in pairs` over
        `list[tuple[Repo, Svc]]` makes `repo` a `Repo` and `svc` a `Svc`, not both
        of them. A tuple whose arity the annotation does not state (`tuple[X, ...]`,
        a bare `tuple`, an arity that differs from the target's) types nothing:
        a wrong resolution would let a write guard certify a call it never saw.
        """
        found: set[str] = set()
        for yielded in self._yielded_annotations(iterable, scope, depth):
            for annotation in _navigate_tuple(yielded, path):
                found |= _base_names(annotation)
        # Taken UNFILTERED, unlike a single-name loop: the position is known, so a
        # `str` or a `StandardDatabase` is a fact and keeps a non-repository value
        # out of the name fallback. `Any`/`object` are the annotation saying
        # "unknown" and must not block it.
        return found - {"Any", "object"}

    def _yielded_annotations(self, iterable: ast.expr, scope: FunctionNode, depth: int) -> list[ast.expr]:
        """Annotations of the value one iteration over `iterable` yields, as far as written down."""
        if depth > _MAX_TYPE_DEPTH:
            return []
        if isinstance(iterable, ast.Call):
            callee = iterable.func
            if isinstance(callee, ast.Name) and callee.id in self.module_symbols.get(scope.module, {}):
                # A function of this module named `enumerate`: not the builtin.
                return self._element_of_annotations(self._annotations_of(iterable, scope, depth), depth)
            if isinstance(callee, ast.Name) and callee.id == "enumerate" and iterable.args:
                return [
                    _tuple_annotation([ast.Name(id="int", ctx=ast.Load()), element])
                    for element in self._yielded_annotations(iterable.args[0], scope, depth + 1)
                ]
            if isinstance(callee, ast.Name) and callee.id == "zip" and iterable.args and not iterable.keywords:
                members = []
                for argument in iterable.args:
                    elements = self._yielded_annotations(argument, scope, depth + 1)
                    members.append(_union_annotation(elements) if elements else _UNKNOWN_ANNOTATION)
                return [_tuple_annotation(members)]
            if isinstance(callee, ast.Name) and callee.id in {"sorted", "reversed", "list", "tuple", "set"}:
                return self._yielded_annotations(iterable.args[0], scope, depth + 1) if iterable.args else []
            if isinstance(callee, ast.Attribute) and callee.attr == "items" and not iterable.args:
                pairs = []
                for mapping in self._annotations_of(callee.value, scope, depth + 1):
                    for alternative in _alternatives(mapping):
                        head, parts = _subscript_parts(alternative)
                        if head in _MAPPING_HEADS and len(parts) == 2:
                            pairs.append(_tuple_annotation(parts))
                return pairs
        return self._element_of_annotations(self._annotations_of(iterable, scope, depth), depth)

    def _annotations_of(self, expression: ast.expr, scope: FunctionNode, depth: int) -> list[ast.expr]:
        """The annotations WRITTEN for an expression: a parameter, a `self.X`, a call's return type."""
        if isinstance(expression, ast.Name):
            written = scope._annotations.get(expression.id)
            return [written] if written is not None else []
        if isinstance(expression, ast.Attribute):
            found: list[ast.expr] = []
            for owner in self._types_of(expression.value, scope, depth + 1):
                for klass in self._related_classes(owner):
                    declared = klass.attributes.get(expression.attr)
                    if declared is not None:
                        found.append(declared)
            return found
        if isinstance(expression, ast.Call):
            return [
                target._return_annotation
                for target in self._call_targets(expression, scope, depth + 1)
                if target._return_annotation is not None
            ]
        return []

    @staticmethod
    def _element_of_annotations(annotations: list[ast.expr], depth: int) -> list[ast.expr]:
        elements: list[ast.expr] = []
        for annotation in annotations:
            for alternative in _alternatives(annotation):
                head, parts = _subscript_parts(alternative)
                if (head in _SEQUENCE_HEADS or head in _MAPPING_HEADS) and parts:
                    # A mapping iterates its KEYS; `.items()` is handled apart.
                    elements.append(parts[0])
                elif head in {"tuple", "Tuple"} and parts:
                    elements.append(_union_annotation([part for part in parts if not isinstance(part, ast.Constant)]))
        return elements

    def _entered_types(self, manager: ast.expr, scope: FunctionNode, depth: int) -> set[str]:
        """What `with <manager> as x` binds `x` to, if the source says so (#2039).

        Two written-down facts and nothing else: a `@contextmanager` function's
        `Iterator[X]`/`Generator[X, ...]` yields an `X`; a class's annotated
        `__enter__`/`__aenter__` returns what it names (`Self` is the class
        itself). A manager whose `__enter__` is not annotated binds an UNTYPED
        name — assuming it returns `self` is the guess this method exists to avoid.
        """
        inner = manager.value if isinstance(manager, ast.Await) else manager
        found: set[str] = set()
        managers: list[FunctionNode] = []
        if isinstance(inner, ast.Call):
            managers = [t for t in self._call_targets(inner, scope, depth) if t.context_manager]
            for target in managers:
                found |= _base_names(target._return_annotation)
            callee = inner.func
            if isinstance(callee, ast.Name) and callee.id == "open" and "open" not in self.module_symbols[scope.module]:
                found.add("IO")
        if managers:
            return found
        for owner in self._types_of(inner, scope, depth):
            for klass in self._related_classes(owner):
                for hook in ("__enter__", "__aenter__"):
                    for method in klass.methods.get(hook, ()):
                        names = _base_names(method._return_annotation)
                        found |= {owner} if names == {"Self"} else names
        return found

    def _related_classes(self, name: str) -> Iterator[ClassNode]:
        """`name`'s own definitions, its ancestors, and its implementors — not its siblings.

        **Up** because ``ArangoActivityRepository`` inherits ``create`` from
        ``BaseArangoRepository``. **Down** because the services are annotated
        against ``I*Repository`` interfaces whose method bodies are ``...``; a
        lookup that stopped at the declared type would resolve every repository
        call in the application to an empty body and report no writes at all.

        Up **and then down again** is the shape to avoid, and the first version
        did it: from ``ArangoCareReminderRepository`` it reached
        ``BaseArangoRepository`` and from there *every* repository in the tree, so
        ``create_profile`` resolved to ``ArangoWateringRepository.create`` and
        every reported path named the wrong collection.

        Down and then up is required, not optional: ``PrivacyService._export_repo``
        is annotated ``IDataExportRepository``, and the ``update`` it calls is
        defined on ``BaseArangoRepository`` — a base of the *implementor*, not of
        the interface. Forbidding that direction was measured losing
        ``GET /privacy/export/{key}/download``, which really does persist a
        download counter.
        """
        seen: set[int] = set()
        candidates = list(self._ancestors(name))
        for implementor in self._implementors(name):
            candidates.extend(self._ancestors(implementor.name))
        for klass in candidates:
            if id(klass) not in seen:
                seen.add(id(klass))
                yield klass

    def _ancestors(self, name: str) -> list[ClassNode]:
        found: list[ClassNode] = []
        seen: set[str] = set()
        queue = deque([name])
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            for klass in self.classes.get(current, ()):
                found.append(klass)
                queue.extend(klass.bases)
        return found

    def _implementors(self, name: str) -> list[ClassNode]:
        found: list[ClassNode] = []
        seen: set[str] = set()
        queue = deque([name])
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            for klass in self.subclasses.get(current, ()):
                found.append(klass)
                queue.append(klass.name)
        return found

    def _call_targets(self, call: ast.Call, scope: FunctionNode, depth: int = 0) -> list[FunctionNode]:
        callee = call.func
        if isinstance(callee, ast.Name):
            local = f"{scope.module}::{callee.id}"
            if local in self.by_id:
                return [self.by_id[local]]
            imported = self.module_symbols.get(scope.module, {}).get(callee.id)
            if imported and imported in self.by_id:
                return [self.by_id[imported]]
            if callee.id in scope._assignments:
                # A local alias — `handler = self._table[key]` or `fn = _pick()`.
                return []
            return []
        if not isinstance(callee, ast.Attribute):
            return []
        targets: list[FunctionNode] = []
        for owner in self._types_of(callee.value, scope, depth + 1):
            for klass in self._related_classes(owner):
                targets.extend(klass.methods.get(callee.attr, ()))
        if callee.attr in _CALLABLE_ARGUMENT_SINKS and call.args:
            # SEC-005. `background_tasks.add_task(fn, ...)` is NOT the Celery case
            # this module excludes: Starlette runs the callable in THIS process,
            # under the same request, after the response body is sent. A handler
            # that hands a writer to it writes on the request path, and the edge
            # from the handler to `fn` is the only thing that says so — the
            # `add_task` call itself resolves to a library method with no body
            # here.
            targets.extend(self._callable_targets(call.args[0], scope, depth + 1))
        return targets

    def _callable_targets(self, expression: ast.expr, scope: FunctionNode, depth: int = 0) -> list[FunctionNode]:
        """The definitions a callable REFERENCE denotes — `fn`, not `fn()` (SEC-005)."""
        if isinstance(expression, ast.Name):
            local = f"{scope.module}::{expression.id}"
            if local in self.by_id:
                return [self.by_id[local]]
            imported = self.module_symbols.get(scope.module, {}).get(expression.id)
            if imported and imported in self.by_id:
                return [self.by_id[imported]]
            return []
        if isinstance(expression, ast.Attribute):
            targets: list[FunctionNode] = []
            for owner in self._types_of(expression.value, scope, depth + 1):
                for klass in self._related_classes(owner):
                    targets.extend(klass.methods.get(expression.attr, ()))
            return targets
        return []

    def _method_by_name(self, name: str) -> list[FunctionNode]:
        return list(self.by_name.get(name, ()))

    # ── the graph, and write reachability over it ──────────────────────────

    def link(self) -> None:
        """Resolve every call site once, and record the ones no type could resolve."""
        vocabulary = self._write_vocabulary()
        for fn in self.functions:
            seen: set[int] = set()
            for call in fn._call_nodes:
                targets = self._call_targets(call, fn)
                if not targets and isinstance(call.func, ast.Attribute):
                    self.unresolved_calls += 1
                    if self._is_external_receiver(call.func.value, fn):
                        self.external_unresolved_calls += 1
                    else:
                        self.genuine_unresolved_calls += 1
                    fn.unresolved.append(call.func.attr)
                    # Only an UNTYPED receiver falls back. A receiver whose type
                    # is known and simply carries no such method is not a blind
                    # spot: `params: dict[str, Any]` calling `.update(...)` is a
                    # dict merge, and letting it match the repository vocabulary
                    # was measured turning `api.mapping.to_response` into a
                    # writer and 181 read routes into hits.
                    receiver_source = ast.unparse(call.func.value)
                    is_primitive = call.func.attr in _COLLECTION_MUTATORS and _COLLECTION_RECEIVER.search(
                        receiver_source
                    )
                    if not is_primitive and call.func.attr in vocabulary and not self._types_of(call.func.value, fn):
                        # Conservative fallback, bounded to the repository write
                        # vocabulary: over-report rather than miss a write behind
                        # a receiver nothing annotates.
                        targets = self._method_by_name(call.func.attr)
                        for target in targets:
                            self.fallback_edges.add((fn.id, target.id))
                for target in targets:
                    if id(target) not in seen:
                        seen.add(id(target))
                        fn.callees.append(target)

    def _is_external_receiver(self, expression: ast.expr, scope: FunctionNode, depth: int = 0) -> bool:
        """Is this receiver typed as, or rooted in, something outside the tree? (#2039)

        Rooted in an external import (`datetime`, `asyncio`, `httpx`), a module
        global or local bound to a call on one (`logger = structlog.get_logger()`),
        an attribute or subscript of such a thing, or a value whose resolved type
        is a name this tree does not define (`StandardDatabase`, `dict`, `str`).
        `Any` and `object` are not types in this sense: they are the annotation
        saying "unknown".
        """
        if depth > _MAX_TYPE_DEPTH:
            return False
        if isinstance(expression, ast.Name):
            if expression.id in scope._annotations or expression.id in {"self", "cls"}:
                return self._types_are_external(expression, scope)
            local = scope._assignments.get(expression.id)
            if local:
                return all(self._is_external_receiver(v, scope, depth + 1) for v in local) or (
                    self._types_are_external(expression, scope)
                )
            managers = scope._context_bindings.get(expression.id)
            if managers and (
                all(self._is_external_receiver(m, scope, depth + 1) for m in managers)
                or self._types_are_external(expression, scope)
            ):
                return True
            if expression.id in self.external_names.get(scope.module, ()):
                return True
            imported_from = self.module_symbols.get(scope.module, {}).get(expression.id, "")
            if imported_from.startswith("app."):
                # `celery_app` is built in `app.tasks.celery_app` and imported here:
                # judge it where it is bound.
                home_module, _, home_name = imported_from.partition("::")
                home_bound = self.module_globals.get(home_module, {}).get(home_name)
                if home_bound is not None and not isinstance(home_bound, ast.Name | ast.Attribute):
                    home = FunctionNode(home_module, "<module>", "<module>", 0, None)
                    return self._is_external_receiver(home_bound, home, depth + 1)
            bound = self.module_globals.get(scope.module, {}).get(expression.id)
            if bound is not None and not isinstance(bound, ast.Name | ast.Attribute):
                return self._is_external_receiver(bound, scope, depth + 1) or self._types_are_external(
                    expression, scope
                )
            return self._types_are_external(expression, scope)
        if isinstance(expression, ast.Attribute | ast.Subscript):
            return self._is_external_receiver(expression.value, scope, depth + 1) or self._types_are_external(
                expression, scope
            )
        if isinstance(expression, ast.Call):
            return self._is_external_receiver(expression.func, scope, depth + 1) or self._types_are_external(
                expression, scope
            )
        if isinstance(expression, ast.Await):
            return self._is_external_receiver(expression.value, scope, depth + 1)
        return self._types_are_external(expression, scope)

    def _types_are_external(self, expression: ast.expr, scope: FunctionNode) -> bool:
        found = self._types_of(expression, scope)
        return bool(found) and not (found & set(self.classes)) and not (found <= {"Any", "object"})

    def _write_vocabulary(self) -> frozenset[str]:
        """Method names on repository classes that reach a direct write.

        Computed from the tree rather than written down, so a new repository
        write method joins it by existing. This is the only name-keyed part of
        the detector and it exists for one case: a call whose receiver carries no
        type anywhere. Bounding the fallback to these names is what keeps the
        over-approximation from swallowing the tree — resolving *every*
        unresolved call by name was measured reporting 356 of 356 read routes.
        """
        provisional = self._reachable_writers(use_declared_callees=False)
        return frozenset(
            fn.name
            for fn in self.functions
            if fn.id in provisional
            and (fn.module.startswith("app.data_access") or (fn.owner or "").endswith("Repository"))
        )

    def _reachable_writers(self, *, use_declared_callees: bool) -> set[str]:
        if use_declared_callees:
            edges = {fn.id: [callee.id for callee in fn.callees] for fn in self.functions}
        else:
            edges = {}
            for fn in self.functions:
                edges[fn.id] = [target.id for call in fn._call_nodes for target in self._call_targets(call, fn)]
        callers: dict[str, list[str]] = defaultdict(list)
        for caller, callees in edges.items():
            for callee in callees:
                callers[callee].append(caller)

        writers = {fn.id for fn in self.functions if fn.direct_write}
        queue = deque(writers)
        while queue:
            current = queue.popleft()
            for caller in callers.get(current, ()):
                if caller not in writers:
                    writers.add(caller)
                    queue.append(caller)
        return writers

    def writers(self) -> set[str]:
        if self._writers is None:
            self._writers = self._reachable_writers(use_declared_callees=True)
        return self._writers

    def write_sinks(self, entry: FunctionNode) -> set[str]:
        """EVERY direct write reachable from `entry`, not just the nearest one.

        :meth:`write_path` answers with the SHORTEST chain, so a function with two
        writes reports one and the other never appears anywhere. That is the hole
        SEC-002 of the #1443 review found in the exemption list: a witness naming
        the argument that forbids ONE write leaves a second, unguarded write in the
        same handler invisible — the route is out of the sweep either way. An
        exemption checked against this set goes red on the second sink whichever
        one a breadth-first search would have reached first.

        A sink is identified by ``<what> in <module>::<qualname of the enclosing
        function>`` and carries **no line number** — see :attr:`FunctionNode.
        write_site` for why, and :meth:`CallGraph.write_path` for the human-facing
        form that does carry one.
        """
        writers = self.writers()
        if entry.id not in writers:
            return set()
        sinks: set[str] = set()
        seen = {entry.id}
        queue: deque[FunctionNode] = deque([entry])
        while queue:
            current = queue.popleft()
            if current.direct_write:
                sinks.add(current.direct_write)
            for callee in current.callees:
                if callee.id not in seen and callee.id in writers:
                    seen.add(callee.id)
                    queue.append(callee)
        return sinks

    def write_path(self, entry: FunctionNode) -> list[str] | None:
        """The shortest handler→…→write chain, or `None` if the handler writes nothing.

        The path is the deliverable, not the boolean: a hit nobody can trace is a
        hit nobody can triage, and #1443 exists because the last such finding was
        traced by hand in a review. Its last element is therefore the *human* form
        :attr:`FunctionNode.write_site` — the sink identity plus ``[line N]`` — and
        not the identity :meth:`write_sinks` compares. Nothing may pin this string.
        """
        writers = self.writers()
        if entry.id not in writers:
            return None
        seen = {entry.id}
        queue: deque[tuple[FunctionNode, list[str]]] = deque([(entry, [entry.id])])
        while queue:
            current, path = queue.popleft()
            if current.direct_write:
                return [*path, current.write_site]
            for callee in current.callees:
                if callee.id in seen or callee.id not in writers:
                    continue
                seen.add(callee.id)
                step = callee.id
                if (current.id, callee.id) in self.fallback_edges:
                    step += "   [name fallback: the receiver carries no type]"
                queue.append((callee, [*path, step]))
        return None  # pragma: no cover - a writer always reaches a direct write


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Is this method read as an attribute — `@property` or `@cached_property`?"""
    for decorator in node.decorator_list:
        name = decorator.attr if isinstance(decorator, ast.Attribute) else getattr(decorator, "id", None)
        if name in {"property", "cached_property"}:
            return True
    return False


def _docstring_ids(tree: ast.Module) -> set[int]:
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = node.body
        if body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                found.add(id(value))
    return found


def _harvest_self_attributes(node: ast.FunctionDef | ast.AsyncFunctionDef, klass: ClassNode) -> None:
    """`self._repo = repo` inherits the annotation of the `repo` parameter — in any method (#2039)."""
    parameters = {
        argument.arg: argument.annotation
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if argument.annotation is not None
    }
    for inner in ast.walk(node):
        if isinstance(inner, ast.AnnAssign) and isinstance(inner.target, ast.Attribute):
            if isinstance(inner.target.value, ast.Name) and inner.target.value.id == "self":
                _record_attribute(klass, inner.target.attr, inner.annotation, explicit=True)
        elif isinstance(inner, ast.Assign):
            for target in inner.targets:
                if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)):
                    continue
                if target.value.id != "self":
                    continue
                annotation = _attribute_annotation(inner.value, parameters)
                if annotation is not None:
                    _record_attribute(klass, target.attr, annotation, explicit=False)


def _attribute_annotation(source: ast.expr, parameters: dict[str, ast.expr]) -> ast.expr | None:
    """The type expression an `__init__` assignment gives `self.X`, if one is written down.

    `self._repo = repo` takes the parameter's annotation and `self._engine =
    Engine()` the constructor. The DEFAULTED shapes — `repo or Default()` and
    `repo if repo is not None else Default()` — are the same two facts joined, and
    are read as their union: every operand is a value the attribute can hold. An
    operand that names nothing typed contributes nothing; it does not untype the
    others.
    """
    if isinstance(source, ast.Name):
        return parameters.get(source.id)
    if isinstance(source, ast.Call) and (
        isinstance(source.func, ast.Name)
        and source.func.id.lstrip("_")[:1].isupper()
        or isinstance(source.func, ast.Subscript)
    ):
        # A constructor, not any call: `self._x = open_conn()` names a FUNCTION,
        # and recording `open_conn` as the attribute's type blocks the name
        # fallback for it while resolving nothing (#2039).
        return source.func
    operands: list[ast.expr] = []
    if isinstance(source, ast.BoolOp):
        operands = list(source.values)
    elif isinstance(source, ast.IfExp):
        operands = [source.body, source.orelse]
    union: ast.expr | None = None
    for operand in operands:
        part = _attribute_annotation(operand, parameters)
        if part is not None:
            union = part if union is None else ast.BinOp(left=union, op=ast.BitOr(), right=part)
    return union


@lru_cache(maxsize=1)
def call_graph() -> CallGraph:
    """The parsed app tree, built once per session.

    `lru_cache` is the whole performance story: the tree is ~935 modules and
    parsing it costs ~2 s. Re-parsing per route — 796 mounted operations — would
    turn a 15 s suite into an hour.
    """
    graph = CallGraph()
    graph.parse_tree(APP_ROOT)
    graph.link()
    return graph


def function_for(endpoint: Any) -> FunctionNode | None:
    """The parsed definition of a mounted handler, by module and qualified name."""
    graph = call_graph()
    return graph.by_id.get(f"{endpoint.__module__}::{endpoint.__qualname__}")


def write_path_of(endpoint: Any) -> list[str] | None:
    """`handler → … → write` for a mounted handler, or `None` if it persists nothing."""
    function = function_for(endpoint)
    if function is None:
        return None
    return call_graph().write_path(function)


def persists(endpoint: Any) -> bool:
    return write_path_of(endpoint) is not None


def write_sinks_of(endpoint: Any) -> set[str]:
    """Every direct write a mounted handler can reach. See :meth:`CallGraph.write_sinks`."""
    entry = function_for(endpoint)
    if entry is None:
        return set()
    return call_graph().write_sinks(entry)


def reachable_keyword_arguments(endpoint: Any, callee_name: str, keyword: str) -> list[tuple[str, Any]]:
    """`(call site, value)` for every reachable call to `callee_name`, per `keyword`.

    The machine-readable half of an exemption. A read whose write is unreachable
    only because an argument forbids it cannot be excused by a sentence — #1441
    was exactly that — so the excuse names the argument and this reads it back out
    of the source. `value` is the literal when the call passes one, the unparsed
    expression when it passes something else, and `None` when the call omits the
    keyword entirely; all three are distinguishable by the caller.
    """
    entry = function_for(endpoint)
    if entry is None:
        return []

    reachable: list[FunctionNode] = []
    seen = {entry.id}
    queue = deque([entry])
    while queue:
        current = queue.popleft()
        reachable.append(current)
        for callee in current.callees:
            if callee.id not in seen:
                seen.add(callee.id)
                queue.append(callee)

    found: list[tuple[str, Any]] = []
    for function in reachable:
        for call in function._call_nodes:
            target = call.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
            if name != callee_name:
                continue
            site = f"{function.module}:{call.lineno}"
            passed = next((word for word in call.keywords if word.arg == keyword), None)
            if passed is None:
                found.append((site, None))
            elif isinstance(passed.value, ast.Constant):
                found.append((site, passed.value.value))
            else:
                found.append((site, ast.unparse(passed.value)))
    return found


def unresolved_call_count() -> int:
    """Attribute calls no receiver type could resolve — the measured blind spot."""
    return call_graph().unresolved_calls


def genuine_unresolved_call_count() -> int:
    """Unresolved calls whose receiver is an annotation gap in this tree (#2039)."""
    return call_graph().genuine_unresolved_calls


def external_unresolved_call_count() -> int:
    """Unresolved calls on a receiver typed as, or rooted in, an external library."""
    return call_graph().external_unresolved_calls


def direct_writers() -> list[FunctionNode]:
    """The seed set: functions that touch the persistence layer themselves."""
    return [fn for fn in call_graph().functions if fn.direct_write]


def writing_functions() -> Iterable[FunctionNode]:
    graph = call_graph()
    writers = graph.writers()
    return [fn for fn in graph.functions if fn.id in writers]
