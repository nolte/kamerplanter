# ADR-008: mDNS/Zeroconf fuer Home-Assistant Auto-Discovery

**Status:** Akzeptiert
**Datum:** 2026-04-24
**Entscheider:** Kamerplanter Development Team

## Kontext

Die Kamerplanter-Custom-Integration in Home Assistant benoetigt bisher eine manuelle URL-Eingabe, um das Backend zu finden. Fuer Endnutzer — vor allem im Homelab-/Raspberry-Pi-Szenario — ist das eine ueberfluessige Huerde: Sie kennen weder die IP-Adresse ihres Containers noch den Port des FastAPI-Prozesses, die Integration fuehlt sich dadurch im Vergleich zu "native" HA-Integrationen unfertig an.

Gleichzeitig laeuft das Kamerplanter-Deployment in sehr unterschiedlichen Netzwerk-Kontexten (Docker-Compose direkt im LAN, K3s mit `hostNetwork`, Standard-Kubernetes mit Overlay-Netzwerk, Cloud). Eine Discovery-Loesung muss diese Heterogenitaet beruecksichtigen und darf Cloud-Deployments nicht mit Multicast-Overhead belasten, in denen sie ohnehin wirkungslos waere.

### Problem

- Manuelle URL-Eingabe ist fuer den Ziel-Anwenderkreis (nicht-DevOps Home-Assistant-User) eine spuerbare Setup-Huerde.
- Es gibt keine Portfolio-einheitliche Discovery-Mechanik — jede HA-Integration ohne Discovery wirkt "alt".
- Eine naive Loesung (z. B. Backend annonciert immer) ist in Cloud-Deployments wirkungslos und in Kubernetes-Standardclustern irrefuehrend, weil Multicast-Pakete das Overlay-Netz nicht verlassen.

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
                                                   Config-Entry vorausgefuellt
```

- **Python-Lib `zeroconf`** als Announcer-Backend (pure Python, keine C-Extensions, Apache-2.0).
- **Register im Lifespan-Startup**, **Unregister im Shutdown** — Stale-Announcements sind ausgeschlossen.
- **Opt-in** per `MDNS_ENABLED=false` (Default). Helm setzt explizit `false`, Docker-Compose-Beispiele setzen `true`.
- **Secure-by-default** — keine Hostname-Leakage, `instance_id` Admin-kontrolliert, TXT-Records ohne Geheimnisse.

### Warum mDNS und nicht HTTP-Broadcast oder SSDP?

| Kriterium | mDNS (Zeroconf) | SSDP (UPnP) | HTTP-Broadcast |
|-----------|-----------------|-------------|----------------|
| HA-Native-Support | Erstklassig (`manifest.json` `zeroconf`) | OK (`ssdp`) | Kein Support |
| Verbreitung in Ziel-Appliances | Hoch (Drucker, NAS, Apple-Ecosystem) | Eher Media-Geraete | Keine |
| Protokoll-Komplexitaet | Gering (RFC 6762/6763) | Hoch (XML, NOTIFY) | Trivial, aber fragil |
| Python-Library | `zeroconf` (ausgereift) | `async_upnp_client` (HA-eigene Abhaengigkeit) | — |
| Cloud-Szenarien | Opt-in deaktivieren | Dito | Niemals |

mDNS ist der HA-Standardweg fuer LAN-Discovery. SSDP waere doppelter Aufwand fuer keinen erkennbaren Mehrwert.

### Warum opt-in und nicht opt-out?

- In Standard-Kubernetes laufen Pods hinter einem Overlay-Netz, das Multicast verwirft. Default-Opt-in wuerde `zeroconf.register_service` unnoetig Arbeit kosten und Betreiber mit harmlosen Warnungen verwirren.
- In Cloud-Deployments ist mDNS schlicht funktionsverletzend (kein LAN, wohin annonciert werden koennte).
- Homelab- und Docker-Compose-Nutzer bekommen die empfohlene Einstellung per Beispiel-Konfiguration / Dokumentation ausgeliefert — kein realer UX-Verlust.

### Abgelehnte Alternativen

1. **DNS-SD via Unicast-DNS (DNSSEC):** Erfordert eine DNS-Infrastruktur, die im Homelab nicht existiert.
2. **Broadcast-basierte Eigenentwicklung:** Keine HA-Integration moeglich; Wartungsaufwand ohne Mehrwert.
3. **HA scannt Port-Range im LAN:** Lange Scans, Security-Hygiene-Alarm, kein HA-natives Pattern.
4. **Kein Discovery — bei manueller URL bleiben:** Weiterhin die Fallback-Option; als alleinige Loesung aber ein anhaltender UX-Nachteil.

## Konsequenzen

### Positiv

- Einrichtungs-Weg fuer HA-Nutzer verkuerzt sich drastisch: Backend starten → HA zeigt die Entdeckung → API-Key eingeben.
- Unique-ID-Mechanik ueber die `instance_id` verhindert doppelte Config-Entries bei Backend-Neuinstallation.
- `zeroconf`-Library ist im HA-Kern ohnehin verfuegbar, die HA-seitige Integration (Phase 2) nutzt nur `manifest.json`-Deklaration und `async_step_zeroconf` — kein zusaetzliches Dependency-Risiko.

### Negativ

- Zusaetzliche Python-Dependency im Backend (`zeroconf`). Risiko niedrig: pure Python, stabil gepflegt, BSD-kompatible Lizenz.
- Zusaetzliche Lifespan-Logik und Error-Paths — minimaler Wartungsaufwand.
- Feature hat je nach Netzwerk-Kontext unterschiedliche Wirkungsgrade; Dokumentation muss die Deployment-Matrix abbilden (siehe `docs/de/reference/environment-variables.md`).

### Neutral

- `MDNS_ENABLED` und `INSTANCE_ID` als neue Umgebungsvariablen. Default-Off haelt alle bestehenden Setups unveraendert.
- Helm-Chart: zwei weitere Keys mit expliziten Defaults; keine Breaking Changes.
- HA-Integration-Aufwand (Phase 2) liegt im separaten `kamerplanter-ha`-Repository; dieser ADR dokumentiert nur die Backend-Entscheidung und die Erwartung an die HA-Seite.

## Verweise

- Spezifikation: `spec/ha-integration/HA-SPEC-ZEROCONF.md`
- RFC 6762 (mDNS), RFC 6763 (DNS-SD)
- HA-Entwicklerdoku: [Zeroconf Discovery](https://developers.home-assistant.io/docs/creating_integration_manifest#zeroconf)
- Related ADR-002 (Python 3.14 — Baseline fuer die `zeroconf`-Library)
