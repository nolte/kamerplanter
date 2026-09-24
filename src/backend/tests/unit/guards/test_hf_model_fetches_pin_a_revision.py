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
instruction not — so no unverified byte is committed to a layer. A
``sha256sum`` that only computes (no check flag), one in a comment, or a check
done some other way (``hashlib`` in Python) does not count; the last is a
stated gap, not a permission.

``from_pretrained('/model')`` and friends with a literal local path are not
fetches and are skipped; a non-literal first argument is NOT skipped, because
this file cannot tell a path from a hub id it cannot see.

**Residual, stated rather than implied.** A download written in a script that
the Dockerfile ``COPY``s and runs (``src/inference-service`` exports DINOv2 via
``torch.hub.load`` from such a script — not Hugging Face, and not in this
file's corpus), ``transformers.pipeline(model=...)``, or a fetch spelled through
``getattr`` is not seen. The non-vacuity assertion below guarantees the scanner
reaches the tree; it cannot guarantee a spelling nobody has written yet.

Traces to #1480 (no TC-ID: image build configuration is not a user-facing case).
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

#: ``sha256sum -c`` / ``--check``, flags in any order and combined short flags
#: (``-c --strict``, ``--strict -c``, ``-bc``). ``sha256sum FILE > SUMS`` without
#: a check flag COMPUTES a digest and verifies nothing, so it must not match.
_DIGEST_CHECK = re.compile(r"\bsha256sum\s+(?:--?[\w-]+\s+)*?(?:-[a-zA-Z]*c[a-zA-Z]*|--check)(?=\s|$)")

#: A heredoc opener in a Dockerfile instruction: ``<<EOF``, ``<<-EOF``, ``<<'EOF'``.
_HEREDOC = re.compile(r"<<-?\s*(?P<q>['\"]?)(?P<tag>\w+)(?P=q)")

#: Unpinned fetches that predate this guard, each named by (Dockerfile, repo).
#: #1480 found them while writing this file and deliberately did not pin them:
#: they belong to docker/embedding-service, a different image with its own
#: parity question (each pin needs the export it replaces measured against it).
#: An entry that matches no unpinned fetch is an error — a stale entry would
#: silently re-permit the fetch the day someone reverts its pin.
_UNPINNED_ALLOWED: dict[tuple[str, str], str] = {
    ("docker/embedding-service/Dockerfile", "intfloat/multilingual-e5-small"): "embedding-service, pre-#1480",
    ("docker/embedding-service/Dockerfile", "intfloat/multilingual-e5-base"): "embedding-service, pre-#1480",
    ("docker/embedding-service/Dockerfile", "intfloat/multilingual-e5-large"): "embedding-service, pre-#1480",
    (
        "docker/embedding-service/Dockerfile",
        "Xenova/paraphrase-multilingual-MiniLM-L12-v2",
    ): "embedding-service, pre-#1480",
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

    @property
    def pinned(self) -> bool:
        return self.revision is not None and _COMMIT_SHA.fullmatch(self.revision) is not None

    @property
    def label(self) -> str:
        return f"{self.path}:{self.line}:{self.spelling}:{self.repo or '?'}"


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
    code_lines = code.splitlines()
    spans = _instruction_spans(blanked)
    sites: list[FetchSite] = []

    def line_of(offset: int) -> int:
        return code.count("\n", 0, offset) + 1

    def digest_checked(line: int) -> bool:
        for first, last in spans:
            if first <= line <= last:
                instruction = " ".join(code_lines[first - 1 : last])
                return _DIGEST_CHECK.search(instruction) is not None
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


# --------------------------------------------------------------------------
# the property, over the checkout
# --------------------------------------------------------------------------


class TestHuggingFaceFetchesArePinned:
    """Every model a Dockerfile pulls from the Hub names the commit it pulls."""

    def test_the_sweep_finds_fetches_at_all(self) -> None:
        """Without this, every parametrized case below is vacuously absent.

        Pinned AND unpinned are both required to be non-empty on the tree: a
        scanner that lost the ``revision=`` reader would still find sites (all
        unpinned) and one that lost the call reader would find none — either
        collapse must be red here rather than look like a clean tree.
        """
        assert _SITES, "no Hugging Face fetch found in any Dockerfile — the scanner stopped reaching the tree"
        assert any(site.pinned for site in _SITES), (
            "no PINNED fetch found — docker/reranker-service pins two since #1480, so the "
            "`revision=` reader has stopped matching"
        )

    @pytest.mark.parametrize("site", _SITES, ids=lambda site: site.label)
    def test_fetch_names_a_commit(self, site: FetchSite) -> None:
        if (site.path, site.repo or "") in _UNPINNED_ALLOWED:
            pytest.skip(f"allow-listed pre-#1480 fetch: {_UNPINNED_ALLOWED[(site.path, site.repo or '')]}")
        assert site.pinned, (
            f"{site.label}: a Hugging Face fetch without a commit pin (revision={site.revision!r}). "
            "Name the 40-hex commit the model was measured on, e.g. "
            "revision='6f5ff65298512715a1e669753bc754d2bc8f367b' — a branch or tag can be moved "
            "under the image and change its output without failing anything (#1480)."
        )

    @pytest.mark.parametrize("site", [site for site in _SITES if site.pinned], ids=lambda site: site.label)
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

    def test_every_allowance_still_excuses_an_unpinned_fetch(self) -> None:
        unpinned = {(site.path, site.repo or "") for site in _SITES if not site.pinned}
        stale = sorted(set(_UNPINNED_ALLOWED) - unpinned)
        assert not stale, (
            f"allow-list entries that match no unpinned fetch: {stale}. Remove them — a stale "
            "entry would re-permit the fetch the day its pin is reverted."
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


def test_a_comment_line_is_not_a_fetch() -> None:
    """The reranker Dockerfile names ``snapshot_download`` in prose (#1456)."""
    snippet = "# huggingface_hub.snapshot_download('org/model')\n    # hf download org/model\nFROM scratch\n"
    assert fetch_sites(snippet, path="Dockerfile") == []


def test_a_local_path_is_not_a_fetch() -> None:
    snippet = "RUN python -c \"import transformers; transformers.AutoTokenizer.from_pretrained('/model')\"\n"
    assert fetch_sites(snippet, path="Dockerfile") == []
