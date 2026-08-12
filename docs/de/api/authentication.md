# Authentifizierung

Kamerplanter unterstützt zwei Authentifizierungsmethoden: **Lokale Konten** (E-Mail + Passwort) und **föderierte Konten** (OAuth 2.0 / OIDC über Google, GitHub, Apple oder generische Provider). Für maschinelle Integrationen (Home Assistant, CI/CD) stehen **API-Keys** zur Verfügung.

!!! note "Light-Modus"
    Im Light-Modus (`KAMERPLANTER_MODE=light`) ist keine Authentifizierung erforderlich. Alle Auth-Endpunkte unter `/auth/...` sind in diesem Modus deaktiviert. Dieser Abschnitt gilt nur für den Full-Modus.

---

## Token-Modell

| Token | Gültigkeitsdauer | Transport | Erneuerung |
|-------|-----------------|-----------|-----------|
| Access Token (JWT) | 15 Minuten | `Authorization: Bearer <token>` | Via Refresh-Token |
| Refresh Token | 30 Tage | HttpOnly Cookie `kp_refresh` | Rotation bei jeder Erneuerung |

Das **Access Token** ist ein signiertes JWT (HS256). Es enthält die Nutzer-ID und läuft nach 15 Minuten ab. Es wird im Arbeitsspeicher der Client-Anwendung gehalten — niemals im localStorage.

Das **Refresh Token** wird als HttpOnly-Cookie gesetzt. Es ist für JavaScript nicht lesbar und schützt damit vor XSS-Angriffen. Bei jedem Aufruf von `/auth/refresh` wird das Token rotiert — das alte Token wird ungültig, ein neues ausgestellt.

---

## Registrierung

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "gartner@example.com",
  "password": "sicheres-passwort-2026",
  "display_name": "Lena Gärtner"
}
```

**Anforderungen an das Passwort:** Mindestens 10, maximal 128 Zeichen.

**Antwort (201 Created):**

```json
{
  "key": "usr_abc123",
  "email": "gartner@example.com",
  "display_name": "Lena Gärtner",
  "email_verified": false,
  "is_active": true,
  "avatar_url": null,
  "locale": "de",
  "timezone": "Europe/Berlin",
  "last_login_at": null,
  "created_at": "2026-03-17T10:00:00Z"
}
```

Nach der Registrierung wird ein persönlicher Mandant automatisch angelegt. Wenn E-Mail-Verifikation aktiv ist (`REQUIRE_EMAIL_VERIFICATION=true`), muss die E-Mail-Adresse vor dem ersten Login bestätigt werden.

### E-Mail-Verifizierung

```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "<token-aus-der-e-mail>"
}
```

---

## Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "gartner@example.com",
  "password": "sicheres-passwort-2026",
  "remember_me": false
}
```

**Antwort (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Gleichzeitig setzt der Server den HttpOnly-Cookie `kp_refresh`. Der Wert von `expires_in` ist in Sekunden angegeben (900 = 15 Minuten).

**`remember_me: true`** verlängert die Lebensdauer des Refresh-Cookies auf 30 Tage. Andernfalls ist der Cookie ein Session-Cookie (läuft beim Schließen des Browsers ab).

### Demo-Konto

In Entwicklungs- und Testumgebungen steht ein vorkonfiguriertes Demo-Konto bereit:

```json
{
  "email": "demo@kamerplanter.local",
  "password": "demo-passwort-2024"
}
```

!!! warning "Produktionsbetrieb"
    Das Demo-Konto und die Demo-Daten dürfen in Produktionsumgebungen nicht aktiv sein. Entfernen Sie den Seed-Schritt aus der Deployment-Konfiguration.

---

## Access Token verwenden

Jede API-Anfrage, die Authentifizierung erfordert, benötigt das Access Token als Bearer-Token im `Authorization`-Header:

```http
GET /api/v1/t/mein-garten/plant-instances/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Token erneuern

Das Access Token läuft nach 15 Minuten ab. Zur Erneuerung wird der Refresh-Cookie automatisch mitgesendet (Browser setzt den Cookie bei Anfragen an `/api/v1/auth`):

```http
POST /api/v1/auth/refresh
X-CSRF-Token: <csrf-token>
```

!!! note "CSRF-Schutz"
    Token-mutierende Endpunkte (`/refresh`, `/logout`, `/logout-all`) erfordern den Header `X-CSRF-Token`. Das CSRF-Token wird als reguläres Cookie `kp_csrf` gesetzt und kann von JavaScript gelesen werden. Es wird bei Login und Refresh erneuert.

**Antwort (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Das alte Refresh-Token wird ungültig. Der neue Refresh-Cookie wird automatisch gesetzt.

---

## Logout

### Aktuellen Browser abmelden

```http
POST /api/v1/auth/logout
X-CSRF-Token: <csrf-token>
```

Invalidiert das aktuelle Refresh-Token und löscht den Cookie.

### Alle Sitzungen abmelden

```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access-token>
X-CSRF-Token: <csrf-token>
```

Invalidiert alle Refresh-Tokens des Nutzers auf allen Geräten.

---

## Passwort zurücksetzen

### Zurücksetzungs-E-Mail anfordern

```http
POST /api/v1/auth/password-reset/request
Content-Type: application/json

{
  "email": "gartner@example.com"
}
```

Aus Sicherheitsgründen gibt dieser Endpunkt immer dieselbe Erfolgsantwort zurück, unabhängig davon, ob die E-Mail-Adresse existiert.

### Neues Passwort setzen

```http
POST /api/v1/auth/password-reset/confirm
Content-Type: application/json

{
  "token": "<token-aus-der-e-mail>",
  "new_password": "neues-passwort-2026"
}
```

---

## OAuth 2.0 / OIDC (Federated Login)

!!! note "Stub-Implementierung"
    Die OAuth/OIDC-Integration ist als Stub implementiert. Die Endpunkte existieren, liefern jedoch noch keinen vollständigen Datenaustausch. Eine vollständige Implementierung ist für einen Folge-Sprint geplant.

### Verfügbare Provider abfragen

```http
GET /api/v1/auth/oauth/providers
```

**Antwort:**

```json
[
  {
    "slug": "google",
    "display_name": "Google",
    "icon_url": "https://..."
  }
]
```

### OAuth-Flow initiieren

```http
GET /api/v1/auth/oauth/{slug}
```

Der Server antwortet mit einem `302`-Redirect zur Autorisierungs-URL des Providers. Nach erfolgreichem Login beim Provider wird der Nutzer zum Callback-Endpunkt zurückgeleitet.

```
GET /api/v1/auth/oauth/{slug}/callback?code=...&state=...
```

Der Server setzt die Cookies und leitet zum Frontend weiter:

```
{frontend_url}/auth/callback?access_token=...&expires_in=900
```

---

## API-Keys (M2M-Integration)

API-Keys ermöglichen maschinellen Zugriff ohne interaktiven Login — zum Beispiel für Home Assistant, Grafana oder CI/CD-Pipelines.

### API-Key erstellen

```http
POST /api/v1/auth/api-keys
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "label": "Home Assistant Integration",
  "tenant_scope": "mein-garten"
}
```

**Antwort (201 Created):**

```json
{
  "key": "apk_xyz789",
  "label": "Home Assistant Integration",
  "raw_key": "kp_sk_abc...xyz",
  "key_prefix": "kp_sk_abc",
  "tenant_scope": "mein-garten",
  "created_at": "2026-03-17T10:00:00Z"
}
```

!!! danger "Raw Key nur einmal sichtbar"
    Das Feld `raw_key` wird nur bei der Erstellung angezeigt und danach nicht mehr ausgegeben. Speichern Sie den Key sofort an einem sicheren Ort.

### API-Key verwenden

```http
GET /api/v1/t/mein-garten/plant-instances/
Authorization: Bearer kp_sk_abc...xyz
```

Der API-Key wird im selben `Authorization`-Header wie ein JWT verwendet.

### API-Keys auflisten

```http
GET /api/v1/auth/api-keys
Authorization: Bearer <access-token>
```

Die Antwort enthält alle Keys des Nutzers ohne den `raw_key`-Wert.

### API-Key widerrufen

```http
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer <access-token>
```

---

## Gerätekopplung (QR-Code)

Für native Mobil-Apps (z. B. die künftige Flutter-App) bietet Kamerplanter eine QR-Code-Kopplung: Ein bereits angemeldeter Nutzer lässt sich im Web-Frontend einen QR-Code anzeigen, scannt ihn mit der App und erhält so ein eigenständiges Token-Paar — ohne Passworteingabe auf dem Mobilgerät. <!-- REQ-023 -->

Der Ablauf hat drei Schritte: Ein angemeldeter Client fordert einen Kopplungscode an (1), die App liest den QR-Code und tauscht den Code gegen ein Token-Paar ein (2), und weil native Clients keinen Cookie-Speicher haben, erneuert die App ihr Zugriffstoken über einen eigenen, cookie-losen Transport (3).

### Kopplungscode anfordern

```http
POST /api/v1/auth/device-pairing
Authorization: Bearer <access-token>
```

**Antwort (201 Created):**

```json
{
  "payload_version": 1,
  "server_url": "https://garten.example.org",
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
  "expires_at": "2026-08-11T14:32:41Z",
  "expires_in": 90
}
```

`server_url` stammt aus der auf dem Server konfigurierten Basis-URL der Instanz — nicht aus der URL der eingehenden Anfrage, die hinter einem Reverse Proxy von außen gar nicht erreichbar wäre. `expires_in` ist bereits die verbleibende Gültigkeitsdauer in Sekunden und steht im Einklang mit `expires_at`.

### QR-Payload

Der QR-Code, den die App scannt, kodiert genau diese drei Felder als JSON:

```json
{
  "v": 1,
  "url": "https://garten.example.org",
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3"
}
```

Das Feld `v` (entspricht `payload_version`) existiert für Vorwärtskompatibilität: Eine künftige App-Version kann eine ihr unbekannte Payload-Version ablehnen, statt sie fehlzuinterpretieren.

### Kopplungscode einlösen

```http
POST /api/v1/auth/device-pairing/redeem
Content-Type: application/json

{
  "code": "Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWdjR0ZwY21sdVp3",
  "device_name": "Pixel 8 (Gewächshaus)"
}
```

Dieser Endpunkt ist **öffentlich** — die App hat zu diesem Zeitpunkt noch kein eigenes Credential, der gescannte Code ist der Nachweis.

**Antwort (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl"
}
```

!!! note "Refresh Token im JSON-Body"
    Anders als beim Browser-Login (siehe [Token-Modell](#token-modell)) liefert die Kopplung das Refresh Token im JSON-Antwortkörper aus und setzt **keinen** Cookie. Das ist bewusst so gebaut: Native Clients besitzen keinen Cookie-Speicher und müssen das Token selbst entgegennehmen, um es sicher (z. B. im Android Keystore) abzulegen.

`device_name` ist optional, maximal 64 Zeichen lang und wird — falls angegeben — als Bezeichnung in der [Sitzungsliste](../user-guide/account.md#aktive-sitzungen-einsehen-und-beenden) angezeigt.

### Zugriffstoken erneuern (native Clients)

Weil ein gekoppeltes Gerät keinen Cookie-Speicher hat, akzeptiert `POST /api/v1/auth/refresh` zusätzlich zum Cookie-Ablauf einen optionalen JSON-Body:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "hZ3JvdzogcmVmcmVzaCB0b2tlbiBmb3IgYSBwYWlyZWQgZGV2aWNl"
}
```

**Antwort (200 OK):** identisch zur Antwort von `/device-pairing/redeem` — `{access_token, token_type, expires_in, refresh_token}` mit dem rotierten Refresh Token im Body.

Ist der Body vorhanden und trägt ein Refresh Token, gilt:

- Der `X-CSRF-Token`-Header wird **nicht** benötigt (kein Cookie wird verbraucht, also gibt es nichts, wovor der CSRF-Schutz schützen müsste).
- Es wird **kein** Cookie gesetzt.
- Das rotierte Refresh Token kommt im JSON-Body zurück.

Fehlt das Feld `refresh_token` im Body, ist es `null`, oder ist der gesamte Body leer, greift stattdessen der klassische Cookie-Pfad inklusive CSRF-Prüfung. Sind Body-Token **und** Cookie gleichzeitig vorhanden, gewinnt der Body — der Cookie wird in diesem Fall ignoriert, nicht als Fallback verbraucht.

!!! warning "`Content-Type: application/json` ist Pflicht"
    Ein nicht leerer Body, der kein gültiges JSON ist, wird mit `422 Unprocessable Entity` abgelehnt. Native Clients müssen den Header `Content-Type: application/json` setzen.

Die Rotation ist transportübergreifend: Ein per Body oder per Cookie erneuertes Refresh Token macht das jeweils vorherige Token auf **beiden** Transportwegen ungültig — es gibt nur eine Rotation, keine getrennte Buchführung je Transportweg.

### Sitzung eines gekoppelten Geräts beenden

!!! warning "Native Clients können `/auth/logout` nicht verwenden"
    `POST /api/v1/auth/logout` prüft den CSRF-Cookie und antwortet ohne ihn mit `403 Forbidden`. Ein gekoppeltes Gerät hat diesen Cookie nie besessen und kann sich darüber folglich nicht abmelden.

Ein gekoppeltes Gerät beendet seine Sitzung stattdessen über die reguläre Sitzungsverwaltung:

```http
DELETE /api/v1/users/me/sessions/{key}
Authorization: Bearer <access-token>
```

Alternativ genügt es, das gespeicherte Refresh Token auf dem Gerät zu verwerfen — die Sitzung läuft dann regulär nach 30 Tagen ab, ohne dass sie aktiv widerrufen wurde.

### Fehlerantworten

| Status | Bedeutung |
|--------|-----------|
| `401 Unauthorized` | „Invalid or expired pairing code." — gilt gleichermaßen für einen unbekannten, bereits eingelösten und einen abgelaufenen Code. Es gibt bewusst **keine** unterscheidbare Antwort, damit eine Anfrage nicht als Orakel für den Zustand eines Codes missbraucht werden kann. |
| `423 Locked` | Die Quelladresse ist wegen zu vieler fehlgeschlagener Einlöseversuche gesperrt; die Antwort nennt die verbleibende Sperrdauer in Minuten. Der zuletzt verwendete Code wird dabei **nicht** verbraucht — derselbe QR-Code kann nach Ablauf der Sperre erneut eingelöst werden, solange seine eigene (kurze) Gültigkeitsdauer noch nicht abgelaufen ist. |
| `429 Too Many Requests` | Das Rate Limit für den Einlöse-Endpunkt ist überschritten. |

### Sicherheitshinweise

!!! danger "Kopplungscode niemals im Klartext neben dem QR-Code anzeigen"
    Zeige den Kopplungscode ausschließlich als QR-Code an, niemals zusätzlich als lesbaren Text auf demselben Bildschirm — sonst genügt ein Blick über die Schulter, um sich als das gekoppelte Gerät auszugeben. Scanne außerdem **nur** einen QR-Code, den du selbst gerade erst erzeugt hast — ein fremder oder älterer QR-Code kann bereits verbraucht, abgelaufen oder manipuliert sein.

    Der Kopplungscode ist kurzlebig (60–120 Sekunden, konfigurierbar) und nur einmal einlösbar. Er ist **kein** Passwort und kein langlebiges Token — er dient ausschließlich dazu, einmalig ein reguläres Token-Paar auszustellen.

---

## Rollen und Berechtigungen

Nutzer können Mitglied mehrerer Mandanten sein und in jedem Mandanten eine eigene Rolle haben.

| Rolle | Beschreibung |
|-------|-------------|
| `viewer` | Lesezugriff auf alle Mandantenressourcen |
| `grower` | Lese- und Schreibzugriff auf Pflanzen, Durchläufe, Aufgaben |
| `admin` | Vollzugriff inklusive Mitgliederverwaltung und Einstellungen |

Die Rolle wird beim Zugriff auf mandantengebundene Endpunkte automatisch geprüft. Endpunkte mit erhöhten Anforderungen dokumentieren ihre Mindestrolle in der Swagger UI.

### Plattform-Admin

Der Plattform-Admin hat Zugriff auf die plattformweite Verwaltung unter `/api/v1/admin/`. Diese Rolle wird über die Mitgliedschaft im `platform`-Mandanten mit der Rolle `admin` gesteuert.

---

## Login-Schutz

Nach mehreren fehlgeschlagenen Login-Versuchen wird das Konto temporär gesperrt. Die API antwortet dann mit `423 Locked` und gibt die verbleibende Sperrdauer an:

```json
{
  "error_code": "ACCOUNT_LOCKED",
  "message": "Account temporarily locked. Try again in 15 minutes.",
  "details": [
    {
      "field": "account",
      "reason": "Too many failed login attempts. Locked for 15 minutes.",
      "code": "ACCOUNT_LOCKED"
    }
  ]
}
```

---

## Umgebungsvariablen (Authentifizierung)

| Variable | Standard | Beschreibung |
|----------|---------|--------------|
| `JWT_SECRET_KEY` | `change-me-...` | Signierschlüssel für JWTs — in Produktion mit `openssl rand -hex 32` generieren |
| `JWT_ALGORITHM` | `HS256` | Signierungsalgorithmus |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Gültigkeitsdauer des Access Tokens in Minuten |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Gültigkeitsdauer des Refresh Tokens in Tagen |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | E-Mail-Verifikation vor erstem Login erzwingen |
| `KAMERPLANTER_MODE` | `full` | `light` deaktiviert die gesamte Authentifizierung |
| `FERNET_KEY` | — | Verschlüsselungsschlüssel für OIDC-Provider-Secrets |

---

## Siehe auch

- [API-Überblick](overview.md) — URL-Struktur und Deployment-Modi
- [Fehlerbehandlung](error-handling.md) — Auth-spezifische Fehlercodes
