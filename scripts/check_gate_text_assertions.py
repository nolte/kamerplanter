#!/usr/bin/env python3
"""Refuse a gate that decides about code by matching raw source text.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_gate_text_assertions.py
    python3 scripts/check_gate_text_assertions.py --list   # name every gate file parsed
    python3 scripts/check_gate_text_assertions.py --json   # machine-readable

**The defect class it closes (#1456).** A gate asks "does the tree do X?" and
answers it by searching a file's text for a name. Text carries two kinds of
content — the code, and the prose beside it — and a search that does not
separate them answers about whichever it hits first:

* **presence** — ``"fetchAllFertilizers" in slice_source`` is satisfied by a
  comment head naming the loader. Delete the real call and the gate stays green.
  Measured twice in one week, in ``fertilizersSlice.ts`` and
  ``activitiesSlice.ts`` (#1610), and again in the catalogue registry (#1624).
* **absence** — ``"cec_meq_per_100g" not in migration_source`` is falsified by a
  docstring saying the field is deliberately *not* migrated: red over a sentence,
  green over the defect. A grep in this repository once reported a repaired
  defect as open because the repair's own explanation still named it.

Both directions are one mistake, and it is the most expensive one a gate can
make: a guard that cannot go red is worse than no guard, because it also stops
anyone from looking.

**Why the four known sites were not enough.** #948 repaired two of four routes of
one shape and the other two stayed open for months. Four literal repairs would
have been the same bet. This check enumerates the *class*: every membership,
regex, or occurrence test in every gate file, whatever the name it searches for.

What it enforces
----------------

In a gate file, a value read from a file with ``read_text()`` / ``read()`` must
not reach a text predicate — ``in``/``not in``, ``re.search`` and friends,
``.count()``, ``.find()``, ``.index()``, ``.startswith()``, ``.endswith()`` —
unless it first passes a **reducer** that removes prose
(:func:`source_text.executable_source`, :func:`source_text.is_called`, a
``strip_comments`` helper) or a **parser** that never saw prose as content
(``ast.parse``, ``yaml.safe_load``, ``json.loads``, ``tomllib.loads``).

Taint is followed through assignment, string operations that preserve content
(``.lower()``, ``.splitlines()``, ``.replace()``, f-strings), iteration, and
local helper functions that return it — so moving the read into a fixture does
not move the site out of view. That propagation is the check's own most likely
blind spot and its tests fix each hop.

**The waiver, and why it is not the same trap.** Not every raw-text assertion is
wrong. Some gates assert *about prose on purpose*: that a ``# renovate:`` comment
is present above a pinned image, that a workflow still carries the sentence
recording a deferral, or — in ``test_model_field_renames_have_migrations`` — that
the naive substring search really would be fooled, which is a falsification test
for this very class. Those sites carry::

    # prose-permeable: <why matching prose is the intent here>

A waiver does not hide a site. The site is still found by the parser, still
counted, and still printed on every run; the waiver only records the decision
next to it, the way ``check_utc_calendar_day.py``'s ``# local-clock:`` sites do.
And a waiver that matches no site is an error, so one cannot be left behind
after the assertion it excused is gone.

That is also why the marker being a comment does not make *this* check
prose-satisfiable. Nothing a comment says can create the ``ast.Compare`` node
that puts a site on the list: detection reads the parse tree, where comments do
not exist. The waiver can only annotate a site the tree already proved is there.
``tests/unit/test_gate_text_assertions_check.py`` asserts exactly that, from both
ends — a file whose *only* occurrence of the pattern is a comment yields no
finding, and a file with a real one yields a finding no comment can remove.

Traces to issue #1456 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the gates live. A file matching one of these is in scope; nothing else
#: is, because ordinary production code reading a file is not making a decision
#: about the tree, and neither is a generator like
#: ``scripts/extract_overwintering_templates.py`` — it reads Markdown to produce
#: data, and prose is its subject by construction.
GATE_GLOBS: tuple[str, ...] = (
    "scripts/check_*.py",
    "scripts/ci/check_*.py",
    "scripts/security/check_*.py",
    "scripts/source_text.py",
    "src/backend/tests/unit/guards/**/*.py",
    "src/backend/tests/support/*.py",
    "src/backend/tests/unit/test_*_check.py",
)

#: Floor under the number of gate files parsed, deliberately **below** today's
#: inventory (103 at #1456). A floor equal to the inventory goes red on every
#: legitimate addition or removal and cannot tell "the inventory shrank" from
#: "my parser collapsed" — the correction #1610 had to make. This one answers
#: only the question it can answer: whether the scan still reaches the tree.
MIN_GATE_FILES = 70

#: The marker that records a deliberate assertion about prose.
WAIVER = re.compile(r"#\s*prose-permeable:\s*(?P<reason>\S.*)")

#: Calls whose result is file text.
_READERS = frozenset({"read_text", "read", "read_bytes"})

#: Calls that remove prose, or that parse text into a structure in which prose
#: was never content. Their result is not tainted.
_REDUCERS = frozenset(
    {
        "executable_source",
        "is_called",
        "strip_comments",
        "_strip_comments",
        "without_comments",
    }
)

#: Parsers whose result is a structure, not text — but only when called through
#: their module (``yaml.safe_load``, ``json.loads``, ``ast.parse``). A bare
#: ``load(path)`` is somebody's own helper and says nothing about prose; treating
#: the plain name as a reducer silently cleared a real hop in an early draft,
#: which is what ``test_each_route_from_a_file_to_a_predicate_is_seen`` caught.
_QUALIFIED_REDUCERS = frozenset(
    {"parse", "safe_load", "safe_load_all", "loads", "load"}
)

#: String operations that carry the content through unchanged.
_PRESERVING = frozenset(
    {
        "lower",
        "upper",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "splitlines",
        "split",
        "rsplit",
        "join",
        "casefold",
        "expandtabs",
        "removeprefix",
        "removesuffix",
        "partition",
        "rpartition",
        "format",
        "decode",
    }
)

#: ``re`` functions whose second argument is the searched text.
_RE_FUNCS = frozenset(
    {"search", "match", "findall", "finditer", "fullmatch", "split", "sub", "subn"}
)

#: Methods that answer an occurrence question about a string. Deliberately only
#: ``count``: ``find``/``startswith`` and friends locate a position rather than
#: decide a fact, and ``line.startswith("#")`` is how a comment stripper is
#: *written* — flagging it would make the cure look like the disease.
_TEXT_METHODS = frozenset({"count"})

#: Function names that are themselves reducers. A predicate inside one of these
#: necessarily runs on unreduced text — that is its job — so it is not a site.
_REDUCER_NAMES = re.compile(
    r"strip|comment|uncomment|tokenis|tokeniz|executable_source"
)

#: Needles that are structure rather than content. Counting newlines is line
#: arithmetic, not a claim about what the tree does.
_STRUCTURAL = frozenset({"\n", "\r\n", "\t", " ", ""})

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class GateTextError(RuntimeError):
    """Raised when the check cannot run at all (missing tree, unparsable gate)."""


@dataclass(frozen=True)
class Site:
    """One text predicate applied to text read from a file."""

    path: str
    line: int
    kind: str
    code: str
    reason: str | None

    @property
    def waived(self) -> bool:
        """Whether a ``# prose-permeable:`` marker records this site as deliberate."""
        return self.reason is not None


@dataclass(frozen=True)
class StaleWaiver:
    """A ``# prose-permeable:`` marker with no site to excuse."""

    path: str
    line: int
    reason: str


def gate_files(root: Path, globs: tuple[str, ...] = GATE_GLOBS) -> list[Path]:
    """List every gate file in scope, de-duplicated and ordered.

    Raises:
        GateTextError: If *root* is not a directory.
    """
    if not root.is_dir():
        raise GateTextError(f"repository root does not exist: {root}")
    found: set[Path] = set()
    for pattern in globs:
        found.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(found)


class _Analysis:
    """Taint analysis over one gate module.

    Sources are the file readers; sinks are the text predicates; reducers and
    parsers clear taint. Helper functions that return tainted text are resolved
    to a fixpoint first, so a read moved behind a helper or a pytest fixture is
    still followed to its predicate.
    """

    def __init__(self, tree: ast.Module) -> None:
        self.tree = tree
        self.tainted_helpers: set[str] = set()
        self.tainted_params: dict[str, set[str]] = {}
        self._resolve()

    def _resolve(self) -> None:
        """Propagate taint across function boundaries until nothing changes.

        Three hops, each of which a real gate in this tree takes:

        1. a local helper that **returns** file text makes its callers tainted;
        2. a local helper **called with** tainted text has that parameter
           tainted inside it — without this, moving the predicate one function
           down hides the site;
        3. a pytest **fixture** returning file text taints the test parameter
           named after it, which is how most guards here get at the tree.
        """
        functions = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        by_name = {function.name: function for function in functions}
        for _ in range(len(functions) + 2):
            grew = False
            for function in functions:
                seed = self.tainted_params.get(function.name, set())
                names = self._local_taint(function.body, seed)
                if function.name not in self.tainted_helpers and any(
                    isinstance(node, ast.Return)
                    and node.value is not None
                    and self._tainted(node.value, names)
                    for node in _walk_scope(function.body)
                ):
                    self.tainted_helpers.add(function.name)
                    grew = True
                grew |= self._propagate_into_calls(function.body, names, by_name)
            for function in functions:
                fixtures = {
                    argument.arg
                    for argument in _parameters(function)
                    if argument.arg in self.tainted_helpers
                }
                if fixtures - self.tainted_params.get(function.name, set()):
                    self.tainted_params.setdefault(function.name, set()).update(
                        fixtures
                    )
                    grew = True
            if not grew:
                break

    def _propagate_into_calls(
        self,
        body: list[ast.stmt],
        names: set[str],
        by_name: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> bool:
        """Taint the parameters of local functions called with tainted text."""
        grew = False
        for node in _walk_scope(body):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            callee = by_name.get(node.func.id)
            if callee is None:
                continue
            parameters = [argument.arg for argument in _parameters(callee)]
            reached: set[str] = set()
            for index, argument in enumerate(node.args):
                if self._tainted(argument, names) and index < len(parameters):
                    reached.add(parameters[index])
            for keyword in node.keywords:
                if keyword.arg and self._tainted(keyword.value, names):
                    reached.add(keyword.arg)
            if reached - self.tainted_params.get(callee.name, set()):
                self.tainted_params.setdefault(callee.name, set()).update(reached)
                grew = True
        return grew

    def _local_taint(self, body: list[ast.stmt], names: set[str]) -> set[str]:
        """Names bound to file text within *body*, not descending into nested scopes.

        Descending would merge every function's locals into one namespace, and a
        name tainted in one function would then be read as tainted in the next —
        the scan reporting sites that are not there, and (worse) clearing ones
        that are. Each ``def`` is analysed as its own scope by :meth:`sites`.
        """
        names = set(names)
        nodes = list(_walk_scope(body))
        # To a fixpoint rather than in one pass: the walk has no document order,
        # so a binding seen after its use would otherwise be missed — and a
        # missed binding is a site this check goes quiet on.
        for _ in range(len(nodes) + 1):
            before = len(names)
            self._bind(nodes, names)
            if len(names) == before:
                break
        return names

    def _bind(self, nodes: list[ast.AST], names: set[str]) -> None:
        """One pass: add every name *nodes* binds to tainted text."""
        for node in nodes:
            if isinstance(node, ast.Assign) and self._tainted(node.value, names):
                names.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
            elif isinstance(node, ast.AnnAssign | ast.AugAssign):
                if (
                    node.value is not None
                    and isinstance(node.target, ast.Name)
                    and self._tainted(node.value, names)
                ):
                    names.add(node.target.id)
            elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
                target = node.target
                if self._tainted(node.iter, names) and isinstance(target, ast.Name):
                    names.add(target.id)

    def _tainted(self, node: ast.expr, names: set[str]) -> bool:
        """Whether *node* evaluates to text that came out of a file unreduced."""
        if isinstance(node, ast.Name):
            return node.id in names
        if isinstance(node, ast.Subscript):
            return self._tainted(node.value, names)
        if isinstance(node, ast.BinOp):
            return self._tainted(node.left, names) or self._tainted(node.right, names)
        if isinstance(node, ast.IfExp):
            # `return rest[:n] if following else rest` — a real shape in
            # `scripts/ci/check_renovate_dashboard.py`, and the hop an earlier
            # draft of this check did not follow, which took a whole module's
            # sites off the list without saying so.
            return self._tainted(node.body, names) or self._tainted(node.orelse, names)
        if isinstance(node, ast.BoolOp):
            return any(self._tainted(value, names) for value in node.values)
        if isinstance(node, ast.NamedExpr | ast.Await | ast.Starred):
            return self._tainted(node.value, names)
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            return any(self._tainted(element, names) for element in node.elts)
        if isinstance(node, ast.JoinedStr):
            return any(self._tainted(value, names) for value in node.values)
        if isinstance(node, ast.FormattedValue):
            return self._tainted(node.value, names)
        if isinstance(node, ast.Attribute):
            return node.attr in _PRESERVING and self._tainted(node.value, names)
        if isinstance(node, ast.Call):
            function = node.func
            name = (
                function.attr
                if isinstance(function, ast.Attribute)
                else function.id
                if isinstance(function, ast.Name)
                else ""
            )
            if name in _REDUCERS:
                return False
            if isinstance(function, ast.Attribute) and name in _QUALIFIED_REDUCERS:
                return False
            if name in _READERS:
                return True
            if name in _PRESERVING and isinstance(function, ast.Attribute):
                return self._tainted(function.value, names)
            return (
                isinstance(function, ast.Name) and function.id in self.tainted_helpers
            )
        return False

    def sites(self) -> list[tuple[int, str, str]]:
        """Every text predicate reached by file text, as ``(line, kind, code)``."""
        found: list[tuple[int, str, str]] = []
        for body, seed in self._scopes():
            names = self._local_taint(body, seed)
            for node in _walk_scope(body):
                found.extend(self._sinks(node, names))
        return sorted(set(found))

    def _scopes(self) -> list[tuple[list[ast.stmt], set[str]]]:
        """The module body and every function body, each as its own namespace."""
        scopes: list[tuple[list[ast.stmt], set[str]]] = [(self.tree.body, set())]
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if _REDUCER_NAMES.search(node.name):
                    continue
                scopes.append((node.body, self.tainted_params.get(node.name, set())))
        return scopes

    def _sinks(self, node: ast.AST, names: set[str]) -> list[tuple[int, str, str]]:
        """Text predicates applied to tainted text at *node*."""
        found: list[tuple[int, str, str]] = []
        if isinstance(node, ast.Compare):
            for operator, comparator in zip(node.ops, node.comparators, strict=True):
                if isinstance(operator, ast.In | ast.NotIn) and self._tainted(
                    comparator, names
                ):
                    found.append((node.lineno, "membership", _render(node)))
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Attribute):
                is_re = (
                    function.attr in _RE_FUNCS
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "re"
                )
                if is_re and len(node.args) >= 2 and self._tainted(node.args[1], names):
                    found.append((node.lineno, "regex", _render(node)))
                elif function.attr in _TEXT_METHODS and self._tainted(
                    function.value, names
                ):
                    needle = node.args[0] if node.args else None
                    structural = (
                        isinstance(needle, ast.Constant)
                        and isinstance(needle.value, str)
                        and not needle.value.strip()
                    )
                    if not structural:
                        found.append((node.lineno, function.attr, _render(node)))
        return found


#: Node types that open a namespace of their own.
_NESTED_SCOPE = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def _parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    """Every named parameter of *function*, in call order."""
    arguments = function.args
    return [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]


def _walk_scope(body: list[ast.stmt]):
    """Walk *body* without entering a nested function or class definition.

    ``ast.walk`` has no notion of scope, so a module-level walk sees every
    function's locals as if they were its own. Everything here depends on
    keeping those apart.
    """
    queue: list[ast.AST] = list(body)
    while queue:
        node = queue.pop()
        yield node
        if isinstance(node, _NESTED_SCOPE):
            # Yielded, never entered — including when it is a member of *body*
            # itself, which is the case at module level and the one that made an
            # early draft merge every function's locals into one namespace.
            continue
        queue.extend(ast.iter_child_nodes(node))


def _render(node: ast.AST) -> str:
    """One-line rendering of a node for the report."""
    text = " ".join(ast.unparse(node).split())
    return text if len(text) <= 96 else text[:93] + "..."


def _comments(text: str) -> tuple[dict[int, str], set[int]]:
    """Every ``# prose-permeable:`` marker by line, and every comment-only line.

    Read from the **comment tokens**, not from the lines. A line scan would find
    the marker quoted in a docstring — this module's own docstring quotes it
    three times — and read documentation as a decision. That is the same mistake
    one file over, so it is not made here: :mod:`tokenize` knows what a comment
    is, and a mention inside a string is not one.
    """
    markers: dict[int, str] = {}
    comment_lines: set[int] = set()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):  # pragma: no cover
        return markers, comment_lines
    lines = text.splitlines()
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        row = token.start[0]
        if lines[row - 1].lstrip().startswith("#"):
            comment_lines.add(row)
        match = WAIVER.search(token.string)
        if match:
            markers[row] = match.group("reason").strip()
    return markers, comment_lines


def _attach(
    sites: list[tuple[int, str, str]],
    markers: dict[int, str],
    comment_lines: set[int],
    relative: str,
) -> tuple[list[Site], list[StaleWaiver]]:
    """Pair each site with the marker attached to it.

    A marker counts when it sits on the site's own line, anywhere in the unbroken
    block of comment lines directly above it, or on the line below. The block
    rather than a single line, because a reason worth writing rarely fits in the
    line budget, and a reason cut to fit is a reason nobody can argue with.
    """
    used: set[int] = set()
    attached: list[Site] = []
    for line, kind, code in sites:
        reason = None
        for candidate in _candidate_lines(line, comment_lines):
            if candidate in markers:
                reason = markers[candidate]
                used.add(candidate)
                break
        attached.append(Site(relative, line, kind, code, reason))
    stale = [
        StaleWaiver(relative, line, reason)
        for line, reason in sorted(markers.items())
        if line not in used
    ]
    return attached, stale


def _candidate_lines(line: int, comment_lines: set[int]) -> list[int]:
    """Lines a marker for the site at *line* may sit on, nearest first."""
    candidates = [line]
    above = line - 1
    while above in comment_lines:
        candidates.append(above)
        above -= 1
    # The block above is consulted BEFORE the line below, so two waived sites in
    # a row cannot steal each other's marker: the second site's own block ends at
    # the first site's code line, and reaching downwards first would hand it the
    # marker written for the site after it.
    candidates.append(line + 1)
    return candidates


@dataclass
class Measurement:
    """What the check measured across the whole gate inventory."""

    files: list[str]
    sites: list[Site]
    stale: list[StaleWaiver]

    @property
    def unwaived(self) -> list[Site]:
        """Sites with no recorded reason. These fail."""
        return [site for site in self.sites if not site.waived]

    @property
    def failed(self) -> bool:
        """Whether the gate is red."""
        return (
            bool(self.unwaived) or bool(self.stale) or len(self.files) < MIN_GATE_FILES
        )


def measure(root: Path, globs: tuple[str, ...] = GATE_GLOBS) -> Measurement:
    """Parse every gate file and locate its raw-source-text predicates.

    Args:
        root: Repository root.
        globs: Gate file patterns (injectable for this check's own tests).

    Returns:
        The measurement.

    Raises:
        GateTextError: If the tree is missing or a gate file cannot be parsed.
    """
    files: list[str] = []
    sites: list[Site] = []
    stale: list[StaleWaiver] = []
    for path in gate_files(root, globs):
        relative = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(path))
        except (OSError, SyntaxError, ValueError) as exc:
            raise GateTextError(f"cannot parse {relative}: {exc}") from exc
        files.append(relative)
        markers, comment_lines = _comments(text)
        found, left_over = _attach(_Analysis(tree).sites(), markers, comment_lines, relative)
        sites.extend(found)
        stale.extend(left_over)
    return Measurement(files=files, sites=sites, stale=stale)


def report(measurement: Measurement, list_files: bool) -> int:
    """Print the measurement and return the process exit code."""
    waived = [site for site in measurement.sites if site.waived]
    print("Gate predicates applied to raw source text (#1456)")
    print()
    print(
        f"  gate files parsed      {len(measurement.files):>4}  (floor {MIN_GATE_FILES})"
    )
    print(f"  text predicates found  {len(measurement.sites):>4}")
    print(f"  recorded as deliberate {len(waived):>4}")
    print(f"  unrecorded             {len(measurement.unwaived):>4}")
    print()

    if list_files:
        for name in measurement.files:
            print(f"  parsed  {name}")
        print()

    if waived:
        print("Deliberately matching prose — printed every run, so the list stays one")
        print("somebody reads rather than a suppression:")
        for site in waived:
            print(f"  {site.path}:{site.line}  [{site.kind}]  {site.reason}")
        print()

    if not measurement.failed:
        print("OK — every gate decides about code from code.")
        return EXIT_OK

    if len(measurement.files) < MIN_GATE_FILES:
        print(
            f"FAILED — only {len(measurement.files)} gate file(s) parsed, floor is "
            f"{MIN_GATE_FILES}.\n"
            "  The scan is not reaching the tree. Either GATE_GLOBS no longer matches\n"
            "  where the gates live, or this check is being run from the wrong root —\n"
            "  both make every 'OK' below meaningless."
        )
        print()

    if measurement.unwaived:
        print(
            f"FAILED — {len(measurement.unwaived)} predicate(s) over unreduced file text:\n"
        )
        for site in measurement.unwaived:
            print(f"  {site.path}:{site.line}  [{site.kind}]")
            print(f"    {site.code}")
        print(
            "\n  Text read from a file carries the code AND the prose beside it. A name\n"
            "  found in a comment head satisfies a presence test; a name explained in a\n"
            "  docstring falsifies an absence test. Either way the gate answers about\n"
            "  the wrong half and cannot go red on the defect it was built for.\n"
            "\n  Reduce the text before matching:\n"
            "      from source_text import executable_source, is_called\n"
            "      is_called('fetchAllFertilizers', source, language='typescript')\n"
            "      'X' in executable_source(source, language='python')\n"
            "  or parse it (ast.parse, yaml.safe_load, json.loads, tomllib.loads).\n"
            "\n  If matching prose IS the intent — asserting a `# renovate:` comment is\n"
            "  there, or proving the naive form would be fooled — record it beside the\n"
            "  assertion:\n"
            "      # prose-permeable: <why prose is the subject here>"
        )
        print()

    if measurement.stale:
        print(f"FAILED — {len(measurement.stale)} waiver(s) excusing nothing:\n")
        for waiver in measurement.stale:
            print(f"  {waiver.path}:{waiver.line}  {waiver.reason}")
        print(
            "\n  A `# prose-permeable:` marker must sit on the line of a predicate this\n"
            "  check found, in the comment block directly above it, or on the line below.\n"
            "  One left behind after its assertion changed reads as a decision nobody took."
        )
        print()
    return EXIT_DEFECTS


def main(argv: list[str] | None = None) -> int:
    """Run the raw-source-text gate check."""
    parser = argparse.ArgumentParser(
        prog="check_gate_text_assertions.py",
        description=(
            "Refuse a gate that decides about code by matching raw source text, in "
            "which a comment can satisfy a presence test and a docstring can falsify "
            "an absence test."
        ),
    )
    parser.add_argument(
        "--root", metavar="PATH", help=f"repository root (default: {REPO_ROOT})"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_files",
        help="name every gate file parsed",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the measurement as JSON"
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else REPO_ROOT
    try:
        measurement = measure(root)
    except GateTextError as exc:
        print(f"check_gate_text_assertions: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(
            json.dumps(
                {
                    "files": len(measurement.files),
                    "floor": MIN_GATE_FILES,
                    "sites": [
                        {
                            "path": site.path,
                            "line": site.line,
                            "kind": site.kind,
                            "code": site.code,
                            "reason": site.reason,
                        }
                        for site in measurement.sites
                    ],
                    "stale_waivers": [
                        {"path": item.path, "line": item.line, "reason": item.reason}
                        for item in measurement.stale
                    ],
                    "failed": measurement.failed,
                },
                indent=2,
            )
        )
        # Same predicate as the human report, so the two modes cannot disagree.
        return EXIT_DEFECTS if measurement.failed else EXIT_OK

    return report(measurement, args.list_files)


if __name__ == "__main__":
    raise SystemExit(main())
