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

**A check is only as good as its list (#1735).** Until #1735 any such check
passed, which let two spellings verify nothing: ``sha256sum /model/* > /tmp/s
&& sha256sum -c /tmp/s`` (the expected values computed from the downloaded
bytes themselves), and a file ``mv``'d into ``/model`` with no line in the list
(``-c`` never looks at a file its list leaves out; ``--strict`` only rejects
malformed lines). Two rules close them, each with a self-test per spelling:

* **Rule A — the checklist is literals from this RUN** (``_checklist_paths``,
  ``_file_content``, ``_literal_output``). Every list the check reads — its
  file operands, or stdin via ``< F`` or a here-document — must be written
  BEFORE it in the same RUN, only by ``printf '%s\\n' 'L' ...``, a
  ``%``-free ``printf 'L\\n'``, ``echo 'L'`` (dash expands ``\\n``; ``echo -e``
  prints ``-e``) or ``cat > F <<'EOF'``, to ``>``/``>|``/``>>`` — the first
  write truncating, since a first ``>>`` appends to whatever an earlier layer
  left — and every line must be ``<64 hex> <space or *><path>``. Any other
  command before the check that names the list (full path, or its basename as
  a word: ``sha256sum ... > s``, ``cp``, ``python -c "open(...)"``), a redirect
  or an argument-writer (``tee``, ``cp``, ``python`` …) with a ``$``-computed
  target, or a ``cd`` before a relative list makes it unknown: red. So is
  ``$( )``/backticks in a ``printf``/``echo`` argument or an unquoted
  here-document.
* **Rule B — kept files and hash lines are one set** (``_pairing_problem``).
  What the stage keeps is what ``COPY --from=<stage>`` or ``RUN
  --mount=from=<stage>`` reads out of it. The paths placed there by ``mv``,
  ``cp``, ``curl -o``/``wget -O`` or a literal writer, and the paths of the
  hash lines of checks that verify the fetch, must be equal — each kept path
  with exactly one line, each line naming a kept path, the line's check after
  the path's last write. The kept directory must be created by ``mkdir``
  WITHOUT ``-p`` in that RUN (the build then fails if it already exists, so
  nothing the base image or an earlier layer put there rides along), and no
  other instruction of the stage may name it. A path is looked for in the raw
  text AND in every word after quote removal (``/mod""el`` is ``/model``), and
  any ``mv``/``cp``/``curl``/``tee``/``python`` … with a ``$``-computed word, or
  a redirect to a computed target, is red in the fetch's RUN: an ``ENV`` of an
  ancestor stage could point it at the kept directory.

Spellings these rules deliberately read as RED because they are not modelled
(the conservative direction): a piped list (``printf ... | sha256sum -c``),
the BSD ``--tag`` line, a ``printf`` format other than ``%s\\n``, ``%b``, a
checklist ``COPY``'d from the build context, a glob, ``-r``/``-a``/``-t`` or a
relative path in ``mv``/``cp``, a fetch landing straight in the kept directory
(``snapshot_download(local_dir='/model')``, ``hf download --local-dir
/model``), ``tar -C``, ``ln``, ``cd`` into it, a checklist stored inside it (it
cannot hash itself), a download stage no ``COPY --from`` names (or names by
index), and a ``COPY --from`` of ``/``. What they can NOT see: a write to the
list or the kept directory through a path the text never spells (a symlink
made in an earlier layer, a ``..`` walk from another directory, ``eval``), and
a stage derived ``FROM`` the download stage whose copy is read instead — that
last one is red only because the download stage itself then has no reader.

``from_pretrained('/model')`` and friends with a literal local path are not
fetches and are skipped; a non-literal first argument is NOT skipped, because
this file cannot tell a path from a hub id it cannot see.

**Residual, stated rather than implied.** A download written in a script that
the Dockerfile ``COPY``s and runs (``src/inference-service`` exports DINOv2 via
``torch.hub.load`` from such a script — not Hugging Face, and not in this
file's corpus), ``transformers.pipeline(model=...)``, or a fetch spelled through
``getattr`` is not seen. The non-vacuity assertion below guarantees the scanner
reaches the tree; it cannot guarantee a spelling nobody has written yet.

Traces to #1480, #1724 and #1735 (no TC-ID: image build configuration is not a user-facing case).
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter
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


#: A shell here-document opener inside a RUN script: ``<<TAG``, ``<<-TAG``, ``<<'TAG'``.
_SHELL_HEREDOC = re.compile(r"<<(?P<dash>-?)\s*(?P<q>['\"]?)(?P<tag>\w+)(?P=q)")


@dataclass(frozen=True)
class _Heredoc:
    """The body of a shell here-document, and whether the shell expands it."""

    body: str
    #: A quoted tag (``<<'EOF'``) turns expansion off: the body is literal.
    quoted: bool


@dataclass(frozen=True)
class _Command:
    """One simple command of a RUN script and the operators around it."""

    text: str
    words: tuple[str, ...]
    before: str
    after: str
    #: Bodies of the here-documents this command opened, in order.
    heredocs: tuple[_Heredoc, ...] = ()

    @property
    def full(self) -> str:
        """The command's text with its here-document bodies — everything it can act on."""
        return "\n".join([self.text, *(heredoc.body for heredoc in self.heredocs)])


def _shell_commands(script: str) -> list[_Command]:
    """Split *script* into simple commands at TOP-LEVEL control operators.

    Quotes, ``$( … )`` and backticks are tracked so that an operator inside
    them — the ``;`` in ``python -c "import x; x.f()"``, a ``|`` inside a
    command substitution — does not split. Consequently a ``sha256sum`` inside
    ``$( )`` or backticks is part of another command's word and can never be
    read as a top-level check. The ``|`` of ``>|`` and the ``&`` of ``2>&1``
    belong to a redirection and do not split either.

    A here-document a command opens (``cat > f <<EOF``) is read as that
    command's input: its body lines are attached to the command (#1735) instead
    of being parsed as commands of their own, which is what the shell does.
    """
    commands: list[_Command] = []
    bodies: dict[int, list[_Heredoc]] = {}
    pending: list[tuple[str, bool, bool, int]] = []
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

    def read_bodies() -> None:
        """Consume the here-document bodies that follow the line just ended."""
        nonlocal index, pending
        for tag, strip_tabs, quoted, owner in pending:
            body: list[str] = []
            while index < len(script):
                end = script.find("\n", index)
                end = len(script) if end == -1 else end
                line = script[index:end]
                index = end + 1
                line = line.lstrip("\t") if strip_tabs else line
                if line == tag:
                    break
                body.append(line)
            bodies.setdefault(owner, []).append(_Heredoc(body="\n".join(body), quoted=quoted))
        pending = []

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
            opener = _SHELL_HEREDOC.match(script, index)
            if opener is not None:
                owner = len(commands)
                pending.append((opener.group("tag"), bool(opener.group("dash")), bool(opener.group("q")), owner))
                current.append(opener.group(0))
                index = opener.end()
                continue
            operator = next((op for op in _OPERATORS if script.startswith(op, index)), None)
            if operator in ("|", "&") and current and current[-1].endswith((">", "<")):
                operator = None  # `>|`, `>&`, `<&`: part of a redirection
            if operator is not None:
                flush(operator)
                index += len(operator)
                if operator == "\n" and pending:
                    read_bodies()
                continue
        current.append(char)
        index += 1
    flush("")
    return [
        _Command(command.text, command.words, command.before, command.after, tuple(bodies.get(position, ())))
        for position, command in enumerate(commands)
    ]


def _run_script(lines: list[str]) -> str:
    """The shell script a RUN instruction executes, from its source *lines*.

    Continuation lines are joined; blank lines (where a comment was) inside a
    continuation vanish, as BuildKit drops them. A heredoc body is the script
    itself, one command per line. ``RUN <cmd> <<EOF`` hands the shell
    ``<cmd> <<EOF``, the body and the terminator — a here-document of
    ``<cmd>``, which ``_shell_commands`` attaches to it. Any other instruction
    yields no script.
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
    return "\n".join([_RUN_PREFIX.sub("", first, count=1).strip(), *body, heredoc.group("tag")])


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

    return bool(_verifying_checks(commands, fetch, errexit_before))


def _verifying_checks(
    commands: list[_Command], fetch: int, errexit_before: list[bool] | None = None
) -> dict[int, list[str]]:
    """Every check after ``commands[fetch]`` that verifies it: index -> hash-line paths.

    A check verifies when the shell model of ``_fetch_is_verified`` says its
    failure fails the RUN AND every checklist it reads was written in this RUN
    from 64-hex literals (``_checklist_paths``, #1735).
    """
    if errexit_before is None:
        errexit_before = []
        state = False
        for command in commands:
            errexit_before.append(state)
            state = _sets_errexit(command, state)
    found: dict[int, list[str]] = {}
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
        if not propagates or commands[-1].after not in ("", "\n", ";"):
            continue
        paths = _checklist_paths(commands, check)
        if paths is not None:
            found[check] = paths
    return found


# --------------------------------------------------------------------------
# #1735: where the checklist comes from, and what it covers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Word:
    """One shell word after quote removal."""

    value: str
    #: No parameter expansion or command substitution anywhere in it.
    literal: bool
    #: An unquoted ``*``, ``?`` or ``[`` — a pathname pattern.
    glob: bool


@dataclass(frozen=True)
class _Parsed:
    """A simple command as words and redirections."""

    args: tuple[_Word, ...]
    #: ``(fd, operator, target)`` — ``("", ">", /tmp/s)``, ``("2", ">&", 1)``, ``("", "<<", EOF)``.
    redirects: tuple[tuple[str, str, _Word], ...]

    @property
    def name(self) -> str:
        return self.args[0].value if self.args else ""

    def writes(self) -> list[_Word]:
        """The files its standard output is redirected into."""
        return [target for fd, op, target in self.redirects if op in (">", ">>", ">|") and fd in ("", "1")]


_REDIRECT_OP = re.compile(r"<<-?|>>|>\||>&|<&|<>|>|<")


def _parse(text: str) -> _Parsed:
    """Split a simple command into words and redirections, the way dash does.

    Single quotes are literal; in double quotes a backslash escapes only
    ``$ ` " \\`` and newline; unquoted, a backslash escapes the next character.
    ``$`` or a backtick anywhere outside single quotes makes the word
    non-literal — its value is then what the shell COMPUTES, which this file
    cannot know.
    """
    args: list[_Word] = []
    redirects: list[tuple[str, str, _Word]] = []
    buffer: list[str] = []
    literal = True
    glob = False
    started = False
    quoted = False
    pending: tuple[str, str] | None = None
    quote: str | None = None
    index = 0

    def flush() -> None:
        nonlocal buffer, literal, glob, started, quoted, pending
        if not started:
            return
        word = _Word("".join(buffer), literal, glob)
        if pending is not None:
            redirects.append((pending[0], pending[1], word))
            pending = None
        else:
            args.append(word)
        buffer, literal, glob, started, quoted = [], True, False, False, False

    while index < len(text):
        char = text[index]
        if quote == "'":
            if char == "'":
                quote = None
            else:
                buffer.append(char)
            index += 1
            continue
        if quote == '"':
            if char == '"':
                quote = None
            elif char == "\\" and text[index + 1 : index + 2] in ("$", "`", '"', "\\", "\n"):
                buffer.append(text[index + 1])
                index += 1
            else:
                literal = literal and char not in "$`"
                buffer.append(char)
            index += 1
            continue
        if char.isspace():
            flush()
            index += 1
            continue
        if char == "\\":
            buffer.append(text[index + 1 : index + 2])
            started = True
            index += 2
            continue
        if char in "'\"":
            quote = char
            started = quoted = True
            index += 1
            continue
        if char in "<>":
            fd = ""
            if started and not quoted and "".join(buffer).isdigit():
                fd = "".join(buffer)
                buffer, literal, glob, started = [], True, False, False
            flush()
            operator = _REDIRECT_OP.match(text, index)
            assert operator is not None
            pending = (fd, operator.group(0))
            index = operator.end()
            continue
        literal = literal and char not in "$`"
        glob = glob or char in "*?["
        buffer.append(char)
        started = True
        index += 1
    flush()
    return _Parsed(tuple(args), tuple(redirects))


def _dash_escapes(text: str) -> str | None:
    """*text* with the backslash escapes dash's ``echo``/``printf`` format expand.

    Only ``\\n``, ``\\t`` and ``\\\\`` are modelled; any other escape (``\\c``,
    an octal ``\\0nnn``) yields None — unknown output, which reads as not literal.
    """
    out: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "\\":
            out.append(text[index])
            index += 1
            continue
        escape = {"n": "\n", "t": "\t", "\\": "\\"}.get(text[index + 1 : index + 2])
        if escape is None:
            return None
        out.append(escape)
        index += 2
    return "".join(out)


def _literal_output(command: _Command, parsed: _Parsed) -> tuple[str, str, str] | None:
    """``(target, operator, content)`` when *command* writes only literal text to one file.

    Recognised writers, each with a self-test:

    * ``printf '%s\\n' 'L1' 'L2' ... > F`` — one line per argument; a format
      with no ``%`` and no arguments writes the format itself. Any other format
      (``'%s  %s\\n'``, ``%b``) is not modelled: None.
    * ``echo 'L' > F`` / ``echo -n`` — dash's ``echo`` expands backslash escapes
      and has no ``-e`` (it would PRINT ``-e``).
    * ``cat > F <<'EOF'`` + body — the here-document is the content; with an
      unquoted tag a ``$``, backtick or backslash in the body makes it unknown.

    Every argument must be literal and glob-free, and the only redirections are
    the one ``>``/``>>``/``>|`` into F (plus ``cat``'s here-document).
    """
    writes = parsed.writes()
    if len(writes) != 1 or not writes[0].literal or writes[0].glob:
        return None
    operator = next(op for fd, op, target in parsed.redirects if target is writes[0])
    others = [op for fd, op, target in parsed.redirects if target is not writes[0]]
    if not parsed.args or any(not word.literal or word.glob for word in parsed.args):
        return None
    rest = [word.value for word in parsed.args[1:]]
    content: str | None
    if parsed.name == "printf" and not others and rest:
        fmt = _dash_escapes(rest[0])
        if fmt == "%s\n":
            content = "".join(f"{line}\n" for line in rest[1:])
        elif fmt is not None and "%" not in fmt and len(rest) == 1:
            content = fmt
        else:
            content = None
    elif parsed.name == "echo" and not others:
        newline = "\n"
        if rest and rest[0] == "-n":
            newline, rest = "", rest[1:]
        expanded = _dash_escapes(" ".join(rest))
        content = None if expanded is None else expanded + newline
    elif parsed.name == "cat" and not rest and others in (["<<"], ["<<-"]) and len(command.heredocs) == 1:
        heredoc = command.heredocs[0]
        expands = not heredoc.quoted and any(char in heredoc.body for char in "$`\\")
        content = None if expands else heredoc.body + "\n"
    else:
        content = None
    return None if content is None else (writes[0].value, operator, content)


#: One line of a ``sha256sum`` checklist: 64 hex, a space, ``' '`` (text) or
#: ``'*'`` (binary), the path. The BSD ``--tag`` form and backslash-escaped
#: names are valid for ``sha256sum -c`` but not modelled here: they read as
#: malformed, which is red.
_HASH_LINE = re.compile(r"[0-9a-fA-F]{64} [ *](?P<path>\S.*)")


def _hash_line_paths(content: str) -> list[str] | None:
    """The paths *content* lists, or None unless EVERY line is a hash line.

    Without ``--strict`` sha256sum only warns about a malformed line and goes
    on, so a line that is not a 64-hex hash line must not be waved through.
    """
    lines = content.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    paths: list[str] = []
    for line in lines:
        match = _HASH_LINE.fullmatch(line)
        if match is None:
            return None
        paths.append(match.group("path"))
    return paths or None


def _has_check_flag(parsed: _Parsed) -> bool:
    for word in parsed.args[1:]:
        if word.value == "--":
            return False
        if _SHORT_CHECK.fullmatch(word.value) or _long_option_matches(word.value, "--check"):
            return True
    return False


#: Commands that write a file named by an ARGUMENT, not only by a redirection.
_ARGUMENT_WRITERS = frozenset({"tee", "cp", "mv", "dd", "install", "ln", "sed", "python", "python3", "sh", "bash"})


def _file_content(commands: list[_Command], check: int, path: str) -> str | None:
    """What the checklist *path* holds when ``commands[check]`` reads it, or None.

    Known only when the RUN wrote it, before the check, exclusively through
    ``_literal_output`` writers, the first of them truncating (``>``/``>|``) — a
    first ``>>`` appends to whatever an earlier layer left there. None, too, as
    soon as any other command before the check could have touched it:

    * one that names it — its full path, or its basename as a word of its own
      (``sha256sum /model/* > /tmp/s``, ``cp x /tmp/s``, ``python -c
      "open('/tmp/s', 'w')"``). A ``sha256sum`` check that only READS it is the
      one exemption;
    * one that redirects output to a non-literal target (``> "$SUMS"``), or an
      argument-writer (``tee``, ``cp``, ``python`` …) with a non-literal
      argument — the path it writes is computed, and may be this one;
    * for a relative *path*, any ``cd`` before the check.
    """
    target = posixpath.normpath(path)
    if not target.startswith("/") and any(command.words[:1] == ("cd",) for command in commands[:check]):
        return None
    mention = re.compile(r"(?<![\w.-])" + re.escape(posixpath.basename(target)) + r"(?![\w.-])")
    content: str | None = None
    for command in commands[:check]:
        parsed = _parse(command.text)
        written = _literal_output(command, parsed)
        if written is not None:
            if posixpath.normpath(written[0]) != target:
                continue
            if written[1] == ">>":
                if content is None:
                    return None
                content += written[2]
            else:
                content = written[2]
            continue
        if any(not word.literal for fd, op, word in parsed.redirects if op in (">", ">>", ">|", "<>")):
            return None
        if parsed.name in _ARGUMENT_WRITERS and any(not word.literal for word in parsed.args):
            return None
        surface = _command_surface(command, parsed)
        if target in surface or mention.search(surface):
            if parsed.name == "sha256sum" and _has_check_flag(parsed) and not parsed.writes():
                continue
            return None
    return content


def _command_surface(command: _Command, parsed: _Parsed) -> str:
    """Everything a path could be spelled in: the raw text AND every word after quote removal.

    The raw text alone misses ``/mod""el`` and ``/mo\\del``, which the shell
    reads as ``/model``; the words alone miss a path inside a ``python -c`` body.
    """
    values = [word.value for word in parsed.args] + [target.value for _, _, target in parsed.redirects]
    return "\n".join([command.full, *values])


def _checklist_paths(commands: list[_Command], check: int) -> list[str] | None:
    """The hash-line paths the check ``commands[check]`` verifies, or None.

    None unless EVERY checklist the check reads is a literal from this RUN
    (``_file_content``): its file operands, or — with no operand or ``-`` —
    its standard input from ``< F`` or a here-document, which then must be
    literal itself. A piped list (``printf ... | sha256sum -c``) is NOT
    modelled: the shell model refuses a check after ``|``, the conservative
    direction.
    """
    command = commands[check]
    parsed = _parse(command.text)
    if any(not word.literal or word.glob for word in parsed.args):
        return None
    operands: list[str] = []
    options_done = False
    for word in parsed.args[1:]:
        if not options_done and word.value == "--":
            options_done = True
        elif options_done or not word.value.startswith("-") or word.value == "-":
            operands.append(word.value)
    stdin = [(op, target) for fd, op, target in parsed.redirects if op in ("<", "<<", "<<-") and fd in ("", "0")]
    paths: list[str] = []
    for operand in operands or ["-"]:
        content: str | None = None
        if operand != "-":
            content = _file_content(commands, check, operand)
        elif len(stdin) == 1 and stdin[0][0] == "<" and stdin[0][1].literal:
            content = _file_content(commands, check, stdin[0][1].value)
        elif len(stdin) == 1 and len(command.heredocs) == 1:
            heredoc = command.heredocs[0]
            if heredoc.quoted or not any(char in heredoc.body for char in "$`\\"):
                content = heredoc.body + "\n"
        listed = None if content is None else _hash_line_paths(content)
        if listed is None:
            return None
        paths.extend(listed)
    return paths


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _mentions(text: str, root: str) -> bool:
    """Whether *text* names *root* or a path under it (``/model``, ``'/model/x'``, ``=/model``)."""
    return re.search(r"(?<![\w-])" + re.escape(root) + r"(?![\w.-])", text) is not None


#: Options of ``mv``/``cp`` that change nothing about WHICH path is written.
_PLAIN_COPY_OPTIONS = frozenset({"-f", "-v", "-n", "-p", "-fv", "-vf"})


def _output_options(parsed: _Parsed) -> tuple[list[str], list[str]]:
    """``(outputs, rest)`` of a ``curl``/``wget``: the files it writes and every other argument."""
    short, long = ("-o", "--output") if parsed.name == "curl" else ("-O", "--output-document")
    outputs: list[str] = []
    rest: list[str] = []
    words = [word.value for word in parsed.args[1:]]
    index = 0
    while index < len(words):
        word = words[index]
        if word in (short, long) and index + 1 < len(words):
            outputs.append(words[index + 1])
            index += 2
            continue
        if word.startswith(long + "="):
            outputs.append(word.split("=", 1)[1])
        elif word.startswith(short) and len(word) > 2:
            outputs.append(word[2:])
        else:
            rest.append(word)
        index += 1
    return outputs, rest


def _pairing_problem(
    commands: list[_Command], roots: set[str], fetching: list[int], elsewhere: list[str]
) -> str | None:
    """Why the kept files and the verified hash lines of one RUN are not the same set; None if they are.

    *roots* are the directories another stage copies out of this one (``COPY
    --from=<stage>``, ``RUN --mount=from=<stage>``): what the image KEEPS.
    *elsewhere* is every other instruction of the stage. A kept path is one a
    command of this RUN places under a root:

    * ``mv``/``cp`` with only ``-f -v -n -p``: each source lands as
      ``<target>/<basename>`` when the target is a root, ends in ``/`` or has
      several sources, else as the target itself. A glob, a relative path, a
      source under a root, ``-r``/``-a``/``-t`` and the like are red — the
      kept set would be unknowable;
    * ``curl -o`` / ``wget -O`` into a root;
    * a literal writer (``printf``/``echo``/``cat <<EOF``) into a root — which
      makes a checklist stored IN the model dir red: it cannot hash itself;
    * ``mkdir``, ``rm``, ``chmod``, ``chown`` and a reading ``sha256sum -c``
      add nothing. ANY other command that names a root is red: the fetch
      itself (``snapshot_download(local_dir='/model')``, ``hf download
      --local-dir /model``), ``tar -C``, ``ln``, ``cd``, a redirect.

    Then, both directions (#1735): every kept path has exactly one hash line in
    a check that verifies the fetch, every such hash line names a kept path,
    and the check that lists a path runs AFTER its last write — a ``cp`` over a
    verified file after the check is red. Each root must be created by a
    ``mkdir`` WITHOUT ``-p`` before the first write: that fails the build if
    the directory already exists, so nothing an earlier layer or the base image
    put there can ride along unlisted. An instruction elsewhere in the stage
    that names a root (a second RUN, ``COPY x /model/``, ``WORKDIR /model``) is
    red for the same reason.
    """
    if not roots:
        return "no `COPY --from=<stage>` or `RUN --mount=from=<stage>` reads this stage, so what it keeps is unknown"
    if "/" in roots:
        return "the stage's whole filesystem is copied out; a kept set cannot be paired with hash lines"
    for instruction in elsewhere:
        for root in sorted(roots):
            if _mentions(instruction, root):
                return f"`{instruction.split(chr(10))[0].strip()}` writes {root} outside the verified RUN"
    writes: list[tuple[int, str]] = []
    created: dict[str, int] = {}
    for index, command in enumerate(commands):
        parsed = _parse(command.text)
        computed = (
            parsed.name in _ARGUMENT_WRITERS | {"curl", "wget"} and any(not w.literal for w in parsed.args)
        ) or any(not target.literal for target in parsed.writes())
        if computed:
            # `mv x "$M"/`, `> "$OUT"`: the path is computed — an `ENV` of an
            # ancestor stage can point it at a kept directory unseen.
            return f"`{command.text[:120]}` writes to a computed path, which may be a kept directory"
        touched = sorted(root for root in roots if _mentions(_command_surface(command, parsed), root))
        if not touched:
            continue
        refusal = f"`{command.text[:120]}` touches {touched[0]} in a way the kept set cannot be read from"
        if any(not word.literal for word in parsed.args) or any(not t.literal for _, _, t in parsed.redirects):
            return refusal
        written = _literal_output(command, parsed)
        if written is not None:
            target = posixpath.normpath(written[0])
            if any(_under(target, root) for root in roots):
                writes.append((index, target))
            continue
        if any(any(_under(posixpath.normpath(t.value), r) for r in roots) for t in parsed.writes()):
            return refusal
        operands = [word.value for word in parsed.args[1:] if not word.value.startswith("-")]
        options = [word.value for word in parsed.args[1:] if word.value.startswith("-")]
        if parsed.name == "mkdir":
            if any(option not in ("-p", "-v") for option in options):
                return refusal
            for operand in operands:
                if posixpath.normpath(operand) in roots and "-p" not in options:
                    created.setdefault(posixpath.normpath(operand), index)
            continue
        if parsed.name in ("rm", "chmod", "chown") or (parsed.name == "sha256sum" and _has_check_flag(parsed)):
            continue
        if parsed.name in ("mv", "cp"):
            if any(option not in _PLAIN_COPY_OPTIONS for option in options) or len(operands) < 2:
                return refusal
            *sources, target = operands
            if any(word.glob for word in parsed.args) or not all(o.startswith("/") for o in operands):
                return refusal
            if any(_under(posixpath.normpath(source), root) for source in sources for root in roots):
                return refusal
            destination = posixpath.normpath(target)
            if not any(_under(destination, root) for root in roots):
                return refusal
            into_directory = destination in roots or target.endswith("/") or len(sources) > 1
            for source in sources:
                kept = posixpath.join(destination, posixpath.basename(posixpath.normpath(source)))
                writes.append((index, kept if into_directory else destination))
            continue
        if parsed.name in ("curl", "wget"):
            outputs, rest = _output_options(parsed)
            if any(_mentions(word, root) for word in rest for root in roots):
                return refusal
            for output in outputs:
                if not output.startswith("/"):
                    return refusal
                writes.append((index, posixpath.normpath(output)))
            continue
        return refusal

    first_write = {root: min((i for i, path in writes if _under(path, root)), default=None) for root in roots}
    for root in sorted(roots):
        start = first_write[root]
        if root not in created or (start is not None and created[root] > start):
            return f"{root} is not created by a `mkdir` without `-p` before it is filled, so it may not start empty"

    checks: dict[int, list[str]] = {}
    for fetch in fetching:
        checks.update(_verifying_checks(commands, fetch))
    lines: Counter[str] = Counter()
    listed_in: dict[str, int] = {}
    for check, paths in checks.items():
        for path in paths:
            if not path.startswith("/"):
                return f"hash line for relative path {path!r}: it cannot be paired with a kept path"
            lines[posixpath.normpath(path)] += 1
            listed_in[posixpath.normpath(path)] = check
    last_write: dict[str, int] = {}
    for index, path in writes:
        last_write[path] = max(index, last_write.get(path, index))
    duplicated = sorted(path for path, count in lines.items() if count > 1)
    if duplicated:
        return f"more than one hash line for {duplicated}"
    unlisted = sorted(set(last_write) - set(lines))
    if unlisted:
        return f"kept without a hash line: {unlisted}"
    unkept = sorted(set(lines) - set(last_write))
    if unkept:
        return f"hash line for a path this stage does not keep: {unkept}"
    late = sorted(path for path, index in last_write.items() if listed_in[path] < index)
    if late:
        return f"written after the check that lists it: {late}"
    return None


def _command_fetches(command: _Command) -> bool:
    """Whether *command* (here-document bodies included) contains any Hugging Face fetch spelling."""
    text = command.full
    return bool(_call_pattern(text).search(text) or _CLI_DOWNLOAD.search(text) or _RESOLVE_URL.search(text))


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
    #: Why the files the stage keeps and the verified hash lines differ; None
    #: when they are the same set (#1735, ``_pairing_problem``).
    pairing: str | None = "not evaluated"

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


#: ``RUN --mount=type=bind,from=<stage>,source=<path>,...`` — a read of another stage.
_MOUNT = re.compile(r"--mount=(?P<spec>\S+)")


def _kept_roots(instructions: list[tuple[int, int, str]]) -> dict[str, set[str]]:
    """Per stage name, the paths other instructions copy out of it — what the image keeps.

    Read from ``COPY --from=<stage> <src>... <dest>`` (shell form; the JSON
    form and a ``--from`` naming a stage by INDEX are not read, so such a stage
    has no roots and its fetch is red) and from
    ``RUN --mount=...,from=<stage>,source=<src>`` (``source`` defaults to ``/``).
    """
    roots: dict[str, set[str]] = {}
    for _first, _last, text in instructions:
        joined = re.sub(r"\\\n", " ", text).strip()
        if re.match(r"COPY\b", joined, re.IGNORECASE):
            parsed = _parse(joined[4:])
            stage = next((w.value.split("=", 1)[1] for w in parsed.args if w.value.startswith("--from=")), None)
            operands = [w.value for w in parsed.args if not w.value.startswith("--")]
            if stage is not None and len(operands) >= 2:
                roots.setdefault(stage, set()).update(posixpath.normpath(src) for src in operands[:-1])
        elif _RUN_PREFIX.match(joined):
            for mount in _MOUNT.finditer(_RUN_PREFIX.match(joined).group(0)):
                options = dict(part.split("=", 1) for part in mount.group("spec").split(",") if "=" in part)
                if "from" in options:
                    source = options.get("source", options.get("src", "/"))
                    roots.setdefault(options["from"], set()).add(posixpath.normpath(source))
    return roots


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

    instructions = [(first, last, "\n".join(blanked_lines[first - 1 : last])) for first, last in spans]
    roots = _kept_roots(instructions)

    def pairing(line: int) -> str | None:
        """``_pairing_problem`` for the RUN that holds *line*, against its stage's kept roots."""
        stage = stage_of(line)
        for first, last, _text in instructions:
            if first <= line <= last:
                commands = _shell_commands(_run_script(blanked_lines[first - 1 : last]))
                fetching = [index for index, command in enumerate(commands) if _command_fetches(command)]
                elsewhere = [
                    other
                    for start, end, other in instructions
                    if (start, end) != (first, last) and stage_of(start) == stage and not _FROM_STAGE.match(other)
                ]
                return _pairing_problem(commands, roots.get(stage, set()) if stage else set(), fetching, elsewhere)
        return "the fetch is not inside a RUN instruction"

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
                pairing=pairing(line_of(match.start())),
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
                pairing=pairing(line_of(match.start())),
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
                pairing=pairing(line_of(match.start())),
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

    @pytest.mark.parametrize("site", _PINNED_SITES, ids=lambda site: site.label)
    def test_pinned_fetch_keeps_exactly_the_files_it_verifies(self, site: FetchSite) -> None:
        """#1735: a check covers only the files its checklist names.

        ``sha256sum -c`` never looks at a file its list leaves out, so a file
        added to the ``mv`` but not to the ``printf`` ships unverified while the
        check stays green. The files the stage keeps (what ``COPY --from`` reads)
        and the verified hash lines must be one set.
        """
        assert site.pairing is None, (
            f"{site.label}: the files this stage keeps and its verified hash lines differ: {site.pairing}. "
            "Give every file moved into the kept directory exactly one literal `<sha256>  <path>` line in "
            "the checklist of the same RUN, and no line for anything else (#1735)."
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

_HEX = "faae32b124a9d54afb7e89b5e9896e03c18a9552d56d1d6b273a709a83012486"
_HEX_2 = "8bf8afbfd11306bd872018c53bfdf2e160a56f8edbcf49933324404791c148d3"

#: The checklist every positive digest spelling reads: literals, this RUN, ``>``.
_WRITE_SUMS = f"    printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums && \\\n"

_DIGEST_SPELLINGS: list[tuple[str, str, bool]] = [
    (
        "sha256sum -c --strict in the same RUN",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c --strict /tmp/sums\n",
        True,
    ),
    ("--strict before -c", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum --strict -c /tmp/sums\n", True),
    ("long --check", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum --check /tmp/sums\n", True),
    ("abbreviated --c", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum --c /tmp/sums\n", True),
    (
        "after --, --ignore-missing is a file operand, not the option",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX}  /m/model.onnx' > ./--ignore-missing && \\\n"
        "    sha256sum -c -- --ignore-missing\n",
        True,
    ),
    ("--ignore-missing after -c", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c --ignore-missing /tmp/sums\n", False),
    (
        "--ignore-missing before -c",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum --ignore-missing -c /tmp/sums\n",
        False,
    ),
    (
        "--ignore-missing after the operand",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums --ignore-missing\n",
        False,
    ),
    ("abbreviated --ignore", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c --ignore /tmp/sums\n", False),
    ("abbreviated --i", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c --strict --i /tmp/sums\n", False),
    (
        "--ignore-missing next to --check",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum --check --strict --ignore-m /tmp/sums\n",
        False,
    ),
    (
        "blank line (a removed comment) inside the continuation",
        _PINNED_FETCH + _WRITE_SUMS + "\n    sha256sum -c /tmp/sums\n",
        True,
    ),
    ("no check at all", _PINNED_FETCH + _WRITE_SUMS + "    rm -rf /dl\n", False),
    ("sha256sum that only COMPUTES", _PINNED_FETCH + "    sha256sum /m/model.onnx > /tmp/sums\n", False),
    (
        "check in the NEXT instruction",
        _PINNED_FETCH + _WRITE_SUMS + "    rm -rf /dl\nRUN sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "check only in a comment",
        _PINNED_FETCH + _WRITE_SUMS + "    rm -rf /dl\n# sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "heredoc RUN",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums\n"
        "sha256sum -c /tmp/sums\nEOF\n",
        True,
    ),
    (
        "check BEFORE the fetch in the same RUN",
        f"RUN printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums && sha256sum -c /tmp/sums && "
        'python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n",
        False,
    ),
    ("check || true", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums || true\n", False),
    ("check || :", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums || :\n", False),
    ("check || exit 0", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums || exit 0\n", False),
    ("check ; true", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums; true\n", False),
    ("check ; any other command", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums; rm -rf /dl\n", False),
    ("check && y || true", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums && rm -rf /dl || true\n", False),
    ("check piped into tee", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums | tee /tmp/log\n", False),
    ("check inside $( )", _PINNED_FETCH + _WRITE_SUMS + "    echo $(sha256sum -c /tmp/sums)\n", False),
    ("check inside backticks", _PINNED_FETCH + _WRITE_SUMS + "    echo `sha256sum -c /tmp/sums`\n", False),
    ("negated check", _PINNED_FETCH + _WRITE_SUMS + "    ! sha256sum -c /tmp/sums\n", False),
    ("backgrounded check", _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c /tmp/sums & wait\n", False),
    (
        "check behind || (runs only if the step before failed)",
        _PINNED_FETCH + _WRITE_SUMS + "    true || sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "set -e, then ; after the check",
        'RUN set -e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"; "
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums; "
        "sha256sum -c /tmp/sums; rm -rf /dl\n",
        True,
    ),
    (
        "set -e undone by set +e, then ; after the check",
        'RUN set -e; set +e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"; "
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums; "
        "sha256sum -c /tmp/sums; rm -rf /dl\n",
        False,
    ),
    (
        "set +e does not mask an && tail (measured)",
        'RUN set +e; python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\" && "
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums && "
        "sha256sum -c /tmp/sums && rm -rf /dl\n",
        True,
    ),
    (
        "heredoc RUN, a line after the check masks it",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums\n"
        "sha256sum -c /tmp/sums\nrm -rf /dl\nEOF\n",
        False,
    ),
    (
        "heredoc RUN under set -e, a line after the check",
        "RUN <<EOF\nset -e\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums\n"
        "sha256sum -c /tmp/sums\nrm -rf /dl\nEOF\n",
        True,
    ),
    (
        "heredoc RUN, check after its terminator",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"printf '%s\\n' '{_HEX}  /m/model.onnx' > /tmp/sums\n"
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


# --------------------------------------------------------------------------
# #1735 rule A: the checklist is 64-hex literals written in the same RUN
# --------------------------------------------------------------------------

_CHECK = "    sha256sum -c --strict /tmp/sums\n"

_CHECKLIST_SPELLINGS: list[tuple[str, str, bool]] = [
    # --- written from literals: verified
    ("printf '%s\\n' literals, >", _PINNED_FETCH + _WRITE_SUMS + _CHECK, True),
    (
        "printf '%s\\n' literals, >|",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX}  /m/model.onnx' >| /tmp/sums && \\\n" + _CHECK,
        True,
    ),
    (
        "printf with the redirect first and double quotes",
        _PINNED_FETCH + f'    printf > /tmp/sums "%s\\n" "{_HEX} */m/model.onnx" && \\\n' + _CHECK,
        True,
    ),
    (
        "printf of a %-free format",
        _PINNED_FETCH + f"    printf '{_HEX}  /m/model.onnx\\n' > /tmp/sums && \\\n" + _CHECK,
        True,
    ),
    ("echo literal", _PINNED_FETCH + f"    echo '{_HEX}  /m/model.onnx' > /tmp/sums && \\\n" + _CHECK, True),
    (
        "echo literal with a dash escape for the second line",
        _PINNED_FETCH + f"    echo '{_HEX}  /m/a\\n{_HEX_2}  /m/b' > /tmp/sums && \\\n" + _CHECK,
        True,
    ),
    (
        "> then >> of literals",
        _PINNED_FETCH + _WRITE_SUMS + f"    echo '{_HEX_2}  /m/b' >> /tmp/sums && \\\n" + _CHECK,
        True,
    ),
    (
        "two literal checklists read by one check",
        _PINNED_FETCH
        + _WRITE_SUMS
        + f"    echo '{_HEX_2}  /m/b' > /tmp/more && \\\n"
        + "    sha256sum -c /tmp/sums /tmp/more\n",
        True,
    ),
    (
        "cat heredoc with a quoted tag",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"cat > /tmp/sums <<'SUMS'\n{_HEX}  /m/model.onnx\nSUMS\n"
        "sha256sum -c --strict /tmp/sums\nEOF\n",
        True,
    ),
    (
        "cat heredoc with an unquoted tag and no expansion",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"cat <<SUMS > /tmp/sums\n{_HEX}  /m/model.onnx\nSUMS\n"
        "sha256sum -c --strict /tmp/sums\nEOF\n",
        True,
    ),
    (
        "check reading a literal heredoc on stdin",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        f"sha256sum -c --strict <<'SUMS'\n{_HEX}  /m/model.onnx\nSUMS\nEOF\n",
        True,
    ),
    (
        "check reading the literal checklist through <",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum -c --strict < /tmp/sums\n",
        True,
    ),
    # --- the issue's spelling 1 and its relatives: NOT verified
    (
        "self-referential: computed, then checked",
        _PINNED_FETCH + "    sha256sum /m/model.onnx > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    ("self-referential over a glob", _PINNED_FETCH + "    sha256sum /m/* > /tmp/sums && \\\n" + _CHECK, False),
    (
        "self-referential through a relative name after cd",
        _PINNED_FETCH + "    cd /tmp && sha256sum /m/model.onnx > sums && \\\n" + _CHECK,
        False,
    ),
    (
        "literal, then a computed line appended",
        _PINNED_FETCH + _WRITE_SUMS + "    sha256sum /m/extra >> /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "computed, then overwritten by literals (red by the rule, not by the bytes)",
        _PINNED_FETCH + "    sha256sum /m/model.onnx > /tmp/sums && \\\n" + _WRITE_SUMS + _CHECK,
        False,
    ),
    (
        "computed hash substituted into printf",
        _PINNED_FETCH + "    printf '%s\\n' \"$(sha256sum /m/model.onnx)\" > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "computed hash substituted with backticks",
        _PINNED_FETCH + "    echo `sha256sum /m/model.onnx` > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "cat heredoc with an unquoted tag and a substitution",
        "RUN <<EOF\n"
        f"python -c \"import huggingface_hub; huggingface_hub.snapshot_download('org/model', revision='{_SHA}')\"\n"
        "cat > /tmp/sums <<SUMS\n$(sha256sum /m/model.onnx)\nSUMS\n"
        "sha256sum -c --strict /tmp/sums\nEOF\n",
        False,
    ),
    (
        "written by python",
        _PINNED_FETCH
        + "    python -c \"import hashlib; open('/tmp/sums', 'w').write(hashlib.sha256(b'x').hexdigest())\" && \\\n"
        + _CHECK,
        False,
    ),
    (
        "copied in, not written in the RUN",
        _PINNED_FETCH + "    cp /src/model.sha256 /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    ("never written in the RUN (COPY'd earlier)", _PINNED_FETCH + _CHECK, False),
    (
        "first literal write APPENDS to what an earlier layer left",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX}  /m/model.onnx' >> /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "written through a variable redirect",
        _PINNED_FETCH + '    sha256sum /m/model.onnx > "$SUMS" && \\\n' + _CHECK,
        False,
    ),
    (
        "written through tee with a variable",
        _PINNED_FETCH
        + '    sha256sum /m/model.onnx > /tmp/computed && tee "$SUMS" < /tmp/computed > /dev/null && \\\n'
        + _CHECK,
        False,
    ),
    (
        "self-referential into a quote-split name",
        _PINNED_FETCH + '    sha256sum /m/model.onnx > /tmp/su""ms && \\\n' + _CHECK,
        False,
    ),
    (
        "one of two checklists is computed",
        _PINNED_FETCH
        + _WRITE_SUMS
        + "    sha256sum /m/b > /tmp/more && \\\n"
        + "    sha256sum -c /tmp/sums /tmp/more\n",
        False,
    ),
    (
        "piped checklist (red by the shell model: a check after | is refused)",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX}  /m/model.onnx' | sha256sum -c --strict\n",
        False,
    ),
    (
        "63-hex line",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX[:-1]}  /m/model.onnx' > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "a line that is not a hash line (ignored by -c without --strict)",
        _PINNED_FETCH + f"    printf '%s\\n' '{_HEX}  /m/model.onnx' 'junk' > /tmp/sums && \\\n"
        "    sha256sum -c /tmp/sums\n",
        False,
    ),
    (
        "echo -e is printed by dash",
        _PINNED_FETCH + f"    echo -e '{_HEX}  /m/model.onnx' > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "printf with a two-%s format (not modelled)",
        _PINNED_FETCH + f"    printf '%s  %s\\n' '{_HEX}' /m/model.onnx > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "BSD --tag line (not modelled)",
        _PINNED_FETCH + f"    printf '%s\\n' 'SHA256 (/m/model.onnx) = {_HEX}' > /tmp/sums && \\\n" + _CHECK,
        False,
    ),
    (
        "check with no checklist at all",
        _PINNED_FETCH + "    sha256sum -c --strict\n",
        False,
    ),
]


@pytest.mark.parametrize(
    ("snippet", "checked"),
    [(s, c) for _, s, c in _CHECKLIST_SPELLINGS],
    ids=[n for n, _, _ in _CHECKLIST_SPELLINGS],
)
def test_scanner_requires_a_literal_checklist(snippet: str, checked: bool) -> None:
    """#1735 rule A: a check whose list the RUN did not write from literals verifies nothing."""
    sites = fetch_sites(snippet, path="Dockerfile")
    assert len(sites) == 1 and sites[0].pinned, "the pinned fetch in the snippet was not found"
    assert sites[0].digest_checked is checked


# --------------------------------------------------------------------------
# #1735 rule B: what the stage keeps and what the checklist lists are one set
# --------------------------------------------------------------------------

_FETCH_TO_DL = (
    "FROM base AS dl\n"
    'RUN python -c "import huggingface_hub; '
    f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}', local_dir='/dl')\" && \\\n"
)
_KEEP = "FROM runtime AS app\nCOPY --from=dl /model/ /app/m/\n"
_TWO_LINES = f"    printf '%s\\n' '{_HEX}  /model/a' '{_HEX_2}  /model/b' > /tmp/sums && \\\n"
_VERIFY = "    sha256sum -c --strict /tmp/sums && \\\n    rm -rf /dl /tmp/sums\n"


def _stage(body: str, keep: str = _KEEP) -> str:
    return _FETCH_TO_DL + body + keep


_PAIRING_SPELLINGS: list[tuple[str, str, str | None]] = [
    # --- paired
    (
        "mv of two files into the kept dir",
        _stage("    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY),
        None,
    ),
    (
        "cp instead of mv",
        _stage("    mkdir /model && \\\n    cp /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY),
        None,
    ),
    (
        "mv one file per command, target without a slash",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /model && \\\n    mv -f /dl/b /model && \\\n" + _TWO_LINES + _VERIFY
        ),
        None,
    ),
    (
        "mv renaming a single file",
        _stage(
            "    mkdir /model && \\\n    mv /dl/onnx/model.onnx /model/a && \\\n    mv /dl/b /model/ && \\\n"
            + _TWO_LINES
            + _VERIFY
        ),
        None,
    ),
    (
        "curl -o into the kept dir from a pinned resolve url",
        "FROM base AS dl\nRUN mkdir /model && \\\n"
        f"    curl -fsSL -o /model/a https://huggingface.co/org/model/resolve/{_SHA}/a && \\\n"
        f"    curl -fsSL --output /model/b https://huggingface.co/org/model/resolve/{_SHA}/b && \\\n"
        + _TWO_LINES
        + _VERIFY
        + _KEEP,
        None,
    ),
    (
        "hash lines split over two literal checklists",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n"
            f"    echo '{_HEX}  /model/a' > /tmp/one && echo '{_HEX_2}  /model/b' > /tmp/two && \\\n"
            "    sha256sum -c /tmp/one /tmp/two\n"
        ),
        None,
    ),
    (
        "kept dir read through RUN --mount=from",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY,
            keep="FROM runtime AS app\nRUN --mount=type=bind,from=dl,source=/model,target=/m cp /m/a /m/b /app/\n",
        ),
        None,
    ),
    # --- the issue's spelling 2 and its relatives: NOT paired
    (
        "kept file without a hash line",
        _stage("    mkdir /model && \\\n    mv /dl/a /dl/b /dl/c /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "kept without a hash line: ['/model/c']",
    ),
    (
        "hash line for a file that is not kept",
        _stage("    mkdir /model && \\\n    mv /dl/a /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "hash line for a path this stage does not keep: ['/model/b']",
    ),
    (
        "hash line for a path outside the kept dir",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /model/ && \\\n"
            f"    printf '%s\\n' '{_HEX}  /model/a' '{_HEX_2}  /dl/b' > /tmp/sums && \\\n" + _VERIFY
        ),
        "hash line for a path this stage does not keep: ['/dl/b']",
    ),
    (
        "two hash lines for one file",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /model/ && \\\n"
            f"    printf '%s\\n' '{_HEX}  /model/a' '{_HEX}  /model/a' > /tmp/sums && \\\n" + _VERIFY
        ),
        "more than one hash line for ['/model/a']",
    ),
    (
        "a kept file overwritten after the check",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n"
            + _TWO_LINES
            + "    sha256sum -c --strict /tmp/sums && \\\n    cp /dl/evil /model/a\n"
        ),
        "written after the check that lists it: ['/model/a']",
    ),
    (
        "a curl -o without a hash line",
        "FROM base AS dl\nRUN mkdir /model && \\\n"
        f"    curl -fsSL -o /model/a https://huggingface.co/org/model/resolve/{_SHA}/a && \\\n"
        f"    curl -fsSL -o /model/b https://huggingface.co/org/model/resolve/{_SHA}/b && \\\n"
        f"    curl -fsSL -o /model/c https://huggingface.co/org/model/resolve/{_SHA}/c && \\\n"
        + _TWO_LINES
        + _VERIFY
        + _KEEP,
        "kept without a hash line: ['/model/c']",
    ),
    (
        "the checklist stored inside the kept dir",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n"
            f"    printf '%s\\n' '{_HEX}  /model/a' '{_HEX_2}  /model/b' > /model/SHA256SUMS && \\\n"
            "    sha256sum -c --strict /model/SHA256SUMS\n"
        ),
        "kept without a hash line: ['/model/SHA256SUMS']",
    ),
    ("mv of a glob", _stage("    mkdir /model && \\\n    mv /dl/* /model/ && \\\n" + _TWO_LINES + _VERIFY), "touches"),
    (
        "cp -r of a directory",
        _stage("    mkdir /model && \\\n    cp -r /dl/onnx /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "touches",
    ),
    ("mv -t", _stage("    mkdir /model && \\\n    mv -t /model /dl/a /dl/b && \\\n" + _TWO_LINES + _VERIFY), "touches"),
    (
        "mv with a relative source",
        _stage("    mkdir /model && \\\n    mv a b /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "touches",
    ),
    (
        "snapshot_download straight into the kept dir",
        "FROM base AS dl\n"
        'RUN mkdir /model && python -c "import huggingface_hub; '
        f"huggingface_hub.snapshot_download('org/model', revision='{_SHA}', local_dir='/model')\" && \\\n"
        + _TWO_LINES
        + _VERIFY
        + _KEEP,
        "touches",
    ),
    (
        "hf download --local-dir into the kept dir",
        f"FROM base AS dl\nRUN mkdir /model && hf download org/model --revision {_SHA} --local-dir /model && \\\n"
        + _TWO_LINES
        + _VERIFY
        + _KEEP,
        "touches",
    ),
    (
        "echo into the kept dir outside any checklist",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && echo x > /model/c && \\\n" + _TWO_LINES + _VERIFY
        ),
        "kept without a hash line: ['/model/c']",
    ),
    (
        "mv into a quote-split spelling of the kept dir",
        _stage('    mkdir /model && \\\n    mv /dl/a /dl/b /dl/c /mod""el/ && \\\n' + _TWO_LINES + _VERIFY),
        "kept without a hash line: ['/model/c']",
    ),
    (
        "mv into a computed path",
        _stage('    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && mv /dl/c "$M"/ && \\\n' + _TWO_LINES + _VERIFY),
        "computed path",
    ),
    (
        "tar -C into the kept dir",
        _stage("    mkdir /model && tar -xf /dl/x.tar -C /model && \\\n" + _TWO_LINES + _VERIFY),
        "touches",
    ),
    (
        "ln -s into the kept dir",
        _stage("    mkdir /model && ln -s /dl/a /model/a && \\\n" + _TWO_LINES + _VERIFY),
        "touches",
    ),
    (
        "cd into the kept dir",
        _stage("    mkdir /model && cd /model && mv /dl/a /dl/b . && \\\n" + _TWO_LINES + _VERIFY),
        "touches",
    ),
    (
        "mkdir -p does not prove the kept dir started empty",
        _stage("    mkdir -p /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "not created by a `mkdir` without `-p`",
    ),
    (
        "kept dir never created in the RUN",
        _stage("    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY),
        "not created by a `mkdir` without `-p`",
    ),
    (
        "a later RUN of the stage adds a file",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n"
            + _TWO_LINES
            + _VERIFY
            + "RUN echo x > /model/c\n"
        ),
        "outside the verified RUN",
    ),
    (
        "a COPY into the kept dir",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY + "COPY extra /model/\n"
        ),
        "outside the verified RUN",
    ),
    (
        "no stage copies out of the download stage",
        _stage("    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY, keep=""),
        "reads this stage",
    ),
    (
        "the whole filesystem is copied out",
        _stage(
            "    mkdir /model && \\\n    mv /dl/a /dl/b /model/ && \\\n" + _TWO_LINES + _VERIFY,
            keep="FROM scratch\nCOPY --from=dl / /\n",
        ),
        "whole filesystem",
    ),
]


@pytest.mark.parametrize(
    ("snippet", "problem"),
    [(s, p) for _, s, p in _PAIRING_SPELLINGS],
    ids=[n for n, _, _ in _PAIRING_SPELLINGS],
)
def test_scanner_pairs_kept_files_with_hash_lines(snippet: str, problem: str | None) -> None:
    """#1735 rule B: kept paths and verified hash lines are the same set, both ways."""
    sites = [site for site in fetch_sites(snippet, path="Dockerfile") if site.pinned]
    assert sites, "the pinned fetch in the snippet was not found"
    for site in sites:
        if problem is None:
            assert site.pairing is None
        else:
            assert site.pairing is not None and problem in site.pairing, site.pairing


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
