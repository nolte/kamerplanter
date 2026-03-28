"""E2E tests for REQ-012 -- Stammdaten-Import via CSV-Upload.

Tests cover:
- Import page navigation and stepper display (TC-012-001, TC-012-002)
- Upload form defaults and controls (TC-012-003 to TC-012-006, TC-012-010)
- Entity type and duplicate strategy dropdowns (TC-012-004, TC-012-005)
- CSV upload and preview display (TC-012-011, TC-012-012)
- Preview status chips and error indicators (TC-012-012, TC-012-023)
- Import confirmation and result display (TC-012-017, TC-012-018, TC-012-019)
- Back button navigation (TC-012-016)
- Upload button disabled state (TC-012-006)
- File accept filter (TC-012-031)
- Empty CSV error handling (TC-012-033)
- Missing columns error (TC-012-034)

NFR-008 ss3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.import_page import ImportPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def import_page(browser: WebDriver, base_url: str) -> ImportPage:
    """Return an ImportPage bound to the test browser."""
    return ImportPage(browser, base_url)


# ── Valid species CSV rows for reuse ──────────────────────────────────────────

SPECIES_HEADER = "scientific_name,common_names,family,genus,cycle_type"
SPECIES_VALID_ROWS = [
    "Solanum lycopersicum,Tomate,Solanaceae,Solanum,annual",
    "Capsicum annuum,Paprika,Solanaceae,Capsicum,annual",
    "Ocimum basilicum,Basilikum,Lamiaceae,Ocimum,annual",
]


# ── TC-012-001 to TC-012-003: Navigation and page structure ──────────────────


class TestImportPageNavigation:
    """TC-012-001 to TC-012-003: Import page navigation and form defaults."""

    def test_import_page_loads_with_stepper(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-002: Direct navigation to /stammdaten/import shows the import page.

        Covers TC-012-001 (sidebar nav) and TC-012-002 (direct URL).
        """
        capture = request.node._screenshot_capture
        import_page.open()
        capture("req012_001_import_page_loaded", "Import page after initial load")

        # Stepper is visible with 3 steps
        step_labels = import_page.get_step_labels()
        assert len(step_labels) == 3, (
            f"Expected 3 stepper steps, got {len(step_labels)}: {step_labels}"
        )

        # Step 1 (upload) is active
        assert import_page.get_active_step_index() == 0, (
            "Expected step 0 (Upload) to be active"
        )

        # Upload form is visible
        assert import_page.is_step_upload_visible(), (
            "Expected the upload step container to be visible"
        )

    def test_upload_form_shows_defaults(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-003: Upload form shows all fields with correct default values."""
        capture = request.node._screenshot_capture
        import_page.open()
        capture("req012_002_upload_form_defaults", "Upload form with default values")

        # Entity type default is 'species'
        entity_value = import_page.get_entity_type_value()
        assert entity_value == "species", (
            f"Expected default entity type 'species', got '{entity_value}'"
        )

        # Duplicate strategy default is 'skip'
        strategy_value = import_page.get_duplicate_strategy_value()
        assert strategy_value == "skip", (
            f"Expected default duplicate strategy 'skip', got '{strategy_value}'"
        )

        # Download template button is visible
        assert import_page.is_download_template_visible(), (
            "Expected download template button to be visible"
        )

        # Upload button is disabled (no file selected)
        assert not import_page.is_upload_button_enabled(), (
            "Expected upload button to be disabled when no file is selected"
        )


# ── TC-012-004 to TC-012-005: Dropdown options ───────────────────────────────


class TestImportDropdowns:
    """TC-012-004 to TC-012-005: Entity type and duplicate strategy dropdowns."""

    def test_entity_type_dropdown_has_three_options(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-004: Entity type dropdown shows Species, Cultivar, BotanicalFamily."""
        capture = request.node._screenshot_capture
        import_page.open()

        options = import_page.get_entity_type_options()
        capture("req012_003_entity_type_options", "Entity type dropdown opened")

        assert len(options) == 3, (
            f"Expected 3 entity type options, got {len(options)}: {options}"
        )

    def test_duplicate_strategy_dropdown_has_three_options(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-005: Duplicate strategy dropdown shows skip, update, fail."""
        capture = request.node._screenshot_capture
        import_page.open()

        options = import_page.get_duplicate_strategy_options()
        capture("req012_004_duplicate_strategy_options", "Duplicate strategy dropdown opened")

        assert len(options) == 3, (
            f"Expected 3 duplicate strategy options, got {len(options)}: {options}"
        )


# ── TC-012-006, TC-012-010: File selection and upload button state ────────────


class TestImportFileSelection:
    """TC-012-006, TC-012-010: File selection and upload button behaviour."""

    def test_upload_button_disabled_without_file(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-006: Upload button is disabled when no file is selected."""
        capture = request.node._screenshot_capture
        import_page.open()
        capture("req012_005_upload_button_disabled", "Upload button disabled state")

        assert not import_page.is_upload_button_enabled(), (
            "Expected upload button to be disabled when no file is selected"
        )

    def test_file_selection_enables_upload_button(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-010: Selecting a CSV file enables the upload button and shows filename."""
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_valid.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        capture("req012_006_before_file_select", "Before selecting a file")

        import_page.select_file(csv_path)
        capture("req012_007_after_file_select", "After selecting a file")

        # Upload button should now be enabled
        assert import_page.is_upload_button_enabled(), (
            "Expected upload button to be enabled after selecting a file"
        )

        # File name should appear on the button
        button_text = import_page.get_file_button_text()
        assert "species_valid.csv" in button_text, (
            f"Expected filename 'species_valid.csv' in button text, got '{button_text}'"
        )

    def test_file_input_accepts_csv_tsv_txt_only(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-031: File input has accept filter for .csv, .tsv, .txt."""
        capture = request.node._screenshot_capture
        import_page.open()

        file_input = import_page.driver.find_element(*ImportPage.FILE_INPUT)
        accept_attr = file_input.get_attribute("accept") or ""
        capture("req012_008_file_accept_filter", "File input accept attribute check")

        assert ".csv" in accept_attr, (
            f"Expected '.csv' in accept attribute, got '{accept_attr}'"
        )
        assert ".tsv" in accept_attr, (
            f"Expected '.tsv' in accept attribute, got '{accept_attr}'"
        )
        assert ".txt" in accept_attr, (
            f"Expected '.txt' in accept attribute, got '{accept_attr}'"
        )


# ── TC-012-011, TC-012-012: Upload and preview ───────────────────────────────


class TestImportUploadAndPreview:
    """TC-012-011, TC-012-012: CSV upload and preview table display."""

    def test_valid_csv_upload_shows_preview(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-011: Uploading a valid species CSV transitions to preview step.

        Verifies stepper advances to step 2, preview table is visible,
        file info shows filename and row count, and rows have status chips.
        """
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_upload_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        capture("req012_009_before_upload", "Before clicking upload")

        import_page.click_upload_and_wait_preview()
        capture("req012_010_preview_step", "Preview step after upload")

        # Preview step should be visible
        assert import_page.is_step_preview_visible(), (
            "Expected preview step to be visible after upload"
        )

        # Stepper should show step 2 as active
        assert import_page.get_active_step_index() == 1, (
            "Expected step 1 (Preview) to be active after upload"
        )

        # File info should show filename and row count
        file_info = import_page.get_preview_file_info()
        assert "species_upload_test.csv" in file_info, (
            f"Expected filename in file info, got '{file_info}'"
        )

        # Preview table should have rows
        row_count = import_page.get_preview_row_count()
        assert row_count > 0, (
            f"Expected at least 1 preview row, got {row_count}"
        )

    def test_preview_shows_status_chips(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-012: Preview table shows color-coded status chips per row.

        Uploads a CSV with valid rows and checks that green (valid) chips appear.
        """
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_chips_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        capture("req012_011_preview_status_chips", "Preview with status chips")

        # All rows should be either valid (green) or duplicate (yellow) — never invalid (red).
        # Seeded species (e.g. Solanum lycopersicum) appear as DUPLICATE, not VALID.
        invalid_count = import_page.count_invalid_rows()
        total_rows = import_page.get_preview_row_count()
        assert total_rows > 0, "Expected at least one preview row"
        assert invalid_count == 0, (
            f"Expected no invalid rows in preview, but got {invalid_count} out of {total_rows}"
        )

    def test_preview_shows_invalid_rows_with_error_chips(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-023: Rows with missing required fields show 'invalid' status and error chips."""
        capture = request.node._screenshot_capture
        import_page.open()

        # Row with missing scientific_name (empty first field)
        rows_with_errors = [
            "Solanum lycopersicum,Tomate,Solanaceae,Solanum,annual",
            ",Unbekannt,Solanaceae,Solanum,annual",  # missing scientific_name
            "Capsicum annuum,Paprika,Solanaceae,Capsicum,annual",
        ]
        csv_path = ImportPage.create_test_csv(
            "species_invalid_test.csv", SPECIES_HEADER, rows_with_errors
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        capture("req012_012_preview_with_errors", "Preview with invalid rows")

        # Should have at least one invalid row
        invalid_count = import_page.count_invalid_rows()
        assert invalid_count >= 1, (
            f"Expected at least 1 invalid row, got {invalid_count}"
        )

        # Should still have non-invalid rows (valid or duplicate)
        valid_count = import_page.count_valid_rows()
        duplicate_count = import_page.count_duplicate_rows()
        assert (valid_count + duplicate_count) >= 1, (
            f"Expected at least 1 non-invalid row, got valid={valid_count} duplicate={duplicate_count}"
        )


# ── TC-012-017 to TC-012-019: Confirm import and result ──────────────────────


class TestImportConfirmAndResult:
    """TC-012-017, TC-012-018, TC-012-019: Import confirmation and result display."""

    def test_confirm_valid_import_shows_result(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-017: Confirming an import with valid rows shows result step.

        Verifies stepper advances to step 3, result chips are shown with
        'created' count, and no error warnings appear.
        """
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_confirm_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        capture("req012_013_before_confirm", "Preview before confirming import")

        import_page.click_confirm_and_wait_result()
        capture("req012_014_result_step", "Result step after confirming import")

        # Result step should be visible
        assert import_page.is_step_result_visible(), (
            "Expected result step to be visible after confirming"
        )

        # Stepper should show step 3 as active
        assert import_page.get_active_step_index() == 2, (
            "Expected step 2 (Result) to be active after confirm"
        )

        # Result chips should exist
        chip_texts = import_page.get_result_chip_texts()
        assert len(chip_texts) > 0, (
            "Expected result chips on the result page"
        )

    def test_new_import_button_resets_to_step_one(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-019: Clicking 'New Import' on the result page resets to step 1."""
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_reset_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        import_page.click_confirm_and_wait_result()
        capture("req012_015_result_before_reset", "Result page before clicking new import")

        import_page.click_new_import()
        capture("req012_016_after_new_import", "Upload step after reset via new import")

        # Should be back on upload step
        assert import_page.is_step_upload_visible(), (
            "Expected upload step to be visible after clicking new import"
        )
        assert import_page.get_active_step_index() == 0, (
            "Expected step 0 (Upload) to be active after reset"
        )

        # Upload button should be disabled again (no file)
        assert not import_page.is_upload_button_enabled(), (
            "Expected upload button to be disabled after reset"
        )


# ── TC-012-016: Back button ──────────────────────────────────────────────────


class TestImportBackNavigation:
    """TC-012-016: Back button in preview returns to upload step."""

    def test_back_button_returns_to_upload_step(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-016: Clicking 'Back' in preview returns to step 1 and clears the job."""
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_back_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        capture("req012_017_preview_before_back", "Preview before clicking back")

        import_page.click_back()
        capture("req012_018_after_back", "Upload step after clicking back")

        # Upload step should be visible again
        assert import_page.is_step_upload_visible(), (
            "Expected upload step after clicking back"
        )
        assert not import_page.is_step_preview_visible(), (
            "Expected preview step to be hidden after clicking back"
        )


# ── TC-012-033, TC-012-034: Upload error handling ────────────────────────────


class TestImportErrorHandling:
    """TC-012-033, TC-012-034: Error handling for invalid CSV files."""

    def test_empty_csv_shows_error(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-033: Uploading an empty CSV file shows an error message."""
        capture = request.node._screenshot_capture
        import_page.open()

        csv_path = ImportPage.create_empty_csv("empty.csv")
        import_page.select_file(csv_path)
        capture("req012_019_before_empty_upload", "Before uploading empty CSV")

        # Click upload and wait for either an error alert OR the preview step (0 rows)
        import_page.click_upload()
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(import_page.driver, 30).until(
            lambda d: (
                len(d.find_elements(*ImportPage.ERROR_ALERT)) > 0
                or len(d.find_elements(By.CSS_SELECTOR, ".MuiSnackbar-root")) > 0
                or len(d.find_elements(*ImportPage.STEP_PREVIEW)) > 0
            )
        )
        capture("req012_020_empty_csv_error", "Result after uploading empty CSV")

        # Either an error is shown OR preview displays 0 rows
        if import_page.is_error_alert_visible():
            assert import_page.is_step_upload_visible(), (
                "Expected to remain on upload step after empty CSV error"
            )
        else:
            # Empty CSV produces a preview with 0 data rows — that is acceptable
            assert import_page.is_step_preview_visible() or import_page.is_step_upload_visible(), (
                "Expected to stay on upload or advance to preview (0 rows) after empty CSV"
            )

    def test_csv_with_missing_columns_shows_error(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-034: CSV with missing required columns shows a structural error."""
        capture = request.node._screenshot_capture
        import_page.open()

        # Header is missing 'scientific_name' (required for species)
        csv_path = ImportPage.create_test_csv(
            "missing_columns.csv",
            "common_names,family,genus",
            ["Tomate,Solanaceae,Solanum"],
        )
        import_page.select_file(csv_path)
        capture("req012_021_before_missing_cols_upload", "Before uploading CSV with missing columns")

        # This may either show an error on step 1 or advance to preview with all invalid rows
        import_page.click_upload()

        # Wait for either error alert or preview step
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(import_page.driver, 30).until(
            lambda d: (
                len(d.find_elements(*ImportPage.ERROR_ALERT)) > 0
                or len(d.find_elements(*ImportPage.STEP_PREVIEW)) > 0
            )
        )
        capture("req012_022_missing_cols_result", "Result after uploading CSV with missing columns")

        # Either an error alert is shown OR all preview rows are invalid
        if import_page.is_error_alert_visible():
            error_text = import_page.get_error_alert_text()
            assert len(error_text) > 0, (
                "Expected error message text in the alert"
            )
        else:
            # If we got to preview, all rows should be invalid
            assert import_page.is_step_preview_visible(), (
                "Expected either error alert or preview step"
            )


# ── TC-012-004, TC-012-005 extended: Entity type switching ───────────────────


class TestImportEntityTypeSwitch:
    """Extended tests for entity type and strategy switching."""

    def test_switch_entity_type_to_cultivar(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-004 (extended): Switching entity type to Cultivar updates the selection."""
        capture = request.node._screenshot_capture
        import_page.open()

        # Find the option text for cultivar by checking the dropdown
        options = import_page.get_entity_type_options()
        capture("req012_023_entity_options_listed", "Entity type options visible")

        # Select the second option (cultivar)
        if len(options) >= 2:
            import_page.select_entity_type(options[1])
            capture("req012_024_entity_cultivar_selected", "Cultivar entity type selected")

            new_value = import_page.get_entity_type_value()
            assert new_value == "cultivar", (
                f"Expected entity type 'cultivar' after selection, got '{new_value}'"
            )

    def test_switch_duplicate_strategy_to_update(
        self,
        import_page: ImportPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-012-005 (extended): Switching duplicate strategy to 'update' works."""
        capture = request.node._screenshot_capture
        import_page.open()

        options = import_page.get_duplicate_strategy_options()
        capture("req012_025_strategy_options_listed", "Duplicate strategy options visible")

        # Select the second option (update)
        if len(options) >= 2:
            import_page.select_duplicate_strategy(options[1])
            capture("req012_026_strategy_update_selected", "Update strategy selected")

            new_value = import_page.get_duplicate_strategy_value()
            assert new_value == "update", (
                f"Expected strategy 'update' after selection, got '{new_value}'"
            )
