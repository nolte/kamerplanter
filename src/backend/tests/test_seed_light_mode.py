from unittest.mock import MagicMock, patch

from app.migrations.seed_light_mode import run_seed_light_mode


class TestSeedLightMode:
    @patch("app.migrations.seed_light_mode.get_membership_repo")
    @patch("app.migrations.seed_light_mode.get_tenant_repo")
    @patch("app.migrations.seed_light_mode.get_user_repo")
    def test_creates_system_user_and_tenant(self, mock_user_repo_fn, mock_tenant_repo_fn, mock_membership_repo_fn):
        user_repo = MagicMock()
        tenant_repo = MagicMock()
        membership_repo = MagicMock()
        mock_user_repo_fn.return_value = user_repo
        mock_tenant_repo_fn.return_value = tenant_repo
        mock_membership_repo_fn.return_value = membership_repo

        user_repo.get_by_key.return_value = None  # Not yet created

        run_seed_light_mode()

        user_repo.create.assert_called_once()
        created_user = user_repo.create.call_args[0][0]
        assert created_user.email == "system@kamerplanter.example"
        assert created_user.display_name == "Gaertner"
        assert created_user.password_hash is None

        tenant_repo.create.assert_called_once()
        created_tenant = tenant_repo.create.call_args[0][0]
        assert created_tenant.name == "Mein Garten"
        assert created_tenant.slug == "mein-garten"

        membership_repo.create.assert_called_once()

    @patch("app.migrations.seed_light_mode.get_membership_repo")
    @patch("app.migrations.seed_light_mode.get_tenant_repo")
    @patch("app.migrations.seed_light_mode.get_user_repo")
    def test_idempotent_second_call(self, mock_user_repo_fn, mock_tenant_repo_fn, mock_membership_repo_fn):
        user_repo = MagicMock()
        tenant_repo = MagicMock()
        membership_repo = MagicMock()
        mock_user_repo_fn.return_value = user_repo
        mock_tenant_repo_fn.return_value = tenant_repo
        mock_membership_repo_fn.return_value = membership_repo

        # System user already exists
        existing_user = MagicMock()
        existing_user.key = "system-user"
        user_repo.get_by_key.return_value = existing_user

        run_seed_light_mode()

        user_repo.create.assert_not_called()
        tenant_repo.create.assert_not_called()
        membership_repo.create.assert_not_called()
