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
