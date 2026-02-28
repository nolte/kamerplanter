---

ID: NFR-001
Titel: Strikte Trennung von Frontend und Backend (Separation of Concerns)
Kategorie: Architektur Unterkategorie: API-Design, Security, Deployment Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI, Docker
Status: Produktionsreif
Priorität: Kritisch
Version: 2.2
Autor: Business Analyst - Agrotech
Datum: 2026-02-27
Tags: [architecture, api-first, security, scalability, separation-of-concerns, layered-architecture, rate-limiting, csp, mqtt-security, audit-trail, dsgvo]
Abhängigkeiten: [NFR-002, NFR-003]
Betroffene Module: [ALL]
---

# NFR-001: Strikte Trennung von Frontend und Backend

## 1. Business Case

### 1.1 User Story

**Als** Systemarchitekt  
**möchte ich** eine klare technische und organisatorische Trennung zwischen Präsentationsschicht, Geschäftslogik und Datenhaltung  
**um** Skalierbarkeit, Wartbarkeit, Sicherheit und die Austauschbarkeit einzelner Komponenten zu gewährleisten.

**Als** Produktmanager  
**möchte ich** dass Frontend und Backend unabhängig voneinander entwickelt und deployed werden können  
**um** schnellere Release-Zyklen und parallele Entwicklung durch separate Teams zu ermöglichen.

**Als** DevOps Engineer  
**möchte ich** dass Frontend und Backend getrennt skalierbar sind  
**um** Ressourcen effizient zu nutzen und unterschiedliche Last-Charakteristika optimal zu bedienen.

### 1.2 Geschäftliche Motivation

Die Agrotech-Anwendung muss:

1. **Multi-Channel-fähig** sein (Web, Mobile, IoT-Devices)
2. **API-getrieben** agieren für Third-Party-Integrationen
3. **Cloud-native** und **edge-computing-ready** sein
4. **Sicherheitskritische** Logik serverseitig isolieren
5. **Internationale Teams** parallel arbeiten lassen

### 1.3 Fachliche Beschreibung

Die strikte Trennung verhindert:

- **Logik-Duplikation** (z.B. GDD-Berechnung im Frontend UND Backend)
- **Sicherheitslücken** (z.B. direkte DB-Zugriffe vom Client)
- **Vendor Lock-in** (z.B. UI-Framework-Wechsel ohne Backend-Refactoring)
- **Skalierungsprobleme** (z.B. ML-Services können nicht separat skaliert werden)

Praktisches Beispiel:

> **Szenario**: Ein Gärtner nutzt die Web-App, eine Partnerfarm verwendet die Mobile-App, und ein IoT-Bewässerungssystem sendet automatisierte Anfragen.  
> **Anforderung**: Alle drei Clients kommunizieren über die **gleiche, versionierte REST-API** ohne redundante Backend-Logik.

---

## 2. Architekturelle Grundprinzipien

### 2.1 Layered Architecture (5-Schichten-Modell)

```
┌─────────────────────────────────────────┐
│  1. PRESENTATION LAYER (Frontend)       │
│     - React/Flutter                     │
│     - State Management (Redux Toolkit)  │
│     - API Client (Axios)               │
└─────────────────┬───────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────┐
│  2. API LAYER (FastAPI)                 │
│     - REST Endpoints                    │
│     - Auth Middleware (JWT)             │
│     - Rate Limiting                     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  3. BUSINESS LOGIC LAYER                │
│     - Domain Services                   │
│     - Calculation Engines (GDD, VPD)    │
│     - State Machines (Plant Phases)     │
│     - Rule Engines (Irrigation, IPM)    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  4. DATA ACCESS LAYER                   │
│     - Repository Pattern                │
│     - AQL Query Builder              │
│     - ORM (ArangoDB Driver)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  5. PERSISTENCE LAYER                   │
│     - ArangoDB Multi-Model Database     │
│     - TimescaleDB (Sensor Data)         │
│     - Redis (Cache)                     │
└─────────────────────────────────────────┘
```

### 2.2 Verbotene Kopplungen

|❌ Verboten|✅ Erlaubt|
|---|---|
|Frontend → ArangoDB Driver|Frontend → API Client|
|Frontend → Business Logic|Frontend → Local Validation|
|Business Logic → UI Components|Business Logic → DTOs|
|API Layer → UI State|API Layer → Response Schemas|

---

## 3. Funktionale Abgrenzung

### 3.1 Frontend-Verantwortlichkeiten

#### Erlaubte Aufgaben

```python
# ✅ FRONTEND - Lokale Validierung
def validate_email_format(email: str) -> bool:
    """Nur Format-Prüfung, keine Duplikat-Checks"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# ✅ FRONTEND - UI State Management
class PlantListStore:
    plants: list[PlantDTO]
    selected_plant_id: str | None
    is_loading: bool
```

#### Verbotene Aufgaben

```python
# ❌ FRONTEND - Geschäftslogik gehört ins Backend!
def calculate_gdd(temp_min: float, temp_max: float, base_temp: float) -> float:
    """NIEMALS im Frontend implementieren!"""
    return max(0, (temp_min + temp_max) / 2 - base_temp)

# ❌ FRONTEND - Direkte DB-Zugriffe
from arango import ArangoClient  # Import ist verboten!
```

### 3.2 Backend-Verantwortlichkeiten

```python
# ✅ BACKEND - Geschäftslogik
from pydantic import BaseModel
from datetime import date

class GDDCalculator:
    """Growing Degree Days Calculation Service"""
    
    def calculate_gdd(
        self,
        temp_min: float,
        temp_max: float,
        base_temp: float
    ) -> float:
        """
        Berechnet Growing Degree Days nach Standard-Formel.
        
        Args:
            temp_min: Tagesminimum in °C
            temp_max: Tagesmaximum in °C
            base_temp: Basistemperatur der Pflanze in °C
        
        Returns:
            GDD-Wert (0 wenn negativ)
        """
        avg_temp = (temp_min + temp_max) / 2
        return max(0, avg_temp - base_temp)
    
    def calculate_cumulative_gdd(
        self,
        plant_id: str,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Summiert GDD über einen Zeitraum aus ArangoDB-Sensordaten.
        
        Args:
            plant_id: UUID der Pflanze
            start_date: Startdatum
            end_date: Enddatum
        
        Returns:
            Kumulierter GDD-Wert
        """
        # AQL-Query nur im Backend!
        aql = """
        FOR p IN plants
            FILTER p._key == @plant_id
            FOR v, e IN 1..1 OUTBOUND p located_in
                FOR r IN sensor_readings
                    FILTER r.location_id == v._key
                    FILTER r.timestamp >= @start_date
                    FILTER r.timestamp <= @end_date
                    RETURN {
                        temp_min: r.temp_min,
                        temp_max: r.temp_max,
                        base_temp: p.base_temp
                    }
        """
        # Implementation...
```

### 3.3 Regelwerke ausschließlich im Backend

**Beispiel: Bewässerungslogik**

```python
# ✅ BACKEND ONLY
class IrrigationRuleEngine:
    """
    Entscheidet, ob bewässert werden muss basierend auf:
    - Substratfeuchtigkeit
    - Pflanzenwachstumsphase
    - VPD
    - Wetterdaten
    """
    
    def should_irrigate(
        self,
        plant_id: str,
        current_moisture: float
    ) -> tuple[bool, str]:
        """
        Returns:
            (should_irrigate, reason)
        """
        plant = self.repo.get_plant(plant_id)
        
        # Phasenspezifische Schwellenwerte
        threshold = self._get_moisture_threshold(
            plant.current_phase,
            plant.species.water_needs
        )
        
        if current_moisture < threshold:
            return (
                True,
                f"Moisture {current_moisture}% below threshold {threshold}%"
            )
        
        # VPD-Check
        vpd = self._calculate_current_vpd(plant.location_id)
        if vpd > 1.5 and current_moisture < 60:
            return (True, "High VPD detected, preventive irrigation")
        
        return (False, "No irrigation needed")
```

---

## 4. API-Design-Anforderungen

### 4.1 API-First-Ansatz

**Prinzip**: Jede Backend-Funktion ist ausschließlich über API erreichbar.

```python
# backend/api/v1/plants.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

router = APIRouter(prefix="/api/v1/plants", tags=["plants"])

@router.post("/", response_model=PlantResponse)
async def create_plant(
    plant_data: PlantCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[ArangoClient, Depends(get_db)]
) -> PlantResponse:
    """
    Erstellt eine neue Pflanze im System.
    
    Geschäftsregeln (Backend):
    - Validiert Substrat-Kompatibilität
    - Prüft Mischkultur-Kompatibilität am Standort
    - Initialisiert GDD-Tracking
    - Erstellt initiale Aufgaben
    """
    service = PlantService(db)
    
    try:
        plant = service.create_plant(
            species_id=plant_data.species_id,
            location_id=plant_data.location_id,
            planted_date=plant_data.planted_date,
            user_id=current_user.id
        )
        return PlantResponse.model_validate(plant)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 4.2 Schnittstellenstandards

#### REST API Konventionen

```yaml
# openapi.yaml (Ausschnitt)
paths:
  /api/v1/plants:
    get:
      summary: Liste alle Pflanzen
      parameters:
        - name: location_id
          in: query
          schema:
            type: string
            format: uuid
        - name: phase
          in: query
          schema:
            type: string
            enum: [seedling, vegetative, flowering, harvest]
      responses:
        200:
          description: Erfolgreiche Antwort
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Plant'
```

#### Versionierung

```
/api/v1/plants          ← Aktuelle Version
/api/v2/plants          ← Breaking Changes
/api/v1/plants/archive  ← Deprecated, wird entfernt
```

<!-- Quelle: Smart-Home-HA-Integration Review A-001 -->
#### API-Stabilität für M2M-Consumer

Die REST API bedient nicht nur Browser-Clients (React-Frontend), sondern auch **Machine-to-Machine-Consumer**:

- **Home Assistant Custom Integration** (`kamerplanter-ha`) — pollt Pflanzen-, Tank- und Aufgabendaten
- **IoT-Gateways** — schreiben Sensordaten via `POST /api/v1/t/{slug}/observations`
- **CI/CD-Pipelines** — automatisierte Seed-Daten-Imports, Health-Checks
- **Monitoring-Systeme** — Dashboard-Daten, Metriken

**Stabilitätsgarantien für `/api/v1/`:**

| Regel | Beschreibung |
|-------|-------------|
| **12-Monats-Garantie** | Alle v1-Endpoints bleiben mindestens 12 Monate nach Release stabil. Breaking Changes nur in `/api/v2/`. |
| **Additive Änderungen erlaubt** | Neue Felder in Response-Objekten sind erlaubt (M2M-Clients MÜSSEN unbekannte Felder ignorieren). |
| **Immutable Identifiers** | `_key`-Werte in ArangoDB sind stabil und dürfen nicht geändert werden. M2M-Clients verwenden `_key` als persistente Referenz. |
| **OpenAPI-Pflicht** | Alle Response-Properties MÜSSEN im OpenAPI-Schema dokumentiert sein (siehe NFR-005 §2.4). Undokumentierte Felder sind nicht Teil des API-Kontrakts. |
| **Deprecation-Vorlauf** | Vor Entfernung eines Endpoints: mindestens 3 Monate `Sunset`-Header + Deprecation-Hinweis in OpenAPI-Spec. |

**Versionierungsstrategie für Breaking Changes:**

```
v1 (stabil)      v2 (Breaking Changes)
────────────     ──────────────────────
GET /api/v1/plants  →  GET /api/v2/plants (neues Schema)
                        ↑ Parallelbetrieb für 6 Monate
                        ↓ v1 wird mit Sunset-Header markiert
```

### 4.3 Verbotene Praktiken

```python
# ❌ VERBOTEN - Serverseitiges Rendering
@app.get("/plants")
def list_plants_html():
    plants = get_plants()
    return render_template("plants.html", plants=plants)

# ❌ VERBOTEN - Mixed Concerns
@app.get("/api/plants")
def list_plants(include_ui: bool = False):
    plants = get_plants()
    if include_ui:  # NIEMALS!
        return {"data": plants, "html": render(plants)}
    return plants
```

---

## 5. GraphDB-Zugriffsbeschränkung

### 5.1 Zugriffskontrolle

```python
# ✅ BACKEND - Erlaubter Zugriff
from arango import ArangoClient

class PlantRepository:
    def __init__(self, client: ArangoClient):
        self._client = client
        self._db = client.db('agrotech_db', username='user', password='pass')
    
    def get_plant_by_id(self, plant_id: str) -> Plant:
        aql = """
        FOR p IN plants
            FILTER p._key == @plant_id
            LET species = FIRST(
                FOR s IN species
                    FILTER p.species_id == s._key
                    RETURN s
            )
            LET location = FIRST(
                FOR v, e IN 1..1 OUTBOUND p located_in
                    RETURN v
            )
            RETURN {plant: p, species: species, location: location}
        """
        cursor = self._db.aql.execute(
            aql,
            bind_vars={'plant_id': plant_id}
        )
        result = next(cursor, None)
        return self._map_to_plant(result) if result else None
```

```javascript
// ❌ FRONTEND - Absolut verboten!
import { Database } from 'arangojs';  // NIEMALS importieren!

// Auch nicht so:
const db = new Database({
  url: 'http://localhost:8529',  // Credentials im Frontend = Sicherheitslücke!
  auth: { username: 'root', password: 'password' }
});
```

### 5.2 Sicherheitsmechanismen

**Backend-Konfiguration**:

```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    arangodb_url: str
    arangodb_database: str
    arangodb_user: str
    arangodb_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Credentials NIEMALS in Frontend-zugänglichen Dateien!
    )

settings = Settings()
```

**Kubernetes Secret** (siehe NFR-002):

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: arangodb-credentials
type: Opaque
data:
  url: aHR0cDovL2FyYW5nb2RiOjg1Mjk=  # Base64: http://arangodb:8529
  database: YWdyb3RlY2hfZGI=          # Base64: agrotech_db
  user: cm9vdA==                      # Base64: root
  password: c3VwZXJzZWNyZXQ=          # Base64: supersecret
```

---

## 6. Sicherheitsanforderungen

### 6.1 Authentifizierung & Autorisierung

> **⚠ ABGELÖST:** Diese Sektion wird durch **REQ-023 (Benutzerverwaltung & Authentifizierung)** vollständig ersetzt. REQ-023 spezifiziert:
> - **Authlib** anstelle von `python-jose` (aktiv maintained, OIDC/PKCE built-in)
> - **15-Minuten-Access-Tokens** (statt 1h) mit Refresh-Token-Rotation (30 Tage)
> - Lokale Accounts (E-Mail + Passwort) + OAuth2/OIDC (Google, GitHub, Apple, generische OIDC-Provider)
> - Mandantenspezifische Rollen im JWT-Payload (`tenant_roles`)
> - Vollständige Spezifikation: Engines, Services, API-Endpoints, Frontend, Abnahmekriterien
>
> Das nachfolgende Code-Beispiel dient nur noch als historische Referenz.

```python
# DEPRECATED — siehe REQ-023 für aktuelle Spezifikation
# backend/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTAuthService:
    SECRET_KEY = settings.jwt_secret
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE = timedelta(hours=1)

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + self.ACCESS_TOKEN_EXPIRE
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.SECRET_KEY, self.ALGORITHM)

    def verify_token(self, token: str) -> str:
        """Returns user_id if valid, raises HTTPException otherwise"""
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise JWTError("Invalid token")
            return user_id
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### 6.2 CORS-Konfiguration

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.agrotech.example.com",  # Produktions-Frontend
        "http://localhost:5173"               # Entwicklung (Vite)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### 6.3 Rate Limiting

> **Referenz:** SEC-H-002 (IT-Security-Review)

Rate Limiting ist eine **verbindliche Anforderung** für alle API-Endpunkte. Die Implementierung erfolgt über `slowapi` mit Redis-Backend zur cluster-weiten Synchronisierung.

**Differenzierte Rate-Limiting-Tiers:**

| Tier | Limit | Scope | Beschreibung |
|------|-------|-------|-------------|
| **Anonym** | 30 req/min | pro IP | Unauthentifizierte Requests (Health, Login, Register, Public Seed-Daten) |
| **Authentifiziert (Read)** | 200 req/min | pro User | GET-Requests auf geschützte Endpunkte |
| **Authentifiziert (Write)** | 30 req/min | pro User | POST/PUT/PATCH/DELETE-Requests |
| **Login/Register** | 5 req/15 min | pro IP | Schutz gegen Brute-Force (siehe REQ-023 Login-Throttle) |
| **CSV-Upload** | 5 req/h + max 10 MB | pro User | REQ-012 Stammdaten-Import |
| **Datenexport** | 3 req/h | pro User | REQ-025 DSGVO-Datenexport |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| RL-001 | Alle API-Endpunkte MÜSSEN einem Rate-Limiting-Tier zugeordnet sein. | MUSS |
| RL-002 | Rate-Limits MÜSSEN über Redis cluster-weit synchronisiert werden (kein In-Memory-Limiting). | MUSS |
| RL-003 | Bei Überschreitung MUSS HTTP 429 (Too Many Requests) mit `Retry-After`-Header zurückgegeben werden. | MUSS |
| RL-004 | Login-Endpunkte MÜSSEN dem Login-Tier folgen (5 Versuche/15 Min pro IP). Dies ist ein Spezialfall des allgemeinen Rate Limitings; die detaillierte Account-Lockout-Logik ist in REQ-023 spezifiziert. | MUSS |
| RL-005 | CSV-Upload MUSS zusätzlich eine maximale Dateigröße von 10 MB erzwingen. | MUSS |

**Technologie:** `slowapi` (FastAPI-kompatibel) + Redis-Backend

```python
# Beispiel: Tier-Konfiguration (illustrativ)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/1"
)
```

### 6.4 HTTP Security Headers

> **Referenz:** SEC-M-003 (IT-Security-Review)

Alle HTTP-Responses MÜSSEN die folgenden Security Headers enthalten. Die Header werden als Traefik-Middleware (siehe NFR-002 §3.5, `default-security-headers@kubernetescrd`) konfiguriert und gelten für alle Routen.

| Header | Wert | Begründung |
|--------|------|-----------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | HSTS — erzwingt HTTPS für 2 Jahre, Preload-Liste |
| `Content-Security-Policy` | siehe unten | XSS-Schutz durch Allowlisting |
| `X-Content-Type-Options` | `nosniff` | Verhindert MIME-Sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking-Schutz |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer-Leakage minimieren |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` | Ungenutzte Browser-APIs deaktivieren |

**Content-Security-Policy (CSP):**

```
default-src 'self';
script-src 'self' 'nonce-{random}';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self';
connect-src 'self' https://sentry.io;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

- `'nonce-{random}'` für Inline-Scripts: Vite und MUI generieren zur Laufzeit Inline-Skripte. Die Nonce wird pro Request serverseitig erzeugt und als Meta-Tag im HTML-Template eingebettet.
- `'unsafe-inline'` für Styles: MUI 7 verwendet Emotion (CSS-in-JS), das Inline-Styles injiziert. Langfristig SOLL auf Nonce-basierte Styles migriert werden.
- `connect-src` erlaubt Sentry **nur nach Einwilligung** (siehe UI-NFR-013). Die CSP-Direktive ist präventiv gesetzt; die tatsächliche Initialisierung erfolgt consent-gesteuert.

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| SH-001 | Alle HTTP-Responses MÜSSEN die oben definierten Security Headers enthalten. | MUSS |
| SH-002 | CSP MUSS Nonces für Inline-Scripts verwenden (keine `'unsafe-inline'` für Scripts). | MUSS |
| SH-003 | Die Header-Konfiguration MUSS zentral in der Traefik-Middleware erfolgen (NFR-002). | MUSS |
| SH-004 | In der Entwicklungsumgebung DARF HSTS deaktiviert werden (kein `preload`). | DARF |

### 6.5 Globale Eingabevalidierung

> **Referenz:** SEC-H-003 (IT-Security-Review)

Alle API-Endpunkte MÜSSEN maximale Feldlängen erzwingen. Die folgende Tabelle definiert die **zentrale Feldlängen-Policy**, die für alle REQs gilt, sofern nicht explizit abweichend spezifiziert.

**Zentrale Feldlängen-Policy:**

| Feldtyp | Max. Länge | Pydantic-Enforcement | Beispielfelder |
|---------|-----------|---------------------|---------------|
| `name` / `title` | 200 Zeichen | `Field(max_length=200)` | `scientific_name`, `common_name`, `display_name`, Tenant-Name |
| `description` | 5.000 Zeichen | `Field(max_length=5000)` | Beschreibungsfelder aller Entitäten |
| `notes` | 10.000 Zeichen | `Field(max_length=10000)` | Freitext-Notizen (FeedingEvent, Inspection, etc.) |
| `url` | 2.083 Zeichen | `Field(max_length=2083)` | `avatar_url`, `callback_url`, externe Links |
| `email` | 254 Zeichen | `Field(max_length=254)` | E-Mail-Adressen (RFC 5321) |
| `slug` | 63 Zeichen | `Field(max_length=63)` | `tenant_slug` (DNS-kompatibel) |
| `list` (Einträge) | 100 Einträge | `Field(max_length=100)` | `common_names`, `photo_refs`, `tags` |
| `file_upload` | 10 MB | Middleware / `UploadFile` | CSV-Import (REQ-012) |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| EV-001 | Alle String-Felder in Pydantic-Modellen MÜSSEN `max_length` definieren. | MUSS |
| EV-002 | Alle Listen-Felder MÜSSEN eine maximale Anzahl an Einträgen definieren. | MUSS |
| EV-003 | Abweichungen von der zentralen Policy MÜSSEN im jeweiligen REQ-Dokument dokumentiert und begründet werden. | MUSS |
| EV-004 | File-Uploads MÜSSEN MIME-Type-Validierung und Größenbegrenzung durchsetzen. | MUSS |

### 6.6 MQTT-Security

> **Referenz:** SEC-H-006 (IT-Security-Review)

MQTT wird für die Kommunikation mit Sensoren (REQ-005) und Aktoren (REQ-018) eingesetzt. Da kompromittierte MQTT-Clients physische Schäden verursachen können (unkontrollierte Bewässerung, CO2-Zufuhr, Beleuchtung), gelten strenge Sicherheitsanforderungen.

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| MQ-001 | MQTT-Kommunikation MUSS über TLS verschlüsselt erfolgen (Port 8883). Unverschlüsselte Verbindungen (Port 1883) DÜRFEN NICHT akzeptiert werden. | MUSS |
| MQ-002 | Alle MQTT-Clients MÜSSEN sich authentifizieren: Username/Password ODER Client-Zertifikate. Anonyme Verbindungen DÜRFEN NICHT akzeptiert werden. | MUSS |
| MQ-003 | Topic-ACLs MÜSSEN pro Device konfiguriert werden. | MUSS |
| MQ-004 | Wildcard-Subscriptions (`#`, `+`) auf Steuerungstopics (`actuators/…`) DÜRFEN NICHT erlaubt werden. | MUSS |
| MQ-005 | Der MQTT-Broker MUSS Verbindungsversuche mit ungültigen Credentials loggen (Security-Audit-Log, siehe §10.2). | MUSS |

**Topic-ACL-Schema:**

| Client-Typ | Publish | Subscribe |
|------------|---------|-----------|
| Sensor-Device | `sensors/{device_id}/+` | — |
| Aktor-Device | `actuators/{device_id}/status` | `actuators/{device_id}/command` |
| Backend-Service | `actuators/{device_id}/command` | `sensors/#`, `actuators/+/status` |

### 6.7 Datenschutz-Folgenabschätzung (DSFA)

> **Referenz:** SEC-K-005 (IT-Security-Review)

Sensordaten (CO2-Konzentration, Temperatur, Luftbewegung, manuelle Aktor-Overrides) können Rückschlüsse auf Anwesenheit und Verhalten von Personen ermöglichen — insbesondere in kleinen Räumen wie Growzelten oder Kellerräumen. Dies betrifft primär REQ-005 (Hybrid-Sensorik) und REQ-018 (Umgebungssteuerung/Aktorik).

Vor Inbetriebnahme der Sensorerfassung MUSS eine **Datenschutz-Folgenabschätzung (DSFA)** nach Art. 35 DSGVO durchgeführt werden. Die DSFA MUSS mindestens die folgenden Risiken bewerten:

- CO2-Kurven als Proxy für Anwesenheitserkennung
- Temperatur-Anomalien durch Körperwärme in kleinen Räumen
- Manuelle Aktor-Overrides als Nachweis von Anwesenheitszeiten
- Langzeitspeicherung von Zeitreihen in TimescaleDB

Technische Maßnahmen zur Risikominimierung: Downsampling-Policy (NFR-011: 90 Tage Rohdaten → 2 Jahre Stundenmittel → 5 Jahre Tagesmittel), Einwilligung für Sensorerfassung (REQ-025 ConsentEngine, Consent-Kategorie `sensor_data_collection`).

---

## 7. Deployment-Anforderungen

### 7.1 Container-Separierung

```yaml
# docker-compose.yml (Entwicklung)
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ARANGODB_URL=http://arangodb:8529
      - ARANGODB_DATABASE=agrotech_db
    depends_on:
      - arangodb
    volumes:
      - ./backend:/app  # Hot reload
  
  arangodb:
    image: arangodb:3.11
    ports:
      - "8529:8529"  # Web UI & HTTP API
    environment:
      - ARANGO_ROOT_PASSWORD=devpassword
    volumes:
      - arangodb_data:/var/lib/arangodb3

volumes:
  arangodb_data:
```

### 7.2 Kubernetes-Deployment (Produktion)

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agrotech-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agrotech-backend
  template:
    metadata:
      labels:
        app: agrotech-backend
    spec:
      containers:
      - name: backend
        image: agrotech/backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ARANGODB_URL
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: url
        - name: ARANGODB_DATABASE
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: database
        - name: ARANGODB_USER
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: user
        - name: ARANGODB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: password
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
---
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agrotech-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agrotech-frontend
  template:
    metadata:
      labels:
        app: agrotech-frontend
    spec:
      containers:
      - name: frontend
        image: agrotech/frontend:v1.0.0
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
```

### 7.3 Unabhängige Skalierung

```yaml
# k8s/hpa-backend.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agrotech-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 8. Monitoring & Logging

### 8.1 Backend-Monitoring

```python
# backend/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metriken
api_requests_total = Counter(
    'api_requests_total',
    'Total API Requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API Request Duration',
    ['method', 'endpoint']
)

active_plants = Gauge(
    'active_plants_total',
    'Total active plants in system'
)

# Middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### 8.2 Strukturiertes Logging

```python
# backend/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Verwendung
@app.post("/api/v1/plants")
async def create_plant(plant_data: PlantCreate):
    logger.info(
        "plant_creation_started",
        species_id=plant_data.species_id,
        location_id=plant_data.location_id,
        user_id=current_user.id
    )
    
    try:
        plant = service.create_plant(plant_data)
        logger.info(
            "plant_created",
            plant_id=plant.id,
            duration_ms=duration
        )
    except Exception as e:
        logger.error(
            "plant_creation_failed",
            error=str(e),
            exc_info=True
        )
        raise
```

### 8.3 Frontend Error Tracking

```typescript
// frontend/src/monitoring/sentry.ts
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay()
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1
});

// API-Client mit Fehlerbehandlung
export async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      options
    );

    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }

    return await response.json();
  } catch (error) {
    Sentry.captureException(error, {
      tags: { endpoint },
      contexts: { api_call: { endpoint, method: options?.method } }
    });
    throw error;
  }
}
```

> **Referenz:** SEC-M-005 (IT-Security-Review)

**DSGVO-Konformität für Sentry:**

Sentry überträgt bei Fehler-Reports potenziell personenbezogene Daten (IP-Adressen, URLs mit Tenant-Slugs, User-Agent, Session-Replay). Die folgenden Anforderungen gelten:

| # | Regel | Stufe |
|---|-------|-------|
| SE-001 | Sentry DARF ERST nach expliziter Einwilligung des Nutzers initialisiert werden (Consent-Kategorie `error_tracking`, siehe UI-NFR-013). | MUSS |
| SE-002 | PII-Scrubbing MUSS aktiviert sein: `beforeSend`-Hook MUSS IP-Adressen, E-Mail-Adressen und User-Namen aus Events entfernen. | MUSS |
| SE-003 | Session-Replay DARF NUR mit separater expliziter Einwilligung aktiviert werden (Consent-Kategorie `error_tracking` mit Sub-Option `session_replay`). | MUSS |
| SE-004 | Sentry MUSS entweder als Self-Hosted-Instanz ODER über ein EU-Rechenzentrum betrieben werden. Bei Nutzung von Sentry SaaS (US) MUSS ein Auftragsverarbeitungsvertrag (AVV) nach Art. 28 DSGVO abgeschlossen und das EU-US Data Privacy Framework als Rechtsgrundlage dokumentiert werden. | MUSS |
| SE-005 | Bei Widerruf der Einwilligung MUSS Sentry sofort deaktiviert werden (kein Nachladen, kein Tracking bis zum nächsten Seitenaufruf). | MUSS |

---

## 9. Qualitätssicherungs-Anforderungen

### 9.1 Backend-Tests

```python
# backend/tests/test_plant_service.py
import pytest
from unittest.mock import Mock, patch

class TestPlantService:
    @pytest.fixture
    def service(self, mock_db):
        return PlantService(mock_db)
    
    def test_create_plant_validates_substrate_compatibility(self, service):
        """Substrat-Kompatibilität wird geprüft"""
        with pytest.raises(ValidationError, match="incompatible substrate"):
            service.create_plant(
                species_id="acidic-loving-plant",
                location_id="alkaline-substrate-location"
            )
    
    def test_create_plant_checks_companion_planting(self, service):
        """Mischkultur-Kompatibilität wird geprüft"""
        # Tomate und Kartoffel sind inkompatibel
        with pytest.raises(ValidationError, match="incompatible neighbor"):
            service.create_plant(
                species_id="tomato",
                location_id="location-with-potato"
            )
```

### 9.2 Frontend-Tests

```typescript
// frontend/src/components/PlantForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlantForm } from './PlantForm';
import { mockApiClient } from '@/test-utils';

describe('PlantForm', () => {
  it('submits data to API and handles success', async () => {
    const mockCreate = vi.fn().mockResolvedValue({ id: '123' });
    mockApiClient.plants.create = mockCreate;
    
    render(<PlantForm />);
    
    await userEvent.selectOptions(
      screen.getByLabelText('Species'),
      'tomato'
    );
    await userEvent.click(screen.getByText('Create Plant'));
    
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        species_id: 'tomato',
        location_id: expect.any(String)
      });
    });
  });
  
  it('displays backend validation errors', async () => {
    mockApiClient.plants.create = vi.fn().mockRejectedValue({
      status: 400,
      data: { detail: 'Incompatible substrate' }
    });
    
    render(<PlantForm />);
    await userEvent.click(screen.getByText('Create Plant'));
    
    expect(
      await screen.findByText('Incompatible substrate')
    ).toBeInTheDocument();
  });
});
```

### 9.3 API Contract Testing

```python
# backend/tests/test_api_contract.py
import pytest
from pydantic import ValidationError

class TestAPIContract:
    def test_plant_create_request_schema(self):
        """API akzeptiert nur valide PlantCreate-Schemas"""
        valid_data = {
            "species_id": "uuid-format",
            "location_id": "uuid-format",
            "planted_date": "2026-02-25"
        }
        plant_create = PlantCreate(**valid_data)
        assert plant_create.species_id == "uuid-format"
        
        # Invalide Daten werden abgelehnt
        with pytest.raises(ValidationError):
            PlantCreate(species_id="invalid")  # Fehlt location_id
    
    def test_plant_response_schema(self):
        """API-Response entspricht PlantResponse-Schema"""
        response_data = {
            "id": "plant-uuid",
            "species": {"name": "Tomato"},
            "location": {"name": "Greenhouse A"},
            "current_phase": "vegetative"
        }
        plant_response = PlantResponse(**response_data)
        assert plant_response.id == "plant-uuid"
```

---

## 10. ArangoDB-Modellierung (Architektur-Support)

### 10.1 Meta-Collections für API-Versionierung

```javascript
// ArangoDB - Tracking von API-Versionen
db._create("api_versions");
db._createEdgeCollection("provides_endpoint");

// API-Version erstellen
db.api_versions.save({
  _key: "v1",
  version: "v1",
  deprecated: false,
  sunset_date: null
});

// Endpoint erstellen
db._create("api_endpoints");
db.api_endpoints.save({
  _key: "plants_post",
  path: "/api/v1/plants",
  method: "POST",
  rate_limit: 100
});

// Beziehung erstellen
db.provides_endpoint.save({
  _from: "api_versions/v1",
  _to: "api_endpoints/plants_post"
});
```

### 10.2 Audit-Trail für API-Zugriffe

> **Referenz:** SEC-H-007 (IT-Security-Review)

Der Audit-Trail ist eine **verbindliche Anforderung**, kein optionales Feature. Alle sicherheitsrelevanten Ereignisse MÜSSEN in der `audit_logs`-Collection (mit `performed_by`- und `affected`-Edge-Collections) protokolliert werden.

**Pflicht-Events:**

| Kategorie | Events | Beispiel |
|-----------|--------|---------|
| **Authentifizierung** | Login (Erfolg/Fehlschlag), Logout, Account-Lockout, Passwort-Änderung, Passwort-Reset | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`, `AUTH_LOCKOUT` |
| **Autorisierung** | Rollen-/Membership-Änderungen, Tenant-Zuordnung | `AUTHZ_ROLE_CHANGED`, `AUTHZ_MEMBERSHIP_CREATED` |
| **Datenmanipulation** | Löschungen (Soft/Hard), Tenant-Löschung mit Kaskade | `DATA_ENTITY_DELETED`, `DATA_TENANT_DELETED` |
| **Admin-Aktionen** | OIDC-Provider-Konfiguration, Account-Linking/-Unlinking, User-Administration | `ADMIN_OIDC_PROVIDER_CREATED`, `ADMIN_ACCOUNT_LINKED` |
| **DSGVO-Aktionen** | Datenexport-Anfrage, Löschantrag, Consent-Änderung, Daten-Anonymisierung | `DSGVO_EXPORT_REQUESTED`, `DSGVO_ERASURE_EXECUTED` |
| **Security** | Token-Revocation, MQTT-Auth-Failure, Rate-Limit-Überschreitung | `SEC_TOKEN_REVOKED`, `SEC_RATE_LIMIT_EXCEEDED` |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| AL-001 | Alle oben genannten Pflicht-Events MÜSSEN im Audit-Log erfasst werden. | MUSS |
| AL-002 | Audit-Log-Einträge DÜRFEN NICHT nachträglich verändert oder gelöscht werden (append-only). | MUSS |
| AL-003 | Retention: Audit-Logs MÜSSEN mindestens 2 Jahre aufbewahrt werden (BSI IT-Grundschutz). Danach MUSS die IP-Adresse anonymisiert werden; der restliche Eintrag bleibt erhalten. | MUSS |
| AL-004 | Ein Prometheus-Counter `audit_events_total{event_type, result}` MUSS für Monitoring und Alerting exportiert werden. | MUSS |
| AL-005 | Jeder Audit-Log-Eintrag MUSS mindestens enthalten: `timestamp` (ISO 8601), `event_type`, `actor` (User-Key oder `system`), `ip_address`, `result` (success/failure), `details` (Event-spezifisch). | MUSS |

**Referenz-Implementierung** (Collections und AQL-Beispiel):

```javascript
// ArangoDB - Jede relevante Mutation wird geloggt
db._create("audit_logs");
db._createEdgeCollection("performed_by");
db._createEdgeCollection("affected");

// Audit-Log erstellen
const auditLog = db.audit_logs.save({
  timestamp: new Date().toISOString(),
  action: "CREATE_PLANT",
  ip_address: "192.168.1.100",
  user_agent: "Mozilla/5.0...",
  api_version: "v1"
});

// Beziehungen erstellen
db.performed_by.save({
  _from: `users/${userId}`,
  _to: auditLog._id
});

db.affected.save({
  _from: auditLog._id,
  _to: `plants/${plantId}`
});

// AQL-Query für Audit-Abfrage
const aql = `
  FOR log IN audit_logs
    FILTER log.action == "CREATE_PLANT"
    LET user = FIRST(
      FOR v IN 1..1 INBOUND log performed_by
        RETURN v
    )
    LET plant = FIRST(
      FOR v IN 1..1 OUTBOUND log affected
        RETURN v
    )
    RETURN {log, user, plant}
`;
```

---

## 11. Abhängigkeiten

### 11.1 Technische Abhängigkeiten

|Abhängigkeit|Typ|Begründung|
|---|---|---|
|NFR-002 (Kubernetes)|Infrastruktur|Container-Deployment für Separation|
|NFR-003 (Code Standards)|Code Quality|Englische API-Endpoints, Type Safety|
|REQ-001 (Stammdaten)|Fachlich|Species-Daten für Validierung|
|REQ-002 (Standorte)|Fachlich|Location-Daten für Plant-Erstellung|

### 11.2 Externe Abhängigkeiten

- **FastAPI** >= 0.109.0 (REST API)
- **Pydantic** >= 2.0 (Schema Validation)
- **python-arango** >= 2.0 (ArangoDB Driver)
- **JWT Libraries** (jose, passlib)
- **Prometheus Client** (Monitoring)

---

## 12. Akzeptanzkriterien

### Definition of Done

- [ ] **Architektur-Compliance**
    
    - [ ] Keine Frontend-Komponente importiert ArangoDB-Driver (arangojs/python-arango)
    - [ ] Keine Business-Logic in Frontend-Code
    - [ ] Alle AQL-Queries ausschließlich in Backend-Repositories
    - [ ] Klare Schichten-Trennung in Projektstruktur sichtbar
- [ ] **API-Design**
    
    - [ ] OpenAPI 3.0 Spezifikation vorhanden
    - [ ] Alle Endpoints dokumentiert (Swagger UI)
    - [ ] API-Versionierung implementiert (`/api/v1/`)
    - [ ] Request/Response-Schemas mit Pydantic validiert
- [ ] **Sicherheit**

    - [ ] JWT-Authentifizierung aktiv
    - [ ] CORS korrekt konfiguriert
    - [ ] Globale Rate-Limiting-Policy aktiv (differenzierte Tiers: Anonym/Auth-Read/Auth-Write/Login/Upload)
    - [ ] DB-Credentials in Kubernetes Secrets
    - [ ] Keine Credentials in Frontend-Code oder ENV-Variablen
    - [ ] HTTP Security Headers konfiguriert (CSP mit Nonces, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
    - [ ] Maximale Feldlängen in allen Pydantic-Modellen definiert (gemäß §6.5 Feldlängen-Policy)
    - [ ] Security-Audit-Log für alle Pflicht-Events aktiv (§10.2)
    - [ ] MQTT-Kommunikation TLS-verschlüsselt mit Authentifizierung und Topic-ACLs (§6.6)
    - [ ] Sentry erst nach Einwilligung initialisiert, PII-Scrubbing aktiv (§8.3)
    - [ ] DSFA für Sensordaten vor Inbetriebnahme durchgeführt (§6.7)
- [ ] **Deployment**
    
    - [ ] Frontend und Backend getrennt deploybar
    - [ ] Separate Docker-Container
    - [ ] Kubernetes Deployments für Frontend/Backend/ArangoDB
    - [ ] HPA (Horizontal Pod Autoscaler) konfiguriert
- [ ] **Testing**
    
    - [ ] Backend Unit Tests >= 80% Coverage
    - [ ] API Contract Tests vorhanden
    - [ ] Frontend Component Tests vorhanden
    - [ ] Integration Tests mit Mock-Backend
- [ ] **Monitoring**
    
    - [ ] Prometheus Metrics exportiert
    - [ ] Strukturiertes JSON-Logging
    - [ ] Frontend Error Tracking (Sentry)
    - [ ] API Request Duration Metrics

### Testszenarien

#### Szenario 1: Frontend kann nicht direkt auf ArangoDB zugreifen

```bash
# Test: Frontend-Build schlägt fehl bei ArangoDB-Import
$ cd frontend
$ npm run build

# Erwartung: Kein arangojs in package.json
$ cat package.json | grep arangojs
# Output: (leer)
```

#### Szenario 2: GDD-Berechnung nur im Backend

```python
# Test: Frontend enthält keine GDD-Berechnung
$ grep -r "calculate_gdd\|base_temp" frontend/src/
# Output: (leer, nur API-Aufrufe erlaubt)

# Backend enthält Implementierung
$ grep -r "def calculate_gdd" backend/
backend/services/gdd_calculator.py:    def calculate_gdd(...):
```

#### Szenario 3: API-Authentifizierung wird erzwungen

```bash
# Test: Unauthentifizierte Requests werden abgelehnt
$ curl -X GET http://localhost:8000/api/v1/plants
# Output: {"detail":"Not authenticated"}

# Mit Token funktioniert es
$ curl -X GET http://localhost:8000/api/v1/plants \
  -H "Authorization: Bearer $TOKEN"
# Output: [{"id": "...", "species": {...}}]
```

#### Szenario 4: Frontend und Backend unabhängig deploybar

```bash
# Test: Frontend-Deployment ohne Backend-Änderung
$ kubectl set image deployment/agrotech-frontend \
  frontend=agrotech/frontend:v1.1.0
# Output: deployment.apps/agrotech-frontend image updated

# Backend läuft weiter auf v1.0.0
$ kubectl get pods -l app=agrotech-backend
# Output: agrotech-backend-xxx Running (v1.0.0)
```

#### Szenario 5: API-Versionierung funktioniert

```bash
# v1 ist aktiv
$ curl http://localhost:8000/api/v1/plants
# Output: [...]

# v2 mit Breaking Changes kann parallel existieren
$ curl http://localhost:8000/api/v2/plants
# Output: [{"id": "...", "plant_data": {...}}]  # Neues Schema
```

---

## 13. Risiken bei Nicht-Einhaltung

|Risiko|Auswirkung|Wahrscheinlichkeit|Mitigation|
|---|---|---|---|
|**Sicherheitslücken**|DB-Credentials im Frontend exponiert|Hoch|Code Reviews, Automated Scanning|
|**Logik-Duplikation**|Frontend und Backend berechnen GDD unterschiedlich|Mittel|Strikte Code-Ownership|
|**Skalierungsprobleme**|Frontend und Backend können nicht getrennt skaliert werden|Hoch|Kubernetes HPA|
|**Vendor Lock-in**|UI-Framework-Wechsel erfordert Backend-Refactoring|Niedrig|API Contracts|
|**Hohe technische Schuld**|Monolithische Codebasis wird unmaintainable|Hoch|Architektur-Reviews|

---

## 14. Erweiterbarkeit

### 14.1 Multi-Channel-Support

```
┌─────────────┐
│  Web-App    │───┐
└─────────────┘   │
                  │
┌─────────────┐   │    ┌──────────────┐
│ Mobile App  │───┼───▶│  Backend API │
└─────────────┘   │    └──────────────┘
                  │
┌─────────────┐   │
│ IoT-Devices │───┘
└─────────────┘
```

Jeder Client nutzt die gleiche API ohne Backend-Änderungen.

### 14.2 Microservices-Migration

```
Aktuell (Monolith):
┌────────────────────────────┐
│  Backend (FastAPI)         │
│  - Plant Service           │
│  - Irrigation Service      │
│  - GDD Calculator          │
└────────────────────────────┘

Zukünftig (Microservices):
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Plant Service │  │ Irrigation Svc│  │ Analytics Svc │
└───────────────┘  └───────────────┘  └───────────────┘
       │                  │                   │
       └──────────────────┴───────────────────┘
                          │
                  ┌───────▼────────┐
                  │   API Gateway  │
                  └────────────────┘
```

API Contracts bleiben stabil, interne Architektur kann sich ändern.

### 14.3 Third-Party-Integrationen

```python
# Beispiel: Wetterstation-Integration
class WeatherStationAdapter:
    """Externe Wetterstation nutzt die gleiche API"""
    
    def __init__(self, api_key: str):
        self.client = ApiClient(
            base_url="https://api.agrotech.example.com",
            api_key=api_key
        )
    
    def report_sensor_reading(
        self,
        location_id: str,
        temperature: float,
        humidity: float
    ):
        """Station sendet Daten via öffentlicher API"""
        return self.client.post(
            "/api/v1/sensor-readings",
            json={
                "location_id": location_id,
                "timestamp": datetime.utcnow().isoformat(),
                "temperature": temperature,
                "humidity": humidity
            }
        )
```

---

## 15. Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2)

- [ ] FastAPI-Setup mit Projektstruktur
- [ ] ArangoDB-Connection-Pool
- [ ] JWT-Authentifizierung
- [ ] OpenAPI-Dokumentation

### Phase 2: Core Services (Woche 3-4)

- [ ] Plant Service (CRUD)
- [ ] Location Service
- [ ] Sensor Reading Service
- [ ] GDD Calculator

### Phase 3: Frontend-Integration (Woche 5-6)

- [ ] API Client Library
- [ ] React Components
- [ ] State Management
- [ ] Error Handling

### Phase 4: Deployment (Woche 7-8)

- [ ] Docker Compose Setup
- [ ] Kubernetes Manifests
- [ ] CI/CD Pipeline
- [ ] Monitoring Setup

---

## 16. Checkliste für Code Reviews

**Backend-Review**:

- [ ] Keine UI-spezifische Logik (z.B. Formatierung für Anzeige)
- [ ] Alle Endpoints haben Pydantic-Schemas
- [ ] Auth-Middleware korrekt angewendet
- [ ] AQL-Queries parametrisiert (keine String-Interpolation)
- [ ] Error Handling mit HTTPException

**Frontend-Review**:

- [ ] Keine Business-Logic (GDD, VPD, etc.)
- [ ] Kein ArangoDB-Driver importiert
- [ ] Alle API-Calls gehen über API-Client
- [ ] Validierung nur für UX (echte Validierung im Backend)
- [ ] Keine Credentials im Code

**API-Contract-Review**:

- [ ] Breaking Changes nur in neuer API-Version
- [ ] OpenAPI-Spec aktualisiert
- [ ] Backward Compatibility gewahrt
- [ ] Deprecation Warnings gesetzt

---

## Anhang A: Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  React   │  │  Redux   │  │  Axios   │  │  Sentry  │   │
│  │Components│  │  Store   │  │  Client  │  │  Tracking│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
                       │ (JSON)
┌──────────────────────▼──────────────────────────────────────┐
│                      API LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ FastAPI  │  │   JWT    │  │  CORS    │  │   Rate   │   │
│  │ Router   │  │  Auth    │  │Middleware│  │  Limiter │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Plant   │  │Irrigation│  │   GDD    │  │   IPM    │   │
│  │ Service  │  │  Engine  │  │Calculator│  │  Engine  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   DATA ACCESS LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Plant   │  │ Location │  │  Sensor  │                  │
│  │   Repo   │  │   Repo   │  │   Repo   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   PERSISTENCE LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ ArangoDB │  │Timescale │  │  Redis   │                  │
│  │Multi-Model│ │    DB    │  │  Cache   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

**Dokumenten-Ende**

**Version**: 2.1
**Status**: Produktionsreif
**Letzte Aktualisierung**: 2026-02-27
**Review**: Pending
**Genehmigung**: Pending

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 2.1 | 2026-02-27 | IT-Security-Review-Findings eingearbeitet: §6.3 Rate Limiting formalisiert (SEC-H-002), §6.4 HTTP Security Headers (SEC-M-003), §6.5 Globale Eingabevalidierung (SEC-H-003), §6.6 MQTT-Security (SEC-H-006), §6.7 DSFA-Pflicht (SEC-K-005), §8.3 Sentry DSGVO-Konformität (SEC-M-005), §10.2 Audit-Trail verbindlich (SEC-H-007), §12 Akzeptanzkriterien erweitert |
| 2.0 | 2026-02-25 | Produktionsreife Version, §6.1 Auth an REQ-023 delegiert |