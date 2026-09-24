"""#1480 — every Hugging Face model an image downloads is pinned to a commit.

**Why this exists now.** Until #1480 the reranker image did not download a model
so much as *build* one: its download stages ran optimum's ONNX exporter over
``BAAI/bge-reranker-v2-m3`` and ``cross-encoder/ms-marco-MiniLM-L-12-v2``. That
exporter capped ``transformers`` below 4.58 and held the lock on a line with
three HIGH CVEs, so #1480 replaced the export with a download of graphs that are
already ONNX — for bge from ``onnx-community/bge-reranker-v2-m3-ONNX``, which is
not the model's author. What made that acceptable is a measurement taken on
2026-09-24 (byte-identical ``tokenizer.json``, identical graph inputs, max
|Δscore| 4.7e-6 over 3 queries x 7 documents, identical rankings) — and a
measurement of a *mutable* repository is only worth anything for the commit it
was taken on. A Hugging Face branch like ``main`` can be force-pushed to a
different graph; a different graph is a different ranking, and nothing fails.

So the pin is the load-bearing half of the change, and this file is what keeps
it load-bearing: every Hugging Face fetch in a Dockerfile of this checkout must
name a 40-hex commit as its revision. Renovate does not bump these (it has no
datasource for a Hugging Face revision), which is the intent: a model change is
a reviewed diff of a ``revision=`` literal with the parity measurement redone.

**No exceptions since #1724.** #1480 found four unpinned downloads in
``docker/embedding-service`` while writing this file and named them on an
allow-list rather than pin them in a change about another image. #1724 pinned
and sha256-verified all four, and the allow-list went with them: every Hugging
Face fetch in the tree is now pinned and verified, and a new unpinned one is red
with its full name — there is no mechanism left to excuse it. The non-vacuity
test pins that down from the other side: it requires every fetch pinned AND
requires the sweep to reach both model images with at least as many pinned
download stages as each has today (four embedding, two reranker).

**Found structurally, not from a list.** Every ``Dockerfile*`` in the checkout is
read, comment lines removed first — a ``#`` line in a Dockerfile is never an
instruction, and the reranker's own Dockerfile names ``snapshot_download`` in
prose (#1456: a comment must neither satisfy nor falsify a gate). The spellings
recognised, each with a self-test below that runs the SAME scanner:

* the Python API — ``snapshot_download(``, ``hf_hub_download(``,
  ``hf_hub_url(``, ``from_pretrained(``, ``SentenceTransformer(``,
  ``CrossEncoder(`` — qualified or bare, and under an ``import ... as`` alias;
  the pin is the ``revision=`` keyword with either quote and any spacing,
  including across a ``\\``-continued line;
* the CLI — ``huggingface-cli download`` / ``hf download`` with ``--revision``;
* a direct URL — ``huggingface.co/<repo>/resolve/<rev>/...`` (also ``hf.co``),
  where the ``<rev>`` path segment is the pin.

**A pin is not an integrity check, so a pinned fetch must also verify.** The
revision tells the server what to send; huggingface_hub checks nothing that
comes back against it. Every PINNED fetch must therefore be followed by a
``sha256sum -c`` (``--check``, flags in any order) in the SAME logical RUN
instruction — continuation lines and heredoc bodies included, the next
instruction not — so no unverified byte is committed to a layer. The check
must come AFTER the fetch and its failure must be able to fail the RUN: one
before the fetch, or one neutralised by ``|| true``, a following ``;``, a pipe,
``$( )``/backticks, ``!`` or ``&``, does not count (the shell model and the
dash measurements behind it are in ``_fetch_is_verified``, which also names
what it does not parse). A ``sha256sum`` that only computes (no check flag),
one with ``--ignore-missing``, one in a comment, or a check done some other way
(``hashlib`` in Python) does not count either; the last is a stated gap, not a
permission.

``from_pretrained('/model')`` and friends with a literal local path are not
fetches and are skipped; a non-literal first argument is NOT skipped, because
this file cannot tell a path from a hub id it cannot see.

**Residual, stated rather than implied.** A download written in a script that
the Dockerfile ``COPY``s and runs (``src/inference-service`` exports DINOv2 via
``torch.hub.load`` from such a script — not Hugging Face, and not in this
file's corpus), ``transformers.pipeline(model=...)``, or a fetch spelled through
``getattr`` is not seen. The non-vacuity assertion below guarantees the scanner
reaches the tree; it cannot guarantee a spelling nobody has written yet.

Traces to #1480 and #1724 (no TC-ID: image build configuration is not a user-facing case).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SKIPPED_DIRS = frozenset({".git", ".venv", "node_modules", ".mypy_cache", ".ruff_cache"})

#: Python callables that fetch from the Hub and accept ``revision=``.
_FETCH_FUNCTIONS = (
    "snapshot_download",
    "hf_hub_download",
    "hf_hub_url",
    "from_pretrained",
    "SentenceTransformer",
    "CrossEncoder",
)

#: The subset that can be re-bound with ``from huggingface_hub import x as y``.
#: ``from_pretrained`` is a method and cannot.
_ALIASABLE = ("snapshot_download", "hf_hub_download", "hf_hub_url", "SentenceTransformer", "CrossEncoder")

#: ``revision='<value>'`` / ``revision = "<value>"`` / ``revision=\\"<value>\\"``.
#: The optional backslash is the shell-escaped quote a ``RUN python -c "..."``
#: body needs for a double-quoted Python literal; without it that spelling would
#: read as unpinned.
_REVISION_KEYWORD = re.compile(r"\brevision\s*=\s*\\?(?P<q>['\"])(?P<rev>[^'\"\\]*)\\?(?P=q)")

#: The keyword arguments that name the repository in the Python API.
_REPO_KEYWORD = re.compile(
    r"\b(?:repo_id|pretrained_model_name_or_path|model_name_or_path)\s*=\s*\\?(?P<q>['\"])(?P<repo>[^'\"\\]*)\\?(?P=q)"
)

#: The first positional argument, when it is a string literal.
_FIRST_LITERAL = re.compile(r"^\s*\\?(?P<q>['\"])(?P<value>[^'\"\\]*)\\?(?P=q)\s*(?:,|$)")

#: ``huggingface-cli download <repo> ...`` / ``hf download <repo> ...`` up to the
#: end of the shell command.
_CLI_DOWNLOAD = re.compile(r"(?<![\w-])(?:huggingface-cli|hf)\s+download\s+(?P<args>[^;&|\n]*)")
_CLI_REVISION = re.compile(r"--revision(?:\s+|=)(?P<q>['\"]?)(?P<rev>[^\s'\"]+)(?P=q)")

#: ``https://huggingface.co/<owner>/<name>/resolve/<rev>/<file>``.
_RESOLVE_URL = re.compile(
    r"\b(?:huggingface\.co|hf\.co)/(?P<repo>[\w.-]+/[\w.-]+)/(?:resolve|raw|blob)/(?P<rev>[^/\s'\"]+)/"
)

_COMMIT_SHA = re.compile(r"[0-9a-f]{40}")

#: One ``sha256sum`` command: its arguments up to the next shell separator.
_SHA256SUM = re.compile(r"(?<![\w-])sha256sum(?P<args>(?:\s+[^\s;&|]+)*)")

#: A short-flag cluster containing ``c`` (``-c``, ``-bc``, ``-cw``).
_SHORT_CHECK = re.compile(r"-[a-zA-Z]*c[a-zA-Z]*")


def _long_option_matches(token: str, option: str) -> bool:
    """Whether GNU getopt_long would read *token* as *option*.

    getopt_long accepts any unambiguous PREFIX of a long option, and sha256sum
    (GNU coreutils 9.7, the one in the build base) has exactly one long option
    beginning ``--c`` and one beginning ``--i`` — so ``--c`` is ``--check`` and
    ``--i`` is ``--ignore-missing``. Measured 2026-09-24 in the image: with one
    listed file present and one missing, ``-c --i``, ``--ig -c``,
    ``-c --ignore`` and ``--c --ignore-m`` all exit 0.
    """
    return len(token) >= 3 and option.startswith(token)


def _verifies_digests(instruction: str) -> bool:
    """Whether *instruction* runs a ``sha256sum`` that CHECKS and misses nothing.

    ``sha256sum -c`` / ``--check``, flags in any order and combined short
    flags (``-c --strict``, ``--strict -c``, ``-bc``). Not accepted:

    * ``sha256sum FILE > SUMS`` without a check flag — it COMPUTES a digest
      and verifies nothing;
    * any check carrying ``--ignore-missing`` or one of its prefixes, in ANY
      argument position — GNU permutes arguments, so ``-c SUMS
      --ignore-missing`` means the same as ``--ignore-missing -c SUMS``. With it,
      a file that is listed but was never downloaded passes silently, which
      is the one failure a digest list exists to catch. It has no short form.

    ``--`` ends option parsing; a token after it is a file operand.
    """
    for command in _SHA256SUM.finditer(instruction):
        checks = False
        ignores_missing = False
        for token in command.group("args").split():
            if token == "--":
                break
            if _SHORT_CHECK.fullmatch(token) or _long_option_matches(token, "--check"):
                checks = True
            elif _long_option_matches(token.split("=", 1)[0], "--ignore-missing"):
                ignores_missing = True
        if checks and not ignores_missing:
            return True
    return False


#: A heredoc opener in a Dockerfile instruction: ``<<EOF``, ``<<-EOF``, ``<<'EOF'``.
_HEREDOC = re.compile(r"<<-?\s*(?P<q>['\"]?)(?P<tag>\w+)(?P=q)")

#: The Dockerfile ``FROM <image> [AS <stage>]`` line, for naming the build stage
#: a fetch runs in.
_FROM_STAGE = re.compile(r"^\s*FROM\s+\S+(?:\s+AS\s+(?P<stage>\S+))?", re.IGNORECASE)

#: ``RUN`` plus its BuildKit flags (``--mount=…``, ``--network=…``).
_RUN_PREFIX = re.compile(r"^\s*RUN\b\s*(?:--\S+\s+)*", re.IGNORECASE)

#: Shell control operators that end a simple command, longest first so ``&&``
#: is not read as two ``&``.
_OPERATORS = ("&&", "||", ";;", ";", "|", "&", "\n")


@dataclass(frozen=True)
class _Command:
    """One simple command of a RUN script and the operators around it."""

    text: str
    words: tuple[str, ...]
    before: str
    after: str


def _shell_commands(script: str) -> list[_Command]:
    """Split *script* into simple commands at TOP-LEVEL control operators.

    Quotes, ``$( … )`` and backticks are tracked so that an operator inside
    them — the ``;`` in ``python -c "import x; x.f()"``, a ``|`` inside a
    command substitution — does not split. Consequently a ``sha256sum`` inside
    ``$( )`` or backticks is part of another command's word and can never be
    read as a top-level check.
    """
    commands: list[_Command] = []
    current: list[str] = []
    before = ""
    quote: str | None = None
    depth = 0
    backtick = False
    index = 0

    def flush(operator: str) -> None:
        nonlocal before, current
        text = "".join(current).strip()
        current = []
        if text:
            commands.append(_Command(text=text, words=tuple(text.split()), before=before, after=operator))
            before = operator
        elif before in ("", "\n"):
            # An empty command between two operators (a blank heredoc line):
            # keep the stronger operator as the one that joins the neighbours.
            before = operator
        if commands and not text and operator not in ("", "\n"):
            last = commands[-1]
            if last.after == "\n":
                commands[-1] = _Command(last.text, last.words, last.before, operator)

    while index < len(script):
        char = script[index]
        if char == "\\" and quote != "'":
            current.append(script[index : index + 2])
            index += 2
            continue
        if quote is not None:
            if char == quote:
                quote = None
            elif char == "$" and script.startswith("$(", index) and quote == '"':
                depth += 1
            elif char == ")" and depth and quote == '"':
                depth -= 1
            current.append(char)
            index += 1
            continue
        if char in "'\"":
            quote = char
        elif script.startswith("$(", index):
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char == "`":
            backtick = not backtick
        elif not depth and not backtick:
            operator = next((op for op in _OPERATORS if script.startswith(op, index)), None)
            if operator is not None:
                flush(operator)
                index += len(operator)
                continue
        current.append(char)
        index += 1
    flush("")
    return commands


def _run_script(lines: list[str]) -> str:
    """The shell script a RUN instruction executes, from its source *lines*.

    Continuation lines are joined; blank lines (where a comment was) inside a
    continuation vanish, as BuildKit drops them. A heredoc body is the script
    itself, one command per line. ``RUN <cmd> <<EOF`` feeds the body to
    ``<cmd>`` rather than to the shell, so there the body is folded into one
    quoted word of that command. Any other instruction yields no script.
    """
    if not lines or not _RUN_PREFIX.match(lines[0]):
        return ""
    first = lines[0]
    heredoc = _HEREDOC.search(first)
    if heredoc is None:
        joined = "\n".join(line for line in lines if line.strip())
        return _RUN_PREFIX.sub("", re.sub(r"\\\n", " ", joined), count=1)
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == heredoc.group("tag"):
            break
        body.append(line)
    head = _RUN_PREFIX.sub("", first[: heredoc.start()], count=1).strip()
    if not head:
        return "\n".join(body)
    blob = " ".join(body).replace("'", '"')
    return f"{head} '{blob}'"


def _sets_errexit(command: _Command, current: bool) -> bool:
    """``set -e`` / ``set -o errexit`` switch errexit on, ``+e`` / ``+o`` off."""
    if not command.words or command.words[0] != "set":
        return current
    words = command.words[1:]
    for position, word in enumerate(words):
        if word in ("-o", "+o") and position + 1 < len(words) and words[position + 1] == "errexit":
            current = word == "-o"
        elif re.fullmatch(r"[-+][a-zA-Z]*e[a-zA-Z]*", word):
            current = word.startswith("-")
    return current


def _fetch_is_verified(commands: list[_Command], fetch: int) -> bool:
    """Whether a check AFTER ``commands[fetch]`` can fail the RUN, measured on dash.

    ``/bin/sh`` in python:3.14-slim is dash, which RUN uses without ``-e``.
    Measured 2026-09-24 in the image, with a checksum list that does not match:

    * the RUN fails for ``C && x``, ``x && C && y``, ``set -e; C; y``,
      ``set +e; C && y``, ``x=$(C)`` and ``(C)``;
    * it SUCCEEDS for ``C || true``, ``C || :``, ``C || exit 0``, ``C; y`` (any
      ``y``, not only ``true``), ``C`` followed by another heredoc line,
      ``C | tee log``, ``echo $(C)``, ``echo `C```, ``! C``, ``C &`` and
      ``x || C`` (C never runs).

    So a check counts only if it is a top-level ``sha256sum`` command after the
    fetch, the operators from the fetch to it are ``&&``, ``;`` or newline (a
    failed fetch then still reaches the check, which fails on missing files),
    it is not followed by ``|``, ``||`` or ``&``, and every operator after it is
    ``&&`` — or ``;``/newline while errexit is on (``set -e`` / ``-o errexit``
    earlier, not undone by ``set +e``). ``set +e`` on its own does NOT mask a
    check whose tail is ``&&`` (measured), so it is only tracked as switching
    errexit off.

    NOT covered, stated rather than implied: ``x=$(C)`` and ``(C)`` do propagate
    the failure but are not recognised (red — the conservative direction);
    ``set -o pipefail`` is not modelled, so ``C | tee`` is refused even with it;
    ``if``/``case``/functions, ``SHELL`` overrides and the JSON exec form of RUN
    are not parsed; ``trap``, ``exec`` redirection and aliases are ignored.
    """
    errexit_before: list[bool] = []
    state = False
    for command in commands:
        errexit_before.append(state)
        state = _sets_errexit(command, state)

    for check in range(fetch + 1, len(commands)):
        command = commands[check]
        if not command.words or command.words[0] != "sha256sum" or not _verifies_digests(command.text):
            continue
        reaches = all(commands[k].after in ("&&", ";", "\n") for k in range(fetch, check))
        if not reaches or command.after in ("|", "||", "&"):
            continue
        propagates = True
        for k in range(check, len(commands) - 1):
            operator = commands[k].after
            if operator == "&&":
                continue
            if operator in (";", "\n") and errexit_before[k + 1]:
                continue
            propagates = False
            break
        if propagates and commands[-1].after in ("", "\n", ";"):
            return True
    return False


def _command_fetches(command: _Command) -> bool:
    """Whether *command* contains any Hugging Face fetch spelling."""
    return bool(
        _call_pattern(command.text).search(command.text)
        or _CLI_DOWNLOAD.search(command.text)
        or _RESOLVE_URL.search(command.text)
    )


#: The minimum number of build stages with a pinned fetch per Dockerfile — what
#: each model image has today (#1480: the reranker's two, #1724: the embedding
#: service's four). Counted per file rather than listed per repository, so the
#: sweep must keep REACHING both images; a model added to either raises the
#: count without touching this, a stage lost to a scanner regression lowers it.
_MIN_PINNED_STAGES: dict[str, int] = {
    "docker/embedding-service/Dockerfile": 4,
    "docker/reranker-service/Dockerfile": 2,
}


@dataclass(frozen=True)
class FetchSite:
    """One Hugging Face download found in a Dockerfile."""

    path: str
    line: int
    spelling: str
    repo: str | None
    revision: str | None
    #: A ``sha256sum -c`` in the same RUN instruction as the fetch.
    digest_checked: bool = False
    #: The ``AS <stage>`` name of the build stage the fetch runs in ("" if unnamed).
    stage: str = ""

    @property
    def pinned(self) -> bool:
        return self.revision is not None and _COMMIT_SHA.fullmatch(self.revision) is not None

    @property
    def label(self) -> str:
        return f"{self.path}:{self.line}:{self.stage or '?'}:{self.spelling}:{self.repo or '?'}"


# --------------------------------------------------------------------------
# the scanner
# --------------------------------------------------------------------------


def _strip_dockerfile_comments(text: str) -> str:
    """Blank every Dockerfile comment line, keeping line numbers in place.

    BuildKit drops a line whose first non-blank character is ``#`` even inside a
    ``\\``-continued ``RUN``, so such a line is prose, never an instruction.
    """
    return "\n".join("" if line.lstrip().startswith("#") else line for line in text.splitlines())


def _fold_continuations(text: str) -> str:
    """Turn ``\\``-newline into space-newline: ``\\s`` then spans it, lines stay put."""
    return re.sub(r"\\\n", " \n", text)


def _instruction_spans(text: str) -> list[tuple[int, int]]:
    """``(first_line, last_line)`` of every logical Dockerfile instruction, 1-based.

    *text* has its comment lines already blanked. An instruction runs on while
    its line ends in ``\\`` — skipping blank lines, which is where a comment
    inside a continued RUN used to be — and through every heredoc it opens. This
    is what "the same RUN" means for the digest check: a ``sha256sum -c`` in the
    NEXT instruction runs in a different layer, after the fetched bytes have
    already been committed to one.
    """
    lines = text.splitlines()
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        start = index
        pending: list[str] = []
        while True:
            line = lines[index]
            pending.extend(match.group("tag") for match in _HEREDOC.finditer(line))
            if line.rstrip().endswith("\\"):
                index += 1
                while index < len(lines) and not lines[index].strip():
                    index += 1
                if index >= len(lines):
                    break
                continue
            for tag in pending:
                index += 1
                while index < len(lines) and lines[index].strip() != tag:
                    index += 1
            break
        end = min(index, len(lines) - 1)
        spans.append((start + 1, end + 1))
        index = end + 1
    return spans


def _call_arguments(text: str, open_paren: int) -> str:
    """The text between the ``(`` at *open_paren* and its matching ``)``.

    Parentheses inside a quoted string do not count. An unbalanced call yields
    the empty string rather than the rest of the file, so a ``revision=`` of a
    LATER call can never be attributed to it: it reads as unpinned, which is the
    direction that goes red.
    """
    depth = 0
    quote: str | None = None
    for index in range(open_paren, len(text)):
        char = text[index]
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1 : index]
    return ""


def _call_pattern(text: str) -> re.Pattern[str]:
    """Match a call to any fetch function, including its ``import ... as`` aliases."""
    names = list(_FETCH_FUNCTIONS)
    alias_import = re.compile(r"\b(?:" + "|".join(_ALIASABLE) + r")\s+as\s+(?P<alias>\w+)")
    names.extend(match.group("alias") for match in alias_import.finditer(text))
    return re.compile(r"(?<![\w-])(?P<fn>" + "|".join(re.escape(name) for name in names) + r")\s*\(")


def _is_local_path(value: str) -> bool:
    return value.startswith(("/", "./", "../", "~"))


def fetch_sites(text: str, *, path: str) -> list[FetchSite]:
    """Every Hugging Face fetch in the Dockerfile *text*, comments excluded."""
    blanked = _strip_dockerfile_comments(text)
    code = _fold_continuations(blanked)
    spans = _instruction_spans(blanked)
    blanked_lines = blanked.splitlines()
    # A stage opens only on the FIRST line of an instruction. A continued line
    # or a heredoc body line that happens to begin with `from` (a Python
    # `from huggingface_hub import …`) is inside a RUN and opens nothing.
    stages = [
        (first, match.group("stage") or "")
        for first, _last in spans
        if (match := _FROM_STAGE.match(blanked_lines[first - 1]))
    ]
    sites: list[FetchSite] = []

    def stage_of(line: int) -> str:
        current = ""
        for number, name in stages:
            if number > line:
                break
            current = name
        return current

    def line_of(offset: int) -> int:
        return code.count("\n", 0, offset) + 1

    def digest_checked(line: int) -> bool:
        """Every fetching command of the fetch's RUN is followed by a check that can fail it."""
        for first, last in spans:
            if first <= line <= last:
                commands = _shell_commands(_run_script(blanked_lines[first - 1 : last]))
                fetching = [index for index, command in enumerate(commands) if _command_fetches(command)]
                return bool(fetching) and all(_fetch_is_verified(commands, index) for index in fetching)
        return False

    for match in _call_pattern(code).finditer(code):
        arguments = _call_arguments(code, match.end() - 1)
        first = _FIRST_LITERAL.match(arguments)
        keyword_repo = _REPO_KEYWORD.search(arguments)
        repo = first.group("value") if first else keyword_repo.group("repo") if keyword_repo else None
        if repo is not None and _is_local_path(repo):
            continue
        revision = _REVISION_KEYWORD.search(arguments)
        sites.append(
            FetchSite(
                path=path,
                line=line_of(match.start()),
                spelling=match.group("fn"),
                repo=repo,
                revision=revision.group("rev") if revision else None,
                digest_checked=digest_checked(line_of(match.start())),
                stage=stage_of(line_of(match.start())),
            )
        )

    for match in _CLI_DOWNLOAD.finditer(code):
        arguments = match.group("args")
        positional = next((token for token in arguments.split() if not token.startswith("-")), None)
        revision = _CLI_REVISION.search(arguments)
        sites.append(
            FetchSite(
                path=path,
                line=line_of(match.start()),
                spelling="cli download",
                repo=positional.strip("'\"") if positional else None,
                revision=revision.group("rev") if revision else None,
                digest_checked=digest_checked(line_of(match.start())),
                stage=stage_of(line_of(match.start())),
            )
        )

    for match in _RESOLVE_URL.finditer(code):
        sites.append(
            FetchSite(
                path=path,
                line=line_of(match.start()),
                spelling="resolve url",
                repo=match.group("repo"),
                revision=match.group("rev"),
                digest_checked=digest_checked(line_of(match.start())),
                stage=stage_of(line_of(match.start())),
            )
        )

    return sorted(sites, key=lambda site: site.line)


def _dockerfiles() -> list[Path]:
    found = [
        path
        for path in sorted(_REPO_ROOT.glob("**/Dockerfile*"))
        if path.is_file() and not _SKIPPED_DIRS.intersection(path.relative_to(_REPO_ROOT).parts)
    ]
    assert found, f"no Dockerfile under {_REPO_ROOT} — the sweep would be vacuously green"
    return found


def _tree_sites() -> list[FetchSite]:
    sites: list[FetchSite] = []
    for dockerfile in _dockerfiles():
        relative = str(dockerfile.relative_to(_REPO_ROOT))
        sites.extend(fetch_sites(dockerfile.read_text(encoding="utf-8"), path=relative))
    return sites


_SITES = _tree_sites()


_PINNED_SITES = [site for site in _SITES if site.pinned]


# --------------------------------------------------------------------------
# the property, over the checkout
# --------------------------------------------------------------------------


class TestHuggingFaceFetchesArePinned:
    """Every model a Dockerfile pulls from the Hub names the commit it pulls."""

    def test_the_sweep_finds_fetches_at_all(self) -> None:
        """Without this, every parametrized case below is vacuously absent.

        Both parametrized tests collect ZERO cases on a scanner that stopped
        reaching the tree — and zero collected cases is not a skip, so the
        guard lane's ``--max-skipped 0`` would not notice. So this asserts, on
        the tree: fetches were found, EVERY one is pinned (no allow-list may
        silently return — #1724 removed the last one), and each model image
        still yields at least as many pinned download stages as it has today.
        A scanner that lost the ``revision=`` reader fails the second
        assertion, one that lost the call reader or the Dockerfile walk fails
        the first or the third.
        """
        assert _SITES, "no Hugging Face fetch found in any Dockerfile — the scanner stopped reaching the tree"
        unpinned = [site.label for site in _SITES if not site.pinned]
        assert not unpinned, (
            f"unpinned Hugging Face fetches: {unpinned}. Since #1724 every fetch in the tree is "
            "pinned and verified; there is no allow-list, pin it."
        )
        reached = {
            path: len({site.stage for site in _PINNED_SITES if site.path == path}) for path in _MIN_PINNED_STAGES
        }
        short = {path: count for path, count in reached.items() if count < _MIN_PINNED_STAGES[path]}
        assert not short, (
            f"pinned download stages per Dockerfile {reached}, expected at least {_MIN_PINNED_STAGES}: "
            "the sweep stopped reaching a model image, or a download stage lost its pin"
        )

    @pytest.mark.parametrize("site", _SITES, ids=lambda site: site.label)
    def test_fetch_names_a_commit(self, site: FetchSite) -> None:
        """Every fetch names a 40-hex commit — no exceptions since #1724."""
        assert site.pinned, (
            f"{site.label}: a Hugging Face fetch without a commit pin (revision={site.revision!r}). "
            "Name the 40-hex commit the model was measured on, e.g. "
            "revision='6f5ff65298512715a1e669753bc754d2bc8f367b' — a branch or tag can be moved "
            "under the image and change its output without failing anything (#1480, #1724)."
        )

    @pytest.mark.parametrize("site", _PINNED_SITES, ids=lambda site: site.label)
    def test_pinned_fetch_verifies_the_bytes_in_the_same_run(self, site: FetchSite) -> None:
        """A commit pin tells the server what to send; it checks nothing that arrives.

        huggingface_hub does not verify downloaded bytes against the revision,
        so a tampered mirror or proxy could serve other files for the right
        commit. The ``sha256sum -c`` must sit in the SAME RUN, so no unverified
        byte is ever committed to a layer the runtime stage copies from.
        """
        assert site.digest_checked, (
            f"{site.label}: pinned, but no `sha256sum -c` in the same RUN. Verify every kept file "
            "against the sha256 of the pinned revision (the Hub's `lfs.sha256` / git blob id, "
            "`/api/models/<repo>/revision/<sha>?blobs=true`) before the layer ends (#1480)."
        )


# --------------------------------------------------------------------------
# the scanner, against every spelling it claims to read
# --------------------------------------------------------------------------

_SHA = "6f5ff65298512715a1e669753bc754d2bc8f367b"

_SPELLINGS: list[tuple[str, str, bool]] = [
    (
        "qualified, single quotes, continued",
        'RUN python -c "\\\nimport huggingface_hub; \\\nhuggingface_hub.snapshot_download(\\\n'
        f"repo_id='org/model', \\\nrevision='{_SHA}', \\\nlocal_dir='/dl')\"\n",
        True,
    ),
    (
        "double quotes, spaced keyword",
        "RUN python -c 'import huggingface_hub; "
        f'huggingface_hub.snapshot_download("org/model", revision = "{_SHA}")\'\n',
        True,
    ),
    (
        "shell-escaped double quotes",
        'RUN python -c "import huggingface_hub; '
        f'huggingface_hub.snapshot_download(\\"org/model\\", revision=\\"{_SHA}\\")"\n',
        True,
    ),
    (
        "positional repo, no revision",
        "RUN python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', local_dir='/m')\"\n",
        False,
    ),
    (
        "branch name is not a pin",
        'RUN python -c "import huggingface_hub; '
        "huggingface_hub.hf_hub_download('org/model', 'x', revision='main')\"\n",
        False,
    ),
    (
        "revision from a variable is not a pin",
        "RUN python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision=REV)\"\n",
        False,
    ),
    (
        "revision of a DIFFERENT call does not pin this one",
        "RUN python -c \"import huggingface_hub as h; h.snapshot_download('org/model'); "
        f"h.hf_hub_download('o/n', 'f', revision='{_SHA}')\"\n",
        False,
    ),
    (
        "import alias",
        'RUN python -c "import huggingface_hub" && python - <<EOF\n'
        "from huggingface_hub import snapshot_download as grab\ngrab('org/model')\nEOF\n",
        False,
    ),
    (
        "from_pretrained with a hub id",
        "RUN python -c \"import transformers; transformers.AutoTokenizer.from_pretrained('org/model')\"\n",
        False,
    ),
    (
        "cli download without --revision",
        "RUN huggingface-cli download org/model --local-dir /m\n",
        False,
    ),
    (
        "hf cli download with --revision",
        f"RUN hf download org/model --revision {_SHA} --local-dir /m\n",
        True,
    ),
    (
        "resolve url on main",
        "RUN curl -fsSL -o /m/model.onnx https://huggingface.co/org/model/resolve/main/onnx/model.onnx\n",
        False,
    ),
    (
        "resolve url on a commit",
        f"RUN curl -fsSL -o /m/model.onnx https://hf.co/org/model/resolve/{_SHA}/onnx/model.onnx\n",
        True,
    ),
]


@pytest.mark.parametrize(("snippet", "pinned"), [(s, p) for _, s, p in _SPELLINGS], ids=[n for n, _, _ in _SPELLINGS])
def test_scanner_reads_the_spelling(snippet: str, pinned: bool) -> None:
    sites = fetch_sites(snippet, path="Dockerfile")
    assert sites, "the scanner found no fetch in a snippet that contains one"
    assert all(site.repo in {"org/model", "o/n"} for site in sites)
    target = next(site for site in sites if site.repo == "org/model")
    assert target.pinned is pinned


_PINNED_FETCH = (
    'RUN python -c "import huggingface_hub; '
    f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}', local_dir='/m')\" && \\\n"
)

_DIGEST_SPELLINGS: list[tuple[str, str, bool]] = [
    (
        "sha256sum -c --strict in the same RUN",
        _PINNED_FETCH + "    sha256sum -c --strict /tmp/model.sha256\n",
        True,
    ),
    ("--strict before -c", _PINNED_FETCH + "    sha256sum --strict -c /tmp/sums\n", True),
    ("long --check", _PINNED_FETCH + "    sha256sum --check /tmp/sums\n", True),
    ("abbreviated --c", _PINNED_FETCH + "    sha256sum --c /tmp/sums\n", True),
    (
        "after --, --ignore-missing is a file operand, not the option",
        _PINNED_FETCH + "    sha256sum -c -- --ignore-missing\n",
        True,
    ),
    ("--ignore-missing after -c", _PINNED_FETCH + "    sha256sum -c --ignore-missing /tmp/sums\n", False),
    ("--ignore-missing before -c", _PINNED_FETCH + "    sha256sum --ignore-missing -c /tmp/sums\n", False),
    ("--ignore-missing after the operand", _PINNED_FETCH + "    sha256sum -c /tmp/sums --ignore-missing\n", False),
    ("abbreviated --ignore", _PINNED_FETCH + "    sha256sum -c --ignore /tmp/sums\n", False),
    ("abbreviated --i", _PINNED_FETCH + "    sha256sum -c --strict --i /tmp/sums\n", False),
    (
        "--ignore-missing next to --check",
        _PINNED_FETCH + "    sha256sum --check --strict --ignore-m /tmp/sums\n",
        False,
    ),
    (
        "blank line (a removed comment) inside the continuation",
        _PINNED_FETCH + "\n    sha256sum -c /tmp/sums\n",
        True,
    ),
    ("no check at all", _PINNED_FETCH + "    rm -rf /dl\n", False),
    ("sha256sum that only COMPUTES", _PINNED_FETCH + "    sha256sum /m/model.onnx > /tmp/sums\n", False),
    (
        "check in the NEXT instruction",
        _PINNED_FETCH + "    rm -rf /dl\nRUN sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "check only in a comment",
        _PINNED_FETCH + "    rm -rf /dl\n# sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "heredoc RUN",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        "sha256sum -c /tmp/sums\nEOF\n",
        True,
    ),
    (
        "check BEFORE the fetch in the same RUN",
        'RUN sha256sum -c /old.sums && python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n",
        False,
    ),
    ("check || true", _PINNED_FETCH + "    sha256sum -c /tmp/sums || true\n", False),
    ("check || :", _PINNED_FETCH + "    sha256sum -c /tmp/sums || :\n", False),
    ("check || exit 0", _PINNED_FETCH + "    sha256sum -c /tmp/sums || exit 0\n", False),
    ("check ; true", _PINNED_FETCH + "    sha256sum -c /tmp/sums; true\n", False),
    ("check ; any other command", _PINNED_FETCH + "    sha256sum -c /tmp/sums; rm -rf /dl\n", False),
    ("check && y || true", _PINNED_FETCH + "    sha256sum -c /tmp/sums && rm -rf /dl || true\n", False),
    ("check piped into tee", _PINNED_FETCH + "    sha256sum -c /tmp/sums | tee /tmp/log\n", False),
    ("check inside $( )", _PINNED_FETCH + "    echo $(sha256sum -c /tmp/sums)\n", False),
    ("check inside backticks", _PINNED_FETCH + "    echo `sha256sum -c /tmp/sums`\n", False),
    ("negated check", _PINNED_FETCH + "    ! sha256sum -c /tmp/sums\n", False),
    ("backgrounded check", _PINNED_FETCH + "    sha256sum -c /tmp/sums & wait\n", False),
    (
        "check behind || (runs only if the step before failed)",
        _PINNED_FETCH + "    true || sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "set -e, then ; after the check",
        'RUN set -e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"; "
        "sha256sum -c /tmp/sums; rm -rf /dl\n",
        True,
    ),
    (
        "set -e undone by set +e, then ; after the check",
        'RUN set -e; set +e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"; "
        "sha256sum -c /tmp/sums; rm -rf /dl\n",
        False,
    ),
    (
        "set +e does not mask an && tail (measured)",
        'RUN set +e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\" && "
        "sha256sum -c /tmp/sums && rm -rf /dl\n",
        True,
    ),
    (
        "heredoc RUN, a line after the check masks it",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        "sha256sum -c /tmp/sums\nrm -rf /dl\nEOF\n",
        False,
    ),
    (
        "heredoc RUN under set -e, a line after the check",
        "RUN <<EOF\nset -e\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        "sha256sum -c /tmp/sums\nrm -rf /dl\nEOF\n",
        True,
    ),
    (
        "heredoc RUN, check after its terminator",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        "EOF\nRUN sha256sum -c /tmp/sums\n",
        False,
    ),
]


@pytest.mark.parametrize(
    ("snippet", "checked"),
    [(s, c) for _, s, c in _DIGEST_SPELLINGS],
    ids=[n for n, _, _ in _DIGEST_SPELLINGS],
)
def test_scanner_scopes_the_digest_check_to_the_run(snippet: str, checked: bool) -> None:
    sites = fetch_sites(snippet, path="Dockerfile")
    assert len(sites) == 1 and sites[0].pinned, "the pinned fetch in the snippet was not found"
    assert sites[0].digest_checked is checked


@pytest.mark.parametrize(
    "snippet",
    [
        'FROM base AS dl-one\nRUN python -c "\\\nimport huggingface_hub; \\\n'
        "from huggingface_hub import snapshot_download as g; \\\ng('org/model')\"\n",
        "FROM base AS dl-one\nRUN python3 <<EOF\nimport huggingface_hub\n"
        "from huggingface_hub import snapshot_download as g\ng('org/model')\nEOF\n",
        "FROM base AS dl-one\nRUN <<EOF\npython - <<'PY'\n"
        "FROM = 1\nPY\npython -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model')\"\nEOF\n",
    ],
    ids=["continued python line starting with from", "heredoc body line starting with from", "FROM inside a heredoc"],
)
def test_only_an_instruction_line_opens_a_stage(snippet: str) -> None:
    """A ``from``/``FROM`` line inside a RUN (continuation or heredoc) is not a stage."""
    assert [site.stage for site in fetch_sites(snippet, path="Dockerfile")] == ["dl-one"]


def test_a_fetch_is_named_by_the_stage_it_runs_in() -> None:
    """A fetch's label reads the ``AS <stage>`` of the enclosing ``FROM``."""
    snippet = (
        "FROM python:3 AS base\n"
        "FROM base as dl-one\n"
        "RUN python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model')\"\n"
        "FROM base AS dl-two\n"
        "RUN python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model')\"\n"
    )
    assert [site.stage for site in fetch_sites(snippet, path="Dockerfile")] == ["dl-one", "dl-two"]


def test_a_comment_line_is_not_a_fetch() -> None:
    """The reranker Dockerfile names ``snapshot_download`` in prose (#1456)."""
    snippet = "# huggingface_hub.snapshot_download('org/model')\n    # hf download org/model\nFROM scratch\n"
    assert fetch_sites(snippet, path="Dockerfile") == []


def test_a_local_path_is_not_a_fetch() -> None:
    snippet = "RUN python -c \"import transformers; transformers.AutoTokenizer.from_pretrained('/model')\"\n"
    assert fetch_sites(snippet, path="Dockerfile") == []
