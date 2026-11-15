"""spec/privacy PRIV-201 (TA-200) — the erasure marker and the tombstone shape are defined once.

Before v0109 the application spelled ``"_anonymized"`` four times and ``^anon_[0-9a-f]{16}$`` three times; the
copies agreed only because a test held them equal, and the second tombstone generation (``anon2_``, PRIV-238)
would have had to be added in three places. The one definition is :mod:`app.domain.models.privacy`; every other
module imports it.

The scan reads the source of ``app/`` and refuses an assignment of the marker literal, and any spelling of the
tombstone shape, outside that module. Shipped migrations are exempt: NFR-016 M-7 freezes their source, so their
copies are deliberate (``v0107``, ``v0109``).

What the scan does not see: a marker built at runtime (``"_" + "anonymized"``) or a tombstone shape written with
another character class (``[a-f0-9]``). It is a text scan for the two spellings that existed, not a proof.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.domain.engines.erasure_engine import TOMBSTONE_FULLMATCH_REGEX, ErasureEngine
from app.domain.models import privacy

APP = Path(__file__).resolve().parents[3] / "app"
DEFINING_MODULE = APP / "domain" / "models" / "privacy.py"
FROZEN = APP / "migrations" / "versions"

#: ``NAME = "_anonymized"`` — an assignment of the literal, i.e. a second definition.
_MARKER_ASSIGNMENT = re.compile(r"""^\s*[A-Za-z_][A-Za-z0-9_]*\s*(?::[^=]+)?=\s*["']_anonymized["']""", re.M)
#: The tombstone shape as it was spelled (``anon_[0-9a-f]{16}``, ``anon2_[0-9a-f]{16}``).
_TOMBSTONE_SHAPE = re.compile(r"anon2?_\[0-9a-f\]\{16\}")


def _application_sources() -> list[Path]:
    return [path for path in APP.rglob("*.py") if FROZEN not in path.parents and path != DEFINING_MODULE]


def test_the_scan_reaches_the_application_and_finds_the_definition() -> None:
    """The measuring tool first: a pattern that never matches would make the guard vacuously green."""
    text = DEFINING_MODULE.read_text(encoding="utf-8")

    assert _MARKER_ASSIGNMENT.search(text)
    assert _TOMBSTONE_SHAPE.search(text)
    assert len(_application_sources()) > 500


@pytest.mark.parametrize(
    "line",
    ['ANONYMIZED_MARKER = "_anonymized"', "_MARKER: str = '_anonymized'", 'X = re.compile(r"^anon_[0-9a-f]{16}$")'],
)
def test_the_scan_recognises_a_second_definition(line: str) -> None:
    assert _MARKER_ASSIGNMENT.search(line) or _TOMBSTONE_SHAPE.search(line)


def test_no_application_module_defines_the_marker_or_the_tombstone_shape_again() -> None:
    offenders = [
        str(path.relative_to(APP))
        for path in _application_sources()
        if _MARKER_ASSIGNMENT.search(text := path.read_text(encoding="utf-8")) or _TOMBSTONE_SHAPE.search(text)
    ]

    assert offenders == []


def test_the_engine_names_are_the_definition_itself() -> None:
    assert TOMBSTONE_FULLMATCH_REGEX is privacy.TOMBSTONE_REGEX


@pytest.mark.parametrize("value", ["anon_0123456789abcdef", "anon2_0123456789abcdef"])
def test_both_generations_are_tombstones(value: str) -> None:
    assert privacy.is_tombstone(value)
    assert ErasureEngine.is_tombstone(value)


@pytest.mark.parametrize(
    "value", ["anon_0123", "anon3_0123456789abcdef", "xanon_0123456789abcdef", "anon_0123456789ABCDEF", "_anonymized"]
)
def test_near_misses_are_not(value: str) -> None:
    assert not privacy.is_tombstone(value)
