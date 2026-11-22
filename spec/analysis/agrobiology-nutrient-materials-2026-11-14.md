# Agrobiologie-Review: `NUTRIENT_MATERIALS` je Material (#2643, REQ-053 §32.5 Pkt. 15 c)

**Datum:** 2026-11-14
**Auftrag:** Betreiberentscheidung 2026-11-14 („`NUTRIENT_MATERIALS` geht je Material ins agrobiologische Review“)
**Grundlage:** Wave-8-Review `spec/analysis/agrobiology-req-053-wave8-ec.md` (R-001 … R-018), Regel E-10 (nur unabhängige, zitierbare Quellen zählen; eine Veröffentlichungsreihe mit gemeinsamer Datenlinie zählt als eine Quelle)
**Einschränkung des Laufs:** ohne Web- und Bibliothekszugang. Neue Quellen wurden nicht recherchiert; das Ergebnis stützt sich nur auf die im Wave-8-Review belegten Quellen.

## Was die Einstufung bedeutet

`NUTRIENT_MATERIALS` (`src/backend/app/domain/engines/task_completion_engine.py`) entscheidet, ob eine Bodenverbesserung (`soil_amendment`) mit Menge zusätzlich ein `feeding_event` schreibt. Das Material erscheint dann in der Düngehistorie der Pflanzen und in der Düngebilanz des Beets (GP-FR-125). Die getrennte Menge `N_INPUT_AMENDMENT_MATERIALS` (`nutrient_hint_engine.py`) entscheidet, ob die Gabe als N-Zufuhr die Regel R1 des Nährstoff-Hinweises zurücksetzt.

- **A** — Düngung: in `NUTRIENT_MATERIALS`.
- **A+N** — Düngung mit N-Zufuhr: zusätzlich in `N_INPUT_AMENDMENT_MATERIALS`.
- **B** — keine Düngung: reine Protokollzeile.

## Gesamtergebnis

Keines der zehn offenen Materialien erreicht heute die Schwelle für A oder A+N.

1. **Quellenlage.** Das Wave-8-Review belegt nur R-011 (Holzasche und Kalk heben den pH) qualitativ mit zwei institutionellen Quellen (UNH Extension, Alberta Agriculture). Sie tragen die Kalkwirkung, nicht eine Düngewirkung (K, P) der Holzasche.
2. **Asymmetrie der Fehler.** Eine falsche Einstufung A schreibt falsche Einträge in Düngehistorie und Düngebilanz; eine zu vorsichtige Einstufung B kostet nur eine fehlende Düngezeile, die Protokollzeile bleibt.

**Ergebnis:** Alle zehn Codes bleiben B. Beide Mengen bleiben unverändert. Kein Nachtrag bestehender Zeilen.

## Einstufung je Code

| Code | Einstufung | Tragende Quellen (E-10) | Begründung | Konfidenz |
|------|-----------|-------------------------|------------|-----------|
| `rock_dust` | B (ohne Einstufung) | keine | Nährstoffbeitrag (K, Mg, Spurenelemente) sehr langsam und herkunftsabhängig; eine Mengenbilanz wäre Scheingenauigkeit (nicht verifiziert) | niedrig |
| `biochar` | B (ohne Einstufung) | keine | unbeladen Bodenhilfsstoff, beladen Nährstoffträger; ein Code kann beides nicht abbilden — Datenmodellfrage, nicht nur Quellenfrage | mittel |
| `sand` | B | keine zitiert (Definition) | Strukturmaterial ohne nennenswerten Nährstoffgehalt | hoch |
| `perlite` | B | keine zitiert (Definition) | inertes Strukturmaterial | hoch |
| `coffee_grounds` | B (ohne Einstufung) | keine | ob frischer Kaffeesatz N zuführt oder bindet, ist offen; A+N würde R1 fälschlich zurücksetzen | niedrig |
| `green_manure` | B (ohne Einstufung) | keine (R-015 offen) | N-Beitrag nur bei Leguminosen, der Code unterscheidet das nicht; Überschneidung mit Modifier M1 und `plan_role = green_manure` (§16.3) — gehört in die Fruchtfolgelogik | mittel |
| `sulfur` | B (ohne Einstufung) | keine | primär pH-Senker; keine S-Bilanz in Spec oder Review | mittel |
| `lime` | B | R-011 (pH-Wirkung) | Kalkungsmittel; die Kategorie `liming` schreibt ohnehin kein `feeding_event`, A wäre ein Widerspruch | mittel bis hoch |
| `wood_ash` | B (ohne Einstufung) | R-011 nur für die Kalkwirkung | Mischfall Kalkung/K-P-Düngung plausibel, Düngewirkung unbelegt; Mengenangaben der Portale widersprechen sich um mehr als eine Größenordnung | niedrig bis mittel |
| `other` | B | nicht erforderlich | ein unbekanntes Material lässt sich nicht als Düngung einstufen | hoch |

## Vorgeschlagener Inhalt der beiden Mengen

```python
NUTRIENT_MATERIALS = {"compost", "manure", "horn_shavings"}
N_INPUT_AMENDMENT_MATERIALS = {"manure", "horn_shavings"}
```

Kein Nachtrag: bestehende `soil_amendment`-Zeilen mit diesen Codes haben kein `feeding_event`, und das bleibt richtig. Wechselt ein Code später nach A, wirkt das nur auf neue Einträge; ein Nachtrag wäre dann eine eigene Betreiberentscheidung.

## Offene Recherchepunkte (Vorschläge, nur mit Web-/Bibliothekszugang zu schließen)

| Nr. | Aussage | Fehlend | Empfohlene Recherche |
|-----|---------|---------|----------------------|
| R-019 | Gesteinsmehl liefert K, Mg, Spurenelemente sehr langsam, herkunftsabhängig | drei Quellen | Herstellerdatenblätter, LfL/LWK, Studien zur Silikat-Verwitterung |
| R-020 | Pflanzenkohle: unbeladen Bodenhilfsstoff, beladen Nährstoffträger | drei Quellen | EBC, DüMV, Hochschulstudien |
| R-021 | Sand und Perlite sind nährstofffreie Strukturmaterialien | drei zitierte Quellen | Scheffer/Schachtschabel, LfL, Substrat-Fachbuch |
| R-022 | Kaffeesatz: N-Zufuhr oder N-Bindung, C:N-Verhältnis | drei Quellen | peer-reviewte Studien, Extension, BGK |
| R-023 | Gründüngung: N-Beitrag nur bei Leguminosen, Menge | drei Quellen (R-015) | BGK, LfL, LWK, Extension |
| R-024 | Elementarer Schwefel senkt den pH; S-Düngung im Hausgarten | drei Quellen | LfL/LWK, Extension |
| R-025 | Kalk: Ca/Mg-Zufuhr als Düngewirkung neben der pH-Wirkung | Düngewirkung, drei Quellen | VDLUFA-Standpunkt Kalk, LfL, BGK |
| R-026 | Holzasche: K- und P-Gehalte, Düngewirkung, Mengen | drei Quellen, europäische Quelle | BGK/LfL-Merkblätter, Düngemittelverordnung |

Priorität hätten `wood_ash` und `green_manure` (häufig im Beet, größte Wirkung auf R1 und Düngebilanz). Die Datenmodellfragen zu `biochar` (beladen/unbeladen) und `green_manure` (Leguminose ja/nein) lassen sich nicht mit Quellen lösen; sie gehören in die Spec.
