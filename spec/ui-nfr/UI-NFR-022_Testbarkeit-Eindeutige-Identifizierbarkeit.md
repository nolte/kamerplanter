---

ID: UI-NFR-022
Titel: Testbarkeit & eindeutige Identifizierbarkeit (E2E)
Kategorie: UI-Verhalten Unterkategorie: Testbarkeit, E2E-Automatisierung, stabile Selektoren
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.25
Autor: Business Analyst - Agrotech
Datum: 2026-11-12
Tags: [testability, e2e, selenium, data-testid, selektoren, page-object, automation]
Abhängigkeiten: [UI-NFR-002, UI-NFR-005, UI-NFR-008, UI-NFR-017]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-022: Testbarkeit & eindeutige Identifizierbarkeit (E2E)

### Änderungshistorie

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.25 | 2026-11-13 | §2.5.1: Kennungen des Werkzeugs „Bereich“ (REQ-053 GP-UX-071, Issue #2913) registriert, darunter `garden-plan-tool-area` und `garden-plan-new-area-type-rule`. |
| 1.24 | 2026-11-12 | §2.5.1: `garden-plan-tool-<tool>` mit seinen Werten (select, pan, bed, garden_object, measure) und die Touch-Kennungen `garden-plan-touch-*` nachregistriert; neu für das Werkzeug „Messen“ (REQ-053 GP-UX-071, Issue #2913): `garden-plan-measure-status`, `garden-plan-measure` / `-line` / `-segment` / `-total`, `garden-plan-measure-place` / `-finish`. |
| 1.23 | 2026-11-12 | §2.5.1: „Meine Position“ im Tab Karte des Feldmodus (REQ-053 GP-UX-026, Issue #2898) registriert: der Abschnitt `field-mode-position`, der Schalter `field-mode-position-switch` (natives Eingabefeld, `role="switch"`), die Beschreibung `field-mode-position-description`, der Hinweis `field-mode-position-hint` mit dem qualifizierenden Attribut `data-reason` (`locating`, `denied`, `unavailable`, `timeout`, `site_loading`, `site_error`, `no_gps`, `far`, `outside_view`, `coarse`), die Überlagerung `field-mode-position-dot` (`data-accuracy-m`) mit dem Genauigkeitskreis `field-mode-position-accuracy`. Keine bestehende Kennung umbenannt (R-021); die Page Objects brauchen keine Anpassung. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.22 | 2026-11-12 | §2.5.1: Beet-QR-Etikett (REQ-053 GP-FR-052, GP-UX-028, Issue #2899) registriert: die Handlung `bed-view-print-label` („Etikett drucken“ unter dem Kopf der Beetansicht), der Dialog `bed-view-label-dialog` mit `bed-view-label-dialog-close`, der Auswahl `bed-view-label-qr-size` und ihren Optionen `bed-view-label-qr-size-<mm>` (`25`, `40`, `60`), dem Hinweis `bed-view-label-offline` und den Handlungen `bed-view-label-download` / `bed-view-label-cancel`; im Feldmodus der Hinweis `field-mode-linked-bed-missing` mit `field-mode-linked-bed-missing-close` (der QR-Link nennt ein Beet, das die Site nicht hat); auf der Login-Seite der Hinweis `login-return-hint` (Rücksprung nach der Anmeldung, UI-NFR-014 R-009). Keine bestehende Kennung umbenannt (R-021); die Page Objects brauchen keine Anpassung. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.21 | 2026-11-12 | §2.5.1: Opt-in „Wiederkehrende Aufgaben anlegen“ beim Platzieren einer Beetvorlage (REQ-053 GP-FR-087, Issue #2897) registriert: `garden-plan-template-recurring-tasks` und `-recurring-tasks-help`; nachregistriert die Vorlagen-Austausch-Kennungen `garden-plan-template-export` / `-import` / `-exchange-notice` (WP 9.9, GP-FR-173). |
| 1.20 | 2026-11-12 | §2.5.1: Gartengrenze im Editor (REQ-053 UC-01, GP-FR-019/032, Issue #2890) registriert: der Überlauf-Eintrag `garden-plan-menu-boundary` („Gartengrenze zeichnen“ bzw. „… entsperren und bearbeiten“ / „… sperren“; Indoor „Grundriss …“), der Hinweis des Grenz-Modus `garden-plan-boundary-mode` mit `data-mode` (`draw`/`edit`) und seine Handlung `garden-plan-boundary-done` („Sperren“ bzw. „Zeichnen beenden“). Die Griffe der entsperrten Grenze tragen die bestehenden Kennungen `garden-plan-handles` / `garden-plan-handle-<id>`, die Formwahl `garden-plan-shape-rect`/`-polygon`. Keine Kennung umbenannt (R-021), Page Object im selben Pull Request (R-020). |
| 1.19 | 2026-11-12 | §2.5.1: „Beet räumen“ der Beetansicht (REQ-053 GP-FR-055, GP-API-019, Issue #2891) registriert: die Handlung `bed-clear-button` im Tab „Pflanzung“ (nur solange Pflanzen stehen und das Beet bearbeitbar ist), der Dialog `bed-clear-dialog` mit dem Satz `bed-clear-affected` (qualifizierende Attribute `data-plant-count`, `data-run-count`), der Folgenliste `bed-clear-effects`, der Auswahl `bed-clear-termination` mit `bed-clear-termination-<art>` und `-<art>-input` (`<art>` ∈ `harvested`, `senesced`, `died`, `cancelled`), der Notiz `bed-clear-reason`, dem Hinweis `bed-clear-irreversible` und den Handlungen `bed-clear-submit` / `bed-clear-cancel`. Keine bestehende Kennung umbenannt (R-021); das Page Object `bed_view_page.py` erhält im selben Pull Request `ClearBedDialog`. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.18 | 2026-11-11 | §2.5.1: Mit dem Drawer bei md (REQ-053 v1.18, GP-UX-069, Issue #2885) entfällt die Kennung `garden-plan-side-panel-drawer` und der `data-variant`-Wert `drawer`; das Panel trägt ab md `garden-plan-side-panel-dock` und `docked`. Keine Kennung umbenannt (R-021): die entfallene Hülle hat keinen Nachfolger, Page Object und TC-053-102 sind im selben Pull Request nachgezogen (R-020). |
| 1.17 | 2026-11-11 | §2.5.1: Nachregistrierung aus der Abnahme der REQ-053-Welle 10 (WP 10.15, Issue #2836): sieben Kennungen waren im Code und in den Page Objects in Gebrauch, aber nicht registriert (Befund aus WP 10.13/10.14, #2880/#2881) — `garden-plan-new-object-type` (Art-Auswahl „Gartenobjekt“ im Dialog „Mit Maßen hinzufügen“), `garden-plan-shape-<form>` (Formwahl beim Zeichnen), `garden-plan-draw-finish` („Fertig“ beim Punkt-Zeichnen), `garden-plan-touchbar` (Touch-Aktionsleiste), `garden-plan-panel-empty` (Tab „Eigenschaften“ ohne Auswahl), `bed-list-link-<key>` (Beetname in der Beetliste) und `garden-plan-back-link-name` (Site-Name im Zurück-Link der Kopfleiste). Jede Kennung ist im Code nachgemessen (Datei und Zeile in #2836); keine umbenannt (R-021). Die Registrierung kommt nach der Verwendung — eine Abweichung von R-020, die hier festgehalten und nicht nachträglich verdeckt wird; einen Guard, der die Registrierung prüft, gibt es nicht. |
| 1.16 | 2026-11-11 | §2.5.1: Aufgaben an Gartenobjekten und Rankhilfe-Hinweis im Pflanzdialog (REQ-053 R-7.2, W-005/W-008, Anhang A 62, WP 10.10, Issue #2831) registriert: der Abschnitt `garden-plan-panel-object-tasks` (`data-object-type` = `compost`/`water_source`/`storage`, nur für diese drei Klassen) im Tab „Eigenschaften“ mit der Liste `garden-plan-panel-object-tasks-list`, den Zeilen `garden-plan-panel-object-task-<key>` (`data-overdue`), der Handlung `garden-plan-panel-object-task-add` („Aufgabe anlegen“) und den Zuständen `garden-plan-panel-object-tasks-empty`, `-error`, `-offline`, `-unsaved`; im bestehenden Aufgaben-Dialog `care-task-dialog` das qualifizierende Attribut `data-target` (`location`/`garden_object`) und der Hinweis `care-task-object-hint`; im Pflanzdialog der Rankhilfe-Hinweis `planting-support-<species_key>` (`data-state` `loading`/`present`/`missing`/`unavailable`, `data-trellis-count`) mit den Einträgen `planting-support-trellis-<key>`. Keine bestehende Kennung umbenannt (R-021); die Page Objects brauchen keine Anpassung. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.15 | 2026-11-11 | §2.5.1: Fensterorientierung und Sonnenfenster-Vorschlag des Gartenplans (REQ-053 §9.8, GP-FR-181, WP 10.7, Issue #2828) registriert: der Abschnitt `garden-plan-panel-window-suggest-section` mit der Handlung `garden-plan-panel-window-suggest` („Aus Fenster vorschlagen“) im Sonnenabschnitt eines Beets, der Vorschau-Dialog `garden-plan-window-suggestion-dialog` mit `garden-plan-window-suggestion-value` (`data-sun-window`), `garden-plan-window-suggestion-none`, `garden-plan-window-suggestion-replace`, `garden-plan-window-suggestion-unchanged`, der Fensterliste `garden-plan-window-suggestion-windows` mit `garden-plan-window-suggestion-window-<key>` (`data-orientation`), den Hinweisen `garden-plan-window-suggestion-hints` (Einträge mit `data-hint`) und den Handlungen `garden-plan-window-suggestion-apply` / `garden-plan-window-suggestion-cancel`, dazu der Konventionshinweis `garden-plan-panel-window-orientation-convention` am Fenster. `garden-plan-panel-window-orientation` trägt jetzt die abgeleitete Richtung (`data-available="true"`). Das Feld „Umkreis um ein Fenster“ folgt `form-field-window_thresholds.suggestion_radius_m`. Keine bestehende Kennung umbenannt (R-021); die Page Objects brauchen keine Anpassung. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.14 | 2026-11-11 | §2.5.1: Indoor-Plan (REQ-053 §9.8, GP-FR-182/183, GP-UX-049, WP 10.8, Issue #2829) registriert: der Leerzustand des Plans `garden-plan-empty` mit dem qualifizierenden Attribut `data-plan-kind` (`garden`/`indoor`), die beiden Handlungen des Indoor-Leerzustands `garden-plan-empty-draw` („Grundriss zeichnen“) und `garden-plan-empty-underlay` („Foto als Vorlage laden“) sowie die bisher nicht registrierte, unveränderte Handlung `garden-plan-empty-add-bed` („Erstes Beet anlegen“, #2617). Keine bestehende Kennung umbenannt (R-021): der Tab `garden-plan-tab-beds` heißt im Indoor-Plan „Pflanzplätze“, die Kennung und der URL-Wert `beds` bleiben; im Indoor-Plan fehlen `garden-plan-layer-frost`, die Gruppen `bed-view-site-conditions-frost`/`-cold-air`/`-heat`/`-wind` und `field-mode-site-wind`, weil die Merkmale ausgeblendet sind. Das Page Object `garden_plan_page.py` erhält im selben Pull Request `EMPTY*`, `empty_plan_kind()` und `tab_label()`. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.13 | 2026-11-11 | §2.5.1: Eigenschaften der Indoor- und Gartenobjekte und Objekt-Legende des Gartenplans (REQ-053 §9.5/§9.8, GP-FR-180, WP 10.6, Issue #2827) registriert: der Abschnitt `garden-plan-panel-object-props` (`data-object-type`) im Tab „Eigenschaften“, die Felder `garden-plan-panel-window-sill-height`, `garden-plan-panel-window-glazing`, die lesende Anzeige `garden-plan-panel-window-orientation` (`data-available`), `garden-plan-panel-door-swing`, der Hinweis `garden-plan-panel-furniture-note`, `garden-plan-panel-lamp-kind`, `garden-plan-panel-lamp-height`, `garden-plan-panel-lamp-ppfd`, `garden-plan-panel-trellis-height`, der Schalter `garden-plan-panel-off-site-switch` mit seiner Ablehnung `garden-plan-panel-off-site-error` sowie die Objekt-Legende `garden-plan-legend-objects` mit den Einträgen `garden-plan-legend-object-<klasse>` im Tab „Ebenen“. Keine bestehende Kennung umbenannt (R-021); die Page Objects brauchen keine Anpassung. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.12 | 2026-11-10 | §2.5.1: Seitenpanel des Gartenplans mit Tabs (REQ-053 §17.3, GP-UX-068/069/070, WP 10.5, Issue #2826) registriert: der Umschalter `garden-plan-panel-toggle` in der Kopfleiste (`aria-expanded`, `aria-controls` auf `garden-plan-properties-panel`; im Überlauf weiter `garden-plan-menu-panel`), das Panel `garden-plan-side-panel` (`data-variant` `docked`/`drawer`/`sheet`, `data-tab`), seine Tab-Leiste `garden-plan-side-panel-tabs`, die Tabs `garden-plan-side-panel-tab-<tab>` und Tab-Panels `garden-plan-side-panel-tabpanel-<tab>` mit `<tab>` ∈ `properties`, `view`, `layers`, `zones`, die Hüllen `garden-plan-side-panel-dock` (ab lg angedockt) und `garden-plan-side-panel-drawer` (md), der Höhen-Schalter `garden-plan-sheet-size` des Bottom Sheets (`data-size` `half`/`full`) und der Legenden-Schalter `garden-plan-legend-toggle` im Tab „Ebenen“. Keine bestehende Kennung umbenannt (R-021): `garden-plan-view-bar` ist der Inhalt des Tabs „Ansicht“ (Rasterstufe, Raster, Einrasten, Einheit, Kompass), `garden-plan-layer-toggles`, `garden-plan-layer-<ebene>`, `garden-plan-attention-filter` und `garden-plan-layer-legend` stehen im Tab „Ebenen“ (Schalter jetzt mit sichtbarem Text), `garden-plan-panel` ist der Inhalt des Tabs „Eigenschaften“, `garden-plan-panel-close` schließt das Panel auf jeder Breite, `garden-plan-sheet` bleibt die Hülle des Bottom Sheets im Dock, `garden-plan-zone-panel` der Inhalt des Tabs „Zonen“, und `garden-plan-zones-open` ist jetzt der Überlauf-Eintrag „Bewässerungszonen verwalten“, der das Panel auf „Zonen“ öffnet (vorher Umschalter in der Kopfleiste). Die Page Objects öffnen im selben Pull Request den passenden Panel-Tab (`open_side_panel_tab`). Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.11 | 2026-11-10 | §2.5.1: Vertikale Werkzeug-Leiste des Gartenplans (REQ-053 §17.3, GP-UX-066/069/070, WP 10.4, Issue #2825) registriert: die Untermenü-Knöpfe `garden-plan-tool-bed-menu` und `garden-plan-tool-garden_object-menu` mit ihren Menüs `garden-plan-tool-bed-submenu` / `garden-plan-tool-garden_object-submenu`, der neue Eintrag `garden-plan-add-with-dimensions-object` (Untermenü „Gartenobjekt“) und die Auswahlgruppe `garden-plan-selection-group`. Keine bestehende Kennung umbenannt (R-021): `garden-plan-toolbar` ist jetzt die Leiste links der Zeichenfläche (ab md, `aria-orientation="vertical"`, unter md unten angedockt), `garden-plan-tool-template` und `garden-plan-add-with-dimensions` sind Einträge im Untermenü „Beet“ (Letzterer im Tab „Liste“ weiter im Überlauf), `garden-plan-save-template-button` ist ein Überlauf-Eintrag nur bei genau einem gewählten Beet, `garden-plan-angle-<step>`, `garden-plan-align-button` und `garden-plan-delete-button` stehen in der Auswahlgruppe und existieren nur bei Auswahl. Die Page Objects öffnen im selben Pull Request das Untermenü „Beet“. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.10 | 2026-11-10 | §2.5.1: Editor-Kopfleiste und Arbeitsflächen-Rahmen des Gartenplans (REQ-053 §17.3, GP-UX-063/067/070, WP 10.3, Issue #2824) registriert: `garden-plan-header-bar` (die eine Kopfleiste, mit `data-overflow-level`), die Überlauf-Einträge `garden-plan-menu-autosave`, `garden-plan-menu-tab-<tab>`, `garden-plan-menu-field-mode`, `garden-plan-menu-panel`, `garden-plan-menu-selectAll` (bisher ohne Registrierung), die Zoom-Überlagerung `garden-plan-zoom-overlay`, der Zeichenflächen-Bereich `garden-plan-canvas-area` und der Zähler `garden-plan-save-status-count` des kompakten Speicher-Status. Keine bestehende Kennung umbenannt (R-021): Tastaturhilfe, Unterlage, „Mit Maßen hinzufügen“ und die Export-/Import-Einträge stehen jetzt im Überlauf `garden-plan-overflow-menu` und behalten ihre Kennungen; entfallen ist allein der Listen-Schalter `garden-plan-view-list` (der Tab „Liste“ ersetzt ihn), die Page Objects nutzen im selben Pull Request `open_tab(...)` und öffnen den Überlauf, wo ein Bedienelement dorthin gewandert ist. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.9 | 2026-11-10 | §2.5.1: Tabs Plan · Liste · Beete der Plan-Route (REQ-053 §17.3, GP-UX-064/070, WP 10.2, Issue #2823) registriert: `garden-plan-tabs` (Tab-Leiste), `garden-plan-tab-<tab>` mit `<tab>` ∈ `plan`, `list`, `beds` (der Wert von `?tab=`), die Tab-Panels `garden-plan-tabpanel-editor` (Editor für Plan und Liste) und `garden-plan-tabpanel-beds` (Beetliste) sowie der Hinweis `garden-plan-beds-offline` im Tab „Beete“ ohne Serververbindung. Keine bestehende Kennung umbenannt (R-021); die Page Objects der Beetliste öffnen den Tab „Beete“ im selben Pull Request. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.8 | 2026-10-30 | §2.5.1: Ebene Pflanzenzustand des Gartenplans (REQ-053 GP-UX-061, Issue #2488) registriert: Ebenen-Schalter `garden-plan-layer-plantState`, der abhängige Filter-Schalter `garden-plan-attention-filter` („Nur Pflanzen mit Handlungsbedarf zeigen“, gesperrt solange die Ebene aus ist) und der Legendenabschnitt `garden-plan-legend-plantState` in `garden-plan-layer-legend`. Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.7 | 2026-10-30 | §2.5.1: Standortbedingungs-Ebenen des Gartenplans (REQ-053 GP-FR-169, Issue #2487) registriert: Ebenen-Schalter `garden-plan-layer-sun`, `garden-plan-layer-moisture`, `garden-plan-layer-frost`; die dekorativen Überlagerungen `garden-plan-sun-layer`, `garden-plan-moisture-layer`, `garden-plan-frost-layer`; die Legendenabschnitte `garden-plan-legend-sun`, `garden-plan-legend-moisture`, `garden-plan-legend-frost` in `garden-plan-layer-legend`; dazu `bed-header-drainage` (Drainage im Kopf der Beetansicht, GP-FR-047). Zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.6 | 2026-10-30 | §2.5.1: Sonnenprofil im Eigenschaften-Feld des Gartenplan-Editors (REQ-053 GP-FR-158/159, Issue #2538) registriert: `garden-plan-panel-sun-profile` mit denselben Suffixen wie `bed-view-sun-profile` (`-window`, `-window-<wert>`, `-window-<wert>-input`, `-hours`, `-foliage`), zusammen mit der Verwendung im selben Pull Request (R-020). |
| 1.5 | 2026-10-20 | §2.5.1: Sonnenprofil des Beets (REQ-053 WP 7.20, GP-FR-158/159) registriert: `bed-view-sun-profile` (Dialog Sonne und Schatten der Beetansicht) und `field-mode-sun-profile` (Beet-Sheet des Feldmodus) mit den qualifizierenden Suffixen `-window` (Gruppe der Chips), `-window-<wert>` (Chip, `<wert>` ∈ `morning`, `midday`, `afternoon`, `all_day`, `mixed`, `unknown`), `-window-<wert>-input`, `-hours` (Stundenfeld) und `-foliage` (Schalter Laubschatten); dazu `field-mode-sun-section` (Abschnitt im Beet-Sheet) und `bed-header-sun-profile` (Zeile im Kopf der Beetansicht). |
| 1.4 | 2026-10-20 | §2.5.1: Identifikatoren des Gartenplan-Editors für REQ-053 Welle 7 (WP 7.10-7.13: Beetvorlagen und Standardgrößen, Objekt-Snap, Ausrichten/Verteilen, Mini-Map, Auto-Save-Option, Mehrfach-Duplizieren) registriert (per R-020, zusammen mit der Verwendung im selben Pull Request). |
| 1.3 | 2026-10-20 | §2.5.1: Bewässerungs-Ebenen und Zonen-Panel des Gartenplans (REQ-053 WP 7.6/7.7) im Präfix `garden-plan-*` registriert: `garden-plan-layer-zones`, `garden-plan-layer-lastWatered`, `garden-plan-layer-legend`, `garden-plan-zones-open`, `garden-plan-zone-panel` mit `garden-plan-zone-*` (Zeile, Formular, Statusblock, Beetliste) und `garden-plan-round-*` (Gießrunden-Dialog). |
| 1.2 | 2026-10-15 | §2.5.1: Präfixe `garden-plan-*` (Editor), `bed-view-*` (Beetansicht) und `field-mode-*` (Feldmodus) für REQ-053 **reserviert** und die in REQ-053 GP-UX-012 genannten Identifikatoren registriert (per R-020, **vor** der Verwendung; Implementierung folgt mit REQ-053 Welle 4/5). §3.3 Kurzreferenz ergänzt. |
| 1.1 | 2026-07-26 | Registrierte Zusatzmuster §2.5.1 (Karten-Layout, Formular-Aktionsleiste, Tabellenkopf, qualifizierende Attribute, konkret vergebene Identifikatoren). |

## 1. Business Case

### 1.1 User Story

**Als** E2E-Test-Autor
**möchte ich** jedes relevante UI-Element und jede Seite über einen stabilen, eindeutigen Identifikator ansprechen können
**um** robuste Selenium-Tests zu schreiben, die nicht bei jeder Layout- oder Textänderung brechen.

**Als** Frontend-Entwickler
**möchte ich** eine verbindliche Konvention, welche Elemente einen Test-Identifikator tragen müssen und wie er benannt wird
**um** Testbarkeit konsistent und ohne Nachdenken bei der Implementierung mitzuliefern.

**Als** QA-Verantwortlicher
**möchte ich** dass Test-Identifikatoren als stabiler Vertrag behandelt werden
**um** eine wartbare, verlässliche Test-Suite mit geringer Flakiness zu betreiben.

### 1.2 Geschäftliche Motivation

Die verbindliche Teststrategie (NFR-008) und der Selenium-Teststandard (NFR-008a) schreiben
vor, **wie** Tests Selektoren wählen (Locator-Hierarchie, Page-Object-Pattern). Sie setzen
dabei stabile, eindeutige Identifikatoren im DOM voraus — es fehlt bisher jedoch die
verbindliche **Bereitstellungs**-Anforderung an das Frontend. Diese UI-NFR schließt die Lücke:

1. **Robuste E2E-Tests** — Selektoren, die an fachliche Test-Identifikatoren statt an
   Layout, Position oder übersetzbaren Text gebunden sind, überleben Refactorings und
   i18n-Änderungen.
2. **Geringere Wartungskosten** — Ein stabiler Identifikator-Vertrag verhindert, dass
   Tests reihenweise durch kosmetische UI-Änderungen brechen (Flakiness-Reduktion).
3. **Schnellere Testentwicklung** — Ein vorhersagbares Namensschema erlaubt Test-Autoren,
   Selektoren abzuleiten, ohne den DOM zu inspizieren.
4. **Barrierefreiheit als Nebeneffekt** — Wo Accessibility-Rollen und `aria-label`
   (UI-NFR-002) konsistent gepflegt sind, dienen sie zusätzlich als sekundäre Test-Anker.

---

## 2. Anforderungen

### 2.1 Grundprinzip & Locator-Hierarchie

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Jedes UI-Element, das ein E2E-Test ansprechen können muss (interaktive Elemente, Seiten-Container, Zustands- und Ergebnisanzeigen), MUSS über einen stabilen, eindeutigen Identifikator adressierbar sein — primär über das Attribut `data-testid`. | MUSS |
| R-002 | Der primäre Test-Identifikator MUSS `data-testid` sein. Die von Tests genutzte Locator-Präzedenz ist in NFR-008a §5.2 normiert (`data-testid` → `#id` → MUI-Klassen → `role` → XPath); dieses Dokument regelt die **Bereitstellung** dieser Identifikatoren durch das Frontend. | MUSS |
| R-003 | Selektoren DÜRFEN NICHT an positionsbasierte Pfade (`nth-child`, XPath-Indizes), an CSS-Utility-Klassen oder an übersetzbaren Anzeigetext gebunden werden müssen — für jedes testrelevante Element MUSS ein von diesen Faktoren unabhängiger Identifikator existieren. | MUSS |
| R-004 | `data-testid` DARF NICHT für Anwendungslogik, Styling oder fachliches Verhalten zweckentfremdet werden — es ist ausschließlich ein Test-Kontrakt. | MUSS |

### 2.2 Seiten-Marker (Page Marker)

| # | Regel | Stufe |
|---|-------|-------|
| R-005 | Jede über eine Route erreichbare Seite MUSS auf ihrem Wurzel-Container einen eindeutigen Seiten-Marker `data-testid="<entity>-<view>-page"` tragen (z.B. `species-list-page`, `species-detail-page`, `species-edit-page`). | MUSS |
| R-006 | Der Seiten-Marker MUSS erst dann im DOM vorhanden sein, wenn die Seite ihren Inhalt darstellt, und pro Seite eindeutig sein (kein Seiten-Marker DARF auf zwei verschiedenen Routen erscheinen). | MUSS |
| R-007 | Der geteilte Ladezustand (Skeleton/Spinner der Seite) MUSS über einen einheitlichen Identifikator `data-testid="loading-skeleton"` erkennbar sein, damit Tests deterministisch auf das Ende des Ladevorgangs warten können (statt fester Wartezeiten). | MUSS |
| R-008 | Der aktive Route-/Navigationszustand SOLL für Navigationselemente identifizierbar sein (vgl. UI-NFR-005), sodass Tests die aktuelle Position verifizieren können. | SOLL |

### 2.3 Bereitstellung auf Elementebene

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Alle interaktiven Elemente (Buttons, Links mit Aktion, Eingabefelder, Selects, Checkboxen, Toggles, Menü-Einträge, Tabs) MÜSSEN einen `data-testid` tragen. | MUSS |
| R-010 | Formular-Eingabefelder MÜSSEN dem Schema `data-testid="form-field-<name>"` folgen (`<name>` = fachlicher Feldname), konsistent mit dem Formular-Komponenten-Pattern im Frontend-Style-Guide. | MUSS |
| R-011 | Dialoge, Modale und Bestätigungsabfragen MÜSSEN einen `data-testid` tragen (z.B. `confirm-dialog`, `create-dialog`), damit Tests ihren Auf-/Zustand eindeutig prüfen können. | MUSS |
| R-012 | Ergebnis-, Status- und Kennzahlanzeigen, deren Wert ein Test verifiziert (z.B. Zähler, Statusbadges, leere/Fehlerzustände), MÜSSEN einen sprechenden `data-testid` tragen (z.B. `plant-count`, `empty-state`, `error-message`). | MUSS |
| R-013 | Dekorative, rein visuelle Elemente ohne Testrelevanz DÜRFEN keinen `data-testid` tragen — Identifikatoren werden gezielt vergeben, nicht flächendeckend gestreut. | SOLL |

### 2.4 Listen, Tabellen & wiederholte Elemente

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Wiederholte Elemente (Tabellenzeilen, Karten, Listeneinträge) MÜSSEN pro Eintrag eindeutig adressierbar sein — über einen Identifikator, der einen **stabilen fachlichen Schlüssel** einbettet (z.B. `data-testid="species-row-{slug}"` oder `-{id}`), NICHT über den Zeilen-/Array-Index. | MUSS |
| R-015 | Der Container einer Liste/Tabelle SOLL einen eigenen `data-testid` tragen (z.B. `species-table`), damit Tests „innerhalb dieser Liste"-Abfragen kapseln können. | SOLL |
| R-016 | Zellen mit testrelevantem Inhalt innerhalb einer Zeile SOLLEN über einen zeilen-relativen `data-testid` erreichbar sein (z.B. `data-testid="cell-status"` innerhalb der Zeile), sodass Assertions ohne Spalten-Positionsannahmen möglich sind. | SOLL |

### 2.5 Namenskonvention

| # | Regel | Stufe |
|---|-------|-------|
| R-017 | `data-testid`-Werte MÜSSEN in **kebab-case** und **englisch** notiert werden (konsistent mit NFR-003 „Source-Code englisch"), unabhängig von der DE-kanonischen Doku- und UI-Sprache. | MUSS |
| R-018 | Es gilt folgendes verbindliches Namensschema: <br>• Seiten: `<entity>-<view>-page` (`view` ∈ `list`, `detail`, `edit`, `create`, …) <br>• Formularfelder: `form-field-<name>` <br>• Aktions-Buttons: `<action>-button` bzw. `<entity>-<action>-button` (z.B. `submit-button`, `species-delete-button`) <br>• Dialoge: `<zweck>-dialog` (z.B. `confirm-dialog`) <br>• Listeneinträge: `<entity>-row-<key>` / `<entity>-card-<key>` mit fachlichem Schlüssel <br>• Geteilte Marker: `loading-skeleton`, `empty-state`, `error-message`. | MUSS |
| R-019 | Ein `data-testid`-Wert MUSS innerhalb der aktuell sichtbaren Ansicht eindeutig sein (mehrfach vorkommende Elemente werden per fachlichem Schlüssel disambiguiert, R-014). | MUSS |
| R-020 | Neue oder abweichende Namensmuster SOLLEN in diesem Dokument bzw. im Frontend-Style-Guide ergänzt werden, bevor sie verwendet werden, damit das Schema die einzige Quelle der Wahrheit bleibt. | SOLL |

#### 2.5.1 Registrierte Zusatzmuster (per R-020)

Über das Grundschema aus R-018 hinaus sind die folgenden Muster verbindlich registriert. Sie sind in der Implementierung bereits vergeben; ein neues Muster wird hier ergänzt, **bevor** es verwendet wird.

**Karten-Layout (`MobileCard`) — Gegenstück zu `cell-<columnId>` im Tabellen-Layout:**

| Muster | Bedeutung |
|---|---|
| `card-title` | Überschriftenzeile einer Karte; unbedingt vorhanden, unabhängig von der Spaltenzuordnung |
| `card-subtitle` | Unterzeile einer Karte; nur vorhanden, wenn überhaupt eine Unterzeile gerendert wird |
| `card-field-<columnId>` | Wert eines Feldes der Karte, geschlüsselt über die `id` der Tabellenspalte, die es spiegelt. Titel und Unterzeile emittieren dieses Muster zusätzlich, wenn ihnen eine Spalten-`id` zugeordnet ist |
| `card-chip-<columnId>` | Einzelner Chip der Chip-Zeile, geschlüsselt über die gespiegelte Spalten-`id` |
| `card-actions` | Container der interaktiven Steuerelemente einer Karte (Favoriten-Umschalter, Überlaufmenü), oben rechts. Abzugrenzen vom rein visuellen `trailing`-Slot: Eine Karte, deren `trailing` bereits belegt ist, hatte sonst keinen Ort für ihre Aktionen — auf `SpeciesListPage` war der Favoriten-Umschalter unterhalb des `sm`-Breakpoints dadurch gar nicht erreichbar. Die Einzel-IDs der enthaltenen Schaltflächen bleiben erhalten |

**Formular-Aktionsleiste:**

| Muster | Bedeutung |
|---|---|
| `form-actions` | Container der Aktionsschaltflächen eines Formulars (Speichern/Abbrechen); ergänzt, nicht ersetzt, die Einzel-IDs der Buttons |

**Tabellenkopf (`DataTable`):**

| Muster | Bedeutung |
|---|---|
| `sort-<columnId>` | Sortier-Bedienelement einer Spalte, geschlüsselt über die `id` der Tabellenspalte. Sitzt auf dem `TableSortLabel` **innerhalb** der Kopfzelle, nicht auf der Zelle selbst: Der Klick-Handler hängt am Label, und ein Klick auf die umgebende Zelle erreicht ihn nicht, da DOM-Ereignisse nach oben und nicht nach unten laufen. Die E2E-Suite klickte zuvor die Kopfzelle und sortierte damit auf jeder Spalte, die breiter als ihr Label ist, nichts — unbemerkt, weil der Sortier-Chip ohnehin aus `defaultSort` gerendert wird (#802) |

Der Chip `sort-chip` (Toolbar) kollidiert nicht mit diesem Muster: Er liegt außerhalb von `<thead>`, sodass eine Präfix-Selektion `[data-testid^='sort-']` innerhalb einer Kopfzelle ihn nie trifft.

**Qualifizierende Attribute (keine `data-testid`-Werte):**

Die folgenden beiden Namen sind **eigenständige HTML-Attribute**, nicht `data-testid`-Werte. Sie qualifizieren ein Element, das seinen eigenen `data-testid` behält, und werden in Kombination selektiert.

| Attribut | Bedeutung | Selektion |
|---|---|---|
| `data-table-section` | Stabiler, englischer Bezeichner des Abschnitts, den eine `DataTable` rendert. Sitzt auf der Komponenten-Wurzel — dem einzigen Element, das Tabellen- und Karten-Layout gemeinsam haben — und unterscheidet mehrere Tabellen derselben Seite | `[data-testid='data-table'][data-table-section='<id>']` |
| `data-chip-color` | Semantische Palettenfarbe eines Chips (`error`, `warning`, …) als fachliche Aussage („dieser Zustand ist ein Problem"), damit Tests nicht an MUI-Styling-Klassen wie `MuiChip-color<Palette>` binden müssen. Ein Chip auf der Standardfarbe emittiert nichts | `[data-testid='card-chip-<id>'][data-chip-color='error']` |

**Konkret vergebene Identifikatoren, die vom Grundschema abweichen oder es präzisieren:**

| `data-testid` | Element |
|---|---|
| `delete-task-button` | Löschen-Aktion auf der Aufgaben-Detailseite |
| `plant-tasks-active-section` / `plant-tasks-done-section` | Die beiden Aufgabenblöcke im Aufgaben-Tab der Pflanzen-Detailseite |
| `calendar-category-filter-toggle` | Auf-/Zuklappen der Kategorie-Filter im Kalender |
| `phase-profile-<key>` / `phase-delete-<key>` | Profil-Öffnen bzw. Löschen je Wachstumsphasen-Zeile |
| `cultivar-delete-<key>` | Löschen je Sorten-Zeile |
| `care-edit-profile-<id>` / `care-confirm-<id>` / `care-snooze-<id>` | Die drei Aktionen einer Pflegekarte in der Aufgaben-Warteschlange |
| `page-title-actions` | Aktionsgruppe im Seitenkopf (vgl. UI-NFR-021) |
| `crop-rotation-dialog` / `companion-planting-dialog` | Dialoge der Fruchtfolge- bzw. Mischkultur-Pflege |
| `sidebar-toggle` | Auf-/Zuklappen der Navigations-Seitenleiste im Hauptlayout |

**Gartenplan, Beetansicht, Feldmodus (REQ-053 GP-UX-012) — reservierte Präfixe:**

Die folgenden drei Präfixe sind für die grafische Garten-/Beetplanung reserviert und dürfen von keinem anderen Modul verwendet werden. Sie sind per R-020 **vor** der Implementierung registriert (REQ-053 v1.4, Anhang A Issue 67); die Identifikatoren der Spalte „Vergeben" entstehen mit REQ-053 Welle 4/5 und sind bis dahin noch nicht im DOM.

| Präfix | Bereich | Vergeben (GP-UX-012) |
|---|---|---|
| `garden-plan-*` | Editor und Gartenübersicht (Route `standorte/sites/:key/plan`) | `garden-plan-page` (Seiten-Marker nach R-005), `garden-plan-canvas` (Zeichenfläche, Wurzel des `PlanRenderer`), `garden-plan-layer-<ebene>` (Ebenen-Schalter: `zones`, `lastWatered`, `sun`, `moisture`, `frost`, `plantState`), `garden-plan-attention-filter` (Filter „Nur Pflanzen mit Handlungsbedarf“ der Ebene `plantState`, Issue #2488), `garden-plan-<ebene>-layer` (dekorative Überlagerung der Standortbedingungen: `sun`, `moisture`, `frost`, Issue #2487), `garden-plan-layer-legend` mit `garden-plan-legend-<ebene>` (Abschnitte `sun`, `moisture`, `frost`, `plantState`), `garden-plan-zones-open`, `garden-plan-zone-panel`, `garden-plan-zone-*` (Zonen-Panel: `row-<key>`, `new`, `name`, `type`, `save`, `delete`, `status`, `hints`, `round-open`), `garden-plan-round-*` (Gießrunden-Dialog: `volume`, `allocation-<art>`, `marker`, `submit`, `result`), `garden-plan-panel-sun-profile` mit denselben Suffixen wie `bed-view-sun-profile` (Sonnenzeit, Stunden und Laubschatten im Eigenschaften-Feld, Issue #2538) |
| `bed-view-*` | Beetansicht (Detailseite eines Beets mit Plan-Tab) | `bed-view-sun-profile` mit `-window`, `-window-<wert>`, `-window-<wert>-input`, `-hours`, `-foliage` (Sonnenprofil im Dialog „Sonne und Schatten“, WP 7.20); sonst — (die heute benannten Beet-Identifikatoren folgen dem Grundschema: `bed-detail-page`, `bed-plan-tab`) |
| `field-mode-*` | Feldmodus (`?mode=field`, REQ-053 §18: Beet-Sheet, Schnellprotokoll-Chips, Rückgängig-Snackbar, Stepper) | `field-mode-sun-section` (Abschnitt Sonne im Beet-Sheet), `field-mode-sun-profile` mit denselben Suffixen wie `bed-view-sun-profile` (WP 7.20), `field-mode-position-*` („Meine Position“, GP-UX-026, #2898); sonst — (Präfix reserviert) |
| `bed-header-*` | Kopf der Beetansicht (`BedHeader`, Detailseite eines Beets) | `bed-header-soil` (Substrat), `bed-header-drainage` (Drainage, nur wenn erfasst, Issue #2487), `bed-header-sun` (Sonnenexposition), `bed-header-sun-profile` (Zeile Sonnenzeit und Laubschatten unter der Sonnenexposition, WP 7.20) |

Weitere in GP-UX-012 vergebene Identifikatoren, die das Grundschema R-018 präzisieren:

| `data-testid` | Element |
|---|---|
| `plan-tool-<name>` | Werkzeug in der Werkzeugleiste des Editors, geschlüsselt über den englischen Werkzeugnamen (`select`, `rect`, `polygon`, `move`, …) |
| `plan-object-<key>` | Gezeichnetes Objekt (Beet, Gartenobjekt, Slot) auf der Zeichenfläche, geschlüsselt über den fachlichen `_key` (R-014) |
| `plan-handle-<position>` | Griff zum Skalieren/Drehen eines selektierten Objekts (`nw`, `n`, `ne`, …, `rotate`) |
| `plan-properties-panel` | Eigenschaftenpanel rechts bzw. als Bottom Sheet |
| `save-plan-button` | Speichern des Plan-Batches (Grundschema `<action>-button`) |
| `plan-conflict-dialog` | 409-Konfliktdialog „Neu laden" / „Meine Änderungen als Kopie behalten (JSON herunterladen)" (Grundschema `<zweck>-dialog`; Wortlaut identisch in REQ-053 GP-UX-017 und GP-ACC-011) |
| `care-event-row-<key>` | Zeile der Pflegehistorie, geschlüsselt über den `_key` des `care_event` (Grundschema `<entity>-row-<key>`) |

**Gartenplan-Editor, REQ-053 Welle 7 (Beetvorlagen, Snap, Mini-Map, Auto-Save, Mehrfach-Duplizieren):**

| `data-testid` | Element |
|---|---|
| `garden-plan-tool-template` | „Aus Vorlage“ (Beet aus Vorlage); ab WP 10.4 Eintrag im Untermenü „Beet“ der Werkzeug-Leiste (`menuitemcheckbox`) |
| `garden-plan-template-panel` / `-select` / `-rotate` / `-place-center` / `-close` / `-hint` / `-failed` | Leiste unter der Werkzeugleiste: Vorlagenwahl, Drehen um 90°, in die Bildmitte setzen, beenden, Hinweis, Ladefehler |
| `garden-plan-template-recurring-tasks` / `-recurring-tasks-help` | Opt-in „Wiederkehrende Aufgaben anlegen“ (Checkbox, Standard aus) und Hilfetext mit den Aufgaben, die angelegt würden; nur bei einer Vorlage mit `recurring_task_templates` (REQ-053 GP-FR-087, #2897) |
| `garden-plan-template-export` / `-import` / `-exchange-notice` | Vorlage als JSON-Datei herunterladen, Vorlagen-Datei importieren (ab Gärtner), Rückmeldung dazu (REQ-053 GP-FR-173, WP 9.9) |
| `garden-plan-template-ghost` | Umriss der Vorlage unter dem Zeiger (SVG-Overlay) |
| `garden-plan-save-template-button` | „Als Vorlage speichern" aus dem gewählten Beet; ab WP 10.4 Eintrag im Überlauf „⋮“, nur bei genau einem gewählten Beet |
| `garden-plan-template-save-dialog` / `-name` / `-submit` / `-cancel` / `-error` | Dialog „Als Vorlage speichern" |
| `garden-plan-add-standard-sizes` | Schnellwahl der Standardgrößen im Dialog „Mit Maßen hinzufügen" |
| `garden-plan-add-standard-<template_key>` | Eine Standardgröße, geschlüsselt über den `_key` der System-Vorlage (z. B. `sys_raised_bed_2x1x0_8`) |
| `garden-plan-add-height` | Höhenfeld (Beet) im Dialog „Mit Maßen hinzufügen" |
| `garden-plan-snap-guide` | Führungslinie entlang der Objektkante, auf der der Fang einrastet (innerhalb von `garden-plan-snap-marker`) |
| `garden-plan-align-button` | Menü „Ausrichten" in der Werkzeugleiste |
| `garden-plan-align-<modus>` | Eintrag `left`, `right`, `top`, `bottom`, `centerH`, `centerV` |
| `garden-plan-distribute-<achse>` | Eintrag `horizontal` bzw. `vertical` (gleichmäßig verteilen) |
| `garden-plan-minimap` / `garden-plan-minimap-viewport` | Mini-Map (120 × 120 px) und ihr Viewport-Rechteck |
| `garden-plan-autosave` | Schalter „Automatisch speichern" (nutzerbezogen, localStorage) |
| `garden-plan-autosave-paused` | Hinweis, dass Auto-Save bei Konflikt oder abgelehntem Speichern pausiert |
| `garden-plan-multi-dialog` / `-count` / `-direction` / `-spacing` / `-scheme` / `-start` / `-preview` / `-error` / `-submit` / `-cancel` | Dialog „Mehrfach duplizieren" |
| `garden-plan-info` | Bestätigung (Erfolgsmeldung) des Editors, z. B. „Vorlage gespeichert" |

**Gartenplan-Editor, REQ-053 Welle 10 (Editor-Arbeitsfläche §17.3, GP-UX-070):**

| `data-testid` | Element |
|---|---|
| `garden-plan-tabs` | Tab-Leiste Plan · Liste · Beete über dem Editor (`role="tablist"`, nur im Planungsmodus, WP 10.2) |
| `garden-plan-tab-<tab>` | Ein Tab, geschlüsselt über den Wert des Query-Parameters `tab`: `plan`, `list`, `beds` (der URL-Wert bleibt `beds` auch dort, wo der Tab „Pflanzplätze“ heißt, GP-FR-183) |
| `garden-plan-tabpanel-editor` | Tab-Panel des Editors; gehört zu „Plan“ und „Liste“ (der Editor zeigt Zeichenfläche bzw. `garden-plan-list`), hinter „Beete“ ausgeblendet, nicht entfernt |
| `garden-plan-tabpanel-beds` | Tab-Panel „Beete“ mit der Beetliste (`bed-list-section`, unverändert) |
| `garden-plan-beds-offline` | Hinweis im Tab „Beete“, solange die Beetliste ohne Serververbindung nicht geladen werden kann |
| `garden-plan-header-bar` | Die eine Editor-Kopfleiste (WP 10.3, GP-UX-063): Zurück, Speichern-Gruppe, Tabs, Feldmodus, Panel-Umschalter, Überlauf; `data-overflow-level` (0–4) nennt, wie viele Schritte der Verlagerungsreihenfolge im Überlauf stehen |
| `garden-plan-overflow` / `garden-plan-overflow-menu` | Überlauf „⋮“ der Kopfleiste und sein Menü (Kennungen bestehen seit Welle 2, ab WP 10.3 am Ende der Kopfleiste) |
| `garden-plan-menu-<id>` | Eintrag im Überlauf „⋮“, wenn ein Bedienelement der Kopfleiste dorthin wandert: `autosave` (Schritt 1, `menuitemcheckbox`), `tab-<tab>` mit `<tab>` ∈ `plan`, `list`, `beds` (Schritt 4, `menuitemradio`, der aktive mit `aria-checked="true"`), `field-mode` (Schritt 2), `panel` (Schritt 3, Panel-Umschalter); dazu die seltenen Aktionen `selectAll` und `multiDuplicate`. Einträge, die eine frühere Schaltfläche ersetzen, behalten deren Kennung: `garden-plan-add-with-dimensions`, `garden-plan-underlay-open`, `garden-plan-keyboard-help-button`, `garden-plan-io-export` / `-import` / `-csv` / `-season` |
| `garden-plan-save-status-count` | Zähler der ungespeicherten Änderungen im kompakten Speicher-Status unter md (der Wortlaut steht für Screenreader in `garden-plan-save-status`) |
| `garden-plan-canvas-area` | Bereich der Zeichenfläche auf Viewport-Höhe (GP-UX-067, mindestens 400 px); trägt `garden-plan-canvas` und die Overlays |
| `garden-plan-zoom-overlay` | Zoom −/%/+ und „An Fläche anpassen“ als Overlay oben rechts auf der Zeichenfläche (Kennungen `garden-plan-zoom-*` unverändert) |
| `garden-plan-toolbar` | Die Werkzeug-Leiste (Kennung unverändert): ab WP 10.4 vertikal links der Zeichenfläche (ab md, `aria-orientation="vertical"`), unter md unten angedockt neben der `TouchBar` (`aria-orientation="horizontal"`); `data-orientation` nennt die Form |
| `garden-plan-tool-<tool>` | Werkzeug der obersten Ebene in der Werkzeug-Leiste (`aria-pressed` zeigt das aktive), `<tool>` ∈ `select`, `pan`, `area`, `bed`, `garden_object`, `plant`, `measure` (REQ-053 GP-UX-001; `area` = „Bereich“, `plant` = „Pflanze setzen“ — nur für Rollen mit Schreibrecht gerendert — und `measure` = „Messen“ aus GP-UX-071, #2913). Die Werte sind die Schlüssel des Werkzeug-Registers (`editor/toolRegistry.ts`); ein weiteres Werkzeug aus GP-UX-071 ergänzt diese Liste. Die Kennung bestand vor der Registrierung (Nachregistrierung, keine Umbenennung, R-021) |
| `garden-plan-tool-<tool>-menu` | Knopf, der das Untermenü eines Werkzeugs öffnet (`aria-haspopup="menu"`), `<tool>` ∈ `area`, `bed`, `garden_object` (WP 10.4; `area` seit #2913; GP-UX-001: höchstens zwei Ebenen) |
| `garden-plan-tool-<tool>-submenu` | Das Untermenü dazu: „Bereich“ mit `garden-plan-add-with-dimensions-area`, „Beet“ mit `garden-plan-tool-template` und `garden-plan-add-with-dimensions`, „Gartenobjekt“ mit `garden-plan-add-with-dimensions-object` |
| `garden-plan-add-with-dimensions-object` | „Mit Maßen hinzufügen“ im Untermenü „Gartenobjekt“ (öffnet `garden-plan-add-dialog` mit Art „Gartenobjekt“) |
| `garden-plan-add-with-dimensions-area` | „Mit Maßen hinzufügen“ im Untermenü „Bereich“ (öffnet `garden-plan-add-dialog` mit Art „Bereich“; REQ-053 GP-UX-071, #2913) |
| `garden-plan-add-kind-area` / `garden-plan-add-area-type` | Im Dialog „Mit Maßen hinzufügen“: die Art „Bereich“ (neben `garden-plan-add-kind-bed` / `-object`) und die Auswahl des Bereichstyps (das native Eingabefeld trägt die Kennung; #2913) |
| `garden-plan-new-area-type` | Typauswahl über der Zeichenfläche, solange das Werkzeug „Bereich“ aktiv ist (Garten, Terrasse, Balkon, Gewächshaus, eigene Bereichstypen; im Indoor-Plan Zimmer); das native Eingabefeld trägt die Kennung; daneben nennt `garden-plan-new-area-type-rule` die Eltern-Regel (REQ-053 GP-UX-071, #2913) |
| `garden-plan-selection-group` | Auswahlgruppe der Werkzeug-Leiste (GP-UX-066, AC-4): Drehraster `garden-plan-angle-<step>`, `garden-plan-align-button`, `garden-plan-delete-button`; nur gerendert, solange eine Auswahl besteht |
| `garden-plan-panel-toggle` | Umschalter des Seitenpanels in der Kopfleiste (WP 10.5, GP-UX-068): `aria-expanded`, `aria-controls` auf `garden-plan-properties-panel`; auf schmaler Kopfleiste als Überlauf-Eintrag `garden-plan-menu-panel` („Seitenpanel ein-/ausblenden“) |
| `garden-plan-side-panel` | Das Seitenpanel (DOM-`id` `garden-plan-properties-panel`, Ziel des Sprunglinks „Zum Eigenschaftenpanel“); eingeklappt nicht gerendert. `data-variant` nennt die Form nach der Breite (`docked` ab md, `sheet` unter md; `drawer` bei md bis v1.17, entfallen mit #2885), `data-tab` den offenen Tab |
| `garden-plan-side-panel-tabs` | Tab-Leiste des Seitenpanels (`role="tablist"`, Roving-Tabindex, Pfeiltasten, Pos1/Ende) |
| `garden-plan-side-panel-tab-<tab>` / `garden-plan-side-panel-tabpanel-<tab>` | Ein Panel-Tab und sein Tab-Panel, `<tab>` ∈ `properties` (Eigenschaften), `view` (Ansicht), `layers` (Ebenen), `zones` (Zonen); nur das aktive Tab-Panel hat Inhalt |
| `garden-plan-side-panel-dock` | Hülle des angedockten Panels ab md (neben der Zeichenfläche). `garden-plan-side-panel-drawer` (Drawer bei md) ist mit #2885 entfallen |
| `garden-plan-sheet-size` | Schalter halbe/volle Höhe des Bottom Sheets unter md (`data-size` `half`/`full`); die Hülle bleibt `garden-plan-sheet` |
| `garden-plan-legend-toggle` | Schalter „Legende anzeigen“ im Tab „Ebenen“ (GP-UX-005: Legende ein-/ausblendbar) |
| `garden-plan-panel-object-props` | Abschnitt „Objekteigenschaften“ im Tab „Eigenschaften“ für jedes gewählte Gartenobjekt (WP 10.6, GP-FR-180); `data-object-type` nennt die Klasse. Enthält je Klasse genau die Felder ihres Props-Modells und den Schalter `garden-plan-panel-off-site-switch` |
| `garden-plan-panel-window-sill-height` / `garden-plan-panel-window-glazing` | Fenster: Brüstungshöhe in m (0–1000, leer = unbekannt) und Verglasung (`single`/`double`/`unknown`, leer = nicht angegeben) |
| `garden-plan-panel-window-orientation` | Fenster: abgeleitete Himmelsrichtung mit Azimut („Südost, 135°“), nur lesend (§9.8, GP-FR-181, WP 10.7); `data-available="false"`, solange keine Richtung ableitbar ist (Fenster ist keine Linie) |
| `garden-plan-panel-window-orientation-convention` | Fenster: Hinweis, dass die Außenseite aus der Zeichenrichtung angenommen wurde, weil kein Umriss innen und außen trennt; nur dann gerendert |
| `garden-plan-panel-door-swing` | Tür: Öffnungsrichtung als Freitext (höchstens 50 Zeichen, leer = nicht angegeben) |
| `garden-plan-panel-furniture-note` | Möbel: Hinweis, dass die Klasse keine eigenen Eigenschaften hat |
| `garden-plan-panel-lamp-kind` / `garden-plan-panel-lamp-height` / `garden-plan-panel-lamp-ppfd` | Lampe: Art (`grow_light`/`ceiling`/`floor`), Montagehöhe in m (Pflicht, 0,01–1000) und Referenz-PPFD in µmol/m²/s (ab 0, leer = nicht angegeben, kein Standardwert) |
| `garden-plan-panel-trellis-height` | Rankhilfe: Höhe in m (Pflicht, 0,01–1000) |
| `garden-plan-panel-off-site-switch` / `garden-plan-panel-off-site-error` | Schalter „Außerhalb des Grundstücks“ (`off_site`, §9.5) und seine Ablehnung, wenn das Objekt beim Ausschalten aus Bereich oder Gartengrenze ragt (nur dann gerendert) |
| `garden-plan-legend-objects` / `garden-plan-legend-object-<klasse>` | Objekt-Legende im Tab „Ebenen“ (GP-FR-180, GP-UX-005) und ihr Eintrag je Objektklasse des Plans, `<klasse>` = `object_type` (`tree`, `window`, `lamp`, …); blendet mit `garden-plan-legend-toggle` aus |
| `garden-plan-panel-window-suggest-section` / `garden-plan-panel-window-suggest` | Abschnitt und Handlung „Aus Fenster vorschlagen“ im Sonnenabschnitt eines gewählten Beets/Pflanzplatzes (GP-FR-181, WP 10.7); nur im Indoor-Plan oder wenn der Plan ein Fenster hat; gesperrt nur bei gesperrtem Beet |
| `garden-plan-window-suggestion-dialog` | Vorschau-Dialog des Fenster-Vorschlags; schreibt nichts, bis `garden-plan-window-suggestion-apply` bestätigt wird (G-W10 c); `garden-plan-window-suggestion-cancel` („Abbrechen“ bzw. „Schließen“ ohne Vorschlag) schließt ohne Schreiben |
| `garden-plan-window-suggestion-value` | Der vorgeschlagene Wert, `data-sun-window` ∈ `morning`, `midday`, `afternoon`, `all_day`, `mixed`; fehlt ohne Vorschlag |
| `garden-plan-window-suggestion-none` | Erklärung, warum kein Vorschlag möglich ist (nicht platziert, kein Fenster im Umkreis, nur sonnenabgewandte Fenster, Tropen) |
| `garden-plan-window-suggestion-replace` / `garden-plan-window-suggestion-unchanged` | Warnung, dass ein eingetragener Wert ungleich „unbekannt“ ersetzt würde (die Bestätigung heißt dann „Ersetzen“), bzw. Hinweis, dass der Vorschlag dem eingetragenen Wert entspricht (dann ohne Bestätigung) |
| `garden-plan-window-suggestion-windows` / `garden-plan-window-suggestion-window-<key>` | Liste der Fenster im Umkreis und ihr Eintrag, `<key>` = Schlüssel des Fensterobjekts, `data-orientation` = abgeleitete Himmelsrichtung (8 Werte) |
| `garden-plan-window-suggestion-hints` | Liste der Hinweise; jeder Eintrag trägt `data-hint` = Hinweis-Code (`hemisphere_assumed`, `tropics`, `no_window`, `diffuse_light_only`, `shading_not_considered`, `season`, `window_distance`, `glazing`) |
| `garden-plan-empty` | Leerzustand der Plan-Route (GP-UX-049), Attribut `data-plan-kind` = `garden` oder `indoor` (Site-Typ `indoor`, `windowsill`, `grow_tent`; WP 10.8, GP-FR-182) |
| `garden-plan-empty-add-bed` | Handlung des Garten-Leerzustands „Erstes Beet anlegen“ (#2617): öffnet den Editor mit „Mit Maßen hinzufügen“; nur mit Schreibrecht und Serververbindung |
| `garden-plan-empty-draw` / `garden-plan-empty-underlay` | Handlungen des Indoor-Leerzustands (WP 10.8): „Grundriss zeichnen“ öffnet den Editor im Grenz-Modus (`garden-plan-boundary-mode`, #2890), „Foto als Vorlage laden“ öffnet ihn mit `garden-plan-underlay-dialog`; nur mit Schreibrecht und Serververbindung |
| `garden-plan-zones-open` | Kennung unverändert, ab WP 10.5 Überlauf-Eintrag „Bewässerungszonen verwalten“: öffnet das Seitenpanel auf dem Tab „Zonen“ |
| `garden-plan-panel-object-tasks` | Abschnitt „Aufgaben“ im Tab „Eigenschaften“ eines gewählten Gartenobjekts der Klassen `compost`, `water_source`, `storage` (R-7.2, W-008, WP 10.10); `data-object-type` nennt die Klasse. Andere Klassen haben den Abschnitt nicht |
| `garden-plan-panel-object-tasks-list` / `garden-plan-panel-object-task-<key>` | Liste der offenen Aufgaben des Objekts (`pending`, `in_progress`, nach Fälligkeit) und ihre Zeile, `<key>` = Schlüssel der Aufgabe; `data-overdue` = `true`/`false` |
| `garden-plan-panel-object-task-add` | Handlung „Aufgabe anlegen“: öffnet `care-task-dialog` mit dem Objekt als Ziel (`data-target="garden_object"`); nur mit Schreibrecht, gesperrt ohne Verbindung und für ein noch nicht gespeichertes Objekt |
| `garden-plan-panel-object-tasks-empty` / `-error` / `-offline` / `-unsaved` | Zustände des Abschnitts: keine offenen Aufgaben; Lesen fehlgeschlagen (mit „Erneut versuchen“); ohne Verbindung (Hinweis, nichts wird gelesen, G-W9); Objekt noch nicht gespeichert |
| `care-task-dialog` (Attribut `data-target`) / `care-task-object-hint` | Der bestehende Aufgaben-Dialog der Beetpflege trägt `data-target` = `location` (Beet) oder `garden_object` (Gartenobjekt, WP 10.10); am Gartenobjekt ersetzt der Hinweis `care-task-object-hint` die Auswahl „Gilt für“ (`care-task-scope-*` entfällt dort) |
| `planting-support-<species_key>` / `planting-support-trellis-<key>` | Rankhilfe-Hinweis im Pflanzdialog für eine Art mit `support_required: true` (W-005, WP 10.10), `data-state` ∈ `loading`, `present`, `missing`, `unavailable`, `data-trellis-count` = Zahl der Rankhilfen im Beet; der Eintrag je Rankhilfe, `<key>` = Schlüssel des Gartenobjekts. Rein informativ, blockiert nichts |
| `garden-plan-new-object-type` | Art-Auswahl im Dialog „Mit Maßen hinzufügen“ für ein Gartenobjekt (`garden-plan-add-dialog`, Untermenü „Gartenobjekt“); das native Eingabefeld der Auswahl trägt die Kennung |
| `garden-plan-shape-<form>` | Formwahl der Werkzeug-Leiste während des Zeichnens, `<form>` ∈ `rect`, `circle`, `polygon`, `polyline` (`polyline` nur beim Werkzeug „Gartenobjekt“); `aria-pressed` zeigt die gewählte Form |
| `garden-plan-draw-finish` | „Fertig“ beim Zeichnen einer Punktform (Polygon, Polylinie): schließt die Form; deaktiviert, bis die Mindestzahl an Punkten gesetzt ist |
| `garden-plan-touchbar` | Touch-Aktionsleiste (`role="toolbar"`, GP-UX-036/037): unter md der Werkzeug-Pfad, bei grobem Zeiger auf jeder Breite (§17.3, GP-UX-069) |
| `garden-plan-touch-place` / `garden-plan-touch-undo` / `garden-plan-touch-finish` / `garden-plan-touch-cancel` | Punkt-Handlungen der `TouchBar` bei jedem Werkzeug, das Punkte setzt (Zeichnen, Gartengrenze, Messen): „Punkt setzen“ am Fadenkreuz `garden-plan-crosshair`, „Rückgängig“ (letzter Punkt), „Fertig“ (deaktiviert, bis genug Punkte gesetzt sind), „Abbrechen“ — beim Messen „Löschen“. Bestehende Kennungen, mit #2913 nachregistriert |
| `garden-plan-measure-status` | Statustext des Werkzeugs „Messen“ (REQ-053 GP-UX-071, #2913) über der Zeichenfläche (`role="status"`, `aria-live="polite"`): nächster Schritt und die gemessene Summe als Text; `data-done` = `true`, sobald die Messung beendet ist |
| `garden-plan-measure` / `garden-plan-measure-line` | Die Messung im Editor-Overlay (`aria-hidden`, für jeden Renderer gleich) und ihre Linie; `data-done` wie beim Statustext; nur gerendert, solange eine Messung besteht |
| `garden-plan-measure-place` / `garden-plan-measure-finish` | Bedienung des Werkzeugs „Messen“ ohne Zeiger in der Werkzeug-Leiste (ab md bei feinem Zeiger, solange Messen aktiv ist; sonst übernimmt die `TouchBar`): „Punkt setzen“ am Fadenkreuz `garden-plan-crosshair` in der Planmitte und „Fertig“ (deaktiviert, bis zwei Punkte gesetzt sind) |
| `garden-plan-measure-segment` / `garden-plan-measure-total` | Länge je Abschnitt (erst ab zwei Abschnitten, in Pfadreihenfolge; ein Abschnitt, der auf dem Bildschirm kürzer ist als seine Beschriftung, bleibt ohne) und die Summe am Ende der Linie, in der Längeneinheit des Nutzers |
| `garden-plan-plant-status` | Statustext des Werkzeugs „Pflanze setzen“ (REQ-053 GP-UX-071, #2913) über der Zeichenfläche (`role="status"`, `aria-live="polite"`): was ein Klick (unter md: Tippen) bewirkt und der Weg ohne Maus; offline der Satz, dass das Werkzeug eine Verbindung braucht (`data-offline` = `true`) |
| `garden-plan-plant-dialog` | Dialog „Pflanze setzen“ für genau einen freien Punkt-Pflanzplatz (REQ-053 GP-UX-071, #2913), Titel mit Beet und Platz; darin `garden-plan-plant-dialog-species` (Artwahl, das Textfeld der Autovervollständigung trägt die Kennung), `garden-plan-plant-dialog-cultivar` (Sorte, nur wenn die Art Sorten hat), `garden-plan-plant-dialog-date` (Pflanztag), `garden-plan-plant-dialog-slot` (Platzwahl, nur wenn der Dialog aus dem Eigenschaftenpanel eines Beets kommt), `garden-plan-plant-dialog-submit` / `garden-plan-plant-dialog-cancel`; die Hinweise des Beets stehen in `planting-hints` |
| `garden-plan-plant-dialog-blocked` / `garden-plan-plant-dialog-open-bed` | Der Server lässt die Einzelpflanze auf diesem Platz nicht zu (Slot-Prüfung oder Ablehnung `ROTATION_VIOLATION` / `INCOMPATIBLE_COMPANION`): Erklärung ohne „Trotzdem pflanzen“ und der Weg „Zum Beet“ zum Pflanzdialog des Beets; „Pflanze setzen“ ist dann gesperrt |
| `garden-plan-plant-dialog-error` / `garden-plan-plant-dialog-catalogue-error` / `garden-plan-plant-dialog-load-error` | Jede andere Ablehnung im Dialog (Platz inzwischen belegt, offline, Plan wird gespeichert, Speichern vorher fehlgeschlagen, sonstiger Fehler) als lesbarer Satz (`role="alert"`); Arten nicht ladbar; das Dialog-Modul nicht ladbar (Fehlergrenze) |
| `garden-plan-panel-plant-slot` / `garden-plan-panel-plant-spot` | „Pflanze setzen“ im Eigenschaftenpanel (Weg ohne Zeiger, WCAG 2.1.1): für einen ausgewählten freien Punkt-Pflanzplatz genau dieser Platz; für ein ausgewähltes Beet mit freien Punkt-Pflanzplätzen der Dialog mit Platzwahl (die Zahl der freien Plätze steht darunter). Nur für Rollen mit Schreibrecht |
| `garden-plan-panel-empty` | Inhalt des Tabs „Eigenschaften“ ohne Auswahl („Nichts ausgewählt“) |
| `bed-list-link-<key>` | Beetname als Link zur Beetansicht in der Beetliste (Tabelle und Karte), `<key>` = Schlüssel der Location; im Tab „Beete“ bzw. „Pflanzplätze“ |
| `garden-plan-back-link-name` | Site-Name im Zurück-Link der Editor-Kopfleiste (§17.3, GP-UX-063); kürzt mit Auslassungspunkten und fehlt unter md (dort nur das Icon mit `aria-label`) |
| `garden-plan-menu-boundary` | Überlauf-Eintrag der Gartengrenze (REQ-053 UC-01, GP-FR-019/032, #2890), nur auf dem Tab „Plan“: ohne Grenze „Gartengrenze zeichnen“ (Indoor „Grundriss zeichnen“), mit gesperrter Grenze „… entsperren und bearbeiten“, im Grenz-Modus „… sperren“ |
| `garden-plan-boundary-mode` | Hinweis über der Zeichenfläche, solange der Grenz-Modus an ist; `data-mode` = `draw` (keine Grenze, Rechteck oder Vieleck zeichnen) oder `edit` (Grenze entsperrt, ihre Griffe `garden-plan-handle-<id>` sind gezeichnet) |
| `garden-plan-boundary-done` | Handlung im Hinweis `garden-plan-boundary-mode`: „Sperren“ (`edit`) bzw. „Zeichnen beenden“ (`draw`) — beendet den Grenz-Modus, die Grenze ist wieder gesperrt; Speichern sperrt sie ebenso |

**Beetansicht, „Beet räumen“ (REQ-053 GP-FR-055, GP-API-019, #2891):**

| `data-testid` | Element |
|---|---|
| `bed-clear-button` | „Beet räumen“ im Tab „Pflanzung“; nur gerendert, solange Pflanzen im Beet stehen, das Mitglied das Beet bearbeiten darf (ab grower) und die Ansicht online und nicht zwischengespeichert ist; im Feldmodus nicht vorhanden (GP-UX-023) |
| `bed-clear-dialog` | Dialog „Beet räumen: <Beet>“; schreibt nichts, bis `bed-clear-submit` bestätigt wird; `bed-clear-cancel` schließt ohne Schreiben |
| `bed-clear-affected` | Satz „Betroffen sind n Pflanzen aus m Durchläufen“; `data-plant-count` und `data-run-count` tragen die Zahlen |
| `bed-clear-effects` | Liste der Folgen (Pflanzen beendet, Durchläufe abgeschlossen, Plätze archiviert, Eintrag „Beet geräumt“) |
| `bed-clear-termination` / `bed-clear-termination-<art>` / `bed-clear-termination-<art>-input` | Auswahl der Beendigungsart (Radiogruppe), Chip und natives Eingabefeld, `<art>` ∈ `harvested` (vorgewählt), `senesced`, `died`, `cancelled` |
| `bed-clear-reason` / `bed-clear-irreversible` | Optionale Notiz (höchstens 1000 Zeichen) und der Hinweis, dass Räumen nicht rückgängig zu machen ist |
| `bed-clear-submit` / `bed-clear-cancel` | Bestätigen (Gefahrenfarbe, während der Anfrage gesperrt) und Abbrechen |
| `bed-view-print-label` | „Etikett drucken“ unter dem Kopf der Beetansicht (GP-FR-052, GP-UX-028, #2899); für jedes Mitglied, gesperrt ohne Verbindung; öffnet `bed-view-label-dialog` |
| `bed-view-label-dialog` / `bed-view-label-dialog-close` | Dialog „Beet-Etikett drucken“ und sein Schließen-Knopf |
| `bed-view-label-qr-size` / `bed-view-label-qr-size-<mm>` | Auswahl der QR-Code-Größe und ihre Optionen, `<mm>` ∈ `25`, `40` (vorgewählt), `60` |
| `bed-view-label-offline` | Hinweis im Dialog, dass ohne Verbindung kein Etikett erstellt werden kann (nur dann gerendert) |
| `bed-view-label-download` / `bed-view-label-cancel` | „Als PDF herunterladen“ (gesperrt ohne Verbindung) und „Abbrechen“ |
| `field-mode-linked-bed-missing` / `field-mode-linked-bed-missing-close` | Hinweis im Feldmodus, wenn `?bed=<key>` (QR-Link des Etiketts) ein Beet nennt, das die Beetliste der Site nicht enthält, und seine Schließen-Handlung (entfernt `bed` aus der Adresse) |
| `login-return-hint` | Hinweis auf der Login-Seite, dass es nach der Anmeldung zur aufgerufenen Seite weitergeht (`?returnTo=`, UI-NFR-014 R-009); nicht neben einer offenen Einladung (`login-pending-invitation`) |

**Feldmodus, „Meine Position“ (REQ-053 GP-UX-026, #2898):**

| `data-testid` | Element |
|---|---|
| `field-mode-position` | Abschnitt „Meine Position“ über der Karte im Tab „Karte“; fehlt ganz, wenn der Browser keine Geolocation-API hat (REQ-002) |
| `field-mode-position-switch` | Schalter (natives Eingabefeld, `role="switch"`); beim Öffnen des Feldmodus immer aus, außerhalb eines sicheren Kontexts gesperrt |
| `field-mode-position-description` | Beschreibung unter dem Schalter (`aria-describedby`): Datenschutzhinweis bzw. ohne sicheren Kontext der Grund der Sperre |
| `field-mode-position-hint` | Hinweis bei eingeschaltetem Schalter; `data-reason` ∈ `locating`, `denied`, `unavailable`, `timeout`, `site_loading`, `site_error`, `no_gps`, `far` (> 500 m vom Plan), `outside_view`, `coarse` (Genauigkeit ≥ 50 m, Punkt wird trotzdem gezeichnet) |
| `field-mode-position-dot` / `field-mode-position-accuracy` | Überlagerung mit dem Punkt (`role="img"`, Name „Deine ungefähre Position, Genauigkeit ±N m“, `data-accuracy-m`) und der Genauigkeitskreis (Radius ≥ 3 m); nimmt keine Zeigerereignisse an |

Formularfelder des Plans folgen unverändert `form-field-<name>`. Neue Muster unter den drei Präfixen werden hier ergänzt, bevor sie verwendet werden (R-020).

### 2.6 Stabilität als Vertrag

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | `data-testid`-Werte MÜSSEN als stabiler Schnittstellenvertrag behandelt werden: Sie DÜRFEN NICHT ohne Grund umbenannt oder entfernt werden. Eine Umbenennung MUSS gemeinsam mit der Anpassung der betroffenen Page Objects erfolgen (NFR-008a §5). | MUSS |
| R-022 | `data-testid`-Werte DÜRFEN NICHT aus übersetzbarem Text, aus Laufzeit-Zufallswerten oder aus rein positionsbasierten Ableitungen erzeugt werden — der Wert MUSS deterministisch und über Renders/Locales/Neustarts hinweg identisch sein. | MUSS |
| R-023 | Der Identifikator eines Elements MUSS über die relevanten Zustände (enabled/disabled, loading, error) hinweg stabil bleiben, sofern es dasselbe logische Element bleibt. | MUSS |

### 2.7 Accessibility-Selektoren als sekundäre Anker

| # | Regel | Stufe |
|---|-------|-------|
| R-024 | Die in UI-NFR-002 geforderten `role`- und `aria-label`-Attribute MÜSSEN so konsistent und aussagekräftig sein, dass sie als sekundäre Test-Anker (Locator-Priorität 4 in NFR-008a §5.2) dienen können — insbesondere für Komponenten, deren `data-testid`-Vergabe technisch schwierig ist (z.B. TreeView-Knoten). | MUSS |
| R-025 | Ein aussagekräftiges `aria-label` bzw. eine korrekte `role` ERSETZT NICHT den geforderten `data-testid` bei interaktiven Elementen (R-009); beide werden bereitgestellt, `data-testid` bleibt der primäre Anker. | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Seiten-Marker & geteilter Ladezustand

```
  Route: /stammdaten/species
  ┌───────────────────────────────────────────────┐
  │ <div data-testid="species-list-page">          │  ← eindeutiger Seiten-Marker
  │                                                 │
  │   während Laden:                                │
  │   ┌───────────────────────────────────────┐    │
  │   │ data-testid="loading-skeleton"        │    │  ← Tests warten hierauf
  │   └───────────────────────────────────────┘    │
  │                                                 │
  │   nach Laden:  data-testid="species-table"      │
  │   ┌───────────────────────────────────────┐    │
  │   │ species-row-tomato    | cell-status ●  │    │  ← Zeile per fachl. Schlüssel
  │   │ species-row-basil     | cell-status ●  │    │
  │   └───────────────────────────────────────┘    │
  │ </div>                                          │
  └───────────────────────────────────────────────┘
```

### 3.2 Selektor-Bindung: robust vs. fragil

```
  ❌ Fragil (verboten als einzige Option):      ✅ Robust (gefordert):
  ┌────────────────────────────────┐           ┌────────────────────────────────┐
  │ //div[3]/table/tr[2]/td[4]     │           │ [data-testid='species-table']  │
  │ .css-1qx8p3f-MuiButton-root    │           │   [data-testid='species-row-   │
  │ button:contains("Speichern")   │           │     basil'] [data-testid='...']│
  │ (bricht bei Layout/i18n)       │           │ [data-testid='submit-button']  │
  └────────────────────────────────┘           └────────────────────────────────┘
```

### 3.3 Namensschema (Kurzreferenz)

```
  Seite ............. <entity>-<view>-page      z.B. species-detail-page
  Formularfeld ...... form-field-<name>         z.B. form-field-name
  Aktions-Button .... <action>-button           z.B. submit-button
  Dialog ............ <zweck>-dialog             z.B. confirm-dialog
  Listeneintrag ..... <entity>-row-<key>         z.B. species-row-tomato
  Geteilte Marker ... loading-skeleton | empty-state | error-message

  Kartenlayout ...... card-title | card-subtitle
                      card-field-<columnId>       z.B. card-field-phase
                      card-chip-<columnId>        z.B. card-chip-status
  Formular-Aktionen . form-actions

  Reservierte Präfixe (REQ-053, §2.5.1):
    garden-plan-*   Editor/Gartenübersicht   z.B. garden-plan-page, garden-plan-canvas
    bed-view-*      Beetansicht
    field-mode-*    Feldmodus (?mode=field)
    plan-tool-<name> | plan-object-<key> | plan-handle-<position>

  Attribute (kein data-testid, qualifizieren ein Element):
    data-table-section=<id>   [data-testid='data-table'][data-table-section='…']
    data-chip-color=<palette> [data-testid='card-chip-…'][data-chip-color='error']
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Seiten-Marker**
    - [ ] Jede Route rendert einen eindeutigen `data-testid="<entity>-<view>-page"`
    - [ ] Kein Seiten-Marker erscheint auf zwei verschiedenen Routen
    - [ ] Geteilter `data-testid="loading-skeleton"` ist vorhanden und verschwindet nach dem Laden
- [ ] **Elementebene**
    - [ ] Alle interaktiven Elemente tragen einen `data-testid`
    - [ ] Formularfelder folgen `form-field-<name>`
    - [ ] Dialoge/Modale tragen einen `data-testid`
    - [ ] Testrelevante Ergebnis-/Statusanzeigen tragen einen sprechenden `data-testid`
- [ ] **Listen & Tabellen**
    - [ ] Wiederholte Einträge sind über einen fachlichen Schlüssel (nicht Index) adressierbar
    - [ ] Listen-/Tabellen-Container tragen einen `data-testid`
- [ ] **Namenskonvention & Stabilität**
    - [ ] Alle `data-testid`-Werte sind kebab-case und englisch
    - [ ] Werte folgen dem verbindlichen Namensschema (R-018)
    - [ ] Werte sind deterministisch (nicht aus Text/Zufall/Position abgeleitet)
    - [ ] Umbenennungen erfolgen synchron mit den betroffenen Page Objects
- [ ] **Accessibility-Anker**
    - [ ] `role`/`aria-label` sind konsistent genug für den Fallback-Locator (NFR-008a §5.2 Prio 4)
- [ ] **Testing**
    - [ ] Ein bestehendes Page Object je Seitentyp bindet ausschließlich an `data-testid`/`role` (kein positionsbasierter XPath)
    - [ ] Optionale Lint-/Review-Regel prüft, dass neue interaktive Komponenten einen `data-testid` mitliefern
    - [ ] Ein E2E-Smoke-Test navigiert alle Hauptseiten allein über Seiten-Marker

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Fragile Selektoren** | Tests brechen bei jeder Layout-/Textänderung, hohe Flakiness | Hoch | `data-testid`-Bereitstellung als MUSS, Page-Object-Kapselung |
| **Fehlende Seiten-Marker** | Tests können Route nicht deterministisch verifizieren, unsichere Waits | Hoch | Verpflichtender `<entity>-<view>-page`-Marker je Route |
| **Index-basierte Listen-Selektoren** | Falsche Zeile getroffen bei Sortier-/Filteränderung | Mittel | Fachlicher Schlüssel im Identifikator (R-014) |
| **i18n-/textgebundene Selektoren** | Tests brechen bei Sprachwechsel oder Textkorrektur | Hoch | Verbot text-/positionsbasierter Ableitung (R-022) |
| **Uneinheitliche Benennung** | Test-Autoren müssen Selektoren raten/DOM inspizieren | Mittel | Verbindliches, dokumentiertes Namensschema (R-018) |
| **Instabile Identifikatoren** | Umbenennungen brechen Tests unbemerkt | Mittel | `data-testid` als Vertrag, synchrone Page-Object-Pflege (R-021) |

---

**Dokumenten-Ende**

**Version**: 1.5
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-10-15
**Review**: Pending
**Genehmigung**: Pending
