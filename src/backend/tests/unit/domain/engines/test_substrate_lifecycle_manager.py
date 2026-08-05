from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import IrrigationStrategy, SubstrateType
from app.domain.engines.substrate_lifecycle_manager import (
    IRRIGATION_STRATEGY_MAP,
    SubstrateLifecycleManager,
)
from app.domain.models.substrate import Substrate, SubstrateBatch


def _make_substrate(
    key: str = "sub1",
    substrate_type: SubstrateType = SubstrateType.COCO,
    reusable: bool = True,
    max_cycles: int = 3,
    ec_base: float = 0.5,
) -> Substrate:
    return Substrate(
        _key=key,
        type=substrate_type,
        reusable=reusable,
        max_reuse_cycles=max_cycles,
        ec_base_ms=ec_base,
    )


def _make_batch(
    key: str = "batch1",
    substrate_key: str = "sub1",
    cycles: int = 1,
    ph_current: float | None = 6.0,
    ec_current: float | None = 0.6,
    ph_history: list[float] | None = None,
    ec_history: list[float] | None = None,
) -> SubstrateBatch:
    return SubstrateBatch(
        _key=key,
        batch_id="B001",
        substrate_key=substrate_key,
        volume_liters=10.0,
        mixed_on=date(2024, 1, 1),
        cycles_used=cycles,
        ph_current=ph_current,
        ec_current_ms=ec_current,
        ph_history=ph_history or [],
        ec_history=ec_history or [],
    )


def _make_manager(substrate: Substrate | None, batch: SubstrateBatch | None) -> SubstrateLifecycleManager:
    repo = MagicMock()
    repo.get_batch_by_key.return_value = batch
    repo.get_substrate_by_key.return_value = substrate
    return SubstrateLifecycleManager(repo)


class TestCheckReusability:
    def test_batch_not_found(self):
        mgr = _make_manager(None, None)
        can_reuse, issues, *_ = mgr.check_reusability("missing")
        assert can_reuse is False
        assert "Batch not found" in issues

    def test_substrate_not_found(self):
        batch = _make_batch()
        mgr = _make_manager(None, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert "Substrate type not found" in issues

    def test_disposable_rockwool_plug(self):
        substrate = _make_substrate(substrate_type=SubstrateType.ROCKWOOL_PLUG, reusable=True)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert any("disposable" in i for i in issues)

    def test_disposable_peat(self):
        substrate = _make_substrate(substrate_type=SubstrateType.PEAT, reusable=True)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False

    def test_not_reusable(self):
        substrate = _make_substrate(reusable=False)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert "not reusable" in issues[0]

    def test_max_cycles_exceeded(self):
        substrate = _make_substrate(max_cycles=2)
        batch = _make_batch(cycles=2)
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert "Max reuse cycles" in issues[0]

    def test_ph_stddev_rejection(self):
        substrate = _make_substrate(substrate_type=SubstrateType.COCO)
        batch = _make_batch(ph_history=[5.0, 6.5, 7.5, 5.5])  # high stddev
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert any("pH instability" in i for i in issues)

    def test_ec_delta_rejection(self):
        substrate = _make_substrate(ec_base=0.5)
        batch = _make_batch(ec_current=3.0, ph_history=[])
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is False
        assert any("EC drift" in i for i in issues)

    def test_coco_reusable_success(self):
        substrate = _make_substrate(substrate_type=SubstrateType.COCO)
        batch = _make_batch(ph_history=[6.0, 6.1, 6.0], ec_current=0.6)
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, prep_steps, prep_time, ready_date = mgr.check_reusability("batch1")
        assert can_reuse is True
        assert issues == []
        assert len(prep_steps) > 0
        assert prep_time > 0
        assert ready_date is not None

    def test_living_soil_higher_ph_tolerance(self):
        substrate = _make_substrate(substrate_type=SubstrateType.LIVING_SOIL)
        batch = _make_batch(ph_history=[6.0, 6.5, 6.2, 6.8])  # stddev ~0.35, below 0.7
        mgr = _make_manager(substrate, batch)
        can_reuse, issues, *_ = mgr.check_reusability("batch1")
        assert can_reuse is True


class TestPrepareForReuse:
    def test_coco_preparation_steps(self):
        substrate = _make_substrate(substrate_type=SubstrateType.COCO)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        steps, total = mgr.prepare_for_reuse(substrate, batch)
        assert len(steps) == 3
        assert any("CalMag" in s["step"] for s in steps)
        assert total > 0

    def test_clay_pebbles_preparation(self):
        substrate = _make_substrate(substrate_type=SubstrateType.CLAY_PEBBLES)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        steps, total = mgr.prepare_for_reuse(substrate, batch)
        assert len(steps) >= 2
        assert any("H2O2" in s["step"] for s in steps)

    def test_living_soil_preparation(self):
        substrate = _make_substrate(substrate_type=SubstrateType.LIVING_SOIL)
        batch = _make_batch()
        mgr = _make_manager(substrate, batch)
        steps, total = mgr.prepare_for_reuse(substrate, batch)
        assert any("mycorrhizae" in s["step"] for s in steps)
        assert total >= 168  # 7 days microbial rest


class TestIrrigationStrategy:
    def test_all_substrate_types_have_strategy(self):
        for st in SubstrateType:
            assert st in IRRIGATION_STRATEGY_MAP

    def test_coco_frequent(self):
        assert SubstrateLifecycleManager.get_irrigation_strategy(SubstrateType.COCO) == IrrigationStrategy.FREQUENT

    def test_living_soil_infrequent(self):
        result = SubstrateLifecycleManager.get_irrigation_strategy(SubstrateType.LIVING_SOIL)
        assert result == IrrigationStrategy.INFREQUENT

    def test_rockwool_continuous(self):
        result = SubstrateLifecycleManager.get_irrigation_strategy(SubstrateType.ROCKWOOL_SLAB)
        assert result == IrrigationStrategy.CONTINUOUS


class TestCompositionValidation:
    def test_valid_composition(self):
        s = Substrate(type=SubstrateType.COCO, composition={"coco_coir": 0.7, "perlite": 0.3})
        assert abs(sum(s.composition.values()) - 1.0) < 0.01

    def test_invalid_composition_sum(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            Substrate(type=SubstrateType.COCO, composition={"coco_coir": 0.5, "perlite": 0.2})

    def test_empty_composition_allowed(self):
        s = Substrate(type=SubstrateType.COCO, composition={})
        assert s.composition == {}

    def test_none_type_empty_composition(self):
        s = Substrate(type=SubstrateType.NONE, composition={})
        assert s.type == SubstrateType.NONE

    def test_none_type_rejects_composition(self):
        with pytest.raises(ValueError, match="empty"):
            Substrate(type=SubstrateType.NONE, composition={"water": 1.0})
