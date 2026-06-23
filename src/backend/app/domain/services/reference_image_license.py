"""REQ-029-A §4.1 — License normalisation and filtering for reference images.

Media sources report licenses either as Creative-Commons URIs
(``http://creativecommons.org/licenses/by-nc/4.0/``) or as enum-like tokens
(``CC_BY_NC_4_0``, the GBIF/iNaturalist style). These pure functions map any
such string to a :class:`ReferenceLicense` and decide whether it may be indexed.

The matching order is deliberate: the most specific compound variants
(``-nc-sa``, ``-nc-nd``) are checked before ``-nc`` / ``-sa`` / ``-nd``, and all
of those before the bare ``by`` — so e.g. ``by-nc-sa`` never collapses to
``CC-BY-NC`` or ``CC-BY``.
"""

from app.domain.models.reference_image import (
    ACCEPTED_LICENSES,
    ACCEPTED_LICENSES_NONCOMMERCIAL,
    ReferenceLicense,
)


def normalize_license(raw: str | None) -> ReferenceLicense:
    """Map a raw license string (URI or GBIF/iNat token) to a :class:`ReferenceLicense`."""
    if not raw:
        return ReferenceLicense.UNKNOWN

    token = raw.strip().lower().replace("_", "-").replace(" ", "-")

    # Public domain / CC0 first (it contains no "by").
    if "publicdomain" in token or "zero" in token or "cc0" in token or token.startswith("pd"):
        return ReferenceLicense.CC0
    # Compound NC variants must precede the simpler "-nc"/"-sa"/"-nd"/"by" checks.
    if "by-nc-sa" in token:
        return ReferenceLicense.CC_BY_NC_SA
    if "by-nc-nd" in token:
        return ReferenceLicense.CC_BY_NC_ND
    if "by-nc" in token:
        return ReferenceLicense.CC_BY_NC
    if "by-sa" in token:
        return ReferenceLicense.CC_BY_SA
    if "by-nd" in token:
        return ReferenceLicense.CC_BY_ND
    if "by" in token:
        return ReferenceLicense.CC_BY
    return ReferenceLicense.UNKNOWN


def is_acceptable(license_value: ReferenceLicense, *, allow_noncommercial: bool = False) -> bool:
    """True if the license permits embedding/indexing.

    ``CC0``/``CC-BY`` are always accepted. ``CC-BY-NC`` is accepted ONLY when
    ``allow_noncommercial=True`` (i.e. the application runs non-commercially;
    pest-image-sources-analysis.md §4.3). Copyleft (``-SA``), no-derivatives
    (``-ND``) and ``UNKNOWN`` stay rejected regardless of the flag, because
    their share-alike/derivative restrictions persist even non-commercially.
    """
    if allow_noncommercial:
        return license_value in ACCEPTED_LICENSES_NONCOMMERCIAL
    return license_value in ACCEPTED_LICENSES
