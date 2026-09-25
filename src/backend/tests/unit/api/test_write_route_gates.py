"""Every write route resolves its caller through a gate, or is allowlisted with a reason (#1353).

Nothing enumerated the write surface. `check_route_role_guards.py` covers the
frontend router against the decision table and says so in its own docstring — a
new backend gate does not turn it red. `check_tenant_body_field.py` covers body
schemas. `test_require_permission_enforcement.py` and
`test_req049_scope_enforcement.py` drive hand-picked endpoints. So a write route
added with a copied `Depends(get_current_tenant)` was green everywhere, and #948
— a guard opted into at the call site — kept recurring because opting in was the
only mechanism there was.

**Two selectors, not one.** #1353 describes the tenant-scoped half. That half
alone would never have reached `/api/v1/admin/settings` (#1385) or
`/api/v1/admin/oidc-providers` (#1399), both of which write installation-wide
configuration and both of which drifted exactly the same way. The admin half is
here for that reason, and it found #1399 on its first run.

**Why a test and not a `scripts/check_*.py` sweep.** The question is which
dependency a mounted route actually resolves, and that is a property of the
assembled app, not of a file. The AST sweep quoted in #1353 keyed on the filename
`tenant_router.py` and therefore missed three routes that live in
`nutrient_calculations/router.py` and `plant_instances/diary_router.py` — the
same opt-in-list hole the sweep exists to close, one level up.

**The allowlist is the interesting half.** Not every ungated write route is a
defect: per-user state, a data-subject right, and POST-as-computation are all
legitimately open to any member. What was missing is anyone having written down
*which is which*. Each entry below carries its reason, and an entry that no
longer matches a route fails — the obsolescence rule `check_layer_imports` and
`check_route_role_guards` already follow.
"""

import enum
import inspect
import pathlib
import re
from typing import Any

import pytest
from fastapi.params import Depends as DependsParam

from app.api.v1.router import api_router
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError
from app.domain.models.tenant_context import TenantContext
from tests.unit.api._write_call_graph import (
    call_graph,
    direct_writers,
    persists,
    reachable_keyword_arguments,
    unresolved_call_count,
    write_path_of,
    write_sinks_of,
)

#: The methods that are a write *by convention*. This comment used to end by
#: saying the real detector did not exist; it does now, and this is what it does.
#:
#: A method is a convention, not a behaviour. Two routes in this codebase were
#: measured writing on a ``GET`` (#1422 review): ``GET /care-reminders/plants/{key}/profile``
#: and ``GET /t/{slug}/care-reminders/dashboard`` both reached
#: ``get_or_create_profile``, which persisted a ``CareProfile`` and an edge — the
#: dashboard for every plant of the tenant, on a plain read, for any member.
#:
#: Deciding whether a handler writes needs the call graph, not the decorator.
#: :mod:`tests.unit.api._write_call_graph` is that detector (#1443), and
#: :func:`mounted_write_operations` now admits a read whose handler reaches a
#: persistence write on exactly the terms it admits a ``POST``: no list, no
#: opt-in, no method name. Run against this head it reported **13** of 356 mounted
#: read operations — ten of them real writes on a ``GET``, recorded in
#: :data:`_PERSISTING_READ_FINDINGS`, and three guarded by an argument the
#: detector cannot evaluate, recorded in :data:`_GUARDED_PERSISTING_READS`.
#:
#: **What the detector sees.** Every module under the imported ``app`` package,
#: parsed once per session. Within it, calls to python-arango collection mutators
#: on a collection receiver, and query strings shaped like an AQL or SQL write —
#: spelled out in the body **or bound to a module-level constant the body merely
#: names**, which is how the TimescaleDB repositories are written and which the
#: first version of this detector could not see (SEC-004) — are the sinks;
#: everything else is reachability over a call graph resolved by
#: RECEIVER TYPE — ``self`` through the enclosing class, an attribute through the
#: type its ``__init__`` annotates, a local through its annotation or its
#: constructor — with the method then looked up on that type's ancestors and on
#: its implementors, because the services here are annotated against
#: ``I*Repository`` interfaces whose method bodies are ``...``.
#:
#: **What it does not see.** Stated, because a guard whose blind spots are
#: implicit is read as having none:
#:
#: * **dynamic dispatch** — ``getattr(obj, name)()``, a handler pulled out of a
#:   registry or a dict, anything whose target is a value at run time;
#: * **writes performed by a Celery task** the route enqueues. Those happen in
#:   another process, off the request path, and are gated on the task. A
#:   ``BackgroundTasks.add_task(fn, ...)`` is **not** that case and IS followed
#:   (SEC-005): Starlette runs ``fn`` in this process, under the same request;
#: * **a write behind a receiver nothing annotates.** Those fall back to matching
#:   by NAME, bounded to the repository write vocabulary, which over-reports
#:   rather than missing — the count of unresolved receivers is asserted against a
#:   ceiling below so the blind spot cannot grow in silence;
#: * **the value of an argument.** The detector is path-insensitive: a write the
#:   callee performs only when a flag allows it counts as reachable. That is what
#:   :data:`_GUARDED_PERSISTING_READS` is for, and why each of its entries carries
#:   a witness this file checks rather than a sentence nobody holds against the
#:   code — the failure #1441 had just been paid for;
#: * **anything outside the ``app`` package.**
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

#: The methods a read is mounted under. A handler mounted on one of these that
#: nevertheless persists is the class #1443 exists to surface.
READ_METHODS = {"GET", "HEAD", "OPTIONS"}

TENANT_PREFIX = "/t/{tenant_slug}"
ADMIN_PREFIX = "/api/v1/admin"


class Operation:
    """One mounted write operation, with the dependencies its signature declares."""

    def __init__(self, method: str, path: str, endpoint: Any, route: Any = None) -> None:
        self.method = method
        self.path = path
        self.module = endpoint.__module__
        self.name = endpoint.__name__
        #: The mounted route itself, kept so the THIRD question below can read
        #: `route.dependant` transitively. `inspect.signature` sees only what the
        #: handler names; a router-level `APIRouter(dependencies=[...])` is
        #: invisible to it, in both directions — a correctly gated route passes
        #: for the wrong reason, and an ungated sibling passes identically.
        self.route = route
        self.dependencies: dict[str, Any] = {}
        try:
            signature = inspect.signature(endpoint)
        except TypeError, ValueError:  # pragma: no cover - defensive
            return
        for parameter_name, parameter in signature.parameters.items():
            if isinstance(parameter.default, DependsParam):
                self.dependencies[parameter_name] = parameter.default.dependency

    @property
    def id(self) -> str:
        """`module.function`, the key the allowlist uses.

        Not `(METHOD, path)`: a path is edited for reasons that have nothing to do
        with authorisation, and an allowlist keyed on one would expire on a rename
        and quietly re-admit the route.
        """
        return f"{self.module.removeprefix('app.api.v1.')}.{self.name}"

    def __repr__(self) -> str:  # pragma: no cover - test output only
        return f"{self.method} {self.path} ({self.id})"


def _operation_id(endpoint: Any) -> str:
    """:attr:`Operation.id` without building an Operation. The same key, one source."""
    return f"{endpoint.__module__.removeprefix('app.api.v1.')}.{endpoint.__name__}"


def mounted_operations() -> list[tuple[str, str, Any, Any]]:
    """Every `(method, cumulative path, endpoint, route)` the v1 router mounts.

    `include_router` does **not** flatten: it leaves `_IncludedRouter` wrappers
    that carry no `path` attribute at all, and whose prefix lives in
    `include_context.prefix`. A flat read of `api_router.routes` therefore finds
    ~50 routes instead of ~796, and every path comes out relative — the mistake
    `scripts/check_frontend_calls_served.py` documents at length after making it.
    `test_the_walk_sees_what_a_flat_read_cannot` below pins that this walk does
    not repeat it.

    Reads are returned alongside writes and the filtering happens above, because
    #1443's question — which of these reads persists? — is asked of the same walk.
    A second walker for the read half would be the shape this file's own docstring
    warns about: two enumerations of one surface, drifting.
    """
    found: list[tuple[str, str, Any, Any]] = []

    def walk(router: Any, prefix: str = "") -> None:
        for route in getattr(router, "routes", []):
            included = getattr(route, "original_router", None)
            if included is not None:
                context = getattr(route, "include_context", None)
                walk(included, prefix + (getattr(context, "prefix", "") or ""))
                continue
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None:
                continue
            path = prefix + (getattr(route, "path", "") or "")
            for method in getattr(route, "methods", ()) or ():
                found.append((method, path, endpoint, route))

    walk(api_router)
    return found


def mounted_write_operations() -> list[Operation]:
    """Every operation that WRITES — by method, or because the detector says so.

    The second half is #1443. A read whose handler reaches a persistence write is
    a write route from here on, answered by the same three questions and the same
    allowlists as a `POST`, without having been listed anywhere first.
    """
    found: list[Operation] = []
    for method, path, endpoint, route in mounted_operations():
        detected_read = (
            method in READ_METHODS and _operation_id(endpoint) not in _GUARDED_PERSISTING_READS and persists(endpoint)
        )
        if method in WRITE_METHODS or detected_read:
            found.append(Operation(method, path, endpoint, route))
    return found


#: Reads the detector reports, whose write is unreachable because of an ARGUMENT.
#:
#: The detector is path-insensitive by construction: it answers "can this handler
#: reach a write", not "does it, with these values". `CareReminderService.
#: get_or_create_profile` takes `may_create` keyword-only and without a default —
#: #1422's fix — and persists only when it is true. Every one of the three routes
#: here reaches it with `may_create=False`.
#:
#: **Each entry is a witness, not a sentence.** The value is
#: `(callee, keyword, sinks)` and `test_every_guarded_read_really_passes_its_guard`
#: re-parses every reachable call to `callee` and fails unless all of them pass
#: `keyword=False` as a literal. Flip one to `True`, add a new caller that omits
#: it, rename the parameter — the entry goes red and the route returns to the
#: sweep. The reason #1441 cost a whole slice is that its allowlist entry was prose
#: that had never been true; an exemption nobody can check is worse than no
#: exemption.
#:
#: **`sinks` is the third element because a witness is not automatically the
#: REASON** (SEC-002 of the #1443 review). The first version carried
#: `(callee, keyword)` only, and it excused the whole route: a second, unguarded
#: write anywhere in the same handler — an audit row, a counter — would have kept
#: the route out of the sweep, silently, because the exemption is keyed on the
#: route and not on the write. The third element is the direct write MEASURED on
#: 2026-09-16 — the SET of them, because
#: `test_the_witness_is_the_only_write_each_guarded_read_reaches` compares against
#: **every** sink the handler reaches rather than against the one a shortest-path
#: search happens to return. Any other sink, additional or substituted, turns the
#: entry red.
#: The two writes `CareReminderService.get_or_create_profile` performs behind
#: `may_create`: the profile document and the plant→profile edge. Measured, not
#: assumed — the first version of this entry named only the edge, because
#: :func:`write_path_of` returns the SHORTEST chain and the document insert sits one
#: hop further along. That is SEC-002 in one line: a witness that names a route says
#: nothing about how many writes the route reaches.
#:
#: A sink names the enclosing FUNCTION and carries no line number. It used to carry
#: one, and #1436 — which inserted lines above ``create_edge`` in
#: ``base_repository.py`` — turned this frozenset red without a single write
#: moving, changing or appearing. A witness that goes red on an unrelated edit is
#: lifted blind the third time, which is the drift this file exists to prevent. The
#: line survives for humans in the path :func:`write_path_of` prints.
#: **One** sink, and the shrink is the measurement (#1292 round two).
#:
#: This set held three until 2026-09-17: the profile document through
#: ``_insert_doc``, its ``has_care_profile`` edge through ``create_edge``, and a
#: ``_delete_doc`` for the orphan a losing racer had to clean up. Three sinks
#: because a care profile was written by three separate statements — which is
#: precisely the defect #1292 round two reports: between the first and the second,
#: a committed-but-unlinked document was readable through the un-indexed
#: ``plant_key`` field, and a concurrent request answered with it.
#:
#: ``ArangoCareReminderRepository.create_linked_profile`` now writes the document
#: and the edge inside one stream transaction, so the delete has nothing to clean
#: up and the two inserts are one function. The detector records at most one sink
#: per function (stated in ``_write_call_graph``'s docstring, not hidden here), so
#: the edge insert one line below is covered by this name rather than carrying its
#: own — sound here because the two are the same transaction and cannot be reached
#: apart.
_CARE_PROFILE_SINKS = frozenset(
    {
        "transaction.collection(col.CARE_PROFILES).insert() in "
        "app.data_access.arango.care_reminder_repository::ArangoCareReminderRepository.create_linked_profile",
    }
)

_GUARDED_PERSISTING_READS: dict[str, tuple[str, str, frozenset[str]]] = {
    "care_reminders.router.get_or_create_profile": ("get_or_create_profile", "may_create", _CARE_PROFILE_SINKS),
    "care_reminders.tenant_router.get_care_dashboard": ("get_or_create_profile", "may_create", _CARE_PROFILE_SINKS),
    "print.tenant_router.export_care_checklist_pdf": ("get_or_create_profile", "may_create", _CARE_PROFILE_SINKS),
}


#: Reads that persist **on purpose**, each bound to the writes it may reach.
#:
#: Two of the ten findings #1443 reported are not defects and cannot be repaired
#: into pure reads (#1461, decision 1 of the group analysis):
#:
#: * ``auth.router.oauth_callback`` is a **browser redirect**. The identity
#:   provider sends the user back with a ``GET`` and there is no other verb
#:   available; the handler then completes the login, which by definition writes
#:   (REQ-023 §4.3a). It is not a read that happens to persist — it is a write
#:   path whose verb the OAuth2 protocol fixes.
#: * ``privacy.router.download_export`` records that the export was collected
#:   (REQ-025 §4.2a). The Art.-15 evidence *is* the download, so the write cannot
#:   move to another request without the evidence recording a different event.
#:
#: **Why a third list and not :data:`_GUARDED_PERSISTING_READS`.** That list is
#: for a write the detector reports but an ARGUMENT makes unreachable, and its
#: value is a `(callee, keyword, sinks)` witness that
#: `test_every_guarded_read_really_passes_its_guard` re-parses and fails unless
#: every reachable call passes the keyword as literal `False`. Neither route here
#: has such an argument — both write on every call — so an entry there would be a
#: witness naming nothing, and it would take the route OUT of the sweep, which is
#: exactly what must not happen: both routes stay in `mounted_write_operations`
#: and keep answering the three authorisation questions like any `POST`.
#:
#: **The relation is `reachable ⊆ excused`, not equality**, and that is a
#: measurement, not a softening. `write_sinks_of` over-approximates: where a
#: receiver carries no type the detector falls back to matching by NAME, which
#: resolves one `self._repo.create(...)` to *every* repository `create` in the
#: tree. Measured on 2026-09-17, ``oauth_callback`` reaches fifteen sink
#: identities that way, most of them `delete` methods on repositories the OAuth
#: path never touches. Pinned as an equality, adding a `delete` to any unrelated
#: repository would turn this red with no write moving, changing or appearing —
#: the drift that cost this file its sink line numbers, one level up. A subset
#: says the thing the entry actually claims: this route reaches no write it is
#: not excused for.
#:
#: **How much "a NEW sink turns it red" is worth differs per entry, and the honest
#: version of that sentence is below** (review SCR-006). Both halves were measured
#: by mutation on 2026-09-18 — an added, detector-resolvable
#: ``self._export_repo.create(...)`` inside the service each route reaches:
#:
#: * ``privacy.download_export`` excuses **one** sink (the atomic
#:   ``increment_download_count`` query since #1662; ``_update_doc`` before). The
#:   mutation adds ``_insert_doc``, which is not in the set, and the sweep goes
#:   **red**. `test_a_second_write_in_an_intentional_read_is_reported` pins that,
#:   so the claim is checked and not believed.
#: * ``auth.oauth_callback`` excuses fifteen, and those fifteen already include
#:   **all four** base document primitives plus ``create_edge``/``delete_edges``.
#:   Any write added anywhere below it goes through one of them, so the identity
#:   is already in the set and the sweep stays **green**. For this entry the sink
#:   set bounds the *shape* of what the route reaches — repository primitives, no
#:   raw query outside the listed ones — and nothing finer. Said out loud because
#:   a witness whose limits are implicit is read as having none, which is the
#:   #1441 failure this file exists to avoid repeating.
#:
#: What still covers ``oauth_callback`` is not this list: the route stays inside
#: `mounted_write_operations`, answers the three authorisation questions like any
#: `POST`, and carries a `_PUBLIC_ALLOWLIST` entry with an obsolescence rule. A
#: sharper witness here needs the detector to carry the *call path* into the sink
#: identity, which is a change to `_write_call_graph` and not to this dict.
_INTENTIONAL_PERSISTING_READS: dict[str, tuple[str, frozenset[str]]] = {
    "auth.router.oauth_callback": (
        "REQ-023 §4.3a — the OAuth2 redirect back from the provider can only be a GET, and "
        "completing the login writes the User, the AuthProvider link and the refresh token. "
        "A write path whose verb the protocol fixes, not a read that persists.",
        frozenset(
            {
                "col.insert() in app.data_access.arango.base_repository::BaseArangoRepository.create_edge",
                "raw query write (f-string) in app.data_access.arango.activity_repository"
                "::ArangoActivityRepository.delete",
                "raw query write (f-string) in app.data_access.arango.base_repository"
                "::BaseArangoRepository.delete_edges",
                "raw query write (f-string) in app.data_access.arango.consent_repository"
                "::ArangoConsentRepository.delete",
                "raw query write (f-string) in app.data_access.arango.data_export_repository"
                "::ArangoDataExportRepository.delete",
                "raw query write (f-string) in app.data_access.arango.email_change_repository"
                "::ArangoEmailChangeRepository.delete",
                "raw query write (f-string) in app.data_access.arango.fertilizer_repository"
                "::ArangoFertilizerRepository.delete",
                "raw query write (f-string) in app.data_access.arango.membership_repository"
                "::ArangoMembershipRepository.delete",
                "raw query write (f-string) in app.data_access.arango.processing_restriction_repository"
                "::ArangoProcessingRestrictionRepository.delete",
                "raw query write (f-string) in app.data_access.arango.tank_repository::ArangoTankRepository.delete",
                # #1664 — ``ArangoUserRepository.delete`` runs its cascade through the
                # shared erasure executor instead of ``_remove_docs_for_user``. The route
                # reaches it only through the detector's ``.delete`` name fallback, as it
                # reached the helper before; the sinks moved, the reach did not.
                "module-level query write _REMOVE_USER in app.data_access.arango.erasure_executor"
                "::ArangoErasureExecutor._run_step",
                "module-level query write _REWRITE_REFERENCE in app.data_access.arango.erasure_executor"
                "::ArangoErasureExecutor._anonymize",
                "module-level query write _REWRITE_REFERENCE in app.data_access.arango.erasure_executor"
                "::ArangoErasureExecutor._pseudonymize",
                "self.collection.delete() in app.data_access.arango.base_repository::BaseArangoRepository._delete_doc",
                "self.collection.insert() in app.data_access.arango.base_repository::BaseArangoRepository._insert_doc",
                "self.collection.update() in app.data_access.arango.base_repository::BaseArangoRepository._update_doc",
                "self.collection.update() in app.data_access.arango.base_repository"
                "::BaseArangoRepository._update_doc_fields",
            }
        ),
    ),
    "privacy.router.download_export": (
        "REQ-025 §4.2a — PrivacyService.prepare_export_download increments download_count on the "
        "DataExportRequest. The Art.-15 evidence IS the collection of the export, so moving the "
        "write to another request would record a different event. One sink, measured. Since #1662 "
        "SCR-005 that sink is an atomic AQL increment rather than a full-model write-back, which "
        "could resurrect a record that expiry had just cleared.",
        frozenset(
            {
                (
                    "raw query write in app.data_access.arango.data_export_repository"
                    "::ArangoDataExportRepository.increment_download_count"
                )
            }
        ),
    ),
}


#: Reads that really do persist. **Open findings, not approvals.**
#:
#: This dict is not an allowlist and must not be read as one. Every entry is a
#: route that answers a ``GET`` and writes to the database while doing it —
#: measured on 2026-09-16 by the detector this file now carries, reported out of
#: the `2026-09-16-write-route-guard` group, and deliberately **not** fixed there:
#: repairing ten handlers is a different change from building the detector, and
#: mixing them would have made neither reviewable.
#:
#: They are listed for one reason only: so the detector can go live today instead
#: of after the repairs. A read that persists and is **not** listed here turns the
#: sweeps red immediately, which is the property #1443 asked for.
#:
#: **All ten are filed**, and the numbers belong here rather than in a commit
#: message: **#1461** is the class issue and carries every one of them with a
#: severity per route; **#1460** is the anonymous glossary path, split out because
#: it is the only entry an unauthenticated caller reaches.
#:
#: Two rules keep this from becoming the thing it replaces.
#: `test_every_finding_is_still_a_persisting_read` deletes the excuse the moment a
#: route stops writing, and `test_the_finding_list_only_shrinks` is a ratchet
#: against :data:`_MEASURED_2026_09_16` — against the IDS, not against their
#: count, so that repairing one and listing the next is not a green diff either.
#: **Empty since #1461/#1460, and that is the acceptance condition.** All ten
#: measured reads were answered: eight were repaired into pure reads and two are
#: recorded as decisions in :data:`_INTENTIONAL_PERSISTING_READS` above, each bound
#: to the writes it was measured reaching.
#:
#: This stays a dict rather than being deleted. It is what a NEWLY detected
#: writing ``GET`` would have to be added to, and
#: `test_the_finding_list_only_shrinks` refuses that against
#: :data:`_MEASURED_2026_09_16` — so the empty dict is the ratchet's resting
#: position, not a leftover. A new finding is a conversation and an issue; there
#: is no id left that this list will accept.
_PERSISTING_READ_FINDINGS: dict[str, str] = {}

#: The ten findings **as measured** on 2026-09-16, by id. The ratchet, and it is
#: deliberately not a length.
#:
#: `len(_PERSISTING_READ_FINDINGS) <= 10` was the first version and SEC-001 of the
#: #1443 security review took it apart in one sentence: an EXCHANGE passes it. Repair
#: one route, add the next one that was found, and the count is ten again — the list
#: has grown a new open defect while every test stays green, which is precisely the
#: drift the ratchet was built to make impossible. Only the identities can express
#: "this set may shrink and may not gain a member".
#:
#: Removing an id from BOTH places as its route is repaired is a two-line diff with
#: an obvious reason. Adding one here is not a diff anybody should be able to write
#: without the conversation — the date in the name says what this set is.
_MEASURED_2026_09_16: frozenset[str] = frozenset(
    {
        "auth.router.oauth_callback",
        "privacy.router.download_export",
        "glossar.public_router.public_get_term",
        "glossar.router.get_term",
        "ki_assistent.tenant_router.get_daily_tip",
        "ki_assistent.tenant_router.get_tips",
        "onboarding.tenant_router.get_onboarding_state",
        "user_preferences.tenant_router.get_preferences",
        "dashboard.tenant_router.get_widget_catalog",
        "season.tenant_router.get_site_season_state",
    }
)


class Reason(enum.Flag):
    """Why a tenant-scoped write route may stay on bare `get_current_tenant`.

    **The category is machine-readable because the prose was not** (SEC-003 of the
    #1443 review). Every entry below used to be a sentence, and the only thing
    holding those sentences to the code was `len(reason) >= 12`. #1441 is what that
    costs: an entry read "that branch is gated inline on the domain role", the
    module carried no `require_*` at all, and the sweep walked past an exploitable
    write for months because nobody can grep a paragraph.

    A flag can be selected on. `test_every_computation_entry_really_writes_nothing`
    takes every :attr:`COMPUTATION` entry and asserts `not persists(endpoint)` with
    the detector this file already carries — the claim is measured now, not
    believed. The prose stays alongside, because *which* computation and *whose*
    row is still a thing only a sentence can say.
    """

    #: The row belongs to the CALLER, not to the tenant: favourites, notification
    #: state, onboarding progress, personal preferences. A domain role is the wrong
    #: axis — a viewer manages their own inbox exactly as a lead does.
    PER_USER = enum.auto()

    #: A data-subject right (DSGVO Art. 15-21). Gating it on rank would make the
    #: right depend on rank, which is what the article does not allow.
    DATA_SUBJECT_RIGHT = enum.auto()

    #: Reads its inputs, returns a result, persists NOTHING. This is the claim the
    #: detector checks; an entry carrying it and reaching a write is a finding.
    COMPUTATION = enum.auto()

    #: Part of the handler writes and is rank-gated INSIDE it, at a named call site
    #: with a test that drives both directions. Exactly one entry carries this, and
    #: it is the one #1441 was about; it is not a category to grow casually, since a
    #: gate in a branch is invisible to every sweep in this file.
    RANK_GATED_INLINE = enum.auto()


#: Tenant-scoped write routes that may resolve `ctx` through bare
#: `get_current_tenant`. Each entry is `(category, prose)` — see :class:`Reason`.
_TENANT_ALLOWLIST: dict[str, tuple[Reason, str]] = {
    # ── Per-user state. The row belongs to the caller, not to the tenant, so a
    # domain role is the wrong axis: a viewer manages their own favourites,
    # notifications and onboarding exactly as a lead does.
    "favorites.tenant_router.add_favorite": (
        Reason.PER_USER,
        "per-user favourite",
    ),
    "favorites.tenant_router.remove_favorite": (
        Reason.PER_USER,
        "per-user favourite",
    ),
    "notifications.tenant_router.mark_read": (
        Reason.PER_USER,
        "per-user notification state",
    ),
    # This entry used to read "that branch is gated inline on the domain role".
    # It was prose, nothing held it against the code, and it was never true (#1441):
    # the whole module carried no `require_*` at all, so a viewer confirmed a care
    # reminder with one tap and produced the two writes the direct route refuses
    # them. The reason now names the call site and the test that reads it, because a
    # reason nobody can check is worse than no entry — it is what kept this sweep
    # walking past the route.
    "notifications.tenant_router.mark_acted": (
        Reason.PER_USER | Reason.RANK_GATED_INLINE,
        "per-user notification state — and, for a care.* notification with a confirm "
        "action, a CareConfirmation and a WateringLog. That one branch is rank-gated "
        "inside the handler at app/api/v1/notifications/tenant_router.py::mark_acted, "
        "on MembershipEngine.can_edit_resource — the same authority "
        "require_permission('watering-log', CREATE) resolves through on the direct "
        "route. tests/api/test_notification_act_role_gate.py asserts both directions "
        "against recording repositories, so this sentence is checked and not merely "
        "written down",
    ),
    "notifications.tenant_router.update_preferences": (
        Reason.PER_USER,
        "per-user notification preferences",
    ),
    "notifications.tenant_router.subscribe_pwa": (
        Reason.PER_USER,
        "per-user push subscription",
    ),
    "notifications.tenant_router.unsubscribe_pwa": (
        Reason.PER_USER,
        "per-user push subscription",
    ),
    "notifications.tenant_router.send_test_notification": (
        Reason.PER_USER,
        "sends to the caller's own configured channel with a fixed body, rate-limited per client address",
    ),
    "onboarding.tenant_router.skip_onboarding": (
        Reason.PER_USER,
        "per-user onboarding progress",
    ),
    "onboarding.tenant_router.reset_onboarding": (
        Reason.PER_USER,
        "per-user onboarding progress",
    ),
    "onboarding.tenant_router.update_onboarding_progress": (
        Reason.PER_USER,
        "per-user onboarding progress",
    ),
    "user_preferences.tenant_router.update_preferences": (
        Reason.PER_USER,
        "per-user preferences",
    ),
    "ki_assistent.tenant_router.create_conversation": (
        Reason.PER_USER,
        "creates an empty per-user conversation record and calls no provider; send_message, which does, is gated",
    ),
    # ── A data-subject right. Gating erasure on a domain role would make the
    # right depend on rank, which is exactly what Art. 17 does not allow.
    "ki_assistent.tenant_router.delete_conversation": (
        Reason.DATA_SUBJECT_RIGHT,
        "DSGVO Art. 17 erasure of the caller's own conversation",
    ),
    # ── POST-as-computation. Reads its inputs, returns a result, writes nothing.
    # Verified per route: none of the service methods behind these reaches a
    # repository create/update/delete.
    "nutrient_plans.tenant_router.calculate_dosages": (
        Reason.COMPUTATION,
        "computation, no write",
    ),
    "nutrient_calculations.router.area_dosing": (
        Reason.COMPUTATION,
        "computation, no write",
    ),
    # The three below joined this list in #1402, and the route they took here is
    # worth stating: they were not "ungated members-only routes" being written
    # down — they answered an ANONYMOUS caller, and each of them reads the
    # fertilizer catalogue with `FertilizerService.get_fertilizer`, whose
    # `tenant_key=""` default skips its own ownership check. Gating them on
    # `get_current_tenant` and threading `ctx.tenant_key` into that call is what
    # moved them from "unauthenticated, reading across tenants" to "computation
    # any member may run" — the same category their `area_dosing` sibling was
    # always in. The four remaining calculators in that module need no entry:
    # they carry the router-level gate and no `ctx` parameter, so this sweep's
    # question ("is `ctx` bare?") does not apply to them at all.
    "nutrient_calculations.router.mixing_protocol": (
        Reason.COMPUTATION,
        "computation over the caller's own catalogue, no write",
    ),
    "nutrient_calculations.router.mixing_safety": (
        Reason.COMPUTATION,
        "computation over the caller's own catalogue, no write",
    ),
    "nutrient_calculations.router.ec_budget": (
        Reason.COMPUTATION,
        "computation over the caller's own catalogue, no write",
    ),
    # These four reach no database at all — they compute from the request body
    # alone. They are listed here rather than left silent because the router-level
    # gate #1402 gave them removed `ctx` from their signatures, and the version of
    # this sweep that read `inspect.signature` therefore stopped reporting them
    # while the third question was satisfied by the router. Four routes reported by
    # nothing, recorded nowhere: the opt-in drift this file exists to catch, moved
    # one level up by the change that was closing it. The sweep now reads the
    # effective chain, so the router-level gate is visible to it and these four
    # need the same written decision as their siblings.
    "nutrient_calculations.router.flushing_protocol": (
        Reason.COMPUTATION,
        "computation from the request body, no read, no write",
    ),
    "nutrient_calculations.router.runoff_analysis": (
        Reason.COMPUTATION,
        "computation from the request body, no read, no write",
    ),
    "nutrient_calculations.router.water_mix": (
        Reason.COMPUTATION,
        "computation from the request body, no read, no write",
    ),
    "nutrient_calculations.router.water_mix_reverse": (
        Reason.COMPUTATION,
        "computation from the request body, no read, no write",
    ),
    "tanks.tenant_router.calculate_ec_dilution": (
        Reason.COMPUTATION,
        "computation over a read tank, no write",
    ),
    "plant_instances.tenant_router.validate_planting": (
        Reason.COMPUTATION,
        "validation, no write",
    ),
    "tasks.tenant_router.validate_hst": (
        Reason.COMPUTATION,
        "validation, no write",
    ),
    "actuators.tenant_router.test_rule": (
        Reason.COMPUTATION,
        "dry-run of a control rule against supplied readings, no side effects",
    ),
}

#: Installation-wide write routes that may resolve their caller through bare
#: `get_current_user`. The bar is higher here: these change configuration for
#: everyone, so an entry needs a reason that survives the question "what stops a
#: viewer in an unrelated tenant from doing this?".
#: Empty, and that is the point. It held one entry —
#: ``admin.recognition.router.start_acquisition`` — whose reason was "deliberate and
#: documented at the site". The route's docstring did say so; the pre-merge review of
#: #1385 read it and found the argument justified the *card* being reachable, not the
#: *route* being open, while the identical ``/acquire`` on the ``admin/pests`` sibling
#: carried ``require_platform_admin`` all along. The entry is deleted rather than
#: reworded (#1401): an allowlist that writes a drift down as approved is worse than no
#: allowlist, because the next reader takes it as a decision someone made on purpose.
_ADMIN_ALLOWLIST: dict[str, str] = {}


#: THE THIRD QUESTION (#1402), and it is a different one from the two above.
#:
#: Both selectors above key on the PRESENCE of a specific weak dependency: the
#: tenant half asks whether `ctx` IS `get_current_tenant`, the admin half whether
#: `get_current_user` appears. A route carrying NO dependency at all fails both
#: tests in the passing direction, and 133 write operations lie outside both
#: prefixes besides. Measured on 2026-09-12, before this question existed:
#: **24** of 439 mounted write operations resolved no authorisation dependency
#: anywhere — fourteen of them not deliberately public. Seven were the
#: calculators under `/api/v1/calculations`, invisible because they fall through
#: both prefixes; seven were under `/t/{tenant_slug}/nutrient-calculations`,
#: which the tenant selector SEES and does not report. Three of those seven also
#: read the fertilizer catalogue with `FertilizerService.get_fertilizer`'s
#: `tenant_key=""` default, which skips its own ownership check.
#:
#: This question asks instead: does the effective dependency chain of this write
#: operation contain ANY authorisation dependency? It reads `route.dependant`
#: transitively rather than `inspect.signature`, so a router-level
#: `APIRouter(dependencies=[...])` counts — which is how the fourteen were fixed,
#: and a per-handler read would have reported them as still open.
#:
#: It is deliberately coarse. "Carries some authorisation" is not "carries the
#: RIGHT authorisation": the installation-wide master data behind bare
#: `get_current_user` (#1402 group B) passes this question and is still a defect.
#: A coarse question that cannot be fooled by absence is worth more than a
#: precise one with a hole, and the precise one is the next refinement.
#: Dependencies that actually REFUSE a caller, by qualified name. A set of exact
#: names and not substring markers, because the first version of this list used
#: substrings and three of them were wrong in the permissive direction: `"mcp_"`
#: matched `require_mcp_enabled` (an operator feature flag that 404s when MCP is
#: off and authorises nobody when it is on) plus `get_mcp_dispatcher` and
#: `get_mcp_session_store`; `"api_key"` matched the `APIKeyHeader` scheme object,
#: which carries `auto_error=False` and therefore never refuses anything. No route
#: was saved by a weak match alone when this was found, so it was latent — but a
#: write route added under `/api/v1/mcp` carrying only `get_mcp_dispatcher` would
#: have counted as authorised and been anonymously reachable.
#:
#: `__qualname__` rather than `__name__`: the three `require_*` factories all
#: return a closure called `_check`, indistinguishable by name and exact by
#: qualified name.
_AUTHORISATION: frozenset[str] = frozenset(
    {
        "get_current_user",
        "get_current_tenant",
        "require_platform_admin",
        "_require_platform_admin",
        "require_permission.<locals>._check",
        "require_tenant_role.<locals>._check",
        # The header-resolved sibling of the line above (#1422). The routers under
        # `/plant-instances/{key}/phases` and `/care-reminders/plants/{key}` carry no
        # `/t/{slug}/` segment, so `require_tenant_role` has no tenant to rank
        # against; this one reads the tenant `require_owned_plant` already resolved.
        "require_active_tenant_role.<locals>._check",
        "require_admin_scope.<locals>._check",
        "require_attachment_permission.<locals>._dependency",
        "get_mcp_principal",
        # #1402 group C. Refuses a caller whose ACTIVE TENANT does not own the plant
        # named in the path, on the two global routers that address one by key.
        # Classified because this guard demanded it: added to the app without an
        # entry in either set, it turned
        # `test_every_auth_shaped_dependency_is_classified` red one session after
        # that test was written. That is the vocabulary drift the rule exists for.
        "require_owned_plant",
    }
)

#: The subset above that gates on MORE than "is authenticated" or "is a member".
#:
#: Named for that definition rather than for "role", which it is not: the set also
#: holds `require_owned_plant`, and ownership is a different axis from rank. The
#: earlier name `_ROLE_GATES` invited the reading that a route carrying any member
#: here has been rank-checked.
#:
#: That reading was wrong for seven routes until #1422: they carried
#: `require_owned_plant` and no rank check, so a tenant *viewer* could drive a phase
#: transition accepting `force: bool` and an irreversible `DELETE` on recorded
#: history. They now carry `require_active_tenant_role` too, and
#: `tests/api/test_plant_scoped_global_routers_api.py` asserts the refusal per route.
#: Membership in this set still does not imply a rank check, which is why the name
#: says what it says.
_MORE_THAN_MEMBERSHIP: frozenset[str] = frozenset(
    {
        "require_permission.<locals>._check",
        "require_tenant_role.<locals>._check",
        # The header-resolved sibling of the line above (#1422). The routers under
        # `/plant-instances/{key}/phases` and `/care-reminders/plants/{key}` carry no
        # `/t/{slug}/` segment, so `require_tenant_role` has no tenant to rank
        # against; this one reads the tenant `require_owned_plant` already resolved.
        "require_active_tenant_role.<locals>._check",
        "require_admin_scope.<locals>._check",
        "require_platform_admin",
        "_require_platform_admin",
        "require_attachment_permission.<locals>._dependency",
        # More than "is authenticated" and more than "is a member": it gates on
        # ownership of the addressed resource, which is a different axis from role
        # and strictly narrower than either. A route carrying it is not bare.
        "require_owned_plant",
    }
)

#: Dependencies whose NAME reads like authorisation and which authorise nobody.
#: Enumerated with a reason so the classification cannot drift silently:
#: `test_every_auth_shaped_dependency_is_classified` fails on a name in the live
#: app that matches neither set — the obsolescence rule the allowlists already
#: follow, applied one level up to the vocabulary itself.
_NOT_AUTHORISATION: dict[str, str] = {
    "require_mcp_enabled": "operator feature flag; 404s when MCP is off, authorises nobody when on",
    "require_ai_tenant_enabled": "REQ-031 feature flag, not a caller check",
    "require_ai_feature_flag": "REQ-031 operator flag, not a caller check",
    "get_is_platform_admin": "returns a bool for the caller to branch on; refuses nobody",
    "get_authenticated_with_api_key": (
        "returns a bool (key vs session) the tenant deletion hands its service (#1791); refuses nobody"
    ),
    "APIKeyHeader": "scheme object with auto_error=False - extracts a header, never refuses",
    "HTTPBearer": "scheme object; extraction only, the provider decides",
    "get_auth_provider": "constructs the provider; get_current_user is what calls it",
    "get_auth_service": "service dependency",
    "get_tenant_service": "service dependency",
    "get_tenant_repo": "repository dependency",
    "get_user_service": "service dependency",
    "get_user_preference_service": "service dependency",
    "get_oauth_engine": "engine dependency",
    "get_active_tenant_key": "resolves the header slug; the refusal is the get_current_user beneath it",
    "get_active_tenant_context": "same - authorisation is the get_current_user it depends on",
    "get_mcp_dispatcher": "infrastructure; dispatches after get_mcp_principal has decided",
    # A FACTORY, not a gate, and it was in `_AUTHORISATION` for one commit — the
    # same mistake the substring `"mcp_"` made, repeated by hand after the
    # substrings were removed. `dependencies.py:879` constructs
    # `McpAuthenticator(...)` and refuses nobody; the refusal is
    # `authenticator.authenticate(...)`, called inside the handler. Its sibling
    # `get_task_entity_guard` has the same shape and was correctly left out,
    # which is what made the inconsistency visible.
    "get_mcp_authenticator": "constructs the authenticator; the handler's authenticate() call is the refusal",
    "get_mcp_session_store": "infrastructure",
}

#: Substrings that make a dependency name "auth-shaped" for the classification
#: guard. Deliberately generous: a name caught here and in neither set is a test
#: failure asking for a one-line decision, which is cheap. A name NOT caught here
#: is assumed infrastructure, which is the residual risk and why this leans wide.
#: Measured at this head: 27 of ~90 distinct names mounted on write routes match.
#: `mcp` and `bearer` are here because the coverage test below found them
#: missing: `get_mcp_dispatcher`, `get_mcp_session_store` and `HTTPBearer` were
#: all classified — somebody had already decided they authorise nobody — and the
#: filter could not see any of them, so a future sibling would have gone
#: unreported. A vocabulary the guard cannot read is not a classification.
_AUTH_SHAPED = (
    "auth",
    "admin",
    "tenant",
    "user",
    "principal",
    "permission",
    "role",
    "require_",
    "key",
    "mcp",
    "bearer",
)


#: Write operations that legitimately resolve no authorisation at all. Every entry
#: is an endpoint a caller must reach BEFORE having a session, or one the product
#: publishes on purpose. Anything else here is a defect wearing a reason.
_PUBLIC_ALLOWLIST: dict[str, str] = {
    "auth.router.login": "issues the session; cannot require one",
    "auth.router.register": "creates the account; cannot require one",
    "auth.router.refresh": "presents the refresh cookie, not an access token",
    "auth.router.logout": "must succeed for an expired or absent session",
    "auth.router.request_password_reset": "the caller has lost the credential",
    "auth.router.confirm_password_reset": "authorised by the emailed token",
    "auth.router.verify_email": "authorised by the emailed token",
    "auth.router.redeem_device_pairing": "authorised by the pairing code",
    "privacy.router.confirm_email_change": "authorised by the emailed token (REQ-025)",
    "ki_assistent.public_router.public_ask": "REQ-031 light-mode probe, published on purpose",
    # Authenticates from the API key in the REQUEST BODY, inside the handler, the
    # way `login` authenticates from a password — so it carries no transport
    # credential and never will. It was previously exempt by accident:
    # `get_mcp_authenticator` was miscounted as authorisation and this is the one
    # live route whose only `_AUTHORISATION` member it was. The exemption is the
    # same; what changed is that it is now written down.
    #
    # Not unguarded: `require_mcp_enabled` 404s the route when MCP is off, the
    # auth rate limiter applies per IP, and REQ-033 SEC-003 collapses the
    # valid-non-service case into the same generic 401 so it cannot be used as an
    # oracle.
    "auth.router.validate_service_account": "authenticates from the key in the body, like login",
    # The OAuth2 redirect back from the provider. It carries no session — the
    # session is what it is about to issue — and it carries no transport
    # credential either: the caller is a browser following a 302, and everything
    # the handler trusts comes out of the `state`/`code` pair it validates against
    # the provider itself. `login` and `register` are exempt for the same reason,
    # one step earlier in the same flow.
    #
    # It was previously exempt by ACCIDENT, as an entry in
    # `_PERSISTING_READ_FINDINGS` — an open-defect list every sweep in this file
    # skips. #1461 took it off that list, because a protocol-fixed verb is not a
    # defect anybody can repair, and that removal is what makes the exemption
    # visible here where the third question can see it.
    "auth.router.oauth_callback": "the OAuth2 redirect carries no session; it issues one (REQ-023)",
}


def _authorisation_chain(operation: Operation) -> list[str]:
    """Every dependency name in the operation's effective chain, router level included."""
    dependant = getattr(operation.route, "dependant", None)
    if dependant is None:  # pragma: no cover - defensive
        return []

    names: list[str] = []
    seen: set[int] = set()

    def walk(node: Any) -> None:
        for sub in node.dependencies:
            if id(sub) in seen:
                continue
            seen.add(id(sub))
            call = sub.call
            names.append(getattr(call, "__qualname__", type(call).__name__))
            walk(sub)

    walk(dependant)
    return names


def _resolves_authorisation(operation: Operation) -> bool:
    return bool(set(_authorisation_chain(operation)) & _AUTHORISATION)


def _resolves_bare_tenant_context(operation: Operation) -> bool:
    """Authenticated and a member, and nothing beyond that.

    Read from the effective chain rather than `inspect.signature`. The signature
    read had a blind spot that #1402 created and then had to close: moving the
    `nutrient_calculations` gate onto its ROUTER removed `ctx` from four
    handlers' signatures, so this sweep stopped seeing them while the third
    question was satisfied by the router-level `get_current_tenant`. Four routes
    were reported by nothing and recorded in no allowlist — the opt-in drift this
    file exists to catch, relocated one level up.
    """
    names = set(_authorisation_chain(operation))
    return "get_current_tenant" in names and not (names & _MORE_THAN_MEMBERSHIP)


def _resolves_bare_user(operation: Operation) -> bool:
    """Authenticated, with no role or scope gate above it."""
    names = set(_authorisation_chain(operation))
    return "get_current_user" in names and not (names & _MORE_THAN_MEMBERSHIP)


#: THE FOURTH QUESTION (#1402 group B): installation-wide master data.
#:
#: These routers are mounted globally and every row in them is shared by the whole
#: installation — one `GrowthPhase` is the phase REQ-003's state machine runs on,
#: for everyone. They carried `APIRouter(dependencies=[Depends(get_current_user)])`
#: and no role gate, so any authenticated member of any tenant could create, change
#: or delete them. Their immediate siblings `companion_planting` and
#: `family_relationships` gated every write on `require_platform_admin` all along,
#: which is what made the omission visible rather than arguable.
#:
#: The third question passes them: `get_current_user` *is* authorisation, just not
#: enough of it. This one asks the narrower thing.
#:
#: **Scoped to a named set of modules, deliberately.** Measured on this tree, 133
#: write operations lie outside both the tenant and the admin prefix, and 117 of
#: them resolve only `get_current_user`. Most are legitimately member-writable — a
#: caller creates their own tenant, exercises their own data-subject rights, edits
#: their own profile — so a blanket rule here would be wrong in more places than it
#: is right. The remaining triage is #1402's own follow-up.
#:
#: What this does close is the per-route drift: a new write route added to any of
#: these seven inherits nothing, and this test names it. A new *module* of the same
#: kind is not covered, which is a rarer event than a new route and is said out
#: loud rather than implied.
_INSTALLATION_WIDE_MODULES: dict[str, str] = {
    "growth_phases": "the phases REQ-003's state machine runs on, installation-wide",
    "location_types": "the location vocabulary every tenant picks from",
    "profiles": "requirement and nutrient profiles shared by every tenant",
    "lifecycle_configs": "per-species lifecycle overrides, one row per species for everyone",
    "activities": "the activity catalogue every tenant's plans reference",
    "crop_rotation": "the rotation rules every bed plan is validated against",
    "enrichment": "external-source enrichment configuration for the installation",
    # #1501. Two modules of exactly the kind the paragraph above says this set does
    # not catch on its own, found by the classification rule below rather than by
    # anybody remembering to add them.
    "phase_sequences": (
        "phase definitions, sequences and their entries — no tenant_key on any of "
        "the three models, so one row is the row every tenant's lifecycle resolves"
    ),
    "ipm": (
        "the pest / disease / treatment catalogue; ipm/tenant_router.py states in "
        "its own docstring that these three stay global reference data"
    ),
}

#: Every other module that mounts a write on the **global** router, with the reason
#: it is not installation-wide master data — #1501.
#:
#: The dict above was an opt-in list, and its own docstring said so: "a new *module*
#: of the same kind is not covered". That is not a hypothetical. `phase_sequences`
#: and `ipm` are two such modules; between them they mounted **twenty** ungated
#: writes on installation-wide catalogues — including the ``DELETE`` on the phase
#: definition REQ-003's state machine runs on — and every sweep in this file was
#: green the whole time, because neither name had ever been typed into a list.
#:
#: This closes that one level up, the same way
#: `test_every_auth_shaped_dependency_is_classified` closes the dependency
#: vocabulary: a module is not *reported*, it is *classified*. Adding a new global
#: router without deciding which half it belongs in fails
#: `test_every_global_write_module_is_classified` with the module's name in the
#: message. The decision stays a human one; what changes is that it has to be made.
#:
#: Scoped to the global surface deliberately — a tenant-prefixed or `/api/v1/admin`
#: module is answered by the first three questions and does not need a fourth.
_NOT_INSTALLATION_WIDE: dict[str, str] = {
    "auth": "session lifecycle; a caller reaches login/register/reset before having one",
    "users": "the caller's own account, sessions and federated identities",
    "privacy": "DSGVO Art. 15-21 self-service; the rows belong to the user",
    "tenants": "tenant lifecycle and membership, gated on require_admin_scope",
    "mcp": "REQ-033 protocol surface, gated on get_mcp_principal",
    "ki_assistent": "REQ-031 light-mode probe, published on purpose",
    # `glossar` stood here until #1515, and its removal is the obsolescence rule
    # below working rather than breaking. The entry existed *because* of a
    # persisting read: `public_get_term` answered an anonymous GET and wrote a
    # cache row through `_store_cache`, so the #1443 detector counted the route as
    # a global write and the module needed a classification. #1515 removed that
    # write, `persists(public_get_term)` is now False, and the module's real
    # writes live on the two surfaces the other selectors already own —
    # `/t/{slug}/glossary/term/{slug}/generate` (tenant) and
    # `/api/v1/admin/glossary/*` (admin, behind `require_platform_admin` since
    # #536). Nothing is left on the global surface, so an entry claiming to
    # classify one would be an exemption nobody can check.
    #
    # Left as a comment rather than deleted silently: the next reader wondering
    # why the glossary is unclassified here should find the answer beside the gap,
    # and `test_every_global_write_module_is_classified` will demand a real entry
    # again the moment the module mounts a global write.
    "care_reminders": "per-plant tenant data; require_owned_plant + require_active_tenant_role",
    "phases": "per-plant tenant data; require_owned_plant + require_active_tenant_role",
    "calculations": "POST-as-computation — reads its inputs, returns a result, persists nothing",
    "companion_planting": "already require_platform_admin on both writes",
    "family_relationships": "already _require_platform_admin on all three writes",
    "botanical_families": (
        "global-only catalogue, gated by require_platform_admin_for_global_catalogue "
        "called in the handler body (#1120) rather than as a dependency, so the "
        "chain-based gate above cannot see it"
    ),
    "species": "hybrid catalogue: own row → rank, global seed → platform admin, foreign → 404 (#808)",
    "cultivars": "hybrid catalogue, same three-way gate in SpeciesService (#1090)",
    "substrates": "hybrid catalogue, same three-way gate in SubstrateService (#1195)",
    "imports": (
        "tenant-owned staged work, not catalogue data: the job carries an uploaded "
        "CSV and is scoped by ImportJob.tenant_key, with the rank decided in "
        "ImportService (#1110 confirm, #1501 upload/read/delete)"
    ),
}

_PLATFORM_ADMIN_GATES = frozenset({"require_platform_admin", "_require_platform_admin"})


def _excused_as_an_open_finding(operation: Operation) -> bool:
    """A detected persisting read whose repair is tracked in :data:`_PERSISTING_READ_FINDINGS`.

    **Not an approval and not an allowlist.** The four sweeps below skip these so
    the detector could go live on the day it was built rather than on the day ten
    unrelated handlers were repaired. Every one of them is a measured defect, the
    entry dies the moment the route stops writing, and the list may not grow.
    """
    return operation.method in READ_METHODS and operation.id in _PERSISTING_READ_FINDINGS


def _module_of(operation: Operation) -> str:
    return operation.module.removeprefix("app.api.v1.").split(".")[0]


def _installation_wide_write_operations() -> list[Operation]:
    """The installation-wide writes: a classified module AND a global path.

    Both halves, since #1501. The module alone was enough while every classified
    module mounted exactly one router; `ipm` does not. Its `tenant_router` writes
    inspections, treatment applications and pest-image contributions — rows that
    DO carry a ``tenant_key`` and are correctly gated on ``require_permission`` /
    ``require_attachment_permission``. Selecting them by module name would have
    demanded ``require_platform_admin`` on four tenant-scoped routes, i.e. the
    over-rejecting fix `test_the_reads_are_not_gated` exists to prevent, one door
    along.
    """
    return [op for op in _global_write_operations() if _module_of(op) in _INSTALLATION_WIDE_MODULES]


def _global_write_operations() -> list[Operation]:
    """Write operations on neither the tenant nor the admin prefix — #1501.

    The residue of the two prefix selectors, and the surface the fourth question
    is asked of. Computed from the path rather than from a list of module names,
    because a list of module names is what let twenty ungated writes through.
    """
    return [
        op for op in mounted_write_operations() if TENANT_PREFIX not in op.path and not op.path.startswith(ADMIN_PREFIX)
    ]


def _tenant_write_operations() -> list[Operation]:
    return [op for op in mounted_write_operations() if TENANT_PREFIX in op.path]


def _admin_write_operations() -> list[Operation]:
    return [op for op in mounted_write_operations() if op.path.startswith(ADMIN_PREFIX)]


def _format(operations: list[Operation]) -> str:
    return "\n  ".join(f"{op.method:6} {op.path}  ({op.id})" for op in sorted(operations, key=lambda o: o.id))


class TestTheWalk:
    """The walk itself, pinned — a sweep that finds nothing is not a clean result."""

    def test_it_finds_a_realistic_number_of_write_operations(self):
        """A floor, not an exact count: the surface grows with every feature.

        Its job is to fail loudly if the walk ever returns almost nothing, which
        is what a flat read does and what would make every assertion below vacuous.
        """
        assert len(mounted_write_operations()) > 300

    def test_the_walk_sees_what_a_flat_read_cannot(self):
        """`include_router` leaves wrappers; reading `api_router.routes` flat misses them."""
        flat = [r for r in api_router.routes if getattr(r, "endpoint", None) is not None]
        assert len(flat) < len(mounted_write_operations()) / 5

    def test_both_scopes_are_actually_populated(self):
        """Either selector matching nothing would make its assertion vacuous."""
        assert len(_tenant_write_operations()) > 200
        assert len(_admin_write_operations()) > 30

    def test_the_sweep_runs_against_the_full_route_surface(self):
        """In light mode half the admin surface is not mounted, and the sweep goes quiet.

        `api/v1/router.py` mounts `auth`, `privacy`, `admin/platform` and
        `admin/oidc-providers` only when `kamerplanter_mode == "full"`. Measured:
        38 admin write operations under `full`, **19** under `light`. The sweep
        passes in both — so under `light` it certifies half the surface while
        reading exactly the same.

        That is not hypothetical. `/admin/oidc-providers` (#1399) is one of the
        routers that disappears, and it is the finding this sweep is credited with.
        Run under `light`, it would have reported nothing and looked identical.

        So the mode is asserted rather than assumed, and this **fails** rather than
        skipping: a skip is indistinguishable from a pass in a CI summary, which is
        the property that let the original 37 accumulate. The floor above is raised
        to 30 for the same reason — it is now a number only `full` can satisfy, so
        deleting this test does not silently restore the hole.
        """
        from app.config.settings import settings

        assert settings.kamerplanter_mode == "full", (
            f"This sweep only covers the full route surface; it is running under "
            f"`{settings.kamerplanter_mode}`, where the auth, privacy, platform-admin "
            f"and OIDC-provider routers are not mounted at all. Run it with "
            f"KAMERPLANTER_MODE=full, or extend it with a light-mode expectation of "
            f"its own — but do not let it report green over half the surface."
        )


class TestTenantWriteGates:
    def test_no_tenant_write_route_resolves_ctx_through_bare_get_current_tenant(self):
        offenders = [
            op
            for op in _tenant_write_operations()
            if _resolves_bare_tenant_context(op)
            and op.id not in _TENANT_ALLOWLIST
            and not _excused_as_an_open_finding(op)
        ]
        assert not offenders, (
            "These tenant-scoped write routes resolve `ctx` through bare `get_current_tenant`, "
            "so every member of the tenant may call them regardless of role. Gate them the way "
            "their siblings are gated, or add them to _TENANT_ALLOWLIST with a reason:\n  " + _format(offenders)
        )

    def test_every_allowlisted_tenant_route_still_exists_and_is_still_ungated(self):
        """An entry that no longer applies fails, rather than sitting there forever.

        Both directions: a route that was deleted, and a route that has since been
        gated. The second is the one that rots quietly — the allowlist would go on
        excusing a route that no longer needs excusing, and the next reader would
        take the entry as a statement that the route must stay open.
        """
        by_id = {op.id: op for op in _tenant_write_operations()}
        stale = []
        for route_id, (_category, reason) in _TENANT_ALLOWLIST.items():
            operation = by_id.get(route_id)
            if operation is None:
                stale.append(f"{route_id}: no such tenant write route ({reason})")
            elif not _resolves_bare_tenant_context(operation):
                stale.append(f"{route_id}: now gated, drop the entry ({reason})")
        assert not stale, "Obsolete _TENANT_ALLOWLIST entries:\n  " + "\n  ".join(stale)

    def test_every_reason_is_written_out(self):
        """A blank or placeholder reason is an entry nobody has to justify.

        Still asserted, and still the weakest rule in the file: it says a sentence
        is present, not that it is true. That is why every entry also carries a
        :class:`Reason`, and why the claim a category makes is measured below.
        """
        for route_id, (category, reason) in _TENANT_ALLOWLIST.items():
            assert len(reason) >= 12, f"{route_id} carries no usable reason: {reason!r}"
            assert category, f"{route_id} carries no Reason category"

    def test_every_computation_entry_really_writes_nothing(self):
        """SEC-003: the one claim in this list a machine can check, checked.

        Thirteen entries say "computation, no write" in one wording or another. Not
        one of them was ever held against the code — the only rule was that the
        sentence be twelve characters long — and #1441 is what a sentence nobody
        checks is worth: it read "gated inline on the domain role" over a module
        with no gate at all, and the sweep walked past an exploitable write.

        The detector this file already carries answers exactly this question, so the
        claim stops being prose. A `COMPUTATION` entry whose route reaches a
        persistence write is a **finding**: the entry is not to be reworded into a
        different category to make this green, it is to be reported.
        """
        by_id = {}
        for _method, _path, endpoint, _route in mounted_operations():
            by_id.setdefault(_operation_id(endpoint), endpoint)

        writing = []
        for route_id, (category, reason) in _TENANT_ALLOWLIST.items():
            if Reason.COMPUTATION not in category:
                continue
            endpoint = by_id.get(route_id)
            if endpoint is None:
                continue  # covered by the obsolescence rule above
            path = write_path_of(endpoint)
            if path is not None:
                writing.append(f"{route_id} ({reason})\n      " + "\n      ".join(path))
        assert not writing, (
            "These routes are allowlisted as COMPUTATION — 'reads its inputs, returns a result, "
            "writes nothing' — and the call graph says they persist. This is a new finding, not a "
            "wording problem: file it before touching the entry, and do not move it to another "
            "category to make this green:\n  " + "\n  ".join(writing)
        )

    def test_the_computation_category_is_populated(self):
        """The control. A selector that matches nothing certifies nothing.

        Measured on 2026-09-16: thirteen of the twenty-seven entries claim to write
        nothing. Were the category renamed or dropped from every entry, the
        assertion above would pass over an empty loop and read exactly as green.
        """
        computations = [rid for rid, (category, _) in _TENANT_ALLOWLIST.items() if Reason.COMPUTATION in category]
        assert len(computations) >= 13, (
            f"only {len(computations)} entries carry Reason.COMPUTATION, down from the thirteen measured "
            "on 2026-09-16. Either routes were repaired — then lower this number in the same diff — or "
            "the claim moved into prose again, where nothing checks it."
        )

    def test_the_allowlist_is_small(self):
        """A ceiling, the same one `_PUBLIC_ALLOWLIST` carries and this list lacked (SEC-003).

        Twenty-seven entries today. Each one is a tenant-scoped write route any
        member may call, and the cheapest way past the sweep above has always been
        to add the twenty-eighth. A twenty-eighth is not automatically wrong — it
        should cost a conversation, and the issue is where the argument goes.
        """
        assert len(_TENANT_ALLOWLIST) <= 28, (
            f"_TENANT_ALLOWLIST has grown to {len(_TENANT_ALLOWLIST)} entries. Adding a route here lets "
            "every member of a tenant call it whatever their role; say why in the issue, not only in the dict."
        )


class TestAdminWriteGates:
    def test_no_admin_write_route_resolves_its_caller_through_bare_get_current_user(self):
        offenders = [
            op
            for op in _admin_write_operations()
            if _resolves_bare_user(op) and op.id not in _ADMIN_ALLOWLIST and not _excused_as_an_open_finding(op)
        ]
        assert not offenders, (
            "These routes write installation-wide configuration behind `get_current_user` alone, "
            "so any authenticated member of any tenant may call them. Gate them with "
            "`require_platform_admin`, or add them to _ADMIN_ALLOWLIST with a reason:\n  " + _format(offenders)
        )

    def test_every_allowlisted_admin_route_still_exists_and_is_still_ungated(self):
        by_id = {op.id: op for op in _admin_write_operations()}
        stale = []
        for route_id, reason in _ADMIN_ALLOWLIST.items():
            operation = by_id.get(route_id)
            if operation is None:
                stale.append(f"{route_id}: no such admin write route ({reason})")
            elif not _resolves_bare_user(operation):
                stale.append(f"{route_id}: now gated, drop the entry ({reason})")
        assert not stale, "Obsolete _ADMIN_ALLOWLIST entries:\n  " + "\n  ".join(stale)

    def test_every_reason_is_written_out(self):
        for route_id, reason in _ADMIN_ALLOWLIST.items():
            assert len(reason) >= 12, f"{route_id} carries no usable reason: {reason!r}"


def _stub_operation(path: str, *dependency_names: str | tuple, module: str = "app.api.v1.invented.router") -> Operation:
    """An Operation whose effective chain is exactly `dependency_names`.

    The probes below build a stub `route.dependant` rather than a handler
    signature, because the sweeps read the effective chain now. A probe built
    from a signature has `route=None`, `_authorisation_chain` returns `[]` for
    it, and every predicate under test answers the same way regardless of what
    it does — which is how the first version of this class came to leave the
    admin sweep provably unguarded (see the docstring below).
    """

    class _Call:
        def __init__(self, name: str) -> None:
            self.__qualname__ = name

    def _sub(spec: str | tuple):
        """A dependency node. A tuple is `(name, *children)` and nests one level deeper.

        Nesting is not decoration: `_authorisation_chain` descends transitively,
        and that descent is what this file credits with seeing router-level and
        parent-router gates. A probe that could only build FLAT chains left it
        uncontrolled — measured, replacing `walk(sub)` with `pass` left all 88
        tests green while the chain changed for 428 of 439 real routes.
        """
        if isinstance(spec, tuple):
            name, *children = spec
            return type("Sub", (), {"call": _Call(name), "dependencies": [_sub(c) for c in children]})()
        return type("Sub", (), {"call": _Call(spec), "dependencies": []})()

    subs = [_sub(spec) for spec in dependency_names]

    class _Route:
        dependant = type("D", (), {"dependencies": subs})()

    def _handler() -> None: ...

    _handler.__module__ = module
    return Operation("POST", path, _handler, _Route())


class TestTheGuardCanFail:
    """Falsification, in-process: an assertion nobody has seen fail proves nothing.

    **These probes were wrong for exactly one commit and the way they were wrong
    is the point of the class.** When the two sweeps moved from `inspect.signature`
    to the effective chain, these kept asserting the signature expressions — a
    different statement from the one the sweeps now make. Measured by mutation at
    the time: replacing the body of `_resolves_bare_user` with `return False`
    left **all 84 tests in this file green**. `_ADMIN_ALLOWLIST` is empty by
    design, so the admin sweep had no other control either, and a typo making it
    constant-`False` would have shipped in silence.

    Every probe below therefore drives the predicate the sweep drives, by name.
    """

    def test_a_bare_tenant_route_is_reported(self):
        operation = _stub_operation("/api/v1/t/{tenant_slug}/invented", "get_current_tenant")
        assert _resolves_bare_tenant_context(operation)
        assert operation.id not in _TENANT_ALLOWLIST

    def test_a_role_gated_tenant_route_is_not_reported(self):
        """The control: a predicate that reports everything is as useless as one that reports nothing."""
        operation = _stub_operation(
            "/api/v1/t/{tenant_slug}/invented",
            "get_current_tenant",
            "require_permission.<locals>._check",
        )
        assert not _resolves_bare_tenant_context(operation)

    def test_a_bare_admin_route_is_reported(self):
        operation = _stub_operation("/api/v1/admin/invented", "get_current_user")
        assert _resolves_bare_user(operation)
        assert operation.id not in _ADMIN_ALLOWLIST

    def test_a_platform_admin_route_is_not_reported(self):
        """The admin sweep's only control — `_ADMIN_ALLOWLIST` is empty, so nothing else drives it."""
        operation = _stub_operation("/api/v1/admin/invented", "get_current_user", "require_platform_admin")
        assert not _resolves_bare_user(operation)

    def test_an_unauthenticated_route_is_reported_by_the_third_question(self):
        operation = _stub_operation("/api/v1/invented", "get_fertilizer_service")
        assert not _resolves_authorisation(operation)

    def test_a_gate_nested_one_level_down_is_still_found(self):
        """The transitive descent, controlled.

        `get_active_tenant_context` already has this shape in production: it
        resolves `get_current_user` beneath itself rather than naming it at the
        route. A wrapper that pulled `get_current_tenant` one level down would
        make every route behind it invisible to the tenant sweep, silently, and
        nothing here noticed until this probe existed.
        """
        operation = _stub_operation(
            "/api/v1/t/{tenant_slug}/invented",
            ("get_some_wrapper", "get_current_tenant"),
        )

        # The nesting is pinned FIRST, because the helper that builds it is a
        # control too. Measured: a `_sub` that attached tuple children as
        # SIBLINGS instead of nesting them left all 91 tests green, and the two
        # probes here went inert without a word — they only asked whether a name
        # was in the chain, never at what depth. Combined with the `walk(sub)`
        # mutation this class exists to catch, 3 failures collapsed to 1, and
        # that one came from the real tree rather than from any probe.
        top_level = [dependency.call.__qualname__ for dependency in operation.route.dependant.dependencies]
        assert top_level == ["get_some_wrapper"], (
            f"the probe is not nested: {top_level}. _sub flattened the chain, so nothing below "
            "asserts anything about transitivity"
        )

        assert "get_current_tenant" in _authorisation_chain(operation)
        assert _resolves_bare_tenant_context(operation)

    def test_a_role_gate_nested_one_level_down_still_counts(self):
        """The other direction: nesting must not turn a gated route into an offender."""
        operation = _stub_operation(
            "/api/v1/t/{tenant_slug}/invented",
            "get_current_tenant",
            ("get_some_wrapper", "require_permission.<locals>._check"),
        )
        assert not _resolves_bare_tenant_context(operation)

    def test_the_three_predicates_disagree_on_the_same_operation(self):
        """They ask different questions, and a rewrite that collapsed them would show here.

        A tenant route behind bare `get_current_tenant`: reported by sweep 1,
        satisfied by sweep 3, untouched by sweep 2. If any two of these ever
        answer identically for every input, two of the three are redundant and one
        of them is not doing the job its name claims.
        """
        operation = _stub_operation("/api/v1/t/{tenant_slug}/invented", "get_current_tenant")
        assert _resolves_bare_tenant_context(operation)
        assert _resolves_authorisation(operation)
        assert not _resolves_bare_user(operation)


@pytest.mark.parametrize("route_id", sorted(_TENANT_ALLOWLIST) + sorted(_ADMIN_ALLOWLIST))
def test_no_route_is_allowlisted_twice(route_id: str):
    """Two entries for one route would let a stale reason outlive a live one."""
    assert not (route_id in _TENANT_ALLOWLIST and route_id in _ADMIN_ALLOWLIST)


#: The routes this change moved off bare `get_current_tenant`. Listed so the
#: behavioural test below has something concrete to drive, and so a later reader
#: can see what the triage decided rather than having to diff for it.
_GATED_HERE = [
    "diagnose.tenant_router.analyze",
    "ki_assistent.tenant_router.explain",
    "ki_assistent.tenant_router.refresh_tips",
    "ki_assistent.tenant_router.send_message",
    "plant_instances.diary_router.request_plant_diary_entry_analysis",
    "plant_instances.diary_router.cancel_plant_diary_entry_analysis",
    "planting_runs.tenant_router.request_run_diary_entry_analysis",
    "planting_runs.tenant_router.cancel_run_diary_entry_analysis",
    "tasks.tenant_router.start_task",
    "tasks.tenant_router.complete_task",
    "tasks.tenant_router.skip_task",
    "tasks.tenant_router.reopen_task",
    "watering_events.tenant_router.confirm_watering",
    "watering_events.tenant_router.quick_confirm_watering",
    "watering_logs.tenant_router.confirm_watering",
    "watering_logs.tenant_router.quick_confirm_watering",
]


def _viewer() -> TenantContext:
    return TenantContext(tenant_key="tenant-a", tenant_slug="mein-garten", user_key="user-a", role=TenantRole.VIEWER)


def _grower() -> TenantContext:
    return TenantContext(tenant_key="tenant-a", tenant_slug="mein-garten", user_key="user-a", role=TenantRole.GROWER)


class TestTheGatesActuallyRefuse:
    """Reading a dependency proves which one is attached; this proves what it does.

    The sweep above is an identity comparison: it cannot tell a working gate from
    a hollowed-out one, which is the failure class this repository keeps paying
    for (#706, #1397). Driving the resolved dependency with a viewer context is
    the shortest statement of the rule that goes red when the gate stops gating.
    """

    @pytest.mark.parametrize("route_id", _GATED_HERE)
    def test_a_viewer_is_refused(self, route_id: str):
        by_id = {op.id: op for op in _tenant_write_operations()}
        operation = by_id.get(route_id)
        assert operation is not None, f"{route_id} no longer exists; update _GATED_HERE"
        check = operation.dependencies["ctx"]
        with pytest.raises(ForbiddenError):
            check(_viewer())

    @pytest.mark.parametrize("route_id", _GATED_HERE)
    def test_a_grower_passes(self, route_id: str):
        """The control. A gate that refuses everyone passes every test above."""
        by_id = {op.id: op for op in _tenant_write_operations()}
        check = by_id[route_id].dependencies["ctx"]
        assert check(_grower()) is not None


class TestEveryWriteOperationResolvesSomeAuthorisation:
    """The third question (#1402): is ANYTHING gating this route?

    The two sweeps above ask whether a specific weak dependency is present. This
    one asks whether any authorisation is, which is the question that catches a
    route carrying none — the case that passed both of them silently, 24 times.
    """

    def test_no_write_operation_is_reachable_without_authorisation(self):
        offenders = [
            op
            for op in mounted_write_operations()
            if not _resolves_authorisation(op)
            and op.id not in _PUBLIC_ALLOWLIST
            and not _excused_as_an_open_finding(op)
        ]
        assert not offenders, (
            "These write operations resolve no authorisation dependency anywhere in their "
            "effective chain — not on the handler, not on their router, not on a parent "
            "router. Gate them, or add them to _PUBLIC_ALLOWLIST with a reason that "
            "survives the question 'why may an anonymous caller do this?':\n  " + _format(offenders)
        )

    def test_every_public_entry_still_exists_and_is_still_public(self):
        """Both halves of the obsolescence rule, and the second is the one that rots.

        An entry naming a route that was since gated would go on excusing a gate
        nobody needs excused, and the next reader takes it as a decision. The
        same rule `check_layer_imports` and `check_route_role_guards` follow.
        """
        by_id = {op.id: op for op in mounted_write_operations()}
        stale = []
        for route_id in _PUBLIC_ALLOWLIST:
            operation = by_id.get(route_id)
            if operation is None:
                stale.append(f"{route_id}: no longer mounted")
            elif _resolves_authorisation(operation):
                stale.append(f"{route_id}: now resolves authorisation — drop the entry")
        assert not stale, "Obsolete _PUBLIC_ALLOWLIST entries:\n  " + "\n  ".join(stale)

    def test_every_reason_is_written_out(self):
        for route_id, reason in _PUBLIC_ALLOWLIST.items():
            assert len(reason) >= 12, f"{route_id} carries no usable reason: {reason!r}"

    def test_the_allowlist_is_small(self):
        """A ceiling, because the cheapest way to make this test green is to grow the list.

        Twelve entries today, all of them pre-session endpoints, a published
        probe, or a route that authenticates from its own request body. A
        thirteenth is not automatically wrong, but it should cost a conversation.

        Grew by one in #1461: `oauth_callback` was exempt from every sweep as an
        entry in `_PERSISTING_READ_FINDINGS`, which is not an allowlist and skips
        more than this one does. Moving it here is a tightening, not a widening —
        the route is now measured by the obsolescence rule and the reason rule
        below, neither of which reached it before.
        """
        assert len(_PUBLIC_ALLOWLIST) <= 13, (
            f"_PUBLIC_ALLOWLIST has grown to {len(_PUBLIC_ALLOWLIST)} entries. "
            "Adding a route here makes it anonymously reachable; say why in the issue, not only in the dict."
        )


class TestTheThirdQuestionCanFail:
    """Falsifiability for the question above — a sweep that cannot report is not a gate.

    `TestTheGuardCanFail` does this for the first two questions. This one exists
    because the third question is the one that was missing, and a question added
    to close a hole is exactly the kind that gets added inert.
    """

    def test_a_router_level_gate_counts_as_authorisation(self):
        """The positive control, and it is not decoration.

        The fourteen routes #1402 gated were fixed at the ROUTER, not the handler.
        Read through `inspect.signature` they still name no auth parameter, so a
        per-handler implementation of this question would report them as open
        forever and the triage would never end.
        """
        by_id = {op.id: op for op in mounted_write_operations()}
        operation = by_id["calculations.router.calc_vpd"]
        assert operation.dependencies == {} or "ctx" not in operation.dependencies
        assert _resolves_authorisation(operation), (
            "calc_vpd is gated by APIRouter(dependencies=[Depends(get_current_user)]); "
            "if this fails, the question reads the handler signature and not the effective chain"
        )

    def test_an_ungated_operation_would_be_reported(self):
        """The negative control, built rather than found — the tree has none left."""

        class _NoDependencies:
            dependencies: list[Any] = []

        class _BareRoute:
            dependant = _NoDependencies()

        def _probe() -> None: ...

        _probe.__module__ = "app.api.v1.calculations.router"
        operation = Operation("POST", "/api/v1/calculations/probe", _probe, _BareRoute())
        assert not _resolves_authorisation(operation)
        assert operation.id not in _PUBLIC_ALLOWLIST

    def test_a_non_authorising_dependency_does_not_count(self):
        """A service dependency must not read as authorisation.

        The first version of this file matched substrings, and `"api_key"` matched
        the `APIKeyHeader` scheme object while `"mcp_"` matched
        `require_mcp_enabled`. Both authorise nobody. This probes the real
        classification rather than a hand-picked name.
        """

        def _service_dependency() -> None: ...

        _service_dependency.__qualname__ = "get_fertilizer_service"

        class _Sub:
            call = _service_dependency
            dependencies: list[Any] = []

        class _Route:
            dependant = type("D", (), {"dependencies": [_Sub()]})()

        def _probe() -> None: ...

        _probe.__module__ = "app.api.v1.calculations.router"
        operation = Operation("POST", "/x", _probe, _Route())
        assert _authorisation_chain(operation) == ["get_fertilizer_service"]
        assert not _resolves_authorisation(operation)


class TestTheClassificationItselfCannotDrift:
    """The vocabulary is an allowlist too, and allowlists rot (#1402).

    `_AUTHORISATION` decides what the three sweeps above believe a gate is. A new
    dependency named like one and classified as neither would be treated as
    infrastructure and silently stop counting — the same failure shape as a seed
    file outside a `check-jsonschema` hook or a write route outside a selector.
    """

    def test_every_auth_shaped_dependency_is_classified(self):
        seen: set[str] = set()
        for operation in mounted_write_operations():
            seen.update(_authorisation_chain(operation))

        unclassified = sorted(
            name
            for name in seen
            if any(shape in name.lower() for shape in _AUTH_SHAPED)
            and name not in _AUTHORISATION
            and name not in _NOT_AUTHORISATION
        )
        assert not unclassified, (
            "These dependencies are mounted on write routes and read like authorisation, but the "
            "sweeps classify them as neither. Add each to _AUTHORISATION if it refuses a caller, or "
            "to _NOT_AUTHORISATION with the reason it does not:\n  " + "\n  ".join(unclassified)
        )

    def test_the_two_sets_are_disjoint(self):
        overlap = _AUTHORISATION & frozenset(_NOT_AUTHORISATION)
        assert not overlap, f"classified as both: {sorted(overlap)}"

    def test_role_gates_are_a_subset_of_authorisation(self):
        assert _MORE_THAN_MEMBERSHIP <= _AUTHORISATION

    def test_every_non_authorisation_reason_is_written_out(self):
        for name, reason in _NOT_AUTHORISATION.items():
            assert len(reason) >= 12, f"{name} carries no usable reason: {reason!r}"

    def test_the_shape_filter_matches_every_name_that_was_classified(self):
        """The real invariant, and it is not a count.

        The guard above can only demand a decision on a name `_AUTH_SHAPED`
        matches. So the filter must match every name anyone has already decided
        about — otherwise a classified name falls out of the scan and the next
        one like it is never reported.

        A count cannot express that. The first version asserted a floor of 12
        matches; measured, `("user", "tenant", "auth")` matches 14 and passes it
        while `require_*`, `admin`, `permission`, `role`, `principal` and `key`
        drop out of the scan entirely — a later `require_new_gate` in neither set
        would then go unreported, which is precisely the vacuity this is for.
        Under the rule below that narrowing fails, because `require_platform_admin`
        is classified, live, and no longer matched.
        """
        seen: set[str] = set()
        for operation in mounted_write_operations():
            seen.update(_authorisation_chain(operation))

        classified_and_live = (set(_AUTHORISATION) | set(_NOT_AUTHORISATION)) & seen
        unmatched = sorted(
            name for name in classified_and_live if not any(shape in name.lower() for shape in _AUTH_SHAPED)
        )
        assert not unmatched, (
            "_AUTH_SHAPED no longer matches these names, although they are classified and mounted. "
            "The classification guard cannot see them, so a future sibling of theirs would go "
            "unreported:\n  " + "\n  ".join(unmatched)
        )

    def test_no_shape_is_an_exact_dependency_name(self):
        """A shape must be a SUBSTRING, not a name written out in full.

        The cheapest way to make the coverage rule above green for an awkward
        future name is to paste that name into `_AUTH_SHAPED` — `"httpbearer"`
        would have worked here instead of `"bearer"`. That passes the ceiling
        (one more match) and leaves `test_every_auth_shaped_dependency_is_classified`
        exactly as vacuous as before, because the filter then only enumerates
        names somebody has already classified and can never surface a new one.

        Not asserting that every shape is load-bearing, and that omission is
        deliberate: measured, `principal`, `permission` and `role` are each
        covered today by another substring (`mcp`, `require_`), so a
        load-bearing rule would demand their deletion. They are there for the
        names that do not exist yet — a `get_principal` without the `mcp` prefix,
        a `check_permission_scope` without `require_` — which is the whole point
        of a shape filter. Cheap insurance is not drift.
        """
        lowered = {name.lower() for name in set(_AUTHORISATION) | set(_NOT_AUTHORISATION)}
        exact = sorted(shape for shape in _AUTH_SHAPED if shape.lower() in lowered)
        assert not exact, (
            "These _AUTH_SHAPED entries are whole dependency names rather than shapes, so the "
            "classification guard can only ever rediscover what is already classified:\n  " + "\n  ".join(exact)
        )

    def test_the_shape_filter_does_not_match_everything(self):
        """Too wide is also a failure: it would demand a decision on every service in the tree."""
        seen: set[str] = set()
        for operation in mounted_write_operations():
            seen.update(_authorisation_chain(operation))

        matched = {name for name in seen if any(shape in name.lower() for shape in _AUTH_SHAPED)}
        assert len(matched) < len(seen) // 2, (
            f"_AUTH_SHAPED matches {len(matched)} of {len(seen)} dependency names. At that width the "
            "guard stops distinguishing authorisation from infrastructure."
        )

    def test_every_non_authorisation_entry_is_still_mounted(self):
        """The obsolescence rule, applied to the vocabulary as well as the routes.

        This file's central argument is that an allowlist without one rots.
        `_NOT_AUTHORISATION` is an allowlist — it says "this name looks like a
        gate and is not" — and until this test it had no such rule.

        **Exact, not a floor.** The first version allowed half the set to be dead,
        on the grounds that an entry might be classified against a read-only
        route. Measured: all 18 entries appear on mounted write routes, so that
        exception carried nothing — while the floor let a name existing nowhere in
        the app sit here indefinitely, verified by adding one and watching all 88
        tests stay green. If a future entry really is read-route-only it needs its
        own exemption with a reason, not a gap wide enough for ten.
        """
        seen: set[str] = set()
        for operation in mounted_write_operations():
            seen.update(_authorisation_chain(operation))

        stale = sorted(name for name in _NOT_AUTHORISATION if name not in seen)
        assert not stale, (
            "These _NOT_AUTHORISATION names appear on no mounted write route. Either the dependency "
            "is gone and the entry should go with it, or it moved to a read route and needs a reason "
            "saying so:\n  " + "\n  ".join(stale)
        )


class TestInstallationWideMasterDataIsPlatformAdminOnly:
    """The fourth question (#1402 group B): who may change a row everyone shares?"""

    def test_every_write_resolves_platform_admin(self):
        offenders = [
            op
            for op in _installation_wide_write_operations()
            if not (set(_authorisation_chain(op)) & _PLATFORM_ADMIN_GATES) and not _excused_as_an_open_finding(op)
        ]
        assert not offenders, (
            "These routes write INSTALLATION-WIDE master data behind authentication alone, so any "
            "member of any tenant may change them for everyone. Gate them on "
            "`require_platform_admin` like their `companion_planting` siblings:\n  " + _format(offenders)
        )

    def test_the_reads_are_not_gated(self):
        """The control, and it is the #706 direction.

        These catalogues must stay readable by every member — a rotation rule
        nobody can read is as broken as one anybody can edit. A gate applied to the
        whole ROUTER instead of to its writes would satisfy the test above and
        break the product, which is exactly how an over-rejecting guard ships
        looking correct.
        """
        gated_reads: list[str] = []

        def walk(router: Any, prefix: str = "") -> None:
            for route in getattr(router, "routes", []):
                included = getattr(route, "original_router", None)
                if included is not None:
                    context = getattr(route, "include_context", None)
                    walk(included, prefix + (getattr(context, "prefix", "") or ""))
                    continue
                endpoint = getattr(route, "endpoint", None)
                if endpoint is None or "GET" not in (getattr(route, "methods", ()) or ()):
                    continue
                module = endpoint.__module__.removeprefix("app.api.v1.").split(".")[0]
                if module not in _INSTALLATION_WIDE_MODULES:
                    continue
                probe = Operation("GET", prefix + (getattr(route, "path", "") or ""), endpoint, route)
                if set(_authorisation_chain(probe)) & _PLATFORM_ADMIN_GATES:
                    gated_reads.append(probe.path)

        walk(api_router)

        assert not gated_reads, (
            "These reads now require platform admin. The rows are shared catalogue data every "
            "member consults:\n  " + "\n  ".join(sorted(gated_reads))
        )

    def test_the_module_set_still_matches_the_tree(self):
        """Obsolescence, both directions — an entry naming a module that is gone, and
        a module in the set that no longer writes anything."""
        stale = []
        by_module = {_module_of(op) for op in mounted_write_operations()}
        for module in _INSTALLATION_WIDE_MODULES:
            if module not in by_module:
                stale.append(f"{module}: mounts no write operation any more")
        assert not stale, "Obsolete _INSTALLATION_WIDE_MODULES entries:\n  " + "\n  ".join(stale)

    def test_every_reason_is_written_out(self):
        for module, reason in _INSTALLATION_WIDE_MODULES.items():
            assert len(reason) >= 12, f"{module} carries no usable reason: {reason!r}"

    def test_no_module_quietly_loses_its_write_operations(self):
        """A per-module ratchet, because one number over the whole set cannot fire.

        This assertion used to read ``>= 15`` against an actual 21. Deleting
        ``"profiles"`` from :data:`_INSTALLATION_WIDE_MODULES` along with its five
        ``require_platform_admin`` dependencies left 16 — above the floor — so every
        test in this class stayed green while five installation-wide writes became
        member-writable again. A threshold with six routes of slack is the NFR-018 §1
        shape: it fires only for a mistake nobody makes.

        The floor is per module and a **minimum**, not an equality: adding a route to
        a gated module is normal and is already checked for its gate by
        :meth:`test_every_installation_wide_write_is_platform_admin_gated`. Removing
        one is the direction that needs a witness. Lowering a number here is a
        deliberate act with a diff line to explain.
        """
        expected = {
            "phase_sequences": 11,
            "ipm": 9,
            "profiles": 5,
            "enrichment": 4,
            "growth_phases": 3,
            "location_types": 3,
            "activities": 3,
            "lifecycle_configs": 2,
            "crop_rotation": 1,
        }
        assert set(expected) == set(_INSTALLATION_WIDE_MODULES), (
            "the floor map and the module set disagree; a module was added or removed in one of the two places only"
        )

        actual: dict[str, int] = {}
        for operation in _installation_wide_write_operations():
            actual[_module_of(operation)] = actual.get(_module_of(operation), 0) + 1

        shrunk = [
            f"{module}: {actual.get(module, 0)} write operations, expected at least {floor}"
            for module, floor in expected.items()
            if actual.get(module, 0) < floor
        ]
        assert not shrunk, "installation-wide write operations disappeared from the gated set:\n  " + "\n  ".join(
            shrunk
        )

    def test_every_global_write_module_is_classified(self):
        """Every module writing on the global router is on one side or the other — #1501.

        The rule that would have found `phase_sequences` and `ipm` before a security
        issue did. `_INSTALLATION_WIDE_MODULES` was an opt-in list and could only
        ever check the modules somebody had already thought of; this checks the
        modules that EXIST.
        """
        classified = set(_INSTALLATION_WIDE_MODULES) | set(_NOT_INSTALLATION_WIDE)
        modules = {_module_of(op) for op in _global_write_operations()}
        unclassified = sorted(modules - classified)
        assert not unclassified, (
            "These modules mount write routes on the GLOBAL router and are classified nowhere. "
            "Decide whether each writes installation-wide master data — a row every tenant "
            "shares, which needs `require_platform_admin` — and add it to "
            "_INSTALLATION_WIDE_MODULES, or record in _NOT_INSTALLATION_WIDE what it writes "
            "instead and which gate answers for it:\n  " + "\n  ".join(unclassified)
        )

    def test_no_module_is_classified_on_both_sides(self):
        both = sorted(set(_INSTALLATION_WIDE_MODULES) & set(_NOT_INSTALLATION_WIDE))
        assert not both, f"classified as both installation-wide and not: {both}"

    def test_every_not_installation_wide_entry_still_names_a_global_writer(self):
        """Obsolescence, the direction the entry itself cannot notice.

        An exemption for a module that no longer writes globally is an exemption
        nobody re-reads, and the next module to take that name inherits it.
        """
        modules = {_module_of(op) for op in _global_write_operations()}
        stale = sorted(set(_NOT_INSTALLATION_WIDE) - modules)
        assert not stale, (
            "These _NOT_INSTALLATION_WIDE entries name a module that mounts no global "
            "write any more — drop them:\n  " + "\n  ".join(stale)
        )

    def test_every_not_installation_wide_reason_is_written_out(self):
        for module, reason in _NOT_INSTALLATION_WIDE.items():
            assert len(reason) >= 12, f"{module} carries no usable reason: {reason!r}"

    def test_the_global_selector_is_populated(self):
        """Either selector matching nothing would make the two rules above vacuous."""
        assert len(_global_write_operations()) > 100
        assert len({_module_of(op) for op in _global_write_operations()}) > 20


# ── #1443: the read half of the write surface ──────────────────────────────────

#: A synthetic app tree for the detector's own controls. It is written to disk and
#: parsed by a FRESH `CallGraph`, not by the cached one over the real app: a probe
#: that can only be built out of the thing it is probing proves nothing about it.
#:
#: The shape is the shape the real tree has — handler → injected service →
#: repository → collection primitive — because a probe that skips the middle would
#: pass while the resolution this file credits with seeing through services was
#: broken.
_SYNTHETIC_TREE = {
    "__init__.py": "",
    "data_access/__init__.py": "",
    "data_access/invented_repository.py": '''
class InventedRepository:
    """A repository of the shape the real ones have."""

    def __init__(self, db) -> None:
        self._db = db

    @property
    def collection(self):
        return self._db.collection("invented")

    def get_by_key(self, key: str):
        return self.collection.get(key)

    def create(self, document: dict) -> dict:
        return self.collection.insert(document)
''',
    "domain/__init__.py": "",
    "domain/invented_service.py": """
from app.data_access.invented_repository import InventedRepository


class InventedService:
    def __init__(self, repo: InventedRepository) -> None:
        self._repo = repo

    def read_only(self, key: str):
        return self._repo.get_by_key(key)

    def touch(self, key: str):
        return self._repo.create({"key": key})
""",
    "api/__init__.py": "",
    "api/invented_router.py": '''
from app.domain.invented_service import InventedService


def get_invented(key: str, service: InventedService):
    """A GET that persists. No method name says so."""
    return service.touch(key)


def read_invented(key: str, service: InventedService):
    """A GET that does not persist. The control."""
    return service.read_only(key)
''',
    # ── SEC-002: a second write behind the same exemption ──────────────────
    "data_access/audit_repository.py": '''
class AuditRepository:
    """A SECOND repository, so its write is a DIFFERENT sink string."""

    def __init__(self, db) -> None:
        self._db = db

    @property
    def collection(self):
        return self._db.collection("audit")

    def create(self, document: dict) -> dict:
        return self.collection.insert(document)
''',
    "domain/guarded_service.py": '''
from app.data_access.audit_repository import AuditRepository
from app.data_access.invented_repository import InventedRepository


class GuardedService:
    def __init__(self, repo: InventedRepository, audit: AuditRepository) -> None:
        self._repo = repo
        self._audit = audit

    def maybe_touch(self, key: str, *, may_create: bool):
        """The `get_or_create_profile` shape: writes only when the flag allows it."""
        if not may_create:
            return self._repo.get_by_key(key)
        return self._repo.create({"key": key})

    def record(self, key: str):
        return self._audit.create({"key": key})
''',
    "api/guarded_router.py": '''
from app.domain.guarded_service import GuardedService


def guarded_get(key: str, service: GuardedService):
    """A GET whose only write is forbidden by an argument. The exemption shape."""
    return service.maybe_touch(key, may_create=False)


def guarded_get_and_audit(key: str, service: GuardedService):
    """The same exemption, plus a write the witness does not name.

    The guarded call comes FIRST on purpose: a shortest-path search therefore
    reports the same sink as `guarded_get`, and the second write is invisible to
    anyone reading the path.
    """
    result = service.maybe_touch(key, may_create=False)
    service.record(key)
    return result
''',
    # ── SEC-004: the query lives at module level, the body only names it ────
    "data_access/timeseries_repository.py": '''
_SQL = """
INSERT INTO readings (value) VALUES (%(value)s)
"""


class TimeseriesRepository:
    """The shape `data_access/timescale/observation_repository.py` has."""

    def __init__(self, pool) -> None:
        self._pool = pool

    def insert(self, value: float) -> None:
        with self._pool.connection() as conn:
            conn.execute(_SQL, {"value": value})
''',
    "api/timeseries_router.py": '''
from app.data_access.timeseries_repository import TimeseriesRepository


def record_reading(value: float, repo: TimeseriesRepository):
    """A handler whose only write is a module-level SQL constant."""
    repo.insert(value)
''',
    # ── SEC-005: BackgroundTasks runs in THIS process, on this request ──────
    "api/background_router.py": '''
from app.domain.invented_service import InventedService


def _persist(service: InventedService, key: str):
    service.touch(key)


def enqueue_get(key: str, background_tasks, service: InventedService):
    """A GET that hands the write to `BackgroundTasks`. Same process, same request."""
    background_tasks.add_task(_persist, service, key)
''',
}


def _write_synthetic_tree(root):
    for relative, source in _SYNTHETIC_TREE.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return root


def _synthetic_graph(root):
    from tests.unit.api._write_call_graph import CallGraph

    graph = CallGraph()
    graph.parse_tree(root)
    graph.link()
    return graph


class TestTheDetectorCanFail:
    """The detector is a guard over a guard, and those certify themselves (#1443 risk 1).

    `TestTheGuardCanFail` does this for the dependency sweeps. This class does it
    for the question those sweeps now depend on — *is this a write route at all* —
    against a handler built for the purpose, so the control cannot be satisfied by
    the real tree happening to contain something.
    """

    def test_a_writing_get_is_found_although_nothing_lists_it(self, tmp_path):
        """The proof that the detector measures something.

        Run against the sweep as it stood before #1443 this handler is invisible:
        it is mounted on a `GET`, `WRITE_METHODS` does not contain `GET`, and no
        list names it. That is the whole defect, reproduced in eleven lines.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))
        handler = graph.by_id["app.api.invented_router::get_invented"]

        path = graph.write_path(handler)

        assert path is not None, "the detector did not find a GET that calls a repository create()"
        assert path[0] == "app.api.invented_router::get_invented"
        assert "app.domain.invented_service::InventedService.touch" in path, (
            f"the chain skipped the service layer: {path}"
        )
        assert "app.data_access.invented_repository::InventedRepository.create" in path
        assert path[-1].startswith(
            "self.collection.insert() in app.data_access.invented_repository::InventedRepository.create"
        )

    def test_a_reading_get_is_not_found(self, tmp_path):
        """The control. A detector that reports everything is as useless as one that reports nothing.

        `read_invented` differs from `get_invented` in one call — `get_by_key`
        instead of `create` — and reaches the same repository, the same
        `self.collection`, through the same service.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))

        assert graph.write_path(graph.by_id["app.api.invented_router::read_invented"]) is None

    def test_a_detector_with_no_sinks_finds_nothing(self, tmp_path, monkeypatch):
        """The mutation, and it is the load-bearing one.

        Empty the sink vocabulary — the collection mutators and the query-write
        shape — and rebuild. Everything else stays: the same tree, the same type
        resolution, the same reachability. If the handler is still reported, the
        report is not coming from the writes, and the whole detector is a
        `return True` with a docstring.
        """
        from tests.unit.api import _write_call_graph as detector

        root = _write_synthetic_tree(tmp_path)
        assert _synthetic_graph(root).write_path(
            _synthetic_graph(root).by_id["app.api.invented_router::get_invented"]
        ), "the pre-condition failed: the unmutated detector must find the probe"

        monkeypatch.setattr(detector, "_COLLECTION_MUTATORS", frozenset())
        monkeypatch.setattr(detector, "_QUERY_WRITE", re.compile(r"(?!x)x"))

        mutated = _synthetic_graph(root)

        assert not [fn for fn in mutated.functions if fn.direct_write], "the mutation did not empty the sinks"
        assert mutated.write_path(mutated.by_id["app.api.invented_router::get_invented"]) is None

    def test_a_second_write_in_a_guarded_handler_is_not_hidden_by_the_witness(self, tmp_path):
        """SEC-002, as a probe rather than as an argument.

        `guarded_get` and `guarded_get_and_audit` are the same exemption shape —
        `maybe_touch(..., may_create=False)`, the witness
        `_GUARDED_PERSISTING_READS` records — and the second one reaches an audit
        write besides. Under the old `(callee, keyword)` entry both routes were
        excused identically, and the audit write left the sweep with the route.

        The first two assertions are the precondition, not decoration: they pin that
        a shortest-path search reports the SAME sink for both handlers, which is why
        comparing paths could never have caught this and comparing sink sets can.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))
        guarded = graph.by_id["app.api.guarded_router::guarded_get"]
        both = graph.by_id["app.api.guarded_router::guarded_get_and_audit"]

        assert graph.write_path(guarded)[-1] == graph.write_path(both)[-1], (
            "the probe does not reproduce the hiding: the two handlers already differ on the nearest sink"
        )

        guarded_sinks = graph.write_sinks(guarded)
        assert len(guarded_sinks) == 1, f"the guarded probe reaches more than the one write: {guarded_sinks}"
        assert guarded_sinks == {
            "self.collection.insert() in app.data_access.invented_repository::InventedRepository.create"
        }

        assert graph.write_sinks(both) == guarded_sinks | {
            "self.collection.insert() in app.data_access.audit_repository::AuditRepository.create"
        }

    def test_a_module_level_query_constant_is_a_sink(self, tmp_path):
        """SEC-004: the whole TimescaleDB write surface was invisible.

        `data_access/timescale/observation_repository.py` binds its
        `INSERT INTO sensor_readings` to `_INSERT_SQL` at module level and
        `insert()` only references the name. The scan looked for literals inside
        function bodies, found none, and reported the repository clean — while the
        detector's own docstring listed `INSERT INTO` as a sink.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))

        writer = graph.by_id["app.data_access.timeseries_repository::TimeseriesRepository.insert"]
        assert writer.direct_write is not None, "a module-level INSERT constant is not a sink"
        assert writer.direct_write.startswith("module-level query write _SQL")

        path = graph.write_path(graph.by_id["app.api.timeseries_router::record_reading"])
        assert path is not None, "the handler that reaches it is still reported clean"
        assert path[-1] == writer.write_site

    def test_a_module_level_constant_that_is_not_a_write_is_not_a_sink(self, tmp_path):
        """The control: `_QUERY_RAW_SQL` next to `_INSERT_SQL` must not report.

        A rule that made every module-level string a sink would turn the whole tree
        into writers and pass the test above identically.
        """
        root = _write_synthetic_tree(tmp_path)
        (root / "data_access" / "reading_repository.py").write_text(
            '_SELECT_SQL = "SELECT value FROM readings WHERE key = %(key)s"\n'
            "\n"
            "\n"
            "class ReadingRepository:\n"
            "    def __init__(self, pool) -> None:\n"
            "        self._pool = pool\n"
            "\n"
            "    def read(self, key: str):\n"
            "        with self._pool.connection() as conn:\n"
            '            return conn.execute(_SELECT_SQL, {"key": key})\n',
            encoding="utf-8",
        )
        graph = _synthetic_graph(root)

        assert graph.by_id["app.data_access.reading_repository::ReadingRepository.read"].direct_write is None

    def test_the_module_level_rule_is_what_finds_it(self, tmp_path):
        """The mutation for SEC-004, and it isolates the new rule from the old one.

        `test_a_detector_with_no_sinks_finds_nothing` empties the whole sink
        vocabulary, so it would go red for either rule. This one leaves the
        collection mutators and the regex alone and disables only the module-level
        binding; if the probe is still found, something else is finding it.
        """
        from tests.unit.api import _write_call_graph as detector

        root = _write_synthetic_tree(tmp_path)
        monkey = detector._is_query_write
        try:
            detector._is_query_write = lambda value: False
            mutated = _synthetic_graph(root)
        finally:
            detector._is_query_write = monkey

        assert mutated.by_id["app.data_access.timeseries_repository::TimeseriesRepository.insert"].direct_write is None
        assert mutated.write_path(mutated.by_id["app.api.timeseries_router::record_reading"]) is None

    def test_a_background_task_is_on_the_request_path(self, tmp_path):
        """SEC-005: the Celery argument does not carry for `BackgroundTasks`.

        `some_task.delay(...)` hands the work to another process and this detector
        says so and skips it. `background_tasks.add_task(fn, ...)` does not: Starlette
        runs `fn` in this process, under this request, after the response body is
        sent — `auth/router.py:197` is the live instance. The call itself resolves to
        a library method with no body in this tree, so without an edge to the first
        positional argument the write it schedules is reported nowhere.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))

        path = graph.write_path(graph.by_id["app.api.background_router::enqueue_get"])

        assert path is not None, "a handler whose write is scheduled through add_task is reported clean"
        assert "app.api.background_router::_persist" in path, f"the edge skipped the scheduled callable: {path}"
        assert path[-1].startswith(
            "self.collection.insert() in app.data_access.invented_repository::InventedRepository.create"
        )

    def test_without_the_add_task_edge_the_background_write_disappears(self, tmp_path, monkeypatch):
        """The mutation for SEC-005. Empty the set, and the probe goes back to clean."""
        from tests.unit.api import _write_call_graph as detector

        root = _write_synthetic_tree(tmp_path)
        monkeypatch.setattr(detector, "_CALLABLE_ARGUMENT_SINKS", frozenset())
        mutated = _synthetic_graph(root)

        assert mutated.write_path(mutated.by_id["app.api.background_router::enqueue_get"]) is None

    # ── #1443 follow-up: the identity an exemption pins must not move on its own ──

    @staticmethod
    def _shift_the_sink_down(root):
        """Insert a comment and three blank lines ABOVE the sink, changing nothing else.

        This is #1436 in miniature: that merge added lines to
        ``base_repository.py`` above `create_edge`, and every witness in
        `_GUARDED_PERSISTING_READS` went red although no write moved, changed or
        appeared.
        """
        target = root / "data_access" / "invented_repository.py"
        source = target.read_text(encoding="utf-8")
        marker = "    def create(self, document: dict) -> dict:"
        assert marker in source, "the probe no longer contains the sink it claims to shift"
        target.write_text(
            source.replace(marker, "    # a comment nobody asked about the write below\n\n\n\n" + marker),
            encoding="utf-8",
        )
        return root

    def test_a_sink_identity_survives_lines_inserted_above_it(self, tmp_path):
        """The reason the line number left the identity (#1443 follow-up).

        Build the probe, read the sinks, push the write four lines down without
        touching it, parse again from scratch. The identity set must be the SAME
        set — that is what makes an exemption that pins it go red on a real change
        and only on a real change.
        """
        root = _write_synthetic_tree(tmp_path)
        before = _synthetic_graph(root)
        handler = "app.api.invented_router::get_invented"
        sinks_before = before.write_sinks(before.by_id[handler])
        writer_before = before.by_id["app.data_access.invented_repository::InventedRepository.create"]

        after = _synthetic_graph(self._shift_the_sink_down(root))
        writer_after = after.by_id["app.data_access.invented_repository::InventedRepository.create"]

        assert writer_after.direct_write_lineno != writer_before.direct_write_lineno, (
            "the probe is vacuous: the edit did not move the write, so identical sinks prove nothing "
            f"(line {writer_before.direct_write_lineno} both times)"
        )
        assert sinks_before, "the precondition failed: the unedited probe reaches no sink at all"
        assert after.write_sinks(after.by_id[handler]) == sinks_before, (
            "the sink identity moved when a comment was inserted above it:\n"
            f"  before: {sorted(sinks_before)}\n"
            f"  after:  {sorted(after.write_sinks(after.by_id[handler]))}"
        )
        assert {fn.direct_write for fn in after.functions if fn.direct_write} == {
            fn.direct_write for fn in before.functions if fn.direct_write
        }

    def test_an_identity_carrying_the_line_number_would_not_have_survived_it(self, tmp_path):
        """The mutation for the test above, and it is the whole defect.

        Rebuild the OLD identity — the one that carried `module:lineno` — out of the
        two fields the detector now keeps apart, and run the same edit past it. If
        this set also came out identical, the test above would be green for a
        format that never had the problem, and the change would be decoration.
        """
        root = _write_synthetic_tree(tmp_path)

        def with_the_line_number(graph):
            return {
                f"{fn.direct_write} at {fn.module}:{fn.direct_write_lineno}"
                for fn in graph.functions
                if fn.direct_write
            }

        before = with_the_line_number(_synthetic_graph(root))
        after = with_the_line_number(_synthetic_graph(self._shift_the_sink_down(root)))

        assert before != after, (
            "the mutation did not bite: an identity containing the line number survived an edit above "
            "the sink, so the test above proves nothing about the identity having lost it"
        )

    def test_the_human_path_still_says_which_line(self, tmp_path):
        """Dropping the line from the IDENTITY must not drop it from the report.

        #1443 exists because a finding nobody can trace is a finding nobody can
        triage. The line moved to `write_site`, which is what `write_path` emits;
        it must still be there, and it must still be right.
        """
        graph = _synthetic_graph(_write_synthetic_tree(tmp_path))
        writer = graph.by_id["app.data_access.invented_repository::InventedRepository.create"]

        path = graph.write_path(graph.by_id["app.api.invented_router::get_invented"])

        assert path[-1] == f"{writer.direct_write}   [line {writer.direct_write_lineno}]"
        assert path[-1] not in graph.write_sinks(graph.by_id["app.api.invented_router::get_invented"]), (
            "the human form leaked into the identity set; a pin could latch onto the line number again"
        )

    def test_the_real_tree_is_the_imported_one(self):
        """The editable-install trap: parsing one checkout while the app walk mounts another.

        A worktree without its own virtualenv resolves `app` through an editable
        install pointing at the primary checkout. Deriving the source root from
        this file's location would then measure a different tree from the one the
        route walk enumerates, and the two would disagree without saying so.
        """
        import app
        from tests.unit.api._write_call_graph import APP_ROOT

        assert pathlib.Path(app.__file__).resolve().parent == APP_ROOT
        assert call_graph().modules_parsed > 500


class TestPersistingReadsAreSweptLikeWrites:
    """The acceptance condition of #1443: a writing GET is gated like a POST.

    Not "is reported". The three questions above — bare tenant context, bare user,
    no authorisation at all — are what a `POST` has to answer, and a read that
    persists now answers them too, without appearing in any list first.
    """

    def test_the_sweep_admits_exactly_the_reads_the_detector_reports(self):
        """The change itself, asserted as an equality rather than as a presence.

        A presence check (`some read is in the sweep`) goes vacuous the day the
        last finding is repaired. An equality stays meaningful at zero: it says the
        sweep's read half *is* the detector's answer, minus the guarded three, for
        any number of them.
        """
        admitted = {op.id for op in mounted_write_operations() if op.method in READ_METHODS}

        detected = set()
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS and persists(endpoint):
                detected.add(_operation_id(endpoint))

        assert admitted == detected - set(_GUARDED_PERSISTING_READS), (
            "the sweep's read half and the detector disagree:\n"
            f"  in the sweep, not detected: {sorted(admitted - detected)}\n"
            f"  detected, not in the sweep: {sorted(detected - set(_GUARDED_PERSISTING_READS) - admitted)}"
        )

    def test_the_detector_agrees_with_the_method_convention_where_it_applies(self):
        """A floor on the other direction, and it is the control for the whole detector.

        If the detector reported reads but could not see the writes everybody
        already agrees are writes, its resolution would be broken in a way no
        assertion above would catch — `mounted_write_operations` would still be
        full, of `POST`s. Measured at this head: 400 of 440 method-writes are also
        detected as persisting — 396 before the #1443 review closed the module-level
        query blind spot (SEC-004) and followed `BackgroundTasks.add_task` (SEC-005).
        The rest are computations, validations and routes whose write is a Celery
        task, which the detector states it cannot see.
        """
        method_writes = [op for op in mounted_write_operations() if op.method in WRITE_METHODS]
        agreeing = [op for op in method_writes if persists(op.route.endpoint)]

        assert len(agreeing) > len(method_writes) * 0.8, (
            f"the detector only recognises {len(agreeing)} of {len(method_writes)} routes that carry a "
            "write method. Its receiver-type resolution has regressed, and the read half is reporting "
            "from a call graph that no longer reaches the repositories."
        )

    def test_every_finding_is_still_a_persisting_read(self):
        """Obsolescence, the direction that rots: a repaired route keeps its excuse.

        The entry stops being true the moment the handler stops writing, and an
        entry that outlives its finding is exactly the artefact #1441 spent a slice
        removing.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        stale = []
        for route_id, reason in _PERSISTING_READ_FINDINGS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                stale.append(f"{route_id}: no such read route any more ({reason})")
            elif not persists(endpoint):
                stale.append(f"{route_id}: no longer persists — delete the entry ({reason})")
        assert not stale, (
            "Obsolete _PERSISTING_READ_FINDINGS entries. These are open findings, not approvals; a "
            "repaired one must be removed, not kept:\n  " + "\n  ".join(stale)
        )

    def test_the_finding_list_only_shrinks(self):
        """A ratchet on the IDS, because a ratchet on the count admits an exchange.

        This assertion used to read `len(...) <= 10`. SEC-001 of the #1443 review
        showed it green for the move it exists to refuse: repair one route, delete
        its entry, add the next unlisted writing `GET` — ten again, a new open
        defect quietly excused, nothing red. Comparing against the measured set
        instead makes the direction explicit: a subset is fine, a new member is not.
        """
        added = sorted(set(_PERSISTING_READ_FINDINGS) - _MEASURED_2026_09_16)
        assert not added, (
            "These reads were added to _PERSISTING_READ_FINDINGS after the 2026-09-16 measurement:\n  "
            + "\n  ".join(added)
            + "\nThe list may shrink as routes are repaired; it may not gain a member. A NEW writing "
            "GET has to be gated or argued in an issue, not listed here."
        )

    def test_the_finding_list_is_empty(self):
        """The acceptance condition of #1461, asserted rather than described.

        `test_the_finding_list_only_shrinks` is a ratchet against the 2026-09-16
        ids and would stay green if one of the eight repaired routes were listed
        again — it may shrink, and re-adding a measured id is a shrink from the
        original ten. This says the stronger thing the group closed on: **none of
        them is open**. Two of the ten are decisions now
        (:data:`_INTENTIONAL_PERSISTING_READS`) and eight write nothing.

        A route that starts persisting again is caught by
        `test_the_sweep_admits_exactly_the_reads_the_detector_reports` and the
        three gate sweeps regardless; what this refuses is the quiet path back —
        re-listing it here as an open finding, where every sweep skips it.
        """
        assert _PERSISTING_READ_FINDINGS == {}, (
            "A read that persists is recorded as an open finding again:\n  "
            + "\n  ".join(sorted(_PERSISTING_READ_FINDINGS))
            + "\nAll ten of the 2026-09-16 measurements were answered in #1461/#1460 — eight repaired, "
            "two recorded as decisions with their sinks. Repair it, argue it in the issue and record "
            "it as intentional, or say in the diff why the sweeps must skip it again."
        )

    def test_the_measured_set_is_the_measurement(self):
        """The frozen set is an artefact too, and widening it is the next cheapest way out.

        Ten is what the detector reported on 2026-09-16 against `eb43c76c3`. This
        does not stop anyone editing the frozenset — nothing can — but it costs a
        second deliberate line in the same diff, which is the difference between a
        decision and a slip.
        """
        assert len(_MEASURED_2026_09_16) == 10, (
            f"_MEASURED_2026_09_16 holds {len(_MEASURED_2026_09_16)} ids; the 2026-09-16 run reported ten."
        )

    def test_every_finding_reason_is_written_out(self):
        for route_id, reason in _PERSISTING_READ_FINDINGS.items():
            assert len(reason) >= 12, f"{route_id} carries no usable reason: {reason!r}"

    def test_a_finding_is_not_also_an_exemption(self):
        overlap = set(_PERSISTING_READ_FINDINGS) & set(_GUARDED_PERSISTING_READS)
        assert not overlap, f"recorded both as an open finding and as guarded: {sorted(overlap)}"

    def test_every_guarded_read_really_passes_its_guard(self):
        """The witness, read back out of the source (#1443, and the lesson of #1441).

        Each entry claims a read reaches a persisting helper only with the write
        forbidden by an argument. This finds every reachable call to that helper
        and fails unless all of them pass the keyword as a literal `False`. Flip
        one, drop it, rename the parameter — the exemption dies and the route goes
        back into the sweep.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        problems = []
        for route_id, (callee, keyword, _sink) in _GUARDED_PERSISTING_READS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                problems.append(f"{route_id}: no such read route any more")
                continue
            if not persists(endpoint):
                problems.append(f"{route_id}: no longer reaches a write at all — drop the entry")
                continue
            passed = reachable_keyword_arguments(endpoint, callee, keyword)
            if not passed:
                problems.append(f"{route_id}: no reachable call to {callee}() — the witness names nothing")
                continue
            for site, value in passed:
                if value is not False:
                    problems.append(f"{route_id}: {site} calls {callee}({keyword}={value!r}), not False")
        assert not problems, (
            "These reads are excused because an argument forbids the write, and the source no longer "
            "agrees:\n  " + "\n  ".join(problems)
        )

    def test_a_guarded_read_would_be_reported_without_its_guard(self):
        """The exemptions are not decoration: each one really is a detector hit.

        An entry naming a route the detector never reported would sit here forever
        suppressing nothing, and would be indistinguishable from one that
        suppresses a real finding.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        for route_id in _GUARDED_PERSISTING_READS:
            endpoint = by_id.get(route_id)
            assert endpoint is not None, f"{route_id} is no longer a mounted read route"
            assert write_path_of(endpoint) is not None, (
                f"{route_id} is excused from a report the detector does not make. Drop the entry."
            )

    def test_the_witness_is_the_only_write_each_guarded_read_reaches(self):
        """SEC-002: the writes the entry excuses are the writes the route reaches.

        `test_every_guarded_read_really_passes_its_guard` proves the named call
        passes `may_create=False`. It does not prove that call is why the route is
        reported — and the exemption removes the route from the sweep entirely, so a
        SECOND write in the same handler would disappear with it, unexamined and
        ungated. The same shape as #1441's prose entry, one level in.

        `write_sinks_of` answers with **every** reachable direct write rather than
        the nearest one, so an added sink cannot hide behind a shorter path. Written
        first as a single sink, this went **red on the tree it was written against**:
        each of the three entries reaches two writes, the profile edge AND the
        profile document, and `write_path_of` had only ever shown the nearer one.
        Both are behind the same `may_create`, so the measurement was widened rather
        than the finding filed — but the hole was real and had been invisible.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        problems = []
        for route_id, (_callee, _keyword, expected) in _GUARDED_PERSISTING_READS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                problems.append(f"{route_id}: no such read route any more")
                continue
            sinks = write_sinks_of(endpoint)
            if sinks != set(expected):
                problems.append(f"{route_id}:\n      excused:   {sorted(expected)}\n      reachable: {sorted(sinks)}")
        assert not problems, (
            "A guarded read reaches a write its witness does not account for. The exemption covers ONE "
            "measured sink; anything else has to be gated or argued on its own:\n  " + "\n  ".join(problems)
        )

    def test_every_intentional_persisting_read_still_persists(self):
        """Obsolescence, the direction that rots — the same rule the findings carry.

        An entry that outlives its write is an excuse for nothing, and the next
        reader takes it as a statement that the route MUST keep writing. If one of
        these two ever stops persisting, the entry goes, it does not stay "just in
        case the write comes back".
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        stale = []
        for route_id, (reason, _sinks) in _INTENTIONAL_PERSISTING_READS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                stale.append(f"{route_id}: no such read route any more ({reason})")
            elif not persists(endpoint):
                stale.append(f"{route_id}: no longer persists — delete the entry ({reason})")
        assert not stale, "Obsolete _INTENTIONAL_PERSISTING_READS entries:\n  " + "\n  ".join(stale)

    def test_an_intentional_persisting_read_reaches_no_write_it_is_not_excused_for(self):
        """SEC-002, applied to the two reads that keep writing on purpose.

        The decision each entry records is about the writes that were MEASURED,
        not about the route. A second, unrelated write added to the same handler —
        an audit row, a counter, a cache — would otherwise inherit an approval
        nobody gave it, which is the failure `_CARE_PROFILE_SINKS` was widened to
        prevent one list down.

        Subset, not equality, and the module comment on
        :data:`_INTENTIONAL_PERSISTING_READS` says why: `write_sinks_of`
        over-approximates through its name fallback, so an equality would go red
        on edits to repositories these routes never touch. A new sink still turns
        this red, which is the claim the entry makes.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        problems = []
        for route_id, (_reason, excused) in _INTENTIONAL_PERSISTING_READS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                continue  # covered by the obsolescence rule above
            unexcused = write_sinks_of(endpoint) - set(excused)
            if unexcused:
                problems.append(f"{route_id}:\n      not excused: " + "\n                   ".join(sorted(unexcused)))
        assert not problems, (
            "A read that persists on purpose reaches a write its entry does not account for. The "
            "decision covers the MEASURED sinks; anything else has to be gated or argued on its "
            "own:\n  " + "\n  ".join(problems)
        )

    def test_a_second_write_in_an_intentional_read_is_reported(self):
        """The mutation SCR-006 asked for, run as a test rather than by hand.

        `privacy.download_export` excuses exactly one sink, so a second write
        inside `PrivacyService.prepare_export_download` has to surface. This drives
        the predicate the sweep drives — `write_sinks_of` minus the excused set —
        over a synthetic tree, because mutating the real service in a test run is
        not available and a hand-run mutation is a claim nobody re-checks.

        The companion claim, that the same mutation does **not** show up for
        `oauth_callback`, is stated on the dict above with its reason; it is a
        property of the sink-identity format, not something this file can fix.
        """
        excused = _INTENTIONAL_PERSISTING_READS["privacy.router.download_export"][1]
        measured_today = {
            (
                "raw query write in app.data_access.arango.data_export_repository"
                "::ArangoDataExportRepository.increment_download_count"
            )
        }
        assert set(excused) == measured_today, (
            "the download_export witness is no longer the single sink this test reasons about"
        )

        # The mutation: the handler grows an insert alongside its update.
        with_a_second_write = measured_today | {
            "self.collection.insert() in app.data_access.arango.base_repository::BaseArangoRepository._insert_doc"
        }
        assert with_a_second_write - set(excused), (
            "a second, unexcused write no longer produces an unexcused sink — the entry has stopped "
            "bounding anything and the dict's promise above is false for it too"
        )

    def test_the_oauth_entry_is_the_blunt_one_and_says_so(self):
        """SCR-006, pinned: the limitation is measured, not merely written down.

        If the entry ever stopped excusing the base primitives, the note above it
        would become wrong in the *safe* direction — but silently, and the next
        reader would take the docstring's caveat as still binding and trust it
        less than they should. Either way the prose and the data have to agree.
        """
        _reason, excused = _INTENTIONAL_PERSISTING_READS["auth.router.oauth_callback"]
        primitives = {
            "self.collection.insert() in app.data_access.arango.base_repository::BaseArangoRepository._insert_doc",
            "self.collection.update() in app.data_access.arango.base_repository::BaseArangoRepository._update_doc",
            "self.collection.update() in app.data_access.arango.base_repository"
            "::BaseArangoRepository._update_doc_fields",
            "self.collection.delete() in app.data_access.arango.base_repository::BaseArangoRepository._delete_doc",
        }
        assert primitives <= set(excused), (
            "the oauth_callback entry no longer excuses every base primitive, so the caveat on "
            "_INTENTIONAL_PERSISTING_READS overstates its own weakness — tighten the note in the same diff."
        )

    def test_every_excused_sink_is_really_reachable(self):
        """The other direction: an entry may not be padded to survive a refactor.

        Subset alone would let somebody widen a set pre-emptively — list every
        sink in the tree and the assertion above can never fail again. This pins
        that each recorded sink is one the route really reaches today, so the set
        is a measurement and not a wish.
        """
        by_id = {}
        for method, _path, endpoint, _route in mounted_operations():
            if method in READ_METHODS:
                by_id[_operation_id(endpoint)] = endpoint

        problems = []
        for route_id, (_reason, excused) in _INTENTIONAL_PERSISTING_READS.items():
            endpoint = by_id.get(route_id)
            if endpoint is None:
                continue
            unreachable = set(excused) - write_sinks_of(endpoint)
            if unreachable:
                problems.append(f"{route_id}:\n      excused but unreachable: " + ", ".join(sorted(unreachable)))
        assert not problems, (
            "These sinks are excused on a route that cannot reach them. Drop them; an excuse for a "
            "write that does not happen hides the next one that does:\n  " + "\n  ".join(problems)
        )

    def test_an_intentional_persisting_read_is_not_also_a_finding_or_an_exemption(self):
        """Three lists, disjoint. An id in two of them means two different verdicts."""
        entries = set(_INTENTIONAL_PERSISTING_READS)
        assert not entries & set(_PERSISTING_READ_FINDINGS), (
            f"recorded both as intentional and as an open finding: {sorted(entries & set(_PERSISTING_READ_FINDINGS))}"
        )
        assert not entries & set(_GUARDED_PERSISTING_READS), (
            f"recorded both as intentional and as argument-guarded: {sorted(entries & set(_GUARDED_PERSISTING_READS))}"
        )

    def test_an_intentional_persisting_read_is_still_swept_like_a_write(self):
        """The property that distinguishes this list from the other two.

        `_GUARDED_PERSISTING_READS` removes a route from `mounted_write_operations`
        and `_PERSISTING_READ_FINDINGS` excuses it from all four gate sweeps.
        Neither may happen here: these routes write on every call, so they have to
        answer the three authorisation questions exactly as a `POST` does. Without
        this assertion the new list would silently become the cheapest way out of
        the file.
        """
        admitted = {op.id for op in mounted_write_operations()}
        missing = sorted(set(_INTENTIONAL_PERSISTING_READS) - admitted)
        assert not missing, f"an intentional persisting read left the write sweep: {missing}"

        for route_id in _INTENTIONAL_PERSISTING_READS:
            assert route_id not in _PERSISTING_READ_FINDINGS

    def test_every_intentional_reason_is_written_out(self):
        for route_id, (reason, _sinks) in _INTENTIONAL_PERSISTING_READS.items():
            assert len(reason) >= 12, f"{route_id} carries no usable reason: {reason!r}"

    def test_the_intentional_list_is_small(self):
        """A ceiling, for the same reason every other list in this file has one.

        Two entries, both protocol- or evidence-bound. A third is the cheapest way
        to close a finding without repairing it — "this one is intentional too" —
        and should cost the conversation the issue is for.
        """
        assert len(_INTENTIONAL_PERSISTING_READS) <= 2, (
            f"_INTENTIONAL_PERSISTING_READS has grown to {len(_INTENTIONAL_PERSISTING_READS)} entries. "
            "A read that writes is a defect until somebody argues otherwise in an issue; say it there, "
            "not only here."
        )

    def test_the_exemption_list_is_small(self):
        """A ceiling, for the same reason `_PUBLIC_ALLOWLIST` has one (SEC-002).

        Three entries today, all of them the same call with the same keyword.
        Every one of them takes a route OUT of the sweep, which makes this the most
        expensive list in the file per line. A fourth is not automatically wrong and
        should cost a conversation — an argument-guarded write is a fix at the
        source waiting to happen, the way #1422's was.
        """
        assert len(_GUARDED_PERSISTING_READS) <= 3, (
            f"_GUARDED_PERSISTING_READS has grown to {len(_GUARDED_PERSISTING_READS)} entries. Each one "
            "removes a persisting read from every sweep in this file; say why in the issue, not only here."
        )

    def test_no_two_writes_share_a_sink_identity(self):
        """The price of dropping the line number, paid over the real tree.

        The identity is `<what> in <module>::<qualname>`, and it is unique only
        because at most ONE sink is recorded per function. If two functions ever
        produced the same string, two different writes would be one entry in every
        sink set and an exemption naming one would silently excuse the other —
        which is the failure `write_sinks` was built to prevent. Measured here
        rather than argued: 116 sinks, 116 distinct names, on 2026-09-16.

        Note what this does NOT claim: 26 functions in the tree contain more than
        one write, 13 of them two that a line-free label could not tell apart. The
        detector reports only the first of them and always did, so no identity
        format can separate them; that limitation belongs to `direct_write` being
        single-valued and is stated in the module docstring, not hidden here.
        """
        sinks = [fn.direct_write for fn in direct_writers()]
        duplicated = sorted({name for name in sinks if sinks.count(name) > 1})

        assert not duplicated, (
            "two functions produced the same sink identity, so one exemption now excuses both:\n  "
            + "\n  ".join(duplicated)
        )
        assert len(sinks) > 100, f"only {len(sinks)} sinks found; the detector stopped seeing the write surface"

    def test_the_unresolved_receiver_count_does_not_grow(self):
        """The blind spot, bounded — the one thing this detector cannot report on itself.

        A call whose receiver carries no type is where a write can hide. Measured
        at this head: 9244 of them across the tree, and only those whose name is in
        the repository write vocabulary are followed. The ceiling is not a quality
        target; it is a tripwire, so that a refactor which un-annotates a layer
        shows up here instead of as a quietly shrinking set of findings.
        """
        assert unresolved_call_count() < 11000, (
            f"{unresolved_call_count()} attribute calls resolve to no receiver type, up from the 9244 "
            "measured on 2026-09-16. The detector is guessing on more of the tree than it was; check "
            "what stopped carrying annotations before trusting a green run."
        )
