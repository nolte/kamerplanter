# ADR-008: mDNS/Zeroconf für Home-Assistant Auto-Discovery

**Status:** Akzeptiert
**Datum:** 2026-04-24
**Entscheider:** Kamerplanter Development Team

## Kontext

Die Kamerplanter-Custom-Integration in Home Assistant benötigt bisher eine manuelle URL-Eingabe, um das Backend zu finden. Für Endnutzer — vor allem im Homelab-/Raspberry-Pi-Szenario — ist das eine überflüssige Hürde: Sie kennen weder die IP-Adresse ihres Containers noch den Port des FastAPI-Prozesses, die Integration fühlt sich dadurch im Vergleich zu "native" HA-Integrationen unfertig an.

Gleichzeitig läuft das Kamerplanter-Deployment in sehr unterschiedlichen Netzwerk-Kontexten (Docker-Compose direkt im LAN, K3s mit `hostNetwork`, Standard-Kubernetes mit Overlay-Netzwerk, Cloud). Eine Discovery-Lösung muss diese Heterogenität berücksichtigen und darf Cloud-Deployments nicht mit Multicast-Overhead belasten, in denen sie ohnehin wirkungslos wäre.

### Problem

- Manuelle URL-Eingabe ist für den Ziel-Anwenderkreis (nicht-DevOps Home-Assistant-User) eine spürbare Setup-Hürde.
- Es gibt keine Portfolio-einheitliche Discovery-Mechanik — jede HA-Integration ohne Discovery wirkt "alt".
- Eine naive Lösung (z. B. Backend annonciert immer) ist in Cloud-Deployments wirkungslos und in Kubernetes-Standardclustern irreführend, weil Multicast-Pakete das Overlay-Netz nicht verlassen.

## Entscheidung

**mDNS/Zeroconf-Announcement des Backends, opt-in per `MDNS_ENABLED`, TXT-Records liefern die Discovery-Metadaten.**

### Architektur

```
Backend (FastAPI Lifespan) ──▶ Zeroconf (UDP 5353) ──▶ Home Assistant
         │                                                     │
  `_kamerplanter._tcp.local.`                       `async_step_zeroconf`
         │                                                     │
  TXT: version, mode, api_path, instance_id ─────────▶ Unique-ID-Check
                                                              │
                                                   Config-Entry vorausgefüllt
```

- **Python-Lib `zeroconf`** als Announcer-Backend (pure Python, keine C-Extensions, Apache-2.0).
- **Register im Lifespan-Startup**, **Unregister im Shutdown** — Stale-Announcements sind ausgeschlossen.
- **Opt-in** per `MDNS_ENABLED=false` (Default). Helm setzt explizit `false`, Docker-Compose-Beispiele setzen `true`.
- **Secure-by-default** — keine Hostname-Leakage, `instance_id` Admin-kontrolliert, TXT-Records ohne Geheimnisse.

### Warum mDNS und nicht HTTP-Broadcast oder SSDP?

| Kriterium | mDNS (Zeroconf) | SSDP (UPnP) | HTTP-Broadcast |
|-----------|-----------------|-------------|----------------|
| HA-Native-Support | Erstklassig (`manifest.json` `zeroconf`) | OK (`ssdp`) | Kein Support |
| Verbreitung in Ziel-Appliances | Hoch (Drucker, NAS, Apple-Ecosystem) | Eher Media-Geräte | Keine |
| Protokoll-Komplexität | Gering (RFC 6762/6763) | Hoch (XML, NOTIFY) | Trivial, aber fragil |
| Python-Library | `zeroconf` (ausgereift) | `async_upnp_client` (HA-eigene Abhängigkeit) | — |
| Cloud-Szenarien | Opt-in deaktivieren | Dito | Niemals |

mDNS ist der HA-Standardweg für LAN-Discovery. SSDP wäre doppelter Aufwand für keinen erkennbaren Mehrwert.

### Warum opt-in und nicht opt-out?

- In Standard-Kubernetes laufen Pods hinter einem Overlay-Netz, das Multicast verwirft. Default-Opt-in würde `zeroconf.register_service` unnötig Arbeit kosten und Betreiber mit harmlosen Warnungen verwirren.
- In Cloud-Deployments ist mDNS schlicht funktionsverletzend (kein LAN, wohin annonciert werden könnte).
- Homelab- und Docker-Compose-Nutzer bekommen die empfohlene Einstellung per Beispiel-Konfiguration / Dokumentation ausgeliefert — kein realer UX-Verlust.

### Abgelehnte Alternativen

1. **DNS-SD via Unicast-DNS (DNSSEC):** Erfordert eine DNS-Infrastruktur, die im Homelab nicht existiert.
2. **Broadcast-basierte Eigenentwicklung:** Keine HA-Integration möglich; Wartungsaufwand ohne Mehrwert.
3. **HA scannt Port-Range im LAN:** Lange Scans, Security-Hygiene-Alarm, kein HA-natives Pattern.
4. **Kein Discovery — bei manueller URL bleiben:** Weiterhin die Fallback-Option; als alleinige Lösung aber ein anhaltender UX-Nachteil.

## Konsequenzen

### Positiv

- Einrichtungs-Weg für HA-Nutzer verkürzt sich drastisch: Backend starten → HA zeigt die Entdeckung → API-Key eingeben.
- Unique-ID-Mechanik über die `instance_id` verhindert doppelte Config-Entries bei Backend-Neuinstallation.
- `zeroconf`-Library ist im HA-Kern ohnehin verfügbar, die HA-seitige Integration (Phase 2) nutzt nur `manifest.json`-Deklaration und `async_step_zeroconf` — kein zusätzliches Dependency-Risiko.

### Negativ

- Zusätzliche Python-Dependency im Backend (`zeroconf`). Risiko niedrig: pure Python, stabil gepflegt, BSD-kompatible Lizenz.
- Zusätzliche Lifespan-Logik und Error-Paths — minimaler Wartungsaufwand.
- Feature hat je nach Netzwerk-Kontext unterschiedliche Wirkungsgrade; Dokumentation muss die Deployment-Matrix abbilden (siehe `docs/de/reference/environment-variables.md`).

### Neutral

- `MDNS_ENABLED` und `INSTANCE_ID` als neue Umgebungsvariablen. Default-Off hält alle bestehenden Setups unverändert.
- Helm-Chart: zwei weitere Keys mit expliziten Defaults; keine Breaking Changes.
- HA-Integration-Aufwand (Phase 2) liegt im separaten `kamerplanter-ha`-Repository; dieser ADR dokumentiert nur die Backend-Entscheidung und die Erwartung an die HA-Seite.

## Verweise

- Spezifikation: `spec/ha-integration/HA-SPEC-ZEROCONF.md`
- RFC 6762 (mDNS), RFC 6763 (DNS-SD)
- HA-Entwicklerdoku: [Zeroconf Discovery](https://developers.home-assistant.io/docs/creating_integration_manifest#zeroconf)
- Related ADR-002 (Python 3.14 — Baseline für die `zeroconf`-Library)
