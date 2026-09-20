"""#1602 — the free-form half of class (b): a ``pip install`` in a command block is bounded.

**The asymmetry this file removes.** NFR-009 §2.3.1 splits Python installs into
class (a) — reaches a delivered artefact, must be hash-bearing — and class (b) —
runner-only, output is a verdict, must carry an ``==`` pin or a bounded range.
Class (b) has two halves, and until this file only one of them was enforced:

* ``additional_dependencies:`` in ``.pre-commit-config.yaml`` — declarative YAML,
  held by ``test_pre_commit_dependency_bounds.py`` beside this file (#1572);
* ``pip install`` inside a ``run:``/``cmds:`` block — free-form shell, held by
  **nothing** until #1602.

The six sites that existed when this was written were all ``==``-pinned, so
nothing was broken. That is precisely the argument for the guard rather than
against it: their compliance was a property of who last edited them, not of the
repository. A class with one enforced half and one described half drifts back to
the enforced half's pre-guard state, and that is not a hypothesis here — it is
this repository's own history, where fifteen of seventeen
``additional_dependencies`` entries sat without a ceiling for years while the
paragraph describing the duty already existed.

**What it reads, and why as YAML.** ``.github/workflows/**``, ``.github/actions/**``
(composite actions carry ``run:`` too), ``.taskfiles/**`` and the root
``Taskfile.yaml``, parsed as YAML, considering only strings underneath a
COMMAND-BEARING KEY (:data:`_COMMAND_KEYS`). Parsing rather than grepping is
what makes the difference between an install and a mention: this repository's
workflow and taskfile trees discuss ``pip install`` in nine files, and in five of
them EVERY hit is prose — a ``#`` comment or a ``desc:`` block quoting a command
that used to be there. A line-based sweep would report those five as findings and
need five register entries to shut up, and a register that holds non-findings is
how an exception list becomes furniture. Under this parser they are not
exceptions; they are simply not sites.

**Unreadable is RED, not skipped.** A requirement string this file cannot parse
as PEP 508 — the shape a shell variable produces — fails unless
:data:`_EXEMPTIONS` records it with a reason. The alternative (skip what you
cannot read) is the vacuity that lets the next unpinned install past, and it
would look exactly as green as correctness.

WHAT THIS GUARD DOES NOT SEE. Named here, at the guard, and not only in the pull
request, because a sweep is only as complete as the spelling it matches:

* **a version in a shell variable** — ``pip install "uv$UV_SPEC"``. There is one
  such site (``backend.yml``); it is in :data:`_EXEMPTIONS` with its argument,
  and the shape is visible rather than skipped because the parse failure is a
  finding. What this file can NOT do is read the variable's value;
* **an install inside a called shell script** — a ``run: ./scripts/foo.sh`` whose
  script installs something. No sweep in this repository reads shell scripts for
  installs today. This is the largest hole and the cheapest one to fall into:
  moving a line from the ``run:`` block into a script silently leaves the guard;
* **a notebook magic** — ``%pip install`` in ``tools/rag-eval/rag_eval.ipynb``.
  Not YAML, so it is not in this file's reach at all. Inventory rather than
  finding: that tree ships nothing and is ``check_renovate_dashboard``'s argued
  exception already;
* **a pre-commit hook installing through its own ``entry:``** — the other
  guard's named gap, repeated here so the two halves describe the same hole;
* **an install in a container image referenced by a step** (``container:``,
  ``uses:`` of a third-party action). That is the image's Dockerfile, i.e.
  ``check_renovate_dashboard.dockerfile_python_installs``.

Traces to #1602 (no TC-ID: a dependency gate is not a user-facing case).
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

#: The trees scanned. WIDER than #1602 asks for (`.github/workflows/**` and
#: `.taskfiles/**`): composite actions and the root Taskfile carry exactly the
#: same `run:`/`cmds:` shapes, and leaving them out would have made the sweep's
#: reach depend on where somebody chose to put a step.
_SCANNED: tuple[str, ...] = (".github/workflows", ".github/actions", ".taskfiles", "Taskfile.yaml")

#: Keys whose value is a command (or a list of commands). Everything below such
#: a key is shell text; everything else in these files is configuration or prose.
#: `install-command:` is go-task/`setup-python`-style tooling input — `backend.yml`
#: passes one to the reusable coverage workflow — and is shell all the same.
_COMMAND_KEYS = frozenset({"run", "cmd", "cmds", "install-command", "install_command", "pre-install-command"})

#: An install invocation: an optional path or `%` magic, `pip`/`pip3`/`uv pip`,
#: then `install`. Also matches `python -m pip install` (the `pip install` tail
#: is what the pattern anchors on).
_INSTALL = re.compile(r"(?:^|[\s;&|(])%?(?:[\w./\\-]*/)?(?:pip[0-9.]*|uv\s+pip)\s+install\b")

#: Shell operators that end one command and start the next.
_SEGMENT_SEPARATOR = re.compile(r"&&|\|\||;|\n|(?<![|])\|(?![|])")

#: pip flags that consume the NEXT token, so that token is not a requirement.
_FLAGS_TAKING_A_VALUE = frozenset(
    {
        "-r",
        "--requirement",
        "-c",
        "--constraint",
        "-e",
        "--editable",
        "-i",
        "--index-url",
        "--extra-index-url",
        "-f",
        "--find-links",
        "-t",
        "--target",
        "--prefix",
        "--python",
        "--platform",
        "--abi",
        "--implementation",
        "--only-binary",
        "--no-binary",
        "--proxy",
        "--cache-dir",
        "--timeout",
        "--retries",
        "--root",
    }
)

#: Flags that turn the invocation into a REQUIREMENTS-LIST install. Such a site
#: names no version here; the list it points at is class (a) and is held by the
#: hash sweeps (`check_renovate_dashboard.unhashed_requirements_installs`,
#: `test_docs_requirements_hash_verification.py`). Delegating rather than
#: re-checking keeps one rule in one place.
_DELEGATING_FLAGS = frozenset({"-r", "--requirement"})


@dataclass(frozen=True)
class Exemption:
    """One install spec this file cannot read as PEP 508, with its argument."""

    #: Path relative to the checkout root.
    file: str
    #: The token EXACTLY as the command spells it.
    spec: str
    #: Why it is acceptable anyway. Read by a human; the machine-checkable part
    #: is that the site still exists (see :func:`stale_exemptions`).
    why: str


#: The register. It holds SPECS THIS FILE CANNOT READ, not sites somebody would
#: rather not fix — "runner-only" is what puts an install INTO class (b) and is
#: never also a reason to exempt it from class (b)'s own requirement (NFR-009
#: §2.3.1 calls that double use a circular argument, and it is how three entries
#: in `tools/rag-eval/requirements.txt` stayed unbounded until #1572).
#:
#: One entry on 2026-09-20. A register that grows is a rule dissolving, so
#: :func:`stale_exemptions` makes an entry that matches nothing RED: the entry
#: has to go when the site does, rather than outliving it as decoration.
_EXEMPTIONS: tuple[Exemption, ...] = (
    Exemption(
        file=".github/workflows/backend.yml",
        spec="uv$UV_SPEC",
        why=(
            "the version lives in a shell variable read from [tool.uv].required-version, so there is no literal "
            "to check here. The same command asserts INLINE that the spec is an exact `==` pin and fails the lane "
            "otherwise (#1296), and the pin itself is guarded by test_uv_pin_is_single.py and "
            "test_uv_pin_manager_covers_every_pin.py — three readers, none of them this one."
        ),
    ),
)


@dataclass(frozen=True)
class InstallSite:
    """One requirement named by one ``pip install`` in a command block."""

    #: Path relative to the checkout root.
    file: str
    #: The command segment the requirement was read out of, whitespace-collapsed.
    command: str
    #: The requirement token exactly as written, or ``None`` for a ``-r`` install.
    spec: str | None

    def __str__(self) -> str:  # pragma: no cover — pytest ids and messages only
        return f"{self.file}: {self.spec or '-r <list>'}  [{self.command[:120]}]"


def command_strings(document: Any) -> list[str]:
    """Every string underneath a command-bearing key, in document order."""
    found: list[str] = []

    def collect(node: Any) -> None:
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, list):
            for item in node:
                collect(item)
        elif isinstance(node, dict):
            for value in node.values():
                collect(value)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and key in _COMMAND_KEYS:
                    collect(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    return found


def scanned_files(repo_root: Path) -> tuple[Path, ...]:
    """Every YAML file in the scanned trees, sorted."""
    found: list[Path] = []
    for entry in _SCANNED:
        root = repo_root / entry
        if root.is_file():
            found.append(root)
        elif root.is_dir():
            found.extend(path for path in root.rglob("*") if path.suffix in (".yml", ".yaml") and path.is_file())
    return tuple(sorted(found))


def _requirement_tokens(segment: str) -> tuple[list[str], bool]:
    """``(requirement tokens, delegates_to_a_list)`` for one install segment.

    Raises:
        ValueError: when the segment cannot be tokenised — an unbalanced quote,
            usually templating. A caller must treat that as a finding rather
            than as "nothing to see": see the module docstring.
    """
    tokens = shlex.split(segment, posix=True)
    # drop everything up to and including the `install` verb
    for index, token in enumerate(tokens):
        if token == "install":
            tokens = tokens[index + 1 :]
            break
    requirements: list[str] = []
    delegates = False
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token.startswith("-"):
            flag = token.split("=", 1)[0]
            if flag in _DELEGATING_FLAGS:
                delegates = True
            if flag in _FLAGS_TAKING_A_VALUE and "=" not in token:
                skip_next = True
            continue
        requirements.append(token)
    return requirements, delegates


def install_sites(file: str, text: str) -> tuple[InstallSite, ...]:
    """Every requirement installed by a command block in *text*.

    A segment that cannot be tokenised yields a site whose ``spec`` is the raw
    segment, so it reaches :func:`unbounded_sites` as a finding.
    """
    document = yaml.safe_load(text)
    sites: list[InstallSite] = []
    for command in command_strings(document):
        for segment in _SEGMENT_SEPARATOR.split(command):
            if not _INSTALL.search(segment):
                continue
            collapsed = " ".join(segment.split())
            try:
                requirements, delegates = _requirement_tokens(segment)
            except ValueError:
                sites.append(InstallSite(file=file, command=collapsed, spec=collapsed))
                continue
            if delegates:
                sites.append(InstallSite(file=file, command=collapsed, spec=None))
                continue
            if not requirements:
                sites.append(InstallSite(file=file, command=collapsed, spec=collapsed))
                continue
            sites.extend(InstallSite(file=file, command=collapsed, spec=spec) for spec in requirements)
    return tuple(sites)


def _bounds(specifier: SpecifierSet) -> tuple[bool, bool]:
    """``(has_floor, has_ceiling)``; identical to the declarative half's reading."""
    has_floor = any(clause.operator in (">=", ">", "==", "===", "~=") for clause in specifier)
    has_ceiling = any(clause.operator in ("<=", "<", "==", "===", "~=") for clause in specifier)
    return has_floor, has_ceiling


def _is_exempt(site: InstallSite, exemptions: tuple[Exemption, ...]) -> bool:
    return any(exemption.file == site.file and exemption.spec == site.spec for exemption in exemptions)


def unbounded_sites(sites: tuple[InstallSite, ...], exemptions: tuple[Exemption, ...] = _EXEMPTIONS) -> list[str]:
    """Sites naming a requirement without an ``==`` pin or a bounded range."""
    offenders: list[str] = []
    for site in sites:
        if site.spec is None or _is_exempt(site, exemptions):
            continue
        try:
            requirement = Requirement(site.spec)
        except InvalidRequirement:
            offenders.append(
                f"{site} — not readable as a PEP 508 requirement (a shell variable? a path?). "
                "Pin it literally, or record it in _EXEMPTIONS with the reason."
            )
            continue
        if requirement.url is not None:
            offenders.append(f"{site} — installed from a URL; neither a pin nor a range applies. Decide it in review.")
            continue
        has_floor, has_ceiling = _bounds(requirement.specifier)
        if not (has_floor and has_ceiling):
            if not requirement.specifier:
                missing = "no version bound at all"
            else:
                missing = "no ceiling" if has_floor else "no floor"
            offenders.append(f"{site} — {missing}")
    return offenders


def stale_exemptions(sites: tuple[InstallSite, ...], exemptions: tuple[Exemption, ...] = _EXEMPTIONS) -> list[str]:
    """Register entries no command block carries any more.

    A register only shrinks honestly if an obsolete entry is loud. A silent one
    is a rule that has quietly stopped applying to anything, and the next reader
    takes it for evidence that the shape is acceptable.
    """
    present = {(site.file, site.spec) for site in sites}
    return [f"{e.file}: {e.spec}" for e in exemptions if (e.file, e.spec) not in present]


#: Anti-vacuity floors, measured on 2026-09-20 against c5aec86c5:
#: eight install invocations in command blocks — six naming a bounded
#: requirement (`PyYAML==6.0.3` three times, `pip-audit==2.10.1`,
#: `pip-licenses==5.5.5`, `pip>=25.0,<27.0`), one naming a shell variable
#: (registered), one delegating to a requirements list. FLOORS, not equalities.
_MINIMUM_SITES = 8
_MINIMUM_BOUNDED_SITES = 6
#: The green control (#1602's second counter-test): `.taskfiles/docs.yaml`
#: already carries a bounded, non-`==` install. If the sweep flagged everything,
#: this one would be a finding too — it must stay clean.
_GREEN_CONTROL = (".taskfiles/docs.yaml", "pip>=25.0,<27.0")


@pytest.fixture(scope="module")
def sites() -> tuple[InstallSite, ...]:
    """Every install site the checked-in command blocks carry."""
    collected: list[InstallSite] = []
    for path in scanned_files(_REPO_ROOT):
        relative = path.relative_to(_REPO_ROOT).as_posix()
        collected.extend(install_sites(relative, path.read_text(encoding="utf-8")))
    return tuple(collected)


class TestTheSweepReachesTheFiles:
    """Anti-vacuity: every assertion below is worthless over an empty site list."""

    def test_the_scanned_trees_exist(self) -> None:
        missing = [entry for entry in _SCANNED if not (_REPO_ROOT / entry).exists()]
        assert not missing, f"scanned paths that no longer exist: {missing}. A moved tree is an unscanned tree."

    def test_at_least_the_measured_number_of_sites_is_found(self, sites: tuple[InstallSite, ...]) -> None:
        assert len(sites) >= _MINIMUM_SITES, (
            f"only {len(sites)} install site(s) found; {_MINIMUM_SITES} were measured on 2026-09-20. "
            "Either sites were removed (lower the floor deliberately) or this parser stopped matching "
            "the shape the files use — the instrument having the gap, not the repository."
        )

    def test_the_green_control_is_seen_and_clean(self, sites: tuple[InstallSite, ...]) -> None:
        """`.taskfiles/docs.yaml`'s bounded pip install proves the sweep
        distinguishes rather than reports everything: it must be FOUND (so the
        sweep reaches it) and NOT a finding (so the rule reads a range, not only
        an `==`)."""
        file, spec = _GREEN_CONTROL
        matching = [site for site in sites if site.file == file and site.spec == spec]
        assert matching, f"the sweep no longer reaches {file}'s `{spec}` install — the green control is gone"
        assert not unbounded_sites(tuple(matching)), unbounded_sites(tuple(matching))

    def test_a_requirements_list_install_is_recognised_as_delegating(self, sites: tuple[InstallSite, ...]) -> None:
        """`pip install -r <list>` names no version; it is held by the hash
        sweeps instead. If this branch were never taken, a `-r` install would be
        read as an unparseable requirement and the delegation would be untested."""
        assert any(site.spec is None for site in sites), (
            "no `-r` install found in any command block; the delegation branch of this sweep is untested "
            "(.taskfiles/docs.yaml carried one on 2026-09-20)."
        )


class TestEveryInstallIsBounded:
    """The rule: class (b), free-form half — `==` pin or bounded range."""

    def test_no_command_block_installs_an_unbounded_requirement(self, sites: tuple[InstallSite, ...]) -> None:
        offenders = unbounded_sites(sites)
        assert not offenders, (
            "unbounded Python installs in workflow/taskfile command blocks (NFR-009 §2.3.1, class (b)): "
            + "; ".join(offenders)
        )

    def test_enough_sites_are_actually_checked(self, sites: tuple[InstallSite, ...]) -> None:
        """The assertion above is also green when every site is exempt. This is
        the floor under the number it really inspects."""
        checked = [site for site in sites if site.spec is not None and not _is_exempt(site, _EXEMPTIONS)]
        assert len(checked) >= _MINIMUM_BOUNDED_SITES, (
            f"only {len(checked)} site(s) are actually bound-checked; {_MINIMUM_BOUNDED_SITES} were measured "
            "on 2026-09-20. An exemption was added, or the parser lost sites."
        )


class TestTheRegisterShrinks:
    """An exception register grows unless an obsolete entry is loud."""

    def test_no_exemption_matches_nothing(self, sites: tuple[InstallSite, ...]) -> None:
        assert not stale_exemptions(sites), (
            "_EXEMPTIONS records installs no command block carries any more: "
            + "; ".join(stale_exemptions(sites))
            + ". Remove the entry with the site; an exemption guarding nothing is read later as permission."
        )

    def test_every_exemption_carries_a_reason(self) -> None:
        thin = [f"{e.file}: {e.spec}" for e in _EXEMPTIONS if len(e.why.strip()) < 40]
        assert not thin, f"exemptions without a written argument: {thin}"


class TestTheGuardCanFail:
    """The falsifier, over a MUTATED copy of the REAL workflow rather than a
    fixture — #1602's red-first condition verbatim: "drop the `==` from one of
    the six and watch it go red". It asserts the SAME expression the rule
    asserts, which is the thing that was wrong three times in this repository
    in one week."""

    @pytest.fixture
    def backend_workflow(self) -> str:
        return (_REPO_ROOT / ".github" / "workflows" / "backend.yml").read_text(encoding="utf-8")

    def test_dropping_a_pin_is_reported(self, backend_workflow: str) -> None:
        mutated = backend_workflow.replace("'pip-audit==2.10.1'", "'pip-audit'", 1)
        assert mutated != backend_workflow, "the mutation did not apply; this test would pass vacuously"
        offenders = unbounded_sites(install_sites(".github/workflows/backend.yml", mutated))
        assert any("pip-audit" in offender for offender in offenders), offenders

    def test_the_unmutated_workflow_is_clean(self, backend_workflow: str) -> None:
        """The other half: the real file is green, so the test above measures
        the mutation and not a sweep that reports everything it sees."""
        assert not unbounded_sites(install_sites(".github/workflows/backend.yml", backend_workflow))

    def test_loosening_a_pin_to_a_floor_is_reported(self, backend_workflow: str) -> None:
        """The subtler half of the same rule: a floor is not a bound."""
        mutated = backend_workflow.replace("'pip-audit==2.10.1'", "'pip-audit>=2.10.1'", 1)
        assert mutated != backend_workflow, "the mutation did not apply; this test would pass vacuously"
        offenders = unbounded_sites(install_sites(".github/workflows/backend.yml", mutated))
        assert any("pip-audit" in offender and "ceiling" in offender for offender in offenders), offenders

    def test_a_mention_in_prose_is_not_a_site(self) -> None:
        """The structural claim the module docstring makes: a `pip install`
        quoted in a `desc:` block or a `#` comment is not an install. Without
        this, five files in these trees would need register entries for text."""
        document = (
            "version: '3'\n"
            "tasks:\n"
            "  demo:\n"
            "    desc: |\n"
            "      This used to be `pip install requests` before the lock arrived.\n"
            "    # and `pip install flask` was next to it\n"
            "    cmds:\n"
            "      - echo nothing-installed-here\n"
        )
        assert install_sites("fixture.yaml", document) == ()

    def test_a_new_unpinned_install_in_a_taskfile_is_reported(self) -> None:
        """The case #1602 is actually about: the SEVENTH site, added tomorrow.
        A taskfile shape rather than a workflow one, so both readers are proven,
        and `cmds:` is a list — the shape `run:` does not have."""
        document = "version: '3'\ntasks:\n  demo:\n    cmds:\n      - python3 -m pip install --user some-linter\n"
        offenders = unbounded_sites(install_sites("fixture.yaml", document))
        assert any("some-linter" in offender for offender in offenders), offenders
