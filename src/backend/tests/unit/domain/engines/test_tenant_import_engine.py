"""#2138 (REQ-056 §8.4) — every key is new, every reference is rewritten, nothing foreign is carried."""

from __future__ import annotations

import io
import json
import zipfile
from itertools import count

import pytest

from app.domain.engines.tenant_export_engine import TenantArchiveError, TenantArchiveWriter, read_tenant_archive
from app.domain.engines.tenant_import_engine import TenantImportEngine
from app.domain.models.tenant_export import TenantArchive

SOURCE, TARGET = "ten-src", "ten-new"


def _archive(**collections: list[dict]) -> TenantArchive:
    return TenantArchive(
        format="kamerplanter-tenant-export/1",
        source_tenant_key=SOURCE,
        tenant={"name": "Garden", "slug": "garden"},
        collections=collections,
    )


def _engine(archive: TenantArchive, members: dict[str, str] | None = None) -> TenantImportEngine:
    keys = count(1)
    return TenantImportEngine(
        archive,
        target_tenant_key=TARGET,
        member_accounts=members or {},
        key_factory=lambda: f"new-{next(keys)}",
    )


def test_every_document_gets_a_new_key_and_internal_references_follow() -> None:
    archive = _archive(
        sites=[{"_key": "s1", "tenant_key": SOURCE}],
        locations=[{"_key": "l1", "site_key": "s1", "parent_location_key": "l1"}],
    )
    engine = _engine(archive)

    location = engine.remap_document("locations", archive.collections["locations"][0], existing_global=set())

    site_key = engine.mapping["sites"]["s1"]
    assert location["_key"] == engine.mapping["locations"]["l1"] != "l1"
    assert location["site_key"] == site_key
    assert location["parent_location_key"] == location["_key"]


def test_a_row_of_another_tenant_refuses_the_archive() -> None:
    archive = _archive(sites=[{"_key": "s1", "tenant_key": "ten-foreign"}])
    with pytest.raises(TenantArchiveError):
        _engine(archive).remap_document("sites", archive.collections["sites"][0], existing_global=set())


def test_accounts_are_mapped_or_pseudonymised() -> None:
    archive = _archive(
        plant_instances=[{"_key": "p1", "tenant_key": SOURCE}],
        plant_diary_entries=[
            {"_key": "d1", "tenant_key": SOURCE, "plant_key": "p1", "created_by": "old-lead"},
            {"_key": "d2", "tenant_key": SOURCE, "plant_key": "p1", "created_by": "old-grower"},
        ],
    )
    engine = _engine(archive, {"old-lead": "acc-lead"})
    rows = [
        engine.remap_document("plant_diary_entries", d, existing_global=set())
        for d in archive.collections["plant_diary_entries"]
    ]

    assert [row["created_by"] for row in rows] == ["acc-lead", "_anonymized"]


def test_a_dangling_internal_pointer_is_cleared_never_kept() -> None:
    archive = _archive(plant_instances=[{"_key": "p1", "tenant_key": SOURCE, "mother_key": "gone", "slot_keys": []}])
    engine = _engine(archive)

    plant = engine.remap_document("plant_instances", archive.collections["plant_instances"][0], existing_global=set())

    assert plant["mother_key"] is None
    assert engine.nulled_references == 1


def test_a_hybrid_catalogue_reference_is_kept_only_when_the_target_has_the_global_row() -> None:
    archive = _archive(plant_instances=[{"_key": "p1", "tenant_key": SOURCE, "species_key": "sp-1"}])
    engine = _engine(archive)
    assert engine.catalogue_requirements() == {"species": {"sp-1"}}

    kept = engine.remap_document(
        "plant_instances", archive.collections["plant_instances"][0], existing_global={"species/sp-1"}
    )
    cleared = engine.remap_document("plant_instances", archive.collections["plant_instances"][0], existing_global=set())

    assert kept["species_key"] == "sp-1"
    assert cleared["species_key"] is None


def test_polymorphic_and_storage_references() -> None:
    archive = _archive(
        plant_instances=[{"_key": "p1", "tenant_key": SOURCE, "photo_refs": ["a1", f"t/{SOURCE}/plant/x.jpg"]}],
        attachments=[{"_key": "a1", "tenant_key": SOURCE, "storage_key": f"t/{SOURCE}/plant/2026/10/a1.jpg"}],
        tasks=[{"_key": "k1", "tenant_key": SOURCE, "entity_type": "plant_instance", "entity_key": "p1"}],
    )
    engine = _engine(archive)

    task = engine.remap_document("tasks", archive.collections["tasks"][0], existing_global=set())
    attachment = engine.remap_document("attachments", archive.collections["attachments"][0], existing_global=set())
    plant = engine.remap_document("plant_instances", archive.collections["plant_instances"][0], existing_global=set())

    assert task["entity_key"] == engine.mapping["plant_instances"]["p1"]
    assert attachment["storage_key"] == f"t/{TARGET}/plant/2026/10/a1.jpg"
    assert plant["photo_refs"] == [engine.mapping["attachments"]["a1"], f"t/{TARGET}/plant/x.jpg"]


def test_an_undeclared_key_field_refuses_the_archive() -> None:
    archive = _archive(sites=[{"_key": "s1", "tenant_key": SOURCE, "brand_new_key": "x"}])
    with pytest.raises(TenantArchiveError) as refused:
        TenantImportEngine.validate_structure(archive)
    assert refused.value.code == "IMPORT_UNDECLARED_REFERENCE"
    assert refused.value.entries == ["sites.brand_new_key"]


def test_a_collection_the_import_never_writes_refuses_the_archive() -> None:
    archive = _archive(users=[{"_key": "u1", "email": "x@example.com"}])
    with pytest.raises(TenantArchiveError) as refused:
        TenantImportEngine.validate_structure(archive)
    assert refused.value.entries == ["users"]


def test_edges_keep_only_ends_with_a_place_in_the_target() -> None:
    archive = _archive(sites=[{"_key": "s1", "tenant_key": SOURCE}], locations=[{"_key": "l1", "site_key": "s1"}])
    engine = _engine(archive)

    inside = engine.remap_edge({"_key": "e1", "_from": "sites/s1", "_to": "locations/l1"}, existing_global=set())
    onto_tenant = engine.remap_edge({"_from": f"tenants/{SOURCE}", "_to": "sites/s1"}, existing_global=set())
    onto_account = engine.remap_edge({"_from": "users/u1", "_to": "sites/s1"}, existing_global=set())

    assert inside == {
        "_from": f"sites/{engine.mapping['sites']['s1']}",
        "_to": f"locations/{engine.mapping['locations']['l1']}",
    }
    assert onto_tenant is not None and onto_tenant["_from"] == f"tenants/{TARGET}"
    assert onto_account is None


class TestTheArchiveFormat:
    def _write(self) -> bytes:
        buffer = io.BytesIO()
        writer = TenantArchiveWriter(buffer, max_bytes=None)
        writer.write_json("tenant.json", {"name": "Garden", "slug": "garden"})
        writer.write_lines("collections/sites.jsonl", [[{"_key": "s1", "tenant_key": SOURCE}]])
        writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": SOURCE})
        return buffer.getvalue()

    def test_a_written_archive_reads_back(self) -> None:
        archive = read_tenant_archive(io.BytesIO(self._write()), max_uncompressed_bytes=10**6)
        assert archive.collections == {"sites": [{"_key": "s1", "tenant_key": SOURCE}]}

    def test_a_tampered_part_fails_its_checksum(self) -> None:
        source = zipfile.ZipFile(io.BytesIO(self._write()))
        tampered = io.BytesIO()
        with zipfile.ZipFile(tampered, "w") as out:
            for name in source.namelist():
                data = source.read(name)
                if name == "collections/sites.jsonl":
                    data = json.dumps({"_key": "s1", "tenant_key": "ten-foreign"}).encode() + b"\n"
                out.writestr(name, data)
        with pytest.raises(TenantArchiveError) as refused:
            read_tenant_archive(io.BytesIO(tampered.getvalue()), max_uncompressed_bytes=10**6)
        assert refused.value.code == "IMPORT_CHECKSUM_MISMATCH"

    def test_an_unknown_format_is_refused(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as out:
            out.writestr("manifest.json", json.dumps({"format": "kamerplanter-tenant-export/99", "files": {}}))
        with pytest.raises(TenantArchiveError) as refused:
            read_tenant_archive(io.BytesIO(buffer.getvalue()), max_uncompressed_bytes=10**6)
        assert refused.value.code == "IMPORT_FORMAT_UNSUPPORTED"

    def test_a_zip_bomb_is_refused_by_its_directory(self) -> None:
        with pytest.raises(TenantArchiveError):
            read_tenant_archive(io.BytesIO(self._write()), max_uncompressed_bytes=10)


def _site_with_underlay(attachment_key: str) -> dict:
    return {
        "_key": "s1",
        "tenant_key": SOURCE,
        "plan": {"plan_revision": 1, "underlay": {"attachment_key": attachment_key, "opacity": 0.5}},
    }


def test_an_underlay_follows_its_attachment_to_the_new_key() -> None:
    archive = _archive(sites=[_site_with_underlay("a1")], attachments=[{"_key": "a1", "tenant_key": SOURCE}])
    engine = _engine(archive)

    site = engine.remap_document("sites", archive.collections["sites"][0], existing_global=set())

    assert site["plan"]["underlay"]["attachment_key"] == engine.mapping["attachments"]["a1"] != "a1"


def test_an_underlay_whose_attachment_is_not_in_the_archive_is_dropped_not_half_kept() -> None:
    archive = _archive(sites=[_site_with_underlay("missing")])
    engine = _engine(archive)

    site = engine.remap_document("sites", archive.collections["sites"][0], existing_global=set())

    assert "underlay" not in site["plan"] and site["plan"]["plan_revision"] == 1


def test_remapping_a_row_twice_gives_the_same_row_because_the_archive_is_not_rewritten_in_place() -> None:
    """The validation pass and the write pass run on the same rows; a nested key must map both times."""
    archive = _archive(sites=[_site_with_underlay("a1")], attachments=[{"_key": "a1", "tenant_key": SOURCE}])
    engine = _engine(archive)
    row = archive.collections["sites"][0]

    first = engine.remap_document("sites", row, existing_global=set())
    second = engine.remap_document("sites", row, existing_global=set())

    assert first == second and row["plan"]["underlay"]["attachment_key"] == "a1"


class TestProvenanceReferences:
    """#2528: a bed's template and substrate are provenance - resolved like any catalogue key, never refusing."""

    @staticmethod
    def _bed_archive(**bed: object) -> TenantArchive:
        return _archive(
            sites=[{"_key": "s1", "tenant_key": SOURCE}],
            locations=[{"_key": "l1", "site_key": "s1", **bed}],
            plant_instances=[{"_key": "p1", "tenant_key": SOURCE, "species_key": "sp-1"}],
        )

    def test_a_provenance_key_is_optional_and_a_species_key_still_refuses(self) -> None:
        engine = _engine(self._bed_archive(template_key="tpl-gone", soil_profile={"substrate_key": "sub-gone"}))

        assert engine.catalogue_requirements() == {"species": {"sp-1"}}
        assert engine.optional_catalogue_requirements() == {
            "bed_templates": {"tpl-gone"},
            "substrates": {"sub-gone"},
        }

    def test_the_single_views_are_the_halves_of_catalogue_needs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """#2513 review R5: the two single views read :meth:`catalogue_needs` - one derivation, not two."""
        engine = _engine(self._bed_archive(template_key="tpl-gone"))
        pair = ({"species": {"sp-x"}}, {"bed_templates": {"tpl-x"}})
        monkeypatch.setattr(engine, "catalogue_needs", lambda: pair)

        assert engine.catalogue_requirements() is pair[0]
        assert engine.optional_catalogue_requirements() is pair[1]

    def test_a_provenance_key_held_by_the_archive_needs_no_catalogue(self) -> None:
        archive = self._bed_archive(template_key="tpl-1")
        archive.collections["bed_templates"] = [{"_key": "tpl-1", "tenant_key": SOURCE}]

        engine = _engine(archive)
        bed = engine.remap_document("locations", archive.collections["locations"][0], existing_global=set())

        assert engine.optional_catalogue_requirements() == {}
        assert bed["template_key"] == engine.mapping["bed_templates"]["tpl-1"]
        assert engine.nulled_references == 0

    def test_a_missing_provenance_key_is_cleared_and_counted(self) -> None:
        archive = self._bed_archive(template_key="tpl-gone", soil_profile={"substrate_key": "sub-gone"})
        engine = _engine(archive)

        bed = engine.remap_document("locations", archive.collections["locations"][0], existing_global=set())

        assert bed["template_key"] is None and bed["soil_profile"]["substrate_key"] is None
        assert engine.nulled_references == 2

    def test_an_existing_system_template_is_kept(self) -> None:
        archive = self._bed_archive(template_key="sys_bed_2x1", soil_profile={"substrate_key": "sub-global"})
        engine = _engine(archive)

        bed = engine.remap_document(
            "locations",
            archive.collections["locations"][0],
            existing_global={"bed_templates/sys_bed_2x1", "substrates/sub-global"},
        )

        assert bed["template_key"] == "sys_bed_2x1" and bed["soil_profile"]["substrate_key"] == "sub-global"
        assert engine.nulled_references == 0
