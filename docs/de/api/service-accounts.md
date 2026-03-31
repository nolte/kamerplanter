# Service Accounts & API-Keys

!!! warning "Noch nicht implementiert"
    Service Accounts sind spezifiziert (REQ-023 v1.7), aber noch **nicht implementiert**. Diese Seite beschreibt das geplante Verhalten. Die hier dokumentierten Endpunkte sind noch nicht verfügbar.

Service Accounts ermöglichen die maschinelle Kommunikation (M2M) zwischen externen Systemen
und der Kamerplanter API — ohne persönliche Nutzer-Credentials zu verwenden. Typische
Einsatzzwecke sind Home Assistant, Grafana, CI/CD-Pipelines und automatisierte
Monitoring-Systeme.

---

## Konzept

Service Accounts sind eigenständige, nicht-interaktive Konten vom Typ `account_type: 'service'`.
Im Gegensatz zu menschlichen Accounts (`account_type: 'human'`) gilt:

- Kein Passwort, keine SSO-Anmeldung
- Authentifizierung ausschließlich per API-Key (Bearer Token)
- Kein interaktiver Login möglich
- Eigene Rate-Limits und IP-Einschränkungen konfigurierbar

### Tenant-scoped vs. Platform-scoped

| Typ | Erstellt von | Zugriff | Beispiel |
|-----|-------------|---------|---------|
| **Tenant-scoped** | Tenant-Admin | Nur auf Ressourcen des eigenen Tenants | Home Assistant, Grafana pro Tenant |
| **Platform-scoped** | KA-Admin (Platform-Admin) | Auf globale und mandantenübergreifende Daten | Backup-System, Enrichment-Pipeline |

---

## Voraussetzungen

- Tenant-Admin-Rolle im betreffenden Tenant (für Tenant-scoped Accounts)
- Platform-Admin-Rolle (für Platform-scoped Accounts)

---

## Service Account erstellen

### Tenant-scoped Service Account

```bash
curl -X POST "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Home Assistant Zelt 1",
    "description": "Liefert Sensor-Daten und steuert Licht/Lueftung fuer Zelt 1",
    "rate_limit_rpm": 500,
    "allowed_ip_ranges": ["192.168.1.0/24"]
  }'
```

**Antwort (201 Created):**

```json
{
  "_key": "sa_abc123",
  "display_name": "Home Assistant Zelt 1",
  "account_type": "service",
  "status": "active",
  "api_key": "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "rate_limit_rpm": 500,
  "allowed_ip_ranges": ["192.168.1.0/24"],
  "created_at": "2026-03-28T10:00:00Z"
}
```

!!! warning "API-Key nur einmal sichtbar"
    Der `api_key`-Wert wird nur bei der Erstellung im Klartext zurückgegeben.
    Danach speichert das System nur noch den SHA-256-Hash. Notieren Sie den Key sofort
    an einem sicheren Ort (z.B. in einem Secret-Manager).

### Platform-scoped Service Account

```bash
curl -X POST "https://api.kamerplanter.example.com/api/v1/service-accounts/" \
  -H "Authorization: Bearer {platform_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Backup Pipeline",
    "description": "Nachts laufende Datensicherung aller Tenants",
    "rate_limit_rpm": 200
  }'
```

---

## API-Key verwenden

Senden Sie den API-Key als `Authorization: Bearer`-Header bei jedem Request:

=== "curl"

    ```bash
    curl -X GET "https://api.kamerplanter.example.com/api/v1/t/mein-garten/plants/" \
      -H "Authorization: Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ```

=== "Python (httpx)"

    ```python
    import httpx

    API_KEY = "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    BASE_URL = "https://api.kamerplanter.example.com"

    client = httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
    )

    response = client.get("/api/v1/t/mein-garten/plants/")
    response.raise_for_status()
    plants = response.json()
    ```

=== "Python (requests)"

    ```python
    import requests

    API_KEY = "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    BASE_URL = "https://api.kamerplanter.example.com"

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {API_KEY}"

    response = session.get(f"{BASE_URL}/api/v1/t/mein-garten/plants/")
    response.raise_for_status()
    plants = response.json()
    ```

!!! note "Key-Format"
    Alle API-Keys tragen das Praefix `kp_`. Das Backend erkennt dieses Praefix
    und leitet den Request in den API-Key-Authentifizierungspfad (statt JWT-Validierung).

---

## Key-Rotation

### Manuelle Rotation

Erstellen Sie einen neuen Key und widerrufen Sie den alten. Die Rotation empfiehlt sich
regelmaessig (alle 90 Tage) oder nach dem Verdacht auf Kompromittierung.

```bash
# Neuen Key generieren (der alte bleibt vorerst aktiv)
curl -X POST "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}/rotate-key" \
  -H "Authorization: Bearer {access_token}"
```

**Antwort:**

```json
{
  "new_api_key": "kp_live_yyyyyyyyyyyyyyyyyyyyyyyy",
  "old_key_revoked_at": "2026-03-28T11:00:00Z"
}
```

!!! tip "Rotations-Workflow"
    1. Neuen Key per `rotate-key` generieren
    2. Neuen Key in die externe Anwendung (Home Assistant, CI/CD) eintragen
    3. Verbindung mit dem neuen Key testen
    4. Alten Key ist nach dem Rotations-Request automatisch ungueltig

### Service Account deaktivieren

```bash
curl -X PATCH "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"status": "suspended"}'
```

---

## IP-Allowlist konfigurieren

Beschraenken Sie den Zugriff auf bestimmte IP-Bereiche (CIDR-Notation):

```bash
curl -X PATCH "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_ip_ranges": [
      "192.168.1.0/24",
      "10.0.0.0/8"
    ]
  }'
```

Wird ein Request von einer nicht erlaubten IP abgesendet, antwortet die API mit `403 Forbidden`.

!!! tip "Keine Einschraenkung"
    Setzen Sie `allowed_ip_ranges` auf `null` oder lassen Sie das Feld weg, um den
    Zugriff aus allen IP-Bereichen zu erlauben (Standard fuer neue Service Accounts).

---

## Rate Limits

Jeder Service Account hat ein konfigurierbares Rate Limit in Requests pro Minute (RPM).

| Wert | Bedeutung |
|------|-----------|
| `null` | Globaler Default (1000 RPM) |
| `500` | 500 Requests pro Minute |
| `100` | Restriktiver Zugriff fuer externe Partner |

Bei Ueberschreitung antwortet die API mit `429 Too Many Requests` und dem Header
`Retry-After: <Sekunden>`.

---

## Berechtigungen

Service Accounts unterliegen der gleichen Permission-Matrix wie menschliche Nutzer.
Ein Tenant-scoped Service Account mit Viewer-Rolle kann nur lesend auf Tenant-Ressourcen
zugreifen; ein Service Account mit Grower-Rolle kann auch schreiben.

Die Rolle wird bei der Erstellung festgelegt:

```bash
curl -X POST ".../service-accounts/" \
  -d '{
    "display_name": "Grafana Read-Only",
    "role": "viewer"
  }'
```

Verfuegbare Rollen: `admin`, `grower`, `viewer` (identisch mit menschlichen Mitgliedern).

---

## Praktisches Beispiel: Home Assistant einrichten

Dieses Beispiel zeigt den vollstaendigen Einrichtungsablauf fuer eine Home Assistant
Integration.

### Schritt 1: Service Account erstellen

```python
import httpx

# Mit dem persoenlichen Account (Tenant-Admin) anmelden
auth = httpx.post(
    "https://api.kamerplanter.example.com/api/v1/auth/login",
    json={"email": "admin@mein-garten.de", "password": "..."},
)
token = auth.json()["access_token"]

# Service Account fuer Home Assistant erstellen
sa = httpx.post(
    "https://api.kamerplanter.example.com/api/v1/t/mein-garten/service-accounts/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "display_name": "Home Assistant",
        "description": "Sensor-Ingestion und Aktor-Steuerung",
        "role": "grower",
        "rate_limit_rpm": 1000,
        "allowed_ip_ranges": ["192.168.1.100/32"],  # Nur HA-Host
    },
)
sa.raise_for_status()
api_key = sa.json()["api_key"]
print(f"API Key (jetzt notieren!): {api_key}")
```

### Schritt 2: API-Key in Home Assistant eintragen

Tragen Sie den Key in der Home Assistant Kamerplanter Integration ein
(Einstellungen → Integrationen → Kamerplanter):

```yaml
# configuration.yaml (Beispiel fuer REST-Sensor)
sensor:
  - platform: rest
    name: "Kamerplanter Sensor Push"
    resource: "https://api.kamerplanter.example.com/api/v1/t/mein-garten/observations/"
    method: POST
    headers:
      Authorization: "Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      Content-Type: "application/json"
```

### Schritt 3: Verbindung testen

```bash
curl -X GET "https://api.kamerplanter.example.com/api/v1/t/mein-garten/service-accounts/me" \
  -H "Authorization: Bearer kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Erwartete Antwort: Informationen zum Service Account (Name, Rolle, letzte Aktivitaet).

---

## Service Accounts auflisten und verwalten

```bash
# Alle Service Accounts eines Tenants auflisten
curl "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/" \
  -H "Authorization: Bearer {access_token}"

# Einzelnen Service Account abrufen
curl "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}"

# Service Account loeschen
curl -X DELETE "https://api.kamerplanter.example.com/api/v1/t/{tenant_slug}/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}"
```

---

## Haeufige Fragen

??? question "Kann ein Service Account mehrere API-Keys gleichzeitig haben?"
    Nein. Pro Service Account gibt es genau einen aktiven API-Key. Bei einer Rotation
    wird der alte Key sofort ungueltig und ein neuer ausgestellt. Planen Sie die
    Rotation so, dass Sie den neuen Key vor dem Widerruf des alten in die Zielanwendung
    eintragen koennen.

??? question "Was passiert bei einem kompromittierten API-Key?"
    Setzen Sie den Service Account sofort per `status: suspended` ausser Betrieb und
    rotieren Sie anschliessend den Key. Pruefen Sie die Aktivitaetslogs
    (`last_active_at`) auf verdaechtige Anfragen.

??? question "Wie unterscheidet sich ein Service Account von einem regulaeren API-Key (v1.4)?"
    Service Accounts (v1.7) sind vollwertige Entitaeten mit eigenem Datensatz, Beschreibung,
    Rolle und Konfiguration. Einfache API-Keys (v1.4 unter `api_keys`) sind leichtgewichtiger,
    aber ohne Rollenzuweisung und IP-Einschraenkung.

??? question "Koennen Service Accounts sich auf mehreren Tenants bewegen?"
    Tenant-scoped Service Accounts sind auf genau einen Tenant beschraenkt.
    Fuer tenant-uebergreifende Zugriffe muss ein Platform-scoped Service Account erstellt
    werden (erfordert Platform-Admin-Rolle).

## Siehe auch

- [Authentifizierung](authentication.md)
- [Fehlerbehandlung](error-handling.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
