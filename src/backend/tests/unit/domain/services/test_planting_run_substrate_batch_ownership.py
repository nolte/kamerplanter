"""A planting run references only a substrate batch of its own tenant — #1868.

``POST /t/{slug}/planting-runs`` took ``substrate_batch_key`` from the body, and
the clone path copied the template's; ``create_run`` checked only the location
(#1372), and the repository stored the key and wrote a ``run_uses_substrate``
edge to whatever batch it named. A batch has exactly one owner (#1195), so the
key is resolved under the run's tenant with ``SubstrateService.get_batch``
semantics — strict equality — before anything is stored.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunType
from app.common.exceptions import NotFoundError
from app.domain.models.planting_run import PlantingRun
from app.domain.services.planting_run_service import PlantingRunService
from tests.unit.domain.services.test_planting_run_location_ownership import FakeRunRepo, FakeSiteRepo

OWN = "tenant_own"
_BATCH_OWNER = {"b_own": OWN, "b_foreign": "tenant_other", "b_legacy": ""}


def _resolve_batch(key: str, *, tenant_key: str) -> None:
    """``SubstrateService.get_batch`` semantics: strict equality, 404 otherwise."""
    if _BATCH_OWNER.get(key) != tenant_key:
        raise NotFoundError("SubstrateBatch", key)


def _service(run_repo: FakeRunRepo, *, resolver=_resolve_batch) -> PlantingRunService:
    engine = MagicMock()
    engine.validate_run_type_constraints.return_value = None
    return PlantingRunService(
        run_repo, MagicMock(), engine=engine, site_repo=FakeSiteRepo(), substrate_batch_resolver=resolver
    )


def _run(batch: str | None, *, clone_from: str | None = None, tenant_key: str = OWN) -> PlantingRun:
    return PlantingRun(
        tenant_key=tenant_key,
        name="Salat",
        run_type=PlantingRunType.MONOCULTURE,
        substrate_batch_key=batch,
        clone_from_run_key=clone_from,
    )


@pytest.mark.parametrize("batch", ["b_foreign", "b_legacy", "no-such-batch"])
def test_a_batch_that_is_not_the_tenants_is_refused_before_anything_is_stored(batch: str) -> None:
    repo = FakeRunRepo()

    with pytest.raises(NotFoundError):
        _service(repo).create_run(_run(batch))

    assert repo.store == {}


def test_the_clone_path_resolves_the_inherited_batch_too() -> None:
    repo = FakeRunRepo()
    repo.store["tpl"] = _run("b_foreign").model_copy(update={"key": "tpl"})

    with pytest.raises(NotFoundError):
        _service(repo).create_run(_run(None, clone_from="tpl"))

    assert list(repo.store) == ["tpl"]


def test_the_tenants_own_batch_is_accepted() -> None:
    repo = FakeRunRepo()

    created = _service(repo).create_run(_run("b_own"))

    assert created.substrate_batch_key == "b_own"


def test_without_a_resolver_a_batch_reference_is_refused_not_skipped() -> None:
    repo = FakeRunRepo()

    with pytest.raises(NotFoundError):
        _service(repo, resolver=None).create_run(_run("b_own"))

    assert repo.store == {}


def test_a_run_without_a_batch_needs_no_resolver() -> None:
    repo = FakeRunRepo()

    created = _service(repo, resolver=None).create_run(_run(None))

    assert created.substrate_batch_key is None
