---
name: Beschreibende Texte und Fachbegriff-Erklaerungen fehlen in der UI
description: User bemängelt fehlende Hintergrundinfos, Panel-Einleitungstexte und Fachbegriff-Erklaerungen in Formularen und Seiten
type: feedback
---

Beschreibende Texte in der UI muessen konsequent ergaenzt werden — Panel-Einleitungstexte, Hilfetext-Icons und Fachbegriff-Tooltips fehlen haeufig.

**Why:** Der User hat wiederholt festgestellt, dass Formulare und Seiten ohne erklaerende Texte ausgeliefert werden. Fachbegriffe wie EC, VPD, PPFD bleiben unerlaeutert. Panels haben keine Einleitungstexte die den Kontext erklaeren. Felder haben keine helperTexts oder Info-Icons. Das macht die App fuer Einsteiger unzugaenglich.

**How to apply:** Bei jeder Frontend-Implementierung (fullstack-developer) und jedem UI-Review (frontend-usability-optimizer) MUSS aktiv geprueft werden:
1. Jedes Panel/Card hat einen Einleitungstext (UI-NFR-008 R-038)
2. Jedes nicht-offensichtliche Feld hat ein Info-Icon mit Hilfetext (UI-NFR-008 R-042)
3. Fachbegriff-Felder verwenden HelpTooltip aus UI-NFR-011
4. Alle Hilfetexte sind als i18n-Keys in DE+EN vorhanden
