"""#2111 - every service function that mutates a tenant membership writes the security audit, or is classified.

The defect class: a persistent audit applied opt-in at the call site. ``admin_add_membership``,
the role and scope changes, the removals, leaving and the creation of a tenant changed who may
do what in a tenant for a year without leaving a row anybody could read (MT-014). A hand list
of methods cannot notice the sibling it does not name, so this guard enumerates the class **by
what a function does**.

**Predicate** - a function (method or module function) under ``app/domain/services/`` is a
member when its own body

* calls ``create`` / ``delete`` / ``update_fields`` / ``delete_while_tenant_frozen`` on a
  receiver whose dotted name contains ``membership`` (``self._membership_repo.create(...)``,
  ``memberships.delete(...)``), or
* calls ``self._create_membership_unless_erasing(...)`` (the insert helper two doors share), or
* calls ``<anything>.create_with_lead_membership(...)`` (founding a tenant with its founder, #2118).

Every member must call ``self._audit_membership(...)`` (the one write path into the
:class:`~app.domain.services.security_audit_service.SecurityAuditService`), or - when it founds a tenant,
whose row is written inside the founding transaction - build the row with ``<audit>.membership_entry(...)``;
otherwise it must be classified in
:data:`_CLASSIFIED` with the reason it needs none. A classification that no longer names a live
member fails, so the list cannot go stale and excuse the next copy.

**Spellings this predicate cannot see:** a membership written through a repository held under a
name without ``membership`` in it, a raw AQL ``INSERT``/``REMOVE`` on the collection, a
``getattr``-built call, a migration or seed (outside ``app/domain/services/``), the account
and tenant *erasure* executors under ``app/data_access/`` that remove memberships as the
subject's data (the erasure record, not this audit, proves them), and a router writing through
the repository directly (held by the no-``data_access``-import rule for routers).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
SERVICES = APP / "domain" / "services"

_MUTATORS = {"create", "delete", "update_fields", "delete_while_tenant_frozen"}
_HELPER = "_create_membership_unless_erasing"
_FOUNDING = "create_with_lead_membership"
_GATE = "_audit_membership"
#: A founding writes its row inside the transaction that creates the tenant: the row is *built* here.
_FOUNDING_GATE = "membership_entry"

_CLASSIFIED: dict[tuple[str, str], str] = {
    ("tenant_service.py", "TenantService._create_membership_unless_erasing"): (
        "the insert helper: it writes no row itself because its callers (admin_add_membership, "
        "accept_invitation) record the join after it returned - a join the erasure freeze took back "
        "raises before any row is written, so no membership that never stood is recorded"
    ),
    ("tenant_service.py", "TenantService._settle_join_against_freeze"): (
        "the take-back of a join the erasure froze meanwhile (REQ-025 AK-IE-07): it removes the "
        "membership _create_membership_unless_erasing just inserted and raises, so the caller records "
        "nothing - the membership never stood"
    ),
    ("tenant_service.py", "TenantService._settle_join_against_member_limit"): (
        "the take-back of a join a concurrent join pushed over the member limit (#2133): it removes the "
        "membership _create_membership_unless_erasing just inserted and raises, so the caller records "
        "nothing - the membership never stood"
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


def _dotted(node: ast.AST) -> str:
    """The dotted spelling of a receiver: ``self._membership_repo`` -> ``self._membership_repo``."""
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _why_member(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """What makes *function* a membership mutation; empty when it is none."""
    reasons: list[str] = []
    for node in _own_nodes(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        receiver = _dotted(node.func.value)
        if node.func.attr in _MUTATORS and "membership" in receiver.lower():
            reasons.append(f"{receiver}.{node.func.attr}(...)")
        elif node.func.attr == _HELPER and receiver == "self":
            reasons.append(f"self.{_HELPER}(...)")
        elif node.func.attr == _FOUNDING:
            reasons.append(f"{receiver}.{_FOUNDING}(...)")
    return reasons


def _calls_the_gate(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and (
            (isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr == _GATE)
            or node.func.attr == _FOUNDING_GATE
        )
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


#: The class size measured when this guard was written (#2111). A change in either direction is a
#: signal to read, not to update blindly: a new member needs the gate or a classification, a
#: vanished one may mean the predicate went blind.
#: +2 with #2137: create_service_account (joins) and remove_service_account (removes).
EXPECTED_MEMBERS = 15  # +1 with #2134: _hand_management_to (the account erasure's INV-1 handover); +1 with #2133


def test_every_membership_mutation_writes_the_audit_or_is_classified() -> None:
    unaudited = sorted(
        f"{rel}::{name} ({', '.join(why)})"
        for (rel, name), (why, gated) in members().items()
        if not gated and (rel, name) not in _CLASSIFIED
    )

    assert unaudited == [], (
        f"A service function that mutates a membership must call self.{_GATE} (#2111) "
        "or be classified with a reason:\n  " + "\n  ".join(unaudited)
    )


def test_the_predicate_sees_the_class() -> None:
    """A predicate that found nothing would be green over nothing."""
    found = members()
    print(f"membership-mutation members: {len(found)}")  # noqa: T201 - the measured count, read by the reviewer
    for (rel, name), (why, gated) in sorted(found.items()):
        print(f"  {rel}::{name} audited={gated} {why}")  # noqa: T201

    assert len(found) == EXPECTED_MEMBERS, sorted(found)
    for known in (
        ("tenant_service.py", "TenantService._found_tenant"),
        ("tenant_service.py", "TenantService.admin_add_membership"),
        ("tenant_service.py", "TenantService.admin_change_membership_role"),
        ("tenant_service.py", "TenantService.admin_remove_membership"),
        ("tenant_service.py", "TenantService.change_member_role"),
        ("tenant_service.py", "TenantService.change_member_scopes"),
        ("tenant_service.py", "TenantService.remove_member"),
        ("tenant_service.py", "TenantService.leave_tenant"),
        ("tenant_service.py", "TenantService.accept_invitation"),
        ("tenant_service.py", "TenantService.create_service_account"),
        ("tenant_service.py", "TenantService.remove_service_account"),
    ):
        assert known in found, f"the predicate lost {known}"


def test_no_classification_is_stale() -> None:
    found = members()
    stale = sorted(f"{rel}::{name}" for rel, name in _CLASSIFIED if (rel, name) not in found)

    assert stale == []


def test_a_classified_entry_is_not_also_audited() -> None:
    """A classified member that calls the gate needs no excuse - the entry would outlive its reason."""
    found = members()
    both = sorted(f"{rel}::{name}" for rel, name in _CLASSIFIED if (rel, name) in found and found[(rel, name)][1])

    assert both == []


def test_the_gate_writes_through_the_audit_service() -> None:
    """A gate that stopped writing would leave every caller 'audited' over nothing."""
    tree = ast.parse((SERVICES / "tenant_service.py").read_text(encoding="utf-8"))
    (gate,) = [fn for name, fn in _functions(tree) if name == f"TenantService.{_GATE}"]
    calls = {
        node.func.attr
        for node in _own_nodes(gate)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "record_membership_change" in calls


def test_the_running_application_wires_the_audit() -> None:
    """The service takes the audit as optional; the wiring is where it must not be left out."""
    source = (APP / "common" / "dependencies.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_tenant_service"]
    (call,) = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "TenantService"
    ]

    assert any(kw.arg == "security_audit" for kw in call.keywords)


# ── #2114: a membership that ends takes the task assignments with it ──────────

_ENDS = {"delete", "delete_while_tenant_frozen"}
_CLEAR = "_end_task_assignments"

_ENDING_CLASSIFIED: dict[tuple[str, str], str] = {
    ("tenant_service.py", "TenantService._settle_join_against_freeze"): (
        "the take-back of a join the erasure froze meanwhile: the membership never stood, so the account was "
        "never assigned a task of this tenant through it"
    ),
    ("tenant_service.py", "TenantService._settle_join_against_member_limit"): (
        "the take-back of a join a concurrent join pushed over the member limit (#2133): the membership never "
        "stood, so the account was never assigned a task of this tenant through it"
    ),
}


def _calls_self(function: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == name
        for node in _own_nodes(function)
    )


def _ends_a_membership(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ENDS
        and "membership" in _dotted(node.func.value).lower()
        for node in _own_nodes(function)
    )


def membership_endings(root: Path = SERVICES) -> dict[tuple[str, str], bool]:
    """Every service function that deletes a membership: (file, qualname) -> calls ``self._end_task_assignments``."""
    found: dict[tuple[str, str], bool] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for qualname, function in _functions(ast.parse(path.read_text(encoding="utf-8"))):
            if _ends_a_membership(function):
                found[(rel, qualname)] = _calls_self(function, _CLEAR)
    return found


def test_every_membership_ending_clears_the_task_assignments_or_is_classified() -> None:
    uncleared = sorted(
        f"{rel}::{name}"
        for (rel, name), clears in membership_endings().items()
        if not clears and (rel, name) not in _ENDING_CLASSIFIED
    )

    assert uncleared == [], (
        f"A service function that deletes a membership must call self.{_CLEAR} (#2114) or be classified:\n  "
        + "\n  ".join(uncleared)
    )


def test_the_ending_predicate_sees_the_class() -> None:
    found = membership_endings()
    print(f"membership endings: {sorted(found)}")  # noqa: T201 - the measured set, read by the reviewer

    assert set(found) == {
        ("tenant_service.py", "TenantService.admin_remove_membership"),
        ("tenant_service.py", "TenantService.remove_member"),
        ("tenant_service.py", "TenantService.leave_tenant"),
        ("tenant_service.py", "TenantService.remove_service_account"),
        ("tenant_service.py", "TenantService._settle_join_against_freeze"),
        ("tenant_service.py", "TenantService._settle_join_against_member_limit"),
    }
    assert [name for (_, name), clears in found.items() if clears] != []


def test_no_ending_classification_is_stale_or_redundant() -> None:
    found = membership_endings()

    assert sorted(k for k in _ENDING_CLASSIFIED if k not in found) == []
    assert sorted(k for k in _ENDING_CLASSIFIED if found.get(k)) == []


def test_the_running_application_wires_the_task_store() -> None:
    tree = ast.parse((APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_tenant_service"]
    (call,) = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "TenantService"
    ]

    assert any(kw.arg == "task_repo" for kw in call.keywords)


def test_the_clear_helper_asks_the_task_store() -> None:
    """A helper that stopped calling the store would leave every ending 'clearing' over nothing."""
    tree = ast.parse((SERVICES / "tenant_service.py").read_text(encoding="utf-8"))
    (helper,) = [fn for name, fn in _functions(tree) if name == f"TenantService.{_CLEAR}"]
    calls = {
        node.func.attr
        for node in _own_nodes(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "clear_assignee" in calls


def test_the_ending_predicate_recognises_each_spelling() -> None:
    def ends(source: str) -> bool:
        (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
        return _ends_a_membership(function)

    assert ends("def f(self):\n    self._membership_repo.delete(k)")
    assert ends("def f(self):\n    self._membership_repo.delete_while_tenant_frozen(k, t)")
    assert ends("def f(memberships):\n    memberships.delete(k)")
    assert not ends("def f(self):\n    self._membership_repo.get_by_key(k)")
    assert not ends("def f(self):\n    self._invitation_repo.delete(k)")


# ── self-tests: the predicate recognises every spelling it claims ──────────────


def _why(source: str) -> list[str]:
    (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
    return _why_member(function)


def test_the_predicate_recognises_each_spelling() -> None:
    assert _why("def f(self):\n    self._membership_repo.create(m)")
    assert _why("def f(self):\n    self._membership_repo.delete(k)")
    assert _why("def f(self):\n    self._membership_repo.update_fields(k, {})")
    assert _why("def f(self):\n    self._membership_repo.delete_while_tenant_frozen(k, t)")
    assert _why("def f(memberships):\n    memberships.delete(k)")
    assert _why("def f(self):\n    self._create_membership_unless_erasing(m)")


def test_the_predicate_ignores_reads_and_other_repositories() -> None:
    assert not _why("def f(self):\n    return self._membership_repo.get_by_key(k)")
    assert not _why("def f(self):\n    self._invitation_repo.create(i)")
    assert not _why("def f(self):\n    self._tenant_repo.delete(k)")
    assert not _why("def f(other):\n    other._create_membership_unless_erasing(m)")


def test_the_founding_spelling_is_a_member_and_its_gate_is_the_row_builder() -> None:
    assert _why("def f(self):\n    self._tenant_repo.create_with_lead_membership(t, m)")

    def gated(source: str) -> bool:
        (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
        return _calls_the_gate(function)

    assert gated("def f(audit):\n    audit.membership_entry(action=a)")
    assert not gated("def f(audit):\n    audit.announce(e)")


def test_the_gate_detection_sees_only_a_call_on_self() -> None:
    def gated(source: str) -> bool:
        (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
        return _calls_the_gate(function)

    assert gated(f"def f(self):\n    self.{_GATE}(a=1)")
    assert not gated(f"def f(self):\n    other.{_GATE}(a=1)")
    assert not gated(f"def f(self):\n    return self.{_GATE}")


# ── #2133: every join passes the member limit ─────────────────────────────────
#
# The member limit (REQ-024 AK-64) is decided in one place, the insert helper every join into an
# existing tenant goes through. The class is the membership *creations* among the members above: a
# raw ``create`` on a membership receiver, a call of the helper, a founding. The rule: a raw insert
# happens only inside the helper, and the helper asks the limit before the insert and settles the
# join against it afterwards. A founding is classified - the founder takes the first seat of a
# tenant that did not exist a moment ago, and every limit is at least 1.

_LIMIT_GATE = "_refuse_beyond_member_limit"
_LIMIT_SETTLE = "_settle_join_against_member_limit"

_CREATION_CLASSIFIED: dict[tuple[str, str], str] = {
    ("tenant_service.py", "TenantService._found_tenant"): (
        "founds a tenant with its founder in one transaction (#2118): the founder takes the first seat of a "
        "tenant nobody else can be in yet, and every member limit is at least 1 (Tenant.max_members ge=1, "
        "TENANT_MAX_MEMBERS_CEILING ge=1)"
    ),
}


def _creates_raw(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create"
        and "membership" in _dotted(node.func.value).lower()
        for node in _own_nodes(function)
    )


def membership_creations(root: Path = SERVICES) -> dict[tuple[str, str], str]:
    """Every service function that creates a membership: (file, qualname) -> ``raw``, ``helper`` or ``founding``."""
    found: dict[tuple[str, str], str] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for qualname, function in _functions(ast.parse(path.read_text(encoding="utf-8"))):
            if _creates_raw(function):
                found[(rel, qualname)] = "raw"
            elif _calls_self(function, _HELPER):
                found[(rel, qualname)] = "helper"
            elif any(
                isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == _FOUNDING
                for node in _own_nodes(function)
            ):
                found[(rel, qualname)] = "founding"
    return found


def test_a_raw_membership_insert_happens_only_inside_the_limited_helper() -> None:
    stray = sorted(
        f"{rel}::{name} ({kind})"
        for (rel, name), kind in membership_creations().items()
        if kind != "helper" and name != f"TenantService.{_HELPER}" and (rel, name) not in _CREATION_CLASSIFIED
    )

    assert stray == [], (
        f"A membership is created outside TenantService.{_HELPER}, which decides the member limit (#2133):\n  "
        + "\n  ".join(stray)
    )


def test_the_helper_asks_the_member_limit_before_and_after_the_insert() -> None:
    tree = ast.parse((SERVICES / "tenant_service.py").read_text(encoding="utf-8"))
    (helper,) = [fn for name, fn in _functions(tree) if name == f"TenantService.{_HELPER}"]

    assert _calls_self(helper, _LIMIT_GATE)
    assert _calls_self(helper, _LIMIT_SETTLE)


def test_the_limit_gate_counts_the_active_members_and_refuses_with_its_own_error() -> None:
    """A gate that stopped counting would leave every join 'limited' over nothing."""
    tree = ast.parse((SERVICES / "tenant_service.py").read_text(encoding="utf-8"))
    for name in (_LIMIT_GATE, _LIMIT_SETTLE):
        (gate,) = [fn for qualname, fn in _functions(tree) if qualname == f"TenantService.{name}"]
        attrs = {
            node.func.attr
            for node in _own_nodes(gate)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        names = {
            node.func.id for node in _own_nodes(gate) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        assert "count_active_members" in attrs, name
        assert "MemberLimitReachedError" in names, name


def test_the_creation_predicate_sees_the_class() -> None:
    found = membership_creations()
    print(f"membership creations: {sorted(found.items())}")  # noqa: T201 - the measured set, read by the reviewer

    assert found == {
        ("tenant_service.py", "TenantService._found_tenant"): "founding",
        ("tenant_service.py", f"TenantService.{_HELPER}"): "raw",
        ("tenant_service.py", "TenantService.admin_add_membership"): "helper",
        ("tenant_service.py", "TenantService.accept_invitation"): "helper",
        # #2137 - a service account takes a seat: it joins through the limited door like everybody else.
        ("tenant_service.py", "TenantService.create_service_account"): "helper",
    }


def test_no_creation_classification_is_stale() -> None:
    found = membership_creations()

    assert sorted(k for k in _CREATION_CLASSIFIED if k not in found) == []


def test_the_running_application_wires_the_member_limit_ceiling() -> None:
    """The service takes the ceiling with a default; the wiring is where the setting must reach it."""
    tree = ast.parse((APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_tenant_service"]
    (call,) = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "TenantService"
    ]
    (ceiling,) = [kw for kw in call.keywords if kw.arg == "max_members_ceiling"]

    assert _dotted(ceiling.value) == "settings.tenant_max_members_ceiling"


def test_the_creation_predicate_recognises_each_spelling() -> None:
    def kind(source: str) -> dict[tuple[str, str], str]:
        tree = ast.parse(source)
        out: dict[tuple[str, str], str] = {}
        for qualname, function in _functions(tree):
            if _creates_raw(function):
                out[("x.py", qualname)] = "raw"
            elif _calls_self(function, _HELPER):
                out[("x.py", qualname)] = "helper"
        return out

    assert kind("def f(self):\n    self._membership_repo.create(m)") == {("x.py", "f"): "raw"}
    assert kind("def f(memberships):\n    memberships.create(m)") == {("x.py", "f"): "raw"}
    assert kind(f"def f(self):\n    self.{_HELPER}(m)") == {("x.py", "f"): "helper"}
    assert kind("def f(self):\n    self._invitation_repo.create(i)") == {}
    assert kind("def f(self):\n    self._membership_repo.get_by_key(k)") == {}


def test_the_running_application_wires_the_service_account_stores() -> None:
    """#2137 - the service takes the key store and the quota with defaults; the wiring must hand both over."""
    tree = ast.parse((APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_tenant_service"]
    (call,) = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "TenantService"
    ]
    keywords = {kw.arg: kw.value for kw in call.keywords}

    assert _dotted(keywords["max_service_accounts"]) == "settings.tenant_max_service_accounts"
    assert isinstance(keywords["api_key_repo"], ast.Call)
    assert _dotted(keywords["api_key_repo"].func) == "get_api_key_repo"
