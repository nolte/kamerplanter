# Local Setup

Skaffold is the only tool for the local development workflow. It handles image building and deployment/updates in the Kubernetes cluster. No manual `docker build`/`kubectl apply` commands.

!!! note "Placeholder"
    This content will be elaborated in a subsequent step.

## Starting Development

```bash
# Full stack (manual trigger)
skaffold dev --trigger=manual --port-forward

# Backend only
skaffold dev --trigger=manual --port-forward -p backend-only

# With debugger
skaffold debug --port-forward
```

## Port Forwards

| Service | Local Port |
|---------|-----------|
| Frontend | 3000 |
| Backend API | 8000 |
| ArangoDB UI | 8529 |
| Home Assistant | 8123 |
