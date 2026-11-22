"""#2862 SEC-001/SEC-002 — the slot writes of sowing, thinning and clearing anchor the tenant in the query itself.

A slot carries no ``tenant_key`` (E-01): the service resolves the slot through its bed and site first
(``resolve_owned_slot``), and the write repeats that anchor so a foreign slot is never written even when the service
check is bypassed - the update then touches zero rows and the caller answers 409 as for any other changed slot. The
thinning also re-reads the run before its first write: still the tenant's, still live.

The transactions run with ``allow_implicit=False``, so ``sites`` must be declared where the anchor reads it. The
behaviour against a real database (a foreign tenant's slot stays untouched) is proven in
``tests/integration/test_slot_thinning_flow.py``.
"""

from __future__ import annotations

import inspect
import re

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango import planting_reservation_repository as repo

#: The anchor: the slot's bed, its site, and the site's tenant compared with the bound tenant.
_ANCHOR = re.compile(
    r"LET location = DOCUMENT\(@@locations, s\.location_key\)\s+"
    r"LET site = location == null \? null : DOCUMENT\(@@sites, location\.site_key\)\s+"
    r"FILTER site != null AND site\.tenant_key == @tenant_key"
)


@pytest.mark.parametrize("name", ["_MARK_SLOT_SOWN", "_CLEAR_SOWN_SLOT", "_MARK_ZONE_STAND"])
def test_every_slot_write_anchors_the_slot_on_the_tenants_site(name: str) -> None:
    query = getattr(repo, name)
    anchor = _ANCHOR.search(query)
    assert anchor is not None, f"{name} writes a slot without anchoring it on the tenant's site"
    # The anchor filters before the update, not after it.
    assert anchor.start() < query.index("UPDATE s WITH")


def test_the_stand_slots_clearing_takes_are_anchored_too() -> None:

    source = inspect.getsource(repo.ArangoPlantingReservationRepository.clear_bed)
    assert "s.thinned_at != null" in source
    assert "FILTER site != null AND site.tenant_key == @tenant_key" in source


def test_the_held_reservation_is_read_through_a_live_run_of_the_tenant() -> None:
    query = repo._RESERVATION_STILL_HELD
    run_check = query.index("FILTER run != null AND run.tenant_key == @tenant_key AND run.status IN @live")
    assert run_check < query.index("FOR e IN @@edges")


@pytest.mark.parametrize("reads", [repo._THIN_READ, repo._SOW_READ, repo._CLEAR_READ, repo._RESERVATION_READ])
def test_the_transactions_declare_the_site_they_anchor_on(reads: tuple[str, ...]) -> None:
    assert col.SITES in reads
