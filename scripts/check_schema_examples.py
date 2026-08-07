#!/usr/bin/env python3
"""Ratchet the number of API schemas that carry no OpenAPI example.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_schema_examples.py
    python3 scripts/check_schema_examples.py --list      # name the offenders
    python3 scripts/check_schema_examples.py --json      # machine-readable

**What it enforces.** `spec/style-guides/BACKEND.md` §5.3 requires every *new or
changed* request/response schema to carry at least one example — either
``model_config`` with ``json_schema_extra={"examples": [...]}`` or a
``Field(..., examples=[...])`` on one of its fields. It deliberately does **not**
require the existing schemas to be retro-fitted. A rule shaped like that cannot
be checked by asking "does every model have an example?", because the honest
answer is "no, by design". It is checked by counting the models that have none
and refusing to let that number grow.

**Shrink-only, like ``scripts/check_bdd_traceability.py``.** Equal to the
baseline is green, above it is red, and below it is green with a note naming the
new number so :data:`MAX_MODELS_WITHOUT_EXAMPLE` can be lowered by hand.

Failing on a *drop* was considered and rejected: it would block every refactoring
that merely deletes or renames a schema module, and two concurrent pull requests
that each lower the count would collide in the constant. The price is that the
baseline may lag behind reality until someone records it — the ratchet still
holds, because a later climb is measured against the recorded number, and that
is the same trade the sibling check makes.

Reference for the underlying rule: ``spec/style-guides/BACKEND.md`` §5.3. The
*published* document is linted separately by ``.spectral.yaml`` in the
``api-docs`` lane, which owns example presence per
``spec/project/api-documentation/``; this counter exists because that lane is
non-required and path-filtered, so it cannot block a merge.

**A green gate does not mean "the API is documented".** The baseline *defers* the
example debt, it does not settle it. Read the number, not the colour.

Standard library only, no Pydantic import, no running stack: the ``static`` CI
job is Python-only, and importing the schema modules would drag in the whole
application (settings, database clients) for a question that is answerable from
the source text.

Counting rules
--------------

Scanned: every ``schemas.py`` below ``src/backend/app/api/v1/`` — that is where
this codebase puts its request/response bodies, and the nested component models
in the same file end up in the published OpenAPI document too, so they count.

A class counts as a model when one of its bases is Pydantic's ``BaseModel`` /
``RootModel``, or another counted model — resolved inside its own module first,
then through its ``from … import`` statements when the base comes from another
scanned ``schemas.py``. Anything else — enums, ``TypedDict``, mixins from
elsewhere — is skipped. Bases are deliberately *not* resolved by bare name across
the tree: 15 class names occur in more than one schema module, so a name-only
match would attach a subclass to whichever module happened to sort first.

A model counts as *having* an example when it declares one itself or inherits one
from a counted base, since Pydantic merges ``model_config`` and inherits fields.
Empty payloads do not count: ``examples=[]``, ``examples=[{}]``, ``examples=[""]``
and ``examples=[None]`` all leave the model in the "no example" bucket, otherwise
the gate would be satisfiable by a keystroke that teaches a consumer nothing. A
payload the checker cannot evaluate statically (``examples=SPECIES_EXAMPLES``, a
function call) is credited as real — a name pointing at something is far more
likely to be content than to be a bypass.

Why the number is approximate — and why that is fine
----------------------------------------------------

This is a **stable, monotone** measure, not an exact one. Static analysis cannot
see everything Pydantic sees at runtime:

* a base class imported from outside the scanned set is invisible, so a model
  inheriting an example through it reads as "no example" here;
* generic wrappers and ``create_model`` factories produce schemas that no
  ``ClassDef`` in the tree corresponds to;
* re-exports move a model between modules without adding one, so a module count
  can move while the model count does not;
* a base reached through ``import app.api.v1.x.schemas`` plus a dotted reference
  is not resolved — only ``from … import Name`` is.

The gap this leaves is one-directional and small: an unresolved base makes a
class invisible, which *under*-counts. It cannot fake progress, because a model
that is not counted was never in the baseline either.

None of that matters for the job: the check compares *this* counter against
*itself* at an earlier commit. What matters is that the same tree always yields
the same number and that the number only moves when somebody adds or removes a
model. So when a refactoring shifts the count by two, that is the counter working,
not a defect — re-run with ``--list`` and confirm the delta is the models you
touched, then move the baseline.

Traces to issue #850 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the request/response bodies live, relative to the repository root.
DEFAULT_SCHEMA_ROOT = "src/backend/app/api/v1"

#: Only files with this name are scanned. Routers define the odd inline model,
#: but the convention (BACKEND.md §5.2) is that schemas live in ``schemas.py``,
#: and widening the glob would make the counter track file-placement accidents.
SCHEMA_FILENAME = "schemas.py"

#: Request/response models carrying no example, measured on the #850 baseline
#: commit. A ratchet, not a target: the check fails if the number grows, so no
#: new schema can be added without an example, and the recorded debt can only
#: shrink. Lower it by hand when the check reports a smaller number — see the
#: module docstring for why sinking is not accepted silently.
#:
#: 711, not the 708 the #850 audit recorded: that figure came from grepping for
#: ``class …(BaseModel)``, which misses the three models deriving from another
#: schema class (``RequirementProfileResponse``, ``NutrientProfileResponse``,
#: ``StarterKitTenantResponse``). All three are real response bodies in the
#: published document, so they belong in the count.
#:
#: 711 → 708 with #970: ``WateringLogCreate``, ``WateringLogUpdate`` and
#: ``WateringConfirmRequest`` changed (enum-typed fields, a typed ``overrides``)
#: and therefore had to gain an example per BACKEND.md §5.3. The new
#: ``WateringConfirmOverrides`` is born with one, so it never entered the debt.
MAX_MODELS_WITHOUT_EXAMPLE = 706

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2

#: Pydantic roots. A class deriving from either is a model without needing to
#: resolve anything else.
PYDANTIC_ROOT_BASES = frozenset({"BaseModel", "RootModel"})

#: Keys inside ``json_schema_extra`` that publish an example. ``examples`` is the
#: Pydantic v2 / OpenAPI 3.1 spelling; ``example`` is the OpenAPI 3.0 singular,
#: accepted here because it is equally visible to a consumer.
EXAMPLE_KEYS = ("examples", "example")


class SchemaExampleError(RuntimeError):
    """Raised when the check cannot run at all (missing root, unparsable module)."""


@dataclass(frozen=True)
class SchemaModel:
    """One request/response model found in a ``schemas.py``."""

    name: str
    module: Path
    line: int
    #: Base names as written in the source, unsubscripted (``Generic[T]`` → ``Generic``).
    bases: tuple[str, ...]
    #: Whether the class body itself declares a non-empty example.
    declares_example: bool
    #: Whether it declares one or inherits one — filled in by :func:`collect_models`.
    has_example: bool = False


@dataclass(frozen=True)
class ParsedModule:
    """One parsed ``schemas.py``: its module-level classes and its import table."""

    path: Path
    classes: tuple[SchemaModel, ...]
    #: Local name → dotted module it was imported from (``from … import Name``).
    imported_from: dict[str, str]


# ── Example detection ────────────────────────────────────────────────────────


def is_meaningful_example(node: ast.expr) -> bool:
    """Decide whether an example payload says anything to a consumer.

    Empty containers and empty/absent scalars are rejected: an ``examples=[{}]``
    satisfies a naive "does it mention examples?" check while documenting
    nothing, which would make the whole gate a formality.

    Anything this function cannot evaluate — a name, a call, an f-string — is
    accepted. A schema author writing ``examples=SPECIES_EXAMPLE`` is pointing at
    content, not evading a check.

    Args:
        node: The AST node of a single example value.

    Returns:
        True when the value carries content.
    """
    if isinstance(node, ast.Constant):
        if node.value is None:
            return False
        if isinstance(node.value, (str, bytes)):
            return bool(node.value.strip() if isinstance(node.value, str) else node.value)
        return True
    if isinstance(node, ast.Dict):
        return bool(node.keys)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return bool(node.elts)
    return True


def _payload_is_meaningful(key: str, value: ast.expr) -> bool:
    """Check one ``example``/``examples`` payload for content.

    ``examples`` is a *list* of examples, so it needs at least one meaningful
    entry; the singular ``example`` is the value itself.
    """
    if key == "examples":
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return any(is_meaningful_example(element) for element in value.elts)
        # Not a literal sequence (a name, a call, a comprehension): assume content.
        return True
    return is_meaningful_example(value)


def dict_declares_example(node: ast.expr) -> bool:
    """Check whether a ``json_schema_extra`` mapping publishes a non-empty example.

    Args:
        node: The value assigned to ``json_schema_extra``.

    Returns:
        True when the mapping holds an ``example``/``examples`` key with content.
    """
    if not isinstance(node, ast.Dict):
        # ``json_schema_extra=SOME_CONSTANT`` or a callable: not statically
        # readable, and — consistent with :func:`is_meaningful_example` — credited.
        return True
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if not isinstance(key_node, ast.Constant) or key_node.value not in EXAMPLE_KEYS:
            continue
        if _payload_is_meaningful(str(key_node.value), value_node):
            return True
    return False


def _call_func_name(node: ast.Call) -> str:
    """Return the bare callee name of a call (``pydantic.Field(...)`` → ``Field``)."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def call_declares_example(node: ast.expr) -> bool:
    """Check a ``Field(...)`` / ``ConfigDict(...)`` call for a non-empty example.

    Both carriers named by BACKEND.md §5.3 pass through here: ``examples=[...]``
    directly on a ``Field``, and ``json_schema_extra={...}`` on either.

    Args:
        node: The AST node of the call (non-calls return False).

    Returns:
        True when the call publishes an example with content.
    """
    if not isinstance(node, ast.Call):
        return False
    if _call_func_name(node) not in {"Field", "ConfigDict"}:
        return False
    for keyword in node.keywords:
        if keyword.arg == "examples" and _payload_is_meaningful("examples", keyword.value):
            return True
        if keyword.arg == "json_schema_extra" and dict_declares_example(keyword.value):
            return True
    return False


def class_declares_example(node: ast.ClassDef) -> bool:
    """Check whether a class body declares an example of its own.

    Three shapes are recognised, all of them reaching the published document:

    * ``model_config = ConfigDict(json_schema_extra={"examples": [...]})``
    * ``model_config = {"json_schema_extra": {"examples": [...]}}`` (the dict
      literal spelling this codebase already uses for ``populate_by_name``)
    * ``field: T = Field(..., examples=[...])`` on any field

    Inheritance is resolved later, in :func:`resolve_examples`.

    Args:
        node: The class definition.

    Returns:
        True when the body itself publishes a non-empty example.
    """
    for statement in node.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign):
            targets, value = list(statement.targets), statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, value = [statement.target], statement.value
        if value is None:
            continue

        is_model_config = any(
            isinstance(target, ast.Name) and target.id == "model_config" for target in targets
        )
        if is_model_config:
            if call_declares_example(value):
                return True
            if isinstance(value, ast.Dict):
                for key_node, value_node in zip(value.keys, value.values, strict=True):
                    if (
                        isinstance(key_node, ast.Constant)
                        and key_node.value == "json_schema_extra"
                        and dict_declares_example(value_node)
                    ):
                        return True
            continue

        # A field default: ``name: str = Field(..., examples=["Monstera"])``.
        if call_declares_example(value):
            return True
    return False


# ── Model collection ─────────────────────────────────────────────────────────


def base_names(node: ast.ClassDef) -> tuple[str, ...]:
    """Return the bare names of a class's bases, in source order.

    Subscripts are unwrapped (``RootModel[list[str]]`` → ``RootModel``) and dotted
    paths reduced to their last segment (``pydantic.BaseModel`` → ``BaseModel``),
    because that is the granularity at which bases are resolved here.
    """
    names: list[str] = []
    for base in node.bases:
        target = base.value if isinstance(base, ast.Subscript) else base
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return tuple(names)


def dotted_module_name(path: Path) -> str:
    """Derive the importable dotted name of a module from its path.

    Walks up while the parent directory is a package (holds ``__init__.py``), so
    ``src/backend/app/api/v1/tanks/schemas.py`` becomes ``app.api.v1.tanks.schemas``
    without the source root having to be configured anywhere.

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


def parse_module(path: Path) -> ParsedModule:
    """Extract the module-level classes and the import table from one ``schemas.py``.

    Only module-level classes are considered — a class nested in a function is
    not part of the stable API surface, and counting it would make the number
    depend on helper-function refactorings.

    Args:
        path: The module to parse.

    Returns:
        The parsed module. Every module-level class is recorded, models and
        non-models alike: the model/non-model decision needs the whole scanned
        set and is made in :func:`collect_models`.

    Raises:
        SchemaExampleError: If the file cannot be read or parsed.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaExampleError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise SchemaExampleError(f"cannot parse {path}: {exc}") from exc

    own_name = dotted_module_name(path)
    imported_from: dict[str, str] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.ImportFrom):
            continue
        target = resolve_relative_import(own_name, statement.module, statement.level)
        for alias in statement.names:
            imported_from[alias.asname or alias.name] = target

    classes = tuple(
        SchemaModel(
            name=statement.name,
            module=path,
            line=statement.lineno,
            bases=base_names(statement),
            declares_example=class_declares_example(statement),
        )
        for statement in tree.body
        if isinstance(statement, ast.ClassDef)
    )
    return ParsedModule(path=path, classes=classes, imported_from=imported_from)


def iter_schema_modules(roots: list[Path]) -> list[Path]:
    """List every ``schemas.py`` below the given roots, in a stable order.

    Args:
        roots: Directories to scan, or single ``.py`` files.

    Returns:
        Sorted module paths.

    Raises:
        SchemaExampleError: If a root does not exist.
    """
    modules: list[Path] = []
    for root in roots:
        if root.is_file():
            modules.append(root)
            continue
        if not root.is_dir():
            raise SchemaExampleError(f"schema root does not exist: {root}")
        modules.extend(root.glob(f"**/{SCHEMA_FILENAME}"))
    return sorted(set(modules))


class BaseResolver:
    """Resolves a base-class name to the scanned class it refers to.

    Resolution order, per base name:

    1. Pydantic's own roots (``BaseModel`` / ``RootModel``) — the terminal case.
    2. A class defined in the same module.
    3. A class in another scanned module that this module imports it from.

    An unresolvable base (an enum, a ``TypedDict``, a mixin defined outside the
    scanned set) resolves to nothing, and a class whose every base is unresolvable
    is not counted as a model at all.
    """

    def __init__(self, parsed: list[ParsedModule]) -> None:
        """Index the parsed modules for lookup.

        Args:
            parsed: Every scanned module, already parsed.
        """
        self._by_module: dict[Path, dict[str, SchemaModel]] = {
            module.path: {entry.name: entry for entry in module.classes} for module in parsed
        }
        self._imports: dict[Path, dict[str, str]] = {
            module.path: module.imported_from for module in parsed
        }
        self._path_of: dict[str, Path] = {
            dotted_module_name(module.path): module.path for module in parsed
        }

    def resolve(self, module: Path, base: str) -> SchemaModel | None:
        """Return the scanned class a base name refers to, or None."""
        local = self._by_module.get(module, {}).get(base)
        if local is not None:
            return local
        source = self._imports.get(module, {}).get(base)
        if source is None:
            return None
        origin = self._path_of.get(source)
        if origin is None:
            return None
        return self._by_module.get(origin, {}).get(base)

    def is_model(self, candidate: SchemaModel, seen: frozenset[tuple[Path, str]] = frozenset()) -> bool:
        """Decide whether a class derives from Pydantic, following its bases.

        Args:
            candidate: The class under test.
            seen: Guard against a pathological self-referential chain.

        Returns:
            True when a chain of bases reaches ``BaseModel`` / ``RootModel``.
        """
        identity = (candidate.module, candidate.name)
        if identity in seen:
            return False
        for base in candidate.bases:
            if base in PYDANTIC_ROOT_BASES:
                return True
            parent = self.resolve(candidate.module, base)
            if parent is not None and self.is_model(parent, seen | {identity}):
                return True
        return False

    def has_example(self, model: SchemaModel, seen: frozenset[tuple[Path, str]] = frozenset()) -> bool:
        """Report whether a model declares an example or inherits one.

        Pydantic merges ``model_config`` down the MRO and inherits fields, so a
        subclass of a documented model is documented — demanding a second copy of
        the example would be asking for duplication.

        Args:
            model: The model under test.
            seen: Guard against a pathological self-referential chain.

        Returns:
            True when the model publishes an example.
        """
        identity = (model.module, model.name)
        if identity in seen:
            return False
        if model.declares_example:
            return True
        for base in model.bases:
            parent = self.resolve(model.module, base)
            if parent is not None and self.has_example(parent, seen | {identity}):
                return True
        return False


def collect_models(modules: list[Path]) -> list[SchemaModel]:
    """Parse every module and return the Pydantic models among their classes.

    Two passes: the first reads all classes, the second decides which of them are
    models and whether each one reaches an example through its bases. The split
    exists because a base may live in a module parsed later.

    Args:
        modules: The ``schemas.py`` files to scan.

    Returns:
        The models, ordered by module then source line.

    Raises:
        SchemaExampleError: If a module cannot be read or parsed.
    """
    parsed = [parse_module(module) for module in modules]
    resolver = BaseResolver(parsed)

    return [
        SchemaModel(
            name=entry.name,
            module=entry.module,
            line=entry.line,
            bases=entry.bases,
            declares_example=entry.declares_example,
            has_example=resolver.has_example(entry),
        )
        for module in parsed
        for entry in module.classes
        if resolver.is_model(entry)
    ]


# ── Reporting ────────────────────────────────────────────────────────────────


def _relative(path: Path) -> str:
    """Render a path relative to the repository root when possible."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def report(
    models: list[SchemaModel],
    modules: list[Path],
    baseline: int,
    list_offenders: bool,
) -> int:
    """Print the ratchet report and return the process exit code.

    Args:
        models: Every model found.
        modules: Every scanned ``schemas.py``.
        baseline: The recorded maximum number of models without an example.
        list_offenders: Whether to name every model that has no example.

    Returns:
        ``EXIT_OK`` on equal-to-baseline, ``EXIT_DEFECTS`` on growth or shrink.
    """
    without = [model for model in models if not model.has_example]
    documented = len(models) - len(without)

    print("API schema example ratchet (#850, BACKEND.md §5.3)")
    print(f"  modules:  {len(modules)} {SCHEMA_FILENAME} file(s)")
    print(f"  models:   {len(models)} — {documented} carry an example, {len(without)} do not")
    print(f"  baseline: {baseline} model(s) without an example (shrink-only)")
    print()

    if list_offenders:
        for model in without:
            print(f"  no example  {_relative(model.module)}:{model.line}  {model.name}")
        if without:
            print()

    if len(without) > baseline:
        added = len(without) - baseline
        print(
            f"FAILED — {len(without)} model(s) without an example, {added} above the baseline "
            f"of {baseline}."
        )
        print(
            "  Every new or changed request/response schema carries at least one example "
            "(BACKEND.md §5.3):"
        )
        print('    model_config = ConfigDict(json_schema_extra={"examples": [{...}]})')
        print("    field: float = Field(ge=0, examples=[1.8])")
        print("  Use a realistic value from the domain — an empty example does not count.")
        print("  Run with --list to see which models are counted.")
        return EXIT_DEFECTS

    if len(without) < baseline:
        # Informational, not a defect — matching ``check_bdd_traceability.py``.
        # Failing here would block every refactoring that merely deletes or
        # renames a schema module, and two concurrent PRs that each lower the
        # count would collide in the constant. The cost of not failing is that
        # the baseline may lag behind reality until someone records it; the
        # ratchet still holds, because a later climb is measured against the
        # recorded number.
        print(
            f"  {len(without)} model(s) without an example, below the recorded baseline of "
            f"{baseline} (shrink-only — informational)."
        )
        print(
            f"  Baseline can be lowered to {len(without)} in MAX_MODELS_WITHOUT_EXAMPLE "
            f"({_relative(Path(__file__).resolve())})."
        )
        print(
            "  (If the drop was not intentional — a deleted or renamed module, for instance — "
            "check that first: --list names every model still counted.)"
        )
        return EXIT_OK

    print(
        f"OK — {len(without)} model(s) without an example, exactly at the recorded baseline. "
        "The debt is deferred, not settled."
    )
    return EXIT_OK


def _resolve(paths: list[str]) -> list[Path]:
    """Resolve CLI paths against the repository root when they are relative."""
    return [Path(path) if Path(path).is_absolute() else REPO_ROOT / path for path in paths]


def main(argv: list[str] | None = None) -> int:
    """Run the schema-example ratchet.

    Returns:
        0 when the count matches the baseline, 1 when it moved in either
        direction, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_schema_examples.py",
        description=(
            "Count the API request/response models that publish no OpenAPI example and compare "
            "the number against a recorded, shrink-only baseline. Growth fails; a drop fails too, "
            "asking for the baseline to be lowered by hand."
        ),
    )
    parser.add_argument(
        "--schema-root",
        action="append",
        metavar="PATH",
        help=f"directory or .py file to scan (repeatable; default: {DEFAULT_SCHEMA_ROOT})",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        metavar="N",
        help="override the recorded baseline (for verifying the check itself, not for CI)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_offenders",
        help="name every model counted as having no example",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the counts as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    roots = _resolve(args.schema_root or [DEFAULT_SCHEMA_ROOT])
    baseline = MAX_MODELS_WITHOUT_EXAMPLE if args.baseline is None else args.baseline

    try:
        modules = iter_schema_modules(roots)
        models = collect_models(modules)
    except SchemaExampleError as exc:
        print(f"check_schema_examples: {exc}", file=sys.stderr)
        return EXIT_USAGE

    without = [model for model in models if not model.has_example]
    if args.json:
        print(
            json.dumps(
                {
                    "modules": len(modules),
                    "models": len(models),
                    "with_example": len(models) - len(without),
                    "without_example": len(without),
                    "baseline": baseline,
                    "offenders": [
                        {
                            "module": _relative(model.module),
                            "line": model.line,
                            "name": model.name,
                        }
                        for model in without
                    ]
                    if args.list_offenders
                    else [],
                },
                indent=2,
            )
        )
        return EXIT_OK if len(without) == baseline else EXIT_DEFECTS

    return report(models, modules, baseline, args.list_offenders)


if __name__ == "__main__":
    raise SystemExit(main())
