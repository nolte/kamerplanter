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

## Passwort ändern (angemeldet)

```http
POST /api/v1/users/me/password
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "current_password": "altes-passwort-2026",
  "new_password": "neues-passwort-2026"
}
```

`current_password` entfällt nur, wenn das Konto noch **kein** lokales Passwort hat (ein reines SSO-Konto, das erstmals eines setzt) — in diesem Fall bestätigst du stattdessen mit einer frischen Anmeldung beim verknüpften Anbieter (nächster Abschnitt) oder, nur wenn all deine Anbieter das nicht unterstützen (GitHub, Apple), mit dem Bestätigungscode aus dem übernächsten Abschnitt. Existiert bereits ein lokales Passwort, muss es korrekt mitgeschickt werden — es ist ein Step-up (siehe unten). Bei Erfolg werden alle aktiven Sitzungen des Nutzers beendet.

Eine mit API-Key authentifizierte Anfrage wird mit `403 Forbidden` abgelehnt — ein API-Key kann das eigene Passwort nicht ändern.

Im Light-Modus (`KAMERPLANTER_MODE=light`) antwortet die Route mit `403 Forbidden`. Das einzige Konto der Instanz wird von jeder Anfrage ohne Anmeldung benutzt; ein dort gesetztes Passwort sagt nichts darüber, wer es gesetzt hat — und es würde nach dem Wechsel in den Full-Modus zur gültigen Anmeldung.

---

## Erneut anmelden zur Bestätigung (OIDC)

Ein Konto ohne lokales Passwort hat kein eigenes Geheimnis, mit dem es die Step-up-Bestätigungen im übernächsten Abschnitt beantworten könnte. Ist mindestens einer seiner verknüpften Anmeldeanbieter ein **OpenID-Connect-Anbieter** (Google oder ein generischer OIDC-Provider mit dem `openid`-Scope), bestätigt es stattdessen mit einer **frischen** Anmeldung genau bei diesem Anbieter — das ist der Regelfall. Nur ein Konto, dessen sämtliche verknüpfte Anbieter das nicht können (ausschließlich GitHub und/oder Apple, siehe Abgrenzung unten), weicht auf den per E-Mail zugeschickten Code aus.

```http
POST /api/v1/users/me/step-up/oidc
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "action": "account_erasure"
}
```

`action` benennt wie beim Code die zu bestätigende Aktion. Optional `provider_key` (Schlüssel eines verknüpften Anbieters aus `GET /users/me/providers`) wählt einen bestimmten Anbieter, wenn mehrere OIDC-fähige verknüpft sind; ohne Angabe nimmt die Route den ersten passenden. Optional `client_nonce` (32 Hex-Zeichen, vom Client zufällig erzeugt) kommt unverändert neben dem Token bzw. dem Fehler zurück — so erkennt die Seite, die die Anmeldung gestartet hat, ihr eigenes Ergebnis und verwirft ein untergeschobenes.

**Antwort (200 OK):**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=kamerplanter&response_type=code&prompt=login&max_age=0&state=…&nonce=…&code_challenge_method=S256"
}
```

Öffne `authorization_url` im Browser — dieselbe Login-Anfrage wie beim normalen Anmelden, zusätzlich mit `prompt=login` und `max_age=0`: Der Anbieter muss die Person erneut anmelden lassen (keine stille Antwort aus dessen eigener Sitzung) und den Anmeldezeitpunkt zurückmelden. Der Anbieter leitet danach an den bestehenden Callback dieses Servers weiter; der meldet niemanden an, sondern leitet ohne Umweg über eine JSON-Antwort direkt zu `{frontend-url}/auth/step-up/callback` weiter:

- Erfolg: `#step_up_token=<Token>&action=<Aktion>&client_nonce=<Nonce>` im URL-**Fragment** (nie in der Query — ein Fragment erreicht keinen Server, keinen Proxy und keinen `Referer`-Header)
- Fehler: `?error=step_up_failed` (allgemein), `?error=step_up_stale` (die Anmeldung war älter als fünf Minuten — erneut versuchen), oder `?error=step_up_cancelled` (am Anbieter abgebrochen)

Das Backend prüft dabei am ID-Token: `iss` ist der erwartete Aussteller, `aud`/`azp` ist diese Instanz, `nonce` stimmt mit der Anfrage überein, `exp` ist nicht abgelaufen, `sub` gehört zu einer verknüpften Anmeldung **dieses** Kontos, die über **genau diese** Anbieter-Konfiguration entstanden ist (die Verknüpfung speichert Konfiguration und Aussteller; `iss` muss dazu passen), und `auth_time` ist eine endliche Zahl und höchstens fünf Minuten alt (30 Sekunden Uhrtoleranz). Eine ältere Verknüpfung ohne gespeicherte Konfiguration gilt nur dann als re-authentifizierbar, wenn genau eine aktive, fähige Konfiguration dieses Typs existiert — sonst bestätigt das Konto mit dem E-Mail-Code. Es prüft **keine** JWKS-Signatur: Das ID-Token kommt direkt vom Token-Endpunkt des Anbieters über TLS (die frische Anmeldung wird nur bei einem `https`-Token-Endpunkt angeboten), in einem Austausch, den dieser Server mit seinem eigenen Client-Secret authentifiziert hat — genau der Fall, für den OIDC Core 3.1.3.7 Nr. 6 die TLS-Absicherung als Ersatz für die Signaturprüfung vorsieht.

Der zurückgegebene `step_up_token` ist fünf Minuten gültig, gilt für genau die angeforderte Aktion, wird durch die erste Aktion verbraucht, die ihn vorlegt, und ist ansonsten wie der E-Mail-Code zu verwenden: als `step_up_token` im Bestätigungs-Body der jeweiligen Aktion (siehe Tabelle unten).

`403 Forbidden` für eine mit API-Key authentifizierte Anfrage, einen Service Account oder eine Light-Modus-Installation. `422 Unprocessable Entity`: `STEP_UP_PASSWORD_REQUIRED`, wenn das Konto ein lokales Passwort hat (es bestätigt damit); `STEP_UP_REAUTH_UNAVAILABLE`, wenn keiner seiner verknüpften Anbieter (bzw. der über `provider_key` gewählte) eine frische Anmeldung unterstützt — dann bestätigt es mit dem E-Mail-Code —; ein Validierungsfehler, wenn `action` fehlt/unbekannt oder `client_nonce` falsch geformt ist. `429 Too Many Requests` (`STEP_UP_LOCKED`), solange der Step-up gesperrt ist.

!!! info "Betreiber-Voraussetzung"
    Der verknüpfte Identity-Provider muss `prompt=login`/`max_age` sowie den Claim `auth_time` unterstützen (Google und die meisten generischen OIDC-Provider tun das) und seinen Token-Endpunkt über `https` anbieten. Die Rückruf-URL der erneuten Anmeldung wird aus `APP_BASE_URL` gebildet (`{APP_BASE_URL}/api/v1/auth/oauth/{slug}/callback`), nie aus dem Host-Header der Anfrage — setze `APP_BASE_URL` auf die öffentliche Adresse und hinterlege genau diese Rückruf-URL beim Provider.

---

## Bestätigungscode per E-Mail anfordern (Ausweichweg für GitHub/Apple)

**Abgrenzung.** GitHub ist reines OAuth2 und stellt kein ID-Token aus — es gibt also keinen Anmeldezeitpunkt, den der vorige Abschnitt prüfen könnte. Apple stellt zwar ein ID-Token aus, aber ohne `auth_time`. Ein Konto, dessen verknüpfte Anmeldewege **ausschließlich** aus GitHub und/oder Apple bestehen, kann sich deshalb nicht frisch erneut anmelden lassen und bestätigt stattdessen mit einem Einmalcode, der an die eigene E-Mail-Adresse geschickt wird — derselbe Nachweis, auf den sich ein Passwort-Reset stützt. Ein Konto mit mindestens einem OIDC-fähigen Anbieter (Google, generisches OIDC) nutzt immer den vorigen Abschnitt; die Route unten verweigert ihm den Code (siehe unten).

```http
POST /api/v1/users/me/step-up-code
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "action": "account_erasure"
}
```

`action` benennt, wofür der Code gelten soll: `account_erasure`, `admin_account_erasure`, `tenant_deletion`, `password_change` oder `email_change`. Der Code bestätigt **ausschließlich** diese eine Aktion — ein für die Passwortänderung angeforderter Code wird bei einem Löschversuch abgelehnt, ohne dabei verbraucht zu werden. Die zugeschickte E-Mail nennt in Klartext, wofür der Code gilt.

**Antwort (202 Accepted):**

```json
{
  "expires_at": "2026-09-25T18:40:00Z",
  "expires_in": 600
}
```

Der Code besteht aus acht Ziffern, ist zehn Minuten gültig und wird durch die erste Aktion verbraucht, die ihn vorlegt; ein erneuter Aufruf ersetzt einen noch gültigen Code durch einen neuen — mit zwei Ausnahmegrenzen: Ein **noch nicht verbrauchter** Code jünger als 60 Sekunden wird nicht ersetzt (sonst würde eine erneute Anfrage den Code entwerten, den die Person gerade abtippt), und es werden höchstens **5 Codes pro Stunde und Konto** verschickt. Der Code wird ausschließlich an die E-Mail-Adresse des eigenen Kontos verschickt — niemals in dieser Antwort oder anderswo zurückgegeben.

`403 Forbidden` für eine mit API-Key authentifizierte Anfrage, einen Service Account oder eine Light-Modus-Installation (dort gibt es kein persönliches Konto, das etwas bestätigen könnte). `422 Unprocessable Entity`: `STEP_UP_PASSWORD_REQUIRED`, wenn das Konto bereits ein lokales Passwort hat — es bestätigt damit, nicht mit einem Code —; `STEP_UP_REAUTH_REQUIRED`, **wenn mindestens ein verknüpfter Anbieter des Kontos OIDC-fähig ist** (siehe oben — die Route sagt dann, den vorigen Abschnitt zu nutzen); ein Validierungsfehler, wenn `action` fehlt oder keiner der oben genannten Werte ist. `429 Too Many Requests` (`STEP_UP_LOCKED`, `details[0].retry_after_minutes`), solange der Step-up des Kontos gesperrt ist, ein noch gültiger Code jünger als 60 Sekunden ist, oder das Stundenbudget an Codes ausgeschöpft ist.

`503 Service Unavailable` (`STEP_UP_CODE_UNDELIVERABLE`), wenn der Code nicht per E-Mail zugestellt werden kann — zum Beispiel, weil die Instanz ohne konfigurierten E-Mail-Versand läuft, oder der Mailserver einen Fehler meldet. In diesem Fall wird nichts ausgegeben: Der Code wird verworfen und sein Kontingent zurückgegeben, sodass weder die 60-Sekunden-Wartezeit noch das Stundenbudget den nächsten Versuch blockieren, sobald der Betreiber den Versand behoben hat.

---

## Step-up-Bestätigung für unumkehrbare Kontoaktionen und Anmeldemittel

Neun Aktionen verlangen zusätzlich zum gültigen Access Token eine erneute Bestätigung durch die angemeldete Person — seit Version 1.19 auch das Ausstellen bzw. Entfernen von Anmeldemitteln und eine Vertrauensanhebung durch Plattform-Admins: <!-- #1847, #1857 -->

| Aktion | Route(n) | Zurückgetipptes Ziel (Body-Feld) | Passwort / Erneute Anmeldung / Code |
|---|---|---|---|
| Eigenes Konto löschen (Art. 17 DSGVO) | `DELETE /users/me`, `POST /privacy/erasure` | eigene E-Mail (`confirm_email`) | eigenes Passwort, sofern lokal vorhanden — sonst `step_up_token` einer frischen Anmeldung, nur bei rein GitHub/Apple der per E-Mail zugeschickte Code (`step_up_code`) |
| Anderes Konto löschen (Plattform-Admin) | `DELETE /admin/platform/users/{key}` | E-Mail des Zielkontos (`confirm_email`) | das des Admins, sonst dessen `step_up_token` bzw. Code |
| Mandant löschen | `DELETE /tenants/{slug}`, `DELETE /admin/platform/tenants/{key}` | Slug (`confirm_slug`) | eigenes Passwort, sonst `step_up_token` bzw. Code |
| E-Mail-Adresse ändern | `POST /privacy/email-change` | — | eigenes Passwort, sonst `step_up_token` bzw. Code |
| Passwort ändern | `POST /users/me/password` | — | aktuelles (`current_password`) — die **erste** Passwortvergabe eines Kontos ohne eines läuft stattdessen über `step_up_token` bzw. Code |
| API-Key ausstellen | `POST /auth/api-keys` | — | eigenes Passwort, sonst `step_up_token` bzw. Code. **Light-Modus:** kein Step-up — die Instanz hat nur das eine Systemkonto |
| Gerät per QR-Code koppeln | `POST /auth/device-pairing` | — | eigenes Passwort, sonst `step_up_token` bzw. Code |
| Anmeldeweg (Provider-Verknüpfung) entfernen | `DELETE /users/me/providers/{provider_key}` | — | eigenes Passwort, sonst `step_up_token` bzw. Code |
| Vertrauen eines anderen Kontos anheben (Plattform-Admin) | `PATCH /admin/platform/users/{key}`, nur wenn `email_verified` oder `is_active` von `false` auf `true` wechselt | — | das des Admins, sonst dessen `step_up_token` bzw. Code |

!!! info "Kein automatischer Widerruf von API-Keys"
    Passwortänderung, Passwort-Reset und `POST /auth/logout-all` widerrufen die Refresh-Token des Kontos — **nicht** dessen API-Keys. Ein Key steht für eine bewusst eingerichtete Maschinen-Integration (Home Assistant, MCP-Client); ihn bei jeder Passwortänderung stillschweigend zu entwerten, würde diese Integrationen ohne Vorwarnung brechen. Ein Key kann seit dieser Version nur noch hinter diesem Step-up entstehen — also nicht mehr aus einer bloß gestohlenen Sitzung oder aus einem anderen Key. Keys sind unter `GET /auth/api-keys` mit Erstellungs- und letztem Nutzungszeitpunkt gelistet und einzeln über `DELETE /auth/api-keys/{key_id}` widerrufbar. <!-- #1847 -->

Eine mit einem API-Key authentifizierte Anfrage oder eine Anfrage eines Service Accounts kann keine dieser neun Aktionen auslösen — auch nicht das Ausstellen eines weiteren API-Keys oder eines Kopplungscodes (siehe Prüfreihenfolge unten).

Beispiel-Body für die Kontolöschung (lokales Konto):

```json
{
  "confirm_email": "gartner@example.com",
  "password": "aktuelles-passwort-2026"
}
```

Beispiel-Body nach einer frischen Anmeldung (OIDC-fähiges Konto):

```json
{
  "confirm_email": "gartner@example.com",
  "step_up_token": "AqX7…"
}
```

Beispiel-Body für ein Konto, das ausschließlich über GitHub/Apple angemeldet ist:

```json
{
  "confirm_email": "gartner@example.com",
  "step_up_code": "48213907"
}
```

**Prüfreihenfolge:**

1. Eine Anfrage mit API-Key oder von einem Service Account wird mit `403 Forbidden` abgelehnt — bevor irgendetwas geprüft oder gezählt wird.
2. Ist die Bestätigung gesperrt (siehe unten), antwortet die Route sofort `429 Too Many Requests`, ohne das Geheimnis zu prüfen.
3. Stimmt das zurückgetippte Ziel nicht (E-Mail ohne Groß-/Kleinschreibung, Slug exakt), antwortet die Route `422 Unprocessable Entity`. Ein falsches Echo zählt **nicht** als Fehlversuch. Die E-Mail-Änderung und die Passwortänderung haben kein Ziel zum Zurücktippen.
4. Hat das betroffene Konto ein lokales Passwort, muss das Passwortfeld korrekt gesetzt sein, sonst `401 Unauthorized`. Sonst — trägt der Body ein `step_up_token`, prüft die Route dieses (bestätigt es nichts oder ist es abgelaufen: `401 Unauthorized`). Fehlt `step_up_token`: Hat das Konto einen OIDC-fähigen verknüpften Anbieter, antwortet die Route `401 Unauthorized` mit dem Fehlercode `STEP_UP_REAUTH_REQUIRED` — ein Hinweis, sich zuerst erneut anzumelden. Andernfalls (nur GitHub/Apple verknüpft) prüft die Route stattdessen `step_up_code`; fehlt der, antwortet sie `401 Unauthorized` mit `STEP_UP_CODE_REQUIRED`.

**Drosselung:** Nach 5 falschen Bestätigungen (Passwort, Code oder eine ungültige/abgelaufene erneute Anmeldung) derselben Kombination aus Konto und Client-Adresse sperrt das System weitere Bestätigungen für **15 Minuten**; bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis auf **4 Stunden**. Zusätzlich gilt eine kontoweite Obergrenze von 15 Fehlversuchen über beliebig viele Client-Adressen hinweg. Alle fünf Aktionen — und das Anfordern eines Codes oder einer erneuten Anmeldung — teilen sich dasselbe Fehlversuchs-Budget je Konto; ein erfolgreicher Step-up leert es wieder.

Eine gesperrte Bestätigung antwortet mit dem Fehlercode `STEP_UP_LOCKED`:

```json
{
  "error_code": "STEP_UP_LOCKED",
  "message": "Too many failed confirmations. Try again in 15 minutes.",
  "details": [
    {
      "field": "password",
      "reason": "Too many failed confirmations.",
      "code": "STEP_UP_LOCKED",
      "retry_after_minutes": 15
    }
  ]
}
```

!!! note "Die Login-Sperre bleibt unberührt"
    Diese Sperre betrifft ausschließlich die fünf oben genannten Bestätigungen und wirkt sich nicht auf `POST /auth/login` aus. Wer eine dieser Bestätigungen sperrt — etwa jemand mit einer gestohlenen Sitzung —, kann sich trotzdem weiterhin anmelden, Sitzungen im Tab **Sitzungen** beenden und das Passwort per E-Mail zurücksetzen.

!!! info "Für Betreiber: zwei verschiedene Voraussetzungen"
    Ein Konto mit einem OIDC-fähigen Anbieter (Google, generisches OIDC) bestätigt über die erneute Anmeldung — dafür muss dieser Anbieter `prompt=login`/`max_age` und `auth_time` unterstützen (siehe oben), nicht SMTP. Nur ein Konto, dessen verknüpfte Anbieter ausschließlich GitHub und/oder Apple sind, braucht den per E-Mail zugeschickten Code und damit funktionierenden Mail-Versand: Läuft die Instanz mit dem Konsolen-E-Mail-Adapter und ohne Debug-Modus — die produktive Voreinstellung ohne konfiguriertes SMTP —, wird der Code nirgends zugestellt und ein solches Konto kann sich dann nicht löschen, keinen Mandanten löschen, kein erstes lokales Passwort setzen und die E-Mail-Adresse nicht ändern. Details zur Konfiguration unter [Umgebungsvariablen](../reference/environment-variables.md#e-mail).

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
  "tenant_scope": "mein-garten",
  "current_password": "aktuelles-passwort-2026"
}
```

`tenant_scope` ist optional und nimmt beim Anlegen den Slug **oder** den Key des Tenants entgegen. In beiden Fällen musst du im genannten Tenant aktives Mitglied sein — sonst antwortet die Route mit `403 Forbidden` ("tenant_scope must name a tenant you are an active member of."), und zwar mit derselben Meldung für einen unbekannten wie für einen fremden Tenant.

!!! info "Ausstellen ist ein Step-up"
    Statt `current_password` kannst du auch `step_up_token` (nach einer frischen Anmeldung, siehe [Erneut anmelden zur Bestätigung](#erneut-anmelden-zur-bestatigung-oidc)) oder `step_up_code` (nach [Bestätigungscode anfordern](#bestatigungscode-per-e-mail-anfordern-ausweichweg-fur-githubapple)) mitschicken — dieselben Regeln wie in der [Step-up-Tabelle](#step-up-bestatigung-fur-unumkehrbare-kontoaktionen-und-anmeldemittel) oben. Eine mit einem API-Key authentifizierte Anfrage antwortet `403 Forbidden`, bevor überhaupt ein Passwort geprüft wird — ein Key kann sich also nicht selbst vermehren. **Im Light-Modus** stellt diese Route den einen MCP-Key der Instanz ohne Step-up aus. <!-- #1847 -->

**Antwort (201 Created):**

```json
{
  "key": "apk_xyz789",
  "label": "Home Assistant Integration",
  "raw_key": "kp_sk_abc...xyz",
  "key_prefix": "kp_sk_abc",
  "tenant_scope": "t-a1b2c3d4",
  "created_at": "2026-03-17T10:00:00Z"
}
```

Gespeichert und zurückgegeben wird immer der **Key** des Tenants, nicht der beim Anlegen eingegebene Slug. Dadurch ändert ein späteres Umbenennen des Tenants (neuer Slug) nichts am Scope, und ein Löschen des Tenants löscht den Key gleich mit.

!!! danger "Raw Key nur einmal sichtbar"
    Das Feld `raw_key` wird nur bei der Erstellung angezeigt und danach nicht mehr ausgegeben. Speichern Sie den Key sofort an einem sicheren Ort.

### API-Key verwenden

```http
GET /api/v1/t/mein-garten/plant-instances/
Authorization: Bearer kp_sk_abc...xyz
```

Der API-Key wird im selben `Authorization`-Header wie ein JWT verwendet.

Ein Key mit `tenant_scope` handelt nur in diesem Tenant. Auf jeder Route unter `/api/v1/t/{slug}/` und auf jeder Route, die den Header `X-Active-Tenant` liest, antwortet ein anderer Tenant mit `403 Forbidden` — auch wenn der Besitzer des Keys dort Mitglied ist — und zwar mit derselben Antwort wie ein Tenant, in dem der Besitzer nicht Mitglied ist. Ohne den Header fällt ein begrenzter Key nur dann auf deinen persönlichen Tenant zurück, wenn dieser sein Scope ist; sonst sieht er nur den gemeinsamen Katalog. Der Abgleich erfolgt dabei ausschließlich über den gespeicherten Tenant-Key (siehe oben).

### IP-Allowlist und Rate Limit je Key

Ein API-Key kann zusätzlich eine CIDR-Allowlist und ein eigenes Anfragen-Limit pro Minute tragen. Beide Einschränkungen gelten identisch für die REST-API und für den [MCP-Server](mcp-server.md) — es gibt **ein** gemeinsames Budget je Key, keine getrennte Zählung je Schnittstelle.

- Liegt die Client-Adresse außerhalb der Allowlist oder lässt sie sich nicht auflösen, antwortet die API mit `401 Unauthorized` ("Client IP is not permitted for this API key.") — derselben Meldung, die auch der MCP-Server dafür gibt.
- Ist das Minutenbudget aufgebraucht, antwortet die API mit `429 Too Many Requests`. Dieselbe Antwort gibt es, wenn der Zähler-Speicher selbst nicht erreichbar ist — ein Ausfall des Zähler-Speichers wird nie als "kein Limit" gewertet.

### Kontoweite Routen und ein begrenzter Key

Ein Key mit `tenant_scope` ist auf genau einen Tenant beschränkt. Auf Routen, die keinen Tenant auflösen — etwa die eigenen Kontodaten (`PATCH`/`DELETE /users/me`, Passwort, Sitzungen, verknüpfte Provider), die [Datenschutz-Endpunkte](../user-guide/privacy.md), die Verwaltung der API-Keys selbst, die Gerätekopplung, `POST /auth/logout-all` oder das Anlegen bzw. Beitreten eines neuen Tenants — antwortet er deshalb mit `403 Forbidden` ("This API key is restricted to one tenant and cannot act on the account."). Dieselbe Antwort gibt es auf den wenigen Routen unter `/t/{slug}/`, die trotz Tenant im Pfad deine **kontoweiten** Einstellungen ändern: Benachrichtigungs-Einstellungen und Web-Push-Abos, Benutzer-Einstellungen, der Onboarding-Status und das Entfernen eines Favoriten. Sie gelten für alle deine Tenants, nicht nur für den des Scopes. Zugelassen bleiben: `GET /users/me` (die eigene Identitätsabfrage), `GET /tenants` (zeigt dann nur den einen Tenant des Scopes) sowie alle übrigen Routen, die einen Tenant auflösen (`/t/{slug}/`, `X-Active-Tenant`) — dort bindet weiterhin der Scope. Ein Key ohne `tenant_scope` ist von dieser Einschränkung nicht betroffen.

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
Content-Type: application/json

{
  "current_password": "aktuelles-passwort-2026"
}
```

!!! info "Anfordern ist ein Step-up"
    Wie beim Ausstellen eines API-Keys kannst du statt `current_password` auch `step_up_token` oder `step_up_code` mitschicken (siehe [Step-up-Tabelle](#step-up-bestatigung-fur-unumkehrbare-kontoaktionen-und-anmeldemittel) oben). Eine mit einem API-Key authentifizierte Anfrage antwortet `403 Forbidden` — ein Key kann sich damit keine vollständige Sitzung selbst ausstellen. <!-- #1847 -->

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

!!! note "Light-Modus: Instanz-Erkennung als App-Link-URL"
    Im Light-Modus (`KAMERPLANTER_MODE=light`) gibt es keine Konten, und die Kopplungs-Endpunkte antworten mit `404`. Das Web-Frontend zeigt dort trotzdem einen QR-Code an — allerdings **keine** JSON-Nutzlast, sondern eine **reine App-Link-URL** ohne Kopplungscode, die auf einen festen Deep-Link-Pfad der aufgerufenen Instanz zeigt:

    ```text
    https://garten.example.org/connect?v=1
    ```

    Der Wert ist ein **einfacher URL-String**, kein JSON-Blob. Das ist der entscheidende Unterschied zu #1118 P12: Die System-Kamera eines Smartphones erkennt eine JSON-Zeichenkette nicht als etwas Öffenbares, eine `https`-URL dagegen als Link. Die URL entsteht rein im Frontend aus `window.location.origin` (der Adresse, über die der Nutzer die Instanz tatsächlich erreicht), enthält kein Credential, ruft keinen Endpunkt auf und meldet niemanden an — sie dient ausschließlich der Instanz-Erkennung. Das Query-Feld `v=1` teilt sich denselben Versionsraum wie das `v` der Kopplungs-Payload, sodass die App eine ihr unbekannte Version ablehnen kann.

#### App-Erkennungs-Kontrakt für den Discovery-Link

Der Discovery-Link ist bewusst als **unverifizierter Deep Link** ausgelegt. Die künftige Kamerplanter-Android-App deklariert dazu einen `intent-filter` mit **Wildcard-Host** (`android:host="*"`) auf dem festen Pfad `/connect`, sodass sie `https://<beliebige-instanz>/connect` abfängt:

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="*" android:pathPrefix="/connect" />
</intent-filter>
```

- **Warum keine verifizierten App Links?** Automatisch verifizierte Android App Links binden über `assetlinks.json` an **feste, im Manifest deklarierte Domains**. Kamerplanter wird jedoch selbst gehostet — jede Instanz hat ihre eigene, im Voraus unbekannte Domain. Über beliebige selbstgehostete Domains hinweg ist eine Auto-Verifizierung daher **nicht möglich**. Der Kontrakt ist deshalb ein **unverifizierter** Deep Link mit Wildcard-Host: Android zeigt beim Öffnen einen App-Auswahldialog (bzw. öffnet direkt, sobald der Nutzer die App als Standard gesetzt hat).
- **Browser-Fallback:** Ist die App nicht installiert, öffnet die System-Kamera die URL im Browser. Der Pfad `/connect` rendert dort eine schlanke Landing-Seite („In der Kamerplanter-App öffnen" bzw. „Im Browser fortfahren"), damit der Link nie ins Leere (404) läuft. Die Seite liegt außerhalb des Auth-Guards und der Modus-Weiche, funktioniert also in Light- **und** Full-Modus.
- **Der Kopplungs-QR bleibt bewusst undurchsichtig:** Der Login-/Kopplungs-QR (`{"v","url","code"}`, siehe oben) bleibt **opakes JSON und ausschließlich in-App scanbar**. Er wird bewusst **nicht** zu einem Deep Link, weil sein `code` ein Einmal-Credential ist: Als System-Kamera-öffenbarer Link könnte er abgefangen und an eine fremde App geroutet werden. Nur der credential-freie Discovery-Link darf eine öffentlich erkennbare URL sein.

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
