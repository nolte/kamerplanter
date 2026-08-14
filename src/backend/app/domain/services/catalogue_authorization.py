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

from app.common.exceptions import ForbiddenError


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
