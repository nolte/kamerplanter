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
:data:`~app.data_access.arango.task_repository.TASK_ENTITY_TYPE_TO_COLLECTION`, the
same map the repository consults when deciding whether to write the edge at all.
So the verified set and the edge-writing set are the *same* set by construction,
rather than two lists that agree today. A binding with an unrecognised
``entity_type`` (``generic``, ``plant``, ``actuator`` all occur) writes no edge.
The system producers that mint such bindings (the actuator fallback task, seeds)
run without a tenant and pass through; a **tenant** caller that names a key under
such a type — or under none — is refused (#1872 C10): the key was stored
unresolved, a latent reference the next reader would trust.

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
* ``garden_object`` (REQ-053 §20.9, R-7.2) — like a location, carries no ``tenant_key`` (E-01); the site is the
  owner, which the garden-object read already joins. Only a ``compost``, ``water_source`` or ``storage`` object
  takes care tasks (:data:`TASK_GARDEN_OBJECT_TYPES`): any other class is a 422.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.common.enums import GardenObjectType
from app.common.exceptions import NotFoundError, ValidationError
from app.data_access.arango.collection_entity_names import entity_name_for_collection
from app.data_access.arango.task_repository import TASK_ENTITY_TYPE_TO_COLLECTION

#: The object classes a care task may hang off (REQ-053 R-7.2: turn the compost, winterise the barrel).
TASK_GARDEN_OBJECT_TYPES: frozenset[GardenObjectType] = frozenset(
    {GardenObjectType.COMPOST, GardenObjectType.WATER_SOURCE, GardenObjectType.STORAGE}
)


class TaskEntityGuard:
    """Resolves a task's entity binding under the caller's tenant, or raises 404.

    Collaborators arrive as **factories**, called only when a binding actually
    needs resolving. Most task creates are unbound or name a type that writes no
    edge, and eagerly constructing four services (each opening a database handle)
    to then do nothing is both wasteful and, in the API test tier, fatal: those
    tests must not reach a datastore (#978), and an unbound create would have
    tripped that guard for a lookup it never performs.
    """

    def __init__(
        self,
        plant_service: Callable[[], Any],
        planting_run_service: Callable[[], Any],
        tank_service: Callable[[], Any],
        site_service: Callable[[], Any],
        garden_object_service: Callable[[], Any] | None = None,
    ) -> None:
        self._plants = plant_service
        self._runs = planting_run_service
        self._tanks = tank_service
        self._sites = site_service
        self._garden_objects = garden_object_service

    def verify(self, entity_type: str | None, entity_key: str | None, *, tenant_key: str) -> None:
        """Raise :class:`NotFoundError` when the binding is not the caller's to make.

        A 404 rather than a 403, deliberately: a 403 would confirm that the key
        names a real entity in *some* tenant, which is the cross-tenant existence
        oracle the ownership-hiding rule exists to prevent. The underlying service
        reads already answer 404 for a foreign row, so this method mostly just lets
        them.

        No-ops when the task is unbound (no key) or when there is no tenant to
        anchor against (the system context: Celery care-reminder generation, the
        actuator fallback tasks and seeds, which mint their own bindings).

        A key under a type that writes no edge — or under no type at all — is
        refused for a tenant caller (#1872 C10): it used to be stored as given,
        a key nobody had resolved that the next reader keyed on it would trust.
        """
        if not tenant_key:
            return
        allowed = ", ".join(sorted(TASK_ENTITY_TYPE_TO_COLLECTION))
        # The service allowlist of REQ-053 §20.9 / K-5: ``Task.entity_type`` stays a free string, so the closed set
        # is enforced here for a tenant caller — with or without a key. A value outside it is a 422.
        if entity_type and entity_type not in TASK_ENTITY_TYPE_TO_COLLECTION:
            raise ValidationError(f"entity_type must be one of {allowed}.")
        if not entity_key:
            return
        if not entity_type:
            raise ValidationError(f"entity_key needs an entity_type of {allowed}.")

        if entity_type == "plant_instance":
            self._plants().get_plant(entity_key, tenant_key=tenant_key)
        elif entity_type == "planting_run":
            self._runs().get_run(entity_key, tenant_key=tenant_key)
        elif entity_type == "tank":
            self._tanks().get_tank(entity_key, tenant_key=tenant_key)
        elif entity_type == "location":
            # Two hops on purpose — see the module docstring: the location's own
            # tenant_key is never written, so the site is the only real anchor.
            # One step through the anchor (#1871 B13): the two-step form answered
            # a foreign location as "No Site <its site key>", an unknown one as
            # "No Location" — an oracle that echoed the other tenant's site.
            self._sites().get_location(entity_key, tenant_key=tenant_key)
        elif entity_type == "garden_object" and self._garden_objects is not None:
            garden_object = self._garden_objects().get_garden_object(entity_key, tenant_key=tenant_key)
            if garden_object.object_type not in TASK_GARDEN_OBJECT_TYPES:
                allowed = ", ".join(sorted(t.value for t in TASK_GARDEN_OBJECT_TYPES))
                raise ValidationError(f"A task can only hang off a garden object of class {allowed}.")
        else:
            # A type was added to TASK_ENTITY_TYPE_TO_COLLECTION without an anchor here.
            # Fail closed: the repository *will* write an edge for it, and nobody
            # has said whose entity it is. Not marked unreachable — it is one map
            # entry away, and a test drives it precisely so this stays honest.
            raise NotFoundError(entity_name_for_collection(TASK_ENTITY_TYPE_TO_COLLECTION[entity_type]), entity_key)
