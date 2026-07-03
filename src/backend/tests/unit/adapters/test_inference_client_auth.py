"""AP-4 service-token header tests for the inference-service clients (INF-S2)."""

from unittest.mock import MagicMock, patch

from app.data_access.external.inference_service_client import InferenceServiceClient
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient


class TestInferenceServiceClientAuth:
    @patch("app.data_access.external.inference_service_client.httpx.post")
    def test_match_sends_bearer_header(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"suggestions": [], "is_plant": False, "model": "m"}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        client = InferenceServiceClient("http://inf:8000", service_token="secret-token")
        client.match(b"imgbytes", k=3)

        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"

    @patch("app.data_access.external.inference_service_client.httpx.post")
    def test_embed_sends_bearer_header(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"embedding": [0.1, 0.2]}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        client = InferenceServiceClient("http://inf:8000", service_token="secret-token")
        client.embed(b"imgbytes")

        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"

    @patch("app.data_access.external.inference_service_client.httpx.get")
    def test_is_ready_sends_bearer_header(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        mock_get.return_value = response

        client = InferenceServiceClient("http://inf:8000", service_token="secret-token")
        assert client.is_ready() is True
        assert mock_get.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"

    def test_token_defaults_from_settings(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "internal_service_token", "from-settings")
        client = InferenceServiceClient("http://inf:8000")
        assert client._auth_headers() == {"Authorization": "Bearer from-settings"}

    @patch("app.data_access.external.inference_service_client.httpx.post")
    def test_no_header_when_token_empty(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"suggestions": [], "is_plant": False, "model": "m"}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        client = InferenceServiceClient("http://inf:8000", service_token="")
        client.match(b"imgbytes")

        assert mock_post.call_args[1]["headers"] == {}


class TestPestInferenceClientAuth:
    @patch("app.data_access.external.pest_inference_client.httpx.post")
    def test_detect_sends_bearer_header(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"findings": []}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        client = PestDetectionInferenceClient("http://inf:8000", service_token="secret-token")
        client.detect(b"tilebytes", mode="symptom")

        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"

    @patch("app.data_access.external.pest_inference_client.httpx.get")
    def test_is_ready_sends_bearer_header(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        mock_get.return_value = response

        client = PestDetectionInferenceClient("http://inf:8000", service_token="secret-token")
        assert client.is_ready() is True
        assert mock_get.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"

    def test_token_defaults_from_settings(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "internal_service_token", "from-settings")
        client = PestDetectionInferenceClient("http://inf:8000")
        assert client._auth_headers() == {"Authorization": "Bearer from-settings"}
