---
plan-type: implementation-plan
title: N-Sprachen-i18n Rollout (Locale-keyed Content-Modell, eine Locale-Resolution)
epic: i18n-nlanguage
covers: [P1-content-model, P2-error-language, P3-consistency, RAG-language, RTL-foundation]
source-issue: 568
source-concept: spec/analysis/i18n-implementation-concept.md
source-capture: spec/analysis/i18n-current-state-capture.md
governing-nfr: spec/nfr/NFR-017_Skalierbare-Mehrsprachigkeit.md
status: ready
created: 2026-07-12
verified-against: develop (Worktree 2026-07-12)
parallelizable: partial
migration-queue: v0019 belegt (actuator_collections) → nächste frei v0020
specialist: fullstack-developer + seed-data pipeline agents + ha/knowledge-service
---

# N-Sprachen-i18n Rollout

## Ziel

Überführung des gespaltenen i18n-Zustands (Per-Sprache-Attribut vs. Locale-Map) in **ein** skalierbares
Modell gemäß NFR-017: ein `LocalizedText`-Content-Modell, eine Locale-Resolution mit einer Fallback-Kette,
Enums als Wert+Katalog, technische Fehler English-only / nutzerseitige Meldungen katalogisierbar, eine
sprachgesteuerte RAG-Strategie, ein RTL-Fundament.

**Nicht Teil dieses Plans (Non-Goals #568):** die tatsächlichen Übersetzungsinhalte, die Wahl der
Launch-Sprachen. Der Plan liefert den *Mechanismus*, sodass jede weitere Sprache additive Datenarbeit ist.

## Leitprinzipien der Umsetzung

- **Additiv, kein Big-Bang.** Loader und Resolver lesen im Übergangsfenster **beide** Formen
  (`common_name` **und** `common_name_de`), damit keine Migration einen Consumer bricht.
- **Migrations-Queue-Awareness:** Die Backfill-Migration claimt die nächste freie Version **v0020**
  (v0019 = `actuator_collections` ist belegt) nach dem claim-at-merge-Prinzip; bei Kollision auf
  v0021 hochziehen.
- **Ein Typ, ein Resolver pro Layer** (DRY): `common/i18n.py` (BE) und `utils/i18n.ts` (FE) sind die
  einzigen Fallback-Implementierungen.
- **Schreibende Agenten auf geteiltem Tree sequenziell** bzw. in Worktrees (Feedback
  `parallel_agents_shared_tree`).

## Ist-Anker (verifiziert 2026-07-12)

| Fläche | Anti-Pattern | Zielmuster vorhanden |
|--------|--------------|----------------------|
| Seed | 784 Suffix-Vork./15 Dateien, 6 Schemas | `glossary_terms`, `starter_kits` (150 Map-Inst.) |
| Backend | 141 `_de`/`_en`-Felder, 72 `language="de"`-Params, ~10 DE-Fehler-Literale | `error_code`-Katalog (36), glossary-Resolver |
| Frontend | 246 Feldzugriffe, ~76 Zweige, 45 Locale-Literale, 519 inline Enum-`t()`, RTL=0 | i18next-Katalog (~5368), Plurals |
| RAG/KI | DE-only Wissensbasis, DE/EN-Prompt-Dicts, `Literal["de","en"]` | multilinguales Embedding, `language`-Spalte |

---

## Phasen & Priorisierung

Priorität: **P0 = Fundament (blockiert alles)** → **P1 = größter Anti-Pattern-Abbau** →
**P2 = Konsolidierung/Format** → **P3 = RAG/KI** → **P4 = RTL/Politur**.

### Phase 0 — Fundament (P0, blockierend, klein, kein Datenfluss-Risiko)

Muss zuerst; alle anderen Phasen bauen darauf. Rein additiv (neue Module), bricht nichts.

- **WP-0.1 `common/i18n.py`** — `type LocalizedText`, `resolve_text()`, `DEFAULT_LOCALE`,
  `SUPPORTED_LOCALES`, `normalize()`/`negotiate()`. Unit-Tests für die Fallback-Kette
  (exakt → Basissprache → Default → erste → `''`).
- **WP-0.2 `utils/i18n.ts`** — `LocalizedText`, `resolveText()`, `resolveEnumLabel()`. Tests.
- **WP-0.3 Schema-`$def`** — `schemas/_defs.schema.yaml#/$defs/localized_text`
  (`additionalProperties:{type:string}`, `minProperties:1`).
- **WP-0.4 Locale-Resolution-Dependency** — `common/locale.py:get_request_locale` (Param>User>Header>
  Default). Noch **nicht** flächig verdrahten (das ist Phase 2), nur bereitstellen + Test.
- **AK:** Module existieren, Tests grün, keine bestehende Route verändert. **Abhängigkeiten:** keine.
  **Spezialist:** fullstack-developer. **Aufwand:** S.

### Phase 1 — Content-Modell-Migration (P1, dominanter Anti-Pattern-Abbau)

Überführt Suffix-Felder → Locale-Map. Pro Entitätsfamilie schneidbar; **je Familie** ein
Dual-Read-Fenster. Reihenfolge nach Größe/Isolation.

**Migrations-Mechanik (einmalig, gilt für alle WP-1.x):**
1. Domain-Modell + DTO: `name_de`/`name_en` → `name: LocalizedText` (Dual-Read-Property, das die alten
   Felder noch akzeptiert und mappt).
2. Seed-YAML + Schema auf `$ref localized_text` umstellen.
3. Loader: beide Formen lesen (Alt-Suffix → Map konvertieren).
4. **Migration v0020** (`v0020_localize_master_data.py`): Bestandsdokumente in ArangoDB von Suffix-
   Feldern auf Map-Felder backfillen (idempotent, additiv; Alt-Felder erst in einem späteren Cleanup-WP
   entfernen).
5. Consumer (FE) auf `resolveText()` umstellen (siehe Phase 2).

- **WP-1.1 IPM** (`ipm.yaml` 370 Vork., größte Fläche; `domain/models/ipm.py`,
  `api/v1/ipm/schemas.py`, `schemas/ipm.schema.yaml`, `seed_data.py:495`, `pest_taxonomy.py`).
  **nur-DE** → Map mit nur `de`-Key (EN-Befüllung ist spätere Datenarbeit). **Aufwand:** L.
- **WP-1.2 Care/Activities** (`activities.yaml` 102, `domain/models/activity.py`,
  `api/v1/activities/schemas.py`, `activity_plans/schemas.py`, `schemas/activities.schema.yaml`).
  **Aufwand:** M.
- **WP-1.3 Phasen** (`phase_sequences.yaml` 42, `domain/models/phase_sequence.py`,
  `api/v1/phase_sequences/schemas.py`, `schemas/phase_sequences.schema.yaml`, `seed_phase_sequences.py`).
  **Aufwand:** M.
- **WP-1.4 Tasks** (`domain/models/task.py:66,68,70,91,108,110`, `api/v1/tasks/schemas.py`).
  **Aufwand:** M.
- **WP-1.5 plant_info/species** (`common_name_de`/`_en` über `plant_info*.yaml` + `fish_species`,
  `adventskalender`, `schemas/plant_info.schema.yaml:126-127`, `seed_plant_info*.py`,
  `seed_adventskalender.py`). **Aufwand:** L (viele Dateien, aber gepaart DE+EN → sauber konvertierbar).
- **WP-1.6 substrates** (`substrates.yaml` 56, `domain/models/substrate.py:21,22`,
  `api/v1/substrates/schemas.py`, `schemas/substrates.schema.yaml`, `seed_substrates.py`). **Aufwand:** S.
- **WP-1.7 Enums-Stammdaten** (`botanical_families.yaml`, `hardiness_zones.yaml`, `location_types.yaml`
  + zugehörige Modelle/Schemas/Loader). **Aufwand:** M.
- **WP-1.8 Aquaponik-Stammdaten** (`api/v1/aquaponik/schemas.py` 12 Suffix-Felder,
  `domain/models/aquaponik.py`). **Aufwand:** S. (Fehler-Literale: siehe WP-2.4.)
- **AK je WP:** `seed-data-validator` grün; Loader ohne Fehler; Migration idempotent (2. Start = no-op);
  API liefert `LocalizedText`; alte + neue Form koexistieren im Übergang.
  **Abhängigkeiten:** Phase 0. **Parallelisierbar:** WP-1.x untereinander, jeweils eigener Worktree.

### Phase 2 — Konsolidierung Resolution & Format (P2, Frontend + BE-Verdrahtung)

- **WP-2.1 BE-Locale-Resolution verdrahten** — die **72** `language: str = "de"`-Params durch
  `Depends(get_request_locale)` ersetzen; `user.locale` anwenden (R-113). Router-weise
  (`ki_assistent`, `glossar`, `pest_detection`, `diagnose`, `recognition`, `print`, `knowledge`).
  **Aufwand:** M.
- **WP-2.2 FE-Content auf `resolveText`** — die **246** `_de`/`_en`-Zugriffe + `useLocalizedField`
  (`hooks/useLocalizedField.ts:16`) auf `resolveText(rec.field, i18n.language)` umstellen; `api/types.ts`
  Suffix-Typen → `LocalizedText`. 16 Dateien (SubstrateDetailPage, WorkflowDetailPage, TaskDetailPage,
  ActivityPlanTab, PestListPage, TreatmentDetailPage, GenericWidget, …). **Aufwand:** L.
- **WP-2.3 FE-binäre Zweige entfernen** — die **~76** `=== 'de'`/`startsWith('en')`-Stellen +
  **45** Locale-Literale (`de-DE`/`en-US`/`en-GB`) auf zentrale `utils/formatting.ts` (`Intl` mit
  `i18n.language`) und `resolveText`/`resolveEnumLabel` umstellen; **99** verstreute `toLocale*` durch die
  Utility ersetzen; `en-US`/`en-GB`-Inkonsistenz vereinheitlichen. dayjs: `dayjs.locale(i18n.language)` +
  `LocalizationProvider adapterLocale` für MUI-X-Pickers; hartkodierte DE-Formatstrings ersetzen
  (`TankStateChart.tsx:153-158`, `SensorHistoryChart.tsx`). **Aufwand:** L.
- **WP-2.4 Fehler-Literale → `error_code`** — die ~10 deutschen `ValueError`/`ValidationError`
  (`hardiness_zone.py:56,63`, `aquaponik_service.py:131,133,146,172,175,270,313`,
  `aquaponik/schemas.py:220`) auf `error_code` + Katalog-Key (`errors.<code>` FE) umstellen; technischer
  EN-Kontext bleibt. **Aufwand:** S.
- **WP-2.5 Enum-Helper** — `resolveEnumLabel`/`useEnumLabel`; die **519** inline `t(\`enums.…\`)` schrittweise
  (opportunistisch beim Anfassen) darauf umstellen; unvollständige Plural-Paare (`_other` ohne `_one`)
  reparieren. **Aufwand:** M (Kern S, Migration der Call-Sites laufend).
- **AK:** eine BE-Resolution aktiv; `user.locale` wirkt; keine binären FE-Content/Format-Zweige mehr in
  angefassten Dateien; Fehler laufen über `error_code`. **Abhängigkeiten:** Phase 0 (+ Phase 1 pro
  Entität für WP-2.2). **Parallelisierbar:** WP-2.1/2.4 (BE) ∥ WP-2.2/2.3/2.5 (FE).

### Phase 3 — RAG / Knowledge / KI (P3)

- **WP-3.1 `Literal["de","en"]` → offener `str`** — KS `schemas.py:35,52,53`, Backend
  `Language = Literal["de","en"]` (`glossary_term.py:25` u.a.), Router-Param-Pattern
  (`print/tenant_router.py` `^(de|en)$`) → Validierung gegen `SUPPORTED_LOCALES`. **Aufwand:** M.
- **WP-3.2 Prompt-Dictionaries parametrisieren** — die parallelen DE/EN-Prompt-Strings
  (`knowledge-service/app/prompt_engine.py:39-165`, `diagnosis_analysis_engine.py:112-158`,
  `ai_assistant_service.py`-Fallbacks) zu **einem** sprach-parametrisierten Template mit Default-Fallback
  (Template-Datei / Locale-Map), statt `if language == "en"`-Zweigen pro Codebasis. **Aufwand:** L.
- **WP-3.3 `doc_language` steuern statt hart** — KS-Aufrufe (`ai_assistant_service.py:414-415` etc.,
  `glossary_service.py:220-221`) von hart `"all"`/`"de"` auf die effektive Locale (R-112) mit
  dokumentiertem Cross-Language-Fallback; `LANG_TO_TSCONFIG` (`repository.py:15`) erweiterbar machen.
  **Aufwand:** M.
- **WP-3.4 Plant-Docs `language`-Frontmatter** — `spec/knowledge/plants/*.md` (210) Frontmatter-
  `language: de` ergänzen; RAG-Chunks haben es bereits. **Aufwand:** S (mechanisch).
- **WP-3.5 `language_mismatch_warning`** — entscheiden: Sprach-Detektion implementieren
  (`models/ai_assistant.py:52,138`, `glossary_term.py:95,138`) **oder** als tote Infrastruktur entfernen.
  **Aufwand:** S/M.
- **WP-3.6 Eval locale-parametrisierbar** — `spec/rag-eval/benchmark_questions.yaml` Struktur so, dass
  weitere Sprach-Benchmarks additiv sind (Datenarbeit selbst = Non-Goal). **Aufwand:** S.
- **AK:** keine `Literal["de","en"]`-Sperren; Prompts sprach-parametrisch mit Fallback; `doc_language`
  aus Resolution; Plant-Docs sprachmarkiert. **Abhängigkeiten:** Phase 0; teilw. Phase 2.1.

### Phase 4 — RTL-Fundament & Cleanup (P4)

- **WP-4.1 RTL-Grundlage** — `theme/theme.ts` `direction` je Locale; Emotion `stylis-plugin-rtl`
  (RTL-Cache); systematische Umstellung physischer `left/right`/`margin-left` auf logische Properties
  (`margin-inline-start` etc., UI-NFR-007 R-024/R-025). Ohne konkrete RTL-Sprache = vorbereitend.
  **Aufwand:** L. **Priorität:** niedrig, entkoppelt.
- **WP-4.2 Suffix-Cleanup** — nach stabilem Übergangsfenster die Alt-`*_de`/`*_en`-Felder aus Modellen/
  Schemas/Loadern entfernen (Migration-Cleanup, eigene Version); Dual-Read abschalten. **Aufwand:** M.
- **WP-4.3 Lint/Review-Gate** — Regel gegen neue `*_de`/`*_en`-Felder (Seed/Schema/Modell) und gegen
  neue binäre `=== 'de'`/`startsWith('en')`-Content-Zweige (NFR-017 P-1 durchsetzen). **Aufwand:** S.
- **AK:** RTL-fähiges Theme; keine Alt-Suffix-Felder mehr; Gate verhindert Regression.
  **Abhängigkeiten:** Phase 1+2 abgeschlossen.

---

## Abhängigkeitsgraph (verdichtet)

```
Phase 0 (Fundament)
   ├─► Phase 1 (Content-Migration, je Entität parallel)  ──► WP-2.2 (FE-Content pro Entität)
   ├─► Phase 2.1/2.4 (BE-Resolution, Fehler)
   ├─► Phase 2.3/2.5 (FE-Format/Enum) — unabhängig von Phase 1
   └─► Phase 3 (RAG/KI) — teilw. nach 2.1
Phase 4 (RTL/Cleanup/Gate) ──► nach Phase 1+2
```

## Migrations-Queue

- **v0020** `v0020_localize_master_data.py` — Backfill Suffix→Map (Phase 1), idempotent, additiv.
  Claim-at-merge; bei Kollision v0021+.
- Späterer **Cleanup-Migration** (Phase 4.2) — separate Version, entfernt Alt-Suffix-Felder erst nach
  bestätigtem Übergangsfenster.

## Risiken & Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|--------|---------------|
| Big-Bang bricht Consumer | Dual-Read-Fenster (Alt+Neu koexistieren), Cleanup erst Phase 4 |
| Migrations-Nummer-Kollision | claim-at-merge, v0020→v0021 |
| FE-Massenänderung (246+76+45) senkt Coverage | Umstellung datei-/entitätsweise, Tests je WP; zentrale Resolver reduzieren Call-Site-Zahl |
| RAG-EN-Qualität ohne native Chunks | Cross-Language-Retrieval + gesteuerte Antwortsprache dokumentiert; native Übersetzung optional additiv |
| RTL zieht Layout-Refactor nach | früh logische CSS-Properties (WP-4.1), entkoppelt einplanbar |
| Regression neuer Suffix-Felder | Lint/Review-Gate (WP-4.3) |

## Definition of Done (Gesamt)

- [ ] Phase 0 Fundament gemergt (Typen, Resolver, Schema-`$def`, Resolution-Dependency).
- [ ] Alle Suffix-Familien (Phase 1) auf `LocalizedText` migriert; Migration v0020 idempotent grün.
- [ ] Eine BE-Locale-Resolution aktiv; `user.locale` wird angewendet.
- [ ] Keine binären FE-Content/Format-Sprach-Zweige mehr (nach Phase 2); Fehler über `error_code`.
- [ ] RAG/KI ohne `Literal["de","en"]`-Sperre; Prompts sprach-parametrisch; Plant-Docs sprachmarkiert.
- [ ] RTL-Fundament + Lint-Gate verhindern Regression.
- [ ] Nachweis (NFR-017 §8): 3./4./5. Sprache = additive Daten-/Katalog-Operation, kein Schema-/Feld-/
      Code-Zweig-Diff.
