---
req_id: REQ-023
title: Benutzerverwaltung & Authentifizierung
category: Plattform & Sicherheit
test_count: 72
coverage_areas:
  - Registrierungsseite (/register)
  - Login-Seite (/login)
  - E-Mail-Verifizierung (/verify-email/:token)
  - Passwort-Reset (/password-reset, /password-reset/:token)
  - OAuth-Callback (/auth/oauth/callback)
  - Kontoeinstellungen — Tab Profil (/settings/account?tab=profile)
  - Kontoeinstellungen — Tab Sicherheit (/settings/account?tab=security)
  - Kontoeinstellungen — Tab Sitzungen (/settings/account?tab=sessions)
  - Kontoeinstellungen — Tab API-Schlüssel (/settings/account?tab=apikeys)
  - Kontoeinstellungen — Tab Integrationen (/settings/account?tab=ha)
  - Kontoeinstellungen — Tab Plattform-Modus (/settings/account?tab=platform)
  - Kontoeinstellungen — Tab Konto (/settings/account?tab=account)
  - Platform-Admin-Panel (Service Accounts, Tenant-Notfallverwaltung)
  - Tenant-Settings Service Accounts (/t/{slug}/settings/service-accounts)
  - Route Guards (ProtectedRoute, PublicOnlyRoute)
generated: 2026-03-21
version: "1.8"
spec_source: spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md
---

# Testfälle: REQ-023 — Benutzerverwaltung & Authentifizierung

Diese Datei enthält alle E2E-Testfälle für die Benutzerverwaltung und Authentifizierung aus der Perspektive eines Nutzers im Browser. Jeder Testfall beschreibt ausschließlich sichtbare UI-Interaktionen und beobachtbare Ergebnisse auf dem Bildschirm.

**Testdaten (Demo-Umgebung):**
- Demo-Nutzer: `demo@kamerplanter.local` / `demo-passwort-2024`
- Demo-Account ist `status: active`, E-Mail verifiziert

---

## Abschnitt 1: Registrierung

### TC-023-001: Erfolgreiche lokale Registrierung (Happy Path)

**Requirement**: REQ-023 §1.1 Szenario 1, AK-01
**Priority**: Critical
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist nicht angemeldet
- Die URL `/register` ist im Browser aufrufbar
- Die E-Mail-Adresse `neuer-gaertner@example.com` existiert noch nicht im System

**Testschritte**:
1. Nutzer navigiert zu `/register`
2. Seite lädt: Überschrift "Registrieren" ist sichtbar
3. Nutzer gibt in das Feld "Anzeigename" den Wert `Neuer Gärtner` ein
4. Nutzer gibt in das Feld "E-Mail" den Wert `neuer-gaertner@example.com` ein
5. Nutzer gibt in das Feld "Passwort" den Wert `sicheres-passwort-2024` ein (10+ Zeichen)
6. Nutzer gibt in das Feld "Passwort bestätigen" denselben Wert ein
7. Nutzer klickt auf "Registrieren"

**Erwartete Ergebnisse**:
- Der "Registrieren"-Button zeigt während der Verarbeitung einen Ladeindikator (CircularProgress)
- Nach erfolgreicher Verarbeitung erscheint ein grünes Snackbar mit dem Text "Registrierung erfolgreich! Bitte prüfen Sie Ihre E-Mails."
- Nutzer wird automatisch zur Seite `/login` weitergeleitet
- Auf `/login` ist kein Fehler-Alert sichtbar

**Nachbedingungen**:
- Ein neuer Nutzer-Account existiert im System mit unverifiziertem Status
- Eine Verifizierungs-E-Mail wurde versendet

**Tags**: [REQ-023, registrierung, happy-path, formular, auth]

---

### TC-023-002: Registrierung — Passwörter stimmen nicht überein

**Requirement**: REQ-023 §4.2 RegisterPage (Frontend-Validierung)
**Priority**: High
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer ist nicht angemeldet und befindet sich auf `/register`

**Testschritte**:
1. Nutzer gibt "Anzeigename": `Test User` ein
2. Nutzer gibt "E-Mail": `test@example.com` ein
3. Nutzer gibt "Passwort": `passwort-2024` ein
4. Nutzer gibt "Passwort bestätigen": `anderes-passwort` ein
5. Nutzer klickt auf "Registrieren"

**Erwartete Ergebnisse**:
- Ein roter Alert-Banner erscheint mit dem Text "Passwörter stimmen nicht überein"
- Es erfolgt kein Seitenwechsel
- Kein Snackbar mit Erfolgsmeldung erscheint

**Nachbedingungen**:
- Kein neuer Account wurde erstellt

**Tags**: [REQ-023, registrierung, validierung, passwort-mismatch]

---

### TC-023-003: Registrierung — Passwort zu kurz (Hinweistext)

**Requirement**: REQ-023 §1 Passwort-Policy (Mindestlänge 10 Zeichen), AK-01
**Priority**: High
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer befindet sich auf `/register`

**Testschritte**:
1. Nutzer klickt auf das Passwort-Feld
2. Nutzer liest den Hilfetext unterhalb des Passwort-Felds

**Erwartete Ergebnisse**:
- Unterhalb des Passwort-Felds ist der Hilfetext "Mindestens 10 Zeichen" sichtbar
- Nutzer wird über die Mindestanforderung vor dem Absenden informiert

**Nachbedingungen**: keine

**Tags**: [REQ-023, registrierung, passwort-policy, hinweistext]

---

### TC-023-004: Registrierung — Pflichtfelder leer gelassen (Browser-Validierung)

**Requirement**: REQ-023 §4.2 RegisterPage
**Priority**: Medium
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer befindet sich auf `/register`

**Testschritte**:
1. Nutzer lässt alle Felder leer
2. Nutzer klickt auf "Registrieren"

**Erwartete Ergebnisse**:
- Der Browser zeigt eine native HTML5-Validierungswarnung am ersten leeren Pflichtfeld
- Es erfolgt kein API-Request (kein Ladeindikator)
- Kein Seitenwechsel findet statt

**Tags**: [REQ-023, registrierung, validierung, pflichtfelder]

---

### TC-023-005: Registrierung — E-Mail-Adresse bereits registriert (Enumeration-Schutz)

**Requirement**: REQ-023 §3.2 AuthService.register_local SEC-H-009, AK-01
**Priority**: High
**Category**: Fehlermeldung / Sicherheit

**Vorbedingungen**:
- Die E-Mail `demo@kamerplanter.local` ist bereits registriert
- Nutzer befindet sich auf `/register`

**Testschritte**:
1. Nutzer gibt "Anzeigename": `Demo Kopie` ein
2. Nutzer gibt "E-Mail": `demo@kamerplanter.local` ein (bereits vorhanden)
3. Nutzer gibt "Passwort": `sicheres-passwort-2024` ein
4. Nutzer gibt "Passwort bestätigen": `sicheres-passwort-2024` ein
5. Nutzer klickt "Registrieren"

**Erwartete Ergebnisse**:
- Das System zeigt dieselbe Erfolgsmeldung wie bei einer echten Neuregistrierung: Snackbar "Registrierung erfolgreich! Bitte prüfen Sie Ihre E-Mails."
- Nutzer wird zu `/login` weitergeleitet
- Es erscheint KEIN Fehler-Alert mit "E-Mail bereits vorhanden" oder ähnlichem (Enumeration-Schutz)

**Nachbedingungen**:
- Kein zweiter Account wurde erstellt
- An die existierende Adresse wurde serverseitig eine Info-E-Mail gesendet (nicht prüfbar im Browser)

**Tags**: [REQ-023, registrierung, sicherheit, enumeration-schutz, SEC-H-009]

---

### TC-023-006: Link zu Login von der Registrierungsseite

**Requirement**: REQ-023 §4.2 RegisterPage
**Priority**: Low
**Category**: Navigation

**Vorbedingungen**:
- Nutzer befindet sich auf `/register`

**Testschritte**:
1. Nutzer klickt auf den Link "Bereits registriert? Anmelden"

**Erwartete Ergebnisse**:
- Nutzer wird zu `/login` weitergeleitet
- Login-Seite mit Überschrift "Anmelden" ist sichtbar

**Tags**: [REQ-023, navigation, registrierung, login-link]

---

## Abschnitt 2: E-Mail-Verifizierung

### TC-023-007: Erfolgreiche E-Mail-Verifizierung (Happy Path)

**Requirement**: REQ-023 §1.1 Szenario 1 (Schritt 5), AK-02
**Priority**: Critical
**Category**: Happy Path

**Vorbedingungen**:
- Ein Nutzer hat sich registriert, hat aber noch keine E-Mail verifiziert
- Ein gültiger Verifizierungs-Token liegt vor (z.B. aus der ConsoleEmailAdapter-Ausgabe in der Entwicklungsumgebung)

**Testschritte**:
1. Nutzer navigiert zu `/verify-email/{gueltiger-token}`
2. Seite lädt mit Überschrift "E-Mail-Verifizierung"
3. Die Seite verarbeitet automatisch den Token aus der URL

**Erwartete Ergebnisse**:
- Ein grüner Erfolgs-Alert erscheint: "E-Mail erfolgreich verifiziert! Sie können sich jetzt anmelden."
- Ein Link "Zurück zur Anmeldung" ist sichtbar
- Nutzer kann auf den Link klicken und wird zu `/login` weitergeleitet

**Nachbedingungen**:
- Nutzer-Account hat `status: active` und `email_verified: true`

**Tags**: [REQ-023, verifizierung, happy-path, email]

---

### TC-023-008: E-Mail-Verifizierung mit ungültigem Token

**Requirement**: REQ-023 §3.2 AuthService.verify_email, AK-02
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer hat einen abgelaufenen oder falschen Token

**Testschritte**:
1. Nutzer navigiert zu `/verify-email/ungueltigertoken123`
2. Seite lädt mit Überschrift "E-Mail-Verifizierung"

**Erwartete Ergebnisse**:
- Ein roter Fehler-Alert erscheint mit dem Text "Ungültiger oder abgelaufener Token"
- Ein Link "Zurück zur Anmeldung" ist sichtbar
- Es erscheint KEIN Erfolgsmeldung

**Tags**: [REQ-023, verifizierung, fehler, ungueltig-token]

---

## Abschnitt 3: Login

### TC-023-009: Erfolgreicher lokaler Login (Happy Path)

**Requirement**: REQ-023 §1.1 Szenario 1, AK-03, FK-02
**Priority**: Critical
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist nicht angemeldet
- Demo-Account `demo@kamerplanter.local` / `demo-passwort-2024` existiert und ist aktiv

**Testschritte**:
1. Nutzer navigiert zu `/login`
2. Seite zeigt Überschrift "Anmelden" und E-Mail/Passwort-Felder
3. Nutzer gibt "E-Mail": `demo@kamerplanter.local` ein
4. Nutzer gibt "Passwort": `demo-passwort-2024` ein
5. Checkbox "Angemeldet bleiben" bleibt deaktiviert (Standard)
6. Nutzer klickt "Anmelden"

**Erwartete Ergebnisse**:
- Der "Anmelden"-Button zeigt während der Verarbeitung einen Ladeindikator
- Nach erfolgreichem Login wird der Nutzer zu `/dashboard` weitergeleitet
- Das Dashboard ist sichtbar und zeigt den eingeloggten Zustand (z.B. Navigation, Nutzer-Name in der AppBar)
- Kein Fehler-Alert ist sichtbar

**Nachbedingungen**:
- Nutzer ist eingeloggt, Session ist aktiv (Session-Cookie, da `remember_me=false`)

**Tags**: [REQ-023, login, happy-path, auth]

---

### TC-023-010: Login mit aktivierter "Angemeldet bleiben"-Checkbox

**Requirement**: REQ-023 §1.1 Szenario 5, AK-03, FK-01a
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist nicht angemeldet und befindet sich auf `/login`

**Testschritte**:
1. Nutzer gibt "E-Mail": `demo@kamerplanter.local` ein
2. Nutzer gibt "Passwort": `demo-passwort-2024` ein
3. Nutzer findet die Checkbox "Angemeldet bleiben" unterhalb des Passwort-Felds
4. Die Checkbox ist standardmäßig nicht aktiviert — Nutzer aktiviert sie per Klick
5. Nutzer bewegt die Maus über die Checkbox und sieht den Tooltip
6. Nutzer klickt "Anmelden"

**Erwartete Ergebnisse**:
- Die Checkbox "Angemeldet bleiben" ist unterhalb des Passwort-Felds und oberhalb des Anmelden-Buttons sichtbar
- Der Tooltip lautet: "Aktivieren Sie diese Option nur auf privaten Geräten. Ihre Sitzung bleibt bis zu 30 Tage aktiv."
- Login ist erfolgreich, Nutzer wird zu `/dashboard` weitergeleitet
- Serverseitig wird ein persistentes Refresh Token mit 30-Tage-TTL erstellt (nicht direkt im Browser prüfbar, aber Session überlebt Browser-Neustart)

**Tags**: [REQ-023, login, remember-me, persistent-session, FK-01a]

---

### TC-023-011: Login-Seite zeigt SSO-Provider-Buttons (wenn konfiguriert)

**Requirement**: REQ-023 §4.2 LoginPage, FK-01
**Priority**: High
**Category**: Listenansicht

**Vorbedingungen**:
- Mindestens ein OAuth-Provider ist aktiviert (z.B. Google mit `enabled: true` und gesetzten Credentials)
- Nutzer ist nicht angemeldet

**Testschritte**:
1. Nutzer navigiert zu `/login`
2. Nutzer scrollt bis unterhalb des "Anmelden"-Buttons

**Erwartete Ergebnisse**:
- Ein Divider mit dem Text "oder" ist sichtbar
- Für jeden aktivierten OAuth-Provider erscheint ein eigener Button: "Anmelden mit Google" / "Anmelden mit GitHub" / etc.
- Buttons sind klar beschriftet mit dem Provider-Namen
- Kein SSO-Button erscheint für deaktivierte Provider

**Tags**: [REQ-023, login, sso, oauth-buttons, FK-01]

---

### TC-023-012: Login-Seite ohne aktivierte SSO-Provider

**Requirement**: REQ-023 §4.2 LoginPage, §5 Seed-Daten (enabled: false)
**Priority**: Medium
**Category**: Listenansicht

**Vorbedingungen**:
- Keine OAuth-Provider sind aktiviert (Standard-Auslieferungszustand: alle Provider `enabled: false`)
- Nutzer ist nicht angemeldet

**Testschritte**:
1. Nutzer navigiert zu `/login`
2. Nutzer schaut auf die gesamte Login-Karte

**Erwartete Ergebnisse**:
- Der Divider "oder" ist NICHT sichtbar
- Keine SSO-Buttons erscheinen
- Nur E-Mail/Passwort-Formular, Checkbox "Angemeldet bleiben", "Anmelden"-Button und die Links "Noch kein Konto? Registrieren" sowie "Passwort vergessen?" sind sichtbar

**Tags**: [REQ-023, login, sso, kein-provider]

---

### TC-023-013: Login mit falschem Passwort

**Requirement**: REQ-023 §3.2 AuthService.login_local, AK-05
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer befindet sich auf `/login`
- Account `demo@kamerplanter.local` existiert

**Testschritte**:
1. Nutzer gibt "E-Mail": `demo@kamerplanter.local` ein
2. Nutzer gibt "Passwort": `falsches-passwort-xyz` ein
3. Nutzer klickt "Anmelden"

**Erwartete Ergebnisse**:
- Ein roter Fehler-Alert erscheint in der Login-Karte mit einer Fehlermeldung (z.B. "Ungültige Zugangsdaten")
- Nutzer bleibt auf `/login`
- Es erfolgt kein Redirect zu `/dashboard`

**Tags**: [REQ-023, login, fehler, falsches-passwort]

---

### TC-023-014: Account-Sperre nach 5 Fehlversuchen

**Requirement**: REQ-023 §3.1 LoginThrottleEngine, AK-05
**Priority**: High
**Category**: Zustandswechsel / Sicherheit

**Vorbedingungen**:
- Ein existierender Account mit der E-Mail `test-brute@example.com` ist vorhanden
- Der Account wurde noch nicht gesperrt (0 Fehlversuche)

**Testschritte**:
1. Nutzer navigiert zu `/login`
2. Nutzer gibt `test-brute@example.com` und ein falsches Passwort ein — klickt "Anmelden" (1. Versuch)
3. Schritte 1-2 werden 4 weitere Male wiederholt (insgesamt 5 Fehlversuche)
4. Nutzer versucht den 6. Login-Versuch (diesmal mit dem richtigen Passwort)

**Erwartete Ergebnisse**:
- Nach dem 5. Fehlversuch erscheint ein Fehler-Alert mit einer Sperr-Meldung (z.B. "Zu viele Fehlversuche. Bitte versuchen Sie es in 15 Minuten erneut.")
- Auch der 6. Versuch (mit korrektem Passwort) schlägt fehl, solange die Sperre aktiv ist
- Kein Redirect zum Dashboard erfolgt

**Tags**: [REQ-023, login, brute-force, account-sperre, AK-05]

---

### TC-023-015: Login mit nicht-verifiziertem Account

**Requirement**: REQ-023 §1 E-Mail-Verifizierung
**Priority**: Medium
**Category**: Fehlermeldung

**Vorbedingungen**:
- Ein Nutzer hat sich registriert, aber die Verifizierungs-E-Mail noch nicht bestätigt (Status: `unverified`)

**Testschritte**:
1. Nutzer navigiert zu `/login`
2. Nutzer gibt E-Mail und Passwort des unverifiziertes Accounts ein
3. Nutzer klickt "Anmelden"

**Erwartete Ergebnisse**:
- Ein roter Fehler-Alert erscheint mit einer Meldung, dass das Konto noch nicht verifiziert wurde (oder generische Fehlermeldung)
- Kein Redirect zum Dashboard

**Tags**: [REQ-023, login, unverifiziert, fehler]

---

### TC-023-016: Redirect von geschützter Route zu Login

**Requirement**: REQ-023 §4.5 ProtectedRoute Route Guard, FK-02 (implizit)
**Priority**: High
**Category**: Navigation / Route Guard

**Vorbedingungen**:
- Nutzer ist nicht angemeldet

**Testschritte**:
1. Nutzer navigiert direkt zu `/dashboard` (ohne vorherigen Login)

**Erwartete Ergebnisse**:
- Nutzer wird automatisch zu `/login` weitergeleitet
- Die Login-Seite ist sichtbar
- Das Dashboard wird nicht angezeigt

**Tags**: [REQ-023, route-guard, protected-route, redirect, navigation]

---

### TC-023-017: Redirect von Login/Register zu Dashboard wenn bereits eingeloggt

**Requirement**: REQ-023 §4.5 PublicOnlyRoute Route Guard
**Priority**: Medium
**Category**: Navigation / Route Guard

**Vorbedingungen**:
- Nutzer ist eingeloggt (z.B. als Demo-Nutzer)

**Testschritte**:
1. Nutzer navigiert zu `/login` (obwohl bereits eingeloggt)

**Erwartete Ergebnisse**:
- Nutzer wird automatisch zu `/dashboard` weitergeleitet
- Die Login-Seite wird NICHT angezeigt

**Tags**: [REQ-023, route-guard, public-only-route, redirect]

---

### TC-023-018: SSO-Login mit Google (OAuth2-Flow-Start)

**Requirement**: REQ-023 §1.1 Szenario 2, AK-08
**Priority**: High
**Category**: Happy Path / Navigation

**Vorbedingungen**:
- Google-Provider ist aktiviert (auf Entwicklungs-/Testumgebung mit Testcredentials konfiguriert)
- Nutzer ist nicht angemeldet und befindet sich auf `/login`

**Testschritte**:
1. Nutzer sieht den Button "Anmelden mit Google" unterhalb des Dividers "oder"
2. Nutzer klickt auf "Anmelden mit Google"

**Erwartete Ergebnisse**:
- Der Browser navigiert zur Google OAuth2 Consent-Seite (Redirect zu `accounts.google.com/...`)
- Die Kamerplanter-URL ist verlassen, die URL zeigt auf Google

**Hinweis**: Der vollständige OAuth-Flow (Google-Login → Callback → Dashboard) setzt Testcredentials voraus und ist ein Integrations-/E2E-Test. Das Prüfen des Redirects zu Google ist das Minimalziel dieses Testfalls.

**Tags**: [REQ-023, sso, oauth, google, redirect]

---

### TC-023-019: Passwort vergessen — Link auf Login-Seite

**Requirement**: REQ-023 §4.2 LoginPage
**Priority**: Medium
**Category**: Navigation

**Vorbedingungen**:
- Nutzer befindet sich auf `/login`

**Testschritte**:
1. Nutzer klickt auf den Link "Passwort vergessen?"

**Erwartete Ergebnisse**:
- Nutzer wird zu `/password-reset` weitergeleitet
- Seite mit Überschrift "Passwort zurücksetzen" und einem E-Mail-Eingabefeld ist sichtbar

**Tags**: [REQ-023, navigation, passwort-reset, link]

---

## Abschnitt 4: Passwort-Reset

### TC-023-020: Passwort-Reset anfordern — bekannte E-Mail (Enumeration-Schutz)

**Requirement**: REQ-023 §1.1 Szenario 7, AK-06, SK-05
**Priority**: High
**Category**: Happy Path / Sicherheit

**Vorbedingungen**:
- Nutzer befindet sich auf `/password-reset`
- Die E-Mail `demo@kamerplanter.local` existiert im System

**Testschritte**:
1. Nutzer gibt "E-Mail": `demo@kamerplanter.local` ein
2. Nutzer klickt "Reset-Link senden"

**Erwartete Ergebnisse**:
- Der Button zeigt kurzzeitig einen Ladeindikator
- Ein grüner Erfolgs-Alert erscheint: "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet."
- Das E-Mail-Formular verschwindet, stattdessen sind der Erfolgs-Alert und ein Link "Zurück zur Anmeldung" sichtbar
- Es wird KEINE direkte Bestätigung gegeben, ob die E-Mail existiert (Enumeration-Schutz)

**Tags**: [REQ-023, passwort-reset, enumeration-schutz, SK-05]

---

### TC-023-021: Passwort-Reset anfordern — unbekannte E-Mail (Enumeration-Schutz)

**Requirement**: REQ-023 §3.2 AuthService.request_password_reset, SK-05
**Priority**: High
**Category**: Sicherheit

**Vorbedingungen**:
- Nutzer befindet sich auf `/password-reset`
- Die E-Mail `nicht-vorhanden@example.com` existiert NICHT im System

**Testschritte**:
1. Nutzer gibt "E-Mail": `nicht-vorhanden@example.com` ein
2. Nutzer klickt "Reset-Link senden"

**Erwartete Ergebnisse**:
- Die Antwort im Browser ist identisch zu TC-023-020: derselbe Erfolgs-Alert "Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet."
- Es erscheint KEIN Fehler-Alert "E-Mail nicht gefunden"
- Kein Unterschied zur bekannten E-Mail sichtbar (Enumeration-Schutz)

**Tags**: [REQ-023, passwort-reset, enumeration-schutz, SK-05, sicherheit]

---

### TC-023-022: Zurück zur Anmeldung von Passwort-Reset-Seite

**Requirement**: REQ-023 §4.2 PasswordResetRequestPage
**Priority**: Low
**Category**: Navigation

**Vorbedingungen**:
- Nutzer befindet sich auf `/password-reset`

**Testschritte**:
1. Nutzer klickt auf "Zurück zur Anmeldung"

**Erwartete Ergebnisse**:
- Nutzer wird zu `/login` weitergeleitet

**Tags**: [REQ-023, navigation, passwort-reset, back-link]

---

### TC-023-023: Neues Passwort setzen — Happy Path

**Requirement**: REQ-023 §1.1 Szenario 7, AK-06, AK-07
**Priority**: Critical
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer hat einen gültigen Passwort-Reset-Token (aus ConsoleEmailAdapter-Ausgabe in Entwicklung)
- Token ist noch nicht abgelaufen (max. 1 Stunde gültig)

**Testschritte**:
1. Nutzer navigiert zu `/password-reset/{gueltiger-token}`
2. Seite zeigt Überschrift "Neues Passwort festlegen" und zwei Passwort-Felder
3. Nutzer gibt "Passwort": `neues-sicheres-passwort-2024` ein
4. Nutzer gibt "Passwort bestätigen": `neues-sicheres-passwort-2024` ein
5. Nutzer klickt "Passwort speichern"

**Erwartete Ergebnisse**:
- Ein grünes Snackbar erscheint: "Passwort erfolgreich zurückgesetzt"
- Nutzer wird zu `/login` weitergeleitet
- Nutzer kann sich jetzt mit dem neuen Passwort anmelden

**Nachbedingungen**:
- Das alte Passwort ist ungültig
- Alle bestehenden Refresh Tokens des Nutzers sind serverseitig invalidiert (andere Geräte werden ausgeloggt)

**Tags**: [REQ-023, passwort-reset, neues-passwort, happy-path, AK-07]

---

### TC-023-024: Neues Passwort — Passwörter stimmen nicht überein

**Requirement**: REQ-023 §4.2 PasswordResetConfirmPage
**Priority**: High
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer befindet sich auf `/password-reset/{gueltiger-token}`

**Testschritte**:
1. Nutzer gibt "Passwort": `neues-passwort-2024` ein
2. Nutzer gibt "Passwort bestätigen": `anderes-passwort` ein
3. Nutzer klickt "Passwort speichern"

**Erwartete Ergebnisse**:
- Ein roter Fehler-Alert erscheint: "Passwörter stimmen nicht überein"
- Kein Seitenwechsel
- Kein Snackbar mit Erfolgsmeldung

**Tags**: [REQ-023, passwort-reset, validierung, mismatch]

---

### TC-023-025: Neues Passwort — Token ungültig

**Requirement**: REQ-023 AK-06 (Token einmalig verwendbar)
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Ein abgelaufener oder bereits verwendeter Token liegt vor

**Testschritte**:
1. Nutzer navigiert zu `/password-reset/abgelaufener-oder-benutzter-token`
2. Nutzer gibt ein neues Passwort in beide Felder ein
3. Nutzer klickt "Passwort speichern"

**Erwartete Ergebnisse**:
- Ein roter Fehler-Alert erscheint (z.B. "Ungültiger oder abgelaufener Token")
- Kein Redirect, kein Erfolgs-Snackbar

**Tags**: [REQ-023, passwort-reset, ungueltig-token, fehler]

---

## Abschnitt 5: Kontoeinstellungen — Tab Profil

### TC-023-026: Profil anzeigen (Happy Path)

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Profil", AK-15
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Nutzer ist als Demo-Nutzer eingeloggt

**Testschritte**:
1. Nutzer navigiert zu `/settings/account`
2. Der Tab "Profil" ist standardmäßig aktiv (oder Nutzer klickt auf Tab "Profil")

**Erwartete Ergebnisse**:
- Tab-Leiste mit den Tabs ist sichtbar (im Full-Modus: Profil, Sicherheit, Sitzungen, API-Schlüssel, Erfahrungsstufe, Integrationen, Plattform-Modus, Konto)
- Im Profil-Tab ist ein Formular mit den Feldern "Anzeigename", Sprache (Dropdown DE/EN), Zeitzone sichtbar
- Das "Anzeigename"-Feld ist mit dem aktuellen Namen des Nutzers vorausgefüllt
- Ein "Speichern"-Button ist vorhanden

**Tags**: [REQ-023, konto-einstellungen, profil, detailansicht]

---

### TC-023-027: Anzeigename ändern und speichern

**Requirement**: REQ-023 §3.2 UserService.update_profile, AK-15
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist eingeloggt und befindet sich auf `/settings/account` im Tab "Profil"

**Testschritte**:
1. Nutzer löscht den aktuellen Inhalt im Feld "Anzeigename"
2. Nutzer gibt `Aktualisierter Gärtner` ein
3. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Ein grünes Snackbar mit "Gespeichert" oder ähnlichem erscheint
- Das Feld "Anzeigename" zeigt weiterhin `Aktualisierter Gärtner`
- Die AppBar oder ein anderer sichtbarer Bereich mit dem Nutzernamen aktualisiert sich

**Tags**: [REQ-023, konto-einstellungen, profil, anzeigename, AK-15]

---

### TC-023-028: Sprache auf Englisch umstellen (Profil-Tab)

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Profil"
**Priority**: Medium
**Category**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt und befindet sich im Tab "Profil"

**Testschritte**:
1. Nutzer findet das Sprache-Dropdown und wählt "Englisch" (EN)
2. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar erscheint
- Die UI-Sprache wechselt zu Englisch (Menüpunkte, Labels werden auf Englisch angezeigt)

**Tags**: [REQ-023, konto-einstellungen, profil, sprache, i18n]

---

## Abschnitt 6: Kontoeinstellungen — Tab Sicherheit

### TC-023-029: Passwort ändern (lokales Passwort vorhanden)

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Sicherheit", AK-15
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist eingeloggt als Demo-Nutzer (hat lokales Passwort)
- Nutzer befindet sich auf `/settings/account` im Tab "Sicherheit"

**Testschritte**:
1. Nutzer sieht den Bereich "Passwort" mit den Feldern "Aktuelles Passwort" und "Neues Passwort"
2. Nutzer gibt "Aktuelles Passwort": `demo-passwort-2024` ein
3. Nutzer gibt "Neues Passwort": `neues-demo-passwort-2025` ein
4. Nutzer klickt "Passwort ändern"

**Erwartete Ergebnisse**:
- Ein grünes Snackbar erscheint: "Passwort geändert. Alle Sitzungen wurden beendet."
- Die Passwort-Felder werden geleert
- Nutzer bleibt auf der Seite (die aktuelle Session ist noch gültig — nur andere Sessions wurden beendet)

**Tags**: [REQ-023, sicherheit, passwort-aendern, happy-path]

---

### TC-023-030: Passwort ändern mit falschem aktuellem Passwort

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Sicherheit"
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer ist eingeloggt, befindet sich im Tab "Sicherheit"

**Testschritte**:
1. Nutzer gibt "Aktuelles Passwort": `falsches-passwort` ein
2. Nutzer gibt "Neues Passwort": `neues-passwort-2024` ein
3. Nutzer klickt "Passwort ändern"

**Erwartete Ergebnisse**:
- Ein roter Alert erscheint (z.B. "Aktuelles Passwort ist falsch" oder generischer Fehler)
- Kein Snackbar mit Erfolgsmeldung

**Tags**: [REQ-023, sicherheit, passwort-aendern, fehler]

---

### TC-023-031: Lokales Passwort für SSO-only-Account hinzufügen

**Requirement**: REQ-023 §1.1 Szenario 4, AK-15 (implizit), §3.2 AuthService.add_local_password
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist über SSO (z.B. Google) eingeloggt und hat KEIN lokales Passwort
- Nutzer befindet sich im Tab "Sicherheit"

**Testschritte**:
1. Nutzer sieht den Bereich "Passwort" — das Feld "Aktuelles Passwort" ist NICHT vorhanden (kein lokales Passwort)
2. Nur das Feld "Neues Passwort" ist sichtbar
3. Nutzer gibt "Neues Passwort": `neues-lokales-passwort-2024` ein
4. Nutzer klickt "Passwort festlegen"

**Erwartete Ergebnisse**:
- Ein Erfolgs-Snackbar erscheint
- In der Provider-Liste erscheint jetzt auch "Lokal" als verknüpfter Provider
- Nutzer kann sich ab sofort auch mit E-Mail + Passwort anmelden

**Tags**: [REQ-023, sicherheit, lokales-passwort, sso-account, account-linking]

---

### TC-023-032: Verknüpfte Auth-Provider anzeigen

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Sicherheit", FK-04
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt, befindet sich im Tab "Sicherheit"
- Nutzer hat mindestens einen verknüpften Provider (z.B. "lokal")

**Testschritte**:
1. Nutzer scrollt im Tab "Sicherheit" zur Liste der verknüpften Auth-Provider

**Erwartete Ergebnisse**:
- Eine Liste "Verbundene Anmeldemethoden" (o.ä.) ist sichtbar
- Für jeden verknüpften Provider erscheint ein Eintrag mit Provider-Name und Datum der Verknüpfung
- Jeder Provider-Eintrag hat einen "Entfernen"-Button (wenn mehrere Provider vorhanden)

**Tags**: [REQ-023, sicherheit, provider, detailansicht, FK-04]

---

### TC-023-033: Letzten Auth-Provider entfernen — verhindert

**Requirement**: REQ-023 §1 Account-Linking (mindestens eine Methode), AK-13
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt und hat genau EINEN Auth-Provider (z.B. nur "lokal")
- Nutzer befindet sich im Tab "Sicherheit"

**Testschritte**:
1. Nutzer sieht den einen verknüpften Provider in der Liste
2. Nutzer prüft ob der "Entfernen"-Button vorhanden ist

**Erwartete Ergebnisse**:
- Der "Entfernen"-Button ist entweder nicht sichtbar ODER deaktiviert (disabled) wenn nur ein Provider vorhanden ist
- Wenn der Button doch klickbar ist und Nutzer klickt: Ein Fehler-Snackbar erscheint (z.B. "Mindestens eine Anmeldemethode muss erhalten bleiben")

**Tags**: [REQ-023, sicherheit, provider-entfernen, letzte-methode, AK-13]

---

### TC-023-034: Auth-Provider entfernen (wenn mehrere vorhanden)

**Requirement**: REQ-023 §3.2 AuthService.unlink_provider
**Priority**: Medium
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer hat zwei verknüpfte Provider (z.B. "lokal" + "Google")
- Nutzer befindet sich im Tab "Sicherheit"

**Testschritte**:
1. Nutzer klickt auf "Entfernen" beim Google-Provider
2. Ein Bestätigungs-Dialog erscheint
3. Nutzer bestätigt die Aktion

**Erwartete Ergebnisse**:
- Der Google-Eintrag verschwindet aus der Provider-Liste
- Ein Erfolgs-Snackbar erscheint
- Der lokale Provider bleibt in der Liste

**Tags**: [REQ-023, sicherheit, provider-entfernen, happy-path]

---

## Abschnitt 7: Kontoeinstellungen — Tab Sitzungen

### TC-023-035: Aktive Sitzungen anzeigen

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "Sessions", FK-04
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt, befindet sich im Tab "Sitzungen"

**Testschritte**:
1. Nutzer klickt auf den Tab "Sitzungen"
2. Seite lädt die Session-Liste

**Erwartete Ergebnisse**:
- Eine Liste aktiver Sitzungen ist sichtbar
- Jede Sitzung zeigt: Geräteinformationen (User-Agent), IP-Adresse (oder anonymisiert), Zeitpunkt der Erstellung, "Angemeldet bleiben: Ja/Nein"
- Die aktuelle Sitzung ist als aktuelle gekennzeichnet (oder hat einen anderen visuellen Hinweis)
- Ein "Beenden"-Button ist bei jeder Sitzung vorhanden (außer ggf. der aktuellen)

**Tags**: [REQ-023, sitzungen, detailansicht, FK-04]

---

### TC-023-036: Einzelne fremde Sitzung beenden

**Requirement**: REQ-023 §3.2 UserService, §4.2 Tab "Sessions"
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist von mindestens zwei Geräten eingeloggt
- Nutzer befindet sich auf Gerät A, Tab "Sitzungen"
- Gerät B's Session ist in der Liste sichtbar

**Testschritte**:
1. Nutzer klickt auf "Beenden" neben der Session von Gerät B
2. Bestätigungs-Dialog erscheint
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Die Session von Gerät B verschwindet aus der Liste
- Ein Erfolgs-Snackbar erscheint
- Die aktuelle Session auf Gerät A bleibt bestehen

**Tags**: [REQ-023, sitzungen, sitzung-beenden, zustandswechsel]

---

## Abschnitt 8: Kontoeinstellungen — Tab API-Schlüssel

### TC-023-037: API-Schlüssel-Liste — Leerzustand

**Requirement**: REQ-023 §4.2 AccountSettingsPage Tab "API-Keys" (Leerzustand)
**Priority**: Medium
**Category**: Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt ohne vorhandene API-Keys
- Nutzer befindet sich im Tab "API-Schlüssel"

**Testschritte**:
1. Nutzer klickt auf den Tab "API-Schlüssel"
2. Nutzer betrachtet den Inhalt der Seite

**Erwartete Ergebnisse**:
- Eine Leerzustand-Meldung ist sichtbar (z.B. "Keine API-Keys vorhanden. Erstellen Sie einen Key für Home Assistant, Monitoring oder andere Anwendungen.")
- Ein "Neuen Schlüssel erstellen"-Button ist vorhanden

**Tags**: [REQ-023, api-schluessel, leerzustand, FK-06]

---

### TC-023-038: API-Schlüssel erstellen (Happy Path) — Einmalige Anzeige

**Requirement**: REQ-023 §3.7, §4.2 Tab "API-Keys", AK, FK-07
**Priority**: Critical
**Category**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist eingeloggt, befindet sich im Tab "API-Schlüssel"

**Testschritte**:
1. Nutzer klickt auf "Neuen Schlüssel erstellen"
2. Ein Dialog öffnet sich mit einem "Bezeichnung"-Eingabefeld
3. Nutzer gibt "Bezeichnung": `Home Assistant Growzelt` ein
4. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Ein neuer Dialog erscheint und zeigt den vollständigen API-Key im Klartext (beginnt mit `kp_`)
- Der Warnhinweis "Kopieren Sie diesen Schlüssel jetzt — er wird nicht erneut angezeigt!" ist deutlich sichtbar
- Ein "Kopieren"-Button (Zwischenablage-Icon) ist neben dem Key vorhanden
- Nach dem Schließen dieses Dialogs ist der Klartext-Key nicht mehr abrufbar
- In der API-Schlüssel-Liste erscheint ein neuer Eintrag "Home Assistant Growzelt" mit Key-Prefix (z.B. `kp_a3f8...`), Erstelldatum und "Nie verwendet"

**Tags**: [REQ-023, api-schluessel, erstellen, happy-path, einmalig-anzeige, FK-07]

---

### TC-023-039: API-Schlüssel-Dialog — Bezeichnung leer gelassen

**Requirement**: REQ-023 §4.2 Tab "API-Keys"
**Priority**: Medium
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer hat den "Neuen Schlüssel erstellen"-Dialog geöffnet

**Testschritte**:
1. Nutzer lässt das "Bezeichnung"-Feld leer
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Browser-native Validierung oder ein Fehler-Hinweis im Dialog erscheint
- Kein Key wird erstellt, Dialog bleibt geöffnet

**Tags**: [REQ-023, api-schluessel, validierung, pflichtfeld]

---

### TC-023-040: API-Schlüssel widerrufen mit Bestätigung

**Requirement**: REQ-023 §3.7, §4.2 Tab "API-Keys", FK-08
**Priority**: High
**Category**: Dialog / Zustandswechsel

**Vorbedingungen**:
- Nutzer hat mindestens einen API-Key in der Liste
- Nutzer befindet sich im Tab "API-Schlüssel"

**Testschritte**:
1. Nutzer klickt auf das Löschen/Widerrufen-Icon neben einem API-Key
2. Ein Bestätigungs-Dialog erscheint

**Erwartete Ergebnisse**:
- Der Bestätigungs-Dialog enthält eine Warnung (z.B. "API-Key 'Home Assistant Growzelt' wirklich widerrufen? Alle Anwendungen die diesen Key verwenden verlieren sofort den Zugriff.")
- Dialog hat "Bestätigen" und "Abbrechen"-Button

**Tags**: [REQ-023, api-schluessel, widerrufen, bestaetigungs-dialog, FK-08]

---

### TC-023-041: API-Schlüssel widerrufen — Bestätigung

**Requirement**: REQ-023 §3.7, §4.2 Tab "API-Keys", FK-08
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Bestätigungs-Dialog aus TC-023-040 ist geöffnet

**Testschritte**:
1. Nutzer klickt auf "Bestätigen" im Widerrufen-Dialog

**Erwartete Ergebnisse**:
- Der API-Key verschwindet aus der Liste (oder wird als "Widerrufen" markiert)
- Ein Erfolgs-Snackbar erscheint: "API-Schlüssel widerrufen"
- Dialog schließt sich

**Tags**: [REQ-023, api-schluessel, widerrufen, zustandswechsel, FK-08]

---

### TC-023-042: API-Schlüssel widerrufen — Abbrechen

**Requirement**: REQ-023 §4.2 Tab "API-Keys"
**Priority**: Low
**Category**: Dialog

**Vorbedingungen**:
- Bestätigungs-Dialog aus TC-023-040 ist geöffnet

**Testschritte**:
1. Nutzer klickt auf "Abbrechen" im Dialog

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Der API-Key bleibt in der Liste — er wurde NICHT widerrufen

**Tags**: [REQ-023, api-schluessel, widerrufen, abbrechen]

---

## Abschnitt 9: Kontoeinstellungen — Tab Integrationen (Home Assistant)

### TC-023-043: Home Assistant Integration konfigurieren (Happy Path)

**Requirement**: REQ-023 §4.2 Tab "Integrationen", v1.5
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer ist eingeloggt und befindet sich im Tab "Integrationen"
- Eine Home Assistant Instanz ist im Netzwerk erreichbar

**Testschritte**:
1. Nutzer klickt auf den Tab "Integrationen"
2. Seite lädt: Die Felder "Home Assistant URL" und "Long-Lived Access Token" sind sichtbar
3. Der Status-Chip zeigt "Nicht konfiguriert" (oder ähnlich)
4. Nutzer gibt "Home Assistant URL": `http://homeassistant.local:8123` ein
5. Nutzer gibt "Long-Lived Access Token": `{gültiger HA Token}` ein
6. Nutzer klickt "Verbindung testen"

**Erwartete Ergebnisse**:
- Während des Tests erscheint ein Ladeindikator
- Nach erfolgreichem Test erscheint eine Bestätigung mit HA-Versionsnummer (z.B. "Verbunden — Home Assistant 2024.3.1")
- Der Status-Chip wechselt auf grün "Verbunden"

**Tags**: [REQ-023, integrationen, home-assistant, verbindung-testen]

---

### TC-023-044: Home Assistant — Token-Sicherheitsanzeige nach Speichern

**Requirement**: REQ-023 §4.2 Tab "Integrationen" (Sicherheitshinweis)
**Priority**: High
**Category**: Sicherheit / Detailansicht

**Vorbedingungen**:
- Nutzer hat HA-Token gespeichert und lädt die Seite neu

**Testschritte**:
1. Nutzer navigiert erneut zu `/settings/account` Tab "Integrationen"

**Erwartete Ergebnisse**:
- Das Token-Feld zeigt NICHT den Klartext-Token
- Stattdessen ist das Feld mit Platzhalterzeichen maskiert ("••••••••") oder zeigt einen Hinweis "Token gesetzt"
- Die URL ist weiterhin sichtbar (nicht sensitiv)
- Ein Button "Token entfernen" ist vorhanden

**Tags**: [REQ-023, integrationen, home-assistant, token-sicherheit, masking]

---

### TC-023-045: Home Assistant — Verbindungstest fehlgeschlagen

**Requirement**: REQ-023 §4.2 Tab "Integrationen"
**Priority**: Medium
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer befindet sich im Tab "Integrationen"
- Die eingegebene HA-URL ist nicht erreichbar

**Testschritte**:
1. Nutzer gibt "Home Assistant URL": `http://nicht-erreichbar.local:8123` ein
2. Nutzer gibt irgendein Token ein
3. Nutzer klickt "Verbindung testen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (z.B. "Nicht erreichbar" oder "Verbindung fehlgeschlagen")
- Der Status-Chip zeigt "Nicht erreichbar" oder Warnzeichen

**Tags**: [REQ-023, integrationen, home-assistant, verbindung-fehler]

---

## Abschnitt 10: Kontoeinstellungen — Tab Konto (Account-Löschung)

### TC-023-046: Account-Löschung — Dialog und Bestätigung

**Requirement**: REQ-023 §3.2 UserService.delete_account, AK-16, FK-05
**Priority**: High
**Category**: Dialog / Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Nutzer befindet sich im Tab "Konto" auf `/settings/account`

**Testschritte**:
1. Nutzer klickt auf den Tab "Konto"
2. Nutzer sieht den Warnhinweis "Das Löschen Ihres Kontos kann nicht rückgängig gemacht werden. Alle Daten werden unwiderruflich entfernt."
3. Nutzer klickt auf "Konto löschen"
4. Ein Bestätigungs-Dialog erscheint

**Erwartete Ergebnisse**:
- Der Bestätigungs-Dialog enthält eine deutliche Warnung: "Sind Sie sicher, dass Sie Ihr Konto löschen möchten? Dies kann nicht rückgängig gemacht werden."
- Dialog hat "Endgültig löschen" und "Abbrechen" Buttons (FK-05 impliziert Passwort-Bestätigung — je nach Implementierung auch Passwort-Eingabe im Dialog)

**Tags**: [REQ-023, konto, loeschen, dialog, FK-05]

---

### TC-023-047: Account-Löschung — Abbrechen

**Requirement**: REQ-023 §4.2 Tab "Konto"
**Priority**: Low
**Category**: Dialog

**Vorbedingungen**:
- Bestätigungs-Dialog aus TC-023-046 ist geöffnet

**Testschritte**:
1. Nutzer klickt "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Nutzer ist weiterhin eingeloggt und auf der Kontoeinstellungsseite

**Tags**: [REQ-023, konto, loeschen, abbrechen]

---

### TC-023-048: Account-Löschung — Bestätigung und Logout

**Requirement**: REQ-023 §3.2 UserService.delete_account, AK-16
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Bestätigungs-Dialog aus TC-023-046 ist geöffnet
- Nutzer ist bereit, den Account zu löschen (Testaccount, nicht Demo-Account)

**Testschritte**:
1. Nutzer klickt "Endgültig löschen" (ggf. nach Eingabe des Passworts im Dialog)

**Erwartete Ergebnisse**:
- Nutzer wird ausgeloggt und zu `/login` weitergeleitet
- Beim Versuch, sich erneut mit den alten Credentials einzuloggen, erscheint ein Fehler-Alert

**Nachbedingungen**:
- Account hat `status: deleted`, E-Mail wurde anonymisiert
- Alle Refresh Tokens sind invalidiert

**Tags**: [REQ-023, konto, loeschen, bestaetigt, AK-16]

---

## Abschnitt 11: Logout

### TC-023-049: Logout (aktuelles Gerät)

**Requirement**: REQ-023 §3.2 AuthService.logout, AK-14
**Priority**: Critical
**Category**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer sucht den Logout-Button (z.B. in der AppBar, im Nutzer-Menü oder auf der AccountSettingsPage)
2. Nutzer klickt "Abmelden"

**Erwartete Ergebnisse**:
- Nutzer wird zu `/login` weitergeleitet
- Der Redux-Auth-State wird geleert (kein Nutzername in der AppBar mehr sichtbar)
- Beim nächsten Versuch, `/dashboard` aufzurufen, wird Nutzer zu `/login` weitergeleitet

**Nachbedingungen**:
- Das aktuelle Refresh Token ist invalidiert
- Der Session-Cookie (wenn vorhanden) wurde gelöscht

**Tags**: [REQ-023, logout, zustandswechsel, AK-14]

---

## Abschnitt 12: Platform-Admin-Panel

### TC-023-050: Platform-Admin-Tab sichtbar und ladbar

**Requirement**: REQ-023 §5a.4, §4.2 AccountSettingsPage Tab "Plattform-Modus"
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Nutzer ist als Platform-Admin eingeloggt (Membership im Platform-Tenant mit Rolle `admin`)
- Nutzer befindet sich auf `/settings/account`

**Testschritte**:
1. Nutzer klickt auf den Tab "Plattform-Modus"
2. Seite lädt Admin-Statistiken und Listen

**Erwartete Ergebnisse**:
- Statistik-Karten erscheinen: "Aktive Nutzer", "Nutzer gesamt", "Aktive Organisationen", "Mitgliedschaften"
- Eine Tabelle "Organisationen" mit allen Tenants ist sichtbar (Spalten: Name, Slug, Typ, Mitglieder, Status)
- Eine Tabelle "Benutzer" mit allen Usern ist sichtbar (Spalten: Name, E-Mail, Organisationen & Rollen, Status, Letzter Login)

**Tags**: [REQ-023, platform-admin, admin-panel, detailansicht]

---

### TC-023-051: Nicht-Platform-Admin hat keinen Plattform-Modus-Tab

**Requirement**: REQ-023 §5a.3, AK-21
**Priority**: High
**Category**: Zustandswechsel / Sicherheit

**Vorbedingungen**:
- Nutzer ist als normaler Tenant-Nutzer (kein Platform-Admin) eingeloggt
- Nutzer befindet sich auf `/settings/account`

**Testschritte**:
1. Nutzer betrachtet die Tab-Leiste auf `/settings/account`

**Erwartete Ergebnisse**:
- Der Tab "Plattform-Modus" ist entweder nicht sichtbar ODER wenn Nutzer ihn aufruft, werden keine Admin-Daten geladen und kein Zugriff gewährt
- Kein Datenleck von Admin-Informationen

**Tags**: [REQ-023, platform-admin, zugriffskontrolle, AK-21]

---

### TC-023-052: Platform-Admin sieht verwaiste Tenants prominent

**Requirement**: REQ-023 §5a.5.1, AK-42
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Mindestens ein Tenant hat keine aktiven Admins (ist verwaist, `orphaned_since` ist gesetzt)
- Nutzer befindet sich im Tab "Plattform-Modus"

**Testschritte**:
1. Nutzer scrollt in der Tenant-Tabelle

**Erwartete Ergebnisse**:
- Verwaiste Tenants sind optisch hervorgehoben (z.B. farbliche Markierung, Badge, Icon)
- Die Tenant-Zeile zeigt einen Hinweis auf den verwaisten Status (z.B. "Verwaist seit: {Datum}")

**Tags**: [REQ-023, platform-admin, verwaister-tenant, detailansicht, AK-42]

---

### TC-023-053: Notfall-Admin ernennen (verwaister Tenant)

**Requirement**: REQ-023 §5a.5.2, §5a.5.5 Szenario 12, AK-43, AK-45, AK-46
**Priority**: High
**Category**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Tenant "Grüne Oase" ist verwaist (keine aktiven Admins)
- Nutzer hat den Tenant im Admin-Panel geöffnet

**Testschritte**:
1. Nutzer klickt auf "Notfall-Admin ernennen" (oder ähnlichen Button) im Tenant-Detail
2. Ein Dialog öffnet sich
3. Nutzer wählt aus einer User-Liste den User "Max Mustermann" (aktiver Nutzer, Mitglied des Tenants)
4. Nutzer gibt im Pflichtfeld "Grund" ein: `Bisherige Admins haben Verein verlassen. Max ist Kassenwart.`
5. Nutzer klickt "Ernennen"

**Erwartete Ergebnisse**:
- Ein Erfolgs-Snackbar erscheint
- In der Mitgliederliste des Tenants wird Max' Rolle als "Admin" angezeigt
- Der verwaiste Status des Tenants ist aufgehoben (kein "Verwaist"-Badge mehr)
- Kein leeres "Grund"-Feld wurde akzeptiert (Pflichtfeld, AK-45)

**Tags**: [REQ-023, platform-admin, notfall-admin, dialog, AK-43, AK-46]

---

### TC-023-054: Notfall-Admin ernennen schlägt fehl wenn Tenant nicht verwaist

**Requirement**: REQ-023 §5a.5.2 Sicherheitsregeln, AK-43
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Tenant "Aktiver Garten" hat mindestens einen aktiven Admin

**Testschritte**:
1. Nutzer versucht, bei "Aktiver Garten" die Aktion "Notfall-Admin ernennen" aufzurufen

**Erwartete Ergebnisse**:
- Der Button "Notfall-Admin ernennen" ist deaktiviert ODER nicht vorhanden, da der Tenant aktive Admins hat
- Falls der Nutzer die Aktion trotzdem auslösen kann: Eine Fehlermeldung erscheint (z.B. "Tenant hat aktive Admins — Notfall-Eingriff nicht erforderlich")

**Tags**: [REQ-023, platform-admin, notfall-admin, fehler, AK-43]

---

### TC-023-055: Tenant suspendieren

**Requirement**: REQ-023 §5a.5.3, §5a.5.5 Szenario 13, AK-49
**Priority**: High
**Category**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Tenant "Test-Garten" existiert und hat Status "active"

**Testschritte**:
1. Nutzer findet "Test-Garten" in der Tenant-Liste im Admin-Panel
2. Nutzer klickt "Suspendieren"
3. Ein Dialog erscheint und fordert den Grund an
4. Nutzer gibt ein: `Testweise Suspendierung`
5. Nutzer klickt "Bestätigen"

**Erwartete Ergebnisse**:
- Tenant-Zeile in der Admin-Liste zeigt jetzt Status "Suspendiert" (oder entsprechenden Chip)
- Ein Erfolgs-Snackbar erscheint

**Nachbedingungen**:
- Nutzer des suspendierten Tenants sehen den Tenant im Tenant-Switcher ausgegraut mit einem Hinweis
- API-Zugriffe auf den Tenant werden blockiert (403, für Mitglieder sichtbar als Fehlermeldung)

**Tags**: [REQ-023, platform-admin, tenant-suspendieren, zustandswechsel, AK-49]

---

### TC-023-056: Tenant reaktivieren

**Requirement**: REQ-023 §5a.5.3, AK-51
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Tenant "Test-Garten" hat Status "suspended" (aus TC-023-055)

**Testschritte**:
1. Nutzer findet "Test-Garten" (suspendiert) in der Admin-Tenant-Liste
2. Nutzer klickt "Reaktivieren"
3. Bestätigungs-Dialog (falls vorhanden): Nutzer bestätigt

**Erwartete Ergebnisse**:
- Tenant-Status wechselt zu "Aktiv"
- Erfolgs-Snackbar erscheint
- Mitglieder des Tenants können sofort wieder auf ihre Daten zugreifen (AK-51)

**Tags**: [REQ-023, platform-admin, tenant-reaktivieren, AK-51]

---

### TC-023-057: Platform-Tenant kann nicht suspendiert werden

**Requirement**: REQ-023 §5a.5.3, AK-50
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Der Platform-Tenant ist in der Admin-Liste sichtbar

**Testschritte**:
1. Nutzer findet den Platform-Tenant in der Tenant-Liste
2. Nutzer versucht, den "Suspendieren"-Button zu klicken

**Erwartete Ergebnisse**:
- Der "Suspendieren"-Button ist nicht vorhanden ODER deaktiviert für den Platform-Tenant
- Falls trotzdem versucht: Fehlermeldung erscheint "Platform-Tenant kann nicht suspendiert werden"

**Tags**: [REQ-023, platform-admin, platform-tenant, schutz, AK-50]

---

### TC-023-058: User suspendieren durch Platform-Admin

**Requirement**: REQ-023 §5a.5.4, AK-52
**Priority**: High
**Category**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Nutzer ist Platform-Admin
- Ein zu suspendierender Nutzer "verdaechtiger@example.com" ist in der User-Liste vorhanden

**Testschritte**:
1. Nutzer findet den User in der User-Tabelle des Admin-Panels
2. Nutzer klickt auf das Bearbeiten-Icon oder "Suspendieren"-Button
3. Seite oder Dialog für User-Bearbeitung öffnet sich
4. Nutzer aktiviert "Suspendieren" mit einem Grund
5. Nutzer speichert

**Erwartete Ergebnisse**:
- User-Status in der Tabelle wechselt auf "Suspendiert" (oder inaktiv)
- Erfolgs-Snackbar erscheint
- Der suspendierte Nutzer kann sich nicht mehr einloggen (alle Sessions wurden serverseitig beendet)

**Tags**: [REQ-023, platform-admin, user-suspendieren, AK-52]

---

### TC-023-059: Platform-Admin kann sich nicht selbst suspendieren

**Requirement**: REQ-023 §5a.5.4 Schutzregeln, AK-53
**Priority**: High
**Category**: Fehlermeldung

**Vorbedingungen**:
- Nutzer ist Platform-Admin und betrachtet seine eigene User-Zeile im Admin-Panel

**Testschritte**:
1. Nutzer versucht, auf "Suspendieren" bei seinem eigenen Account zu klicken

**Erwartete Ergebnisse**:
- Der "Suspendieren"-Button ist deaktiviert oder nicht vorhanden für den eigenen Account
- Wenn trotzdem versucht: Fehlermeldung "Sie können sich nicht selbst suspendieren"

**Tags**: [REQ-023, platform-admin, selbst-suspendierung, schutz, AK-53]

---

## Abschnitt 13: Service Accounts

### TC-023-060: Service Account Liste — Einstiegspunkt (Tenant-Admin)

**Requirement**: REQ-023 §5b.10, §5b.3
**Priority**: High
**Category**: Listenansicht

**Vorbedingungen**:
- Nutzer ist eingeloggt als Tenant-Admin von "Mein Garten"
- Nutzer navigiert zu den Tenant-Einstellungen

**Testschritte**:
1. Nutzer navigiert zu `/t/mein-garten/settings/service-accounts`
2. Seite lädt

**Erwartete Ergebnisse**:
- Tabellenüberschrift und eine leere Liste (oder vorhandene Service Accounts) sind sichtbar
- Tabellenspalten: Name, Rolle, Status, Letzte Aktivität, IP-Bereich, Aktionen
- Ein "Service Account erstellen"-Button ist sichtbar
- Der Menüpunkt "Service Accounts" ist in der Navigation NUR für Tenant-Admins sichtbar

**Tags**: [REQ-023, service-accounts, listenansicht, tenant-admin]

---

### TC-023-061: Service Account erstellen (Happy Path) — API-Key einmalig anzeigen

**Requirement**: REQ-023 §5b.9 Szenario 8, §5b.10, AK-25, AK-26, AK-28
**Priority**: Critical
**Category**: Happy Path / Dialog

**Vorbedingungen**:
- Nutzer ist Tenant-Admin
- Nutzer befindet sich auf der Service Account Liste-Seite

**Testschritte**:
1. Nutzer klickt "Service Account erstellen"
2. Ein Dialog öffnet sich mit den Feldern: Name, Beschreibung, Rolle, Rate Limit, IP-Bereiche
3. Nutzer gibt "Name": `Home Assistant Growzelt` ein
4. Nutzer gibt "Beschreibung": `Sensor- und Aktor-Integration` ein
5. Nutzer wählt "Rolle": `Gärtner` (grower) aus dem Dropdown
6. Nutzer gibt "Rate Limit": `500` ein
7. Nutzer gibt "IP-Bereiche": `192.168.1.0/24` ein
8. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Ein Ergebnis-Dialog erscheint mit dem API-Key im Klartext (`kp_...`)
- Der Warnhinweis ist deutlich sichtbar: "Kopieren Sie diesen Schlüssel jetzt — er wird nicht erneut angezeigt!"
- Ein "Kopieren"-Button ist vorhanden
- Nach dem Schließen des Dialogs erscheint der neue Service Account in der Liste mit Status "Aktiv"
- Die Rolle "Gärtner" (grower) ist als Chip in der Zeile sichtbar

**Tags**: [REQ-023, service-accounts, erstellen, happy-path, api-key-einmalig, AK-25, AK-26]

---

### TC-023-062: Service Account erstellen — Rolle "Admin" nicht wählbar für Tenant-Admin

**Requirement**: REQ-023 §5b.3, AK-28
**Priority**: High
**Category**: Formvalidierung

**Vorbedingungen**:
- Nutzer ist Tenant-Admin (KEIN Platform-Admin)
- Dialog "Service Account erstellen" ist geöffnet

**Testschritte**:
1. Nutzer öffnet das "Rolle"-Dropdown

**Erwartete Ergebnisse**:
- Im Dropdown sind nur "Gärtner" (grower) und "Beobachter" (viewer) auswählbar
- Die Option "Admin" ist NICHT im Dropdown vorhanden (AK-28)

**Tags**: [REQ-023, service-accounts, rollen, tenant-admin, AK-28]

---

### TC-023-063: Service Account Detail — Tabs Übersicht, API-Keys, Tenants

**Requirement**: REQ-023 §5b.10 ServiceAccountDetailPage
**Priority**: High
**Category**: Detailansicht

**Vorbedingungen**:
- Ein Service Account "Home Assistant Growzelt" existiert
- Nutzer ist Tenant-Admin und navigiert zu dessen Detailseite

**Testschritte**:
1. Nutzer klickt auf "Home Assistant Growzelt" in der Service Account Liste
2. Detailseite lädt

**Erwartete Ergebnisse**:
- Tab-Leiste mit den Tabs "Übersicht", "API-Keys", "Tenants" ist sichtbar
- Tab "Übersicht" zeigt: Name, Beschreibung, Status (grüner Chip "Aktiv"), Erstellt von, Rate Limit, IP-Bereiche — alle editierbar
- Tab "API-Keys" zeigt aktive Keys mit Label, Prefix, Erstelldatum, Letztem Zugriff, und "Key rotieren"-Button
- Tab "Tenants" zeigt alle Memberships des Service Accounts

**Tags**: [REQ-023, service-accounts, detailansicht, tabs]

---

### TC-023-064: Service Account API-Key rotieren

**Requirement**: REQ-023 §5b.9 Szenario 10, §5b.6 rotate_api_key, AK-36
**Priority**: High
**Category**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Nutzer befindet sich auf der Detailseite eines Service Accounts, Tab "API-Keys"

**Testschritte**:
1. Nutzer klickt "Key rotieren"
2. Ein Bestätigungs-Dialog erscheint (Hinweis: alter Key wird sofort ungültig)
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Ein neuer Dialog mit dem neuen API-Key im Klartext erscheint (einmalig)
- Der Warnhinweis "Kopieren Sie diesen Schlüssel jetzt — er wird nicht erneut angezeigt!" ist sichtbar
- In der Key-Liste zeigt sich ein neuer Key-Eintrag, der alte ist verschwunden oder als "Widerrufen" markiert (AK-36)

**Tags**: [REQ-023, service-accounts, key-rotation, AK-36]

---

### TC-023-065: Service Account suspendieren

**Requirement**: REQ-023 §5b.9 Szenario 11, §5b.5, AK-33
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Service Account "Home Assistant Growzelt" hat Status "active"
- Nutzer ist Tenant-Admin auf der Detailseite

**Testschritte**:
1. Nutzer klickt "Suspendieren" auf der Service Account Detailseite (Tab Übersicht)
2. Bestätigungs-Dialog erscheint
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Status-Chip wechselt von "Aktiv" (grün) zu "Suspendiert" (orange)
- Erfolgs-Snackbar erscheint
- In der Liste-Ansicht ist der Status ebenfalls auf "Suspendiert" aktualisiert
- Alle API-Keys des Service Accounts sind sofort ungültig (AK-33, serverseitig; im Browser: API-Anfragen mit dem Key geben Fehler)

**Tags**: [REQ-023, service-accounts, suspendieren, AK-33]

---

### TC-023-066: Service Account reaktivieren

**Requirement**: REQ-023 §5b.5, AK-34
**Priority**: High
**Category**: Zustandswechsel

**Vorbedingungen**:
- Service Account hat Status "suspended" (aus TC-023-065)

**Testschritte**:
1. Nutzer klickt "Reaktivieren" auf der Detailseite
2. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Status-Chip wechselt zurück zu "Aktiv" (grün)
- API-Keys funktionieren wieder (AK-34)

**Tags**: [REQ-023, service-accounts, reaktivieren, AK-34]

---

### TC-023-067: Service Account löschen (Soft-Delete)

**Requirement**: REQ-023 §5b.5, AK-35
**Priority**: High
**Category**: Zustandswechsel / Dialog

**Vorbedingungen**:
- Ein Service Account "Grafana Monitoring" existiert mit Status "active"
- Nutzer ist Tenant-Admin

**Testschritte**:
1. Nutzer klickt auf das Löschen-Icon des Service Accounts in der Liste
2. Bestätigungs-Dialog erscheint mit Warnhinweis
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Service Account verschwindet aus der aktiven Liste (oder zeigt Status "Gelöscht" in grau)
- Erfolgs-Snackbar erscheint
- Service Account ist nicht mehr reaktivierbar (AK-35)

**Tags**: [REQ-023, service-accounts, loeschen, soft-delete, AK-35]

---

### TC-023-068: Service Account — Erfahrungsstufe Einschränkung

**Requirement**: REQ-023 §5b.10 Sichtbarkeit, REQ-021 Erfahrungsstufen
**Priority**: Medium
**Category**: Zustandswechsel

**Vorbedingungen**:
- Nutzer ist Tenant-Admin mit Erfahrungsstufe "Beginner"

**Testschritte**:
1. Nutzer navigiert zu den Tenant-Einstellungen
2. Nutzer sucht den Menüpunkt "Service Accounts"

**Erwartete Ergebnisse**:
- Der Menüpunkt "Service Accounts" ist NICHT sichtbar (nur ab `intermediate` sichtbar)
- Service Account Seite ist über Direkt-URL auch nicht erreichbar (Redirect oder leere Seite)

**Tags**: [REQ-023, service-accounts, erfahrungsstufe, beginner, sichtbarkeit]

---

## Abschnitt 14: OAuth-Callback

### TC-023-069: OAuth-Callback-Seite verarbeitet Code und State

**Requirement**: REQ-023 §3.2 AuthService.complete_oauth, §4.2 OAuthCallbackPage
**Priority**: High
**Category**: Happy Path

**Vorbedingungen**:
- Nutzer wurde von Google (oder anderem Provider) zurück zu Kamerplanter weitergeleitet
- URL enthält `?code=...&state=...` Parameter

**Testschritte**:
1. Browser navigiert automatisch zu `/auth/oauth/callback?code={code}&state={state}` (nach OAuth-Redirect)
2. OAuthCallbackPage verarbeitet die Parameter

**Erwartete Ergebnisse**:
- Kurzzeitig erscheint ein Ladeindikator oder die Callback-Seite
- Bei Erfolg: Nutzer wird zu `/dashboard` weitergeleitet und ist eingeloggt
- Kein Fehler-Alert bei gültigem Code/State

**Tags**: [REQ-023, oauth, callback, happy-path]

---

### TC-023-070: OAuth-Callback — ungültiger State (CSRF-Schutz)

**Requirement**: REQ-023 §3.1 OAuthEngine.validate_state, SK-03
**Priority**: High
**Category**: Fehlermeldung / Sicherheit

**Vorbedingungen**:
- URL enthält einen State-Parameter, der nicht dem in Redis gespeicherten State entspricht

**Testschritte**:
1. Browser navigiert zu `/auth/oauth/callback?code=irgendwas&state=falscher-state`

**Erwartete Ergebnisse**:
- Ein Fehler-Alert erscheint (z.B. "Anmeldung fehlgeschlagen" oder "Ungültige Sitzung")
- Nutzer ist NICHT eingeloggt
- Redirect zu `/login` oder Fehlermeldung auf der Callback-Seite

**Tags**: [REQ-023, oauth, callback, csrf-schutz, ungueltig-state, SK-03]

---

## Abschnitt 15: Verbundener Tenant-Status

### TC-023-071: Suspendierter Tenant im Tenant-Switcher

**Requirement**: REQ-023 §5a.5.3, AK-49
**Priority**: High
**Category**: Zustandswechsel / Visuelle Rückmeldung

**Vorbedingungen**:
- Nutzer ist Mitglied von zwei Tenants: "Aktiver Garten" (aktiv) und "Gesperrter Garten" (suspendiert)
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer öffnet den Tenant-Switcher in der AppBar
2. Nutzer betrachtet die Liste der verfügbaren Tenants

**Erwartete Ergebnisse**:
- "Aktiver Garten" erscheint normal und ist auswählbar
- "Gesperrter Garten" erscheint ausgegraut mit einem Hinweis "Suspendiert" oder ähnlichem
- Beim Versuch, "Gesperrter Garten" auszuwählen: Eine Fehlermeldung erscheint (z.B. "Tenant ist suspendiert. Kontaktieren Sie den Plattform-Administrator.")
- Daten des suspendierten Tenants sind nicht zugänglich

**Tags**: [REQ-023, tenant-switcher, tenant-suspendiert, visuell, AK-49]

---

### TC-023-072: Automatischer Token-Refresh — transparentes Verhalten

**Requirement**: REQ-023 §4.4 Axios-Interceptor, AK-04, FK-03
**Priority**: High
**Category**: Happy Path / Transparent

**Vorbedingungen**:
- Nutzer ist eingeloggt
- Der Access Token ist abgelaufen (15 Minuten seit Login vergangen)
- Ein gültiger Refresh Token ist im Browser-Cookie vorhanden

**Testschritte**:
1. Nutzer navigiert nach 15+ Minuten Inaktivität zu einer neuen Seite (z.B. `/stammdaten`)

**Erwartete Ergebnisse**:
- Die Seite lädt OHNE Unterbrechung oder Fehlermeldung
- Nutzer wird NICHT zu `/login` weitergeleitet
- Im Hintergrund hat der Axios-Interceptor automatisch einen neuen Access Token angefordert (transparent für den Nutzer)
- Kein Ladeindikator sichtbar (oder nur sehr kurz beim API-Request)

**Tags**: [REQ-023, token-refresh, transparent, axios-interceptor, AK-04, FK-03]

---

## Coverage-Matrix

| Spec-Abschnitt | Beschreibung | Testfall-IDs |
|---|---|---|
| §1.1 Szenario 1 (Registrierung) | Lokale Registrierung — Einzelgärtner | TC-023-001 bis TC-023-006 |
| §1.1 Szenario 2 (Google SSO) | Google-SSO Schnelleinstieg | TC-023-018 |
| §1.1 Szenario 3 (Generischer OIDC) | Keycloak OIDC | TC-023-011 |
| §1.1 Szenario 4 (Account-Linking) | Google-User setzt lokales Passwort | TC-023-031 |
| §1.1 Szenario 5 (Angemeldet bleiben) | Privates Gerät | TC-023-010 |
| §1.1 Szenario 6 (Ohne Angemeldet bleiben) | Öffentliches Gerät | TC-023-009 |
| §1.1 Szenario 7 (Passwort-Reset) | Reset-Flow vollständig | TC-023-019 bis TC-023-025 |
| §4.2 E-Mail-Verifizierung | Verifizierungsseite | TC-023-007 bis TC-023-008 |
| §4.2 Login-Seite | Login, SSO-Buttons, Checkbox | TC-023-009 bis TC-023-019 |
| §4.2 AccountSettings Profil | Profil anzeigen, bearbeiten | TC-023-026 bis TC-023-028 |
| §4.2 AccountSettings Sicherheit | Passwort, Provider-Verwaltung | TC-023-029 bis TC-023-034 |
| §4.2 AccountSettings Sitzungen | Session-Verwaltung | TC-023-035 bis TC-023-036 |
| §4.2 AccountSettings API-Keys | API-Key Lifecycle | TC-023-037 bis TC-023-042 |
| §4.2 AccountSettings Integrationen | Home Assistant | TC-023-043 bis TC-023-045 |
| §4.2 AccountSettings Konto | Account-Löschung | TC-023-046 bis TC-023-048 |
| §4.4 Axios-Interceptor | Automatischer Token-Refresh | TC-023-072 |
| §4.5 Route Guards | ProtectedRoute, PublicOnlyRoute | TC-023-016 bis TC-023-017 |
| §5a Platform-Admin | Admin-Panel, Plattform-Modus | TC-023-050 bis TC-023-059 |
| §5a.5 Tenant-Notfallverwaltung | Notfall-Admin, Suspendierung | TC-023-052 bis TC-023-059 |
| §5b Service Accounts | Erstellen, Lifecycle, Key-Rotation | TC-023-060 bis TC-023-068 |
| §3.2 OAuth-Callback | OAuthCallbackPage | TC-023-069 bis TC-023-070 |
| Tenant-Status im UI | Suspendierter Tenant Anzeige | TC-023-071 |
| Logout | Abmelden | TC-023-049 |

### Abnahmekriterien-Abdeckung

| AK | Beschreibung | Testfall |
|---|---|---|
| AK-01 | Registrierung erstellt unverifiziertes Konto | TC-023-001 |
| AK-02 | Verifizierungs-Link aktiviert Account | TC-023-007 bis 008 |
| AK-03 | Login mit remember_me=true → persistentes Cookie | TC-023-010 |
| AK-03a | Login mit remember_me=false → Session-Cookie | TC-023-009 |
| AK-04 | Token-Rotation transparent | TC-023-072 |
| AK-05 | Account-Sperre nach 5 Fehlversuchen | TC-023-014 |
| AK-06 | Passwort-Reset-Token 1h gültig | TC-023-023 bis 025 |
| AK-07 | Nach Reset alle Tokens invalidiert | TC-023-023 |
| AK-08 | Google SSO erstellt verifizierten User | TC-023-018 |
| AK-13 | Letzten Provider entfernen verhindert | TC-023-033 |
| AK-14 | Logout invalidiert Refresh Token | TC-023-049 |
| AK-15 | Profil-Update persistiert | TC-023-027 |
| AK-16 | Account-Löschung soft-delete + anonymisiert | TC-023-048 |
| AK-21 | Nicht-Platform-Admin: 403 auf Admin-Endpunkte | TC-023-051 |
| AK-25 | Service Account Erstellung mit Membership | TC-023-061 |
| AK-26 | API-Key bei Erstellung einmalig sichtbar | TC-023-061, TC-023-038 |
| AK-28 | Tenant-Admin kann nur grower/viewer-Rolle setzen | TC-023-062 |
| AK-33 | Suspendierung macht API-Keys ungültig | TC-023-065 |
| AK-34 | Reaktivierung stellt API-Keys wieder her | TC-023-066 |
| AK-35 | Löschung revoked alle Keys, Memberships 'left' | TC-023-067 |
| AK-36 | Key-Rotation revoked alten, erstellt neuen Key | TC-023-064 |
| AK-42 | Verwaist-Erkennung (0 aktive Admins) | TC-023-052 |
| AK-43 | Emergency-Admin nur bei verwaisten Tenants | TC-023-053 bis 054 |
| AK-45 | Grund-Feld Pflichtfeld bei Emergency-Admin | TC-023-053 |
| AK-46 | Emergency-Admin Rollen-Beförderung | TC-023-053 |
| AK-49 | Suspendierter Tenant → 403 für Mitglieder (sichtbar) | TC-023-055, TC-023-071 |
| AK-50 | Platform-Tenant nicht suspendierbar | TC-023-057 |
| AK-51 | Reaktivierung sofort wirksam | TC-023-056 |
| AK-52 | User-Suspendierung: alle Tokens invalidiert | TC-023-058 |
| AK-53 | Platform-Admin kann sich nicht selbst suspendieren | TC-023-059 |
| FK-01 | Login zeigt aktivierte SSO-Provider | TC-023-011, 012 |
| FK-01a | "Angemeldet bleiben"-Checkbox sichtbar | TC-023-010 |
| FK-02 | Nach Login Redirect zu Dashboard | TC-023-009 |
| FK-03 | 401 → automatischer Token-Refresh | TC-023-072 |
| FK-04 | AccountSettings zeigt Provider und Sessions | TC-023-032, 035 |
| FK-05 | Account-Löschung mit Bestätigungs-Dialog | TC-023-046 |
| FK-06 | API-Key-Liste mit allen Spalten | TC-023-037 |
| FK-07 | Neuer API-Key einmalig angezeigt | TC-023-038 |
| FK-08 | Key revoken mit Bestätigungs-Dialog | TC-023-040 bis 042 |
| SK-05 | Passwort-Reset: kein Hinweis ob E-Mail existiert | TC-023-020, 021 |
| SEC-H-009 | Registrierung: kein Hinweis ob E-Mail bereits vorhanden | TC-023-005 |
