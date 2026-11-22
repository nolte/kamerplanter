"""v0113 — #2857: a stored ``day_neutral`` that was only the old default becomes ``unspecified``.

**Why.** ``LifecycleConfig.photoperiod_type`` defaulted to ``day_neutral`` - in the model, the API body, the profile
form and the core seed, which created every ``species.yaml`` species' lifecycle with it. A stored ``day_neutral``
therefore did not say the species was classified. Since #2857 the default is ``unspecified`` and ``day_neutral`` is a
statement the tent rule acts on (REQ-053 §9.2a: a day-neutral plant leaves the photoperiod conflict), so a default
left as ``day_neutral`` would silence real conflicts.

**How a default is told from a stated value.** Only the seed data state a type with a source: the
``lifecycle_configs`` of ``adventskalender.yaml``, ``plant_info.yaml`` and the ``plant_info_*.yaml`` files (compared
against the Steckbriefe by ``seed_steckbrief_consistency``) and the entries of ``lifecycles_outdoor.yaml``.
:attr:`PhotoperiodUnspecifiedMigration.SOURCED` freezes the type each of them states for a species (180 species, no
two sources disagree), taken from those files at this version. A lifecycle that holds ``day_neutral`` is decided by
its species (``lifecycle.species_key``):

* a **global catalogue species** (``tenant_key`` empty) named in ``SOURCED`` keeps ``day_neutral`` when that is the
  stated type (``kept_sourced``); when the source states another type the lifecycle gets it (``corrected``). That is
  hemp: ``plant_info.yaml`` states ``short_day``, but the loader never resolved a species listed under
  ``lifecycle_configs`` alone, so the core seed's ``day_neutral`` stayed (the loader is repaired in the same change);
* every other lifecycle - a global species without a source, a tenant's own species (whatever its name: a catalogue
  value is never written to a tenant's row), a lifecycle whose species is gone - becomes ``unspecified``. Its
  ``day_neutral`` cannot be told from the default: the API body and the profile form offered ``day_neutral``
  preselected. ``unspecified`` claims nothing (E-10); a person who meant ``day_neutral`` sets it again.

Only ``day_neutral`` rows are touched; a stored ``short_day`` or ``long_day`` was never a default. Phase sequences
are left alone: their ``photoperiod_type`` is shown, but no rule reads it (the resolver and the tent rule read the
lifecycle); the system sequences state theirs in ``phase_sequences.yaml``.

**Consistent against a live writer.** The update re-checks ``photoperiod_type == "day_neutral"``; a lifecycle a
person changed between scan and write is skipped and counted (``skipped_changed_since_scan``).

**Idempotent (M-3).** A second run finds only the ``kept_sourced`` rows and writes nothing.
**Dry run (M-5).** Counts per bucket, nothing written.
**Not reversible (M-6).** ``down`` could put ``day_neutral`` back on the rows it marked, but the code before this
version cannot read ``unspecified``, which the seeds and the API write from now on - a downgrade would not reach a
state the old code can load, so none is offered.
**Frozen (M-7).** Collection names, the values and ``SOURCED`` are literals on the class.
"""

from __future__ import annotations

from typing import Any, ClassVar, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class PhotoperiodUnspecifiedMigration(Migration):
    version = "0113"
    name = "photoperiod_unspecified"
    description = (
        "#2857: a lifecycle's stored day_neutral that no seed source states becomes unspecified; a catalogue species "
        "whose source states another type gets it (hemp: short_day)."
    )
    reversible = False

    #: Frozen collection names (M-7).
    LIFECYCLES = "lifecycle_configs"
    SPECIES = "species"

    #: Frozen ``PhotoperiodType`` values (M-7).
    DAY_NEUTRAL = "day_neutral"
    UNSPECIFIED = "unspecified"

    #: Lifecycle keys a report lists per bucket before it only counts.
    LISTED = 25
    #: Keys per update statement.
    BATCH_SIZE = 500

    #: The type the seed sources state per scientific name (#2857), frozen at this version.
    SOURCED: ClassVar[dict[str, str]] = {
        "Adiantum raddianum": "day_neutral",
        "Aechmea fasciata": "day_neutral",
        "Aeschynanthus radicans": "day_neutral",
        "Aglaonema commutatum": "day_neutral",
        "Allium cepa": "long_day",
        "Allium porrum": "long_day",
        "Allium sativum": "long_day",
        "Allium schoenoprasum": "long_day",
        "Alocasia x amazonica": "day_neutral",
        "Aloe vera": "day_neutral",
        "Anemone hupehensis": "short_day",
        "Anethum graveolens": "long_day",
        "Anthurium andraeanum": "day_neutral",
        "Aphelandra squarrosa": "short_day",
        "Apium graveolens": "long_day",
        "Apium graveolens var. rapaceum": "long_day",
        "Ardisia crenata": "day_neutral",
        "Asparagus officinalis": "day_neutral",
        "Asparagus setaceus": "day_neutral",
        "Aspidistra elatior": "day_neutral",
        "Asplenium nidus": "day_neutral",
        "Astilbe chinensis": "long_day",
        "Beaucarnea recurvata": "day_neutral",
        "Begonia rex-cultorum": "day_neutral",
        "Begonia semperflorens": "day_neutral",
        "Beta vulgaris subsp. vulgaris": "long_day",
        "Brassica oleracea var. gemmifera": "long_day",
        "Brassica oleracea var. sabellica": "day_neutral",
        "Buxus sempervirens": "day_neutral",
        "Calendula officinalis": "day_neutral",
        "Cannabis sativa": "short_day",
        "Capsicum annuum": "day_neutral",
        "Cattleya hybrida": "day_neutral",
        "Ceropegia woodii": "day_neutral",
        "Chamaedorea elegans": "day_neutral",
        "Chlorophytum comosum": "day_neutral",
        "Cichorium intybus": "long_day",
        "Clematis spp.": "long_day",
        "Clivia miniata": "day_neutral",
        "Codiaeum variegatum": "day_neutral",
        "Coffea arabica": "day_neutral",
        "Coriandrum sativum": "long_day",
        "Cornus mas": "day_neutral",
        "Crassula ovata": "day_neutral",
        "Ctenanthe burle-marxii": "day_neutral",
        "Cucumis sativus": "day_neutral",
        "Cucurbita maxima": "day_neutral",
        "Cucurbita pepo": "day_neutral",
        "Curio rowleyanus": "day_neutral",
        "Cyclamen persicum": "day_neutral",
        "Dahlia pinnata": "short_day",
        "Dahlia x cultorum": "short_day",
        "Daucus carota": "long_day",
        "Delphinium elatum": "long_day",
        "Dendrobium nobile": "day_neutral",
        "Dieffenbachia seguine": "day_neutral",
        "Dracaena angolensis": "day_neutral",
        "Dracaena fragrans": "day_neutral",
        "Dracaena marginata": "day_neutral",
        "Dracaena trifasciata": "day_neutral",
        "Dypsis lutescens": "day_neutral",
        "Echeveria elegans": "day_neutral",
        "Echinacea purpurea": "long_day",
        "Epipremnum aureum": "day_neutral",
        "Euphorbia pulcherrima": "short_day",
        "Fatsia japonica": "day_neutral",
        "Ficus benjamina": "day_neutral",
        "Ficus elastica": "day_neutral",
        "Ficus lyrata": "day_neutral",
        "Fittonia albivenis": "day_neutral",
        "Foeniculum vulgare": "long_day",
        "Forsythia x intermedia": "day_neutral",
        "Fragaria x ananassa": "day_neutral",
        "Gardenia jasminoides": "short_day",
        "Geranium sanguineum": "day_neutral",
        "Goeppertia lancifolia": "day_neutral",
        "Goeppertia makoyana": "day_neutral",
        "Goeppertia orbifolia": "day_neutral",
        "Guzmania lingulata": "day_neutral",
        "Gymnocalycium mihanovichii": "day_neutral",
        "Haworthiopsis fasciata": "day_neutral",
        "Hedera helix": "day_neutral",
        "Helianthus annuus": "day_neutral",
        "Helleborus niger": "day_neutral",
        "Hemerocallis spp.": "day_neutral",
        "Hibiscus rosa-sinensis": "day_neutral",
        "Hippeastrum hybridum": "day_neutral",
        "Hosta spp.": "day_neutral",
        "Howea forsteriana": "day_neutral",
        "Hoya carnosa": "day_neutral",
        "Hydrangea macrophylla": "day_neutral",
        "Impatiens walleriana": "day_neutral",
        "Jasminum polyanthum": "short_day",
        "Kalanchoe blossfeldiana": "short_day",
        "Kalanchoe daigremontiana": "short_day",
        "Lactuca sativa": "long_day",
        "Lavandula angustifolia": "day_neutral",
        "Levisticum officinale": "day_neutral",
        "Ligustrum vulgare": "day_neutral",
        "Lithops spp.": "day_neutral",
        "Livistona chinensis": "day_neutral",
        "Lupinus polyphyllus": "day_neutral",
        "Malus domestica": "day_neutral",
        "Mammillaria spp.": "day_neutral",
        "Maranta leuconeura": "day_neutral",
        "Medicago sativa": "day_neutral",
        "Melissa officinalis": "day_neutral",
        "Mentha piperita": "day_neutral",
        "Monstera adansonii": "day_neutral",
        "Monstera deliciosa": "day_neutral",
        "Neoregelia carolinae": "day_neutral",
        "Nephrolepis exaltata": "day_neutral",
        "Nymphaea alba": "day_neutral",
        "Ocimum basilicum": "day_neutral",
        "Opuntia microdasys": "day_neutral",
        "Origanum vulgare": "day_neutral",
        "Oxalis triangularis": "day_neutral",
        "Pachira aquatica": "day_neutral",
        "Paeonia lactiflora": "day_neutral",
        "Pastinaca sativa": "day_neutral",
        "Pelargonium zonale": "day_neutral",
        "Peperomia obtusifolia": "day_neutral",
        "Petroselinum crispum": "long_day",
        "Petunia x hybrida": "day_neutral",
        "Phacelia tanacetifolia": "day_neutral",
        "Phalaenopsis hybrida": "day_neutral",
        "Phaseolus vulgaris": "day_neutral",
        "Philodendron hederaceum": "day_neutral",
        "Phlox paniculata": "day_neutral",
        "Pilea peperomioides": "day_neutral",
        "Pisum sativum": "long_day",
        "Platycerium bifurcatum": "day_neutral",
        "Plectranthus verticillatus": "day_neutral",
        "Prunus avium": "day_neutral",
        "Prunus domestica": "day_neutral",
        "Pyrus communis": "day_neutral",
        "Raphanus sativus": "day_neutral",
        "Rheum rhabarbarum": "day_neutral",
        "Rhipsalis baccifera": "day_neutral",
        "Rhododendron simsii": "short_day",
        "Rhododendron spp.": "day_neutral",
        "Ribes rubrum": "day_neutral",
        "Ribes uva-crispa": "day_neutral",
        "Rosa spp.": "day_neutral",
        "Rubus fruticosus agg.": "day_neutral",
        "Rubus idaeus": "day_neutral",
        "Salvia officinalis": "day_neutral",
        "Salvia rosmarinus": "day_neutral",
        "Sambucus nigra": "day_neutral",
        "Satureja hortensis": "day_neutral",
        "Schefflera arboricola": "day_neutral",
        "Schlumbergera truncata": "short_day",
        "Sedum morganianum": "day_neutral",
        "Sinapis alba": "day_neutral",
        "Solanum lycopersicum": "day_neutral",
        "Soleirolia soleirolii": "day_neutral",
        "Spathiphyllum wallisii": "day_neutral",
        "Spinacia oleracea": "long_day",
        "Stephanotis floribunda": "short_day",
        "Strelitzia reginae": "day_neutral",
        "Streptocarpus hybridus": "long_day",
        "Streptocarpus ionanthus": "day_neutral",
        "Stromanthe sanguinea": "day_neutral",
        "Syngonium podophyllum": "day_neutral",
        "Syringa vulgaris": "day_neutral",
        "Tagetes patula": "day_neutral",
        "Thymus vulgaris": "day_neutral",
        "Tigridia pavonia": "day_neutral",
        "Tillandsia usneoides": "day_neutral",
        "Tradescantia zebrina": "day_neutral",
        "Tropaeolum majus": "day_neutral",
        "Vaccinium corymbosum": "day_neutral",
        "Viburnum opulus": "day_neutral",
        "Viola x wittrockiana": "day_neutral",
        "Vitis vinifera": "day_neutral",
        "Vriesea splendens": "day_neutral",
        "Weigela florida": "day_neutral",
        "Yucca elephantipes": "day_neutral",
        "Zamioculcas zamiifolia": "day_neutral",
        "Zantedeschia aethiopica": "day_neutral",
    }

    #: Every lifecycle holding ``day_neutral``, with what the decision needs from its species.
    SCAN = """
    FOR lc IN @@lifecycles
      FILTER lc.photoperiod_type == @day_neutral
      SORT lc._key
      LET sp = (lc.species_key == null OR lc.species_key == "") ? null : DOCUMENT(@species, lc.species_key)
      RETURN {
        key: lc._key,
        species_found: sp != null,
        is_global: sp != null AND (sp.tenant_key == null OR sp.tenant_key == ""),
        scientific_name: sp == null ? null : sp.scientific_name
      }
    """

    #: Writes ``@target`` on the listed lifecycles that still hold ``day_neutral``; returns how many it wrote.
    APPLY = """
    FOR lc IN @@lifecycles
      FILTER lc._key IN @keys AND lc.photoperiod_type == @day_neutral
      UPDATE lc WITH { photoperiod_type: @target } IN @@lifecycles
      COLLECT WITH COUNT INTO written
      RETURN written
    """

    @classmethod
    def decide(cls, row: dict[str, Any]) -> tuple[str, str | None]:
        """The bucket of a scanned lifecycle and the type to write (``None`` = keep ``day_neutral``)."""
        if not row.get("species_found"):
            return "unspecified_species_missing", cls.UNSPECIFIED
        if not row.get("is_global"):
            return "unspecified_tenant_species", cls.UNSPECIFIED
        stated = cls.SOURCED.get(str(row.get("scientific_name") or ""))
        if stated is None:
            return "unspecified_without_source", cls.UNSPECIFIED
        if stated == cls.DAY_NEUTRAL:
            return "kept_sourced", None
        return "corrected", stated

    def _apply(self, db: StandardDatabase, keys: list[str], target: str) -> int:
        written = 0
        for start in range(0, len(keys), self.BATCH_SIZE):
            cursor = cast(
                Cursor,
                db.aql.execute(
                    self.APPLY,
                    bind_vars={
                        "@lifecycles": self.LIFECYCLES,
                        "keys": keys[start : start + self.BATCH_SIZE],
                        "day_neutral": self.DAY_NEUTRAL,
                        "target": target,
                    },
                ),
            )
            written += sum(int(n) for n in cursor)
        return written

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not (db.has_collection(self.LIFECYCLES) and db.has_collection(self.SPECIES)):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        rows = cast(
            Cursor,
            db.aql.execute(
                self.SCAN,
                bind_vars={"@lifecycles": self.LIFECYCLES, "species": self.SPECIES, "day_neutral": self.DAY_NEUTRAL},
            ),
        )
        scanned = 0
        buckets: dict[str, dict[str, Any]] = {}
        targets: dict[str, list[str]] = {}
        corrected_to: dict[str, int] = {}
        for row in rows:
            scanned += 1
            bucket, target = self.decide(row)
            entry = buckets.setdefault(bucket, {"count": 0, "listed": []})
            entry["count"] += 1
            if len(entry["listed"]) < self.LISTED:
                entry["listed"].append(str(row["key"]))
            if target is None:
                continue
            targets.setdefault(target, []).append(str(row["key"]))
            if bucket == "corrected":
                corrected_to[target] = corrected_to.get(target, 0) + 1
        planned = sum(len(keys) for keys in targets.values())
        details: dict[str, Any] = {
            "scanned_day_neutral": scanned,
            "buckets": buckets,
            "corrected_to": corrected_to,
        }
        if dry_run:
            details["will_write"] = planned
            logger.info("photoperiod_unspecified_dry_run", scanned=scanned, will_write=planned)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        written = sum(self._apply(db, keys, target) for target, keys in sorted(targets.items()))
        details["written"] = written
        details["skipped_changed_since_scan"] = planned - written
        logger.info("photoperiod_unspecified_applied", scanned=scanned, written=written)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=written, dry_run=False, details=details
        )


migration = PhotoperiodUnspecifiedMigration()
