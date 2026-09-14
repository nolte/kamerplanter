"""NFR-015 §6.1 — a ZAP suppression may not outlive its review, and this enforces it.

`tests/security/zap-rules.tsv` states the rule in its own header:

    Every IGNORE row MUST include "# expires YYYY-MM-DD — approved by <role>"
    in the Note column. Expired IGNOREs trigger a CI warning; after 30 days
    of grace, they fail the build.

Nothing checked it. Both files were empty until #1376/#1389, so the convention had
never been exercised — a documented rule with no enforcement, which is the shape
#1042 catalogues and the one this repository has spent a lot of review time on.

A suppression is a security control turned off. Turning one off on evidence is
ordinary engineering; leaving it off because nobody noticed the note expired is how
a real finding gets hidden behind an old false positive. So the grace period is
arithmetic here, not prose.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

#: The repository root is four levels up from ``src/backend/tests/unit/`` — measured,
#: not counted by eye: ``parents[3]`` is ``src/``, which has no ``tests/security``,
#: and the control below caught that immediately.
_SECURITY = Path(__file__).resolve().parents[4] / "tests" / "security"
_RULE_FILES = ("zap-rules.tsv", "zap-api-rules.tsv")

#: The grace the header promises after an expiry before the build fails.
_GRACE_DAYS = 30

_EXPIRY = re.compile(r"#\s*expires\s+(\d{4}-\d{2}-\d{2})\s+—\s+approved by\s+(\S+)")


def _rows() -> list[tuple[str, int, list[str]]]:
    """``(file, line number, fields)`` for every non-comment row in both files."""
    found: list[tuple[str, int, list[str]]] = []
    for name in _RULE_FILES:
        path = _SECURITY / name
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            found.append((name, number, line.split("\t")))
    return found


def test_the_rule_files_are_where_this_test_thinks_they_are():
    """The control. Both files must exist, or every check below passes over nothing.

    They are copied into the scan by `security-zap-postmerge.yml` and
    `security-zap-nightly.yml`; a rename there without one here would leave this
    file agreeing with an empty list.
    """
    missing = [name for name in _RULE_FILES if not (_SECURITY / name).is_file()]

    assert not missing, f"ZAP rule files not found: {missing} (looked in {_SECURITY})"


@pytest.mark.parametrize(("name", "number", "fields"), _rows(), ids=lambda v: str(v)[:40])
def test_every_row_has_the_four_documented_fields(name: str, number: int, fields: list[str]):
    """`<PluginID>\\t<THRESHOLD>\\t<Confidence>\\t<Note>` — tab-separated, as the header says.

    A row split by spaces instead of tabs is read by ZAP as a malformed entry and
    silently ignored, so the suppression would not apply and nobody would be told.
    """
    assert len(fields) == 4, f"{name}:{number} has {len(fields)} tab-separated fields, expected 4"
    assert fields[1] in {"OFF", "IGNORE", "WARN", "FAIL"}, f"{name}:{number} threshold={fields[1]!r}"
    assert fields[2] in {"LOW", "MEDIUM", "HIGH"}, f"{name}:{number} confidence={fields[2]!r}"


@pytest.mark.parametrize(("name", "number", "fields"), _rows(), ids=lambda v: str(v)[:40])
def test_every_ignore_carries_an_expiry_and_an_approver(name: str, number: int, fields: list[str]):
    """An IGNORE without a dated approval is a permanent hole with no owner."""
    if fields[1] != "IGNORE":
        pytest.skip("only IGNORE rows carry the expiry requirement")

    assert _EXPIRY.search(fields[3]), (
        f"{name}:{number} is an IGNORE with no "
        f'"# expires YYYY-MM-DD — approved by <role>" note. The header of '
        f"zap-rules.tsv requires one (NFR-015 §6.1)."
    )


@pytest.mark.parametrize(("name", "number", "fields"), _rows(), ids=lambda v: str(v)[:40])
def test_no_ignore_is_past_its_grace_period(name: str, number: int, fields: list[str]):
    """The arithmetic the header promises, actually performed.

    Past the expiry is a warning the reviewer should see; past expiry plus the
    grace period fails, because by then the suppression has outlived its evidence
    and nobody has looked.
    """
    if fields[1] != "IGNORE":
        pytest.skip("only IGNORE rows expire")

    match = _EXPIRY.search(fields[3])
    assert match, "covered by test_every_ignore_carries_an_expiry_and_an_approver"

    expiry = date.fromisoformat(match.group(1))
    overdue = (datetime.now(UTC).date() - expiry).days

    assert overdue <= _GRACE_DAYS, (
        f"{name}:{number} suppresses rule {fields[0]} and expired {overdue} days ago "
        f"({expiry}, approved by {match.group(2)}) — past the {_GRACE_DAYS}-day grace. "
        f"Re-verify the finding and either renew the note with a new date and approval "
        f"or remove the row. A suppression nobody has revisited hides the next real "
        f"finding behind the last false one."
    )


def test_the_row_scan_is_not_vacuous():
    """At least one row exists, or every parametrised check above is empty.

    Both files were empty until #1376/#1389 added the first suppression. If they
    return to empty this test fails and says so, rather than the file quietly
    becoming a no-op that still reports green.
    """
    rows = _rows()

    assert rows, (
        "no ZAP rule rows found. If every suppression was legitimately removed, delete "
        "this test with the same commit — an empty scan makes the checks above assert "
        "nothing while still passing."
    )
