"""Absence pin: the hybrid catalogues must never enter the default-tenant backfill.

Rationale (#1090 C-2, #324)
---------------------------
``backfill_tenant_key`` exists for genuinely tenant-scoped resources: it resolves
*one* default tenant (``_resolve_default_tenant``) and stamps it onto every
document that is missing a ``tenant_key``. That is correct for a site or a tank —
those always belonged to somebody — and catastrophic for the hybrid master-data
catalogues (``species``, ``cultivars``), where ``tenant_key == ""`` is a real,
final value meaning "global, visible to every tenant". Sweeping the catalogues
into the default-tenant stamp would hand the whole shared catalogue to one
arbitrary tenant and hide it from all others — exactly the #324 regression class
(a strict filter that made the global seeds disappear). Worse, phases 1 and 3 of
the backfill match ``tenant_key == null OR tenant_key == ""``, so they would also
re-own rows the cutover migrations ``v0036``/``v0038`` deliberately left global.

The cutover migrations state this policy in prose ("``SPECIES``/``CULTIVARS`` is
not, and must never be, in its ``TOP_LEVEL_COLLECTIONS``"). Prose does not fail a
build, and the list is an inviting place to "fix" a catalogue row that looks
un-owned. This module turns the statement into a gate: adding either collection to
any of the backfill's collection lists turns these tests red, and the reviewer is
pointed at the cutover docstrings instead of shipping the leak.

The pin is deliberately written against the module's *data*, not its behaviour —
the lists are the whole decision surface, and asserting on them keeps the test a
pure unit test that never touches a database.
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.migrations.backfill_tenant_key import (
    CHILD_PROPAGATION,
    SLOT_PROPAGATION,
    TOP_LEVEL_COLLECTIONS,
)

#: Hybrid master-data catalogues: rows may be global (``tenant_key == ""``) or
#: tenant-owned. Their cutover is owned by v0036 (species) / v0038 (cultivars).
HYBRID_CATALOG_COLLECTIONS = [col.SPECIES, col.CULTIVARS]


def _all_backfilled_collections() -> list[str]:
    """Every collection the backfill writes to, across all of its phases.

    Mirrors ``v0004_backfill_tenant_key._scoped_collections`` — phase 3 sweeps the
    union of the top-level list, the child-propagation children and the slot
    child, so an entry smuggled into *any* of them ends up default-stamped.
    """
    return [*TOP_LEVEL_COLLECTIONS, *(child for child, _, _ in CHILD_PROPAGATION), SLOT_PROPAGATION[0]]


@pytest.mark.parametrize("collection", HYBRID_CATALOG_COLLECTIONS)
def test_hybrid_catalog_is_not_a_top_level_backfill_collection(collection: str):
    assert collection not in TOP_LEVEL_COLLECTIONS, (
        f"{collection!r} must never be default-tenant-stamped: '' is a legitimate global value there. "
        "See app/migrations/versions/v0036_cutover_species_tenant_key.py / "
        "v0038_cutover_cultivar_tenant_key.py for the cutover policy (#324)."
    )


@pytest.mark.parametrize("collection", HYBRID_CATALOG_COLLECTIONS)
def test_hybrid_catalog_is_not_reachable_through_any_backfill_phase(collection: str):
    # Phase 2/2b would also work: a catalogue smuggled in as a propagation child
    # inherits its parent's tenant and is then swept by the phase-3 fallback.
    assert collection not in _all_backfilled_collections()


def test_pin_is_not_vacuous():
    # Guards the guard: if the lists were ever emptied or renamed away, the two
    # assertions above would pass for the wrong reason. A known genuinely
    # tenant-scoped collection must stay in scope of the backfill.
    assert col.SITES in TOP_LEVEL_COLLECTIONS
    assert col.SLOTS in _all_backfilled_collections()
