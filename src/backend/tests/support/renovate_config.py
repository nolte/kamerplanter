"""Reading ``renovate.json5`` textually, for the guards that measure it.

``renovate.json5`` is JSON5 — comments, single quotes, trailing commas, unquoted
keys — and no JSON5 parser is in the backend's locked dependency set. Adding one
for a guard would put a dependency into the required lane's install for the sake
of reading two arrays, so the guards locate a manager block and extract its
literals instead.

Both functions here were written inside ``test_uv_pin_manager_covers_every_pin``
and moved out when ``test_nuclei_templates_digest_pin`` (#1543) needed the same
two, each having re-derived one of them slightly worse: a second copy of a reader
whose failure mode is "silently returns nothing" is exactly the kind of
duplication that lets one copy be fixed and the other keep lying.
"""

from __future__ import annotations

import json
from typing import Any


def strip_comments(text: str) -> str:
    """Drop whole-line ``//`` comments.

    NOT cosmetic, and the reason is a defect ``test_uv_pin_manager_covers_every_pin``
    had in its first draft. The custom manager for workflow ``run:`` pins carries
    a COMMENT in its ``matchStrings`` explaining that
    ``[tool.uv].required-version`` replaced the literal ``uv==`` it used to match.
    A predicate reading the raw block text for that phrase therefore classified
    that manager as a pin reader and lent its ``.github/workflows/**`` pattern to
    the coverage check — prose answering for configuration, which is this
    repository's most expensive measurement bug.

    Only whole-line comments are dropped: a ``//`` inside a string (``https://``,
    and every ``managerFilePatterns`` regex begins with ``/``) must survive, so a
    trailing-comment form is deliberately left unhandled rather than handled
    wrongly. Each caller asserts that the literals really came through.
    """
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))


def array_value(text: str, key: str) -> str | None:
    """The ``[...]`` value of *key*, by bracket matching rather than by slicing.

    Slicing from one key to the next assumes an order the file does not promise;
    a block that put ``matchStrings`` before ``managerFilePatterns`` would have
    yielded an empty slice and a silently empty pattern list — or, worse, the
    next manager's array.
    """
    start = text.find(f"{key}:")
    if start == -1:
        return None
    opening = text.find("[", start)
    if opening == -1:
        return None
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                return text[opening : index + 1]
    return None


_JSON5_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def _skip_blank_and_comments(text: str, index: int) -> int:
    """First index at or after *index* that is neither whitespace nor a comment."""
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text.startswith("//", index):
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline + 1
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end == -1 else end + 2
        else:
            break
    return index


def json5_to_json(text: str) -> str:
    """Rewrite the JSON5 subset ``renovate.json5`` uses into strict JSON.

    Added for ``test_renovate_automerge_policy`` (NFR-009 §3.4), which asserts
    WHERE a key sits — top level versus inside a ``packageRules`` entry — and a
    textual reader cannot tell those apart without guessing from indentation.
    The subset is exactly what the file uses: ``//`` and ``/* */`` comments,
    single- and double-quoted strings with backslash escapes, unquoted
    identifier keys, trailing commas. Comments are dropped by a tokenizer that
    knows it is inside a string, so the ``//`` of ``https://`` and of every
    ``/…/`` regex survives — the case ``strip_comments`` above deliberately does
    not handle. Anything outside the subset reaches ``json.loads`` unchanged
    and fails there loudly, which is the intended failure mode.
    """
    out: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in "'\"":
            quote, index, chars = char, index + 1, []
            while text[index] != quote:
                if text[index] == "\\":
                    escaped = text[index + 1]
                    chars.append(_JSON5_ESCAPES.get(escaped, escaped))
                    index += 2
                else:
                    chars.append(text[index])
                    index += 1
            index += 1
            out.append(json.dumps("".join(chars)))
        elif text.startswith("//", index) or text.startswith("/*", index):
            index = _skip_blank_and_comments(text, index)
            out.append("\n")
        elif char.isalpha() or char in "_$":
            end = index
            while end < len(text) and (text[end].isalnum() or text[end] in "_$"):
                end += 1
            word = text[index:end]
            out.append(word if word in ("true", "false", "null") else json.dumps(word))
            index = end
        elif char == ",":
            following = _skip_blank_and_comments(text, index + 1)
            if following < len(text) and text[following] not in "]}":
                out.append(",")
            index += 1
        else:
            out.append(char)
            index += 1
    return "".join(out)


def load(text: str) -> dict[str, Any]:
    """``renovate.json5`` as the object Renovate reads, via :func:`json5_to_json`."""
    config = json.loads(json5_to_json(text))
    if not isinstance(config, dict):
        raise ValueError("renovate.json5 does not hold an object at its top level")
    return config
