# Deployment

Kamerplanter kann auf verschiedene Arten betrieben werden — von einem einzelnen `docker compose up` auf dem eigenen Rechner bis hin zu einem voll verwalteten Kubernetes-Cluster.

## Welche Methode passt zu dir?

| Szenario | Empfohlene Methode |
|----------|-------------------|
| Ausprobieren, ein Nutzer, Heimnetz | [Docker Compose Schnellstart](docker-quickstart.md) |
| Dauerbetrieb auf Raspberry Pi / NAS | [Docker Compose Dauerbetrieb](docker-dauerbetrieb.md) |
| Mehrere Nutzer, Hochverfügbarkeit, professioneller Betrieb | [Kubernetes + Helm](kubernetes.md) |

## In diesem Abschnitt

### Docker Compose

- [Docker installieren](docker-installation.md) — Docker auf Windows, macOS, Linux oder Raspberry Pi einrichten
- [Docker Compose Schnellstart](docker-quickstart.md) — In 5 Minuten zur laufenden Instanz
- [Docker Compose Dauerbetrieb](docker-dauerbetrieb.md) — Updates, Backups und Zugriff von anderen Geraeten

### Kubernetes

- [Betriebsprofile](betriebsprofile.md) — Welche Komponenten brauche ich? Vergleich von Minimal bis SaaS
- [Kubernetes](kubernetes.md) — Cluster-Voraussetzungen und Kamerplanter deployen
- [Helm Charts](helm.md) — Chart-Struktur, Konfiguration und Anpassung
- [ArgoCD](argocd.md) — GitOps-basiertes Deployment
- [CI/CD](ci-cd.md) — Automatische Builds und Deployments mit GitHub Actions
