"""Page object for the REQ-034 plant photo gallery.

Encapsulates the "Fotos" tab of a plant instance detail page
(``PlantPhotoGallery``), the upload dialog (``PlantPhotoUploadDialog`` →
``ImageCapturePanel``), the full-size lightbox (``PlantPhotoLightbox``) and the
cover preview (``PlantCoverPreview``).  Every locator is a ``data-testid`` taken
verbatim from the frontend components — no position-based XPath.
"""

from __future__ import annotations

from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from .base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage

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

    #: The two states the gallery's own fetch settles into. `PlantPhotoGallery`
    #: gates its **entire** subtree -- including `GALLERY` itself -- behind its
    #: own ``loading`` flag (``if (loading) return <LoadingSkeleton .../>``,
    #: `PlantPhotoGallery.tsx`), so `GALLERY` never appears mid-fetch the way
    #: `pflege_dashboard_page.PAGE` used to: unlike that container, ours *is*
    #: the settled-content signal, not merely an outer wrapper mounted ahead of
    #: it. Kept as a disjunction with `ERROR_DISPLAY` anyway, mirroring
    #: :meth:`open`'s own wait, so a fetch that fails outright still resolves
    #: the anchor instead of burning the full budget.
    GALLERY_BRANCHES = (GALLERY, ERROR_DISPLAY)

    def wait_for_gallery_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the gallery has rendered its content or an error surface.

        Deliberately does not raise: this is an *anchor* for the readers below,
        not an assertion of its own -- a gallery that legitimately errors is a
        state the caller's own assertion must still be able to observe. Reusing
        :meth:`open`'s own wait would be redundant when the caller just called
        it, but several of the readers below are also skip-gates or read
        before/after a mutation, and #946 (the `has_care_card` defect this
        anchor is modelled on) showed that relying on caller discipline alone
        is exactly how a reader stays vacuous once some future test calls it
        from a context that skipped the anchoring `open()`/`click_photos_tab()`.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                self.GALLERY_BRANCHES, "plant photo gallery content", timeout=timeout
            )

    def is_gallery_loaded(self) -> bool:
        """Return True if the gallery container has rendered.

        Anchored on :meth:`wait_for_gallery_content`, not merely on the
        `GALLERY` locator being probed once: this reader gates a
        ``pytest.skip(...)`` at every one of its seven call sites in
        ``test_req034_plant_gallery.py`` (all immediately after ``open()``,
        which today already waits on the identical branch pair -- but a skip
        decision made on an unanchored read is the same vacuity #946 found in
        `pflege_dashboard_page.has_overdue_section`, and this reader should not
        depend on every future caller repeating that discipline).
        """
        self.wait_for_gallery_content()
        elements = self.driver.find_elements(*self.GALLERY)
        return len(elements) > 0

    def has_photos_tab(self) -> bool:
        """Return True if the 'Fotos' tab is present in the tab bar.

        Deliberately instantaneous, not anchored on the gallery's own content:
        `PHOTOS_TAB` lives in the detail page's `Tabs` bar, which renders
        unconditionally in the same pass as `[data-testid='plant-instance-
        detail-page']` once `PlantInstanceDetailPage`'s *own* top-level
        ``loading`` flag clears -- a different, earlier gate than the gallery's.
        Its one call site (`test_photos_tab_visible_and_opens_gallery`) reads it
        immediately after ``open_info_tab()``, which already waits for that
        container -- the readiness this method reports has already been bought
        by the caller.
        """
        return len(self.driver.find_elements(*self.PHOTOS_TAB)) > 0

    def click_photos_tab(self) -> None:
        self.wait_for_element_clickable(self.PHOTOS_TAB).click()
        self.wait_for_element_visible(self.GALLERY)

    def get_photos_tab_label(self) -> str:
        """Return the 'Fotos' tab's current label text.

        Deliberately instantaneous: its two call sites already wrap it in a
        hand-rolled poll (`test_gallery_tab_label_english`) that re-samples
        until the label settles, because the split i18n bundles (#612) load
        the active namespace asynchronously *after* the locale switch -- a
        single-shot wait here could not distinguish "still the stale DE label"
        from "genuinely never translated", which is exactly what that loop is
        for.
        """
        return self.find_present(self.PHOTOS_TAB).text.strip()

    # ── Gallery state ───────────────────────────────────────────────────

    def get_photo_count(self) -> int:
        """Return the number of thumbnail items currently in the grid.

        Anchored on :meth:`wait_for_gallery_content`: read both before and
        after a mutation and compared (`test_upload_photo_via_file_appears_in_
        grid`, `test_delete_photo_with_confirmation`) and as a skip-gate
        (`test_empty_gallery_shows_empty_state`) -- a zero taken before the
        gallery's own fetch resolved would satisfy "count did not change"
        without having counted anything, the same defect class as #946's
        `count_care_cards_for_plant`.
        """
        self.wait_for_gallery_content()
        return len(self.driver.find_elements(*self.PHOTO_ITEMS))

    def has_empty_state(self) -> bool:
        """Whether the gallery's empty state is displayed (waits; see `BasePage`)."""
        return self.is_visible_within(self.EMPTY_STATE, IMPLICIT_WAIT_EQUIVALENT)

    def has_add_button(self) -> bool:
        """Return True if the header 'add photo' button is visible.

        Anchored on :meth:`wait_for_gallery_content`: combined with
        :meth:`is_gallery_loaded` behind an ``or`` in five skip-gates
        (``if not gallery.is_gallery_loaded() or not gallery.has_add_button():
        pytest.skip(...)``) -- Python's short-circuit evaluation only reaches
        this call once the left operand is `False` (gallery loaded), so this
        read already happened to be safe in practice, but it should not depend
        on staying the *second* operand of that expression.
        """
        self.wait_for_gallery_content()
        els = self.driver.find_elements(*self.ADD_BUTTON)
        return bool(els) and els[0].is_displayed()

    def has_empty_state_action(self) -> bool:
        """Return True if the empty-state's 'add photo' CTA is present.

        Anchored on :meth:`wait_for_gallery_content`: its one call site ORs it
        with :meth:`has_add_button` right after :meth:`has_empty_state`, so an
        unanchored read here could silently drop that assertion's coverage.
        """
        self.wait_for_gallery_content()
        return len(self.driver.find_elements(*self.EMPTY_STATE_ACTION)) > 0

    def has_cover_previews(self) -> bool:
        """Return True if at least one cover-preview widget is rendered.

        Deliberately instantaneous: `PlantCoverPreview` renders its outer
        ``[data-testid='plant-cover-preview']`` box unconditionally on mount
        (`PlantCoverPreview.tsx`) -- unlike the gallery grid, this box is never
        gated behind a loading flag, so it appears in the same render pass as
        the list rows or the info-tab widget that hosts it. See
        :meth:`has_cover_image` for the *inner* placeholder/image race this box
        does have.
        """
        return len(self.driver.find_elements(*self.COVER_PREVIEW)) > 0

    def has_any_write_action(self) -> bool:
        """True if any write affordance (add / set-cover / delete) is present.

        Anchored on :meth:`wait_for_gallery_content` (via :meth:`has_add_button`
        and directly): no current call site exists, but this is public reader
        surface on a HIGH-bucket page (#946) and the two raw reads it used to
        do directly would otherwise reintroduce the same vacuity the other
        gallery readers were just fixed for, the moment a future test starts
        calling it.
        """
        self.wait_for_gallery_content()
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

        Deliberately instantaneous: its one call site
        (`test_capture_dialog_offers_three_modes`) reads it immediately after
        :meth:`open_upload_dialog`, which already waits for `CAPTURE_PANEL` to
        be visible -- the readiness this method needs has already been bought
        by the caller.
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
        """Return True if the drag&drop dropzone is present.

        Deliberately instantaneous -- see :meth:`get_capture_mode_testids_visible`:
        same one call site, same `CAPTURE_PANEL` anchor already bought by
        :meth:`open_upload_dialog`.
        """
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
        """Return True if the capture-panel error message is visible.

        Deliberately instantaneous: unused today (no call site), but paired
        with :meth:`wait_for_capture_error` for any caller that needs to *wait*
        for the error rather than sample it -- that dedicated waiter, not a
        self-anchor here, is the right primitive for the async normalization
        this error follows.
        """
        els = self.driver.find_elements(*self.CAPTURE_ERROR)
        return bool(els) and els[0].is_displayed()

    def get_capture_error_text(self) -> str:
        return self.wait_for_element_visible(self.CAPTURE_ERROR).text

    def wait_for_capture_error(self, timeout: int = 15) -> str:
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.CAPTURE_ERROR))
        return el.text

    def is_upload_dialog_open(self) -> bool:
        """Return True if the upload dialog is present.

        Deliberately instantaneous: unused today (no call site); any future
        caller reaches this state through :meth:`open_upload_dialog`, which
        already waits for `UPLOAD_DIALOG` to be visible.
        """
        return len(self.driver.find_elements(*self.UPLOAD_DIALOG)) > 0

    def has_upload_preview(self) -> bool:
        """Return True if the normalized upload preview is rendered.

        Deliberately instantaneous: its one call site
        (`test_invalid_file_type_rejected`) asserts its *absence* right after
        :meth:`wait_for_capture_error` resolved -- the capture panel's
        normalization attempt has, by construction, already finished by then
        (the error and the preview are mutually exclusive outcomes of the same
        attempt), so this read is anchored transitively.
        """
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
        """Return True if the lightbox is present and visible.

        Deliberately instantaneous: used at both polarities
        (`test_thumbnail_opens_lightbox`), but each call site carries its own
        matching-direction anchor rather than relying on this reader to supply
        one -- the positive read follows :meth:`open_lightbox`, which waits for
        `LIGHTBOX` to become visible; the negative read follows
        :meth:`close_lightbox`, which waits for `LIGHTBOX` to become hidden.
        Anchoring this reader on a *container* the way :meth:`is_gallery_loaded`
        is would not help either direction, since `LIGHTBOX` itself is the only
        settled-content signal there is.
        """
        els = self.driver.find_elements(*self.LIGHTBOX)
        return bool(els) and els[0].is_displayed()

    def is_lightbox_image_visible(self) -> bool:
        """Return True if the full-size lightbox image is visible.

        Deliberately instantaneous: its one call site follows
        :meth:`open_lightbox`, and `LIGHTBOX_IMAGE` renders unconditionally in
        the same JSX subtree as `LIGHTBOX` (`PlantPhotoLightbox.tsx`) -- no
        separate loading flag gates the `<img>` element itself, only the
        browser's own image decode, which `is_displayed()` does not require.
        """
        els = self.driver.find_elements(*self.LIGHTBOX_IMAGE)
        return bool(els) and els[0].is_displayed()

    def close_lightbox(self) -> None:
        self.wait_for_element_clickable(self.LIGHTBOX_CLOSE).click()
        self.wait_for_element_hidden(self.LIGHTBOX)

    # ── Cover photo ─────────────────────────────────────────────────────

    def has_set_cover_buttons(self) -> bool:
        """Return True if at least one 'set cover' action button is present.

        Anchored on :meth:`wait_for_gallery_content`: its one call site is an
        ``if`` branch (not an assert), read right after
        :meth:`wait_for_photo_count` confirmed the grid grew -- already safe in
        practice, but self-anchoring removes the dependency on that ordering
        for any future caller, matching :meth:`has_add_button` above.
        """
        self.wait_for_gallery_content()
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
        """Return True if the 'cover' badge is present on a thumbnail.

        Deliberately instantaneous: its one call site follows
        :meth:`wait_for_cover_badge`, a dedicated waiter for this exact locator
        -- the readiness this method reports has already been bought there.
        """
        return len(self.driver.find_elements(*self.COVER_BADGE)) > 0

    def wait_for_cover_badge(self, timeout: int = 15) -> None:
        self.poll(timeout).until(EC.presence_of_element_located(self.COVER_BADGE))

    def has_cover_image(self) -> bool:
        """Return True if the resolved cover thumbnail is shown.

        Waited, not merely anchored: `PlantCoverPreview` has *no* loading gate
        distinguishing "still resolving" from "no cover" the way the gallery
        grid does -- it renders `COVER_PLACEHOLDER` from the very first paint
        (``fetchedThumb`` starts ``null``, so ``showPlaceholder`` starts
        ``true``) and only swaps to `COVER_IMAGE` once its own
        ``listPlantPhotos`` fetch resolves (`PlantCoverPreview.tsx`). A
        zero-wait read taken right after the widget mounts therefore always
        finds the placeholder branch, even for a plant with a real cover --
        the exact "empty vs not-yet-settled" conflation #946 targets, just
        without a distinguishing DOM state to anchor on. `is_visible_within`
        gives a real cover the `IMPLICIT_WAIT_EQUIVALENT` budget to resolve
        instead of sampling at t=0; it cannot (nothing here can, without a new
        frontend loading-state hook, which is out of this reviewer's mandate)
        fully distinguish "still resolving, will show a cover" from
        "genuinely no cover" within that budget -- see :meth:`has_cover_previews`
        for the box that *is* safe to read unanchored.
        """
        return self.is_visible_within(self.COVER_IMAGE, IMPLICIT_WAIT_EQUIVALENT)

    def has_cover_placeholder(self) -> bool:
        """Return True if the neutral botanical placeholder icon is shown.

        Deliberately instantaneous, unlike :meth:`has_cover_image`: the
        placeholder is `PlantCoverPreview`'s guaranteed first-paint state
        (``showPlaceholder`` starts ``true``), so waiting for it would add
        nothing -- it is already there. This does **not** make the widget's
        settled *cover* state observable; see :meth:`has_cover_image`.
        """
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
        """Return True if the delete-confirmation dialog is present.

        Deliberately instantaneous: its one call site follows
        :meth:`click_delete_for_index`, which already waits for `CONFIRM_DIALOG`
        to be visible -- the readiness this method reports has already been
        bought by the caller.
        """
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
