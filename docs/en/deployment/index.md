# Deployment

Kamerplanter can be operated in different ways. This section describes running it on a Kubernetes cluster with Helm charts.

## When do I need Kubernetes?

| Scenario | Recommended method |
|----------|-------------------|
| Trying it out, single user, home network | [Docker Compose](../getting-started/quickstart.md) |
| Permanent operation on Raspberry Pi / NAS | [Docker Compose (Release)](../getting-started/first-deployment.md) |
| Multiple users, high availability, professional use | **Kubernetes + Helm** (this section) |

Kubernetes is worth it if you already run a cluster or want to manage multiple services centrally. For simple home use, Docker Compose is the better choice.

## In this section

- [Kubernetes](kubernetes.md) — Cluster prerequisites and deploying Kamerplanter
- [Helm Charts](helm.md) — Chart structure, configuration, and customization
- [CI/CD](ci-cd.md) — Automated builds and deployments with GitHub Actions
