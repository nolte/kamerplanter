"""Shared hybrid-catalog tenant-union read predicate (SEC-B4, PR #324 follow-up).

Several ArangoDB collections are **hybrid catalogs**: they hold globally seeded
system rows (``tenant_key == ""`` — the empty tenant IS the global marker, there
is no ``is_system`` flag on the row) *plus* per-tenant custom rows. A read for a
tenant must therefore *union* that tenant's own rows with the global rows, or the
seeded catalogue disappears for every real tenant — the #324 regression class, a
strict ``doc.tenant_key == @tenant_key`` filter that traded a leak for an empty
list. It must equally never return a *foreign* tenant's rows.

This module is the single source of truth for that predicate. Before it existed
the same fragment was copied verbatim into
:class:`~app.data_access.arango.fertilizer_repository.ArangoFertilizerRepository`,
:class:`~app.data_access.arango.nutrient_plan_repository.ArangoNutrientPlanRepository`
and :class:`~app.data_access.arango.task_repository.ArangoTaskRepository` (twice),
with a deliberately narrower two-arm variant in
:class:`~app.data_access.arango.ai_repository.ArangoAiProviderRepository`. Routing
every consumer through one helper means the next consumer (species reads) adds a
call, not a fifth copy.

**The empty-string arm is parameterised on purpose.** The three catalog
repositories want the full three-arm union
(``== @tenant_key OR == "" OR == null``). ``ai_provider_configs`` deliberately
reads only two arms (``== @tenant_key OR == null``): its system defaults are
seeded with a *null* ``tenant_key``, never an empty string, so admitting the
``== ""`` arm would widen its read scope — a behaviour change under a
"no behaviour change" banner. Callers that want the narrower semantics pass
``include_empty_string=False``; the default is the three-arm union.
"""

from __future__ import annotations


def tenant_union_predicate(
    tenant_key: str,
    *,
    doc_var: str = "doc",
    field: str = "tenant_key",
    bind_name: str = "tenant_key",
    include_empty_string: bool = True,
) -> tuple[str, dict[str, str]]:
    """Build the hybrid-catalog tenant-union read predicate and its bind var.

    Returns a parenthesised AQL boolean fragment plus the single bind-var mapping
    the fragment references, so a caller merges it into an existing ``bind_vars``
    dict and drops the fragment into its ``FILTER``/``filter_clauses`` exactly the
    way these repositories already assemble AQL:

    >>> tenant_union_predicate("t1")
    ('(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)', {'tenant_key': 't1'})
    >>> tenant_union_predicate("t1", include_empty_string=False)
    ('(doc.tenant_key == @tenant_key OR doc.tenant_key == null)', {'tenant_key': 't1'})

    Args:
        tenant_key: The caller's tenant, bound (never interpolated) as ``@<bind_name>``.
        doc_var: The AQL document variable the predicate reads (``doc`` by default;
            pass the loop variable a hand-written query uses if it differs).
        field: The tenant-ownership field name (``tenant_key`` by default).
        bind_name: The bind-variable name the fragment references. Override it
            only to avoid a collision with an existing bind var in the same query.
        include_empty_string: When ``True`` (default) the fragment is the full
            three-arm union (``@tenant_key OR "" OR null``). Pass ``False`` for the
            two-arm variant (``@tenant_key OR null``) that
            :class:`ArangoAiProviderRepository` needs to keep its read scope
            unchanged — its system defaults carry a null tenant, never ``""``.

    Returns:
        ``(fragment, bind_vars)`` — the AQL predicate string and the
        ``{bind_name: tenant_key}`` mapping it references.
    """
    arms = [f"{doc_var}.{field} == @{bind_name}"]
    if include_empty_string:
        arms.append(f'{doc_var}.{field} == ""')
    arms.append(f"{doc_var}.{field} == null")
    fragment = "(" + " OR ".join(arms) + ")"
    return fragment, {bind_name: tenant_key}
