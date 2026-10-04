"""#2139 — every image type the upload pipeline admits by default is one the EXIF strip can strip.

The defect class: an image type sits in the MIME whitelist while
``exif_stripper`` cannot re-encode it, so the pipeline stores it with its
EXIF/GPS block and the REQ-025 erasure later records it as ``skipped``. #2139
found it for HEIC/HEIF (the iPhone default): accepted by
``storage_allowed_mime_types`` and ``_PHOTO_MIME_TYPES``, passed through by the
strip.

The class is not HEIC: it is **every ``image/*`` type any attachment category
resolves to under the default settings**, enumerated through the resolver the
pipeline itself calls (``Settings.allowed_mime_types_for_category``) for every
``AttachmentCategory``. Each must be ``is_strippable_format``. An operator
override that re-adds such a type is refused at runtime by
``AttachmentService.upload`` while ``storage_strip_exif`` is on
(``tests/api/test_attachments_router.py::TestHeicIsNotAcceptedUnstripped``).

**What it cannot see**: a type whose stripper entry exists but does not in fact
remove metadata — the strip tests own that (``test_exif_stripper.py``).
"""

from __future__ import annotations

import pytest

from app.common.enums import AttachmentCategory
from app.config.settings import Settings
from app.domain.engines.storage.exif_stripper import is_strippable_format


def _admitted_image_types(settings: Settings) -> dict[str, set[str]]:
    return {
        category.value: {
            mime for mime in settings.allowed_mime_types_for_category(category.value) if mime.startswith("image/")
        }
        for category in AttachmentCategory
    }


def test_every_image_type_admitted_by_default_is_strippable() -> None:
    admitted = _admitted_image_types(Settings())
    # Non-vacuity: the photo categories admit images at all.
    assert admitted["diary"] >= {"image/jpeg", "image/png", "image/webp"}

    unstrippable = {
        f"{category}: {mime}"
        for category, mimes in admitted.items()
        for mime in mimes
        if not is_strippable_format(mime)
    }
    assert not unstrippable, f"admitted but never stripped of EXIF/GPS (#2139): {sorted(unstrippable)}"


@pytest.mark.parametrize("mime", ["image/heic", "image/heif"])
def test_the_check_flags_a_whitelist_that_admits_an_unstrippable_type(mime: str) -> None:
    """Self-test through the same enumeration: a configuration that admits HEIC is reported."""
    old = Settings(storage_allowed_mime_types_diary=f"image/jpeg,{mime}")
    admitted = _admitted_image_types(old)

    assert any(mime in mimes and not is_strippable_format(mime) for mimes in admitted.values())
