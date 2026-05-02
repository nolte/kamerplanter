"""REQ-014 v1.6 (W-021) WateringEvent dual-support tests.

Verifies that the spec-canonical fields (slot_keys, target_ec_ms,
measured_ec_ms, runoff_ec_ms) and the deprecated legacy fields
(plant_keys, target_ec, measured_ec, runoff_ec) stay in lockstep on
both input and output.
"""

from app.domain.models.watering_event import WateringEvent


def _base_kwargs() -> dict:
    return {"volume_liters": 1.0}


class TestSlotKeysAlias:
    def test_slot_keys_input_mirrors_to_plant_keys(self):
        ev = WateringEvent(**_base_kwargs(), slot_keys=["s1", "s2"])
        assert ev.slot_keys == ["s1", "s2"]
        assert ev.plant_keys == ["s1", "s2"]

    def test_plant_keys_input_mirrors_to_slot_keys(self):
        ev = WateringEvent(**_base_kwargs(), plant_keys=["p1"])
        assert ev.slot_keys == ["p1"]
        assert ev.plant_keys == ["p1"]

    def test_both_unset_keeps_empty_lists(self):
        ev = WateringEvent(**_base_kwargs())
        assert ev.slot_keys == []
        assert ev.plant_keys == []

    def test_slot_keys_takes_precedence_when_both_provided(self):
        ev = WateringEvent(**_base_kwargs(), slot_keys=["a"], plant_keys=["b"])
        # When both are supplied the validator does not overwrite — the caller
        # is responsible for sending consistent data.
        assert ev.slot_keys == ["a"]
        assert ev.plant_keys == ["b"]


class TestEcMsAlias:
    def test_ec_ms_input_mirrors_to_unit_less_alias(self):
        ev = WateringEvent(
            **_base_kwargs(),
            target_ec_ms=1.5,
            measured_ec_ms=1.4,
            runoff_ec_ms=1.7,
        )
        assert ev.target_ec == 1.5
        assert ev.measured_ec == 1.4
        assert ev.runoff_ec == 1.7

    def test_legacy_ec_input_mirrors_to_ms_canonical(self):
        ev = WateringEvent(
            **_base_kwargs(),
            target_ec=2.0,
            measured_ec=1.9,
            runoff_ec=2.1,
        )
        assert ev.target_ec_ms == 2.0
        assert ev.measured_ec_ms == 1.9
        assert ev.runoff_ec_ms == 2.1

    def test_unset_remains_none_on_both_aliases(self):
        ev = WateringEvent(**_base_kwargs())
        assert ev.target_ec_ms is None
        assert ev.target_ec is None
        assert ev.measured_ec_ms is None
        assert ev.measured_ec is None
        assert ev.runoff_ec_ms is None
        assert ev.runoff_ec is None
