"""Small text-sanitisation helpers shared across the app."""

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(value: str | None) -> str | None:
    """Reduce an HTML-bearing string to collapsed plain text.

    Reference-image attributions from Wikimedia Commons (``extmetadata`` →
    ``Artist``) can contain HTML such as ``<a href="...">Name</a> from France``.
    Persisting that markup leaks it into the gallery caption, so we strip tags,
    unescape entities and collapse whitespace at ingestion. ``None`` and strings
    that become empty after stripping return ``None`` (so callers keep treating
    "no attribution" uniformly).
    """
    if value is None:
        return None
    text = _WS_RE.sub(" ", html.unescape(_TAG_RE.sub("", value))).strip()
    return text or None
