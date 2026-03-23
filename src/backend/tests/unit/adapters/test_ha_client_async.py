"""Tests for async methods on HomeAssistantClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.data_access.external.ha_client import HomeAssistantClient


@pytest.fixture
def client():
    return HomeAssistantClient("http://ha.local:8123", "test-token", timeout=5)


class TestFireEvent:
    @pytest.mark.asyncio
    async def test_fire_event_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": "Event fired."}
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.ha_client.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.post.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            result = await client.fire_event(
                "kamerplanter_care", {"plant": "tomato"},
            )

            assert result == {"message": "Event fired."}
            mock_ac.post.assert_called_once_with(
                "http://ha.local:8123/api/events/kamerplanter_care",
                json={"plant": "tomato"},
                headers={"Authorization": "Bearer test-token"},
            )

    @pytest.mark.asyncio
    async def test_fire_event_raises_on_error(self, client):
        with patch("app.data_access.external.ha_client.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )
            mock_ac.post.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            with pytest.raises(httpx.HTTPStatusError):
                await client.fire_event("test", {})


class TestCreatePersistentNotification:
    @pytest.mark.asyncio
    async def test_success(self, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.ha_client.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.post.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            await client.create_persistent_notification(
                title="Test", message="Hello", notification_id="n123",
            )

            mock_ac.post.assert_called_once_with(
                "http://ha.local:8123/api/services/persistent_notification/create",
                json={
                    "title": "Test",
                    "message": "Hello",
                    "notification_id": "n123",
                },
                headers={"Authorization": "Bearer test-token"},
            )


class TestDismissPersistentNotification:
    @pytest.mark.asyncio
    async def test_success(self, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.ha_client.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.post.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            await client.dismiss_persistent_notification("n123")

            mock_ac.post.assert_called_once_with(
                "http://ha.local:8123/api/services/persistent_notification/dismiss",
                json={"notification_id": "n123"},
                headers={"Authorization": "Bearer test-token"},
            )


class TestCallService:
    @pytest.mark.asyncio
    async def test_call_service_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"entity_id": "light.kitchen"}]
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.ha_client.httpx.AsyncClient") as mock_cls:
            mock_ac = AsyncMock()
            mock_ac.post.return_value = mock_resp
            mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
            mock_ac.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_ac

            result = await client.call_service(
                "notify", "mobile_app", {"message": "hi"},
            )

            assert result == [{"entity_id": "light.kitchen"}]
            mock_ac.post.assert_called_once_with(
                "http://ha.local:8123/api/services/notify/mobile_app",
                json={"message": "hi"},
                headers={"Authorization": "Bearer test-token"},
            )
