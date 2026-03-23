"""Page object for the Onboarding Wizard (REQ-020)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class OnboardingWizardPage(BasePage):
    """Interact with the Onboarding Wizard (``/onboarding``).

    Covers all 7 wizard steps:
      1. Experience Level & Smart-Home Toggle
      2. Starter Kit Selection
      3. Favorite Species
      4. Site Setup
      5. Plant Selection (intermediate/expert only)
      6. Nutrient Plans (conditional)
      7. Summary & Completion
    """

    PATH = "/onboarding"

    # ── Page-level locators ────────────────────────────────────────────
    WIZARD = (By.CSS_SELECTOR, "[data-testid='onboarding-wizard']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")

    # ── Navigation buttons ─────────────────────────────────────────────
    NEXT_BUTTON = (By.CSS_SELECTOR, "[data-testid='onboarding-next']")
    BACK_BUTTON = (By.CSS_SELECTOR, "[data-testid='onboarding-back']")
    SKIP_BUTTON = (By.CSS_SELECTOR, "[data-testid='skip-onboarding']")
    COMPLETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='onboarding-complete']")

    # ── Completed / Skipped card ───────────────────────────────────────
    RESTART_BUTTON = (By.CSS_SELECTOR, "[data-testid='onboarding-restart']")
    GO_DASHBOARD_BUTTON = (By.CSS_SELECTOR, "[data-testid='onboarding-go-dashboard']")

    # ── Step 1: Experience Level ───────────────────────────────────────
    STEP_WELCOME = (By.CSS_SELECTOR, "[data-testid='onboarding-step-welcome']")
    EXP_BEGINNER = (By.CSS_SELECTOR, "[data-testid='experience-beginner']")
    EXP_INTERMEDIATE = (By.CSS_SELECTOR, "[data-testid='experience-intermediate']")
    EXP_EXPERT = (By.CSS_SELECTOR, "[data-testid='experience-expert']")
    SMART_HOME_TOGGLE = (By.CSS_SELECTOR, "[data-testid='smart-home-toggle']")

    # ── Step 2: Starter Kit ────────────────────────────────────────────
    STEP_KIT = (By.CSS_SELECTOR, "[data-testid='onboarding-step-kit']")

    # ── Step 3: Favorite Species ───────────────────────────────────────
    STEP_FAVORITES = (By.CSS_SELECTOR, "[data-testid='onboarding-step-favorites']")
    FAVORITES_SEARCH = (By.CSS_SELECTOR, "[data-testid='favorites-search'] input")

    # ── Step 4: Site Setup ─────────────────────────────────────────────
    STEP_SITE = (By.CSS_SELECTOR, "[data-testid='onboarding-step-site']")
    SITE_OPTION_NEW = (By.CSS_SELECTOR, "[data-testid='site-option-new']")
    SITE_NAME_FIELD = (By.CSS_SELECTOR, "[data-testid='site-name-field'] input")
    SITE_TYPE_SELECT = (By.CSS_SELECTOR, "[data-testid='site-type-select']")
    TAP_WATER_EC = (By.CSS_SELECTOR, "[data-testid='onboarding-tap-ec'] input")
    TAP_WATER_PH = (By.CSS_SELECTOR, "[data-testid='onboarding-tap-ph'] input")
    RO_TOGGLE = (By.CSS_SELECTOR, "[data-testid='onboarding-ro-toggle']")

    # ── Step 5: Plant Selection (intermediate/expert) ──────────────────
    STEP_PLANTS = (By.CSS_SELECTOR, "[data-testid='onboarding-step-plant-selection']")

    # ── Step 6: Nutrient Plans (conditional) ───────────────────────────
    STEP_NUTRIENT_PLANS = (By.CSS_SELECTOR, "[data-testid='onboarding-step-nutrient-plans']")

    # ── Step 7: Summary ────────────────────────────────────────────────
    STEP_COMPLETE = (By.CSS_SELECTOR, "[data-testid='onboarding-step-complete']")

    # ── MUI Stepper ────────────────────────────────────────────────────
    STEPPER = (By.CSS_SELECTOR, ".MuiStepper-root")
    STEPPER_STEPS = (By.CSS_SELECTOR, ".MuiStepper-root .MuiStep-root")
    ACTIVE_STEP_LABEL = (By.CSS_SELECTOR, ".MuiStepLabel-root.Mui-active .MuiStepLabel-label")

    # ── Snackbar ───────────────────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, ".MuiSnackbar-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ─────────────────────────────────────────────────────

    def open(self) -> OnboardingWizardPage:
        """Navigate to the onboarding wizard, ensure it starts on Step 1.

        The backend persists ``wizard_step`` between page loads.  When tests
        run sequentially in the same browser session the wizard may resume on
        a later step.  This method handles three cases:

        1. **Completed / Skipped** — the restart button is visible.  Click it
           to reset backend state and return to Step 1.
        2. **Resumed mid-wizard** — the welcome step is *not* visible.  Click
           Back repeatedly until Step 1 (experience level) is shown.
        3. **Fresh start** — the welcome step is already visible.  No action
           needed.
        """
        self.navigate(self.PATH)
        self.wait_for_element(self.WIZARD)
        self.wait_for_loading_complete()
        self._ensure_step_one()
        return self

    def _ensure_step_one(self) -> None:
        """Reset the wizard to Step 1 if it resumed on a later step or shows the completed card."""
        import time

        # Case 1: completed / skipped card — click Restart
        restart_els = self.driver.find_elements(*self.RESTART_BUTTON)
        if restart_els and restart_els[0].is_displayed():
            self.scroll_and_click(restart_els[0])
            # After restart the wizard reloads at step 0; wait for step 1 content
            self.wait_for_element(self.STEP_WELCOME)
            self.wait_for_loading_complete()
            return

        # Case 2: already on step 1
        if self.is_step_welcome_visible():
            return

        # Case 3: resumed on step > 1 — click Back until Step 1 is visible
        # Guard against infinite loops with a maximum of 10 iterations (wizard has at most 7 steps)
        for _ in range(10):
            back_els = self.driver.find_elements(*self.BACK_BUTTON)
            if not back_els or not back_els[0].is_displayed() or not back_els[0].is_enabled():
                break
            self.scroll_and_click(back_els[0])
            # Brief pause to let the React state update render
            time.sleep(0.15)
            if self.is_step_welcome_visible():
                return

        # Final fallback: wait for step welcome (may already be visible after last click)
        self.wait_for_element(self.STEP_WELCOME, timeout=5)

    # ── Wizard-level queries ───────────────────────────────────────────

    def is_wizard_visible(self) -> bool:
        """Return True if the onboarding-wizard container is displayed."""
        elements = self.driver.find_elements(*self.WIZARD)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_stepper_step_count(self) -> int:
        """Return the number of steps shown in the MUI Stepper."""
        steps = self.driver.find_elements(*self.STEPPER_STEPS)
        return len(steps)

    def is_stepper_visible(self) -> bool:
        """Return True if the desktop MUI Stepper is present."""
        return len(self.driver.find_elements(*self.STEPPER)) > 0

    def get_stepper_labels(self) -> list[str]:
        """Return all step labels from the MUI Stepper."""
        steps = self.driver.find_elements(
            By.CSS_SELECTOR, ".MuiStepper-root .MuiStepLabel-label"
        )
        return [s.text for s in steps if s.text]

    # ── Button queries ─────────────────────────────────────────────────

    def is_next_button_visible(self) -> bool:
        """Return True if the Next button is present and displayed."""
        elements = self.driver.find_elements(*self.NEXT_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_next_button_enabled(self) -> bool:
        """Return True if the Next button is enabled."""
        elements = self.driver.find_elements(*self.NEXT_BUTTON)
        return len(elements) > 0 and elements[0].is_enabled()

    def is_back_button_visible(self) -> bool:
        """Return True if the Back button is present and displayed."""
        elements = self.driver.find_elements(*self.BACK_BUTTON)
        if not elements:
            return False
        # On desktop, Back button is only rendered when activeStep > 0
        return elements[0].is_displayed()

    def is_back_button_enabled(self) -> bool:
        """Return True if the Back button is enabled."""
        elements = self.driver.find_elements(*self.BACK_BUTTON)
        return len(elements) > 0 and elements[0].is_enabled()

    def is_skip_button_visible(self) -> bool:
        """Return True if the Skip button is present and displayed."""
        elements = self.driver.find_elements(*self.SKIP_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_complete_button_visible(self) -> bool:
        """Return True if the Complete button is present and displayed."""
        elements = self.driver.find_elements(*self.COMPLETE_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_complete_button_enabled(self) -> bool:
        """Return True if the Complete button is enabled."""
        elements = self.driver.find_elements(*self.COMPLETE_BUTTON)
        return len(elements) > 0 and elements[0].is_enabled()

    def is_restart_button_visible(self) -> bool:
        """Return True if the Restart button is visible (completed/skipped state)."""
        elements = self.driver.find_elements(*self.RESTART_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_go_dashboard_button_visible(self) -> bool:
        """Return True if the Go-to-Dashboard button is visible."""
        elements = self.driver.find_elements(*self.GO_DASHBOARD_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Step visibility queries ────────────────────────────────────────

    def is_step_welcome_visible(self) -> bool:
        """Return True if Step 1 (Experience Level) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_WELCOME)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_kit_visible(self) -> bool:
        """Return True if Step 2 (Starter Kit) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_KIT)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_favorites_visible(self) -> bool:
        """Return True if Step 3 (Favorites) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_FAVORITES)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_site_visible(self) -> bool:
        """Return True if Step 4 (Site Setup) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_SITE)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_plants_visible(self) -> bool:
        """Return True if Step 5 (Plant Selection) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_PLANTS)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_nutrient_plans_visible(self) -> bool:
        """Return True if Step 6 (Nutrient Plans) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_NUTRIENT_PLANS)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_complete_visible(self) -> bool:
        """Return True if Step 7 (Summary) content is displayed."""
        elements = self.driver.find_elements(*self.STEP_COMPLETE)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Button interactions ────────────────────────────────────────────

    def click_next(self) -> None:
        """Click the Next button."""
        btn = self.wait_for_element_clickable(self.NEXT_BUTTON)
        self.scroll_and_click(btn)

    def click_back(self) -> None:
        """Click the Back button."""
        btn = self.wait_for_element_clickable(self.BACK_BUTTON)
        self.scroll_and_click(btn)

    def click_skip(self) -> None:
        """Click the Skip Onboarding button."""
        btn = self.wait_for_element_clickable(self.SKIP_BUTTON)
        self.scroll_and_click(btn)

    def click_complete(self) -> None:
        """Click the Complete/Finish button."""
        btn = self.wait_for_element_clickable(self.COMPLETE_BUTTON)
        self.scroll_and_click(btn)

    def click_restart(self) -> None:
        """Click the Restart button on the completed card."""
        btn = self.wait_for_element_clickable(self.RESTART_BUTTON)
        self.scroll_and_click(btn)

    def click_go_dashboard(self) -> None:
        """Click the Go-to-Dashboard button on the completed card."""
        btn = self.wait_for_element_clickable(self.GO_DASHBOARD_BUTTON)
        self.scroll_and_click(btn)

    # ── Step 1: Experience Level interactions ──────────────────────────

    def select_experience_level(self, level: str) -> None:
        """Click an experience level card. *level* is 'beginner', 'intermediate', or 'expert'."""
        locator = (By.CSS_SELECTOR, f"[data-testid='experience-{level}']")
        card = self.wait_for_element_clickable(locator)
        self.scroll_and_click(card)

    def is_experience_selected(self, level: str) -> bool:
        """Return True if the given experience level card has a primary-coloured border."""
        locator = (By.CSS_SELECTOR, f"[data-testid='experience-{level}']")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return False
        # The parent Card gets borderColor: 'primary.main' when selected.
        # Check that the card's parent has border-width 2 (selected) vs 1 (not).
        card = elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'MuiCard-root')]")
        border = card.value_of_css_property("border-width") or ""
        return "2px" in border

    def get_experience_card_font_weight(self, level: str) -> str:
        """Return the font-weight of the subtitle inside an experience card."""
        locator = (By.CSS_SELECTOR, f"[data-testid='experience-{level}'] .MuiTypography-subtitle1")
        el = self.driver.find_element(*locator)
        return el.value_of_css_property("font-weight")

    def is_smart_home_toggle_visible(self) -> bool:
        """Return True if the Smart Home toggle is present in the DOM."""
        return len(self.driver.find_elements(*self.SMART_HOME_TOGGLE)) > 0

    def is_smart_home_toggle_checked(self) -> bool:
        """Return True if the Smart Home toggle is in the 'on' state."""
        elements = self.driver.find_elements(*self.SMART_HOME_TOGGLE)
        if not elements:
            return False
        # MUI Switch renders a hidden input[type=checkbox] inside
        checkbox = elements[0].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def click_smart_home_toggle(self) -> None:
        """Click the Smart Home toggle switch."""
        el = self.wait_for_element_clickable(self.SMART_HOME_TOGGLE)
        self.scroll_and_click(el)

    # ── Step 2: Starter Kit interactions ───────────────────────────────

    def get_kit_cards(self) -> list[WebElement]:
        """Return all starter kit card action areas."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='kit-']")

    def get_kit_card_count(self) -> int:
        """Return the number of starter kit cards."""
        return len(self.get_kit_cards())

    def click_kit(self, kit_id: str) -> None:
        """Click a starter kit card by its kit_id."""
        locator = (By.CSS_SELECTOR, f"[data-testid='kit-{kit_id}']")
        card = self.wait_for_element_clickable(locator)
        self.scroll_and_click(card)

    def is_kit_selected(self, kit_id: str) -> bool:
        """Return True if the given kit card has a primary-coloured border."""
        locator = (By.CSS_SELECTOR, f"[data-testid='kit-{kit_id}']")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return False
        card = elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'MuiCard-root')]")
        border = card.value_of_css_property("border-width") or ""
        return "2px" in border

    def kit_has_toxicity_warning(self, kit_id: str) -> bool:
        """Return True if the given kit card shows a toxicity warning chip."""
        locator = (By.CSS_SELECTOR, f"[data-testid='kit-{kit_id}']")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return False
        chips = elements[0].find_elements(By.CSS_SELECTOR, ".MuiChip-colorWarning")
        return len(chips) > 0

    def get_kit_difficulty_chip_color(self, kit_id: str) -> str:
        """Return the MUI color class of the difficulty chip for a kit."""
        locator = (By.CSS_SELECTOR, f"[data-testid='kit-{kit_id}'] .MuiChip-root:last-child")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return ""
        class_list = elements[0].get_attribute("class") or ""
        for color in ("success", "warning", "error"):
            if f"MuiChip-color{color.capitalize()}" in class_list:
                return color
        return ""

    # ── Step 3: Favorites interactions ─────────────────────────────────

    def get_favorite_selected_count_text(self) -> str:
        """Return the text showing the number of selected favorites."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='onboarding-step-favorites'] .MuiTypography-body2"
        )
        return el.text

    def get_favorite_tiles(self) -> list[WebElement]:
        """Return all favorite species tile elements."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='favorite-tile-']")

    def click_favorite_tile(self, species_key: str) -> None:
        """Click a favorite species tile by its species key."""
        locator = (By.CSS_SELECTOR, f"[data-testid='favorite-tile-{species_key}']")
        tile = self.wait_for_element_clickable(locator)
        self.scroll_and_click(tile)

    def is_favorite_tile_selected(self, species_key: str) -> bool:
        """Return True if a favorite tile is in the favorited state (warning border)."""
        locator = (By.CSS_SELECTOR, f"[data-testid='favorite-tile-{species_key}']")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return False
        border_color = elements[0].value_of_css_property("border-color")
        # Warning color in MUI is orange-ish; check for aria-pressed too
        aria = elements[0].get_attribute("aria-pressed")
        return aria == "true"

    def favorite_tile_has_kit_badge(self, species_key: str) -> bool:
        """Return True if a favorite tile has the 'Im Kit' badge (primary chip)."""
        locator = (By.CSS_SELECTOR, f"[data-testid='favorite-tile-{species_key}'] .MuiChip-colorPrimary")
        return len(self.driver.find_elements(*locator)) > 0

    def search_favorites(self, term: str) -> None:
        """Type a search term into the favorites search field."""
        search = self.wait_for_element_clickable(self.FAVORITES_SEARCH)
        search.clear()
        search.send_keys(term)

    def get_favorites_no_results_visible(self) -> bool:
        """Return True if the no-results empty state is visible on the favorites step."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='onboarding-step-favorites'] .MuiTypography-body2[class*='text.secondary']"
        )
        # Fallback: look for the centered empty box
        empty_boxes = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='onboarding-step-favorites'] > div[style*='text-align: center']"
        )
        return len(empty_boxes) > 0 or (
            len(self.get_favorite_tiles()) == 0
            and self.is_step_favorites_visible()
        )

    # ── Step 4: Site Setup interactions ────────────────────────────────

    def is_new_site_selected(self) -> bool:
        """Return True if the 'new site' card is selected."""
        elements = self.driver.find_elements(*self.SITE_OPTION_NEW)
        if not elements:
            return False
        card = elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'MuiCard-root')]")
        border = card.value_of_css_property("border-width") or ""
        return "2px" in border

    def click_new_site_option(self) -> None:
        """Click the 'new site' card."""
        btn = self.wait_for_element_clickable(self.SITE_OPTION_NEW)
        self.scroll_and_click(btn)

    def get_site_name_value(self) -> str:
        """Return the current value of the site name field."""
        el = self.driver.find_element(*self.SITE_NAME_FIELD)
        return el.get_attribute("value") or ""

    def set_site_name(self, name: str) -> None:
        """Clear and type a new site name."""
        el = self.wait_for_element_clickable(self.SITE_NAME_FIELD)
        el.clear()
        el.send_keys(name)

    def get_site_type_value(self) -> str:
        """Return the current visible text of the site type selector."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='site-type-select'] .MuiSelect-select"
        )
        return el.text

    def select_site_type(self, label_text: str) -> None:
        """Open the site type dropdown and select by visible text."""
        trigger = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='site-type-select'] .MuiSelect-select")
        )
        self.scroll_and_click(trigger)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{label_text}')]")
        )
        option.click()

    def is_water_section_visible(self) -> bool:
        """Return True if the water section (EC, pH, RO) is in the DOM."""
        return len(self.driver.find_elements(*self.TAP_WATER_EC)) > 0

    def set_tap_water_ec(self, value: str) -> None:
        """Enter a value into the tap water EC field."""
        el = self.wait_for_element_clickable(self.TAP_WATER_EC)
        el.clear()
        el.send_keys(value)

    def get_tap_water_ec_value(self) -> str:
        """Return the current value of the EC field."""
        el = self.driver.find_element(*self.TAP_WATER_EC)
        return el.get_attribute("value") or ""

    def set_tap_water_ph(self, value: str) -> None:
        """Enter a value into the tap water pH field."""
        el = self.wait_for_element_clickable(self.TAP_WATER_PH)
        el.clear()
        el.send_keys(value)

    def get_tap_water_ph_value(self) -> str:
        """Return the current value of the pH field."""
        el = self.driver.find_element(*self.TAP_WATER_PH)
        return el.get_attribute("value") or ""

    def click_ro_toggle(self) -> None:
        """Click the RO system toggle."""
        el = self.wait_for_element_clickable(self.RO_TOGGLE)
        self.scroll_and_click(el)

    def is_ro_toggle_checked(self) -> bool:
        """Return True if the RO toggle is checked."""
        elements = self.driver.find_elements(*self.RO_TOGGLE)
        if not elements:
            return False
        checkbox = elements[0].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def click_existing_site(self, site_key: str) -> None:
        """Click an existing site card."""
        locator = (By.CSS_SELECTOR, f"[data-testid='site-option-{site_key}']")
        card = self.wait_for_element_clickable(locator)
        self.scroll_and_click(card)

    def get_existing_site_cards(self) -> list[WebElement]:
        """Return all existing site card elements."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='site-option-']:not([data-testid='site-option-new'])")

    def is_site_name_field_visible(self) -> bool:
        """Return True if the site name input is visible in the DOM."""
        return len(self.driver.find_elements(*self.SITE_NAME_FIELD)) > 0

    # ── Step 5: Plant Selection interactions ───────────────────────────

    def get_plant_config_rows(self) -> list[WebElement]:
        """Return all plant configuration row elements."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='plant-config-']")

    def click_plant_count_plus(self, species_key: str) -> None:
        """Click the + button for a species in the plant selection step."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-count-plus-{species_key}']")
        btn = self.wait_for_element_clickable(locator)
        self.scroll_and_click(btn)

    def click_plant_count_minus(self, species_key: str) -> None:
        """Click the - button for a species in the plant selection step."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-count-minus-{species_key}']")
        btn = self.wait_for_element_clickable(locator)
        self.scroll_and_click(btn)

    def is_plant_count_plus_enabled(self, species_key: str) -> bool:
        """Return True if the + button is enabled for a species."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-count-plus-{species_key}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_enabled()

    def is_plant_count_minus_enabled(self, species_key: str) -> bool:
        """Return True if the - button is enabled for a species."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-count-minus-{species_key}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_enabled()

    def get_plant_count_value(self, species_key: str) -> str:
        """Return the current count value for a species."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-count-input-{species_key}'] input")
        elements = self.driver.find_elements(*locator)
        if not elements:
            return "0"
        return elements[0].get_attribute("value") or "0"

    def is_plant_phase_select_visible(self, species_key: str) -> bool:
        """Return True if the phase dropdown is visible for a species (only when count > 0)."""
        locator = (By.CSS_SELECTOR, f"[data-testid='plant-phase-select-{species_key}']")
        return len(self.driver.find_elements(*locator)) > 0

    def select_plant_phase(self, species_key: str, phase_label: str) -> None:
        """Select a phase for a species from the dropdown."""
        trigger = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='plant-phase-select-{species_key}'] .MuiSelect-select")
        )
        self.scroll_and_click(trigger)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{phase_label}')]")
        )
        option.click()

    def get_total_plant_count_text(self) -> str:
        """Return the total plant count text shown below the plant configs."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='onboarding-step-plant-selection'] .MuiTypography-h6"
        )
        return el.text

    # ── Step 7: Summary queries ────────────────────────────────────────

    def is_summary_checkmark_visible(self) -> bool:
        """Return True if the success checkmark icon is visible on the summary step."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='onboarding-step-complete'] .MuiSvgIcon-root"
        )
        return len(elements) > 0

    # ── Snackbar queries ───────────────────────────────────────────────

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a snackbar to appear and return its text."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR)
        )
        return el.text

    # ── Compound helpers ───────────────────────────────────────────────

    def advance_to_step_kit(self, experience_level: str | None = None) -> None:
        """Navigate from Step 1 to Step 2 (Starter Kit).

        Clicks an experience level card before advancing so that the wizard
        registers a user interaction on Step 1.  When *experience_level* is
        ``None`` the already-selected default (beginner) is clicked.
        """
        self.wait_for_element(self.STEP_WELCOME)
        self.select_experience_level(experience_level or "beginner")
        self.click_next()
        self.wait_for_element(self.STEP_KIT)

    def advance_to_step_favorites(self) -> None:
        """Navigate from Step 2 to Step 3 (Favorites)."""
        self.wait_for_element(self.STEP_KIT)
        self.click_next()
        self.wait_for_element(self.STEP_FAVORITES)

    def advance_to_step_site(self) -> None:
        """Navigate from Step 3 to Step 4 (Site Setup)."""
        self.wait_for_element(self.STEP_FAVORITES)
        self.click_next()
        self.wait_for_element(self.STEP_SITE)

    def advance_to_step_plants(self) -> None:
        """Navigate from Step 4 to Step 5 (Plant Selection). Only for intermediate/expert."""
        self.wait_for_element(self.STEP_SITE)
        self.click_next()
        self.wait_for_element(self.STEP_PLANTS)

    def advance_to_summary_beginner(self) -> None:
        """Navigate from Step 4 (Site) directly to Summary (beginner path)."""
        self.wait_for_element(self.STEP_SITE)
        self.click_next()
        self.wait_for_element(self.STEP_COMPLETE)

    def navigate_beginner_to_summary(self, kit_id: str | None = None) -> None:
        """Walk through the full beginner wizard flow to the summary step.

        Args:
            kit_id: If provided, select this starter kit on step 2.
        """
        self.open()
        self.wait_for_element(self.STEP_WELCOME)
        # Step 1 → Step 2 (select experience level first)
        self.select_experience_level("beginner")
        self.click_next()
        self.wait_for_element(self.STEP_KIT)
        # Select kit if provided
        if kit_id:
            self.click_kit(kit_id)
        # Step 2 → Step 3 (Favorites)
        self.click_next()
        self.wait_for_element(self.STEP_FAVORITES)
        # Step 3 → Step 4 (Site)
        self.click_next()
        self.wait_for_element(self.STEP_SITE)
        # Step 4 → Summary (beginner skips plants/nutrient plans)
        self.click_next()
        self.wait_for_element(self.STEP_COMPLETE)
