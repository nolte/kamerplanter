#!/usr/bin/env python3
"""Start and stop the cross-encoder ranking service for its T1 reach probe (#1680).

``up`` builds ``docker/reranker-service`` from this working copy at the target
the compose file uses (``bge-reranker-v2-m3``, ADR-007), runs it with its port
published on 127.0.0.1 at a port Docker picks, and writes the base URL to
``.reach/ranking.url``. It deliberately does **not** wait for ``/ready`` or the
image's ``HEALTHCHECK``: those are the service's statements about itself, and
#1609 was exactly a ``HEALTHCHECK`` that reported healthy while ``/ready``
answered 503 for ever. The probe's observation polls ``/rerank`` itself.

``down`` removes the container and the URL file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import ReachError, log, project_name, reach_dir, repo_root, run  # noqa: E402

BUILD_TARGET = "bge-reranker-v2-m3"
CONTAINER_PORT = 8081
#: A cold build exports the model to ONNX; a cached one takes seconds.
BUILD_TIMEOUT_SECONDS = 3000


def _names() -> tuple[str, str]:
    name = f"{project_name()}-ranking"
    return name, f"{name}:local"


def url_file() -> Path:
    return reach_dir() / "ranking.url"


def up() -> None:
    container, image = _names()
    reach_dir().mkdir(parents=True, exist_ok=True)
    log(f"building {BUILD_TARGET} from docker/reranker-service as {image}")
    run(
        ["docker", "build", "--target", BUILD_TARGET, "-t", image, str(repo_root() / "docker" / "reranker-service")],
        timeout=BUILD_TIMEOUT_SECONDS,
    )
    run(["docker", "rm", "-f", container], timeout=60, check=False)
    run(["docker", "run", "-d", "--name", container, "-p", f"127.0.0.1::{CONTAINER_PORT}", image], timeout=120)
    address = run(["docker", "port", container, str(CONTAINER_PORT)], timeout=30).stdout.decode().split()[0]
    host, _, port = address.rpartition(":")
    url = f"http://{'127.0.0.1' if host in ('0.0.0.0', '') else host}:{port}"
    url_file().write_text(url + "\n", encoding="utf-8")
    log(f"ranking service container {container} started at {url} (readiness not awaited)")


def down() -> None:
    container, _ = _names()
    run(["docker", "rm", "-f", container], timeout=120, check=False)
    url_file().unlink(missing_ok=True)
    log(f"ranking service container {container} removed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("up", "down"))
    args = parser.parse_args(argv)
    try:
        up() if args.command == "up" else down()
    except ReachError as exc:
        print(f"reach ranking: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
