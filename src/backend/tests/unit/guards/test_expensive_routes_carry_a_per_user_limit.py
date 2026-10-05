"""#2109 — every expensive authenticated route carries a per-user rate limit, or says why not.

The defect class: an authenticated route whose single request costs real CPU or
I/O — it takes a file upload, runs an inference, renders a document — has no
request budget for a session at all. The shared limiter keyed every limit on the
client address, and none of these routes was decorated: one account could queue
uploads, EXIF strips, thumbnail renders, CV inferences and PDF renders as fast as
it could send them (#2109, MT-012).

**Predicate** — a leaf route of the assembled app is a member when

* its dependency tree carries an ``UploadFile`` body parameter (read from
  FastAPI's own dependant tree, not from source), or
* its dependency tree reaches one of :data:`_EXPENSIVE_PROVIDERS` — the
  providers of the services that run an inference model or render a document —
  by identity.

Every member must carry a ``@limiter.limit`` on the shared limiter whose key
function is :func:`app.api.v1.auth.router.user_rate_limit_key` (one bucket per
account, the address only when no principal was resolved), or be classified in
:data:`_CLASSIFIED` with the reason it needs none. A classification that no
longer names a member fails, and :data:`_EXPECTED_MEMBERS` pins the set so a
predicate that silently loses a route fails instead of shrinking.

**What it cannot see**: an expensive route that neither uploads nor reaches one
of the listed providers (a new inference service must be added to the list —
the pinned member set and this docstring are where a reviewer looks), and the
*size* of a budget, which the route tests own
(``tests/api/test_expensive_routes_per_user_limit.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

#: Providers whose service runs a model or renders a document per request.
_EXPENSIVE_PROVIDER_NAMES = frozenset(
    {
        "get_cv_diagnosis_service",
        "get_pest_detection_service",
        "get_identification_service",
        "get_reference_image_service",
        "get_print_service",
        # #2110 (MT-013) — the services that put a prompt in front of an LLM.
        "get_ai_assistant_service",
        "get_glossary_service",
        "get_diagnose_service",
    }
)

#: Members that need no per-user limit of their own, keyed ``"<METHOD> <path>"``.
_CLASSIFIED: dict[str, str] = {
    "GET /api/v1/t/{tenant_slug}/cv-diagnosis/status": "a status read: no inference runs",
    "GET /api/v1/t/{tenant_slug}/cv-diagnosis/history": "a paginated history read: no inference runs",
    "POST /api/v1/t/{tenant_slug}/cv-diagnosis/diagnose/{request_key}/confirm": (
        "records the user's confirmation of a stored result: no inference runs"
    ),
    "GET /api/v1/t/{tenant_slug}/pests/status": "a status read: no inference runs",
    "GET /api/v1/t/{tenant_slug}/pests/plants/{plant_key}/history": "a history read: no inference runs",
    "POST /api/v1/t/{tenant_slug}/pests/detections/{detection_key}/feedback": (
        "stores feedback on a stored detection: no inference runs"
    ),
    "POST /api/v1/t/{tenant_slug}/pests/detections/{detection_key}/create-inspection": (
        "creates an inspection from a stored detection: no inference runs"
    ),
    "POST /api/v1/t/{tenant_slug}/identification/{request_key}/select": (
        "records the chosen result of a stored identification: no inference runs"
    ),
    "POST /api/v1/t/{tenant_slug}/identification/{request_key}/instance": (
        "links a stored identification to a plant: no inference runs"
    ),
    "GET /api/v1/t/{tenant_slug}/identification/history": "a history read: no inference runs",
    "GET /api/v1/recognition/status": "reports which identification adapters are configured: no inference runs",
    "GET /api/v1/t/{tenant_slug}/plant-instances/{key}/photos/assess/adapters": (
        "lists the configured assessment adapters: no assessment runs"
    ),
    # #2110 (MT-013) — routes of the LLM services that put no prompt in front of a model.
    "GET /api/v1/t/{tenant_slug}/ai/tips": "a read of stored tip cards: it never generates (#1461)",
    "POST /api/v1/t/{tenant_slug}/ai/tips/{tip_key}/dismiss": "flags a stored tip card: no LLM call",
    "POST /api/v1/t/{tenant_slug}/ai/tips/{tip_key}/acted-on": "flags a stored tip card: no LLM call",
    "GET /api/v1/t/{tenant_slug}/ai/daily-tip": "a read of today's stored card: it never generates (#1461)",
    "POST /api/v1/t/{tenant_slug}/ai/daily-tip/dismiss": "flags today's stored card: no LLM call",
    "GET /api/v1/t/{tenant_slug}/ai/conversations": "lists the caller's conversations: no LLM call",
    "POST /api/v1/t/{tenant_slug}/ai/conversations": "creates an empty conversation: no LLM call",
    "DELETE /api/v1/t/{tenant_slug}/ai/conversations/{conversation_key}": "an Art. 17 delete: no LLM call",
    "GET /api/v1/t/{tenant_slug}/ai/providers": "lists provider records: no LLM call",
    "GET /api/v1/ai/knowledge-service/health": "a readiness probe of the knowledge service: no LLM call",
    "GET /api/v1/public/ai/health": "a readiness probe of the knowledge service: no LLM call",
    "POST /api/v1/public/ai/ask": (
        "anonymous light-mode route: there is no account to bucket on; it carries the per-address "
        "limit AI_PUBLIC_RATE_LIMIT_PER_MIN instead"
    ),
    "GET /api/v1/t/{tenant_slug}/diagnosis/symptoms": "reads the symptom catalogue: no LLM call",
    "GET /api/v1/t/{tenant_slug}/glossary/terms": "lists curated terms: no LLM call",
    "GET /api/v1/t/{tenant_slug}/glossary/term/{slug}": "serves a cached or curated text: it never generates (#1460)",
    "GET /api/v1/public/glossary/terms": "lists curated terms: no LLM call",
    "GET /api/v1/public/glossary/term/{slug}": "serves a cached or curated text: it never generates (#1460)",
    "PUT /api/v1/admin/glossary/term/{slug}": "platform-admin catalogue write: no LLM call",
    "DELETE /api/v1/admin/glossary/term/{slug}": "platform-admin catalogue write: no LLM call",
    "POST /api/v1/admin/glossary/cache/invalidate-all": "platform-admin cache drop: no LLM call",
    "POST /api/v1/admin/glossary/term/{slug}/cache/invalidate": "platform-admin cache drop: no LLM call",
}

#: Pinned member set (#2109): the routes the predicate must reach.
_EXPECTED_LIMITED = frozenset(
    {
        "POST /api/v1/t/{tenant_slug}/attachments",
        "POST /api/v1/t/{tenant_slug}/plant-instances/{key}/photos",
        "POST /api/v1/t/{tenant_slug}/tasks/{key}/photos",
        "POST /api/v1/t/{tenant_slug}/ipm/pests/{pest_key}/images",
        "POST /api/v1/import/upload",
        "POST /api/v1/t/{tenant_slug}/cv-diagnosis/diagnose",
        "POST /api/v1/t/{tenant_slug}/pests/detect",
        "POST /api/v1/t/{tenant_slug}/pests/plants/{plant_key}/detect",
        "POST /api/v1/t/{tenant_slug}/identification/identify",
        "POST /api/v1/t/{tenant_slug}/identification/reference",
        "GET /api/v1/t/{tenant_slug}/print/nutrient-plan/{plan_key}",
        "GET /api/v1/t/{tenant_slug}/print/care-checklist",
        "GET /api/v1/t/{tenant_slug}/print/plant-labels",
        # #2110 (MT-013) — every route that puts a prompt in front of an LLM.
        "POST /api/v1/t/{tenant_slug}/ai/tips/refresh",
        "POST /api/v1/t/{tenant_slug}/ai/daily-tip/refresh",
        "POST /api/v1/t/{tenant_slug}/ai/explain",
        "POST /api/v1/t/{tenant_slug}/ai/conversations/{conversation_key}/messages",
        "POST /api/v1/t/{tenant_slug}/glossary/term/{slug}/generate",
        "POST /api/v1/t/{tenant_slug}/diagnosis/analyze",
    }
)


def _leaf_routes(routes: list[Any], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix + route.path_format, route
        elif hasattr(route, "original_router"):
            yield from _leaf_routes(route.original_router.routes, prefix + route.include_context.prefix)


def _walk(dependant: Dependant) -> Iterator[Dependant]:
    yield dependant
    for child in dependant.dependencies:
        yield from _walk(child)


def _takes_upload(dependant: Dependant) -> bool:
    return any("UploadFile" in repr(param.field_info.annotation) for d in _walk(dependant) for param in d.body_params)


def _reaches_expensive_provider(dependant: Dependant) -> bool:
    calls: list[Callable[..., Any] | None] = [d.call for d in _walk(dependant)]
    return any(getattr(call, "__name__", None) in _EXPENSIVE_PROVIDER_NAMES for call in calls)


def _members() -> dict[str, APIRoute]:
    from app.main import app

    out: dict[str, APIRoute] = {}
    for path, route in _leaf_routes(app.router.routes):
        if _takes_upload(route.dependant) or _reaches_expensive_provider(route.dependant):
            for method in sorted(route.methods or []):
                out[f"{method} {path}"] = route
    return out


def _per_user_limited(route: APIRoute) -> bool:
    from app.api.v1.auth.router import limiter, user_rate_limit_key

    name = f"{route.endpoint.__module__}.{route.endpoint.__name__}"
    return any(limit.key_func is user_rate_limit_key for limit in limiter._route_limits.get(name, []))


def test_every_expensive_route_is_limited_per_user_or_classified() -> None:
    members = _members()
    unbounded = sorted(key for key, route in members.items() if key not in _CLASSIFIED and not _per_user_limited(route))
    assert not unbounded, "expensive routes without a per-user @limiter.limit (#2109):\n" + "\n".join(unbounded)


def test_the_predicate_reaches_every_pinned_route() -> None:
    members = _members()
    missing = sorted(_EXPECTED_LIMITED - set(members))
    assert not missing, f"the predicate lost: {missing}"


def test_every_classification_names_a_live_member() -> None:
    members = _members()
    stale = sorted(set(_CLASSIFIED) - set(members))
    assert not stale, f"classified routes that are no longer members: {stale}"
    still_limited = sorted(key for key in _CLASSIFIED if _per_user_limited(members[key]))
    assert not still_limited, f"classified as needing no limit but limited: {still_limited}"


def test_the_check_tells_an_ip_keyed_limit_apart() -> None:
    """Self-test: a route limited on the address only is not a per-user limit."""
    from app.api.v1.auth.router import limiter

    members = {f"{route.endpoint.__module__}.{route.endpoint.__name__}": route for route in _members().values()}
    ip_limited = [name for name in limiter._route_limits if name.startswith("app.api.v1.privacy.router.")]
    assert ip_limited, "the privacy routes carry IP limits; the self-test needs one"
    from app.main import app

    routes = {
        f"{route.endpoint.__module__}.{route.endpoint.__name__}": route for _, route in _leaf_routes(app.router.routes)
    }
    assert not _per_user_limited(routes[ip_limited[0]])
    assert members, "the walk reached no member at all"
