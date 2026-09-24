#!/usr/bin/env python3
"""Which ArangoDB collection backs which domain model — read off the repositories.

Two gates need the same fact: the privacy inventory (#1700, "is every stored
account reference reached by the erasure inventory?") and the tenant-scope guard
(#1708, "which repository reads must take a ``tenant_key``?"). Both anchor on the
models, and a model reaches a collection through exactly one place — the
repository that binds it. Two private copies of that reader would drift the way
every other pair of hand-maintained enumerations in this tree has, so this module
is the one implementation both import.

**Why AST and not an import.** ``check_privacy_inventory.py`` runs in the
required ``static`` lane on a bare runner with none of the backend's
dependencies, so this module must work without importing ``app``. The tenant
guard *can* import the application, and cross-checks this reader against the
runtime ``model_fields`` (``test_tenant_scoped_reads_are_derived.py``) so a
collapse of the AST reader shows up as a disagreement, not as a quietly smaller
inventory.

The spellings of a binding this reader resolves, stated because the question
"name a spelling my pattern misses" has real answers:

* ``class R(BaseArangoRepository[M])`` whose ``__init__`` calls
  ``super().__init__(db, <collection>)``;
* an inline ``BaseArangoRepository[M](db, <collection>, M)``, or the
  unsubscripted ``BaseArangoRepository(db, <collection>, M)`` whose model is only
  the third argument (``PropagationRepository``'s sibling collections — missed by
  the first version of this reader, #1708);
* a named repository subclass instantiated with its collection,
  ``_LocationRepository(db, col.LOCATIONS)`` — the ``_PlantingRunEntryRepository``
  / ``_PropagationEventRepository`` shape (:func:`repository_classes` only; the
  model-name map :func:`repository_bindings` the privacy gate reads records the
  two inline spellings above but not this one);
* a repository class that inherits its collection from a repository base, or
  calls ``BaseArangoRepository.__init__(self, db, <collection>)`` explicitly
  (``ArangoPhaseSequenceRepository``, :func:`repository_classes` only).

Not resolved: a collection passed as a parameter or computed at run time, a
repository that writes through ``self._db.collection(...)`` without binding a
model (``ArangoCalendarSourceRepository``, the MCP repositories) — those have a
collection but no model, and the callers decide what that means.
"""

from __future__ import annotations

import ast
import pathlib
from dataclasses import dataclass, field

COLLECTIONS_REL = "data_access/arango/collections.py"
DATA_ACCESS_REL = "data_access"
MODELS_REL = "domain/models"
BASE_REPOSITORY = "BaseArangoRepository"

#: Models whose repository does not bind them through ``BaseArangoRepository[M]``
#: (hand-written ``coll.insert`` in a repository bound to another model). Every
#: value must be a collection name ``collections.py`` declares — checked by the
#: privacy inventory (R6). Moved here from ``check_privacy_inventory.py`` (#1700)
#: so the tenant-scope guard (#1708) places the same models in the same
#: collections instead of keeping a second copy.
MODEL_COLLECTIONS_BY_HAND: dict[str, str] = {
    "TaskComment": "task_comments",  # task_repository.create_comment
    "TaskAuditEntry": "task_audit_entries",  # task_repository.create_audit_entry
    "WorkflowTemplate": "workflow_templates",  # task_repository (col.WORKFLOW_TEMPLATES)
    "Attachment": "attachments",  # attachment_repository (raw AQL over col.ATTACHMENTS)
    "OnboardingState": "onboarding_states",  # onboarding_state_repository (raw=True)
    "UserPreference": "user_preferences",  # user_preference_service (raw collection access)
    "McpAuditLog": "mcp_audit_log",  # mcp_repository.ArangoMcpAuditRepository
    "McpIdempotencyRecord": "mcp_idempotency_record",  # mcp_repository.ArangoMcpIdempotencyRepository
    # Added by #1708: raw-written collections the tenant-scope guard must place.
    # None of these carries a user-reference field, so R6 of the privacy gate
    # is unaffected by them.
    "TaskTemplate": "task_templates",  # task_repository (col.TASK_TEMPLATES)
    "WorkflowPhase": "workflow_phases",  # task_repository (col.WORKFLOW_PHASES)
    "WorkflowExecution": "workflow_executions",  # task_repository (col.WORKFLOW_EXECUTIONS)
    "PhaseDefinition": "phase_definitions",  # phase_sequence_repository (raw=True)
    "PhaseSequence": "phase_sequences",  # phase_sequence_repository
    "PhaseSequenceEntry": "phase_sequence_entries",  # phase_sequence_repository
    "StarterKit": "starter_kits",  # starter_kit_repository (raw)
    "SystemSettings": "system_settings",  # system_settings_repository (raw)
}

__all__ = [
    "BASE_REPOSITORY",
    "COLLECTIONS_REL",
    "DATA_ACCESS_REL",
    "MODELS_REL",
    "MODEL_COLLECTIONS_BY_HAND",
    "RepositoryClass",
    "collection_constants",
    "model_fields",
    "repository_bindings",
    "repository_classes",
    "resolve_collection",
    "subscript_model",
]


def collection_constants(app_root: pathlib.Path) -> dict[str, str]:
    """``NAME = "value"`` module-level string constants of ``collections.py``."""
    path = app_root / COLLECTIONS_REL
    if not path.is_file():
        return {}
    constants: dict[str, str] = {}
    for stmt in ast.parse(path.read_text(encoding="utf-8")).body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            constants[stmt.targets[0].id] = stmt.value.value
    return constants


def resolve_collection(node: ast.expr, constants: dict[str, str]) -> str | None:
    """A collection-name expression -> the name: a literal, ``col.X`` or a bare ``X``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Attribute):
        return constants.get(node.attr)
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def subscript_model(node: ast.expr) -> str | None:
    """``BaseArangoRepository[Model]`` -> ``"Model"``."""
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == BASE_REPOSITORY
        and isinstance(node.slice, ast.Name)
    ):
        return node.slice.id
    return None


def _inline_binding(call: ast.Call) -> str | None:
    """The model an inline repository construction binds, in either spelling.

    ``BaseArangoRepository[M](db, <collection>, M)`` names it in the subscript;
    the unsubscripted ``BaseArangoRepository(db, <collection>, M)`` — the
    ``PropagationRepository`` sibling collections — only in the third argument.
    """
    model = subscript_model(call.func)
    if model is not None:
        return model
    if isinstance(call.func, ast.Name) and call.func.id == BASE_REPOSITORY:
        if len(call.args) >= 3 and isinstance(call.args[2], ast.Name):
            return call.args[2].id
        for keyword in call.keywords:
            if keyword.arg == "model_cls" and isinstance(keyword.value, ast.Name):
                return keyword.value.id
    return None


def _is_explicit_base_init(call: ast.Call) -> bool:
    """``BaseArangoRepository.__init__(self, db, <collection>, ...)``."""
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "__init__"
        and isinstance(func.value, ast.Name)
        and func.value.id == BASE_REPOSITORY
    )


def _is_super_init(call: ast.Call) -> bool:
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "__init__"
        and isinstance(func.value, ast.Call)
        and isinstance(func.value.func, ast.Name)
        and func.value.func.id == "super"
    )


def _base_name(node: ast.expr) -> str | None:
    """``Base``, ``module.Base`` or ``Base[T]`` -> ``"Base"``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None


def _imports(tree: ast.Module) -> dict[str, str]:
    """``{local name: "module.path"}`` for every ``from X import Y`` in *tree*."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                found[alias.asname or alias.name] = node.module
    return found


@dataclass
class RepositoryClass:
    """One repository class under ``data_access``, as far as its source declares it.

    ``model_module`` is the module the model name was imported from in the
    repository's own file. It matters: ``QualityAssessment`` is defined twice
    under ``domain/models`` (``harvest.py`` and ``attachment.py``), and a
    name-keyed lookup picks whichever it met first.
    """

    name: str
    path: pathlib.Path
    node: ast.ClassDef
    base_names: tuple[str, ...]
    imports: dict[str, str]
    model: str | None = None
    collection: str | None = None
    #: ``self.<attribute>`` -> the collection of the sub-repository bound there.
    attributes: dict[str, str] = field(default_factory=dict)
    #: ``self.<attribute>`` -> the model name bound there (when one is).
    attribute_models: dict[str, str] = field(default_factory=dict)

    @property
    def model_module(self) -> str | None:
        return self.imports.get(self.model) if self.model else None


def repository_classes(
    app_root: pathlib.Path, constants: dict[str, str], *, include_plain: bool = False
) -> dict[str, RepositoryClass]:
    """Every class under ``data_access`` that is a ``BaseArangoRepository`` (transitively).

    With ``include_plain`` also every other class under ``data_access`` — the
    read-only multi-collection repositories (``ArangoCalendarSourceRepository``)
    and the facades that only *hold* bound sub-repositories
    (``PropagationRepository``) have no model of their own but still read.
    Their sub-repository attributes are resolved the same way.

    Keyed by class name. Two classes of the same name in different modules would
    collide; the tenant guard asserts none does.
    """
    root = app_root / DATA_ACCESS_REL
    classes: dict[str, RepositoryClass] = {}
    if not root.is_dir():
        return classes
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = _imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            models = [m for base in node.bases if (m := subscript_model(base)) is not None]
            classes[node.name] = RepositoryClass(
                name=node.name,
                path=path,
                node=node,
                base_names=tuple(n for base in node.bases if (n := _base_name(base)) is not None),
                imports=imports,
                model=models[0] if models else None,
            )

    def is_repository(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name == BASE_REPOSITORY:
            return True
        candidate = classes.get(name)
        if candidate is None or name in seen:
            return False
        return any(is_repository(base, seen | {name}) for base in candidate.base_names)

    repositories = {n: c for n, c in classes.items() if n != BASE_REPOSITORY and is_repository(n)}
    selected = {n: c for n, c in classes.items() if n != BASE_REPOSITORY} if include_plain else dict(repositories)
    for repo in repositories.values():
        for call in ast.walk(repo.node):
            if isinstance(call, ast.Call) and _is_super_init(call) and len(call.args) >= 2:
                repo.collection = resolve_collection(call.args[1], constants)
            elif isinstance(call, ast.Call) and _is_explicit_base_init(call) and len(call.args) >= 3:
                repo.collection = resolve_collection(call.args[2], constants)

    def inherited(name: str, seen: frozenset[str] = frozenset()) -> tuple[str | None, str | None]:
        repo = repositories.get(name)
        if repo is None or name in seen:
            return None, None
        if repo.collection:
            return repo.model, repo.collection
        for base in repo.base_names:
            model, collection = inherited(base, seen | {name})
            if collection:
                return repo.model or model, collection
        return repo.model, None

    for repo in selected.values():
        for stmt in ast.walk(repo.node):
            if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.value, ast.Call)):
                continue
            target = stmt.targets[0]
            if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)):
                continue
            if target.value.id != "self":
                continue
            call = stmt.value
            model = _inline_binding(call)
            collection: str | None = None
            if model is not None:
                collection = resolve_collection(call.args[1], constants) if len(call.args) >= 2 else None
            elif isinstance(call.func, ast.Name) and call.func.id in repositories:
                sub = repositories[call.func.id]
                model = sub.model
                if len(call.args) >= 2:
                    collection = resolve_collection(call.args[1], constants)
                if collection is None:
                    collection = inherited(call.func.id)[1]
            if collection:
                repo.attributes[target.attr] = collection
                if model:
                    repo.attribute_models[target.attr] = model

    for name, repo in repositories.items():
        if repo.collection is None:
            model, collection = inherited(name)
            repo.collection = collection
            repo.model = repo.model or model
    return selected


def repository_bindings(app_root: pathlib.Path, constants: dict[str, str]) -> dict[str, set[str]]:
    """Model class name -> the collections a repository binds it to.

    The spellings are the subclass ``class R(BaseArangoRepository[M])`` whose
    ``__init__`` calls ``super().__init__(db, <collection>)``, and an inline
    ``BaseArangoRepository[M](db, <collection>, M)``. Keyed by model *name*, which
    is what the privacy inventory (#1700) compares against; a caller that needs
    the defining module uses :func:`repository_classes`.
    """
    bindings: dict[str, set[str]] = {}
    root = app_root / DATA_ACCESS_REL
    if not root.is_dir():
        return bindings
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                models = [m for base in node.bases if (m := subscript_model(base)) is not None]
                if not models:
                    continue
                for call in ast.walk(node):
                    if isinstance(call, ast.Call) and _is_super_init(call) and len(call.args) >= 2:
                        collection = resolve_collection(call.args[1], constants)
                        if collection is not None:
                            for model in models:
                                bindings.setdefault(model, set()).add(collection)
            elif isinstance(node, ast.Call) and (model := _inline_binding(node)) is not None:
                if len(node.args) >= 2 and (collection := resolve_collection(node.args[1], constants)) is not None:
                    bindings.setdefault(model, set()).add(collection)
    return bindings


def model_fields(app_root: pathlib.Path) -> dict[tuple[str, str], set[str]]:
    """``{(module, class): field names}`` for every class under ``domain/models``.

    Inherited fields count: a field declared on a base class inside the models
    package is stored by every subclass. A base is resolved through the defining
    module first, then through that module's ``from X import Base``; a base
    outside the package (``BaseModel``) carries nothing readable and is skipped.
    ``module`` is the dotted import path (``app.domain.models.harvest``).
    """
    root = app_root / MODELS_REL
    found: dict[tuple[str, str], set[str]] = {}
    if not root.is_dir():
        return found
    classes: dict[tuple[str, str], tuple[list[str], set[str]]] = {}
    module_imports: dict[str, dict[str, str]] = {}
    for path in sorted(root.rglob("*.py")):
        module = "app." + str(path.relative_to(app_root)).removesuffix(".py").replace("/", ".")
        module = module.removesuffix(".__init__")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_imports[module] = _imports(tree)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            own = {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
            bases = [name for base in node.bases if (name := _base_name(base)) is not None]
            classes[(module, node.name)] = (bases, own)

    def resolve(module: str, name: str) -> tuple[str, str] | None:
        if (module, name) in classes:
            return (module, name)
        source = module_imports.get(module, {}).get(name)
        if source is not None and (source, name) in classes:
            return (source, name)
        return None

    def all_fields(ident: tuple[str, str], seen: frozenset[tuple[str, str]]) -> set[str]:
        bases, own = classes[ident]
        result = set(own)
        for base in bases:
            parent = resolve(ident[0], base)
            if parent is not None and parent not in seen and parent != ident:
                result |= all_fields(parent, seen | {ident})
        return result

    for ident in classes:
        found[ident] = all_fields(ident, frozenset())
    return found
