from app.domain.engines.vernalization_tracker import VernalizationTracker


class TestVernalizationProgress:
    def setup_method(self):
        self.tracker = VernalizationTracker()

    def test_zero_progress(self):
        result = self.tracker.calculate_vernalization_progress(0, 30)
        assert result["progress_percent"] == 0.0
        assert result["days_remaining"] == 30
        assert result["is_complete"] is False

    def test_half_progress(self):
        result = self.tracker.calculate_vernalization_progress(15, 30)
        assert result["progress_percent"] == 50.0
        assert result["days_remaining"] == 15

    def test_complete(self):
        result = self.tracker.calculate_vernalization_progress(30, 30)
        assert result["is_complete"] is True
        assert result["progress_percent"] == 100.0
        assert result["days_remaining"] == 0

    def test_over_complete(self):
        result = self.tracker.calculate_vernalization_progress(40, 30)
        assert result["is_complete"] is True
        assert result["progress_percent"] == 100.0

    def test_zero_required(self):
        result = self.tracker.calculate_vernalization_progress(0, 0)
        assert result["is_complete"] is True


class TestColdDay:
    def setup_method(self):
        self.tracker = VernalizationTracker()

    def test_cold_day(self):
        assert self.tracker.is_cold_day(3.0) is True

    def test_warm_day(self):
        assert self.tracker.is_cold_day(10.0) is False

    def test_at_threshold(self):
        assert self.tracker.is_cold_day(5.0) is True

    def test_custom_threshold(self):
        assert self.tracker.is_cold_day(7.0, threshold_c=8.0) is True
