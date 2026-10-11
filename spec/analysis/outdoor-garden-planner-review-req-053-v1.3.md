# Outdoor-Gärtner-Review REQ-053 v1.2b — Editor, Standortmerkmale, Import/Export

Datum: 2026-10-11 · Reviewer: `outdoor-garden-planner-reviewer` (Agent). Zahlen mit „unverifiziert“ sind Praxisschätzungen des Reviewers und nicht belegt (O-17).

| Befund | Kern | Eingearbeitet als |
|--------|------|-------------------|
| K-01 | Tageszeit der Sonne fehlt (Morgen- vs. Nachmittagssonne) | `site_conditions.sun_profile`, GP-FR-158 |
| K-02 | Saisonale Schwankung durch Laubschatten | GP-FR-159 |
| K-03 | Keine Eignungsprüfung Beet ↔ `Species.shade_tolerance` | GP-FR-160 (`site_fit`), O-16 |
| K-04 | Backup MUST, Wiederherstellung (Import) nur SHOULD | GP-FR-170, O-18 |
| K-05 | Vorjahresplan als Vorlage fehlt | GP-FR-171, O-20 |
| W-01 | Frostsenke/Kaltluft/Wärmespeicher; `frost_exposed` nur Bool | `microclimate`, GP-FR-162 |
| W-02 | Schwellen fest, Äquinoktium als Sommerbezug fragwürdig | GP-FR-164, O-17 |
| W-03 | Wind | GP-FR-163 |
| W-04 | Drainage/Feuchte nur im Bodentab | GP-FR-169 (Karten-Ebenen) |
| W-05 | Wurzeldruck/Allelopathie | GP-FR-165 |
| W-06 | Erreichbarkeit/Beetbreite | GP-FR-166 |
| W-07 | Wasserzugang als Beetkennzahl | GP-FR-167 |
| W-08 | Hang pro Beet | GP-FR-168 |
| W-09 | Hintergrundbild zu niedrig priorisiert | GP-FR-033 → SHOULD, O-19 |
| W-10 | Beet per Maßeingabe anlegen | GP-UX-046 |
| W-11 | Teil-Export, Import in andere Site | GP-FR-172 |
| W-12 | Beet-Vorlagen teilen | GP-FR-173 |
| W-13 | CSV-Import für Beetlisten | GP-FR-174 |
| W-14 | CSV-Spalten ohne Standortmerkmale | GP-FR-175 |
| W-15 | Parzellenliste im PDF | GP-FR-176 |
| H-01/H-02 | Manuell vs. abgeleitet; Erfassung als Kurzbefragung | §10.2 Einleitung, GP-UX-057 |
| H-04/H-05 | Überdimensioniert: 12 Maßstabsstufen, PNG-Wasserzeichen, SVG-Download, GeoJSON | Anpassungen in §23.1, O-21 |
| H-06 | Schema-Rückwärtskompatibilität | GP-NFR-072 |

Offene Betreiberfragen: siehe REQ-053 §32.1 (O-16…O-21). Abgrenzung zu REQ-054: `site_fit` wird als Optimierungskriterium wiederverwendet; die Saison-Kopie ist nur die Datenkopie.
