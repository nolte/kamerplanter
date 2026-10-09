"""#2174 — the interactive reference contribution reads the ``reference_contribution`` opt-in.

``POST /identification/reference`` turned a user's photo into a (quarantined)
recognition reference without ever reading the consent the automatic gallery
hook (REQ-034 §4.1 Guard 3) already required. What is pinned here, on the
service the route calls:

* without the opt-in — never granted or revoked — the contribution is refused
  with ``CONSENT_REQUIRED`` **before** the species lookup, the quota, the
  contribution marker and the embedding: a refused request leaves no trace;
* Light mode refuses outright (REQ-034 §4.1 Guard 2 / AC-16), even with an
  opt-in on record, and does not even read it;
* with the opt-in the contribution proceeds as before;
* a service built without the consent collaborators refuses to contribute;
* the species is resolved under the contributor's tenant (``readable_species``,
  as the gallery hook does): another tenant's private species answers 404 like
  an unknown one — no contribution, no existence oracle — while global, own and
  explicitly granted species proceed.

All collaborators are in-memory doubles — no database is touched.
"""

from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app.common.exceptions import AdapterNotAvailableError, ConsentRequiredError, NotFoundError
from app.config.settings import settings
from app.domain.engines.consent_engine import REFERENCE_CONTRIBUTION, ConsentEngine
from app.domain.services.reference_image_service import ReferenceImageService
from tests.support.fake_consent_repo import FakeConsentRepo
from tests.support.fake_contribution_marker import FakeContributionMarker
from tests.support.fake_species_repo import FakeSpeciesRepo

USER = "user_anna"
TENANT = "tenant_anna"
SPECIES = "species_monstera"
FOREIGN_TENANT = "tenant_ben"
FOREIGN_PRIVATE_SPECIES = "species_ben_private"


def _image() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 120, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _build(consent_repo: FakeConsentRepo | None, *, with_engine: bool = True):
    inference = MagicMock()
    inference.embed.return_value = [0.1] * 4
    inference.upsert_reference.return_value = {"status": "ok", "dim": 4}
    species_repo = FakeSpeciesRepo()
    species_repo.add(SPECIES, "Monstera deliciosa")  # global (tenant_key="")
    species_repo.add(FOREIGN_PRIVATE_SPECIES, "Philodendron privatum", tenant_key=FOREIGN_TENANT)
    rate_limiter = MagicMock()
    identification_engine = MagicMock()
    identification_engine.compute_image_hash.return_value = "hash"
    marker = FakeContributionMarker()
    service = ReferenceImageService(
        MagicMock(),
        MagicMock(),
        inference,
        MagicMock(),
        species_repo=species_repo,
        rate_limiter=rate_limiter,
        identification_engine=identification_engine,
        contribution_marker=marker,
        consent_repo=consent_repo,
        consent_engine=ConsentEngine() if with_engine else None,
    )
    doubles = SimpleNamespace(
        inference=inference,
        species_repo=species_repo,
        rate_limiter=rate_limiter,
        identification_engine=identification_engine,
        marker=marker,
    )
    return service, doubles


def _assert_untouched(doubles: SimpleNamespace) -> None:
    assert doubles.species_repo.lookups == []
    doubles.rate_limiter.check_and_increment.assert_not_called()
    doubles.identification_engine.compute_image_hash.assert_not_called()
    assert doubles.marker.writes == 0
    assert doubles.marker.since is None
    doubles.inference.embed.assert_not_called()
    doubles.inference.upsert_reference.assert_not_called()


@pytest.fixture
def full_mode(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")


@pytest.mark.usefixtures("full_mode")
def test_without_any_consent_record_the_contribution_is_refused_before_anything_runs():
    consent_repo = FakeConsentRepo()
    service, doubles = _build(consent_repo)

    with pytest.raises(ConsentRequiredError) as caught:
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert caught.value.status_code == 403
    assert caught.value.error_code == "CONSENT_REQUIRED"
    assert consent_repo.reads == [(USER, REFERENCE_CONTRIBUTION)]
    _assert_untouched(doubles)


@pytest.mark.usefixtures("full_mode")
def test_a_revoked_consent_refuses_the_contribution():
    consent_repo = FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): False})
    service, doubles = _build(consent_repo)

    with pytest.raises(ConsentRequiredError):
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    _assert_untouched(doubles)


@pytest.mark.usefixtures("full_mode")
def test_a_consent_for_another_purpose_or_user_does_not_open_the_contribution():
    consent_repo = FakeConsentRepo(
        {
            (USER, "plant_identification"): True,
            ("user_ben", REFERENCE_CONTRIBUTION): True,
        }
    )
    service, doubles = _build(consent_repo)

    with pytest.raises(ConsentRequiredError):
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    _assert_untouched(doubles)


@pytest.mark.usefixtures("full_mode")
def test_with_the_consent_granted_the_contribution_proceeds():
    consent_repo = FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): True})
    service, doubles = _build(consent_repo)

    result = service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert result["accepted"] is True
    assert result["pending_review"] is True
    doubles.rate_limiter.check_and_increment.assert_called_once()
    assert doubles.marker.writes == 1
    doubles.inference.upsert_reference.assert_called_once()
    assert doubles.inference.upsert_reference.call_args.kwargs["contributed_by"] == USER


@pytest.mark.usefixtures("full_mode")
def test_revoking_after_a_contribution_refuses_the_next_one():
    consent_repo = FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): True})
    service, doubles = _build(consent_repo)
    service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    consent_repo.set(USER, REFERENCE_CONTRIBUTION, granted=False)
    with pytest.raises(ConsentRequiredError):
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert doubles.rate_limiter.check_and_increment.call_count == 1
    assert doubles.marker.writes == 1
    assert doubles.inference.upsert_reference.call_count == 1


def test_light_mode_refuses_even_with_the_consent_on_record(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    consent_repo = FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): True})
    service, doubles = _build(consent_repo)

    with pytest.raises(AdapterNotAvailableError) as caught:
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert caught.value.status_code == 409
    assert caught.value.error_code == "ADAPTER_NOT_AVAILABLE"
    assert "light mode" in caught.value.message
    assert consent_repo.reads == []
    _assert_untouched(doubles)


@pytest.mark.usefixtures("full_mode")
@pytest.mark.parametrize("missing", ["repo", "engine"])
def test_a_service_without_the_consent_collaborators_refuses_to_contribute(missing):
    consent_repo = None if missing == "repo" else FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): True})
    service, doubles = _build(consent_repo, with_engine=missing != "engine")

    with pytest.raises(RuntimeError, match="#2174"):
        service.contribute_user_reference(SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    _assert_untouched(doubles)


# ── species scope — the contributor's tenant must be able to read the species ──


def _granted_service():
    consent_repo = FakeConsentRepo({(USER, REFERENCE_CONTRIBUTION): True})
    return _build(consent_repo)


@pytest.mark.usefixtures("full_mode")
def test_another_tenants_private_species_is_not_found_and_nothing_is_contributed():
    service, doubles = _granted_service()

    with pytest.raises(NotFoundError) as caught:
        service.contribute_user_reference(FOREIGN_PRIVATE_SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert caught.value.status_code == 404
    # The same answer an unknown key gets — the 404 does not tell the two apart.
    with pytest.raises(NotFoundError) as unknown:
        service.contribute_user_reference("species_ghost", _image(), user_key=USER, tenant_key=TENANT)
    assert (caught.value.error_code, caught.value.status_code) == (unknown.value.error_code, unknown.value.status_code)
    doubles.rate_limiter.check_and_increment.assert_not_called()
    assert doubles.marker.writes == 0
    doubles.inference.embed.assert_not_called()
    doubles.inference.upsert_reference.assert_not_called()


@pytest.mark.usefixtures("full_mode")
def test_the_owning_tenant_contributes_to_its_private_species():
    service, doubles = _build(FakeConsentRepo({("user_ben", REFERENCE_CONTRIBUTION): True}))

    result = service.contribute_user_reference(
        FOREIGN_PRIVATE_SPECIES, _image(), user_key="user_ben", tenant_key=FOREIGN_TENANT
    )

    assert result["accepted"] is True
    assert doubles.inference.upsert_reference.call_args.kwargs["scientific_name"] == "Philodendron privatum"


@pytest.mark.usefixtures("full_mode")
def test_a_species_granted_to_the_tenant_can_be_contributed_to():
    service, doubles = _granted_service()
    doubles.species_repo.grant(FOREIGN_PRIVATE_SPECIES, TENANT)

    result = service.contribute_user_reference(FOREIGN_PRIVATE_SPECIES, _image(), user_key=USER, tenant_key=TENANT)

    assert result["accepted"] is True
    doubles.inference.upsert_reference.assert_called_once()
