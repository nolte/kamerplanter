"""#1963 — ``readable_species`` and the stored-species check of a planting run, without a database."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.species_visibility import readable_species


def _repo(owner: str | None, granted: bool = False) -> MagicMock:
    repo = MagicMock()
    repo.get_by_key.return_value = None if owner is None else SimpleNamespace(tenant_key=owner)
    repo.is_granted_to.return_value = granted
    return repo


@pytest.mark.parametrize(
    ("owner", "granted", "tenant", "readable"),
    [
        ("", False, "A", True),  # global
        ("A", False, "A", True),  # own
        ("B", True, "A", True),  # granted
        ("B", False, "A", False),  # foreign
        ("B", False, "", False),  # no tenant reads only global
        (None, False, "A", False),  # unknown
    ],
)
def test_readable_species_is_global_own_or_granted(owner, granted, tenant, readable) -> None:
    assert (readable_species(_repo(owner, granted), "sp", tenant) is not None) is readable


def _service(resolver) -> PlantingRunService:
    return PlantingRunService(MagicMock(), MagicMock(), engine=MagicMock(), species_resolver=resolver)


def test_a_stored_species_the_resolver_refuses_is_not_readable() -> None:
    def resolver(key, *, tenant_key):
        raise NotFoundError("Species", key)

    assert _service(resolver)._species_is_readable("sp", "A") is False


def test_a_stored_species_the_resolver_answers_is_readable() -> None:
    assert _service(lambda key, *, tenant_key: object())._species_is_readable("sp", "A") is True


def test_without_a_resolver_a_tenant_run_reads_nothing_and_a_tenantless_run_is_not_judged() -> None:
    service = _service(None)

    assert service._species_is_readable("sp", "A") is False
    assert service._species_is_readable("sp", "") is True
