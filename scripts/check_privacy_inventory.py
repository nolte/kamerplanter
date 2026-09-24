#!/usr/bin/env python3
"""A declared personal-data inventory must be the one the executing path reads (#1622).

The defect
----------
REQ-025 / NFR-011 carry two statutory duties over the same subject matter: Art. 15
says what a data subject must be shown, Art. 17 says what must go. The repository
declared both — ``DataExportEngine.USER_DATA_MANIFEST`` and
``ErasureEngine.build_erasure_plan`` — and neither had a call site. The export and
erasure that *do* run walked a different enumeration, hand-written at the point of
execution.

Measured on 2026-09-21, before the repair: the declared erasure plan named 26
ArangoDB collections; the executing account cascade reached 11. Symmetric
difference 23. Four collections the cascade actually removes (``api_keys``,
``user_preferences``, ``onboarding_states``, ``memberships``) appeared in no
declared inventory at all, and ``tasks`` — declared personal data for export —
appeared in no erasure enumeration.

Why a guard and not just the repair
-----------------------------------
Two lists that must agree and are never compared drift. This pair already had,
for as long as both existed. Repairing today's 23 differences leaves the 24th,
added next month, exactly as invisible. So this hook does not check today's
collection names. It enumerates the CLASS:

  R1  every entry of the erasure inventory is attributed to an executor drawn
      from the closed enum, spelled as a literal — an inventory that cannot say
      who erases an entry is documentation, not a plan. The literal is required
      because this script reads the file without importing it and cannot resolve
      a name to its value; a named constant would read as "no attribution".
      The closed enum is READ from ``ErasureExecutor`` in
      ``domain/models/privacy.py`` (#1645), not kept here as a second copy:
      until #1645 this script carried its own list, and retiring a name
      (``retention_worker``, which meant "no executor yet") had to be done in
      two places that nothing compared;
  R2  every collection the *export* manifest declares as personal data appears
      in the *erasure* inventory — the Art. 15 and Art. 17 answers to "what does
      this system hold about me" may not disagree. Since #1719 in both
      directions: every collection the erasure deletes or anonymises (a non-phase
      delete step, an anonymisation or pseudonymisation rule) is a manifest
      source, or is named in ``DataExportEngine.EXCLUDED_FROM_DISCLOSURE`` with a
      literal reason. The erasure removing it is the proof it is the subject's
      data; an exclusion is the written claim that it adds nothing a disclosed
      source does not already deliver. An exclusion for a collection the erasure
      does not reach, or that is also disclosed, is stale and refused;
  R3  both declared inventories are READ by executing code: ``build_export_manifest``
      and ``build_erasure_plan`` are called from a module under ``app/`` other
      than the engine that defines them;
  R4  no executing path writes a personal-data collection name down again — a
      user-scoped bulk removal must take its collection from the inventory, not
      from a literal or a ``collections.py`` constant;
  R5  every filtered step and every rule names the field it matches (#1663);
  R6  every persisted model field shaped like an account key (``user_key``,
      ``*_user_key``, ``*_by_key``, ``*_account_key``, ``*_by``) is reached by
      the erasure inventory — a document step, a rule's key or one of its
      ``clear_fields`` — or named in ``ErasureEngine.EXCLUDED_USER_REFERENCES``
      with a reason (#1700).

Why R6 exists
-------------
R2 compares the export manifest with the erasure inventory and nothing else. A
collection absent from *both* passes it. Measured on 2026-09-24 before #1700:
R6 named 23 stored model fields in neither list (plus five models it could not
yet place in a collection) — among them
``ai_conversations.user_key``, ``notifications.user_key``,
``calendar_feeds.user_key``, ``task_comments.created_by``,
``invitations.invited_by_user_key``, ``tenants.owner_user_key``,
``pest_image_contributions.promoted_by``, ``attachments.created_by`` — while
R1–R5 were green. The anchor is the models, which nobody edits to satisfy a
privacy list. A model is placed in its collection through its repository
(``BaseArangoRepository[M]`` + the collection it passes), or through
:data:`MODEL_COLLECTIONS_BY_HAND` where the repository writes raw — both read
from ``scripts/arango_repository_bindings.py``, which the tenant-scope guard
(#1708) shares, so the two gates cannot disagree about where a model lives; a model it
cannot place is reported, never skipped.

A comment cannot satisfy it
---------------------------
R1, R2 and R4 are read off the **AST**, where comments do not exist. R3 goes
through :func:`scripts.source_text.is_called`, which strips comments and
docstrings before looking for a call — the vacuum trap repaired in #1545, #1610
and #1624 and generalised in #1456. A docstring that says "walks the manifest"
satisfies nothing here.

The anti-vacuity floors
-----------------------
:data:`MIN_STEPS`, :data:`MIN_EXECUTORS`, :data:`MIN_MANIFEST_SOURCES` and
:data:`MIN_FILTERED_STEPS` sit **deliberately below** today's inventory (32 steps /
5 executors / 16 sources / 27 edge-or-document steps),
far enough that a legitimate shrink does not trip them. They exist to catch this
script's own reader collapsing — an AST walk that silently returns nothing would
otherwise report a green tree with no inventory at all, which is the failure mode
a gate about missing enumerations must not have.

Known blind spots (the honest residue)
--------------------------------------
* R4 knows one user-scoped removal helper, ``_remove_docs_for_user``, plus
  ``delete_edges`` *in a function that also calls it* (the account-cascade
  shape). Since #1664 no production code calls that helper: every user-scoped
  removal runs in ``ArangoErasureExecutor``, which binds each collection from
  the plan (``@@collection``). R4 stays as the tripwire for a copy of the old
  shape coming back; it does not inspect the executor's bind variables. A cascade written with raw AQL, with a differently named helper, or
  with the edge deletion split into its own function is not seen. Spellings of
  the same thing it does not match, stated rather than assumed:
  ``db.aql.execute("... REMOVE ... users/...")``, ``self._purge(col.API_KEYS, key)``,
  a collection name passed through a local variable assigned from a constant.
* R3 proves a call exists, not that the call result is used. A caller that reads
  the manifest and throws it away passes.
* R6 sees only fields whose *name* has one of its shapes, declared on a model
  under ``domain/models`` or on a base class inside that package (#1700
  review). A ``where``-filtered document step covers its field only together
  with a rule or an exclusion for the remaining rows. A key stored as ``author`` or ``owner``, nested
  in a dict/list, or written by a repository without a model (raw dicts) is not
  seen. It checks that a field is *declared*, not that the declared step reaches
  it — that is the reach test's job (``test_account_erasure_reach.py``).
* R2 (reverse) takes an exclusion's reason on trust; that an excluded edge
  belongs to a disclosed document is pinned by
  ``test_every_excluded_edge_belongs_to_a_disclosed_document``, not here.
  Measured on 2026-09-24 before #1719, the reverse direction named 20
  collections: 5 were exported as a result (``user_favorites``, ``api_keys``,
  ``user_preferences``, ``onboarding_states``, ``pest_detections``), 15 edges
  were excluded.
* R2 compares collection names, not fields. A manifest entry that declares the
  right collection and the wrong field is the business of
  ``test_every_manifest_field_exists_on_its_model``.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from arango_repository_bindings import (  # noqa: E402
    COLLECTIONS_REL,
    MODEL_COLLECTIONS_BY_HAND,
    collection_constants,
    repository_bindings,
)
from source_text import is_called  # noqa: E402

BACKEND = pathlib.Path("src/backend")
APP_ROOT = BACKEND / "app"
ERASURE_ENGINE_REL = "domain/engines/erasure_engine.py"
EXPORT_ENGINE_REL = "domain/engines/data_export_engine.py"
PRIVACY_MODELS_REL = "domain/models/privacy.py"
MODELS_REL = "domain/models"

#: The alias in :data:`PRIVACY_MODELS_REL` that declares the closed set of
#: executors an inventory entry may name (R1). Read off the AST, because this
#: script must run without importing the application.
EXECUTOR_ALIAS = "ErasureExecutor"

#: Methods that return a declared personal-data inventory, and must be called by
#: executing code outside their own engine module (R3).
INVENTORY_READERS = {
    "build_erasure_plan": ERASURE_ENGINE_REL,
    "build_export_manifest": EXPORT_ENGINE_REL,
}

#: The list on ``DataExportEngine`` that names erasure targets which are
#: deliberately not disclosed, each with its reason (R2 reverse, #1719).
DISCLOSURE_EXCLUSIONS = "EXCLUDED_FROM_DISCLOSURE"

#: Helper whose whole purpose is removing documents by user reference (R4).
USER_SCOPED_REMOVAL = "_remove_docs_for_user"
EDGE_REMOVAL = "delete_edges"

#: Step kinds that filter a collection by the subject and therefore must name
#: the field they filter on (R5). ``user`` and ``phase`` carry their own rules.
FILTERED_KINDS = frozenset({"edge", "document"})
UNFILTERED_KINDS = frozenset({"user", "phase"})
EDGE_ENDPOINTS = frozenset({"_from", "_to"})

# Floors, deliberately below today's 32 / 5 / 16 / 27.
MIN_STEPS = 8
MIN_EXECUTORS = 2
MIN_MANIFEST_SOURCES = 10
MIN_FILTERED_STEPS = 6

# ── R6: the anchor outside the two lists (#1700) ─────────────────────────────
#
#: A persisted model field whose name says "this holds an account key". Derived
#: from what ``domain/models`` spells on 2026-09-24, not from the inventory:
#:
#: * ``user_key`` and ``*_user_key`` — ``Membership.user_key``,
#:   ``Invitation.invited_by_user_key``, ``Tenant.owner_user_key``,
#:   ``Task.assigned_to_user_key`` …
#: * ``*_by_key`` — the server-set attribution of #1669 (``harvested_by_key`` …)
#: * ``*_account_key`` — ``McpAuditLog.service_account_key`` (a ``users`` key)
#: * ``*_by`` — ``created_by``, ``promoted_by``, ``contributed_by``,
#:   ``dismissed_by``, ``uploaded_by`` … Some of these are free text typed by the
#:   caller (``performed_by``, ``harvester``'s siblings); the pattern takes them
#:   all, and a free-text field is classified by an exclusion that says so rather
#:   than by the pattern guessing.
#:
#: What it does not match, stated rather than assumed: a key stored under a name
#: without one of these shapes (``author``, ``owner``), a key nested inside a
#: dict or list field, and a model this script cannot place in a collection is
#: *reported*, not skipped (see :data:`MODEL_COLLECTIONS_BY_HAND`).
USER_REFERENCE_FIELD = re.compile(
    r"^(user_key|[a-z0-9_]+_user_key|[a-z0-9_]+_by_key|[a-z0-9_]+_account_key|[a-z0-9_]+_by)$"
)


#: Models that carry a user-reference field but are never stored as documents.
#: The reason is the claim a reviewer checks; an unplaceable model not named here
#: is a violation, so a new stored model cannot fall through silently.
NOT_PERSISTED_MODELS: dict[str, str] = {
    "TenantContext": "request-scoped auth context, built per request (common/auth.py)",
    "ErasurePlan": "the plan itself, built in memory by ErasureEngine.build_erasure_plan",
    "MemberInfo": "read projection of memberships joined with users (tenant_service.list_members)",
}

#: Floor for R6. Measured on 2026-09-24: 52 user-reference model fields
#: (``main`` prints the count on every green run). The floor sits a small margin
#: below that — not at a token 6 — so a reader that loses one models module, or
#: the base-class walk, trips it instead of shrinking R6 silently. A legitimate
#: removal of more than four such fields lowers it here, in the same change.
MIN_USER_REFERENCE_FIELDS = 48


def _class_list_calls(tree: ast.AST, class_name: str, attr: str) -> list[ast.Call]:
    """Return the ``Call`` elements of ``<class_name>.<attr> = [...]``."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for stmt in node.body:
            target = None
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target = stmt.target.id
            elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0].id
            if target != attr or not isinstance(stmt.value, ast.List):
                continue
            return [e for e in stmt.value.elts if isinstance(e, ast.Call)]
    return []


def _closed_executor_set(tree: ast.AST) -> frozenset[str]:
    """The string members of ``type ErasureExecutor = Literal[...]`` (or a plain assignment).

    Returns an empty set when the alias is missing or is not a literal union of
    strings; the caller reports that rather than checking R1 against nothing.
    """
    for node in ast.walk(tree):
        value: ast.expr | None = None
        if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name) and node.name.id == EXECUTOR_ALIAS:
            value = node.value
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == EXECUTOR_ALIAS
        ):
            value = node.value
        if not isinstance(value, ast.Subscript):
            continue
        members = value.slice.elts if isinstance(value.slice, ast.Tuple) else [value.slice]
        return frozenset(m.value for m in members if isinstance(m, ast.Constant) and isinstance(m.value, str))
    return frozenset()


def _kwarg(call: ast.Call, name: str) -> str | None:
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return None


def _is_written_down_name(node: ast.expr) -> bool:
    """True when *node* is a collection name spelled out rather than read.

    A string literal, or an attribute whose name is a constant (``col.API_KEYS``).
    ``step.collection`` — an attribute whose name is lower-case — is a value read
    from the inventory and passes.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    return isinstance(node, ast.Attribute) and node.attr.isupper()


def _base_name(node: ast.expr) -> str | None:
    """``Base`` or ``module.Base`` -> ``"Base"``; anything else (``Generic[T]``) -> ``None``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _user_reference_fields(app_root: pathlib.Path) -> list[tuple[pathlib.Path, int, str, str]]:
    """``(file, line, model, field)`` for every model field :data:`USER_REFERENCE_FIELD` matches.

    Inherited fields count (#1700 review): a field declared on a base class
    inside the models package is stored by every subclass, so it is reported
    once per subclass, at the line of its declaration. A base is resolved in its
    own module first, then by name across the package. A name defined in
    several other modules is not guessed at: the subclass inherits the fields of
    *every* candidate — fail closed, a field R6 then asks about that the model
    does not store is a loud false positive, where a guess could be a silent
    false negative. A base outside the package (``BaseModel``) carries nothing
    this script can read and is skipped.
    """
    found: list[tuple[pathlib.Path, int, str, str]] = []
    root = app_root / MODELS_REL
    if not root.is_dir():
        return found
    # (path, name) -> (bases, own fields as (line, name))
    classes: dict[tuple[pathlib.Path, str], tuple[list[str], list[tuple[int, str]]]] = {}
    by_name: dict[str, list[pathlib.Path]] = {}
    for path in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.ClassDef):
                continue
            fields = [
                (stmt.lineno, stmt.target.id)
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            ]
            bases = [name for base in node.bases if (name := _base_name(base)) is not None]
            classes[(path, node.name)] = (bases, fields)
            by_name.setdefault(node.name, []).append(path)

    def resolve(path: pathlib.Path, name: str) -> list[tuple[pathlib.Path, str]]:
        if (path, name) in classes:
            return [(path, name)]
        return [(candidate, name) for candidate in by_name.get(name, [])]

    def all_fields(
        ident: tuple[pathlib.Path, str], seen: frozenset[tuple[pathlib.Path, str]]
    ) -> list[tuple[pathlib.Path, int, str]]:
        bases, own = classes[ident]
        result = [(ident[0], line, name) for line, name in own]
        for base in bases:
            for parent in resolve(ident[0], base):
                if parent not in seen and parent != ident:
                    result.extend(all_fields(parent, seen | {ident}))
        return result

    for ident in classes:
        model = ident[1]
        names_seen: set[str] = set()
        for field_path, line, field in all_fields(ident, frozenset()):
            if field in names_seen or not USER_REFERENCE_FIELD.match(field):
                continue
            names_seen.add(field)
            found.append((field_path, line, model, field))
    return found


def _has_where(call: ast.Call) -> bool:
    """True unless ``where=`` is absent or a literal empty dict; an unreadable value counts as a filter."""
    for kw in call.keywords:
        if kw.arg == "where":
            return not (isinstance(kw.value, ast.Dict) and not kw.value.keys)
    return False


def _list_kwarg(call: ast.Call, name: str) -> list[str]:
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.List):
            return [e.value for e in kw.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def check(app_root: pathlib.Path = APP_ROOT) -> list[str]:
    violations: list[str] = []
    ERASURE_ENGINE = app_root / ERASURE_ENGINE_REL
    EXPORT_ENGINE = app_root / EXPORT_ENGINE_REL
    PRIVACY_MODELS = app_root / PRIVACY_MODELS_REL

    erasure_tree = ast.parse(ERASURE_ENGINE.read_text(encoding="utf-8"))
    export_tree = ast.parse(EXPORT_ENGINE.read_text(encoding="utf-8"))

    steps = _class_list_calls(erasure_tree, "ErasureEngine", "DELETE_STEPS")
    anon = _class_list_calls(erasure_tree, "ErasureEngine", "ANONYMIZE_COLLECTIONS")
    pseudo = _class_list_calls(erasure_tree, "ErasureEngine", "PSEUDONYMIZE_AUDIT_COLLECTIONS")
    manifest = _class_list_calls(export_tree, "DataExportEngine", "USER_DATA_MANIFEST")

    # ── R1: every inventory entry names an executor from the closed set ──
    closed_set: frozenset[str] = frozenset()
    if PRIVACY_MODELS.is_file():
        closed_set = _closed_executor_set(ast.parse(PRIVACY_MODELS.read_text(encoding="utf-8")))
    if not closed_set:
        violations.append(
            f"R1 {PRIVACY_MODELS} — no '{EXECUTOR_ALIAS}' literal union of executor names "
            f"could be read; without the closed set no inventory entry can be attributed."
        )
    executors: set[str] = set()
    for call in steps:
        collection = _kwarg(call, "collection") or "<unnamed>"
        executor = _kwarg(call, "executor")
        if executor is None:
            violations.append(
                f"R1 {ERASURE_ENGINE}:{call.lineno} — inventory entry '{collection}' "
                f"carries no literal executor=; an entry nobody is attributed to is "
                f"documentation, not a plan."
            )
        elif executor not in closed_set:
            violations.append(
                f"R1 {ERASURE_ENGINE}:{call.lineno} — inventory entry '{collection}' "
                f"names executor '{executor}', which is not one of {sorted(closed_set)} "
                f"({EXECUTOR_ALIAS} in {PRIVACY_MODELS})."
            )
        else:
            executors.add(executor)

    # ── R2: the export inventory reconciles with the erasure inventory ──
    erasure_names = {name for call in (*steps, *anon, *pseudo) if (name := _kwarg(call, "collection")) is not None}
    manifest_names: set[str] = set()
    for call in manifest:
        for key in ("collection", "edge_collection"):
            if (name := _kwarg(call, key)) is not None:
                manifest_names.add(name)
                if name not in erasure_names:
                    violations.append(
                        f"R2 {EXPORT_ENGINE}:{call.lineno} — '{name}' is declared personal "
                        f"data for Art. 15 export but appears in no erasure inventory entry. "
                        f"What must be disclosed must also be erasable."
                    )

    # ── R2 (reverse, #1719): what the erasure removes because it is the
    # subject's is disclosed, or excluded with the reason ──
    #
    # The forward direction alone let ``user_favorites`` through: deleted on
    # erasure (so demonstrably the subject's) and absent from the Art. 15
    # bundle. Every non-phase delete step and every anonymisation or
    # pseudonymisation rule names a collection that holds the subject's data;
    # each must be a manifest source, or appear in
    # ``DataExportEngine.EXCLUDED_FROM_DISCLOSURE`` with a literal reason.
    erasure_targets: dict[str, int] = {}
    for call in (*steps, *anon, *pseudo):
        name = _kwarg(call, "collection")
        if name is None or _kwarg(call, "kind") == "phase":
            continue
        erasure_targets.setdefault(name, call.lineno)
    disclosure_exclusions: dict[str, int] = {}
    for call in _class_list_calls(export_tree, "DataExportEngine", DISCLOSURE_EXCLUSIONS):
        name, reason = _kwarg(call, "collection"), _kwarg(call, "reason")
        if not name or not reason or not reason.strip():
            violations.append(
                f"R2 {EXPORT_ENGINE}:{call.lineno} — a disclosure exclusion must name a literal "
                f"collection= and a non-empty reason=; an exclusion without a reason is a hole."
            )
            continue
        disclosure_exclusions[name] = call.lineno
    for name, lineno in sorted(erasure_targets.items()):
        if name in manifest_names or name in disclosure_exclusions:
            continue
        violations.append(
            f"R2 {ERASURE_ENGINE}:{lineno} — '{name}' is erased or anonymised as the subject's data but is "
            f"not disclosed under Art. 15. Declare it in DataExportEngine.USER_DATA_MANIFEST, or name it in "
            f"DataExportEngine.{DISCLOSURE_EXCLUSIONS} with the reason it is not the subject's data."
        )
    for name, lineno in sorted(disclosure_exclusions.items()):
        if name not in erasure_targets:
            violations.append(
                f"R2 {EXPORT_ENGINE}:{lineno} — the disclosure exclusion '{name}' names no collection the "
                f"erasure inventory removes or anonymises; a stale exclusion hides the next one of that name."
            )
        elif name in manifest_names:
            violations.append(
                f"R2 {EXPORT_ENGINE}:{lineno} — '{name}' is both a manifest source and excluded from "
                f"disclosure; one of the two is wrong."
            )

    # ── R3: both declared inventories are read by executing code ──
    for reader, defining_rel in INVENTORY_READERS.items():
        defining_module = app_root / defining_rel
        callers = [
            path
            for path in sorted(app_root.rglob("*.py"))
            if path != defining_module and is_called(reader, path.read_text(encoding="utf-8"), language="python")
        ]
        if not callers:
            violations.append(
                f"R3 {defining_module} — '{reader}' has no call site under {app_root} "
                f"outside its own module. A declared personal-data inventory that the "
                f"executing path does not read is the split #1622 measured."
            )

    # ── R4: no executing path spells a personal-data collection out again ──
    for path in sorted(app_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
            removes = [c for c in calls if c.func.attr == USER_SCOPED_REMOVAL]  # type: ignore[union-attr]
            if not removes:
                continue
            watched = removes + [c for c in calls if c.func.attr == EDGE_REMOVAL]  # type: ignore[union-attr]
            for call in watched:
                if call.args and _is_written_down_name(call.args[0]):
                    violations.append(
                        f"R4 {path}:{call.lineno} — the user-scoped removal in "
                        f"'{fn.name}' spells its collection out instead of taking it "
                        f"from the declared inventory. Walk "
                        f"ErasureEngine.build_erasure_plan(...).steps."
                    )

    # ── R5: every filtered step and every rule names its user field ──
    filtered_steps = 0
    for call in steps:
        collection = _kwarg(call, "collection") or "<unnamed>"
        kind = _kwarg(call, "kind")
        if kind in UNFILTERED_KINDS:
            continue
        if kind not in FILTERED_KINDS:
            violations.append(
                f"R5 {ERASURE_ENGINE}:{call.lineno} — inventory entry '{collection}' carries no "
                f"literal kind= from {sorted(FILTERED_KINDS | UNFILTERED_KINDS)}; this script "
                f"cannot tell whether it must name a user field, so it refuses it."
            )
            continue
        filtered_steps += 1
        user_field = _kwarg(call, "user_field")
        if not user_field:
            violations.append(
                f"R5 {ERASURE_ENGINE}:{call.lineno} — {kind} entry '{collection}' names no "
                f"literal user_field=; an executor cannot find the subject's rows without "
                f"guessing, and a guessed filter deletes somebody else's data."
            )
        elif kind == "edge" and user_field not in EDGE_ENDPOINTS:
            violations.append(
                f"R5 {ERASURE_ENGINE}:{call.lineno} — edge entry '{collection}' is keyed on "
                f"'{user_field}'; an edge reaches the subject through one of "
                f"{sorted(EDGE_ENDPOINTS)}."
            )
    for call in (*anon, *pseudo):
        if not _kwarg(call, "user_field"):
            collection = _kwarg(call, "collection") or "<unnamed>"
            violations.append(
                f"R5 {ERASURE_ENGINE}:{call.lineno} — rule for '{collection}' names no literal "
                f"user_field=; a rule that cannot say which field it matches is inert."
            )

    # ── R6: every stored user reference is inventoried or excluded (#1700) ──
    #
    # R2 compares the export manifest with the erasure inventory and nothing
    # else, so a collection absent from BOTH is invisible to it. #1700 measured
    # twelve such surfaces. The anchor here is the models: every persisted model
    # field shaped like an account key must be matched by a delete step, an
    # anonymisation / pseudonymisation rule (its key or one of its
    # ``clear_fields``), or a written exclusion — for the collection that stores
    # the model.
    constants = collection_constants(app_root)
    bindings = repository_bindings(app_root, constants)
    known_collections = set(constants.values())
    references = _user_reference_fields(app_root)
    for model in sorted({model for _p, _l, model, _f in references} & MODEL_COLLECTIONS_BY_HAND.keys()):
        collection = MODEL_COLLECTIONS_BY_HAND[model]
        if collection not in known_collections:
            violations.append(
                f"R6 {app_root / COLLECTIONS_REL} — MODEL_COLLECTIONS_BY_HAND maps '{model}' to "
                f"'{collection}', which collections.py does not declare."
            )
    covered: set[tuple[str, str]] = set()
    # A document step with a non-empty ``where`` removes only the matching rows
    # (``attachments`` of category ``pest_reference``). It covers the field only
    # together with a rule or an exclusion for the rest (#1700 review).
    partial: dict[tuple[str, str], int] = {}
    for call in steps:
        c, f = _kwarg(call, "collection"), _kwarg(call, "user_field")
        if _kwarg(call, "kind") == "document" and c and f:
            if _has_where(call):
                partial.setdefault((c, f), call.lineno)
            else:
                covered.add((c, f))
    for call in (*anon, *pseudo):
        c = _kwarg(call, "collection")
        if c is None:
            continue
        if f := _kwarg(call, "user_field"):
            covered.add((c, f))
        covered.update((c, cleared) for cleared in _list_kwarg(call, "clear_fields"))
    excluded: dict[tuple[str, str], int] = {}
    for call in _class_list_calls(erasure_tree, "ErasureEngine", "EXCLUDED_USER_REFERENCES"):
        c, f, reason = _kwarg(call, "collection"), _kwarg(call, "user_field"), _kwarg(call, "reason")
        if not c or not f or not reason or not reason.strip():
            violations.append(
                f"R6 {ERASURE_ENGINE}:{call.lineno} — an exclusion must name a literal collection=, "
                f"user_field= and a non-empty reason=; an exclusion without a reason is a hole."
            )
            continue
        excluded[(c, f)] = call.lineno
    seen_pairs: set[tuple[str, str]] = set()
    for path, lineno, model, field in references:
        if model in NOT_PERSISTED_MODELS:
            continue
        collections = set(bindings.get(model, set()))
        if model in MODEL_COLLECTIONS_BY_HAND:
            collections.add(MODEL_COLLECTIONS_BY_HAND[model])
        if not collections:
            violations.append(
                f"R6 {path}:{lineno} — model '{model}' carries the user reference '{field}', and no "
                f"repository binds it to a collection this script can read. Bind it through "
                f"BaseArangoRepository[{model}], or name its collection in MODEL_COLLECTIONS_BY_HAND "
                f"(or NOT_PERSISTED_MODELS, with the reason) in {pathlib.Path(__file__).name}."
            )
            continue
        for collection in sorted(collections):
            seen_pairs.add((collection, field))
            if (collection, field) in covered or (collection, field) in excluded:
                continue
            if (collection, field) in partial:
                violations.append(
                    f"R6 {path}:{lineno} — '{collection}.{field}' ({model}) is removed only by the "
                    f"where-filtered step at {ERASURE_ENGINE}:{partial[(collection, field)]}; the rows "
                    f"outside that where keep the account reference. Add an anonymisation rule for "
                    f"them, or exclude the field with the reason."
                )
                continue
            violations.append(
                f"R6 {path}:{lineno} — '{collection}.{field}' ({model}) holds an account reference and is in "
                f"neither the erasure inventory nor ErasureEngine.EXCLUDED_USER_REFERENCES. Declare a "
                f"delete step or an anonymisation rule, or exclude it with the reason."
            )
    for (collection, field), lineno in sorted(excluded.items()):
        if (collection, field) not in seen_pairs:
            violations.append(
                f"R6 {ERASURE_ENGINE}:{lineno} — the exclusion '{collection}.{field}' names no stored model "
                f"field this script finds; a stale exclusion hides the next field of that name."
            )

    # ── Anti-vacuity: the reader above must have found an inventory ──
    if len(steps) < MIN_STEPS:
        violations.append(
            f"FLOOR {ERASURE_ENGINE} — read {len(steps)} inventory entries, expected at "
            f"least {MIN_STEPS}. Either the inventory collapsed or this script's reader did."
        )
    if len(executors) < MIN_EXECUTORS:
        violations.append(
            f"FLOOR {ERASURE_ENGINE} — read {len(executors)} distinct executor(s), expected at least {MIN_EXECUTORS}."
        )
    if filtered_steps < MIN_FILTERED_STEPS:
        violations.append(
            f"FLOOR {ERASURE_ENGINE} — read {filtered_steps} filtered (edge/document) "
            f"inventory entries, expected at least {MIN_FILTERED_STEPS}; R5 over none is vacuous."
        )
    if len(manifest_names) < MIN_MANIFEST_SOURCES:
        violations.append(
            f"FLOOR {EXPORT_ENGINE} — read {len(manifest_names)} manifest source(s), "
            f"expected at least {MIN_MANIFEST_SOURCES}."
        )

    if len(references) < MIN_USER_REFERENCE_FIELDS:
        violations.append(
            f"FLOOR {app_root / MODELS_REL} — read {len(references)} user-reference model field(s), "
            f"expected at least {MIN_USER_REFERENCE_FIELDS}; R6 over none is vacuous."
        )

    return violations


def main() -> int:
    if not APP_ROOT.is_dir():
        print(
            f"ERROR: {APP_ROOT} not found — run from the repository root.",
            file=sys.stderr,
        )
        return 2
    violations = check()
    if violations:
        print(
            "\nA declared personal-data inventory is not the one the executing path reads (#1622).\n",
            file=sys.stderr,
        )
        for site in violations:
            print(f"  FAIL {site}", file=sys.stderr)
        return 1
    references = _user_reference_fields(APP_ROOT)
    names = sorted({field for _path, _line, _model, field in references})
    print(f"R6 user-reference fields ({USER_REFERENCE_FIELD.pattern}): {', '.join(names)}")
    print(f"R6 measured {len(references)} user-reference model field(s); floor {MIN_USER_REFERENCE_FIELDS}.")
    print("privacy inventory: one enumeration, attributed and read by the executing path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
