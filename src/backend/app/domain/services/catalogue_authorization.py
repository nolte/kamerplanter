"""The one rule for writing *global* reference data (#1109, #1120, #1110).

Three surfaces answer the same question — "may this caller modify a row that
every tenant reads?" — and each of them reached it by a different route:

* :mod:`app.domain.services.species_service` for the global arm of the hybrid
  species / cultivar catalogue (SEC-002 #808, C-4 #1090),
* ``app.api.v1.botanical_families.router`` for botanical families, which are
  global-*only* — the model carries no ``tenant_key``, so there is not even an
  ownership boundary to fall back on (#1120),
* :mod:`app.domain.services.import_service` for the CSV import, which writes the
  very same rows from a completely different entry point (#1110).

They used to carry three copies of the refusal, two of them spelled out
literally. That is the drift pattern REQ-049 §2.3 was re-pinned over: a rule
stated in more than one place eventually answers differently in each, and the
copy nobody looks at is the one that stays permissive. Hence one function,
imported by all three.

Deliberately **not** a FastAPI dependency: two of the three callers are domain
services with no request in scope, and expressing the rule as a route dependency
would have put it out of reach of exactly the caller (#1110's import path) that
was bypassing it.
"""

from __future__ import annotations

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError
from app.domain.engines.membership_engine import MembershipEngine


def require_platform_admin_for_global_catalogue(*, is_platform_admin: bool, entity: str) -> None:
    """Refuse a non-platform-admin write to global reference data.

    ``entity`` names the catalogue in the refusal ("species", "cultivar",
    "botanical family"); it is lower-cased into the message so callers may pass
    the same capitalised entity name they use for a 404.

    A 403 rather than a 404 on purpose: a global row is visible to every caller,
    so hiding its existence would be a lie the caller can trivially disprove with
    a GET. Ownership hiding (foreign row → 404) is a different arm and stays with
    :func:`~app.domain.services.species_service._authorize_tenant_owned_write`.

    The light-mode operator (REQ-027) and a ``platform`` lead both arrive here as
    ``is_platform_admin=True`` — the mode split lives in
    :func:`~app.common.auth.get_is_platform_admin`, not in this rule, so curating
    the shared catalogue in a single-operator deployment keeps working.
    """
    if not is_platform_admin:
        raise ForbiddenError(f"Only a platform admin may modify the global {entity.lower()} catalogue.")


def require_role_for_catalogue_create(
    *,
    plural_noun: str,
    caller_role: TenantRole | None,
    is_platform_admin: bool,
) -> None:
    """Gate a hybrid-catalogue **create** on the caller's domain role — SEC-005 (#1113).

    The create sibling of ``SpeciesService._authorize_tenant_owned_write``, and deliberately
    the same kind of object: **one** function shared by Species and Cultivar rather
    than a check per router. A router-only copy is precisely the drift that pulled
    the delete boundary apart from :class:`MembershipEngine` before REQ-049 §2.3 was
    re-pinned — and the reason the create hole existed at all is that the two POST
    routes stamped ownership without ever asking who the caller was, while their
    PUT/DELETE neighbours did.

    Qualified as **SEC-005 (#1113)** throughout: ``SEC-005`` names two unrelated
    findings (R-7) — the #808 companion-anchor/search scoping and this create gate.

    Only one of the write gate's four arms survives, because there is no existing
    row to own:

    * ``caller_role is None`` — the unscoped **system-context** create (seeders,
      CSV import, migrations, enrichment; no HTTP caller). No gate at all, mirroring
      the ``tenant_key is None`` escape of :func:`_authorize_tenant_owned_write`, so
      those callers keep working unchanged. Every HTTP route passes a real role
      (:func:`~app.common.auth.get_active_tenant_context` falls back to
      :attr:`TenantRole.VIEWER`, never ``None``), so the escape is not reachable
      from the wire.
    * platform admin — bypasses the domain rank, as it does for update/delete. This
      is what keeps light-mode curation (REQ-027) of the shared catalogue working:
      the sole operator holds no membership, so their context role is the fail-safe
      viewer.
    * otherwise the domain role gate: ``can_edit_resource`` — lead or grower may
      create, a viewer may not (REQ-049 §2.3). There is no ``can_delete_resource``
      arm and no ownership arm to choose between, so unlike the write gate this
      takes no predicate argument: passing one would be a parameter that never
      varies, and an argument that can only hold one value is the kind of hook that
      silently stops meaning anything.

    Refusal is a 403, never a 404: the caller is a legitimate member of the tenant
    they are creating in — they are merely under-privileged — and there is no
    existing row whose existence a 404 could hide.

    Moved here from ``species_service`` by #1195, when substrates became the third
    hybrid catalogue to need it. It lived next to one of its callers for as long as
    there was only one; a second copy in ``substrate_service`` would have been the
    drift this module's own docstring exists to prevent.
    """
    if caller_role is None:
        return
    if is_platform_admin:
        return
    if not MembershipEngine.can_edit_resource(caller_role):
        raise ForbiddenError(f"Your role may not create {plural_noun} in this tenant.")
