"""#2078 — every service function that hands out a membership role checks it for escalation, or is classified.

The defect class: a guard applied opt-in at the call site, here for *who may be given which
role*. #2032 put a step-up on the tenant-scoped role route; the step-up proves who is asking,
not that they may be given the role, so a ``management`` holder in the ``platform`` tenant
sent their own password and became ``lead`` — the platform role (#2078). The invitation routes
carried the same hole one door over. A hand list of routes cannot notice the sibling it does
not name, so this guard enumerates the class **by what a function does**.

**Predicate** — a function (method or module function) under ``app/domain/services/`` is a
member when its own body

* writes the key ``"role"`` in a dict literal (``update_fields(key, {"role": ...})``), or
* assigns ``.role`` on a membership, or
* constructs ``Membership(role=...)`` or ``Invitation(role=...)`` (the two models that carry a
  role into a tenant).

Every member must either call ``self._refuse_role_grant(...)`` (the one place the rule of
``MembershipEngine.role_grant_refusal`` meets stored state) or be classified in
:data:`_CLASSIFIED` with the reason it needs none. A classification that no longer names a
live member fails, so the list cannot go stale and excuse the next copy.

**The rule** (REQ-024 AK-58): nobody raises their *own* role through the tenant-scoped route,
and ``lead`` in the ``platform`` tenant — the platform role — is handed out only by someone who
holds it. Outside the platform tenant a ``management`` holder may still appoint a lead
(REQ-049 §2.4).

**Spellings this predicate cannot see:** a role written through a key held in a variable, a
``**fields`` splat, ``setattr``, a role set by a repository method called under a neutral
name, a migration or seed (outside ``app/domain/services/``), and a router writing through the
repository directly (held by the no-``data_access``-import rule for routers).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
SERVICES = APP / "domain" / "services"

_ROLE_MODELS = {"Membership", "Invitation"}
_GATE = "_refuse_role_grant"

_CLASSIFIED: dict[tuple[str, str], str] = {
    ("tenant_service.py", "TenantService._found_tenant"): (
        "founding a new tenant (create_personal_tenant, create_organization): the founder is its lead by "
        "construction; a personal tenant or a new organisation is never the platform tenant (is_platform is "
        "seeded, not request-settable, REQ-024 AK-20), and there is no existing membership to raise"
    ),
    ("tenant_service.py", "TenantService.admin_change_membership_role"): (
        "platform-admin path: both routes require require_platform_admin and a platform admin may change any "
        "role in any tenant; the acting admin's step-up is checked here (#2032)"
    ),
    ("tenant_service.py", "TenantService.accept_invitation"): (
        "copies the role of an invitation whose creation passed the check (create_email_invitation, "
        "create_link_invitation); the accepting account chooses nothing"
    ),
}


def _own_nodes(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    """Every node of *function*'s body, nested functions and classes excluded."""
    nodes: list[ast.AST] = []
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(
            child
            for child in ast.iter_child_nodes(node)
            if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda)
        )
    return nodes


def _why_member(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """What makes *function* a role grant; empty when it is none."""
    reasons: list[str] = []
    for node in _own_nodes(function):
        if isinstance(node, ast.Dict):
            reasons += ["writes key 'role'" for k in node.keys if isinstance(k, ast.Constant) and k.value == "role"]
        elif isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            reasons += ["assigns .role" for t in targets if isinstance(t, ast.Attribute) and t.attr == "role"]
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name in _ROLE_MODELS:
                reasons += [f"constructs {name}(role=...)" for kw in node.keywords if kw.arg == "role"]
    return reasons


def _calls_the_gate(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == _GATE
        for node in _own_nodes(function)
    )


def _functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            found += [
                (f"{node.name}.{item.name}", item)
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
    return found


def members(root: Path = SERVICES) -> dict[tuple[str, str], tuple[list[str], bool]]:
    """Every member of the class: (file, qualname) -> (why, calls the gate)."""
    found: dict[tuple[str, str], tuple[list[str], bool]] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for qualname, function in _functions(ast.parse(path.read_text(encoding="utf-8"))):
            if why := _why_member(function):
                found[(rel, qualname)] = (why, _calls_the_gate(function))
    return found


#: The class size measured when this guard was written (#2078). A change in either direction is a
#: signal to read, not to update blindly: a new member needs the gate or a classification, a
#: vanished one may mean the predicate went blind.
#: +1 with #2137: create_service_account (viewer/grower, checked).
EXPECTED_MEMBERS = 8  # 8 until #2118 merged the two founding functions into ``_found_tenant``


def test_every_role_grant_checks_for_escalation_or_is_classified() -> None:
    ungated = sorted(
        f"{rel}::{name} ({', '.join(why)})"
        for (rel, name), (why, gated) in members().items()
        if not gated and (rel, name) not in _CLASSIFIED
    )

    assert ungated == [], (
        f"A service function that writes a membership or invitation role must call self.{_GATE} (#2078) "
        "or be classified with a reason:\n  " + "\n  ".join(ungated)
    )


def test_the_predicate_sees_the_class() -> None:
    """A predicate that found nothing would be green over nothing."""
    found = members()
    print(f"role-grant members: {len(found)}")  # noqa: T201 - the measured count, read by the reviewer
    for (rel, name), (why, gated) in sorted(found.items()):
        print(f"  {rel}::{name} gated={gated} {why}")  # noqa: T201

    assert len(found) == EXPECTED_MEMBERS, sorted(found)
    for known in (
        ("tenant_service.py", "TenantService.change_member_role"),
        ("tenant_service.py", "TenantService.create_email_invitation"),
        ("tenant_service.py", "TenantService.create_link_invitation"),
        ("tenant_service.py", "TenantService.admin_change_membership_role"),
    ):
        assert known in found, f"the predicate lost {known}"


def test_the_tenant_scoped_grants_are_gated() -> None:
    found = members()
    for entry in (
        ("tenant_service.py", "TenantService.change_member_role"),
        ("tenant_service.py", "TenantService.create_email_invitation"),
        ("tenant_service.py", "TenantService.create_link_invitation"),
        # #2106 - the platform-admin add meets the same rule behind its route's gate: ``lead`` in the
        # platform tenant is handed out only by someone who holds it. The entry that classified it is gone.
        ("tenant_service.py", "TenantService.admin_add_membership"),
    ):
        assert entry in found and found[entry][1], f"{entry} does not call self.{_GATE}"


def test_no_classification_is_stale() -> None:
    found = members()
    stale = sorted(f"{rel}::{name}" for rel, name in _CLASSIFIED if (rel, name) not in found)

    assert stale == []


def test_a_classified_entry_is_not_also_gated() -> None:
    """A classified member that calls the gate needs no excuse - the entry would outlive its reason."""
    found = members()
    both = sorted(f"{rel}::{name}" for rel, name in _CLASSIFIED if (rel, name) in found and found[(rel, name)][1])

    assert both == []


def test_the_gate_asks_the_engine_and_refuses() -> None:
    """A gate that stopped consulting the rule would leave every caller 'gated' over nothing."""
    tree = ast.parse((SERVICES / "tenant_service.py").read_text(encoding="utf-8"))
    (gate,) = [fn for name, fn in _functions(tree) if name == f"TenantService.{_GATE}"]
    calls = {
        node.func.attr
        for node in _own_nodes(gate)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    raised = {
        node.exc.func.id
        for node in _own_nodes(gate)
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name)
    }

    assert "role_grant_refusal" in calls
    assert "ForbiddenError" in raised


# ── self-tests: the predicate recognises every spelling it claims ──────────────


def _why(source: str) -> list[str]:
    (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
    return _why_member(function)


def test_the_predicate_recognises_each_spelling() -> None:
    assert _why("def f(self):\n    self._membership_repo.update_fields(k, {'role': r})")
    assert _why("def f(self, m):\n    m.role = r")
    assert _why("def f(self):\n    Membership(user_key=u, role=r)")
    assert _why("def f(self):\n    Invitation(tenant_key=t, role=r)")


def test_the_predicate_ignores_reads_and_other_keys() -> None:
    assert not _why("def f(self):\n    return self._membership_repo.get_by_key(k)")
    assert not _why("def f(self):\n    self._membership_repo.update_fields(k, {'admin_scopes': s})")
    assert not _why("def f(self):\n    Membership(user_key=u, tenant_key=t)")
    assert not _why("def f(self):\n    return m.role == r")


def test_the_gate_detection_sees_only_a_call_on_self() -> None:
    def gated(source: str) -> bool:
        (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
        return _calls_the_gate(function)

    assert gated(f"def f(self):\n    self.{_GATE}(a=1)")
    assert not gated(f"def f(self):\n    other.{_GATE}(a=1)")
    assert not gated(f"def f(self):\n    return self.{_GATE}")
