#!/usr/bin/env python3
"""Reduce a source file to the text a machine executes, dropping what it only reads.

Every gate in this repository that asks "does the tree do X?" has to answer it
from text, and text carries two kinds of content: the code, and the prose
alongside it. A predicate that does not separate them answers the wrong
question, in both directions:

* **presence** — ``"fetchAllFertilizers" in slice_source`` is satisfied by a
  comment head that names the loader. Deleting the real call leaves the gate
  green (#1610, #1624).
* **absence** — ``"cec_meq_per_100g" not in migration_source`` is *falsified* by
  a docstring that says the field is deliberately **not** migrated. The gate
  goes red over a sentence and green over the defect
  (``test_model_field_renames_have_migrations``), and a grep once reported a
  repaired defect as open because the repair's own explanation still named it.

Both are the same mistake: prose answering for code. This module is the one
place that mistake is solved, so a new gate does not have to re-derive it — and
so the next fix lands once rather than in two of four siblings.

It deliberately does **not** drop string literals. A literal is executable
content: ``load_yaml("species.yaml")`` names a real file, and a gate that reads
literals is reading a decision. Only comments and Python docstrings go.

Known limits, stated rather than hidden
---------------------------------------

The C-like stripper is a tokeniser, not a parser. It recognises string literals
(``'``, ``"``, and template literals) so a ``//`` inside one survives, but it
does not track regular-expression literals: ``/a\\/\\/b/`` would lose its tail.
No gate in this tree reads a regex literal, and a parser for each language is a
dependency none of them may take. The YAML/TOML/shell stripper is quote-aware on
the same terms.

Python is handled by :mod:`tokenize`, which is the real lexer, plus an
:mod:`ast` pass for docstrings — so for Python the result is exact, and it
parses again whenever the input did: a docstring that is the only statement of
its class or function body is replaced by ``pass`` rather than by nothing, so no
block is left empty (#1671). That ``pass`` is the one token the Python result
contains that the input did not; it names nothing a gate could look for.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize

__all__ = ["UnknownLanguage", "executable_source", "is_called", "language_of"]

#: Languages this module can reduce, mapped to the stripper that handles them.
_C_LIKE = frozenset({"typescript", "javascript", "json5", "tsx", "jsx"})
_HASH_LIKE = frozenset({"yaml", "toml", "shell", "ini", "dockerfile"})

#: Extension → language, for callers that have a path rather than a name.
_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".json5": "json5",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".lock": "toml",
    ".sh": "shell",
}


class UnknownLanguage(ValueError):
    """Raised for a language this module has no stripper for.

    Refusing is the point: returning the text unchanged would make the caller's
    predicate silently prose-permeable again, which is the defect this module
    exists to close.
    """


def language_of(suffix: str) -> str:
    """Map a file suffix to a language name.

    Args:
        suffix: File suffix including the dot, e.g. ``".ts"``.

    Returns:
        The language name accepted by :func:`executable_source`.

    Raises:
        UnknownLanguage: If the suffix is not mapped.
    """
    try:
        return _BY_SUFFIX[suffix.lower()]
    except KeyError:
        raise UnknownLanguage(f"no stripper for files ending in {suffix!r}") from None


def executable_source(text: str, *, language: str) -> str:
    """Return *text* with its comments (and Python docstrings) removed.

    Line structure is preserved: every dropped span is replaced by nothing on
    its own line rather than by joining lines, so a line number taken from the
    result still points at the same line of the original.

    Args:
        text: The file's contents.
        language: One of ``python``, ``typescript``, ``javascript``, ``json5``,
            ``yaml``, ``toml``, ``shell``, ``ini``, ``dockerfile``.

    Returns:
        The executable text.

    Raises:
        UnknownLanguage: If *language* is not supported.
    """
    if language == "python":
        return _strip_python(text)
    if language in _C_LIKE:
        return _strip_c_like(text)
    if language in _HASH_LIKE:
        return _strip_hash_like(text)
    raise UnknownLanguage(f"no stripper for language {language!r}")


def is_called(name: str, text: str, *, language: str) -> bool:
    """Report whether *name* is **called** in the executable part of *text*.

    This is the predicate a presence gate wants, and the one a bare ``in`` test
    is mistaken for. ``name`` mentioned in a comment head, in a sentence, or as
    a substring of a longer identifier does not satisfy it; ``name(...)`` does.

    Args:
        name: The identifier to look for.
        text: The file's contents.
        language: As for :func:`executable_source`.

    Returns:
        ``True`` when the executable text calls *name*.

    Raises:
        UnknownLanguage: If *language* is not supported.
    """
    return bool(
        re.search(
            rf"(?<![\w$]){re.escape(name)}\s*\(",
            executable_source(text, language=language),
        )
    )


def _strip_python(text: str) -> str:
    """Drop Python comments and docstrings, keeping every other line in place."""
    try:
        drop = _python_comment_spans(text)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # An unparsable module is not silently passed through as executable: the
        # caller gets the hash-like reduction, which is strictly more aggressive
        # for `#` comments and never less.
        return _strip_hash_like(text)
    try:
        drop |= _python_docstring_spans(text)
    except SyntaxError:
        pass
    lines = text.splitlines(keepends=True)
    for row, start, end, replacement in sorted(drop, reverse=True):
        line = lines[row]
        lines[row] = line[:start] + replacement + line[end:]
    return "".join(lines)


#: A removed span as ``(row index, start col, end col, replacement)``. Columns
#: are *character* offsets into the line; ``replacement`` is ``""`` except where
#: dropping the span would leave a block with no statement at all.
_Span = tuple[int, int, int, str]


def _python_comment_spans(text: str) -> set[_Span]:
    """Locate every comment token as a span to drop."""
    spans: set[_Span] = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            spans.add((token.start[0] - 1, token.start[1], token.end[1], ""))
    return spans


def _char_col(line: str, byte_col: int) -> int:
    """Convert an :mod:`ast` column (a UTF-8 *byte* offset) to a character offset.

    ``ast`` reports ``col_offset``/``end_col_offset`` in bytes, while the
    stripper slices ``str`` lines by character. On a line with a non-ASCII
    character before the column the two differ, and slicing by the byte value
    overshoots — past the end of the docstring and, on its closing line, past
    the newline, which joins the next line onto it (#1671).
    """
    return len(line.encode("utf-8")[:byte_col].decode("utf-8", errors="ignore"))


def _python_docstring_spans(text: str) -> set[_Span]:
    """Locate every docstring, as one span per line it occupies.

    A docstring is a bare string expression that opens a module, class, or
    function body — the same rule the interpreter uses, so this cannot disagree
    with what is actually documentation and what is a value.

    When the docstring is the *only* statement of a class or function body,
    removing it would leave an empty block, which does not parse. Its first
    line is then replaced by ``pass`` instead of by nothing, so the result stays
    parsable while every line keeps its number (#1671). ``pass`` is a statement
    that does nothing; it names no identifier and calls nothing, so no presence
    or absence predicate can be satisfied or falsified by it.
    """
    spans: set[_Span] = set()
    lines = text.splitlines()
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if not isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue
        body = getattr(node, "body", [])
        if not body:
            continue
        first = body[0]
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)):
            continue
        if not isinstance(first.value.value, str):
            continue
        only_statement = len(body) == 1 and not isinstance(node, ast.Module)
        first_row = first.lineno - 1
        last_row = (first.end_lineno or first.lineno) - 1
        for row in range(first_row, last_row + 1):
            line = lines[row]
            start = _char_col(line, first.col_offset) if row == first_row else 0
            end = (
                _char_col(line, first.end_col_offset or 0)
                if row == last_row
                else len(line)
            )
            replacement = "pass" if only_statement and row == first_row else ""
            spans.add((row, start, end, replacement))
    return spans


#: One pass over C-like source: a quoted or backticked literal (kept), or a
#: ``/* … */`` block or ``//`` line comment (dropped). The alternation tries the
#: literal first, so a ``//`` inside ``"https://…"`` never starts a comment.
_C_TOKEN = re.compile(
    r"""'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|`(?:\\.|[^`\\])*`|(/\*.*?\*/|//[^\n]*)""",
    re.DOTALL,
)


def _strip_c_like(text: str) -> str:
    """Drop ``//`` and ``/* */`` comments, keeping string and template literals."""

    def replace(match: re.Match[str]) -> str:
        if match.group(1) is None:
            return match.group(0)
        # Keep the newlines a block comment spanned, so line numbers survive.
        return "\n" * match.group(1).count("\n")

    return _C_TOKEN.sub(replace, text)


def _strip_hash_like(text: str) -> str:
    """Drop ``#`` comments outside quotes, line by line.

    Quote-aware because a ``#`` is ordinary inside a YAML or shell string —
    ``image: foo@sha256:…`` has none, but ``run: echo "a # b"`` does, and a
    blind cut would silently shorten the line a gate then measures.
    """
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        quote: str | None = None
        cut = None
        for index, char in enumerate(line):
            if quote is not None:
                if char == quote:
                    quote = None
                continue
            if char in "'\"":
                quote = char
                continue
            if char == "#":
                cut = index
                break
        if cut is None:
            out.append(line)
        else:
            trailing = "\n" if line.endswith("\n") else ""
            out.append(line[:cut].rstrip(" \t") + trailing)
    return "".join(out)
