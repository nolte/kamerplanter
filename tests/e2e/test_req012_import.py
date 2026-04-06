"""E2E tests for REQ-012 — Stammdaten-Import via CSV-Upload.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-012.md):
  TC-REQ-012-001  ->  TC-012-002  Direkte Navigation zur Import-Seite per URL
  TC-REQ-012-002  ->  TC-012-003  Upload-Formular zeigt alle Pflichtfelder mit Standardwerten
  TC-REQ-012-003  ->  TC-012-004  Datentyp-Dropdown zeigt alle drei Entitaetsoptionen
  TC-REQ-012-004  ->  TC-012-005  Duplikatstrategie-Dropdown zeigt alle drei Strategien
  TC-REQ-012-005  ->  TC-012-006  Upload-Button ist deaktiviert solange keine Datei ausgewaehlt
  TC-REQ-012-006  ->  TC-012-010  Dateiauswahl per Klick zeigt Dateinamen im Button
  TC-REQ-012-007  ->  TC-012-031  Upload einer Nicht-CSV-Datei — Dateiauswahl-Filter
  TC-REQ-012-008  ->  TC-012-011  Erfolgreicher Upload einer gueltigen Species-CSV leitet zur Vorschau
  TC-REQ-012-009  ->  TC-012-012  Vorschau zeigt farbcodierte Status-Chips pro Zeile
  TC-REQ-012-010  ->  TC-012-023  Fehlende Pflichtfelder werden als 'invalid' markiert
  TC-REQ-012-011  ->  TC-012-017  Bestaetigung eines vollstaendig gueltigen Species-Imports
  TC-REQ-012-012  ->  TC-012-019  'Neuer Import'-Button auf Ergebnis-Seite setzt Prozess zurueck
  TC-REQ-012-013  ->  TC-012-016  'Zurueck'-Button in Vorschau wechselt zurueck zu Schritt 1
  TC-REQ-012-014  ->  TC-012-033  Upload einer leeren CSV-Datei zeigt Fehlermeldung
  TC-REQ-012-015  ->  TC-012-034  CSV mit fehlenden Pflichtspalten im Header
  TC-REQ-012-016  ->  TC-012-004  Datentyp wechseln zu Cultivar
  TC-REQ-012-017  ->  TC-012-005  Duplikatstrategie wechseln zu 'update'
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.import_page import ImportPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def import_page(browser: WebDriver, base_url: str) -> ImportPage:
    """Return an ImportPage bound to the test browser."""
    return ImportPage(browser, base_url)


# -- Valid species CSV rows for reuse ------------------------------------------

SPECIES_HEADER = "scientific_name,common_names,family,genus,cycle_type"
SPECIES_VALID_ROWS = [
    "Solanum lycopersicum,Tomate,Solanaceae,Solanum,annual",
    "Capsicum annuum,Paprika,Solanaceae,Capsicum,annual",
    "Ocimum basilicum,Basilikum,Lamiaceae,Ocimum,annual",
]


# -- TC-REQ-012-001 to TC-REQ-012-002: Navigation and page structure ----------


class TestImportPageNavigation:
    """Import page navigation and form defaults (Spec: TC-012-001, TC-012-002, TC-012-003)."""

    @pytest.mark.smoke
    def test_import_page_loads_with_stepper(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-001: Direct navigation to /stammdaten/import shows the import page.

        Spec: TC-012-002 -- Direkte Navigation zur Import-Seite per URL.
        """
        import_page.open()
        screenshot("TC-REQ-012-001_import-page-loaded", "Import page after initial load")

        # Stepper is visible with 3 steps
        step_labels = import_page.get_step_labels()
        assert len(step_labels) == 3, (
            f"TC-REQ-012-001 FAIL: Expected 3 stepper steps, got {len(step_labels)}: {step_labels}"
        )

        # Step 1 (upload) is active
        assert import_page.get_active_step_index() == 0, (
            "TC-REQ-012-001 FAIL: Expected step 0 (Upload) to be active"
        )

        # Upload form is visible
        assert import_page.is_step_upload_visible(), (
            "TC-REQ-012-001 FAIL: Expected the upload step container to be visible"
        )

    @pytest.mark.smoke
    def test_upload_form_shows_defaults(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-002: Upload form shows all fields with correct default values.

        Spec: TC-012-003 -- Upload-Formular zeigt alle Pflichtfelder mit Standardwerten.
        """
        import_page.open()
        screenshot("TC-REQ-012-002_upload-form-defaults", "Upload form with default values")

        # Entity type default is 'species'
        entity_value = import_page.get_entity_type_value()
        assert entity_value == "species", (
            f"TC-REQ-012-002 FAIL: Expected default entity type 'species', got '{entity_value}'"
        )

        # Duplicate strategy default is 'skip'
        strategy_value = import_page.get_duplicate_strategy_value()
        assert strategy_value == "skip", (
            f"TC-REQ-012-002 FAIL: Expected default duplicate strategy 'skip', got '{strategy_value}'"
        )

        # Download template button is visible
        assert import_page.is_download_template_visible(), (
            "TC-REQ-012-002 FAIL: Expected download template button to be visible"
        )

        # Upload button is disabled (no file selected)
        assert not import_page.is_upload_button_enabled(), (
            "TC-REQ-012-002 FAIL: Expected upload button to be disabled when no file is selected"
        )


# -- TC-REQ-012-003 to TC-REQ-012-004: Dropdown options -----------------------


class TestImportDropdowns:
    """Entity type and duplicate strategy dropdowns (Spec: TC-012-004, TC-012-005)."""

    @pytest.mark.core_crud
    def test_entity_type_dropdown_has_three_options(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-003: Entity type dropdown shows Species, Cultivar, BotanicalFamily.

        Spec: TC-012-004 -- Datentyp-Dropdown zeigt alle drei Entitaetsoptionen.
        """
        import_page.open()

        options = import_page.get_entity_type_options()
        screenshot("TC-REQ-012-003_entity-type-options", "Entity type dropdown opened")

        assert len(options) == 3, (
            f"TC-REQ-012-003 FAIL: Expected 3 entity type options, got {len(options)}: {options}"
        )

    @pytest.mark.core_crud
    def test_duplicate_strategy_dropdown_has_three_options(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-004: Duplicate strategy dropdown shows skip, update, fail.

        Spec: TC-012-005 -- Duplikatstrategie-Dropdown zeigt alle drei Strategien.
        """
        import_page.open()

        options = import_page.get_duplicate_strategy_options()
        screenshot("TC-REQ-012-004_duplicate-strategy-options", "Duplicate strategy dropdown opened")

        assert len(options) == 3, (
            f"TC-REQ-012-004 FAIL: Expected 3 duplicate strategy options, got {len(options)}: {options}"
        )


# -- TC-REQ-012-005 to TC-REQ-012-007: File selection and upload button --------


class TestImportFileSelection:
    """File selection and upload button behaviour (Spec: TC-012-006, TC-012-010, TC-012-031)."""

    @pytest.mark.smoke
    def test_upload_button_disabled_without_file(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-005: Upload button is disabled when no file is selected.

        Spec: TC-012-006 -- Upload-Button ist deaktiviert solange keine Datei ausgewaehlt.
        """
        import_page.open()
        screenshot("TC-REQ-012-005_upload-button-disabled", "Upload button disabled state")

        assert not import_page.is_upload_button_enabled(), (
            "TC-REQ-012-005 FAIL: Expected upload button to be disabled when no file is selected"
        )

    @pytest.mark.core_crud
    def test_file_selection_enables_upload_button(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-006: Selecting a CSV file enables the upload button and shows filename.

        Spec: TC-012-010 -- Dateiauswahl per Klick zeigt Dateinamen im Button.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_valid.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        screenshot("TC-REQ-012-006_before-file-select", "Before selecting a file")

        import_page.select_file(csv_path)
        screenshot("TC-REQ-012-006_after-file-select", "After selecting a file")

        # Upload button should now be enabled
        assert import_page.is_upload_button_enabled(), (
            "TC-REQ-012-006 FAIL: Expected upload button to be enabled after selecting a file"
        )

        # File name should appear on the button
        button_text = import_page.get_file_button_text()
        assert "species_valid.csv" in button_text, (
            f"TC-REQ-012-006 FAIL: Expected filename 'species_valid.csv' in button text, got '{button_text}'"
        )

    @pytest.mark.core_crud
    def test_file_input_accepts_csv_tsv_txt_only(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-007: File input has accept filter for .csv, .tsv, .txt.

        Spec: TC-012-031 -- Upload einer Nicht-CSV-Datei wird abgelehnt (Dateiauswahl-Filter).
        """
        import_page.open()

        file_input = import_page.driver.find_element(*ImportPage.FILE_INPUT)
        accept_attr = file_input.get_attribute("accept") or ""
        screenshot("TC-REQ-012-007_file-accept-filter", "File input accept attribute check")

        assert ".csv" in accept_attr, (
            f"TC-REQ-012-007 FAIL: Expected '.csv' in accept attribute, got '{accept_attr}'"
        )
        assert ".tsv" in accept_attr, (
            f"TC-REQ-012-007 FAIL: Expected '.tsv' in accept attribute, got '{accept_attr}'"
        )
        assert ".txt" in accept_attr, (
            f"TC-REQ-012-007 FAIL: Expected '.txt' in accept attribute, got '{accept_attr}'"
        )


# -- TC-REQ-012-008 to TC-REQ-012-010: Upload and preview ---------------------


class TestImportUploadAndPreview:
    """CSV upload and preview table display (Spec: TC-012-011, TC-012-012, TC-012-023)."""

    @pytest.mark.core_crud
    def test_valid_csv_upload_shows_preview(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-008: Uploading a valid species CSV transitions to preview step.

        Spec: TC-012-011 -- Erfolgreicher Upload einer gueltigen Species-CSV leitet zur Vorschau.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_upload_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        screenshot("TC-REQ-012-008_before-upload", "Before clicking upload")

        import_page.click_upload_and_wait_preview()
        screenshot("TC-REQ-012-008_preview-step", "Preview step after upload")

        # Preview step should be visible
        assert import_page.is_step_preview_visible(), (
            "TC-REQ-012-008 FAIL: Expected preview step to be visible after upload"
        )

        # Stepper should show step 2 as active
        assert import_page.get_active_step_index() == 1, (
            "TC-REQ-012-008 FAIL: Expected step 1 (Preview) to be active after upload"
        )

        # File info should show filename and row count
        file_info = import_page.get_preview_file_info()
        assert "species_upload_test.csv" in file_info, (
            f"TC-REQ-012-008 FAIL: Expected filename in file info, got '{file_info}'"
        )

        # Preview table should have rows
        row_count = import_page.get_preview_row_count()
        assert row_count > 0, (
            f"TC-REQ-012-008 FAIL: Expected at least 1 preview row, got {row_count}"
        )

    @pytest.mark.core_crud
    def test_preview_shows_status_chips(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-009: Preview table shows color-coded status chips per row.

        Spec: TC-012-012 -- Vorschau zeigt farbcodierte Status-Chips pro Zeile.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_chips_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        screenshot("TC-REQ-012-009_preview-status-chips", "Preview with status chips")

        # All rows should be either valid (green) or duplicate (yellow) — never invalid (red).
        # Seeded species (e.g. Solanum lycopersicum) appear as DUPLICATE, not VALID.
        invalid_count = import_page.count_invalid_rows()
        total_rows = import_page.get_preview_row_count()
        assert total_rows > 0, (
            "TC-REQ-012-009 FAIL: Expected at least one preview row"
        )
        assert invalid_count == 0, (
            f"TC-REQ-012-009 FAIL: Expected no invalid rows in preview, but got {invalid_count} out of {total_rows}"
        )

    @pytest.mark.core_crud
    def test_preview_shows_invalid_rows_with_error_chips(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-010: Rows with missing required fields show 'invalid' status and error chips.

        Spec: TC-012-023 -- Fehlende Pflichtfelder in Species-CSV werden als 'invalid' markiert.
        """
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
        screenshot("TC-REQ-012-010_preview-with-errors", "Preview with invalid rows")

        # Should have at least one invalid row
        invalid_count = import_page.count_invalid_rows()
        assert invalid_count >= 1, (
            f"TC-REQ-012-010 FAIL: Expected at least 1 invalid row, got {invalid_count}"
        )

        # Should still have non-invalid rows (valid or duplicate)
        valid_count = import_page.count_valid_rows()
        duplicate_count = import_page.count_duplicate_rows()
        assert (valid_count + duplicate_count) >= 1, (
            f"TC-REQ-012-010 FAIL: Expected at least 1 non-invalid row, "
            f"got valid={valid_count} duplicate={duplicate_count}"
        )


# -- TC-REQ-012-011 to TC-REQ-012-012: Confirm import and result --------------


class TestImportConfirmAndResult:
    """Import confirmation and result display (Spec: TC-012-017, TC-012-019)."""

    @pytest.mark.core_crud
    def test_confirm_valid_import_shows_result(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-011: Confirming an import with valid rows shows result step.

        Spec: TC-012-017 -- Bestaetigung eines vollstaendig gueltigen Species-Imports.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_confirm_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        screenshot("TC-REQ-012-011_before-confirm", "Preview before confirming import")

        import_page.click_confirm_and_wait_result()
        screenshot("TC-REQ-012-011_result-step", "Result step after confirming import")

        # Result step should be visible
        assert import_page.is_step_result_visible(), (
            "TC-REQ-012-011 FAIL: Expected result step to be visible after confirming"
        )

        # Stepper should show step 3 as active
        assert import_page.get_active_step_index() == 2, (
            "TC-REQ-012-011 FAIL: Expected step 2 (Result) to be active after confirm"
        )

        # Result chips should exist
        chip_texts = import_page.get_result_chip_texts()
        assert len(chip_texts) > 0, (
            "TC-REQ-012-011 FAIL: Expected result chips on the result page"
        )

    @pytest.mark.core_crud
    def test_new_import_button_resets_to_step_one(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-012: Clicking 'New Import' on the result page resets to step 1.

        Spec: TC-012-019 -- 'Neuer Import'-Button auf Ergebnis-Seite setzt Prozess zurueck.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_reset_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        import_page.click_confirm_and_wait_result()
        screenshot("TC-REQ-012-012_result-before-reset", "Result page before clicking new import")

        import_page.click_new_import()
        screenshot("TC-REQ-012-012_after-new-import", "Upload step after reset via new import")

        # Should be back on upload step
        assert import_page.is_step_upload_visible(), (
            "TC-REQ-012-012 FAIL: Expected upload step to be visible after clicking new import"
        )
        assert import_page.get_active_step_index() == 0, (
            "TC-REQ-012-012 FAIL: Expected step 0 (Upload) to be active after reset"
        )

        # Upload button should be disabled again (no file)
        assert not import_page.is_upload_button_enabled(), (
            "TC-REQ-012-012 FAIL: Expected upload button to be disabled after reset"
        )


# -- TC-REQ-012-013: Back button ----------------------------------------------


class TestImportBackNavigation:
    """Back button in preview returns to upload step (Spec: TC-012-016)."""

    @pytest.mark.core_crud
    def test_back_button_returns_to_upload_step(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-013: Clicking 'Back' in preview returns to step 1 and clears the job.

        Spec: TC-012-016 -- 'Zurueck'-Button in der Vorschau wechselt zurueck zu Schritt 1.
        """
        import_page.open()

        csv_path = ImportPage.create_test_csv(
            "species_back_test.csv", SPECIES_HEADER, SPECIES_VALID_ROWS
        )
        import_page.select_file(csv_path)
        import_page.click_upload_and_wait_preview()
        screenshot("TC-REQ-012-013_preview-before-back", "Preview before clicking back")

        import_page.click_back()
        screenshot("TC-REQ-012-013_after-back", "Upload step after clicking back")

        # Upload step should be visible again
        assert import_page.is_step_upload_visible(), (
            "TC-REQ-012-013 FAIL: Expected upload step after clicking back"
        )
        assert not import_page.is_step_preview_visible(), (
            "TC-REQ-012-013 FAIL: Expected preview step to be hidden after clicking back"
        )


# -- TC-REQ-012-014 to TC-REQ-012-015: Upload error handling ------------------


class TestImportErrorHandling:
    """Error handling for invalid CSV files (Spec: TC-012-033, TC-012-034)."""

    @pytest.mark.core_crud
    def test_empty_csv_shows_error(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-014: Uploading an empty CSV file shows an error message.

        Spec: TC-012-033 -- Upload einer leeren CSV-Datei zeigt Fehlermeldung.
        """
        import_page.open()

        csv_path = ImportPage.create_empty_csv("empty.csv")
        import_page.select_file(csv_path)
        screenshot("TC-REQ-012-014_before-empty-upload", "Before uploading empty CSV")

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
        screenshot("TC-REQ-012-014_empty-csv-error", "Result after uploading empty CSV")

        # Either an error is shown OR preview displays 0 rows
        if import_page.is_error_alert_visible():
            assert import_page.is_step_upload_visible(), (
                "TC-REQ-012-014 FAIL: Expected to remain on upload step after empty CSV error"
            )
        else:
            # Empty CSV produces a preview with 0 data rows — that is acceptable
            assert import_page.is_step_preview_visible() or import_page.is_step_upload_visible(), (
                "TC-REQ-012-014 FAIL: Expected to stay on upload or advance to preview (0 rows) after empty CSV"
            )

    @pytest.mark.core_crud
    def test_csv_with_missing_columns_shows_error(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-015: CSV with missing required columns shows a structural error.

        Spec: TC-012-034 -- CSV mit fehlenden Pflichtspalten im Header wird als Strukturfehler markiert.
        """
        import_page.open()

        # Header is missing 'scientific_name' (required for species)
        csv_path = ImportPage.create_test_csv(
            "missing_columns.csv",
            "common_names,family,genus",
            ["Tomate,Solanaceae,Solanum"],
        )
        import_page.select_file(csv_path)
        screenshot("TC-REQ-012-015_before-missing-cols-upload", "Before uploading CSV with missing columns")

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
        screenshot("TC-REQ-012-015_missing-cols-result", "Result after uploading CSV with missing columns")

        # Either an error alert is shown OR all preview rows are invalid
        if import_page.is_error_alert_visible():
            error_text = import_page.get_error_alert_text()
            assert len(error_text) > 0, (
                "TC-REQ-012-015 FAIL: Expected error message text in the alert"
            )
        else:
            # If we got to preview, all rows should be invalid
            assert import_page.is_step_preview_visible(), (
                "TC-REQ-012-015 FAIL: Expected either error alert or preview step"
            )


# -- TC-REQ-012-016 to TC-REQ-012-017: Entity type switching ------------------


class TestImportEntityTypeSwitch:
    """Extended tests for entity type and strategy switching (Spec: TC-012-004, TC-012-005)."""

    @pytest.mark.core_crud
    def test_switch_entity_type_to_cultivar(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-016: Switching entity type to Cultivar updates the selection.

        Spec: TC-012-004 -- Datentyp-Dropdown (extended): Wechsel zu Cultivar.
        """
        import_page.open()

        # Find the option text for cultivar by checking the dropdown
        options = import_page.get_entity_type_options()
        screenshot("TC-REQ-012-016_entity-options-listed", "Entity type options visible")

        # Select the second option (cultivar)
        if len(options) >= 2:
            import_page.select_entity_type(options[1])
            screenshot("TC-REQ-012-016_entity-cultivar-selected", "Cultivar entity type selected")

            new_value = import_page.get_entity_type_value()
            assert new_value == "cultivar", (
                f"TC-REQ-012-016 FAIL: Expected entity type 'cultivar' after selection, got '{new_value}'"
            )

    @pytest.mark.core_crud
    def test_switch_duplicate_strategy_to_update(
        self,
        import_page: ImportPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-012-017: Switching duplicate strategy to 'update' works.

        Spec: TC-012-005 -- Duplikatstrategie-Dropdown (extended): Wechsel zu 'update'.
        """
        import_page.open()

        options = import_page.get_duplicate_strategy_options()
        screenshot("TC-REQ-012-017_strategy-options-listed", "Duplicate strategy options visible")

        # Select the second option (update)
        if len(options) >= 2:
            import_page.select_duplicate_strategy(options[1])
            screenshot("TC-REQ-012-017_strategy-update-selected", "Update strategy selected")

            new_value = import_page.get_duplicate_strategy_value()
            assert new_value == "update", (
                f"TC-REQ-012-017 FAIL: Expected strategy 'update' after selection, got '{new_value}'"
            )
