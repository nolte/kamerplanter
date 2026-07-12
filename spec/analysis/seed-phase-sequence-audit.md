# Audit: Seed-Species <-> Phase-Sequence-Zuordnung (REQ-003)

**Erstellt von:** Seed-Phase-Sequence-Audit (Claude Code, Opus 4.8) — Issue #576
**Datum:** 2026-07-12
**Frage:** Welche der geseedeten Arten haben heute eine *biologisch passende* Phase-Sequence,
und welche fallen nur mangels besserem Muster auf den Blanket-Default `indoor_default`?
**Methode:** Statische Rekonstruktion der Zuordnung aus den Seed-Quellen + Attribut-getriebener
Soll-Ist-Abgleich gegen die REQ-003-Archetypen (kein DB-Lauf, keine Code-Änderung).

> **Scope-Hinweis:** Reiner Analyse-Report. Das eigentliche Seeding der hier vorformulierten
> Sequenzen ist bewusst ein **Folge-Issue** (Removal-/Datenänderungs-Verbot in additiven Analyse-PRs).

---

## 1. Kernbefund

| Kennzahl | Wert |
|---|---|
| Geseedete Arten (Inventar, dedupliziert) | **207** |
| davon Outdoor mit **explizitem** `phase_sequence` | **38** |
| davon Indoor auf Blanket-`indoor_default` | **169** |
| Verdikt `ok` (attributgerecht zugeordnet) | **38** |
| Verdikt `mismatch` (klarer Attributkonflikt -> Gap) | **124** |
| Verdikt `default-fallback` (tolerierbarer Annual-/Tender-Crop-Fit) | **45** |
| Definierte `phase_definitions` heute | **10** |
| Definierte `phase_sequences` heute | **11** (10 Outdoor + 1 Indoor-Default) |
| Vorformulierte neue Sequenzen (dieser Report) | **8** |
| Vorformulierte neue `phase_definitions` | **18** |
| Draft-YAML validiert gegen `phase_sequences.schema.yaml` | **PASS** |

**Aussage:** Nur **38 von 207** Arten (18 %) sind heute biologisch gezielt zugeordnet — alle 38
stammen aus der handkuratierten `lifecycles_outdoor.yaml`. Die restlichen **169** Indoor-Arten
teilen sich **eine einzige** Sequence (`indoor_default`), obwohl mindestens **124** davon einen
Lebenszyklus haben, den `indoor_default` strukturell falsch abbildet (perennierende Blattschmuck-,
Sukkulenten-/CAM-, monokarpe, photoperiodische, Palmen-, Farn- und Geophyten-Zyklen auf einem
*annuellen, nicht-wiederholenden* Sämling->Ernte-Schema mit cannabis-typischer `flushing`-Phase).

> **Faktenkorrektur zum Issue:** Das Issue nennt „12 `phase_definitions`". Die Datei
> `phase_sequences.yaml` enthält tatsächlich **10** `phase_definitions`
> (`germination, seedling, vegetative, flowering, fruiting, ripening, dormancy, sprouting,
> senescence, flushing`) und **11** `phase_sequences`. Die 11-Sequenzen-Angabe stimmt.

---

## 2. Zuordnungs-Mechanik (rein statisch, kein Resolver)

Die Sequence-Zuordnung erfolgt an **zwei** Stellen im Seed-Code, ohne jeden attributgetriebenen
Resolver:

1. **Outdoor — explizit.** `seed_lifecycles_outdoor.py::run_seed_lifecycles_outdoor()` liest das
   Feld `phase_sequence:` je Eintrag aus `lifecycles_outdoor.yaml` (38 Arten) und legt die
   `HAS_PHASE_SEQUENCE`-Kante über `_ensure_has_phase_sequence_edge(species_key, ps_key)` an
   (`seed_lifecycles_outdoor.py:246-290`).
2. **Indoor — Blanket-Default.** `seed_data.py::_link_indoor_species_to_default_sequence()`
   (`seed_data.py:108-151`) iteriert über **alle** Arten in `species_key_map` und hängt jede Art
   **ohne** bereits existierende `HAS_PHASE_SEQUENCE`-Kante an die eine `indoor_default`-Sequence.
   Damit fällt jede Art, die keinen Outdoor-Lifecycle-Eintrag hat, unterschiedslos auf
   `indoor_default` — unabhängig von `cycle_type`, `flowering_strategy`, `photosynthesis_type`,
   `photoperiod_type` oder `growth_habit`.

Kein `plant_info*.yaml`/`adventskalender.yaml`-Eintrag setzt ein eigenes `phase_sequence`-Feld
(verifiziert per Grep) — die `lifecycle_configs`-Blöcke dort tragen nur Achsen wie `cycle_type`,
`photoperiod_type`, `dormancy_required`, aber **keine** Sequence-Bindung. Die reichhaltigen
Steuer-Attribute (REQ-001 `cultivation_cycle_type`, `flowering_strategy`, `growth_determinacy`;
`species.yaml::lifecycle_overrides`) sind also **vorhanden, aber für die Sequence-Wahl ungenutzt**.

**Datengrundlage des Inventars:**
`species.yaml` (66 Basis-Arten + `lifecycle_overrides` + `perennial_species`),
`plant_info*.yaml` (9 Dateien, `new_species`), `adventskalender.yaml` (`new_species`),
`lifecycles_outdoor.yaml` (38 Outdoor-Lifecycles), abgeglichen mit den 210 Steckbriefen
`spec/knowledge/plants/*.md`. Die Differenz 210 Steckbriefe -> 207 geseedete Arten resultiert aus
`spp.`-Aggregaten und einzelnen Steckbriefen ohne eigenen Seed-Eintrag.

---

## 3. Inventar A — Outdoor-Arten (38, explizit zugeordnet)

Alle 38 Outdoor-Arten sind handkuratiert und tragen eine attribut-passende Sequence
(`dormancy`/`vernalization`/Frucht-/Ernte-Charakteristik deckt sich mit der gewählten Sequence).
Verdikt durchgehend **`ok`**.

| # | Species | Aufgeloeste Sequence | cycle_type | dormancy | vernalization | Verdikt |
|---|---|---|---|---|---|---|
| 1 | _Lupinus polyphyllus_ | `annual_flower` | annual | False | False | ok |
| 2 | _Phacelia tanacetifolia_ | `annual_flower` | annual | False | False | ok |
| 3 | _Sinapis alba_ | `annual_flower` | annual | False | False | ok |
| 4 | _Tagetes patula_ | `annual_flower` | annual | False | False | ok |
| 5 | _Tropaeolum majus_ | `annual_flower` | annual | False | False | ok |
| 6 | _Satureja hortensis_ | `annual_harvest` | annual | False | False | ok |
| 7 | _Spinacia oleracea_ | `annual_harvest` | annual | False | False | ok |
| 8 | _Pastinaca sativa_ | `biennial_vernalization` | biennial | True | True | ok |
| 9 | _Rheum rhabarbarum_ | `perennial_early_harvest` | perennial | True | False | ok |
| 10 | _Malus domestica_ | `perennial_fruit_early` | perennial | True | False | ok |
| 11 | _Prunus avium_ | `perennial_fruit_early` | perennial | True | False | ok |
| 12 | _Prunus domestica_ | `perennial_fruit_early` | perennial | True | False | ok |
| 13 | _Pyrus communis_ | `perennial_fruit_early` | perennial | True | False | ok |
| 14 | _Sambucus nigra_ | `perennial_fruit_early` | perennial | True | False | ok |
| 15 | _Ribes rubrum_ | `perennial_fruit_sprouting` | perennial | True | False | ok |
| 16 | _Ribes uva-crispa_ | `perennial_fruit_sprouting` | perennial | True | False | ok |
| 17 | _Rubus fruticosus agg._ | `perennial_fruit_sprouting` | perennial | True | False | ok |
| 18 | _Rubus idaeus_ | `perennial_fruit_sprouting` | perennial | True | False | ok |
| 19 | _Vaccinium corymbosum_ | `perennial_fruit_sprouting` | perennial | True | False | ok |
| 20 | _Vitis vinifera_ | `perennial_full_fruit` | perennial | True | False | ok |
| 21 | _Levisticum officinale_ | `perennial_harvest_veg` | perennial | True | False | ok |
| 22 | _Medicago sativa_ | `perennial_harvest_veg` | perennial | True | False | ok |
| 23 | _Melissa officinalis_ | `perennial_harvest_veg` | perennial | True | False | ok |
| 24 | _Origanum vulgare_ | `perennial_harvest_veg` | perennial | True | False | ok |
| 25 | _Forsythia x intermedia_ | `perennial_standard` | perennial | True | False | ok |
| 26 | _Geranium sanguineum_ | `perennial_standard` | perennial | True | False | ok |
| 27 | _Hemerocallis spp._ | `perennial_standard` | perennial | True | False | ok |
| 28 | _Hosta spp._ | `perennial_standard` | perennial | True | False | ok |
| 29 | _Hydrangea macrophylla_ | `perennial_standard` | perennial | True | False | ok |
| 30 | _Ligustrum vulgare_ | `perennial_standard` | perennial | True | False | ok |
| 31 | _Paeonia lactiflora_ | `perennial_standard` | perennial | True | False | ok |
| 32 | _Phlox paniculata_ | `perennial_standard` | perennial | True | False | ok |
| 33 | _Rosa spp._ | `perennial_standard` | perennial | True | False | ok |
| 34 | _Syringa vulgaris_ | `perennial_standard` | perennial | True | False | ok |
| 35 | _Viburnum opulus_ | `perennial_standard` | perennial | True | False | ok |
| 36 | _Weigela florida_ | `perennial_standard` | perennial | True | False | ok |
| 37 | _Helleborus niger_ | `perennial_winter_flower` | perennial | True | False | ok |
| 38 | _Rhododendron spp._ | `perennial_winter_flower` | perennial | True | False | ok |

**Verteilung der Outdoor-Sequenzen:** `perennial_standard` 12, `perennial_fruit_early` 5,
`perennial_fruit_sprouting` 5, `annual_flower` 5, `perennial_harvest_veg` 4, `perennial_winter_flower` 2,
`annual_harvest` 2, `biennial_vernalization` 1, `perennial_early_harvest` 1, `perennial_full_fruit` 1.

---

## 4. Inventar B — Indoor-Arten (169, Blanket `indoor_default`)

Spalte **Verdikt**: `mismatch` = mindestens ein treibendes Attribut widerspricht der `indoor_default`-
Semantik (annuell, `is_repeating: false`, terminiert bei `ripening`, cannabis-`flushing`);
`default-fallback` = annuelle/tender-als-annuell-kultivierte Nutz-/Zierpflanze, für die `indoor_default`
ein tolerierbarer, aber **nicht attributgeleiteter** Fit ist. Spalte **Vorgeschlagene Sequence** =
Zielsequenz aus Abschnitt 6 (`*` = bereits existierende Sequence, nur Zuordnung fehlt).

| # | Species | Familie | growth_habit | cycle_type | flowering_strategy | photoperiod | CAM | Verdikt | Vorgeschlagene Sequence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | _Adiantum raddianum_ | - | fern | perennial | - | day_neutral | - | mismatch | fern_spore |
| 2 | _Aechmea fasciata_ | - | epiphyte | perennial | monocarpic | day_neutral | CAM | mismatch | clonal_monocarp |
| 3 | _Aeschynanthus radicans_ | - | epiphyte | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 4 | _Aglaonema commutatum_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 5 | _Allium cepa_ | - | bulb_geophyte | biennial | monocarpic | long_day | - | mismatch | geophyte_fine |
| 6 | _Allium porrum_ | - | herb | biennial | - | long_day | - | default-fallback | - |
| 7 | _Allium sativum_ | - | bulb_geophyte | perennial | polycarpic | long_day | - | mismatch | geophyte_fine |
| 8 | _Allium schoenoprasum_ | Amaryllidaceae | herb | perennial | - | long_day | - | mismatch | evergreen_foliage_perennial |
| 9 | _Alocasia x amazonica_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 10 | _Aloe vera_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 11 | _Anemone hupehensis_ | - | herb | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 12 | _Anethum graveolens_ | Apiaceae | herb | annual | - | long_day | - | default-fallback | - |
| 13 | _Anthurium andraeanum_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 14 | _Aphelandra squarrosa_ | - | shrub | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 15 | _Apium graveolens_ | Apiaceae | herb | biennial | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 16 | _Apium graveolens var. rapaceum_ | - | herb | biennial | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 17 | _Ardisia crenata_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 18 | _Artemisia dracunculus_ | Asteraceae | herb | - | - | - | - | default-fallback | - |
| 19 | _Asparagus officinalis_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 20 | _Asparagus setaceus_ | - | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 21 | _Aspidistra elatior_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 22 | _Asplenium nidus_ | - | fern | perennial | - | day_neutral | - | mismatch | fern_spore |
| 23 | _Astilbe chinensis_ | - | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 24 | _Avena sativa_ | Poaceae | grass | - | - | - | - | default-fallback | - |
| 25 | _Beaucarnea recurvata_ | - | succulent | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 26 | _Begonia rex-cultorum_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 27 | _Begonia semperflorens_ | - | herb | annual | - | day_neutral | - | default-fallback | - |
| 28 | _Beta vulgaris subsp. vulgaris_ | - | herb | biennial | - | long_day | - | default-fallback | - |
| 29 | _Brassica oleracea var. botrytis_ | Brassicaceae | herb | - | - | - | - | default-fallback | - |
| 30 | _Brassica oleracea var. capitata_ | Brassicaceae | herb | - | monocarpic | - | - | mismatch | biennial_vernalization* |
| 31 | _Brassica oleracea var. gemmifera_ | - | herb | biennial | - | long_day | - | default-fallback | - |
| 32 | _Brassica oleracea var. gongylodes_ | Brassicaceae | herb | - | - | - | - | default-fallback | - |
| 33 | _Brassica oleracea var. italica_ | Brassicaceae | herb | - | - | - | - | default-fallback | - |
| 34 | _Brassica oleracea var. sabellica_ | - | herb | biennial | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 35 | _Buxus sempervirens_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 36 | _Calendula officinalis_ | - | herb | annual | - | day_neutral | - | default-fallback | - |
| 37 | _Cannabis sativa_ | Cannabaceae | herb | annual | - | short_day | - | mismatch | photoperiodic_ornamental |
| 38 | _Capsicum annuum_ | Solanaceae | herb | annual | polycarpic | day_neutral | - | default-fallback | - |
| 39 | _Cattleya hybrida_ | - | epiphyte | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 40 | _Ceropegia woodii_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 41 | _Chamaedorea elegans_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | palm_evergreen |
| 42 | _Chlorophytum comosum_ | Asparagaceae | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 43 | _Cichorium intybus_ | Asteraceae | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 44 | _Citrullus lanatus_ | Cucurbitaceae | vine | - | - | - | - | default-fallback | - |
| 45 | _Clematis spp._ | - | vine | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 46 | _Clivia miniata_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 47 | _Codiaeum variegatum_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 48 | _Coffea arabica_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 49 | _Coriandrum sativum_ | Apiaceae | herb | annual | - | long_day | - | default-fallback | - |
| 50 | _Cornus mas_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 51 | _Crassula ovata_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 52 | _Ctenanthe burle-marxii_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 53 | _Cucumis melo_ | Cucurbitaceae | vine | - | - | - | - | default-fallback | - |
| 54 | _Cucumis sativus_ | Cucurbitaceae | vine | annual | - | day_neutral | - | default-fallback | - |
| 55 | _Cucurbita maxima_ | Cucurbitaceae | vine | annual | - | day_neutral | - | default-fallback | - |
| 56 | _Cucurbita pepo_ | Cucurbitaceae | vine | annual | - | day_neutral | - | default-fallback | - |
| 57 | _Curio rowleyanus_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 58 | _Cyclamen persicum_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 59 | _Dahlia pinnata_ | - | bulb_geophyte | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 60 | _Dahlia x cultorum_ | - | bulb_geophyte | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 61 | _Daucus carota_ | Apiaceae | herb | biennial | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 62 | _Delphinium elatum_ | - | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 63 | _Dendrobium nobile_ | - | epiphyte | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 64 | _Dieffenbachia seguine_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 65 | _Dracaena angolensis_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 66 | _Dracaena fragrans_ | Asparagaceae | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 67 | _Dracaena marginata_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 68 | _Dracaena trifasciata_ | Asparagaceae | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 69 | _Dypsis lutescens_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | palm_evergreen |
| 70 | _Echeveria elegans_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 71 | _Echinacea purpurea_ | - | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 72 | _Epipremnum aureum_ | Araceae | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 73 | _Eruca vesicaria_ | Brassicaceae | herb | - | - | - | - | default-fallback | - |
| 74 | _Euphorbia pulcherrima_ | - | shrub | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 75 | _Fatsia japonica_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 76 | _Ficus benjamina_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 77 | _Ficus elastica_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 78 | _Ficus lyrata_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 79 | _Fittonia albivenis_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 80 | _Foeniculum vulgare_ | Apiaceae | herb | annual | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 81 | _Fragaria x ananassa_ | Rosaceae | groundcover | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 82 | _Gardenia jasminoides_ | - | shrub | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 83 | _Glycine max_ | Fabaceae | herb | - | - | - | - | default-fallback | - |
| 84 | _Goeppertia lancifolia_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 85 | _Goeppertia makoyana_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 86 | _Goeppertia orbifolia_ | Marantaceae | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 87 | _Guzmania lingulata_ | Bromeliaceae | epiphyte | perennial | monocarpic | day_neutral | - | mismatch | clonal_monocarp |
| 88 | _Gymnocalycium mihanovichii_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 89 | _Haworthiopsis fasciata_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 90 | _Hedera helix_ | - | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 91 | _Helianthus annuus_ | Asteraceae | herb | annual | - | day_neutral | - | default-fallback | - |
| 92 | _Hibiscus rosa-sinensis_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 93 | _Hippeastrum hybridum_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 94 | _Hordeum vulgare_ | Poaceae | grass | - | - | - | - | default-fallback | - |
| 95 | _Howea forsteriana_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | palm_evergreen |
| 96 | _Hoya carnosa_ | - | vine | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 97 | _Humulus lupulus_ | Cannabaceae | vine | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 98 | _Impatiens walleriana_ | - | herb | annual | - | day_neutral | - | default-fallback | - |
| 99 | _Jasminum polyanthum_ | - | vine | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 100 | _Kalanchoe blossfeldiana_ | - | succulent | perennial | polycarpic | short_day | CAM | mismatch | photoperiodic_ornamental |
| 101 | _Kalanchoe daigremontiana_ | - | succulent | perennial | monocarpic | short_day | CAM | mismatch | photoperiodic_ornamental |
| 102 | _Lactuca sativa_ | Asteraceae | herb | annual | - | long_day | - | default-fallback | - |
| 103 | _Lavandula angustifolia_ | Lamiaceae | subshrub | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 104 | _Lens culinaris_ | Fabaceae | herb | - | - | - | - | default-fallback | - |
| 105 | _Lithops spp._ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_double_rest |
| 106 | _Livistona chinensis_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | palm_evergreen |
| 107 | _Luffa aegyptiaca_ | Cucurbitaceae | vine | - | - | - | - | default-fallback | - |
| 108 | _Mammillaria spp._ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 109 | _Maranta leuconeura_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 110 | _Matricaria chamomilla_ | Asteraceae | herb | - | - | - | - | default-fallback | - |
| 111 | _Mentha piperita_ | Lamiaceae | herb | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 112 | _Monstera adansonii_ | - | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 113 | _Monstera deliciosa_ | Araceae | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 114 | _Neoregelia carolinae_ | - | epiphyte | perennial | monocarpic | day_neutral | CAM | mismatch | clonal_monocarp |
| 115 | _Nephrolepis exaltata_ | - | fern | perennial | - | day_neutral | - | mismatch | fern_spore |
| 116 | _Nicotiana tabacum_ | Solanaceae | herb | - | - | - | - | default-fallback | - |
| 117 | _Nymphaea alba_ | Nymphaeaceae | aquatic | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 118 | _Ocimum basilicum_ | Lamiaceae | herb | annual | polycarpic | day_neutral | - | default-fallback | - |
| 119 | _Opuntia microdasys_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 120 | _Oryza sativa_ | Poaceae | grass | - | - | - | - | default-fallback | - |
| 121 | _Oxalis triangularis_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 122 | _Pachira aquatica_ | - | tree | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 123 | _Pelargonium zonale_ | Geraniaceae | subshrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 124 | _Peperomia obtusifolia_ | - | herb | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 125 | _Petroselinum crispum_ | Apiaceae | herb | biennial | monocarpic | long_day | - | mismatch | biennial_vernalization* |
| 126 | _Petunia x hybrida_ | Solanaceae | herb | annual | polycarpic | day_neutral | - | default-fallback | - |
| 127 | _Phalaenopsis hybrida_ | - | epiphyte | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 128 | _Phaseolus vulgaris_ | Fabaceae | herb | annual | - | day_neutral | - | default-fallback | - |
| 129 | _Philodendron hederaceum_ | - | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 130 | _Physalis peruviana_ | Solanaceae | herb | - | polycarpic | - | - | default-fallback | - |
| 131 | _Pilea peperomioides_ | Urticaceae | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 132 | _Pisum sativum_ | Fabaceae | vine | annual | - | long_day | - | default-fallback | - |
| 133 | _Platycerium bifurcatum_ | - | fern | perennial | - | day_neutral | - | mismatch | fern_spore |
| 134 | _Plectranthus verticillatus_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 135 | _Raphanus sativus_ | Brassicaceae | herb | annual | - | day_neutral | - | default-fallback | - |
| 136 | _Rhipsalis baccifera_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 137 | _Rhododendron simsii_ | - | shrub | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 138 | _Salvia officinalis_ | Lamiaceae | subshrub | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 139 | _Salvia rosmarinus_ | Lamiaceae | subshrub | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 140 | _Schefflera arboricola_ | - | shrub | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 141 | _Schlumbergera truncata_ | - | succulent | perennial | polycarpic | short_day | CAM | mismatch | photoperiodic_ornamental |
| 142 | _Sedum morganianum_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 143 | _Solanum lycopersicum_ | Solanaceae | herb | annual | polycarpic | day_neutral | - | default-fallback | - |
| 144 | _Solanum melongena_ | Solanaceae | herb | - | polycarpic | - | - | default-fallback | - |
| 145 | _Solanum tuberosum_ | Solanaceae | herb | - | - | - | - | default-fallback | - |
| 146 | _Soleirolia soleirolii_ | - | groundcover | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 147 | _Sorghum bicolor_ | Poaceae | grass | - | - | - | - | default-fallback | - |
| 148 | _Spathiphyllum wallisii_ | Araceae | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 149 | _Stephanotis floribunda_ | - | vine | perennial | polycarpic | short_day | - | mismatch | photoperiodic_ornamental |
| 150 | _Strelitzia reginae_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 151 | _Streptocarpus hybridus_ | - | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 152 | _Streptocarpus ionanthus_ | - | herb | perennial | polycarpic | long_day | - | mismatch | evergreen_foliage_perennial |
| 153 | _Stromanthe sanguinea_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 154 | _Syngonium podophyllum_ | - | vine | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 155 | _Tagetes erecta_ | Asteraceae | herb | - | - | - | - | default-fallback | - |
| 156 | _Thymus vulgaris_ | Lamiaceae | subshrub | - | polycarpic | - | - | mismatch | evergreen_foliage_perennial |
| 157 | _Tigridia pavonia_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 158 | _Tillandsia usneoides_ | - | epiphyte | perennial | - | day_neutral | CAM | mismatch | cam_succulent_rest |
| 159 | _Tradescantia zebrina_ | - | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 160 | _Trifolium pratense_ | Fabaceae | herb | - | - | - | - | default-fallback | - |
| 161 | _Triticum aestivum_ | Poaceae | grass | - | - | - | - | default-fallback | - |
| 162 | _Verbena x hybrida_ | Verbenaceae | herb | - | polycarpic | - | - | default-fallback | - |
| 163 | _Vicia faba_ | Fabaceae | herb | - | - | - | - | default-fallback | - |
| 164 | _Viola x wittrockiana_ | Violaceae | herb | perennial | polycarpic | day_neutral | - | mismatch | evergreen_foliage_perennial |
| 165 | _Vriesea splendens_ | - | epiphyte | perennial | monocarpic | day_neutral | CAM | mismatch | clonal_monocarp |
| 166 | _Yucca elephantipes_ | - | tree | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 167 | _Zamioculcas zamiifolia_ | - | succulent | perennial | polycarpic | day_neutral | CAM | mismatch | cam_succulent_rest |
| 168 | _Zantedeschia aethiopica_ | - | bulb_geophyte | perennial | polycarpic | day_neutral | - | mismatch | geophyte_fine |
| 169 | _Zea mays_ | Poaceae | grass | - | - | - | - | default-fallback | - |

---

## 5. Gap-Liste — Arten ohne heute passende Sequence (124)

Jede der folgenden Arten fällt heute nur mangels Muster auf `indoor_default` und hat einen
Lebenszyklus, den `indoor_default` strukturell falsch abbildet. Gruppiert nach vorgeschlagener
Zielsequenz (Abschnitt 6). `biennial_vernalization*` = **existierende** Sequence — hier fehlt nur die
Zuordnung (monokarpe Wurzel-/Blatt-Zweijährige, die als Indoor „aufgelöst" wurden, weil sie keinen
Outdoor-Lifecycle-Eintrag haben).

| Vorgeschlagene Sequence | Anzahl | Species |
|---|---|---|
| `cam_succulent_rest` | 20 | _Aloe vera_, _Cattleya hybrida_, _Ceropegia woodii_, _Crassula ovata_, _Curio rowleyanus_, _Dracaena angolensis_, _Dracaena trifasciata_, _Echeveria elegans_, _Gymnocalycium mihanovichii_, _Haworthiopsis fasciata_, _Hoya carnosa_, _Mammillaria spp._, _Opuntia microdasys_, _Peperomia obtusifolia_, _Phalaenopsis hybrida_, _Rhipsalis baccifera_, _Sedum morganianum_, _Tillandsia usneoides_, _Yucca elephantipes_, _Zamioculcas zamiifolia_ |
| `cam_double_rest` | 1 | _Lithops spp._ |
| `clonal_monocarp` | 4 | _Aechmea fasciata_, _Guzmania lingulata_, _Neoregelia carolinae_, _Vriesea splendens_ |
| `photoperiodic_ornamental` | 13 | _Anemone hupehensis_, _Aphelandra squarrosa_, _Cannabis sativa_, _Dahlia pinnata_, _Dahlia x cultorum_, _Euphorbia pulcherrima_, _Gardenia jasminoides_, _Jasminum polyanthum_, _Kalanchoe blossfeldiana_, _Kalanchoe daigremontiana_, _Rhododendron simsii_, _Schlumbergera truncata_, _Stephanotis floribunda_ |
| `palm_evergreen` | 4 | _Chamaedorea elegans_, _Dypsis lutescens_, _Howea forsteriana_, _Livistona chinensis_ |
| `fern_spore` | 4 | _Adiantum raddianum_, _Asplenium nidus_, _Nephrolepis exaltata_, _Platycerium bifurcatum_ |
| `geophyte_fine` | 8 | _Allium cepa_, _Allium sativum_, _Clivia miniata_, _Cyclamen persicum_, _Hippeastrum hybridum_, _Oxalis triangularis_, _Tigridia pavonia_, _Zantedeschia aethiopica_ |
| `evergreen_foliage_perennial` | 63 | _Aeschynanthus radicans_, _Aglaonema commutatum_, _Allium schoenoprasum_, _Alocasia x amazonica_, _Anthurium andraeanum_, _Ardisia crenata_, _Asparagus officinalis_, _Asparagus setaceus_, _Aspidistra elatior_, _Astilbe chinensis_, _Beaucarnea recurvata_, _Begonia rex-cultorum_, _Buxus sempervirens_, _Chlorophytum comosum_, _Cichorium intybus_, _Clematis spp._, _Codiaeum variegatum_, _Coffea arabica_, _Cornus mas_, _Ctenanthe burle-marxii_, _Delphinium elatum_, _Dendrobium nobile_, _Dieffenbachia seguine_, _Dracaena fragrans_, _Dracaena marginata_, _Echinacea purpurea_, _Epipremnum aureum_, _Fatsia japonica_, _Ficus benjamina_, _Ficus elastica_, _Ficus lyrata_, _Fittonia albivenis_, _Fragaria x ananassa_, _Goeppertia lancifolia_, _Goeppertia makoyana_, _Goeppertia orbifolia_, _Hedera helix_, _Hibiscus rosa-sinensis_, _Humulus lupulus_, _Lavandula angustifolia_, _Maranta leuconeura_, _Mentha piperita_, _Monstera adansonii_, _Monstera deliciosa_, _Nymphaea alba_, _Pachira aquatica_, _Pelargonium zonale_, _Philodendron hederaceum_, _Pilea peperomioides_, _Plectranthus verticillatus_, _Salvia officinalis_, _Salvia rosmarinus_, _Schefflera arboricola_, _Soleirolia soleirolii_, _Spathiphyllum wallisii_, _Strelitzia reginae_, _Streptocarpus hybridus_, _Streptocarpus ionanthus_, _Stromanthe sanguinea_, _Syngonium podophyllum_, _Thymus vulgaris_, _Tradescantia zebrina_, _Viola x wittrockiana_ |
| `biennial_vernalization*` | 7 | _Apium graveolens_, _Apium graveolens var. rapaceum_, _Brassica oleracea var. capitata_, _Brassica oleracea var. sabellica_, _Daucus carota_, _Foeniculum vulgare_, _Petroselinum crispum_ |

**Treibende Attribute je Gap-Klasse (Zitat aus den Seed-Daten):**

- **CAM (`photosynthesis_type: cam`, 20+1):** distinkte Ruhephysiologie (kühl-trockene Winterruhe;
  Lithops mit zusätzlichem sommerlichem Hüllblattwechsel). REQ-003 v2.10 D9; Business-Case „Sukkulente/CAM":
  „Aktivwachstum -> `winter_rest` ↻ — biologisch verschieden von perennial-`dormancy`".
- **Monokarpe Bromelien (`flowering_strategy: monocarpic`, 4):** terminale Einmalblüte + **klonale
  Fortführung** über Kindel statt Zyklus-Neustart. REQ-001 (`flowering_strategy`), REQ-003 D10,
  Business-Case „Kindel-Monokarp". `indoor_default` würde fälschlich einen neuen Sämlingszyklus starten.
- **Photoperiodische Zierpflanzen (`photoperiod_type: short_day`, 13):** Kurztag-Induktion ->
  Hochblattfärbung (Weihnachtsstern, Kalanchoe, Schlumbergera). REQ-003 D11 / E1
  (`photoperiod_based`-Trigger, `critical_day_length_hours`).
- **Palmen (`growth_habit`/Gattung, 4):** immergrün ohne Blühzyklus — Etablierung + Wedel-/Stammwachstum.
  REQ-003 D12 (`young_palm`, `shaft_growth`).
- **Farne (`growth_habit: fern`, 4):** sporenbasiert, keine Blüte — Wedel-/Ruhephase. REQ-003 D12
  (`leaf_phase`, `rest_phase`).
- **Feingranulare Geophyten (`growth_habit: bulb_geophyte`, 8):** Speicherorgan-Zyklus
  (Austrieb -> Wachstum -> Blüte -> Knollen-/Zwiebelfüllung -> Trockenruhe). REQ-003 D12 + D7
  (Bulb-Geophyten-Zyklus `dormancy -> bud_break` mit `is_cycle_restart`).
- **Immergrüne Blattschmuck-Perennials (`cycle_type: perennial`, 63):** die **größte** Indoor-Kohorte
  (Araceae, Ficus, Marantaceae, tropische Foliage). Kein Ruhezyklus, Dauerwachstum, seltene Blüte —
  aber `indoor_default` terminiert nach einer Saison. Dieser Ablauf war in REQ-003 nicht als eigenes
  Template geführt; **dieser Audit deckt ihn als eigenständige Lücke auf** (Abschnitt 6, Sequence
  `evergreen_foliage_perennial`).
- **Monokarpe Zweijährige (`flowering_strategy: monocarpic`, 7):** Sellerie, Kohl, Möhre, Fenchel,
  Petersilie — botanisch Biennials mit Vernalisation. Sie passen in die **existierende**
  `biennial_vernalization`; heute fehlt nur die Zuordnung (kein Outdoor-Lifecycle-Eintrag).

**45 Arten** mit Verdikt `default-fallback` (annuelle/tender Nutzpflanzen wie Tomate, Gurke, Salat,
Bohnen, Getreide, Basilikum) sind in Abschnitt 4 gelistet. Für sie ist `indoor_default` funktional
tragbar; sauberer wären jedoch die existierenden `annual_harvest`/`annual_flower` bzw. — für die
tender-perennierenden Kräuter (Lavandula, Mentha, Salvia, Thymus; via `perennial_species`) —
`evergreen_foliage_perennial`. Diese Feinzuordnung ist Folge-Arbeit, kein Blocker.

---

## 6. Vorformulierte fehlende Phase-Sequenzen (Draft-YAML)

Der folgende Draft ergänzt **18 `phase_definitions`** (alle Phasennamen aus dem kanonischen
`PhaseType`-Enum in `schemas/_defs.schema.yaml`, 53 Werte) und **8 `phase_sequences`**.
Sieben davon setzen die REQ-003-Templates **D9-D12** um; die achte
(`evergreen_foliage_perennial`) schließt die in Abschnitt 5 aufgedeckte größte Lücke.

**Validierung:** Das komplette Draft-Dokument wurde mit `jsonschema` gegen
`src/backend/app/migrations/seed_data/schemas/phase_sequences.schema.yaml` geprüft -> **PASS**
(18 `phase_definitions`, 8 `phase_sequences`; alle `required`-Felder gesetzt, alle Enums
[`cycle_type`, `stress_tolerance`, `photoperiod_type`] gültig, keine `additionalProperties`).

> **Referenz-Integrität:** Das Schema behandelt `phase_sequence_entry.phase_name` als freien String
> (kein `$ref` auf `phase_definition.name`), validiert also unabhängig. Der Draft liefert dennoch für
> **jeden** verwendeten Phasennamen eine passende `phase_definition` mit, damit die Sequenzen beim
> späteren Seeding ohne Nachpflege bestehen.

```yaml
# yaml-language-server: $schema=./schemas/phase_sequences.schema.yaml
# DRAFT — proposed additional phase definitions + phase sequences (audit #576).
# NOT seeded here; validation-only draft for the follow-up seeding issue.
# Phase names reuse the canonical PhaseType enum (_defs.schema.yaml, 53 values).

phase_definitions:
  # -- CAM / succulent rest phases (D9) --
  - name: active_growth
    display_name: Active Growth
    display_name_de: Aktivwachstum
    description: Main CAM/succulent active growth window (spring to autumn)
    description_de: Hauptwachstumsfenster der CAM-/Sukkulentenkultur (Frühjahr bis Herbst)
    typical_duration_days: 210
    stress_tolerance: medium
    watering_interval_days: 7
    tags: [cam, succulent, growth]
    is_system: true
  - name: winter_rest
    display_name: Winter Rest
    display_name_de: Winterruhe (kühl-trocken)
    description: Cool, dry winter rest for CAM succulents; biologically distinct from woody dormancy
    description_de: Kühl-trockene Winterruhe der CAM-Sukkulenten; biologisch verschieden von Gehölz-Dormanz
    typical_duration_days: 120
    stress_tolerance: high
    watering_interval_days: 30
    tags: [cam, succulent, rest, winter]
    is_system: true
  - name: summer_rest
    display_name: Summer Rest
    display_name_de: Sommerruhe
    description: Aestivation rest for summer-dormant geophytes and mesembs
    description_de: Sommerruhe sommerruhender Geophyten und Mittagsblumengewächse
    typical_duration_days: 90
    stress_tolerance: high
    watering_interval_days: 30
    tags: [succulent, rest, summer]
    is_system: true
  - name: winter_hull_change
    display_name: Hull Change
    display_name_de: Hüllblattwechsel
    description: Lithops leaf-pair renewal during rest; watering must stop
    description_de: Blattpaar-Erneuerung bei Lithops während der Ruhe; Gießen muss ruhen
    typical_duration_days: 60
    stress_tolerance: high
    watering_interval_days: 45
    tags: [lithops, mesemb, rest]
    is_system: true

  # -- Clonal monocarp phases (D10) --
  - name: juvenile
    display_name: Juvenile
    display_name_de: Jugendphase
    description: Pre-reproductive vegetative maturation of monocarpic rosette plants
    description_de: Vorreproduktive vegetative Reifung monokarper Rosettenpflanzen
    typical_duration_days: 365
    stress_tolerance: medium
    watering_interval_days: 7
    tags: [monocarp, juvenile]
    is_system: true
  - name: mature
    display_name: Mature
    display_name_de: Reife (blühfähig)
    description: Reproductively mature rosette ready for terminal flowering
    description_de: Reproduktiv reife Rosette, bereit zur terminalen Blüte
    typical_duration_days: 180
    stress_tolerance: medium
    watering_interval_days: 7
    tags: [monocarp, mature]
    is_system: true
  - name: pup_establishment
    display_name: Pup Establishment
    display_name_de: Kindel-Etablierung
    description: Clonal offset (pup) rooting after the mother rosette dies; new instance continuation
    description_de: Bewurzelung des klonalen Kindels nach Absterben der Mutterrosette; Fortführung als neue Instanz
    typical_duration_days: 90
    stress_tolerance: low
    watering_interval_days: 5
    tags: [monocarp, pup, clonal]
    is_system: true

  # -- Photoperiodic ornamental induction phases (D11) --
  - name: short_day_induction
    display_name: Short-Day Induction
    display_name_de: Kurztag-Induktion
    description: Photoperiodic flower induction under short days (< critical day length)
    description_de: Photoperiodische Blühinduktion unter Kurztag (< kritische Tageslänge)
    typical_duration_days: 42
    stress_tolerance: medium
    watering_interval_days: 4
    tags: [photoperiod, short-day, induction]
    is_system: true
  - name: bract_coloring
    display_name: Bract Coloring
    display_name_de: Hochblattfärbung
    description: Bract/inflorescence coloring following short-day induction (poinsettia, Kalanchoe)
    description_de: Hochblatt-/Blütenstandsfärbung nach Kurztag-Induktion (Weihnachtsstern, Kalanchoe)
    typical_duration_days: 35
    stress_tolerance: medium
    watering_interval_days: 4
    tags: [photoperiod, ornamental, bract]
    is_system: true

  # -- Palm / fern / fine geophyte phases (D12) --
  - name: establishment
    display_name: Establishment
    display_name_de: Etablierung
    description: Post-transplant establishment of woody/evergreen ornamentals
    description_de: Anwuchsphase holziger/immergrüner Zierpflanzen nach dem Umtopfen
    typical_duration_days: 120
    stress_tolerance: low
    watering_interval_days: 5
    tags: [establishment]
    is_system: true
  - name: young_palm
    display_name: Young Palm
    display_name_de: Jungpalme
    description: Juvenile palm stage before trunk formation
    description_de: Juveniles Palmenstadium vor der Stammbildung
    typical_duration_days: 365
    stress_tolerance: medium
    watering_interval_days: 6
    tags: [palm, juvenile]
    is_system: true
  - name: shaft_growth
    display_name: Shaft Growth
    display_name_de: Stammwachstum
    description: Ongoing frond and trunk growth of established evergreen palms
    description_de: Fortlaufendes Wedel- und Stammwachstum etablierter immergrüner Palmen
    typical_duration_days: 300
    stress_tolerance: medium
    watering_interval_days: 6
    tags: [palm, growth]
    is_system: true
  - name: leaf_phase
    display_name: Frond Phase
    display_name_de: Wedelphase
    description: Active frond growth of ferns (no flowering; spore-based reproduction)
    description_de: Aktives Wedelwachstum der Farne (keine Blüte; sporenbasierte Vermehrung)
    typical_duration_days: 210
    stress_tolerance: medium
    watering_interval_days: 3
    tags: [fern, frond]
    is_system: true
  - name: rest_phase
    display_name: Rest Phase
    display_name_de: Ruhephase
    description: Reduced-growth rest for ferns and evergreens over winter
    description_de: Wachstumsreduzierte Winterruhe für Farne und Immergrüne
    typical_duration_days: 90
    stress_tolerance: high
    watering_interval_days: 7
    tags: [fern, rest]
    is_system: true
  - name: sprout_formation
    display_name: Sprout Formation
    display_name_de: Austriebsbildung
    description: Bud/sprout formation of geophytes emerging from the storage organ
    description_de: Knospen-/Austriebsbildung der Geophyten aus dem Speicherorgan
    typical_duration_days: 21
    stress_tolerance: low
    watering_interval_days: 4
    tags: [geophyte, sprout]
    is_system: true
  - name: tuber_formation
    display_name: Tuber Formation
    display_name_de: Knollenbildung
    description: Storage-organ (tuber/corm/bulb) fill before senescence
    description_de: Auffüllung des Speicherorgans (Knolle/Korm/Zwiebel) vor der Seneszenz
    typical_duration_days: 45
    stress_tolerance: medium
    watering_interval_days: 5
    tags: [geophyte, storage]
    is_system: true
  - name: dry_storage
    display_name: Dry Storage
    display_name_de: Trockenlager
    description: Dormant dry storage of the geophyte storage organ (lifted or in situ)
    description_de: Trockene Ruhelagerung des Geophyten-Speicherorgans (ausgegraben oder in situ)
    typical_duration_days: 120
    stress_tolerance: high
    watering_interval_days: 45
    tags: [geophyte, storage, dormancy]
    is_system: true

  # -- Evergreen indoor foliage perennial phases (audit finding) --
  - name: maintenance
    display_name: Maintenance Growth
    display_name_de: Erhaltungswachstum
    description: Steady-state maintenance growth of an evergreen foliage plant between flushes
    description_de: Stationäres Erhaltungswachstum einer immergrünen Blattschmuckpflanze zwischen den Schüben
    typical_duration_days: 180
    stress_tolerance: medium
    watering_interval_days: 5
    tags: [indoor, foliage, maintenance]
    is_system: true

phase_sequences:

  # -- D9a: CAM succulent single winter rest --
  - name: cam_succulent_rest
    display_name: CAM Succulent (Winter Rest)
    display_name_de: CAM-Sukkulente (Winterruhe)
    description: CAM succulents with active growth, bloom and a cool-dry winter rest
    description_de: CAM-Sukkulenten mit Aktivwachstum, Blüte und kühl-trockener Winterruhe
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 0
    dormancy_required: true
    photoperiod_type: day_neutral
    tags: [cam, succulent, indoor, rest]
    is_system: true
    entries:
      - phase_name: active_growth
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: flowering
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: winter_rest
        sequence_order: 2
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- D9b: CAM double rest (Lithops / mesembs) --
  - name: cam_double_rest
    display_name: CAM Double Rest
    display_name_de: CAM-Doppelruhe
    description: Mesembs/Lithops with both a summer rest and a winter hull-change rest
    description_de: Mittagsblumen/Lithops mit Sommerruhe und winterlichem Hüllblattwechsel
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 0
    dormancy_required: true
    photoperiod_type: day_neutral
    tags: [cam, mesemb, lithops, double-rest]
    is_system: true
    entries:
      - phase_name: active_growth
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: flowering
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: winter_hull_change
        sequence_order: 2
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: summer_rest
        sequence_order: 3
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- D10: Clonal monocarp (Kindel) — terminal bloom + pup continuation --
  - name: clonal_monocarp
    display_name: Clonal Monocarp (Pup Continuation)
    display_name_de: Klonaler Monokarp (Kindel-Fortführung)
    description: Monocarpic rosettes (Bromeliad/Agave) that flower once, die, and continue via pups
    description_de: Monokarpe Rosetten (Bromelie/Agave) die einmal blühen, absterben und über Kindel fortleben
    cycle_type: perennial
    is_repeating: false
    photoperiod_type: day_neutral
    tags: [monocarp, clonal, bromeliad, indoor]
    is_system: true
    entries:
      - phase_name: juvenile
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
      - phase_name: mature
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
      - phase_name: flowering
        sequence_order: 2
        is_terminal: false
        allows_harvest: false
      - phase_name: pup_establishment
        sequence_order: 3
        is_terminal: true
        allows_harvest: false

  # -- D11: Photoperiodic ornamental short-day induction --
  - name: photoperiodic_ornamental
    display_name: Photoperiodic Ornamental (Short-Day)
    display_name_de: Photoperiodische Zierpflanze (Kurztag)
    description: Short-day ornamentals induced to color bracts/flowers (poinsettia, Kalanchoe)
    description_de: Kurztag-Zierpflanzen mit induzierter Hochblatt-/Blütenfärbung (Weihnachtsstern, Kalanchoe)
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 0
    photoperiod_type: short_day
    critical_day_length_hours: 12
    tags: [photoperiod, short-day, ornamental, indoor]
    is_system: true
    entries:
      - phase_name: active_growth
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: short_day_induction
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: bract_coloring
        sequence_order: 2
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: rest_phase
        sequence_order: 3
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- D12a: Evergreen palm --
  - name: palm_evergreen
    display_name: Evergreen Palm
    display_name_de: Immergrüne Palme
    description: Evergreen palms with no flowering cycle; establishment then continuous frond/shaft growth
    description_de: Immergrüne Palmen ohne Blühzyklus; Etablierung, dann fortlaufendes Wedel-/Stammwachstum
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 1
    photoperiod_type: day_neutral
    tags: [palm, evergreen, indoor]
    is_system: true
    entries:
      - phase_name: young_palm
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
      - phase_name: establishment
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: shaft_growth
        sequence_order: 2
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- D12b: Spore-based fern --
  - name: fern_spore
    display_name: Spore-Based Fern
    display_name_de: Sporenbasierter Farn
    description: Ferns with active frond phase and a reduced winter rest; no flowering
    description_de: Farne mit aktiver Wedelphase und reduzierter Winterruhe; keine Blüte
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 0
    photoperiod_type: day_neutral
    tags: [fern, spore, indoor]
    is_system: true
    entries:
      - phase_name: leaf_phase
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: rest_phase
        sequence_order: 1
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- Audit finding: evergreen indoor foliage perennial (largest indoor cohort) --
  - name: evergreen_foliage_perennial
    display_name: Evergreen Foliage Perennial
    display_name_de: Immergrüne Blattschmuck-Staude
    description: Tropical foliage houseplants (Araceae, Ficus, Marantaceae) with continuous growth, no dormancy, occasional bloom
    description_de: Tropische Blattschmuckpflanzen (Aronstab-, Ficus-, Pfeilwurzgewächse) mit Dauerwachstum, ohne Ruhe, seltener Blüte
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 1
    dormancy_required: false
    photoperiod_type: day_neutral
    tags: [indoor, foliage, evergreen, perennial]
    is_system: true
    entries:
      - phase_name: establishment
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
      - phase_name: active_growth
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: flowering
        sequence_order: 2
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: maintenance
        sequence_order: 3
        is_terminal: true
        allows_harvest: false
        is_recurring: true

  # -- D12c: Fine-grained geophyte --
  - name: geophyte_fine
    display_name: Fine-Grained Geophyte
    display_name_de: Feingranularer Geophyt
    description: Storage-organ geophytes with sprout, growth, bloom, storage fill and dry dormancy
    description_de: Speicherorgan-Geophyten mit Austrieb, Wachstum, Blüte, Speicherauffüllung und Trockenruhe
    cycle_type: perennial
    is_repeating: true
    cycle_restart_entry_order: 4
    dormancy_required: true
    photoperiod_type: day_neutral
    tags: [geophyte, bulb, tuber, corm, indoor]
    is_system: true
    entries:
      - phase_name: sprout_formation
        sequence_order: 0
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: vegetative
        sequence_order: 1
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: flowering
        sequence_order: 2
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: tuber_formation
        sequence_order: 3
        is_terminal: false
        allows_harvest: false
        is_recurring: true
      - phase_name: dry_storage
        sequence_order: 4
        is_terminal: true
        allows_harvest: false
        is_recurring: true
```

### Zuordnungs-Matrix (Draft-Sequence -> Kandidaten)

| Draft-Sequence | REQ-003-Bezug | Kandidaten (Anzahl) | Restart-Semantik |
|---|---|---|---|
| `cam_succulent_rest` | D9 | 20 | wiederholend, Winterruhe terminal->Restart 0 |
| `cam_double_rest` | D9 (Lithops) | 1 | wiederholend, Sommerruhe terminal->Restart 0 |
| `clonal_monocarp` | D10 | 4 | **nicht** wiederholend; `pup_establishment` terminal = neue Instanz |
| `photoperiodic_ornamental` | D11 | 13 | wiederholend, `short_day`-Induktion, `critical_day_length_hours: 12` |
| `palm_evergreen` | D12 | 4 | wiederholend, Restart bei `establishment` (kein Jungpalmen-Rücksprung) |
| `fern_spore` | D12 | 4 | wiederholend, `leaf_phase`<->`rest_phase` |
| `geophyte_fine` | D12 + D7 | 8 | wiederholend, Restart bei `dry_storage`->`sprout_formation` |
| `evergreen_foliage_perennial` | Audit-Fund | 63 | wiederholend, Restart bei `active_growth` (kein Termin-Ende) |

---

## 7. Empfehlungen (für das Seeding-Folge-Issue)

1. **Draft-Sequenzen seeden** (Abschnitt 6) — additive Ergänzung in `phase_sequences.yaml`,
   danach die `HAS_PHASE_SEQUENCE`-Blanket-Logik durch einen **attributgetriebenen Resolver**
   ersetzen bzw. ergänzen, der `flowering_strategy`/`photosynthesis_type`/`photoperiod_type`/
   `growth_habit`/`cycle_type` in dieser Präzedenz auswertet (siehe `target()`-Logik dieses Audits).
2. **Bestehende Sequenzen zuordnen** — die 7 monokarpen Biennials auf `biennial_vernalization`,
   die 45 `default-fallback`-Nutzpflanzen auf `annual_harvest`/`annual_flower`.
3. **Idempotenz beachten** — `_link_indoor_species_to_default_sequence` überspringt Arten mit
   existierender Kante; ein Resolver muss vor der Blanket-Stufe laufen, sonst „gewinnt" `indoor_default`.
4. **Migration** — Umhängen bestehender Kanten ist eine Datenänderung (versioniertes Migrations-
   Framework, NFR-016) und gehört nicht in einen additiven Seed-PR.

---

## Quellen

- `spec/req/REQ-003_Phasensteuerung.md` v2.10 (Changelog 2.9/2.10; Business-Case-Archetypen
  „Sukkulente/CAM", „Kindel-Monokarp", „Photoperioden-Zier", „Palme/Farn/feingranulare Geophyten";
  `TransitionTriggerType` `photoperiod_based`/`vernalization_based`; `PhaseType` 53 Werte).
- `spec/req/REQ-001_Stammdatenverwaltung.md` (`flowering_strategy` monocarpic/polycarpic,
  `cultivation_cycle_type`, `growth_determinacy`).
- `spec/req/REQ-047` (Überwinterungs-Automatik; Ruhe-/Dormanz-Anbindung).
- `spec/analysis/lifecycle-flow-completeness-audit.md` (Befund 2: D9-D12-Flow-Templates;
  Phasen-Belege `winter_rest` 42x, `pup_establishment`, `short_day_induction`, `young_palm`,
  `leaf_phase`, `corm_ripening` u. a.).
- `spec/analysis/perennial-outdoor-lifecycle-modelling.md` (Outdoor-Perennial-Modellierung).
- Seed-Quellen: `src/backend/app/migrations/seed_data/{species.yaml, lifecycles_outdoor.yaml,
  phase_sequences.yaml, plant_info*.yaml, adventskalender.yaml}`;
  `schemas/phase_sequences.schema.yaml`, `schemas/_defs.schema.yaml`.
- Seed-Code: `seed_data.py:108-151` (Blanket-Default), `seed_lifecycles_outdoor.py:246-290`
  (explizite Outdoor-Zuordnung).
- Steckbriefe: `spec/knowledge/plants/*.md` (210).
