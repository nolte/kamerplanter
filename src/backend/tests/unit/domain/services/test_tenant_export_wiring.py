"""#2138 — what the provider hands the tenant export: its signing key and its reading source.

**Signing key** (REQ-056 §8.3): ``TENANT_EXPORT_SIGNING_SECRET`` when set, otherwise the derivation
from ``JWT_SECRET_KEY`` every installation used so far. One key signs and checks: with a dedicated
secret an archive signed under the JWT-derived key is unverified.

**Readings** (REQ-056 §8.3): only with ``TIMESCALEDB_ENABLED`` does the service get a reading source;
without it the archive has no ``timeseries/readings.csv``.

Measured through ``get_tenant_export_service`` with the datastores stubbed, so the assertion is on
the wiring a real process builds, not on a hand-made service.
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.common import dependencies as deps
from app.config.settings import Settings
from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.domain.engines.tenant_export_engine import TenantArchiveWriter, read_tenant_archive
from app.domain.services.tenant_export_service import export_signing_key, resolve_export_signing_key

JWT = "j" * 48
DEDICATED = "d" * 64


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(deps, "get_db", lambda: MagicMock(name="arango_db"))
    monkeypatch.setattr(deps, "get_connection", lambda: MagicMock(name="arango_connection"))
    monkeypatch.setattr(deps, "get_timescale_connection", lambda: MagicMock(name="timescale"))
    monkeypatch.setattr(deps.settings, "jwt_secret_key", JWT)

    def build(*, dedicated: str = "", timescale: bool = False):
        monkeypatch.setattr(deps.settings, "tenant_export_signing_secret", dedicated)
        monkeypatch.setattr(deps.settings, "timescaledb_enabled", timescale)
        return deps.get_tenant_export_service()

    return build


def _signed(key: bytes | None) -> bytes:
    buffer = io.BytesIO()
    writer = TenantArchiveWriter(buffer, max_bytes=None)
    writer.write_json("tenant.json", {"name": "Garden"})
    writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": "t-src"}, signing_key=key)
    return buffer.getvalue()


class TestTheSigningKey:
    def test_without_a_dedicated_secret_the_key_is_todays_jwt_derivation(self, provider) -> None:
        assert provider()._signing_key == export_signing_key(JWT)

    def test_a_dedicated_secret_replaces_the_jwt_derivation(self, provider) -> None:
        key = provider(dedicated=DEDICATED)._signing_key

        assert key == export_signing_key(DEDICATED)
        assert key != export_signing_key(JWT)

    def test_with_a_dedicated_secret_an_archive_signed_under_the_jwt_key_is_unverified(self) -> None:
        key = resolve_export_signing_key(dedicated_secret=DEDICATED, jwt_secret=JWT)

        assert read_tenant_archive(io.BytesIO(_signed(key)), signing_key=key).verified is True
        legacy = _signed(export_signing_key(JWT))
        assert read_tenant_archive(io.BytesIO(legacy), signing_key=key).verified is False

    def test_no_secret_at_all_signs_nothing(self) -> None:
        assert resolve_export_signing_key(dedicated_secret="", jwt_secret="") is None

    @pytest.mark.parametrize("value", ["", "x" * 32])
    def test_the_setting_is_empty_or_long_enough(self, value: str) -> None:
        assert Settings(tenant_export_signing_secret=value).tenant_export_signing_secret == value

    def test_a_short_secret_refuses_to_load(self) -> None:
        with pytest.raises(ValidationError, match="at least 32 characters"):
            Settings(tenant_export_signing_secret="x" * 31)


class TestTheReadingSource:
    def test_without_timescaledb_there_is_no_reading_source(self, provider) -> None:
        assert provider(timescale=False)._readings is None

    def test_with_timescaledb_the_service_reads_from_it(self, provider) -> None:
        assert isinstance(provider(timescale=True)._readings, TimescaleObservationRepository)
