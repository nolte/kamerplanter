"""#1035 — ``display_name`` must reject a whitespace-only value, not just an
empty one.

``min_length=1`` is length-based, so ``"   "`` passed the boundary and the model
and was persisted. The fix is the shared :data:`app.common.validators.DisplayName`
annotated type (reject-not-normalise), applied to the canonical ``User`` model and
to every request schema that mirrors the field. These tests drive the **real**
models, not a mock that never becomes a model (#996), so a green here is the
production validator firing.
"""

import pytest
from pydantic import ValidationError

from app.api.v1.admin.platform.schemas import AdminUserUpdate
from app.api.v1.auth.schemas import RegisterRequest
from app.api.v1.users.schemas import ProfileUpdateRequest
from app.domain.models.user import User, UserProfileUpdate

BLANK_VALUES = ["", " ", "   ", "\t", "\n", " \t \n "]


class TestUserModelRejectsBlankDisplayName:
    def test_normal_name_is_accepted(self):
        user = User(email="alice@example.com", display_name="Alice Grower")
        assert user.display_name == "Alice Grower"

    def test_internal_spaces_are_preserved(self):
        """Reject-only: a name with internal spaces must be untouched."""
        user = User(email="bob@example.com", display_name="Bob Smith")
        assert user.display_name == "Bob Smith"

    def test_surrounding_spaces_are_preserved(self):
        """Reject-only, not normalise: ``"  Bob  "`` is a valid name and is
        stored verbatim (it is not empty after stripping)."""
        user = User(email="bob@example.com", display_name="  Bob  ")
        assert user.display_name == "  Bob  "

    @pytest.mark.parametrize("value", BLANK_VALUES)
    def test_blank_value_is_rejected(self, value: str):
        with pytest.raises(ValidationError) as exc_info:
            User(email="alice@example.com", display_name=value)
        assert "display_name" in str(exc_info.value)


class TestUserProfileUpdateRejectsBlankDisplayName:
    def test_none_is_accepted(self):
        """The self-service update leaves ``display_name`` optional."""
        update = UserProfileUpdate()
        assert update.display_name is None

    def test_normal_name_is_accepted(self):
        update = UserProfileUpdate(display_name="Renamed")
        assert update.display_name == "Renamed"

    @pytest.mark.parametrize("value", [" ", "   ", "\t"])
    def test_blank_value_is_rejected(self, value: str):
        with pytest.raises(ValidationError):
            UserProfileUpdate(display_name=value)


class TestRequestSchemasRejectBlankDisplayName:
    """The mirrored request schemas reject blanks at the FastAPI boundary too, so
    the direct-construction registration path returns 422 rather than a 500 from a
    raw ``pydantic.ValidationError`` escaping ``User(...)`` in the handler."""

    @pytest.mark.parametrize("value", [" ", "   ", "\t"])
    def test_register_request_rejects_blank(self, value: str):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@example.com", password="a" * 12, display_name=value)

    def test_register_request_accepts_normal_name(self):
        req = RegisterRequest(email="a@example.com", password="a" * 12, display_name="Alice")
        assert req.display_name == "Alice"

    @pytest.mark.parametrize("value", [" ", "   ", "\t"])
    def test_profile_update_request_rejects_blank(self, value: str):
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(display_name=value)

    @pytest.mark.parametrize("value", [" ", "   ", "\t"])
    def test_admin_user_update_rejects_blank(self, value: str):
        with pytest.raises(ValidationError):
            AdminUserUpdate(display_name=value)

    def test_admin_user_update_accepts_normal_name(self):
        assert AdminUserUpdate(display_name="Renamed").display_name == "Renamed"
