"""#1788 — every container an account owns has a decided fate when the account is erased.

The defect class of #1788: a container **owned** by an account (not merely
written by it) outlives the account with everything in it. The account-erasure
plan reaches rows by the account's *reference* fields; ownership of a whole
container is a different relation, and the personal tenant — the only such
container today — kept its sites, plants, diary and tasks for good, because the
plan only replaced its ``owner_user_key``.

This guard enumerates the class from the domain models, not from a list of the
sites found so far: every model field that records an **owning account**
(``owner_user_key`` / ``*_owner_key`` / ``owner_*_key``) must be decided in
:data:`DECIDED_OWNERSHIP`, with what the account erasure does to the container.
A new ownership field fails here until someone decides it. The decision for
``Tenant.owner_user_key`` is additionally pinned to the code that carries it out,
through the public surface (signatures and the declared plan), never the source
text.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re

from pydantic import BaseModel

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService

#: A field that names the account *owning* the row's container.
OWNERSHIP_FIELD = re.compile(r"^(owner_[a-z_]*key|[a-z_]*_owner_key|owner_user_key)$")

#: (model, field) -> what the account erasure does with the owned container.
DECIDED_OWNERSHIP: dict[tuple[str, str], str] = {
    ("Tenant", "owner_user_key"): (
        "A personal tenant whose only active member is the erased account goes through the "
        "tenant-erasure inventory (PrivacyService.erase_account step 4, #1788); any other tenant "
        "is kept and loses the owner reference (ErasureEngine tenants rule); who takes over a "
        "shared personal tenant is open (#1824)."
    ),
}


def ownership_fields(models: list[type[BaseModel]]) -> set[tuple[str, str]]:
    """``(model, field)`` for every field of *models* that records an owning account (pure)."""
    found: set[tuple[str, str]] = set()
    for model in models:
        for name in model.model_fields:
            if OWNERSHIP_FIELD.match(name):
                found.add((model.__name__, name))
    return found


def _domain_models() -> list[type[BaseModel]]:
    import app.domain.models as package

    models: list[type[BaseModel]] = []
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"app.domain.models.{info.name}")
        models += [
            obj
            for obj in vars(module).values()
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__module__ == module.__name__
        ]
    return models


def test_every_ownership_field_is_decided():
    undecided = sorted(ownership_fields(_domain_models()) - set(DECIDED_OWNERSHIP))
    assert undecided == [], (
        "A model records an owning account without a decided fate on account erasure (#1788). "
        "Decide it in DECIDED_OWNERSHIP and implement it in the account erasure: "
        f"{undecided}"
    )


def test_no_decision_names_a_field_that_does_not_exist():
    assert sorted(set(DECIDED_OWNERSHIP) - ownership_fields(_domain_models())) == []


def test_the_tenant_decision_is_carried_by_the_code():
    # The kept tenant names nobody: the plan's rule on the owner field.
    rules = [r for r in ErasureEngine().build_erasure_plan("probe").anonymize if r.collection == "tenants"]
    assert [r.user_field for r in rules] == ["owner_user_key"]
    # The erased one: the account erasure hands personal tenants to the tenant service,
    # and records them on the request so a retry still reaches them.
    assert {"recorded_personal_tenant_keys", "on_personal_tenants_resolved"} <= set(
        inspect.signature(PrivacyService.erase_account).parameters
    )
    assert "tenant_service" in inspect.signature(PrivacyService).parameters
    assert callable(TenantService.erase_personal_tenant_of)
    assert callable(TenantService.personal_tenant_keys_of)


class TestTheDetectorSeesTheClass:
    """Self-tests through the same detector the guard uses."""

    def test_an_ownership_field_under_another_name_is_found(self):
        class Garden(BaseModel):
            owner_account_key: str
            created_by: str

        class Board(BaseModel):
            board_owner_key: str

        assert ownership_fields([Garden, Board]) == {("Garden", "owner_account_key"), ("Board", "board_owner_key")}

    def test_a_reference_that_is_not_ownership_is_not(self):
        class Row(BaseModel):
            user_key: str
            created_by: str
            tenant_key: str

        assert ownership_fields([Row]) == set()
