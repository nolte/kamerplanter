#!/usr/bin/env python3
"""Refuse a GitHub Actions gate that cannot fail.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_workflow_gate_integrity.py
    python3 scripts/check_workflow_gate_integrity.py --list   # name every site
    python3 scripts/check_workflow_gate_integrity.py --json   # machine-readable

**What it enforces.** NFR-018 §2: a check that cannot report a failure is
indistinguishable from one that is not running, and must not exist. The spec
says so and — §8, in its own words, the "unangenehme Pointe" — has no gate of
its own. This is that gate, in the minimal form the 2026-08-08 issue-pattern
audit asked for (measure P5.4). Cluster G is eighteen issues of checks that
reported green on nothing: #814 (a pre-commit hook printing ``Passed`` for a
check whose tool was absent), #828 (a required context that gated no test run),
the ZAP scaffold that echoed ``OK`` while scanning nothing.

Five shapes, all of which have occurred in this repository:

1. **``|| true`` in a ``run:`` step.** The step's verdict is discarded. Often
   correct — ``grep -c`` exits 1 on no match and a counting expression under
   ``set -e`` needs the guard — and that is exactly why it needs a reason
   rather than a ban: ``skaffold render … || true`` discarded a real render
   failure for months (see the header of ``skaffold-verify.yml``).

2. **``continue-on-error: true``.** The step or job cannot turn its check red.
   Legitimate for a *reporter* — a fork pull request's read-only token cannot
   create a check run, and the suite's own verdict is not that reporter's to
   give. Not legitimate for anything that measures.

3. **A job consuming ``needs.<x>.outputs`` without consulting
   ``needs.<x>.result``**, when its own ``if:`` overrides GitHub's dependency
   gating (``always()``, ``cancelled()``, ``failure()``). Without the override
   GitHub skips the dependent job when its dependency fails, and the shape is
   safe. *With* it, a failed or cancelled producer leaves every output an empty
   string, every comparison false, every step skipped — and a job whose steps
   are all skipped **reports success**. That is how ``lint-test-build (22)``
   would have gone green without tsc, ESLint, vitest or the build ever running;
   the comment in ``frontend.yml`` that describes the trap is the reason this
   third shape is checked at all.

4. **A comment on a line reached through a trailing ``\\``.** The ``#`` ends
   the logical line, so the command runs truncated at the previous argument and
   the next flag is executed as its own program. The step goes *red*, which
   looks self-reporting — but the truncated command is the one that writes the
   artefacts later steps gate on. ``security-nuclei-nightly.yml`` lost
   ``-tags``, ``-severity`` and both output flags this way; ``results.jsonl``
   and ``results.sarif`` were never written, so the SARIF upload
   (``if: hashFiles(...) != ''``) and the issue-opening step (an ``existsSync``
   early return) skipped silently for 22 consecutive nights, 2026-08-08 to
   2026-08-29 (#1010). Two inert gates behind one loud one.

5. **A path the workflow reads that its own ``paths:`` filter excludes.** The
   workflow declares *when it runs* — ``on.push.paths`` / ``on.pull_request.paths``
   — in one place, and *what it reads* somewhere else entirely: a ``run:`` step, a
   ``yq`` lookup, a ``with: file:`` input. The two lists are maintained by hand,
   by different people, at different times, and nothing asserts they agree. When
   they drift the result is always the same shape — **the one change most able to
   break a check is the one change that never runs it** — and the breakage
   surfaces later, on ``develop`` or in a nightly, where nobody can attribute it.

   Four incidents on 2026-08-31 alone (#1313). #1296: ``backend.yml`` pinned its
   own lock-compiling toolchain but nothing watched the pin file, so
   ``Lock staleness`` went red on every backend pull request *and on develop* for
   four days. #1302: ``security-nuclei-templates.yml`` is the only nuclei lane
   with a ``pull_request`` trigger and its filter excluded
   ``.github/renovate-pins.yaml``, so #1280 changed only the nuclei pin, ran no
   nuclei check at all, merged green — and the nightly then failed to start for
   two nights. Those two are literally the same defect in two lanes, found six
   hours apart, which is what makes it mechanical rather than incidental;
   #1010/#1294 and #1295 are the same family from other directions.

   And it was still present in a third, unreported place when this shape was
   written: ``docker-publish.yml`` runs
   ``scripts/ci/determine_chart_version.sh`` — the script that computes the
   published chart version — and builds ``src/inference-service`` and
   ``src/knowledge-service`` into images that production pulls by ``:latest``,
   while none of those four paths appeared in its ``push`` filter.

   The fifth shape asks "does the workflow read this path?", and the answer is
   decided against the **tracked** files of the checkout, never against what
   happens to be lying in the working tree (:class:`TreeIndex`, #1340). Resolving
   it on disk made the verdict a function of untracked state: gitignored E2E
   output turned the same workflows red on a workstation and green in CI, while
   in CI — where nothing untracked exists — the rule could not report an
   untracked read path at all.

**Why the fifth shape lives here and not in a script of its own.** This file
already owns workflow discovery, the justification hatch, the ``--list``/``--json``
contract, its selftests and the pre-commit wiring in the required ``static``
lane. A second thin checker for one rule would duplicate all of that and then
drift from it — which is, recursively, the defect #1313 is about. #1295 is the
worked example: three workflows reasoned in their comments about a ``shellcheck``
that ran nowhere, for months. Sibling guards drifting apart is the class, not the
cure.

**The escape hatch.** A site may stand by carrying a justification on its own
line or in the comment block directly above it::

    # gate-integrity-ok: grep -c exits 1 on no match; the count is the result
    hits=$(grep -c '^kind:' file || true)

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer. For shape 3 the marker goes in the comment block above the
job key, which is where this repository already explains its jobs. Shape 5 adds
one placement — a marker anywhere in the same workflow whose reason *names the
path* — because a reference can sit inside a JavaScript or shell string where a
``#`` is a syntax error rather than a comment, and because the honest place to
write "this reference deliberately does not widen the trigger" is next to the
``paths:`` filter it declines to widen. Naming the path is what keeps that
placement from becoming a file-wide silencer.

**Best-effort, and deliberately so.** Shapes 1, 2, 4 and 5 are found textually, so
a swallowed exit code spelled ``|| :`` or ``; true`` slips through; shape 3 reads
the parsed YAML but cannot see through a composite action or a reusable
workflow. A checker that tried to be exhaustive here would need a shell parser
and would still miss things, while its false positives got it switched off.
What it does guarantee is that the shapes that have actually cost this
repository something cannot be *added* without somebody writing down why.

Standard library plus PyYAML — the same isolated pre-commit environment the
chart-digest hook uses, because the required ``static`` job runs on a bare
runner with none of the project's dependencies installed.

Traces to the 2026-08-08 issue-pattern audit, measure P5.4 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the workflows live, relative to the repository root.
DEFAULT_SCAN_ROOT = ".github/workflows"

#: The marker that exempts a site, plus the minimum length of the reason that
#: must follow it. A bare marker is not an exemption.
JUSTIFICATION_MARKER = "# gate-integrity-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: A discarded exit code in a shell line.
SWALLOWED_EXIT = re.compile(r"\|\|\s*true\b")

#: ``continue-on-error: true`` at any indentation (job or step level).
CONTINUE_ON_ERROR = re.compile(r"^\s*continue-on-error:\s*true\s*$")

#: Expression functions that override GitHub's "skip me when my dependency
#: failed" behaviour. Their presence in a job-level ``if:`` is what turns a
#: missing ``needs.<x>.result`` check into a false green.
GATING_OVERRIDES = ("always()", "cancelled()", "failure()")

_NEEDS_OUTPUT = re.compile(r"needs\.([A-Za-z0-9_-]+)\.outputs\b")
_NEEDS_RESULT = re.compile(r"needs\.([A-Za-z0-9_*-]+)\.result\b")

#: The ``on:`` keys whose ``paths:`` filter decides whether a *diff* runs the
#: workflow. ``schedule`` and ``workflow_dispatch`` are deliberately absent: they
#: fire regardless of the diff, so their existence does not mean the change that
#: breaks a check ever meets it.
DIFF_TRIGGERS = ("push", "pull_request", "pull_request_target")

#: A candidate repo-relative path: at least two ``/``-separated segments. One
#: segment is not enough to tell ``Taskfile.yaml`` from a shell word, and the
#: existence probe below cannot rescue that — ``docker``, ``helm`` and ``spec``
#: are all directories *and* plausible words in prose.
_PATH_CANDIDATE = re.compile(r"(?<![A-Za-z0-9_./@-])((?:[A-Za-z0-9_.+-]+/)+[A-Za-z0-9_.+-]+)")

#: Probe segment used to ask "does this filter entry match anything *below* this
#: directory?". Any name that cannot collide with a real one works.
_DIRECTORY_PROBE = "__gate_integrity_probe__"

#: How long each ``git`` probe below may take before the checker stops waiting
#: and resolves against the filesystem instead. Generous by two orders of
#: magnitude — ``git ls-files`` over this repository's 4 300 tracked paths takes
#: single-digit milliseconds — because this runs in the required ``static`` lane
#: and a hang there costs more than a wrong answer would.
GIT_TIMEOUT_SECONDS = 5

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class WorkflowIntegrityCheckError(Exception):
    """A usage or environment problem — not a finding about the workflows."""


@dataclass(frozen=True)
class Finding:
    """One gate-integrity smell in one workflow file."""

    path: Path
    line: int
    kind: str
    detail: str
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None

    def relative(self) -> str:
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)


#: Human wording per finding kind, used in the report.
KIND_LABELS = {
    "swallowed_exit": "the step's exit code is discarded",
    "continue_on_error": "this cannot turn its check red",
    "unguarded_needs_output": "a failed dependency makes this job report success",
    "commented_continuation": "a comment ends this command early, so it runs truncated",
    "uncovered_path_reference": "this workflow reads a file its own paths: filter excludes",
}


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the site on *line*, or ``None``.

    Accepted on the site's own line (trailing comment) and anywhere in the
    contiguous comment block directly above it. The block form matters here:
    this repository explains its jobs in a comment paragraph above the job key,
    and a marker is most useful inside the paragraph that already argues the
    point.
    """
    candidates = [lines[line - 1]]
    index = line - 2
    while index >= 0 and lines[index].strip().startswith("#"):
        candidates.append(lines[index].strip())
        index -= 1
    for candidate in candidates:
        marker = candidate.find(JUSTIFICATION_MARKER)
        if marker == -1:
            continue
        reason = candidate[marker + len(JUSTIFICATION_MARKER) :].strip()
        if len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def _strip_comment(line: str) -> str:
    """Return the part of *line* before its first ``#``.

    Crude on purpose: a ``#`` inside a quoted string would truncate early, which
    can only ever *hide* a finding on that line, never invent one. The
    alternative — matching inside comments — reported the two ``|| true``
    occurrences that ``skaffold-verify.yml`` mentions in its own header while
    explaining that it removed them.
    """
    hash_index = line.find("#")
    return line if hash_index == -1 else line[:hash_index]


def _job_line(lines: list[str], name: str) -> int:
    """The 1-based line of the ``<name>:`` key in the ``jobs:`` mapping."""
    pattern = re.compile(rf"^\s{{2,4}}{re.escape(name)}:\s*$")
    for index, line in enumerate(lines, start=1):
        if pattern.match(line):
            return index
    return 1


def _strings(node: Any) -> list[str]:
    """Every string anywhere inside a parsed YAML node."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for value in node.values() for text in _strings(value)]
    if isinstance(node, list):
        return [text for value in node for text in _strings(value)]
    return []


def scan_text(path: Path, lines: list[str]) -> list[Finding]:
    """Find the two textual shapes: swallowed exits and continue-on-error."""
    findings: list[Finding] = []
    for number, line in enumerate(lines, start=1):
        code = _strip_comment(line)
        if SWALLOWED_EXIT.search(code):
            findings.append(
                Finding(
                    path=path,
                    line=number,
                    kind="swallowed_exit",
                    detail=code.strip(),
                    justification=justification_for(lines, number),
                )
            )
        if CONTINUE_ON_ERROR.match(code):
            findings.append(
                Finding(
                    path=path,
                    line=number,
                    kind="continue_on_error",
                    detail=code.strip(),
                    justification=justification_for(lines, number),
                )
            )
    return findings


def scan_continuations(path: Path, lines: list[str]) -> list[Finding]:
    """Find a command truncated by a comment on one of its continued lines.

    A ``#`` reached through a trailing ``\\`` ends the logical line: everything
    after it is a comment, and the *following* lines become separate commands.
    The shell runs the command truncated at the previous argument and then tries
    to execute the next flag as a program.

    Why this belongs in a gate-integrity check rather than in a shell linter:
    the visible symptom is a red step, which looks self-reporting — but the
    truncated command is the one that produces the artefacts the *later* steps
    gate on. ``security-nuclei-nightly.yml`` lost ``-tags``, ``-severity`` and
    both ``-o``/``-sarif-export`` this way, so ``results.jsonl`` and
    ``results.sarif`` were never written, and the two steps downstream —
    ``if: hashFiles('results.sarif') != ''`` and an ``existsSync`` early
    return — skipped silently for 22 consecutive nights while the scan appeared
    to run. Two inert gates, which is exactly NFR-018 §2.

    Why adopting actionlint does not retire this shape. #1295 brings in
    actionlint, which runs shellcheck over every ``run:`` block, and assumed
    this scan merely duplicated ``SC2215``. Measured — actionlint ``latest``
    with its bundled shellcheck 0.11.0, over three ``run:`` blocks of identical
    structure differing only in the line after the ``#`` — the overlap is
    partial, because shellcheck keys on what *follows* the comment:

    * a flag (``-tags exposure``) → ``SC2215``, "this flag is used as a command
      name". That is the ``security-nuclei-nightly.yml`` case above, and the
      only one the "isn't this just SC2215?" question actually looks at.
    * an argument to a command whose arity it knows (``dest.txt`` after
      ``cp source.txt``) → ``SC2225``, "this cp has no destination".
    * a bare positional to a command it does not know (``mycmd … arg``) →
      **nothing reported**, and still nothing under ``--enable=all`` at
      ``-S style``, the lowest severity.

    This scan keys on the *structure* instead — a ``#`` reached through a
    trailing ``\\``, whatever follows — and flags all three. The two are
    therefore complementary, not redundant, and #1295 (R5) keeps both: retiring
    this one would leave the third case with no static signal at all, caught
    only once the truncated command has already run — and per the paragraph
    above, that run's red step is the least informative part of the damage.

    Detection is on the *code* part of each line, so a documentation block whose
    own comment line happens to end in a backslash is not a finding: stripping
    the comment leaves no trailing continuation to follow.
    """
    findings: list[Finding] = []
    for index, line in enumerate(lines):
        if not _strip_comment(line).rstrip().endswith("\\"):
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if not following.lstrip().startswith("#"):
            continue
        findings.append(
            Finding(
                path=path,
                line=index + 2,
                kind="commented_continuation",
                detail=following.strip(),
                justification=justification_for(lines, index + 2),
            )
        )
    return findings


def filter_pattern_groups(document: Any) -> list[list[str]]:
    """One ``paths:`` list per diff-driven trigger, in file order.

    Grouped per trigger rather than flattened, because ``!`` negation is
    *ordered within a list*: a change is selected by the last entry that matches
    it. Flattening would let a positive entry on ``push`` cancel an exclusion on
    ``pull_request`` and vice versa.

    A workflow is then considered to cover a path when **any** of its triggers
    does. That union across triggers is deliberate: grading each trigger
    separately would report ``security-nuclei-templates.yml``'s intentionally
    narrower ``push`` filter — the template directory only, while the
    ``pull_request`` filter also watches the validator hook and the pins file —
    as findings naming no defect. Whether the *right lane* fires is the sibling
    shape (#1302's deeper half: a pin assertion living only in a nightly that
    blocks nothing) and needs a judgement this one does not make.
    """
    if not isinstance(document, dict):
        return []
    # PyYAML resolves the bare key ``on:`` to the boolean True (YAML 1.1), which
    # is why every workflow parser in this repository has to look for both.
    trigger_block = document.get(True, document.get("on"))
    if not isinstance(trigger_block, dict):
        return []
    groups: list[list[str]] = []
    for trigger in DIFF_TRIGGERS:
        spec = trigger_block.get(trigger)
        if not isinstance(spec, dict):
            continue
        entries = spec.get("paths")
        if not isinstance(entries, list):
            continue
        group = [entry for entry in entries if isinstance(entry, str)]
        if group:
            groups.append(group)
    return groups


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub path-filter pattern into an anchored regex.

    GitHub's filter globs, as documented for ``on.<event>.paths``: ``*`` matches
    any run of characters except ``/``, ``**`` matches any run including ``/``,
    ``?`` matches exactly one character except ``/``, and ``[…]`` is a character
    range. Everything else is literal — notably ``.``, which a naive
    ``fnmatch``-style translation would turn into "any character" and quietly
    widen every entry.
    """
    out: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if pattern[index + 1 : index + 2] == "*":
                out.append(".*")
                index += 2
                continue
            out.append("[^/]*")
            index += 1
            continue
        if char == "?":
            out.append("[^/]")
            index += 1
            continue
        if char == "[":
            close = pattern.find("]", index + 1)
            if close != -1:
                body = pattern[index + 1 : close]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append(f"[{body}]")
                index = close + 1
                continue
        out.append(re.escape(char))
        index += 1
    return re.compile("^" + "".join(out) + "$")


_ON_KEY = re.compile(r"^(?:on|true|\"on\"|'on'):")


def trigger_block_lines(lines: list[str]) -> set[int]:
    """The 1-based line numbers of the top-level ``on:`` block.

    Excluded from reference extraction, because a ``paths:`` entry is the filter
    — not something the workflow reads. Two reasons it has to be skipped rather
    than left to cover itself: a negated entry (``!scripts/ci/**``) would
    otherwise be read as a *reference* to the very directory it removes from the
    trigger, and a ``branches:``/``tags:`` value can collide with a real path.

    A ``dorny/paths-filter`` block inside ``jobs:`` is deliberately NOT skipped.
    Those entries are the workflow reasoning about paths, and they are how the
    ``docker-publish.yml`` side-service drift surfaced: the fan-out filtered on
    ``src/inference-service/**`` while the trigger did not list it, so a push
    touching only that tree published nothing.
    """
    start = None
    for index, line in enumerate(lines):
        if start is None:
            if _ON_KEY.match(line):
                start = index
            continue
        if line and not line[0].isspace() and not line.startswith("#"):
            return set(range(start + 1, index + 1))
    if start is None:
        return set()
    return set(range(start + 1, len(lines) + 1))


#: Environment variables through which git redirects a command away from the
#: repository named by ``-C``. A commit hook inherits ``GIT_INDEX_FILE`` (an
#: absolute temporary index for ``git commit -a`` / ``git commit <path>``) and
#: ``git -C <other> ls-files`` would then list *this* repository's index while
#: ``rev-parse`` still reports the other tree — the toplevel guard passes and the
#: wrong index answers. For this repository's own root the inherited index is
#: the right one (it is the commit being made); for any other root it is not.
_GIT_REDIRECTING_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)


def _run_git(tree_root: Path, *arguments: str) -> tuple[str | None, str]:
    """Run one ``git`` command inside *tree_root*.

    Returns:
        ``(stdout, "")`` on success, or ``(None, reason)`` when git could not
        answer — absent from PATH, not a repository, refused (``safe.directory``),
        or hung past :data:`GIT_TIMEOUT_SECONDS`. The reason is what the report
        prints when the checker has to fall back to the filesystem, so a
        workstation that is back on the #1340 predicate can see why.
    """
    env = os.environ
    if tree_root.resolve() != REPO_ROOT.resolve():
        env = {key: value for key, value in os.environ.items() if key not in _GIT_REDIRECTING_VARIABLES}
    try:
        completed = subprocess.run(
            ["git", "-C", str(tree_root), *arguments],
            capture_output=True,
            encoding="utf-8",
            errors="surrogateescape",
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        return None, "git is not on PATH"
    except subprocess.TimeoutExpired:
        return None, f"git {arguments[0]} did not answer within {GIT_TIMEOUT_SECONDS}s"
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"git {arguments[0]} could not run: {exc}"
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        return None, f"git {arguments[0]} exited {completed.returncode}" + (f": {detail[-1]}" if detail else "")
    return completed.stdout, ""


def _implied_directories(files: frozenset[str]) -> frozenset[str]:
    """Every directory implied by a tracked file.

    Git tracks files, not directories: ``src/backend`` exists only because
    something below it does. The ``is_dir`` half of the path rule needs those
    directories by name — ``src/backend/app/**`` counts as reaching
    ``src/backend`` — so they are derived here instead of probed on disk, where
    an untracked sibling would answer for them.
    """
    directories: set[str] = set()
    for entry in files:
        parent = entry.rpartition("/")[0]
        # Stop at the first ancestor already known: every ancestor above it was
        # added by whichever entry added that one. Measured on this checkout,
        # the PurePosixPath walk this replaces cost 60 ms of a 65 ms index build.
        while parent and parent not in directories:
            directories.add(parent)
            parent = parent.rpartition("/")[0]
    return frozenset(directories)


@dataclass(frozen=True)
class TreeIndex:
    """Which repo-relative paths count as existing in one checkout.

    "Exists" has to mean **tracked by git**, not "is on disk". The predicate was
    ``(tree_root / candidate).exists()`` until #1340, and that made the verdict a
    function of *untracked* state, in both directions at once:

    * **False positive.** ``test-reports/e2e/`` is gitignored E2E output.
      ``e2e-smoke.yml`` names it as the report path of its ``dorny/test-reporter``
      step, so the same workflows scanned green on a fresh CI checkout and red on
      every workstation that had run the suite once — and the hook is
      ``always_run``, so it blocked unrelated commits. There is no ``paths:``
      entry that *should* cover it: it is an artefact the run produces, and
      adding one would mean "re-run E2E when a report changes".
    * **Two answers for one tree.** CI checks out only tracked files, so a
      workstation and CI could disagree about the same workflow. Only the
      false-positive half changes here: a path that is not in the repository
      cannot appear in a diff, so whether a ``paths:`` filter covers it is not
      a meaningful question, and such a reference is dropped rather than
      reported — on the workstation now as in CI before.

    Reading the **index** (``git ls-files``) rather than ``HEAD`` is deliberate:
    the pre-commit hook runs while a commit is being made, and a newly added file
    is in the index before it is in any commit. A workflow and the file it starts
    reading are therefore judged together, in the commit that introduces them.

    Known blind spots, stated rather than papered over: a submodule is a
    gitlink and a symlink is a mode-120000 entry, so ``git ls-files`` reports
    both as files — :meth:`is_dir` says no, and a reference *through* them is
    not tracked. This repository has neither today; the :meth:`exists` reading
    then reports less rather than more, and :attr:`resolution` says which
    predicate answered so a surprising verdict can be traced.
    """

    root: Path
    #: Tracked paths, or ``None`` when git could not answer — see
    #: :meth:`for_root` for what that fallback is and who reaches it.
    tracked_files: frozenset[str] | None
    tracked_directories: frozenset[str]
    #: ``"index"`` when git answered, ``"filesystem"`` on the fallback.
    resolution: str
    #: Why the fallback was taken; empty on the index path.
    reason: str

    @classmethod
    def for_root(cls, root: Path) -> TreeIndex:
        """Index *root*, falling back to the filesystem when git cannot answer.

        The fallback is the filesystem listing the predicate used before #1340,
        and it is reached in exactly two situations:

        * **The tree is not a git checkout at all** — a ``git archive`` export or
          a source tarball. There "on disk" and "tracked" coincide, so the
          fallback is not an approximation.
        * **The tree root is not itself the root of a work tree.** ``git -C
          <subdir> ls-files`` answers relative to the subdirectory, so a root
          *inside* a repository would get a listing whose names do not match the
          repo-relative references the workflows use; the toplevel is compared
          so that "tracked" always means "tracked at this root".

        Every other failure — ``git`` absent, ``safe.directory`` refusing the
        checkout, a hung invocation — takes the fallback too, and *that* one is
        the #1340 predicate coming back on a workstation. It is therefore never
        silent: :attr:`reason` names it, the report prints it, and the JSON
        carries the resolution.

        Raises:
            WorkflowIntegrityCheckError: the root is a work tree with **nothing
                tracked** (a fresh ``git init`` over an export). Every reference
                would then resolve to "not tracked" and the shape would pass
                without measuring anything — the vacuity this file refuses.
        """
        toplevel, reason = _run_git(root, "rev-parse", "--show-toplevel")
        if toplevel is None or not toplevel.strip():
            return cls._fallback(root, reason or "not a git work tree")
        if Path(toplevel.strip()).resolve() != root.resolve():
            return cls._fallback(root, f"{root} is inside the work tree {toplevel.strip()}, not its root")
        listing, reason = _run_git(root, "ls-files", "-z")
        if listing is None:
            return cls._fallback(root, reason)
        files = frozenset(entry for entry in listing.split("\0") if entry)
        if not files:
            raise WorkflowIntegrityCheckError(
                f"{root} is a git work tree with nothing tracked — every path reference would "
                "resolve to 'not tracked' and the check would pass without measuring anything; "
                "add the files, or point --tree-root at a plain export"
            )
        return cls(
            root=root,
            tracked_files=files,
            tracked_directories=_implied_directories(files),
            resolution="index",
            reason="",
        )

    @classmethod
    def _fallback(cls, root: Path, reason: str) -> TreeIndex:
        return cls(
            root=root,
            tracked_files=None,
            tracked_directories=frozenset(),
            resolution="filesystem",
            reason=reason,
        )

    def exists(self, reference: str) -> bool:
        """Whether *reference* names a tracked file or a tracked directory."""
        if self.tracked_files is None:
            return (self.root / reference).exists()
        return reference in self.tracked_files or reference in self.tracked_directories

    def is_dir(self, reference: str) -> bool:
        """Whether *reference* names a directory holding tracked files."""
        if self.tracked_files is None:
            return (self.root / reference).is_dir()
        return reference in self.tracked_directories


def path_references(lines: list[str], tree: TreeIndex) -> dict[str, int]:
    """Every repo-relative path the workflow *references*, and where first.

    A reference is a **literal** path in the executable part of a line outside
    the ``on:`` block. The comment is stripped first, and that distinction is
    load-bearing: leaving comments in raised eleven candidates against four real
    ones, because this repository argues about paths in prose at length. A path
    named in a comment is a mention, not a read.

    Two filters make the candidate set precise enough for a required lane:

    * **at least two segments.** A single name cannot be told apart from a shell
      word, and existence cannot rescue it — ``docker``, ``helm`` and ``spec``
      are all real directories *and* plausible English.
    * **it must be tracked in the checkout.** This is what removes URLs
      (``github.com/projectdiscovery/nuclei-templates``), image references
      (``ghcr.io/nolte/kamerplanter-backend``), action references (the part of
      ``actions/checkout@<sha>`` before the ``@``) and runtime artefacts the
      workflow writes rather than reads (``results.sarif``, ``test-reports/e2e``).
      It also means the guard says nothing about a reference to a file that is
      not in the repository — that is a different defect, and a loud one at
      runtime.

      *Tracked*, not merely present on disk: see :class:`TreeIndex` for why the
      distinction is the whole of #1340. A filesystem probe makes the verdict a
      function of whatever the last local run left behind, so the same workflows
      passed in CI and failed on a workstation.

    Known blind spot, stated rather than papered over: a path assembled from
    variables (``"$ROOT/tool.sh"``), or reached indirectly through a ``task``
    target that reads a third file, is invisible here. It would still have
    caught all four incidents in the module docstring.
    """
    skipped = trigger_block_lines(lines)
    found: dict[str, int] = {}
    for number, line in enumerate(lines, start=1):
        if number in skipped:
            continue
        for match in _PATH_CANDIDATE.finditer(_strip_comment(line)):
            candidate = match.group(1)
            # `a/./b` is `a/b` to the filesystem and was to the old predicate;
            # the index is an exact-string set, so normalise before looking up.
            parts = [part for part in candidate.split("/") if part != "."]
            candidate = "/".join(parts)
            if len(parts) < 2 or ".." in parts or "" in parts:
                continue
            if not tree.exists(candidate):
                continue
            found.setdefault(candidate, number)
    return found


def _comment_block_reasons(lines: list[str]) -> list[str]:
    """Every justification reason in the file, joined across its comment block.

    Joining matters: a reason long enough to be worth reading wraps over several
    ``#`` lines, and the path it names is as likely to land on the second line
    as the first.
    """
    reasons: list[str] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip().startswith("#"):
            index += 1
            continue
        start = index
        while index < len(lines) and lines[index].strip().startswith("#"):
            index += 1
        block = " ".join(line.strip().lstrip("#").strip() for line in lines[start:index])
        marker = block.find(JUSTIFICATION_MARKER.lstrip("# "))
        if marker != -1:
            reasons.append(block[marker + len(JUSTIFICATION_MARKER.lstrip("# ")) :].strip())
    return reasons


def path_justification_for(lines: list[str], line: int, reference: str) -> str | None:
    """The reason exempting *reference*, or ``None``.

    The shared placements first — the reference's own line, or the comment block
    directly above it. Then one placement this shape adds: a marker **anywhere**
    in the same workflow whose reason names the path verbatim.

    That extra placement is not laxity, it is reachability. A reference can sit
    inside a ``script:`` block's JavaScript or a quoted shell string, where a
    trailing ``#`` is a syntax error rather than a comment — the real case is
    ``security-nuclei-postmerge.yml``, which quotes ``docs/security/nuclei-triage.md``
    in the body of the issue it opens. And the honest home for "this reference
    deliberately does not widen the trigger" is beside the ``paths:`` filter it
    declines to widen. Requiring the path to appear in the reason is what stops
    the placement from becoming a file-wide silencer: one marker exempts one
    named path, not the file.
    """
    direct = justification_for(lines, line)
    if direct is not None:
        return direct
    for reason in _comment_block_reasons(lines):
        if reference in reason and len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def entry_matches(pattern: str, reference: str, *, is_directory: bool) -> bool:
    """Whether one filter pattern selects *reference*.

    A **file** matches when the pattern matches it outright. A **directory**
    matches when the pattern matches the directory, matches something beneath it,
    or is itself rooted beneath it — ``src/backend/app/**`` counts as reaching
    ``src/backend``. That last case is partial coverage, and it counts on
    purpose: this shape reports the *absence* of any trigger path into a
    reference, not the completeness of one, and grading completeness would demand
    a written reason for entries that do fire.
    """
    regex = glob_to_regex(pattern)
    if regex.match(reference):
        return True
    if not is_directory:
        return False
    return bool(
        regex.match(f"{reference}/{_DIRECTORY_PROBE}") or pattern.startswith(f"{reference}/")
    )


def covers(group: list[str], reference: str, *, is_directory: bool) -> bool:
    """Whether one trigger's ``paths:`` list selects a change to *reference*.

    GitHub evaluates the list in order and lets the **last** matching entry
    decide, so a ``!`` exclusion after a positive pattern removes what the
    positive pattern admitted. Modelling that rather than merely dropping ``!``
    entries matters for honesty as much as correctness: with the entries simply
    skipped, the leading ``!`` was escaped into the regex and could never match
    anything, so the line that dropped them was unobservable — a guard nobody can
    watch fail, which is the class this whole file exists to refuse.
    """
    verdict = False
    for entry in group:
        negated = entry.startswith("!")
        pattern = entry[1:] if negated else entry
        if entry_matches(pattern, reference, is_directory=is_directory):
            verdict = not negated
    return verdict


def scan_path_filters(path: Path, lines: list[str], document: Any, tree: TreeIndex) -> list[Finding]:
    """Find files the workflow reads that its own ``paths:`` filter excludes.

    Only workflows that *have* a diff-driven ``paths:`` filter are in scope: a
    workflow without one runs on every change, so it cannot drift away from one.

    An unfiltered sibling trigger does **not** exempt a filtered workflow.
    ``schedule`` and ``workflow_dispatch`` fire regardless of the diff, and
    ``security-nuclei-postmerge.yml``'s label-driven ``pull_request`` leg fires
    only when somebody remembers the label — none of them puts the change that
    breaks a check in front of that check automatically, which is the whole
    property being asserted.

    Coverage is decided per reference — see :func:`covers`.
    """
    groups = filter_pattern_groups(document)
    if not groups:
        return []

    findings: list[Finding] = []
    for reference, line in path_references(lines, tree).items():
        is_directory = tree.is_dir(reference)
        if any(covers(group, reference, is_directory=is_directory) for group in groups):
            continue
        findings.append(
            Finding(
                path=path,
                line=line,
                kind="uncovered_path_reference",
                detail=f"reads '{reference}', which no paths: entry of this workflow covers",
                justification=path_justification_for(lines, line, reference),
            )
        )
    return sorted(findings, key=lambda finding: finding.line)


def scan_needs(path: Path, lines: list[str], document: Any) -> list[Finding]:
    """Find jobs that read a dependency's outputs without reading its result.

    Only jobs whose own ``if:`` overrides GitHub's dependency gating are
    considered — see the module docstring for why the others are safe.
    """
    if not isinstance(document, dict):
        return []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []

    findings: list[Finding] = []
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        condition = job.get("if")
        condition_text = condition if isinstance(condition, str) else ""
        if not any(override in condition_text for override in GATING_OVERRIDES):
            continue

        texts = _strings(job)
        consumed = {match for text in texts for match in _NEEDS_OUTPUT.findall(text)}
        checked = {match for text in texts for match in _NEEDS_RESULT.findall(text)}
        if "*" in checked:
            continue
        unguarded = sorted(consumed - checked)
        if not unguarded:
            continue

        line = _job_line(lines, str(name))
        findings.append(
            Finding(
                path=path,
                line=line,
                kind="unguarded_needs_output",
                detail=f"job '{name}' reads needs.{', needs.'.join(unguarded)}.outputs, never .result",
                justification=justification_for(lines, line),
            )
        )
    return findings


def scan_file(path: Path, tree: TreeIndex) -> list[Finding]:
    """Every finding in one workflow file.

    Args:
        path: The workflow file.
        tree: The indexed checkout the workflow's path references are resolved
            against. Passed in rather than built here because building it
            shells out to ``git``, and doing that once per workflow file would
            be two dozen subprocesses per run.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowIntegrityCheckError(f"cannot read {path}: {exc}") from exc
    lines = source.splitlines()
    try:
        document = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise WorkflowIntegrityCheckError(f"cannot parse {path}: {exc}") from exc

    findings = [
        *scan_text(path, lines),
        *scan_continuations(path, lines),
        *scan_needs(path, lines, document),
        *scan_path_filters(path, lines, document, tree),
    ]
    return sorted(findings, key=lambda finding: (finding.line, finding.kind))


def collect(
    scan_root: Path, tree_root: Path | None = None, *, tree: TreeIndex | None = None
) -> list[Finding]:
    """Every finding below *scan_root*, justified or not.

    Args:
        scan_root: The workflow directory to scan.
        tree_root: The checkout path references are resolved against. Indexed
            once here and shared by every file, so one ``git`` call answers for
            the whole run.
        tree: An already built index; ``main`` builds it first so it can say
            which predicate answered.
    """
    if not scan_root.exists():
        raise WorkflowIntegrityCheckError(f"scan root does not exist: {scan_root}")
    paths = sorted(
        path for path in scan_root.rglob("*") if path.suffix in {".yml", ".yaml"}
    )
    if not paths:
        raise WorkflowIntegrityCheckError(f"no workflow files under {scan_root}")
    if tree is None:
        tree = TreeIndex.for_root(REPO_ROOT if tree_root is None else tree_root)
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path, tree))
    return findings


def report(
    findings: list[Finding], *, list_all: bool, as_json: bool, tree: TreeIndex | None = None
) -> int:
    """Print the outcome and return the process exit code.

    When *tree* resolved against the filesystem, say so — on stderr for the
    human report and as ``resolution`` in the JSON — because that is the #1340
    predicate, and a verdict that depends on untracked files must be
    recognisable as one.
    """
    unjustified = [finding for finding in findings if not finding.justified]
    justified = [finding for finding in findings if finding.justified]
    if tree is not None and tree.resolution != "index":
        print(
            "check_workflow_gate_integrity: path references resolved against the FILESYSTEM, "
            f"not the git index ({tree.reason}); untracked files can change this verdict",
            file=sys.stderr,
        )

    if as_json:
        print(
            json.dumps(
                {
                    "sites": len(findings),
                    "resolution": tree.resolution if tree is not None else "index",
                    "justified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                            "reason": finding.justification,
                        }
                        for finding in justified
                    ],
                    "unjustified": [
                        {
                            "file": finding.relative(),
                            "line": finding.line,
                            "kind": finding.kind,
                            "detail": finding.detail,
                        }
                        for finding in unjustified
                    ],
                },
                indent=2,
            )
        )
        return EXIT_DEFECTS if unjustified else EXIT_OK

    if unjustified:
        print(
            f"check_workflow_gate_integrity: {len(unjustified)} site(s) where a check cannot fail\n"
        )
        for finding in unjustified:
            print(f"  {finding.relative()}:{finding.line}: {KIND_LABELS[finding.kind]}")
            print(f"      {finding.detail}")
        print(
            "\nNFR-018 §2: a check that cannot report a failure is indistinguishable from\n"
            "one that is not running. Either restore the verdict, or say — where it\n"
            "stands, on the same line or in the comment block directly above it — why the\n"
            "discarded outcome is not a verdict:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <why this cannot hide a failure>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        if any(finding.kind == "uncovered_path_reference" for finding in unjustified):
            print(
                "\nFor an uncovered path (#1313): the workflow reads a file that cannot\n"
                "trigger it, so the one change most able to break this check is the one\n"
                "change that never runs it. Add the path — or a pattern covering it — to\n"
                "the workflow's `paths:` filter. If widening the trigger would be wrong\n"
                "(a path quoted in an error message, a file read only by a dispatched\n"
                "job), write the reason and NAME THE PATH in it; the marker may then sit\n"
                "anywhere in that workflow, including beside the `paths:` filter itself."
            )
        return EXIT_DEFECTS

    print(
        f"check_workflow_gate_integrity: OK — {len(justified)} justified site(s), no unexplained "
        "swallowed verdict."
    )
    if list_all:
        for finding in justified:
            print(
                f"  {finding.relative()}:{finding.line} [{finding.kind}]: {finding.justification}"
            )
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every swallowed verdict carries a reason, 1 when at least one
        does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_workflow_gate_integrity.py",
        description=(
            "Refuse a GitHub Actions gate that cannot fail (NFR-018 §2): a discarded exit "
            "code, continue-on-error, a job reading a dependency's outputs without its "
            "result, a comment truncating a continued command, or a file the workflow reads "
            "that its own paths: filter excludes. A site may stand by carrying a "
            f"'{JUSTIFICATION_MARKER} <reason>' comment."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the workflow directory to scan (default: {DEFAULT_SCAN_ROOT})",
    )
    parser.add_argument(
        "--tree-root",
        metavar="PATH",
        default=None,
        help=(
            "the checkout path references are resolved against: its TRACKED files, "
            "or its filesystem when it is not the root of a git work tree "
            "(default: this repository)"
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="also name every justified site when the check passes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    raw = args.scan_root or DEFAULT_SCAN_ROOT
    scan_root = Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw
    tree_root = Path(args.tree_root).resolve() if args.tree_root else REPO_ROOT

    try:
        tree = TreeIndex.for_root(tree_root)
        findings = collect(scan_root, tree=tree)
    except WorkflowIntegrityCheckError as exc:
        print(f"check_workflow_gate_integrity: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(findings, list_all=args.list_all, as_json=args.json, tree=tree)


if __name__ == "__main__":
    raise SystemExit(main())
