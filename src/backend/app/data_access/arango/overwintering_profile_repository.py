from arango.database import StandardDatabase

from app.common.types import OverwinteringProfileKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile


class ArangoOverwinteringProfileRepository(BaseArangoRepository[OverwinteringProfile], IOverwinteringProfileRepository):
    """REQ-022 §OverwinteringProfile — ArangoDB repository (G-002)."""

    _model_cls = OverwinteringProfile
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.OVERWINTERING_PROFILES)

    # ── Reads ──────────────────────────────────────────────────────────

    def get_profile_by_key(self, key: OverwinteringProfileKey) -> OverwinteringProfile | None:
        return super().get_by_key(key)

    def get_profile_by_plant_key(self, plant_key: str) -> OverwinteringProfile | None:
        return self.find_one_by_field("plant_key", plant_key)

    def get_profile_by_run_key(self, run_key: str) -> OverwinteringProfile | None:
        return self.find_one_by_field("planting_run_key", run_key)

    def list_by_tenant(
        self, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[OverwinteringProfile], int]:
        return super().get_all(offset, limit, tenant_key=tenant_key)

    # ── Writes ─────────────────────────────────────────────────────────

    def create_profile(self, profile: OverwinteringProfile) -> OverwinteringProfile:
        return super().create(profile)

    def update_profile(self, key: OverwinteringProfileKey, profile: OverwinteringProfile) -> OverwinteringProfile:
        return super().update(key, profile)

    def delete_profile(self, key: OverwinteringProfileKey) -> bool:
        return super().delete(key)

    # ── Edges ──────────────────────────────────────────────────────────

    def create_subject_edge(
        self,
        profile_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> None:
        """Link the profile to its subject (planting run primary, plant fallback)."""
        profile_id = f"{col.OVERWINTERING_PROFILES}/{profile_key}"
        if planting_run_key:
            from_id = f"{col.PLANTING_RUNS}/{planting_run_key}"
        elif plant_key:
            from_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        else:
            return
        self.create_edge(col.HAS_OVERWINTERING_PROFILE, from_id, profile_id)

    def create_winter_quarter_edge(self, profile_key: str, location_key: str) -> None:
        profile_id = f"{col.OVERWINTERING_PROFILES}/{profile_key}"
        location_id = f"{col.LOCATIONS}/{location_key}"
        self.create_edge(col.OVERWINTERS_AT, profile_id, location_id)
