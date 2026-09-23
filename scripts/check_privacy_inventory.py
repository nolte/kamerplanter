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
      a name to its value; a named constant would read as "no attribution";
  R2  every collection the *export* manifest declares as personal data appears
      in the *erasure* inventory — the Art. 15 and Art. 17 answers to "what does
      this system hold about me" may not disagree;
  R3  both declared inventories are READ by executing code: ``build_export_manifest``
      and ``build_erasure_plan`` are called from a module under ``app/`` other
      than the engine that defines them;
  R4  no executing path writes a personal-data collection name down again — a
      user-scoped bulk removal must take its collection from the inventory, not
      from a literal or a ``collections.py`` constant.

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
6 executors / 16 sources / 27 edge-or-document steps),
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
* R2 compares collection names, not fields. A manifest entry that declares the
  right collection and the wrong field is the business of
  ``test_every_manifest_field_exists_on_its_model``.
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from source_text import is_called  # noqa: E402

BACKEND = pathlib.Path("src/backend")
APP_ROOT = BACKEND / "app"
ERASURE_ENGINE_REL = "domain/engines/erasure_engine.py"
EXPORT_ENGINE_REL = "domain/engines/data_export_engine.py"

#: The closed set of executors an inventory entry may name. Mirrors
#: ``app.domain.models.privacy.ErasureExecutor``; kept here as text because this
#: script must run without importing the application.
EXECUTORS = frozenset(
    {
        "account_cascade",
        "membership_cascade",
        "pest_image_cleanup",
        "storage_cleanup",
        "reference_index_cleanup",
        "retention_worker",
    }
)

#: Methods that return a declared personal-data inventory, and must be called by
#: executing code outside their own engine module (R3).
INVENTORY_READERS = {
    "build_erasure_plan": ERASURE_ENGINE_REL,
    "build_export_manifest": EXPORT_ENGINE_REL,
}

#: Helper whose whole purpose is removing documents by user reference (R4).
USER_SCOPED_REMOVAL = "_remove_docs_for_user"
EDGE_REMOVAL = "delete_edges"

#: Step kinds that filter a collection by the subject and therefore must name
#: the field they filter on (R5). ``user`` and ``phase`` carry their own rules.
FILTERED_KINDS = frozenset({"edge", "document"})
UNFILTERED_KINDS = frozenset({"user", "phase"})
EDGE_ENDPOINTS = frozenset({"_from", "_to"})

# Floors, deliberately below today's 32 / 6 / 16 / 27.
MIN_STEPS = 8
MIN_EXECUTORS = 2
MIN_MANIFEST_SOURCES = 10
MIN_FILTERED_STEPS = 6


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


def check(app_root: pathlib.Path = APP_ROOT) -> list[str]:
    violations: list[str] = []
    ERASURE_ENGINE = app_root / ERASURE_ENGINE_REL
    EXPORT_ENGINE = app_root / EXPORT_ENGINE_REL

    erasure_tree = ast.parse(ERASURE_ENGINE.read_text(encoding="utf-8"))
    export_tree = ast.parse(EXPORT_ENGINE.read_text(encoding="utf-8"))

    steps = _class_list_calls(erasure_tree, "ErasureEngine", "DELETE_STEPS")
    anon = _class_list_calls(erasure_tree, "ErasureEngine", "ANONYMIZE_COLLECTIONS")
    pseudo = _class_list_calls(erasure_tree, "ErasureEngine", "PSEUDONYMIZE_AUDIT_COLLECTIONS")
    manifest = _class_list_calls(export_tree, "DataExportEngine", "USER_DATA_MANIFEST")

    # ── R1: every inventory entry names an executor from the closed set ──
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
        elif executor not in EXECUTORS:
            violations.append(
                f"R1 {ERASURE_ENGINE}:{call.lineno} — inventory entry '{collection}' "
                f"names executor '{executor}', which is not one of {sorted(EXECUTORS)}."
            )
        else:
            executors.add(executor)

    # ── R2: the export inventory reconciles with the erasure inventory ──
    erasure_names = {
        name
        for call in (*steps, *anon, *pseudo)
        if (name := _kwarg(call, "collection")) is not None
    }
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

    # ── R3: both declared inventories are read by executing code ──
    for reader, defining_rel in INVENTORY_READERS.items():
        defining_module = app_root / defining_rel
        callers = [
            path
            for path in sorted(app_root.rglob("*.py"))
            if path != defining_module
            and is_called(reader, path.read_text(encoding="utf-8"), language="python")
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

    # ── Anti-vacuity: the reader above must have found an inventory ──
    if len(steps) < MIN_STEPS:
        violations.append(
            f"FLOOR {ERASURE_ENGINE} — read {len(steps)} inventory entries, expected at "
            f"least {MIN_STEPS}. Either the inventory collapsed or this script's reader did."
        )
    if len(executors) < MIN_EXECUTORS:
        violations.append(
            f"FLOOR {ERASURE_ENGINE} — read {len(executors)} distinct executor(s), expected "
            f"at least {MIN_EXECUTORS}."
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

    return violations


def main() -> int:
    if not APP_ROOT.is_dir():
        print(f"ERROR: {APP_ROOT} not found — run from the repository root.", file=sys.stderr)
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
    print("privacy inventory: one enumeration, attributed and read by the executing path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
