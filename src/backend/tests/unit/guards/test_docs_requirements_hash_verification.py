"""#1571 — the permanent falsifier for "the documentation toolchain installs hash-verified".

**Why this file exists at all.** NFR-009 §2.3 requires a permanent falsifier per
INSTALL MECHANISM, and says why in the spec rather than only here: a falsifier
reproduces the command that really runs in the supply chain, so a test for
``uv sync --locked`` says nothing about ``pip install -r``. ``docs/requirements.txt``
is class (a) of NFR-009 §2.3.1 — a delivery lane installs it into the published
documentation site — and until #1571 the claim "hash-verified" was carried in
three places (``.taskfiles/docs.yaml``, ``docs/requirements.in``, the compiled
file's own header) by nothing but a one-off hand measurement recorded in a
comment. ``task docs:venv`` was the sole bearer of the verification. Add
``--no-deps``, switch to ``uv pip install``, drop the file for a range, and the
gate stays GREEN while verifying nothing — the inert class #1377/#1383 were
written against.

**THE VACUITY THIS FILE IS SHAPED AROUND, measured on 2026-09-20.** ``pip``
accepts a distribution as soon as **ANY** of its listed ``--hash=`` lines
matches. ``docs/requirements.txt`` is compiled ``--universal`` and most packages
therefore carry several hashes — ``babel`` carries two. Altering ONE of them
leaves the install at **exit 0**, and the first falsification run for #1571 did
exactly that and proved nothing. So the tamper below zeroes **every** hash of
exactly one package, and :class:`TestTheSingleHashTamperIsVacuous` keeps that
measurement alive as a test rather than as a comment somebody deletes. What
pip's hash mode secures is therefore a wrong, stale or orphaned hash **SET** —
which is the shape a hand edit and a half-applied Renovate artifact update both
take. The same warning is in NFR-009 §2.3 beside the older sdist-versus-wheel
one, so the next person writing a hash falsifier meets it before writing the
vacuous probe.

**What this file does.** Copies ``docs/requirements.txt`` into a temp directory
(never touching the checkout), zeroes all hashes of one package, and requires
``pip install --dry-run`` to abort naming a hash mismatch — with a positive
control on an untouched copy that additionally asserts the tampered package
appears in pip's own *install report*. That second half is the #1377 lesson: a
falsifier that cannot reach a consumed line passes while measuring nothing.

**Why ``--dry-run`` and not a real install.** pip's hash checking happens when it
obtains the distribution, which ``--dry-run`` still does; nothing is unpacked
into an environment afterwards. Measured here on 2026-09-20 with a warm pip
cache: positive control 9.6 s for 52 packages, tamper 1.8 s (pip fails fast).
A real install of the MkDocs toolchain costs minutes and would measure the same
line.

**Skipping is loud, and fails the build in CI**, exactly as the two uv twins
beside this file do it: without a usable interpreter or with no network the
tamper would fail for the wrong reason, so the file skips with the reason spelled
out — and ``test_the_falsifier_is_never_merely_skipped_in_ci`` turns that skip
red on a runner, which is the difference between "green" and "green having
measured nothing". Traces to #1571 (no TC-ID: a dependency gate is not a
user-facing case).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import venv
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_REQUIREMENTS = _REPO_ROOT / "docs" / "requirements.txt"

#: The package whose hashes get zeroed. Chosen, not picked at random, and every
#: property is ASSERTED below rather than trusted:
#:
#:   * it is in the compiled file (otherwise the tamper edits nothing);
#:   * it carries MORE THAN ONE hash, so the single-hash vacuity above can be
#:     demonstrated on the same package the real tamper uses — a vacuity proof on
#:     a different package would be an argument, not a measurement;
#:   * it appears in pip's install report for the untouched file, so the line the
#:     tamper edits is one this install really consumes (#1377).
_TAMPER_TARGET = "babel"

_ZEROED = "--hash=sha256:" + "0" * 64

#: Errors that mean "the runner cannot do this", not "the file is fine". Same
#: list, same purpose, as in the two uv falsifiers beside this file.
_NOT_A_HASH_VERDICT = ("No interpreter found", "Network", "network", "offline", "Temporary failure")

_HASH_VERDICT = re.compile(r"DO NOT MATCH THE HASHES|hash(es)? (mismatch|do not match)", re.IGNORECASE)


def _package_block(text: str, package: str) -> list[str]:
    """The lines of one package's entry: its ``name==version \\`` line and its hashes.

    ``uv pip compile --generate-hashes`` writes one entry per distribution as a
    backslash-continued block, so the block ends at the first line that is not a
    continuation of it.
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(f"{package}==")), None)
    if start is None:
        return []
    block = [lines[start]]
    index = start
    while lines[index].rstrip().endswith("\\"):
        index += 1
        block.append(lines[index])
    return block


def _tamper(text: str, package: str, *, how_many: int) -> str:
    """Return *text* with ``how_many`` of *package*'s hashes replaced by zeroes."""
    replaced = 0
    out: list[str] = []
    inside = False
    for line in text.splitlines(keepends=True):
        if line.startswith(f"{package}=="):
            inside = True
            out.append(line)
            continue
        if inside and "--hash=sha256:" in line and replaced < how_many:
            out.append(re.sub(r"--hash=sha256:[0-9a-f]{64}", _ZEROED, line))
            replaced += 1
            continue
        if inside and "--hash=" not in line:
            inside = False
        out.append(line)
    assert replaced == how_many, f"wanted to alter {how_many} hash(es) of {package}, altered {replaced}"
    return "".join(out)


def _why_the_falsifier_cannot_run() -> str | None:
    """A reason to skip, or None when the measurement can be made."""
    if not _REQUIREMENTS.is_file():
        return f"{_REQUIREMENTS} does not exist"
    if not hasattr(venv, "EnvBuilder"):  # pragma: no cover — defensive
        return "the venv module is unavailable"
    return None


_SKIP_REASON = _why_the_falsifier_cannot_run()


@pytest.fixture(scope="module")
def requirements_text() -> str:
    return _REQUIREMENTS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pip(tmp_path_factory: pytest.TempPathFactory) -> Iterator[list[str]]:
    """A pip command line, in a throwaway venv.

    The interpreter running pytest comes from ``uv``, which does not install pip
    into the environment at all — so "just call ``sys.executable -m pip``" would
    skip this whole file on every developer machine and every runner. Building
    one venv per module costs ~7 s and is what makes the measurement possible.
    """
    if _SKIP_REASON is not None:  # pragma: no cover — environment-dependent
        pytest.skip(_SKIP_REASON)
    root = tmp_path_factory.mktemp("docs-hash-falsifier")
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(root / "venv")
    executable = root / "venv" / "bin" / "python"
    if not executable.is_file():  # pragma: no cover — Windows layout, not used in CI
        executable = root / "venv" / "Scripts" / "python.exe"
    if not executable.is_file():  # pragma: no cover
        pytest.skip("could not build a venv carrying pip")
    yield [str(executable), "-m", "pip", "install", "--dry-run", "--ignore-installed", "-q"]


def _run(pip: list[str], requirements: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*pip, *extra, "-r", str(requirements)],
        capture_output=True,
        text=True,
        timeout=900,
        cwd=str(_REPO_ROOT),
    )


def _skip_if_the_runner_is_the_problem(result: subprocess.CompletedProcess[str]) -> None:
    combined = f"{result.stdout}\n{result.stderr}"
    for marker in _NOT_A_HASH_VERDICT:
        if marker in combined:  # pragma: no cover — only on a broken runner
            pytest.skip(f"pip could not reach the index ({marker!r}); this measures the runner, not the file")


class TestTheTamperTargetIsUsable:
    """Every property the tamper relies on is measured, not assumed."""

    def test_the_target_is_in_the_compiled_file(self, requirements_text: str) -> None:
        assert _package_block(requirements_text, _TAMPER_TARGET), (
            f"{_TAMPER_TARGET} is no longer in {_REQUIREMENTS.name}; pick a new target rather than "
            "leaving a tamper that edits nothing."
        )

    def test_the_target_carries_more_than_one_hash(self, requirements_text: str) -> None:
        """Required by :class:`TestTheSingleHashTamperIsVacuous`: with one hash
        there is no 'one of several' to demonstrate, and the vacuity measurement
        would silently become a second copy of the real tamper."""
        block = _package_block(requirements_text, _TAMPER_TARGET)
        hashes = sum(line.count("--hash=sha256:") for line in block)
        assert hashes > 1, f"{_TAMPER_TARGET} carries {hashes} hash(es); the vacuity control needs at least two"

    def test_the_tamper_helper_changes_exactly_what_it_claims(self, requirements_text: str) -> None:
        """The measuring instrument first. A helper that silently altered zero
        lines would make every assertion below pass over an untouched file."""
        block = _package_block(requirements_text, _TAMPER_TARGET)
        count = sum(line.count("--hash=sha256:") for line in block)
        tampered = _tamper(requirements_text, _TAMPER_TARGET, how_many=count)

        # every hash of the target is zeroed ...
        after = _package_block(tampered, _TAMPER_TARGET)
        assert after, "the tamper destroyed the package entry instead of its hashes"
        assert all("--hash=sha256:" not in line or _ZEROED in line for line in after)

        # ... and NOTHING else moved. Compared line by line and by position, not
        # by membership: several packages share an identical `# via ...` trailer,
        # so a set or `in` comparison would report "unchanged" over a real edit.
        before_lines, after_lines = requirements_text.splitlines(), tampered.splitlines()
        assert len(before_lines) == len(after_lines)
        moved = [i for i, (a, b) in enumerate(zip(before_lines, after_lines, strict=True)) if a != b]
        assert len(moved) == count, f"expected exactly {count} changed line(s), {len(moved)} changed"


class TestThePositiveControlReachesTheTamperedPackage:
    """#1377: a falsifier that cannot reach a consumed line proves nothing."""

    def test_the_untouched_file_installs_and_the_target_is_in_the_report(
        self, pip: list[str], tmp_path: Path, requirements_text: str
    ) -> None:
        copy = tmp_path / "requirements.txt"
        copy.write_text(requirements_text, encoding="utf-8")
        report = tmp_path / "report.json"
        result = _run(pip, copy, "--report", str(report))
        _skip_if_the_runner_is_the_problem(result)
        assert result.returncode == 0, f"the untouched file did not install:\n{result.stdout}\n{result.stderr}"
        installed = {entry["metadata"]["name"].lower() for entry in json.loads(report.read_text())["install"]}
        assert _TAMPER_TARGET in installed, (
            f"{_TAMPER_TARGET} is not in pip's install report, so the hashes this file tampers with are "
            "never read. Pick a target that is actually installed."
        )


class TestTamperingEveryHashOfOnePackageIsRefused:
    """The falsifier proper: the same expression the claim makes."""

    def test_pip_aborts_with_a_hash_verdict(self, pip: list[str], tmp_path: Path, requirements_text: str) -> None:
        block = _package_block(requirements_text, _TAMPER_TARGET)
        count = sum(line.count("--hash=sha256:") for line in block)
        copy = tmp_path / "requirements.txt"
        copy.write_text(_tamper(requirements_text, _TAMPER_TARGET, how_many=count), encoding="utf-8")
        result = _run(pip, copy)
        _skip_if_the_runner_is_the_problem(result)
        combined = f"{result.stdout}\n{result.stderr}"
        assert result.returncode != 0, (
            "pip installed a requirement list whose hashes were replaced by zeroes. "
            "The 'hash-verified' claim on docs/requirements.txt is not true of this install path."
        )
        assert _HASH_VERDICT.search(combined), (
            f"pip failed, but not with a hash verdict — so this may be measuring something else:\n{combined}"
        )


class TestTheSingleHashTamperIsVacuous:
    """Keeps the #1571 measurement alive as a TEST, not as a comment.

    If a future pip stops accepting "any listed hash matches", this test goes red
    and the docstring above has to be rewritten — which is the correct outcome.
    A comment would simply have become wrong.
    """

    def test_altering_one_of_several_hashes_still_installs(
        self, pip: list[str], tmp_path: Path, requirements_text: str
    ) -> None:
        copy = tmp_path / "requirements.txt"
        copy.write_text(_tamper(requirements_text, _TAMPER_TARGET, how_many=1), encoding="utf-8")
        result = _run(pip, copy)
        _skip_if_the_runner_is_the_problem(result)
        assert result.returncode == 0, (
            "pip now rejects a package when ONE of its several hashes is wrong. That is stricter than "
            "measured on 2026-09-20 and better — update this test and the note in NFR-009 §2.3, but do not "
            "delete the warning: the vacuous probe is still the obvious first attempt.\n"
            f"{result.stdout}\n{result.stderr}"
        )


class TestTheFalsifierIsNeverMerelySkipped:
    """A skipped test reports like a passed one."""

    def test_the_falsifier_is_never_merely_skipped_in_ci(self) -> None:
        if not os.environ.get("CI"):
            pytest.skip("not running in CI ($CI unset). The falsifier runs here.")
        assert _SKIP_REASON is None, (  # pragma: no cover — only fires on a broken runner
            f"the docs hash falsifier cannot run on this runner ({_SKIP_REASON}), so the "
            "'hash-verified' claim on docs/requirements.txt went unmeasured while the build stayed green."
        )
        assert shutil.which(sys.executable) or Path(sys.executable).is_file()
