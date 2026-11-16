"""A domain model stamped with the caller's account key stores it under a name the privacy inventory can see.

``scripts/check_privacy_inventory.py`` R6 finds every persisted account reference by the *shape* of its field name
(``user_key``, ``*_user_key``, ``*_by_key``, ``*_account_key``, ``*_by``) and refuses one the erasure does not reach.
A key stored under any other name is invisible to it: ``rooting_protocols.author`` held the raw key of the account
that last saved a protocol, was returned to every member, and survived that account's erasure (#2976). The repair
renamed the field to ``author_user_key``; this guard refuses the class, not the one site.

The class: a call that constructs a model defined in ``app/domain/models`` and passes the caller's account key —
an attribute ``<anything>.user_key`` (``ctx.user_key``, ``membership.user_key``) or a bare ``user_key`` /
``actor_user_key`` — as a keyword argument. The keyword is the stored field name, so it must have the R6 shape.
Calls to functions and to classes outside ``domain/models`` (a service method's ``actor_key=``) are not stored
fields and are not this guard's business.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

_APP = Path(__file__).resolve().parents[3] / "app"
_MODELS = _APP / "domain" / "models"

#: The bare names the code uses for the caller's own account key.
_ACCOUNT_KEY_NAMES = frozenset({"user_key", "actor_user_key"})

#: ``(model, field)`` stamps measured against the write path and decided: the key never lands in a stored field
#: R6 cannot see. A decided stamp the walk no longer finds is stale and refused, so the list cannot rot.
DECIDED: dict[tuple[str, str], str] = {
    ("AuthProvider", "provider_user_id"): (
        "the local login link names its own account as the provider's subject id; the whole auth_providers row "
        "is deleted on erasure by its user_key (ErasureEngine.DELETE_STEPS), so the copy goes with it"
    ),
    ("PlanBatchWrite", "editor_key"): (
        "a write set built in memory for one transaction (a dataclass, never stored); the editor lands in "
        "sites.plan.plan_updated_by, which the erasure anonymises"
    ),
    ("ServiceAccountInfo", "key"): "a read projection of a tenant's service accounts, returned and never stored",
}


def _model_class_names() -> frozenset[str]:
    names: set[str] = set()
    for path in _MODELS.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    return frozenset(names)


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _is_account_key(value: ast.expr) -> bool:
    if isinstance(value, ast.Attribute):
        return value.attr == "user_key"
    return isinstance(value, ast.Name) and value.id in _ACCOUNT_KEY_NAMES


def account_stamps(source: str, models: frozenset[str]) -> list[tuple[int, str, str]]:
    """``(line, model, field)`` of every keyword that hands a model the caller's account key."""
    found: list[tuple[int, str, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        model = _called_name(node)
        if model is None or model not in models:
            continue
        for keyword in node.keywords:
            if keyword.arg is not None and _is_account_key(keyword.value):
                found.append((node.lineno, model, keyword.arg))
    return found


@pytest.fixture(scope="module")
def reference_shape():  # type: ignore[no-untyped-def]
    return load_repo_script("check_privacy_inventory").USER_REFERENCE_FIELD


def test_every_stamped_account_key_has_a_reference_shaped_name(reference_shape) -> None:  # type: ignore[no-untyped-def]
    models = _model_class_names()
    stamps: list[str] = []
    seen: set[tuple[str, str]] = set()
    violations: list[str] = []
    for path in sorted(_APP.rglob("*.py")):
        for line, model, field in account_stamps(path.read_text(encoding="utf-8"), models):
            where = f"{path.relative_to(_APP.parent)}:{line} {model}({field}=...)"
            stamps.append(where)
            seen.add((model, field))
            if not reference_shape.match(field) and (model, field) not in DECIDED:
                violations.append(where)

    # The measuring tool first: a walk that finds no stamp at all would make the assertion below vacuous.
    assert len(stamps) >= 5, stamps
    assert violations == [], (
        "these fields store the caller's account key under a name scripts/check_privacy_inventory.py R6 cannot "
        f"see, so the erasure never reaches them (#2976): {violations}"
    )
    assert sorted(set(DECIDED) - seen) == [], "decided stamps the walk no longer finds; remove them from DECIDED"


class TestTheRule:
    MODELS = frozenset({"RootingProtocol", "CareEvent"})

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("RootingProtocol(name='n', author=ctx.user_key)", [(1, "RootingProtocol", "author")]),
            ("models.CareEvent(created_by=user_key)", [(1, "CareEvent", "created_by")]),
            ("service.send(user=ctx.user_key)", []),
            ("RootingProtocol(name=ctx.tenant_key)", []),
            ("Unrelated(author=ctx.user_key)", []),
        ],
        ids=["attribute-stamp", "bare-name-stamp", "not-a-model", "not-an-account-key", "class-outside-models"],
    )
    def test_account_stamps(self, source: str, expected: list[tuple[int, str, str]]) -> None:
        assert account_stamps(source, self.MODELS) == expected

    def test_the_shape_refuses_the_old_field_and_takes_the_new_one(self, reference_shape) -> None:  # type: ignore[no-untyped-def]
        assert not reference_shape.match("author")
        assert reference_shape.match("author_user_key")
