# Spezifikation: REQ-040 - Wissensbasis-Enrichment via OpenFarm (optionaler CC0-Dump) & Growstuff (nur Mapping-Vorlage)

```yaml
ID: REQ-040
Titel: Wissensbasis-Enrichment (OpenFarm optionaler CC0-Dump & Growstuff nur Mapping-Vorlage) inkl. Companion-Daten
Kategorie: Stammdaten
Fokus: Backend
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, REST-APIs
Status: Entwurf (zurückgestellt/optional)
Version: 1.1
Abhängigkeit: REQ-011 (Externe Stammdatenanreicherung), REQ-028 (Mischkultur/Companion), REQ-001 (Stammdaten), REQ-025 (DSGVO/Consent)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-19 | Initialer Entwurf — Integration von OpenFarm + Growstuff (awesome-agriculture) |
| 1.1 | 2026-06-20 | G2/G3: OpenFarm nur optionaler CC0-Dump (Server tot), Growstuff nur Mapping-Idee (kein Wertimport wg. CC-BY-SA/REQ-032); Priorität optional |

## 1. Business Case

**User Story (Admin — Lücken schließen):** "Als Plattform-Administrator möchte ich die Wissensbasis aus zwei zusätzlichen, frei verfügbaren Garten-Datenbanken (OpenFarm, Growstuff) anreichern, damit Lücken bei Anbauzeiträumen, Pflegehinweisen und vor allem Mischkultur-Beziehungen ohne manuelle Pflege geschlossen werden."

**User Story (Gärtnerin — Mischkultur):** "Als Gärtnerin möchte ich, dass das System für meine Pflanzen automatisch bekannte Mischkultur-Partner kennt, damit die Companion-Empfehlung (REQ-028) auch für Arten greift, die noch keine kuratierten `compatible_with`-Kanten haben."

**Beschreibung:**
REQ-040 ergänzt die bestehende Enrichment-Architektur aus **REQ-011** um **eine optionale, einmalige Datenquelle** und **eine reine Mapping-Vorlage**. Die in v1.0 vorgesehenen zwei **Live-Adapter** (`OpenFarmAdapter`, `GrowstuffAdapter`) sind nach der verifizierten Lizenz- und Nutzungsanalyse (`spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`, REQ-040-Abschnitt) **nicht mehr Bestandteil der Spezifikation**:

- **OpenFarm (Entscheidung G3):** Der OpenFarm-Server ist seit **April 2025 abgeschaltet/archiviert** (die v1-API antwortet nur noch mit `301`-Redirect). Ein Live-Adapter ist damit **nicht realisierbar**. Die Daten sind **CC0 (Public Domain, keine Auflagen)**; deshalb bleibt ein **optionaler, einmaliger statischer CC0-Dump-Import** aus einem Mirror möglich (bei Bedarf, nicht als wartbare Live-Quelle). Dieser Dump-Import respektiert die bestehende REQ-011-Confidence-Kette (leere Felder Auto-Accept 0.9, bestehende Felder Propose-only 0.7).
- **Growstuff (Entscheidung G2):** Die Growstuff-Daten stehen unter **CC-BY-SA 3.0** (der Code unter AGPL-3.0 ist irrelevant, da nur API-Daten konsumiert würden). Eine Verschmelzung in Kamerplanters Stammdaten würde **ShareAlike + Attribution** auf die abgeleitete Daten-Sammlung auslösen und damit **jeden Export/jede Druckansicht binden (Kollision mit REQ-032)**. Entscheidung: **Growstuff wird ausschließlich als Mapping-/Ideen-Vorlage genutzt — es werden KEINE Growstuff-Werte importiert.** Das Field-Mapping bleibt als Referenz/Inspiration erhalten, erzeugt aber keine Stammdaten.

Der **separate Import-Pfad für Companion-Relationen** in den Graph (REQ-028) bleibt erhalten, gilt aber **nur im Kontext des optionalen OpenFarm-CC0-Dumps** — niemals aus Growstuff.

**Konkrete Lücken, die (optional) geschlossen werden können:**

- **Anbauzeiträume** (`sowing_*_months`, `harvest_months`) — das Anbauzeitraum-Audit hat die Restlücken bereits **weitgehend geschlossen** (nur 10/143 echte Lücken waren offen). Der Zusatznutzen ist daher marginal.
- **Pflegehinweise** (Sonnenbedarf, Aussaatmethode, Reihen-/Pflanzabstand, Tage bis Reife) — nur aus dem OpenFarm-CC0-Dump.
- **Companion-Planting-Daten** — speisen die Mischkultur-Graphkanten (REQ-028: `compatible_with` / `incompatible_with`), **nur aus dem OpenFarm-CC0-Dump**. REQ-028 §8 nennt REQ-011 explizit als automatische Anreicherungsquelle für diese Edges.

**Begründung niedrige/optionale Priorität:** Die Anbauzeitraum-Lücken sind laut Audit großteils geschlossen, und mit **GBIF + Perenual** existieren bereits zwei produktive Enrichment-Quellen (REQ-011). Dem marginalen Zusatznutzen steht **reale Lizenzreibung** gegenüber (OpenFarm-Server tot, Growstuff-ShareAlike kollidiert mit REQ-032). Deshalb ist REQ-040 als **optional/zurückgestellt** eingestuft.

**Abgrenzung:**

- **REQ-011** bleibt der architektonische Rahmen (ABC, Registry, Sync-Engine, `external_sources`/`external_mappings`/`sync_runs`, Lokale Hoheit, Provenienz). REQ-040 fügt nur den optionalen CC0-Dump-Import + Companion-Import (aus dem Dump) + Lizenz-Tracking hinzu — keinen Live-Adapter.
- **REQ-028** bleibt autoritativ für Edge-Modell, Scores, Effekt-Typen und Empfehlungs-Engine. REQ-040 *befüllt* diese Edges (aus dem OpenFarm-CC0-Dump), definiert sie nicht neu.
- **REQ-001** liefert die Ziel-Felder auf `Species`.
- **REQ-032** (Export/Druck) ist der load-bearing Grund, warum Growstuff-Werte nicht importiert werden (siehe §5.3).

### 1.1 Projekt-Steckbriefe

> **Wichtige Caveats vorab (verifiziert 2026-06, siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`):** Beide Quellen sind crowdsourced, lückenhaft und englischsprachig. **OpenFarm ist tot** — der Server ist seit **April 2025 abgeschaltet/archiviert** und die v1-API antwortet nur noch mit `301`-Redirect; ein Live-Abruf ist nicht mehr möglich, nutzbar ist nur ein **statischer CC0-Dump aus einem Mirror**. Growstuff ist zwar aktiver, seine **Daten stehen aber unter CC-BY-SA 3.0** — das erzwingt Attribution *und* Share-Alike (siehe §5.3), was mit REQ-032 kollidiert; daher werden **keine Growstuff-Werte importiert**, Growstuff dient nur als Mapping-Vorlage.

| Eigenschaft | **OpenFarm** (optionaler CC0-Dump) | **Growstuff** (nur Mapping-Vorlage) |
|---|---|---|
| Name | OpenFarm | Growstuff |
| URL / API | `https://openfarm.cc/` · API `https://openfarm.cc/api/v1/` — **abgeschaltet (4/2025), nur 301-Redirect** | `https://www.growstuff.org/` · API `https://www.growstuff.org/api/v1/` (OpenAPI 2.0) |
| Lizenz Code | MIT (Open Source, GitHub `openfarmcc/OpenFarm`) | AGPL-3.0 (Open Source, GitHub `Growstuff/growstuff`) — **irrelevant, da keine Code-/Daten-Übernahme** |
| Lizenz Daten | **CC0 / Public Domain** (keine Attributionspflicht) | **CC-BY-SA 3.0 Unported** (Attribution an `growstuff.org` + Share-Alike) |
| Sprache der Daten | Englisch | Englisch |
| Typ | Ehem. Crowdsourced DB + REST-API (JSON:API) — **nur noch als statischer Dump/Mirror verfügbar** | Crowdsourced Open-Data-DB + REST-API (JSON, auch CSV) |
| Datenfokus | Growing Guides, Crop-Stammdaten, Companion Plants | Crop-Stammdaten, Aussaat/Ernte-Crowdsourcing, Companion-Hinweise |
| Nutzung in REQ-040 | **Optionaler, einmaliger CC0-Dump-Import** (kein Live-Adapter) | **Nur Field-Mapping-Vorlage — kein Wertimport** |
| Reifegrad / Aktivität | **Abgeschaltet/archiviert** (Server tot seit 4/2025); Daten leben v. a. via FarmBot/Mirrors weiter | **Aktiv**, seit 2012, semantisch versioniert ab v1 |
| Rate-Limit | Entfällt (kein Live-Abruf) | Entfällt (kein Live-Abruf) |

**Konsequenz für die Architektur:** Wegen der unterschiedlichen Daten-Lizenzen führt REQ-040 ein **Lizenz-/Attribution-Tracking pro angereichertem Feld** ein (siehe §2.2). CC0-Daten (OpenFarm-Dump) brauchen keine Attribution; werden über das Tracking nur zu Transparenzzwecken als „via OpenFarm-Dump (CC0)" markiert. Growstuff-Felder tauchen in diesem Tracking **nicht** auf, weil keine Growstuff-Werte importiert werden — genau das hält die Wissensbasis CC-BY-SA-frei und vermeidet die REQ-032-Kollision (siehe §5.3).

## 2. Datenmodell-Erweiterung (ArangoDB)

REQ-040 nutzt die bestehenden Collections aus REQ-011 (`external_sources`, `external_mappings`, `sync_runs`) und erweitert sie additiv. **Nur OpenFarm** erhält einen `external_sources`-Eintrag — Growstuff wird nicht als Quelle geführt, da daraus keine Werte importiert werden.

### 2.1 Neuer `external_sources`-Eintrag (nur OpenFarm-CC0-Dump)

Ein neues Dokument in der bestehenden Collection (Schema unverändert gegenüber REQ-011, `license`/`attribution_required`-Felder ergänzt). Es markiert den **statischen CC0-Dump-Import**, keinen Live-Adapter (`auth_type`/`rate_limit` entfallen, `import_mode: "static_dump"`):

```json
{
  "_key": "openfarm",
  "name": "OpenFarm (statischer CC0-Dump)",
  "base_url": null,
  "import_mode": "static_dump",
  "rate_limit_per_day": null,
  "rate_limit_per_minute": null,
  "is_active": false,
  "priority": 6,
  "license": "CC0-1.0",
  "license_data_url": "https://github.com/openfarmcc/OpenFarm",
  "attribution_required": false,
  "attribution_text": null,
  "maintenance_status": "archived",
  "last_sync_at": null,
  "last_sync_status": null,
  "total_records_synced": 0
}
```

> **Kein Growstuff-Eintrag:** Growstuff wird bewusst **nicht** in `external_sources` registriert. Da REQ-040 keine Growstuff-Werte importiert (Entscheidung G2, §5.3), gibt es weder einen Adapter noch einen Sync-Lauf noch Provenance-Einträge für Growstuff. Der Eintrag bliebe sonst eine irreführende „aktive Quelle".

**Priorisierung in der Konflikt-Kette (REQ-011 §1.1):** OpenFarm (Prio 6) wird **nach** den bestehenden Quellen Perenual (1), GBIF (3) und Trefle (4) eingereiht. Damit bleibt die Lokale Hoheit gewahrt: Der Dump-Import füllt nur leere Felder automatisch (Confidence 0.9); bei belegten Feldern erzeugt er ausschließlich Vorschläge (Confidence 0.7), die im Admin akzeptiert werden müssen. `is_active` steht auf `false` — der Dump-Import wird bewusst manuell und einmalig durch den Admin ausgelöst, nicht periodisch.

### 2.2 Provenance-/Attribution-Erweiterung der `external_mappings`

Das bestehende `field_mappings`-Objekt aus REQ-011 wird pro Feld um Lizenz- und Attributionsangaben ergänzt (additiv, non-breaking). Es trägt **ausschließlich OpenFarm-CC0-Felder** — Growstuff erzeugt keine Mappings (kein Wertimport):

```json
{
  "_key": "species_42_openfarm_tomato",
  "internal_collection": "species",
  "internal_key": "42",
  "source_key": "openfarm",
  "external_id": "tomato",
  "field_mappings": {
    "harvest_months": {
      "external_value": [7, 8, 9],
      "mapped_at": "2026-06-19T03:15:00Z",
      "confidence": 0.9,
      "accepted": true,
      "license": "CC0-1.0",
      "attribution_required": false,
      "attribution_text": null
    }
  },
  "last_checked_at": "2026-06-19T03:15:00Z",
  "checksum": "sha256:def456..."
}
```

Für OpenFarm-Dump-Felder ist `attribution_required: false` und `license: "CC0-1.0"`. Diese Felder werden bei der Provenienz-Anzeige (§4) ohne Attributionszwang dargestellt, bleiben aber als „angereichert via OpenFarm-Dump (CC0)" gekennzeichnet. Das `attribution_required`/`attribution_text`-Schema bleibt dennoch im Modell, weil REQ-011 es generisch für alle Quellen vorsieht; für REQ-040 ist es bei OpenFarm immer `false`/`null`.

### 2.3 Companion-Import-Mapping (in den Graph, REQ-028)

Companion-Daten erzeugen **keine** Species-Felder, sondern Edges. Sie laufen daher über einen separaten Import-Pfad in die REQ-028-Edge-Collections (`compatible_with`, `incompatible_with`) des Named Graph `kamerplanter_graph`. **Companion-Edges stammen ausschließlich aus dem optionalen OpenFarm-CC0-Dump** — Growstuff-Companion-Hinweise werden nicht importiert (Entscheidung G2, §5.3). Jede importierte Edge trägt — gemäß REQ-028 Edge-Properties — `source` und zusätzlich Lizenz-Herkunft:

| REQ-028 Edge-Property | Befüllung durch REQ-040 |
|---|---|
| `compatibility_score` | Heuristik (siehe §3.4); Default 0.6 (general) |
| `effect_type` | Default `general` (Dump liefert keine differenzierten Effekt-Typen) |
| `description` | Freitext aus Dump, mit Quellen-Suffix („via OpenFarm-Dump") |
| `source` | `"openfarm"` (CC0) |
| `bidirectional` | `true` (Companion-Hinweise sind i. d. R. symmetrisch) |

Zur Idempotenz und Rückverfolgbarkeit wird zusätzlich ein Eintrag in `external_mappings` mit `internal_collection: "compatible_with"` (bzw. `incompatible_with`), `source_key: "openfarm"` und dem Edge-`_key` geschrieben. So bleibt der Checksum-Vergleich (REQ-011 §3.4) auch für Companion-Edges nutzbar.

**Wichtig (REQ-028 §2.4 Scoping):** Companion-Edges sind **globale Stammdaten**. Importierte Edges müssen mindestens eine Species-Auflösung auf beiden Seiten haben (beide Partner existieren lokal mit `scientific_name`-Match). Nicht auflösbare Companion-Hinweise werden als `skipped` protokolliert, nicht als neue Species angelegt.

### 2.4 AQL-Beispiel: aus dem OpenFarm-CC0-Dump importierte Companion-Edges

```aql
FOR em IN external_mappings
  FILTER em.internal_collection IN ["compatible_with", "incompatible_with"]
     AND em.source_key == "openfarm"
  RETURN {
    edge_key: em.internal_key,
    source: em.source_key,
    license: "CC0-1.0",
    attribution_required: false
  }
```

> Da REQ-040 keine CC-BY-SA-Daten importiert, ist `attribution_required` für alle REQ-040-Edges konstant `false`. Eine Attributions-Filterung wie in v1.0 ist nicht mehr nötig — die Wissensbasis bleibt CC-BY-SA-frei.

## 3. Technische Umsetzung (Python)

> **Kein Live-Adapter.** Die in v1.0 vorgesehenen Live-Adapter `OpenFarmAdapter` (Server tot, G3) und `GrowstuffAdapter` (CC-BY-SA, G2) entfallen. REQ-040 implementiert stattdessen **einen optionalen, einmaligen statischen CC0-Dump-Importer für OpenFarm** und behält das **Growstuff-Field-Mapping nur als Referenztabelle** (§3.2) ohne ausführbaren Adapter.

### 3.1 OpenFarm-CC0-Dump-Importer (kein Live-Adapter)

Der Importer liest einen lokal bereitgestellten **statischen CC0-Dump** (JSON-Fixture aus einem OpenFarm-Mirror, z. B. ein Snapshot des `openfarmcc/OpenFarm`-Repos). Es findet **kein** Netzwerk-Abruf gegen `openfarm.cc` statt — die API ist seit 4/2025 abgeschaltet (`301`-Redirect). Der Importer liefert `ExternalSpeciesData` (inkl. `companions`-Liste, im REQ-011-ABC bereits vorgesehen) und speist diese in die bestehende REQ-011-Confidence-Kette ein.

```python
import json
from pathlib import Path

from app.adapters.base import ExternalSpeciesData


class OpenFarmDumpImporter:
    """Einmaliger Importer für einen statischen OpenFarm-CC0-Dump (Mirror).

    Caveat (G3): Der OpenFarm-Server ist seit 4/2025 abgeschaltet — die
    v1-API antwortet nur noch mit 301. Es gibt deshalb KEINEN Live-Adapter;
    dieser Importer liest ausschließlich eine lokal bereitgestellte
    CC0-Dump-Datei. Datenqualität crowdsourced/lückenhaft, englisch.
    """

    source_key = "openfarm"

    def load_crops(self, dump_path: Path) -> list[ExternalSpeciesData]:
        """Liest den CC0-Dump und mappt jede Crop auf ExternalSpeciesData."""
        raw_crops = json.loads(dump_path.read_text(encoding="utf-8"))
        return [self._map_crop(item) for item in raw_crops]

    def _map_crop(self, raw: dict) -> ExternalSpeciesData:
        attrs = raw.get("attributes", raw)
        return ExternalSpeciesData(
            external_id=str(raw.get("id", attrs.get("slug", ""))),
            scientific_name=attrs.get("binomial_name"),
            common_names=attrs.get("common_names", [])
            or [n for n in [attrs.get("name")] if n],
            light_requirements_ppfd=self._map_sun(
                attrs.get("sun_requirements")
            ),
            companions=self._extract_companions(attrs),
            raw_data=raw,
        )

    @staticmethod
    def _map_sun(sun: str | None) -> int | None:
        mapping = {
            "Full Shade": 100,
            "Partial Shade": 200,
            "Partial Sun": 400,
            "Full Sun": 600,
        }
        return mapping.get(sun) if sun else None

    @staticmethod
    def _extract_companions(attrs: dict) -> list[str]:
        # Der Dump liefert Companion-Hinweise teils in Guides/Practices,
        # teils als 'companions'-Liste. Robust beide Quellen prüfen.
        comps = attrs.get("companions") or []
        return [c for c in comps if isinstance(c, str)]
```

**Field-Mapping OpenFarm-Dump → Species (REQ-001):**

| OpenFarm-Feld | Ziel `Species`-Feld | Verarbeitung |
|---|---|---|
| `binomial_name` | `scientific_name` | direkt (Match-Schlüssel) |
| `common_names`, `name` | `common_names` | Liste, englisch (Sprach-Caveat §5) |
| `sun_requirements` | `light_requirements_ppfd` | Enum→PPFD-Heuristik (`_map_sun`) |
| `sowing_method` | `propagation_notes` (Freitext) | nur falls leer (Auto-Accept) |
| `spread`, `row_spacing` | `planting_distance_cm` | numerisch, cm |
| `days_to_maturity` | `days_to_maturity` | numerisch |
| `companions` / Guides | → Companion-Import (§3.4) | **nicht** Species-Feld |

### 3.2 Growstuff-Field-Mapping (nur Referenz/Vorlage — kein Adapter)

> **Kein ausführbarer Adapter.** Aus Growstuff werden **keine Werte importiert** (Entscheidung G2). Der folgende Mapping-Entwurf bleibt erhalten, weil er als **konzeptionelle Vorlage** nützlich ist (welche Growstuff-Felder fachlich auf welche `Species`-Felder abbilden würden) — z. B. falls künftig eine lizenzkonforme, isolierte Quelle gewünscht wird. Es existiert bewusst **keine** `GrowstuffAdapter`-Klasse, kein `@AdapterRegistry.register`, kein `external_sources`-Eintrag und kein Sync-Lauf für Growstuff. Damit bleibt die gesamte Wissensbasis frei von CC-BY-SA-Bindung und kollidiert nicht mit den Export-/Druckansichten aus REQ-032 (§5.3).

**Field-Mapping Growstuff → Species (REQ-001) — REINE REFERENZ, NICHT IMPLEMENTIERT:**

| Growstuff-Feld | Hypothetisches Ziel `Species`-Feld | Hinweis |
|---|---|---|
| `scientific_names[0]` / `scientific_name` | `scientific_name` | Match-Schlüssel — wäre sprachneutral |
| `name` | `common_names` | englisch (Sprach-Caveat §5) |
| `perennial` | `lifecycle.cycle_type` | Bool→Enum (`perennial`/`annual`) |
| aggregierte Planting-Daten | `sowing_*_months` | Monats-Histogramm aus Crowdsourcing |
| aggregierte Harvest-Daten | `harvest_months` | Monats-Histogramm aus Crowdsourcing |
| `companions` / parent/sibling | (Companion-Idee) | dient nur als Mapping-Inspiration |

> **Lizenz-Grund (load-bearing):** Würde auch nur ein Growstuff-Wert übernommen, gälte die abgeleitete Daten-Sammlung als CC-BY-SA-„Adaptation" und zöge ShareAlike + Attribution auf jeden Export/Druck (REQ-032). Deshalb endet die Growstuff-Nutzung hier bei der Mapping-Tabelle — kein Code, keine Daten.

### 3.3 Registrierung in der bestehenden Kette

Es wird **kein** Live-Adapter registriert. Der OpenFarm-CC0-Dump-Import läuft **nicht** über den periodischen `enrichment.sync_all`-Task (REQ-011 §3.5), sondern wird **einmalig und manuell** durch den Admin ausgelöst (§4.2). Die in die Confidence-Kette eingespeisten `ExternalSpeciesData` durchlaufen dabei dieselbe REQ-011-Konflikt-/Confidence-Logik (Auto-Accept 0.9 / Propose-only 0.7), aber nicht den Registry-Iterations-Pfad. Growstuff ist gar nicht registriert (§3.2).

### 3.4 Companion-Graph-Import (separater Pfad, nur aus OpenFarm-Dump)

Da Companion-Daten Edges statt Felder erzeugen, ergänzt REQ-040 eine Methode in einem `CompanionImportService`, der die REQ-028-Edge-Repositories nutzt. Er läuft **nach** dem OpenFarm-Dump-Species-Import (Species müssen existieren, damit beide Partner auflösbar sind) und verarbeitet **ausschließlich `source_key="openfarm"`** (CC0). Growstuff-Companion-Hinweise werden nicht importiert.

```python
import structlog

logger = structlog.get_logger()

# Heuristischer Default-Score (Dump liefert keine validierten Scores)
OPENFARM_DEFAULT_SCORE = 0.6


class CompanionImportService:
    """Importiert OpenFarm-CC0-Companion-Hinweise als REQ-028-Edges."""

    def __init__(self, species_repo, companion_edge_repo, mapping_repo) -> None:
        self._species_repo = species_repo
        self._edge_repo = companion_edge_repo      # REQ-028 compatible_with/incompatible_with
        self._mapping_repo = mapping_repo

    async def import_companions(
        self, external_data: ExternalSpeciesData
    ) -> tuple[int, int]:
        """Erzeugt compatible_with-Edges für aufgelöste Companion-Partner.

        Nur für den OpenFarm-CC0-Dump (source_key fest "openfarm").
        Returns: (created, skipped)
        """
        primary = await self._species_repo.find_by_scientific_name(
            external_data.scientific_name
        )
        if not primary:
            return 0, len(external_data.companions)

        created = skipped = 0

        for partner_name in external_data.companions:
            partner = await self._species_repo.find_by_common_or_scientific(
                partner_name
            )
            if not partner:
                skipped += 1  # nicht auflösbar -> kein Species-Anlegen (§2.3)
                continue

            edge_key = await self._edge_repo.upsert_compatible(
                from_key=primary["_key"],
                to_key=partner["_key"],
                compatibility_score=OPENFARM_DEFAULT_SCORE,
                effect_type="general",
                description=f"{partner_name} (via OpenFarm-Dump)",
                source="openfarm",
                bidirectional=True,
            )
            await self._mapping_repo.upsert(
                internal_collection="compatible_with",
                internal_key=edge_key,
                source_key="openfarm",
                external_id=external_data.external_id,
                field_mappings={
                    "edge": {
                        "external_value": partner_name,
                        "license": "CC0-1.0",
                        "attribution_required": False,
                    }
                },
                checksum=None,
            )
            created += 1

        logger.info(
            "companion_import",
            source="openfarm",
            primary=external_data.scientific_name,
            created=created,
            skipped=skipped,
        )
        return created, skipped
```

**Wichtig:** Importierte Companion-Edges erhalten bewusst nur `effect_type: general` und einen konservativen Score (0.6), da der Dump keine differenzierten Effekt-Typen oder validierten Scores liefert. Kuratierte Seed-Daten (REQ-028 §6) und Admin-Edits behalten Vorrang — ein bestehender Edge mit höherem Score wird durch den Import **nicht** herabgestuft (Upsert prüft `compatibility_score` und überschreibt nur nach unten nicht).

### 3.5 Auslösung (kein Celery-Beat)

Es wird **kein** Beat-Eintrag angelegt: Der OpenFarm-CC0-Dump ist ein **einmaliger, manuell ausgelöster** Import, keine periodische Quelle. Ein leichtgewichtiger, manuell dispatchter Task liest den Dump und triggert anschließend den Companion-Import:

```python
from celery import shared_task


@shared_task(name="enrichment.import_openfarm_dump")
def import_openfarm_dump_task(dump_path: str) -> dict:
    """Einmaliger Import des statischen OpenFarm-CC0-Dumps (manuell)."""
    import asyncio
    from pathlib import Path
    from app.dependencies import (
        get_companion_import_service,
        get_openfarm_dump_importer,
    )

    importer = get_openfarm_dump_importer()
    service = get_companion_import_service()
    crops = importer.load_crops(Path(dump_path))
    return asyncio.run(_run_openfarm_dump_import(crops, service))
```

> **Kein wiederkehrender Schedule.** Da der OpenFarm-Server tot ist, gibt es nichts periodisch zu synchronisieren. Der Task wird ausschließlich on-demand via Admin-Aktion (§4.2) gestartet.

## 4. Frontend-Integration

React 19 / TS 5.9 / MUI 7, i18n DE/EN. REQ-040 erweitert die bestehende Enrichment-Admin-Ansicht (REQ-011) additiv — keine neuen Seiten.

### 4.1 Quellen-/Attribution-Anzeige

- In der Provenienz-Ansicht einer Species (`/species/{key}/enrichments`) zeigen die aus dem OpenFarm-CC0-Dump stammenden Felder ein neutrales „OpenFarm-Dump (CC0)"-Badge ohne Lizenz-/Attributionszwang.
- Companion-Empfehlungen (REQ-028 UI §7) zeigen bei extern importierten Edges ein dezentes Herkunfts-Tag („via OpenFarm-Dump").
- **Kein Growstuff-Badge:** Da keine Growstuff-Werte importiert werden, erscheint Growstuff nirgends in der Provenienz-Anzeige. Ein CC-BY-SA-Lizenz-Badge wird nicht benötigt.

### 4.2 Enrichment-Admin

- Die bestehende Quellen-Liste (REQ-011) zeigt OpenFarm mit `maintenance_status: "archived"`-Badge („Archiviert — nur statischer CC0-Dump") als Transparenzhinweis; die Quelle ist standardmäßig `is_active: false`.
- Auslösung des **einmaligen Dump-Imports** über einen dedizierten Admin-Button „OpenFarm-CC0-Dump importieren" (lädt die bereitgestellte Dump-Datei). Kein periodischer Sync-Button, da keine Live-Quelle.
- Accept/Reject von Propose-only-Feldern nutzt den bestehenden `/accept`-Endpunkt (REQ-011 §3.7).

### 4.3 i18n-Keys (Auswahl)

```
enrichment.source.openfarm = "OpenFarm (CC0-Dump)" / "OpenFarm (CC0 dump)"
enrichment.license.cc0 = "Lizenz: Public Domain (CC0)" / "License: Public Domain (CC0)"
enrichment.maintenance.archived = "Archiviert — nur statischer CC0-Dump" / "Archived — static CC0 dump only"
enrichment.companion.imported = "Importiert via {source}" / "Imported via {source}"
enrichment.action.importDump = "OpenFarm-CC0-Dump importieren" / "Import OpenFarm CC0 dump"
```

## 5. Konfiguration, Deployment & Lizenz

### 5.1 Konfiguration

| Einstellung | Wert / Quelle |
|---|---|
| OpenFarm-Live-API | **entfällt** — Server seit 4/2025 abgeschaltet (`301`), kein Netzwerk-Abruf |
| OpenFarm-Dump-Pfad | Pfad zur lokal bereitgestellten CC0-Dump-Datei (env `OPENFARM_DUMP_PATH`, optional) |
| Growstuff | **keine Konfiguration** — kein Adapter, kein Abruf (G2) |
| Feature-Flag | `ENRICHMENT_OPENFARM_DUMP_ENABLED` (Default: `false`) — der Dump-Import ist standardmäßig aus |

Es werden keine API-Keys benötigt: OpenFarm wird offline aus einem Dump gelesen, Growstuff gar nicht abgerufen.

### 5.2 Robustheit des Dump-Imports

- Es gibt keine Live-Abrufe und damit keine Rate-Limits, Timeouts oder Retries gegen externe Server.
- Fehlt die Dump-Datei oder ist sie unlesbar/korrupt, bricht **nur** der manuell ausgelöste Import ab (mit klarer Fehlermeldung); die bestehende Wissensbasis und die produktiven Quellen GBIF/Perenual (REQ-011) bleiben unberührt.
- Da der Import einmalig und idempotent (Upsert/Checksum) ist, kann er nach Korrektur der Dump-Datei gefahrlos wiederholt werden.

### 5.3 Lizenz-Handling: warum CC0-Dump ja, Growstuff nein (load-bearing)

**OpenFarm (CC0 / Public Domain):** Keine Attributionspflicht, keine Share-Alike-Bindung. Felder aus dem CC0-Dump werden ohne Lizenz-Auflagen übernommen; die Herkunft wird nur zu Transparenzzwecken getrackt (§2.2). Der Re-Export/Druck (REQ-032) ist unproblematisch.

**Growstuff (CC-BY-SA 3.0) — bewusst NICHT importiert:** CC-BY-SA erzeugt zwei Pflichten, die mit dem Export-/Druck-Konzept aus REQ-032 kollidieren:

1. **Attribution:** Jeder übernommene Wert müsste „Data from Growstuff (growstuff.org), CC-BY-SA 3.0" mitführen — in jeder Export- und Druckansicht (REQ-032).
2. **Share-Alike (der eigentliche Knackpunkt):** CC-BY-SA verlangt, dass *abgeleitete, weiterverbreitete* Sammlungen unter einer kompatiblen Lizenz stehen. Verschmilzt man Growstuff-Felder mit den eigenen Species-Daten, gilt die **gesamte abgeleitete Daten-Sammlung** als „Adaptation" und würde CC-BY-SA „durchschlagen" lassen — das bindet **jeden** Export/Druck (Kollision mit REQ-032) und wäre mit Kamerplanters MIT-Outbound nicht sauber vereinbar.

> **Design-Entscheidung (G2):** Statt Growstuff-Daten aufwendig per-Feld zu isolieren und einen Share-Alike-Export-Filter zu bauen, werden **gar keine Growstuff-Werte übernommen**. Growstuff dient ausschließlich als **Mapping-/Ideen-Vorlage** (§3.2). So bleibt die Wissensbasis **vollständig CC-BY-SA-frei** und die REQ-032-Export-/Druckansichten bleiben uneingeschränkt nutzbar — ohne Attributions- oder ShareAlike-Caveat. Details siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md` (REQ-040-Abschnitt).

### 5.4 Sprach-Mapping (englische Daten)

Der OpenFarm-CC0-Dump liefert englische Common-Names und Freitexte. Konsequenzen:

- `scientific_name` ist sprachneutral und dient als primärer Match-Schlüssel (robust).
- Englische `common_names` werden nicht in `common_name_de` geschrieben, sondern in die sprachneutrale `common_names`-Liste; eine DE-Übersetzung bleibt manuell/kuratiert (kein automatisches Übersetzen, um Falschzuordnungen zu vermeiden).
- Companion-Auflösung erfolgt bevorzugt über `scientific_name`; nur als Fallback über englische Common-Names (`find_by_common_or_scientific`), was die `skipped`-Quote erhöhen kann (akzeptiert, da konservativ).

### 5.5 Consent (REQ-025)

Externe Anreicherung ist in REQ-025 eine **optionale Verarbeitung** (Consent „enrichment"). Der OpenFarm-CC0-Dump-Import fügt keine personenbezogenen Daten hinzu (rein botanische Daten) und läuft innerhalb desselben Consent-Gates wie REQ-011. Da der Import global und admin-getrieben ist und Companion-Edges global sind, betrifft Consent hier nur die Sichtbarkeit/Nutzung im jeweiligen Tenant, nicht den globalen Seed-/Dump-Import.

### 5.6 Offline-Fallback

- Ohne Netzwerkzugang (z. B. Light-Modus / On-Prem ohne Internet) funktioniert die Wissensbasis vollständig aus Seed-Daten (REQ-001/REQ-028 §6).
- Der OpenFarm-CC0-Dump ist ohnehin eine **lokale JSON-Fixture** und damit von Haus aus offline-tauglich und lizenzrechtlich unkritisch. Growstuff-Snapshots werden bewusst **nicht** mitgeliefert (kein CC-BY-SA-Material in der Auslieferung).

## 6. Abhängigkeiten

**Benötigt:**
- **REQ-011** — Collections `external_sources`/`external_mappings`/`sync_runs`, Konflikt-/Confidence-Logik. REQ-040 ergänzt ausschließlich additiv (CC0-Dump-Import statt Live-Adapter).
- **REQ-028** — Edge-Collections `compatible_with`/`incompatible_with`, Edge-Properties, Companion-Edge-Repository. REQ-040 befüllt diese aus dem OpenFarm-CC0-Dump.
- **REQ-001** — Ziel-Felder auf `Species` (`scientific_name`, `common_names`, Anbauzeiträume, Pflege).
- **REQ-025** — Consent-Gate „enrichment".

**Systemabhängigkeiten:**
- ArangoDB (Mappings, Edges), Redis + Celery (manuell ausgelöster Dump-Import-Task). Kein httpx/Live-HTTP nötig.

**Wird benötigt von:**
- **REQ-028** — profitiert von zusätzlichen Companion-Edges (aus dem CC0-Dump) für Arten ohne kuratierte Seed-Daten.
- **REQ-015 / REQ-006** — angereicherte Anbauzeiträume verbessern Aussaat-/Erntekalender (marginaler Zusatznutzen, da Audit-Lücken weitgehend geschlossen).

> **Keine REQ-032-Bindung:** Da keine CC-BY-SA-Daten importiert werden, muss der Export/Druck (REQ-032) **keine** Growstuff-Attribution mitführen — genau das ist das Ziel von Entscheidung G2 (§5.3).

**Externe Abhängigkeiten:**
- OpenFarm-CC0-Dump (Mirror/Snapshot des `openfarmcc/OpenFarm`-Repos) — **Server tot (4/2025)**, nur statischer Dump, kein Live-Endpunkt.
- Growstuff — **keine** externe Abhängigkeit (kein Abruf; nur Mapping-Vorlage).

## 7. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **`OpenFarmDumpImporter`** liest einen lokalen CC0-Dump (kein Netzwerk-Abruf), mit Field-Mapping gemäß §3.1.
- [ ] **Kein Growstuff-Adapter und kein Growstuff-Import:** Growstuff bleibt reine Mapping-Referenz (§3.2); keine `GrowstuffAdapter`-Klasse, kein `external_sources`-Eintrag, keine Growstuff-Werte in der DB.
- [ ] **Kein Live-Adapter / kein Beat:** Der Dump-Import wird einmalig manuell ausgelöst, nicht via `enrichment.sync_all` oder Celery-Beat.
- [ ] **`external_sources`-Eintrag** nur für `openfarm` (CC0, `import_mode: "static_dump"`, `is_active: false`, `maintenance_status: "archived"`).
- [ ] **Per-Feld-Lizenz-Tracking:** `external_mappings.field_mappings` trägt für OpenFarm-Felder `license: "CC0-1.0"` + `attribution_required: false`.
- [ ] **Lokale Hoheit gewahrt:** Leere Felder Auto-Accept (0.9), belegte Felder Propose-only (0.7), Prio 6 nach bestehenden Quellen.
- [ ] **Companion-Import** erzeugt REQ-028-`compatible_with`-Edges (nur aus OpenFarm-Dump) nur für beidseitig auflösbare Partner; nicht auflösbare → `skipped` (kein Species-Anlegen).
- [ ] **Kuratierte Edges geschützt:** Import stuft bestehende, höher bewertete Companion-Edges nicht herab.
- [ ] **Idempotenz:** Wiederholter Dump-Import erzeugt identische Ergebnisse (Checksum/Upsert).
- [ ] **Robustheit:** Fehlende/korrupte Dump-Datei bricht nur den Import ab, nicht die bestehende Wissensbasis.
- [ ] **Consent-Gate:** Bei fehlendem Consent „enrichment" wird der Import pro Tenant nicht angewendet.
- [ ] **Frontend:** OpenFarm-CC0-Badge + Companion-Herkunftstag sichtbar, Admin-Button „CC0-Dump importieren"; i18n DE/EN. **Kein** Growstuff-/CC-BY-SA-Badge.
- [ ] **CC-BY-SA-Freiheit:** Die Wissensbasis enthält keine Growstuff-Werte; Export/Druck (REQ-032) braucht keine Growstuff-Attribution.
- [ ] **Tests:** Unit-Tests für `OpenFarmDumpImporter` mit gemockter Dump-Fixture; Companion-Import-Test (auflösbar/skip/Schutz bestehender Edges).

### Testszenarien:

**Szenario 1: Anbauzeitraum-Lücke via OpenFarm-CC0-Dump schließen**
```
GIVEN: Species "Solanum lycopersicum" ohne harvest_months
WHEN: OpenFarm-CC0-Dump liefert harvest_months = [7, 8, 9]
THEN:
  - Feld auto-akzeptiert (confidence 0.9)
  - external_mappings trägt license "CC0-1.0", attribution_required false
```

**Szenario 2: Companion-Edge-Import (auflösbar, aus CC0-Dump)**
```
GIVEN: "Daucus carota" und "Allium cepa" existieren lokal
WHEN: OpenFarm-CC0-Dump liefert companions=["onion"] für carrot
THEN:
  - compatible_with-Edge (bidirectional, score 0.6, effect_type general) erstellt
  - source = "openfarm", external_mappings-Eintrag (CC0) für die Edge angelegt
```

**Szenario 3: Companion-Hinweis nicht auflösbar**
```
GIVEN: Companion "marshmallow" hat kein lokales Species-Match
WHEN: Import läuft
THEN:
  - keine Species angelegt, keine Edge erstellt
  - als skipped protokolliert
```

**Szenario 4: Kuratierte Edge geschützt**
```
GIVEN: compatible_with (Tomate↔Basilikum) aus REQ-028-Seed mit score 0.9
WHEN: OpenFarm-CC0-Dump-Import liefert dieselbe Relation (Default 0.6)
THEN:
  - bestehender Score 0.9 bleibt erhalten (kein Downgrade)
  - source-Provenienz wird ergänzt, nicht überschrieben
```

**Szenario 5: Keine Growstuff-Werte in der Wissensbasis (CC-BY-SA-Freiheit)**
```
GIVEN: REQ-040 ist implementiert (nur OpenFarm-CC0-Dump + Growstuff-Mapping-Vorlage)
WHEN: Die DB nach Quellen-Provenienz durchsucht wird
THEN:
  - kein external_mappings-Eintrag mit source_key "growstuff"
  - kein external_sources-Dokument "growstuff"
  - Export/Druck (REQ-032) führt keine CC-BY-SA-Attribution
```

**Szenario 6: Fehlende/korrupte Dump-Datei**
```
GIVEN: OPENFARM_DUMP_PATH zeigt auf eine fehlende oder unlesbare Datei
WHEN: der manuelle Dump-Import ausgelöst wird
THEN:
  - der Import bricht mit klarer Fehlermeldung ab
  - bestehende Stammdaten + Quellen GBIF/Perenual unverändert
  - nach Korrektur ist ein idempotenter Wiederholungslauf möglich
```

**Szenario 7: Consent fehlt**
```
GIVEN: Tenant hat Consent "enrichment" nicht erteilt
WHEN: der OpenFarm-CC0-Dump-Import läuft
THEN:
  - die Anreicherung wird für diesen Tenant nicht angewendet
```

---

**Hinweise für RAG-Integration:**
- Keywords: OpenFarm, Growstuff, CC0-Dump, Companion-Import, CC-BY-SA, CC0, Share-Alike, Mapping-Vorlage, Anbauzeiträume, awesome-agriculture, optional/zurückgestellt
- Fachbegriffe: statischer CC0-Dump-Import, Datenprovenienz, Per-Feld-Lizenz-Tracking, ShareAlike-Konflikt, Idempotenz, kein Live-Adapter
- Caveats: OpenFarm-Server tot seit 4/2025 (nur statischer CC0-Dump, kein Live-Adapter), Growstuff CC-BY-SA → nur Mapping-Vorlage (kein Wertimport, kollidiert sonst mit REQ-032), englische Quelldaten (Sprach-Mapping), niedrige Priorität (Audit-Lücken weitgehend geschlossen, GBIF+Perenual vorhanden)
- Verknüpfung: ergänzt REQ-011 (Confidence-Kette/Mappings), befüllt REQ-028 (Companion-Edges aus CC0-Dump), nutzt REQ-001 (Species-Felder), REQ-025 (Consent); KEINE REQ-032-Attribution nötig (G2). Lizenzbasis: `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`
