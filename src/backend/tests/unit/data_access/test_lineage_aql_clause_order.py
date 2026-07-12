"""Regression guard against the AQL ``OPTIONS``-before-``PRUNE`` ordering bug (#571).

The graph-traversal grammar is strict::

    FOR v, e, p IN 1..N OUTBOUND @start GRAPH 'g'
      [PRUNE <cond>]
      [OPTIONS {...}]
      [FILTER <cond>]
      RETURN ...

``PRUNE`` MUST come before ``OPTIONS``; the reverse is a hard parse error
(ArangoDB ERR 1501) that turns every lineage traversal into an HTTP 500. Mocked
repository unit tests never see this because they stub ``aql.execute`` and never
send the string to a parser, so this cheap static scan extracts the AQL of each
lineage traversal method and asserts the clause order — a future reorder makes
the build red. The SEC-B4 cross-tenant ``PRUNE``/``FILTER`` isolation itself is
exercised against a real ArangoDB in
``tests/integration/test_propagation_lineage_tenant_isolation.py``.
"""

from __future__ import annotations

import inspect
import re

from app.data_access.repositories.propagation_repository import PropagationRepository

# The three graph-traversal methods that carry a PRUNE + OPTIONS clause pair.
LINEAGE_METHODS = (
    "trace_ancestor_paths",
    "list_ancestors",
    "list_descendants",
)

_TRAVERSAL_RE = re.compile(r"FOR\s+.+?\bGRAPH\b.+?RETURN", re.DOTALL)


def _traversal_body(method_name: str) -> str:
    """Return the AQL text of a lineage traversal method's source (FOR..RETURN)."""
    source = inspect.getsource(getattr(PropagationRepository, method_name))
    match = _TRAVERSAL_RE.search(source)
    assert match, f"no graph traversal found in {method_name}()"
    return match.group(0)


def test_each_lineage_traversal_has_prune_before_options() -> None:
    """PRUNE must precede OPTIONS in every lineage traversal (#571)."""
    for method_name in LINEAGE_METHODS:
        body = _traversal_body(method_name)
        prune_at = body.find("PRUNE")
        options_at = body.find("OPTIONS")

        assert prune_at != -1, f"{method_name}: PRUNE clause missing"
        assert options_at != -1, f"{method_name}: OPTIONS clause missing"
        assert prune_at < options_at, f"{method_name}: AQL PRUNE must come before OPTIONS (ERR 1501 / HTTP 500, #571)"


def test_each_lineage_traversal_keeps_tenant_filter_after_options() -> None:
    """The SEC-B4 tenant FILTER stays after OPTIONS so the projected vertex is kept."""
    for method_name in LINEAGE_METHODS:
        body = _traversal_body(method_name)
        options_at = body.find("OPTIONS")
        filter_at = body.find("FILTER v.tenant_key == @tenant_key")

        assert filter_at != -1, f"{method_name}: tenant boundary FILTER missing (SEC-B4)"
        assert options_at < filter_at, f"{method_name}: tenant FILTER must follow OPTIONS clause"
