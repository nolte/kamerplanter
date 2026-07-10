# Pre-Analysis — Issue #436

> Orchestriert via `nolte-shared:issue-orchestrate` (Spec: `claude-shared/spec/project/issue-orchestration/`).
> Maschinenlesbare Audit-Felder (classification, subagent_type, source) bleiben Englisch (grep-bar); Prosa Deutsch (Issue-Sprache).

## Issue-Metadaten

| Feld | Wert |
|---|---|
| number | 436 |
| title | fix(species): photo identification creates duplicate species — no scientific_name normalization (× vs x) |
| url | https://github.com/nolte/kamerplanter/issues/436 |
| state | OPEN |
| labels | `bug`, `backend` |
| milestone | — |
| linked PRs | keine |
| prior art | kein offener PR/Branch; **Wiederverwendung:** `photo_quality_assessor._normalize` (Backend) normalisiert bereits scientific_names |

## Klassifikation

- **primary_class:** `bug` — gemeldeter Prod-Defekt: Duplikat-Spezies durch fehlende `scientific_name`-Normalisierung.
- **secondary_class:** `spec-change` (REQ-Dokument mit Ausbaustufen, vom Operator angefordert) · `feature-request` (interaktive Disambiguierung + Merk-Store).
- **Rationale:** Das treibende Outcome ist der Bugfix; die Spec-Formalisierung und das interaktive Feature sind sekundäre Dimensionen.
- **Klassifikations-Bestätigung (spec-change/security-Pflicht):** wird mit der Freigabe dieses Artefakts durch den Operator bestätigt (spec-change vorhanden → explizite Bestätigung erforderlich).

## Requirements-Gate

- **Status:** erfüllt. Kein `project/requirements/`-Artefakt bei τ_high existierte → Operator wählte **requirements-elicit zuerst**.
- **Artefakt:** `project/requirements/species-scientific-name-normalization.md` — `U_gate = 0.82` (≥ τ_high 0.8), Saturation, 12 confirmed Requirements (R1–R7 Bugfix, R8–R12 Feature), 5 benannte Restrisiken.
- Jedes Arbeitspaket unten spurt auf dieses Artefakt (nicht auf rohe Issue-Prosa).

## In-/Out-of-Scope

**In scope (dieser PR — direkte Umsetzung, Split-Route):**
- REQ-Spec-Dokument mit explizit formulierten **Ausbaustufen** (Operator-Anforderung).
- Stufe-1-Verhalten: kanonische `scientific_name`-Normalisierung, persistenter `scientific_name_normalized`-Key, beide Dedup-Pfade idempotent, Backfill-Migration (Fragaria-Paar), Unit-Tests.

**Out of scope (→ formale Pipeline, `feature-decompose`/`roadmap-plan`):**
- Stufe-2/3-Umsetzung: interaktiver Disambiguierungs-Dialog, tenant-lokaler Merk-Store, Ähnlichkeits-Kandidaten-Ranking, Frontend.
- Stufe 4: vollautomatische Fuzzy-Taxonomie (Autoren-Zitate, `subsp.`/`var.`, Synonym-Graphen).

## Ausbaustufen (Kern der Operator-Anforderung → wird in WP1 als REQ formalisiert)

| Stufe | Inhalt | Route |
|---|---|---|
| **0 (Ist/Bug)** | Strikter AQL-`==`-Vergleich → Duplikate (`×` vs `x`) | — (Problem) |
| **1 (Bugfix, dieser PR)** | Kanonische Normalisierung + persistenter Key + idempotentes `create_species` + Backfill-Migration; Exakt-nach-Normalisierung = Auto-Accept | **direkt** |
| **2 (Feature)** | User-in-the-Loop-Disambiguierung bei nicht-exaktem Match + Ähnlichkeits-Kandidaten (simple String-Distanz) | **Pipeline** |
| **3 (Feature)** | Tenant-lokaler Merk-Store (gemerkte Entscheidung, Re-Apply, „keep new") | **Pipeline** |
| **4 (Zukunft)** | Vollautomatische Fuzzy-Taxonomie | out of scope |

## Route-Entscheidung (operator-bestätigt)

- **SPLIT.** Stufe 0→1 direkt als **ein PR-Strang**; Stufe 2–4 an die formale Pipeline. Keine Vermischung: der Feature-Rest wird **explizit** über `feature-decompose`/`roadmap-plan` geplant (nicht still zurückgelassen).
- Begründung *bounded* für Teil 1: ein kohärentes Outcome („Spezies-Identitätsauflösung: Spec + Stufe-1-Implementierung"), ein Feature-Branch, kein neues Roadmap-Item nötig für die direkte Umsetzung.

## Arbeitspakete (DAG)

| ID | Problemstellung | Acceptance Criteria | Berührte Artefakte | Specialist (`subagent_type`/skill) | Deps |
|---|---|---|---|---|---|
| **WP1** | REQ-Spec-Dokument authoren, das das Spezies-Identitätsauflösungs-Verhalten inkl. der 4 **Ausbaustufen** formalisiert; als neue REQ (Vorschlag REQ-048) oder Erweiterung von REQ-029 §1.2 — Placement entscheidet die `spec`-Skill via Dedup/Drift-Check. Cross-Link REQ-029, REQ-001, REQ-024. | Dok existiert unter `spec/req/`; enthält die 4 Ausbaustufen mit klarer Stufen-Abgrenzung + Akzeptanzkriterien je Stufe; verlinkt REQ-029/001/024; DE-kanonisch (+ EN-Mirror falls Konvention). | `spec/req/REQ-0XX_*.md` (+ ggf. EN-Mirror), REQ-Index | `nolte-shared:spec` | — |
| **WP2** | Stufe-1-Backend: zentrale Normalisierungs-Utility (`×`↔`x` inkl. Genus-Prefix, `casefold`, Whitespace-Collapse, strip); `scientific_name_normalized` am Species-Model (populate on create/update); beide Dedup-Pfade (`_match_candidates`, `create_species`) über den normalisierten Key; `create_species` **idempotent** (löst auf bestehende Spezies auf); `photo_quality_assessor._normalize` auf die Utility refaktorieren. Original-Display-Name unangetastet. | R1–R5 erfüllt; `Fragaria × ananassa` matcht `Fragaria x ananassa` (kein neues Insert); `create_species` gibt bestehende Spezies zurück statt Duplikat/Fehler; Display-Spelling bleibt. Unit-Tests grün. | `app/domain/models/species.py`, `app/domain/engines/identification_engine.py`, `app/domain/services/species_service.py`, `app/data_access/arango/species_repository.py`, neue `app/domain/…/normalization`-Util, `app/domain/engines/photo_quality_assessor.py`, Tests unter `src/backend/tests/` | `fullstack-developer` | WP1 |
| **WP3** | Einmalige Backfill-Migration im versionierten Framework: `scientific_name_normalized` für Bestands-Spezies befüllen; das beobachtete `Fragaria × / x ananassa`-Paar reconcilen — Zeile mit aktiven Pflanzen + reicherer Metadaten (family, cultivars) behalten. | R6 erfüllt; Migration unter `app.migrations`/`schema_migrations`; idempotent; Fragaria-Paar reconciled; Test/Trockenlauf belegt. | `src/backend/app/migrations/…`, Migrations-Test | `fullstack-developer` | WP2 |
| **WP4** | Verify + PR: `quality-gate` grün; PR via `pull-request-create` mit `Closes #436` und Risk/rollout-Notes (Klassifikation + je WP der Specialist). | Gate grün; PR offen, Issue verlinkt, Notes vollständig. | — | `nolte-engineering:quality-gate` → `nolte-shared:pull-request-create` | WP1, WP2, WP3 |
| **RT** (Routing, kein Dispatch jetzt) | Stufe 2–4 (interaktive Disambiguierung, tenant-lokaler Merk-Store, Ranking, Frontend) formal planen, grounded in REQ-0XX (WP1) + Elicitation-Artefakt. | Roadmap-Item/Features existieren; keine stille Nicht-Planung. | `project/roadmap.md`, `project/features/` | `nolte-shared:roadmap-plan` → `feature-decompose` | nach WP1 |

## Risiken

- **R-A (Cross-Tenant, Stufe 2/3):** Merk-Store + Kandidatenliste müssen strikt tenant-scoped sein (SEC-001-Muster). Harter Test im Feature-Work.
- **R-B (`casefold` am Key):** sicher, da Display-Name erhalten (R3); Key nie angezeigt. Verifizieren, dass kein Pfad den normalisierten Key rendert.
- **R-C (Migration auf Alt-Volumes):** Reconcile darf keine aktiven Pflanzen-Kanten verwaisen lassen; Zeilenwahl nach aktiven Pflanzen + Metadaten-Reichtum.
- **R-D (Doppelte Normalisierung):** WP2 muss `photo_quality_assessor._normalize` konsolidieren, nicht eine zweite parallele Implementierung schaffen.

## Offene Fragen

- WP1: Neue REQ-048 vs. Erweiterung REQ-029 §1.2 — final durch `spec`-Skill (Dedup/Drift). Empfehlung: neue REQ-048, da eigenständige, cross-cutting Fähigkeit („Spezies-Identitätsauflösung") mit eigenen Ausbaustufen.
- WP4: Ein PR für WP1–WP3 (Spec + Stufe-1-Code + Migration) — Default „ein PR-Strang je Issue".

## Audit-Trail

- worktree: `/home/nolte/repos/.worktrees/kamerplanter/species-dedup` · branch: `fix/species-scientific-name-normalization` (← origin/develop)
- resume: `.resume/issue-orchestrate/436-species-dedup.yml`
