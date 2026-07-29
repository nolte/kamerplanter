"""Tests for the §12a gate (``scripts/check_utc_calendar_day.py``).

A gate nobody tests is a gate nobody can trust, and this one has exactly two
ways to fail silently: missing a real ``date.today()`` (the sweep of #858 has to
be repeated a fourth time) and flagging something that is not one (the check gets
switched off within a week, and then it guards nothing). Both directions are
pinned below.

**Why the tests live here.** ``scripts/`` carries no test suite of its own and
``pytest tests/unit/`` from ``src/backend`` is a PR-gating check, so the script
is loaded **by path** and exercised from the backend unit suite — the same
arrangement, for the same reason, as
``tests/unit/test_gherkin_line_classification.py``.

Traces to issue #858 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest


def _find_repo_root(start: Path) -> Path | None:
    """The checkout root: the ancestor holding both ``Taskfile.yaml`` and ``scripts/``."""
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and scripts/)",
        allow_module_level=True,
    )

_CHECK_PATH = _REPO_ROOT / "scripts" / "check_utc_calendar_day.py"
if not _CHECK_PATH.is_file():  # pragma: no cover — only in a partial checkout
    pytest.skip(f"{_CHECK_PATH} does not exist in this checkout", allow_module_level=True)

check = _load_module_by_path("_kamerplanter_utc_calendar_day_check", _CHECK_PATH)

_APP_ROOT = _REPO_ROOT / "src" / "backend" / "app"


def _scan(tmp_path: Path, source: str) -> list:
    """Write *source* as a module and return the call sites the check finds."""
    module = tmp_path / "sample.py"
    module.write_text(textwrap.dedent(source), encoding="utf-8")
    return check.scan_file(module)


class TestDetection:
    """Every spelling of ``datetime.date.today()`` this codebase can produce."""

    def test_plain_import(self, tmp_path: Path) -> None:
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            def f():
                return date.today()
            """,
        )

        assert [(s.line, s.expression) for s in sites] == [(5, "date.today()")]

    def test_aliased_import(self, tmp_path: Path) -> None:
        """``from datetime import date as _date`` — the calendar router's spelling.

        Both #858 sites in ``api/v1/calendar/tenant_router.py`` used this alias,
        so a checker blind to it would have reported the sweep complete while two
        call sites remained.
        """
        sites = _scan(
            tmp_path,
            """
            from datetime import date as _date

            year = _date.today().year
            """,
        )

        assert [s.expression for s in sites] == ["_date.today()"]

    def test_function_local_import(self, tmp_path: Path) -> None:
        """This codebase imports inside function bodies to break cycles."""
        sites = _scan(
            tmp_path,
            """
            def f():
                from datetime import date as _date

                return _date.today()
            """,
        )

        assert [s.line for s in sites] == [5]

    def test_module_attribute_access(self, tmp_path: Path) -> None:
        sites = _scan(
            tmp_path,
            """
            import datetime
            import datetime as dt

            a = datetime.date.today()
            b = dt.date.today()
            """,
        )

        assert [s.expression for s in sites] == ["datetime.date.today()", "dt.date.today()"]

    def test_several_sites_in_one_file_are_all_reported(self, tmp_path: Path) -> None:
        """``calendar_service`` held three; reporting only the first hides two."""
        sites = _scan(
            tmp_path,
            """
            from datetime import date, timedelta

            start = date.today() - timedelta(days=30)
            end = date.today() + timedelta(days=90)
            """,
        )

        assert [s.line for s in sites] == [4, 5]


class TestNonDetection:
    """What the check must stay quiet about, so it survives its first month."""

    def test_today_utc_is_not_a_finding(self, tmp_path: Path) -> None:
        assert (
            _scan(
                tmp_path,
                """
                from app.common.datetimes import today_utc

                value = today_utc()
                """,
            )
            == []
        )

    def test_an_unrelated_today_method_is_not_a_finding(self, tmp_path: Path) -> None:
        """``clock.today()`` is not ``datetime.date.today()``.

        Names are resolved through the module's imports, not matched by spelling,
        so an injected clock or a domain object with a ``today()`` method does not
        produce a false positive.
        """
        assert (
            _scan(
                tmp_path,
                """
                from datetime import date

                def f(clock, calendar):
                    return clock.today(), calendar.season.today(), date(2026, 1, 1)
                """,
            )
            == []
        )

    def test_datetime_class_today_is_out_of_scope(self, tmp_path: Path) -> None:
        """``datetime.today()`` (the class) is a naive *datetime*, not a day.

        It is a related hazard with a different fix (``now_utc()``), and §12a /
        #858 are scoped to the calendar day. Reporting it here would mean this
        check fails for a reason its own message does not explain.
        """
        assert (
            _scan(
                tmp_path,
                """
                from datetime import datetime

                value = datetime.today()
                """,
            )
            == []
        )

    def test_prose_mentioning_date_today_is_not_a_finding(self, tmp_path: Path) -> None:
        """The AST does not see comments — which is why it is an AST and not a grep.

        Four files in ``app/`` discuss ``date.today()`` in prose (including
        ``app/common/datetimes.py``, the helper's own docstring). A regex-based
        gate would fail permanently on the very documentation that explains it.
        """
        assert (
            _scan(
                tmp_path,
                '''
                """Never call date.today() here — use today_utc()."""

                # date.today() would drift by a day.
                value = 1
                ''',
            )
            == []
        )


class TestJustification:
    """The escape hatch: opt out in place, with a reason, or not at all."""

    def test_trailing_marker_exempts_the_site(self, tmp_path: Path) -> None:
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            stamp = date.today()  # local-clock: operator wall clock, never persisted
            """,
        )

        assert len(sites) == 1
        assert sites[0].justified
        assert sites[0].justification == "operator wall clock, never persisted"

    def test_marker_on_the_line_above_exempts_the_site(self, tmp_path: Path) -> None:
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            # local-clock: the log file name follows the operator's wall clock
            stamp = date.today()
            """,
        )

        assert sites[0].justified

    def test_a_bare_marker_is_not_an_exemption(self, tmp_path: Path) -> None:
        """Otherwise the hatch degenerates into a silencer.

        A reviewer cannot argue with a token; the reason is the whole point of
        preferring a per-site hatch over a numeric baseline.
        """
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            stamp = date.today()  # local-clock:
            """,
        )

        assert not sites[0].justified

    def test_a_too_short_reason_is_not_an_exemption(self, tmp_path: Path) -> None:
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            stamp = date.today()  # local-clock: ok
            """,
        )

        assert not sites[0].justified

    def test_a_marker_two_lines_up_does_not_reach(self, tmp_path: Path) -> None:
        """The marker binds to one call site, not to everything after it."""
        sites = _scan(
            tmp_path,
            """
            from datetime import date

            # local-clock: this reason belongs to the statement below it
            other = 1
            stamp = date.today()
            """,
        )

        assert not sites[0].justified


class TestExitCodes:
    """The contract the pre-commit hook and the ``static`` lane depend on."""

    def test_a_bare_call_fails_the_run(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (tmp_path / "sample.py").write_text("from datetime import date\nx = date.today()\n", encoding="utf-8")

        assert check.main(["--scan-root", str(tmp_path)]) == check.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "sample.py:2" in out
        # The message names the fix and the hatch, so neither needs a lookup.
        assert check.REPLACEMENT in out
        assert check.JUSTIFICATION_MARKER in out

    def test_a_justified_call_passes_and_is_reported(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Green, but never silent: an exemption stays visible in the log."""
        (tmp_path / "sample.py").write_text(
            "from datetime import date\nx = date.today()  # local-clock: operator wall clock only\n",
            encoding="utf-8",
        )

        assert check.main(["--scan-root", str(tmp_path)]) == check.EXIT_OK
        assert "operator wall clock only" in capsys.readouterr().out

    def test_a_missing_scan_root_is_a_usage_error(self, tmp_path: Path) -> None:
        """Distinct from a finding: a mis-wired hook must not read as 'clean'."""
        assert check.main(["--scan-root", str(tmp_path / "nope")]) == check.EXIT_USAGE

    def test_unparseable_source_is_a_usage_error(self, tmp_path: Path) -> None:
        (tmp_path / "broken.py").write_text("def (\n", encoding="utf-8")

        assert check.main(["--scan-root", str(tmp_path)]) == check.EXIT_USAGE

    def test_json_output_separates_the_two_buckets(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        import json

        (tmp_path / "sample.py").write_text(
            "from datetime import date\na = date.today()\nb = date.today()  # local-clock: operator wall clock only\n",
            encoding="utf-8",
        )

        assert check.main(["--scan-root", str(tmp_path), "--json"]) == check.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert payload["call_sites"] == 2
        assert [entry["line"] for entry in payload["unjustified"]] == [2]
        assert [entry["reason"] for entry in payload["justified"]] == ["operator wall clock only"]


class TestTheRealTree:
    """The gate against the tree it actually guards."""

    def test_the_backend_app_code_is_clean(self, capsys: pytest.CaptureFixture[str]) -> None:
        """#858's sweep, asserted rather than assumed.

        This is the test that turns the sweep into a standing property: it fails
        the moment a bare ``date.today()`` reappears anywhere under ``app/``,
        including in a file nobody thought to re-read.
        """
        assert check.main(["--scan-root", str(_APP_ROOT)]) == check.EXIT_OK, capsys.readouterr().out
