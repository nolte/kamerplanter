"""Request bounds and CPU budget of the embedding service (#1725).

Kept apart from ``main.py`` and importing only the standard library and
pydantic, so the backend's guard suite
(src/backend/tests/unit/guards/test_ml_sidecar_limits.py) loads THIS file — the
one ``main.py`` imports — by path, without onnxruntime, transformers or a model.
docker/reranker-service/limits.py is its sibling and is held to the same
assertions by the same parametrized test; ``cpu_budget`` is a verbatim copy
there, because the two images are separate build contexts.

**Why bounds at all.** Before #1725 no field of ``/embed`` was bounded and all
texts of a request ran through the graph as one padded batch. Measured
2026-09-24 in the e5-large image under the chart's limits (``-m 4g --cpus 2``)
with texts of more than 512 tokens: 16 texts answered in 70 s, 64 texts were
OOMKilled in that one-batch shape. The bounds below turn an oversized request
into a 422 (FastAPI's own answer to a pydantic validation error) before it
reaches the tokenizer; ``main.py`` runs the graph one text at a time under one
lock, which is what keeps the memory of an accepted request flat.

**Why these values.** The only caller is src/knowledge-service/app/embedding.py:
``embed()`` sends one query, ``embed_batch()`` the chunks of one knowledge file
(spec/knowledge/rag: at most 16 chunks per file, at most 3524 characters per
chunk, measured 2026-09-24), in slices of at most ``_MAX_TEXTS_PER_REQUEST``
(32) — half of ``MAX_TEXTS`` — so a larger file is split by the caller instead
of refused here. The guard test re-reads that slice size. No minimum is set: an
empty ``texts`` list is answered with empty embeddings.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

#: The model this image serves; the final Dockerfile target sets it.
DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "multilingual-e5-base")

#: Items in ``texts``. The caller slices to at most 32 per request.
MAX_TEXTS = 64

#: Characters per text. Tokenization truncates each text to 512 tokens anyway,
#: so text past this bound could never change a vector; it would only cost
#: tokenizer time. The largest corpus chunk is 3524 characters.
MAX_TEXT_CHARS = 16384

#: Characters in ``prefix``. The caller sends ``"query: "`` or ``"passage: "``.
MAX_PREFIX_CHARS = 64

#: Characters in ``model`` (echoed back, never used to select a graph).
MAX_MODEL_CHARS = 128

#: Where the container's cgroup filesystem is mounted.
CGROUP_ROOT = Path("/sys/fs/cgroup")


class EmbedRequest(BaseModel):
    texts: list[Annotated[str, Field(max_length=MAX_TEXT_CHARS)]] = Field(max_length=MAX_TEXTS)
    model: str = Field(default=DEFAULT_MODEL, max_length=MAX_MODEL_CHARS)
    prefix: str = Field(default="", max_length=MAX_PREFIX_CHARS)


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
