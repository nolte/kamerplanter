from fastapi import APIRouter, Depends

from app.api.v1.user_preferences.schemas import UserPreferenceResponse, UserPreferenceUpdate
from app.common.auth import get_current_user
from app.common.dependencies import get_user_preference_service
from app.domain.models.user import User
from app.domain.services.user_preference_service import UserPreferenceService

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])


@router.get("", response_model=UserPreferenceResponse)
def get_preferences(
    user: User = Depends(get_current_user),
    service: UserPreferenceService = Depends(get_user_preference_service),
):
    pref = service.get_preferences(user.key)
    return UserPreferenceResponse(key=pref.key or "", **pref.model_dump(exclude={"key"}))


@router.patch("", response_model=UserPreferenceResponse)
def update_preferences(
    body: UserPreferenceUpdate,
    user: User = Depends(get_current_user),
    service: UserPreferenceService = Depends(get_user_preference_service),
):
    updates = body.model_dump(exclude_none=True)
    pref = service.update_preferences(user.key, updates)
    return UserPreferenceResponse(key=pref.key or "", **pref.model_dump(exclude={"key"}))
