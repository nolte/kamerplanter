# Deployment

Kamerplanter kann auf verschiedene Arten betrieben werden — von einem einzelnen `docker compose up` auf dem eigenen Rechner bis hin zu einem voll verwalteten Kubernetes-Cluster.

## Welche Methode passt zu dir?

| Szenario | Empfohlene Methode |
|----------|-------------------|
| Ausprobieren, ein Nutzer, Heimnetz | [Docker Compose Schnellstart](docker-quickstart.md) |
| Dauerbetrieb auf Raspberry Pi / NAS | [Docker Compose Dauerbetrieb](docker-dauerbetrieb.md) |
| Mehrere Nutzer, Hochverfügbarkeit, professioneller Betrieb | [Kubernetes + Helm](kubernetes.md) / [ArgoCD](argocd.md) |

!!! danger "Vor jedem Rollout: Pflicht-Secrets setzen"
    Unabhängig vom gewählten Weg verweigert das Backend den Start, sobald `DEBUG=false` gesetzt ist und `JWT_SECRET_KEY`, `FERNET_KEY` oder `ERASURE_TOMBSTONE_SALT` fehlen. Jede Deployment-Seite in diesem Abschnitt zeigt, wo diese Werte hingehören — die vollständige Referenz steht in der [Konfigurationsmatrix](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

## In diesem Abschnitt

### Docker Compose

- [Docker installieren](docker-installation.md) — Docker auf Windows, macOS, Linux oder Raspberry Pi einrichten
- [Docker Compose Schnellstart](docker-quickstart.md) — In 5 Minuten zur laufenden Instanz
- [Docker Compose Dauerbetrieb](docker-dauerbetrieb.md) — Updates, Backups und Zugriff von anderen Geraeten

### Kubernetes

- [Betriebsprofile](betriebsprofile.md) — Welche Komponenten brauche ich? Vergleich von Minimal bis SaaS
- [Konfigurationsmatrix](konfigurationsmatrix.md) — Erschöpfende Referenz aller Funktionen mit Schalter, Pflicht-Secrets und Ressourcenauswirkung
- [Kubernetes](kubernetes.md) — Cluster-Voraussetzungen und Kamerplanter deployen
- [Helm Charts](helm.md) — Chart-Struktur, Konfiguration und Anpassung
- [ArgoCD](argocd.md) — GitOps-basiertes Deployment
- [CI/CD](ci-cd.md) — Automatische Builds und Deployments mit GitHub Actions
- [Bilderkennung in Betrieb nehmen](inference-service.md) — Selbst gehostete Pflanzen-Bilderkennung (optional)
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablenreferenz
