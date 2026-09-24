#!/usr/bin/env python3
"""Probe the HTTP contract of a built ONNX sidecar image (#1725).

    scripts/ci/probe_model_service_contract.py <image> reranker
    scripts/ci/probe_model_service_contract.py <image> embedding

``scripts/ci/smoke_model_image.sh`` proves that the image becomes READY. This
proves that a ready image SERVES its contract — a correct answer for a normal
request, the empty-list answer, a 422 for a request one past EACH bound in
``docker/<service>/limits.py`` (whose error list names the field and does not
echo the input), and a 413 for a body whose ``Content-Length`` exceeds the
image's own ``MAX_BODY_BYTES``:

reranker
    ``POST /rerank`` with a query and three documents, exactly one of them about
    the query → 200 and that document ranked first; ``documents: []`` → 200
    ``{"results": []}``; 101 documents, a 4097-character query, a
    16385-character document, ``top_k`` 51 and ``top_k`` 0 → 422 each.
embedding
    ``POST /embed`` with two texts → 200, two distinct L2-normalised vectors of
    the model's hidden size (read from the ``config.json`` shipped in the image,
    so the probe holds for every ``--target``); ``texts: []`` → 200 with no
    embeddings; 65 texts, a 16385-character text, a 65-character prefix and a
    129-character model → 422 each.
both
    A declared ``Content-Length`` of ``MAX_BODY_BYTES + 1`` (read from the
    image's ``limits.py``, so the probe and the image cannot disagree) → 413,
    answered from the headers alone: the probe sends no body at all.

The container is started exactly as the chart runs it and as the smoke script
starts it: read-only root filesystem, a 64 MiB tmpfs on /tmp, no capabilities,
no privilege escalation, UID 1000. A bound that only holds on a writable image,
or an answer that needs root, is therefore a red here and not a crash-loop in
the cluster.

Standard library only: it runs on a bare CI runner next to ``docker``. On
failure the container logs are printed, because the service's traceback is the
only place the cause appears.
"""

from __future__ import annotations

import http.client
import json
import math
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

#: How long the model may take to load (the image's own HEALTHCHECK start period).
READY_TIMEOUT_SECONDS = 300
POLL_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 120

PORTS = {"reranker": 8081, "embedding": 8080}

#: The same flags as scripts/ci/smoke_model_image.sh — the chart's runtime shape.
HARDENED_RUN = [
    "--read-only",
    "--tmpfs",
    "/tmp:rw,noexec,nosuid,size=64m",
    "--cap-drop",
    "ALL",
    "--security-opt",
    "no-new-privileges",
    "--user",
    "1000:1000",
]


class ProbeError(Exception):
    """A contract assertion did not hold."""


def _docker(*args: str, timeout: float = 120) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise ProbeError(f"docker {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _request(url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    """``(status, parsed JSON body)``; a non-2xx status is returned, not raised."""
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, body = exc.code, exc.read()
    try:
        return status, json.loads(body) if body else None
    except json.JSONDecodeError:
        return status, body.decode(errors="replace")


def _wait_ready(base: str) -> None:
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    last = "(never answered)"
    while time.monotonic() < deadline:
        try:
            status, body = _request(f"{base}/ready")
            if status == 200:
                return
            last = f"{status} {body}"
        except (urllib.error.URLError, OSError) as exc:
            last = str(exc)
        time.sleep(POLL_SECONDS)
    raise ProbeError(f"{base}/ready never answered 200 within {READY_TIMEOUT_SECONDS}s (last: {last})")


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ProbeError(message)
    print(f"probe: ok — {message}")


def _expect_refused(base: str, path: str, payload: dict[str, Any], what: str) -> None:
    """422, with an error list that names fields and carries no ``input`` (the default handler echoes it)."""
    status, body = _request(f"{base}{path}", payload)
    _expect(status == 422, f"{what} is refused with 422 (got {status})")
    detail = body.get("detail") if isinstance(body, dict) else None
    _expect(
        isinstance(detail, list) and detail and all(set(error) == {"loc", "type", "msg"} for error in detail),
        f"the 422 for {what} carries loc/type/msg only, no input (got {str(body)[:200]})",
    )


def _image_constant(image: str, name: str) -> int:
    """An integer from the ``limits.py`` the image ships — the value the running service uses."""
    script = f"import limits; print(limits.{name})"
    return int(_docker("run", "--rm", *HARDENED_RUN, "--entrypoint", "python", image, "-c", script))


def _expect_body_cap(base: str, path: str, image: str) -> None:
    """A declared Content-Length one past the cap is answered 413 before any body is sent."""
    cap = _image_constant(image, "MAX_BODY_BYTES")
    host, port = base.removeprefix("http://").rsplit(":", 1)
    connection = http.client.HTTPConnection(host, int(port), timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        connection.putrequest("POST", path)
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(cap + 1))
        connection.endheaders()
        status = connection.getresponse().status
    finally:
        connection.close()
    _expect(
        status == 413, f"a declared body of {cap + 1} bytes (MAX_BODY_BYTES + 1) is refused with 413 (got {status})"
    )


def probe_reranker(base: str, image: str) -> None:
    documents = [
        "Car engines need regular oil changes to keep running smoothly.",
        "Tomato plants need deep, regular watering, especially while their fruit is setting.",
        "The stock market closed higher on Friday after a volatile week.",
    ]
    status, body = _request(
        f"{base}/rerank",
        {"query": "How often should I water my tomato plants?", "documents": documents, "top_k": 3},
    )
    _expect(status == 200, f"POST /rerank with 3 documents answers 200 (got {status}: {body})")
    ranking = [result["index"] for result in body["results"]]
    _expect(sorted(ranking) == [0, 1, 2], f"all 3 documents are ranked exactly once (got {ranking})")
    _expect(ranking[0] == 1, f"the tomato-watering document ranks first (got order {ranking})")

    status, body = _request(f"{base}/rerank", {"query": "anything", "documents": []})
    _expect(
        status == 200 and body.get("results") == [], f'documents: [] answers 200 {{"results": []}} ({status}: {body})'
    )

    _expect_refused(base, "/rerank", {"query": "q", "documents": ["d"] * 101}, "101 documents")
    _expect_refused(base, "/rerank", {"query": "q" * 4097, "documents": ["d"]}, "a 4097-character query")
    _expect_refused(base, "/rerank", {"query": "q", "documents": ["d" * 16385]}, "a 16385-character document")
    _expect_refused(base, "/rerank", {"query": "q", "documents": ["d"], "top_k": 51}, "top_k 51")
    _expect_refused(base, "/rerank", {"query": "q", "documents": ["d"], "top_k": 0}, "top_k 0")
    _expect_body_cap(base, "/rerank", image)


def _hidden_size(image: str) -> int:
    """The embedding width of the model the image ships, from its own config.json."""
    script = (
        "import json, os; "
        "print(json.load(open(f\"/app/models/onnx/{os.environ['EMBEDDING_MODEL']}/config.json\"))['hidden_size'])"
    )
    return int(_docker("run", "--rm", *HARDENED_RUN, "--entrypoint", "python", image, "-c", script))


def probe_embedding(base: str, image: str) -> None:
    dimension = _hidden_size(image)
    texts = ["Tomato plants need regular watering.", "Der Motor des Autos ist kaputt."]
    status, body = _request(f"{base}/embed", {"texts": texts, "prefix": "passage: "})
    _expect(status == 200, f"POST /embed with 2 texts answers 200 (got {status}: {body})")
    vectors = body["embeddings"]
    _expect(len(vectors) == 2, f"2 embeddings come back (got {len(vectors)})")
    _expect(
        all(len(vector) == dimension for vector in vectors) and body["dimensions"] == dimension,
        f"both have the model's hidden size {dimension} (got {[len(v) for v in vectors]}, "
        f"dimensions={body['dimensions']})",
    )
    norms = [math.sqrt(sum(value * value for value in vector)) for vector in vectors]
    _expect(all(abs(norm - 1.0) < 1e-3 for norm in norms), f"both are L2-normalised (norms {norms})")
    _expect(vectors[0] != vectors[1], "the two texts get different vectors")

    status, body = _request(f"{base}/embed", {"texts": []})
    _expect(
        status == 200 and body.get("embeddings") == [] and body.get("dimensions") == 0,
        f"texts: [] answers 200 with no embeddings ({status}: {body})",
    )

    _expect_refused(base, "/embed", {"texts": ["t"] * 65}, "65 texts")
    _expect_refused(base, "/embed", {"texts": ["t" * 16385]}, "a 16385-character text")
    _expect_refused(base, "/embed", {"texts": ["t"], "prefix": "p" * 65}, "a 65-character prefix")
    _expect_refused(base, "/embed", {"texts": ["t"], "model": "m" * 129}, "a 129-character model")
    _expect_body_cap(base, "/embed", image)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[2] not in PORTS:
        print(f"usage: {argv[0]} <image> {{{'|'.join(PORTS)}}}", file=sys.stderr)
        return 2
    image, kind = argv[1], argv[2]
    port = PORTS[kind]

    try:
        container = _docker("run", "-d", "-p", f"127.0.0.1::{port}", *HARDENED_RUN, image)
    except ProbeError as exc:
        print(f"FAIL: {image} could not be started: {exc}", file=sys.stderr)
        return 1
    try:
        host_port = _docker("port", container, f"{port}/tcp").splitlines()[0].rsplit(":", 1)[1]
        base = f"http://127.0.0.1:{host_port}"
        print(f"probe: {image} ({kind}) at {base}")
        _wait_ready(base)
        if kind == "reranker":
            probe_reranker(base, image)
        else:
            probe_embedding(base, image)
    except (ProbeError, KeyError, TypeError, IndexError, ValueError, OSError) as exc:
        print(f"FAIL: {image} does not serve its {kind} contract: {exc!r}", file=sys.stderr)
        print("--- container logs ---", file=sys.stderr)
        subprocess.run(["docker", "logs", container], stdout=sys.stderr, stderr=sys.stderr, check=False, timeout=60)
        return 1
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False, timeout=60)
    print(f"probe: {image} serves its {kind} contract")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
