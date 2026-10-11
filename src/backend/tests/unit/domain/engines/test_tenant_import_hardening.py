"""#2138 security review of PR #2267 — what a crafted archive must never achieve.

An import writes rows into a **shared** database on the strength of an uploaded file.
Each test here is one thing an archive could otherwise do to the rest of the
installation, and the refusal that stops it:

* **SEC-001** — a row that claims no tenant (``tenant_key`` empty or absent) would be
  written as a global catalogue row every tenant reads; a parent-scoped row anchored
  to nothing of the archive would be owned by nobody.
* **SEC-002** — an edge between two global catalogue rows (or in an edge collection
  the import never writes) would rewrite the catalogue relations every tenant sees.
* **SEC-004** — a storage key outside ``t/<source>/`` (or with a ``..`` segment) would
  point the new tenant's attachment at another tenant's object.
* **SEC-005** — the encrypted weather-provider key reference must not leave the
  installation, and every secret-looking field of an exported model is decided.
* **SEC-008** — the ZIP directory is checked before anything is decompressed; every
  parser failure is a 422 refusal, never a 500.
"""

from __future__ import annotations

import io
import json
import zipfile
from itertools import count

import pytest

from app.domain.engines.tenant_export_engine import (
    TenantArchiveError,
    TenantArchiveWriter,
    TenantExportEngine,
    archive_document,
    read_tenant_archive,
)
from app.domain.engines.tenant_import_engine import TenantImportEngine
from app.domain.models.tenant_export import TenantArchive

SOURCE, TARGET = "ten-src", "ten-new"


def _archive(edges: dict[str, list[dict]] | None = None, **collections: list[dict]) -> TenantArchive:
    return TenantArchive(
        format="kamerplanter-tenant-export/1",
        source_tenant_key=SOURCE,
        tenant={"name": "Garden", "slug": "garden"},
        collections=collections,
        edges=edges or {},
    )


def _engine(archive: TenantArchive) -> TenantImportEngine:
    keys = count(1)
    return TenantImportEngine(
        archive, target_tenant_key=TARGET, member_accounts={}, key_factory=lambda: f"new-{next(keys)}"
    )


def _refused(archive: TenantArchive) -> TenantArchiveError:
    with pytest.raises(TenantArchiveError) as refused:
        TenantImportEngine.validate_structure(archive)
        _engine(archive).validate_documents()
    return refused.value


# ── SEC-001 ─────────────────────────────────────────────────────────


class TestEveryRowBelongsToTheNewTenant:
    @pytest.mark.parametrize("tenant_key", ["", None])
    def test_a_tenant_scoped_row_without_the_source_key_is_refused(self, tenant_key) -> None:
        row = {"_key": "sp1", "scientific_name": "Fakeus globalis"}
        if tenant_key is not None:
            row["tenant_key"] = tenant_key
        assert _refused(_archive(species=[row])).code == "IMPORT_FORMAT_UNSUPPORTED"

    def test_a_tenant_scoped_row_is_written_with_the_target_key(self) -> None:
        archive = _archive(sites=[{"_key": "s1", "tenant_key": SOURCE}])
        site = _engine(archive).remap_document("sites", archive.collections["sites"][0], existing_global=set())
        assert site["tenant_key"] == TARGET

    def test_a_parent_scoped_row_anchored_to_nothing_of_the_archive_is_refused(self) -> None:
        archive = _archive(locations=[{"_key": "l1", "site_key": "site-of-someone-else"}])
        assert _refused(archive).code == "IMPORT_FORMAT_UNSUPPORTED"

    def test_a_parent_scoped_row_that_supplies_a_tenant_key_gets_the_target(self) -> None:
        archive = _archive(
            sites=[{"_key": "s1", "tenant_key": SOURCE}],
            locations=[{"_key": "l1", "site_key": "s1", "tenant_key": SOURCE}],
        )
        engine = _engine(archive)
        engine.validate_documents()
        location = engine.remap_document("locations", archive.collections["locations"][0], existing_global=set())
        assert location["tenant_key"] == TARGET


# ── SEC-002 ─────────────────────────────────────────────────────────


class TestEdgesStayInsideTheTenant:
    def test_an_edge_between_two_global_catalogue_rows_is_refused(self) -> None:
        archive = _archive(
            sites=[{"_key": "s1", "tenant_key": SOURCE}],
            edges={"belongs_to_family": [{"_from": "species/sp-global", "_to": "botanical_families/fam-1"}]},
        )
        engine = _engine(archive)
        with pytest.raises(TenantArchiveError):
            engine.remap_edge(
                archive.edges["belongs_to_family"][0],
                existing_global={"species/sp-global", "botanical_families/fam-1"},
            )

    def test_an_edge_collection_the_import_never_writes_is_refused(self) -> None:
        archive = _archive(
            sites=[{"_key": "s1", "tenant_key": SOURCE}],
            edges={"tenant_has_access": [{"_from": f"tenants/{SOURCE}", "_to": "species/private-of-b"}]},
        )
        assert _refused(archive).code == "IMPORT_FORMAT_UNSUPPORTED"

    def test_an_edge_tenant_key_becomes_the_target(self) -> None:
        archive = _archive(sites=[{"_key": "s1", "tenant_key": SOURCE}])
        edge = _engine(archive).remap_edge(
            {"_from": "sites/s1", "_to": f"tenants/{SOURCE}", "tenant_key": SOURCE}, existing_global=set()
        )
        assert edge is not None and edge["tenant_key"] == TARGET

    def test_the_importable_and_excluded_edges_do_not_overlap(self) -> None:
        assert TenantExportEngine.IMPORTABLE_EDGES.isdisjoint(TenantExportEngine.EXCLUDED_EDGES)
        assert "tenant_has_access" in TenantExportEngine.EXCLUDED_EDGES


# ── SEC-004 ─────────────────────────────────────────────────────────


class TestObjectKeysStayInTheSourceNamespace:
    @pytest.mark.parametrize(
        "storage_key",
        ["t/ten-other/plant/2026/10/a.jpg", "plant/a.jpg", f"t/{SOURCE}/../ten-other/plant/a.jpg"],
    )
    def test_a_storage_key_outside_the_source_namespace_is_refused(self, storage_key: str) -> None:
        archive = _archive(attachments=[{"_key": "a1", "tenant_key": SOURCE, "storage_key": storage_key}])
        with pytest.raises(TenantArchiveError):
            _engine(archive).remap_document("attachments", archive.collections["attachments"][0], existing_global=set())

    def test_a_photo_ref_naming_another_namespace_is_refused(self) -> None:
        archive = _archive(
            plant_instances=[{"_key": "p1", "tenant_key": SOURCE, "photo_refs": ["t/ten-other/plant/x.jpg"]}]
        )
        with pytest.raises(TenantArchiveError):
            _engine(archive).remap_document(
                "plant_instances", archive.collections["plant_instances"][0], existing_global=set()
            )


# ── SEC-005 ─────────────────────────────────────────────────────────


class TestSecretsDoNotLeave:
    def test_the_weather_provider_key_reference_is_redacted(self) -> None:
        stored = {
            "_key": "w1",
            "_rev": "r",
            "tenant_key": SOURCE,
            "sources": [{"source": "owm", "config": {"api_key_ref": "gAAAAAFERNETCIPHERTEXT", "city": "Kiel"}}],
        }
        exported = archive_document(stored, collection="weather_source_configs")
        assert "gAAAAAFERNETCIPHERTEXT" not in json.dumps(exported)
        assert exported["sources"][0]["config"]["city"] == "Kiel"


# ── SEC-008 ─────────────────────────────────────────────────────────


def _zip(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in entries.items():
            out.writestr(name, data)
    return buffer.getvalue()


def _valid_archive_bytes(tenant: dict | None = None, members: bytes | None = None) -> bytes:
    buffer = io.BytesIO()
    writer = TenantArchiveWriter(buffer, max_bytes=None)
    writer.write_json("tenant.json", tenant or {"name": "Garden", "slug": "garden"})
    if members is not None:
        writer.write_lines("members.jsonl", [[json.loads(line) for line in members.splitlines()]])
    writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": SOURCE})
    return buffer.getvalue()


class TestTheDirectoryIsCheckedFirst:
    def test_too_many_entries_are_refused_before_reading(self) -> None:
        data = _zip({f"objects/{i}.bin": b"" for i in range(50)})
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**6, max_entries=10)

    def test_one_oversized_entry_is_refused_before_reading(self) -> None:
        data = _zip({"manifest.json": b"{}", "objects/big.bin": b"0" * 4096})
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**6, max_entry_bytes=1024)

    def test_an_oversized_tenant_json_is_refused(self) -> None:
        data = _valid_archive_bytes(tenant={"name": "G", "slug": "g", "description": "x" * (1024 * 1024 + 1)})
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**8)

    def test_a_member_line_of_the_wrong_shape_is_a_refusal_not_a_crash(self) -> None:
        data = _valid_archive_bytes(members=b'{"user_key": "u1", "role": ["not", "a", "string"]}')
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**6)

    def test_deeply_nested_json_is_refused(self) -> None:
        deep = "[" * 200 + "]" * 200
        buffer = io.BytesIO()
        writer = TenantArchiveWriter(buffer, max_bytes=None)
        writer.write_json("tenant.json", {"name": "G", "slug": "g"})
        writer.write_lines("collections/sites.jsonl", [[{"_key": "s1", "tenant_key": SOURCE, "x": json.loads(deep)}]])
        writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": SOURCE})
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(buffer.getvalue()), max_uncompressed_bytes=10**6)

    def test_an_encrypted_entry_is_a_refusal_not_a_crash(self) -> None:
        data = bytearray(_valid_archive_bytes())
        # Set the "encrypted" flag bit on every local and central header: zipfile raises RuntimeError on read.
        for signature, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            start = 0
            while (index := data.find(signature, start)) >= 0:
                data[index + offset] |= 0x01
                start = index + 4
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(bytes(data)), max_uncompressed_bytes=10**6)


# ── SEC-R2-01 (review round 2) ──────────────────────────────────────


def _archive_with_part(name: str, data: bytes, *, compression: int) -> bytes:
    """A well-formed archive (manifest lists every part with its true hash) carrying *data* as *name*."""
    import hashlib

    tenant = json.dumps({"name": "Garden", "slug": "garden"}).encode()
    files = {
        "tenant.json": {"rows": 1, "sha256": hashlib.sha256(tenant).hexdigest()},
        name: {"rows": 0, "sha256": hashlib.sha256(data).hexdigest()},
    }
    manifest = json.dumps({"format": "kamerplanter-tenant-export/1", "source_tenant_key": SOURCE, "files": files})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as out:
        out.writestr("manifest.json", manifest, compress_type=zipfile.ZIP_DEFLATED)
        out.writestr("tenant.json", tenant, compress_type=zipfile.ZIP_DEFLATED)
        out.writestr(name, data, compress_type=compression)
    return buffer.getvalue()


class TestTheDocumentsAreBoundedBeforeTheyAreParsed:
    def test_the_documents_together_are_bounded_apart_from_the_objects(self) -> None:
        data = _archive_with_part("collections/sites.jsonl", b"{}\n" * 1000, compression=zipfile.ZIP_STORED)
        with pytest.raises(TenantArchiveError) as refused:
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**8, max_document_bytes=2000)
        assert "documents unpack beyond" in str(refused.value)

    def test_the_caller_cannot_raise_the_total_past_the_fixed_ceiling(self, monkeypatch) -> None:
        import app.domain.engines.tenant_export_engine as engine

        monkeypatch.setattr(engine, "MAX_UNCOMPRESSED_BYTES", 2000)
        data = _archive_with_part("objects/plant/a.bin", b"0" * 4000, compression=zipfile.ZIP_STORED)
        with pytest.raises(TenantArchiveError) as refused:
            read_tenant_archive(io.BytesIO(data), max_uncompressed_bytes=10**12)
        assert "unpacks beyond" in str(refused.value)
