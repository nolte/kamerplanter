"""AP-4 service-token header tests for the inference-service clients (INF-S2)."""

from unittest.mock import MagicMock, patch

from app.data_access.external.cv_diagnosis_inference_client import CvDiagnosisInferenceClient
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


class TestCvDiagnosisInferenceClientAuth:
    @patch("app.data_access.external.cv_diagnosis_inference_client.httpx.post")
    def test_classify_sends_bearer_header_and_params(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"classifications": [], "disclaimer": "d", "model_meta": {}}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        client = CvDiagnosisInferenceClient("http://inf:8000", service_token="secret-token")
        payload = client.classify(b"imgbytes", k=3, with_phenotype=True)

        assert payload["disclaimer"] == "d"
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret-token"
        assert mock_post.call_args[1]["params"] == {"k": 3, "phenotype": True}

    @patch("app.data_access.external.cv_diagnosis_inference_client.httpx.get")
    def test_is_ready_true_on_200(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        mock_get.return_value = response

        client = CvDiagnosisInferenceClient("http://inf:8000", service_token="t")
        assert client.is_ready() is True
        assert mock_get.call_args[1]["headers"]["Authorization"] == "Bearer t"

    @patch("app.data_access.external.cv_diagnosis_inference_client.httpx.get")
    def test_is_ready_false_on_http_error(self, mock_get):
        import httpx

        mock_get.side_effect = httpx.ConnectError("boom")
        client = CvDiagnosisInferenceClient("http://inf:8000", service_token="t")
        assert client.is_ready() is False

    @patch("app.data_access.external.cv_diagnosis_inference_client.httpx.get")
    def test_status_failsafe_on_unreachable(self, mock_get):
        import httpx

        mock_get.side_effect = httpx.ConnectError("boom")
        client = CvDiagnosisInferenceClient("http://inf:8000", service_token="t")
        snapshot = client.status()
        assert snapshot["ready"] is False
        assert snapshot["enabled"] is False

    def test_token_defaults_from_settings(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "internal_service_token", "from-settings")
        client = CvDiagnosisInferenceClient("http://inf:8000")
        assert client._auth_headers() == {"Authorization": "Bearer from-settings"}
