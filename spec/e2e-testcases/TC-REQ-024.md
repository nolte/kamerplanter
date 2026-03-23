---
req_id: REQ-024
title: Mandantenverwaltung & Gemeinschaftsgärten
category: Plattform & Kollaboration
test_count: 82
coverage_areas:
  - Tenant-Erstellung (TenantCreatePage — /tenants/create)
  - Tenant-Einstellungen (TenantSettingsPage — /t/{slug}/settings)
  - Tenant-Switcher in der App-Bar (TenantSwitcher-Komponente)
  - Mitgliederverwaltung (Tab "Mitglieder" in TenantSettingsPage)
  - Einladungssystem — E-Mail-Einladung und Einladungslink
  - Einladung annehmen (InvitationAcceptPage — /invitations/accept/:token)
  - RBAC-Rollensystem (Admin, Gärtner, Beobachter) — UI-seitige Berechtigungssteuerung
  - Standort-Zuweisungen (AssignmentListPage — /t/{slug}/assignments)
  - Zuweisungsbasierte Write-Kontrolle (sichtbare Bearbeitungs-Buttons je Rolle)
  - Platform-Admin-Panel (Tenant-Übersicht, Notfallverwaltung)
  - Tenant-Notfallverwaltung (Suspendierung, Emergency-Admin)
  - Duty-Rotation / Gießdienst-Dienstplan
  - Pinnwand / Bulletin-Board (Posts, Kommentare, Reaktionen, Pinnen)
  - Gemeinsame Einkaufslisten
  - Stammdaten-Scoping (tenant_has_access — Sichtbarkeit globaler Stammdaten)
  - Letzter-Admin-Schutz (Degradierung/Entfernung verhindert)
  - Tenant-Löschung (Soft-Delete)
  - Persönlicher Tenant — automatische Erstellung bei Registrierung
generated: 2026-03-21
version: "1.4"
---

# TC-REQ-024: Mandantenverwaltung & Gemeinschaftsgärten

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-024 Mandantenverwaltung & Gemeinschaftsgärten v1.4**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte aus `src/frontend/src/i18n/locales/de/translation.json`.

REQ-024 definiert Kamerplanter als Multi-Tenant-Plattform: Jeder Nutzer gehört zu mindestens einem Tenant (persönlicher Garten), kann mehrere Tenants wechseln, Mitglieder einladen und Berechtigungen über ein 3-Rollen-Modell (Admin / Gärtner / Beobachter) verwalten. Gemeinschaftsgärten erweitern dies um Dienstpläne, Pinnwand und gemeinsame Einkaufslisten.

---

## 1. Persönlicher Tenant — Automatische Erstellung bei Registrierung

### TC-024-001: Persönlicher Tenant nach Registrierung automatisch vorhanden

**Requirement**: REQ-024 §1 — Kernkonzepte, AK-01
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Ein neuer Nutzer hat sich soeben über `/register` registriert (E-Mail: `neuer.gaertner@example.com`, Anzeigename: "Max Gärtner")
- Nutzer ist auf das Dashboard weitergeleitet worden

**Testschritte**:
1. Nutzer öffnet den Tenant-Switcher in der App-Bar (Dropdown mit Garten-Auswahl)

**Erwartete Ergebnisse**:
- Das Dropdown enthält genau einen Eintrag: "Max Gärtners Garten" (oder äquivalenter Name aus dem Anzeigenamen)
- Der Eintrag zeigt das Haus-Icon (persönlicher Tenant)
- Daneben ist ein "Admin"-Chip sichtbar
- Der Tenant ist als aktiv markiert (hervorgehoben)
- Die URL enthält `/t/max-gaertners-garten/...` (oder äquivalenter Slug)

**Nachbedingungen**:
- Nutzer ist Admin seines persönlichen Tenants

**Tags**: [req-024, personal-tenant, registration, ak-01, tenant-switcher]

---

### TC-024-002: Persönlicher Tenant ist für andere Nutzer unsichtbar

**Requirement**: REQ-024 §1 — Kernkonzepte, AK-18
**Priority**: Critical
**Category**: Berechtigungsprüfung
**Preconditions**:
- Nutzer A (Max) ist eingeloggt und hat einen persönlichen Tenant "Maxs Garten" mit 3 Zimmerpflanzen
- Nutzer B (Lisa) ist in einem separaten Browser eingeloggt
- Max und Lisa sind **nicht** beide im selben organisatorischen Tenant

**Testschritte**:
1. Lisa öffnet ihr Dashboard
2. Lisa öffnet den Tenant-Switcher

**Erwartete Ergebnisse**:
- Lisas Tenant-Liste zeigt nur ihre eigenen Tenants
- "Maxs Garten" erscheint **nicht** in Lisas Tenant-Switcher
- Lisa hat keine Möglichkeit, auf Maxs Tenant-Slug zu navigieren (Zugriff auf `/t/maxs-garten/...` würde abgelehnt)

**Nachbedingungen**:
- Keine Änderung am Systemzustand

**Tags**: [req-024, isolation, personal-tenant, ak-18, cross-tenant-security]

---

## 2. Organisations-Tenant erstellen (TenantCreatePage)

### TC-024-003: Organisations-Tenant erfolgreich erstellen — Happy Path

**Requirement**: REQ-024 §4.1 TenantCreatePage, §3.2 TenantService, AK-03
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Demo-User: `demo@kamerplanter.local`)
- Nutzer hat bisher weniger als 10 organisatorische Tenants

**Testschritte**:
1. Nutzer navigiert zu `/tenants/create`
2. Seite "Organisation erstellen" lädt mit Seitentitel und Einleitungstext
3. Nutzer gibt im Feld "Name" ein: `Grüne Oase e.V.`
4. Nutzer gibt im Feld "Beschreibung" ein: `Gemeinschaftsgarten in Berlin-Kreuzberg, 24 Parzellen`
5. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Während des Speicherns ist der Button deaktiviert oder zeigt eine Lade-Animation
- Nach erfolgreichem Speichern erscheint eine Erfolgs-Snackbar: "Organisation erfolgreich erstellt"
- Nutzer wird zum Dashboard weitergeleitet
- Im Tenant-Switcher erscheint jetzt ein neuer Eintrag "Grüne Oase e.V." mit Gruppen-Icon (organisatorischer Tenant) und "Admin"-Chip

**Nachbedingungen**:
- Neuer Tenant "Grüne Oase e.V." existiert im System
- Nutzer ist automatisch Admin dieses Tenants

**Tags**: [req-024, tenant-create, organization, happy-path, ak-03]

---

### TC-024-004: Tenant erstellen — Pflichtfeld "Name" leer gelassen

**Requirement**: REQ-024 §3.1 TenantEngine (validate_tenant_name: min 2 Zeichen)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer klickt "Erstellen" (oder versucht das Formular abzusenden)

**Erwartete Ergebnisse**:
- Das Formular wird nicht abgesendet
- Das Pflichtfeld "Name" zeigt eine Fehlermeldung (Browser-native Required-Validierung oder Inline-Fehler)
- Nutzer bleibt auf der Erstellungsseite

**Nachbedingungen**:
- Kein Tenant erstellt

**Tags**: [req-024, tenant-create, formvalidierung, required-field]

---

### TC-024-005: Tenant erstellen — Name zu kurz (1 Zeichen)

**Requirement**: REQ-024 §3.1 TenantEngine (validate_tenant_name: min 2 Zeichen)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer gibt im Feld "Name" ein: `A`
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Formular wird abgelehnt (Fehlermeldung erscheint oder Snackbar mit Fehlermeldung)
- Kein neuer Tenant erscheint im Tenant-Switcher

**Nachbedingungen**:
- Kein Tenant erstellt

**Tags**: [req-024, tenant-create, formvalidierung, grenzen]

---

### TC-024-006: Tenant erstellen — Maximallimit von 10 Organisations-Tenants überschritten

**Requirement**: REQ-024 §3.1 TenantEngine (can_create_organization: max 10), AK-02
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer ist bereits Admin von genau 10 organisatorischen Tenants

**Testschritte**:
1. Nutzer navigiert zu `/tenants/create`
2. Nutzer gibt im Feld "Name" ein: `Elfter Garten`
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint (Snackbar oder Inline-Fehler) mit einem Hinweis auf das Limit (max. 10 Organisations-Tenants)
- Kein neuer Tenant wird erstellt
- Der Tenant-Switcher zeigt weiterhin 10 + persönliche Tenants

**Nachbedingungen**:
- Kein elfter Tenant erstellt

**Tags**: [req-024, tenant-create, ak-02, limit, fehlermeldung]

---

### TC-024-007: Tenant erstellen — Slug-Generierung aus Umlauten korrekt

**Requirement**: REQ-024 §3.1 TenantEngine (generate_slug: ä→ae, ö→oe, ü→ue, ß→ss), AK-03
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer gibt im Feld "Name" ein: `Grüne Oase e.V.`
2. Nutzer klickt "Erstellen"
3. Nach erfolgreicher Erstellung navigiert Nutzer zum neuen Tenant

**Erwartete Ergebnisse**:
- Die URL des neuen Tenants enthält einen URL-sicheren Slug ohne Umlaute (z.B. `/t/gruene-oase-ev/...`)
- Keine Sonderzeichen oder Umlaute in der URL

**Nachbedingungen**:
- Tenant mit korrektem Slug existiert

**Tags**: [req-024, tenant-create, slug, ak-03, umlaute]

---

## 3. Tenant-Switcher (App-Bar)

### TC-024-008: Tenant-Switcher zeigt alle Tenants mit Rolle und Typ-Icon

**Requirement**: REQ-024 §4.2 TenantSwitcher, FK-01
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Demo-User ist eingeloggt
- Demo-User ist Mitglied in: "Demo-Garten" (personal, Admin) und "Gemeinschaftsgarten Sonnenschein" (organization, Admin)

**Testschritte**:
1. Nutzer klickt auf den Tenant-Switcher in der App-Bar (Dropdown-Trigger mit aktuellem Tenant-Namen)

**Erwartete Ergebnisse**:
- Dropdown öffnet sich
- Eintrag 1: "Demo-Garten" — Haus-Icon sichtbar (personal), "Admin"-Chip
- Eintrag 2: "Gemeinschaftsgarten Sonnenschein" — Gruppen-Icon sichtbar (organization), "Admin"-Chip
- Aktiver Tenant ist hervorgehoben (z.B. durch Häkchen oder fettgedruckten Text)
- Am Ende der Liste befindet sich ein Button "Neuen Garten erstellen" (o.ä.)

**Nachbedingungen**:
- Kein Status geändert (nur Lesevorgang)

**Tags**: [req-024, tenant-switcher, listenansicht, fk-01, rollen-chip]

---

### TC-024-009: Tenant wechseln — URL und Daten aktualisieren sich

**Requirement**: REQ-024 §1.1 Szenario 3, AK-04, FK-02
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Demo-User ist eingeloggt, aktiver Tenant ist "Demo-Garten" (`/t/demo-garten/dashboard`)
- Nutzer ist auch Mitglied bei "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Nutzer öffnet Tenant-Switcher in der App-Bar
2. Nutzer wählt "Gemeinschaftsgarten Sonnenschein" aus dem Dropdown

**Erwartete Ergebnisse**:
- Dropdown schließt sich
- URL ändert sich von `/t/demo-garten/dashboard` zu `/t/gemeinschaftsgarten-sonnenschein/dashboard`
- Seiteninhalt (Dashboard, Navigation, Datentabellen) lädt die Daten des neuen Tenants
- Tenant-Switcher zeigt jetzt "Gemeinschaftsgarten Sonnenschein" als aktiven Tenant
- Der Wechsel erfolgt ohne Abmeldung/Neuanmeldung

**Nachbedingungen**:
- Aktiver Tenant im Redux-State und localStorage = "Gemeinschaftsgarten Sonnenschein"

**Tags**: [req-024, tenant-switcher, ak-04, fk-02, navigation, url-routing]

---

### TC-024-010: Tenant-Switcher persistiert letzten aktiven Tenant nach Reload

**Requirement**: REQ-024 §4.2 TenantSwitcher (localStorage-Persistenz)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat Tenant "Gemeinschaftsgarten Sonnenschein" als aktiven Tenant gewählt
- Nutzer lädt die Seite neu (F5)

**Testschritte**:
1. Nutzer drückt F5 oder klickt den Browser-Reload-Button

**Erwartete Ergebnisse**:
- Nach dem Reload ist "Gemeinschaftsgarten Sonnenschein" weiterhin der aktive Tenant
- URL bleibt im Kontext von `/t/gemeinschaftsgarten-sonnenschein/...`
- Der Tenant-Switcher zeigt den korrekten aktiven Tenant

**Nachbedingungen**:
- Kein Datenverlust durch Reload

**Tags**: [req-024, tenant-switcher, localstorage, persistenz, reload]

---

### TC-024-011: Nutzer mit nur einem Tenant sieht keine leere Switcher-Liste

**Requirement**: REQ-024 §4.2 TenantSwitcher
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist neu registriert und hat nur den persönlichen Tenant

**Testschritte**:
1. Nutzer öffnet Tenant-Switcher

**Erwartete Ergebnisse**:
- Dropdown zeigt genau einen Tenant (den persönlichen)
- Button "Neuen Garten erstellen" ist sichtbar und klickbar
- Kein leerer Zustand / keine Fehlermeldung

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, tenant-switcher, single-tenant, neues-mitglied]

---

## 4. Tenant-Einstellungen (TenantSettingsPage)

### TC-024-012: Tenant-Einstellungsseite aufrufen als Admin

**Requirement**: REQ-024 §4.1, §1a.2 (Admin darf Tenant-Einstellungen ändern)
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist Admin des Tenants "Gemeinschaftsgarten Sonnenschein"
- Nutzer befindet sich in diesem Tenant-Kontext

**Testschritte**:
1. Nutzer navigiert zu `/t/gemeinschaftsgarten-sonnenschein/settings`

**Erwartete Ergebnisse**:
- Seite lädt mit Titel "Gemeinschaftsgarten Sonnenschein — Einstellungen" (o.ä.)
- Tab "Mitglieder" ist sichtbar und aktiv
- Tab "Einladungen" ist sichtbar (für Admins)
- Mitgliederliste lädt

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, settings-page, admin, navigation, fk-03]

---

### TC-024-013: Nicht-Admin sieht Einstellungsseite ohne Admin-Funktionen

**Requirement**: REQ-024 §1a.2, FK-06
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Nutzer "Max" hat Rolle "grower" im Tenant "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Max navigiert zu `/t/gemeinschaftsgarten-sonnenschein/settings`

**Erwartete Ergebnisse**:
- Seite lädt die Mitgliederliste (Max darf Mitglieder sehen: Name + Rolle)
- Tab "Einladungen" ist **nicht sichtbar** (nur für Admins)
- Kein Button "Mitglied einladen", "Einladungslink erstellen" oder "Mitglied entfernen" sichtbar
- Rollen-Dropdowns neben Mitgliedern sind **nicht anklickbar** (ausgegraut oder nicht vorhanden)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, settings-page, grower-rolle, fk-06, berechtigungspruefung]

---

### TC-024-014: Beobachter sieht Mitgliederliste (read-only)

**Requirement**: REQ-024 §1a.2 (Viewer kann Mitglieder auflisten: Name + Rolle sichtbar)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Nutzer "Anna" hat Rolle "viewer" im Tenant "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Anna navigiert zu `/t/gemeinschaftsgarten-sonnenschein/settings`

**Erwartete Ergebnisse**:
- Seite lädt und zeigt Mitgliederliste mit Namen und Rollen
- Keine Bearbeiten-, Einladen- oder Entfernen-Buttons sichtbar
- Tab "Einladungen" ist nicht sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, settings-page, viewer-rolle, readonly, berechtigungspruefung]

---

## 5. Mitgliederverwaltung

### TC-024-015: Mitgliederliste zeigt Mitglieder mit Rollen-Chip

**Requirement**: REQ-024 §4.2 MemberListPage, FK-03
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Tenant hat 3 Mitglieder: Lisa (Admin), Max (Gärtner), Anna (Beobachter)
- Nutzer befindet sich auf `/t/gemeinschaftsgarten-sonnenschein/settings`

**Testschritte**:
1. Nutzer öffnet Tab "Mitglieder"

**Erwartete Ergebnisse**:
- Tabelle zeigt 3 Zeilen mit den Spalten: Name (oder Avatar + Name), Rolle, Beigetreten-am
- Lisas Rolle zeigt Chip "Admin" (rote Farbe gemäß §4.2)
- Max' Rolle zeigt Chip "Gärtner" (grüne Farbe)
- Annas Rolle zeigt Chip "Beobachter" (graue Farbe)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, member-list, rollen-chip, fk-03, listenansicht]

---

### TC-024-016: Mitglied-Rolle ändern — Gärtner zu Admin hochstufen

**Requirement**: REQ-024 §1a.2, §3.2 MembershipEngine (can_assign_role), FK-03
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Lisa ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Max hat Rolle "grower"
- Lisa befindet sich auf der Mitglieder-Seite des Tenants

**Testschritte**:
1. Lisa klickt auf das Rollen-Dropdown neben Max
2. Lisa wählt "Admin" aus dem Dropdown
3. Änderung wird gespeichert (ggf. Bestätigungs-Dialog)

**Erwartete Ergebnisse**:
- Max' Rollen-Chip ändert sich zu "Admin" (rote Farbe)
- Eine Erfolgs-Snackbar erscheint (oder visuelle Bestätigung der Änderung)
- Max kann nun Admin-Funktionen ausführen (Tab "Einladungen" sichtbar bei nächster Anmeldung)

**Nachbedingungen**:
- Max' Membership hat Rolle "admin" im Tenant

**Tags**: [req-024, member-role-change, admin-upgrade, happy-path, fk-03]

---

### TC-024-017: Letzten Admin degradieren ist nicht möglich

**Requirement**: REQ-024 §1a.2 (Letzter Admin kann nicht entfernt/degradiert werden), AK-10
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Tenant "Solo-Garten" hat genau einen Admin: den eingeloggten Nutzer "Max"
- Max befindet sich auf der Mitglieder-Seite des Tenants

**Testschritte**:
1. Max klickt auf sein eigenes Rollen-Dropdown
2. Max versucht, seine Rolle auf "Gärtner" zu ändern

**Erwartete Ergebnisse**:
- Aktion wird abgelehnt: Eine Fehlermeldung erscheint (z.B. Snackbar "Der letzte Admin kann nicht degradiert werden" o.ä.)
- Max' Rolle bleibt "Admin"

**Nachbedingungen**:
- Keine Rollenänderung

**Tags**: [req-024, last-admin-guard, ak-10, fehlermeldung, kritisch]

---

### TC-024-018: Mitglied entfernen als Admin — Happy Path

**Requirement**: REQ-024 §1a.2, §3.2, i18n "pages.tenants.memberRemoved"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Lisa ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Anna hat Rolle "viewer" und soll entfernt werden
- Lisa befindet sich auf der Mitglieder-Seite

**Testschritte**:
1. Lisa klickt auf den Löschen-Button (Papierkorb-Icon) neben Anna
2. Ein Bestätigungs-Dialog erscheint ("Mitglied entfernen" o.ä.)
3. Lisa bestätigt die Aktion

**Erwartete Ergebnisse**:
- Bestätigungs-Dialog erscheint mit Annas Namen vor der Aktion
- Nach Bestätigung: Snackbar "Mitglied entfernt" erscheint
- Annas Zeile verschwindet aus der Mitgliederliste
- Mitgliederzahl im Tenant-Switcher reduziert sich um 1

**Nachbedingungen**:
- Anna ist kein Mitglied mehr im Tenant

**Tags**: [req-024, member-remove, admin, happy-path, confirm-dialog]

---

### TC-024-019: Letzten Admin entfernen ist nicht möglich

**Requirement**: REQ-024 §1a.2, AK-10
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Tenant "Solo-Garten" hat genau einen Admin: den eingeloggten Nutzer
- Keine anderen Admins vorhanden

**Testschritte**:
1. Nutzer (Admin) klickt auf Löschen-Button neben seinem eigenen Eintrag

**Erwartete Ergebnisse**:
- Aktion wird abgelehnt: Fehlermeldung erscheint ("Letzter Admin kann nicht entfernt werden" o.ä.)
- Der Löschen-Button ist ggf. deaktiviert oder nicht vorhanden für den letzten Admin

**Nachbedingungen**:
- Kein Mitglied entfernt

**Tags**: [req-024, last-admin-guard, ak-10, fehlermeldung, kritisch]

---

### TC-024-020: Tenant freiwillig verlassen (Leave)

**Requirement**: REQ-024 §1a.2 (eigene Membership verlassen: Admin wenn nicht letzter)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Max hat Rolle "grower" im Tenant "Gemeinschaftsgarten Sonnenschein"
- Mindestens ein anderes Admin-Mitglied ist vorhanden

**Testschritte**:
1. Max navigiert zu den Tenant-Einstellungen (oder einem "Tenant verlassen"-Button)
2. Max klickt "Tenant verlassen" (o.ä.)
3. Bestätigungs-Dialog erscheint
4. Max bestätigt

**Erwartete Ergebnisse**:
- Nach Bestätigung wird Max aus dem Tenant entfernt
- "Gemeinschaftsgarten Sonnenschein" erscheint nicht mehr in Max' Tenant-Switcher
- Max wird zum Dashboard seines persönlichen Tenants weitergeleitet

**Nachbedingungen**:
- Max ist kein Mitglied mehr im Tenant

**Tags**: [req-024, leave-tenant, happy-path, membership]

---

### TC-024-021: Letzter Admin kann Tenant nicht verlassen

**Requirement**: REQ-024 §1a.2 (nicht letzter Admin), AK-10
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer ist einziger Admin im Tenant "Solo-Org"
- Nutzer versucht, den Tenant zu verlassen

**Testschritte**:
1. Nutzer klickt auf "Tenant verlassen"
2. Bestätigungs-Dialog erscheint (wenn vorhanden)
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Aktion wird abgelehnt: Fehlermeldung erscheint ("Sie sind der letzte Admin. Ernennen Sie zuerst einen anderen Admin." o.ä.)
- Nutzer bleibt Mitglied des Tenants

**Nachbedingungen**:
- Keine Änderung der Membership

**Tags**: [req-024, leave-tenant, last-admin-guard, ak-10, fehlermeldung]

---

## 6. Einladungssystem

### TC-024-022: E-Mail-Einladung senden — Happy Path

**Requirement**: REQ-024 §1 Einladungssystem, §4.2 InviteDialog, AK-06, i18n "invitationSent"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer befindet sich auf `/t/gemeinschaftsgarten-sonnenschein/settings`, Tab "Einladungen"

**Testschritte**:
1. Nutzer gibt im Feld "E-Mail-Adresse" ein: `neues.mitglied@example.com`
2. Nutzer klickt "Einladung senden"

**Erwartete Ergebnisse**:
- Snackbar "Einladung gesendet" erscheint
- Das E-Mail-Feld wird geleert
- In der Einladungsliste erscheint eine neue Zeile mit: Typ "E-Mail", Status "pending", E-Mail-Adresse `neues.mitglied@example.com`

**Nachbedingungen**:
- Einladungs-E-Mail wurde (serverseitig) an die Adresse gesendet
- Einladung mit Status "pending" ist im System

**Tags**: [req-024, email-invitation, ak-06, happy-path, fk-04]

---

### TC-024-023: Einladungslink erstellen und kopieren — Happy Path

**Requirement**: REQ-024 §1 Einladungssystem (type: link), §4.2 InviteDialog, FK-04, i18n "linkCopied"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer befindet sich auf Tab "Einladungen"

**Testschritte**:
1. Nutzer klickt auf "Einladungslink" (oder den entsprechenden Button)

**Erwartete Ergebnisse**:
- Snackbar "Einladungslink in die Zwischenablage kopiert" erscheint
- In der Einladungsliste erscheint eine neue Zeile mit: Typ "Link", Status "pending"
- Link kann in einem Browser-Tab geöffnet werden (Funktionstest: `/invitations/accept/...`)

**Nachbedingungen**:
- Einladungslink mit Status "pending" ist im System

**Tags**: [req-024, link-invitation, fk-04, happy-path, ak-07]

---

### TC-024-024: Einladung widerrufen — Happy Path

**Requirement**: REQ-024 §1a.2 (Einladungslinks revoken), §3.2 (revoke_invitation)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Mindestens eine ausstehende Einladung (status: pending) ist in der Liste vorhanden
- Nutzer ist Admin im Tenant

**Testschritte**:
1. Nutzer klickt auf den Widerrufen-Button (oder "Einladung widerrufen") neben der Einladung
2. (Optional) Bestätigungs-Dialog erscheint
3. Nutzer bestätigt

**Erwartete Ergebnisse**:
- Einladung verschwindet aus der aktiven Einladungsliste (oder Status ändert sich zu "Widerrufen")
- Wenn der Einladungslink nach dem Widerrufen geöffnet wird, erscheint eine Fehlermeldung ("Einladung ungültig" o.ä.)

**Nachbedingungen**:
- Einladung hat Status "revoked"

**Tags**: [req-024, revoke-invitation, admin, happy-path]

---

### TC-024-025: Einladung annehmen — Happy Path (InvitationAcceptPage)

**Requirement**: REQ-024 §4.1 InvitationAcceptPage, §3.2 accept_invitation, AK-06, i18n "invitationAccepted"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Eine gültige E-Mail-Einladung mit Token `abc123xyz` für den Tenant "Gemeinschaftsgarten Sonnenschein" existiert (status: pending)
- Nutzer "Neues Mitglied" ist eingeloggt (oder meldet sich auf der Accept-Page an)

**Testschritte**:
1. Nutzer öffnet den Einladungslink im Browser: `/invitations/accept/abc123xyz`
2. Die Einladungs-Accept-Seite lädt mit dem Tenant-Namen "Gemeinschaftsgarten Sonnenschein"
3. Nutzer klickt "Einladung annehmen" (o.ä.)

**Erwartete Ergebnisse**:
- Erfolgs-Meldung erscheint: "Einladung angenommen! Sie sind jetzt Mitglied."
- Nutzer wird zum Dashboard des Tenants "Gemeinschaftsgarten Sonnenschein" weitergeleitet
- Im Tenant-Switcher erscheint "Gemeinschaftsgarten Sonnenschein" als neuer Tenant

**Nachbedingungen**:
- Nutzer ist Mitglied im Tenant mit der vordefinierten Rolle (z.B. "viewer")
- Einladung hat Status "accepted"

**Tags**: [req-024, accept-invitation, happy-path, ak-06, invitation-accept-page]

---

### TC-024-026: Abgelaufene Einladung annehmen — Fehlermeldung

**Requirement**: REQ-024 §3.1 InvitationEngine (validate_invitation: nicht abgelaufen), AK-08
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Eine Einladung mit `expires_at` in der Vergangenheit (z.B. vor 2 Tagen abgelaufen) existiert mit Token `expired-token-456`

**Testschritte**:
1. Nutzer öffnet `/invitations/accept/expired-token-456`

**Erwartete Ergebnisse**:
- Seite lädt und zeigt eine Fehlermeldung: "Einladung ungültig" oder "Diese Einladung ist abgelaufen" o.ä.
- Kein "Annehmen"-Button aktiv
- Keine Membership wird erstellt

**Nachbedingungen**:
- Kein Mitglied hinzugefügt

**Tags**: [req-024, expired-invitation, ak-08, fehlermeldung]

---

### TC-024-027: Einladungslink mit max_uses erschöpft — Fehlermeldung

**Requirement**: REQ-024 §1 (max_uses), AK-07
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Ein Einladungslink wurde mit `max_uses: 5` erstellt und bereits 5 Mal genutzt
- Ein neuer Nutzer versucht diesen Link zu nutzen

**Testschritte**:
1. Nutzer öffnet den Einladungslink im Browser (z.B. `/invitations/accept/used-token-789`)

**Erwartete Ergebnisse**:
- Seite zeigt Fehlermeldung: "Einladung ungültig" oder "Maximale Nutzungsanzahl erreicht" o.ä.
- Kein "Annehmen"-Button aktiv

**Nachbedingungen**:
- Kein sechstes Mitglied hinzugefügt

**Tags**: [req-024, max-uses-invitation, ak-07, fehlermeldung]

---

### TC-024-028: Nutzer ist bereits Mitglied — Einladung erneut annehmen

**Requirement**: REQ-024 §3.1 InvitationEngine (can_accept: User nicht bereits Mitglied)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Max ist bereits Mitglied im Tenant "Gemeinschaftsgarten Sonnenschein"
- Max versucht einen Einladungslink für denselben Tenant zu öffnen

**Testschritte**:
1. Max öffnet den Einladungslink für "Gemeinschaftsgarten Sonnenschein"

**Erwartete Ergebnisse**:
- Seite zeigt Hinweis: "Sie sind bereits Mitglied in diesem Garten" o.ä.
- Keine doppelte Membership wird erstellt

**Nachbedingungen**:
- Max hat weiterhin nur eine Membership im Tenant

**Tags**: [req-024, duplicate-membership, fehlermeldung, einladung]

---

### TC-024-029: Gärtner kann keine Einladungen erstellen

**Requirement**: REQ-024 §1a.2 (Mitglied einladen: nur Admin)
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max hat Rolle "grower" im Tenant

**Testschritte**:
1. Max navigiert zu `/t/gemeinschaftsgarten-sonnenschein/settings`

**Erwartete Ergebnisse**:
- Tab "Einladungen" ist **nicht sichtbar** für Max
- Es gibt keinen "Einladungslink erstellen"- oder "Einladung senden"-Button

**Nachbedingungen**:
- Keine Einladung erstellt

**Tags**: [req-024, invitation-create, grower-keine-berechtigung, fk-06]

---

## 7. Standort-Zuweisungen (AssignmentListPage)

### TC-024-030: Standort-Zuweisungsseite aufrufen als Admin

**Requirement**: REQ-024 §4.1 AssignmentListPage, §4.2 AssignmentListPage (Matrix-Darstellung)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Tenant hat folgende Locations: "Parzelle A1", "Parzelle A2", "Kompostplatz"
- "Parzelle A1" ist Max zugewiesen, "Kompostplatz" hat keine Zuweisung (Gemeinschaft)

**Testschritte**:
1. Nutzer navigiert zu `/t/gemeinschaftsgarten-sonnenschein/assignments`

**Erwartete Ergebnisse**:
- Seite lädt mit Zuweisungs-Matrix
- Zeilen repräsentieren Locations: "Parzelle A1", "Parzelle A2", "Kompostplatz"
- "Parzelle A1" zeigt Zuweisung zu Max (grüne Farbcodierung gemäß §4.2)
- "Kompostplatz" zeigt keine Zuweisung (blaue Farbcodierung für Gemeinschaft)
- "Parzelle A2" zeigt keine Zuweisung (graue Farbcodierung)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, assignment-list, fk-05, matrix-darstellung, listenansicht]

---

### TC-024-031: Standort einem Mitglied zuweisen als Admin — Happy Path

**Requirement**: REQ-024 §1a.2, §3.2 assign_location
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin im Tenant
- "Parzelle A2" hat keine Zuweisung
- Anna ist Mitglied mit Rolle "grower"

**Testschritte**:
1. Nutzer navigiert zu `/t/gemeinschaftsgarten-sonnenschein/assignments`
2. Nutzer klickt auf die Zelle "Parzelle A2" × Anna (Matrix-Klick oder Drag-and-Drop)
3. Nutzer wählt Rolle "Verantwortlich" aus dem Dialog/Dropdown
4. Optional: Nutzer gibt `valid_from: 2026-04-01`, `valid_until: 2026-10-31` ein
5. Nutzer bestätigt die Zuweisung

**Erwartete Ergebnisse**:
- "Parzelle A2" × Anna-Zelle ändert sich auf grüne Farbe (zugewiesen)
- Erfolgs-Snackbar erscheint
- Bei nächstem Laden der Seite ist die Zuweisung persistent

**Nachbedingungen**:
- LocationAssignment für Anna + Parzelle A2 existiert im System

**Tags**: [req-024, assign-location, admin, happy-path, fk-05]

---

### TC-024-032: Gärtner kann Standort-Zuweisungen nicht verwalten

**Requirement**: REQ-024 §1a.2 (LocationAssignment erstellen/ändern/entfernen: nur Admin)
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max hat Rolle "grower" im Tenant

**Testschritte**:
1. Max navigiert zu `/t/gemeinschaftsgarten-sonnenschein/assignments`

**Erwartete Ergebnisse**:
- Max sieht die Zuweisung (read-only-Ansicht) **oder** die Seite ist für Gärtner nicht zugänglich (Redirect oder 403-Hinweis)
- Keine Klick-to-Assign-Buttons oder Drag-and-Drop-Funktionalität für Max
- Kein "Zuweisung erstellen"-Button sichtbar

**Nachbedingungen**:
- Keine Änderung der Zuweisungen

**Tags**: [req-024, assignment-manage, grower-keine-berechtigung, fk-06]

---

### TC-024-033: Zuweisungsbasierte Write-Kontrolle — Gärtner sieht Bearbeiten-Button nur für eigene/gemeinschaftliche Ressourcen

**Requirement**: REQ-024 §1a.5 Zuweisungsbasierte Write-Kontrolle, §1.1 Szenario 2, AK-11, AK-41, AK-42
**Priority**: Critical
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max hat Rolle "grower", "Parzelle A1" ist ihm zugewiesen, "Parzelle A2" ist Lisa zugewiesen, "Kompostplatz" hat keine Zuweisung
- Max navigiert zur Pflanzen-Listenansicht oder Locations-Seite des Tenants

**Testschritte**:
1. Max navigiert zu `/t/gemeinschaftsgarten-sonnenschein/sites`
2. Max öffnet die Location "Parzelle A1" (seine Parzelle)
3. Max öffnet die Location "Kompostplatz" (Gemeinschaft)
4. Max öffnet die Location "Parzelle A2" (Lisas Parzelle)

**Erwartete Ergebnisse**:
- Für "Parzelle A1": Bearbeiten-Button ist sichtbar und aktiv (zugewiesene Ressource)
- Für "Kompostplatz": Bearbeiten-Button ist sichtbar und aktiv (Gemeinschaftsressource, keine Zuweisung)
- Für "Parzelle A2": Bearbeiten-Button ist **nicht sichtbar** oder deaktiviert (Lisas Parzelle)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, write-control, grower, ak-11, ak-41, ak-42, kritisch]

---

### TC-024-034: Abgelaufene Standort-Zuweisung wird nicht berücksichtigt

**Requirement**: REQ-024 §1a.5 (LocationAssignment valid_from/valid_until), AK-15, AK-43
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- "Parzelle A3" ist Max zugewiesen mit `valid_until: 2025-12-31` (in der Vergangenheit)
- Heute ist 2026-03-21

**Testschritte**:
1. Max navigiert zur Location "Parzelle A3"

**Erwartete Ergebnisse**:
- Der Bearbeiten-Button für "Parzelle A3" ist **nicht sichtbar** für Max (Zuweisung ist abgelaufen)
- Max kann "Parzelle A3" nur lesen (wenn kein anderer hat es zugewiesen → Gemeinschaftsressource ODER wenn ein anderer es hat → keine Berechtigung)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, expired-assignment, ak-15, ak-43, zeitfenster]

---

### TC-024-035: Beobachter kann keine Ressourcen erstellen oder bearbeiten

**Requirement**: REQ-024 §1a.1 (Viewer: R all, keine Create/Update/Delete), AK-12, FK-07
**Priority**: Critical
**Category**: Berechtigungsprüfung
**Preconditions**:
- Anna hat Rolle "viewer" im Tenant "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Anna navigiert zu `/t/gemeinschaftsgarten-sonnenschein/sites`
2. Anna navigiert zu einer beliebigen Location

**Erwartete Ergebnisse**:
- Alle Bearbeiten-, Erstellen- und Löschen-Buttons sind **nicht sichtbar** für Anna
- Anna kann Daten lesen (Pflanzen, Aufgaben, Harvests sehen)
- Keine Bearbeiten-Formulare oder Erstellungs-Dialoge öffnen sich

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, viewer-rolle, ak-12, fk-07, read-only, kritisch]

---

## 8. RBAC — Rollen-spezifische UI-Einschränkungen

### TC-024-036: Admin kann Tasks zuweisen — Gärtner kann es nicht

**Requirement**: REQ-024 §1a.1 (Tasks: Zuweisen (assigned_to): nur Admin), AK-33
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Lisa ist Admin, Max ist Gärtner im selben Tenant
- Eine Task "Tomaten gießen" existiert im Tenant

**Testschritte**:
1. Lisa öffnet die Task "Tomaten gießen"
2. Lisa klickt auf "Zuweisen an" und wählt Max aus (Mitglieder-Dropdown sichtbar)
3. Bestätigt die Zuweisung
4. Max öffnet dieselbe Task (als Gärtner)

**Erwartete Ergebnisse**:
- Für Lisa: "Zuweisen an"-Dropdown ist sichtbar, Lisa kann Max als Assignee festlegen
- Task zeigt "Zugewiesen an: Max"
- Für Max: "Zuweisen an"-Feld ist nicht bearbeitbar (kein Dropdown, nur Anzeige des Assignees)

**Nachbedingungen**:
- Task ist Max zugewiesen

**Tags**: [req-024, task-assign, ak-33, admin-only, grower-restricted]

---

### TC-024-037: Viewer kann keine neue Pflanze erstellen

**Requirement**: REQ-024 §1a.1 (Plant Instances: Viewer R all, kein Create), AK-12
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Anna hat Rolle "viewer" im Tenant

**Testschritte**:
1. Anna navigiert zu `/t/gemeinschaftsgarten-sonnenschein/plant-instances`

**Erwartete Ergebnisse**:
- "Pflanze erstellen"-Button ist **nicht sichtbar** für Anna
- Anna sieht die Pflanzenliste (read-only)

**Nachbedingungen**:
- Keine neue Pflanze erstellt

**Tags**: [req-024, viewer-rolle, ak-12, plant-create, fk-07]

---

### TC-024-038: Gärtner kann Pflanzen-Phasen-Transition auslösen für eigene/gemeinschaftliche Pflanzen

**Requirement**: REQ-024 §1a.1 (Plant Instances: Phasen-Transition: admin, grower (own+community)), AK-30
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Max ist Gärtner, "Parzelle A1" ist ihm zugewiesen
- Pflanze "Tomate-01" befindet sich in Parzelle A1 (eigene Ressource)
- Pflanze "Kompost-Kürbis" befindet sich im Kompostplatz (Gemeinschaft)

**Testschritte**:
1. Max öffnet "Tomate-01" Detailansicht
2. Max klickt "Nächste Phase"
3. Max öffnet "Kompost-Kürbis" Detailansicht
4. Max klickt "Nächste Phase"

**Erwartete Ergebnisse**:
- Für "Tomate-01": Phasen-Transition-Button ist aktiv, Phase wechselt nach Klick
- Für "Kompost-Kürbis": Phasen-Transition-Button ist aktiv, Phase wechselt nach Klick

**Nachbedingungen**:
- Beide Pflanzen haben nächste Phase

**Tags**: [req-024, phase-transition, grower, ak-30, own-community-resource]

---

### TC-024-039: Gärtner kann Phasen-Transition NICHT für Pflanzen anderer Gärtner auslösen

**Requirement**: REQ-024 §1a.1, §1a.5 Zuweisungsbasierte Write-Kontrolle, AK-42
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max ist Gärtner, "Parzelle A2" ist Lisa zugewiesen
- Pflanze "Tomate-Lisa" befindet sich in Parzelle A2 (Lisas Parzelle)

**Testschritte**:
1. Max öffnet "Tomate-Lisa" Detailansicht

**Erwartete Ergebnisse**:
- Phasen-Transition-Button ("Nächste Phase") ist **nicht sichtbar** oder deaktiviert für Max
- Max sieht die Pflanzendaten (read-only)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, phase-transition, grower-restricted, ak-42, write-control]

---

## 9. Tenant-Löschung

### TC-024-040: Tenant löschen als Admin (Soft-Delete) — Happy Path

**Requirement**: REQ-024 §1a.2, §3.2 delete_tenant (Soft-Delete), AK-16
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin eines Tenants "Test-Garten" mit 2 weiteren Mitgliedern

**Testschritte**:
1. Nutzer navigiert zu den Tenant-Einstellungen
2. Nutzer klickt auf "Tenant löschen" (in der Gefahrenzone o.ä.)
3. Bestätigungs-Dialog erscheint mit Hinweis auf aktive Mitglieder
4. Nutzer bestätigt die Löschung

**Erwartete Ergebnisse**:
- Bestätigungs-Dialog erscheint und warnt vor aktiven Mitgliedern
- Nach Bestätigung: Tenant "Test-Garten" erscheint nicht mehr im Tenant-Switcher
- Nutzer wird zum Dashboard des persönlichen Tenants weitergeleitet

**Nachbedingungen**:
- Tenant hat Status "deleted" (Soft-Delete)
- Alle Memberships sind deaktiviert

**Tags**: [req-024, tenant-delete, soft-delete, ak-16, happy-path]

---

### TC-024-041: Gärtner kann Tenant nicht löschen

**Requirement**: REQ-024 §1a.2 (Tenant löschen: nur Admin)
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max hat Rolle "grower" im Tenant

**Testschritte**:
1. Max navigiert zu den Tenant-Einstellungen (falls zugänglich)

**Erwartete Ergebnisse**:
- "Tenant löschen"-Button ist **nicht sichtbar** für Max
- Tenant-Einstellungsseite zeigt keine Gefahrenzone/Löschfunktion für Gärtner

**Nachbedingungen**:
- Kein Tenant gelöscht

**Tags**: [req-024, tenant-delete, grower-keine-berechtigung, fk-06]

---

## 10. Platform-Admin-Panel

### TC-024-042: Platform-Admin sieht alle Tenants in Übersicht

**Requirement**: REQ-024 §1a.4 (Platform-Admin: Alle Tenants auflisten), FK-01 analog
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Demo-User ist eingeloggt und hat "admin"-Membership im Platform-Tenant (`is_platform: true`)
- System hat mindestens 3 Tenants: "Demo-Garten", "Gemeinschaftsgarten Sonnenschein", "Platform"

**Testschritte**:
1. Demo-User navigiert zum Admin-Panel (z.B. `/admin/tenants` oder `/t/platform/...`)

**Erwartete Ergebnisse**:
- Liste zeigt alle Tenants des Systems (nicht nur eigene)
- Jeder Eintrag zeigt: Name, Slug, Typ, Status, Mitgliederzahl
- Aktionsoptionen (Bearbeiten, Suspendieren) sind sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, platform-admin, tenant-overview, ak-45, listenansicht]

---

### TC-024-043: Platform-Viewer kann Tenant-Übersicht nur lesen

**Requirement**: REQ-024 §1a.4 (Platform-Viewer: Tenant-Übersicht read-only), AK-38, AK-39
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Nutzer hat "viewer"-Membership im Platform-Tenant

**Testschritte**:
1. Nutzer navigiert zum Admin-Panel (Tenant-Übersicht)

**Erwartete Ergebnisse**:
- Tenant-Liste ist sichtbar (read-only)
- Keine "Suspendieren"-, "Emergency-Admin ernennen"- oder "Löschen"-Buttons sichtbar
- Keine Bearbeiten-Funktionen für globale Stammdaten sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, platform-viewer, ak-38, ak-39, readonly]

---

### TC-024-044: Tenant suspendieren als Platform-Admin

**Requirement**: REQ-024 §1a.4, AK-47, AK-48
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Demo-User hat Platform-Admin-Rolle
- Tenant "Problem-Garten" ist aktiv

**Testschritte**:
1. Platform-Admin navigiert zur Tenant-Übersicht
2. Klickt auf "Suspendieren" neben "Problem-Garten"
3. Gibt einen Suspendierungsgrund ein: "Verstoß gegen Nutzungsbedingungen"
4. Bestätigt die Aktion

**Erwartete Ergebnisse**:
- Bestätigungs-Dialog mit Grund-Textfeld erscheint
- Nach Bestätigung: "Problem-Garten" zeigt Status "Suspendiert" in der Admin-Übersicht
- Wenn ein anderer Nutzer im Tenant-Switcher "Problem-Garten" sieht: Es erscheint ausgegraut mit Hinweis "Suspendiert" (AK-47)

**Nachbedingungen**:
- Tenant hat `status: suspended` und `suspended_reason` gesetzt

**Tags**: [req-024, suspend-tenant, platform-admin, ak-47, ak-48, zustandswechsel]

---

### TC-024-045: Suspendierter Tenant — Zugriff auf Ressourcen blockiert

**Requirement**: REQ-024 AK-47, AK-48
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Tenant "Problem-Garten" ist suspendiert
- Nutzer "Max" ist Mitglied in "Problem-Garten"

**Testschritte**:
1. Max öffnet den Tenant-Switcher
2. Max versucht "Problem-Garten" zu aktivieren

**Erwartete Ergebnisse**:
- "Problem-Garten" erscheint im Tenant-Switcher ausgegraut mit Hinweis "Suspendiert"
- Wenn Max versucht auf den suspendierten Tenant zuzugreifen: Fehlermeldung "Dieser Garten ist suspendiert" oder "Kein Zugriff" erscheint
- Keine Ressourcen des Tenants sind bearbeitbar

**Nachbedingungen**:
- Max verbleibt in seinem aktiven Tenant

**Tags**: [req-024, suspended-tenant, ak-47, ak-48, fehlermeldung, kritisch]

---

### TC-024-046: Tenant reaktivieren als Platform-Admin

**Requirement**: REQ-024 §1a.4 (Platform-Admin: Tenant reaktivieren)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- "Problem-Garten" ist suspendiert
- Demo-User hat Platform-Admin-Rolle

**Testschritte**:
1. Platform-Admin navigiert zur Tenant-Übersicht
2. Klickt auf "Reaktivieren" neben "Problem-Garten"
3. Bestätigt die Aktion

**Erwartete Ergebnisse**:
- "Problem-Garten" zeigt Status "Aktiv" in der Admin-Übersicht
- Im Tenant-Switcher des Mitglieds Max erscheint "Problem-Garten" wieder normal (nicht ausgegraut)

**Nachbedingungen**:
- Tenant hat `status: active`

**Tags**: [req-024, reactivate-tenant, platform-admin, zustandswechsel]

---

### TC-024-047: Platform-Admin kann Mitgliederliste eines fremden Tenants einsehen

**Requirement**: REQ-024 AK-45, AK-46 (VIEW_TENANT_MEMBERS_CROSS)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Demo-User hat Platform-Admin-Rolle
- Tenant "Fremder-Garten" existiert, zu dem Demo-User **nicht** als reguläres Mitglied gehört

**Testschritte**:
1. Demo-User navigiert zur Admin-Tenant-Detailansicht von "Fremder-Garten"
2. Demo-User klickt auf "Mitglieder anzeigen"

**Erwartete Ergebnisse**:
- Mitgliederliste von "Fremder-Garten" ist sichtbar (mit Namen und Rollen)
- Demo-User kann die Liste lesen, auch ohne Membership in diesem Tenant

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, platform-admin, cross-tenant-members, ak-45, ak-46]

---

## 11. Stammdaten-Scoping (tenant_has_access)

### TC-024-048: Neuer Tenant sieht alle globalen Stammdaten (Auto-Assign)

**Requirement**: REQ-024 §2 Stammdaten-Scoping, AK-21, AK-22
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Globale Species "Solanum lycopersicum" (Tomate) existiert im System
- Neuer Tenant "Neugarten" wurde soeben mit `auto_assign_master_data=true` (Default) erstellt

**Testschritte**:
1. Admin des neuen Tenants navigiert zu `/api/v1/species` (oder entsprechender Frontend-Seite)
2. Nutzer sucht nach "Tomate" oder "Solanum lycopersicum"

**Erwartete Ergebnisse**:
- "Solanum lycopersicum" erscheint in der Artenliste des Tenants
- Globale Schädlinge, Krankheiten, Behandlungen, Düngemittel und Nährstoffpläne sind ebenfalls sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, auto-assign, ak-21, ak-22, stammdaten-scoping]

---

### TC-024-049: Tenant-eigenen Schädling anlegen (origin: tenant)

**Requirement**: REQ-024 §2 Stammdaten-Scoping, AK-25
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer navigiert zur Schädlings-Seite

**Testschritte**:
1. Nutzer klickt "Schädling erstellen"
2. Nutzer gibt Name: "Lokaler Schneckenschaden" ein
3. Nutzer speichert

**Erwartete Ergebnisse**:
- Neuer Schädling "Lokaler Schneckenschaden" erscheint in der Liste des Tenants
- Der Schädling ist erkennbar als tenant-eigener Eintrag (z.B. durch Label "Eigener Eintrag" oder abweichende Darstellung)

**Nachbedingungen**:
- Schädling mit `origin: 'tenant'` und dem Tenant-Key gesetzt

**Tags**: [req-024, tenant-own-pest, ak-25, stammdaten-scoping]

---

### TC-024-050: Tenant-eigener Schädling für anderen Tenant unsichtbar

**Requirement**: REQ-024 §2 Stammdaten-Scoping, AK-26
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- "Lokaler Schneckenschaden" (origin: tenant) existiert im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer ist Admin eines anderen Tenants "Anderer-Garten"

**Testschritte**:
1. Nutzer navigiert im Kontext von "Anderer-Garten" zur Schädlings-Seite

**Erwartete Ergebnisse**:
- "Lokaler Schneckenschaden" erscheint **nicht** in der Liste von "Anderer-Garten"
- Nur globale Schädlinge und eigene Schädlinge von "Anderer-Garten" sind sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, tenant-data-isolation, ak-26, stammdaten-scoping, cross-tenant-security]

---

### TC-024-051: Platform-Admin kann Tenant-Stammdaten zu global promoten

**Requirement**: REQ-024 §1a.4 (Species promoten: tenant → global), AK-27
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Demo-User hat Platform-Admin-Rolle
- "Lokaler Schneckenschaden" (origin: tenant) existiert im Tenant "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Platform-Admin öffnet die Admin-Ansicht für den Schädling "Lokaler Schneckenschaden"
2. Platform-Admin klickt "Zu global promoten" (o.ä.)
3. Bestätigungs-Dialog erscheint
4. Platform-Admin bestätigt

**Erwartete Ergebnisse**:
- Schädling zeigt nach der Promotion keinen Tenant-spezifischen Hinweis mehr
- Andere Tenants (mit `auto_assign_master_data=true`) können den Schädling jetzt in ihrer Liste sehen

**Nachbedingungen**:
- Schädling hat `origin: 'system'`, `tenant_key: null`

**Tags**: [req-024, promote-to-global, platform-admin, ak-27]

---

### TC-024-052: Platform-Viewer kann keine Stammdaten ändern

**Requirement**: REQ-024 §1a.4 (Platform-Viewer: Globale Species nur lesen), AK-40
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Nutzer hat "viewer"-Membership im Platform-Tenant

**Testschritte**:
1. Nutzer navigiert zur globalen Species-Liste im Admin-Panel
2. Nutzer versucht eine Species zu bearbeiten (klickt auf Bearbeiten-Button, falls sichtbar)

**Erwartete Ergebnisse**:
- Bearbeiten- und Erstellen-Buttons sind **nicht sichtbar** oder deaktiviert für Platform-Viewer
- "Zu global promoten"-Aktionen sind nicht verfügbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, platform-viewer, ak-40, readonly, stammdaten]

---

## 12. Duty-Rotation / Gießdienst-Dienstplan

### TC-024-053: Duty-Rotation erstellen als Admin — Happy Path

**Requirement**: REQ-024 §1a.3 (Duty-Rotation erstellen: nur Admin), §1.1 Szenario 7, §2 DutyRotation-Modell
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Mindestens 4 Mitglieder sind im Tenant: Max, Lisa, Tom, Anna
- Nutzer navigiert zur Dienstplan-Seite (z.B. `/t/gemeinschaftsgarten-sonnenschein/duty-rotations`)

**Testschritte**:
1. Nutzer klickt "Dienstplan erstellen"
2. Dialog/Formular öffnet sich
3. Nutzer gibt Name ein: `Gießdienst Gemeinschaftsbeete`
4. Nutzer wählt Diensttyp: "Gießdienst" (watering)
5. Nutzer wählt Mitglieder: Max, Lisa, Tom, Anna
6. Nutzer wählt Intervall: "Wöchentlich"
7. Nutzer wählt Starttag: "Montag"
8. Nutzer klickt "Speichern"

**Erwartete Ergebnisse**:
- Erfolgs-Snackbar erscheint
- Neuer Dienstplan "Gießdienst Gemeinschaftsbeete" erscheint in der Liste mit Status "Aktiv"
- Dienstplan zeigt die 4 Mitglieder in Rotations-Reihenfolge

**Nachbedingungen**:
- DutyRotation mit 4 Mitgliedern und wöchentlichem Intervall ist aktiv

**Tags**: [req-024, duty-rotation, admin, happy-path, giessdienst]

---

### TC-024-054: Gärtner kann Duty-Rotation sehen, aber nicht erstellen/bearbeiten

**Requirement**: REQ-024 §1a.3 (Duty-Rotation erstellen/bearbeiten: nur Admin; anzeigen: alle)
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- "Gießdienst Gemeinschaftsbeete" ist aktiv
- Max hat Rolle "grower"

**Testschritte**:
1. Max navigiert zur Dienstplan-Seite

**Erwartete Ergebnisse**:
- Max sieht den Dienstplan "Gießdienst Gemeinschaftsbeete" (Anzeige der Rotations-Reihenfolge, aktuell diensthabende Person)
- Kein "Erstellen"- oder "Bearbeiten"-Button für Max sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, duty-rotation, grower-readonly, fk-06]

---

### TC-024-055: Dienst-Tausch anfragen — Happy Path

**Requirement**: REQ-024 §1a.3 (Dienst-Tausch anfragen: Admin, Grower), §1.1 Szenario 7
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Tom hat Gießdienst in KW 12 (2026-03-16)
- Tom ist als Gärtner eingeloggt

**Testschritte**:
1. Tom navigiert zum Dienstplan
2. Tom klickt auf seinen Dienst (KW 12) → "Tausch anfragen"
3. Dialog öffnet sich mit Option: Tauschpartner wählen (Anna) oder offene Anfrage an alle
4. Tom gibt Grund ein: "Urlaub"
5. Tom sendet die Anfrage

**Erwartete Ergebnisse**:
- Tausch-Anfrage erscheint im System mit Status "Ausstehend"
- Anna (und optionale andere Mitglieder) sieht die Tausch-Anfrage in ihrem Dienstplan
- Tom sieht den Dienst als "Tausch angefragt" markiert

**Nachbedingungen**:
- DutySwapRequest mit Status "pending" existiert

**Tags**: [req-024, duty-swap, grower, happy-path, tausch-anfrage]

---

### TC-024-056: Dienst-Tausch annehmen — Happy Path

**Requirement**: REQ-024 §1a.3 (Dienst-Tausch akzeptieren: Admin, Grower)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Tausch-Anfrage von Tom für KW 12 an Anna existiert (status: pending)
- Anna ist als Gärtner eingeloggt

**Testschritte**:
1. Anna sieht die Tausch-Anfrage in ihrem Dienstplan (oder Benachrichtigung)
2. Anna klickt "Tausch annehmen"

**Erwartete Ergebnisse**:
- Tausch-Anfrage zeigt Status "Akzeptiert"
- Dienstplan aktualisiert sich: KW 12 zeigt Anna statt Tom
- Tom sieht die Bestätigung: "Anna hat deinen Dienst übernommen"

**Nachbedingungen**:
- DutySwapRequest hat Status "accepted"
- Rotations-Zuweisung für KW 12 zeigt Anna

**Tags**: [req-024, duty-swap, accept, grower, happy-path]

---

### TC-024-057: Beobachter kann keinen Dienst-Tausch anfragen

**Requirement**: REQ-024 §1a.3 (Dienst-Tausch anfragen: nicht für Viewer)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Anna hat Rolle "viewer" im Tenant
- Ein Dienstplan ist aktiv

**Testschritte**:
1. Anna navigiert zum Dienstplan
2. Anna versucht auf "Tausch anfragen" zu klicken

**Erwartete Ergebnisse**:
- "Tausch anfragen"-Button ist **nicht sichtbar** für Anna (Viewer haben keine Teilnahme-Berechtigung)

**Nachbedingungen**:
- Kein Tausch angefragt

**Tags**: [req-024, duty-swap, viewer-keine-berechtigung, berechtigungspruefung]

---

## 13. Pinnwand / Bulletin-Board

### TC-024-058: Pinnwand-Post erstellen als Gärtner — Happy Path

**Requirement**: REQ-024 §1a.3 (Pinnwand-Post erstellen: Admin, Grower), §1.1 Szenario 8, §2 BulletinPost-Modell
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Tom ist Gärtner im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer befindet sich auf der Pinnwand-Seite (z.B. `/t/gemeinschaftsgarten-sonnenschein/bulletin`)

**Testschritte**:
1. Tom klickt "Neuer Beitrag" (o.ä.)
2. Dialog öffnet sich
3. Tom wählt Kategorie: "Warnung" (alert)
4. Tom gibt Text ein: "Schneckenalarm auf den Salatbeeten! Bitte heute Abend Bierfallen aufstellen."
5. Tom klickt "Veröffentlichen"

**Erwartete Ergebnisse**:
- Post erscheint auf der Pinnwand mit Kategorie-Chip "Warnung" (oder entsprechender Farbe/Icon)
- Post zeigt Autor "Tom" und Erstellungszeitpunkt
- Post erscheint oben in der Pinnwand-Liste (neuester zuerst)

**Nachbedingungen**:
- BulletinPost mit `category: 'alert'` und `status: 'active'` existiert

**Tags**: [req-024, bulletin-post, grower, happy-path, szenario-8]

---

### TC-024-059: Pinnwand-Post kommentieren — Happy Path

**Requirement**: REQ-024 §1a.3 (Pinnwand-Post kommentieren: Admin, Grower)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Post "Schneckenalarm" existiert auf der Pinnwand
- Lisa ist Gärtner/Admin im Tenant

**Testschritte**:
1. Lisa öffnet den Post "Schneckenalarm"
2. Lisa klickt auf "Kommentieren"
3. Lisa gibt ein: "Habe Schneckenkorn mitgebracht, liegt im Schuppen"
4. Lisa klickt "Senden"

**Erwartete Ergebnisse**:
- Kommentar erscheint unterhalb des Posts mit Autor "Lisa"
- Kommentar-Zähler des Posts erhöht sich

**Nachbedingungen**:
- BulletinComment existiert

**Tags**: [req-024, bulletin-comment, grower, happy-path]

---

### TC-024-060: Pinnwand-Post pinnen als Admin

**Requirement**: REQ-024 §1a.3 (Pinnwand-Post pinnen: nur Admin), AK-34, §1.1 Szenario 8
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Post "Nächster Arbeitseinsatz: Samstag 14.03." existiert auf der Pinnwand
- Lisa ist Admin im Tenant

**Testschritte**:
1. Lisa öffnet den Post "Nächster Arbeitseinsatz"
2. Lisa klickt auf "Anpinnen" (Pin-Icon oder Menüeintrag)

**Erwartete Ergebnisse**:
- Post erscheint oben auf der Pinnwand (über nicht-gepinnten Posts)
- Visuelles Indikator "Angepinnt" ist am Post sichtbar (Pin-Icon o.ä.)

**Nachbedingungen**:
- BulletinPost hat `pinned: true`

**Tags**: [req-024, pin-bulletin, admin, ak-34, happy-path]

---

### TC-024-061: Gärtner kann Pinnwand-Post NICHT pinnen

**Requirement**: REQ-024 §1a.3 (Pinnwand-Post pinnen: nur Admin), AK-34
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Tom ist Gärtner im Tenant
- Ein Post existiert auf der Pinnwand

**Testschritte**:
1. Tom öffnet einen Pinnwand-Post

**Erwartete Ergebnisse**:
- "Anpinnen"-Button ist **nicht sichtbar** für Tom

**Nachbedingungen**:
- Kein Post gepinnt

**Tags**: [req-024, pin-bulletin, grower-keine-berechtigung, ak-34]

---

### TC-024-062: Gärtner kann eigenen Post löschen — nicht die Posts anderer

**Requirement**: REQ-024 §1a.3 (Post löschen: Admin alle, Grower eigene), AK-35
**Priority**: High
**Category**: Berechtigungsprüfung
**Preconditions**:
- Tom hat Post "Schneckenalarm" (eigener Post) erstellt
- Lisa hat Post "Nächster Arbeitseinsatz" erstellt
- Tom ist Gärtner

**Testschritte**:
1. Tom klickt auf "Löschen" bei seinem Post "Schneckenalarm"
2. Tom klickt auf "Löschen" bei Lisas Post "Nächster Arbeitseinsatz"

**Erwartete Ergebnisse**:
- Für eigenen Post: Lösch-Aktion ist möglich (Button sichtbar), Post verschwindet nach Bestätigung
- Für Lisas Post: "Löschen"-Button ist **nicht sichtbar** für Tom

**Nachbedingungen**:
- Nur Toms eigener Post gelöscht

**Tags**: [req-024, delete-post, grower-eigene, ak-35, berechtigungspruefung]

---

### TC-024-063: Beobachter kann Pinnwand nur lesen

**Requirement**: REQ-024 §1a.3 (Pinnwand-Post lesen: alle; erstellen/kommentieren: kein Viewer)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Anna ist Viewer im Tenant
- Pinnwand hat mehrere Posts

**Testschritte**:
1. Anna navigiert zur Pinnwand

**Erwartete Ergebnisse**:
- Anna sieht alle Posts und gepinnten Posts (read-only)
- Kein "Neuer Beitrag"- oder "Kommentieren"-Button sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, bulletin-board, viewer-readonly, fk-07]

---

### TC-024-064: Post mit Ablaufdatum — automatisches Ausblenden

**Requirement**: REQ-024 §2 BulletinPost (expires_at: automatisches Ausblenden)
**Priority**: Low
**Category**: Zustandswechsel
**Preconditions**:
- Post "Ernte-Angebot: Zucchini zu verschenken" wurde mit `expires_at` gestern erstellt

**Testschritte**:
1. Nutzer navigiert zur Pinnwand

**Erwartete Ergebnisse**:
- Der abgelaufene Post ist **nicht mehr sichtbar** auf der aktiven Pinnwand (ausgeblendet/archiviert)

**Nachbedingungen**:
- Kein Status geändert (Anzeige-Filter)

**Tags**: [req-024, bulletin-expires, automatisch, zustandswechsel]

---

## 14. Gemeinsame Einkaufsliste (SharedShoppingList)

### TC-024-065: Einkaufsliste erstellen als Admin — Happy Path

**Requirement**: REQ-024 §1a.3 (Shopping-List erstellen: nur Admin), §2 SharedShoppingList-Modell
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Lisa ist Admin im Tenant "Gemeinschaftsgarten Sonnenschein"
- Nutzer befindet sich auf der Einkaufslisten-Seite

**Testschritte**:
1. Lisa klickt "Neue Liste erstellen"
2. Lisa gibt Namen ein: `Saatgut-Sammelbestellung Frühjahr 2026`
3. Lisa klickt "Erstellen"

**Erwartete Ergebnisse**:
- Neue Einkaufsliste erscheint mit Status "Offen" (open)
- Liste zeigt den Namen und Erstellungszeitpunkt

**Nachbedingungen**:
- SharedShoppingList mit `status: 'open'` existiert

**Tags**: [req-024, shopping-list, admin, happy-path]

---

### TC-024-066: Gärtner kann Items zur Einkaufsliste hinzufügen

**Requirement**: REQ-024 §1a.3 (Shopping-List Items hinzufügen: Admin, Grower)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "Saatgut-Sammelbestellung Frühjahr 2026" mit Status "Offen" existiert
- Max ist Gärtner

**Testschritte**:
1. Max öffnet "Saatgut-Sammelbestellung Frühjahr 2026"
2. Max klickt "Item hinzufügen"
3. Max gibt ein: Item "Tomatensamen Sungold", Menge "3 Tüten"
4. Max klickt "Hinzufügen"

**Erwartete Ergebnisse**:
- Item "Tomatensamen Sungold (3 Tüten)" erscheint in der Liste
- Item zeigt Anforderer "Max" und ist standardmäßig nicht abgehakt

**Nachbedingungen**:
- Item in der SharedShoppingList mit `requested_by: Max._key`

**Tags**: [req-024, shopping-list-item, grower, happy-path]

---

### TC-024-067: Gärtner kann keine Einkaufsliste erstellen

**Requirement**: REQ-024 §1a.3 (Shopping-List erstellen: nur Admin)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max ist Gärtner im Tenant

**Testschritte**:
1. Max navigiert zur Einkaufslisten-Seite

**Erwartete Ergebnisse**:
- "Neue Liste erstellen"-Button ist **nicht sichtbar** für Max

**Nachbedingungen**:
- Keine Liste erstellt

**Tags**: [req-024, shopping-list-create, grower-keine-berechtigung]

---

### TC-024-068: Beobachter kann Einkaufsliste nur lesen

**Requirement**: REQ-024 §1a.3 (Shopping-List anzeigen: alle; Items hinzufügen/abschließen: nur Admin+Grower)
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Anna ist Viewer im Tenant
- "Saatgut-Sammelbestellung Frühjahr 2026" existiert mit 3 Items

**Testschritte**:
1. Anna navigiert zur Einkaufslisten-Seite
2. Anna öffnet die Einkaufsliste

**Erwartete Ergebnisse**:
- Anna sieht die Liste und alle Items (read-only)
- Kein "Item hinzufügen"- oder "Abschließen"-Button sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, shopping-list, viewer-readonly, fk-07]

---

### TC-024-069: Einkaufsliste abschließen als Admin

**Requirement**: REQ-024 §1a.3 (Shopping-List abschließen: nur Admin)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- "Saatgut-Sammelbestellung Frühjahr 2026" mit Status "Offen" und mehreren Items existiert
- Lisa ist Admin

**Testschritte**:
1. Lisa öffnet die Einkaufsliste
2. Lisa klickt "Liste abschließen" (o.ä.)
3. Bestätigungs-Dialog erscheint
4. Lisa bestätigt

**Erwartete Ergebnisse**:
- Listen-Status ändert sich zu "Abgeschlossen" (closed)
- Keine weiteren Items können hinzugefügt werden (Bearbeiten deaktiviert)

**Nachbedingungen**:
- SharedShoppingList hat `status: 'closed'`

**Tags**: [req-024, shopping-list-close, admin, zustandswechsel]

---

## 15. Cross-Tenant-Isolation

### TC-024-070: Ressourcen eines Tenants für Nicht-Mitglieder unsichtbar

**Requirement**: REQ-024 §1 Kernkonzepte, AK-14
**Priority**: Critical
**Category**: Berechtigungsprüfung
**Preconditions**:
- "Gemeinschaftsgarten Sonnenschein" hat 5 Pflanzen, 3 Aufgaben
- Nutzer "Fremder" ist **nicht** Mitglied in "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. "Fremder" navigiert (oder versucht zu navigieren) zu `/t/gemeinschaftsgarten-sonnenschein/plant-instances`

**Erwartete Ergebnisse**:
- Zugriff wird verweigert: Seite zeigt Fehlermeldung "Kein Zugriff" oder Nutzer wird zum eigenen Dashboard weitergeleitet
- Keine Pflanzen oder Aufgaben des Tenants sind sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, cross-tenant-isolation, ak-14, kritisch, sicherheit]

---

### TC-024-071: Persönlicher und organisatorischer Tenant vollständig getrennt

**Requirement**: REQ-024 §1.1 Szenario 6, AK-18
**Priority**: Critical
**Category**: Berechtigungsprüfung
**Preconditions**:
- Max hat: Tenant "Maxs Garten" (persönlich, 3 Orchideen) + Tenant "Grüne Oase e.V." (Gärtner, 20 Tomaten)
- Lisa ist Mitglied in "Grüne Oase e.V." (Gärtner), aber **nicht** in "Maxs Garten"

**Testschritte**:
1. Lisa ist in "Grüne Oase e.V." aktiv und sieht Maxs Parzelle A1 (20 Tomaten)
2. Lisa versucht "Maxs Garten" im Tenant-Switcher zu finden oder direkt aufzurufen

**Erwartete Ergebnisse**:
- "Maxs Garten" erscheint **nicht** in Lisas Tenant-Switcher
- Lisas Zugriff auf `/t/maxs-garten/...` wird verweigert
- Maxs Orchideen sind für Lisa vollständig unsichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, personal-tenant-isolation, ak-18, szenario-6, kritisch]

---

## 16. Mobile-Ansicht (MobileCard)

### TC-024-072: Mitgliederliste auf mobilen Geräten als MobileCard dargestellt

**Requirement**: REQ-024 §4.2 MemberListPage, NFR (Mobile-First)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Browser-Viewport ist auf mobile Breite eingestellt (< sm Breakpoint, z.B. 375px)
- Tenant "Gemeinschaftsgarten Sonnenschein" hat 3 Mitglieder
- Nutzer befindet sich auf TenantSettingsPage, Tab "Mitglieder"

**Testschritte**:
1. Nutzer öffnet Tab "Mitglieder" auf einem mobilen Viewport

**Erwartete Ergebnisse**:
- Mitglieder werden als MobileCard-Komponenten dargestellt (nicht als Tabelle)
- Jede Karte zeigt: Name, Rolle-Chip, Beigetreten-Datum
- Rollen-Dropdown und Löschen-Button sind auf der Karte zugänglich (falls Admin)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, mobile-card, member-list, responsive, mobil]

---

## 17. Leere Zustände (Empty States)

### TC-024-073: Mitgliederliste leer — Empty-State-Anzeige

**Requirement**: REQ-024 §4.2, i18n "pages.tenants.noMembers"
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist Admin eines Tenants, der noch keine anderen Mitglieder hat (nur der Ersteller selbst)

**Testschritte**:
1. Nutzer öffnet TenantSettingsPage, Tab "Mitglieder"

**Erwartete Ergebnisse**:
- Sofern nur der Admin selbst als Mitglied vorhanden ist und keine leere Liste erscheint: korrekte Darstellung mit 1 Mitglied
- Wenn der Nutzer alle anderen Mitglieder entfernt hat: "Noch keine Mitglieder vorhanden." wird angezeigt

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, empty-state, member-list, i18n]

---

### TC-024-074: Einladungsliste leer — Empty-State-Anzeige

**Requirement**: REQ-024 §4.2, i18n "pages.tenants.noInvitations"
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- Tenant hat keine ausstehenden Einladungen
- Nutzer ist Admin und befindet sich auf Tab "Einladungen"

**Testschritte**:
1. Nutzer öffnet Tab "Einladungen"

**Erwartete Ergebnisse**:
- "Keine ausstehenden Einladungen." wird angezeigt

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, empty-state, invitation-list, i18n]

---

## 18. Grenzwert- und Edge-Case-Tests

### TC-024-075: Tenant-Name mit genau 2 Zeichen (Minimalgrenze)

**Requirement**: REQ-024 §3.1 TenantEngine (validate_tenant_name: min 2 Zeichen)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer gibt im Feld "Name" ein: `AB` (exakt 2 Zeichen)
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Tenant wird erfolgreich erstellt (2 Zeichen ist gültig)
- Tenant "AB" erscheint im Tenant-Switcher

**Nachbedingungen**:
- Tenant mit Name "AB" existiert

**Tags**: [req-024, tenant-create, formvalidierung, minimalgrenze]

---

### TC-024-076: Tenant-Name mit genau 200 Zeichen (Maximalgrenze)

**Requirement**: REQ-024 §3.1 TenantEngine (validate_tenant_name: max 100 Zeichen; Frontend: maxLength=200)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer gibt einen Namen mit genau 200 Zeichen ein (Feld erlaubt laut Frontend `maxLength: 200`)
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Frontend lässt die Eingabe zu (maxLength=200 im Input-Element)
- Erstellung erfolgreich oder Backend gibt Fehlermeldung wenn serverseitige Validierung auf 100 Zeichen begrenzt

**Nachbedingungen**:
- Status abhängig von Backend-Validierung

**Tags**: [req-024, tenant-create, formvalidierung, maximalgrenze, grenzwert]

---

### TC-024-077: Nur-Leerzeichen als Tenant-Name abgelehnt

**Requirement**: REQ-024 §3.1 TenantEngine (kein reiner Whitespace)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer befindet sich auf `/tenants/create`

**Testschritte**:
1. Nutzer gibt im Feld "Name" nur Leerzeichen ein: `   `
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Fehlermeldung erscheint oder Formular wird nicht abgesendet
- Kein Tenant mit leerem/whitespace-Namen erstellt

**Nachbedingungen**:
- Kein Tenant erstellt

**Tags**: [req-024, tenant-create, formvalidierung, whitespace-name]

---

### TC-024-078: Nutzer in Tenant A Admin, in Tenant B Viewer — verschiedene UI-Zustände

**Requirement**: REQ-024 §1 Kernkonzepte, AK-05
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Max hat Rolle "admin" in "Demo-Garten" und Rolle "viewer" in "Gemeinschaftsgarten Sonnenschein"

**Testschritte**:
1. Max aktiviert "Demo-Garten" im Tenant-Switcher → navigiert zu `/t/demo-garten/settings`
2. Max wechselt zu "Gemeinschaftsgarten Sonnenschein" → navigiert zu `/t/gemeinschaftsgarten-sonnenschein/settings`

**Erwartete Ergebnisse**:
- In "Demo-Garten": Tab "Einladungen" sichtbar, "Mitglied einladen"-Button aktiv, Rollen-Dropdowns bearbeitbar
- In "Gemeinschaftsgarten Sonnenschein": Tab "Einladungen" NICHT sichtbar, keine Verwaltungs-Buttons aktiv

**Nachbedingungen**:
- Kein Status geändert (nur Lesen)

**Tags**: [req-024, multi-role, ak-05, zustandswechsel, rollen-kontext]

---

### TC-024-079: OIDC-Provider mit default_tenant_key — neuer Nutzer auto-joinned

**Requirement**: REQ-024 §1 Einladungssystem OIDC-Auto-Join, AK-09, §1.1 Szenario 4
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- OIDC-Provider "keycloak-anbauverein" ist konfiguriert mit `default_tenant_key` = Tenant "Cannabis Social Club Berlin" und `default_role: 'grower'`
- Nutzer "Anna" hat noch keinen Kamerplanter-Account

**Testschritte**:
1. Anna öffnet die Kamerplanter-Loginseite
2. Anna klickt auf den OIDC-Button "Cannabis Social Club Berlin" (Keycloak-Login)
3. Anna wird zu Keycloak weitergeleitet und meldet sich an
4. Anna wird zurück zu Kamerplanter geleitet

**Erwartete Ergebnisse**:
- Anna ist jetzt eingeloggt in Kamerplanter
- Im Tenant-Switcher erscheint "Cannabis Social Club Berlin" mit Rolle "Gärtner"
- Anna wird automatisch auf das Tenant-Dashboard weitergeleitet

**Nachbedingungen**:
- Anna hat Membership mit Rolle "grower" im "Cannabis Social Club Berlin"-Tenant

**Tags**: [req-024, oidc-auto-join, ak-09, szenario-4, happy-path]

---

### TC-024-080: Einladungs-E-Mail ohne gültige E-Mail-Adresse abgelehnt

**Requirement**: REQ-024 §4.2 InviteDialog (E-Mail-Validierung)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Nutzer ist Admin auf der Einladungs-Seite

**Testschritte**:
1. Nutzer gibt im Feld "E-Mail-Adresse" ein: `keine-email`
2. Nutzer klickt "Einladung senden"

**Erwartete Ergebnisse**:
- Formular wird nicht abgesendet
- Fehlermeldung erscheint: ungültige E-Mail-Adresse (Browser-native Validierung oder Inline-Fehler)

**Nachbedingungen**:
- Keine Einladung gesendet

**Tags**: [req-024, email-invitation, formvalidierung, invalid-email]

---

### TC-024-081: Platform-Tenant kann nicht von regulärem Nutzer auf is_platform=true gesetzt werden

**Requirement**: REQ-024 §2 Tenant-Modell, AK-20
**Priority**: Medium
**Category**: Berechtigungsprüfung
**Preconditions**:
- Regulärer Nutzer (kein Platform-Admin) ist Admin seines eigenen Tenants
- Nutzer versucht, seinen Tenant als "Platform-Tenant" zu markieren

**Testschritte**:
1. Nutzer navigiert zu Tenant-Einstellungen
2. Nutzer sucht nach einer Option "Platform-Tenant" oder versucht, `is_platform: true` zu setzen

**Erwartete Ergebnisse**:
- Keine solche Option ist im Formular sichtbar
- Das Backend lehnt einen Versuch ab, `is_platform: true` zu setzen (Fehlermeldung falls versucht)

**Nachbedingungen**:
- Kein regulärer Tenant hat `is_platform: true` gesetzt

**Tags**: [req-024, platform-tenant, ak-20, sicherheit, berechtigungspruefung]

---

### TC-024-082: Tenant-Slug erscheint korrekt in der URL nach Wechsel

**Requirement**: REQ-024 §4.3 URL-Struktur, §1.1 Szenario 3
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Max ist Mitglied in "Grüne Oase e.V." (slug: `gruene-oase-ev`)
- Max ist aktiver Tenant in "Maxs Garten" (slug: `maxs-garten`)

**Testschritte**:
1. Max öffnet Pflanzenliste: URL ist `/t/maxs-garten/plant-instances`
2. Max wechselt im Tenant-Switcher zu "Grüne Oase e.V."

**Erwartete Ergebnisse**:
- URL ändert sich zu `/t/gruene-oase-ev/...` (entsprechender Seite im neuen Tenant)
- Seiten-Inhalt zeigt die Daten von "Grüne Oase e.V."
- Browser-Zurück-Button ermöglicht Rückkehr zu `/t/maxs-garten/...`

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-024, url-routing, tenant-switcher, navigation, ak-04]

---

## Abdeckungsmatrix

| Spec-Abschnitt | Testfall-IDs |
|---|---|
| §1 Kernkonzepte — Persönlicher Tenant | TC-024-001, TC-024-002 |
| §1 Kernkonzepte — Organisations-Tenant erstellen | TC-024-003 – TC-024-007 |
| §1 Einladungssystem (E-Mail, Link, OIDC) | TC-024-022 – TC-024-029, TC-024-079 |
| §1.1 Szenarien (1–8) | TC-024-003, TC-024-033, TC-024-009, TC-024-079, TC-024-036, TC-024-071, TC-024-053, TC-024-058 |
| §1a.1 Ressourcen-Permissions | TC-024-033 – TC-024-035, TC-024-037 – TC-024-039 |
| §1a.2 Tenant-Verwaltungs-Permissions | TC-024-012 – TC-024-021, TC-024-029, TC-024-032, TC-024-040 – TC-024-041 |
| §1a.3 Kollaborations-Permissions | TC-024-053 – TC-024-069 |
| §1a.4 Platform-Rollen | TC-024-042 – TC-024-047, TC-024-051 – TC-024-052 |
| §1a.5 Zuweisungsbasierte Write-Kontrolle | TC-024-033, TC-024-034, TC-024-038, TC-024-039 |
| §2 DutyRotation / DutySwapRequest | TC-024-053 – TC-024-057 |
| §2 BulletinPost / BulletinComment | TC-024-058 – TC-024-064 |
| §2 SharedShoppingList | TC-024-065 – TC-024-069 |
| §2 Stammdaten-Scoping (tenant_has_access) | TC-024-048 – TC-024-052 |
| §3.1 TenantEngine (Slug, Name-Validierung) | TC-024-003 – TC-024-007, TC-024-075 – TC-024-077 |
| §3.1 MembershipEngine (Letzter-Admin-Schutz) | TC-024-017, TC-024-019, TC-024-021 |
| §3.1 InvitationEngine (Validierung) | TC-024-025 – TC-024-028 |
| §4.1 TenantCreatePage | TC-024-003 – TC-024-007 |
| §4.1 TenantSettingsPage | TC-024-012 – TC-024-014 |
| §4.1 InvitationAcceptPage | TC-024-025 – TC-024-028 |
| §4.2 TenantSwitcher | TC-024-008 – TC-024-011, TC-024-082 |
| §4.2 MemberListPage | TC-024-015 – TC-024-021, TC-024-072 |
| §4.2 AssignmentListPage | TC-024-030 – TC-024-032 |
| §4.3 URL-Struktur | TC-024-009, TC-024-082 |
| AK-01 – AK-22 | TC-024-001 – TC-024-052 (vollständig) |
| AK-29 – AK-44 (RBAC Permission-Matrix) | TC-024-033 – TC-024-044 |
| AK-45 – AK-51 (Notfallverwaltung) | TC-024-042 – TC-024-047 |
| FK-01 – FK-07 (Frontend-Kriterien) | TC-024-008, TC-024-009, TC-024-015, TC-024-023, TC-024-030, TC-024-013 – TC-024-014 |
| Cross-Tenant-Isolation | TC-024-070, TC-024-071 |
| Leere Zustände (Empty States) | TC-024-073, TC-024-074 |
| Mobile-Ansicht | TC-024-072 |
| Grenzwerte & Edge Cases | TC-024-075 – TC-024-081 |
