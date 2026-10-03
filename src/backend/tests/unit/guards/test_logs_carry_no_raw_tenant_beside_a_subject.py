"""No log call hands a raw tenant key to the logger next to a subject reference (#1928, #1989).

The #1788 review (GDPR-05) removed the tenant key from
``tenant_erasure.personal_tenant_retained``: the tenant key sits on the
pseudonymised retention rows (erasure records, the CanG/PflSchG harvest and
treatment rows), and for a personal tenant it identifies its owner. A log line
that carries it beside ``subject=<salted pseudonym>`` joins the pseudonym to the
tenant and the tenant's rows to the subject — the join the salted
``log_subject`` exists to prevent. Such a line carries ``tenant=log_tenant(...)``
instead (``ErasureEngine.log_tenant``, keyed with ``LOG_PSEUDONYM_SALT``).

**The rule** (one detector, :func:`findings_in_source`, shared by the tree scan
and the self-test): a log call that names a raw tenant **and** a subject.

* *A raw tenant* is a keyword named like a tenant — ``tenant``, ``tenant_key``,
  ``*_tenant_key``, ``tenant_slug``, ``tenant_keys`` — whose value is neither a
  literal nor a :data:`_TENANT_PSEUDONYMS` call, **or** a tenant-named name or
  attribute (``tenant_key``, ``ctx.tenant_key``, ``tenant.key``) anywhere in a
  positional argument (the ``%s`` spelling), an f-string message, a keyword of
  any other name (``owner=``, ``extra={...}``, ``**{"tenant": ...}``). A call
  ends that search: ``len(tenant_keys)`` is a count, ``log_tenant(k)`` the
  pseudonym.
* *A subject* is a keyword ``subject``, ``*_subject``, ``user_key`` or an actor
  keyword ``*ed_by`` (``contributed_by=``, ``requested_by=``), a
  ``log_subject(...)`` call anywhere in the call, or a local the enclosing
  function assigned from ``log_subject(...)``.
* *Bound loggers*: ``log = logger.bind(...)`` in a function carries what it
  binds into every ``log.<method>(...)`` of that function, so a subject bound
  once and a raw tenant passed later (or the reverse) is one line.

**History.** Added with #1928 (17 sites on develop, 6 fixed there, 11
allow-listed for #1989). #1989 fixed the 11 and, from a wider measurement than
this rule had, two spellings the first detector missed: the four
``NotificationEngine.notify`` lines that inherit the bound
``subject``/``tenant_key`` pair (only the ``bind`` itself was a finding), and
``NoopReferenceIndexStore.add_user_contribution``, whose ``contributed_by=``
was the contributor's *plaintext* account key beside ``tenant_key=``. The
allow-list is empty.

**Spellings this guard still cannot see**: a ``**fields`` splat of a dict built
elsewhere, a tenant key under a name that is not tenant-like (``key=``,
``owner_key=``) or held in a local not named like a tenant, a subject handed in
through a parameter not named like one, a logger reached under a name without
``log``, and two log lines that share an entity key (``attachment_id``) — one
with the subject, the other with the raw tenant. The ~80 log calls that pass a
raw tenant key *without* a subject are out of this rule.
"""

from __future__ import annotations

import ast
import re

import pytest

from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import (
    BACKEND_ROOT,
    _guarded_modules,
    _is_log_call,
    _rel,
)

#: A keyword, name or attribute that holds a tenant key or the tenant itself.
_TENANT_NAME = re.compile(r"^(tenant|tenant_key|\w+_tenant_key|tenant_slug|tenant_keys)$")
_TENANT_KEYWORD = _TENANT_NAME
_SUBJECT_KEYWORD = re.compile(r"^(subject|\w+_subject|user_key|\w+ed_by)$")
#: The calls that turn a tenant key into what a log line may carry beside a subject.
_TENANT_PSEUDONYMS = {"log_tenant", "log_tenant_record_key"}

#: ``path::enclosing_function::event`` -> reason. Keyed by the log event name, so an
#: edit above an entry neither orphans it nor moves the excuse onto another line.
#: Empty since #1989: every site the rule finds logs the pseudonym.
_ALLOWED: dict[str, str] = {}


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    return func.attr if isinstance(func, ast.Attribute) else ""


def _raw_tenant_value(value: ast.expr) -> bool:
    """A tenant-named keyword's value is raw unless it is a literal or the pseudonym."""
    if isinstance(value, ast.Constant):
        return False
    return not (isinstance(value, ast.Call) and _call_name(value.func) in _TENANT_PSEUDONYMS)


def _tenant_references(node: ast.AST) -> list[str]:
    """Tenant-named names/attributes inside *node*, not looking into calls."""
    if isinstance(node, ast.Call):
        return []
    if isinstance(node, ast.Name):
        return [node.id] if _TENANT_NAME.match(node.id) else []
    if isinstance(node, ast.Attribute):
        if _TENANT_NAME.match(node.attr):
            return [ast.unparse(node)]
        return _tenant_references(node.value)
    return [hit for child in ast.iter_child_nodes(node) for hit in _tenant_references(child)]


def _names_log_subject(node: ast.AST, subject_locals: set[str]) -> bool:
    return any(
        (isinstance(n, ast.Call) and _call_name(n.func) == "log_subject")
        or (isinstance(n, ast.Name) and n.id in subject_locals)
        for n in ast.walk(node)
    )


def _inspect(node: ast.Call, subject_locals: set[str]) -> tuple[list[str], bool]:
    """``(raw tenant spellings, names a subject)`` of one log call."""
    raw: list[str] = []
    names_subject = False
    for kw in node.keywords:
        if kw.arg and _TENANT_KEYWORD.match(kw.arg):
            if _raw_tenant_value(kw.value):
                raw.append(f"{kw.arg}=")
        else:
            raw.extend(f"{kw.arg or '**'}={hit}" for hit in _tenant_references(kw.value))
        if kw.arg and _SUBJECT_KEYWORD.match(kw.arg):
            names_subject = True
    for arg in node.args:
        raw.extend(f"arg:{hit}" for hit in _tenant_references(arg))
    return raw, names_subject or _names_log_subject(node, subject_locals)


def _event_name(node: ast.Call) -> str:
    first = node.args[0] if node.args else None
    return first.value if isinstance(first, ast.Constant) and isinstance(first.value, str) else "?"


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.scope: list[str] = []
        self.findings: list[str] = []
        self.sites: list[str] = []
        #: Per function: locals assigned from ``log_subject(...)``, and bound
        #: loggers -> (raw tenant spellings, names a subject) of their ``bind``.
        self.subject_locals: list[set[str]] = [set()]
        self.bound: list[dict[str, tuple[list[str], bool]]] = [{}]

    def _enter(self, node: ast.AST, name: str) -> None:
        self.scope.append(name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter(node, node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.subject_locals.append(set())
        self.bound.append({})
        self._enter(node, node.name)
        self.subject_locals.pop()
        self.bound.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_Assign(self, node: ast.Assign) -> None:
        # Visit the value first: a ``bind`` call is itself a log call.
        self.generic_visit(node)
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return
        target, value = node.targets[0].id, node.value
        if isinstance(value, ast.Call) and _call_name(value.func) == "log_subject":
            self.subject_locals[-1].add(target)
        elif isinstance(value, ast.Call) and _call_name(value.func) == "bind" and _is_log_call(value):
            self.bound[-1][target] = _inspect(value, self.subject_locals[-1])

    def visit_Call(self, node: ast.Call) -> None:
        if _is_log_call(node):
            raw, names_subject = _inspect(node, self.subject_locals[-1])
            receiver = node.func.value if isinstance(node.func, ast.Attribute) else None
            if isinstance(receiver, ast.Name) and receiver.id in self.bound[-1]:
                bound_raw, bound_subject = self.bound[-1][receiver.id]
                raw = raw + [f"bound {spelling}" for spelling in bound_raw]
                names_subject = names_subject or bound_subject
            self.sites.append(self.rel)
            if raw and names_subject:
                key = f"{self.rel}::{'.'.join(self.scope) or '<module>'}::{_event_name(node)}"
                self.findings.append(f"{key} ({', '.join(raw)})")
        self.generic_visit(node)


def findings_in_source(source: str, rel: str) -> list[str]:
    """THE detector: log calls in *source* (a module at *rel*) with a raw tenant beside a subject."""
    visitor = _Visitor(rel)
    visitor.visit(ast.parse(source))
    return visitor.findings


def _scan() -> tuple[list[str], int]:
    findings: list[str] = []
    sites = 0
    for path in _guarded_modules():
        visitor = _Visitor(_rel(path))
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        findings.extend(visitor.findings)
        sites += len(visitor.sites)
    return findings, sites


def test_the_scan_sees_log_calls() -> None:
    _findings, sites = _scan()
    assert sites > 500, f"only {sites} log calls seen"


def test_no_log_call_carries_a_raw_tenant_key_beside_a_subject() -> None:
    findings, _sites = _scan()
    unexplained = [f for f in findings if f.split(" (")[0] not in _ALLOWED]
    assert not unexplained, (
        "a log call hands a raw tenant key to the logger next to a subject reference; log "
        "tenant=log_tenant(<key>) (app.common.log_privacy) or drop it where a count suffices:\n  "
        + "\n  ".join(unexplained)
    )


def test_allowlist_entries_still_exist() -> None:
    findings, _sites = _scan()
    live = {f.split(" (")[0] for f in findings}
    assert [entry for entry in _ALLOWED if entry not in live] == []


@pytest.mark.parametrize(
    ("source", "caught"),
    [
        ('logger.info("e", subject=log_subject(u), tenant_key=tenant.key)', True),
        ('logger.info("e", tenant_key=key, subject=requested_by)', True),
        ('logger.info("e", tenant=tenant_key, admin_subject=who)', True),
        ('logger.info("e", tenant_slug=slug, user_key=u)', True),
        ('logger.info("e", owner_tenant_key=k, who=log_subject(u))', True),
        ('logger.info("e", tenant=tenant_key or other, subject=s)', True),
        ('logger.info("e", tenant_key=getattr(row, "tenant_key"), subject=s)', True),
        ('logger.info("e", tenant_keys=keys, subject=s)', True),
        # #1989: spellings the first detector missed
        ('logger.info("e %s", tenant_key, subject=s)', True),
        ('logger.info(f"e {ctx.tenant_key}", subject=s)', True),
        ('logger.info("e", extra={"tenant_key": tenant_key}, subject=s)', True),
        ('logger.info("e", **{"tenant": tenant_key}, subject=s)', True),
        ('logger.info("e", owner=updated.tenant_key, admin_subject=s)', True),
        ('logger.info("e", scope=tenant.key, subject=s)', True),
        ('logger.info("e", tenant_key=k, contributed_by=contributed_by)', True),
        ('logger.info("e", tenant_key=k, requested_by=log_subject(u))', True),
        ('def f():\n    ref = log_subject(u)\n    logger.info("e", actor=ref, tenant_key=k)', True),
        ('def f():\n    log = logger.bind(subject=log_subject(u))\n    log.info("e", tenant_key=k)', True),
        ('def f():\n    log = logger.bind(tenant_key=k)\n    log.info("e", subject=s)', True),
        # the pseudonymised tenant, a literal, a count, or no subject: not this rule
        ('logger.info("e", subject=log_subject(u), tenant=log_tenant(tenant.key))', False),
        ('logger.info("e", subject=s, record_key=log_tenant_record_key(r.key))', False),
        ('logger.info("e", tenant_key="demo", subject=s)', False),
        ('logger.info("e", tenant_key=tenant_key, removed=3)', False),
        ('logger.info("e", subject=s, record_key=k)', False),
        ('logger.info("e", tenants=len(tenant_keys), subject=s)', False),
        ('logger.info("e", tenant_key=k, sort_by=field)', False),
        ('def f():\n    log = logger.bind(subject=s, tenant=log_tenant(k))\n    log.info("e", removed=1)', False),
        ('def f():\n    log = logger.bind(subject=s)\n\ndef g():\n    log.info("e", tenant_key=k)', False),
        # not a log call
        ('audit.record("e", subject=s, tenant_key=k)', False),
        ('send("e", subject=s, tenant_key=k)', False),
    ],
)
def test_detector_sees_each_spelling(source: str, caught: bool) -> None:
    assert bool(findings_in_source(source, "app/x.py")) is caught


@pytest.mark.parametrize(
    "rel",
    [
        "app/domain/services/tenant_service.py",
        "app/domain/engines/notification_engine.py",
        "app/data_access/vectordb/noop_reference_index_store.py",
    ],
)
def test_the_lines_named_in_1928_and_1989_pass(rel: str) -> None:
    path = BACKEND_ROOT / rel
    assert findings_in_source(path.read_text(encoding="utf-8"), _rel(path)) == []
