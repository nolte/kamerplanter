from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.exceptions import ValidationError
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.engines.onboarding_engine import OnboardingEngine
from app.domain.models.onboarding import OnboardingState

if TYPE_CHECKING:
    from app.domain.services.starter_kit_service import StarterKitService


class OnboardingService:
    def __init__(self, db, starter_kit_service: StarterKitService) -> None:
        from app.data_access.arango import collections as col
        self._repo = BaseArangoRepository(db, col.ONBOARDING_STATES)
        self._db = db
        self._kit_service = starter_kit_service
        self._engine = OnboardingEngine()

    def get_state(self, user_key: str) -> OnboardingState:
        docs = self._repo.find_by_field("user_key", user_key)
        if docs:
            return OnboardingState(**docs[0])
        # Auto-create initial state
        state = OnboardingState(user_key=user_key)
        doc = self._repo.create(state)
        return OnboardingState(**doc)

    def save_progress(self, user_key: str, wizard_step: int, **kwargs) -> OnboardingState:
        state = self.get_state(user_key)
        data = state.model_dump()
        data["wizard_step"] = wizard_step
        data.update(kwargs)
        updated = OnboardingState(**data)
        doc = self._repo.update(state.key or "", updated)
        return OnboardingState(**doc)

    def complete_wizard(
        self,
        user_key: str,
        kit_id: str | None = None,
        experience_level: str | None = None,
        site_name: str = "",
        plant_count: int = 3,
        has_ro_system: bool | None = None,
        tap_water_ec_ms: float | None = None,
        tap_water_ph: float | None = None,
    ) -> dict:
        """Complete the onboarding wizard, optionally applying a starter kit."""
        state = self.get_state(user_key)
        created_entities: dict[str, list[str]] = {}

        if kit_id:
            kit = self._kit_service.get_kit_by_id(kit_id)
            errors = self._engine.validate_kit_application(kit, site_name, plant_count)
            if errors:
                raise ValidationError("Invalid kit application", [
                    {"field": "kit", "reason": e, "code": "VALIDATION_ERROR"} for e in errors
                ])
            entity_plan = self._engine.build_entity_plan(
                kit, site_name, plant_count,
                has_ro_system=has_ro_system,
                tap_water_ec_ms=tap_water_ec_ms,
                tap_water_ph=tap_water_ph,
            )
            created_entities["plan"] = [str(entity_plan)]

        state_data = state.model_dump()
        state_data.update({
            "completed": True,
            "completed_at": datetime.now(UTC).isoformat(),
            "selected_kit_id": kit_id,
            "selected_experience_level": experience_level,
            "wizard_step": 5,
            "created_entities": created_entities,
        })
        updated = OnboardingState(**state_data)
        self._repo.update(state.key or "", updated)

        return {
            "status": "completed",
            "created_entities": created_entities,
        }

    def skip_wizard(self, user_key: str) -> OnboardingState:
        state = self.get_state(user_key)
        data = state.model_dump()
        data["skipped"] = True
        data["completed_at"] = datetime.now(UTC).isoformat()
        updated = OnboardingState(**data)
        doc = self._repo.update(state.key or "", updated)
        return OnboardingState(**doc)
