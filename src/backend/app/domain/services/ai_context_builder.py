"""REQ-031 §4.2 (+ ADR-002) — ``AiContextBuilder``.

Builds the PII-free :class:`~app.domain.interfaces.knowledge_service.
QuestionContext` sent to the Knowledge Service. Two hard rules (NFR-007):

* the **base context** (species/phase/substrate/ec/ph) is always safe to send —
  no names, e-mails, IPs or free-text notes ever enter it;
* the **extended context** (aggregated care history) is only attached when the
  user granted ``ai_tenant_data_access`` and is likewise aggregate-only.

ADR-002: tenant-owned species are not in the KS index, so
:meth:`resolve_species_for_ks` maps them onto a resolvable anchor (parent →
genus → family) and reports a :class:`ConfidenceLevel` the UI surfaces.
"""

from __future__ import annotations

from collections.abc import Callable

from app.common.enums import DataOrigin
from app.domain.interfaces.knowledge_service import ConfidenceLevel, QuestionContext
from app.domain.models.species import Species

#: A parent-species resolver (``parent_species_key -> Species | None``).
ParentResolver = Callable[[str], Species | None]
#: A family-name resolver (``family_key -> family name | None``).
FamilyResolver = Callable[[str], str | None]


class AiContextBuilder:
    """Assembles the KS question context with strict data minimisation."""

    def __init__(
        self,
        *,
        parent_resolver: ParentResolver | None = None,
        family_resolver: FamilyResolver | None = None,
    ) -> None:
        self._parent_resolver = parent_resolver
        self._family_resolver = family_resolver

    def resolve_species_for_ks(self, species: Species) -> tuple[str | None, str | None, ConfidenceLevel]:
        """ADR-002 — map a species onto a KS-resolvable value.

        Returns ``(ks_species_value, cultivar_hint, confidence)``. Global species
        resolve directly (HIGH); tenant species fall back through their parent
        (MEDIUM), genus (LOW) and family (LOW); a tenant species with no botanical
        anchor yields ``(None, hint, NONE)`` so the caller skips the KS call and
        answers rule-based.
        """
        if species.origin != DataOrigin.TENANT:
            return (species.scientific_name, None, ConfidenceLevel.HIGH)

        first_common = species.common_names[0] if species.common_names else None

        parent_key = getattr(species, "parent_species_key", None)
        if parent_key and self._parent_resolver is not None:
            parent = self._parent_resolver(parent_key)
            if parent is not None and parent.origin != DataOrigin.TENANT:
                return (
                    parent.scientific_name,
                    species.scientific_name or first_common,
                    ConfidenceLevel.MEDIUM,
                )

        if species.genus:
            return (
                f"{species.genus} sp.",
                species.scientific_name or first_common,
                ConfidenceLevel.LOW,
            )

        family_key = getattr(species, "family_key", None)
        if family_key and self._family_resolver is not None:
            family_name = self._family_resolver(family_key)
            if family_name:
                return (family_name, species.scientific_name, ConfidenceLevel.LOW)

        return (None, species.scientific_name or first_common, ConfidenceLevel.NONE)

    def build_base_context(
        self,
        *,
        species: Species | None = None,
        phase: str | None = None,
        substrate: str | None = None,
        ec: float | None = None,
        ph: float | None = None,
    ) -> QuestionContext:
        """Build the always-safe base context (§4.2).

        Only master values enter here. When a species is given, ADR-002
        resolution fills ``species``/``cultivar_hint``/``confidence``.
        """
        ks_species: str | None = None
        cultivar_hint: str | None = None
        confidence = ConfidenceLevel.HIGH
        if species is not None:
            ks_species, cultivar_hint, confidence = self.resolve_species_for_ks(species)
        return QuestionContext(
            species=ks_species,
            cultivar_hint=cultivar_hint,
            confidence=confidence,
            phase=phase,
            substrate=substrate,
            ec=ec,
            ph=ph,
        )
