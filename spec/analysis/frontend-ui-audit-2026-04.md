# Frontend-UI-Audit — Kamerplanter Web-App

**Datum:** 2026-04-25
**Spec-Stand:** UI-NFR-008 v1.3 (inkl. Sektion 2.11), UI-NFR-001 v2.0, UI-NFR-010 v1.1, UI-NFR-011 v1.1, UI-NFR-017 v1.0, UI-NFR-018 v1.0, UI-NFR-002
**Methodik:** Statische Code-Analyse von `src/frontend/src/` gegen alle UI-NFR-Specs.
**Status:** Read-Only-Audit — keine Code-Änderungen durchgeführt.
**Geprüfte Dateien:** ~140 `.tsx`-Dateien (Pages + Dialoge + Shared Components)

---

## Zusammenfassung

Die Kamerplanter-Frontend-Codebasis ist funktional gut aufgestellt: Shared-Komponenten (`DataTable`, `FormRow`, `UnsavedChangesGuard`, `PageTitle`) sind vorhanden und werden von der Mehrheit der Seiten korrekt eingesetzt. Die grössten Defizite betreffen drei Bereiche: (1) **Alle 17 Detail-Seiten** verwenden `maxWidth: 900` und verstoßen damit gegen UI-NFR-008 R-053 (mind. 1280px), die als Einzige vorhandene `ActivityDetailPage` mit korrekter Implementierung ist ein gutes Referenzbeispiel. (2) **UI-NFR-018 (Origin-Chip)** ist nie vollständig implementiert worden: kein `OriginChip`-Singleton, keine Tooltips auf den bestehenden System-Chips, kein Herkunftsfilter in den Listenansichten. (3) **UI-NFR-011 (HelpTooltip)** ist vollständig absent — die Komponente existiert nicht im Codebase, und alle Fachbegriff-Felder (EC, VPD, PPFD, NPK, CalMag, GDD etc.) fehlen jede Erklärung. Top-3-Empfehlungen: (a) R-053-Rollout auf alle 17 Detail-Seiten nach dem `ActivityDetailPage`-Muster, (b) `OriginChip`-Komponente + `useOriginProtection`-Hook einmalig implementieren und in alle 17 betroffenen Seiten einhängen, (c) `HelpTooltip`-MVP (Phase 1: 8 Kernbegriffe) schnellstmöglich umsetzen.

---

## Audit-Übersicht (Compliance-Score pro Bereich)

| Bereich | Geprüfte Files | MUSS-Verstöße | SOLL-Lücken | Status |
|---------|----------------|---------------|-------------|--------|
| Detail-Seiten Stammdaten | 6 | 3–5 je Seite | mehrere | Rot |
| Detail-Seiten Düngung/Ernte | 5 | 3–5 je Seite | mehrere | Rot |
| Detail-Seiten Anbau/Standorte | 8 | 2–4 je Seite | mehrere | Rot |
| Listen-Seiten | 18 | 2–3 je Seite | mehrere | Gelb |
| Dashboard | 1 | 0 | 1 | Grün |
| Auth/Onboarding | 9 | 0–1 | wenige | Grün |
| Admin | 2 | 1 | 1 | Gelb |
| Dialoge (Create/Edit) | ~30 | 1–2 je Dialog | mehrere | Gelb |
| Phasen-Seiten | 6 | 2–3 | mehrere | Gelb |
| Aufgaben-Seiten | 7 | 2–3 | mehrere | Gelb |

---

## Befunde nach Priorität

### P1 — Blocker / Hohe Sichtbarkeit

#### F-001: `maxWidth: 900` auf allen Detail-Seiten (17 Dateien)

- **Spec:** UI-NFR-008 §2.11 R-053
- **Betroffene Pages:**
  - `pages/standorte/SiteDetailPage.tsx`
  - `pages/standorte/LocationDetailPage.tsx`
  - `pages/standorte/TankDetailPage.tsx` (Sonderfall: `maxWidth: { xs: '100%', md: 900, xl: 1100 }` — xl immer noch unter 1280)
  - `pages/standorte/SlotDetailPage.tsx`
  - `pages/standorte/SubstrateDetailPage.tsx`
  - `pages/standorte/BatchDetailPage.tsx`
  - `pages/duengung/FertilizerDetailPage.tsx`
  - `pages/duengung/NutrientPlanDetailPage.tsx`
  - `pages/duengung/FeedingEventDetailPage.tsx`
  - `pages/ernte/HarvestBatchDetailPage.tsx`
  - `pages/stammdaten/SpeciesDetailPage.tsx`
  - `pages/stammdaten/CultivarDetailPage.tsx`
  - `pages/stammdaten/BotanicalFamilyDetailPage.tsx`
  - `pages/aufgaben/TaskDetailPage.tsx` (zweimal)
  - `pages/aufgaben/WorkflowDetailPage.tsx`
  - `pages/pflanzen/PlantInstanceDetailPage.tsx` (zweimal)
  - `pages/pflanzen/LifecycleConfigSection.tsx`
- **Problem:** Das Formular-Container-`Box` verwendet durchgängig `maxWidth: 900`, was auf Viewports ab 1024px (typischer Laptop) das Layout unnötig einengt und auf grossen Monitoren (1920px+) mehr als 50% des verfügbaren Platzes ungenutzt lässt. R-053 fordert mindestens `maxWidth: 1280` auf `md+`, damit kompakte Panels horizontal nebeneinander Platz finden.
- **Referenzimplementierung:** `pages/stammdaten/ActivityDetailPage.tsx` (die einzige konforme Seite) verwendet `FORM_MAX_WIDTH = 1280` und ein `gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 760px) 1fr' }` Master-Detail-Layout.
- **Empfohlene Lösung:** `maxWidth: 900` → `maxWidth: 1280` (oder eine breakpoint-variable Konstante `FORM_MAX_WIDTH`). Gleichzeitig für Seiten mit Fließtextfeldern (Beschreibungen, Notizen) nach ActivityDetailPage-Muster Master-Detail-Grid einführen: linke Spalte (760px) für Identifikation + Fließtext, rechte Spalte für kompakte Panels (Klassifizierung, Werte, Einstellungen).
- **Geschätzter Aufwand:** M–L (30–90 min je Seite, abhängig von Anzahl Panels)
- **Selenium-Verifizierbar:** Ja — Screenshot-Vergleich auf 1920×1080 Viewport vor/nach zeigt deutlichen Unterschied im Whitespace-Anteil.

---

#### F-002: Keine `OriginChip`-Komponente, keine vollständige UI-NFR-018-Implementierung

- **Spec:** UI-NFR-018 §4.1 R-001 (MUSS), §4.2 R-006 (MUSS), §4.3 R-009 (MUSS), §4.4 R-011–R-013 (MUSS), §4.5 R-016 (MUSS), §5.1 R-023 (MUSS)
- **Betroffene Pages (laut Prüfmatrix UI-NFR-018 §7):**
  - `pages/stammdaten/SpeciesDetailPage.tsx` — kein Origin-Chip (kein `origin`-Feld vorhanden)
  - `pages/stammdaten/SpeciesListPage.tsx` — kein Origin-Filter, kein Herkunfts-Chip in Spalten
  - `pages/duengung/FertilizerDetailPage.tsx` — kein Origin-Chip
  - `pages/duengung/FertilizerListPage.tsx` — kein Origin-Filter
  - `pages/duengung/NutrientPlanDetailPage.tsx` — kein Origin-Chip
  - `pages/duengung/NutrientPlanListPage.tsx` — kein Origin-Filter
  - `pages/pflanzenschutz/PestListPage.tsx`, `DiseaseListPage.tsx`, `TreatmentListPage.tsx` — kein Origin-Filter
  - `pages/aufgaben/WorkflowDetailPage.tsx` — System-Chip vorhanden (`Chip label={t('pages.tasks.systemWorkflow')}`) aber: kein `SettingsIcon`, kein Tooltip, nicht `size="small"` laut Spec, nicht als `OriginChip`-Komponente
  - `pages/aufgaben/WorkflowTemplateListPage.tsx` — System-Chip vorhanden aber ohne Tooltip, kein Origin-Filter
  - `pages/phasen/PhaseSequenceDetailPage.tsx` — System-Chip vorhanden (`is_system`) aber ohne Tooltip, Icon fehlt
  - `pages/phasen/PhaseSequenceListPage.tsx` — System-Chip vorhanden ohne Tooltip, kein Origin-Filter
  - `pages/phasen/PhaseDefinitionDetailPage.tsx` — System-Chip vorhanden ohne Tooltip
  - `pages/phasen/PhaseDefinitionListPage.tsx` — System-Chip ohne Tooltip, kein Origin-Filter
  - `pages/stammdaten/ActivityDetailPage.tsx` — System-Chip vorhanden (kein Tooltip)
  - `pages/stammdaten/ActivityListPage.tsx` — Ja/Nein-Label statt `OriginChip`, kein Filter
- **Problem:** (a) Die zentrale `OriginChip`-Komponente aus §5.1 existiert nicht. Stattdessen gibt es je nach Seite unterschiedliche Ad-hoc-Implementierungen: Workflow hat `color="info"`, Phasen haben `color="info"`, ActivityList zeigt Ja/Nein. (b) Kein einziger bestehender System-Chip hat einen erklärenden Tooltip (R-009 MUSS). (c) Kein einziger System-Chip enthält ein Icon (R-005 MUSS). (d) i18n-Keys `common.origin.*` fehlen komplett in `de/translation.json` und `en/translation.json`. (e) Kein einziger Herkunfts-Filter in Listenansichten.
- **Empfohlene Lösung:** `OriginChip`-Komponente in `src/frontend/src/components/common/OriginChip.tsx` implementieren (Props: `origin?: 'system'|'enrichment'|'import'|'tenant'`, `isSystem?: boolean`). `useOriginProtection`-Hook in `src/frontend/src/hooks/useOriginProtection.ts`. i18n-Keys `common.origin.*` in beiden Sprachdateien ergänzen. Dann alle 17 Seiten der Prüfmatrix einbinden.
- **Geschätzter Aufwand:** L (90+ min Gesamtaufwand: ~60 min Komponente + Hook + i18n, dann ~2 min je Seite)
- **Selenium-Verifizierbar:** Ja — Screenshot der WorkflowDetailPage zeigt korrekten Chip mit Icon; E2E-Test prüft ob Edit/Delete-Button bei `is_system=true` ausgeblendet ist.

---

#### F-003: `HelpTooltip`-Komponente fehlt vollständig — alle Fachbegriff-Felder ohne Erklärung

- **Spec:** UI-NFR-011 §2.2 (MUSS für alle Fachbegriff-Felder), UI-NFR-008 R-042–R-046 (MUSS)
- **Betroffene Pages (Auswahl):**
  - `pages/duengung/FertilizerDetailPage.tsx` — EC, NPK, mixing_priority ohne HelpTooltip
  - `pages/duengung/NutrientPlanDetailPage.tsx` — EC, pH, Substrattyp ohne HelpTooltip
  - `pages/duengung/NutrientCalculationsPage.tsx` — EC, pH, CalMag, Flushing ohne HelpTooltip (hat immerhin helperText)
  - `pages/pflanzen/ProfileEditDialog.tsx` — EC, pH, VPD, PPFD ohne HelpTooltip (hat helperText-Werte, aber kein ausfaltbarer Tooltip)
  - `pages/standorte/TankDetailPage.tsx` — EC (mS/cm) als Tabellenspalten-Header ohne HelpTooltip
  - `pages/standorte/TankStateCreateDialog.tsx` — pH/EC-Felder ohne HelpTooltip (haben kein helperText)
  - `pages/pflanzenschutz/PestListPage.tsx`, `TreatmentListPage.tsx` — Fachbegriff-Spalten ohne HelpTooltip
  - `pages/stammdaten/SpeciesDetailPage.tsx` — GDD, VPD-Felder ohne HelpTooltip
  - Alle restlichen ~110 Dateien
- **Problem:** Die `HelpTooltip`-Komponente aus UI-NFR-011 §4 existiert nicht im Codebase. Das Glossar-Namespace (`glossary.*`) fehlt in beiden i18n-Dateien. Einige Seiten haben `helperText` mit Wertebereichen (z.B. `ProfileEditDialog` mit `"0.8–1.5 kPa"`), was als Minimalmassnahme akzeptabel ist, aber den vollständigen Tooltip mit `short`/`long`/`beginnerTip`/Glossar-Verlinkung nicht ersetzt. Fachbegriffe wie EC, VPD, PPFD, NPK, CalMag, GDD, CEC werden auf 8+ zentralen Seiten ohne jede Erklärung angezeigt.
- **Empfohlene Lösung:** Phase-1-MVP gemäss UI-NFR-011 §8: `HelpTooltip`-Komponente in `src/frontend/src/components/shared/HelpTooltip.tsx`, `glossary.de.json` + `glossary.en.json` mit mindestens 8 Kernbegriffen (EC, pH, VPD, PPFD, NPK, CalMag, GDD, DLI), Integration in NutrientPlanDetailPage, FertilizerDetailPage, NutrientCalculationsPage.
- **Geschätzter Aufwand:** L (>90 min für MVP: ~60 min Komponente + Glossar-JSON, ~15 min je Seite für Integration)
- **Selenium-Verifizierbar:** Ja — E2E-Test: Hover auf EC-Label in FertilizerDetailPage → Tooltip erscheint. Screenshot vor/nach.

---

### P2 — Wichtig

#### F-004: Pattern C (UI-NFR-017) — Titel und Chips in derselben Flex-Row

- **Spec:** UI-NFR-017 §3.3 R-010 (MUSS), R-024 (MUSS)
- **Betroffene Pages:**
  - `pages/duengung/NutrientPlanDetailPage.tsx` — `PageTitle` + `is_template`-Chip + Favoriten-Icon in **einer** Flex-Row (`display: 'flex', alignItems: 'center'`)
  - `pages/durchlaeufe/PlantingRunDetailPage.tsx` — `PageTitle` + Status-Chip + Edit-IconButton in **einer** Flex-Row
  - `pages/ernte/HarvestBatchDetailPage.tsx` — `PageTitle` mit `action`-Prop gesetzt auf ein `Chip`-Element — der `PageTitle`-`action`-Prop setzt Titel und Action in denselben Flex-Container
- **Nicht betroffen (korrekt implementiert):**
  - `pages/duengung/FertilizerDetailPage.tsx` — korrekte 2-Zeilen-Implementierung (Titel-Zeile + Meta-Zeile separat)
- **Problem:** R-010 und R-024 fordern explizit, dass `h4`-Titel und `small`-Chips **nicht** in derselben Flex-Row stehen, da der Grössenunterschied (`h4` ~34px, Chip ~24px) eine saubere vertikale Ausrichtung verhindert. Für die `ernte/HarvestBatchDetailPage.tsx` ist der PageTitle-eigene `action`-Prop das Problem: der aktuelle `PageTitle`-Code rendert Titel und Action auf `alignItems: 'center'` in einer Row.
- **Empfohlene Lösung:** Für betroffene Seiten eigene Pattern-C-Implementierung (2 Box-Zeilen) statt `PageTitle.action`-Prop für Chips. Alternativ: PageTitle-Komponente um separaten `meta`-Prop erweitern, der eine zweite Zeile rendert.
- **Geschätzter Aufwand:** S (15–20 min je Seite)
- **Selenium-Verifizierbar:** Eingeschränkt — visueller Screenshot-Vergleich zeigt ob Chips auf Höhe der Unterkante des Titeltexts hängen.

---

#### F-005: Drei Listen-Seiten verwenden `<Table>` statt `DataTable` (UI-NFR-010 R-037)

- **Spec:** UI-NFR-010 §2.10 R-037 (MUSS)
- **Betroffene Pages:**
  - `pages/phasen/PhaseDefinitionListPage.tsx` — vollständige benutzerdefinierte `<Table>`-Implementierung ohne `DataTable`
  - `pages/phasen/PhaseSequenceListPage.tsx` — vollständige benutzerdefinierte `<Table>`-Implementierung ohne `DataTable`
  - `pages/standorte/WateringEventListPage.tsx` — hybride Implementierung: äusserer `DataTable` mit `<Table>` für Expansion-Row-Details
- **Problem:** Die Phasen-Listen-Seiten implementieren Sortierung, Suche und Leerzustände komplett eigenständig statt die zentrale `DataTable`-Komponente zu nutzen. Konkret fehlen dadurch: URL-Persistenz (R-016–R-018), sticky Header (R-023), standardisiertes Skeleton-Loading (R-029), einheitliche Pagination (R-011), Mobile-Card-Ansicht (R-021). `WateringEventListPage` nutzt `DataTable` für die Haupttabelle aber eine Raw-`<Table>` für Expansion-Details — das ist ein Grenzfall (kein Vollverstoss, aber inkonsistent).
- **Empfohlene Lösung:** PhaseDefinitionListPage und PhaseSequenceListPage auf `DataTable`-Pattern migrieren. WateringEventListPage Expansion-Detail-Table ist akzeptabel als Detail-Ansicht (nicht als Primärtabelle).
- **Geschätzter Aufwand:** M (45–60 min je Seite)
- **Selenium-Verifizierbar:** Ja — E2E-Test: Suchfeld vorhanden, URL-Parameter nach Filter setzen.

---

#### F-006: Unicode-Escape-Verletzungen (R-049) in 53 Dateien

- **Spec:** UI-NFR-008 §2.8 R-049 (MUSS)
- **Betroffene Dateien (Auswahl, gesamt 53 Dateien):**
  - `pages/giessprotokoll/WateringLogListPage.tsx` — 6 Vorkommen (`'—'`, `'—'` als Leerwert)
  - `pages/ernte/HarvestBatchDetailPage.tsx` — 10 Vorkommen
  - `pages/standorte/LocationDetailPage.tsx` — 4 Vorkommen (`'—'`, `'m²'`)
  - `pages/phasen/PhaseDefinitionDetailPage.tsx` — 5 Vorkommen
  - `pages/pflanzen/PlantInstanceListPage.tsx` — 9 Vorkommen
  - `pages/duengung/FeedingEventDetailPage.tsx` — 6 Vorkommen
  - `pages/stammdaten/SpeciesDetailPage.tsx` — 5 Vorkommen
  - `pages/durchlaeufe/PlantingRunDetailPage.tsx` — 5 Vorkommen
  - 45 weitere Dateien mit 1–4 Vorkommen
- **Häufigste Muster:**
  - `'—'` → sollte `'—'` sein (Leerwert-Geviertstrich)
  - `'m²'` → sollte `'m²'` sein (Flächeneinheit)
  - `'°C'` → sollte `'°C'` sein (Temperatureinheit)
  - `'μmol/m²/s'` → sollte `'µmol/m²/s'` sein
- **Empfohlene Lösung:** Globales `sed`-/IDE-Replace auf die häufigsten Escapes. Priorität: `—` → `—` (am häufigsten, da Leerwert-Pattern) und Unit-Escapes.
- **Geschätzter Aufwand:** S (< 30 min mit Batch-Replace)
- **Selenium-Verifizierbar:** Eingeschränkt — Rendering ist identisch, jedoch Code-Review-Blocker gemäss Spec.

---

#### F-007: Keine URL-Persistenz für Filter/Sortierung auf fast allen Listen-Seiten

- **Spec:** UI-NFR-010 §2.4 R-016–R-018 (MUSS)
- **Konforme Seiten (mit `useSearchParams`):**
  - `pages/stammdaten/SpeciesListPage.tsx` — hat `useSearchParams` für Family-Filter
  - `pages/tenants/InvitationAcceptPage.tsx` — Sonderfall (Token in URL)
- **Nicht konforme Listen-Seiten (ALLE anderen, ca. 17 Seiten):**
  - `pages/duengung/FertilizerListPage.tsx`
  - `pages/duengung/NutrientPlanListPage.tsx`
  - `pages/duengung/FeedingEventListPage.tsx`
  - `pages/pflanzenschutz/PestListPage.tsx`, `DiseaseListPage.tsx`, `TreatmentListPage.tsx`
  - `pages/ernte/HarvestBatchListPage.tsx`
  - `pages/stammdaten/ActivityListPage.tsx`, `BotanicalFamilyListPage.tsx`
  - `pages/pflanzen/PlantInstanceListPage.tsx`
  - `pages/standorte/SiteListPage.tsx`, `SubstrateListPage.tsx`, `TankListPage.tsx`
  - `pages/giessprotokoll/WateringLogListPage.tsx`
  - `pages/durchlaeufe/PlantingRunListPage.tsx`
  - `pages/aufgaben/WorkflowTemplateListPage.tsx`
  - `pages/aufgaben/TaskQueuePage.tsx`
- **Problem:** Filter- und Sortierzustände werden im lokalen React-State gehalten und gehen bei Navigation verloren. Gefilterte Ansichten sind nicht über URL teilbar.
- **Empfohlene Lösung:** `useSearchParams`-Hook für Suchbegriff, aktive Filter und Sortierung in der `DataTable`-Wrapper-Schicht oder pro Seite. Alternativ Zentralisierung im `DataTable`-Komponent selbst.
- **Geschätzter Aufwand:** M–L (30–60 min je Seite oder einmalig in DataTable-Komponente)
- **Selenium-Verifizierbar:** Ja — E2E: Filter setzen, URL kopieren, neu laden → Filter muss wiederhergestellt sein.

---

#### F-008: Fehlende Panel-Einleitungstexte (R-038) auf mehreren Detail-Seiten

- **Spec:** UI-NFR-008 §2.6 R-038 (MUSS)
- **Betroffene Pages:**
  - `pages/standorte/SiteDetailPage.tsx` — Cards haben `h6`-Titel aber keinen `Typography variant="body2"` Einleitungstext
  - `pages/standorte/SubstrateDetailPage.tsx` — 4 Panels ohne Einleitungstext
  - `pages/duengung/FertilizerDetailPage.tsx` — Panels ohne Einleitungstext (nur Titel)
  - `pages/duengung/NutrientPlanDetailPage.tsx` — Panels ohne Einleitungstext
  - `pages/stammdaten/CultivarDetailPage.tsx` — Panels ohne Einleitungstext
  - `pages/standorte/LocationDetailPage.tsx` — Panels ohne Einleitungstext
  - `pages/ernte/HarvestBatchDetailPage.tsx` — Panels ohne Einleitungstext
- **Nicht betroffen (korrekt):**
  - `pages/stammdaten/SpeciesDetailPage.tsx` — Hat `editIntro`-Text über dem Formular
  - `pages/stammdaten/ActivityDetailPage.tsx` — Hat Einleitungstexte in Panels
- **Problem:** Panels haben Überschrift (`h6`) aber keinen erklärenden Einleitungstext. Für Einsteiger ist unklar, was z.B. das Panel "Nährstoffe" in einem Substrat-Formular bedeutet.
- **Empfohlene Lösung:** Unter jedem Panel-`Typography variant="h6"` einen `Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}` mit praxisnahem Einleitungstext (max. 1–2 Sätze) hinzufügen. i18n-Keys `pages.<page>.section<Name>Intro` in DE + EN.
- **Geschätzter Aufwand:** S (20–30 min je Seite)
- **Selenium-Verifizierbar:** Eingeschränkt — Screenshot vor/nach zeigt ob Text erscheint.

---

#### F-009: Phasen-Detail-Seiten fehlt `UnsavedChangesGuard`

- **Spec:** UI-NFR-008 §2.2 R-007 (MUSS)
- **Betroffene Pages:**
  - `pages/aufgaben/ActivityPlanDetailPage.tsx`
  - `pages/phasen/PhaseDefinitionDetailPage.tsx`
  - `pages/phasen/PhaseSequenceDetailPage.tsx`
- **Problem:** Diese drei Detail-Seiten enthalten editierbare Formulare, haben aber keinen `UnsavedChangesGuard`. Nutzer können ungespeicherte Änderungen durch Navigation verlieren ohne Warnung.
- **Empfohlene Lösung:** `UnsavedChangesGuard dirty={isDirty}` wie bei allen anderen Detail-Seiten hinzufügen. Voraussetzung: `isDirty` aus `useForm`/`useFormState` ableiten.
- **Geschätzter Aufwand:** S (< 30 min je Seite)
- **Selenium-Verifizierbar:** Ja — E2E: Feld ändern ohne Speichern, zurücknavigieren → Dialog erscheint.

---

#### F-010: Fehlende i18n-Keys für UI-NFR-018 (`common.origin.*`)

- **Spec:** UI-NFR-018 §6 R-007 (MUSS)
- **Betroffene Dateien:**
  - `src/frontend/src/i18n/locales/de/translation.json` — `common.origin.*` fehlt komplett
  - `src/frontend/src/i18n/locales/en/translation.json` — `common.origin.*` fehlt komplett
- **Problem:** Die i18n-Keys `common.origin.system`, `common.origin.enrichment`, `common.origin.import`, `common.origin.tooltipSystem` etc. aus UI-NFR-018 §6 sind in keiner Sprachdatei vorhanden. Ohne diese kann die `OriginChip`-Komponente (F-002) nicht korrekt lokalisiert werden.
- **Empfohlene Lösung:** Keys gemäss der vollständigen Liste in UI-NFR-018 §6 in beide Sprachdateien eintragen.
- **Geschätzter Aufwand:** S (< 15 min)
- **Selenium-Verifizierbar:** Nein (Unit-Test für i18n-Vollständigkeit empfohlen)

---

#### F-011: Hardcodierte deutsche Validierungsmeldung in 2 Dateien

- **Spec:** UI-NFR-007 (Internationalisierung) — alle sichtbaren Texte über `t()`
- **Betroffene Dateien:**
  - `pages/stammdaten/BotanicalFamilyDetailPage.tsx:45` — `message: "Muss auf '-aceae' enden"`
  - `pages/stammdaten/BotanicalFamilyCreateDialog.tsx:29` — `message: "Muss auf '-aceae' enden"`
- **Problem:** Zod-Validierungsmeldung ist hartcodiert auf Deutsch. In der EN-Spracheinstellung erscheint trotzdem die deutsche Meldung.
- **Empfohlene Lösung:** `message: t('pages.botanicalFamilies.mustEndWithAceae')` oder via Zod-`.refine()` mit Zod-i18n-Adapter. i18n-Key in DE + EN ergänzen.
- **Geschätzter Aufwand:** S (< 15 min)
- **Selenium-Verifizierbar:** Ja — E2E: Ungültige Familie eingeben bei EN-Spracheinstellung → Meldung muss englisch erscheinen.

---

### P3 — Nice-to-have / Konsistenz

#### F-012: Fehlende Breadcrumb-Eintragung für `/aufgaben/activity-plans`

- **Spec:** UI-NFR-005 (Navigation), CLAUDE.md-Checkliste Breadcrumbs
- **Betroffene Datei:** `src/frontend/src/routes/breadcrumbs.ts`
- **Problem:** Route `/aufgaben/activity-plans` (→ `ActivityPlanOverviewPage`) und `/aufgaben/activity-plans/:speciesKey` (→ `ActivityPlanDetailPage`) sind in `AppRoutes.tsx` definiert, aber fehlen in `breadcrumbMap`. Nutzer auf diesen Seiten sehen keine Breadcrumbs.
- **Empfohlene Lösung:**
  ```typescript
  '/aufgaben/activity-plans': { label: 'nav.activityPlans', parent: '/dashboard' }
  ```
  sowie i18n-Key `nav.activityPlans` in DE + EN.
- **Geschätzter Aufwand:** S (< 10 min)
- **Selenium-Verifizierbar:** Ja — Screenshot der `/aufgaben/activity-plans`-Seite zeigt Breadcrumb-Leiste.

---

#### F-013: `ImportPage` verwendet manuelles `Typography h4` statt `PageTitle`

- **Spec:** UI-NFR-017 §2.1 R-001 (MUSS)
- **Betroffene Datei:** `pages/stammdaten/ImportPage.tsx:95`
- **Problem:** `<Typography variant="h4" component="h1" gutterBottom>` statt `<PageTitle title={...} />`. Dadurch kein `document.title`-Update, keine `data-testid="page-title"`.
- **Empfohlene Lösung:** Durch `<PageTitle title={t('pages.import.title')} />` ersetzen.
- **Geschätzter Aufwand:** S (< 10 min)
- **Selenium-Verifizierbar:** Ja — `document.title` im Browser-Tab.

---

#### F-014: Inkongruente Empty-Value-Darstellung (3 Muster gleichzeitig)

- **Spec:** Checkliste Darstellungs-Usability (einheitlich `—`)
- **Betroffene Dateien:** Querfeld — betrifft ~40 Dateien
- **Problem:** Im Codebase existieren gleichzeitig: `'—'` (Unicode-Escape), `'—'` (direktes UTF-8), `'N/A'`, `'-'`, `null` als Leerwert-Darstellung. Die häufigste Form `'—'` ist zugleich ein R-049-Verstoss.
- **Empfohlene Lösung:** Globales Replace zu `'—'` (direkte UTF-8-Zeichen). Ggf. zentrale Hilfsfunktion `emptyValue()` oder Konstante `EMPTY_VALUE = '—'`.
- **Geschätzter Aufwand:** S (Batch-Replace)
- **Selenium-Verifizierbar:** Eingeschränkt

---

#### F-015: Keine URL-Filter-Persistenz auf den meisten Listen-Seiten (SOLL aus UI-NFR-010)

Redundant zu F-007, bereits erfasst als P2.

---

#### F-016: `TankDetailPage.tsx` Spaltenheader `'EC (mS/cm)'` direkt hardcodiert statt via `t()`

- **Spec:** UI-NFR-007 (Internationalisierung)
- **Betroffene Datei:** `pages/standorte/TankDetailPage.tsx:371` — `{ id: 'ec', label: 'EC (mS/cm)', ... }`; `pages/standorte/TankDetailPage.tsx:1073` — `{ id: 'ec', label: 'EC (mS/cm)', ...}` und `{ label: 'EC (mS/cm)' }` in Mobile-Card
- **Problem:** Diese Spaltentitel sind nicht über `t()` lokalisiert. Damit schlägt jede i18n-Umschaltung fehl.
- **Empfohlene Lösung:** `label: t('pages.tanks.ecHeader')` und i18n-Key eintragen.
- **Geschätzter Aufwand:** S (< 15 min)
- **Selenium-Verifizierbar:** Ja — EN-Sprachwechsel, Spaltenheader prüfen.

---

#### F-017: PageTitle `action`-Prop rendert Titel und Action auf derselben `alignItems: 'center'`-Zeile — keine Unterstützung für Pattern-C-Meta-Zeile

- **Spec:** UI-NFR-017 §3.3 R-010–R-012
- **Betroffene Datei:** `src/frontend/src/components/layout/PageTitle.tsx`
- **Problem:** Das `action`-Prop platziert beliebige Elemente (inkl. Chips) in der Titel-Zeile. Pattern C erfordert eine separate zweite Zeile für Meta-Chips. Seiten, die Chips als `action`-Prop übergeben (z.B. `HarvestBatchDetailPage`), verstoßen daher gegen R-010/R-024. Die Komponente selbst müsste ein optionales `meta`-Prop bekommen, das eine zweite Zeile rendert.
- **Empfohlene Lösung:** `PageTitle` um `meta?: ReactNode`-Prop erweitern (zweite Flex-Zeile mit `mt: 0.5, alignItems: 'center', flexWrap: 'wrap'`). Betroffene Seiten auf `meta`-Prop umstellen.
- **Geschätzter Aufwand:** S (< 30 min für Komponente + Seiten-Migration)
- **Selenium-Verifizierbar:** Eingeschränkt — visueller Vergleich

---

#### F-018: Fehlende `data-testid` auf mehreren interaktiven Elementen

- **Spec:** Accessibility-Checkliste (UI-NFR-002 ergänzend)
- **Problem:** Zwar 503 vorhandene `data-testid`-Attribute — gut. Aber einzelne kritische Aktionen haben keines: z.B. IconButtons ohne Text in Phasen-Seiten. Kein systematisches Scan durchgeführt.
- **Geschätzter Aufwand:** S–M (nach Bedarf)
- **Selenium-Verifizierbar:** Direkt durch Selenium-Selektoren

---

## Empfohlene Refactor-Reihenfolge

1. **Bundle 1: R-053-Rollout + Panel-Einleitungstexte (F-001 + F-008)** — Top-5 meist genutzte Seiten: `FertilizerDetailPage`, `SpeciesDetailPage`, `NutrientPlanDetailPage`, `SiteDetailPage`, `PlantInstanceDetailPage`. Nach ActivityDetailPage-Muster: `FORM_MAX_WIDTH=1280`, Master-Detail-Grid für Seiten mit Fließtext, kompakte Panels in 2-Spalten-Grid. Gleichzeitig Einleitungstexte für alle Panels ergänzen. Aufwand: ~6–8h Gesamt.

2. **Bundle 2: OriginChip + i18n-Keys (F-002 + F-010)** — Einmalige Komponente `OriginChip.tsx` + Hook `useOriginProtection.ts` + i18n-Keys (`common.origin.*`). Dann sukzessiv in alle 17 Seiten einhängen. Aufwand: ~2h Grundkomponente + ~30 min für alle 17 Seiten.

3. **Bundle 3: HelpTooltip MVP (F-003)** — `HelpTooltip`-Komponente, `glossary.de.json`/`glossary.en.json` mit 8 Pflichtbegriffen, Integration in NutrientPlanDetailPage + FertilizerDetailPage + NutrientCalculationsPage. Aufwand: ~3–4h.

4. **Bundle 4: Unicode-Escapes + Hardcoded Strings (F-006 + F-011 + F-016)** — Batch-Replace, Aufwand < 1h.

5. **Bundle 5: UnsavedChangesGuard (F-009)** — 3 Seiten, Aufwand ~45 min.

6. **Bundle 6: Phasen-Listen auf DataTable migrieren (F-005)** — PhaseDefinitionListPage + PhaseSequenceListPage, Aufwand ~2h.

7. **Bundle 7: Pattern C Korrekturen (F-004 + F-017)** — PageTitle-Komponente erweitern, 3 Seiten anpassen, Aufwand ~1h.

8. **Bundle 8: URL-Persistenz (F-007)** — Systematisch für alle Liste-Seiten, am besten in DataTable-Komponente zentralisiert. Aufwand: L (>1 Arbeitstag).

---

## Anhang A: Vollständige Liste R-053-Verstösse (`maxWidth: 900`)

| Datei | Aktuelles maxWidth | Zeile(n) |
|-------|-------------------|----------|
| `pages/standorte/BatchDetailPage.tsx` | `900` | 118 |
| `pages/standorte/LocationDetailPage.tsx` | `900` | 324 |
| `pages/standorte/SiteDetailPage.tsx` | `900` | 168 |
| `pages/standorte/SubstrateDetailPage.tsx` | `900` | 256 |
| `pages/standorte/SlotDetailPage.tsx` | `900` | 105 |
| `pages/standorte/TankDetailPage.tsx` | `{ xs:'100%', md:900, xl:1100 }` | 1104 |
| `pages/aufgaben/WorkflowDetailPage.tsx` | `900` | 1169 |
| `pages/aufgaben/TaskDetailPage.tsx` | `900` | 920, 1169 |
| `pages/duengung/FeedingEventDetailPage.tsx` | `900` | 336 |
| `pages/duengung/NutrientPlanDetailPage.tsx` | `900` | 1228 |
| `pages/duengung/FertilizerDetailPage.tsx` | `900` | 829 |
| `pages/ernte/HarvestBatchDetailPage.tsx` | `900` | 506, 660, 738 |
| `pages/stammdaten/BotanicalFamilyDetailPage.tsx` | `900` | 228 |
| `pages/stammdaten/CultivarDetailPage.tsx` | `900` | 258 |
| `pages/stammdaten/SpeciesDetailPage.tsx` | `900` | 390 |
| `pages/pflanzen/PlantInstanceDetailPage.tsx` | `900` | 1792, 2148 |
| `pages/pflanzen/LifecycleConfigSection.tsx` | `900` | 118 |

**Konforme Seite (Referenz):**

| Datei | maxWidth | Anmerkung |
|-------|---------|-----------|
| `pages/stammdaten/ActivityDetailPage.tsx` | `FORM_MAX_WIDTH = 1280` | Master-Detail-Grid, READING_COL_MAX = 760, vollständig konform |

---

## Anhang B: R-054/R-055-Verstösse (Fließtext ohne maxWidth 760)

| Datei | Feld | minRows | maxWidth-Constraint vorhanden? |
|-------|------|---------|-------------------------------|
| `pages/stammdaten/ActivityDetailPage.tsx` | `description`, `description_de` | 4 | Ja (`Box maxWidth: READING_COL_MAX`) — konform |
| `pages/duengung/NutrientPlanDetailPage.tsx` | notes-Feld (l.1253) | 3 | Nein |
| `pages/giessprotokoll/WateringLogDetailPage.tsx` | notes-Feld (l.580) | 3 | Nein |
| `pages/durchlaeufe/PlantingRunEditDialog.tsx` | notes-Feld (l.174) | 3 | Dialog-intern, akzeptabel |
| `pages/auth/NotificationSettingsTab.tsx` | template-Feld (l.398) | 3 | Nein |
| `pages/admin/AdminEditTenantPage.tsx` | notes-Feld (l.237) | 3 | Nein |

Hinweis: `minRows={3}` liegt unter dem in R-054 genannten Schwellenwert `minRows >= 4`, ist aber dennoch ein Fließtextfeld und sollte idealerweise das 760px-Limit erhalten. Pflicht-R-054 gilt streng ab `minRows >= 4` — nur `ActivityDetailPage.tsx`-Felder sind betroffen.

---

## Anhang C: Pages ohne `UnsavedChangesGuard`

| Datei | Hat Formular? | Hat Guard? |
|-------|--------------|-----------|
| `pages/aufgaben/ActivityPlanDetailPage.tsx` | Ja | Nein |
| `pages/phasen/PhaseDefinitionDetailPage.tsx` | Ja (bedingt, da `is_system`-Schutz) | Nein |
| `pages/phasen/PhaseSequenceDetailPage.tsx` | Ja | Nein |
| Alle anderen Detail-Pages | Ja | Ja (korrekt) |

---

## Anhang D: Hardcoded Strings / i18n-Verletzungen

| Datei | Zeile | Hardcoded String | Empfehlung |
|-------|-------|-----------------|-----------|
| `pages/stammdaten/BotanicalFamilyDetailPage.tsx` | 45 | `"Muss auf '-aceae' enden"` | `t('pages.botanicalFamilies.mustEndWithAceae')` |
| `pages/stammdaten/BotanicalFamilyCreateDialog.tsx` | 29 | `"Muss auf '-aceae' enden"` | `t('pages.botanicalFamilies.mustEndWithAceae')` |
| `pages/standorte/TankDetailPage.tsx` | 371, 1073, 1088 | `'EC (mS/cm)'` | `t('pages.tanks.ecHeader')` |
| `pages/pflanzen/ProfileEditDialog.tsx` | 199–200 | `label="EC"`, `label="pH"` | `t('pages.profiles.ecLabel')`, `t('pages.profiles.phLabel')` |

---

## Nicht geprüft / Einschränkungen

- **Barrierefreiheit (WCAG 2.1 kontrastprüfung):** Kontrast-Checks (UI-NFR-002 §3) erfordern visuelles Rendering und wurden nicht durchgeführt. Empfehlung: axe-core oder Lighthouse Accessibility Audit.
- **Responsive Verhalten auf echter Hardware:** Breakpoint-Korrektheit wurde durch Code-Analyse geprüft, nicht durch visuelles Mobile-Testing. Insbesondere die `xs`-Darstellung der Phasen-Seiten mit Custom-Table-Implementierung (keine MobileCard) ist ungeprüft.
- **UI-NFR-003 (Performance / Lazy Loading / Memoization):** Nicht im Scope dieses Audits.
- **UI-NFR-012 (PWA/Offline):** Nicht geprüft.
- **UI-NFR-013 (Consent):** Nicht geprüft.
- **UI-NFR-016 (Phasen-Diagramme):** Nicht geprüft (separate Visualisierungs-Spec).
- **DashboardPage:** Nur oberflächlich geprüft (keine schwerwiegenden Mängel festgestellt).
- **~20 Dialog-Dateien** (`*CreateDialog.tsx`): Stichprobenartig geprüft (FertilizerCreateDialog, SpeciesCreateDialog, TankFillCreateDialog). Hauptbefund: fehlende `inputMode` + fehlende HelpTooltip-Integration. Vollständige Einzeldokumentation aller ~30 Dialoge würde Audit-Scope sprengen.
