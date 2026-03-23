---
req_id: NFR-006
title: Strukturierte API-Fehlerbehandlung mit eindeutiger Tracking-ID
category: API-Design / Error Handling / Observability
test_count: 38
coverage_areas:
  - NFR-006 §2.1 Standardisiertes Error-Format (ErrorResponse-Schema)
  - NFR-006 §2.3 Error-ID-Format (err_<uuid4>)
  - NFR-006 §3.1 Allgemeine Fehler-Codes (400/401/403/404/409/422/429/500/503)
  - NFR-006 §3.2 Domänenspezifische Fehler-Codes (ENTITY_NOT_FOUND, DUPLICATE_ENTRY, PHASE_TRANSITION_INVALID, SLOT_OCCUPIED, INCOMPATIBLE_SUBSTRATE, INCOMPATIBLE_COMPANION)
  - NFR-006 §6 Sicherheitsanforderungen (keine Stack-Traces, keine DB-Details, keine internen Pfade)
  - NFR-006 §7 Frontend-Integration (useApiError Hook, Snackbar-Meldungen, Feld-Fehler in Formularen)
  - NFR-006 §9 Akzeptanzkriterien (Testszenarien 1-4)
generated: 2026-03-21
version: "1.0"
selenium_ready: true
test_type: E2E
perspective: browser
---

# TC-NFR-006: Strukturierte API-Fehlerbehandlung mit eindeutiger Tracking-ID

## Scope und Abgrenzung

Diese Testfälle prüfen **ausschließlich das beobachtbare Browserverhalten** bei API-Fehlern. Sie dienen als
Grundlage für Selenium-/Playwright-E2E-Tests. Der Tester sitzt vor dem Browser und beobachtet:

- Welche Fehlermeldung in der UI erscheint (Snackbar, Feld-Fehler, ErrorPage)
- Ob die Meldung fachlich korrekt und sicher ist (keine technischen Details sichtbar)
- Ob die Fehler-Referenz-ID (`error_id`) sichtbar angezeigt wird, wo die Spec es verlangt
- Ob nach einem Fehler die UI in einem konsistenten Zustand bleibt

**Nicht im Scope**: Direkte API-Inspektion per `curl`, Log-Aggregation, Datenbankzustand.

---

## Testfall-Gruppen

| Gruppe | Beschreibung | Testfälle |
|--------|-------------|-----------|
| A | Netzwerk- und Verbindungsfehler | TC-NFR006-001 – TC-NFR006-003 |
| B | Authentifizierungs- und Autorisierungsfehler | TC-NFR006-004 – TC-NFR006-007 |
| C | Nicht-gefunden-Fehler (404 / ENTITY_NOT_FOUND) | TC-NFR006-008 – TC-NFR006-011 |
| D | Duplikat-Fehler (409 / DUPLICATE_ENTRY) | TC-NFR006-012 – TC-NFR006-015 |
| E | Pydantic-Validierungsfehler (422 / VALIDATION_ERROR) | TC-NFR006-016 – TC-NFR006-021 |
| F | Domänenspezifische 422-Fehler | TC-NFR006-022 – TC-NFR006-026 |
| G | Rate-Limiting (429 / RATE_LIMITED) | TC-NFR006-027 – TC-NFR006-028 |
| H | Interne Serverfehler (500 / INTERNAL_ERROR) | TC-NFR006-029 – TC-NFR006-032 |
| I | Service Unavailable (503) | TC-NFR006-033 – TC-NFR006-034 |
| J | Sicherheit – keine technischen Details in der UI | TC-NFR006-035 – TC-NFR006-038 |

---

## Gruppe A: Netzwerk- und Verbindungsfehler

---

## TC-NFR006-001: Snackbar bei totalem Netzwerkverlust während Formular-Submit

**Requirement**: NFR-006 §7.1 — Frontend-Integration, Network Error Handling
**Priority**: Critical
**Category**: Fehlermeldung / Netzwerkfehler
**Tags**: [NFR-006, network-error, snackbar, formular, create-dialog]

**Zusammenfassung**: Wenn die Netzwerkverbindung unterbrochen ist und der Nutzer ein Formular absendet, erscheint eine deutsche Fehlermeldung in der Snackbar — kein weißer Schirm, kein Stack-Trace.

**Vorbedingungen**:
- Nutzer ist angemeldet (Tenant aktiv)
- Browser-DevTools: Netzwerk auf "Offline" stellen (oder Netzwerkkabel physisch trennen)
- Navigation: Stammdaten > Botanische Familien

**Testschritte**:
1. Nutzer öffnet den Dialog "Botanische Familie anlegen" (Button "Erstellen" klicken).
2. Nutzer füllt das Feld "Name" mit `Solanaceae` aus.
3. Nutzer wählt einen Wert für "Nährstoffbedarf" aus dem Dropdown.
4. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Die Snackbar erscheint mit der Meldung: **"Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung."**
- Die Snackbar hat Fehler-Schweregrad (rot / `error`-Severity in MUI).
- Der Dialog bleibt offen — die eingegebenen Daten gehen nicht verloren.
- Kein Stack-Trace, keine URL, keine internen Bezeichner sind sichtbar.
- Das "Speichern"-Button ist nach dem Fehler wieder klickbar.

**Nachbedingungen**:
- Netzwerk wieder einschalten; erneutes Klicken auf "Speichern" schließt den Dialog und zeigt Erfolgsmeldung.

---

## TC-NFR006-002: Fehlermeldung bleibt nach Netzwerkfehler auf Detailseite sichtbar

**Requirement**: NFR-006 §7.1 — Frontend-Integration, Network Error Handling
**Priority**: High
**Category**: Fehlermeldung / Netzwerkfehler
**Tags**: [NFR-006, network-error, detail-page, retry]

**Zusammenfassung**: Wenn eine Detailseite nach Offline-Gehen neu geladen wird, zeigt die UI eine aussagekräftige Fehlermeldung mit Retry-Option, aber keine technischen Details.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Nutzer befindet sich auf der Detailseite einer Botanischen Familie, z.B. `/stammdaten/botanische-familien/solanaceae`.
- Browser-DevTools: Netzwerk auf "Offline" stellen.

**Testschritte**:
1. Nutzer drückt F5 (Seite neu laden) oder klickt auf einen Link, der einen API-Aufruf auslöst.

**Erwartetes Ergebnis**:
- Die UI zeigt entweder:
  - Eine `ApiErrorDisplay`-Komponente mit der Meldung `"Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung."`, oder
  - Eine Snackbar mit demselben Text.
- Ein "Erneut versuchen"-Button ist vorhanden und klickbar.
- Keine technischen Details (IP-Adressen, Ports, DNS-Fehlermeldungen) sind sichtbar.

**Nachbedingungen**:
- Netzwerk wieder einschalten; Klick auf "Erneut versuchen" lädt die Daten erfolgreich.

---

## TC-NFR006-003: Gleichzeitiger Timeout (408) – Illustrated Error Page erscheint

**Requirement**: NFR-006 §3.1 — Error-Code 408; ErrorPage §7 Frontend-Integration
**Priority**: Medium
**Category**: Fehlermeldung / Timeout / ErrorPage
**Tags**: [NFR-006, timeout, 408, error-page, illustrated]

**Zusammenfassung**: Wenn der Server mit HTTP 408 antwortet (Request Timeout), rendert die `ErrorPage`-Komponente die korrekte Illustration und den deutschen Titeltext.

**Vorbedingungen**:
- Test-Umgebung kann 408-Responses simulieren (z.B. via Mock Service Worker oder Backend-Stub).
- Nutzer ist angemeldet.

**Testschritte**:
1. Nutzer navigiert zu einer Seite, deren API-Aufruf mit HTTP 408 simuliert wird.

**Erwartetes Ergebnis**:
- Auf der Seite erscheint die `ErrorPage`-Komponente (`data-testid="error-page"`).
- Die Statuscode-Zahl **"408"** ist sichtbar.
- Titel: **"Zeitüberschreitung"**
- Meldung: **"Die Anfrage hat zu lange gedauert. Bitte versuchen Sie es erneut."**
- Button **"Zurück zum Dashboard"** ist vorhanden (`data-testid="error-go-home"`).

**Nachbedingungen**:
- Klick auf "Zurück zum Dashboard" navigiert zu `/dashboard`.

---

## Gruppe B: Authentifizierungs- und Autorisierungsfehler

---

## TC-NFR006-004: Abgelaufene Session – ErrorPage 401 bei API-Aufruf

**Requirement**: NFR-006 §3.1 — HTTP 401 UNAUTHORIZED; ErrorPage Frontend-Integration
**Priority**: Critical
**Category**: Fehlermeldung / Authentifizierung / ErrorPage
**Tags**: [NFR-006, 401, unauthorized, session-expired, error-page]

**Zusammenfassung**: Wenn das JWT-Token abgelaufen ist und der Nutzer eine Seite mit API-Ladedaten aufruft, zeigt die UI die 401-ErrorPage — kein leerer Zustand, kein weißer Schirm.

**Vorbedingungen**:
- Nutzer war angemeldet; JWT-Token ist abgelaufen (Test-Umgebung: Token manuell aus localStorage entfernen oder Expiry verkürzen).
- Nutzer navigiert direkt zu einer geschützten Seite, z.B. `/stammdaten/botanische-familien`.

**Testschritte**:
1. Nutzer öffnet Browser und navigiert direkt zu einer geschützten URL.

**Erwartetes Ergebnis**:
- Die `ErrorPage`-Komponente (`data-testid="error-page"`) erscheint.
- Statuscode **"401"** ist sichtbar.
- Titel: **"Nicht autorisiert"**
- Meldung: **"Sie müssen sich anmelden, um auf diese Seite zugreifen zu können."**
- Button **"Zurück zum Dashboard"** vorhanden.
- Kein technischer Text (Token-Details, JWT-Payload, interne Fehlermeldung) sichtbar.

**Nachbedingungen**:
- Nutzer kann über den "Zurück zum Dashboard"-Button zur Login-Seite navigieren und sich erneut anmelden.

---

## TC-NFR006-005: Fehlende Berechtigung – ErrorPage 403 bei Tenant-fremdem Zugriff

**Requirement**: NFR-006 §3.1 — HTTP 403 FORBIDDEN; REQ-024 Mandantenverwaltung
**Priority**: Critical
**Category**: Fehlermeldung / Autorisierung / ErrorPage
**Tags**: [NFR-006, 403, forbidden, tenant, rbac, error-page]

**Zusammenfassung**: Ein Nutzer mit Viewer-Rolle versucht eine Schreiboperation (z.B. Löschen). Die UI zeigt die 403-ErrorPage oder Snackbar mit dem richtigen deutschen Text.

**Vorbedingungen**:
- Nutzer ist als Tenant-Viewer angemeldet (Rolle `viewer`).
- Navigation: Stammdaten > Botanische Familien.

**Testschritte**:
1. Nutzer navigiert zur Liste der Botanischen Familien.
2. Nutzer öffnet eine Famille und klickt auf "Löschen" (falls der Button überhaupt sichtbar ist).

**Erwartetes Ergebnis**:
- Falls der Button ausgeblendet ist (bevorzugtes UI-Verhalten): Der "Löschen"-Button ist für Viewer nicht vorhanden — kein Fehler entsteht.
- Falls der API-Aufruf trotzdem ausgelöst wird (Direktaufruf per URL-Manipulation): Die Seite zeigt `ErrorPage` mit Statuscode **"403"**, Titel **"Zugriff verweigert"**, Meldung **"Sie haben keine Berechtigung, auf diese Ressource zuzugreifen."**
- Kein Stack-Trace, keine RBAC-Details, keine internen Rollen-Bezeichner sichtbar.

**Nachbedingungen**:
- Keine Daten wurden verändert.

---

## TC-NFR006-006: Login-Fehler bei falschen Credentials – Snackbar ohne technische Details

**Requirement**: NFR-006 §3.1 — HTTP 401 UNAUTHORIZED; REQ-023 Authentifizierung
**Priority**: Critical
**Category**: Fehlermeldung / Login / Formular
**Tags**: [NFR-006, 401, login, credentials, snackbar]

**Zusammenfassung**: Bei falschen Login-Daten erscheint eine fachliche Fehlermeldung, niemals der raw HTTP-Response oder interne Klassen-Namen.

**Vorbedingungen**:
- Nutzer ist nicht angemeldet.
- Navigation: Login-Seite.

**Testschritte**:
1. Nutzer gibt eine gültige E-Mail-Adresse und ein falsches Passwort ein.
2. Nutzer klickt auf "Anmelden".

**Erwartetes Ergebnis**:
- Eine Fehlermeldung erscheint (Snackbar oder inline), die **ausschließlich** fachliche Information enthält.
- Die Meldung enthält **keine** technischen Details wie `bcrypt`, `PasswordEngine`, `hash`, HTTP-Status-Code als Zahl, Token-Informationen.
- Der Nutzer bleibt auf der Login-Seite; die E-Mail-Adresse bleibt im Feld erhalten.

**Nachbedingungen**:
- Nach 3 fehlgeschlagenen Versuchen erscheint eine Hinweis-Meldung zu Login-Throttling (REQ-023 LoginThrottleEngine).

---

## TC-NFR006-007: Login-Throttling – Snackbar-Hinweis nach maximalen Fehlversuchen

**Requirement**: NFR-006 §3.1 — HTTP 429 RATE_LIMITED; REQ-023 LoginThrottleEngine
**Priority**: High
**Category**: Fehlermeldung / Rate-Limiting / Login
**Tags**: [NFR-006, 429, rate-limited, login-throttle, snackbar]

**Zusammenfassung**: Nach Überschreiten der maximalen Login-Versuche erscheint eine Rate-Limit-Meldung mit dem korrekten deutschen Text, ohne interne Throttle-Details zu exponieren.

**Vorbedingungen**:
- Nutzer ist nicht angemeldet.
- Test-Umgebung: LoginThrottle ist auf niedrigen Schwellwert konfiguriert (z.B. 3 Versuche).

**Testschritte**:
1. Nutzer gibt 3x hintereinander falsche Zugangsdaten ein und klickt jeweils auf "Anmelden".

**Erwartetes Ergebnis**:
- Nach dem letzten Fehlversuch erscheint eine Fehlermeldung in der Snackbar oder als Inline-Text.
- Die Meldung enthält **kein** `RATE_LIMITED`-Code-String direkt sichtbar, **keine** Zeitstempel-Details aus dem Backend.
- Der "Anmelden"-Button ist für eine Weile deaktiviert oder eine Wartezeit wird fachlich kommuniziert.
- Kein Stack-Trace, keine interne IP-basierte Throttle-Konfiguration sichtbar.

**Nachbedingungen**:
- Nach der Wartezeit ist der Login wieder möglich.

---

## Gruppe C: Nicht-gefunden-Fehler (404 / ENTITY_NOT_FOUND)

---

## TC-NFR006-008: Direktaufruf einer nicht existierenden Ressourcen-URL

**Requirement**: NFR-006 §3.1/3.2 — HTTP 404 NOT_FOUND / ENTITY_NOT_FOUND; §9 Szenario 1
**Priority**: High
**Category**: Fehlermeldung / 404 / Navigation / ErrorPage
**Tags**: [NFR-006, 404, not-found, direct-url, error-page, nfr006-szenario1]

**Zusammenfassung**: Wenn der Nutzer eine URL zu einer nicht existierenden Entität aufruft (z.B. mit einem ungültigen Key), rendert die UI die 404-ErrorPage mit illustration und deutschem Text.

**Vorbedingungen**:
- Nutzer ist angemeldet.

**Testschritte**:
1. Nutzer navigiert direkt zu einer URL mit ungültigem Entity-Key, z.B. `/stammdaten/botanische-familien/nicht-vorhanden-xyz`.

**Erwartetes Ergebnis**:
- Die `ErrorPage`-Komponente (`data-testid="error-page"`) erscheint.
- Statuscode **"404"** ist als große Zahl sichtbar.
- Titel: **"Seite nicht gefunden"**
- Meldung: **"Die angeforderte Seite existiert nicht oder wurde verschoben."**
- Button **"Zurück zum Dashboard"** (`data-testid="error-go-home"`) ist vorhanden und funktioniert.
- Der Button **"Zurück"** (`data-testid="error-go-back"`) ist vorhanden (da Browserhistorie > 1 Eintrag).
- Kein technischer Text (AQL, ArangoDB-Key-Format `_key:`, Collection-Namen) ist sichtbar.

**Nachbedingungen**:
- Klick auf "Zurück" kehrt zur vorherigen Seite zurück.

---

## TC-NFR006-009: Löschen einer Ressource, die zwischenzeitlich gelöscht wurde

**Requirement**: NFR-006 §3.2 — ENTITY_NOT_FOUND; §7.1 useApiError Hook
**Priority**: High
**Category**: Fehlermeldung / 404 / Concurrent-Delete / Snackbar
**Tags**: [NFR-006, entity-not-found, concurrent-delete, snackbar, optimistic-ui]

**Zusammenfassung**: Wenn Nutzer A eine Ressource löscht und Nutzer B gleichzeitig dieselbe Ressource zu löschen versucht, sieht Nutzer B eine fachliche Snackbar-Meldung.

**Vorbedingungen**:
- Nutzer A und Nutzer B sind beide angemeldet (verschiedene Browser oder Tabs).
- Beide befinden sich auf der Liste der Botanischen Familien und sehen denselben Eintrag "Testfamilie".

**Testschritte**:
1. Nutzer A löscht "Testfamilie" und bestätigt den Confirm-Dialog.
2. Nutzer B klickt ebenfalls auf "Löschen" bei "Testfamilie" und bestätigt den Confirm-Dialog.

**Erwartetes Ergebnis (Nutzer B)**:
- Die Snackbar erscheint mit der Meldung: **"Die angeforderte Ressource wurde nicht gefunden."**
- Die Liste bei Nutzer B aktualisiert sich (Eintrag ist bereits weg).
- Kein Stack-Trace, kein ArangoDB-Key, kein `DocumentGetError` sichtbar.

**Nachbedingungen**:
- Liste zeigt korrekte Daten ohne den gelöschten Eintrag.

---

## TC-NFR006-010: Referenzierte Entität existiert nicht – Pflanzinstanz mit ungültigem Species-Key

**Requirement**: NFR-006 §3.2 — ENTITY_NOT_FOUND; §1.3 Praktisches Beispiel
**Priority**: High
**Category**: Fehlermeldung / 422 / Formular / Snackbar
**Tags**: [NFR-006, entity-not-found, species-key, plant-instance, create-form, nfr006-beispiel]

**Zusammenfassung**: Wenn der Nutzer eine Pflanzinstanz mit einem ungültigen `species_key` anlegt, erscheint in der Snackbar eine fachliche Meldung — kein technischer Fehler.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Pflanzen > Neue Pflanzinstanz anlegen.
- Test-Umgebung: API-Mock antwortet auf POST `/plant-instances` mit HTTP 422, `error_code: "ENTITY_NOT_FOUND"`, `field: "species_key"`.

**Testschritte**:
1. Nutzer öffnet den Dialog "Pflanzinstanz anlegen".
2. Nutzer gibt einen ungültigen Species-Key ein (z.B. durch direktes Tippen in das Suchfeld und Auswahl einer nicht vorhandenen Option).
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Die Snackbar erscheint mit der Meldung: **"Die angeforderte Ressource wurde nicht gefunden."**
- Alternativ: Das Formularfeld `species_key` zeigt einen Inline-Fehlertext.
- Kein technischer Fehlertext (`ArangoSpeciesRepository`, `species/xyz-123`, AQL-Query) sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer kann einen gültigen Species-Key auswählen und den Dialog erfolgreich speichern.

---

## TC-NFR006-011: Botanische Familie im Edit-Dialog nicht gefunden – Snackbar statt weißer Schirm

**Requirement**: NFR-006 §3.2 — ENTITY_NOT_FOUND; §7.1 Frontend-Integration
**Priority**: Medium
**Category**: Fehlermeldung / Edit-Dialog / 404 / Snackbar
**Tags**: [NFR-006, entity-not-found, edit-dialog, botanical-family]

**Zusammenfassung**: Wenn der Nutzer einen Edit-Dialog öffnet und die Entität währenddessen von einem anderen Nutzer gelöscht wurde, erscheint beim Speichern eine fachliche Snackbar-Meldung.

**Vorbedingungen**:
- Nutzer A hat den Edit-Dialog einer Botanischen Familie geöffnet.
- Nutzer B löscht diese Familie.
- Nutzer A ist noch im offenen Edit-Dialog.

**Testschritte**:
1. Nutzer A ändert einen Wert im Formular.
2. Nutzer A klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar mit Meldung: **"Die angeforderte Ressource wurde nicht gefunden."**
- Der Dialog bleibt offen (Daten nicht verloren).
- Keine technischen Details im sichtbaren UI.

**Nachbedingungen**:
- Nutzer A kann den Dialog schließen und sieht, dass der Eintrag aus der Liste verschwunden ist.

---

## Gruppe D: Duplikat-Fehler (409 / DUPLICATE_ENTRY)

---

## TC-NFR006-012: Anlegen einer Botanischen Familie mit doppeltem Namen – Snackbar DUPLICATE_ENTRY

**Requirement**: NFR-006 §3.2 — DUPLICATE_ENTRY; §4.4 Verwendung in Routen; §9 Szenario 2 (Analogie)
**Priority**: High
**Category**: Fehlermeldung / 409 / Formular / Snackbar / Duplikat
**Tags**: [NFR-006, duplicate-entry, botanical-family, create-form, snackbar]

**Zusammenfassung**: Wenn der Nutzer eine Botanische Familie anlegt, deren Name bereits existiert, erscheint in der Snackbar die korrekte deutsche Duplikat-Meldung.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Botanische Familie "Solanaceae" existiert bereits in der Datenbank.
- Navigation: Stammdaten > Botanische Familien.

**Testschritte**:
1. Nutzer klickt auf "Erstellen".
2. Nutzer gibt im Feld "Name" den Wert `Solanaceae` ein.
3. Nutzer füllt alle Pflichtfelder aus und klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Die Snackbar erscheint mit der Meldung: **"Ein Eintrag mit diesem Namen existiert bereits."**
- Der Dialog bleibt offen; das Feld "Name" zeigt ggf. einen Inline-Fehlertext.
- Kein technischer Text (`unique constraint`, `idx_1858169123378298880`, `ArangoDB`, `_key: 575`) ist in der UI sichtbar.

**Nachbedingungen**:
- Nutzer ändert den Namen; Speichern-Klick schließt den Dialog erfolgreich.

---

## TC-NFR006-013: Duplikat beim Anlegen einer Spezies – Snackbar ohne DB-Details

**Requirement**: NFR-006 §3.2 — DUPLICATE_ENTRY; §6.4 Verbotene vs. erlaubte Fehlerantworten
**Priority**: High
**Category**: Fehlermeldung / 409 / Formular / Snackbar / Duplikat
**Tags**: [NFR-006, duplicate-entry, species, create-form, snackbar, security]

**Zusammenfassung**: Beim Versuch, eine Spezies mit bereits vergebenem wissenschaftlichen Namen anzulegen, erscheint die fachliche Duplikat-Meldung — explizit keine ArangoDB-Fehlermeldung sichtbar.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Spezies mit `scientific_name="Solanum lycopersicum"` existiert bereits.
- Navigation: Stammdaten > Arten.

**Testschritte**:
1. Nutzer klickt auf "Erstellen".
2. Nutzer gibt im Feld "Wissenschaftlicher Name" den Wert `Solanum lycopersicum` ein.
3. Nutzer füllt Pflichtfelder aus und klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar mit Meldung: **"Ein Eintrag mit diesem Namen existiert bereits."**
- Kein Text aus dem ArangoDB-Error-Format (`[HTTP 409][ERR 1210] unique constraint violated`) ist sichtbar.
- Kein interner Collection-Name (`species`, `botanical_families`) oder Index-Name sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer kann einen anderen Namen eingeben und erfolgreich speichern.

---

## TC-NFR006-014: Duplikat beim Anlegen eines Nährstoffplans mit vorhandenem Namen

**Requirement**: NFR-006 §3.2 — DUPLICATE_ENTRY
**Priority**: Medium
**Category**: Fehlermeldung / 409 / Formular / Snackbar
**Tags**: [NFR-006, duplicate-entry, nutrient-plan, create-form]

**Zusammenfassung**: Beim Anlegen eines Nährstoffplans mit bereits vergebenem Namen zeigt die UI die standardisierte Duplikat-Meldung.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Nährstoffplan mit dem Namen "Basis-Wachstum" existiert bereits.
- Navigation: Düngung > Nährstoffpläne.

**Testschritte**:
1. Nutzer klickt auf "Erstellen".
2. Nutzer gibt im Feld "Name" den Wert `Basis-Wachstum` ein.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar mit Meldung: **"Ein Eintrag mit diesem Namen existiert bereits."**
- Kein technischer Text aus dem Backend sichtbar.

**Nachbedingungen**:
- Nutzer kann einen anderen Namen wählen und erfolgreich speichern.

---

## TC-NFR006-015: Doppelter Pflanzendurchlauf-Name – Snackbar im PlantingRunCreateDialog

**Requirement**: NFR-006 §3.2 — DUPLICATE_ENTRY; REQ-013
**Priority**: Medium
**Category**: Fehlermeldung / 409 / Dialog / Snackbar
**Tags**: [NFR-006, duplicate-entry, planting-run, create-dialog]

**Zusammenfassung**: Ein Nutzer legt einen Pflanzendurchlauf mit bereits vergebenem Namen an und erhält die standardisierte Duplikat-Meldung.

**Vorbedingungen**:
- Nutzer ist angemeldet (Tenant aktiv).
- Pflanzendurchlauf "Frühling 2026" existiert bereits.
- Navigation: Durchläufe.

**Testschritte**:
1. Nutzer klickt auf "Erstellen".
2. Nutzer gibt im Feld "Name" `Frühling 2026` ein.
3. Nutzer füllt Pflichtfelder aus und klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar mit Meldung: **"Ein Eintrag mit diesem Namen existiert bereits."**
- Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer ändert den Namen; Dialog schließt sich nach erfolgreichem Speichern.

---

## Gruppe E: Pydantic-Validierungsfehler (422 / VALIDATION_ERROR)

---

## TC-NFR006-016: Pflichtfeld fehlt – Formular zeigt Feld-Fehler (body.name missing)

**Requirement**: NFR-006 §2.1 ErrorResponse-Schema; §4.2 validation_error_handler; §9 Szenario 2
**Priority**: Critical
**Category**: Formvalidierung / 422 / Inline-Fehler
**Tags**: [NFR-006, validation-error, required-field, inline-error, botanical-family, nfr006-szenario2]

**Zusammenfassung**: Wenn der Nutzer ein Formular mit fehlendem Pflichtfeld absendet, erscheinen Inline-Fehlertexte an den entsprechenden Feldern und eine Snackbar — entsprechend dem Backend-`details[].field`-Mapping.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien > "Erstellen".
- Der Create-Dialog ist geöffnet.
- Client-seitige Zod-Validierung ist deaktiviert oder umgangen (direkter API-Mock mit HTTP 422 Response).

**Testschritte**:
1. Nutzer lässt das Pflichtfeld "Name" leer.
2. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Das Formularfeld "Name" zeigt einen Inline-Fehlertext (z.B. "Pflichtfeld" oder der vom Backend gelieferte Grund).
- Die Snackbar erscheint mit: **"Bitte überprüfen Sie Ihre Eingaben."**
- Kein technischer Text (`body.name`, `Field required`, Pydantic-Klassen-Name) ist direkt in der UI sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer füllt das Feld aus; Speichern schließt Dialog erfolgreich.

---

## TC-NFR006-017: Ungültiger Enum-Wert – Dropdown-Fehler im Formular

**Requirement**: NFR-006 §4.2 — validation_error_handler; §9 Szenario 2 (typical_nutrient_demand)
**Priority**: High
**Category**: Formvalidierung / 422 / Inline-Fehler / Enum
**Tags**: [NFR-006, validation-error, enum, dropdown, botanical-family, nfr006-szenario2]

**Zusammenfassung**: Wenn ein Dropdown-Wert nicht im erlaubten Enum liegt (Backend-seitige Validierung), erscheint der Fehler feldspezifisch und ohne interne Pydantic-Details.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien > "Erstellen".
- Test-Umgebung: API-Mock antwortet mit HTTP 422, `details[0].field="body.typical_nutrient_demand"`, `details[0].reason="Input should be 'low', 'medium' or 'high'"`, `details[0].code="enum"`.

**Testschritte**:
1. Nutzer öffnet den Create-Dialog.
2. Nutzer füllt alle Felder aus.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Das Feld "Nährstoffbedarf" zeigt einen Inline-Fehlertext.
- Snackbar: **"Bitte überprüfen Sie Ihre Eingaben."**
- Der `code: "enum"` Pydantic-interne Typ wird **nicht** direkt in der UI angezeigt.
- Kein Text `Input should be...` in Pydantic-Rohformat sichtbar (der Hook bereinigt dies).

**Nachbedingungen**:
- Nutzer wählt einen gültigen Wert; Speichern erfolgreich.

---

## TC-NFR006-018: Mehrere Validierungsfehler gleichzeitig – alle Felder hervorgehoben

**Requirement**: NFR-006 §2.1 — `details: list[ErrorDetail]`; §4.2 validation_error_handler
**Priority**: High
**Category**: Formvalidierung / 422 / Mehrere-Fehler / Inline-Fehler
**Tags**: [NFR-006, validation-error, multiple-fields, inline-error, form]

**Zusammenfassung**: Bei mehreren gleichzeitigen Validierungsfehlern werden alle betroffenen Felder hervorgehoben — nicht nur das erste.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien > "Erstellen".
- Test-Umgebung: API-Mock antwortet mit HTTP 422 und 2 Fehlern: `body.name` (missing) und `body.typical_nutrient_demand` (enum).

**Testschritte**:
1. Nutzer öffnet den Create-Dialog ohne Felder auszufüllen.
2. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Sowohl das Feld "Name" als auch das Feld "Nährstoffbedarf" zeigen Inline-Fehlertexte.
- Snackbar: **"Bitte überprüfen Sie Ihre Eingaben."** (nur einmal, nicht mehrfach).
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer füllt alle Felder aus und speichert erfolgreich.

---

## TC-NFR006-019: Client-seitige Zod-Validierung schlägt an – kein API-Aufruf

**Requirement**: NFR-006 §7 — Frontend-Integration; Zod-Schemas im Frontend (ergänzend)
**Priority**: High
**Category**: Formvalidierung / Client-Side / Zod / Keine API
**Tags**: [NFR-006, client-validation, zod, botanical-family, no-api-call]

**Zusammenfassung**: Die client-seitige Zod-Validierung verhindert den API-Aufruf bei offensichtlichen Eingabefehlern. Die Fehlermeldung erscheint sofort, ohne Netzwerk-Roundtrip.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien > "Erstellen".

**Testschritte**:
1. Nutzer gibt im Feld "Name" den Wert `Solanum` ein (endet nicht auf `aceae`).
2. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Das Feld "Name" zeigt sofort (ohne Ladeindikator) einen Inline-Fehlertext.
- Kein Netzwerk-Request wird gesendet (in DevTools Network-Tab: kein POST sichtbar).
- Die Fehlermeldung ist verständlich auf Deutsch.

**Nachbedingungen**:
- Nutzer korrigiert den Namen zu `Solanaceae`; Speichern erfolgreich.

---

## TC-NFR006-020: Ungültige pH-Grenzen im BotanicalFamily-Formular – client-seitige Validierung

**Requirement**: NFR-006 §7 — Frontend-Integration; Zod min(3)/max(9) Validierung
**Priority**: Medium
**Category**: Formvalidierung / Client-Side / Boundary / Inline-Fehler
**Tags**: [NFR-006, client-validation, ph-range, boundary, botanical-family]

**Zusammenfassung**: Das Formularfeld für `soil_ph_min` akzeptiert keine Werte ausserhalb des erlaubten Bereichs (3–9). Der Inline-Fehler erscheint ohne API-Aufruf.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien > Edit-Dialog einer vorhandenen Familie.

**Testschritte**:
1. Nutzer gibt im Feld "pH-Min" den Wert `1.5` ein (unterhalb des Minimums von 3).
2. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Das Feld "pH-Min" zeigt einen Inline-Fehlertext.
- Kein Netzwerk-Request wird gesendet.
- Die Meldung enthält keine technischen Zod-Schema-Details.

**Nachbedingungen**:
- Nutzer gibt einen Wert im Bereich 3–9 ein; Speichern erfolgreich.

---

## TC-NFR006-021: `days_to_maturity` ausserhalb des erlaubten Bereichs – Cultivar-Dialog

**Requirement**: NFR-006 §7 — Frontend-Integration; Zod min(1)/max(365) für Cultivar
**Priority**: Medium
**Category**: Formvalidierung / Client-Side / Boundary / Inline-Fehler
**Tags**: [NFR-006, client-validation, days-to-maturity, cultivar, boundary]

**Zusammenfassung**: Im Cultivar-Erstellungsdialog wird ein Wert von 400 für `days_to_maturity` eingegeben. Der Inline-Fehler erscheint sofort.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Arten > Detail einer Spezies > Tab "Sorten" > "Neue Sorte".

**Testschritte**:
1. Nutzer öffnet den Sorte-Erstellen-Dialog.
2. Nutzer gibt im Feld "Tage bis zur Erntereife" den Wert `400` ein.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Das Feld "Tage bis zur Erntereife" zeigt einen Inline-Fehlertext (maximal 365 Tage).
- Kein Netzwerk-Request wird gesendet.

**Nachbedingungen**:
- Nutzer gibt einen Wert zwischen 1 und 365 ein; Speichern erfolgreich.

---

## Gruppe F: Domänenspezifische 422-Fehler

---

## TC-NFR006-022: Ungültiger Phasenübergang – Snackbar PHASE_TRANSITION_INVALID

**Requirement**: NFR-006 §3.2 — PHASE_TRANSITION_INVALID; REQ-003 Phasensteuerung
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel / 422 / Snackbar
**Tags**: [NFR-006, phase-transition-invalid, growth-phase, plant-instance, snackbar]

**Zusammenfassung**: Wenn der Nutzer versucht, eine Phase rückwärts zu wechseln (z.B. von Vegetativ zurück auf Keimling), erscheint eine Snackbar mit einer fachlichen Meldung — keine Backend-Exception sichtbar.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Eine Pflanzinstanz befindet sich in der Phase "Vegetativ".
- Navigation: Pflanzen > Pflanzinstanz-Detail > Phase wechseln.
- Test-Umgebung: API-Mock antwortet bei rückwärtigem Übergang mit HTTP 422, `error_code: "PHASE_TRANSITION_INVALID"`.

**Testschritte**:
1. Nutzer öffnet den Phasen-Wechsel-Dialog.
2. Nutzer wählt "Keimling" als Zielphase (Rückwärtstransition).
3. Nutzer klickt auf "Speichern" oder "Bestätigen".

**Erwartetes Ergebnis**:
- Alternativ ist die Zielphase "Keimling" im Dialog ausgegraut/deaktiviert (bevorzugtes UI-Verhalten für ungültige Übergänge).
- Falls nicht ausgegraut: Snackbar erscheint mit einer fachlichen Meldung.
- Kein technischer Text (`PhaseTransitionEngine`, `validate_transition()`, Enum-Werte) sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer kann einen vorwärtigen Übergang auswählen und bestätigen.

**Siehe auch**: TC-REQ-006 Phasensteuerung Testfälle für vollständige Phasen-Zustandsmaschinen-Tests.

---

## TC-NFR006-023: Belegter Stellplatz – Snackbar SLOT_OCCUPIED

**Requirement**: NFR-006 §3.2 — SLOT_OCCUPIED; REQ-002 Standortverwaltung
**Priority**: High
**Category**: Fehlermeldung / 422 / Dialog / Snackbar
**Tags**: [NFR-006, slot-occupied, standort, slot, snackbar]

**Zusammenfassung**: Wenn der Nutzer versucht, eine Pflanzinstanz einem bereits belegten Stellplatz zuzuweisen, erscheint eine verständliche Snackbar-Meldung.

**Vorbedingungen**:
- Nutzer ist angemeldet (Tenant aktiv).
- Ein Stellplatz "Beet A, Platz 1" ist bereits belegt.
- Navigation: Standorte > Beet A > Stellplatz 1.
- Test-Umgebung: API-Mock antwortet mit HTTP 422, `error_code: "SLOT_OCCUPIED"`.

**Testschritte**:
1. Nutzer öffnet den Dialog "Pflanzinstanz zuweisen" für "Beet A, Platz 1".
2. Nutzer wählt eine Pflanzinstanz aus.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar erscheint mit einer fachlichen Meldung, die kommuniziert, dass der Stellplatz belegt ist.
- Kein technischer Text (`SLOT_OCCUPIED`, Collection-Name, `_key`) direkt sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer wählt einen freien Stellplatz; Zuweisung erfolgreich.

---

## TC-NFR006-024: Inkompatibles Substrat – Snackbar INCOMPATIBLE_SUBSTRATE

**Requirement**: NFR-006 §3.2 — INCOMPATIBLE_SUBSTRATE; REQ-019 Substratverwaltung
**Priority**: Medium
**Category**: Fehlermeldung / 422 / Dialog / Snackbar
**Tags**: [NFR-006, incompatible-substrate, substrate, snackbar]

**Zusammenfassung**: Wenn der Nutzer ein Substrat auswählt, das nicht mit der Spezies kompatibel ist, erscheint eine fachliche Snackbar-Meldung ohne interne Klassen-Namen.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Test-Umgebung: API-Mock antwortet mit HTTP 422, `error_code: "INCOMPATIBLE_SUBSTRATE"`.

**Testschritte**:
1. Nutzer öffnet den Dialog "Substrat zuweisen" für eine Pflanzinstanz.
2. Nutzer wählt ein inkompatibles Substrat aus.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar erscheint mit einer fachlichen Meldung zu Substrat-Inkompatibilität.
- Kein interner Text (`SubstrateLifecycleManager`, `INCOMPATIBLE_SUBSTRATE` als Code-String direkt) sichtbar.
- Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer wählt kompatibles Substrat; Speichern erfolgreich.

---

## TC-NFR006-025: Mischkultur-Konflikt – Snackbar INCOMPATIBLE_COMPANION

**Requirement**: NFR-006 §3.2 — INCOMPATIBLE_COMPANION; REQ-028 Companion Planting
**Priority**: Medium
**Category**: Fehlermeldung / 422 / Mischkultur / Snackbar
**Tags**: [NFR-006, incompatible-companion, companion-planting, snackbar]

**Zusammenfassung**: Wenn der Nutzer eine Pflanzinstanz einem Stellplatz zuweist, der eine inkompatible Nachbarpflanze hat, erscheint eine Mischkultur-Konflikt-Meldung.

**Vorbedingungen**:
- Nutzer ist angemeldet (Tenant aktiv).
- Test-Umgebung: API-Mock antwortet mit HTTP 422, `error_code: "INCOMPATIBLE_COMPANION"`.

**Testschritte**:
1. Nutzer öffnet den Slot-Zuweisung-Dialog.
2. Nutzer wählt eine Spezies aus, die mit dem Nachbar-Slot inkompatibel ist.
3. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar erscheint mit einer fachlichen Meldung zur Mischkultur-Inkompatibilität.
- Alternativ: Eine Warnungs-Anzeige im Dialog (nicht-blockierend gemäss REQ-028).
- Kein interner Error-Code (`INCOMPATIBLE_COMPANION`) als Rohtext sichtbar.

**Nachbedingungen**:
- Nutzer kann die Zuweisung bestätigen (wenn Warnung nicht-blockierend) oder andere Spezies wählen.

**Siehe auch**: TC-REQ-028 Companion Planting für vollständige Mischkultur-UI-Tests.

---

## TC-NFR006-026: Karenz-Verletzung – Snackbar bei Ernte während aktiver Karenzfrist

**Requirement**: NFR-006 §3.2 — VALIDATION_ERROR (domänenspezifisch); REQ-010 IPM Karenz-Gate
**Priority**: High
**Category**: Fehlermeldung / 422 / Ernte / Karenz / Snackbar
**Tags**: [NFR-006, validation-error, karenz, harvest, ipm, snackbar]

**Zusammenfassung**: Wenn der Nutzer eine Ernte anlegt und die Karenzfrist einer Behandlung noch nicht abgelaufen ist, erscheint eine fachliche Fehlermeldung.

**Vorbedingungen**:
- Nutzer ist angemeldet (Tenant aktiv).
- Eine Pflanzinstanz hat eine aktive Behandlung mit laufender Karenzfrist.
- Navigation: Ernte > Neue Ernte anlegen.
- Test-Umgebung: API-Mock antwortet mit HTTP 422.

**Testschritte**:
1. Nutzer öffnet den "Ernte anlegen"-Dialog für die betroffene Pflanzinstanz.
2. Nutzer füllt alle Felder aus und klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Die Snackbar zeigt eine fachliche Meldung (Karenzfrist noch nicht abgelaufen).
- Kein technischer Text (`KarenzViolationError`, `SafetyIntervalValidator`) sichtbar.
- Der Dialog bleibt offen.

**Nachbedingungen**:
- Nutzer muss bis zum Ende der Karenzfrist warten oder die Behandlung prüfen.

---

## Gruppe G: Rate-Limiting (429 / RATE_LIMITED)

---

## TC-NFR006-027: Rate-Limit ausgelöst – ErrorPage 429 mit illustration

**Requirement**: NFR-006 §3.1 — HTTP 429 RATE_LIMITED; ErrorPage Frontend-Integration
**Priority**: High
**Category**: Fehlermeldung / 429 / Rate-Limit / ErrorPage
**Tags**: [NFR-006, 429, rate-limited, error-page, illustrated]

**Zusammenfassung**: Wenn das API-Rate-Limit ausgelöst wird, rendert die UI die 429-ErrorPage mit der korrekten deutschen Meldung und Illustration.

**Vorbedingungen**:
- Test-Umgebung: Rate-Limit auf niedrigen Schwellwert konfiguriert.
- Nutzer ist angemeldet.

**Testschritte**:
1. Nutzer löst schnell hintereinander viele API-Anfragen aus (z.B. durch schnelles Paginieren oder wiederholtes Absenden).
2. Das Rate-Limit wird überschritten; der Server antwortet mit HTTP 429.

**Erwartetes Ergebnis**:
- `ErrorPage`-Komponente erscheint (`data-testid="error-page"`).
- Statuscode **"429"** sichtbar.
- Titel: **"Zu viele Anfragen"**
- Meldung: **"Sie haben zu viele Anfragen gesendet. Bitte warten Sie einen Moment."**
- Button **"Zurück zum Dashboard"** vorhanden.
- Kein technischer Text (Rate-Limit-Konfiguration, IP-Adresse, X-RateLimit-Header als Rohtext) sichtbar.

**Nachbedingungen**:
- Nach der Rate-Limit-Abklingzeit ist die Seite wieder nutzbar.

---

## TC-NFR006-028: Test-Benachrichtigung Rate-Limit – Button deaktiviert (REQ-030)

**Requirement**: NFR-006 §3.1 — HTTP 429 RATE_LIMITED; REQ-030 Notification System
**Priority**: Medium
**Category**: Fehlermeldung / 429 / Rate-Limit / Button-Zustand
**Tags**: [NFR-006, 429, rate-limited, notification, test-button, disabled-state]

**Zusammenfassung**: Die Test-Benachrichtigungs-Funktion (REQ-030) ist auf 5 Anfragen pro Stunde begrenzt. Nach Überschreiten zeigt die UI entweder einen deaktivierten Button oder eine Fehlermeldung.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Navigation: Kontoeinstellungen > Benachrichtigungen (REQ-030 Tab).
- Test-Umgebung: Rate-Limit für Test-Notifications auf 1/Stunde konfiguriert.

**Testschritte**:
1. Nutzer klickt 2x auf "Test-Benachrichtigung senden".

**Erwartetes Ergebnis**:
- Beim zweiten Klick erscheint entweder:
  - Eine Snackbar mit einer fachlichen Rate-Limit-Meldung, oder
  - Der Button ist deaktiviert mit einem Tooltip "Limit erreicht".
- Kein technischer Text (Rate-Limit-Algorithmus, interne Zähler) sichtbar.

**Nachbedingungen**:
- Nach einer Stunde ist der Button wieder aktiv.

---

## Gruppe H: Interne Serverfehler (500 / INTERNAL_ERROR)

---

## TC-NFR006-029: Simulierter DB-Ausfall – ErrorPage 500 ohne technische Details

**Requirement**: NFR-006 §3.1 — HTTP 500 INTERNAL_ERROR; §6 Sicherheitsanforderungen; §9 Szenario 3
**Priority**: Critical
**Category**: Fehlermeldung / 500 / Sicherheit / ErrorPage
**Tags**: [NFR-006, 500, internal-error, security, no-stack-trace, error-page, nfr006-szenario3]

**Zusammenfassung**: Bei einem simulierten internen Serverfehler (z.B. DB-Ausfall) zeigt die UI die 500-ErrorPage mit generischer Meldung — kein Stack-Trace, keine ArangoDB-Details sichtbar.

**Vorbedingungen**:
- Test-Umgebung: API-Mock antwortet auf beliebige Anfrage mit HTTP 500, `error_code: "INTERNAL_ERROR"`, `details: []`, `message: "Ein interner Fehler ist aufgetreten. Bitte kontaktieren Sie den Support mit der Referenz-ID."`.
- Nutzer ist angemeldet.
- Navigation: Stammdaten > Botanische Familien.

**Testschritte**:
1. Nutzer lädt die Seite oder führt eine Aktion aus, die den simulierten 500-Fehler auslöst.

**Erwartetes Ergebnis**:
- `ErrorPage`-Komponente (`data-testid="error-page"`) erscheint.
- Statuscode **"500"** sichtbar.
- Titel: **"Serverfehler"**
- Meldung: **"Ein interner Fehler ist aufgetreten. Wir arbeiten daran, das Problem zu beheben."**
- Button **"Zurück zum Dashboard"** vorhanden.
- Kein Stack-Trace, kein `Traceback`, kein `File "/"`, kein `ArangoDB`, kein `arango.exceptions`, kein `.py`-Dateipfad, kein `localhost:`, kein `redis://` sichtbar.

**Nachbedingungen**:
- Nach Behebung des Fehlers ist die Seite wieder nutzbar.

---

## TC-NFR006-030: Serverfehler beim Formular-Submit – Snackbar mit error_id (INTERNAL_ERROR)

**Requirement**: NFR-006 §2.3 — error_id-Format; §7.2 Anzeige für Endanwender; §9 Szenario 3
**Priority**: Critical
**Category**: Fehlermeldung / 500 / Snackbar / error_id / Sicherheit
**Tags**: [NFR-006, internal-error, snackbar, error-id, reference-number, security]

**Zusammenfassung**: Wenn ein Formular-Submit einen 500-Fehler zurückliefert, zeigt die Snackbar die generische Fehlermeldung mit der `error_id` als Support-Referenz — aber keine internen Details.

**Vorbedingungen**:
- Nutzer ist angemeldet.
- Test-Umgebung: API-Mock antwortet auf POST mit HTTP 500, `error_id: "err_abc123-test"`, `error_code: "INTERNAL_ERROR"`, `details: []`.
- Navigation: Stammdaten > Botanische Familien > "Erstellen".

**Testschritte**:
1. Nutzer füllt das Formular korrekt aus.
2. Nutzer klickt auf "Speichern".

**Erwartetes Ergebnis**:
- Snackbar erscheint mit der Meldung: **"Serverfehler. Bitte versuchen Sie es später erneut."**
- Der Dialog bleibt offen.
- Kein Stack-Trace, kein ArangoDB-Text, kein Python-Pfad sichtbar.
- (Optional, je nach Implementierungsstand) Die `error_id` ist als Referenz sichtbar für den Support.

**Nachbedingungen**:
- Nach Behebung ist Speichern erfolgreich.

**Anmerkung**: Gemäss NFR-006 §7.2 soll die UI die `error_id` als Support-Referenz anzeigen. Die Snackbar aus `useApiError` zeigt aktuell für `INTERNAL_ERROR` nur die generische `errors.server`-Meldung. Diese Testfall-Anforderung dokumentiert das Soll-Verhalten: bei INTERNAL_ERROR soll die `error_id` in der Snackbar angezeigt werden.

---

## TC-NFR006-031: Unbehandelter Backend-Fehler – kein Rohtext exponiert

**Requirement**: NFR-006 §4.2 — unhandled_error_handler; §6.2 Verbotene Inhalte
**Priority**: Critical
**Category**: Fehlermeldung / 500 / Sicherheit / Information Disclosure
**Tags**: [NFR-006, unhandled-error, security, information-disclosure, internal-error]

**Zusammenfassung**: Wenn eine unbehandelte Exception im Backend auftritt, erscheint in der UI nur die generische INTERNAL_ERROR-Meldung — kein Python-Traceback, kein Pfad, kein Stack-Frame.

**Vorbedingungen**:
- Test-Umgebung: Der `unhandled_error_handler` kann durch einen dedizierten Endpunkt getriggert werden (z.B. `/api/v1/test/trigger-error`).
- Nutzer ist angemeldet.

**Testschritte**:
1. Nutzer oder Test-Automatisierung ruft einen Endpunkt auf, der eine unbehandelte Exception auslöst.

**Erwartetes Ergebnis**:
- Der Response-Body enthält ausschliesslich:
  - `error_id` (Format: `err_<uuid4>`)
  - `error_code`: `"INTERNAL_ERROR"`
  - `message`: `"Ein interner Fehler ist aufgetreten. Bitte kontaktieren Sie den Support mit der Referenz-ID."`
  - `details`: `[]`
  - `timestamp`, `path`, `method`
- Kein Stack-Trace sichtbar.
- Kein `Traceback (most recent call last)` Text.
- Kein Python-Dateipfad (`/app/`, `/usr/local/lib/python3.14/`).
- Kein Datenbankbegriff (`ArangoDB`, `arango.exceptions`, `redis://`).

**Nachbedingungen**:
- Fehler ist im Backend-Log mit der `error_id` korrelierbar.

---

## TC-NFR006-032: ErrorPage-Fallback für unbekannte Fehlercodes

**Requirement**: NFR-006 §7 — Frontend-Integration; ErrorPage fallback
**Priority**: Medium
**Category**: Fehlermeldung / Fallback / ErrorPage
**Tags**: [NFR-006, fallback, unknown-status-code, error-page]

**Zusammenfassung**: Wenn ein unbekannter HTTP-Statuscode (ausserhalb der illustrierten Codes) zurückgegeben wird, zeigt die UI die generische Fallback-ErrorPage.

**Vorbedingungen**:
- Test-Umgebung: API-Mock antwortet mit HTTP 550 (unbekannter Code) oder einem nicht in `ILLUSTRATED_CODES` enthaltenen Statuscode.

**Testschritte**:
1. Nutzer oder Test löst eine Anfrage aus, die mit einem unbekannten Statuscode beantwortet wird.

**Erwartetes Ergebnis**:
- Der `ApiErrorDisplay` rendert `ErrorDisplay` (kein `ErrorPage` mit Illustration).
- Eine verständliche Fehlermeldung erscheint.
- Kein weisser Schirm, kein JavaScript-Crash (kein Uncaught Error in DevTools).

**Nachbedingungen**:
- Die Anwendung bleibt nutzbar (kein kompletter Absturz).

---

## Gruppe I: Service Unavailable (503)

---

## TC-NFR006-033: Abhängiger Service nicht erreichbar – ErrorPage 503

**Requirement**: NFR-006 §3.1 — HTTP 503 SERVICE_UNAVAILABLE
**Priority**: High
**Category**: Fehlermeldung / 503 / ErrorPage
**Tags**: [NFR-006, 503, service-unavailable, error-page]

**Zusammenfassung**: Wenn ein abhängiger Service (z.B. ein externer Enrichment-Service) nicht erreichbar ist, zeigt die UI die 503-ErrorPage mit der korrekten deutschen Meldung.

**Vorbedingungen**:
- Test-Umgebung: API-Mock antwortet mit HTTP 503.
- Nutzer ist angemeldet.

**Testschritte**:
1. Nutzer führt eine Aktion aus, die den nicht verfügbaren Service benötigt (z.B. Stammdaten-Anreicherung aus REQ-011).

**Erwartetes Ergebnis**:
- `ErrorPage`-Komponente erscheint mit Statuscode **"503"**.
- Titel: **"Wartungsarbeiten"**
- Meldung: **"Der Dienst wird gerade gewartet. Bitte versuchen Sie es in Kürze erneut."**
- Button **"Zurück zum Dashboard"** vorhanden.
- Kein technischer Text (Service-Namen, Kubernetes-Pod-Namen, interne IPs) sichtbar.

**Nachbedingungen**:
- Nach Service-Wiederverfügbarkeit ist die Funktion wieder nutzbar.

---

## TC-NFR006-034: Home Assistant Service Unavailable – Graceful Degradation in der UI

**Requirement**: NFR-006 §3.1 — SERVICE_UNAVAILABLE; REQ-018 Umgebungssteuerung
**Priority**: Medium
**Category**: Fehlermeldung / 503 / Graceful Degradation / Snackbar
**Tags**: [NFR-006, 503, service-unavailable, home-assistant, graceful-degradation]

**Zusammenfassung**: Wenn Home Assistant nicht erreichbar ist und der Nutzer eine HA-abhängige Funktion aufruft, erscheint eine fachliche Meldung — kein interner HA-Client-Fehler sichtbar.

**Vorbedingungen**:
- Test-Umgebung: HA-Client antwortet nicht (simulierter Ausfall).
- Test-Umgebung: API-Mock antwortet mit HTTP 503, `error_code: "SERVICE_UNAVAILABLE"`.

**Testschritte**:
1. Nutzer versucht eine Aktion, die Home Assistant erfordert (z.B. Sensorwert aktualisieren).

**Erwartetes Ergebnis**:
- Snackbar oder ErrorPage mit einer fachlichen Meldung.
- Kein interner Text (`ha_client.py`, `HA_URL`, `HAClientError`, Home-Assistant-URL mit Port).
- Die restliche Anwendung bleibt nutzbar (Graceful Degradation).

**Nachbedingungen**:
- Nach HA-Wiederverfügbarkeit funktioniert die Aktion normal.

---

## Gruppe J: Sicherheit – keine technischen Details in der UI

Diese Gruppe prüft explizit die Sicherheitsanforderungen aus NFR-006 §6 (Allowlist-Prinzip, minimale Informationsexposition). Die Tests sind als negative Prüfungen formuliert: Sie suchen nach verbotenem Inhalt in der UI.

---

## TC-NFR006-035: Kein ArangoDB-Text in beliebiger Fehlermeldung sichtbar

**Requirement**: NFR-006 §6.2.2 — Verbotene Infrastruktur-Informationen; §6.5 CI-Enforcement
**Priority**: Critical
**Category**: Sicherheit / Information Disclosure / Negative-Test
**Tags**: [NFR-006, security, information-disclosure, arangodb, negative-test]

**Zusammenfassung**: In keiner sichtbaren Fehlermeldung der UI erscheinen die Zeichenketten `ArangoDB`, `arango`, `AQL`, `DocumentInsertError`, `_key`, `_id`, `botanical_families/`, `idx_` oder ähnliche ArangoDB-interne Texte.

**Vorbedingungen**:
- Test-Umgebung: API-Mock antwortet auf verschiedene Fehler-Szenarien (404, 409, 422, 500).
- Nutzer ist angemeldet.

**Testschritte**:
1. Tester provoziert alle testbaren Fehler-Szenarien der Gruppen C bis I (Schritte aus den jeweiligen TCs).
2. Tester prüft alle sichtbaren Texte im Browser (Snackbar, ErrorPage, Formular-Fehler, Tooltips, `title`-Attribute).

**Erwartetes Ergebnis**:
- Die Zeichenketten `ArangoDB`, `arango`, `AQL`, `DocumentInsertError`, `FOR doc IN`, `_key:`, `_id:`, `idx_`, `unique constraint`, `botanical_families/`, `species/` erscheinen in **keiner** sichtbaren UI-Komponente.
- Gilt für alle Fehlertexte: Snackbar, Inline-Fehler, ErrorPage, Dialog-Inhalt.

**Nachbedingungen**:
- Kein Testschritt verletzt die Sicherheitsanforderung; alle Fehler zeigen nur fachliche Informationen.

---

## TC-NFR006-036: Kein Python-Stack-Trace oder Dateipfad in Fehlermeldung sichtbar

**Requirement**: NFR-006 §6.2.1/6.2.2 — Verbotene Software- und Infrastruktur-Informationen
**Priority**: Critical
**Category**: Sicherheit / Information Disclosure / Negative-Test / Stack-Trace
**Tags**: [NFR-006, security, stack-trace, python-path, no-traceback, negative-test]

**Zusammenfassung**: Kein Python-Traceback, kein Dateipfad (`/app/`, `/usr/local/lib/python3.14/`, `.py`-Endung) und kein Framework-Name (`FastAPI`, `Pydantic`, `uvicorn`) erscheinen in einer sichtbaren Fehlermeldung.

**Vorbedingungen**:
- Test-Umgebung: Unhandled-Error-Handler aktiv; ein Endpunkt löst eine Exception aus.
- Nutzer ist angemeldet.

**Testschritte**:
1. Tester provoziert einen 500-Fehler über verschiedene Wege (Formular-Submit, Seitenladen, direkte URL).
2. Tester prüft alle sichtbaren Texte im Browser.

**Erwartetes Ergebnis**:
- Die Zeichenketten `Traceback`, `File "/"`, `.py"`, `line `, `FastAPI`, `Pydantic`, `uvicorn`, `Python 3`, `/app/`, `/usr/local/lib/` erscheinen in **keiner** sichtbaren UI-Komponente.
- Der Response-Body enthält nur die erlaubten Felder aus `ErrorResponse`.

**Nachbedingungen**:
- Alle 500-Fehler zeigen ausschliesslich die generische `INTERNAL_ERROR`-Meldung.

---

## TC-NFR006-037: Vollständiges ErrorResponse-Schema in jedem Fehler vorhanden

**Requirement**: NFR-006 §2.1 — Standardisiertes Error-Format; §9 Definition of Done
**Priority**: Critical
**Category**: Fehlerformat / Schema / API-Kontrakt
**Tags**: [NFR-006, error-schema, api-contract, error-id, error-code, required-fields]

**Zusammenfassung**: Jede API-Fehlerantwort (4xx und 5xx) enthält alle Pflichtfelder des `ErrorResponse`-Schemas. Die `ApiError`-Klasse im Frontend kann die Response korrekt parsen.

**Vorbedingungen**:
- Test-Umgebung: Browser-DevTools Network-Tab ist geöffnet.
- Nutzer ist angemeldet.

**Testschritte**:
1. Tester provoziert folgende Fehler-Typen: 404, 409, 422, 500.
2. Tester öffnet jeweils den Network-Tab in DevTools und prüft den Response-Body.

**Erwartetes Ergebnis**:
- Jeder Response-Body enthält:
  - `error_id` — Format: Zeichenkette, die mit `err_` beginnt, gefolgt von einer UUID (`err_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
  - `error_code` — einer der definierten Codes (z.B. `ENTITY_NOT_FOUND`, `DUPLICATE_ENTRY`, `VALIDATION_ERROR`, `INTERNAL_ERROR`).
  - `message` — nicht-leere Zeichenkette.
  - `details` — Array (leer oder mit Objekten).
  - `timestamp` — ISO 8601-konformes Datum-Zeit-Format.
  - `path` — beginnt mit `/api/v1/`.
  - `method` — ein HTTP-Verb in Grossbuchstaben (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`).
- Kein Feld ausserhalb dieses Schemas ist vorhanden.
- Die `ApiError`-Klasse im Frontend wirft keine JavaScript-Fehler beim Parsen.

**Nachbedingungen**:
- Alle Fehlermeldungen werden korrekt angezeigt (keine `undefined`- oder `null`-Texte in der UI).

---

## TC-NFR006-038: error_id-Format korrekt – starts with "err_" + UUID v4

**Requirement**: NFR-006 §2.3 — Error-ID-Format (`err_<uuid4>`)
**Priority**: High
**Category**: Fehlerformat / Schema / error_id / Validierung
**Tags**: [NFR-006, error-id, uuid4, format-validation, api-contract]

**Zusammenfassung**: Die `error_id` in jedem Fehler-Response folgt dem definierten Format `err_<uuid4>`, sodass Support-Teams sie eindeutig suchen können.

**Vorbedingungen**:
- Browser-DevTools Network-Tab geöffnet.
- Test-Umgebung: Realer Backend-Aufruf (kein Mock, damit echte UUIDs generiert werden).
- Nutzer ist angemeldet.

**Testschritte**:
1. Tester provoziert einen 404-Fehler durch Aufruf einer nicht existierenden URL.
2. Tester prüft im DevTools Network-Tab den Response-Body.

**Erwartetes Ergebnis**:
- Das Feld `error_id` ist vorhanden.
- Der Wert beginnt mit `err_`.
- Der Teil nach `err_` ist ein valides UUID v4 Format: 8-4-4-4-12 Hexadezimalzeichen getrennt durch Bindestriche.
- Regex-Prüfung: `^err_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
- Jeder Aufruf generiert eine **neue**, eindeutige `error_id` (keine Wiederholung).

**Nachbedingungen**:
- Die `error_id` kann in der Log-Aggregation gefunden werden (Szenario 4 aus NFR-006 §9 — nur in Infrastruktur-Tests verifizierbar, nicht im Browser-E2E-Test).

---

## Abdeckungs-Matrix

| NFR-006 Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| §2.1 Standardisiertes Error-Format | ErrorResponse-Schema (alle 7 Pflichtfelder) | TC-NFR006-037 |
| §2.3 Error-ID-Format | `err_<uuid4>` Präfix + UUID v4 | TC-NFR006-038 |
| §3.1 HTTP 400 BAD_REQUEST | Syntaktisch fehlerhafte Anfrage | (client-seitig abgefangen, s. TC-NFR006-019–021) |
| §3.1 HTTP 401 UNAUTHORIZED | Fehlende/abgelaufene Auth | TC-NFR006-004, TC-NFR006-006 |
| §3.1 HTTP 403 FORBIDDEN | Autorisierung fehlgeschlagen | TC-NFR006-005 |
| §3.1 HTTP 404 NOT_FOUND | Ressource nicht gefunden | TC-NFR006-008 |
| §3.1 HTTP 409 CONFLICT | Duplikat | TC-NFR006-012–015 |
| §3.1 HTTP 422 VALIDATION_ERROR | Pydantic-Validierungsfehler | TC-NFR006-016–021 |
| §3.1 HTTP 429 RATE_LIMITED | Zu viele Anfragen | TC-NFR006-007, TC-NFR006-027–028 |
| §3.1 HTTP 500 INTERNAL_ERROR | Interner Serverfehler | TC-NFR006-029–032 |
| §3.1 HTTP 503 SERVICE_UNAVAILABLE | Abhängiger Service nicht erreichbar | TC-NFR006-033–034 |
| §3.2 ENTITY_NOT_FOUND | Referenzierte Entität existiert nicht | TC-NFR006-009–011 |
| §3.2 DUPLICATE_ENTRY | Doppelter Schlüssel | TC-NFR006-012–015 |
| §3.2 INCOMPATIBLE_SUBSTRATE | Substrat-Inkompatibilität | TC-NFR006-024 |
| §3.2 INCOMPATIBLE_COMPANION | Mischkultur-Konflikt | TC-NFR006-025 |
| §3.2 SLOT_OCCUPIED | Belegter Stellplatz | TC-NFR006-023 |
| §3.2 PHASE_TRANSITION_INVALID | Ungültiger Phasenübergang | TC-NFR006-022 |
| §6.2.1 Software-Infos verboten | Framework, Python, Klassen-Namen | TC-NFR006-035–036 |
| §6.2.2 Infrastruktur-Infos verboten | DB-Namen, IPs, Pfade, Stack-Traces | TC-NFR006-031, TC-NFR006-035–036 |
| §6.2.3 Geschäftslogik-Interna verboten | Interne Keys, Pydantic-Roh-Output | TC-NFR006-035 |
| §7.1 Frontend API-Client | ApiError-Klasse, interceptors | TC-NFR006-037, TC-NFR006-001 |
| §7.1 useApiError Hook | Feld-Fehler, Snackbar-Mapping | TC-NFR006-016–018, TC-NFR006-012 |
| §7.2 Anzeige mit error_id | Support-Referenz sichtbar | TC-NFR006-030 |
| §9 Szenario 1 — Nicht existierende Ressource | GET mit ungültigem Key | TC-NFR006-008 |
| §9 Szenario 2 — Validierungsfehler | POST mit fehlenden/ungültigen Feldern | TC-NFR006-016–017 |
| §9 Szenario 3 — Interner Fehler ohne Details | 500 ohne Stack-Trace | TC-NFR006-029–031 |
| §9 Szenario 4 — error_id im Log | error_id-Format korrekt | TC-NFR006-038 |
| Netzwerkfehler (kein API-Status) | Network Error im fetch | TC-NFR006-001–002 |
| ErrorPage illustrations | 400/401/403/404/408/429/500/502/503 | TC-NFR006-003, TC-NFR006-004–005, TC-NFR006-027, TC-NFR006-029, TC-NFR006-033 |
| HTTP 408 Request Timeout | Illustrated ErrorPage | TC-NFR006-003 |
| HTTP 502 Bad Gateway | (Illustrated, kein dedizierter TC — Analogie zu 503) | — |
