# ZG-004: Gemeinschaftsgarten-Mitglied / Urban Gardener

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Sekundaere Zielgruppe (teilweise adressiert)
**Quelle:** `spec/analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Gemeinschaftsgarten-Nutzer (Mitglied oder Admin) |
| **Altersgruppe** | 25-60 Jahre (breite Streuung) |
| **Betriebsgroesse** | 1-5 eigene Parzellen, 5-50 Mitglieder im Tenant |
| **Technische Affinitaet** | Gering bis Mittel |
| **Botanisches Vorwissen** | Gering (Neulinge) bis Hoch (erfahrene Mitglieder) |
| **Primaere Nutzungsumgebung** | Smartphone (im Garten, Koordination), Desktop (Admin-Aufgaben) |
| **Abdeckungsgrad** | Teilweise -- Kollaborations-Features noch nicht vollstaendig implementiert |

## 2. Persona

### 2a. Admin-Persona
**Name:** Tom, 42, Sozialarbeiter und Gemeinschaftsgarten-Initiator
**Situation:** Hat vor 2 Jahren einen Gemeinschaftsgarten mit 30 Parzellen in einem Berliner Hinterhof gegruendet. 35 Mitglieder, 10 davon aktiv in der Orga. Koordiniert Giessdienst-Rotation, gemeinsame Werkzeug-Anschaffung und Saatgut-Bestellungen. Nutzt aktuell eine chaotische WhatsApp-Gruppe und ein Google Sheet. Moechte die Organisation professionalisieren, ohne Mitglieder technisch zu ueberfordern.

### 2b. Mitglied-Persona
**Name:** Aisha, 28, Studentin
**Situation:** Hat zum ersten Mal eine Parzelle im Gemeinschaftsgarten uebernommen. Keine Gartenerfahrung, aber motiviert. Braucht Anleitung was wann zu pflanzen ist und wann sie mit Giessen dran ist. Moechte Ernteueberscuesse mit anderen teilen.

**Motivation (Admin):**
- Giessdienst-Rotation fair und transparent organisieren
- Gemeinsame Einkaufsliste fuer Saatgut und Betriebsmittel
- Pinnwand fuer Ankuendigungen (Arbeitseinsaetze, Feste, Regelaenderungen)
- Parzellen-Zuweisung und Mitglieder-Verwaltung
- Ernte-Teilen ermoeglichen (Tauschboerse)

**Motivation (Mitglied):**
- Wissen was auf meiner Parzelle wann zu tun ist
- Giessdienst-Plan einsehen und bestaetigen
- Ernte teilen oder Hilfe anfragen
- Von erfahrenen Mitgliedern lernen

## 3. Kernbeduerfnisse

### 3.1 Multi-Tenancy und Rollen (REQ-024)
- Tenant-Typ: `organization` (Gemeinschaftsgarten als Tenant)
- Rollen: Admin (Vollzugriff), Grower (eigene Parzelle + Gemeinschaftsaufgaben), Viewer (nur lesen)
- Einladungslink fuer neue Mitglieder
- Parzellen-Zuweisung: LocationAssignment pro Mitglied
- Mitglieder koennen nur ihre eigenen Parzellen bearbeiten

### 3.2 Giessdienst-Rotation (REQ-024)
- DutyRotation: Zyklischer Plan wer wann den Gemeinschaftsgarten giesst
- Automatische Erinnerung an das Mitglied das dran ist
- Tausch-Moeglichkeit wenn jemand verhindert ist
- Kalender-Integration (wer hat wann Dienst?)

### 3.3 Pinnwand / Bulletin Board (REQ-024)
- BulletinPost: Admin kann Ankuendigungen posten
- Kommentare auf Posts
- Kategorien: Ankuendigung, Arbeitseinsatz, Tausch, Frage
- Push-Benachrichtigung bei neuen Posts (wenn verfuegbar)

### 3.4 Gemeinsame Einkaufsliste (REQ-024)
- SharedShoppingList: Mitglieder fuegen Bedarfe hinzu (Saatgut, Erde, Werkzeug)
- Admin kann Sammelbestellung koordinieren
- Status-Tracking: offen -> bestellt -> eingetroffen

### 3.5 Aufgaben-Delegation (REQ-006)
- Aufgaben koennen Mitgliedern zugewiesen werden
- Gemeinschafts-Aufgaben: Kompost umsetzen, Zaun reparieren, Wasserleitung warten
- Status sichtbar fuer alle (wer hat was erledigt?)

### 3.6 Ernte-Teilen (REQ-024)
- Ernteueberscuesse anbieten ("5 kg Zucchini zu verschenken")
- Anfragen stellen ("Braucht jemand Tomaten-Setzlinge?")
- Integration mit Ernte-Dokumentation (REQ-007)

### 3.7 Standort-Hierarchie (REQ-002)
- Gemeinschaftsgarten -> Bereich (Gemuese, Obst, Blumen, Gemeinschaft) -> Parzelle -> Beet
- Gemeinschafts-Flaechen (Kompost, Geraeteschuppen, Wasseranschluss)
- Standort-basierte Zuweisung: Welches Mitglied hat welche Parzelle?

## 4. Typische Workflows

### 4.1 Neues Mitglied aufnehmen (Admin)
1. Einladungslink generieren
2. Mitglied registriert sich ueber Link
3. Admin weist Parzelle zu (LocationAssignment)
4. Mitglied erhaelt Giessdienst-Slot in der Rotation
5. Beginner-Modus wird fuer Neulinge empfohlen

### 4.2 Giessdienst-Woche (Mitglied)
1. Montag: Erinnerung "Du bist diese Woche fuer den Giessdienst eingeteilt"
2. Giessdienst durchfuehren (alle zugewiesenen Bereiche)
3. Bestaetigung im System (Ein-Tap oder Kommentar)
4. Bei Verhinderung: Tausch anfragen ueber Pinnwand

### 4.3 Sammelbestellung (Admin)
1. Admin erstellt Bestellrunde auf SharedShoppingList
2. Mitglieder fuegen ihre Bedarfe hinzu (Saatgut, Pflanzen)
3. Admin schliesst Liste, berechnet Gesamtbestellung
4. Bestellung wird aufgegeben, Status: "bestellt"
5. Ware eingetroffen: Verteilung an Mitglieder

### 4.4 Arbeitseinsatz organisieren (Admin)
1. BulletinPost: "Samstag 10 Uhr Fruehlings-Arbeitseinsatz"
2. Aufgaben erstellen: Beete vorbereiten, Kompost verteilen, Zaun reparieren
3. Mitglieder melden sich fuer Aufgaben an
4. Am Tag: Aufgaben abhaken, Fortschritt dokumentieren

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-002 | Hoch | Standort-Hierarchie, Parzellen |
| REQ-006 | Hoch | Aufgaben-Delegation, Gemeinschafts-Tasks |
| REQ-007 | Mittel | Ernte-Dokumentation und -Teilen |
| REQ-015 | Mittel | Kalender (Giessdienst, Arbeitseinsaetze) |
| REQ-020 | Hoch | Onboarding fuer Garten-Neulinge |
| REQ-021 | Hoch | Erfahrungsstufen (Neulinge vs. erfahrene Gaertner) |
| REQ-023 | Hoch | Registrierung, Einladungslink |
| REQ-024 | Kritisch | Tenant, Rollen, DutyRotation, Pinnwand, Einkaufsliste |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-004 (Gemeinschaft) | ZG-002 (Freiland) | ZG-005 (Social Club) |
|---------|:-:|:-:|:-:|
| Kollaboration | Kritisch | Nein (Einzelperson) | Kritisch |
| Rollen-System | Kritisch | Irrelevant | Kritisch |
| Giessdienst | Kritisch | Irrelevant | Teilweise |
| Botanisches Niveau | Gemischt (Neulinge + Profis) | Mittel-Hoch | Hoch |
| Compliance-Bedarf | Nein | Nein | Hoch (CanG) |
| Ernte-Teilen | Kritisch | Nein | Vereinsbasiert |

## 7. Evaluationskriterien

1. **Mitglieder-Verwaltung:** Kann ein Admin Mitglieder per Einladungslink aufnehmen und Rollen zuweisen?
2. **Parzellen-Zuweisung:** Kann eine Parzelle einem Mitglied zugewiesen werden?
3. **Giessdienst-Rotation:** Wird der Giessdienst fair rotiert und rechtzeitig erinnert?
4. **Pinnwand:** Koennen Ankuendigungen gepostet und kommentiert werden?
5. **Einkaufsliste:** Koennen Mitglieder Bedarfe zur gemeinsamen Liste hinzufuegen?
6. **Aufgaben-Delegation:** Koennen Gemeinschafts-Aufgaben erstellt und zugewiesen werden?
7. **Berechtigungen:** Kann ein Mitglied nur seine eigene Parzelle bearbeiten?
8. **Ernte-Teilen:** Koennen Ernteueberscuesse angeboten werden?
9. **Kalender:** Sind Giessdienst und Arbeitseinsaetze im Kalender sichtbar?
10. **Onboarding Neulinge:** Werden Gartenanfaenger durch den Einstieg gefuehrt?

## 8. Sprachstil und Fachbegriffe

- **Parzelle** (Plot), **Gemeinschaftsflaeche** (Shared Area)
- **Giessdienst** (Watering Duty), **Rotation** (Shift Rotation)
- **Arbeitseinsatz** (Community Work Day)
- **Sammelbestellung** (Group Order)
- **Pinnwand** (Bulletin Board), **Schwarzes Brett**
- **Ernte teilen** (Harvest Sharing), **Tauschboerse**
- **Hochbeet** (Raised Bed), **Kompost** (Compost)
- **Nutzgarten** (Kitchen Garden), **Ziergarten** (Ornamental Garden)
- **Mitglied** (Member), **Vereinsadmin** (Club Admin)
