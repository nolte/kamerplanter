"""#1383 — the permanent falsifier for "backend installs are hash-verified".

**The claim.** NFR-009 §2.3/§6.1: every artifact this project installs is checked
against the hash ``src/backend/uv.lock`` records, so two builds of one commit
install the same bytes and a substituted wheel fails the build.

**Why the claim needed a falsifier.** It had none. Two things were believed to
carry it and neither did:

1. ``uv lock --check`` verifies **no hashes at all** — it compares the lock
   against ``pyproject.toml`` and the lock's own metadata, nothing else. Measured
   again here, on uv 0.12.15, by :class:`TestUvLockCheckAloneIsNotTheGuard`: a
   lock with a wheel hash replaced by zeroes still exits 0.
2. The first hash-tamper test written for #1377 altered an **sdist** hash. The
   backend installs that package from its **wheel**, so nothing ever read the
   line the test changed. It passed, it proved nothing, and it is the reason
   :class:`TestThePositiveControlReachesTheTamperedWheel` exists: the positive
   control asserts the tampered package appears in ``uv sync``'s *installed*
   list, so "the test touched a line that is actually consumed" is measured
   rather than assumed.

**What this file does.** Copies ``pyproject.toml`` + ``uv.lock`` into a temp
directory (never touching the checkout), alters the sha256 of one wheel, and
asserts ``uv sync --locked --no-install-project`` exits non-zero naming a hash
mismatch — with a positive control on an untouched copy of the same two files.

**Cost, measured on 2026-09-16 with a warm uv cache (uv 0.12.15):** positive
control 0.09 s for 103 installed packages, tamper run 0.02 s (uv fails fast, so
nothing is installed at all). Neither run needs the network when the shared uv
cache already holds the artifacts — the positive control was re-measured with
``--offline`` and still exited 0. ``--offline`` is deliberately **not** passed in
the test: on a cold cache (a fresh runner, before the job's own
``uv sync --locked --no-install-project`` step has populated it) it would turn an
ordinary download into a hard failure that says "offline" instead of what is
wrong. The lanes that run this — ``backend.yml``'s ``Lock staleness`` and
``lint-test`` jobs, ``backend-guards.yml`` — all sync the same lock in an earlier
step, so the cache is warm by the time pytest gets here.

**Skipping is loud, and impossible in CI.** Without a matching ``uv`` on PATH the
tamper run would fail for the wrong reason, so the file skips with the reason
spelled out — and
``test_the_hash_falsifier_is_never_merely_skipped_in_ci`` fails the build if that
skip ever fires on a runner, which is the difference between "green" and
"green having measured nothing". Traces to #1383/#1377 (no TC-ID: a dependency
gate is not a user-facing case).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_BACKEND = _REPO_ROOT / "src" / "backend"
_PYPROJECT = _BACKEND / "pyproject.toml"
_LOCK = _BACKEND / "uv.lock"

# The package whose wheel hash gets altered. Chosen, not picked at random:
#
#   * it is a DIRECT dependency of the backend (asserted below), so it is in the
#     default dependency set `uv sync --no-install-project` installs;
#   * its lock entry carries exactly one wheel and no environment marker, so
#     "installed on the runner" does not depend on the platform;
#   * it is pure Python, so the wheel is what gets used — there is no
#     sdist-build path that could bypass the line under test (the #1377 trap).
#
# All three properties are checked by the tests rather than trusted, so this
# file goes red with a readable reason if a future lock stops satisfying them.
_TAMPER_TARGET = "structlog"

_ZEROED_HASH = "sha256:" + "0" * 64


def _uv_version() -> str | None:
    """The version of the ``uv`` on PATH, or None when there is none."""
    if shutil.which("uv") is None:
        return None
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", result.stdout)
    return match.group(1) if match else None


def _raw_required_version() -> object:
    """``[tool.uv].required-version`` exactly as pyproject.toml spells it."""
    return tomllib.loads(_PYPROJECT.read_text()).get("tool", {}).get("uv", {}).get("required-version")


def _required_uv_version() -> str | None:
    """``[tool.uv].required-version`` as a bare version, when it is an ``==`` pin.

    Returning None for anything else is a SILENT degradation of this whole file:
    the version gate in :func:`_why_the_falsifier_cannot_run` stops comparing,
    and the tamper run can then execute under a uv that is not the one the
    repository installs from. It is tolerated here only because
    :class:`TestTheRequiredVersionIsStillAnExactPin` turns the same condition
    into a RED test with the full consequence spelled out — see
    ``tests/unit/guards/test_uv_pin_is_single.py`` for the two other readers that
    degrade at the same moment.
    """
    pin = _raw_required_version()
    if isinstance(pin, str) and pin.startswith("=="):
        return pin[2:].strip()
    return None


class TestTheRequiredVersionIsStillAnExactPin:
    """A floor instead of an ``==`` pin switches three readers off at once."""

    def test_required_version_is_an_exact_equality_specifier(self) -> None:
        pin = _raw_required_version()
        assert isinstance(pin, str) and pin.startswith("=="), (
            f"src/backend/pyproject.toml pins [tool.uv].required-version to {pin!r}, which is not an exact "
            "`==` specifier. Three readers degrade silently on anything else and NONE of them goes red on "
            "its own: (1) the `uv toolchain` customManager in renovate.json5 matches "
            '`required-version = "==(?<currentValue>...)"` and stops tracking the pin; (2) the coverage '
            "lane's install-command in backend.yml appends the specifier to the package name, so a floor "
            "installs the newest release of the day instead of the pinned one; (3) _required_uv_version() "
            "above returns None, so this falsifier stops checking that the uv on PATH is the uv the "
            "repository locks with. Loosen this only together with all three."
        )


def _why_the_falsifier_cannot_run() -> str | None:
    """The skip reason, or None when the falsifier can actually measure something."""
    installed = _uv_version()
    if installed is None:
        return (
            "uv is not on PATH (or does not report a version). The hash-verification claim of "
            "NFR-009 §2.3 is therefore UNMEASURED in this run — install uv "
            "(`astral-sh/setup-uv`, or `uvx --from 'uv==<pin>' uv`) to exercise it."
        )
    required = _required_uv_version()
    if required is not None and installed != required:
        return (
            f"uv {installed} is on PATH but src/backend/pyproject.toml pins "
            f"[tool.uv].required-version to =={required}. `uv sync` in the copied tree would refuse "
            "on the version, not on the hash, so this run would go red for the wrong reason and a "
            "real hash defect would be indistinguishable from a toolchain mismatch."
        )
    return None


_SKIP_REASON = _why_the_falsifier_cannot_run()

# Errors that mean "the runner cannot do this", not "the lock is fine".
_NOT_A_HASH_VERDICT = ("required-version", "No interpreter found", "Network", "offline")


def _copy_lock_into(directory: Path) -> Path:
    """Copy the two files uv reads into *directory*. The checkout is never written."""
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copy2(_BACKEND / name, directory / name)
    return directory / "uv.lock"


def _uv(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"}}
    # An explicit bound: an unbounded subprocess turns a hung resolver into a
    # job-level timeout with no attribution.
    return subprocess.run(["uv", *args], cwd=cwd, capture_output=True, text=True, timeout=900, env=env)


def _tamper(lock: Path) -> str:
    """Replace the sha256 of *one wheel* of the target package. Returns the old hash."""
    text = lock.read_text()

    # prose-permeable: tamper helper over a generated uv.lock: it must locate the exact bytes it writes back
    entry = re.search(
        rf'^\[\[package\]\]\nname = "{re.escape(_TAMPER_TARGET)}"\n(?P<body>(?:.*\n)*?)\n\[\[package\]\]',
        text,
        re.MULTILINE,
    )
    assert entry is not None, (
        f"{_TAMPER_TARGET} has no [[package]] entry in uv.lock. The falsifier has lost its subject — "
        "pick another direct, unmarked, pure-Python dependency and say so in the module docstring."
    )
    body = entry.group("body")

    wheels = re.search(r"^wheels = \[\n(?P<lines>(?:.*\n)*?)\]$", body, re.MULTILINE)
    assert wheels is not None, f"{_TAMPER_TARGET} has no `wheels = [...]` block — it would install from an sdist"
    wheel_lines = [line for line in wheels.group("lines").splitlines() if line.strip()]
    assert len(wheel_lines) == 1, (
        f"{_TAMPER_TARGET} now has {len(wheel_lines)} wheels; this file assumes exactly one so that the "
        "altered line is certainly the one installed on this platform (the #1377 sdist trap in another shape)"
    )
    assert "marker = " not in wheel_lines[0], f"{_TAMPER_TARGET}'s wheel is marker-gated and may not install here"

    old_hash = re.search(r'hash = "(sha256:[0-9a-f]{64})"', wheel_lines[0])
    assert old_hash is not None, f"{_TAMPER_TARGET}'s wheel entry carries no sha256 — nothing to falsify"

    tampered_line = wheel_lines[0].replace(old_hash.group(1), _ZEROED_HASH)
    # prose-permeable: same helper: the count proves the replacement is unambiguous before writing
    assert text.count(wheel_lines[0]) == 1
    lock.write_text(text.replace(wheel_lines[0], tampered_line))
    return old_hash.group(1)


@pytest.fixture(scope="module")
def positive_control(tmp_path_factory: pytest.TempPathFactory) -> subprocess.CompletedProcess[str]:
    """``uv sync --locked --no-install-project`` on an UNTOUCHED copy of the lock."""
    if _SKIP_REASON:
        pytest.skip(_SKIP_REASON)
    directory = tmp_path_factory.mktemp("uv-lock-control")
    _copy_lock_into(directory)
    return _uv(["sync", "--locked", "--no-install-project"], directory)


class TestThePositiveControlReachesTheTamperedWheel:
    """Without this, a red tamper run proves nothing about the hash line."""

    def test_the_untouched_lock_installs_cleanly(self, positive_control: subprocess.CompletedProcess[str]) -> None:
        assert positive_control.returncode == 0, (
            "The UNTOUCHED lock failed to install, so the tamper test below cannot attribute its failure "
            f"to the altered hash.\nstderr:\n{positive_control.stderr}"
        )

    def test_the_target_package_is_actually_installed_from_its_wheel(
        self, positive_control: subprocess.CompletedProcess[str]
    ) -> None:
        """The anti-vacuum check. #1377's first tamper test altered a line nothing read."""
        installed = {
            line.strip()[2:].split("==")[0]
            for line in positive_control.stderr.splitlines()
            if line.strip().startswith("+ ")
        }
        assert installed, (
            "`uv sync` reported no installed packages at all, so 'the tampered wheel is installed' is "
            f"unverifiable.\nstderr:\n{positive_control.stderr}"
        )
        assert _TAMPER_TARGET in installed, (
            f"{_TAMPER_TARGET} is NOT among the {len(installed)} packages `uv sync --no-install-project` "
            "installs, so altering its hash would falsify nothing — exactly the defect that made the "
            "first hash-tamper test in #1377 vacuous. Pick a package that is installed."
        )

    def test_the_target_is_a_direct_backend_dependency(self) -> None:
        declared = tomllib.loads(_PYPROJECT.read_text())["project"]["dependencies"]
        names = {re.split(r"[\[><=~!;\s]", spec, maxsplit=1)[0] for spec in declared}
        assert _TAMPER_TARGET in names, (
            f"{_TAMPER_TARGET} is no longer a direct dependency in src/backend/pyproject.toml. It may still "
            "be installed transitively, but the falsifier should target something the project itself "
            "declares, so a dependency drop makes this file red rather than quietly weaker."
        )


class TestUvSyncLockedRejectsATamperedWheelHash:
    """The claim NFR-009 §2.3 makes, under test."""

    def test_an_altered_wheel_hash_fails_the_install(self, tmp_path: Path) -> None:
        if _SKIP_REASON:
            pytest.skip(_SKIP_REASON)
        lock = _copy_lock_into(tmp_path)
        original = _tamper(lock)

        result = _uv(["sync", "--locked", "--no-install-project"], tmp_path)

        assert result.returncode != 0, (
            "`uv sync --locked` INSTALLED a lock whose wheel hash had been replaced by zeroes. "
            "The 'installs are hash-verified' claim in NFR-009 §2.3/§6.1 is false as written and the "
            f"lanes that rely on it are not gates.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
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
        assert _TAMPER_TARGET in combined, f"The hash verdict does not name {_TAMPER_TARGET}\n{combined}"
        assert _ZEROED_HASH in combined, (
            f"uv did not echo the expected (tampered) hash, so it is not clear it read the altered line.\n{combined}"
        )
        assert original in combined, (
            "uv did not echo the hash it actually computed, so the mismatch cannot be attributed to the "
            f"substituted value.\n{combined}"
        )


class TestUvLockCheckAloneIsNotTheGuard:
    """The measured reason the Lock staleness job runs two commands, not one."""

    def test_uv_lock_check_does_not_notice_the_tampered_hash(self, tmp_path: Path) -> None:
        if _SKIP_REASON:
            pytest.skip(_SKIP_REASON)
        lock = _copy_lock_into(tmp_path)
        _tamper(lock)

        result = _uv(["lock", "--check"], tmp_path)

        assert result.returncode == 0, (
            "`uv lock --check` now rejects a tampered hash. That is GOOD NEWS, not a defect — but this "
            "repository's comments (backend.yml 'Lock staleness', .taskfiles/backend.yaml `deps:check`, "
            "NFR-009 §6.1) all state the opposite as measured fact, and #1377's review turned on it. "
            "Re-measure, then update those comments and this test together.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def test_the_hash_falsifier_is_never_merely_skipped_in_ci() -> None:
    """A skip is an honest local outcome and an unacceptable one on a runner.

    Everything above self-skips when uv is absent or mismatched. That is right
    on a contributor's machine and wrong in a pipeline: the lane would report
    green having verified nothing, which is the shape NFR-018 §2 forbids. This
    test is the one that cannot skip on a runner.
    """
    if not os.environ.get("CI"):
        pytest.skip(
            "not running in CI ($CI unset). "
            + (f"The falsifier above WOULD skip here: {_SKIP_REASON}" if _SKIP_REASON else "The falsifier runs here.")
        )
    assert _SKIP_REASON is None, (
        "The hash-verification falsifier skipped ON A RUNNER, so this lane reports green without having "
        "measured the claim it exists for. Give the job a `uv` matching "
        "[tool.uv].required-version (`astral-sh/setup-uv` with `version-file:`). Reason: " + _SKIP_REASON
    )
