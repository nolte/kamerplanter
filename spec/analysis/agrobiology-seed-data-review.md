# Agrarbiologisches Seed-Daten Review
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-18
**Auftrag:** Verifikation aller [AGROBIO-CHECK] Findings aus dem Seed-Data-Validator
**Referenz-Report:** `spec/requirements-analysis/seed-data-validation-report.md`
**Analysierte Seed-Dateien:** `botanical_families.yaml`, `ipm.yaml`, `fertilizers.yaml`, `plagron.yaml`, `plant_info_indoor_3.yaml`, `plant_info_outdoor_1.yaml`

---

## Gesamtbewertung

Von 9 zur Pruefung vorgelegten [AGROBIO-CHECK] Findings:
- 4 Findings vollstaendig bestaetigt — kein Korrekturbedarf an den Seed-Daten
- 3 Findings bestaetigt mit Erweiterungsempfehlung — kein Pflichtfehler, aber fachliche Praezisierung empfehlenswert
- 2 Findings mit konkretem Korrekturbedarf — Daten muessen geaendert werden

Die NPK-Werte und Fertilizer-Daten sind insgesamt von hoher Qualitaet. Die kritischsten Luecken liegen in der taxonomischen Vollstaendigkeit der botanischen Familien-Daten und einer Enum-Schwaeche im IPM-Modell.

---

## Ergebnisse im Einzelnen

### 1. Asparagaceae-Wertekonflikt (S-001)

**Fragestellung:** Welche Werte fuer `typical_nutrient_demand` und `frost_tolerance` sind korrekt fuer Asparagaceae?

**Befund:** Beide widersprueechlichen Definitionen haben eine Berechtigung, denn Asparagaceae ist eine botanisch ausserordentlich heterogene Familie (ca. 2900 Arten, 114 Gattungen). Eine einzige Wertangabe kann die Diversitaet nicht abbilden.

Die relevanten Teilgruppen innerhalb der Familie:

| Nutzungsgruppe | Nährstoffbedarf | Frosttoleranz | Beispiele |
|----------------|----------------|---------------|-----------|
| Gartenbau-Nutzpflanzen | schwer (heavy) | hart (hardy, bis -20 C) | Asparagus officinalis (Spargel) |
| Zimmerpflanzen tropisch | gering (light) | empfindlich (sensitive, min. 10-15 C) | Dracaena fragrans, Sansevieria trifasciata, Chlorophytum comosum |
| Geophyten | mittel (medium) | hart (hardy) | Hyacinthus orientalis, Muscari |
| Sukkulenten | gering (light) | maessig bis hart (je Art) | Agave, Yucca |

**Empfehlung:** Die kanonische Definition in `botanical_families.yaml` behalt `light/moderate` als repraesentativen Wert fuer die im System dominante Zimmerpflanzen-Nutzung. Der `description`-Text muss die Heterogenitaet der Familie explizit benennen. Die Duplikat-Definition in `plant_info_outdoor_1.yaml` (heavy/hardy, repraesentiert nur Spargel) und in `plant_info_indoor_3.yaml` (keine Werteangaben) sind zu entfernen.

**Empfohlene botanical_families.yaml Definition:**
```yaml
- name: Asparagaceae
  common_name_de: "Spargelgewächse"
  common_name_en: Asparagus family
  order: Asparagales
  typical_nutrient_demand: light
  frost_tolerance: moderate
  typical_root_depth: shallow
  typical_growth_forms: [herb, shrub, succulent]
  common_pests: [spider_mites, mealybug, asparagus_beetle]
  common_diseases: [root_rot, rust, fusarium]
  pollination_type: [insect, self, wind]
  soil_ph_preference: {min_ph: 6.0, max_ph: 7.5}
  description: >-
    Grosse und heterogene Familie (ca. 2900 Arten). Typische Zimmerpflanzen
    (Dracaena, Sansevieria, Chlorophytum — Schwachzehrer, frostempfindlich)
    und Nutzpflanzen (Spargel — Starkzehrer, winterhart bis -20°C).
    Artspezifische Pflegedaten beachten.
  rotation_category: ornamental
```

**Korrekturbedarf:** Duplikate in plant_info_outdoor_1.yaml und plant_info_indoor_3.yaml entfernen.

---

### 2. Geraniaceae fehlt (V-011 / P-008)

**Fragestellung:** Ist Geraniaceae die korrekte Familie fuer Pelargonium? Welche Familienwerte sind botanisch korrekt?

**Befund:** Geraniaceae ist die taxonomisch korrekte Familie fuer Pelargonium zonale (APG IV, 2016, Ordnung Geraniales). Die Zuordnung in `plant_info_indoor_3.yaml` (`"Pelargonium zonale": Geraniaceae`) ist richtig.

Wichtige taxonomische Anmerkung: Der Volksname "Geranie" fuer Pelargonium ist ein historischer Irrtum, der sich seit dem 18. Jahrhundert haelt. Echte Geranien (Gattung Geranium) sind grossenteils winterharte Stauden. Pelargonium (ca. 280 Arten, Ursprung Suedafrika) ist frost-empfindlich. Beide Gattungen gehoeren zur selben Familie Geraniaceae, aber mit sehr unterschiedlicher Oekologie.

**Problem:** `plant_info_indoor_3.yaml` deklariert Geraniaceae unter `new_families` nur mit `name` und `order` — alle oekologischen Felder fehlen. `botanical_families.yaml` kennt die Familie nicht.

**Empfohlene vollstaendige Familiendefinition:**
```yaml
- name: Geraniaceae
  common_name_de: "Storchschnabelgewächse"
  common_name_en: Geranium family
  order: Geraniales
  typical_nutrient_demand: medium
  frost_tolerance: sensitive
  typical_root_depth: shallow
  typical_growth_forms: [herb, shrub]
  common_pests: [aphids, whitefly, spider_mites, vine_weevil]
  common_diseases: [botrytis, powdery_mildew, rust, bacterial_blight]
  pollination_type: [insect]
  soil_ph_preference: {min_ph: 6.0, max_ph: 7.0}
  description: >-
    Familie mit Pelargonium (Balkon-/Zimmergeranien, frostempfindlich,
    Herkunft Südafrika) und Geranium (winterharte Storchschnabel-Stauden).
    Pelargonium wird umgangssprachlich fälschlich als 'Geranie' bezeichnet.
    Gute Drainage essentiell, Staunässe vermeiden.
  rotation_category: ornamental
```

**Parameterbegründung:**
- `typical_nutrient_demand: medium` — Pelargonien sind Mittelzehrer, besonders K- und Mg-bedürftig fuer intensive Bluetenfärbung
- `frost_tolerance: sensitive` — gilt fuer Pelargonium als Leitgattung im Indoor/Balkon-Bereich (Geranium-Stauden waeren hardy, aber nicht der Kamerplanter-Anwendungsfall)
- `soil_ph_preference 6.0-7.0` — leicht saures bis neutrales Substrat; unter 5.5: Fe/Mn-Toxizitaet; ueber 7.5: Fe/Mn-Mangel
- `bacterial_blight` in common_diseases — Xanthomonas hortorum pv. pelargonii ist quarantaenepflichtig in manchen EU-Staaten und befaellt ausschliesslich Pelargonium

**Korrekturbedarf:** Geraniaceae vollstaendige Definition zu botanical_families.yaml hinzufuegen. Alternativ: Die unvollstaendige Deklaration in plant_info_indoor_3.yaml durch vollstaendige Werte ergaenzen.

---

### 3. Powdery Mildew — Erysiphe spp. (P-006)

**Fragestellung:** Ist `scientific_name: Erysiphe spp.` korrekt und vollstaendig fuer Echter Mehltau?

**Befund:** Erysiphe spp. (Ordnung Erysiphales, Klasse Leotiomycetes) ist eine gueltige Hauptgattung fuer Echten Mehltau. Der Eintrag ist als Allroundeintrag akzeptabel, aber taxonomisch unvollstaendig fuer ein System mit Cannabis-Fokus.

Relevante Gattungen im Kamerplanter-Kontext:
- Erysiphe spp. — Gurke (E. cichoracearum), Tomate (E. lycopersici), allgemein Cucurbitaceae/Solanaceae
- Golovinomyces ambrosiae — Cannabis-spezifischer Echter Mehltau (nach Braun und Cook, 2012, molekularer Revision; frueher Erysiphe ambrosiae); am Indoor-Growbox-System haeufigste Art
- Podosphaera xanthii — Kuerbis und andere Cucurbitaceae (z.B. Zucchini, Melone)
- Podosphaera aphanis — Erdbeere
- Leveillula taurica — Paprika (Capsicum annuum), endophytisch wachsend, erst spaet sichtbar — reagiert anders auf Umweltbedingungen (befaellt Pflanzen auch bei moderater Luftfeuchtigkeit)

**Bewertung:** Fuer ein System mit Cannabis-Fokus sollte Golovinomyces ambrosiae als Cannabis-Erstbefallserreger erwaehnt werden, da er sich in Diagnostik und Behandlungsreaktion von anderen Erysiphe-Arten unterscheiden kann.

**Empfehlung (minimal):** Im `description`-Feld des Disease-Eintrags erwaehnen: "Cannabis: Golovinomyces ambrosiae; Gurke/Kuerbis: Podosphaera xanthii; Paprika: Leveillula taurica."

**Korrekturbedarf:** Kein Pflichtfehler — als pragmatischer Sammeleintrag akzeptabel. Praezisierung empfohlen.

---

### 4. Downy Mildew — Peronospora spp. (P-007)

**Fragestellung:** Ist Peronospora spp. als allgemeiner Bezeichner fuer Falschen Mehltau korrekt? Cannabis-spezifischer Erreger?

**Befund:** Peronospora spp. ist fuer viele Kulturen korrekt (Spinat: P. farinosa, Brassicaceae: P. brassicae, Basilikum: P. belbahrii — wirtschaftlich bedeutsam!). Fuer Cannabis und Gurke sind jedoch andere Gattungen zustaendig:
- Cannabis: Pseudoperonospora humuli — erst 2011 als eigener Cannabis-Erreger bestaetigt (Bates et al., 2011, Plant Disease). Eng verwandt mit P. cubensis (Gurke).
- Gurke: Pseudoperonospora cubensis

Schwerwiegenderer Befund — pathogen_type: **fungal ist taxonomisch falsch** fuer alle Falscher-Mehltau-Erreger. Peronospora, Pseudoperonospora, Plasmopara, Bremia gehoeren zu den Oomyceten (Stramenopiles, Klasse Oomycota), nicht zu den echten Pilzen (Fungi). Dasselbe gilt fuer Pythium spp. (Root Rot, ebenfalls ein Oomycet).

Praktische Konsequenz der Fehlklassifikation: Oomyceten sind unempfindlich gegenueber den meisten Standardfungiziden (Azole, Strobilurine). Wirksame Mittel sind Phosphonate (Phosphorige Saeure, z.B. Aliette), Phenylamide (z.B. Metalaxyl) und Kupferpraeparate. Falls das IPM-System Behandlungsempfehlungen aus pathogen_type ableitet, koennte falsche Klassifikation zu falschen Empfehlungen fuehren.

**Empfehlung (Pflicht):** Enum `pathogen_type` in der `Disease`-Pydantic-Klasse um `oomycete` erweitern. Pythium spp. und Peronospora/Pseudoperonospora umklassifizieren auf `pathogen_type: oomycete`.

**Korrekturbedarf:** pathogen_type: fungal bei Peronospora und Pythium ist sachlich falsch. Enum-Erweiterung erforderlich.

---

### 5. Sugar Royal NPK 9-0-0 (P-004)

**Fragestellung:** Ist ein NPK-Wert von 9-0-0 fuer ein Aminosaeure-Supplement biologisch und analytisch plausibel?

**Befund:** Ja — vollstaendig korrekt und biochemisch erklaerbar.

Alle Aminosaeuren enthalten Stickstoff in ihrer Aminogruppe (-NH2). Der N-Gewichtsanteil variiert je nach Aminosaeure stark: Glycin 18,7%, Alanin 15,7%, Arginin 32,2% (vier N-Atome!), Lysin 19,2%. Ein Produkt aus 18 verschiedenen Aminosaeuren mit einem gewichteten mittleren N-Anteil von 8,5% (deklariert als gerundete 9% im NPK-Format) ist chemisch korrekt — insbesondere wenn N-reiche Aminosaeuren wie Arginin, Asparagin, Glutamin prominent vertreten sind.

Der organisch gebundene N aus Aminogruppen unterscheidet sich fundamental von Mineral-N:
- Er wird nicht direkt als Nitrat oder Ammonium aufgenommen
- Freisetzung durch mikrobielle Deaminasen im Substrat (langsam, puffer-artig)
- Oder Direktaufnahme als Aminosaeure-Molekuel ueber spezifische Transporter in der Wurzel
- Kein proportionaler EC-Beitrag (EC 0,02 mS/cm pro mL ist korrekt niedrig)

Nebenbefund Daten-Inkonsistenz: Das Referenzdokument `plagron_sugar_royal.md` spezifiziert `mixing_priority: 65` und `is_organic: true`, waehrend `plagron.yaml` `mixing_priority: 40` und `is_organic: false` deklariert. Die Referenz-Dok-Werte sind korrekt (Aminosaeure-Supplement nach Basisduenger und PK-Booster, organischen Ursprungs).

**Korrekturbedarf:** NPK-Wert korrekt. Korrekturbedarf bei mixing_priority (40 auf 65 aendern) und is_organic (false auf true aendern) gemaess Referenzdokument.

---

### 6. Sensi Bloom B NPK 2-4-8 (P-001)

**Fragestellung:** Ist das NPK-Verhaeltnis 2-4-8 fuer einen Bluetooth-Basisdünger plausibel?

**Befund:** Vollstaendig korrekt und gegen Referenzdokument `an_sensi_bloom_b.md` verifiziert.

Physiologische Begruendung des P:K = 1:2 Verhaeltnisses in der Bluetephase:
- K (8%) — Kalium steuert Stomata-Regulierung, Turgor-Aufrechterhaltung in Bluetengewebe, Zucker-Translokation im Phloem, und ist Cofaktor fuer mehr als 60 Enzyme inklusive Terpen-Cyclase (Harzproduktion). Kalium ist in der Bluetephase der dominante Makronaehrstoff.
- P (4%) — Phosphor unterstuetzt die ATP-Synthese fuer Zellteilung im generativen Gewebe, Phospholipid-Synthese fuer Zellmembranen, und ist energieliefernd fuer Terpen-Biosynthese. Doppelter P-Wert gegenueber Grow B (2%) korrekt fuer erhoehten Bedarf in der generativen Phase.
- N (2%) — Wird nur noch ergaenzend benoetigt; Enzyme fuer Terpenstoffwechsel und Photosynthese-Aufrechterhaltung. Zusammen mit Part A (3% N) ergibt sich 5% Gesamt-N, angemessen.

**Korrekturbedarf:** Keiner.

---

### 7. Sensi Grow A CalMag-Komponente NPK 3-0-0 (P-002)

**Fragestellung:** Ist NPK 3-0-0 korrekt fuer ein Produkt das als CalMag-Komponente beschrieben wird?

**Befund:** NPK 3-0-0 ist korrekt. N und Ca kommen aus Calciumnitrat (Ca(NO3)2) — die N-Deklaration erfasst den Stickstoffanteil des Salzes, der Calcium-Anteil (~3% Ca) ist im NPK-Schema nicht abbildbar.

Die CalMag-Charakterisierung ist wichtig fuer die Mischungsreihenfolge (Part A immer zuerst): Calcium aus Part A muss im Wasser vorverdunnt sein, bevor Part B (mit Phosphaten und Sulfaten aus Monikaliumphosphat, Kaliumsulfat) hinzukommt — sonst bilden sich unloesliche Calciumsulfat- (CaSO4, Gips) und Calciumphosphat- (Ca3(PO4)2, Apatit) Ausfaellungen.

Modellierungsluecke: Das Fertilizer-Modell hat kein `ca_percent`- oder `mg_percent`-Feld. Fuer CalMag-Produkte und Calcium-basierte Basisdunger (besonders fuer Hydroponik und Coco-Substrate, wo Ca/Mg-Kationenaustausch relevant ist) waere ein `secondary_nutrients`-Feld wertvoll.

**Korrekturbedarf:** NPK-Wert ist korrekt. Mittelfristig: Modell um `ca_percent: float | None = None` und `mg_percent: float | None = None` erweitern. Sofort: Notes-Feld praezisieren.

---

### 8. GMB-Plan FLOWERING identisches NPK (P-003)

**Fragestellung:** Ist es ein Fehler, dass Fruehblute und Spaetblute im GMB-Plan dasselbe NPK-Verhaeltnis [4.0, 3.0, 8.0] haben?

**Befund:** Kein Fehler — systembedingt korrekt.

Das Advanced Nutrients pH Perfect GMB-System (Grow-Micro-Bloom) ist ein 3-Part-System, das mit einem fixen 1:1:1-Dosierungsverhaeltnis (gleiche mL-Menge aller drei Komponenten) ueber alle Wachstumsphasen arbeitet. Das resultierende NPK-Profil der Mischung aendert sich daher nicht zwischen Frueh- und Spaetblute. Nur die Gesamtdosis (mL/L) und der EC-Zielwert werden phasenbezogen angepasst. Dies ist das Kern-Designprinzip des GMB-Systems: Maximale Vereinfachung fuer den Grower, Steuerung ausschliesslich ueber Gesamtkonzentration.

Der Unterschied zwischen den Bluetooth-Phasen ist korrekt abgebildet: target_ec_ms 1.6 (Fruehblute) vs. 1.8 (Spaetblute). Die Zugabe eines externen PK-Boosters (PK 13-14) in der Spaetblute verschiebt das effektive NPK-Verhaltnis der gesamten Naehrloesung stark in Richtung hoh-PK / niedrig-N — dieser Effekt ist durch die separate Booster-Dosierung modelliert.

**Korrekturbedarf:** Keiner.

---

## Dringlichkeits-Ranking der empfohlenen Korrekturen

### Prioritaet 1 — Sofortiger Korrekturbedarf

| Nr | Datei | Aenderung |
|----|-------|-----------|
| 1a | `ipm.yaml` | `pathogen_type: fungal` bei Peronospora spp. und Pythium spp. auf `oomycete` aendern; Enum in Domain-Model erweitern |
| 1b | `plant_info_outdoor_1.yaml` | Asparagaceae-Definition unter `new_families` entfernen (Duplikat) |
| 1c | `plant_info_indoor_3.yaml` | Asparagaceae-Definition unter `new_families` entfernen (Duplikat) |
| 1d | `botanical_families.yaml` | Geraniaceae vollstaendige Familiendefinition ergaenzen (Daten oben) |
| 1e | `plagron.yaml` | Sugar Royal: `mixing_priority: 40` auf `65` aendern; `is_organic: false` auf `true` aendern |

### Prioritaet 2 — Empfohlen, kein Pflichtfehler

| Nr | Datei | Aenderung |
|----|-------|-----------|
| 2a | `ipm.yaml` | Powdery Mildew: `description`-Feld mit Gattungshinweisen ergaenzen (Golovinomyces fuer Cannabis, Podosphaera fuer Cucurbitaceae) |
| 2b | `ipm.yaml` | Downy Mildew: `scientific_name` um Pseudoperonospora humuli (Cannabis) ergaenzen |
| 2c | `fertilizers.yaml` | Sensi Grow A: `notes`-Feld ergaenzen mit "Ca ~3% (aus Calciumnitrat), nicht in NPK abbildbar" |
| 2d | Domain Model | `Fertilizer` um `ca_percent: float | None = None` und `mg_percent: float | None = None` erweitern |

### Prioritaet 3 — Langfristig / Optional

| Nr | Empfehlung |
|----|------------|
| 3a | Asparagaceae `description`-Feld in botanical_families.yaml um Heterogenitaet-Hinweis erweitern |
| 3b | `botanical_families.yaml` — Geraniaceae: `frost_tolerance: sensitive` mit Hinweis versehen, dass Geranium-Stauden (nicht Pelargonium) winter-hart sind |

---

## Quellenangaben fuer fachliche Bewertungen

- APG IV (2016): An update of the Angiosperm Phylogeny Group classification. Botanical Journal of the Linnean Society 181(1): 1-20.
- Braun, U. & Cook, R.T.A. (2012): Taxonomic Manual of the Erysiphales (Powdery Mildews). CBS Biodiversity Series 11. Utrecht.
- Bates, S.L. et al. (2011): First report of Pseudoperonospora humuli causing downy mildew of Cannabis sativa in Canada. Plant Disease 95(1):76.
- MycoBank / Species Fungorum: Taxonomische Referenz fuer Pilze und Oomyceten.
- Epstein, E. & Bloom, A.J. (2005): Mineral Nutrition of Plants. Sinauer Associates. (Grundlage Mineralernaehrung und NPK-Physiologie)
- Mengel, K. & Kirkby, E.A. (2001): Principles of Plant Nutrition. 5th ed. Kluwer. (Naehrstoffphysiologie Ca, K, N)
- ASPCA Animal Poison Control: Pelargonium toxicity data.
- RHS Plant Finder: Geraniaceae, Asparagaceae taxonomische Angaben.
