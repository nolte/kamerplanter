# ADR-008: mDNS/Zeroconf for Home Assistant Auto-Discovery

**Status:** Accepted
**Date:** 2026-04-24
**Deciders:** Kamerplanter Development Team

## Context

The Kamerplanter custom integration in Home Assistant currently requires manual URL entry to locate the backend. For the target audience — homelab and Raspberry-Pi users — this is an unnecessary hurdle: they typically don't know the IP of their container or the port of the FastAPI process. Compared with native HA integrations, the setup feels unpolished.

At the same time, Kamerplanter runs in very different network contexts (Docker Compose directly on the LAN, K3s with `hostNetwork`, standard Kubernetes with an overlay network, cloud). A discovery mechanism must respect this heterogeneity and must not inflict multicast overhead on cloud deployments where it would be ineffective anyway.

### Problem

- Manual URL entry is a real setup hurdle for the target audience (non-DevOps Home Assistant users).
- There is no portfolio-uniform discovery mechanism — any HA integration without discovery feels outdated.
- A naive solution (always announce) is useless in cloud deployments and misleading in standard Kubernetes clusters where multicast packets never leave the overlay network.

## Decision

**mDNS/Zeroconf announcement from the backend, opt-in via `MDNS_ENABLED`, with TXT records carrying the discovery metadata.**

### Architecture

```
Backend (FastAPI lifespan) ──▶ Zeroconf (UDP 5353) ──▶ Home Assistant
         │                                                     │
  `_kamerplanter._tcp.local.`                       `async_step_zeroconf`
         │                                                     │
  TXT: version, mode, api_path, instance_id ─────────▶ unique-ID check
                                                              │
                                                     pre-filled config entry
```

- **`zeroconf` Python library** as the announcer backend (pure Python, no C extensions, Apache 2.0).
- **Register on lifespan startup**, **unregister on shutdown** — stale announcements are impossible.
- **Opt-in** via `MDNS_ENABLED=false` (default). Helm explicitly sets `false`, Docker-Compose examples set `true`.
- **Secure by default** — no hostname leakage, admin-controlled `instance_id`, no secrets in TXT records.

### Why mDNS and not HTTP broadcast or SSDP?

| Criterion | mDNS (Zeroconf) | SSDP (UPnP) | HTTP broadcast |
|-----------|-----------------|-------------|----------------|
| HA native support | Excellent (`manifest.json` `zeroconf`) | OK (`ssdp`) | None |
| Uptake in target appliances | High (printers, NAS, Apple ecosystem) | Mostly media devices | None |
| Protocol complexity | Low (RFC 6762/6763) | High (XML, NOTIFY) | Trivial but fragile |
| Python library | `zeroconf` (mature) | `async_upnp_client` (HA-only dep) | — |
| Cloud scenarios | Opt-in disable | Same | Never |

mDNS is HA's standard route for LAN discovery. SSDP would be double the effort for no clear upside.

### Why opt-in rather than opt-out?

- Standard Kubernetes runs pods behind an overlay network that drops multicast. Default-on would make `zeroconf.register_service` do needless work and confuse operators with harmless warnings.
- In cloud deployments mDNS is simply non-functional (no LAN to announce on).
- Homelab and Docker-Compose users get the recommended setting through the example configuration and documentation — no real UX loss.

### Rejected alternatives

1. **DNS-SD via unicast DNS (DNSSEC):** requires DNS infrastructure that doesn't exist in a homelab.
2. **Custom broadcast-based mechanism:** no HA integration path; maintenance with no upside.
3. **HA scans a port range on the LAN:** long scans, security-hygiene concerns, not an HA-native pattern.
4. **No discovery — stay with manual URL:** still the fallback; as the only option it remains a persistent UX drawback.

## Consequences

### Positive

- Setup for HA users collapses to: start backend → HA surfaces the discovery → enter API key.
- Unique-ID via the `instance_id` prevents duplicate config entries on backend reinstall.
- The `zeroconf` library ships with HA core; the HA-side integration (Phase 2) only needs a `manifest.json` declaration and `async_step_zeroconf` — no additional dependency risk.

### Negative

- Extra Python dependency in the backend (`zeroconf`). Risk low: pure Python, actively maintained, permissive license.
- Additional lifespan logic and error paths — minimal maintenance overhead.
- Effectiveness varies by network context; documentation has to cover the deployment matrix (see `docs/en/reference/environment-variables.md`).

### Neutral

- `MDNS_ENABLED` and `INSTANCE_ID` as new environment variables. Default-off keeps all existing setups unchanged.
- Helm chart: two additional keys with explicit defaults; no breaking changes.
- HA integration work (Phase 2) lives in the separate `kamerplanter-ha` repository; this ADR only captures the backend decision and the expectations on the HA side.

## References

- Specification: `spec/ha-integration/HA-SPEC-ZEROCONF.md`
- RFC 6762 (mDNS), RFC 6763 (DNS-SD)
- HA developer docs: [Zeroconf Discovery](https://developers.home-assistant.io/docs/creating_integration_manifest#zeroconf)
- Related ADR-002 (Python 3.14 — baseline for the `zeroconf` library)
