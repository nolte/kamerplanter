"""The #1619 route-scoping hook, checked against its own failure modes.

A guard nobody falsifies is a comment with a shebang. The cases below are the
three ways this one could be useless:

* it could miss the defect it exists for (the unfixed IPM read);
* it could be satisfied by a *comment* claiming the predicate — the vacuum trap
  of PR #1545, #1608 and #1610, where the assertion's own prose satisfied it;
* it could be so strict that a correctly-scoped route is red, which is how a
  guard gets disabled.
"""

from __future__ import annotations

import pathlib
import sys

#: ``src/backend/tests/unit/…`` → the repository root is four levels up.
#: Resolved, not ``importorskip``-ed: a hook whose own test SKIPS when the path
#: drifts is the silent-skip failure this repository has measured before.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_plant_scoped_route_tenant as check_module  # noqa: E402


def _write(tmp_path: pathlib.Path, body: str) -> pathlib.Path:
    (tmp_path / "router.py").write_text(body, encoding="utf-8")
    return tmp_path


UNFIXED = """
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ipm")


@router.get("/plants/{plant_key}/karenz")
def get_karenz_periods(plant_key: str, ctx=Depends(get_current_tenant), service=Depends(get_ipm_service)):
    return service.get_karenz_periods(plant_key)
"""

COMMENT_ONLY = '''
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ipm")


@router.get("/plants/{plant_key}/karenz")
def get_karenz_periods(plant_key: str, ctx=Depends(get_current_tenant), service=Depends(get_ipm_service)):
    # Scoped to ctx.tenant_key by the service; tenant_key=ctx.tenant_key.
    """The service scopes this to ctx.tenant_key."""
    return service.get_karenz_periods(plant_key)
'''

FIXED = """
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ipm")


@router.get("/plants/{plant_key}/karenz")
def get_karenz_periods(plant_key: str, ctx=Depends(get_current_tenant), service=Depends(get_ipm_service)):
    return service.get_karenz_periods(plant_key, tenant_key=ctx.tenant_key)
"""

DEPENDENCY = """
from fastapi import APIRouter, Depends

from app.common.plant_ownership import require_owned_plant

router = APIRouter(prefix="/phases", dependencies=[Depends(require_owned_plant)])


@router.get("/plants/{plant_key}/history")
def history(plant_key: str, service=Depends(get_phase_service)):
    return service.history(plant_key)
"""

MARKED = """
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ipm")


# tenant-scope-ok: verified in the repository (#517).
@router.post("/plants/{plant_key}/inspections")
def create_inspection(plant_key: str, ctx=Depends(get_current_tenant), service=Depends(get_ipm_service)):
    inspection = Inspection(tenant_key=ctx.tenant_key)
    return service.create_inspection(plant_key, inspection)
"""

MARKER_WITHOUT_REASON = """
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ipm")


# tenant-scope-ok:
@router.get("/plants/{plant_key}/karenz")
def get_karenz_periods(plant_key: str, ctx=Depends(get_current_tenant), service=Depends(get_ipm_service)):
    return service.get_karenz_periods(plant_key)
"""

TERMINAL_KEY = """
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/tanks")


@router.get("/{tank_key}")
def get_tank(tank_key: str, service=Depends(get_tank_service)):
    return service.get(tank_key)
"""


def test_it_catches_the_defect_it_exists_for(tmp_path: pathlib.Path) -> None:
    violations, exempted = check_module.check(_write(tmp_path, UNFIXED))

    assert len(violations) == 1, violations
    assert "GET /plants/{plant_key}/karenz" in violations[0]
    assert not exempted


def test_a_comment_asserting_the_predicate_does_not_satisfy_it(tmp_path: pathlib.Path) -> None:
    """The whole point: prose is not enforcement.

    This source mentions ``ctx.tenant_key`` and even ``tenant_key=ctx.tenant_key``
    — in a comment and a docstring. The check reads the AST, where neither
    exists, so it must be as red as the version with no comment at all.
    """
    violations, _ = check_module.check(_write(tmp_path, COMMENT_ONLY))

    assert len(violations) == 1, violations


def test_the_real_fix_clears_it(tmp_path: pathlib.Path) -> None:
    violations, exempted = check_module.check(_write(tmp_path, FIXED))

    assert violations == []
    assert exempted == []


def test_a_router_level_ownership_dependency_clears_it(tmp_path: pathlib.Path) -> None:
    violations, _ = check_module.check(_write(tmp_path, DEPENDENCY))

    assert violations == []


def test_a_marker_with_a_reason_is_recorded_not_silenced(tmp_path: pathlib.Path) -> None:
    violations, exempted = check_module.check(_write(tmp_path, MARKED))

    assert violations == []
    assert len(exempted) == 1
    assert "#517" in exempted[0]


def test_a_marker_without_a_reason_does_not_count(tmp_path: pathlib.Path) -> None:
    violations, exempted = check_module.check(_write(tmp_path, MARKER_WITHOUT_REASON))

    assert len(violations) == 1, violations
    assert not exempted


def test_a_terminal_key_is_out_of_class(tmp_path: pathlib.Path) -> None:
    """``GET /tanks/{tank_key}`` is the resource itself, not a parent.

    Whether that read is scoped is a real question, and a different one; pinning
    it here would make the hook claim a reach it does not have.
    """
    violations, _ = check_module.check(_write(tmp_path, TERMINAL_KEY))

    assert violations == []


def test_the_ownable_params_track_the_ownership_allowlist() -> None:
    """A new tenant-ownable collection must not silently fall out of the class.

    ``OWNABLE_PARAMS`` is the name map onto
    ``OWNERSHIP_VERIFIABLE_COLLECTIONS``; if that frozenset grows and the map
    does not, every route taking the new key is out of class and nobody is told.
    """
    from app.data_access.arango.tenant_ownership import OWNERSHIP_VERIFIABLE_COLLECTIONS

    assert len(check_module.OWNABLE_PARAMS) == len(OWNERSHIP_VERIFIABLE_COLLECTIONS), (
        "OWNABLE_PARAMS and OWNERSHIP_VERIFIABLE_COLLECTIONS have drifted — "
        f"{sorted(check_module.OWNABLE_PARAMS)} vs {sorted(OWNERSHIP_VERIFIABLE_COLLECTIONS)}"
    )


def test_the_repository_tree_is_clean() -> None:
    """The hook's verdict on the real tree, asserted from the suite too."""
    root = REPO_ROOT / "src" / "backend" / "app" / "api"
    violations, _ = check_module.check(root)

    assert violations == [], violations
