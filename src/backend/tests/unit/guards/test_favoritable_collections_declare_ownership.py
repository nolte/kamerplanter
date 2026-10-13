"""Every favouritable catalogue that *has* a ``tenant_key`` must be guarded (#1538).

This is the guard on the failure the issue actually uncovered, and it is not the
one the issue described. The resolver was tenant-blind by construction, yes — but
the **measurable** cross-tenant write came from a hand-maintained set drifting
away from the models: ``Species.tenant_key`` arrived with #808 (REQ-001 v4.0),
``_TENANT_OWNED_CATALOG_COLLECTIONS`` was written for #965 before that, and the
comment above it went on asserting "species carry no ``tenant_key``" for as long
as nothing re-read the model. Nothing did.

So the guard asks the **model**, not a comment: for each favouritable collection,
does its Pydantic model declare a ``tenant_key`` field? If yes it must be in the
guarded set; if no it must not be (an unnecessary entry would read every row's
absent field and, worse, suggest a protection that has nothing to protect).

Adding a collection to ``_FAVOURITABLE_COLLECTIONS`` without adding it here fails
too: the mapping below is required to be total over that tuple, so the new target
cannot slip in unclassified.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.data_access.arango import collections as col
from app.domain.models.activity import Activity
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.species import Species
from app.domain.models.substrate import Substrate
from app.domain.services.favorites_service import (
    _FAVOURITABLE_COLLECTIONS,
    _TENANT_OWNED_CATALOG_COLLECTIONS,
)

#: The model persisted in each favouritable collection.
_MODEL_BY_COLLECTION: dict[str, type[BaseModel]] = {
    col.SPECIES: Species,
    col.NUTRIENT_PLANS: NutrientPlan,
    col.FERTILIZERS: Fertilizer,
    col.ACTIVITIES: Activity,
    col.BOTANICAL_FAMILIES: BotanicalFamily,
    col.SUBSTRATES: Substrate,
}


def test_every_favouritable_collection_is_classified() -> None:
    """A new favourite target cannot enter unclassified."""
    assert set(_FAVOURITABLE_COLLECTIONS) == set(_MODEL_BY_COLLECTION)


def test_a_collection_whose_model_owns_a_tenant_key_is_guarded() -> None:
    declares_ownership = {
        collection for collection, model in _MODEL_BY_COLLECTION.items() if "tenant_key" in model.model_fields
    }

    assert declares_ownership == set(_TENANT_OWNED_CATALOG_COLLECTIONS), (
        "The favourites tenant predicate is derived from the models: a catalogue whose model "
        "declares tenant_key must be in _TENANT_OWNED_CATALOG_COLLECTIONS, and one that does not "
        "must stay out. This drifted once already (#808 gave Species a tenant_key, #965's set was "
        "never revisited, and a foreign tenant's species stayed favouritable until #1538)."
    )


def test_species_is_guarded_by_name() -> None:
    """The specific regression, named, so the guard cannot go vacuous.

    ``test_a_collection_whose_model_owns_a_tenant_key_is_guarded`` compares two
    sets built from the same source. If ``_MODEL_BY_COLLECTION`` ever lost its
    species entry, both sides would shrink together and the comparison would stay
    green while the hole reopened.
    """
    assert "tenant_key" in Species.model_fields
    assert col.SPECIES in _TENANT_OWNED_CATALOG_COLLECTIONS


def test_botanical_families_stay_unguarded() -> None:
    """The counterweight: the one catalogue with no ownership field at all.

    Guarding it would hide the whole seeded family catalogue behind a field no
    row carries — the #324 regression in its purest form.
    """
    assert "tenant_key" not in BotanicalFamily.model_fields
    assert col.BOTANICAL_FAMILIES not in _TENANT_OWNED_CATALOG_COLLECTIONS
