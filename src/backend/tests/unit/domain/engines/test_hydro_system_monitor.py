from app.domain.engines.hydro_system_monitor import HydroSystemMonitor


class TestAnalyzeRunoff:
    def setup_method(self):
        self.monitor = HydroSystemMonitor()

    def test_healthy_runoff(self):
        result = self.monitor.analyze_runoff(
            input_ec=1.5, input_ph=6.0,
            runoff_ec=1.6, runoff_ph=6.1,
            input_volume_liters=1.0, runoff_volume_liters=0.18,
        )
        assert result["overall_health"] == "healthy"
        assert result["ec_analysis"]["status"] == "healthy"
        assert result["ph_analysis"]["status"] == "healthy"

    def test_salt_buildup(self):
        result = self.monitor.analyze_runoff(
            input_ec=1.5, input_ph=6.0,
            runoff_ec=2.5, runoff_ph=6.0,
            input_volume_liters=1.0, runoff_volume_liters=0.18,
        )
        assert result["ec_analysis"]["status"] == "warning"
        assert "buildup" in result["ec_analysis"]["action"].lower()

    def test_ph_exhaustion(self):
        result = self.monitor.analyze_runoff(
            input_ec=1.5, input_ph=6.0,
            runoff_ec=1.5, runoff_ph=4.5,
            input_volume_liters=1.0, runoff_volume_liters=0.18,
        )
        assert result["ph_analysis"]["status"] == "warning"

    def test_low_runoff(self):
        result = self.monitor.analyze_runoff(
            input_ec=1.5, input_ph=6.0,
            runoff_ec=1.5, runoff_ph=6.0,
            input_volume_liters=1.0, runoff_volume_liters=0.05,
        )
        assert result["runoff_volume"]["status"] == "low"

    def test_high_runoff(self):
        result = self.monitor.analyze_runoff(
            input_ec=1.5, input_ph=6.0,
            runoff_ec=1.5, runoff_ph=6.0,
            input_volume_liters=1.0, runoff_volume_liters=0.30,
        )
        assert result["runoff_volume"]["status"] == "high"


class TestValidateEC:
    def setup_method(self):
        self.monitor = HydroSystemMonitor()

    def test_valid_coco(self):
        valid, msg = self.monitor.validate_ec_for_substrate(1.5, "coco")
        assert valid is True

    def test_too_high_soil(self):
        valid, msg = self.monitor.validate_ec_for_substrate(2.0, "soil")
        assert valid is False

    def test_too_low_hydro(self):
        valid, msg = self.monitor.validate_ec_for_substrate(0.1, "hydro_solution")
        assert valid is False

    def test_unknown_substrate(self):
        valid, msg = self.monitor.validate_ec_for_substrate(2.0, "unknown")
        assert valid is True
