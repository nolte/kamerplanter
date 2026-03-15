# Agrarbiologischer Review: Plant-Info-Dokumente Batch 4
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-05
**Batch:** Kräuter, Zierpflanzen, Gemüse — 11 Dokumente
**Analysierte Dokumente:**

| Datei | Art | Anbaukontext |
|-------|-----|-------------|
| `ocimum_basilicum.md` | Basilikum | Indoor/Outdoor/Kübel |
| `petroselinum_crispum.md` | Petersilie | Indoor/Outdoor/Kübel |
| `anethum_graveolens.md` | Dill | Outdoor/Kübel |
| `allium_schoenoprasum.md` | Schnittlauch | Indoor/Outdoor/Kübel |
| `allium_porrum.md` | Lauch (Porree) | Outdoor/Beet |
| `raphanus_sativus_var_sativus.md` | Radieschen | Outdoor/Beet/Indoor |
| `cichorium_intybus.md` | Wegwarte/Zichorie | Outdoor/Beet |
| `apium_graveolens_var_rapaceum.md` | Knollensellerie | Outdoor/Beet |
| `viola_x_wittrockiana.md` | Stiefmuetterchen | Outdoor/Kübel/Indoor |
| `fragaria_x_ananassa.md` | Kulturerdbeere | Outdoor/Kübel/Indoor |
| `helianthus_annuus.md` | Sonnenblume | Outdoor/Kübel |

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3/5 | Mehrere sachliche Fehler (Photoperiode, Taxonomie, Nomenklatur) |
| Phasenparameter-Vollstaendigkeit | 4/5 | VPD, PPFD, EC gut abgedeckt; vereinzelt thermodynamisch inkonsistent |
| Duenge-Logik | 4/5 | NPK-Profile phasengerecht, EC-Werte plausibel |
| IPM-Eintraege | 4/5 | Gut gepflegt; ein Nomenklatur-Fehler beim Sellerie |
| Mischkultur-Symmetrie | 2/5 | 7 dokumentierte Richtungsasymmetrien — kritisch fuer Graph-Import |
| CSV-Import-Eignung | 3/5 | Spalten-Inkonsistenzen quer ueber Dokumente; negative Allelopathie-Scores ungeklaert |

Die Dokumentenqualitaet ist fuer einfache Kulturen (Schnittlauch, Radieschen, Sonnenblume) hoch. Fuer komplexere Arten (Knollensellerie, Fragaria, Cichorium) bestehen sachliche Fehler und Inkonsistenzen, die vor dem Produktiv-Import korrigiert werden muessen. Die Mischkultur-Symmetrieprobleme sind systemkritisch, da asymmetrische Graphkanten die Empfehlungslogik korrumpieren.

---

## K-xxx: Kritisch — Sofortiger Korrekturbedarf

### K-001: Radieschen 4.3 bezeichnet Langtagspflanze als "Kurztagskultur"

**Dokument:** `raphanus_sativus_var_sativus.md`, Abschnitt 4.3
**Fehlerhafter Text:** "Kurze Kulturzeit (4-6 Wochen) macht Radieschen zur idealen einjaehrigen Kurztagskultur fuer Staffelsaaten."
**Problem:** Radieschen (*Raphanus sativus* var. *sativus*) ist eine **Langtagspflanze** (`long_day`), die unter Langtagsbedingungen (>14h Licht) zur Bluetenbildung (Schossen) neigt und dann als Speisepflanze wertlos wird. Der Begriff "Kurztagskultur" ist biologisch falsch. Der korrekte Begriff waere "kurzfristige Kultur" oder "schnellwuechsige Jahreskultur". Die falsche Bezeichnung koennte Nutzer irreleiten, die die optimale Kulturzeit (Fruehjahr/Herbst = Kurztagsbedingungen vermeidend) missverstehen.
**Korrekte Formulierung:** "Kurze Kulturzeit (4–6 Wochen) macht Radieschen zur idealen Jahreskultur fuer Staffelsaaten. Wegen der Schosstendenz unter Langtagsbedingungen (>14h Licht) empfehlen sich Hauptkulturen im Fruehjahr (Maerz–Mai) und Herbst (Aug.–Okt.)."
**Anbaukontext:** Outdoor / Indoor (Wachstumslicht-Steuerung betroffen)

---

### K-002: Apium graveolens var. rapaceum — care_style "tropical" biologisch falsch

**Dokument:** `apium_graveolens_var_rapaceum.md`, Abschnitt 1.1 und 6.4
**Fehlerhafter Wert:** `care_style: tropical`
**Problem:** Knollensellerie (*Apium graveolens* var. *rapaceum*) ist eine gemaessigt-kontinentale bis mediterrane Kulturpflanze aus dem europaeischen Raum. Die Art benoetigt Vernalisation (Kaeltereiz) zur Blueteninduktion, toleriert leichten Frost und hat ihren Ursprung in Sumpflaendereien Mitteleuropas und des Mittelmeerraums. Der `tropical` Care-Style impliziert hohe Luftfeuchtigkeit (70–80%), ganzjaehrige Waerme und feuchte Substratfuehrung — das Gegenteil der korrekten Kulturansprueche (maessige Luftfeuchte 50–65%, kuehle Nacht, klarer Fruehjahrsstart). Die falsche Care-Style-Zuweisung fuehrt zu falschen Giessplänen und falschen Reminderparamtern im System.
**Korrekte Formulierung:** `care_style: outdoor_annual_veg` oder ein neues Preset `temperate_vegetable`. Bis ein solches Preset existiert: `care_style: mediterranean` als naechste Annaeherung.
**Anbaukontext:** Outdoor / Gewächshaus

---

### K-003: Apium graveolens var. rapaceum — Selleriefliegen-Nomenklatur umgekehrt

**Dokument:** `apium_graveolens_var_rapaceum.md`, Abschnitt 5.1
**Fehlerhafter Text:** "Selleriefliege (*Acidia heraclei* syn. *Euleia heraclei*)"
**Problem:** Nach aktueller Taxonomie (Fauna Europaea, Eckfelder & Hauser 2008) ist der **akzeptierte Name** *Euleia heraclei* (Loew, 1862). *Acidia heraclei* ist das aeltere Synonym. Die Dokument-Reihenfolge "Acidia (syn. Euleia)" ist invertiert — der Synonym wird als Hauptname, der akzeptierte Name als Synonym dargestellt.
**Korrekte Formulierung:** "Selleriefliege (*Euleia heraclei*, syn. *Acidia heraclei*)"
**Anbaukontext:** Outdoor / Freiland

---

### K-004: Mischkultur-Asymmetrie — Basilikum/Schnittlauch

**Dokumente:** `ocimum_basilicum.md` vs. `allium_schoenoprasum.md`
**Problem:** `ocimum_basilicum.md` listet Schnittlauch als **compatible** (score 0.7). `allium_schoenoprasum.md` listet Basilikum **nicht** in den compatible_plants-Eintraegen. Die Graphkante existiert nur in einer Richtung.
**Systemauswirkung:** Der Mischkultur-Empfehlungs-Graph erzeugt inkonsistente Ergebnisse: "Was passt zu Basilikum?" liefert Schnittlauch; "Was passt zu Schnittlauch?" liefert nicht Basilikum.
**Korrekturbedarf:** In `allium_schoenoprasum.md` Eintrag hinzufuegen:
```yaml
- partner: "Ocimum basilicum"
  effect: compatible
  score: 0.7
  reason: "Gegenseitige Schadinsekten-Verwirrung durch aerogene Terpene; Basilikum profitiert von Schnittlauch-Schwefelverbindungen"
```

---

### K-005: Mischkultur-Asymmetrie — Petersilie/Radieschen

**Dokumente:** `petroselinum_crispum.md` vs. `raphanus_sativus_var_sativus.md`
**Problem:** `petroselinum_crispum.md` listet Radieschen als **compatible** (score 0.8). `raphanus_sativus_var_sativus.md` listet Petersilie **nicht** in den companion plants.
**Systemauswirkung:** Gleiche strukturelle Kante wie K-004.
**Korrekturbedarf:** In `raphanus_sativus_var_sativus.md` Eintrag hinzufuegen:
```yaml
- partner: "Petroselinum crispum"
  effect: compatible
  score: 0.8
  reason: "Petersilie lockert Boden und kann Erdfloehe vom Radieschen ablenken; optische Kombination"
```

---

### K-006: Mischkultur-Asymmetrie — Petersilie/Dill (Incompatible)

**Dokumente:** `petroselinum_crispum.md` vs. `anethum_graveolens.md`
**Problem:** `petroselinum_crispum.md` listet Dill als **incompatible** (mild). `anethum_graveolens.md` listet Petersilie **nicht** in den incompatible-Eintraegen (nur: Moehre, Fenchel, Basilikum, Paprika, Tomate, Lavendel).
**Systemauswirkung:** "Vermeiden bei Dill" gibt keine Warnung vor Petersilie. "Vermeiden bei Petersilie" warnt korrekt vor Dill. Halbseitige Warnung.
**Korrekturbedarf:** In `anethum_graveolens.md` Eintrag hinzufuegen:
```yaml
- partner: "Petroselinum crispum"
  effect: incompatible
  severity: mild
  reason: "Gegenseitige Wachstumshemmung durch aehnliche Wurzelexudate; Kreuzung kann Hybridsaemlingen aehneln"
```

---

### K-007: Mischkultur-Asymmetrie — Porree/Schnittlauch (Incompatible)

**Dokumente:** `allium_porrum.md` vs. `allium_schoenoprasum.md`
**Problem:** `allium_porrum.md` listet Schnittlauch als **incompatible** (mild, begruendet mit Naehrstoffkonkurrenz und Schaelingsuebertragung). `allium_schoenoprasum.md` listet Lauch/Porree **nicht** in den incompatible-Eintraegen (nur: Bohnen, Erbse, Kohl, Rote Beete).
**Biologischer Hintergrund:** Die gegenseitige Konkurrenz zwischen Allium-Arten in unmittelbarer Naehe ist gut belegt. Wenn das Verhaeltnis als inkompatibler bewertet wird, muss es in beiden Dokumenten erscheinen.
**Korrekturbedarf:** In `allium_schoenoprasum.md` Eintrag hinzufuegen:
```yaml
- partner: "Allium porrum"
  effect: incompatible
  severity: mild
  reason: "Naehrstoffkonkurrenz zwischen Allium-Arten; erhoehtes Risiko gemeinsamer Schaderreger (Lauchmotte, Zwiebelfliege)"
```

---

### K-008: Mischkultur-Asymmetrie — Cichorium/Sonnenblume (Incompatible)

**Dokumente:** `cichorium_intybus.md` vs. `helianthus_annuus.md`
**Problem:** `cichorium_intybus.md` listet Sonnenblume als **incompatible** (mild, Allelopathie und Beschattung). `helianthus_annuus.md` listet Cichorium/Wegwarte **nicht** in den incompatible-Eintraegen.
**Korrekturbedarf:** In `helianthus_annuus.md` Eintrag hinzufuegen:
```yaml
- partner: "Cichorium intybus"
  effect: incompatible
  severity: mild
  reason: "Allelopathische Hemmstoffe der Sonnenblume koennen Keimung und Wachstum von Cichorium beeintraechtigen; Beschattung durch Hochstand"
```

---

### K-009: Mischkultur-Asymmetrie — Dill/Sonnenblume (Compatible)

**Dokumente:** `anethum_graveolens.md` vs. `helianthus_annuus.md`
**Problem:** `anethum_graveolens.md` listet Sonnenblume als **compatible** (score 0.7, begruendet mit Windschutz und Nützlingsforderung). `helianthus_annuus.md` listet Dill **nicht** in den compatible-Eintraegen (nur: Buschbohne, Gurke, Mais, Tagetes, Kapuzinerkresse).
**Korrekturbedarf:** In `helianthus_annuus.md` Eintrag hinzufuegen:
```yaml
- partner: "Anethum graveolens"
  effect: compatible
  score: 0.7
  reason: "Dill foerdert Nützlinge (Schwebefliegen, Brackwespen) die auch Sonnenblume schuetzen; unterschiedliche Wuchshöhen"
```

---

### K-010: Mischkultur-Asymmetrie — Erdbeere/Petersilie

**Dokumente:** `fragaria_x_ananassa.md` vs. `petroselinum_crispum.md`
**Problem:** `petroselinum_crispum.md` listet Erdbeere als **compatible** (score 0.7). `fragaria_x_ananassa.md` listet Petersilie **nicht** in den compatible-Eintraegen (nur: Knoblauch, Zwiebel, Buschbohne, Tagetes, Salat, Spinat, Schnittlauch, Borretsch, Radieschen, Ringelblume, Stiefmuetterchen).
**Korrekturbedarf:** In `fragaria_x_ananassa.md` Eintrag hinzufuegen:
```yaml
- partner: "Petroselinum crispum"
  effect: compatible
  score: 0.7
  reason: "Petersilie soll Erdbeerpflanzen vor Grauschimmel schuetzen; Bodenbedeckung reduziert Spritzwasser-Infektion"
```

---

## M-xxx: Wesentlich — Korrekturbedarf vor Produktiv-Import

### M-001: Fragaria x ananassa — photoperiod_type "day_neutral" unzureichend fuer Sortenvielfalt

**Dokument:** `fragaria_x_ananassa.md`, Abschnitt 1.1 und 4.1
**Problem:** Das Dokument traegt `photoperiod_type: day_neutral` als Art-Level-Wert, fuegt jedoch den Hinweis hinzu: "sortenabhaengig: June-bearing Sorten = Langtagspflanze, Everbearing/Day-Neutral-Sorten = neutral". Biologisch korrekt ist: Einmal tragende Sorten (June-bearing) sind echte Kurztagspflanzen (Blueteninduktion <12–14h Licht), nicht Langtagspflanzen wie das Dokument suggieriert. Everbearing-Sorten sind tagneutral. Das Art-Level-Feld `day_neutral` ist fuer das System ein Kategorisierungsproblem — beim CSV-Import landet nur ein Wert, der 30–40% aller kultivierten Sorten falsch beschreibt.

**Fachliche Korrektur:** June-bearing Erdbeersorten sind **Kurztagspflanzen** (`short_day`), keine Langtagspflanzen. Everbearing und Day-Neutral-Sorten sind `day_neutral`. Die korrekte Loesung ist:
- Art-Level (`fragaria_x_ananassa.md`): `photoperiod_type: short_day` als Hauptkategorie (repraesentiert die klassische Form)
- Cultivar-Level: Attribut `photoperiod_override: day_neutral` fuer Everbearing/Day-Neutral-Sorten

**Handlungsbedarf:** REQ-001 Cultivar-Modell pruefen — kann `photoperiod_type` auf Cultivar-Ebene ueberschrieben werden?

---

### M-002: Allium porrum — akzeptierter Name nach POWO ist Allium ampeloprasum

**Dokument:** `allium_porrum.md`, Abschnitt 1.1
**Problem:** Nach POWO (Plants of the World Online, powo.science.kew.org, Stand 2025) ist der akzeptierte Name fuer Porree/Lauch *Allium ampeloprasum* L., mit *Allium porrum* L. als Synonym. Im Gartenbau, Lebensmittelhandel und vielen Pflanzen-Datenbanken wird weiterhin *A. porrum* als Gebrauchsname verwendet, was die Dokument-Situation erklaert. Fuer ein System mit Taxonomie-Anspruch (REQ-001, REQ-011 GBIF-Integration) sollte der akzeptierte Name verwendet werden.
**Empfehlung:** Hauptname auf `Allium ampeloprasum` aendern, `Allium porrum` als Synonym eintragen. Oder: Explizit dokumentieren, dass der Handelsname verwendet wird und bei GBIF-Anreicherung das Mapping auf den akzeptierten Namen erfolgt.
**Betroffene Felder:** `scientific_name`, `synonyms`

---

### M-003: CSV-Spaltenheader nicht konsistent quer ueber alle 11 Dokumente

**Betroffene Dokumente:** Alle 11
**Problem:** Die CSV-Import-Zeilen am Ende jedes Dokuments haben unterschiedliche Spaltensets. Beispiele:
- `ocimum_basilicum.md`: endet mit `hardiness_zones,allelopathy_score,native_habitat`
- `allium_schoenoprasum.md`: enthaelt zusaetzlich `overwintering_hardiness`, `care_style`
- `cichorium_intybus.md`: enthaelt `taproot_depth_cm`, `vernalization_required`
- `apium_graveolens_var_rapaceum.md`: enthaelt `vernalization_weeks`, `bulb_type`
- `viola_x_wittrockiana.md`: enthaelt `traits` als Listenfeld (Semikolon-getrennt)

Der REQ-012 CSV-Import-Engine (CsvParser, RowValidator) kann unterschiedliche Spaltensets nicht ohne explizites Schema-Mapping verarbeiten. Fehlende Spalten werden als `null` importiert, was zu falschen Standardwerten fuehren kann.
**Handlungsbedarf:** Ein kanonisches CSV-Schema fuer Species-Import definieren. Optionale Felder als leere Spalten beibehalten (kein Weglassen). Alle Dokumente auf das kanonische Schema angleichen.

---

### M-004: care_style "herb_tropical" fuer Petersilie und Schnittlauch biologisch ungeeignet

**Betroffene Dokumente:** `petroselinum_crispum.md`, `allium_schoenoprasum.md`
**Problem:**
- *Petroselinum crispum* (Petersilie): Zweijaehrige Pflanze mit Ursprung in Suedosteuropa / Kaukasus-Region. Kalt-tolerant (bis -15°C als zweijahrige Pflanze), benoetigt Vernalisation, bevorzugt kuehlere Temperaturen (15–20°C). Die `herb_tropical`-Einstellung bewirkt falsche Giesspläne (hoehere Giessfrequenz als noetig) und falsche Luft-feuchte-Zielwerte im System.
- *Allium schoenoprasum* (Schnittlauch): Perenner Gebirgskrautler aus arktisch-borealen Standorten. Extrem frosthart (USDA Zone 3, bis -40°C). Saisonale Ruhephase im Winter. `herb_tropical` ist fuer diese Art grundlegend falsch.

**Korrekte Werte:**
- Petersilie: `care_style: mediterranean` (als naechste verfuegbare Annaeherung)
- Schnittlauch: `care_style: outdoor_perennial` oder `herb_temperate` (neues Preset erwuenscht)

---

### M-005: Negative Allelopathie-Scores — Systemkompatibilitaet unklar

**Betroffene Dokumente:** `fragaria_x_ananassa.md` (score: -0.4), `helianthus_annuus.md` (score: -0.6)
**Problem:** Beide Dokumente verwenden negative Allelopathie-Scores zur Darstellung von Autotoxizitaet (Erdbeere: Replant Disease, Bodenmuedigkeit) und Phytotoxizitaet (Sonnenblume: Heliannuol, Heliannuolid als Keimhemmstoff). Die biologische Korrektheit ist nicht in Frage gestellt — negative Werte sind fuer diese Arten wissenschaftlich belegte Realitaet.

**Ungeklaerte Systemfrage:** Unterstuetzt das ArangoDB Species-Modell (REQ-001) und die CSV-Import-Logik (REQ-012 RowValidator) negative Float-Werte fuer `allelopathy_score`? Die Validator-Logik muss `NEGATIVE_FLOAT_ALLOWED = True` fuer dieses Feld setzen.
**Handlungsbedarf:** Backend pruefen: `src/backend/app/domain/engines/row_validator.py` — Validierungsregel fuer `allelopathy_score` auf Bereich `[-1.0, 1.0]` erweitern, nicht nur `[0.0, 1.0]`.

---

### M-006: Fragaria photoperiod-Fehler — June-bearing ist Kurztagspflanze, nicht Langtagspflanze

**Dokument:** `fragaria_x_ananassa.md`, Abschnitt 4.1
**Fehlerhafter Text:** "June-bearing = long_day (Langtagspflanze)"
**Problem:** June-bearing (einmal tragende) Erdbeersorten werden durch **kurze Tage** (weniger als 12–14 Stunden Licht) zur Blueteninduktion gebraucht — sie sind **Kurztagspflanzen**. Klassischer Lehrbuch-Fall: Herbsttage verkuerzen sich, Blueteninduktion erfolgt im Oktober/November, Fruchtreife folgt im Mai/Juni. "Long_day" ist hier das Gegenteil des Richtigen.
**Korrekte Formulierung:** "June-bearing = short_day (Kurztagspflanze): Blueteninduktion erfordert <12–14h Photoperiode bei Temperaturen unter 15°C (Herbstbedingungen)"
**Anbaukontext:** Besonders relevant fuer Indoor-Erdbeerproduktion mit Kunstlichtsteuerung

---

## H-xxx: Hinweise und Best-Practice-Empfehlungen

### H-001: Basilikum photoperiod_type "short_day" ist eine Vereinfachung

**Dokument:** `ocimum_basilicum.md`, Abschnitt 1.1 und 4.1
**Hinweis:** *Ocimum basilicum* reagiert auf Taglaengenveraenderung, wird aber in der Literatur meist als **fakultative Kurztagspflanze** oder "quantitativ kurztagsempfindliche Pflanze" eingestuft. Unter Growbox-Bedingungen mit 18h Licht bluehen die meisten Sorten deutlich spaeter, aber nicht gar nicht. Das Enum `short_day` suggeriert ein klares kategoriales Verhalten, das bei den meisten Handelssorten so nicht zutrifft. Der Dokument-Hinweis "viele moderne Sorten weniger photoperiodempfindlich" ist fachlich korrekt und entschaerft das Problem. Fuer den Growbox-Nutzer ist die praktische Auswirkung (Bluehinderung durch kurze Dunkelphase) wichtiger als die taxonomische Kategorie.
**Empfehlung:** Hinweis in Abschnitt 4.1 erweitertn: "Kurztagspflanze (fakultativ) — moderne Suessbasilikum-Sorten (Sweet Basil, Genovese) sind deutlich weniger photoperiodempfindlich als Wildformen. Unter 18/6h-Lichtzyklus erfolgt Bluetenbildung 2–4 Wochen spaeter als unter 12/12h."

---

### H-002: Viola x wittrockiana care_style "custom" — Datenkonsistenz-Risiko

**Dokument:** `viola_x_wittrockiana.md`, Abschnitt 1.1
**Hinweis:** Der Wert `care_style: custom` ist ehrlich (kein Preset passt genau), erzeugt aber beim CSV-Import ein Problem: Der CareReminderEngine-Lookup (REQ-022) basiert auf care_style-Presets. Ein unbekannter Wert `custom` kann zu einem KeyError oder Fallback auf Default-Werte fuehren, die fuer Stiefmuetterchen ungeeignet sind (z.B. tropical-Defaults).
**Empfehlung:** Entweder ein neues Preset `cool_season_annual` einfuehren (Stiefmuetterchen, Vergissmeinnicht, Hornveilchen — kuehlpraeferierende Zweijaehrige), oder `care_style: outdoor_annual` als naechste Annaeherung verwenden. Im Dokument explizit dokumentieren, welche Abweichungen vom gewaelten Preset vorliegen.

---

### H-003: Score-Asymmetrien in beiderseits deklarierten Mischkultur-Paaren

**Betroffene Paare:**
| Paar | Score in Dokument A | Score in Dokument B |
|------|--------------------|--------------------|
| Erdbeere-Schnittlauch | 0.8 (Erdbeere→Schnittlauch) | 0.9 (Schnittlauch→Erdbeere) |
| Erdbeere-Radieschen | 0.7 (Erdbeere→Radieschen) | 0.8 (Radieschen→Erdbeere) |
| Schnittlauch-Petersilie | 0.7 (Schnittlauch→Petersilie) | 0.8 (Petersilie→Schnittlauch) |

**Hinweis:** Geringfuegige Score-Unterschiede sind nicht zwingend Fehler — Mischkultur-Beziehungen koennen asymmetrisch bewertet werden (Pflanze A profitiert staerker als Pflanze B). Falls das System jedoch einen symmetrischen Score benoetigt (z.B. fuer Ranking), sollte der hoehste Wert oder der Durchschnitt als kanonischer Wert definiert werden.
**Empfehlung:** Im Datenmodell entscheiden: Werden Scores pro Richtung oder als gemeinsamer Edge-Wert gespeichert? Falls pro Richtung: Scores koennen legitim divergieren. Falls als gemeinsamer Wert: Angleichen auf den staerkeren Wert (upper bound).

---

### H-004: Cichorium intybus — Titelbezeichnung "Chicorée" vs. botanisch "Wegwarte"

**Dokument:** `cichorium_intybus.md`, Dateiname und Abschnitt 1.1
**Hinweis:** Der Nutzer-Anfrage-Begriff "Chicorée" und der Dateiname stimmen ueberein. Im Dokument wird die Art korrekt als *Cichorium intybus* (Gemeine Wegwarte) behandelt. "Chicorée" bezeichnet im Deutschen eigentlich den Treibsalat aus den gebleichten Blatttrieben (*C. intybus* var. *foliosum*), waehrend "Wegwarte" die Wildform und "Zichorie" die Rohkaffeeform beschreibt. Das Dokument behandelt die Stammart, was korrekt ist. Der Titel koennte als "Zichorie / Wegwarte (*Cichorium intybus*)" praeziser sein, um Verwechslung mit dem Treibsalat-Chicorée zu vermeiden.
**Empfehlung:** Titel in Abschnitt 1.1 anpassen: "common_name: Gemeine Wegwarte, Zichorie, Chicorée (Treibsalat-Variante: var. foliosum)". Im Nutzerprofil-System unterscheiden zwischen Wildform-Nutzung und Treibsalat-Kultur.

---

### H-005: Allium porrum — Inkonsistente Verwendung von "heavy" vs. "heavy_feeder"

**Dokument:** `allium_porrum.md`, Abschnitt 1.1 und 6.1
**Hinweis:** Das Dokument verwendet in verschiedenen Abschnitten die Zeichenfolgen `heavy` und `heavy_feeder` fuer das `nutrient_demand_level`-Feld. Das System-Enum (REQ-001, common/enums.py) sollte einen kanonischen Wert definieren. Wenn `heavy_feeder` der Enum-Wert ist, muss in Abschnitt 1.1 ebenfalls `heavy_feeder` stehen. Der CSV-Import wuerde `heavy` als ungueltigen Enum-Wert ablehnen.
**Korrekturbedarf:** Alle Vorkommen von `heavy` (als Standalone-Wert fuer dieses Feld) auf `heavy_feeder` vereinheitlichen.

---

### H-006: Anethum graveolens — Allelopathie-Score 0.2 bei bekannter Inhibitionswirkung

**Dokument:** `anethum_graveolens.md`, Abschnitt 7 / 1.1
**Hinweis:** Dill wird in der Literatur mit moeaiger allelopathischer Aktivitaet beschrieben, insbesondere Hemmung von Karottensamen-Keimung (*Daucus carota*) durch Sesquiterpenlactone im Wasser-Extrakt. Ein Score von 0.2 erscheint auf der niedrigen Seite — Literaturwerte wuerden eher 0.3–0.4 rechtfertigen. Gleichzeitig ist die Inhibitionswirkung von Dill verglichen mit Sonnenblume (-0.6) oder Walnuss tatsaechlich gering. Score 0.2 ist vertretbar, aber die begruendende Literaturangabe fehlt.
**Empfehlung:** Literaturbeleg fuer den Score ergaenzen oder Wert auf 0.3 anpassen mit Erlaeuterung der Hemmwirkung auf Apiaceae-Saemern.

---

### H-007: Viola x wittrockiana overwintering_profiles — neues Datenmodell-Feld?

**Dokument:** `viola_x_wittrockiana.md`, Abschnitt (Ende des Dokuments)
**Hinweis:** Das Dokument enthaelt einen `overwintering_profiles`-Block mit Feldern wie `frost_tolerance_c`, `protection_method`, `spring_uncovering_trigger`. Diese Felder entsprechen dem OverwinteringProfile-Node aus dem Outdoor-Garden-Planner Review (REQ-022 v2.3). Fuer Stiefmuetterchen ist Ueberwinterungsmanagement relevant (zweijahrige Kultur, Fruehjahrsblueher). Ob dieses Feld im aktuellen Species-Modell vorhanden ist oder erst mit dem REQ-022-Extension eingefuehrt wird, sollte geprueft werden, damit der CSV-Import diesen Block nicht ignoriert.
**Empfehlung:** Beim Import sicherstellen, dass unbekannte Felder im CSV nicht zu Importfehlern fuehren (graceful skip unbekannter Spalten).

---

### H-008: Sellerie pruning_type "summer_pruning" ungenaue Kategorie

**Dokument:** `apium_graveolens_var_rapaceum.md`, Abschnitt 3 (Pflegemassnahmen)
**Hinweis:** Das Entfernen aelterer Aussenblatter beim Knollensellerie (um die Knollenentwicklung zu foerdern) wird als `pruning_type: summer_pruning` klassifiziert. Diese Kategorie ist eigentlich fuer Obstbaumschnitt und Strauchrueckschnitt im Sommer gedacht (Sommerschnitt zur Wuchshemmung). Beim Sellerie handelt es sich um "Blattausdunnung" oder "Ausputzen" (Removing outer leaves). Falls das System diesen Typ verwendet, um Schnittanweisungen zu generieren, koennte `summer_pruning` missverstaendliche Aufgaben erzeugen.
**Empfehlung:** Neuen Enum-Wert `leaf_thinning` einfuehren oder `foliage_removal` verwenden. Bis dahin: Texterklaerung im Dokument erweitern.

---

## Zusammenfassung: Mischkultur-Symmetrie-Matrix

Die folgende Matrix zeigt alle geprueften Paare aus den 11 Dokumenten:

| Paar | A -> B | B -> A | Symmetrie |
|------|--------|--------|-----------|
| Basilikum — Schnittlauch | compatible 0.7 | nicht erwaehnt | ASYMMETRISCH (K-004) |
| Basilikum — Petersilie | compatible 0.7 | compatible 0.7 | OK |
| Basilikum — Dill | incompatible mild | incompatible mild | OK |
| Petersilie — Schnittlauch | compatible 0.8 | compatible 0.7 | OK (Score-Delta) |
| Petersilie — Radieschen | compatible 0.8 | nicht erwaehnt | ASYMMETRISCH (K-005) |
| Petersilie — Dill | incompatible mild | nicht erwaehnt | ASYMMETRISCH (K-006) |
| Petersilie — Sellerie | incompatible moderate | incompatible moderate | OK |
| Petersilie — Erdbeere | compatible 0.7 | nicht erwaehnt | ASYMMETRISCH (K-010) |
| Porree — Schnittlauch | incompatible mild | nicht erwaehnt | ASYMMETRISCH (K-007) |
| Porree — Sellerie | compatible 0.8 | compatible 0.9 | OK (Score-Delta) |
| Cichorium — Sonnenblume | incompatible mild | nicht erwaehnt | ASYMMETRISCH (K-008) |
| Dill — Sonnenblume | compatible 0.7 | nicht erwaehnt | ASYMMETRISCH (K-009) |
| Stiefmuetterchen — Sonnenblume | incompatible moderate | incompatible moderate | OK |
| Stiefmuetterchen — Erdbeere | compatible 0.7 | compatible 0.7 | OK |
| Erdbeere — Schnittlauch | compatible 0.8 | compatible 0.9 | OK (Score-Delta) |
| Erdbeere — Radieschen | compatible 0.7 | compatible 0.8 | OK (Score-Delta) |

**7 Asymmetrien gefunden (K-004 bis K-010)** — alle muessen vor Graph-Import korrigiert werden.

---

## Parameter-Uebersicht: Vollstaendigkeitspruefung

| Parameter | Basilikum | Petersilie | Dill | Schnittlauch | Porree | Radieschen | Cichorium | Sellerie | Stiefmuetterchen | Erdbeere | Sonnenblume |
|-----------|-----------|-----------|------|-------------|--------|-----------|----------|---------|-----------------|---------|------------|
| PPFD pro Phase | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| DLI-Angabe | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt | fehlt |
| VPD pro Phase | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| EC pro Phase | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| pH-Substrat | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| NPK-Verhaeltnis | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Temperatur Tag/Nacht | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Ruhephase | k.A. noetig | Winterruhe angegeben | k.A. noetig | Winterruhe OK | k.A. noetig | k.A. noetig | Winterruhe OK | k.A. noetig | Winterruhe OK | Winterruhe OK | k.A. (einjahrig) |
| Toxizitaet | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Winterhaerte-Zone | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |

**DLI (Daily Light Integral)** fehlt in allen 11 Dokumenten. Dies ist eine wiederholte Feststellung aus frueheren Reviews (Batch 1–3). DLI = PPFD x Photoperiode x 0,0036 (mol/m2/d) — besonders relevant fuer Indoor-Anbau unter Kunstlicht. Fuer den Growbox-Nutzer (Basilikum Indoor, Erdbeere Indoor) waere DLI-Angabe pro Phase wertvoller als absolute PPFD-Werte.

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Taxonomie / Synonyme | Plants of the World Online | powo.science.kew.org |
| Insekten-Nomenklatur | Fauna Europaea | faunaeur.org |
| Companion Planting Forschung | Rodale Institute | rodaleinstitute.org |
| Erdbeere Photoperiod | Darrow (1966), Fragaria and Strawberry | Klassische Referenz |
| Selleriefliege Taxonomie | Fauna Europaea Diptera | faunaeur.org/diptera |
| Dill Allelopathie | Baziramakenga et al. (1994), J. Chem. Ecol. | Peer Review |
| Sonnenblume Allelopathie | Sunflower allelopathy review, Industrial Crops | ISI-Journals |
| Indoor-Erdbeerproduktion | Universität Wageningen, CEA-Studien | wur.nl |

---

## Glossar (kontextbezogen)

- **Kurztagspflanze (Short-day plant):** Bluetet wenn die Photoperiode (Taglaenge) unter einen kritischen Schwellenwert faellt. Beispiel: June-bearing Erdbeere, Chrysantheme.
- **Langtagspflanze (Long-day plant):** Bluetet wenn die Photoperiode ueber einen kritischen Schwellenwert steigt. Beispiel: Radieschen (Schossen), Spinat, Dill.
- **Tagneutral (Day-neutral):** Bluetezeitpunkt wird nicht durch Taglaenge gesteuert. Beispiel: Everbearing Erdbeere, Tomate.
- **Vernalisation:** Kaeltereiz (mehrere Wochen unter 5–10°C), der zur Bluetenbildung bei Zweijahrigen benoetigt wird. Beispiel: Petersilie, Sellerie, Porree.
- **Allelopathie:** Biochemische Hemmung oder Foerderung anderer Pflanzen durch freigesetzte Stoffe. Negative Scores = Autotoxizitaet (Hemmung der eigenen Art oder Bodenmude).
- **Replant Disease (Bodenmuedigkeit):** Autotoxizitaet bei Erdbeeren durch akkumulierte Phenolsauren nach Daueranbau.
- **DLI (Daily Light Integral):** Tageslichtgesamtmenge in mol/m2/d. Berechnung: PPFD (micromol/m2/s) x Photoperiode (h) x 0,0036.
- **VPD (Vapor Pressure Deficit):** Dampfdruckdefizit der Luft in kPa. Steuergroesse fuer Transpiration und Naehrstofftransport. Abhaengig von Temperatur und Luftfeuchtigkeit.
- **care_style:** Systeminternes Preset der CareReminderEngine (REQ-022), das Giess-, Duenge- und Klimaempfehlungen gruppiert. Falsche Zuweisung fuehrt zu falschen automatischen Pflegeerinnerungen.
- **POWO:** Plants of the World Online — massgebliche Taxonomie-Datenbank des Royal Botanic Gardens Kew, akzeptiert APG IV-Klassifikation.
