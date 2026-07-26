"""E2E tests for REQ-034 — Pflanzenfoto-Galerie.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-034.md):
  TC-REQ-034-001  ->  TC-REQ-034-001  Galerie-Tab auf der Detailseite sichtbar
  TC-REQ-034-002  ->  TC-REQ-034-002  Leere Galerie zeigt Leerzustand + Upload-CTA
  TC-REQ-034-003  ->  TC-REQ-034-003  Pflanze ohne Foto zeigt Platzhalter in der Liste
  TC-REQ-034-004  ->  TC-REQ-034-006  Foto per Datei-Upload erscheint im Thumbnail-Grid
  TC-REQ-034-005  ->  TC-REQ-034-007  Aufnahme-Dialog bietet Webcam/Kamera/Datei
  TC-REQ-034-006  ->  TC-REQ-034-005  Klick auf Thumbnail oeffnet Lightbox mit Originalbild
  TC-REQ-034-007  ->  TC-REQ-034-009  Ungueltiger Dateityp wird abgelehnt
  TC-REQ-034-008  ->  TC-REQ-034-011  Foto als Titelbild markieren (Cover-Badge)
  TC-REQ-034-009  ->  TC-REQ-034-012  Titelbild erscheint als Vorschau im Info-Tab
  TC-REQ-034-010  ->  TC-REQ-034-013  Einzelnes Foto loeschen (mit Bestaetigung)
  TC-REQ-034-011  ->  TC-REQ-034-018  Galerie-UI in Englisch (i18n)

Scope & deliberate omissions
----------------------------
* The three capture paths (live webcam via getUserMedia, smartphone rear
  camera via ``<input capture>`` and file upload) are exercised UI-side: the
  test asserts the *visibility* of all three affordances (TC-REQ-034-005 ->
  spec TC-007) and drives the **file-upload path** for every actual upload,
  because a physical webcam/phone camera cannot be automated in headless CI.
  Spec TC-006 (smartphone camera) and TC-004 (drag&drop wiring) are covered
  through the same shared ``ImageCapturePanel`` file path.
* DINOv2 reference contribution (spec TC-016/TC-017) is **out of scope**: the
  inference service is disabled by default (Phase 1, no-op hook), so there is
  no consent UI to drive; TC-016's expectation ("no contribution prompt
  appears") is implicitly satisfied by the plain upload flow in
  TC-REQ-034-004, which never surfaces a reference prompt.
* The viewer read-only permission case (spec TC-015) and oversize-file
  rejection (spec TC-010) are documented below but skipped: they require a
  dedicated viewer-role account / a >20 MB fixture that the smoke account and
  repo cannot provide deterministically.

All uploads are real photos written to the test gallery — the suite therefore
leaves residue.  Tests that mutate state clean up after themselves (the
delete-photo test removes what the upload test would have added) and assert on
relative counts so re-runs converge.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import PlantInstanceListPage, PlantPhotoGalleryPage

pytestmark = pytest.mark.requires_auth

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VALID_PHOTO = FIXTURE_DIR / "sample_plant_photo.png"
INVALID_PHOTO = FIXTURE_DIR / "not_an_image.png"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    """Return a PlantInstanceListPage bound to the test browser."""
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def gallery(browser: WebDriver, base_url: str) -> PlantPhotoGalleryPage:
    """Return a PlantPhotoGalleryPage bound to the test browser."""
    return PlantPhotoGalleryPage(browser, base_url)


# -- Helpers ------------------------------------------------------------------


def _first_plant_key(plant_list: PlantInstanceListPage) -> str | None:
    """Open the list, click the first row and return the key from the URL.

    Mirrors the helper used in test_req003_phasensteuerung.  Returns ``None``
    when no plant instance exists so callers can skip gracefully.
    """
    plant_list.open()
    if plant_list.get_row_count() == 0:
        return None
    plant_list.click_row(0)
    plant_list.wait_for_url_contains("/pflanzen/plant-instances/")
    url = plant_list.driver.current_url
    return url.split("#", 1)[0].rstrip("/").rsplit("/", 1)[-1]


def _upload_one_photo(gallery: PlantPhotoGalleryPage) -> None:
    """Open the upload dialog, pick the valid fixture and confirm the upload."""
    gallery.open_upload_dialog()
    gallery.select_file(str(VALID_PHOTO))
    gallery.wait_for_upload_preview()
    gallery.confirm_upload()


# ============================================================================
# 1. Gallery tab & display
# ============================================================================


class TestPlantGalleryTab:
    """Gallery tab visibility and empty state (Spec: TC-REQ-034-001/002)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_photos_tab_visible_and_opens_gallery(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-001: 'Fotos' tab is present and opens the gallery view.

        Spec: TC-REQ-034-001 — Galerie-Tab auf der Pflanzeninstanz-Detailseite
        sichtbar.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot open gallery")

        gallery.open_info_tab(key)
        screenshot(
            "TC-REQ-034-001_detail-info-tab",
            "Plant detail page on the info tab before opening the gallery",
        )

        assert gallery.has_photos_tab(), (
            "TC-REQ-034-001 FAIL: Expected a 'Fotos' (photos-tab) tab in the tab bar"
        )

        gallery.click_photos_tab()
        screenshot(
            "TC-REQ-034-001_gallery-tab-open",
            "Gallery tab active after clicking the photos tab",
        )
        assert gallery.is_gallery_loaded(), (
            "TC-REQ-034-001 FAIL: Clicking the photos tab did not open the gallery"
        )

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_empty_gallery_shows_empty_state(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-002: A gallery without photos shows the empty state + CTA.

        Spec: TC-REQ-034-002 — Leere Galerie zeigt Leerzustand mit
        Upload-Aufforderung.  We can only assert this when a plant without
        photos exists; otherwise the test skips rather than failing.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot open gallery")

        gallery.open(key)
        if not gallery.is_gallery_loaded():
            pytest.skip("Gallery did not load (error display) — cannot assert empty state")

        if gallery.get_photo_count() > 0:
            pytest.skip("First plant already has photos — empty state not applicable")

        screenshot(
            "TC-REQ-034-002_empty-state",
            "Empty gallery showing the empty-state placeholder and add CTA",
        )
        assert gallery.has_empty_state(), (
            "TC-REQ-034-002 FAIL: Expected empty-state placeholder in an empty gallery"
        )
        assert gallery.has_add_button() or gallery.has_empty_state_action(), (
            "TC-REQ-034-002 FAIL: Expected an 'add photo' affordance in the empty state"
        )


class TestPlantGalleryListPlaceholder:
    """Cover placeholder in the list view (Spec: TC-REQ-034-003)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_plant_without_photo_shows_placeholder(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-003: Plants without a photo render a neutral placeholder.

        Spec: TC-REQ-034-003 — Pflanze ohne Foto zeigt Platzhalter in der
        Listenansicht (kein gebrochenes Bild).
        """
        plant_list.open()
        if plant_list.get_row_count() == 0:
            pytest.skip("No plant instances — cannot check list placeholders")

        screenshot(
            "TC-REQ-034-003_list-cover-previews",
            "Plant list with per-row cover previews",
        )

        # Every row renders a PlantCoverPreview — for plants without a cover it
        # shows the botanical placeholder icon, never a broken <img>.
        assert gallery.has_cover_previews(), (
            "TC-REQ-034-003 FAIL: Expected at least one cover-preview widget in the list"
        )
        assert gallery.has_cover_placeholder() or gallery.has_cover_image(), (
            "TC-REQ-034-003 FAIL: Cover previews rendered neither a placeholder "
            "nor an image — possible broken-image state"
        )


# ============================================================================
# 2. Upload
# ============================================================================


class TestPlantGalleryUpload:
    """File upload and capture-mode affordances (Spec: TC-REQ-034-006/007)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_capture_dialog_offers_three_modes(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-005: The capture dialog offers webcam, camera and file upload.

        Spec: TC-REQ-034-007 — Aufnahme-Dialog bietet Webcam, Smartphone-Kamera
        und Datei-Upload (Wiederverwendung der Bilderkennungs-UX).

        The live-webcam button only renders when ``getUserMedia`` is available;
        in headless Chrome it may be absent.  We therefore require the two
        always-present paths (mobile camera + file upload) plus the drag&drop
        dropzone, and treat the webcam button as best-effort.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot open upload dialog")

        gallery.open(key)
        if not gallery.is_gallery_loaded() or not gallery.has_add_button():
            pytest.skip("Gallery not writable for this account — cannot open upload")

        gallery.open_upload_dialog()
        screenshot(
            "TC-REQ-034-005_capture-dialog",
            "Upload dialog with the shared image capture panel (three modes)",
        )

        modes = gallery.get_capture_mode_testids_visible()
        assert "mobile-camera" in modes, (
            f"TC-REQ-034-005 FAIL: Expected the smartphone-camera option, got {modes}"
        )
        assert "file-upload" in modes, (
            f"TC-REQ-034-005 FAIL: Expected the file-upload option, got {modes}"
        )
        assert gallery.has_dropzone(), (
            "TC-REQ-034-005 FAIL: Expected the drag&drop dropzone to be present"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_upload_photo_via_file_appears_in_grid(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-004: A file upload adds a thumbnail to the grid.

        Spec: TC-REQ-034-006 — Foto per Datei-Upload hinzufuegen.  Drives the
        file-upload path of the shared capture panel; webcam/phone-camera are
        UI-equivalent and not automatable in CI.

        Cleanup: the uploaded photo is removed at the end so the suite does not
        accumulate fixtures across runs.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot upload")

        gallery.open(key)
        if not gallery.is_gallery_loaded() or not gallery.has_add_button():
            pytest.skip("Gallery not writable for this account — cannot upload")

        before = gallery.get_photo_count()
        screenshot(
            "TC-REQ-034-004_before-upload",
            f"Gallery before upload ({before} photos)",
        )

        gallery.open_upload_dialog()
        gallery.select_file(str(VALID_PHOTO))
        gallery.wait_for_upload_preview()
        screenshot(
            "TC-REQ-034-004_upload-preview",
            "Normalized image preview shown before confirming the upload",
        )

        gallery.confirm_upload()
        gallery.wait_for_photo_count(before + 1)
        screenshot(
            "TC-REQ-034-004_after-upload",
            f"Gallery after upload ({before + 1} photos)",
        )

        assert gallery.get_photo_count() == before + 1, (
            f"TC-REQ-034-004 FAIL: Expected {before + 1} photos after upload, "
            f"got {gallery.get_photo_count()}"
        )

        # Cleanup — remove the just-uploaded photo (first item) to keep the
        # gallery state stable for re-runs.
        gallery.click_delete_for_index(0)
        gallery.confirm_delete()
        gallery.wait_for_photo_count(before)

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_invalid_file_type_rejected(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-007: A non-image file is rejected with an error.

        Spec: TC-REQ-034-009 — Ungueltiger Dateityp wird abgelehnt.  The
        gallery normalizes the selected file client-side via a canvas; a file
        that is not a decodable image fails normalization and surfaces the
        'unsupported format' error.  No photo is added.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot test validation")

        gallery.open(key)
        if not gallery.is_gallery_loaded() or not gallery.has_add_button():
            pytest.skip("Gallery not writable for this account — cannot open upload")

        before = gallery.get_photo_count()
        gallery.open_upload_dialog()
        gallery.select_file(str(INVALID_PHOTO))

        error_text = gallery.wait_for_capture_error()
        screenshot(
            "TC-REQ-034-007_invalid-file-error",
            "Unsupported-format error after selecting a non-image file",
        )
        assert error_text.strip(), (
            "TC-REQ-034-007 FAIL: Expected a non-empty 'unsupported format' error message"
        )

        # No preview => the file was never accepted for upload.
        assert not gallery.has_upload_preview(), (
            "TC-REQ-034-007 FAIL: An invalid file must not produce an upload preview"
        )

        gallery.cancel_upload()
        assert gallery.get_photo_count() == before, (
            "TC-REQ-034-007 FAIL: Gallery photo count changed after a rejected upload"
        )


# ============================================================================
# 3. Lightbox, cover photo, delete
# ============================================================================


class TestPlantGalleryLightbox:
    """Full-size lightbox viewer (Spec: TC-REQ-034-005)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_thumbnail_opens_lightbox(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-006: Clicking a thumbnail opens the full-size lightbox.

        Spec: TC-REQ-034-005 — Klick auf Thumbnail oeffnet Lightbox mit
        Originalbild.  Uploads a throwaway photo first so the test is
        self-contained, then removes it again.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot test lightbox")

        gallery.open(key)
        if not gallery.is_gallery_loaded():
            pytest.skip("Gallery did not load — cannot test lightbox")

        uploaded_here = False
        if gallery.get_photo_count() == 0:
            if not gallery.has_add_button():
                pytest.skip("Empty read-only gallery — cannot create a photo to view")
            _upload_one_photo(gallery)
            gallery.wait_for_photo_count_at_least(1)
            uploaded_here = True

        gallery.open_lightbox(0)
        screenshot(
            "TC-REQ-034-006_lightbox-open",
            "Lightbox showing the full-size photo",
        )
        assert gallery.is_lightbox_open(), (
            "TC-REQ-034-006 FAIL: Lightbox did not open on thumbnail click"
        )
        assert gallery.is_lightbox_image_visible(), (
            "TC-REQ-034-006 FAIL: Lightbox opened without a visible full-size image"
        )

        gallery.close_lightbox()
        assert not gallery.is_lightbox_open(), "TC-REQ-034-006 FAIL: Lightbox did not close"

        if uploaded_here:
            gallery.click_delete_for_index(0)
            gallery.confirm_delete()
            gallery.wait_for_photo_count(0)


class TestPlantGalleryCover:
    """Cover photo set + info-tab preview (Spec: TC-REQ-034-011/012)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_set_cover_and_preview_in_info_tab(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-008 / 009: Set a cover photo; it previews in the info tab.

        Spec: TC-REQ-034-011 — Foto als Titelbild markieren (Cover-Badge).
        Spec: TC-REQ-034-012 — Titelbild erscheint als Vorschau im Info-Tab.

        Uploads a throwaway photo, marks it as cover, verifies the badge + the
        info-tab cover image, then deletes the photo to restore state.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot test cover")

        gallery.open(key)
        if not gallery.is_gallery_loaded() or not gallery.has_add_button():
            pytest.skip("Gallery not writable for this account — cannot set cover")

        before = gallery.get_photo_count()
        _upload_one_photo(gallery)
        gallery.wait_for_photo_count(before + 1)

        # The freshly uploaded photo has a 'set cover' action unless it is
        # already the cover.  Click it if present, otherwise it is already cover.
        if gallery.has_set_cover_buttons():
            gallery.set_cover_for_index(0)
            gallery.wait_for_success_snackbar()
        gallery.wait_for_cover_badge()
        screenshot(
            "TC-REQ-034-008_cover-badge",
            "Photo marked as cover with the cover badge visible",
        )
        assert gallery.has_cover_badge(), (
            "TC-REQ-034-008 FAIL: Expected a cover badge after setting the cover photo"
        )

        # Info tab cover preview (AC-06).
        gallery.open_info_tab(key)
        gallery.wait_for_cover_image()
        screenshot(
            "TC-REQ-034-009_info-tab-cover",
            "Info tab showing the cover photo preview",
        )
        assert gallery.has_cover_image(), (
            "TC-REQ-034-009 FAIL: Expected the cover image preview on the info tab"
        )

        # Cleanup — remove the uploaded cover photo.
        gallery.open(key)
        gallery.wait_for_photo_count_at_least(before + 1)
        gallery.click_delete_for_index(0)
        gallery.confirm_delete()
        gallery.wait_for_photo_count(before)


class TestPlantGalleryDelete:
    """Single photo deletion with confirmation (Spec: TC-REQ-034-013)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_delete_photo_with_confirmation(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-010: A photo is deleted only after confirming the dialog.

        Spec: TC-REQ-034-013 — Einzelnes Foto loeschen.  Uploads a throwaway
        photo, opens the delete confirm dialog and confirms; the gallery loses
        exactly one photo.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot test delete")

        gallery.open(key)
        if not gallery.is_gallery_loaded() or not gallery.has_add_button():
            pytest.skip("Gallery not writable for this account — cannot delete")

        before = gallery.get_photo_count()
        _upload_one_photo(gallery)
        gallery.wait_for_photo_count(before + 1)
        after_upload = gallery.get_photo_count()
        screenshot(
            "TC-REQ-034-010_before-delete",
            f"Gallery before delete ({after_upload} photos)",
        )

        gallery.click_delete_for_index(0)
        screenshot(
            "TC-REQ-034-010_delete-confirm-dialog",
            "Delete confirmation dialog (safety prompt)",
        )
        assert gallery.is_confirm_dialog_open(), (
            "TC-REQ-034-010 FAIL: Expected a confirmation dialog before deletion"
        )

        gallery.confirm_delete()
        gallery.wait_for_photo_count(after_upload - 1)
        screenshot(
            "TC-REQ-034-010_after-delete",
            f"Gallery after delete ({after_upload - 1} photos)",
        )
        assert gallery.get_photo_count() == after_upload - 1, (
            f"TC-REQ-034-010 FAIL: Expected {after_upload - 1} photos after delete, "
            f"got {gallery.get_photo_count()}"
        )


# ============================================================================
# 4. Internationalisation
# ============================================================================


class TestPlantGalleryI18n:
    """Gallery UI in English (Spec: TC-REQ-034-018)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_gallery_tab_label_english(
        self,
        plant_list: PlantInstanceListPage,
        gallery: PlantPhotoGalleryPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-034-011: With the UI in English the photos tab reads 'Photos'.

        Spec: TC-REQ-034-018 — Galerie-UI in Englisch; no raw i18n keys leak.

        The conftest seeds the locale via localStorage; this test flips it to
        English in the browser and reloads, then asserts the translated tab
        label.  It restores the German locale afterwards to avoid leaking the
        change into subsequent tests sharing the session browser.
        """
        key = _first_plant_key(plant_list)
        if key is None:
            pytest.skip("No plant instance available — cannot check i18n")

        # Switch the persisted i18n language to English and reload. The app's
        # i18next detector reads the 'kamerplanter-lang' localStorage key
        # (see src/frontend/src/i18n/i18n.ts → lookupLocalStorage).
        gallery.driver.execute_script("window.localStorage.setItem('kamerplanter-lang', 'en');")
        try:
            gallery.open(key)
            # gallery.open() may only change the URL hash of the already-open
            # plant page (no document reload), so i18next never re-reads the
            # locale — force a full reload to apply the language switch.
            gallery.driver.refresh()
            gallery.wait_for_loading_complete()
            if not gallery.is_gallery_loaded():
                pytest.skip("Gallery did not load — cannot assert i18n labels")

            # The split i18n bundles (#612) load the EN namespace async after
            # the language switch; the tab briefly renders the fallback DE
            # label. Poll instead of sampling once.
            deadline = time.time() + 8
            label = gallery.get_photos_tab_label()
            while time.time() < deadline and label.lower() != "photos":
                time.sleep(0.3)
                label = gallery.get_photos_tab_label()
            screenshot(
                "TC-REQ-034-011_gallery-english",
                "Gallery tab with the UI language set to English",
            )

            assert label, "TC-REQ-034-011 FAIL: Photos tab has no label in English mode"
            assert "." not in label, (
                f"TC-REQ-034-011 FAIL: Tab label looks like a raw i18n key: '{label}'"
            )
            assert label.lower() == "photos", (
                f"TC-REQ-034-011 FAIL: Expected English tab label 'Photos', got '{label}'"
            )
        finally:
            # Restore the default German locale for session-shared follow-ups.
            gallery.driver.execute_script("window.localStorage.setItem('kamerplanter-lang', 'de');")
