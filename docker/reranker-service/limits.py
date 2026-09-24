"""Request bounds and CPU budget of the reranker service (#1725).

Kept apart from ``main.py`` and importing only the standard library and
pydantic, so the backend's guard suite
(src/backend/tests/unit/guards/test_ml_sidecar_limits.py) loads THIS file — the
one ``main.py`` imports — by path, without onnxruntime, tokenizers or a model.
docker/embedding-service/limits.py is its sibling and is held to the same
assertions by the same parametrized test; ``cpu_budget`` is a verbatim copy
there, because the two images are separate build contexts.

**Why bounds at all.** Before #1725 only ``top_k`` was bounded: a request could
carry any number of documents of any length and the service tokenized and ran
all of them. Measured 2026-09-24 in the bge image under the chart's limits
(``-m 4g --cpus 2``) with documents of more than 512 tokens: 20 documents
answered in 112 s, 100 documents were OOMKilled in the old one-batch shape. The
bounds below turn an oversized request into a 422 (FastAPI's own answer to a
pydantic validation error) before it reaches the tokenizer; ``main.py`` runs the
graph one pair at a time under one lock, which is what keeps the memory of an
accepted request flat (see ``main.py``).

**Why these values.** The only caller is src/knowledge-service/app/reranker.py.
It sends the question as ``query`` — at most 2000 characters (``AskRequest``;
``/search`` allows 500) — and ``title + "\\n" + content`` of at most
``reranker_initial_k`` (default 20) retrieved chunks as ``documents``; the
largest chunk in spec/knowledge/rag measured 3524 characters that way on
2026-09-24. Every bound leaves headroom over that, and the guard test re-reads
the caller's limits and re-measures the corpus, so a caller that grows past a
bound goes red there rather than degrading to its no-rerank fallback silently.
No minimum is set: an empty ``documents`` list is a valid request answered with
``{"results": []}``.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

#: Characters in ``query``. The caller sends at most 2000 (``AskRequest``).
MAX_QUERY_CHARS = 4096

#: Items in ``documents``. The caller sends at most ``reranker_initial_k`` (20).
MAX_DOCUMENTS = 100

#: Characters per document. Tokenization truncates each pair to 512 tokens
#: anyway, so text past this bound could never change a score; it would only
#: cost tokenizer time. The largest corpus chunk is 3524 characters.
MAX_DOCUMENT_CHARS = 16384

#: Results returned. Unchanged from before #1725.
MAX_TOP_K = 50

#: Where the container's cgroup filesystem is mounted.
CGROUP_ROOT = Path("/sys/fs/cgroup")


class RerankRequest(BaseModel):
    query: str = Field(max_length=MAX_QUERY_CHARS)
    documents: list[Annotated[str, Field(max_length=MAX_DOCUMENT_CHARS)]] = Field(max_length=MAX_DOCUMENTS)
    top_k: int = Field(default=5, ge=1, le=MAX_TOP_K)


def _available_cpus() -> int:
    """CPUs this process may be scheduled on (affinity), else the host count."""
    sched_getaffinity = getattr(os, "sched_getaffinity", None)
    if sched_getaffinity is not None:
        try:
            return len(sched_getaffinity(0))
        except OSError:
            pass
    return os.cpu_count() or 1


def _read_fields(path: Path) -> list[str] | None:
    try:
        return path.read_text(encoding="ascii", errors="replace").split()
    except OSError:
        return None


def _cgroup_cpu_limit(cgroup_root: Path) -> int | None:
    """The CPU quota of the cgroup, rounded UP to whole CPUs; None when unlimited or unreadable.

    cgroup v2 publishes ``cpu.max`` as ``<quota> <period>`` (``max`` = no
    quota). cgroup v1 publishes ``cpu.cfs_quota_us`` (``-1`` = no quota) and
    ``cpu.cfs_period_us`` under the ``cpu`` controller directory. Rounded up so
    a fractional limit (``1.5`` CPUs) still gets a thread for its fraction.
    """
    v2 = _read_fields(cgroup_root / "cpu.max")
    if v2 is not None:
        if len(v2) == 2 and v2[0] != "max":
            return _ceil_quota(v2[0], v2[1])
        return None
    for controller in ("cpu", "cpu,cpuacct"):
        quota = _read_fields(cgroup_root / controller / "cpu.cfs_quota_us")
        period = _read_fields(cgroup_root / controller / "cpu.cfs_period_us")
        if quota and period:
            return _ceil_quota(quota[0], period[0])
    return None


def _ceil_quota(quota: str, period: str) -> int | None:
    try:
        quota_us, period_us = int(quota), int(period)
    except ValueError:
        return None
    if quota_us <= 0 or period_us <= 0:
        return None
    return math.ceil(quota_us / period_us)


def cpu_budget(cgroup_root: Path = CGROUP_ROOT, *, available_cpus: int | None = None) -> int:
    """Threads the inference session may use: the container's CPU limit, never the host's.

    ``os.cpu_count()`` reports the HOST. Measured 2026-09-24 with
    ``docker run --cpus 2``: ``os.cpu_count()`` and ``sched_getaffinity`` both
    8, ``cpu.max`` ``200000 100000`` — so the service used to start 8 intra-op
    threads to share 2 CPUs of quota, which the kernel throttles. The budget is
    the smaller of the affinity set and the cgroup quota (rounded up), and at
    least 1.

    Args:
        cgroup_root: The cgroup mount; injectable so the guard test can feed a
            fake v1/v2 tree.
        available_cpus: The affinity count; injectable for the same reason.
            Defaults to ``len(os.sched_getaffinity(0))``.
    """
    budget = available_cpus if available_cpus is not None else _available_cpus()
    limit = _cgroup_cpu_limit(cgroup_root)
    if limit is not None:
        budget = min(budget, limit)
    return max(1, budget)
