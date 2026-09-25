#!/usr/bin/env python3
"""Stand the capability-reach T2 stack up, seed it, and take it down (#1680).

Invoked by the Taskfile targets in ``.taskfiles/reach.yaml``; not meant to be
called by hand, though it can be::

    python3 scripts/reach/stack.py up
    python3 scripts/reach/stack.py seed --subject reach-subject
    python3 scripts/reach/stack.py seed-files --subject reach-subject
    python3 scripts/reach/stack.py seed-shared-file --subject reach-subject
    python3 scripts/reach/stack.py seed-tenant --tenant reach-tenant --control reach-control-tenant
    python3 scripts/reach/stack.py down

``up`` starts the E2E stack's full-mode services (``docker-compose.e2e.yml``)
with the ``docker-compose.reach.yml`` overlay under a project name unique to this
working copy, waits for them, and records the host-side addresses in
``.reach/stack.json``. ``seed`` runs ``seed_privacy_subject.py`` inside the
backend container and stores its record under ``.reach/subjects/``.
``seed-files`` runs ``seed_stored_files.py`` there for a subject ``seed`` already
wrote — one photo with GPS EXIF per attachment category in the subject's tenant —
and stores ``.reach/subjects/<subject>.files.json``. ``seed-shared-file`` runs
``seed_shared_file.py`` there — the subject and a co-holder upload the same photo
into a shared tenant (#1770) — and stores ``.reach/subjects/<subject>.shared.json``.
``seed-tenant`` runs
``seed_tenant_for_erasure.py`` there — a tenant and a control tenant with a row
in every tenant-erasure inventory collection (#1769) — and stores
``.reach/subjects/tenant-<tenant>.json``. ``down`` removes
containers, networks and volumes and clears ``.reach/``'s run state.

A reach environment target's job is to make the system exist, not to say
anything about reach: every failure here exits non-zero, and the audit's runner
reports that probe *not probed* with this output, never *not reached*.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import (  # noqa: E402 — sibling import after the path insert
    BACKEND_SERVICE,
    DEFAULT_SUBJECT,
    STACK_SERVICES,
    Arango,
    ReachError,
    compose_command,
    http_json,
    log,
    project_name,
    reach_dir,
    read_stack,
    read_subject,
    repo_root,
    run,
    run_in_backend,
    stack_file,
    subject_file,
    wait_until,
)

#: ``docker compose up --wait`` bound. The backend runs the full-mode seed before
#: uvicorn binds (see the healthcheck comment in docker-compose.e2e.yml), and a
#: first run builds two images.
UP_TIMEOUT_SECONDS = 840

#: The values docker-compose.e2e.yml sets for the full-mode services. Test-only.
ARANGO_DATABASE = "kamerplanter_e2e_full"
ARANGO_USERNAME = "root"
ARANGO_PASSWORD = "e2e-test-password"
#: Entries ArangoDB keeps in the database's query log (its maximum).
QUERY_LOG_LENGTH = 16384


def _published(service: str, port: int) -> str:
    """``http://127.0.0.1:<host port>`` of a container port Docker published."""
    result = run(compose_command("port", service, str(port)), timeout=30)
    address = result.stdout.decode("utf-8").strip().splitlines()[0]
    host, _, host_port = address.rpartition(":")
    host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    return f"http://{host}:{host_port}"


def up() -> None:
    reach = reach_dir()
    (reach / "storage").mkdir(parents=True, exist_ok=True)
    (reach / "subjects").mkdir(parents=True, exist_ok=True)
    log(f"starting {', '.join(STACK_SERVICES)} as compose project {project_name()}")
    run(
        compose_command("up", "-d", "--build", "--wait", "--wait-timeout", str(UP_TIMEOUT_SECONDS), *STACK_SERVICES),
        timeout=UP_TIMEOUT_SECONDS + 600,
    )
    stack = {
        "project": project_name(),
        "api_url": _published(BACKEND_SERVICE, 8000),
        "arangodb": {
            "url": _published("arangodb", 8529),
            "database": ARANGO_DATABASE,
            "username": ARANGO_USERNAME,
            "password": ARANGO_PASSWORD,
        },
        "storage_root": str(reach / "storage" / "attachments"),
    }

    def api_live() -> bool:
        try:
            status, _ = http_json("GET", f"{stack['api_url']}/api/v1/health/live", timeout=5)
        except (urllib.error.URLError, OSError) as exc:
            del exc  # not listening yet
            return False
        return status == 200

    wait_until(api_live, timeout=120, what="the API to answer on its published port")
    # The query log is per database and holds 64 entries by default; arangod has
    # no startup option for its length. 16384 is the server's ceiling and far
    # more than one export plus one erasure issue.
    Arango(stack).request("PUT", "/_api/query/properties", {"maxSlowQueries": QUERY_LOG_LENGTH})
    stack_file().write_text(json.dumps(stack, indent=2) + "\n", encoding="utf-8")
    log(f"stack up: API {stack['api_url']}, ArangoDB {stack['arangodb']['url']}")


def down() -> None:
    run(compose_command("down", "-v", "--remove-orphans", "--timeout", "10"), timeout=300)
    reach = reach_dir()
    stack_file().unlink(missing_ok=True)
    for tree in ("storage", "subjects"):
        shutil.rmtree(reach / tree, ignore_errors=True)
    log(f"stack {project_name()} removed with its volumes")


def seed(subject: str) -> None:
    read_stack()  # refuse early, with the right message, when the stack is not up
    scripts = repo_root() / "scripts"
    output = run_in_backend(
        scripts / "reach" / "seed_privacy_subject.py",
        "--subject",
        subject,
        # The seed places each collection in its model the way the inventory
        # guard does; it reuses that reader rather than carrying a copy. The
        # support tuple is the guard's import closure: it imports the
        # repository-binding reader since #1712.
        support=(
            scripts / "check_privacy_inventory.py",
            scripts / "arango_repository_bindings.py",
            scripts / "source_text.py",
        ),
        timeout=300,
    )
    record = json.loads(output)
    path = subject_file(subject)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    collections = sorted({row["collection"] for row in record["rows"]})
    log(f"seeded subject {subject!r}: {len(record['rows'])} rows in {len(collections)} collections -> {path}")


def seed_files(subject: str) -> None:
    read_stack()
    tenant_key = read_subject(subject)["tenant_key"]
    reach = repo_root() / "scripts" / "reach"
    output = run_in_backend(
        reach / "seed_stored_files.py",
        "--subject",
        subject,
        "--tenant-key",
        tenant_key,
        # The seed checks the stored bytes with the observer's own EXIF reader.
        support=(reach / "observe_storage_residue.py", reach / "_reach_common.py"),
        timeout=300,
    )
    record = json.loads(output)
    path = subject_file(subject).with_name(f"{subject}.files.json")
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    refused = ", ".join(record["refused"]) or "none"
    log(f"seeded {len(record['files'])} stored files for {subject!r} (refused categories: {refused}) -> {path}")


def seed_shared_file(subject: str) -> None:
    """The subject and a co-holder upload the same photo into a shared tenant (#1770)."""
    read_stack()
    read_subject(subject)  # the subject must exist: its erasure is what the probe observes
    output = run_in_backend(
        repo_root() / "scripts" / "reach" / "seed_shared_file.py", "--subject", subject, timeout=300
    )
    record = json.loads(output)
    path = subject_file(subject).with_name(f"{subject}.shared.json")
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"seeded a photo {subject!r} shares with {record['co_holder']!r} in tenant {record['tenant_key']!r} -> {path}")


def seed_tenant(tenant: str, control: str, personal_of: str | None = None) -> None:
    """Seed a tenant and a control tenant into every tenant-erasure inventory collection (#1769).

    ``personal_of`` seeds the tenant as that account's personal tenant, the
    account its only member (#1788).
    """
    read_stack()
    scripts = repo_root() / "scripts"
    output = run_in_backend(
        scripts / "reach" / "seed_tenant_for_erasure.py",
        "--tenant",
        tenant,
        "--control",
        control,
        *(("--personal-of", personal_of) if personal_of else ()),
        # The model-valid row builder of the subject seed, and its import closure.
        support=(
            scripts / "reach" / "seed_privacy_subject.py",
            scripts / "check_privacy_inventory.py",
            scripts / "arango_repository_bindings.py",
            scripts / "source_text.py",
        ),
        timeout=300,
    )
    record = json.loads(output)
    path = subject_file(f"tenant-{tenant}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"seeded tenant {tenant!r} and control {control!r}: {len(record['rows'])} rows -> {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("up", help="start the stack and record its addresses")
    sub.add_parser("down", help="remove the stack, its volumes and the run state")
    seed_parser = sub.add_parser("seed", help="seed one data subject into every declared collection")
    seed_parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    files_parser = sub.add_parser("seed-files", help="upload one GPS-EXIF photo per attachment category")
    files_parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    shared_parser = sub.add_parser("seed-shared-file", help="the subject and a co-holder upload the same photo")
    shared_parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    tenant_parser = sub.add_parser("seed-tenant", help="seed a tenant and a control tenant for the tenant erasure")
    tenant_parser.add_argument("--tenant", required=True)
    tenant_parser.add_argument("--control", required=True)
    tenant_parser.add_argument("--personal-of", default=None, help="seed it as this account's personal tenant (#1788)")
    args = parser.parse_args(argv)
    try:
        if args.command == "up":
            up()
        elif args.command == "down":
            down()
        elif args.command == "seed-files":
            seed_files(args.subject)
        elif args.command == "seed-shared-file":
            seed_shared_file(args.subject)
        elif args.command == "seed-tenant":
            seed_tenant(args.tenant, args.control, args.personal_of)
        else:
            seed(args.subject)
    except ReachError as exc:
        print(f"reach stack: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
