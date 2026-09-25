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

**What is asserted, over which selector.** Every spelling that publishes a
host port is read from every file that can carry it — never from a list of the
files the defect was found in:

* a Compose ``ports:`` entry, short syntax (``"8529:8529"``,
  ``"127.0.0.1::8529"``, ``"[::1]:80:80"``, ranges, ``/udp``) or long syntax
  (``published:`` / ``host_ip:``), in every tracked file that is a Compose file
  by name OR by shape, and in every Compose-shaped fenced YAML block of a
  Markdown file (a spec or doc example is copied as surely as the file); plus
  ``network_mode: host`` (interpolation resolved), which puts every listener of
  the container on every host interface;
* a GitHub Actions ``services:`` / ``container:`` ``ports:`` entry (the runner
  hands it to ``docker create -p``) and their ``options:`` string;
* a ``docker`` / ``podman`` / ``nerdctl`` ``run`` or ``create`` command (also
  ``docker compose run``, ``docker service create``) with ``-p`` / ``-p8080:80``
  / ``-dp`` / ``--publish`` / ``-P`` / ``--publish-all`` / ``--network host`` in
  any tracked script, config, JSON, shebang script or document. A YAML file is
  read scalar by scalar, so a folded ``>-`` command is one line and a workflow
  publish is keyed by its job;
* the same flags in a Python argv sequence (``["docker", "run", "-p", …]`` or a
  call to a helper whose name contains an engine), read from the AST, an
  f-string rendered with its placeholders so ``f"127.0.0.1::{port}"`` keeps its
  literal host;
* a kind cluster config (``kind: Cluster``, ``apiVersion: kind.x-k8s.io/…``)
  in any tracked YAML file, fenced YAML block or shell heredoc (#1756): every
  ``extraPortMappings`` entry is a host publish of the node container and must
  name a loopback ``listenAddress`` (kind's default is ``0.0.0.0``), and an
  explicit ``networking.apiServerAddress`` must be loopback. An
  ``apiVersion: kind.x-k8s.io/…`` line that does not sit in a config this
  module could read fails.

This module itself is not read: its text is its fixtures.

**What it cannot see**, named so nobody reads its silence as coverage: a publish
assembled at runtime (a variable or ``*args`` holding ``"-p"``, an engine binary
held in a variable, a Docker SDK ``ports=`` mapping, testcontainers); a
``docker run`` whose ``run`` and ``-p`` sit in different strings of a shell
script (a function wrapping ``docker run "$@"``); a Compose-shaped YAML file
that does not parse and is not named like one; a Markdown YAML block that does
not parse and has no ``ports:`` / ``network_mode:`` line. None of the first
three exists in this checkout (``git grep`` for ``ports=``, ``testcontainers``,
``DockerContainer(`` on 2026-09-25); a new one needs its own reading here. A
kind cluster already running keeps the binding it was created with — the
config is read, not the cluster — and a kind config in a file type the text
sweep does not read (see ``_eligible``) is not seen. And a loopback bind is only as good as the engine:
Docker Engine before 28.0 let hosts on the same L2 segment reach ports
published on ``127.0.0.1`` (moby's ``route_localnet`` fix) — not checkable from
the repository.

Each entry must name a loopback host address (``127.0.0.0/8`` or ``::1``).
Environment interpolation is resolved the way Compose resolves it with the
variable unset (``${VAR:-default}`` → ``default``), so ``"${PORT:-8000}:8000"``
is the unbound ``8000:8000`` it starts as. A host address that is itself
interpolated can be widened by whoever sets the variable; it is accepted only
when its default is loopback AND the entry is named in :data:`ALLOWED_OVERRIDABLE`
with the reason remote reach is wanted.

**Fail closed.** A spelling this module cannot resolve — an interpolation
without a default in the host field, ``${VAR:?…}`` there, a nested default, a
bare IPv6 address, a hostname instead of an address, an unknown long-syntax
key, a ``ports:`` value that is not a list, swarm's ``published=…,target=…``
form, a non-literal argv spec — is a failure that names the spelling, never a
skip.

**Red first.** Run against develop 47771d74d this module failed with the 13
unbound Compose entries above, the ``--publish 8080:80`` in
``.taskfiles/mcp.yaml``, ``-P`` in ``scripts/ci/smoke_model_image.sh``, every
``docker run -p 8529:8529`` the integration tests' docstrings tell a developer
to run (with ``rootpassword``), the two GitHub Actions publishes and the
Compose examples in REQ-027 (Light mode) and NFR-001. The kind sweep (#1756),
run against develop 0c217e570, failed with the two ingress mappings (80, 443)
of ``kind-config.yaml`` and the 16 ``extraPortMappings`` entries of the three
``cat > kind-config.yaml <<EOF`` examples in NFR-004.
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

# Publishes that stay on every interface, keyed (file, where, the entry as
# written) — `where` is the Compose service, the workflow job, or the line of
# a text file. None today: the two GitHub Actions publishes an earlier draft of
# #1750 exempted as "a hosted runner has no inbound path" also run under `act`
# on a developer's workstation, where they are exactly this defect.
ALLOWED_UNBOUND: dict[tuple[str, str, str], str] = {}


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
            if service.get("network_mode") is not None:
                try:
                    mode, _ = resolve(str(service["network_mode"]))
                except UnparseableError as exc:
                    findings.append(Finding(item.path, str(name), f"network_mode: {service['network_mode']}", str(exc)))
                else:
                    if mode.strip() == "host":
                        findings.append(
                            Finding(
                                item.path, str(name), "network_mode: host", "every listener binds every host interface"
                            )
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
    *(".sh", ".bash", ".py", ".yml", ".yaml", ".md", ".toml", ".json"),
    *(".cfg", ".ini", ".txt", ".j2", ".env", ".example"),
)
_TEXT_NAMES = re.compile(r"(^|/)(Taskfile[^/]*|Makefile|Dockerfile[^/]*|Justfile)$")
_LOCKFILE = re.compile(r"(^|/)[^/]*-lock\.json$")
_CONTAINER_CLI = re.compile(
    r"(?<![\w-])(?:docker(?:-compose)?|podman(?:-compose)?|nerdctl)(?![\w-])"
    r"(?P<middle>.*?)(?<![\w-])(?:run|create)(?![\w-])(?P<tail>.*)"
)
_SHELL_END = re.compile(r"&&|\|\||;|(?<![|])\|(?![|])")
_TOKEN = re.compile(r"\"[^\"]*\"|'[^']*'|\S+")

#: Options of ``docker run|create``, ``docker compose run``, ``docker service
#: create``, podman and nerdctl that take NO value. The walk stops at the first
#: token that is not an option — the image or service — so a ``-p`` that belongs
#: to the program in the container (``psql -p 5432``) is never read as a
#: publish. An option missing from this table is assumed to take a value: the
#: walk then reads one token too far rather than stopping early, so its error
#: is a false alarm, never a missed publish.
_BOOLEAN_LONG = frozenset(
    {
        *("--rm", "--detach", "--interactive", "--tty", "--init", "--privileged", "--read-only"),
        *("--publish-all", "--service-ports", "--no-deps", "--use-aliases", "--build", "--remove-orphans"),
        *(
            "--quiet-pull",
            "--no-TTY",
            "--no-healthcheck",
            "--oom-kill-disable",
            "--sig-proxy",
            "--disable-content-trust",
        ),
        *("--replace", "--quiet", "--help"),
    }
)
_BOOLEAN_SHORT = frozenset("ditPTq")

#: The two non-address results a CLI sweep can report.
PUBLISH_ALL = "-P"
HOST_NETWORK = "--network host"

#: This module's own text is its fixtures and its red-first record — every
#: publish in it is an example of the class, none runs.
_SELF = Path(__file__).resolve()


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


def publishes_in_options(tokens: list[str | None]) -> list[str]:
    """The publishes among the options of one container-starting command.

    ``tokens`` are the arguments after ``run`` / ``create``; ``None`` is an
    argument whose value is unknown (a Python variable). The walk ends at the
    first literal that is not an option — the image or the service.
    """
    found: list[str] = []
    index = 0

    def following() -> str | None:
        nonlocal index
        index += 1
        return tokens[index] if index < len(tokens) else None

    while index < len(tokens):
        token = tokens[index]
        if token is None:
            index += 1
            continue
        if token == "--" or not token.startswith("-") or token == "-":
            break
        name, has_value, value = token.partition("=")
        if name.startswith("--"):
            if name == "--publish":
                spec = value if has_value else following()
                found.append(spec if spec is not None else "<non-literal>")
            elif name == "--publish-all":
                if not has_value or value.strip("\"'").lower() not in ("false", "0"):
                    found.append(PUBLISH_ALL)
            elif name in ("--network", "--net"):
                if (value if has_value else following()) == "host":
                    found.append(HOST_NETWORK)
            elif not has_value and name not in _BOOLEAN_LONG:
                following()
        else:
            letters = token[1:]
            for position, letter in enumerate(letters):
                if letter in _BOOLEAN_SHORT:
                    if letter == "P":
                        found.append(PUBLISH_ALL)
                    continue
                attached = letters[position + 1 :].removeprefix("=")
                argument = attached or following()
                if letter == "p":
                    found.append(argument if argument is not None else "<non-literal>")
                break
        index += 1
    return found


def _unquote(token: str) -> str:
    return token.strip("\"'`")


def cli_publishes(text: str) -> list[tuple[int, str]]:
    """Every publish in a ``docker|podman|nerdctl … run|create`` command: (line, spec).

    Every command of a line is read (``a && docker run …; docker run …``), and
    each only up to its image. ``-P`` / ``--publish-all`` report as
    :data:`PUBLISH_ALL`, ``--network host`` / ``--net=host`` as
    :data:`HOST_NETWORK`.
    """
    found = []
    for number, line in logical_lines(text):
        for segment in _SHELL_END.split(line):
            match = _CONTAINER_CLI.search(segment)
            if not match:
                continue
            tokens: list[str | None] = [_unquote(token) for token in _TOKEN.findall(match.group("tail"))]
            found += [(number, _clean_spec(spec)) for spec in publishes_in_options(tokens)]
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


_ENGINES = ("docker", "podman", "nerdctl")


def argv_publishes(source: str) -> list[tuple[int, str]]:
    """Every publish in a Python argv sequence that starts a container: (line, spec).

    A sequence is a list/tuple literal or a call's positional arguments; it
    starts a container when it holds ``"run"`` or ``"create"`` and either an
    engine element (``"docker"``, ``"podman"``, ``"nerdctl"``) or a callee whose
    name contains one. A spec that is not a literal is reported as
    ``<non-literal>`` so the caller fails closed on it.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.List | ast.Tuple):
            elements, engine_callee = list(node.elts), False
        elif isinstance(node, ast.Call):
            callee = _callee_name(node).lower()
            elements, engine_callee = list(node.args), any(engine in callee for engine in _ENGINES)
        else:
            continue
        strings = [_argv_string(element) for element in elements]
        verbs = [index for index, value in enumerate(strings) if value in ("run", "create")]
        if not verbs or not (engine_callee or any(value in _ENGINES for value in strings)):
            continue
        found += [(elements[verbs[0]].lineno, spec) for spec in publishes_in_options(strings[verbs[0] + 1 :])]
    return found


def _yaml_strings(node: Any, trail: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    """Every string scalar of a parsed YAML document with the key path it sits under."""
    if isinstance(node, str):
        return [(trail, node)]
    if isinstance(node, dict):
        return [item for key, value in node.items() for item in _yaml_strings(value, (*trail, str(key)))]
    if isinstance(node, list):
        return [item for value in node for item in _yaml_strings(value, trail)]
    return []


def _where_in_yaml(document: Any, trail: tuple[str, ...]) -> str:
    """A workflow's publishes are keyed by job — the allow-list names the job, never a line."""
    if isinstance(document, dict) and isinstance(document.get("jobs"), dict) and trail[:1] == ("jobs",):
        return f"jobs.{trail[1]}" if len(trail) > 1 else "jobs"
    return "yaml"


def text_publishes(path: str, text: str, document: Any) -> list[tuple[str, str]]:
    """(where, spec) for every CLI publish in one file.

    A YAML file that parses is read scalar by scalar — a folded ``>-`` command
    is one line there, and a container's ``options:`` string is read as the
    ``docker create`` arguments the runner makes of it — plus its comment
    lines, which the parse drops. Any other file, and a YAML file that does not
    parse (a Helm template), is read as text.
    """
    found: list[tuple[str, str]] = []
    if document is not None:
        for trail, value in _yaml_strings(document):
            where = _where_in_yaml(document, trail)
            if trail and trail[-1] == "options" and ("services" in trail or "container" in trail):
                value = "docker create " + value
            found += [(where, spec) for _, spec in cli_publishes(value)]
        # Comments vanish in the parse, yet a commented copy-paste command
        # (``#   docker run -p 8529:8529 \``) is still a command someone runs.
        comments = "\n".join(
            re.sub(r"^\s*#+ ?", "", row) if row.lstrip().startswith("#") else "" for row in text.splitlines()
        )
        found += [(f"line {number}", spec) for number, spec in cli_publishes(comments)]
        return found
    found += [(f"line {number}", spec) for number, spec in cli_publishes(text)]
    if path.endswith(".py"):
        found += [(f"line {number}", spec) for number, spec in argv_publishes(text)]
    return found


_FENCE = re.compile(r"^(?P<indent>[ \t]*)```(?:ya?ml)[^\n]*\n(?P<body>.*?)^(?P=indent)```", re.MULTILINE | re.DOTALL)


def markdown_compose_blocks(path: str, text: str) -> tuple[list[YamlFile], list[str]]:
    """Compose-shaped fenced YAML blocks of a Markdown file, and the ``ports:`` blocks that do not parse."""
    blocks, broken = [], []
    for match in _FENCE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        body = "\n".join(row[len(match.group("indent")) :] for row in match.group("body").splitlines())
        try:
            documents = list(yaml.load_all(body, Loader=_StringLoader))  # noqa: S506 — SafeLoader subclass
        except yaml.YAMLError as exc:
            if re.search(r"^\s*(ports|network_mode)\s*:", body, re.MULTILINE):
                broken.append(f"{path}:{line}: a YAML block with ports: that does not parse ({type(exc).__name__})")
            continue
        blocks += [YamlFile(f"{path}:{line}", document, "") for document in documents if _looks_like_compose(document)]
    return blocks, broken


def _has_shebang(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(2) == b"#!"
    except OSError:  # pragma: no cover
        return False


def _eligible(root: Path, path: str) -> bool:
    if _LOCKFILE.search(path) or (root / path).resolve() == _SELF:
        return False
    if path.endswith(_TEXT_SUFFIXES) or _TEXT_NAMES.search(path):
        return True
    return "." not in Path(path).name and _has_shebang(root / path)


def _judge_cli(path: str, where: str, spec: str) -> tuple[Finding | None, tuple[str, str, str] | None]:
    key = (path, where, spec)
    if spec == PUBLISH_ALL:
        return Finding(path, where, spec, "--publish-all binds every exposed port on every interface"), None
    if spec == HOST_NETWORK:
        return Finding(path, where, spec, "the host network puts every listener on every host interface"), None
    try:
        verdict = judge_short(spec)
    except UnparseableError as exc:
        return Finding(path, where, spec, f"unparseable: {exc}"), None
    if not verdict.bound:
        if key in ALLOWED_UNBOUND:
            return None, key
        return Finding(path, where, spec, verdict.problem), None
    if verdict.host_ip_interpolated:
        return Finding(path, where, spec, _INTERPOLATED_HOST), None
    return None, None


def sweep_cli(root: Path, tracked: list[str], parsed: dict[str, YamlFile]) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    seen: set = set()
    for path in tracked:
        if not _eligible(root, path):
            continue
        try:
            text = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        item = parsed.get(path)
        document = item.document if item is not None and not item.error else None
        try:
            publishes = text_publishes(path, text, document)
        except SyntaxError as exc:
            findings.append(Finding(path, "ast", "", f"unparseable Python: {exc}"))
            continue
        for where, spec in publishes:
            finding, key = _judge_cli(path, where, spec)
            if finding is not None:
                findings.append(finding)
            if key is not None:
                seen.add(key)
    return findings, seen


def sweep_markdown(root: Path, tracked: list[str]) -> tuple[list[Finding], set]:
    findings: list[Finding] = []
    for path in tracked:
        if not path.endswith(".md"):
            continue
        blocks, broken = markdown_compose_blocks(path, (root / path).read_text(encoding="utf-8"))
        findings += [Finding(entry.split(":", 1)[0], "yaml block", "", entry) for entry in broken]
        found, _ = sweep_compose(blocks)
        findings += found
    return findings, set()


# ------------------------------------------------------------------ kind clusters

#: kind publishes a node container's port on the host through the cluster
#: config, not through a ``docker run`` this module could read: every
#: ``extraPortMappings`` entry becomes a ``-p <listenAddress>:<hostPort>:…`` of
#: the node container, and ``listenAddress`` defaults to ``0.0.0.0``
#: (kind.sigs.k8s.io/docs/user/configuration, "0.0.0.0 is the current
#: default"). ``networking.apiServerAddress`` is the same kind of bind for the
#: API server; its default is ``127.0.0.1``, so only an explicit value is read.
#: kind interpolates no environment variable in its config, so there is no
#: overridable spelling and no allow-list here.
_KIND_API_VERSION = "kind.x-k8s.io/"
_KIND_API_LINE = re.compile(r"^[ \t]*apiVersion:[ \t]*[\"']?kind\.x-k8s\.io/", re.MULTILINE)
_KIND_MAPPING_KEYS = {"containerPort", "hostPort", "listenAddress", "protocol"}
_HEREDOC = re.compile(
    r"<<-?[ \t]*(?P<quote>['\"]?)(?P<tag>[A-Za-z_]\w*)(?P=quote)[^\n]*\n(?P<body>.*?)^[ \t]*(?P=tag)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def is_kind_cluster(document: Any) -> bool:
    return (
        isinstance(document, dict)
        and document.get("kind") == "Cluster"
        and str(document.get("apiVersion", "")).startswith(_KIND_API_VERSION)
    )


def _yaml_regions(path: str, text: str) -> list[tuple[int, int, str]]:
    """``(start, end, body)`` of every place a YAML document can sit in ``text``.

    A YAML file is one region. Any other text contributes its fenced YAML
    blocks (de-indented as in :func:`markdown_compose_blocks`) and its shell
    heredoc bodies — a spec that tells a developer to ``cat > kind-config.yaml
    <<EOF`` is a config as surely as the file.
    """
    if path.endswith((".yml", ".yaml")):
        return [(0, len(text), text)]
    regions = []
    for match in _FENCE.finditer(text):
        indent = match.group("indent")
        body = "\n".join(row[len(indent) :] for row in match.group("body").splitlines())
        regions.append((match.start(), match.end(), body))
    regions += [(match.start(), match.end(), match.group("body")) for match in _HEREDOC.finditer(text)]
    return sorted(regions)


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def kind_clusters(path: str, text: str) -> tuple[list[tuple[str, dict[str, Any]]], list[str]]:
    """The kind cluster configs written in ``text``, and every one this guard cannot read.

    Fail closed: each ``apiVersion: kind.x-k8s.io/…`` line must lie inside a
    region that parsed into a kind ``Cluster`` document; one that does not — a
    region that does not parse, a config embedded in a form not read here — is
    reported, never skipped.
    """
    clusters: list[tuple[str, dict[str, Any]]] = []
    covered: list[tuple[int, int]] = []
    for start, end, body in _yaml_regions(path, text):
        if _KIND_API_VERSION not in body:
            continue
        try:
            documents = list(yaml.load_all(body, Loader=_StringLoader))  # noqa: S506 — SafeLoader subclass
        except yaml.YAMLError:
            continue
        found = [document for document in documents if is_kind_cluster(document)]
        if not found:
            continue
        covered.append((start, end))
        where = path if (start, end) == (0, len(text)) else f"{path}:{_line_of(text, start)}"
        clusters += [(where, document) for document in found]
    broken = [
        f"{path}:{_line_of(text, match.start())}: a kind cluster config this guard cannot read"
        for match in _KIND_API_LINE.finditer(text)
        if not any(start <= match.start() < end for start, end in covered)
    ]
    return clusters, broken


def _judge_kind_address(where: str, raw: str, address: Any, missing: str) -> Finding | None:
    if address is None:
        return Finding(where, "kind", raw, missing)
    try:
        verdict = judge_host(str(address), host_interpolated=False)
    except UnparseableError as exc:
        return Finding(where, "kind", raw, f"unparseable: {exc}")
    return None if verdict.bound else Finding(where, "kind", raw, verdict.problem.replace("Docker", "kind"))


def judge_kind_cluster(where: str, document: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    networking = document.get("networking")
    if networking is not None and not isinstance(networking, dict):
        findings.append(Finding(where, "networking", render(networking), "networking: is not a mapping"))
    elif networking and "apiServerAddress" in networking:
        finding = _judge_kind_address(
            where, f"apiServerAddress={networking['apiServerAddress']}", networking["apiServerAddress"], ""
        )
        findings += [finding] if finding else []
    nodes = document.get("nodes")
    if nodes is None:
        return findings
    if not isinstance(nodes, list):
        return [*findings, Finding(where, "nodes", render(nodes), "nodes: is not a list — unparseable")]
    for index, node in enumerate(nodes):
        node_where = f"nodes[{index}]"
        if not isinstance(node, dict):
            findings.append(Finding(where, node_where, render(node), "node is not a mapping — unparseable"))
            continue
        mappings = node.get("extraPortMappings")
        if mappings is None:
            continue
        if not isinstance(mappings, list):
            findings.append(Finding(where, node_where, render(mappings), "extraPortMappings: is not a list"))
            continue
        for mapping in mappings:
            raw = render(mapping)
            if not isinstance(mapping, dict):
                findings.append(Finding(where, node_where, raw, "port mapping is not a mapping — unparseable"))
                continue
            unknown = set(mapping) - _KIND_MAPPING_KEYS
            if unknown or "containerPort" not in mapping:
                problem = f"keys this guard does not know: {sorted(unknown)}" if unknown else "no containerPort"
                findings.append(Finding(where, node_where, raw, f"unparseable: {problem}"))
                continue
            finding = _judge_kind_address(
                where,
                raw,
                mapping.get("listenAddress"),
                "names no listenAddress, so kind binds every interface (default 0.0.0.0)",
            )
            if finding is not None:
                findings.append(Finding(finding.path, node_where, finding.raw, finding.problem))
    return findings


def sweep_kind(root: Path, tracked: list[str]) -> tuple[list[Finding], list[str]]:
    """Every kind cluster config in a tracked file, and the findings over them."""
    findings: list[Finding] = []
    seen: list[str] = []
    for path in tracked:
        if not _eligible(root, path):
            continue
        try:
            text = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # prose-permeable: a cheap prefilter over every text file; a Markdown example is a config as surely as
        # the file, so its prose half is part of the subject — kind_clusters() then parses what it selects
        if _KIND_API_VERSION not in text:
            continue
        clusters, broken = kind_clusters(path, text)
        findings += [Finding(entry.split(":", 1)[0], "kind", "", entry) for entry in broken]
        for where, document in clusters:
            seen.append(where)
            findings += judge_kind_cluster(where, document)
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
def kind_sweep(tracked: list[str]) -> tuple[list[Finding], list[str]]:
    assert _REPO_ROOT is not None
    return sweep_kind(_REPO_ROOT, tracked)


@pytest.fixture(scope="module")
def sweeps(
    tracked: list[str], all_yaml: list[YamlFile], kind_sweep: tuple[list[Finding], list[str]]
) -> dict[str, tuple[list[Finding], set]]:
    assert _REPO_ROOT is not None
    compose, _ = compose_files(all_yaml)
    return {
        "compose": sweep_compose(compose),
        "workflows": sweep_workflows(all_yaml),
        "cli": sweep_cli(_REPO_ROOT, tracked, {item.path: item for item in all_yaml}),
        "markdown": sweep_markdown(_REPO_ROOT, tracked),
        "kind": (kind_sweep[0], set()),
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

        assert cli_publishes(text), "the --publish in .taskfiles/mcp.yaml is no longer seen"

    def test_every_kind_cluster_config_is_found(self, kind_sweep: tuple[list[Finding], list[str]]) -> None:
        _, seen = kind_sweep

        # The file the defect was found in is a floor, not the selector.
        assert "kind-config.yaml" in seen, seen


class TestEveryPublishBindsLoopback:
    def test_compose(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["compose"]
        assert not findings, "Compose ports that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_workflow_containers(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["workflows"]
        assert not findings, "workflow container ports that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_compose_blocks_in_markdown(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        """A Compose example in a doc or a spec is copied as surely as the file itself."""
        findings, _ = sweeps["markdown"]
        assert not findings, "Compose examples in Markdown that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_docker_run_commands(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        findings, _ = sweeps["cli"]
        assert not findings, "docker run publishes that do not bind loopback:\n" + "\n".join(map(str, findings))

    def test_kind_cluster_port_mappings(self, sweeps: dict[str, tuple[list[Finding], set]]) -> None:
        """#1756 — a kind ``extraPortMappings`` entry is a host publish by another tool."""
        findings, _ = sweeps["kind"]
        assert not findings, "kind cluster configs that do not bind loopback:\n" + "\n".join(map(str, findings))

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
        ("docker run -d --name a img && docker run -d -p 6379:6379 valkey", ["6379:6379"]),
        ("docker run --rm postgres:16 psql -h db -p 5432 -U x", []),
        ("docker run -e A=1 -v x:/y --name db -p 127.0.0.1:1:1 img -p 9", ["127.0.0.1:1:1"]),
        ("docker run --unknown-flag value -p 80:80 img", ["80:80"]),
        ("docker run -d -p8529:8529 arangodb", ["8529:8529"]),
        ("docker run -dp8529:8529 arangodb", ["8529:8529"]),
        ("docker create -p 80:80 app", ["80:80"]),
        ("docker container create --publish 80:80 app", ["80:80"]),
        ("docker service create --publish published=8080,target=80 app", ["published=8080,target=80"]),
        ("podman run -p 80:80 app", ["80:80"]),
        ("nerdctl run -p 127.0.0.1:80:80 app", ["127.0.0.1:80:80"]),
        ("docker run --publish-all=true app", ["-P"]),
        ("docker run --publish-all=false app", []),
        ("docker run --network host app", ["--network host"]),
        ("docker run --net=host app", ["--network host"]),
        ("PGPASSWORD=x psql -h localhost -p 5433", []),
    ],
)
def test_cli_publishes(text: str, specs: list[str]) -> None:
    assert [spec for _, spec in cli_publishes(text)] == specs


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
        ('_docker("run", "-p8080:80", image)', ["8080:80"]),
        ('["docker", "create", "-dp", "80:80", image]', ["80:80"]),
        ('["podman", "run", "--network=host", image]', ["--network host"]),
        ('["docker", "run", "--network", "host", image]', ["--network host"]),
    ],
)
def test_argv_publishes(source: str, specs: list[str]) -> None:
    assert [spec for _, spec in argv_publishes(source)] == specs


def test_workflow_scalars_are_keyed_by_job_and_options_are_read() -> None:
    document = load_yaml(
        "jobs:\n"
        "  it:\n"
        "    runs-on: ubuntu-latest\n"
        "    services:\n"
        "      db:\n"
        "        image: x\n"
        "        options: >-\n"
        "          --publish 8529:8529\n"
        "          --health-cmd true\n"
        "    steps:\n"
        "      - run: >-\n"
        "          docker run -d\n"
        "          -p 6379:6379 valkey\n"
    )

    assert sorted(text_publishes(".github/workflows/x.yml", "", document)) == [
        ("jobs.it", "6379:6379"),
        ("jobs.it", "8529:8529"),
    ]


def test_markdown_compose_blocks_are_read() -> None:
    text = '# Doc\n\n```yaml\nservices:\n  web:\n    image: x\n    ports:\n      - "8000:8000"\n```\n'

    blocks, broken = markdown_compose_blocks("doc.md", text)
    findings, _ = sweep_compose(blocks)

    assert not broken
    assert [(finding.path, finding.raw) for finding in findings] == [("doc.md:3", "8000:8000")]


def test_markdown_block_with_ports_that_does_not_parse_fails_closed() -> None:
    _, broken = markdown_compose_blocks("doc.md", "```yaml\nports:\n  - [\n```\n")

    assert broken


def test_network_mode_is_resolved_before_it_is_compared() -> None:
    document = load_yaml('services:\n  a:\n    image: x\n    network_mode: "${NET:-host}"\n')

    findings, _ = sweep_compose([YamlFile("compose.yaml", document, "")])

    assert [finding.raw for finding in findings] == ["network_mode: host"]


def test_yaml_comment_commands_are_read() -> None:
    text = (
        "tasks:\n  x:\n    # run it by hand:\n"
        "    #   docker run -d --name db -p 8529:8529 \\\n"
        "    #     arangodb\n    cmds: [true]\n"
    )

    assert text_publishes("Taskfile.yaml", text, load_yaml(text)) == [("line 4", "8529:8529")]


# ------------------------------------------------------------------ kind clusters (#1756)

_KIND_HEAD = "kind: Cluster\napiVersion: kind.x-k8s.io/v1alpha4\n"


def _kind(mapping: str) -> dict[str, Any]:
    return load_yaml(_KIND_HEAD + "nodes:\n  - role: control-plane\n    extraPortMappings:\n" + mapping)


@pytest.mark.parametrize(
    ("mapping", "bound"),
    [
        ("      - containerPort: 80\n        hostPort: 80\n", False),
        ('      - containerPort: 80\n        hostPort: 80\n        listenAddress: "0.0.0.0"\n', False),
        ('      - containerPort: 80\n        hostPort: 80\n        listenAddress: ""\n', False),
        ('      - containerPort: 80\n        hostPort: 80\n        listenAddress: "192.168.1.5"\n', False),
        ('      - containerPort: 80\n        hostPort: 80\n        listenAddress: "127.0.0.1"\n', True),
        ('      - containerPort: 80\n        hostPort: 80\n        listenAddress: "::1"\n', True),
    ],
)
def test_kind_port_mapping(mapping: str, bound: bool) -> None:
    assert (judge_kind_cluster("kind.yaml", _kind(mapping)) == []) is bound


@pytest.mark.parametrize(
    "mapping",
    [
        '      - containerPort: 80\n        listenAddress: "localhost"\n',
        '      - containerPort: 80\n        listenAddress: "${BIND}"\n',
        '      - containerPort: 80\n        listenAddress: "127.0.0.1"\n        hostIP: "0.0.0.0"\n',
        '      - hostPort: 80\n        listenAddress: "127.0.0.1"\n',
        "      - 80:80\n",
    ],
)
def test_unparseable_kind_mapping_fails_closed(mapping: str) -> None:
    findings = judge_kind_cluster("kind.yaml", _kind(mapping))

    assert findings
    assert all("unparseable" in finding.problem for finding in findings), findings


def test_kind_api_server_address_is_read() -> None:
    document = load_yaml(_KIND_HEAD + 'networking:\n  apiServerAddress: "0.0.0.0"\n')

    assert [finding.raw for finding in judge_kind_cluster("kind.yaml", document)] == ["apiServerAddress=0.0.0.0"]


def test_kind_config_in_a_heredoc_and_a_fence_is_read() -> None:
    body = _KIND_HEAD + "nodes:\n- role: control-plane\n  extraPortMappings:\n  - containerPort: 80\n    hostPort: 80\n"
    text = f"# Setup\n\n```bash\ncat > kind-config.yaml <<EOF\n{body}EOF\n```\n\n```yaml\n{body}```\n"

    clusters, broken = kind_clusters("doc.md", text)

    assert not broken
    assert [where for where, _ in clusters] == ["doc.md:4", "doc.md:15"]
    assert all(judge_kind_cluster(where, document) for where, document in clusters)


def test_kind_config_this_guard_cannot_read_fails_closed() -> None:
    text = 'CONFIG = """\nkind: Cluster\napiVersion: kind.x-k8s.io/v1alpha4\n"""\n'

    clusters, broken = kind_clusters("make_cluster.py", text)

    assert clusters == []
    assert broken == ["make_cluster.py:3: a kind cluster config this guard cannot read"]


def test_a_non_kind_cluster_document_is_not_read() -> None:
    document = load_yaml("apiVersion: external-secrets.io/v1beta1\nkind: ClusterSecretStore\n")

    assert not is_kind_cluster(document)
