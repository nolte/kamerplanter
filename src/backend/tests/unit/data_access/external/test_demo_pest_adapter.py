"""REQ-044 — demo pest adapter: gating + placeholder findings."""

import pytest

from app.config.settings import settings
from app.data_access.external.demo_pest_adapter import DemoPestAdapter


@pytest.fixture
def adapter() -> DemoPestAdapter:
    return DemoPestAdapter()


class TestConfigured:
    def test_off_by_default(self, adapter, monkeypatch) -> None:
        monkeypatch.setattr(settings, "pest_detection_enabled", True)
        monkeypatch.setattr(settings, "pest_detection_demo_enabled", False)
        assert adapter.is_configured() is False

    def test_requires_feature_flag(self, adapter, monkeypatch) -> None:
        monkeypatch.setattr(settings, "pest_detection_enabled", False)
        monkeypatch.setattr(settings, "pest_detection_demo_enabled", True)
        assert adapter.is_configured() is False

    def test_configured_when_both_flags_on(self, adapter, monkeypatch) -> None:
        monkeypatch.setattr(settings, "pest_detection_enabled", True)
        monkeypatch.setattr(settings, "pest_detection_demo_enabled", True)
        assert adapter.is_configured() is True


class TestDetect:
    def test_returns_direct_and_symptom_findings(self, adapter) -> None:
        result = adapter.detect([b"tile1", b"tile2"])
        assert result.tiles_processed == 2
        assert result.disclaimer.strip()
        modes = {f.mode.value for f in result.findings}
        assert modes == {"direct", "symptom"}
        direct = next(f for f in result.findings if f.mode.value == "direct")
        assert direct.bounding_box is not None
        # never invents a beneficial as a pest — placeholders are real pest labels
        assert all(f.category.value == "pest" for f in result.findings)
