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
