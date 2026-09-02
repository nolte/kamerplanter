"""Tests for the route role-guard gate (``scripts/check_route_role_guards.py``).

**What is under test.** The parsing and the five rules, driven against
*constructed* miniature routers and decision tables written into ``tmp_path`` —
never against the real ``AppRoutes.tsx``. A test asserting "the router has 85
decided routes" would go red on the next legitimate route and teach nobody
anything; one case below does read the real pair, but only to assert that the
shipped tree passes, which is a property that must hold at every commit.

**The deliberately-broken router.** :class:`TestItCanFail` drops a wrapper the
table declares, adds a route nobody decided, and points the table at a route that
no longer exists — the three shapes #1261 is about — and asserts the check goes
red and names each. A gate nobody has watched fail is a gate nobody knows works.

**The obsolete-entry direction is the half that rots.** A deleted route leaving
its decision behind turns the table into a pre-approval: the next route to re-use
that path inherits a judgement nobody made for it. Same rule, same reason, as
``check_layer_imports``' obsolete-allowlist entry.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path.

Traces to #1261 / REQ-049 §2.3 (no TC-ID: a source-tree gate is not a
user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("check_route_role_guards")


ROUTER_TEMPLATE = """\
import {{ Route }} from 'react-router-dom';
import RequireRole from '@/auth/RequireRole';

export const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={{<ProtectedRoute />}}>
{routes}
    </Route>,
  ),
);
"""

GUARDED_ROUTE = """\
      <Route
        path="{path}"
        element={{
          <RequireRole min="{min}">
            <Suspense fallback={{<LoadingSkeleton variant="card" />}}>
              <{component} />
            </Suspense>
          </RequireRole>
        }}
      />
"""

PLAIN_ROUTE = """\
      <Route
        path="{path}"
        element={{
          <Suspense fallback={{<LoadingSkeleton variant="card" />}}>
            <{component} />
          </Suspense>
        }}
      />
"""


@pytest.fixture
def build_pair(tmp_path: Path) -> Callable[..., tuple[Path, Path]]:
    """Return a helper writing a miniature router + decision table into ``tmp_path``.

    Returns the ``(router, table)`` pair the check takes as its two inputs.
    """

    def _build(
        *,
        guarded_routes: dict[str, str] | None = None,
        plain_routes: tuple[str, ...] = (),
        declared_guarded: dict[str, str] | None = None,
        action_gated: tuple[str, ...] = (),
        ungated: tuple[str, ...] = (),
    ) -> tuple[Path, Path]:
        guarded_routes = {} if guarded_routes is None else guarded_routes
        declared = guarded_routes if declared_guarded is None else declared_guarded

        blocks = [
            GUARDED_ROUTE.format(path=path, min=minimum, component="PageFor" + str(index))
            for index, (path, minimum) in enumerate(guarded_routes.items())
        ]
        blocks += [
            PLAIN_ROUTE.format(path=path, component="PlainPage" + str(index)) for index, path in enumerate(plain_routes)
        ]
        router = tmp_path / "AppRoutes.tsx"
        router.write_text(ROUTER_TEMPLATE.format(routes="".join(blocks)), encoding="utf-8")

        entries = "\n".join(
            f"  '{path}': {{ min: '{minimum}', gate: 'POST /x — require_tenant_role({minimum})' }},"
            for path, minimum in declared.items()
        )
        table = tmp_path / "roleGuardedRoutes.ts"
        table.write_text(
            textwrap.dedent(
                """\
                /* A doc comment naming 'not-a-real-route' in prose. */
                export const ROLE_GUARDED_ROUTES = {
                %(entries)s
                };

                export const ACTION_GATED_ROUTES: readonly string[] = [
                %(action)s
                ];

                export const UNGATED_ROUTES: readonly string[] = [
                %(ungated)s
                ];
                """
            )
            % {
                "entries": entries,
                "action": "\n".join(f"  '{path}'," for path in action_gated),
                "ungated": "\n".join(f"  '{path}'," for path in ungated),
            },
            encoding="utf-8",
        )
        return router, table

    return _build


def rules(findings: list[object]) -> list[tuple[str, str]]:
    """Reduce findings to ``(rule, route)`` pairs for readable assertions."""
    return sorted((f.rule, f.route) for f in findings)  # type: ignore[attr-defined]


class TestAcceptsACompleteTable:
    """A router whose every route is decided, with the declared guards in place."""

    def test_no_findings(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        router, table = build_pair(
            guarded_routes={"pflanzen/identifikation": "grower"},
            plain_routes=("dashboard", "glossar"),
            action_gated=("dashboard",),
            ungated=("glossar",),
        )
        assert checker.collect(router, table) == []

    def test_exit_code_is_zero(
        self, build_pair: Callable[..., tuple[Path, Path]], capsys: pytest.CaptureFixture[str]
    ) -> None:
        router, table = build_pair(
            guarded_routes={"vermehrung": "grower"},
            plain_routes=("glossar",),
            ungated=("glossar",),
        )
        code = checker.main(["--router", str(router), "--table", str(table)])
        assert code == checker.EXIT_OK
        assert "1 guarded" in capsys.readouterr().out


class TestItCanFail:
    """The three shapes #1261 is about, each asserted to turn the check red."""

    def test_guard_declared_but_not_applied(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        # The regression: a route loses its wrapper while the table still says it
        # is guarded — the state `develop` was in before #1261, one route at a time.
        router, table = build_pair(
            plain_routes=("pflanzen/identifikation",),
            declared_guarded={"pflanzen/identifikation": "grower"},
        )
        assert rules(checker.collect(router, table)) == [("missing-guard", "pflanzen/identifikation")]

    def test_route_with_no_decision(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        router, table = build_pair(plain_routes=("brandneu",))
        assert rules(checker.collect(router, table)) == [("undecided-route", "brandneu")]

    def test_decision_for_a_route_that_no_longer_exists(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        router, table = build_pair(plain_routes=("glossar",), ungated=("glossar", "entfernt"))
        assert rules(checker.collect(router, table)) == [("obsolete-decision", "entfernt")]

    def test_exit_code_is_one(
        self, build_pair: Callable[..., tuple[Path, Path]], capsys: pytest.CaptureFixture[str]
    ) -> None:
        router, table = build_pair(plain_routes=("brandneu",))
        code = checker.main(["--router", str(router), "--table", str(table)])
        assert code == checker.EXIT_FINDINGS
        assert "undecided-route" in capsys.readouterr().out


class TestGuardAndTableMustAgree:
    """Both directions of the pairing, and the minimum itself."""

    def test_wrapper_on_an_undeclared_route_is_refused(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        # A guard the table does not back may be stricter than the API, which
        # removes read access the API grants — the mirror image of the bug.
        router, table = build_pair(
            guarded_routes={"glossar": "grower"},
            declared_guarded={},
            ungated=("glossar",),
        )
        assert rules(checker.collect(router, table)) == [("undeclared-guard", "glossar")]

    def test_minimum_mismatch_is_refused(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        router, table = build_pair(
            guarded_routes={"vermehrung": "lead"},
            declared_guarded={"vermehrung": "grower"},
        )
        assert rules(checker.collect(router, table)) == [("guard-minimum-mismatch", "vermehrung")]

    def test_route_decided_in_two_buckets_is_refused(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        router, table = build_pair(
            plain_routes=("dashboard",),
            action_gated=("dashboard",),
            ungated=("dashboard",),
        )
        assert ("decided-twice", "dashboard") in rules(checker.collect(router, table))


class TestParsing:
    """Input handling that a green run would otherwise hide."""

    def test_a_route_named_only_in_prose_is_not_a_decision(self, build_pair: Callable[..., tuple[Path, Path]]) -> None:
        # The table's doc comments quote route paths to explain the buckets.
        # Counting those as entries would let the check pass on documentation
        # instead of on the lists — green on the wrong evidence.
        router, table = build_pair(plain_routes=("not-a-real-route",))
        assert rules(checker.collect(router, table)) == [("undecided-route", "not-a-real-route")]

    def test_a_line_comment_beside_an_entry_does_not_change_the_parse(
        self, tmp_path: Path, build_pair: Callable[..., tuple[Path, Path]]
    ) -> None:
        """A per-entry reason may contain an apostrophe (#1333).

        The buckets carry each decision's *reason* as a `//` comment beside it —
        that is what makes the table reviewable rather than a bare list. English
        reasons contain apostrophes, and before this was handled the first such
        comment made the parser read prose as route names: twelve decided routes
        were reported `undecided-route` and two comment fragments came back as
        `obsolete-decision`, on a table that was in fact complete.

        Fails against the pre-#1333 parser, which is the point.
        """
        router, table = build_pair(plain_routes=("a", "b"), ungated=("a", "b"))
        source = table.read_text(encoding="utf-8")
        source = source.replace(
            "  'a',",
            "  // RequireRole's restrict-only mode can't help here — it isn't a read page.\n  'a',",
            1,
        )
        table.write_text(source, encoding="utf-8")

        assert checker.collect(router, table) == []

    @pytest.mark.parametrize(
        "entries",
        [
            ("https://example.test/x", "a"),
            ("a", "https://example.test/x"),
            ("https://example.test/x",),
        ],
        ids=["first", "last", "sole"],
    )
    def test_an_entry_containing_comment_markers_is_parsed_intact(
        self, build_pair: Callable[..., tuple[Path, Path]], entries: tuple[str, ...]
    ) -> None:
        """A `//` or `/*` inside a quoted entry is part of the entry, not a comment.

        A stripper that cut comments blindly left a stump of the entry (or, for
        the last entry of a bucket, nothing at all) and reported it as a deleted
        route — a heuristic that only caught one of the shapes. The parser now
        recognises comments only outside string literals, so the entry survives
        in every position and the decision table is read as written. The URL is
        then simply a decision for a route the router does not have.
        """
        router, table = build_pair(plain_routes=("a",), ungated=entries)

        expected = [("obsolete-decision", "https://example.test/x")]
        if "a" not in entries:
            expected.append(("undecided-route", "a"))
        assert sorted(rules(checker.collect(router, table))) == sorted(expected)

    def test_element_before_path_is_refused_rather_than_mis_attributed(
        self, tmp_path: Path, build_pair: Callable[..., tuple[Path, Path]]
    ) -> None:
        _, table = build_pair(ungated=("a", "b"))
        router = tmp_path / "Swapped.tsx"
        router.write_text(
            '<Route element={<RequireRole min="grower"><A /></RequireRole>} path="a" />\n'
            '<Route path="b" element={<B />} />\n',
            encoding="utf-8",
        )
        with pytest.raises(checker.RouteGuardCheckError):
            checker.collect(router, table)

    def test_missing_table_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, build_pair: Callable[..., tuple[Path, Path]]
    ) -> None:
        # NFR-018 §2: "I could not measure this" must never report green.
        router, _ = build_pair(plain_routes=("glossar",), ungated=("glossar",))
        code = checker.main(["--router", str(router), "--table", str(tmp_path / "nope.ts")])
        assert code == checker.EXIT_USAGE

    def test_json_output_carries_the_findings(
        self, build_pair: Callable[..., tuple[Path, Path]], capsys: pytest.CaptureFixture[str]
    ) -> None:
        router, table = build_pair(plain_routes=("brandneu",))
        code = checker.main(["--router", str(router), "--table", str(table), "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert code == checker.EXIT_FINDINGS
        assert payload["findings"][0]["route"] == "brandneu"


class TestShippedTree:
    """The one case that reads the real files: the tree in this commit passes."""

    def test_the_repository_router_is_fully_decided(self) -> None:
        repo_root = find_repo_root(Path(__file__).resolve())
        assert repo_root is not None
        router = repo_root / checker.DEFAULT_ROUTER
        table = repo_root / checker.DEFAULT_TABLE
        assert checker.collect(router, table) == []
