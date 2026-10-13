"""One permission source for the tenant-scoped CRUD gates — MT-045.6 (#2144), REQ-024 AK-44c.

Two matrices decided the same question. ``require_permission`` (every router)
decides on the :class:`MembershipEngine` predicates; ``require_attachment_permission``
(the attachment, photo and pest-image routes) decided on the descriptive matrix
``app.core.permissions._RBAC`` through ``has_permission``. Nothing compared the
two, and they had already drifted once (grower delete, corrected by hand). The
audit found them equal on attachments today and the matrix silent on the five
resources the routers name by a free string (``"diary-entry"`` and friends) — a
matrix that says "denied" where the gate admits.

Now:

1. the attachment guard decides through the same function as ``require_permission``
   (:func:`app.common.auth.role_permits`) — proven by behaviour over every role and
   every action, not by reading its source;
2. every ``(resource, action)`` a router wires through either dependency names a
   :class:`ResourceType` member, so the descriptive matrix *can* describe it;
3. for each wired pair and each role the matrix (``has_permission``) says what the
   gate does — the AK-44c comparison, so neither source is maintained alone;
4. nothing outside the matrix module and this guard reads the matrix to decide
   (``assert_permission``/``list_permissions`` had no caller and are gone).

Spellings (2) cannot see: a resource passed through a variable or a call result;
it is reported as unresolved and fails, so it cannot slip by as "covered".
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import app.core.permissions as matrix
from app.api.v1.attachments.permissions import require_attachment_permission
from app.common.auth import require_permission
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError
from app.core.permissions import Action, ResourceType, has_permission
from app.domain.models.tenant_context import TenantContext

APP = Path(__file__).resolve().parents[3] / "app"
_GATES = {"require_permission", "require_attachment_permission"}


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(tenant_key="t1", tenant_slug="t1", user_key="u1", role=role, admin_scopes=[])


def _admits(dependency, role: TenantRole) -> bool:  # noqa: ANN001
    try:
        dependency(ctx=_ctx(role))
    except ForbiddenError:
        return False
    return True


def _wired_pairs() -> tuple[set[tuple[ResourceType, Action]], list[str]]:
    pairs: set[tuple[ResourceType, Action]] = set()
    unresolved: list[str] = []
    for path in sorted((APP / "api").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _GATES):
                continue
            where = f"{path.relative_to(APP).as_posix()}:{node.lineno} {ast.unparse(node)}"
            if node.func.id == "require_attachment_permission":
                resource_node, action_node = None, node.args[0]
            else:
                resource_node, action_node = node.args[0], node.args[1]
            resource = ResourceType.ATTACHMENT if resource_node is None else _member(resource_node, ResourceType)
            action = _member(action_node, Action)
            if resource is None or action is None:
                unresolved.append(where)
                continue
            pairs.add((resource, action))
    return pairs, unresolved


def _member(node: ast.expr, enum: type) -> object | None:
    """``ResourceType.X`` / ``Action.X`` → the member; anything else (a string, a variable) → ``None``."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == enum.__name__:
        return enum[node.attr]
    return None


@pytest.mark.parametrize("action", list(Action), ids=lambda a: a.value)
@pytest.mark.parametrize("role", list(TenantRole), ids=lambda r: r.value)
def test_the_attachment_guard_decides_like_require_permission(role: TenantRole, action: Action) -> None:
    assert _admits(require_attachment_permission(action), role) == _admits(
        require_permission(ResourceType.ATTACHMENT, action), role
    )


def test_every_wired_resource_is_a_matrix_member() -> None:
    pairs, unresolved = _wired_pairs()

    assert len(pairs) >= 40, "the sweep found almost nothing — a blind scan would pass vacuously"
    assert unresolved == [], (
        "require_permission / require_attachment_permission with a resource or action that is not a "
        "ResourceType / Action member — the descriptive matrix cannot describe it (REQ-024 AK-44c):\n  "
        + "\n  ".join(unresolved)
    )


def test_the_matrix_says_what_the_gate_does_for_every_wired_pair() -> None:
    pairs, _ = _wired_pairs()
    drift = sorted(
        f"{resource.value}/{action.value} {role.value}: matrix={has_permission(role, resource, action)} "
        f"gate={_admits(require_permission(resource, action), role)}"
        for resource, action in pairs
        for role in TenantRole
        if has_permission(role, resource, action) != _admits(require_permission(resource, action), role)
    )

    assert drift == [], "app/core/permissions.py and the router gate disagree:\n  " + "\n  ".join(drift)


def test_nothing_outside_the_matrix_decides_on_it() -> None:
    readers = sorted(
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if path != Path(matrix.__file__)
        and any(
            isinstance(node, ast.ImportFrom)
            and node.module == "app.core.permissions"
            and any(alias.name in {"has_permission", "assert_permission", "list_permissions"} for alias in node.names)
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        )
    )

    assert readers == [], f"a second permission source reads the descriptive matrix: {readers}"
    assert not hasattr(matrix, "assert_permission"), "assert_permission had no caller; it is not a gate"
    assert not hasattr(matrix, "list_permissions"), "list_permissions had no caller; it is not a gate"
