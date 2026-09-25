"""Every deletion of a stored object asks whether another record still holds it (#1770).

Deduplicated uploads give every uploader a record of their own over **one**
stored object. The defect #1770 closed was a destructive path that treated "this
record goes" as "these bytes go": the single delete, the Phase 0 erasure and the
thumbnail discard each removed an object another member's record still pointed
at. The fix put one question in front of each of them —
``storage_keys_held_elsewhere`` — and this guard makes that question part of the
shape of the code rather than of three reviews.

The selector is the whole class, not the three sites: **every** call in ``app/``
to the object-storage delete methods (``delete_object``, ``delete_prefix``),
wherever it sits. Each enclosing function must either ask the question itself,
or be named below with the reason the objects it deletes are never shared
attachment objects. A new destructive path fails here until it does one or the
other.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[3] / "app"

#: The storage-adapter methods that remove bytes.
DELETE_METHODS = frozenset({"delete_object", "delete_prefix"})

#: The question a caller asks before deleting an object records may share.
HOLDER_QUESTION = "storage_keys_held_elsewhere"

#: ``(path relative to app/, function)`` → why the objects it deletes are never an
#: object another attachment record could share.
NOT_SHARED: dict[tuple[str, str], str] = {
    ("data_access/storage/s3_adapter.py", "_delete_sync"): (
        "the adapter's own implementation of delete_object; callers decide what to delete"
    ),
    ("domain/services/tenant_service.py", "_purge_tenant_storage"): (
        "tenant deletion: every record of the tenant goes, and no other tenant's record can hold a "
        "t/{tenant}/ object (dedup is tenant-scoped)"
    ),
    ("domain/services/privacy_service.py", "_fail_export"): (
        "an Art. 15 export bundle under privacy/exports/<user>/, written once per request, never an attachment"
    ),
    ("domain/services/privacy_service.py", "_run_export_file_cleanup"): (
        "the subject's Art. 15 export bundles, never an attachment"
    ),
    ("domain/services/privacy_service.py", "expire_data_exports"): (
        "expired Art. 15 export bundles, never an attachment"
    ),
}


def _calls_in(node: ast.AST, relative: str, function: ast.AST | None, found: dict) -> None:
    """Record ``(relative, innermost function)`` for every delete-method call under *node*."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            _calls_in(child, relative, child, found)
            continue
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr in DELETE_METHODS
            and isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef)
        ):
            found[(relative, function.name)] = function
        _calls_in(child, relative, function, found)


def _destructive_functions() -> dict[tuple[str, str], ast.AST]:
    """``(path, innermost function)`` for every call to a delete method in app/."""
    found: dict[tuple[str, str], ast.AST] = {}
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        _calls_in(tree, path.relative_to(APP_ROOT).as_posix(), None, found)
    return found


def _asks_the_holder_question(function: ast.AST) -> bool:
    return any(isinstance(node, ast.Attribute) and node.attr == HOLDER_QUESTION for node in ast.walk(function))


def test_the_selector_sees_the_known_destructive_paths():
    # A selector that found nothing would pass everything below.
    found = set(_destructive_functions())
    assert ("domain/services/attachment_service.py", "delete") in found
    assert ("data_access/storage/local_fs_adapter.py", "erase_user_objects") in found
    assert ("tasks/storage_tasks.py", "_generate") in found


def test_every_stored_object_delete_asks_whether_another_record_holds_it():
    offenders = [
        f"{path}::{name}"
        for (path, name), function in sorted(_destructive_functions().items())
        if (path, name) not in NOT_SHARED and not _asks_the_holder_question(function)
    ]
    assert offenders == [], (
        "these functions delete stored objects without asking "
        f"`{HOLDER_QUESTION}` whether another record still holds them (#1770): {offenders}. "
        "Ask it, or add the function to NOT_SHARED with the reason its objects are never shared."
    )


def test_every_exemption_still_names_a_destructive_path():
    stale = sorted(set(NOT_SHARED) - set(_destructive_functions()))
    assert stale == [], f"NOT_SHARED names functions that no longer delete stored objects: {stale}"
