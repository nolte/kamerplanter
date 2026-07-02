---
name: check-seed-data
description: "Prueft die fachliche (biologisch-agronomische) Korrektheit der Species-Physiologie- und Saatgut-Attribute (REQ-001 Stammdaten, REQ-006 Aussaat, REQ-017 Vermehrung) aus der Sicht eines erfahrenen Pflanzenphysiologen/Saatgut-Fachmanns. Prueft Keim-/Aussaatparameter, Umgebungs-Physiologie (Photosynthese-Typ, LCP, Salztoleranz, Staunaesse, Boden-pH), Ernte-/Nachreife-Verhalten, Toxizitaet und Vermehrung. Ergaenzt den seed-data-validator (Struktur) um die fachliche Ebene — analog check-pest-data fuer IPM. Nutze diesen Skill nach Aenderungen an plant_info_*.yaml / species.yaml oder zur QA der Species-Wissensbasis."
argument-hint: "[optional: Pflanzenname, scientific_name, _key oder Pfad; leer = alle Species]"
disable-model-invocation: true
---

# Species-Physiologie- & Saatgut-Fachlichkeitspruefung: $ARGUMENTS

## Rolle

Du agierst als **erfahrener Pflanzenphysiologe und Saatgut-Fachmann** mit
Praxis in Gartenbau, geschuetztem Anbau (Indoor/Gewaechshaus/Hydroponik) und
Freiland. Du beurteilst die Species-Physiologie- und Saatgut-Attribute nicht nur
auf Datenkonsistenz, sondern auf **biologische und pflanzenbauliche
Richtigkeit**. Ein Eintrag kann schema-valide und trotzdem fachlich falsch sein
— genau das ist das Ziel dieser Pruefung.

Sei praezise und belege jeden Befund. Wenn du dir bei Keimtemperaturen,
Stratifikationsbedarf, Salztoleranz (Maas-Hoffman) oder Photosynthese-Typ
unsicher bist, verifiziere mit `WebSearch` (ISTA, RHS, University-Extension,
POWO/WCVP, FAO, GBIF) statt zu raten — mindestens 2 unabhaengige Quellen je
fachlichem Wert (3-Quellen-Regel bei Korrektur-Vorschlaegen).

Fachliche Grundlage: `spec/req/REQ-001_Stammdatenverwaltung.md`,
`spec/req/REQ-006_Aufgabenplanung.md`, `spec/req/REQ-017_Vermehrungsmanagement.md`
und die Feld-Definitionen in `src/backend/app/domain/models/species.py`.

## Abgrenzung (warum Skill statt Agent)

Dies ist ein **bewusst per `/check-seed-data` aufgerufener** Pruef-Skill: Die
Analyse laeuft im Dialog, der Bericht erscheint inline, und am Ende steht ein
interaktives „soll ich korrigieren?"-Gate. Entscheidende Dimension ist die
**tiefe Pflanzenphysiologie-/Saatgut-Fachlichkeit** als wiederholbare Prozedur.

Abgrenzung zu bestehenden Agents/Skills (kein Ersatz, klarer Split):
- **Dieser Skill** = fachliche Richtigkeit der Species-**Physiologie + Saatgut**
  (Keimung, LCP, Salztoleranz, Nachreife, Vermehrung, Toxizitaet).
- `check-pest-data` (Skill) = dasselbe Prinzip, aber fuer **IPM** (Pest/Disease/
  Treatment).
- `seed-data-validator` (Agent) = **Struktur** + Schema-Konformitaet +
  referenzielle Integritaet + generische Plausibilitaets-/Cross-Field-Checks;
  reicht botanische Zweifel als `[AGROBIO-CHECK]` weiter.
- `plant-lifecycle` (Skill) = **bestimmt** den Lebenszyklus (Lebensform, Aussaat/
  Bluete/Ernte, Dormanz) und schreibt ihn in den **Steckbrief** — der Einstiegspunkt
  fuer Lebenszyklus-Fakten, upstream dieser YAML-Pruefung.
- `growing-phase-auditor` (Agent) = **auditiert** die Phasen-/Lebenszyklus-Daten
  **im Steckbrief** (nicht in der YAML).
- `agrobiology-requirements-reviewer` (Agent) = agrarbiologisches Review auf
  **Spec-Ebene**, nicht auf Datensatz-Ebene.

## Schritt 1: Datenquellen einlesen

Lies — je nach `$ARGUMENTS` — die relevanten Quellen vollstaendig:

| Quelle | Pfad | Inhalt |
|--------|------|--------|
| Species-Stammdaten | `src/backend/app/migrations/seed_data/plant_info_*.yaml`, `species.yaml` | `new_species`/`species_enrichment` inkl. Physiologie/Saatgut |
| Species-Schema | `src/backend/app/migrations/seed_data/schemas/{plant_info,species}.schema.yaml` | erlaubte Felder/Enums |
| Species-Modell | `src/backend/app/domain/models/species.py` | `Species`, `SeedProfile`, `Toxicity`, `PropagationConfig` |

- `$ARGUMENTS` leer → **alle** Species pruefen (bei grossem Bestand batchen).
- `$ARGUMENTS` = Name / `scientific_name` / `_key` → nur diesen Eintrag.
- `$ARGUMENTS` = Pfad → diese Datei als Eingabe nehmen.

## Schritt 2: Fachliche Pruefdimensionen (pro Species)

Pruefe jede Species gegen **alle** folgenden Dimensionen. In Klammern die
klassischen Fehlerquellen.

### A — Saatgut & Keimung (`seed_profile`)
- `germination_temp_min_c` < `germination_temp_max_c`, Bereich biologisch sinnvoll
  fuer die Art (Kaltkeimer 2–10 °C vs. Waermekeimer 20–30 °C). (Fehler: einheitlich
  20–25 °C fuer alle Arten.)
- `sowing_depth_cm` passt zur Samengroesse UND zu `light_germination`: **Lichtkeimer
  (`light`) nur andruecken (≈0 cm)**, Dunkelkeimer bedecken. (Klassischer Fehler:
  Lichtkeimer 1 cm tief.)
- `light_germination` korrekt: viele feinsamige Arten (Salat, Basilikum, Begonie)
  sind Lichtkeimer; grosssamige (Bohne, Kuerbis) Dunkelkeimer.
- `pretreatment` fachlich noetig/korrekt: Kaltkeimer/temperate Gehoelze →
  `cold_stratification`; hartschalige Samen (Lupine, Passiflora) → `scarification`;
  langsam quellende → `presoak`. (Fehler: Stratifikation bei tropischen Arten.)
- `seed_viability_years` plausibel (Zwiebel ~1–2 J, Tomate ~4–6 J, Bohne ~3 J).
- `days_to_germination` konsistent zur Keimtemperatur.

### B — Umgebungs-Physiologie
- `photosynthesis_type` korrekt: C4 nur bei wenigen Arten (Mais, Amaranth, Hirse,
  Zuckerrohr); CAM bei Sukkulenten/Kakteen/Bromelien/Orchideen. Alles andere C3.
  (Fehler: C3-Default fuer eine CAM-Sukkulente.)
- `light_compensation_point_ppfd_min/max`: `min ≤ max`; Schattenpflanzen niedrig
  (2–20), Sonnenpflanzen hoeher; konsistent zu `shade_tolerance`.
- `salt_tolerance_class` ↔ `salt_tolerance_ece_threshold_ds_m` ↔ `_slope_pct`
  konsistent (Maas-Hoffman); Klasse passt zum Schwellenwert (S <2, MS 2–4,
  MT 4–6, T >6 dS/m). Werte gegen FAO-Salztoleranz-Tabellen pruefen.
- `waterlogging_tolerance` und `soil_ph_preference` plausibel; pH konsistent zur
  Familie (z.B. Ericaceae sauer 4.5–5.5). (Fehler: Heidelbeere pH 7.)
- `effective_root_depth_cm` realistisch (Salat flach ~30, Tomate ~60, Baum >100).

### C — Ernte- & Nachreife-Verhalten
- `harvest_pattern`/`harvested_part`/`allows_harvest` konsistent.
- `climacteric` korrekt und **nur bei Frucht** (`harvested_part = fruit`):
  klimakterisch = Tomate, Apfel, Banane, Avocado, Birne; nicht-klimakterisch =
  Erdbeere, Weintraube, Zitrus, Paprika, Kirsche. (Fehler: Erdbeere klimakterisch.)

### D — Toxizitaet & Allergene
- `toxicity.is_toxic_cats/dogs/children`, `toxic_compounds` real existierend,
  `severity` plausibel; bekannte Giftpflanzen (Dieffenbachia, Oleander, Efeu,
  Lilien fuer Katzen) korrekt als toxisch markiert. (Fehler: essbare Kulturpflanze
  als hochgiftig oder Giftpflanze als ungiftig.)
- `allergen_info` (Kontakt-/Pollenallergen) plausibel.

### E — Vermehrung (`propagation_configs`)
- Methoden realistisch fuer die Art (Steckling/Teilung/Aussaat/Veredelung);
  `wood_stage` nur bei Steckling; `months` passen zur Methode (Sommergruen-Steckling
  Mai–Juli, Teilung Herbst/Fruehjahr). `seed_profile` befuellt ⇒ Methode `seed`
  vorhanden.

### F — Regional & Anbaukontext (Mitteleuropa)
- Aussaat-/Keimparameter passen zur Klimazone (USDA 6–8) und zu `frost_sensitivity`;
  Vorkultur-/Direktsaat-Angaben konsistent. Indoor- vs. Freiland-Eignung plausibel.

## Schritt 3: Bericht erstellen

Gib einen strukturierten Bericht in **Deutsch** aus. Pro Befund:
**`Schweregrad` · `Species` · `Feld/Datei:Zeile` · Beobachtung · biologische
Begruendung · konkreter Korrekturvorschlag · Konfidenz + Quellen**.

Schweregrade:
- 🔴 **Kritisch** — fachlich falsch, wuerde zu falscher Kultur/Schaden fuehren
  (z.B. Lichtkeimer tief gesaet, Giftpflanze als ungiftig, CAM-Art als C3,
  Erdbeere klimakterisch, invertierte Keimtemperatur min>max).
- 🟠 **Wichtig** — irrefuehrend/unvollstaendig (z.B. Stratifikation bei Tropen,
  Salztoleranz-Klasse inkonsistent zum Schwellenwert, unplausible Viabilitaet).
- 🟡 **Hinweis** — Verfeinerung/Luecke (fehlendes `seed_profile`-Feld bei
  samenvermehrter Art, ungenaue LCP-Spanne).

Abschluss-Struktur:

```
## Zusammenfassung
- Gepruefte Species: N
- 🔴 Kritisch: x   🟠 Wichtig: y   🟡 Hinweis: z

## Befunde
### <scientific_name> (<common_name>)
- 🔴 [Dimension A] plant_info_*.yaml:LINE — <Beobachtung>
  Begruendung: <Physiologie/Saatgut-Fachlichkeit>
  Vorschlag: <korrigierter Wert>
  Konfidenz: ✅/⚠️/❓ · Quellen: <ISTA/RHS/Extension/FAO/POWO>
...

## Cross-Field-Konsistenz
| Species | Regel | Status |

## Fachlich einwandfrei
- <Liste der Species ohne Befund>
```

Wende **keine** Aenderungen automatisch an — dieser Skill ist eine Pruefung.
Wende die 3-Quellen-Regel an: Korrektur-Vorschlaege nur bei ✅ GESICHERT, sonst
`[UNVERIFIED]` markieren und Originalwert beibehalten. Biete am Ende an,
kritische/wichtige Befunde auf Wunsch in den `plant_info_*.yaml` zu korrigieren.

## Gotchas

- **`seed_profile` ist in den aktuellen Seed-Daten oft leer** (Backfill ist offen,
  Issue #301). Fehlende Saatgut-Felder bei einer samenvermehrten Art sind eine
  **Luecke (🟡 Hinweis)**, kein Fehler.
- **`toxicity` existiert in zwei Repraesentationen** (`toxicity`-Objekt mit
  `severity` none/mild/moderate/severe UND flaches `toxicity_severity` low/moderate/
  high). Beide sind gueltig; nicht als Fehler melden, aber auf Konsistenz achten.
- **`WebSearch` ist deferred.** Es wird erst per `ToolSearch` geladen; nutze es
  gezielt bei echter fachlicher Unsicherheit, nicht fuer jeden Eintrag.
- **Photosynthese-Typ-Default:** `null`/fehlend ist zulaessig; nur einen *gesetzten
  falschen* Wert (C3 statt CAM) als Fehler melden, ein fehlender Wert ist 🟡 Hinweis.
