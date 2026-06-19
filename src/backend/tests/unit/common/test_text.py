"""Tests for HTML-stripping of reference-image attributions (REQ-029-A §4.1)."""

from app.common.text import strip_html


def test_strip_html_removes_anchor_markup():
    raw = '<a rel="nofollow" class="external text" href="https://flickr.com/x">INRA DIST</a> from France'
    assert strip_html(raw) == "INRA DIST from France"


def test_strip_html_unescapes_entities():
    assert strip_html("Jane &amp; John") == "Jane & John"


def test_strip_html_collapses_whitespace():
    assert strip_html("  Jane\n  Doe  ") == "Jane Doe"


def test_strip_html_plain_text_is_unchanged():
    assert strip_html("© rarehero") == "© rarehero"


def test_strip_html_none_stays_none():
    assert strip_html(None) is None


def test_strip_html_markup_only_becomes_none():
    assert strip_html("<a href='x'></a>") is None
