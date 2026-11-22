"""REQ-053 WP 5.3 (#2432) - a body ceiling for one route whose path carries variables, JSON included.

The garden-plan import takes a 5 MB JSON file where every other JSON body is held to 1 MiB. The ceiling is matched
on the method and a full-match pattern of the path before the body is read; a path that only looks like it, another
method, or a trailing slash keeps the global ceiling (the safe direction). Measured through raw ASGI calls against an
application that reads the whole body, as ``test_tenant_import_body_ceiling`` does.
"""

from __future__ import annotations

import asyncio
import re

from app.common.body_limit import RequestBodyLimitMiddleware, RoutePatternCeiling
from tests.api.test_tenant_import_body_ceiling import MIB, _post, _Reader

JSON = b"application/json"
PATTERN = re.compile(r"^/api/v1/t/[^/]+/sites/[^/]+/plan/import$")
MATCH = "/api/v1/t/alice/sites/site_1/plan/import"


def _app() -> tuple[_Reader, RequestBodyLimitMiddleware]:
    inner = _Reader()
    return inner, RequestBodyLimitMiddleware(
        inner,
        max_body_bytes=2 * MIB,
        spool_budget_bytes=64 * MIB,
        spool_wait_seconds=0,
        pattern_ceilings=[RoutePatternCeiling(method="POST", pattern=PATTERN, max_body_bytes=5 * MIB)],
    )


def _post_json(app: RequestBodyLimitMiddleware, path: str, size: int, method: str = "POST") -> tuple[int, dict]:
    return asyncio.run(_post(app, path=path, size=size, method=method, content_type=JSON))


class TestThePatternCeiling:
    def test_a_json_body_above_one_mib_reaches_the_matching_route_and_takes_no_spool_budget(self) -> None:
        inner, app = _app()

        status, payload = _post_json(app, MATCH, 3 * MIB)

        assert (status, payload) == (200, {"read": 3 * MIB})
        assert inner.read == 3 * MIB and app.budget.in_use_bytes == 0

    def test_the_same_body_is_a_413_everywhere_else(self) -> None:
        for path, method in (
            ("/api/v1/t/alice/sites/site_1/plan/batch", "POST"),
            (MATCH + "/", "POST"),
            (MATCH + "/x", "POST"),
            ("/api/v1/t/alice/sites/a/b/plan/import", "POST"),
            (MATCH, "PUT"),
        ):
            inner, app = _app()
            status, _payload = _post_json(app, path, 3 * MIB, method)
            assert status == 413, (path, method)
            assert inner.read < 3 * MIB, "the body was cut, not read to the end"

    def test_the_route_ceiling_itself_holds(self) -> None:
        inner, app = _app()

        status, _payload = _post_json(app, MATCH, 6 * MIB)

        assert status == 413
        assert inner.read <= 5 * MIB + 256 * 1024
