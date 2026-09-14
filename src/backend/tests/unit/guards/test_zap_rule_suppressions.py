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
#: DISCOVERED, not listed. A hard-coded pair passes over nothing the moment a
#: workflow is renamed or a third ZAP lane is added, and a scan over an empty list
#: reports green — the vacuity the row scan already has a control for.
_WORKFLOWS = sorted((_REPO_ROOT / ".github" / "workflows").glob("*zap*.yml"))

#: ZAP's own vocabulary, read off `zap_common.py` in the pinned image rather than
#: off the file header — an earlier header listed `OFF`, which is not a level at
#: all. This is the STRUCTURAL check: a row outside this set is malformed by any
#: reading. Whether a well-formed non-IGNORE row is HONOURED is a separate and
#: stricter question, and `load_rules` answers it with a rejection — see
#: test_zap_gate.py::test_a_threshold_other_than_ignore_is_rejected_rather_than_ignored.
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

    Tabs and spaces are indistinguishable in a diff, and a space-separated row
    parses to one field. `load_rules` now reports that itself, so this is the
    second of two checks — kept because it names the file and the line before
    anything runs, and because it also pins the confidence column, which the gate
    does not read. (An earlier version of this docstring justified the check by
    what `zap_common.load_config` raises. That was true of ZAP's parser, and ZAP
    no longer reads these files at all.)
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


#: The ZAP wrapper scripts whose invocations must carry no config option.
_ZAP_WRAPPERS = re.compile(r"zap-(baseline|api-scan|full-scan)\.py")

#: Every spelling that populates ZAP's `config_dict`: `-c <file>` and `-u <url>`,
#: plus their long forms. The first version of this guard matched only
#: `^\s*-c\s+zap-\S*rules\.tsv` — anchored at line start, and requiring the
#: argument to begin with `zap-`. Four ways past it were demonstrated in review:
#: reflowing the invocation onto one line, staging the file under another name,
#: quoting the argument, and using `-u` instead. A guard that a rename walks
#: around is the failure mode this repository keeps paying for, so the match is
#: on the OPTION, anywhere in the logical command line.
_CONFIG_OPTION = re.compile(r"(?:^|\s)(-c|-u|--config|--config-url)(?:[=\s]|$)")

#: The FIFTH spelling, and the one NFR-015 §4 used to prescribe: the `zaproxy/action-*`
#: wrappers take the same file as `rules_file_name:` and hand it to the same
#: `zap-api-scan.py` as `-c`. The key names no script, so the patterns above cannot
#: see it, and `rules_file_name` has no meaning other than that config — so it is
#: refused outright.
_ACTION_RULES_FILE = re.compile(r"rules_file_name\s*:")

#: `cmd_options:` is the action's raw-flag passthrough and reaches the same place,
#: but it is ALSO where `-a -j -T 15` legitimately lives. Judging the key alone
#: would reject a valid step and teach the next reader to work around the guard,
#: so the value is what is read — with `_CONFIG_OPTION`, the same predicate as on
#: a `docker run` line.
_ACTION_CMD_OPTIONS = re.compile(r"cmd_options\s*:")


def _logical_lines(text: str) -> list[tuple[int, str]]:
    """Join shell backslash-continuations, so one invocation is one line.

    Returns `(line number of the first physical line, joined text)`.
    """
    joined: list[tuple[int, str]] = []
    buffer = ""
    start = 0
    for number, physical in enumerate(text.splitlines(), 1):
        if not buffer:
            start = number
        stripped = physical.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        joined.append((start, buffer + stripped))
        buffer = ""
    if buffer:
        joined.append((start, buffer))
    return joined


def test_no_workflow_hands_a_config_to_zap():
    """`-c` / `-u` is the switch that widens the API scan; it must stay absent.

    Measured on `/zap/zap-api-scan.py` in the pinned image: a non-empty
    `config_dict` replaces the `API-Minimal` policy with `Default Policy` and calls
    `enable_all_scanners`. Rule 40018 stops running everywhere, every other active
    rule starts, and both happen as a side effect of adding one suppression line.
    """
    offenders = []
    for path in _WORKFLOWS:
        for number, command in _logical_lines(path.read_text(encoding="utf-8")):
            if command.lstrip().startswith("#"):
                continue  # a shell comment inside a `run:` block, e.g. the one saying why
            handed_on_a_command_line = _ZAP_WRAPPERS.search(command) and _CONFIG_OPTION.search(command)
            handed_through_the_action = _ACTION_RULES_FILE.search(command) or (
                _ACTION_CMD_OPTIONS.search(command) and _CONFIG_OPTION.search(command)
            )
            if handed_on_a_command_line or handed_through_the_action:
                offenders.append(f"{path.name}:{number}")

    assert not offenders, (
        f"ZAP is being handed a config at {offenders}. Suppression belongs to "
        f"zap_gate.py --rules: giving it to the scanner swaps the API scan's policy "
        f"for the full active rule set and can only express 'off everywhere'."
    )


def test_the_workflow_scan_covers_the_zap_workflows_that_exist():
    """The control for the scan above, which is otherwise green over an empty list.

    Discovery is by glob, so this asserts the glob still finds the lanes rather
    than that two names still resolve — a rename is then covered automatically and
    a third ZAP workflow is picked up without anyone remembering.
    """
    names = {path.name for path in _WORKFLOWS}

    assert {"security-zap-postmerge.yml", "security-zap-nightly.yml"} <= names, (
        f"the ZAP workflow glob found {sorted(names)}. If a lane was renamed, the "
        f"guard above is now scanning fewer files than it thinks."
    )


def test_this_guard_would_see_a_config_option_it_is_looking_for():
    """The guard's own control, because the guard is a text match.

    Its predecessor passed on four real spellings of the thing it forbids. A
    pattern that matches nothing looks exactly like a workflow that is clean, so
    the shapes are asserted directly rather than trusted.
    """
    evasions = [
        "            zap-api-scan.py -t openapi.json -c zap-api-rules.tsv",
        "              -c zapwork/staged-rules.tsv \\\n              -J api-report.json",
        '              -c "zap-api-rules.tsv"',
        "              -u https://example.invalid/rules.conf",
        "              --config=rules.tsv",
    ]
    prefix = "            zap-full-scan.py \\\n"

    for evasion in evasions:
        text = prefix + evasion if not _ZAP_WRAPPERS.search(evasion) else evasion
        hits = [
            command
            for _, command in _logical_lines(text)
            if _ZAP_WRAPPERS.search(command) and _CONFIG_OPTION.search(command)
        ]
        assert hits, f"the guard does not see {evasion!r}"

    # The action form names no script at all, so it needs its own pattern — and
    # this is the shape NFR-015 §4 prescribed until this change.
    def _caught(line: str) -> bool:
        return bool(
            _ACTION_RULES_FILE.search(line) or (_ACTION_CMD_OPTIONS.search(line) and _CONFIG_OPTION.search(line))
        )

    assert _caught('          rules_file_name: "tests/security/zap-api-rules.tsv"')
    assert _caught('          cmd_options: "-a -c zap-api-rules.tsv"')

    # And the negative half, which is why the key alone is not the test: a guard
    # that rejects every `cmd_options:` would reject the flags §4 legitimately
    # passes, and a guard people route around stops guarding.
    assert not _caught('          cmd_options: "-a -j -m 5 -T 15"')


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
