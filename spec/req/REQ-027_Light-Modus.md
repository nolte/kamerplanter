# Spezifikation: REQ-027 - Light-Modus (Anonymer Zugang)

```yaml
ID: REQ-027
Titel: Light-Modus (Anonymer Zugang)
Kategorie: Plattform & Deployment
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-023 v1.3, REQ-024 v1.1, REQ-025
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.0 | 2026-02-27 | Erstversion — Light-Modus als Deployment-Option für lokale Instanzen |

## 1. Business Case

**User Story (Einzelnutzer ohne Login):** "Als Zimmerpflanzen-Besitzer mit 5 Pflanzen auf einem Raspberry Pi möchte ich die App einfach im Browser öffnen und sofort meine Pflanzen verwalten können — ohne mich registrieren, anmelden oder ein Passwort merken zu müssen."

**User Story (Heimnetzwerk):** "Als Hobby-Gärtner mit einem Home-Server möchte ich Kamerplanter im lokalen Netzwerk betreiben und von Laptop, Tablet und Handy darauf zugreifen — ohne dass jedes Gerät ein eigenes Login braucht."

**User Story (Schnelleinstieg):** "Als Erstnutzer möchte ich die App ausprobieren können, ohne vorher eine E-Mail-Adresse angeben zu müssen — damit ich sofort sehe, ob die App zu meinen Bedürfnissen passt."

**User Story (Kein Overhead):** "Als Einzelnutzer auf meinem eigenen Rechner will ich nichts von Tenants, Mitgliederverwaltung, DSGVO-Consent-Bannern oder Einladungssystemen sehen — weil diese Konzepte für mich als einzigen Nutzer irrelevant sind."

**User Story (Onboarding ohne Login):** "Als neuer Nutzer im Light-Modus möchte ich den Onboarding-Wizard (REQ-020) direkt beim ersten Start durchlaufen können — ohne vorher einen Account anlegen zu müssen."

**Beschreibung:**

Zwei Findings aus dem Casual-Houseplant-User-Review ([spec/requirements-analysis/casual-houseplant-user-review.md](../requirements-analysis/casual-houseplant-user-review.md)) motivieren diese Anforderung:

- **N-002 (Registrierung als Pflicht vor dem ersten Nutzen):** Bevor ein Casual User irgendetwas tun kann, muss er sich registrieren, E-Mail verifizieren und einen Tenant erstellen — das ist ein Dealbreaker für jemanden mit 3 Zimmerpflanzen auf der Fensterbank.
- **F-003 (Mandantenverwaltung und DSGVO-Formulare):** Concepts wie "Tenants", "Mitgliederverwaltung", "Consent-Banner" und "Datenschutz-Einstellungen" sind Overhead für Einzelnutzer auf lokalen Instanzen.

Der Light-Modus ist ein **Deployment-Modus** für geschlossene Netzwerke und lokale Instanzen (Raspberry Pi, Home-Server, einzelner PC, Docker Compose auf dem Laptop). Er deaktiviert Auth, Tenants und DSGVO-Consent auf Konfigurationsebene — die App funktioniert sofort nach dem Öffnen.

**Kernkonzepte:**

**Deployment-Modi — `KAMERPLANTER_MODE`:**

Eine einzige Environment-Variable steuert den Betriebsmodus:

| Modus | Wert | Zielgruppe | Netzwerk |
|-------|------|-----------|----------|
| **Full** (Standard) | `full` | Mehrbenutzerbetrieb, SaaS, Gemeinschaftsgärten | Öffentliches Internet, VPN |
| **Light** | `light` | Einzelnutzer, Familien, kleine Gruppen im LAN | Geschlossenes Heimnetzwerk, localhost |

**System-User — Impliziter Nutzer im Light-Modus:**

Beim ersten Start im Light-Modus erzeugt das System automatisch einen **System-User** und einen **System-Tenant**. Alle Aktionen werden diesem User zugeordnet, ohne dass eine Authentifizierung stattfindet.

**Auth-Adapter-Pattern — Austauschbare Authentifizierung:**

Die bestehende Architektur verwendet bereits das Adapter-Pattern (z.B. `IEmailService` → `ConsoleEmailAdapter`/`SmtpEmailAdapter`). Für den Light-Modus wird dieses Pattern auf die Authentifizierung angewendet:

```
IAuthProvider (ABC)
  ├── FullAuthProvider     → JWT + Login + Registrierung (REQ-023)
  └── LightAuthProvider    → System-User, kein Token, immer authentifiziert
```

### 1.1 Szenarien

**Szenario 1: Erster Start im Light-Modus — Raspberry Pi**
```
Voraussetzung: Docker Compose mit KAMERPLANTER_MODE=light

1. Nutzer öffnet http://raspberry:5173 im Browser
2. System erkennt: Erster Start (kein System-User in DB)
3. System erstellt automatisch:
   - System-User: display_name="Gärtner", email="system@local", status=active
   - System-Tenant: name="Mein Garten", slug="mein-garten", type=personal
   - Membership: System-User → System-Tenant, role=admin
4. Onboarding-Wizard (REQ-020) startet direkt (Schritt 1: Erfahrungsstufe)
5. Kein Login-Screen, kein Registrierungs-Formular, kein Consent-Banner
```

**Szenario 2: Mehrere Geräte im LAN — Familiennutzung**
```
Voraussetzung: Light-Modus auf Home-Server

1. Partnerin öffnet Kamerplanter auf dem Tablet
2. Kein Login nötig — System-User wird automatisch verwendet
3. Beide Geräte sehen dieselben Pflanzen (gleicher System-Tenant)
4. Alle Änderungen werden dem System-User zugeordnet
```

**Szenario 3: Onboarding ohne Login-Schritt**
```
Voraussetzung: Light-Modus, erster Start

1. Frontend erkennt: Modus = light
2. Onboarding-Wizard (REQ-020) startet bei Schritt 1 (Erfahrungsstufe)
   → Login-Schritt wird übersprungen (kein Schritt 0)
3. Nutzer wählt Erfahrungsstufe, Starter-Kit, Standort → fertig
4. Pflanzen sind sofort sichtbar
```

**Szenario 4: API-Zugriff ohne Token**
```
Voraussetzung: Light-Modus

1. Frontend sendet API-Request OHNE Authorization-Header:
   GET /api/v1/t/mein-garten/sites
2. get_current_user (LightAuthProvider) gibt System-User zurück
3. get_current_tenant löst "mein-garten" auf, prüft Membership → OK
4. Response: Sites des System-Tenants
```

**Szenario 5: Upgrade von Light auf Full**
```
Voraussetzung: Nutzer hat im Light-Modus 30 Pflanzen angelegt

1. Nutzer möchte Kamerplanter mit Freund teilen
2. Ändert KAMERPLANTER_MODE=full, startet neu
3. Beim nächsten Aufruf: Login-Screen erscheint
4. Nutzer registriert sich (REQ-023)
5. System erkennt: Bestehende Daten im System-Tenant vorhanden
   → Hinweis: "Bestehende Daten können über die Admin-Oberfläche
      Ihrem neuen Account zugewiesen werden"
6. Bestehende Pflanzen bleiben im System-Tenant erhalten
```

## 2. Deployment-Modi-Vergleich

### 2.1 Feature-Visibility-Matrix

| Feature | Light-Modus | Full-Modus |
|---------|:-----------:|:----------:|
| **Login-Screen** | Ausgeblendet | Sichtbar |
| **Registrierung** | Ausgeblendet | Sichtbar |
| **Passwort-vergessen** | Ausgeblendet | Sichtbar |
| **JWT-Token** | Nicht verwendet | Erforderlich |
| **Onboarding-Wizard** | Startet direkt (ohne Login) | Nach Login/Registrierung |
| **Tenant-Switcher** | Ausgeblendet | Sichtbar |
| **Mitgliederverwaltung** | Ausgeblendet | Sichtbar |
| **Einladungssystem** | Ausgeblendet | Sichtbar |
| **Standort-Zuweisungen** | Ausgeblendet | Sichtbar |
| **DSGVO-Consent-Banner** | Ausgeblendet | Sichtbar |
| **Datenschutz-Einstellungen** | Ausgeblendet | Sichtbar |
| **Account-Einstellungen** | Eingeschränkt (nur Sprache, Erfahrungsstufe) | Vollständig |
| **Pflanzen verwalten** | Vollständig | Vollständig |
| **Standorte verwalten** | Vollständig | Vollständig |
| **Pflegeerinnerungen** | Vollständig | Vollständig |
| **Düngung & Bewässerung** | Vollständig | Vollständig |
| **Erntemanagement** | Vollständig | Vollständig |
| **IPM/Pflanzenschutz** | Vollständig | Vollständig |
| **Aufgabenplanung** | Vollständig (ohne User-Zuweisung) | Vollständig |
| **Phasensteuerung** | Vollständig | Vollständig |
| **Stammdaten-Import** | Vollständig | Vollständig |
| **Externe Anreicherung** | Vollständig | Vollständig |

### 2.2 Ausgeblendete UI-Elemente im Light-Modus

| Bereich | Element | Begründung |
|---------|---------|-----------|
| **Sidebar/Navigation** | "Mitglieder"-Menüpunkt | Kein Multi-User |
| **Sidebar/Navigation** | "Einladungen"-Menüpunkt | Kein Multi-User |
| **App-Bar** | Tenant-Switcher-Dropdown | Nur ein Tenant |
| **App-Bar** | User-Avatar + Logout-Button | Kein Login |
| **AccountSettingsPage** | Tab "Sicherheit" (Passwort ändern, Auth-Provider) | Kein Login |
| **AccountSettingsPage** | Tab "Sessions" (aktive Sitzungen) | Kein Login |
| **AccountSettingsPage** | Tab "Datenschutz" (DSGVO-Einstellungen) | Kein personenbezogener Datenschutz |
| **Aufgaben** | "Zuweisen an"-Dropdown bei Tasks | Nur ein User |
| **Standorte** | "Zuweisungen"-Tab auf Location-Detailseite | Kein Multi-User |
| **Routes** | `/login`, `/register`, `/forgot-password` | Nicht erreichbar |
| **Routes** | `/t/{slug}/members`, `/t/{slug}/invitations` | Nicht erreichbar |

## 3. System-User- und System-Tenant-Definition

### 3.1 System-User

Beim ersten Start im Light-Modus wird ein vordefinierter System-User erzeugt:

```python
SYSTEM_USER = User(
    key="system-user",
    email="system@local",
    display_name="Gärtner",       # i18n: "Gardener" (EN)
    status="active",
    email_verified=True,
    avatar_url=None,
    locale="de",
    timezone="Europe/Berlin",
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)
```

**Eigenschaften:**
- `_key: "system-user"` — Deterministisch, kein zufälliger Key
- `email: "system@local"` — Interne Kennung, wird nirgends angezeigt
- Kein Passwort-Hash (kein Login nötig)
- `email_verified: True` — Keine Verifizierung nötig
- `status: "active"` — Sofort einsatzbereit

### 3.2 System-Tenant

```python
SYSTEM_TENANT = Tenant(
    key="system-tenant",
    name="Mein Garten",           # i18n: "My Garden" (EN)
    slug="mein-garten",
    type="personal",
    description="",
    status="active",
    max_members=None,
    settings={"locale": "de", "timezone": "Europe/Berlin"},
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)
```

**Eigenschaften:**
- `_key: "system-tenant"` — Deterministisch
- `slug: "mein-garten"` — Wird in API-URLs verwendet (`/api/v1/t/mein-garten/...`)
- `type: "personal"` — Persönlicher Tenant, nicht organisatorisch
- Alle Ressourcen werden automatisch diesem Tenant zugeordnet

### 3.3 System-Membership

```python
SYSTEM_MEMBERSHIP = Membership(
    role="admin",
    joined_at=datetime.now(UTC),
    status="active",
)
# Edge: has_membership: system-user → system-membership
# Edge: membership_in: system-membership → system-tenant
```

### 3.4 Seed-Logik (Idempotent)

```python
def seed_light_mode(db: StandardDatabase) -> None:
    """Erzeugt System-User + System-Tenant falls nicht vorhanden.
    Idempotent — kann bei jedem Start aufgerufen werden."""
    users = db.collection("users")
    if not users.has("system-user"):
        users.insert({**SYSTEM_USER.dict(), "_key": "system-user"})
        # ... Tenant, Membership, Edges
```

- Wird beim App-Start aufgerufen, wenn `KAMERPLANTER_MODE=light`
- Idempotent: Doppelter Aufruf erzeugt keine Duplikate
- Bestehende Daten bleiben unverändert

## 4. Auth-Adapter-Interface

### 4.1 Interface-Definition (ABC)

```python
from abc import ABC, abstractmethod
from app.domain.models.user import User


class IAuthProvider(ABC):
    """Abstraktes Auth-Interface — austauschbar per Deployment-Modus."""

    @abstractmethod
    def resolve_user(self, authorization: str | None) -> User:
        """Gibt den authentifizierten User zurück.
        Wirft UnauthorizedError wenn Authentifizierung fehlschlägt."""
        ...

    @abstractmethod
    def is_authentication_required(self) -> bool:
        """Gibt True zurück wenn Endpoints einen Authorization-Header erwarten."""
        ...
```

Datei: `src/backend/app/domain/interfaces/auth_provider.py`

### 4.2 Full-Auth-Provider (REQ-023)

```python
class FullAuthProvider(IAuthProvider):
    """JWT-basierte Authentifizierung — Standard für Full-Modus."""

    def __init__(self, token_engine: TokenEngine, user_repo: IUserRepository):
        self._token_engine = token_engine
        self._user_repo = user_repo

    def resolve_user(self, authorization: str | None) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError("Missing or invalid Authorization header.")
        token = authorization.removeprefix("Bearer ")
        payload = self._token_engine.decode_access_token(token)
        user = self._user_repo.get_by_key(payload["sub"])
        if not user or user.status != "active":
            raise UnauthorizedError("User not found or inactive.")
        return user

    def is_authentication_required(self) -> bool:
        return True
```

### 4.3 Light-Auth-Provider

```python
class LightAuthProvider(IAuthProvider):
    """Immer authentifiziert — gibt System-User zurück."""

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    def resolve_user(self, authorization: str | None) -> User:
        user = self._user_repo.get_by_key("system-user")
        if not user:
            raise RuntimeError(
                "System user not found. Run light-mode seed first."
            )
        return user

    def is_authentication_required(self) -> bool:
        return False
```

### 4.4 Dependency-Integration

Die bestehende `get_current_user`-Dependency in `src/backend/app/common/auth.py` delegiert an den konfigurierten Provider:

```python
def get_auth_provider() -> IAuthProvider:
    """Factory — wählt Auth-Provider basierend auf KAMERPLANTER_MODE."""
    if settings.kamerplanter_mode == "light":
        return LightAuthProvider(get_user_repo())
    return FullAuthProvider(get_token_engine(), get_user_repo())


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_provider: IAuthProvider = Depends(get_auth_provider),
) -> User:
    """Extract and validate user — delegiert an Auth-Provider."""
    return auth_provider.resolve_user(authorization)
```

**Auswirkung:** Bestehende Router, die `Depends(get_current_user)` verwenden, funktionieren unverändert — im Light-Modus wird der System-User zurückgegeben, im Full-Modus das JWT-basierte Verhalten.

### 4.5 Tenant-Context im Light-Modus

`get_current_tenant` funktioniert unverändert, da der System-User eine gültige Membership im System-Tenant hat. Der `tenant_slug` in der URL (`/api/v1/t/mein-garten/...`) wird wie gewohnt aufgelöst.

## 5. Settings / Environment-Variablen

### 5.1 Neue Settings

| Variable | Typ | Default | Beschreibung |
|----------|-----|---------|-------------|
| `KAMERPLANTER_MODE` | `Literal['light', 'full']` | `full` | Deployment-Modus |

### 5.2 Settings-Integration

```python
# src/backend/app/config/settings.py (Erweiterung)

class Settings(BaseSettings):
    # ... bestehende Settings ...

    # REQ-027 Deployment Mode
    kamerplanter_mode: Literal["light", "full"] = "full"
```

### 5.3 Docker Compose Beispiel

```yaml
# docker-compose.light.yml — Lokale Einzelnutzer-Instanz
services:
  backend:
    image: kamerplanter/backend:latest
    environment:
      KAMERPLANTER_MODE: light
      ARANGODB_HOST: arangodb
      # Kein JWT_SECRET_KEY nötig
      # Kein SMTP_* nötig
      # Kein OIDC_* nötig
    ports:
      - "8000:8000"

  frontend:
    image: kamerplanter/frontend:latest
    environment:
      VITE_KAMERPLANTER_MODE: light
    ports:
      - "5173:5173"

  arangodb:
    image: arangodb:3.11
    environment:
      ARANGO_ROOT_PASSWORD: rootpassword
    volumes:
      - arango-data:/var/lib/arangodb3
```

### 5.4 Frontend Environment-Variable

| Variable | Typ | Default | Beschreibung |
|----------|-----|---------|-------------|
| `VITE_KAMERPLANTER_MODE` | `'light' \| 'full'` | `'full'` | Steuert UI-Visibility |

```typescript
// src/frontend/src/config/mode.ts
export const KAMERPLANTER_MODE = (
  import.meta.env.VITE_KAMERPLANTER_MODE || 'full'
) as 'light' | 'full';

export const isLightMode = KAMERPLANTER_MODE === 'light';
```

## 6. Backend-Anpassungen

### 6.1 App-Start (Lifespan)

```python
# src/backend/app/main.py (Erweiterung)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.kamerplanter_mode == "light":
        seed_light_mode(get_db())   # System-User + System-Tenant
    yield
    close_connection()
```

### 6.2 Conditional Route Registration

Im Light-Modus werden Auth-spezifische Router nicht registriert:

```python
# src/backend/app/api/v1/router.py (Erweiterung)

if settings.kamerplanter_mode == "full":
    api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    api_router.include_router(oidc_router, prefix="/admin/oidc-providers", tags=["admin"])
    api_router.include_router(privacy_router, prefix="/privacy", tags=["privacy"])
```

Alle anderen Router (sites, plants, tasks, ...) werden in beiden Modi registriert.

### 6.3 Mode-Informations-Endpoint

```python
@router.get("/mode")
def get_deployment_mode() -> dict:
    """Gibt den aktuellen Deployment-Modus zurück.
    Wird vom Frontend beim Start abgefragt."""
    return {
        "mode": settings.kamerplanter_mode,
        "features": {
            "auth": settings.kamerplanter_mode == "full",
            "multi_tenant": settings.kamerplanter_mode == "full",
            "privacy_consent": settings.kamerplanter_mode == "full",
        }
    }
```

Route: `GET /api/v1/mode` — Kein Auth erforderlich (public).

## 7. Frontend-Anpassungen

### 7.1 Mode-Aware Routing

```typescript
// src/frontend/src/routes/AppRoutes.tsx (Erweiterung)

function AppRoutes() {
  if (isLightMode) {
    // Kein Login-Redirect, kein AuthGuard
    // System-Tenant-Slug wird als Default verwendet
    return (
      <Routes>
        <Route path="/" element={<Navigate to="/t/mein-garten/dashboard" />} />
        <Route path="/t/:slug/*" element={<TenantLayout />}>
          {/* Alle funktionalen Routen */}
        </Route>
        <Route path="/onboarding" element={<OnboardingWizard />} />
        {/* /login, /register sind nicht definiert → 404 */}
      </Routes>
    );
  }

  // Full-Modus: Bestehende Routing-Logik mit AuthGuard
  return ( /* ... bestehend ... */ );
}
```

### 7.2 Mode-Aware Sidebar

```typescript
// src/frontend/src/layouts/Sidebar.tsx (Erweiterung)

// Bestehende Navigation, aber im Light-Modus ohne:
// - Mitglieder-Link
// - Einladungen-Link
// - Tenant-Switcher

const navigationItems = useMemo(() => {
  const items = [ /* ... bestehende Items ... */ ];
  if (isLightMode) {
    return items.filter(item =>
      !['members', 'invitations', 'assignments'].includes(item.id)
    );
  }
  return items;
}, [isLightMode]);
```

### 7.3 Mode-Aware App-Bar

```typescript
// Im Light-Modus:
// - Kein Tenant-Switcher (nur ein Tenant)
// - Kein User-Avatar / Logout-Button
// - Kein Benachrichtigungs-Icon für Einladungen
// Stattdessen: Nur App-Titel + Sprach-Umschalter + Theme-Toggle
```

### 7.4 Mode-Aware AccountSettingsPage

```typescript
// Im Light-Modus zeigt AccountSettingsPage nur:
// - Tab "Allgemein" (Sprache, Zeitzone)
// - Tab "Erfahrungsstufe" (REQ-021)
// Ausgeblendet:
// - Tab "Sicherheit" (Passwort, Auth-Provider)
// - Tab "Sessions" (aktive Sitzungen)
// - Tab "Datenschutz" (DSGVO)
```

### 7.5 Mode-Aware Onboarding

```typescript
// Im Light-Modus:
// - OnboardingWizard startet direkt (kein Login-Redirect)
// - Schritt "Account erstellen" wird übersprungen
// - Onboarding-State wird dem System-User zugeordnet
```

### 7.6 API-Client ohne Auth-Header

```typescript
// src/frontend/src/api/client.ts (Erweiterung)

const apiClient = axios.create({ baseURL: '/api/v1' });

apiClient.interceptors.request.use((config) => {
  if (!isLightMode) {
    const token = store.getState().auth.accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  // Im Light-Modus: Kein Authorization-Header → LightAuthProvider auf Backend
  return config;
});
```

### 7.7 Redux Store im Light-Modus

```typescript
// Im Light-Modus:
// - authSlice wird nicht initialisiert (kein Token-Management)
// - tenantSlice wird mit System-Tenant vorbelegt:
//   activeTenant: { slug: "mein-garten", role: "admin", type: "personal" }
// - Kein Token-Refresh-Interceptor
```

## 8. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Bei `KAMERPLANTER_MODE=light` startet die App ohne Login-Screen | E2E |
| AK-02 | System-User und System-Tenant werden beim ersten Start automatisch erzeugt | Integration |
| AK-03 | Seed-Logik ist idempotent — mehrfacher App-Start erzeugt keine Duplikate | Unit |
| AK-04 | API-Requests ohne Authorization-Header geben im Light-Modus gültige Responses | Integration |
| AK-05 | API-Requests ohne Authorization-Header geben im Full-Modus 401 Unauthorized | Integration |
| AK-06 | Onboarding-Wizard startet im Light-Modus direkt ohne Login-Schritt | E2E |
| AK-07 | Pflanzen können im Light-Modus vollständig angelegt, bearbeitet und gelöscht werden | E2E |
| AK-08 | Pflegeerinnerungen (REQ-022) funktionieren im Light-Modus uneingeschränkt | Integration |
| AK-09 | Alle Ressourcen werden dem System-Tenant zugeordnet (`tenant_key: "system-tenant"`) | Integration |
| AK-10 | `GET /api/v1/mode` gibt den korrekten Modus und Feature-Flags zurück | Unit |

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | Login-Screen, Registrierung und Passwort-vergessen sind im Light-Modus nicht erreichbar | E2E |
| FK-02 | Tenant-Switcher ist im Light-Modus nicht sichtbar | E2E |
| FK-03 | Mitglieder- und Einladungen-Menüpunkte sind im Light-Modus nicht sichtbar | E2E |
| FK-04 | AccountSettingsPage zeigt im Light-Modus nur Sprache + Erfahrungsstufe | E2E |
| FK-05 | DSGVO-Consent-Banner erscheint im Light-Modus nicht | E2E |
| FK-06 | Alle funktionalen Seiten (Pflanzen, Standorte, Düngung, IPM, Ernten) sind im Light-Modus vollständig nutzbar | E2E |
| FK-07 | `VITE_KAMERPLANTER_MODE` steuert die UI-Visibility korrekt | Unit |

### Nicht-funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| NK-01 | Wechsel von `light` auf `full` erfordert nur das Ändern einer Environment-Variable + Neustart | Manuell |
| NK-02 | Bestehende Daten im System-Tenant bleiben bei Moduswechsel erhalten | Integration |
| NK-03 | Kein Code-Duplikat — Light-Modus nutzt denselben Code wie Full-Modus (nur Auth-Layer ist ausgetauscht) | Code-Review |

## 9. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| **REQ-023** | Auth-Architektur — `get_current_user`-Dependency wird durch Adapter-Pattern erweitert |
| **REQ-024** | Tenant-Architektur — System-Tenant nutzt das bestehende Tenant-Modell |
| **REQ-025** | DSGVO — Im Light-Modus deaktiviert (keine personenbezogenen Daten) |
| REQ-020 | Onboarding-Wizard — Startet im Light-Modus ohne Login-Schritt |
| REQ-021 | Erfahrungsstufen — Funktioniert unverändert (User-Preference am System-User) |
| NFR-001 | 5-Layer-Architektur — Auth-Adapter auf Domain-Interfaces-Ebene |

### Auswirkung auf bestehende Implementierung:

| Bereich | Änderung | Umfang |
|---------|---------|--------|
| `settings.py` | Neues Feld `kamerplanter_mode` | 1 Zeile |
| `auth.py` | `get_current_user` delegiert an `IAuthProvider` | ~15 Zeilen |
| `main.py` | Conditional `seed_light_mode()` bei App-Start | ~5 Zeilen |
| `router.py` | Conditional Router-Registration für Auth-Endpunkte | ~5 Zeilen |
| `Sidebar.tsx` | Navigation-Filter für Light-Modus | ~5 Zeilen |
| `AppRoutes.tsx` | Conditional Routing ohne AuthGuard | ~15 Zeilen |
| `api/client.ts` | Conditional Authorization-Header | ~3 Zeilen |
| Neue Dateien | `IAuthProvider` (ABC), `LightAuthProvider`, `FullAuthProvider`, `seed_light_mode`, `mode.ts` | ~100 Zeilen |

**Gesamtaufwand:** ~150 Zeilen neue/geänderte Code-Zeilen. Keine Datenbankschema-Änderungen. Keine neuen Collections.

## 10. Scope-Abgrenzung

**In Scope:**
- Environment-Variable `KAMERPLANTER_MODE` (light | full)
- System-User + System-Tenant bei erstem Start (idempotent)
- Auth-Adapter-Pattern (`IAuthProvider` → `FullAuthProvider` / `LightAuthProvider`)
- Feature-Visibility im Frontend (ausblenden von Auth/Tenant/DSGVO-UI)
- Mode-Informations-Endpoint (`GET /api/v1/mode`)
- Docker Compose Beispiel für Light-Modus

**Nicht in Scope (bewusst ausgeklammert):**
- **Nutzer-Umschaltung im Light-Modus** — Es gibt nur einen System-User. Für Multi-User: Full-Modus nutzen.
- **Granulares Feature-Toggling** — Kein "Light-Modus mit Auth aber ohne Tenants". Die Modi sind atomar: alles oder nichts.
- **Runtime-Umschaltung** — Moduswechsel erfordert Neustart. Kein Hot-Switching.
- **Migration von System-User-Daten** — Beim Upgrade auf Full-Modus bleiben Daten im System-Tenant. Automatische Übernahme in einen neuen User-Account ist eine zukünftige Erweiterung.
- **Reverse-Proxy-Auth** — Integration mit externem Auth (Authelia, Authentik Proxy) ist ein eigenes Thema.
- **Light-Modus mit mehreren Tenants** — Im Light-Modus existiert nur ein Tenant.

## 11. Sicherheitshinweis

Der Light-Modus ist **ausdrücklich nicht für öffentlich erreichbare Instanzen** gedacht. Ohne Authentifizierung hat jeder im Netzwerk vollen Lese- und Schreibzugriff.

**Empfohlene Einsatzszenarien:**
- `localhost` (einzelner Rechner)
- Geschlossenes Heimnetzwerk (hinter Router-Firewall)
- Docker auf einem Raspberry Pi ohne Port-Forwarding
- VPN-geschütztes Netzwerk

**Warnhinweis im Frontend:**
Wenn der Light-Modus aktiv ist und die App nicht über `localhost` oder eine private IP (10.x, 172.16–31.x, 192.168.x) aufgerufen wird, wird ein nicht-blockierender Hinweis angezeigt:

> "Kamerplanter läuft im Light-Modus ohne Authentifizierung. Dieser Modus ist nur für geschlossene Netzwerke gedacht."
