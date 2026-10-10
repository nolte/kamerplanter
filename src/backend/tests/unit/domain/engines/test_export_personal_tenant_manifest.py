"""#2135 (MT-039) — the Art. 15 bundle carries the subject's **personal** tenant, completely.

Measured before this change: ``DataExportEngine.USER_DATA_MANIFEST`` had no source for
``sites``, ``locations``, ``slots``, ``plant_instances`` or ``planting_runs`` at all, and
``tasks`` / ``attachments`` / ``plant_diary_entries`` only by a user-reference field
(assigned tasks, own uploads, own entries). A personal tenant is named after its owner
and ``Site.gps_coordinates`` there is typically the home address — the bundle said
nothing about it, and the account-erasure notice even told members "data of the garden
itself is not part of the personal data export".

Operator decision 2026-10-04: the export includes the personal tenant completely (sites
with explicit ``gps_coordinates``, locations, slots, plants, runs, tasks, diary,
attachment metadata), filtered by ``tenant_key IN personal_tenant_keys_of(user)``;
organisation tenants are excluded (only the membership appears).
"""

from __future__ import annotations

import re

from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.privacy import DataSourceDefinition

#: The personal-tenant categories the decision names, and the anchor each must use.
EXPECTED: dict[str, tuple[tuple[str, str], ...]] = {
    "sites": (),
    "locations": (("site_key", "sites"),),
    "slots": (("location_key", "locations"), ("site_key", "sites")),
    "plant_instances": (),
    "planting_runs": (),
    "tasks": (),
    "plant_diary_entries": (),
    "attachments": (),
    # #2165 — tanks, watering and feeding logs, sensors and their readings
    "tanks": (),
    "tank_states": (("tank_key", "tanks"),),
    "tank_fill_events": (("tank_key", "tanks"),),
    "maintenance_logs": (("tank_key", "tanks"),),
    "watering_events": (),
    "watering_logs": (),
    "feeding_events": (),
    "sensors": (("tank_key", "tanks"),),
    "sensor_readings": (),
    "sensor_hourly": (),
    "sensor_daily": (),
}

#: A field shaped like another account's key (the R6 pattern of check_privacy_inventory).
_ACCOUNT_KEY = re.compile(r"(^user_key$|_user_key$|_by_key$|_account_key$|_by$|^created_by$|^assigned_to)")


def _personal_sources() -> list[DataSourceDefinition]:
    return [s for s in DataExportEngine().build_export_manifest("u1") if s.personal_tenant_scope is not None]


def test_every_personal_tenant_category_is_a_source() -> None:
    found = {
        s.collection: tuple((hop.field, hop.collection) for hop in s.personal_tenant_scope.via)
        for s in _personal_sources()
    }  # type: ignore[union-attr]

    assert found == EXPECTED


def test_the_site_discloses_its_coordinates_explicitly() -> None:
    (site,) = [s for s in _personal_sources() if s.collection == "sites"]

    assert "gps_coordinates" in site.fields


def test_no_personal_tenant_source_hands_out_another_accounts_key() -> None:
    """Art. 15(4): a shared personal garden holds other members' rows; their account keys stay out."""
    leaking = [f"{s.collection}.{f}" for s in _personal_sources() for f in s.fields if _ACCOUNT_KEY.search(f)]

    assert leaking == []


def test_a_personal_tenant_source_is_neither_user_filtered_nor_gapped() -> None:
    for source in _personal_sources():
        assert source.filter_field is None, source.collection
        assert source.edge_collection is None, source.collection
        assert source.tenant_scoped is False, source.collection
        assert source.disclosure_gap is None, source.collection


def test_the_account_sources_are_untouched() -> None:
    """The assigned-task, own-upload and own-entry sources still exist beside the garden-wide ones."""
    manifest = DataExportEngine().build_export_manifest("u1")
    by_user = {(s.collection, s.filter_field) for s in manifest if s.personal_tenant_scope is None}

    assert ("tasks", "assigned_to_user_key") in by_user
    assert ("attachments", "created_by") in by_user
