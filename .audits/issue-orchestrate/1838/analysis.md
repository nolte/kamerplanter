# Pre-analysis — #1838 e2e: generate the E2E stack's Fernet key per run

- Classification: `security` (secondary `infra`). Requirements gate: operator override (autonomous strand B). Route: implement directly.
- Cause (established): `git show origin/develop:docker-compose.e2e.yml` carries one real-format Fernet key at 4 services (backend, celery-worker, backend-full, celery-worker-full); tree scan finds no other real-format Fernet key.
- WP1 per-run key helper + compose interpolation; WP2 wire every stack-starting caller; WP3 guard over tracked files; WP4 convention (BACKEND.md §16.3) + docs. Specialist: generalist (orchestrator), reviewed by code-security-reviewer.
- Out of scope, filed: #1859 (worker Fernet gate), #1860 (other credential shapes).
