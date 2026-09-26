# Fehlerbehandlung

Alle API-Fehler folgen einem einheitlichen JSON-Format. Jede Fehlerantwort enthält eine eindeutige Fehler-ID, einen maschinenlesbaren Fehlercode, eine menschenlesbare Nachricht und ein `details`-Array für feldspezifische Validierungsfehler.

---

## Fehlerstruktur

```json
{
  "error_id": "err_f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "error_code": "ENTITY_NOT_FOUND",
  "message": "PlantInstance with key 'pi_xyz' not found.",
  "details": [
    {
      "field": "key",
      "reason": "No PlantInstance with key 'pi_xyz'.",
      "code": "ENTITY_NOT_FOUND",
      "entity": "plant_instance"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/plant-instances/pi_xyz",
  "method": "GET"
}
```

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `error_id` | String | Eindeutige UUID des Fehlerereignisses — für Support-Anfragen |
| `error_code` | String | Maschinenlesbarer Code (vollständige Liste unten) |
| `message` | String | Kurze Fehlerbeschreibung auf Englisch |
| `details` | Array | Feldspezifische Fehlerdetails (kann leer sein) |
| `details[].field` | String | Feldname oder Pfad zum fehlerhaften Wert |
| `details[].reason` | String | Erläuterung des konkreten Problems |
| `details[].code` | String | Maschinenlesbarer Detailcode |
| `details[].entity` | String | **Optional.** Name der fehlenden Ressource in `snake_case` aus einem geschlossenen Vokabular (`task`, `attachment`, `plant_instance`) — nur bei 404-Fehlern gesetzt |
| `timestamp` | String | Zeitpunkt des Fehlers (ISO 8601, UTC) |
| `path` | String | URL-Pfad der fehlgeschlagenen Anfrage |
| `method` | String | HTTP-Methode der fehlgeschlagenen Anfrage |

!!! tip "Zwei 404 auf derselben Route unterscheiden"
    Eine Route, die erst eine Eltern- und dann eine Kindressource auflöst, antwortet in beiden Fällen mit `ENTITY_NOT_FOUND` und HTTP 404. Unterschieden werden sie über `details[0].entity` — nicht über `message`, die auf Englisch formuliert und jederzeit umformulierbar ist. Ein Client, der das Feld nicht kennt, verhält sich wie bisher: `error_code` und Status sind unverändert.

!!! info "`entity` ist ein geschlossenes Vokabular"
    Der Wert ist immer der `snake_case`-Name **einer** Ressourcenart: ein Name je Modell, immer Singular (`tenant`, nie `tenants`; `plant_instance`, nie `plant_instances`). Er ist nie ein Speicher-/Collection-Name und nie ein Freitext. Neben den Modellnamen gibt es benannte Ausnahmen für Dinge, die kein Modell sind — darunter `storage_object` (Datei im Objektspeicher), `session` (Anmeldesitzung), `mcp_tool` und `resource` (Rückfall, wenn der Server die Art nicht benennen darf). Vergleichen Sie den Wert exakt; ein unbekannter Wert sollte wie „keine Angabe" behandelt werden.

!!! tip "error_id für Support nutzen"
    Die `error_id` wird im Server-Log protokolliert. Geben Sie diese ID bei der Fehlersuche oder in Support-Anfragen an — damit kann der Fehler serverseitig exakt nachvollzogen werden.

---

## HTTP-Statuscodes

| Code | Bedeutung | Wann |
|------|----------|------|
| `200 OK` | Erfolg | Lesende Anfragen (GET) |
| `201 Created` | Ressource erstellt | POST mit neuer Ressource |
| `204 No Content` | Erfolg ohne Body | DELETE |
| `400 Bad Request` | Fehlerhafte Anfrage | Syntaxfehler im Request-Body |
| `401 Unauthorized` | Nicht authentifiziert | Kein oder ungültiges Token |
| `403 Forbidden` | Keine Berechtigung | Authentifiziert, aber fehlende Rolle |
| `404 Not Found` | Ressource nicht gefunden | Unbekannte ID oder Slug |
| `409 Conflict` | Konflikt | Doppelter Eintrag oder ungültiger Zustandsübergang |
| `422 Unprocessable Entity` | Validierungsfehler | Fachliche Regeln verletzt (z.B. Karenzzeit) |
| `423 Locked` | Konto gesperrt | Zu viele fehlgeschlagene Loginversuche |
| `429 Too Many Requests` | Rate Limit überschritten | Zu viele Anfragen pro Minute |
| `502 Bad Gateway` | Externe Quelle nicht erreichbar | GBIF/Perenual-Timeout |
| `503 Service Unavailable` | Feature nicht konfiguriert | Instanz fehlt eine für die Aktion nötige Konfiguration |
| `500 Internal Server Error` | Interner Fehler | Unerwarteter Serverfehler |

---

## Fehlercodes

### Allgemeine Fehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `ENTITY_NOT_FOUND` | 404 | Die angeforderte Ressource existiert nicht |
| `DUPLICATE_ENTRY` | 409 | Ein Eintrag mit diesem Wert existiert bereits |
| `VALIDATION_ERROR` | 422 | Pydantic-Validierungsfehler (Typen, Pflichtfelder) |
| `INTERNAL_ERROR` | 500 | Unerwarteter interner Fehler |

### Authentifizierungs- und Autorisierungsfehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `UNAUTHORIZED` | 401 | Kein gültiges Token vorhanden |
| `INVALID_TOKEN` | 401 | Token abgelaufen oder manipuliert |
| `FORBIDDEN` | 403 | Authentifiziert, aber ohne ausreichende Rolle |
| `EMAIL_NOT_VERIFIED` | 403 | E-Mail-Adresse noch nicht bestätigt |
| `ACCOUNT_LOCKED` | 423 | Konto nach zu vielen Fehlversuchen gesperrt |
| `STEP_UP_LOCKED` | 429 | Zu viele fehlgeschlagene Bestätigungen bei einer unumkehrbaren Kontoaktion oder Anmeldemittel-Änderung (Konto- oder Mandantenlöschung, E-Mail- oder Passwortänderung, API-Key ausstellen, Gerät koppeln, Anmeldeweg entfernen, Admin-Vertrauensanhebung) — `details[0].retry_after_minutes` nennt die Wartezeit; betrifft nicht die Anmeldung |
| `STEP_UP_REAUTH_REQUIRED` | 401 (422 beim Anfordern des Codes) | Ein Konto mit einem OIDC-fähigen Anbieter (Google, generisches OIDC) muss sich für diese Aktion erneut bei diesem Anbieter anmelden — `POST /users/me/step-up/oidc` startet die Anmeldung; der per E-Mail zugeschickte Code wird diesem Konto verweigert |
| `STEP_UP_REAUTH_FAILED` | 401 | Die erneute Anmeldung beim Anbieter hat diese Aktion nicht bestätigt (abgelaufen, abgebrochen oder ungültig) — nur als Weiterleitungs-Fehlercode auf `/auth/step-up/callback`, nie als JSON |
| `STEP_UP_PASSWORD_REQUIRED` | 422 | Das Konto hat ein lokales Passwort und bestätigt damit — weder erneute Anmeldung noch E-Mail-Code sind nötig. |
| `STEP_UP_REAUTH_UNAVAILABLE` | 422 | Keiner der verknüpften Anbieter des Kontos (bzw. der gewählte) kann eine frische Anmeldung nachweisen — das Konto bestätigt mit dem E-Mail-Code. |
| `STEP_UP_CODE_REQUIRED` | 401 | Ein Konto ohne lokales Passwort und ohne OIDC-fähigen Anbieter (nur GitHub/Apple) hat für eine dieser Aktionen keinen Bestätigungscode mitgeschickt — zuerst per `POST /users/me/step-up-code` anfordern |
| `STEP_UP_CODE_UNDELIVERABLE` | 503 | Der Bestätigungscode konnte nicht per E-Mail zugestellt werden (kein E-Mail-Versand konfiguriert oder Mailserver-Fehler); es wurde nichts ausgegeben — die Wartezeit und das Stundenkontingent bleiben unberührt, ein erneuter Versuch ist sofort möglich, sobald der Betreiber den Versand behoben hat |

### Phasen- und Statusfehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `PHASE_TRANSITION_INVALID` | 422 | Ungültiger Übergang im Phasenstatus (z.B. Rückwärtsübergang) |
| `INVALID_STATUS_TRANSITION` | 422 | Ungültiger Statuswechsel eines Objekts |
| `INVALID_RUN_STATE` | 409 | Operation im aktuellen Zustand nicht erlaubt |

### Pflanzenschutz- und Erntefehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `KARENZ_VIOLATION` | 422 | Ernte nicht möglich — Karenzzeit noch nicht abgelaufen |
| `RESISTANCE_WARNING` | 422 | Resistenzrisiko — Wirkstoff zu oft in Folge eingesetzt |
| `HST_VIOLATION` | 422 | Trainingsmaßnahme (HST) in dieser Phase nicht erlaubt |

### Substrat- und Kompatibilitätsfehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `SUBSTRATE_EXHAUSTED` | 422 | Substratcharge hat maximale Wiederverwendungszyklen überschritten |
| `ROTATION_VIOLATION` | 422 | Pflanzenfamilie wurde zu kürzlich in diesem Slot angebaut |
| `INCOMPATIBLE_COMPANION` | 422 | Zwei Pflanzenarten sind als Mischkultur unverträglich |

### Externe Dienste

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `EXTERNAL_SOURCE_ERROR` | 502 | Externer Datendienst (GBIF, Perenual) nicht erreichbar |
| `ADAPTER_NOT_FOUND` | 404 | Kein Adapter für die angegebene Quelle registriert |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate Limit des Servers oder eines externen Dienstes überschritten |

### DSGVO- und Löschfehler

| Fehlercode | HTTP | Beschreibung |
|-----------|------|-------------|
| `ERASURE_INCOMPLETE` | 500 | Eine sofortige Konto-Löschung (Platform-Admin, Aufräumlauf für nie bestätigte Konten) hat einen Schritt nicht erreicht; der Löschantrag ist gespeichert und wird automatisch wiederholt |
| `TENANT_ERASURE_INCOMPLETE` | 500 | Eine Mandantenlöschung hat etwas nicht erreicht, das den Mandanten noch hält (nur Sammlungsnamen in der Meldung, keine Mandanten- oder Kontokennung); der Vorgang ist gespeichert und wird automatisch wiederholt |
| `WRITE_CONFLICT` | 409 | Für dieses Konto oder diesen Mandanten läuft bereits eine Löschung |
| `FEATURE_NOT_CONFIGURED` | 503 | Die Instanz ist für Konto- oder Mandanten-Löschungen nicht korrekt konfiguriert; es wurde nichts geändert |

---

## Validierungsfehler (422)

FastAPI und Pydantic erzeugen bei Eingabefehler automatisch strukturierte Validierungsfehler. Die `details`-Liste enthält für jedes fehlerhafte Feld einen eigenen Eintrag:

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "kein-gueltige-email",
  "password": "kurz",
  "display_name": ""
}
```

**Antwort (422):**

```json
{
  "error_id": "err_b5e3c8a1-...",
  "error_code": "VALIDATION_ERROR",
  "message": "The input data is invalid.",
  "details": [
    {
      "field": "body.email",
      "reason": "value is not a valid email address",
      "code": "value_error"
    },
    {
      "field": "body.password",
      "reason": "String should have at least 10 characters",
      "code": "string_too_short"
    },
    {
      "field": "body.display_name",
      "reason": "String should have at least 1 character",
      "code": "string_too_short"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/auth/register",
  "method": "POST"
}
```

---

## Karenz-Violation (KARENZ_VIOLATION)

Der Karenz-Gate-Mechanismus verhindert die Erstellung einer Ernte, solange die Karenzzeit eines angewendeten Pflanzenschutzmittels noch nicht abgelaufen ist.

```http
POST /api/v1/t/mein-garten/harvest/batches
```

**Antwort (422), wenn Karenzzeit aktiv:**

```json
{
  "error_id": "err_c7d2e5f3-...",
  "error_code": "KARENZ_VIOLATION",
  "message": "Cannot harvest: safety interval for 'Pyrethrin' has 5 days remaining.",
  "details": [
    {
      "field": "active_ingredient",
      "reason": "Safety interval not elapsed: 5 days remaining.",
      "code": "KARENZ_VIOLATION"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/mein-garten/harvest/batches",
  "method": "POST"
}
```

!!! danger "Karenzzeit ist rechtlich relevant"
    Die Karenzzeit (Pre-Harvest Interval) zwischen letzter Pflanzenschutzmittel-Anwendung und Ernte ist gesetzlich vorgeschrieben (PflSchG/CanG). Dieser Fehler darf clientseitig nicht ignoriert werden.

---

## Konflikte (409)

HTTP 409 wird verwendet, wenn eine Operation aufgrund des aktuellen Zustands nicht durchführbar ist — etwa das Hinzufügen einer Pflanze zu einem bereits abgeschlossenen Durchlauf:

```json
{
  "error_id": "err_a1b2c3d4-...",
  "error_code": "INVALID_RUN_STATE",
  "message": "Operation 'add_plant' not allowed in status 'completed'.",
  "details": [],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/mein-garten/planting-runs/run_123/plants",
  "method": "POST"
}
```

---

## Rate Limiting (429)

Bei Überschreitung des Rate Limits antwortet die API mit HTTP 429. Der `Retry-After`-Header gibt an, nach wie vielen Sekunden ein erneuter Versuch möglich ist:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

```json
{
  "error": "Rate limit exceeded: 20 per 1 minute"
}
```

---

## Interne Fehler (500)

Bei unerwarteten internen Fehlern gibt die API niemals Details über die serverseitige Ursache preis. Die `error_id` ist das einzige Instrument zur Fehlerkorrelation:

```json
{
  "error_id": "err_9f8e7d6c-...",
  "error_code": "INTERNAL_ERROR",
  "message": "An internal error occurred. Please contact support with the reference ID.",
  "details": [],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/mein-garten/plant-instances/",
  "method": "GET"
}
```

---

## Empfehlungen für API-Clients

- **Fehlercode auswerten, nicht nur den HTTP-Statuscode.** Mehrere semantisch unterschiedliche Fehler können denselben Statuscode haben (z.B. sind `KARENZ_VIOLATION`, `HST_VIOLATION` und `ROTATION_VIOLATION` alle HTTP 422).
- **`error_id` protokollieren.** In eigenen Logs und bei Support-Anfragen immer die `error_id` angeben.
- **`details`-Array iterieren** für feldspezifische Fehlermeldungen in Formularvalidierungen.
- **Auf `401` mit Token-Refresh reagieren.** Nach Ablauf des Access Tokens (15 min) liefert die API `401 UNAUTHORIZED`. Der Client soll automatisch einen Refresh-Versuch starten.
- **`409 INVALID_RUN_STATE` nicht wiederholen.** Dieser Fehler zeigt einen fachlichen Zustandskonflikt an — die Operation ist erst nach einer Zustandsänderung möglich.

---

## Siehe auch

- [API-Überblick](overview.md) — URL-Struktur und Endpunkt-Gruppen
- [Authentifizierung](authentication.md) — Auth-Fehler im Detail
- [IPM-System](../user-guide/pest-management.md) — Karenzzeit-Konzept erklärt
