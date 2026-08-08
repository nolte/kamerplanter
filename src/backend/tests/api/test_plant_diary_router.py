"""API tests for the plant-diary endpoints (REQ-013 §4.7, REQ-050 §2.5.1).

Three groups:

* the **cross-tenant fix** on the pre-existing run-scoped endpoints. They
  verified only the *run* against the caller's tenant and then loaded the entry
  by bare key, so a foreign ``entry_key`` was readable, writable and deletable
  across tenants. Each of the three tests below fails on the code as it stood
  before this work package (AK-12);
* the **standalone** endpoints of REQ-013 §4.7, specified since v2.0 and never
  built — without them a plant outside a planting run has no diary at all;
* **marking** an entry for AI analysis on both prefixes (AK-01, AK-02, AK-03).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.diary.tenant_router import router as diary_overview_router
from app.api.v1.plant_instances.diary_router import router as plant_diary_router
from app.api.v1.planting_runs.tenant_router import router as planting_runs_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_plant_diary_service,
    get_plant_instance_service,
    get_planting_run_service,
)
from app.common.enums import AttachmentCategory, DiaryAnalysisState, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_diary_service import PlantDiaryService
from tests.support.diary_fakes import (
    FakeAttachmentRepository,
    FakeDiaryRepository,
    FakePlantingRunService,
    FakePlantInstanceService,
)

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"
PLANT_KEY = "plant-1"
OTHER_PLANT_KEY = "plant-2"
#: A plant of ``tenant-b``. Exists in the installation, is never addressable
#: from ``tenant-a`` — the anchor of the SEC-002 tests below.
FOREIGN_PLANT_KEY = "plant-b-1"
RUN_KEY = "run-1"
AUTHOR = "user-author"
OTHER_USER = "user-other"

# SEC-003 — the four attachment shapes ``photo_refs`` has to tell apart.
OWN_PHOTO = "photo-own"
OTHER_MEMBERS_PHOTO = "photo-of-other-member"
GALLERY_PHOTO = "photo-gallery"
FOREIGN_PHOTO = "photo-of-tenant-b"


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch):
    """Run in full mode, so §7.2 authorship and consent are actually evaluated.

    In Light mode both gates fall away by design (§7.5); a default that happened
    to be Light would make the authorship tests pass without testing anything.
    """
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "full")
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", "api-test-secret-value")


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _plant(key: str, tenant_key: str = TENANT_KEY) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant_key,
        instance_id=f"P-{key}",
        species_key="solanum_lycopersicum",
        plant_name=f"Tomate {key}",
        planted_on=date(2026, 4, 18),
    )


def _build(role: TenantRole = TenantRole.GROWER, user_key: str = AUTHOR):
    repo = FakeDiaryRepository()
    attachments = FakeAttachmentRepository()
    # A diary photo each member uploaded themselves, plus one belonging to the
    # other member of the same tenant — the SEC-003 case — and a gallery photo of
    # the caller's own that is still not a *diary* attachment.
    attachments.add(OWN_PHOTO, tenant_key=TENANT_KEY, created_by=AUTHOR)
    attachments.add(OTHER_MEMBERS_PHOTO, tenant_key=TENANT_KEY, created_by=OTHER_USER)
    attachments.add(
        GALLERY_PHOTO,
        tenant_key=TENANT_KEY,
        created_by=AUTHOR,
        category=AttachmentCategory.PLANT,
    )
    attachments.add(FOREIGN_PHOTO, tenant_key=FOREIGN_TENANT_KEY, created_by="user-of-tenant-b")
    diary_service = PlantDiaryService(diary_repo=repo, attachment_repo=attachments)
    plant_service = FakePlantInstanceService(
        plants={
            PLANT_KEY: _plant(PLANT_KEY),
            OTHER_PLANT_KEY: _plant(OTHER_PLANT_KEY),
            FOREIGN_PLANT_KEY: _plant(FOREIGN_PLANT_KEY, tenant_key=FOREIGN_TENANT_KEY),
        }
    )
    run_service = FakePlantingRunService({RUN_KEY: TENANT_KEY})
    repo.plants = plant_service.plants
    repo.run_plants[RUN_KEY] = [PLANT_KEY, OTHER_PLANT_KEY]

    app = FastAPI()
    app.include_router(plant_diary_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(planting_runs_router, prefix="/api/v1/t/{tenant_slug}")
    # The overview is mounted next to the two entry paths so one test can read
    # the *same* seeded document through both and compare the answers. The
    # divergence this work package removes was only visible that way: each path
    # was internally consistent, and only the pair contradicted itself.
    app.include_router(diary_overview_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key=user_key,
        role=role,
    )
    app.dependency_overrides[get_plant_diary_service] = lambda: diary_service
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    app.dependency_overrides[get_planting_run_service] = lambda: run_service
    return TestClient(app), repo


def _run_entry_url(entry_key: str, plant_key: str = PLANT_KEY) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/planting-runs/{RUN_KEY}/plants/{plant_key}/diary/{entry_key}"


def _run_plant_diary_url(plant_key: str = PLANT_KEY) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/planting-runs/{RUN_KEY}/plants/{plant_key}/diary"


def _plant_url(path: str = "", plant_key: str = PLANT_KEY) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plant-instances/{plant_key}/diary{path}"


def _overview_url() -> str:
    return f"/api/v1/t/{TENANT_SLUG}/diary"


def _run_diary_url() -> str:
    return f"/api/v1/t/{TENANT_SLUG}/planting-runs/{RUN_KEY}/diary"


# ── The cross-tenant leak on the pre-existing run endpoints (AK-12) ───────────


class TestRunDiaryCrossTenantIsolation:
    """A foreign ``entry_key`` must answer 404, never 200 and never 403.

    Before the fix all three endpoints checked only the run. The run in these
    tests genuinely belongs to the caller, so the old code passed its only guard
    and then fetched a document owned by ``tenant-b``.
    """

    def test_get_of_a_foreign_entry_is_not_found(self):
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, text="Fremde Notiz")

        resp = client.get(_run_entry_url("foreign-1"))

        assert resp.status_code == 404, resp.text
        # AK-12 / §4.0: the existence of another tenant's record is not disclosed
        # by a distinguishable "forbidden".
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert "Fremde Notiz" not in resp.text

    def test_update_of_a_foreign_entry_is_not_found_and_changes_nothing(self):
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, text="Fremde Notiz")

        resp = client.put(_run_entry_url("foreign-1"), json={"text": "übernommen"})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert repo.docs["foreign-1"]["text"] == "Fremde Notiz"

    def test_delete_of_a_foreign_entry_is_not_found_and_keeps_the_document(self):
        # Deleting a diary entry is lead-only (REQ-049 §2.3); act as lead so the
        # request reaches the cross-tenant isolation check under test rather than
        # being stopped at the role gate.
        client, repo = _build(role=TenantRole.LEAD)
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY)

        resp = client.delete(_run_entry_url("foreign-1"))

        assert resp.status_code == 404, resp.text
        assert "foreign-1" in repo.docs

    def test_own_entry_still_works_through_the_run_path(self):
        client, repo = _build()
        repo.seed("own-1", tenant_key=TENANT_KEY, plant_key=PLANT_KEY)

        resp = client.get(_run_entry_url("own-1"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["key"] == "own-1"

    def test_entry_of_another_plant_is_not_addressable_through_this_url(self):
        # Same tenant, but the URL names a plant the entry does not belong to.
        client, repo = _build()
        repo.seed("own-1", tenant_key=TENANT_KEY, plant_key=OTHER_PLANT_KEY)

        resp = client.get(_run_entry_url("own-1", plant_key=PLANT_KEY))

        assert resp.status_code == 404, resp.text


class TestRunDiaryListingCrossTenantIsolation:
    """SEC-002 — the *listing* leaked what the single-entry reads had closed.

    ``GET /planting-runs/{run}/plants/{plant_key}/diary`` verified only the
    **run** against the caller's tenant and then passed the path's ``plant_key``
    straight into ``get_by_plant``, whose AQL traverses ``has_diary_entry`` from
    ``plant_instances/{plant_key}`` with **no** ``tenant_key`` predicate at all.
    Pairing a run of one's own with a foreign ``plant_key`` therefore returned
    another tenant's complete entries — ``text``, ``title``, ``tags``,
    ``measurements``, ``photo_refs``, ``created_by``, and since REQ-050 the
    ``analysis`` and the lease fields as well.

    The fix is in the data-access layer (``get_by_plant`` is tenant-mandatory)
    *and* at the endpoint (the plant is resolved against the caller's tenant, so
    a foreign plant answers 404 rather than a successful empty list — AK-12
    forbids distinguishing "not yours" from "does not exist", and an empty 200
    would still be a distinguishable answer for a plant that *has* no entries).
    """

    def test_a_foreign_plant_key_does_not_list_the_foreign_tenants_entries(self):
        client, repo = _build()
        repo.seed(
            "foreign-1",
            tenant_key=FOREIGN_TENANT_KEY,
            plant_key=FOREIGN_PLANT_KEY,
            text="FREMDE-NOTIZ-GEHEIM",
            title="Fremder Titel",
            tags=["fremd"],
            photo_refs=["foreign-photo"],
            created_by="user-of-tenant-b",
        )

        resp = client.get(_run_plant_diary_url(plant_key=FOREIGN_PLANT_KEY))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert "FREMDE-NOTIZ-GEHEIM" not in resp.text
        assert "foreign-photo" not in resp.text

    def test_the_repository_read_itself_refuses_the_foreign_tenants_entries(self):
        """The guard is a property of the storage layer, not of one endpoint.

        Asked directly — as the next endpoint that forgets the plant check would
        ask — the repository still hands back nothing of the other tenant.
        """
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, plant_key=PLANT_KEY, text="FREMDE-NOTIZ-GEHEIM")
        repo.seed("own-1", tenant_key=TENANT_KEY, plant_key=PLANT_KEY, text="Eigene Notiz")

        entries, total = repo.get_by_plant(PLANT_KEY, tenant_key=TENANT_KEY)

        assert [e.key for e in entries] == ["own-1"]
        assert total == 1
        # And the same read is refused outright without a tenant, rather than
        # silently spanning the installation.
        with pytest.raises(ValueError):
            repo.get_by_plant(PLANT_KEY, tenant_key="")

        # The endpoint on the caller's own plant keeps working.
        resp = client.get(_run_plant_diary_url(plant_key=PLANT_KEY))
        assert resp.status_code == 200, resp.text
        assert [e["key"] for e in resp.json()] == ["own-1"]

    def test_the_standalone_listing_is_tenant_scoped_too(self):
        # Same repository read, second prefix. Here the plant lookup already
        # answered 404, so only the storage-layer half is new — a foreign entry
        # that happens to hang off an *own* plant must not surface either.
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, plant_key=PLANT_KEY, text="FREMDE-NOTIZ-GEHEIM")
        repo.seed("own-1", tenant_key=TENANT_KEY, plant_key=PLANT_KEY)

        resp = client.get(_plant_url())

        assert resp.status_code == 200, resp.text
        assert [e["key"] for e in resp.json()] == ["own-1"]
        assert "FREMDE-NOTIZ-GEHEIM" not in resp.text

    def test_the_run_aggregation_is_tenant_scoped_too(self):
        # ``get_by_run`` enters through ``run_contains`` and had the same shape:
        # anchored on a foreign key, no ``tenant_key`` predicate. The run is
        # tenant-checked by the endpoint, so this is defence in depth — a
        # mis-parented entry must not ride along.
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, plant_key=PLANT_KEY, text="FREMDE-NOTIZ-GEHEIM")
        repo.seed("own-1", tenant_key=TENANT_KEY, plant_key=PLANT_KEY)

        resp = client.get(_run_diary_url())

        assert resp.status_code == 200, resp.text
        assert [r["diary_entry"]["key"] for r in resp.json()] == ["own-1"]
        assert "FREMDE-NOTIZ-GEHEIM" not in resp.text


# ── The standalone endpoints (REQ-013 §4.7) ──────────────────────────────────


class TestStandaloneDiaryCrud:
    def test_create_list_get_update_delete(self):
        # Full CRUD flow: the delete step is lead-only (REQ-049 §2.3), so run the
        # whole flow as a lead who can create, update and delete.
        client, repo = _build(role=TenantRole.LEAD)

        created = client.post(
            _plant_url(),
            json={
                "entry_type": "problem",
                "title": "Braune Flecken unten",
                "text": "Seit dem Umtopfen hängen die unteren Blätter.",
                "tags": ["blatt"],
                "photo_refs": [OWN_PHOTO],
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        entry_key = body["key"]
        assert body["plant_key"] == PLANT_KEY
        assert body["created_by"] == AUTHOR
        # A fresh entry is not marked (REQ-050 §5 default).
        assert body["analysis_state"] == "none"
        assert body["analysis"] is None

        listing = client.get(_plant_url())
        assert listing.status_code == 200
        assert [e["key"] for e in listing.json()] == [entry_key]

        single = client.get(_plant_url(f"/{entry_key}"))
        assert single.status_code == 200
        assert single.json()["title"] == "Braune Flecken unten"

        updated = client.put(_plant_url(f"/{entry_key}"), json={"title": "Korrigiert"})
        assert updated.status_code == 200, updated.text
        assert updated.json()["title"] == "Korrigiert"

        deleted = client.delete(_plant_url(f"/{entry_key}"))
        assert deleted.status_code == 204
        assert entry_key not in repo.docs

    def test_a_foreign_plant_is_not_found(self):
        client, _repo = _build()
        # The plant exists in the installation but belongs to another tenant.
        client.app.dependency_overrides[get_plant_instance_service] = lambda: FakePlantInstanceService(
            plants={PLANT_KEY: _plant(PLANT_KEY, tenant_key=FOREIGN_TENANT_KEY)}
        )

        resp = client.get(_plant_url())

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"

    def test_a_foreign_entry_on_an_own_plant_is_not_found(self):
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, plant_key=PLANT_KEY)

        resp = client.get(_plant_url("/foreign-1"))

        assert resp.status_code == 404, resp.text

    def test_update_cannot_smuggle_analysis_fields(self):
        # REQ-050 §2.2 — state transitions never travel through the generic
        # update; the request schema does not carry the fields and the service
        # refuses them even if they arrive.
        client, repo = _build()
        repo.seed("own-1", plant_key=PLANT_KEY)

        resp = client.put(
            _plant_url("/own-1"),
            json={"text": "neu", "analysis_state": "completed"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["analysis_state"] == "none"
        assert repo.docs["own-1"]["analysis_state"] == "none"


class TestPhotoRefsAreValidated:
    """SEC-003 — ``photo_refs`` was free-form input nothing ever looked at.

    Delivery is tenant-bound, so this was never a cross-tenant leak. **Inside**
    a shared tenant it defeated §7.2 outright: that rule ("markieren darf nur,
    wer den Eintrag selbst verfasst hat") is justified in the requirement by the
    sentence that a member must not hand "die Notizen **und Fotos** anderer
    Mitglieder" to a language model unasked. It held for the notes and not for
    the photos — a grower wrote an entry of their *own*, put another member's
    attachment id in it, marked it (author, gate opens) and their external model
    received the foreign image.
    """

    def test_own_diary_photo_is_accepted(self):
        client, _repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OWN_PHOTO]},
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["photo_refs"] == [OWN_PHOTO]

    def test_another_members_photo_is_refused(self):
        # The §7.2 rule, applied to the photo instead of only to the entry.
        client, _repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OTHER_MEMBERS_PHOTO]},
        )

        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "FORBIDDEN"

    def test_a_lead_may_attach_a_photo_they_did_not_upload(self):
        # Consistent with §7.2: a lead may already mark someone else's entry, so
        # refusing them the weaker action would make no sense.
        client, _repo = _build(role=TenantRole.LEAD, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OTHER_MEMBERS_PHOTO]},
        )

        assert resp.status_code == 201, resp.text

    def test_a_foreign_tenants_attachment_is_refused(self):
        client, _repo = _build(role=TenantRole.LEAD, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [FOREIGN_PHOTO]},
        )

        # Same answer as "does not exist" — the endpoint is not an oracle for
        # attachment ids of other tenants (AK-12).
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"

    def test_an_unknown_attachment_is_refused_the_same_way(self):
        client, _repo = _build(role=TenantRole.LEAD, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": ["does-not-exist"]},
        )

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"

    def test_a_non_diary_category_is_refused(self):
        # The caller's own gallery photo — right tenant, right uploader, wrong
        # category. §4.4 would hand its rendition to an external model all the
        # same, which is why the category is pinned server-side.
        client, _repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [GALLERY_PHOTO]},
        )

        assert resp.status_code == 422, resp.text

    def test_more_than_five_photos_are_refused(self):
        # REQ-013 §2.3. The schema catches it before the service does, which is
        # why the answer is FastAPI's 422 and not the service's error code.
        client, _repo = _build()

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OWN_PHOTO] * 6},
        )

        assert resp.status_code == 422, resp.text

    def test_an_update_cannot_smuggle_a_foreign_members_photo_in(self):
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR, photo_refs=[OWN_PHOTO])

        resp = client.put(_plant_url("/own-1"), json={"photo_refs": [OWN_PHOTO, OTHER_MEMBERS_PHOTO]})

        assert resp.status_code == 403, resp.text
        assert repo.docs["own-1"]["photo_refs"] == [OWN_PHOTO]

    def test_an_update_that_keeps_the_stored_photos_is_not_re_judged(self):
        """Only the *added* references are checked.

        Entries written before this rule may legitimately carry a reference the
        current rule would refuse. Re-judging them on every edit would turn those
        documents into documents nobody can edit any more — while the guard's
        purpose (stopping a member from *pulling in* a foreign photo) is served
        entirely by checking the delta.
        """
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR, photo_refs=[OTHER_MEMBERS_PHOTO])

        resp = client.put(_plant_url("/own-1"), json={"text": "neu", "photo_refs": [OTHER_MEMBERS_PHOTO]})

        assert resp.status_code == 200, resp.text
        assert resp.json()["text"] == "neu"

    def test_the_run_prefix_validates_too(self):
        # Both prefixes drive the same service, so both are covered — asserted
        # rather than assumed, because the run path is the one that historically
        # skipped checks the standalone path performed.
        client, _repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)

        resp = client.post(
            _run_plant_diary_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OTHER_MEMBERS_PHOTO]},
        )

        assert resp.status_code == 403, resp.text

    def test_a_service_without_an_attachment_catalogue_refuses_rather_than_waves_through(self):
        # The guard fails closed. A service assembled without the resolver cannot
        # judge a reference, and accepting it "for now" is how a guard ends up
        # inert in production while every test still passes.
        client, _repo = _build()
        client.app.dependency_overrides[get_plant_diary_service] = lambda: PlantDiaryService(
            diary_repo=FakeDiaryRepository()
        )

        resp = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Blatt.", "photo_refs": [OWN_PHOTO]},
        )

        assert resp.status_code == 422, resp.text


# ── Marking for analysis (AK-01, AK-02, AK-03, AK-19) ────────────────────────


class TestRequestAnalysis:
    def test_grower_marks_own_entry(self):
        # AK-01
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        resp = client.post(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["analysis_state"] == "requested"
        assert body["analysis_requested_by"] == AUTHOR
        assert body["analysis_requested_at"] is not None

    def test_viewer_cannot_mark(self):
        # AK-02 — a viewer reads state and result but never marks.
        client, repo = _build(role=TenantRole.VIEWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        resp = client.post(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "FORBIDDEN"
        assert repo.docs["own-1"]["analysis_state"] == "none"

    def test_viewer_can_still_read_the_entry(self):
        # AK-02, second half: reading stays open to a viewer.
        client, repo = _build(role=TenantRole.VIEWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, analysis_state=DiaryAnalysisState.COMPLETED.value)

        resp = client.get(_plant_url("/own-1"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["analysis_state"] == "completed"

    def test_grower_cannot_mark_someone_elses_entry(self):
        # §7.2 / AK-19 — in a shared tenant a grower marks only their own.
        client, repo = _build(role=TenantRole.GROWER, user_key=OTHER_USER)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        resp = client.post(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 403, resp.text
        assert repo.docs["own-1"]["analysis_state"] == "none"

    def test_lead_may_mark_someone_elses_entry(self):
        # §7.2 — marking a foreign entry is a lead decision.
        client, repo = _build(role=TenantRole.LEAD, user_key=OTHER_USER)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        resp = client.post(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["analysis_state"] == "requested"

    def test_unmark_while_requested(self):
        # AK-03, first half.
        client, repo = _build()
        repo.seed(
            "own-1",
            plant_key=PLANT_KEY,
            analysis_state=DiaryAnalysisState.REQUESTED.value,
            analysis_requested_by=AUTHOR,
            analysis_requested_at="2026-08-04T07:05:00+00:00",
        )

        resp = client.delete(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["analysis_state"] == "none"
        assert resp.json()["analysis_requested_by"] is None

    def test_unmark_while_in_progress_is_refused(self):
        # AK-03, second half — an agent already holds the entry; the data has
        # left the instance and "un-marking" would be a promise the server
        # cannot keep. It fails loudly instead of doing nothing.
        client, repo = _build()
        future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
        repo.seed(
            "own-1",
            plant_key=PLANT_KEY,
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_requested_by=AUTHOR,
            analysis_claimed_by="goose-laptop",
            analysis_claimed_at=datetime.now(UTC).isoformat(),
            analysis_lease_expires_at=future,
        )

        resp = client.delete(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "conflict.invalid_state"
        assert repo.docs["own-1"]["analysis_state"] == "in_progress"

    def test_marking_a_foreign_entry_is_not_found(self):
        # AK-12 again, on the write path.
        client, repo = _build()
        repo.seed("foreign-1", tenant_key=FOREIGN_TENANT_KEY, plant_key=PLANT_KEY)

        resp = client.post(_plant_url("/foreign-1/request-analysis"))

        assert resp.status_code == 404, resp.text
        assert repo.docs["foreign-1"]["analysis_state"] == "none"

    def test_marking_works_through_the_run_prefix_too(self):
        # REQ-013 §4.7 — both prefixes carry the pair.
        client, repo = _build()
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        marked = client.post(f"{_run_entry_url('own-1')}/request-analysis")
        assert marked.status_code == 200, marked.text
        assert marked.json()["analysis_state"] == "requested"

        cancelled = client.delete(f"{_run_entry_url('own-1')}/request-analysis")
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["analysis_state"] == "none"

    def test_pre_req050_entry_without_state_can_be_marked(self):
        # AK-26 on the write path: an entry stored before REQ-050 has no
        # ``analysis_state`` attribute at all.
        client, repo = _build()
        doc = repo.seed("legacy-1", plant_key=PLANT_KEY, created_by=AUTHOR)
        doc.pop("analysis_state")

        resp = client.post(_plant_url("/legacy-1/request-analysis"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["analysis_state"] == "requested"

    def test_re_marking_a_completed_entry_keeps_the_previous_result(self):
        # AK-21 — the old result stays visible while the entry waits again.
        client, repo = _build()
        repo.seed(
            "own-1",
            plant_key=PLANT_KEY,
            created_by=AUTHOR,
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis={
                "summary": "Vermutlich Staunässe.",
                "findings": [],
                "recommended_actions": [],
                "analyzed_photo_ids": [],
                "model": "claude-opus-5",
                "recipe_version": "1.0.0",
                "analyzed_at": "2026-08-04T07:14:52+00:00",
                "disclaimer": "Hypothese.",
            },
        )

        resp = client.post(_plant_url("/own-1/request-analysis"))

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["analysis_state"] == "requested"
        assert body["analysis"]["summary"] == "Vermutlich Staunässe."


# ── One truth, one answer: the lease correction on every read path (AK-06) ────


def _seed_crashed_agent(repo, key: str = "own-1", **fields) -> None:
    """An entry an agent claimed and then died on: the lease has run out.

    Stored state is ``in_progress``; the deadline is in the past. Nobody is
    analysing this entry — it is back in the work queue and any agent may claim
    it (``include_stale``).
    """
    repo.seed(
        key,
        plant_key=PLANT_KEY,
        created_by=AUTHOR,
        analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
        analysis_requested_by=AUTHOR,
        analysis_requested_at="2026-08-04T07:05:00+00:00",
        analysis_claimed_by="goose-laptop",
        analysis_claimed_at=(datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
        analysis_lease_expires_at=(datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
        **fields,
    )


class TestExpiredLeaseReadsTheSameEverywhere:
    """The core of this work package.

    The overview corrected a run-out lease back to ``requested``; the
    plant-instance and run-scoped reads projected the stored ``in_progress``
    unchanged. The same entry therefore said "wird analysiert" in the tab and
    "wartet auf Analyse" in the overview — and the tab was the one lying: no
    agent held the entry any more (AK-06).
    """

    def test_every_read_path_answers_requested(self):
        client, repo = _build()
        _seed_crashed_agent(repo)

        single = client.get(_plant_url("/own-1"))
        listing = client.get(_plant_url())
        run_single = client.get(_run_entry_url("own-1"))
        run_listing = client.get(_run_diary_url())
        overview = client.get(_overview_url())

        assert single.json()["analysis_state"] == "requested", single.text
        assert listing.json()[0]["analysis_state"] == "requested", listing.text
        assert run_single.json()["analysis_state"] == "requested", run_single.text
        assert run_listing.json()[0]["diary_entry"]["analysis_state"] == "requested", run_listing.text
        assert overview.json()["items"][0]["analysis_state"] == "requested", overview.text

    def test_the_lease_evidence_stays_visible(self):
        # The stored state is not published a second time — it is derivable from
        # the lease fields, which are projected raw. A "requested" entry that
        # still names a holder whose deadline has passed *is* the crashed-agent
        # case, and a diagnostician can still see it.
        client, repo = _build()
        _seed_crashed_agent(repo)

        body = client.get(_plant_url("/own-1")).json()

        assert body["analysis_claimed_by"] == "goose-laptop"
        assert body["analysis_lease_expires_at"] is not None

    def test_reading_does_not_write(self):
        # The reset happens on the next *write* to the entry; a read that
        # corrected the stored document would make the work queue depend on
        # somebody having opened the right page.
        client, repo = _build()
        _seed_crashed_agent(repo)
        rev_before = repo.docs["own-1"]["_rev"]

        client.get(_plant_url("/own-1"))
        client.get(_overview_url())

        assert repo.docs["own-1"]["analysis_state"] == "in_progress"
        assert repo.docs["own-1"]["_rev"] == rev_before

    def test_a_live_lease_still_reads_as_in_progress(self):
        # The correction must not swallow the honest case: an agent that is
        # holding the entry right now.
        client, repo = _build()
        repo.seed(
            "own-1",
            plant_key=PLANT_KEY,
            created_by=AUTHOR,
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
            analysis_claimed_at=datetime.now(UTC).isoformat(),
            analysis_lease_expires_at=(datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        )

        assert client.get(_plant_url("/own-1")).json()["analysis_state"] == "in_progress"
        assert client.get(_overview_url()).json()["items"][0]["analysis_state"] == "in_progress"

    def test_a_claim_without_a_deadline_reads_as_requested(self):
        # A partial write can leave ``in_progress`` without a deadline. Reading
        # that as "never expires" would be the permanent block the lease exists
        # to prevent, so it counts as expired on every path.
        client, repo = _build()
        repo.seed(
            "own-1",
            plant_key=PLANT_KEY,
            created_by=AUTHOR,
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
        )

        assert client.get(_plant_url("/own-1")).json()["analysis_state"] == "requested"
        assert client.get(_overview_url()).json()["items"][0]["analysis_state"] == "requested"


# ── can_request_analysis on every construction site (§7.2, AK-18a) ────────────


class TestCanRequestAnalysisIsFilledEverywhere:
    """The flag is per **user and entry**, so every path must ask for itself.

    ``DiaryEntryResponse`` is built in exactly two places — the shared
    projection in ``diary_schemas.py`` and, until this work package, a
    hand-written copy inside ``list_run_diary_entries``. The mixed-authorship
    tests below are the ones that fail if a path ever fills the flag with one
    blanket value for a whole page.
    """

    def test_author_with_a_writing_role_may_mark(self):
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_plant_url("/own-1")).json()["can_request_analysis"] is True

    def test_observer_never_may(self):
        # §6 — a viewer reads state and result but never marks, so the control
        # is not offered in the first place (AK-02, AK-19).
        client, repo = _build(role=TenantRole.VIEWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_plant_url("/own-1")).json()["can_request_analysis"] is False

    def test_foreign_author_without_a_lead_role_may_not(self):
        # §7.2 — handing someone else's observations and photos to a language
        # model is a lead decision.
        client, repo = _build(role=TenantRole.GROWER, user_key=OTHER_USER)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_plant_url("/own-1")).json()["can_request_analysis"] is False

    def test_a_lead_may_mark_a_foreign_entry(self):
        client, repo = _build(role=TenantRole.LEAD, user_key=OTHER_USER)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_plant_url("/own-1")).json()["can_request_analysis"] is True

    def test_a_listing_judges_each_entry_separately(self):
        # The trap this test exists for: one verdict computed once and stamped
        # onto every row of the page.
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("mine", plant_key=PLANT_KEY, created_by=AUTHOR, created_at="2026-08-03T10:00:00+00:00")
        repo.seed("theirs", plant_key=PLANT_KEY, created_by=OTHER_USER, created_at="2026-08-03T09:00:00+00:00")

        verdicts = {e["key"]: e["can_request_analysis"] for e in client.get(_plant_url()).json()}

        assert verdicts == {"mine": True, "theirs": False}

    def test_the_run_aggregation_judges_each_entry_separately(self):
        # Same page, the *other* construction site: ``list_run_diary_entries``
        # assembled the response from a raw dict of its own.
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("mine", plant_key=PLANT_KEY, created_by=AUTHOR, created_at="2026-08-03T10:00:00+00:00")
        repo.seed("theirs", plant_key=PLANT_KEY, created_by=OTHER_USER, created_at="2026-08-03T09:00:00+00:00")

        rows = client.get(_run_diary_url()).json()
        verdicts = {r["diary_entry"]["key"]: r["diary_entry"]["can_request_analysis"] for r in rows}

        assert verdicts == {"mine": True, "theirs": False}
        # The plant context of the aggregation survives the refactoring.
        assert {r["plant_key"] for r in rows} == {PLANT_KEY}

    def test_creating_and_marking_answer_with_the_flag_too(self):
        # Every endpoint that returns an entry returns the same shape; a client
        # that renders the answer of a POST must not have to guess the verdict.
        client, _repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)

        created = client.post(
            _plant_url(),
            json={"entry_type": "observation", "text": "Untere Blätter hängen."},
        )
        assert created.status_code == 201, created.text
        assert created.json()["can_request_analysis"] is True

        marked = client.post(_plant_url(f"/{created.json()['key']}/request-analysis"))
        assert marked.status_code == 200, marked.text
        assert marked.json()["can_request_analysis"] is True

    def test_the_flag_is_not_an_authorisation(self):
        # AK-18a — the endpoint re-evaluates §7.2 whatever the client believed.
        # A caller that reads ``false`` and posts anyway is refused, and the
        # document is untouched.
        client, repo = _build(role=TenantRole.GROWER, user_key=OTHER_USER)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_plant_url("/own-1")).json()["can_request_analysis"] is False

        refused = client.post(_plant_url("/own-1/request-analysis"))

        assert refused.status_code == 403, refused.text
        assert refused.json()["error_code"] == "FORBIDDEN"
        assert repo.docs["own-1"]["analysis_state"] == "none"

    def test_a_viewer_is_refused_on_the_run_prefix_as_well(self):
        # The second prefix carries the same pair: display aid and enforcement.
        client, repo = _build(role=TenantRole.VIEWER, user_key=AUTHOR)
        repo.seed("own-1", plant_key=PLANT_KEY, created_by=AUTHOR)

        assert client.get(_run_entry_url("own-1")).json()["can_request_analysis"] is False

        refused = client.post(f"{_run_entry_url('own-1')}/request-analysis")

        assert refused.status_code == 403, refused.text
        assert repo.docs["own-1"]["analysis_state"] == "none"
