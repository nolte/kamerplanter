"""REQ-029 §3.6 / §5 — identification service: consent gate, rate limit, status."""

import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.common.exceptions import (
    AdapterNotAvailableError,
    ConsentRequiredError,
    FeatureNotConfiguredError,
    RateLimitError,
)
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
    is_external = True

    def __init__(self, configured: bool = True, *, adapter_key: str | None = None) -> None:
        self._configured = configured
        if adapter_key is not None:
            self.adapter_key = adapter_key
        # Mirror the real adapters' egress classification (REQ-034 §4a.1): the
        # self-hosted DINOv2 path is non-external, every hosted service is.
        self.is_external = adapter_key != "local_embedding"

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
    # SEC-003: the configured per-user daily floor (50) wins over the adapter's
    # larger free-tier default so one account cannot drain the shared quota.
    rate_limiter.check_and_increment.assert_called_once()
    _, kwargs = rate_limiter.check_and_increment.call_args
    assert kwargs["key"] == "identify:plantnet:u1"
    assert kwargs["limit"] == settings.identification_rate_limit_per_user_day


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


# ── REQ-034 §4a — quality assessment ──────────────────────────────────


def _registry_with(plantnet=True, local=False):
    """Registry with optionally-configured plantnet + local_embedding adapters."""
    adapters: dict[str, _StubAdapter] = {}
    if plantnet is not None:
        adapters["plantnet"] = _StubAdapter(configured=plantnet, adapter_key="plantnet")
    if local is not None:
        adapters["local_embedding"] = _StubAdapter(configured=local, adapter_key="local_embedding")
    return _FakeRegistry(adapters, "plantnet")


def _raw_engine(result):
    engine = MagicMock()
    engine.identify_raw.return_value = result
    return engine


def test_assess_quality_external_runs_consent_and_returns_raw():
    registry = _registry_with(plantnet=True, local=False)
    result = IdentificationResult(suggestions=[], is_plant=True)
    rate_limiter = MagicMock()
    service = _service(
        consent_granted=True,
        registry=registry,
        rate_limiter=rate_limiter,
        engine=_raw_engine(result),
    )
    out = service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")
    assert out is result
    # External path is rate-limited per adapter+user and fails closed (SEC-003).
    _, kwargs = rate_limiter.check_and_increment.call_args
    assert kwargs["key"] == "assess:plantnet:u1"
    assert kwargs["fail_closed"] is True


def test_assess_quality_local_rate_limit_fails_open(monkeypatch):
    """SEC-003 — the self-hosted path keeps fail-open (no third-party cost)."""
    # Force a positive limit so the limiter is actually invoked for the local path.
    monkeypatch.setattr(settings, "identification_rate_limit_per_user_day", 25)
    registry = _registry_with(plantnet=False, local=True)
    result = IdentificationResult(suggestions=[], is_plant=True)
    rate_limiter = MagicMock()
    service = _service(
        consent_granted=True,
        registry=registry,
        rate_limiter=rate_limiter,
        engine=_raw_engine(result),
    )
    service.assess_quality(_real_jpeg(), adapter_key="local_embedding", tenant_key="t1", user_key="u1")
    _, kwargs = rate_limiter.check_and_increment.call_args
    assert kwargs["key"] == "assess:local_embedding:u1"
    assert kwargs["fail_closed"] is False


class _FailingRedis:
    """Redis stub whose every operation raises (simulates an outage)."""

    def incr(self, *_args, **_kwargs):
        raise ConnectionError("redis down")

    def expire(self, *_args, **_kwargs):  # pragma: no cover - never reached
        raise ConnectionError("redis down")


def test_assess_quality_external_blocked_on_redis_outage(monkeypatch):
    """SEC-003 — Redis outage + external adapter ⇒ reject (fail closed, 429)."""
    from app.domain.services.identification_rate_limiter import IdentificationRateLimiter

    monkeypatch.setattr(settings, "identification_rate_limit_per_user_day", 25)
    registry = _registry_with(plantnet=True, local=False)
    limiter = IdentificationRateLimiter(_FailingRedis())
    service = _service(
        consent_granted=True,
        registry=registry,
        rate_limiter=limiter,
        engine=_raw_engine(IdentificationResult(suggestions=[], is_plant=True)),
    )
    with pytest.raises(RateLimitError):
        service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")


def test_assess_quality_local_allowed_on_redis_outage(monkeypatch):
    """SEC-003 — Redis outage + local adapter ⇒ allowed (fail open)."""
    from app.domain.services.identification_rate_limiter import IdentificationRateLimiter

    monkeypatch.setattr(settings, "identification_rate_limit_per_user_day", 25)
    registry = _registry_with(plantnet=False, local=True)
    limiter = IdentificationRateLimiter(_FailingRedis())
    result = IdentificationResult(suggestions=[], is_plant=True)
    service = _service(
        consent_granted=True,
        registry=registry,
        rate_limiter=limiter,
        engine=_raw_engine(result),
    )
    out = service.assess_quality(_real_jpeg(), adapter_key="local_embedding", tenant_key="t1", user_key="u1")
    assert out is result


def test_is_external_derived_from_adapter_capability():
    """SEC-005 — external classification comes from the adapter's is_external flag."""
    registry = _registry_with(plantnet=True, local=True)
    service = _service(consent_granted=True, registry=registry)
    assert service._is_external("plantnet") is True
    assert service._is_external("local_embedding") is False


def test_is_external_unregistered_key_falls_back_to_allowlist():
    """SEC-005 — an unregistered key uses the static allow-list (plant_id ⇒ external)."""
    registry = _registry_with(plantnet=True, local=False)
    service = _service(consent_granted=True, registry=registry)
    # Not registered here, but a known external service → treated as external.
    assert service._is_external("plant_id") is True
    # Unknown, non-allow-listed key → not optimistically external.
    assert service._is_external("totally_unknown") is False


def test_assess_quality_external_blocked_without_consent():
    registry = _registry_with(plantnet=True)
    service = _service(consent_granted=None, registry=registry, engine=_raw_engine(None))
    with pytest.raises(ConsentRequiredError):
        service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")


def test_assess_quality_local_skips_consent(monkeypatch):
    # The self-hosted adapter has no data egress → no consent needed even with
    # no consent record present in full mode.
    registry = _registry_with(plantnet=False, local=True)
    result = IdentificationResult(suggestions=[], is_plant=True)
    service = _service(consent_granted=None, registry=registry, engine=_raw_engine(result))
    out = service.assess_quality(_real_jpeg(), adapter_key="local_embedding", tenant_key="t1", user_key="u1")
    assert out is result


def test_assess_quality_local_unavailable_409():
    # local_embedding registered but not configured (inference disabled) → 409.
    registry = _registry_with(plantnet=True, local=False)
    service = _service(consent_granted=True, registry=registry, engine=_raw_engine(None))
    with pytest.raises(AdapterNotAvailableError):
        service.assess_quality(_real_jpeg(), adapter_key="local_embedding", tenant_key="t1", user_key="u1")


def test_assess_quality_unknown_adapter_409():
    registry = _registry_with(plantnet=True)
    service = _service(consent_granted=True, registry=registry, engine=_raw_engine(None))
    with pytest.raises(AdapterNotAvailableError):
        service.assess_quality(_real_jpeg(), adapter_key="ghost", tenant_key="t1", user_key="u1")


def test_assess_quality_external_blocked_in_light_mode_without_optin(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    monkeypatch.setattr(settings, "identification_external_in_light_mode", False)
    registry = _registry_with(plantnet=True)
    service = _service(consent_granted=None, registry=registry, engine=_raw_engine(None))
    with pytest.raises(AdapterNotAvailableError):
        service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")


def test_assess_quality_light_mode_default_blocks_external_keeps_local(monkeypatch):
    """SEC-002 — with the Light-mode default (opt-in off) the external path is 409
    while the self-hosted ``local_embedding`` path stays usable and untouched."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    # Assert we are relying on the documented default, not an override.
    assert settings.identification_external_in_light_mode is False
    registry = _registry_with(plantnet=True, local=True)
    result = IdentificationResult(suggestions=[], is_plant=True)
    service = _service(consent_granted=None, registry=registry, engine=_raw_engine(result))
    # External path → 409.
    with pytest.raises(AdapterNotAvailableError):
        service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")
    # Local path → runs through untouched.
    out = service.assess_quality(_real_jpeg(), adapter_key="local_embedding", tenant_key="t1", user_key="u1")
    assert out is result


def test_assess_quality_external_allowed_in_light_mode_with_optin(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    monkeypatch.setattr(settings, "identification_external_in_light_mode", True)
    registry = _registry_with(plantnet=True)
    result = IdentificationResult(suggestions=[], is_plant=True)
    service = _service(consent_granted=None, registry=registry, engine=_raw_engine(result))
    # Light mode skips the backend consent record entirely → runs through.
    out = service.assess_quality(_real_jpeg(), adapter_key="plantnet", tenant_key="t1", user_key="u1")
    assert out is result


def test_list_assessment_adapters_full_mode():
    registry = _registry_with(plantnet=True, local=False)
    service = _service(consent_granted=True, registry=registry)
    adapters = {a["key"]: a for a in service.list_assessment_adapters()}
    assert adapters["plantnet"]["available"] is True
    assert adapters["plantnet"]["external"] is True
    assert adapters["plantnet"]["requires_consent"] is True
    # local_embedding registered but not configured → returned, greyed-out.
    assert adapters["local_embedding"]["available"] is False
    assert adapters["local_embedding"]["external"] is False
    assert adapters["local_embedding"]["requires_consent"] is False


def test_list_assessment_adapters_light_mode_blocks_external(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    monkeypatch.setattr(settings, "identification_external_in_light_mode", False)
    registry = _registry_with(plantnet=True, local=True)
    service = _service(consent_granted=True, registry=registry)
    adapters = {a["key"]: a for a in service.list_assessment_adapters()}
    # External path disabled in light mode without opt-in.
    assert adapters["plantnet"]["available"] is False
    assert adapters["plantnet"]["requires_consent"] is False  # no consent subsystem in light mode
    # Self-hosted stays available.
    assert adapters["local_embedding"]["available"] is True
