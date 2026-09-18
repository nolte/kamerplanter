"""#1464 — the permanent falsifier for "the shared libraries install hash-verified".

**What this is.** ``test_lock_hash_verification.py`` beside this file does for
``src/backend/uv.lock`` what this one does for the two shared libraries,
``src/libs/kp_vectordb`` and ``src/libs/kp_errortracking``. Read that module
first: it carries the full argument, including the two measured facts this file
depends on and does not re-derive at length —

* ``uv lock --check`` verifies **no hashes at all**; only ``uv sync --locked``
  does, which is why a lock gate is two commands and not one;
* a tamper test that alters an **sdist** hash of a package installed from its
  **wheel** passes while proving nothing (#1377). Hence the positive control
  below asserts the target really appears in ``uv sync``'s *installed* list.

**Why the libraries needed their own falsifier.** Until #1464 they had no lock at
all: ``side-services.yml`` ran ``pip install -e '.[dev]'`` for ``kp_vectordb``,
the one unhashed Python install left in the repository, and
``check_renovate_dashboard.py`` carried both trees on an allowance list named
``LOCKLESS_PYTHON_PROJECTS``. The reason recorded for the allowance was that a
shared library has no image of its own and therefore nothing that "installs from
a lock". That is true about images and false about installs: the CI job installs
these packages on a runner exactly like the four service images #1374 locked, so
NFR-009 §2.3 applies to it in the same words.

**A lock that is never verified is a file, not a gate.** Adding two ``uv.lock``
would satisfy every check in this repository — the health check counts managers
and the presence of a lock beside a pyproject, not whether its hashes bind. This
file is what makes the new locks load-bearing: it tampers with a copy and
requires the install to refuse it, per library, naming the library in the
failure. Traces to #1464 (no TC-ID: a dependency gate is not a user-facing case).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_ZEROED_HASH = "sha256:" + "0" * 64

# Errors that mean "the runner cannot do this", not "the lock is fine".
_NOT_A_HASH_VERDICT = ("required-version", "No interpreter found", "Network", "offline")


@dataclass(frozen=True)
class Library:
    """A locked shared library and the package whose wheel hash gets altered."""

    #: Path from the checkout root — the same string the health check enumerates.
    directory: str
    #: The tamper target. Chosen, not picked at random, and every property is
    #: asserted below rather than trusted: installed by the exact `uv sync`
    #: invocation CI runs, exactly one wheel, no environment marker, pure Python.
    target: str
    #: Where the target is declared, so a dependency drop reddens this file
    #: instead of quietly weakening it. `kp_errortracking` declares NO runtime
    #: dependencies on purpose (it degrades to a no-op without sentry-sdk), so
    #: its target can only come from the dev extra — which is what CI installs.
    declared_in: str

    def __str__(self) -> str:  # pragma: no cover — pytest ids only
        return self.directory


_LIBRARIES = (
    Library(directory="src/libs/kp_vectordb", target="structlog", declared_in="dependencies"),
    Library(directory="src/libs/kp_errortracking", target="sentry-sdk", declared_in="dev"),
)

#: What `task deps:sync:kp-*` and side-services.yml run, minus the project itself
#: (a copied tree has no package to build). `--extra dev` is not decoration: it
#: is the dependency set CI installs, and for kp_errortracking it is the ONLY
#: one — `[project].dependencies` is empty, so without it `uv sync` would install
#: nothing and any tamper would be unreachable.
_SYNC = ["sync", "--locked", "--no-install-project", "--extra", "dev"]


def _uv_version() -> str | None:
    """The version of the ``uv`` on PATH, or None when there is none."""
    if shutil.which("uv") is None:
        return None
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", result.stdout)
    return match.group(1) if match else None


def _raw_required_version(library: Library) -> object:
    """``[tool.uv].required-version`` exactly as that library's pyproject spells it."""
    pyproject = _REPO_ROOT / library.directory / "pyproject.toml"
    return tomllib.loads(pyproject.read_text()).get("tool", {}).get("uv", {}).get("required-version")


def _required_uv_version(library: Library) -> str | None:
    """The pin as a bare version when it is an ``==`` pin, else None."""
    pin = _raw_required_version(library)
    return pin[2:].strip() if isinstance(pin, str) and pin.startswith("==") else None


def _why_the_falsifier_cannot_run() -> str | None:
    """The skip reason, or None when the falsifier can actually measure something.

    The two libraries pin the same uv as the backend and the four service images
    — one toolchain, now eight readers — so a single check covers both. The
    ``TestEveryLibraryPinsTheSameUv`` case below is what keeps that true.
    """
    installed = _uv_version()
    if installed is None:
        return (
            "uv is not on PATH (or does not report a version). The hash-verification claim of "
            "NFR-009 §2.3 is therefore UNMEASURED for the shared libraries in this run — install uv "
            "(`astral-sh/setup-uv`, or `uvx --from 'uv==<pin>' uv`) to exercise it."
        )
    pins = {_required_uv_version(library) for library in _LIBRARIES} - {None}
    mismatched = sorted(pin for pin in pins if pin != installed)
    if mismatched:
        return (
            f"uv {installed} is on PATH but the shared libraries pin [tool.uv].required-version to "
            f"{mismatched}. `uv sync` in the copied tree would refuse on the version, not on the hash, "
            "so this run would go red for the wrong reason and a real hash defect would be "
            "indistinguishable from a toolchain mismatch."
        )
    return None


_SKIP_REASON = _why_the_falsifier_cannot_run()


def _copy_lock_into(library: Library, directory: Path) -> Path:
    """Copy the two files uv reads into *directory*. The checkout is never written."""
    source = _REPO_ROOT / library.directory
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copy2(source / name, directory / name)
    return directory / "uv.lock"


def _uv(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"}}
    # An explicit bound: an unbounded subprocess turns a hung resolver into a
    # job-level timeout with no attribution.
    return subprocess.run(["uv", *args], cwd=cwd, capture_output=True, text=True, timeout=900, env=env)


def _tamper(library: Library, lock: Path) -> str:
    """Replace the sha256 of *one wheel* of the library's target. Returns the old hash."""
    text = lock.read_text()

    entry = re.search(
        rf'^\[\[package\]\]\nname = "{re.escape(library.target)}"\n(?P<body>(?:.*\n)*?)(?=\n\[\[package\]\]|\Z)',
        text,
        re.MULTILINE,
    )
    assert entry is not None, (
        f"{library.target} has no [[package]] entry in {library.directory}/uv.lock. The falsifier has lost "
        "its subject — pick another installed, unmarked, pure-Python dependency and say so here."
    )
    body = entry.group("body")

    wheels = re.search(r"^wheels = \[\n(?P<lines>(?:.*\n)*?)\]$", body, re.MULTILINE)
    assert wheels is not None, f"{library.target} has no `wheels = [...]` block — it would install from an sdist"
    wheel_lines = [line for line in wheels.group("lines").splitlines() if line.strip()]
    assert len(wheel_lines) == 1, (
        f"{library.target} now has {len(wheel_lines)} wheels in {library.directory}/uv.lock; this file assumes "
        "exactly one so that the altered line is certainly the one installed on this platform (the #1377 "
        "sdist trap in another shape)"
    )
    assert "marker = " not in wheel_lines[0], f"{library.target}'s wheel is marker-gated and may not install here"

    old_hash = re.search(r'hash = "(sha256:[0-9a-f]{64})"', wheel_lines[0])
    assert old_hash is not None, f"{library.target}'s wheel entry carries no sha256 — nothing to falsify"

    tampered_line = wheel_lines[0].replace(old_hash.group(1), _ZEROED_HASH)
    assert text.count(wheel_lines[0]) == 1
    lock.write_text(text.replace(wheel_lines[0], tampered_line))
    return old_hash.group(1)


@pytest.fixture(scope="module", params=_LIBRARIES, ids=str)
def library(request: pytest.FixtureRequest) -> Library:
    return request.param


@pytest.fixture(scope="module")
def positive_control(library: Library, tmp_path_factory: pytest.TempPathFactory) -> subprocess.CompletedProcess[str]:
    """``uv sync --locked --no-install-project --extra dev`` on an UNTOUCHED copy."""
    if _SKIP_REASON:
        pytest.skip(_SKIP_REASON)
    directory = tmp_path_factory.mktemp(f"uv-lock-control-{Path(library.directory).name}")
    _copy_lock_into(library, directory)
    return _uv(_SYNC, directory)


class TestEveryLibraryIsLockedAtAll:
    """The precondition #1464 created, asserted where a removal would be loud."""

    @pytest.mark.parametrize("candidate", _LIBRARIES, ids=str)
    def test_the_library_has_a_lock_beside_its_pyproject(self, candidate: Library) -> None:
        lock = _REPO_ROOT / candidate.directory / "uv.lock"
        assert lock.is_file(), (
            f"{candidate.directory}/uv.lock is gone. Without it the install in side-services.yml falls back "
            "to an unhashed resolve and `rangeStrategy: update-lockfile` has nothing to update — the state "
            "#1464 closed. Regenerate with `uv lock` in that directory."
        )

    @pytest.mark.parametrize("candidate", _LIBRARIES, ids=str)
    def test_every_locked_package_carries_a_hash(self, candidate: Library) -> None:
        """ "Hash-complete" is the property, and it is cheap to measure directly."""
        lock = (_REPO_ROOT / candidate.directory / "uv.lock").read_text()
        root_name = tomllib.loads((_REPO_ROOT / candidate.directory / "pyproject.toml").read_text())["project"]["name"]
        hashless = []
        for chunk in lock.split("[[package]]")[1:]:
            name = re.search(r'name = "([^"]+)"', chunk)
            if name and name.group(1) != root_name and 'hash = "sha256:' not in chunk:
                hashless.append(name.group(1))
        assert hashless == [], (
            f"{candidate.directory}/uv.lock records no hash for {hashless}. A lock is a gate only for the "
            "packages whose bytes it pins; the project itself is the sole legitimate exception (it is built "
            "from the checkout, not downloaded)."
        )


class TestEveryLibraryPinsTheSameUv:
    """A floor instead of an ``==`` pin switches the version gate off silently."""

    @pytest.mark.parametrize("candidate", _LIBRARIES, ids=str)
    def test_required_version_is_an_exact_equality_specifier(self, candidate: Library) -> None:
        pin = _raw_required_version(candidate)
        assert isinstance(pin, str) and pin.startswith("=="), (
            f"{candidate.directory}/pyproject.toml pins [tool.uv].required-version to {pin!r}, which is not "
            "an exact `==` specifier. `astral-sh/setup-uv` with `version-file:` then installs whatever "
            "satisfies the floor, the `uv toolchain` customManager in renovate.json5 stops matching, and "
            "_why_the_falsifier_cannot_run() above stops checking that the uv on PATH is the uv the "
            "repository locks with. Loosen this only together with all three."
        )

    def test_the_libraries_pin_the_same_uv_as_the_backend(self) -> None:
        """One toolchain, eight readers — a second pin is the #1296 class."""
        backend = tomllib.loads((_REPO_ROOT / "src" / "backend" / "pyproject.toml").read_text())
        expected = backend["tool"]["uv"]["required-version"]
        divergent = {
            candidate.directory: _raw_required_version(candidate)
            for candidate in _LIBRARIES
            if _raw_required_version(candidate) != expected
        }
        assert divergent == {}, (
            f"src/backend/pyproject.toml pins uv {expected!r}; these disagree: {divergent}. Renovate's "
            "`uv toolchain` group moves every reference in one pull request, so a divergence means a "
            "reference it does not know about — the lock would be written by a different resolver than "
            "the one that installs from it (#1296)."
        )


class TestThePositiveControlReachesTheTamperedWheel:
    """Without this, a red tamper run proves nothing about the hash line."""

    def test_the_untouched_lock_installs_cleanly(
        self, library: Library, positive_control: subprocess.CompletedProcess[str]
    ) -> None:
        assert positive_control.returncode == 0, (
            f"The UNTOUCHED lock of {library.directory} failed to install, so the tamper test below cannot "
            f"attribute its failure to the altered hash.\nstderr:\n{positive_control.stderr}"
        )

    def test_the_target_package_is_actually_installed_from_its_wheel(
        self, library: Library, positive_control: subprocess.CompletedProcess[str]
    ) -> None:
        """The anti-vacuum check. #1377's first tamper test altered a line nothing read."""
        installed = {
            line.strip()[2:].split("==")[0]
            for line in positive_control.stderr.splitlines()
            if line.strip().startswith("+ ")
        }
        assert installed, (
            f"`uv sync` reported no installed packages at all for {library.directory}, so 'the tampered "
            f"wheel is installed' is unverifiable.\nstderr:\n{positive_control.stderr}"
        )
        assert library.target in installed, (
            f"{library.target} is NOT among the {len(installed)} packages `{' '.join(_SYNC)}` installs in "
            f"{library.directory}, so altering its hash would falsify nothing — exactly the defect that "
            "made the first hash-tamper test in #1377 vacuous. Pick a package that is installed."
        )

    def test_the_target_is_declared_by_the_library_itself(self, library: Library) -> None:
        pyproject = tomllib.loads((_REPO_ROOT / library.directory / "pyproject.toml").read_text())
        project = pyproject["project"]
        declared = (
            project["dependencies"]
            if library.declared_in == "dependencies"
            else project["optional-dependencies"][library.declared_in]
        )
        names = {re.split(r"[\[><=~!;\s]", spec, maxsplit=1)[0] for spec in declared}
        assert library.target in names, (
            f"{library.target} is no longer declared in {library.directory}/pyproject.toml under "
            f"{library.declared_in!r}. It may still be installed transitively, but the falsifier should "
            "target something the library itself declares, so a dependency drop makes this file red rather "
            "than quietly weaker."
        )


class TestUvSyncLockedRejectsATamperedWheelHash:
    """The claim NFR-009 §2.3 makes, per library, under test."""

    def test_an_altered_wheel_hash_fails_the_install(self, library: Library, tmp_path: Path) -> None:
        if _SKIP_REASON:
            pytest.skip(_SKIP_REASON)
        lock = _copy_lock_into(library, tmp_path)
        original = _tamper(library, lock)

        result = _uv(_SYNC, tmp_path)

        assert result.returncode != 0, (
            f"`uv sync --locked` INSTALLED a {library.directory} lock whose wheel hash had been replaced by "
            "zeroes. The 'installs are hash-verified' claim in NFR-009 §2.3/§6.1 is false as written for "
            f"this library and its lane is not a gate.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

        combined = result.stdout + result.stderr
        for unrelated in _NOT_A_HASH_VERDICT:
            assert unrelated not in combined, (
                f"The run failed on {unrelated!r}, not on the hash. A red run for the wrong reason is not "
                f"evidence for the hash claim.\n{combined}"
            )
        assert "Hash mismatch" in combined, (
            "The run failed, but not with a hash verdict. Read the output before believing this gate: "
            f"the failure may be unrelated to the tamper.\n{combined}"
        )
        assert library.target in combined, f"The hash verdict does not name {library.target}\n{combined}"
        assert _ZEROED_HASH in combined, (
            f"uv did not echo the expected (tampered) hash, so it is not clear it read the altered line.\n{combined}"
        )
        assert original in combined, (
            "uv did not echo the hash it actually computed, so the mismatch cannot be attributed to the "
            f"substituted value.\n{combined}"
        )


class TestUvLockCheckAloneIsNotTheGuard:
    """Re-measured per library — the reason a lock gate is two commands, not one."""

    def test_uv_lock_check_does_not_notice_the_tampered_hash(self, library: Library, tmp_path: Path) -> None:
        if _SKIP_REASON:
            pytest.skip(_SKIP_REASON)
        lock = _copy_lock_into(library, tmp_path)
        _tamper(library, lock)

        result = _uv(["lock", "--check"], tmp_path)

        assert result.returncode == 0, (
            f"`uv lock --check` now rejects a tampered hash in {library.directory}. That is GOOD NEWS, not "
            "a defect — but this repository's comments (backend.yml 'Lock staleness', "
            ".taskfiles/backend.yaml `deps:check`, NFR-009 §6.1) all state the opposite as measured fact. "
            f"Re-measure, then update those comments and this test together.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def test_the_library_hash_falsifier_is_never_merely_skipped_in_ci() -> None:
    """A skip is an honest local outcome and an unacceptable one on a runner.

    The twin of the same test in ``test_lock_hash_verification.py``: everything
    above self-skips when uv is absent or mismatched, which is right on a
    contributor's machine and wrong in a pipeline, where the lane would report
    green having verified nothing (NFR-018 §2).
    """
    if not os.environ.get("CI"):
        pytest.skip(
            "not running in CI ($CI unset). "
            + (f"The falsifier above WOULD skip here: {_SKIP_REASON}" if _SKIP_REASON else "The falsifier runs here.")
        )
    assert _SKIP_REASON is None, (
        "The shared-library hash-verification falsifier skipped ON A RUNNER, so this lane reports green "
        "without having measured the claim it exists for. Give the job a `uv` matching "
        "[tool.uv].required-version (`astral-sh/setup-uv` with `version-file:`). Reason: " + _SKIP_REASON
    )
