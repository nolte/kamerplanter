"""#2119 (MT-023) — a repository over a tenant-bearing model decides its tenant scope.

``BaseArangoRepository.is_tenant_scoped`` defaults to ``False``. Its only effect
is in the base list reads (:meth:`get_all`, :meth:`list_window`): with the flag
set, a call without a ``tenant_key`` raises unless it says ``all_tenants=True``;
without it, the same call silently returns every tenant's rows (SEC-B4). A
default that is wrong for most tenant-bearing collections and that nobody has to
write down is the "guard opt-in at the call site" shape: on ``origin/develop``
before #2119, 15 of 43 repositories whose model declares ``tenant_key`` had
never decided.

**The rule.** Every concrete :class:`BaseArangoRepository` subclass under
``app/data_access`` whose bound model (``_model_cls``) declares ``tenant_key``
does exactly one of:

* set ``is_tenant_scoped = True``, or
* state why not in ``tenant_scope_exempt_reason`` — and be on
  :data:`EXEMPT_REPOSITORIES` here, so a new exemption is a reviewed diff in this
  file and never a quiet default.

Neither is a finding; both is a finding too (a flag that is on cannot be
exempt, and the stale reason would mislead the next reader).

**What the flag does not cover — named, not discovered later.** The flag gates
only the two base list reads. A hand-written read is held to its own tenant
argument by ``test_tenant_scoped_reads_are_derived.py``; ``find_by_field`` and
``get_page`` are not gated by the flag at all. And the rule sees only a model
bound as the ``_model_cls`` *class attribute*: a composed view
(``BaseArangoRepository[FishStock](db, col.FISH_STOCKS, FishStock)``) is an
instance, not a subclass, and keeps the base default. Measured on 2026-10-10: 42
such views, 17 of them over a model that declares ``tenant_key`` (actuator,
aquaponics, IPM, InvenTree, fertilizer stocks, cultivars, substrate batches).
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import cache
from typing import Any

import pytest
from pydantic import BaseModel

import app.data_access as data_access
from app.data_access.arango.base_repository import BaseArangoRepository

#: The repositories that deliberately keep the base list reads tenant-less, each
#: with its reason in ``tenant_scope_exempt_reason`` on the class itself. Pinned
#: exactly: adding a name is the review point for a new exemption, removing one is
#: what converting it to ``is_tenant_scoped`` records.
EXEMPT_REPOSITORIES: frozenset[str] = frozenset(
    {
        "ArangoSpeciesRepository",
        "ArangoSubstrateRepository",
    }
)

#: Anti-vacuity floor: measured 43 tenant-bearing repositories on 2026-10-10.
MIN_TENANT_BEARING_REPOSITORIES = 43

#: A reason must say something; a placeholder is not a decision.
MIN_REASON_LENGTH = 40


def _tenant_bearing(cls: type) -> bool:
    model = getattr(cls, "_model_cls", None)
    return isinstance(model, type) and issubclass(model, BaseModel) and "tenant_key" in model.model_fields


def undecided(classes: list[type]) -> list[str]:
    """The tenant-bearing repositories that neither scope nor state an exemption, or do both."""
    findings: list[str] = []
    for cls in classes:
        if not _tenant_bearing(cls):
            continue
        scoped = cls.is_tenant_scoped is True
        reason = getattr(cls, "tenant_scope_exempt_reason", None)
        has_reason = isinstance(reason, str) and len(reason.strip()) >= MIN_REASON_LENGTH
        if scoped and reason is not None:
            findings.append(f"{cls.__module__}.{cls.__name__}: is_tenant_scoped AND an exemption reason")
        elif not scoped and not has_reason:
            findings.append(f"{cls.__module__}.{cls.__name__}: neither is_tenant_scoped nor an exemption reason")
    return sorted(findings)


def _subclasses(cls: type) -> list[type]:
    found: list[type] = []
    for sub in cls.__subclasses__():
        found.append(sub)
        found.extend(_subclasses(sub))
    return found


@cache
def _application_repositories() -> tuple[type, ...]:
    """Every ``BaseArangoRepository`` subclass defined under ``app.data_access``.

    Imports every module first, so a repository no test happens to import is
    still seen; test-local subclasses are excluded by module.
    """
    for module in pkgutil.walk_packages(data_access.__path__, "app.data_access."):
        importlib.import_module(module.name)
    unique = {cls for cls in _subclasses(BaseArangoRepository) if cls.__module__.startswith("app.data_access.")}
    return tuple(sorted(unique, key=lambda c: (c.__module__, c.__name__)))


def _tenant_bearing_repositories() -> list[type]:
    return [cls for cls in _application_repositories() if _tenant_bearing(cls)]


class TestEveryTenantBearingRepositoryDecides:
    def test_no_repository_is_undecided(self) -> None:
        assert undecided(list(_application_repositories())) == [], (
            "A repository whose model declares tenant_key must set is_tenant_scoped = True, or state "
            "tenant_scope_exempt_reason and be added to EXEMPT_REPOSITORIES (MT-023, #2119)."
        )

    def test_the_exemptions_are_exactly_the_pinned_set(self) -> None:
        exempt = {cls.__name__ for cls in _tenant_bearing_repositories() if not cls.is_tenant_scoped}
        assert exempt == EXEMPT_REPOSITORIES, (
            "The set of tenant-bearing repositories that keep the base list reads tenant-less changed. "
            "A new exemption is reviewed here; a converted one leaves the set."
        )

    def test_no_repository_outside_the_rule_carries_a_reason(self) -> None:
        stray = [
            cls.__name__
            for cls in _application_repositories()
            if "tenant_scope_exempt_reason" in vars(cls) and not _tenant_bearing(cls)
        ]
        assert stray == [], "An exemption reason on a repository whose model has no tenant_key decides nothing"


class TestTheInventoryIsNotVacuous:
    def test_the_enumeration_sees_the_tenant_bearing_repositories(self) -> None:
        names = {cls.__name__ for cls in _tenant_bearing_repositories()}
        assert len(names) >= MIN_TENANT_BEARING_REPOSITORIES, sorted(names)
        # Known members of both outcomes, so an enumeration that silently lost a
        # package (a broken import walk) cannot pass on the remainder.
        assert {"ArangoPlantInstanceRepository", "ArangoAttachmentRepository", "ArangoSpeciesRepository"} <= names

    def test_every_exemption_names_a_real_repository(self) -> None:
        names = {cls.__name__ for cls in _tenant_bearing_repositories()}
        assert names >= EXEMPT_REPOSITORIES


class _TenantBearing(BaseModel):
    tenant_key: str = ""


class _Global(BaseModel):
    name: str = ""


_REASON = "a synthetic reason long enough to count as a stated decision"


def _repo(name: str, model: type[BaseModel], **attrs: Any) -> type:
    namespace: dict[str, Any] = {"_model_cls": model, "__module__": "tests.synthetic", **attrs}
    return type(name, (BaseArangoRepository,), namespace)


class TestTheDetectorItself:
    """The rule run on synthetic repositories — the same :func:`undecided` the application test calls."""

    def test_an_undecided_tenant_bearing_repository_is_flagged(self) -> None:
        assert undecided([_repo("Silent", _TenantBearing)]) == [
            "tests.synthetic.Silent: neither is_tenant_scoped nor an exemption reason"
        ]

    def test_a_scoped_repository_passes(self) -> None:
        assert undecided([_repo("Scoped", _TenantBearing, is_tenant_scoped=True)]) == []

    def test_an_exempt_repository_with_a_reason_passes(self) -> None:
        assert undecided([_repo("Exempt", _TenantBearing, tenant_scope_exempt_reason=_REASON)]) == []

    @pytest.mark.parametrize("reason", ["", "   ", "tbd"])
    def test_a_placeholder_reason_is_not_a_decision(self, reason: str) -> None:
        assert undecided([_repo("Placeholder", _TenantBearing, tenant_scope_exempt_reason=reason)]) != []

    def test_scoped_and_exempt_at_once_is_flagged(self) -> None:
        both = _repo("Both", _TenantBearing, is_tenant_scoped=True, tenant_scope_exempt_reason=_REASON)
        assert undecided([both]) == ["tests.synthetic.Both: is_tenant_scoped AND an exemption reason"]

    def test_a_repository_without_a_tenant_is_outside_the_rule(self) -> None:
        assert undecided([_repo("Global", _Global)]) == []

    def test_the_flag_inherited_from_a_scoped_parent_counts(self) -> None:
        parent = _repo("Parent", _TenantBearing, is_tenant_scoped=True)
        child: type = type("Child", (parent,), {"__module__": "tests.synthetic"})
        assert undecided([child]) == []
