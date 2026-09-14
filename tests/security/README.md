# `tests/security/`

Verbindliche Artefakte für das automatisierte DAST-Setup nach **NFR-014 (Nuclei)** und **NFR-015 (OWASP ZAP)**. Dieser Ordner ist die einzige Quelle für Templates, Suppressions, Rules und Skripte, die in CI gegen die laufende Anwendung ausgeführt werden.

| Pfad | Spec | Phase | Inhalt |
|---|---|---|---|
| `nuclei-templates/` | [NFR-014 §3.2](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md#32-eigene-templates) | 2 | Projekt-eigene YAML-Templates: Security-Headers, CORS, Debug-Endpoints, Tenant-Leak, JWT-Leak, Source-Map. |
| `nuclei-suppressions.yaml` | [NFR-014 §6.1](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md#61-false-positive-suppression) | 1 (skeleton) | Versionierte False-Positive-Suppressions. Pflicht-Felder: `template_id`, `reason`, `expires`, `approved_by`. |
| `zap-rules.tsv` | [NFR-015 §6.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#61-zap-rules-tuning) | 3 | Unterdrückungen für das Baseline- und Full-Scan-Profil. Format: `<PluginID>\t<THRESHOLD>\t<Confidence>\t<Note>` — siehe den Dateikopf, er ist die ausführliche Fassung. |
| `zap-api-rules.tsv` | [NFR-015 §6.1](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md#61-zap-rules-tuning) | 3 | Dasselbe für das API-Scan-Profil. |
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
- Suppressions und IGNORE-Regeln haben **immer** ein `expires`-Datum (max. 12 Monate) und einen `approved_by`. Abgelaufene Einträge führen zu CI-Warnings, nach 30 Tagen Karenz zu einem Fail — und greifen dann auch nicht mehr, damit der verdeckte Fund im selben Lauf wieder auftaucht.
- Test-Identitäten für authentifizierte Scans werden ausschliesslich über externes Tooling unter [`zap-setup/`](zap-setup/README.md) angelegt — über die öffentliche Backend-REST-API, nicht über produktive Backend-Module. Der Pre-Deploy-Check (NFR-015 §3.1) verifiziert, dass keine `@zap.kamerplanter.example`-Konten in Produktions-DB-Snapshots erscheinen.

### ZAP-Regeldateien: wer sie liest, und warum nicht ZAP (seit 2026-09-14, #1376/#1389)

`zap-rules.tsv` und `zap-api-rules.tsv` gehen **ausschliesslich** an
`scripts/security/zap_gate.py --rules`. Sie werden **nicht** per `-c`/`-u` an die
ZAP-Wrapper übergeben und **nicht** über `zaproxy/action-*` (`rules_file_name:`,
`cmd_options:`) eingespeist. Grund, gemessen an `/zap/zap-api-scan.py` im
digest-gepinnten Image:

```python
scan_policy = 'API-Minimal'
if config_dict:
    scan_policy = 'Default Policy'
    zap.ascan.enable_all_scanners(scanpolicyname=scan_policy)
```

Der erste Eintrag — gleich welcher — ersetzt die 23-Regeln-Policy durch den
vollständigen aktiven Regelsatz, und die einzige Form, die ZAP kennt, ist „Regel
überall aus". Der Gate verwirft stattdessen einzelne **Instanzen** nach URL.

Daraus folgen drei Pflichten für jede `IGNORE`-Zeile, die
`src/backend/tests/unit/guards/` in der **required** Lane `Write-route and tree
guards` durchsetzt:

1. `# expires YYYY-MM-DD — approved by <rolle>`;
2. `scope=<URL-Regex>`, unverankert (`re.search`) und ohne impliziten Standard —
   regelweit heisst ausgeschrieben `scope=.*`;
3. als THRESHOLD nur `IGNORE`; `WARN`/`FAIL`/`INFO`/`PASS` wären wirkungslos und
   werden mit Meldung zurückgewiesen.

Das Ablaufdatum selbst prüft die required Lane bewusst **nicht** — sie läuft bei
jedem Push in jedem Branch, und eine kalenderabhängige Zusicherung dort würde ab
einem bekannten Datum jeden Merge im Repository blockieren. Durchgesetzt wird der
Ablauf dort, wo die Unterdrückung wirkt: in den beiden ZAP-Lanes.
