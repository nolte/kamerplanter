"""The closed vocabulary ``details[0].entity`` draws from (NFR-006 §2.2a, #1465).

``NotFoundError`` has carried a machine-readable ``details[0].entity`` since
#1437, normalised through :func:`~app.common.exceptions.normalise_entity_name`.
Normalising folds spelling, not *meaning*: ``"tenants"`` and ``"Tenant"`` are two
published values for one model, and ``"LifecycleConfig for species"`` or a bare
collection name are values no client can branch on at all. Measured over ``app/``
before this module existed: 146 literal raiser sites spelling **59** distinct
names, plus 17 sites passing a run-time *collection* name.

**The rule, stated once.** A published entity name is the name of a domain model
class under ``app.domain.models``, folded to ``snake_case`` by
:func:`normalise_entity_name` — plus the nine names in
:data:`NON_MODEL_ENTITY_NAMES`, which are not models and say why.

**Why it is discovered rather than listed.** A hand-kept list would be the 60th
copy of a fact the model classes already hold, and it would drift exactly as the
59 spellings did — silently, because nothing would compare the two. Discovery
also keeps the *derivation* sites honest: ``BaseArangoRepository`` publishes the
name of whatever model a repository binds (109 of them today), so any list short
of "every model" would have been a vocabulary the code already violated.

**The raisers keep writing an English class name** (``NotFoundError(
"PlantInstance", key)``), because that first argument is also the human-readable
``message``. What is pinned is that ``normalise_entity_name(<that literal>)``
lands in :func:`entity_names` — enforced over every raiser site, every entity
-name parameter, every ``_entity_name`` class attribute and every
``NotFoundError`` subclass by ``tests/unit/guards/test_entity_name_vocabulary.py``.

Nothing in the request path needs the whole set: production derives a single name
through :func:`entity_name` or the collection table in
``app.data_access.arango.entity_names``. :func:`entity_names` therefore walks the
model package lazily, and caches.
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import lru_cache
from typing import Final

from pydantic import BaseModel

from app.common.exceptions import normalise_entity_name

#: The names that are **not** a domain model, each with the reason it cannot be
#: one. The only hand-written entity names in the codebase, and every entry has
#: to earn it: a name that *could* be derived from a model must be, or the two
#: spellings drift apart the way ``"tenants"`` and ``"Tenant"`` did.
NON_MODEL_ENTITY_NAMES: Final[dict[str, str]] = {
    "favorite_target": (
        "A favourite's target key that resolves to no catalogue at all "
        "(FavoritesService). There is no model to name precisely because the "
        "lookup failed; SEC-002 requires an unresolvable and a foreign-tenant "
        "key to answer identically."
    ),
    "inven_tree_part": (
        "A part in the remote InvenTree instance (REQ-016). It is not persisted "
        "here, so no local model carries the name; folded like its sibling "
        "models InvenTreeConnection / InvenTreeReference so the product name "
        "reads the same way in all three."
    ),
    "mcp_server": (
        "The MCP endpoint itself answering 404 while the feature is disabled "
        "(REQ-033). Not a document — the missing thing is the surface."
    ),
    "mcp_tool": (
        "A tool name the MCP dispatcher does not know (REQ-033). ``McpToolSpec`` "
        "is the description of a *registered* tool, not the tool the caller "
        "asked for, so naming the model would publish an inaccurate value."
    ),
    "plant_photo": (
        "An ``Attachment`` in the plant-gallery category (NFR-013). Deliberately "
        "distinct from ``attachment``: #1437 made ``attachment`` the value that "
        "de-stages a *task* photo in the client, and a gallery photo must not "
        "trigger that branch."
    ),
    "reference_image": (
        "A species reference-image record in the admin surface. The models in "
        "``reference_image.py`` describe the acquisition *job* and its "
        "candidates, not the stored image."
    ),
    "resource": (
        "The fail-closed fallback when a run-time collection maps to no model "
        "(``app.data_access.arango.entity_names``). Deliberately uninformative: "
        "echoing the collection name would publish storage detail and, on a "
        "caller-supplied collection, reflect caller input."
    ),
    "session": (
        "A login session as ``GET /auth/sessions`` presents it. Stored as a "
        "``RefreshToken`` row — the mechanism, not the thing the caller asked "
        "about — and read back as the ``SessionInfo`` projection."
    ),
    "storage_object": (
        "A blob in the object store (S3 / local-filesystem adapter). Below the "
        "document layer: it has a key in a bucket, not a model."
    ),
}

_MODELS_PACKAGE: Final[str] = "app.domain.models"


def entity_name(model_cls: type[BaseModel]) -> str:
    """The published ``details[0].entity`` value for ``model_cls``.

    The one function that turns a model into its entity name, so a derivation
    site and the vocabulary can never disagree on the folding.
    """
    return normalise_entity_name(model_cls.__name__)


@lru_cache(maxsize=1)
def domain_model_classes() -> frozenset[type[BaseModel]]:
    """Every Pydantic model declared under ``app.domain.models``.

    Declared *there*, not merely imported there: a model is attributed to the
    module that defines it, so a re-export cannot enter the vocabulary twice
    under two module paths.
    """
    package = importlib.import_module(_MODELS_PACKAGE)
    found: set[type[BaseModel]] = set()
    for module_info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{_MODELS_PACKAGE}.{module_info.name}")
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == module.__name__:
                found.add(value)
    return frozenset(found)


@lru_cache(maxsize=1)
def entity_names() -> frozenset[str]:
    """The closed vocabulary: one snake_case name per model, plus the exceptions."""
    return frozenset(entity_name(model) for model in domain_model_classes()) | frozenset(NON_MODEL_ENTITY_NAMES)
