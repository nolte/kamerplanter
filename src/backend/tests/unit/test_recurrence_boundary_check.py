"""Tests for the recurrence-boundary counter (``scripts/check_recurrence_boundary.py``).

**What is under test.** Two different things, kept apart on purpose:

*The detection logic*, driven against **constructed** trees written into
``tmp_path`` — never against the real ``src/backend/app``. A test asserting
"the tree holds eleven cadence advances" would go red on the next legitimate
refactor and teach nobody anything; what is worth pinning is what the scanner
does with a given input, in both directions.

*The ratchet*, which necessarily reads the real tree — that is what a ratchet
is for — but does so through a **named register** rather than a number.

**Red first, and the falsification asserts the same expression.** Every
"it stays quiet here" test has a partner that shows the same construct going red
when the one thing that excuses it is removed. A green test next to a rule that
is inert is this repository's most expensive recurring mistake; the only proof
against it is the negative control, on the *same* expression.

Traces to ADR-008 phase 0 and issue #1061, feature F-6 (no TC-ID: a source-tree
gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("check_recurrence_boundary")


def scan(source: str, name: str = "some_engine.py") -> list:
    """Scan one module's source text as if it were a file called *name*."""
    return checker.scan_source(Path(name), textwrap.dedent(source))


def kinds_at(sites: list) -> set[str]:
    """Every signal reported across *sites*."""
    return {kind for site in sites for kind in site.kinds}


# ── It can fail: the three signals, each on its own ──────────────────────────


class TestItCanFail:
    """A gate nobody has watched fail is a gate nobody knows works."""

    def test_a_cadence_operand_is_reported(self) -> None:
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, schedule):
                return last + timedelta(days=schedule.interval_days)
            """
        )
        assert len(sites) == 1
        assert sites[0].kinds == ("cadence_operand",)
        assert sites[0].function == "compute"
        assert not sites[0].justified

    def test_a_next_occurrence_binding_is_reported(self) -> None:
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, step):
                next_due = last + timedelta(days=step)
                return next_due
            """
        )
        assert kinds_at(sites) == {"occurrence_binding"}

    def test_a_next_occurrence_function_is_reported(self) -> None:
        sites = scan(
            """
            from datetime import timedelta

            def next_watering_date(base, step):
                return base + timedelta(days=step)
            """
        )
        assert kinds_at(sites) == {"occurrence_context"}

    def test_an_augmented_advance_is_reported(self) -> None:
        """``cursor += timedelta(...)`` is the loop form of the same defect."""
        sites = scan(
            """
            from datetime import timedelta

            def walk(start, schedule, end):
                cursor = start
                while cursor < end:
                    cursor += timedelta(days=schedule.interval_days)
                return cursor
            """
        )
        assert len(sites) == 1
        assert "cadence_operand" in sites[0].kinds

    def test_a_cadence_read_from_a_string_key_is_reported(self) -> None:
        """``config["interval_days"]`` says "interval" as loudly as an attribute does."""
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, config):
                return last + timedelta(days=config["interval_days"])
            """
        )
        assert kinds_at(sites) == {"cadence_operand"}


# ── What it must refuse to report ────────────────────────────────────────────


class TestTheQuietSide:
    """A counter that drowns the baseline in legitimate offsets is switched off."""

    def test_a_ttl_is_not_a_cadence(self) -> None:
        sites = scan(
            """
            from datetime import UTC, datetime, timedelta

            def issue_token(hours):
                expires_at = datetime.now(UTC) + timedelta(hours=hours)
                return expires_at
            """
        )
        assert sites == []

    def test_a_lookback_window_is_not_a_cadence(self) -> None:
        sites = scan(
            """
            from datetime import UTC, datetime, timedelta

            def purge(days):
                cutoff = datetime.now(UTC) - timedelta(days=days)
                return cutoff
            """
        )
        assert sites == []

    def test_a_template_offset_is_not_a_cadence(self) -> None:
        """A first-occurrence offset from a template repeats nothing.

        This is the shape the counting definition names outside the boundary, and
        the one ``task_service.instantiate_workflow`` carries. It is caught by the
        *binding* signal (``due_date``) — deliberately, so that it must be argued
        down at the site rather than silently dropped — and it is the reason the
        real tree carries seven written reasons.
        """
        sites = scan(
            """
            from datetime import timedelta

            def instantiate(now, template):
                due_date = now + timedelta(days=template.days_offset)
                return due_date
            """
        )
        assert kinds_at(sites) == {"occurrence_binding"}

    def test_a_duration_hidden_behind_a_name_is_not_seen(self) -> None:
        """A documented blind spot, pinned so nobody mistakes silence for absence.

        ``scripts/check_recurrence_boundary.py`` says the count is a floor rather
        than a census. This is what that costs, made concrete: the same cadence,
        spelled through a local, is invisible. If a later version learns to follow
        the binding, this test is the one that should change — loudly.
        """
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, schedule):
                step = timedelta(days=schedule.interval_days)
                return last + step
            """
        )
        assert sites == []


# ── The escape hatch, and its negative control ───────────────────────────────


_JUSTIFIED = """
from datetime import timedelta

def compute(last, schedule):
    # recurrence-owner-ok: this is a one-shot waiting period, nothing recurs
    return last + timedelta(days=schedule.interval_days)
"""

_TRAILING = """
from datetime import timedelta

def compute(last, schedule):
    return last + timedelta(days=schedule.interval_days)  # recurrence-owner-ok: nothing recurs here at all
"""

_BARE_MARKER = """
from datetime import timedelta

def compute(last, schedule):
    # recurrence-owner-ok: no
    return last + timedelta(days=schedule.interval_days)
"""


class TestTheEscapeHatch:
    """A site may stand by carrying a reason — and only by carrying one."""

    def test_a_reason_above_the_site_excuses_it(self) -> None:
        sites = scan(_JUSTIFIED)
        assert len(sites) == 1
        assert sites[0].justified
        assert sites[0].justification == "this is a one-shot waiting period, nothing recurs"

    def test_a_trailing_reason_excuses_it_too(self) -> None:
        sites = scan(_TRAILING)
        assert len(sites) == 1 and sites[0].justified

    def test_removing_the_reason_makes_the_same_site_red_again(self) -> None:
        """The negative control, on the same expression the positive test used.

        Not "a similar site is red" — *this* site, with one line deleted. That is
        the only form that proves the reason is what turned it green.
        """
        without = _JUSTIFIED.replace(
            "    # recurrence-owner-ok: this is a one-shot waiting period, nothing recurs\n", ""
        )
        assert without != _JUSTIFIED
        sites = scan(without)
        assert len(sites) == 1
        assert not sites[0].justified

    def test_a_bare_marker_is_not_an_exemption(self) -> None:
        """`no` is not a reason. A hatch that opens on a keystroke is a silencer."""
        sites = scan(_BARE_MARKER)
        assert len(sites) == 1
        assert not sites[0].justified

    def test_a_multi_line_reason_is_reported_whole(self) -> None:
        """A register showing only the first clause is one a reviewer cannot judge."""
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, schedule):
                # recurrence-owner-ok: a Karenz period is a one-shot waiting time,
                # not a cadence — nothing recurs here.
                return last + timedelta(days=schedule.interval_days)
            """
        )
        assert sites[0].justification == (
            "a Karenz period is a one-shot waiting time, not a cadence — nothing recurs here."
        )


class TestTheRegisterCannotOutliveItsDebt:
    """A pardon left behind after the fix pardons nothing, and must go."""

    def test_a_reason_with_no_site_under_it_is_a_finding(self) -> None:
        sites = scan(
            """
            from datetime import timedelta

            def compute(last, schedule):
                # recurrence-owner-ok: this used to be a cadence advance, and is not any more
                return schedule.next_run
            """
        )
        assert len(sites) == 1
        assert sites[0].kinds == ("stale_justification",)
        assert not sites[0].justified

    def test_a_reason_that_still_covers_a_site_is_not_stale(self) -> None:
        """The negative control: the same marker, with the code still under it."""
        sites = scan(_JUSTIFIED)
        assert [site.kinds for site in sites] == [("cadence_operand",)]


# ── The tree contract ────────────────────────────────────────────────────────


class TestTheTreeContract:
    """Discovery, owner exclusion, exit codes and the machine-readable shape."""

    def _tree(self, root: Path, files: dict[str, str]) -> Path:
        for relative, source in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(source), encoding="utf-8")
        return root

    def test_the_owner_module_is_not_counted_against_itself(self, tmp_path: Path) -> None:
        root = self._tree(
            tmp_path,
            {
                "domain/engines/recurrence_engine.py": """
                    from datetime import timedelta

                    def next_occurrence(base, schedule):
                        return base + timedelta(days=schedule.interval_days)
                """,
                "domain/services/other.py": """
                    from datetime import timedelta

                    def next_occurrence(base, schedule):
                        return base + timedelta(days=schedule.interval_days)
                """,
            },
        )
        sites = checker.collect(root)
        assert [site.relative().endswith("other.py") for site in sites] == [True]

    def test_an_empty_scan_root_is_a_usage_error_not_a_green(self, tmp_path: Path) -> None:
        """A scan that measured nothing must not look like a scan that found nothing."""
        (tmp_path / "empty").mkdir()
        assert checker.main(["--scan-root", str(tmp_path / "empty")]) == checker.EXIT_USAGE

    def test_gate_mode_is_red_and_inventory_mode_is_not(self, tmp_path: Path) -> None:
        root = self._tree(
            tmp_path,
            {
                "engine.py": """
                    from datetime import timedelta

                    def compute(last, schedule):
                        return last + timedelta(days=schedule.interval_days)
                """
            },
        )
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_DEFECTS
        assert checker.main(["--scan-root", str(root), "--inventory"]) == checker.EXIT_OK

    def test_json_reports_counts_and_site_attribution(self, tmp_path: Path, capsys) -> None:  # noqa: ANN001
        root = self._tree(
            tmp_path,
            {
                "engine.py": """
                    from datetime import timedelta

                    def compute(last, schedule):
                        # recurrence-owner-ok: a one-shot waiting period, nothing recurs
                        first = last + timedelta(days=schedule.interval_days)
                        return first + timedelta(days=schedule.interval_days)
                """
            },
        )
        assert checker.main(["--scan-root", str(root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert payload["total"] == 2
        assert payload["open"] == 1
        assert payload["justified"] == 1
        assert all(site["file"] and site["line"] for site in payload["sites"])


# ── The ratchet, against the real tree ───────────────────────────────────────


#: Every cadence advance the backend still computes outside ``RecurrenceEngine``,
#: keyed by ``file::function::signals`` and carrying how many sit in that function.
#:
#: **This is the phase-0 (a) baseline of ADR-008.** It is a *register*, not a
#: number: phases 1–2 empty it entry by entry, and each entry says what has to
#: move. Two properties matter and neither is negotiable:
#:
#: * A cadence advance that is **not** in here fails the test — that is the
#:   ratchet. New scheduling code goes through the engine or it does not land.
#: * An entry whose site is **gone** fails the test too. A register that can
#:   outlive its debt stops being evidence of anything; the same rule
#:   ``_KNOWN_OPEN`` in ``tests/unit/migrations/test_substrate_invariants.py``
#:   applies to seed data.
#:
#: The second property is a deliberate, narrow departure from NFR-018 §2.1's
#: "a drop is green, never a failure". The cost that rule guards against is a
#: *shared line*: two pull requests that both clean up collide on one integer, so
#: cleaning up is punished. A per-site register has no shared line — removing
#: your own entry touches only your own three lines, in the same change that
#: removed the code — and it buys the property an integer cannot have: the record
#: cannot quietly go stale. The number itself is still computed on every run and
#: is written down nowhere.
_KNOWN_OPEN: dict[str, tuple[int, str]] = {
    "src/backend/app/domain/engines/care_reminder_engine.py::calculate_due_date::cadence_operand+occurrence_context": (
        2,
        "The care path's own next-due arithmetic: base + snooze_days and base + interval. "
        "ADR-008 boundary 2 keeps the interval decision here; boundary 1 moves the date. "
        "Phase 1 turns both into RecurrenceEngine.fixed_interval_rule + next_occurrence — "
        "the snooze becomes a re-seeded rule (F-7).",
    ),
    "src/backend/app/domain/engines/inspection_scheduler.py::next_inspection_date::"
    "cadence_operand+occurrence_context": (
        1,
        "IPM inspection cadence (REQ-010): BASE_INTERVAL_DAYS scaled by phase and pressure. "
        "The scaling is interval authority and stays; the date is the engine's.",
    ),
    "src/backend/app/domain/engines/succession_plan_engine.py::generate_batch_run::cadence_operand": (
        1,
        "Succession sowing (REQ-028 Sukzession): batch n starts (n-1) * interval_days after the "
        "plan. ADR-008 names the Sukzessionssatz explicitly as a path that must express its "
        "cadence as a rule.",
    ),
    "src/backend/app/domain/engines/tank_engine.py::calculate_next_maintenance::"
    "cadence_operand+occurrence_binding+occurrence_context": (
        1,
        "Tank maintenance cadence (REQ-014). Duplicated verbatim in "
        "tasks/tank_maintenance_tasks.py — the two entries below are the same rule in a "
        "second place, which is the ADR's whole argument in one file pair.",
    ),
    "src/backend/app/domain/engines/watering_forecast_engine.py::generate_forecast::cadence_operand": (
        1,
        "Adaptive watering projection: re-reads the interval per step and walks forward. A "
        "projection is still an answer to 'when is the next time', so boundary 1 covers it.",
    ),
    "src/backend/app/domain/engines/watering_schedule_engine.py::get_next_watering_dates::occurrence_context": (
        1,
        "WEEKDAYS mode enumerates a weekly cadence by walking days and testing weekday() — a "
        "BYDAY rule written out by hand.",
    ),
    "src/backend/app/domain/engines/watering_schedule_engine.py::get_next_watering_dates::"
    "occurrence_binding+occurrence_context": (
        1,
        "INTERVAL mode aligns the first occurrence onto the cadence grid via a modulo.",
    ),
    "src/backend/app/domain/engines/watering_schedule_engine.py::get_next_watering_dates::"
    "cadence_operand+occurrence_binding+occurrence_context": (
        1,
        "INTERVAL mode's advance step itself.",
    ),
    "src/backend/app/tasks/tank_maintenance_tasks.py::generate_tank_maintenance_tasks::"
    "cadence_operand+occurrence_binding": (
        2,
        "The Celery job recomputes tank_engine.calculate_next_maintenance twice in one function "
        "rather than calling it — the same cadence in a third and fourth place.",
    ),
}


def _real_tree_sites() -> list:
    root = find_repo_root(Path(__file__).resolve())
    if root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip("checkout root not found")
    return [site for site in checker.collect(root / checker.DEFAULT_SCAN_ROOT) if not site.justified]


class TestTheRatchet:
    """The ADR-008 phase-0 (a) baseline, as a register that must shrink to nothing."""

    def test_no_cadence_advance_arrives_outside_the_register(self) -> None:
        counted: dict[str, int] = {}
        for site in _real_tree_sites():
            counted[site.identity()] = counted.get(site.identity(), 0) + 1

        arrived = {
            identity: count for identity, count in counted.items() if count > _KNOWN_OPEN.get(identity, (0, ""))[0]
        }
        assert not arrived, (
            "New cadence advance(s) outside RecurrenceEngine (ADR-008 boundary 1): "
            + "; ".join(f"{identity} (now {count})" for identity, count in sorted(arrived.items()))
            + ". Express the cadence as an RRULE and advance it with "
            "RecurrenceEngine.next_occurrence, or write a '# recurrence-owner-ok: <reason>' "
            "at the site saying why nothing there recurs. Run "
            "`task check:recurrence-boundary -- --inventory` to see the full picture."
        )

    def test_a_healed_entry_must_leave_the_register(self) -> None:
        counted: dict[str, int] = {}
        for site in _real_tree_sites():
            counted[site.identity()] = counted.get(site.identity(), 0) + 1

        healed = {
            identity: (registered, counted.get(identity, 0))
            for identity, (registered, _) in _KNOWN_OPEN.items()
            if counted.get(identity, 0) < registered
        }
        assert not healed, (
            "These entries no longer describe the tree and must be removed from _KNOWN_OPEN "
            "(or their count lowered): "
            + "; ".join(
                f"{identity} (registered {was}, found {now})" for identity, (was, now) in sorted(healed.items())
            )
            + ". A register that outlives its debt stops being evidence of anything."
        )

    def test_the_register_retires_itself_when_the_debt_is_gone(self) -> None:
        """The obsolescence rule ADR-008 phase 1 exits on.

        When the register empties, this whole class is dead mechanism dressed as
        policy: the honest successor is the scanner itself, wired into the
        required ``static`` lane at zero threshold (F-10), where it also catches
        the case this register cannot — a cadence advance added and removed
        between two runs.
        """
        assert _KNOWN_OPEN, (
            "The phase-0 (a) baseline is empty: no cadence advance outside RecurrenceEngine "
            "remains. Delete this register and its two tests above, and wire "
            "scripts/check_recurrence_boundary.py into .pre-commit-config.yaml as a hook in "
            "the required `static` lane (ADR-008 phase 4 / feature F-10). Leaving an empty "
            "register in place would be a gate that can no longer fail."
        )
