"""Gherkin line classification — single source of truth for every ``.feature`` parser.

Two independent consumers parse the very same ``.feature`` syntax in this
repository:

* ``tests/e2e/conftest.py`` scans the tag lines so that every Gherkin tag is
  registered as a pytest marker *before* collection starts (pytest-bdd turns
  tags into markers at decoration time and never registers them, and the suite
  runs under ``--strict-markers``).
* ``scripts/check_bdd_traceability.py`` scans tags, keywords and docstrings to
  resolve every scenario back to its declared ``@TC-…`` test case.

Both used to carry a hand-copied ``_TAG_LINE`` regex, but only the traceability
script tracked Gherkin **docstring** state. The two halves therefore drifted,
and the conftest half was the dangerous one: it classified *any* line consisting
solely of ``@token`` items as a tag line — including a line inside a Gherkin
docstring, where ``@example``, ``@media`` or an e-mail-ish ``@handle`` is
ordinary prose. Such a phantom tag is then rejected by the conftest typo guard
and raised as a ``pytest.UsageError`` from ``pytest_configure``, which is not a
failing test but a **collection abort**: exit 2, and all ~720 E2E tests never
run. A one-line prose change in a ``.feature`` could take the whole suite down.

This module removes the drift by owning the classification once. It is
deliberately **standard-library only** and free of any Selenium / E2E runtime
import, for three reasons: it runs inside ``pytest_configure`` on the collection
path, ``scripts/check_bdd_traceability.py`` must keep working on a bare checkout
without the E2E extras installed, and it has to be unit-testable in the ordinary
(non-E2E) test run.

Scope note: this is *not* a Gherkin parser. It classifies lines — the subset
this repository writes (tags, comments, docstrings, everything else) — and
leaves keyword/dialect interpretation to the caller, which is where the two
consumers legitimately differ.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum

# A Gherkin tag line: only ``@tag`` tokens, nothing else. The "nothing else"
# anchoring is what keeps an ``@`` inside step text ("Given the user @admin
# logs in") from being read as a tag. It is *not* enough on its own — a
# docstring line may consist of nothing but ``@token`` items — which is exactly
# what the docstring state in :func:`iter_lines` exists for.
TAG_LINE: re.Pattern[str] = re.compile(r"^\s*@\S+(?:[ \t]+@\S+)*[ \t]*$")

# Gherkin docstring fences. Cucumber accepts both the triple-quote and the
# triple-backtick form, and everything between an opening fence and the next
# line starting with the *same* fence is opaque payload: it may contain ``#``,
# a line that looks like a keyword, or a line that looks like a tag block.
DOCSTRING_DELIMITERS: tuple[str, ...] = ('"""', "```")


class GherkinLineKind(StrEnum):
    """What a single source line of a ``.feature`` file is.

    ``CONTENT`` is deliberately coarse: keyword lines (``Feature:``,
    ``Scenario:``, ``Examples:``), steps, data tables and free-form description
    all land there. Distinguishing them needs the dialect table, which only the
    traceability check cares about, so that decision stays with the caller.
    """

    BLANK = "blank"
    COMMENT = "comment"
    DOCSTRING = "docstring"
    TAG = "tag"
    CONTENT = "content"


@dataclass(frozen=True, slots=True)
class GherkinLine:
    """One classified source line of a ``.feature`` file."""

    number: int
    """1-based line number, suitable for diagnostics."""

    raw: str
    """The line exactly as written, without its line terminator."""

    stripped: str
    """``raw`` with surrounding whitespace removed."""

    kind: GherkinLineKind
    """The classification, including the docstring context of this line."""

    @property
    def is_tag(self) -> bool:
        """Return whether this line is a Gherkin tag line outside any docstring."""
        return self.kind is GherkinLineKind.TAG

    @property
    def tags(self) -> tuple[str, ...]:
        """Return the tag names on this line, without their leading ``@``.

        Empty for every non-tag line, so a caller may read it unconditionally.
        A bare ``@`` token yields no name (there is nothing to register), which
        matches what both consumers did before this module existed.
        """
        if self.kind is not GherkinLineKind.TAG:
            return ()
        return tuple(token[1:] for token in self.stripped.split() if len(token) > 1)


def _as_lines(source: str | Iterable[str]) -> Iterable[str]:
    """Normalise the input to a sequence of terminator-free lines.

    Accepting both a whole file's text and an already-split sequence keeps the
    API usable by a caller that needs the raw lines for something else too (the
    traceability check reads the leading ``# language:`` header off them before
    it starts classifying).
    """
    return source.splitlines() if isinstance(source, str) else source


def iter_lines(source: str | Iterable[str]) -> Iterator[GherkinLine]:
    """Classify every line of a ``.feature`` source, docstring context included.

    The docstring state machine is the whole point of this function: a line
    inside a fence (see :data:`DOCSTRING_DELIMITERS`) is reported as
    :attr:`GherkinLineKind.DOCSTRING` and therefore never as a tag, a comment or
    a keyword — no matter what it contains.

    Every line is yielded, none is swallowed, so line numbers stay meaningful
    and each caller decides for itself which kinds it ignores.

    An unterminated docstring at end of file is not an error here: the remaining
    lines are simply reported as ``DOCSTRING`` and the iterator ends. Refusing
    to parse would re-introduce exactly the blast radius this module exists to
    remove — a malformed ``.feature`` must never abort the collection of an
    unrelated suite.

    Args:
        source: The file's text, or its already-split lines.

    Yields:
        One :class:`GherkinLine` per input line, in source order.
    """
    docstring_delimiter: str | None = None

    for number, raw in enumerate(_as_lines(source), start=1):
        stripped = raw.strip()

        if docstring_delimiter is not None:
            # Inside a docstring. The closing fence line is itself part of the
            # docstring — reporting it as DOCSTRING keeps a ``"""`` line from
            # ever being mistaken for content.
            if stripped.startswith(docstring_delimiter):
                docstring_delimiter = None
            kind = GherkinLineKind.DOCSTRING
        elif stripped.startswith(DOCSTRING_DELIMITERS):
            # Opening fence. The delimiter is remembered verbatim so a ``"""``
            # docstring is not closed by a ``` ``` ``` line and vice versa.
            docstring_delimiter = stripped[:3]
            kind = GherkinLineKind.DOCSTRING
        elif not stripped:
            kind = GherkinLineKind.BLANK
        elif stripped.startswith("#"):
            # Comments and the ``# language:`` header.
            kind = GherkinLineKind.COMMENT
        elif TAG_LINE.match(raw):
            kind = GherkinLineKind.TAG
        else:
            kind = GherkinLineKind.CONTENT

        yield GherkinLine(number=number, raw=raw, stripped=stripped, kind=kind)


def iter_tags(source: str | Iterable[str]) -> Iterator[tuple[int, str]]:
    """Yield every Gherkin tag declared outside a docstring.

    Args:
        source: The file's text, or its already-split lines.

    Yields:
        ``(line_number, tag_name)`` pairs in source order, the tag name without
        its leading ``@``. A tag repeated on several lines is yielded once per
        occurrence — de-duplication is the caller's business, since the
        traceability check needs the positions and the marker registration does
        not.
    """
    for line in iter_lines(source):
        for tag in line.tags:
            yield line.number, tag
