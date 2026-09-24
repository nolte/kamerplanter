"""#1750 — every host port this repository publishes binds to the loopback interface.

**The defect this is written against, measured 2026-09-25 on develop
47771d74d.** ``docker-compose.yml`` published ArangoDB ``8529``, Valkey
``6379``, pgvector ``5433``, Ollama ``11434``, TimescaleDB ``5432``, the backend
``8000`` and the frontend ``8080`` as bare ``"<host>:<container>"`` mappings.
Docker binds such a mapping on EVERY interface of the host, so on a workstation
on a shared network each of them was reachable from other machines — the data
stores with the ``changeme`` defaults of ``.env.example``, Ollama and the
light-mode app with no authentication at all. ``docker-compose.release.yml``,
the file the permanent-operation guide has end users run on a home server, did
the same for six services. #1725 had bound only the reranker; #1739's guard
(``test_ml_sidecar_limits.py``) asserted its hardening flags but never the
bind, so even that one fix had no guard.

**What is asserted, over which selector.** Three spellings publish a host port,
and each is read from every file that can carry it — never from a list of the
files the defect was found in:

* a Compose ``ports:`` entry, short syntax (``"8529:8529"``,
  ``"127.0.0.1::8529"``, ``"[::1]:80:80"``, ranges, ``/udp``) or long syntax
  (``published:`` / ``host_ip:``), in every tracked file that is a Compose file
  by name OR by shape, plus ``network_mode: host``, which puts every listener of
  the container on every host interface;
* a GitHub Actions ``services:`` / ``container:`` ``ports:`` entry (the runner
  hands it to ``docker create -p``);
* a ``docker run`` / ``docker compose run`` ``-p`` / ``--publish`` /
  ``-P`` / ``--publish-all`` flag in any tracked script, config or document —
  a copy-paste command in the docs publishes a port as surely as a Compose file;
* the same flags in a Python argv sequence (``["docker", "run", "-p", …]`` or a
  call to a ``*docker*`` helper), read from the AST, an f-string rendered with
  its placeholders so ``f"127.0.0.1::{port}"`` keeps its literal host.

**What it cannot see**, named so nobody reads its silence as coverage: a publish
assembled at runtime (a variable holding ``"-p"``, a Docker SDK ``ports=``
mapping, testcontainers), and a ``docker run`` whose ``run`` and ``-p`` sit in
different strings of a shell script (a function wrapping ``docker run "$@"``).
None exists in this checkout (``git grep`` for ``ports=``, ``testcontainers``,
``DockerContainer(`` on 2026-09-25); a new one needs its own reading here.
A kind cluster's ``extraPortMappings`` (``kind-config.yaml``, no
``listenAddress`` → ``0.0.0.0``) is a publish by another tool and is tracked
as #1756, not read here.

Each entry must name a loopback host address (``127.0.0.0/8`` or ``::1``).
Environment interpolation is resolved the way Compose resolves it with the
variable unset (``${VAR:-default}`` → ``default``), so ``"${PORT:-8000}:8000"``
is the unbound ``8000:8000`` it starts as. A host address that is itself
interpolated can be widened by whoever sets the variable; it is accepted only
when its default is loopback AND the entry is named in :data:`ALLOWED_OVERRIDABLE`
with the reason remote reach is wanted.

**Fail closed.** A spelling this module cannot resolve — an interpolation
without a default, ``${VAR:?…}``, a nested default, a bare IPv6 address, a
hostname instead of an address, an unknown long-syntax key, a ``ports:`` value
that is not a list — is a failure that names the spelling, never a skip.

**Red first.** Run against develop 47771d74d this module failed with the 13
unbound Compose entries above, the ``--publish 8080:80`` in
``.taskfiles/mcp.yaml`` and every ``docker run -p 8529:8529`` the integration
tests' docstrings tell a developer to run (with ``rootpassword``).
"""

from __future__ import annotations

import ast
import ipaddress
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("repository root not found", allow_module_level=True)


# ------------------------------------------------------------------ allow-lists

# Entries whose host address is an interpolation. Keyed (file, service, the
# entry exactly as written): a count would let a second, unreviewed entry take
# the place of a removed one. Each still has to default to loopback.
_FRONT_DOOR_WEB = (
    "The web UI is the application's one front door. It stays on 127.0.0.1 unless the operator sets "
    "KAMERPLANTER_BIND_ADDRESS (e.g. 0.0.0.0) to open it to phones and tablets on the home network — "
    "the documented 'Accessing from other devices' workflow (docs/*/deployment/docker-dauerbetrieb.md)."
)
_FRONT_DOOR_API = (
    "The API port is what a Home Assistant host elsewhere on the network addresses "
    "(docs/*/guides/home-assistant-integration.md, 'http://raspberry:8000'). Same opt-in as the web UI: "
    "127.0.0.1 unless the operator sets KAMERPLANTER_BIND_ADDRESS."
)
ALLOWED_OVERRIDABLE: dict[tuple[str, str, str], str] = {
    ("docker-compose.yml", "frontend", "${KAMERPLANTER_BIND_ADDRESS:-127.0.0.1}:8080:8080"): _FRONT_DOOR_WEB,
    ("docker-compose.yml", "backend", "${KAMERPLANTER_BIND_ADDRESS:-127.0.0.1}:8000:8000"): _FRONT_DOOR_API,
    ("docker-compose.release.yml", "frontend", "${KAMERPLANTER_BIND_ADDRESS:-127.0.0.1}:8080:8080"): _FRONT_DOOR_WEB,
    ("docker-compose.release.yml", "backend", "${KAMERPLANTER_BIND_ADDRESS:-127.0.0.1}:8000:8000"): _FRONT_DOOR_API,
}

# Publishes that stay on every interface. Keyed (file, where, the entry as
# written).
_GITHUB_HOSTED_RUNNER = (
    "Runs on a GitHub-hosted runner: a single-use VM that accepts no inbound connection from any other host, "
    "so there is no network the port could be exposed to. Binding it would change the job definition and "
    "invalidate the recorded lane manifest (.github/lane-inputs/, job_spec_sha256) for no reduction in exposure."
)
ALLOWED_UNBOUND: dict[tuple[str, str, str], str] = {
    (".github/workflows/backend-guards.yml", "jobs.integration.services.arangodb", "8529:8529"): _GITHUB_HOSTED_RUNNER,
    (".github/workflows/lane-inputs.yml", "docker run", "8529:8529"): _GITHUB_HOSTED_RUNNER,
}


# ------------------------------------------------------------------ parsing


class _StringLoader(yaml.SafeLoader):
    """SafeLoader that keeps every plain scalar but booleans and null a string.

    PyYAML resolves YAML 1.1: an unquoted ``8080:80`` is the sexagesimal
    integer 484880, not the string Compose (YAML 1.2) reads. Dropping the int
    and float resolvers makes ``- 8080:80`` and ``- 8080`` arrive as written.
    Compose's merge tags (``!override``, ``!reset``) load as their plain node.
    """


_NUMBER_TAGS = ("tag:yaml.org,2002:int", "tag:yaml.org,2002:float")
_StringLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag not in _NUMBER_TAGS]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _construct_plain(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)


for _tag in ("!override", "!reset"):
    _StringLoader.add_constructor(_tag, _construct_plain)


def load_yaml(text: str) -> Any:
    return yaml.load(text, Loader=_StringLoader)  # noqa: S506 — SafeLoader subclass


_INTERPOLATION = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:(?P<op>:-|-|:\?|\?|:\+|\+)(?P<word>[^${}]*))?\}")
_BARE_VARIABLE = re.compile(r"\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<op>)(?P<word>)")


class UnparseableError(ValueError):
    """A spelling this guard cannot resolve — reported as a failure, never skipped."""


def resolve(text: str, placeholder: str | None = None) -> tuple[str, bool]:
    """Resolve Compose / shell interpolation as it resolves with every variable unset.

    Returns the resolved text and whether anything was interpolated. A variable
    with a default (``${VAR:-x}``, ``${VAR-x}``) resolves to it. Any other
    variable — no default, ``:?``/``?``, ``:+``/``+``, a bare ``$VAR`` — has no
    value this guard can know: it becomes ``placeholder`` when the caller passes
    one (a PORT field, where the value cannot change which interface is bound)
    and raises :class:`UnparseableError` otherwise (a HOST field). Anything left over
    (a nested default) raises either way.
    """
    interpolated = False
    text = text.replace("$$", "\0")

    def substitute(match: re.Match[str]) -> str:
        nonlocal interpolated
        interpolated = True
        if match.group("op") in (":-", "-"):
            return match.group("word")
        if placeholder is None:
            raise UnparseableError(f"interpolation {match.group(0)!r} has no default to resolve")
        return placeholder

    resolved = _INTERPOLATION.sub(substitute, text)
    resolved = _BARE_VARIABLE.sub(substitute, resolved)
    if "$" in resolved or "{" in resolved or "}" in resolved:
        raise UnparseableError(f"interpolation left unresolved in {text!r}")
    return resolved.replace("\0", "$"), interpolated


_PORT = r"\d{1,5}"
_PORT_OR_RANGE = re.compile(rf"^{_PORT}(?:-{_PORT})?$")


def _check_ports(*values: str) -> None:
    for value in values:
        if not _PORT_OR_RANGE.match(value):
            raise UnparseableError(f"{value!r} is not a port or a port range")
        for port in value.split("-"):
            if not 1 <= int(port) <= 65535:
                raise UnparseableError(f"{port} is not a port number")


def _host_address(text: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        return ipaddress.ip_address(text)
    except ValueError as exc:
        raise UnparseableError(f"host address {text!r} is not an IP address") from exc


@dataclass(frozen=True)
class Publish:
    """One host-port publication and where it was written."""

    path: str
    where: str
    raw: str


@dataclass(frozen=True)
class Verdict:
    bound: bool
    host_ip_interpolated: bool
    problem: str


def short_syntax_host(spec: str) -> tuple[str | None, bool]:
    """The host address of a ``docker -p`` / Compose short-syntax spec, or None when it names none.

    Returns ``(host, host_was_interpolated)``.
    """
    body = spec.strip()
    if not body:
        raise UnparseableError("empty port spec")
    host_part = None
    if body.startswith("["):
        close = body.find("]")
        if close == -1 or body[close + 1 : close + 2] != ":":
            raise UnparseableError(f"{spec!r}: unterminated IPv6 host")
        host_part, rest = body[1:close], body[close + 2 :]
        mapping = rest
    else:
        mapping = body
    # PORT fields: an unknown value cannot move the bind, so it resolves to a
    # placeholder port; the HOST field is resolved separately, without one.
    resolved, _ = resolve(mapping, placeholder="1")
    resolved = re.sub(r"/(tcp|udp|sctp)$", "", resolved)
    if host_part is not None:
        parts = resolved.split(":")
        if len(parts) != 2:
            raise UnparseableError(f"{spec!r}: expected [host]:published:target")
        _check_ports(*(p for p in parts if p))
        host_resolved, host_interpolated = resolve(host_part)
        return host_resolved, host_interpolated
    parts = resolved.split(":")
    if len(parts) in (1, 2):
        _check_ports(*(p for p in parts if p))
        return None, False
    if len(parts) == 3:
        _check_ports(*(p for p in parts[1:] if p))
        # The host field on its own, with no placeholder: an unknown host fails closed.
        host_resolved, host_interpolated = resolve(_raw_host_field(mapping))
        return host_resolved, host_interpolated
    raise UnparseableError(f"{spec!r}: an IPv6 host address must be written in brackets")


def _raw_host_field(mapping: str) -> str:
    """The unresolved text before the second-to-last colon outside ``${…}``."""
    depth = 0
    colons: list[int] = []
    for index, char in enumerate(mapping):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == ":" and depth == 0:
            colons.append(index)
    if len(colons) < 2:
        raise UnparseableError(f"{mapping!r}: cannot locate the host field")
    return mapping[: colons[-2]]


def judge_host(host: str | None, host_interpolated: bool) -> Verdict:
    if host is None:
        return Verdict(False, False, "names no host address, so Docker binds every interface")
    if not host:
        return Verdict(False, host_interpolated, "host address is empty, so Docker binds every interface")
    address = _host_address(host)
    if not address.is_loopback:
        return Verdict(False, host_interpolated, f"host address {host} is not loopback")
    return Verdict(True, host_interpolated, "")


def judge_short(spec: str) -> Verdict:
    host, interpolated = short_syntax_host(spec)
    return judge_host(host, interpolated)


_LONG_KEYS = {"target", "published", "host_ip", "protocol", "mode", "app_protocol", "name"}


def judge_long(entry: dict[str, Any]) -> Verdict:
    unknown = set(entry) - _LONG_KEYS
    if unknown:
        raise UnparseableError(f"long-syntax keys this guard does not know: {sorted(unknown)}")
    if "target" not in entry:
        raise UnparseableError("long-syntax entry without target")
    _check_ports(resolve(str(entry["target"]), placeholder="1")[0])
    if entry.get("published") not in (None, ""):
        _check_ports(resolve(str(entry["published"]), placeholder="1")[0])
    if "host_ip" not in entry:
        return Verdict(False, False, "long-syntax entry without host_ip, so Docker binds every interface")
    host, interpolated = resolve(str(entry["host_ip"]))
    return judge_host(host, interpolated)


def judge_entry(entry: Any) -> Verdict:
    if isinstance(entry, str):
        return judge_short(entry)
    if isinstance(entry, dict):
        return judge_long(entry)
    raise UnparseableError(f"ports entry of type {type(entry).__name__}: {entry!r}")


def render(entry: Any) -> str:
    if isinstance(entry, dict):
        return ",".join(f"{key}={entry[key]}" for key in sorted(entry))
    return str(entry)


# ------------------------------------------------------------------ discovery


_SKIP_PARTS = {"node_modules", ".git", ".venv", "venv", "__pycache__"}


def tracked_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)  # noqa: S603, S607
        entries = [e.decode("utf-8", "surrogateescape") for e in completed.stdout.split(b"\0") if e]
    except OSError, subprocess.CalledProcessError:  # pragma: no cover — outside a checkout
        entries = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    return sorted(e for e in entries if not _SKIP_PARTS.intersection(Path(e).parts) and (root / e).is_file())


_COMPOSE_NAME = re.compile(r"(^|/)(docker-)?compose[^/]*\.ya?ml$|\.compose\.ya?ml$")


def _looks_like_compose(document: Any) -> bool:
    if not isinstance(document, dict) or "jobs" in document:
        return False
    services = document.get("services")
    if not isinstance(services, dict) or not services:
        return False
    return any(
        isinstance(service, dict) and ({"image", "build", "ports", "network_mode"} & set(service))
        for service in services.values()
    )


@dataclass(frozen=True)
class YamlFile:
    path: str
    document: Any
    error: str


def yaml_files(root: Path, tracked: list[str]) -> list[YamlFile]:
    result = []
    for path in tracked:
        if not path.endswith((".yml", ".yaml")):
            continue
        try:
            document = load_yaml((root / path).read_text(encoding="utf-8"))
            result.append(YamlFile(path, document, ""))
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            result.append(YamlFile(path, None, f"{type(exc).__name__}: {exc}"))
    return result


def compose_files(files: list[YamlFile]) -> tuple[list[YamlFile], list[str]]:
    """Compose files by name or by shape, and the name-matched ones that do not parse."""
    found, broken = [], []
    for item in files:
        by_name = bool(_COMPOSE_NAME.search(item.path))
        if item.error:
            if by_name:
                broken.append(f"{item.path}: {item.error}")
            continue
        if by_name or _looks_like_compose(item.document):
            found.append(item)
    return found, broken


# ------------------------------------------------------------------ sweeps


_INTERPOLATED_HOST = "host address is an interpolation (widenable by the environment)"


@dataclass(frozen=True)
class Finding:
    path: str
    where: str
    raw: str
    problem: str

    def __str__(self) -> str:
        return f"{self.path} [{self.where}] {self.raw!r}: {self.problem}"


def _judge_listing(path: str, where: str, ports: Any, overridable_ok: bool) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()
    if ports is None:
        return findings, seen
    if not isinstance(ports, list):
        findings.append(Finding(path, where, render(ports), "ports: is not a list — unparseable"))
        return findings, seen
    for entry in ports:
        raw = render(entry)
        key = (path, where, raw)
        try:
            verdict = judge_entry(entry)
        except UnparseableError as exc:
            findings.append(Finding(path, where, raw, f"unparseable: {exc}"))
            continue
        if not verdict.bound:
            if key in ALLOWED_UNBOUND:
                seen.add(key)
                continue
            findings.append(Finding(path, where, raw, verdict.problem))
        elif verdict.host_ip_interpolated:
            if overridable_ok and key in ALLOWED_OVERRIDABLE:
                seen.add(key)
                continue
            findings.append(Finding(path, where, raw, _INTERPOLATED_HOST + " and not in ALLOWED_OVERRIDABLE"))
    return findings, seen


def sweep_compose(files: list[YamlFile]) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    seen: set = set()
    for item in files:
        services = item.document.get("services") if isinstance(item.document, dict) else None
        if services is None:
            continue
        if not isinstance(services, dict):
            findings.append(Finding(item.path, "services", render(services), "services: is not a mapping"))
            continue
        for name, service in services.items():
            if not isinstance(service, dict):
                continue
            if str(service.get("network_mode", "")).strip() == "host":
                findings.append(
                    Finding(item.path, str(name), "network_mode: host", "every listener binds every host interface")
                )
            # Keyed by service name alone: that is how ALLOWED_OVERRIDABLE names it.
            found, keys = _judge_listing(item.path, str(name), service.get("ports"), overridable_ok=True)
            findings += found
            seen |= keys
    return findings, seen


def sweep_workflows(files: list[YamlFile]) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    seen: set = set()
    for item in files:
        if not item.path.startswith(".github/") or not isinstance(item.document, dict):
            continue
        jobs = item.document.get("jobs")
        if not isinstance(jobs, dict):
            continue
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            containers: list[tuple[str, Any]] = []
            if isinstance(job.get("container"), dict):
                containers.append((f"jobs.{job_name}.container", job["container"]))
            for service_name, service in (job.get("services") or {}).items():
                if isinstance(service, dict):
                    containers.append((f"jobs.{job_name}.services.{service_name}", service))
            for where, container in containers:
                found, keys = _judge_listing(item.path, where, container.get("ports"), overridable_ok=False)
                findings += found
                seen |= keys
    return findings, seen


_TEXT_SUFFIXES = (
    *(".sh", ".bash", ".py", ".yml", ".yaml", ".md", ".toml"),
    *(".cfg", ".ini", ".txt", ".j2", ".env", ".example"),
)
_TEXT_NAMES = re.compile(r"(^|/)(Taskfile[^/]*|Makefile|Dockerfile[^/]*|Justfile)$")
_DOCKER_RUN = re.compile(r"(?<![\w-])docker(?:-compose)?(?![\w-])(?P<middle>.*?)(?<![\w-])run(?![\w-])(?P<tail>.*)")
_SHELL_END = re.compile(r"&&|\|\||;|(?<![|])\|(?![|])")
_PUBLISH = re.compile(r"(?<!\S)(?:--publish|-[dit]*p)(?:=|\s+)(?P<spec>\S+)")
_PUBLISH_ALL = re.compile(r"(?<!\S)(?:--publish-all|-[dit]*P[dit]*)(?=\s|$)")


def logical_lines(text: str) -> list[tuple[int, str]]:
    """Physical lines joined across trailing backslashes (also ``\\\\`` inside a Python string)."""
    lines = text.splitlines()
    result: list[tuple[int, str]] = []
    buffer, start = "", 0
    for number, line in enumerate(lines, start=1):
        if not buffer:
            start = number
        stripped = line.rstrip()
        continued = re.search(r"\\{1,2}$", stripped)
        buffer += (stripped[: continued.start()] if continued else line) + " "
        if not continued:
            result.append((start, buffer))
            buffer = ""
    if buffer:
        result.append((start, buffer))
    return result


def _clean_spec(spec: str) -> str:
    return spec.strip("\"'`),;")


def cli_publishes(path: str, text: str) -> list[tuple[int, str]]:
    """Every ``docker [compose] run`` publish flag in ``text``: (line, spec) — ``-P`` as spec ``-P``."""
    found = []
    for number, line in logical_lines(text):
        match = _DOCKER_RUN.search(line)
        if not match:
            continue
        tail = _SHELL_END.split(match.group("tail"), maxsplit=1)[0]
        for publish in _PUBLISH.finditer(tail):
            found.append((number, _clean_spec(publish.group("spec"))))
        for _ in _PUBLISH_ALL.finditer(tail):
            found.append((number, "-P"))
    return found


def _argv_string(node: ast.expr) -> str | None:
    """A constant string, or an f-string with each placeholder rendered as ``1``; else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        rendered = ""
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                rendered += part.value
            else:
                rendered += "1"
        return rendered
    return None


def _callee_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def argv_publishes(source: str) -> list[tuple[int, str]]:
    """Every publish flag in a Python argv sequence that runs a container: (line, spec).

    A sequence is a list/tuple literal or a call's positional arguments; it runs
    a container when it holds ``"run"`` and either a ``"docker"`` element or the
    callee's name contains ``docker``. A spec that is not a literal is reported
    as ``<non-literal>`` so the caller fails closed on it.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.List | ast.Tuple):
            elements, docker_callee = list(node.elts), False
        elif isinstance(node, ast.Call):
            elements, docker_callee = list(node.args), "docker" in _callee_name(node).lower()
        else:
            continue
        strings = [_argv_string(element) for element in elements]
        if "run" not in strings or not (docker_callee or "docker" in strings):
            continue
        after_run = strings.index("run") + 1
        for index in range(after_run, len(strings)):
            value = strings[index]
            if value in ("-p", "--publish"):
                spec = strings[index + 1] if index + 1 < len(strings) else None
                found.append((elements[index].lineno, spec if spec is not None else "<non-literal>"))
            elif value is not None and value.startswith("--publish="):
                found.append((elements[index].lineno, value.partition("=")[2]))
            elif value in ("-P", "--publish-all"):
                found.append((elements[index].lineno, "-P"))
    return found


def sweep_cli(root: Path, tracked: list[str]) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    seen: set = set()
    for path in tracked:
        if not (path.endswith(_TEXT_SUFFIXES) or _TEXT_NAMES.search(path)):
            continue
        try:
            text = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # prose-permeable: cheap pre-filter; the subject IS prose too — a doc command publishes a port
        if "docker" not in text:
            continue
        publishes = cli_publishes(path, text)
        if path.endswith(".py"):
            try:
                publishes += argv_publishes(text)
            except SyntaxError as exc:
                findings.append(Finding(path, "ast", "", f"unparseable Python: {exc}"))
        for number, spec in publishes:
            key = (path, "docker run", spec)
            where = f"line {number}"
            if spec == "-P":
                findings.append(Finding(path, where, spec, "--publish-all binds every exposed port on every interface"))
                continue
            try:
                verdict = judge_short(spec)
            except UnparseableError as exc:
                findings.append(Finding(path, where, spec, f"unparseable: {exc}"))
                continue
            if not verdict.bound:
                if key in ALLOWED_UNBOUND:
                    seen.add(key)
                    continue
                findings.append(Finding(path, where, spec, verdict.problem))
            elif verdict.host_ip_interpolated:
                findings.append(Finding(path, where, spec, _INTERPOLATED_HOST))
    return findings, seen


# ------------------------------------------------------------------ the guard


@pytest.fixture(scope="module")
def tracked() -> list[str]:
    assert _REPO_ROOT is not None
    return tracked_files(_REPO_ROOT)


@pytest.fixture(scope="module")
def all_yaml(tracked: list[str]) -> list[YamlFile]:
    assert _REPO_ROOT is not None
    return yaml_files(_REPO_ROOT, tracked)


@pytest.fixture(scope="module")
def sweeps(tracked: list[str], all_yaml: list[YamlFile]) -> dict[str, tuple[list[Finding], set]]:
    assert _REPO_ROOT is not None
    compose, _ = compose_files(all_yaml)
    return {
        "compose": sweep_compose(compose),
        "workflows": sweep_workflows(all_yaml),
        "cli": sweep_cli(_REPO_ROOT, tracked),
    }


class TestSelector:
    def test_every_compose_file_is_found_and_parses(self, all_yaml: list[YamlFile]) -> None:
        compose, broken = compose_files(all_yaml)
        names = {item.path for item in compose}

        assert not broken, broken
        # The files the defect was found in are a floor, not the selector.
        assert {"docker-compose.yml", "docker-compose.release.yml"} <= names, names

    def test_the_cli_sweep_sees_the_known_publishes(self, tracked: list[str]) -> None:
        """If the text sweep stopped matching, every rule below would pass vacuously."""
        assert _REPO_ROOT is not None
        text = (_REPO_ROOT / ".taskfiles" / "mcp.yaml").read_text(encoding="utf-8")

        assert cli_publishes(".taskfiles/mcp.yaml", text), "the --publish in .taskfiles/mcp.yaml is no longer seen"


class TestEveryPublishBindsLoopback:
    def test_compose(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["compose"]
        assert not findings, "Compose ports that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_workflow_containers(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["workflows"]
        assert not findings, "workflow container ports that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_docker_run_commands(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["cli"]
        assert not findings, "docker run publishes that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_every_allow_list_entry_still_exists(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        """A stale entry is a hole waiting for a new publish of the same spelling."""
        seen = set().union(*(keys for _, keys in sweeps.values()))

        assert set(ALLOWED_OVERRIDABLE) - seen == set()
        assert set(ALLOWED_UNBOUND) - seen == set()

    def test_every_overridable_entry_defaults_to_loopback(self) -> None:
        for (_, _, raw), reason in ALLOWED_OVERRIDABLE.items():
            assert reason.strip()
            assert judge_short(raw).bound, raw


# ------------------------------------------------------------------ the parser itself


@pytest.mark.parametrize(
    ("spec", "bound"),
    [
        ("8529:8529", False),
        ("8529", False),
        ("8000-8005:8000-8005", False),
        ("0.0.0.0:8529:8529", False),
        ("[::]:80:80", False),
        ("192.168.1.10:11434:11434", False),
        ("${PORT:-8000}:8000", False),
        ("${PORT-8000}:8000/udp", False),
        ("${BIND:-0.0.0.0}:8080:8080", False),
        ("${PORT}:8000", False),
        ("$PORT:8000", False),
        ("127.0.0.1::$PORT", True),
        ("127.0.0.1:${PORT:?set it}:8000", True),
        ("127.0.0.1:8529:8529", True),
        ("127.0.0.1::8529", True),
        ("127.0.0.1:8000-8005:8000-8005", True),
        ("127.0.0.1:${PORT:-8000}:8000", True),
        ("127.0.1.1:53:53/udp", True),
        ("[::1]:6001:6001", True),
        ("${BIND:-127.0.0.1}:8080:8080", True),
    ],
)
def test_short_syntax(spec: str, bound: bool) -> None:
    assert judge_short(spec).bound is bound


@pytest.mark.parametrize(
    "spec",
    [
        "${BIND:?set it}:80:80",
        "${BIND}:80:80",
        "$BIND:80:80",
        "${BIND:+x}:80:80",
        "${A:-${B:-127.0.0.1}}:80:80",
        "::1:80:80",
        "localhost:80:80",
        "127.0.0.1:http:80",
        "127.0.0.1:99999:80",
    ],
)
def test_unparseable_short_syntax_fails_closed(spec: str) -> None:
    with pytest.raises(UnparseableError):
        judge_short(spec)


def test_interpolated_host_is_flagged() -> None:
    assert judge_short("${BIND:-127.0.0.1}:8080:8080").host_ip_interpolated is True
    assert judge_short("127.0.0.1:${PORT:-8000}:8000").host_ip_interpolated is False


@pytest.mark.parametrize(
    ("entry", "bound"),
    [
        ({"target": "80", "published": "8080"}, False),
        ({"target": "80", "published": "8080", "host_ip": "0.0.0.0"}, False),
        ({"target": "80", "published": "8080", "host_ip": "127.0.0.1", "protocol": "tcp"}, True),
        ({"target": "80", "host_ip": "::1", "mode": "host"}, True),
    ],
)
def test_long_syntax(entry: dict[str, Any], bound: bool) -> None:
    assert judge_long(entry).bound is bound


def test_long_syntax_unknown_key_fails_closed() -> None:
    with pytest.raises(UnparseableError):
        judge_long({"target": "80", "host_ip": "127.0.0.1", "hostip": "0.0.0.0"})


def test_unquoted_yaml_port_stays_a_string() -> None:
    """PyYAML would read ``- 8080:80`` as the base-60 integer 484880."""
    document = load_yaml("services:\n  web:\n    image: x\n    ports:\n      - 8080:80\n      - 8080\n")

    assert document["services"]["web"]["ports"] == ["8080:80", "8080"]


def test_compose_sweep_reports_network_mode_host_and_non_list_ports() -> None:
    text = "services:\n  a:\n    image: x\n    network_mode: host\n  b:\n    image: x\n    ports: '80:80'\n"
    files = [YamlFile("compose.yaml", load_yaml(text), "")]

    findings, _ = sweep_compose(files)

    assert {finding.where for finding in findings} == {"a", "b"}


def test_compose_merge_tags_are_read() -> None:
    document = load_yaml("services:\n  a:\n    image: x\n    ports: !override\n      - 80:80\n")

    findings, _ = sweep_compose([YamlFile("docker-compose.x.yml", document, "")])

    assert [finding.raw for finding in findings] == ["80:80"]


def test_compose_found_by_shape_not_only_by_name() -> None:
    files = [YamlFile("deploy/stack.yaml", load_yaml("services:\n  a:\n    image: x\n    ports: ['80:80']\n"), "")]

    compose, _ = compose_files(files)

    assert [item.path for item in compose] == ["deploy/stack.yaml"]


@pytest.mark.parametrize(
    ("text", "specs"),
    [
        ("docker run -d -p 8529:8529 arangodb", ["8529:8529"]),
        ("docker run -dp 3000:3000 app", ["3000:3000"]),
        ("docker run --publish=127.0.0.1:80:80 app", ["127.0.0.1:80:80"]),
        ('docker run -d \\\n  -p "11434:11434" \\\n  ollama', ["11434:11434"]),
        ("docker compose -p proj run --rm --publish 8080:80 frontend", ["8080:80"]),
        ("docker compose -p proj up -d", []),
        ("docker run -P app", ["-P"]),
        ("docker run app && psql -p 5432", []),
        ("PGPASSWORD=x psql -h localhost -p 5433", []),
    ],
)
def test_cli_publishes(text: str, specs: list[str]) -> None:
    assert [spec for _, spec in cli_publishes("x.sh", text)] == specs


@pytest.mark.parametrize(
    ("source", "specs"),
    [
        ('run(["docker", "run", "-d", "-p", f"127.0.0.1::{PORT}", image])', ["127.0.0.1::1"]),
        ('_docker("run", "-d", "-p", "8529:8529", image)', ["8529:8529"]),
        ('_docker("run", "--publish=8080:80", image)', ["8080:80"]),
        ('_docker("run", "-P", image)', ["-P"]),
        ('_docker("run", "-p", spec, image)', ["<non-literal>"]),
        ('["docker", "compose", "-p", project_name()]', []),
        ('[sys.executable, "-m", "pytest", "-p", "no:cacheprovider"]', []),
    ],
)
def test_argv_publishes(source: str, specs: list[str]) -> None:
    assert [spec for _, spec in argv_publishes(source)] == specs
