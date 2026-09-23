"""The falsification suite for ``scripts/check_gate_text_assertions.py`` (#1456).

This check exists because a gate can be satisfied by prose. It would be an
unusually poor joke if it were satisfiable by prose itself, so that is the first
thing asserted here and it is asserted from both ends:

* a gate file whose **only** occurrence of the pattern is inside a comment and a
  docstring yields no finding — the check cannot be made to report something
  that is not there;
* a gate file with a real predicate yields a finding that no amount of prose
  around it removes — the check cannot be talked out of something that is.

Detection is an :mod:`ast` walk, where comments do not exist as nodes at all, so
neither property is a promise: they follow from the parser. The tests below fix
that, and fix each hop of the taint propagation separately, because the
propagation — not the sink list — is where this check would silently go quiet.

The ``# prose-permeable:`` waiver is held to the same rule: it counts only as a
comment token, never as a sentence in a docstring, and a waiver attached to no
site is an error rather than a decoration.

Traces to #1456 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

check = load_repo_script("check_gate_text_assertions")
source_text = load_repo_script("source_text")

#: The glob the fake trees below are measured through.
_ONLY = ("gates/*.py",)


def _tree(root: Path, **modules: str) -> Path:
    """Write a fake gate tree and return its root."""
    (root / "gates").mkdir(parents=True, exist_ok=True)
    for name, body in modules.items():
        (root / "gates" / f"{name}.py").write_text(textwrap.dedent(body), encoding="utf-8")
    return root


def _sites(root: Path) -> list[check.Site]:
    """Every site the check finds in a fake tree."""
    return check.measure(root, _ONLY).sites


class TestTheCheckCannotBeSatisfiedByProse:
    """The meta-trap: this check's own positive branch must be comment-blind."""

    def test_a_predicate_written_only_in_prose_is_not_a_site(self, tmp_path: Path) -> None:
        """The failing direction of every gate this check exists to fix.

        Every spelling of the pattern appears here — in a module docstring, in a
        function docstring, in a ``#`` comment, and in a plain string — and not
        one of them is code. A line-based or regex-based implementation reports
        four findings; the parser reports none.
        """
        root = _tree(
            tmp_path,
            quiet='''
            """This module once did `"marker" in path.read_text()` and no longer does."""

            def audit(path):
                """Historically: assert "marker" in path.read_text(encoding="utf-8")."""
                # if "marker" in path.read_text(): raise SystemExit(1)
                note = 'the old form was: "marker" in path.read_text()'
                return note
            ''',
        )

        assert _sites(root) == []

    def test_a_real_predicate_is_a_site_no_comment_can_remove(self, tmp_path: Path) -> None:
        """The other direction: prose beside a real site does not clear it."""
        root = _tree(
            tmp_path,
            loud='''
            def audit(path):
                # This is fine, honestly. It has been reviewed. See #0000.
                """It is fine."""
                return "marker" in path.read_text(encoding="utf-8")
            ''',
        )

        (site,) = _sites(root)
        assert site.kind == "membership"
        assert not site.waived

    def test_the_waiver_counts_only_as_a_comment(self, tmp_path: Path) -> None:
        """A sentence in a docstring is documentation, not a decision.

        This is the exact confusion the check refuses everywhere else, so its own
        escape hatch may not fall for it.
        """
        root = _tree(
            tmp_path,
            docstring_waiver='''
            def audit(path):
                """Sites here carry # prose-permeable: because the subject is prose."""
                return "marker" in path.read_text()
            ''',
        )

        (site,) = _sites(root)
        assert site.reason is None

    def test_a_comment_waiver_records_the_site_without_hiding_it(self, tmp_path: Path) -> None:
        """A waived site stays on the list — it is a deferral somebody reads."""
        root = _tree(
            tmp_path,
            waived="""
            def audit(path):
                # prose-permeable: the marker being read IS a comment
                return "marker" in path.read_text()
            """,
        )
        measurement = check.measure(root, _ONLY)

        assert [site.reason for site in measurement.sites] == ["the marker being read IS a comment"]
        assert measurement.unwaived == []

    def test_a_waiver_excusing_nothing_is_red(self, tmp_path: Path) -> None:
        """Otherwise a waiver outlives the assertion it excused, unnoticed."""
        root = _tree(
            tmp_path,
            leftover="""
            def audit(path):
                # prose-permeable: whatever this used to excuse is gone
                return path.is_file()
            """,
        )
        measurement = check.measure(root, _ONLY)

        assert [item.line for item in measurement.stale] == [3]
        assert measurement.failed


class TestTheTaintReachesEveryHopItClaims:
    """Where this check would go quiet: the propagation, not the sink list."""

    @pytest.mark.parametrize(
        ("label", "body"),
        [
            (
                "direct",
                """
                def audit(path):
                    return "marker" in path.read_text()
                """,
            ),
            (
                "local variable",
                """
                def audit(path):
                    source = path.read_text()
                    return "marker" in source
                """,
            ),
            (
                "string operation",
                """
                def audit(path):
                    return "marker" in path.read_text().lower().replace("a", "b")
                """,
            ),
            (
                "iteration",
                """
                def audit(path):
                    for line in path.read_text().splitlines():
                        if "marker" in line:
                            return True
                    return False
                """,
            ),
            (
                "helper return value",
                """
                def load(path):
                    return path.read_text()

                def audit(path):
                    return "marker" in load(path)
                """,
            ),
            (
                "helper parameter",
                """
                def decide(source):
                    return "marker" in source

                def audit(path):
                    return decide(path.read_text())
                """,
            ),
            (
                "pytest fixture",
                """
                def workflow():
                    return open("x").read()

                def test_it(workflow):
                    assert "marker" in workflow
                """,
            ),
            (
                "regular expression",
                """
                import re

                def audit(path):
                    return re.search("marker", path.read_text()) is not None
                """,
            ),
            (
                "occurrence count",
                """
                def audit(path):
                    return path.read_text().count("marker") == 1
                """,
            ),
        ],
    )
    def test_each_route_from_a_file_to_a_predicate_is_seen(self, tmp_path: Path, label: str, body: str) -> None:
        """One case per spelling of "the text came out of a file".

        Each is a shape a gate in this tree actually uses. A hop this list does
        not carry is a hop the check does not follow, and a gate one refactoring
        away from being invisible.
        """
        root = _tree(tmp_path, module=body)

        assert len(_sites(root)) == 1, f"{label}: not followed"

    @pytest.mark.parametrize(
        ("label", "body"),
        [
            (
                "executable_source",
                """
                from source_text import executable_source

                def audit(path):
                    return "marker" in executable_source(path.read_text(), language="python")
                """,
            ),
            (
                "is_called",
                """
                from source_text import is_called

                def audit(path):
                    return is_called("marker", path.read_text(), language="typescript")
                """,
            ),
            (
                "ast.parse",
                """
                import ast

                def audit(path):
                    return "marker" in ast.dump(ast.parse(path.read_text()))
                """,
            ),
            (
                "yaml.safe_load",
                """
                import yaml

                def audit(path):
                    return "marker" in yaml.safe_load(path.read_text())
                """,
            ),
        ],
    )
    def test_a_reduced_or_parsed_value_is_not_a_site(self, tmp_path: Path, label: str, body: str) -> None:
        """The correct forms must be silent, or the check pushes people off them."""
        root = _tree(tmp_path, module=body)

        assert _sites(root) == [], f"{label}: falsely reported"

    def test_one_function_does_not_taint_the_next(self, tmp_path: Path) -> None:
        """Scopes are separate, or the check invents sites and clears real ones."""
        root = _tree(
            tmp_path,
            two="""
            def reads(path):
                source = path.read_text()
                return len(source)

            def unrelated(source):
                return "marker" in source
            """,
        )

        assert _sites(root) == []

    def test_a_comment_stripper_may_read_raw_text(self, tmp_path: Path) -> None:
        """Flagging the cure would make it look like the disease."""
        root = _tree(
            tmp_path,
            stripper="""
            def strip_comments(text):
                return "\\n".join(
                    line for line in text.splitlines() if "#" not in line
                )
            """,
        )

        assert _sites(root) == []


class TestTheInventoryIsMeasuredNotAssumed:
    def test_a_collapsed_scan_is_red_rather_than_green(self, tmp_path: Path) -> None:
        """The anti-vacuity floor.

        A scan that matches nothing reports "no findings", which is the same
        output as a clean tree. The floor makes the two distinguishable.
        """
        measurement = check.measure(_tree(tmp_path, only='"x"\n'), _ONLY)

        assert measurement.sites == []
        assert measurement.failed, "one gate file is not an inventory"

    def test_the_floor_leaves_room_to_move(self) -> None:
        """A floor equal to today's count goes red on every legitimate change.

        It also cannot tell "a gate was retired" from "the parser collapsed",
        which is the correction #1610 had to make. Headroom is the point, so it
        is asserted rather than left to whoever edits the constant next.
        """
        measurement = check.measure(check.REPO_ROOT)

        assert len(measurement.files) > check.MIN_GATE_FILES + 10

    def test_this_repository_decides_about_code_from_code(self) -> None:
        """The arming condition: the real tree, not a fixture."""
        measurement = check.measure(check.REPO_ROOT)

        assert measurement.unwaived == [], "\n".join(
            f"{site.path}:{site.line} [{site.kind}] {site.code}" for site in measurement.unwaived
        )
        assert measurement.stale == []


class TestTheReducerKeepsCodeAndDropsProse:
    def test_python_loses_its_comments_and_docstrings_only(self) -> None:
        reduced = source_text.executable_source(
            'def f():\n    """calls marker()"""\n    # marker()\n    return marker()\n',
            language="python",
        )

        assert reduced.count("marker") == 1
        assert "return marker()" in reduced

    def test_a_typescript_comment_goes_and_a_url_stays(self) -> None:
        reduced = source_text.executable_source(
            '// listAllWidgets loads it\nconst u = "https://a//b";\nlistAllWidgets();\n',
            language="typescript",
        )

        assert "https://a//b" in reduced
        assert reduced.count("listAllWidgets") == 1

    def test_a_hash_inside_a_yaml_string_survives(self) -> None:
        reduced = source_text.executable_source('image: "a # b"   # the real comment\n', language="yaml")

        assert reduced.strip() == 'image: "a # b"'

    def test_a_name_in_a_comment_is_not_a_call(self) -> None:
        """The #1610 defect, in one assertion."""
        commented = "// fetchAllFertilizers is the complete loader\nfetchPage();\n"

        assert "fetchAllFertilizers" in commented
        assert not source_text.is_called("fetchAllFertilizers", commented, language="typescript")

    def test_an_unmapped_language_is_refused_rather_than_passed_through(self) -> None:
        """Returning the text unchanged would re-open the class silently."""
        with pytest.raises(source_text.UnknownLanguage):
            source_text.executable_source("x", language="cobol")


class TestThePythonReductionStillParses:
    """A gate that wants to *parse* the reduced text must be able to (#1671).

    Two independent defects broke that: a docstring that is the only statement
    of its block left the block empty, and ``ast`` columns are UTF-8 *byte*
    offsets, so a docstring with a non-ASCII character before its closing
    quotes was sliced past its end — past the newline — joining the next line
    onto it and shifting every line number below.
    """

    def test_a_docstring_only_block_reparses_and_keeps_its_line_numbers(self) -> None:
        text = (
            "class Boom(Exception):\n"
            '    """Raised when it goes boom."""\n'
            "\n"
            "def f():\n"
            '    """Only a docstring,\n'
            '    over two lines."""\n'
            "\n"
            'def g(): """inline"""\n'
            "marker = 1\n"
        )

        reduced = source_text.executable_source(text, language="python")
        tree = ast.parse(reduced)

        assert reduced.count("\n") == text.count("\n")
        assert "docstring" not in reduced
        assert [n.lineno for n in tree.body] == [1, 4, 8, 9]

    def test_a_non_ascii_docstring_does_not_swallow_the_next_line(self) -> None:
        text = 'def f():\n    """Probe \u2192 ``reachable=False`` (\u00a7 5)."""\n    return marker()\nother = 2\n'

        reduced = source_text.executable_source(text, language="python")
        tree = ast.parse(reduced)

        assert reduced.splitlines()[2] == "    return marker()"
        assert "reachable" not in reduced
        assert [n.lineno for n in tree.body] == [1, 4]

    def test_every_backend_module_reparses_with_its_line_count(self) -> None:
        repo_root = find_repo_root(Path(__file__).resolve())
        assert repo_root is not None
        modules = sorted((repo_root / "src" / "backend" / "app").rglob("*.py"))
        # Anti-vacuity: an empty or mis-rooted walk must not pass as "0 failures".
        assert len(modules) > 100, f"walk found only {len(modules)} modules"

        failures = []
        for module in modules:
            text = module.read_text(encoding="utf-8")
            reduced = source_text.executable_source(text, language="python")
            if reduced.count("\n") != text.count("\n"):
                failures.append(f"{module}: line count changed")
                continue
            try:
                ast.parse(reduced)
            except SyntaxError as exc:
                failures.append(f"{module}:{exc.lineno}: {exc.msg}")

        assert failures == [], f"{len(failures)} of {len(modules)} modules:\n" + "\n".join(failures[:20])
