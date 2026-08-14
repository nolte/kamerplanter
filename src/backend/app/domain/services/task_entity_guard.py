"""Anchor a task's entity binding in the caller's tenant (SEC-I01, #1102).

``POST /t/{tenant_slug}/tasks`` stamps the new task with the caller's
``tenant_key`` but never checked that the caller-supplied
``entity_key``/``entity_type`` — the plant / planting-run / location / tank the
task hangs off — belongs to that tenant. The repository then built a ``has_task``
edge to whatever key arrived.

**What that is and is not.** It is not a cross-tenant read: the task carries the
caller's own tenant and every entity read stays scoped, so no foreign data was
disclosed. What it stored was an *unvalidated cross-boundary reference* plus a
graph edge pointing at a foreign document — the class the species and
task-template work anchored on the parent (foreign → 404), because the moment any
join, enrichment or export dereferences that edge, a latent reference becomes a
real cross-tenant path.

**Which types are checked, and why exactly those.** The set is taken from
:data:`~app.data_access.arango.task_repository.ENTITY_TYPE_TO_COLLECTION`, the
same map the repository consults when deciding whether to write the edge at all.
So the verified set and the edge-writing set are the *same* set by construction,
rather than two lists that agree today. A binding with an unrecognised
``entity_type`` (``generic``, ``plant``, ``actuator`` all occur) writes no edge
and dereferences to nothing, so there is nothing to anchor and it passes through
untouched — rejecting it would break producers over a reference that does not
exist.

**Each type is anchored where its tenancy actually lives**, which is not uniform:

* ``plant_instance``, ``planting_run``, ``tank`` — stamped with ``tenant_key`` at
  create, so their own service read is the anchor.
* ``location`` — **not** stamped. ``Location`` carries a ``tenant_key`` field, but
  no create path ever writes it (``Location(**body.model_dump())`` in the
  locations router), so it is ``""`` on every stored row. Tenancy is carried by
  the parent :class:`Site`, exactly as ``_verify_location_tenant`` in that router
  already does it. Anchoring on the field instead of the site would look like a
  security fix and would in fact 404 **every** location-bound task — an
  over-rejecting guard, which is the more expensive failure of the two.
"""

from __future__ import annotations

from typing import Any

from app.common.exceptions import NotFoundError
from app.data_access.arango.task_repository import ENTITY_TYPE_TO_COLLECTION


class TaskEntityGuard:
    """Resolves a task's entity binding under the caller's tenant, or raises 404."""

    def __init__(
        self,
        plant_service: Any,
        planting_run_service: Any,
        tank_service: Any,
        site_service: Any,
    ) -> None:
        self._plants = plant_service
        self._runs = planting_run_service
        self._tanks = tank_service
        self._sites = site_service

    def verify(self, entity_type: str | None, entity_key: str | None, *, tenant_key: str) -> None:
        """Raise :class:`NotFoundError` when the binding is not the caller's to make.

        A 404 rather than a 403, deliberately: a 403 would confirm that the key
        names a real entity in *some* tenant, which is the cross-tenant existence
        oracle the ownership-hiding rule exists to prevent. The underlying service
        reads already answer 404 for a foreign row, so this method mostly just lets
        them.

        No-ops when the task is unbound (no key or no type), when the type writes
        no edge, or when there is no tenant to anchor against (the system context:
        Celery care-reminder generation and seeds, which mint their own bindings).
        """
        if not entity_key or not entity_type or not tenant_key:
            return
        if entity_type not in ENTITY_TYPE_TO_COLLECTION:
            return

        if entity_type == "plant_instance":
            self._plants.get_plant(entity_key, tenant_key=tenant_key)
        elif entity_type == "planting_run":
            self._runs.get_run(entity_key, tenant_key=tenant_key)
        elif entity_type == "tank":
            self._tanks.get_tank(entity_key, tenant_key=tenant_key)
        elif entity_type == "location":
            # Two hops on purpose — see the module docstring: the location's own
            # tenant_key is never written, so the site is the only real anchor.
            location = self._sites.get_location(entity_key)
            self._sites.get_site(location.site_key, tenant_key=tenant_key)
        else:
            # A type was added to ENTITY_TYPE_TO_COLLECTION without an anchor here.
            # Fail closed: the repository *will* write an edge for it, and nobody
            # has said whose entity it is. Not marked unreachable — it is one map
            # entry away, and a test drives it precisely so this stays honest.
            raise NotFoundError(entity_type, entity_key)
