---
ID: NFR-010
Titel: UI-Vollständigkeit — Pflegemasken & Listenansichten für alle Entitäten
Kategorie: Usability / UI-Vollständigkeit
Unterkategorie: CRUD-Masken, Listenansichten, Datenpflege
Fokus: Frontend
Technologie: React 18, TypeScript, MUI, Redux Toolkit, Zod, react-router-dom
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [ui, crud, listenansicht, pflegemaske, vollständigkeit, datenpflege, usability]
Abhängigkeiten: [NFR-001, NFR-003, NFR-006, UI-NFR-004, UI-NFR-008, UI-NFR-010]
Betroffene Module: [Frontend]
---

# NFR-010: UI-Vollständigkeit — Pflegemasken & Listenansichten für alle Entitäten

## Abgrenzung zu bestehenden NFRs

| Dokument | Fokus | Definiert |
|---|---|---|
| NFR-001 (Separation of Concerns) | Schichtenarchitektur, API-Kommunikation | **Wie** Frontend mit Backend kommuniziert |
| NFR-003 (Code-Standard & Linting) | ESLint, TypeScript strict, Formatierung | **Wie** Code geschrieben wird |
| NFR-006 (API-Fehlerbehandlung) | Error-Handling, Fehlermeldungen im UI | **Wie** Fehler angezeigt werden |
| UI-NFR-004 (Feedback) | Toast, Validierungsdarstellung, Bestätigungsdialoge | **Wie** Feedback visuell dargestellt wird |
| UI-NFR-008 (Formulare) | Validierungszeitpunkte, Dirty-State, Submit-Verhalten | **Wie** Formulare sich verhalten |
| UI-NFR-010 (Tabellen) | Sortierung, Filter, Pagination, Responsive, a11y | **Wie** Tabellen sich verhalten |
| **NFR-010 (dieses Dokument)** | CRUD-Masken, Listenansichten, Datenpflege | **Was** pro Entität vorhanden sein muss |

NFR-010 definiert die **Mindestanforderungen an die UI-Abdeckung** jeder Domänenentität. Es stellt sicher, dass jede Entität über vollständige Pflegemasken (Create, Read, Update, Delete) sowie tabellarische Listenansichten verfügt. Die bestehenden Shared-Komponenten und Patterns werden referenziert und als verbindlich für alle CRUD-Masken erklärt.

---

## 1. Business Case

### 1.1 User Stories

**Als** Administrator
**möchte ich** für jede Entität im System vollständige Pflege-Masken (Erstellen, Anzeigen, Bearbeiten, Löschen) vorfinden
**um** alle Stamm- und Bewegungsdaten ohne technische Workarounds oder API-Zugriffe pflegen zu können.

**Als** Endanwender (Gärtner/Grower)
**möchte ich** tabellarische Übersichten aller Datensätze mit Sortierung, Pagination und Suche
**um** schnell den gesuchten Eintrag zu finden und per Klick zu dessen Detail-Ansicht zu navigieren.

**Als** Endanwender
**möchte ich** beim Bearbeiten vor ungespeicherten Änderungen gewarnt werden und beim Löschen eine Bestätigung erhalten
**um** versehentlichen Datenverlust zu vermeiden.

**Als** Entwickler
**möchte ich** ein einheitliches Pattern für CRUD-Masken und Listenansichten
**um** neue Entitäten konsistent und effizient implementieren zu können, ohne UI-Patterns neu zu erfinden.

### 1.2 Geschäftliche Motivation

Ohne vollständige CRUD-Abdeckung:

1. **Dateninkonsistenzen** — Entitäten, die nur erstellt aber nicht bearbeitet werden können, erzwingen Löschen + Neuanlage bei Korrekturen
2. **Produktivitätsverlust** — Fehlende Listen-/Detailansichten erfordern API-Zugriffe oder Datenbankabfragen durch Entwickler
3. **Fehleranfälligkeit** — Ohne Löschfunktion mit Bestätigung bleiben verwaiste Datensätze im System
4. **Inkonsistente UX** — Unterschiedliche Pflegetiefe pro Entität verwirrt Anwender und erhöht Schulungsaufwand

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein Gärtner hat beim Anlegen einer Botanischen Familie den Nährstoffbedarf falsch auf „low" gesetzt. Der korrekte Wert ist „heavy".
> **Ohne NFR-010**: Es gibt kein Edit-Formular für BotanicalFamily. Der Gärtner muss die Familie löschen und komplett neu anlegen — inklusive aller Referenzen (Species, Cultivars), die dadurch ungültig werden.
> **Mit NFR-010**: Der Gärtner öffnet die Detail-Ansicht, klickt „Bearbeiten", ändert den Wert und speichert. Alle Referenzen bleiben intakt.

---

## 2. Anforderungen an Pflegemasken (CRUD)

### 2.1 CRUD-Operationen

Jede Domänenentität **MUSS** folgende UI-Operationen unterstützen:

| Operation | UI-Element | Beschreibung |
|---|---|---|
| **Create** | Dialog oder eigene Seite | Neuen Datensatz anlegen mit Formularvalidierung |
| **Read** | Detail-Seite oder Detail-Section | Alle Felder des Datensatzes anzeigen (read-only) |
| **Update** | Edit-Formular (inline oder eigene Seite) | Bestehenden Datensatz bearbeiten |
| **Delete** | Button mit Bestätigungsdialog | Datensatz entfernen nach expliziter Bestätigung |

### 2.2 Create-Dialog / Create-Seite

**MUSS**:
- Einleitungstext oberhalb des Formulars, der dem Nutzer kurz erklärt, was er anlegt und welche Auswirkungen das Erstellen hat (z.B. *„Legen Sie eine neue Botanische Familie an. Familien gruppieren Pflanzenarten mit ähnlichem Nährstoffbedarf."*)
- Alle Pflichtfelder sind visuell gekennzeichnet (Asterisk `*` im Label)
- Eingabevalidierung via Zod-Schema mit feldspezifischen Fehlermeldungen
- Hinweistexte (`helperText`) für Felder, die Erklärung benötigen (vgl. REQ-012 UI-NFR-003)
- Absende-Button ist deaktiviert, solange Pflichtfelder leer oder Validierung fehlschlägt
- Erfolgsrückmeldung (Snackbar/Toast) nach erfolgreichem Erstellen
- Fehlerbehandlung gemäß NFR-006 (feldspezifische API-Fehler anzeigen)

**MUSS** bestehende Shared-Komponenten verwenden:

| Komponente | Pfad | Zweck |
|---|---|---|
| `FormTextField` | `src/frontend/src/components/form/FormTextField.tsx` | Texteingabefelder mit Label, helperText, Validierung |
| `FormSelectField` | `src/frontend/src/components/form/FormSelectField.tsx` | Dropdown-Auswahl (Enum-Werte, Referenzen) |
| `FormNumberField` | `src/frontend/src/components/form/FormNumberField.tsx` | Numerische Eingaben (pH, EC, Temperatur etc.) |
| `FormDateField` | `src/frontend/src/components/form/FormDateField.tsx` | Datumseingaben |
| `FormChipInput` | `src/frontend/src/components/form/FormChipInput.tsx` | Mehrfachauswahl als Chips (Tags, Kategorien) |
| `FormActions` | `src/frontend/src/components/form/FormActions.tsx` | Standardisierte Aktionsleiste (Speichern, Abbrechen) |

### 2.3 Read / Detail-Ansicht

**MUSS**:
- Alle Felder der Entität werden angezeigt (read-only)
- Navigation zurück zur Listenansicht (Breadcrumbs via `src/frontend/src/components/layout/Breadcrumbs.tsx`)
- Seitentitel via `PageTitle`-Komponente (`src/frontend/src/components/layout/PageTitle.tsx`)
- Aktionsleiste mit Buttons für „Bearbeiten" und „Löschen"
- Eingebettete Kind-Entitäten als Sections anzeigen (z.B. Cultivars in Species-Detail)

**MUSS** Lade- und Fehlerzustände behandeln:

| Zustand | Komponente | Verhalten |
|---|---|---|
| Laden | `LoadingSkeleton` (`src/frontend/src/components/common/LoadingSkeleton.tsx`) | Skeleton-Platzhalter während API-Call |
| Fehler | `ErrorDisplay` (`src/frontend/src/components/common/ErrorDisplay.tsx`) | Fehlermeldung mit Retry-Option |
| Nicht gefunden | 404-Seite | Navigation zu `NotFoundPage` bei ungültigem Key |

### 2.4 Update / Edit-Formular

**MUSS**:
- Einleitungstext oberhalb des Formulars, der dem Nutzer erklärt, welchen Datensatz er bearbeitet und worauf er achten sollte (z.B. *„Bearbeiten Sie die Eigenschaften dieser Botanischen Familie. Änderungen wirken sich auf alle zugeordneten Arten aus."*)
- Formular wird mit den aktuellen Werten des Datensatzes vorbelegt
- Gleiche Validierungsregeln wie beim Create-Dialog (Zod-Schema)
- `UnsavedChangesGuard` (`src/frontend/src/components/form/UnsavedChangesGuard.tsx`) warnt vor dem Verlassen bei ungespeicherten Änderungen
- Absende-Button ist deaktiviert, wenn keine Änderungen vorgenommen wurden
- Optimistic Updates oder Loading-State während der API-Kommunikation
- Erfolgsrückmeldung nach erfolgreichem Speichern

**SOLL**: Edit kann als eigener Modus auf der Detail-Seite (inline-edit) oder als separate Seite umgesetzt werden — beides ist akzeptabel, muss aber pro Entitätsgruppe konsistent sein.

### 2.5 Delete mit Bestätigung

**MUSS**:
- Löschung erfordert explizite Bestätigung über `ConfirmDialog` (`src/frontend/src/components/common/ConfirmDialog.tsx`)
- Dialog zeigt die zu löschende Entität (Name/ID) im Bestätigungstext
- Lösch-Button verwendet `destructive={true}` (roter Button)
- Loading-State während des API-Calls (`loading`-Prop auf `ConfirmDialog`)
- Nach erfolgreicher Löschung: Rückkehr zur Listenansicht mit Erfolgsrückmeldung
- Bei Fehler (z.B. referentielle Integrität): Fehlermeldung gemäß NFR-006

---

## 3. Anforderungen an Listenansichten

### 3.1 Tabellarische Übersicht

Jede Domänenentität **MUSS** eine tabellarische Listenansicht besitzen, die auf der `DataTable`-Komponente (`src/frontend/src/components/common/DataTable.tsx`) basiert.

**MUSS**:
- Einleitungstext oberhalb der Tabelle (unterhalb des Seitentitels), der dem Nutzer kurz erklärt, welche Datensätze die Liste enthält und wofür sie verwendet werden (z.B. *„Botanische Familien gruppieren Pflanzenarten nach Verwandtschaft und bestimmen den typischen Nährstoffbedarf. Klicken Sie auf einen Eintrag, um Details und zugehörige Arten zu sehen."*)
- Spalten zeigen die wichtigsten Felder der Entität (Name, Status, Typ, Datum etc.)
- Zeilenklick navigiert zur Detail-Ansicht (`onRowClick`)
- Jede Zeile ist über einen eindeutigen Schlüssel identifizierbar (`getRowKey`)
- i18n-konforme Spaltenüberschriften (DE/EN via react-i18next)
- Domänenwerte in Dropdowns/Tabellen werden gemäß UI-NFR-007 (REQ-001 R-004a, R-005a) lokalisiert

### 3.2 Pagination

**MUSS**:
- Server-seitige Pagination mit konfigurierbaren Seitengrößen (`rowsPerPageOptions: [10, 25, 50, 100]`)
- Anzeige der Gesamtanzahl der Datensätze
- Standardmäßig 50 Einträge pro Seite

### 3.3 Sortierung

**MUSS**:
- Alle sichtbaren Spalten MÜSSEN sortierbar sein
- Sortierrichtung (aufsteigend/absteigend) per Klick auf Spaltenüberschrift umschaltbar
- Sortierzustand visuell durch Pfeilsymbol in der Spaltenüberschrift angezeigt (MUI `TableSortLabel`)
- Standard-Sortierung: Name aufsteigend (oder Erstellungsdatum absteigend, falls kein Name-Feld vorhanden)
- Sortierung erfolgt server-seitig (API-Parameter `sort_by`, `sort_order`)

> **Hinweis**: Die aktuelle `DataTable`-Komponente unterstützt noch keine Sortierung. Diese Erweiterung ist bei der Umsetzung von NFR-010 zu implementieren.

### 3.3a Durchsuchbarkeit

**MUSS**:
- Jede Listenansicht MUSS ein Suchfeld oberhalb der Tabelle bereitstellen
- Das Suchfeld durchsucht alle textuellen Spalten der Tabelle (Volltextsuche)
- Sucheingaben werden mit Debouncing versehen (300ms Verzögerung, vgl. UI-NFR-003 R-017)
- Die Suche erfolgt server-seitig (API-Parameter `search`)
- Bei aktiver Suche wird die Ergebnisanzahl angezeigt (z.B. *„3 von 42 Ergebnissen"*)
- Der Suchbegriff wird in der URL als Query-Parameter abgebildet (`?search=...`), damit gefilterte Ansichten teilbar sind (vgl. UI-NFR-005 R-003)
- Ein „Zurücksetzen"-Button (X-Icon) im Suchfeld löscht den Suchbegriff und zeigt alle Datensätze

> **Hinweis**: Die aktuelle `DataTable`-Komponente unterstützt noch keine Suche. Diese Erweiterung ist bei der Umsetzung von NFR-010 zu implementieren (MUI `TextField` mit `InputAdornment`).

### 3.4 Leerzustand

**MUSS**:
- Bei leerer Datenmenge zeigt die Tabelle eine `EmptyState`-Komponente (`src/frontend/src/components/common/EmptyState.tsx`)
- `EmptyState` enthält eine beschreibende Nachricht und einen Action-Button zum Erstellen des ersten Eintrags

### 3.5 Ladezustand

**MUSS**:
- Während des Ladens wird `LoadingSkeleton` mit `variant="table"` angezeigt
- Kein leerer Zustand oder Flackern zwischen Laden und Datenanzeige

### 3.6 Erstell-Aktion

**MUSS**:
- Prominenter „Hinzufügen"-Button (FAB oder Button in der Toolbar) oberhalb der Tabelle
- Öffnet den zugehörigen Create-Dialog oder navigiert zur Create-Seite

---

## 4. Vollständigkeitsmatrix

### 4.1 Ist-Zustand (aktuell implementiert)

| Entität | REQ | List | Create | Read | Update | Delete | Vollständig? |
|---|---|---|---|---|---|---|---|
| BotanicalFamily | REQ-001 | ✓ | ✓ | ✓ | **—** | ✓ | Nein |
| Species | REQ-001 | ✓ | ✓ | ✓ | ✓ | ✓ | **Ja** |
| Cultivar | REQ-001 | ✓¹ | ✓ | **—** | **—** | ✓ | Nein |
| Site | REQ-002 | ✓ | ✓ | ✓ | ✓ | ✓ | **Ja** |
| Location | REQ-002 | ✓¹ | ✓ | ✓ | ✓ | ✓ | **Ja** |
| Slot | REQ-002 | ✓¹ | ✓ | ✓ | **—** | **—** | Nein |
| Substrate | REQ-002 | ✓ | ✓ | ✓ | **—** | **—** | Nein |
| Batch | REQ-002 | **—** | ✓ | ✓ | **—** | **—** | Nein |
| PlantInstance | REQ-003 | ✓ | ✓ | ✓ | **—** | ✓ | Nein |
| GrowthPhase | REQ-003 | ✓¹ | ✓ | ✓ | ✓ | **—** | Nein |

¹ = Eingebettete Section in übergeordneter Detail-Seite (kein eigenständiger Routen-Endpunkt)

### 4.2 Soll-Zustand (100% Abdeckung)

| Entität | REQ | List | Create | Read | Update | Delete | Umsetzungsform |
|---|---|---|---|---|---|---|---|
| BotanicalFamily | REQ-001 | ✓ | ✓ | ✓ | **✓** | ✓ | Eigenständige Seiten |
| Species | REQ-001 | ✓ | ✓ | ✓ | ✓ | ✓ | Eigenständige Seiten |
| Cultivar | REQ-001 | ✓ | ✓ | **✓** | **✓** | ✓ | Section in Species-Detail² |
| Site | REQ-002 | ✓ | ✓ | ✓ | ✓ | ✓ | Eigenständige Seiten |
| Location | REQ-002 | ✓ | ✓ | ✓ | ✓ | ✓ | Section in Site-Detail² |
| Slot | REQ-002 | ✓ | ✓ | ✓ | **✓** | **✓** | Section in Location-Detail² |
| Substrate | REQ-002 | ✓ | ✓ | ✓ | **✓** | **✓** | Eigenständige Seiten |
| Batch | REQ-002 | **✓** | ✓ | ✓ | **✓** | **✓** | Eigenständige Seiten oder Section in Substrate-Detail² |
| PlantInstance | REQ-003 | ✓ | ✓ | ✓ | **✓** | ✓ | Eigenständige Seiten |
| GrowthPhase | REQ-003 | ✓ | ✓ | ✓ | ✓ | **✓** | Section in PlantInstance-Detail² |

**Fett** = fehlende Operation, die implementiert werden muss.

² = Eingebettete Entitäten dürfen als Section in der übergeordneten Detail-Seite umgesetzt werden (siehe Abschnitt 5).

### 4.3 Zukünftige Entitäten (noch nicht implementiert)

Bei Implementierung der folgenden REQs **MUSS** jede neue Entität von Beginn an vollständige CRUD-Masken erhalten:

| Entität | REQ | Beschreibung |
|---|---|---|
| NutrientProfile | REQ-004 | Nährstoffprofile (NPK-Werte, EC-Zielwerte) |
| FertilizerProduct | REQ-004 | Düngemittel-Produkte (Zusammensetzung, Dosierung) |
| MixingRecipe | REQ-004 | Mischrezepte (Reihenfolge, EC-Berechnung) |
| SensorConfig | REQ-005 | Sensorkonfiguration (MQTT-Topics, Kalibrierung) |
| SensorReading | REQ-005 | Messwert-Anzeige (Zeitreihen, Diagramme) |
| Task | REQ-006 | Aufgaben (Planung, Zuweisung, Status) |
| HarvestRecord | REQ-007 | Erntedokumentation (Gewicht, Qualität) |
| DryingBatch | REQ-008 | Trocknungs-Chargen (Temperatur, Dauer) |
| CuringBatch | REQ-008 | Aushärtungs-Chargen (Feuchte, Dauer) |
| IPMObservation | REQ-010 | Schädlingsbeobachtungen (Befallsgrad, Fotos) |
| IPMIntervention | REQ-010 | Bekämpfungsmaßnahmen (Mittel, Karenzzeit) |

---

## 5. Ausnahmen: Eingebettete Entitäten

### 5.1 Erlaubte Einbettung

Entitäten, die **ausschließlich im Kontext einer übergeordneten Entität** existieren, dürfen als eingebettete Section in der Detail-Seite der übergeordneten Entität umgesetzt werden. In diesem Fall gelten angepasste Regeln:

| Standard-CRUD | Eingebettete Variante |
|---|---|
| Eigenständige Listenseite | Tabelle/Section in der übergeordneten Detail-Seite |
| Eigenständige Detail-Seite | Expandable Row oder Inline-Anzeige in der Section |
| Eigenständige Edit-Seite | Dialog (Modal) zum Bearbeiten |
| Navigation über Router | Kein eigener Routen-Endpunkt erforderlich |

### 5.2 Aktuelle eingebettete Entitäten

| Kind-Entität | Eltern-Entität | Seite |
|---|---|---|
| Cultivar | Species | `SpeciesDetailPage.tsx` → `CultivarListSection.tsx` |
| Location | Site | `SiteDetailPage.tsx` → `LocationListSection.tsx` |
| Slot | Location | `LocationDetailPage.tsx` (inline) |
| GrowthPhase | PlantInstance | `PlantInstanceDetailPage.tsx` → `GrowthPhaseListSection.tsx` |
| Batch | Substrate | `SubstrateDetailPage.tsx` (inline) |

### 5.3 Anforderungen an eingebettete Sections

Auch eingebettete Entitäten **MÜSSEN** vollständige CRUD-Operationen bieten:

- **List**: Tabelle innerhalb der Section (kann vereinfachtes Layout nutzen)
- **Create**: Dialog (Modal) mit Formularvalidierung
- **Read**: Inline-Anzeige oder Expandable Row (Detail-Dialog akzeptabel)
- **Update**: Edit-Dialog (Modal) mit vorausgefüllten Werten
- **Delete**: `ConfirmDialog` mit Bestätigungsabfrage

---

## 6. Konsistenzregeln

### 6.1 UI-Pattern-Konsistenz

**MUSS**: Alle CRUD-Masken folgen einem einheitlichen Pattern:

| Aspekt | Regel |
|---|---|
| **Einleitungstexte** | Jede Listenansicht und jedes Formular (Create/Edit) beginnt mit einem kurzen erklärenden Text (1–2 Sätze) unterhalb des Seitentitels, der Kontext und Zweck der Ansicht beschreibt. Texte sind i18n-fähig (DE/EN). |
| **Formular-Layouts** | Einheitliche Feldanordnung (Labels links, Felder rechts oder vertikal gestapelt) |
| **Button-Platzierung** | Primäre Aktion rechts, Abbrechen links (vgl. `FormActions`) |
| **Validierung** | Inline-Feldvalidierung bei Blur, Formular-Validierung bei Submit |
| **Fehlermeldungen** | Unter dem Feld (helperText), rot eingefärbt |
| **Erfolgsmeldungen** | Snackbar (unten-mittig), automatisch ausblendend |
| **Lösch-Bestätigung** | Immer über `ConfirmDialog` mit `destructive={true}` |
| **Lade-Indikatoren** | `LoadingSkeleton` für initiales Laden, Button-Loading für Aktionen |

### 6.2 Responsivität

**MUSS**: Alle Masken und Listen sind auf Desktop-Bildschirmen (≥1024px) vollständig nutzbar.
**SOLL**: Listen und Detail-Ansichten sind auf Tablet-Bildschirmen (≥768px) nutzbar.

### 6.3 Barrierefreiheit

**MUSS**:
- Formulare verwenden `<label>`-Elemente (MUI TextField `label`-Prop)
- Dialoge verwenden `role="dialog"` bzw. `role="alertdialog"` (MUI Dialog Standard)
- Fokus-Management: Dialog öffnet → Fokus auf erstes Feld; Dialog schließt → Fokus zurück auf Auslöser
- `data-testid`-Attribute auf allen interaktiven Elementen (für Testbarkeit)

---

## 7. Akzeptanzkriterien

### Definition of Done

- [ ] **Vollständigkeit**
    - [ ] Jede Entität in der Vollständigkeitsmatrix (Abschnitt 4.2) hat alle 5 CRUD-Operationen implementiert
    - [ ] Alle Listenansichten verwenden die `DataTable`-Komponente
    - [ ] Keine Entität hat weniger als 5/5 CRUD-Operationen (oder dokumentierte Ausnahme)
- [ ] **Create-Dialoge**
    - [ ] Einleitungstext oberhalb des Formulars vorhanden (1–2 Sätze, i18n DE/EN)
    - [ ] Pflichtfelder sind visuell gekennzeichnet (Asterisk)
    - [ ] Zod-Validierung mit deutschen Fehlermeldungen
    - [ ] Hinweistexte (helperText) wo fachlich nötig
    - [ ] Erfolgs-Snackbar nach Erstellen
    - [ ] API-Fehler werden gemäß NFR-006 angezeigt
- [ ] **Detail-/Read-Ansichten**
    - [ ] Alle Felder der Entität werden angezeigt
    - [ ] Breadcrumb-Navigation vorhanden
    - [ ] Loading- und Error-States implementiert
    - [ ] Aktionsleiste mit Bearbeiten- und Löschen-Buttons
- [ ] **Edit-Formulare**
    - [ ] Einleitungstext oberhalb des Formulars vorhanden (1–2 Sätze, i18n DE/EN)
    - [ ] Formular ist mit aktuellen Werten vorbelegt
    - [ ] `UnsavedChangesGuard` ist aktiv
    - [ ] Speichern-Button ist bei unverändertem Formular deaktiviert
    - [ ] Gleiche Validierung wie beim Create
    - [ ] Erfolgs-Snackbar nach Speichern
- [ ] **Delete-Funktion**
    - [ ] Löschung erfordert `ConfirmDialog` mit Bestätigung
    - [ ] Dialog zeigt den Namen/Bezeichner der zu löschenden Entität
    - [ ] `destructive={true}` auf dem Bestätigungsbutton
    - [ ] Loading-State während des Löschvorgangs
    - [ ] Rückkehr zur Liste nach erfolgreicher Löschung
- [ ] **Listenansichten**
    - [ ] Einleitungstext oberhalb der Tabelle vorhanden (1–2 Sätze, i18n DE/EN)
    - [ ] Pagination mit konfigurierbaren Seitengrößen
    - [ ] Alle Spalten sind sortierbar (server-seitig, MUI `TableSortLabel`)
    - [ ] Suchfeld oberhalb der Tabelle vorhanden (Volltextsuche mit 300ms Debouncing)
    - [ ] Suchbegriff als URL-Query-Parameter abgebildet (`?search=...`)
    - [ ] Ergebnisanzahl bei aktiver Suche angezeigt
    - [ ] Leerzustand mit `EmptyState` und Erstell-Aktion
    - [ ] Ladezustand mit `LoadingSkeleton`
    - [ ] Zeilenklick navigiert zur Detail-Ansicht
    - [ ] „Hinzufügen"-Button prominent sichtbar
- [ ] **Konsistenz**
    - [ ] Alle Masken verwenden die gemeinsamen Form-Komponenten
    - [ ] Einheitliches Pattern für eigenständige und eingebettete Entitäten
    - [ ] i18n-Schlüssel für alle Labels und Meldungen vorhanden (DE + EN)
- [ ] **Testing**
    - [ ] Jede CRUD-Operation hat mindestens einen vitest-Test
    - [ ] Tests prüfen Formularvalidierung (Pflichtfelder, Fehlermeldungen)
    - [ ] Tests prüfen Loading-, Empty- und Error-States
    - [ ] Tests prüfen `ConfirmDialog`-Interaktion bei Delete

### Testszenarien

#### Szenario 1: Vollständiger CRUD-Zyklus (BotanicalFamily)

```
1. Nutzer öffnet /stammdaten/botanische-familien → Listenansicht mit DataTable
2. Nutzer klickt „Hinzufügen" → Create-Dialog öffnet sich
3. Nutzer füllt Pflichtfelder aus (Name, Nährstoffbedarf) → Speichern
4. Erfolgs-Snackbar erscheint, neuer Eintrag in der Liste sichtbar
5. Nutzer klickt auf den Eintrag → Detail-Ansicht mit allen Feldern
6. Nutzer klickt „Bearbeiten" → Edit-Formular mit vorausgefüllten Werten
7. Nutzer ändert Nährstoffbedarf → Speichern → Erfolgs-Snackbar
8. Nutzer klickt „Löschen" → ConfirmDialog mit Familien-Name
9. Nutzer bestätigt → Rückkehr zur Liste, Eintrag entfernt
```

#### Szenario 2: Eingebettete Entität (Cultivar in Species)

```
1. Nutzer öffnet Species-Detail-Seite → CultivarListSection zeigt Sorten
2. Nutzer klickt „Sorte hinzufügen" → Create-Dialog öffnet sich
3. Nutzer füllt Felder aus → Speichern → neue Sorte in der Section sichtbar
4. Nutzer klickt auf Sorte → Detail-Dialog/Inline-Anzeige mit allen Feldern
5. Nutzer klickt „Bearbeiten" → Edit-Dialog mit vorausgefüllten Werten
6. Nutzer ändert Wert → Speichern → aktualisierte Anzeige
7. Nutzer klickt „Löschen" → ConfirmDialog → Bestätigung → Sorte entfernt
```

#### Szenario 3: Leere Liste mit EmptyState

```
1. Nutzer öffnet /standorte/substrate → keine Substrate vorhanden
2. EmptyState-Komponente wird angezeigt mit Nachricht und „Erstellen"-Button
3. Nutzer klickt „Erstellen" → Create-Dialog öffnet sich
```

#### Szenario 4: UnsavedChangesGuard

```
1. Nutzer bearbeitet ein Substrat (ändert pH-Wert)
2. Nutzer klickt auf Breadcrumb-Link (Navigation weg von der Seite)
3. ConfirmDialog warnt: „Ungespeicherte Änderungen gehen verloren"
4. Nutzer klickt „Abbrechen" → bleibt auf der Edit-Seite
5. Nutzer klickt „Verlassen" → Navigation wird fortgesetzt
```

#### Szenario 5: Delete mit referenzieller Integrität

```
1. Nutzer versucht, eine BotanicalFamily zu löschen, die von Species referenziert wird
2. ConfirmDialog wird angezeigt, Nutzer bestätigt
3. API gibt HTTP 409 (CONFLICT) zurück
4. Fehlermeldung gemäß NFR-006: „BotanicalFamily kann nicht gelöscht werden, da sie von Species referenziert wird."
5. Dialog bleibt offen, Nutzer kann abbrechen
```

---

## 8. Abhängigkeiten

### 8.1 Technische Abhängigkeiten

| Abhängigkeit | Typ | Beschreibung |
|---|---|---|
| **NFR-001** (Separation of Concerns) | Architektur | Alle CRUD-Operationen kommunizieren über REST-API mit dem Backend |
| **NFR-003** (Code-Standard) | Code Quality | ESLint, TypeScript strict, einheitliche Benennung |
| **NFR-006** (API-Fehlerbehandlung) | Error Handling | Fehlermeldungen in Formularen und bei Löschaktionen |
| **REQ-001** (Stammdatenverwaltung) | Fachlich | Definiert Entitäten BotanicalFamily, Species, Cultivar |
| **REQ-002** (Standort/Substrat) | Fachlich | Definiert Entitäten Site, Location, Slot, Substrate, Batch |
| **REQ-003** (Phasensteuerung) | Fachlich | Definiert Entitäten PlantInstance, GrowthPhase |

### 8.2 Komponentenabhängigkeiten

| Shared-Komponente | Pfad | Genutzt für |
|---|---|---|
| `DataTable` | `src/frontend/src/components/common/DataTable.tsx` | Alle Listenansichten |
| `ConfirmDialog` | `src/frontend/src/components/common/ConfirmDialog.tsx` | Alle Delete-Bestätigungen |
| `EmptyState` | `src/frontend/src/components/common/EmptyState.tsx` | Leerzustand in Listen |
| `LoadingSkeleton` | `src/frontend/src/components/common/LoadingSkeleton.tsx` | Ladezustand |
| `ErrorDisplay` | `src/frontend/src/components/common/ErrorDisplay.tsx` | Fehlerzustand |
| `FormTextField` | `src/frontend/src/components/form/FormTextField.tsx` | Texteingaben in Formularen |
| `FormSelectField` | `src/frontend/src/components/form/FormSelectField.tsx` | Dropdown-Auswahl |
| `FormNumberField` | `src/frontend/src/components/form/FormNumberField.tsx` | Numerische Felder |
| `FormDateField` | `src/frontend/src/components/form/FormDateField.tsx` | Datumsfelder |
| `FormChipInput` | `src/frontend/src/components/form/FormChipInput.tsx` | Mehrfachauswahl |
| `FormActions` | `src/frontend/src/components/form/FormActions.tsx` | Aktionsleiste in Formularen |
| `UnsavedChangesGuard` | `src/frontend/src/components/form/UnsavedChangesGuard.tsx` | Schutz vor Datenverlust |
| `Breadcrumbs` | `src/frontend/src/components/layout/Breadcrumbs.tsx` | Navigation in Detail-Seiten |
| `PageTitle` | `src/frontend/src/components/layout/PageTitle.tsx` | Seitentitel |

---

## 9. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Unvollständige CRUD-Masken** | Nutzer können Datensätze nicht korrigieren, müssen Löschen + Neuanlage | Hoch | Vollständigkeitsmatrix als DoD-Prüfung |
| **Inkonsistente UI-Patterns** | Unterschiedliche Pflege-Erfahrung pro Entität, erhöhter Schulungsaufwand | Mittel | Verbindliche Shared-Komponenten |
| **Fehlende Löschbestätigung** | Versehentliche Datenlöschung ohne Rückfrage | Hoch | `ConfirmDialog`-Pflicht für alle Delete-Operationen |
| **Fehlende UnsavedChangesGuard** | Unbemerkt verlorene Änderungen beim Navigieren | Mittel | Guard-Pflicht für alle Edit-Formulare |
| **Verwaiste Datensätze** | Entitäten ohne Delete-Funktion sammeln sich an | Mittel | Delete-Operation für jede Entität verpflichtend |
| **Steigende Implementierungskosten** | Nachträgliche Ergänzung fehlender Masken ist aufwändiger als Sofort-Implementierung | Hoch | NFR-010 als Pflicht bei jeder neuen Entität |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
