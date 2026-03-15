from unittest.mock import MagicMock

import pytest

from app.common.enums import ActivityCategory, StressLevel
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.activity import Activity
from app.domain.services.activity_service import ActivityService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return ActivityService(mock_repo)


def _make_activity(**kwargs) -> Activity:
    defaults = {"_key": "abc123", "name": "Topping", "category": "training_hst"}
    defaults.update(kwargs)
    return Activity(**defaults)


class TestActivityService:
    def test_list_activities(self, service, mock_repo):
        activities = [_make_activity()]
        mock_repo.get_all.return_value = (activities, 1)
        items, total = service.list_activities()
        assert total == 1
        assert len(items) == 1
        mock_repo.get_all.assert_called_once_with(0, 50, None)

    def test_list_with_category_filter(self, service, mock_repo):
        mock_repo.get_all.return_value = ([], 0)
        service.list_activities(filters={"category": "pruning"})
        mock_repo.get_all.assert_called_once_with(0, 50, {"category": "pruning"})

    def test_get_activity(self, service, mock_repo):
        activity = _make_activity()
        mock_repo.get_by_key.return_value = activity
        result = service.get_activity("abc123")
        assert result.name == "Topping"

    def test_get_activity_not_found(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None
        with pytest.raises(NotFoundError):
            service.get_activity("nonexistent")

    def test_create_activity(self, service, mock_repo):
        activity = _make_activity()
        mock_repo.create.return_value = activity
        result = service.create_activity(activity)
        assert result.name == "Topping"

    def test_update_activity(self, service, mock_repo):
        existing = _make_activity()
        updated = _make_activity(name="Updated Topping")
        mock_repo.get_by_key.return_value = existing
        mock_repo.update.return_value = updated
        result = service.update_activity("abc123", {"name": "Updated Topping"})
        assert result.name == "Updated Topping"

    def test_update_ignores_unknown_fields(self, service, mock_repo):
        existing = _make_activity()
        mock_repo.get_by_key.return_value = existing
        mock_repo.update.return_value = existing
        service.update_activity("abc123", {"unknown_field": "value"})
        # Should not raise — unknown fields are silently ignored

    def test_delete_activity(self, service, mock_repo):
        activity = _make_activity(is_system=False)
        mock_repo.get_by_key.return_value = activity
        mock_repo.delete.return_value = True
        result = service.delete_activity("abc123")
        assert result is True

    def test_delete_system_activity_forbidden(self, service, mock_repo):
        activity = _make_activity(is_system=True)
        mock_repo.get_by_key.return_value = activity
        with pytest.raises(ForbiddenError, match="System activities"):
            service.delete_activity("abc123")

    def test_get_system_activities(self, service, mock_repo):
        activities = [_make_activity(is_system=True)]
        mock_repo.get_system_activities.return_value = activities
        result = service.get_system_activities()
        assert len(result) == 1
        assert result[0].is_system is True

    def test_get_by_category(self, service, mock_repo):
        activities = [_make_activity(category=ActivityCategory.PRUNING)]
        mock_repo.get_by_category.return_value = activities
        result = service.get_by_category("pruning")
        assert len(result) == 1
