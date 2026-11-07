"""Page objects for the bed's site features and its photo gallery (REQ-053 WP 8.18, 8.22; tested in WP 8.31).

Two component objects on top of the bed view (:class:`~.bed_view_page.BedViewPage`):

* :class:`SiteConditionsDialog` - "Standortmerkmale: <Beet>" (``SiteConditionsDialog`` / ``SiteConditionsFields`` /
  ``ChipChoice``): frost risk, cold-air pocket, stored heat, wind, slope, aspect, access sides;
* :class:`BedPhotosTab` - the "Fotos" tab (``BedPhotosTab``) with the shared upload dialog
  (``PlantPhotoUploadDialog`` / ``ImageCapturePanel``) and the remove confirmation (``ConfirmDialog``).

Every hook is a ``data-testid`` that exists in ``src/frontend/src/features/gardenPlanner/bed/`` or
``src/frontend/src/components/`` - none is guessed. A chip of ``ChipChoice`` is a ``<label>`` whose native radio or
checkbox covers it at opacity 0; the dialog's chips are switched with the keyboard (focus + Space on that input,
the input's own activation key), a coordinate-free and trusted activation. State-changing helpers read their effect
back (the input's checked state, a closed dialog, the gallery count) and fail loudly when it never arrives
(`e2e-test-stability` §D); there is no retry loop and no sleep.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


def press_space_on(page: BasePage, element: WebElement, what: str) -> None:
    """Focus *element* (a native radio/checkbox/switch input) and press Space - its own activation key.

    ``focus()`` is the precondition, verified: a focus that did not land would send the Space to ``<body>``.
    """
    page.scroll_into_view(element)
    page.driver.execute_script("arguments[0].focus();", element)
    if not page.driver.execute_script("return document.activeElement === arguments[0];", element):
        raise AssertionError(f"{what}: the input did not take the keyboard focus")
    ActionChains(page.driver).send_keys(Keys.SPACE).perform()


class SiteConditionsDialog(BasePage):
    """ "Standortmerkmale: <Beet>" of the bed view; the fields carry the prefix ``bed-view-site-conditions``."""

    DIALOG = _tid("bed-site-dialog")
    SUBMIT = _tid("bed-site-submit")
    PREFIX = "bed-view-site-conditions"

    def _input(self, group: str, value: str) -> WebElement:
        return self.wait_for_element(_tid(f"{self.PREFIX}-{group}-{value}-input"))

    def group_info(self, group: str) -> dict[str, object]:
        """One chip group: its role, its title, its hint (``aria-describedby``) and the type of every input."""
        box = self.wait_for_element(_tid(f"{self.PREFIX}-{group}"))
        return self.driver.execute_script(
            "var box = arguments[0];"
            "var title = document.getElementById(box.getAttribute('aria-labelledby'));"
            "var hintId = box.getAttribute('aria-describedby');"
            "var hint = hintId ? document.getElementById(hintId) : null;"
            "return {role: box.getAttribute('role'),"
            " title: title ? title.textContent.trim() : '',"
            " hint: hint ? hint.textContent.trim() : '',"
            " inputs: Array.from(box.querySelectorAll('input')).map(function (i) {"
            "   return [i.value, i.type]; })};",
            box,
        )

    def is_checked(self, group: str, value: str) -> bool:
        return self._input(group, value).is_selected()

    def checked(self, group: str) -> list[str]:
        """The values checked in *group*, read from the inputs themselves."""
        box = self.wait_for_element(_tid(f"{self.PREFIX}-{group}"))
        return [
            i.get_attribute("value") or ""
            for i in box.find_elements(By.CSS_SELECTOR, "input")
            if i.is_selected()
        ]

    def choose(self, group: str, value: str) -> None:
        """Check *value* of a single-choice group (radio) with the keyboard; verified."""
        radio = self._input(group, value)
        if radio.is_selected():
            raise AssertionError(
                f"{group}={value!r} is already chosen; the test expected to change it"
            )
        press_space_on(self, radio, f"choosing {group}={value!r}")
        try:
            self.poll().until(lambda _d: radio.is_selected())
        except TimeoutException as exc:
            raise AssertionError(f"{group}={value!r} is not chosen after Space") from exc

    def toggle(self, group: str, value: str) -> None:
        """Flip one chip of a multiple-choice group (checkbox) with the keyboard; verified."""
        box = self._input(group, value)
        before = box.is_selected()
        press_space_on(self, box, f"toggling {group}={value!r}")
        try:
            self.poll().until(lambda _d: box.is_selected() is not before)
        except TimeoutException as exc:
            raise AssertionError(f"{group}={value!r} stayed {before} after Space") from exc

    def set_cold_air_pocket(self, on: bool) -> None:
        switch = self.wait_for_element(_tid(f"{self.PREFIX}-cold-air"))
        if switch.is_selected() is on:
            raise AssertionError(f"'Kaltluftsee' is already {'on' if on else 'off'}")
        press_space_on(self, switch, "the cold-air switch")
        try:
            self.poll().until(lambda _d: switch.is_selected() is on)
        except TimeoutException as exc:
            raise AssertionError("the 'Kaltluftsee' switch did not flip") from exc

    def degrees(self, field: str) -> str:
        """The text of the slope (``slope``) or aspect (``aspect``) field."""
        return self.wait_for_element(_tid(f"{self.PREFIX}-{field}")).get_attribute("value") or ""

    def enter_degrees(self, field: str, text: str) -> None:
        """Type *text* into a degrees field and commit it with Enter (the field commits on Enter or blur)."""
        element = self.wait_for_element_clickable(_tid(f"{self.PREFIX}-{field}"))
        self.clear_and_fill(element, text)
        if (element.get_attribute("value") or "") != text:
            raise AssertionError(
                f"the {field} field should hold {text!r}, it holds {element.get_attribute('value')!r}"
            )
        element.send_keys(Keys.ENTER)

    def degrees_helper(self, field: str) -> str:
        element = self.wait_for_element(_tid(f"{self.PREFIX}-{field}"))
        return (
            self.driver.execute_script(
                "var root = arguments[0].closest('.MuiFormControl-root');"
                "var help = root ? root.querySelector('.MuiFormHelperText-root') : null;"
                "return help ? help.textContent.replace(/\\s+/g, ' ').trim() : '';",
                element,
            )
            or ""
        )

    def has_free_text_for(self, group: str) -> bool:
        """Whether a chip group holds any text input (it must not: the features are choices)."""
        box = self.wait_for_element(_tid(f"{self.PREFIX}-{group}"))
        return bool(box.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea"))

    def save_and_wait_closed(self, what: str) -> None:
        """ "Speichern"; the dialog closes only after the server accepted the PATCH (``onChanged``)."""
        self.wait_and_click(self.SUBMIT)
        try:
            self.wait_for_element_hidden(self.DIALOG)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the site-conditions dialog did not close after 'Speichern'"
            ) from exc


class BedPhotosTab(BasePage):
    """The "Fotos" tab of one bed and the upload dialog it opens."""

    TAB = _tid("bed-photos")
    ADD = _tid("bed-photos-add")
    COUNT = _tid("bed-photos-count")
    EMPTY = (By.CSS_SELECTOR, "[data-testid='bed-photos'] [data-testid='empty-state']")
    EMPTY_ACTION = (
        By.CSS_SELECTOR,
        "[data-testid='bed-photos'] [data-testid='empty-state-action']",
    )
    PHOTO_CARDS = (By.CSS_SELECTOR, "[data-testid='bed-photos'] li[data-testid^='bed-photo-']")

    UPLOAD_DIALOG = _tid("plant-photo-upload-dialog")
    CAPTURE_PANEL = _tid("image-capture-panel")
    FILE_INPUT = _tid("capture-file-input")
    CAPTURE_ERROR = _tid("capture-error")
    UPLOAD_PREVIEW = _tid("plant-photo-upload-preview")
    UPLOAD_CONFIRM = _tid("plant-photo-upload-confirm")
    UPLOAD_CANCEL = _tid("plant-photo-upload-cancel")

    CONFIRM_DIALOG = _tid("confirm-dialog")
    CONFIRM = (
        By.CSS_SELECTOR,
        "[data-testid='confirm-dialog'] [data-testid='confirm-dialog-confirm']",
    )

    def empty_state_text(self) -> str | None:
        found = self.driver.find_elements(*self.EMPTY)
        return _text(found[0]) if found else None

    def photo_ids(self) -> list[str]:
        """Attachment ids of the gallery's cards, in the order shown (newest first)."""
        self.wait_for_element(self.TAB)
        return [
            (card.get_attribute("data-testid") or "")[len("bed-photo-") :]
            for card in self.driver.find_elements(*self.PHOTO_CARDS)
        ]

    def wait_for_photo_count(self, count: int, what: str) -> list[str]:
        try:
            self.poll(timeout=30).until(lambda _d: len(self.photo_ids()) == count)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the gallery should show {count} photo(s), it shows {self.photo_ids()}"
            ) from exc
        return self.photo_ids()

    def cover_ids(self) -> list[str]:
        """The cards that carry the "Titelfoto" chip."""
        return [pid for pid in self.photo_ids() if self.is_present(_tid(f"bed-photo-cover-{pid}"))]

    def wait_for_cover(self, attachment_id: str, what: str) -> None:
        try:
            self.poll().until(lambda _d: self.cover_ids() == [attachment_id])
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: only {attachment_id!r} should carry 'Titelfoto', the chips sit on {self.cover_ids()}"
            ) from exc

    # ── Upload ─────────────────────────────────────────────────────────

    def open_upload(self) -> None:
        """ "Foto hinzufügen" (or the empty state's "Erstes Foto hinzufügen"); return once the capture panel shows."""
        if self.is_present(self.ADD):
            self.wait_and_click(self.ADD)
        else:
            self.wait_and_click(self.EMPTY_ACTION)
        self.wait_for_element_visible(self.UPLOAD_DIALOG)
        self.wait_for_element_visible(self.CAPTURE_PANEL)

    def choose_file(self, path: str) -> None:
        """Hand a file to the capture panel's hidden file input (the file is sent, not clicked)."""
        file_input = self.find_present(self.FILE_INPUT)
        self.driver.execute_script(
            "arguments[0].removeAttribute('hidden');"
            "arguments[0].style.display = 'block';"
            "arguments[0].style.width = '1px';"
            "arguments[0].style.height = '1px';"
            "arguments[0].style.opacity = '0.01';",
            file_input,
        )
        file_input.send_keys(path)

    def wait_for_capture_error(self, what: str) -> str:
        try:
            return _text(self.wait_for_element_visible(self.CAPTURE_ERROR))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the capture panel shows no error") from exc

    def wait_for_preview(self, what: str) -> None:
        try:
            self.wait_for_element_visible(self.UPLOAD_PREVIEW)
        except TimeoutException as exc:
            error = (
                _text(self.driver.find_element(*self.CAPTURE_ERROR))
                if self.is_present(self.CAPTURE_ERROR)
                else None
            )
            raise AssertionError(
                f"{what}: no upload preview appeared (capture error: {error!r})"
            ) from exc

    def confirm_upload(self, what: str) -> None:
        """ "Hochladen"; the dialog closes only after the upload and the link answered (``onClose`` after ``upload``)."""
        self.wait_and_click(self.UPLOAD_CONFIRM)
        self.wait_for_upload_closed(what)

    def double_tap_confirm(self, what: str) -> None:
        """Two clicks on "Hochladen" in one gesture: the button is locked while the upload runs."""
        button = self.wait_for_element_clickable(self.UPLOAD_CONFIRM)
        self.scroll_into_view(button)
        ActionChains(self.driver).move_to_element(button).click().click().perform()
        self.wait_for_upload_closed(what)

    def wait_for_upload_closed(self, what: str) -> None:
        try:
            self.wait_for_element_hidden(self.UPLOAD_DIALOG, timeout=30)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the upload dialog did not close (upload refused?)"
            ) from exc

    def upload_state(self) -> dict[str, bool]:
        """Whether "Hochladen" is enabled and a preview is shown (read after the capture panel answered)."""
        self.wait_for_element(self.UPLOAD_DIALOG)
        return {
            "confirm_enabled": self.wait_for_element(self.UPLOAD_CONFIRM).is_enabled(),
            "preview": self.is_present(self.UPLOAD_PREVIEW),
        }

    def cancel_upload(self) -> None:
        self.wait_and_click(self.UPLOAD_CANCEL)
        self.wait_for_element_hidden(self.UPLOAD_DIALOG)

    def upload(self, path: str, what: str) -> None:
        self.open_upload()
        self.choose_file(path)
        self.wait_for_preview(what)
        self.confirm_upload(what)

    # ── Cover and remove ───────────────────────────────────────────────

    def toggle_cover(self, attachment_id: str) -> None:
        """The star button of one card; return once its ``aria-pressed`` flipped (the server answered the gallery)."""
        locator = _tid(f"bed-photo-toggle-cover-{attachment_id}")
        before = self.wait_for_element(locator).get_attribute("aria-pressed")
        self.wait_and_click(locator)
        try:
            self.poll().until(
                lambda d: d.find_element(*locator).get_attribute("aria-pressed") != before
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"the cover toggle of {attachment_id!r} stayed aria-pressed={before!r}"
            ) from exc

    def remove(self, attachment_id: str, what: str) -> None:
        """ "Foto entfernen" and confirm; return once the card left the gallery."""
        self.wait_and_click(_tid(f"bed-photo-remove-{attachment_id}"))
        self.wait_for_element_visible(self.CONFIRM_DIALOG)
        self.wait_and_click(self.CONFIRM)
        try:
            self.poll(timeout=30).until(lambda _d: attachment_id not in self.photo_ids())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: photo {attachment_id!r} is still in the gallery"
            ) from exc
