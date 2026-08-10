#!/usr/bin/env python3
"""Refuse a request schema that lets through input its domain model rejects at a construction site.

**Scope — construction sites only, not the whole codebase.** This gate is a
property of the request schemas a router **constructs a domain model from** at
the boundary (``DomainModel(**body.model_dump())``), and only those. It is *not*
the property "every value this application persists was validated at the
boundary" — its name once read that way, and #1020 recorded the cost. A router
that never constructs the domain model — it writes a dict straight to a
collection, as ``PATCH /admin/platform/tenants/{key}`` did in #997 — has no
construction site, so it is **invisible here by construction**, and no number of
extra pairings would find it. That dict-writer / reach-past-the-boundary shape
is a *different* class (#1020, #1019, #1018, #997), and the gate that owns it is
``scripts/check_layer_imports.py`` (NFR-001): a persistence write needs the
``app.data_access`` collection constants, and that import is what the layer gate
refuses. Read a green result here as "the schemas that build a domain model do
not widen it", never as "the boundary validates everywhere".

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_boundary_validation.py
    python3 scripts/check_boundary_validation.py --list   # name every pairing found
    python3 scripts/check_boundary_validation.py --json   # machine-readable

**The defect it closes.** ``main.py`` registers a handler for FastAPI's
``RequestValidationError`` (→ 422) and one for ``Exception`` (→ 500). Constructing
a *domain* model inside a handler raises a plain ``pydantic.ValidationError``,
which is neither: it falls through to the 500 handler. The caller is told "we
broke" for input we ourselves consider invalid, and the endpoint is unusable
until somebody notices. #966 was that shape and stood for 274 days.

**Why a check and not a global handler.** ``spec/style-guides/BACKEND.md`` §5.4
records the decision: validation happens per endpoint, at the boundary, so the
request schema rejects what the domain model would reject. A blanket
``pydantic.ValidationError`` → 422 handler was rejected because the same
exception carries two opposite meanings — the caller sent something invalid (422
is right) or *we* assembled the model wrongly (500 is right, and it must reach
error tracking). #966 was the second kind; a blanket handler would have turned
that outage into a quiet stream of client errors and made it harder to find, not
easier.

A per-endpoint rule needs something that catches the next endpoint that forgets
it, or the class simply keeps growing. That is this script.

What it detects — and what it deliberately does not
---------------------------------------------------

Two shapes, both decidable from **annotations alone**, both certain:

* **enum widened to ``str``** — the domain field is an ``Enum``, the request
  field is plain ``str`` (or ``str | None``). The boundary accepts
  ``"definitely-not-a-member"``; the domain model rejects it. There is no input
  for which this is safe. Both known instances of the class are this shape:
  #966/#967 (``substrate_type``) and half of #971 (``application_method``).
* **nullable widened over a non-nullable domain field** — the request field
  accepts ``None``, the domain field does not, and the splat dumps without
  ``exclude_unset``/``exclude_none``, so a ``None`` is forwarded rather than
  dropped. That is #966's *other* half: an omitted field dumped as ``None``
  disables the domain default instead of falling back to it, and **every**
  request 500s.

Deliberately **not** detected: a domain ``@model_validator(mode="after")``
enforcing a cross-field rule the request schema does not restate — #970's
reported instance. It is measurable (32 pairings on the 2026-08-07 tree carry
one) but not *decidable*: whether the rule is reachable given the request
schema's field types needs the rule's semantics, and the request schema may
already mirror it through field constraints or a validator of its own. Flagging
those would have reported the endpoint #971 had just fixed. A check with false
positives gets suppressed, and a suppressed check guards nothing — so this one
covers a narrow, certain subset rather than the whole class. §5.4 carries the
rule for the part no checker can see; a reviewer enforces that half.

Also deliberately **not** detected, for a structural reason rather than an
undecidable one: a router that writes a dict straight to a collection instead of
constructing the domain model (#1020). It has no construction site, so no
pairing exists to compare, so nothing here can see it. That is a different check
— ``scripts/check_layer_imports.py`` (NFR-001) — and it owns that class; see the
scope note at the top of this docstring.

How a request schema is paired with a domain model
--------------------------------------------------

Pairings are **read off the code**, never guessed from names alone:

1. **Construction sites.** Inside a function under ``src/backend/app/api/``, a
   call ``DomainModel(**<param>.model_dump(...))`` where ``<param>`` is an
   annotated parameter of that same function. The annotation is the request
   schema, the callee is the domain model. This is the inbound direction and the
   only one that matters: the 44 further ``**x.model_dump()`` splats in the API
   tree build *response* models out of domain objects, where no caller input is
   involved.
2. **Sibling update schemas.** Once ``XCreate`` in a module is paired to domain
   model ``D`` by rule 1, an exactly-named ``XUpdate`` / ``XPatch`` in the same
   module is paired to ``D`` as well — provided it is really used as a request
   body (an annotated endpoint parameter somewhere under ``app/api/``).

Rule 2 exists because the update path is where the *worse* bug lives. An update
router hands the dumped body to a service, which assigns it onto the loaded
domain model with ``setattr``; Pydantic does not validate on assignment (#968),
so an unknown enum value is **persisted first and raises afterwards** — a 500
plus a poisoned document that every later read trips over. #971 found exactly
that on ``PUT /watering-logs/{key}``, with no test covering the path at all.
Rule 2 is name-based and therefore weaker than rule 1, which is why it demands an
exact stem and reports only the same certain shapes.

Precision guards
----------------

A pairing's field is skipped when the request schema could legitimately be doing
the validation itself:

* the request schema declares a ``@field_validator`` naming that field, or a
  ``@model_validator`` whose body **mentions** that field — either may narrow the
  value in ways no annotation shows. Mentioning is the test rather than mere
  presence: a schema that grew a boundary validator for some *other* rule would
  otherwise become a blind spot in its entirety, and ``WateringLogCreate`` (#971)
  is exactly such a schema;
* for the nullable shape, the domain model declares a
  ``@model_validator(mode="before")``, which can substitute a default for a
  ``None`` before field validation ever sees it.

Both guards err towards silence: they can suppress a true finding, never invent
one. A miss is recoverable, a false positive gets the gate switched off.

Unresolvable names are skipped rather than guessed at. The trade is
one-directional: an exotic spelling slips through, but nothing that is not
certainly a 500 is ever reported.

The ratchet, and why only one of the two shapes has one
-------------------------------------------------------

The enum shape has **46 existing occurrences** across 9 schema modules — real
debt that cannot be paid off in one change, so it carries a shrink-only ceiling
like ``scripts/check_schema_examples.py``. The nullable shape has **none** left
(#967 converted the only site), so it is a plain defect with no baseline —
``scripts/check_utc_calendar_day.py`` makes that argument: a ratchet constant
pinned at zero is dead machinery pretending to be a policy.

**Growth fails, a drop does not.** Per #973: a baseline that must be edited to an
exact number conflicts on every concurrent pull request, on a single integer
carrying no review value, and — worse — resolving that conflict by taking either
side yields a ceiling that is too high, silently loosening the gate. So a drop
prints the new number and passes; lowering :data:`MAX_ENUM_WIDENED_FIELDS` is
housekeeping, never a merge blocker.

**A green gate does not mean "the boundary validates".** The ceiling *defers*
this debt; it only holds that it stops growing. Read the number, not the colour.

Standard library only, no Pydantic import, no running stack: the ``static`` CI
job is Python-only, and importing the API tree would drag in settings and
database clients for a question answerable from the source text.

Traces to issue #970 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The backend application package. Everything here is parsed, because an import
#: chain that resolves a base class or an enum may leave the two scanned subtrees.
DEFAULT_APP_ROOT = "src/backend/app"

#: Where request schemas and routers live, relative to :data:`DEFAULT_APP_ROOT`.
#: Construction sites are only looked for here — a domain model built inside a
#: service from data the service itself assembled is not a boundary question.
API_SUBPATH = "api"

#: Enum-widened request fields, last re-measured against the tree in #1115
#: (introduced on the #970 baseline commit). A ceiling, not a target: the check
#: fails when the number grows, so no new endpoint can widen an enum to ``str``,
#: and the recorded debt can only shrink. Lower it by hand when the check reports
#: a smaller number — a drop is deliberately not a failure, see the module
#: docstring and #973.
MAX_ENUM_WIDENED_FIELDS = 46

#: The marker that exempts one field, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption: the point of the hatch is
#: the reason, not the token. Placed on the field's own line or the one above it.
JUSTIFICATION_MARKER = "# boundary-widening:"
MIN_JUSTIFICATION_CHARS = 12

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2

#: Bases that make a class an enum. ``StrEnum`` is what BACKEND.md §11 mandates;
#: the others are accepted so a stray ``IntEnum`` is not invisible.
ENUM_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "IntFlag", "Flag", "ReprEnum"})

#: Bases that make a class a Pydantic model without further resolution.
PYDANTIC_ROOT_BASES = frozenset({"BaseModel", "RootModel"})

#: Suffixes of a request schema that creates a resource. Used to derive the stem
#: for the sibling-update pairing (rule 2 in the module docstring).
CREATE_SUFFIXES = ("Create", "Request", "Input")

#: Suffixes of a request schema that edits an existing resource.
UPDATE_SUFFIXES = ("Update", "Patch")

#: Dump keywords that stop a ``None`` reaching the domain model. Only these two
#: matter for the nullable shape; ``exclude={...}`` is handled separately because
#: it names the dropped fields explicitly.
NONE_SUPPRESSING_DUMP_FLAGS = frozenset({"exclude_unset", "exclude_none"})

#: Domain annotations too loose to make a nullable request field a certain
#: defect: they accept ``None`` as a value rather than rejecting it.
NULL_TOLERANT_DOMAIN_ATOMS = frozenset({"Any", "object"})


class BoundaryCheckError(Exception):
    """A usage or environment problem — not a finding about the code."""


# ── Parsed source tree ───────────────────────────────────────────────────────


@dataclass
class Module:
    """One parsed module of the backend application package."""

    path: Path
    dotted: str
    tree: ast.Module
    source_lines: tuple[str, ...]
    #: Module-level classes by name.
    classes: dict[str, ast.ClassDef] = field(default_factory=dict)
    #: Local name → dotted module it was imported from (``from … import Name``).
    imports: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassRef:
    """A class together with the module whose namespace resolves its names."""

    module: Module
    node: ast.ClassDef

    @property
    def name(self) -> str:
        return self.node.name


@dataclass(frozen=True)
class Annotation:
    """A type annotation reduced to what this check needs to decide.

    ``atoms`` holds the non-``None`` alternatives as bare names — ``str | None``
    yields ``("str",)`` with ``optional=True``, ``list[str]`` yields ``("list",)``.
    Only the outermost constructor is kept: the shapes under test are decided at
    that level, and descending further would invent precision the check does not
    have.
    """

    atoms: tuple[str, ...]
    optional: bool
    #: The annotation exactly as written, for the report.
    text: str


@dataclass(frozen=True)
class Pairing:
    """One request schema paired with the domain model it is splatted into."""

    request: ClassRef
    domain: ClassRef
    #: Where the pairing was read off the code.
    path: Path
    line: int
    #: How it was established: a construction site, or a sibling update schema.
    origin: str
    #: True when the splat forwards a ``None`` instead of dropping it. Unknown
    #: (and therefore False) for a sibling update schema, which has no splat.
    forwards_none: bool


@dataclass(frozen=True)
class Finding:
    """One request field that lets through input the domain model rejects."""

    #: ``enum_widened_to_str`` or ``nullable_over_non_nullable``.
    kind: str
    pairing: Pairing
    field_name: str
    request_annotation: str
    domain_annotation: str
    #: Where the *request* field is declared — the place to fix it.
    path: Path
    line: int
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None


def dotted_module_name(path: Path) -> str:
    """Derive the importable dotted name of a module from its path.

    Walks up while the parent directory is a package, so
    ``src/backend/app/api/v1/tanks/schemas.py`` becomes
    ``app.api.v1.tanks.schemas`` without the source root being configured.

    Args:
        path: The module file.

    Returns:
        The dotted name.
    """
    parts = [path.stem]
    directory = path.parent
    while (directory / "__init__.py").is_file():
        parts.append(directory.name)
        directory = directory.parent
    return ".".join(reversed(parts))


def resolve_relative_import(importer: str, module: str | None, level: int) -> str:
    """Resolve a relative ``from`` target against the importing module's package.

    Args:
        importer: Dotted name of the module containing the import.
        module: The dotted tail written after the dots, if any.
        level: Number of leading dots (0 for an absolute import).

    Returns:
        The absolute dotted module name.
    """
    if level == 0:
        return module or ""
    package = importer.split(".")[:-level]
    return ".".join([*package, module]) if module else ".".join(package)


def parse_module(path: Path) -> Module:
    """Parse one module and index its module-level classes and import table.

    Imports are collected from the whole tree, not only module level: this
    codebase habitually imports inside functions to break cycles, and a base
    class or enum reached that way must still resolve.

    Args:
        path: The module to parse.

    Returns:
        The parsed module.

    Raises:
        BoundaryCheckError: If the file cannot be read or parsed.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BoundaryCheckError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise BoundaryCheckError(f"cannot parse {path}: {exc}") from exc

    module = Module(
        path=path,
        dotted=dotted_module_name(path),
        tree=tree,
        source_lines=tuple(source.splitlines()),
    )
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef):
            module.classes[statement.name] = statement
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        target = resolve_relative_import(module.dotted, node.module, node.level)
        for alias in node.names:
            module.imports.setdefault(alias.asname or alias.name, target)
    return module


class SourceTree:
    """Every parsed module of the application, with name resolution across it."""

    def __init__(self, modules: list[Module]) -> None:
        """Index the parsed modules by dotted name.

        Args:
            modules: Every module of the application package.
        """
        self._by_dotted = {module.dotted: module for module in modules}
        self.modules = modules

    def resolve(self, module: Module, name: str) -> ClassRef | None:
        """Return the class a bare name refers to in *module*'s namespace.

        Resolution is same-module first, then through the module's own
        ``from … import Name`` table. A name is never matched across the tree by
        bare spelling: class names repeat, and a name-only match would attach a
        field to whichever module happened to sort first.

        Args:
            module: The namespace the name is written in.
            name: The bare class name.

        Returns:
            The class, or None when it is not resolvable inside the scanned tree.
        """
        local = module.classes.get(name)
        if local is not None:
            return ClassRef(module, local)
        origin = self._by_dotted.get(module.imports.get(name, ""))
        if origin is None:
            return None
        target = origin.classes.get(name)
        return ClassRef(origin, target) if target is not None else None


# ── Class facts ──────────────────────────────────────────────────────────────


def base_names(node: ast.ClassDef) -> tuple[str, ...]:
    """Return the bare names of a class's bases, in source order.

    Subscripts are unwrapped (``RootModel[list[str]]`` → ``RootModel``) and dotted
    paths reduced to their last segment (``pydantic.BaseModel`` → ``BaseModel``).
    """
    names: list[str] = []
    for base in node.bases:
        target = base.value if isinstance(base, ast.Subscript) else base
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return tuple(names)


def is_enum(tree: SourceTree, ref: ClassRef) -> bool:
    """Report whether a class is an enumeration.

    Args:
        tree: The parsed application tree.
        ref: The class under test.

    Returns:
        True when one of its bases is an ``enum`` base or another enum.
    """
    return _derives_from(tree, ref, ENUM_BASES)


def is_pydantic_model(tree: SourceTree, ref: ClassRef) -> bool:
    """Report whether a class derives from ``BaseModel`` / ``RootModel``.

    Args:
        tree: The parsed application tree.
        ref: The class under test.

    Returns:
        True when a chain of resolvable bases reaches a Pydantic root.
    """
    return _derives_from(tree, ref, PYDANTIC_ROOT_BASES)


def _derives_from(
    tree: SourceTree,
    ref: ClassRef,
    roots: frozenset[str],
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    """Walk a class's bases looking for one of *roots*.

    Args:
        tree: The parsed application tree.
        ref: The class under test.
        roots: Terminal base names.
        seen: Guard against a pathological self-referential chain.

    Returns:
        True when a base chain reaches one of *roots*.
    """
    identity = (ref.module.dotted, ref.name)
    if identity in seen:
        return False
    for base in base_names(ref.node):
        if base in roots:
            return True
        parent = tree.resolve(ref.module, base)
        if parent is not None and _derives_from(tree, parent, roots, seen | {identity}):
            return True
    return False


def parse_annotation(node: ast.expr) -> Annotation:
    """Reduce an annotation AST to its non-``None`` atoms plus a nullability flag.

    ``Optional[X]``, ``Union[...]``, ``X | None``, ``Annotated[X, ...]`` and
    string (forward-reference) annotations are all unwrapped. Anything else
    contributes its bare name — or ``"?"`` when there is none, which is a name
    nothing can be compared against and therefore never produces a finding.

    Args:
        node: The annotation expression.

    Returns:
        The reduced annotation.
    """
    atoms: list[str] = []
    optional = False

    def walk(current: ast.expr) -> None:
        nonlocal optional
        if isinstance(current, ast.BinOp) and isinstance(current.op, ast.BitOr):
            walk(current.left)
            walk(current.right)
            return
        if isinstance(current, ast.Constant):
            if current.value is None:
                optional = True
            elif isinstance(current.value, str):
                try:
                    walk(ast.parse(current.value, mode="eval").body)
                except SyntaxError:
                    atoms.append("?")
            return
        if isinstance(current, ast.Subscript):
            container = current.value
            name = (
                container.id
                if isinstance(container, ast.Name)
                else container.attr
                if isinstance(container, ast.Attribute)
                else ""
            )
            if name == "Optional":
                optional = True
                walk(current.slice)
                return
            if name == "Annotated":
                inner = current.slice
                walk(inner.elts[0] if isinstance(inner, ast.Tuple) and inner.elts else inner)
                return
            if name == "Union":
                inner = current.slice
                for element in inner.elts if isinstance(inner, ast.Tuple) else [inner]:
                    walk(element)
                return
            atoms.append(name or "?")
            return
        if isinstance(current, ast.Name):
            atoms.append(current.id)
            return
        if isinstance(current, ast.Attribute):
            atoms.append(current.attr)
            return
        atoms.append("?")

    walk(node)
    return Annotation(tuple(atoms), optional, ast.unparse(node))


def model_fields(
    tree: SourceTree,
    ref: ClassRef,
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> dict[str, tuple[Annotation, ClassRef, int]]:
    """Collect a model's annotated fields, inherited ones included.

    Bases are visited first so an override in the subclass wins, which is what
    Pydantic does.

    Args:
        tree: The parsed application tree.
        ref: The model.
        seen: Guard against a pathological self-referential chain.

    Returns:
        Field name → (annotation, the class that declares it, its source line).
        The declaring class travels with the annotation because the annotation's
        names must be resolved in *that* module's namespace, not the subclass's.
    """
    identity = (ref.module.dotted, ref.name)
    if identity in seen:
        return {}
    collected: dict[str, tuple[Annotation, ClassRef, int]] = {}
    for base in base_names(ref.node):
        parent = tree.resolve(ref.module, base)
        if parent is not None:
            collected.update(model_fields(tree, parent, seen | {identity}))
    for statement in ref.node.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            collected[statement.target.id] = (
                parse_annotation(statement.annotation),
                ref,
                statement.lineno,
            )
    return collected


def _validator_functions(node: ast.ClassDef) -> list[tuple[str, ast.Call, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Return every validator in a class body as (decorator name, call, function)."""
    found: list[tuple[str, ast.Call, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for statement in node.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in statement.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            if name in {"field_validator", "model_validator"}:
                found.append((name, decorator, statement))
    return found


def _mentioned_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return every identifier, attribute and string literal appearing in a function body.

    Used to decide which fields a ``@model_validator`` could plausibly be
    narrowing. A validator that never mentions a field — by attribute access,
    by name, or as a string key — is not validating it, so suppressing that
    field would be suppressing on no evidence at all.
    """
    mentioned: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Attribute):
            mentioned.add(node.attr)
        elif isinstance(node, ast.Name):
            mentioned.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            mentioned.add(node.value)
        elif isinstance(node, ast.keyword) and node.arg:
            mentioned.add(node.arg)
    return mentioned


def self_validated_fields(tree: SourceTree, ref: ClassRef) -> frozenset[str]:
    """Report which of a model's fields the model itself might be narrowing.

    Two carriers, and neither is read as blanket cover:

    * ``@field_validator("a", "b")`` names its fields outright.
    * ``@model_validator`` sees every field, but the check credits it only with
      the fields its body actually *mentions* — by attribute, by bare name or as
      a string key. A validator that never refers to a field cannot be validating
      it, and treating any validator as cover for the whole model would blind the
      check to precisely the schemas that got a boundary validator added for some
      *other* rule — ``WateringLogCreate`` (#971) being the first of them.

    The direction of the residual error is deliberate: a validator that mentions
    a field it does not narrow suppresses a true finding (a miss), never invents
    one. Misses are recoverable; false positives get a gate switched off.

    Args:
        tree: The parsed application tree.
        ref: The model.

    Returns:
        The field names to leave alone.
    """
    named: set[str] = set()
    for ref_in_chain in _class_chain(tree, ref):
        for kind, decorator, function in _validator_functions(ref_in_chain.node):
            if kind == "model_validator":
                named |= _mentioned_names(function)
                continue
            for argument in decorator.args:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    named.add(argument.value)
    return frozenset(named)


def has_before_model_validator(tree: SourceTree, ref: ClassRef) -> bool:
    """Report whether a model runs a ``mode="before"`` model validator.

    Such a validator may substitute a default for a forwarded ``None`` before any
    field validation happens, which makes the nullable shape uncertain.

    Args:
        tree: The parsed application tree.
        ref: The model.

    Returns:
        True when the model or one of its bases declares one.
    """
    for ref_in_chain in _class_chain(tree, ref):
        for kind, decorator, _function in _validator_functions(ref_in_chain.node):
            if kind != "model_validator":
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant) and keyword.value.value == "before":
                    return True
    return False


def _class_chain(
    tree: SourceTree,
    ref: ClassRef,
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> list[ClassRef]:
    """Return a class and every resolvable base of it, subclass first."""
    identity = (ref.module.dotted, ref.name)
    if identity in seen:
        return []
    chain = [ref]
    for base in base_names(ref.node):
        parent = tree.resolve(ref.module, base)
        if parent is not None:
            chain.extend(_class_chain(tree, parent, seen | {identity}))
    return chain


# ── Pairing discovery ────────────────────────────────────────────────────────


def _dump_call_details(node: ast.expr) -> tuple[str, frozenset[str], frozenset[str]] | None:
    """Describe a ``<name>.model_dump(...)`` call, or return None for anything else.

    Args:
        node: The value splatted with ``**``.

    Returns:
        (the dumped name, the truthy keyword flags, the explicitly excluded field
        names), or None when the node is not a ``model_dump`` on a bare name.
    """
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "model_dump"):
        return None
    source = node.func.value
    if not isinstance(source, ast.Name):
        return None
    flags = {
        keyword.arg
        for keyword in node.keywords
        if keyword.arg and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
    }
    excluded: set[str] = set()
    for keyword in node.keywords:
        if keyword.arg != "exclude":
            continue
        if isinstance(keyword.value, (ast.Set, ast.List, ast.Tuple)):
            excluded.update(
                element.value
                for element in keyword.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
    return source.id, frozenset(flags), frozenset(excluded)


def _annotated_parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, ast.expr]:
    """Return the function's annotated parameters, by name."""
    arguments = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    return {argument.arg: argument.annotation for argument in arguments if argument.annotation is not None}


@dataclass(frozen=True)
class ConstructionSite:
    """One ``DomainModel(**<request>.model_dump(...))`` inside an API function."""

    module: Module
    line: int
    domain_name: str
    request_annotation: ast.expr
    dump_flags: frozenset[str]
    excluded_fields: frozenset[str]


def find_construction_sites(tree: SourceTree, api_root: Path) -> list[ConstructionSite]:
    """Find every domain-model construction fed by a request body under *api_root*.

    Args:
        tree: The parsed application tree.
        api_root: The API package; only functions below it are inspected.

    Returns:
        The sites, in module then line order.
    """
    sites: list[ConstructionSite] = []
    for module in tree.modules:
        if not module.path.is_relative_to(api_root):
            continue
        for function in ast.walk(module.tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            parameters = _annotated_parameters(function)
            for call in ast.walk(function):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
                    continue
                for keyword in call.keywords:
                    if keyword.arg is not None:
                        continue
                    details = _dump_call_details(keyword.value)
                    if details is None:
                        continue
                    dumped, flags, excluded = details
                    annotation = parameters.get(dumped)
                    if annotation is None:
                        continue
                    sites.append(
                        ConstructionSite(
                            module=module,
                            line=call.lineno,
                            domain_name=call.func.id,
                            request_annotation=annotation,
                            dump_flags=flags,
                            excluded_fields=excluded,
                        )
                    )
    return sorted(sites, key=lambda site: (str(site.module.path), site.line))


def _request_body_schema_names(tree: SourceTree, api_root: Path) -> set[tuple[str, str]]:
    """Collect every schema actually used as an annotated endpoint parameter.

    Returns:
        ``(dotted module, class name)`` for each schema bound to a request body.
    """
    used: set[tuple[str, str]] = set()
    for module in tree.modules:
        if not module.path.is_relative_to(api_root):
            continue
        for function in ast.walk(module.tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for annotation in _annotated_parameters(function).values():
                parsed = parse_annotation(annotation)
                if not parsed.atoms:
                    continue
                resolved = tree.resolve(module, parsed.atoms[0])
                if resolved is not None:
                    used.add((resolved.module.dotted, resolved.name))
    return used


def build_pairings(tree: SourceTree, api_root: Path) -> list[Pairing]:
    """Pair request schemas with the domain models they are splatted into.

    Both rules from the module docstring are applied: construction sites first,
    then the exactly-named sibling update schema of every paired create schema.

    Args:
        tree: The parsed application tree.
        api_root: The API package.

    Returns:
        The pairings, deduplicated, in a stable order.
    """
    pairings: list[Pairing] = []
    seen: set[tuple[str, str, str, str]] = set()

    def remember(pairing: Pairing) -> bool:
        identity = (
            pairing.request.module.dotted,
            pairing.request.name,
            pairing.domain.module.dotted,
            pairing.domain.name,
        )
        if identity in seen:
            return False
        seen.add(identity)
        pairings.append(pairing)
        return True

    from_sites: list[Pairing] = []
    for site in find_construction_sites(tree, api_root):
        domain = tree.resolve(site.module, site.domain_name)
        parsed = parse_annotation(site.request_annotation)
        request = tree.resolve(site.module, parsed.atoms[0]) if parsed.atoms else None
        if domain is None or request is None:
            continue
        if not (is_pydantic_model(tree, domain) and is_pydantic_model(tree, request)):
            continue
        pairing = Pairing(
            request=request,
            domain=domain,
            path=site.module.path,
            line=site.line,
            origin="construction",
            forwards_none=not (site.dump_flags & NONE_SUPPRESSING_DUMP_FLAGS),
        )
        from_sites.append(pairing)
        remember(pairing)

    request_bodies = _request_body_schema_names(tree, api_root)
    for pairing in from_sites:
        stem = _create_stem(pairing.request.name)
        if stem is None:
            continue
        module = pairing.request.module
        for suffix in UPDATE_SUFFIXES:
            sibling = module.classes.get(f"{stem}{suffix}")
            if sibling is None:
                continue
            sibling_ref = ClassRef(module, sibling)
            if (module.dotted, sibling_ref.name) not in request_bodies:
                continue
            if not is_pydantic_model(tree, sibling_ref):
                continue
            remember(
                Pairing(
                    request=sibling_ref,
                    domain=pairing.domain,
                    path=module.path,
                    line=sibling.lineno,
                    origin=f"sibling of {pairing.request.name}",
                    # An update route hands the body to a service rather than
                    # splatting it here, so there is no dump call to read. The
                    # nullable shape is therefore not decidable and not reported.
                    forwards_none=False,
                )
            )
    return pairings


def _create_stem(name: str) -> str | None:
    """Return the resource stem of a create-schema name, or None.

    ``WateringLogCreate`` → ``WateringLog``. A name that is only the suffix
    (``Create``) yields None: it has no stem to match a sibling against.
    """
    for suffix in CREATE_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return None


# ── Finding detection ────────────────────────────────────────────────────────


def _justification_for(module: Module, line: int) -> str | None:
    """Return the exemption reason attached to a source line, if any.

    The marker is honoured on the line itself or the line directly above it, and
    the reason must carry content — a bare marker is not an exemption.

    Args:
        module: The module the field is declared in.
        line: 1-based line number of the field declaration.

    Returns:
        The reason text, or None.
    """
    for candidate in (line, line - 1):
        if not 1 <= candidate <= len(module.source_lines):
            continue
        text = module.source_lines[candidate - 1]
        marker = text.find(JUSTIFICATION_MARKER)
        if marker == -1:
            continue
        reason = text[marker + len(JUSTIFICATION_MARKER) :].strip()
        if len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def find_findings(tree: SourceTree, pairings: list[Pairing]) -> list[Finding]:
    """Compare every pairing field by field and report the certain widenings.

    Args:
        tree: The parsed application tree.
        pairings: The request-schema/domain-model pairs.

    Returns:
        The findings, in module then line order.
    """
    findings: list[Finding] = []
    for pairing in pairings:
        request_fields = model_fields(tree, pairing.request)
        domain_fields = model_fields(tree, pairing.domain)
        validated = self_validated_fields(tree, pairing.request)
        domain_coerces = has_before_model_validator(tree, pairing.domain)

        for name, (request_annotation, request_owner, request_line) in request_fields.items():
            if name not in domain_fields or name in validated:
                continue
            domain_annotation, domain_owner, _ = domain_fields[name]
            kind = _classify(
                tree,
                request_annotation=request_annotation,
                domain_annotation=domain_annotation,
                domain_owner=domain_owner,
                forwards_none=pairing.forwards_none,
                domain_coerces=domain_coerces,
            )
            if kind is None:
                continue
            findings.append(
                Finding(
                    kind=kind,
                    pairing=pairing,
                    field_name=name,
                    request_annotation=request_annotation.text,
                    domain_annotation=domain_annotation.text,
                    path=request_owner.module.path,
                    line=request_line,
                    justification=_justification_for(request_owner.module, request_line),
                )
            )
    return sorted(findings, key=lambda finding: (str(finding.path), finding.line, finding.field_name))


def _classify(
    tree: SourceTree,
    *,
    request_annotation: Annotation,
    domain_annotation: Annotation,
    domain_owner: ClassRef,
    forwards_none: bool,
    domain_coerces: bool,
) -> str | None:
    """Decide whether one field pair is a certain 500, and of which shape.

    Args:
        tree: The parsed application tree.
        request_annotation: The request schema's annotation of the field.
        domain_annotation: The domain model's annotation of the same field.
        domain_owner: The class declaring the domain field — the namespace the
            domain annotation's names resolve in.
        forwards_none: Whether the splat forwards a ``None`` rather than dropping it.
        domain_coerces: Whether the domain model runs a ``mode="before"`` validator.

    Returns:
        The finding kind, or None when the pair is safe or undecidable.
    """
    if len(domain_annotation.atoms) == 1 and set(request_annotation.atoms) == {"str"}:
        domain_type = tree.resolve(domain_owner.module, domain_annotation.atoms[0])
        if domain_type is not None and is_enum(tree, domain_type):
            return "enum_widened_to_str"

    if (
        request_annotation.optional
        and not domain_annotation.optional
        and forwards_none
        and not domain_coerces
        and domain_annotation.atoms
        and not set(domain_annotation.atoms) & NULL_TOLERANT_DOMAIN_ATOMS
        and "?" not in domain_annotation.atoms
    ):
        return "nullable_over_non_nullable"

    return None


# ── Reporting ────────────────────────────────────────────────────────────────


def _relative(path: Path) -> str:
    """Render a path relative to the repository root when possible."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _describe(finding: Finding) -> str:
    """Render one finding as a single, self-contained line."""
    return (
        f"  {_relative(finding.path)}:{finding.line}  "
        f"{finding.pairing.request.name}.{finding.field_name}: {finding.request_annotation}"
        f"   →   {finding.pairing.domain.name}.{finding.field_name}: {finding.domain_annotation}"
    )


ENUM_GUIDANCE = """\
  A request field typed `str` accepts any string; the domain field is an enum and
  rejects everything outside it — with a plain pydantic.ValidationError, which is
  not FastAPI's RequestValidationError and therefore answers 500, not 422.

  Fix it at the boundary (BACKEND.md §5.4): give the request field the same enum
  the domain model uses.

      from app.common.enums import ApplicationMethod

      class WateringLogCreate(BaseModel):
          application_method: ApplicationMethod = ApplicationMethod.DRENCH

  The endpoint then answers 422 with the permitted values, and the enum reaches
  the published OpenAPI document, so a consumer can see them without guessing."""

NULLABLE_GUIDANCE = """\
  The request field accepts null, the domain field does not, and the body is
  dumped without `exclude_unset=True`/`exclude_none=True` — so an omitted field is
  forwarded as None, which *disables* the domain default instead of falling back
  to it. That default only applies to a missing key. This is #966: every single
  request 500ed for 274 days.

  Two fixes, pick the one that states the intent:

      # the field is optional to *send*, never null → let the domain default win
      plan = NutrientPlan(**body.model_dump(exclude_unset=True), tenant_key=...)

      # the field is genuinely nullable → say so on the domain model too
      reference_substrate_type: SubstrateType | None = None"""


def report(findings: list[Finding], pairings: list[Pairing], baseline: int, list_all: bool) -> int:
    """Print the report and return the process exit code.

    Args:
        findings: Every finding, justified ones included.
        pairings: Every request/domain pairing found.
        baseline: The recorded ceiling for the enum-widened shape.
        list_all: Whether to name every pairing and every counted finding.

    Returns:
        ``EXIT_OK`` or ``EXIT_DEFECTS``.
    """
    justified = [finding for finding in findings if finding.justified]
    counted = [finding for finding in findings if not finding.justified]
    widened = [finding for finding in counted if finding.kind == "enum_widened_to_str"]
    nullable = [finding for finding in counted if finding.kind == "nullable_over_non_nullable"]

    print("Boundary validation check (#970, BACKEND.md §5.4)")
    print(f"  pairings: {len(pairings)} request schema(s) paired with a domain model")
    print(f"  enum widened to str:            {len(widened)}  (ceiling {baseline}, shrink-only)")
    print(f"  nullable over non-nullable:     {len(nullable)}  (no baseline — zero allowed)")
    if justified:
        print(f"  justified via {JUSTIFICATION_MARKER}  {len(justified)}")
    print()

    if list_all:
        for pairing in pairings:
            print(
                f"  pairing  {pairing.request.name} → {pairing.domain.name}"
                f"  ({_relative(pairing.path)}:{pairing.line}, {pairing.origin})"
            )
        print()
        for finding in counted:
            print(_describe(finding))
        if counted:
            print()
    for finding in justified:
        print(f"  justified  {_relative(finding.path)}:{finding.line}  {finding.field_name}: {finding.justification}")
    if justified:
        print()

    failed = False

    if nullable:
        print(f"FAILED — {len(nullable)} request field(s) forward a null the domain model rejects:\n")
        for finding in nullable:
            print(_describe(finding))
        print()
        print(NULLABLE_GUIDANCE)
        print()
        failed = True

    if len(widened) > baseline:
        print(
            f"FAILED — {len(widened)} request field(s) widen a domain enum to str, "
            f"{len(widened) - baseline} above the ceiling of {baseline}.\n"
        )
        print("  Every field counted, the new one among them:\n")
        for finding in widened:
            print(_describe(finding))
        print()
        print(ENUM_GUIDANCE)
        print()
        failed = True

    if failed:
        print(
            f"  If a field here is genuinely right as it stands, say why where it is declared,\n"
            f"  on its own line or the one above:\n"
            f"\n"
            f"      {JUSTIFICATION_MARKER} <why the domain model cannot reject this>\n"
            f"\n"
            f"  The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    if len(widened) < baseline:
        # Informational, not a defect — matching ``check_schema_examples.py`` and
        # the lesson of #973. Failing on a drop would make every concurrent pull
        # request that fixes a field collide on one integer, and resolving that
        # conflict by taking either side leaves a ceiling that is too high, which
        # loosens the gate invisibly.
        print(
            f"  {len(widened)} enum-widened field(s), below the recorded ceiling of {baseline} "
            f"(shrink-only — informational)."
        )
        print(
            f"  Ceiling can be lowered to {len(widened)} in MAX_ENUM_WIDENED_FIELDS "
            f"({_relative(Path(__file__).resolve())})."
        )
        return EXIT_OK

    print(
        f"OK — {len(widened)} enum-widened field(s), exactly at the recorded ceiling, and no "
        "nullable widening. The enum debt is deferred, not settled."
    )
    return EXIT_OK


def collect(app_root: Path) -> tuple[SourceTree, list[Pairing], list[Finding]]:
    """Parse the application and produce its pairings and findings.

    Args:
        app_root: The backend application package.

    Returns:
        The parsed tree, the pairings, and the findings.

    Raises:
        BoundaryCheckError: If the root is missing or a module cannot be parsed.
    """
    if not app_root.is_dir():
        raise BoundaryCheckError(f"application root does not exist: {app_root}")
    modules = [parse_module(path) for path in sorted(app_root.glob("**/*.py"))]
    tree = SourceTree(modules)
    pairings = build_pairings(tree, app_root / API_SUBPATH)
    return tree, pairings, find_findings(tree, pairings)


def main(argv: list[str] | None = None) -> int:
    """Run the boundary-validation check.

    Returns:
        0 when no nullable widening exists and the enum count is at or below the
        ceiling, 1 on a finding, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_boundary_validation.py",
        description=(
            "Report request schemas that accept input their domain model rejects — the shape that "
            "answers HTTP 500 instead of 422. The enum-widening count is compared against a "
            "shrink-only ceiling; a nullable widening is a plain defect."
        ),
    )
    parser.add_argument(
        "--app-root",
        metavar="PATH",
        help=f"the backend application package to scan (default: {DEFAULT_APP_ROOT})",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        metavar="N",
        help="override the recorded ceiling (for verifying the check itself, not for CI)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="name every pairing and every counted field",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    raw_root = args.app_root or DEFAULT_APP_ROOT
    app_root = Path(raw_root) if Path(raw_root).is_absolute() else REPO_ROOT / raw_root
    baseline = MAX_ENUM_WIDENED_FIELDS if args.baseline is None else args.baseline

    try:
        _tree, pairings, findings = collect(app_root)
    except BoundaryCheckError as exc:
        print(f"check_boundary_validation: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        counted = [finding for finding in findings if not finding.justified]
        widened = [finding for finding in counted if finding.kind == "enum_widened_to_str"]
        nullable = [finding for finding in counted if finding.kind == "nullable_over_non_nullable"]
        print(
            json.dumps(
                {
                    "pairings": len(pairings),
                    "enum_widened_to_str": len(widened),
                    "nullable_over_non_nullable": len(nullable),
                    "justified": len(findings) - len(counted),
                    "baseline": baseline,
                    "findings": [
                        {
                            "kind": finding.kind,
                            "module": _relative(finding.path),
                            "line": finding.line,
                            "request_model": finding.pairing.request.name,
                            "domain_model": finding.pairing.domain.name,
                            "field": finding.field_name,
                            "request_annotation": finding.request_annotation,
                            "domain_annotation": finding.domain_annotation,
                            "justification": finding.justification,
                        }
                        for finding in findings
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK if not nullable and len(widened) <= baseline else EXIT_DEFECTS

    return report(findings, pairings, baseline, args.list_all)


if __name__ == "__main__":
    raise SystemExit(main())
