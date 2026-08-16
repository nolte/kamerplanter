# Offene Issues — Umsetzungsplan (Stand 2026-08-14)

26 offene Issues. Dieser Plan ordnet sie nach **berührten Dateien** statt nach Thema,
weil der Engpass die Merge-Serialisierung ist, nicht das Implementieren.

## Die eigentliche Kostenrechnung

`develop` hat `strict: true` (Branch muss aktuell sein) und `enforce_admins: true`.
Gemessen an PR #1138/#1143:

| Posten | Dauer |
|---|---|
| `static / Static CI Tests` | ~7–8 min |
| `lint-test-build (22)` | ~4 min (parallel) |
| Renovate-Verkehr auf `develop` | mehrere Merges pro Stunde |
| Folge: Branch-Update + erneuter CI-Lauf | ~10 min pro Runde |

Ein PR kostet also **10–25 min Wanduhr**, unabhängig davon, ob er drei Zeilen oder
dreihundert ändert. 26 Einzel-PRs wären 5–10 Stunden reine Wartezeit; die
`automerge`-Action hilft nicht zuverlässig, weil ihr Retry-Fenster (6 Versuche in
~30 s) kürzer ist als ein Check-Lauf.

**Konsequenz: bündeln.** Aus 26 Issues werden 11 PRs, und die Bündel sind so
geschnitten, dass sie **keine gemeinsamen Dateien** anfassen — dadurch können sie
parallel entwickelt und ohne Rebase-Konflikte hintereinander gemergt werden.

## Nicht autonom umsetzbar — vorab zu entscheiden

Diese vier stoppen einen autonomen Lauf, wenn sie nicht vorher geklärt sind:

| Issue | Warum blockiert | Was ich brauche |
|---|---|---|
| **#1122** Service-Accounts im Active-Tenant-Kontext | Der Issue-Body *ist* eine Fragenliste (darf ein Service-Account „als Org" handeln? wie wird seine Rolle modelliert?) | Produktentscheidung |
| **#618** KAMI-Bildpipeline | Cloudflare-Zugangsdaten fehlen | Credentials |
| **#779** `/api/v2`-Migration | Breaking Change, `stale`-Label, Monatsarbeit | Roadmap-Entscheidung: jetzt, später, nie |
| **#1092** `tenant_has_access`-Kante | Datenmodell-Entwurf mit Semantikfragen (wer vergibt Grants, wie werden sie widerrufen) | Design-Entscheidung |

**#12** (Renovate Dependency Dashboard) ist kein Arbeitsposten, sondern ein Bot-Artefakt.

## Die 11 Bündel

Spalte „Konflikt" = welche anderen Bündel dieselben Dateien anfassen (leer = keine).

### Welle 1 — sofort, unabhängig, klein

| # | Bündel | Issues | Berührt | Konflikt |
|---|---|---|---|---|
| 1 | **Auth-Ratelimit** | #1130, #1131 | `api/v1/auth/router.py`, Limiter-Config | 3 |
| 2 | **Frontend-Kleinkram** | #1132, #1139 | `i18n/locales/*/pages.json`, Login-Layout | — |
| 3 | **Prod-Pin** | #1025 | Helm/ArgoCD-Werte | — |
| 4 | **Katalog-Rollengates** | #1110, #1120 | `imports/router.py`, `botanical_families/router.py` | 5 |

Vier PRs, alle klein, alle unabhängig voneinander → parallel entwickelbar,
seriell mergebar. Realistisch ein Vormittag.

### Welle 2 — baut auf Welle 1

| # | Bündel | Issues | Berührt | Voraussetzung |
|---|---|---|---|---|
| 5 | **Cultivar-Referenzintegrität** | #1112, #1114 | `planting_runs/`, `cultivars/schemas.py`, Frontend-Formular | Bündel 4 (gleiche Router-Familie) |
| 6 | **Guard + Task-Bindung** | #1111, #1102 | Guard-Test, `task_service.py` | — |
| 7 | **DAST-Template** | #1133 | `security/nuclei-templates/` | Bündel 1 (prüft dessen Verhalten) |
| 8 | **Native Refresh** | #1134 | `api/v1/auth/router.py` | Bündel 1 (gleiche Datei) |

### Welle 3 — mittelgroß, je ein eigener Strang

| # | Bündel | Issues | Warum eigener PR |
|---|---|---|---|
| 9 | **A11y-Kette** | #1094 → #1095 → #1096 | Drei aufeinander aufbauende Schritte: Helper + Backfill, dann E2E-Journey, dann DoD-Kopplung im Spec. #1096 kann erst benennen, was 1094/1095 geschaffen haben. |
| 10 | **API-Oberfläche** | #1124, #1137 | Zwei additive Endpunkt-/Feld-Erweiterungen, beide vom Android-Client getrieben, beide mit OpenAPI-Auswirkung |
| 11 | **MCP** | #1098, #1121 | Substrat-Layer exponieren + Katalog-Tools tenant-fähig machen; beide ändern den öffentlichen MCP-Vertrag |

### Eigene Sprints (nicht in den Sweep)

- **#1061** ADR-008-Konsolidierung — Planung liegt bereits vor (#1117 gemergt: Requirements + F-6..F-10). Das ist ein Sprint, kein Bündel.
- **#779** `/api/v2` — siehe Entscheidungstabelle oben.

## Ausführungsweg pro Bündel

Für jedes Bündel dieselbe Kette, die sich in #1138/#1143 bewährt hat:

1. `issue-orchestrate` für das führende Issue (liest Issue + Kommentare, zerlegt in Arbeitspakete, legt das Audit-Artefakt an)
2. Implementierung durch den passenden Spezialisten (Backend → `fullstack-developer`, Test-Tier → die jeweiligen Generatoren)
3. **Rot-zuerst-Nachweis** im browserfreien Selftest-Tier bzw. als Unit-Test, bevor der Fix steht
4. `quality-gate` lokal
5. `pull-request-create` → `code-review` → Befunde abarbeiten → `pull-request-merge`

Der Review-Schritt ist nicht optional: In beiden PRs dieser Session hat er echte
Defekte gefunden (einmal einen Guard, der still nichts geprüft hätte; einmal einen
Selftest, der einen unmöglichen Zustand zertifizierte).

## Merge-Reihenfolge

Innerhalb einer Welle beliebig, aber **immer einzeln** und mit Rebase dazwischen
(`strict: true`). Zwischen den Wellen die Voraussetzungen aus der Tabelle beachten.
Bei Renovate-Stau: `gh pr update-branch` statt Rebase — erzeugt einen Merge-Commit,
keine History-Umschreibung, und die Checks laufen sofort an.

## Aufwandsschätzung

| Welle | PRs | Implementierung | Merge-Wanduhr |
|---|---|---|---|
| 1 | 4 | ~4 h | ~1,5 h |
| 2 | 4 | ~6 h | ~1,5 h |
| 3 | 3 | ~12 h | ~1 h |
| **Summe** | **11** | **~22 h** | **~4 h** |

Ohne Bündelung: dieselben ~22 h Implementierung, aber ~8 h Merge-Wanduhr.
