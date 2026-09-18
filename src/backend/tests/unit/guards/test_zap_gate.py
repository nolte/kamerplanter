"""NFR-015 §5.1/§5.2/§6.1 — the ZAP verdict, and the suppressions it honours.

`scripts/security/zap_gate.py` owns what "blocking" means: the severity matrix,
the confidence filter, and — since #1376/#1389 — the rule-file suppressions.

That last part moved here for a measured reason. Handing the rule file to
`zap-api-scan.py` with `-c` looks like the obvious place for it, but that script
picks its active scan policy from whether the config produced any entries::

    scan_policy = 'API-Minimal'
    if config_dict:
        scan_policy = 'Default Policy'
        zap.ascan.enable_all_scanners(scanpolicyname=scan_policy)

So the first suppression would swap a 23-rule minimal policy for the full active
rule set, and the only shape ZAP can express is "turn this rule off everywhere".
The gate drops matching *instances* instead: rule 40018 keeps running, and a
finding at any other URL still blocks. `test_a_finding_at_another_url_still_blocks`
is the test that says so, and it is the one that would go red if the suppression
ever widened back into a rule-wide off switch.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_GATE = _REPO_ROOT / "scripts" / "security" / "zap_gate.py"

_CONFIRM = "http://backend:8000/api/v1/privacy/email-change/confirm"
_ELSEWHERE = "http://backend:8000/api/v1/plants/search"


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_zap_gate_under_test", _GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_zap_gate_under_test"] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _report(*uris: str, pluginid: str = "40018", riskcode: str = "3") -> dict:
    """A ZAP JSON report carrying one alert over *uris*.

    The shape is copied from the real `api-report.json` of run 34504023147, not
    invented: `riskcode` and `confidence` are strings there, and the URL lives in
    `instances[].uri`.
    """
    return {
        "site": [
            {
                "@name": "http://backend:8000",
                "alerts": [
                    {
                        "pluginid": pluginid,
                        "alert": "SQL Injection",
                        "riskcode": riskcode,
                        "confidence": "2",
                        "instances": [{"uri": uri, "method": "POST", "param": "token"} for uri in uris],
                    }
                ],
            }
        ]
    }


def _rules(tmp_path: Path, note: str, *, plugin: str = "40018") -> Path:
    path = tmp_path / "rules.tsv"
    path.write_text(
        "# a comment row\n\n" + "\t".join([plugin, "IGNORE", "MEDIUM", note]) + "\n",
        encoding="utf-8",
    )
    return path


def _valid_note(
    *,
    expires: date | None = None,
    scope: str | None = _CONFIRM,
    approved: date | None = None,
) -> str:
    """A note in the documented form.

    The approval date is part of it: the span between approval and expiry is what
    bounds a suppression's life, and deriving that from `date.today()` would make
    the check a function of when it runs.
    """
    expires = expires or (date.today() + timedelta(days=180))
    approved = approved or (expires - timedelta(days=180))
    parts = [f"# expires {expires.isoformat()} — approved by operator ({approved.isoformat()})."]
    if scope is not None:
        parts.append(f"scope={scope}")
    parts.append("Measured false positive.")
    return " ".join(parts)


def _run(tmp_path: Path, report: dict, rules: Path | None, monkeypatch) -> tuple[int, Path]:
    """Drive `main()` the way the workflow does, and return (exit code, verdict)."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    emit = tmp_path / "blocking.json"

    argv = ["zap_gate.py", str(report_path), "--profile", "api", "--emit-blocking", str(emit)]
    if rules is not None:
        argv += ["--rules", str(rules)]
    monkeypatch.setattr(sys, "argv", argv)

    return gate.main(), emit


class TestSuppressionScope:
    def test_a_scoped_suppression_clears_the_finding_it_names(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, _valid_note())

        code, emit = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 0
        assert json.loads(emit.read_text()) == []

    def test_a_finding_at_another_url_still_blocks(self, tmp_path, monkeypatch):
        """The property the whole design exists for.

        ZAP's own IGNORE turns the rule off for the entire target. If this gate
        ever grows that behaviour, 40018 at an endpoint nobody has looked at
        would pass silently — and this test is the only thing that says no.
        """
        rules = _rules(tmp_path, _valid_note())

        code, emit = _run(tmp_path, _report(_ELSEWHERE), rules, monkeypatch)

        assert code == 1
        assert [f["plugin"] for f in json.loads(emit.read_text())] == ["40018"]

    def test_an_alert_keeps_blocking_while_one_instance_survives(self, tmp_path, monkeypatch):
        """One ZAP alert carries every URL the rule fired on.

        Suppressing the alert rather than the instance would take the unexamined
        URL with it — the same hole as a rule-wide off switch, reached by a
        different route.
        """
        rules = _rules(tmp_path, _valid_note())

        code, emit = _run(tmp_path, _report(_CONFIRM, _ELSEWHERE), rules, monkeypatch)

        assert code == 1
        [finding] = json.loads(emit.read_text())
        assert [i["uri"] for i in finding["instances"]] == [_ELSEWHERE]

    def test_a_suppression_for_another_rule_does_not_apply(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, _valid_note(), plugin="90019")

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_no_rules_file_at_all_leaves_the_verdict_untouched(self, tmp_path, monkeypatch):
        """The control: without a suppression the report under test IS blocking.

        Every assertion above that expects a 0 would also pass if the report were
        harmless to begin with.
        """
        code, _ = _run(tmp_path, _report(_CONFIRM), None, monkeypatch)

        assert code == 1


class TestSuppressionValidity:
    """A row the gate cannot fully validate is reported AND stops applying.

    Both halves matter: a malformed suppression must not quietly widen, and it
    must not quietly go inert either.
    """

    def test_an_ignore_without_an_expiry_does_not_apply(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, "# approved by operator. scope=.* No date.")

        code, emit = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1
        assert json.loads(emit.read_text()), "the finding it was hiding must reappear"

    def test_a_note_with_two_scopes_does_not_apply(self, tmp_path, monkeypatch):
        """The first `scope=` in the prose wins, so two of them is ambiguous.

        Measured hazard rather than a hypothetical: the header, the README and
        NFR-015 §6.1 all tell an author to write `scope=.*` for the rule-wide case,
        so a note explaining itself — "rule-wide would be scope=.* but here
        scope=/api/… only" — parsed to the rule-wide off switch this design exists
        to prevent.
        """
        note = (
            f"# expires {(date.today() + timedelta(days=90)).isoformat()} — approved by "
            f"operator ({date.today().isoformat()}). Rule-wide would be scope=.* but here "
            f"scope={_CONFIRM} only."
        )
        rules = _rules(tmp_path, note)

        code, _ = _run(tmp_path, _report(_ELSEWHERE), rules, monkeypatch)

        assert code == 1, "the ambiguous note must not silence anything"

    def test_an_ignore_without_an_approval_date_does_not_apply(self, tmp_path, monkeypatch):
        """`approved by operator` with no date leaves the span uncheckable."""
        note = f"# expires 2099-01-01 — approved by operator. scope={_CONFIRM}"
        rules = _rules(tmp_path, note)

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_a_suppression_longer_than_a_year_does_not_apply(self, tmp_path, monkeypatch):
        """`tests/security/README.md` caps a suppression at twelve months.

        Checked against the row's OWN two dates, not the clock, so it means the same
        in the required lane as in the ZAP lane and cannot become a dated landmine:
        a row that satisfies it today satisfies it forever.
        """
        approved = date(2026, 1, 1)
        rules = _rules(tmp_path, _valid_note(expires=date(2030, 1, 1), approved=approved))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_a_suppression_expiring_before_its_approval_does_not_apply(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, _valid_note(expires=date(2026, 1, 1), approved=date(2026, 6, 1)))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_a_year_to_the_day_is_still_inside_the_cap(self, tmp_path, monkeypatch):
        """The boundary, because 365 vs 366 decides whether a leap year is a violation."""
        approved = date(2026, 3, 1)
        rules = _rules(tmp_path, _valid_note(expires=approved + timedelta(days=365), approved=approved))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 0

    def test_an_ignore_without_a_scope_does_not_apply(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, _valid_note(scope=None))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_an_unusable_scope_regex_does_not_apply(self, tmp_path, monkeypatch):
        rules = _rules(tmp_path, _valid_note(scope="(unclosed"))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1

    def test_an_expiry_inside_the_grace_still_applies_and_warns(self, tmp_path, monkeypatch, capsys):
        """The countdown is asserted as a literal, and the literal is derived here.

        The row fails once `overdue > GRACE_DAYS`, so the first failing day is
        `overdue == 31`. Expiring yesterday is `overdue == 1`, which leaves 30 days.
        Computing the expected value with the same expression the gate uses would
        have reproduced the off-by-one this assertion was written to pin down: the
        first version said 29, matching a message that counted one day short.
        """
        yesterday = date.today() - timedelta(days=1)
        rules = _rules(tmp_path, _valid_note(expires=yesterday))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 0, "inside the grace the suppression still holds"
        assert "fails the build in 30 day(s)" in capsys.readouterr().out

    def test_the_last_day_of_the_grace_counts_one(self, tmp_path, monkeypatch, capsys):
        """`overdue == GRACE_DAYS` is the final day it applies, so the message is 1."""
        edge = date.today() - timedelta(days=gate.GRACE_DAYS)
        rules = _rules(tmp_path, _valid_note(expires=edge))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 0
        assert "fails the build in 1 day(s)" in capsys.readouterr().out

    def test_an_impossible_date_is_reported_and_does_not_kill_the_run(self, tmp_path, monkeypatch):
        """`# expires 2026-02-30` has the right shape and no such day.

        Unguarded, `date.fromisoformat` raised before a single alert was read —
        and because the verdict file is written at the end, the profile produced
        none. The issue-opening step reads a missing file as "this profile did not
        run", sees the other one, and reports no blocking findings for a scan that
        was never judged.
        """
        # The approval date is part of the note for a reason that bit this very
        # test: without it `load_rules` rejects the row at the approval check and
        # `continue`s, so the `try/except ValueError` this test exists to pin down
        # was never reached — deleting that except clause left the test green.
        rules = _rules(tmp_path, "# expires 2026-02-30 — approved by operator (2026-01-01). scope=.*")

        code, emit = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1
        assert emit.is_file(), "a bad rule row must not cost the verdict file"
        assert [f["plugin"] for f in json.loads(emit.read_text())] == ["40018"]

    def test_a_threshold_other_than_ignore_is_rejected_rather_than_ignored(self, tmp_path, monkeypatch):
        """WARN/FAIL/INFO/PASS are ZAP's vocabulary and this gate implements none.

        Since ZAP no longer reads these files, such a row changes nothing. NFR-015
        §6.1 ships `40012 WARN HIGH` as an example, so someone will write one and
        expect reflected XSS to start blocking. Silence would be the worst answer.
        """
        path = tmp_path / "rules.tsv"
        path.write_text("40012\tWARN\tHIGH\tReflected XSS — triage in the issue\n", encoding="utf-8")

        _, problems, _ = gate.load_rules(path)

        assert problems and "not honoured" in problems[0]

    def test_a_row_split_by_spaces_is_reported_rather_than_skipped(self, tmp_path):
        """Tabs and spaces look identical in a diff, and the row parses to one field.

        The parser used to `continue` past it without a word, so the suppression
        did not apply and nobody was told — the same silence this file exists to
        prevent, reached through the parser instead of through the scanner.
        """
        path = tmp_path / "rules.tsv"
        path.write_text("40018 IGNORE MEDIUM # expires 2099-01-01 — approved by x scope=.*\n", encoding="utf-8")

        _, problems, _ = gate.load_rules(path)

        assert problems and "tab-separated" in problems[0]

    def test_an_expiry_past_the_grace_fails_and_stops_applying(self, tmp_path, monkeypatch):
        """Past the grace, the finding comes back in the same run that goes red.

        Failing while still suppressing would tell a reader the build is broken
        without showing what the lapsed row had been covering.
        """
        lapsed = date.today() - timedelta(days=gate.GRACE_DAYS + 1)
        rules = _rules(tmp_path, _valid_note(expires=lapsed))

        code, emit = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 1
        assert [f["plugin"] for f in json.loads(emit.read_text())] == ["40018"]

    def test_the_grace_boundary_itself_still_applies(self, tmp_path, monkeypatch):
        """Exactly GRACE_DAYS overdue is inside the grace, not past it."""
        edge = date.today() - timedelta(days=gate.GRACE_DAYS)
        rules = _rules(tmp_path, _valid_note(expires=edge))

        code, _ = _run(tmp_path, _report(_CONFIRM), rules, monkeypatch)

        assert code == 0


class TestStaleSuppression:
    def test_a_suppression_that_matched_nothing_is_reported(self, tmp_path, monkeypatch, capsys):
        """The row outliving its finding is the failure mode of suppressions.

        Nothing goes red — the suppression is not wrong, only obsolete — but it
        has to be visible, or it sits there covering an endpoint long after the
        evidence for it is gone.
        """
        rules = _rules(tmp_path, _valid_note())

        code, _ = _run(tmp_path, _report(_ELSEWHERE), rules, monkeypatch)

        assert code == 1
        out = capsys.readouterr().out
        assert "matched no finding in the api report" in out, (
            "the note names the profile: the same rule file serves the baseline and the "
            "full scan, so 'this report' read as 'anywhere' and made a row that is live "
            "in one profile look dead in the other."
        )

    def test_a_broader_suppression_over_the_same_finding_is_not_called_stale(self, tmp_path, monkeypatch, capsys):
        """Two rows covering one URL: both are doing work, neither is stale.

        Crediting only the first match reported the second as "matched no finding
        … remove the row" — the signal that means a suppression has outlived its
        evidence, aimed at one that had not.
        """
        path = tmp_path / "rules.tsv"
        path.write_text(
            "\t".join(["40018", "IGNORE", "MEDIUM", _valid_note()])
            + "\n"
            + "\t".join(["40018", "IGNORE", "MEDIUM", _valid_note(scope="/api/v1/privacy/")])
            + "\n",
            encoding="utf-8",
        )

        code, _ = _run(tmp_path, _report(_CONFIRM), path, monkeypatch)

        assert code == 0
        assert "matched no finding" not in capsys.readouterr().out


class TestEmittedVerdict:
    def test_the_verdict_file_is_written_even_when_nothing_blocks(self, tmp_path, monkeypatch):
        """`security-zap-postmerge.yml` reads absence as "the gate never ran".

        If a clean run wrote no file, every clean post-merge scan would open a
        failure instead of staying quiet.
        """
        code, emit = _run(tmp_path, _report(_CONFIRM, pluginid="10049", riskcode="0"), None, monkeypatch)

        assert code == 0
        assert emit.is_file()
        assert json.loads(emit.read_text()) == []

    def test_the_verdict_carries_what_the_issue_body_needs(self, tmp_path, monkeypatch):
        code, emit = _run(tmp_path, _report(_CONFIRM), None, monkeypatch)

        assert code == 1
        [finding] = json.loads(emit.read_text())
        assert finding["plugin"] == "40018"
        assert finding["name"] == "SQL Injection"
        assert finding["site"] == "http://backend:8000"
        assert finding["count"] == 1
        assert finding["instances"] == [{"method": "POST", "uri": _CONFIRM}]
