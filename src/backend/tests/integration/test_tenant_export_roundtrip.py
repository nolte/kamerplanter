"""#2138 (REQ-056 AK-30, AK-32, AK-33, AK-34) — a tenant archive survives the trip, and an import touches no one else.

Only a real server can say whether the export reads what the tenant-erasure predicate
selects, whether the import's new keys and rewritten references land, and whether a
restore into a database that holds another tenant leaves that tenant alone. Measured
here through :class:`TenantExportService` with the real ArangoDB repositories, a
real local-fs object store and the step-up verifier replaced (the step-up rule is the
unit tier's, ``test_tenant_export_service.py``).

* **Roundtrip (AK-32).** Tenant A is exported from one database, the archive is
  imported through the full request → task path into an empty one (catalogue only),
  the new tenant is exported again. The second archive equals the first once every
  source key is substituted by its new key — the substitution here is a plain
  string replacement over every value, independent of the import's declarations, so
  a reference the import failed to rewrite shows up as a difference. Unmapped
  accounts read ``_anonymized``.
* **Restore beside another tenant (AK-33).** A is exported, then lost, then B keeps
  working; the archive is imported into the *same* database. No document of B
  changes (``_rev``), no pre-existing key is reused.
* **What never leaves (AK-30).** E-mail addresses, password and API-key hashes,
  invitation tokens, integration secrets and B's rows are seeded with markers; none
  is in the archive bytes.
* **Refusals (AK-34).** A missing global catalogue row refuses the import with the
  list and writes nothing; a failure mid-write leaves no tenant and no row behind.
* **A crafted archive (PR #2267 review SEC-001/-002/-003).** Rows without the source
  tenant's key and an edge between two global catalogue rows are refused before a
  single document is written; an archive this installation did not sign imports as
  unverified.
* **Unreachable until done, swept when dead (SEC-007).** The new tenant is
  ``importing`` with inactive memberships while rows are written, ``active`` after;
  an import whose run died is erased through the tenant-erasure inventory by the
  hourly sweep.

Locally::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_tenant_export_roundtrip.py -v
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.async_bridge import run_async
from app.common.exceptions import MemberLimitReachedError, TenantImportRefusedError
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.data_access.arango.tenant_export_store import (
    ArangoTenantDataStore,
    ArangoTenantExportRequestRepository,
    ArangoTenantImportRequestRepository,
)
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.timescale.null_observation_repository import NullObservationRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.tenant_export_engine import TenantArchiveWriter, read_tenant_archive
from app.domain.models.tenant_export import TenantImportMemberGrant, TenantImportRequest
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.tenant_export_service import StepUpFactors, TenantExportService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

SOURCE_DB = run_database_name("tenant_export_source")
TARGET_DB = run_database_name("tenant_export_target")

A, B = "ten-a", "ten-b"
#: The bytes of the seeded photo; the attachment row states their true size and hash (the import recomputes both).
PHOTO = b"JPEG"
LEAD, GROWER, ADMIN = "u-lead", "u-grower", "u-admin"
SECRETS = {
    "email": "lead-secret@example.com",
    "password_hash": "$2b$12$PASSWORDHASHMARKERxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "api_key_hash": "APIKEYHASHMARKER0123456789",
    "invitation_token": "INVITATIONTOKENMARKER",
    "provider_secret": "PROVIDERSECRETMARKER",
    "weather_key_ref": "gAAAAAWEATHERKEYREFMARKER",
    "foreign_row": "ROW-OF-TENANT-B-MARKER",
}


# ── databases ─────────────────────────────────────────────────────────


def _database(name: str):
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(name):
        system.delete_database(name)
    system.create_database(name)
    database = client.db(name, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    return system, database


@pytest.fixture
def source(tmp_path):
    system, database = _database(SOURCE_DB)
    _seed_catalogue(database)
    yield database
    system.delete_database(SOURCE_DB)


@pytest.fixture
def target():
    system, database = _database(TARGET_DB)
    _seed_catalogue(database)
    yield database
    system.delete_database(TARGET_DB)


def _seed_catalogue(db) -> None:
    db.collection("botanical_families").insert({"_key": "fam-1", "name": "Solanaceae"})
    db.collection("species").insert(
        {"_key": "sp-global", "scientific_name": "Solanum lycopersicum", "tenant_key": "", "family_key": "fam-1"}
    )
    db.collection("growth_phases").insert({"_key": "gp-veg", "name": "vegetative"})
    db.collection("pests").insert({"_key": "pest-1", "scientific_name": "Tetranychus urticae"})
    db.collection("users").insert(
        {"_key": ADMIN, "email": "admin@example.com", "display_name": "Admin", "account_type": "human"}
    )
    db.collection("tenants").insert(
        {"_key": "platform", "name": "Platform", "slug": "platform", "owner_user_key": ADMIN, "is_platform": True}
    )
    db.collection("memberships").insert(
        {"user_key": ADMIN, "tenant_key": "platform", "role": "lead", "admin_scopes": ["management"], "is_active": True}
    )


def _seed_tenant(db, tenant: str, *, marker: str = "") -> dict[str, str]:
    """A small but connected tenant: places, plants, diary, IPM, a task, a photo and edges."""
    db.collection("tenants").insert(
        {
            "_key": tenant,
            "name": f"Garden {tenant}",
            "slug": f"garden-{tenant}",
            "tenant_type": "organization",
            "owner_user_key": f"{tenant}-{LEAD}",
            "status": "active",
            "max_members": 10,
            "plan_key": "standard",
        }
    )
    for user, email in ((f"{tenant}-{LEAD}", f"{tenant}-{SECRETS['email']}"), (f"{tenant}-{GROWER}", None)):
        db.collection("users").insert(
            {
                "_key": user,
                "email": email or f"{user}@example.com",
                "display_name": f"Name {user}",
                "password_hash": SECRETS["password_hash"],
                "account_type": "human",
            }
        )
    memberships = ArangoMembershipRepository(db)
    from app.domain.models.membership import Membership

    memberships.create(
        Membership(
            user_key=f"{tenant}-{LEAD}",
            tenant_key=tenant,
            role="lead",
            admin_scopes=["management", "technical"],
            joined_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    memberships.create(
        Membership(user_key=f"{tenant}-{GROWER}", tenant_key=tenant, role="grower", joined_at=datetime(2026, 2, 1))
    )
    k = {
        name: f"{tenant}-{name}" for name in ("site", "loc", "slot", "plant", "sp-own", "diary", "insp", "task", "att")
    }
    db.collection("sites").insert({"_key": k["site"], "tenant_key": tenant, "name": f"Site {tenant} {marker}"})
    db.collection("locations").insert({"_key": k["loc"], "site_key": k["site"], "name": "Bed 1"})
    db.collection("slots").insert({"_key": k["slot"], "location_key": k["loc"], "slot_id": "S1"})
    db.collection("species").insert(
        {
            "_key": k["sp-own"],
            "scientific_name": f"Capsicum {tenant}",
            "scientific_name_normalized": f"capsicum {tenant}",
            "tenant_key": tenant,
            "family_key": "fam-1",
        }
    )
    db.collection("attachments").insert(
        {
            "_key": k["att"],
            "tenant_key": tenant,
            "storage_key": f"t/{tenant}/plant/2026/10/{k['att']}.jpg",
            "created_by": f"{tenant}-{LEAD}",
            "mime_type": "image/jpeg",
            "byte_size": len(PHOTO),
            "sha256": hashlib.sha256(PHOTO).hexdigest(),
            "original_filename": "p.jpg",
            "category": "plant",
        }
    )
    db.collection("plant_instances").insert(
        {
            "_key": k["plant"],
            "tenant_key": tenant,
            "instance_id": "P-1",
            "species_key": "sp-global",
            "location_key": k["loc"],
            "slot_key": k["slot"],
            "site_key": k["site"],
            "current_phase_key": "gp-veg",
            "photo_refs": [k["att"]],
            "cover_photo_ref": k["att"],
            "mother_key": "dangling-plant-of-nobody",
        }
    )
    db.collection("plant_diary_entries").insert(
        {"_key": k["diary"], "tenant_key": tenant, "plant_key": k["plant"], "created_by": f"{tenant}-{LEAD}"}
    )
    db.collection("inspections").insert(
        {
            "_key": k["insp"],
            "tenant_key": tenant,
            "plant_key": k["plant"],
            "inspected_by_key": f"{tenant}-{GROWER}",
            "findings": [{"pest_key": "pest-1", "severity": "low"}],
        }
    )
    db.collection("tasks").insert(
        {
            "_key": k["task"],
            "tenant_key": tenant,
            "entity_type": "plant_instance",
            "entity_key": k["plant"],
            "assigned_to_user_key": f"{tenant}-{GROWER}",
            "name": f"Water {marker}",
        }
    )
    db.collection("contains").insert({"_from": f"sites/{k['site']}", "_to": f"locations/{k['loc']}"})
    db.collection("instance_of").insert({"_from": f"plant_instances/{k['plant']}", "_to": "species/sp-global"})
    db.collection("belongs_to_family").insert({"_from": f"species/{k['sp-own']}", "_to": "botanical_families/fam-1"})
    # Secrets that must never reach an archive (AK-30).
    db.collection("api_keys").insert(
        {"user_key": f"{tenant}-{LEAD}", "tenant_scope": tenant, "key_hash": f"{SECRETS['api_key_hash']}-{tenant}"}
    )
    db.collection("invitations").insert(
        {"tenant_key": tenant, "token_hash": f"{SECRETS['invitation_token']}-{tenant}", "email": "x@example.com"}
    )
    db.collection("ai_provider_configs").insert({"tenant_key": tenant, "api_key_encrypted": SECRETS["provider_secret"]})
    db.collection("weather_source_configs").insert(
        {
            "tenant_key": tenant,
            "site_key": k["site"],
            "sources": [{"source": "owm", "config": {"api_key_ref": SECRETS["weather_key_ref"]}}],
        }
    )
    return k


# ── service wiring ────────────────────────────────────────────────────


SIGNING_KEY = b"integration-installation-key-0123456789"
SALT = "tenant-export-salt-not-a-secret-0123456789"


def _service(
    db, storage_root: Path, *, signing_key: bytes | None = SIGNING_KEY, readings: Any = None
) -> TenantExportService:
    from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
    from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository

    tenant_repo = ArangoTenantRepository(db)
    membership_repo = ArangoMembershipRepository(db)
    audit = SecurityAuditService(ArangoSecurityAuditRepository(db))
    entitlements = EntitlementService(plan_repo=None, tenant_repo=tenant_repo)
    step_up = MagicMock()
    storage = LocalFsStorageAdapter(
        str(storage_root), "http://storage.invalid", "test-signing-secret", max_object_size_bytes=50 * 1024 * 1024
    )
    tenant_service = TenantService(
        tenant_repo=tenant_repo,
        membership_repo=membership_repo,
        invitation_repo=ArangoInvitationRepository(db),
        assignment_repo=ArangoLocationAssignmentRepository(db),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        security_audit=audit,
        step_up_verifier=step_up,
        entitlements=entitlements,
        storage_adapter=storage,
        reference_index_store=NoopReferenceIndexStore(),
        observation_repo=NullObservationRepository(),
        tenant_erasure_executor=ArangoTenantErasureExecutor(db),
        tenant_erasure_repo=ArangoTenantErasureRepository(db),
        tombstone_salt=SALT,
    )
    return TenantExportService(
        store=ArangoTenantDataStore(db),
        export_repo=ArangoTenantExportRequestRepository(db),
        import_repo=ArangoTenantImportRequestRepository(db),
        tenant_repo=tenant_repo,
        membership_repo=membership_repo,
        user_repo=ArangoUserRepository(db),
        tenant_service=tenant_service,
        storage=storage,
        step_up_verifier=step_up,
        security_audit=audit,
        entitlements=entitlements,
        signing_key=signing_key,
        allowed_mime_types=lambda category: ["image/jpeg", "image/png", "image/webp"],
        max_object_bytes=10 * 1024 * 1024,
        readings=readings,
    )


def _grant(email: str, role: str = "lead", scopes: tuple[str, ...] = ("management", "technical")) -> dict:
    return {"email": email, "role": role, "admin_scopes": list(scopes)}


async def _put(storage, key: str, data: bytes) -> None:
    async def chunks():
        yield data

    await storage.put_object(key, chunks(), "image/jpeg")


def _person(key: str) -> User:
    return User(key=key, email=f"{key}@example.com", display_name=key)


def _export(service: TenantExportService, db, tenant: str) -> bytes:
    """Request (as the tenant's lead) and run an export; the archive's bytes."""
    request = service.request_export(
        requester=_person(f"{tenant}-{LEAD}"),
        authenticated_with_api_key=False,
        origin="tenant_management",
        factors=StepUpFactors(password="pw"),
        client_ip=None,
        slug=db.collection("tenants").get(tenant)["slug"],
    )
    done = run_async(service.run_export(request.key or ""))
    assert done is not None and done.status == "completed", done
    stream = run_async(service.open_download(done))

    async def read() -> bytes:
        return b"".join([chunk async for chunk in stream])

    return run_async(read())


def _parts(archive: bytes) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in z.namelist():
            if name.endswith(".jsonl"):
                out[name] = [json.loads(line) for line in z.read(name).splitlines() if line.strip()]
    return out


def _substitute(value: Any, table: dict[str, str]) -> Any:
    if isinstance(value, str):
        collection, slash, key = value.partition("/")
        if slash and not value.startswith("t/") and key in table:
            return f"{collection}/{table[key]}"  # a document id (_from/_to)
        for old, new in table.items():
            if value == old:
                return new
            if old.startswith("t/") and value.startswith(old):
                return new + value[len(old) :]
        return value
    if isinstance(value, list):
        return [_substitute(item, table) for item in value]
    if isinstance(value, dict):
        return {name: _substitute(inner, table) for name, inner in value.items()}
    return value


# ── tests ─────────────────────────────────────────────────────────────


def test_roundtrip_export_import_export_differs_only_in_keys(source, target, tmp_path) -> None:
    seeded = _seed_tenant(source, A)
    _seed_tenant(source, B, marker=SECRETS["foreign_row"])
    src = _service(source, tmp_path / "src-store")
    run_async(_put(src._storage, f"t/{A}/plant/2026/10/{seeded['att']}.jpg", b"JPEG"))

    first = _export(src, source, A)

    # AK-30 — no secret and no row of B in the bytes (also not compressed: read every part).
    with zipfile.ZipFile(io.BytesIO(first)) as z:
        unpacked = b"".join(z.read(name) for name in z.namelist())
    for name, secret in SECRETS.items():
        assert secret.encode() not in unpacked, name
    assert f"{B}-".encode() not in unpacked

    # Import through the full request → task path into a database that only has the catalogue.
    target.collection("users").insert(
        {"_key": "new-lead", "email": "new-lead@example.com", "display_name": "New lead", "account_type": "human"}
    )
    dst = _service(target, tmp_path / "dst-store")
    accepted = dst.request_import(
        io.BytesIO(first),
        size_bytes=len(first),
        requester=_person(ADMIN),
        authenticated_with_api_key=False,
        member_mapping={f"{A}-{LEAD}": _grant("new-lead@example.com")},
        plan_key=None,
        factors=StepUpFactors(password="pw"),
        client_ip=None,
    )
    finished = run_async(dst.run_import(accepted.key or ""))
    assert finished is not None and finished.status == "completed", finished
    new_tenant = finished.target_tenant_key or ""
    assert new_tenant and new_tenant != A
    assert finished.report["plant_instances"] == 1
    assert accepted.verified is True  # the same installation key signed it
    # SEC-007 — open only now: the tenant is active and the mapped lead's membership active.
    assert target.collection("tenants").get(new_tenant)["status"] == "active"
    imported_members = list(
        target.aql.execute("FOR m IN memberships FILTER m.tenant_key == @t RETURN m", bind_vars={"t": new_tenant})
    )
    assert [(m["user_key"], m["role"], m["is_active"]) for m in imported_members] == [("new-lead", "lead", True)]

    request = dst.request_export(
        requester=_person("new-lead"),
        authenticated_with_api_key=False,
        origin="tenant_management",
        factors=StepUpFactors(password="pw"),
        client_ip=None,
        slug=target.collection("tenants").get(new_tenant)["slug"],
    )
    done = run_async(dst.run_export(request.key or ""))
    assert done is not None and done.status == "completed"
    stream = run_async(dst.open_download(done))

    async def read() -> bytes:
        return b"".join([chunk async for chunk in stream])

    second = run_async(read())

    # Build the source → target key table from the second archive by content position (one row each).
    one, two = _parts(first), _parts(second)
    table: dict[str, str] = {A: new_tenant, f"t/{A}/": f"t/{new_tenant}/", f"{A}-{LEAD}": "new-lead"}
    for name, rows in one.items():
        if name.startswith("collections/"):
            assert len(rows) == len(two.get(name, [])), name
            for old_row, new_row in zip(sorted(rows, key=lambda r: r["_key"]), two[name], strict=True):
                table[old_row["_key"]] = new_row["_key"]
    table[f"{A}-{GROWER}"] = "_anonymized"

    for name, rows in one.items():
        if name == "members.jsonl":
            continue
        expected = sorted(
            json.dumps(_substitute({k: v for k, v in row.items() if k != "_key"}, table), sort_keys=True)
            for row in rows
        )
        actual = sorted(json.dumps({k: v for k, v in row.items() if k != "_key"}, sort_keys=True) for row in two[name])
        if name == "collections/plant_instances.jsonl":
            # The source's dangling pointer is cleared, never carried (it could name a foreign row).
            expected = [e.replace('"mother_key": "dangling-plant-of-nobody"', '"mother_key": null') for e in expected]
        assert actual == expected, name

    # The object came along under the new tenant's prefix.
    with zipfile.ZipFile(io.BytesIO(second)) as z:
        assert z.read(f"objects/plant/2026/10/{seeded['att']}.jpg") == b"JPEG"
    # The new tenant's members: the mapped lead owns it; the grower was not mapped and is gone.
    members = [m["user_key"] for m in two["members.jsonl"]]
    assert members == ["new-lead"]
    assert target.collection("tenants").get(new_tenant)["owner_user_key"] == "new-lead"


def test_restoring_a_beside_b_changes_nothing_of_b(source, tmp_path) -> None:
    _seed_tenant(source, A)
    seeded_b = _seed_tenant(source, B)
    service = _service(source, tmp_path / "store")
    archive = _export(service, source, A)

    # A is lost (its rows removed), B keeps working.
    for name in ("sites", "locations", "slots", "plant_instances", "species", "plant_diary_entries", "inspections"):
        source.aql.execute(
            "FOR d IN @@c FILTER STARTS_WITH(d._key, @p) REMOVE d IN @@c", bind_vars={"@c": name, "p": f"{A}-"}
        )
    source.collection("tasks").update({"_key": seeded_b["task"], "name": "Water after A was lost"})
    source.collection("sites").insert({"_key": "b-site-2", "tenant_key": B, "name": "B grew"})

    def snapshot() -> dict[str, str]:
        out: dict[str, str] = {}
        for info in source.collections():
            if info["system"]:
                continue
            for doc in source.collection(info["name"]).all():
                out[doc["_id"]] = doc["_rev"]
        return out

    before = snapshot()
    finished = run_async(
        service.import_archive(
            read_tenant_archive(io.BytesIO(archive), max_uncompressed_bytes=10**8),
            actor_user_key=ADMIN,
            member_grants={
                f"{A}-{LEAD}": TenantImportMemberGrant(
                    account_key=f"{A}-{LEAD}", role="lead", admin_scopes=["management", "technical"]
                )
            },
            plan_key="standard",
        )
    )
    after = snapshot()

    unchanged = {doc_id: rev for doc_id, rev in before.items() if after.get(doc_id) != rev}
    assert unchanged == {}, "an import changed or removed a document that existed before it"
    new_ids = set(after) - set(before)
    assert new_ids, "the import wrote nothing"
    new_keys = {doc_id.split("/", 1)[1] for doc_id in new_ids}
    assert new_keys.isdisjoint({doc_id.split("/", 1)[1] for doc_id in before})
    restored = list(
        source.aql.execute(
            "FOR p IN plant_instances FILTER p.tenant_key == @t RETURN p", bind_vars={"t": finished.tenant_key}
        )
    )
    assert len(restored) == 1 and restored[0]["species_key"] == "sp-global"
    b_rows = list(source.aql.execute("FOR s IN sites FILTER s.tenant_key == @t RETURN s._key", bind_vars={"t": B}))
    assert sorted(b_rows) == sorted([seeded_b["site"], "b-site-2"])


def test_a_missing_catalogue_entry_refuses_and_writes_nothing(source, target, tmp_path) -> None:
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    target.collection("pests").delete("pest-1")
    dst = _service(target, tmp_path / "dst")
    tenants_before = target.collection("tenants").count()

    with pytest.raises(TenantImportRefusedError) as refused:
        dst.request_import(
            io.BytesIO(archive),
            size_bytes=len(archive),
            requester=_person(ADMIN),
            authenticated_with_api_key=False,
            member_mapping={},
            plan_key=None,
            factors=StepUpFactors(password="pw"),
            client_ip=None,
        )

    assert refused.value.error_code == "IMPORT_MISSING_CATALOG_ENTRIES"
    assert [d["reason"] for d in refused.value.details] == ["pests/pest-1"]
    assert target.collection("tenants").count() == tenants_before
    assert target.collection("tenant_import_requests").count() == 0


def test_a_failure_mid_import_leaves_no_tenant_behind(source, target, tmp_path) -> None:
    _seed_tenant(source, A)
    archive = read_tenant_archive(
        io.BytesIO(_export(_service(source, tmp_path / "src"), source, A)), max_uncompressed_bytes=10**8
    )
    dst = _service(target, tmp_path / "dst")
    store = dst._store
    real_insert = store.insert_documents
    calls = {"n": 0}

    def failing_insert(collection: str, documents: list[dict[str, Any]]) -> list[str]:
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("disk full")
        return real_insert(collection, documents)

    store.insert_documents = failing_insert  # type: ignore[method-assign]
    counts_before = {
        info["name"]: target.collection(info["name"]).count() for info in target.collections() if not info["system"]
    }

    with pytest.raises(RuntimeError):
        run_async(dst.import_archive(archive, actor_user_key=ADMIN, member_grants={}, plan_key="standard"))

    counts_after = {
        info["name"]: target.collection(info["name"]).count() for info in target.collections() if not info["system"]
    }
    grown = {name: (counts_before[name], n) for name, n in counts_after.items() if n != counts_before[name]}
    # The founding wrote one security-audit row (membership_added) and the rollback's inventory erasure its
    # record (I1 of round 3); both are the proof and stay. No row of the tenant is left.
    assert set(grown) <= {"security_audit_log", "tenant_erasure_records"}, grown


def _crafted(entries: dict[str, list[dict]], edges: dict[str, list[dict]] | None = None) -> bytes:
    """An archive written by hand (unsigned), the way an attacker would."""
    buffer = io.BytesIO()
    writer = TenantArchiveWriter(buffer, max_bytes=None)
    writer.write_json("tenant.json", {"name": "Crafted", "slug": "crafted"})
    for name, rows in entries.items():
        writer.write_lines(f"collections/{name}.jsonl", [rows])
    for name, rows in (edges or {}).items():
        writer.write_lines(f"edges/{name}.jsonl", [rows])
    writer.write_lines("members.jsonl", [[]])
    writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": "ten-src"})
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("entries", "edges"),
    [
        # SEC-001 — a "tenant" species with no tenant key would become a global catalogue row.
        ({"species": [{"_key": "evil", "scientific_name": "Evilus globalis", "tenant_key": ""}]}, None),
        ({"species": [{"_key": "evil", "scientific_name": "Evilus globalis"}]}, None),
        # SEC-002 — an edge between two global rows rewrites the catalogue for everybody.
        (
            {"sites": [{"_key": "s1", "tenant_key": "ten-src"}]},
            {"belongs_to_family": [{"_from": "species/sp-global", "_to": "botanical_families/fam-1"}]},
        ),
        # SEC-002 — an access grant is never imported.
        (
            {"sites": [{"_key": "s1", "tenant_key": "ten-src"}]},
            {"tenant_has_access": [{"_from": "tenants/ten-src", "_to": "species/sp-global"}]},
        ),
    ],
)
def test_a_crafted_archive_is_refused_before_anything_is_written(target, tmp_path, entries, edges) -> None:
    data = _crafted(entries, edges)
    dst = _service(target, tmp_path / "dst")

    def counts() -> dict[str, int]:
        return {
            info["name"]: target.collection(info["name"]).count() for info in target.collections() if not info["system"]
        }

    before = counts()
    with pytest.raises(TenantImportRefusedError) as refused:
        dst.request_import(
            io.BytesIO(data),
            size_bytes=len(data),
            requester=_person(ADMIN),
            authenticated_with_api_key=False,
            member_mapping={},
            plan_key=None,
            factors=StepUpFactors(password="pw"),
            client_ip=None,
        )
    assert refused.value.error_code == "IMPORT_FORMAT_UNSUPPORTED"
    after = counts()
    # The refusal itself is audited (I9): one security-audit row, nothing else.
    assert {name: n for name, n in after.items() if n != before[name]} == {
        "security_audit_log": before["security_audit_log"] + 1
    }
    row = next(iter(target.aql.execute("FOR r IN security_audit_log SORT r.created_at DESC LIMIT 1 RETURN r")))
    assert row["action"] == "tenant_import_requested"
    assert row["outcome"] == "refused:IMPORT_FORMAT_UNSUPPORTED"
    assert row["archive_sha256"] == hashlib.sha256(data).hexdigest()


def test_a_foreign_archive_imports_unverified(source, target, tmp_path) -> None:
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src", signing_key=b"another-installation-key-xxxxxxx"), source, A)
    dst = _service(target, tmp_path / "dst")
    accepted = dst.request_import(
        io.BytesIO(archive),
        size_bytes=len(archive),
        requester=_person(ADMIN),
        authenticated_with_api_key=False,
        member_mapping={},
        plan_key=None,
        factors=StepUpFactors(password="pw"),
        client_ip=None,
    )
    assert accepted.verified is False


def test_the_tenant_is_unreachable_while_importing_and_a_dead_import_is_swept(source, target, tmp_path) -> None:
    _seed_tenant(source, A)
    archive = read_tenant_archive(
        io.BytesIO(_export(_service(source, tmp_path / "src"), source, A)), max_uncompressed_bytes=10**8
    )
    dst = _service(target, tmp_path / "dst")
    target.collection("users").insert(
        {"_key": "new-lead", "email": "new-lead@example.com", "display_name": "L", "account_type": "human"}
    )
    seen: dict[str, Any] = {}
    real_insert = dst._store.insert_documents

    def observing_insert(collection: str, documents: list[dict[str, Any]]) -> list[str]:
        tenant_key = documents[0].get("tenant_key") if documents else None
        if tenant_key and "status" not in seen:
            seen["status"] = target.collection("tenants").get(tenant_key)["status"]
            seen["active_members"] = list(
                target.aql.execute(
                    "FOR m IN memberships FILTER m.tenant_key == @t AND m.is_active RETURN m",
                    bind_vars={"t": tenant_key},
                )
            )
        return real_insert(collection, documents)

    dst._store.insert_documents = observing_insert  # type: ignore[method-assign]
    grants = {f"{A}-{LEAD}": TenantImportMemberGrant(account_key="new-lead", role="lead", admin_scopes=["management"])}
    run_async(dst.import_archive(archive, actor_user_key=ADMIN, member_grants=grants, plan_key="standard"))
    assert seen == {"status": "importing", "active_members": []}

    # A run that died after founding: the tenant stays ``importing`` with rows in it.
    dst._store.insert_documents = real_insert  # type: ignore[method-assign]
    half = dst._tenant_service.found_imported_tenant(
        actor_user_key=ADMIN,
        name="Half",
        slug_hint="half",
        description=None,
        settings={},
        plan_key="standard",
        owner_user_key=ADMIN,
        members=[],
    )
    half_key = half.key or ""
    target.collection("sites").insert({"_key": "half-site", "tenant_key": half_key, "name": "half"})
    long_ago = datetime(2026, 1, 1, tzinfo=UTC)
    stale = dst._imports.create(
        TenantImportRequest(
            requested_by_user_key=ADMIN,
            status="running",
            source_format="kamerplanter-tenant-export/1",
            target_tenant_key=half_key,
            requested_at=long_ago,
            updated_at=long_ago,
        )
    )

    # The repository stamps ``updated_at`` on create; the run's last heartbeat was long ago.
    dst._imports.update_fields(stale.key or "", {"updated_at": long_ago})

    result = run_async(dst.expire())

    assert result["abandoned_imports"] == 1
    assert target.collection("sites").get("half-site") is None
    assert target.collection("tenants").get(half_key) is None


# ── PR #2267 security review, round 2 ────────────────────────────────


def _request_and_run(dst: TenantExportService, archive: bytes, mapping: dict[str, dict]) -> TenantImportRequest:
    accepted = dst.request_import(
        io.BytesIO(archive),
        size_bytes=len(archive),
        requester=_person(ADMIN),
        authenticated_with_api_key=False,
        member_mapping=mapping,
        plan_key=None,
        factors=StepUpFactors(password="pw"),
        client_ip=None,
    )
    finished = run_async(dst.run_import(accepted.key or ""))
    assert finished is not None
    return finished


def test_the_owner_gets_the_scopes_the_admin_confirmed_and_the_admin_is_the_actor(source, target, tmp_path) -> None:
    """SEC-R2-02 — the founder's membership carries the confirmed scopes, not a fixed management + technical."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    target.collection("users").insert(
        {"_key": "new-lead", "email": "new-lead@example.com", "display_name": "L", "account_type": "human"}
    )
    dst = _service(target, tmp_path / "dst")

    finished = _request_and_run(dst, archive, {f"{A}-{LEAD}": _grant("new-lead@example.com", scopes=("management",))})

    assert finished.status == "completed", finished
    tenant = finished.target_tenant_key
    owner = next(
        iter(
            target.aql.execute(
                "FOR m IN memberships FILTER m.tenant_key == @t AND m.user_key == 'new-lead' RETURN m",
                bind_vars={"t": tenant},
            )
        )
    )
    assert owner["role"] == "lead" and owner["admin_scopes"] == ["management"]
    founding = list(
        target.aql.execute(
            "FOR r IN security_audit_log FILTER r.tenant_key == @t AND r.action == 'membership_added' RETURN r",
            bind_vars={"t": tenant},
        )
    )
    assert [(r["actor_user_key"], r["target_user_key"], r["new_scopes"]) for r in founding] == [
        (ADMIN, "new-lead", ["management"])
    ]


def test_without_a_confirmed_lead_the_admin_owns_the_import_with_both_scopes(source, target, tmp_path) -> None:
    """The documented fallback of SEC-R2-02: a tenant is never founded without a member who can manage it."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    dst = _service(target, tmp_path / "dst")

    finished = _request_and_run(dst, archive, {})

    assert finished.status == "completed", finished
    owner = next(
        iter(
            target.aql.execute(
                "FOR m IN memberships FILTER m.tenant_key == @t RETURN m", bind_vars={"t": finished.target_tenant_key}
            )
        )
    )
    assert (owner["user_key"], owner["role"], sorted(owner["admin_scopes"])) == (
        ADMIN,
        "lead",
        ["management", "technical"],
    )


def test_the_request_names_the_tenant_before_it_exists(source, target, tmp_path) -> None:
    """I3 — no moment in which a founded tenant is named by no request the sweep reads."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    dst = _service(target, tmp_path / "dst")
    seen: dict[str, Any] = {}
    real_found = dst._tenant_service.found_imported_tenant

    def observing_found(**kwargs: Any):
        recorded = list(target.aql.execute("FOR r IN tenant_import_requests RETURN r.target_tenant_key"))
        seen["recorded"] = recorded
        seen["tenant_exists"] = bool(recorded[0]) and target.collection("tenants").has(recorded[0])
        return real_found(**kwargs)

    dst._tenant_service.found_imported_tenant = observing_found  # type: ignore[method-assign]
    finished = _request_and_run(dst, archive, {})

    assert finished.status == "completed", finished
    assert seen == {"recorded": [finished.target_tenant_key], "tenant_exists": False}


def test_a_rollback_that_leaves_rows_keeps_the_tenant_for_the_sweep(source, target, tmp_path) -> None:
    """SEC-R2-03 — rows the rollback could not remove stay findable: tenant ``importing``, request names it."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    dst = _service(target, tmp_path / "dst")
    store = dst._store
    real_insert = store.insert_documents
    calls = {"n": 0}

    def failing_insert(collection: str, documents: list[dict[str, Any]]) -> list[str]:
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("disk full")
        return real_insert(collection, documents)

    real_remove = store.remove_documents

    def failing_remove(collection: str, keys: list[str]) -> int:
        # Only the rows the run wrote: the tenant shell itself (memberships, tenant) would still be removable,
        # so the test measures the decision not to remove it, not a second failure.
        if collection == "sites":
            raise RuntimeError("connection lost")
        return real_remove(collection, keys)

    store.insert_documents = failing_insert  # type: ignore[method-assign]
    store.remove_documents = failing_remove  # type: ignore[method-assign]
    # The database is unreachable for the inventory erasure of the rollback too (I1 of round 3).
    real_erase = dst._tenant_service.erase_abandoned_import

    def unreachable_erase(tenant_key: str, *, now: datetime) -> bool:
        raise RuntimeError("connection lost")

    dst._tenant_service.erase_abandoned_import = unreachable_erase  # type: ignore[method-assign]

    finished = _request_and_run(dst, archive, {})
    dst._tenant_service.erase_abandoned_import = real_erase  # type: ignore[method-assign]

    assert finished.status == "cleanup_pending", finished
    assert finished.failure_reason == "IMPORT_FAILED"
    half = finished.target_tenant_key or ""
    assert half and target.collection("tenants").get(half)["status"] == "importing"
    left = list(target.aql.execute("FOR s IN sites FILTER s.tenant_key == @t RETURN s._key", bind_vars={"t": half}))
    assert left, "the rows the rollback could not remove are still there"
    audited = list(
        target.aql.execute("FOR r IN security_audit_log FILTER r.outcome != null SORT r.created_at RETURN r.outcome")
    )
    assert audited[-1] == "cleanup_pending:IMPORT_FAILED"

    # The next hourly sweep erases the half tenant through the tenant-erasure inventory, whatever its age.
    store.remove_documents = real_remove  # type: ignore[method-assign]
    result = run_async(dst.expire())

    assert result["abandoned_imports"] == 1
    assert list(target.aql.execute("FOR s IN sites FILTER s.tenant_key == @t RETURN s", bind_vars={"t": half})) == []
    assert target.collection("tenants").get(half) is None
    ended = dst._imports.get(finished.key or "")
    assert ended is not None and (ended.status, ended.target_tenant_key, ended.failure_reason) == (
        "failed",
        None,
        "IMPORT_FAILED",
    )


def test_an_attachments_size_and_hash_come_from_its_object(target, tmp_path) -> None:
    """I7 — the quota counts ``byte_size``, a re-upload deduplicates on ``sha256``: neither is the archive's word."""
    from app.domain.models.tenant_export import TenantArchive

    photo = b"\xff\xd8 the real photo bytes"
    archive = TenantArchive(
        format="kamerplanter-tenant-export/1",
        source_tenant_key="ten-src",
        tenant={"name": "Liar", "slug": "liar"},
        collections={
            "attachments": [
                {
                    "_key": "a1",
                    "tenant_key": "ten-src",
                    "storage_key": "t/ten-src/plant/2026/10/a1.jpg",
                    "mime_type": "image/jpeg",
                    "byte_size": 1,
                    "sha256": "0" * 64,
                    "original_filename": "a1.jpg",
                    "created_by": "_anonymized",
                    "category": "plant",
                }
            ]
        },
        objects={"plant/2026/10/a1.jpg": photo},
    )
    dst = _service(target, tmp_path / "dst")

    outcome = run_async(dst.import_archive(archive, actor_user_key=ADMIN, member_grants={}, plan_key="standard"))

    row = target.collection("attachments").get(outcome.key_mapping["attachments"]["a1"])
    assert (row["byte_size"], row["sha256"]) == (len(photo), hashlib.sha256(photo).hexdigest())


def test_a_legacy_stamped_catalogue_row_counts_as_present(target, tmp_path) -> None:
    """I10 — a harvest indicator still carrying the v0004 stamp is a catalogue row, not a missing one."""
    target.collection("harvest_indicators").insert(
        {"_key": "hi-1", "indicator_type": "trichome", "measurement_unit": "%", "tenant_key": "default"}
    )
    data = _crafted(
        {
            "plant_instances": [{"_key": "p1", "tenant_key": "ten-src", "instance_id": "P-1"}],
            "harvest_observations": [{"_key": "h1", "plant_key": "p1", "indicator_key": "hi-1"}],
        }
    )
    dst = _service(target, tmp_path / "dst")

    finished = _request_and_run(dst, data, {})

    assert finished.status == "completed", finished
    written = list(
        target.aql.execute("FOR h IN harvest_observations FILTER h.indicator_key == 'hi-1' RETURN h", bind_vars={})
    )
    assert len(written) == 1


# ── PR #2267 security review, round 3 ────────────────────────────────


def _importing_tenants(db) -> list[str]:
    return list(db.aql.execute("FOR t IN tenants FILTER t.status == 'importing' RETURN t._key"))


def _two_members(target) -> dict[str, dict]:
    for key in ("new-lead", "new-grower"):
        target.collection("users").insert(
            {"_key": key, "email": f"{key}@example.com", "display_name": key, "account_type": "human"}
        )
    return {
        f"{A}-{LEAD}": _grant("new-lead@example.com"),
        f"{A}-{GROWER}": _grant("new-grower@example.com", role="grower", scopes=()),
    }


def test_a_failure_while_founding_leaves_no_tenant_behind(source, target, tmp_path) -> None:
    """R3-01 — the second membership fails after the tenant was written: the rollback takes the tenant too."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    mapping = _two_members(target)
    dst = _service(target, tmp_path / "dst")

    def failing_membership(membership: Any) -> Any:
        raise RuntimeError("connection lost")

    dst._tenant_service._create_membership_unless_erasing = failing_membership  # type: ignore[method-assign]

    finished = _request_and_run(dst, archive, mapping)

    assert (finished.status, finished.failure_reason, finished.target_tenant_key) == ("failed", "IMPORT_FAILED", None)
    assert _importing_tenants(target) == []


def test_a_request_never_lets_go_of_a_tenant_that_is_still_importing(source, target, tmp_path) -> None:
    """R3-01 — whatever path a failure took, an ``importing`` tenant stays named for the sweep."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    dst = _service(target, tmp_path / "dst")
    real_insert = dst._store.insert_documents

    def failing_insert(collection: str, documents: list[dict[str, Any]]) -> list[str]:
        raise RuntimeError("disk full")

    async def broken_rollback(tenant_key: str, written: Any, objects: Any) -> bool:
        raise RuntimeError("the rollback itself died")

    dst._store.insert_documents = failing_insert  # type: ignore[method-assign]
    dst._rollback = broken_rollback  # type: ignore[method-assign]

    finished = _request_and_run(dst, archive, {})

    half = finished.target_tenant_key or ""
    assert (finished.status, bool(half)) == ("cleanup_pending", True), finished
    assert _importing_tenants(target) == [half]

    dst._store.insert_documents = real_insert  # type: ignore[method-assign]
    run_async(dst.expire())
    assert _importing_tenants(target) == []
    ended = dst._imports.get(finished.key or "")
    assert ended is not None and (ended.status, ended.target_tenant_key) == ("failed", None)


def test_the_rollback_also_removes_what_its_lists_do_not_know(source, target, tmp_path) -> None:
    """I1 of round 3 — a write whose outcome the run never learned is erased through the inventory and prefix."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    dst = _service(target, tmp_path / "dst")
    real_insert = dst._store.insert_documents
    seen: dict[str, str] = {}

    def committed_then_failed(collection: str, documents: list[dict[str, Any]]) -> list[str]:
        if collection == "sites":
            real_insert(collection, documents)  # committed, but the client sees an error
            seen["tenant"] = str(documents[0]["tenant_key"])
            run_async(_put(dst._storage, f"t/{seen['tenant']}/plant/orphan.jpg", b"JPEG"))
            raise RuntimeError("connection reset after commit")
        return real_insert(collection, documents)

    dst._store.insert_documents = committed_then_failed  # type: ignore[method-assign]

    finished = _request_and_run(dst, archive, {})

    assert finished.status == "failed", finished
    tenant = seen["tenant"]
    assert list(target.aql.execute("FOR s IN sites FILTER s.tenant_key == @t RETURN s", bind_vars={"t": tenant})) == []
    assert not (tmp_path / "dst" / "t" / tenant).exists() or not any((tmp_path / "dst" / "t" / tenant).rglob("*.jpg"))
    assert target.collection("tenants").get(tenant) is None


def _plan_bound_service(target, tmp_path):
    from app.data_access.arango.plan_repository import ArangoPlanRepository
    from app.data_access.arango.tenant_repository import ArangoTenantRepository as _Tenants

    dst = _service(target, tmp_path / "dst")
    entitlements = EntitlementService(plan_repo=ArangoPlanRepository(target), tenant_repo=_Tenants(target))
    dst._entitlements = entitlements
    dst._tenant_service._entitlements = entitlements
    return dst


def _request_on_plan(dst, archive: bytes, mapping, plan_key: str):
    return dst.request_import(
        io.BytesIO(archive),
        size_bytes=len(archive),
        requester=_person(ADMIN),
        authenticated_with_api_key=False,
        member_mapping=mapping,
        plan_key=plan_key,
        factors=StepUpFactors(password="pw"),
        client_ip=None,
    )


def test_the_target_plans_member_limit_refuses_the_request_before_anything_is_written(source, target, tmp_path) -> None:
    """REQ-056 §8.4 step 6 (AK-46) — the mapped accounts are counted against the plan before the upload is stored."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    mapping = _two_members(target)
    target.collection("plans").insert({"_key": "tiny", "name": "Tiny", "limits": {"members": 1}})
    dst = _plan_bound_service(target, tmp_path)

    with pytest.raises(MemberLimitReachedError):
        _request_on_plan(dst, archive, mapping, "tiny")

    assert list(target.collection("tenant_import_requests").all()) == []
    assert _importing_tenants(target) == []


def test_the_target_plans_member_limit_counts_the_inactive_imported_members(source, target, tmp_path) -> None:
    """I3 of round 3 and §8.4 step 6 — a plan lowered after the request ends the run before the founding."""
    _seed_tenant(source, A)
    archive = _export(_service(source, tmp_path / "src"), source, A)
    mapping = _two_members(target)
    target.collection("plans").insert({"_key": "tiny", "name": "Tiny", "limits": {"members": 5}})
    dst = _plan_bound_service(target, tmp_path)
    accepted = _request_on_plan(dst, archive, mapping, "tiny")
    target.collection("plans").update({"_key": "tiny", "limits": {"members": 1}})

    finished = run_async(dst.run_import(accepted.key or ""))

    assert finished is not None and (finished.status, finished.failure_reason) == ("failed", "MEMBER_LIMIT_REACHED")
    assert finished.target_tenant_key is None
    assert _importing_tenants(target) == []


def test_the_sweep_takes_the_oldest_stale_imports_first(target) -> None:
    """I2 of round 3 — with more than 100 stale requests, the ones longest without a heartbeat are not starved."""
    imports = ArangoTenantImportRequestRepository(target)
    recent, oldest = datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        {
            "requested_by_user_key": ADMIN,
            "status": "running",
            "source_format": "kamerplanter-tenant-export/1",
            "requested_at": (oldest if i == 100 else recent).isoformat(),
            "updated_at": (oldest if i == 100 else recent).isoformat(),
            "_key": f"imp-{i:04d}",
        }
        for i in range(101)
    ]
    target.collection("tenant_import_requests").insert_many(rows)

    stale = imports.list_stale_active(datetime(2026, 6, 1, tzinfo=UTC))

    assert len(stale) == 100
    assert "imp-0100" in {request.key for request in stale}
