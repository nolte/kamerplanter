# Deployment

Kamerplanter kann auf verschiedene Arten betrieben werden. Dieser Abschnitt beschreibt den Betrieb auf einem Kubernetes-Cluster mit Helm-Charts.

## Wann brauche ich Kubernetes?

| Szenario | Empfohlene Methode |
|----------|-------------------|
| Ausprobieren, ein Nutzer, Heimnetz | [Docker Compose](../getting-started/quickstart.md) |
| Dauerbetrieb auf Raspberry Pi / NAS | [Docker Compose (Release)](../getting-started/first-deployment.md) |
| Mehrere Nutzer, Hochverfügbarkeit, professioneller Betrieb | **Kubernetes + Helm** (dieser Abschnitt) |

Kubernetes lohnt sich, wenn du bereits einen Cluster betreibst oder mehrere Dienste zentral verwalten möchtest. Für den einfachen Heimgebrauch ist Docker Compose die bessere Wahl.

## In diesem Abschnitt

- [Kubernetes](kubernetes.md) — Cluster-Voraussetzungen und Kamerplanter deployen
- [Helm Charts](helm.md) — Chart-Struktur, Konfiguration und Anpassung
- [CI/CD](ci-cd.md) — Automatische Builds und Deployments mit GitHub Actions
