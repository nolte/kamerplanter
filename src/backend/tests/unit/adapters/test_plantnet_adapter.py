"""REQ-029 §3.3 — unit tests for the Pl@ntNet adapter (mocked HTTP)."""

from unittest.mock import MagicMock, patch

import pytest
import structlog
from httpx import HTTPStatusError, Request, RequestError, Response

from app.common.exceptions import ExternalSourceError, RateLimitError
from app.data_access.external.plantnet_adapter import PlantNetAdapter
from app.domain.interfaces.plant_identification_adapter import PlantOrgan

SECRET_API_KEY = "super-secret-key-12345"

PLANTNET_RESPONSE = {
    "results": [
        {
            "score": 0.9123,
            "species": {
                "scientificNameWithoutAuthor": "Monstera deliciosa",
                "commonNames": ["Swiss Cheese Plant", "Fensterblatt"],
                "family": {"scientificNameWithoutAuthor": "Araceae"},
                "genus": {"scientificNameWithoutAuthor": "Monstera"},
                "gbif": {"id": "2868543"},
            },
            "images": [{"url": {"m": "https://example.org/monstera_m.jpg"}}],
        },
        {
            "score": 0.0421,
            "species": {
                "scientificNameWithoutAuthor": "Monstera adansonii",
                "commonNames": ["Monkey Mask"],
                "family": {"scientificNameWithoutAuthor": "Araceae"},
                "genus": {"scientificNameWithoutAuthor": "Monstera"},
                "gbif": {"id": None},
            },
            "images": [],
        },
    ]
}


def _adapter(api_key: str = "test-key") -> PlantNetAdapter:
    adapter = PlantNetAdapter()
    # The key is resolved at call time (DB overrides env); pin it for the test.
    adapter._resolve_api_key = lambda: api_key  # type: ignore[method-assign]
    return adapter


def _mock_client_returning(response: MagicMock):
    """Build a context-manager mock that yields a client whose post() returns ``response``."""
    client = MagicMock()
    client.post.return_value = response
    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False
    return ctx, client


def test_is_configured_reflects_api_key():
    assert _adapter("key").is_configured() is True
    assert _adapter("").is_configured() is False


def test_resolve_api_key_uses_effective_db_key():
    """The adapter must resolve the effective key (DB overrides env) at call time."""
    adapter = PlantNetAdapter()
    fake_service = MagicMock()
    fake_service.get_effective_plantnet_api_key.return_value = "db-key"
    with patch(
        "app.common.dependencies.get_system_settings_service",
        return_value=fake_service,
    ):
        assert adapter._resolve_api_key() == "db-key"
        assert adapter.is_configured() is True


def test_resolve_api_key_falls_back_to_env_when_collection_missing():
    """If the settings service blows up (collection missing) fall back to env."""
    adapter = PlantNetAdapter()
    with (
        patch(
            "app.common.dependencies.get_system_settings_service",
            side_effect=RuntimeError("collection not found"),
        ),
        patch(
            "app.data_access.external.plantnet_adapter.settings",
        ) as mock_settings,
    ):
        mock_settings.plantnet_api_key = "env-key"
        assert adapter._resolve_api_key() == "env-key"


def test_identify_maps_suggestions():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = PLANTNET_RESPONSE
    ctx, client = _mock_client_returning(response)

    with patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx):
        result = _adapter().identify(b"\xff\xd8imagebytes", organ=PlantOrgan.LEAF, max_results=5)

    assert result.is_plant is True
    assert len(result.suggestions) == 2

    top = result.suggestions[0]
    assert top.rank == 1
    assert top.scientific_name == "Monstera deliciosa"
    assert top.common_names == ["Swiss Cheese Plant", "Fensterblatt"]
    assert top.family == "Araceae"
    assert top.genus == "Monstera"
    assert top.confidence == pytest.approx(0.9123)
    assert top.gbif_id == 2868543
    # Adapter-neutral, namespaced external id (REQ-029-A §0.1.1 point 5).
    assert top.external_id == "plantnet:2868543"
    assert top.image_url == "https://example.org/monstera_m.jpg"

    # Missing GBIF id falls back to a slugged scientific name, still namespaced.
    second = result.suggestions[1]
    assert second.gbif_id is None
    assert second.external_id == "plantnet:monstera_adansonii"

    # organ is forwarded as form data
    _, kwargs = client.post.call_args
    assert kwargs["data"] == {"organs": "leaf"}


def test_identify_auto_organ_sends_auto():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"results": []}
    ctx, client = _mock_client_returning(response)

    with patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx):
        result = _adapter().identify(b"\xff\xd8img", organ=PlantOrgan.AUTO)

    assert result.is_plant is False
    _, kwargs = client.post.call_args
    assert kwargs["data"] == {"organs": "auto"}


def test_identify_rate_limit_raises():
    response = MagicMock()
    response.status_code = 429
    ctx, _ = _mock_client_returning(response)

    with (
        patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx),
        pytest.raises(RateLimitError),
    ):
        _adapter().identify(b"\xff\xd8img")


@pytest.mark.parametrize("status_code", [401, 403])
def test_identify_key_error_raises_external_source_error(status_code):
    response = MagicMock()
    response.status_code = status_code
    ctx, _ = _mock_client_returning(response)

    with (
        patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx),
        pytest.raises(ExternalSourceError),
    ):
        _adapter().identify(b"\xff\xd8img")


def test_identify_404_means_no_plant():
    response = MagicMock()
    response.status_code = 404
    ctx, _ = _mock_client_returning(response)

    with patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx):
        result = _adapter().identify(b"\xff\xd8img")

    assert result.is_plant is False
    assert result.suggestions == []


def test_identify_network_error_raises_external_source_error():
    client = MagicMock()
    client.post.side_effect = RequestError("boom")
    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False

    with (
        patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx),
        pytest.raises(ExternalSourceError),
    ):
        _adapter().identify(b"\xff\xd8img")


def test_identify_without_key_raises():
    with pytest.raises(ExternalSourceError):
        _adapter("").identify(b"\xff\xd8img")


def test_network_error_does_not_leak_api_key():
    """GDPR-004: a failed request must not leak the api-key into logs or errors.

    httpx embeds the full request URL (incl. the ``api-key`` query param) in its
    exception message, so str(exc) must never reach the log or the raised error.
    """
    request = Request(
        "POST",
        f"https://my-api.plantnet.org/v2/identify/all?api-key={SECRET_API_KEY}",
    )
    client = MagicMock()
    client.post.side_effect = RequestError(
        f"connection failed for url with api-key={SECRET_API_KEY}",
        request=request,
    )
    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False

    with (
        patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx),
        structlog.testing.capture_logs() as logs,
        pytest.raises(ExternalSourceError) as exc_info,
    ):
        _adapter(SECRET_API_KEY).identify(b"\xff\xd8img")

    log_text = repr(logs)
    assert SECRET_API_KEY not in log_text
    assert SECRET_API_KEY not in str(exc_info.value)
    # The exception class is logged instead of the raw message.
    assert any(entry.get("error_type") == "RequestError" for entry in logs)


def test_http_status_error_logs_status_without_key():
    """GDPR-004: HTTPStatusError must log the status code, never the secret URL."""
    request = Request(
        "POST",
        f"https://my-api.plantnet.org/v2/identify/all?api-key={SECRET_API_KEY}",
    )
    error_response = Response(500, request=request)
    response = MagicMock()
    response.status_code = 500
    response.raise_for_status.side_effect = HTTPStatusError(
        f"500 Server Error for url with api-key={SECRET_API_KEY}",
        request=request,
        response=error_response,
    )
    ctx, _ = _mock_client_returning(response)

    with (
        patch("app.data_access.external.plantnet_adapter.Client", return_value=ctx),
        structlog.testing.capture_logs() as logs,
        pytest.raises(ExternalSourceError) as exc_info,
    ):
        _adapter(SECRET_API_KEY).identify(b"\xff\xd8img")

    log_text = repr(logs)
    assert SECRET_API_KEY not in log_text
    assert SECRET_API_KEY not in str(exc_info.value)
    failure = next(entry for entry in logs if entry["event"] == "plantnet_identify_failed")
    assert failure["error_type"] == "HTTPStatusError"
    assert failure["status_code"] == 500


def test_diagnose_not_supported():
    assert PlantNetAdapter.supports_health_assessment is False
    with pytest.raises(NotImplementedError):
        _adapter().diagnose(b"\xff\xd8img")
