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

## Batch 2 (Arten 31–60, `brassica_oleracea_var_gemmifera` … `dahlia_hapet_daydream`) — 2026-10-16

Konventionen wie bei Batch 1. Tally je Art: `spacing_cm (1.9)` | `row_spacing_cm` | `light_requirement` | `nutrient_demand` | Konfidenz | `nitrogen_fixing` | `rotation_pause_years`.

### Bilanz je Art

| Art | spacing | row | light | nutrient_demand | Konf. | N-Fix | Pause |
|---|---|---|---|---|---|---|---|
| Brassica oleracea var. gemmifera | 60 | 60 | full_sun | heavy_feeder | medium | false | Familie |
| Brassica oleracea var. gongylodes | 15 | 30 | full_sun | medium_feeder | medium | false | Familie |
| Brassica oleracea var. italica | 30–45 | 45 | full_sun | heavy_feeder | medium | false | Familie |
| Brassica oleracea var. sabellica | 30–60 | 45 | full_sun | heavy_feeder | medium | false | Familie |
| Buxus sempervirens | 30–40 | n/a | null | n/a | — | null | n/a |
| Calendula officinalis | null | 40–60 | full_sun | n/a | — | false | Familie |
| Cannabis sativa | null | null | null | null (Pflicht) | — | false | 3 (low) |
| Capsicum annuum | 40–50 | 40–50 | full_sun | heavy_feeder | low | false | Familie |
| Cattleya hybrida, Chamaedorea elegans, Chlorophytum comosum, Codiaeum variegatum, Crassula ovata, Ctenanthe burle-marxii, Cyclamen persicum (keine 6.1) | n/a | n/a | null / partial_shade / partial_shade / partial_shade / full_sun / partial_shade / partial_shade | n/a | — | n/a | n/a |
| Ceropegia woodii, Clivia miniata, Curio rowleyanus | n/a | n/a | partial_shade / partial_shade / full_sun | n/a | — | null | n/a |
| Cichorium intybus | 30 | 30 | full_sun | medium_feeder | low | false | Familie |
| Citrullus lanatus | 107–152 | 183 | full_sun | null (Pflicht) | — | null | Familie |
| Clematis spp. | null | n/a (freie Pflanzung) | null | n/a | — | null | n/a |
| Coffea arabica | n/a | n/a | partial_shade | n/a | — | null | n/a |
| Coriandrum sativum | 20–25 | 12–30 | full_sun | light_feeder | low | false | Familie |
| Cornus mas | null | n/a (freie Pflanzung) | null | n/a | — | null | n/a |
| Cucumis melo | 60 | 150–180 | full_sun | null (Pflicht) | — | false | Familie |
| Cucumis sativus | 30–45 | 120–180 | full_sun | heavy_feeder | medium | false | Familie |
| Cucurbita maxima | 75–100 | 150 | full_sun | heavy_feeder | high | false | Familie |
| Cucurbita pepo | 100 | 100 | full_sun | heavy_feeder | high | false | Familie |
| Dahlia 'Embassy' / 'Hapet Daydream' | 60 | n/a (freie Pflanzung) | full_sun | n/a | — | null | Familie |

### Lücken je Art × Feld

| Art | Feld | Status | Grund / Befund der Recherche |
|---|---|---|---|
| Cannabis sativa | `nutrient_demand` | **unbelegt (Pflicht)** | keine Fachquelle für eine Zehrerstufe gelesen |
| Cannabis sativa | `row_spacing_cm`, `spacing_cm` | unbelegt | TFZ 2023 (Körnerhanf 25–45 / Faser 12–20) und Schweizer Bauer (Blütenstände 50/100/150) beschreiben Feldkultur; Steckbrief meint Einzelpflanzen 80–120 |
| Cannabis sativa | `light_requirement` | unbelegt | Abschnitt 1.7 stützt sich nur auf Blog/Hersteller |
| Cannabis sativa | `rotation_pause_years` 3 | Konfidenz low | einzige Quelle Schweizer Bauer Dossier 2018 (FiBL-Autoren „2–3 Jahre"); Cannabaceae-Familienwert als Kandidat 3, schwach |
| Buxus sempervirens | `light_requirement` | unbelegt | RHS „sun or shade" ohne Vorzug |
| Buxus sempervirens | `nitrogen_fixing` | unbelegt | Buxaceae ohne Familienwert; Dauergehölz |
| Calendula officinalis | `spacing_cm` | unbelegt | LfL Sachsen 2006 nennt nur Reihenabstand 40–60 (Feldanbau); Blog-Werte 20–30 verworfen |
| Calendula officinalis | `nutrient_demand` | n/a | Natur im Garten führt sie als Erholungs-/Gründüngungsbeet, keine Zehrerstufe |
| Cattleya hybrida | `light_requirement` | unbelegt | RHS nur C. labiata „Full sun, Partial shade" ohne Vorzug |
| Clematis spp. | `spacing_cm` | unbelegt | RHS nennt nur Wandabstand 30–45 cm; Händlerwert 80 cm verworfen |
| Clematis spp. | `light_requirement` | unbelegt | RHS „sunny or part-shaded" ohne Vorzug |
| Clivia miniata | `light_requirement` | knapp belegt | partial_shade nach RHS-Kulturtext („bright, filtered light"), RHS-Position „Full sun, Partial shade" — Nachschärfung erwünscht |
| Codiaeum variegatum | `light_requirement` | schwach belegt | RHS-Eintrag nur auf Varietätsebene (var. pictum) |
| Cornus mas | `spacing_cm` | unbelegt | RHS nur Endbreite 2,5–4 m; LFA-MV-Versuch 4,5×1,5 m als PDF unlesbar |
| Cornus mas | `light_requirement` | unbelegt | RHS „full sun or partial shade" ohne Vorzug |
| Cornus mas | `nutrient_demand`, `nitrogen_fixing` | n/a/unbelegt | Wildobst/Gehölz; Cornaceae ohne Familienwert |
| Citrullus lanatus | `nutrient_demand` | **unbelegt (Pflicht)** | LKSH/SBB nennen nur Kürbis, Gurke, Zucchini |
| Citrullus lanatus | `nitrogen_fixing` | unbelegt | nur Cucumis („Melone/Zuckermelone") gelistet |
| Cucumis melo | `nutrient_demand` | **unbelegt (Pflicht)** | LKSH nur Kürbis, SBB Zuckermelone nur in der Anbaupausen-Tabelle, NiG ohne Melone; Plantura/utopia „Starkzehrer" verworfen |
| Cichorium intybus | `nutrient_demand` low | Konfidenz low | nur SBB Tab. 2 (Radicchio/Endivie), Chicorée nicht gelistet |
| Coriandrum sativum | `nutrient_demand` low | Konfidenz low | LKSH + NiG nur Sammelgruppe „Kräuter"; `nitrogen_fixing` false über zwei Quellen abgeleitet (DLR Doldenblütler, LKSH Doldenblütler ≠ Hülsenfrüchte), Koriander nicht namentlich |
| Capsicum annuum | `nutrient_demand` low | Konfidenz low | SBB/NiG S.2 Starkzehrer, NiG S.3 Schema Mittelzehrer |
| Cucurbita pepo | Abstände | Quelle schwach | Herstellerangabe Bingenheimer ('Solara') über Händlerseite violey.com; Gartenakademie RLP nennt keine Abstände |
| Calendula, Cannabis, Citrullus, Cornus mas, Cucumis melo | `rotation_pause_years` | Familienwert gilt | kein Art-Override belegt (außer Cannabis 3); Cannabaceae/Cornaceae/Buxaceae ohne Familienwert |
| Zierpflanzen (Cattleya, Ceropegia, Chamaedorea, Chlorophytum, Clematis, Clivia, Codiaeum, Coffea, Crassula, Ctenanthe, Curio, Cyclamen, Dahlia ×2, Buxus) | `nutrient_demand`, `rotation_pause_years` | n/a | keine Fruchtfolge-Quelle nennt Zehrerstufen für Zierpflanzen |
| Zimmerpflanzen (Cattleya, Ceropegia, Chamaedorea, Chlorophytum, Clivia, Codiaeum, Coffea, Crassula, Ctenanthe, Curio, Cyclamen) | `row_spacing_cm`, `spacing_cm` | n/a | keine Beetkultur |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert (1.9/6.1/1.10) | Hinweis |
|---|---|---|---|
| Brassica oleracea var. gongylodes | 1.6 „25–30" | 15 / 30 (RHS) | — |
| Brassica oleracea var. italica | 1.6 „40–50" | 30–45 / 45 (RHS Calabrese) | OSU 46/91 verworfen |
| Brassica oleracea var. sabellica | 1.6 „50–60" | 30–60 / 45 (RHS) | — |
| Calendula officinalis | 1.6 „20–30" | ungestützt | — |
| Cannabis sativa | 1.6 „80–120"; 7.1 Alt „Anbaupause 2–3" | ungestützt; Override 3 | — |
| Cichorium intybus | 1.6/1.3 „25–30 / 30–40" | 30 / 30 (Kiepenkerl/Sperli, Quadratverband-Lesart) | LWG 2111 Zuckerhut 40/35 in Quelle-Zelle |
| Citrullus lanatus | 1.6 „80–120 / 150–200"; 6.1 Alt „Starkzehrer", 1.1 heavy_feeder | 107–152 / 183 (ACES, Clemson, umgerechnet); Zehrerstufe unbelegt | deutsche Mini-Sorten (100/120, 80/80) nicht übernommen |
| Coriandrum sativum | 1.6 „25–30", „Halbschatten für Blatternte" | 20–25 / 12–30; full_sun (USU, Kiepenkerl) | — |
| Cucumis sativus | 1.6 „60–100" | 30–45 / 120–180 (Bodenkultur) | Rankhilfe enger, in Quelle-Zelle |
| Cucumis melo | 1.6 „60–100 / 120–150"; 6.1 Alt „Starkzehrer", 1.1 heavy_feeder | 60 / 150–180 (US-Extension umgerechnet); Zehrerstufe unbelegt | — |
| Cucurbita maxima | 1.6 „150–200" | 75–100 / 150 (LFA MV, LWK NRW) | — |
| Cucurbita pepo | 1.6 „80–100" | 100 / 100 (Bingenheimer) | — |
| Dahlia 'Hapet Daydream' | 1.6 Sortenbreite 60–75 | 60 (RHS-Untergrenze „at least 60 cm") | RHS deckt die Sortenbreite nicht |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Brassica oleracea var. gemmifera | `adventskalender.yaml` (`new_species`) — modellgetrieben gesperrt bis Migration M6 (siehe Batch 1); Werte nur im Steckbrief |
| Chlorophytum comosum | nur `plant_info.yaml` species_enrichment, Importer ungeguardet — Werte nur im Steckbrief |
| Dahlia 'Embassy', 'Hapet Daydream' | kein Seed-Eintrag für Dahlia pinnata — Werte nur im Steckbrief |
| Capsicum annuum | `species_enrichment`-Eintrag in `plant_info_outdoor_1.yaml` existierte bereits (Brief ging von „neu anlegen“ aus) — sieben Felder dort ergänzt, kein Duplikat-Key; Capsicum in `adventskalender.yaml` unangetastet |
| Citrullus lanatus, Cucumis melo | Seed hatte noch kein `spacing_cm` — aus 1.9 neu gesetzt ("107–152" / "60") |
| 13 Arten mit Seed-`spacing_cm` ≠ 1.9 | Bestandswerte unverändert (Scope): gongylodes 28↔15, italica 45↔30–45, sabellica 50↔30–60, Buxus 30↔30–40, Capsicum 45↔40–50, Cichorium 28↔30, Coriandrum 27↔20–25, Cucumis sativus 80↔30–45, Cucurbita maxima 175↔75–100, Cucurbita pepo 90↔100; Calendula 30, Clematis 100, Cornus mas 300 ohne Steckbrief-Beleg (1.9 DATEN FEHLEN) |
| Familien-Seeds | `botanical_families.yaml`: Solanaceae und Cucurbitaceae `rotation_pause_years: 4` (belegt, `agrobiology-thresholds-req-053.md` §C) |

### Lehren aus Batch 2

1. Der `plant-info-document-generator` hat erneut still Tippfehler/Wortlaut „korrigiert" (Cichorium 2, Citrullus 1, Cucumis sativus 1, Dahlia 2 Zeilen). `git diff | grep '^-[^-]'` allein übersieht Listenzeilen, die mit `- ` beginnen (Diff-Präfix `--`): zusätzlich `git diff --numstat` auf Löschungen prüfen.
2. Melone/Wassermelone und Cannabis haben keine belastbare Zehrerstufen-Quelle in den üblichen Fruchtfolge-Merkblättern (LKSH, SBB, NiG).
3. Gehölze/Stauden (Clematis, Cornus mas, Buxus): RHS nennt Endbreite statt Pflanzabstand — nie ableiten.

## Batch 3 (Arten 61–90, `dahlia_pinnata_great_silence` … `goeppertia_makoyana`) — 2026-10-17

Konventionen wie bei Batch 1 und 2. Auswahl: alphabetische Dateiliste von `spec/knowledge/plants/*.md`, Position 61–90 (Batch 1 + 2 = Position 1–60, keine Überschneidung). Tally je Art: `spacing_cm (1.9)` | `row_spacing_cm` | `light_requirement` | `nutrient_demand` | Konfidenz | `nitrogen_fixing` | `rotation_pause_years`.

### Bilanz je Art

| Art | spacing | row | light | nutrient_demand | Konf. | N-Fix | Pause |
|---|---|---|---|---|---|---|---|
| Dahlia 'Great Silence' / 'Armateras' / 'Lavender Perfection' | 60 | freie Pflanzung | full_sun | null | — | null | null |
| Daucus carota | 3–5 | 25–30 | full_sun | medium_feeder | low | false | 5 (Art-Abweichung, Familie 4) |
| Delphinium elatum | null | freie Pflanzung | full_sun | null | — | null | null |
| Echinacea purpurea | null | freie Pflanzung | full_sun | null | — | null | null |
| Eruca vesicaria | 15–23 | 15 | null | light_feeder | low | false | Familie |
| Foeniculum vulgare | 25 | 40 | full_sun | medium_feeder | low | false | Familie |
| Fragaria x ananassa | 25–30 | 40 | full_sun | medium_feeder | low | false | 4 |
| Forsythia x intermedia | 45–60 (nur Hecke) | freie Pflanzung | full_sun | n/a | — | n/a | n/a |
| Geranium sanguineum | null | freie Pflanzung | null | n/a | — | n/a | n/a |
| Glycine max | 10–20 | 18–75 | null | null | — | true | null |
| Dendrobium, Dracaena angolensis, Dypsis, Fatsia, Gardenia, Goeppertia ×2 | n/a | n/a | partial_shade | n/a | — | n/a | n/a |
| Dracaena marginata, Echeveria, Ficus benjamina | n/a | n/a | full_sun | n/a | — | n/a | n/a |
| Dieffenbachia, Dracaena trifasciata, Drachenpalmen, Epipremnum, Euphorbia pulcherrima, Ficus elastica, Ficus lyrata, Fittonia | n/a | n/a | null | n/a | — | n/a | n/a |

### Lücken (Wert `null`, Grund)

| Art | Feld | Grund |
|---|---|---|
| Dieffenbachia, Dracaena trifasciata, Epipremnum, Euphorbia, Ficus elastica, Drachenpalmen, Geranium sanguineum, Eruca, Glycine max | `light_requirement` | RHS nennt Spanne ohne Vorzug („Full sun, Partial shade"); bei Eruca und Glycine max keine Standortstufe gelesen |
| Ficus lyrata | `light_requirement` | RHS-Positionsfeld „Full sun", Kulturtext „full sun or partial shade" widerspricht — konservativ null |
| Fittonia | `light_requirement` | RHS nennt nur „bright light, out of direct sun", keine Standortstufe |
| Delphinium, Echinacea, Geranium sanguineum | `spacing_cm` | RHS nennt Endbreite/Etikett, keinen Pflanzabstand; Echinacea 1.6 „40–50" von keiner Quelle gestützt |
| Dahlien ×3, Delphinium, Echinacea, Glycine max | `nutrient_demand`, `rotation_pause_years` | Zierpflanzen ohne Zehrerstufe in Fruchtfolge-Quellen; Glycine max keine Zehrerstufen-Quelle gelesen |
| Dahlien ×3, Delphinium, Echinacea | `nitrogen_fixing` | nicht belegt |
| Foeniculum, Eruca | `rotation_pause_years` | nur Familienwert Apiaceae/Brassicaceae 4 gestützt |
| Zimmerpflanzen (Abschnitt 6 „Entfällt") | 6.1-Felder | kein 6.1-Abschnitt; Felder bleiben null |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert | Hinweis |
|---|---|---|---|
| Dahlien ×3 | 1.6 „60–80 / 60–70 / 60–90" | 60 (RHS „about 60cm apart") | Untergrenze, größere Sorten mehr |
| Daucus carota | 6.1 Alt „Anbaupause 3–5", „Mittelzehrer" | Pause 5 (LKSH); oekolandbau.de nennt Schwachzehrer | Konfidenz deshalb low |
| Dracaena angolensis | 1.7 „bevorzugt volle Sonne" | partial_shade (NC State) | Quelle gewinnt |
| Eruca vesicaria | 1.6 „5–10 / 20 cm"; 6.1 Alt „Anbaupause 2–3" | 15–23 / 15 (LWG 2168, OSU); SBB 4–5 | — |
| Echinacea purpurea | 1.6 „40–50" | keine Quelle | 1.9 DATEN FEHLEN |
| Foeniculum vulgare | 6.1 Alt „Anbaupause 2–3" | SBB 4–5 (Familie 4); Zehrerstufe LWG/NiG Mittelzehrer, SBB Starkzehrer | Konfidenz low |
| Fragaria x ananassa | 1.6 „60–80" Reihenabstand; 6.1 Alt „3–4 Jahre" | 40 (LWG 3182); RHS 35–40 / 75; LWG Pause „4–5" -> 4 | — |
| Glycine max | 1.6 „5–10 / 40–60" | 10–20 / 18–75 (OMAFRA Edamame); LfL Körnersoja 12,5–50 in Quelle-Zelle | — |
| Forsythia x intermedia | 1.6 Solitär „150–200" | 45–60 (RHS, nur Heckenpflanzung) | Wert gilt nur für Hecke |
| Ficus benjamina | 1.7 Toleranz partial_shade | Anspruch full_sun (RHS) | formal korrekt, für Zimmerkultur ungewöhnlich sonnig |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Fragaria x ananassa | nur `plant_info.yaml`, Importer ungeguardet — Werte nur im Steckbrief |
| Dahlien ×3, Drachenpalmen | kein Seed-Eintrag — Werte nur im Steckbrief |
| Eruca vesicaria, Glycine max | 1.9 `spacing_cm` nicht übernommen: `species.yaml` hat bereits „10--15", der Importer füllt `species_enrichment` nur fill-if-empty |
| Seed-`spacing_cm` ≠ 1.9 | Bestand unverändert: Daucus 5↔3–5, Foeniculum 28↔25, Forsythia 150-200↔45–60 (Hecke), Delphinium 50, Echinacea 40, Geranium 30-40 (1.9 DATEN FEHLEN) |
| Basisarten aus `species.yaml` | Daucus, Foeniculum, Eruca, Glycine, Epipremnum, Dracaena trifasciata: Felder in den bestehenden `species_enrichment`-Eintrag |

### Lehren aus Batch 3

1. Der `plant-info-document-generator` lief in diesem Batch ohne Bash und konnte `git diff --numstat` nicht selbst prüfen (Zeilenzahl-Selbstprüfung); die Prüfung durch den Aufrufer ergab 0 Löschungen. Prüfpflicht beim Aufrufer bleibt.
2. Ein Agent trug eine Lichtstufe aus „bright, filtered light" ab, obwohl die RHS-Position eine Spanne ohne Vorzug nennt (Dieffenbachia); auf null zurückgesetzt. Dem Agenten die Regel „Spanne ohne Vorzug = null" ausdrücklich mitgeben.
3. Gehölze/Stauden: RHS gibt nur Endbreite oder Heckenabstand — Pflanzabstand nur bei ausdrücklichem „plant … apart".

## Batch 4 (Arten 91–120, `goeppertia_orbifolia` … `malus_domestica`) — 2026-10-17

Konventionen wie bei Batch 1–3. Auswahl: alphabetische Dateiliste von `spec/knowledge/plants/*.md` (ohne `_*`), Position 91–120 (Batch 1–3 = Position 1–90, keine Überschneidung). Tally je Art: `spacing_cm (1.9)` | `row_spacing_cm` | `light_requirement` | `nutrient_demand` | Konfidenz | `nitrogen_fixing` | `rotation_pause_years`. „n/a" = Zimmerpflanze bzw. Abschnitt 6 „Entfällt"; „frei" = freie Pflanzung, keine Reihenkultur.

### Bilanz je Art

| Art | spacing | row | light | nutrient_demand | Konf. | N-Fix | Pause |
|---|---|---|---|---|---|---|---|
| Lactuca sativa | 30 | 30 | full_sun | medium_feeder | medium | false | Familie (Asteraceae 3) |
| Luffa aegyptiaca | 40–100 | 150–200 | full_sun | null | — | null | Familie (Cucurbitaceae 4) |
| Lens culinaris | null | null | null | null | — | true | Familie (Fabaceae 6) |
| Helianthus annuus | null | null | full_sun | null | — | null | null |
| Hordeum vulgare | null | null | null | null | — | null | null |
| Humulus lupulus | null | null | null | null | — | null | null |
| Levisticum officinale | 30–45 | null | null | null | — | null | Familie (Apiaceae 4) |
| Lupinus polyphyllus | null | frei | null | n/a | — | true | null |
| Helleborus niger | 30–36 | frei | partial_shade | n/a | — | null | null |
| Hemerocallis spp. | 25–40 | frei | full_sun | n/a | — | null | null |
| Hosta spp. | null | frei | partial_shade | n/a | — | n/a | n/a |
| Hydrangea macrophylla | null | frei | partial_shade | n/a | — | null | null |
| Impatiens walleriana | 20–25 | frei | partial_shade | n/a | — | n/a | n/a |
| Lavandula angustifolia | null | frei | full_sun | n/a | — | n/a | n/a |
| Ligustrum vulgare | null | frei | null | n/a | — | null | null |
| Malus domestica | null | frei | full_sun | n/a | — | null | null |
| Goeppertia orbifolia, Guzmania lingulata, Howea forsteriana, Kalanchoe blossfeldiana | n/a | n/a | partial_shade | n/a | — | n/a | n/a |
| Lithops spp., Kalanchoe daigremontiana | n/a | n/a | full_sun | n/a | — | n/a | n/a |
| Gymnocalycium, Haworthiopsis, Hedera helix, Hibiscus rosa-sinensis, Hippeastrum, Hoya carnosa, Jasminum polyanthum, Livistona chinensis | n/a bzw. null | n/a bzw. frei | null | n/a | — | n/a | n/a |

### Lücken (Wert `null`, Grund)

| Art | Feld | Grund |
|---|---|---|
| Hedera helix, Humulus lupulus, Jasminum polyanthum, Livistona chinensis, Ligustrum vulgare | `light_requirement` | RHS nennt Spanne ohne Vorzug |
| Haworthiopsis fasciata, Hoya carnosa, Hibiscus rosa-sinensis, Levisticum officinale, Lupinus polyphyllus | `light_requirement` | Quellen widersprechen sich (RHS-Positionsfeld vs. Kulturtext bzw. Artseite vs. Guide) |
| Gymnocalycium, Hordeum, Lens, Hippeastrum | `light_requirement` | keine Standortstufe gelesen („bright, filtered light" ist keine Stufe) |
| Helianthus, Hordeum, Humulus, Lens, Levisticum (Reihe), Lavandula, Hosta, Hydrangea, Ligustrum, Lupinus, Malus | `spacing_cm` / `row_spacing_cm` | RHS nennt nur Endbreite bzw. Obergrenze; Getreide/Hülsenfrüchte nach Saatstärke; Hopfen/Sonnenblume: Fachquellen als PDF nicht lesbar |
| Lens, Hordeum, Humulus, Helianthus, Levisticum, Luffa | `nutrient_demand` | keine artspezifische Zehrerstufe gelesen (LK NRW nennt nur Sammelgruppe „Kräuter") |
| Zierpflanzen/Gehölze (Helleborus, Hemerocallis, Hosta, Hydrangea, Jasminum, Ligustrum, Lupinus, Malus, Hibiscus) | `nutrient_demand`, `rotation_pause_years` | keine Zehrerstufe in Fruchtfolge-Quellen |
| Helleborus, Hemerocallis, Helianthus, Hydrangea, Ligustrum, Luffa, Malus, Levisticum | `nitrogen_fixing` | nicht belegt |
| Zimmerpflanzen (Abschnitt 6 „Entfällt") | 6.1-Felder | kein 6.1-Abschnitt; Felder bleiben null |
| Lavandula, Livistona | 6.1-Felder | Datei hat nur 6.2/6.3, kein 6.1; nichts angelegt |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert | Hinweis |
|---|---|---|---|
| Hemerocallis spp. | 1.6 „45–60" | 25–40 (Illinois Extension) | Einzelquelle |
| Helleborus niger | 1.6 „30–40" | 30–36 (Proven Winners, Sorte) | Einzelquelle |
| Luffa aegyptiaca | 1.6 „60–100" in der Reihe | 40–100 / Reihe 150–200 (OMAFRA 2012) | teilweise bestätigt |
| Levisticum officinale | 1.6 „80–100"; 6.1 „3–4 Jahre" | 30–45 „to start with" (RHS); SBB Doldenblütler 4–5 | Wert gilt nur für die Anfangspflanzung |
| Lactuca sativa | 6.1 „2 Jahre" | SBB Korbblütler 3 | Familienwert Asteraceae 3 |
| Lens culinaris | 1.6 „5 cm / 30–40"; 6.1 „4–5 Jahre" | LfL: Drillsaat ca. 12,5 cm (Feldanbau); Pause mind. 6 | Familienwert Fabaceae 6 |
| Hosta spp. | 1.6 „40–80" | RHS „bis zu 90 cm" | stützt keinen Einzelwert |
| Hordeum, Humulus, Hydrangea | 1.6 / 6.1 Zehrerstufe und Anbaupause | keine lesbare Quelle | unbelegt, unverändert |
| Malus domestica | 1.6 „300–500" | unterlagenabhängig 50–1000 (LWG 2021) | kein einheitlicher Artwert |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Guzmania lingulata, Helianthus annuus | Basisarten mit Enrichment nur in `plant_info.yaml` (Importer ungeguardet) — Werte nur im Steckbrief; ein zusätzlicher Enrichment-Eintrag in `plant_info_*_N.yaml` wurde bewusst nicht angelegt (Doppel-Enrichment) |
| Humulus lupulus | Basisart (`species.yaml`) ohne belegten Wert — kein leerer Enrichment-Eintrag angelegt |
| Lactuca sativa, Lavandula, Hordeum, Lens, Luffa | Felder in den bestehenden `species_enrichment`-Eintrag (`plant_info_outdoor_1/2.yaml`) |
| übrige 22 Arten | Felder im `new_species`-Eintrag (`plant_info_indoor_2.yaml`, `plant_info_outdoor_2.yaml`); Arten ohne belegten Wert tragen `null` mit `# MISSING`-Kommentar |
| `spacing_cm` | in Batch 4 für keine Art geschrieben (Bestandswert vorhanden). Seed ↔ 1.9: Helleborus 30-40 ↔ 30–36, Hemerocallis 45-60 ↔ 25–40, Impatiens 20-30 ↔ 20–25, Lactuca 25-30 ↔ 30, Levisticum 60-80 ↔ 30–45, Luffa (species.yaml) 60--100 ↔ 40–100 |
| `rotation_pause_years` | für alle 30 Arten `null` (keine Art-Abweichung vom Familienwert belegt) |
| `nitrogen_fixing` | Lactuca `false`, Lens `true`, Lupinus `true` (im Seed bereits vorhanden) |

### Lehren aus Batch 4

1. Die drei Sub-Batch-Subagenten liefen ohne Bash; die Prüfung `git diff --numstat origin/develop` durch den Aufrufer ergab 0 Löschungen. Ein Agent hängte unaufgefordert einen zusätzlichen Schlusskommentar an (Hippeastrum); vom Aufrufer entfernt — Dateiende stets mit prüfen.
2. Viele Fachquellen (LfL, LWG-Merkblatt 2111, Hochschul-PDFs) sind per WebFetch nicht lesbar; ein Agent las PDFs über den Read-Pfad. Für künftige Batches das PDF-Lesen im Brief vorschlagen.
3. Lichtstufe: Positionsfeld-Spannen führen häufig zu `null`; bei Hydrangea, Impatiens und Malus wurde die Stufe nur gesetzt, weil der Kulturtext der Quelle ausdrücklich einen Vorzug nennt.

## Batch 5 (Arten 121–150, `mammillaria_spp` … `physalis_peruviana`) — 2026-10-17

Konventionen wie bei Batch 1–4. Auswahl: alphabetische Dateiliste von `spec/knowledge/plants/*.md` (ohne `_*`), Position 121–150 (Batch 1–4 = Position 1–120, keine Überschneidung). Gemischt: 12 Zimmerpflanzen, 5 Zierstauden/Beetzierpflanzen (Paeonia, Nymphaea, Petunia, Phlox, Pelargonium), 13 Nutz-/Gründüngungs-/Kräuterarten.

### Bilanz je Feld

| Feld | gesetzt (mit Quelle) | `null` n/a | `null` unbelegt |
|---|---|---|---|
| `row_spacing_cm` | 8 (Matricaria, Melissa, Mentha, Pastinaca, Ocimum, Oryza, Petroselinum, Physalis) | 17 (12 Zimmerpflanzen, 5 Stauden/Beetzierpflanzen ohne Reihenkultur) | 5 (Medicago, Nicotiana, Origanum, Phacelia, Phaseolus) |
| `light_requirement` | 18 (`full_sun` 12, `partial_shade` 6) | 0 | 12 |
| `nutrient_demand` (+ `_source`, `_confidence`) | 7 (light 5, medium 2; Konfidenz high 1, medium 2, low 4) | 17 (12 Zimmerpflanzen, 5 Zierpflanzen; optional) | 6 von 13 Nutzarten (**Pflicht**): Medicago, Nicotiana, Oryza, Petroselinum, Phacelia, Physalis |
| `nitrogen_fixing` | 11 (`true` 2: Medicago, Phaseolus; `false` 9) | 17 (Zimmer-/Zierpflanzen) | 2 (Origanum, Nicotiana) |
| `rotation_pause_years` (Art-Override) | 3 (Phaseolus 3, Melissa 4, Mentha 4) | 17 (Zimmer-/Zierpflanzen) | übrige Nutzarten: „Familienwert gilt" bzw. unbelegt (Nicotiana, Ocimum, Oryza) |

### Bilanz je Art

Tally: `spacing_cm (1.9)` | `row_spacing_cm` | `light_requirement` | `nutrient_demand` | Konfidenz | `nitrogen_fixing` | `rotation_pause_years`. „n/a" = Zimmerpflanze / Abschnitt 6 „Entfällt"; „frei" = freie Pflanzung.

| Art | spacing | row | light | nutrient_demand | Konf. | N-Fix | Pause |
|---|---|---|---|---|---|---|---|
| Matricaria chamomilla | null | 30–35 | full_sun | light_feeder | medium | false | Familie (Asteraceae 3) |
| Medicago sativa | null | null | full_sun | null | — | true | Familie (Fabaceae 6) |
| Melissa officinalis | 25–30 | 42–62,5 | null | light_feeder | low | false | 4 |
| Mentha x piperita | 20–25 | 62,5–75 | null | light_feeder | low | false | 4 |
| Pastinaca sativa | 10–15 | 30–40 | full_sun | medium_feeder | medium | false | Familie (Apiaceae 4) |
| Ocimum basilicum | null | 25 | full_sun | medium_feeder | low | false | null |
| Origanum vulgare | 20–30 | null | full_sun | light_feeder | low | null | null |
| Oryza sativa | null | 15–25 | null | null | — | false | null |
| Nicotiana tabacum | null | null | null | null | — | null | null |
| Petroselinum crispum | 15–30 | 20–30 | null | null | — | false | Familie (Apiaceae 4) |
| Phacelia tanacetifolia | null | null | full_sun | null | — | false | null |
| Phaseolus vulgaris | 15 | null | full_sun | light_feeder | high | true | 3 (Art-Abweichung) |
| Physalis peruviana | 61 | 91 | full_sun | null | — | false | Familie (Solanaceae 4) |
| Paeonia lactiflora | 100 | frei | full_sun | n/a | — | n/a | n/a |
| Nymphaea alba | null | frei | full_sun | n/a | — | n/a | n/a |
| Petunia x hybrida | null | frei | full_sun | n/a | — | null | null |
| Phlox paniculata | null | frei | null | n/a | — | null | null |
| Pelargonium zonale | null | frei | null | n/a | — | n/a | n/a |
| Monstera adansonii, Monstera deliciosa, Nephrolepis exaltata, Peperomia obtusifolia, Phalaenopsis, Philodendron hederaceum | n/a | n/a | partial_shade | n/a | — | n/a | n/a |
| Opuntia microdasys | n/a | n/a | full_sun | n/a | — | n/a | n/a |
| Mammillaria, Maranta, Neoregelia, Oxalis triangularis, Pachira aquatica | n/a | n/a | null | n/a | — | n/a | n/a |

### Lücken (Wert `null`, Grund)

| Art | Feld | Grund |
|---|---|---|
| Mammillaria, Maranta, Melissa, Mentha, Neoregelia, Oxalis, Pachira, Petroselinum, Phlox, Pelargonium | `light_requirement` | RHS nennt Spanne ohne Vorzug bzw. Artseite ohne Position bzw. Artseite in sich widersprüchlich (Oxalis); Mammillaria nur Gattungsebene, uneinheitlich |
| Oryza, Nicotiana | `light_requirement` | keine Lichtstufe gelesen (LfL-Infofolie bzw. keine lesbare Fachquelle) |
| Medicago, Phacelia, Oryza, Nicotiana, Petroselinum, Physalis | `nutrient_demand` | **Pflicht, unbelegt**: Medicago/Phacelia nur Futter-/Gründüngungsleguminose bzw. Gründüngung ohne Zehrerklasse; Petroselinum nur Sammelgruppe „Kräuter" (LKSH, LK NRW, NiG), Petersilie nicht namentlich; Oryza, Nicotiana, Physalis in keiner gelesenen Zehrerliste |
| Matricaria, Medicago, Ocimum, Origanum, Oryza, Nicotiana, Phacelia, Pelargonium, Petunia, Phlox, Nymphaea | `spacing_cm` (1.9) | Drill-/Flächenkultur nach Saatstärke bzw. RHS nennt nur Endbreite/keinen Abstand bzw. LWG „20 × 25" ohne Zuordnung Reihe/Pflanze (Basilikum) |
| Medicago, Origanum, Nicotiana, Phacelia, Phaseolus | `row_spacing_cm` | RHS nennt keinen Reihenabstand (45 cm Bohne nur A-Gestell); LKSH-Luzerne-Versuch 12,5 cm nur Versuchsangabe; Phacelia „wie Getreide" ohne Zahl |
| Origanum, Nicotiana, Petunia, Phlox, Paeonia, Nymphaea, Phacelia | `nitrogen_fixing` / Zehrerstufe / Pause | nicht belegt bzw. Zierstaude ohne Fruchtfolge-Eintrag |
| Zimmerpflanzen (12) | 6.1-Felder | kein 6.1-Abschnitt bzw. nur Alt-Zeilen ohne Quelle; Felder bleiben null |
| Nicotiana (alle Felder) | alle 7 | KTBL-Quelle nicht lesbar (HTML statt PDF), Kentucky-Leitfaden nennt eine Rechentabelle, keine Empfehlung |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert | Hinweis |
|---|---|---|---|
| Matricaria chamomilla | 1.6 „15–20" Direktsaat; Anbaupause „1–2 Jahre" (Kamillenmüdigkeit) | Reihe 30–35 (Sächs. LfL, Drillkultur); „selbstverträglich" | Abschnitt für Kamille ist 7.1, nicht 6.1 |
| Melissa officinalis | 1.6 „30–40"; Pause 3 | 25–30 in der Reihe, Reihe 42–62,5 (LfL Bayern, Feldanbau); Lippenblütler 4–5 | Pause 4 = Untergrenze der Spanne |
| Mentha x piperita | 1.6 „30–40"; Mittelzehrer; Pause 3–4 | 20–25 / 62,5–75 (LfL Bayern); Sammelgruppe Kräuter = Schwachzehrer; 4–5 | Zehrerstufe `low` wegen Sammelgruppe |
| Pastinaca sativa | Reihe 25–30; Pause 3–4 | 30–40 (LWG), 30 (RHS); Doldenblütler 4–5 (SBB) | Familienwert Apiaceae 4 gilt |
| Ocimum basilicum | Schwachzehrer; 1.6 „25–30" | LWG 2151 „mittleres Nährstoffbedürfnis" (medium, low); 20 × 25 | Einzelquelle gegen Gruppenangabe LK NRW |
| Oryza sativa | 1.6 „20–30 × 20–30" (Pikiermethode) | 15–25 Reihe (LfL, Drillsaat/Trockenreis) | Kulturverfahren verschieden |
| Origanum vulgare | 1.6 „30–40" | RHS mind. 20–30 | — |
| Paeonia lactiflora | 6.1 Mittelzehrer (unbelegt); 1.7 Schattentoleranz partial_shade | RHS „do best in full sun" | Standort `full_sun` gesetzt |
| Petroselinum crispum | 6.1 Pause 3–4 | SBB Doldenblütler inkl. Petersilie 4–5 | Familienwert Apiaceae 4 |
| Phaseolus vulgaris | 1.6 Reihe 40–50 / Stange 60–80; Familienwert Fabaceae 6 | RHS Buschbohne mind. 15 cm; SBB Bohne 3–4 (Erbse separat 5–6) | Art-Override 3 gesetzt — Familienwert Fabaceae 6 und Bohne 3 laufen auseinander |
| Physalis peruviana | 1.6 „70–90"; Mittelzehrer, Pause 3–4 unbelegt | Hudson Valley Seed 61 / Reihe 91 | Einzelquelle Saatgutanbieter |
| Petunia, Phlox, Phacelia, Neoregelia | 6.1 Zehrerstufen (Starkzehrer/Mittelzehrer/Schwachzehrer/Schwachzehrer) | ohne Quelle | unbelegt, unverändert |

### Konfidenz `low` — Nachschärfung erwünscht

(`high` gilt nur bei mindestens drei übereinstimmenden unabhängigen Quellen, Schema-Definition; Pastinaca hat zwei — SBB 2022, LWG 2013 — und steht daher auf `medium`.)

| Art | `nutrient_demand` | Befund |
|---|---|---|
| Melissa officinalis | light_feeder | nur Sammelgruppe „Kräuter" (NiG Burgenland, LK NRW 2020), Art nicht namentlich |
| Mentha x piperita | light_feeder | wie Melisse; widerspricht Bestand Mittelzehrer und gestaffelter N-Düngung (LfL) |
| Ocimum basilicum | medium_feeder | LWG 2151 (artspezifisch) gegen LK NRW (Gruppe Kräuter, schwach) |
| Origanum vulgare | light_feeder | nur Gruppenangabe Kräuter |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Monstera deliciosa, Petunia x hybrida | Basisarten mit Enrichment nur in `plant_info.yaml` (Importer ungeguardet) — Werte nur im Steckbrief, kein Doppel-Enrichment angelegt |
| Matricaria, Nicotiana, Oryza, Physalis | Felder im bestehenden `species_enrichment`-Eintrag `plant_info_outdoor_1.yaml` |
| Mentha, Ocimum, Petroselinum, Phaseolus | `species_enrichment` in `plant_info_outdoor_2.yaml` (Seed-Namen „Mentha piperita"; Ocimum/Petroselinum/Phaseolus zusätzlich in `adventskalender.yaml`, dort nicht geschrieben — Modellgrenze wie Batch 1) |
| übrige 20 Arten | `new_species`-Eintrag (`plant_info_indoor_2/3.yaml`, `plant_info_outdoor_2/3.yaml`); Seed-Name Phalaenopsis „Phalaenopsis hybrida" |
| Medicago sativa | `nitrogen_fixing: true` stand im Seed bereits (übernommen, nicht doppelt) |
| Nymphaea alba | Steckbrief hatte schon 1.9 „Saatgut & Keimung" → neue Abschnitte als 1.10 (Abstand) / 1.11 (Licht) nummeriert; Parser, der exakt „1.9 Pflanzabstand" sucht, findet sie dort nicht |
| `spacing_cm` | in Batch 5 für keine Art geschrieben (Bestandswert vorhanden) |

### Betreiberfragen

1. Familienwert Lamiaceae fehlt in `botanical_families.yaml`; Melisse/Mentha tragen den LfL-Wert 4 (Spanne 4–5, „alle Lippenblütler") als Art-Override — als Familienwert Lamiaceae erfassen?
2. Phaseolus: Art-Override 3 (SBB Bohne 3–4) gegen Familienwert Fabaceae 6 — Familienwert unverändert lassen oder je Gattung differenzieren?
3. Mentha (Seed `nutrient_demand_level: medium_feeder` vs. neu `nutrient_demand: light_feeder`) und Ocimum (`light_feeder` vs. `medium_feeder`): zwei Zehrerfelder derselben Art widersprechen sich — welches Feld hat Vorrang (REQ-053 H-004)?

### Lehren aus Batch 5

1. Die Sub-Batch-Agenten liefen mit Bash; `pdftotext` auf per `curl` geladene PDFs (LWG, SBB, LKSH, LfL, NiG) lieferte lesbare Quellen, wo WebFetch scheiterte — künftig im Brief vorschlagen (PDF in leeres Scratchpad-Verzeichnis, `pdftotext -layout`). Spaltenreihenfolge bei NiG-PDFs ohne `-layout` unzuverlässig.
2. Kräuter erscheinen in den Zehrer-Listen nur als Sammelgruppe „Kräuter" (Schwachzehrer): Petersilie bleibt Pflichtlücke, Melisse/Minze/Oregano nur `low`.
3. Wo ein Steckbrief schon einen Abschnitt 1.9 hat (Nymphaea) oder die Fruchtfolgetabelle anders nummeriert ist (Kamille 7.1), musste von der Vorlage abgewichen werden — Extraktor-Parser darauf prüfen.
4. Gründüngungs-/Futterleguminosen (Phacelia, Medicago) haben in Gartenbau-Fruchtfolgequellen keine Zehrerklasse — Pflichtfeld bleibt `null`, kein Default.

## Batch 6 (Arten 151–180, `pilea_peperomioides` … `soleirolia_soleirolii`) — 2026-10-17

Konventionen wie bei Batch 1–5. Auswahl: alphabetische Dateiliste von `spec/knowledge/plants/*.md` (ohne `_*`), Position 151–180 (Batch 1–5 = Position 1–150, keine Überschneidung; `sorghum_bicolor` und `spathiphyllum_wallisii` folgen in Batch 7). Gemischt: 10 Zimmerpflanzen (Pilea … Soleirolia), 2 Ziergehölze (Rosa, Rhododendron spp.), 18 Nutz-/Gründüngungs-/Kräuterarten (8 Obst-/Beerengehölze und Rhabarber, 7 Gemüse/Kräuter, Gelbsenf, Holunder).

### Bilanz je Feld

| Feld | gesetzt (mit Quelle) | `null` n/a | `null` unbelegt |
|---|---|---|---|
| `row_spacing_cm` | 11 (Pisum 30, Satureja 30, Prunus domestica 400, Pyrus 350, Raphanus 15, Rheum 91–122, Ribes rubrum 280, Ribes uva-crispa 280, Rubus fruticosus 280, Rubus idaeus 150–200, Solanum tuberosum 60–75) | 12 (10 Zimmerpflanzen, Rosa, Rhododendron spp.; keine Reihenkultur) | 7 (Prunus avium, Rosmarinus, Salvia, Sambucus, Sinapis, Solanum lycopersicum, Solanum melongena) |
| `light_requirement` | 25 (`full_sun` 17, `partial_shade` 8) | 0 | 5 (Plectranthus, Sambucus, Sedum, Sinapis, Soleirolia) |
| `nutrient_demand` (+ `_source`, `_confidence`) | 9 (light 4, medium 2, heavy 3; Konfidenz high 3, medium 1, low 5) | 12 (10 Zimmerpflanzen, Rosa, Rhododendron spp.; optional) | 9 von 18 Nutzarten (**Pflicht**): Prunus avium, Prunus domestica, Pyrus, Ribes rubrum, Ribes uva-crispa, Rubus fruticosus, Rubus idaeus, Sambucus, Sinapis |
| `nitrogen_fixing` | 1 (`true`: Pisum) | 12 (Zimmer-/Zierpflanzen) | 17 von 18 Nutzarten (keine gelesene Quelle nennt „fixiert keinen Stickstoff“; `false` ist eine Behauptung, kein Platzhalter) |
| `rotation_pause_years` (Art-Override) | 1 (Pisum 5) | 12 (Zimmer-/Zierpflanzen) | übrige Nutzarten: „Familienwert gilt“ (Brassicaceae 4, Solanaceae 4) bzw. kein Familienwert (Lamiaceae, Fabaceae, Rosaceae, Polygonaceae) bzw. Dauerkultur ohne Quelle |

### Bilanz je Art

Tally: `spacing_cm (1.9)` | `row_spacing_cm` | `light_requirement` | `nutrient_demand` | Konfidenz | `nitrogen_fixing` | `rotation_pause_years`. „n/a“ = Zimmer-/Zierpflanze bzw. kein Reihenanbau.

| Art | spacing | row | light | nutrient_demand | Konf. | N-Fix | Pause |
|---|---|---|---|---|---|---|---|
| Pisum sativum | 7,5 | 30 | full_sun | light_feeder | high | true | 5 (Art-Abweichung) |
| Raphanus sativus var. sativus | 2,5–5 | 15 | full_sun | medium_feeder | low | null | Familie (Brassicaceae 4) |
| Rosmarinus officinalis | 45 (min.) | null | full_sun | light_feeder | low | null | null |
| Salvia officinalis | 30 (min.) | null | full_sun | light_feeder | low | null | null |
| Satureja hortensis | 25 | 30 | full_sun | light_feeder | low | null | null |
| Sinapis alba | null | null | null | null | — | null | null |
| Solanum lycopersicum | 45–60 | null | full_sun | heavy_feeder | high | null | Familie (Solanaceae 4) |
| Solanum melongena | 60 | null | full_sun | heavy_feeder | medium | null | Familie (Solanaceae 4) |
| Solanum tuberosum | 30–37 | 60–75 | full_sun | heavy_feeder | high | null | Familie (Solanaceae 4) |
| Rheum rhabarbarum | 75–90 | 91–122 | full_sun | medium_feeder | low | null | null |
| Prunus avium | null | null | full_sun | null | — | null | null |
| Prunus domestica | null | 400 | full_sun | null | — | null | null |
| Pyrus communis | 350–550 | 350 | full_sun | null | — | null | null |
| Ribes rubrum | 120–150 | 280 | full_sun | null | — | null | null |
| Ribes uva-crispa | 120–150 | 280 | full_sun | null | — | null | null |
| Rubus fruticosus | 250–350 | 280 | full_sun | null | — | null | null |
| Rubus idaeus | 40–60 | 150–200 | full_sun | null | — | null | null |
| Sambucus nigra | null | null | null | null | — | null | null |
| Rosa spp. | 60 | n/a | full_sun | n/a | — | n/a | n/a |
| Rhododendron spp. | 50–100 | n/a | partial_shade | n/a | — | n/a | n/a |
| Pilea, Platycerium, Rhipsalis, Rhododendron simsii, Saintpaulia, Schefflera, Schlumbergera | n/a | n/a | partial_shade | n/a | — | n/a | n/a |
| Plectranthus, Sedum morganianum, Soleirolia | n/a | n/a | null | n/a | — | n/a | n/a |

### Lücken (Wert `null`, Grund)

| Art | Feld | Grund |
|---|---|---|
| Plectranthus verticillatus | `light_requirement` | UF/IFAS nennt „prefers bright light“ / „moderate light“ und Schutz vor Direktsonne ohne eindeutige Stufe; keine RHS-Artseite gelesen |
| Sedum morganianum | `light_requirement` | RHS-Artseite in sich widersprüchlich (Position „Full sun“, Kulturtext unter Glas „bright, filtered light“), kein ausdrücklicher Vorzug |
| Soleirolia soleirolii | `light_requirement` | RHS nennt Spanne „Full sun, Partial shade“ ohne ausdrücklichen Vorzug |
| Sambucus nigra | `light_requirement`, `row_spacing_cm`, alle 6.1-Felder | RHS-Spanne „Full sun, Partial shade“ ohne Vorzug; RHS nennt nur Endbreite 2,5–4 m (kein Abstand); Steckbrief ohne Fruchtfolge-Abschnitt und keine Zehrerstufe in den gelesenen Listen |
| Sinapis alba | alle 7 Felder | keine Kammer-/Hochschulquelle gelesen (TLL-Leitlinie auf openagrar lieferte HTML statt PDF); Gelbsenf steht bei Natur im Garten nur als Gründünger ohne Zehrerklasse |
| Prunus avium, Prunus domestica, Pyrus, Ribes rubrum, Ribes uva-crispa, Rubus fruticosus, Rubus idaeus, Sambucus | `nutrient_demand` | **Pflicht, unbelegt**: Obstgehölze und Beerenobst kommen in keiner gelesenen Zehrerliste (SBB, LKSH, LK NRW, Natur im Garten) namentlich vor |
| Rosmarinus, Salvia, Satureja | `nutrient_demand` (nur `low`) | nur Sammelgruppe „Kräuter“ (LKSH, LK NRW, Natur im Garten), Arten nicht namentlich |
| Prunus avium, Rosmarinus, Salvia, Solanum lycopersicum, Solanum melongena, Sinapis | `row_spacing_cm` | RHS nennt keinen Reihenabstand (Einzelpflanzung/Mindestabstand) bzw. Gelbsenf: keine Quelle |
| Prunus avium, Prunus domestica, Sambucus, Sinapis | `spacing_cm` (1.9) | RHS nennt keinen Abstand bzw. nur Endbreite; Sächs. LfL nennt nur Spindelanlagen (Erwerbsanbau) |
| Alle Nutzarten außer Pisum | `nitrogen_fixing` | keine gelesene Quelle belegt `false`; PFAF „some varieties can fix nitrogen“ (Rubus/Prunus) reicht nicht für `false` |
| Alle Nutzarten außer Pisum | `rotation_pause_years` (Art-Override) | keine artspezifische Quelle; Familienwert gilt, wo `botanical_families.yaml` ihn führt |
| Zimmerpflanzen (10), Rosa, Rhododendron spp. | 6.1-Felder | n/a (Zimmer-/Zierpflanze, keine Fruchtfolge) |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert | Hinweis |
|---|---|---|---|
| Pisum sativum | 6.1 Pause 4–5; 1.6 Reihe 30–50 | SBB 5–6, LKSH 6–7; RHS Doppelreihe 30 | Art-Override 5 = untere Grenze SBB; Familienwert Fabaceae in `botanical_families.yaml` nicht gesetzt |
| Raphanus sativus | 6.1 Schwachzehrer; Pause 3–4 | LKSH, Natur im Garten: Mittelzehrer; SBB: Schwachzehrer; Pause SBB 4–5, LKSH 4 | Quellen widersprechen sich → `medium_feeder`, Konfidenz low; Familienwert Brassicaceae 4 gilt |
| Satureja hortensis | 1.6 Reihe 25, in der Reihe 10–20 | Plantura: Reihe 30, Pflanze 25 | Einzelquelle Ratgeberseite (Plantura); Reihe 30 und Licht full_sun nur daraus, im Seed übernommen |
| Solanum lycopersicum / melongena / tuberosum | 1.6 50–80 / 50–60 / 30–35 × 70–80; Pause 3–4 | RHS 45–60 / 60 / 30–37 × 60–75; SBB Nachtschatten 4 Jahre | Familienwert Solanaceae 4 gilt |
| Rubus fruticosus | 1.6 150–200 | RHS 250–350; Sächs. LfL 75–150 (Fächer) | Reihenabstand 280 aus Spindelanlage Erwerbsanbau |
| Rheum rhabarbarum | 1.6 80–100; „Starkzehrer“ ohne Quelle | RHS 75–90; Arkansas „medium“, UConn „little to no fertilizer“ | `medium_feeder`, Konfidenz low; Bestand „Starkzehrer“ unbelegt |
| Rhododendron spp. | 1.6 80–200 | Plantura 50–100 | Ratgeberquelle |
| Prunus domestica, Pyrus communis, Ribes rubrum, Ribes uva-crispa | 6.1 Mittelzehrer / Pausen 3–7 | unbelegt | Bestand unverändert |
| Sinapis alba | 6.1 Schwachzehrer; Pause 3–4 | unbelegt | Bestand unverändert |
| Saintpaulia, Schefflera, Soleirolia | 1.7 Schattentoleranz `shade` | Anspruch `partial_shade` (RHS) bzw. unbelegt (Soleirolia) | Toleranz ≠ Anspruch; Bestand nicht als Beleg genutzt |

### Konfidenz `low` / schwache Quelle — Nachschärfung erwünscht

| Art | Feld | Befund |
|---|---|---|
| Raphanus sativus | `nutrient_demand` medium_feeder (low) | SBB gegen LKSH/Natur im Garten widersprüchlich |
| Rheum rhabarbarum | `nutrient_demand` medium_feeder (low) | Arkansas „medium“ gegen UConn „little to no“; keine deutsche Kammerquelle |
| Rosmarinus, Salvia, Satureja | `nutrient_demand` light_feeder (low) | nur Sammelgruppe „Kräuter“ |
| Solanum melongena | `nutrient_demand` heavy_feeder (medium) | zwei Quellen (SBB, Natur im Garten) |
| Prunus domestica, Pyrus communis, Ribes rubrum, Ribes uva-crispa, Rubus fruticosus | `row_spacing_cm` | Werte (400 / 350 / 280) stammen aus Spindel-/Versuchsanlagen des Erwerbsobstbaus (Sächs. LfL), nicht aus Hausgarten-Empfehlungen — für Beetplanung ggf. verwerfen |
| Satureja hortensis, Rhododendron spp. | Licht / Abstände | Ratgeberseite Plantura (Einzelquelle) |
| Schlumbergera, Rhododendron simsii | `light_requirement` | RHS-Gruppenseiten (Weihnachtskaktus, Zimmerazaleen), keine Artseite |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Pisum sativum, Salvia officinalis, Salvia rosmarinus (Seed-Name für Rosmarinus), Solanum lycopersicum, Solanum tuberosum | `species_enrichment`-Eintrag in `plant_info_outdoor_2.yaml` (Pisum und Solanum lycopersicum zusätzlich in `adventskalender.yaml`, dort nicht geschrieben — Modellgrenze wie Batch 1/5) |
| Solanum melongena, Raphanus sativus | `species_enrichment`-Eintrag in `plant_info_outdoor_1.yaml` (Raphanus zusätzlich in `adventskalender.yaml`, dort nicht geschrieben) |
| Saintpaulia ionantha | Seed-Name `Streptocarpus ionanthus` (`plant_info_supplement_1.yaml`, `new_species`) |
| übrige 22 Arten | `new_species`-Eintrag (`plant_info_indoor_3.yaml`, `plant_info_outdoor_2.yaml`) |
| `spacing_cm` | in Batch 6 für keine Art geschrieben (Bestandswert vorhanden) |
| Solanum tuberosum | Steckbrief führt 1.7/1.8 hinter Abschnitt 2; neue 1.9/1.10 stehen vor dem ersten „## 2.“ → Reihenfolge 1.6, 1.9, 1.10, 2, 1.7, 1.8; Parser darauf prüfen |
| Rheum rhabarbarum | kein „6.1 Fruchtfolge-Einordnung“ → neuer Abschnitt „6.4 Fruchtfolge-Einordnung (Beetplanung)“ |
| Sambucus nigra | 6.1 = Mischkultur, kein Fruchtfolge-Abschnitt; keine 6.x-Ergänzung, da kein Wert gelesen |

### Betreiberfragen

1. Familienwerte Lamiaceae und Fabaceae (und Rosaceae, Polygonaceae) fehlen in `botanical_families.yaml` — Pisum trägt den SBB-Wert 5 als Art-Override; Batch 5 notierte für Fabaceae noch 6. Familienwerte nachziehen?
2. Reihenabstände der Obstgehölze (Prunus domestica 400, Pyrus 350, Ribes 280, Rubus fruticosus 280) stammen aus Erwerbsobst-Spindelanlagen — für die Beetplanung (Hausgarten) übernehmen oder auf `null` setzen?
3. Raphanus: Seed `nutrient_demand_level: light_feeder` vs. neu `nutrient_demand: medium_feeder`; Rheum und Solanum analog zwei Zehrerfelder derselben Art — welches Feld hat Vorrang (REQ-053 H-004)?

### Lehren aus Batch 6

1. Obstgehölze, Beerenobst und Holunder tauchen in keiner Fruchtfolge-/Zehrerliste auf (Listen sind Gemüsebau); die Pflichtlücke `nutrient_demand` betrifft hier eine ganze Artengruppe (8 Arten) und braucht eine Obstbau-Quelle (z. B. Sächs. LfL Obstbau, Bayerische Gartenakademie), nicht weitere Gemüselisten.
2. Reihenabstände aus Erwerbsobst-Unterlagen sind keine Hausgarten-Empfehlung; künftig im Brief verlangen, dass Versuchs-/Spindelanlagen als „schwache Quelle“ markiert werden.
3. Die Sub-Batch-Agenten (3 × 10 Arten) lasen die Zehrerstufen-Quellen aus vorab per `curl` + `pdftotext -layout` abgelegten Textdateien (SBB, LKSH, NiG, LK NRW) — spart je Agent die Wiederholung der PDF-Beschaffung; so beibehalten.
4. RHS-Gruppenseiten (Weihnachtskaktus, Zimmerazaleen) sind keine Artseiten; als Quelle zulässig, aber im Steckbrief als Gruppenquelle vermerken.

## Batch 7 (Arten 181–210, `sorghum_bicolor` … `zea_mays`) — 2026-10-17

Konventionen wie bei Batch 1–6. Auswahl: alphabetische Dateiliste von `spec/knowledge/plants/*.md` (ohne `_*`), Position 181–210 (Batch 1–6 = Position 1–180, keine Überschneidung; **letzter Batch**, damit alle 210 Steckbriefe bearbeitet). Gemischt: 12 Zimmerpflanzen (Spathiphyllum, Stephanotis, Strelitzia, Streptocarpus, Stromanthe, Syngonium, Tillandsia, Tradescantia, Vriesea, Yucca, Zamioculcas, Zantedeschia), 8 Zier-/Beetpflanzen und Ziergehölze (Syringa, Tagetes erecta/patula, Tigridia, Verbena, Viburnum, Viola, Weigela), 10 Nutzarten (Sorghum, Spinat, Thymian, Rotklee, Weizen, Kapuzinerkresse, Heidelbeere, Ackerbohne, Weinrebe, Mais).

### Bilanz je Feld

| Feld | gesetzt (mit Quelle) | `null` n/a | `null` unbelegt |
|---|---|---|---|
| `row_spacing_cm` | 9 (Sorghum 30–50, Spinat 20, Tagetes erecta 30, Tagetes patula 30, Weizen 12,5–25, Tropaeolum 30, Ackerbohne 45, Weinrebe 150–180, Mais 34–45) | 15 (12 Zimmerpflanzen, Syringa, Viburnum, Weigela; keine Reihenkultur) | 6 (Thymus, Trifolium, Vaccinium, Tigridia, Verbena, Viola) |
| `light_requirement` | 26 (`full_sun` 18, `partial_shade` 8) | 0 | 4 (Sorghum, Viburnum, Viola, Weigela) |
| `nutrient_demand` (+ `_source`, `_confidence`) | 8 (light 5, medium 1, heavy 2; Konfidenz medium 2, low 6, high 0) | 20 (12 Zimmerpflanzen, 8 Zierpflanzen; optional) | 2 von 10 Nutzarten (**Pflicht**): Weizen, Kapuzinerkresse |
| `nitrogen_fixing` | 2 (`true`: Rotklee, Ackerbohne) | 20 (Zimmer-/Zierpflanzen) | 8 von 10 Nutzarten (keine gelesene Quelle nennt „fixiert keinen Stickstoff“; `false` ist eine Behauptung) |
| `rotation_pause_years` (Art-Override) | 2 (Rotklee 4, Ackerbohne 4) | 20 (Zimmer-/Zierpflanzen) | übrige Nutzarten: „Familienwert gilt“ (Spinat: Familie Amaranthaceae nicht in `botanical_families.yaml`) bzw. kein Familienwert (Lamiaceae, Fabaceae, Poaceae) bzw. Dauerkultur ohne Quelle bzw. „selbstverträglich“ ohne Zahl (Mais, Sorghum) |

### Bilanz je Art

Tally: `row_spacing_cm` | `light_requirement` | `nutrient_demand` (Konfidenz) | `nitrogen_fixing` | `rotation_pause_years`. „n/a“ = Zimmer-/Zierpflanze bzw. kein Reihenanbau.

| Art | row | light | nutrient_demand | N-Fix | Pause |
|---|---|---|---|---|---|
| Sorghum bicolor | 30–50 | null | heavy_feeder (low) | null | null (selbstverträglich, kein Zahlenwert) |
| Spinacia oleracea | 20 | full_sun | medium_feeder (low) | null | null (Familienwert nicht gesetzt) |
| Thymus vulgaris | null | full_sun | light_feeder (low) | null | null |
| Trifolium pratense | null | full_sun | light_feeder (low) | true | 4 (Art-Abweichung) |
| Triticum aestivum | 12,5–25 | full_sun | null | null | null |
| Tropaeolum majus | 30 | full_sun | null | null | null |
| Vaccinium corymbosum | null | full_sun | light_feeder (medium) | null | null |
| Vicia faba | 45 | full_sun | light_feeder (low) | true | 4 (Art-Abweichung) |
| Vitis vinifera | 150–180 | full_sun | light_feeder (low) | null | null |
| Zea mays | 34–45 | full_sun | heavy_feeder (medium) | null | null (selbstverträglich) |
| Tagetes erecta / patula | 30 | full_sun | n/a | n/a | n/a |
| Syringa, Tigridia, Verbena | null (n/a bzw. unbelegt) | full_sun | n/a | n/a | n/a |
| Viburnum, Viola, Weigela | null | null | n/a | n/a | n/a |
| Stephanotis, Strelitzia, Yucca, Zantedeschia | n/a | full_sun | n/a | n/a | n/a |
| Spathiphyllum, Streptocarpus, Stromanthe, Syngonium, Tillandsia, Tradescantia, Vriesea, Zamioculcas | n/a | partial_shade | n/a | n/a | n/a |

### Lücken (Wert `null`, Grund)

| Art | Feld | Grund |
|---|---|---|
| Sorghum bicolor | `light_requirement` | keine gelesene Quelle nennt einen Lichtanspruch (LTZ nennt nur Wärmebedarf, C4) |
| Viburnum opulus, Weigela florida, Viola x wittrockiana | `light_requirement` | RHS nennt Spanne „Full sun, Partial shade“ ohne ausdrücklichen Vorzug |
| Triticum aestivum, Tropaeolum majus | `nutrient_demand` | **Pflicht, unbelegt**: Weizen in keiner Gemüsebau-Zehrerliste, Kapuzinerkresse in keiner der vier Fruchtfolge-Quellen namentlich (grep „Kapuziner“/„Tropaeol“ ohne Treffer) |
| Thymus, Trifolium, Vaccinium, Tigridia, Verbena, Viola | `row_spacing_cm` | RHS nennt nur Pflanzabstand (Thymus 20–30, Vaccinium 1–2 m bzw. LWG 1,5 m) bzw. keine Quelle |
| Sorghum, Thymus, Trifolium, Triticum, Vaccinium, Vitis, Syringa, Tigridia, Verbena, Viburnum, Weigela | `spacing_cm` (1.9) | keine Quelle für Abstand in der Reihe bzw. nur Endgröße (RHS); Tigridia: RHS nennt nur Pflanztiefe 10 cm |
| Zantedeschia aethiopica | `spacing_cm`, `row_spacing_cm` | RHS-Gattungsguide nennt Horste bis 90 cm Breite ohne Abstandszahl; 30 cm gelten dort nur für kleinere Calla-Hybriden |
| Alle Nutzarten außer Rotklee/Ackerbohne | `nitrogen_fixing` | keine gelesene Quelle belegt `false` |
| Mais, Sorghum | `rotation_pause_years` | FiBL/Uni Göttingen bzw. LTZ/EIP LUPI-HIRSE-Huhn: „selbstverträglich“ ohne Zahl; die 1 Jahr bei Mais ist nur eine Bio-Suisse-Vorgabe |
| Thymus, Spinat, Tropaeolum, Weizen, Heidelbeere, Weinrebe | `rotation_pause_years` | keine Artquelle; Familienwert Lamiaceae/Amaranthaceae/Tropaeolaceae/Poaceae/Ericaceae/Vitaceae nicht in `botanical_families.yaml` bzw. Dauerkultur |
| Zimmerpflanzen (12), Syringa, Tagetes (2), Tigridia, Verbena, Viburnum, Viola, Weigela | 6.1-Felder | n/a (Zimmer-/Zierpflanze, keine Fruchtfolge) |

### Konflikte mit Bestandswerten (Bestand unverändert gelassen)

| Art | Bestand | belegter Wert | Hinweis |
|---|---|---|---|
| Spinacia oleracea | 6.1 Mittelzehrer; Pause 2 Jahre | SBB/NiG Schwachzehrer, LKSH/LK NRW Mittelzehrer (2:2); SBB-Familienwert 3–4 | `medium_feeder`, Konfidenz low (Auslegung); Licht RHS „sun or partial shade“ gleichrangig → `full_sun` gewählt (Auslegung) |
| Trifolium pratense | 6.1 Pause 3–4 | Weimar 2009: Reinsaat 4–7, Rotkleegras 3–4 | Art-Override 4 = Minimum Reinsaat; Bestand gilt nur für Rotkleegras |
| Triticum aestivum | 1.6 Drillsaat 10–15 cm; 6.1 Starkzehrer, Pause 2 Jahre | belegt 12,5–25 cm (Versuchsvarianten LK Steiermark, schwach) | Zehrerstufe und Pause im Bestand unbelegt, nicht übernommen |
| Vicia faba | 6.1 Pause 4–5 | LfL Bayern „mindestens 4 bis 5 Jahre“ | passt, Art-Override 4 = untere Grenze |
| Zea mays, Sorghum | 6.1 Pause 2–3 | selbstverträglich (FiBL, Göttingen, LTZ) | Wert bleibt null |
| Vitis vinifera | 6.1 Mittelzehrer | RHS/UC IPM: kaum Düngung nötig → `light_feeder` (low, indirekt) | Hausgarten-Ratgeber, keine Zehrerklassifikation |
| Tagetes erecta / patula, Viola | 1.6 25–40 / 20–25 / 20–25 cm | Gardeners' World 15 cm in der Reihe (schwach) | Bestand unverändert; Tagetes-erecta-Bestand „Leichtezer“ in 6.1 ist ein ungültiger Enum-Wert ohne Quelle |
| Tigridia pavonia | 1.6 10–15 cm | RHS nennt nur Pflanztiefe | Bestand nicht als Beleg genutzt |
| Syringa vulgaris, Streptocarpus | 1.7 Toleranz partial_shade / shade | Anspruch full_sun (RHS) / partial_shade (RHS-Gattungsguide) | Toleranz ≠ Anspruch |

### Konfidenz `low` / schwache Quelle — Nachschärfung erwünscht

| Art | Feld | Befund |
|---|---|---|
| Sorghum bicolor | `nutrient_demand` heavy_feeder (low) | Ackerbau-Quellen (LTZ „relativ hoher Nährstoffbedarf“, TFZ N-Bedarf 30 % unter Mais, EIP 120 kg N/ha) ohne Zehrerklasse; Einstufung indirekt, TFZ widerspricht teilweise |
| Spinat, Thymus, Rotklee, Ackerbohne, Weinrebe | `nutrient_demand` (low) | widersprüchlich (Spinat) bzw. nur Gruppenangabe („Kräuter“, „Hülsenfrüchte“, „Bohnen“) bzw. Ratgeber (Weinrebe) |
| Mais, Heidelbeere | `nutrient_demand` (medium) | je zwei Quellen (FiBL Feldmais + NiG Zuckermais; UGA direkt + RHS indirekt) |
| Tagetes (2), Viola | `row_spacing_cm`/Abstand | Gardeners' World (Zeitschrift, schwach, Gattungsangabe) |
| Tropaeolum | `row_spacing_cm` 30 | RHS-Kinderseite „Grow it“ (Einzelquelle, schwach) |
| Weizen | `row_spacing_cm` 12,5–25 | Versuchsbericht LK Steiermark 2024 (Varianten, keine Gartenempfehlung); Licht PFAF (schwach) |
| Weinrebe | `row_spacing_cm` 150–180 | RHS Hausgarten-Minirebanlage, keine Erwerbsanlage gelesen |
| Rotklee | Licht | PFAF (schwach) |
| Tillandsia, Tradescantia, Zamioculcas, Zantedeschia, Stephanotis | `light_requirement` | RHS-Position (Spanne) und Kulturtext unterscheiden sich; Wert folgt dem Kulturtext (Konvention Batch 6: Position = Toleranz, Kulturtext = Anspruch); Tillandsia am wackeligsten (Position „Full sun“, Text „bright, indirect light“) |
| Streptocarpus, Zantedeschia | `light_requirement` | RHS-Gattungs-/Cultivar-Seiten, keine Artseite |

### Seed-Übernahme (Steckbrief → YAML) — Ausnahmen

| Art | Befund |
|---|---|
| Spathiphyllum wallisii, Viola x wittrockiana | nur `plant_info.yaml` `species_enrichment` (Importer ungeguardet) — Werte nur im Steckbrief, kein Doppel-Enrichment angelegt |
| Tagetes erecta | `species_enrichment` in `plant_info_outdoor_1.yaml`; zusätzlich Eintrag in `adventskalender.yaml`, dort nicht geschrieben (Modellgrenze wie Batch 1) |
| Sorghum, Triticum, Verbena, Vicia, Zea | `species_enrichment` in `plant_info_outdoor_1.yaml` |
| Thymus, Trifolium | `species_enrichment` in `plant_info_outdoor_2.yaml`; Trifolium trug `nitrogen_fixing: true` bereits (Skript übersprang den Eintrag, sechs Felder manuell nachgetragen, Wert identisch) |
| Tigridia pavonia | `new_species` in `plant_info.yaml` |
| Syngonium podophyllum | `new_species` in `plant_info_supplement_1.yaml` |
| übrige 18 Arten | `new_species` in `plant_info_indoor_3.yaml` (10) und `plant_info_outdoor_2.yaml` (8) |
| `spacing_cm` | in Batch 7 für keine Art geschrieben; Validator-Warnung „row_spacing ⇒ spacing_cm“ bleibt für Arten mit Reihenabstand ohne Bestands-`spacing_cm` stehen (Weizen, Sorghum) |
| Steckbrief-Struktur | 1.9/1.10 überall frei und vor `## 2.` eingefügt (kein Fall von 1.7/1.8 hinter Abschnitt 2); Thymus und Vaccinium: neuer Abschnitt „6.4 Fruchtfolge-Einordnung (Beetplanung)“; Vicia faba: Zeilen unter 6.1 (6.4 = Familien-Kompatibilität bereits belegt); Syringa: 6.1 = Mischkultur, keine Ergänzung; Zantedeschia: keine abschließende `<!-- /Quelle -->`-Zeile, Quellenzeilen am Dateiende angehängt |

### Betreiberfragen

1. Sorghum `heavy_feeder` (low) stützt sich auf kg-N/ha-Angaben ohne Zehrerklassen-Begriff — behalten oder auf `null` setzen (E-10 streng gelesen)?
2. Familienwerte Lamiaceae, Fabaceae, Rosaceae, Poaceae, Cannabaceae fehlen in `botanical_families.yaml`; Polygonaceae, Amaranthaceae, Ericaceae, Vitaceae, Tropaeolaceae sind dort gar nicht angelegt (siehe Gesamtbilanz).
3. Spinat: medium_feeder (Auslegung bei 2:2-Quellenlage) und full_sun (Quelle „sun or partial shade“) — bestätigen?

### Lehren aus Batch 7

1. RHS-Suche per `curl` liefert nichts (JS-Rendering); Artseiten-ID per WebSearch finden, danach `curl` auf `/plants/<id>/<slug>/details` (Position-Feld liegt im HTML). RHS-Anleitungen (marigolds, pansies, weigela, lilac) liefern teils 404.
2. RHS-„Position“ ist eine Toleranzspanne; als Anspruch zählt der Kulturtext („bright indirect/filtered light“ → `partial_shade`). Bei Spanne ohne Vorzug bleibt `null`.
3. WebSearch-Snippets zählen nicht als gelesen; jede zitierte Aussage wurde per `curl`/`pdftotext` oder WebFetch geprüft.
4. Gemüsebau-Zehrerlisten decken Zierpflanzen, Obst, Getreide und Klee nicht ab; für Nutzarten außerhalb des Gemüsebaus braucht die Nachbelegung Ackerbau-/Obstbau-Quellen (LfL, LK, LWG), die selten eine Zehrerklasse nennen.
5. Das Einfüge-Skript muss vorhandene Einzelschlüssel pro Feld behandeln, nicht den ganzen Eintrag überspringen (Trifolium).

## Gesamtbilanz Batches 1–7 (alle 210 Steckbriefe) — 2026-10-17

Zählung aus den Steckbriefen (Abschnitt 1.9/1.10/6.x, Parse der Tabellenzeilen; 210 Dateien). Einzelwerte je Batch stehen in den Batch-Abschnitten.

| Feld | gesetzt | Aufschlüsselung | n/a bzw. leer |
|---|---|---|---|
| `row_spacing_cm` | 88 | — (Stand 2026-10-18 nach Betreiberentscheidung #2371: −5 Obstgehölze) | 94 n/a (Zimmerpflanzen, Stauden, Gehölze ohne Reihenkultur), 28 unbelegt (23 + Prunus domestica, Pyrus communis, Ribes rubrum, Ribes uva-crispa, Rubus fruticosus) |
| `light_requirement` | 156 | `full_sun` 99, `partial_shade` 57 (`shade` 0) | 54 `null` (Spanne ohne Vorzug bzw. keine Quelle) |
| `nutrient_demand` | 50 | `light_feeder` 18, `medium_feeder` 15, `heavy_feeder` 17; Konfidenz high 10, medium 13, low 27 | 61 mit `DATEN FEHLEN`, davon 30 Nutzarten (Pflichtlücke, unten), 31 Zier-/Zimmerpflanzen (n/a); 90 Steckbriefe ohne Zehrer-Zeile (Zimmerpflanzen, bewusst n/a) |
| `nitrogen_fixing` | 47 | `true` 8, `false` 39 | übrige null/n/a |
| `rotation_pause_years` (Art-Override) | 10 mit Zahlenwert | Avena 4, Cannabis 3, Daucus 5, Fragaria 4, Melissa 4, Mentha 4, Phaseolus 3, Pisum 5, Trifolium 4, Vicia 4 | übrige: Familienwert gilt oder unbelegt |

### Offene Pflichtlücke `nutrient_demand` bei Nutzpflanzen — Nachbelegungsliste (30 Arten)

Quellenhinweis aus allen Batches: Gemüsebau-Listen (SBB, LKSH, NiG, LK NRW) reichen für diese Arten nicht; benötigt werden Obstbau-Quellen (Sächs. LfL, LWG, Bayerische Gartenakademie), Ackerbau-/Futterbau-Quellen (LfL, Landwirtschaftskammern, KTBL) und Kräuter-/Sonderkultur-Merkblätter.

| Gruppe | Arten |
|---|---|
| Obst-/Beerengehölze, Wildobst | Malus domestica, Prunus avium, Prunus domestica, Pyrus communis, Ribes rubrum, Ribes uva-crispa, Rubus fruticosus, Rubus idaeus, Cornus mas; zusätzlich Sambucus nigra (kein Fruchtfolge-Abschnitt, keine Zehrer-Zeile) |
| Getreide/Körnerfrüchte/Ackerbau | Avena sativa, Hordeum vulgare, Triticum aestivum, Oryza sativa, Glycine max, Lens culinaris, Medicago sativa, Helianthus annuus, Cannabis sativa, Humulus lupulus, Nicotiana tabacum |
| Gemüse/Kräuter/Sonstige | Anethum graveolens, Levisticum officinale, Petroselinum crispum, Citrullus lanatus, Cucumis melo, Luffa aegyptiaca, Physalis peruviana, Tropaeolum majus |
| Gründüngung | Phacelia tanacetifolia, Sinapis alba |

Hinweis: Die Zuordnung Nutzart/Zierpflanze für die Zählung 30/31 erfolgte heuristisch aus dem `DATEN FEHLEN`-Text; Steckbriefe ohne Zehrer-Zeile (90) sind nicht einzeln geprüft.

### Fehlende Familienwerte in `botanical_families.yaml` (Stand 2026-10-18, nach #2371)

Entscheidung siehe Abschnitt „Betreiberentscheidung #2371“ unten. `rotation_pause_years` ist nun gesetzt für Solanaceae, Apiaceae, Brassicaceae, Cucurbitaceae (je 4), Lamiaceae (4), Asteraceae (3), Fabaceae (3). Weiterhin `null` (E-10, keine belastbare Familienquelle):

| Familie | Status | Arten mit belegter Art-Abweichung / Hinweis |
|---|---|---|
| Rosaceae | angelegt, `null` | Fragaria 4 (Art-Override); WebSearch 2026-10-18 fand nur Ratgeberseiten (Erdbeere 3–4), keine Beratungsstelle mit Familienwert; Obstgehölze und Rosa ohne Quelle |
| Poaceae | angelegt, `null` | Avena 4; WebSearch 2026-10-18: nur Anbauanteil-/Selbstfolgeregeln (GAP, Südtiroler Bio-Regel), keine Anbaupause je Jahr; Mais und Sorghum „selbstverträglich“ ohne Zahl |
| Cannabaceae | angelegt, `null` | Cannabis 3 (Art-Override); keine Hopfen-Quelle |
| Polygonaceae | nicht angelegt | Rheum rhabarbarum; kein erfundener Wert |
| Amaranthaceae | nicht angelegt | Spinacia (SBB nennt 3–4 für Gänsefußgewächse, Familie nicht angelegt), Beta |
| Ericaceae, Vitaceae, Tropaeolaceae | nicht angelegt | Dauerkulturen bzw. Zierpflanze ohne Quelle |

## Betreiberentscheidung #2371 (2026-10-18) — umgesetzt

Quelle: Kommentar des Betreibers in #2371 („source quality decides, conservative defaults“). Folgearbeit zu den Betreiberfragen der Batches 5–7.

| Nr. | Entscheidung | Umsetzung |
|---|---|---|
| 1 | Familien-`rotation_pause_years` nur mit Quelle; Fabaceae 3; nicht angelegte Familien ohne erfundenen Wert | Fabaceae 3 (Untergrenze der Art-Spanne 3–5; Pisum 5, Vicia 4, Trifolium 4, Phaseolus 3 bleiben Art-Overrides). Lamiaceae 4 (LfL Bayern, Kulturanleitungen Zitronenmelisse und Pfefferminze: „vier- bis fünfjährige Anbaupause für alle Lippenblütler“, Untergrenze). Rosaceae, Poaceae, Cannabaceae `null` (WebSearch ohne belastbare Familienquelle, siehe Tabelle oben). Polygonaceae, Amaranthaceae, Ericaceae, Vitaceae, Tropaeolaceae nicht angelegt, kein Wert |
| 2 | Bei Widerspruch gewinnt das quellenbelegte `nutrient_demand` über `nutrient_demand_level` | Konflikte unten; `nutrient_demand_level` bleibt als Altfeld (Kommentar im Seed, Zeile „Vorrang Zehrerfelder“ im Steckbrief), nichts gelöscht |
| 3 | Obst-Reihenabstände aus Erwerbsanlagen nicht übernehmen | `row_spacing_cm` = `null` für Prunus domestica (400), Pyrus communis (350), Ribes rubrum (280), Ribes uva-crispa (280), Rubus fruticosus (280); keine Hausgarten-Quelle gelesen. Steckbrief §1.9 auf `DATEN FEHLEN` gesetzt |
| 4 | Schwach belegte Werte bleiben mit `confidence: low`; Spinat `medium_feeder` / `full_sun` | Keine Datenänderung: Satureja (`light_feeder`, low), Sorghum (`heavy_feeder`, low), Spinat (`medium_feeder`, low; `full_sun`) |

### Konflikte `nutrient_demand` gegen `nutrient_demand_level` (Vorrang: `nutrient_demand`)

| Art | `nutrient_demand_level` (Altfeld, bleibt) | `nutrient_demand` (gilt, Konfidenz) |
|---|---|---|
| Mentha × piperita | medium_feeder | light_feeder (low; Sammelgruppe Kräuter, Gegenindiz LfL Entzug 42 kg N) |
| Ocimum basilicum | light_feeder | medium_feeder (low; LWG Merkblatt 2151, abweichend LK NRW Kräuter = Schwachzehrer) |
| Raphanus sativus | light_feeder | medium_feeder (low; 2 Quellen Mittelzehrer, 1 Schwachzehrer) |
| Rheum rhabarbarum | heavy_feeder | medium_feeder (low; Arkansas „medium“, UConn „little to no“) |
| Allium sativum | light_feeder | medium_feeder (siehe Batch 1–3) |
| Asparagus officinalis | heavy_feeder | medium_feeder (siehe Batch 1–3) |
| Trifolium pratense | nitrogen_fixer | light_feeder (`nitrogen_fixing` trägt die Fixierung) |
| Vitis vinifera | medium_feeder | light_feeder (siehe Batch 6/7) |

Ein Abgleich beider Felder im Seed (`plant_info_outdoor_*.yaml`) ergab 7 abweichende Arten; die Regel gilt für alle (die Betreiberentscheidung nannte Mentha, Ocimum, Raphanus ausdrücklich; Rheum aus Batch-6-Frage 3 und die übrigen folgen derselben Regel). Solanum: kein Widerspruch. Hinweis: `nutrient_demand_level` skaliert weiterhin das EC-Ziel (`phase_resource_resolver`); eine Angleichung an `nutrient_demand` ist Folgearbeit außerhalb dieser Datenänderung.
