"""Collection → published entity name, for the raisers that only hold a collection (#1465).

A handful of guards are generic over the collection they verify — the declarative
reference check (``BaseArangoRepository._owned_reference_fields``), the shared
ownership guard, the InvenTree link guard, the favourites target resolver, the
task entity binding. Before this module they passed the *collection* name into
:class:`~app.common.exceptions.NotFoundError`, so ``details[0].entity`` came back
as ``"plant_instances"`` / ``"cultivars"`` — a plural storage name, next to
``"plant_instance"`` from the model-bound raiser for the very same thing.

Two reasons this maps to a **model class** rather than depluralising the
collection name: a rule that strips an ``s`` is a second, weaker copy of the
naming decision (``equipment``, ``species`` have no plural form to strip), and
several of these collections are named by the *caller* (``entity_collection``
arrives in a request body), so the value must come from a fixed table rather than
from caller input.

Unmapped collections fold to :data:`FALLBACK_ENTITY_NAME` rather than raising:
turning a 404 into a 500 because a collection is new is the worse failure, and
echoing the collection name is what this module exists to stop. The guard test
pins the table against the collections these sites can actually reach.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel

from app.data_access.arango import collections as col
from app.domain.entity_names import entity_name
from app.domain.models.activity import Activity
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.harvest import HarvestObservation
from app.domain.models.inventree import Equipment
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.site import Location
from app.domain.models.species import Cultivar, Species
from app.domain.models.substrate import Substrate
from app.domain.models.tank import Tank

#: What a collection with no model in the table publishes. In the vocabulary
#: (``NON_MODEL_ENTITY_NAMES["resource"]``) and deliberately uninformative.
FALLBACK_ENTITY_NAME: Final[str] = "resource"

#: Every collection one of the collection-generic 404 raisers can reach.
COLLECTION_ENTITY_MODELS: Final[dict[str, type[BaseModel]]] = {
    col.ACTIVITIES: Activity,
    col.BOTANICAL_FAMILIES: BotanicalFamily,
    col.CULTIVARS: Cultivar,
    col.EQUIPMENT: Equipment,
    col.FERTILIZERS: Fertilizer,
    col.HARVEST_OBSERVATIONS: HarvestObservation,
    col.LOCATIONS: Location,
    col.NUTRIENT_PLANS: NutrientPlan,
    col.PLANT_INSTANCES: PlantInstance,
    col.PLANTING_RUNS: PlantingRun,
    col.SPECIES: Species,
    col.SUBSTRATES: Substrate,
    col.TANKS: Tank,
}


def entity_name_for_collection(collection: str) -> str:
    """The published entity name for ``collection``, or the fail-closed fallback.

    Never returns ``collection`` itself — see the module docstring for why a
    caller-supplied collection name must not reach the wire.
    """
    model = COLLECTION_ENTITY_MODELS.get(collection)
    return entity_name(model) if model is not None else FALLBACK_ENTITY_NAME
