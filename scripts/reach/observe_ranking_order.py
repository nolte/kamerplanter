#!/usr/bin/env python3
"""Ask the ranking endpoint itself whether it ranks, and print how many endpoints did (#1680).

Observation step of the ``ranking-endpoint-answers`` reach probe (the #1609
class: ``/ready`` answered 503 for ever while the image's ``HEALTHCHECK``
reported healthy). It never reads ``/ready``, ``/health`` or the container's
health status — those are the service's statements about itself.

It polls ``POST /rerank`` on the URL ``reach:ranking:up`` wrote to
``.reach/ranking.url`` until the endpoint answers with a ranking or the deadline
passes. Then it sends two queries over the same two documents whose correct
orderings are opposite, and prints ``1`` only when the endpoint returned each
query's correct ordering — a constant answer, a stub or an echo prints ``0``.
An endpoint that never answers prints ``0`` as well: that is the defect, not a
failed observation.

Output: one integer, the number of ranking endpoints that answered correctly (0 or 1).
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import http_json, reach_dir  # noqa: E402

#: Model load of bge-reranker-v2-m3 on CPU takes tens of seconds; the image's own
#: HEALTHCHECK allows a 300 s start period, so the poll does too.
ANSWER_DEADLINE_SECONDS = 300
DOCUMENTS = [
    "Basil grows well next to tomatoes and is said to improve their flavour.",
    "Dill attracts pollinators and is a good companion for cucumbers.",
]
#: (query, the correct order of DOCUMENTS by relevance)
CASES = [
    ("Which herb is a good companion plant for tomatoes?", [0, 1]),
    ("Which herb is a good companion plant for cucumbers?", [1, 0]),
]


def ordering(base_url: str, query: str) -> list[int] | None:
    """The document order the endpoint returned for *query*, or None when it gave no ranking."""
    try:
        status, body = http_json(
            "POST",
            f"{base_url}/rerank",
            body={"query": query, "documents": DOCUMENTS, "top_k": len(DOCUMENTS)},
            timeout=30,
        )
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        del exc  # an endpoint that does not answer yet is polled again
        return None
    if status != 200 or not isinstance(body, dict) or not isinstance(body.get("results"), list):
        return None
    try:
        return [int(result["index"]) for result in body["results"]]
    except (KeyError, TypeError, ValueError) as exc:
        del exc  # a body without a ranking is no ranking
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deadline", type=float, default=ANSWER_DEADLINE_SECONDS)
    args = parser.parse_args(argv)
    url_file = reach_dir() / "ranking.url"
    if not url_file.is_file():
        print(f"observe ranking: {url_file} is missing; run `task reach:ranking:up` first", file=sys.stderr)
        return 1
    base_url = url_file.read_text(encoding="utf-8").strip()

    deadline = time.monotonic() + args.deadline
    first = ordering(base_url, CASES[0][0])
    while first is None and time.monotonic() < deadline:
        time.sleep(2)
        first = ordering(base_url, CASES[0][0])
    if first is None:
        print(0)
        return 0
    second = ordering(base_url, CASES[1][0])
    print(1 if first == CASES[0][1] and second == CASES[1][1] else 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
