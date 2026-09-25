# Pre-analysis — issue #1756

- Issue: https://github.com/nolte/kamerplanter/issues/1756 (author `nolte`, repository owner → trusted)
- Classification: `security` (secondary: `infra`) — the dev cluster ingress answers on every workstation interface.
- Requirements gate: operator override (autonomous sweep 2026-09-24/25, every gate pre-approved); the issue carries three testable acceptance criteria.
- Route: implement directly (one outcome, one PR strand, no roadmap item).

## Measurements (established)

- `kind-config.yaml:21-27` — two `extraPortMappings` without `listenAddress`.
- kind docs (kind.sigs.k8s.io/docs/user/configuration, via context7): `listenAddress` is the host bind address, "0.0.0.0 is the current default".
- Live: `docker ps` → `kamerplanter-control-plane … 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 127.0.0.1:45383->6443/tcp`; `ss -ltn` → `0.0.0.0:80`, `0.0.0.0:443`. The API server is already loopback (kind default `apiServerAddress: 127.0.0.1`).
- Guard `src/backend/tests/unit/guards/test_published_ports_bind_loopback.py:50-53` names kind as a blind spot.
- Further kind configs in the corpus: three heredoc examples in `spec/nfr/NFR-004_Lokale-Entwicklungsumgebung.md` (bash fences, ~L199, ~L1437, ~L1512) plus a commented troubleshooting hint (~L1262).
- No documented flow reaches the dev ingress from another host (`git grep` over `docs/*/development`, Taskfiles, skaffold, values-dev: ingress host `kamerplanter.local`, access via Skaffold port-forward on localhost).

## Work packages

| id | problem | acceptance | files | specialist |
|----|---------|-----------|-------|------------|
| WP1 | guard reads kind cluster configs (YAML files, Markdown YAML fences, heredocs) and refuses a mapping without loopback `listenAddress`, fail closed; red first | red against develop via the tracked-file sweep | guard module | generalist (strand agent, operator brief) |
| WP2 | bind every mapping to 127.0.0.1 | guard green | `kind-config.yaml`, NFR-004 examples | generalist |
| WP3 | docs: recreate-cluster note + LAN opt-out explanation | DE/EN mirrored | `docs/{de,en}/development/local-setup.md` | generalist |

Dependencies: WP1 → WP2 → WP3.

## Risks

- Existing clusters keep the 0.0.0.0 bind until recreated (kind bakes port mappings into the node container).
- kind configs support no environment interpolation, so a #1757-style `KAMERPLANTER_BIND_ADDRESS` opt-in is not available in the file itself.
