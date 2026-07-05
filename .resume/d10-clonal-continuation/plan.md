# Plan — feat/d10-clonal-continuation (Issue #381)

**Issue:** [#381](https://github.com/nolte/kamerplanter/issues/381) — feat(lifecycle):
D10 clonal continuation — new pup instance + `descended_from` edge (REQ-017)
**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/d10-clonal-continuation`
**Branch:** `feat/d10-clonal-continuation` (off `origin/develop`)
**Ursprung:** Follow-up aus #305/#385 (`.resume/req003-lifecycle-engine/plan.md`,
A3/D10 als bewusst zurückgestellt markiert).

---

## Goal

Beim **terminalen Event einer monokarpischen Mutter** (Agave/Bromelie/Guzmania-
Muster) statt eines Zyklus-Neustarts eine **neue `plant_instance` in Phase
`pup_establishment`** erzeugen und via **`descended_from`-Edge (REQ-017)** mit der
Mutter verknüpfen — explizit **kein** `is_cycle_restart`. Am Ende: Mutter terminal,
Nachfolger-Instanz existiert, Edge existiert, Tests belegen alle drei sowie die
Abgrenzung „kein Cycle-Restart". Tests grün, PR nach `develop`.

## Current state (recherchiert am 2026-07-05, Explore-Agent)

> **Kernbefund — die Entscheidungslogik ist inert.**
> `CyclicLifecycleEngine.should_restart_cycle` (`cyclic_lifecycle_engine.py:77`)
> ist **pure Logik, die kein Produktionspfad aufruft** (nur Unit-Tests). Der
> Runtime-Cycle-Restart läuft über eine **andere** Engine:
> `PhaseTransitionEngine._is_perennial_cycle_restart` (`phase_transition_engine.py:25`),
> sequence-/lifecycle-config-getrieben. Beide Engines sind entkoppelt. D10 muss
> die monokarpische Terminal-Entscheidung erst in den Runtime-Pfad verdrahten
> (dieselbe „implementiert-aber-inert"-Falle wie bei #385 E4/E6-Seed-Aktivierung).

Fakten mit Fundstellen:

- **Monokarpisch-Terminal-Branch** existiert und ist korrekt:
  `cyclic_lifecycle_engine.py:91-92` — `is_monocarpic(lifecycle) and
  core_phase(current_phase_name) in _REPRODUCTIVE_TERMINAL` → `(False, "Monocarpic:
  … terminal senescence …")`. `_REPRODUCTIVE_TERMINAL =
  {"flowering","fruit_development","ripening"}` (`:25`). Pur, gibt Tupel zurück →
  Seiteneffekt muss im Caller passieren.
- **Runtime-Terminal-Pfad:** `PhaseTransitionEngine.execute_transition`
  (`phase_transition_engine.py:131-204`) mutiert State; `terminate(...)` (`:206-254`,
  E5) ist der End-of-Life-Hook (setzt `termination_type`/`removed_on`, friert
  Phase-History ein). **Kein** Pfad konsultiert heute `is_monocarpic`/
  `should_restart_cycle`; **keiner** spawnt eine Nachfolger-Instanz.
- **Post-Transition-Seam:** `phase_service._on_phase_transition_callbacks`
  (`phase_service.py:271-273`) — registrierter-Callback-Mechanismus, existierende
  Erweiterungsstelle für Seiteneffekte nach Transition.
- **Trigger-Kette:** Celery `check_auto_transitions` (`tasks/phase_transitions.py:74-158`)
  → `phase_service.transition_phase` (`:253-275`) → `execute_transition`.
- **`descended_from` ist KEINE registrierte Edge-Collection.** Repo-weit nur in
  Prosa/Spec + Scaffold-Docstring. Registry: `collections.py` — `GRAPH_NAME=
  "kamerplanter_graph"` (`:543`), `GRAPH_EDGE_DEFINITIONS` (`:545+`). Neuer Eintrag
  `descended_from` (PLANT_INSTANCES→PLANT_INSTANCES) + Konstante + Namensliste
  (~`:434/:457`) nötig. `CLONED_FROM` (`:290`) ist NUTRIENT_PLANS→NUTRIENT_PLANS,
  **nicht** wiederverwendbar.
- **Edge-Write-Helfer:** `base_repository.create_edge(edge_collection, from_id,
  to_id, data)` (`base_repository.py:424-440`); Vorbild `PLACED_IN`-Edge in
  `plant_instance_repository.create()` (`:31-37`).
- **PlantInstance-Model** (`models/plant_instance.py:8-77`): Pflicht `instance_id`,
  `species_key`, `planted_on`; Phase `current_phase_key`/`current_phase_started_at`.
  **Keine** Lineage-Felder (`mother_key`/`descended_from`) heute.
- **Instanz-Erzeugung:** `PlantInstanceService.create_plant` (`:66-103`) →
  `_resolve_initial_phase_key` (`:291-314`, erste Phase der Sequence). Pup muss
  `current_phase_key` auf `pup_establishment` **erzwingen** (Bypass des Resolvers).
  Repo `create()` legt Doc + optional `PLACED_IN`-Edge an.
- **`pup_establishment`** ist nur Vokabular im Role-Map (`phase_role_map.py:49` →
  `seedling`), **kein geseedeter Phasen-Record**. → Klären, welche Phase der
  Nachfolger konkret bekommt (Sequence der Species muss `pup_establishment`
  enthalten, sonst Fallback nötig).
- **REQ-017-Scaffolds sind reine Stubs, an nichts verdrahtet:**
  `lineage_engine.py` (`LineageEngine.trace_ancestors/is_graft_compatible` →
  NotImplemented; **nichts importiert es**), `services/propagation_service.py`
  (`record/list_for_plant` → raise), `models/propagation.py` (`PropagationEvent`:
  method clone/seed/graft/division, `parent_plant_keys`/`child_plant_keys`),
  `api/v1/propagation/router.py` (leer, **nicht** ins App-Routing includiert).
- **Tests-Vorbild:** `test_flow_templates_d9_d12.py::TestD10PupMonocarpy` (`:52-97`)
  — Docstring (`:56-58`) sagt explizit, klonale Fortführung sei „DEFERRED to
  REQ-017, NOT tested here". `test_cyclic_lifecycle_engine.py::TestShouldRestartCycle`
  (`:51-85`) mit `setup_method` + `_lc()`/`_mother()`-Factories. Neue Tests folgen
  diesem Muster.

Referenzen: `spec/req/REQ-003_Phasensteuerung.md` (§D10), `spec/req/REQ-017*`
(Vermehrungsmanagement, `descended_from`-Kante), `.resume/req003-lifecycle-engine/plan.md`.

## Load-bearing design decision

**Wie tief REQ-017 hier implementiert wird und an welchem Seam D10 andockt.**
Empfehlung (vor Arbeitsbeginn via `requirements-elicit` bestätigen):

1. **Minimaler REQ-017-Schnitt** — nur was D10 braucht: `descended_from`-Edge-
   Collection registrieren + Nachfolger-Spawn + Edge-Write. **Kein** voller
   `LineageEngine.trace_ancestors`/`is_graft_compatible`, **keine**
   Propagation-API/Router-Registrierung (bleibt separater REQ-017-Follow-up).
   Grund: Issue-Scope ist eng D10; Scope-Creep in volle Lineage-Traversierung
   vermeiden. Ggf. `PropagationEvent(method=clone)` mitschreiben — **offen** (Q2).
2. **Seam = Runtime-Terminal-Pfad, nicht die inerte Pure-Engine.** Die
   monokarpische Terminal-Entscheidung in `PhaseTransitionEngine` (bzw. den
   `_on_phase_transition_callbacks`-Seam im `phase_service`) verdrahten, sodass
   beim Übergang der Mutter in die terminale Reproduktionsphase (a) **kein**
   Cycle-Restart erfolgt und (b) genau **ein** Nachfolger gespawnt + verlinkt wird
   (idempotent!). Reine Engine-Entscheidung bleibt testbar/pur; der Service trägt
   den Seiteneffekt (5-Schichten, wie im #385-Muster).

### Open questions — VOR Arbeitsbeginn klären (via requirements-elicit)

1. **Trigger-Zeitpunkt:** Spawn beim **Auto-Transition** in die terminale
   Reproduktionsphase (Celery `check_auto_transitions`), oder erst beim
   expliziten `terminate`/`remove` (E5) der Mutter? „Terminal event" ist mehrdeutig
   — Empfehlung: beim Eintritt in die terminale Phase (= der monokarpische
   Terminalpunkt), da die Mutter danach seneszent weiterlebt bis zum Absterben.
2. **PropagationEvent mitschreiben?** Nur `descended_from`-Edge, oder zusätzlich
   ein `PropagationEvent(method=clone)` persistieren (Reuse des Stubs
   `propagation_service`/`models/propagation.py`)? Letzteres wäre saubere
   REQ-017-Semantik, aber mehr Scope.
3. **PlantInstance-Lineage-Feld:** Zusätzlich zum Graph-Edge ein denormalisiertes
   Feld (`mother_key`/`propagated_from`) am Model + Response, oder ausschließlich
   die Kante? Kante = REQ-017-Weg; Feld erleichtert FE-Queries.
4. **Nachfolger-Platzierung & Attribute:** Erbt der Pup Location/Slot der Mutter
   (Slot wird durch Mutter-Terminierung frei?), `tenant_key`, `species_key`,
   `cultivar`? `planted_on` = Terminal-Datum? Welche Phase konkret, falls die
   Species-Sequence kein `pup_establishment` enthält (Fallback)?
5. **Frontend-Sichtbarkeit:** Soll der Abstammungs-Link in der Plant-Detail-View
   angezeigt werden („Nachkomme von …" / „Kindel"), oder ist #381 rein Backend +
   Tests? (Issue-Scope nennt nur Backend + Tests → Empfehlung: Backend-only,
   FE als separater REQ-017-Follow-up.)
6. **Migration:** Neue Edge-Collection `descended_from` auf Alt-Volumes — reicht
   idempotente Collection-Erzeugung beim Startup (additiv), oder braucht es einen
   Eintrag im versionierten Migrations-Framework (NFR-016/ADR-005)?

## Ordered work steps

1. **Requirements-Elicit**: Open Questions 1–6 beantworten, Requirement-Artefakt
   `project/requirements/d10-clonal-continuation.md` ≥ Threshold.
2. **Edge-Collection registrieren**: `DESCENDED_FROM = "descended_from"` in
   `collections.py` (Konstante + `GRAPH_EDGE_DEFINITIONS` PLANT_INSTANCES→
   PLANT_INSTANCES + Namensliste). Startup-Erzeugung verifizieren; ggf. Migration.
3. **Nachfolger-Spawn**: `PlantInstanceService` um eine Methode erweitern, die eine
   Instanz mit **erzwungener** `pup_establishment`-Phase erzeugt (Bypass
   `_resolve_initial_phase_key`) und die `descended_from`-Edge (child→mother) via
   `create_edge` schreibt. Tenant/Location/Attribute laut Q4. **Idempotent**.
4. **Verdrahtung des Terminal-Seams**: monokarpische Terminal-Entscheidung
   (`is_monocarpic` + terminale Reproduktionsphase) in den Runtime-Pfad hängen
   (Q1), sodass kein Cycle-Restart erfolgt und genau ein Spawn passiert. Guard
   gegen Doppel-Spawn (z. B. Marker/Existenz-Check der Edge).
5. **Tests**: Mutter wird terminal + Nachfolger-Instanz existiert bei
   `pup_establishment` + `descended_from`-Edge existiert + **NICHT** Cycle-Restart
   (`is_cycle_restart`/`cycle_number` unverändert); Idempotenz (kein Doppel-Spawn);
   Nicht-Monokarp-Kontrast unverändert. Muster aus `TestD10PupMonocarpy` +
   Service-/Repo-Integrationstest. Docstring-Deferral dort entfernen.
6. **Quality-Gate** (ruff/format/pytest; ggf. eslint/tsc/vitest falls FE) grün,
   dann PR nach `develop` via `pull-request-create` (Closes #381, Refs #305/#385).
   Doku (mkdocs DE/EN) + ggf. 3-Agent-Kette falls FE berührt.

## Invariants & guardrails (aus CLAUDE.md + Specs)

- **5-Schichten-Architektur** (NFR-001): API → Service → Engine → Repository →
  ArangoDB. Engines **pur** (kein I/O); Seiteneffekt (Spawn/Edge) im Service.
- **Keine Rückwärtstransition** in der Phase-Engine außer via `is_cycle_restart`/
  `is_reversion`. D10 ist **explizit kein** Restart — die Mutter geht terminal,
  Kontinuität über eine **neue Instanz**. Diese Grenze nicht verwischen.
- **Source-Code nur Englisch** (NFR-003); Doku Deutsch (DE-kanonisch, EN-Mirror).
- **Additiv, kein Removal** (Enum-/Collection-Werte); Edge-Collection additiv.
  Daten-/Schema-Migrationen nur über NFR-016/ADR-005 (Startup-Crash-Falle auf
  Alt-Volumes, vgl. Enum-Retirement-Falle).
- **Tenant-Isolation (SEC-001, #385):** Nachfolger erbt `tenant_key` der Mutter;
  `tenant_key` durch alle neuen Pfade durchreichen; Cross-Tenant-Test.
- **Idempotenz:** Spawn/Edge dürfen bei wiederholter Auswertung **nicht**
  dupliziert werden (vgl. non-idempotentes `generate_runs`-Bug aus #360/#361).
- **Pydantic v2**; `mixing_priority`-Konvention (REQ-004) nicht verletzen.
- **REQ-017-Scope-Disziplin:** `LineageEngine`/`PropagationService`-Vollausbau ist
  **nicht** Teil von #381 — nur der D10-nötige Minimalschnitt (siehe Design-Decision).
- **Feedback-Pflicht:** falls FE berührt → 3-Agent-Kette (UI-Review → Tests → Doku);
  Source-Code bevorzugt via `fullstack-developer`-Agent.

## Status / resume-anchor checklist

Erste unerledigte Box = Wiedereinstiegspunkt der nächsten Session.

- [x] **Resume anchor:** `requirements-elicit` durchlaufen; Open Questions 1–6
      beantwortet; Requirement-Artefakt ≥ Threshold (U_gate=0.85) →
      `project/requirements/d10-clonal-continuation.md`. **Entscheidungen:**
      Q1=Trigger bei Eintritt in terminale Phase (Auto-Transition); Q2=**inkl.**
      PropagationEvent(method=clone); Q3=Edge **+** denorm. Feld
      (mother_key/propagated_from); Q4a=Location erben, **kein** Slot; Q4b=Fallback
      auf erste Sequence-Phase; Q5=**Backend + Frontend** (Lineage-Link) + Tests
      → 3-Agent-Kette; Q6=idempotente Startup-Erzeugung (keine versionierte Migration).
- [x] `descended_from` Edge-Collection registriert (`collections.py`), Startup-
      Erzeugung verifiziert; Q6 = additiv (Reconciliation `:1476-1489`), keine
      Migration. Zusätzlich additive Doc-Collection `PROPAGATION_EVENTS` (für R3).
- [x] Nachfolger-Spawn im `PlantInstanceService` (`_spawn_pup`, erzwungene
      `pup_establishment`-Phase mit Fallback, Edge child→mother, Tenant/Attribute
      geerbt, kein Slot, idempotent via `has_descendants`). Denorm. `mother_key`
      am Model + `PlantResponse`; `PropagationEvent(method=clone)` persistiert.
- [x] Terminal-Seam verdrahtet: `is_monocarpic_terminal` (pure Engine) +
      `handle_monocarpic_terminal_transition` als `register_on_transition`-Callback
      (`dependencies.py:217`); kein Restart (mutiert Mutter nie), Doppel-Spawn-Guard.
- [x] Tests: **Backend** (19 Fälle) + **Frontend** (3 Fälle: Link@mother_key,
      Fallback-auf-Key bei 404, kein Link bei null) grün. Deferral-Docstring in
      `test_flow_templates_d9_d12.py` entfernt. FE-Feld `mother_key` in
      `api/types.ts`; Link im Info-Tab (`PlantInstanceDetailPage.tsx`), i18n
      `pages.plantInstances.descendedFrom(+Tooltip)` DE/EN.
- [x] **3-Agent-Kette** (FE berührt): UI-Review (a11y-Tooltip tastaturerreichbar,
      `aria-hidden` Icon, `wordBreak`, Skeleton gegen Key→Name-Flackern) → Tests
      (voller Lauf: **3621 pytest + 1892 vitest grün**, ruff/eslint/tsc clean;
      MSW-Handler des Ancestry-Tests gehärtet) → Doku (4 DE/EN-Seitenpaare erweitert,
      `mkdocs build --strict` grün, `propagation.md`-Admonition korrigiert).
- [x] Quality-Gate grün (Backend 3621/Frontend 1892 vor Rebase; nach Rebase auf
      `origin/develop` = PR #388: Backend 3309 unit + ruff clean, FE tsc/eslint
      clean, 34 merge-betroffene Tests grün). Doku aktualisiert (`mkdocs --strict`).
      Rebase-Konflikte (2× growth-phases.md „Siehe auch") gelöst (beide Link-Sets).
- [x] PR nach `develop` via `pull-request-create`: **PR #390 (Draft)**
      (`f1c46554d`→gepusht), Closes #381, Refs #305/#385. Branch auf `origin/develop`
      (inkl. #388) rebased. **Offen:** Draft → ready nach erstem grünem CI.
