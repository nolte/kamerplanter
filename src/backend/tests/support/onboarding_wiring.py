"""Build the onboarding services from one database handle, as the app does (#1638).

``OnboardingService`` and ``StarterKitService`` no longer take a
``StandardDatabase``; their collaborators are injected by
``app.common.dependencies``. Tests that hold a single handle — a live ArangoDB in
the integration tier, a ``MagicMock`` in the unit tier — build the same graph
here instead of repeating it at every call site, so the wiring the tests exercise
cannot drift from the wiring production uses.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango.favorites_repository import ArangoFavoritesRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.onboarding_state_repository import ArangoOnboardingStateRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.starter_kit_repository import ArangoStarterKitRepository
from app.domain.services.favorites_service import FavoritesService
from app.domain.services.onboarding_service import OnboardingService
from app.domain.services.starter_kit_service import StarterKitService
from app.domain.services.user_preference_service import UserPreferenceService


def build_favorites_service(db: Any) -> FavoritesService:
    """``FavoritesService`` over the real repositories on ``db``."""
    return FavoritesService(ArangoFavoritesRepository(db), ArangoNutrientPlanRepository(db))


def build_starter_kit_service(db: Any) -> StarterKitService:
    """``StarterKitService`` over the real repositories on ``db``."""
    return StarterKitService(ArangoStarterKitRepository(db), ArangoSpeciesRepository(db))


def build_onboarding_service(db: Any) -> OnboardingService:
    """``OnboardingService`` wired the way ``get_onboarding_service`` wires it."""
    return OnboardingService(
        ArangoOnboardingStateRepository(db),
        build_starter_kit_service(db),
        favorites_service=build_favorites_service(db),
        user_preference_service=UserPreferenceService(db),
    )
