# Frontend-Design-Review REQ-053 v1.2b — grafischer Editor

Datum: 2026-10-11 · Reviewer: `frontend-design-reviewer` (Agent) · Geprüft: §9, §17, §18, §19.4, §23, §24, §25, UI-NFR-001/002/003/012/019/022.
Zusammenfassung der Befunde und ihrer Einarbeitung in REQ-053 v1.3 (§9.7). Der Agent hat kein Schreibrecht; der Bericht wurde vom Aufrufer abgelegt und verdichtet.

| Befund | Kern | Eingearbeitet als |
|--------|------|-------------------|
| K-01 | Auswahl bei überlappenden Objekten undefiniert | GP-UX-032/033, GP-NFR-065 |
| K-02 | Pflanzenwahl auf dichten Beeten per Touch unmöglich (8–15 px Markerabstand) | GP-UX-034/035 |
| K-03 | Mehrfachauswahl, Polygon, Punkt löschen, Abbrechen, Alt ohne Touch-Entsprechung | GP-UX-036/037/038 |
| K-04 | Gestenkonflikte (Long-Press doppelt belegt, Tipp-Semantik, Doppelklick, Phantom-Touches) | GP-UX-040/041, GP-NFR-066 |
| K-05 | „Zoom %“ ohne Bezugsgröße, Beschriftungen in der Übersicht unsichtbar | GP-FR-150, GP-NFR-067 |
| K-06 | Eltern-Kind-Verhalten beim Verschieben/Skalieren/Löschen offen | GP-FR-151/152/153 |
| K-07 | Fokusmodell: bis zu 2 500 Tab-Stopps | GP-NFR-068/069/070 |
| W-01 | Snap ohne Prioritäten, Toleranz für Finger zu klein | GP-FR-154 |
| W-02 | Griffe an kleinen Objekten | GP-UX-048 |
| W-03 | Undo-Granularität | GP-FR-155 |
| W-04 | Fehlbedienungsschutz ungleichmäßig, „2 s destruktiv“ ohne Bezug | GP-UX-043, GP-FR-156, GP-UX-023 bereinigt |
| W-05 | Pfeile doppelt belegt, Redo uneinheitlich, Einzeltasten (WCAG 2.1.4), Anlegen per Tastatur | GP-UX-044/045/046 |
| W-06 | Beschriftungskollisionen | GP-UX-047 |
| W-07 | Eingabe der Sonne/Schatten-Angabe nicht spezifiziert | GP-FR-157 (Kacheln, Stapel-Zuweisung) |
| W-08 | Leerzustände unvollständig | GP-UX-049 |
| W-09 | Import-/Export-UI fehlt | GP-UX-050/051 |
| W-10 | Kopfzeile/Sheet auf sm/xs | GP-UX-052 |
| W-11 | Keine clientseitige Live-Validierung | GP-UX-053 |
| H-01…H-06 | Achsensymbole, Blickrichtung, Kiosk, Messprofile (INP), Prioritäts-Inkonsistenz, WCAG 1.4.13/2.5.1 | GP-UX-054/055/056, GP-NFR-071; GP-NFR-028 → MUST |

Bereinigte Widersprüche: Long-Press (GP-UX-008 ↔ GP-FR-027), Pfeiltasten (GP-FR-010 ↔ GP-FR-021), Redo (GP-FR-026 ↔ GP-UX-009), Beschriftungs-Zoom (GP-NFR-010 ↔ GP-UX-015), „2 s destruktiv“ (GP-UX-023), Doppelklick (GP-FR-023 ↔ GP-UX-006), GP-NFR-028 SHOULD/MVP. Noch **nicht** angepasst: GP-UX-006 (Info-Blase: WCAG 1.4.13 ausblendbar/hoverbar) und GP-NFR-020/-021/-023 (Verweis auf Roving-Tabindex GP-NFR-068).
