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

#: Cache policy of the session-authorized download routes (#2254). The browser
#: may keep the bytes but must ask the server before every reuse, so a logout,
#: a removed membership or a deleted attachment takes effect on the next view;
#: an unchanged object costs a ``304`` (``If-None-Match`` against the ETag).
#: ``private, max-age=86400`` served the cached bytes for a day without asking.
SESSION_DOWNLOAD_CACHE_CONTROL = "private, no-cache"

#: Cache policy of the token download route (#2254). The token is a bearer
#: credential with a short lifetime (``STORAGE_PRESIGN_TTL_SECONDS``, 15 min by
#: default) and every presign issues a new URL, so a cached copy can only be
#: reused under a URL whose authorization ends long before a ``max-age=86400``
#: would. Nothing is stored: the copy cannot outlive the token or a deletion.
TOKEN_DOWNLOAD_CACHE_CONTROL = "no-store"


def if_none_match_hits(if_none_match: str | None, etag: str) -> bool:
    """Whether an ``If-None-Match`` header matches ``etag`` (weak comparison, RFC 9110 §13.1.2)."""
    if not if_none_match:
        return False
    if if_none_match.strip() == "*":
        return True

    wanted = _opaque_tag(etag)
    return any(_opaque_tag(candidate) == wanted for candidate in if_none_match.split(","))


def _opaque_tag(tag: str) -> str:
    """An entity tag without surrounding space and without the weak ``W/`` marker."""
    return tag.strip().removeprefix("W/")


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


__all__ = [
    "SESSION_DOWNLOAD_CACHE_CONTROL",
    "TOKEN_DOWNLOAD_CACHE_CONTROL",
    "harden_download_headers",
    "if_none_match_hits",
]
