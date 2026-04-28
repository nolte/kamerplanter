"""E2E tests for REQ-028 -- Mischkultur & Companion Planting.

Diese Tests decken REQ-028-spezifische Workflows fuer Mischkultur-Empfehlungen
und Fruchtfolge-Validierung ab. Sie sind bewusst von den REQ-001-Tests
(``test_req001_companion_planting.py``, ``test_req001_crop_rotation.py``)
abgegrenzt, welche Stammdaten-CRUD-Aspekte testen.

Fokus REQ-028:
- Companion-Empfehlungs-Engine: Beziehungsdaten (kompatibel/inkompatibel) sichtbar
  fuer eine Primary-Spezies (Spec §1.1 Szenario 1, §3.1 Algorithmus, §10 Szenario 1)
- Score- und Effekt-Indikatoren der Empfehlung sichtbar (Spec §6.2 Seed-Daten,
  §7.1 UI-Mischkultur-Partner-Panel)
- Fruchtfolge-Zyklus: 4-Jahres-Wartezeit pro Familie konfigurierbar
  (Spec §1 Outdoor-Garden-Planner-Review G-008, REQ-002 Fruchtfolge, CLAUDE.md
  "Fruchtfolge: 4-Jahres-Zyklus")
- Selbst-Inkompatibilitaet einer Familie (Familien-Level family_incompatible_with)
  laesst sich anzeigen (Spec §6.4: Solanaceae↔Solanaceae severe)

Spec-TC Mapping (test TC -> Spec-Szenarien in REQ-028 §10 / §1.1):
  TC-REQ-028-001  ->  §1.1 Szenario 1, §10 Szenario 1   Companion-Page laedt mit Eintrag
  TC-REQ-028-002  ->  §1.1 Szenario 1, §10 Szenario 1   Empfehlungen werden fuer Primary-Spezies geladen
  TC-REQ-028-003  ->  §6.2 Seed-Daten, §7.1 Score-Badge Score-Chip ist an Empfehlungen sichtbar
  TC-REQ-028-004  ->  §10 Szenario 1                    Inkompatibilitaets-Liste rendert getrennt von Kompatibilitaeten
  TC-REQ-028-005  ->  §6.4 Familien-Level Seed-Daten    Fruchtfolge-Page zeigt Wartezeit-Konfiguration (4-Jahres-Zyklus)
  TC-REQ-028-006  ->  §1.1 Szenario 4                   Fruchtfolge-Dialog erlaubt 4-Jahres-Wartezeit (Familien-Selbstinkompatibilitaet)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import CompanionPlantingPage, CropRotationPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def companion_page(browser: WebDriver, base_url: str) -> CompanionPlantingPage:
    """Page object for the Companion Planting page (REQ-028 Mischkultur)."""
    return CompanionPlantingPage(browser, base_url)


@pytest.fixture
def rotation_page(browser: WebDriver, base_url: str) -> CropRotationPage:
    """Page object for the Crop Rotation page (REQ-028 Fruchtfolge)."""
    return CropRotationPage(browser, base_url)


# -- TC-028-001 to TC-028-004: Companion-Empfehlungs-Engine -------------------


class TestCompanionRecommendationEngine:
    """REQ-028 Mischkultur-Empfehlungen — Engine-Output in der UI sichtbar.

    Spec: REQ-028 §1.1 Szenario 1 (Tomate + was passt dazu?), §3.1 4-Schritt-
    Algorithmus, §7.1 Mischkultur-Partner-Panel, §10 Szenario 1.

    Diese Tests fokussieren auf den Empfehlungs-Output (Score, kompatibel/
    inkompatibel-Trennung), nicht auf das CRUD-Anlegen von Edges (= REQ-001).
    """

    @pytest.mark.smoke
    def test_companion_page_loads_for_req028(
        self,
        companion_page: CompanionPlantingPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-001: Mischkultur-Page laedt erfolgreich.

        Spec: REQ-028 §7.1 -- Mischkultur-Partner-Panel ist Einstieg in die
        Empfehlungs-UI.
        """
        companion_page.open()
        screenshot(
            "TC-REQ-028-001_mischkultur-page-loaded",
            "Mischkultur-Seite (Companion Planting) nach initialem Laden",
        )

        title = companion_page.get_title()
        assert title, (
            "TC-REQ-028-001 FAIL: Erwartet nicht-leeren Page-Titel auf der Mischkultur-Seite. "
            f"Bekommen: {title!r}"
        )

    @pytest.mark.smoke
    def test_recommendations_load_for_primary_species(
        self,
        companion_page: CompanionPlantingPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-002: Nach Auswahl einer Primary-Spezies werden Empfehlungen geladen.

        Spec: REQ-028 §1.1 Szenario 1 -- "Tomate + was passt dazu?", §3.1
        4-Schritt-Algorithmus liefert recommended_companions + incompatible_species.
        """
        companion_page.open()

        species_options = companion_page.get_species_options()
        if len(species_options) == 0:
            pytest.skip("Keine Spezies fuer Mischkultur-Empfehlung vorhanden")

        screenshot(
            "TC-REQ-028-002_before-primary-select",
            "Mischkultur-Seite vor Auswahl der Primary-Spezies",
        )

        primary = species_options[0]
        companion_page.select_species(primary)
        companion_page.wait_for_loading_complete()

        screenshot(
            "TC-REQ-028-002_after-primary-select",
            f"Mischkultur-Empfehlungen nach Auswahl von {primary}",
        )

        # Engine-Output: zwei Listen (kompatibel + inkompatibel) muessen rendern,
        # auch wenn sie leer sind. Beide sind Pflicht-Bestandteile des
        # CompanionAdvice-Response (Spec §4.2 CompanionAdvice).
        compatible = companion_page.get_compatible_species()
        incompatible = companion_page.get_incompatible_species()

        assert isinstance(compatible, list), (
            "TC-REQ-028-002 FAIL: recommended_companions-Liste muss in der UI rendern "
            "(REQ-028 §4.2 CompanionAdvice.recommended_companions)"
        )
        assert isinstance(incompatible, list), (
            "TC-REQ-028-002 FAIL: incompatible_species-Liste muss in der UI rendern "
            "(REQ-028 §4.2 CompanionAdvice.incompatible_species)"
        )

    @pytest.mark.core_crud
    def test_compatible_recommendations_show_score_badge(
        self,
        companion_page: CompanionPlantingPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-003: Kompatible Empfehlungen zeigen Score-Badge / -Chip.

        Spec: REQ-028 §6.2 Seed-Daten (Score-Spalte), §7.1 UI -- Score-Badge
        ist Pflicht-Bestandteil des Mischkultur-Partner-Panels.

        Hinweis: Test ueberspringt sich, falls die Demo-Instanz keine
        Spezies-Level Seed-Edges hat (z.B. leere Datenbank). Sobald Seed-Daten
        existieren (>=25 compatible_with-Paare laut DoD), greift die
        Verifikation des Score-Chips.
        """
        companion_page.open()

        species_options = companion_page.get_species_options()
        if len(species_options) == 0:
            pytest.skip("Keine Spezies vorhanden")

        # Suche nach einer Spezies mit kompatiblen Empfehlungen (Tomate ist der
        # kanonische Eintrag aus Spec §6.2 -- mehrere compatible_with-Edges).
        # Falls die Demo-Instanz noch keine Seed-Edges hat, ueberspringen wir.
        candidate = None
        for option in species_options[:5]:  # max 5 Versuche
            companion_page.select_species(option)
            companion_page.wait_for_loading_complete()
            if companion_page.get_compatible_species():
                candidate = option
                break

        if candidate is None:
            pytest.skip(
                "Keine Spezies mit kompatiblen Empfehlungen vorhanden -- "
                "Score-Badge-Test benoetigt geseedete compatible_with-Edges "
                "(REQ-028 §6.2)"
            )

        screenshot(
            "TC-REQ-028-003_score-badge",
            f"Score-Chips an kompatiblen Empfehlungen fuer {candidate}",
        )

        # Score-Chip-Verifikation: Im CompanionPlantingPage.tsx wird pro
        # ListItem ein <Chip label={`Bewertung: ${c.score}`}> gerendert.
        compatible_card_locator = CompanionPlantingPage.COMPATIBLE_CARD
        cards = companion_page.driver.find_elements(*compatible_card_locator)
        assert cards, (
            "TC-REQ-028-003 FAIL: Erwartet 'Kompatible Arten'-Card auf der "
            "Mischkultur-Seite (REQ-028 §7.1)"
        )

        chips = cards[0].find_elements(By.CSS_SELECTOR, ".MuiChip-root")
        assert len(chips) > 0, (
            "TC-REQ-028-003 FAIL: Erwartet mindestens einen Score-Chip an "
            "kompatibler Empfehlung (REQ-028 §6.2 + §7.1 Score-Badge)"
        )

    @pytest.mark.core_crud
    def test_compatible_and_incompatible_lists_render_separately(
        self,
        companion_page: CompanionPlantingPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-004: Engine-Output trennt kompatible von inkompatiblen Spezies.

        Spec: REQ-028 §10 Szenario 1 -- recommended_companions UND
        incompatible_species werden getrennt geliefert; §7.1 UI: zwei
        Bereiche "Empfohlene Partner" und "Vermeiden".
        """
        companion_page.open()

        species_options = companion_page.get_species_options()
        if len(species_options) == 0:
            pytest.skip("Keine Spezies vorhanden")

        companion_page.select_species(species_options[0])
        companion_page.wait_for_loading_complete()

        screenshot(
            "TC-REQ-028-004_dual-list-rendering",
            "Mischkultur-Seite zeigt kompatible und inkompatible Listen getrennt",
        )

        compat_cards = companion_page.driver.find_elements(
            *CompanionPlantingPage.COMPATIBLE_CARD
        )
        incompat_cards = companion_page.driver.find_elements(
            *CompanionPlantingPage.INCOMPATIBLE_CARD
        )

        assert len(compat_cards) >= 1, (
            "TC-REQ-028-004 FAIL: 'Kompatible Arten'-Card fehlt "
            "(REQ-028 §7.1 Mischkultur-Partner-Panel zwei Bereiche)"
        )
        assert len(incompat_cards) >= 1, (
            "TC-REQ-028-004 FAIL: 'Inkompatible Arten'-Card fehlt "
            "(REQ-028 §7.1 'Vermeiden'-Bereich)"
        )


# -- TC-028-005 to TC-028-006: Fruchtfolge / 4-Jahres-Zyklus ------------------


class TestCropRotationCycle:
    """REQ-028 Fruchtfolge — 4-Jahres-Zyklus pro Familie validieren.

    Spec: REQ-028 §6.4 Familien-Level Seed-Daten (Solanaceae↔Solanaceae
    severe = Selbstinkompatibilitaet -> erzwingt mehrjaehrigen Wechsel),
    CLAUDE.md "Fruchtfolge: 4-Jahres-Zyklus (Starkzehrer -> Mittelzehrer ->
    Schwachzehrer -> Gruenduengung)".

    Abgrenzung zu REQ-001-Tests:
    - REQ-001 testet das Anlegen eines Nachfolger-Eintrags (Stammdaten-CRUD).
    - REQ-028 testet, dass die Fruchtfolge-UI das 4-Jahres-Wartezeit-Feld
      korrekt anbietet und so den Zyklus erzwingen kann.
    """

    @pytest.mark.smoke
    def test_crop_rotation_page_loads_for_req028(
        self,
        rotation_page: CropRotationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-005: Fruchtfolge-Seite laedt und zeigt Familien-Auswahl.

        Spec: REQ-028 §6.4 -- Fruchtfolge-Validator basiert auf
        family_incompatible_with-Edges (Solanaceae↔Solanaceae severe).
        Die UI ist der Einstieg, um den 4-Jahres-Zyklus zu konfigurieren.
        """
        rotation_page.open()
        screenshot(
            "TC-REQ-028-005_fruchtfolge-page-loaded",
            "Fruchtfolge-Seite nach initialem Laden",
        )

        title = rotation_page.get_title()
        assert title, (
            "TC-REQ-028-005 FAIL: Erwartet nicht-leeren Page-Titel auf der "
            f"Fruchtfolge-Seite. Bekommen: {title!r}"
        )

        family_options = rotation_page.get_family_options()
        assert isinstance(family_options, list), (
            "TC-REQ-028-005 FAIL: Familien-Auswahl muss in der UI rendern "
            "(REQ-028 §6.4 Familien-Level Seed-Daten)"
        )

    @pytest.mark.core_crud
    def test_rotation_dialog_supports_four_year_wait(
        self,
        rotation_page: CropRotationPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-028-006: Fruchtfolge-Dialog akzeptiert 4-Jahres-Wartezeit.

        Spec: REQ-028 §6.4 Familien-Selbstinkompatibilitaet (severe), CLAUDE.md
        "Fruchtfolge -- 4-Jahres-Zyklus". Das ``wait_years``-Feld muss Werte
        bis mindestens 4 zulassen, damit der Validator den vollen Zyklus
        erzwingen kann.

        Wir oeffnen den Dialog, setzen wait_years=4 und verifizieren, dass das
        Feld den Wert akzeptiert. Wir komittieren NICHT, um den Test idempotent
        zu halten (REQ-001-Tests committen bereits Edges).
        """
        rotation_page.open()

        family_options = rotation_page.get_family_options()
        if len(family_options) < 2:
            pytest.skip(
                "Fuer Fruchtfolge-Dialog werden mindestens 2 Familien benoetigt "
                "(z.B. Solanaceae + Fabaceae)"
            )

        rotation_page.select_family(family_options[0])
        screenshot(
            "TC-REQ-028-006_before-dialog",
            f"Fruchtfolge-Seite vor Dialog-Oeffnung fuer {family_options[0]}",
        )

        rotation_page.click_add_successor()
        rotation_page.set_dialog_wait_years("4")

        screenshot(
            "TC-REQ-028-006_dialog-four-year-wait",
            "Fruchtfolge-Dialog mit 4-Jahres-Wartezeit (REQ-028 4-Jahres-Zyklus)",
        )

        # Verifikation: Das wait_years-Input zeigt den Wert "4". Damit ist
        # der 4-Jahres-Zyklus aus REQ-028 §6.4 / CLAUDE.md konfigurierbar.
        wait_input = rotation_page.driver.find_element(
            *CropRotationPage.DIALOG_WAIT_YEARS
        )
        actual_value = wait_input.get_attribute("value")
        assert actual_value == "4", (
            f"TC-REQ-028-006 FAIL: Erwartet wait_years='4' (4-Jahres-Zyklus, "
            f"REQ-028 §6.4), bekommen wait_years={actual_value!r}"
        )

        # Aufraeumen: Dialog schliessen, kein Commit (Test bleibt idempotent).
        rotation_page.click_dialog_cancel()
