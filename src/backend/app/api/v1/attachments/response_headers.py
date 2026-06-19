"""NFR-013 — download-response header hardening (SEC-009).

Centralizes the security headers applied to every attachment download / stream
response (tenant router + global token router) so the rules stay consistent:

* ``X-Content-Type-Options: nosniff`` is always set — the browser must honor the
  declared ``Content-Type`` instead of MIME-sniffing user-supplied bytes.
* Only ``image/*`` MIME types may be served ``inline``. Every other type
  (``application/pdf``, ``text/csv``, ``application/zip``, …) is forced to
  ``Content-Disposition: attachment`` so a malicious payload cannot execute in
  the browsing context (drive-by / stored-XSS via served content).

When the MIME type is not known at the call site (the token router has no
catalog lookup) ``mime_type`` is ``None``; the helper then keeps an explicitly
requested ``inline`` disposition only when it is safe to assume an image is not
involved — to stay safe it downgrades any non-image-confirmed ``inline`` to
``attachment``.
"""

from __future__ import annotations


def _is_image(mime_type: str | None) -> bool:
    return bool(mime_type) and mime_type.lower().startswith("image/")


def harden_download_headers(
    headers: dict[str, str],
    *,
    mime_type: str | None,
    requested_disposition: str | None = None,
) -> dict[str, str]:
    """Return ``headers`` with download security headers applied (SEC-009).

    Args:
        headers: Base response headers (mutated and returned).
        mime_type: The object's MIME type, or ``None`` when unknown.
        requested_disposition: A ``Content-Disposition`` the caller wants to set
            (e.g. ``inline; filename="..."``). It is honored only for confirmed
            ``image/*`` types; otherwise it is replaced with ``attachment``.

    Returns:
        The hardened headers dict.
    """
    headers["X-Content-Type-Options"] = "nosniff"

    if _is_image(mime_type):
        # Images may render inline; preserve a requested inline disposition.
        if requested_disposition:
            headers["Content-Disposition"] = requested_disposition
        return headers

    # Non-image (or unknown) content must download, never render inline.
    headers["Content-Disposition"] = "attachment"
    return headers


__all__ = ["harden_download_headers"]
