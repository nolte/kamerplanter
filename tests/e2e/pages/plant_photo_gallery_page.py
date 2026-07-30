"""Page object for the REQ-034 plant photo gallery.

Encapsulates the "Fotos" tab of a plant instance detail page
(``PlantPhotoGallery``), the upload dialog (``PlantPhotoUploadDialog`` →
``ImageCapturePanel``), the full-size lightbox (``PlantPhotoLightbox``) and the
cover preview (``PlantCoverPreview``).  Every locator is a ``data-testid`` taken
verbatim from the frontend components — no position-based XPath.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage

DETAIL_PATH_PREFIX = "/pflanzen/plant-instances"


class PlantPhotoGalleryPage(BasePage):
    """Interact with the plant photo gallery tab and its dialogs."""

    # ── Detail-page anchors (REQ-034 §2.3 tab integration) ──────────────
    DETAIL_PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-detail-page']")
    PHOTOS_TAB = (By.CSS_SELECTOR, "[data-testid='photos-tab']")
    INFO_COVER_PREVIEW = (By.CSS_SELECTOR, "[data-testid='info-cover-preview']")
    INFO_OPEN_GALLERY = (By.CSS_SELECTOR, "[data-testid='info-open-gallery']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Gallery container ───────────────────────────────────────────────
    GALLERY = (By.CSS_SELECTOR, "[data-testid='plant-photo-gallery']")
    ADD_BUTTON = (By.CSS_SELECTOR, "[data-testid='plant-photo-add-button']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    EMPTY_STATE_ACTION = (By.CSS_SELECTOR, "[data-testid='empty-state-action']")
    PHOTO_ITEMS = (By.CSS_SELECTOR, "[data-testid='plant-photo-item']")
    PHOTO_THUMBS = (By.CSS_SELECTOR, "[data-testid='plant-photo-thumb']")
    COVER_BADGE = (By.CSS_SELECTOR, "[data-testid='plant-photo-cover-badge']")
    SET_COVER_BUTTONS = (By.CSS_SELECTOR, "[data-testid='plant-photo-set-cover']")
    DELETE_BUTTONS = (By.CSS_SELECTOR, "[data-testid='plant-photo-delete']")

    # ── Cover preview (info tab / list view) ────────────────────────────
    COVER_PREVIEW = (By.CSS_SELECTOR, "[data-testid='plant-cover-preview']")
    COVER_IMAGE = (By.CSS_SELECTOR, "[data-testid='plant-cover-image']")
    COVER_PLACEHOLDER = (By.CSS_SELECTOR, "[data-testid='plant-cover-placeholder']")

    # ── Upload dialog (REQ-034 §2.2) ────────────────────────────────────
    UPLOAD_DIALOG = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-dialog']")
    UPLOAD_HINT = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-hint']")
    UPLOAD_PREVIEW = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-preview']")
    UPLOAD_CONFIRM = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-confirm']")
    UPLOAD_CANCEL = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-cancel']")
    UPLOAD_CLOSE = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-close']")
    UPLOAD_ERROR = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-error']")
    UPLOAD_RETAKE = (By.CSS_SELECTOR, "[data-testid='plant-photo-upload-retake']")

    # ── Capture panel (shared with REQ-029 recognition) ─────────────────
    CAPTURE_PANEL = (By.CSS_SELECTOR, "[data-testid='image-capture-panel']")
    CAPTURE_DROPZONE = (By.CSS_SELECTOR, "[data-testid='capture-dropzone']")
    CAPTURE_MOBILE_CAMERA = (By.CSS_SELECTOR, "[data-testid='capture-mobile-camera']")
    CAPTURE_WEBCAM_START = (By.CSS_SELECTOR, "[data-testid='capture-webcam-start']")
    CAPTURE_UPLOAD_BUTTON = (By.CSS_SELECTOR, "[data-testid='capture-upload']")
    CAPTURE_FILE_INPUT = (By.CSS_SELECTOR, "[data-testid='capture-file-input']")
    CAPTURE_CAMERA_INPUT = (By.CSS_SELECTOR, "[data-testid='capture-camera-input']")
    CAPTURE_ERROR = (By.CSS_SELECTOR, "[data-testid='capture-error']")

    # ── Lightbox (REQ-034 §2.3 / AC-02) ─────────────────────────────────
    LIGHTBOX = (By.CSS_SELECTOR, "[data-testid='plant-photo-lightbox']")
    LIGHTBOX_IMAGE = (By.CSS_SELECTOR, "[data-testid='plant-photo-lightbox-image']")
    LIGHTBOX_CLOSE = (By.CSS_SELECTOR, "[data-testid='plant-photo-lightbox-close']")

    # ── Shared confirm dialog + snackbar ────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_DELETE = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")
    SNACKBAR_SUCCESS = (
        By.CSS_SELECTOR,
        "#notistack-snackbar, .SnackbarItem-variantSuccess",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self, key: str) -> "PlantPhotoGalleryPage":
        """Deep-link to the gallery tab via the ``#photos`` hash fragment.

        Waits for either the gallery container (success) or the error display
        (e.g. non-existent key) so the call never hangs.
        """
        self.navigate(f"{DETAIL_PATH_PREFIX}/{key}#photos")
        self.poll(20).until(
            lambda d: d.find_elements(*self.GALLERY) or d.find_elements(*self.ERROR_DISPLAY)
        )
        return self

    def open_info_tab(self, key: str) -> "PlantPhotoGalleryPage":
        """Open the plant detail page on its default (info) tab."""
        self.navigate(f"{DETAIL_PATH_PREFIX}/{key}")
        self.poll(20).until(
            lambda d: d.find_elements(*self.DETAIL_PAGE) or d.find_elements(*self.ERROR_DISPLAY)
        )
        return self

    def is_gallery_loaded(self) -> bool:
        return len(self.driver.find_elements(*self.GALLERY)) > 0

    def has_photos_tab(self) -> bool:
        return len(self.driver.find_elements(*self.PHOTOS_TAB)) > 0

    def click_photos_tab(self) -> None:
        self.wait_for_element_clickable(self.PHOTOS_TAB).click()
        self.wait_for_element_visible(self.GALLERY)

    def get_photos_tab_label(self) -> str:
        return self.find_present(self.PHOTOS_TAB).text.strip()

    # ── Gallery state ───────────────────────────────────────────────────

    def get_photo_count(self) -> int:
        return len(self.driver.find_elements(*self.PHOTO_ITEMS))

    def has_empty_state(self) -> bool:
        els = self.driver.find_elements(*self.EMPTY_STATE)
        return bool(els) and els[0].is_displayed()

    def has_add_button(self) -> bool:
        els = self.driver.find_elements(*self.ADD_BUTTON)
        return bool(els) and els[0].is_displayed()

    def has_empty_state_action(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE_ACTION)) > 0

    def has_cover_previews(self) -> bool:
        return len(self.driver.find_elements(*self.COVER_PREVIEW)) > 0

    def has_any_write_action(self) -> bool:
        """True if any write affordance (add / set-cover / delete) is present."""
        return (
            self.has_add_button()
            or bool(self.driver.find_elements(*self.SET_COVER_BUTTONS))
            or bool(self.driver.find_elements(*self.DELETE_BUTTONS))
        )

    def wait_for_photo_count(self, expected: int, timeout: int = 20) -> None:
        """Wait until the thumbnail grid holds exactly *expected* items."""
        self.poll(timeout).until(lambda d: len(d.find_elements(*self.PHOTO_ITEMS)) == expected)

    def wait_for_photo_count_at_least(self, minimum: int, timeout: int = 20) -> None:
        self.poll(timeout).until(lambda d: len(d.find_elements(*self.PHOTO_ITEMS)) >= minimum)

    # ── Upload flow ─────────────────────────────────────────────────────

    def open_upload_dialog(self) -> None:
        """Click 'Add photo' (header button or empty-state CTA) and wait."""
        add_buttons = self.driver.find_elements(*self.ADD_BUTTON)
        if add_buttons and add_buttons[0].is_displayed():
            add_buttons[0].click()
        else:
            self.wait_and_click(self.EMPTY_STATE_ACTION)
        self.wait_for_element_visible(self.UPLOAD_DIALOG)
        self.wait_for_element_visible(self.CAPTURE_PANEL)

    def get_capture_mode_testids_visible(self) -> list[str]:
        """Return which of the three capture affordances are rendered.

        The webcam button only renders when ``getUserMedia`` is supported; the
        mobile-camera and file-upload buttons are always present.
        """
        present = []
        if self.driver.find_elements(*self.CAPTURE_MOBILE_CAMERA):
            present.append("mobile-camera")
        if self.driver.find_elements(*self.CAPTURE_WEBCAM_START):
            present.append("webcam")
        if self.driver.find_elements(*self.CAPTURE_UPLOAD_BUTTON):
            present.append("file-upload")
        return present

    def has_dropzone(self) -> bool:
        return len(self.driver.find_elements(*self.CAPTURE_DROPZONE)) > 0

    def select_file(self, file_path: str) -> None:
        """Send a path to the hidden capture file input.

        MUI renders the ``<input hidden>`` with ``display:none``; we briefly
        make it interactable so Selenium's ``send_keys`` is accepted, mirroring
        the REQ-012 import page helper.
        """
        file_input = self.find_present(self.CAPTURE_FILE_INPUT)
        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].style.visibility = 'visible';"
            "arguments[0].style.height = '1px';"
            "arguments[0].style.width = '1px';"
            "arguments[0].style.opacity = '0.01';"
            "arguments[0].removeAttribute('hidden');",
            file_input,
        )
        file_input.send_keys(file_path)

    def wait_for_upload_preview(self, timeout: int = 20) -> None:
        """Wait until the client-side normalized preview is shown."""
        self.poll(timeout).until(EC.visibility_of_element_located(self.UPLOAD_PREVIEW))

    def confirm_upload(self) -> None:
        btn = self.wait_for_element_clickable(self.UPLOAD_CONFIRM)
        btn.click()
        # Dialog closes on success (component calls onClose after upload).
        self.wait_for_element_hidden(self.UPLOAD_DIALOG, timeout=25)

    def has_capture_error(self) -> bool:
        els = self.driver.find_elements(*self.CAPTURE_ERROR)
        return bool(els) and els[0].is_displayed()

    def get_capture_error_text(self) -> str:
        return self.wait_for_element_visible(self.CAPTURE_ERROR).text

    def wait_for_capture_error(self, timeout: int = 15) -> str:
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.CAPTURE_ERROR))
        return el.text

    def is_upload_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.UPLOAD_DIALOG)) > 0

    def has_upload_preview(self) -> bool:
        return len(self.driver.find_elements(*self.UPLOAD_PREVIEW)) > 0

    def cancel_upload(self) -> None:
        self.wait_and_click(self.UPLOAD_CANCEL)
        self.wait_for_element_hidden(self.UPLOAD_DIALOG)

    # ── Lightbox ────────────────────────────────────────────────────────

    def open_lightbox(self, index: int = 0) -> None:
        thumbs = self.driver.find_elements(*self.PHOTO_THUMBS)
        self.scroll_and_click(thumbs[index])
        self.wait_for_element_visible(self.LIGHTBOX)

    def is_lightbox_open(self) -> bool:
        els = self.driver.find_elements(*self.LIGHTBOX)
        return bool(els) and els[0].is_displayed()

    def is_lightbox_image_visible(self) -> bool:
        els = self.driver.find_elements(*self.LIGHTBOX_IMAGE)
        return bool(els) and els[0].is_displayed()

    def close_lightbox(self) -> None:
        self.wait_for_element_clickable(self.LIGHTBOX_CLOSE).click()
        self.wait_for_element_hidden(self.LIGHTBOX)

    # ── Cover photo ─────────────────────────────────────────────────────

    def has_set_cover_buttons(self) -> bool:
        return len(self.driver.find_elements(*self.SET_COVER_BUTTONS)) > 0

    def set_cover_for_index(self, index: int = 0) -> None:
        """Click the 'set cover' icon on the photo at *index*.

        Coordinate-free: the action bar packs 40px IconButtons 2px apart over a
        card whose thumb opens the lightbox, and every one of them
        ``stopPropagation``s (`PlantPhotoGallery.tsx:339-352`). A coordinate
        dispatch that misses therefore activates a *neighbouring* action or the
        card, and raises nothing either way. A disabled button (``isBusy``) now
        fails loudly instead of swallowing the click.
        """
        buttons = self.driver.find_elements(*self.SET_COVER_BUTTONS)
        self.click_coordinate_free(buttons[index])

    def has_cover_badge(self) -> bool:
        return len(self.driver.find_elements(*self.COVER_BADGE)) > 0

    def wait_for_cover_badge(self, timeout: int = 15) -> None:
        self.poll(timeout).until(EC.presence_of_element_located(self.COVER_BADGE))

    def has_cover_image(self) -> bool:
        return len(self.driver.find_elements(*self.COVER_IMAGE)) > 0

    def has_cover_placeholder(self) -> bool:
        return len(self.driver.find_elements(*self.COVER_PLACEHOLDER)) > 0

    def wait_for_cover_image(self, timeout: int = 15) -> None:
        self.poll(timeout).until(EC.presence_of_element_located(self.COVER_IMAGE))

    # ── Delete flow ─────────────────────────────────────────────────────

    def click_delete_for_index(self, index: int = 0) -> None:
        """Click the delete icon on the photo at *index* (coordinate-free).

        Same reasoning as :meth:`set_cover_for_index` -- and here a coordinate
        miss onto a neighbouring action would be actively harmful, since the bar
        also holds 'set cover' and 'assess quality'.
        """
        buttons = self.driver.find_elements(*self.DELETE_BUTTONS)
        self.click_coordinate_free(buttons[index])
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def is_confirm_dialog_open(self) -> bool:
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def confirm_delete(self) -> None:
        self.wait_and_click(self.CONFIRM_DELETE)
        self.wait_for_element_hidden(self.CONFIRM_DIALOG, timeout=20)

    def cancel_delete(self) -> None:
        self.wait_and_click(self.CONFIRM_CANCEL)
        self.wait_for_element_hidden(self.CONFIRM_DIALOG)

    # ── Snackbar ────────────────────────────────────────────────────────

    def wait_for_success_snackbar(self, timeout: int = 15) -> str:
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR_SUCCESS))
        return el.text
