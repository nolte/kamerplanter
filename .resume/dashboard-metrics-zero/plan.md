# Plan — fix/dashboard-metrics-zero

**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/dashboard-metrics-zero`
**Branch:** `fix/dashboard-metrics-zero` (off `origin/develop`)
**Symptom (User, Screenshot 2026-07-05):** Dashboard-Kennzahlenbereich zeigt
„Aufgaben heute" = 0, „Pflegeerinnerungen" = 0, „Aktive Pflanzen" = 0 total /
0 active — **obwohl aktive Pflanzen existieren**. Keine validen Daten im
Kennzahlenbereich.

---

## Goal

Der Dashboard-Kennzahlenbereich zeigt reale, tenant-korrekte Werte statt hart 0:
`plants_total` / `plants_active` (Kachel „Aktive Pflanzen"), `open_tasks_today`
(„Aufgaben heute") und `care_reminders_due` („Pflegeerinnerungen"). Am Ende:
existierende aktive Pflanzen erscheinen mit korrekter Anzahl, die Zahlen sind
tenant-isoliert, und der stille `0`-Fallback kann fehlende Implementierung nicht
mehr maskieren. Tests grün, PR nach `develop`.

## Current state (recherchiert am 2026-07-05, Explore-Agent)

> **Root Cause — die vom Service erwarteten Repository-Zählmethoden existieren
> schlicht nicht.** Der `DashboardService` prüft jede Kennzahl-Quelle per
> `hasattr(...)` und fällt bei fehlender Methode **still auf `0`** zurück. Da
> **keine** der erwarteten `count_*`/`list_*`-Methoden in irgendeinem Repository
> implementiert ist, sind **alle** Kacheln hart 0 — unabhängig vom Tenant. Es
> ist ein **Missing-Implementation-Bug, maskiert durch defensive `hasattr`-
> Guards** — **kein** `tenant_key`-Filterproblem. (Der tenant_key wird korrekt
> durchgereicht, aber die Guards greifen *vor* jedem DB-Zugriff, also wird er nie
> benutzt.)

Fakten mit Fundstellen:

- **Frontend (die drei Kacheln)** werden durch das generische Widget-Shell
  gerendert: `src/frontend/src/components/dashboard/widgets/GenericWidget.tsx:26-73`
  (zieht numerische Slices aus dem Payload `:31-34`, rendert als große Zahlen
  `:52-63`). Registrierung `widgetRegistry.ts:31`. i18n-Labels
  `i18n/locales/de/translation.json:5076-5087` (`active_plants_summary`,
  `tasks_today`, `care_reminders`), EN-Pendant `en/translation.json:5083`.
- **Datenlade-Pfad FE:** `DashboardPage.tsx:74-76` dispatcht `fetchAggregated`
  (`store/slices/dashboardSlice.ts:34-37`) → `api/endpoints/dashboard.ts:16-21`
  → `GET /dashboard/aggregated?widgets=<keys>` (tenant-scoped Client). Payloads
  in State `dashboardSlice.ts:59`; Provider `DashboardPage.tsx:320`; Zugriff
  `DashboardDataContext.tsx:26-29`.
- **Backend-Router:** `src/backend/app/api/v1/dashboard/tenant_router.py:106-124`
  (`GET /aggregated`) ruft `service.get_summary(ctx.tenant_key)` (tenant_key aus
  `get_current_tenant`, korrekt durchgereicht `:118`) und schneidet pro Widget via
  `_slice_summary_for` (`:89-104`) zu: `active_plants_summary` →
  `{plants_total, plants_active}`; `tasks_today` → `{open_tasks_today,
  upcoming_tasks}`; `care_reminders` → `{care_reminders_due}`.
- **Der Bug-Ort — Service mit `hasattr`-Guards:**
  `src/backend/app/domain/services/dashboard_service.py`
  - `get_summary` `:82-108`
  - `_plant_counts` `:112-125` — `hasattr(self._plant_repo, "count_for_tenant")`
    (`:113`) ist **False → `return 0, 0`**. „active" über `count_active_for_tenant`
    (`:117-121`), sonst Fallback `active = total`.
  - `_task_counts` `:127-137` — Guards auf `count_open_due_on` / `count_overdue`
    → False → `0, 0`.
  - `_care_due_count` `:148-155` — Guard auf `count_due_on` → False → `0`.
- **Fehlende Implementierung — verifiziert repo-weit:** `count_for_tenant`,
  `count_active_for_tenant`, `count_open_due_on`, `count_overdue`, `count_due_on`,
  `count_below_threshold`, `list_upcoming`, `list_recent` kommen **ausschließlich
  als `hasattr`-Probe** in `dashboard_service.py` vor — **keine einzige `def`**
  in irgendeinem Repository.
- **Repo-Wiring:** `src/backend/app/common/dependencies.py:1058-1068`
  (`get_dashboard_service`) injiziert die konkreten Repos.
- **Vorlage für tenant-korrekte AQL-Zählung existiert:**
  `data_access/arango/plant_instance_repository.py` — `get_survival_stats` (`:151`)
  filtert korrekt `FILTER p.tenant_key == @tenant_key` (`:169`) und **lehnt leeren
  tenant_key ab** (`:161-164`). Muster für die neuen `count_*`-Methoden.
- **„active"-Semantik** ist nirgends im Repo kodiert (weil `count_active_for_tenant`
  fehlt). Statusmodell existiert (FE-i18n Status „Aktiv" `de/translation.json:2080`).
  Vorgesehener Service-Fallback: fehlt `count_active_for_tenant`, gilt `active =
  total` (`dashboard_service.py:117-121`) — greift real nie, da schon
  `count_for_tenant` fehlt. **Open Question:** Welches Feld/welche Enum-Werte
  definieren „aktiv" bei einer `plant_instance`? (siehe Design-Decision).

## Design decision (load-bearing) — Repo-Methoden implementieren vs. `hasattr` entfernen

**Vorschlag:** **Beides, in dieser Reihenfolge.** (a) Die vom Service erwarteten
`count_*`/`list_*`-Methoden in den jeweiligen Repositories real implementieren
(tenant-gefiltertes AQL nach Vorbild `get_survival_stats`), damit die Kacheln
echte Werte liefern. (b) Danach die stillen `hasattr`-Guards im Service so
härten, dass ein künftig fehlendes Repo-Method nicht wieder unbemerkt zu `0`
kollabiert (echter Aufruf statt Probe; fehlende Methode = Programmierfehler, der
auffällt — nicht ein Wert, der wie „0 Pflanzen" aussieht). Der maskierende
Fallback ist die eigentliche Falle: er macht einen Implementierungsfehler von
einem korrekt aussehenden Leerzustand ununterscheidbar.

**Open Questions — VOR Implementierungsbeginn via `requirements-elicit` klären:**

1. **„Aktiv"-Definition:** Welches Feld/Enum an `plant_instance` markiert eine
   Pflanze als aktiv? (Status-Enum? Abwesenheit von `removed_on`/`termination_type`
   — vgl. E5-Terminierung aus #385/#390? Nicht in terminaler Phase?) Das
   entscheidet das AQL-`FILTER` von `count_active_for_tenant`.
2. **Scope dieser Working Copy:** Nur die drei sichtbaren Kacheln
   (`count_for_tenant`, `count_active_for_tenant`, `count_open_due_on`,
   `count_overdue`, `count_due_on`) — **oder** alle 8 vom Service geprobten
   Methoden inkl. `count_below_threshold`, `list_upcoming`, `list_recent`
   (weitere Widgets, die evtl. auch still 0/leer sind)? Empfehlung: erst die drei
   gemeldeten Kacheln vollständig grün, weitere Widgets als abgegrenzter
   Folge-Scope, falls betroffen.
3. **`hasattr`-Härtung — wie streng?** Guard ganz entfernen (fehlende Methode →
   `AttributeError` = lauter Fehler) vs. explizites Protokoll/ABC am Repo-Interface
   (typsicher, verhindert Drift dauerhaft). Empfehlung: Interface/Protocol in
   `domain/interfaces/`, Service ruft direkt — passt zur 5-Schichten-ABC-Konvention.
4. **„Aufgaben heute" & „Pflegeerinnerungen" — Fälligkeitslogik:** Bezugszeitpunkt
   `open_due_on(today)` = tenant-lokale Zeitzone? Zählt „überfällig" mit rein
   (Service hat separates `count_overdue`)? Care-Reminder-Fälligkeit nach welchem
   Feld (`due_on`/`next_due`)?
5. **Regressionstest gegen die Maskierung:** Test, der beweist, dass bei
   vorhandenen aktiven Pflanzen `plants_active > 0` zurückkommt — plus ein Test,
   der sicherstellt, dass eine fehlende Repo-Methode **nicht** mehr still zu 0
   wird (sondern auffällt). Ist das als Akzeptanzkriterium gewünscht?

## Requirements-Elicit — Ergebnis (2026-07-05, alle Antworten authoritativ)

Artefakt: `project/requirements/dashboard-metrics-zero.md` (U_gate = 0.80 = τ_high,
Saturation). Bestätigte Entscheidungen:

- **Q1 „aktiv":** `count_active_for_tenant` = `removed_on == null` (codebase-konsistent).
- **Q2 Scope:** **alle 8** geprobten Methoden (nicht nur die 3 Kacheln) —
  `count_for_tenant`, `count_active_for_tenant`, `count_open_due_on`,
  `count_overdue`, `count_due_on`, `count_below_threshold`, `list_upcoming`,
  `list_recent`.
- **Q3 Härtung:** Protocol/ABC in `domain/interfaces/`, Service ruft direkt (kein
  `hasattr`); fehlende Methode = lauter Fehler.
- **Q4 Fälligkeit:** „Aufgaben heute" strukturell = heute-nur (offen =
  `status ∈ {pending, in_progress}`), `count_overdue` separat = `due_date < today`.
  „Pflegeerinnerungen" = **heute + überfällig** (`due_date <= today`), da nur ein
  Care-Count existiert.
- **Q5 Tank-low:** **neues `Tank.low_threshold_percent`-Feld** (Default 20 %);
  `count_below_threshold` vergleicht jüngsten `TankState.fill_level_percent` gegen
  den tank-eigenen Schwellwert. (Kein Tank-Schwellwert-Konzept existierte bisher.)
- **Q-Regression:** Regressionstest gegen 0-Maskierung als Akzeptanzkriterium
  gesetzt (R8).

## Work steps (verfeinert)

1. **Requirements-Elicit** ✓ erledigt → Artefakt ≥ Threshold (siehe oben).
2. **„Aktiv"-Semantik fixieren** (aus Q1): Feld/Filter im PlantInstance-Modell
   verifizieren (`models/plant_instance.py`, Terminierungs-/Status-Felder aus
   #385/#390).
3. **Repo-Methoden implementieren** (tenant-gefiltertes AQL, Vorbild
   `get_survival_stats:151-169`, leeren tenant_key ablehnen) — **alle 8**:
   `PlantInstanceRepository.count_for_tenant` / `count_active_for_tenant`
   (`removed_on == null`); Task-Repo `count_open_due_on` / `count_overdue`
   (`status ∈ {pending,in_progress}`) / `list_upcoming`; Care-Reminder-Repo
   `count_due_on` (`due_date <= today`); Tank-Repo `count_below_threshold`
   (jüngster `TankState` vs. `Tank.low_threshold_percent`); Activity-Repo
   `list_recent`. Zusätzlich: **`Tank.low_threshold_percent` (Default 20 %)** ans
   Modell.
4. **Service härten** (`dashboard_service.py`): `hasattr`-Guards durch echte
   Aufrufe / Interface-Typ ersetzen (Q3), sodass fehlende Methoden nicht mehr
   still zu 0 kollabieren.
5. **Tests:** Repo-Unit-Tests (tenant-Isolation: fremd-tenant zählt nicht mit;
   leerer tenant_key abgelehnt), Service-Test (reale Counts durchgereicht),
   **Regressionstest gegen die 0-Maskierung** (Q5). Muster aus bestehenden
   `dashboard_service`-/`plant_instance_repository`-Tests.
6. **Verifikation am realen Flow** (`/verify` bzw. `run`-Skill): Dashboard mit
   Demo-User (`demo@kamerplanter.local`) laden, Kacheln zeigen reale Zahlen.
7. **Quality-Gate** (ruff/format/pytest; eslint/tsc/vitest nur falls FE berührt —
   voraussichtlich **Backend-only**, FE-Shell ist korrekt) grün, dann PR nach
   `develop` via `pull-request-create`.

## Invariants & guardrails (aus CLAUDE.md + Specs)

- **5-Schichten-Architektur** (NFR-001): API → Service → Engine → Repository →
  ArangoDB. Zähllogik/AQL gehört ins **Repository**, nicht in den Service; der
  Service orchestriert nur. Externe Interfaces als ABC in `domain/interfaces/`.
- **Tenant-Isolation (SEC-001):** Jede neue `count_*`-Methode **muss** `FILTER
  p.tenant_key == @tenant_key` setzen und leeren `tenant_key` ablehnen (Vorbild
  `get_survival_stats:161-164`). Cross-Tenant-Test Pflicht — sonst leaken Zahlen
  über Tenants.
- **Source-Code nur Englisch** (NFR-003); Doku Deutsch (DE-kanonisch, EN-Mirror).
- **Kein stiller Fallback als „Feature":** Der `hasattr`→0-Pfad ist die
  eigentliche Ursache dafür, dass der Bug unbemerkt blieb. Härtung nicht
  auslassen.
- **Pydantic v2**; python-arango `add_persistent_index` (nicht `add_hash_index`).
- **Feedback-Pflicht:** falls FE berührt → 3-Agent-Kette (UI-Review → Tests →
  Doku) + Auto-UI-Review. Source-Code bevorzugt via `fullstack-developer`-Agent.
- **Branch von `develop`;** Hauptcheckout bleibt auf `develop` (Arbeit nur im
  Worktree). GitHub-Texte (PR/Commits) Englisch.

## Status / resume-anchor checklist

Erste unerledigte Box = Wiedereinstiegspunkt der nächsten Session.

- [x] **Resume anchor:** `requirements-elicit` durchlaufen; Open Questions 1–5
      beantwortet; Requirement-Artefakt ≥ Threshold →
      `project/requirements/dashboard-metrics-zero.md` (U_gate 0.80).
- [x] „Aktiv"-Semantik fixiert (Q1): `count_active_for_tenant` = `removed_on ==
      null`; `removed_on`-Feld im PlantInstance-Modell verifiziert (`:24`).
- [x] Repo-`count_*`/`list_*`-Methoden implementiert (alle 8, tenant-gefiltert,
      leeren tenant_key abgelehnt via `_require_tenant_key`) — Plant / Task /
      Care (als `Task category=care_reminder`) / Tank / Activity +
      `Tank.low_threshold_percent`-Feld. Neue Protocols in
      `domain/interfaces/dashboard_repositories.py`.
- [x] `DashboardService` gehärtet: `hasattr` entfernt, Protocol-typisiert;
      `except AttributeError: raise` (fehlende Methode = laut), nur echte
      Laufzeitfehler degradieren zu 0/[]. R3-Datenmodell-Abweichung (Care=Task)
      im Artefakt dokumentiert + verifiziert.
- [x] Tests grün: 13 Repo-Unit (tenant-Isolation + leerer tenant_key) + 3
      Service (inkl. **Regressionstest gegen 0-Maskierung** R8). Ziel 20/20,
      breiter Slice 439/439, ruff/format clean.
- [x] Voller Backend-Quality-Gate grün: ruff check + format clean; pytest
      Vollsuite **3774 passed, 1 skipped** (187s).
- [x] Realer Flow verifiziert (kind-Cluster, In-Pod-Inline-AQL gegen Live-DB,
      da Skaffold-Pod den Primary-Checkout-Code fährt): `system-tenant` hat 4
      Pflanzen (3 aktiv), 12 überfällige care_reminder-Tasks. **ALT** (deployter
      `hasattr`-Service) = 0/0/0 (Bug reproduziert). **NEU** = plants 4/3,
      care_due 12, open_today 0 (legitim, nichts exakt heute fällig).
- [x] PR nach `develop` erstellt (Draft): **#399**
      (https://github.com/nolte/kamerplanter/pull/399). Alle Boxen erledigt.
