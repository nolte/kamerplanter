"""Every way into a tenant asks the erasure freeze, and every invitation asks the owner (#1924).

Two decisions keep a personal tenant from being joined once its owner asked to
be erased (REQ-025 AK-IE-06, AK-IE-07):

* a **membership** inserted into an *existing* tenant is checked against the
  tenant-erasure record once it exists and taken back atomically against the
  record's withdrawal — ``TenantService._create_membership_unless_erasing``;
* an **invitation** is neither created nor accepted while the tenant's owner has
  an open erasure request — ``TenantService._refuse_invitation_while_owner_erasing``.

Both were fixed for the call sites that existed; the class is "a path that joins
an account to a tenant, or hands out the means to". It is derived here, not
listed: every call that inserts a membership or an invitation, found in the
syntax tree of ``app/``, must either be the gate itself, join a tenant the same
function has just created (nobody can be erasing it), or sit in a function that
also calls the gate.

The self-test at the bottom is the non-vacuity proof: the same predicate must
flag a source that inserts a membership or an invitation without the gate, and
the derived populations must contain the call sites known today — a rename that
made the sweep see nothing would fail there rather than pass.
"""

from __future__ import annotations

import ast
import pathlib
import textwrap

APP_ROOT = pathlib.Path(__file__).resolve().parents[3] / "app"

#: One-off data migrations seed the platform's first accounts; no erasure can be
#: open against a tenant they are creating.
_EXCLUDED = ("migrations",)

_MEMBERSHIP_GATE = "_create_membership_unless_erasing"
_INVITATION_GATE = "_refuse_invitation_while_owner_erasing"
_INVITATION_WRITES = frozenset({"create", "mark_accepted_if_pending"})
_FOUNDING = "create_with_lead_membership"


def _receiver_name(call: ast.Call) -> str | None:
    """The last name of the object a method is called on: ``self._membership_repo.create`` -> ``_membership_repo``."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    value = func.value
    if isinstance(value, ast.Attribute):
        return value.attr
    if isinstance(value, ast.Name):
        return value.id
    return None


def _calls(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _method_calls(node: ast.AST, receiver_suffix: str, methods: frozenset[str] | set[str]) -> list[ast.Call]:
    return [
        c
        for c in _calls(node)
        if isinstance(c.func, ast.Attribute)
        and c.func.attr in methods
        and (_receiver_name(c) or "").endswith(receiver_suffix)
    ]


def _calls_named(node: ast.AST, name: str) -> bool:
    return any(isinstance(c.func, ast.Attribute) and c.func.attr == name for c in _calls(node))


def _functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]


def _membership_findings(tree: ast.Module, label: str) -> tuple[list[str], int]:
    """``(violations, sites)`` — membership inserts that skip the freeze check."""
    problems: list[str] = []
    sites = 0
    for function in _functions(tree):
        # #2118 - a tenant is founded with its founder's membership in one transaction
        # (``create_with_lead_membership``): a membership of a tenant that did not exist a moment ago, which
        # nobody can be erasing. Counted as a site, never a violation.
        sites += len(_method_calls(function, "tenant_repo", {_FOUNDING}))
        inserts = _method_calls(function, "membership_repo", {"create"})
        if not inserts:
            continue
        sites += len(inserts)
        if function.name == _MEMBERSHIP_GATE:
            continue
        if _method_calls(function, "tenant_repo", {"create"}):
            continue  # joins the tenant it has just created
        problems.extend(f"{label}:{call.lineno} ({function.name})" for call in inserts)
    return problems, sites


def _invitation_findings(tree: ast.Module, label: str) -> tuple[list[str], int]:
    """``(violations, sites)`` — invitation creates/accepts that skip the owner check."""
    problems: list[str] = []
    sites = 0
    for function in _functions(tree):
        writes = _method_calls(function, "invitation_repo", _INVITATION_WRITES)
        if not writes:
            continue
        sites += len(writes)
        if _calls_named(function, _INVITATION_GATE):
            continue
        problems.extend(f"{label}:{call.lineno} ({function.name})" for call in writes)
    return problems, sites


def _app_trees() -> list[tuple[str, ast.Module]]:
    trees = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        relative = path.relative_to(APP_ROOT)
        if relative.parts[0] in _EXCLUDED:
            continue
        trees.append((str(relative), ast.parse(path.read_text(encoding="utf-8"))))
    return trees


def test_every_membership_insert_into_an_existing_tenant_goes_through_the_freeze_check():
    problems: list[str] = []
    sites = 0
    for label, tree in _app_trees():
        found, count = _membership_findings(tree, label)
        problems.extend(found)
        sites += count
    assert not problems, (
        "a membership is inserted without TenantService._create_membership_unless_erasing — "
        "it can land in a tenant whose erasure is frozen (REQ-025 AK-IE-07):\n" + "\n".join(problems)
    )
    assert sites >= 2, f"the sweep saw {sites} membership inserts; the gate and the tenant founding exist today"


def test_every_invitation_write_asks_whether_the_owner_asked_for_erasure():
    problems: list[str] = []
    sites = 0
    for label, tree in _app_trees():
        found, count = _invitation_findings(tree, label)
        problems.extend(found)
        sites += count
    assert not problems, (
        "an invitation is created or accepted without TenantService._refuse_invitation_while_owner_erasing — "
        "somebody can join a personal tenant during its owner's erasure grace (REQ-025 AK-IE-06):\n"
        + "\n".join(problems)
    )
    assert sites >= 3, f"the sweep saw {sites} invitation writes; two creators and the acceptance exist today"


# ── non-vacuity ─────────────────────────────────────────────────────


def _parse(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


def test_the_membership_sweep_flags_an_insert_that_skips_the_gate():
    bad = _parse(
        """
        class S:
            def add(self, m):
                return self._membership_repo.create(m)
        """
    )
    problems, sites = _membership_findings(bad, "bad.py")
    assert sites == 1
    assert problems == ["bad.py:4 (add)"]


def test_the_membership_sweep_spares_the_gate_and_a_join_of_a_tenant_just_created():
    good = _parse(
        """
        class S:
            def _create_membership_unless_erasing(self, m):
                return self._membership_repo.create(m)

            def create_tenant(self, t, m):
                self._tenant_repo.create(t)
                self._membership_repo.create(m)
        """
    )
    assert _membership_findings(good, "good.py") == ([], 2)


def test_the_membership_sweep_counts_a_founding_and_does_not_flag_it():
    founding = _parse(
        """
        class S:
            def found(self, t, m):
                return self._tenant_repo.create_with_lead_membership(t, m)
        """
    )
    assert _membership_findings(founding, "founding.py") == ([], 1)


def test_the_invitation_sweep_flags_a_create_and_an_accept_that_skip_the_owner_check():
    bad = _parse(
        """
        class S:
            def invite(self, i):
                return self._invitation_repo.create(i)

            def accept(self, k):
                return self._invitation_repo.mark_accepted_if_pending(k, {})
        """
    )
    problems, sites = _invitation_findings(bad, "bad.py")
    assert sites == 2
    assert len(problems) == 2


def test_the_invitation_sweep_accepts_a_function_that_asks_first():
    good = _parse(
        """
        class S:
            def invite(self, t, i):
                self._refuse_invitation_while_owner_erasing(tenant_key=t)
                return self._invitation_repo.create(i)
        """
    )
    assert _invitation_findings(good, "good.py") == ([], 1)


def test_the_receiver_match_sees_a_bare_name_and_an_attribute_alike():
    tree = _parse(
        """
        def f(membership_repo, self):
            membership_repo.create(1)
            self._membership_repo.create(2)
            self.something_else.create(3)
        """
    )
    found = _method_calls(tree, "membership_repo", {"create"})
    assert [c.lineno for c in found] == [3, 4]
