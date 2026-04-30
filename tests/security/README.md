# `tests/security/`

Verbindliche Artefakte für das automatisierte DAST-Setup nach **NFR-014 (Nuclei)** und **NFR-015 (OWASP ZAP)**. Dieser Ordner ist die einzige Quelle für Templates, Suppressions, Rules und Skripte, die in CI gegen die laufende Anwendung ausgeführt werden.

| Pfad | Spec | Phase | Inhalt |
|---|---|---|---|
| `nuclei-templates/` | [NFR-014 §3.2](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md#32-eigene-templates) | 2 | Projekt-eigene YAML-Templates: Security-Headers, CORS, Debug-Endpoints, Tenant-Leak, JWT-Leak, Source-Map. |
| `nuclei-suppressions.yaml` | [NFR-014 §6.1](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md#61-false-positive-suppression) | 1 (skeleton) | Versionierte False-Positive-Suppressions. Pflicht-Felder: `template_id`, `reason`, `expires`, `approved_by`. |
| `zap-rules.tsv` | [NFR-015 §6.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#61-zap-rules-tuning) | 1 (skeleton) | ZAP-Regelanpassungen für Baseline + Full-Scan. Format: `<PluginID>\t<THRESHOLD>\t<Confidence>\t<Note>`. |
| `zap-api-rules.tsv` | [NFR-015 §6.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#61-zap-rules-tuning) | 1 (skeleton) | Wie oben, aber für `action-api-scan`. |
| `zap-context.xml` | [NFR-015 §3.2](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#32-zap-auth-konfiguration-jwt-basiert) | 3 | ZAP-Context: registriert HttpSender + Passive-Skripte, definiert Excludes für öffentliche Endpunkte. |
| `zap-scripts/jwt-httpsender.js` | [NFR-015 §3.2](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#32-zap-auth-konfiguration-jwt-basiert) | 3 | HttpSender-Skript, das auf jeden Folgerequest das Bearer-Token setzt und bei `401` einen Refresh triggert. |
| `zap-scripts/cross-tenant-passive.js` | [NFR-015 §3.3](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#33-cross-tenant-negativtests) | 3 | Passive-Rule, die JWT-Tenant gegen URL-Tenant prüft und Cross-Tenant-Zugriffe als Critical raised. |
| `zap-setup/test-identities.yaml` | [NFR-015 §3.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#31-test-identitäten) | 1 | Daten-Definition (Tenants, Users, Memberships) für die ZAP-Test-Identitäten. |
| `zap-setup/seed-test-identities.sh` | [NFR-015 §3.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#31-test-identitäten) | 1 | Idempotentes Bash-Setup: Registriert Users via `POST /auth/register`, legt Tenants an, lädt Mitglieder über Invitation-Flow ein. Keine direkten DB-Zugriffe. |
| `zap-setup/seed-cross-tenant.sh` | [NFR-015 §3.3](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#33-cross-tenant-negativtests) | 3 | Per-Run-Setup: Login pro Test-Identität, Resource-Erzeugung in Tenant α, Token-Export für ZAP. |

## Phasen-Lieferung

Foundation (diese PR, **Phase 1**) liefert nur die Skelett-Dateien und das Verzeichnislayout. Die mit Phase 2/3 markierten Artefakte werden in den Folge-PRs befüllt:

- **Phase 2 — NFR-014 (Nuclei)**: Templates, Workflows, Wrapper-Skripte, Triage-Doku.
- **Phase 3 — NFR-015 (OWASP ZAP)**: Context, Skripte, Setup, Workflows, Spec-Drift-Detection.

## Pflicht-Konventionen

- Eigene Templates / Skripte werden im Pre-Commit-Hook syntaktisch validiert (siehe Phase 2 / 3).
- Suppressions und IGNORE-Regeln haben **immer** ein `expires`-Datum (max. 12 Monate) und einen `approved_by`. Abgelaufene Einträge führen ab Phase 2 zu CI-Warnings, nach 30 Tagen Karenz zu einem Fail.
- Test-Identitäten für authentifizierte Scans werden ausschliesslich über externes Tooling unter [`zap-setup/`](zap-setup/README.md) angelegt — über die öffentliche Backend-REST-API, nicht über produktive Backend-Module. Der Pre-Deploy-Check (NFR-015 §3.1) verifiziert, dass keine `@zap.kamerplanter.example`-Konten in Produktions-DB-Snapshots erscheinen.
