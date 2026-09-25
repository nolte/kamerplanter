#!/usr/bin/env python3
"""Start, seed and stop the pgvector reference index for the Art. 17 Phase 0.5 probe (#1745).

The DINOv2 reference index is the inference-service's ``species_embeddings``
table in PostgreSQL + pgvector (``src/inference-service/app/vectordb/``). User
reference contributions land there with ``source = 'user_contributed'``,
``contributed_by`` and ``tenant_key`` (``SpeciesEmbeddingRepository.upsert_reference``),
and REQ-025 Phase 0.5 is the erasure step that has to remove them.

Since #1753 the reach stack is wired to that store the way a deployment is.
``up`` runs the store and the product's inference-service (built from
``src/inference-service`` with its own Dockerfile) on the compose project's
network, lets the inference-service apply its migrations as it does in a
cluster, and recreates ``backend-full`` and ``celery-worker-full`` with
``INFERENCE_SERVICE_ENABLED``, ``INFERENCE_SERVICE_URL`` and the shared
``INTERNAL_SERVICE_TOKEN`` (an extra compose file under ``.reach/``). Phase 0.5
of the erasure therefore binds ``InferenceServiceReferenceIndexStore`` in the
worker and deletes through the service's erase endpoint; the observation after
the erasure shows what that did to the rows (``observe_reference_index.py``).
Before #1753 there was nothing to wire: ``get_reference_index_store()``
returned ``NoopReferenceIndexStore`` unconditionally.

``up`` builds ``docker/vectordb`` (PostgreSQL 18 + pgvector) and the
inference-service image from this working copy, waits — bounded — until the
store accepts TCP connections, the inference-service answers ``/health`` and
its migrations created ``species_embeddings``, then recreates the two backend
services and waits for the API. It records ``.reach/vectordb.json``. No port is
published: the helpers reach the store through ``docker exec … psql`` over the
container's own socket.

``seed --subject`` inserts two rows: the subject's contribution, with the
column set ``upsert_reference`` writes (``is_active = false``: contributions are
quarantined until an admin activates them), and one curated control row
(``source = 'gbif'``, no ``contributed_by``) an erasure must leave alone. The
subject and its tenant go in as psql variables, never as SQL text. The row ids
are recorded in ``.reach/subjects/<subject>.embeddings.json``.

``down`` removes both containers (the store with its anonymous data volume),
the compose override and the record. The recreated backend services are removed
with the rest of the stack by ``reach:stack:down``.
Like every reach environment step, a failure exits non-zero and the runner
reports the probe *not probed*.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    BACKEND_SERVICE,
    COMPOSE_FILES,
    COMPOSE_PROFILE,
    DEFAULT_SUBJECT,
    WORKER_SERVICE,
    ReachError,
    http_json,
    log,
    project_name,
    reach_dir,
    read_stack,
    read_subject,
    repo_root,
    run,
    stack_file,
    wait_until,
)

DATABASE = "kamerplanter_vectors_reach"
USER = "postgres"
#: Test-only value for this throw-away container; nothing outside it uses it.
PASSWORD = "reach-test-password"
DIMENSIONS = 384
#: A cold build compiles pgvector from source; the inference-service image
#: exports the DINOv2 ONNX model in its build.
BUILD_TIMEOUT_SECONDS = 1800
READY_TIMEOUT_SECONDS = 180
PSQL_TIMEOUT_SECONDS = 60
#: Network aliases on the compose project's network.
VECTORDB_ALIAS = "reach-vectordb"
INFERENCE_ALIAS = "reach-inference"
#: Test-only shared secret between the backend services and the inference-service.
SERVICE_TOKEN = "reach-internal-service-token-not-for-production"
#: The backend runs the full-mode seed again when it is recreated.
BACKEND_RECREATE_TIMEOUT_SECONDS = 840

#: The columns ``SpeciesEmbeddingRepository.upsert_reference`` inserts, in its order.
CONTRIBUTION_COLUMNS = (
    "species_key",
    "scientific_name",
    "organ",
    "embedding",
    "model",
    "source",
    "source_record_id",
    "license",
    "attribution",
    "source_url",
    "is_active",
    "contributed_by",
    "tenant_key",
    "contributed_at",
)

#: Both seeded rows; ``:'name'`` is psql's quoted variable interpolation.
SEED_SQL = f"""
INSERT INTO species_embeddings ({", ".join(CONTRIBUTION_COLUMNS)})
VALUES ('reach-species', 'Reach contributed species', 'leaf', :'contributed_vector'::vector, 'dinov2_vits14',
        'user_contributed', :'contributed_record', NULL, NULL, NULL,
        false, :'subject', :'tenant_key', now())
RETURNING id;
INSERT INTO species_embeddings ({", ".join(CONTRIBUTION_COLUMNS)})
VALUES ('reach-species', 'Reach curated species', 'leaf', :'curated_vector'::vector, 'dinov2_vits14',
        'gbif', :'curated_record', 'CC-BY-4.0', 'reach control row', NULL,
        true, NULL, NULL, NULL)
RETURNING id;
"""


def vector_literal(seed: str) -> str:
    """A deterministic, L2-normalised 384-dimensional pgvector literal (pure; unit-tested)."""
    raw: list[float] = []
    counter = 0
    while len(raw) < DIMENSIONS:
        digest = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
        raw.extend((byte - 127.5) / 127.5 for byte in digest)
        counter += 1
    raw = raw[:DIMENSIONS]
    norm = math.sqrt(sum(value * value for value in raw))
    return "[" + ",".join(repr(value / norm) for value in raw) + "]"


def _names() -> tuple[str, str]:
    name = f"{project_name()}-vectordb"
    return name, f"{name}:local"


def _inference_names() -> tuple[str, str]:
    name = f"{project_name()}-inference"
    return name, f"{name}:local"


def _network() -> str:
    """The compose project's default network, which the backend services are on."""
    return f"{project_name()}_default"


def override_file() -> Path:
    return reach_dir() / "inference.override.yml"


def backend_override() -> str:
    """Compose override wiring the API and the worker to the reach inference-service (pure; unit-tested).

    Both services get the same three values: the scheduled Art. 17 erasure runs
    in the worker, the contribution route in the API (#1753).
    """
    lines = ["services:"]
    for service in (BACKEND_SERVICE, WORKER_SERVICE):
        lines += [
            f"  {service}:",
            "    environment:",
            '      INFERENCE_SERVICE_ENABLED: "true"',
            f'      INFERENCE_SERVICE_URL: "http://{INFERENCE_ALIAS}:8000"',
            f'      INTERNAL_SERVICE_TOKEN: "{SERVICE_TOKEN}"',
        ]
    return "\n".join(lines) + "\n"


def record_file() -> Path:
    return reach_dir() / "vectordb.json"


def read_record() -> dict[str, Any]:
    path = record_file()
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:vectordb:up` first")
    return json.loads(path.read_text(encoding="utf-8"))


def embeddings_file(subject: str) -> Path:
    return reach_dir() / "subjects" / f"{subject}.embeddings.json"


def psql(record: dict[str, Any], sql: str, variables: dict[str, str] | None = None) -> str:
    """Run *sql* in the store over ``docker exec``; tuples only, unaligned. Raises on any SQL error."""
    command = ["docker", "exec", "-i", record["container"], "psql", "-U", record["user"], "-d", record["database"]]
    command += ["-v", "ON_ERROR_STOP=1", "-X", "-q", "-A", "-t"]
    for name, value in (variables or {}).items():
        command += ["-v", f"{name}={value}"]
    result = run([*command, "-f", "-"], stdin=sql.encode("utf-8"), timeout=PSQL_TIMEOUT_SECONDS)
    return result.stdout.decode("utf-8")


def _wait(what: str, check: list[str], timeout: float = READY_TIMEOUT_SECONDS) -> None:
    deadline = time.monotonic() + timeout
    while run(check, timeout=30, check=False).returncode != 0:
        if time.monotonic() > deadline:
            raise ReachError(f"{what} within {timeout:.0f}s")
        time.sleep(2)


def up() -> None:
    container, image = _names()
    inference, inference_image = _inference_names()
    network = _network()
    reach_dir().mkdir(parents=True, exist_ok=True)
    if run(["docker", "network", "inspect", network], timeout=30, check=False).returncode != 0:
        raise ReachError(f"network {network} is missing; run `task reach:stack:up` first")

    log(f"building docker/vectordb as {image}")
    run(["docker", "build", "-t", image, str(repo_root() / "docker" / "vectordb")], timeout=BUILD_TIMEOUT_SECONDS)
    log(f"building src/inference-service as {inference_image}")
    run(
        ["docker", "build", "-t", inference_image, str(repo_root() / "src" / "inference-service")],
        timeout=BUILD_TIMEOUT_SECONDS,
    )

    run(["docker", "rm", "-f", "-v", inference, container], timeout=60, check=False)
    run(
        [
            "docker", "run", "-d", "--name", container,
            "--network", network, "--network-alias", VECTORDB_ALIAS,
            "-e", f"POSTGRES_PASSWORD={PASSWORD}",
            "-e", f"POSTGRES_USER={USER}",
            "-e", f"POSTGRES_DB={DATABASE}",
            image,
        ],
        timeout=120,
    )  # fmt: skip
    # The entrypoint's init phase runs a server on the socket only; TCP answers
    # once the real server is up, so readiness is asked over 127.0.0.1.
    _wait(
        f"{container} did not accept connections",
        ["docker", "exec", container, "pg_isready", "-h", "127.0.0.1", "-U", USER, "-d", DATABASE],
    )

    run(
        [
            "docker", "run", "-d", "--name", inference,
            "--network", network, "--network-alias", INFERENCE_ALIAS,
            "-e", f"VECTORDB_HOST={VECTORDB_ALIAS}",
            "-e", f"VECTORDB_DATABASE={DATABASE}",
            "-e", f"VECTORDB_USERNAME={USER}",
            "-e", f"VECTORDB_PASSWORD={PASSWORD}",
            "-e", f"INTERNAL_SERVICE_TOKEN={SERVICE_TOKEN}",
            inference_image,
        ],
        timeout=120,
    )  # fmt: skip
    # /health answers once the lifespan ran — after the store connection and the
    # service's own migrations, which is what the probe needs; the model load
    # (non-blocking) is irrelevant to the erase endpoints.
    health = "import sys,urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"
    _wait(f"{inference} did not answer /health", ["docker", "exec", inference, "python", "-c", health])

    record = {"container": container, "database": DATABASE, "user": USER, "inference": inference}
    tables = psql(record, "SELECT to_regclass('public.species_embeddings') IS NOT NULL;").strip()
    if tables != "t":
        raise ReachError(f"the inference-service did not create species_embeddings (psql answered {tables!r})")

    override_file().write_text(backend_override(), encoding="utf-8")
    compose = ["docker", "compose", "-p", project_name()]
    for name in COMPOSE_FILES:
        compose += ["-f", str(repo_root() / name)]
    compose += ["-f", str(override_file()), "--profile", COMPOSE_PROFILE]
    log(f"recreating {BACKEND_SERVICE} and {WORKER_SERVICE} wired to {INFERENCE_ALIAS}")
    run(
        [
            *compose, "up", "-d", "--no-deps", "--no-build", "--force-recreate",
            "--wait", "--wait-timeout", str(BACKEND_RECREATE_TIMEOUT_SECONDS),
            BACKEND_SERVICE, WORKER_SERVICE,
        ],
        timeout=BACKEND_RECREATE_TIMEOUT_SECONDS + 60,
    )  # fmt: skip
    _repoint_api(compose)
    record_file().write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log(f"reference index {container} and inference-service {inference} up; backend services wired")


def _repoint_api(compose: list[str]) -> None:
    """Record the recreated API's new host port in ``.reach/stack.json`` and wait until it answers.

    The overlay publishes ``127.0.0.1::8000``: Docker picks a fresh host port on
    every (re)creation, so the address ``reach:stack:up`` recorded is gone.
    """
    result = run([*compose, "port", BACKEND_SERVICE, "8000"], timeout=30)
    address = result.stdout.decode("utf-8").strip().splitlines()[0]
    host, _, host_port = address.rpartition(":")
    host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    stack = read_stack()
    stack["api_url"] = f"http://{host}:{host_port}"
    stack_file().write_text(json.dumps(stack, indent=2) + "\n", encoding="utf-8")

    def api_live() -> bool:
        try:
            status, _ = http_json("GET", f"{stack['api_url']}/api/v1/health/live", timeout=5)
        except OSError:
            return False
        return status == 200

    wait_until(api_live, timeout=120, what="the recreated API to answer on its published port")


def seed(subject: str) -> None:
    record = read_record()
    tenant_key = read_subject(subject)["tenant_key"]
    token = hashlib.sha256(f"{project_name()}:{subject}".encode()).hexdigest()[:12]
    output = psql(
        record,
        SEED_SQL,
        {
            "subject": subject,
            "tenant_key": tenant_key,
            "contributed_record": f"reach-contribution-{token}",
            "curated_record": f"reach-curated-{token}",
            "contributed_vector": vector_literal("reach-contributed"),
            "curated_vector": vector_literal("reach-curated"),
        },
    )
    ids = [int(line) for line in output.split() if line.strip()]
    if len(ids) != 2:
        raise ReachError(f"expected two inserted row ids, psql printed {output!r}")
    path = embeddings_file(subject)
    path.parent.mkdir(parents=True, exist_ok=True)
    seeded = {"subject": subject, "tenant_key": tenant_key, "contributed_id": ids[0], "curated_id": ids[1]}
    path.write_text(json.dumps(seeded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"seeded contribution {ids[0]} and curated control row {ids[1]} -> {path}")


def down() -> None:
    container, _ = _names()
    inference, _ = _inference_names()
    run(["docker", "rm", "-f", "-v", inference, container], timeout=120, check=False)
    record_file().unlink(missing_ok=True)
    override_file().unlink(missing_ok=True)
    log(f"reference index container {container} and inference-service {inference} removed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("up", help="build and start the store and the inference-service, wire the backend")
    sub.add_parser("down", help="remove the store and its record")
    seed_parser = sub.add_parser("seed", help="insert the subject's contribution and a curated control row")
    seed_parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    args = parser.parse_args(argv)
    try:
        if args.command == "up":
            up()
        elif args.command == "down":
            down()
        else:
            seed(args.subject)
    except ReachError as exc:
        print(f"reach vectordb: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
