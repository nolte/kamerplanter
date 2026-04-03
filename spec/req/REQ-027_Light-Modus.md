# Spezifikation: REQ-027 - Light-Modus (Anonymer Zugang)

```yaml
ID: REQ-027
Titel: Light-Modus (Anonymer Zugang)
Kategorie: Plattform & Deployment
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI
Status: Entwurf
Version: 1.2 (Bidirektionaler Moduswechsel Light↔Full)
Abhängigkeit: REQ-023 v1.6, REQ-024 v1.3, REQ-025
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.2 | 2026-03-16 | **Bidirektionaler Moduswechsel:** Upgrade Light→Full (System-Tenant-Übernahme durch ersten registrierten User, Platform-Admin-Transfer), Downgrade Full→Light (Datenverlust akzeptabel, System-User/Tenant-Reaktivierung, Multi-Tenant-Daten verwaist). Neue Szenarien 5–8, Upgrade-/Downgrade-API, Abnahmekriterien. |
| 1.1 | 2026-03-16 | **Platform-Tenant im Light-Modus:** System-User erhält automatisch admin-Membership im Platform-Tenant. Alle globalen Stammdaten (Species, Pests, Diseases, Treatments, Fertilizers, NutrientPlans) werden via `tenant_has_access`-Kanten dem System-Tenant zugewiesen. Seed-Logik erweitert um Platform-Tenant-Erstellung und Auto-Assign. |
| 1.0 | 2026-02-27 | Erstversion — Light-Modus als Deployment-Option für lokale Instanzen |

## 1. Business Case

**User Story (Einzelnutzer ohne Login):** "Als Zimmerpflanzen-Besitzer mit 5 Pflanzen auf einem Raspberry Pi möchte ich die App einfach im Browser öffnen und sofort meine Pflanzen verwalten können — ohne mich registrieren, anmelden oder ein Passwort merken zu müssen."

**User Story (Heimnetzwerk):** "Als Hobby-Gärtner mit einem Home-Server möchte ich Kamerplanter im lokalen Netzwerk betreiben und von Laptop, Tablet und Handy darauf zugreifen — ohne dass jedes Gerät ein eigenes Login braucht."

**User Story (Schnelleinstieg):** "Als Erstnutzer möchte ich die App ausprobieren können, ohne vorher eine E-Mail-Adresse angeben zu müssen — damit ich sofort sehe, ob die App zu meinen Bedürfnissen passt."

**User Story (Kein Overhead):** "Als Einzelnutzer auf meinem eigenen Rechner will ich nichts von Tenants, Mitgliederverwaltung, DSGVO-Consent-Bannern oder Einladungssystemen sehen — weil diese Konzepte für mich als einzigen Nutzer irrelevant sind."

**User Story (Onboarding ohne Login):** "Als neuer Nutzer im Light-Modus möchte ich den Onboarding-Wizard (REQ-020) direkt beim ersten Start durchlaufen können — ohne vorher einen Account anlegen zu müssen."

**Beschreibung:**

Zwei Findings aus dem Casual-Houseplant-User-Review ([spec/analysis/casual-houseplant-user-review.md](../requirements-analysis/casual-houseplant-user-review.md)) motivieren diese Anforderung:

- **N-002 (Registrierung als Pflicht vor dem ersten Nutzen):** Bevor ein Casual User irgendetwas tun kann, muss er sich registrieren, E-Mail verifizieren und einen Tenant erstellen — das ist ein Dealbreaker für jemanden mit 3 Zimmerpflanzen auf der Fensterbank.
- **F-003 (Mandantenverwaltung und DSGVO-Formulare):** Concepts wie "Tenants", "Mitgliederverwaltung", "Consent-Banner" und "Datenschutz-Einstellungen" sind Overhead für Einzelnutzer auf lokalen Instanzen.

Der Light-Modus ist ein **Deployment-Modus** für geschlossene Netzwerke und lokale Instanzen (Raspberry Pi, Home-Server, einzelner PC, Docker Compose auf dem Laptop). Er deaktiviert Auth, Tenants und DSGVO-Consent auf Konfigurationsebene — die App funktioniert sofort nach dem Öffnen.

<!-- Quelle: Widerspruchsanalyse W-002 -->
**Rechtliche Abgrenzung — DSGVO-Haushaltsausnahme (Art. 2 Abs. 2 lit. c):**

Der Light-Modus stützt sich auf die **Haushaltsausnahme** der DSGVO: Die Verordnung findet keine Anwendung auf die Verarbeitung personenbezogener Daten durch natürliche Personen zur Ausübung ausschließlich persönlicher oder familiärer Tätigkeiten. Der Light-Modus ist daher **ausschließlich für private Deployments** vorgesehen:
- `localhost` / einzelner Rechner
- Geschlossenes Heimnetzwerk (hinter Router-Firewall)
- Raspberry Pi ohne Port-Forwarding
- VPN-geschütztes LAN

**Wenn der Light-Modus außerhalb der Haushaltsausnahme betrieben wird** (öffentlich erreichbar, gewerblicher Einsatz, Cloud-Hosting), MUSS der Betreiber auf den Full-Modus wechseln. Das System kann dies nicht automatisch erzwingen, aber die Deployment-Dokumentation MUSS diesen Sachverhalt prominent darstellen.

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

<!-- Quelle: Bidirektionaler Moduswechsel v1.2 -->
**Szenario 5: Upgrade von Light auf Full — System-Tenant-Übernahme**
```
Voraussetzung: Nutzer hat im Light-Modus 30 Pflanzen, 3 Standorte, 5 Nährstoffpläne angelegt

1. Nutzer möchte Kamerplanter mit Freund teilen
2. Ändert KAMERPLANTER_MODE=full, startet neu
3. Backend erkennt: Moduswechsel (vorher light, jetzt full)
   → System-User (system@local) wird auf status: "inactive" gesetzt
   → Platform-Tenant und System-Tenant bleiben bestehen
4. Beim nächsten Aufruf: Login-Screen erscheint
5. Nutzer registriert sich (REQ-023) → persönlicher Tenant wird NICHT erstellt
6. Stattdessen: System erkennt System-Tenant mit Daten
   → Übernahme-Dialog: "Es gibt bestehende Daten (30 Pflanzen, 3 Standorte).
      Möchten Sie diese in Ihr Konto übernehmen?"
7. Nutzer bestätigt → System-Tenant wird in-place übernommen:
   a) system-tenant.name → "{display_name}s Garten"
   b) system-tenant.type bleibt "personal"
   c) Neue Membership: registrierter User → system-tenant (role: admin)
   d) System-User-Membership wird auf status: "left" gesetzt
   e) Neuer User erhält admin-Membership im Platform-Tenant (= erster KA-Admin)
8. Alle 30 Pflanzen, Standorte, Nährstoffpläne etc. gehören jetzt dem neuen User
9. Neuer User kann jetzt weitere Mitglieder einladen (REQ-024)
```

**Szenario 6: Upgrade Light→Full — Übernahme ablehnen**
```
Voraussetzung: Wie Szenario 5

1-5. Wie Szenario 5
6. Nutzer lehnt Übernahme ab: "Nein, neu starten"
7. System erstellt persönlichen Tenant für den neuen User (Standard REQ-024)
8. System-Tenant bleibt mit status: "active" bestehen (verwaist)
   → Nur über KA-Admin-Panel einsehbar/löschbar
9. Neuer User erhält admin-Membership im Platform-Tenant (= KA-Admin)
10. KA-Admin kann System-Tenant später über Admin-Panel löschen oder
    einem anderen User zuweisen
```

**Szenario 7: Downgrade von Full auf Light**
```
Voraussetzung: Full-Modus mit 3 Usern, 2 Tenants, 50 Pflanzen verteilt

1. Admin ändert KAMERPLANTER_MODE=light, startet neu
2. Backend erkennt: Moduswechsel (vorher full, jetzt light)
3. System prüft: System-User vorhanden?
   a) Ja → System-User wird auf status: "active" gesetzt
   b) Nein → System-User + System-Tenant werden neu erstellt (Seed-Logik)
4. System prüft: System-Tenant vorhanden?
   a) Ja → System-Tenant wird reaktiviert (status: "active")
   b) Nein → System-Tenant wird neu erstellt
5. System-User erhält admin-Membership in System-Tenant + Platform-Tenant
6. Auto-Assign: Alle globalen Stammdaten → System-Tenant
7. Frontend: Kein Login-Screen, arbeitet als System-User im System-Tenant

WICHTIG — Datenverlust:
- Alle anderen Tenants und deren Daten bleiben in der DB, sind aber im
  Light-Modus nicht erreichbar (nur System-Tenant ist operativ)
- User-Accounts, Memberships, Einladungen sind nicht sichtbar
- Bei erneutem Upgrade auf Full sind die Daten wieder zugänglich
```

**Szenario 8: Roundtrip Light → Full → Light**
```
Phase 1 — Light:
  System-User hat 10 Pflanzen im System-Tenant

Phase 2 — Upgrade auf Full:
  Nutzer registriert sich als "Anna", übernimmt System-Tenant
  Anna hat jetzt 10 Pflanzen, lädt Freund "Max" ein
  Max erstellt eigenen Tenant mit 5 Pflanzen
  Anna erstellt 20 weitere Pflanzen → insgesamt 30

Phase 3 — Downgrade auf Light:
  System-User wird reaktiviert, System-Tenant wird reaktiviert
  System-User sieht die 30 Pflanzen im System-Tenant (Annas Daten)
  Max' separater Tenant (5 Pflanzen) ist nicht sichtbar, aber in DB erhalten
  Anna und Max können sich nicht anmelden (Auth deaktiviert)

Phase 4 — Erneuter Upgrade auf Full:
  Anna meldet sich an → System-Tenant-Übernahme-Dialog erscheint erneut
  Anna übernimmt → hat wieder 30 Pflanzen
  Max meldet sich an → sein Tenant mit 5 Pflanzen ist wieder da
```
<!-- /Quelle: Bidirektionaler Moduswechsel v1.2 -->

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
| **Externe Anreicherung** | Deaktiviert (Standard) — aktivierbar per `ENABLE_ENRICHMENT_LIGHTMODE=true` | Vollständig (mit Consent) |

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

<!-- Quelle: Platform-Tenant & Auto-Assign v1.1 -->
### 3.4 Platform-Tenant-Membership im Light-Modus

Im Light-Modus erhält der System-User automatisch eine admin-Membership im Platform-Tenant (REQ-024 v1.3). Damit ist der System-User gleichzeitig:
- **KA-Admin** (via Platform-Tenant-Membership) → kann globale Stammdaten verwalten
- **Tenant-Admin** (via System-Tenant-Membership) → kann Pflanzen, Standorte etc. verwalten

```python
SYSTEM_PLATFORM_MEMBERSHIP = Membership(
    role="admin",
    joined_at=datetime.now(UTC),
    status="active",
)
# Edge: has_membership: system-user → system-platform-membership
# Edge: membership_in: system-platform-membership → platform-tenant
```

### 3.5 Seed-Logik (Idempotent, erweitert)

```python
def seed_light_mode(db: StandardDatabase) -> None:
    """Erzeugt System-User + System-Tenant + Platform-Tenant + Auto-Assign.
    Idempotent — kann bei jedem Start aufgerufen werden."""
    users = db.collection("users")

    # 1. System-User erstellen
    if not users.has("system-user"):
        users.insert({**SYSTEM_USER.dict(), "_key": "system-user"})

    # 2. System-Tenant erstellen
    tenants = db.collection("tenants")
    if not tenants.has("system-tenant"):
        tenants.insert({**SYSTEM_TENANT.dict(), "_key": "system-tenant"})
        # Membership: system-user → system-tenant (admin)
        _create_membership(db, "system-user", "system-tenant", "admin")

    # 3. Platform-Tenant erstellen (REQ-024 v1.3)
    if not tenants.has("platform"):
        tenants.insert({**PLATFORM_TENANT.dict(), "_key": "platform"})
        # Membership: system-user → platform (admin) → macht System-User zum KA-Admin
        _create_membership(db, "system-user", "platform", "admin")

    # 4. Auto-Assign: Alle globalen Stammdaten → System-Tenant
    auto_assign_all_master_data("system-tenant", db)
```

**Schritt 4 (Auto-Assign)** erstellt `tenant_has_access`-Kanten für alle globalen Species, Pests, Diseases, Treatments, Fertilizers und NutrientPlans zum System-Tenant. Damit sieht der Light-Modus-Nutzer alle verfügbaren Stammdaten ohne manuelle Zuweisung.
<!-- /Quelle: Platform-Tenant & Auto-Assign v1.1 -->

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

<!-- Quelle: Bidirektionaler Moduswechsel v1.2 -->
## 7a. Moduswechsel-Mechanik

### 7a.1 Modus-Erkennung beim Start

Das Backend erkennt einen Moduswechsel durch Vergleich des gespeicherten Modus mit dem aktuellen:

```python
# src/backend/app/config/settings.py
class Settings(BaseSettings):
    kamerplanter_mode: Literal["light", "full"] = "full"

# Beim App-Start (lifespan):
def detect_mode_change(db: StandardDatabase, current_mode: str) -> str | None:
    """Erkennt Moduswechsel. Gibt vorherigen Modus zurück, oder None."""
    meta = db.collection("system_meta")
    prev = meta.get("deployment_mode")
    if prev is None:
        # Erster Start — kein Wechsel
        meta.insert({"_key": "deployment_mode", "mode": current_mode})
        return None
    if prev["mode"] != current_mode:
        old_mode = prev["mode"]
        meta.update({"_key": "deployment_mode", "mode": current_mode})
        return old_mode
    return None
```

**Neue Collection:** `system_meta` (Doc Collection, max. wenige Dokumente) — speichert systemweite Metadaten wie den zuletzt aktiven Deployment-Modus.

### 7a.2 Upgrade: Light → Full

Wird ausgeführt wenn `detect_mode_change()` den Wechsel `light → full` erkennt:

```python
def handle_upgrade_light_to_full(db: StandardDatabase) -> None:
    """Bereitet System für Full-Modus vor nach Light-Modus-Betrieb."""
    users = db.collection("users")

    # 1. System-User deaktivieren (kein Login im Full-Modus möglich)
    if users.has("system-user"):
        users.update({"_key": "system-user", "status": "inactive"})

    # 2. Platform-Tenant bleibt aktiv (wird vom ersten Admin übernommen)
    # 3. System-Tenant bleibt aktiv (wird vom ersten registrierten User übernommen)

    # 4. Setze Flag für Frontend: Übernahme-Dialog anzeigen
    meta = db.collection("system_meta")
    meta.insert_or_replace({
        "_key": "pending_takeover",
        "system_tenant_key": "system-tenant",
        "created_at": datetime.now(UTC).isoformat(),
    })
```

**Übernahme-Endpoint (nach Registrierung):**

```python
@router.post("/system/takeover")
def takeover_system_tenant(
    accept: bool,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> dict:
    """Übernimmt oder verwirft den System-Tenant nach Upgrade.
    Nur aufrufbar wenn pending_takeover existiert."""

    if accept:
        # System-Tenant in-place übernehmen
        tenant_service.takeover_system_tenant(
            user=current_user,
            new_name=f"{current_user.display_name}s Garten",
        )
        # → Membership: current_user → system-tenant (admin)
        # → System-User-Membership: status → "left"
        # → Platform-Tenant: current_user → admin (= KA-Admin)
    else:
        # Standard: Persönlichen Tenant erstellen (REQ-024)
        tenant_service.create_personal_tenant(current_user)
        # → Platform-Tenant: current_user → admin (= KA-Admin)

    # Flag entfernen
    db.collection("system_meta").delete("pending_takeover")
    return {"takeover": accept, "tenant_slug": "mein-garten" if accept else ...}
```

**Route:** `POST /api/v1/system/takeover` — Erfordert Auth (Full-Modus), nur aufrufbar wenn `pending_takeover` in `system_meta` existiert.

**Frontend-Flow:**

```typescript
// Nach erfolgreicher Registrierung im Full-Modus:
// 1. Frontend prüft: GET /api/v1/system/takeover-status
// 2. Wenn pending_takeover vorhanden → Übernahme-Dialog anzeigen:
//    "Es gibt bestehende Daten (X Pflanzen, Y Standorte).
//     Möchten Sie diese in Ihr Konto übernehmen?"
//    [Ja, übernehmen] [Nein, neu starten]
// 3. POST /api/v1/system/takeover mit accept: true/false
// 4. Redirect zum Dashboard
```

### 7a.3 Downgrade: Full → Light

Wird ausgeführt wenn `detect_mode_change()` den Wechsel `full → light` erkennt:

```python
def handle_downgrade_full_to_light(db: StandardDatabase) -> None:
    """Bereitet System für Light-Modus vor nach Full-Modus-Betrieb.
    Datenverlust für Nicht-System-Tenant-Daten ist akzeptabel."""
    users = db.collection("users")
    tenants = db.collection("tenants")
    memberships = db.collection("memberships")

    # 1. System-User reaktivieren oder neu erstellen
    if users.has("system-user"):
        users.update({"_key": "system-user", "status": "active"})
    else:
        users.insert({**SYSTEM_USER.dict(), "_key": "system-user"})

    # 2. System-Tenant reaktivieren oder neu erstellen
    if tenants.has("system-tenant"):
        tenants.update({"_key": "system-tenant", "status": "active"})
    else:
        tenants.insert({**SYSTEM_TENANT.dict(), "_key": "system-tenant"})

    # 3. Platform-Tenant reaktivieren oder neu erstellen
    if tenants.has("platform"):
        tenants.update({"_key": "platform", "status": "active"})
    else:
        tenants.insert({**PLATFORM_TENANT.dict(), "_key": "platform"})

    # 4. System-User Memberships sicherstellen
    _ensure_membership(db, "system-user", "system-tenant", "admin")
    _ensure_membership(db, "system-user", "platform", "admin")

    # 5. Auto-Assign: Alle globalen Stammdaten → System-Tenant
    auto_assign_all_master_data("system-tenant", db)

    # 6. Aufräumen: pending_takeover entfernen falls vorhanden
    meta = db.collection("system_meta")
    if meta.has("pending_takeover"):
        meta.delete("pending_takeover")
```

**Verhalten anderer Tenants beim Downgrade:**

| Ressource | Verhalten | Begründung |
|-----------|----------|------------|
| Andere Tenants (personal, organization) | Bleiben in DB, nicht erreichbar | Kein Datenverlust, wiederherstellbar bei erneutem Upgrade |
| User-Accounts (außer System-User) | Bleiben in DB, nicht nutzbar | Auth ist deaktiviert im Light-Modus |
| Memberships anderer User | Bleiben in DB, inaktiv | Werden bei Upgrade reaktiviert |
| System-Tenant-Daten | Vollständig nutzbar | Gehören dem System-User |
| Daten anderer Tenants | In DB erhalten, nicht sichtbar | Light-Modus operiert nur auf System-Tenant |
| tenant_has_access-Kanten | Bleiben erhalten | Werden bei Upgrade wieder relevant |
| Overlay-Daten (tenant_*_config) | Bleiben erhalten | System-Tenant-Overlays sind nutzbar |

**Wichtig:** Es werden **keine Daten gelöscht**. Alle Tenants, Users, Memberships und Ressourcen bleiben in der Datenbank. Der Light-Modus kann sie nur nicht anzeigen, weil er ausschließlich mit dem System-User und System-Tenant arbeitet. Bei erneutem Upgrade auf Full sind alle Daten wieder zugänglich.

**Tatsächlicher Datenverlust tritt nur ein wenn:**
- Der System-Tenant im Full-Modus von einem User übernommen wurde (Szenario 5), dann beim Downgrade der System-User diesen Tenant mit den Daten des vorherigen Users sieht — aber keine Daten verloren gehen
- Ein User im Full-Modus Daten im System-Tenant ändert und dann downgraded — der System-User sieht die geänderten Daten

### 7a.4 Modus-Tracking Endpoint

```python
@router.get("/system/takeover-status")
def get_takeover_status() -> dict:
    """Gibt den Übernahme-Status zurück.
    Nur relevant nach Upgrade Light→Full."""
    meta = db.collection("system_meta")
    pending = meta.get("pending_takeover")
    if pending is None:
        return {"pending": False}

    # Zähle Ressourcen im System-Tenant
    stats = _count_system_tenant_resources(db)
    return {
        "pending": True,
        "system_tenant_key": pending["system_tenant_key"],
        "resource_counts": stats,  # {"plants": 30, "sites": 3, ...}
    }
```

**Route:** `GET /api/v1/system/takeover-status` — Im Full-Modus: Auth erforderlich. Im Light-Modus: nicht relevant (404).
<!-- /Quelle: Bidirektionaler Moduswechsel v1.2 -->

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
<!-- Quelle: Platform-Tenant & Auto-Assign v1.1 -->
| AK-11 | Platform-Tenant wird beim Light-Modus-Start automatisch erstellt (idempotent) | Integration |
| AK-12 | System-User hat admin-Membership im Platform-Tenant (= KA-Admin) | Integration |
| AK-13 | Alle globalen Stammdaten (Species, Pests, Diseases, Treatments, Fertilizers, NutrientPlans) haben `tenant_has_access`-Kanten zum System-Tenant | Integration |
| AK-14 | Light-Modus-Nutzer sieht alle verfügbaren Stammdaten ohne manuelle Zuweisung | E2E |
<!-- /Quelle: Platform-Tenant & Auto-Assign v1.1 -->
<!-- Quelle: Bidirektionaler Moduswechsel v1.2 -->
| AK-15 | Moduswechsel wird erkannt: `system_meta.deployment_mode` wird beim Start verglichen und aktualisiert | Integration |
| AK-16 | **Upgrade Light→Full:** System-User wird auf `status: inactive` gesetzt | Integration |
| AK-17 | **Upgrade Light→Full:** `pending_takeover` wird in `system_meta` gesetzt | Integration |
| AK-18 | **Upgrade Light→Full:** Erster registrierter User kann System-Tenant übernehmen (`POST /system/takeover`, accept=true) | Integration |
| AK-19 | **Upgrade Light→Full:** Bei Übernahme erhält User admin-Membership in System-Tenant + Platform-Tenant | Integration |
| AK-20 | **Upgrade Light→Full:** Bei Ablehnung wird persönlicher Tenant erstellt, System-Tenant bleibt verwaist | Integration |
| AK-21 | **Upgrade Light→Full:** `pending_takeover` wird nach Übernahme/Ablehnung entfernt | Integration |
| AK-22 | **Downgrade Full→Light:** System-User wird reaktiviert oder neu erstellt | Integration |
| AK-23 | **Downgrade Full→Light:** System-Tenant wird reaktiviert oder neu erstellt | Integration |
| AK-24 | **Downgrade Full→Light:** Auto-Assign aller Stammdaten zum System-Tenant wird ausgeführt | Integration |
| AK-25 | **Downgrade Full→Light:** Andere Tenants/Users bleiben in DB erhalten (kein Löschen) | Integration |
| AK-26 | **Downgrade Full→Light:** App arbeitet sofort als System-User im System-Tenant | E2E |
| AK-27 | **Roundtrip:** Light→Full→Light→Full: Alle Daten bleiben erhalten und sind nach erneutem Upgrade zugänglich | Integration |
| AK-28 | `GET /api/v1/system/takeover-status` gibt korrekte Ressourcen-Zählung zurück | Integration |
<!-- /Quelle: Bidirektionaler Moduswechsel v1.2 -->

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
| **REQ-023 v1.6** | Auth-Architektur — `get_current_user`-Dependency wird durch Adapter-Pattern erweitert. Platform-Admin-Rolle für System-User. |
| **REQ-024 v1.3** | Tenant-Architektur — System-Tenant + Platform-Tenant nutzen das bestehende Modell. `tenant_has_access`-Kanten für Auto-Assign. |
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
- **Reverse-Proxy-Auth** — Integration mit externem Auth (Authelia, Authentik Proxy) ist ein eigenes Thema.
- **Light-Modus mit mehreren Tenants** — Im Light-Modus existiert nur ein operativer Tenant (System-Tenant). Der Platform-Tenant dient ausschließlich der KA-Admin-Berechtigung.
- **Automatische Daten-Migration bei Downgrade** — Beim Downgrade Full→Light werden keine Daten aus anderen Tenants in den System-Tenant kopiert. Die Daten bleiben in der DB und sind beim nächsten Upgrade wieder zugänglich.
- **Selektive Tenant-Übernahme** — Beim Upgrade kann nur der System-Tenant übernommen werden. Andere verwaiste Tenants müssen über das KA-Admin-Panel verwaltet werden.

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
