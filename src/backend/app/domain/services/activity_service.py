from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.common.types import ActivityKey
from app.domain.interfaces.activity_repository import IActivityRepository
from app.domain.models.activity import Activity


class ActivityService:
    def __init__(self, repo: IActivityRepository) -> None:
        self._repo = repo

    def list_activities(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[Activity], int]:
        return self._repo.get_all(offset, limit, filters)

    def get_activity(self, key: ActivityKey) -> Activity:
        activity = self._repo.get_by_key(key)
        if activity is None:
            raise NotFoundError("Activity", key)
        return activity

    def create_activity(self, activity: Activity) -> Activity:
        return self._repo.create(activity)

    def update_activity(self, key: ActivityKey, data: dict) -> Activity:
        existing = self.get_activity(key)
        allowed_fields = {
            "name",
            "name_de",
            "description",
            "description_de",
            "category",
            "stress_level",
            "skill_level",
            "recovery_days_default",
            "recovery_days_by_species",
            "forbidden_phases",
            "restricted_sub_phases",
            "tools_required",
            "estimated_duration_minutes",
            "requires_photo",
            "species_compatible",
            "sort_order",
            "tags",
        }
        merged = existing.model_dump()
        for field, value in data.items():
            if field in allowed_fields:
                merged[field] = value
        try:
            validated = Activity.model_validate(merged)
        except PydanticValidationError as exc:
            raise ValidationError(
                message=str(exc.errors()[0]["msg"]),
                details=[
                    {"field": ".".join(str(loc) for loc in e["loc"]), "reason": e["msg"], "code": e["type"]}
                    for e in exc.errors()
                ],
            ) from exc
        return self._repo.update(key, validated)

    def delete_activity(self, key: ActivityKey) -> bool:
        activity = self.get_activity(key)
        if activity.is_system:
            raise ForbiddenError("System activities cannot be deleted.")
        return self._repo.delete(key)

    def get_system_activities(self) -> list[Activity]:
        return self._repo.get_system_activities()

    def get_by_category(self, category: str) -> list[Activity]:
        return self._repo.get_by_category(category)
