---
req_id: REQ-025
title: Datenschutz & Betroffenenrechte (DSGVO)
category: Plattform & Datenschutz
test_count: 62
coverage_areas:
  - PrivacySettingsPage Navigation und Tab-Struktur
  - Tab "Einwilligungen" — Consent-Verwaltung (Art. 7)
  - Tab "Datenexport" — Auskunft und Portabilitaet (Art. 15/20)
  - Tab "Account loeschen" — Recht auf Loeschung (Art. 17)
  - Tab "Verarbeitungseinschraenkung" — Art. 18 und Widerspruch Art. 21
  - E-Mail-Aenderung (Art. 16) via AccountSettingsPage
  - Consent-Gate — Feature-Sperren bei fehlendem Consent
  - Datenschutzrichtlinie (oeffentlich zugaenglich)
  - Authentifizierungsschutz
  - Edge Cases und Grenzbedingungen
generated: 2026-03-21
version: "1.1"
status: Entwurf — PrivacySettingsPage noch nicht implementiert (spec existiert)
---

# TC-REQ-025: Datenschutz & Betroffenenrechte (DSGVO)

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-025 Datenschutz & Betroffenenrechte (DSGVO) v1.1**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte aus REQ-025 § 4.3.

**Hinweis zum Implementierungsstand:** Die `PrivacySettingsPage` unter `/settings/privacy` ist laut Spezifikation definiert, aber noch nicht implementiert. Diese Testfaelle beschreiben das Soll-Verhalten gemaess Spezifikation und dienen als Grundlage fuer Selenium-/Playwright-E2E-Tests nach der Implementierung.

**Abhaengigkeiten:** REQ-023 (Auth, Sessions, E-Mail-Verifikation), REQ-024 (Tenant-Mitgliedschaften), NFR-011 (Retention-Fristen).

---

## 1. Navigation und Seitenstruktur

### TC-025-001: PrivacySettingsPage ist ueber Einstellungen erreichbar

**Requirement**: REQ-025 § 4.1 — Neue Seiten
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt (lokaler Account, z.B. `demo@kamerplanter.local`)
- Nutzer befindet sich auf einer beliebigen Seite, z.B. dem Dashboard

**Testschritte**:
1. Nutzer navigiert zum Nutzer-Menu oder zu den Account-Einstellungen
2. Nutzer klickt auf den Navigations-Eintrag "Datenschutz-Einstellungen" oder navigiert direkt zu `/settings/privacy`

**Erwartete Ergebnisse**:
- Die Seite mit dem Titel "Datenschutz-Einstellungen" wird geladen
- Vier Tabs sind sichtbar: "Einwilligungen", "Datenexport", "Account loeschen", "Verarbeitungseinschraenkung"
- Der erste Tab "Einwilligungen" ist standardmaessig aktiv

**Nachbedingungen**:
- Nutzer befindet sich auf `/settings/privacy`

**Tags**: [req-025, privacy-settings, navigation, tab-struktur]

---

### TC-025-002: Unauthentifizierter Zugriff auf PrivacySettingsPage wird umgeleitet

**Requirement**: REQ-025 § 3.3 — API-Schicht Auth-Anforderungen
**Priority**: Critical
**Category**: Authentifizierung
**Preconditions**:
- Nutzer ist NICHT eingeloggt (kein aktiver Session-Cookie)

**Testschritte**:
1. Nutzer gibt direkt `/settings/privacy` in der Adressleiste ein
2. Nutzer drueckt Enter

**Erwartete Ergebnisse**:
- Nutzer wird auf die Login-Seite (`/login`) weitergeleitet
- Die PrivacySettingsPage wird NICHT angezeigt
- Nach erfolgreichem Login wird der Nutzer zurueck zu `/settings/privacy` weitergeleitet

**Nachbedingungen**:
- Keine Daten wurden preisegegeben

**Tags**: [req-025, auth-guard, redirect, unauthenticated]

---

### TC-025-003: Tab-Navigation funktioniert via URL-Parameter

**Requirement**: REQ-025 § 4.1 — Frontend-Integration
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf der PrivacySettingsPage

**Testschritte**:
1. Nutzer klickt auf Tab "Datenexport"
2. Nutzer notiert die aktuelle URL
3. Nutzer klickt auf Tab "Account loeschen"
4. Nutzer klickt im Browser auf "Zurueck"

**Erwartete Ergebnisse**:
- Nach Klick auf "Datenexport" aktualisiert sich die URL (z.B. `/settings/privacy?tab=export`)
- Der Tab-Inhalt wechselt zu "Datenexport"
- Nach Klick auf "Account loeschen" wechselt der Inhalt entsprechend
- Beim Zurueck-Klick wird der "Datenexport"-Tab wieder angezeigt
- Die URL stimmt mit dem aktiven Tab ueberein

**Nachbedingungen**:
- URL-basierte Tab-Navigation funktioniert korrekt

**Tags**: [req-025, tab-navigation, url-state, browser-history]

---

## 2. Tab "Einwilligungen" — Consent-Verwaltung (Art. 7)

### TC-025-004: Einwilligungs-Uebersicht zeigt alle vier Verarbeitungszwecke

**Requirement**: REQ-025 § 4.2 — Tab "Einwilligungen", § 3.1 ConsentEngine.PURPOSES
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich auf `/settings/privacy`
- Tab "Einwilligungen" ist aktiv

**Testschritte**:
1. Nutzer betrachtet die Liste der Verarbeitungszwecke auf dem Tab "Einwilligungen"

**Erwartete Ergebnisse**:
- Vier Verarbeitungszwecke sind aufgelistet:
  1. "Grundfunktionen" — Rechtsgrundlage: Art. 6(1)(b) Vertragserfuellung
  2. "Fehler-Tracking (Sentry)" — Rechtsgrundlage: Art. 6(1)(a) Einwilligung
  3. "Passwort-Sicherheitscheck (HaveIBeenPwned)" — Rechtsgrundlage: Art. 6(1)(a) Einwilligung
  4. "Externe Stammdatenanreicherung" — Rechtsgrundlage: Art. 6(1)(a) Einwilligung
- Jeder Eintrag zeigt: Label, Beschreibung, Rechtsgrundlage, aktuellen Status

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-025, consent, purposes, listenansicht, ak-13]

---

### TC-025-005: Erforderlicher Verarbeitungszweck "Grundfunktionen" ist nicht widerrufbar

**Requirement**: REQ-025 § 3.1 ConsentEngine, § 4.2 — Tab "Einwilligungen", AK-13, FK-03
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich auf dem Tab "Einwilligungen"

**Testschritte**:
1. Nutzer sucht den Eintrag "Grundfunktionen" in der Liste
2. Nutzer versucht den Toggle/Schalter fuer "Grundfunktionen" zu betaetigen

**Erwartete Ergebnisse**:
- Der Toggle fuer "Grundfunktionen" ist deaktiviert (disabled) und kann nicht angeklickt werden
- Ein Hinweistext "Erforderlich fuer den Betrieb" ist sichtbar
- Der Toggle zeigt dauerhaft den Status "erteilt" (eingeschaltet)
- Kein Fehlerdialog erscheint beim Klickversuch

**Nachbedingungen**:
- Consent fuer "core_functionality" bleibt unveraendert

**Tags**: [req-025, consent, required-purpose, disabled-toggle, ak-13, fk-03]

---

### TC-025-006: Optionale Einwilligung widerrufen — Happy Path

**Requirement**: REQ-025 § 1.1 Szenario 4, § 3.2 PrivacyService.revoke_consent, AK-13
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Fehler-Tracking (Sentry)" ist aktuell erteilt (Toggle = ON)
- Nutzer befindet sich auf dem Tab "Einwilligungen"

**Testschritte**:
1. Nutzer sucht den Eintrag "Fehler-Tracking (Sentry)"
2. Nutzer betaetigt den Toggle (schaltet ihn von ON auf OFF)

**Erwartete Ergebnisse**:
- Der Toggle wechselt sofort auf OFF
- Der Status-Text aendert sich zu "Widerrufen am [heutiges Datum]"
- Eine Erfolgs-Benachrichtigung erscheint (z.B. Snackbar: "Einwilligung widerrufen")
- Die Aenderung bleibt nach Seitenneuladung erhalten

**Nachbedingungen**:
- `error_tracking`-Consent ist auf `granted: false` gesetzt mit aktuellem `revoked_at`-Zeitstempel

**Tags**: [req-025, consent, revoke, toggle, happy-path]

---

### TC-025-007: Optionale Einwilligung erteilen — Happy Path

**Requirement**: REQ-025 § 3.2 PrivacyService.grant_consent
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Externe Stammdatenanreicherung" ist aktuell widerrufen (Toggle = OFF)
- Nutzer befindet sich auf dem Tab "Einwilligungen"

**Testschritte**:
1. Nutzer sucht den Eintrag "Externe Stammdatenanreicherung"
2. Nutzer betaetigt den Toggle (schaltet ihn von OFF auf ON)

**Erwartete Ergebnisse**:
- Der Toggle wechselt sofort auf ON
- Der Status-Text aendert sich zu "Erteilt am [heutiges Datum]"
- Eine Erfolgs-Benachrichtigung erscheint (Snackbar-Meldung)
- Die Aenderung bleibt nach Seitenneuladung erhalten

**Nachbedingungen**:
- `external_enrichment`-Consent ist auf `granted: true` gesetzt mit aktuellem `granted_at`-Zeitstempel

**Tags**: [req-025, consent, grant, toggle, happy-path]

---

### TC-025-008: Consent-Zeitstempel werden korrekt angezeigt

**Requirement**: REQ-025 § 4.2 — Tab "Einwilligungen" (Zeitstempel der letzten Aenderung)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Passwort-Sicherheitscheck" wurde vor einigen Tagen erteilt und gestern widerrufen

**Testschritte**:
1. Nutzer navigiert zum Tab "Einwilligungen"
2. Nutzer betrachtet den Eintrag "Passwort-Sicherheitscheck (HaveIBeenPwned)"

**Erwartete Ergebnisse**:
- Der Zeitstempel des Widerrufs ist sichtbar (Format: "Widerrufen am {{date}}")
- Das Datum stimmt mit dem tatsaechlichen Widerrufszeitpunkt ueberein
- Kein Erteilungs-Zeitstempel wird angezeigt, wenn die Einwilligung aktuell widerrufen ist

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, consent, timestamp, i18n, detailansicht]

---

### TC-025-009: Consent-Gate — Funktion ohne Einwilligung ist gesperrt

**Requirement**: REQ-025 § 3.6 Middleware Consent-Pruefung, § 9, AK-14
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Externe Stammdatenanreicherung" ist widerrufen (`granted: false`)
- Nutzer navigiert zu einer Seite, die Stammdatenanreicherung ausloest (z.B. eine Artendetailseite mit Anreicherungs-Button)

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanzenart
2. Nutzer klickt den Button "Externe Daten abrufen" (oder aequivalenter Anreicherungs-Trigger)

**Erwartete Ergebnisse**:
- Eine Fehlermeldung wird angezeigt (z.B. Snackbar oder Alert): "Einwilligung fuer 'Externe Stammdatenanreicherung' nicht erteilt."
- Die Anreicherung wird NICHT ausgefuehrt
- Ein Link oder Hinweis auf die Datenschutz-Einstellungen ist sichtbar

**Nachbedingungen**:
- Kein externer API-Aufruf wurde ausgefuehrt

**Tags**: [req-025, consent-gate, blocked-feature, ak-14, external-enrichment]

---

## 3. Tab "Datenexport" — Art. 15 / Art. 20

### TC-025-010: Erstmaligen Datenexport anfordern — Happy Path

**Requirement**: REQ-025 § 1.1 Szenario 1, § 4.2 Tab "Datenexport", AK-01, FK-04
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Es existiert kein aktiver Export-Auftrag fuer diesen Nutzer
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet den Tab "Datenexport"
2. Nutzer klickt den Button "Meine Daten exportieren"

**Erwartete Ergebnisse**:
- Der Button "Meine Daten exportieren" ist klickbar (nicht deaktiviert)
- Nach dem Klick erscheint ein Statusindikator: "Export wird vorbereitet..." (pending-Status sichtbar)
- Der Button "Meine Daten exportieren" wird deaktiviert (keine Doppel-Anforderung moeglich)
- Der neue Export-Auftrag erscheint in der Liste vergangener Exporte mit Status "Ausstehend" oder "In Bearbeitung"
- Eine Bestaetigung wird angezeigt (Snackbar oder Inline-Meldung)

**Nachbedingungen**:
- Ein `DataExportRequest` mit Status `pending` ist fuer den Nutzer erstellt
- Der Celery-Task zur Datenzusammenstellung wurde ausgeloest

**Tags**: [req-025, data-export, art-15, art-20, happy-path, ak-01, fk-04]

---

### TC-025-011: Export-Button ist deaktiviert waehrend ein Export laeuft

**Requirement**: REQ-025 § 3.1 DataExportEngine.validate_export_request (Max. 1 aktiver Export), FK-04, AK-03
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Export-Auftrag mit Status `pending` oder `processing` existiert bereits fuer diesen Nutzer
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet den Tab "Datenexport"
2. Nutzer versucht den Button "Meine Daten exportieren" zu klicken

**Erwartete Ergebnisse**:
- Der Button "Meine Daten exportieren" ist deaktiviert (disabled)
- Ein Hinweistext ist sichtbar, der erklaert, dass ein Export bereits laeuft (z.B. "Export wird vorbereitet...")
- Der laufende Export ist in der Liste mit Status "Ausstehend" oder "In Bearbeitung" sichtbar

**Nachbedingungen**:
- Kein zweiter Export-Auftrag wurde erstellt

**Tags**: [req-025, data-export, duplicate-prevention, disabled-button, ak-03, fk-04]

---

### TC-025-012: Abgeschlossenen Export herunterladen

**Requirement**: REQ-025 § 3.2 PrivacyService.download_export, § 4.2 Tab "Datenexport"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Export-Auftrag mit Status `completed` existiert fuer diesen Nutzer
- Die 72-Stunden-Frist ist noch nicht abgelaufen
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet die Liste vergangener Exporte
2. Nutzer findet den abgeschlossenen Export (Status: "Abgeschlossen")
3. Nutzer klickt den "Herunterladen"-Link neben dem Eintrag

**Erwartete Ergebnisse**:
- Die JSON-Datei wird heruntergeladen (Browser-Download-Dialog erscheint oder Download startet automatisch)
- Die Dateigroe (z.B. in KB oder MB) ist neben dem Download-Link sichtbar
- Der Hinweistext "Verfuegbar bis {{date}}" ist sichtbar
- Der Download-Link ist klickbar und liefert eine gueltige Datei

**Nachbedingungen**:
- `download_count` des Export-Auftrags wurde inkrementiert (sichtbar falls angezeigt)

**Tags**: [req-025, data-export, download, completed-export, happy-path]

---

### TC-025-013: Abgelaufener Export zeigt keinen Download-Link mehr

**Requirement**: REQ-025 § 1.1 Szenario 1 (72h-Link), AK-02, NFR-011 R-05
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Export-Auftrag mit Status `expired` existiert (Ablaufzeit ist ueberschritten)
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet die Liste vergangener Exporte
2. Nutzer sucht den abgelaufenen Export

**Erwartete Ergebnisse**:
- Der Export-Eintrag wird angezeigt mit Status "Abgelaufen"
- KEIN "Herunterladen"-Link ist sichtbar
- Kein Datum "Verfuegbar bis" wird angezeigt (oder es zeigt ein vergangenes Datum)
- Es ist erklaert, dass ein neuer Export angefordert werden kann

**Nachbedingungen**:
- Kein Download war moeglich

**Tags**: [req-025, data-export, expired, no-download-link, ak-02]

---

### TC-025-014: Fehlgeschlagener Export zeigt Fehlerstatus

**Requirement**: REQ-025 § 3.5 Celery-Task process_data_export (Fehlerfall)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Export-Auftrag mit Status `failed` existiert (Celery-Task-Fehler)
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet die Liste vergangener Exporte

**Erwartete Ergebnisse**:
- Der fehlgeschlagene Export-Eintrag zeigt Status "Fehlgeschlagen"
- Eine verstaendliche Fehlermeldung oder ein Hinweis ist sichtbar
- Ein neuer Export kann angefordert werden (Button ist nicht dauerhaft deaktiviert)

**Nachbedingungen**:
- Nutzer kann einen neuen Export-Versuch starten

**Tags**: [req-025, data-export, failed-status, error-display]

---

### TC-025-015: Export-Liste zeigt mehrere vergangene Exporte

**Requirement**: REQ-025 § 4.2 Tab "Datenexport" — Liste vergangener Exporte
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 3 vergangene Export-Auftraege mit verschiedenen Status existieren (completed, expired, failed)
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer betrachtet den Tab "Datenexport"

**Erwartete Ergebnisse**:
- Alle vergangenen Export-Auftraege sind in chronologischer Reihenfolge aufgelistet (neueste zuerst)
- Jeder Eintrag zeigt: Anforderungsdatum, Status, Dateigroe (bei completed), Ablaufzeit (bei completed)
- Status-Abzeichen (Chips oder Labels) sind visuell differenziert (z.B. Farben)
- Der Info-Text "Download ist 72 Stunden verfuegbar" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, data-export, list, multiple-exports, status-display]

---

## 4. Tab "Account loeschen" — Art. 17

### TC-025-016: Loeschformular zeigt Warnhinweis und Aufschluesselung

**Requirement**: REQ-025 § 4.2 Tab "Account loeschen", AK-08a, FK-05
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer navigiert zum Tab "Account loeschen"

**Testschritte**:
1. Nutzer klickt auf den Tab "Account loeschen"
2. Nutzer liest den angezeigten Inhalt

**Erwartete Ergebnisse**:
- Der Warnhinweis "Diese Aktion ist nach 90 Tagen unwiderruflich." ist prominent sichtbar
- Eine transparente Aufschluesselung zeigt zwei Kategorien:
  - **Vollstaendig geloescht:** Profildaten, Sessions, Einwilligungen, Aufgaben (und weitere)
  - **Anonymisiert (nicht geloescht):** Erntedokumentation, IPM-Behandlungsnachweise — mit Begruendung (CanG, PflSchG)
- Das Passwort-Eingabefeld ist sichtbar
- Der Bestaetigungs-Button "Account endgueltig loeschen" ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert (nur Anzeige)

**Tags**: [req-025, erasure, warning, data-breakdown, ak-08a, fk-05]

---

### TC-025-017: Account-Loeschung erfordert Passwort-Bestaetigung

**Requirement**: REQ-025 § 1.1 Szenario 3, § 3.2 PrivacyService.request_erasure, FK-05
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt mit einem lokalen Account
- Nutzer befindet sich auf dem Tab "Account loeschen"

**Testschritte**:
1. Nutzer laesst das Passwort-Eingabefeld leer
2. Nutzer klickt den Button "Account endgueltig loeschen"

**Erwartete Ergebnisse**:
- Eine Validierungsmeldung erscheint: Das Passwort-Feld ist pflichtangabe
- Die Loeschung wird NICHT eingeleitet
- Eine entsprechende Fehlermeldung wird neben dem Passwort-Feld oder als Snackbar angezeigt

**Nachbedingungen**:
- Kein Loeschauftrag wurde erstellt
- Nutzer ist weiterhin eingeloggt

**Tags**: [req-025, erasure, password-required, validation, fk-05]

---

### TC-025-018: Account-Loeschung erfordert Checkbox-Bestaetigung

**Requirement**: REQ-025 § 4.2 Tab "Account loeschen" — Bestaetigungs-Dialog mit Checkbox, FK-05
**Priority**: Critical
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt mit einem lokalen Account
- Nutzer befindet sich auf dem Tab "Account loeschen"
- Nutzer hat das korrekte Passwort eingegeben

**Testschritte**:
1. Nutzer gibt das korrekte Passwort ein
2. Nutzer klickt den Button "Account endgueltig loeschen" OHNE die Bestaetigung-Checkbox anzuhaken

**Erwartete Ergebnisse**:
- Ein Bestaetigungs-Dialog erscheint
- Die Checkbox mit Text "Ich verstehe, dass mein Account geloescht wird und gesetzlich geschuetzte Daten anonymisiert aufbewahrt bleiben" ist sichtbar
- Der "Bestaetigen"-Button im Dialog ist deaktiviert, solange die Checkbox nicht angehakt ist

**Nachbedingungen**:
- Kein Loeschauftrag wurde erstellt

**Tags**: [req-025, erasure, confirmation-checkbox, dialog, ak-08a, fk-05]

---

### TC-025-019: Account-Loeschung — vollstaendiger Happy Path

**Requirement**: REQ-025 § 1.1 Szenario 3, § 3.2 PrivacyService.request_erasure, AK-07, AK-08
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit einem lokalen Account (Testnutzer, nicht `demo@kamerplanter.local` in Produktivumgebung)
- Nutzer befindet sich auf dem Tab "Account loeschen"

**Testschritte**:
1. Nutzer gibt das korrekte Passwort in das Bestaetungsfeld ein
2. Nutzer klickt "Account endgueltig loeschen"
3. Im erscheinenden Dialog hakt Nutzer die Checkbox "Ich verstehe, dass mein Account geloescht wird..." an
4. Nutzer klickt "Bestaetigen" im Dialog

**Erwartete Ergebnisse**:
- Nach Bestaetigung wird der Nutzer sofort ausgeloggt
- Eine abschliessende Meldung erscheint (z.B. auf der Login-Seite): "Ihr Account wurde fuer die Loeschung vorgemerkt."
- Ein erneuter Login-Versuch mit den alten Zugangsdaten schlaegt fehl
- Die Meldung erklaert, dass eine endgueltige Loeschung nach 90 Tagen erfolgt

**Nachbedingungen**:
- Nutzer ist ausgeloggt und alle Sessions sind invalidiert
- `ErasureRequest` mit Status `scheduled` wurde erstellt

**Tags**: [req-025, erasure, soft-delete, logout, happy-path, ak-07]

---

### TC-025-020: Falsches Passwort bei Account-Loeschung

**Requirement**: REQ-025 § 3.2 PrivacyService.request_erasure (Passwort-Verifikation)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt mit einem lokalen Account
- Nutzer befindet sich auf dem Tab "Account loeschen"

**Testschritte**:
1. Nutzer gibt ein falsches Passwort in das Bestaetungsfeld ein
2. Nutzer klickt "Account endgueltig loeschen"
3. Nutzer hakt im Dialog die Checkbox an und klickt "Bestaetigen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Das eingegebene Passwort ist falsch."
- Die Loeschung wird NICHT eingeleitet
- Nutzer bleibt eingeloggt
- Das Passwort-Feld wird geleert oder fokussiert, damit der Nutzer es erneut eingeben kann

**Nachbedingungen**:
- Kein Loeschauftrag wurde erstellt

**Tags**: [req-025, erasure, wrong-password, error-message]

---

### TC-025-021: Loeschangabe zeigt Trennung "vollstaendig geloescht" vs. "anonymisiert"

**Requirement**: REQ-025 § 4.2 Tab "Account loeschen", AK-08, AK-08a
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Der Nutzer hat Erntedaten und IPM-Behandlungen im System (die anonymisiert werden)
- Nutzer befindet sich auf dem Tab "Account loeschen"

**Testschritte**:
1. Nutzer liest die Aufschluesselung der Daten auf dem Tab "Account loeschen"

**Erwartete Ergebnisse**:
- Die Aufschluesselung zeigt klar zwei Kategorien:
  - **Kategorie 1 "Vollstaendig geloescht"**: Profildaten, Sessions, Einwilligungen, Aufgaben, etc.
  - **Kategorie 2 "Anonymisiert (aufbewahrt)"**: Erntedokumentation (Begruendung: CanG), Behandlungsnachweise (Begruendung: PflSchG §11)
- Die Rechtsgrundlage (CanG, PflSchG) fuer die Aufbewahrungspflicht ist erklaert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, erasure, data-categories, anonymization, legal-retention, ak-08a]

---

### TC-025-022: Abbruch der Account-Loeschung im Bestaetigungs-Dialog

**Requirement**: REQ-025 § 4.2 Tab "Account loeschen" — Bestaetigungs-Dialog
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer hat Passwort eingegeben und Loeschungs-Dialog ist geoeffnet

**Testschritte**:
1. Nutzer sieht den Bestaetigungs-Dialog
2. Nutzer klickt "Abbrechen" im Dialog

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich
- Nutzer bleibt eingeloggt
- Kein Loeschauftrag wurde erstellt
- Nutzer befindet sich weiterhin auf dem Tab "Account loeschen"

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, erasure, cancel, dialog, abort]

---

## 5. Tab "Verarbeitungseinschraenkung" — Art. 18 und Art. 21

### TC-025-023: Tab "Verarbeitungseinschraenkung" zeigt Info-Text und Formular

**Requirement**: REQ-025 § 4.2 Tab "Verarbeitungseinschraenkung"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer navigiert zum Tab "Verarbeitungseinschraenkung"

**Testschritte**:
1. Nutzer klickt auf den Tab "Verarbeitungseinschraenkung"

**Erwartete Ergebnisse**:
- Ein Info-Text erklaert Art. 18 DSGVO (Recht auf Einschraenkung der Verarbeitung)
- Ein Formular ist sichtbar mit:
  - Dropdown/Select fuer "Scope" (z.B. "Alle Daten", "Sensordaten", "Analyse", "Anreicherung")
  - Dropdown/Select fuer "Grund" mit den Optionen: "Richtigkeit der Daten wird bestritten", "Verarbeitung ist rechtswidrig", "Zweck abgelaufen", "Widerspruch ausstehend"
- Eine Liste aktiver Einschraenkungen ist sichtbar (oder leer mit entsprechendem Hinweis)
- Ein separater Bereich "Widerspruch (Art. 21)" mit eigenem Formular ist vorhanden

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, restriction, art-18, form-display, info-text]

---

### TC-025-024: Verarbeitungseinschraenkung setzen — Happy Path

**Requirement**: REQ-025 § 3.2 PrivacyService.restrict_processing, AK-11
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Keine aktive Einschraenkung fuer den Scope "Sensordaten" existiert
- Nutzer befindet sich auf dem Tab "Verarbeitungseinschraenkung"

**Testschritte**:
1. Nutzer waehlt im Dropdown "Scope" den Wert "Sensordaten" aus
2. Nutzer waehlt im Dropdown "Grund" den Wert "Richtigkeit der Daten wird bestritten" aus
3. Nutzer klickt "Einschraenkung setzen" (oder aequivalenter Button)

**Erwartete Ergebnisse**:
- Eine Erfolgs-Benachrichtigung erscheint
- Die neue Einschraenkung erscheint in der Liste aktiver Einschraenkungen
- Die Liste zeigt: Scope, Grund, Datum der Erstellung
- Ein "Aufheben"-Button ist neben der Einschraenkung sichtbar

**Nachbedingungen**:
- `ProcessingRestriction` fuer `sensor_data` / `accuracy_contested` wurde erstellt

**Tags**: [req-025, restriction, art-18, set-restriction, happy-path]

---

### TC-025-025: Aktive Verarbeitungseinschraenkung aufheben

**Requirement**: REQ-025 § 3.2 PrivacyService.lift_restriction
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Eine aktive Einschraenkung fuer Scope "Analyse" existiert
- Nutzer befindet sich auf dem Tab "Verarbeitungseinschraenkung"

**Testschritte**:
1. Nutzer findet die aktive Einschraenkung in der Liste
2. Nutzer klickt den "Aufheben"-Button neben der Einschraenkung

**Erwartete Ergebnisse**:
- Ein Bestaetigungs-Dialog oder direktes Aufheben erfolgt
- Die Einschraenkung verschwindet aus der Liste aktiver Einschraenkungen
- Eine Erfolgs-Benachrichtigung erscheint (z.B. "Einschraenkung aufgehoben")

**Nachbedingungen**:
- `ProcessingRestriction.lifted_at` wurde gesetzt

**Tags**: [req-025, restriction, lift-restriction, zustandswechsel]

---

### TC-025-026: Doppelte Einschraenkung fuer gleichen Scope wird verhindert

**Requirement**: REQ-025 § 2 ArangoDB-Modellierung — UNIQUE INDEX auf [user_key, scope]
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt
- Eine aktive Einschraenkung fuer Scope "Alle Daten" existiert bereits
- Nutzer befindet sich auf dem Tab "Verarbeitungseinschraenkung"

**Testschritte**:
1. Nutzer waehlt erneut Scope "Alle Daten" und einen Grund aus
2. Nutzer klickt "Einschraenkung setzen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Fuer diesen Bereich existiert bereits eine aktive Einschraenkung."
- Die bestehende Einschraenkung bleibt unveraendert
- Keine zweite Einschraenkung wird erstellt

**Nachbedingungen**:
- Nur eine Einschraenkung pro Scope bleibt aktiv

**Tags**: [req-025, restriction, duplicate-prevention, unique-constraint, error-message]

---

### TC-025-027: Widerspruch gemaess Art. 21 einlegen

**Requirement**: REQ-025 § 3.2 PrivacyService.object_to_processing, AK-12
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf dem Tab "Verarbeitungseinschraenkung" im Bereich "Widerspruch (Art. 21)"

**Testschritte**:
1. Nutzer sucht den Bereich "Widerspruch" auf dem Tab
2. Nutzer gibt im Zweck-Feld einen Verarbeitungszweck ein (z.B. "Externe Datenanalyse")
3. Nutzer gibt eine Begruendung als Freitext ein (z.B. "Ich halte die Verarbeitung auf Basis berechtigten Interesses fuer nicht gerechtfertigt.")
4. Nutzer klickt "Widerspruch einlegen"

**Erwartete Ergebnisse**:
- Eine Erfolgs-Benachrichtigung erscheint
- Der Widerspruch erscheint als neue Einschraenkung in der Liste mit Grund "Widerspruch ausstehend"
- Das Freitext-Begruendungsfeld wurde korrekt uebernommen

**Nachbedingungen**:
- `ProcessingRestriction` mit `reason: objection_pending` wurde erstellt

**Tags**: [req-025, objection, art-21, objection_pending, ak-12, happy-path]

---

### TC-025-028: Leere Liste aktiver Einschraenkungen zeigt Leer-Zustand

**Requirement**: REQ-025 § 4.2 Tab "Verarbeitungseinschraenkung"
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Keine aktiven Verarbeitungseinschraenkungen existieren fuer diesen Nutzer

**Testschritte**:
1. Nutzer navigiert zum Tab "Verarbeitungseinschraenkung"

**Erwartete Ergebnisse**:
- Die Liste aktiver Einschraenkungen zeigt einen leeren Zustand (z.B. "Keine aktiven Einschraenkungen")
- Das Formular zum Setzen einer neuen Einschraenkung ist weiterhin sichtbar und nutzbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, restriction, empty-state, listenansicht]

---

## 6. E-Mail-Aenderung — Art. 16

### TC-025-029: E-Mail-Aenderung anfordern — Happy Path

**Requirement**: REQ-025 § 1.1 Szenario 2, § 3.2 PrivacyService.request_email_change, AK-04
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt mit einem lokalen Account (E-Mail: `nutzer@example.com`)
- Die neue E-Mail-Adresse `neue@example.com` ist noch nicht im System vergeben
- Der E-Mail-Aenderungs-Bereich befindet sich in den Account-Einstellungen (`/settings/account` oder im Profil-Tab der AccountSettingsPage)

**Testschritte**:
1. Nutzer navigiert zu den Account-Einstellungen (Profil-Tab)
2. Nutzer gibt die neue E-Mail-Adresse `neue@example.com` in das Aenderungsformular ein
3. Nutzer klickt "E-Mail-Adresse aendern" oder aequivalenter Button

**Erwartete Ergebnisse**:
- Eine Bestaetigung erscheint: "Eine Verifikations-E-Mail wurde an neue@example.com gesendet."
- Hinweistext: "Bitte bestaetigen Sie die neue Adresse. Der Link ist 24 Stunden gueltig."
- Die angezeigte E-Mail-Adresse hat sich noch NICHT geaendert (erst nach Verifikation)

**Nachbedingungen**:
- `EmailChangeRequest` mit Status `pending` wurde erstellt
- Verifikations-E-Mail wurde an `neue@example.com` gesendet

**Tags**: [req-025, email-change, art-16, verification-required, ak-04, happy-path]

---

### TC-025-030: E-Mail-Aenderung mit bereits vergebener Adresse

**Requirement**: REQ-025 § 3.2 PrivacyService.request_email_change (Pruefung: nicht bereits vergeben), AK-04
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Die E-Mail-Adresse `vorhanden@example.com` ist bereits von einem anderen Nutzer belegt

**Testschritte**:
1. Nutzer navigiert zum E-Mail-Aenderungsformular
2. Nutzer gibt `vorhanden@example.com` ein
3. Nutzer klickt den Bestaetungs-Button

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Diese E-Mail-Adresse ist bereits vergeben." (oder aequivalent)
- Kein `EmailChangeRequest` wurde erstellt
- Nutzer kann eine andere E-Mail-Adresse eingeben

**Nachbedingungen**:
- E-Mail-Adresse des Nutzers unveraendert

**Tags**: [req-025, email-change, duplicate-email, error-message]

---

### TC-025-031: E-Mail-Aenderung mit ungueltigem Format

**Requirement**: REQ-025 § 3.4 EmailChangeRequest Schema (EmailStr-Validierung)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist eingeloggt und befindet sich im E-Mail-Aenderungsformular

**Testschritte**:
1. Nutzer gibt eine ungueltige E-Mail-Adresse ein (z.B. "kein-at-zeichen")
2. Nutzer klickt den Bestaetungs-Button

**Erwartete Ergebnisse**:
- Eine Client-seitige Validierungsmeldung erscheint: "Bitte geben Sie eine gueltige E-Mail-Adresse ein."
- Der Submit wird blockiert
- Das Formular fokussiert auf das fehlerhafte Feld

**Nachbedingungen**:
- Kein Request wurde ausgeloest

**Tags**: [req-025, email-change, invalid-format, client-validation]

---

### TC-025-032: E-Mail-Verifikationslink bestaetigt die Aenderung

**Requirement**: REQ-025 § 3.2 PrivacyService.confirm_email_change, AK-04, AK-05, AK-06
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Ein `EmailChangeRequest` mit Status `pending` existiert fuer diesen Nutzer
- Der Nutzer hat eine Verifikations-E-Mail erhalten und klickt den enthaltenen Link
- Der Link-Format entspricht: `/privacy/email-change/confirm?token=<TOKEN>`

**Testschritte**:
1. Nutzer oeffnet den Verifikations-Link aus der E-Mail im Browser
2. Browser navigiert zur Bestaetungsseite

**Erwartete Ergebnisse**:
- Eine Erfolgsseite oder -meldung erscheint: "Ihre E-Mail-Adresse wurde erfolgreich aktualisiert."
- Der Nutzer wird ausgeloggt (alle Sessions invalidiert)
- Eine Info-Meldung erscheint: "Bitte melden Sie sich mit Ihrer neuen E-Mail-Adresse erneut an."
- Eine Info-E-Mail wurde an die ALTE Adresse gesendet (visuell nicht direkt pruefbar, aber in der Erfolgsmeldung erwaehnt)

**Nachbedingungen**:
- `User.email` wurde auf die neue Adresse gesetzt
- Alle bestehenden Refresh-Tokens wurden invalidiert

**Tags**: [req-025, email-change, confirm-token, sessions-invalidated, ak-04, ak-05, ak-06]

---

### TC-025-033: Abgelaufener E-Mail-Verifikationslink

**Requirement**: REQ-025 § 3.2 confirm_email_change (Ablaufdatum 24h), AK-04
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Ein `EmailChangeRequest` mit Status `expired` existiert (24h ueberschritten)
- Der Nutzer versucht, den abgelaufenen Link zu oeffnen

**Testschritte**:
1. Nutzer oeffnet einen abgelaufenen Verifikations-Link im Browser

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Dieser Link ist nicht mehr gueltig. Links sind 24 Stunden gueltig."
- Die E-Mail-Adresse wurde NICHT geaendert
- Ein Hinweis erscheint, dass eine neue E-Mail-Aenderung beantragt werden kann

**Nachbedingungen**:
- `User.email` unveraendert

**Tags**: [req-025, email-change, expired-token, error-message]

---

### TC-025-034: E-Mail-Aenderungs-Token kann nicht wiederverwendet werden

**Requirement**: REQ-025 § 3.4 EmailChangeRequest — UNIQUE INDEX on verification_token_hash
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Ein Verifikationslink wurde bereits erfolgreich genutzt (`status: confirmed`)
- Der Nutzer versucht, denselben Link ein zweites Mal zu oeffnen

**Testschritte**:
1. Nutzer oeffnet denselben Verifikationslink erneut im Browser

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Dieser Link wurde bereits verwendet." (oder "Ungueltig")
- Keine weitere Aktion wird ausgefuehrt

**Nachbedingungen**:
- Kein zweiter Aenderungsvorgang

**Tags**: [req-025, email-change, token-reuse-prevention, error-message]

---

## 7. Datenschutzrichtlinie — Art. 13/14

### TC-025-035: Datenschutzrichtlinie ist ohne Login abrufbar

**Requirement**: REQ-025 § 3.2 PrivacyService.get_privacy_policy (oeffentlich zugaenglich), AK-15
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist NICHT eingeloggt

**Testschritte**:
1. Nutzer navigiert direkt zu `/privacy/policy` (oder einem entsprechenden oeffentlichen Link im Footer)

**Erwartete Ergebnisse**:
- Die Datenschutzrichtlinie wird angezeigt, ohne dass ein Login erforderlich ist
- Die aktuelle Version und das Gueltigkeitsdatum sind sichtbar
- Eine Liste der Verarbeitungszwecke mit Rechtsgrundlagen ist aufgefuehrt
- Kontaktdaten des Verantwortlichen sind sichtbar

**Nachbedingungen**:
- Kein Login-Status veraendert

**Tags**: [req-025, privacy-policy, public-access, ak-15, unauthenticated]

---

### TC-025-036: Datenschutzrichtlinie zeigt Retention-Zusammenfassung

**Requirement**: REQ-025 § 3.4 PrivacyPolicyResponse.retention_summary, NFR-011
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ruft die oeffentliche Datenschutzrichtlinie auf

**Testschritte**:
1. Nutzer betrachtet die Datenschutzrichtlinien-Seite
2. Nutzer sucht den Abschnitt zu Aufbewahrungsfristen

**Erwartete Ergebnisse**:
- Eine Zusammenfassung der Aufbewahrungsfristen ist sichtbar
- Mindestens enthalten: Profildaten (90 Tage nach Soft-Delete), Erntedaten (5 Jahre), Behandlungsdaten (3 Jahre)
- Die rechtlichen Grundlagen fuer Aufbewahrungspflichten sind erklaert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, privacy-policy, retention-summary, nfr-011]

---

## 8. Authentifizierung und Session-Verhalten nach DSGVO-Aktionen

### TC-025-037: Aktive Sessions nach E-Mail-Aenderung invalidiert

**Requirement**: REQ-025 AK-05, § 3.2 confirm_email_change (Invalidiert alle Refresh Tokens)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf zwei Geraeten gleichzeitig eingeloggt (zwei Browser-Sessions)
- Eine E-Mail-Aenderung wurde gerade bestaetigt (Token-Link wurde angeklickt)

**Testschritte**:
1. Session A: E-Mail-Verifikationslink wird geoeffnet und bestaetigt
2. Session B: Nutzer versucht, eine geschuetzte Seite aufzurufen (z.B. Dashboard)

**Erwartete Ergebnisse**:
- Session A: Erfolgsmeldung "E-Mail aktualisiert", Nutzer wird ausgeloggt
- Session B: Nutzer wird auf die Login-Seite umgeleitet (Session ungueltig)
- In keiner Session ist weiterhin Zugriff ohne erneuten Login moeglich

**Nachbedingungen**:
- Beide Sessions sind invalidiert

**Tags**: [req-025, session-invalidation, email-change, ak-05, cross-session]

---

### TC-025-038: Aktive Sessions nach Account-Loeschung sofort invalidiert

**Requirement**: REQ-025 AK-07, § 3.2 request_erasure (Sofort: Alle Refresh Tokens invalidieren)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf zwei Geraeten gleichzeitig eingeloggt
- Eine Account-Loeschung wurde auf Geraet A bestaetigt

**Testschritte**:
1. Geraet A: Account-Loeschung wird bestaetigt
2. Geraet B: Nutzer versucht, eine beliebige Seite aufzurufen

**Erwartete Ergebnisse**:
- Geraet A: Nutzer wird sofort ausgeloggt, Loeschbestaetigung erscheint
- Geraet B: Nutzer wird auf die Login-Seite umgeleitet (Session ungueltig)
- Login mit den alten Zugangsdaten schlaegt auf beiden Geraeten fehl

**Nachbedingungen**:
- Alle Sessions des Nutzers sind invalidiert

**Tags**: [req-025, erasure, session-invalidation, ak-07, cross-session]

---

## 9. Consent-Auswirkungen auf Features

### TC-025-039: Sentry-Fehlertracking wird nach Consent-Entzug deaktiviert

**Requirement**: REQ-025 § 3.6, § 10 TTDSG TT-002 (Sentry erst nach Einwilligung)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Fehler-Tracking (Sentry)" ist aktuell erteilt
- Nutzer befindet sich auf dem Tab "Einwilligungen"

**Testschritte**:
1. Nutzer widerruft die Einwilligung "Fehler-Tracking (Sentry)" (Toggle OFF)
2. Nutzer beobachtet die Seite und erzeugt bewusst einen Frontend-Fehler (z.B. navigiert zu einer defekten URL)

**Erwartete Ergebnisse**:
- Der Toggle wechselt auf OFF, Bestaetigung erscheint
- Der Sentry-SDK sollte keine Fehlerberichte mehr senden (nicht direkt visuell pruefbar, aber der Toggle-Zustand spiegelt die Einstellung wider)
- Es erscheint KEIN Cookie-Banner oder Einwilligungs-Overlay, solange nur technisch notwendige Speicher genutzt werden

**Nachbedingungen**:
- `error_tracking`-Consent ist widerrufen

**Tags**: [req-025, consent, sentry, ttdsg, tt-002, feature-toggle]

---

### TC-025-040: HaveIBeenPwned-Check wird nach Consent-Entzug deaktiviert

**Requirement**: REQ-025 § 9 (hibp_check Consent-pflichtig), AK-14
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Einwilligung "Passwort-Sicherheitscheck" ist widerrufen
- Nutzer aendert sein Passwort in den Sicherheits-Einstellungen

**Testschritte**:
1. Nutzer navigiert zu den Sicherheits-Einstellungen (Passwort aendern)
2. Nutzer gibt ein neues Passwort ein und speichert

**Erwartete Ergebnisse**:
- Der HaveIBeenPwned-Check wird NICHT ausgefuehrt (kein Hinweis auf gecheckte Passwort-Sicherheit)
- ODER: Eine Meldung erscheint, dass der HIBP-Check aufgrund fehlender Einwilligung deaktiviert ist
- Das Passwort wird gespeichert ohne Sicherheitscheck-Warnung

**Nachbedingungen**:
- Passwort wurde geaendert, HIBP-Check nicht ausgefuehrt

**Tags**: [req-025, consent, hibp, password-change, ak-14]

---

## 10. Edge Cases und Grenzwerte

### TC-025-041: Export-Status per Seiten-Refresh aktualisieren

**Requirement**: REQ-025 § 4.2 Tab "Datenexport" — Status pending/processing/completed
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Export-Auftrag wurde soeben erstellt (Status: pending)
- Nutzer befindet sich auf dem Tab "Datenexport"

**Testschritte**:
1. Nutzer wartet einige Sekunden und laedt die Seite neu (F5 oder Seiten-Neuladung)
2. Nutzer prueft den Status des Exports

**Erwartete Ergebnisse**:
- Der aktuelle Status wird korrekt geladen (z.B. jetzt "In Bearbeitung" oder bereits "Abgeschlossen")
- Der Download-Link erscheint, sobald der Status "Abgeschlossen" ist
- Die Status-Anzeige ist konsistent mit dem Server-Zustand

**Nachbedingungen**:
- Kein neuer Export wurde angefordert

**Tags**: [req-025, data-export, status-refresh, polling-or-manual]

---

### TC-025-042: Verarbeitungseinschraenkung mit scope "all" blockiert sichtbare Features

**Requirement**: REQ-025 § 3.7 Middleware Restriction-Pruefung (scope "all" blockiert alles), AK-11
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Eine aktive Verarbeitungseinschraenkung fuer Scope "Alle Daten" (`scope: all`) existiert

**Testschritte**:
1. Nutzer navigiert zu einem Feature, das Datenverarbeitung ausloest (z.B. Stammdatenanreicherung oder Sensorwert-Eingabe)
2. Nutzer versucht, die Aktion auszufuehren

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Verarbeitung eingeschraenkt." (oder aequivalent)
- Die Aktion wird NICHT ausgefuehrt
- Ein Hinweis auf die Datenschutz-Einstellungen ist sichtbar

**Nachbedingungen**:
- Keine Datenverarbeitung erfolgte

**Tags**: [req-025, restriction, scope-all, blocked-feature, ak-11]

---

### TC-025-043: Nutzer ohne Consent-Records sieht korrekte Standardzustaende

**Requirement**: REQ-025 § 3.1 ConsentEngine.is_processing_allowed (Consent=None → nicht erlaubt)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist neu registriert und hat noch keine Consent-Entscheidungen getroffen
- Nutzer navigiert zum Tab "Einwilligungen"

**Testschritte**:
1. Nutzer betrachtet die Einwilligungsliste unmittelbar nach der Registrierung

**Erwartete Ergebnisse**:
- "Grundfunktionen" zeigt Status "Erteilt" (immer aktiv, required)
- Alle optionalen Zwecke zeigen Status "Nicht erteilt" (Toggle OFF)
- Keine abgelaufenen Zeitstempel werden angezeigt
- Der Nutzer kann optionale Einwilligungen individuell erteilen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-025, consent, new-user, default-state]

---

### TC-025-044: Mehrere Einwilligungen koennen unabhaengig voneinander verwaltet werden

**Requirement**: REQ-025 § 3.1 ConsentEngine — jeder Zweck unabhaengig steuerbar
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt
- Alle optionalen Einwilligungen sind aktuell erteilt

**Testschritte**:
1. Nutzer widerruft "Fehler-Tracking (Sentry)" (Toggle OFF)
2. Nutzer laesst "Passwort-Sicherheitscheck" auf ON
3. Nutzer widerruft "Externe Stammdatenanreicherung" (Toggle OFF)
4. Nutzer laedt die Seite neu

**Erwartete Ergebnisse**:
- Nach Neuladung: "Fehler-Tracking (Sentry)" = OFF, "Passwort-Sicherheitscheck" = ON, "Externe Stammdatenanreicherung" = OFF
- Jede Einwilligung hat ihren eigenen Zeitstempel
- Kein Consent beeinflusst einen anderen

**Nachbedingungen**:
- Drei Consents haben unterschiedliche Status

**Tags**: [req-025, consent, independent-management, persistence]

---

### TC-025-045: Export-Datei enthaelt alle im Manifest definierten Datenkategorien

**Requirement**: REQ-025 § 3.1 DataExportEngine.USER_DATA_MANIFEST, AK-01, AK-16
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt und hat Daten in mehreren Kategorien (Profil, Aufgaben, Ernte, Einwilligungen)
- Ein abgeschlossener Export mit Status `completed` ist verfuegbar

**Testschritte**:
1. Nutzer oeffnet den Tab "Datenexport"
2. Nutzer klickt "Herunterladen" fuer den abgeschlossenen Export
3. Nutzer oeffnet die heruntergeladene JSON-Datei

**Erwartete Ergebnisse**:
- Die JSON-Datei enthaelt Abschnitte fuer alle definierten Datenkategorien:
  - "Profildaten" (E-Mail, Anzeigename, Locale, Zeitzone)
  - "Verknuepfte Authentifizierungs-Provider"
  - "Aktive Sessions" (Geraet, IP anonymisiert, Ablauf)
  - "Tenant-Mitgliedschaften"
  - "Einwilligungen"
  - "Zugewiesene Aufgaben"
  - "Erntedaten"
  - "Inspektionsprotokolle"
- Die Datei ist valides JSON
- Keine Passwoerter oder rohen Token sind enthalten

**Nachbedingungen**:
- Download-Zaehler wurde inkrementiert

**Tags**: [req-025, data-export, json-content, manifest, ak-01]

---

### TC-025-046: Gleichzeitige Einwilligungsverwaltung — Konsistenz nach Neuladung

**Requirement**: REQ-025 § 2 ArangoDB — UNIQUE INDEX on [user_key, purpose] (Upsert-Verhalten)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- Nutzer ist eingeloggt und der Tab "Einwilligungen" ist in zwei Browser-Tabs geoeffnet

**Testschritte**:
1. Tab 1: Nutzer erteilt Einwilligung "Fehler-Tracking" (Toggle ON)
2. Tab 2: Nutzer widerruft Einwilligung "Fehler-Tracking" (Toggle OFF)
3. Tab 1: Nutzer laedt die Seite neu

**Erwartete Ergebnisse**:
- Nach Neuladung in Tab 1 wird der aktuelle Status korrekt angezeigt (letzter Schreibvorgang gewinnt)
- Kein Widerspruch zwischen den Tabs

**Nachbedingungen**:
- Konsistenter Zustand nach Neuladung

**Tags**: [req-025, consent, concurrent-edit, consistency, edge-case]

---

## 11. Vollstaendige Abdeckungs-Matrix

| REQ-025 Spezifikations-Abschnitt | Testfall-IDs |
|----------------------------------|--------------|
| § 1.1 Szenario 1: Datenexport | TC-025-010, TC-025-011, TC-025-012, TC-025-013, TC-025-014, TC-025-015, TC-025-041, TC-025-045 |
| § 1.1 Szenario 2: E-Mail-Aenderung | TC-025-029, TC-025-030, TC-025-031, TC-025-032, TC-025-033, TC-025-034, TC-025-037 |
| § 1.1 Szenario 3: Account-Loeschung | TC-025-016, TC-025-017, TC-025-018, TC-025-019, TC-025-020, TC-025-021, TC-025-022, TC-025-038 |
| § 1.1 Szenario 4: Einwilligungsverwaltung | TC-025-004, TC-025-005, TC-025-006, TC-025-007, TC-025-008 |
| § 3.1 DataExportEngine | TC-025-010, TC-025-011, TC-025-045 |
| § 3.1 ErasureEngine | TC-025-016, TC-025-019, TC-025-021 |
| § 3.1 ConsentEngine | TC-025-004, TC-025-005, TC-025-043, TC-025-044 |
| § 3.2 PrivacyService (alle Methoden) | TC-025-010 bis TC-025-034, TC-025-039 bis TC-025-041 |
| § 3.3 API Auth-Schutz | TC-025-002 |
| § 3.6 Consent-Middleware (require_consent) | TC-025-009, TC-025-040 |
| § 3.7 Restriction-Middleware | TC-025-042 |
| § 4.1 Navigation und Routing | TC-025-001, TC-025-002, TC-025-003 |
| § 4.2 Tab "Einwilligungen" | TC-025-004 bis TC-025-009, TC-025-039, TC-025-040, TC-025-043, TC-025-044, TC-025-046 |
| § 4.2 Tab "Datenexport" | TC-025-010 bis TC-025-015, TC-025-041, TC-025-045 |
| § 4.2 Tab "Account loeschen" | TC-025-016 bis TC-025-022, TC-025-038 |
| § 4.2 Tab "Verarbeitungseinschraenkung" | TC-025-023 bis TC-025-028, TC-025-042 |
| § 6 Abnahmekriterien (AK-01 bis AK-17) | Alle relevanten AKs durch obige Tests abgedeckt |
| § 6 Frontend-Kriterien (FK-01 bis FK-05) | TC-025-001, TC-025-005 bis 025-007, TC-025-011, TC-025-016 bis TC-025-018 |
| § 9 Datenschutz-Bewertung externer Dienste | TC-025-009, TC-025-039, TC-025-040 |
| § 10 TTDSG-Konformitaet | TC-025-039 |
| Datenschutzrichtlinie oeffentlich | TC-025-035, TC-025-036 |

---

## 12. Abnahmekriterien-Traceability

| AK/FK | Beschreibung | Testfall(e) |
|-------|-------------|-------------|
| AK-01 | Datenexport enthaelt alle Manifest-Daten | TC-025-045 |
| AK-02 | Export nach 72h nicht mehr downloadbar | TC-025-013 |
| AK-03 | Max. 1 aktiver Export pro User | TC-025-011 |
| AK-04 | E-Mail-Aenderung erfordert Token-Verifikation (24h) | TC-025-029, TC-025-032, TC-025-033 |
| AK-05 | Sessions nach E-Mail-Aenderung invalidiert | TC-025-037 |
| AK-06 | Info-E-Mail an alte Adresse | TC-025-032 (Erwaehnung in Erfolgsmeldung) |
| AK-07 | Kontolöschung: Soft-Delete sofort | TC-025-019 |
| AK-08 | Erntedaten/Behandlungen anonymisiert, nicht geloescht | TC-025-021 |
| AK-08a | Loeschbestaetigung zeigt fully_deleted vs. anonymized | TC-025-016, TC-025-021 |
| AK-09 | Hard-Delete nach 90 Tagen | (Celery-Aufgabe — kein direkter E2E-Test moeglich) |
| AK-10 | Erasure-Audit-Log 1 Jahr aufbewahrt | (Backend-Integration-Test) |
| AK-11 | Verarbeitungseinschraenkung blockiert Endpunkte | TC-025-042 |
| AK-12 | Widerspruch erstellt Restriction reason=objection_pending | TC-025-027 |
| AK-13 | Erforderliche Einwilligungen nicht widerrufbar | TC-025-005 |
| AK-14 | Consent-Pruefung blockiert Features ohne Einwilligung | TC-025-009, TC-025-040 |
| AK-15 | Datenschutzrichtlinie ohne Auth abrufbar | TC-025-035 |
| AK-16 | Celery-Task erstellt korrekte JSON-Datei | TC-025-045 (via Download-Inhaltspruefung) |
| AK-17 | Celery-Task execute_scheduled_erasures | (Backend-Integration-Test) |
| FK-01 | PrivacySettingsPage zeigt alle 4 Tabs | TC-025-001 |
| FK-02 | Einwilligungs-Toggles funktionieren | TC-025-006, TC-025-007 |
| FK-03 | Erforderliche Einwilligungen als nicht-aenderbar dargestellt | TC-025-005 |
| FK-04 | Export-Button deaktiviert waehrend Export laeuft | TC-025-011 |
| FK-05 | Loeschdialog erfordert Passwort und Checkbox | TC-025-017, TC-025-018 |
