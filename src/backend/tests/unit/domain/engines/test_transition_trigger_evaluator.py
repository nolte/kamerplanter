"""Tests for TransitionTriggerEvaluator (REQ-003 E1/E2 + gdd)."""

from app.common.enums import PhotoperiodType
from app.domain.engines.transition_trigger_evaluator import TransitionTriggerEvaluator


class TestPhotoperiod:
    def setup_method(self) -> None:
        self.ev = TransitionTriggerEvaluator()

    def test_short_day_fires_when_day_shorter_than_critical(self) -> None:
        # cannabis flip: critical 12h, current day 11h -> fire
        assert self.ev.photoperiod_should_fire(PhotoperiodType.SHORT_DAY, 12.0, 11.0) is True
        assert self.ev.photoperiod_should_fire(PhotoperiodType.SHORT_DAY, 12.0, 13.0) is False

    def test_long_day_fires_when_day_longer_than_critical(self) -> None:
        assert self.ev.photoperiod_should_fire(PhotoperiodType.LONG_DAY, 14.0, 15.0) is True
        assert self.ev.photoperiod_should_fire(PhotoperiodType.LONG_DAY, 14.0, 13.0) is False

    def test_day_neutral_never_fires(self) -> None:
        assert self.ev.photoperiod_should_fire(PhotoperiodType.DAY_NEUTRAL, 12.0, 8.0) is False

    def test_no_critical_length_never_fires(self) -> None:
        assert self.ev.photoperiod_should_fire(PhotoperiodType.SHORT_DAY, None, 8.0) is False


class TestVernalization:
    def setup_method(self) -> None:
        self.ev = TransitionTriggerEvaluator()

    def test_fires_when_chill_days_reach_requirement(self) -> None:
        assert self.ev.vernalization_should_fire(60, 60) is True
        assert self.ev.vernalization_should_fire(60, 61) is True
        assert self.ev.vernalization_should_fire(60, 59) is False

    def test_no_requirement_never_fires(self) -> None:
        assert self.ev.vernalization_should_fire(None, 100) is False
        assert self.ev.vernalization_should_fire(0, 100) is False


class TestGdd:
    def setup_method(self) -> None:
        self.ev = TransitionTriggerEvaluator()

    def test_fires_when_accumulated_reaches_threshold(self) -> None:
        assert self.ev.gdd_should_fire(800.0, 800.0) is True
        assert self.ev.gdd_should_fire(800.0, 950.0) is True
        assert self.ev.gdd_should_fire(800.0, 799.9) is False

    def test_no_threshold_never_fires(self) -> None:
        assert self.ev.gdd_should_fire(None, 5000.0) is False
