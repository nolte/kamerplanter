# ZG-005: Cannabis Social Club / Anbauvereinigung

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Sekundaere Zielgruppe (teilweise adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Organisierter Cannabis-Anbauverein (CanG-konform) |
| **Altersgruppe** | 25-55 Jahre |
| **Betriebsgroesse** | 20-500 Pflanzen, mehrere Raeume, Team-Betrieb |
| **Technische Affinitaet** | Mittel bis Hoch |
| **Botanisches Vorwissen** | Hoch (professionelle Anbauer im Team) |
| **Primaere Nutzungsumgebung** | Desktop (Verwaltung/Reporting), Tablet (im Anbau-Raum) |
| **Abdeckungsgrad** | Teilweise -- Compliance-Reporting fehlt als eigenstaendige Funktion |

## 2. Persona

### 2a. Vereins-Manager
**Name:** Patrick, 38, ehemaliger Gastronom, Vorsitzender einer Anbauvereinigung
**Situation:** Hat seit CanG-Inkrafttreten (April 2024) eine Anbauvereinigung mit 120 Mitgliedern und 3 Anbauraumen gegruendet. Muss behordliche Auflagen erfuellen: Dokumentation des Anbaus, Chargen-Nachverfolgung, Abgabe-Protokolle. Nutzt OIDC ueber den Vereins-IdP (Keycloak) fuer SSO aller Mitglieder. Braucht Rollen-Trennung: Anbauer duerfen Pflanzen pflegen, Manager sehen Reporting, Buchhalter kontrollieren Verbrauch.

### 2b. Vereins-Anbauer
**Name:** Lisa, 29, Gaertnermeisterin und Head-Grower im Social Club
**Situation:** Verantwortlich fuer 3 Anbauraeume mit je 50-80 Pflanzen. Dokumentiert jeden Grow-Zyklus lueckenlos fuer Behoerden-Kontrollen. Arbeitet mit standardisierten Naehrstoffplaenen und muss Chargen-Nummern fuer jede Ernte vergeben. Hat 2 Junior-Grower im Team.

**Motivation:**
- **Compliance:** Lueckenlose Dokumentation nach CanG (Ernte-Protokolle, Chargen-IDs, Abgabe-Nachweise)
- **Rollen-Trennung:** Anbauer, Manager, Buchhalter mit granularen Berechtigungen
- **Team-Koordination:** Aufgaben-Delegation, Schichtplanung
- **Revisionssicherheit:** Audit-Trail fuer Behoerden-Kontrollen
- **Skalierung:** Verwaltung mehrerer Anbauraeume und Teams

## 3. Kernbeduerfnisse

### 3.1 Compliance-Dokumentation (NFR-011, REQ-007, REQ-010)
- CanG-Aufbewahrungsfristen fuer alle Anbauprozessdaten
- Revisionssichere Ernte-Protokolle (nicht nachtraeglich aenderbar)
- Chargen-Nummern (Batch-IDs) fuer jede Ernte-Charge
- Seed-to-Shelf-Traceability: Saatgut/Klon -> Pflanze -> Ernte -> Abgabe
- Behandlungs-Nachweise (Pflanzenschutz-Dokumentation nach PflSchG)
- Karenz-Gate: Automatische Sperre zwischen letzter Behandlung und Ernte

### 3.2 RBAC Permission-Matrix (REQ-024)
- **Admin:** Voller Zugriff, Mitglieder-Verwaltung, Behoerden-Reporting
- **Grower:** Pflanzen-Management, Ernte-Dokumentation, nur zugewiesene Raeume
- **Viewer:** Read-Only (z.B. fuer behoerdliche Pruefer oder Buchhalter)
- Granulare Rechte pro Ressourcentyp (PlantingRun, HarvestBatch, Treatment, etc.)
- `require_permission()` FastAPI Dependency fuer alle Endpunkte

### 3.3 Multi-Raum-Management (REQ-002, REQ-013)
- Mehrere Anbauraeume als Standorte in der Location-Hierarchie
- Raueme in verschiedenen Phasen (Veg-Raum, Bluete-Raum, Trocknung)
- PlantingRuns pro Raum mit unterschiedlichen Naehrstoffplaenen
- Batch-Operationen: 50 Pflanzen gleichzeitig in naechste Phase

### 3.4 Team-Koordination (REQ-006, REQ-024)
- Aufgaben-Zuweisung an Team-Mitglieder
- Schichtplan-Integration (wer arbeitet wann?)
- Status-Ueberblick: Welche Raeume brauchen Aufmerksamkeit?
- Uebergabe-Protokoll zwischen Schichten

### 3.5 Authentifizierung und SSO (REQ-023)
- OIDC-Integration fuer Vereins-IdP (Keycloak, Authentik)
- Service Accounts fuer Sensor-Systeme und Automatisierung
- 2FA fuer Admin-Zugang (Compliance-Anforderung)
- IP-Allowlist fuer Service Accounts

### 3.6 Ernte und Abgabe (REQ-007)
- Ernte-Chargen mit eindeutiger Chargen-Nummer
- Qualitaetsbewertung pro Charge
- Abgabe-Dokumentation (wer hat wann wieviel erhalten)
- Gewichtskontrolle und -protokollierung
- Lager-Bestandsfuehrung

### 3.7 DSGVO-Konformitaet (REQ-025)
- Mitglieder-Daten mit definierten Aufbewahrungsfristen
- Betroffenenrechte (Auskunft, Loeschung, Berichtigung)
- Datenschutz-Folgenabschaetzung fuer Sensor-Daten
- Consent-Management fuer optionale Datenverarbeitungen

### 3.8 Reporting (Fehlend -- empfohlen als REQ-032)
- PDF-Reports fuer Behoerden-Kontrollen
- Ernte-Protokoll nach CanG-Vorgaben
- Behandlungsnachweis nach PflSchG
- Monats-/Quartals-Zusammenfassung
- Digitale Signatur oder Export-Zertifizierung

## 4. Typische Workflows

### 4.1 Neuen Grow-Zyklus starten (Head-Grower)
1. PlantingRun fuer Bluete-Raum anlegen (Strain, Charge, Naehrstoffplan)
2. Pflanzen aus Clone-Run des Veg-Raums uebernehmen
3. Team-Aufgaben verteilen (taegliche Kontrolle, Giessen, pH-Messung)
4. Phase-Transition dokumentieren (12/12-Start)
5. Chargen-Nummer wird automatisch vergeben

### 4.2 Behoerden-Kontrolle vorbereiten (Admin)
1. Reporting-Dashboard oeffnen
2. Zeitraum waehlen (letztes Quartal)
3. Ernte-Protokolle exportieren (Chargen, Gewichte, Qualitaet)
4. Behandlungsnachweise exportieren (Pflanzenschutz)
5. Mitglieder-Abgabe-Protokoll erstellen
6. PDF generieren, optional digital signieren

### 4.3 Tagesablauf Head-Grower
1. Dashboard: Alle Raeume pruefen (VPD, Temperatur, Aufgaben)
2. Faellige Aufgaben delegieren an Junior-Grower
3. Inspektions-Runde: Schaedlings-Check, Phasen-Bewertung
4. EC/pH-Messungen dokumentieren
5. Ernte-Readiness pruefen (Bluete-Raum 1)
6. Uebergabe-Protokoll fuer Spaetschicht erstellen

### 4.4 Neues Mitglied aufnehmen (Admin)
1. Mitglied registriert sich ueber Vereins-OIDC
2. Admin weist Rolle zu (Grower mit Raum-Zuweisung)
3. Einweisung dokumentieren (Compliance-Schulung)
4. Berechtigungen pruefen (nur zugewiesene Raeume bearbeitbar)

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-003 | Hoch | Phasensteuerung (wie ZG-001, aber Team-uebergreifend) |
| REQ-004 | Hoch | Naehrstoffmanagement (standardisierte Plaene fuer alle Raeume) |
| REQ-007 | Kritisch | Ernte-Dokumentation, Chargen-IDs, Qualitaetsbewertung |
| REQ-010 | Hoch | Behandlungsdokumentation, Karenz-Gate |
| REQ-013 | Kritisch | PlantingRun als Chargen-Einheit, Batch-Operationen |
| REQ-023 | Kritisch | OIDC-SSO, Service Accounts, 2FA |
| REQ-024 | Kritisch | RBAC, Multi-Tenant, Rollen, Einladung |
| REQ-025 | Hoch | DSGVO-Betroffenenrechte, Consent |
| NFR-011 | Kritisch | CanG-Aufbewahrungsfristen, Retention Policy |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-005 (Social Club) | ZG-001 (Cannabis Solo) | ZG-004 (Gemeinschaftsgarten) |
|---------|:-:|:-:|:-:|
| Team-Betrieb | Kritisch | Nein (Einzelperson) | Ja (lockerer) |
| Compliance | Kritisch (CanG) | Mittel | Nein |
| RBAC | Kritisch | Irrelevant | Einfach |
| Chargen-Tracking | Kritisch | Nice-to-have | Irrelevant |
| OIDC/SSO | Kritisch | Nein | Nein |
| Reporting | Kritisch | Nein | Nein |
| Skalierung | 100+ Pflanzen | 4-50 Pflanzen | Pro Mitglied wenige |

## 7. Evaluationskriterien

1. **RBAC:** Kann ein Grower nur die ihm zugewiesenen Raeume bearbeiten?
2. **Chargen-Tracking:** Ist jede Ernte-Charge lueckenlos zum Saatgut/Klon rueckverfolgbar?
3. **Karenz-Gate:** Wird eine Ernte blockiert wenn ein aktiver Karenz-Intervall vorliegt?
4. **OIDC-Login:** Koennen Mitglieder sich ueber den Vereins-IdP anmelden?
5. **Service Accounts:** Kann ein Sensor-System per API-Key Daten liefern?
6. **Team-Aufgaben:** Koennen Aufgaben an bestimmte Mitglieder delegiert werden?
7. **Ernte-Reporting:** Kann ein Ernte-Protokoll als PDF exportiert werden?
8. **Revisionssicherheit:** Sind Ernte- und Behandlungs-Protokolle vor nachtraeglicher Aenderung geschuetzt?
9. **DSGVO:** Kann ein Mitglied Auskunft ueber seine Daten anfordern?
10. **Multi-Raum:** Koennen mehrere Raeume mit verschiedenen Phasen parallel verwaltet werden?

## 8. Sprachstil und Fachbegriffe

Kombination aus Cannabis-Fachsprache (wie ZG-001) plus Vereins-/Compliance-Terminologie:

- **Anbauvereinigung** (Cultivation Association), **Social Club**
- **CanG** (Cannabis-Gesetz), **BtMG** (Betaeubungsmittelgesetz)
- **Chargen-Nummer** (Batch ID), **Seed-to-Shelf**
- **Abgabe-Protokoll** (Distribution Protocol)
- **Behandlungsnachweis** (Treatment Record), **Karenz** (Safety Interval)
- **PflSchG** (Pflanzenschutzgesetz)
- **Revisionssicher** (Tamper-proof / Audit-proof)
- **OIDC/SSO** (Single Sign-On ueber Vereins-IdP)
- **Head-Grower** (Leiter des Anbaus), **Junior-Grower**
- **Veg-Raum / Bluete-Raum / Trocknung** (Room Types)
- **Compliance** (Regelkonformitaet), **Audit** (Pruefung)
