# Knowledge-Base Expansion Plan

**Erstellt:** 2026-04-07
**Aktueller Stand:** 267 Chunks, 36 YAML-Dateien, 87.4% Benchmark-Score
**Ziel:** ~550 Chunks, ~196 Benchmark-Fragen, >85% Score auf erweitertem Benchmark

---

## Uebersicht

| Phase | Thema | Neue Chunks | Prioritaet |
|-------|-------|-------------|------------|
| 1 | Artspezifische Zimmerpflanzen (Top 35) | ~110 | HOECHSTE |
| 2 | Krankheiten & Schaedlinge erweitern | ~31 | HOCH |
| 3 | Gemuese-Anbauanleitungen (Top 17) | ~61 | HOCH |
| 4 | Vermehrung | ~19 | MITTEL-HOCH |
| 5 | Balkon/Terrasse/Kuebel | ~18 | MITTEL |
| 6 | Saisonkalender | ~18 | MITTEL |
| 7 | Obstbaeume & Beerenstraeucher | ~17 | MITTEL-NIEDRIG |
| 8 | Bodenverbesserung | ~9 | NIEDRIG |
| **Total** | | **~283** | |

Kumulativ: 267 (bestehend) + 283 (neu) = **~550 Chunks**

---

## Phase 1: Artspezifische Zimmerpflanzen-Pflege (HOECHSTE Prioritaet)

**Begruendung:** 210 Pflanzenprofile existieren bereits als Markdown unter `spec/knowledge/plants/*.md`.
Umwandlung in RAG-optimierte YAML-Chunks gibt maximalen Nutzwert bei minimalem Recherche-Aufwand.

**Verzeichnis:** `spec/knowledge/pflege/arten/`
**Pro Pflanze:** 3-5 Chunks (Licht/Standort, Giessen/Substrat, Duengung/Umtopfen, Probleme, Vermehrung)

### Dateiliste (35 Pflanzen/Gruppen, ~110 Chunks)

| Datei | Art(en) | Chunks |
|-------|---------|--------|
| monstera-deliciosa.yaml | Monstera deliciosa | 4 |
| ficus-lyrata.yaml | Ficus lyrata | 4 |
| ficus-elastica.yaml | Ficus elastica | 3 |
| ficus-benjamina.yaml | Ficus benjamina | 3 |
| calathea-pflege.yaml | Goeppertia (Calathea) spp. | 5 |
| alocasia-amazonica.yaml | Alocasia x amazonica | 3 |
| philodendron-hederaceum.yaml | Philodendron hederaceum | 3 |
| epipremnum-aureum.yaml | Epipremnum aureum (Pothos) | 3 |
| spathiphyllum.yaml | Spathiphyllum wallisii | 3 |
| dracaena-trifasciata.yaml | Dracaena trifasciata (Sansevieria) | 3 |
| zamioculcas.yaml | Zamioculcas zamiifolia | 3 |
| pilea-peperomioides.yaml | Pilea peperomioides | 3 |
| strelitzia-reginae.yaml | Strelitzia reginae | 3 |
| crassula-ovata.yaml | Crassula ovata (Geldbaum) | 3 |
| aloe-vera.yaml | Aloe vera | 3 |
| hoya-carnosa.yaml | Hoya carnosa | 3 |
| maranta-leuconeura.yaml | Maranta leuconeura | 3 |
| chlorophytum.yaml | Chlorophytum comosum | 3 |
| dieffenbachia.yaml | Dieffenbachia seguine | 3 |
| schefflera.yaml | Schefflera arboricola | 3 |
| yucca.yaml | Yucca elephantipes | 3 |
| dracaena-marginata.yaml | Dracaena marginata | 3 |
| aspidistra.yaml | Aspidistra elatior | 3 |
| hedera-helix.yaml | Hedera helix | 3 |
| begonia-rex.yaml | Begonia rex-cultorum | 3 |
| tradescantia.yaml | Tradescantia zebrina | 3 |
| syngonium.yaml | Syngonium podophyllum | 3 |
| anthurium.yaml | Anthurium andraeanum | 3 |
| codiaeum.yaml | Codiaeum variegatum (Kroton) | 3 |
| nephrolepis.yaml | Nephrolepis exaltata (Farn) | 3 |
| sukkulenten-sammlung.yaml | Echeveria, Haworthia, Sedum | 4 |
| kakteen-grundpflege.yaml | Mammillaria, Gymnocalycium, Opuntia | 4 |
| palmen-zimmerpflege.yaml | Chamaedorea, Howea, Dypsis | 4 |
| bromelien-pflege.yaml | Guzmania, Vriesea, Aechmea | 4 |
| hibiscus-rosa.yaml | Hibiscus rosa-sinensis | 3 |

**Quelldaten:** `spec/knowledge/plants/*.md`
**Abhaengigkeiten:** Keine

---

## Phase 2: Krankheiten & Schaedlinge erweitern (HOCH)

**Begruendung:** Aktuell nur 5 Pathogen-Chunks + 12 Schaedlings-Chunks.
Nutzer fragen haeufig nach Symptomen — breite Krankheitsabdeckung ist essenziell.

**Verzeichnis:** `spec/knowledge/diagnostik/`

### Neue Dateien (~31 Chunks)

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| pilzkrankheiten-erweitert.yaml | Rost, Schwarzfleckenkrankheit, Verticillium-Welke, Fusarium, Alternaria, Buchsbaum-Sterben, Sternrusstau, Graufleckenkrankheit | 8 |
| bakterielle-krankheiten.yaml | Feuerbrand, Bakterielle Weichfaeule, Bakterienbrand, Pseudomonas, Xanthomonas | 5 |
| virale-krankheiten.yaml | Mosaik-Viren (TMV/CMV), TSWV, Ringfleckenviren, Virusdiagnostik-Grundlagen | 4 |
| physiologische-stoerungen.yaml | Sonnenbrand, Frostschaden, Chlorose vertieft, Bluetenendfaeule, Gruenkragen, Aufplatzen | 6 |
| schaedlinge-erweitert.yaml | Dickmaulruessler, Buchsbaumzuensler, Apfelwickler, Kirschessigfliege, Schnecken, Nematoden, Wolllaeuse vertieft, Schildlaeuse vertieft | 8 |

**Quelldaten:** Phytopathologie-Fachwissen
**Abhaengigkeiten:** Keine

---

## Phase 3: Gemuese-Anbauanleitungen (HOCH)

**Verzeichnis:** `spec/knowledge/pflege/gemuese/`
**Pro Gemuese:** 3-5 Chunks (Aussaat/Voranzucht, Auspflanzen, Pflege, Krankheiten, Ernte)

### Dateiliste (17 Arten/Gruppen, ~61 Chunks)

| Datei | Art(en) | Chunks |
|-------|---------|--------|
| tomate-anbau.yaml | Solanum lycopersicum | 5 |
| paprika-chili-anbau.yaml | Capsicum annuum | 4 |
| gurke-anbau.yaml | Cucumis sativus | 4 |
| zucchini-kuerbis-anbau.yaml | Cucurbita spp. | 4 |
| salat-anbau.yaml | Lactuca sativa | 3 |
| moehre-anbau.yaml | Daucus carota | 3 |
| zwiebel-knoblauch-anbau.yaml | Allium spp. | 4 |
| kohl-anbau.yaml | Brassica oleracea | 5 |
| bohne-erbse-anbau.yaml | Phaseolus/Pisum | 4 |
| kartoffel-anbau.yaml | Solanum tuberosum | 4 |
| erdbeere-anbau.yaml | Fragaria x ananassa | 4 |
| rote-bete-mangold-anbau.yaml | Beta vulgaris | 3 |
| spinat-anbau.yaml | Spinacia oleracea | 3 |
| radieschen-anbau.yaml | Raphanus sativus | 2 |
| lauch-anbau.yaml | Allium porrum | 3 |
| sellerie-anbau.yaml | Apium graveolens | 3 |
| mais-anbau.yaml | Zea mays | 3 |

**Quelldaten:** `spec/knowledge/plants/*.md` + Praxis-Anbauanleitungen
**Abhaengigkeiten:** Profitiert von Phase 2 (Krankheits-Querverweise)

---

## Phase 4: Vermehrung (MITTEL-HOCH)

**Verzeichnis:** `spec/knowledge/pflege/vermehrung/`

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| stecklinge-grundlagen.yaml | Kopf-, Stamm-, Blattstecklinge, Wasser vs. Substrat, Bewurzelungshormon | 5 |
| teilung-und-ableger.yaml | Wurzelstock-Teilung, Kindel, Auslaeufer, Rhizom-Teilung | 4 |
| aussaat-grundlagen.yaml | Aussaat-Substrat, Licht-/Dunkelkeimer, Stratifikation, Pikieren | 4 |
| absenker-abmoosen.yaml | Absenker, Luftschichtung/Abmoosen, Steckhoelzer | 3 |
| veredelung-grundlagen.yaml | Kopulation, Okulation, Unterlagen-Wahl | 3 |

**~19 Chunks**

---

## Phase 5: Balkon/Terrasse/Kuebel (MITTEL)

**Verzeichnis:** `spec/knowledge/outdoor/balkon/`

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| balkon-grundlagen.yaml | Tragfaehigkeit, Windschutz, Sonnenstunden, Substrat, Wasserabfluss | 5 |
| balkon-gemuese.yaml | Top 10 Balkongemuese, Topfgroessen, Vertical Gardening | 5 |
| balkon-zierpflanzen.yaml | Sommerblumen, Herbstbepflanzung, Winterharte Kuebelpflanzen | 4 |
| kuebelpflege-vertieft.yaml | Duengung im Kuebel, Hitze-Management, Auto-Bewaesserung | 4 |

**~18 Chunks**

---

## Phase 6: Saisonkalender (MITTEL)

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| outdoor/saisonkalender-garten.yaml | Monat-fuer-Monat Garten (Jan-Dez) | 12 |
| pflege/saisonkalender-zimmerpflanzen.yaml | Zweimonatlich Zimmerpflanzen | 6 |

**~18 Chunks**

---

## Phase 7: Obstbaeume & Beerenstraeucher (MITTEL-NIEDRIG)

**Verzeichnis:** `spec/knowledge/pflege/obst/`

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| obstbaum-grundpflege.yaml | Pflanzung, Jahreszeitpflege, Duengung, Krankheiten | 4 |
| obstbaum-schnitt.yaml | Pflanz-/Erziehungs-/Erhaltungs-/Sommerschnitt | 5 |
| beerenstraeucher.yaml | Himbeere, Brombeere, Johannisbeere, Stachelbeere, Heidelbeere | 5 |
| wein-kiwi.yaml | Weinrebe, Kiwi | 3 |

**~17 Chunks**

---

## Phase 8: Bodenverbesserung (NIEDRIG)

| Datei | Inhalt | Chunks |
|-------|--------|--------|
| outdoor/kompostierung.yaml | Kompost anlegen, Heiss-/Kaltkompost, Wurmkompost, Bokashi | 5 |
| outdoor/mulchen-bodenbedeckung.yaml | Materialien, Zeitpunkt, No-Dig-Methode | 4 |

**~9 Chunks**

---

## Benchmark-Erweiterung

Der aktuelle Benchmark (100 Fragen) sollte auf ~196 Fragen erweitert werden:

| Kategorie | Aktuell | Neu | Beispiel-Fragen |
|-----------|---------|-----|-----------------|
| pflege (artspezifisch) | 12 | +25 | "Warum verliert mein Ficus Blaetter?", "Calathea rollt Blaetter ein" |
| diagnostik (Krankheiten) | 15 | +15 | "Orangefarbene Pusteln auf Blatt" (Rost), "Pflanze welkt einseitig" (Verticillium) |
| gemuese (NEU) | 0 | +15 | "Wann Tomaten ausgeizen?", "Gurke bitter", "Kartoffel gruen" |
| vermehrung (NEU) | 0 | +10 | "Monstera-Steckling in Wasser", "Steckling fault statt Wurzeln" |
| balkon (NEU) | 0 | +10 | "Balkon Nordseite was waechst?", "Tomaten im Kuebel welche Groesse?" |
| saisonkalender (NEU) | 0 | +8 | "Was mache ich im Maerz im Garten?" |
| obst (NEU) | 0 | +8 | "Wann Apfelbaum schneiden?", "Himbeeren zurueckschneiden?" |
| boden (NEU) | 0 | +5 | "Wie lange dauert Kompost?", "Was ist No-Dig?" |
| **Total** | **100** | **+96** | |

---

## Abhaengigkeiten und Sequenzierung

```
Phase 1 (Zimmerpflanzen) -----> Phase 4 (Vermehrung)
         |
         v
Phase 6 (Saisonkalender Zimmerpflanzen)

Phase 2 (Krankheiten) -------> Phase 3 (Gemuese)
         |                            |
         v                            v
Phase 7 (Obstbaeume)          Phase 5 (Balkon)

Phase 8 (Bodenverbesserung) -- standalone
```

**Parallelisierbar:** Phase 1 + Phase 2 gleichzeitig (keine gegenseitige Abhaengigkeit)
**Sequenziell:** Phase 3 nach Phase 2 (Krankheits-Querverweise)

---

## Implementierungs-Strategie

Fuer jede neue YAML-Datei:

1. **Daten aus Pflanzenprofil extrahieren** (`spec/knowledge/plants/<species>.md`)
2. **In problemorientierte, konversationelle Chunks umschreiben** (nicht Enzyklopaedie-Stil)
3. **Tags und Metadata ergaenzen** (umgangssprachliche Suchbegriffe, expertise_level, applicable_phases)
4. **Eindeutige Chunk-IDs** vergeben (`<species-slug>-<topic>`)
5. **Benchmark-Fragen erstellen** (mindestens 1-2 pro YAML-Datei)
6. **Topic-Synonyme ergaenzen** (`topic_synonyms.yaml`)
7. **Ingestion + Eval** zur Verifikation

**Agent-Einsatz:**
- `knowledge-chunk-author`: Erstellt Chunks aus Pflanzen-Profilen
- `agrobiology-requirements-reviewer`: Prueft botanische Korrektheit
- `rag-eval-runner`: Testet nach jeder Phase
