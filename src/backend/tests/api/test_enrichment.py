"""API tests for enrichment endpoints."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_enrichment_service, get_tenant_service
from app.common.enums import AuthType, SyncStatus, SyncTrigger
from app.domain.models.enrichment import (
    ExternalMapping,
    ExternalSource,
    ExternalSpeciesData,
    FieldMapping,
    SyncRun,
)
from app.domain.models.user import User


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def _mock_user():
    return User(_key="test_user", email="test@example.com", display_name="Test User")


@pytest.fixture
def client(mock_service, _mock_user):
    """A PLATFORM-ADMIN caller, because the writes here changed installation-wide rows.

    Enrichment configuration belongs to the installation, not to a tenant: one
    external-source mapping is what every tenant's species enrichment runs on.
    Until #1402 these routes carried `get_current_user` alone, so any authenticated
    member of any tenant could trigger a sync, accept an enrichment, or edit a
    mapping for everyone. They are gated like their `companion_planting` siblings
    now, and this fixture supplies the caller that gate expects.

    `TestTheWritesAreRefusedWithoutPlatformAdmin` below drives the same routes
    WITHOUT the override — a suite that only ever calls through one is a suite that
    cannot tell a gate from its absence.
    """
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_enrichment_service] = lambda: mock_service
        app.dependency_overrides[get_current_user] = lambda: _mock_user
        app.dependency_overrides[require_platform_admin] = lambda: _mock_user
        yield TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides.pop(get_enrichment_service, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_platform_admin, None)


@pytest.fixture
def sample_source():
    return ExternalSource(
        _key="src_1",
        name="GBIF",
        source_key="gbif",
        base_url="https://api.gbif.org/v1",
        auth_type=AuthType.NONE,
        rate_limit_per_minute=60,
        priority=1,
        enabled=True,
    )


@pytest.fixture
def sample_sync_run():
    return SyncRun(
        _key="run_1",
        source_key="gbif",
        status=SyncStatus.SUCCESS,
        triggered_by=SyncTrigger.MANUAL,
        total_processed=5,
        new_mappings=3,
        updated_mappings=1,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, 0, 5, tzinfo=UTC),
    )


@pytest.fixture
def sample_mapping():
    return ExternalMapping(
        _key="em_1",
        internal_collection="species",
        internal_key="sp_1",
        source_key="gbif",
        external_id="12345",
        field_mappings={
            "genus": FieldMapping(external_value="Rosa", confidence=0.9, accepted=True),
            "native_habitat": FieldMapping(external_value="Europe", confidence=0.7, accepted=False),
        },
    )


class TestListSources:
    def test_list_sources(self, client, mock_service, sample_source):
        mock_service.list_sources.return_value = [sample_source]

        response = client.get("/api/v1/enrichment/sources")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_key"] == "gbif"
        assert data[0]["name"] == "GBIF"


class TestGetSource:
    def test_get_source(self, client, mock_service, sample_source):
        mock_service.get_source.return_value = sample_source

        response = client.get("/api/v1/enrichment/sources/gbif")

        assert response.status_code == 200
        data = response.json()
        assert data["source_key"] == "gbif"


class TestTriggerSync:
    def test_trigger_sync(self, client, mock_service, sample_sync_run):
        mock_service.trigger_sync.return_value = sample_sync_run

        response = client.post("/api/v1/enrichment/sources/gbif/sync", json={"full_sync": False})

        assert response.status_code == 202
        data = response.json()
        assert data["source_key"] == "gbif"
        assert data["status"] == "success"


class TestSyncHistory:
    def test_get_history(self, client, mock_service, sample_sync_run):
        mock_service.get_sync_history.return_value = [sample_sync_run]

        response = client.get("/api/v1/enrichment/sources/gbif/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_processed"] == 5


class TestSpeciesEnrichments:
    def test_get_enrichments(self, client, mock_service, sample_mapping):
        mock_service.get_species_enrichments.return_value = [sample_mapping]

        response = client.get("/api/v1/enrichment/species/sp_1/enrichments")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source_key"] == "gbif"
        assert "genus" in data[0]["field_mappings"]

    def test_accept_enrichment(self, client, mock_service, sample_mapping):
        mock_service.accept_enrichment.return_value = sample_mapping

        response = client.post(
            "/api/v1/enrichment/species/sp_1/enrichments/gbif/accept",
            json={"fields": ["genus"]},
        )

        assert response.status_code == 200
        mock_service.accept_enrichment.assert_called_once_with("sp_1", "gbif", ["genus"])

    def test_reject_enrichment(self, client, mock_service, sample_mapping):
        mock_service.reject_enrichment.return_value = sample_mapping

        response = client.post(
            "/api/v1/enrichment/species/sp_1/enrichments/gbif/reject",
            json={"fields": ["native_habitat"]},
        )

        assert response.status_code == 200
        mock_service.reject_enrichment.assert_called_once_with("sp_1", "gbif", ["native_habitat"])

    def test_accept_empty_fields_fails(self, client, mock_service):
        response = client.post(
            "/api/v1/enrichment/species/sp_1/enrichments/gbif/accept",
            json={"fields": []},
        )

        assert response.status_code == 422


class TestExternalSearch:
    def test_search_external(self, client, mock_service):
        mock_service.search_external.return_value = [
            ExternalSpeciesData(
                external_id="123",
                scientific_name="Rosa canina",
                common_names=["Dog Rose"],
                genus="Rosa",
                family_name="Rosaceae",
                synonyms=["Rosa canis"],
                taxonomic_authority="L.",
                taxonomic_status="ACCEPTED",
                canonical_name="Rosa canina",
            )
        ]

        response = client.post(
            "/api/v1/enrichment/search",
            json={"source_key": "gbif", "query": "Rosa"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["scientific_name"] == "Rosa canina"
        assert data[0]["synonyms"] == ["Rosa canis"]
        assert data[0]["taxonomic_authority"] == "L."
        assert data[0]["taxonomic_status"] == "ACCEPTED"
        assert data[0]["canonical_name"] == "Rosa canina"


class TestHealth:
    def test_get_health(self, client, mock_service):
        mock_service.get_source_health.return_value = {"gbif": True, "perenual": False}

        response = client.get("/api/v1/enrichment/health")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestTheWritesAreRefusedWithoutPlatformAdmin:
    """The gate itself (#1402 group B), driven without the override that hides it.

    Every other test in this file supplies a platform admin. These do not, and they
    are the only thing here that goes red if the `require_platform_admin`
    dependencies are dropped again. `require_platform_admin` resolves through
    `get_current_user` and a membership lookup, so a caller with neither is
    refused before any handler runs.
    """

    @pytest.fixture
    def member_client(self, mock_service, _mock_user):
        """Authenticated, no platform-admin membership — the caller #1402 describes."""
        with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
            from app.main import app

            app.dependency_overrides[get_enrichment_service] = lambda: mock_service
            app.dependency_overrides[get_current_user] = lambda: _mock_user
            app.dependency_overrides.pop(require_platform_admin, None)
            # `require_platform_admin` resolves a real `TenantService`, which without
            # this double reaches for a database and turns every refusal below into a
            # 500. The assertion used to accept that 500 — and an ungated route
            # answers 500 here too, so it certified nothing (NFR-018 §1). The double
            # reports "no platform membership", which is the caller #1402 describes,
            # and lets the gate answer the 403 the assertion can now demand exactly.
            tenant_service = MagicMock()
            tenant_service.get_membership.return_value = None
            app.dependency_overrides[get_tenant_service] = lambda: tenant_service
            yield TestClient(app, raise_server_exceptions=False)
            app.dependency_overrides.pop(get_enrichment_service, None)
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_tenant_service, None)

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("POST", "/api/v1/enrichment/sources/gbif/sync"),
            ("POST", "/api/v1/enrichment/species/sp1/enrichments/e1/accept"),
            ("POST", "/api/v1/enrichment/species/sp1/enrichments/e1/reject"),
            # The fourth gated write, absent from this list until review round 1.
            # A sweep that misses one route is how the router half-drifts back.
            ("POST", "/api/v1/enrichment/search"),
        ],
    )
    def test_a_plain_member_is_refused(self, member_client, method: str, path: str):
        response = member_client.request(method, path, json={})

        assert response.status_code == 403, (
            f"{method} {path} answered {response.status_code} for a caller with no platform-admin "
            "membership; the gate from #1402 is gone or inert"
        )

    def test_the_reads_stay_open_to_a_member(self, member_client, mock_service):
        """The control, and the #706 direction.

        Gating the whole router instead of its writes would satisfy every refusal
        above and break the product: these catalogues are what every tenant's
        enrichment consults.
        """
        mock_service.list_sources.return_value = []

        response = member_client.get("/api/v1/enrichment/sources")

        assert response.status_code == 200, response.text
