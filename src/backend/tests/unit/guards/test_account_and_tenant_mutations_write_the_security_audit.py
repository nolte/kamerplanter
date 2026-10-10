"""#2111 - every service function that changes an account's trust flags or a tenant's lifecycle writes the
security audit, or is classified.

The defect class (MT-014): a persistent audit applied opt-in at the call site. The membership class was
closed by #2149 (``test_membership_mutations_write_the_security_audit.py``); a platform admin who
deactivated an account, revoked its address verification, suspended a tenant or accepted / withdrew a
tenant's deletion still left no row anybody could read. A hand list of methods cannot notice the sibling
it does not name, so this guard enumerates the class **by what a function does**. It is a separate guard
rather than an extension of the membership one because the predicate is a different one (which
*attributes* of which *documents* are written) and because the membership guard's measured class size
must keep meaning what it measured.

**Predicate** - a function (method or module function) under ``app/domain/services/`` is a member when
its own body

* calls ``update_fields`` on an **account receiver** (dotted name ending in ``user_repo`` or the name
  ``users``) with a payload that names ``is_active``, ``email_verified`` or ``account_type`` - or a
  payload the AST cannot read (a variable, a ``**`` spread): an opaque payload counts, it is the caller
  that has to show it carries no trust field;
* calls ``update_fields`` on a **tenant receiver** (ending in ``tenant_repo`` or the name ``tenants``)
  with a payload naming ``is_active``, ``status``, ``deletion_scheduled_at``, ``is_platform``,
  ``owner_user_key`` or ``tenant_type`` - or an opaque payload;
* calls ``delete`` on an account or a tenant receiver; or
* calls ``self.<helper>(...)`` where ``<helper>`` is a member of the same class classified as a
  **helper** (:data:`_HELPERS`): a helper writes no row itself, so whoever calls it is in the class.

Every member must call ``self._audit_account(...)``, ``self._audit_tenant(...)`` or
``self._audit_membership(...)`` (the three write paths into the
:class:`~app.domain.services.security_audit_service.SecurityAuditService`), or be classified in
:data:`_HELPERS` / :data:`_EXEMPT` with the reason it needs none. A classification that no longer names a
live member fails, so the lists cannot go stale and excuse the next copy.

**Spellings this predicate cannot see:** a write through a repository held under another name, a raw AQL
``UPDATE`` on ``users`` / ``tenants``, a ``getattr``-built call, a migration or seed (outside
``app/domain/services/``), the erasure executors under ``app/data_access/`` (the erasure records, not this
audit, prove them), and a router writing through the repository directly (held by the
no-``data_access``-import rule for routers).
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.unit.guards.test_membership_mutations_write_the_security_audit import _dotted, _functions, _own_nodes

APP = Path(__file__).resolve().parents[3] / "app"
SERVICES = APP / "domain" / "services"

_USER_FIELDS = frozenset({"is_active", "email_verified", "account_type"})
_TENANT_FIELDS = frozenset(
    {"is_active", "status", "deletion_scheduled_at", "is_platform", "owner_user_key", "tenant_type"}
)
_GATES = frozenset({"_audit_account", "_audit_tenant", "_audit_membership"})

#: Members that write no row themselves **because their callers do**; a caller of one is a member too.
_HELPERS: dict[tuple[str, str], str] = {
    ("tenant_service.py", "TenantService._apply_tenant_update"): (
        "the store both tenant update paths share: admin_update_tenant records the suspension or reactivation "
        "after it returned, update_tenant refuses every lifecycle field before it is reached"
    ),
    ("tenant_service.py", "TenantService._set_tenant_status"): (
        "the lifecycle write the deletion and cancellation paths share; the person-initiated ones record "
        "their row after it returned"
    ),
    ("tenant_service.py", "TenantService._schedule_tenant_erasure"): (
        "freezes a tenant for its deletion grace; delete_tenant records the accepted deletion after it returned"
    ),
    ("tenant_service.py", "TenantService._mark_tenant_erasing"): (
        "moves a tenant whose grace is over into 'deleted'; delete_tenant records the accepted deletion"
    ),
}

#: Members that need no row, with the reason.
_EXEMPT: dict[tuple[str, str], str] = {
    ("user_service.py", "UserService.update_profile"): (
        "the account's own profile edit: the opaque payload is built from three named fields (display_name, "
        "avatar_url, locale) - no trust field can reach it"
    ),
    ("tenant_service.py", "TenantService.update_tenant"): (
        "the tenant's own edit (name, description, member limit): every lifecycle field raises before the "
        "store, so no account gains or loses access through it"
    ),
    ("auth_service.py", "AuthService.verify_email"): (
        "the account's own address confirmation by the mailed link - not an act on another account; "
        "email_confirmed_at is its proof"
    ),
    ("auth_service.py", "AuthService._take_back_registration"): (
        "removes the account a failed registration just created: it never stood"
    ),
    ("privacy_service.py", "PrivacyService.request_erasure"): (
        "the subject's own erasure request closes the account; the erasure request (NFR-011 R-06) is its proof"
    ),
    ("privacy_service.py", "PrivacyService._open_immediate_erasure"): (
        "an admin's or the cleanup's account erasure closes the account; the erasure request with its origin, "
        "step-up and salted requested_by_subject (NFR-011 R-06, kept three years, never withdrawn) is its proof"
    ),
    ("tenant_service.py", "TenantService.run_tenant_erasure_task"): (
        "the worker running a deletion whose acceptance delete_tenant recorded; nobody acts here"
    ),
    ("tenant_service.py", "TenantService.resume_tenant_erasures"): (
        "the daily beat running a deletion whose acceptance was recorded (delete_tenant) or that an account "
        "erasure decided (the erasure request is the proof); nobody acts here"
    ),
    ("tenant_service.py", "TenantService._erase_tenant_for_account_erasure"): (
        "a personal tenant going with its erased owner: the account erasure decided it, its erasure request "
        "and the tenant-erasure record (origin account_erasure) are the proof"
    ),
    ("tenant_service.py", "TenantService._orphan_organisation"): (
        "an organisation left without management by an account erasure (#2134): the account erasure decided "
        "it, the tenant-erasure record (origin orphaned_organisation) is the proof"
    ),
}


def _payload(call: ast.Call) -> ast.AST | None:
    if len(call.args) >= 2:
        return call.args[1]
    for kw in call.keywords:
        if kw.arg in {"fields", "data", "updates"}:
            return kw.value
    return None


def _names_a_field(payload: ast.AST | None, fields: frozenset[str]) -> bool:
    """Whether *payload* names one of *fields*; an opaque payload (not a plain dict literal) counts."""
    if not isinstance(payload, ast.Dict) or any(key is None for key in payload.keys):
        return True
    return any(isinstance(key, ast.Constant) and key.value in fields for key in payload.keys)


def _is_account(receiver: str) -> bool:
    return receiver.endswith("user_repo") or receiver == "users"


def _is_tenant(receiver: str) -> bool:
    return receiver.endswith("tenant_repo") or receiver == "tenants"


def _direct_reasons(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    reasons: list[str] = []
    for node in _own_nodes(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        receiver, attr = _dotted(node.func.value), node.func.attr
        if attr == "update_fields" and _is_account(receiver) and _names_a_field(_payload(node), _USER_FIELDS):
            reasons.append(f"{receiver}.update_fields(account trust)")
        elif attr == "update_fields" and _is_tenant(receiver) and _names_a_field(_payload(node), _TENANT_FIELDS):
            reasons.append(f"{receiver}.update_fields(tenant lifecycle)")
        elif attr == "delete" and (_is_account(receiver) or _is_tenant(receiver)):
            reasons.append(f"{receiver}.delete(...)")
    return reasons


def _self_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {
        node.func.attr
        for node in _own_nodes(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    }


def _calls_a_gate(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return bool(_self_calls(function) & _GATES)


def members(
    root: Path = SERVICES, helpers: dict[tuple[str, str], str] | None = None
) -> dict[tuple[str, str], tuple[list[str], bool]]:
    """Every member of the class: (file, qualname) -> (why, calls a gate); helper callers included."""
    helpers = _HELPERS if helpers is None else helpers
    found: dict[tuple[str, str], tuple[list[str], bool]] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        functions = _functions(ast.parse(path.read_text(encoding="utf-8")))
        for qualname, function in functions:
            if why := _direct_reasons(function):
                found[(rel, qualname)] = (why, _calls_a_gate(function))
        # A caller of a classified helper is a member; repeat until nothing new joins.
        grew = True
        while grew:
            grew = False
            helper_names = {
                name.rsplit(".", 1)[-1]: name.rsplit(".", 1)[0]
                for (file, name) in found
                if file == rel and (file, name) in helpers
            }
            for qualname, function in functions:
                if (rel, qualname) in found:
                    continue
                owner = qualname.rsplit(".", 1)[0] if "." in qualname else None
                via = sorted(
                    f"self.{helper}(...)"
                    for helper, cls in helper_names.items()
                    if cls == owner and helper in _self_calls(function)
                )
                if via:
                    found[(rel, qualname)] = (via, _calls_a_gate(function))
                    grew = True
    return found


#: The class size measured when this guard was written (#2111). A change in either direction is a signal to
#: read, not to update blindly: a new member needs a gate or a classification, a vanished one may mean the
#: predicate went blind.
#: 20 at #2111: 6 audited (admin_update_user, admin_update_tenant, delete_tenant, cancel_tenant_erasure, and
#: create_service_account / remove_service_account through the membership audit), 4 helpers, 10 exempt.
EXPECTED_MEMBERS = 20


def test_every_trust_or_lifecycle_mutation_writes_the_audit_or_is_classified() -> None:
    classified = _HELPERS.keys() | _EXEMPT.keys()
    unaudited = sorted(
        f"{rel}::{name} ({', '.join(why)})"
        for (rel, name), (why, gated) in members().items()
        if not gated and (rel, name) not in classified
    )

    assert unaudited == [], (
        "A service function that changes an account's trust flags or a tenant's lifecycle must call "
        "self._audit_account / self._audit_tenant (#2111) or be classified with a reason:\n  " + "\n  ".join(unaudited)
    )


def test_the_predicate_sees_the_class() -> None:
    """A predicate that found nothing would be green over nothing."""
    found = members()
    print(f"account/tenant trust-mutation members: {len(found)}")  # noqa: T201 - the measured count
    for (rel, name), (why, gated) in sorted(found.items()):
        print(f"  {rel}::{name} audited={gated} {why}")  # noqa: T201

    assert len(found) == EXPECTED_MEMBERS, sorted(found)
    for known in (
        ("user_service.py", "UserService.admin_update_user"),
        ("tenant_service.py", "TenantService.admin_update_tenant"),
        ("tenant_service.py", "TenantService.delete_tenant"),
        ("tenant_service.py", "TenantService.cancel_tenant_erasure"),
        ("privacy_service.py", "PrivacyService._open_immediate_erasure"),
    ):
        assert known in found, f"the predicate lost {known}"
    for audited in (
        ("user_service.py", "UserService.admin_update_user"),
        ("tenant_service.py", "TenantService.admin_update_tenant"),
        ("tenant_service.py", "TenantService.delete_tenant"),
        ("tenant_service.py", "TenantService.cancel_tenant_erasure"),
    ):
        assert found[audited][1], f"{audited} no longer writes the audit"


def test_no_classification_is_stale() -> None:
    found = members()
    stale = sorted(f"{rel}::{name}" for rel, name in _HELPERS.keys() | _EXEMPT.keys() if (rel, name) not in found)

    assert stale == []


def test_a_classified_entry_is_not_also_audited() -> None:
    """A classified member that calls a gate needs no excuse - the entry would outlive its reason."""
    found = members()
    both = sorted(f"{rel}::{name}" for rel, name in _HELPERS.keys() | _EXEMPT.keys() if found[(rel, name)][1])

    assert both == []
    assert not (_HELPERS.keys() & _EXEMPT.keys())


def test_the_gates_write_through_the_audit_service() -> None:
    """A gate that stopped writing would leave every caller 'audited' over nothing."""
    for file, gate, write in (
        ("user_service.py", "UserService._audit_account", "record_account_change"),
        ("tenant_service.py", "TenantService._audit_tenant", "record_tenant_change"),
        ("tenant_service.py", "TenantService._audit_membership", "record_membership_change"),
    ):
        tree = ast.parse((SERVICES / file).read_text(encoding="utf-8"))
        (function,) = [fn for name, fn in _functions(tree) if name == gate]
        calls = {
            node.func.attr
            for node in _own_nodes(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }

        assert write in calls, gate


def test_the_running_application_wires_the_audit_into_both_services() -> None:
    """Both services take the audit as optional; the wiring is where it must not be left out."""
    tree = ast.parse((APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    for factory_name, cls in (("get_user_service", "UserService"), ("get_tenant_service", "TenantService")):
        (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == factory_name]
        (call,) = [
            n
            for n in ast.walk(factory)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == cls
        ]

        assert any(kw.arg == "security_audit" for kw in call.keywords), factory_name


# ── self-tests: the predicate recognises every spelling it claims ──────────────


def _members_of(source: str, helpers: dict[tuple[str, str], str] | None = None, *, tmp: Path) -> dict:
    (tmp / "x.py").write_text(source, encoding="utf-8")
    return {name: gated for (_, name), (_, gated) in members(tmp, helpers or {}).items()}


def test_a_synthetic_unaudited_deactivation_is_flagged(tmp_path: Path) -> None:
    found = _members_of(
        "class S:\n"
        "    def deactivate(self, k):\n"
        "        self._user_repo.update_fields(k, {'is_active': False})\n"
        "    def suspend(self, k):\n"
        "        self._tenant_repo.update_fields(k, {'status': 'suspended'})\n"
        "    def audited(self, k):\n"
        "        self._user_repo.update_fields(k, {'email_verified': True})\n"
        "        self._audit_account(k)\n",
        tmp=tmp_path,
    )

    assert found == {"S.deactivate": False, "S.suspend": False, "S.audited": True}


def test_the_predicate_reads_the_payload(tmp_path: Path) -> None:
    found = _members_of(
        "class S:\n"
        "    def stamp(self, k):\n"
        "        self._user_repo.update_fields(k, {'last_login_at': 1})\n"
        "    def opaque(self, k, data):\n"
        "        self._user_repo.update_fields(k, data)\n"
        "    def spread(self, k, data):\n"
        "        self._user_repo.update_fields(k, {**data})\n"
        "    def erasure(self, k):\n"
        "        self._tenant_erasure_repo.update_fields(k, {'status': 'x'})\n"
        "    def remove(self, k):\n"
        "        self._tenant_repo.delete(k)\n"
        "    def read(self, k):\n"
        "        return self._user_repo.get_by_key(k)\n",
        tmp=tmp_path,
    )

    assert set(found) == {"S.opaque", "S.spread", "S.remove"}


def test_a_caller_of_a_helper_joins_the_class_and_only_through_the_same_class(tmp_path: Path) -> None:
    source = (
        "class S:\n"
        "    def _write(self, k):\n"
        "        self._tenant_repo.update_fields(k, {'is_active': False})\n"
        "    def door(self, k):\n"
        "        self._write(k)\n"
        "    def outer(self, k):\n"
        "        self.door(k)\n"
        "class T:\n"
        "    def door(self, k):\n"
        "        self._write(k)\n"
    )

    assert set(_members_of(source, tmp=tmp_path)) == {"S._write"}
    assert set(_members_of(source, {("x.py", "S._write"): "helper"}, tmp=tmp_path)) == {"S._write", "S.door"}
