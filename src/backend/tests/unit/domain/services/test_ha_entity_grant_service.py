"""The per-tenant Home Assistant entity allowlist itself (MT-015, #2112).

The gate every read, write and dispatch asks; tested here for the properties a
caller relies on: per tenant, fail-closed, value-free refusals, idempotent grants.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import ValidationError
from app.domain.interfaces.ha_entity_gate import DenyAllHaEntityGate
from app.domain.services.ha_entity_grant_service import (
    HA_ENTITY_NOT_GRANTED,
    MAX_GRANTS_PER_REQUEST,
    HaEntityGrantSnapshot,
    only_granted,
    require_granted,
)
from tests.support.ha_entity_grants import grant_service

A, B = "tenant-a", "tenant-b"


class TestIsGranted:
    def test_a_grant_belongs_to_one_tenant(self) -> None:
        grants = grant_service({A: {"sensor.tent"}})

        assert grants.is_granted(A, "sensor.tent")
        assert not grants.is_granted(B, "sensor.tent")

    @pytest.mark.parametrize("tenant_key", ["", None])
    def test_no_tenant_has_no_grants(self, tenant_key) -> None:
        grants = grant_service({A: {"sensor.tent"}})

        assert not grants.is_granted(tenant_key, "sensor.tent")
        assert grants.granted_entity_ids(tenant_key) == frozenset()

    @pytest.mark.parametrize(
        "entity_id", [None, "", "sensor", "Sensor.Tent", "sensor.tent/../../config", "sensor.tent\n"]
    )
    def test_a_malformed_id_is_never_granted(self, entity_id) -> None:
        assert not grant_service({A: {"sensor.tent"}}).is_granted(A, entity_id)

    def test_the_snapshot_answers_like_the_service(self) -> None:
        grants = grant_service({A: {"sensor.tent"}, B: {"switch.fan"}})
        snapshot = grants.snapshot()

        assert isinstance(snapshot, HaEntityGrantSnapshot)
        for tenant in (A, B, ""):
            for entity in ("sensor.tent", "switch.fan", "sensor.other"):
                assert snapshot.is_granted(tenant, entity) == grants.is_granted(tenant, entity)
            assert snapshot.granted_entity_ids(tenant) == grants.granted_entity_ids(tenant)

    def test_the_absent_gate_grants_nothing(self) -> None:
        gate = DenyAllHaEntityGate()

        assert not gate.is_granted(A, "sensor.tent")
        assert gate.granted_entity_ids(A) == frozenset()


class TestRequireGranted:
    def test_unset_references_need_no_grant(self) -> None:
        require_granted(DenyAllHaEntityGate(), A, {"ha_entity_id": None, "weather_entity_id": ""})

    def test_a_granted_reference_passes(self) -> None:
        grant_service({A: {"sensor.tent"}}).require_granted(A, {"ha_entity_id": "sensor.tent"})

    def test_each_refused_field_is_named_without_its_value(self) -> None:
        grants = grant_service({A: {"sensor.tent"}})

        with pytest.raises(ValidationError) as caught:
            grants.require_granted(
                A, {"temp_min_entity": "sensor.tent", "humidity_entity": "sensor.door", "wind": "sensor.window"}
            )

        error = caught.value
        assert error.status_code == 422
        assert [(d["field"], d["code"]) for d in error.details] == [
            ("humidity_entity", HA_ENTITY_NOT_GRANTED),
            ("wind", HA_ENTITY_NOT_GRANTED),
        ]
        rendered = repr(error.message) + repr(error.details)
        assert "sensor.door" not in rendered and "sensor.window" not in rendered

    def test_another_tenants_grant_does_not_help(self) -> None:
        with pytest.raises(ValidationError):
            grant_service({B: {"sensor.tent"}}).require_granted(A, {"ha_entity_id": "sensor.tent"})


class TestOnlyGranted:
    def test_a_listing_is_reduced_to_the_tenants_grants(self) -> None:
        listing = [{"entity_id": "sensor.tent"}, {"entity_id": "sensor.door"}, {"friendly_name": "no id"}]

        assert only_granted(grant_service({A: {"sensor.tent"}}), A, listing) == [{"entity_id": "sensor.tent"}]
        assert only_granted(DenyAllHaEntityGate(), A, listing) == []


class TestAdministration:
    def test_granting_is_idempotent_and_counts_only_new_grants(self) -> None:
        grants = grant_service({A: {"sensor.tent"}})

        assert grants.grant(A, ["sensor.tent", "switch.fan", "switch.fan"]) == 1
        assert grants.grant(A, ["switch.fan"]) == 0
        assert [g.entity_id for g in grants.list_grants(A)] == ["sensor.tent", "switch.fan"]

    def test_a_notify_service_is_granted_like_an_entity(self) -> None:
        grants = grant_service()

        grants.grant(A, ["notify.mobile_app_phone"])

        assert grants.is_granted(A, "notify.mobile_app_phone")

    def test_a_malformed_id_is_refused_and_nothing_is_granted(self) -> None:
        grants = grant_service()

        with pytest.raises(ValidationError):
            grants.grant(A, ["sensor.ok", "../etc/passwd"])

        assert grants.list_grants(A) == []

    def test_a_request_is_bounded(self) -> None:
        with pytest.raises(ValidationError):
            grant_service().grant(A, [f"sensor.s{i}" for i in range(MAX_GRANTS_PER_REQUEST + 1)])

    def test_revoking_withdraws_one_grant_of_one_tenant(self) -> None:
        grants = grant_service({A: {"sensor.tent", "switch.fan"}, B: {"sensor.tent"}})

        assert grants.revoke(A, "sensor.tent") is True
        assert grants.revoke(A, "sensor.tent") is False
        assert grants.granted_entity_ids(A) == frozenset({"switch.fan"})
        assert grants.granted_entity_ids(B) == frozenset({"sensor.tent"})


class _Inventory:
    def __init__(self, entities: list[dict] | Exception) -> None:
        self._entities = entities

    def list_entities(self) -> list[dict]:
        if isinstance(self._entities, Exception):
            raise self._entities
        return self._entities


class TestInventory:
    def test_each_entity_is_marked_for_the_tenant_and_stale_grants_are_listed(self) -> None:
        live = [
            {"entity_id": "sensor.tent", "domain": "sensor", "friendly_name": "Tent"},
            {"entity_id": "switch.fan", "domain": "switch", "friendly_name": "Fan"},
        ]
        grants = grant_service({A: {"sensor.tent", "sensor.gone"}}, ha_client_factory=lambda: _Inventory(live))

        configured, entries = grants.inventory(A)

        assert configured is True
        assert [(e["entity_id"], e["granted"], e["present"]) for e in entries] == [
            ("sensor.gone", True, False),
            ("sensor.tent", True, True),
            ("switch.fan", False, True),
        ]

    def test_an_unreachable_home_assistant_yields_the_grants_alone(self) -> None:
        grants = grant_service({A: {"sensor.tent"}}, ha_client_factory=lambda: _Inventory(RuntimeError("down")))

        configured, entries = grants.inventory(A)

        assert configured is True
        assert [(e["entity_id"], e["present"]) for e in entries] == [("sensor.tent", False)]

    def test_without_home_assistant_the_inventory_says_so(self) -> None:
        configured, entries = grant_service({A: {"sensor.tent"}}, ha_client_factory=lambda: None).inventory(A)

        assert configured is False
        assert [e["entity_id"] for e in entries] == ["sensor.tent"]


class TestLightModeGrantsOnUse:
    """Light mode (REQ-027): one household, its operator is the only user and has no admin panel.

    Binding an entity grants it (source ``light_mode``) instead of being refused, so the
    rows a later switch to full mode is checked against exist. Reads stay gated.
    """

    def test_binding_records_a_grant_instead_of_refusing(self) -> None:
        grants = grant_service(grant_on_use=True)

        require_granted(grants, A, {"ha_entity_id": "sensor.tent"})

        assert grants.is_granted(A, "sensor.tent")
        assert [g.source for g in grants.list_grants(A)] == ["light_mode"]

    def test_a_malformed_id_is_still_refused(self) -> None:
        grants = grant_service(grant_on_use=True)

        with pytest.raises(ValidationError):
            require_granted(grants, A, {"ha_entity_id": "Sensor With Spaces"})

        assert grants.list_grants(A) == []

    def test_no_tenant_is_never_admitted(self) -> None:
        with pytest.raises(ValidationError):
            require_granted(grant_service(grant_on_use=True), "", {"ha_entity_id": "sensor.tent"})

    def test_the_listing_is_the_whole_inventory(self) -> None:
        listing = [{"entity_id": "sensor.tent"}, {"entity_id": "sensor.door"}]

        assert only_granted(grant_service(grant_on_use=True), A, listing) == listing

    def test_reads_stay_gated_until_something_is_bound(self) -> None:
        grants = grant_service(grant_on_use=True)

        assert not grants.is_granted(A, "sensor.tent")

    def test_full_mode_admits_nothing(self) -> None:
        grants = grant_service()

        with pytest.raises(ValidationError):
            require_granted(grants, A, {"ha_entity_id": "sensor.tent"})
        assert grants.list_grants(A) == []


class TestTheFactoryFollowsTheMode:
    """The DI factory decides grant-on-use from the operating mode — full mode never admits."""

    @pytest.mark.parametrize(("mode", "admits"), [("full", False), ("light", True)])
    def test_grant_on_use_only_in_light_mode(self, monkeypatch: pytest.MonkeyPatch, mode: str, admits: bool) -> None:
        from unittest.mock import MagicMock

        from app.common import dependencies
        from app.config.settings import settings

        monkeypatch.setattr(settings, "kamerplanter_mode", mode)
        monkeypatch.setattr(dependencies, "get_db", MagicMock())

        assert dependencies.get_ha_entity_grant_service().admits_on_use() is admits
