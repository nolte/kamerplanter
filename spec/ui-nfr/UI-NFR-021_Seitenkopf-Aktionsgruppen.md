---

ID: UI-NFR-021
Titel: Seitenkopf-Aktionsgruppen (Page-Header Action Bar)
Kategorie: UI-Verhalten Unterkategorie: Page-Header, Aktions-Buttons, Button-Gruppen, Overflow, Bulk-Modus, Responsive, Barrierefreiheit
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Prioritaet: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-07-12
Tags: [page-header, action-bar, page-actions, button-gruppen, primaeraktion, sekundaeraktion, utility, export, bulk-modus, selection-mode, destruktiv, overflow, kebab-menu, responsive, kiosk, a11y]
Abhaengigkeiten: [UI-NFR-001, UI-NFR-002, UI-NFR-006, UI-NFR-017, UI-NFR-019]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-021: Seitenkopf-Aktionsgruppen (Page-Header Action Bar)

> **Motivation:** Die Aktions-Buttons im Seitenkopf wirken heute vollstaendig individuell pro Seite. Die Task-Queue zeigt vier `outlined`-Buttons plus einen `contained`-Button; die Pflanzen-Erkennung nur einen einzigen `contained`-Button; die Pflanzen-Detailseite mischt `outlined`, `text` und einen roten **Text**-Button "Pflanze entfernen". Diese Uneinheitlichkeit erhoeht die kognitive Last, verschlechtert die Erlernbarkeit und wirkt lieblos — im Kiosk-/Feldbetrieb verstaerkt sich der Effekt. UI-NFR-017 regelt das Seitenkopf-**Layout** (Titel, Meta-Zeile, Pattern A-D), definiert aber nur punktuell einzelne Aktions-Regeln. Dieses Dokument definiert verbindlich die **Funktion und das Layout jeder Aktions-Gruppe** im Seitenkopf: welche Aktionen hineingehoeren, ihre Gruppierung, Prioritaet, Reihenfolge, Varianten-Zuordnung, das Overflow-Verhalten sowie Responsive-, Kiosk- und Barrierefreiheits-Regeln.

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**moechte ich** auf jeder Seite die verfuegbaren Aktionen an derselben Stelle, in derselben Reihenfolge und mit denselben visuellen Auspraegungen vorfinden
**um** die Anwendung ohne Umlernen bedienen zu koennen.

**Als** Endanwender im Kiosk-/Feldbetrieb
**moechte ich** die wichtigste Aktion einer Seite sofort und mit ausreichend grosser Trefferflaeche erreichen
**um** auch mit Handschuhen oder feuchten Fingern effizient arbeiten zu koennen.

**Als** Frontend-Entwickler
**moechte ich** eine verbindliche Taxonomie und Varianten-Zuordnung fuer Seitenkopf-Aktionen
**um** neue Seiten ohne Einzelfall-Entscheidungen konsistent umzusetzen und bestehende Seiten dagegen pruefen zu koennen.

### 1.2 Geschaeftliche Motivation

1. **Erlernbarkeit** -- Eine feste Position und Prioritaet der Aktionsgruppen macht die Anwendung vorhersehbar; Nutzer finden die Primaeraktion ohne Suchen.
2. **Wiedererkennung** -- Einheitliche Varianten (contained/outlined/text) vermitteln Professionalitaet und eine erkennbare Handlungs-Hierarchie.
3. **Barrierefreiheit** -- Definierte Fokus-Reihenfolge und nicht-visuelle Kennzeichnung destruktiver Aktionen verbessern die Bedienung mit Screenreader und Tastatur.
4. **Wartbarkeit** -- Eine gemeinsame Konvention (spaeter eine gemeinsame `PageActions`-Komponente) verhindert, dass jede Seite ihre Kopf-Aktionen von Hand nachbaut.

### 1.3 Entscheidung: Neues Dokument statt Erweiterung von UI-NFR-017

Diese Anforderung wird als **eigenstaendiges UI-NFR-021** gefuehrt, nicht als Erweiterung von UI-NFR-017. Begruendung:

- Der `spec/ui-nfr/`-Korpus fuehrt jeweils **ein fokussiertes Thema pro Dokument** (UI-NFR-010 Tabellen, UI-NFR-016 Phasen-Visualisierung, UI-NFR-020 Anbau-Zeitachse). UI-NFR-017 regelt das **Seitenkopf-Layout** (Titel, Meta-Zeile, vertikale Ausrichtung, Abstaende, Favoriten-Icon, Tabs). Die vollstaendige Taxonomie der **Aktions-Gruppen** (Funktion, Prioritaet, Overflow, Bulk-Modus, Varianten-Hierarchie, Aktions-A11y) ist ein eigenstaendiges, umfangreiches Thema, das UI-NFR-017 sonst uebermaessig aufblaehen wuerde.
- UI-NFR-017 enthaelt bereits **punktuelle** Aktions-Regeln (R-008 rechtsbuendig/oben, R-009 destruktiv = `outlined color="error"`, R-017/R-019 Erstellen = `contained` + AddIcon). UI-NFR-021 **baut auf diesen auf und praezisiert sie**, statt sie zu duplizieren -- die Zuordnung ist in Abschnitt 2 explizit dokumentiert.
- Das Ausgangs-Issue rahmt die Anforderung ausdruecklich als Kandidat **UI-NFR-021** *oder* Erweiterung von UI-NFR-017; die Korpus-Konvention "ein Thema pro Dokument" gibt hier den Ausschlag fuer ein neues Dokument.

### 1.4 Hinweis zur Dokumentsprache (DE-only)

Der gesamte `spec/ui-nfr/`-Korpus wird **einsprachig auf Deutsch** gefuehrt (siehe CLAUDE.md: "Documentation is written in German"). Es existiert weder eine EN-Spiegelung noch eine Ordner-/Suffix-Konvention fuer `spec/`. Die in `spec/style-guides/DOCS.md` beschriebene DE-kanonische/EN-gespiegelte Paarpflege betrifft ausschliesslich die **Endnutzer-Dokumentation unter `docs/de/` und `docs/en/`**, nicht die Spezifikations-Dokumente unter `spec/`. Dieses Dokument folgt daher der tatsaechlichen Korpus-Konvention (DE-only), um kein alleinstehendes EN-Fragment inmitten von 20 deutschsprachigen Geschwister-Dokumenten zu erzeugen.

---

## 2. Verhaeltnis zu UI-NFR-017 und UI-NFR-006

UI-NFR-021 ersetzt keine Layout-Regeln von UI-NFR-017, sondern setzt darauf auf. Die folgende Tabelle stellt die Zustaendigkeiten klar und verhindert Widersprueche.

| Aspekt | Zustaendig | Bemerkung |
|--------|-----------|-----------|
| Position der Aktions-Zone (rechtsbuendig, an Titel-Zeile ausgerichtet) | UI-NFR-017 R-008, R-013, R-014 | UI-NFR-021 uebernimmt diese Platzierung unveraendert. |
| Erstellen-Button = `contained` + `AddIcon` | UI-NFR-017 R-019 | Von UI-NFR-021 als **Primaeraktion-Gruppe** (Abschnitt 4/5) uebernommen und praezisiert. |
| Destruktive Aktion = `outlined color="error"` | UI-NFR-017 R-009 | Von UI-NFR-021 als **Destruktiv-Gruppe** uebernommen und um Position/Overflow-Ausschluss erweitert. |
| Titel, Meta-Zeile, Chips, Favoriten-Icon, Tabs, Abstaende | UI-NFR-017 | Bleibt vollstaendig bei UI-NFR-017. |
| **Taxonomie der Aktions-Gruppen, Prioritaet, Reihenfolge innerhalb der Zone, Varianten-Hierarchie, Overflow, Bulk-Modus, Aktions-A11y** | **UI-NFR-021** | Neu. |
| MUI-Button-Varianten, semantische Farbrollen, Icon-Regeln (`aria-label`) | UI-NFR-006 R-007, R-021 | UI-NFR-021 waehlt pro Gruppe eine Variante/Farbrolle aus dem Design-System; es definiert keine neuen Tokens. |

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | UI-NFR-021 MUSS auf den Platzierungs-Regeln von UI-NFR-017 (R-008, R-013, R-014) aufsetzen; die Aktions-Zone MUSS rechtsbuendig und an der Titel-Zeile oben ausgerichtet stehen. | MUSS |
| R-002 | Wo UI-NFR-017 R-009 (destruktiv) und R-019 (Erstellen) mit diesem Dokument uebereinstimmen, gelten die hier praezisierten Fassungen; es DARF keine widersprechende zweite Regel eingefuehrt werden. | MUSS |

---

## 3. Taxonomie der Aktionsgruppen

Jede Aktion im Seitenkopf MUSS genau einer der folgenden fuenf Gruppen zugeordnet werden. Die Gruppe bestimmt Position, Reihenfolge, Variante und Overflow-Verhalten (Abschnitte 4-6).

| Gruppe | Zweck | Beispiele | Anzahl typisch |
|--------|-------|-----------|----------------|
| **G1 Primaeraktion** | Die eine wichtigste, vorwaertsgerichtete Aktion der Seite ("Happy Path"). | "+ Aufgabe erstellen", "Pflanze fotografieren", "+ Erstellen" | 0-1 |
| **G2 Sekundaeraktionen** | Haeufige, nicht-primaere Aktionen mit direktem Entity-Bezug. | "Auf Schaedlinge pruefen", "Phasenwechsel", "Erinnerungen generieren" | 0-n |
| **G3 Utility / Export** | Hilfs- und Ausgabe-Aktionen ohne Zustandsaenderung an der Entity. | "Pflegecheckliste als PDF", "Drucken", "Exportieren" | 0-n |
| **G4 Auswahl-/Bulk-Modus** | Umschalter, der die Seite in einen Mehrfachauswahl-Modus versetzt. | "Mehrere auswaehlen" | 0-1 |
| **G5 Destruktive Aktion** | Irreversible oder datenverwerfende Aktion an der Entity. | "Loeschen", "Pflanze entfernen" | 0-1 |

| # | Regel | Stufe |
|---|-------|-------|
| R-003 | Jede Aktion im Seitenkopf MUSS genau einer Gruppe G1-G5 zugeordnet sein. Aktionen ohne eindeutige Gruppe DUERFEN NICHT im Seitenkopf platziert werden. | MUSS |
| R-004 | Eine Seite MUSS hoechstens **eine** Primaeraktion (G1) besitzen. Gibt es keinen klaren "Happy Path", bleibt G1 leer. | MUSS |
| R-005 | Eine Seite MUSS hoechstens **eine** destruktive Aktion (G5) direkt sichtbar im Kopf haben; weitere destruktive Aktionen MUESSEN in das Overflow-Menue (Abschnitt 6) verlagert werden. | MUSS |
| R-006 | Der Bulk-Modus-Umschalter (G4) DARF nur auf Listen-/Uebersichtsseiten erscheinen, auf denen Mehrfachauswahl fachlich sinnvoll ist. | SOLL |
| R-007 | Aktionen, die sich auf ein **einzelnes Listenelement** beziehen (Zeilen-Aktionen), DUERFEN NICHT als Seitenkopf-Aktion gefuehrt werden; sie gehoeren in die Zeile bzw. das Zeilen-Menue (siehe UI-NFR-010). | MUSS |

---

## 4. Varianten-Zuordnung pro Gruppe

Die MUI-`variant`/`color`-Kombination MUSS deterministisch aus der Gruppe folgen. Das beendet das heutige Ad-hoc-Mischen. Alle Farbrollen stammen aus dem Design-System (UI-NFR-006 R-007).

| Gruppe | MUI variant | MUI color | Icon | Begruendung |
|--------|-------------|-----------|------|-------------|
| G1 Primaeraktion | `contained` | `primary` | fuehrendes `startIcon` (z.B. `AddIcon`) | Hoechste visuelle Gewichtung fuer den Happy Path. |
| G2 Sekundaeraktionen | `outlined` | `primary` (Default) | optionales `startIcon` | Deutlich sichtbar, aber der Primaeraktion untergeordnet. |
| G3 Utility / Export | `text` | `primary` bzw. `inherit` | `startIcon` (z.B. `DownloadIcon`, `PrintIcon`) | Geringste Gewichtung; im Overflow bevorzugt. |
| G4 Auswahl-/Bulk-Modus | `outlined` | `primary` | `ChecklistIcon`/`CheckBoxIcon` | Wie G2, da Moduswechsel; im aktiven Zustand als `contained` markiert. |
| G5 Destruktive Aktion | `outlined` | `error` | `DeleteIcon` | Erbt UI-NFR-017 R-009; Rot signalisiert Gefahr ohne die volle Flaeche eines `contained`-Buttons. |

| # | Regel | Stufe |
|---|-------|-------|
| R-008 | Die Variante/Farbe eines Seitenkopf-Buttons MUSS ausschliesslich aus seiner Gruppe (Abschnitt 3) folgen; abweichende Ad-hoc-Kombinationen sind unzulaessig. | MUSS |
| R-009 | Es DARF hoechstens **ein** `contained`-Button (G1) in der Aktions-Zone sichtbar sein, damit die Handlungs-Hierarchie eindeutig bleibt. | MUSS |
| R-010 | Destruktive Aktionen (G5) DUERFEN NICHT als `text`-Button dargestellt werden (heutiger Verstoss: rotes Text-"Pflanze entfernen"); sie MUESSEN `variant="outlined" color="error"` verwenden. | MUSS |
| R-011 | Funktionale Icons in Aktions-Buttons MUESSEN einen `aria-label` bzw. sichtbaren Text tragen (UI-NFR-006 R-021); dekorative Icons `aria-hidden="true"`. | MUSS |

---

## 5. Anordnung und Reihenfolge

Innerhalb der rechtsbuendigen Aktions-Zone (UI-NFR-017 R-008) MUSS die Links-nach-rechts-Reihenfolge der Gruppen fest sein. Die Primaeraktion steht **aussen rechts** (Daumen-naechste Position auf mobilen Geraeten, Ende der Lesereihenfolge).

**Feste Reihenfolge (links → rechts):**

```
[ G4 Bulk ] [ G3 Utility/Export ] [ G2 Sekundaer ] [ ⋮ Overflow ]   [ G5 Destruktiv ]   [ G1 Primaer ]
└────────────────── nach Bedarf im Overflow ──────────────────┘
```

| # | Regel | Stufe |
|---|-------|-------|
| R-012 | Die Gruppen MUESSEN in der Reihenfolge G4 → G3 → G2 → (Overflow) → G5 → G1 von links nach rechts angeordnet sein. Die Primaeraktion (G1) steht immer aussen rechts. | MUSS |
| R-013 | Die destruktive Aktion (G5) MUSS visuell von der Primaeraktion (G1) getrennt stehen (eigene Gruppe, `gap` gemaess UI-NFR-017 R-028), um Fehlklicks zu vermeiden. | MUSS |
| R-014 | Innerhalb einer Gruppe MUESSEN Aktionen nach absteigender Haeufigkeit/Wichtigkeit sortiert sein; die stabilste Reihenfolge ueber Seitenbesuche hinweg ist zu bevorzugen (keine kontextabhaengige Umsortierung). | MUSS |
| R-015 | Die Aktions-Zone MUSS `display: flex`, `gap: 1` (UI-NFR-017 R-028) und `alignItems: 'center'` verwenden. | MUSS |

---

## 6. Overflow-Regel ("Mehr"-Menue)

Der Seitenkopf DARF horizontal niemals ueberlaufen. Ueberzaehlige Aktionen wandern in ein Kebab-/"Mehr"-Menue.

| # | Regel | Stufe |
|---|-------|-------|
| R-016 | Uebersteigt die Zahl **direkt sichtbarer** Aktions-Buttons auf Desktop **drei** (zzgl. Primaeraktion G1), MUESSEN die niedriger priorisierten Aktionen in ein Overflow-Menue (`IconButton` mit `MoreVertIcon`, `⋮`) zusammengefasst werden. | MUSS |
| R-017 | Die Primaeraktion (G1) DARF NIEMALS in das Overflow-Menue wandern; sie bleibt stets als eigenstaendiger Button sichtbar. | MUSS |
| R-018 | Die Verlagerungs-Reihenfolge in das Overflow-Menue MUSS der umgekehrten Prioritaet folgen: zuerst G3 (Utility/Export), dann G2 (Sekundaer), dann G4 (Bulk). G5 (destruktiv) wandert nur, wenn mehr als eine destruktive Aktion existiert (R-005). | MUSS |
| R-019 | Das Overflow-Menue (`Menu`/`MenuItem`) MUSS jede Aktion mit Icon **und** Text-Label darstellen; destruktive Eintraege MUESSEN `color="error"` und eine visuelle Trennung (Divider) erhalten. | MUSS |
| R-020 | Der Overflow-`IconButton` MUSS einen `aria-label` (z.B. "Weitere Aktionen"), `aria-haspopup="menu"` und korrekte `aria-expanded`-Zustaende tragen. | MUSS |
| R-021 | Enthaelt der Seitenkopf hoechstens die durch R-016 erlaubte Anzahl, DARF kein Overflow-Menue erzeugt werden (kein leeres `⋮`). | MUSS |

---

## 7. Responsive / Mobile-First und Kiosk

Die Aktions-Zone MUSS Mobile-First kollabieren und die Touch-Target-Vorgaben aus UI-NFR-001 sowie UI-NFR-019 erfuellen.

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Alle Aktions-Buttons und der Overflow-`IconButton` MUESSEN auf Mobile/Tablet eine Trefferflaeche von mindestens **48×48px** einhalten (UI-NFR-001 R-011). | MUSS |
| R-023 | Auf schmalen Breakpoints (`xs`) MUSS der Header `flexWrap: 'wrap'` verwenden (UI-NFR-017 R-038); die Aktions-Zone bricht unter den Titel um, behaelt aber ihre interne Reihenfolge (R-012). | MUSS |
| R-024 | Auf `xs` MUSS die Overflow-Schwelle (R-016) auf **eine** direkt sichtbare Aktion (die Primaeraktion G1) reduziert werden; alle uebrigen Aktionen wandern in das `⋮`-Menue. Ausnahme siehe R-024a. | MUSS |
| R-024a | Ein Steuerelement, das einen **eigenen Ablauf kapselt** (Kamera-Freigabe, Datei-Download, Druckdialog) und deshalb nicht als Menueeintrag darstellbar ist, DARF auf `xs` zusaetzlich sichtbar bleiben. Zulaessig ist hoechstens **ein** solches Element je Seitenkopf, und es MUSS im Code an der Aufrufstelle begruendet sein. Bekannte Faelle: `PrintButton` (TaskQueuePage), `PestScanButton` (PlantInstanceDetailPage). Ein reines Kommando ohne eigenen Ablauf faellt NICHT unter diese Ausnahme. | DARF |
| R-025 | Sekundaer- und Utility-Buttons (G2/G3) SOLLEN auf `xs` als Icon-only mit `aria-label` dargestellt werden, wenn Text und Icon nicht nebeneinander passen (analog UI-NFR-017 R-040). | SOLL |
| R-026 | Im Kiosk-Modus MUESSEN Aktions-Buttons die Groessen aus UI-NFR-019 einhalten (min. 64×64px, Primaeraktion 72×72px, `size="large"`); Hamburger-/verdeckte Menues sind unzulaessig (UI-NFR-019 R-021). | MUSS |
| R-027 | Im Kiosk-Modus DARF das Overflow-Menue NICHT als einziger Zugang zu einer haeufig benoetigten Aktion dienen; benoetigte Aktionen MUESSEN direkt sichtbar sein (UI-NFR-019 R-021). Overflow ist im Kiosk nur fuer selten benoetigte Aktionen zulaessig. | MUSS |
| R-028 | Destruktive Aktionen (G5) MUESSEN im Kiosk-Modus den erhoehten Bestaetigungsaufwand aus UI-NFR-019 R-030/R-031 erfuellen (Long-Press oder zweistufiger Dialog, Mindestabstand). | MUSS |

---

## 8. Barrierefreiheit

| # | Regel | Stufe |
|---|-------|-------|
| R-029 | Die DOM-/Tab-Reihenfolge der Aktions-Zone MUSS der visuellen Reihenfolge entsprechen (UI-NFR-002 R-004): G4 → G3 → G2 → Overflow → G5 → G1. | MUSS |
| R-030 | Jeder Aktions-Button MUSS ein aussagekraeftiges, sichtbares Label oder `aria-label` haben (UI-NFR-002 R-009); Icon-only-Buttons IMMER mit `aria-label`. | MUSS |
| R-031 | Die destruktive Intention (G5) DARF NICHT allein ueber Farbe vermittelt werden; sie MUSS zusaetzlich ueber Text/`aria-label` (z.B. "Pflanze entfernen") und Icon erkennbar sein (nicht-visuelle Konvenienz, UI-NFR-002). | MUSS |
| R-032 | Das Overflow-Menue MUSS vollstaendig per Tastatur bedienbar sein (Enter/Space oeffnet, Pfeiltasten navigieren, Escape schliesst und gibt den Fokus an den `⋮`-Button zurueck — UI-NFR-002 R-003, R-006). | MUSS |
| R-033 | Der Wechsel in den Bulk-Modus (G4) MUSS ueber eine ARIA-Live-Region angekuendigt werden (UI-NFR-002 R-011), damit Screenreader-Nutzer den Moduswechsel bemerken. | MUSS |

---

## 9. Konsistenz ueber Seitentypen

Die Gruppen-Zuordnung MUSS ueber Listen-, Detail- und Formular-Seiten hinweg gleich interpretiert werden.

| Seitentyp | Typisches G1 | Typische G2/G3/G4 | Typisches G5 | UI-NFR-017-Pattern |
|-----------|--------------|-------------------|--------------|--------------------|
| Listen-/Uebersichtsseite | "+ Erstellen" | Bulk-Modus (G4), Export (G3), Filter-Toggles (als G2/IconButton) | -- | Pattern D |
| Detailseite | seitenspezifische Primaeraktion (optional) | Sekundaeraktionen (G2), Export/Druck (G3) | "Loeschen"/"Entfernen" | Pattern B/C |
| Formular-/Editier-Seite | "Speichern" (sofern im Kopf, sonst am Formular-Ende) | "Abbrechen" (G2) | -- | Pattern B |

| # | Regel | Stufe |
|---|-------|-------|
| R-034 | Dieselbe fachliche Aktion (z.B. "Loeschen") MUSS ueber alle Seiten hinweg dieselbe Gruppe, Variante und Position erhalten. | MUSS |
| R-035 | Formular-Primaeraktionen ("Speichern") gehoeren primaer an das Formular-Ende (UI-NFR-008); erscheinen sie zusaetzlich im Kopf, MUESSEN sie als G1 (`contained primary`) gefuehrt werden. | SOLL |

---

## 10. Wireframe-Uebersicht

```
Desktop — Listenseite (Pattern D)
┌────────────────────────────────────────────────────────────────────────┐
│  Aufgaben                                                                │
│                    [Mehrere auswaehlen] [⤓ PDF] [⚙ Erinnerungen] [⋮]  [+ Aufgabe]
│                     └ G4 ────────────┘ └ G3 ─┘ └ G2 ────────────┘ Ovfl   └ G1 ─┘
│  [Filter / Tabelle...]                                                   │
└────────────────────────────────────────────────────────────────────────┘

Desktop — Detailseite (Pattern C)
┌────────────────────────────────────────────────────────────────────────┐
│  Basilikum #12  ☆                     [Auf Schaedlinge pruefen] [⋮]   [🗑 Entfernen]
│  [Phase: Vegetativ] [Basilikum]        └ G2 ───────────────────┘ Ovfl   └ G5 ──────┘
│  [Details] [Bestand] [Bearbeiten]                                        │
└────────────────────────────────────────────────────────────────────────┘

Mobile (xs) — nur G1 sichtbar, Rest im Overflow
┌──────────────────────────────┐
│  Aufgaben                     │
│                  [⋮] [+ Aufg.]│
│  [Filter / Liste...]          │
└──────────────────────────────┘
```

---

## 11. Referenzbeispiele (konforme Ziel-Zustaende)

Die drei im Issue genannten Seiten werden hier als **Ziel-Zustaende nach dieser Anforderung** annotiert. Die tatsaechliche Umstellung ist Folgearbeit (Abschnitt 13).

### 11.1 Task-Queue (heute: 4× outlined + 1× contained)

- G1 Primaer: "+ Aufgabe erstellen" (`contained primary`, aussen rechts).
- G2 Sekundaer: "Erinnerungen generieren" (`outlined primary`).
- G3 Utility/Export: "Pflegecheckliste als PDF" (`text`, `DownloadIcon`).
- G4 Bulk: "Mehrere auswaehlen" (`outlined`, Toggle).
- Overflow: Da inkl. G1 vier+ Aktionen — auf Desktop bleiben G4/G3/G2 sichtbar (Schwelle 3 erreicht, grenzwertig); auf `xs` bleibt nur G1, der Rest wandert in `⋮`.

### 11.2 Pflanze fotografieren / erkennen (heute: 1× contained)

- G1 Primaer: "Pflanze fotografieren" (`contained primary`). Bereits konform — genau eine Primaeraktion, kein Overflow, keine destruktive Aktion. Dient als Muster fuer den Minimalfall.

### 11.3 Pflanzen-Detailseite (heute: outlined + text + roter Text-"Entfernen")

- G2 Sekundaer: "Auf Schaedlinge pruefen", "Phasenwechsel" (`outlined primary`).
- G2 / Overflow: "Etikett/Label", "Labels" — als G2 oder, bei Ueberschreiten der Schwelle (R-016), ins `⋮`-Menue.
- G5 Destruktiv: "Pflanze entfernen" — MUSS von rotem `text` auf `outlined color="error"` (R-010) umgestellt und rechts, getrennt von G1, platziert werden. Behebt zugleich den heutigen Verstoss gegen UI-NFR-017 R-009.

---

## 12. Akzeptanzkriterien

### Definition of Done

- [ ] Jede Seitenkopf-Aktion ist genau einer Gruppe G1-G5 zugeordnet (R-003).
- [ ] Pro Seite existiert hoechstens eine Primaeraktion (G1) und hoechstens ein sichtbarer `contained`-Button (R-004, R-009).
- [ ] Variante/Farbe folgt deterministisch aus der Gruppe (R-008); kein rotes `text`-"Entfernen" mehr (R-010).
- [ ] Reihenfolge G4 → G3 → G2 → Overflow → G5 → G1 ist eingehalten; G1 steht aussen rechts (R-012).
- [ ] Ab >3 sichtbaren Aktionen (Desktop) bzw. >1 (xs) greift das Overflow-Menue; G1 wandert nie hinein (R-016, R-017, R-024). Ein zusaetzlich sichtbares Element auf `xs` ist nur zulaessig, wenn es die Ausnahme R-024a erfuellt und diese an der Aufrufstelle begruendet ist.
- [ ] Alle Buttons erreichen 48×48px (Standard) bzw. 64/72px (Kiosk) Trefferflaeche (R-022, R-026).
- [ ] Tab-/Fokus-Reihenfolge = visuelle Reihenfolge; Overflow-Menue voll tastaturbedienbar (R-029, R-032).
- [ ] Destruktive Intention wird nicht allein ueber Farbe vermittelt (R-031).

### Pruefmatrix (Beispiel-Seiten)

| Seite | G1 | G2 | G3 | G4 | G5 | Overflow noetig |
|-------|----|----|----|----|----|-----------------|
| TaskQueuePage | + Aufgabe | Erinnerungen | PDF-Checkliste | Mehrere auswaehlen | -- | xs: ja |
| PlantIdentificationPage | Fotografieren | -- | -- | -- | -- | nein |
| PlantInstanceDetailPage | -- | Schaedlinge pruefen, Phasenwechsel | -- | -- | Entfernen | ggf. (Labels) |
| FertilizerListPage | + Erstellen | -- | Export | -- | -- | nein |

---

## 13. Nicht Teil dieser Anforderung (Folgearbeit)

Diese Anforderung spezifiziert ausschliesslich die **Regeln**. **Ausdruecklich nicht** Teil dieser Anforderung sind:

- ~~Die Umstellung bestehender Seiten auf diese Regeln ("Rolling") — sie ist eine separate Umsetzungs-Folgearbeit.~~
- ~~Die Implementierung einer gemeinsamen `PageActions`-/`ActionBar`-Komponente (heute existiert nur `PageTitle.tsx`); ihr Entwurf und Bau sind Folgearbeit.~~
- ~~Aenderungen an Anwendungscode unter `src/frontend/**` jeglicher Art.~~

**Aufgehoben am 2026-07-28 (Issue #832).** Die drei Ausschluesse oben galten,
solange der Umfang der Umstellung unbekannt war. Er wurde gemessen: Von 80
`<PageTitle>`-Vorkommen fuehren **10** mehr als eine Aktion im `action`-Slot;
37 fuehren genau eine und erfuellen R-024 damit bereits, 33 haben keinen
`action`-Slot. R-024 ist eine **MUSS**-Regel — sie auf zehn bekannten Seiten
unerfuellt zu lassen, waehrend die Behebung mechanisch ist, war der teurere
der beiden Wege.

Daher gilt ab sofort:

- Die Umstellung der betroffenen Bestandsseiten ist Teil dieser Anforderung.
- Die gemeinsame Komponente ist gebaut: `PageHeaderActions`
  (`src/frontend/src/components/layout/PageHeaderActions.tsx`). Sie nimmt die
  Primaeraktion (G1) und die Sekundaer-/Utility-Aktionen (G2/G3) als Daten
  entgegen und klappt Letztere auf `xs` in ein `⋮`-Menue ein. `PageTitle`
  bleibt unveraendert; die Komponente wird in dessen `action`-Slot gegeben.
- Aenderungen unter `src/frontend/**` sind fuer genau diesen Zweck zulaessig.

Weiterhin **nicht** Teil dieser Anforderung:

- Der Kiosk-Modus. R-027 verbietet das Overflow-Menue als einzigen Zugang zu
  haeufig benoetigten Aktionen; ein kiosktaugliches Layout ist eine eigene
  Entscheidung und wird von `PageHeaderActions` bewusst nicht geraten.
- Aktionsgruppen ausserhalb des Seitenkopfs (Karten-, Dialog- und
  Tabellenzeilen-Aktionen).

---

## 14. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Eintrittswahrscheinlichkeit |
|--------|-----------|---------------------------|
| Weiterhin individuelle Aktions-Layouts pro Seite | Hohe kognitive Last, schlechte Erlernbarkeit | Hoch (aktueller Zustand) |
| Destruktive Aktion als unauffaelliger Text-Button | Versehentliches Loeschen, Datenverlust | Mittel (heute an PlantInstanceDetailPage aufgetreten) |
| Seitenkopf laeuft auf Mobile ueber | Abgeschnittene/unerreichbare Aktionen | Hoch (ohne Overflow-Regel) |
| Mehrdeutige Handlungs-Hierarchie (mehrere `contained`-Buttons) | Nutzer erkennt Primaeraktion nicht | Mittel |
| Fehlende `aria-label`/Fokus-Reihenfolge an Kopf-Aktionen | WCAG-Verletzung, Screenreader unbedienbar | Mittel |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-07-12
**Review**: Pending
**Genehmigung**: Pending
