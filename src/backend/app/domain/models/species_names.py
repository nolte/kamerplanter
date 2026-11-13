"""The one display rule for a species' vernacular name (REQ-001 v4.14, UI-NFR-007 R-009a, #2902).

``Species.common_names`` is a flat, language-mixed list whose order carries no
language: the seed files list the English name first for most species. A reader
that shows "the first entry" therefore shows English in a German UI. The language
map ``Species.common_names_i18n`` says which of those names belong to which
language, and this module is the single place that turns the two into ONE name:

1. a species WITH a language map: the first name of the requested language, else
   the first name of the canonical language ``de``, else none;
2. a species WITHOUT a language map (``{}`` — created by a tenant or by the CSV
   import, which know no language): the first entry of ``common_names``, else none;
3. :func:`localized_common_name` falls back to the scientific name where (1) or (2)
   found none; :func:`localized_vernacular_name` answers ``None`` instead, for a
   reader that already shows the scientific name in a field of its own.

The rule mirrors the frontend helper ``getLocalizedCommonName``
(``src/frontend/src/utils/plantDisplay.ts``) including the language normalisation
(``de-DE`` -> ``de``). Every server-built display name goes through here; the
guard ``tests/unit/guards/test_species_display_names_use_the_resolver.py`` holds
that no reader takes ``common_names[0]`` on its own.

The functions take the raw fields rather than a :class:`~app.domain.models.species.Species`
so that a repository row (``species.common_names`` / ``species.common_names_i18n``
read straight from an AQL projection, possibly ``null``) resolves through the same
rule as a loaded model.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from app.common.locale import DEFAULT_LOCALE

#: The canonical language of names and generated texts (UI-NFR-007 R-009a). A reader
#: that has no request language - a background task, a persisted title - resolves in
#: this language; a request's language comes from ``app.common.locale.get_request_locale``.
CANONICAL_NAME_LANGUAGE = DEFAULT_LOCALE


def normalize_name_language(language: str | None) -> str:
    """``language`` as the key of ``common_names_i18n``: ``de-DE`` / ``en_US`` / ``EN`` -> ``de`` / ``en`` / ``en``.

    A missing or blank language is the canonical one.
    """
    # Typed locals, one call each: the write-route guard resolves a typed receiver, not a chain.
    raw: str = re.split(r"[-_]", language or "", maxsplit=1)[0]
    stripped: str = raw.strip()
    primary: str = stripped.lower()
    return primary or CANONICAL_NAME_LANGUAGE


def _first_name(names: Sequence[str] | None) -> str | None:
    """The first non-blank name of ``names`` without surrounding whitespace; ``None`` when there is none.

    Skips blank entries like the frontend's ``firstNonEmpty`` (``utils/plantDisplay.ts``).
    """
    for raw in names or ():
        name: str = str(raw)
        stripped: str = name.strip()
        if stripped:
            return stripped
    return None


def localized_vernacular_name(
    common_names: Sequence[str] | None,
    common_names_i18n: Mapping[str, Sequence[str]] | None,
    language: str | None,
) -> str | None:
    """The vernacular name to show for ``language``, or ``None`` when the species has none to show.

    For a reader that shows the scientific name next to it (a separate field): the
    scientific fallback of :func:`localized_common_name` would show it twice.
    """
    if common_names_i18n:
        by_language: dict[str, Sequence[str]] = dict(common_names_i18n)
        wanted = normalize_name_language(language)
        for code in (wanted, CANONICAL_NAME_LANGUAGE):
            name = _first_name(by_language.get(code))
            if name is not None:
                return name
        # The map knows the species' languages and neither the requested nor the
        # canonical one is among them: the flat list would only guess.
        return None
    # No language map (a tenant-created or CSV-imported species): the list is all
    # the record says, and its first entry is what the user typed first.
    return _first_name(common_names)


def localized_common_name(
    common_names: Sequence[str] | None,
    common_names_i18n: Mapping[str, Sequence[str]] | None,
    scientific_name: str | None,
    language: str | None,
) -> str:
    """The display name of a species for ``language``: vernacular name by the rule above, else the scientific name.

    Empty only when the species carries neither.
    """
    return localized_vernacular_name(common_names, common_names_i18n, language) or (scientific_name or "")
