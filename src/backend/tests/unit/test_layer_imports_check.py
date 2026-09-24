"""Tests for the layer gate (``scripts/check_layer_imports.py``).

**What is under test.** The detection and allowlist logic, driven against
*constructed* API trees written into ``tmp_path`` — never against the real
``src/backend/app/api``. A test asserting "the tree has 22 crossings" would go
red on the next legitimate refactoring and teach nobody anything.

**The deliberately-broken router.** :class:`TestItCanFail` writes a router that
imports a repository — the #1019/#997 shape — and asserts the check goes red and
names it. A gate nobody has watched fail is a gate nobody knows works.

**The other direction is the half that rots.** :class:`TestObsoleteEntries` pins
that an allowlist entry matching no import is an ERROR. Without that rule the
allowlist decays into a set of pre-approvals for imports nobody has written yet:
a removed crossing leaves its entry behind, and re-adding the import later is
silently permitted. The same rule guards
``seed_steckbrief_consistency.ALLOWED_DISCREPANCIES``.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path.

**Rule 2 (#1556) is tested the same way**, in :class:`TestBusinessLogicHandles`.
The rule it must satisfy is stronger than "does it catch the two sites the issue
named": those two used one spelling (``self._user_repo._db``), and a guard
written to that spelling would certify the tree clean while four modules holding
their own ``StandardDatabase`` stood untouched. So the tests drive BOTH spellings
against constructed trees, and one asserts that a module using the spelling the
issue's own grep could not see is still caught.

**Rule 2 has no allowlist since #1638.** The four modules it once recorded were
moved behind repositories and the entry mechanism was removed, so
:class:`TestRuleTwoCannotBeSatisfiedByListing` pins both halves: the mechanism is
gone, and re-adding a handle to any of the four formerly-recorded modules — in a
copy of the real ``app/domain`` — turns the gate red.

Traces to the 2026-08-08 issue-pattern audit, measure P1.3 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
import shutil
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_layer_imports")


@pytest.fixture
def build_tree(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing a miniature ``app/api`` package into ``tmp_path``.

    Returns the scan root (``app/api``). Relative-import resolution walks the
    package chain, so the ``__init__.py`` files matter.
    """

    def _write(path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        for parent in path.parents:
            if parent == tmp_path:
                break
            (parent / "__init__.py").touch()
        path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")

    def _build(*, router: str, area: str = "species") -> Path:
        app = tmp_path / "app"
        _write(app / "api" / "v1" / area / "router.py", router)
        return app / "api"

    return _build


def _modules(scan_root: Path) -> list[str]:
    """Every data-access module imported below *scan_root*, sorted."""
    return sorted(site.module for site in checker.collect(scan_root))


class TestItCanFail:
    """The deliberately-broken router, and the check going red on it."""

    def test_a_router_importing_a_repository_is_caught(self, build_tree: Callable[..., Path]) -> None:
        """The #1019/#997 shape: persistence driven straight from the endpoint."""
        scan_root = build_tree(
            router="""
            from fastapi import APIRouter

            from app.data_access.arango.species_repository import ArangoSpeciesRepository

            router = APIRouter()
            """
        )
        assert _modules(scan_root) == ["app.data_access.arango.species_repository"]

    def test_the_broken_router_makes_the_process_exit_non_zero(
        self,
        build_tree: Callable[..., Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Detection is worth nothing if the gate still reports success.

        The module-level allowlist is emptied so the constructed tree is judged
        on its own; this also pins that ``main`` reads that constant at all.
        """
        monkeypatch.setattr(checker, "ALLOWED_IMPORTS", ())
        scan_root = build_tree(
            router="""
            from app.data_access.arango.species_repository import ArangoSpeciesRepository
            """
        )
        assert checker.main(["--scan-root", str(scan_root)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "app.data_access.arango.species_repository" in out
        assert "NFR-001" in out
        assert "ALLOWED_IMPORTS" in out

    def test_the_plain_import_spelling_is_caught_too(self, build_tree: Callable[..., Path]) -> None:
        """``import app.data_access.x`` reaches the same package by another road."""
        scan_root = build_tree(
            router="""
            import app.data_access.arango.species_repository
            """
        )
        assert _modules(scan_root) == ["app.data_access.arango.species_repository"]

    def test_the_package_itself_is_caught(self, build_tree: Callable[..., Path]) -> None:
        """``from app.data_access.arango import collections`` — the raw-AQL shape."""
        scan_root = build_tree(
            router="""
            from app.data_access.arango import collections
            """
        )
        assert _modules(scan_root) == ["app.data_access.arango"]

    def test_a_service_import_is_not_a_crossing(self, build_tree: Callable[..., Path]) -> None:
        """Going through the business logic is the whole point; it must stay quiet."""
        scan_root = build_tree(
            router="""
            from app.domain.services.species_service import SpeciesService
            from app.common.dependencies import get_species_service
            """
        )
        assert _modules(scan_root) == []

    def test_a_similarly_named_package_is_not_matched(self, build_tree: Callable[..., Path]) -> None:
        """``app.data_access_helpers`` is a different package, not a prefix match."""
        scan_root = build_tree(
            router="""
            from app.data_access_helpers import paginate
            """
        )
        assert _modules(scan_root) == []


class TestTheAllowlist:
    """A recorded crossing passes; an unrecorded one does not."""

    @pytest.fixture
    def two_crossings(self, build_tree: Callable[..., Path]) -> Path:
        return build_tree(
            router="""
            from app.data_access.arango.species_repository import ArangoSpeciesRepository
            from app.data_access.external.inference_service_client import InferenceServiceClient
            """
        )

    def _entry(self, scan_root: Path, module: str) -> object:
        site = next(site for site in checker.collect(scan_root) if site.module == module)
        return checker.AllowedImport(path=site.relative(), module=module, reason="recorded for this test")

    def test_a_recorded_crossing_is_not_a_violation(self, two_crossings: Path) -> None:
        sites = checker.collect(two_crossings)
        allowlist = (
            self._entry(two_crossings, "app.data_access.arango.species_repository"),
            self._entry(two_crossings, "app.data_access.external.inference_service_client"),
        )
        violations, obsolete = checker.classify(sites, allowlist)
        assert violations == []
        assert obsolete == []

    def test_an_unrecorded_crossing_beside_a_recorded_one_still_fails(self, two_crossings: Path) -> None:
        """Recording one import must not shelter the file's other ones."""
        sites = checker.collect(two_crossings)
        allowlist = (self._entry(two_crossings, "app.data_access.arango.species_repository"),)
        violations, obsolete = checker.classify(sites, allowlist)
        assert [site.module for site in violations] == ["app.data_access.external.inference_service_client"]
        assert obsolete == []

    def test_the_entry_is_keyed_on_the_file_as_well_as_the_module(self, two_crossings: Path) -> None:
        """A crossing recorded for one router does not license another one.

        Keying on the module alone would turn every entry into a blanket
        permission for that repository across the whole API layer.
        """
        sites = checker.collect(two_crossings)
        allowlist = (
            checker.AllowedImport(
                path="src/backend/app/api/v1/somewhere_else/router.py",
                module="app.data_access.arango.species_repository",
                reason="recorded against a different file",
            ),
        )
        violations, _obsolete = checker.classify(sites, allowlist)
        assert "app.data_access.arango.species_repository" in [site.module for site in violations]


class TestObsoleteEntries:
    """An allowlist entry that matches nothing is an error, not a courtesy."""

    def test_an_entry_matching_no_import_fails_the_check(self, build_tree: Callable[..., Path]) -> None:
        """The debt was paid; the entry has to go with it.

        Left behind, it silently re-permits the import the moment somebody adds
        it back — a hole nobody opened deliberately.
        """
        scan_root = build_tree(router="from app.domain.services.species_service import SpeciesService\n")
        stale = checker.AllowedImport(
            path="src/backend/app/api/v1/species/router.py",
            module="app.data_access.arango.species_repository",
            reason="removed in an earlier change, entry forgotten",
        )
        violations, obsolete = checker.classify(checker.collect(scan_root), (stale,))
        assert violations == []
        assert obsolete == [stale]

    def test_an_obsolete_entry_makes_the_process_exit_non_zero(
        self,
        build_tree: Callable[..., Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Reporting it is worth nothing if the gate still goes green."""
        monkeypatch.setattr(
            checker,
            "ALLOWED_IMPORTS",
            (
                checker.AllowedImport(
                    path="src/backend/app/api/v1/species/router.py",
                    module="app.data_access.arango.species_repository",
                    reason="removed in an earlier change, entry forgotten",
                ),
            ),
        )
        scan_root = build_tree(router="from app.domain.services.species_service import SpeciesService\n")
        assert checker.main(["--scan-root", str(scan_root)]) == checker.EXIT_DEFECTS
        assert "match no import any more" in capsys.readouterr().out


class TestProcessContract:
    """Exit codes and the machine-readable output."""

    def test_json_reports_violations_and_obsolete_entries(
        self,
        build_tree: Callable[..., Path],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            checker,
            "ALLOWED_IMPORTS",
            (
                checker.AllowedImport(
                    path="nowhere/router.py",
                    module="app.data_access.arango.gone_repository",
                    reason="stale",
                ),
            ),
        )
        scan_root = build_tree(router="from app.data_access.arango.species_repository import ArangoSpeciesRepository\n")
        assert checker.main(["--scan-root", str(scan_root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert [entry["module"] for entry in payload["violations"]] == ["app.data_access.arango.species_repository"]
        assert [entry["module"] for entry in payload["obsolete_allowlist"]] == [
            "app.data_access.arango.gone_repository"
        ]

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot run must not report success — the #814 failure mode."""
        assert checker.main(["--scan-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err


@pytest.fixture
def build_domain(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing a miniature ``app/domain`` package into ``tmp_path``.

    Returns the scan root (``app/domain``).
    """

    def _build(*, modules: dict[str, str]) -> Path:
        domain = tmp_path / "app" / "domain"
        for relative, source in modules.items():
            path = domain / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
        return domain

    return _build


class TestBusinessLogicHandles:
    """Rule 2: no module under ``app/domain`` holds or reaches a persistence handle."""

    def test_the_reach_through_a_repository_spelling_is_caught(self, build_domain: Callable[..., Path]) -> None:
        """``self._user_repo._db`` — the shape #1556 measured, and the only one it saw."""
        root = build_domain(
            modules={
                "services/auth_service.py": """
                class AuthService:
                    def verify_email(self, token):
                        db = self._user_repo._db  # type: ignore[attr-defined]
                        return db.aql.execute("FOR d IN users RETURN d")
                """
            }
        )
        assert [site.marker for site in checker.collect_handles(root)] == [checker.HANDLE_MARKER]

    def test_the_spelling_the_issue_grep_could_not_see_is_caught_too(self, build_domain: Callable[..., Path]) -> None:
        """A service HANDED a ``StandardDatabase``.

        This is the assertion that makes the guard a guard about the class. It
        contains no ``_repo._db`` anywhere, so the ``_repo`` + ``_db`` grep — the
        measurement #1556 concluded "only two" from — reports it as clean.
        """
        root = build_domain(
            modules={
                "services/favorites_service.py": """
                from arango.database import StandardDatabase

                class FavoritesService:
                    def __init__(self, db: StandardDatabase) -> None:
                        self._db = db
                """
            }
        )
        markers = sorted(site.marker for site in checker.collect_handles(root))
        assert markers == ["handle", "import:arango.database"]

    def test_an_engine_is_business_logic_too(self, build_domain: Callable[..., Path]) -> None:
        """The scan root is ``app/domain``, not ``app/domain/services``.

        NFR-001 puts engines on the business-logic side of the boundary as much
        as services; scanning only ``services/`` would leave a door open one
        directory across.
        """
        root = build_domain(
            modules={
                "engines/calendar_aggregation_engine.py": """
                class CalendarAggregationEngine:
                    def __init__(self, db) -> None:
                        self._db = db
                """
            }
        )
        assert [site.relative() for site in checker.collect_handles(root)]

    def test_the_plain_driver_import_spelling_is_caught(self, build_domain: Callable[..., Path]) -> None:
        root = build_domain(modules={"services/s.py": "import arango\n"})
        assert [site.marker for site in checker.collect_handles(root)] == ["import:arango"]

    def test_a_clean_service_is_not_a_crossing(self, build_domain: Callable[..., Path]) -> None:
        root = build_domain(
            modules={
                "services/clean_service.py": """
                from app.domain.interfaces.user_repository import IUserRepository

                class CleanService:
                    def __init__(self, user_repo: IUserRepository) -> None:
                        self._user_repo = user_repo

                    def verify(self, token):
                        return self._user_repo.get_by_email_verification_token(token)
                """
            }
        )
        assert checker.collect_handles(root) == []

    def test_a_similarly_named_attribute_is_not_matched(self, build_domain: Callable[..., Path]) -> None:
        """``species_in_database`` and ``_dbg`` are not the handle."""
        root = build_domain(
            modules={
                "engines/identification_engine.py": """
                class IdentificationEngine:
                    def run(self, m):
                        self._dbg = m.species_in_database
                        return self._dbg
                """
            }
        )
        assert checker.collect_handles(root) == []

    def test_the_getattr_escape_is_caught(self, build_domain: Callable[..., Path]) -> None:
        """``getattr(repo, "_db")`` spells the same break without the attribute node."""
        root = build_domain(
            modules={
                "services/s.py": """
                class S:
                    def run(self, repo):
                        return getattr(repo, "_db")
                """
            }
        )
        assert [site.marker for site in checker.collect_handles(root)] == [checker.HANDLE_MARKER]

    def test_a_handle_stored_under_another_name_is_caught_by_its_use(self, build_domain: Callable[..., Path]) -> None:
        """No ``_db`` anywhere, and no ``arango`` import — but it still runs AQL.

        This is the assertion that stops the rule from being shaped like the
        offenders that happen to exist today, which is the mistake #1556 made one
        level up.
        """
        root = build_domain(
            modules={
                "services/s.py": """
                class S:
                    def __init__(self, database):
                        self.database = database

                    def run(self):
                        return self.database.aql.execute("FOR d IN users RETURN d")
                """
            }
        )
        assert [site.marker for site in checker.collect_handles(root)] == [checker.HANDLE_MARKER]

    def test_all_three_detections_collapse_into_one_marker(self, build_domain: Callable[..., Path]) -> None:
        """One finding per module, so a recorded module cannot change spelling and pass."""
        root = build_domain(
            modules={
                "services/s.py": """
                class S:
                    def __init__(self, db):
                        self._db = db

                    def run(self, repo):
                        return getattr(repo, "_db").aql.execute("FOR d IN users RETURN d")
                """
            }
        )
        assert [site.marker for site in checker.collect_handles(root)] == [checker.HANDLE_MARKER]

    def test_a_crossing_makes_the_process_exit_non_zero(
        self,
        build_domain: Callable[..., Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = build_domain(modules={"services/s.py": "class S:\n    def __init__(self, db):\n        self._db = db\n"})
        assert checker.main(["--handle-scan-root", str(root)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "hold or reach a persistence handle" in out
        assert "services/s.py" in out

    def test_a_missing_handle_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert checker.main(["--handle-scan-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err


class TestTheRealTree:
    """What the pre-commit hook asserts, asserted here too."""

    def test_the_api_layer_carries_no_unrecorded_crossing(self) -> None:
        """Running it from pytest as well means a backend-only change goes red here."""
        assert checker.main([]) == checker.EXIT_OK

    def test_the_business_logic_carries_no_unrecorded_handle(self) -> None:
        """Rule 2 on the real ``app/domain``; ``main([])`` runs both rules."""
        assert checker.main([]) == checker.EXIT_OK

    def test_the_business_logic_holds_no_handle_at_all(self) -> None:
        """Not "no unrecorded one": rule 2 has nothing to record into (#1638).

        #1556's two ``auth_service`` sites and #1638's four modules are all GONE,
        which this asserts directly on the scan rather than through an allowlist
        an entry could have satisfied.
        """
        sites = checker.collect_handles(checker.REPO_ROOT / checker.DEFAULT_HANDLE_SCAN_ROOT)
        assert [f"{site.relative()}:{site.line}: {site.marker}" for site in sites] == []

    def test_every_allowlist_entry_names_a_reason_worth_reading(self) -> None:
        """A one-word reason is a rubber stamp, and the allowlist IS the review.

        Not a style rule: this list is the only place the eleven-and-counting
        crossings are argued about, and an entry that says "legacy" turns the
        gate back into the thing it replaced.
        """
        thin = [f"{entry.path}: {entry.module}" for entry in checker.ALLOWED_IMPORTS if len(entry.reason) < 60]
        assert not thin, "allowlist entries with a reason too short to argue with:\n" + "\n".join(thin)


#: The modules rule 2 recorded before #1638, with a handle spelling to re-add.
_FORMERLY_RECORDED = {
    "services/favorites_service.py": "from arango.database import StandardDatabase\n",
    "services/starter_kit_service.py": "\n\ndef _probe(db):\n    return db.aql.execute('RETURN 1')\n",
    "services/onboarding_service.py": "\n\nclass _Holder:\n    def __init__(self, db):\n        self._db = db\n",
    "engines/calendar_aggregation_engine.py": "\n\ndef _reach(repo):\n    return getattr(repo, '_db')\n",
}


class TestRuleTwoCannotBeSatisfiedByListing:
    """#1638 acceptance: the allowlist reached zero and the mechanism went with it."""

    def test_there_is_no_handle_allowlist_to_add_an_entry_to(self) -> None:
        leftovers = [
            name for name in ("ALLOWED_HANDLES", "AllowedHandle", "classify_handles") if hasattr(checker, name)
        ]
        assert leftovers == [], f"the rule-2 entry mechanism is back: {leftovers}"

    @pytest.mark.parametrize("relative", sorted(_FORMERLY_RECORDED))
    def test_re_adding_a_handle_to_a_formerly_recorded_module_fails(
        self, relative: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A copy of the REAL ``app/domain`` with one handle re-introduced goes red.

        The real tree rather than a constructed one, so the test also proves the
        rest of ``app/domain`` stays clean around the injected site — a green
        baseline, then one line, then red.
        """
        real = checker.REPO_ROOT / checker.DEFAULT_HANDLE_SCAN_ROOT
        domain = tmp_path / "app" / "domain"
        shutil.copytree(real, domain, ignore=shutil.ignore_patterns("__pycache__"))
        assert checker.main(["--handle-scan-root", str(domain)]) == checker.EXIT_OK
        capsys.readouterr()

        target = domain / relative
        target.write_text(target.read_text(encoding="utf-8") + _FORMERLY_RECORDED[relative], encoding="utf-8")

        assert checker.main(["--handle-scan-root", str(domain)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert relative in out
        assert "no allowlist" in out
