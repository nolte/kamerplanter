# Spezifikation: REQ-023 - Benutzerverwaltung & Authentifizierung

```yaml
ID: REQ-023
Titel: Benutzerverwaltung & Authentifizierung
Kategorie: Plattform & Sicherheit
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Authlib, React, TypeScript, MUI
Status: Entwurf
Version: 1.2 (Security-Review)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.2 | 2026-02-27 | SEC-K-002: IP-Anonymisierung nach 7 Tagen, `ip_anonymized_at` Feld. SEC-K-004: CSRF-Strategie — `SameSite=Lax` (statt Strict) + Double-Submit Cookie für zustandsändernde Cookie-Endpunkte. |
| 1.1 | 2026-02-25 | Tech-Stack-Review: Authlib statt python-jose, Token-TTL-Anpassungen |
| 1.0 | 2026-02-24 | Erstversion |

## 1. Business Case

**User Story (Lokale Registrierung):** "Als Einzelgärtner möchte ich mich mit E-Mail und Passwort registrieren können, ohne einen externen Anbieter wie Google nutzen zu müssen — weil ich meine Pflanzendaten privat halten möchte und keinen Social-Login verwenden will."

**User Story (SSO-Anmeldung):** "Als Hobby-Gärtner möchte ich mich mit meinem bestehenden Google-Konto anmelden können — damit ich kein weiteres Passwort verwalten muss und sofort loslegen kann."

**User Story (Account-Verknüpfung):** "Als Nutzer, der sich initial mit Google angemeldet hat, möchte ich nachträglich ein lokales Passwort setzen können — damit ich auch ohne Google-Verfügbarkeit auf meine Pflanzen zugreifen kann."

**User Story (Profilpflege):** "Als registrierter Nutzer möchte ich meinen Anzeigenamen, mein Profilbild und meine Sprach-/Zeitzoneneinstellungen verwalten können — damit andere Gartenmitglieder mich erkennen und das System in meiner Zeitzone arbeitet."

**User Story (Passwort-Reset):** "Als Nutzer, der sein Passwort vergessen hat, möchte ich über meine E-Mail-Adresse ein neues Passwort setzen können — ohne den Support kontaktieren zu müssen."

**User Story (OIDC-Anbindung):** "Als Systemadministrator möchte ich einen eigenen OpenID-Connect-Provider (z.B. Keycloak, Authentik) konfigurieren können — damit unser Gemeinschaftsgarten den zentralen Identity Provider der Organisation nutzen kann."

**Beschreibung:**
Kamerplanter ist aktuell ein Einbenutzer-System ohne Authentifizierung. Für Mehrbenutzerbetrieb (Gemeinschaftsgärten, Mikro-Farmen, Anbauvereinigungen) ist eine vollständige Benutzerverwaltung die **Grundvoraussetzung**. Diese REQ **ersetzt NFR-001 §6.1** (JWT-Skizze mit `python-jose`, 1h Access Token) durch eine vollständige Spezifikation und bildet die Basis für REQ-024 (Mandantenverwaltung).

**Technologie-Entscheidung (JWT/OAuth-Library):**
Diese Spezifikation verwendet **Authlib** (aktiv maintained) anstelle von `python-jose` (letztes Release 2022, in NFR-001 §6.1 referenziert). Authlib bietet:
- JWT-Signierung/-Validierung (ersetzt `python-jose`)
- OAuth2/OIDC Client mit PKCE-Support (ersetzt manuelle `httpx`-Implementierung)
- OIDC Discovery (`.well-known/openid-configuration`) built-in
- Flask/FastAPI-Integration

**Abweichungen von NFR-001 §6.1:**
| Aspekt | NFR-001 §6.1 (alt) | REQ-023 (neu) | Begründung |
|--------|--------------------|--------------|-----------|
| Library | `python-jose` + `passlib` | `authlib` + `passlib` | `python-jose` unmaintained seit 2022; Authlib bietet OIDC/PKCE built-in |
| Access Token TTL | 1 Stunde | **15 Minuten** | Kürzeres Fenster bei Token-Kompromittierung; Refresh-Token-Mechanismus kompensiert UX |
| Refresh Token | Nicht spezifiziert | 30 Tage, HttpOnly Cookie, Rotation | Erforderlich für 15-Min-Access-Tokens ohne ständige Neuanmeldung |
| Token Payload | `sub`, `exp`, `type` | `sub`, `email`, `display_name`, `tenant_roles`, `exp`, `iat`, `type` | Mandanten-Rollen für REQ-024 im Token; reduziert DB-Lookups |

**Kernkonzepte:**

**Dual-Authentifizierung — Lokal + Föderiert:**
Das System unterstützt zwei gleichberechtigte Authentifizierungspfade:
1. **Lokale Accounts** — E-Mail + Passwort (Bcrypt-gehasht), vollständig self-contained
2. **Föderierte Accounts** — OAuth2/OIDC mit benannten Providern (Google, GitHub, Apple) und beliebig vielen generischen OIDC-Providern

Ein User kann mehrere Auth-Methoden verknüpfen (z.B. Google + lokales Passwort). Die erste erfolgreiche Anmeldung erstellt den User-Account; weitere Provider werden verknüpft.

**Benannte SSO-Provider:**

| Provider | Protokoll | Scope | Besonderheit |
|----------|-----------|-------|-------------|
| Google | OAuth2 + OIDC | `openid email profile` | Größte Verbreitung, E-Mail immer verifiziert |
| GitHub | OAuth2 | `read:user user:email` | Technische Nutzer, E-Mail ggf. privat → separater API-Call |
| Apple | OAuth2 + OIDC | `name email` | Name nur beim ersten Login übermittelt, muss gespeichert werden |

**Generischer OIDC-Provider:**
Zusätzlich können beliebig viele OIDC-Provider über Konfiguration registriert werden (z.B. Keycloak, Authentik, Azure AD, Okta). Die Konfiguration erfolgt per Provider-Eintrag:

```yaml
# Konfigurationsbeispiel: Generischer OIDC-Provider
oidc_providers:
  - slug: "keycloak-gemeinschaftsgarten"
    display_name: "Gemeinschaftsgarten Berlin"
    issuer_url: "https://auth.garden-berlin.org/realms/garten"
    client_id: "kamerplanter"
    client_secret: "${KEYCLOAK_SECRET}"
    scopes: ["openid", "email", "profile"]
    icon_url: "https://auth.garden-berlin.org/logo.png"  # Optional
    auto_discover: true  # .well-known/openid-configuration
```

**JWT-Token-Lifecycle:**

| Token | Lebensdauer | Speicherort | Refresh-Mechanismus |
|-------|-------------|-------------|---------------------|
| Access Token | 15 Minuten | Memory (Frontend) | Automatisch via Refresh Token |
| Refresh Token | 30 Tage | HttpOnly Secure Cookie | Rotation bei Nutzung (altes Token wird invalidiert) |

- **Access Token:** Enthält `sub` (user_key), `email`, `display_name`, `tenant_roles` (Mapping tenant_key → role). Kurzlebig, wird bei jedem API-Request als `Authorization: Bearer <token>` mitgesendet.
- **Refresh Token:** Langlebig, wird als HttpOnly/Secure/SameSite=Lax Cookie gespeichert. Bei Nutzung wird ein neues Refresh-Token-Paar ausgestellt und das alte invalidiert (Token-Rotation verhindert Token-Diebstahl).
- **Token-Revocation:** Logout invalidiert alle Refresh Tokens des Nutzers. Optional: "Von allen Geräten abmelden" invalidiert alle Sessions.

**CSRF-Schutz-Strategie (SEC-K-004):**

Da Refresh Tokens als HttpOnly Cookie übertragen werden, sind zustandsändernde Endpunkte, die diesen Cookie verwenden, potenziell CSRF-anfällig. Die Strategie kombiniert zwei Maßnahmen:

1. **`SameSite=Lax`** (statt `Strict`): OAuth-Callbacks sind Top-Level-Navigationen (Redirect von Google/GitHub/Apple zurück zur App). `SameSite=Strict` würde den Refresh-Token-Cookie bei diesen Cross-Origin-Navigationen blockieren. `SameSite=Lax` erlaubt den Cookie bei Top-Level-Navigationen (GET), blockiert ihn aber bei Cross-Origin POST/PUT/DELETE (CSRF-Schutz für die meisten Szenarien).

2. **Double-Submit Cookie Pattern** für POST-Endpunkte, die den Refresh-Token-Cookie verwenden:
   - Bei Token-Refresh (`POST /auth/refresh`): Server setzt zusätzlich einen nicht-HttpOnly Cookie `csrf_token` mit einem zufälligen Wert. Client muss diesen Wert als `X-CSRF-Token`-Header mitsenden. Server vergleicht Cookie-Wert mit Header-Wert.
   - Betroffene Endpunkte: `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`
   - Der CSRF-Token wird bei jedem Token-Refresh erneuert (analog zur Refresh-Token-Rotation)
   - **Nicht** betroffen: `POST /auth/login`, `POST /auth/register` (verwenden keinen Cookie, sondern Request-Body-Credentials)

| Endpunkt | Cookie-basiert | CSRF-Schutz |
|----------|---------------|-------------|
| `POST /auth/login` | Nein (Body) | Nicht nötig |
| `POST /auth/register` | Nein (Body) | Nicht nötig |
| `POST /auth/refresh` | Ja (Refresh Cookie) | Double-Submit Cookie |
| `POST /auth/logout` | Ja (Refresh Cookie) | Double-Submit Cookie |
| `POST /auth/logout-all` | Ja (Refresh Cookie) | Double-Submit Cookie |
| `GET /auth/oauth/{slug}/callback` | Nein (OAuth State) | OAuth State-Parameter |
| Alle anderen Endpunkte | Nein (Bearer Token) | Nicht nötig (Token im Header) |

**Passwort-Policy:**
- Minimale Länge: 10 Zeichen
- Keine Komplexitätsregeln (NIST 800-63B Empfehlung: Länge > Komplexität)
- Bcrypt mit Cost Factor 12
- Breach-Check gegen HaveIBeenPwned API (SHA-1-Prefix, k-Anonymity, optional)
- Rate Limiting: Max. 5 fehlgeschlagene Login-Versuche pro 15 Minuten pro E-Mail

**E-Mail-Verifizierung:**
- Lokale Registrierung: Verifizierungs-Link per E-Mail (Token gültig 24h)
- SSO-Registrierung: E-Mail automatisch als verifiziert markiert (Provider garantiert Verifizierung)
- Unbestätigte Accounts können das System nutzen, aber keine Einladungen (REQ-024) versenden

**Account-Linking:**
Ein User kann mehrere Auth-Provider verknüpfen:
- Matching erfolgt über **verifizierte E-Mail-Adresse**: Login mit Google (`max@example.com`) wird automatisch mit dem lokalen Account (`max@example.com`) verknüpft
- Kein Auto-Link bei unverifizierter E-Mail (verhindert Account-Übernahme)
- User kann jederzeit zusätzliche Provider verknüpfen oder entfernen (mindestens eine Auth-Methode muss bestehen bleiben)

### 1.1 Szenarien

**Szenario 1: Lokale Registrierung — Einzelgärtner**
```
1. Nutzer öffnet /register
2. Gibt ein: E-Mail "max@example.com", Anzeigename "Max", Passwort "mein-sicheres-passwort-2024"
3. System erstellt User-Account (status: unverified)
4. Verifizierungs-E-Mail wird gesendet (Token: 24h gültig)
5. Nutzer klickt Verifizierungs-Link → status: active
6. Nutzer wird eingeloggt (Access Token + Refresh Token)
7. System erstellt automatisch einen persönlichen Tenant "Maxs Garten"
```

**Szenario 2: Google-SSO — Schnelleinstieg**
```
1. Nutzer klickt "Mit Google anmelden"
2. Redirect zu Google OAuth2 Consent Screen
3. Google gibt zurück: email="lisa@gmail.com", name="Lisa Müller", picture_url="..."
4. System prüft: Existiert User mit email="lisa@gmail.com"?
   → Nein: Neuer User wird erstellt (status: active, email_verified: true)
   → Ja: Bestehender User wird eingeloggt, Google-Provider wird verknüpft
5. JWT-Token-Paar wird ausgestellt
6. Redirect zu Dashboard
```

**Szenario 3: Generischer OIDC — Gemeinschaftsgarten mit Keycloak**
```
1. Admin hat OIDC-Provider "keycloak-gemeinschaftsgarten" konfiguriert
2. Nutzer öffnet /login → sieht Button "Gemeinschaftsgarten Berlin"
3. Redirect zu Keycloak-Login-Seite der Organisation
4. Nach Authentifizierung: OIDC-Token mit sub/email/name
5. System erstellt/verknüpft User-Account
6. Nutzer wird in den zugehörigen Tenant eingeladen (falls konfiguriert)
```

**Szenario 4: Account-Linking — Google-User setzt lokales Passwort**
```
1. Nutzer hat sich initial mit Google angemeldet
2. Navigiert zu /settings/account
3. Wählt "Lokales Passwort hinzufügen"
4. Setzt Passwort → system speichert Bcrypt-Hash
5. Nutzer kann sich jetzt wahlweise mit Google ODER E-Mail/Passwort anmelden
```

**Szenario 5: Passwort-Reset**
```
1. Nutzer klickt "Passwort vergessen" auf /login
2. Gibt E-Mail ein → System sendet Reset-Link (Token: 1h gültig, einmalig verwendbar)
3. Nutzer klickt Link → Setzt neues Passwort
4. Alle bestehenden Refresh Tokens werden invalidiert (erzwingt Neuanmeldung auf allen Geräten)
```

## 2. ArangoDB-Modellierung

### Nodes:

- **`:User`** — Benutzerkonto
  - Collection: `users`
  - Properties:
    - `email: str` (UNIQUE, lowercase-normalisiert)
    - `display_name: str` (Anzeigename, z.B. "Max Mustermann")
    - `avatar_url: Optional[str]` (Profilbild-URL, von SSO übernommen oder manuell gesetzt)
    - `locale: str` (Default: `de`, Sprachpräferenz für i18n)
    - `timezone: str` (Default: `Europe/Berlin`, IANA-Zeitzone)
    - `status: Literal['unverified', 'active', 'suspended', 'deleted']`
    - `email_verified: bool` (Default: `false`)
    - `email_verification_token: Optional[str]` (Einmalig, gehashed gespeichert)
    - `email_verification_expires: Optional[datetime]`
    - `password_hash: Optional[str]` (Bcrypt, `null` bei reinen SSO-Accounts)
    - `password_reset_token: Optional[str]` (Einmalig, gehashed gespeichert)
    - `password_reset_expires: Optional[datetime]`
    - `failed_login_attempts: int` (Default: 0, Reset nach erfolgreichem Login)
    - `locked_until: Optional[datetime]` (Temporäre Sperrung nach zu vielen Fehlversuchen)
    - `last_login_at: Optional[datetime]`
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:AuthProvider`** — Verknüpfter Authentifizierungsprovider
  - Collection: `auth_providers`
  - Properties:
    - `provider: str` (z.B. `google`, `github`, `apple`, `keycloak-gemeinschaftsgarten`)
    - `provider_user_id: str` (Eindeutige ID beim Provider, z.B. Google `sub`)
    - `provider_email: Optional[str]` (E-Mail beim Provider, kann von User.email abweichen)
    - `provider_name: Optional[str]` (Name beim Provider)
    - `provider_avatar_url: Optional[str]`
    - `access_token_encrypted: Optional[str]` (Verschlüsselt, für API-Zugriff beim Provider)
    - `refresh_token_encrypted: Optional[str]` (Verschlüsselt, für Token-Refresh beim Provider)
    - `token_expires_at: Optional[datetime]`
    - `linked_at: datetime`
    - `last_used_at: Optional[datetime]`

- **`:RefreshToken`** — Aktive Refresh-Token-Sessions
  - Collection: `refresh_tokens`
  - Properties:
    - `token_hash: str` (SHA-256 Hash des Tokens, UNIQUE)
    - `device_info: Optional[str]` (User-Agent, für "Aktive Sessions"-Übersicht)
    - `ip_address: Optional[str]` (Letzte bekannte IP; **Rechtsgrundlage:** Art. 6(1)(f) berechtigtes Interesse — Erkennung kompromittierter Sessions)
    - `ip_anonymized_at: Optional[datetime]` (Zeitpunkt der IP-Anonymisierung; `null` = noch nicht anonymisiert)
    - `issued_at: datetime`
    - `expires_at: datetime`
    - `revoked: bool` (Default: `false`)
    - `replaced_by: Optional[str]` (Token-Hash des Nachfolgers bei Rotation)
  - **IP-Anonymisierung (SEC-K-002):** Nach 7 Tagen wird `ip_address` automatisch anonymisiert (Celery-Task, NFR-011 R-03):
    - IPv4: Letztes Oktett → `0` (z.B. `192.168.1.42` → `192.168.1.0`)
    - IPv6: Auf `/48`-Präfix gekürzt (z.B. `2001:db8:85a3::8a2e:370:7334` → `2001:db8:85a3::`)
    - `ip_anonymized_at` wird auf den Anonymisierungszeitpunkt gesetzt

- **`:OidcProviderConfig`** — Konfigurierte OIDC-Provider (System-Level)
  - Collection: `oidc_provider_configs`
  - Properties:
    - `slug: str` (URL-sicher, UNIQUE, z.B. `keycloak-gemeinschaftsgarten`)
    - `display_name: str` (Anzeigename auf Login-Seite)
    - `provider_type: Literal['google', 'github', 'apple', 'oidc']`
    - `issuer_url: Optional[str]` (OIDC Discovery URL, für generische Provider)
    - `authorization_url: str`
    - `token_url: str`
    - `userinfo_url: Optional[str]`
    - `jwks_url: Optional[str]` (JSON Web Key Set für Token-Validierung)
    - `client_id: str`
    - `client_secret_encrypted: str` (Verschlüsselt gespeichert)
    - `scopes: list[str]` (Default: `['openid', 'email', 'profile']`)
    - `icon_url: Optional[str]` (Für Login-Button)
    - `enabled: bool` (Default: `true`)
    - `auto_discover: bool` (Default: `true`, nutzt `.well-known/openid-configuration`)
    - `default_tenant_key: Optional[str]` (Forward-Referenz → REQ-024: Neuen Usern automatisch diesem Tenant zuweisen. Wird erst mit REQ-024 aktiv.)
    - `created_at: datetime`
    - `updated_at: datetime`

### Edges:

```
has_auth_provider:  users → auth_providers     (1:N, User hat Auth-Provider)
has_session:        users → refresh_tokens      (1:N, User hat aktive Sessions)
```

### Indizes:

```
users:
  - PERSISTENT INDEX on [email] UNIQUE
  - PERSISTENT INDEX on [status]

auth_providers:
  - PERSISTENT INDEX on [provider, provider_user_id] UNIQUE  (eindeutig pro Provider)

refresh_tokens:
  - PERSISTENT INDEX on [token_hash] UNIQUE
  - PERSISTENT INDEX on [expires_at]  (für TTL-Cleanup)
  - TTL INDEX on [expires_at] expireAfter: 0  (automatische Bereinigung abgelaufener Tokens)

oidc_provider_configs:
  - PERSISTENT INDEX on [slug] UNIQUE
  - PERSISTENT INDEX on [provider_type]
```

### AQL-Beispiellogik:

**User mit allen Auth-Providern laden:**
```aql
LET user = DOCUMENT(users, @user_key)
LET providers = (
  FOR ap IN 1..1 OUTBOUND user GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_auth_provider'] }
    RETURN {
      provider: ap.provider,
      provider_email: ap.provider_email,
      linked_at: ap.linked_at,
      last_used_at: ap.last_used_at
    }
)
RETURN MERGE(user, { auth_providers: providers })
```

**User per Provider-ID finden (SSO-Login):**
```aql
FOR ap IN auth_providers
  FILTER ap.provider == @provider AND ap.provider_user_id == @provider_user_id
  LET user = FIRST(
    FOR u IN 1..1 INBOUND ap GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_auth_provider'] }
      RETURN u
  )
  RETURN { auth_provider: ap, user: user }
```

**Aktive Sessions eines Users:**
```aql
FOR rt IN 1..1 OUTBOUND DOCUMENT(users, @user_key) GRAPH 'kamerplanter_graph'
  OPTIONS { edgeCollections: ['has_session'] }
  FILTER rt.revoked == false AND rt.expires_at > DATE_ISO8601(DATE_NOW())
  SORT rt.issued_at DESC
  RETURN {
    device_info: rt.device_info,
    ip_address: rt.ip_address,
    issued_at: rt.issued_at,
    expires_at: rt.expires_at
  }
```

**Abgelaufene/Revoked Tokens bereinigen (Celery-Task):**
```aql
FOR rt IN refresh_tokens
  FILTER rt.revoked == true OR rt.expires_at < DATE_ISO8601(DATE_NOW())
  REMOVE rt IN refresh_tokens
```

## 3. Backend-Architektur

### 3.1 Engine-Schicht

**`PasswordEngine`** — Passwort-Hashing und -Validierung (pure Logik, kein I/O):

```python
class PasswordEngine:
    BCRYPT_ROUNDS = 12
    MIN_LENGTH = 10

    def hash_password(self, password: str) -> str: ...
    def verify_password(self, password: str, password_hash: str) -> bool: ...
    def validate_password_policy(self, password: str) -> list[str]: ...
        # Gibt Liste von Fehlermeldungen zurück, leer = gültig
        # Prüft: Mindestlänge, nicht identisch mit E-Mail
```

**`TokenEngine`** — JWT-Erstellung und -Validierung (pure Logik, nutzt `authlib.jose`):

```python
# Implementierung nutzt authlib.jose.jwt (nicht python-jose)
# pip install authlib

class TokenEngine:
    def create_access_token(self, user: User, tenant_roles: dict[str, str]) -> str: ...
        # Payload: { sub: user_key, email, display_name, tenant_roles, exp, iat, type: "access" }
        # Algorithmus: HS256 (via authlib.jose.jwt.encode), Lebensdauer: 15 Minuten

    def create_refresh_token(self) -> tuple[str, str]: ...
        # Gibt (raw_token, token_hash) zurück
        # raw_token = secrets.token_urlsafe(32), token_hash = SHA-256(raw_token)
        # raw_token wird an Client gesendet, token_hash wird gespeichert

    def decode_access_token(self, token: str) -> TokenPayload: ...
        # Validiert Signatur, Ablaufdatum, Typ (via authlib.jose.jwt.decode)
        # Wirft InvalidTokenError bei Fehler

    def hash_token(self, raw_token: str) -> str: ...
        # SHA-256 Hash für DB-Speicherung (hashlib.sha256)
```

**`OAuthEngine`** — OAuth2/OIDC-Flow-Logik (nutzt `authlib.integrations.httpx_client`):

Authlib stellt `AsyncOAuth2Client` bereit, der PKCE, OIDC Discovery und Token-Exchange kapselt. Der `OAuthEngine` nutzt diesen Client intern und normalisiert die Provider-spezifischen Unterschiede:

```python
# Implementierung nutzt authlib.integrations.httpx_client.AsyncOAuth2Client
# PKCE (S256) wird automatisch von Authlib gehandhabt

class OAuthEngine:
    def create_oauth_client(self, provider_config: OidcProviderConfig) -> AsyncOAuth2Client: ...
        # Erstellt konfigurierten Authlib-Client mit PKCE-Support
        # Bei auto_discover=True: nutzt Authlib's OIDC Discovery automatisch

    def build_authorization_url(self, client: AsyncOAuth2Client, state: str, nonce: str) -> str: ...
        # Delegiert an client.create_authorization_url() (PKCE code_verifier wird automatisch generiert)

    def exchange_code_for_token(self, client: AsyncOAuth2Client, code: str, code_verifier: str) -> dict: ...
        # Delegiert an client.fetch_token() — gibt id_token + access_token zurück

    def validate_state(self, state: str, expected_state: str) -> bool: ...
        # CSRF-Schutz: Vergleicht state-Parameter

    def extract_user_info(self, provider_type: str, id_token: dict, userinfo: dict) -> OAuthUserInfo: ...
        # Normalisiert Provider-spezifische Claims zu einheitlichem Format
        # Google: sub, email, name, picture
        # GitHub: id, email (separater API-Call), login, avatar_url
        # Apple: sub, email, name (nur beim ersten Login — muss gespeichert werden!)
        # OIDC: sub, email, preferred_username, name, picture

    def should_auto_link(self, existing_user: User, oauth_email: str) -> bool: ...
        # True wenn existing_user.email == oauth_email UND existing_user.email_verified == True
```

**`LoginThrottleEngine`** — Brute-Force-Schutz (pure Logik):

```python
class LoginThrottleEngine:
    MAX_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    def check_allowed(self, failed_attempts: int, locked_until: Optional[datetime]) -> bool: ...
    def calculate_lockout(self, failed_attempts: int) -> Optional[datetime]: ...
        # Exponentielle Verzögerung: 15min, 30min, 1h, 2h, 4h
```

### 3.2 Service-Schicht

**`AuthService`** — Orchestriert Authentifizierungsflows:

```python
class AuthService:
    def __init__(self, user_repo, auth_provider_repo, refresh_token_repo,
                 oidc_config_repo, password_engine, token_engine,
                 oauth_engine, login_throttle_engine, email_service): ...

    # --- Lokale Authentifizierung ---
    async def register_local(self, email: str, password: str, display_name: str) -> User: ...
        # 1. Validiert Passwort-Policy (PasswordEngine)
        # 2. Prüft E-Mail-Eindeutigkeit
        # 3. Erstellt User (status: unverified)
        # 4. Sendet Verifizierungs-E-Mail
        # 5. Erstellt persönlichen Default-Tenant (REQ-024)

    async def login_local(self, email: str, password: str) -> TokenPair: ...
        # 1. Prüft Throttle (LoginThrottleEngine)
        # 2. Findet User per E-Mail
        # 3. Verifiziert Passwort (PasswordEngine)
        # 4. Erstellt Token-Paar (TokenEngine)
        # 5. Speichert RefreshToken
        # 6. Aktualisiert last_login_at

    async def verify_email(self, token: str) -> User: ...
    async def request_password_reset(self, email: str) -> None: ...
        # Sendet Reset-E-Mail, KEIN Fehler wenn E-Mail nicht existiert (Enumeration-Schutz)
    async def reset_password(self, token: str, new_password: str) -> None: ...
        # Invalidiert alle Refresh Tokens nach Reset

    # --- Föderierte Authentifizierung ---
    async def initiate_oauth(self, provider_slug: str) -> OAuthRedirect: ...
        # 1. Lädt OidcProviderConfig
        # 2. Generiert state + nonce (CSRF-Schutz)
        # 3. Speichert state in Redis (5 Min TTL)
        # 4. Gibt Authorization URL zurück

    async def complete_oauth(self, provider_slug: str, code: str, state: str) -> TokenPair: ...
        # 1. Validiert state (OAuthEngine)
        # 2. Tauscht code gegen Token beim Provider
        # 3. Extrahiert User-Info (OAuthEngine)
        # 4. Findet/erstellt User + AuthProvider
        # 5. Auto-Link falls gleiche verifizierte E-Mail (OAuthEngine)
        # 6. Erstellt JWT-Token-Paar

    # --- Token-Management ---
    async def refresh_tokens(self, refresh_token: str) -> TokenPair: ...
        # Token-Rotation: altes Token wird invalidiert, neues Paar wird erstellt

    async def logout(self, refresh_token: str) -> None: ...
        # Invalidiert das aktuelle Refresh Token

    async def logout_all_devices(self, user_key: str) -> int: ...
        # Invalidiert ALLE Refresh Tokens des Users, gibt Anzahl zurück

    # --- Account-Linking ---
    async def link_provider(self, user_key: str, provider_slug: str, code: str, state: str) -> AuthProvider: ...
    async def unlink_provider(self, user_key: str, provider_key: str) -> None: ...
        # Fehler wenn es die letzte Auth-Methode wäre

    async def add_local_password(self, user_key: str, password: str) -> None: ...
        # Für SSO-Only-User die ein lokales Passwort setzen wollen
```

**`UserService`** — Benutzerprofil-Verwaltung:

```python
class UserService:
    def __init__(self, user_repo, auth_provider_repo): ...

    async def get_profile(self, user_key: str) -> UserProfile: ...
    async def update_profile(self, user_key: str, updates: UserProfileUpdate) -> User: ...
        # Erlaubte Felder: display_name, avatar_url, locale, timezone
    async def list_auth_providers(self, user_key: str) -> list[AuthProviderInfo]: ...
    async def list_active_sessions(self, user_key: str) -> list[SessionInfo]: ...
    async def delete_account(self, user_key: str) -> None: ...
        # Soft-Delete: status → deleted, E-Mail anonymisiert
        # Alle Refresh Tokens invalidiert
        # Tenant-Mitgliedschaften entfernt (REQ-024)
```

### 3.3 API-Schicht

**Router: `/api/v1/auth`** — Authentifizierung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| POST | `/auth/register` | Lokale Registrierung | Nein |
| POST | `/auth/login` | Lokaler Login | Nein |
| POST | `/auth/logout` | Logout (aktuelles Gerät) | Ja |
| POST | `/auth/logout-all` | Logout (alle Geräte) | Ja |
| POST | `/auth/refresh` | Token-Refresh | Nein (Cookie) |
| POST | `/auth/verify-email` | E-Mail bestätigen | Nein |
| POST | `/auth/password-reset/request` | Passwort-Reset anfordern | Nein |
| POST | `/auth/password-reset/confirm` | Passwort-Reset durchführen | Nein |
| GET | `/auth/oauth/providers` | Aktivierte Provider auflisten (für Login-Seite) | Nein |
| GET | `/auth/oauth/{provider_slug}` | OAuth-Redirect initiieren | Nein |
| GET | `/auth/oauth/{provider_slug}/callback` | OAuth-Callback verarbeiten | Nein |

**Router: `/api/v1/users`** — Benutzerverwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/users/me` | Eigenes Profil abrufen | Ja |
| PATCH | `/users/me` | Eigenes Profil aktualisieren | Ja |
| GET | `/users/me/providers` | Verknüpfte Auth-Provider auflisten | Ja |
| POST | `/users/me/providers/{provider_slug}/link` | Provider verknüpfen | Ja |
| DELETE | `/users/me/providers/{provider_key}` | Provider-Verknüpfung entfernen | Ja |
| POST | `/users/me/password` | Lokales Passwort setzen/ändern | Ja |
| GET | `/users/me/sessions` | Aktive Sessions auflisten | Ja |
| DELETE | `/users/me/sessions/{session_key}` | Einzelne Session beenden | Ja |
| DELETE | `/users/me` | Account löschen (Soft-Delete) | Ja |

**Router: `/api/v1/admin/oidc-providers`** — OIDC-Provider-Verwaltung (nur System-Admin):

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/admin/oidc-providers` | Alle konfigurierten Provider auflisten | Admin |
| POST | `/admin/oidc-providers` | Neuen OIDC-Provider registrieren | Admin |
| GET | `/admin/oidc-providers/{slug}` | Provider-Details abrufen | Admin |
| PATCH | `/admin/oidc-providers/{slug}` | Provider aktualisieren | Admin |
| DELETE | `/admin/oidc-providers/{slug}` | Provider deaktivieren | Admin |
| POST | `/admin/oidc-providers/{slug}/test` | OIDC-Discovery testen | Admin |

**Gesamtanzahl API-Endpunkte:** ~23

### 3.4 Middleware

**`AuthMiddleware`** — FastAPI Dependency für geschützte Endpunkte:

```python
async def get_current_user(
    authorization: str = Header(None),
    token_engine: TokenEngine = Depends(get_token_engine),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Extrahiert und validiert den Access Token.
    Gibt den vollständigen User zurück.
    Wirft 401 bei fehlendem/ungültigem Token."""

async def get_current_user_optional(
    authorization: str = Header(None),
    token_engine: TokenEngine = Depends(get_token_engine),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Optional[User]:
    """Wie get_current_user, gibt aber None statt 401 bei fehlendem Token.
    Für Endpunkte die sowohl authentifiziert als auch anonym funktionieren."""

def require_role(role: str):
    """Factory für Dependency die eine bestimmte Tenant-Rolle erfordert.
    Wird in REQ-024 vollständig spezifiziert."""
```

### 3.5 Celery-Tasks

| Task | Schedule | Beschreibung |
|------|----------|-------------|
| `cleanup_expired_tokens` | Stündlich | Entfernt abgelaufene/revoked Refresh Tokens |
| `cleanup_unverified_accounts` | Täglich 03:00 | Löscht unbestätigte Accounts älter als 7 Tage |
| `rotate_oidc_discovery` | Alle 6 Stunden | Aktualisiert OIDC-Discovery-Dokumente (JWKS, Endpoints) |

## 4. Frontend

### 4.1 Neue Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `LoginPage` | `/login` | E-Mail/Passwort-Login + SSO-Buttons |
| `RegisterPage` | `/register` | Lokale Registrierung |
| `EmailVerificationPage` | `/verify-email/:token` | E-Mail-Bestätigung |
| `PasswordResetRequestPage` | `/password-reset` | Passwort-Reset anfordern |
| `PasswordResetConfirmPage` | `/password-reset/:token` | Neues Passwort setzen |
| `AccountSettingsPage` | `/settings/account` | Profil, Auth-Provider, Sessions |

### 4.2 Komponenten

**`LoginPage`:**
- E-Mail + Passwort-Formular
- Divider "oder"
- SSO-Buttons (dynamisch aus `/api/v1/auth/oauth/providers`):
  - Google: Offizielles Google-Sign-In-Branding
  - GitHub: GitHub-Logo + "Mit GitHub anmelden"
  - Apple: Offizielles Apple-Sign-In-Branding (Dark/Light Modus)
  - Generische OIDC: icon_url + display_name
- Link zu "Passwort vergessen"
- Link zu "Registrieren"

**`AccountSettingsPage`:**
- **Tab "Profil":** Anzeigename, Avatar (URL-Eingabe), Sprache (DE/EN), Zeitzone
- **Tab "Sicherheit":** Passwort ändern/setzen, Verknüpfte Provider (Google ✓, GitHub ✓, etc.), Provider entfernen
- **Tab "Sessions":** Liste aktiver Sessions (Gerät, IP, Zeitpunkt), "Andere Sessions beenden"-Button
- **Tab "Account":** Account löschen (Bestätigungs-Dialog mit Passworteingabe)

### 4.3 Auth-State-Management (Redux)

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Thunks:
// loginLocal(email, password) → setzt user + accessToken
// loginOAuth(providerSlug) → Redirect zu OAuth-Provider
// oauthCallback(providerSlug, code, state) → setzt user + accessToken
// refreshToken() → nutzt Cookie, aktualisiert accessToken
// logout() → löscht State + Cookie
```

### 4.4 Axios-Interceptor

```typescript
// Request-Interceptor: Fügt Authorization-Header hinzu
// Response-Interceptor: Bei 401 → automatischer Token-Refresh → Retry
// Falls Refresh fehlschlägt → Logout + Redirect zu /login
```

### 4.5 Route-Guards

```typescript
// ProtectedRoute: Erfordert authentifizierten User, Redirect zu /login
// PublicOnlyRoute: Nur für nicht-authentifizierte User (Login/Register), Redirect zu /dashboard
```

## 5. Seed-Daten

### Benannte SSO-Provider (Vorkonfiguriert):

```json
[
  {
    "slug": "google",
    "display_name": "Google",
    "provider_type": "google",
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
    "scopes": ["openid", "email", "profile"],
    "enabled": false,
    "auto_discover": true
  },
  {
    "slug": "github",
    "display_name": "GitHub",
    "provider_type": "github",
    "authorization_url": "https://github.com/login/oauth/authorize",
    "token_url": "https://github.com/login/oauth/access_token",
    "userinfo_url": "https://api.github.com/user",
    "scopes": ["read:user", "user:email"],
    "enabled": false,
    "auto_discover": false
  },
  {
    "slug": "apple",
    "display_name": "Apple",
    "provider_type": "apple",
    "authorization_url": "https://appleid.apple.com/auth/authorize",
    "token_url": "https://appleid.apple.com/auth/token",
    "jwks_url": "https://appleid.apple.com/auth/keys",
    "scopes": ["name", "email"],
    "enabled": false,
    "auto_discover": false
  }
]
```

**Hinweis:** Benannte Provider werden mit `enabled: false` ausgeliefert. Aktivierung erfordert das Setzen von `client_id` und `client_secret` durch den System-Admin.

### Demo-User (Nur Entwicklungsumgebung):

```json
{
  "email": "demo@kamerplanter.local",
  "display_name": "Demo-Gärtner",
  "password": "demo-passwort-2024",
  "status": "active",
  "email_verified": true,
  "locale": "de",
  "timezone": "Europe/Berlin"
}
```

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Lokale Registrierung erstellt User mit `status: unverified` und sendet Verifizierungs-E-Mail | Integration |
| AK-02 | Verifizierungs-Link setzt `status: active` und `email_verified: true` | Integration |
| AK-03 | Lokaler Login gibt Access Token (15 Min) + Refresh Token (30 Tage, HttpOnly Cookie) zurück | Integration |
| AK-04 | Token-Refresh erstellt neues Token-Paar und invalidiert altes Refresh Token (Rotation) | Integration |
| AK-05 | Nach 5 Fehlversuchen wird Account 15 Minuten gesperrt (`locked_until` gesetzt) | Unit + Integration |
| AK-06 | Passwort-Reset-Token ist 1 Stunde gültig und einmalig verwendbar | Integration |
| AK-07 | Nach Passwort-Reset sind alle bestehenden Refresh Tokens invalidiert | Integration |
| AK-08 | Google-OAuth2-Login erstellt User mit `email_verified: true` und verknüpftem AuthProvider | Integration |
| AK-09 | GitHub-OAuth2-Login holt E-Mail via separatem API-Call wenn privat | Integration |
| AK-10 | Apple-Sign-In speichert Name beim ersten Login (wird nur einmal übermittelt) | Integration |
| AK-11 | Generischer OIDC-Provider mit `auto_discover: true` nutzt `.well-known/openid-configuration` | Integration |
| AK-12 | Account-Linking: SSO-Login mit gleicher verifizierter E-Mail verknüpft automatisch mit bestehendem Account | Integration |
| AK-13 | Account-Linking: Entfernen des letzten Auth-Providers wird verhindert (mindestens eine Methode) | Unit |
| AK-14 | Logout invalidiert Refresh Token; Logout-All invalidiert alle Tokens des Users | Integration |
| AK-15 | Profil-Update (display_name, locale, timezone) persistiert korrekt | Integration |
| AK-16 | Account-Löschung setzt `status: deleted`, anonymisiert E-Mail, invalidiert alle Tokens | Integration |
| AK-17 | Celery-Task bereinigt abgelaufene Tokens stündlich und unbestätigte Accounts nach 7 Tagen | Integration |

### Sicherheitskriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| SK-01 | Passwörter sind ausschließlich als Bcrypt-Hash (Cost 12) gespeichert | Code Review |
| SK-02 | Refresh Tokens sind als SHA-256-Hash gespeichert (Klartext nie in DB) | Code Review |
| SK-03 | OAuth-state-Parameter verhindert CSRF (Redis, 5 Min TTL) | Integration |
| SK-04 | PKCE (Proof Key for Code Exchange) wird für alle OAuth-Flows verwendet | Integration |
| SK-05 | Passwort-Reset-Request gibt keinen Hinweis ob E-Mail existiert (Enumeration-Schutz) | Integration |
| SK-06 | Client Secrets und Provider-Tokens sind AES-256-verschlüsselt in der Datenbank | Code Review |
| SK-07 | Alle Auth-Endpunkte haben Rate Limiting (100/min pro IP) | Integration |
| SK-08 | Access Token enthält keine sensitiven Daten (kein Passwort-Hash, keine Provider-Tokens) | Unit |

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | Login-Seite zeigt dynamisch alle aktivierten SSO-Provider als Buttons | E2E |
| FK-02 | Nach erfolgreichem Login wird User zum Dashboard redirected | E2E |
| FK-03 | 401-Response löst automatischen Token-Refresh aus; bei Refresh-Fehler → Redirect zu /login | Integration |
| FK-04 | AccountSettingsPage zeigt verknüpfte Provider und aktive Sessions korrekt an | E2E |
| FK-05 | Account-Löschung erfordert Passwort-Bestätigung im Dialog | E2E |

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| NFR-001 | Architektur-Layer (erweitert §6.1 JWT-Skizze zur vollständigen Spezifikation) |
| NFR-006 | API-Fehlerbehandlung (401 UNAUTHORIZED, 403 FORBIDDEN) |
| NFR-007 | Retry-Logik (Auth-Fehler sind nicht retryable) |

### Wird benötigt von:

| REQ | Bezug |
|-----|-------|
| REQ-024 | Mandantenverwaltung — baut auf User-Entität und JWT-Token auf |
| REQ-006 | Task-Zuweisung an User (zukünftige Erweiterung) |
| REQ-015 | Kalenderansicht — "vorbereitet für JWT-Auth" |

### Neue Infrastruktur-Abhängigkeiten:

| Komponente | Zweck |
|------------|-------|
| Redis | OAuth-State-Speicherung (5 Min TTL), Rate Limiting |
| Fernet/AES-256 | Verschlüsselung von Provider-Secrets und -Tokens |

### E-Mail-Service (Adapter-Pattern):

Der E-Mail-Versand wird über ein **abstraktes Interface** entkapselt (analog zum bestehenden Adapter-Pattern für GBIF/Perenual in REQ-011):

```python
# domain/interfaces/email_service.py
class IEmailService(ABC):
    @abstractmethod
    async def send_verification_email(self, to: str, token: str, display_name: str) -> None: ...
    @abstractmethod
    async def send_password_reset_email(self, to: str, token: str) -> None: ...
    @abstractmethod
    async def send_invitation_email(self, to: str, tenant_name: str, inviter_name: str, token: str, role: str) -> None: ...
```

Konkrete Implementierungen (austauschbar, nicht Teil dieser REQ):
- `SmtpEmailAdapter` — Direkter SMTP-Versand (`aiosmtplib`)
- `ResendEmailAdapter` — Transactional API (Resend)
- `ConsoleEmailAdapter` — Entwicklungsumgebung (loggt E-Mails auf stdout)

Die Wahl der konkreten Implementierung erfolgt per Konfiguration (`EMAIL_ADAPTER=smtp|resend|console`). Für die Entwicklungsumgebung genügt der `ConsoleEmailAdapter`.

## 8. Neue Python-Dependencies

| Paket | Version | Zweck | Status im Stack |
|-------|---------|-------|----------------|
| `authlib` | `>=1.3.0` | JWT (HS256), OAuth2 Client, OIDC Discovery, PKCE | **Neu** — ersetzt `python-jose` aus NFR-001 §6.1 |
| `passlib[bcrypt]` | `>=1.7.4` | Passwort-Hashing (Bcrypt, Cost 12) | **Neu** — in NFR-001 §6.1 referenziert, aber nicht installiert |
| `slowapi` | `>=0.1.9` | Rate Limiting (nutzt Redis als Backend) | **Neu** |
| `cryptography` | `>=42.0` | Fernet-Verschlüsselung für Provider-Secrets | **Neu** |
| `httpx` | `>=0.28.0` | HTTP-Client für GitHub-API, HIBP-Check | **Bereits vorhanden** |
| `redis` | `>=5.2.0` | OAuth-State, Rate Limiting, Token-Blocklist | **Bereits vorhanden** (Celery-Broker) |

## 9. Scope-Abgrenzung

**In Scope:**
- Lokale Benutzerkonten (E-Mail + Passwort)
- OAuth2/OIDC mit Google, GitHub, Apple (benannt) + generische OIDC-Provider
- JWT Access/Refresh Token Lifecycle mit Rotation
- Benutzerprofil-Verwaltung (Name, Avatar, Locale, Timezone)
- Passwort-Reset per E-Mail
- Account-Linking (mehrere Auth-Methoden pro User)
- Login-Throttling und Rate Limiting
- Session-Verwaltung (aktive Geräte, Logout-All)
- OIDC-Provider-Konfiguration durch System-Admin

**Nicht in Scope (bewusst ausgeklammert):**
- Mandanten/Tenants und Rollenkonzept → REQ-024
- 2-Faktor-Authentifizierung (TOTP, WebAuthn) → zukünftige Erweiterung
- Social-Login-Profilsynchronisation (regelmäßiger Name/Bild-Abgleich) → zukünftig
- SAML 2.0 → Enterprise-Segment, aktuell nicht priorisiert
- E-Mail-Template-Customization → Standard-Templates genügen initial
- User-Administration durch Nicht-Admins (Nutzer können nur ihr eigenes Profil verwalten)
