# Requirements — Aktiv-Tenant-Auflösung auf globalen Routen (Issue #1091, REQ-049 A1)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **Was:** Der Personal-Tenant-Platzhalter in `get_active_tenant_key` /
  `get_creating_tenant_key` / `get_active_tenant_context`
  (`src/backend/app/common/auth.py`) wird durch einen echten
  Aktiv-Tenant-Mechanismus ersetzt: ein `X-Active-Tenant`-Header trägt auf
  globalen (pfadlos tenant-bewussten) Routen den Tenant, in dem der Caller
  gerade handelt. Schließt die offene REQ-049-Designentscheidung A1 (#808)
  auf der #780-Zwei-Achsen-Basis. Zusätzlich (Kopplung SEC-005/#1113): der
  interaktive Create von Species und Cultivar wird rollen-gegated, damit das
  Org-Kontext-Landing das latente Viewer-Write-Loch nie öffnet.
- **Für wen:** Org-Mitglieder (Gemeinschaftsgärten, REQ-024/O-4), die auf dem
  globalen Katalog ihre org-eigenen Arten/Sorten sehen und als Org anlegen
  wollen; Single-Tenant-Nutzer bleiben unverändert.
- **Explizit außerhalb:**
  - **MCP-Katalog-Tools** bleiben global-only (Umzug auf `TenantToolInput` =
    öffentliche Contract-Änderung) → eigenes Folge-Issue.
  - **Favoriten** bleiben persönlich-über-Tenants (frühere Operator-Entscheidung);
    der Header bindet sie NICHT um.
  - **`/t/{slug}/`-Routen**: dort bindet weiterhin der Pfad (`get_current_tenant`).
  - Keine `/t/{slug}/`-Zwillinge der Katalog-Routen (Alternative verworfen).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `4` (4 verbraucht)
- `U_gate = min_d c_d` = **0.8**
- Termination: `saturation` nach Teach-back 2026-08-10 (alle vier Fragen beantwortet, Gesamtbild bestätigt)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification | Q1 (Header) + Q2 (403) + Teach-back |
| `non_functional` | yes | 0.8 | specification | Orakelfreiheit, Fail-safe-Erhalt; Teach-back |
| `constraints` | yes | 0.85 | interpretation | Ein-Resolver-Regel (Docstring-Zusage „replace only this function"); #780-Achse |
| `domain_objects` | yes | 0.85 | interpretation | TenantContext, Membership, TenantRole, tenant_union_predicate |
| `actors` | yes | 0.85 | interpretation | Org-Mitglied (viewer/grower/lead), Single-Tenant-Nutzer, anonym/light |
| `acceptance_criteria` | yes | 0.8 | specification | Issue-ACs + Q2/Q4-Präzisierungen; Teach-back |
| `edge_cases` | yes | 0.8 | specification | Ungültiger Header (Q2), Austritt aus Org (403 statt still), anonym (Q1) |
| `scope_boundaries` | yes | 0.9 | interpretation | Q3/Q4: MCP-Split, Favoriten/Pfad-Routen unberührt |

## Requirements

### R1 — Signal: `X-Active-Tenant`-Header `confirmed`

WHEN eine globale (pfadlos tenant-bewusste) Route aufgerufen wird UND der
Request einen `X-Active-Tenant`-Header (Tenant-Slug) trägt, THE SYSTEM SHALL
den aktiven Tenant aus diesem Header auflösen. WITHOUT Header SHALL das
bisherige Verhalten gelten (Personal-Tenant); anonym/light-mode → `""`
(global-only, fail-safe unverändert — Abwesenheit von Kontext verengt, nie
erweitert). *(Q1, Teach-back)*

### R2 — Ungültiger Header → 403, orakelfrei `confirmed`

WHEN der Header einen Tenant benennt, in dem der Caller kein **aktives**
Membership hat, ODER einen unbekannten Slug, THE SYSTEM SHALL mit 403
antworten — mit **identischer** Antwort für beide Fälle (kein
Existenz-Orakel) und niemals still auf Personal-Tenant oder global
zurückfallen (die stille Kontext-Verwechslung ist genau der Fehler, den
dieses Feature behebt). *(Q2, Teach-back)*

### R3 — Ein Resolver für Read, Write-Stamping und Rolle `confirmed`

THE SYSTEM SHALL die Auflösung ausschließlich in dem einen bestehenden
Resolver ändern: `get_active_tenant_key` (Read-Scope),
`get_creating_tenant_key` (Write-Stamping, identisches Funktionsobjekt) und
`get_active_tenant_context` (Rolle + Admin-Scopes aus dem Membership des
**aktiven** Tenants — ein Org-Viewer erhält die Viewer-Rolle der Org, nie die
Lead-Rolle seines Personal-Tenants) lösen identisch auf; Read-Sichtbarkeit und
Ownership-Stempel können nie divergieren. *(Docstring-Zusage; Teach-back)*

### R4 — Sichtbarkeit beide Richtungen `confirmed`

WHEN ein Org-Mitglied mit gültigem Header liest, THE SYSTEM SHALL global +
org-eigene Zeilen liefern; fremde Tenants (inkl. des eigenen Personal-Tenants
anderer) bleiben verborgen (#324 beide Richtungen). WHEN es schreibt, SHALL
der Create mit dem **aktiven** Tenant gestempelt werden.

### R5 — Create-Rollen-Gate (SEC-005/#1113, im selben Strang) `confirmed`

WHEN ein interaktiver Species- oder Cultivar-Create im aktiven Tenant erfolgt,
THE SYSTEM SHALL die Domänen-Rolle prüfen (`MembershipEngine.can_edit_resource`;
Viewer → 403), mit `get_active_tenant_context` + Platform-Admin-Bypass analog
PUT/DELETE — Species und Cultivar gemeinsam, damit keine dritte Gate-Variante
entsteht. *(Scope-Erweiterung, operator-bestätigt; verhindert das
SEC-005-Fenster.)*

### R6 — Geltungsbereich `confirmed`

Der Header wirkt auf genau die heutigen Konsumenten des Resolvers
(Species-/Cultivar-Katalog, botanical-family-Fläche). Favoriten
(persönlich-über-Tenants) und alle `/t/{slug}/`-Routen bleiben unberührt;
künftige Konsumenten opt-in per `Depends`. *(Q4, Teach-back)*

### R7 — Design festgehalten `confirmed`

Ein ADR dokumentiert die Signal-Entscheidung (Header vs. JWT-Claim vs.
Routen-Zwillinge, mit Begründung), und REQ-049 wird um den
Aktiv-Tenant-Mechanismus ergänzt (A1 geschlossen). *(Issue-AC; Teach-back)*

## Surviving assumptions / open risks

- **Header-Name/Format** (`assumed`): `X-Active-Tenant` mit Tenant-**Slug**
  (menschenlesbar, wie `/t/{slug}/`); der Resolver mappt Slug→Key. Falls die
  Implementierung Key bevorzugt, im ADR begründen.
- **Frontend-Switcher** (`assumed`): Das Frontend setzt den Header zentral im
  API-Client, sobald ein Org-Kontext gewählt ist; UI-Arbeit dafür ist Teil
  dieses Strangs nur, soweit der Switcher bereits existiert — sonst Folge-Issue
  (bei Dekomposition prüfen).
- **CORS** (`assumed`): der neue Header muss in `Access-Control-Allow-Headers`
  aufgenommen werden, sonst schickt der Browser ihn nie ab.

## Consumer contract

`U_gate = 0.8 = τ_high` — Dekomposition darf aufsetzen. Kernentscheidungen
R1–R7 teach-back-bestätigt 2026-08-10 (issue-orchestrate-Lauf zu #1091).
