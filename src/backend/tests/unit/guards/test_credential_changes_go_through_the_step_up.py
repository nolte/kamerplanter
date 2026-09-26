"""#1841 / #1815 — every credential or identity change in a service is step-up gated or classified.

The defect class: a guard applied opt-in at the call site. #1846 unified the step-up
for the routes it knew and listed them by hand (``_STEP_UP_ENTRIES`` in
``test_password_checks_go_through_the_step_up_verifier.py``); the e-mail change was
not on the list, so a hijacked session — or an API key — moved the account onto an
attacker's address without re-authenticating (#1841). A hand list cannot notice
the sibling it does not name. This guard enumerates the class **by what a member
does**, not by its name.

**Predicate** — a function (method or module function) under ``app/domain/services/``
is a member when its own body

* writes the key ``"email"`` or ``"password_hash"`` — as a dict-literal key (the
  ``update_fields(key, {"email": ...})`` / ``model_copy(update={...})`` spelling),
  as an attribute assignment (``user.password_hash = ...``), or as a keyword of an
  account construction (``User(email=..., password_hash=...)``);
* opens an e-mail change — constructs an ``EmailChangeRequest`` (the confirmation
  later writes the address; the *request* is where the step-up belongs, #1841);
* creates or deletes a sign-in method or a machine credential:
  ``self._auth_provider_repo.create/delete``, ``self._api_key_repo.create``;
* issues a device-pairing code — a bearer credential for a new session:
  ``.issue(...)`` on ``self._device_pairing_code_store`` or on a local bound from
  ``self._require_device_pairing_store()``.

Every member must either call ``self._step_up_verifier.verify(...)`` itself (or a same-class helper that does), or be
classified in :data:`_CLASSIFIED` with the reason it needs no step-up of its own,
or be in :data:`_PENDING` — known gaps, each with its follow-up issue (empty since #1847/#1857).
A classification or pending entry that no longer names a live member fails, so
neither list can go stale and excuse the next copy.

**Spellings this predicate cannot see** (so nobody reads green as more than it is):
a write through a key held in a variable (``{field: value}``), ``setattr``, a dict
built by ``dict(email=...)`` outside a model construction, a ``**fields`` splat, a
write in a repository method called under a neutral name, and anything outside
``app/domain/services/`` (routers are held by the no-``data_access``-import rule).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
SERVICES = APP / "domain" / "services"

#: Review SEC-004 (a): the reset and verification tokens, the verified flag and a
#: pending new address are identity state as much as the address and hash are.
_CREDENTIAL_KEYS = {
    "email",
    "password_hash",
    "password_reset_token",
    "email_verification_token",
    "email_verified",
    "new_email",
}
#: The persisted account model: a keyword of its construction is a write.
#: (A projection such as ``UserProfile(email=...)`` or an ``Invitation`` addressed
#: to someone else is not the account's identity.)
_ACCOUNT_MODELS = {"User"}
#: Constructing one of these opens an identity change.
_IDENTITY_CHANGE_MODELS = {"EmailChangeRequest"}
_CREDENTIAL_REPO_CALLS = {
    ("_auth_provider_repo", "create"),
    ("_auth_provider_repo", "delete"),
    ("_auth_provider_repo", "update"),
    ("_api_key_repo", "create"),
}

#: Members that need no step-up of their own, with the reason read from the code.
_CLASSIFIED: dict[tuple[str, str], str] = {
    ("auth_service.py", "AuthService.register_local"): (
        "account creation: the password is chosen by the person creating the account; there is no session to hijack"
    ),
    ("auth_service.py", "AuthService.reset_password"): (
        "proof of the mailbox: the reset token was mailed to the account's address (possession of the inbox is "
        "the re-authentication), and the method revokes every session"
    ),
    ("auth_service.py", "AuthService._register_oauth_user"): (
        "account creation on the federated sign-in path: the provider authenticated the person"
    ),
    ("auth_service.py", "AuthService._create_oauth_provider"): (
        "sign-in path: links the provider identity the OAuth callback just authenticated; reached only from "
        "_complete_login (the sign-in half of the provider callback), never from a signed-in session"
    ),
    ("privacy_service.py", "PrivacyService.confirm_email_change"): (
        "gated upstream: the token exists only for a request that passed the step-up in request_email_change, "
        "and possession of the new mailbox is proven by the token"
    ),
    ("privacy_service.py", "PrivacyService._suppress_taken_email_change"): (
        "reached only from request_email_change, after its step-up; the EmailChangeRequest it builds is a decoy "
        "that is never persisted"
    ),
    ("notification_service.py", "NotificationService.send_email_digest"): (
        "reads, not writes: {'email': to_email} is the delivery config handed to the e-mail channel for one send"
    ),
    ("auth_service.py", "AuthService._complete_login"): (
        "sign-in path: stamps last_used_at on the provider link the OAuth callback just authenticated"
    ),
    ("auth_service.py", "AuthService.request_password_reset"): (
        "unauthenticated mail path: the token goes only to the account's own address and grants nothing without "
        "that mailbox; refused silently for service accounts"
    ),
    ("auth_service.py", "AuthService.verify_email"): (
        "proof of the mailbox: the verification token was mailed to the address it verifies"
    ),
    ("privacy_service.py", "PrivacyService._take_back_credentials_since"): (
        "reached only from revert_email_change, after its single-use mailbox proof; it removes sign-in links "
        "created during a takeover (security review of #1848, SEC-002) — a removal on the owner's behalf"
    ),
    ("privacy_service.py", "PrivacyService.revert_email_change"): (
        "proof of the previous mailbox (#1848): the single-use revert token was mailed to the address it restores "
        "— the same proof a password reset relies on; bounded window, and it signs out every session"
    ),
    ("user_service.py", "UserService.update_profile"): (
        "the field set is built in the same function from a closed tuple (display_name, avatar_url, locale) — "
        "no credential key can reach update_fields"
    ),
    ("privacy_service.py", "PrivacyService.erase_account_now"): (
        "reached only behind a step-up'd entry (erase_account_by_admin) or the unverified-account cleanup "
        "(no interactive caller); pinned by test_the_immediate_admin_erasure_starts_only_behind_the_step_up"
    ),
}

#: Known members without a step-up yet -> the follow-up issue tracking each. Emptied
#: by #1847 (API keys, device pairing, provider unlink) and #1857 (admin update).
_PENDING_ISSUES: dict[tuple[str, str], str] = {}
_PENDING: set[tuple[str, str]] = set(_PENDING_ISSUES)


def _receiver_attr(node: ast.expr) -> str | None:
    """``_x`` for ``self._x`` — the service collaborator a call goes to."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return None


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


def _pairing_store_locals(nodes: list[ast.AST]) -> set[str]:
    """Locals bound from ``self._require_device_pairing_store()``."""
    names: set[str] = set()
    for node in nodes:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "_require_device_pairing_store"
        ):
            names.add(node.targets[0].id)
    return names


def _why_member(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """What makes *function* a credential/identity change; empty when it is none."""
    nodes = _own_nodes(function)
    pairing_stores = _pairing_store_locals(nodes)
    reasons: list[str] = []
    for node in nodes:
        if isinstance(node, ast.Dict):
            reasons += [
                f"writes key {k.value!r}"
                for k in node.keys
                if isinstance(k, ast.Constant) and k.value in _CREDENTIAL_KEYS
            ]
        elif isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            reasons += [
                f"assigns .{t.attr}" for t in targets if isinstance(t, ast.Attribute) and t.attr in _CREDENTIAL_KEYS
            ]
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name in _ACCOUNT_MODELS:
                reasons += [f"constructs {name}({kw.arg}=...)" for kw in node.keywords if kw.arg in _CREDENTIAL_KEYS]
            if name in _IDENTITY_CHANGE_MODELS:
                reasons.append(f"opens an identity change ({name})")
            if isinstance(func, ast.Attribute):
                receiver = _receiver_attr(func.value)
                if (receiver, func.attr) in _CREDENTIAL_REPO_CALLS:
                    reasons.append(f"calls self.{receiver}.{func.attr}")
                if receiver == "_user_repo" and func.attr == "update_fields":
                    # Review SEC-004 (c): a field set the source does not spell out
                    # can carry any credential key; a literal dict is read above.
                    fields = (
                        node.args[1]
                        if len(node.args) > 1
                        else next((kw.value for kw in node.keywords if kw.arg == "fields"), None)
                    )
                    if fields is not None and not isinstance(fields, ast.Dict):
                        reasons.append("writes user fields from a non-literal dict")
                if receiver == "_user_repo" and func.attr in {"update", "replace"}:
                    reasons.append(f"replaces the user document (self._user_repo.{func.attr})")
                if func.attr == "issue" and (
                    receiver == "_device_pairing_code_store"
                    or (isinstance(func.value, ast.Name) and func.value.id in pairing_stores)
                ):
                    reasons.append("issues a device-pairing code")
    return reasons


def _calls_the_verifier(
    function: ast.FunctionDef | ast.AsyncFunctionDef, gating_helpers: frozenset[str] = frozenset()
) -> bool:
    """Whether *function* calls ``self._step_up_verifier.verify`` — or one of its class's *gating_helpers*.

    A gating helper is a method of the same class that calls the verifier itself
    (``AuthService._verify_credential_step_up``, #1847): one level, by name, so a
    helper that stops calling the verifier un-gates every caller with it.
    """
    for node in _own_nodes(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        # Only ``verify`` confirms; ``issue_code`` / ``admit_reauth`` /
        # ``issue_reauth_token`` hand a factor out (security review of #1847, SEC-002).
        if _receiver_attr(node.func.value) == "_step_up_verifier" and node.func.attr == "verify":
            return True
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr in gating_helpers:
            return True
    return False


def _gating_helpers(functions: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]) -> dict[str, frozenset[str]]:
    """Per class: the methods that call the verifier directly."""
    helpers: dict[str, set[str]] = {}
    for qualname, function in functions:
        if "." in qualname and _calls_the_verifier(function):
            cls, name = qualname.split(".", 1)
            helpers.setdefault(cls, set()).add(name)
    return {cls: frozenset(names) for cls, names in helpers.items()}


def _functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """(qualified name, node) of every module function and method."""
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
    """Every member of the class: (file, qualname) -> (why, calls the verifier).

    *root* lets the measurement run over another tree (the services of a base
    commit, checked out elsewhere) — the reported before/after counts.
    """
    found: dict[tuple[str, str], tuple[list[str], bool]] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        functions = _functions(ast.parse(path.read_text(encoding="utf-8")))
        helpers = _gating_helpers(functions)
        for qualname, function in functions:
            if why := _why_member(function):
                own_class = qualname.split(".", 1)[0] if "." in qualname else ""
                found[(rel, qualname)] = (why, _calls_the_verifier(function, helpers.get(own_class, frozenset())))
    return found


#: The class size measured when this guard was written (#1841). A change in either
#: direction is a signal to read, not to update blindly: a new member needs a
#: step-up or a classification, a vanished one may mean the predicate went blind.
EXPECTED_MEMBERS = 21


def test_every_credential_change_is_step_up_gated_or_classified() -> None:
    found = members()
    ungated = sorted(
        f"{rel}::{name} ({', '.join(why)})"
        for (rel, name), (why, gated) in found.items()
        if not gated and (rel, name) not in _CLASSIFIED and (rel, name) not in _PENDING
    )

    assert ungated == [], (
        "A service function that writes an e-mail or password hash, or creates/deletes a sign-in method or "
        "credential, must call self._step_up_verifier.verify (#1841) or be classified with a reason:\n  "
        + "\n  ".join(ungated)
    )


def test_the_predicate_sees_the_class() -> None:
    """A predicate that found nothing would be green over nothing."""
    found = members()
    print(f"credential-change members: {len(found)}")  # noqa: T201 - the measured count, read by the reviewer
    for (rel, name), (why, gated) in sorted(found.items()):
        print(f"  {rel}::{name} gated={gated} {why}")  # noqa: T201

    assert len(found) == EXPECTED_MEMBERS, sorted(found)
    for known in (
        ("privacy_service.py", "PrivacyService.request_erasure"),
        ("auth_service.py", "AuthService.change_password"),
        ("privacy_service.py", "PrivacyService.confirm_email_change"),
        ("privacy_service.py", "PrivacyService.request_email_change"),
    ):
        assert known in found, f"the predicate lost {known}"


def test_the_gated_entries_are_gated() -> None:
    found = members()
    for entry in (
        ("privacy_service.py", "PrivacyService.request_erasure"),
        ("privacy_service.py", "PrivacyService.request_email_change"),
        ("auth_service.py", "AuthService.change_password"),
        ("auth_service.py", "AuthService.create_api_key"),
        ("auth_service.py", "AuthService.create_device_pairing"),
        ("auth_service.py", "AuthService.unlink_provider"),
        ("user_service.py", "UserService.admin_update_user"),
    ):
        assert entry in found and found[entry][1], f"{entry} is not behind self._step_up_verifier"


def test_no_classification_is_stale() -> None:
    """An entry that names no member any more is an excuse waiting for the next copy."""
    found = members()
    stale = sorted(f"{rel}::{name}" for rel, name in set(_CLASSIFIED) | _PENDING if (rel, name) not in found)

    assert stale == []


def test_a_pending_entry_that_got_its_step_up_leaves_the_list() -> None:
    found = members()
    done = sorted(
        f"{rel}::{name} ({_PENDING_ISSUES[(rel, name)]})"
        for rel, name in _PENDING
        if (rel, name) in found and found[(rel, name)][1]
    )

    assert done == [], f"now gated, remove from _PENDING_ISSUES: {done}"


def test_a_classified_entry_is_not_also_gated() -> None:
    """A classified member that calls the verifier needs no excuse — the entry would outlive its reason."""
    found = members()
    both = sorted(f"{rel}::{name}" for rel, name in _CLASSIFIED if (rel, name) in found and found[(rel, name)][1])

    assert both == []


# ── self-tests: the predicate recognises every spelling it claims ──────────────


def _why(source: str) -> list[str]:
    (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
    return _why_member(function)


def test_the_predicate_recognises_each_spelling() -> None:
    assert _why("def f(self):\n    self._user_repo.update_fields(k, {'email': e})")
    assert _why("def f(self):\n    u = u.model_copy(update={'password_hash': h})")
    assert _why("def f(self, user):\n    user.password_hash = h")
    assert _why("def f(self):\n    User(email=e, display_name=n)")
    assert _why("def f(self):\n    EmailChangeRequest(user_key=k, new_email=e)")
    assert _why("def f(self):\n    self._auth_provider_repo.create(p)")
    assert _why("def f(self):\n    self._auth_provider_repo.delete(k)")
    assert _why("def f(self):\n    self._api_key_repo.create(k)")
    assert _why("def f(self):\n    store = self._require_device_pairing_store()\n    store.issue(c, u)")
    assert _why("def f(self):\n    self._device_pairing_code_store.issue(c, u)")


def test_the_predicate_ignores_reads_and_other_keys() -> None:
    assert not _why("def f(self):\n    return self._user_repo.get_by_email(e)")
    assert not _why("def f(self):\n    self._user_repo.update_fields(k, {'display_name': n})")
    assert not _why("def f(self):\n    send(to_email=e)")
    assert not _why("def f(self):\n    return UserProfile(email=u.email)")
    assert not _why("def f(self):\n    self._api_key_repo.delete(k)")
    assert not _why("def f(self):\n    store = self._require_device_pairing_store()\n    store.consume(c)")


# ── review SEC-004 (d): the second class — irreversible actions ─────────────────
#
# The credential predicate above catches a write of identity state. An erasure is
# reached through a handful of core methods instead; a new route calling one of them
# directly would skip the step-up without writing a single credential key. So every
# *caller* of an irreversible core, anywhere under ``app/``, must

# * call ``self._step_up_verifier`` itself, or
# * reach it through a method of its own class that does (resolved transitively
#   inside the class: ``delete_tenant`` -> ``_verify_tenant_deletion_step_up``), or
# * be classified in :data:`_IRREVERSIBLE_CALLERS` with the reason it needs none.

#: The methods that erase for good. ``erase_account`` / ``run_tenant_erasure`` are
#: the executing cores; the others claim, record and hand over to them.
_IRREVERSIBLE = {
    "erase_account_now",
    "erase_account",
    "_finalize_erasure",
    "_run_tenant_erasure",
    "run_tenant_erasure",
    "_erase_tenant_for_account_erasure",
    "erase_personal_tenant_of",
}

_IRREVERSIBLE_CALLERS: dict[tuple[str, str], str] = {
    ("domain/services/privacy_service.py", "PrivacyService.erase_account_now"): (
        "the shared immediate-erasure entry: reached from erase_account_by_admin (step-up) and the unverified-"
        "account cleanup task; test_the_immediate_admin_erasure_starts_only_behind_the_step_up pins the admin origin"
    ),
    ("domain/services/privacy_service.py", "PrivacyService._finalize_erasure"): (
        "runs a request that already exists — created behind the step-up (request_erasure / erase_account_by_admin) "
        "or by the unverified cleanup"
    ),
    ("domain/services/privacy_service.py", "PrivacyService.execute_scheduled_erasures"): (
        "daily beat: hard-deletes requests whose Art. 17 grace ran out; each was opened behind the step-up"
    ),
    ("domain/services/privacy_service.py", "PrivacyService._erase_personal_tenants"): (
        "the personal-tenant step of the executing core erase_account, which only _finalize_erasure reaches"
    ),
    ("domain/services/tenant_service.py", "TenantService.resume_tenant_erasures"): (
        "daily beat: retries deletions whose record was created behind the step-up in delete_tenant"
    ),
    ("domain/services/tenant_service.py", "TenantService.erase_personal_tenant_of"): (
        "part of an account erasure (#1788): the account erasure that decided it carried its own step-up or is the "
        "unverified cleanup"
    ),
    ("domain/services/tenant_service.py", "TenantService._erase_tenant_for_account_erasure"): (
        "the tenant half of an account erasure, reached only from erase_personal_tenant_of"
    ),
    ("domain/services/tenant_service.py", "TenantService._run_tenant_erasure"): (
        "the runner of a claimed record; its callers (delete_tenant, resume_tenant_erasures, "
        "_erase_tenant_for_account_erasure) are checked here themselves"
    ),
    ("tasks/auth_tasks.py", "cleanup_unverified_accounts"): (
        "Celery: erases registrations never verified past their deadline — no person, no session"
    ),
}


def _qualified_functions(tree: ast.Module) -> dict[str, tuple[str | None, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """qualname -> (enclosing class, node) for every function, nested ones under their outer name."""
    found: dict[str, tuple[str | None, ast.FunctionDef | ast.AsyncFunctionDef]] = {}

    def walk(body: list[ast.stmt], prefix: str, cls: str | None) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                walk(node.body, f"{prefix}{node.name}.", node.name)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                found[f"{prefix}{node.name}"] = (cls, node)
                walk(node.body, f"{prefix}{node.name}.", cls)

    walk(tree.body, "", None)
    return found


def _called_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in _own_nodes(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute | ast.Name)
    }


def _self_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {
        node.func.attr
        for node in _own_nodes(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    }


def irreversible_callers(root: Path = APP) -> dict[tuple[str, str], tuple[set[str], bool]]:
    """Every caller of an irreversible core: (file, qualname) -> (cores it calls, reaches the verifier)."""
    found: dict[tuple[str, str], tuple[set[str], bool]] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        functions = _qualified_functions(ast.parse(path.read_text(encoding="utf-8")))
        # Gated methods per class, to a fixpoint: calls the verifier, or calls a gated
        # method of the same class.
        gated = {q for q, (_cls, fn) in functions.items() if _calls_the_verifier(fn)}
        changed = True
        while changed:
            changed = False
            for q, (cls, fn) in functions.items():
                if q in gated or cls is None:
                    continue
                if any(f"{cls}.{name}" in gated for name in _self_calls(fn)):
                    gated.add(q)
                    changed = True
        for q, (_cls, fn) in functions.items():
            if cores := _called_names(fn) & _IRREVERSIBLE:
                found[(rel, q)] = (cores, q in gated)
    return found


#: Measured when the second class was added (review SEC-004 d).
EXPECTED_IRREVERSIBLE_CALLERS = 11


def test_every_caller_of_an_irreversible_core_reaches_the_step_up_or_is_classified() -> None:
    found = irreversible_callers()
    print(f"irreversible-core callers: {len(found)}")  # noqa: T201 - the measured count, read by the reviewer
    for (rel, name), (cores, gated) in sorted(found.items()):
        print(f"  {rel}::{name} gated={gated} {sorted(cores)}")  # noqa: T201
    ungated = sorted(
        f"{rel}::{name} -> {sorted(cores)}"
        for (rel, name), (cores, gated) in found.items()
        if not gated and (rel, name) not in _IRREVERSIBLE_CALLERS
    )

    assert ungated == [], (
        "A caller of an irreversible erasure core must reach self._step_up_verifier (directly or through a "
        "method of its class) or be classified with a reason:\n  " + "\n  ".join(ungated)
    )
    assert len(found) == EXPECTED_IRREVERSIBLE_CALLERS, sorted(found)


def test_the_step_up_entries_of_the_irreversible_class_are_gated() -> None:
    found = irreversible_callers()
    for entry in (
        ("domain/services/privacy_service.py", "PrivacyService.erase_account_by_admin"),
        ("domain/services/tenant_service.py", "TenantService.delete_tenant"),
    ):
        assert entry in found and found[entry][1], f"{entry} does not reach the step-up"


def test_no_irreversible_classification_is_stale() -> None:
    found = irreversible_callers()
    stale = sorted(f"{rel}::{name}" for rel, name in _IRREVERSIBLE_CALLERS if (rel, name) not in found)
    both = sorted(f"{rel}::{name}" for rel, name in _IRREVERSIBLE_CALLERS if found.get((rel, name), (0, False))[1])

    assert stale == []
    assert both == [], "classified but gated — the entry would outlive its reason"


def test_the_irreversible_predicate_resolves_helpers_inside_the_class_only() -> None:
    source = """
class S:
    def _check(self):
        self._step_up_verifier.verify()
    def entry(self):
        self._check()
        self._run_tenant_erasure(1)
    def sneaky(self):
        other._check()
        self._run_tenant_erasure(1)
"""
    functions = _qualified_functions(ast.parse(source))
    gated = {q for q, (_c, fn) in functions.items() if _calls_the_verifier(fn)}
    assert gated == {"S._check"}
    assert _self_calls(functions["S.entry"][1]) == {"_check", "_run_tenant_erasure"}
    assert "_check" not in _self_calls(functions["S.sneaky"][1])


# ── the verifier every service gets is the wired one (review, latent code fallback) ──
#
# A ``StepUpVerifier`` without a re-authentication policy cannot tell whether an
# account must re-authenticate at its provider, so it accepts the e-mailed code for
# any federated account — also one Variant 1 refuses it to. The services fall back
# to such a verifier only when constructed without one, which tests do. So the rule
# is held at composition: every construction of a step-up service under ``app/``
# passes ``step_up_verifier=``, and every construction of a verifier passes
# ``reauth_policy=`` — the fallback can then never be what production runs.

_STEP_UP_SERVICES = {"AuthService", "PrivacyService", "TenantService", "UserService"}


def _constructions(root: Path = APP) -> list[tuple[str, int, str, set[str]]]:
    found: list[tuple[str, int, str, set[str]]] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in _STEP_UP_SERVICES | {"StepUpVerifier"}:
                    found.append((rel, node.lineno, name, {kw.arg for kw in node.keywords if kw.arg}))
    return found


#: The one place a policy-less verifier is built: the services' fallback for tests.
_UNWIRED_VERIFIER_ALLOWED = {"domain/services/step_up_service.py"}


def test_every_production_step_up_service_gets_the_wired_verifier() -> None:
    found = _constructions()
    services = [c for c in found if c[2] in _STEP_UP_SERVICES]
    assert len(services) >= 3, services  # the DI providers — a scan that found none proves nothing

    missing = sorted(f"{rel}:{line} {name}" for rel, line, name, kws in services if "step_up_verifier" not in kws)
    unwired = sorted(
        f"{rel}:{line}"
        for rel, line, name, kws in found
        if name == "StepUpVerifier" and "reauth_policy" not in kws and rel not in _UNWIRED_VERIFIER_ALLOWED
    )

    assert missing == [], "a step-up service built without step_up_verifier= falls back to the unwired one"
    assert unwired == [], "a StepUpVerifier built without reauth_policy= accepts the code for OIDC accounts"


# ── security review of the #1847 bundle (SEC-002): only ``verify`` gates ────────


def _gated(source: str, qualname: str) -> bool:
    functions = _functions(ast.parse(source))
    helpers = _gating_helpers(functions)
    function = dict(functions)[qualname]
    own_class = qualname.split(".", 1)[0]
    return _calls_the_verifier(function, helpers.get(own_class, frozenset()))


def test_issuing_a_code_is_not_a_step_up() -> None:
    source = (
        "class S:\n"
        "    def mint(self, user):\n"
        "        self._step_up_verifier.issue_code(user, action='x')\n"
        "        self._api_key_repo.create(user)\n"
    )

    assert _gated(source, "S.mint") is False


def test_a_helper_that_only_issues_a_code_does_not_gate_its_callers() -> None:
    source = (
        "class S:\n"
        "    def _send_code(self, user):\n"
        "        self._step_up_verifier.issue_code(user, action='x')\n"
        "    def mint(self, user):\n"
        "        self._send_code(user)\n"
        "        self._api_key_repo.create(user)\n"
    )

    assert _gated(source, "S.mint") is False


def test_a_helper_that_verifies_gates_its_callers() -> None:
    source = (
        "class S:\n"
        "    def _step_up(self, user):\n"
        "        self._step_up_verifier.verify(user, action='x')\n"
        "    def mint(self, user):\n"
        "        self._step_up(user)\n"
        "        self._api_key_repo.create(user)\n"
    )

    assert _gated(source, "S.mint") is True
