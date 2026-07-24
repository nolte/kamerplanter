---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "749"
classification: "bug"
secondary-classes: [test]
route: "direct"
status: approved
created: "2026-07-24"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #749 — Settings deep-links using ?tab= query are silently ignored (useTabUrl resolves hash only)
- **URL**: https://github.com/nolte/kamerplanter/issues/749
- **Labels**: bug, test, frontend
- **Linked items**: #743 (root-cause analysis; REQ-030 page object dort bereits auf Hash-Konvention umgestellt)
- **Prior art checked**: keine offenen/gemergten PRs referenzieren #749 (`closedByPullRequestsReferences` leer, PR-Suche leer); Hash-Konvention bereits etabliert in `ModuleGuard`, `DashboardPage`, `IdentificationConsentGate` und allen `useTabUrl`-Konsumenten

## Classification

- **Primary class**: bug
- **Secondary class(es)**: test (E2E-Tests asserten gegen den falschen Tab)
- **Rationale**: In-App-Links und E2E-Navigationen mit `?tab=` landen still auf Tab 0 (Profil), weil `useTabUrl` (`src/frontend/src/hooks/useTabUrl.ts:22-27`) ausschließlich das Hash-Fragment auswertet — beobachtbares Fehlverhalten, kein Feature.

## Requirements gate

Kein Requirement-Artefakt unter `project/requirements/` für dieses Issue.
**Operator override recorded**: Das Issue ist ein präzises Follow-up aus der
Root-Cause-Analyse von #743, vom Repository-Owner (trusted author) mit
explizitem „Expected"-Abschnitt, file:line-Referenzen und vollständiger
Call-Site-Liste eingereicht. Die Anforderung ist eindeutig testbar formuliert;
ein `requirements-elicit`-Interview würde keine neue Information liefern.
Autonomer Lauf per direkter Skill-Invocation mit Issue-URL durch den Operator.

## Scope

- **In scope**: Migration aller verbleibenden `?tab=`-Call-Sites auf die Hash-Form (`/settings#<key>`), sodass In-App-Links auf dem intendierten Settings-Tab landen und die REQ-023-E2E-Tests den Tab prüfen, den sie zu testen behaupten. Zusätzlich zur Issue-Liste gefunden: `tests/e2e/pages/notification_settings_page.py` (PATH + Docstrings) nutzt ebenfalls `?tab=notifications`.
- **Out of scope**: Query-Alias in `useTabUrl` (`?tab=` zusätzlich akzeptieren) — verworfen zugunsten der etablierten Hash-Konvention (Konsistenz mit #743-Fix und allen übrigen Konsumenten; kein externer Bookmark-Vertrag auf `?tab=` bekannt). Kein Umbau der Tab-Definitionen der `AccountSettingsPage`.

## Route

- **Decision**: direct
- **Rationale**: Ein kohärentes Outcome (Deep-Links funktionieren), ein einzelner PR-Strang, kein Roadmap-Item — bounded per Spec-Definition.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — Frontend-Admin-Pages auf Hash-Form migrieren

- **Problem statement**: `AdminEditUserPage.tsx` (Zeilen 143, 196) und `AdminEditTenantPage.tsx` (Zeilen 145, 198) navigieren mit `navigate('/settings?tab=platform')`; der Query-Teil wird ignoriert und der Nutzer landet auf dem Profil-Tab statt auf dem Platform-Tab.
- **Acceptance criteria**: Alle vier Call-Sites navigieren zu `/settings#platform`; `grep -rn "?tab=" src/frontend/src` liefert 0 Treffer; bestehende Frontend-Tests (vitest) bleiben grün; falls Tests die Navigation asserten, sind sie auf die Hash-Form angepasst.
- **Touched files / artifacts**: `src/frontend/src/pages/admin/AdminEditUserPage.tsx`, `src/frontend/src/pages/admin/AdminEditTenantPage.tsx`, ggf. zugehörige Tests unter `src/frontend/src/test/`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### P2 — E2E-Page-Objects auf Hash-Form migrieren

- **Problem statement**: `tests/e2e/pages/account_settings_page.py:62` baut `f"{self.PATH}?tab={tab}"` und `tests/e2e/pages/notification_settings_page.py:32` definiert `PATH = "/settings?tab=notifications"` — beide navigieren dadurch effektiv auf den Profil-Tab; die REQ-023-Security-Tests asserten gegen den falschen Tab.
- **Acceptance criteria**: `account_settings_page.open(tab=...)` navigiert zu `/settings#<tab>`; `notification_settings_page.PATH` (und Docstrings) nutzen `/settings#notifications`; `grep -rn "?tab=" tests/` liefert 0 Treffer; `ruff check tests/e2e` grün; keine Test-Semantik über die URL-Form hinaus verändert.
- **Touched files / artifacts**: `tests/e2e/pages/account_settings_page.py`, `tests/e2e/pages/notification_settings_page.py`
- **Specialist**: `nolte-engineering:e2e-test-reviewer`
- **Depends on**: none (sequenzielle Dispatch-Reihenfolge nur wegen geteiltem Worktree)

## Dependency ordering

P1 → P2 (fachlich unabhängig; sequenziell wegen geteiltem Working Tree).

## Risks

- **Light-Mode-Tab-Mengen**: `security`/`platform`-Tabs existieren nur im Full-Mode; die E2E-Tests, die diese Tabs ansteuern, laufen im Full-Profil — keine Änderung der Tab-Verfügbarkeit durch dieses Issue. Mitigation: nur URL-Form ändern, keine Tab-Logik.
- **E2E nicht lokal verifizierbar**: Selenium-Suite braucht laufenden Stack; Verifikation mechanisch (grep + ruff) plus CI `e2e-smoke`. Mitigation: Änderung ist rein string-förmig, Page-Object-Kontrakt unverändert.
- Keine security-sensitiven Pfade berührt (kein Auth-/Tenant-/Crypto-Code) → kein `code-security-reviewer`/`security-review`-Gate erforderlich.

## Open questions

Keine — Lauf ist autonom; Entscheidung „Migration auf Hash statt Query-Alias" folgt der bestehenden Repo-Konvention (siehe Scope).

## Dispatch log

- 2026-07-24 P1 dispatched to `nolte-engineering:fullstack-developer` — done: 4 Call-Sites in AdminEditUserPage.tsx (143, 196) und AdminEditTenantPage.tsx (145, 198) auf `/settings#platform` migriert; `grep "?tab=" src/frontend/src` = 0 Treffer; tsc PASS, eslint PASS (nur pre-existing Warnings), vitest 32/32 PASS; keine vitest-Datei deckt die Admin-Edit-Pages ab, keine Testanpassung nötig.
- 2026-07-24 P2 dispatched to `nolte-engineering:e2e-test-reviewer` — done: `account_settings_page.py:62` `?tab={tab}` → `#{tab}` (Signatur unverändert); Befund: `notification_settings_page.py` war bereits durch #748 (`06b0344ab`) auf `/settings#notifications` migriert, dort nur noch Docstring-Prosa mit `?tab=`-Literal bereinigt; `grep "?tab=" tests/` = 0 Treffer; ruff auf geänderten Zeilen clean (nur pre-existing N812-Baseline), compileall PASS.
