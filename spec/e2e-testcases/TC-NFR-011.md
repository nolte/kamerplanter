---
req_id: NFR-011
title: Vorratsdatenspeicherung & Aufbewahrungsfristen
category: Datenschutz & Compliance
test_count: 38
coverage_areas:
  - Account-Loeschung (Soft-Delete, sichtbare UI-Zustaende) — R-01, R-02
  - Sitzungsverwaltung und IP-Anonymisierung — R-03, R-11
  - Einladungsverwaltung (abgelaufene Einladungen) — R-12
  - Datenexport-Ablauf (Status "Abgelaufen") — R-05
  - Admin-Benutzerverwaltung und Loeschbestaetigung — R-01
  - Ernte- und Behandlungsdaten: Anonymisierung statt Loeschung — R-16, R-17, R-18
  - Sensor-Downsampling: Eingeschraenkte Detailaufloesung nach Fristablauf — R-14
  - Konfigurierbarkeit: Mindestfristen-Schutzwall (nicht unterschreitbar) — AK-10
  - DSGVO-Interaktion: Account-Loeschung blockiert gesetzliche Aufbewahrungspflichten — §5
  - Monitoring: Retention-Lauf-Status in Admin-Auswertung — AK-05, AK-06
generated: 2026-03-21
version: "1.0"
status: >
  Testfaelle decken die gesamte Retention-Matrix ab.
  Teile mit direktem UI-Mapping (Account-Loeschung, Sitzungen, Einladungen, Export-Status) sind
  sofort ausfuehrbar. Teile die Zeitablauf voraussetzen (Anonymisierung nach 7 Tagen,
  Hard-Delete nach 90 Tagen) erfordern Test-Clock-Injection oder Datenbankseeding mit
  backdatierten Timestamps. PrivacySettingsPage (REQ-025) noch nicht implementiert —
  betroffene Testfaelle als "ausstehend" markiert.
---

# TC-NFR-011: Vorratsdatenspeicherung & Aufbewahrungsfristen

Dieses Dokument enthaelt End-to-End-Testfaelle aus **NFR-011 Vorratsdatenspeicherung &
Aufbewahrungsfristen v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser.
Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in den Testschritten.
Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm
erwartet.

**Hinweis zur Testausfuehrung:** NFR-011 ist ein Cross-Cutting Concern. Die meisten
Retention-Effekte sind im Browser nur als *Zustandsaenderung nach Zeitablauf* sichtbar.
Fuer automatisierte E2E-Tests muessen Systemzeit oder Seed-Daten mit backdatierten Timestamps
manipuliert werden (z.B. per Playwright `clock.setSystemTime()` oder Testdaten-Fixture mit
`updated_at = now() - 91 days`). Testfaelle, die zeitbasiertes Seeding erfordern, sind
entsprechend markiert.

**Abhaengigkeiten:** REQ-023 (Auth, Sessions, User-Datenmodell), REQ-024 (Tenant,
Einladungen), REQ-025 (DSGVO Selbstauskunft, Datenexport — noch ausstehend), REQ-007 (Ernte),
REQ-010 (IPM, Behandlungen).

---

## 1. Account-Loeschung und Soft-Delete (R-01, R-02)

Die Nutzer-Perspektive auf R-01 (Soft-Delete → Hard-Delete nach 90 Tagen) und R-02
(unbestaetigt → Hard-Delete nach 7 Tagen) zeigt sich in zwei Kontexten: (a) Nutzer loescht
selbst sein Konto ueber Account-Einstellungen, (b) Platform-Admin loescht Nutzer ueber das
Admin-Panel.

---

### TC-NFR011-001: Nutzer loescht eigenes Konto — Weiterleitung zur Login-Seite

**Requirement**: NFR-011 §2.1 R-01 — Soft-Delete + Retention 90 Tage; REQ-025 §3 Account-Loeschung
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt (z.B. `demo@kamerplanter.local`)
- Nutzer hat keine aktiven Eintraege, die gesetzliche Aufbewahrungspflichten ausloesen

**Testschritte**:
1. Nutzer navigiert zu `/settings` und oeffnet den Tab "Konto"
2. Nutzer liest den Warnhinweis "Das Loeschen Ihres Kontos kann nicht rueckgaengig gemacht werden. Alle Daten werden unwiderruflich entfernt."
3. Nutzer klickt auf den Button "Konto loeschen" (`data-testid="delete-account-btn"`)
4. Ein Browser-Bestaedigungsdialog erscheint mit dem Text: "Sind Sie sicher, dass Sie Ihr Konto loeschen moechten? Dies kann nicht rueckgaengig gemacht werden."
5. Nutzer klickt auf "OK"

**Erwartete Ergebnisse**:
- Der Bestaedigungsdialog schliesst sich
- Der Browser navigiert automatisch zur Seite `/login`
- Auf der Login-Seite ist der Nutzer ausgeloggt — kein Name, kein Avatar in der Navigation
- Eine erneute Anmeldung mit denselben Zugangsdaten (`demo@kamerplanter.local`) ist **nicht moeglich** (Account im Soft-Delete-Zustand)
- Eine Fehlermeldung erscheint beim Login-Versuch: "Ungueltige Zugangsdaten" oder ein gleichwertiger Fehlertext

**Postconditions**:
- Account befindet sich im Zustand `status: deleted` (Soft-Delete)
- Nach 90 Tagen (Retention R-01) wird der Account endgueltig geloescht (Hard-Delete, nicht E2E-testbar ohne Zeitmanipulation)

**Tags**: [nfr-011, R-01, soft-delete, account-loeschung, auth, req-023]

---

### TC-NFR011-002: Nutzer bricht Account-Loeschung ab

**Requirement**: NFR-011 §2.1 R-01 — Soft-Delete
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich im Tab "Konto" der Account-Einstellungen

**Testschritte**:
1. Nutzer klickt auf den Button "Konto loeschen" (`data-testid="delete-account-btn"`)
2. Ein Browser-Bestaedigungsdialog erscheint mit Text "Sind Sie sicher...?"
3. Nutzer klickt auf "Abbrechen"

**Erwartete Ergebnisse**:
- Der Dialog schliesst sich ohne Aktion
- Der Nutzer bleibt auf der Account-Einstellungsseite eingeloggt
- Die Seite zeigt unveraendert den Tab "Konto" mit dem "Konto loeschen"-Button

**Postconditions**:
- Account-Status unveraendert (weiterhin aktiv)

**Tags**: [nfr-011, R-01, soft-delete, abbruch, dialog]

---

### TC-NFR011-003: Platform-Admin loescht Nutzer sofort ueber Admin-Panel (Hard-Delete)

**Requirement**: NFR-011 §2.1 R-01; Pages: `/admin/users/:key`
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist als Platform-Admin eingeloggt
- Zu loeschender Testnutzer (z.B. `test-delete@kamerplanter.local`) existiert, Status "Aktiv"
- Der Testnutzer hat keine Ernte-/Behandlungs-/Inspektionsdaten (keine gesetzliche Aufbewahrungspflicht aktiv)

**Testschritte**:
1. Platform-Admin navigiert zu `/admin/users`
2. Admin sucht den Testnutzer in der Nutzerliste und klickt auf seinen Namen oder den Bearbeiten-Button
3. Auf der Nutzer-Detailseite scrollt Admin nach unten bis zur "Danger Zone"
4. Admin klickt auf den Button "Benutzer loeschen" (`data-testid="delete-user-btn"`)
5. Ein roter Bestaetigungsbereich erscheint mit dem Text: "Sind Sie sicher, dass Sie den Benutzer 'Testnutzer' (test-delete@kamerplanter.local) und alle zugehoerigen Daten unwiderruflich loeschen moechten?"
6. Admin klickt auf den roten Button "Endgueltig loeschen" (`data-testid="confirm-delete-user-btn"`)

**Erwartete Ergebnisse**:
- Die Seite zeigt eine Erfolgs-Snackbar: "Benutzer geloescht"
- Admin wird zur Nutzerliste `/admin/users` weitergeleitet
- Der geloeschte Nutzer erscheint **nicht** mehr in der Nutzerliste
- Eine Suche nach der E-Mail-Adresse des Nutzers liefert keine Ergebnisse

**Postconditions**:
- Nutzer-Account wurde entfernt
- Login mit den Zugangsdaten des geloeschten Nutzers schlaegt fehl

**Tags**: [nfr-011, R-01, hard-delete, admin, req-023, admin-panel]

---

### TC-NFR011-004: Platform-Admin bricht Nutzer-Loeschung ab (zweistufiger Dialog)

**Requirement**: NFR-011 §2.1 R-01; UX-Sicherheit
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Nutzer ist als Platform-Admin eingeloggt
- Zu loeschender Testnutzer existiert auf `/admin/users/:key`

**Testschritte**:
1. Admin oeffnet die Nutzer-Detailseite und klickt auf "Benutzer loeschen" (`data-testid="delete-user-btn"`)
2. Der rote Bestaetigungsbereich erscheint
3. Admin klickt auf "Abbrechen"

**Erwartete Ergebnisse**:
- Der rote Bestaetigungsbereich verschwindet
- Der Button "Benutzer loeschen" erscheint wieder
- Der Nutzer ist weiterhin in der Datenbank sichtbar (kein Seiteneffekt)

**Postconditions**:
- Nutzer-Account unveraendert

**Tags**: [nfr-011, R-01, hard-delete, abbruch, admin-panel]

---

### TC-NFR011-005: Unbestaetiger Account erscheint in Admin-Liste mit Status "Nicht verifiziert"

**Requirement**: NFR-011 §2.1 R-02 — Unbestaetiigte Accounts, 7 Tage Frist
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Platform-Admin ist eingeloggt
- Mindestens ein Nutzer mit Status "unverified" existiert (z.B. durch Registrierung ohne E-Mail-Bestaetigung)

**Testschritte**:
1. Platform-Admin navigiert zu `/admin/users`
2. Admin betrachtet die Nutzerliste

**Erwartete Ergebnisse**:
- Unbestaetiigte Nutzer werden in der Liste mit einem Chip/Label "Nicht verifiziert" (`adminUnverified`) gekennzeichnet
- Das Konto erscheint mit dem Status-Chip in der entsprechenden Spalte
- (Hinweis fuer Tester: Nach 7 Tagen wird dieser Account automatisch geloescht — nicht E2E-testbar ohne Zeitmanipulation)

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-02, unverified, admin-panel, listenansicht]

---

### TC-NFR011-006: Harter Loeschlauf — unbestaetiger Account nach 7 Tagen verschwunden (zeitabhaengig)

**Requirement**: NFR-011 §2.1 R-02 — Hard-Delete nach 7 Tagen
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testdaten-Fixture: Nutzer mit `status: unverified` und `created_at = JETZT - 8 Tage` existiert in der Datenbank
- Celery-Retention-Task wurde einmalig ausgefuehrt (Testumgebung: Task manuell getriggert)

**Testschritte**:
1. Platform-Admin navigiert zu `/admin/users`
2. Admin sucht nach der E-Mail-Adresse des 8 Tage alten unbestaetigen Testnutzers
3. Admin betrachtet die Suchergebnisse

**Erwartete Ergebnisse**:
- Der Nutzer erscheint **nicht** mehr in der Liste
- Die Suche liefert keine Treffer fuer diesen Account
- (Optional) Kein Fehler oder Ladezustand — die Liste zeigt normal "Keine Ergebnisse" fuer diese Suche

**Postconditions**:
- Unbestaetiger Account wurde durch Retention-Task entfernt

**Tags**: [nfr-011, R-02, hard-delete, unverified, zeitabhaengig, celery, admin-panel]

---

## 2. Sitzungsverwaltung und IP-Anonymisierung (R-03, R-11)

Der Nutzer sieht aktive Sitzungen in AccountSettingsPage unter Tab "Sitzungen". Die
IP-Anonymisierung (R-03) ist fuer den Nutzer im Browser nicht direkt sichtbar — der Test
kann nur pruefen, ob eine Sitzung die IP-Adresse noch anzeigt (falls das UI IPs zeigt) oder
ob alte Sitzungen aus der Liste verschwunden sind (R-11).

---

### TC-NFR011-007: Nutzer sieht aktive Sitzungen in Account-Einstellungen

**Requirement**: NFR-011 §2.1 R-03, R-11 — Sitzungsdaten; REQ-023 §2
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens eine aktive Sitzung besteht (aktuelle Sitzung)

**Testschritte**:
1. Nutzer navigiert zu `/settings` und klickt auf den Tab "Sitzungen"
2. Nutzer betrachtet die angezeigte Sitzungsliste

**Erwartete Ergebnisse**:
- Eine Tabelle oder Kartenliste der aktiven Sitzungen wird angezeigt
- Der Abschnittstitel "Aktive Sitzungen" ist sichtbar
- Die aktuelle Sitzung ist mit dem Label "Aktuelle Sitzung" hervorgehoben
- Jede Sitzung zeigt ihren Typ: "Persistent" oder "Sitzung" (entsprechend Anmelde-Option)
- Abgelaufene Sitzungen (R-11) erscheinen **nicht** in der Liste

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-03, R-11, sessions, sitzungen, listenansicht, req-023]

---

### TC-NFR011-008: Nutzer widerruft eine einzelne aktive Sitzung

**Requirement**: NFR-011 §2.1 R-11 — Abgelaufene Refresh Tokens sofort loeschen; REQ-023 §2
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist von zwei verschiedenen Browsern/Geraeten eingeloggt (zwei aktive Sitzungen)
- Nutzer befindet sich im Tab "Sitzungen" der Account-Einstellungen

**Testschritte**:
1. Nutzer sieht zwei Sitzungen in der Liste (eine davon ist die aktuelle Sitzung)
2. Nutzer klickt auf den Widerrufen-Button der **anderen** (nicht-aktuellen) Sitzung
3. Eine Bestaetigung oder sofortige Entfernung erfolgt

**Erwartete Ergebnisse**:
- Die widerrufene Sitzung verschwindet sofort aus der Liste
- Die aktuelle Sitzung bleibt weiterhin sichtbar und aktiv
- Der Nutzer ist weiterhin eingeloggt
- Eine Erfolgs-Snackbar oder ein visuelles Feedback bestaetigt den Widerruf

**Postconditions**:
- Ein Refresh-Token wurde invalidiert

**Tags**: [nfr-011, R-11, sessions, sitzungs-widerruf, refresh-token]

---

### TC-NFR011-009: Passwort-Aenderung beendet alle anderen Sitzungen

**Requirement**: NFR-011 §2.1 R-11 — Abgelaufene Tokens sofort loeschen; REQ-023 §2
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist von zwei verschiedenen Browsern eingeloggt (zwei aktive Sitzungen)
- Nutzer befindet sich im Tab "Sicherheit" der Account-Einstellungen

**Testschritte**:
1. Nutzer gibt das aktuelle Passwort ein und ein neues Passwort (mind. 8 Zeichen)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Erfolgs-Snackbar erscheint: "Passwort geaendert. Alle Sitzungen wurden beendet."
- Im Tab "Sitzungen" erscheint nach Neuladen nur noch die aktuelle Sitzung
- Alle anderen Sitzungen (andere Browser/Geraete) sind aus der Liste entfernt

**Postconditions**:
- Alle anderen Refresh-Tokens wurden invalidiert und entsprechend R-11 bereinigt

**Tags**: [nfr-011, R-11, sessions, passwort-aenderung, refresh-token]

---

### TC-NFR011-010: IP-Anonymisierung — alte Sitzungseintraege zeigen anonymisierte IP (zeitabhaengig)

**Requirement**: NFR-011 §2.1 R-03 — IPv4 letztes Oktett → 0 nach 7 Tagen
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Testdaten-Fixture: Eine Sitzung mit `issued_at = JETZT - 8 Tage` und einer konkreten IPv4-Adresse (z.B. `192.168.1.42`) existiert
- Celery-Anonymisierungs-Task wurde ausgefuehrt
- (Hinweis: Test nur ausfuehrbar wenn UI die IP-Adresse der Sitzung anzeigt)

**Testschritte**:
1. Nutzer navigiert zu `/settings` → Tab "Sitzungen"
2. Nutzer betrachtet die 8 Tage alte Sitzung (falls sichtbar)

**Erwartete Ergebnisse**:
- Falls das UI die IP-Adresse anzeigt: Die angezeigte Adresse lautet `192.168.1.0` (letztes Oktett anonymisiert)
- Keine vollstaendige IP-Adresse sichtbar fuer diese Sitzung
- (Fallback-Pruefung: Wenn UI keine IPs anzeigt, ist dieser Test nicht anwendbar — Pruefung erfolgt dann auf Integrations-Ebene)

**Postconditions**:
- IP-Adresse dieser Sitzung ist anonymisiert

**Tags**: [nfr-011, R-03, ip-anonymisierung, sessions, zeitabhaengig, celery]

---

## 3. Einladungsverwaltung — Abgelaufene Einladungen (R-12)

Einladungen werden in TenantSettingsPage angezeigt. Abgelaufene Einladungen erhalten den
Status-Chip "Abgelaufen". Nach 30 Tagen nach Ablauf werden sie durch den Retention-Task
geloescht (R-12).

---

### TC-NFR011-011: Abgelaufene Einladung zeigt Status "Abgelaufen" in Tenant-Einstellungen

**Requirement**: NFR-011 §2.1 R-12 — Einladungen, 30 Tage nach Ablauf loeschen; REQ-024
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist als Tenant-Admin eingeloggt
- Testdaten-Fixture: Eine Einladung mit `status: expired` und `expires_at` in der Vergangenheit existiert im Tenant
- Nutzer befindet sich auf den Tenant-Einstellungen `/t/{slug}/settings` → Tab "Einladungen"

**Testschritte**:
1. Nutzer oeffnet die Tenant-Einstellungsseite und klickt auf den Tab "Einladungen"
2. Nutzer betrachtet die Einladungsliste

**Erwartete Ergebnisse**:
- Die abgelaufene Einladung erscheint in der Liste mit dem Status-Chip "Abgelaufen" (`enums.invitationStatus.expired`)
- Der Status-Chip hat die Farbe `default` (nicht `warning` wie bei ausstehenden Einladungen)
- Der Widerrufen-Button ist fuer abgelaufene Einladungen **nicht** sichtbar oder deaktiviert

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-12, einladungen, expired, tenant-settings, req-024]

---

### TC-NFR011-012: Abgelaufene Einladung nach 30 Tagen + Retention-Task nicht mehr sichtbar (zeitabhaengig)

**Requirement**: NFR-011 §2.1 R-12 — Hard-Delete 30 Tage nach Ablauf
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist als Tenant-Admin eingeloggt
- Testdaten-Fixture: Eine Einladung mit `status: expired` und `expires_at = JETZT - 31 Tage` existiert
- Celery-Retention-Task wurde ausgefuehrt

**Testschritte**:
1. Nutzer oeffnet die Tenant-Einstellungen → Tab "Einladungen"
2. Nutzer betrachtet die vollstaendige Einladungsliste

**Erwartete Ergebnisse**:
- Die 31 Tage alte abgelaufene Einladung erscheint **nicht** mehr in der Liste
- Die Liste zeigt entweder "Keine ausstehenden Einladungen." (`noInvitations`) oder nur noch gueltuge Eintraege

**Postconditions**:
- Abgelaufene Einladung wurde durch Retention-Task entfernt

**Tags**: [nfr-011, R-12, einladungen, hard-delete, zeitabhaengig, celery]

---

### TC-NFR011-013: Nutzer widerruft eine ausstehende Einladung manuell (vor Ablauf)

**Requirement**: NFR-011 §2.1 R-12 — Einladungslebenszyklus; REQ-024
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist als Tenant-Admin eingeloggt
- Eine ausstehende Einladung (`status: pending`) existiert im Tenant

**Testschritte**:
1. Nutzer oeffnet Tenant-Einstellungen → Tab "Einladungen"
2. Nutzer klickt auf den Widerrufen-Button der ausstehenden Einladung (`data-testid="revoke-invitation-{key}"`)

**Erwartete Ergebnisse**:
- Die Einladung verschwindet sofort aus der Liste oder aendert ihren Status auf "Abgelaufen"
- Eine Erfolgs-Snackbar oder visuelles Feedback bestaetigt den Widerruf
- Die eingeladene E-Mail-Adresse kann erneut eingeladen werden

**Postconditions**:
- Einladung invalidiert

**Tags**: [nfr-011, R-12, einladungen, widerruf, req-024]

---

## 4. Datenexport — Ablauf nach 72 Stunden (R-05)

Der Datenexport (REQ-025, PrivacySettingsPage) ist noch nicht implementiert. Diese Testfaelle
beschreiben das Soll-Verhalten gemaess NFR-011 §2.1 R-05 und sind als spec-forward markiert.

---

### TC-NFR011-014: Abgelaufener Datenexport zeigt Status "Abgelaufen" (spec-forward, PrivacySettingsPage ausstehend)

**Requirement**: NFR-011 §2.1 R-05 — Export-Dateien 72 Stunden, danach Status "expired"
**Priority**: High
**Category**: Detailansicht
**Status**: Ausstehend — PrivacySettingsPage nicht implementiert
**Preconditions**:
- Nutzer ist eingeloggt
- PrivacySettingsPage unter `/settings/privacy` ist implementiert
- Testdaten-Fixture: Ein Datenexport mit `status: completed` und `completed_at = JETZT - 73 Stunden` existiert
- Celery-Retention-Task wurde ausgefuehrt

**Testschritte**:
1. Nutzer navigiert zu `/settings/privacy` → Tab "Datenexport"
2. Nutzer betrachtet die Exportliste

**Erwartete Ergebnisse**:
- Der 73 Stunden alte Export zeigt den Status "Abgelaufen" in der Liste
- Der Download-Button ist deaktiviert oder nicht vorhanden
- Ein Hinweis erklaert: "Der Download-Link ist abgelaufen. Bitte einen neuen Export anfordern."
- Die Export-Datei ist **nicht** mehr herunterzuladen (HTTP 404 oder aequivalente Fehlermeldung)

**Postconditions**:
- Export-Datei vom Dateisystem entfernt, Status auf "expired" gesetzt

**Tags**: [nfr-011, R-05, datenexport, expired, privacy-settings, req-025, ausstehend]

---

### TC-NFR011-015: Neuer Datenexport kann nach Ablauf erneut angefordert werden (spec-forward)

**Requirement**: NFR-011 §2.1 R-05; REQ-025 §3 Datenexport
**Priority**: Medium
**Category**: Happy Path
**Status**: Ausstehend — PrivacySettingsPage nicht implementiert
**Preconditions**:
- Nutzer ist eingeloggt
- PrivacySettingsPage implementiert
- Ein zuvor erstellter Export hat Status "Abgelaufen"

**Testschritte**:
1. Nutzer navigiert zu `/settings/privacy` → Tab "Datenexport"
2. Nutzer klickt auf "Neuen Export anfordern"

**Erwartete Ergebnisse**:
- Ein neuer Export wird erstellt mit Status "In Bearbeitung" oder "Ausstehend"
- Der Export-Button ist waehrend der Verarbeitung deaktiviert ("Nur ein aktiver Export gleichzeitig moeglich")
- Nach Verarbeitung erscheint ein Download-Link mit Hinweis auf 72-Stunden-Gueltigkeit

**Postconditions**:
- Neuer Export-Datensatz erstellt

**Tags**: [nfr-011, R-05, datenexport, neuer-export, req-025, ausstehend]

---

## 5. Erntedaten und Behandlungsanwendungen: Anonymisierung statt Loeschung (R-16, R-17, R-18, §5)

Wenn ein Nutzer sein Konto loescht, werden Ernte- (R-16, 5 Jahre CanG), Behandlungs- (R-17,
3 Jahre PflSchG) und Inspektionsdaten (R-18, 3 Jahre PflSchG) **nicht geloescht**, sondern
anonymisiert: Der Nutzerbezug wird entfernt, die Fachdaten bleiben erhalten.

---

### TC-NFR011-016: Erntedaten nach Account-Loeschung zeigen keinen Nutzerbezug mehr (zeitabhaengig nach Loeschung)

**Requirement**: NFR-011 §2.3 R-16, §5 Punkt 3 — Anonymisierung Erntedaten; REQ-007
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testnutzer `ernte-test@kamerplanter.local` hat mindestens eine HarvestBatch-Eintraege erstellt
- Testnutzer wurde geloescht (Konto-Loeschung erfolgt, z.B. 91 Tage zurueckliegend — Hard-Delete ausgefuehrt)
- Platform-Admin hat Zugriff auf Ernte-Uebersicht des Tenants

**Testschritte**:
1. Platform-Admin oeffnet die Ernte-Uebersicht des betroffenen Tenants (z.B. `/t/{slug}/ernte`)
2. Admin betrachtet die Ernte-Liste und sucht nach dem Eintrag des geloeschten Nutzers

**Erwartete Ergebnisse**:
- Die Ernte-Eintraege sind weiterhin in der Liste sichtbar (gesetzliche Aufbewahrungspflicht CanG 5 Jahre)
- Felder die den Nutzer identifizieren (Erstellt-Von, Verantwortlicher etc.) zeigen "Unbekannt", "Anonymisiert" oder einen leeren Wert
- Die Erntemengen, Qualitaetsbewertungen und Zeitstempel sind vollstaendig erhalten
- Kein Fehler beim Laden der Seite

**Postconditions**:
- Erntedaten bleiben fuer 5 Jahre aufbewahrt (CanG-Pflicht), ohne Personenbezug

**Tags**: [nfr-011, R-16, ernte, anonymisierung, canG, req-007, zeitabhaengig]

---

### TC-NFR011-017: Behandlungsanwendungen nach Account-Loeschung — Karenz-Daten bleiben erhalten

**Requirement**: NFR-011 §2.3 R-17, §5 Punkt 3 — Anonymisierung Behandlungsdaten; REQ-010; PflSchG §11
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testnutzer hat TreatmentApplication-Eintraege erstellt (insbesondere chemische Behandlungen mit Karenzzeit)
- Testnutzer wurde geloescht und Hard-Delete wurde ausgefuehrt

**Testschritte**:
1. Platform-Admin navigiert zur Behandlungs-Uebersicht des betroffenen Tenants
2. Admin betrachtet die Behandlungsprotokolle

**Erwartete Ergebnisse**:
- Die Behandlungseintraege sind weiterhin sichtbar (PflSchG-Pflicht 3 Jahre)
- Wirkstoff, Dosierung, Anwendungsdatum und Karenzzeit-Felder sind vollstaendig vorhanden
- Das Feld "Durchgefuehrt von" zeigt "Anonymisiert" oder ist leer
- Keine Assoziation mit dem geloeschten Nutzernamen in der Anzeige

**Postconditions**:
- Behandlungsdaten bleiben 3 Jahre erhalten (PflSchG), ohne Personenbezug

**Tags**: [nfr-011, R-17, behandlung, anonymisierung, pflschg, karenz, req-010, zeitabhaengig]

---

### TC-NFR011-018: Inspektionsprotokolle nach Account-Loeschung — fachliche Daten erhalten

**Requirement**: NFR-011 §2.3 R-18, §5 Punkt 3 — Anonymisierung Inspektionsdaten; REQ-010; PflSchG §11
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testnutzer hat Inspektionseintraege erstellt
- Testnutzer wurde geloescht

**Testschritte**:
1. Platform-Admin navigiert zu den Inspektionsprotokollen des betroffenen Tenants
2. Admin betrachtet die Inspektionsliste

**Erwartete Ergebnisse**:
- Inspektionseintraege bleiben sichtbar (PflSchG-Pflicht 3 Jahre)
- Befunddaten (Schadorganismus, Schweregrad, Befall-Beschreibung) sind vollstaendig
- Der Nutzer-Bezug ("Inspekteur" oder aequivalentes Feld) zeigt "Anonymisiert" oder ist leer
- Kein Fehler beim Laden der Seite

**Postconditions**:
- Inspektionsdaten 3 Jahre aufbewahrt ohne Personenbezug

**Tags**: [nfr-011, R-18, inspektionen, anonymisierung, pflschg, req-010, zeitabhaengig]

---

### TC-NFR011-019: DSGVO-Loeschanfrage — Erntedaten werden anonymisiert, nicht geloescht (spec-forward)

**Requirement**: NFR-011 §5 Punkt 3 — Art. 17 Abs. 3 lit. b; REQ-025 §3 Account-Loeschung; REQ-007
**Priority**: Critical
**Category**: Fehlermeldung / Hinweismeldung
**Status**: Ausstehend — PrivacySettingsPage nicht vollstaendig implementiert
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer hat Ernte-Eintraege (HarvestBatch innerhalb der 5-Jahres-Frist)
- PrivacySettingsPage mit "Account loeschen"-Tab implementiert

**Testschritte**:
1. Nutzer navigiert zu `/settings/privacy` → Tab "Account loeschen"
2. Nutzer initiert den Loeschprozess (Passwort bestaetigen, Checkbox aktivieren)
3. Nutzer bestaetigt die Loeschung

**Erwartete Ergebnisse**:
- Eine Erfolgsmeldung erscheint oder der Nutzer wird zur Login-Seite weitergeleitet
- Ein Informationstext weist explizit darauf hin, welche Datenkategorien anonymisiert (nicht geloescht) werden: z.B. "Erntedaten werden gemaess CanG 5 Jahre aufbewahrt, Ihre Identitaet wird jedoch entfernt."
- Die Kategorien sind klar unterschieden: "Vollstaendig geloescht" vs. "Anonymisiert (gesetzliche Pflicht)"

**Postconditions**:
- Account im Soft-Delete-Zustand
- Erntedaten anonymisiert aber erhalten

**Tags**: [nfr-011, R-16, dsgvo, art17, anonymisierung, canG, req-025, ausstehend]

---

## 6. Sensor-Daten — Downsampling-Stufen sichtbar im UI (R-14, R-15)

Der Nutzer sieht Sensordaten in Diagrammen und Tabellen (REQ-005). Das Downsampling
macht sich als reduzierte Datenpunktdichte bemerkbar: Rohdaten (< 90 Tage) zeigen
Minutenaufloesung, Stundendaten (90 Tage – 2 Jahre) zeigen Stundenmittelwerte,
Tagesdaten (2–5 Jahre) zeigen Tagesmittelwerte.

---

### TC-NFR011-020: Sensordaten-Diagramm zeigt feine Aufloesung fuer Zeitraum < 90 Tage (Rohdaten-Stufe)

**Requirement**: NFR-011 §2.2 R-14 Stufe 1 — 90 Tage Rohdaten volle Aufloesung
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Ein Sensor mit Messdaten der letzten 7 Tage existiert (REQ-005)
- Nutzer hat Zugriff auf die Sensordetailseite oder ein Dashboard-Diagramm

**Testschritte**:
1. Nutzer navigiert zur Sensor-Ansicht oder zum Pflanzendashboard
2. Nutzer waehlt einen Zeitbereich von "letzte 7 Tage" im Datumsfilter
3. Nutzer betrachtet das Sensordiagramm

**Erwartete Ergebnisse**:
- Das Diagramm zeigt viele eng liegende Datenpunkte (Minutenaufloesung oder Subminutenaufloesung)
- Detaillierte Kurvenverlaeufe sind sichtbar (kein stufenfoermiges Aggregat)
- Die Datenpunktdichte entspricht der urspruenglichen Sensormessrate

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-14, sensordaten, rohdaten, diagramm, req-005]

---

### TC-NFR011-021: Sensordaten-Diagramm zeigt Stundenmittelwerte fuer Zeitraum 90 Tage–2 Jahre (Stufe 2)

**Requirement**: NFR-011 §2.2 R-14 Stufe 2 — Stundenmittelwerte nach 90 Tagen
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Sensor existiert mit Daten aelter als 90 Tage (z.B. Messdaten aus dem Vorjahr)
- Zeitraum-Filter erlaubt Auswahl von "letztes Jahr" oder spezifischem Datumsbereich

**Testschritte**:
1. Nutzer navigiert zur Sensor-Ansicht
2. Nutzer stellt den Zeitbereich auf einen Zeitraum ein, der 90–730 Tage in der Vergangenheit beginnt (z.B. "vor 6 Monaten bis vor 4 Monaten")
3. Nutzer betrachtet das Diagramm

**Erwartete Ergebnisse**:
- Das Diagramm zeigt deutlich weniger Datenpunkte als fuer aktuelle Daten (Stundenmittelwerte statt Rohdaten)
- Der Zeitabstand zwischen Datenpunkten betraegt ca. 1 Stunde
- Die Y-Achse zeigt Durchschnittswerte (ggf. mit Min/Max-Baendern wenn UI diese darstellt)
- Kein Fehler beim Laden aelterer Daten

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-14, sensordaten, stundenmittel, downsampling, req-005]

---

### TC-NFR011-022: Sensordaten-Diagramm zeigt Tagesmittelwerte fuer Zeitraum 2–5 Jahre (Stufe 3)

**Requirement**: NFR-011 §2.2 R-14 Stufe 3 — Tagesmittelwerte nach 2 Jahren
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- System laeuft seit mindestens 2 Jahren und hat historische Sensordaten
- Testdaten-Fixture: Sensordaten mit `timestamp = JETZT - 3 Jahre` in `sensor_daily`-View

**Testschritte**:
1. Nutzer navigiert zur Sensor-Ansicht
2. Nutzer waehlt einen Zeitbereich von "vor 3 Jahren" im Datumsfilter
3. Nutzer betrachtet das Diagramm

**Erwartete Ergebnisse**:
- Das Diagramm zeigt einen Datenpunkt pro Tag (Tagesmittelwert)
- Stunden- oder Minutenaufloesung ist **nicht** verfuegbar fuer diesen Zeitraum
- Kein Fehler oder leeres Diagramm — die aggregierten Tagesdaten werden korrekt geladen
- Optional: Ein Hinweis im UI informiert dass historische Daten aggregiert dargestellt werden

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-14, sensordaten, tagesmittel, downsampling, req-005, zeitabhaengig]

---

### TC-NFR011-023: Sensordaten aelter als 5 Jahre sind nicht mehr abrufbar

**Requirement**: NFR-011 §2.2 R-14 — Tagesdaten nach 5 Jahren loeschen
**Priority**: Medium
**Category**: Fehlermeldung / Leerzustand
**Preconditions**:
- Testdaten-Fixture: Kein Sensordaten-Eintrag juenger als 5 Jahre + 1 Tag fuer einen bestimmten Sensor
- TimescaleDB Retention Policy wurde ausgefuehrt

**Testschritte**:
1. Nutzer navigiert zur Sensor-Ansicht und waehlt einen Zeitbereich von "vor 6 Jahren"
2. Nutzer betrachtet das Diagramm

**Erwartete Ergebnisse**:
- Das Diagramm zeigt einen Leerzustand: "Keine Daten fuer diesen Zeitraum verfuegbar" oder ein leeres Diagramm
- Kein Fehler (kein rotes Fehlerbanner) — leerer Datensatz wird korrekt als "keine Daten" angezeigt
- Keine historischen Sensordaten jenseits der 5-Jahres-Grenze werden angezeigt

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-14, sensordaten, datenleer, retention-ablauf, zeitabhaengig]

---

### TC-NFR011-024: Aktor-Logs zeigen aggregierte Werte fuer Zeitraum > 90 Tage (R-15)

**Requirement**: NFR-011 §2.2 R-15 — Aktor-Logs: 90 Tage roh, danach Override-Anzahl/Tag
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Testdaten-Fixture: Manuelle Aktor-Overrides existieren, sowohl aktuelle (< 90 Tage) als auch aeltere (> 90 Tage)

**Testschritte**:
1. Nutzer navigiert zur Aktor-Log-Ansicht (z.B. Umgebungssteuerung, REQ-018) fuer einen Standort
2. Nutzer betrachtet aktuelle Logs (letzte 30 Tage): Einzelne Override-Ereignisse mit Zeitstempel
3. Nutzer wechselt den Zeitfilter auf "vor 4 Monaten"

**Erwartete Ergebnisse**:
- Aktuelle Logs (< 90 Tage): Einzelne Override-Ereignisse mit individuellem Zeitstempel sind sichtbar
- Aeltere Logs (> 90 Tage): Nur noch aggregierte Tageszusammenfassungen ("X Overrides am TT.MM.JJJJ") oder Tagesmittelwerte
- Keine detaillierten Einzelereignisse fuer den alten Zeitraum mehr sichtbar

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-15, aktor-logs, aggregierung, req-018]

---

## 7. Konfigurierbarkeit — Mindestfristen-Schutzwall (AK-10)

Die Retention-Fristen sind per Umgebungsvariable konfigurierbar. Die gesetzlichen
Mindestfristen (R-16, R-17, R-18) duerfen nicht unterschritten werden. Diese Tests
pruefen sichtbare Auswirkungen der Konfiguration im Admin-Bereich.

---

### TC-NFR011-025: Admin sieht Retention-Konfiguration in Systemeinstellungen (spec-forward)

**Requirement**: NFR-011 §4 Konfigurierbarkeit — `RetentionSettings`; AK-10
**Priority**: Medium
**Category**: Detailansicht
**Status**: Ausstehend — Kein dedizierter Retention-Settings-Bereich im Frontend implementiert
**Preconditions**:
- Platform-Admin ist eingeloggt
- Ein Admin-Bereich fuer Systemkonfiguration ist implementiert

**Testschritte**:
1. Platform-Admin navigiert zu den System-Einstellungen (z.B. `/admin/settings/retention`)
2. Admin betrachtet die konfigurierten Retention-Fristen

**Erwartete Ergebnisse**:
- Die aktuell konfigurierten Fristen werden angezeigt (z.B. "Soft-Delete-Aufbewahrung: 90 Tage")
- Gesetzliche Mindestfristen sind als schreibgeschuetzt markiert oder zeigen einen Hinweis: "Gesetzliche Mindestfrist (CanG) — kann nicht unterschritten werden"
- Alle konfigurierbaren Fristen aus `RetentionSettings` sind sichtbar

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, AK-10, retention-config, admin, ausstehend]

---

### TC-NFR011-026: Gesetzliche Mindestfristen-Schutzwall — Unterschreitung wird verhindert

**Requirement**: NFR-011 §4 Letzter Absatz — Validierung `RetentionSettings`; AK-10
**Priority**: Critical
**Category**: Formvalidierung
**Status**: Ausstehend — Kein dedizierter Retention-Settings-Bereich implementiert
**Preconditions**:
- Platform-Admin ist eingeloggt
- Admin-Einstellungsseite fuer Retention-Fristen ist implementiert

**Testschritte**:
1. Platform-Admin navigiert zu den Retention-Einstellungen
2. Admin versucht, die "Erntedata-Aufbewahrungsfrist" auf 2 Jahre zu setzen (Minimum: 5 Jahre per CanG)
3. Admin klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Ein Validierungsfehler erscheint direkt beim Eingabefeld: "Mindestens 5 Jahre erforderlich (gesetzliche Pflicht gemaess CanG)"
- Der Wert wird **nicht** gespeichert
- Die aktuell konfigurierte Frist (5 Jahre oder mehr) bleibt unveraendert

**Postconditions**:
- Konfiguration unveraendert, gesetzliche Mindestfrist gewahrt

**Tags**: [nfr-011, AK-10, mindestfristen, validierung, canG, pflschg, ausstehend]

---

## 8. Monitoring und Retention-Lauf-Status (AK-04, AK-05, AK-06)

Der Celery-Master-Task laeuft taeglich um 02:00 UTC. Aus Browser-Perspektive sind
Monitoring-Informationen nur sichtbar, wenn ein Admin-Dashboard die letzten Celery-Task-
Resultate oder Prometheus-Metriken anzeigt.

---

### TC-NFR011-027: Platform-Admin sieht letzten Retention-Lauf-Status im Admin-Panel (spec-forward)

**Requirement**: NFR-011 §3.3 Logging; AK-05; AK-06
**Priority**: Medium
**Category**: Detailansicht
**Status**: Ausstehend — Kein Celery-Task-Status-Widget im Admin-Panel implementiert
**Preconditions**:
- Platform-Admin ist eingeloggt
- Celery-Task `enforce_retention_policy` wurde mindestens einmal ausgefuehrt
- Admin-Panel zeigt Celery-Task-Status (z.B. `/admin/tasks` oder System-Health-Widget)

**Testschritte**:
1. Platform-Admin navigiert zum Admin-Dashboard oder System-Health-Bereich
2. Admin sucht den Eintrag fuer `enforce_retention_policy`

**Erwartete Ergebnisse**:
- Der letzte Ausfuehrungs-Zeitstempel wird angezeigt (z.B. "Heute 02:00 UTC")
- Der Status des Letzten Laufs ist sichtbar: "Erfolgreich" oder "Fehler"
- Ergebniszaehler pro Kategorie werden angezeigt (z.B. "3 Accounts Hard-Deleted, 47 IPs anonymisiert")
- Falls Fehler aufgetreten sind: eine Warnmeldung oder rotes Badge ist sichtbar

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, AK-04, AK-05, monitoring, celery, admin-panel, ausstehend]

---

### TC-NFR011-028: Retention-Fehler erzeugen sichtbare Warnung im Admin-Panel (spec-forward)

**Requirement**: NFR-011 §3.3 Logging — `retention_run_errors_total`; AK-05
**Priority**: Medium
**Category**: Fehlermeldung
**Status**: Ausstehend — Kein Task-Monitoring-Widget implementiert
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testdaten-Fixture: Celery-Task hat Fehler in einer Sub-Task gelogged (z.B. Datei konnte nicht geloescht werden)

**Testschritte**:
1. Platform-Admin navigiert zum System-Health-Bereich
2. Admin betrachtet den Retention-Task-Status

**Erwartete Ergebnisse**:
- Fehlgeschlagene Sub-Tasks werden mit einer Warnung oder einem Fehler-Icon markiert
- Die Fehlerkategorie ist identifizierbar (z.B. "cleanup_expired_exports: 1 Fehler")
- Ein Hinweis empfiehlt manuelle Pruefung oder zeigt die Fehlermeldung im Tooltip

**Postconditions**:
- Keine automatische Aktion

**Tags**: [nfr-011, AK-05, retention-fehler, monitoring, admin-panel, ausstehend]

---

## 9. Consent Records und Processing Restrictions (R-04, R-13, spec-forward)

Diese Testfaelle haengen vollstaendig von der PrivacySettingsPage (REQ-025) ab.

---

### TC-NFR011-029: Widerrufener Consent bleibt 3 Jahre in der Consent-History sichtbar (spec-forward)

**Requirement**: NFR-011 §2.1 R-04 — Consent Records 3 Jahre nach Widerruf; REQ-025
**Priority**: High
**Category**: Detailansicht
**Status**: Ausstehend — PrivacySettingsPage nicht implementiert
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer hat einen optionalen Consent (z.B. "Externe Datenanreicherung") zu einem frueheren Zeitpunkt widerrufen
- Widerruf liegt weniger als 3 Jahre zurueck

**Testschritte**:
1. Nutzer navigiert zu `/settings/privacy` → Tab "Einwilligungen"
2. Nutzer betrachtet die Consent-History oder den Audit-Bereich

**Erwartete Ergebnisse**:
- Der widerrufene Consent ist in der History mit Zeitstempel des Widerrufs sichtbar
- Status: "Widerrufen am TT.MM.JJJJ HH:MM Uhr"
- Der Eintrag ist **nicht** endgueltig geloescht (3-Jahres-Frist noch nicht abgelaufen)

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-04, consent, widerruf, req-025, ausstehend]

---

### TC-NFR011-030: Verarbeitungseinschraenkung bleibt bis zur expliziten Aufhebung bestehen (spec-forward)

**Requirement**: NFR-011 §2.1 R-13 — Processing Restrictions unbegrenzt bis Aufhebung; REQ-025 Art. 18
**Priority**: High
**Category**: Zustandswechsel
**Status**: Ausstehend — PrivacySettingsPage nicht implementiert
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer hat eine Verarbeitungseinschraenkung (Art. 18) aktiv gesetzt

**Testschritte**:
1. Nutzer navigiert zu `/settings/privacy` → Tab "Verarbeitungseinschraenkung"
2. Nutzer betrachtet die aktive Einschraenkung

**Erwartete Ergebnisse**:
- Die aktive Einschraenkung ist sichtbar mit Datum der Erstellung
- Kein automatisches Ablaufdatum wird angezeigt (unbegrenzt gueltig)
- Ein Button "Einschraenkung aufheben" ist sichtbar
- Der eingeschraenkte Bereich (z.B. "Sensordaten", "Analyse") ist klar beschriftet

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-13, processing-restriction, art18, req-025, ausstehend]

---

## 10. Passwort-Reset- und E-Mail-Verifikations-Token-Ablauf (R-08, R-09)

Der Nutzer sieht den Ablauf dieser Token als "ungueltige Token"-Fehlermeldung auf der
Verifizierungs- oder Passwort-Reset-Bestaettigungs-Seite.

---

### TC-NFR011-031: Abgelaufener Passwort-Reset-Token zeigt Fehlermeldung

**Requirement**: NFR-011 §2.1 R-08 — Passwort-Reset-Token ablaufen nach 1 Stunde; REQ-023 §1
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist ausgeloggt
- Testdaten-Fixture: Passwort-Reset-Token mit `password_reset_expires = JETZT - 2 Stunden` existiert
  (oder Test-URL mit einem bekannt abgelaufenen Token)

**Testschritte**:
1. Nutzer oeffnet die Passwort-Reset-URL mit dem abgelaufenen Token in der Adressleiste: `/reset-password?token=ABGELAUFENER_TOKEN`
2. Nutzer betrachtet die Seite

**Erwartete Ergebnisse**:
- Die Seite zeigt eine Fehlermeldung: "Ungueltiger oder abgelaufener Token" (`pages.auth.invalidToken`)
- Das Passwort-Reset-Formular wird **nicht** angezeigt (oder ist deaktiviert)
- Ein Link oder Button "Neuen Reset anfordern" oder "Zurueck zur Anmeldung" ist sichtbar

**Postconditions**:
- Kein Passwort wurde zurueckgesetzt

**Tags**: [nfr-011, R-08, passwort-reset, token-ablauf, req-023, fehlermeldung]

---

### TC-NFR011-032: Abgelaufener E-Mail-Verifikations-Token zeigt Fehlermeldung

**Requirement**: NFR-011 §2.1 R-09 — E-Mail-Verifikations-Token ablaufen nach 24 Stunden; REQ-023 §1
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat sich registriert aber die Verifikations-E-Mail nicht innerhalb von 24 Stunden bestaetigt
- Testdaten-Fixture: Verifikations-Token mit `email_verification_expires = JETZT - 25 Stunden`

**Testschritte**:
1. Nutzer klickt auf den Verifikations-Link aus der (alten) E-Mail: `/verify-email?token=ABGELAUFENER_TOKEN`
2. Nutzer betrachtet die Seite

**Erwartete Ergebnisse**:
- Die Seite zeigt eine Fehlermeldung: "Ungueltiger oder abgelaufener Token"
- Eine Option zum erneuten Senden der Verifikations-E-Mail wird angeboten
- Das Konto bleibt im Status "Nicht verifiziert"

**Postconditions**:
- Kein Konto wurde verifiziert
- Konto im Status "unverified" wird nach 7 Tagen durch Retention-Task geloescht (R-02)

**Tags**: [nfr-011, R-09, email-verifikation, token-ablauf, req-023, fehlermeldung]

---

## 11. Gemeinsame Community-Daten nach Nutzer-Loeschung (R-19, R-20, R-21, R-22)

Diese Testfaelle betreffen REQ-024 v1.2-Funktionen (DutyRotation, BulletinPost,
SharedShoppingList). Diese Funktionen sind noch nicht implementiert.

---

### TC-NFR011-033: Pinnwand-Beitraege nach Nutzer-Loeschung zeigen anonymisierten Autor (spec-forward)

**Requirement**: NFR-011 §2.1 R-20 — BulletinPost Anonymisierung bei User-Loeschung; REQ-024 v1.2
**Priority**: Medium
**Category**: Detailansicht
**Status**: Ausstehend — BulletinPost-Feature nicht implementiert
**Preconditions**:
- Tenant-Mitglied betrachtet die Pinnwand des Tenants
- Ein anderes Mitglied, das Beitraege geschrieben hat, wurde geloescht

**Testschritte**:
1. Nutzer navigiert zur Tenant-Pinnwand
2. Nutzer betrachtet Beitraege des geloeschten Nutzers

**Erwartete Ergebnisse**:
- Beitraege sind weiterhin sichtbar (Inhalt bleibt erhalten — berechtigtes Interesse des Tenants)
- Der Autorname zeigt "Ehemaliges Mitglied" oder "Anonymisiert"
- Avatar-Bild ist ersetzt durch ein generisches Platzhalter-Icon
- Kein Fehler beim Laden der Seite

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-20, bulletin, anonymisierung, req-024, ausstehend]

---

### TC-NFR011-034: Aufgaben-Bewertungen bleiben nach Nutzer-Loeschung erhalten, Zuweisung anonymisiert (spec-forward)

**Requirement**: NFR-011 §2.1 R-22 — Tasks: assigned_to anonymisieren, Bewertungen erhalten; REQ-006
**Priority**: Medium
**Category**: Detailansicht
**Status**: Ausstehend — assigned_to-Anonymisierung bei Nutzerloeschung noch nicht implementiert
**Preconditions**:
- Nutzer betrachtet eine abgeschlossene Aufgabe, die einem inzwischen geloeschten Mitglied zugewiesen war
- Der geloeschte Nutzer hatte die Aufgabe mit Schwierigkeits-/Qualitaetsbewertung abgeschlossen

**Testschritte**:
1. Nutzer navigiert zur Aufgabendetailansicht
2. Nutzer betrachtet die Aufgaben-Metadaten

**Erwartete Ergebnisse**:
- Das Feld "Zugewiesen an" zeigt "Ehemaliges Mitglied" oder leer
- Die Schwierigkeits- und Qualitaetsbewertungen (Sterne/Punkte) sind weiterhin sichtbar
- Der Zeitstempel der Aufgabenerledigung ist erhalten
- Kein Fehler beim Laden der Aufgabe

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-22, aufgaben, anonymisierung, bewertungen, req-006, ausstehend]

---

## 12. Systemweite Integritaets-Checks

---

### TC-NFR011-035: Geloesche Nutzerdaten erscheinen nicht mehr in Tenant-Mitgliederliste

**Requirement**: NFR-011 §2.1 R-01; REQ-024 Tenant-Mitgliedschaft
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Tenant-Admin ist eingeloggt
- Ein Tenant-Mitglied hat sein Konto geloescht (Soft-Delete, Account im `deleted`-Status)

**Testschritte**:
1. Tenant-Admin navigiert zu den Tenant-Einstellungen → Tab "Mitglieder"
2. Admin betrachtet die Mitgliederliste

**Erwartete Ergebnisse**:
- Das geloeschte Mitglied erscheint **nicht** mehr in der Mitgliederliste
- Die Mitgliederzahl ist entsprechend reduziert
- Kein Fehler oder leerer Namenseintrag fuer das geloeschte Mitglied

**Postconditions**:
- Tenant-Mitgliedschaft des geloeschten Nutzers entfernt

**Tags**: [nfr-011, R-01, mitgliederliste, tenant, req-024]

---

### TC-NFR011-036: Sensor-Downsampling — Zeitreihendiagramm ohne Unterbrechung beim Stufen-Uebergang

**Requirement**: NFR-011 §2.2 R-14 — Nahtloser Uebergang Rohdaten → Stundenmittel
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Sensor mit Daten aus beiden Stufen (aktuelle Rohdaten + Stundenmittel aus dem Bereich 90–180 Tage)
- Zeitreihendiagramm mit Zoom-/Pan-Funktion verfuegbar

**Testschritte**:
1. Nutzer navigiert zur Sensor-Ansicht mit Zeitreihendiagramm
2. Nutzer waehlt einen Zeitbereich, der den 90-Tage-Grenzpunkt einschliesst (z.B. "letztes Quartal")
3. Nutzer betrachtet den Bereich um den Uebergangspunkt (vor ca. 90 Tagen)

**Erwartete Ergebnisse**:
- Das Diagramm zeigt keine sichtbare Luecke oder Unterbrechung am 90-Tage-Grenzpunkt
- Der Uebergang von Rohdaten zu Stundenmittelwerten ist als Dichteaenderung der Datenpunkte erkennbar, aber nicht als fehlende Daten
- Kein Fehler-Banner oder Ladeindikator am Grenzpunkt

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, R-14, sensordaten, downsampling, uebergang, diagramm]

---

### TC-NFR011-037: Celery-Retention-Task wird taeglich um 02:00 UTC ausgefuehrt — Admin-Bestaetigung

**Requirement**: NFR-011 §3.1 Master-Task — taeglich 02:00 UTC; AK-04
**Priority**: High
**Category**: Detailansicht
**Status**: Ausstehend — Kein Task-Monitoring im Admin-Panel
**Preconditions**:
- Platform-Admin ist eingeloggt
- Es ist nach 02:15 UTC (Task haette bereits laufen sollen)
- Admin-Panel mit Celery-Task-Monitoring ist implementiert

**Testschritte**:
1. Platform-Admin navigiert zu System-Health oder Task-Monitor (`/admin/tasks` o.ae.)
2. Admin sucht den Eintrag `enforce_retention_policy` in der Task-Liste

**Erwartete Ergebnisse**:
- Der letzte Ausfuehrungs-Zeitstempel zeigt eine Zeit im Zeitfenster 02:00–02:30 UTC des aktuellen Tages
- Status des letzten Laufs: "Erfolgreich"
- Dauer des letzten Laufs ist angegeben (z.B. "Dauer: 1.2 Sekunden")
- Naechste geplante Ausfuehrung ist sichtbar (morgen 02:00 UTC)

**Postconditions**:
- Keine Aktion ausgefuehrt

**Tags**: [nfr-011, AK-04, celery, task-monitoring, scheduling, ausstehend]

---

### TC-NFR011-038: Erasure-Audit-Log nach 1 Jahr geloescht — nicht mehr in Admin-Auswertung sichtbar (spec-forward, zeitabhaengig)

**Requirement**: NFR-011 §2.1 R-06 — Erasure-Audit-Logs 1 Jahr nach Abschluss loeschen
**Priority**: Medium
**Category**: Listenansicht
**Status**: Ausstehend — PrivacySettingsPage / Audit-Log-Ansicht nicht implementiert
**Preconditions**:
- Platform-Admin ist eingeloggt
- Testdaten-Fixture: Erasure-Request mit `completed_at = JETZT - 13 Monate` existiert
- Celery-Retention-Task wurde ausgefuehrt

**Testschritte**:
1. Platform-Admin navigiert zur Datenschutz-Audit-Ansicht (z.B. `/admin/privacy/erasure-requests`)
2. Admin sucht nach dem 13 Monate alten Erasure-Eintrag

**Erwartete Ergebnisse**:
- Der 13 Monate alte Erasure-Eintrag erscheint **nicht** mehr in der Liste
- Die Gesamtanzahl der Erasure-Eintraege ist entsprechend reduziert
- Neuere Eintraege (< 1 Jahr alt) sind weiterhin sichtbar

**Postconditions**:
- Alter Erasure-Audit-Eintrag durch Retention-Task entfernt

**Tags**: [nfr-011, R-06, erasure-audit, hard-delete, admin, req-025, ausstehend, zeitabhaengig]

---

## Coverage-Matrix

| NFR-011 Sektion | Retention-Regel | Testfall-IDs | Status |
|-----------------|-----------------|--------------|--------|
| §2.1 R-01 Soft-Deleted Accounts (90 Tage) | Hard-Delete nach 90 Tagen | TC-NFR011-001, TC-NFR011-002, TC-NFR011-003, TC-NFR011-004, TC-NFR011-035 | Teile sofort testbar; R-01 zeitabhaengig |
| §2.1 R-02 Unbestaetiigte Accounts (7 Tage) | Hard-Delete nach 7 Tagen | TC-NFR011-005, TC-NFR011-006 | R-02 zeitabhaengig |
| §2.1 R-03 IP-Adressen in Sessions (7 Tage) | Anonymisierung IPv4 letztes Oktett→0 | TC-NFR011-007, TC-NFR011-010 | zeitabhaengig; UI zeigt mgl. keine IP |
| §2.1 R-04 Consent Records (3 Jahre) | Hard-Delete nach 3 Jahren | TC-NFR011-029 | Ausstehend (PrivacySettings) |
| §2.1 R-05 Export-Dateien (72 Stunden) | Status "expired", Datei geloescht | TC-NFR011-014, TC-NFR011-015 | Ausstehend (PrivacySettings) |
| §2.1 R-06 Erasure-Audit-Logs (1 Jahr) | Hard-Delete nach 1 Jahr | TC-NFR011-038 | Ausstehend + zeitabhaengig |
| §2.1 R-07 E-Mail-Aenderungsanfragen (24h) | Hard-Delete — kein direkter UI-Effekt | (Gedeckt durch REQ-025 TC-025) | — |
| §2.1 R-08 Passwort-Reset-Token (1h) | Token-Felder nullen; Fehlermeldung im UI | TC-NFR011-031 | Sofort testbar |
| §2.1 R-09 E-Mail-Verifikations-Token (24h) | Token-Felder nullen; Fehlermeldung im UI | TC-NFR011-032 | Sofort testbar |
| §2.1 R-10 OAuth State (5 min, Redis TTL) | Automatisch — kein UI-Effekt | (Kein E2E-Test moeglich) | — |
| §2.1 R-11 Abgelaufene Refresh Tokens | Sofort Hard-Delete — Sitzungsliste | TC-NFR011-007, TC-NFR011-008, TC-NFR011-009 | Sofort testbar |
| §2.1 R-12 Einladungen abgelaufen (30 Tage) | Hard-Delete nach 30 Tagen | TC-NFR011-011, TC-NFR011-012, TC-NFR011-013 | Teile zeitabhaengig |
| §2.1 R-13 Processing Restrictions (unbegrenzt) | Bleibt bis expliziter Aufhebung | TC-NFR011-030 | Ausstehend |
| §2.2 R-14 Sensordaten Downsampling (3-stufig) | 90 Tage roh → 2 Jahre stuendlich → 5 Jahre taeglich | TC-NFR011-020, TC-NFR011-021, TC-NFR011-022, TC-NFR011-023, TC-NFR011-036 | Zeitabhaengig / Fixture |
| §2.2 R-15 Aktor-Logs (90 Tage roh, 1 Jahr aggreg.) | Aggregation sichtbar im Log-Viewer | TC-NFR011-024 | Zeitabhaengig |
| §2.3 R-16 Erntedaten (5 Jahre CanG) | Anonymisierung bei Loeschung | TC-NFR011-016, TC-NFR011-019 | Zeitabhaengig |
| §2.3 R-17 Behandlungsanwendungen (3 Jahre PflSchG) | Anonymisierung bei Loeschung | TC-NFR011-017 | Zeitabhaengig |
| §2.3 R-18 Inspektionsprotokolle (3 Jahre PflSchG) | Anonymisierung bei Loeschung | TC-NFR011-018 | Zeitabhaengig |
| §2.1 R-19 DutyRotation — Anonymisierung | User-Referenz auf NULL | (Kein UI vorhanden) | Ausstehend |
| §2.1 R-20 BulletinPost — Anonymisierung | Autor anonymisiert | TC-NFR011-033 | Ausstehend |
| §2.1 R-21 SharedShoppingList — Anonymisierung | User-Referenz anonym. | (Kein UI vorhanden) | Ausstehend |
| §2.1 R-22 Tasks assigned_to — Anonymisierung | Zuweisung anonym., Bewertungen bleiben | TC-NFR011-034 | Ausstehend |
| §4 Konfigurierbarkeit | Mindestfristen-Schutzwall | TC-NFR011-025, TC-NFR011-026 | Ausstehend |
| §3.1 Celery Master-Task (02:00 UTC) | Taeglich ausgefuehrt | TC-NFR011-037 | Ausstehend |
| §3.3 Logging & Monitoring | Admin-Lauf-Status sichtbar | TC-NFR011-027, TC-NFR011-028 | Ausstehend |
| §5 DSGVO-Loeschanfrage — Interaktion | Anonymisierung statt Loeschung | TC-NFR011-019 | Ausstehend |
| AK-10 Mindestfristen nicht unterschreitbar | Formvalidierung Admin | TC-NFR011-026 | Ausstehend |

### Legende

| Kategorie | Bedeutung |
|-----------|-----------|
| **Sofort testbar** | Kein Zeit-Seeding erforderlich, UI vorhanden |
| **Zeitabhaengig** | Erfordert Test-Clock-Manipulation oder Datenbank-Fixture mit backdatierten Timestamps |
| **Ausstehend** | UI-Komponente noch nicht implementiert (spec-forward) |
| **Kein E2E-Test** | Mechanismus ist rein server- oder infrastruktur-seitig (Redis TTL, TimescaleDB Policy) — nur via Integrations-Tests pruefen |
