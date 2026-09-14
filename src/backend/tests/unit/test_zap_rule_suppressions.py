"""NFR-015 §6.1 — a ZAP suppression may not outlive its review, nor widen the scan.

`tests/security/zap-rules.tsv` states the first half in its own header:

    Every IGNORE row MUST include "# expires YYYY-MM-DD — approved by <role>"
    in the Note column. Expired IGNOREs trigger a CI warning; after 30 days
    of grace, they fail the build.

Nothing performed that arithmetic until #1376/#1389 — both files were empty, so
the convention had never been exercised, the #1042 shape.

The second half was found by the review of that change and is the sharper one.
Handing these files to `zap-api-scan.py` with `-c` — the obvious place for them —
makes that script swap its active scan policy::

    scan_policy = 'API-Minimal'
    if config_dict:
        scan_policy = 'Default Policy'
        zap.ascan.enable_all_scanners(scanpolicyname=scan_policy)

One suppression row would therefore have replaced a 23-rule minimal policy with
the full active rule set, under a 45-minute job timeout. So the files are read by
`scripts/security/zap_gate.py` alone, and `test_no_workflow_hands_these_files_to_zap`
keeps it that way.

This module checks the FILES. `test_zap_gate.py` checks what the gate does with
them. The validation itself is not reimplemented here — it calls `load_rules`, so
the format the guard enforces and the format the gate applies cannot drift apart.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SECURITY = _REPO_ROOT / "tests" / "security"
_RULE_FILES = ("zap-rules.tsv", "zap-api-rules.tsv")
_WORKFLOWS = (
    _REPO_ROOT / ".github" / "workflows" / "security-zap-postmerge.yml",
    _REPO_ROOT / ".github" / "workflows" / "security-zap-nightly.yml",
)

#: ZAP's own vocabulary, read off `zap_common.py` in the pinned image rather than
#: off the file header — an earlier header listed `OFF`, which is not a level and
#: makes `load_config` raise `Level OFF is not a supported level` before the scan
#: starts. `OUTOFSCOPE` is a fifth, differently-shaped row type this repository
#: does not use: it carries a regex instead of a note, so it cannot hold an expiry.
_THRESHOLDS = {"PASS", "IGNORE", "INFO", "WARN", "FAIL"}
_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}

_APPROVER = re.compile(r"#\s*expires\s+\d{4}-\d{2}-\d{2}\s+—\s+approved by\s+(\S+)")


def _load_gate() -> ModuleType:
    path = _REPO_ROOT / "scripts" / "security" / "zap_gate.py"
    spec = importlib.util.spec_from_file_location("_zap_gate_for_rules", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_zap_gate_for_rules"] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


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

    Both ZAP workflows name these paths on the `zap_gate.py --rules` command line,
    so a rename there without one here would leave this file agreeing with an
    empty list while the gate agreed with a missing file (`load_rules` returns no
    problems for a path that does not exist — deliberately, so a profile without a
    rule file is not an error, which is exactly why the existence check lives here).
    """
    missing = [name for name in _RULE_FILES if not (_SECURITY / name).is_file()]

    assert not missing, f"ZAP rule files not found: {missing} (looked in {_SECURITY})"


@pytest.mark.parametrize(("name", "number", "fields"), _rows(), ids=lambda v: str(v)[:40])
def test_every_row_has_the_four_documented_fields(name: str, number: int, fields: list[str]):
    """`<PluginID>\\t<THRESHOLD>\\t<Confidence>\\t<Note>` — tab-separated, as the header says.

    Spaces instead of tabs is not a silent no-op: `zap_common.load_config` raises
    `Unexpected number of tokens on line`. Loud — but the workflow swallows the
    wrapper's exit code (`|| echo …`), so the run limps on and dies later at the
    gate with "report does not exist", which names neither the file nor the line.
    """
    assert len(fields) == 4, f"{name}:{number} has {len(fields)} tab-separated fields, expected 4"
    assert fields[1] in _THRESHOLDS, (
        f"{name}:{number} threshold={fields[1]!r} is not one of {sorted(_THRESHOLDS)} — "
        f"ZAP's zap_conf_lvls, which rejects anything else with a ValueError."
    )
    assert fields[2] in _CONFIDENCE, f"{name}:{number} confidence={fields[2]!r}"


@pytest.mark.parametrize("name", _RULE_FILES)
def test_the_gate_accepts_every_row_in_the_shipped_file(name: str):
    """The production parser on the production file: no expiry past its grace, no
    missing scope, no unusable regex.

    Delegated rather than reimplemented, so a rule this guard is happy with is by
    construction a rule the gate will actually apply. The previous version of this
    file did its own arithmetic and disagreed with `zap_gate.py` about the grace
    period by 30 days.
    """
    path = _SECURITY / name

    _, problems, _ = gate.load_rules(path)

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(("name", "number", "fields"), _rows(), ids=lambda v: str(v)[:40])
def test_every_ignore_names_who_approved_it(name: str, number: int, fields: list[str]):
    """An IGNORE with no named approver is a hole nobody owns.

    The gate checks the date and the scope, because those change what it does. It
    does not check the approver, because that changes nothing at runtime — which
    is exactly why it needs a check of its own.
    """
    if len(fields) < 4 or fields[1] != "IGNORE":
        pytest.skip("only well-formed IGNORE rows carry the approval requirement")

    assert _APPROVER.search(fields[3]), (
        f'{name}:{number} is an IGNORE with no "# expires YYYY-MM-DD — approved by <role>" note (NFR-015 §6.1).'
    )


def test_no_workflow_hands_these_files_to_zap():
    """`-c` is the switch that widens the API scan; it must stay absent.

    Measured on `/zap/zap-api-scan.py` in the pinned image: a non-empty config
    file replaces the `API-Minimal` policy with `Default Policy` and calls
    `enable_all_scanners`. Rule 40018 stops running everywhere, every other active
    rule starts, and both happen as a side effect of adding one suppression line.
    """
    offenders = [
        f"{path.name}:{number}"
        for path in _WORKFLOWS
        if path.is_file()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"^\s*-c\s+zap-\S*rules\.tsv", line)
    ]

    assert not offenders, (
        f"ZAP is being handed a rule file at {offenders}. Suppression belongs to "
        f"zap_gate.py --rules: passing it to the scanner swaps the API scan's policy "
        f"for the full active rule set and can only express 'off everywhere'."
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
