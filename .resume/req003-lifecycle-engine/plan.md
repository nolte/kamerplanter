# Plan — feat/req003-lifecycle-engine (Issue #305)

**Issue:** [#305](https://github.com/nolte/kamerplanter/issues/305) — feat(lifecycle):
implement REQ-003 lifecycle engine — D8–D13 flow templates + E1–E8
triggers/paths/resources
**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/req003-lifecycle-engine`
**Branch:** `feat/req003-lifecycle-engine` (off `origin/develop`)

---

## Goal

Issue #305 **vollständig** umsetzen: die Backend-Engine-Implementierung +
Cross-Spec-Wiring + Model/Schema-Felder + UI der REQ-003-Lebenszyklus-Audits, die
in PR #304 (Spec/Schema) zurückgestellt wurden. Am Ende: alle Checkboxen aus #305
(A–G + Acceptance Criteria) erfüllt, Tests grün, PR nach `develop`.

## Current state (recherchiert am 2026-07-05)

> **Überraschung — viel ist schon da.** Beim Worktree-Setup zeigte sich, dass
> große Teile der #305-Checkliste bereits auf `origin/develop` implementiert sind.
> Der **erste Arbeitsschritt ist deshalb ein präzises Gap-Audit** der Checkliste
> gegen den Code, nicht eine Neuimplementierung. Nicht doppelt bauen.

Bereits vorhanden (Stichproben-belegt, verifizieren!):

- **F (Model/Schema):** `TransitionTriggerType.PHOTOPERIOD_BASED/VERNALIZATION_BASED`
  (`app/common/enums.py`), `TerminationType`/`termination_cause`,
  `lifecycle.growth_determinacy`, `phase.is_reversion`/`is_premature`,
  `plant_instance.termination_type` + `vernalization`-Felder — existieren als
  Pydantic-Felder.
- **A/D8:** `app/domain/engines/phase_role_map.py` (Phase→Engine-Rolle-Mapping,
  inkl. `bract_coloring`, `winter_rest`, `pup_establishment`).
- **B/E1+E2:** `app/domain/engines/transition_trigger_evaluator.py`
  (`photoperiod_should_fire`, `vernalization_should_fire`, `gdd_should_fire`),
  `photoperiod_calculator`, `VernalizationTracker`.
- **E7/E8:** `app/domain/engines/phase_resource_resolver.py`.
- **Engine:** `phase_transition_engine.py` behandelt `is_cycle_restart`.

Sichtbare Lücken (zu bestätigen im Audit):

- **G (Frontend):** keine Treffer für `termination_type`/`survival` unter
  `src/frontend/src` → UI-Erfassung von `termination_type`/`termination_cause`
  beim Entfernen + Survival-Rate/Failure-Cause-View fehlen vermutlich ganz.
- **G:** Per-Phase-Bewässerungs-/Nährstoff-Regime in der Plant-Detail/Phase-View.
- **D9–D12:** Phase-Sequenz-Seeds für CAM/Sukkulenten, Kindel-Monokarpie, photo-
  periodische Zierpflanze, Palme/Farn/Geophyt — Vollständigkeit unklar.
- **E3–E6:** `is_reversion`-Guard in `validate_transition`, `reversion_count`-
  Inkrement, `growth_determinacy`-Branch, Death-Freeze (E5), Premature-Bolting
  (E6) — Verdrahtung in Engine/Service prüfen.
- **Tests:** Acceptance-Criteria-Abdeckung pro Trigger/Flag/Template.

Referenzen: `spec/req/REQ-003_Phasensteuerung.md` (§D8–D13, §E1–E8),
`spec/analysis/lifecycle-flow-completeness-audit.md`.

## Load-bearing design decision

**Wie gehen wir mit dem bereits vorhandenen Code um?** — Fix-forward und
Lückenschluss, keine Neuimplementierung. Der `develop`-Stand liefert das
Fundament (Modelle, D8-Map, Trigger-Evaluatoren, Resource-Resolver); #305 wird
durch (a) ein belastbares Gap-Audit, (b) das Schließen der offenen Verdrahtung
(E3–E6), (c) die fehlenden Seeds (D9–D12), (d) das komplette Frontend (G) und
(e) die Test-Abdeckung abgeschlossen.

### Open questions — VOR Arbeitsbeginn klären (via requirements-elicit)

1. **Scope-Schnitt:** Soll #305 in **einem** großen PR landen oder in Teil-PRs
   (Backend-Gaps / Seeds / Frontend / Tests)? Empfehlung: ein PR pro
   Abschnitt-Cluster, aber ein Feature-Branch — je nach Reviewer-Last.
2. **Frontend-Umfang (G):** Reicht ein einfacher Survival-Rate-Table, oder wird
   eine Chart-Visualisierung (Verlust nach Phase/Ursache) erwartet? (dataviz-Skill)
3. **D9–D12-Seeds:** Neue reale Arten seeden oder nur generische Flow-Template-
   Fixtures? Welche Arten sind Referenz (Agave/Bromelie, Poinsettia, Palme, Farn)?
4. **E5 Death-Freeze ↔ #291:** Wie genau werden offene Tasks/Reminders geschlossen
   — Reuse der #291-Mechanik oder neuer Pfad?
5. **Migration:** Braucht `termination_type`/`reversion_count`/`growth_determinacy`
   eine Daten-Migration (versioniertes Framework, NFR-016) für Alt-Instanzen?

## Ordered work steps

1. **Gap-Audit**: #305-Checkliste (A–G + AC) Zeile für Zeile gegen Code; Ergebnis
   als Delta-Liste (done / partial / missing). Ausgangspunkt Resume-Anchor unten.
2. **Backend-Lücken (A–F)**: E3-Reversion-Guard + `reversion_count`, E4-Determinacy-
   Branch, E5-Death-Freeze (+ Task/Reminder-Close), E6-Premature-Bolting; D9–D12-
   Seeds; E7/E8-Resolver-Vollständigkeit; Enum/Schema-Mirror falls Restlücken.
3. **Frontend (G)**: `termination_type`/`termination_cause`-Capture beim Entfernen;
   Survival-Rate/Failure-Cause-View; Per-Phase-Bewässerungs-/Nährstoff-Regime in
   Detail/Phase-View. → danach Pflicht-3-Agent-Kette (UI-Review → Tests → Doku).
4. **Tests (Acceptance Criteria)**: Unit-Tests je Trigger (E1/E2), Flag (E3/E6),
   Template (D9–D12), D8-Mapping, E4/E5, E7/E8; keine Regression D1–D7.
5. **Quality-Gate** (ruff/eslint/tsc/pytest/vitest) grün, dann PR nach `develop`
   via `pull-request-create`. Doku (mkdocs) + Fact-Tables aktualisieren.

## Invariants & guardrails (aus CLAUDE.md + Specs)

- **5-Schichten-Architektur** (NFR-001): API → Service → Engine → Repository →
  ArangoDB. Frontend nur via REST. Engines pur/testbar (kein I/O), Caller sammelt
  Kontext — dem Muster im `TransitionTriggerEvaluator` folgen.
- **Source-Code nur Englisch** (NFR-003); Doku Deutsch (DE-kanonisch, EN-Mirror).
- **Additiv, kein Removal** in diesem PR (Enum-Werte etc.); Daten-Migrationen über
  das versionierte Framework (NFR-016/ADR-005), sonst Startup-Crash-Falle.
- **Pydantic v2**, `mixing_priority`-Konvention (REQ-004) nicht verletzen.
- **Frontend**: Custom Hooks mit objects/arrays via `useMemo` stabilisieren; i18n
  `pages.<section>.<key>` / `enums.<enumName>.<value>`; Mobile-First; beschreibende
  Texte + Fachbegriff-Erklärungen; MUI 7.
- **Feedback-Pflicht**: nach Implementierung 3-Agent-Kette (UI-Review → Tests →
  Doku); Source-Code bevorzugt via `fullstack-developer`-Agent.
- **Keine Rückwärtstransition** in der Phase-Engine außer via `is_cycle_restart`
  ODER `is_reversion` (E3) — das ist genau die neue erlaubte Ausnahme.

## Status / resume-anchor checklist

Erste unerledigte Box = Wiedereinstiegspunkt der nächsten Session.

- [x] **Resume anchor:** `requirements-elicit` durchlaufen; Open Questions 1–5
      beantwortet; Requirement-Artefakt ≥ Threshold.
      → `project/requirements/req003-lifecycle-engine.md` (U_gate=0.8). Q1=Ein PR,
      Q2=Tabelle+Chart, Q3=Reale Arten; Q4 (E5-Reuse) + Q5 (keine Migration) als
      code-belegte Assumptions A1/A2.
- [x] Gap-Audit der #305-Checkliste (A–G + AC) gegen Code als Delta-Liste erstellt.
      **DONE (nicht anfassen):** A2, A4, A5, B2, C1, E7, F1–F4, G2, AC3.
      **Lücken (zu bauen):**
      - C2/E4: `growth_determinacy` schema-only — keine Engine hält indeterminate
        in stabiler recurring-Produktivphase / `harvest_pattern='continuous'`.
      - D1/E5: `terminate()` verwaist — `/remove`→`remove_plant` setzt nur
        `removed_on`, nie `termination_type/cause`, cancelt keine care_reminders.
        Router/Service-Hook + Reminder-Cancel fehlen.
      - D2/E6: `is_premature` schema-only — nie gesetzt/evaluiert/geseedet.
      - E8: Nutrient-Resolver ignoriert `target_ph` + Mikronährstoff-pH-Gating.
      - G1: Frontend termination-Capture + Survival/Failure-View KOMPLETT leer.
      - AC1/AC2: Test-Lücken (E6-Behavior, D10–D12-Template-Seed-Tests, E4-Branch).
      **Scope-Grenzfälle (Nutzer-Entscheid):** A3 (D10 klonale Fortführung via
      neue Instanzen + `descended_from`, REQ-017 `lineage_engine` = NotImplemented)
      und B1 (Indoor-Licht-Photoperiode, REQ-018) — beide groß/dependency-schwer,
      im Code als Follow-up markiert. A1 minor (Transition-Engine konsultiert
      `phase_role_map` nicht, aber Map wird von Resolver/Cyclic-Engine genutzt).
- [x] Backend-Lücken **E4/E5/E6** verdrahtet + getestet (E3 laut Audit schon done).
      → DONE: E4 `stays_in_productive_phase` (cyclic_engine + phase_transitions),
      E5 `remove_plant(termination_type/cause)`+`terminate()`+Reminder/Task-Cancel
      (+ `RemovePlantRequest`/`PlantResponse`-Felder, `/remove`-Body), E6
      `is_premature` in History, E8 pH-Gating im Resolver. 58 gezielte Tests grün,
      Gesamt 3350 pass, ruff clean. 13 Dateien + 1 neue Test-Datei.
- [ ] D9–D12 Seeds: laut Audit **bereits als art-bezogene Phasenlisten geseedet**
      (A2/A4/A5 done); A3/D10-klonale-Fortführung = **Follow-up (REQ-017)**. Rest:
      nur **D10–D12-Template-Tests** (in Test-Phase gefaltet).
- [x] E8-Resolver pH-/Mikronährstoff-Gating erledigt (im Backend-Cluster). E7 done.
- [x] **Frontend G1**: survival-stats-Endpoint (tenant-scoped AQL, Loss-by-Phase/
      Cause) + Termination-Dialog + Survival-View Tabelle & recharts-Chart. i18n de/en,
      tsc/eslint clean, vitest-Vollsuite 1861 grün.
- [x] **Security-Review** (read-only): Tenant-Isolation vollständig sauber; SEC-001
      Defence-in-Depth (`remove_plant` tenant_key durchgereicht + Cross-Tenant-Test)
      angewandt & grün.
- [ ] Frontend G: termination-Capture + Survival-View + Per-Phase-Regime-View.
- [~] 3-Agent-Kette: UI-Review ✅ (a11y/role/aria, Irreversibel-Warnung, Ladezustände,
      3. Barrierefreiheits-Tabelle); Tests → finales Quality-Gate; Doku → mkdocs-Agent (offen).
- [x] Acceptance-Criteria-Tests komplett; keine D1–D7-Regression.
      D10–D12-Template-Tests ergänzt (`test_flow_templates_d9_d12.py`); alle
      E-Trigger/Flags + D8 abgedeckt.
- [x] Quality-Gate grün: Backend 3376 pass + ruff/format clean; Frontend tsc 0,
      eslint 0 errors (15 nicht-blockierende Warns = Bestandsmuster), vitest 1861 pass.
- [x] Doku (mkdocs): 6 Seiten DE+EN, strict-build grün. E4/E6-Admonitions nach
      Seed-Aktivierung auf „aktiv für Tomate/Paprika/Gurke bzw. Spinat" geflippt;
      E8 bleibt „Teilweise verfügbar" (Resolver-Integration = Follow-up).
- [x] **E4/E6-Seed-Aktivierung**: Tomate/Paprika/Gurke → `growth_determinacy:
      indeterminate` (species.yaml lifecycle_overrides); Spinat → photoperioden-
      getriggerte `vegetative→bolting`-Regel `is_premature:true` (lifecycles_outdoor.yaml).
      Schema/Loader additiv; 8 neue Seed-Tests; Backend-Vollsuite 3384 pass.
- [x] **Follow-up-Issues angelegt:** #381 (A3/D10 klonale Fortführung, REQ-017),
      #382 (B1/E1 Indoor-Photoperiode, REQ-018), #383 (E7/E8 Resolver→Service-
      Integration). Nichts still fallengelassen.
- [x] PR nach `develop`: **#385 (Draft)** via `pull-request-create`; Closes #305,
      Refs #381/#382/#383. 2× auf develop rebased (#376/#377, dann #378/#379); Gate
      grün: Backend 3402 pytest, Frontend tsc/eslint/vitest 1889, mkdocs strict.
      **FERTIG** — Draft nach erstem grünem CI auf ready flippen.
