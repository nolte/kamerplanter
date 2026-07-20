# Deployment

Kamerplanter can be operated in different ways — from a single `docker compose up` on your own machine to a fully managed Kubernetes cluster.

## Which method is right for you?

| Scenario | Recommended method |
|----------|-------------------|
| Trying it out, single user, home network | [Docker Compose Quick Start](docker-quickstart.md) |
| Permanent operation on Raspberry Pi / NAS | [Docker Compose Permanent Operation](docker-dauerbetrieb.md) |
| Multiple users, high availability, professional use | [Kubernetes + Helm](kubernetes.md) / [ArgoCD](argocd.md) |

!!! danger "Set the mandatory secrets before every rollout"
    Regardless of the path you choose, the backend refuses to start once `DEBUG=false` is set and `JWT_SECRET_KEY`, `FERNET_KEY`, or `ERASURE_TOMBSTONE_SALT` is missing. Every deployment page in this section shows where these values belong — the complete reference lives in the [Configuration Matrix](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

## In this section

### Docker Compose

- [Docker Installation](docker-installation.md) — Set up Docker on Windows, macOS, Linux, or Raspberry Pi
- [Docker Compose Quick Start](docker-quickstart.md) — Up and running in 5 minutes
- [Docker Compose Permanent Operation](docker-dauerbetrieb.md) — Updates, backups, and access from other devices

### Kubernetes

- [Deployment Profiles](betriebsprofile.md) — Which components do I need? Comparing Minimal to SaaS
- [Configuration Matrix](konfigurationsmatrix.md) — Exhaustive reference of every feature with its switch, mandatory secrets, and resource impact
- [Kubernetes](kubernetes.md) — Cluster prerequisites and deploying Kamerplanter
- [Helm Charts](helm.md) — Chart structure, configuration, and customization
- [ArgoCD](argocd.md) — GitOps-based deployment
- [CI/CD](ci-cd.md) — Automated builds and deployments with GitHub Actions
- [Setting Up Image Recognition](inference-service.md) — Self-hosted plant image recognition (optional)
- [Environment Variables](../reference/environment-variables.md) — Complete variable reference
