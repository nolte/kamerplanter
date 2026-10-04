"""Every reader of ``email_verified`` that TRUSTS it uses the proof, or is decided.

``test_email_verified_writers_record_the_proof`` covers who *sets* the flag. This covers who *acts on
it*. ``email_verified`` is stamped without any confirmation when ``REQUIRE_EMAIL_VERIFICATION=false``,
so a decision that trusts it hands the address to whoever registered it first. The measured instance:
the OIDC auto-link read it, so the registrant of ``victim@example.org`` kept the account when the
victim signed in through a provider.

The population is derived, not listed: every function under ``app/`` (migrations excluded) that
reads ``email_verified`` — an attribute load, a ``["email_verified"]`` / ``.get("email_verified")``
read, or an AQL ``<alias>.email_verified`` comparison. A reader must mention ``email_confirmed_at``
or ``address_proven`` in the same function, or be on :data:`DECIDED` with its reason. A
:data:`DECIDED` entry that no longer matches a reader fails, so the list cannot outlive what it
excused.
"""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
PROOF_NAMES = ("email_confirmed_at", "address_proven")
_AQL_READ = re.compile(r"\b\w+\.email_verified\b")

#: (relative path, function) -> why reading the flag without the proof is not a trust decision.
DECIDED: dict[tuple[str, str], str] = {
    ("domain/services/auth_service.py", "AuthService.login_local"): (
        "Sign-in gate of the account's own password, enforced only while REQUIRE_EMAIL_VERIFICATION is on: it "
        "decides whether the holder of the credential may enter, not whether a third party's assertion may "
        "act on the address."
    ),
    ("domain/services/auth_service.py", "AuthService._to_profile"): "Response projection; nothing decides on it.",
    ("domain/services/auth_service.py", "AuthService._register_oauth_user"): (
        "Reads the PROVIDER's claim (OAuthUserInfo.email_verified) and writes the proof with it; the writers guard "
        "covers the write."
    ),
    ("domain/engines/oauth_engine.py", "OAuthEngine._extract_from_id_token"): (
        "Parses the PROVIDER's claim into OAuthUserInfo; not a stored account's flag."
    ),
    ("domain/engines/oauth_engine.py", "OAuthEngine._fetch_userinfo_endpoint"): (
        "Parses the PROVIDER's claim into OAuthUserInfo; not a stored account's flag."
    ),
    ("domain/services/user_service.py", "UserService.admin_update_user"): (
        "Compares the stored flag with the requested one to record a lowering (#1992) and to demand the "
        "step-up; it grants nothing to anyone."
    ),
    ("domain/services/user_service.py", "UserService._to_profile"): "Response projection; nothing decides on it.",
    ("domain/services/privacy_service.py", "PrivacyService._open_immediate_erasure"): (
        "Skips the erasure of an account the flag marks established; an unproven-but-flagged account is KEPT, "
        "so reading the flag alone errs toward not deleting."
    ),
    ("data_access/arango/user_repository.py", "<module>"): (
        "The unverified-account cleanup's selection query; it errs toward not selecting."
    ),
    ("api/v1/admin/platform/router.py", "list_all_users"): "Response projection; nothing decides on it.",
    ("api/v1/admin/platform/router.py", "update_user"): "Response projection; nothing decides on it.",
}


def _is_flag(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return node.attr == "email_verified" and isinstance(node.ctx, ast.Load)
    if isinstance(node, ast.Subscript):
        return isinstance(node.slice, ast.Constant) and node.slice.value == "email_verified"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        return bool(node.args) and isinstance(node.args[0], ast.Constant) and node.args[0].value == "email_verified"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(_AQL_READ.search(node.value)) and "\n" in node.value
    return False


def _mentions_proof(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return node.attr in PROOF_NAMES
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value in PROOF_NAMES
    return False


def _readers(source: str) -> list[tuple[str, bool]]:
    """``(function name, uses the proof)`` for each function that reads ``email_verified``."""
    tree = ast.parse(textwrap.dedent(source))
    found: list[tuple[str, bool]] = []

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, (*scope, child.name))
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                nodes = list(ast.walk(child))
                if any(_is_flag(n) for n in nodes):
                    found.append((".".join((*scope, child.name)), any(_mentions_proof(n) for n in nodes)))
                visit(child, (*scope, child.name))
            else:
                visit(child, scope)

    visit(tree, ())
    # Module-level code (an AQL constant) is a reader too; its scope is "<module>".
    outside = [
        n
        for stmt in tree.body
        if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        for n in ast.walk(stmt)
    ]
    if any(_is_flag(n) for n in outside):
        found.append(("<module>", any(_mentions_proof(n) for n in outside)))
    return found


def _population() -> dict[tuple[str, str], bool]:
    population: dict[tuple[str, str], bool] = {}
    for path in sorted(APP.rglob("*.py")):
        relative = path.relative_to(APP).as_posix()
        if relative.startswith("migrations/"):
            continue
        for function, proves in _readers(path.read_text(encoding="utf-8")):
            population[(relative, function)] = proves
    return population


def test_every_reader_of_email_verified_uses_the_proof_or_is_decided() -> None:
    missing = sorted(key for key, proves in _population().items() if not proves and key not in DECIDED)
    assert not missing, (
        f"these functions read email_verified without email_confirmed_at/address_proven: {missing}. "
        "Decide on User.address_proven, or list the function in DECIDED with the reason it is no trust decision."
    )


def test_every_decided_entry_still_matches_a_proofless_reader() -> None:
    population = _population()
    stale = sorted(key for key in DECIDED if population.get(key) is not False)
    assert not stale, f"DECIDED entries that no longer name a proofless reader: {stale}"


def test_the_derived_population_is_not_vacuous() -> None:
    population = _population()
    # The OIDC auto-link is the decision this guard exists for, and it uses the proof.
    assert population[("domain/services/auth_service.py", "AuthService._complete_login")] is True
    assert ("domain/services/auth_service.py", "AuthService.login_local") in population
    assert ("domain/engines/notification_engine.py", "NotificationEngine.resolve_email_recipient") in population
    assert population[("domain/engines/notification_engine.py", "NotificationEngine.resolve_email_recipient")] is True


def test_the_detector_tells_a_trusting_reader_from_a_proving_one() -> None:
    trusting = """
    class S:
        def link(self, user):
            return user.email_verified
    """
    proving = """
    class S:
        def link(self, user):
            return user.email_verified and user.email_confirmed_at is not None
    """
    by_helper = """
    class S:
        def link(self, user):
            return user.address_proven
    """
    dict_read = """
    def f(doc):
        return doc.get("email_verified")
    """
    aql = '''
    def q():
        return """
        FOR doc IN users
          FILTER doc.email_verified == false
        """
    '''
    writer_only = """
    def w(repo, key):
        repo.update_fields(key, {"email_verified": True})
    """
    assert _readers(trusting) == [("S.link", False)]
    assert _readers(proving) == [("S.link", True)]
    assert _readers(by_helper) == []  # the helper's own name is not the flag
    assert _readers(dict_read) == [("f", False)]
    assert _readers(aql) == [("q", False)]
    assert _readers(writer_only) == []


def test_the_detector_finds_a_module_level_reader() -> None:
    module_level = '''
Q = """
FOR doc IN users
  FILTER doc.email_verified == false
"""
'''
    assert _readers(module_level) == [("<module>", False)]
