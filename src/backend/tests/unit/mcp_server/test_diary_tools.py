"""REQ-050 §4 — the five diary AI-analysis MCP tools.

These tests are the guard on the **external** contract: ``kamerplanter-goose``
is written against REQ-050 §4 without reading our source, so a renamed ``data``
key or a swallowed error code breaks a repository that cannot be grepped from
here.

Two decisions shape the setup:

* The **real** :class:`PlantDiaryService` runs against an in-memory repository
  rather than a hand-written fake service. A fake that raises whatever the test
  asks for would prove that the tool re-raises what it is given — not that a
  second claim actually loses the compare-and-set (AK-05) or that a stale lease
  actually reappears. The state machine is exercised, not simulated.
* Where the property lives on the **wire** rather than in the tool's return
  value — the ``details`` object of an error, the ordering of image content
  blocks — the assertion runs through the transport's own
  ``_tool_result`` / ``_tool_error_result``. A tool-level assertion would pass
  while the recipe still saw nothing.
"""

from __future__ import annotations

import inspect
import json
from base64 import b64decode, b64encode
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from app.api.v1.mcp.router import _tool_error_result, _tool_result
from app.common.datetimes import now_utc
from app.common.enums import DiaryAnalysisState, DiaryEntryType, TenantRole
from app.common.exceptions import (
    AttachmentNotFoundError,
    ContractError,
    ForbiddenError,
    KamerplanterError,
    NotFoundError,
)
from app.domain.engines.storage.thumbnail_generator import metadata_keys
from app.domain.models.plant_diary_entry import DiaryAnalysis, DiaryFinding, PlantDiaryEntry
from app.domain.services.plant_diary_service import (
    ANALYSIS_DISCLAIMER,
    PlantDiaryService,
    lease_expired,
)
from app.mcp_server.base import McpToolError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.diary import (
    AddPlantDiaryEntry,
    ClaimDiaryAnalysis,
    GetDiaryEntry,
    GetDiaryEntryPhotos,
    ListPendingDiaryAnalyses,
    SubmitDiaryAnalysis,
)
from tests.support.diary_fakes import FakeDiaryRepository

TENANT = "home"
FOREIGN_TENANT = "allotment"

#: The two classes that may carry a published §4.0 contract code out of a tool.
#:
#: ``ContractError`` is what the domain raises (``conflict.already_claimed``,
#: ``validation.error``); ``McpToolError`` is what the MCP layer itself raises
#: (``payload.too_large``, ``validation.tenant_required``). They are siblings,
#: not subclasses, and the transport deliberately treats them alike — it copies
#: ``error_details`` by attribute rather than by class. Pinning one of the two
#: here would assert *which* class a condition happens to use, which is not the
#: contract; ``error_code`` and ``error_details``, asserted below, are. An
#: unrelated ``NotFoundError`` still fails these tests, which is the point.
CONTRACT_FAILURE = (ContractError, McpToolError)


# ── In-memory persistence ─────────────────────────────────────────────────────
class _DiaryRepo(FakeDiaryRepository):
    """The shared repository double plus the one read it leaves unimplemented.

    Extending rather than re-writing matters here: the revision counter and the
    compare-and-set of ``update_fields_checked`` are what make AK-05 an actual
    lost race instead of a scripted answer, and a second hand-written copy of
    that fencing would be free to drift away from the AQL it stands in for.
    """

    def list_pending_analyses(
        self,
        tenant_key: str,
        *,
        limit: int = 20,
        include_stale: bool = True,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        moment = now or now_utc()
        matches: list[PlantDiaryEntry] = []
        for doc in self.docs.values():
            if doc.get("tenant_key") != tenant_key:
                continue
            entry = PlantDiaryEntry(**dict(doc))
            waiting = entry.analysis_state == DiaryAnalysisState.REQUESTED
            if waiting or (include_stale and lease_expired(entry, moment)):
                matches.append(entry)
        # Mirrors the repository's ``SORT doc.analysis_requested_at ASC`` (AK-04).
        matches.sort(key=lambda e: e.analysis_requested_at or datetime.min.replace(tzinfo=UTC))
        return matches[:limit], len(matches)


# ── Plant / catalogue context ─────────────────────────────────────────────────
class _Plant:
    def __init__(self, key: str, tenant: str = TENANT) -> None:
        self.key = key
        self.tenant_key = tenant
        self.instance_id = "HOCHBEETA_TOM_05"
        self.plant_name = "Tomate Beet 2 #05"
        self.species_key = "solanum_lycopersicum"
        self.cultivar_key = "san_marzano"
        self.location_key = "loc-1"
        self.current_phase_key = "flowering-entry"
        self.current_phase_started_at = datetime(2026, 7, 12, tzinfo=UTC)
        self.planted_on = date(2026, 4, 18)


class _PlantService:
    def __init__(self, plants: list[_Plant] | None = None) -> None:
        self._plants = {p.key: p for p in (plants or [])}
        self.seen_tenant: str | None = None

    def get_plant(self, key: str, tenant_key: str = "") -> _Plant:
        self.seen_tenant = tenant_key
        plant = self._plants.get(key)
        if plant is None or plant.tenant_key != tenant_key:
            raise NotFoundError("PlantInstance", key)
        return plant


class _Species:
    scientific_name = "Solanum lycopersicum"


class _Cultivar:
    name = "San Marzano"


class _SpeciesService:
    def get_species(self, key: str) -> _Species:
        if key != "solanum_lycopersicum":
            raise NotFoundError("Species", key)
        return _Species()

    def get_cultivar(self, key: str) -> _Cultivar:
        if key != "san_marzano":
            raise NotFoundError("Cultivar", key)
        return _Cultivar()


class _Location:
    name = "Hochbeet A"


class _SiteService:
    def get_location(self, key: str, tenant_key: str = "") -> _Location:
        if key != "loc-1":
            raise NotFoundError("Location", key)
        return _Location()


class _PhaseService:
    def get_current_phase(self, plant_key: str) -> dict[str, Any]:
        return {"phase": "flowering", "phase_key": "flowering-entry"}


# ── Attachments / renditions ──────────────────────────────────────────────────
async def _stream(data: bytes):
    yield data


class _Attachment:
    def __init__(self, key: str, mime_type: str = "image/jpeg") -> None:
        self.key = key
        self.mime_type = mime_type
        self.storage_key = f"t/{TENANT}/diary/2026/08/{key}.jpg"


class _Attachments:
    """Serves renditions and **refuses** to serve originals (AK-07).

    ``open_stream`` — the original-bytes path — raises instead of returning data.
    A fallback to the original would otherwise be invisible: the response looks
    the same, only it now carries a 25 MB EXIF-bearing photo to a third-party
    model. The guard is here rather than in one test so *every* test in this file
    covers it.
    """

    def __init__(self) -> None:
        self.records: dict[str, _Attachment] = {}
        self.renditions: dict[tuple[str, int], bytes] = {}
        self.seen_tenants: list[str] = []
        self.original_reads: list[str] = []
        #: Every rendition actually fetched, in order (SEC-004). The cost of a
        #: photo call is measured here rather than inferred from the response —
        #: a response that fails with ``payload.too_large`` says nothing about
        #: how many objects were read to produce it.
        self.thumbnail_reads: list[tuple[str, int]] = []

    def add(self, key: str, *, mime_type: str = "image/jpeg", **sizes: bytes) -> None:
        self.records[key] = _Attachment(key, mime_type)
        for name, data in sizes.items():
            self.renditions[key, int(name.removeprefix("px"))] = data

    def get_attachment(self, attachment_id: str, tenant_key: str) -> _Attachment:
        self.seen_tenants.append(tenant_key)
        attachment = self.records.get(attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError(attachment_id)
        return attachment

    async def open_thumbnail_stream(self, attachment: _Attachment, size: int):
        raw = self.renditions.get((attachment.key, size))
        if raw is None:
            raise NotFoundError("object", f"{attachment.storage_key}_t{size}.webp")
        self.thumbnail_reads.append((attachment.key, size))
        return _stream(raw)

    async def open_stream(self, attachment: _Attachment):
        self.original_reads.append(attachment.key)
        raise AssertionError("AK-07: an MCP photo delivery must never read the original object.")


# ── Fixtures / builders ───────────────────────────────────────────────────────
def _membership(tenant: str = TENANT, role: TenantRole = TenantRole.GROWER) -> McpTenantMembership:
    return McpTenantMembership(tenant_key=tenant, tenant_slug=tenant, tenant_name=tenant.title(), role=role)


def _entry(
    key: str,
    *,
    tenant: str = TENANT,
    state: DiaryAnalysisState = DiaryAnalysisState.REQUESTED,
    requested_at: datetime | None = None,
    created_at: datetime | None = None,
    photos: list[str] | None = None,
    text: str = "Seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer.",
    title: str | None = "Braune Flecken unten",
) -> PlantDiaryEntry:
    return PlantDiaryEntry(
        _key=key,
        tenant_key=tenant,
        plant_key="plant-1",
        entry_type=DiaryEntryType.PROBLEM,
        title=title,
        text=text,
        tags=["blatt", "substrat"],
        measurements={"height_cm": 84, "leaf_count": 22},
        photo_refs=photos or [],
        created_by="user-4471023",
        created_at=created_at or datetime(2026, 8, 3, 18, 22, 11, tzinfo=UTC),
        analysis_state=state,
        analysis_requested_at=requested_at or datetime(2026, 8, 4, 7, 5, tzinfo=UTC),
    )


class _World:
    """One assembled tenant world: repo, real service, and a bound ToolContext."""

    def __init__(self, *, role: TenantRole = TenantRole.GROWER) -> None:
        self.repo = _DiaryRepo()
        self.service = PlantDiaryService(diary_repo=self.repo)
        self.plants = _PlantService([_Plant("plant-1")])
        self.attachments = _Attachments()
        membership = _membership(role=role)
        principal = McpPrincipal(account_key="sa-1", display_name="goose", memberships=(membership,))
        self.ctx = ToolContext(
            principal,
            membership,
            services={
                "plant_diary_service": self.service,
                "attachment_service": self.attachments,
                "plant_instance_service": self.plants,
                "species_service": _SpeciesService(),
                "site_service": _SiteService(),
                "phase_service": _PhaseService(),
            },
        )


@pytest.fixture
def world() -> _World:
    return _World()


# ══ AK-04 — the work queue ═══════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_ak04_queue_is_tenant_scoped_oldest_first_and_free_of_content(world: _World) -> None:
    # created_at order is the *reverse* of requested_at order, so a tool that
    # sorted by the wrong field could not accidentally pass.
    world.repo.create(
        _entry(
            "late",
            requested_at=datetime(2026, 8, 4, 9, 0, tzinfo=UTC),
            created_at=datetime(2026, 8, 1, tzinfo=UTC),
            text="LATE-SECRET-TEXT",
        )
    )
    world.repo.create(
        _entry(
            "early",
            requested_at=datetime(2026, 8, 4, 7, 0, tzinfo=UTC),
            created_at=datetime(2026, 8, 3, tzinfo=UTC),
            text="EARLY-SECRET-TEXT",
            photos=["ph-1", "ph-2"],
        )
    )
    world.repo.create(_entry("foreign", tenant=FOREIGN_TENANT, text="FOREIGN-SECRET-TEXT"))

    tool = ListPendingDiaryAnalyses()
    response = await tool.run(world.ctx, tool.Input())

    keys = [item["entry_key"] for item in response.data["entries"]]
    assert keys == ["early", "late"], "oldest requested_at first (AK-04)"
    assert response.data["total"] == 2, "total counts only the acting tenant"

    wire = json.dumps(_tool_result(response), default=str)
    for secret in ("EARLY-SECRET-TEXT", "LATE-SECRET-TEXT", "FOREIGN-SECRET-TEXT"):
        assert secret not in wire, "the work queue carries no free text (§7.3, AK-04)"
    assert "photo_refs" not in wire
    assert response.content_blocks == [], "the work queue carries no images"
    # The projection itself, spelled out — these are the published keys.
    assert set(response.data["entries"][0]) == {
        "entry_key",
        "plant_key",
        "plant_name",
        "species_name",
        "entry_type",
        "title",
        "created_at",
        "requested_at",
        "photo_count",
        "analysis_state",
    }
    assert response.data["entries"][0]["photo_count"] == 2
    assert response.data["entries"][0]["requested_at"] == "2026-08-04T07:00:00Z", "§4.0 Z-suffix"


@pytest.mark.asyncio
async def test_ak04_total_is_independent_of_limit(world: _World) -> None:
    for index in range(5):
        world.repo.create(_entry(f"e{index}", requested_at=datetime(2026, 8, 4, 7, index, tzinfo=UTC)))

    tool = ListPendingDiaryAnalyses()
    response = await tool.run(world.ctx, tool.Input(limit=2))

    assert len(response.data["entries"]) == 2
    assert response.data["total"] == 5, "an agent must learn how much is left (§4.1)"


@pytest.mark.asyncio
async def test_an_empty_queue_is_not_an_error(world: _World) -> None:
    tool = ListPendingDiaryAnalyses()
    response = await tool.run(world.ctx, tool.Input())
    assert response.data == {"entries": [], "total": 0}


@pytest.mark.asyncio
async def test_a_stale_lease_is_reported_as_claimable_again(world: _World) -> None:
    entry = _entry("stale", state=DiaryAnalysisState.IN_PROGRESS)
    entry.analysis_claimed_by = "goose-crashed"
    entry.analysis_lease_expires_at = now_utc() - timedelta(minutes=5)
    world.repo.create(entry)

    tool = ListPendingDiaryAnalyses()
    response = await tool.run(world.ctx, tool.Input())

    # AK-06: the stored value still says in_progress, but the entry is claimable
    # — reporting the stored state would tell the agent to skip what the queue
    # just handed it.
    assert response.data["entries"][0]["analysis_state"] == "requested"


@pytest.mark.asyncio
async def test_limit_above_the_ceiling_is_a_validation_error(world: _World) -> None:
    tool = ListPendingDiaryAnalyses()
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(limit=101))
    assert excinfo.value.error_code == "validation.error"


# ══ AK-05 — claiming ═════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_ak05_first_claim_wins_and_the_second_is_refused(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2"]))
    tool = ClaimDiaryAnalysis()

    first = await tool.execute(world.ctx, tool.Input(entry_key="e-1", worker_id="goose-laptop"))
    assert set(first.data) == {"entry_key", "lease_token", "lease_expires_at", "photo_count"}
    assert first.data["photo_count"] == 2
    assert first.data["lease_token"]
    assert first.data["lease_expires_at"].endswith("Z")

    stored_before = dict(world.repo.docs["e-1"])
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(world.ctx, tool.Input(entry_key="e-1", worker_id="goose-desktop"))

    assert excinfo.value.error_code == "conflict.already_claimed"
    # §4.2: the agent must be able to decide whether to come back later.
    assert excinfo.value.error_details["claimed_by"] == "goose-laptop"
    assert excinfo.value.error_details["lease_expires_at"]
    assert world.repo.docs["e-1"] == stored_before, "a refused claim changes nothing"

    # …and the details survive all the way onto the wire, which is where the
    # recipe reads them. A tool-level assertion alone would pass while the
    # transport dropped them.
    wire = _tool_error_result(excinfo.value)
    assert wire["isError"] is True
    assert wire["structuredContent"]["error_code"] == "conflict.already_claimed"
    assert wire["structuredContent"]["details"]["claimed_by"] == "goose-laptop"


@pytest.mark.asyncio
async def test_an_expired_lease_may_be_claimed_again(world: _World) -> None:
    entry = _entry("e-1", state=DiaryAnalysisState.IN_PROGRESS)
    entry.analysis_claimed_by = "goose-crashed"
    entry.analysis_lease_expires_at = now_utc() - timedelta(minutes=1)
    world.repo.create(entry)

    tool = ClaimDiaryAnalysis()
    response = await tool.execute(world.ctx, tool.Input(entry_key="e-1", worker_id="goose-fresh"))

    assert response.data["entry_key"] == "e-1"
    assert world.repo.docs["e-1"]["analysis_claimed_by"] == "goose-fresh"


@pytest.mark.asyncio
async def test_a_dry_run_claim_does_not_claim(world: _World) -> None:
    world.repo.create(_entry("e-1"))
    tool = ClaimDiaryAnalysis()

    preview = await tool.preview(world.ctx, tool.Input(entry_key="e-1", worker_id="goose", dry_run=True))

    assert "lease_token" not in preview.data, "a dry run must not hand out a usable lease"
    assert world.repo.docs["e-1"]["analysis_state"] == "requested"


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"worker_id": ""}, "worker_id"),
        ({"worker_id": "   "}, "worker_id"),
        ({"worker_id": "goose", "lease_seconds": 3601}, "lease_seconds"),
        ({"worker_id": "goose", "lease_seconds": 0}, "lease_seconds"),
    ],
)
@pytest.mark.asyncio
async def test_claim_argument_rules(world: _World, kwargs: dict[str, Any], field: str) -> None:
    world.repo.create(_entry("e-1"))
    tool = ClaimDiaryAnalysis()
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(world.ctx, tool.Input(entry_key="e-1", **kwargs))
    assert excinfo.value.error_code == "validation.error"
    assert excinfo.value.error_details.get("field") == field


@pytest.mark.asyncio
async def test_a_dry_run_claim_applies_the_same_argument_rules(world: _World) -> None:
    world.repo.create(_entry("e-1"))
    tool = ClaimDiaryAnalysis()
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.preview(world.ctx, tool.Input(entry_key="e-1", worker_id="", dry_run=True))
    assert excinfo.value.error_code == "validation.error"


# ══ §4.3 — the entry itself ══════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_get_diary_entry_returns_the_published_shape_without_image_data(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2"]))
    tool = GetDiaryEntry()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert set(response.data) == {
        "entry_key",
        "entry_type",
        "title",
        "text",
        "tags",
        "measurements",
        "photo_refs",
        "created_at",
        "created_by",
        "analysis_state",
        "analysis",
        "analysis_error",
        "plant",
    }
    assert response.data["entry_type"] == "problem"
    # §4.3: the bare user_key as stored — no ``user/`` collection prefix is
    # invented on the way out, because none is stored.
    assert response.data["created_by"] == "user-4471023"
    # Nothing analysed yet: stable keys carrying null, not absent keys.
    assert response.data["analysis"] is None
    assert response.data["analysis_error"] is None
    assert response.data["measurements"] == {"height_cm": 84, "leaf_count": 22}
    assert response.data["photo_refs"] == ["ph-1", "ph-2"]
    assert response.data["created_at"] == "2026-08-03T18:22:11Z"
    assert response.data["plant"] == {
        "plant_key": "plant-1",
        "plant_name": "Tomate Beet 2 #05",
        "instance_id": "HOCHBEETA_TOM_05",
        "species_key": "solanum_lycopersicum",
        "species_name": "Solanum lycopersicum",
        "cultivar_name": "San Marzano",
        "current_phase": "flowering",
        "phase_started_at": "2026-07-12T00:00:00Z",
        "location_name": "Hochbeet A",
        "planted_on": "2026-04-18",
    }
    # §4.3 is the text half of the split: no image blocks, no Base-64 anywhere.
    assert response.content_blocks == []
    assert world.attachments.original_reads == []


@pytest.mark.asyncio
async def test_missing_plant_fields_come_as_null_not_as_absent_keys(world: _World) -> None:
    entry = _entry("e-1")
    entry.plant_key = "gone"
    world.repo.create(entry)
    tool = GetDiaryEntry()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    plant = response.data["plant"]
    # §4.3: "Felder …, die am Datensatz fehlen, kommen als null, nicht als
    # ausgelassener Schlüssel" — the shape must not depend on the data.
    assert set(plant) == {
        "plant_key",
        "plant_name",
        "instance_id",
        "species_key",
        "species_name",
        "cultivar_name",
        "current_phase",
        "phase_started_at",
        "location_name",
        "planted_on",
    }
    assert plant["plant_name"] is None
    assert plant["species_name"] is None


@pytest.mark.asyncio
async def test_measurements_of_an_entry_without_any_is_an_object(world: _World) -> None:
    entry = _entry("e-1")
    entry.measurements = None
    world.repo.create(entry)
    tool = GetDiaryEntry()
    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))
    assert response.data["measurements"] == {}


@pytest.mark.asyncio
async def test_ak21_a_repeat_analysis_can_read_the_previous_result(world: _World) -> None:
    """§4.3 carries the persisted result, so a re-analysis is not blind (AK-21).

    An entry that was analysed once and marked again sits in ``requested`` with
    its previous result still on it. If ``get_diary_entry`` dropped that result,
    the agent could reach it through **none** of the five tools — it would see
    only the state and start over without knowing what the last run concluded.
    """

    entry = _entry("e-1", state=DiaryAnalysisState.REQUESTED, photos=["ph-1"])
    entry.analysis = DiaryAnalysis(
        summary="Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
        findings=[
            DiaryFinding(
                label="Staunässe / Wurzelstress",
                confidence=0.72,
                rationale="Saurer Substratgeruch und hängende untere Blätter.",
            )
        ],
        recommended_actions=["Substrat abtrocknen lassen", "Drainage prüfen"],
        analyzed_photo_ids=["ph-1"],
        model="claude-opus-5",
        recipe_version="1.0.0",
        analyzed_at=datetime(2026, 8, 4, 7, 14, 52, tzinfo=UTC),
        disclaimer=ANALYSIS_DISCLAIMER,
    )
    world.repo.create(entry)
    tool = GetDiaryEntry()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    # The §4.5 wire shape, key for key — the same object the submit tool mirrors
    # back, including the server-set disclaimer and the Z-suffixed timestamp.
    assert response.data["analysis"] == {
        "summary": "Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
        "findings": [
            {
                "label": "Staunässe / Wurzelstress",
                "confidence": 0.72,
                "rationale": "Saurer Substratgeruch und hängende untere Blätter.",
            }
        ],
        "recommended_actions": ["Substrat abtrocknen lassen", "Drainage prüfen"],
        "analyzed_photo_ids": ["ph-1"],
        "model": "claude-opus-5",
        "recipe_version": "1.0.0",
        "analyzed_at": "2026-08-04T07:14:52Z",
        "disclaimer": ANALYSIS_DISCLAIMER,
    }
    assert response.data["analysis_error"] is None
    # Still the text half of the split: no images travel with the prior result.
    assert response.content_blocks == []


@pytest.mark.asyncio
async def test_a_previous_failure_is_readable_too_and_carries_no_analysis(world: _World) -> None:
    entry = _entry("e-1", state=DiaryAnalysisState.FAILED)
    entry.analysis_error = "Das Modell hat die Bilder nicht verarbeiten können."
    world.repo.create(entry)
    tool = GetDiaryEntry()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert response.data["analysis"] is None
    assert response.data["analysis_error"] == "Das Modell hat die Bilder nicht verarbeiten können."
    assert response.data["analysis_state"] == "failed"


# ══ AK-07 / AK-09 / content_index — photos ═══════════════════════════════════
@pytest.mark.asyncio
async def test_ak07_only_renditions_are_delivered_never_the_original(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1"]))
    world.attachments.add("ph-1", px1280=b"WEBP-1280-BYTES" * 16, px512=b"WEBP-512" * 8)
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert world.attachments.original_reads == [], "the original object was never opened (AK-07)"
    assert [block.type for block in response.content_blocks] == ["image"]
    assert response.content_blocks[0].mime_type == "image/webp"
    # The delivered bytes are the rendition's, not the original's.
    assert b64decode(response.content_blocks[0].data) == b"WEBP-1280-BYTES" * 16
    assert response.data["photos"][0]["byte_size"] == len(b"WEBP-1280-BYTES" * 16)
    assert response.data["size"] == 1280


@pytest.mark.asyncio
async def test_ak07_a_missing_rendition_never_falls_back_to_the_original(world: _World) -> None:
    # The failure this guards: "rendition missing → serve the original instead"
    # looks like a helpful fallback and ships EXIF/GPS to a third-party model.
    world.repo.create(_entry("e-1", photos=["ph-1"]))
    world.attachments.add("ph-1")  # record exists, no renditions at all
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert world.attachments.original_reads == []
    assert response.data["photos"] == []
    assert response.content_blocks == []
    assert response.data["pending"] == [{"photo_id": "ph-1", "status": "thumbnail_pending"}]


@pytest.mark.asyncio
async def test_ak09_missing_rendition_is_pending_the_rest_succeeds_and_generation_is_triggered(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.tasks import storage_tasks

    dispatched: list[tuple[str, str]] = []
    monkeypatch.setattr(
        storage_tasks.generate_thumbnails,
        "delay",
        lambda attachment_id, tenant_key: dispatched.append((attachment_id, tenant_key)),
    )

    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2", "ph-3"]))
    world.attachments.add("ph-1", px1280=b"A" * 90)
    world.attachments.add("ph-2")  # rendition not generated yet
    world.attachments.add("ph-3", px1280=b"C" * 60)
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    # The call stays successful — a hard failure would block an entry with two
    # ready photos over one missing thumbnail.
    assert _tool_result(response)["isError"] is False
    assert [p["photo_id"] for p in response.data["photos"]] == ["ph-1", "ph-3"]
    assert response.data["pending"] == [{"photo_id": "ph-2", "status": "thumbnail_pending"}]
    assert len(response.content_blocks) == 2
    # …and the generation was actually kicked off, against the real task object.
    assert dispatched == [("ph-2", TENANT)]


def _webp_rendition(*, with_metadata: bool) -> bytes:
    """A real 512 px WebP rendition, optionally carrying EXIF/GPS and an ICC profile.

    Built rather than fixtured because the property under test is a property of
    the *bytes*: ``metadata_keys`` parses the container, so a placeholder like
    ``b"WEBP"`` proves nothing either way.
    """
    import io

    from PIL import Image, ImageCms

    image = Image.new("RGB", (512, 384), (34, 120, 60))
    params: dict[str, object] = {"quality": 82, "method": 4}
    if with_metadata:
        exif = Image.Exif()
        exif[0x010F] = "ACME"
        exif[0x0110] = "SuperCam 9000"
        exif[0x8825] = {1: "N", 2: (52.0, 31.0, 12.0), 3: "E", 4: (13.0, 24.0, 36.0)}
        params["exif"] = exif.tobytes()
        params["icc_profile"] = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", **params)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_sec006_a_rendition_carrying_metadata_is_not_delivered(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC-006 — the delivery path asserts the property it rests its case on.

    §4.4 / §7.3 permit handing a photo to a third-party model **because** the
    rendition carries no EXIF, no GPS and no device identity. The generator
    enforces that and fails closed, but ``_load_renditions`` reads raw bytes out
    of object storage: an object written by anything other than the generator —
    a restore, an operator copy, a future second producer — is outside that
    guarantee. Such a rendition is treated exactly like a missing one and
    regenerated; it is never delivered.

    The clean rendition beside it must still travel, so the guard is a filter and
    not an outage.
    """
    from app.tasks import storage_tasks

    dispatched: list[tuple[str, str]] = []
    monkeypatch.setattr(
        storage_tasks.generate_thumbnails,
        "delay",
        lambda attachment_id, tenant_key: dispatched.append((attachment_id, tenant_key)),
    )

    tainted = _webp_rendition(with_metadata=True)
    clean = _webp_rendition(with_metadata=False)
    # Precondition of the test, asserted rather than assumed.
    assert metadata_keys(tainted), "the fixture must actually carry metadata"
    assert metadata_keys(clean) == []

    world.repo.create(_entry("e-1", photos=["ph-tainted", "ph-clean"]))
    world.attachments.add("ph-tainted", px512=tainted)
    world.attachments.add("ph-clean", px512=clean)
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1", size=512))

    assert [p["photo_id"] for p in response.data["photos"]] == ["ph-clean"]
    assert response.data["pending"] == [{"photo_id": "ph-tainted", "status": "thumbnail_pending"}]
    assert dispatched == [("ph-tainted", TENANT)]
    # And the bytes really did not travel.
    wire = json.dumps(_tool_result(response), default=str)
    assert b64encode(tainted).decode() not in wire


@pytest.mark.asyncio
async def test_a_photo_whose_attachment_is_gone_is_not_reported_as_pending_forever(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-gone"]))
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    # Deviation from the §4.4 example vocabulary, on purpose: promising
    # "thumbnail_pending" for a record that no longer exists would send the agent
    # into an endless retry. ``pending`` non-empty still means "not complete",
    # which is the check §4.4 tells a recipe to make.
    assert response.data["pending"] == [{"photo_id": "ph-gone", "status": "unavailable"}]
    assert response.data["photos"] == []


@pytest.mark.asyncio
async def test_content_index_addresses_the_content_array_not_the_photos_list(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2", "ph-3"]))
    world.attachments.add("ph-1", px1280=b"one" * 30)
    world.attachments.add("ph-2", px1280=b"two" * 30)
    world.attachments.add("ph-3", px1280=b"three" * 30)
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))
    wire = _tool_result(response)

    assert [p["content_index"] for p in response.data["photos"]] == [1, 2, 3]
    assert wire["content"][0]["type"] == "text", "the summary stays the leading block"
    for photo, expected in zip(
        response.data["photos"],
        [b"one" * 30, b"two" * 30, b"three" * 30],
        strict=True,
    ):
        block = wire["content"][photo["content_index"]]
        assert block["type"] == "image"
        assert block["mimeType"] == "image/webp"
        assert block["data"] == b64encode(expected).decode()
    # Base-64 never leaks into the structured half — it would double every
    # photo on the wire and land in the persisted idempotency record.
    structured = json.dumps(wire["structuredContent"])
    for expected in (b"one" * 30, b"two" * 30, b"three" * 30):
        assert b64encode(expected).decode() not in structured


@pytest.mark.asyncio
async def test_an_entry_without_photos_is_a_success(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=[]))
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1"))
    wire = _tool_result(response)

    # Four of the six entry types are usually recorded without a photo — a recipe
    # that treated this as a failure would break on ordinary data (§4.4).
    assert wire["isError"] is False
    assert response.data["photos"] == []
    assert response.data["pending"] == []
    assert len(wire["content"]) == 1
    assert wire["content"][0]["type"] == "text"


@pytest.mark.parametrize("size", [128, 0, 1024, 2048])
@pytest.mark.asyncio
async def test_an_unoffered_rendition_size_is_a_validation_error(world: _World, size: int) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1"]))
    tool = GetDiaryEntryPhotos()
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1", size=size))
    assert excinfo.value.error_code == "validation.error"
    assert excinfo.value.error_details.get("field") == "size"


@pytest.mark.asyncio
async def test_a_photo_id_from_another_entry_is_a_validation_error(world: _World) -> None:
    world.repo.create(_entry("e-1", photos=["ph-1"]))
    world.attachments.add("ph-1", px1280=b"x" * 30)
    world.attachments.add("ph-foreign", px1280=b"y" * 30)
    tool = GetDiaryEntryPhotos()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1", photo_ids=["ph-foreign"]))

    assert excinfo.value.error_code == "validation.error"
    assert excinfo.value.error_details.get("field") == "photo_ids"


# ══ AK-08 — the payload ceiling ══════════════════════════════════════════════
@pytest.mark.asyncio
async def test_ak08_over_the_ceiling_fails_loudly_and_names_a_size_that_fits(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "mcp_max_image_payload_mb", 1)

    big = b"B" * (700 * 1024)  # Base-64 ≈ 933 KB each → two exceed 1 MB
    small = b"s" * (50 * 1024)
    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2"]))
    world.attachments.add("ph-1", px1280=big, px512=small)
    world.attachments.add("ph-2", px1280=big, px512=small)
    tool = GetDiaryEntryPhotos()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    # Never a shortened success: an agent that believes it saw both photos while
    # one was dropped draws wrong conclusions and never finds out (AK-08).
    assert excinfo.value.error_code == "payload.too_large"
    assert excinfo.value.error_details["photo_ids"] == ["ph-1", "ph-2"]
    assert excinfo.value.error_details["suggested_size"] == 512

    wire = _tool_error_result(excinfo.value)
    assert wire["isError"] is True
    assert wire["structuredContent"]["details"]["photo_ids"] == ["ph-1", "ph-2"]
    assert wire["structuredContent"]["details"]["suggested_size"] == 512

    # …and the suggestion is honest: the retry it names actually succeeds.
    ok = await tool.run(world.ctx, tool.Input(entry_key="e-1", size=512))
    assert [p["photo_id"] for p in ok.data["photos"]] == ["ph-1", "ph-2"]


@pytest.mark.asyncio
async def test_sec004_a_repeated_photo_id_is_fetched_once(world: _World) -> None:
    """SEC-004 — the selection check said *whether*, never *how often*.

    ``_select_photo_ids`` only asserted membership, so ``[<valid id>] * 2000``
    passed it and the loader fetched the same rendition two thousand times. The
    payload ceiling did not help: it was applied to the assembled result, i.e.
    after all the work had been paid for.
    """
    world.repo.create(_entry("e-1", photos=["ph-1", "ph-2"]))
    world.attachments.add("ph-1", px1280=b"one" * 30)
    world.attachments.add("ph-2", px1280=b"two" * 30)
    tool = GetDiaryEntryPhotos()

    response = await tool.run(world.ctx, tool.Input(entry_key="e-1", photo_ids=["ph-1"] * 2000 + ["ph-2"]))

    assert world.attachments.thumbnail_reads == [("ph-1", 1280), ("ph-2", 1280)]
    assert [p["photo_id"] for p in response.data["photos"]] == ["ph-1", "ph-2"]
    # The first occurrence keeps the caller's position — ``content_index`` maps
    # onto that order.
    assert [p["content_index"] for p in response.data["photos"]] == [1, 2]


@pytest.mark.asyncio
async def test_sec004_the_read_stops_at_the_budget_instead_of_loading_everything(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC-004 — the budget is carried into the loop, not applied to its result.

    Five photos of ~930 KB Base-64 each against a 1 MB ceiling: the second one
    already crosses it, so the remaining three must never be fetched. The
    refusal itself is unchanged (AK-08) — the call fails with
    ``payload.too_large`` and is never a shortened success.
    """
    from app.config.settings import settings

    monkeypatch.setattr(settings, "mcp_max_image_payload_mb", 1)

    photos = [f"ph-{i}" for i in range(5)]
    world.repo.create(_entry("e-1", photos=photos))
    for photo_id in photos:
        world.attachments.add(photo_id, px1280=b"B" * (700 * 1024), px512=b"s" * (50 * 1024))
    tool = GetDiaryEntryPhotos()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert excinfo.value.error_code == "payload.too_large"
    at_1280 = [photo_id for photo_id, size in world.attachments.thumbnail_reads if size == 1280]
    assert at_1280 == ["ph-0", "ph-1"], "the loop stops the moment the budget is gone"
    # ``photo_ids`` still names the whole selection: it answers which images the
    # call concerned, which is what the agent has to change, and it must not
    # depend on how far the read happened to get.
    assert excinfo.value.error_details["photo_ids"] == photos


def test_sec008_zero_means_refused_configuration_not_an_unlimited_payload() -> None:
    """SEC-008 — ``MCP_MAX_IMAGE_PAYLOAD_MB=0`` used to switch the ceiling off.

    The reader clamped negatives to zero and the guard returned early on a
    non-positive ceiling, so both ``0`` and any negative value meant *unlimited*:
    the opposite of what an operator setting zero intends, and the amplifier for
    any unbounded-assembly bug. There is no sensible "off" for this ceiling, so
    the value is rejected at construction.
    """
    import pydantic

    from app.config.settings import Settings

    for refused in (0, -1):
        with pytest.raises(pydantic.ValidationError):
            Settings(mcp_max_image_payload_mb=refused)

    assert Settings(mcp_max_image_payload_mb=1).mcp_max_image_payload_mb == 1


@pytest.mark.asyncio
async def test_sec008_a_small_ceiling_actually_binds(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The other half of SEC-008: the smallest configurable ceiling must be a
    # ceiling. Under the old reader an operator could only *raise* the limit; the
    # one value that read as "throttle hard" read as "no limit at all".
    from app.config.settings import settings

    monkeypatch.setattr(settings, "mcp_max_image_payload_mb", 1)

    world.repo.create(_entry("e-1", photos=["ph-1"]))
    world.attachments.add("ph-1", px1280=b"H" * (1500 * 1024))
    tool = GetDiaryEntryPhotos()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert excinfo.value.error_code == "payload.too_large"
    assert excinfo.value.error_details["max_payload_bytes"] == 1024 * 1024


@pytest.mark.asyncio
async def test_ak08_suggested_size_is_null_when_no_offered_rendition_fits(
    world: _World,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "mcp_max_image_payload_mb", 1)

    huge = b"H" * (1500 * 1024)
    world.repo.create(_entry("e-1", photos=["ph-1"]))
    world.attachments.add("ph-1", px1280=huge, px512=huge)
    tool = GetDiaryEntryPhotos()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.run(world.ctx, tool.Input(entry_key="e-1"))

    assert excinfo.value.error_code == "payload.too_large"
    # The key stays present with an explicit null rather than disappearing, so
    # the structure is stable across responses (§4.0). Recommending 512 px
    # unverified would send the agent into a second call that fails identically.
    assert excinfo.value.error_details["suggested_size"] is None
    assert "suggested_size" in _tool_error_result(excinfo.value)["structuredContent"]["details"]


# ══ AK-10 / AK-11 / AK-22 — submitting ═══════════════════════════════════════
async def _claimed(world: _World, *, photos: list[str] | None = None) -> str:
    world.repo.create(_entry("e-1", photos=photos or ["ph-1", "ph-2"]))
    claim = await ClaimDiaryAnalysis().execute(
        world.ctx,
        ClaimDiaryAnalysis.Input(entry_key="e-1", worker_id="goose-laptop"),
    )
    return claim.data["lease_token"]


@pytest.mark.asyncio
async def test_ak10_a_valid_lease_persists_the_result_and_mirrors_the_server_disclaimer(world: _World) -> None:
    token = await _claimed(world)
    tool = SubmitDiaryAnalysis()

    response = await tool.execute(
        world.ctx,
        tool.Input(
            entry_key="e-1",
            lease_token=token,
            status="completed",
            summary="Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
            findings=[{"label": "Staunässe / Wurzelstress", "confidence": 0.72, "rationale": "Saurer Geruch."}],
            recommended_actions=["Substrat abtrocknen lassen", "Drainage prüfen"],
            analyzed_photo_ids=["ph-1", "ph-2"],
            model="claude-opus-5",
            recipe_version="1.0.0",
            # AK-11: an agent-supplied disclaimer is impossible — the field does
            # not exist in the input schema at all.
        ),
    )

    assert response.data["analysis_state"] == "completed"
    analysis = response.data["analysis"]
    assert set(analysis) == {
        "summary",
        "findings",
        "recommended_actions",
        "analyzed_photo_ids",
        "model",
        "recipe_version",
        "analyzed_at",
        "disclaimer",
    }
    assert analysis["findings"][0]["confidence"] == 0.72
    assert analysis["analyzed_at"].endswith("Z")
    assert "Sprachmodell" in analysis["disclaimer"], "the disclaimer is the server's (AK-11)"
    # …and it is what actually stands on the entry.
    assert world.repo.docs["e-1"]["analysis"]["disclaimer"] == analysis["disclaimer"]
    assert world.repo.docs["e-1"]["analysis_state"] == "completed"


@pytest.mark.asyncio
async def test_ak10_a_failed_submission_records_the_error_instead_of_an_analysis(world: _World) -> None:
    token = await _claimed(world)
    tool = SubmitDiaryAnalysis()

    response = await tool.execute(
        world.ctx,
        tool.Input(entry_key="e-1", lease_token=token, status="failed", error="Model refused the image."),
    )

    assert response.data["analysis_state"] == "failed"
    assert response.data["analysis_error"] == "Model refused the image."
    assert "analysis" not in response.data


@pytest.mark.asyncio
async def test_ak10_submitting_without_a_claim_is_refused(world: _World) -> None:
    world.repo.create(_entry("e-1"))
    tool = SubmitDiaryAnalysis()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(
            world.ctx,
            tool.Input(entry_key="e-1", lease_token="anything", status="completed", summary="x"),
        )

    assert excinfo.value.error_code == "conflict.not_claimed"
    assert world.repo.docs["e-1"].get("analysis") is None


@pytest.mark.asyncio
async def test_ak10_a_foreign_lease_token_is_refused(world: _World) -> None:
    await _claimed(world)
    tool = SubmitDiaryAnalysis()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(
            world.ctx,
            tool.Input(entry_key="e-1", lease_token="not-the-token", status="completed", summary="x"),
        )

    assert excinfo.value.error_code == "conflict.lease_expired"
    assert world.repo.docs["e-1"].get("analysis") is None


@pytest.mark.asyncio
async def test_ak10_an_expired_lease_is_refused(world: _World) -> None:
    token = await _claimed(world)
    # Move the deadline into the past without touching the rest of the lease.
    world.repo.docs["e-1"]["analysis_lease_expires_at"] = (now_utc() - timedelta(seconds=1)).isoformat()
    tool = SubmitDiaryAnalysis()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(
            world.ctx,
            tool.Input(entry_key="e-1", lease_token=token, status="completed", summary="x"),
        )

    assert excinfo.value.error_code == "conflict.lease_expired"


@pytest.mark.asyncio
async def test_a_dry_run_submission_does_not_persist(world: _World) -> None:
    token = await _claimed(world)
    tool = SubmitDiaryAnalysis()

    preview = await tool.preview(
        world.ctx,
        tool.Input(entry_key="e-1", lease_token=token, status="completed", summary="ok", dry_run=True),
    )

    assert preview.data["disclaimer"]
    assert world.repo.docs["e-1"].get("analysis") is None
    assert world.repo.docs["e-1"]["analysis_state"] == "in_progress"


# AK-22 — every rejection of §4.5, one test case each.
_LONG = "x" * 2001


@pytest.mark.parametrize(
    ("case", "payload"),
    [
        ("completed_without_summary", {"status": "completed"}),
        ("completed_with_blank_summary", {"status": "completed", "summary": "   "}),
        ("failed_without_error", {"status": "failed"}),
        ("failed_with_blank_error", {"status": "failed", "error": "  "}),
        ("summary_too_long", {"status": "completed", "summary": _LONG}),
        (
            "confidence_above_one",
            {
                "status": "completed",
                "summary": "ok",
                "findings": [{"label": "l", "confidence": 1.5, "rationale": "r"}],
            },
        ),
        (
            "confidence_below_zero",
            {
                "status": "completed",
                "summary": "ok",
                "findings": [{"label": "l", "confidence": -0.1, "rationale": "r"}],
            },
        ),
        (
            "finding_label_too_long",
            {
                "status": "completed",
                "summary": "ok",
                "findings": [{"label": "y" * 201, "confidence": 0.5, "rationale": "r"}],
            },
        ),
        (
            "finding_rationale_too_long",
            {
                "status": "completed",
                "summary": "ok",
                "findings": [{"label": "l", "confidence": 0.5, "rationale": _LONG}],
            },
        ),
        (
            "too_many_findings",
            {
                "status": "completed",
                "summary": "ok",
                "findings": [{"label": f"l{i}", "confidence": 0.5, "rationale": "r"} for i in range(11)],
            },
        ),
        (
            "too_many_recommended_actions",
            {"status": "completed", "summary": "ok", "recommended_actions": [f"a{i}" for i in range(11)]},
        ),
        (
            "unknown_analyzed_photo_id",
            {"status": "completed", "summary": "ok", "analyzed_photo_ids": ["ph-elsewhere"]},
        ),
        ("model_too_long", {"status": "completed", "summary": "ok", "model": "m" * 201}),
        ("recipe_version_too_long", {"status": "completed", "summary": "ok", "recipe_version": "v" * 51}),
    ],
)
@pytest.mark.asyncio
async def test_ak22_submission_input_rules(world: _World, case: str, payload: dict[str, Any]) -> None:
    token = await _claimed(world)
    tool = SubmitDiaryAnalysis()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(world.ctx, tool.Input(entry_key="e-1", lease_token=token, **payload))

    assert excinfo.value.error_code == "validation.error", case
    assert world.repo.docs["e-1"].get("analysis") is None, f"{case} must not persist anything"
    # The entry stays claimed, so the agent can correct and retry within its lease.
    assert world.repo.docs["e-1"]["analysis_state"] == "in_progress", case


@pytest.mark.asyncio
async def test_ak22_too_many_analyzed_photo_ids(world: _World) -> None:
    # Every id hangs on the entry, so the "id not attached to this entry" rule
    # cannot be what fires — it is ``DiaryAnalysis.analyzed_photo_ids``'
    # max_length of 5 (§4.5). The ids repeat because a diary entry itself now
    # carries at most five photos (REQ-013 §2.3, enforced on the domain model
    # since SEC-003), so an entry with six distinct photos cannot be built.
    token = await _claimed(world, photos=["ph-1"])
    tool = SubmitDiaryAnalysis()

    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.execute(
            world.ctx,
            tool.Input(
                entry_key="e-1",
                lease_token=token,
                status="completed",
                summary="ok",
                analyzed_photo_ids=["ph-1"] * 6,
            ),
        )

    assert excinfo.value.error_code == "validation.error"


@pytest.mark.asyncio
async def test_ak22_a_dry_run_rejects_the_same_payloads(world: _World) -> None:
    token = await _claimed(world)
    tool = SubmitDiaryAnalysis()
    with pytest.raises(CONTRACT_FAILURE) as excinfo:
        await tool.preview(
            world.ctx,
            tool.Input(entry_key="e-1", lease_token=token, status="completed", dry_run=True),
        )
    assert excinfo.value.error_code == "validation.error"


# ══ AK-12 — a foreign tenant is 'not found', never 'permission denied' ═══════
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda ctx: GetDiaryEntry().run(ctx, GetDiaryEntry.Input(entry_key="e-foreign")),
            id="get_diary_entry",
        ),
        pytest.param(
            lambda ctx: GetDiaryEntryPhotos().run(ctx, GetDiaryEntryPhotos.Input(entry_key="e-foreign")),
            id="get_diary_entry_photos",
        ),
        pytest.param(
            lambda ctx: ClaimDiaryAnalysis().execute(
                ctx, ClaimDiaryAnalysis.Input(entry_key="e-foreign", worker_id="goose")
            ),
            id="claim_diary_analysis",
        ),
        pytest.param(
            lambda ctx: SubmitDiaryAnalysis().execute(
                ctx,
                SubmitDiaryAnalysis.Input(entry_key="e-foreign", lease_token="t", status="completed", summary="ok"),
            ),
            id="submit_diary_analysis",
        ),
    ],
)
async def test_ak12_an_entry_of_another_tenant_is_not_found(world: _World, call) -> None:
    world.repo.create(_entry("e-foreign", tenant=FOREIGN_TENANT, photos=["ph-1"]))

    with pytest.raises(KamerplanterError) as excinfo:
        await call(world.ctx)

    exc = excinfo.value
    # Distinguishing "exists but forbidden" from "does not exist" would turn the
    # interface into an oracle for other tenants' records (§4.0, AK-12).
    assert isinstance(exc, NotFoundError), f"expected not_found, got {type(exc).__name__}"
    assert not isinstance(exc, ForbiddenError)
    assert exc.error_code == "ENTITY_NOT_FOUND"
    assert "allotment" not in exc.message, "the answer must not reveal the other tenant"


@pytest.mark.asyncio
async def test_ak12_the_work_queue_never_leaks_a_foreign_entry(world: _World) -> None:
    world.repo.create(_entry("e-foreign", tenant=FOREIGN_TENANT))
    tool = ListPendingDiaryAnalyses()
    response = await tool.run(world.ctx, tool.Input())
    assert response.data == {"entries": [], "total": 0}


def test_ak07_the_module_holds_no_route_to_an_original_at_all() -> None:
    """A static guard so the two AK-07 tests above cannot go vacuous.

    They assert that ``open_stream`` was *not* called — negative evidence, which
    stays true if someone later adds a fallback behind a condition the tests do
    not hit. These are the three ways to reach an original from here; none of
    them may appear in the module at all.
    """

    from app.mcp_server.tools import diary

    source = inspect.getsource(diary)
    for forbidden in ("open_stream", "get_download", "presign_download", ".storage_key"):
        assert forbidden not in source, (
            f"'{forbidden}' reaches the original upload; MCP delivers renditions only (AK-07, AC-S7)."
        )
    assert "open_thumbnail_stream" in source


# ══ Palette wiring ═══════════════════════════════════════════════════════════
def test_the_three_services_are_declared_on_the_context_not_resolved_ad_hoc(world: _World) -> None:
    """The tools' dependencies are visible on :class:`ToolContext`, as for the shipped palette.

    Reaching through ``ctx._service("plant_diary_service")`` works, but it makes
    a tool's dependencies invisible at the one place that lists them — and the
    fake injection below is keyed on exactly these names either way, so the
    declared property costs nothing and documents the coupling.
    """

    from app.mcp_server.tools import diary

    assert world.ctx.plant_diary_service is world.service
    assert world.ctx.attachment_service is world.attachments
    assert isinstance(world.ctx.phase_service, _PhaseService)

    assert "ctx._service(" not in inspect.getsource(diary), (
        "the diary tools resolve their services through the declared properties"
    )


@pytest.mark.parametrize("service_name", ["plant_diary_service", "attachment_service", "phase_service"])
def test_each_new_context_property_names_a_real_dependency_factory(service_name: str) -> None:
    """Every test above injects a fake, so the production wiring is never run here.

    A typo in the resolved name would therefore stay invisible until the first
    real MCP call in a deployed instance. The factory's existence is the cheapest
    thing that catches it.
    """

    from app.common import dependencies as deps

    assert callable(getattr(deps, f"get_{service_name}", None)), (
        f"ToolContext.{service_name} resolves 'get_{service_name}', which does not exist"
    )


def test_the_diary_tools_are_registered_with_the_declared_permissions() -> None:
    from app.mcp_server.registry import load_tools

    registry = load_tools()
    expected = {
        "list_pending_diary_analyses": ("mcp.read", False),
        "get_diary_entry": ("mcp.read", False),
        "get_diary_entry_photos": ("mcp.read", False),
        "claim_diary_analysis": ("mcp.write", True),
        "submit_diary_analysis": ("mcp.write", True),
        # REQ-033 §2.2 — outside the analysis contract, same permission class.
        "add_plant_diary_entry": ("mcp.write", True),
    }
    specs = {spec.name: spec for spec in registry.specs()}
    for name, (permission, write) in expected.items():
        assert name in specs, f"{name} is not in the palette"
        assert specs[name].permission == permission
        assert specs[name].write is write
        assert specs[name].destructive is False
        # Tenant binding is what keeps a diary bot inside one garden.
        assert registry.get(name).tenant_scoped is True


# ══ REQ-033 §2.2 — add_plant_diary_entry (REQ-050 §9, O-04) ══════════════════
#
# The sixth tool is not part of the analysis contract: it lets an agent
# *document* an observation. What the tests below pin is exactly that boundary —
# the entry is written, and nothing about the analysis state machine moves.
@pytest.mark.asyncio
async def test_add_entry_writes_it_against_the_acting_tenant_and_principal(world: _World) -> None:
    tool = AddPlantDiaryEntry()
    response = await tool.execute(
        world.ctx,
        tool.Input(
            plant_key="plant-1",
            text="Untere Blätter hängen seit dem Umtopfen.",
            title="Nach dem Umtopfen",
            tags=["substrat"],
            measurements={"height_cm": 84},
        ),
    )

    stored = world.repo.get_or_raise(response.data["entry_key"])
    assert stored.tenant_key == TENANT, "the entry belongs to the bound tenant, never to a caller-supplied one"
    assert stored.created_by == "sa-1", "authorship is the principal's account, not an argument"
    assert stored.plant_key == "plant-1"
    assert stored.text == "Untere Blätter hängen seit dem Umtopfen."
    assert stored.tags == ["substrat"]
    assert stored.measurements == {"height_cm": 84}
    assert world.plants.seen_tenant == TENANT, "the plant is resolved against the acting tenant (SEC-001)"


@pytest.mark.asyncio
async def test_add_entry_defaults_to_observation_and_leaves_the_analysis_machine_alone(world: _World) -> None:
    """Writing an entry must not enqueue it: marking is a user action (§1.3).

    An agent that could mark its own entries would create its own work — and the
    consent gate in §7.1 sits on the *marking* path, so it would also be walked
    past. The assertion on the queue is the one that matters; the state field
    alone could be satisfied by an entry that is somehow pending anyway.
    """

    tool = AddPlantDiaryEntry()
    response = await tool.execute(world.ctx, tool.Input(plant_key="plant-1", text="Erste Blüte offen."))

    stored = world.repo.get_or_raise(response.data["entry_key"])
    assert stored.entry_type == DiaryEntryType.OBSERVATION, "default entry type"
    assert stored.analysis_state == DiaryAnalysisState.NONE
    assert stored.analysis_requested_at is None
    assert stored.analysis is None
    assert response.data["analysis_state"] == "none", "the response says so too, so a recipe stops polling"

    queue = ListPendingDiaryAnalyses()
    pending = await queue.run(world.ctx, queue.Input())
    assert pending.data["total"] == 0, "a written entry is not waiting for analysis"


@pytest.mark.asyncio
async def test_add_entry_refuses_a_foreign_plant_with_not_found(world: _World) -> None:
    """AK-12 shape: a plant in another tenant is indistinguishable from no plant."""

    world.plants._plants["foreign-plant"] = _Plant("foreign-plant", tenant=FOREIGN_TENANT)
    tool = AddPlantDiaryEntry()
    args = tool.Input(plant_key="foreign-plant", text="Sollte nie geschrieben werden.")

    for stage in (tool.preview, tool.execute):
        with pytest.raises(NotFoundError):
            await stage(world.ctx, args)
    assert world.repo.docs == {}, "neither the preview nor the refused write persisted anything"


@pytest.mark.asyncio
async def test_add_entry_preview_describes_the_effect_without_writing(world: _World) -> None:
    tool = AddPlantDiaryEntry()
    response = await tool.preview(
        world.ctx,
        tool.Input(plant_key="plant-1", entry_type=DiaryEntryType.PROBLEM, text="Spinnmilben an der Unterseite."),
    )

    assert world.repo.docs == {}, "a dry run persists nothing"
    assert response.data == {"plant_key": "plant-1", "entry_type": "problem", "title": None}
    assert "Would add" in response.summary


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("text", ""),
        ("text", "x" * 5001),
        ("title", "t" * 201),
    ],
)
def test_add_entry_rejects_out_of_bound_input_before_any_write(field: str, value: str) -> None:
    """The bounds are declared on the Input model, so they reach the recipe twice.

    Once as a rejection — the dispatcher turns this into ``validation.error``
    before a handler runs — and once in the published ``inputSchema``, asserted
    below. Relying on the domain model alone would produce an unhandled failure
    at persistence time instead.
    """

    from pydantic import ValidationError as PydanticValidationError

    payload = {"plant_key": "plant-1", "text": "gültig", field: value}
    with pytest.raises(PydanticValidationError):
        AddPlantDiaryEntry.Input(**payload)


def test_add_entry_publishes_its_bounds_and_carries_no_photo_refs() -> None:
    """O-04 was decided *without* ``photo_refs`` — this holds that decision.

    ``_require_attachable_photos`` (SEC-003) only lets an author attach a photo
    they uploaded themselves, unless they are a tenant lead. A service account
    never uploads, so the field would be a near-permanent rejection; MCP has no
    upload path to make it useful either. ``extra: forbid`` already refuses the
    argument — this test states that the refusal is intended.
    """

    schema = AddPlantDiaryEntry.Input.model_json_schema()
    properties = schema["properties"]

    assert "photo_refs" not in properties
    with pytest.raises(Exception, match="photo_refs"):
        AddPlantDiaryEntry.Input(plant_key="plant-1", text="x", photo_refs=["ph-1"])

    assert properties["text"]["maxLength"] == 5000
    assert properties["text"]["minLength"] == 1
    assert properties["title"]["anyOf"][0]["maxLength"] == 200
    # The write envelope every state-changing tool carries (§2.6).
    for field in ("tenant", "dry_run", "idempotency_key"):
        assert field in properties
