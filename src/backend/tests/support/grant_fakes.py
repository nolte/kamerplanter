"""Grant-arm defaults for species/cultivar repository doubles (#1092).

Since #1092 a masterdata row is visible three ways: the caller owns it, it is
global, or it has been **explicitly granted** to the caller. The by-key reads
(:meth:`SpeciesService.get_species`, :meth:`SpeciesService.get_cultivar`) ask the
repository the third question directly, because a predicate arm in a list query
does nothing for a document load.

Most doubles in this suite model a world with no grants at all. For them ``False``
is not a stub — it is the true answer, and stating it here once keeps the
scope-hiding tests (foreign row → 404) asserting what they were written to assert
instead of dying on ``AttributeError``.

What this mixin deliberately does **not** do is default to ``True`` or fall back to
some other visibility check. A grant arm that answered "yes" by default would turn
every one of those 404 tests green for the wrong reason — the exact shape of an
inert guard. Doubles that *do* model grants (``tests/api/test_species_grants.py``)
override these with a real answer.
"""

from __future__ import annotations


class NoGrantsMixin:
    """No explicit grant exists in this fixture's world."""

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        return False

    def is_cultivar_granted_to(self, cultivar_key: str, tenant_key: str) -> bool:
        return False
