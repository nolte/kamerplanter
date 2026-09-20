"""#1602 — the free-form half of class (b): a ``pip install`` in a command block is bounded.

**The asymmetry this file removes.** NFR-009 §2.3.1 splits Python installs into
class (a) — reaches a delivered artefact, must be hash-bearing — and class (b) —
runner-only, output is a verdict, must carry an ``==`` pin or a bounded range.
Class (b) has two halves, and until this file only one of them was enforced:

* ``additional_dependencies:`` in ``.pre-commit-config.yaml`` — declarative YAML,
  held by ``test_pre_commit_dependency_bounds.py`` beside this file (#1572);
* ``pip install`` inside a ``run:``/``cmds:`` block — free-form shell, held by
  **nothing** until #1602.

NFR-009 §2.3.1's member list names a THIRD form of class (b) that neither guard
holds: ``tools/rag-eval/requirements.txt``. It carries floors and ceilings today
(#1572 put them there), and that is a property of its last editor, not of the
repository — the same sentence this file's next paragraph uses about the six
install sites. It is out of #1602's scope (it is a requirement LIST, not a
command block) and named in the residual set below rather than implied.

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
  ``check_renovate_dashboard.dockerfile_python_installs``;
* **``uvx --from '<package><specifier>'``** — and this one EXISTS in the tree
  already: ``.taskfiles/docs.yaml`` runs ``uvx --from 'uv{{.UV_SPEC}}' uv pip
  compile …``. It is a runner-only tool install by any reading of §2.3.1, and
  this file does not see it. It is named rather than matched on purpose: the one
  existing instance spells its version as a go-task template, so matching it
  would immediately require a register entry for a templated string — a parser
  entry, which is what :data:`_EXEMPTIONS` must not fill up with. The version it
  templates is ``[tool.uv].required-version``, already guarded three times over
  (``test_uv_pin_is_single.py``). A ``uvx --from 'black==24.1.0'`` added
  tomorrow would be unseen; that is the cost, stated rather than discovered;
* **``uv tool install`` and ``pipx install``** — same class, no lock, straight
  from the index. ``pipx`` is deliberately NOT matched here: the only occurrence
  in these trees is inside a ``printf`` that tells a contributor how to install
  pre-commit, so matching the word would report help text (see
  ``test_a_mention_inside_a_quoted_string_is_not_a_site``, which is the general
  defence, and the sister sweep's ``_DOCKERFILE_PIP_INSTALL``, which does match
  ``pipx`` because a Dockerfile has no help text);
* **the file behind ``-r``/``-c``** — a ``-r list.txt`` delegates to the hash
  sweeps, but only ``requirements*.txt``/``constraints*.txt`` names are in their
  patterns (``check_renovate_dashboard._REQUIREMENT_LIST_PATTERNS``); ``-r
  deps/base.pip`` would be delegated by this file to a sweep that does not read
  it. A ``-c constraints.txt`` is skipped here as a flag value and is not
  checked for bounds at all — the sister sweep names the same gap.

Traces to #1602 (no TC-ID: a dependency gate is not a user-facing case).
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.requirements import InvalidRequirement, Requirement

from tests.support.repo_scripts import find_repo_root
from tests.support.version_bounds import missing_bound

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

#: The trees scanned. WIDER than #1602 asks for (`.github/workflows/**` and
#: `.taskfiles/**`): composite actions and the root Taskfile carry exactly the
#: same `run:`/`cmds:` shapes, and leaving them out would have made the sweep's
#: reach depend on where somebody chose to put a step.
_SCANNED: tuple[str, ...] = (".github/workflows", ".github/actions", ".taskfiles", "Taskfile.yaml")

#: Directories the walk does not descend into. Build output and dependency trees
#: carry YAML nobody in this repository edits.
_SKIPPED_DIRECTORIES = frozenset({".git", ".venv", "node_modules", "__pycache__", "dist", "build"})

#: Keys whose value is a command (or a list of commands). Everything below such
#: a key is shell text; everything else in these files is configuration or prose.
#: `install-command:` is go-task/`setup-python`-style tooling input — `backend.yml`
#: passes one to the reusable coverage workflow — and is shell all the same.
_COMMAND_KEYS = frozenset({"run", "cmd", "cmds", "install-command", "install_command", "pre-install-command"})

#: An install invocation: an optional path or `%` magic, `pip`/`pip3`/`uv pip`,
#: then `install`. Also matches `python -m pip install` (the `pip install` tail
#: is what the pattern anchors on).
#:
#: THE OPTION PART IS NOT DECORATION. A first version demanded that `install`
#: follow `pip` IMMEDIATELY, and `pip --no-cache-dir install foo` / `pip -q
#: install foo` / `python -m pip --quiet install foo` were then invisible rather
#: than red — a spelling of the very thing the rule forbids, which is the
#: vacuity class NFR-018 §1 is about. The sister sweep in
#: `scripts/ci/check_renovate_dashboard.py` (`_DOCKERFILE_PIP_INSTALL`) had
#: already met the same form and documents it; the sub-expression below is taken
#: from there verbatim so the two readings cannot drift.
_INSTALL = re.compile(
    r"""(?:^|[\s;&|(])%?(?:[\w./\\-]*/)?
        (?:pip[0-9.]*|uv\s+pip)
        (?:\s+-{1,2}[\w-]+(?:[=\s]\S+)?)*   # global options before the subcommand
        \s+install\b
    """,
    re.VERBOSE,
)

#: Shell operators that end one command and start the next. Line continuations
#: are joined BEFORE this splits (:func:`install_sites`): a correct multi-line
#: `pip install \` + continuation would otherwise be torn in half and reported as
#: a finding for a pure formatting change — and the only way out would be a
#: register entry for a line break, i.e. exactly the furniture this file's
#: header refuses.
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
    """Every YAML file in the scanned trees, sorted.

    Walks with PRUNING rather than globbing everything and filtering afterwards:
    this file runs in `backend-guards.yml`, which is unfiltered and required, and
    that lane's whole argument is its fifteen-second runtime. None of the scanned
    trees contains a `node_modules` today — the point is that the cost of one
    appearing is not paid here.
    """
    found: list[Path] = []
    for entry in _SCANNED:
        root = repo_root / entry
        if root.is_file():
            found.append(root)
            continue
        for directory, subdirectories, filenames in os.walk(root):
            subdirectories[:] = [name for name in subdirectories if name not in _SKIPPED_DIRECTORIES]
            found.extend(Path(directory) / filename for filename in filenames if filename.endswith((".yml", ".yaml")))
    return tuple(sorted(found))


class _NotAnInstallError(Exception):
    """The pattern matched inside a quoted string; there is no install here."""


def _requirement_tokens(segment: str) -> tuple[list[str], bool]:
    """``(requirement tokens, delegates_to_a_list)`` for one install segment.

    Raises:
        ValueError: when the segment cannot be tokenised — an unbalanced quote,
            usually templating. A caller must treat that as a finding rather
            than as "nothing to see": see the module docstring.
    """
    tokens = shlex.split(segment, posix=True)
    # Drop everything up to and including the `install` VERB. It must be a token
    # of its own: `printf 'install first: pipx install foo'` matches the pattern
    # inside a quoted string and is a MENTION, not an install (`.taskfiles/
    # checks.yaml` has one). No `install` token means no site — reported by
    # raising, so the caller decides rather than this helper silently returning
    # an empty list that looks like "installs nothing".
    for index, token in enumerate(tokens):
        if token == "install":
            tokens = tokens[index + 1 :]
            break
    else:
        raise _NotAnInstallError(segment)
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
        for segment in _SEGMENT_SEPARATOR.split(command.replace("\\\n", " ")):
            if not _INSTALL.search(segment):
                continue
            collapsed = " ".join(segment.split())
            try:
                requirements, delegates = _requirement_tokens(segment)
            except _NotAnInstallError:
                continue
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


def _is_exempt(site: InstallSite, exemptions: tuple[Exemption, ...]) -> bool:
    return any(exemption.file == site.file and exemption.spec == site.spec for exemption in exemptions)


def _parsed(spec: str) -> Requirement | None:
    """The requirement *spec* denotes, or ``None`` when it is not PEP 508."""
    try:
        return Requirement(spec)
    except InvalidRequirement:
        return None


def loosen_the_first_pin(file: str, text: str, *, keep_floor: bool) -> tuple[str, str]:
    """Rewrite the first ``==``-pinned install in *text* so the rule must report it.

    THE MUTATION IS DRIVEN BY THE PATTERN, NOT BY A LITERAL. An earlier version
    of the falsifiers below mutated the string ``'pip-audit==2.10.1'``. That
    exact literal is what `renovate.json5`'s custom manager bumps automatically,
    with patch auto-merge on — so the next release of pip-audit would have made
    `replace()` a no-op, both falsifiers red, and this file's home lane
    (`backend-guards.yml`, unfiltered and REQUIRED) would have blocked the merge
    train over a version number. #1608 had to repair exactly this shape in the
    ZAP pin guard the same day: a guard that checks the VALUE where it means the
    FORM.

    Args:
        file: Repository-relative path, used to read the sites back.
        text: The file's contents.
        keep_floor: ``True`` rewrites ``name==X`` to ``name>=X`` (a floor is not
            a bound); ``False`` drops the specifier entirely.

    Returns:
        ``(mutated text, package name)``.

    Raises:
        AssertionError: when the file carries no ``==``-pinned install, or the
            substitution does not apply — either way the falsifier would pass
            vacuously and must fail loudly instead.
    """
    pinned = next(
        (
            site
            for site in install_sites(file, text)
            if site.spec is not None and (parsed := _parsed(site.spec)) is not None and "==" in str(parsed.specifier)
        ),
        None,
    )
    assert pinned is not None and pinned.spec is not None, f"{file} carries no `==`-pinned install to mutate"
    requirement = Requirement(pinned.spec)
    version = str(requirement.specifier).removeprefix("==")
    replacement = f"{requirement.name}>={version}" if keep_floor else requirement.name
    pattern = re.compile(rf"{re.escape(requirement.name)}\s*==\s*[0-9][\w.*+!-]*")
    mutated, applied = pattern.subn(replacement, text, count=1)
    assert applied == 1 and mutated != text, f"the mutation of {requirement.name} did not apply to {file}"
    return mutated, requirement.name


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
        missing = missing_bound(requirement.specifier)
        if missing is not None:
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


#: Anti-vacuity floors. Measured on 2026-09-20 against c5aec86c5: EIGHT install
#: invocations in command blocks — six naming a bounded requirement
#: (`PyYAML==6.0.3` three times, `pip-audit==2.10.1`, `pip-licenses==5.5.5`,
#: `pip>=25.0,<27.0`), one naming a shell variable (registered), one delegating
#: to a requirements list.
#:
#: THE FLOORS SIT DELIBERATELY BELOW THAT. A floor equal to the inventory turns
#: every legitimate consolidation — dropping one of the two identical PyYAML
#: steps in `frontend.yml`, moving `pip-audit` to `uv tool` — into a red
#: required lane with no defect behind it, and at the floor "the inventory
#: shrank" is indistinguishable from "the parser collapsed". These numbers exist
#: to catch the SECOND thing: a parser that suddenly reads two sites, or none,
#: fails here instead of passing every check below vacuously.
_MINIMUM_SITES = 6
_MINIMUM_BOUNDED_SITES = 4

#: The file the falsifiers mutate. It is named once, as a PATH — the versions
#: inside it are found by pattern (:func:`loosen_the_first_pin`).
_BACKEND_WORKFLOW = ".github/workflows/backend.yml"


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

    def test_a_bounded_non_pin_is_seen_and_not_reported(self, sites: tuple[InstallSite, ...]) -> None:
        """#1602's green counter-test, phrased as a CLASS rather than a value.

        The tree carries at least one install that is bounded WITHOUT being an
        `==` pin — `.taskfiles/docs.yaml`'s `pip>=25.0,<27.0` on 2026-09-20. It
        must be FOUND (so the sweep reaches a `cmds:` list) and NOT reported (so
        the rule reads a range and does not simply flag everything that is not a
        pin). Asserting the literal `pip>=25.0,<27.0` would have been a third
        pinned value in a guard about pinned values: that file says itself that
        raising the ceiling is "a reviewed decision", i.e. an EXPECTED change,
        and it would have turned red here with a message pointing the wrong way.
        """
        ranged = [
            site
            for site in sites
            if site.spec is not None
            # A BOUNDED, NON-PIN range — not merely "no `==` in the string". Read
            # that way, this control swept up a requirement with NO specifier at
            # all, and it went red together with the rule during the red
            # counter-test: the control then reports the defect a second time
            # instead of staying green and proving the sweep distinguishes.
            and (parsed := _parsed(site.spec)) is not None
            and str(parsed.specifier)
            and "==" not in str(parsed.specifier)
        ]
        assert ranged, (
            "no bounded non-`==` install found anywhere in the scanned trees; the green control of this "
            "sweep is gone, so `test_no_command_block_installs_an_unbounded_requirement` can no longer "
            "distinguish 'bounded' from 'pinned' (.taskfiles/docs.yaml carried one on 2026-09-20)."
        )
        assert not unbounded_sites(tuple(ranged)), unbounded_sites(tuple(ranged))


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
        return (_REPO_ROOT / _BACKEND_WORKFLOW).read_text(encoding="utf-8")

    def test_dropping_a_pin_is_reported(self, backend_workflow: str) -> None:
        mutated, name = loosen_the_first_pin(_BACKEND_WORKFLOW, backend_workflow, keep_floor=False)
        offenders = unbounded_sites(install_sites(_BACKEND_WORKFLOW, mutated))
        assert any(name in offender for offender in offenders), offenders

    def test_the_unmutated_workflow_is_clean(self, backend_workflow: str) -> None:
        """The other half: the real file is green, so the test above measures
        the mutation and not a sweep that reports everything it sees."""
        assert not unbounded_sites(install_sites(_BACKEND_WORKFLOW, backend_workflow))

    def test_loosening_a_pin_to_a_floor_is_reported(self, backend_workflow: str) -> None:
        """The subtler half of the same rule: a floor is not a bound."""
        mutated, name = loosen_the_first_pin(_BACKEND_WORKFLOW, backend_workflow, keep_floor=True)
        offenders = unbounded_sites(install_sites(_BACKEND_WORKFLOW, mutated))
        assert any(name in offender and "ceiling" in offender for offender in offenders), offenders

    def test_a_global_option_before_the_subcommand_is_still_seen(self, backend_workflow: str) -> None:
        """`pip --no-cache-dir install x` is the same install with a flag in
        the middle. The first version of `_INSTALL` demanded `install`
        immediately and read this as nothing at all — invisible, not red."""
        mutated, name = loosen_the_first_pin(_BACKEND_WORKFLOW, backend_workflow, keep_floor=False)
        with_option = mutated.replace("-m pip install", "-m pip --no-cache-dir install", 1)
        assert with_option != mutated, "the option was not inserted; this test would pass vacuously"
        offenders = unbounded_sites(install_sites(_BACKEND_WORKFLOW, with_option))
        assert any(name in offender for offender in offenders), offenders

    def test_a_line_continuation_does_not_split_an_install(self) -> None:
        """A correct multi-line install must stay ONE site. Without joining
        `\\\n` first, the tail lands in its own segment and the head looks like
        an install naming nothing — a finding produced by a formatting change."""
        document = (
            "version: '3'\ntasks:\n  demo:\n    cmds:\n      - |\n"
            "        python3 -m pip install \\\n"
            "          'some-tool==1.2.3'\n"
        )
        sites = install_sites("fixture.yaml", document)
        assert [site.spec for site in sites] == ["some-tool==1.2.3"], sites
        assert not unbounded_sites(sites)

    def test_a_requirements_list_install_delegates(self) -> None:
        """`pip install -r <list>` names no version; the list it points at is
        class (a) and is held by the hash sweeps. The branch is exercised here
        rather than through whatever the tree happens to contain today."""
        document = "version: '3'\ntasks:\n  demo:\n    cmds:\n      - pip install -q -r docs/requirements.txt\n"
        sites = install_sites("fixture.yaml", document)
        assert [site.spec for site in sites] == [None], sites
        assert not unbounded_sites(sites)

    def test_a_mention_inside_a_quoted_string_is_not_a_site(self) -> None:
        """`.taskfiles/checks.yaml` prints installation advice from a `cmds:`
        block. The install VERB must be a token of its own, or that help text
        would be a finding — and the only way to silence it a register entry
        for a `printf`."""
        document = (
            "version: '3'\n"
            "tasks:\n"
            "  demo:\n"
            "    cmds:\n"
            "      - |\n"
            "        printf 'Install first:  pip install pre-commit' >&2\n"
        )
        assert install_sites("fixture.yaml", document) == ()

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
