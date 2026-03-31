# API-Überblick

Die Kamerplanter-API ist eine REST-API, die auf [FastAPI](https://fastapi.tiangolo.com/) basiert. Alle Endpunkte geben JSON zurück und folgen etablierten HTTP-Konventionen. Eine interaktive Dokumentation mit Swagger UI steht unter `/api/v1/docs` bereit.

---

## Basis-URL

```
http://localhost:8000/api/v1
```

In Produktionsumgebungen wird die API über Traefik als Ingress-Controller unter der konfigurierten Domain erreichbar.

## Interaktive Dokumentation

| URL | Inhalt |
|-----|--------|
| `/api/v1/docs` | Swagger UI — alle Endpunkte direkt ausprobieren |
| `/api/v1/redoc` | ReDoc — lesbare Referenzdokumentation |
| `/api/v1/openapi.json` | OpenAPI-Schema (JSON) — für Code-Generierung |

---

## Deployment-Modi

Das Verhalten der API hängt vom konfigurierten Deployment-Modus ab. Den aktuellen Modus liefert der Mode-Endpunkt:

```http
GET /api/v1/mode
```

```json
{
  "mode": "full",
  "features": {
    "auth": true,
    "multi_tenant": true,
    "privacy_consent": true
  }
}
```

### `full` (Standard)

Vollständiger Betrieb mit Authentifizierung, Mandantenverwaltung und DSGVO-Funktionen. Alle Auth-Endpunkte sind aktiv. Jede Anfrage muss authentifiziert sein (außer `health`, `mode` und öffentliche OAuth-Callbacks).

### `light`

Aktiviert durch `KAMERPLANTER_MODE=light`. Kein Login erforderlich — alle Endpunkte sind ohne Authentifizierung zugänglich. Geeignet für lokale Einzelnutzer-Installationen ohne Multi-Tenant-Bedarf. Die Auth-Router (`/auth/...`) sind in diesem Modus deaktiviert.

!!! warning "Light-Modus nicht für produktiven Multi-User-Betrieb"
    Im Light-Modus gibt es keine Zugriffskontrolle. Setzen Sie diesen Modus ausschließlich für isolierte lokale Instanzen ein.

---

## URL-Struktur

Die API unterscheidet zwischen **globalen Ressourcen** und **mandantengebundenen Ressourcen**.

### Globale Ressourcen

Stammdaten wie Pflanzenarten, botanische Familien und IPM-Referenzdaten sind global — sie gehören keinem einzelnen Mandanten.

```
GET  /api/v1/species/
GET  /api/v1/species/{key}
GET  /api/v1/botanical-families/
GET  /api/v1/cultivars/
GET  /api/v1/ipm/pests/
GET  /api/v1/starter-kits/
```

### Mandantengebundene Ressourcen

Alle nutzerspezifischen Daten (Pflanzen, Durchläufe, Sensoren, Tanks usw.) sind einem Mandanten zugeordnet und werden über den Mandanten-Slug in der URL adressiert:

```
/api/v1/t/{tenant_slug}/...
```

Beispiele:

```
GET  /api/v1/t/mein-garten/plant-instances/
POST /api/v1/t/mein-garten/planting-runs/
GET  /api/v1/t/mein-garten/tanks/
GET  /api/v1/t/mein-garten/tasks/
```

Der Tenant-Slug wird bei der Registrierung automatisch aus dem Nutzernamen generiert (persönlicher Mandant). Für Gemeinschaftsgärten kann ein separater Mandant angelegt werden.

### Health-Endpunkte

Die Health-Endpunkte erfordern keine Authentifizierung und sind für Kubernetes-Liveness- und Readiness-Probes vorgesehen:

```
GET /api/v1/health/live    → {"status": "alive"}
GET /api/v1/health/ready   → {"status": "ready", "database": true}
```

---

## Endpunkt-Übersicht

Die folgende Tabelle listet alle verfügbaren Router-Gruppen. Im Full-Modus sind `auth`-, `oidc-providers`- und `platform-admin`-Routen zusätzlich aktiv.

### Globale Endpunkte

| Gruppe | Pfad-Präfix | Beschreibung | REQ |
|--------|------------|--------------|-----|
| Authentifizierung | `/auth` | Login, Registrierung, Token, OAuth (nur full) | REQ-023 |
| Nutzer | `/users` | Eigenes Profil, Passwort ändern, Sessions | REQ-023 |
| Mandanten | `/tenants` | Mandanten-CRUD, Mitgliedschaften, Einladungen | REQ-024 |
| Botanische Familien | `/botanical-families` | Pflanzenfamilien-Stammdaten | REQ-001 |
| Arten | `/species` | Pflanzenarten-Stammdaten | REQ-001 |
| Sorten | `/species/{key}/cultivars` | Kultursorten (unterhalb einer Art) | REQ-001 |
| Lebenszyklen | `/species/{key}/lifecycle` | Lebenszyklus-Konfigurationen pro Art | REQ-003 |
| Wachstumsphasen | `/growth-phases` | Globale Phasendefinitionen | REQ-003 |
| Pflanzenphasen | `/plant-instances/{key}/phases` | Phasenübergänge einer Einzelpflanze | REQ-003 |
| Profile | `/profiles` | Anforderungs- und Nährstoffprofile | REQ-004 |
| Standorttypen | `/location-types` | Standorttyp-Stammdaten | REQ-002 |
| Substrate | `/substrates` | Substrattypen und -chargen | REQ-019 |
| Anreicherung | `/enrichment` | GBIF/Perenual-Datenanreicherung | REQ-011 |
| Familienbeziehungen | `/family-relationships` | Schädlingsrisiken und Kompatibilität pro Pflanzenfamilie | REQ-001 |
| Companion-Planting | `/companion-planting` | Mischkultur-Empfehlungen | REQ-028 |
| Fruchtfolge | `/crop-rotation` | Rotationsvalidierung | REQ-002 |
| IPM (global) | `/ipm` | Schädlinge, Krankheiten, Behandlungen — Stammdaten | REQ-010 |
| Berechnungen | `/calculations` | EC/VPD-Berechnungen | REQ-004 |
| Nährstoffberechnungen | `/nutrient-calculations` | Nährstofflösungs-Berechnungen | REQ-004 |
| Pflegeerinnerungen | `/care-reminders` | Automatische Pflegepläne | REQ-022 |
| Starter-Kits | `/starter-kits` | Vorkonfigurierte Pakete | REQ-020 |
| Import | `/import` | CSV-Import für Stammdaten | REQ-012 |
| Aktivitäten | `/activities` | Aktivitätsdefinitionen (Gießen, Düngen, etc.) | REQ-006 |
| Aktivitätspläne | `/activity-plans` | Generierung und Anwendung von Aktivitätsplänen | REQ-006 |
| Wissensdatenbank | `/knowledge` | RAG-basierte Suche und KI-Antworten (optional) | — |
| Beobachtungen | `/observations` | TimescaleDB-Status | REQ-005 |
| Health | `/health` | Liveness und Readiness | — |
| Modus | `/mode` | Aktueller Deployment-Modus (full/light) | REQ-027 |

### Mandantengebundene Endpunkte (`/t/{slug}/...`)

| Gruppe | Pfad-Präfix | Beschreibung | REQ |
|--------|------------|--------------|-----|
| Standorte | `/sites` | Standort-CRUD, Standorthierarchie, Sensoren | REQ-002 |
| Bereiche | `/locations` | Bereiche und Unter-Standorte | REQ-002 |
| Stellplätze | `/slots` | Slot-Verwaltung innerhalb von Bereichen | REQ-002 |
| Pflanzeninstanzen | `/plant-instances` | Einzelpflanzen-Tracking | REQ-001 |
| Pflanzdurchläufe | `/planting-runs` | Batch-Verwaltung, Phasen, Tagebuch | REQ-013 |
| Tanks | `/tanks` | Tankzustände, Befüllungen, Wartung, Sensoren | REQ-014 |
| Düngemittel | `/fertilizers` | Düngemittel, Bestände, Unverträglichkeiten | REQ-004 |
| Nährstoffpläne | `/nutrient-plans` | EC-basierte Nahrungspläne, Kanäle, Dosierungen | REQ-004 |
| Düngeereignisse | `/feeding-events` | Dokumentation von Düngegaben | REQ-004 |
| Gießereignisse | `/watering-events` | Bewässerungsprotokoll mit Bestätigung | REQ-004 |
| Gießprotokoll | `/watering-logs` | Detailliertes Bewässerungsprotokoll | REQ-004 |
| IPM (Mandant) | `/ipm` | Mandantenspezifische Inspektionen und Behandlungen | REQ-010 |
| Ernte | `/harvest` | Erntedokumentation und Karenz-Gate | REQ-007 |
| Aufgaben | `/tasks` | Aufgabenplanung, Workflows, Queue | REQ-006 |
| Kalender | `/calendar` | iCal-Feeds, Aussaatkalender, Saisonübersicht | REQ-015 |
| Onboarding | `/onboarding` | Einrichtungsassistent | REQ-020 |
| Starter-Kits | `/starter-kits` | Kit-Anwendung für Mandanten | REQ-020 |
| Nutzerpräferenzen | `/user-preferences` | Erfahrungsstufe, Sprache | REQ-021 |
| Favoriten | `/favorites` | Pflanzen-Favoriten und Nährstoffplan-Matching | — |
| Benachrichtigungen | `/notifications` | Benachrichtigungen, Präferenzen, Test-Versand | REQ-022 |
| Beobachtungen | `/observations` | Sensordaten-CRUD (TimescaleDB) | REQ-005 |

### Admin-Endpunkte

| Gruppe | Pfad-Präfix | Beschreibung | REQ |
|--------|------------|--------------|-----|
| Plattform-Admin | `/admin/platform` | Statistiken, Mandanten-, Nutzerverwaltung | REQ-024 |
| OIDC-Provider | `/admin/oidc-providers` | Föderierte Authentifizierungs-Provider | REQ-023 |
| Einstellungen | `/admin/settings` | Home-Assistant-Konfiguration | REQ-018 |

---

## Anfrage- und Antwortformat

Alle Request-Bodies und Responses verwenden `application/json`. Eine explizite `Content-Type: application/json`-Kopfzeile ist für POST/PUT/PATCH-Anfragen erforderlich.

### Paginierung

Listenendpunkte unterstützen `skip` und `limit` als Query-Parameter:

```http
GET /api/v1/species/?skip=0&limit=50
```

Standardwerte: `skip=0`, `limit=100` (je nach Endpunkt variierend).

### Datumsformat

Alle Datums- und Zeitangaben folgen ISO 8601 im UTC-Format:

```
2026-03-17T10:30:00Z
```

---

## Rate Limiting

Zur Missbrauchsvermeidung sind sensible Endpunkte mit Rate Limits versehen:

| Endpunkt-Gruppe | Standard-Limit |
|----------------|---------------|
| Auth-Endpunkte (`/auth/login`, `/auth/register`) | 20 Anfragen/Minute pro IP |
| Allgemeine API-Endpunkte | 100 Anfragen/Minute |

Bei Überschreitung antwortet die API mit HTTP `429 Too Many Requests`.

---

## CORS-Konfiguration

Erlaubte Origins werden über die Umgebungsvariable `CORS_ORIGINS` als kommagetrennte Liste konfiguriert:

```bash
CORS_ORIGINS=https://app.kamerplanter.example.com,https://admin.kamerplanter.example.com
```

Standardmäßig sind `http://localhost:3000` und `http://localhost:5173` (Vite-Dev-Server) erlaubt.

---

## Sicherheits-Header

Jede API-Antwort enthält folgende Sicherheits-Header:

| Header | Wert |
|--------|------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Strict-Transport-Security` | Aktiv (nur außerhalb des Debug-Modus) |

---

## Siehe auch

- [Authentifizierung](authentication.md) — Token-Workflow und API-Keys
- [Fehlerbehandlung](error-handling.md) — Fehlerstruktur und Fehlercodes
- [Service Accounts](service-accounts.md) — M2M-Zugriff (geplant, noch nicht implementiert)
- [Lokale Entwicklungsumgebung](../development/local-setup.md) — Backend lokal starten
