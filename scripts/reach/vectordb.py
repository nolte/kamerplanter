#!/usr/bin/env python3
"""Start, seed and stop the pgvector reference index for the Art. 17 Phase 0.5 probe (#1745).

The DINOv2 reference index is the inference-service's ``species_embeddings``
table in PostgreSQL + pgvector (``src/inference-service/app/vectordb/``). User
reference contributions land there with ``source = 'user_contributed'``,
``contributed_by`` and ``tenant_key`` (``SpeciesEmbeddingRepository.upsert_reference``),
and REQ-025 Phase 0.5 is the erasure step that has to remove them.

The reach stack's backend is **not** wired to this store, and cannot be: Phase
0.5 calls ``get_reference_index_store()`` (``app/common/dependencies.py``), which
returns ``NoopReferenceIndexStore`` unconditionally — there is no setting, URL or
binding that would point it at a database. So this helper does not plug the
store into the backend; it stands up the store the product writes contributions
into, so that the observation after an erasure shows what the erasure did to it
(``observe_reference_index.py``). Wiring the backend is the product's change to
make, not the environment's.

``up`` builds ``docker/vectordb`` (PostgreSQL 18 + pgvector) from this working
copy, runs it, waits — bounded — until the server accepts TCP connections (the
image's init phase runs a socket-only server first), applies the
inference-service's migrations in order with ``ON_ERROR_STOP``, and records
``.reach/vectordb.json``. No port is published: every access goes through
``docker exec … psql`` over the container's own socket.

``seed --subject`` inserts two rows: the subject's contribution, with the
column set ``upsert_reference`` writes (``is_active = false``: contributions are
quarantined until an admin activates them), and one curated control row
(``source = 'gbif'``, no ``contributed_by``) an erasure must leave alone. The
subject and its tenant go in as psql variables, never as SQL text. The row ids
are recorded in ``.reach/subjects/<subject>.embeddings.json``.

``down`` removes the container with its anonymous data volume and the record.
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
    DEFAULT_SUBJECT,
    ReachError,
    log,
    project_name,
    reach_dir,
    read_subject,
    repo_root,
    run,
)

DATABASE = "kamerplanter_vectors_reach"
USER = "postgres"
#: Test-only value for this throw-away container; nothing outside it uses it.
PASSWORD = "reach-test-password"
DIMENSIONS = 384
#: A cold build compiles pgvector from source.
BUILD_TIMEOUT_SECONDS = 1200
READY_TIMEOUT_SECONDS = 120
PSQL_TIMEOUT_SECONDS = 60

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


def up() -> None:
    container, image = _names()
    reach_dir().mkdir(parents=True, exist_ok=True)
    log(f"building docker/vectordb as {image}")
    run(["docker", "build", "-t", image, str(repo_root() / "docker" / "vectordb")], timeout=BUILD_TIMEOUT_SECONDS)
    run(["docker", "rm", "-f", "-v", container], timeout=60, check=False)
    run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container,
            "-e",
            f"POSTGRES_PASSWORD={PASSWORD}",
            "-e",
            f"POSTGRES_USER={USER}",
            "-e",
            f"POSTGRES_DB={DATABASE}",
            image,
        ],
        timeout=120,
    )
    # The entrypoint's init phase runs a server on the socket only; TCP answers
    # once the real server is up, so readiness is asked over 127.0.0.1.
    ready = ["docker", "exec", container, "pg_isready", "-h", "127.0.0.1", "-U", USER, "-d", DATABASE]
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while run(ready, timeout=30, check=False).returncode != 0:
        if time.monotonic() > deadline:
            raise ReachError(f"{container} did not accept connections within {READY_TIMEOUT_SECONDS}s")
        time.sleep(2)
    record = {"container": container, "database": DATABASE, "user": USER}
    migrations = sorted((repo_root() / "src" / "inference-service" / "app" / "vectordb" / "migrations").glob("*.sql"))
    if not migrations:
        raise ReachError("no inference-service vectordb migrations found")
    for migration in migrations:
        psql(record, migration.read_text(encoding="utf-8"))
        log(f"applied {migration.name}")
    record_file().write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    log(f"reference index {container} up with {len(migrations)} migrations")


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
    run(["docker", "rm", "-f", "-v", container], timeout=120, check=False)
    record_file().unlink(missing_ok=True)
    log(f"reference index container {container} removed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("up", help="build and start the store and apply the migrations")
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
