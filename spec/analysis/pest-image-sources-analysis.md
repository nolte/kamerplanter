# Bildquellen-Analyse für die Schädlings- & Nützlingserkennung (REQ-044)

**Datum:** 2026-06-22
**Status:** Analyse / Entscheidungsgrundlage
**Bezug:** REQ-044 (Schädlingserkennung), REQ-010 (IPM), REQ-029-A (DINOv2-Erkennungsdienst)
**Vorgänger-Docs:** `pest-detection-research.md`, `pest-detection-implementation-prep.md`, `pest-detection-readiness.md` (insb. WP-1 Lizenz, WP-3 Datensatz-Akquise)
**Methodik:** Codebase-Scan (Ist-Zustand) + adversarial-verifizierte Tiefenrecherche (25 Quellen abgerufen, 101 Claims extrahiert, 25 verifiziert: **21 bestätigt / 4 widerlegt**). Jeder belastbare Befund unten ist als *verifiziert* markiert; alles andere ist explizit als *unverifiziert/offen* gekennzeichnet.

---

## 1. Problemstellung

Die aktuelle Datenbasis ist **zu gering, um eine automatische Erkennung produktiv zu starten.** Diese Analyse beantwortet: *Welche zusätzlichen, kommerziell nutzbaren Bildquellen gibt es für die 12 Zielklassen — und welche schließen die vier bekannten Lücken?*

### Verbindliche Constraints (aus WP-1)

| Constraint | Wert |
|---|---|
| Bild-Lizenz | **nur CC0 oder CC-BY** (kommerziell + weiterverteilbar mit Attribution); **kein** CC-BY-NC, **kein** CC-BY-SA |
| Modell-Lizenz | Apache-2.0 (Code + Weights); RF-DETR-S / D-FINE-S; YOLO/Ultralytics (AGPL) ausgeschlossen |
| DSGVO | keine erkennbaren Personen; serverseitiges EXIF-Stripping |
| Architektur | **keine Bildpersistenz** — nur DINOv2-Embeddings + Attributions-Manifest (Label, Quelle, Source-URL, Lizenz, Attribution) |
| Bedarf Stufe 1 | frozen DINOv2 + Prototypical/kNN, ~10–30 Bilder/Klasse (on-leaf) |
| Bedarf Stufe 2 | RF-DETR-S + SAHI-Tiling, **150+ annotierte Box-Labels/Klasse** (Gelbtafel) |

### Ist-Zustand der Akquise (Codebase)

| Baustein | Stand | Datei |
|---|---|---|
| CLI `acquire_pest_dataset` | implementiert | `src/backend/app/migrations/acquire_pest_dataset.py:1` |
| `PestDatasetAcquisitionService` | implementiert | `src/backend/app/domain/services/pest_dataset_acquisition.py:30` |
| GBIF-Media-Client | implementiert | `src/backend/app/data_access/external/gbif_media_client.py:23` |
| Lizenz-Filter (CC0/CC-BY) | implementiert | `reference_image.py:30` (`ACCEPTED_LICENSES`), `reference_image_license.py:16` |
| Taxonomie (7 Pest + 5 Beneficial) | vollständig, mit GBIF-Keys | `src/backend/app/domain/models/pest_taxonomy.py:36` |
| Seed-Daten + `detection_slug` | implementiert | `src/backend/app/migrations/seed_data/ipm.yaml` |

**Einzige Quelle heute:** GBIF, ausschließlich iNaturalist-Research-Grade-Dataset (`50c9509d-22c7-4a22-a47d-8c48425ef4a7`), Ziel `pest_reference_min_usable=30` Bilder/Klasse. Das reicht für Stufe 1, **nicht** für den Detektor.

### Die 12 Zielklassen

**Schädlinge:** `spider_mite` (*Tetranychus urticae*, 2130185), `thrips_frankliniella` (*Frankliniella occidentalis*, 8351995), `thrips_echinothrips` (*Echinothrips americanus*, 1420846), `fungus_gnat` (Sciaridae, 3525), `aphid` (Aphididae, 3042), `mealybug` (Pseudococcidae, 4534), `whitefly` (*Trialeurodes vaporariorum*, 2012132).
**Nützlinge:** `ladybird` (Coccinellidae, 7782, inkl. **Larven**), `lacewing` (Chrysopidae, 9265, **Larven**), `hoverfly` (Syrphidae, 6920, **Larven**), `predatory_mite` (Phytoseiidae, 3511), `parasitoid_wasp` (*Encarsia formosa*, 1365418).

### Die vier bekannten Lücken

1. **Trauermücken** (`fungus_gnat`, Sciaridae) — keine dedizierten Detektor-Datensätze.
2. **Wollläuse** (`mealybug`, Pseudococcidae) — sehr dünne Abdeckung.
3. **Spinnmilben** (`spider_mite`, <0,5 mm) — Web-Bilder zeigen meist Schadbild statt Tier.
4. **Nützlings-Larven** (`ladybird`/`lacewing`/`hoverfly`) — Research-Grade-Daten überwiegend Adulte.

---

## 2. Kernergebnis (Executive Summary)

Jenseits von GBIF-iNat-RG ist das verfügbare CC0/CC-BY-Bildangebot für diese 12 Klassen **fragmentiert und dünn.** Die wichtigsten verifizierten Befunde:

1. **Nur _eine_ Zielklasse ist heute über einen fertigen, sauber lizenzierten Detektor-Datensatz gelöst:** `whitefly`, über die Yellow-Sticky-Trap-Sets von **Nieuwenhuizen et al. (2019) / md-121** (CC0, 5807 Whitefly-Boxen — deutlich über der 150+-Schwelle). *(verifiziert, 3-0)*
2. **Die Thrips-Lücken schließen sich am 2026-09-01:** Ein **Frontiers-2025-Set** liefert artaufgelöste Boxen für *F. occidentalis*, *E. americanus* und *T. vaporariorum* unter CC-BY 4.0 — aber das Zenodo-Release ist **bis 1. September 2026 unter Embargo** und heute unbrauchbar. *(verifiziert, 3-0)*
3. **Die vier harten Lücken** (`fungus_gnat`, `mealybug`, `spider_mite`, Nützlings-Larven) werden durch **keinen** verifizierten fertigen Datensatz abgedeckt. AgriPest ist Feldkultur-only und irrelevant (sein „mite" ist *Petrobia latens*, nicht *T. urticae*). *(verifiziert, 3-0)*
4. **Der strategisch wichtigste Befund ist juristisch:** Creative Commons' eigene veröffentlichte Position besagt, dass KI-Training häufig bereits urheberrechtlich erlaubt ist und CC-Bedingungen (inkl. NC) deshalb nur begrenzt greifen; unter der **EU-TDM-Schranke (DSM Art. 4 / §44b UrhG) wird die CC-Lizenz „nicht ausgelöst"**, und eine CC-Lizenz allein ist **kein** Art.-4(3)-Opt-out. Das öffnet — konditioniert — den großen **CC-BY-NC-Default-Pool von iNaturalist**, aber nur als CC's *umstrittene* Auslegung, die eine projektspezifische anwaltliche Klärung braucht, nicht als gesicherte Rechtslage. *(verifiziert, 3-0; mit drei Defeatern)*
5. **Methodisch ist der Weg validiert:** Few-Shot-Learning ist das passende Regime bei knappen, visuell ähnlichen Insektendaten *(verifiziert, 3-0)*, und **Copy-Paste-Blend-Augmentation** ist empirisch stark (Whitefly-Recall 54,4 % → 93,2 % bei Erweiterung 140 → 560 Bilder, GAN nur +1–3 pp obendrauf). *(verifiziert, 3-0)*

> **Fazit in einem Satz:** Whitefly ist gelöst, Thrips kommt per Kalendereintrag (2026-09-01), und die restlichen vier Lücken lassen sich realistisch nur über (a) **per-Foto-CC0/CC-BY-Harvesting** aus Beobachtungsquellen, (b) **Copy-Paste-Augmentation**, (c) **eigene HITL-/Citizen-Science-Akquise** und (d) die **anwaltlich freizugebende CC-BY-NC/TDM-Erweiterung** schließen.

---

## 3. Verifizierte Quellen-Tabelle

Legende Eignung: ✅ direkt nutzbar · 🟡 nutzbar mit Klärung/Aufwand · 🔴 ungeeignet/blockiert · ❔ im Scope, aber in dieser Runde **nicht verifiziert**

| Quelle | Abgedeckte Zielklassen | Per-Bild-Lizenzmechanik | Realistische Bildmenge | Integrationsaufwand | Eignung |
|---|---|---|---|---|---|
| **iNaturalist Direkt-API** | potenziell alle 12 | Foto-Lizenz ≠ Observation-Lizenz; **Default CC-BY-NC**; pro Foto editierbar/filterbar | hoch im NC-Pool, **klein im CC0/CC-BY-Teil** | niedrig (analog `GBIFMediaClient`) | 🟡 (CC0/CC-BY-Teil ✅; NC-Teil nur via §6) |
| **iDigBio Media-API** (`/v2/search/media/`) | Taxon-Filter via `rq` (scientificname/family/genus) | Lizenz **server-seitig** filterbar (Gegenteil widerlegt, 0-3) | gering — Specimen-/Herbar-biased, Live-Pest-Ertrag dünn & ungetestet | mittel | 🟡 |
| **Nieuwenhuizen 2019 / md-121 (Yellow Sticky Traps)** | `whitefly` (5807 Boxen) | **CC0** (4TU + md-121 LICENSE verbatim) | 284 Bilder / 8114 Boxen gesamt | niedrig–mittel (Box-Format) | ✅ |
| **Frontiers 2025 (Zenodo 10.5281/zenodo.15574404)** | `thrips_frankliniella`, `thrips_echinothrips`, `whitefly` | **CC-BY 4.0** | artaufgelöste Boxen | — | 🔴 **bis 2026-09-01 embargoed** |
| **AgriPest** | keine (Feldkultur) | — | — | — | 🔴 ausgeschlossen |
| **iNaturalist CC-BY-NC-Pool (via TDM Art. 4)** | potenziell alle 12 (inkl. Lücken) | NC, aber TDM-Schranke „triggert" Lizenz evtl. nicht | **groß** (Default-Lizenz!) | niedrig technisch, **hoch juristisch** | 🟡 nur anwaltlich freigegeben |
| Observation.org | EU-/DE-Fokus, potenziell alle | ❔ | ❔ | niedrig | ❔ unverifiziert |
| EOL Media-API | potenziell alle | ❔ (laut Doku CC/PD) | ❔ | mittel | ❔ unverifiziert |
| BHL / BOLD / Wikimedia Commons / Flickr-CC / Pl@ntNet | ❔ | ❔ | ❔ | variabel | ❔ unverifiziert |

> **Warnung zur Tabelle:** Observation.org, EOL, BHL, BOLD, Wikimedia Commons, Flickr-CC und Pl@ntNet standen im Recherche-Scope, produzierten aber **keine überlebenden verifizierten Claims**. Ihre per-Bild-Lizenzmechanik und ihr per-Taxon-Ertrag sind **offen** und müssen in einer Folgerunde geprüft werden (siehe §8 Offene Fragen).

---

## 4. Detailbefunde

### 4.1 Beobachtungs-/Aggregator-Quellen

**iNaturalist (verifiziert, 3-0).** Fotos werden **getrennt von der Beobachtung** lizenziert; der Default für neu hochgeladene Medien ist **CC-BY-NC**. GBIF nimmt nur Datensätze mit CC0/CC-BY/CC-BY-NC auf — der GBIF-iNat-Pool ist deshalb auf Observation-Ebene **NC-dominiert.** Operative Konsequenz: **auf das per-Foto-Lizenzfeld filtern** (nicht auf die Observation-Lizenz). Ein harter NC-Filter verwirft damit den **Großteil** des Pools — genau das ist der heutige Engpass.
Quellen: [iNat-Lizenz-FAQ](https://help.inaturalist.org/en/support/solutions/articles/151000173511-how-do-licenses-work-on-inaturalist-should-i-change-my-licenses-), [iNat-Hilfe](https://help.inaturalist.org/en/support/solutions/articles/151000170346).

**iDigBio (verifiziert, 3-0).** Dedizierter Endpoint `/v2/search/media/` (Params `mq`, `rq`, `sort`, `fields`, `fields_exclude`, `limit`, `offset`, `no_attribution`). Taxon-Filter **indirekt** über `rq` gegen Record-Taxonomie (scientificname/family/genus), da es kein Media-natives Taxon-Feld gibt. Lizenz **ist** server-seitig filterbar (die gegenteilige Behauptung wurde mit 0-3 widerlegt). **Caveat:** Specimen-/Herbar-biased → Live-Pest-Ertrag für diese 12 Taxa (v. a. Spinnmilbe, Nützlings-Nymphen) ungetestet und vermutlich dünn.
Quellen: [iDigBio Search-API Wiki](https://github.com/iDigBio/idigbio-search-api/wiki), [ridigbio `idig_search_media`](https://rdrr.io/cran/ridigbio/man/idig_search_media.html).

### 4.2 Annotierte Detektor-Datensätze

**Nieuwenhuizen 2019 / md-121 — der einzige sofort nutzbare Treffer (verifiziert, 3-0).** **CC0** (saubere Title-Chain, da Upstream bereits CC0). 284 Bilder @ 5184×3456 px, 8114 Boxen: **Whitefly (*T. vaporariorum*) 5807**, *Macrolophus pygmaeus* 1619, *Nesidiocoris tenuis* 688. Deckt von den 12 Klassen **nur `whitefly`** ab (die beiden anderen sind Nicht-Ziel-Raubwanzen). Yellow-Sticky-Trap = adulte/Stufe-2-Box-Daten. Kleiner, nicht widerlegender Caveat: Das einzelne `WF`-Label könnte *T. vaporariorum* und *Bemisia tabaci* vermengen (Whitefly-Ebene, nicht artrein).
Quellen: [4TU.ResearchData 12707066](https://data.4tu.nl/articles/Raw_data_from_Yellow_Sticky_Traps_with_insects_for_training_of_deep_learning_Convolutional_Neural_Network_for_object_detection/12707066), [md-121 GitHub](https://github.com/md-121/yellow-sticky-traps-dataset).

**Frontiers 2025 — taxonomisch wertvollster Treffer, aber zeitlich blockiert (verifiziert, 3-0).** Artaufgelöste Box-Klassen für *F. occidentalis* (`thrips_frankliniella`), *E. americanus* (`thrips_echinothrips`), *T. vaporariorum* (`whitefly`) plus Nicht-Ziel *B. tabaci*, unter **CC-BY 4.0**. **Blocker:** Zenodo-DOI `10.5281/zenodo.15574404` **bis 2026-09-01 embargoed** → Kalendereintrag setzen und nach Freigabe nachziehen.
Quellen: [Frontiers 2025](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1668795/full), [Zenodo-Record](https://zenodo.org/records/15574404).

**AgriPest — ausgeschlossen (verifiziert, 3-0).** Nur Feldkulturen (Weizen/Reis/Mais/Raps), 14 Feldschädlinge, **null** Nützlinge, **null** Whitefly/Frankliniella/Tetranychus/Pseudococcidae/Sciaridae. Sein „mite" ist *Petrobia latens* (Braune Weizenmilbe), **nicht** *T. urticae* — die Spinnmilben-Lücke wird damit **nicht** geschlossen.
Quellen: [Sensors 21(5):1601](https://www.mdpi.com/1424-8220/21/5/1601), [PMC7956390](https://pmc.ncbi.nlm.nih.gov/articles/PMC7956390/).

> **Roboflow Universe / Kaggle / Hugging Face:** In dieser Runde wurden **keine** namentlichen Sets für `mealybug`/`spider_mite`/`fungus_gnat` mit *verifizierter* kommerzieller Lizenz bestätigt (die Roboflow-Suchseite war als Quelle unzuverlässig). Solche Sets existieren vermutlich, ihre Lizenz ist aber **einzeln zu verifizieren** und gilt bis dahin als ungeklärt.

### 4.3 Rechtsfrage: CC-BY-NC + TDM-Schranke (der größte Hebel)

**Creative Commons' Position (verifiziert, 2-1 / 3-0).** CC schreibt wörtlich: *„AI training is often permitted by copyright. This means that the CC license conditions have limited application to machine reuse."* BY-, SA- und ND-Bedingungen werden **nur bei öffentlicher Weitergabe** von Werken/Adaptionen ausgelöst — interne, nicht-verteilte Nutzung löst sie nicht aus. NC gilt dagegen für *alle* Nutzungen, die eine urheberrechtliche Erlaubnis erfordern. **Direkt relevant für Kamerplanters Architektur:** keine Bildpersistenz, nur Embeddings + Attributions-Manifest, keine öffentliche Weiterverteilung der Quellbilder.

**TDM-Schranke (verifiziert, 3-0).** CC (TDM-Statement 2021): *„If the use of a CC-licensed work for TDM purposes is covered by the exception established at Article 4, the license is not triggered … the CC license terms do not apply"*; und *„CC licenses cannot be construed … as a reservation of a right in the context of Article 4 … CC licenses do not operate as an opt-out."* Das deutsche Pendant ist **§44b UrhG**. Das **OLG Hamburg (Kneschke v. LAION, 2024)** bestätigte die TDM-Schranke für KI-Trainingsdaten.

**Drei konkrete Defeater (Caveats):**
1. Die **Reproduktion während des Minings** kann das Vervielfältigungsrecht trotzdem berühren.
2. Plattform oder Uploader können ein **separates, ausdrückliches Art.-4(3)-Opt-out** setzen, das NC reaktiviert.
3. **Lawful-Access**-Erfordernis; zudem jurisdiktionsabhängig (EU).

> Dies ist eine **rechtsanwaltlich freizugebende** Erweiterungsoption, kein Engineering-Freibrief. Sie ist CC's umstrittene Auslegung und **keine gesicherte Rechtslage.** Würde sie freigegeben, erschließt sie den großen iNaturalist-CC-BY-NC-Default-Pool — und damit potenziell **alle vier Lücken** auf einen Schlag.
Quellen: [CC AI-Training Primer](https://creativecommons.org/2025/05/15/understanding-cc-licenses-and-ai-training-a-legal-primer/), [CC: Using CC-licensed works for AI training](https://creativecommons.org/using-cc-licensed-works-for-ai-training-2/), [CC TDM-Statement (PDF)](https://creativecommons.org/wp-content/uploads/2021/12/CC-Statement-on-the-TDM-Exception-Art-4-DSM-Final.pdf), [Wolters Kluwer: Kneschke v. LAION](https://legalblogs.wolterskluwer.com/copyright-blog/kneschke-vs-laion-landmark-ruling-on-tdm-exceptions-for-ai-training-data-part-2/), [Bird & Bird: OLG Hamburg](https://www.twobirds.com/en/insights/2025/germany/higher-regional-court-hamburg-confirms-ai-training-was-permitted-(kneschke-v,-d-,-laion)).

### 4.4 Datenmengen & Methodik

**Few-Shot ist das richtige Regime (verifiziert, 3-0).** Gomes & Borges (Agronomy 2022) zeigen Prototypical Networks auf IP-FSL (142 Klassen, 6817 Bilder) mit 86–88 % Accuracy — passend zu Kamerplanters frozen-DINOv2 + Prototypical bei ~10–30 Bildern/Klasse. **Caveat:** vor DINOv2, auf IP102-Feldschädlingen; stützt die *Strategiefamilie*, nicht die exakte Pipeline.
**Widerlegt (0-3):** Der Reifestadien-Transfer (Larve vs. Adult, ~86–88 %) überträgt sich **nicht** sauber auf die Nützlings-Larven-Lücke — diese Lücke ist also methodisch **nicht** durch Few-Shot „mitgelöst".
Quellen: [Agronomy 12(8):1733](https://www.mdpi.com/2073-4395/12/8/1733), [FSL-Insect-Repo](https://github.com/Jacocirino/FSLInsectImageRecognition).

**Copy-Paste-Blend-Augmentation ist empirisch stark (verifiziert, 3-0).** Quaghebeur et al. 2022: Whitefly-Detektor-Recall @IoU≥0,50 stieg **54,4 % → 93,2 %** (avg IoU 34,6 → 70,9) bei Erweiterung 140 → 560 Bilder per Copy-Paste-Blend (ohne GAN); GAN brachte nur +1,4/+2,6 pp obendrauf. → **Primärer Daten-Multiplikator** für die Stufe-2-Box-Lücken: sobald ~150 echte Boxen einer Klasse vorliegen, lässt sich der effektive Trainingsumfang vervielfachen. **Caveat:** Einzelstudie, eine Art, kleiner Testsplit.
Quelle: [PMC9523729](https://pmc.ncbi.nlm.nih.gov/articles/PMC9523729/).

### 4.5 Aktive Datengewinnung (HITL / Citizen Science / Biocontrol)

- **In-App user-contributed images** existieren bereits (REQ-010, PR #258: Upload/Kamera + Admin-Promotion/Moderation). Dies ist der strategisch wertvollste Kanal: **volle Nutzungsrechte**, exakte Zieldomäne (Zimmerpflanze, Handykamera, reale Beleuchtung), schließt die Lab-vs-Field-Lücke. Ausbaurichtung: Active Learning (Modell prä-annotiert → Nutzer bestätigt), gezielte „Wir suchen Fotos von …"-Kampagnen für die vier Lücken.
- **Universitäts-Extension / Biocontrol-Quellen:** [UC IPM Natural Enemies Gallery](https://ipm.ucanr.edu/natural-enemies/) ist eine kuratierte Nützlings-Bildquelle (Lizenz pro Bild zu klären). Nützlings-Versender (Encarsia-, Phytoseiidae-Produkte) haben oft freigebbare Produktfotos — Freigabe/Lizenz aktiv einholen. In dieser Runde **kein** verifizierter offener Datensatz für `predatory_mite`/`parasitoid_wasp`.

---

## 5. Bewertung pro Zielklasse

| Klasse | Bester verifizierter Weg | Lücke? |
|---|---|---|
| `whitefly` | ✅ md-121/Nieuwenhuizen (CC0, 5807 Boxen) — **gelöst** | nein |
| `thrips_frankliniella` | 🟡 Frontiers 2025 (CC-BY) **ab 2026-09-01**; bis dahin iNat CC0/CC-BY + HITL | teilw. (zeitlich) |
| `thrips_echinothrips` | 🟡 Frontiers 2025 **ab 2026-09-01**; bis dahin iNat + HITL | teilw. (zeitlich) |
| `aphid` | 🟡 iNat/iDigBio CC0/CC-BY (breit) + Indoor-Kontext via HITL | klein |
| `spider_mite` | 🔴 kein Set; per-Foto-CC0/CC-BY-Harvesting + **Makro-Eigenakquise** + Augmentation; als Schadbild-Klasse parallel führen | **ja (1)** |
| `mealybug` | 🔴 kein Set; **Makro-Eigenakquise** (Watte-Optik) + iNat-Harvesting + TDM-Pool | **ja (2)** |
| `fungus_gnat` | 🔴 kein Set; **Gelbtafel-Eigenakquise** + HITL + TDM-Pool | **ja (3)** |
| `ladybird`/`lacewing`/`hoverfly` (Larven) | 🔴 kein Set; iNat `lifeStage`-Filter (unbestätigt) + EOL + HITL | **ja (4)** |
| `predatory_mite` | 🟡 UC IPM + Biocontrol-Lieferanten (Lizenz klären) + HITL | ja |
| `parasitoid_wasp` (*Encarsia formosa*) | 🟡 Biocontrol-Lieferanten-Fotos (Lizenz klären) + HITL | ja |

---

## 6. Priorisierte Empfehlung

**Sofort (gleiche Architektur, niedriges Risiko):**
1. **md-121/Nieuwenhuizen (CC0)** einziehen → `whitefly`-Stufe-2 sofort lösen (Gelbtafel-Pfad, RF-DETR-S-Warmstart).
2. **iNaturalist Direkt-API als zweite Quelle** neben dem GBIF-RG-Export, mit **per-Foto-Lizenzfilter** (CC0/CC-BY) und — sobald bestätigt — `lifeStage`-Filter für Larven.
3. **iDigBio-Media-Client** (`/v2/search/media/`, `rq`-Taxon-Filter, server-seitiger Lizenzfilter) als Ergänzung; Ertrag pro Taxon messen.

**Kurzfristig (Detektor-Pfad freischalten):**
4. **Copy-Paste-Blend-Augmentation** aufsetzen — primärer Daten-Multiplikator; aus Klassifikations-Crops Box-Daten erzeugen.
5. **Kalendereintrag 2026-09-01:** Frontiers-2025-Set (CC-BY) nachziehen → schließt beide Thrips-Lücken mit echten Boxen.

**Strukturell (höchster langfristiger Wert):**
6. **In-App-HITL ausbauen** (Active Learning auf dem vorhandenen user-contributed-Kanal) — volle Rechte, echte Zieldomäne; gezielte Kampagnen für die vier Lücken.
7. **Eigen-Akquise** für `fungus_gnat` (Gelbtafel) und `mealybug` (Makro).
8. **Biocontrol-/Extension-Fotos** für `predatory_mite`/`parasitoid_wasp` aktiv freigeben lassen.

**Anwaltlich klären (Show-Stopper-Löser):**
9. **CC-BY-NC + TDM-Art.-4-Pathway** für die embedding-only-Architektur prüfen lassen — potenziell der größte einzelne Daten-Hebel, der alle vier Lücken erschließt. Drei Defeater adressieren (Reproduktion-beim-Mining, Art.-4(3)-Opt-out, Lawful-Access).

**Lizenz-Leitplanke durchgehend:** Jede neue Quelle läuft durch dieselbe `is_acceptable()`-Pipeline (`reference_image_license.py`). Research-Benchmarks (IP102/AgriPest/Pest24) nur für **Vortraining**, nie als weiterverteilte Referenzbilder.

---

## 7. Zeitkritische & Lizenz-Hinweise

- ⏰ **2026-09-01:** Frontiers-2025-Zenodo-Set (`10.5281/zenodo.15574404`, CC-BY 4.0) wird frei — Trigger setzen.
- ⚖️ **Alle Rechtsbefunde** stammen aus CC's *eigenen* Veröffentlichungen (hohe Autorität für die Lizenz-Mechanik, aber umstrittene Auslegung der TDM-Rechtslage, ausdrücklich keine Rechtsberatung). Die Kette CC-BY-NC → nutzbar-via-Art.-4-TDM ist **nicht gesicherte Rechtslage** und darf ohne projektspezifische anwaltliche Freigabe **nicht** als Grundlage dienen.

---

## 8. Offene Fragen (für Folgerunde / Anwalt)

1. **iNat `lifeStage`-Filter** (kritisch für Nützlings-Larven): Bietet die Direkt-API einen per-Foto-CC0/CC-BY-Filter **und** einen Larven-/Adult-Filter? Wie viele CC0/CC-BY-**Larven**-Fotos pro Nützling existieren real? *(in dieser Runde unbestätigt)*
2. **Per-Taxon-Ertrag** der unverifizierten Quellen — Observation.org, EOL Media-API, BOLD, Wikimedia Commons Category-API, Flickr-CC-API, Pl@ntNet — speziell für `fungus_gnat`, `mealybug` und die <0,5 mm Spinnmilbe (Tier, nicht Schadbild)?
3. **Anwaltliche Freigabe** des CC-BY-NC → DSM-Art.-4-TDM-Pfads für die embedding-only-Architektur, inkl. Reproduktion-beim-Mining-Risiko und möglichem Art.-4(3)-Opt-out durch iNaturalist/Uploader?
4. **Universitäts-Extension / Biocontrol-Lieferanten** mit Bereitschaft, CC0/CC-BY-Fotos für *Encarsia formosa*, Phytoseiidae und Schwebfliegen-Larven freizugeben?

---

## 9. Recherche-Metadaten

- **Verifikationsmodus:** adversariale 3-Stimmen-Verifikation pro Claim (2/3 Refutes = Kill).
- **Statistik:** 5 Suchwinkel · 25 Quellen abgerufen · 101 Claims extrahiert · 25 verifiziert → **21 bestätigt / 4 widerlegt** → 9 synthetisierte Befunde.
- **Widerlegte Claims (nicht in den Report übernommen):** (a) iDigBio-Lizenz *nicht* server-seitig filterbar → falsch (sie **ist** filterbar); (b) Frontiers-Set „ohne Lizenz" → falsch (CC-BY, nur embargoed); (c) „NC verhindert KI-Training nicht zuverlässig" als generelle Aussage → zu stark; (d) Few-Shot-Reifestadien-Transfer auf Larven → überträgt nicht.
