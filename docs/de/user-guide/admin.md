# Plattform-Admin-Bereich

Der Plattform-Admin-Bereich ist ausschließlich für Nutzer mit der Plattform-Rolle **admin** zugänglich. Er ermöglicht die plattformweite Verwaltung aller Mandanten und Nutzer — unabhängig von der mandantengebundenen Tenant-Admin-Rolle.

---

## Voraussetzungen

- Plattform-Rolle **admin** (unterscheidet sich von der Tenant-Admin-Rolle)
- Zugang über `/admin/platform` (im Full-Modus)

!!! warning "Nicht mit Tenant-Admin verwechseln"
    Die Plattform-Admin-Rolle ist eine **plattformweite** Sonderrolle. Sie berechtigt zum Zugriff auf Daten aller Mandanten. Die Tenant-Admin-Rolle dagegen ist auf einen einzelnen Mandanten beschränkt und wird über **Einstellungen > Mandanten > Mitglieder** vergeben.

---

## Abgrenzung: Plattform-Admin vs. Tenant-Admin

| Funktion | Plattform-Admin | Tenant-Admin |
|---------|----------------|-------------|
| Alle Mandanten verwalten | Ja | Nein |
| Nutzerverwaltung plattformweit | Ja | Nein |
| Mandantenstatistiken einsehen | Ja | Nein |
| OIDC-Provider konfigurieren | Ja | Nein |
| Mitglieder des eigenen Mandanten verwalten | Ja | Ja |
| Standorte und Pflanzdaten des Mandanten | Ja | Ja |

---

## Mandantenverwaltung

Im Bereich **Admin > Mandanten** können Sie:

- Alle Mandanten der Plattform einsehen (Name, Slug, Mitgliederzahl, Erstellungsdatum)
- Einzelne Mandanten deaktivieren oder löschen
- Mandanten-Kontingente und Limits einsehen
- Mitglieder eines Mandanten stellvertretend verwalten

!!! danger "Mandanten löschen ist irreversibel"
    Das Löschen eines Mandanten entfernt alle zugehörigen Daten (Pflanzen, Durchläufe, Protokolle). Diese Aktion kann nicht rückgängig gemacht werden. Erstellen Sie vorher ein Daten-Export für den betroffenen Mandanten.

---

## Nutzerverwaltung

Im Bereich **Admin > Nutzer** können Sie:

- Alle Nutzerkonten der Plattform einsehen
- Nutzerkonten sperren oder deaktivieren
- Plattform-Rollen zuweisen (`admin`, `viewer`)
- Passwort-Reset für Nutzer auslösen
- DSGVO-Anfragen (Datenlöschung, Datenauskunft) bearbeiten

!!! note "DSGVO-Anfragen"
    Betroffenenrechte nach Art. 15–21 DSGVO stehen Nutzern über die Self-Service-API unter `/api/v1/privacy/` zur Verfügung. Als Platform-Admin können Sie Anfragen im Admin-Bereich einsehen und bearbeiten. Weitere Informationen: [Datenschutz (DSGVO)](privacy.md).

---

## Statistiken

Der Bereich **Admin > Statistiken** bietet eine Übersicht über:

- Anzahl aktiver Mandanten und Nutzer
- Aktive Pflanzdurchläufe plattformweit
- Celery-Task-Queue-Status
- Speicherverbrauch (ArangoDB, TimescaleDB, Redis)

---

## OIDC-Provider

Unter **Admin > OIDC-Provider** konfigurieren Sie föderierte Authentifizierungs-Provider (z.B. Google, GitHub, firmeneigene OIDC-Instanzen). Diese Einstellungen gelten plattformweit für alle Mandanten.

Mehr dazu: [Authentifizierung](../api/authentication.md).

---

## Häufige Fragen

??? question "Wer kann die Plattform-Admin-Rolle vergeben?"
    Die Plattform-Admin-Rolle kann nur von einem bestehenden Platform-Admin vergeben werden — direkt über die API oder im Admin-Bereich. Beim ersten Setup wird der erste registrierte Nutzer automatisch als Platform-Admin konfiguriert.

??? question "Kann ein Platform-Admin auch Tenant-Daten einsehen?"
    Ja. Platform-Admins haben Lesezugriff auf alle mandantengebundenen Daten. Diese Berechtigung sollte auf vertrauenswürdige Personen beschränkt und mit einem Audit-Log versehen sein (REQ-024).

??? question "Gibt es eine Viewer-Rolle für den Admin-Bereich?"
    Ja. Die Plattform-Rolle `viewer` bietet Lesezugriff auf alle Admin-Statistiken und Mandanten-Übersichten, jedoch keine Schreibberechtigungen.

---

## Siehe auch

- [Mandanten & Gärten](tenants.md) — Mandantenverwaltung als Tenant-Admin (REQ-024)
- [Datenschutz (DSGVO)](privacy.md) — Betroffenenrechte und DSGVO-Compliance
- [Authentifizierung](../api/authentication.md) — JWT, OAuth2/OIDC, Service Accounts
