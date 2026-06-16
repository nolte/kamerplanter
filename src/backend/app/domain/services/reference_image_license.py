"""REQ-029-A §4.1 — License normalisation and filtering for reference images.

GBIF reports licenses either as Creative-Commons URIs
(``http://creativecommons.org/licenses/by-nc/4.0/``) or as enum-like tokens
(``CC_BY_NC_4_0``). These pure functions map any such string to a
:class:`ReferenceLicense` and decide whether it may be indexed.

The matching order is deliberate: the more specific ``-NC`` / ``-SA`` variants
are checked before the bare ``by`` so that e.g. ``by-nc`` never collapses to
``CC-BY``.
"""

from app.domain.models.reference_image import ACCEPTED_LICENSES, ReferenceLicense


def normalize_license(raw: str | None) -> ReferenceLicense:
    """Map a raw GBIF license string to a :class:`ReferenceLicense`."""
    if not raw:
        return ReferenceLicense.UNKNOWN

    token = raw.strip().lower().replace("_", "-").replace(" ", "-")

    # Public domain / CC0 first (it contains no "by").
    if "publicdomain" in token or "zero" in token or "cc0" in token or token.startswith("pd"):
        return ReferenceLicense.CC0
    # Non-commercial and share-alike must precede the bare "by" check.
    if "by-nc" in token:
        return ReferenceLicense.CC_BY_NC
    if "by-sa" in token:
        return ReferenceLicense.CC_BY_SA
    if "by" in token:
        return ReferenceLicense.CC_BY
    return ReferenceLicense.UNKNOWN


def is_acceptable(license_value: ReferenceLicense) -> bool:
    """True if the license permits embedding/indexing (CC0 or CC-BY only)."""
    return license_value in ACCEPTED_LICENSES
