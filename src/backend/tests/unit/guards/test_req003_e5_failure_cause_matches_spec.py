"""REQ-003 E5 declares the loss vocabulary and the cause-class pre-fill table the code implements (#2888 F-19).

``test_spec_literal_discriminators_match_models.py`` joins a spec ``Literal`` to a model field only under a
model heading and only when the literal sits on one line. E5 has neither: it declares ``termination_type``,
``termination_cause`` and ``failure_cause_class`` as prose bullets of ``PlantInstance`` and wraps the two
long literals over two lines — so the guard never saw them, and F-18 put ``bolting`` into the spec with
nothing comparing it to ``TerminationCause``.

This module pins E5 directly:

* the three literals of E5 name exactly the values of ``TerminationType``, ``TerminationCause`` and
  ``FailureCauseClass`` (a literal may span lines; HTML comments are prose and dropped first);
* the pre-fill table of E5 (research §5) is row for row the domain table ``FAILURE_CAUSE_TABLE``:
  the pre-fill, the classes the gardener may change to, and which rows carry the wilt follow-up.

The self-tests at the bottom run the same parsers over texts that disagree with the code, so a parser
that stops matching cannot turn this module vacuously green.
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

import pytest

from app.common.enums import FailureCauseClass, TerminationCause, TerminationType, WiltFollowUp
from app.domain.engines.failure_cause_engine import FailureCauseEngine, find_failure_cause_violations
from app.domain.models.failure_cause import FAILURE_CAUSE_TABLE, FailureCauseTable
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
assert _REPO_ROOT is not None
_REQ_003 = next((_REPO_ROOT / "spec" / "req").glob("REQ-003_*.md"))

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_SECTION = re.compile(r"^### E5\b.*?(?=^### )", re.S | re.M)
_LITERAL = re.compile(r"`([a-z_]+):\s*Literal\[(.*?)\]", re.S)
_QUOTED = re.compile(r"'([^']*)'")
_BACKTICKED = re.compile(r"`([a-z_]+)`")

#: The E5 field -> the enum it must equal.
_FIELDS: dict[str, type[StrEnum]] = {
    "termination_type": TerminationType,
    "termination_cause": TerminationCause,
    "failure_cause_class": FailureCauseClass,
}


def e5_section(text: str) -> str:
    match = _SECTION.search(_HTML_COMMENT.sub("", text))
    assert match is not None, "REQ-003 has no '### E5' section followed by another '###' heading"
    return match.group(0)


def e5_literals(section: str) -> dict[str, frozenset[str]]:
    """Every ``field: Literal[...]`` of the section; the literal may span lines."""
    return {field: frozenset(_QUOTED.findall(body)) for field, body in _LITERAL.findall(section)}


def e5_table(section: str) -> dict[str, tuple[str | None, frozenset[str], str]]:
    """Per cause of the pre-fill table: (pre-fill, every class it allows, wilt marker).

    The allowed classes are the pre-fill plus the "Nutzer kann ändern zu" column; ``jede Klasse`` stands for
    every class. The wilt marker is ``wilt_prone_family`` when the row binds the follow-up to
    "welkeanfälligen Familien", ``always`` when it names the "Welke-Rückfrage" otherwise, else ``never``.
    """
    rows: dict[str, tuple[str | None, frozenset[str], str]] = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[0].startswith("`") or cells[0].startswith("`termination_cause`"):  # noqa: PLR2004
            continue
        causes, prefill_cell, change_cell = cells
        prefill = next(iter(_BACKTICKED.findall(prefill_cell)), None)
        allowed = (
            {cls.value for cls in FailureCauseClass}
            if "jede Klasse" in change_cell
            else set(_BACKTICKED.findall(change_cell))
        )
        if prefill is not None:
            allowed.add(prefill)
        if "welkeanfällig" in change_cell:
            wilt = WiltFollowUp.WILT_PRONE_FAMILY.value
        elif "Welke-Rückfrage" in change_cell:
            wilt = WiltFollowUp.ALWAYS.value
        else:
            wilt = WiltFollowUp.NEVER.value
        for cause in _BACKTICKED.findall(causes):
            rows[cause] = (prefill, frozenset(allowed), wilt)
    return rows


def e5_empty_cause_row(section: str) -> tuple[str, str] | None:
    """The (pre-fill, change-to) cells of the table row for an empty cause (``leer …``), or ``None``."""
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0].startswith("leer"):  # noqa: PLR2004 - the table has three columns
            return cells[1], cells[2]
    return None


def empty_cause_row_says_what_holds(row: tuple[str, str] | None) -> bool:
    """The row exists, derives no class and accepts any class that is stated explicitly."""
    return row is not None and row[0].startswith("keine") and "jede Klasse" in row[1] and "`" not in row[0]


def table_as_spec(table: FailureCauseTable) -> dict[str, tuple[str | None, frozenset[str], str]]:
    """The domain table in the shape :func:`e5_table` reads the spec."""
    return {
        rule.termination_cause.value: (
            rule.prefill.value if rule.prefill is not None else None,
            frozenset(cls.value for cls in rule.choices),
            rule.wilt_follow_up.value,
        )
        for rule in table.rules
    }


@pytest.fixture(scope="module")
def section() -> str:
    return e5_section(_REQ_003.read_text(encoding="utf-8"))


class TestE5MatchesTheCode:
    def test_every_e5_literal_names_exactly_the_enum_values(self, section) -> None:
        literals = e5_literals(section)
        assert set(literals) >= set(_FIELDS), f"E5 lost a literal: found {sorted(literals)}"
        divergent = [
            f"{field}: spec {sorted(literals[field])} <-> {enum.__name__} {sorted(enum)} "
            f"(spec-only {sorted(literals[field] - set(enum))}, code-only {sorted(set(enum) - literals[field])})"
            for field, enum in _FIELDS.items()
            if literals[field] != frozenset(member.value for member in enum)
        ]
        assert not divergent, "REQ-003 E5 and the enums disagree:\n  " + "\n  ".join(divergent)

    def test_an_empty_cause_derives_no_class_and_accepts_a_stated_one(self, section) -> None:
        """v2.25: the empty-cause row says what the code does (bulk clear and legacy keep no class)."""
        assert empty_cause_row_says_what_holds(e5_empty_cause_row(section)), (
            "REQ-003 E5 lost the row 'leer (keine Ursache) | keine | jede Klasse, nur wenn ausdrücklich angegeben'"
        )
        record = FailureCauseEngine().resolve(
            termination_cause=None,
            failure_cause_class=None,
            failure_pathogen=None,
            failure_pathogen_confirmed=None,
            failure_pathogen_source=None,
        )
        assert record.failure_cause_class is None
        for cls in FailureCauseClass:
            assert not find_failure_cause_violations(
                termination_type=TerminationType.DIED,
                termination_cause=None,
                failure_cause_class=cls,
                failure_pathogen=None,
                failure_pathogen_confirmed=None,
                failure_pathogen_source=None,
            )

    def test_the_prefill_table_is_the_domain_table(self, section) -> None:
        spec = e5_table(section)
        code = table_as_spec(FAILURE_CAUSE_TABLE)
        assert set(spec) == set(code), f"causes: spec-only {set(spec) - set(code)}, code-only {set(code) - set(spec)}"
        divergent = [
            f"{cause}: spec {spec[cause]} <-> code {code[cause]}" for cause in code if spec[cause] != code[cause]
        ]
        assert not divergent, "REQ-003 E5 pre-fill table and FAILURE_CAUSE_TABLE disagree:\n  " + "\n  ".join(divergent)


_SPEC_SAMPLE = """
### E5 — Ungeplantes Absterben
- `termination_type: Literal['harvested','senesced','died','cancelled'] | None` — x
- `termination_cause: Literal['disease','pest','frost','heat','drought','waterlogging','neglect','mechanical',
  'bolting','unknown'] | None` — x
- `failure_cause_class: Literal['abiotic','pest_foliar','pest_soil','disease_soil','disease_foliar','mechanical',
  'unknown'] | None` — x

  | `termination_cause` | Vorbelegung `failure_cause_class` | Nutzer kann ändern zu |
  |---------------------|-----------------------------------|------------------------|
  | `frost`, `neglect` | `abiotic` | — |
  | `heat`, `drought`, `waterlogging` | `abiotic` | `disease_soil` (Welke-Rückfrage, REQ-053 §11.3a) |
  | `bolting` | `abiotic` | — |
  | `mechanical` | `mechanical` | — |
  | `pest` | keine — Pflichtauswahl | `pest_foliar` / `pest_soil` |
  | `disease` | keine — Pflichtauswahl | `disease_foliar` / `disease_soil` |
  | `unknown` | `unknown` | jede Klasse (Welke-Rückfrage bei welkeanfälligen Familien) |
  | leer (keine Ursache) | keine — es entsteht keine Klasse | jede Klasse, nur wenn ausdrücklich angegeben |

### E6 — next
"""


class TestTheParsersDiscriminate:
    """Falsification: the same parsers over texts that disagree with the code."""

    def test_the_sample_agrees_with_the_code(self) -> None:
        section = e5_section(_SPEC_SAMPLE)
        assert e5_literals(section)["termination_cause"] == frozenset(TerminationCause)
        assert e5_table(section) == table_as_spec(FAILURE_CAUSE_TABLE)

    def test_a_cause_missing_from_the_wrapped_literal_is_seen(self) -> None:
        section = e5_section(_SPEC_SAMPLE.replace("\n  'bolting','unknown']", "\n  'unknown']"))
        assert TerminationCause.BOLTING.value not in e5_literals(section)["termination_cause"]

    def test_an_enum_value_the_spec_lacks_is_seen(self) -> None:
        literal = e5_literals(e5_section(_SPEC_SAMPLE))["termination_cause"]
        assert literal != frozenset(TerminationCause) | {"lightning"}

    def test_the_old_unknown_or_empty_row_is_seen(self) -> None:
        old = _SPEC_SAMPLE.replace(
            "  | `unknown` | `unknown` | jede Klasse (Welke-Rückfrage bei welkeanfälligen Familien) |\n"
            "  | leer (keine Ursache) | keine — es entsteht keine Klasse "
            "| jede Klasse, nur wenn ausdrücklich angegeben |\n",
            "  | `unknown` / leer | `unknown` | jede Klasse (Welke-Rückfrage bei welkeanfälligen Familien) |\n",
        )
        assert old != _SPEC_SAMPLE
        assert not empty_cause_row_says_what_holds(e5_empty_cause_row(e5_section(old)))
        assert empty_cause_row_says_what_holds(e5_empty_cause_row(e5_section(_SPEC_SAMPLE)))

    def test_an_empty_row_that_derives_a_class_is_seen(self) -> None:
        drifted = _SPEC_SAMPLE.replace("| keine — es entsteht keine Klasse |", "| `unknown` |")
        assert not empty_cause_row_says_what_holds(e5_empty_cause_row(e5_section(drifted)))

    def test_a_changed_prefill_row_is_seen(self) -> None:
        drifted = _SPEC_SAMPLE.replace("| `bolting` | `abiotic` | — |", "| `bolting` | `unknown` | — |")
        assert e5_table(e5_section(drifted))["bolting"] != table_as_spec(FAILURE_CAUSE_TABLE)["bolting"]

    def test_a_lost_wilt_follow_up_is_seen(self) -> None:
        drifted = _SPEC_SAMPLE.replace("(Welke-Rückfrage, REQ-053 §11.3a)", "")
        assert e5_table(e5_section(drifted))["heat"][2] == WiltFollowUp.NEVER.value

    def test_a_commented_out_literal_declares_nothing(self) -> None:
        commented = _SPEC_SAMPLE.replace("- `termination_type", "<!-- - `termination_type").replace(
            "'cancelled'] | None` — x", "'cancelled'] | None` — x -->"
        )
        assert "termination_type" not in e5_literals(e5_section(commented))
