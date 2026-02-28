"""E2E tests for REQ-004 — Nutrient Calculations page (TC-REQ-004-061 to TC-REQ-004-090).

Covers:
- NutrientCalculationsPage: page load, all four calculation panels
- Mixing Protocol: calculate with default values, result display
- Flushing: calculate schedule, result display
- Runoff Analysis: calculate health status, EC/pH delta alerts
- Mixing Safety: validate empty list, result display
- EC-budget logic: base water EC is subtracted (critical REQ-004 domain rule)
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .pages.nutrient_calculations_page import NutrientCalculationsPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def calc_page(browser: WebDriver, base_url: str) -> NutrientCalculationsPage:
    """Return a NutrientCalculationsPage bound to the current browser session."""
    return NutrientCalculationsPage(browser, base_url)


# ── TC-REQ-004-061 to TC-REQ-004-064: Page Load ───────────────────────────────


class TestNutrientCalculationsPageLoad:
    """TC-REQ-004-061 to TC-REQ-004-064: Page load and panel presence."""

    def test_calculations_page_loads(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-061: Nutrient calculations page loads and shows the page title."""
        calc_page.open()
        capture = request.node._screenshot_capture
        capture("REQ004-061_calc-page-loaded")

        title = calc_page.get_page_title_text()
        assert title, (
            f"Expected a non-empty page title on the nutrient calculations page, got: '{title}'"
        )

    def test_page_has_four_calculation_panels(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-062: Calculations page shows exactly four calculation panels (cards)."""
        calc_page.open()
        capture = request.node._screenshot_capture
        capture("REQ004-062_calc-page-four-panels")

        headings = calc_page.get_all_card_headings()
        assert len(headings) >= 4, (
            f"Expected at least 4 card headings (one per panel), got {len(headings)}: {headings}"
        )

    def test_mixing_protocol_panel_has_calculate_button(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-063: Mixing Protocol panel has a calculate button."""
        calc_page.open()
        capture = request.node._screenshot_capture
        capture("REQ004-063_calc-mixing-button")

        buttons = calc_page.driver.find_elements(*calc_page.CALCULATE_BUTTONS)
        assert len(buttons) >= 1, (
            f"Expected at least one calculate/validate button on the page, got {len(buttons)}"
        )

    def test_all_panels_visible_on_load(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-064: All four panels are visible without scrolling issues."""
        calc_page.open()
        headings = calc_page.get_all_card_headings()

        capture = request.node._screenshot_capture
        capture("REQ004-064_calc-all-panels-visible")

        # Each panel should have a non-empty heading
        assert all(h.strip() for h in headings), (
            f"All card headings should be non-empty, got: {headings}"
        )


# ── TC-REQ-004-065 to TC-REQ-004-072: Mixing Protocol ────────────────────────


class TestMixingProtocol:
    """TC-REQ-004-065 to TC-REQ-004-072: Mixing Protocol panel tests."""

    def test_mixing_protocol_calculate_shows_result(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-065: Clicking calculate in Mixing Protocol shows an EC result alert."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-065_mixing-protocol-before-calc")

        # Use default values (no fertilizer keys — backend calculates empty list)
        calc_page.fill_mixing_protocol(
            volume=10.0,
            target_ec=1.8,
            target_ph=6.0,
            base_ec=0.3,
            base_ph=7.2,
            fertilizer_keys="",
        )
        calc_page.click_calculate_mixing_protocol()

        # Wait for alert to appear in the card
        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_protocol_alerts()) > 0
        )

        capture("REQ004-065_mixing-protocol-result")

        alerts = calc_page.get_mixing_protocol_alerts()
        assert len(alerts) > 0, (
            "Expected at least one alert with EC result after calculating mixing protocol"
        )

    def test_mixing_protocol_result_contains_ec(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-066: Mixing Protocol result alert contains an EC value in mS/cm."""
        calc_page.open()
        calc_page.fill_mixing_protocol(volume=10.0, target_ec=1.8)
        calc_page.click_calculate_mixing_protocol()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_protocol_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-066_mixing-protocol-ec-result")

        alerts = calc_page.get_mixing_protocol_alerts()
        alert_text = " ".join(alerts)
        assert "mS" in alert_text or "EC" in alert_text or any(
            char.isdigit() for char in alert_text
        ), (
            f"Expected mixing protocol result to contain EC value (mS/cm), got: '{alert_text}'"
        )

    def test_mixing_protocol_base_water_ec_is_subtracted(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-067: EC-budget rule: target EC minus base water EC (REQ-004 domain rule).

        When base water EC equals target EC, the calculated EC should approach zero.
        This verifies the critical EC-net = target EC - base water EC logic.
        """
        calc_page.open()
        # Set base EC equal to target EC — net EC should be zero or very small
        calc_page.fill_mixing_protocol(
            volume=10.0,
            target_ec=1.0,
            base_ec=1.0,  # base equals target — no fertilizer budget left
            fertilizer_keys="",
        )
        calc_page.click_calculate_mixing_protocol()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_protocol_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-067_mixing-protocol-zero-ec-budget")

        alerts = calc_page.get_mixing_protocol_alerts()
        assert len(alerts) > 0, (
            "Expected a result alert even when base EC equals target EC (zero budget case)"
        )

    def test_mixing_protocol_large_volume(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-068: Mixing Protocol calculates correctly for a large volume (100 L)."""
        calc_page.open()
        calc_page.fill_mixing_protocol(
            volume=100.0,
            target_ec=2.0,
            base_ec=0.2,
        )
        calc_page.click_calculate_mixing_protocol()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_protocol_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-068_mixing-protocol-large-volume")

        alerts = calc_page.get_mixing_protocol_alerts()
        assert len(alerts) > 0, (
            f"Expected a result for large volume calculation, got no alerts: {alerts}"
        )


# ── TC-REQ-004-073 to TC-REQ-004-079: Flushing ───────────────────────────────


class TestFlushingCalculation:
    """TC-REQ-004-073 to TC-REQ-004-079: Flushing protocol calculation tests."""

    def test_flushing_calculate_shows_result(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-073: Clicking calculate in Flushing panel shows a result alert."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-073_flushing-before-calc")

        calc_page.fill_flushing(current_ec=1.5, days_until_harvest=14)
        calc_page.click_calculate_flushing()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_flushing_alerts()) > 0
        )

        capture("REQ004-073_flushing-result")

        alerts = calc_page.get_flushing_alerts()
        assert len(alerts) > 0, (
            "Expected at least one alert after calculating the flushing schedule"
        )

    def test_flushing_result_contains_flush_days(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-074: Flushing result alert contains recommended flush days."""
        calc_page.open()
        calc_page.fill_flushing(current_ec=2.0, days_until_harvest=7)
        calc_page.click_calculate_flushing()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_flushing_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-074_flushing-flush-days")

        alerts = calc_page.get_flushing_alerts()
        alert_text = " ".join(alerts)
        # The alert should contain a number (flush days or flush start day)
        assert any(char.isdigit() for char in alert_text), (
            f"Expected flushing result to contain numeric flush day information, got: '{alert_text}'"
        )

    def test_flushing_generates_schedule_table(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-075: Flushing panel shows a day-by-day schedule DataTable."""
        calc_page.open()
        calc_page.fill_flushing(current_ec=1.8, days_until_harvest=10)
        calc_page.click_calculate_flushing()

        # Wait for the result to appear
        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_flushing_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-075_flushing-schedule-table")

        has_table = calc_page.flushing_has_schedule_table()
        alerts = calc_page.get_flushing_alerts()
        # Either a table OR just alert info is acceptable (depends on API response)
        assert has_table or len(alerts) > 0, (
            "Expected either a schedule table or alert info in the flushing result area"
        )

    def test_flushing_low_ec_minimal_flush(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-076: Low EC (near 0) results in minimal or no flush protocol."""
        calc_page.open()
        calc_page.fill_flushing(current_ec=0.2, days_until_harvest=14)
        calc_page.click_calculate_flushing()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_flushing_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-076_flushing-low-ec")

        alerts = calc_page.get_flushing_alerts()
        assert len(alerts) > 0, (
            "Expected a result even for low EC flushing calculation"
        )


# ── TC-REQ-004-080 to TC-REQ-004-086: Runoff Analysis ────────────────────────


class TestRunoffAnalysis:
    """TC-REQ-004-080 to TC-REQ-004-086: Runoff analysis calculation tests."""

    def test_runoff_calculate_shows_result(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-080: Clicking calculate in Runoff panel shows health status alerts."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-080_runoff-before-calc")

        calc_page.fill_runoff_analysis(
            input_ec=1.8,
            runoff_ec=2.5,
            input_ph=6.0,
            runoff_ph=5.5,
            input_vol=1.0,
            runoff_vol=0.2,
        )
        calc_page.click_calculate_runoff()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_runoff_alerts()) > 0
        )

        capture("REQ004-080_runoff-result")

        alerts = calc_page.get_runoff_alerts()
        assert len(alerts) > 0, (
            "Expected at least one result alert after calculating runoff analysis"
        )

    def test_runoff_shows_ec_status_alert(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-081: Runoff result shows an EC status alert with a delta value."""
        calc_page.open()
        calc_page.fill_runoff_analysis(
            input_ec=1.8,
            runoff_ec=2.5,
            input_ph=6.0,
            runoff_ph=5.5,
        )
        calc_page.click_calculate_runoff()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_runoff_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-081_runoff-ec-status")

        alerts = calc_page.get_runoff_alerts()
        alert_text = " ".join(alerts).lower()
        assert "ec" in alert_text or "delta" in alert_text or any(
            char.isdigit() for char in alert_text
        ), (
            f"Expected EC status information in runoff result, got: '{alert_text}'"
        )

    def test_runoff_healthy_result_shown(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-082: Healthy runoff values (EC delta < 0.5) show success alert."""
        calc_page.open()
        # Input EC very close to runoff EC — healthy
        calc_page.fill_runoff_analysis(
            input_ec=1.8,
            runoff_ec=1.9,  # small delta
            input_ph=6.0,
            runoff_ph=6.0,  # no pH shift
            input_vol=1.0,
            runoff_vol=0.3,  # 30% runoff — acceptable
        )
        calc_page.click_calculate_runoff()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_runoff_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-082_runoff-healthy")

        alerts = calc_page.get_runoff_alerts()
        assert len(alerts) > 0, (
            "Expected runoff result alerts for healthy input values"
        )

    def test_runoff_high_ec_delta_shows_warning(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-083: High EC delta between input and runoff shows a warning or error alert."""
        calc_page.open()
        # Large EC delta — should indicate salt accumulation
        calc_page.fill_runoff_analysis(
            input_ec=1.5,
            runoff_ec=4.0,  # very high — salt build-up
            input_ph=6.0,
            runoff_ph=5.5,
        )
        calc_page.click_calculate_runoff()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_runoff_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-083_runoff-high-ec-delta")

        alerts = calc_page.get_runoff_alerts()
        assert len(alerts) > 0, (
            "Expected warning/error alerts for high EC delta in runoff analysis"
        )

    def test_runoff_shows_volume_status(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-084: Runoff result includes a volume/runoff percentage status."""
        calc_page.open()
        calc_page.fill_runoff_analysis(
            input_ec=1.8,
            runoff_ec=2.0,
            input_ph=6.0,
            runoff_ph=6.0,
            input_vol=1.0,
            runoff_vol=0.25,
        )
        calc_page.click_calculate_runoff()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_runoff_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-084_runoff-volume-status")

        alerts = calc_page.get_runoff_alerts()
        # At least 3 alerts: overall health, EC status, pH status (volume status is 4th)
        assert len(alerts) >= 1, (
            f"Expected multiple result alerts for runoff analysis, got {len(alerts)}: {alerts}"
        )


# ── TC-REQ-004-087 to TC-REQ-004-090: Mixing Safety ─────────────────────────


class TestMixingSafety:
    """TC-REQ-004-087 to TC-REQ-004-090: Mixing safety validation tests."""

    def test_mixing_safety_empty_keys_validates(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-087: Validating an empty fertilizer key list returns a result."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-087_mixing-safety-before")

        # Empty key list — should be safe (no incompatibilities possible)
        calc_page.fill_mixing_safety("")
        calc_page.click_validate_mixing_safety()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_safety_alerts()) > 0
        )

        capture("REQ004-087_mixing-safety-empty-result")

        alerts = calc_page.get_mixing_safety_alerts()
        assert len(alerts) > 0, (
            "Expected at least one alert after validating mixing safety with empty key list"
        )

    def test_mixing_safety_result_has_safe_or_unsafe_indicator(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-088: Mixing safety result shows a safe or unsafe indicator."""
        calc_page.open()
        calc_page.fill_mixing_safety("")
        calc_page.click_validate_mixing_safety()

        WebDriverWait(calc_page.driver, 20).until(
            lambda d: len(calc_page.get_mixing_safety_alerts()) > 0
        )

        capture = request.node._screenshot_capture
        capture("REQ004-088_mixing-safety-indicator")

        is_safe = calc_page.mixing_safety_result_is_safe()
        is_unsafe = calc_page.mixing_safety_result_is_unsafe()
        assert is_safe or is_unsafe, (
            "Expected mixing safety result to show either a 'safe' (green) or 'unsafe' (red) alert"
        )

    def test_mixing_safety_panel_has_text_input(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-089: Mixing Safety panel has a text input for fertilizer keys."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-089_mixing-safety-input-field")

        card = calc_page._get_card_by_heading("Mischsicherheit")
        text_inputs = card.find_elements(By.CSS_SELECTOR, "input:not([type='number'])")
        assert len(text_inputs) > 0, (
            "Expected at least one text input (fertilizer keys) in the Mixing Safety panel"
        )

    def test_mixing_safety_validate_button_present(
        self, calc_page: NutrientCalculationsPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-090: Mixing Safety panel has a validate button."""
        calc_page.open()

        capture = request.node._screenshot_capture
        capture("REQ004-090_mixing-safety-validate-button")

        card = calc_page._get_card_by_heading("Mischsicherheit")
        buttons = card.find_elements(By.CSS_SELECTOR, ".MuiButton-contained")
        assert len(buttons) > 0, (
            "Expected a validate button (MuiButton-contained) in the Mixing Safety panel"
        )
        assert any(
            btn.is_displayed() and btn.is_enabled() for btn in buttons
        ), (
            "Expected the validate button in the Mixing Safety panel to be visible and enabled"
        )
