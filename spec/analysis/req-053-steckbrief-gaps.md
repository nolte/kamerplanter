# REQ-053 WP 0.5b — Lückenliste der Steckbrief-Anreicherung (E-10)

> Betreiberentscheidung E-10 (REQ-053 v1.4 §32.2): Werte nur mit belastbarer Quelle je
> Wert; sonst bleibt das Feld `null` und steht hier — **kein stiller Default**. Die Liste
> ist der Dry-Run-Report aus Plan §3 Zeile 0.5b und die Arbeitsliste für spätere
> Nachbelegungen durch den `plant-info-document-generator`. Felder: `row_spacing_cm`
> (GP-FR-061), `light_requirement` (E-05, GP-FR-160), `nutrient_demand` +
> `nutrient_demand_source`/`_confidence` (GP-FR-138, H-004), `nitrogen_fixing` (K-001),
> `rotation_pause_years` (K-004, Art-Override und Familie).
>
> Konventionen: **n/a** = Feld für diesen Pflanzentyp nicht anwendbar (Zimmerpflanze ohne
> Beetkultur, Staude ohne Reihenkultur, Zierpflanze ohne Zehrerstufe) — kein Nachbelegungs-
> bedarf; **unbelegt** = Wert wäre plausibel, aber keine Fachquelle (Landwirtschaftskammer,
> LWG/LfL, Universität, RHS, Saatgut-Kulturanleitung) gefunden — Nachbelegungsbedarf;
> **Familienwert gilt** = kein Art-Override belegt, `BotanicalFamily.rotation_pause_years`
> greift. Quellen je gesetztem Wert stehen in den Steckbriefen (Abschnitte 1.9, 1.10, 6.1)
> und in `nutrient_demand_source` der Seeds.

## Batch 1 (Arten 1–30, `adiantum_raddianum` … `brassica_oleracea_var_capitata`) — 2026-10-16

### Bilanz

| Feld | gesetzt (mit Quelle) | `null` n/a | `null` unbelegt | Nachbelegungsbedarf |
|---|---|---|---|---|
| `row_spacing_cm` | 12 | 17 (14 Zimmerpflanzen, 3 Stauden/Beetzierpflanzen ohne Reihenkultur) | 1 | Allium schoenoprasum |
| `light_requirement` | 27 | 0 | 3 | Aglaonema commutatum, Aspidistra elatior, Begonia semperflorens |
| `nutrient_demand` (+ `_source`, `_confidence`) | 11 (high 4, medium 2, low 5) | 17 (Zierpflanzen, optional) | 2 (**Pflicht bei Nutzpflanzen**) | Anethum graveolens, Avena sativa |
| `nitrogen_fixing` | 12 (alle `false`, belegt) | 17 (Zierpflanzen) | 1 | Asparagus officinalis |
| `rotation_pause_years` (Art-Override) | 1 (Avena sativa 4) | 17 (Zierpflanzen) | 12 × „Familienwert gilt" (kein Override nötig); Asparagus officinalis Dauerkultur unbelegt | Asparagus officinalis (nur, falls ein Wert ≤ 8 belegbar ist) |
| `rotation_pause_years` (Familie) | 5 (Amaryllidaceae 4, Amaranthaceae 3, Apiaceae 4, Asteraceae 3, Brassicaceae 4) | 12 Zierpflanzen-Familien (`rotation_category = ornamental`) | 1 (Poaceae) | Poaceae — nur tertiäre Quellen (3), `spec/analysis/agrobiology-thresholds-req-053.md` §C „unverified" |

### Seed-Übernahme (Steckbrief → YAML) — Abweichungen von der Bilanz

| Art | Seed-Datei | Befund |
|---|---|---|
| Allium porrum, Beta vulgaris subsp. vulgaris | `adventskalender.yaml` (`new_species`) | **Werte nur im Steckbrief, nicht im Seed.** Der Adventskalender-Importer trägt `new_species`-Felder modellgetrieben (`Species.model_fields`), und `tests/unit/migrations/test_seed_adventskalender_harvest.py::test_real_yaml_has_no_field_drift` verbietet jeden Schlüssel, den das Pydantic-Modell nicht kennt — die sieben Beetplanungs-Felder kommen erst mit Migration M6 (GP-FR-139, Welle 1) ins Modell. Bis dahin ist `adventskalender.yaml` kein zulässiger Ort; der Extraktor muss die beiden Arten nach M6 erneut schreiben (Werte: Porree `row_spacing_cm` 30, `full_sun`, `heavy_feeder`/low, `nitrogen_fixing` false; Rote Bete 30, `full_sun`, `medium_feeder`/medium, false). Die Annahme „Schema vor Modell wird validiert, aber nicht geschrieben" aus WP 0.5a gilt für diese Datei nicht — Pipeline-Lücke für `plant-info-to-seed-yaml` Regel 6 / `seed-data-validator` `[SCHEMA-AHEAD-OF-MODEL]`. |
| Allium schoenoprasum, Anethum graveolens, Apium graveolens, Artemisia dracunculus, Avena sativa, Brassica oleracea var. botrytis/capitata | `plant_info_outdoor_1.yaml` (`species_enrichment`) | Felder stehen im Seed; `seed_plant_info_extended.py` überspringt unbekannte Enrichment-Felder bis M6 mit `enrichment_unknown_field`-Warnung (kein Crash, gemessen). Nach M6 greift die Fill-if-empty-Semantik. |
| Avena sativa | `plant_info_outdoor_1.yaml` | `row_spacing_cm` ohne `spacing_cm` (Drillsaat) — Validator-Warnung „row_spacing ⇒ spacing_cm" bleibt bewusst stehen; `compute_layout` kann Hafer nicht als Einzelpflanzen-Reihe legen (Saatstärke statt Abstand). |
| Brassica oleracea var. botrytis | `plant_info_outdoor_1.yaml` | Bestand `spacing_cm: "60"` > neues `row_spacing_cm: "50"` (LWG 50/50) — Validator `[AGROBIO-CHECK]`; Bestandswert nicht angefasst (Scope). |

### Lücken je Art × Feld

| Art | Feld | Status | Grund / Befund der Recherche |
|---|---|---|---|
| Aglaonema commutatum | `light_requirement` | unbelegt | RHS-Artseite ohne Standortangabe; Chicago Botanic Garden „Partial/Full Shade", NC State „Deep/Partial shade" — Spanne ohne Vorzug, keine Stufe wählbar |
| Aspidistra elatior | `light_requirement` | unbelegt | RHS: Position „Full shade, Partial shade" ohne Vorzug |
| Begonia semperflorens | `light_requirement` | unbelegt | RHS „Full shade, Partial shade"; Clemson HGIC „Sonne bis Halbschatten"; NC State alle vier Stufen — Spanne ohne Vorzug |
| Allium schoenoprasum | `row_spacing_cm` | unbelegt | RHS „Chives" und Wisconsin Extension nennen Horstabstand (15–20 cm), aber keinen Reihenabstand |
| Anethum graveolens | `nutrient_demand` | **unbelegt (Pflicht)** | LKSH/NiG/LWK NRW führen nur die Sammelgruppe „Kräuter" (Schwachzehrer), Dill nicht namentlich; LfULG Sachsen und DLR RLP nennen keine Zehrerstufe |
| Avena sativa | `nutrient_demand` | **unbelegt (Pflicht)** | Fruchtfolge-Quellen für den Garten führen kein Getreide; LFA MV 2025 nennt nur „eher extensive" Düngung |
| Avena sativa | `spacing_cm` (1.9) | n/a | Drillsaat-Bestandskultur — Quelle nennt Saatstärke (280–380 Körner/m²), keinen Pflanzabstand in der Reihe |
| Asparagus officinalis | `nitrogen_fixing` | unbelegt | keine gelesene Quelle ordnet Spargel einer Nicht-Leguminosen-Gruppe zu (LWK Niedersachsen, RHS, VT nennen den Punkt nicht) |
| Asparagus officinalis | `rotation_pause_years` | unbelegt | Dauerkultur: RHS rät nur „choose fresh ground"; Alt-Angabe „10–15 Jahre" im Steckbrief (5.3) unbelegt und > 8 (K-004-Obergrenze; gehört ggf. in `soil_persistence_years`, REQ-054 H-10) |
| Anemone hupehensis | `spacing_cm` (1.9) | unbelegt | RHS nennt nur die Endbreite (0,5–1 m), keinen Pflanzabstand — keine Ableitung aus der Wuchsbreite (E-10) |
| Astilbe chinensis | `spacing_cm` (1.9) | unbelegt | RHS nennt nur die Endbreite; Alt-Wert 1.6 „40–60" ohne Quelle |
| Anemone hupehensis, Aphelandra squarrosa, Asparagus setaceus, Astilbe chinensis | `nutrient_demand`, `nitrogen_fixing`, `rotation_pause_years` | n/a | Zierpflanzen — Zehrerstufe optional, keine Fruchtfolge-Quelle nennt sie |
| 14 Zimmerpflanzen (Adiantum, Aechmea, Aeschynanthus, Aglaonema, Alocasia, Aloe, Anthurium, Aphelandra, Ardisia, Asparagus setaceus, Aspidistra, Asplenium, Beaucarnea, Begonia rex) | `row_spacing_cm`, `spacing_cm` (1.9) | n/a | keine Beetkultur |
| Poaceae (Familie) | `rotation_pause_years` | unbelegt | LKSH 2020 nennt für Gräser keine Pause, SBB 2022 keinen Eintrag; nur tertiär (Plantura) 3 → `null`, Fallback `rotation_window_years` |

### Konfidenz `low` (eine oder widersprüchliche Quellen) — Nachschärfung erwünscht

| Art | `nutrient_demand` | Befund |
|---|---|---|
| Allium cepa | medium_feeder | SBB 2022 und Natur im Garten 2022: Mittelzehrer; LWK NRW 2016 und FiBL 2007: Schwachzehrer (2:2) |
| Allium porrum | heavy_feeder | LKSH: Starkzehrer; LWK NRW: Mittelstarkzehrer; Natur im Garten: Mittelzehrer |
| Allium sativum | medium_feeder | nur Natur im Garten 2022; SBB, LKSH, LWK NRW nennen Knoblauch nicht (Alt-Feld 1.1: light_feeder) |
| Artemisia dracunculus | light_feeder | nur Natur im Garten 2022, Sammelgruppe „Kräuter" |
| Asparagus officinalis | medium_feeder | LWK Niedersachsen „mittlere Nährstoffansprüche"; VT „medium-heavy feeder" (Alt-Feld 1.1/3.2: heavy_feeder) |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen — Folgearbeit, nicht Teil von WP 0.5b)

| Art | Bestand | belegter Wert (1.9/6.1) | Hinweis |
|---|---|---|---|
| Allium sativum | 1.6 Platzbedarf „10–15 / 25–30"; 1.1 `light_feeder` | 1.9 „15 / 30" (RHS); 6.1 `medium_feeder` (NiG, low) | Seed-`spacing_cm` bleibt; Zehrerstufe 1.1 vs 6.1 divergiert |
| Allium porrum | 1.6 Reihe „30–40" | 30 (RHS) | — |
| Allium schoenoprasum | 1.6 Platzbedarf „20–25" | 15–20 (RHS) | — |
| Allium cepa / sativum / porrum / schoenoprasum | 6.1 Alt-Zeile „Anbaupause (Jahre)" 3 / 3 / 3–4 / 4–5 | Familienwert Amaryllidaceae 4 (SBB, ÖLN) | Alt-Zeile ist nicht das Extraktionsfeld; kein Art-Override belegt |
| Anethum graveolens | 1.6 Reihe „15–20" | 8–15 (Wisconsin Ext.) | — |
| Apium graveolens | 1.6 „30–40 / 40–50" | 30–35 / 30–35 (BBZ Arenenberg „30 × 35", Zuordnung Reihe/In-Reihe in der Quelle nicht getrennt) | USU Extension: 30 / 60 |
| Apium graveolens var. rapaceum | 1.6 „35–40" | 30–35 (RHS, Arenenberg) | — |
| Asparagus officinalis | 1.1/3.2 `heavy_feeder`/„Starkzehrer"; 5.3 „10–15 Jahre kein Spargel nach Spargel" | `medium_feeder` (low) | — |
| Avena sativa | 1.6 Reihe „12–15"; 6.1 Alt „Anbaupause 2–3"; 5.4 „3–4 Jahre" | 10–14; 4 (LFA MV 2025, Selbstunverträglichkeit/Hafernematoden) | Art-Override 4 gesetzt, Familie Poaceae `null` |
| Beta vulgaris subsp. vulgaris | 1.6 „10–15 / 25–30" | 10 / 30 (LWG-Flyer Rote Bete, RHS); LWG „Sä- und Pflanztermine" nennt 25 / 8 | — |
| Brassica oleracea var. capitata | 1.6 „50–60 (klein) / 60–80 (groß)"; 6.1 Alt „Anbaupause 3–4" | 50 / 50 (LWG); Familienwert 4 (LKSH, SBB 4–5) | LWG stützt nur die Untergrenze kleiner Sorten |
| Asparagus setaceus | 6.1 Alt „Mittelzehrer" | — (Zimmerpflanze, unbelegt) | Alt-Zeile ohne Quelle |

### Lehren für Batch 2–7

1. Der `plant-info-document-generator` hat kein Edit-Werkzeug und schreibt Dateien komplett neu
   — zwei stille Nebenwirkungen (Tippfehler „korrigiert", Pflanzabstand aus Endbreite
   abgeleitet) wurden nur durch `git diff | grep '^-[^-]'` bzw. Lesen der Quelle-Zelle erkannt.
   Prüfpflicht je Sub-Batch: 0 entfernte Zeilen, Quelle-Zelle nennt „Pflanzabstand", nicht „spread".
2. RHS-Artseiten („Position") sind für `light_requirement` die verlässlichste Quelle; „Full sun,
   Partial shade" ohne Vorzug ergibt `null` — das trifft Zimmer- und Schattenpflanzen häufig.
3. Für Zehrerstufen reichen vier Quellen (LKSH, SBB 2022, Natur im Garten 2022, LWK NRW 2016)
   nur bei gängigem Gemüse zu `high`; Kräuter und Getreide stehen dort nur als Gruppe oder gar
   nicht → bei Batch 2 ff. gezielt Kulturanleitungen der Landesanstalten (LfULG, DLR, LFA) lesen.
4. Nicht erreichbar bzw. unbrauchbar waren wiederholt: extension.umn.edu (403), Missouri
   Botanical Garden (TLS), BZfE-PDFs (404) — nicht erneut ansteuern.
