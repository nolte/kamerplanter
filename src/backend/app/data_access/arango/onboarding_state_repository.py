"""The ``onboarding_states`` collection (REQ-020), with full-replace null semantics."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository


class ArangoOnboardingStateRepository(BaseArangoRepository):
    """Persistence for the onboarding wizard's per-user singleton state (#1516).

    A class of its own rather than a bare ``BaseArangoRepository`` instance
    because :attr:`BaseArangoRepository._update_is_full_replace` is a ``ClassVar``:
    the null semantics belong to the collection, not to the call site that happens
    to want them.

    **What it repairs.** In the inherited merge mode a ``None`` never reached the
    store, so ``OnboardingService.reset_wizard`` — which nulls ``completed_at``,
    ``selected_kit_id``, ``selected_experience_level``, ``site_type``,
    ``selected_site_key`` and ``plant_count`` — left every one of them in place.
    The "reset" wizard reopened on the previous run's selections while reporting
    ``completed=False``; the list-valued fields it resets in the same dict
    (``plant_configs``, the two favourite lists) *did* land, because ``[]`` is not
    ``None``, which is why the reset looked like it worked. The same drop hit
    ``ensure_onboarding_state_for_user``'s ``completed_at: None`` on the
    light-to-full takeover path (REQ-027).

    **Every writer builds a full model from the stored state**, so none can lose a
    field it never mentioned (re-measured 2026-09-18 after #1515 split the read from
    the auto-create, over all five update call sites in ``OnboardingService`` — the
    only writer of this collection; the user repository's account cascade deletes
    rows, it does not update them): ``save_progress``, ``complete_wizard``,
    ``ensure_onboarding_state_for_user``, ``reset_wizard`` and ``skip_wizard`` each
    resolve the row through ``_materialise`` (which either returns the stored state
    or ``create``s the singleton), then start from ``state.model_dump()``, apply a
    literal ``dict.update`` and re-validate through ``OnboardingState``. The #1515
    split changed *when* the row appears, not the shape of the model handed to
    ``update``.

    Shaped like the package's other repositories (#1525 SCR-013): the collection name
    lives in ``__init__``, so no caller can point it elsewhere. The one deliberate
    difference is that it declares **no** ``_model_cls`` and no type parameter: raw
    mode is kept (FR-002 A3) because :class:`OnboardingService` wraps the returned
    ``dict`` into :class:`~app.domain.models.onboarding.OnboardingState` itself, and a
    binding here would annotate a return type the methods do not produce.
    """

    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ONBOARDING_STATES, raw=True)
