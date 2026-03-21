---
req_id: REQ-010
title: Integriertes Schädlings- und Krankheitsmanagement (IPM)
category: Schädlingsmanagement
test_count: 58
coverage_areas:
  - Schädlings-Katalog (PestListPage — Erstellen, Suchen, Sortieren, Löschen)
  - Krankheits-Katalog (DiseaseListPage — Erstellen, Suchen, Sortieren, Löschen)
  - Behandlungs-Katalog (TreatmentListPage — Erstellen, Suchen, Sortieren, Löschen)
  - Karenzzeit-Status (KarenzStatusCard auf Pflanzen-Detailseite)
  - Formularvalidierung (Pflichtfelder, Enum-Werte, Grenzen)
  - Tabellen-Chips und visuelle Indikatoren
  - Leerer Zustand und Illustrationen
  - Mobile Card-Ansicht (unterhalb md-Breakpoint)
  - Tablet-Spaltenpriorität (hideBelowBreakpoint)
  - IPM-Hierarchie (kulturell > biologisch > chemisch)
  - Resistenzmanagement-Warnung (max. 3 Anwendungen / 90 Tage)
  - Behandlungs-Inkompatibilität (kontraindizierte Wirkstoffe)
  - Hermaphrodismus-Befund (isolated / spreading / critical)
  - Sofortmaßnahmen-Protokoll nach Schweregrad
  - Stress-Korrelation am Hermie-Befund
  - Cultivar-Hermie-Prone-Markierung
  - Hermie-Prone-Warnung bei neuem Pflanzdurchlauf
  - Bestäubungs-Check-Tasks nach Hermie-Befund
  - Navigationsstruktur Pflanzenschutz (/pflanzenschutz/pests, /diseases, /treatments)
generated: 2026-03-21
version: "1.0"
---

# TC-REQ-010: Integriertes Schädlings- und Krankheitsmanagement (IPM)

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-010 IPM-System v1.0**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-010 bildet das Fundament des integrierten Pflanzenschutzes: von Schädlings- und Krankheitskatalogen über Behandlungsoptionen bis hin zur Karenzzeit-Enforcement und Hermaphrodismus-Protokollen.

---

## 1. Schädlings-Katalog (PestListPage)

### TC-010-001: Schädlings-Listenansicht aufrufen — Ladevorgang und Tabellenstruktur

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog, Listenansicht-Filter
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt und Mitglied eines Tenants
- Mindestens 3 Schädlinge sind im System angelegt (z. B. Spinnmilbe, Blattlaus, Thripse)

**Testschritte**:
1. Nutzer navigiert zu `/t/{tenant-slug}/pflanzenschutz/pests`

**Erwartete Ergebnisse**:
- Seite lädt mit Seitentitel "Schädlinge"
- Während des Ladevorgangs ist eine Lade-Animation sichtbar
- Nach dem Laden erscheint eine Tabelle mit Spaltenüberschriften: "Wissenschaftlicher Name", "Gebräuchlicher Name", "Schädlingstyp", "Lebenszyklus (Tage)", "Erkennungsschwierigkeit"
- Jede Zeile zeigt die Daten eines Schädlings
- Der Button "Schädling erstellen" ist rechts oben sichtbar
- Ein beschreibender Einleitungstext ist unterhalb des Titels zu sehen

**Nachbedingungen**:
- Kein Status geändert (nur Lesevorgang)

**Tags**: [req-010, pest-list, listenansicht, navigation, pflanzenschutz]

---

### TC-010-002: Schädlings-Liste — Chip-Farben für Erkennungsschwierigkeit

**Requirement**: REQ-010 § 6 DoD — Listenansicht-Filter, Tablet-Spaltenprioritäten
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen
- Je ein Schädling mit Erkennungsschwierigkeit "easy", "medium", "hard" ist vorhanden

**Testschritte**:
1. Nutzer betrachtet die Tabellenspalte "Erkennungsschwierigkeit"

**Erwartete Ergebnisse**:
- Schädling mit Erkennungsschwierigkeit "Einfach" zeigt einen grünen Chip
- Schädling mit Erkennungsschwierigkeit "Mittel" zeigt einen orangenen (warning) Chip
- Schädling mit Erkennungsschwierigkeit "Schwierig" zeigt einen roten (error) Chip
- Die Chip-Beschriftungen lauten "Einfach", "Mittel" bzw. "Schwierig" (deutsche i18n-Werte)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, pest-list, chip-farben, erkennungsschwierigkeit, visuell]

---

### TC-010-003: Schädlings-Liste — Suche filtert in Echtzeit

**Requirement**: REQ-010 § 6 DoD — Listenansicht-Filter (URL-persistiert)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen mit mind. 5 Schädlingen
- Schädlinge mit unterschiedlichen Namen vorhanden (z. B. "Tetranychus urticae" / "Spinnmilbe", "Myzus persicae" / "Blattlaus")

**Testschritte**:
1. Nutzer klickt in das Suchfeld "Tabelle durchsuchen..."
2. Nutzer gibt "Spinnmilbe" ein

**Erwartete Ergebnisse**:
- Nach kurzer Verzögerung (Debounce ca. 300 ms) filtert die Tabelle auf Zeilen, die "Spinnmilbe" enthalten
- Nur passende Einträge sind sichtbar
- Die URL aktualisiert sich mit dem Suchbegriff als Query-Parameter
- Zeile mit "Blattlaus" ist nicht mehr sichtbar
- Der Paginierungstext zeigt die reduzierte Anzahl gefundener Einträge

**Nachbedingungen**:
- Suche ist in der URL gespeichert und bleibt bei Seitenreload erhalten

**Tags**: [req-010, pest-list, suche, filter, url-zustand, debounce]

---

### TC-010-004: Schädlings-Liste — Suche findet keinen Treffer (Leer-Zustand)

**Requirement**: REQ-010 § 6 DoD — Listenansicht
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen mit mind. 1 Schädling

**Testschritte**:
1. Nutzer gibt in das Suchfeld einen nicht vorhandenen Begriff ein, z. B. "XYZUnbekannt"

**Erwartete Ergebnisse**:
- Die Tabelle zeigt den Text "Keine Ergebnisse für Ihre Suche gefunden"
- Die Tabelle zeigt keine Datenzeilen
- Kein Absturz oder Fehlerdialog erscheint

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, pest-list, leer-zustand, suche-ohne-treffer]

---

### TC-010-005: Schädlings-Liste vollständig leer (Initialzustand ohne Daten)

**Requirement**: REQ-010 § 6 DoD — Listenansicht
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Kein Schädling ist im System angelegt

**Testschritte**:
1. Nutzer navigiert zu `/t/{tenant-slug}/pflanzenschutz/pests`

**Erwartete Ergebnisse**:
- Die Tabelle zeigt einen Leer-Zustand mit Illustration (Kami-IPM-Illustration)
- Ein Button "Schädling erstellen" ist im Leer-Zustand sichtbar
- Die Tabelle zeigt keine Datenzeilen und kein Suchfeld-Resultat-Text

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, pest-list, leer-zustand, illustration, empty-state]

---

### TC-010-006: Schädlings-Liste — Spalten auf Tablet ausgeblendet (hideBelowBreakpoint)

**Requirement**: REQ-010 § 6 DoD — Tablet-Spaltenprioritäten
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen
- Browser-Viewport ist kleiner als md-Breakpoint (< 900 px)
- Mindestens 1 Schädling mit gesetztem Lebenszyklus ist vorhanden

**Testschritte**:
1. Nutzer verkleinert das Browser-Fenster auf Tablet-Breite (< 900 px) oder öffnet die Seite auf einem Tablet-Gerät

**Erwartete Ergebnisse**:
- Die Spalten "Schädlingstyp" und "Lebenszyklus (Tage)" sind nicht mehr sichtbar
- Die Spalten "Wissenschaftlicher Name", "Gebräuchlicher Name" und "Erkennungsschwierigkeit" bleiben sichtbar
- Die Tabelle ist ohne horizontales Scrollen lesbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, pest-list, tablet, responsive, hide-below-breakpoint]

---

### TC-010-007: Schädlings-Liste — Mobile Card-Ansicht unterhalb sm-Breakpoint

**Requirement**: REQ-010 § 6 DoD — Mobile-Erfassung
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen
- Browser-Viewport ist kleiner als sm-Breakpoint (< 600 px)
- Mindestens 1 Schädling mit gesetztem Lebenszyklus ist vorhanden

**Testschritte**:
1. Nutzer öffnet die Seite auf einem Smartphone oder verkleinert den Viewport entsprechend

**Erwartete Ergebnisse**:
- Anstelle einer Tabelle werden Karten (MobileCard) pro Schädling angezeigt
- Jede Karte zeigt: Wissenschaftlicher Name als Titel, Gebräuchlicher Name als Untertitel
- Chips zeigen Schädlingstyp und Erkennungsschwierigkeit
- Lebenszyklus-Tage sind als Feld-Wert sichtbar (nur wenn gesetzt)
- Der "Schädling erstellen"-Button ist weiterhin zugänglich

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, pest-list, mobile, card-ansicht, responsive]

---

### TC-010-008: Schädling erstellen — Happy Path

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt auf `/t/{tenant-slug}/pflanzenschutz/pests`

**Testschritte**:
1. Nutzer klickt den Button "Schädling erstellen"
2. Der Erstell-Dialog öffnet sich mit Titel "Schädling erstellen"
3. Nutzer gibt im Feld "Wissenschaftlicher Name" ein: "Tetranychus urticae"
4. Nutzer gibt im Feld "Gebräuchlicher Name" ein: "Spinnmilbe"
5. Nutzer wählt im Dropdown "Schädlingstyp" den Wert "Milbe"
6. Nutzer gibt im Feld "Lebenszyklus (Tage)" den Wert "14" ein
7. Nutzer gibt im Feld "Opt. Temperatur min (°C)" den Wert "20" ein
8. Nutzer gibt im Feld "Opt. Temperatur max (°C)" den Wert "30" ein
9. Nutzer wählt im Dropdown "Erkennungsschwierigkeit" den Wert "Schwierig"
10. Nutzer klickt den Button "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Eine Erfolgs-Benachrichtigung erscheint (Snackbar mit "Erstellen" oder ähnlichem Bestätigungstext)
- Die Tabelle lädt neu und zeigt "Tetranychus urticae" / "Spinnmilbe" in der Liste
- Der neu erstellte Eintrag hat einen roten Chip "Schwierig" in der Spalte Erkennungsschwierigkeit

**Nachbedingungen**:
- Schädling "Tetranychus urticae" ist im System gespeichert

**Tags**: [req-010, pest-create, happy-path, dialog, formular]

---

### TC-010-009: Schädling erstellen — Pflichtfeld "Wissenschaftlicher Name" leer

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Schädlinge ist geöffnet

**Testschritte**:
1. Nutzer lässt das Feld "Wissenschaftlicher Name" leer
2. Nutzer füllt das Feld "Gebräuchlicher Name" aus: "Spinnmilbe"
3. Nutzer klickt den Button "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Unter dem Feld "Wissenschaftlicher Name" erscheint eine Fehlermeldung (Pflichtfeld-Validierung)
- Kein Eintrag wird angelegt

**Nachbedingungen**:
- Kein Schädling wurde erstellt

**Tags**: [req-010, pest-create, formvalidierung, pflichtfeld, wissenschaftlicher-name]

---

### TC-010-010: Schädling erstellen — Pflichtfeld "Gebräuchlicher Name" leer

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Schädlinge ist geöffnet

**Testschritte**:
1. Nutzer füllt das Feld "Wissenschaftlicher Name" aus: "Tetranychus urticae"
2. Nutzer lässt das Feld "Gebräuchlicher Name" leer
3. Nutzer klickt den Button "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Unter dem Feld "Gebräuchlicher Name" erscheint eine Fehlermeldung
- Kein Eintrag wird angelegt

**Nachbedingungen**:
- Kein Schädling wurde erstellt

**Tags**: [req-010, pest-create, formvalidierung, pflichtfeld, gebraeuchlicher-name]

---

### TC-010-011: Schädling erstellen — Dialog abbrechen verwirft Eingaben

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Medium
**Category**: Dialog
**Preconditions**:
- Erstell-Dialog für Schädlinge ist geöffnet mit bereits eingegebenen Daten

**Testschritte**:
1. Nutzer gibt im Feld "Wissenschaftlicher Name" ein: "TestOrganism"
2. Nutzer klickt den Button "Abbrechen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Die Schädlings-Liste zeigt keinen neuen Eintrag "TestOrganism"
- Die Tabelle bleibt unverändert

**Nachbedingungen**:
- Kein Schädling wurde erstellt

**Tags**: [req-010, pest-create, dialog, abbrechen, verwirft-eingaben]

---

### TC-010-012: Schädling erstellen — Lebenszyklus-Feld optionale Eingabe (null erlaubt)

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Low
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Schädlinge ist geöffnet

**Testschritte**:
1. Nutzer füllt "Wissenschaftlicher Name": "Frankliniella occidentalis"
2. Nutzer füllt "Gebräuchlicher Name": "Thripse"
3. Nutzer lässt das Feld "Lebenszyklus (Tage)" leer
4. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich erfolgreich
- Erfolgs-Benachrichtigung erscheint
- In der Tabelle erscheint der neue Eintrag; die Spalte "Lebenszyklus (Tage)" zeigt "—" (em-Dash)

**Nachbedingungen**:
- Schädling "Frankliniella occidentalis" ist gespeichert, Lebenszyklus-Feld ist leer

**Tags**: [req-010, pest-create, optional-feld, null, lifecycle-days]

---

## 2. Krankheits-Katalog (DiseaseListPage)

### TC-010-013: Krankheits-Listenansicht aufrufen

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog, Listenansicht-Filter
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 3 Krankheiten sind im System angelegt (z. B. Echter Mehltau, Botrytis, Wurzelfäule)

**Testschritte**:
1. Nutzer navigiert zu `/t/{tenant-slug}/pflanzenschutz/diseases`

**Erwartete Ergebnisse**:
- Seite lädt mit Seitentitel "Krankheiten"
- Tabelle zeigt Spalten: "Wissenschaftlicher Name", "Gebräuchlicher Name", "Erregertyp", "Inkubationszeit (Tage)"
- Ein beschreibender Einleitungstext ist unterhalb des Titels sichtbar
- Der Button "Krankheit erstellen" ist rechts oben sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, disease-list, listenansicht, navigation, pflanzenschutz]

---

### TC-010-014: Krankheits-Liste — Chip-Farben für Erregertyp

**Requirement**: REQ-010 § 6 DoD — Listenansicht-Filter, Tablet-Spaltenprioritäten
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/diseases` ist geladen
- Je eine Krankheit mit Erregertyp "fungal", "bacterial", "viral", "physiological" ist vorhanden

**Testschritte**:
1. Nutzer betrachtet die Tabellenspalte "Erregertyp"

**Erwartete Ergebnisse**:
- Erregertyp "Pilzlich" zeigt einen orangenen (warning) Chip
- Erregertyp "Bakteriell" zeigt einen roten (error) Chip
- Erregertyp "Viral" zeigt einen lila (secondary) Chip
- Erregertyp "Physiologisch" zeigt einen blauen (info) Chip
- Alle Chip-Beschriftungen sind in deutscher Sprache

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, disease-list, chip-farben, erregertyp, visuell]

---

### TC-010-015: Krankheits-Liste — Inkubationszeit-Spalte auf Tablet ausgeblendet

**Requirement**: REQ-010 § 6 DoD — Tablet-Spaltenprioritäten
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/diseases` ist geladen
- Viewport < md (< 900 px)

**Testschritte**:
1. Nutzer öffnet die Seite auf Tablet-Breite

**Erwartete Ergebnisse**:
- Die Spalte "Inkubationszeit (Tage)" ist nicht mehr sichtbar
- Die Spalten "Wissenschaftlicher Name", "Gebräuchlicher Name" und "Erregertyp" bleiben sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, disease-list, tablet, responsive, hide-below-breakpoint]

---

### TC-010-016: Krankheit erstellen — Happy Path mit Umweltauslösern und betroffenen Pflanzenteilen

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt auf `/t/{tenant-slug}/pflanzenschutz/diseases`

**Testschritte**:
1. Nutzer klickt "Krankheit erstellen"
2. Nutzer gibt "Wissenschaftlicher Name" ein: "Botrytis cinerea"
3. Nutzer gibt "Gebräuchlicher Name" ein: "Botrytis (Grauschimmel)"
4. Nutzer wählt "Erregertyp": "Pilzlich"
5. Nutzer gibt "Inkubationszeit (Tage)" ein: "3"
6. Nutzer tippt im Chip-Eingabefeld "Umweltauslöser" den Text "Hohe Luftfeuchtigkeit" und drückt Enter
7. Nutzer tippt "Temperaturen 15–20°C" und drückt Enter — ein zweiter Chip erscheint
8. Nutzer tippt im Chip-Eingabefeld "Betroffene Pflanzenteile" den Text "Blüte" und drückt Enter
9. Nutzer tippt "Blätter" und drückt Enter
10. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Benachrichtigung erscheint
- Die Tabelle zeigt "Botrytis cinerea" / "Botrytis (Grauschimmel)" als neuen Eintrag
- Erregertyp-Chip zeigt "Pilzlich" in orangener Farbe

**Nachbedingungen**:
- Krankheit "Botrytis cinerea" ist mit Umweltauslösern und betroffenen Pflanzenteilen gespeichert

**Tags**: [req-010, disease-create, happy-path, chip-input, umweltausloser, pflanzenteile]

---

### TC-010-017: Krankheit erstellen — Pflichtfelder leer (beide Namen fehlen)

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Krankheiten ist geöffnet

**Testschritte**:
1. Nutzer lässt "Wissenschaftlicher Name" und "Gebräuchlicher Name" leer
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Beide Pflichtfelder zeigen Validierungsfehler unterhalb der Felder
- Kein Eintrag wird angelegt

**Nachbedingungen**:
- Keine Krankheit wurde erstellt

**Tags**: [req-010, disease-create, formvalidierung, pflichtfelder]

---

### TC-010-018: Krankheit erstellen — Inkubationszeit 0 wird abgewiesen (min. 1)

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Medium
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Krankheiten ist geöffnet

**Testschritte**:
1. Nutzer füllt "Wissenschaftlicher Name": "Pseudoperonospora humuli"
2. Nutzer füllt "Gebräuchlicher Name": "Falscher Mehltau"
3. Nutzer gibt im Feld "Inkubationszeit (Tage)" den Wert "0" ein
4. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Unterhalb des Feldes "Inkubationszeit (Tage)" erscheint ein Validierungsfehler (Wert muss >= 1 sein)
- Kein Eintrag wird angelegt

**Nachbedingungen**:
- Keine Krankheit wurde erstellt

**Tags**: [req-010, disease-create, formvalidierung, grenzwert, inkubationszeit]

---

## 3. Behandlungs-Katalog (TreatmentListPage)

### TC-010-019: Behandlungs-Listenansicht aufrufen

**Requirement**: REQ-010 § 6 DoD — Listenansicht-Filter, IPM-Hierarchie
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt
- Mindestens 4 Behandlungen sind vorhanden (je eine pro Typ: kulturell, biologisch, chemisch, mechanisch)

**Testschritte**:
1. Nutzer navigiert zu `/t/{tenant-slug}/pflanzenschutz/treatments`

**Erwartete Ergebnisse**:
- Seite lädt mit Seitentitel "Behandlungen"
- Tabelle zeigt Spalten: "Bezeichnung", "Behandlungstyp", "Wirkstoff", "Karenzzeit (Tage)", "Anwendungsmethode"
- Ein beschreibender Einleitungstext ist sichtbar
- Der Button "Behandlung erstellen" ist rechts oben sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, treatment-list, listenansicht, navigation, ipm-hierarchie]

---

### TC-010-020: Behandlungs-Liste — Chip-Farben für Behandlungstyp (IPM-Hierarchie)

**Requirement**: REQ-010 § 6 DoD — IPM-Hierarchie (Kulturmaßnahme > Biologisch > Chemisch)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/treatments` ist geladen
- Je eine Behandlung aller vier Typen ist vorhanden

**Testschritte**:
1. Nutzer betrachtet die Spalte "Behandlungstyp" für jeden Eintrag

**Erwartete Ergebnisse**:
- Behandlungstyp "Chemisch" zeigt einen roten (error) Chip — visuell höchste Warnstufe
- Behandlungstyp "Biologisch" zeigt einen grünen (success) Chip — visuell sicherste Stufe
- Behandlungstyp "Kulturmaßnahme" zeigt einen blauen (info) Chip
- Behandlungstyp "Mechanisch" zeigt einen grauen (default) Chip
- Die Chip-Farbgebung spiegelt die IPM-Hierarchie wider (Chemisch = höchste Warnstufe)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, treatment-list, chip-farben, ipm-hierarchie, behandlungstyp]

---

### TC-010-021: Behandlungs-Liste — Karenzzeit-Chip nur bei safety_interval_days > 0

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/treatments` ist geladen
- Eine Behandlung mit Karenzzeit = 21 Tage ist vorhanden
- Eine Behandlung mit Karenzzeit = 0 ist vorhanden

**Testschritte**:
1. Nutzer betrachtet die Spalte "Karenzzeit (Tage)"

**Erwartete Ergebnisse**:
- Behandlung mit 21 Tagen Karenzzeit zeigt einen orangenen Chip "21 Tage"
- Behandlung ohne Karenzzeit (0 Tage) zeigt "—" (em-Dash, kein Chip)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, treatment-list, karenzzeit, chip, visuell]

---

### TC-010-022: Behandlungs-Liste — Wirkstoff- und Anwendungsmethode-Spalten auf Tablet ausgeblendet

**Requirement**: REQ-010 § 6 DoD — Tablet-Spaltenprioritäten
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/treatments` ist geladen
- Viewport < md (< 900 px)

**Testschritte**:
1. Nutzer öffnet die Seite auf Tablet-Breite

**Erwartete Ergebnisse**:
- Die Spalten "Wirkstoff" und "Anwendungsmethode" sind nicht mehr sichtbar
- Die Spalten "Bezeichnung", "Behandlungstyp" und "Karenzzeit (Tage)" bleiben sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, treatment-list, tablet, responsive, hide-below-breakpoint]

---

### TC-010-023: Behandlung erstellen — Biologische Behandlung (Happy Path)

**Requirement**: REQ-010 § 6 DoD — IPM-Hierarchie, Nützlings-Kalkulation
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt auf `/t/{tenant-slug}/pflanzenschutz/treatments`

**Testschritte**:
1. Nutzer klickt "Behandlung erstellen"
2. Nutzer gibt "Bezeichnung" ein: "Phytoseiulus persimilis (Raubmilbe)"
3. Nutzer wählt "Behandlungstyp": "Biologisch"
4. Nutzer gibt "Wirkstoff" ein: "Phytoseiulus persimilis"
5. Nutzer wählt "Anwendungsmethode": "Freilassung"
6. Nutzer lässt "Karenzzeit (Tage)" auf "0"
7. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Benachrichtigung erscheint
- In der Tabelle erscheint "Phytoseiulus persimilis (Raubmilbe)" mit grünem Chip "Biologisch"
- Karenzzeit-Spalte zeigt "—" (kein Chip, da 0 Tage)

**Nachbedingungen**:
- Biologische Behandlung ist im System gespeichert

**Tags**: [req-010, treatment-create, happy-path, biologisch, nützling]

---

### TC-010-024: Behandlung erstellen — Chemische Behandlung mit Karenzzeit

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Erstell-Dialog für Behandlungen ist geöffnet

**Testschritte**:
1. Nutzer gibt "Bezeichnung" ein: "Pyrethrin-Spray"
2. Nutzer wählt "Behandlungstyp": "Chemisch"
3. Nutzer gibt "Wirkstoff" ein: "Pyrethrin"
4. Nutzer wählt "Anwendungsmethode": "Sprühen"
5. Nutzer gibt "Karenzzeit (Tage)" ein: "21"
6. Nutzer gibt "Dosierung (ml/L)" ein: "2.5"
7. Nutzer tippt im Feld "Schutzausrüstung" den Text "Handschuhe" und drückt Enter
8. Nutzer tippt "Schutzbrille" und drückt Enter
9. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog schließt sich
- Erfolgs-Benachrichtigung erscheint
- In der Tabelle erscheint "Pyrethrin-Spray" mit rotem Chip "Chemisch"
- Karenzzeit-Spalte zeigt orangenen Chip "21 Tage"

**Nachbedingungen**:
- Chemische Behandlung mit 21 Tagen Karenzzeit ist im System gespeichert

**Tags**: [req-010, treatment-create, chemisch, karenzzeit, schutzausruestung]

---

### TC-010-025: Behandlung erstellen — Pflichtfeld "Bezeichnung" leer

**Requirement**: REQ-010 § 6 DoD — Behandlungs-Katalog
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Erstell-Dialog für Behandlungen ist geöffnet

**Testschritte**:
1. Nutzer lässt das Feld "Bezeichnung" leer
2. Nutzer wählt Behandlungstyp "Chemisch"
3. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Unterhalb des Feldes "Bezeichnung" erscheint eine Pflichtfeld-Fehlermeldung
- Kein Eintrag wird angelegt

**Nachbedingungen**:
- Keine Behandlung wurde erstellt

**Tags**: [req-010, treatment-create, formvalidierung, pflichtfeld, bezeichnung]

---

### TC-010-026: Behandlung erstellen — Mobile Card-Ansicht der Behandlungsliste

**Requirement**: REQ-010 § 6 DoD — Mobile-Erfassung
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/treatments` geladen, Viewport < sm (< 600 px)
- Mindestens 1 Behandlung mit Karenzzeit vorhanden

**Testschritte**:
1. Nutzer öffnet die Seite auf einem Smartphone

**Erwartete Ergebnisse**:
- Mobile Cards werden angezeigt
- Jede Karte zeigt Bezeichnung als Titel, Wirkstoff als Untertitel (wenn gesetzt)
- Behandlungstyp-Chip ist sichtbar
- Anwendungsmethode und Karenzzeit (wenn > 0) sind als Felder sichtbar
- "Behandlung erstellen"-Button ist erreichbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, treatment-list, mobile, card-ansicht, responsive]

---

## 4. Karenzzeit-Status (KarenzStatusCard)

### TC-010-027: Karenzzeit-Status — Keine aktive Karenzzeit (grüner Status)

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement (Szenario 2)
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Eine Pflanzeninstanz existiert und ist in der Detailansicht geöffnet
- Für diese Pflanze wurde keine chemische Behandlung durchgeführt oder die Karenzzeit ist bereits abgelaufen

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanze (z. B. `/t/{slug}/pflanzen/{plant-key}`)
2. Nutzer sucht die "Karenzzeit-Status"-Karte auf der Seite

**Erwartete Ergebnisse**:
- Die KarenzStatusCard ist sichtbar mit Titel "Karenzzeit-Status"
- Ein grünes Haken-Icon ist links neben dem Titel sichtbar
- Eine grüne Erfolgs-Meldung zeigt: "Keine aktiven Karenzzeiten. Ernte ist sicher möglich."
- Kein Warnungs-Chip oder Datumseintrag ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, karenz-status, gruen, ernte-sicher, detailansicht]

---

### TC-010-028: Karenzzeit-Status — Aktive Karenzzeit zeigt Warnung (orangener Status)

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement (Szenario 2)
**Priority**: Critical
**Category**: Detailansicht
**Preconditions**:
- Eine Pflanzeninstanz existiert mit einer aktiven Karenzzeit
- Pflanze wurde vor 10 Tagen mit "Pyrethrin-Spray" (Karenzzeit: 21 Tage) behandelt
- Karenzzeit ist noch nicht abgelaufen (11 verbleibende Tage)

**Testschritte**:
1. Nutzer navigiert zur Detailseite der betroffenen Pflanze
2. Nutzer sucht die "Karenzzeit-Status"-Karte

**Erwartete Ergebnisse**:
- Ein orangenes Warn-Icon ist links neben dem Kartentitel sichtbar
- Eine orangene Warnmeldung zeigt: "1 aktive Karenzzeit(en). Ernte ist derzeit nicht sicher."
- Ein Chip mit dem Behandlungsnamen oder Wirkstoff "Pyrethrin" ist sichtbar
- Neben dem Chip erscheint "Karenzzeit: 21 Tage"
- Das "Sicher ab"-Datum ist angegeben (Datum der Behandlung + 21 Tage)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, karenz-status, warnung, aktive-karenz, ernte-blockiert]

---

### TC-010-029: Karenzzeit-Status — Mehrere aktive Karenzzeiten

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Pflanze wurde mit 2 chemischen Mitteln mit unterschiedlichen Karenzzeiten behandelt
- Beide Karenzzeiten sind noch aktiv

**Testschritte**:
1. Nutzer öffnet die Detailseite der Pflanze
2. Nutzer betrachtet die "Karenzzeit-Status"-Karte

**Erwartete Ergebnisse**:
- Die Warnmeldung zeigt "2 aktive Karenzzeit(en). Ernte ist derzeit nicht sicher."
- Zwei separate Chips mit den jeweiligen Behandlungsnamen sind sichtbar
- Jeder Chip hat sein eigenes "Sicher ab"-Datum
- Das orange Warn-Icon ist weiterhin sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, karenz-status, mehrere-karenzzeiten, warnung]

---

## 5. Resistenzmanagement (UI-Warnung)

### TC-010-030: Resistenzwarnung bei Überschreitung der max. Anwendungen (Szenario 3)

**Requirement**: REQ-010 § 6 DoD — Resistenzmanagement, Testszenarien § Szenario 3
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Eine Pflanze wurde 3-mal mit demselben Wirkstoff (z. B. "Pyrethrin") innerhalb der letzten 90 Tage behandelt
- Der Nutzer versucht eine weitere Behandlung mit demselben Wirkstoff zuzuordnen

**Testschritte**:
1. Nutzer öffnet den Behandlungs-Zuordnungs-Dialog für die Pflanze (sofern vorhanden)
2. Nutzer wählt "Pyrethrin-Spray" als Behandlung aus
3. Nutzer klickt "Anwenden" oder "Speichern"

**Erwartete Ergebnisse**:
- Das System zeigt eine Warnmeldung: "RESISTENZWARNUNG: Wirkstoff-Rotation erforderlich"
- Die Anwendung wird blockiert oder eine deutliche Warnung wird vor dem Speichern angezeigt
- Alternativ wird vorgeschlagen, einen anderen Wirkstoff zu verwenden (z. B. Spinosad)

**Nachbedingungen**:
- Keine vierte Pyrethrin-Anwendung wird ohne explizite Nutzerbestätigung gespeichert

**Tags**: [req-010, resistenzmanagement, warnung, wirkstoff-rotation, max-anwendungen]

---

### TC-010-031: Wirkstoff-Rotation — Warnung markiert als NICHT EMPFOHLEN

**Requirement**: REQ-010 § 6 DoD — Resistenzmanagement (Szenario 3)
**Priority**: High
**Category**: Fehlermeldung
**Preconditions**:
- Pflanze wurde 3x mit "Pyrethroid"-Behandlung in 60 Tagen behandelt
- Erneuter Schädlingsbefall (Thripse) wurde dokumentiert

**Testschritte**:
1. Nutzer öffnet die Behandlungsempfehlungs-Ansicht für die Pflanze mit Thripse-Befall

**Erwartete Ergebnisse**:
- "Pyrethroid" oder Pyrethroid-basierte Behandlungen werden als "NICHT EMPFOHLEN — Resistenzrisiko" markiert
- Alternative Behandlungen (z. B. Spinosad-basierte) werden als bevorzugte Optionen angezeigt
- Die Rotations-Historie ist für den Nutzer einsehbar

**Nachbedingungen**:
- Kein Status geändert (nur Anzeigelogik)

**Tags**: [req-010, resistenzmanagement, nicht-empfohlen, thripse, spinosad]

---

## 6. Hermaphrodismus-Protokoll

### TC-010-032: Hermaphrodismus-Befund — Isolated (Einzelne Nanners, Szenario 4)

**Requirement**: REQ-010 § 6 DoD — Hermaphrodismus-Erkennung, Schweregrad, Sofortmaßnahmen-Protokoll
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- PlantInstance "White Widow #3" befindet sich in der Blütephase (Woche 5)
- Die Pflanze ist in der Inspektions-Ansicht geöffnet
- Letzte Inspektion war vor 2 Tagen ohne Befund

**Testschritte**:
1. Nutzer öffnet die Inspektions-Erfassung für "White Widow #3"
2. Nutzer aktiviert die Option "Hermaphrodismus erkannt" (Checkbox oder Toggle)
3. Nutzer wählt Befund-Typ: "Nanners"
4. Nutzer wählt Schweregrad: "Isolated (Einzelne Nanners)"
5. Nutzer gibt Ort auf der Pflanze ein: "Obere Cola"
6. Nutzer aktiviert NICHT "Pollen-Freisetzung wahrscheinlich"
7. Nutzer wählt Stress-Korrelation: "Lichtleck"
8. Nutzer wählt Sofortmaßnahme: "Nanners entfernt"
9. Nutzer speichert die Inspektion

**Erwartete Ergebnisse**:
- Die Inspektion wird gespeichert
- Das System zeigt das Sofortmaßnahmen-Protokoll für Schweregrad "Isolated":
  - "Nanners vorsichtig mit Pinzette entfernen (nicht schütteln!)"
  - "Betroffene Stelle mit Wasser besprühen (Pollen deaktivieren)"
  - "Foto-Dokumentation der Stelle"
- Das Protokoll enthält Follow-up-Hinweise: "Tägliche Kontrolle für 7 Tage", "Inspektionsintervall auf 1 Tag reduzieren"
- Stress-Ursache "Lichtleck" ist am Befund dokumentiert
- Die Pflanze verbleibt im Grow (keine Isolierungs- oder Entfernungsempfehlung)
- Empfehlung "Lichtleck beheben" wird angezeigt

**Nachbedingungen**:
- Hermaphrodismus-Befund ist gespeichert; Inspektionsintervall des Runs ist auf 1 Tag erhöht

**Tags**: [req-010, hermaphrodismus, isolated, nanners, sofortmassnahmen, stress-korrelation, lichtleck]

---

### TC-010-033: Hermaphrodismus-Befund — Spreading (Mehrere Stellen, Pflanze isolieren)

**Requirement**: REQ-010 § 6 DoD — Hermaphrodismus-Schweregrad, Sofortmaßnahmen-Protokoll
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- PlantInstance mit Hermaphrodismus-Befund, Schweregrad "Spreading"
- Nachbarpflanzen im selben Slot vorhanden

**Testschritte**:
1. Nutzer erfasst eine Inspektion mit Befund-Typ "Nanners", Schweregrad "Spreading"
2. Nutzer gibt mehrere Befund-Orte an
3. Nutzer speichert

**Erwartete Ergebnisse**:
- Das Sofortmaßnahmen-Protokoll für "Spreading" erscheint:
  - "Pflanze sofort isolieren (separater Raum/Zelt)"
  - "Alle sichtbaren Nanners/Pollensäcke entfernen"
  - "Nachbarpflanzen auf Pollenspuren untersuchen"
- Follow-up: "Tägliche Kontrolle der isolierten Pflanze", "Bestäubungs-Check aller Pflanzen im selben Raum"
- Empfehlung "Cultivar als hermie_prone markieren" wird angezeigt
- Die Pflanze erhält die Empfehlung "Isolieren" (plant_action: isolate)

**Nachbedingungen**:
- Befund ist gespeichert; Isolierungs-Empfehlung ist dokumentiert

**Tags**: [req-010, hermaphrodismus, spreading, isolieren, sofortmassnahmen, bestaeubungscheck]

---

### TC-010-034: Hermaphrodismus-Befund — Critical (Massive Bestäubungsgefahr, Szenario 5)

**Requirement**: REQ-010 § 6 DoD — Hermaphrodismus-Schweregrad, Sofortmaßnahmen-Protokoll, Bestäubungs-Check
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- PlantInstance "Bagseed #1" in Blütephase Woche 6
- 5 weitere Pflanzen im selben Location/Slot
- Mehrere vollständige Pollensäcke an verschiedenen Colas sichtbar

**Testschritte**:
1. Nutzer öffnet Inspektions-Erfassung für "Bagseed #1"
2. Nutzer wählt Befund-Typ: "Pollensäcke"
3. Nutzer wählt Schweregrad: "Critical (Massive Bestäubungsgefahr)"
4. Nutzer aktiviert: "Pollen-Freisetzung wahrscheinlich" = Ja
5. Nutzer speichert

**Erwartete Ergebnisse**:
- Das Sofortmaßnahmen-Protokoll für "Critical" erscheint mit roter/kritischer Hervorhebung:
  - "Pflanze SOFORT und VORSICHTIG aus dem Grow entfernen"
  - "Nicht schütteln — Pollen verbreitet sich über Luft"
  - "In Müllsack einpacken bevor Transport"
  - "Alle Nachbarpflanzen auf Bestäubung prüfen"
- Das System generiert automatisch Bestäubungs-Check-Tasks für alle 5 Nachbarpflanzen im selben Slot
- Die Tasks enthalten die Prüfpunkte: "Calyx-Schwellung ohne Trichom-Reife" und "Samenbildung"
- Der Cultivar "Bagseed #1" wird automatisch als hermie_prone markiert
- Eine Warnung für zukünftige Runs mit diesem Cultivar wird hinterlegt

**Nachbedingungen**:
- 5 Bestäubungs-Check-Tasks sind für Nachbarpflanzen erstellt
- Cultivar ist als hermie_prone markiert
- Hermie-Warnung für zukünftige Runs ist aktiv

**Tags**: [req-010, hermaphrodismus, critical, pollensaecke, sofortmassnahmen, bestaeubungscheck, hermie-prone, cross-ref-req-001]

---

### TC-010-035: Hermie-Prone-Cultivar-Warnung bei neuem Pflanzdurchlauf (Szenario 6)

**Requirement**: REQ-010 § 6 DoD — Genetische Markierung, Hermie-Prone-Warnung, Testszenarien § Szenario 6
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Cultivar "Bagseed #1" ist als hermie_prone markiert (1 critical-Vorfall)
- Nutzer möchte einen neuen Pflanzdurchlauf mit diesem Cultivar erstellen

**Testschritte**:
1. Nutzer navigiert zur Erstellung eines neuen Pflanzdurchlaufs
2. Nutzer wählt Cultivar "Bagseed #1" im entsprechenden Feld aus

**Erwartete Ergebnisse**:
- Eine Warnmeldung wird angezeigt, z. B.:
  "ACHTUNG: Cultivar hat 1 Hermaphrodismus-Vorfall (Schweregrad: critical). Erhöhte Überwachung ab Blütewoche 3 empfohlen."
- Die Warnung enthält konkrete Empfehlungen: "Stress-Faktoren minimieren (kein Lichtleck, Temperatur <28°C)"
- Der Nutzer kann den Durchlauf dennoch erstellen (Warnung ist nicht blockierend)
- Der Inspektions-Scheduler ist automatisch auf erhöhte Frequenz ab Blütephase eingestellt

**Nachbedingungen**:
- Neuer Pflanzdurchlauf wird mit hermie_prone-Warnung verknüpft

**Tags**: [req-010, hermie-prone, warnung, pflanzdurchlauf, cultivar, cross-ref-req-001, cross-ref-req-013]

---

### TC-010-036: Bestäubungs-Check nach Hermie-Befund — Calyx-Schwellung (Szenario 7)

**Requirement**: REQ-010 § 6 DoD — Bestäubungs-Check, Testszenarien § Szenario 7
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Ein Hermie-Befund (severity = "spreading") wurde vor 7 Tagen dokumentiert
- Pflanze ist isoliert
- 4 Nachbarpflanzen befinden sich weiter im Run
- Bestäubungs-Check-Task ist für eine Nachbarpflanze generiert worden

**Testschritte**:
1. Nutzer öffnet den Bestäubungs-Check-Task der Nachbarpflanze
2. Nutzer wählt Check-Typ: "Calyx-Squeeze"
3. Nutzer aktiviert: "Calyx-Schwellung ohne Trichom-Reife" = Ja
4. Nutzer speichert den Check

**Erwartete Ergebnisse**:
- Die Nachbarpflanze wird als "potenziell bestäubt" markiert
- Eine Warnmeldung erscheint: "Calyx-Schwellung ohne Trichom-Reife deutet auf Bestäubung hin"
- Das System empfiehlt eine Nachkontrolle in 7 Tagen (Samenentwicklung nach 2–3 Wochen sichtbar)
- Eine optionale Hinweismeldung zur Ernte-Qualitätsprognose wird angezeigt (Qualitätsprognose korrigiert nach unten)

**Nachbedingungen**:
- Bestäubungs-Check ist gespeichert; Nachkontroll-Task in 7 Tagen kann generiert werden

**Tags**: [req-010, bestaeubungscheck, calyx-squeeze, potenzielle-bestaeubung, qualitaetsprognose, szenario-7]

---

### TC-010-037: Hermaphrodismus-Befund — Stress-Korrelationen auswählen

**Requirement**: REQ-010 § 6 DoD — Stress-Korrelation
**Priority**: High
**Category**: Formvalidierung
**Preconditions**:
- Inspektions-Erfassung für eine Pflanze mit Hermaphrodismus-Befund ist offen

**Testschritte**:
1. Nutzer aktiviert "Hermaphrodismus erkannt"
2. Nutzer klickt auf das Dropdown "Stress-Korrelation"

**Erwartete Ergebnisse**:
- Das Dropdown bietet alle definierten Stress-Korrelationsoptionen an:
  - "Lichtleck"
  - "Hitzestress"
  - "Überdüngung"
  - "Training-Stress"
  - "Genetisch"
  - "Unbekannt"
- Nutzer kann genau eine Stress-Korrelation auswählen
- Die Auswahl wird am Befund gespeichert und ist in der Befunds-Detailansicht sichtbar

**Nachbedingungen**:
- Stress-Korrelation ist dokumentiert

**Tags**: [req-010, hermaphrodismus, stress-korrelation, dropdown, lichtleck, hitzestress]

---

### TC-010-038: Hermie-Historie eines Cultivars — Mehrere Runs übergreifend

**Requirement**: REQ-010 § 6 DoD — Hermie-Historie
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Cultivar "XYZ" hat über 3 verschiedene Runs insgesamt 2 Hermaphrodismus-Vorfälle (1x isolated, 1x spreading)
- Nutzer ist auf der Cultivar-Detailseite

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Cultivars (z. B. unter Stammdaten)
2. Nutzer sucht den Bereich "Hermaphrodismus-Historie" oder vergleichbares Tab/Abschnitt

**Erwartete Ergebnisse**:
- Eine Übersicht zeigt: Gesamtzahl Vorfälle (2), höchster Schweregrad ("spreading")
- Pro Vorfall sind sichtbar: Schweregrad, Stress-Korrelation, Datum des Vorfalls
- Wenn critical-Vorfälle vorhanden: "WARNUNG: Cultivar zeigt Hermaphrodismus" mit Empfehlung zur erhöhten Überwachung ab Blütewoche 3

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, hermie-historie, cultivar, mehrere-runs, analyse]

---

## 7. Früherkennung und Biologische Intervention (Szenario 1)

### TC-010-039: Nützlings-Empfehlung bei Spinnmilben-Befall (Szenario 1)

**Requirement**: REQ-010 § 6 DoD — Behandlungsempfehlung, Nützlings-Kalkulation, Testszenarien § Szenario 1
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- PlantInstance ist in der Blütephase, letzte Inspektion vor 4 Tagen
- Nützling "Phytoseiulus persimilis" mit Zielschädling "Spinnmilbe" ist im System hinterlegt
- Befalls-Fläche von 10 m² ist in der Pflanzenkonfiguration hinterlegt

**Testschritte**:
1. Nutzer erfasst eine neue Inspektion für die Pflanze
2. Nutzer gibt Befalls-Level: "Mittel" (medium) an
3. Nutzer wählt erkannten Schädling: "Spinnmilbe (Tetranychus urticae)"
4. Nutzer speichert die Inspektion

**Erwartete Ergebnisse**:
- Das System zeigt eine Behandlungsempfehlung an
- "Phytoseiulus persimilis" wird als empfohlene biologische Behandlung vorgeschlagen
- Die empfohlene Ausbringungsmenge wird berechnet und angezeigt (z. B. "500 Nützlinge für 10 m²")
- Eine Warnung wird angezeigt: "Keine chemische Behandlung verwenden — würde Nützlinge abtöten"
- Ein Follow-up-Inspektions-Vorschlag in 3 Tagen wird generiert

**Nachbedingungen**:
- Inspektion ist gespeichert; Nützlings-Empfehlung ist für den Nutzer sichtbar

**Tags**: [req-010, nützling, spinnmilbe, biologische-intervention, empfehlung, kalkulation, szenario-1]

---

### TC-010-040: Behandlungsempfehlung sortiert nach IPM-Hierarchie

**Requirement**: REQ-010 § 6 DoD — Behandlungsempfehlung (Kulturmaßnahme > Biologisch > Chemisch)
**Priority**: High
**Category**: Listenansicht
**Preconditions**:
- Schädlingsbefall ist dokumentiert
- Behandlungen aller vier Typen sind dem Schädling zugeordnet

**Testschritte**:
1. Nutzer öffnet die Behandlungsempfehlungs-Liste für den erkannten Befall

**Erwartete Ergebnisse**:
- Kulturmaßnahmen (blauer Chip) erscheinen zuerst in der Liste
- Biologische Behandlungen (grüner Chip) erscheinen als zweite Gruppe
- Chemische Behandlungen (roter Chip) erscheinen zuletzt
- Mechanische Behandlungen erscheinen zwischen biologisch und chemisch oder als eigenständige Gruppe
- Die Sortierung ist für den Nutzer als Priorisierung erkennbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, behandlungsempfehlung, ipm-hierarchie, sortierung, kulturmassnahme, biologisch, chemisch]

---

## 8. Behandlungs-Inkompatibilität

### TC-010-041: Warnung bei Chemie-Inkompatibilität (kontraindizierte Wirkstoffe)

**Requirement**: REQ-010 § 6 DoD — Chemie-Inkompatibilität
**Priority**: Critical
**Category**: Fehlermeldung
**Preconditions**:
- Behandlung A (Wirkstoff X) und Behandlung B (Wirkstoff Y) sind als kontraindiziert markiert
- Behandlung A wurde für die Pflanze bereits angewendet (kürzlich, innerhalb weniger Stunden/Tage)

**Testschritte**:
1. Nutzer wählt Behandlung B zur Anwendung für dieselbe Pflanze aus
2. Nutzer klickt "Anwenden" oder "Speichern"

**Erwartete Ergebnisse**:
- Das System zeigt eine Warn- oder Fehlermeldung: "Inkompatibilität erkannt: Wirkstoff Y ist nicht kompatibel mit Wirkstoff X"
- Die gleichzeitige Anwendung wird blockiert oder erfordert eine explizite Bestätigung
- Die Meldung nennt den konkreten Wirkstoff-Konflikt

**Nachbedingungen**:
- Keine inkompatible Behandlung wird ohne Warnung gespeichert

**Tags**: [req-010, inkompatibilitaet, chemie, kontraindiziert, warnung, blockierung]

---

## 9. Inspektions-Workflow und Scheduling

### TC-010-042: Inspektions-Task wird automatisch für Blütephase generiert

**Requirement**: REQ-010 § 6 DoD — Inspektions-Workflow (häufigere Inspektionen in Blüte)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Eine Pflanze tritt in die Blütephase ein (Phasenwechsel in REQ-003)
- Letzte Inspektion der Pflanze war vor mehr als 3 Tagen

**Testschritte**:
1. Nutzer wechselt die Phase einer Pflanze zur "Blütephase" (z. B. via Phasen-Steuerung)
2. Nutzer navigiert zur Aufgabenliste

**Erwartete Ergebnisse**:
- Ein neuer Inspektions-Task wurde automatisch generiert
- Der Task-Titel lautet sinngemäß "Inspektion: Schädlingskontrolle" oder ähnlich
- Der Task ist für ein nahes Datum fällig (innerhalb von 1–3 Tagen)
- Der Task ist der Kategorie "Pflanzenschutz" oder "Schädlingskontrolle" zugeordnet

**Nachbedingungen**:
- Inspektions-Task ist in der Aufgabenliste sichtbar

**Tags**: [req-010, inspektion, automatisch, blüte, aufgabe, cross-ref-req-006, cross-ref-req-003]

---

### TC-010-043: Inspektions-Frequenz erhöht sich bei hohem Befallsdruck

**Requirement**: REQ-010 § 6 DoD — Inspektions-Workflow, Befallshistorie
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Eine Pflanze hat eine Inspektion mit Befalls-Level "high" erhalten
- Basis-Inspektionsintervall ist auf 7 Tage konfiguriert

**Testschritte**:
1. Nutzer dokumentiert eine Inspektion mit Befalls-Level "Hoch" für die Pflanze
2. Nutzer öffnet die Aufgabenliste und sucht nach dem nächsten Inspektions-Task

**Erwartete Ergebnisse**:
- Der nächste Inspektions-Task ist für ca. 2–3 Tage (statt 7 Tage) fällig
- Die Frequenzerhöhung ist für den Nutzer durch den Fälligkeitstermin erkennbar

**Nachbedingungen**:
- Erhöhtes Inspektionsintervall ist aktiv

**Tags**: [req-010, inspektion, frequenz, befallsdruck, hoch, dynamisch]

---

## 10. Behandlungs-Tracking (Efficacy-Rating)

### TC-010-044: Efficacy-Rating nach Behandlung erfassen

**Requirement**: REQ-010 § 6 DoD — Behandlungs-Tracking (Wirksam/Teilweise/Unwirksam)
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Eine Behandlungsanwendung wurde für eine Pflanze gespeichert
- Nutzer ist auf der Behandlungsdetailseite oder der Pflanzenseite

**Testschritte**:
1. Nutzer öffnet die Behandlungsanwendung (TreatmentApplication) in der Detailansicht
2. Nutzer klickt auf "Wirksamkeit bewerten" oder entsprechendes Feld
3. Nutzer wählt "Wirksam" aus den Optionen (Wirksam / Teilweise wirksam / Unwirksam)
4. Nutzer speichert die Bewertung

**Erwartete Ergebnisse**:
- Die Bewertung wird gespeichert
- Eine Erfolgs-Benachrichtigung erscheint
- In der Behandlungsübersicht ist die Wirksamkeitsbewertung sichtbar

**Nachbedingungen**:
- Efficacy-Rating ist an der Behandlungsanwendung dokumentiert

**Tags**: [req-010, behandlungs-tracking, efficacy-rating, wirksam, bewertung]

---

## 11. Standort-Historie und Befalls-Analyse

### TC-010-045: Befallshistorie eines Slots über mehrere Zyklen

**Requirement**: REQ-010 § 6 DoD — Standort-Historie
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Ein Slot/Standort hat in den letzten 90 Tagen mehrere Schädlingsbefälle gehabt
- Mindestens 2 verschiedene Schädlinge wurden im selben Slot erfasst

**Testschritte**:
1. Nutzer navigiert zur Detailseite des Slots (unter Standorte)
2. Nutzer öffnet den Bereich "Befallshistorie" oder "IPM-Verlauf"

**Erwartete Ergebnisse**:
- Eine Übersicht der Schädlinge/Krankheiten im letzten Zeitraum ist sichtbar
- Jeder Schädling zeigt die Anzahl der Vorfälle
- Die Sortierung ist nach Häufigkeit absteigend
- Das Datum der letzten Inspektion und der Risikostatus sind erkennbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, standort-historie, befallshistorie, slot, zyklen, analyse]

---

### TC-010-046: Dashboard — Präventions-Score und letzter Inspektionsstatus

**Requirement**: REQ-010 § 6 DoD — Prävention-Score
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Nutzer ist eingeloggt und auf dem Dashboard
- Eine Pflanze wurde vor 5 Tagen zuletzt inspiziert (Befalls-Level: "Mittel")

**Testschritte**:
1. Nutzer navigiert zur Dashboard-Seite
2. Nutzer sucht den IPM/Pflanzenschutz-Widget oder -Bereich

**Erwartete Ergebnisse**:
- Das Dashboard zeigt einen Präventions-Indikator, z. B.: "Letzte Inspektion vor 5 Tagen, Risiko: Mittel"
- Der Risikoindikator ist visuell (Chip-Farbe oder Icon) erkennbar
- Ein Link oder Button führt zur Pflanzenschutz-Übersicht

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, dashboard, praeventions-score, inspektionsstatus, risiko]

---

## 12. Navigation und Routing

### TC-010-047: Navigation zwischen Pflanzenschutz-Unterseiten via Sidebar

**Requirement**: REQ-010 § 6 DoD — Navigation
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt auf einer beliebigen Seite

**Testschritte**:
1. Nutzer klickt in der Seitennavigation (Sidebar) auf "Pflanzenschutz"
2. Nutzer klickt auf "Schädlinge"
3. Nutzer klickt in der Sidebar auf "Krankheiten"
4. Nutzer klickt in der Sidebar auf "Behandlungen"

**Erwartete Ergebnisse**:
- Schritt 2: URL ändert sich zu `.../pflanzenschutz/pests`, PestListPage wird gerendert
- Schritt 3: URL ändert sich zu `.../pflanzenschutz/diseases`, DiseaseListPage wird gerendert
- Schritt 4: URL ändert sich zu `.../pflanzenschutz/treatments`, TreatmentListPage wird gerendert
- Kein Seitenfehler tritt auf, alle Seiten laden korrekt

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, navigation, sidebar, routing, pflanzenschutz]

---

### TC-010-048: Direktnavigation via URL zu Pflanzenschutz-Seiten

**Requirement**: REQ-010 § 6 DoD — Navigation
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer öffnet direkt die URL `/t/{tenant-slug}/pflanzenschutz/pests`
2. Nutzer öffnet direkt die URL `/t/{tenant-slug}/pflanzenschutz/diseases`
3. Nutzer öffnet direkt die URL `/t/{tenant-slug}/pflanzenschutz/treatments`

**Erwartete Ergebnisse**:
- Alle drei URLs laden korrekt die entsprechende Seite
- Kein 404-Fehler oder Login-Redirect erscheint (für eingeloggte Nutzer)
- Die Tabelleninhalte werden geladen

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, navigation, direktnavigation, url, deep-link]

---

## 13. Authentifizierung und Zugriffsrechte

### TC-010-049: Nicht eingeloggter Nutzer wird zu Login weitergeleitet

**Requirement**: REQ-010 § 4 — Authentifizierung & Autorisierung
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist nicht eingeloggt

**Testschritte**:
1. Nutzer öffnet direkt `/t/meingarten/pflanzenschutz/pests`

**Erwartete Ergebnisse**:
- Nutzer wird zur Login-Seite weitergeleitet
- Die Schädlingsliste ist nicht zugänglich
- Kein Datenleck ist erkennbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, auth, unauthenticated, redirect, sicherheit]

---

### TC-010-050: Globale Stammdaten (Pests/Diseases/Treatments) ohne Tenant-Einschränkung lesbar

**Requirement**: REQ-010 § 4 — Authentifizierung (Lesen ohne Tenant-Mitgliedschaft)
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist eingeloggt aber kein Mitglied des angefragten Tenants
- Alternativ: globale IPM-Stammdaten (Schädlinge, Krankheiten, Behandlungen) sind global sichtbar

**Testschritte**:
1. Nutzer navigiert zur globalen Pflanzenschutz-Übersicht (falls eine solche ohne Tenant-Kontext existiert)

**Erwartete Ergebnisse**:
- Schädlinge, Krankheiten und Behandlungen aus dem globalen Katalog sind lesbar
- Kein "Zugriff verweigert"-Fehler für Lesezugriff erscheint
- Schreib- und Löschfunktionen sind nur für berechtigte Nutzer sichtbar/aktiv

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, auth, globale-stammdaten, lesezugriff, tenant]

---

## 14. Wetter-Integration und Risiko-Score

### TC-010-051: Pilz-Risikowarnung bei hoher Luftfeuchtigkeit

**Requirement**: REQ-010 § 6 DoD — Wetter-Integration
**Priority**: Medium
**Category**: Zustandswechsel
**Preconditions**:
- Sensorwerte zeigen Luftfeuchtigkeit > 80 % für mehr als 12 Stunden
- Eine pilzanfällige Pflanze (z. B. in Blütephase) ist im System vorhanden

**Testschritte**:
1. Nutzer navigiert zur Pflanzendetailseite der pilzanfälligen Pflanze
2. Nutzer sucht nach IPM-Risikohinweisen oder Dashboard-Benachrichtigungen

**Erwartete Ergebnisse**:
- Eine Warnmeldung ist sichtbar, z. B.: "Hohes Mehltau-/Botrytis-Risiko: Luftfeuchtigkeit > 80%"
- Die Warnung empfiehlt Gegenmaßnahmen (Belüftung verbessern, VPD-Anpassung)
- Der Risiko-Score ist als visueller Indikator (Chip oder Alert) sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, wetter-integration, pilz, botrytis, luftfeuchtigkeit, risiko-score]

---

## 15. Fehlerzustände und Netzwerkfehler

### TC-010-052: Netzwerkfehler beim Laden der Schädlingsliste

**Requirement**: REQ-010 § 6 — Listenansicht
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Browser hat keine Netzwerkverbindung oder die API ist nicht erreichbar

**Testschritte**:
1. Nutzer navigiert zu `/t/{tenant-slug}/pflanzenschutz/pests` ohne Netzwerkverbindung

**Erwartete Ergebnisse**:
- Eine Fehlermeldung wird angezeigt (Snackbar oder Alert), z. B. "Netzwerkfehler..." oder "Serverfehler..."
- Die Tabelle zeigt keinen Inhalt (leerer Zustand)
- Kein nicht behandelter Fehler (White Screen) erscheint

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, netzwerkfehler, fehlerbehandlung, ladevorgang]

---

### TC-010-053: Serverfehler beim Erstellen eines Schädlings

**Requirement**: REQ-010 § 6 DoD — Pest/Disease-Katalog
**Priority**: Medium
**Category**: Fehlermeldung
**Preconditions**:
- Erstell-Dialog für Schädlinge ist geöffnet
- API gibt einen Serverfehler zurück (z. B. doppelter Name)

**Testschritte**:
1. Nutzer gibt einen wissenschaftlichen Namen ein, der bereits im System existiert
2. Nutzer klickt "Erstellen"

**Erwartete Ergebnisse**:
- Dialog bleibt geöffnet
- Eine Fehlermeldung erscheint (Snackbar oder inline): "Ein Eintrag mit diesem Namen existiert bereits." oder ähnlicher Fehler
- Kein Datenverlust — der Nutzer kann das Formular korrigieren

**Nachbedingungen**:
- Kein Duplikat wurde angelegt

**Tags**: [req-010, serverfehler, duplikat, fehlerbehandlung, dialog]

---

## 16. Tabellen-Sortierung

### TC-010-054: Schädlings-Liste nach wissenschaftlichem Namen sortieren

**Requirement**: REQ-010 § 6 DoD — Listenansicht
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/pests` ist geladen mit mind. 3 Schädlingen in nicht-alphabetischer Reihenfolge

**Testschritte**:
1. Nutzer klickt auf die Spaltenüberschrift "Wissenschaftlicher Name" (Standard-Sortierung: aufsteigend)
2. Nutzer klickt erneut auf die Spaltenüberschrift (Sortierung: absteigend)

**Erwartete Ergebnisse**:
- Nach erstem Klick: Einträge sind alphabetisch aufsteigend nach wissenschaftlichem Namen sortiert
- Nach zweitem Klick: Einträge sind alphabetisch absteigend sortiert
- Ein Sortier-Pfeil-Icon zeigt die aktuelle Sortierrichtung an
- Die URL-Parameter werden aktualisiert (URL-persistierte Tabellenzustände)

**Nachbedingungen**:
- Sortiereinstellung ist in URL gespeichert

**Tags**: [req-010, sortierung, tabelle, url-zustand, wissenschaftlicher-name]

---

### TC-010-055: Behandlungs-Liste Standard-Sortierung nach Name

**Requirement**: REQ-010 § 6 DoD — Listenansicht
**Priority**: Low
**Category**: Listenansicht
**Preconditions**:
- `/t/{tenant-slug}/pflanzenschutz/treatments` wird erstmalig ohne URL-Parameter geladen

**Testschritte**:
1. Nutzer navigiert zur Behandlungsliste

**Erwartete Ergebnisse**:
- Die Liste ist standardmäßig aufsteigend nach "Bezeichnung" sortiert
- Der Sortier-Pfeil bei "Bezeichnung" zeigt aufwärts

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-010, sortierung, behandlung, standard-sortierung, bezeichnung]

---

## 17. Cross-Referenz-Tests (Karenzzeit-Enforcement mit REQ-007)

### TC-010-056: Ernte-Task wird blockiert bei aktiver Karenzzeit (Szenario 2)

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement, Testszenarien § Szenario 2
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Pflanze wurde vor 10 Tagen mit Pestizid (Karenzzeit: 21 Tage) behandelt
- Nutzer versucht, einen Ernte-Task zu erstellen oder eine Ernte zu starten

**Testschritte**:
1. Nutzer navigiert zur Ernte-Sektion der Pflanze (REQ-007)
2. Nutzer klickt "Ernte erstellen" oder "Ernte starten"

**Erwartete Ergebnisse**:
- Das System blockiert die Ernte-Erstellung
- Eine Warnmeldung ist sichtbar: "Ernte nicht möglich: Aktive Karenzzeit. Sicher ab: [Datum]"
- Verbleibende Karenzzeit wird angezeigt (z. B. "Noch 11 Tage")
- Der "Ernte erstellen"-Button ist deaktiviert oder eine Sperrseite wird angezeigt
- Alternativtermin-Hinweis ist sichtbar (frühestmögliches Erntedatum)

**Nachbedingungen**:
- Keine Ernte wird angelegt, solange die Karenzzeit aktiv ist

**Tags**: [req-010, karenzzeit-enforcement, ernte-blockiert, szenario-2, cross-ref-req-007]

---

### TC-010-057: Karenzzeit abgelaufen — Ernte wieder möglich

**Requirement**: REQ-010 § 6 DoD — Karenzzeit-Enforcement (Szenario 2)
**Priority**: Critical
**Category**: Zustandswechsel
**Preconditions**:
- Pflanze wurde vor 25 Tagen mit Pestizid (Karenzzeit: 21 Tage) behandelt
- Karenzzeit ist damit abgelaufen
- KarenzStatusCard zeigt grünen Status

**Testschritte**:
1. Nutzer navigiert zur Pflanzendetailseite
2. Nutzer überprüft die KarenzStatusCard
3. Nutzer navigiert zur Ernte-Sektion und klickt "Ernte erstellen"

**Erwartete Ergebnisse**:
- KarenzStatusCard zeigt: "Keine aktiven Karenzzeiten. Ernte ist sicher möglich." (grüner Status)
- Der "Ernte erstellen"-Button ist aktiv (nicht deaktiviert)
- Die Ernte-Erstellung kann ohne Blockierung abgeschlossen werden

**Nachbedingungen**:
- Ernte kann angelegt werden

**Tags**: [req-010, karenzzeit-abgelaufen, ernte-moeglich, gruen-status, cross-ref-req-007]

---

### TC-010-058: Hermaphrodismus-Befund erzeugt Cultivar-Markierung (Cross-Ref REQ-001/REQ-017)

**Requirement**: REQ-010 § 6 DoD — Genetische Markierung; Cross-Ref REQ-001, REQ-017
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Hermaphrodismus-Befund (severity = "critical") wurde für Pflanze "Bagseed #1" gespeichert
- Cultivar des Bagseed #1 hat noch keine hermie_prone-Markierung

**Testschritte**:
1. Nutzer navigiert zur Cultivar-Detailseite des Cultivars von "Bagseed #1" (unter Stammdaten/REQ-001)
2. Nutzer sucht nach Hermie-Prone-Kennzeichnung

**Erwartete Ergebnisse**:
- Die Cultivar-Detailseite zeigt ein "Hermie-prone"-Badge, Label oder Warnung
- Die Markierung enthält: Datum der Erstmeldung, Schweregrad des Vorfalls ("Critical"), Stress-Kontext
- In der Liniage-Ansicht (REQ-017) ist für Pflanzen dieser genetischen Linie eine Warnung sichtbar

**Nachbedingungen**:
- Cultivar ist dauerhaft als hermie_prone markiert

**Tags**: [req-010, genetische-markierung, cultivar, hermie-prone, cross-ref-req-001, cross-ref-req-017]

---

## Abdeckungsmatrix

| Spez-Abschnitt | Beschreibung | Testfall-IDs |
|---|---|---|
| REQ-010 § 6 DoD — Pest/Disease-Katalog | Listenansicht, Erstellen, Validierung | TC-010-001 bis TC-010-018 |
| REQ-010 § 6 DoD — Behandlungs-Katalog | Listenansicht, Erstellen, IPM-Hierarchie | TC-010-019 bis TC-010-026 |
| REQ-010 § 6 DoD — Karenzzeit-Enforcement | KarenzStatusCard, Ernte-Blockierung | TC-010-027 bis TC-010-029, TC-010-056, TC-010-057 |
| REQ-010 § 6 DoD — Resistenzmanagement | Max. 3 Anwendungen, Wirkstoff-Rotation | TC-010-030, TC-010-031 |
| REQ-010 § 6 DoD — Hermaphrodismus | Isolated/Spreading/Critical, Protokoll | TC-010-032 bis TC-010-038 |
| REQ-010 § 6 DoD — Behandlungsempfehlung | Biologisch, IPM-Hierarchie | TC-010-039, TC-010-040 |
| REQ-010 § 6 DoD — Chemie-Inkompatibilität | Kontraindizierte Wirkstoffe | TC-010-041 |
| REQ-010 § 6 DoD — Inspektions-Workflow | Auto-Tasks, Frequenz nach Befallsdruck | TC-010-042, TC-010-043 |
| REQ-010 § 6 DoD — Behandlungs-Tracking | Efficacy-Rating | TC-010-044 |
| REQ-010 § 6 DoD — Standort-Historie | Befallsmuster pro Slot | TC-010-045 |
| REQ-010 § 6 DoD — Prävention-Score | Dashboard-Indikator | TC-010-046 |
| REQ-010 § 6 DoD — Navigationstruktur | Routing Pflanzenschutz | TC-010-047, TC-010-048 |
| REQ-010 § 4 — Authentifizierung | Auth-Schutz, globale Stammdaten | TC-010-049, TC-010-050 |
| REQ-010 § 6 DoD — Wetter-Integration | Pilz-Risikowarnung | TC-010-051 |
| REQ-010 Fehlerzustände | Netzwerkfehler, Serverfehler | TC-010-052, TC-010-053 |
| REQ-010 Tabellen-Sortierung | Sortierung, URL-Persistenz | TC-010-054, TC-010-055 |
| Cross-Ref REQ-001/REQ-017 | Genetische Markierung hermie_prone | TC-010-058 |

### Bekannte Lücken (noch nicht implementierte UI-Features)

Die folgenden DoD-Anforderungen aus § 6 haben noch keine fertigen UI-Seiten im Frontend und benötigen entsprechende Implementierung bevor die Testfälle ausführbar sind:

- **Inspektions-Erfassung mit Hermaphrodismus-Feldern** (TC-010-032 bis TC-010-038): Keine dedizierte Inspektions-Seite im Frontend vorhanden (`pflanzenschutz/` enthält nur List-Pages und KarenzStatusCard)
- **Behandlungsanwendungs-Workflow** (TC-010-039 bis TC-010-044): TreatmentApplication-Seite fehlt im Frontend
- **Nützlings-Kalkulation** (TC-010-039): Kein UI für Ausbringungs-Kalkulation vorhanden
- **Resistenzmanagement-Warnung** (TC-010-030, TC-010-031): Warnung muss im Behandlungs-Zuordnungs-UI sichtbar sein
- **Bestäubungs-Check-Workflow** (TC-010-036): Kein UI für Bestäubungs-Checks sichtbar
- **Compliance-Export** (CSV/PDF): Kein Export-Button in TreatmentListPage implementiert

Diese Lücken sind als **Spec-Vorgriff** dokumentiert — die Testfälle sind für die zukünftige Implementierung vorgesehen.
