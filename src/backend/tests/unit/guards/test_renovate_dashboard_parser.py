"""#1383 — the Renovate-health check, driven against a real dashboard body.

**What this guards.** ``scripts/ci/check_renovate_dashboard.py`` decides whether
Renovate is still reading the files it is supposed to read. That decision is the
one nothing in this repository could make between 2026-08-02 and 2026-09-10,
while the ``pip-compile`` manager extracted nothing at all and every lane stayed
green.

**The fixtures are real, and there are two of them, for a measured reason.**

``renovate_dashboard_2026-09-16.md`` is the verbatim body of issue #12 on the day
this was written (``gh issue view 12 --json body``). It is **not** the healthy
state: #1374 had not reached ``develop`` yet, so Renovate had not re-scanned, and
the body still shows ``poetry`` reading four ``pyproject.toml`` files and
``pip_requirements`` reading four side-service ``requirements.txt`` that the
working tree no longer contains. That makes it the most honest drift fixture
available — it is what the lane really would say today, and saying it would be
correct.

``renovate_dashboard_expected_after_1374.md`` is derived from it mechanically —
the two service ``pyproject.toml`` moved from ``poetry`` to ``pep621``, the four
deleted ``requirements.txt`` dropped, the two lock-less libraries left where
``task renovate:dry-run`` measured them. It WAS the healthy state; since #1464 it
is a drift fixture, and ``TestThePre1464BodyIsNowCorrectlyRed`` below is the
red-first proof for that change — six findings, each named.

``renovate_dashboard_expected_after_1464.md`` is derived from it the same way: both
libraries under ``pep621`` (seven trees), no ``poetry`` at all, and the three
``tests/e2e`` manifests that the ``ignorePaths`` override in ``renovate.json5``
admitted. Every number in it comes from ``task renovate:dry-run`` run before and
after that override on 2026-09-17 — ``pep621`` 5 -> 7 files, ``poetry``
2 -> absent, ``pip_requirements`` 2 -> 3, ``npm`` 1 -> 2, ``dockerfile`` 8 -> 9,
total 80 -> 83. Since #1509 it is a DRIFT fixture, and
``TestThePre1509BodyIsNowCorrectlyRed`` is the red-first proof for that change.

``renovate_dashboard_expected_after_1509.md`` is the healthy state today, derived
the same mechanical way: ``tests/e2e/requirements.txt`` became
``tests/e2e/pyproject.toml`` + ``uv.lock``, so it moved from ``pip_requirements``
to ``pep621`` (eight trees); ``docs/requirements.txt`` is compiled with
``--generate-hashes``; and the ``tests/e2e/Dockerfile`` block gained the
``ghcr.io/astral-sh/uv`` layer that replaced its ``pip install``.

WHAT THAT DRY-RUN MEASURED, AND WHAT IT DID NOT — the #1509 review found the
first version of this paragraph claiming more than the run covered. Measured
with ``task renovate:dry-run`` (Renovate 44.103.2, 2026-09-19), each number read
from the run rather than reasoned about: ``pep621`` 7 -> 8 files,
``pip_requirements`` 3 -> 2 (``depCount`` 20 -> 56, the compiled docs list), and
the three ``tests/e2e/Dockerfile`` dependencies with their digests, taken
verbatim from the run's ``packageFile`` dump.

NOT re-measured, deliberately: the image digests in the OTHER ``dockerfile``
blocks, which this body inherits from its #1464 ancestor and which age with
every Renovate digest bump on develop. Nothing in :func:`check.build_report`
reads them — the ``dockerfile`` manager is asserted by FILE, not by dependency —
so pinning them to today's tree would buy nothing and cost a fixture edit per
digest bump. The one dependency that IS asserted here is the uv layer, because
it is what this change introduced;
:meth:`TestTheFixturesAreTheRealThing.test_the_e2e_dockerfile_block_shows_the_uv_layer`
holds it.

**Two measurements corrected the plan, in this order.** The #1383 analysis said
``poetry`` read "exactly the two side-service pyproject.toml". The real body
shows **four**: ``src/libs/kp_errortracking`` and ``src/libs/kp_vectordb`` were
in there too. The first version of this file then assumed those two would move
under ``pep621`` once ``poetry`` was disabled repository-wide. ``task
renovate:dry-run`` (Renovate 44.94.1, 2026-09-16) says they do not —
``enabled: false`` disables a manager's dependencies without stopping its
extraction, so ``poetry`` keeps extracting exactly those two and ``pep621``
claims exactly the five trees that have a ``uv.lock``. A rule of the form
"``poetry`` must not appear" would have alerted on a correct repository every
day. The rule that survives the measurement is "no second manager inside a
LOCKED tree", and the two lock-less libraries were enumerated in
``LOCKLESS_PYTHON_PROJECTS`` rather than waved through.

**#1464 then removed the premise rather than the rule.** Both libraries got a
hash-bearing ``uv.lock``, so ``pep621`` claims them and ``poetry`` — which only
ever extracted trees without one — leaves the inventory entirely. That is a
CONSEQUENCE of locking them, measured after the fact, not a rule that
``poetry`` must be absent: the rule is still "no second manager inside a locked
tree", now over seven trees instead of five, and ``LOCKLESS_PYTHON_PROJECTS`` is
empty.

The healthy fixture is built to that measurement, not to the guess.

**What is NOT under test here.** Whether Renovate's dashboard format is stable —
that is upstream's. This file pins the parser against one real body and against
injected problems; the format changing shows up as a :class:`DashboardError`,
which is a red run, not a silent pass. Traces to #1383 (no TC-ID: a CI observer
is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_renovate_dashboard.py"
_FIXTURES = Path(__file__).parent / "fixtures"
_TODAY = _FIXTURES / "renovate_dashboard_2026-09-16.md"
_PRE_1464 = _FIXTURES / "renovate_dashboard_expected_after_1374.md"
_PRE_1509 = _FIXTURES / "renovate_dashboard_expected_after_1464.md"
_HEALTHY = _FIXTURES / "renovate_dashboard_expected_after_1509.md"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_renovate_dashboard_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_renovate_dashboard_under_test"] = module
    spec.loader.exec_module(module)
    return module


check = _load()


@pytest.fixture
def healthy_body() -> str:
    return _HEALTHY.read_text()


@pytest.fixture
def todays_body() -> str:
    return _TODAY.read_text()


@pytest.fixture
def pre_1464_body() -> str:
    """The state that was healthy BEFORE #1464 — and must not be, after it."""
    return _PRE_1464.read_text()


def _inject(body: str, anchor: str, replacement: str) -> str:
    """Replace *anchor* once, and REFUSE to return an unchanged body.

    Measured need, not caution (#1509): two injection cases here anchored on
    `docs/requirements.txt (12)` and `pep621 (7)`, counts the new healthy fixture
    no longer carries. The positive ones went red — an unchanged healthy body
    does not alert — but a case asserting `alert is False` would have gone
    vacuously GREEN on a fixture it never touched. The anchor is asserted here so
    a drifted fixture reads as a broken test rather than as a passing one.
    """
    assert anchor in body, f"the fixture carries no {anchor!r} to inject at — this case would test nothing"
    return body.replace(anchor, replacement, 1)


def _report(body: str) -> dict:
    return check.build_report(body, repo_root=_REPO_ROOT)


class TestTheFixturesAreTheRealThing:
    """A fixture that drifted from the source is a certificate of nothing."""

    def test_both_fixtures_exist_and_are_substantial(self) -> None:
        for fixture in (_TODAY, _PRE_1464, _PRE_1509, _HEALTHY):
            assert fixture.is_file(), f"{fixture} is missing"
            assert len(fixture.read_text().splitlines()) > 500, (
                f"{fixture} is far shorter than a real dashboard body (~880 lines). A truncated fixture "
                "would exercise the parser on a shape Renovate never emits."
            )

    def test_the_healthy_fixture_really_is_the_repository_it_claims_to_describe(self, healthy_body: str) -> None:
        """Every pyproject the healthy fixture lists must exist in the checkout.

        The recurring failure here is a fixture that invents an impossible shape:
        the positive case then certifies nothing. This ties the fixture to the
        working tree.
        """
        inventory = check.manager_inventory(healthy_body)
        for package_file in inventory["pep621"]:
            assert (_REPO_ROOT / package_file).is_file(), (
                f"the healthy fixture lists {package_file} under pep621, but no such file exists in the "
                "checkout — the fixture describes a repository that is not this one"
            )

    def test_the_e2e_dockerfile_block_shows_the_uv_layer(self, healthy_body: str) -> None:
        """The fixture must not describe the image #1509 replaced.

        Its first version was a byte copy of the #1464 body: two base images, no
        `ghcr.io/astral-sh/uv`, while `tests/e2e/Dockerfile` had just been
        changed to copy that binary and `uv sync --locked` with it. A fixture
        that contradicts the change it was written for certifies nothing. Asserted
        by dependency NAME and not by digest, so a Renovate digest bump on
        develop does not make this red.
        """
        section = healthy_body[healthy_body.index("<summary>tests/e2e/Dockerfile") :]
        section = section[: section.index("</details>")]

        assert "ghcr.io/astral-sh/uv" in section, (
            "the fixture's tests/e2e/Dockerfile block predates #1509 — it still describes the image that "
            "installed with pip. Re-derive it from `task renovate:dry-run`."
        )

    def test_the_expected_locked_trees_all_carry_a_lock_on_disk(self) -> None:
        for package_file in check.EXPECTED_PEP621_FILES:
            assert (_REPO_ROOT / package_file).is_file(), f"{package_file} does not exist"
            assert (_REPO_ROOT / package_file).with_name("uv.lock").is_file(), (
                f"no uv.lock beside {package_file} — the expectation in check_renovate_dashboard.py is "
                "unsatisfiable against this checkout"
            )

    def test_the_healthy_fixture_matches_the_dry_run_measurement(self, healthy_body: str) -> None:
        """`task renovate:dry-run`, Renovate 44.103.2, 2026-09-19 — the numbers this fixture encodes.

        Compared as SETS, not as lists. The dashboard's ordering within a manager
        is Renovate's rendering detail and differs from the order the same run's
        JSON extract dump uses (measured on 2026-09-17: the dump sorts by path,
        the dashboard does not). :func:`check.build_report` reads membership and
        never order, so asserting a list here would make a correct repository red
        on a day Renovate changed how it sorts — a defect in the measuring tool,
        not in the thing measured.
        """
        inventory = check.manager_inventory(healthy_body)
        assert set(inventory["pep621"]) == set(check.EXPECTED_PEP621_FILES), (
            "the dry-run measured pep621 extracting exactly the eight locked trees; "
            f"the fixture says {inventory['pep621']}"
        )
        assert "poetry" not in inventory, (
            "the dry-run measured poetry leaving the inventory entirely once both shared libraries got a "
            "uv.lock (#1464) — it only ever extracted the two lock-less ones; "
            f"the fixture says {inventory.get('poetry')}"
        )
        assert inventory["pip_requirements"] == [
            "docs/requirements.txt",
            "tools/rag-eval/requirements.txt",
        ], (
            "tests/e2e/ left pip_requirements when #1509 locked it, and it must not come back: that "
            "prefix is a LOCKED tree now, so a second manager there is the #1371 shape"
        )
        assert inventory["npm"] == ["src/frontend/package.json", "tests/e2e/package.json"]

    def test_no_python_tree_in_the_checkout_is_lockless(self) -> None:
        """#1464's own acceptance criterion, measured against the filesystem."""
        assert check.lockless_python_trees(_REPO_ROOT) == [], (
            "a pyproject.toml without a uv.lock beside it. LOCKLESS_PYTHON_PROJECTS is empty on purpose: "
            "every Python tree here installs from a hash-bearing lock (NFR-009 §2.3)."
        )


class TestUnhashedInstallsAreAFindingNow:
    """#1509: the reported-only category became a gate, with one argued exception.

    It was report-only for one cycle, deliberately — the three lists predated
    #1464 and reddening the lane for a decision nobody had made would have
    failed a correct repository. The decision exists now, one outcome per file
    (lock, hash-pin in place, argued exception), so the default flips. A
    reported-only category that nobody ever converts is how a workaround becomes
    the design (CI spec §H).
    """

    def test_the_register_holds_exactly_the_one_argued_file(self) -> None:
        assert check.KNOWN_UNHASHED_REQUIREMENTS == ("tools/rag-eval/requirements.txt",), (
            f"KNOWN_UNHASHED_REQUIREMENTS is {check.KNOWN_UNHASHED_REQUIREMENTS}. #1509 shrank it to the "
            "one list that no image, lane or task installs; a second entry needs that same argument in "
            "writing, in the file itself."
        )

    def test_the_argument_lives_in_the_file_and_not_only_in_the_pull_request(self) -> None:
        """A reason recorded only in a merged PR body is a reason the next reader never sees."""
        for requirements in check.KNOWN_UNHASHED_REQUIREMENTS:
            text = (_REPO_ROOT / requirements).read_text()
            assert "#1509" in text, f"{requirements} carries no written argument for its exception"

    def test_the_sweep_finds_exactly_the_register_in_this_checkout(self) -> None:
        assert check.unhashed_requirements_installs(_REPO_ROOT) == sorted(check.KNOWN_UNHASHED_REQUIREMENTS)

    def test_the_real_checkout_does_not_alert_for_it(self, healthy_body: str) -> None:
        report = _report(healthy_body)

        assert report["alert"] is False
        assert report["undecided_unhashed_requirements"] == []

    def test_the_green_render_still_names_the_exception(self, healthy_body: str) -> None:
        """Otherwise the allowance lives only in JSON, which is an allowance nobody re-reads."""
        rendered = check.render(_report(healthy_body))

        assert "argued exception" in rendered
        for requirements in check.KNOWN_UNHASHED_REQUIREMENTS:
            assert requirements in rendered

    def test_an_undecided_list_reddens_the_lane(self, healthy_body: str, tmp_path: Path) -> None:
        """THE positive control for the flip: this assertion is what was False before #1509."""
        (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["alert"] is True
        assert any("Installed without hash verification: requirements.txt" in f for f in report["findings"])

    def test_the_argued_exception_does_not_redden_it(self, healthy_body: str, tmp_path: Path) -> None:
        """The same tree, same sweep, only the path differs — so the register is what decides."""
        (tmp_path / "tools" / "rag-eval").mkdir(parents=True)
        (tmp_path / "tools" / "rag-eval" / "requirements.txt").write_text("httpx>=0.28.0\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["undecided_unhashed_requirements"] == []
        assert not any("Installed without hash verification" in f for f in report["findings"])

    def test_a_hash_bearing_list_is_not_reported(self, tmp_path: Path) -> None:
        """pip's own `--hash=` form: a pinned list must not read as unpinned."""
        (tmp_path / "requirements.txt").write_text("fastapi==0.115.0 --hash=sha256:" + "a" * 64 + "\n")

        assert check.unhashed_requirements_installs(tmp_path) == []

    def test_the_continuation_form_generate_hashes_emits_is_understood(self, tmp_path: Path) -> None:
        """`--generate-hashes` puts the hashes BELOW the entry, behind a backslash."""
        (tmp_path / "requirements.txt").write_text(
            "babel==2.18.0 \\\n    --hash=sha256:" + "a" * 64 + " \\\n    --hash=sha256:" + "b" * 64 + "\n"
        )

        assert check.unhashed_requirements_installs(tmp_path) == []

    def test_one_hashed_entry_does_not_certify_the_rest(self, tmp_path: Path) -> None:
        """The review's S2: `"--hash=" in text` is a FILE test, not an ENTRY test.

        A list with one hashed entry and forty unhashed ones read as hashed. pip
        refuses such a file outright — hash-checking mode is all-or-nothing — so
        the damage was bounded, but the check claimed more than it measured.
        """
        (tmp_path / "requirements.txt").write_text(
            "fastapi==0.115.0 --hash=sha256:" + "a" * 64 + "\nstarlette==0.40.0\n"
        )

        assert check.unhashed_requirements_installs(tmp_path) == ["requirements.txt"]

    def test_an_option_line_is_not_mistaken_for_an_unhashed_entry(self, tmp_path: Path) -> None:
        """`-r`, `-c` and `--index-url` name no distribution and carry no hash."""
        (tmp_path / "requirements.txt").write_text(
            "--index-url https://example.invalid/simple\n-c constraints.txt\n"
            "fastapi==0.115.0 --hash=sha256:" + "a" * 64 + "\n"
        )

        assert check.unhashed_requirements_installs(tmp_path) == []

    def test_the_exception_is_per_file_and_not_per_directory(self, healthy_body: str, tmp_path: Path) -> None:
        """A second list beside the argued one is not covered by its argument."""
        (tmp_path / "tools" / "rag-eval").mkdir(parents=True)
        (tmp_path / "tools" / "rag-eval" / "requirements.txt").write_text("httpx>=0.28.0\n")
        (tmp_path / "tools" / "rag-eval" / "extra-requirements.txt").write_text("psycopg>=3.2.0\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["undecided_unhashed_requirements"] == ["tools/rag-eval/extra-requirements.txt"]

    def test_a_list_beside_a_uv_lock_is_still_reported(self, tmp_path: Path) -> None:
        """The exemption this used to assert was removed by #1509's own red-first run.

        Restoring the pre-#1509 `tests/e2e/requirements.txt` beside the new
        `tests/e2e/uv.lock` produced a GREEN check — the proof that the new gate
        reddens did not redden, because a sibling lock excused the list. A
        directory holding both is not a locked tree; it is two sources of truth
        for one install, and `pip install -r` reads the one without hashes.
        """
        (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\n")
        (tmp_path / "uv.lock").write_text("version = 1\n")

        assert check.unhashed_requirements_installs(tmp_path) == ["requirements.txt"]

    def test_an_unhashed_list_is_reported(self, tmp_path: Path) -> None:
        """The positive control — otherwise the three greens above prove nothing."""
        (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\n")
        (tmp_path / "nested").mkdir()
        (tmp_path / "nested" / "requirements-dev.txt").write_text("ruff\n")

        assert check.unhashed_requirements_installs(tmp_path) == [
            "nested/requirements-dev.txt",
            "requirements.txt",
        ]

    @pytest.mark.parametrize(
        "spelling",
        [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements.pip",
            "requirements/dev.txt",
            "constraints.txt",
            # The review's correction: the word comes SECOND in these two, so a
            # `requirements*` prefix glob never saw them.
            "dev-requirements.txt",
            "test-requirements.txt",
            "deep/nested/requirements/dev.txt",
        ],
    )
    def test_every_list_spelling_is_swept(self, tmp_path: Path, spelling: str) -> None:
        """The #1509 class-sweep question: name a spelling of the same thing I miss.

        `.pip` is pip's second extension, `requirements/dev.txt` is the directory
        layout whose file name does not start with the word, and `constraints.txt`
        is installed with `-c` in the same way. None of them was matched by the
        single `requirements*.txt` glob this started with.
        """
        target = tmp_path / spelling
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fastapi==0.115.0\n")

        assert check.unhashed_requirements_installs(tmp_path) == [spelling]

    def test_a_virtualenv_is_not_swept(self, tmp_path: Path) -> None:
        """A `.venv` holds other projects' requirement lists by the dozen."""
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "requirements.txt").write_text("whatever\n")

        assert check.unhashed_requirements_installs(tmp_path) == []

    def test_the_mkdocs_build_output_is_not_swept(self, tmp_path: Path) -> None:
        """Measured during #1509: `task docs:build` copies the list into `site/`.

        MkDocs copies every non-Markdown file under `docs/` into the built site,
        so a local docs build materialises `site/requirements.txt` — the dry-run
        showed `pip_requirements fileCount 3` where a clean checkout has 2. CI
        checks out clean and would never have seen it; a developer running the
        check after a docs build would have got a finding about a build artefact.
        """
        (tmp_path / "site").mkdir()
        (tmp_path / "site" / "requirements.txt").write_text("mkdocs>=1.6\n")

        assert check.unhashed_requirements_installs(tmp_path) == []

    def test_only_the_root_level_site_is_excluded(self, tmp_path: Path) -> None:
        """`.gitignore` says `site/`, anchored — so the exclusion is anchored too.

        Excluding the bare name at any depth would hide a real
        `docs/site/requirements.txt` somebody adds one day: a sweep quietly
        shrinking rather than a rule (#1509 review, S3).
        """
        (tmp_path / "docs" / "site").mkdir(parents=True)
        (tmp_path / "docs" / "site" / "requirements.txt").write_text("mkdocs>=1.6\n")

        assert check.unhashed_requirements_installs(tmp_path) == ["docs/site/requirements.txt"]


class TestDockerfilesMustNotInstallPythonOutsideALock:
    """The #1509 class sweep: the spelling a `requirements*.txt` sweep cannot see.

    Asked as the question that keeps a sweep honest — name a spelling of the
    same thing my pattern does not match. A Dockerfile that names its packages
    INLINE has no requirement list at all, so the sweep above is blind to it by
    construction, and an image is the artefact NFR-009 §2.3 is most about.
    """

    def test_no_dockerfile_in_this_checkout_installs_with_pip(self) -> None:
        assert check.dockerfile_python_installs(_REPO_ROOT) == [], (
            "every image here installs with `uv sync --locked`; a `pip install` in a build stage ships "
            "whatever the index served during that build"
        )

    def test_the_e2e_image_installs_from_its_lock(self) -> None:
        """The subject of #1509's first outcome, asserted at the artefact."""
        dockerfile = (_REPO_ROOT / "tests" / "e2e" / "Dockerfile").read_text()

        assert "uv sync --locked" in dockerfile
        assert (_REPO_ROOT / "tests" / "e2e" / "uv.lock").is_file()
        assert not (_REPO_ROOT / "tests" / "e2e" / "requirements.txt").exists(), (
            "the list #1509 replaced is back beside the lock — two sources of truth for the same install"
        )

    @pytest.mark.parametrize(
        "instruction",
        [
            "RUN pip install --no-cache-dir -r requirements.txt",
            "RUN pip3 install selenium",
            "RUN python -m pip install selenium",
            "RUN python3.14 -m pip install --user selenium",
            "RUN uv pip install selenium",
            "RUN apt-get update && pip install selenium",
            # Found by the #1509 review: a GLOBAL OPTION sits between the program
            # and the subcommand, which the first pattern forbade.
            "RUN pip --no-cache-dir install selenium",
            "RUN python -m pip -q install selenium",
            # `uv pip sync` installs an environment from a list exactly as
            # `install` does, and the JSON exec form is the same instruction
            # with different punctuation.
            "RUN uv pip sync requirements.txt",
            'RUN ["pip", "install", "selenium"]',
            "RUN pipx install pre-commit",
        ],
    )
    def test_every_spelling_is_caught(self, tmp_path: Path, instruction: str) -> None:
        """The positive control, one case per spelling the repository could use."""
        (tmp_path / "Dockerfile").write_text(f"FROM python:3.14-slim\n{instruction}\n")

        assert check.dockerfile_python_installs(tmp_path) == ["Dockerfile:2"]

    def test_a_comment_explaining_a_fixed_defect_is_not_a_defect(self, tmp_path: Path) -> None:
        """Three Dockerfiles here say "it used to be an unpinned `pip install`"."""
        (tmp_path / "Dockerfile").write_text(
            "FROM python:3.14-slim\n# lock -- it used to be an unpinned `pip install` outside any lock.\n"
            "RUN uv sync --locked\n"
        )

        assert check.dockerfile_python_installs(tmp_path) == []

    def test_a_suffixed_dockerfile_is_swept_too(self, tmp_path: Path) -> None:
        """`Dockerfile.e2e` is the same file with a different name."""
        (tmp_path / "Dockerfile.e2e").write_text("FROM python:3.14-slim\nRUN pip install selenium\n")

        assert check.dockerfile_python_installs(tmp_path) == ["Dockerfile.e2e:2"]

    @pytest.mark.parametrize(
        "instruction",
        [
            "RUN uv sync --locked --no-dev",
            # A lock-reading subcommand, not an index resolve. Matching these
            # would make the sweep report the locked form it exists to demand.
            "RUN poetry install --no-root",
            "RUN pdm install --frozen-lockfile",
            "COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /bin/uv",
        ],
    )
    def test_a_locked_or_unrelated_instruction_is_not_reported(self, tmp_path: Path, instruction: str) -> None:
        (tmp_path / "Dockerfile").write_text(f"FROM python:3.14-slim\n{instruction}\n")

        assert check.dockerfile_python_installs(tmp_path) == []


class TestTheClaimsAreNoWiderThanTheMeasurement:
    """#1491 review, W3: a claim wider than its instrument is invisible."""

    def test_the_finding_text_says_pep_621_and_not_every_python_tree(self) -> None:
        source = Path(check.__file__).read_text()

        assert "Every PEP 621 tree in this repository installs from a hash-bearing lock" in source
        assert "Every Python tree in this repository installs from a hash-bearing lock" not in source, (
            "the finding claims more than `lockless_python_trees()` measures: it reads pyproject.toml only, "
            "so three requirements.txt are outside it. Narrow the claim or widen the sweep — not neither."
        )

    def test_the_side_services_comment_says_pep_621_too(self) -> None:
        """The same sentence in the other place it is written down."""
        workflow = (_REPO_ROOT / ".github" / "workflows" / "side-services.yml").read_text()

        assert "like every other PEP 621 tree in" in workflow
        assert "like every other Python install in\n        # this repository. Until then" not in workflow


class TestTheLocklessRegisterStaysEmpty:
    def test_the_lockless_allowance_is_still_empty(self) -> None:
        """An allowance register is how a workaround becomes the design (CI spec §H)."""
        assert check.LOCKLESS_PYTHON_PROJECTS == (), (
            f"LOCKLESS_PYTHON_PROJECTS has grown back to {check.LOCKLESS_PYTHON_PROJECTS}. #1464 emptied it; "
            "a tree added here needs its argument in writing, not a line in a tuple."
        )

    def test_the_sweep_sees_every_python_tree_in_the_checkout(self) -> None:
        """Otherwise `lockless_python_trees() == []` could be green having looked at nothing."""
        swept = {
            path.relative_to(_REPO_ROOT).as_posix()
            for path in _REPO_ROOT.rglob("pyproject.toml")
            if not check._SWEEP_EXCLUDED.intersection(path.relative_to(_REPO_ROOT).parts)
        }
        assert swept == set(check.EXPECTED_PEP621_FILES), (
            f"the checkout holds {sorted(swept)} but EXPECTED_PEP621_FILES names "
            f"{sorted(check.EXPECTED_PEP621_FILES)}. A Python tree that is in one and not the other is "
            "either unobserved by Renovate or an expectation with nothing behind it."
        )


class TestTheUnchangedHealthyBodyIsGreen:
    """The positive control. Everything below is measured against this."""

    def test_no_alert(self, healthy_body: str) -> None:
        report = _report(healthy_body)
        assert report["alert"] is False, "findings: " + json.dumps(report["findings"], indent=2)

    def test_it_really_read_the_inventory(self, healthy_body: str) -> None:
        """Green because it looked, not because it found nothing to look at."""
        report = _report(healthy_body)
        assert set(report["pep621_files"]) >= set(check.EXPECTED_PEP621_FILES)
        assert "pip-compile" not in report["managers"]
        assert "poetry" not in report["managers"], (
            "the healthy state has NO poetry manager since #1464: it only ever extracted the two shared "
            "libraries, and it extracted them because they had no lock. A poetry that reappears means a "
            "lock was removed."
        )
        assert report["observed_files"]["npm"] == ["src/frontend/package.json", "tests/e2e/package.json"], (
            "green because it looked at the E2E suite too — `tests/e2e` sat behind an inherited "
            "`ignorePaths` rule until #1464 and its absence produced no signal at all."
        )
        assert len(report["managers"]) > 5, f"only {report['managers']} — suspiciously few managers parsed"

    def test_the_render_says_so(self, healthy_body: str) -> None:
        assert "healthy" in check.render(_report(healthy_body))


class TestTodaysRealBodyIsCorrectlyRed:
    """Issue #12 as of 2026-09-16 — before #1374 reached develop."""

    def test_it_alerts(self, todays_body: str) -> None:
        report = _report(todays_body)
        assert report["alert"] is True

    def test_it_names_poetry_on_the_locked_trees_and_the_missing_ones(self, todays_body: str) -> None:
        findings = "\n".join(_report(todays_body)["findings"])
        assert "`poetry` reads src/inference-service/pyproject.toml" in findings
        assert "`poetry` reads src/knowledge-service/pyproject.toml" in findings
        assert "docker/reranker-service/pyproject.toml" in findings

    def test_it_now_blames_poetry_for_the_two_shared_libraries_as_well(self, todays_body: str) -> None:
        """Tolerated until #1464, a finding after it — the libraries have locks now."""
        findings = "\n".join(_report(todays_body)["findings"])
        for library in ("src/libs/kp_vectordb/pyproject.toml", "src/libs/kp_errortracking/pyproject.toml"):
            assert f"`poetry` reads {library}" in findings, (
                f"{library} carries a uv.lock since #1464, so a second manager on it is #1371 verbatim — "
                "the same rule that already covered the four service images"
            )

    def test_it_names_the_side_service_requirements_files(self, todays_body: str) -> None:
        findings = "\n".join(_report(todays_body)["findings"])
        for requirements in (
            "docker/embedding-service/requirements.txt",
            "docker/reranker-service/requirements.txt",
            "src/inference-service/requirements.txt",
            "src/knowledge-service/requirements.txt",
        ):
            assert requirements in findings, f"{requirements} is read by pip_requirements but not reported"

    def test_it_does_not_report_unrelated_requirements_files(self, todays_body: str) -> None:
        """`docs/` and `tools/rag-eval/` are other trees and deliberately untouched (#1374)."""
        findings = "\n".join(_report(todays_body)["findings"])
        assert "docs/requirements.txt" not in findings
        assert "tools/rag-eval/requirements.txt" not in findings


class TestThePre1464BodyIsNowCorrectlyRed:
    """The RED-FIRST proof for #1464, and it is a whole fixture rather than a flag.

    ``renovate_dashboard_expected_after_1374.md`` was the healthy state until
    #1464: two shared libraries under ``poetry`` with no lock, and no ``tests/e2e``
    anywhere. Every rule this change adds has to turn exactly that body red, and
    each for its own named reason — otherwise the new green fixture certifies
    only that a fixture was written to match a checker.
    """

    def test_it_alerts(self, pre_1464_body: str) -> None:
        assert _report(pre_1464_body)["alert"] is True

    def test_it_names_the_two_libraries_as_missing_from_pep621(self, pre_1464_body: str) -> None:
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert "`pep621` does not list: src/libs/kp_vectordb/pyproject.toml" in findings
        assert "src/libs/kp_errortracking/pyproject.toml" in findings

    def test_it_names_poetry_on_both_libraries(self, pre_1464_body: str) -> None:
        """They are LOCKED trees now, so a second manager on them is #1371 verbatim."""
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert "`poetry` reads src/libs/kp_vectordb/pyproject.toml" in findings
        assert "`poetry` reads src/libs/kp_errortracking/pyproject.toml" in findings

    @pytest.mark.parametrize(
        ("manager", "package_file"),
        [
            ("npm", "tests/e2e/package.json"),
            ("dockerfile", "tests/e2e/Dockerfile"),
        ],
    )
    def test_it_names_every_unobserved_e2e_manifest(self, pre_1464_body: str, manager: str, package_file: str) -> None:
        """An ignored path emits nothing at all; this is the only side it is visible from.

        The Python manifest is no longer in this list because #1509 replaced it:
        ``tests/e2e/requirements.txt`` became a ``pyproject.toml`` with a lock,
        so its tripwire is :data:`check.EXPECTED_PEP621_FILES` — asserted by
        :meth:`test_it_names_the_two_libraries_as_missing_from_pep621` below,
        which now also names it.
        """
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert f"`{manager}` does not read {package_file}" in findings

    def test_it_also_names_the_e2e_tree_as_missing_from_pep621(self, pre_1464_body: str) -> None:
        """The pre-#1464 body predates the E2E lock too (#1509)."""
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert "tests/e2e/pyproject.toml" in findings

    def test_it_is_red_for_exactly_the_reasons_this_change_closes(self, pre_1464_body: str) -> None:
        """No stray extra finding — otherwise the fixture is describing a second defect."""
        assert len(_report(pre_1464_body)["findings"]) == 5, _report(pre_1464_body)["findings"]


class TestThePre1509BodyIsNowCorrectlyRed:
    """The RED-FIRST proof for #1509's inventory half, as a whole fixture.

    ``renovate_dashboard_expected_after_1464.md`` was the healthy state until
    #1509: ``tests/e2e/requirements.txt`` under ``pip_requirements`` and no
    ``tests/e2e/pyproject.toml`` anywhere. Locking that tree has to turn exactly
    that body red, and for its own two reasons — the tree missing from
    ``pep621``, and a second manager sitting inside what is now a LOCKED tree
    (#1371 verbatim). Without this the new green fixture would certify only that
    a fixture was written to match a checker.

    The FILESYSTEM half of #1509 — the unhashed-requirements sweep and the
    Dockerfile sweep — cannot be proven from a fixture: both read the real
    checkout, which this change fixes. Their red-first proof is in
    :class:`TestUnhashedInstallsAreAFindingNow` and
    :class:`TestDockerfilesMustNotInstallPythonOutsideALock`, against a
    constructed tree.
    """

    @pytest.fixture
    def pre_1509_body(self) -> str:
        return _PRE_1509.read_text()

    def test_it_alerts(self, pre_1509_body: str) -> None:
        assert _report(pre_1509_body)["alert"] is True

    def test_it_names_the_e2e_tree_as_missing_from_pep621(self, pre_1509_body: str) -> None:
        findings = "\n".join(_report(pre_1509_body)["findings"])
        assert "`pep621` does not list: tests/e2e/pyproject.toml" in findings

    def test_it_names_pip_requirements_inside_the_now_locked_e2e_tree(self, pre_1509_body: str) -> None:
        findings = "\n".join(_report(pre_1509_body)["findings"])
        assert "`pip_requirements` reads tests/e2e/requirements.txt" in findings

    def test_it_is_red_for_exactly_those_two_reasons(self, pre_1509_body: str) -> None:
        assert len(_report(pre_1509_body)["findings"]) == 2, _report(pre_1509_body)["findings"]


class TestInjectedRepositoryProblems:
    """The `⚠️ WARN: pip-compile error` line, put back where nobody read it."""

    @staticmethod
    def _with_problems(body: str, *lines: str) -> str:
        block = "## Repository problems\n\nThese problems occurred while renovating this repository.\n\n"
        block += "".join(f"-   {line}\n" for line in lines)
        block += "\n"
        return body.replace("## Detected Dependencies", block + "## Detected Dependencies", 1)

    def test_a_warn_line_alerts(self, healthy_body: str) -> None:
        body = self._with_problems(healthy_body, "`WARN: pip-compile error`")
        report = _report(body)
        assert report["alert"] is True
        assert any("pip-compile error" in finding for finding in report["findings"])

    def test_an_error_line_alerts(self, healthy_body: str) -> None:
        body = self._with_problems(healthy_body, "`ERROR: Failed to look up dependency`")
        assert _report(body)["alert"] is True

    def test_the_line_is_quoted_verbatim(self, healthy_body: str) -> None:
        """Paraphrasing a Renovate diagnostic loses the only clue it carries."""
        body = self._with_problems(healthy_body, "`WARN: Package lookup failures` (`some-package`)")
        report = _report(body)
        assert any("`WARN: Package lookup failures` (`some-package`)" in f for f in report["findings"])

    def test_a_problems_section_without_a_severity_does_not_alert(self, healthy_body: str) -> None:
        """Renovate writes prose in that section too; only WARN/ERROR is a finding."""
        body = self._with_problems(healthy_body, "Renovate had nothing of note to report.")
        assert _report(body)["alert"] is False

    def test_a_warn_mentioned_outside_the_section_is_ignored(self, healthy_body: str) -> None:
        """Otherwise a pull-request title containing 'WARN' would alert forever."""
        body = _inject(
            healthy_body,
            "## Detected Dependencies",
            "## Open\n\n - [ ] chore(deps): update WARN-detector to v2\n\n## Detected Dependencies",
        )
        assert _report(body)["alert"] is False


class TestInjectedInventoryDrift:
    """One injected defect at a time, each red for its own reason."""

    def test_poetry_reaching_into_a_locked_tree_alerts(self, healthy_body: str) -> None:
        """#1371 verbatim: a second manager on a tree that has a lock."""
        body = _inject(
            healthy_body,
            "<details><summary>pre-commit (1)</summary>",
            "<details><summary>poetry (1)</summary>\n<blockquote>\n\n"
            "<details><summary>src/backend/pyproject.toml (1)</summary>\n\n - `fastapi >=0.115.0`\n\n"
            "</details>\n\n</blockquote>\n</details>\n\n"
            "<details><summary>pre-commit (1)</summary>",
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("`poetry` reads src/backend/pyproject.toml" in f for f in report["findings"])

    def test_pip_compile_reappearing_alerts(self, healthy_body: str) -> None:
        """The manager whose six silent weeks this whole lane exists for."""
        body = _inject(
            healthy_body,
            "<details><summary>pre-commit (1)</summary>",
            "<details><summary>pip-compile (1)</summary>\n<blockquote>\n\n"
            "<details><summary>src/backend/requirements.txt (1)</summary>\n\n - `fastapi ==0.115.0`\n\n"
            "</details>\n\n</blockquote>\n</details>\n\n"
            "<details><summary>pre-commit (1)</summary>",
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("`pip-compile` appears in the inventory" in f for f in report["findings"])

    @pytest.mark.parametrize("dropped", check.EXPECTED_PEP621_FILES)
    def test_a_missing_side_service_file_alerts(self, healthy_body: str, dropped: str) -> None:
        """Every one of the five, not just a representative — that is the point of a strong expectation."""
        body = _inject(healthy_body, f"<summary>{dropped} (", "<summary>some/other/pyproject.toml (")
        report = _report(body)
        assert report["alert"] is True
        assert any(dropped in f and "does not list" in f for f in report["findings"]), report["findings"]

    def test_an_unknown_pep621_file_alerts(self, healthy_body: str) -> None:
        """A new Python tree must be declared, not absorbed silently."""
        body = _inject(
            healthy_body,
            "<details><summary>src/backend/pyproject.toml (42)</summary>",
            "<details><summary>src/brand-new-service/pyproject.toml (1)</summary>\n\n - `fastapi >=0.1`\n\n"
            "</details>\n\n<details><summary>src/backend/pyproject.toml (42)</summary>",
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("does not know about" in f for f in report["findings"])

    def test_a_reappearing_side_service_requirements_file_alerts(self, healthy_body: str) -> None:
        body = _inject(
            healthy_body,
            "<details><summary>docs/requirements.txt (53)</summary>",
            "<details><summary>src/knowledge-service/requirements.txt (3)</summary>\n\n - `fastapi >=0.1`\n\n"
            "</details>\n\n<details><summary>docs/requirements.txt (53)</summary>",
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("src/knowledge-service/requirements.txt" in f for f in report["findings"])

    def test_pep621_vanishing_entirely_alerts_loudly(self, healthy_body: str) -> None:
        """The exact shape of the six silent weeks."""
        body = _inject(healthy_body, "<summary>pep621 (8)</summary>", "<summary>pep666 (8)</summary>")
        report = _report(body)
        assert report["alert"] is True
        assert any("absent from the inventory entirely" in f for f in report["findings"])

    def test_a_missing_lock_on_disk_alerts(self, healthy_body: str, tmp_path: Path) -> None:
        """The one fact the dashboard cannot carry, so it is read from the checkout."""
        for package_file in check.EXPECTED_PEP621_FILES:
            target = tmp_path / package_file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("[project]\nname = 'x'\n")
        # Every tree but the backend gets a lock; the backend deliberately does not.
        for package_file in check.EXPECTED_PEP621_FILES[1:]:
            (tmp_path / package_file).with_name("uv.lock").write_text("version = 1\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["alert"] is True
        assert any("No uv.lock beside: src/backend/pyproject.toml" in f for f in report["findings"])
        assert report["locks_verified_on_disk"] == list(check.EXPECTED_PEP621_FILES[1:])


class TestTheBodyArrivesThroughAFile:
    """The ~900-line body is passed by PATH, not as one env/argv string.

    ``MAX_ARG_STRLEN`` caps a single argument (and, in practice, a single
    environment entry) at 128 KiB on Linux. The dashboard body is ~30 KiB today
    and grows with every package file Renovate learns about, so the env route
    has a ceiling that would be reached on a day nothing in this repository
    changed — an ``E2BIG`` in a lane whose whole purpose is to notice silence.
    """

    def test_body_file_is_read_and_the_report_is_written(self, tmp_path: Path) -> None:
        body_file = tmp_path / "dashboard-body.md"
        body_file.write_text(_HEALTHY.read_text(), encoding="utf-8")
        report_path = tmp_path / "report.json"

        assert check.main(["--body-file", str(body_file), str(report_path)], repo_root=_REPO_ROOT) == 0

        written = json.loads(report_path.read_text())
        assert written["alert"] is False, f"the healthy fixture read from a file alerted: {written['findings']}"
        assert set(written["pep621_files"]) == set(check.EXPECTED_PEP621_FILES)

    def test_a_body_far_past_the_env_ceiling_still_goes_through(self, tmp_path: Path) -> None:
        """The ceiling the file route exists to clear, exercised rather than asserted in prose.

        The padding is plain prose placed BEFORE the first heading, so the parser
        sees the same sections — the point under test is the transport, not the
        grammar.
        """
        padding = ("Renovate prose that is not a heading and carries no WARN or ERROR token.\n") * 2000
        body = padding + _HEALTHY.read_text()
        assert len(body.encode()) > 128 * 1024, (
            "the padded body is smaller than MAX_ARG_STRLEN, so this test would pass through the env "
            "route as well and prove nothing about the file route"
        )

        body_file = tmp_path / "huge-dashboard-body.md"
        body_file.write_text(body, encoding="utf-8")
        report_path = tmp_path / "report.json"

        assert check.main(["--body-file", str(body_file), str(report_path)], repo_root=_REPO_ROOT) == 0
        assert json.loads(report_path.read_text())["alert"] is False

    def test_an_unreadable_body_file_is_undetermined_and_writes_no_report(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"
        with pytest.raises(check.DashboardError, match="could not be read"):
            check.main(["--body-file", str(tmp_path / "never-fetched.md"), str(report_path)], repo_root=_REPO_ROOT)
        assert not report_path.exists(), (
            "a report was written although the body file was never fetched — the workflow's issue step "
            "keys on that file's existence, so this would open an alert issue off a failed download"
        )

    def test_the_workflow_really_invokes_the_script_that_way(self) -> None:
        """The lane and this suite must reach the script through the SAME door.

        Without this, the tests above could certify a ``--body-file`` path that
        the workflow does not use — the recurring failure class here (a test that
        reaches the rule by a route production never takes).
        """
        workflow = (_REPO_ROOT / ".github" / "workflows" / "renovate-health.yml").read_text()
        assert "--body-file dashboard-body.md" in workflow, (
            "renovate-health.yml does not hand the body to check_renovate_dashboard.py by file path; the "
            "--body-file tests above would then measure a door nobody walks through"
        )
        assert "RENOVATE_DASHBOARD_BODY=" not in workflow, (
            "renovate-health.yml still builds RENOVATE_DASHBOARD_BODY from the body — that is the "
            "MAX_ARG_STRLEN route this change removed"
        )


class TestUndeterminedIsNeverClean:
    """NFR-018 §2 — a check that cannot decide must go red, not green."""

    def test_an_empty_body_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="empty"):
            _report("   \n  ")

    def test_a_body_without_the_detected_section_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="Detected Dependencies"):
            _report("# Some issue\n\nNothing to see here.\n")

    def test_an_empty_detected_section_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="no manager blocks"):
            _report("## Detected Dependencies\n\n(nothing)\n")

    def test_main_writes_no_report_when_undetermined(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"
        with pytest.raises(check.DashboardError):
            check.main([str(report_path)], body="", repo_root=_REPO_ROOT)
        assert not report_path.exists(), (
            "a report was written for an undetermined run — the workflow's issue step keys on the file's "
            "existence, so this would open an alert issue off a parse failure"
        )

    def test_main_writes_the_report_and_exits_zero_on_drift(self, todays_body: str, tmp_path: Path) -> None:
        """Drift is reported through the ISSUE, not through a red run (operator decision)."""
        report_path = tmp_path / "report.json"
        assert check.main([str(report_path)], body=todays_body, repo_root=_REPO_ROOT) == 0
        written = json.loads(report_path.read_text())
        assert written["alert"] is True
        assert written["findings"]
