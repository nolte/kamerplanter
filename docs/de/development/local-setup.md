# Lokales Setup

Skaffold ist das einzige Werkzeug für den lokalen Entwicklungsprozess. Es übernimmt Image-Building und Deployment/Update im Kubernetes-Cluster. Keine manuellen `docker build`/`kubectl apply`-Befehle.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Voraussetzungen

- Docker Desktop oder ein lokaler Kubernetes-Cluster (Kind, k3s, minikube)
- Skaffold installiert
- Node.js 25+ (via asdf, `.tool-versions` in `src/frontend/`)
- Python 3.14+

## Entwicklungsstart

```bash
# Vollstack (manueller Trigger)
skaffold dev --trigger=manual --port-forward

# Nur Backend
skaffold dev --trigger=manual --port-forward -p backend-only

# Mit Debugger
skaffold debug --port-forward
```

## Port-Weiterleitungen

| Service | Lokaler Port |
|---------|-------------|
| Frontend | 3000 |
| Backend API | 8000 |
| ArangoDB UI | 8529 |
| Home Assistant | 8123 |
