"""REQ-016 InvenTree adapter scaffold tests."""

import pytest

from app.data_access.external.inventree_adapter import InvenTreeAdapter


def _adapter() -> InvenTreeAdapter:
    return InvenTreeAdapter(base_url="https://inventree.test/api/", api_token="x")


@pytest.mark.asyncio
class TestInvenTreeAdapterScaffold:
    async def test_list_stock_raises_until_follow_up(self):
        with pytest.raises(NotImplementedError, match="pending"):
            await _adapter().list_stock_for_part(1)

    async def test_reserve_raises_until_follow_up(self):
        with pytest.raises(NotImplementedError, match="pending"):
            await _adapter().reserve_part(1, 0.5)

    async def test_health_check_reports_scaffold_state(self):
        result = await _adapter().health_check()
        assert result["backend"] == "inventree"
        assert result["base_url"] == "https://inventree.test/api"
        assert result["ready"] is False
