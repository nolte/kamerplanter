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
golden outputs (#1763)
    SHAPE IS NOT CONTENT. The MiniLM image on ``develop`` before #1758 passed
    every assertion above while transformers 5 tokenized almost every word to
    ``<unk>``: right width, unit norm, two different vectors — of garbage. So
    the probe also sends the fixed inputs recorded in
    ``docker/<service>-service/golden/<target>.json`` (a normal sentence, a
    German one, a mixed-language one and a text past the 512-token window)
    and requires every output to lie within ``GOLDEN_TOLERANCE`` of the value
    computed once from the pinned model files by
    ``scripts/ci/compute_model_golden_outputs.py``. The golden file is chosen
    by the model name the image itself declares (``EMBEDDING_MODEL`` /
    ``RERANKER_MODEL``), so the probe holds for every ``--target``; an image
    whose model has no golden file is a failure, not a skip.

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

import functools
import hashlib
import http.client
import json
import math
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
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


#: The checkout root: this file is scripts/ci/probe_model_service_contract.py.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Where each service's golden outputs live — next to the Dockerfile that pins
#: the model, because they change only together with its `revision=` literal
#: (src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py).
GOLDEN_DIRS = {
    "embedding": REPO_ROOT / "docker" / "embedding-service" / "golden",
    "reranker": REPO_ROOT / "docker" / "reranker-service" / "golden",
}

#: The environment variable through which each image names the model it ships.
MODEL_ENV = {"embedding": "EMBEDDING_MODEL", "reranker": "RERANKER_MODEL"}

#: The golden file format this probe reads; a file of another schema is refused.
GOLDEN_SCHEMA = 1

#: How an embedding is reduced before it is stored (#1763). A full vector is
#: 384-1024 floats per input; four inputs across four models would be ~10 000
#: numbers of diff noise per re-pin. The reduction keeps two views of it:
#:
#: - ``GOLDEN_SAMPLE_SIZE`` components at evenly spaced indices — the literal
#:   values, readable in a diff; and
#: - ``GOLDEN_PROJECTIONS`` projections onto fixed +-1/sqrt(dim) directions
#:   derived from sha256 (``golden_projection_signs``) — each one a weighted
#:   sum over EVERY component, so a change confined to dimensions the sample
#:   does not hit still moves them. A projection's error is bounded by the
#:   L2 distance between the two vectors, so it needs no looser tolerance.
#:
#: A hash of rounded values was rejected: rounding is discontinuous, so two
#: vectors 1e-9 apart can straddle a rounding boundary and hash differently —
#: a tolerance cannot be applied to a hash.
GOLDEN_SAMPLE_SIZE = 64
GOLDEN_PROJECTIONS = 8

#: Decimal places stored. The rounding error (<= 5e-7) is three orders of
#: magnitude below ``GOLDEN_TOLERANCE``, so it never decides a verdict.
GOLDEN_DECIMALS = 6

#: The largest |Δ| allowed between a stored golden value and the image's
#: output, for every embedding component, projection and reranker score.
#: Measured on 2026-09-25 (see the golden files' `computed` block and #1763):
#: see `GOLDEN_TOLERANCE_MEASUREMENT` below.
GOLDEN_TOLERANCE = 1e-3

#: The same, for a reranker logit (magnitude ~1-12, not ~0.05 like a unit
#: vector's component), recovered from the served score by ``score_logit``.
GOLDEN_LOGIT_TOLERANCE = 1e-2

#: A golden logit stays inside this band so its float32 sigmoid never rounds
#: to exactly 0.0 or 1.0 — ``score_logit`` could not invert it.
GOLDEN_MAX_ABS_LOGIT = 14.0


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


# --------------------------------------------------------------------------
# golden outputs (#1763)
# --------------------------------------------------------------------------


@functools.cache
def golden_projection_signs(index: int, dimension: int) -> tuple[int, ...]:
    """The +-1 weights of projection *index* over a vector of *dimension* components.

    Derived from sha256, not from ``random``: the golden files outlive any one
    interpreter, and nothing about ``random``'s stream is promised across
    Python versions. Written once in the generator, read here — both import
    this function, so the two cannot drift.
    """
    signs = []
    for component in range(dimension):
        digest = hashlib.sha256(f"kamerplanter-golden:{index}:{component}".encode()).digest()
        signs.append(1 if digest[0] & 1 else -1)
    return tuple(signs)


def golden_sample_indices(dimension: int) -> list[int]:
    """``GOLDEN_SAMPLE_SIZE`` evenly spaced component indices of a *dimension*-wide vector."""
    return [position * dimension // GOLDEN_SAMPLE_SIZE for position in range(GOLDEN_SAMPLE_SIZE)]


def reduce_embedding(vector: list[float]) -> dict[str, list[float]]:
    """The stored view of one embedding: its sampled components and its projections."""
    dimension = len(vector)
    scale = 1.0 / math.sqrt(dimension)
    projections = [
        scale
        * math.fsum(sign * value for sign, value in zip(golden_projection_signs(k, dimension), vector, strict=True))
        for k in range(GOLDEN_PROJECTIONS)
    ]
    return {
        "sample": [round(vector[index], GOLDEN_DECIMALS) for index in golden_sample_indices(dimension)],
        "projection": [round(value, GOLDEN_DECIMALS) for value in projections],
    }


def image_model(image: str, kind: str) -> str:
    """The model name the image declares in its own environment (``EMBEDDING_MODEL``/``RERANKER_MODEL``)."""
    env = json.loads(_docker("image", "inspect", "--format", "{{json .Config.Env}}", image))
    prefix = f"{MODEL_ENV[kind]}="
    values = [entry.removeprefix(prefix) for entry in env if entry.startswith(prefix)]
    if len(values) != 1 or not values[0]:
        raise ProbeError(f"{image} does not declare exactly one {MODEL_ENV[kind]} (env: {env})")
    return values[0]


def load_golden(kind: str, model: str, golden_dir: Path | None = None) -> tuple[Path, dict[str, Any]]:
    """The one golden file whose ``model`` is *model*; any other count is a failure."""
    directory = golden_dir if golden_dir is not None else GOLDEN_DIRS[kind]
    matches = []
    for path in sorted(directory.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("model") == model:
            matches.append((path, document))
    if len(matches) != 1:
        raise ProbeError(
            f"expected exactly one golden file for model {model!r} in {directory}, found "
            f"{[str(path) for path, _ in matches]} — generate it with scripts/ci/compute_model_golden_outputs.py"
        )
    path, document = matches[0]
    reduction = document.get("reduction")
    expected = {"sample_size": GOLDEN_SAMPLE_SIZE, "projections": GOLDEN_PROJECTIONS, "decimals": GOLDEN_DECIMALS}
    if document.get("schema") != GOLDEN_SCHEMA or (kind == "embedding" and reduction != expected):
        raise ProbeError(
            f"{path} has schema {document.get('schema')!r} / reduction {reduction!r}; this probe reads "
            f"schema {GOLDEN_SCHEMA} with reduction {expected} — regenerate it"
        )
    return path, document


def max_deviation(expected: list[float], actual: list[float]) -> float:
    """``max |expected - actual|``; lists of different length are a failure, never a truncated zip."""
    if len(expected) != len(actual):
        raise ProbeError(f"{len(actual)} values where the golden file holds {len(expected)}")
    deltas = [abs(e - a) for e, a in zip(expected, actual, strict=True)]
    # `max` skips a NaN whenever it is not first (every comparison with NaN is
    # False), so a NaN output would read as "no deviation" — it is returned as
    # NaN instead, which no tolerance admits.
    if any(math.isnan(delta) for delta in deltas):
        return math.nan
    return max(deltas, default=0.0)


def compare_golden(label: str, expected: list[float], actual: list[float], tolerance: float) -> float:
    """Raise when *actual* leaves the tolerance band around *expected*; return the deviation."""
    deviation = max_deviation(expected, actual)
    if not deviation <= tolerance:  # `not <=` so a NaN is a failure too
        worst = max(
            range(len(expected)),
            key=lambda i: math.inf if math.isnan(expected[i] - actual[i]) else abs(expected[i] - actual[i]),
        )
        raise ProbeError(
            f"{label}: max |Δ| {deviation:.3g} exceeds the golden tolerance {tolerance:g} "
            f"(worst at position {worst}: golden {expected[worst]!r}, image {actual[worst]!r})"
        )
    return deviation


def score_logit(score: float) -> float:
    """The logit behind a reranker score — the service answers ``sigmoid(logit)``."""
    if not 0.0 < score < 1.0:
        raise ProbeError(f"reranker score {score!r} is saturated; its logit cannot be recovered")
    return math.log(score) - math.log1p(-score)


def _golden_summary(path: Path, golden: dict[str, Any], deviation: float, count: int, tolerance: float) -> str:
    return (
        f"{count} outputs of {golden['repo_id']}@{golden['revision'][:12]} match {path.relative_to(REPO_ROOT)} "
        f"within {tolerance:g} (max |Δ| measured: {deviation:.3g})"
    )


def probe_embedding_golden(base: str, path: Path, golden: dict[str, Any]) -> float:
    """Every golden case, embedded by the running image, within tolerance; returns the max |Δ|."""
    cases = golden["cases"]
    payload: dict[str, Any] = {"texts": [case["text"] for case in cases]}
    if golden.get("prefix"):
        payload["prefix"] = golden["prefix"]
    status, body = _request(f"{base}/embed", payload)
    _expect(status == 200, f"POST /embed with the {len(cases)} golden texts answers 200 (got {status})")
    worst, count = 0.0, 0
    for case, vector in zip(cases, body["embeddings"], strict=True):
        reduced = reduce_embedding(vector)
        for view in ("sample", "projection"):
            worst = max(worst, compare_golden(f"{case['name']} {view}", case[view], reduced[view], GOLDEN_TOLERANCE))
            count += len(case[view])
    print(f"probe: ok — {_golden_summary(path, golden, worst, count, GOLDEN_TOLERANCE)}")
    return worst


def probe_reranker_golden(base: str, path: Path, golden: dict[str, Any]) -> float:
    """Every golden case, scored by the running image, within tolerance; returns the max |Δ|."""
    worst, count = 0.0, 0
    for case in golden["cases"]:
        documents = case["documents"]
        status, body = _request(
            f"{base}/rerank", {"query": case["query"], "documents": documents, "top_k": len(documents)}
        )
        _expect(status == 200, f"POST /rerank for golden case {case['name']} answers 200 (got {status})")
        by_index = {result["index"]: result["score"] for result in body["results"]}
        logits = [score_logit(by_index[index]) for index in range(len(documents))]
        worst = max(worst, compare_golden(f"{case['name']} logits", case["logits"], logits, GOLDEN_LOGIT_TOLERANCE))
        count += len(logits)
    print(f"probe: ok — {_golden_summary(path, golden, worst, count, GOLDEN_LOGIT_TOLERANCE)}")
    return worst


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
        golden_path, golden = load_golden(kind, image_model(image, kind))
        _wait_ready(base)
        if kind == "reranker":
            probe_reranker(base, image)
            probe_reranker_golden(base, golden_path, golden)
        else:
            probe_embedding(base, image)
            probe_embedding_golden(base, golden_path, golden)
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
