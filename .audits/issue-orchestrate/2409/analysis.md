---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: "2409"
classification: infra
secondary-classes: [docs]
route: direct
status: approved-scope
created: 2026-11-02
---

# Issue Orchestration — Pre-analysis (#2409, Rest nach #2597)

## Issue metadata
- **Issue**: #2409 — ci: audit and reduce redundant PR test runs and Docker builds (offen)
- **Linked items**: PR #2597 (gemergt 2026-10-31T08:37Z) — Audit + per-Image-Cache-Scopes; Owner-Kommentar: Rest braucht Betreiberentscheidungen
- **Prior art checked**: `.audits/cicd-audit/2026-10-31-pr-redundancy-audit.md` (§7 Empfehlungen, §8 offene Punkte)

## Classification
- **Primary class**: infra (secondary: docs)
- **Asserted cause verified**: confirmed in #2597 (sechs Jobs im Default-Scope `buildkit`); heute nachgemessen: auf PR-Refs (#2629/#2631/#2632) existieren nur `index-e2e-backend/frontend/tests`, kein `index-buildkit` (gh api actions/caches).

## Scope
- **In scope** (Betreiberwahl "Doku + Messung"): (P1) Vorher/Nachher-Messung der Scope-Änderung im Audit nachtragen; (P2) `docs/{de,en}/deployment/ci-cd.md`: Zuständigkeit je Check, bewusste Duplikation, Scope-Regel.
- **Out of scope**: 7.1 Vitest einmal, 7.3 bundle-budget+lighthouse, 7.5 ein Image für backend/worker, 7.6 docker-publish-Scopes (Betreiber hat nicht freigegeben; bleiben offen, Issue bleibt offen). 7.2/7.4 vom Audit verworfen.

## Route
- **Decision**: direct — ein Ergebnis, ein PR-Strang, kein Roadmap-Item.

## Work packages
### P1 — Messung nachtragen
- **Acceptance**: Audit enthält §4a mit Median/Min/Max der `build-*`-Jobs aus erfolgreichen `docker-lint-build`-PR-Läufen nach 2026-10-31T08:38Z, Vergleich zu Baseline §4, Cache-Index-Gegenprobe, Grenzen der Aussage.
- **Files**: `.audits/cicd-audit/2026-10-31-pr-redundancy-audit.md`
- **Specialist**: Orchestrator (eigene Messung; kein Dokumentations-Edit am Produkt)
- **Depends on**: none

### P2 — ci-cd.md DE/EN
- **Acceptance**: DE-Seite (kanonisch, "du") und EN-Spiegel tragen: Zuständigkeit je Pflicht-Check, bewusst belassene Duplikation, Cache-Scope-Regel (ersetzt Layer-Caching-Satz); `mkdocs build --strict` grün; DOCS.md-Regeln (keine Issue-/REQ-Verweise im Endnutzertext) eingehalten.
- **Files**: `docs/de/deployment/ci-cd.md`, `docs/en/deployment/ci-cd.md`
- **Specialist**: mkdocs-documentation
- **Depends on**: P1 (Zahlen), nur lose

## Risks
- Messung ist durch wechselnde Änderungen (Python 3.15-Basisimage, Layer-Invalidierung) konfundiert → als Indiz kennzeichnen, nicht als Beweis.
- Queue-Zeiten der Stichprobe schwanken stark (bis 12 min); nicht als Effekt der Änderung ausweisen.

## Open questions
- none

## Dispatch log
