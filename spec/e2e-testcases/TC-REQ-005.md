---
req_id: REQ-005
title: Hybrid-Sensorik & Home Assistant Integration
category: Monitoring
test_count: 58
coverage_areas:
  - Smart-Home-Gesamtdeaktivierung (UserPreference.smart_home_enabled)
  - HA-Optionalitaet (ha_token_set, AccountSettings Tab "Integrationen")
  - HA-Verbindungskonfiguration und Verbindungstest
  - Sensor-Anlage an Standort (SiteDetailPage, LocationDetailPage)
  - Sensor-Anlage an Tank (TankDetailPage)
  - Sensor-Bearbeitung und Loeschung
  - HA-Entity-Auswahl mit Autocomplete
  - Manuelle Messwert-Eingabe mit Plausibilitaetspruefung
  - Datenquellen-Kennzeichnung (Auto vs. Manual vs. Interpoliert)
  - Sensor-Health-Monitoring und Offline-Status
  - Automatische Task-Generierung bei Sensor-Ausfall
  - Kalibrierungs-Workflow (1-Point, 2-Point, Multi-Point)
  - Kalibrierungs-Erinnerung (>90 Tage)
  - Quality-Score-Anzeige
  - Anomalie-Erkennung (Ausreisser-Marker)
  - Interpolations-Anzeige (gestrichelte Linie)
  - Onboarding-Wizard Schritt 2 (Smart-Home-Toggle)
  - Wetter-Integration (Freiland-Standorte, Frostwarnung)
  - CSV-Export
  - Phasenabhaengige Alert-Profile
generated: 2026-03-21
version: "2.6"
---

# TC-REQ-005: Hybrid-Sensorik & Home Assistant Integration

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-005 Hybrid-Sensorik v2.6**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in den Testschritten. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-005 beschreibt einen Hybrid-Ansatz mit vier Datenquellen: automatisch (HA/MQTT) → semi-automatisch → Wetter-API (Freiland) → manuell. Die Smart-Home-Gesamtdeaktivierung (§4b) und die HA-Optionalitaet (§4a) sind zentrale Testbereiche, da sie die UI-Sichtbarkeit ganzer Sektionen steuern.

---

## 1. Smart-Home-Gesamtdeaktivierung (UserPreference)

### TC-REQ-005-001: Neue Nutzer sehen keine Sensor-Elemente (smart_home_enabled = false)

**Requirement**: REQ-005 §4b — Smart-Home-Gesamtdeaktivierung, UI-Visibility-Matrix
**Priority**: Critical
**Category**: Listenansicht / Navigation
**Preconditions**:
- Nutzer hat gerade das Onboarding abgeschlossen ohne Smart-Home-Toggle aktiviert zu haben
- `smart_home_enabled = false` (Standardwert fuer neue Nutzer)

**Testschritte**:
1. Nutzer navigiert zum Dashboard nach abgeschlossenem Onboarding
2. Nutzer betrachtet die Seitennavigation (Sidebar)

**Erwartete Ergebnisse**:
- Die Menuepunkte "Sensoren", "Aktoren" und "Umgebungssteuerung" sind in der Sidebar **nicht sichtbar**
- Das Dashboard zeigt keine Klimadaten-Widgets (keine VPD-Heatmap, keine Temperatur-Trends, keine CO₂-Karten)
- Die Sensor-Bereiche auf Standort- und Tank-Detailseiten sind nicht sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, smart-home-disabled, navigation, visibility, sidebar, new-user]

---

### TC-REQ-005-002: Smart-Home in Kontoeinstellungen aktivieren

**Requirement**: REQ-005 §4b — Smart-Home-Gesamtdeaktivierung, Steuerung
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist eingeloggt
- `smart_home_enabled = false`

**Testschritte**:
1. Nutzer navigiert zu Kontoeinstellungen (AccountSettings)
2. Nutzer klickt auf den Tab "Integrationen"
3. Der Abschnitt "Smart Home & Sensorik" ist sichtbar mit dem Hinweistext "Smart-Home-Funktionen sind deaktiviert. Sensor- und Aktor-Elemente werden in der gesamten Oberfläche ausgeblendet."
4. Nutzer setzt den Toggle "Smart Home Funktionen aktivieren" auf EIN

**Erwartete Ergebnisse**:
- Die Seite aktualisiert sich oder der Toggle zeigt sofort den aktivierten Zustand
- In der Sidebar erscheinen nun die Menuepunkte "Sensoren" und verwandte Bereiche
- Auf Standort-Detailseiten ist die Sensor-Sektion nun sichtbar
- Der Hinweistext "Smart-Home-Funktionen sind deaktiviert..." verschwindet

**Nachbedingungen**:
- `smart_home_enabled = true` fuer diesen Nutzer

**Tags**: [req-005, smart-home-toggle, account-settings, tab-integrationen, activation]

---

### TC-REQ-005-003: Smart-Home wieder deaktivieren ohne Datenverlust

**Requirement**: REQ-005 §4b — Verhalten bei Deaktivierung (Daten bleiben erhalten)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Mindestens ein Sensor ist am System konfiguriert mit gespeicherten Messwerten

**Testschritte**:
1. Nutzer navigiert zu Kontoeinstellungen → Tab "Integrationen"
2. Nutzer setzt den Toggle "Smart Home Funktionen aktivieren" auf AUS
3. Nutzer navigiert zur Standort-Detailseite, an der ein Sensor konfiguriert war
4. Nutzer setzt den Toggle in Kontoeinstellungen wieder auf EIN
5. Nutzer navigiert erneut zur Standort-Detailseite

**Erwartete Ergebnisse**:
- Nach Schritt 2: Sensor-Sektion auf der Standort-Detailseite ist nicht mehr sichtbar
- Nach Schritt 4: Sensor-Sektion erscheint wieder
- Nach Schritt 5: Der zuvor konfigurierte Sensor ist unveraendert sichtbar mit all seinen Daten
- Es erscheint keine Meldung ueber Datenverlust

**Nachbedingungen**:
- `smart_home_enabled = true`; alle Sensor-Daten erhalten

**Tags**: [req-005, smart-home-toggle, data-retention, reactivation]

---

### TC-REQ-005-004: Smart-Home-Toggle im Onboarding-Wizard aktivieren

**Requirement**: REQ-005 §4b — Aktivierung im Onboarding-Wizard (Schritt 2)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer befindet sich im Onboarding-Wizard, Schritt 2 ("Smart Home & Sensorik")

**Testschritte**:
1. Nutzer sieht den Toggle "Ich nutze Smart-Home-Geräte oder Sensoren" (deaktiviert)
2. Nutzer aktiviert den Toggle
3. Ein Hinweistext erscheint: "Sensoren, Aktoren und Live-Messwerte werden im System verfügbar."
4. Nutzer schlieSst den Onboarding-Wizard ab (alle verbleibenden Schritte bestaetigend)
5. Nutzer betrachtet die Sidebar nach Onboarding-Abschluss

**Erwartete Ergebnisse**:
- Nach Schritt 3: Der Hinweistext "Sensoren, Aktoren und Live-Messwerte werden im System verfügbar." ist sichtbar
- Nach Schritt 5: Sensor-bezogene Menuepunkte sind in der Sidebar sichtbar
- `smart_home_enabled = true` wurde korrekt gesetzt

**Nachbedingungen**:
- Onboarding abgeschlossen; `smart_home_enabled = true`

**Tags**: [req-005, onboarding, smart-home-toggle, wizard-step-2]

---

### TC-REQ-005-005: Deaktivierter Smart-Home-Toggle blendet auch manuelle Messeingabe aus

**Requirement**: REQ-005 §4b — Manuelle Messwert-Eingabe entfaellt bei smart_home_enabled = false
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = false`
- Nutzer befindet sich auf einer Standort-Detailseite

**Testschritte**:
1. Nutzer navigiert zur Standort-Detailseite eines Standorts
2. Nutzer sucht nach Formularen oder Buttons zur Eingabe manueller Messwerte (Temperatur, Feuchte, EC, pH)

**Erwartete Ergebnisse**:
- Keine Formulare oder Buttons zur manuellen Messwert-Eingabe sind sichtbar
- Der Standort zeigt nur allgemeine Informationen, Pflanzen und Aufgaben

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, smart-home-disabled, manual-entry-hidden, site-detail]

---

## 2. HA-Verbindungskonfiguration (AccountSettings Tab "Integrationen")

### TC-REQ-005-006: HA-URL und Token konfigurieren (Happy Path)

**Requirement**: REQ-005 §4a — Aktivierungsbedingung, HA-Konfiguration
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Kein HA-Token ist bisher konfiguriert (`ha_token_set = false`)
- Eine Home-Assistant-Instanz ist im Netzwerk erreichbar

**Testschritte**:
1. Nutzer navigiert zu Kontoeinstellungen → Tab "Integrationen"
2. Der Abschnitt "Home Assistant Integration" ist sichtbar (weil `smart_home_enabled = true`)
3. Nutzer gibt in das Feld "Home Assistant URL" den Wert `http://homeassistant.local:8123` ein
4. Nutzer gibt in das Feld "Zugangs-Token" einen gueltigen HA Long-Lived Access Token ein
5. Nutzer klickt auf den Button "Verbindung testen"

**Erwartete Ergebnisse**:
- Schritt 5: Ein Ladeindikator erscheint auf dem Button "Verbindung testen"
- Nach kurzer Zeit erscheint die Erfolgsmeldung "Verbindung erfolgreich" (Snackbar oder Alert)
- Die HA-spezifischen Felder auf Sensor-Formularen sind nun verfuegbar (z.B. HA Entity-ID Feld)

**Nachbedingungen**:
- `ha_token_set = true`; HA-Integration aktiv

**Tags**: [req-005, ha-integration, connection-test, account-settings, tab-integrationen]

---

### TC-REQ-005-007: HA-Verbindungstest mit falscher URL schlaegt fehl

**Requirement**: REQ-005 §4a — HA-Optionalitaet, Verbindungstest
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Nutzer befindet sich auf AccountSettings → Tab "Integrationen"

**Testschritte**:
1. Nutzer gibt in "Home Assistant URL" eine nicht erreichbare URL ein, z.B. `http://nicht-erreichbar.local:8123`
2. Nutzer gibt einen beliebigen Token ein
3. Nutzer klickt auf "Verbindung testen"

**Erwartete Ergebnisse**:
- Ladeindikator erscheint kurz
- Eine Fehlermeldung "Verbindung fehlgeschlagen" erscheint (Snackbar oder Alert mit error-Typ)
- Der Status wird nicht als "verbunden" gespeichert

**Nachbedingungen**:
- `ha_token_set` bleibt unveraendert (nicht gesetzt oder vorheriger Wert)

**Tags**: [req-005, ha-integration, connection-test, error, unreachable-url]

---

### TC-REQ-005-008: HA-Konfiguration ist ausgeblendet wenn smart_home_enabled = false

**Requirement**: REQ-005 §4b — HA-Konfiguration nur sichtbar bei smart_home_enabled = true
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = false`
- Nutzer navigiert zu Kontoeinstellungen → Tab "Integrationen"

**Testschritte**:
1. Nutzer oeffnet Kontoeinstellungen
2. Nutzer klickt auf Tab "Integrationen"
3. Nutzer sucht nach dem Abschnitt "Home Assistant Integration" mit URL- und Token-Feldern

**Erwartete Ergebnisse**:
- Der Abschnitt "Home Assistant Integration" mit URL-Feld, Token-Feld und "Verbindung testen"-Button ist **nicht sichtbar**
- Nur der Toggle "Smart Home Funktionen aktivieren" und sein Hinweistext sind sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, ha-integration-hidden, smart-home-disabled, account-settings]

---

### TC-REQ-005-009: HA-spezifische Felder in Sensor-Formular ausgeblendet wenn ha_token_set = false

**Requirement**: REQ-005 §4a — UI-Visibility-Regel, ha_entity_id ausgeblendet ohne HA
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- HA-Token ist **nicht** konfiguriert (`ha_token_set = false`)
- Nutzer ist auf einer Standort-Detailseite mit mindestens einem konfigurierten Sensor

**Testschritte**:
1. Nutzer oeffnet den Dialog "Sensor hinzufuegen" auf der Standort-Detailseite
2. Nutzer sucht im Dialog nach dem Feld "HA Entity-ID" und dem HA-Sensor-Autocomplete

**Erwartete Ergebnisse**:
- Das Feld "HA Entity-ID" (i18n: `pages.sensors.haEntityId`) ist **nicht sichtbar** oder nicht vorhanden
- Das HA-Sensor-Autocomplete "HA-Sensor auswählen" ist **nicht sichtbar**
- Das Feld "MQTT-Topic" kann je nach Implementierung sichtbar sein

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, sensor-form, ha-entity-hidden, ha-not-configured, sensor-create-dialog]

---

## 3. Sensor-Anlage und -Verwaltung an Standorten

### TC-REQ-005-010: Sensor an Standort anlegen (Happy Path)

**Requirement**: REQ-005 §6 DoD — Manuelle Eingabe, Datenquellen-Kennzeichnung
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Nutzer ist auf der Detailseite eines Standorts (SiteDetailPage)
- Ein Standort mit mindestens einem Slot ist vorhanden

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Standorts
2. Nutzer sucht den Abschnitt "Sensoren" mit dem Button "Sensor hinzufügen"
3. Nutzer klickt auf "Sensor hinzufügen"
4. Der Dialog "Sensor hinzufügen" oeffnet sich
5. Nutzer gibt im Feld "Sensorname" den Wert `Temperatur Gewächshaus` ein
6. Nutzer waehlt im Dropdown "Messgröße" den Eintrag `Temperatur (°C)` aus
7. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Eine Erfolgsmeldung "Sensor erstellt" erscheint (Snackbar)
- Der Dialog schliesst sich
- In der Sensor-Tabelle des Standorts erscheint ein neuer Eintrag "Temperatur Gewächshaus" mit Messgröße "Temperatur (°C)"

**Nachbedingungen**:
- Sensor ist an den Standort gebunden; keine Messungen vorhanden

**Tags**: [req-005, sensor-create, site-detail, happy-path]

---

### TC-REQ-005-011: Sensor anlegen ohne Namen schlaegt fehl (Pflichtfeld)

**Requirement**: REQ-005 §3 SensorDefinition — name als Pflichtfeld (min_length=1)
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Nutzer hat den Dialog "Sensor hinzufügen" auf einer Standort-Detailseite geoeffnet

**Testschritte**:
1. Nutzer laesst das Feld "Sensorname" leer
2. Nutzer waehlt im Dropdown "Messgröße" einen Eintrag aus (z.B. `pH-Wert`)
3. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Der Dialog bleibt geoeffnet
- Am Feld "Sensorname" erscheint eine Validierungsfehlermeldung (z.B. Rotrand oder Fehlertext unterhalb des Feldes)
- Kein Sensor wird angelegt

**Nachbedingungen**:
- Kein neuer Sensor in der Datenbank

**Tags**: [req-005, sensor-create, form-validation, required-field, name-empty]

---

### TC-REQ-005-012: Sensor mit HA-Entity-ID verknüpfen per Autocomplete

**Requirement**: REQ-005 §4a — HA-Integration, Entity-ID-Inferenz mit Nutzerbestaetigung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true` und `ha_token_set = true`
- HA-Instanz ist erreichbar und liefert Sensoren zurueck
- Dialog "Sensor hinzufügen" ist geoeffnet

**Testschritte**:
1. Im Dialog "Sensor hinzufügen" erscheint ein Autocomplete-Feld "HA-Sensor auswählen"
2. Nutzer klickt in das Autocomplete-Feld oder beginnt zu tippen (z.B. `growzelt`)
3. Eine Dropdown-Liste erscheint mit verfuegbaren HA-Sensoren (z.B. `sensor.growzelt_temperature`)
4. Jeder Eintrag zeigt den Friendly Name, die Entity-ID und den aktuellen Wert samt Einheit
5. Nutzer waehlt `sensor.growzelt_temperature (Growzelt Temperatur) — 24.5 °C` aus

**Erwartete Ergebnisse**:
- Das Feld "HA Entity-ID" wird automatisch mit `sensor.growzelt_temperature` befuellt
- Das Feld "Sensorname" wird mit dem Friendly Name `Growzelt Temperatur` vorausgefuellt
- Das Dropdown "Messgröße" wird auf `Temperatur (°C)` vorausgewaehlt (automatische Inferenz)
- Ein Chip neben dem Eintrag zeigt den inferierten Messgrössen-Typ an

**Nachbedingungen**:
- Felder sind vorausgefuellt; Nutzer kann sie noch aendern vor dem Speichern

**Tags**: [req-005, ha-entity-autocomplete, entity-inference, sensor-create-dialog]

---

### TC-REQ-005-013: Sensor bearbeiten (Messgrösse aendern)

**Requirement**: REQ-005 §3 SensorDefinition — Sensor-Bearbeitung
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Sensor `Temperatur Gewächshaus` mit Messgröße `Temperatur (°C)` existiert auf einem Standort

**Testschritte**:
1. Nutzer navigiert zur Standort-Detailseite mit dem Sensor
2. Nutzer klickt auf das Bearbeiten-Icon (Stift) in der Sensor-Tabellenzeile von "Temperatur Gewächshaus"
3. Der Dialog "Sensor bearbeiten" oeffnet sich mit vorausgefuellten Werten
4. Nutzer aendert das Dropdown "Messgröße" von `Temperatur (°C)` auf `Luftfeuchtigkeit (%)`
5. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Erfolgsmeldung "Gespeichert" erscheint (Snackbar)
- In der Sensor-Tabelle zeigt die Zeile jetzt `Luftfeuchtigkeit (%)` als Messgröße

**Nachbedingungen**:
- Sensor hat die neue Messgröße; bestehende Messdaten sind unveraendert

**Tags**: [req-005, sensor-edit, metric-type-change, site-detail]

---

### TC-REQ-005-014: Sensor deaktivieren per Toggle

**Requirement**: REQ-005 §3 SensorDefinition — is_active Toggle (nur im Edit-Modus sichtbar)
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein aktiver Sensor existiert auf einem Standort

**Testschritte**:
1. Nutzer klickt auf das Bearbeiten-Icon eines aktiven Sensors
2. Im Dialog "Sensor bearbeiten" ist der Toggle "Aktiv" sichtbar und eingeschaltet
3. Nutzer schaltet den Toggle "Aktiv" auf AUS
4. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung erscheint
- In der Sensor-Tabelle zeigt die Zeile fuer diesen Sensor ein deaktiviertes Status-Icon (z.B. ausgegraut oder mit "Inaktiv"-Indikator)

**Nachbedingungen**:
- Sensor ist deaktiviert; wird im Health-Check uebersprungen

**Tags**: [req-005, sensor-deactivate, is-active-toggle, edit-dialog]

---

### TC-REQ-005-015: Sensor loeschen mit Bestaetigungsdialog

**Requirement**: REQ-005 §3 Sensor-Node — Sensor-Loeschung
**Priority**: High
**Category**: Dialog
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Sensor existiert in der Sensor-Tabelle eines Standorts

**Testschritte**:
1. Nutzer klickt auf das Loeschen-Icon (Papierkorb) in der Sensor-Tabellenzeile
2. Ein Bestaetigungsdialog erscheint
3. Nutzer klickt auf "Loeschen" oder "Bestaetigen"

**Erwartete Ergebnisse**:
- Nach Schritt 2: Dialog-Text fragt "Sensor \"Temperatur Gewächshaus\" wirklich löschen?" (oder aequivalent)
- Nach Schritt 3: Dialog schliesst sich; Snackbar "Sensor gelöscht" erscheint
- Die Sensor-Tabellenzeile verschwindet aus der Liste

**Nachbedingungen**:
- Sensor ist aus dem System entfernt

**Tags**: [req-005, sensor-delete, confirm-dialog, site-detail]

---

### TC-REQ-005-016: Sensor an Location (Unterstandort) anlegen

**Requirement**: REQ-005 §4a — Sensor-Konfiguration per located_at Edge
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Eine Location (Unterstandort) existiert mit sichtbarer Sensor-Sektion (LocationDetailPage)

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Location (z.B. "Growzelt A")
2. Nutzer klickt auf den Button "Sensor hinzufügen" (data-testid: `add-sensor-button`)
3. Nutzer gibt Sensorname und Messgröße ein
4. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Erfolgsmeldung "Sensor erstellt"
- Sensor erscheint in der Sensor-Liste der Location

**Nachbedingungen**:
- Sensor ist an die Location gebunden

**Tags**: [req-005, sensor-create, location-detail, sublocation]

---

## 4. Sensor-Anlage an Tanks

### TC-REQ-005-017: Sensor an Tank anlegen (Happy Path)

**Requirement**: REQ-005 §2 Edge monitors_tank — Tank-Sensor-Binding
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Tank existiert in TankDetailPage
- Nutzer ist auf der TankDetailPage

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Tanks
2. Im Abschnitt "Sensoren" klickt Nutzer auf "Sensor hinzufügen" (data-testid: `tank-add-sensor-button`)
3. Dialog oeffnet sich; Standard-Messgröße ist `EC (mS/cm)` (da parentType = 'tank')
4. Nutzer gibt den Namen `EC-Sensor Haupttank` ein
5. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Snackbar "Sensor erstellt"
- Im Tank-Sensor-Bereich erscheint der neue Sensor

**Nachbedingungen**:
- Sensor ist mit dem Tank verknuepft; moegliche Befuellung zeigt HA-Live-Werte wenn HA aktiv

**Tags**: [req-005, sensor-create, tank-detail, tank-sensor, ec-sensor]

---

### TC-REQ-005-018: Tank-Sensor-Bereich ausgeblendet wenn smart_home_enabled = false

**Requirement**: REQ-005 §4b — TankDetailPage Sensor-Binding-Sektion ausgeblendet
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = false`

**Testschritte**:
1. Nutzer navigiert zur Detailseite eines Tanks
2. Nutzer sucht nach dem Sensor-Bereich und HA-Live-Werten

**Erwartete Ergebnisse**:
- Der Abschnitt "Sensoren" mit dem Button "Sensor hinzufügen" ist **nicht sichtbar**
- Keine Live-Werte-Anzeige oder HA/MQTT-Badges erscheinen
- Tank-Zustaende sind nur ueber das manuelle Tankzustands-Formular erfassbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, tank-sensor-hidden, smart-home-disabled, tank-detail]

---

## 5. Manuelle Messwert-Eingabe

### TC-REQ-005-019: Plausiblen manuellen Messwert eingeben (Happy Path)

**Requirement**: REQ-005 §3 ManualInputValidator, §6 DoD "Manuelle Eingabe mit Plausibilitaetspruefung"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Sensor vom Typ `pH-Wert` existiert an einem Standort
- Der vorherige pH-Wert war 6.2 (vor 1 Stunde)
- Ein Formular oder Button zur manuellen Messeingabe ist sichtbar

**Testschritte**:
1. Nutzer navigiert zur Messhistorie oder zum Sensor-Detail des pH-Sensors
2. Nutzer klickt auf "Messung hinzufuegen" oder ein aequivalentes Aktions-Element
3. Nutzer gibt den Wert `6.4` in das Wertfeld ein
4. Nutzer waehlt Konfidenz "Hoch" (z.B. kalibriertes Geraet verwendet)
5. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Kein Warnhinweis erscheint (Wert ist plausibel, keine starke Abweichung)
- Eine Erfolgsmeldung erscheint (Snackbar)
- Der neue Messwert erscheint in der Messhistorie mit Quelle "Manuell" (Datenquellen-Badge)
- Der Quality-Score der Eingabe spiegelt "Hoch" Konfidenz wider (ggf. als Qualitaetsindikator sichtbar)

**Nachbedingungen**:
- Manueller Messwert gespeichert mit source='manual'

**Tags**: [req-005, manual-entry, ph-value, plausibility-check, happy-path]

---

### TC-REQ-005-020: Unplausiblen manuellen Messwert eingeben loest Warnhinweis aus

**Requirement**: REQ-005 §3 ManualInputValidator — suspicious-Flag, confirm_required
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Sensor vom Typ `pH-Wert` existiert; der zuletzt gespeicherte Wert war pH 6.0 (vor 2 Stunden)
- Formular zur manuellen Messeingabe ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `4.5` in das pH-Wertfeld ein (Aenderung von -1.5 in 2h; überschreitet max_change_per_hour * hours = 0.5 * 2 = 1.0)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Ein Warnhinweis erscheint im Formular: "Ungewöhnlich starke Änderung — bitte bestätigen" (oder aequivalent)
- Ein Bestaetigungsschritt ist erforderlich (zusaetzlicher Klick oder Dialog)
- Ohne Bestaetigung wird der Wert nicht gespeichert

**Nachbedingungen**:
- Wert wird nur nach expliziter Bestaetigung gespeichert

**Tags**: [req-005, manual-entry, plausibility-warning, confirm-required, suspicious-change]

---

### TC-REQ-005-021: Physikalisch unmoeglichen Wert eingeben wird abgewiesen

**Requirement**: REQ-005 §3 SensorReading.VALID_RANGES — Bereichsvalidierung
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Formular zur manuellen Messeingabe fuer einen pH-Sensor ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `15` in das pH-Wertfeld ein (auSserhalb des gueltigen Bereichs 0–14)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "pH = 15 außerhalb physikalisch möglichem Bereich: 0–14" (oder aequivalent)
- Das Formular bleibt geoeffnet; der Wert wird nicht gespeichert
- Der Button "Speichern" ist deaktiviert oder die Meldung erscheint inline

**Nachbedingungen**:
- Kein Messwert gespeichert

**Tags**: [req-005, manual-entry, range-validation, ph-out-of-range, critical-error]

---

### TC-REQ-005-022: Grenzbereichswert loest Warnung (nicht Fehler) aus

**Requirement**: REQ-005 §3 SensorReading.validate_plausibility — warning_margin (10% des Bereichs)
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Formular zur manuellen Messeingabe fuer einen EC-Sensor ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `14.2` in das EC-Feld ein (nahe Grenzbereich: EC-max=15, warning_margin=1.5)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Ein Warnhinweis erscheint: "ec nahe Grenzbereich — bitte visuell bestätigen" (oder aequivalent)
- Der Wert kann dennoch gespeichert werden (Warnung, kein Fehler)
- Eine Bestaetigung kann erforderlich sein

**Nachbedingungen**:
- Wert wird mit Warnung gespeichert

**Tags**: [req-005, manual-entry, warning-margin, boundary-value, ec-near-limit]

---

### TC-REQ-005-023: Datenquellen-Badge zeigt "Manuell" vs. "Home Assistant"

**Requirement**: REQ-005 §6 DoD — "Datenquellen-Kennzeichnung: UI zeigt deutlich Auto vs. Manual"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = true` und `ha_token_set = true`
- Ein Sensor hat sowohl automatische (ha_auto) als auch manuelle (manual) Messungen in der Historie

**Testschritte**:
1. Nutzer navigiert zur Messhistorie eines Sensors
2. Nutzer betrachtet die Eintraege in der Liste

**Erwartete Ergebnisse**:
- Automatisch erfasste Werte zeigen das Label "Home Assistant" (i18n: `pages.tanks.sourceHaAuto`)
- Manuell erfasste Werte zeigen das Label "Manuell" (i18n: `pages.tanks.sourceManual`)
- Die beiden Quellen sind visuell klar unterscheidbar (z.B. verschiedenfarbige Badges)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, data-provenance, source-badge, manual-vs-auto, observation-history]

---

## 6. Sensor-Health-Monitoring und automatische Task-Generierung

### TC-REQ-005-024: Sensor-Status "Offline" wird im UI angezeigt

**Requirement**: REQ-005 §3 SensorHealth — status: 'offline', §6 DoD Sensor-Health-Monitoring
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Temperatur-Sensor ist seit mehr als 2 Stunden ohne Messung (ueberschreitet PARAMETER_WARNING_HOURS['temp'] = 2h)

**Testschritte**:
1. Nutzer navigiert zur Standort-Detailseite mit dem betroffenen Sensor
2. Nutzer betrachtet die Sensor-Tabelle

**Erwartete Ergebnisse**:
- In der Sensor-Tabellenzeile des betroffenen Sensors ist ein Status-Indikator sichtbar (z.B. Chip "Offline" oder rotes Icon)
- Der Status ist eindeutig von einem aktiven Online-Sensor unterscheidbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, sensor-health, offline-status, sensor-table, warning-indicator]

---

### TC-REQ-005-025: Automatischer Task bei Sensor-Ausfall > 24h

**Requirement**: REQ-005 §6 DoD — "Auto-Task-Generation: Manual-Measurement-Task bei Ausfall >24h", Szenario 2
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Ein Temperatur-Sensor ist seit mehr als 24 Stunden ohne Messung
- Der stündliche Health-Check hat den Ausfall erkannt
- Nutzer navigiert zur Aufgabenliste (Aufgaben-Seite)

**Testschritte**:
1. Nutzer navigiert zur Aufgabenliste
2. Nutzer sucht nach einer neuen Aufgabe mit Kategorie "Manuelle Messung"

**Erwartete Ergebnisse**:
- Eine Aufgabe "Manuelle Temperatur Messung" (oder "Manual temp Messung erforderlich") ist in der Liste sichtbar
- Die Aufgabe hat hohe Prioritaet (Kennzeichnung als "Hoch" oder rotes Label)
- Das Faelligkeitsdatum ist der heutige Tag
- Die Aufgabenbeschreibung erwaehnt den ausgefallenen Sensor und die Dauer des Ausfalls

**Nachbedingungen**:
- Task ist in der Aufgabenliste sichtbar und kann abgearbeitet werden

**Tags**: [req-005, sensor-offline, auto-task-generation, manual-measurement-task, task-priority-high]

---

### TC-REQ-005-026: Kein doppelter Task wird generiert wenn bereits einer existiert

**Requirement**: REQ-005 §2 AQL Sensor-Health-Check — FILTER LENGTH(existing_tasks) == 0
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Ein Sensor ist seit >24h offline
- Eine Aufgabe "Manuelle Temperatur Messung" (pending) existiert bereits fuer diesen Sensor

**Testschritte**:
1. Nutzer navigiert zur Aufgabenliste
2. Nutzer zaehlt die Aufgaben vom Typ "Manuelle Temperatur Messung" fuer den betroffenen Standort

**Erwartete Ergebnisse**:
- Genau eine (nicht mehrere) Aufgabe "Manuelle Temperatur Messung" fuer diesen Sensor/Standort ist sichtbar
- Kein zweiter, duplizierter Eintrag erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, no-duplicate-task, idempotent-task-generation, sensor-offline]

---

## 7. Kalibrierungs-Workflow

### TC-REQ-005-027: 1-Point Kalibrierung fuer pH-Sensor durchfuehren

**Requirement**: REQ-005 §6 DoD — "Kalibrierungs-Workflow: UI für 1-Point, 2-Point, Multi-Point Calibration"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein pH-Sensor existiert
- Eine Kalibrierungs-Funktion ist in der Sensor-Detailansicht oder einem Dialog zugaenglich

**Testschritte**:
1. Nutzer navigiert zur Kalibrierungs-Funktion des pH-Sensors (z.B. Button "Kalibrieren" in der Sensor-Detailansicht oder Maintenance-Dialog)
2. Nutzer waehlt "1-Punkt-Kalibrierung" (Single-Point)
3. Nutzer gibt den Referenzwert `7.0` ein (Sollwert der Pufferloesung)
4. Nutzer gibt den gemessenen Wert `7.2` ein (Ist-Anzeige des Sensors)
5. Nutzer klickt auf "Kalibrierung speichern"

**Erwartete Ergebnisse**:
- Erfolgsmeldung erscheint
- Die berechneten Kalibrierungsparameter werden angezeigt: Offset = `7.0 - 7.2 = -0.2`, Factor = `1.0`
- Der Sensor zeigt als letztes Kalibrierungsdatum das heutige Datum
- Ein Kalibrierungs-Erinnerungshinweis "Naechste Kalibrierung in 90 Tagen" ist ggf. sichtbar

**Nachbedingungen**:
- Kalibrierungs-Event ist gespeichert; Sensor-Offset aktualisiert

**Tags**: [req-005, calibration, single-point, ph-sensor, calibration-offset]

---

### TC-REQ-005-028: 2-Point Kalibrierung fuer pH-Sensor (Szenario 5)

**Requirement**: REQ-005 §6 Szenario 5 — 2-Point-Kalibrierung mit pH 4.0 und 7.0 Pufferlösungen
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Dialog fuer 2-Punkt-Kalibrierung ist geoeffnet
- pH-Sensor zeigt 7.2 bei pH-7.0-Pufferloesung und 4.3 bei pH-4.0-Pufferloesung

**Testschritte**:
1. Nutzer waehlt "2-Punkt-Kalibrierung" (Two-Point)
2. Fuer Punkt 1: Nutzer gibt Referenz `7.0` und Messung `7.2` ein
3. Fuer Punkt 2: Nutzer gibt Referenz `4.0` und Messung `4.3` ein
4. Nutzer klickt auf "Kalibrierung speichern"

**Erwartete Ergebnisse**:
- Berechnete Parameter werden angezeigt oder bestaetigt:
  - Factor ≈ 1.034 (= (7.0-4.0) / (7.2-4.3))
  - Offset ≈ -0.445 (= 7.0 - 1.034 * 7.2)
- Kalibrierungs-Event mit `calibration_type='two_point'` wird gespeichert
- Sensor zeigt aktualisiertes Kalibrierungsdatum

**Nachbedingungen**:
- Sensor.calibration_offset ≈ -0.445, Sensor.calibration_factor ≈ 1.034

**Tags**: [req-005, calibration, two-point, ph-sensor, scenario-5]

---

### TC-REQ-005-029: Validierung: Anzahl Messwerte muss Referenzwerte entsprechen

**Requirement**: REQ-005 §3 CalibrationRecord — validate_value_count_match
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog fuer Multi-Punkt-Kalibrierung ist geoeffnet
- Nutzer hat 3 Referenzwerte eingegeben

**Testschritte**:
1. Nutzer gibt 3 Referenzwerte ein: `4.0`, `7.0`, `10.0`
2. Nutzer gibt nur 2 Messwerte ein: `4.2`, `7.1`
3. Nutzer klickt auf "Kalibrierung speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Anzahl Messwerte muss Referenzwerten entsprechen" (oder aequivalent)
- Das Formular bleibt geoeffnet
- Kein Kalibrierungs-Event wird gespeichert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, calibration, validation-error, value-count-mismatch, multi-point]

---

### TC-REQ-005-030: Kalibrierungs-Erinnerung nach 90 Tagen

**Requirement**: REQ-005 §6 DoD — "Kalibrierungs-Erinnerung: Alert bei >90 Tage seit letzter Kalibrierung"
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Ein pH-Sensor wurde zuletzt vor 95 Tagen kalibriert

**Testschritte**:
1. Nutzer navigiert zur Sensor-Liste oder Sensor-Detailansicht des betroffenen Sensors

**Erwartete Ergebnisse**:
- Ein Hinweis oder Badge "Kalibrierung überfällig" (OVERDUE) ist beim Sensor sichtbar
- Das letzte Kalibrierungsdatum ist angezeigt (vor 95 Tagen)
- Optional: Eine Aufgabe "Kalibrierung erforderlich" erscheint in der Aufgabenliste

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, calibration-reminder, overdue, 90-days, sensor-detail]

---

### TC-REQ-005-031: Kalibrierungsparameter auSserhalb vernuenftigem Bereich wird abgewiesen

**Requirement**: REQ-005 §3 SensorDefinition — validate_reasonable_calibration (factor: 0.5-2.0)
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Kalibrierungsdialog ist geoeffnet

**Testschritte**:
1. Nutzer gibt eine 1-Punkt-Kalibrierung ein, die zu einem Factor von `3.5` fuehren wuerde (weit ausserhalb 0.5-2.0)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Fehlermeldung erscheint: "Calibration factor außerhalb vernünftigem Bereich (0.5–2.0)" (oder aequivalent)
- Das Formular bleibt geoeffnet

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, calibration, validation-error, factor-out-of-range]

---

## 8. Sensor-Health und Live-Status im Dashboard / Tank

### TC-REQ-005-032: Live-Status-Badge in TankDetailPage (HA-Live vs. Veraltet vs. Offline)

**Requirement**: REQ-005 §6 DoD — Datenquellen-Kennzeichnung; i18n freshLive, freshRecent, freshStale, freshOffline
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = true` und `ha_token_set = true`
- Ein Tank mit HA-Sensor (EC) existiert

**Testschritte**:
1. Nutzer navigiert zur Tank-Detailseite
2. Nutzer klickt auf "Live abrufen" (i18n: `pages.tanks.liveQuery`) oder wartet auf automatisches Laden

**Erwartete Ergebnisse**:
- Live-Werte werden mit einem Badge angezeigt:
  - Aktuell (< 5 Min): "Aktuell" (i18n: `pages.tanks.freshLive`)
  - Kurzlich: "Vor X Min" (i18n: `pages.tanks.freshRecent`)
  - Veraltet: "Veraltet" (i18n: `pages.tanks.freshStale`)
  - Kein Signal: "Offline" (i18n: `pages.tanks.freshOffline`)
- Die Quelle "HA Live" (i18n: `pages.tanks.sourceHaLive`) ist sichtbar wenn Daten von HA kommen

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, live-status, freshness-badge, tank-detail, ha-live, source-badge]

---

### TC-REQ-005-033: "Messung uebernehmen"-Button nimmt HA-Live-Wert als manuelle Messung

**Requirement**: REQ-005 §4a — Live-EC-Anzeige, automatische EC-Uebernahme (bei smart_home_enabled = true)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Nutzer hat `smart_home_enabled = true` und `ha_token_set = true`
- Tank-Detailseite zeigt einen Live-EC-Wert von 1.8 mS/cm von HA

**Testschritte**:
1. Nutzer betrachtet den Live-Wert-Bereich auf der Tank-Detailseite
2. Nutzer klickt auf "Messung übernehmen" (i18n: `pages.tanks.adoptReading`)

**Erwartete Ergebnisse**:
- Snackbar-Meldung "Messung übernommen" (i18n: `pages.tanks.adopted`) erscheint
- Der uebernommene Wert erscheint in der Messhistorie des Tanks mit Quellenangabe

**Nachbedingungen**:
- Messwert ist als Observation gespeichert

**Tags**: [req-005, adopt-reading, ha-live-to-manual, tank-detail, live-ec]

---

### TC-REQ-005-034: Kein HA konfiguriert — Info-Hinweis in TankDetailPage

**Requirement**: REQ-005 §4a — Backend-Verhalten ohne HA; i18n noHaConfigured
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`, aber `ha_token_set = false`
- Nutzer navigiert zur Tank-Detailseite

**Testschritte**:
1. Nutzer betrachtet den Live-Werte-Bereich des Tanks

**Erwartete Ergebnisse**:
- Ein Info-Hinweis erscheint: "Home Assistant nicht konfiguriert" (i18n: `pages.tanks.noHaConfigured`)
- Kein Live-Werte-Panel mit HA-Daten ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, ha-not-configured, tank-detail, info-message, graceful-degradation]

---

## 9. Anomalie-Erkennung und Interpolation

### TC-REQ-005-035: Statistischer Ausreisser wird im Verlaufs-Chart markiert

**Requirement**: REQ-005 §6 DoD — "Anomalie-Erkennung: Statistische Ausreißer-Erkennung (Z-Score)", Szenario 7
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Ein Sensor hat eine 7-taetige Messhistorie: Mittelwert 55%, Stddev 3%
- Ein neuer Wert von 75% wurde gespeichert (Z-Score = 6.67, weit ueber 3.0)

**Testschritte**:
1. Nutzer navigiert zur Verlaufsansicht / Chart des betroffenen Sensors
2. Nutzer betrachtet den Datenpunkt fuer den Ausreisserwert

**Erwartete Ergebnisse**:
- Der Datenpunkt 75% ist im Chart visuell hervorgehoben (z.B. roter Marker, anderes Symbol, Ausrufungszeichen)
- Ein Tooltip oder Label zeigt: "Statistischer Ausreißer erkannt — Sensor prüfen" oder aequivalent
- Der Datenpunkt unterscheidet sich klar von normalen Datenpunkten

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, anomaly-detection, z-score, outlier-marker, chart, scenario-7]

---

### TC-REQ-005-036: Interpolierte Werte erscheinen als gestrichelte Linie im Chart

**Requirement**: REQ-005 §6 Szenario 6 — Interpolation, UI zeigt gestrichelte Linie
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Ein EC-Sensor hat eine Datenlücke von 10:00 bis 12:00 Uhr (2h Ausfall)
- Interpolierte Werte wurden fuer 11:00 Uhr berechnet (source='interpolated')

**Testschritte**:
1. Nutzer navigiert zum Verlaufs-Chart des betroffenen EC-Sensors
2. Nutzer betrachtet den Zeitbereich 10:00–12:00

**Erwartete Ergebnisse**:
- Im Zeitbereich 10:00–12:00 erscheint eine **gestrichelte Linie** (nicht durchgezogen)
- Der interpolierte Wert um 11:00 (ca. 1.9 mS/cm) ist sichtbar
- Das visuelle Erscheinungsbild unterscheidet klar zwischen echten Messwerten (durchgezogene Linie) und interpolierten Werten (gestrichelt)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, interpolation, dashed-line, chart, data-gap, scenario-6]

---

### TC-REQ-005-037: Rate-of-Change-Warnung bei zu schneller Werteaenderung

**Requirement**: REQ-005 §3 SensorReadingValidator — Rate-of-Change-Validierung
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Formular zur manuellen Temperatureingabe ist geoeffnet
- Letzter Temperaturwert war 22°C (vor 1 Minute)

**Testschritte**:
1. Nutzer gibt den Wert `35°C` ein (Rate = 13°C/min, max erlaubt: 0.5°C/min)
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Eine Warnmeldung erscheint: "Unplausibel schnelle Änderung: X °C/min (Max: 0.5)" oder aequivalent
- Bestaetigung ist erforderlich um fortzufahren

**Nachbedingungen**:
- Wert wird nur nach expliziter Bestaetigung gespeichert

**Tags**: [req-005, rate-of-change, validation-warning, temperature, anomaly-detection]

---

## 10. Historische Trends und Chart-Visualisierung

### TC-REQ-005-038: 30-Tage-Verlauf eines Sensors anzeigen

**Requirement**: REQ-005 §6 DoD — "Historical Trending: 30 Tage Verlauf mit Chart-Visualisierung"
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Ein Sensor hat mindestens 30 Tage an Messdaten
- Nutzer navigiert zur Verlaufsansicht des Sensors

**Testschritte**:
1. Nutzer navigiert zur Messhistorie oder Verlaufs-Chart eines Sensors
2. Nutzer waehlt einen Zeitraum von 30 Tagen (oder dieser ist der Standard)

**Erwartete Ergebnisse**:
- Ein Linien- oder Flaechenchart mit mindestens 30 Tagen Messdaten wird angezeigt
- Die X-Achse zeigt Zeitstempel, die Y-Achse die Messwerte mit Einheit
- Min-, Max- und Durchschnittswerte sind lesbar (entweder im Chart oder als Kennzahlen darueber/darunter)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, historical-trending, 30-day-chart, visualization, time-series]

---

### TC-REQ-005-039: CSV-Export der Sensor-Messdaten

**Requirement**: REQ-005 §6 DoD — "Export-Funktion: CSV-Export fuer externe Analysen"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Ein Sensor hat Messdaten (mindestens 10 Eintraege)
- Nutzer ist auf der Sensor-Detailseite oder Verlaufsseite

**Testschritte**:
1. Nutzer sucht den "CSV exportieren"- oder "Export"-Button auf der Sensor-Verlaufsseite
2. Nutzer klickt auf den Export-Button

**Erwartete Ergebnisse**:
- Der Browser startet einen Datei-Download
- Die heruntergeladene Datei hat die Endung `.csv`
- Die CSV-Datei enthaelt mindestens die Spalten: Zeitstempel, Wert, Einheit, Quelle

**Nachbedingungen**:
- CSV-Datei ist auf dem Rechner des Nutzers gespeichert

**Tags**: [req-005, csv-export, sensor-history, download]

---

## 11. Multi-Sensor-Aggregation

### TC-REQ-005-040: Aggregierter Wert bei mehreren Sensoren pro Parameter/Location

**Requirement**: REQ-005 §6 DoD — "Multi-Sensor-Aggregation: Durchschnitt bei 2+ Sensoren", Szenario 4
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Drei Temperatursensoren sind an demselben Raum/Location konfiguriert:
  - Sensor A: 24.0°C, Quality 1.0
  - Sensor B: 24.5°C, Quality 0.9
  - Sensor C: 23.8°C, Quality 0.8
- Nutzer navigiert zur Location-Detailseite

**Testschritte**:
1. Nutzer betrachtet den Temperaturwert auf der Location-Detailseite

**Erwartete Ergebnisse**:
- Ein **aggregierter Wert** wird angezeigt, z.B. ca. 24.2°C (gewichteter Durchschnitt)
- Ein Konfidenz-Indikator zeigt "Hoch" (3 Sensoren vorhanden)
- Optional sind die Einzelwerte expandierbar oder in einer Untertabelle sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, multi-sensor-aggregation, weighted-average, quality-score, scenario-4]

---

## 12. Wetter-Integration fuer Freiland-Standorte

### TC-REQ-005-041: 3-Tages-Wettervorhersage-Widget im Dashboard fuer Outdoor-Site

**Requirement**: REQ-005 §1 Wetter-Integration (G-010) — Dashboard Wetter-Widget
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Ein Outdoor-Standort mit GPS-Koordinaten (`type='outdoor'`) ist konfiguriert
- Wetter-API-Daten wurden fuer diesen Standort abgerufen
- Nutzer navigiert zum Dashboard

**Testschritte**:
1. Nutzer oeffnet das Dashboard
2. Nutzer sucht ein Wetter-Widget fuer den Outdoor-Standort

**Erwartete Ergebnisse**:
- Ein Wetter-Widget zeigt die 3-Tages-Vorhersage fuer den Outdoor-Standort
- Sichtbare Informationen: Datum, min/max Temperatur, Niederschlag (mm), Windgeschwindigkeit
- Die Datenquelle (z.B. "DWD", "Open-Meteo") ist sichtbar oder im Tooltip erkennbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, weather-widget, dashboard, outdoor-site, 3-day-forecast, dwd]

---

### TC-REQ-005-042: Frostwarnung erscheint bei Nachttemperatur < 2°C

**Requirement**: REQ-005 §1 Wetter-Integration (G-010) — Szenario 8 Frostwarnung
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- Ein Outdoor-Standort `Gemüsebeet` mit GPS-Koordinaten und frostempfindlichen Pflanzen ist konfiguriert
- Wettervorhersage zeigt Nachttemperatur von 1°C (< 2°C Schwelle)
- Nutzer navigiert zur Aufgabenliste oder zum Dashboard

**Testschritte**:
1. Nutzer oeffnet die Aufgabenliste
2. Nutzer sucht nach einer Frostschutz-Aufgabe

**Erwartete Ergebnisse**:
- Eine Aufgabe "Frostschutz anbringen" mit hoher Prioritaet ist in der Liste sichtbar
- Die Aufgabenbeschreibung erwaehnt den betroffenen Standort und die Anzahl frostempfindlicher Pflanzen
- Optional: Eine Benachrichtigung "Frost heute Nacht! X frostempfindliche Pflanzen schützen!" ist im System sichtbar

**Nachbedingungen**:
- Aufgabe ist in der Aufgabenliste und kann abgearbeitet werden

**Tags**: [req-005, frost-warning, weather-integration, outdoor, task-generation, scenario-8]

---

### TC-REQ-005-043: Gieß-Erinnerung zeigt Regen-Hinweis bei >5mm Vorhersage

**Requirement**: REQ-005 §1 Wetter-Integration (G-010) — Szenario 9 Regen unterdrückt Gieß-Erinnerung
**Priority**: High
**Category**: Fehlermeldung / Detailansicht
**Preconditions**:
- Ein Outdoor-Standort `Balkonkasten` ist konfiguriert
- Eine Gieß-Erinnerung ist fuer morgen 08:00 Uhr faellig
- Wettervorhersage zeigt 12mm Regen fuer morgen

**Testschritte**:
1. Nutzer oeffnet die Aufgaben- oder Pflegeliste und findet die Gieß-Erinnerung
2. Nutzer betrachtet die Details der Erinnerung

**Erwartete Ergebnisse**:
- Die Gieß-Erinnerung ist **weiterhin sichtbar** (nicht automatisch geloescht)
- Ein Zusatzhinweis erscheint: "Es regnet — Gießen wahrscheinlich nicht nötig"
- Der Nutzer kann selbst entscheiden, ob er die Aufgabe abschliesst oder ueberspringt

**Nachbedingungen**:
- Gieß-Erinnerung ist unveraendert (nicht geloescht)

**Tags**: [req-005, rain-forecast, watering-reminder, hint-added, not-deleted, scenario-9, req-022-integration]

---

### TC-REQ-005-044: Indoor-Standort (type='indoor') zeigt kein Wetter-Widget

**Requirement**: REQ-005 §1 Wetter-Integration (G-010) — nur outdoor/greenhouse Standorte
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Ein Indoor-Standort (`type='indoor'`) ist konfiguriert
- Nutzer navigiert zur Detailseite des Indoor-Standorts

**Testschritte**:
1. Nutzer betrachtet die Detailseite eines Indoor-Standorts
2. Nutzer sucht nach einem Wetter-Widget oder Wettervorhersage-Element

**Erwartete Ergebnisse**:
- Kein Wetter-Widget und keine Wettervorhersage wird fuer den Indoor-Standort angezeigt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, weather-widget-hidden, indoor-site, outdoor-only]

---

## 13. Phasenabhaengige Alert-Profile

### TC-REQ-005-045: VPD-Alert-Schwellenwert aendert sich bei Phasenwechsel

**Requirement**: REQ-005 §3 PhaseAlertProfile — dynamische Schwellenwerte aus REQ-003 PhaseControlProfile
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Eine Pflanze durchlaeuft Phase "Vegetativ" mit VPD-Ziel 0.8–1.5 kPa
- Nutzer wechselt die Phase auf "Bluete" (VPD-Ziel 0.4–0.8 kPa)
- Nutzer navigiert zur Sensor-Uebersicht

**Testschritte**:
1. Nutzer vollzieht den Phasenwechsel auf der Pflanzen-Detailseite (Phase "Vegetativ" → "Bluete")
2. Nutzer navigiert zur VPD-Sensor-Anzeige oder zum Dashboard
3. Nutzer betrachtet die angezeigten Sollwert-Bereiche fuer VPD

**Erwartete Ergebnisse**:
- Die Anzeige des VPD-Sollbereichs hat sich von "0.8–1.5 kPa" auf "0.4–0.8 kPa" aktualisiert
- Ggf. erscheint ein Hinweis-Chip oder Farbaenderung im VPD-Widget wenn der aktuelle Messwert auSserhalb des neuen Sollbereichs liegt

**Nachbedingungen**:
- Phasenwechsel vollzogen; VPD-Zielwerte entsprechen Bluete-Phase

**Tags**: [req-005, phase-alert-profile, vpd-threshold, phase-transition, req-003-integration]

---

## 14. Grenzwert-Tests fuer Sensor-Validierung

### TC-REQ-005-046: EC-Wert am unteren Grenzwert (0.0 mS/cm) ist gueltig

**Requirement**: REQ-005 §3 SensorReading.VALID_RANGES — ec: (0, 15)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Formular zur manuellen EC-Messeingabe ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `0.0` ein
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Kein Fehler, nur ggf. Warnung im Grenzbereich (10% = 1.5 mS => 0.0 liegt im unteren Grenzbereich)
- Wert wird akzeptiert und gespeichert (Warnung-Hinweis moeglich)

**Nachbedingungen**:
- Wert gespeichert

**Tags**: [req-005, boundary-value, ec-lower-bound, valid-range]

---

### TC-REQ-005-047: Temperaturwert -11°C wird abgelehnt (auSserhalb Bereich -10 bis 50)

**Requirement**: REQ-005 §3 SensorReading.VALID_RANGES — temp: (-10, 50)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Formular zur manuellen Temperatureingabe ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `-11` ein
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Fehlermeldung: "temp = -11°C außerhalb physikalisch möglichem Bereich: -10–50°C" (oder aequivalent)
- Wert wird nicht gespeichert

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, boundary-value, temperature-out-of-range, valid-range]

---

### TC-REQ-005-048: PPFD-Wert 2499 µmol/m²/s ist gueltig (unter Maximum 2500)

**Requirement**: REQ-005 §3 SensorReading.VALID_RANGES — ppfd: (0, 2500)
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Formular zur manuellen PPFD-Eingabe ist geoeffnet

**Testschritte**:
1. Nutzer gibt den Wert `2499` ein
2. Nutzer klickt auf "Speichern"

**Erwartete Ergebnisse**:
- Warnung im Grenzbereich (250 Einheiten = 10% von 2500): "ppfd nahe Grenzbereich — bitte visuell bestätigen"
- Wert wird akzeptiert (Warnung, kein Fehler)

**Nachbedingungen**:
- Wert gespeichert

**Tags**: [req-005, boundary-value, ppfd-upper-bound, valid-range]

---

## 15. Navigation, Leerzustand und Accessibility

### TC-REQ-005-049: Leerzustand der Sensor-Liste auf neuem Standort

**Requirement**: REQ-005 — Sensor-Listensektion, Leerzustand
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein neuer Standort ohne Sensoren wurde angelegt

**Testschritte**:
1. Nutzer navigiert zur Detailseite des neuen Standorts
2. Nutzer betrachtet den Abschnitt "Sensoren"

**Erwartete Ergebnisse**:
- Eine Leerzustand-Meldung erscheint: "Keine Sensoren zugeordnet" (i18n: `pages.sensors.noSensors`)
- Ein Aktions-Button "Sensor hinzufügen" ist im Leerzustand sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, empty-state, sensor-list, no-sensors]

---

### TC-REQ-005-050: HA Entity-ID Feldformat-Validierung

**Requirement**: REQ-005 §3 SensorDefinition — ha_entity_id: muss mit 'sensor.' oder 'binary_sensor.' beginnen
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Dialog "Sensor hinzufügen" mit sichtbarem HA Entity-ID Feld ist geoeffnet (`ha_token_set = true`)

**Testschritte**:
1. Nutzer gibt in "HA Entity-ID" den Wert `switch.mein_sensor` ein (beginnt mit 'switch.', nicht 'sensor.')
2. Nutzer klickt auf "Erstellen"

**Erwartete Ergebnisse**:
- Eine Validierungsmeldung erscheint: "HA Entity muss mit 'sensor.' oder 'binary_sensor.' beginnen" (oder aequivalent)
- Sensor wird nicht angelegt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, ha-entity-id, format-validation, sensor-create-dialog]

---

### TC-REQ-005-051: Temperaturanzeige gemaess UserPreference (°C vs. °F)

**Requirement**: REQ-005 §1 — Temperatureinheit temperature_unit-Praeferenz (REQ-020 v1.2)
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer hat in den Einstellungen "°F" als Temperatureinheit ausgewaehlt
- Ein Temperatursensor hat einen aktuellen Messwert von 24.5°C gespeichert

**Testschritte**:
1. Nutzer navigiert zur Sensor-Anzeige oder dem Live-Werte-Bereich
2. Nutzer betrachtet den angezeigten Temperaturwert

**Erwartete Ergebnisse**:
- Der Wert wird in Fahrenheit angezeigt: ca. 76.1°F (Umrechnungsformel: 24.5 * 9/5 + 32)
- Die Einheit "°F" ist beim Wert sichtbar
- Interne Speicherung erfolgt weiterhin in °C (Konvertierung nur in der Anzeige)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, temperature-unit, fahrenheit, user-preference, req-020-integration]

---

## 16. Integration mit anderen REQ-Bereichen

### TC-REQ-005-052: Live-EC-Anzeige im Duengungsbereich bei smart_home_enabled = false ausgeblendet

**Requirement**: REQ-005 §4b — Duengung REQ-004: Live-EC-Anzeige ausgeblendet
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = false`

**Testschritte**:
1. Nutzer navigiert zu einem Nährstoffplan oder FeedingEvent-Formular (Duengungsbereich)
2. Nutzer sucht nach einer "Live-EC"-Anzeige oder einem Auto-Fill-Button

**Erwartete Ergebnisse**:
- Keine Live-EC-Anzeige und kein Auto-Fill-Button ist sichtbar
- EC-/pH-Werte muessen manuell eingetragen werden

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, live-ec-hidden, smart-home-disabled, req-004-integration]

---

### TC-REQ-005-053: Sensor-basierte Phasen-Transition-Trigger bei smart_home_enabled = false ausgeblendet

**Requirement**: REQ-005 §4b — REQ-013 Pflanzdurchlauf: sensor-basierte Phase-Transition-Trigger ausgeblendet
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer hat `smart_home_enabled = false`
- Nutzer navigiert zu einem aktiven Pflanzdurchlauf (PlantingRunDetailPage)

**Testschritte**:
1. Nutzer oeffnet den Phasenuebergang-Dialog einer aktiven Phase
2. Nutzer sucht nach Optionen wie "Automatisch bei VPD X kPa" oder "Sensor-Trigger"

**Erwartete Ergebnisse**:
- Sensor-basierte Trigger-Optionen sind nicht sichtbar
- Phasenuebergaenge werden nur manuell oder zeitbasiert angeboten

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, sensor-trigger-hidden, phase-transition, smart-home-disabled, req-013-integration]

---

## 17. Edge Cases und Fehlerzustaende

### TC-REQ-005-054: Sensor ohne vorherige Messung zeigt "CRITICAL" Status

**Requirement**: REQ-005 §3 SensorFallbackManager — check_sensor_health: "Sensor hat noch nie Daten geliefert"
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Sensor wurde angelegt, hat aber noch keine einzige Messung geliefert

**Testschritte**:
1. Nutzer navigiert zur Sensor-Liste des Standorts
2. Nutzer betrachtet den Status-Indikator des neuen Sensors

**Erwartete Ergebnisse**:
- Ein kritischer Status-Indikator ist sichtbar (z.B. "CRITICAL", rotes Icon, oder "Noch keine Daten")
- Die Sensor-Zeile ist visuell von aktiven Sensoren unterscheidbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, sensor-health, never-delivered-data, critical-status]

---

### TC-REQ-005-055: Parameterspezifische Ausfall-Schwellen (EC: 6h, Temp: 2h)

**Requirement**: REQ-005 §3 SensorFallbackManager.PARAMETER_WARNING_HOURS — temp: 2.0h, ec: 6.0h
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer hat `smart_home_enabled = true`
- Ein Temperatur-Sensor hat zuletzt vor 3 Stunden gemeldet (> 2h Schwelle)
- Ein EC-Sensor hat zuletzt vor 3 Stunden gemeldet (< 6h Schwelle)

**Testschritte**:
1. Nutzer navigiert zur Sensor-Liste des Standorts
2. Nutzer vergleicht die Status-Indikatoren des Temperatur-Sensors und des EC-Sensors

**Erwartete Ergebnisse**:
- Der Temperatur-Sensor zeigt einen **Warnstatus** (WARNING, da 3h > 2h-Schwelle)
- Der EC-Sensor zeigt **keinen** Warnstatus (OK, da 3h < 6h-Schwelle)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, parameter-specific-thresholds, temp-2h, ec-6h, sensor-health]

---

### TC-REQ-005-056: Sensor-Loeschung schlaegt ab wenn Bestaetigungsdialog abgebrochen wird

**Requirement**: REQ-005 — ConfirmDialog Abbruch bei Sensor-Loeschung
**Priority**: Low
**Category**: Dialog
**Preconditions**:
- Ein Sensor existiert; Loeschen-Icon wurde geklickt; Bestaetigungsdialog ist geoeffnet

**Testschritte**:
1. Bestaetigungsdialog ist geoeffnet ("Sensor löschen?")
2. Nutzer klickt auf "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schliesst sich
- Sensor ist weiterhin in der Sensor-Tabelle vorhanden (unveraendert)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, sensor-delete, cancel-dialog, abort]

---

### TC-REQ-005-057: Wetter-API-Daten bei Indoor-Standort werden nicht abgerufen

**Requirement**: REQ-005 §1 Wetter-Integration — nur Sites mit type: 'outdoor' oder type: 'greenhouse'
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Ein Indoor-Standort ohne GPS-Koordinaten ist konfiguriert

**Testschritte**:
1. Nutzer navigiert zur Standort-Detailseite eines Indoor-Standorts
2. Nutzer sucht nach Wetterdaten oder Wetterhinweisen

**Erwartete Ergebnisse**:
- Keine Wetterdaten sind sichtbar
- Kein Frostwarnung-Element oder Wetter-Widget erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, indoor-no-weather, weather-api, outdoor-only-restriction]

---

### TC-REQ-005-058: Measure-Tool-Empfehlung bei manueller pH-Eingabe sichtbar

**Requirement**: REQ-005 §3 ManualInputValidator.suggest_measurement_tool — pH-Empfehlung
**Priority**: Low
**Category**: Detailansicht
**Preconditions**:
- Formular zur manuellen pH-Messeingabe ist geoeffnet

**Testschritte**:
1. Nutzer betrachtet das Formular fuer die manuelle pH-Eingabe
2. Nutzer sucht nach Hilfetext oder Tooltips fuer empfohlene Messgeraete

**Erwartete Ergebnisse**:
- Ein Hinweistext oder Tooltip zeigt empfohlene Geraete fuer pH-Messung: z.B. "Apera pH20", "Bluelab pH Pen"
- Die empfohlene Genauigkeit (±0.1 pH) ist ggf. als Hilfetext sichtbar
- Ein Hinweis auf regelmaessige Kalibrierung mit pH 4.0 und 7.0 Pufferlösungen erscheint

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-005, measurement-tool-suggestion, ph-manual-entry, helper-text]

---

## Abdeckungs-Matrix

| Spezifikationsabschnitt | Abgedeckte Testfaelle |
|-------------------------|----------------------|
| §1 Business Case — Drei Betriebsmodi | TC-REQ-005-001, TC-REQ-005-004 |
| §1 Business Case — Ueberwachte Parameter (Klima, Substrat, Licht, Hydro) | TC-REQ-005-019 bis TC-REQ-005-022, TC-REQ-005-046 bis TC-REQ-005-048 |
| §1 Wetter-Integration (G-010) — Frostwarnung | TC-REQ-005-042 |
| §1 Wetter-Integration (G-010) — Regen-adaptive Giesserinnerung | TC-REQ-005-043 |
| §1 Wetter-Integration (G-010) — Wetter-Widget Dashboard | TC-REQ-005-041 |
| §1 Wetter-Integration (G-010) — Indoor ohne Wetter | TC-REQ-005-044, TC-REQ-005-057 |
| §3 SensorDefinition (CRUD) | TC-REQ-005-010 bis TC-REQ-005-016 |
| §3 SensorDefinition — ha_entity_id Validierung | TC-REQ-005-050 |
| §3 SensorReading — Plausibilitaetspruefung | TC-REQ-005-021, TC-REQ-005-022, TC-REQ-005-046 bis TC-REQ-005-048 |
| §3 ManualInputValidator — suspicious Flag | TC-REQ-005-020, TC-REQ-005-037 |
| §3 ManualInputValidator — Quality-Score | TC-REQ-005-019, TC-REQ-005-058 |
| §3 SensorFallbackManager — Health-Check | TC-REQ-005-024, TC-REQ-005-054, TC-REQ-005-055 |
| §3 SensorFallbackManager — Auto-Task | TC-REQ-005-025, TC-REQ-005-026 |
| §3 SensorFallbackManager — Interpolation | TC-REQ-005-036 |
| §3 CalibrationRecord — 1-Point | TC-REQ-005-027 |
| §3 CalibrationRecord — 2-Point | TC-REQ-005-028 |
| §3 CalibrationRecord — Validierung value_count | TC-REQ-005-029 |
| §3 CalibrationRecord — factor Bereich | TC-REQ-005-031 |
| §3 PhaseAlertProfile — dynamische Schwellenwerte | TC-REQ-005-045 |
| §4a HA-Optionalitaet — ha_token_set | TC-REQ-005-006 bis TC-REQ-005-009 |
| §4b Smart-Home-Gesamtdeaktivierung — Navigation | TC-REQ-005-001, TC-REQ-005-005 |
| §4b Smart-Home-Gesamtdeaktivierung — Aktivierung | TC-REQ-005-002, TC-REQ-005-003, TC-REQ-005-004 |
| §4b Smart-Home-Gesamtdeaktivierung — Tank | TC-REQ-005-018 |
| §4b Smart-Home-Gesamtdeaktivierung — Duengung | TC-REQ-005-052 |
| §4b Smart-Home-Gesamtdeaktivierung — Pflanzdurchlauf | TC-REQ-005-053 |
| §6 DoD — Kalibrierungs-Erinnerung 90 Tage | TC-REQ-005-030 |
| §6 DoD — Anomalie-Erkennung Z-Score | TC-REQ-005-035 |
| §6 DoD — Rate-of-Change | TC-REQ-005-037 |
| §6 DoD — Historical Trending 30 Tage | TC-REQ-005-038 |
| §6 DoD — CSV-Export | TC-REQ-005-039 |
| §6 DoD — Multi-Sensor-Aggregation | TC-REQ-005-040 |
| §6 DoD — Datenquellen-Kennzeichnung | TC-REQ-005-023, TC-REQ-005-032 |
| §6 DoD — Live-Status-Badge (freshness) | TC-REQ-005-032, TC-REQ-005-033 |
| §6 DoD — Messung uebernehmen (Adopt) | TC-REQ-005-033 |
| §6 Kein HA konfiguriert — Info-Hinweis | TC-REQ-005-034 |
| §6 Szenario 3 — Manuelle Eingabe mit Bestaetigung | TC-REQ-005-020 |
| §6 Szenario 4 — Multi-Sensor-Aggregation | TC-REQ-005-040 |
| §6 Szenario 5 — 2-Point Kalibrierung | TC-REQ-005-028 |
| §6 Szenario 6 — Interpolation gestrichelte Linie | TC-REQ-005-036 |
| §6 Szenario 7 — Anomalie-Erkennung | TC-REQ-005-035 |
| §6 Szenario 8 — Frostwarnung mit Task | TC-REQ-005-042 |
| §6 Szenario 9 — Regen-Hinweis bei Giesserinnerung | TC-REQ-005-043 |
| UI-Temperatureinheit (°C/°F) | TC-REQ-005-051 |
| Onboarding-Wizard Smart-Home-Toggle | TC-REQ-005-004 |
| Leerzustand Sensor-Liste | TC-REQ-005-049 |
| Sensor-Tank-Binding (monitors_tank Edge) | TC-REQ-005-017 |
| Sensor-Loeschung — Abbruch | TC-REQ-005-056 |
