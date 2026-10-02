"""No log call hands a raw tenant key to the logger next to a subject reference (#1928).

The #1788 review (GDPR-05) removed the tenant key from
``tenant_erasure.personal_tenant_retained``: the tenant key sits on the
pseudonymised retention rows (erasure records, the CanG/PflSchG harvest and
treatment rows), and for a personal tenant it identifies its owner. A log line
that carries it beside ``subject=<salted pseudonym>`` joins the pseudonym to the
tenant and the tenant's rows to the subject — the join the salted
``log_subject`` exists to prevent. #1928 found the same pair on the invitation
and tenant-erasure lines of ``tenant_service``; those carry
``tenant=log_tenant(...)`` now (``ErasureEngine.log_tenant``, keyed with
``LOG_PSEUDONYM_SALT``).

**The rule** (one detector, :func:`findings_in_source`, shared by the tree scan
and the self-test): a log call that passes a tenant keyword —
``tenant``, ``tenant_key``, ``*_tenant_key``, ``tenant_slug`` — whose value is
not a call or a literal, **and** a subject keyword — ``subject``, ``*_subject``,
``user_key`` — or any keyword whose value is a ``log_subject(...)`` call.

**What the scan found when it was added** (develop, 2026-10-02): 17 sites. The 4
in ``tenant_service`` that #1928 names and the 2 account-erasure storage lines in
``privacy_service`` were fixed; the 11 in other services are allow-listed below
and tracked in a follow-up issue — operational lines outside #1928's invitation /
erasure scope.

**Spellings this guard cannot see**: a tenant key inside an f-string under a
neutral keyword (``prefix=f"t/{tenant_key}/"`` — the storage-key class is
``test_privacy_logs_carry_no_plaintext_subject``'s), a tenant key and a subject
on two *consecutive* log calls, a ``**fields`` splat or ``extra={...}``, a
logger reached under another name, and a tenant key under a keyword that is not
named like a tenant (``owner=``, ``scope=``). The 81 log calls that pass a raw
tenant key *without* a subject are out of this rule.
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

_TENANT_KEYWORD = re.compile(r"^(tenant|tenant_key|\w+_tenant_key|tenant_slug)$")
_SUBJECT_KEYWORD = re.compile(r"^(subject|\w+_subject|user_key)$")

_FOLLOW_UP = "operational line outside #1928's invitation / erasure scope; tracked in #1989"

#: ``path::enclosing_function::event`` -> reason. Keyed by the log event name, so an
#: edit above an entry neither orphans it nor moves the excuse onto another line.
_ALLOWED: dict[str, str] = {
    f"app/domain/{module}::{function}::{event}": _FOLLOW_UP
    for module, function, event in (
        ("engines/notification_engine.py", "NotificationEngine.notify", "?"),
        ("services/attachment_service.py", "AttachmentService.upload", "attachment_uploaded"),
        ("services/attachment_service.py", "AttachmentService._link_to_stored_object", "attachment_uploaded"),
        (
            "services/identification_service.py",
            "IdentificationService.assess_quality",
            "photo_quality_assessment_requested",
        ),
        ("services/pest_image_service.py", "PestImageService.contribute", "pest_image_contributed"),
        ("services/pest_image_service.py", "PestImageService.delete", "pest_image_deleted"),
        ("services/pest_image_service.py", "PestImageService.set_promotion", "pest_image_promotion_changed"),
        ("services/pest_image_service.py", "PestImageService.set_active", "pest_image_active_changed"),
        ("services/plant_diary_service.py", "PlantDiaryService.request_analysis", "diary_analysis_requested"),
        (
            "services/plant_diary_service.py",
            "PlantDiaryService.cancel_analysis_request",
            "diary_analysis_request_cancelled",
        ),
        (
            "services/reference_image_service.py",
            "ReferenceImageService.contribute_user_reference",
            "reference_user_contribution_quarantined",
        ),
    )
}


def _is_raw(value: ast.expr) -> bool:
    return not isinstance(value, ast.Call | ast.Constant)


def _event_name(node: ast.Call) -> str:
    first = node.args[0] if node.args else None
    return first.value if isinstance(first, ast.Constant) and isinstance(first.value, str) else "?"


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.scope: list[str] = []
        self.findings: list[str] = []
        self.sites: list[str] = []

    def _enter(self, node: ast.AST, name: str) -> None:
        self.scope.append(name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter(node, node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter(node, node.name)

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:
        if _is_log_call(node):
            keywords = [kw for kw in node.keywords if kw.arg]
            raw_tenant = [kw.arg for kw in keywords if _TENANT_KEYWORD.match(kw.arg or "") and _is_raw(kw.value)]
            names_subject = any(
                _SUBJECT_KEYWORD.match(kw.arg or "")
                or (isinstance(kw.value, ast.Call) and _call_name(kw.value.func) == "log_subject")
                for kw in keywords
            )
            self.sites.append(self.rel)
            if raw_tenant and names_subject:
                key = f"{self.rel}::{'.'.join(self.scope) or '<module>'}::{_event_name(node)}"
                self.findings.append(f"{key} ({', '.join(str(k) for k in raw_tenant)}=)")
        self.generic_visit(node)


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    return func.attr if isinstance(func, ast.Attribute) else ""


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
        # the pseudonymised tenant, a literal, or no subject: not this rule
        ('logger.info("e", subject=log_subject(u), tenant=log_tenant(tenant.key))', False),
        ('logger.info("e", tenant_key="demo", subject=s)', False),
        ('logger.info("e", tenant_key=tenant_key, removed=3)', False),
        ('logger.info("e", subject=s, record_key=k)', False),
        # not a log call
        ('audit.record("e", subject=s, tenant_key=k)', False),
        ('send("e", subject=s, tenant_key=k)', False),
    ],
)
def test_detector_sees_each_spelling(source: str, caught: bool) -> None:
    assert bool(findings_in_source(source, "app/x.py")) is caught


def test_the_tenant_service_lines_named_in_1928_pass() -> None:
    path = BACKEND_ROOT / "app/domain/services/tenant_service.py"
    assert findings_in_source(path.read_text(encoding="utf-8"), _rel(path)) == []
