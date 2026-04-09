# Deployment

Kamerplanter can be operated in different ways — from a single `docker compose up` on your own machine to a fully managed Kubernetes cluster.

## Which method is right for you?

| Scenario | Recommended method |
|----------|-------------------|
| Trying it out, single user, home network | [Docker Compose Quick Start](docker-quickstart.md) |
| Permanent operation on Raspberry Pi / NAS | [Docker Compose Permanent Operation](docker-dauerbetrieb.md) |
| Multiple users, high availability, professional use | [Kubernetes + Helm](kubernetes.md) |

## In this section

### Docker Compose

- [Docker Installation](docker-installation.md) — Set up Docker on Windows, macOS, Linux, or Raspberry Pi
- [Docker Compose Quick Start](docker-quickstart.md) — Up and running in 5 minutes
- [Docker Compose Permanent Operation](docker-dauerbetrieb.md) — Updates, backups, and access from other devices

### Kubernetes

- [Deployment Profiles](deployment-profiles.md) — Which components do I need? Comparing Minimal to SaaS
- [Kubernetes](kubernetes.md) — Cluster prerequisites and deploying Kamerplanter
- [Helm Charts](helm.md) — Chart structure, configuration, and customization
- [ArgoCD](argocd.md) — GitOps-based deployment
- [CI/CD](ci-cd.md) — Automated builds and deployments with GitHub Actions
