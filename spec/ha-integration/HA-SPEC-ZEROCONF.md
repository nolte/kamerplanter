# Spezifikation: mDNS/Zeroconf Auto-Discovery fuer Home Assistant

```yaml
ID: HA-SPEC-ZEROCONF
Titel: mDNS/Zeroconf Auto-Discovery fuer Home Assistant
Status: Teilweise umgesetzt (Phase 1 Backend-Seite fertig, Phase 2 HA-Seite offen)
Version: 1.0
Datum: 2026-04-24
Scope: src/backend/app/common/mdns.py, src/backend/app/config/settings.py,
       src/backend/app/main.py (Lifespan), kamerplanter-ha/config_flow.py (Phase 2)
Abhaengigkeiten: HA-SPEC-CONFIG-LIFECYCLE (Config Flow, Unique ID)
Style Guide: spec/style-guides/BACKEND.md, spec/style-guides/HA-INTEGRATION.md
```

---

## 1. Ziel

Das Kamerplanter-Backend annonciert sich im lokalen Netzwerk via mDNS/Zeroconf, damit die Kamerplanter-Custom-Integration in Home Assistant das Backend **ohne manuelle URL-Eingabe** findet und einen Zeroconf-Discovery-Config-Flow anbietet.

Die manuelle Konfiguration (URL-Eingabe) bleibt als Fallback fuer Setups bestehen, in denen mDNS nicht funktioniert (Cloud-Deployments, Standard-Kubernetes ohne hostNetwork, getrennte L2-Segmente).

---

## 2. Scope

**Phase 1 (umgesetzt, Backend-Seite):**
- Backend annonciert `_kamerplanter._tcp.local.` im lokalen Netzwerk.
- Opt-in per Umgebungsvariable `MDNS_ENABLED` (Default `false`).
- Service-Name enthaelt eine stabile `INSTANCE_ID`, keine interne Hostname-Leakage.
- TXT-Records mit Mindestmetadaten fuer HA-Discovery.
- Start/Stop ueber die FastAPI-Lifespan.

**Phase 2 (offen, HA-Seite — Repo `kamerplanter-ha`):**
- `manifest.json` deklariert `zeroconf`-Discovery fuer `_kamerplanter._tcp.local.`.
- `async_step_zeroconf` im Config Flow: Unique-ID-Check gegen `instance_id`, Abort bei Duplikat, Pre-Fill der URL aus `host:port`.
- Re-Use des bestehenden API-Key-Eingabeschrittes — Zeroconf liefert nur die URL, nicht die Auth.

**Nicht im Scope:**
- Encrypted DNS-SD (DNSSEC/TLS) — mDNS bleibt unverschluesselt. Authentisierung erfolgt nachgelagert ueber den API-Key.
- WAN-Discovery — Zeroconf ist LAN-only.
- mDNS-Discovery in die andere Richtung (Backend entdeckt HA) — HA wird weiterhin per `HA_URL` manuell konfiguriert.

---

## 3. Anforderungen (MUST/SHOULD/MAY)

### 3.1 Service-Announcement

- **MUSS** den Service-Typ `_kamerplanter._tcp.local.` verwenden.
- **MUSS** den Service-Namen als `Kamerplanter (<instance_id>).<service_type>` bilden (Namespaces vermeiden Kollisionen mit anderen Kamerplanter-Instanzen im gleichen LAN).
- **MUSS** den Backend-Port (Standard 8000) annoncieren.
- **MUSS** den Server-Hostname als `<instance_id>.local.` setzen — **nicht** den Container-/Pod-Hostnamen (kein Information Disclosure).
- **MUSS** auf Shutdown via `Zeroconf.unregister_service(...)` abmelden, damit keine Stale-Announcements im LAN haengenbleiben.

### 3.2 TXT-Records

Folgende Schluessel **MUESSEN** gesetzt werden:

| Schluessel | Inhalt | Zweck |
|------------|--------|-------|
| `version` | `app_version` | HA-Integration kann Kompatibilitaet pruefen |
| `mode` | `kamerplanter_mode` (`full`, `light`) | Unterscheidet Auth-Modi; beeinflusst Config-Flow-Schritte |
| `api_path` | `/api` | Basis-Pfad unter der Backend-URL (fuer zukuenftige Reverse-Proxy-Setups) |
| `instance_id` | `settings.instance_id` | Unique-ID fuer HA-Config-Entry (Duplikat-Abwehr) |

Optional **KANN**:

| Schluessel | Inhalt | Zweck |
|------------|--------|-------|
| `tenant` | Slug des Default-Tenants | Mehrinstanz-Installationen unterscheiden |

### 3.3 Instance-ID

- **MUSS** stabil ueber Neustarts hinweg sein, wenn `INSTANCE_ID` gesetzt ist.
- **MUSS** automatisch generiert werden (`kp-<uuid8>`), wenn `INSTANCE_ID` leer ist.
- **MUSS** via Pydantic-Field validiert werden: `max_length=64`, Pattern `^[a-zA-Z0-9\-]*$` (keine Pfad-Injektion, keine Unicode-Ueberraschungen im mDNS-Namen).
- **SOLLTE** vom Deployment explizit gesetzt werden (z. B. `INSTANCE_ID=kp-homelab-01`), damit HA-Config-Entries nach Backend-Neuinstallation wiederverwendbar bleiben.

### 3.4 Opt-in und Defaults

- **MUSS** per Default deaktiviert sein (`MDNS_ENABLED=false`) — secure-by-default.
- **MUSS** in Helm-Values auf `false` stehen, weil der Default-K8s-Netzwerk-Stack mDNS nicht durchlaesst (siehe §5).
- **SOLLTE** in der Docker-Compose-Beispielkonfiguration auf `true` stehen, weil Docker-Compose-Deployments typischerweise im LAN laufen.

### 3.5 HA-Integration (Phase 2)

- **MUSS** im `manifest.json` deklarieren:
  ```json
  "zeroconf": [{"type": "_kamerplanter._tcp.local."}]
  ```
- **MUSS** `async_step_zeroconf` implementieren, das:
  - `instance_id` aus TXT-Records liest,
  - `await self.async_set_unique_id(instance_id)` aufruft,
  - `self._abort_if_unique_id_configured()` pruefen,
  - die URL aus `host:port` und `api_path` bildet und dem User im naechsten Schritt vor-ausgefuellt anzeigt.
- **MUSS** im Dialog den API-Key erfragen (Zeroconf liefert keine Auth).
- **MUSS** `mode`-TXT-Record auswerten und im `light`-Modus den API-Key-Schritt ueberspringen.

---

## 4. Architektur

```
┌─────────────────────────────┐         UDP 5353 Multicast
│ Kamerplanter Backend        │ ─────────────────────────────────▶
│                             │     `_kamerplanter._tcp.local.`
│   app/common/mdns.py        │     TXT: version, mode, api_path,
│   MdnsAnnouncer             │          instance_id
│   (FastAPI Lifespan)        │
└─────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────┐
│ Home Assistant              │
│                             │
│   Zeroconf Discovery        │
│   manifest.json: zeroconf[] │
│   config_flow.async_step_   │
│     zeroconf                │
│                             │
│   → Config Flow Pre-Fill    │
│   → User gibt API-Key ein   │
└─────────────────────────────┘
```

- Zeroconf laeuft als eigener Thread (Python-Lib `zeroconf`), kein Blocking des FastAPI-Event-Loops.
- Register/Unregister geschehen im `lifespan`-Kontext, damit Stop-Signals auch bei SIGTERM sauber abgearbeitet werden.

---

## 5. Deployment-Matrix

| Deployment | `MDNS_ENABLED` | Begruendung |
|------------|:-------------:|-------------|
| Docker Compose / Bare Metal | `true` | Backend laeuft direkt im LAN — Multicast funktioniert. |
| K3s / MicroK8s Single-Node + `hostNetwork: true` | `true` | Pod teilt Host-Netzwerk — Multicast erreicht das LAN. |
| Standard K8s-Cluster (Calico/Cilium/Flannel) | `false` | Overlay-Netzwerk blockiert Multicast; annoncierte Pod-IP waere ohnehin nicht LAN-erreichbar. |
| Cloud (AWS/GCP/Azure) | `false` | Kein lokales LAN mit dem HA-Host. |

Der manuelle Config Flow (URL-Eingabe) funktioniert in allen Szenarien als Fallback.

---

## 6. Sicherheit

- mDNS-Announcements sind unverschluesselt und auf jedem Geraet im LAN sichtbar. Kamerplanter veroeffentlicht bewusst **keine** sicherheitsrelevanten Felder (keine Tokens, keine internen Hostnames, keine Cluster-Details).
- Der Service-Name enthaelt ausschliesslich die `instance_id` — ein Admin-gewaehlter Wert. Die Integration kann also nicht durch mDNS-Beobachtung Rueckschluesse auf interne Hostnames oder Container-Namen ziehen.
- Authentisierung erfolgt nachgelagert ueber den API-Key-Eingabeschritt im HA-Config-Flow.
- Die `instance_id`-Validierung (`^[a-zA-Z0-9\-]*$`, `max_length=64`) verhindert Injection ueber exotische Unicode-Sequenzen in den Service-Namen.

---

## 7. Teststrategie

### Phase 1 (umgesetzt)

Unit-Tests unter `src/backend/tests/unit/test_mdns.py`:

- `generate_instance_id()` Format und Eindeutigkeit.
- `create_service_info()` Properties, Server-Hostname, Namens-Struktur.
- `MdnsAnnouncer.start()` ruft `Zeroconf.register_service` mit korrekter `ServiceInfo` auf.
- `MdnsAnnouncer.stop()` unregisters und schliesst den Zeroconf-Handle.
- Pydantic-Validierung: Laengenueberschreitung / ungueltige Zeichen in `INSTANCE_ID` wird abgelehnt.

Insgesamt 11 Tests (100% pass).

### Phase 2 (offen)

- HA-Integration-Test (`pytest-homeassistant-custom-component`): Zeroconf-Discovery-Flow mit simulierten `ServiceInfo`-Mocks; Unique-ID-Duplikatabwehr; Fallback auf User-Step bei fehlenden TXT-Records.
- Manueller End-to-End-Test: Backend mit `MDNS_ENABLED=true` im LAN; HA zeigt die Discovery-Benachrichtigung; Config-Flow fuehrt erfolgreich zum Config-Entry.

---

## 8. Migrations- und Rollout-Plan

1. **Phase 1 merged** (dieser Branch): Backend annonciert, Feature ist opt-in und dokumentiert. Keine HA-seitige Aenderung notwendig — bestehende Installationen sehen keinen Unterschied.
2. **Phase 2 im `kamerplanter-ha`-Repo**: Zeroconf-Step im Config Flow, `manifest.json`-Erweiterung. Release als Minor-Version — existierende Config-Entries bleiben funktionsfaehig; Discovery betrifft nur Neuinstallationen.
3. **Dokumentation**: `docs/*/guides/home-assistant-integration.md` beschreibt die Auto-Discovery als empfohlenen Setup-Pfad, Manual-Setup bleibt als Alternative erhalten.

---

## 9. Offene Punkte

- Soll das Helm-Chart zusaetzlich einen Beispiel-Wert mit `hostNetwork: true` in `values.example.yaml` mitliefern, damit Homelab-Nutzer den mDNS-Weg direkt aktivieren koennen?
- Im `light`-Modus ist kein API-Key noetig; soll die HA-Integration in dem Fall auch den Zeroconf-Step ganz ohne User-Interaktion abschliessen, oder als Bestaetigungsschritt behalten?
- Langfristig: CNAME `kamerplanter.local.` auf die erste erreichbare Instanz, damit Nicht-HA-Nutzer einen stabilen Einstiegs-Link haben?

---

## 10. Referenzen

- [RFC 6762 — Multicast DNS](https://www.rfc-editor.org/rfc/rfc6762)
- [RFC 6763 — DNS-Based Service Discovery](https://www.rfc-editor.org/rfc/rfc6763)
- [Home Assistant — Zeroconf Discovery](https://developers.home-assistant.io/docs/creating_integration_manifest#zeroconf)
- [python-zeroconf Library](https://github.com/python-zeroconf/python-zeroconf)
- Interne Spec: `spec/ha-integration/HA-SPEC-CONFIG-LIFECYCLE.md` (Config Flow, Unique ID)
- ADR: `docs/de/adr/008-zeroconf-mdns-auto-discovery.md`
