"""Assigning a substrate batch to a slot stays inside the caller's tenant — #1864.

``POST /api/v1/substrates/batches/{batch_key}/assign-slot/{slot_key}`` resolved no
tenant; the service checked that the batch *existed* and the repository wrote a
``filled_with`` edge between any two keys. A member of any tenant, any role,
could attach tenant B's batch to tenant B's slot, or cross them between tenants.

A slot carries no usable ``tenant_key`` of its own: it is its location's site's
(#1397). The doubles below keep that shape — the slot and location docs leave
``tenant_key`` empty, only the sites carry it — so a check that read
``slot.tenant_key`` would refuse the caller's own slot here, as it would in
production.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.site import Location, Site, Slot
from app.domain.models.substrate import SubstrateBatch
from app.domain.services.substrate_service import SubstrateService


class _SubstrateRepo:
    def __init__(self) -> None:
        self.edges: list[tuple[str, str]] = []
        self._batches = {
            "b_a": SubstrateBatch(
                _key="b_a", tenant_key="t_a", batch_id="A-1", volume_liters=10, mixed_on=date(2026, 9, 1)
            ),
            "b_b": SubstrateBatch(
                _key="b_b", tenant_key="t_b", batch_id="B-1", volume_liters=10, mixed_on=date(2026, 9, 1)
            ),
        }

    def get_batch_or_raise(self, key: str) -> SubstrateBatch:
        if key not in self._batches:
            raise NotFoundError("SubstrateBatch", key)
        return self._batches[key]

    def assign_batch_to_slot(self, batch_key: str, slot_key: str) -> dict:
        self.edges.append((batch_key, slot_key))
        return {"_from": f"slots/{slot_key}", "_to": f"substrate_batches/{batch_key}"}


class _Anchors:
    """slot → location → site; only the site says whose it is."""

    _sites = {
        "site_a": Site(_key="site_a", tenant_key="t_a", name="A"),
        "site_b": Site(_key="site_b", tenant_key="t_b", name="B"),
    }
    _locations = {
        "loc_a": Location(_key="loc_a", name="A", site_key="site_a", area_m2=1.0),
        "loc_b": Location(_key="loc_b", name="B", site_key="site_b", area_m2=1.0),
    }
    _slots = {
        "slot_a": Slot(_key="slot_a", slot_id="TENTA_A1", location_key="loc_a"),
        "slot_b": Slot(_key="slot_b", slot_id="TENTB_B1", location_key="loc_b"),
    }

    def get_site_by_key(self, key: str) -> Site | None:
        return self._sites.get(key)

    def get_location_by_key(self, key: str) -> Location | None:
        return self._locations.get(key)

    def get_slot_by_key(self, key: str) -> Slot | None:
        return self._slots.get(key)


def _service() -> tuple[SubstrateService, _SubstrateRepo]:
    repo = _SubstrateRepo()
    return SubstrateService(repo, slot_anchors=_Anchors()), repo  # type: ignore[arg-type]


def _assign(service: SubstrateService, batch: str, slot: str, *, role: TenantRole = TenantRole.GROWER) -> dict:
    return service.assign_batch_to_slot(batch, slot, tenant_key="t_a", caller_role=role, is_platform_admin=False)


def test_a_grower_links_their_own_batch_to_their_own_slot() -> None:
    service, repo = _service()

    _assign(service, "b_a", "slot_a")

    assert repo.edges == [("b_a", "slot_a")]


@pytest.mark.parametrize(
    ("batch", "slot"),
    [("b_b", "slot_a"), ("b_a", "slot_b"), ("b_b", "slot_b"), ("b_a", "no-such-slot"), ("no-such-batch", "slot_a")],
    ids=["foreign-batch", "foreign-slot", "both-foreign", "unknown-slot", "unknown-batch"],
)
def test_a_foreign_or_unknown_key_answers_404_and_writes_nothing(batch: str, slot: str) -> None:
    service, repo = _service()

    with pytest.raises(NotFoundError):
        _assign(service, batch, slot)

    assert repo.edges == []


def test_a_viewer_may_not_link() -> None:
    service, repo = _service()

    with pytest.raises(ForbiddenError):
        _assign(service, "b_a", "slot_a", role=TenantRole.VIEWER)

    assert repo.edges == []


def test_a_foreign_key_is_refused_before_the_role_gate() -> None:
    # 404 for a foreign key even for a viewer: the role answer must not confirm
    # that the key exists in another tenant.
    service, _ = _service()

    with pytest.raises(NotFoundError):
        _assign(service, "b_b", "slot_a", role=TenantRole.VIEWER)


def test_without_slot_anchors_the_service_refuses_rather_than_skipping_the_slot_check() -> None:
    repo = _SubstrateRepo()
    service = SubstrateService(repo)  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        service.assign_batch_to_slot(
            "b_a", "slot_a", tenant_key="t_a", caller_role=TenantRole.GROWER, is_platform_admin=False
        )

    assert repo.edges == []


def test_the_tenant_is_keyword_only_without_a_default() -> None:
    import inspect

    param = inspect.signature(SubstrateService.assign_batch_to_slot).parameters["tenant_key"]

    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
