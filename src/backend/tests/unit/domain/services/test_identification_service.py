"""REQ-029 §3.6 / §5 — identification service: consent gate, rate limit, status."""

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.common.exceptions import ConsentRequiredError, FeatureNotConfiguredError, RateLimitError
from app.config.settings import settings
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.models.privacy import ConsentRecord
from app.domain.services.identification_service import IdentificationService


def _real_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (48, 48), color=(0, 100, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _StubAdapter(PlantIdentificationAdapter):
    adapter_key = "plantnet"
    supports_health_assessment = False
    rate_limit_per_day = 500

    def __init__(self, configured: bool = True) -> None:
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def identify(self, image_data, *, organ=PlantOrgan.AUTO, max_results=5, include_health=False, language="de"):
        return IdentificationResult(suggestions=[], is_plant=True)

    def diagnose(self, image_data, *, language="de") -> HealthAssessment:
        raise NotImplementedError


class _FakeRegistry:
    """Stand-in for IdentificationAdapterRegistry with a fixed adapter set."""

    def __init__(self, adapters: dict[str, _StubAdapter], preferred_key: str | None) -> None:
        self._adapters = adapters
        self._preferred_key = preferred_key

    def get(self, key):
        adapter = self._adapters.get(key)
        if adapter is None:
            raise KeyError(key)
        return adapter

    def get_preferred(self):
        if self._preferred_key is None:
            return None
        return self._adapters.get(self._preferred_key)

    def all_keys(self):
        return list(self._adapters.keys())


class _FakeConsentRepo:
    def __init__(self, granted: bool | None) -> None:
        self._granted = granted

    def get_by_user_and_purpose(self, user_key, purpose):
        if self._granted is None:
            return None
        return ConsentRecord(user_key=user_key, purpose=purpose, granted=self._granted)


def _service(*, consent_granted, registry, rate_limiter=None, engine=None) -> IdentificationService:
    return IdentificationService(
        engine=engine or MagicMock(),
        identification_repo=MagicMock(),
        consent_repo=_FakeConsentRepo(consent_granted),
        consent_engine=ConsentEngine(),
        rate_limiter=rate_limiter or MagicMock(),
        registry=registry,
    )


def _registry_with_plantnet(configured=True, preferred="plantnet"):
    adapter = _StubAdapter(configured=configured)
    return _FakeRegistry({"plantnet": adapter}, preferred if configured else None), adapter


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch):
    """Default every test to the full mode so the consent gate is active.

    The Light-mode behaviour (consent bypass) is exercised explicitly below by
    overriding ``settings.kamerplanter_mode`` to ``"light"``.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")


def test_identify_blocked_without_consent():
    registry, _ = _registry_with_plantnet()
    service = _service(consent_granted=None, registry=registry)

    with pytest.raises(ConsentRequiredError):
        service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")


def test_identify_blocked_with_revoked_consent():
    registry, _ = _registry_with_plantnet()
    service = _service(consent_granted=False, registry=registry)

    with pytest.raises(ConsentRequiredError):
        service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")


def test_identify_in_light_mode_skips_backend_consent(monkeypatch):
    """REQ-027 — Light mode has no consent subsystem; identify must run anyway.

    With no consent record present the full mode would raise ConsentRequiredError;
    in Light mode the backend gate is skipped and the engine is invoked.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    registry, _ = _registry_with_plantnet()
    engine = MagicMock()
    engine.identify.return_value = {"is_plant": True, "suggestions": [], "request_key": "ident_light"}
    service = _service(consent_granted=None, registry=registry, engine=engine)

    out = service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")

    assert out["request_key"] == "ident_light"
    engine.identify.assert_called_once()


def test_identify_full_mode_still_enforces_consent(monkeypatch):
    """Counterpart: in full mode the consent gate stays a hard precondition."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    registry, _ = _registry_with_plantnet()
    service = _service(consent_granted=None, registry=registry)

    with pytest.raises(ConsentRequiredError):
        service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")


def test_identify_with_consent_calls_engine():
    registry, adapter = _registry_with_plantnet()
    engine = MagicMock()
    engine.identify.return_value = {"is_plant": True, "suggestions": [], "request_key": "ident_1"}
    rate_limiter = MagicMock()
    service = _service(consent_granted=True, registry=registry, rate_limiter=rate_limiter, engine=engine)

    out = service.identify_plant(_real_jpeg(), organ=PlantOrgan.LEAF, tenant_key="t1", user_key="u1")

    assert out["request_key"] == "ident_1"
    engine.identify.assert_called_once()
    # Rate limiter uses the adapter's free-tier default (500/day) keyed per user.
    rate_limiter.check_and_increment.assert_called_once()
    _, kwargs = rate_limiter.check_and_increment.call_args
    assert kwargs["key"] == "identify:plantnet:u1"
    assert kwargs["limit"] == 500


def test_identify_feature_not_configured():
    registry, _ = _registry_with_plantnet(configured=False)
    service = _service(consent_granted=True, registry=registry)

    with pytest.raises(FeatureNotConfiguredError):
        service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")


def test_identify_propagates_rate_limit():
    registry, _ = _registry_with_plantnet()
    rate_limiter = MagicMock()
    rate_limiter.check_and_increment.side_effect = RateLimitError("plantnet", retry_after=3600)
    service = _service(consent_granted=True, registry=registry, rate_limiter=rate_limiter)

    with pytest.raises(RateLimitError):
        service.identify_plant(_real_jpeg(), tenant_key="t1", user_key="u1")


def test_status_reports_availability():
    registry, _ = _registry_with_plantnet()
    service = _service(consent_granted=True, registry=registry)

    status = service.get_status()
    assert status["available"] is True
    assert status["active_adapter"] == "plantnet"
    assert status["adapters"]["plantnet"]["configured"] is True
    assert status["adapters"]["plantnet"]["rate_limit_per_day"] == 500


def test_status_unavailable_when_unconfigured():
    registry, _ = _registry_with_plantnet(configured=False)
    service = _service(consent_granted=True, registry=registry)

    status = service.get_status()
    assert status["available"] is False
    assert status["active_adapter"] is None


def test_is_available():
    registry, _ = _registry_with_plantnet()
    assert _service(consent_granted=True, registry=registry).is_available() is True

    registry_off, _ = _registry_with_plantnet(configured=False)
    assert _service(consent_granted=True, registry=registry_off).is_available() is False
