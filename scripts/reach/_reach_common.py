"""Shared plumbing of the capability-reach helpers under ``scripts/reach/`` (#1680).

The helpers are the target-repository half of the capability reach audit
(``spec/project/capability-reach-audit/`` in ``nolte/claude-shared``): Taskfile
targets that stand the T2 environment up and act on it, and observation steps
whose output the audit's runner compares against a probe's expectation. They run
on the host with the standard library only — the runner invokes them as
``python3 scripts/reach/<name>.py`` from the repository root, where none of the
backend's dependencies are installed. Code that needs the backend (the seed, the
declared inventories) is shipped into the running backend container and executed
there; see :func:`run_in_backend`.

Everything the stack exposes to the host is recorded in ``.reach/stack.json`` by
``stack.py up``: the ArangoDB and API base URLs (Docker picks the host ports),
the database, and the credentials of this throw-away stack. Nothing here holds a
real secret; the values are the E2E stack's test-only ones.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

#: The E2E compose file whose full-mode services the reach stack reuses, and the
#: overlay that adds what a probe needs (host ports, query tracking, host-readable storage).
COMPOSE_FILES = ("docker-compose.e2e.yml", "docker-compose.reach.yml")
#: Environment variable the overlay binds the E2E file's object-storage volume to.
#: Compose does not resolve a relative ``device`` in a volume's driver options, so
#: :func:`run` hands it the absolute path of ``.reach/storage``.
STORAGE_DIR_VARIABLE = "REACH_STORAGE_DIR"
#: The E2E file puts the full-mode services behind this profile.
COMPOSE_PROFILE = "full"
#: The services a T2 probe needs: data store, broker, API, worker. No frontend,
#: no Selenium — nothing a reach probe observes goes through a browser.
STACK_SERVICES = ("arangodb", "valkey", "backend-full", "celery-worker-full")
BACKEND_SERVICE = "backend-full"
WORKER_SERVICE = "celery-worker-full"

#: Default subject key; the Taskfile passes the same value.
DEFAULT_SUBJECT = "reach-subject"

#: Wall-clock bound on every HTTP call a helper makes (NFR-007: no unbounded wait).
HTTP_TIMEOUT_SECONDS = 30


class ReachError(RuntimeError):
    """A helper could not do its job; the message says why, the exit code is non-zero."""


def repo_root() -> Path:
    """The checkout root: the nearest ancestor of this file holding ``Taskfile.yaml``."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise ReachError(f"no checkout root above {here}")


def reach_dir() -> Path:
    """``.reach/`` — ignored by git; holds the stack record, subject records, storage."""
    return repo_root() / ".reach"


def project_name() -> str:
    """Compose project name, unique per working copy.

    Two worktrees running the probes at once must not share containers or
    volumes; a stack torn down by one would vanish under the other.
    """
    digest = hashlib.sha256(str(repo_root()).encode("utf-8")).hexdigest()[:8]
    return f"kp-reach-{digest}"


def compose_command(*args: str) -> list[str]:
    """``docker compose`` with this stack's project, files and profile, plus *args*."""
    command = ["docker", "compose", "-p", project_name()]
    for name in COMPOSE_FILES:
        command += ["-f", str(repo_root() / name)]
    command += ["--profile", COMPOSE_PROFILE]
    return [*command, *args]


def log(message: str) -> None:
    """Progress for a human reading the task output. Never on stdout."""
    print(f"[reach] {message}", file=sys.stderr, flush=True)


def run(
    command: list[str], *, timeout: float, stdin: bytes | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run *command* bounded by *timeout*; raise :class:`ReachError` on failure when *check*."""
    try:
        result = subprocess.run(
            command,
            input=stdin,
            capture_output=True,
            timeout=timeout,
            cwd=repo_root(),
            env={**os.environ, STORAGE_DIR_VARIABLE: str(reach_dir() / "storage")},
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReachError(f"{command[:4]} timed out after {timeout:.0f}s") from exc
    if check and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace").strip()[-2000:]
        raise ReachError(f"{' '.join(command[:6])} … exited {result.returncode}: {stderr}")
    return result


#: Where :func:`run_in_backend` places the working copy's scripts in the container.
CONTAINER_SCRIPT_DIR = "/tmp/reach-scripts"


def run_in_backend(script: Path, *args: str, support: tuple[Path, ...] = (), timeout: float = 300) -> str:
    """Execute a repository script inside the running backend container; return its stdout.

    *script* and every *support* module are copied to :data:`CONTAINER_SCRIPT_DIR`
    first, so the code that runs is the working copy's, and the script imports
    ``app`` from the container's own ``/app``: the backend the stack runs.
    """
    run(compose_command("exec", "-T", BACKEND_SERVICE, "mkdir", "-p", CONTAINER_SCRIPT_DIR), timeout=60)
    for path in (script, *support):
        run(compose_command("cp", str(path), f"{BACKEND_SERVICE}:{CONTAINER_SCRIPT_DIR}/{path.name}"), timeout=60)
    command = compose_command(
        "exec",
        "-T",
        "-w",
        "/app",
        "-e",
        "PYTHONPATH=/app",
        BACKEND_SERVICE,
        "python",
        f"{CONTAINER_SCRIPT_DIR}/{script.name}",
        *args,
    )
    result = run(command, timeout=timeout)
    sys.stderr.write(result.stderr.decode("utf-8", "replace"))
    return result.stdout.decode("utf-8")


# ── The stack record ────────────────────────────────────────────────────────


def stack_file() -> Path:
    return reach_dir() / "stack.json"


def read_stack() -> dict[str, Any]:
    path = stack_file()
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:stack:up` first")
    return json.loads(path.read_text(encoding="utf-8"))


def subject_file(subject: str) -> Path:
    return reach_dir() / "subjects" / f"{subject}.json"


def read_subject(subject: str) -> dict[str, Any]:
    path = subject_file(subject)
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:privacy-subject` first")
    return json.loads(path.read_text(encoding="utf-8"))


# ── HTTP ────────────────────────────────────────────────────────────────────


def http_json(
    method: str,
    url: str,
    *,
    body: object | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = HTTP_TIMEOUT_SECONDS,
) -> tuple[int, Any]:
    """One JSON request; returns ``(status, parsed body or None)``. Never raises on a 4xx/5xx."""
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        parsed = json.loads(raw) if raw else None
    except ValueError:
        parsed = raw.decode("utf-8", "replace")
    return status, parsed


class Arango:
    """Minimal ArangoDB HTTP client for the observation side (no python-arango on the host)."""

    def __init__(self, stack: dict[str, Any]) -> None:
        arango = stack["arangodb"]
        self._base = f"{arango['url']}/_db/{arango['database']}"
        token = base64.b64encode(f"{arango['username']}:{arango['password']}".encode()).decode()
        self._headers = {"Authorization": f"Basic {token}"}

    def request(self, method: str, path: str, body: object | None = None) -> Any:
        status, parsed = http_json(method, f"{self._base}{path}", body=body, headers=self._headers)
        if status >= 400:
            raise ReachError(f"ArangoDB {method} {path} answered {status}: {parsed}")
        return parsed

    def aql(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[Any]:
        """Run *query* and drain every batch of its cursor."""
        page = self.request("POST", "/_api/cursor", {"query": query, "bindVars": bind_vars or {}, "batchSize": 1000})
        rows = list(page.get("result", []))
        while page.get("hasMore"):
            page = self.request("POST", f"/_api/cursor/{page['id']}")
            rows.extend(page.get("result", []))
        return rows

    def document(self, document_id: str) -> dict[str, Any] | None:
        status, parsed = http_json("GET", f"{self._base}/_api/document/{document_id}", headers=self._headers)
        if status == 404:
            return None
        if status >= 400:
            raise ReachError(f"ArangoDB GET document {document_id} answered {status}: {parsed}")
        return parsed

    def collections(self) -> set[str]:
        listing = self.request("GET", "/_api/collection?excludeSystem=true")
        return {entry["name"] for entry in listing.get("result", [])}

    def slow_queries(self) -> list[dict[str, Any]]:
        """ArangoDB's own list of tracked queries for this database (threshold 0: all of them)."""
        return list(self.request("GET", "/_api/query/slow"))

    def mark(self, label: str) -> None:
        """Leave a marker in the query log so a later reader can split it by phase."""
        self.aql("RETURN @reach_marker", {"reach_marker": label})


def wait_until(predicate, *, timeout: float, interval: float = 2.0, what: str) -> Any:
    """Poll *predicate* until it returns a truthy value or *timeout* passes."""
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() > deadline:
            raise ReachError(f"timed out after {timeout:.0f}s waiting for {what}")
        time.sleep(interval)
