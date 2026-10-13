# Entwickler-Tooling-Spezifikationen

Dieses Verzeichnis enthält Spezifikationen für **Werkzeuge, die Entwickler und Claude Code zusätzlich zur Codebasis nutzen**.

Abgrenzung:

| Verzeichnis | Inhalt |
|-------------|--------|
| `spec/req/`, `spec/nfr/`, `spec/ui-nfr/` | Fachliche und technische Anforderungen an das **Produkt** |
| `spec/style-guides/` | Code-Konventionen, durchgesetzt durch Linter/Compiler |
| **`spec/dev-tooling/` (dieses Verzeichnis)** | Tooling für den **Entwicklungsprozess**, nicht Teil des produktiven Stacks |

## Dokumente

| ID | Titel | Status |
|----|-------|--------|
| [DEVTOOL-001](MCP-SERVERS.md) | MCP-Server-Integration für Claude Code | Verbindlich |
| [DEVTOOL-002](PRECOMMIT-CONCURRENCY.md) | `task precommit` unter parallelen Arbeitskopien (#1641) | Messbericht |
| [DEVTOOL-003](INTEGRATION-DB-ISOLATION.md) | Integrationstest-Datenbanken unter parallelen Arbeitskopien (#1661) | Messbericht |
