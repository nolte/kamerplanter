# Debugging

This page explains how to debug the backend and frontend in the local development environment. All methods assume a running Skaffold setup (see [Local Setup](local-setup.md)).

---

## Backend Debugging with debugpy

The backend container image includes [debugpy](https://github.com/microsoft/debugpy) — the Python debugger used by VS Code, PyCharm, and other IDEs for remote debugging.

### Starting debug mode

```bash
skaffold debug --port-forward
```

The `debug` profile in `skaffold.yaml` sets `DEBUGPY_ENABLED=true` as a Docker build argument. The container then starts debugpy and optionally waits for a connection.

Debugpy listens on port `5678`. Skaffold does not forward this port automatically — it must be set up manually:

```bash
kubectl port-forward deployment/kamerplanter-backend 5678:5678
```

### VS Code — launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Kamerplanter Backend (Remote)",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/src/backend",
          "remoteRoot": "/app"
        }
      ],
      "justMyCode": true
    }
  ]
}
```

### PyCharm — Remote debug configuration

1. Menu: `Run` → `Edit Configurations` → `+` → `Python Debug Server`
2. Host: `localhost`, Port: `5678`
3. Path Mappings: `src/backend/app` → `/app/app`
4. Start the configuration, then run `skaffold debug --port-forward`

### Breakpoints and log output

The backend server runs with uvicorn in `--reload` mode. Structured logs are output via [structlog](https://www.structlog.org/):

```python
import structlog

log = structlog.get_logger()

async def create_species(data: CreateSpeciesRequest) -> Species:
    log.info("creating_species", scientific_name=data.scientific_name)
    # Set a breakpoint here
    result = await self.repo.create(data)
    log.info("species_created", key=result.key)
    return result
```

### Viewing pod logs

Without a debugger, logs often provide enough information:

```bash
# Backend logs (last 100 lines, then follow live)
kubectl logs -l app=kamerplanter-backend --tail=100 -f

# Celery worker logs
kubectl logs -l app=kamerplanter-worker --tail=100 -f

# Errors only
kubectl logs -l app=kamerplanter-backend --tail=200 | grep '"level":"error"'
```

---

## Frontend Debugging

### Browser DevTools

Most frontend issues can be resolved with browser developer tools:

- **Console** (`F12` → Console): JavaScript errors, unhandled promise rejections, i18n warnings for missing keys
- **Network** (`F12` → Network): API requests, HTTP status codes, request/response bodies
- **Redux DevTools**: Track Redux state changes (browser extension for Chrome/Firefox required)

### React Developer Tools

The [React DevTools](https://react.dev/learn/react-developer-tools) browser extension allows you to:
- Inspect the component tree
- View props and state of individual components
- Use the re-render profiler for performance analysis

### Vite Source Maps

In development mode (Vite dev server, port `5173`), source maps are active. Breakpoints can be set directly in TypeScript files in the browser debugger.

### Common Frontend Issues

??? question "API requests fail with 401"
    The JWT token has expired or the `kp_active_tenant_slug` entry in `localStorage` is missing. Check in Browser DevTools under `Application → Local Storage`:
    - `kp_active_tenant_slug` must be set to a valid tenant slug (e.g. `demo`)
    - Run through the login flow again, or manually delete the token and log in again

??? question "i18n keys are displayed as raw text"
    Missing translation keys are logged as a warning in the console: `i18next: key "pages.myPage.missingKey" for language "en" not found`. Add the key in `src/i18n/locales/en/translation.json` and `de/translation.json`.

??? question "Redux state is not updating"
    Use Redux DevTools to check dispatched actions and state changes. Common causes: wrong slice action exported, missing Immer mutation, `createSelector` memoization issue (unstable reference from a custom hook missing `useMemo`).

??? question "MSW mocks are not active in the browser"
    The Mock Service Worker is only active during tests. In development mode, requests hit the real backend proxy at `/api`. If the backend API is not reachable, check the Skaffold port forward.

---

## ArangoDB Web UI

The ArangoDB web interface is available at [http://localhost:8529](http://localhost:8529):

| Field | Value |
|-------|-------|
| Username | `root` |
| Password | `rootpassword` |
| Database | `kamerplanter` |

Useful AQL queries for debugging:

```aql
// Show all plant species
FOR s IN species RETURN s

// Check connections for a tenant
FOR v, e IN 1..1 OUTBOUND 'tenants/demo' GRAPH 'kamerplanter_graph'
  RETURN { vertex: v._id, edge: e._from }

// Last 10 tasks
FOR t IN tasks
  SORT t.created_at DESC
  LIMIT 10
  RETURN t
```

---

## Debugging Celery Tasks

Background tasks (Celery Beat + Worker) have separate logs:

```bash
# Celery worker
kubectl logs -l app=kamerplanter-worker -f

# Celery Beat (scheduler)
kubectl logs -l app=kamerplanter-beat -f
```

Trigger a task manually (direct Python call in the backend pod):

```bash
kubectl exec -it deployment/kamerplanter-backend -- python -c "
from app.tasks.care_reminders import generate_due_care_reminders
result = generate_due_care_reminders.delay()
print('Task ID:', result.id)
"
```

---

## Health Endpoints

The backend provides two health endpoints that are also useful for manual diagnostics:

```bash
# Liveness (is the process running?)
curl http://localhost:8000/api/v1/health/live

# Readiness (is the database reachable?)
curl http://localhost:8000/api/v1/health/ready
```

Expected response (both): `{"status": "ok"}` with HTTP 200.

---

## Common Error Scenarios

??? question "Backend pod in CrashLoopBackOff"
    1. Retrieve logs: `kubectl logs <pod-name> --previous`
    2. Common causes: Pydantic validation error at startup, missing environment variable, ArangoDB not yet ready
    3. Test the ArangoDB connection directly: `kubectl exec -it deployment/kamerplanter-backend -- python -c "from app.data_access.arango.connection import ArangoConnection; from app.config.settings import Settings; c = ArangoConnection(Settings()); c.connect(); print('OK')"`

??? question "Seed data was not created"
    The migration runs as an init container. View its logs:
    ```bash
    kubectl logs <backend-pod-name> -c init-seed
    ```

??? question "Frontend shows a blank page with no error message"
    Check the browser console for JavaScript errors. Typical cause: a Redux action is dispatched with an `undefined` payload, causing a reducer error.

## See also

- [Local Setup](local-setup.md)
- [Testing](testing.md)
- [Code Standards](code-standards.md)
