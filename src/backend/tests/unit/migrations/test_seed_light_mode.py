from unittest.mock import MagicMock, patch

from app.migrations.seed_light_mode import run_seed_light_mode


class TestSeedLightMode:
    @patch("app.migrations.seed_light_mode.load_yaml")
    @patch("app.migrations.seed_light_mode.get_connection")
    def test_creates_system_user_and_tenant(self, mock_get_conn, mock_load_yaml):
        mock_load_yaml.return_value = {
            "system_user": {
                "key": "light-system-user",
                "email": "system@kamerplanter.example",
                "display_name": "Gaertner",
            },
            "system_tenant": {
                "key": "light-system-tenant",
                "name": "Mein Garten",
                "slug": "mein-garten",
            },
        }

        users_col = MagicMock()
        tenants_col = MagicMock()
        memberships_col = MagicMock()

        users_col.has.return_value = False
        tenants_col.has.return_value = False
        memberships_col.has.return_value = False

        db = MagicMock()
        db.collection.side_effect = lambda name: {
            "users": users_col,
            "tenants": tenants_col,
            "memberships": memberships_col,
        }[name]
        mock_get_conn.return_value.db = db

        run_seed_light_mode()

        users_col.insert.assert_called_once()
        user_doc = users_col.insert.call_args[0][0]
        assert user_doc["email"] == "system@kamerplanter.example"
        assert user_doc["display_name"] == "Gaertner"
        assert user_doc["password_hash"] is None

        tenants_col.insert.assert_called_once()
        tenant_doc = tenants_col.insert.call_args[0][0]
        assert tenant_doc["name"] == "Mein Garten"
        assert tenant_doc["slug"] == "mein-garten"

        memberships_col.insert.assert_called_once()

    @patch("app.migrations.seed_light_mode.load_yaml")
    @patch("app.migrations.seed_light_mode.get_connection")
    def test_idempotent_second_call(self, mock_get_conn, mock_load_yaml):
        mock_load_yaml.return_value = {
            "system_user": {
                "key": "light-system-user",
                "email": "system@kamerplanter.example",
                "display_name": "Gaertner",
            },
            "system_tenant": {
                "key": "light-system-tenant",
                "name": "Mein Garten",
                "slug": "mein-garten",
            },
        }

        users_col = MagicMock()
        tenants_col = MagicMock()
        memberships_col = MagicMock()

        # System user already exists
        users_col.has.return_value = True

        db = MagicMock()
        db.collection.side_effect = lambda name: {
            "users": users_col,
            "tenants": tenants_col,
            "memberships": memberships_col,
        }[name]
        mock_get_conn.return_value.db = db

        run_seed_light_mode()

        users_col.insert.assert_not_called()
        tenants_col.insert.assert_not_called()
        memberships_col.insert.assert_not_called()
