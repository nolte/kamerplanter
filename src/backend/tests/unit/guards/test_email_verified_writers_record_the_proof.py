"""#1948 — every writer of ``email_verified`` also writes ``email_confirmed_at``, or is decided.

``email_verified`` is stamped without any confirmation when
``REQUIRE_EMAIL_VERIFICATION=false``, so it cannot decide who is mailed
(REQ-030 §3.4). ``email_confirmed_at`` is the proof and is read by
``NotificationEngine.resolve_email_recipient``. A writer that raises
``email_verified`` and forgets the proof silently keeps its account out of
notification mail; one that writes only the proof would hand mail to an
unverified account. The class is every such writer, so it is derived, not listed:

* **Writers** — every function under ``app/`` that sets ``email_verified`` to a
  value other than a literal ``False``/``None``: a ``User(...)`` constructor
  keyword, a dict key (``update_fields`` / ``move_email`` payloads), or an
  attribute assignment. Read from the AST, so a new writer is found without being
  enrolled. Response models (``UserProfile(email_verified=user.email_verified)``)
  are not writers: they are not ``User`` constructors.
* A writer must mention ``email_confirmed_at`` in the same function, or be on
  :data:`DECIDED` with its reason. A :data:`DECIDED` entry that no longer matches
  a writer fails, so the list cannot outlive what it excused.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"

#: (relative path, function) -> why it raises ``email_verified`` without the proof.
DECIDED: dict[tuple[str, str], str] = {
    ("domain/services/auth_service.py", "AuthService.register_local"): (
        "Registration stamps the flag only while REQUIRE_EMAIL_VERIFICATION is off, where nothing has been "
        "confirmed. Withholding the proof is the point of #1948: such an account is mailed only after "
        "it follows a verification link."
    ),
    ("migrations/seed_auth.py", "run_seed_auth"): (
        "The seeded demo account (@kamerplanter.local) is a fixture, not a mailbox; nothing can be mailed to it."
    ),
    ("migrations/seed_light_mode.py", "run_seed_light_mode"): (
        "The light-mode system account has no mailbox; it signs in without a credential."
    ),
    ("migrations/seed_e2e_platform_admin.py", "run_seed_e2e_platform_admin"): (
        "E2E fixture account on a reserved test address; an e-mail-channel test confirms through the link."
    ),
}

#: (relative path, class) -> why a request model that carries ``email_verified`` as an *input* is not a
#: proof writer. The value is written by ``UserService.admin_update_user`` from a dict, which no AST of a
#: single function can follow, so the request model is the derived edge.
DECIDED_INPUTS: dict[tuple[str, str], str] = {
    ("api/v1/admin/platform/schemas.py", "AdminUserUpdate"): (
        "An administrator raising the flag is an attestation, not the owner's proof of the address "
        "(#1857 step-up governs who may raise it); the proof stays absent so no mail is aimed at it."
    ),
}


def _writers(source: str) -> list[tuple[str, bool]]:
    """``(function name, writes the proof)`` for each function that raises ``email_verified``."""
    tree = ast.parse(textwrap.dedent(source))
    found: list[tuple[str, bool]] = []

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, (*scope, child.name))
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                body_nodes = list(ast.walk(child))
                if any(_raises_verified(n) for n in body_nodes):
                    found.append((".".join((*scope, child.name)), any(_writes_proof(n) for n in body_nodes)))
                visit(child, (*scope, child.name))
            else:
                visit(child, scope)

    visit(tree, ())
    return found


def _is_falsy_literal(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value in (False, None)


def _raises_verified(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "User":
        return any(k.arg == "email_verified" and not _is_falsy_literal(k.value) for k in node.keywords)
    if isinstance(node, ast.Dict):
        return any(
            isinstance(k, ast.Constant) and k.value == "email_verified" and not _is_falsy_literal(v)
            for k, v in zip(node.keys, node.values, strict=True)
        )
    if isinstance(node, ast.Assign):
        return any(isinstance(t, ast.Attribute) and t.attr == "email_verified" for t in node.targets) and (
            not _is_falsy_literal(node.value)
        )
    return False


def _writes_proof(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "User":
        return any(k.arg == "email_confirmed_at" for k in node.keywords)
    if isinstance(node, ast.Dict):
        return any(isinstance(k, ast.Constant) and k.value == "email_confirmed_at" for k in node.keys)
    if isinstance(node, ast.Assign):
        return any(isinstance(t, ast.Attribute) and t.attr == "email_confirmed_at" for t in node.targets)
    return False


def _inputs(source: str) -> list[str]:
    """Classes declaring an *optional* ``email_verified`` field: a request model that lets a caller set it."""
    found: list[str] = []
    for node in ast.walk(ast.parse(textwrap.dedent(source))):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if (
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "email_verified"
                and not (isinstance(item.annotation, ast.Name) and item.annotation.id == "bool")
            ):
                found.append(node.name)
    return found


def _input_population() -> set[tuple[str, str]]:
    return {
        (path.relative_to(APP).as_posix(), name)
        for path in sorted((APP / "api").rglob("*.py"))
        for name in _inputs(path.read_text(encoding="utf-8"))
    }


def _population() -> dict[tuple[str, str], bool]:
    population: dict[tuple[str, str], bool] = {}
    for path in sorted(APP.rglob("*.py")):
        for function, proves in _writers(path.read_text(encoding="utf-8")):
            population[(path.relative_to(APP).as_posix(), function)] = proves
    return population


def test_every_writer_of_email_verified_writes_the_proof_or_is_decided() -> None:
    population = _population()
    missing = sorted(key for key, proves in population.items() if not proves and key not in DECIDED)
    assert not missing, (
        f"these functions raise email_verified without writing email_confirmed_at: {missing}. "
        "Write the proof where the owner demonstrably reached the address, or decide it in DECIDED with a reason."
    )


def test_every_decided_entry_still_matches_a_writer_without_the_proof() -> None:
    population = _population()
    stale = sorted(key for key in DECIDED if population.get(key) is not False)
    assert not stale, f"DECIDED entries that no longer name a proofless writer: {stale}"


def test_the_derived_population_is_not_vacuous() -> None:
    population = _population()
    for known in (
        ("domain/services/auth_service.py", "AuthService.verify_email"),
        ("domain/services/auth_service.py", "AuthService._register_oauth_user"),
        ("domain/services/auth_service.py", "AuthService.register_local"),
    ):
        assert known in population, f"the detector no longer finds {known}"
    assert population[("domain/services/auth_service.py", "AuthService.verify_email")] is True
    # Registration stamps email_verified without a confirmation and must not carry the proof:
    assert population[("domain/services/auth_service.py", "AuthService.register_local")] is False


def test_the_detector_tells_a_proofless_writer_from_a_proving_one() -> None:
    proofless = """
    class S:
        def confirm(self, repo, key):
            repo.update_fields(key, {"email_verified": True})
    """
    proving = """
    class S:
        def confirm(self, repo, key):
            repo.update_fields(key, {"email_verified": True, "email_confirmed_at": 1})
    """
    lowering = """
    class S:
        def demote(self, repo, key):
            repo.update_fields(key, {"email_verified": False})
    """
    constructor = """
    def make():
        return User(email="a@b.c", display_name="A", email_verified=True)
    """
    response_model = """
    def to_profile(user):
        return UserProfile(email_verified=user.email_verified)
    """
    assert _writers(proofless) == [("S.confirm", False)]
    assert _writers(proving) == [("S.confirm", True)]
    assert _writers(lowering) == []
    assert _writers(constructor) == [("make", False)]
    assert _writers(response_model) == []


def test_every_request_model_that_accepts_email_verified_is_decided() -> None:
    population = _input_population()
    assert population == set(DECIDED_INPUTS), (
        f"request models carrying an optional email_verified: {sorted(population)}; decided: "
        f"{sorted(DECIDED_INPUTS)}. A new input surface needs a decision about the proof."
    )


def test_the_input_detector_tells_an_optional_field_from_a_response_field() -> None:
    assert _inputs("class A(BaseModel):\n    email_verified: bool | None = None\n") == ["A"]
    assert _inputs("class B(BaseModel):\n    email_verified: bool\n") == []
