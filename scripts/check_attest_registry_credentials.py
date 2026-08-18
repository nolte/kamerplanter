#!/usr/bin/env python3
"""Refuse an attestation push that has no Docker-store credential to push with.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_attest_registry_credentials.py
    python3 scripts/check_attest_registry_credentials.py --list   # name every site
    python3 scripts/check_attest_registry_credentials.py --json   # machine-readable

**The incident (#1218).** ``publish-helm-charts`` in ``docker-publish.yml``
logged in with ``helm registry login`` and then ran
``actions/attest-build-provenance`` with ``push-to-registry: true``. Every run
since 2026-08-01 died with::

    Error: No credentials found for registry ghcr.io

Two published releases (v0.1.0, v0.2.0) lost their chart ``.tgz``, their
``docker-compose-<version>.yml``, their ``.env.example-<version>`` and the
release body's Packages block, because the failing job took
``update-release-assets`` down with it. Seventeen days, nobody noticed.

**Why the YAML gives no hint.** The two logins write *different files*.
``helm registry login`` writes Helm's own store (``$HELM_REGISTRY_CONFIG``,
default ``~/.config/helm/registry/config.json``). ``actions/attest`` — which
``attest-build-provenance`` delegates to — reads exactly one path, from its
bundled ``dist/index.js`` at the pinned SHA ``508db95``, lines 62801-62824::

    const getRegistryCredentials = (imageName) => {
        const { registry } = parseImageName(imageName);
        const dockerConfigFile = path.join(os.homedir(), '.docker', 'config.json');
        ...
        if (!creds) {
            throw new Error(`No credentials found for registry ${registry}`);
        }

Nothing in a workflow file states that dependency, so the eight image jobs (which
use ``docker/login-action`` and succeed) and the chart job (which did not) looked
interchangeable. This checker states it.

**What it enforces.** For every job containing a step that uses an
``actions/attest*`` action with ``push-to-registry`` true, that same job must
contain a step that writes the *Docker* credential store — a
``docker/login-action`` step, or a ``run:`` step invoking ``docker login`` —
and that step must actually have run by the time the attestation does:

* **Earlier in the job.** Steps run in file order, and the action reads
  ``~/.docker/config.json`` when *it* runs. A login below the attest step leaves
  the file unwritten at exactly the moment it is read, and the run dies with the
  same ``No credentials found for registry <host>`` this whole gate exists for.
* **Unconditionally**, or under the attest step's own ``if:``. Whether an
  expression is true on the release run is not statically decidable, so a login
  guarded by a condition the attest step does not share is treated as *not*
  satisfying the requirement rather than as satisfying it — the lenient reading
  is the one that reproduced the incident. Two steps carrying the *same*
  condition run or skip together, which is decidable and therefore accepted.

When both the attested subject's registry and the login's registry resolve to
literal hostnames, they must also be the same host; when either is an unresolved
expression the comparison is skipped rather than guessed (see §Precision).

**The escape hatch.** A site may stand by carrying a justification on its own
line or in the comment block directly above the step::

    # attest-credentials-ok: HELM_REGISTRY_CONFIG is pointed at ~/.docker/config.json above

The reason is mandatory and must be more than a word, so the hatch cannot be
used as a silencer. This mirrors ``scripts/check_workflow_gate_integrity.py``'s
``# gate-integrity-ok:`` marker deliberately: one convention, not two.

**Precision, and what is deliberately not checked.**

* ``push-to-registry`` written as an expression (``${{ … }}``) is treated as
  *possibly* true and therefore requires a login. The escape hatch is the answer
  when it is provably false — the reverse default would reproduce this incident
  the first time somebody parameterised the flag.
* A registry spelled as an unresolved expression makes the host comparison
  unresolvable, so only the *presence* rule applies there. Only ``${{ env.X }}``
  is substituted, from the workflow-level and job-level ``env:`` mappings; the
  ``github``/``matrix``/``secrets`` contexts are not knowable statically.
* A ``${{ … }}`` expression inside a ``run:`` command line is collapsed to one
  opaque token *before* the line is split on whitespace. It contains spaces, so
  naive tokenising tears it into three pieces and makes ``docker login -u
  ${{ github.actor }} … ghcr.io`` read ``github.actor`` as the registry — a
  spurious mismatch that would turn the required lane red on a correct workflow.
* A ``docker login`` continued across lines with a trailing backslash is read as
  the one command it is; a ``docker login`` with no arguments at all means
  Docker Hub, which is what the daemon does with it.
* A login performed by a composite action or a reusable workflow is invisible
  here. That is what the marker is for.

**Why not import the sibling checker's helpers.** These gates run in the required
``static`` job on a bare runner, invoked one file at a time by pre-commit; they
are scripts, not a package, and ``scripts/`` is on no import path. The
justification helper is therefore duplicated rather than shared — twenty lines
against a cross-file import that only works by accident of the working directory.

Standard library plus PyYAML — the same isolated pre-commit environment the
gate-integrity hook uses, because the required ``static`` job runs on a bare
runner with none of the project's dependencies installed.

Traces to issue #1218 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
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
JUSTIFICATION_MARKER = "# attest-credentials-ok:"
MIN_JUSTIFICATION_CHARS = 12

#: ``actions/attest``, ``actions/attest-build-provenance``, ``actions/attest-sbom``
#: — the whole family shares the one ``getRegistryCredentials`` implementation.
ATTEST_ACTION = re.compile(r"^actions/attest(?:-[a-z0-9-]+)?@")

#: The step form that writes ``~/.docker/config.json``.
DOCKER_LOGIN_ACTION = re.compile(r"^docker/login-action@")

#: The shell form of the same thing. ``docker login`` writes the Docker store
#: whether it is run by the action or by hand.
DOCKER_LOGIN_RUN = re.compile(r"\bdocker\s+login\b")

#: Helm's own store — the near-miss that caused #1218. Detected only to make the
#: finding say what the job *did* do instead.
HELM_LOGIN_RUN = re.compile(r"\bhelm\s+registry\s+login\b")

#: A GitHub Actions expression left in a value we would otherwise compare.
EXPRESSION = re.compile(r"\$\{\{")

#: A whole ``${{ … }}`` expression, collapsed to :data:`EXPRESSION_TOKEN` before
#: a shell command line is split on whitespace. ``DOTALL`` because a ``run:``
#: block may wrap one across lines.
EXPRESSION_SPAN = re.compile(r"\$\{\{.*?\}\}", re.DOTALL)

#: The opaque stand-in for a collapsed expression. Not spellable in YAML, so it
#: can never collide with a real registry name.
EXPRESSION_TOKEN = "\x00expression\x00"

#: ``docker login`` flags that take no value. Everything else spelled ``-x`` or
#: ``--xy`` consumes the token after it, which is how ``-u <user>`` avoids being
#: mistaken for the registry argument.
VALUELESS_LOGIN_FLAGS = frozenset({"--password-stdin"})

#: Shell punctuation that ends the ``docker login`` command line.
COMMAND_SEPARATORS = frozenset({"|", "||", "&", "&&", ";", ">", ">>", "2>&1"})

#: ``if:`` values under which a step always runs, so they are no condition at
#: all. ``success()`` is the implicit default; ``always()`` and ``!cancelled()``
#: widen it. Anything else is an expression whose run-time value is unknowable
#: here, and is therefore treated as a real condition.
ALWAYS_RUN_CONDITIONS = frozenset({"true", "success()", "always()", "!cancelled()", "! cancelled()"})

#: ``${{ env.NAME }}`` — the one context resolvable from the file itself.
ENV_REFERENCE = re.compile(r"\$\{\{\s*env\.([A-Za-z_][A-Za-z0-9_-]*)\s*\}\}")

#: Canonical name for Docker Hub, which spells itself several ways.
DOCKER_HUB = "docker.io"
DOCKER_HUB_ALIASES = frozenset({"docker.io", "index.docker.io", "registry-1.docker.io", "registry.hub.docker.com"})

#: A list item at or above the indentation of the line we are anchoring, i.e.
#: the ``- `` that starts the step.
LIST_ITEM = re.compile(r"^(\s*)-\s")

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class AttestCredentialsCheckError(Exception):
    """A usage or environment problem — not a finding about the workflows."""


@dataclass(frozen=True)
class Finding:
    """One attesting job that cannot reach the registry it attests to."""

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


@dataclass(frozen=True)
class LoginStep:
    """A step that writes ``~/.docker/config.json``.

    Attributes:
        position: Index among the job's steps, so a login can be compared
            against the attest step it is supposed to precede.
        registry: The host it authenticates against, or ``None`` when that
            cannot be resolved statically (presence satisfied, comparison
            skipped).
        condition: The step's normalised ``if:``, or ``None`` when it always
            runs.
    """

    position: int
    registry: str | None
    condition: str | None


@dataclass(frozen=True)
class AttestSite:
    """One ``actions/attest*`` step that pushes its attestation to a registry.

    Attributes:
        ordinal: Index among *all* ``actions/attest*`` steps of the job —
            including the ones that do not push. This is the number that ties
            the site back to its ``uses:`` line, because the line scan sees
            every attest step and cannot tell the pushing ones apart. Counting
            pushing steps only is exactly the desynchronisation that let a
            justification on a harmless step exculpate a real violation.
        position: Index among the job's steps.
        registry: The attested subject's registry, or ``None`` when unresolvable.
        condition: The step's normalised ``if:``, or ``None``.
    """

    ordinal: int
    position: int
    registry: str | None
    condition: str | None


#: Human wording per finding kind, used in the report.
KIND_LABELS = {
    "attest_without_docker_login": "nothing writes ~/.docker/config.json in this job",
    "attest_login_after_attest_step": "the Docker login runs only after the attestation",
    "attest_login_only_conditional": "the Docker login may be skipped on the run that attests",
    "attest_login_registry_mismatch": "the Docker login targets a different registry",
}


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the site on *line*, or ``None``.

    Accepted on the site's own line (trailing comment) and anywhere in the
    contiguous comment block directly above it. The block form matters here:
    this repository explains its steps in a comment paragraph above the ``- name:``
    key — ``docker-publish.yml`` lines 161-168 are exactly that — and a marker is
    most useful inside the paragraph that already argues the point.

    Args:
        lines: The file's lines, without terminators.
        line: 1-based line the finding is anchored to.

    Returns:
        The reason text when a marker with a long-enough reason is present.
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


def step_start_line(lines: list[str], line: int) -> int:
    """The 1-based line of the ``- `` that starts the step containing *line*.

    Anchoring the finding at the ``uses:`` key would put the justification block
    *below* the step's ``- name:``, where nobody writes comments. Walking up to
    the list item puts the marker where this repository already comments steps.

    A ``- `` deeper than the anchor's own indentation is shell content inside a
    ``run:`` block, not a step, hence the indentation bound.
    """
    anchor_indent = len(lines[line - 1]) - len(lines[line - 1].lstrip())
    for index in range(line - 1, -1, -1):
        match = LIST_ITEM.match(lines[index])
        if match and len(match.group(1)) <= anchor_indent:
            return index + 1
    return line


def job_line(lines: list[str], name: str) -> int:
    """The 1-based line of the ``<name>:`` key in the ``jobs:`` mapping."""
    pattern = re.compile(rf"^\s{{2,4}}{re.escape(name)}:\s*$")
    for index, line in enumerate(lines, start=1):
        if pattern.match(line):
            return index
    return 1


def job_ranges(lines: list[str], names: list[str]) -> dict[str, tuple[int, int]]:
    """Map every job name to the 1-based ``(first, last)`` line span it occupies.

    Used to attribute a ``uses: actions/attest…`` line to the job it sits in:
    ``docker-publish.yml`` carries nine of them, all identical in text.
    """
    starts = sorted((job_line(lines, name), name) for name in names)
    spans: dict[str, tuple[int, int]] = {}
    for position, (start, name) in enumerate(starts):
        end = starts[position + 1][0] - 1 if position + 1 < len(starts) else len(lines)
        spans[name] = (start, max(start, end))
    return spans


def resolve_env(text: str, env: dict[str, str]) -> str:
    """Substitute ``${{ env.NAME }}`` from *env*, following one level of nesting.

    Bounded iteration rather than recursion: a workflow env value referring to
    itself must not hang the linter.
    """
    for _ in range(4):
        replaced = ENV_REFERENCE.sub(lambda match: env.get(match.group(1), match.group(0)), text)
        if replaced == text:
            return text
        text = replaced
    return text


def canonical_registry(host: str) -> str:
    """Normalise a registry hostname for comparison."""
    stripped = re.sub(r"^https?://", "", host.strip()).strip("/").lower()
    stripped = stripped.removesuffix("/v1")
    if stripped in DOCKER_HUB_ALIASES or not stripped:
        return DOCKER_HUB
    return stripped


def registry_of_image(name: str) -> str | None:
    """The registry an image reference points at, or ``None`` if undecidable.

    Follows the Docker reference grammar: the first path segment is a registry
    only when it carries a ``.`` or a ``:``, or is ``localhost``; otherwise the
    reference is a Docker Hub short name. Deliberately looks at the head segment
    alone, so ``ghcr.io/${{ github.repository_owner }}/charts/x`` still resolves
    to ``ghcr.io`` even though the rest of the string never will.
    """
    head = name.strip().split("/")[0]
    if not head or EXPRESSION.search(head):
        return None
    if "." in head or ":" in head or head == "localhost":
        return canonical_registry(head)
    return DOCKER_HUB


def wants_registry_push(value: Any) -> bool:
    """Whether an attest step's ``push-to-registry`` can be true at run time.

    An expression counts as true: the flag's value is then unknowable here, and
    defaulting the unknown to *false* would reproduce #1218 the first time
    somebody parameterised it. The marker is the way to say otherwise.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip()
    if EXPRESSION.search(text):
        return True
    return text.lower() == "true"


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    """The job's steps, skipping anything that is not a mapping."""
    steps = job.get("steps")
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def _uses(step: dict[str, Any]) -> str:
    value = step.get("uses")
    return value.strip() if isinstance(value, str) else ""


def _run(step: dict[str, Any]) -> str:
    value = step.get("run")
    return value if isinstance(value, str) else ""


def _with(step: dict[str, Any]) -> dict[str, Any]:
    value = step.get("with")
    return value if isinstance(value, dict) else {}


def step_condition(step: dict[str, Any]) -> str | None:
    """The step's ``if:``, normalised, or ``None`` when the step always runs.

    Normalising strips an enclosing ``${{ … }}`` and collapses whitespace, so
    ``if: ${{ github.ref_type == 'tag' }}`` and ``if: github.ref_type == 'tag'``
    — the two spellings of one condition — compare equal. That comparison is the
    only thing this value is used for: two steps under the same condition run or
    skip together, which is decidable without knowing what the condition means.
    """
    raw = step.get("if")
    if raw is None:
        return None
    text = " ".join(str(raw).split())
    if text.startswith("${{") and text.endswith("}}"):
        text = " ".join(text[3:-2].split())
    if not text or text.lower() in ALWAYS_RUN_CONDITIONS:
        return None
    return text


def docker_login_steps(job: dict[str, Any], env: dict[str, str]) -> list[LoginStep]:
    """Every step in *job* that writes the Docker credential store.

    A ``registry`` of ``None`` means "this step logs in, but to a registry that
    cannot be resolved statically" — which satisfies the presence rule and
    suppresses the host comparison.
    """
    logins: list[LoginStep] = []
    for position, step in enumerate(_steps(job)):
        condition = step_condition(step)
        if DOCKER_LOGIN_ACTION.match(_uses(step)):
            raw = _with(step).get("registry")
            if raw is None:
                # login-action's documented default is Docker Hub.
                logins.append(LoginStep(position=position, registry=DOCKER_HUB, condition=condition))
                continue
            resolved = resolve_env(str(raw), env)
            registry = None if EXPRESSION.search(resolved) else canonical_registry(resolved)
            logins.append(LoginStep(position=position, registry=registry, condition=condition))
            continue
        run = resolve_env(_run(step), env)
        logins.extend(
            LoginStep(position=position, registry=registry, condition=condition)
            for registry in _shell_login_registries(run)
        )
    return logins


def _logical_line(text: str) -> str:
    """The first shell command line of *text*, following ``\\`` continuations.

    ``docker login \\`` with its registry on the next line is one command, and
    reading only the physical first line of it yields "no argument" — which
    resolves to Docker Hub and produces a mismatch against a GHCR subject that
    is not there. Returns ``""`` for empty input rather than indexing into an
    empty list: ``run: docker login`` with nothing after it is legal YAML, and a
    linter that raises ``IndexError`` on it prints a traceback instead of a
    verdict.
    """
    parts: list[str] = []
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            parts.append(stripped[:-1])
            continue
        parts.append(stripped)
        break
    return " ".join(parts)


def _shell_tokens(line: str) -> list[str]:
    """Split a command line, keeping each ``${{ … }}`` expression as one token.

    An expression contains spaces, so plain whitespace splitting tears it apart
    and hands its tail to whatever consumes the next token.
    """
    return EXPRESSION_SPAN.sub(EXPRESSION_TOKEN, line).split()


def _shell_login_registries(run: str) -> list[str | None]:
    """The registry of every ``docker login`` invocation in a ``run:`` block."""
    return [_registry_from_shell_login(run, match.end()) for match in DOCKER_LOGIN_RUN.finditer(run)]


def _registry_from_shell_login(run: str, start: int) -> str | None:
    """Best-effort registry argument of the ``docker login`` beginning at *start*.

    Returns ``None`` when it cannot be read off, which makes the step count as a
    login to an unknown registry — presence satisfied, comparison skipped. Being
    wrong in the strict direction here would report a job that does log in.
    """
    tokens = _shell_tokens(_logical_line(run[start:]))
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("-"):
            # `-u user` / `--username user` take a value; `--password-stdin` does not.
            if "=" not in token and token not in VALUELESS_LOGIN_FLAGS:
                index += 2
            else:
                index += 1
            continue
        # `in`, not `==`: a host only partly spelled as an expression
        # (`${{ env.REG }}.example.com`) is just as unresolvable, and guessing
        # at it would report a job that logs in exactly where it should.
        if EXPRESSION_TOKEN in token or token in COMMAND_SEPARATORS:
            return None
        return canonical_registry(token)
    # `docker login` with no argument authenticates against Docker Hub.
    return DOCKER_HUB


def attest_push_sites(job: dict[str, Any], env: dict[str, str]) -> list[AttestSite]:
    """Every attest step in *job* that pushes its attestation to a registry.

    Each site carries its ``ordinal`` among *all* attest steps of the job, not
    among the pushing ones: that ordinal is what the caller indexes the
    ``uses: actions/attest…`` line list with. Numbering the pushing steps
    consecutively desynchronises the two lists the moment a non-pushing attest
    step precedes a pushing one, which anchors the finding on the wrong step —
    and a justification comment on that wrong step then silently exempts the
    real violation.
    """
    sites: list[AttestSite] = []
    ordinal = 0
    for position, step in enumerate(_steps(job)):
        if not ATTEST_ACTION.match(_uses(step)):
            continue
        current = ordinal
        ordinal += 1
        options = _with(step)
        if not wants_registry_push(options.get("push-to-registry")):
            continue
        raw = options.get("subject-name")
        registry = registry_of_image(resolve_env(raw, env)) if isinstance(raw, str) else None
        sites.append(
            AttestSite(
                ordinal=current,
                position=position,
                registry=registry,
                condition=step_condition(step),
            )
        )
    return sites


def _attest_lines(lines: list[str], span: tuple[int, int]) -> list[int]:
    """Every ``uses: actions/attest…`` line inside a job's line span.

    The optional ``- `` prefix matters: a step whose *first* key is ``uses:``
    writes it on the list-item line itself, and skipping that form would anchor
    the finding at the job key instead — where nobody looks for the step, and
    where the justification comment above the step is out of reach.
    """
    first, last = span
    found = []
    for number in range(first, last + 1):
        stripped = lines[number - 1].strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if stripped.startswith("uses:") and ATTEST_ACTION.match(stripped[len("uses:") :].strip()):
            found.append(number)
    return found


def _env_of(node: Any) -> dict[str, str]:
    """The ``env:`` mapping of a workflow or job, as strings."""
    env = node.get("env") if isinstance(node, dict) else None
    if not isinstance(env, dict):
        return {}
    return {str(key): str(value) for key, value in env.items()}


def scan_document(path: Path, lines: list[str], document: Any) -> list[Finding]:
    """Every finding in one parsed workflow."""
    if not isinstance(document, dict):
        return []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []

    workflow_env = _env_of(document)
    named_jobs = [(str(name), job) for name, job in jobs.items() if isinstance(job, dict)]
    spans = job_ranges(lines, [name for name, _ in named_jobs])

    findings: list[Finding] = []
    for name, job in named_jobs:
        env = {**workflow_env, **_env_of(job)}

        sites = attest_push_sites(job, env)
        if not sites:
            continue

        logins = docker_login_steps(job, env)
        uses_helm_login = any(HELM_LOGIN_RUN.search(_run(step)) for step in _steps(job))
        anchors = _attest_lines(lines, spans[name])
        attest_steps = sum(1 for step in _steps(job) if ATTEST_ACTION.match(_uses(step)))
        # The line scan and the parsed steps must agree on how many attest steps
        # the job has, or the ordinal means nothing. When they do not, fall back
        # to the job key: a finding anchored one step too high is a nuisance, one
        # anchored on the wrong step is an exemption granted to the wrong site.
        aligned = len(anchors) == attest_steps

        for site in sites:
            anchor = anchors[site.ordinal] if aligned else spans[name][0]
            line = step_start_line(lines, anchor)

            usable = [
                login
                for login in logins
                if login.position < site.position and (login.condition is None or login.condition == site.condition)
            ]
            if not usable:
                kind, reason = _explain_unusable(logins, site, uses_helm_login=uses_helm_login)
                findings.append(
                    Finding(
                        path=path,
                        line=line,
                        kind=kind,
                        detail=(
                            f"job '{name}' attests to {site.registry or 'the attested registry'} "
                            f"with push-to-registry: true, but {reason}"
                        ),
                        justification=justification_for(lines, line),
                    )
                )
                continue

            known = [login.registry for login in usable if login.registry is not None]
            if site.registry is None or len(known) != len(usable) or site.registry in known:
                continue
            findings.append(
                Finding(
                    path=path,
                    line=line,
                    kind="attest_login_registry_mismatch",
                    detail=(
                        f"job '{name}' attests to {site.registry} with push-to-registry: true, "
                        f"but its Docker login(s) target {', '.join(sorted(set(known)))}"
                    ),
                    justification=justification_for(lines, line),
                )
            )
    return findings


def _explain_unusable(
    logins: list[LoginStep],
    site: AttestSite,
    *,
    uses_helm_login: bool,
) -> tuple[str, str]:
    """Why no Docker login covers *site*, as a finding kind and a clause.

    The three reasons need three different repairs — add a step, move a step,
    drop or match a condition — so they are three kinds rather than one. When
    both near misses are present the conditional one is reported: a login that
    is merely misplaced is also conditional, and the condition is the harder
    fact to see.
    """
    earlier_conditional = [login for login in logins if login.position < site.position and login.condition is not None]
    if earlier_conditional:
        conditions = ", ".join(sorted({f"`if: {login.condition}`" for login in earlier_conditional}))
        attest_condition = f"carries `if: {site.condition}`" if site.condition else "is unconditional"
        return (
            "attest_login_only_conditional",
            (
                f"every Docker login before that step is conditional ({conditions}) while the attest step "
                f"{attest_condition} — nothing here decides whether the login runs on the run that attests"
            ),
        )
    if logins:
        return (
            "attest_login_after_attest_step",
            (
                "the step that writes ~/.docker/config.json runs after it — steps run in file order, and "
                "the action reads the credential file at the moment it runs, not at the end of the job"
            ),
        )
    instead = (
        " — its only registry login is `helm registry login`, which writes Helm's own store" if uses_helm_login else ""
    )
    return (
        "attest_without_docker_login",
        f"no step in it writes ~/.docker/config.json{instead}",
    )


def scan_file(path: Path) -> list[Finding]:
    """Every finding in one workflow file."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AttestCredentialsCheckError(f"cannot read {path}: {exc}") from exc
    lines = source.splitlines()
    try:
        document = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise AttestCredentialsCheckError(f"cannot parse {path}: {exc}") from exc

    findings = scan_document(path, lines, document)
    return sorted(findings, key=lambda finding: (finding.line, finding.kind))


def collect(scan_root: Path) -> list[Finding]:
    """Every finding below *scan_root*, justified or not.

    Raises:
        AttestCredentialsCheckError: when the root is absent or holds no
            workflow files. Scanning nothing and reporting clean is the shape
            NFR-018 §2 forbids, so it is an error rather than a pass.
    """
    if not scan_root.exists():
        raise AttestCredentialsCheckError(f"scan root does not exist: {scan_root}")
    paths = sorted(path for path in scan_root.rglob("*") if path.suffix in {".yml", ".yaml"})
    if not paths:
        raise AttestCredentialsCheckError(f"no workflow files under {scan_root}")
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return findings


def report(findings: list[Finding], *, list_all: bool, as_json: bool) -> int:
    """Print the outcome and return the process exit code."""
    unjustified = [finding for finding in findings if not finding.justified]
    justified = [finding for finding in findings if finding.justified]

    if as_json:
        print(
            json.dumps(
                {
                    "sites": len(findings),
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
            f"check_attest_registry_credentials: {len(unjustified)} attesting job(s) with no Docker-store credential\n"
        )
        for finding in unjustified:
            print(f"  {finding.relative()}:{finding.line}: {KIND_LABELS[finding.kind]}")
            print(f"      {finding.detail}")
        print(
            "\n`actions/attest*` with `push-to-registry: true` reads ~/.docker/config.json and\n"
            "nothing else (its dist/index.js getRegistryCredentials). `helm registry login`\n"
            "writes Helm's own store, so a job that only has that one fails with\n"
            "'No credentials found for registry <host>' — issue #1218, which cost two\n"
            "releases their chart, their compose file, their env example and their release\n"
            "notes' Packages block.\n"
            "\n"
            "Add the step the eight image jobs already carry, ABOVE the attest step and\n"
            "without an `if:` the attest step does not itself carry:\n"
            "\n"
            "    - name: Log in to GHCR\n"
            "      uses: docker/login-action@<pinned-sha>\n"
            "      with:\n"
            "        registry: ${{ env.REGISTRY }}\n"
            "        username: ${{ github.actor }}\n"
            "        password: ${{ secrets.GITHUB_TOKEN }}\n"
            "\n"
            "…or say — on the step's own line, or in the comment block directly above it —\n"
            "why this job reaches the registry some other way:\n"
            "\n"
            f"    {JUSTIFICATION_MARKER} <how ~/.docker/config.json gets its entry>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    print(
        f"check_attest_registry_credentials: OK — every registry-pushing attestation has a "
        f"Docker-store login ({len(justified)} justified site(s))."
    )
    if list_all:
        for finding in justified:
            print(f"  {finding.relative()}:{finding.line} [{finding.kind}]: {finding.justification}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every registry-pushing attestation has a Docker-store login (or a
        reason), 1 when at least one does not, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_attest_registry_credentials.py",
        description=(
            "Refuse an `actions/attest*` step with `push-to-registry: true` in a job that "
            "never writes ~/.docker/config.json (issue #1218). A site may stand by carrying "
            f"a '{JUSTIFICATION_MARKER} <reason>' comment."
        ),
    )
    parser.add_argument(
        "--scan-root",
        metavar="PATH",
        default=None,
        help=f"the workflow directory to scan (default: {DEFAULT_SCAN_ROOT})",
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

    try:
        findings = collect(scan_root)
    except AttestCredentialsCheckError as exc:
        print(f"check_attest_registry_credentials: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(findings, list_all=args.list_all, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
